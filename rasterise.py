import rasterio
from rasterio.features import rasterize, shapes
import geopandas as gpd
import numpy as np
from scipy.ndimage import binary_propagation
from shapely.geometry import shape
import os


def main():
    print("Starting flood extent processing script...")

    # Load river extent GeoJSON
    river_gdf = gpd.read_file("river_extent.geojson")
    print(f"Loaded river extent GeoJSON with {len(river_gdf)} features")
    print(f"Original CRS: {river_gdf.crs}")

    # Load max flood extent GeoJSON
    max_flood_gdf = gpd.read_file("overall_output.geojson")
    print(f"Loaded max flood extent GeoJSON with {len(max_flood_gdf)} features")
    print(f"Original CRS: {max_flood_gdf.crs}")

    # Load DEM
    print("Loading DEM...")
    dem_dataset = rasterio.open("dem_mosaic.tif")
    elevation_data = dem_dataset.read(1)
    elevation_data = elevation_data.astype("float32")
    elevation_data[elevation_data == dem_dataset.nodata] = np.nan  # Handle nodata
    dem_transform = dem_dataset.transform
    dem_crs = dem_dataset.crs
    print(f"DEM CRS: {dem_crs}")

    # Reproject river and flood extents to match DEM CRS if necessary
    if dem_crs != river_gdf.crs:
        print("Reprojecting river and flood extent to match DEM CRS...")
        river_gdf = river_gdf.to_crs(crs=dem_crs)
        max_flood_gdf = max_flood_gdf.to_crs(crs=dem_crs)
        print(f"Reprojected river CRS: {river_gdf.crs}")
        print(f"Reprojected max flood CRS: {max_flood_gdf.crs}")

    # Define raster properties based on DEM
    width = dem_dataset.width
    height = dem_dataset.height
    transform = dem_transform

    # Rasterize river extent
    print("Rasterizing river extent...")
    river_raster = rasterize(
        [(geom, 1) for geom in river_gdf.geometry],
        out_shape=(height, width),
        transform=transform,
        fill=0,
        dtype="uint8",
    )
    print("River extent rasterized.")

    # Rasterize max flood extent
    print("Rasterizing max flood extent...")
    max_flood_raster = rasterize(
        [(geom, 1) for geom in max_flood_gdf.geometry],
        out_shape=(height, width),
        transform=transform,
        fill=0,
        dtype="uint8",
    )
    print("Max flood extent rasterized.")

    # Mask elevation data outside max flood extent
    print("Masking elevation data outside max flood extent...")
    elevation_data[max_flood_raster == 0] = np.nan

    # Determine river elevation and max elevation within flood extent
    river_elevation = np.nanmin(elevation_data[river_raster == 1])
    max_elevation = np.nanmax(elevation_data[max_flood_raster == 1])

    print(f"River elevation: {river_elevation:.2f} meters")
    print(f"Max elevation within flood extent: {max_elevation:.2f} meters")

    # Generate severity levels (water levels) from river elevation to max elevation
    severity_levels = np.linspace(river_elevation, max_elevation, num=150)
    print(f"Generated {len(severity_levels)} severity levels.")

    # Initialize the flooded area with the river extent
    current_flood = river_raster.astype(bool)

    # Initialize an empty GeoDataFrame to store all flood extents
    all_flood_extents = gpd.GeoDataFrame(columns=["geometry", "severity"], crs=dem_crs)

    # Simulate flooding
    print("Simulating flooding...")
    for idx, water_level in enumerate(severity_levels):
        severity = idx + 1  # Severity levels from 1 to 200

        if severity % 10 == 0 or severity == 1:
            print(
                f"Processing severity level {severity}/{len(severity_levels)}: Water level = {water_level:.2f} meters"
            )

        # Create a mask where elevation <= current water level
        elevation_mask = elevation_data <= water_level

        # Propagate the flood from current flooded area into elevation_mask
        new_flood = binary_propagation(current_flood, mask=elevation_mask)

        # Determine the newly flooded areas
        flood_increment = new_flood & ~current_flood

        if not np.any(flood_increment):
            if severity % 10 == 0 or severity == 1:
                print(f"No new areas flooded at severity level {severity}.")
            continue

        current_flood = new_flood

        # Convert flood_increment to polygons
        results = (
            {"properties": {"severity": severity}, "geometry": shape(geom)}
            for geom, value in shapes(
                flood_increment.astype("uint8"),
                mask=flood_increment,
                transform=transform,
            )
            if value == 1
        )

        results_list = list(results)

        if not results_list:
            if severity % 10 == 0 or severity == 1:
                print(f"No polygons generated at severity level {severity}.")
            continue  # Skip to the next severity level

        # Create GeoDataFrame from features
        gdf = gpd.GeoDataFrame.from_features(results_list, crs=dem_crs)

        # Simplify geometries to reduce file size (optional)
        gdf["geometry"] = gdf["geometry"].simplify(tolerance=1, preserve_topology=True)

        # Append to all_flood_extents
        all_flood_extents = all_flood_extents._append(gdf, ignore_index=True)

        if severity % 10 == 0 or severity == 1:
            print(
                f"Flood polygons for severity level {severity} added to GeoDataFrame."
            )

    # Reproject all_flood_extents to EPSG:4326
    print("Reprojecting combined flood extents to EPSG:4326...")
    all_flood_extents = all_flood_extents.to_crs(epsg=4326)

    # Save the combined GeoDataFrame to a single GeoJSON file
    output_file = "combined_flood_extents.geojson"
    all_flood_extents.to_file(output_file, driver="GeoJSON")
    print(f"Combined flood extents saved to '{output_file}'.")

    print("Flood extent processing completed.")


if __name__ == "__main__":
    main()
