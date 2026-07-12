from api.database import get_connection


def get_roads_geojson():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT json_build_object(
            'type', 'FeatureCollection',
            'features', COALESCE(json_agg(
                json_build_object(
                    'type', 'Feature',
                    'properties', json_build_object(
                        'road_id', road_id,
                        'street_name', street_name,
                        'road_type', road_type
                    ),
                    'geometry', ST_AsGeoJSON(geom)::json
                )
            ), '[]'::json)
        )
        FROM roads;
    """)

    result = cur.fetchone()[0]
    cur.close()
    conn.close()
    return result


def get_roads_by_type_geojson(road_type):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT json_build_object(
            'type', 'FeatureCollection',
            'features', COALESCE(json_agg(
                json_build_object(
                    'type', 'Feature',
                    'properties', json_build_object(
                        'road_id', road_id,
                        'street_name', street_name,
                        'road_type', road_type
                    ),
                    'geometry', ST_AsGeoJSON(geom)::json
                )
            ), '[]'::json)
        )
        FROM roads
        WHERE road_type = %s;
    """,
        (road_type,),
    )

    result = cur.fetchone()[0]
    cur.close()
    conn.close()
    return result
