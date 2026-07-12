def find_duplicate_road_ids(features):
    seen = set()
    duplicates = set()

    for feature in features:
        road_id = feature.get("properties", {}).get("road_id")

        if road_id in seen:
            duplicates.add(road_id)
        else:
            seen.add(road_id)

    return duplicates