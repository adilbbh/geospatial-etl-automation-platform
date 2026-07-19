from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from api.routers.health import router as health_router
from api.routers.jobs import router as jobs_router
from api.routers.roads import router as roads_router
from api.routers.uploads import router as uploads_router

PROJECT_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = PROJECT_DIR / "api" / "static"
INDEX_FILE = STATIC_DIR / "index.html"


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


@app.get("/", response_class=HTMLResponse)
def home():
    with INDEX_FILE.open("r", encoding="utf-8") as file:
        return file.read()
