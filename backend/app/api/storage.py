from fastapi import APIRouter

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