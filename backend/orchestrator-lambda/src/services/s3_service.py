"""
S3 service for file operations.

Provides functions for reading, writing, and listing files in S3 buckets.
All S3 operations are centralized here for reusability and maintainability.
"""
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import boto3

from src.config.settings import (
    AWS_REGION,
    MARKET_ANALYSIS_BUCKET,
    OUTPUT_BUCKET,
)


logger = logging.getLogger(__name__)

# Initialize S3 client
s3_client = boto3.client("s3", region_name=AWS_REGION)


def read_file(bucket: str, key: str) -> str:
    """
    Read a file from S3 and return its contents as string.

    Args:
        bucket: S3 bucket name
        key: S3 object key

    Returns:
        File contents as UTF-8 string

    Raises:
        Exception: If file cannot be read
    """
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response["Body"].read().decode("utf-8")
        logger.info(f"Successfully read s3://{bucket}/{key}")
        return content
    except Exception as e:
        logger.error(f"Failed to read s3://{bucket}/{key}: {str(e)}")
        raise


def read_pdf(bucket: str, key: str) -> bytes:
    """
    Read a PDF file from S3 and return as bytes.

    Args:
        bucket: S3 bucket name
        key: S3 object key

    Returns:
        PDF file contents as bytes

    Raises:
        Exception: If file cannot be read
    """
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response["Body"].read()
        logger.info(f"Successfully read PDF s3://{bucket}/{key}")
        return content
    except Exception as e:
        logger.error(f"Failed to read PDF s3://{bucket}/{key}: {str(e)}")
        raise


def read_json(bucket: str, key: str) -> dict[str, Any]:
    """
    Read a JSON file from S3 and parse it.

    Args:
        bucket: S3 bucket name
        key: S3 object key

    Returns:
        Parsed JSON as dictionary

    Raises:
        Exception: If file cannot be read or parsed
    """
    content = read_file(bucket, key)
    return json.loads(content)


def save_json(
    data: dict[str, Any],
    request_id: str,
    analysis_type: str,
    bucket: str | None = None
) -> str | None:
    """
    Save a dictionary as JSON to S3.

    Args:
        data: Dictionary to save
        request_id: Unique request identifier (used in key)
        analysis_type: Type of analysis (used as prefix)
        bucket: Target bucket (defaults to OUTPUT_BUCKET)

    Returns:
        S3 URI of saved file, or None if OUTPUT_BUCKET not configured
    """
    target_bucket = bucket or OUTPUT_BUCKET
    if not target_bucket:
        logger.info("OUTPUT_BUCKET not configured, skipping S3 save")
        return None

    key = f"{analysis_type}/{request_id}.json"

    s3_client.put_object(
        Bucket=target_bucket,
        Key=key,
        Body=json.dumps(data, indent=2, ensure_ascii=False),
        ContentType="application/json"
    )

    logger.info(f"Saved result to s3://{target_bucket}/{key}")
    return f"s3://{target_bucket}/{key}"


def list_json_files(
    bucket: str,
    prefix: str,
    limit: int | None = None
) -> list[dict[str, Any]]:
    """
    List JSON files in an S3 bucket with given prefix.

    Args:
        bucket: S3 bucket name
        prefix: S3 key prefix to filter
        limit: Maximum number of files to return (sorted by last_modified desc)

    Returns:
        List of file metadata dicts with keys: key, filename, last_modified, size
    """
    files = []
    paginator = s3_client.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj.get("Key", "")
            if key.endswith(".json"):
                filename = key.split("/")[-1] if "/" in key else key
                files.append({
                    "key": key,
                    "filename": filename,
                    "last_modified": obj.get("LastModified").isoformat() if obj.get("LastModified") else None,
                    "size": obj.get("Size", 0),
                })

    # Sort by last_modified descending (most recent first)
    files.sort(key=lambda x: x.get("last_modified") or "", reverse=True)

    if limit:
        files = files[:limit]

    return files


def read_json_metadata(key: str) -> dict | None:
    """
    Read JSON file from S3 and extract only metadata fields.

    Thread-safe for use with ThreadPoolExecutor.
    Memory-optimized: extracts only metadata, not full content.

    Args:
        key: S3 object key to fetch

    Returns:
        Dict with metadata fields or None if read fails
    """
    response = None
    try:
        response = s3_client.get_object(Bucket=MARKET_ANALYSIS_BUCKET, Key=key)
        content_str = response["Body"].read().decode("utf-8")
        full_content = json.loads(content_str)
        content = {
            "nace_code": full_content.get("nace_code"),
            "analysis_id": full_content.get("analysis_id"),
            "market_analysis_id": full_content.get("market_analysis_id"),
            "client_name": full_content.get("client_name"),
        }
        del full_content
        return content
    except Exception as e:
        logger.warning(f"Failed to read content for {key}: {str(e)}")
        return None
    finally:
        if response and "Body" in response:
            response["Body"].close()


def fetch_files_with_metadata(
    bucket: str,
    prefix: str,
    limit: int = 10,
    client_name_filter: str | None = None,
    category_code_filter: str | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch file list with metadata content in parallel.

    Args:
        bucket: S3 bucket name
        prefix: S3 key prefix
        limit: Maximum number of files to process
        client_name_filter: Optional client name to filter by
        category_code_filter: Optional NACE code to filter by

    Returns:
        List of file dicts with content metadata included
    """
    files = list_json_files(bucket, prefix, limit=limit)

    # Fetch content in parallel using ThreadPoolExecutor
    json_keys = [f["key"] for f in files]
    with ThreadPoolExecutor(max_workers=10) as executor:
        contents = list(executor.map(read_json_metadata, json_keys))

    # Merge content into files
    for f, content in zip(files, contents):
        f["content"] = content

    # Filter by clientName if provided
    if client_name_filter:
        files = [
            f for f in files
            if f.get("content") and f["content"].get("client_name") and
            client_name_filter.lower() in f["content"]["client_name"].lower()
        ]
        logger.info(f"Filtered to {len(files)} files matching clientName: {client_name_filter}")

    # Filter by category_code_filter (nace_code) if provided
    if category_code_filter:
        files = [
            f for f in files
            if f.get("content") and f["content"].get("nace_code") and
            category_code_filter.lower() in f["content"]["nace_code"].lower()
        ]
        logger.info(f"Filtered to {len(files)} files matching nace_code: {category_code_filter}")

    return files
