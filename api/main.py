import time
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from api.logging_config import get_request_logger
from api.routers.health import router as health_router
from api.routers.jobs import router as jobs_router
from api.routers.roads import router as roads_router
from api.routers.uploads import router as uploads_router

PROJECT_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = PROJECT_DIR / "api" / "static"
INDEX_FILE = STATIC_DIR / "index.html"

request_logger = get_request_logger()


app = FastAPI(
    title="Geospatial API",
    version="0.1.0",
)

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static",
)

app.include_router(health_router)
app.include_router(roads_router)
app.include_router(uploads_router)
app.include_router(jobs_router)


@app.middleware("http")
async def log_api_request(
    request: Request,
    call_next,
):
    """Log the result and processing time of every API request."""

    request_id = request.headers.get("X-Request-ID") or uuid4().hex

    start_time = time.perf_counter()

    client_ip = request.client.host if request.client else "unknown"

    try:
        response = await call_next(request)

    except Exception:
        duration_ms = round(
            (time.perf_counter() - start_time) * 1000,
            2,
        )

        request_logger.exception(
            "Request failed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": 500,
                "duration_ms": duration_ms,
                "client_ip": client_ip,
            },
        )

        raise

    duration_ms = round(
        (time.perf_counter() - start_time) * 1000,
        2,
    )

    response.headers["X-Request-ID"] = request_id

    request_logger.info(
        "Request completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "client_ip": client_ip,
        },
    )

    return response


@app.get("/", response_class=HTMLResponse)
def home():
    with INDEX_FILE.open("r", encoding="utf-8") as file:
        return file.read()
