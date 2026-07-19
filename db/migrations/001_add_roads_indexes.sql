-- Indexes for filtering and spatial queries on the roads table.

CREATE INDEX IF NOT EXISTS idx_roads_road_type
ON public.roads (road_type);

-- Avoid creating a duplicate spatial index when GeoServer,
-- FME, or another loader has already created one.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_indexes
        WHERE schemaname = 'public'
          AND tablename = 'roads'
          AND indexdef ILIKE '%USING gist (geom)%'
    ) THEN
        EXECUTE '
            CREATE INDEX idx_roads_geom_gist
            ON public.roads
            USING gist (geom)
        ';
    END IF;
END
$$;

ANALYZE public.roads;
