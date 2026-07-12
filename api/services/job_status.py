import json
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parents[2]
JOBS_DIR = PROJECT_DIR / "logs" / "jobs"


def update_job_status(
    job_id: str,
    status: str,
    filename: str,
    message: str = "",
) -> None:
    JOBS_DIR.mkdir(parents=True, exist_ok=True)

    job_data: dict[str, Any] = {
        "job_id": job_id,
        "filename": filename,
        "status": status,
        "message": message,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }

    job_file = JOBS_DIR / f"{job_id}.json"

    with job_file.open("w", encoding="utf-8") as file:
        json.dump(job_data, file, indent=2)


def get_job_status(job_id: str) -> dict[str, Any] | None:
    job_file = JOBS_DIR / f"{job_id}.json"

    if not job_file.exists():
        return None

    with job_file.open("r", encoding="utf-8") as file:
        return json.load(file)
