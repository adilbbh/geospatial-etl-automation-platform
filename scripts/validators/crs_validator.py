def validate_crs(geojson):
    errors = []

    crs = geojson.get("crs")

    if crs is None:
        # GeoJSON default assumption
        return errors

    crs_name = crs.get("properties", {}).get("name", "")

    if "4326" not in crs_name and "CRS84" not in crs_name:
        errors.append(f"Invalid CRS: {crs_name}. Expected EPSG:4326")

    return errors
