# polygon-processing

This repo contains all the code and datasets related to the processing and generation of the flood extent vectors.

## Scripts

### simplify_geojson.py

This script simplifies, buffers, and combines polygons in a GeoJSON file.

### rasterise.py

This script processes flood extent data and generates combined flood extents.

## Data

### Input Data

Located in the `input_data/` directory:

-   combined_flood_extents.geojson
-   Flood_Awareness_Flood_Risk_Overall-5287907542270699974.geojson
-   qld_gov_flood_extent.geojson

### Output Data

Located in the `output_data/` directory:

-   flood_extents.mbtiles

## Acknowledgements

-   [GeoPandas](https://geopandas.org/)
-   [Shapely](https://shapely.readthedocs.io/)
-   [Rasterio](https://rasterio.readthedocs.io/)
-   [NumPy](https://numpy.org/)
-   [SciPy](https://www.scipy.org/)
