def validate_geometry(feature):
    errors = []

    geometry = feature.get("geometry")

    if geometry is None:
        errors.append("Missing geometry")
        return errors

    if geometry.get("type") != "LineString":
        errors.append("Geometry must be LineString")

    coordinates = geometry.get("coordinates", [])

    if len(coordinates) < 2:
        errors.append("LineString must have at least 2 coordinates")

    return errors
