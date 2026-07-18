import json
import os
from pathlib import Path

import psycopg2

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}


def write_roads_to_postgis(
    features, input_file_name, duplicate_road_ids, validate_feature, log_message
):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("TRUNCATE TABLE roads RESTART IDENTITY;")

    insert_sql = """
        INSERT INTO roads
        (road_id, road_name, road_type, source_file, geom)
        VALUES
        (%s, %s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326));
    """

    valid_count = 0
    invalid_count = 0
    error_report = []

    for feature in features:
        errors = validate_feature(feature)

        if errors:
            invalid_count += 1
            error_report.append(
                {
                    "road_id": feature.get("properties", {}).get("road_id"),
                    "errors": errors,
                }
            )
            log_message(f"Invalid feature: {errors}")
            continue

        props = feature["properties"]

        if props.get("road_id") in duplicate_road_ids:
            invalid_count += 1
            error_report.append(
                {
                    "road_id": props.get("road_id"),
                    "errors": [f"Duplicate road_id: {props.get('road_id')}"],
                }
            )
            log_message(f"Invalid feature: duplicate road_id {props.get('road_id')}")
            continue

        geometry_json = json.dumps(feature["geometry"])

        cur.execute(
            insert_sql,
            (
                props["road_id"],
                props["road_name"],
                props["road_type"],
                input_file_name,
                geometry_json,
            ),
        )

        valid_count += 1
        log_message(f"Loaded road: {props['road_id']}")

    conn.commit()
    cur.close()
    conn.close()

    return valid_count, invalid_count, error_report
