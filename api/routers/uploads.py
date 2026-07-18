from fastapi import APIRouter, File, HTTPException, UploadFile

from api.services.upload_service import save_uploaded_file


router = APIRouter(
    prefix="/upload",
    tags=["Uploads"],
)


@router.post("")
async def upload_spatial_file(
    file: UploadFile = File(...),
):
    """Upload a GeoJSON file or Shapefile ZIP package."""

    try:
        saved_path, job_id = await save_uploaded_file(file)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except OSError as error:
        raise HTTPException(
            status_code=500,
            detail="The server could not save the uploaded file.",
        ) from error

    finally:
        await file.close()

    return {
        "job_id": job_id,
        "status": "QUEUED",
        "message": "File saved for ETL processing.",
        "internal_filename": saved_path.name,
        "file_type": saved_path.suffix.lower(),
    }