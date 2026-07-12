# Geospatial ETL Automation Platform

A production-style geospatial data ingestion and processing platform built with Python, FastAPI, PostGIS, GeoServer, Docker, FME Form, and real-time file monitoring.

The project demonstrates how spatial datasets can be uploaded, validated, transformed, loaded into PostGIS, exposed through REST APIs, and visualized on an interactive Leaflet map.

## Architecture

```text
GeoJSON Upload
      │
      ▼
FastAPI Upload API
      │
      ▼
Incoming Folder
      │
      ▼
Real-Time Watchdog Service
      │
      ▼
FME / Python ETL Pipeline
      │
      ├── Schema validation
      ├── Attribute validation
      ├── CRS validation
      ├── Geometry validation
      └── Duplicate detection
      │
      ▼
PostGIS
      │
      ├── FastAPI REST API
      └── GeoServer WMS/WFS
      │
      ▼
Leaflet Web Map
```

## Main Features

- GeoJSON upload through FastAPI
- Real-time folder monitoring with Watchdog
- Automated FME command-line execution
- Python-based ETL pipeline
- Schema, attribute, CRS, geometry, and duplicate validation
- PostGIS spatial database integration
- GeoServer-ready database layers
- GeoJSON REST API responses
- Filtering roads by road type
- Interactive Leaflet map with feature popups
- ETL job tracking:
  - `QUEUED`
  - `PROCESSING`
  - `SUCCESS`
  - `FAILED`
- Timestamped archive and failed-file handling
- Docker-based local infrastructure
- Environment-variable configuration for credentials

## Technology Stack

| Area | Technology |
|---|---|
| Backend API | Python, FastAPI, Uvicorn |
| ETL | Python, FME Form |
| Spatial database | PostgreSQL, PostGIS |
| Map services | GeoServer |
| Web mapping | Leaflet |
| Automation | Watchdog, PowerShell |
| Infrastructure | Docker Compose |
| Data format | GeoJSON |

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Opens the Leaflet web map |
| `GET` | `/roads` | Returns all roads as a GeoJSON FeatureCollection |
| `GET` | `/roads/type/{road_type}` | Filters roads by road type |
| `POST` | `/upload` | Uploads a GeoJSON file for processing |
| `GET` | `/jobs/{job_id}` | Returns the current ETL job status |
| `GET` | `/docs` | Opens the Swagger API documentation |

## Project Structure

```text
geospatial-etl-automation-platform/
├── api/
│   ├── routers/
│   │   ├── jobs.py
│   │   ├── roads.py
│   │   └── uploads.py
│   ├── services/
│   │   ├── job_status.py
│   │   ├── road_service.py
│   │   └── upload_service.py
│   ├── static/
│   │   └── index.html
│   ├── database.py
│   └── main.py
├── data/
│   └── roads.geojson
├── scripts/
│   ├── readers/
│   ├── validators/
│   ├── writers/
│   ├── utils/
│   ├── load_roads.py
│   ├── watch_folder.py
│   └── watch_folder_realtime.py
├── .env.example
├── .gitignore
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/adilbbh/geospatial-etl-automation-platform.git
cd geospatial-etl-automation-platform
```

### 2. Create the environment file

Copy `.env.example` to `.env`.

PowerShell:

```powershell
Copy-Item .env.example .env
```

Update the values inside `.env` with your local credentials.

Never commit the real `.env` file.

### 3. Start Docker services

```powershell
docker compose --env-file .env up -d
```

Services:

| Service | Default address |
|---|---|
| PostGIS | `localhost:5433` |
| pgAdmin | `http://localhost:5050` |
| GeoServer | `http://localhost:8080/geoserver` |

### 4. Create and activate the Python environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 5. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 6. Load the sample roads

```powershell
python .\scripts\load_roads.py
```

### 7. Start the real-time watcher

Open a separate terminal:

```powershell
.\.venv\Scripts\Activate.ps1
python .\scripts\watch_folder_realtime.py
```

### 8. Start FastAPI

Open another terminal:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn api.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

## Example GeoJSON Schema

```json
{
  "type": "Feature",
  "properties": {
    "road_id": "R001",
    "road_name": "Main Street",
    "road_type": "primary"
  },
  "geometry": {
    "type": "LineString",
    "coordinates": [
      [19.944, 50.064],
      [19.950, 50.068]
    ]
  }
}
```

## ETL Validation

The Python pipeline separates responsibilities into reusable components:

| Component | Responsibility |
|---|---|
| `schema_validator.py` | Checks required attributes |
| `attribute_validator.py` | Checks valid attribute values |
| `geometry_validator.py` | Checks geometry presence and type |
| `crs_validator.py` | Checks the dataset coordinate system |
| `duplicate_validator.py` | Detects duplicate road identifiers |
| `postgis_writer.py` | Writes valid features to PostGIS |
| `error_report.py` | Records rejected features |
| `summary_report.py` | Produces ETL execution statistics |

## FME Integration

The project supports command-line execution of an FME workspace.

FME workspace files are excluded from this public repository because local FME workspaces may contain machine-specific paths and encrypted database connection details.

Users can provide their own workspace path through:

```powershell
$env:FME_WORKSPACE = "C:\path\to\roads_to_postgis.fmw"
.\scripts\run_fme_etl.ps1
```

FME Form must be installed separately.

## Security

- Real credentials are stored in `.env`
- `.env` is excluded through `.gitignore`
- `.env.example` contains placeholders only
- Database volumes and runtime files are not committed
- FME workspaces containing local connection details are excluded
- Uploaded, archived, failed, and log files are excluded

## Skills Demonstrated

- Geospatial ETL architecture
- Python application design
- REST API development
- PostGIS spatial SQL
- Docker-based infrastructure
- Real-time event-driven processing
- Spatial data validation
- GeoJSON processing
- GeoServer integration
- Web mapping with Leaflet
- Secure configuration management
- Job-status tracking and error handling

## Current Status

This project is under active development.

Planned improvements:

- ETL validation dashboard
- Multi-format spatial uploads
- Automated GeoServer publishing
- Authentication and authorization
- Automated testing
- CI/CD with GitHub Actions
- Cloud deployment

## Author

**Adil Nawaz**

Geospatial and GIS professional focused on spatial ETL, automation, APIs, PostGIS, GeoServer, Python, and cloud-native geospatial systems.