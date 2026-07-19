from fastapi.testclient import TestClient

import api.routers.roads as roads_router
from api.main import app

client = TestClient(app)

EMPTY_FEATURE_COLLECTION = {
    "type": "FeatureCollection",
    "features": [],
}


def test_bbox_endpoint_returns_geojson(monkeypatch):
    captured_parameters = {}

    def fake_bbox_service(
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
    ):
        captured_parameters.update(
            {
                "min_lon": min_lon,
                "min_lat": min_lat,
                "max_lon": max_lon,
                "max_lat": max_lat,
            }
        )

        return EMPTY_FEATURE_COLLECTION

    monkeypatch.setattr(
        roads_router,
        "get_roads_in_bbox_geojson",
        fake_bbox_service,
    )

    response = client.get(
        "/roads/bbox",
        params={
            "min_lon": -97.76,
            "min_lat": 30.25,
            "max_lon": -97.72,
            "max_lat": 30.29,
        },
    )

    assert response.status_code == 200
    assert response.json() == EMPTY_FEATURE_COLLECTION

    assert captured_parameters == {
        "min_lon": -97.76,
        "min_lat": 30.25,
        "max_lon": -97.72,
        "max_lat": 30.29,
    }


def test_bbox_rejects_reversed_longitude():
    response = client.get(
        "/roads/bbox",
        params={
            "min_lon": -97.70,
            "min_lat": 30.25,
            "max_lon": -97.76,
            "max_lat": 30.29,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == ("min_lon must be smaller than max_lon.")


def test_bbox_rejects_reversed_latitude():
    response = client.get(
        "/roads/bbox",
        params={
            "min_lon": -97.76,
            "min_lat": 30.30,
            "max_lon": -97.72,
            "max_lat": 30.29,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == ("min_lat must be smaller than max_lat.")


def test_bbox_rejects_longitude_outside_valid_range():
    response = client.get(
        "/roads/bbox",
        params={
            "min_lon": -181,
            "min_lat": 30.25,
            "max_lon": -97.72,
            "max_lat": 30.29,
        },
    )

    assert response.status_code == 422


def test_roads_by_type_endpoint(monkeypatch):
    expected_response = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "road_id": "10",
                    "road_name": "Example Motorway",
                    "road_type": "motorway",
                    "source_file": "test.geojson",
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [-97.75, 30.26],
                        [-97.74, 30.27],
                    ],
                },
            }
        ],
    }

    monkeypatch.setattr(
        roads_router,
        "get_roads_by_type_geojson",
        lambda road_type: expected_response,
    )

    response = client.get("/roads/type/motorway")

    assert response.status_code == 200
    assert response.json() == expected_response
