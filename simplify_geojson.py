import geopandas as gpd
from shapely.ops import unary_union
import argparse
import sys


def simplify_buffer_combine(
    input_geojson, output_geojson, simplification_tolerance=0.5, buffer_size=0.001
):
    """
    Simplifies, buffers, and combines polygons in a GeoJSON file.

    Parameters:
    - input_geojson (str): Path to the input GeoJSON file.
    - output_geojson (str): Path where the output GeoJSON will be saved.
    - simplification_tolerance (float): Tolerance for simplifying geometries.
    - buffer_size (float): Size of the buffer to apply to geometries.
    """
    try:
        # Read the input GeoJSON file
        print(f"Reading input GeoJSON from {input_geojson}...")
        gdf = gpd.read_file(input_geojson)

        if gdf.empty:
            print("The input GeoJSON is empty. Exiting.")
            sys.exit(1)

        # Ensure geometries are valid
        print("Ensuring all geometries are valid...")
        gdf["geometry"] = gdf["geometry"].buffer(0)

        # Simplify geometries
        print(f"Simplifying geometries with tolerance {simplification_tolerance}...")
        gdf["geometry"] = gdf["geometry"].simplify(
            tolerance=simplification_tolerance, preserve_topology=True
        )

        # Buffer geometries to eliminate small holes/gaps
        print(
            f"Buffering geometries by {buffer_size} units to eliminate small holes/gaps..."
        )
        gdf["geometry"] = gdf["geometry"].buffer(buffer_size)

        # Combine all geometries into a single geometry (dissolve)
        print("Combining all geometries into a single geometry...")
        combined_geometry = unary_union(gdf["geometry"])

        # Create a new GeoDataFrame with the combined geometry
        print("Creating a new GeoDataFrame with the combined geometry...")
        result_gdf = gpd.GeoDataFrame(geometry=[combined_geometry], crs=gdf.crs)

        # Save the result to a new GeoJSON file
        print(f"Saving the processed GeoJSON to {output_geojson}...")
        result_gdf.to_file(output_geojson, driver="GeoJSON")

        print("Processing complete!")

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)


def parse_arguments():
    """
    Parses command-line arguments.

    Returns:
    - args: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Simplify, buffer, and combine polygons in a GeoJSON file."
    )
    parser.add_argument("input_geojson", help="Path to the input GeoJSON file.")
    parser.add_argument("output_geojson", help="Path for the output GeoJSON file.")
    parser.add_argument(
        "--simplify",
        type=float,
        default=0.0001,
        help="Simplification tolerance (default: 0.0001). Adjust based on coordinate system.",
    )
    parser.add_argument(
        "--buffer",
        type=float,
        default=0.0001,
        help="Buffer size to apply (default: 0.0001). Adjust based on coordinate system.",
    )
    return parser.parse_args()


def main():
    args = parse_arguments()
    simplify_buffer_combine(
        input_geojson=args.input_geojson,
        output_geojson=args.output_geojson,
        simplification_tolerance=args.simplify,
        buffer_size=args.buffer,
    )


if __name__ == "__main__":
    main()
