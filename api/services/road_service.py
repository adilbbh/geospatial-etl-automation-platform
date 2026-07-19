from api.database import get_connection


def get_roads_geojson():
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT json_build_object(
                'type', 'FeatureCollection',
                'features', COALESCE(
                    json_agg(
                        json_build_object(
                            'type', 'Feature',
                            'properties', json_build_object(
                                'road_id', road_id,
                                'road_name', road_name,
                                'road_type', road_type,
                                'source_file', source_file
                            ),
                            'geometry', ST_AsGeoJSON(geom)::json
                        )
                    ),
                    '[]'::json
                )
            )
            FROM roads;
            """)

        return cur.fetchone()[0]

    finally:
        cur.close()
        conn.close()


def get_roads_by_type_geojson(road_type):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT json_build_object(
                'type', 'FeatureCollection',
                'features', COALESCE(
                    json_agg(
                        json_build_object(
                            'type', 'Feature',
                            'properties', json_build_object(
                                'road_id', road_id,
                                'road_name', road_name,
                                'road_type', road_type,
                                'source_file', source_file
                            ),
                            'geometry', ST_AsGeoJSON(geom)::json
                        )
                    ),
                    '[]'::json
                )
            )
            FROM roads
            WHERE road_type = %s;
            """,
            (road_type,),
        )

        return cur.fetchone()[0]

    finally:
        cur.close()
        conn.close()


def get_roads_in_bbox_geojson(
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
):
    """Return roads intersecting a WGS84 bounding box."""

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT json_build_object(
                'type', 'FeatureCollection',
                'features', COALESCE(
                    json_agg(
                        json_build_object(
                            'type', 'Feature',
                            'properties', json_build_object(
                                'road_id', road_id,
                                'road_name', road_name,
                                'road_type', road_type,
                                'source_file', source_file
                            ),
                            'geometry', ST_AsGeoJSON(geom)::json
                        )
                    ),
                    '[]'::json
                )
            )
            FROM roads
            WHERE ST_Intersects(
                geom,
                ST_MakeEnvelope(
                    %s,
                    %s,
                    %s,
                    %s,
                    4326
                )::geography
            );
            """,
            (
                min_lon,
                min_lat,
                max_lon,
                max_lat,
            ),
        )

        return cur.fetchone()[0]

    finally:
        cur.close()
        conn.close()
