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
INPUT_FILE = PROJECT_DIR / "data" / "roads.geojson"

Feature = Dict[str, Any]
GeoJSON = Dict[str, Any]


def validate_feature(feature: Feature) -> List[Any]:
    errors: List[Any] = []
    errors.extend(validate_schema(feature))
    errors.extend(validate_geometry(feature))
    errors.extend(validate_attributes(feature))
    return errors


def main() -> None:
    log_message("Reading GeoJSON...")

    try:
        geojson = read_geojson(INPUT_FILE)
    except FileNotFoundError:
        message = f"Input file not found: {INPUT_FILE}"
        log_message(message)
        save_error_report([
            {"dataset": INPUT_FILE.name, "errors": [message]}
        ])
        return
    except json.JSONDecodeError as exc:
        message = f"Invalid GeoJSON: {exc}"
        log_message(message)
        save_error_report([
            {"dataset": INPUT_FILE.name, "errors": [message]}
        ])
        return

    crs_errors = validate_crs(geojson)
    if crs_errors:
        log_message(f"CRS validation failed: {crs_errors}")
        save_error_report([
            {"dataset": INPUT_FILE.name, "errors": crs_errors}
        ])
        return

    features = geojson.get("features", [])
    if not isinstance(features, list):
        message = "GeoJSON 'features' must be a list"
        log_message(message)
        save_error_report([
            {"dataset": INPUT_FILE.name, "errors": [message]}
        ])
        return

    duplicate_road_ids = find_duplicate_road_ids(features)
    log_message(f"Duplicate road IDs: {duplicate_road_ids}")
    log_message(f"Total features: {len(features)}")

    valid_count, invalid_count, error_report = write_roads_to_postgis(
        features=features,
        input_file_name=INPUT_FILE.name,
        duplicate_road_ids=duplicate_road_ids,
        validate_feature=validate_feature,
        log_message=log_message,
    )

    save_error_report(error_report)
    save_summary_report(
        total_features=len(features),
        valid_count=valid_count,
        invalid_count=invalid_count,
        input_file=INPUT_FILE.name,
    )

    log_message("ETL completed.")
    log_message(f"Valid features loaded: {valid_count}")
    log_message(f"Invalid features skipped: {invalid_count}")


if __name__ == "__main__":
    main()
