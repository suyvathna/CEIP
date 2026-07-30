import hashlib
from io import BytesIO
from uuid import uuid4

from minio import Minio

from app.core.config import settings
from app.storage.minio_client import client


def upload_file(file):
    extension = file.filename.split(".")[-1]
    object_name = f"{uuid4()}.{extension}"

    # Read the whole file into memory to hash it before it ever reaches
    # storage - this is what lets the platform later prove a piece of
    # evidence is byte-for-byte what was originally submitted (see
    # Evidence.sha256_hash). Fine for the photo/PDF/document sizes this
    # platform deals with; a very large-file use case would want a
    # streaming hash instead.
    data = file.file.read()
    sha256_hash = hashlib.sha256(data).hexdigest()

    client.put_object(
        bucket_name=settings.minio_bucket,
        object_name=object_name,
        data=BytesIO(data),
        length=len(data),
        content_type=file.content_type,
    )

    return {
        "filename": file.filename,
        "object_name": object_name,
        "content_type": file.content_type,
        "sha256_hash": sha256_hash,
    }

def download_file(object_name: str):
    return client.get_object(
        settings.minio_bucket,
        object_name,
    )

def delete_file(object_name: str):
    client.remove_object(
        settings.minio_bucket,
        object_name,
    )
