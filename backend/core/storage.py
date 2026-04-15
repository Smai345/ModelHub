"""
MinIO object storage service for model artifacts and datasets.
"""
from __future__ import annotations

import io
import structlog
from typing import Optional, BinaryIO
from minio import Minio
from minio.error import S3Error

from backend.core.config import settings

log = structlog.get_logger()

_client: Optional[Minio] = None


def get_minio_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        _ensure_buckets(_client)
    return _client


def _ensure_buckets(client: Minio) -> None:
    for bucket in (settings.MINIO_BUCKET_MODELS, settings.MINIO_BUCKET_DATASETS):
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
            log.info("Created MinIO bucket", bucket=bucket)


def upload_model(
    data: BinaryIO,
    object_name: str,
    length: int,
    content_type: str = "application/octet-stream",
    bucket: str = None,
) -> str:
    """Upload model artifact; returns full object path."""
    bucket = bucket or settings.MINIO_BUCKET_MODELS
    client = get_minio_client()
    client.put_object(
        bucket_name=bucket,
        object_name=object_name,
        data=data,
        length=length,
        content_type=content_type,
    )
    log.info("Model uploaded", bucket=bucket, object=object_name, size=length)
    return f"{bucket}/{object_name}"


def download_model(object_path: str) -> bytes:
    """Download model artifact. object_path = 'bucket/object_name'."""
    parts = object_path.split("/", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid object path: {object_path}")
    bucket, object_name = parts
    client = get_minio_client()
    response = client.get_object(bucket, object_name)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def delete_model(object_path: str) -> None:
    parts = object_path.split("/", 1)
    if len(parts) != 2:
        return
    bucket, object_name = parts
    client = get_minio_client()
    try:
        client.remove_object(bucket, object_name)
        log.info("Model deleted", bucket=bucket, object=object_name)
    except S3Error as e:
        log.warning("Failed to delete model", error=str(e))


def get_presigned_url(object_path: str, expires_seconds: int = 3600) -> str:
    """Generate a presigned download URL."""
    from datetime import timedelta
    parts = object_path.split("/", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid object path: {object_path}")
    bucket, object_name = parts
    client = get_minio_client()
    return client.presigned_get_object(
        bucket, object_name, expires=timedelta(seconds=expires_seconds)
    )
