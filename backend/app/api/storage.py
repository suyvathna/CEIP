from fastapi import APIRouter, UploadFile, File
from app.services.storage_service import upload_file

from app.storage.minio_client import client
from app.core.config import settings

router = APIRouter(prefix="/storage", tags=["Storage"])


@router.get("/health")
def storage_health():
    exists = client.bucket_exists(settings.minio_bucket)

    return {
        "connected": True,
        "bucket_exists": exists,
        "bucket": settings.minio_bucket,
    }

@router.post("/upload")
def upload(file: UploadFile = File(...)):
    object_name = upload_file(file)

    return {
        "uploaded": True,
        "object_name": object_name,
    }