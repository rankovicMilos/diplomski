"""
Local filesystem storage (STORAGE_BACKEND=local), a drop-in for s3_service.

Buckets are folders under LOCAL_DATA_DIR and keys are paths inside them, so
s3://<bucket>/<key> becomes <LOCAL_DATA_DIR>/<bucket>/<key>.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config.settings import LOCAL_DATA_DIR, MARKET_ANALYSIS_BUCKET, OUTPUT_BUCKET


logger = logging.getLogger(__name__)


def _path(bucket: str, key: str) -> Path:
    root = (LOCAL_DATA_DIR / bucket).resolve()
    path = (root / key).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"Key escapes the bucket folder: {key}")
    return path


def read_file(bucket: str, key: str) -> str:
    """Read a file and return its contents as a UTF-8 string."""
    content = _path(bucket, key).read_text(encoding="utf-8")
    logger.info(f"Successfully read {bucket}/{key}")
    return content


def read_pdf(bucket: str, key: str) -> bytes:
    """Read a PDF file and return it as bytes."""
    content = _path(bucket, key).read_bytes()
    logger.info(f"Successfully read PDF {bucket}/{key}")
    return content


def read_json(bucket: str, key: str) -> dict[str, Any]:
    """Read a JSON file and parse it."""
    return json.loads(read_file(bucket, key))


def save_json(
    data: dict[str, Any],
    request_id: str,
    analysis_type: str,
    bucket: str | None = None
) -> str | None:
    """
    Save a dictionary as JSON to <analysis_type>/<request_id>.json.

    Returns:
        Path of the saved file
    """
    target_bucket = bucket or OUTPUT_BUCKET
    key = f"{analysis_type}/{request_id}.json"
    path = _path(target_bucket, key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    logger.info(f"Saved result to {path}")
    return str(path)


def list_json_files(
    bucket: str,
    prefix: str,
    limit: int | None = None
) -> list[dict[str, Any]]:
    """
    List JSON files under a key prefix, most recently modified first.

    Returns:
        List of file metadata dicts with keys: key, filename, last_modified, size
    """
    root = LOCAL_DATA_DIR / bucket
    if not root.is_dir():
        return []

    files = []
    for path in root.rglob("*.json"):
        key = path.relative_to(root).as_posix()
        if not key.startswith(prefix):
            continue
        stat = path.stat()
        files.append({
            "key": key,
            "filename": path.name,
            "last_modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            "size": stat.st_size,
        })

    files.sort(key=lambda x: x["last_modified"], reverse=True)
    return files[:limit] if limit else files


def read_json_metadata(key: str) -> dict | None:
    """Read a report from the output bucket and keep only the listing fields."""
    try:
        full_content = read_json(MARKET_ANALYSIS_BUCKET, key)
    except Exception as e:
        logger.warning(f"Failed to read content for {key}: {str(e)}")
        return None
    return {
        "nace_code": full_content.get("nace_code"),
        "analysis_id": full_content.get("analysis_id"),
        "market_analysis_id": full_content.get("market_analysis_id"),
        "client_name": full_content.get("client_name"),
    }


def fetch_files_with_metadata(
    bucket: str,
    prefix: str,
    limit: int = 10,
    client_name_filter: str | None = None,
    category_code_filter: str | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch file list with metadata content.

    Args:
        bucket: Bucket folder name
        prefix: Key prefix
        limit: Maximum number of files to process
        client_name_filter: Optional client name to filter by
        category_code_filter: Optional NACE code to filter by

    Returns:
        List of file dicts with content metadata included
    """
    files = list_json_files(bucket, prefix, limit=limit)
    for f in files:
        f["content"] = read_json_metadata(f["key"])

    if client_name_filter:
        files = [
            f for f in files
            if f.get("content") and f["content"].get("client_name") and
            client_name_filter.lower() in f["content"]["client_name"].lower()
        ]
        logger.info(f"Filtered to {len(files)} files matching clientName: {client_name_filter}")

    if category_code_filter:
        files = [
            f for f in files
            if f.get("content") and f["content"].get("nace_code") and
            category_code_filter.lower() in f["content"]["nace_code"].lower()
        ]
        logger.info(f"Filtered to {len(files)} files matching nace_code: {category_code_filter}")

    return files
