from uuid import uuid4

from minio import Minio

from app.core.config import settings
from app.storage.minio_client import client


def upload_file(file):
    extension = file.filename.split(".")[-1]
    object_name = f"{uuid4()}.{extension}"

    client.put_object(
        bucket_name=settings.minio_bucket,
        object_name=object_name,
        data=file.file,
        length=-1,
        part_size=10 * 1024 * 1024,
        content_type=file.content_type,
    )

    return {
    "filename": file.filename,
    "object_name": object_name,
    "content_type": file.content_type,
    }

def download_file(object_name: str):
    return client.get_object(
        settings.minio_bucket,
        object_name,
    )