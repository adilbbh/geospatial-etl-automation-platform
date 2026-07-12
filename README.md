\# FME ETL Lab



\## Project path


F:\\DockerData\\09\_Projects\\FME\_ETL\_Lab


\## Activate Python environment


```powershell

cd F:\\DockerData\\09\_Projects\\FME\_ETL\_Lab

.\\.venv\\Scripts\\Activate.ps1

## Current architecture

```text
data/roads.geojson
        ↓
scripts/load_roads.py
        ↓
scripts/readers/geojson_reader.py
        ↓
scripts/validators/
        ↓
scripts/writers/postgis_writer.py
        ↓
PostGIS roads table
        ↓
FastAPI + GeoServer
        ↓
Leaflet map

File responsibilities
scripts/load_roads.py

Main ETL controller. It coordinates reading, validation, writing, logging, and reporting.

scripts/readers/geojson_reader.py

Reads GeoJSON input files.

scripts/validators/schema_validator.py

Checks required attributes: road_id, road_name, road_type.

scripts/validators/geometry_validator.py

Checks geometry exists and is LineString.

scripts/validators/attribute_validator.py

Checks allowed road_type values.

scripts/validators/duplicate_validator.py

Finds duplicate road_id values.

scripts/validators/crs_validator.py

Checks dataset CRS.

scripts/writers/postgis_writer.py

Writes valid features into PostGIS.

scripts/utils/logger.py

Writes ETL logs to logs/etl_log.txt.

scripts/utils/error_report.py

Writes rejected feature errors to logs/error_report.json.

scripts/utils/summary_report.py

Writes ETL summary to logs/summary_report.json

