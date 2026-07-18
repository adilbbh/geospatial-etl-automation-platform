import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from readers.geojson_reader import read_geojson
from utils.error_report import save_error_report
from utils.logger import log_message
from utils.summary_report import save_summary_report
from validators.attribute_validator import validate_attributes
from validators.crs_validator import validate_crs
from validators.duplicate_validator import find_duplicate_road_ids
from validators.geometry_validator import validate_geometry
from validators.schema_validator import validate_schema
from writers.postgis_writer import write_roads_to_postgis


PROJECT_DIR = Path(__file__).resolve().parents[1]

DEFAULT_INPUT_FILE = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "austin_roads_ingested.geojson"
)

Feature = Dict[str, Any]
GeoJSON = Dict[str, Any]


def validate_feature(feature: Feature) -> List[Any]:
    """Run all feature-level validation checks."""

    errors: List[Any] = []

    errors.extend(validate_schema(feature))
    errors.extend(validate_geometry(feature))
    errors.extend(validate_attributes(feature))

    return errors


def record_dataset_error(
    input_file: Path,
    message: str,
) -> None:
    """Log and save an error affecting the complete dataset."""

    log_message(message)

    save_error_report(
        [
            {
                "dataset": input_file.name,
                "errors": [message],
            }
        ]
    )


def process_geojson(
    input_file: Path,
) -> tuple[int, int]:
    """
    Validate and load one GeoJSON dataset into PostGIS.

    Returns:
        A tuple containing valid and invalid feature counts.
    """

    input_file = input_file.resolve()

    log_message(f"Reading GeoJSON: {input_file}")

    try:
        geojson: GeoJSON = read_geojson(input_file)

    except FileNotFoundError as error:
        message = f"Input file not found: {input_file}"
        record_dataset_error(input_file, message)
        raise RuntimeError(message) from error

    except json.JSONDecodeError as error:
        message = f"Invalid GeoJSON: {error}"
        record_dataset_error(input_file, message)
        raise RuntimeError(message) from error

    crs_errors = validate_crs(geojson)

    if crs_errors:
        message = f"CRS validation failed: {crs_errors}"

        log_message(message)

        save_error_report(
            [
                {
                    "dataset": input_file.name,
                    "errors": crs_errors,
                }
            ]
        )

        raise RuntimeError(message)

    features = geojson.get("features", [])

    if not isinstance(features, list):
        message = "GeoJSON 'features' must be a list"
        record_dataset_error(input_file, message)
        raise RuntimeError(message)

    if not features:
        message = "GeoJSON contains no features"
        record_dataset_error(input_file, message)
        raise RuntimeError(message)

    duplicate_road_ids = find_duplicate_road_ids(features)

    log_message(
        f"Duplicate road IDs: {duplicate_road_ids}"
    )
    log_message(f"Total features: {len(features)}")

    valid_count, invalid_count, error_report = (
        write_roads_to_postgis(
            features=features,
            input_file_name=input_file.name,
            duplicate_road_ids=duplicate_road_ids,
            validate_feature=validate_feature,
            log_message=log_message,
        )
    )

    save_error_report(error_report)

    save_summary_report(
        total_features=len(features),
        valid_count=valid_count,
        invalid_count=invalid_count,
        input_file=input_file.name,
    )

    log_message("ETL completed.")
    log_message(f"Valid features loaded: {valid_count}")
    log_message(f"Invalid features skipped: {invalid_count}")

    if valid_count == 0:
        raise RuntimeError(
            "No valid features were loaded into PostGIS."
        )

    return valid_count, invalid_count


def parse_arguments() -> argparse.Namespace:
    """Read the optional GeoJSON path from the command line."""

    parser = argparse.ArgumentParser(
        description=(
            "Validate a road GeoJSON dataset and load it "
            "into PostGIS."
        )
    )

    parser.add_argument(
        "input_file",
        nargs="?",
        type=Path,
        default=DEFAULT_INPUT_FILE,
        help=(
            "GeoJSON file to process. The default is the "
            "Austin ingested dataset."
        ),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    try:
        process_geojson(args.input_file)

    except RuntimeError as error:
        log_message(f"ETL failed: {error}")
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()