ALLOWED_ROAD_TYPES = {
    "motorway",
    "motorway_link",
    "primary",
    "primary_link",
    "secondary",
    "secondary_link",
    "tertiary",
    "residential",
    "unclassified",
    "living_street",
}


def validate_attributes(feature):
    errors = []

    properties = feature.get("properties", {})
    road_type = properties.get("road_type")

    if not isinstance(road_type, str) or not road_type.strip():
        errors.append("road_type must contain a value")
        return errors

    # Some OSM records contain combined values such as:
    # "secondary, secondary_link"
    road_types = {value.strip() for value in road_type.split(",") if value.strip()}

    invalid_types = sorted(road_types - ALLOWED_ROAD_TYPES)

    if invalid_types:
        errors.append(
            "Invalid road_type value(s): "
            f"{invalid_types}. "
            f"Allowed values: {sorted(ALLOWED_ROAD_TYPES)}"
        )

    return errors
