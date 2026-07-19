from fastapi.testclient import TestClient

import api.routers.health as health_router
from api.main import app

client = TestClient(app)


def test_api_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "geospatial-api",
    }


def test_database_health(monkeypatch):
    expected_response = {
        "status": "healthy",
        "database": "gis",
        "postgis_version": "3.4",
    }

    monkeypatch.setattr(
        health_router,
        "check_database_health",
        lambda: expected_response,
    )

    response = client.get("/health/database")

    assert response.status_code == 200
    assert response.json() == expected_response


def test_database_health_returns_503(monkeypatch):
    def raise_database_error():
        raise RuntimeError("Database unavailable")

    monkeypatch.setattr(
        health_router,
        "check_database_health",
        raise_database_error,
    )

    response = client.get("/health/database")

    assert response.status_code == 503
    assert response.json()["detail"] == ("The database connection is unavailable.")


def test_response_contains_request_id():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers.get("X-Request-ID")


def test_existing_request_id_is_reused():
    request_id = "interview-test-request-123"

    response = client.get(
        "/health",
        headers={
            "X-Request-ID": request_id,
        },
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id
