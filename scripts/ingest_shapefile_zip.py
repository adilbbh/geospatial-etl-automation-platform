from __future__ import annotations
import shutil
import zipfile
from pathlib import Path
import geopandas as gpd
import pandas as pd
PROJECT_DIR = Path(__file__).resolve().parents[1]

INPUT_ZIP = (
    PROJECT_DIR
    / "data"
    / "source"
    / "austin_roads_1000.zip"
)
EXTRACT_DIR = (
    PROJECT_DIR
    / "cache"
    / "austin_roads_1000"
)
OUTPUT_FILE = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "austin_roads_ingested.geojson"
)
REJECTED_FILE = (
    PROJECT_DIR
    / "data"
    / "rejected"
    / "austin_roads_rejected.geojson"
)
REQUIRED_COLUMNS = [
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

def extract_zip() -> Path:
    if not INPUT_ZIP.exists():
        raise FileNotFoundError(
            f"Input ZIP not found: {INPUT_ZIP}"
        )

    if EXTRACT_DIR.exists():
        shutil.rmtree(EXTRACT_DIR)

    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(INPUT_ZIP, "r") as zip_file:
        zip_file.extractall(EXTRACT_DIR)

    shapefiles = list(EXTRACT_DIR.rglob("*.shp"))

    if not shapefiles:
        raise FileNotFoundError(
            "No .shp file found inside the ZIP."
        )

    if len(shapefiles) > 1:
        raise ValueError(
            f"Expected one shapefile, found {len(shapefiles)}."
        )

    return shapefiles[0]


def normalize_missing_values(
    roads: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    text_columns = [
        "osm_id",
        "road_name",
        "road_type",
        "oneway",
        "max_speed",
        "source",
        "city",
        "state",
        "country",
    ]
    missing_tokens = [
        "",
        "nan",
        "NaN",
        "None",
        "none",
        "null",
        "NULL",
    ]
    for column in text_columns:
        if column in roads.columns:
            roads[column] = roads[column].replace(
                missing_tokens,
                pd.NA,
            )

    return roads


def validate_schema(
    roads: gpd.GeoDataFrame,
) -> None:
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in roads.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    if roads.crs is None:
        raise ValueError("Input dataset has no CRS.")


def split_valid_and_rejected(
    roads: gpd.GeoDataFrame,
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    valid_geometry = (
        roads.geometry.notna()
        & ~roads.geometry.is_empty
        & roads.geometry.is_valid
        & roads.geometry.geom_type.isin(
            ["LineString", "MultiLineString"]
        )
    )

    valid_roads = roads[valid_geometry].copy()
    rejected_roads = roads[~valid_geometry].copy()

    return valid_roads, rejected_roads


def main() -> None:
    print(f"Input ZIP: {INPUT_ZIP}")

    shapefile_path = extract_zip()

    print(f"Extracted shapefile: {shapefile_path}")

    roads = gpd.read_file(shapefile_path)

    print(f"Read features: {len(roads)}")
    print(f"Input CRS: {roads.crs}")

    roads = normalize_missing_values(roads)

    validate_schema(roads)

    roads = roads.to_crs("EPSG:4326")

    valid_roads, rejected_roads = split_valid_and_rejected(
        roads
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REJECTED_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    valid_roads.to_file(
        OUTPUT_FILE,
        driver="GeoJSON",
    )

    if not rejected_roads.empty:
        rejected_roads.to_file(
            REJECTED_FILE,
            driver="GeoJSON",
        )
    elif REJECTED_FILE.exists():
        REJECTED_FILE.unlink()

    print()
    print("--- INGESTION RESULT ---")
    print(f"Accepted features: {len(valid_roads)}")
    print(f"Rejected features: {len(rejected_roads)}")
    print(f"Output CRS: {valid_roads.crs}")
    print(f"Accepted output: {OUTPUT_FILE}")

    if rejected_roads.empty:
        print("Rejected output: none")
    else:
        print(f"Rejected output: {REJECTED_FILE}")

if __name__ == "__main__":
    main()