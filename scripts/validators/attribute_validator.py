ALLOWED_ROAD_TYPES = ["primary", "secondary", "residential", "motorway"]


def validate_attributes(feature):
    errors = []

    properties = feature.get("properties", {})
    road_type = properties.get("road_type")

    if road_type not in ALLOWED_ROAD_TYPES:
        errors.append(
            f"Invalid road_type: {road_type}. Allowed values: {ALLOWED_ROAD_TYPES}"
        )

    return errors