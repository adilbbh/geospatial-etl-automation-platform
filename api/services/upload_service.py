from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from api.services.job_status import update_job_status


PROJECT_DIR = Path(__file__).resolve().parents[2]
INCOMING_DIR = PROJECT_DIR / "incoming"

ALLOWED_EXTENSIONS = {".geojson"}


def validate_upload_filename(filename: str | None) -> str:
    if not filename:
        raise ValueError("Uploaded file has no filename.")

    safe_filename = Path(filename).name
    suffix = Path(safe_filename).suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError(
            "Unsupported file type. Only .geojson files are allowed."
        )

    return safe_filename


async def save_uploaded_file(
    upload_file: UploadFile,
) -> tuple[Path, str]:
    INCOMING_DIR.mkdir(parents=True, exist_ok=True)

    safe_filename = validate_upload_filename(upload_file.filename)
    job_id = uuid4().hex

    original_path = Path(safe_filename)

    destination = INCOMING_DIR / (
        f"{job_id}__{original_path.name}"
    )

    content = await upload_file.read()

    if not content:
        raise ValueError("The uploaded file is empty.")

    destination.write_bytes(content)

    update_job_status(
        job_id=job_id,
        status="QUEUED",
        filename=original_path.name,
        message="File accepted and waiting for processing.",
    )

    return destination, job_id