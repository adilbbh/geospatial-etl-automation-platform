from fastapi import APIRouter, HTTPException, Query

from api.services.road_service import (
    get_roads_by_type_geojson,
    get_roads_geojson,
    get_roads_in_bbox_geojson,
)

router = APIRouter()


@router.get("/roads")
def get_roads():
    return get_roads_geojson()


@router.get("/roads/bbox")
def get_roads_in_bbox(
    min_lon: float = Query(..., ge=-180, le=180),
    min_lat: float = Query(..., ge=-90, le=90),
    max_lon: float = Query(..., ge=-180, le=180),
    max_lat: float = Query(..., ge=-90, le=90),
):
    """Return roads intersecting the requested map extent."""

    if min_lon >= max_lon:
        raise HTTPException(
            status_code=400,
            detail="min_lon must be smaller than max_lon.",
        )

    if min_lat >= max_lat:
        raise HTTPException(
            status_code=400,
            detail="min_lat must be smaller than max_lat.",
        )

    return get_roads_in_bbox_geojson(
        min_lon=min_lon,
        min_lat=min_lat,
        max_lon=max_lon,
        max_lat=max_lat,
    )


@router.get("/roads/type/{road_type}")
def get_roads_by_type(road_type: str):
    return get_roads_by_type_geojson(road_type)
