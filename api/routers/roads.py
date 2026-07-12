from fastapi import APIRouter
from api.services.road_service import get_roads_geojson, get_roads_by_type_geojson

router = APIRouter()


@router.get("/roads")
def get_roads():
    return get_roads_geojson()


@router.get("/roads/type/{road_type}")
def get_roads_by_type(road_type: str):
    return get_roads_by_type_geojson(road_type)
