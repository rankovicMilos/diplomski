"""
S3 service for generating presigned upload URLs and file operations.
"""
import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import boto3
from botocore.config import Config

from src.config import (
    AWS_REGION,
    CONVERSION_OUTPUT_PREFIX,
    CSV_CONFIG,
    PDF_CONFIG,
    PRESIGNED_URL_EXPIRATION,
    S3_BUCKET,
    STORAGE_BACKEND,
    FileTypeConfig,
)

logger = logging.getLogger(__name__)


@dataclass
class PresignedUrlResult:
    """Result of presigned URL generation."""

    upload_url: str
    key: str
    bucket: str
    expires_in: int


class S3Service:
    """Service for S3 operations."""

    def __init__(self):
        self._client = boto3.client(
            "s3",
            region_name=AWS_REGION,
            config=Config(signature_version="s3v4"),
        )

    def generate_pdf_upload_url(self, filename: str) -> PresignedUrlResult:
        """
        Generate a presigned URL for uploading a PDF file.

        Args:
            filename: Original filename from the client

        Returns:
            PresignedUrlResult with upload URL and metadata
        """
        return self._generate_upload_url(filename, PDF_CONFIG)

    def _generate_upload_url(
        self,
        filename: str,
        file_config: FileTypeConfig,
    ) -> PresignedUrlResult:
        """
        Generate a presigned URL for uploading a file.

        Args:
            filename: Original filename from the client
            file_config: Configuration for the file type

        Returns:
            PresignedUrlResult with upload URL and metadata
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        s3_key = self._generate_s3_key(filename, file_config.upload_prefix, timestamp)

        upload_url = self._client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": S3_BUCKET,
                "Key": s3_key,
                "ContentType": file_config.content_type,
                "Metadata": {
                    "original_filename": filename,
                    "upload_timestamp": timestamp,
                },
            },
            ExpiresIn=PRESIGNED_URL_EXPIRATION,
        )

        return PresignedUrlResult(
            upload_url=upload_url,
            key=s3_key,
            bucket=S3_BUCKET,
            expires_in=PRESIGNED_URL_EXPIRATION,
        )

    def download_file(self, bucket: str, key: str) -> bytes:
        """
        Download a file from S3.

        Args:
            bucket: S3 bucket name
            key: S3 object key

        Returns:
            File content as bytes
        """
        logger.info(f"Downloading file from s3://{bucket}/{key}")
        response = self._client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()

    def upload_file(
        self,
        content: bytes,
        bucket: str,
        key: str,
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """
        Upload a file to S3.

        Args:
            content: File content as bytes
            bucket: S3 bucket name
            key: S3 object key
            content_type: MIME type of the file
            metadata: Optional metadata to attach to the object

        Returns:
            S3 key of the uploaded file
        """
        logger.info(f"Uploading file to s3://{bucket}/{key}")
        put_params = {
            "Bucket": bucket,
            "Key": key,
            "Body": content,
            "ContentType": content_type,
        }
        if metadata:
            put_params["Metadata"] = metadata

        self._client.put_object(**put_params)
        return key

    def upload_csv(
        self,
        csv_content: bytes,
        original_filename: str,
        original_key: str,
    ) -> str:
        """
        Upload a converted CSV file to S3.

        Args:
            csv_content: CSV content as bytes
            original_filename: Original Excel filename
            original_key: Original S3 key of the Excel file

        Returns:
            S3 key of the uploaded CSV file
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        csv_filename = original_filename.rsplit(".", 1)[0] + ".csv"
        csv_key = f"{CONVERSION_OUTPUT_PREFIX}/{csv_filename}"

        metadata = {
            "original_filename": original_filename,
            "original_s3_key": original_key,
            "conversion_timestamp": timestamp,
        }

        return self.upload_file(
            content=csv_content,
            bucket=S3_BUCKET,
            key=csv_key,
            content_type=CSV_CONFIG.content_type,
            metadata=metadata,
        )

    def _generate_s3_key(
        self,
        filename: str,
        prefix: str,
        timestamp: str,
        extension: str | None = None,
    ) -> str:
        """
        Generate a unique S3 key for the uploaded file.

        Format: {prefix}/{base_name}_{timestamp}_{hash}.{ext}
        """
        # Strip extension if present to avoid duplication
        if "." in filename:
            base_name, original_ext = filename.rsplit(".", 1)
            ext = extension if extension else f".{original_ext}"
        else:
            base_name = filename
            ext = extension if extension else ".pdf"

        name_hash = hashlib.md5(f"{filename}{timestamp}".encode("utf-8")).hexdigest()[:8]
        return f"{prefix}/{base_name}_{timestamp}_{name_hash}{ext}"


def _create_service() -> S3Service:
    if STORAGE_BACKEND == "local":
        from src.services.local_storage_service import LocalStorageService

        return LocalStorageService()
    return S3Service()


# Singleton instance for Lambda reuse
s3_service = _create_service()
