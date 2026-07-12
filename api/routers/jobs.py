from fastapi import APIRouter, HTTPException

from api.services.job_status import get_job_status

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)


@router.get("/{job_id}")
def read_job_status(job_id: str):
    job = get_job_status(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found.",
        )

    return job
