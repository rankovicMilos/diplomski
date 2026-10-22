"""
Local filesystem version of S3Service (STORAGE_BACKEND=local).

Buckets are folders under LOCAL_DATA_DIR. Instead of an S3 presigned URL, PDF uploads get
a URL on the local upload server (PUT /local-upload/<key>), so the frontend upload flow
works unchanged.
"""
import logging
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from src.config import (
    LOCAL_DATA_DIR,
    LOCAL_UPLOAD_BASE_URL,
    PRESIGNED_URL_EXPIRATION,
    S3_BUCKET,
    FileTypeConfig,
)
from src.services.s3_service import PresignedUrlResult, S3Service

logger = logging.getLogger(__name__)


def local_path(bucket: str, key: str) -> Path:
    """Path of an object; keys cannot leave the bucket folder."""
    root = (LOCAL_DATA_DIR / bucket).resolve()
    path = (root / key).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"Key escapes the bucket folder: {key}")
    return path


class LocalStorageService(S3Service):
    """S3Service with the S3 calls replaced by file operations."""

    def __init__(self):  # no boto3 client
        pass

    def _generate_upload_url(
        self,
        filename: str,
        file_config: FileTypeConfig,
    ) -> PresignedUrlResult:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        key = self._generate_s3_key(filename, file_config.upload_prefix, timestamp)
        return PresignedUrlResult(
            upload_url=f"{LOCAL_UPLOAD_BASE_URL}/local-upload/{quote(key)}",
            key=key,
            bucket=S3_BUCKET,
            expires_in=PRESIGNED_URL_EXPIRATION,
        )

    def download_file(self, bucket: str, key: str) -> bytes:
        logger.info(f"Reading file {bucket}/{key}")
        return local_path(bucket, key).read_bytes()

    def upload_file(
        self,
        content: bytes,
        bucket: str,
        key: str,
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> str:
        path = local_path(bucket, key)
        logger.info(f"Writing file {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return key
