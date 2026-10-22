"""S3 storage backend."""
import logging
import os
from typing import Any, Optional
from urllib.parse import quote

from botocore.exceptions import ClientError

from ..exceptions import ConfigError
from .base import METADATA_SUFFIX, BaseStorage
from .factory import StorageFactory

logger = logging.getLogger(__name__)

# S3 user metadata must be ASCII and the whole header block is limited to 2 KB,
# so values are URL-encoded and truncated. Full metadata lives in the sidecar file.
MAX_METADATA_VALUE_LENGTH = 200


@StorageFactory.register("s3")
class S3Storage(BaseStorage):
    def __init__(self, bucket: Optional[str] = None, prefix: str = ""):
        self.bucket = bucket or os.environ.get("RAW_DATA_BUCKET")
        if not self.bucket:
            raise ConfigError("S3 storage requires a bucket (RAW_DATA_BUCKET env var)")
        self.prefix = prefix.strip("/")

        import boto3
        self.client = boto3.client("s3")

    def find(self, stem: str) -> Optional[str]:
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket, Prefix=self._full_key(stem) + ".", MaxKeys=10
            )
        except ClientError as e:
            if e.response["Error"]["Code"] != "AccessDenied":
                raise
            # Without s3:ListBucket existing documents cannot be looked up: treat as not stored
            logger.warning(f"Cannot list s3://{self.bucket} (no s3:ListBucket); "
                           f"treating {stem} as not stored")
            return None
        for obj in response.get("Contents", []):
            if not obj["Key"].endswith(METADATA_SUFFIX):
                return obj["Key"]
        return None

    def read(self, key: str) -> Optional[bytes]:
        try:
            return self.client.get_object(Bucket=self.bucket, Key=self._full_key(key))["Body"].read()
        except self.client.exceptions.NoSuchKey:
            return None

    def _write(self, key: str, content: bytes, content_type: str, metadata: dict[str, Any]) -> str:
        full_key = self._full_key(key)
        self.client.put_object(
            Bucket=self.bucket,
            Key=full_key,
            Body=content,
            ContentType=content_type,
            Metadata={k: self._encode(v) for k, v in metadata.items()},
        )
        return f"s3://{self.bucket}/{full_key}"

    def _full_key(self, key: str) -> str:
        return f"{self.prefix}/{key}" if self.prefix else key

    @staticmethod
    def _encode(value: Any) -> str:
        text = ",".join(map(str, value)) if isinstance(value, list) else str(value)
        return quote(text[:MAX_METADATA_VALUE_LENGTH], safe=" /:.,-_")
