"""
Configuration loader for the ingestion Lambda.
Environment variables take precedence over YAML defaults.
"""
import os
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class FileTypeConfig:
    """Configuration for a supported file type."""

    content_type: str
    upload_prefix: str


def _load_yaml_config() -> dict:
    """Load configuration from YAML file."""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


_config = _load_yaml_config()

# S3 settings (env vars override YAML)
S3_BUCKET = (
    os.environ.get("S3_BUCKET")
    or os.environ.get("ORCHESTRATOR_DATA_BUCKET")
    or os.environ.get("CLIENT_DATA_BUCKET")
    or _config["s3"]["bucket"]
)
AWS_REGION = os.environ.get("AWS_REGION", _config["s3"]["region"])

# Storage backend: "local" keeps buckets as folders under LOCAL_DATA_DIR, "s3" uses AWS
STORAGE_BACKEND = os.environ.get("STORAGE_BACKEND", "local")
LOCAL_DATA_DIR = Path(os.environ.get("LOCAL_DATA_DIR", Path(__file__).resolve().parents[4] / "data"))
# With local storage, "presigned" upload URLs point at the local upload server
LOCAL_UPLOAD_BASE_URL = os.environ.get("LOCAL_UPLOAD_BASE_URL", "http://localhost:3000/api-proxy")

# CORS origin of the frontend
ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "http://localhost:3000")

# Presigned URL settings
PRESIGNED_URL_EXPIRATION = int(
    os.environ.get("PRESIGNED_URL_EXPIRATION", _config["presigned_url"]["expiration_seconds"])
)

# File type configurations
FILE_TYPES: dict[str, FileTypeConfig] = {
    name: FileTypeConfig(
        content_type=cfg["content_type"],
        upload_prefix=cfg["upload_prefix"],
    )
    for name, cfg in _config["file_types"].items()
}

# Current default (PDF only for now)
PDF_CONFIG = FILE_TYPES["pdf"]

# Excel configurations
XLSX_CONFIG = FILE_TYPES["xlsx"]
XLS_CONFIG = FILE_TYPES["xls"]
CSV_CONFIG = FILE_TYPES["csv"]

# Conversion settings
CONVERSION_OUTPUT_PREFIX = _config["conversion"]["output_prefix"]
CONVERSION_SOURCE_PREFIX = _config["conversion"]["source_prefix"]
SUPPORTED_EXCEL_EXTENSIONS = _config["conversion"]["supported_extensions"]
