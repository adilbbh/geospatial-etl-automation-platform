from __future__ import annotations

import argparse
import shutil
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
CACHE_DIR = PROJECT_DIR / "cache" / "shapefile_uploads"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
REJECTED_DIR = PROJECT_DIR / "data" / "rejected"

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


def safe_extract_zip(
    input_zip: Path,
    extract_dir: Path,
) -> None:
    """Extract a ZIP file while preventing unsafe paths."""

    if not input_zip.exists():
        raise FileNotFoundError(
            f"Input ZIP not found: {input_zip}"
        )

    if not zipfile.is_zipfile(input_zip):
        raise ValueError(
            f"The uploaded file is not a valid ZIP: {input_zip.name}"
        )

    if extract_dir.exists():
        shutil.rmtree(extract_dir)

    extract_dir.mkdir(parents=True, exist_ok=True)
    extract_root = extract_dir.resolve()

    with zipfile.ZipFile(input_zip, "r") as archive:
        for member in archive.infolist():
            destination = (
                extract_dir / member.filename
            ).resolve()

            if (
                destination != extract_root
                and extract_root not in destination.parents
            ):
                raise ValueError(
                    f"Unsafe ZIP entry detected: {member.filename}"
                )

        archive.extractall(extract_dir)


def find_shapefile(extract_dir: Path) -> Path:
    """Find exactly one Shapefile inside the extracted ZIP."""

    shapefiles = list(extract_dir.rglob("*.shp"))

    if not shapefiles:
        raise FileNotFoundError(
            "No .shp file was found inside the ZIP."
        )

    if len(shapefiles) > 1:
        names = [path.name for path in shapefiles]

        raise ValueError(
            "Expected one Shapefile, but found "
            f"{len(shapefiles)}: {names}"
        )

    return shapefiles[0]


def normalize_missing_values(
    roads: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Replace common text representations of missing values."""

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
    """Validate required columns and coordinate system."""

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
        raise ValueError(
            "The uploaded Shapefile does not contain a CRS."
        )


def split_valid_and_rejected(
    roads: gpd.GeoDataFrame,
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """Separate valid road geometry from rejected records."""

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


def process_shapefile_zip(
    input_zip: Path,
    output_file: Path,
    rejected_file: Path,
) -> tuple[int, int]:
    """Process one Shapefile ZIP and create accepted/rejected outputs."""

    input_zip = input_zip.resolve()
    output_file = output_file.resolve()
    rejected_file = rejected_file.resolve()

    extraction_name = input_zip.stem.replace("__", "_")
    extract_dir = CACHE_DIR / extraction_name

    print(f"Input ZIP: {input_zip}")

    safe_extract_zip(
        input_zip=input_zip,
        extract_dir=extract_dir,
    )

    shapefile_path = find_shapefile(extract_dir)

    print(f"Extracted Shapefile: {shapefile_path}")

    roads = gpd.read_file(shapefile_path)

    print(f"Read features: {len(roads)}")
    print(f"Input CRS: {roads.crs}")

    roads = normalize_missing_values(roads)

    validate_schema(roads)

    roads = roads.to_crs("EPSG:4326")

    valid_roads, rejected_roads = split_valid_and_rejected(
        roads
    )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    rejected_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    valid_roads.to_file(
        output_file,
        driver="GeoJSON",
    )

    if rejected_roads.empty:
        if rejected_file.exists():
            rejected_file.unlink()
    else:
        rejected_roads.to_file(
            rejected_file,
            driver="GeoJSON",
        )

    print()
    print("--- INGESTION RESULT ---")
    print(f"Accepted features: {len(valid_roads)}")
    print(f"Rejected features: {len(rejected_roads)}")
    print(f"Output CRS: {valid_roads.crs}")
    print(f"Accepted output: {output_file}")

    if rejected_roads.empty:
        print("Rejected output: none")
    else:
        print(f"Rejected output: {rejected_file}")

    return len(valid_roads), len(rejected_roads)


def parse_arguments() -> argparse.Namespace:
    """Read command-line arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Extract and validate a Shapefile ZIP package."
        )
    )

    parser.add_argument(
        "input_zip",
        type=Path,
        help="Path to the input Shapefile ZIP.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="Optional accepted GeoJSON output path.",
    )

    parser.add_argument(
        "--rejected",
        type=Path,
        help="Optional rejected GeoJSON output path.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    safe_stem = args.input_zip.stem.replace("__", "_")

    output_file = (
        args.output
        if args.output
        else PROCESSED_DIR / f"{safe_stem}_ingested.geojson"
    )

    rejected_file = (
        args.rejected
        if args.rejected
        else REJECTED_DIR / f"{safe_stem}_rejected.geojson"
    )

    process_shapefile_zip(
        input_zip=args.input_zip,
        output_file=output_file,
        rejected_file=rejected_file,
    )


if __name__ == "__main__":
    main()