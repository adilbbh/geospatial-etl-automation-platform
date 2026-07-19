import psycopg2
from fastapi import APIRouter, HTTPException, status

from api.database import check_database_health

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("")
def api_health():
    """Confirm that the FastAPI application is running."""

    return {
        "status": "healthy",
        "service": "geospatial-api",
    }


@router.get("/database")
def database_health():
    """Confirm that PostgreSQL and PostGIS are available."""

    try:
        return check_database_health()

    except (RuntimeError, psycopg2.Error) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The database connection is unavailable.",
        ) from error
