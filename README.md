# Geospatial ETL Automation Platform

A practical geospatial data-processing project built with Python, FastAPI, PostGIS, GeoServer, Docker, Leaflet, GeoPandas, OSMnx, Watchdog, and FME Form.

The platform processes road datasets from source files to a web map. It includes data ingestion, validation, database loading, API access, map services, and visualization.

## Workflow

```text
Shapefile ZIP / GeoJSON
        ↓
Python or FME ETL
        ↓
Schema, CRS, attribute and geometry validation
        ↓
PostGIS
        ↓
FastAPI and GeoServer
        ↓
Leaflet web map
```

## Current Dataset

The current version uses approximately 1,000 OpenStreetMap road segments from Austin, Texas.

The dataset is:

* downloaded with OSMnx;
* exported as a Shapefile ZIP;
* extracted and validated;
* converted to EPSG:4326;
* loaded into PostGIS;
* exposed through FastAPI and GeoServer;
* displayed on a Leaflet map.

Road data © OpenStreetMap contributors.

## Main Features

* Shapefile ZIP and GeoJSON processing
* Schema and attribute validation
* CRS validation and transformation
* Geometry validation
* Duplicate road-ID detection
* Accepted and rejected data handling
* PostGIS integration
* FastAPI GeoJSON endpoints
* GeoServer WMS and WFS services
* Leaflet web visualization
* Road filtering by type
* Real-time folder monitoring
* Optional FME integration
* Docker-based local environment
* ETL job-status tracking

## Technology Stack

| Area               | Technology                |
| ------------------ | ------------------------- |
| Backend            | Python, FastAPI           |
| Spatial processing | GeoPandas, Shapely, OSMnx |
| Database           | PostgreSQL, PostGIS       |
| Map services       | GeoServer                 |
| Web map            | Leaflet                   |
| Automation         | Watchdog, PowerShell      |
| ETL                | Python, FME Form          |
| Infrastructure     | Docker Compose            |

## API Endpoints

| Endpoint                  | Description            |
| ------------------------- | ---------------------- |
| `/`                       | Leaflet web map        |
| `/roads`                  | All roads as GeoJSON   |
| `/roads/type/{road_type}` | Roads filtered by type |
| `/upload`                 | GeoJSON upload         |
| `/jobs/{job_id}`          | ETL job status         |
| `/docs`                   | Swagger documentation  |

## Project Structure

```text
api/          FastAPI routes, services and Leaflet page
data/         Source, processed, sample and rejected datasets
scripts/      Download, ingestion, validation and loading scripts
tests/        Automated tests
docker/       Local infrastructure configuration
```

## Run Locally

```powershell
docker compose up -d
pip install -r requirements.txt
python scripts\download_osm_roads.py
python scripts\ingest_shapefile_zip.py
python scripts\load_roads.py
python -m uvicorn api.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

## Current Status

The complete Austin road workflow is working successfully:

* 1,000 road features processed
* 1,000 records loaded into PostGIS
* 0 invalid geometries
* FastAPI endpoints working
* GeoServer WMS and WFS working
* Leaflet map working

## Planned Improvements

* In Progress

## Author

**Adil Nawaz**

Geospatial professional focused on spatial ETL, Python automation, PostGIS, GeoServer, FME, APIs, and web mapping.
