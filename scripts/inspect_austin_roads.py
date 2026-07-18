from pathlib import Path
import geopandas as gpd
PROJECT_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "austin_roads_1000.geojson"
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
def main() -> None:
    print(f"Reading dataset: {DATA_PATH}")
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )
    roads = gpd.read_file(DATA_PATH)

    print("\n--- BASIC INFORMATION ---")
    print(f"Feature count: {len(roads)}")
    print(f"CRS: {roads.crs}")
    print(f"Columns: {list(roads.columns)}")

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in roads.columns
    ]
    print("\n--- SCHEMA CHECK ---")

    if missing_columns:
        print(f"Missing required columns: {missing_columns}")
    else:
        print("All required columns are present.")

    print("\n--- GEOMETRY CHECK ---")
    print("Geometry types:")
    print(roads.geometry.geom_type.value_counts())

    empty_count = int(roads.geometry.is_empty.sum())
    null_geometry_count = int(roads.geometry.isna().sum())
    invalid_count = int((~roads.geometry.is_valid).sum())

    print(f"Empty geometries: {empty_count}")
    print(f"Null geometries: {null_geometry_count}")
    print(f"Invalid geometries: {invalid_count}")

    print("\n--- ATTRIBUTE COMPLETENESS ---")

    missing_names = int(
    roads["road_name"]
    .replace(["nan", "None", "null", ""], None)
    .isna()
    .sum()
)
    missing_speed = int(
    roads["max_speed"]
    .replace(["nan", "None", "null", ""], None)
    .isna()
    .sum()
)
    missing_road_type = int(
    roads["road_type"]
    .replace(["nan", "None", "null", ""], None)
    .isna()
    .sum()
)
    print(f"Missing road names: {missing_names}")
    print(f"Missing speed limits: {missing_speed}")
    print(f"Missing road types: {missing_road_type}")

    print("\n--- ROAD TYPES ---")
    print(roads["road_type"].value_counts().head(15))

    print("\n--- SAMPLE RECORDS ---")

    sample_columns = [
        "road_id",
        "osm_id",
        "road_name",
        "road_type",
        "oneway",
        "max_speed",
        "length_m",
    ]

    print(
        roads[sample_columns]
        .head(10)
        .to_string(index=False)
    )

    print("\n--- FINAL RESULT ---")

    errors = []

    if len(roads) != 1000:
        errors.append(
            f"Expected 1000 features but found {len(roads)}."
        )

    if roads.crs is None:
        errors.append("CRS is missing.")

    elif roads.crs.to_epsg() != 4326:
        errors.append(
            f"Expected EPSG:4326 but found {roads.crs}."
        )

    if missing_columns:
        errors.append(
            f"Missing required columns: {missing_columns}"
        )

    if empty_count > 0:
        errors.append(
            f"Dataset contains {empty_count} empty geometries."
        )

    if null_geometry_count > 0:
        errors.append(
            f"Dataset contains {null_geometry_count} null geometries."
        )

    if invalid_count > 0:
        errors.append(
            f"Dataset contains {invalid_count} invalid geometries."
        )

    if errors:
        print("Dataset validation failed:")

        for error in errors:
            print(f"- {error}")

        raise SystemExit(1)

    print("Dataset passed all essential validation checks.")

if __name__ == "__main__":
    main()