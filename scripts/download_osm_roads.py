from pathlib import Path
import shutil

import geopandas as gpd
import osmnx as ox


PROJECT_DIR = Path(__file__).resolve().parents[1]

SOURCE_DIR = PROJECT_DIR / "data" / "source"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"

SHAPEFILE_FOLDER = SOURCE_DIR / "austin_roads_1000"
SHAPEFILE_PATH = SHAPEFILE_FOLDER / "austin_roads_1000.shp"
ZIP_BASE_PATH = SOURCE_DIR / "austin_roads_1000"
GEOJSON_PATH = PROCESSED_DIR / "austin_roads_1000.geojson"

CENTER_POINT = (30.2672, -97.7431)
DOWNLOAD_DISTANCE_METERS = 4000
TARGET_ROADS = 1000

def clean_osm_value(value):
    """Convert OSM values into clean, shapefile-safe text."""

    if value is None:
        return None

    if isinstance(value, list):
        cleaned_items = [
            str(item)
            for item in value
            if item is not None
        ]

        return ", ".join(cleaned_items) or None

    # Detect pandas/NumPy missing values such as NaN.
    try:
        if value != value:
            return None
    except (TypeError, ValueError):
        pass

    text = str(value).strip()

    if text.lower() in {"nan", "none", "null", ""}:
        return None

    return text

def main():
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    if SHAPEFILE_FOLDER.exists():
        shutil.rmtree(SHAPEFILE_FOLDER)

    SHAPEFILE_FOLDER.mkdir(parents=True, exist_ok=True)

    old_zip = ZIP_BASE_PATH.with_suffix(".zip")

    if old_zip.exists():
        old_zip.unlink()

    print("Downloading Austin roads from OpenStreetMap...")

    graph = ox.graph.graph_from_point(
        CENTER_POINT,
        dist=DOWNLOAD_DISTANCE_METERS,
        network_type="drive",
        simplify=True,
    )
    _, roads = ox.convert.graph_to_gdfs(graph)

    roads = roads.reset_index()

    print(f"Downloaded road segments: {len(roads)}")

    roads = roads.head(TARGET_ROADS).copy()

    roads["road_id"] = range(1, len(roads) + 1)

    roads["osm_id"] = roads["osmid"].apply(clean_osm_value)

    roads["road_name"] = roads["name"].apply(clean_osm_value)

    roads["road_type"] = roads["highway"].apply(clean_osm_value)

    roads["oneway"] = roads["oneway"].astype(str)

    roads["max_speed"] = roads["maxspeed"].apply(clean_osm_value)

    roads["length_m"] = roads["length"].round(2)

    roads["source"] = "OpenStreetMap"
    roads["city"] = "Austin"
    roads["state"] = "Texas"
    roads["country"] = "USA"

    roads = roads[
        [
            "road_id",
            "osm_id",
            "road_name",
            "road_type",
            "oneway",
            "max_speed",
            "length_m",
            "source",
            "city",
            "state",
            "country",
            "geometry",
        ]
    ]
    roads = gpd.GeoDataFrame(
        roads,
        geometry="geometry",
        crs=roads.crs,
    ).to_crs("EPSG:4326")

    roads.to_file(
        SHAPEFILE_PATH,
        driver="ESRI Shapefile",
        encoding="UTF-8",
    )
    roads.to_file(
        GEOJSON_PATH,
        driver="GeoJSON",
    )
    shutil.make_archive(
        str(ZIP_BASE_PATH),
        "zip",
        SHAPEFILE_FOLDER,
    )
    print()
    print("Austin road dataset created successfully.")
    print(f"Road segments: {len(roads)}")
    print(f"CRS: {roads.crs}")
    print(f"Shapefile ZIP: {old_zip}")
    print(f"Processed GeoJSON: {GEOJSON_PATH}")

if __name__ == "__main__":
    main()