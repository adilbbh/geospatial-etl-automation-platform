REQUIRED_ATTRIBUTES = ["road_id", "road_name", "road_type"]


def validate_schema(feature):
    errors = []

    properties = feature.get("properties", {})

    for attribute in REQUIRED_ATTRIBUTES:
        if attribute not in properties:
            errors.append(f"Missing required attribute: {attribute}")

    return errors