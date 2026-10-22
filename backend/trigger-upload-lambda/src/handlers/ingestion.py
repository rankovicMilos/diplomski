"""
Ingestion Lambda handler for file uploads and Excel to CSV conversion.

Trigger: API Gateway (Lambda proxy integration)

Usage (frontend):
1. For Excel files - send POST with base64 encoded file:
   {
       "filename": "data.xlsx",
       "file_content": "<base64 encoded file content>"
   }
   Returns: { "csv_key": "...", "rows_processed": 123 }

2. For PDF files - send POST to get presigned URL:
   {
       "filename": "report.pdf"
   }
   Returns: { "upload_url": "...", "key": "..." }
"""
import base64
import json
import logging
from typing import Any

from src.config import S3_BUCKET, SUPPORTED_EXCEL_EXTENSIONS
from src.services import excel_processor, s3_service
from src.utils import error_response, success_response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Handle API Gateway event.

    For Excel files: receives file content, converts to CSV, uploads to S3.
    For PDF files: generates presigned URL for direct upload.

    Args:
        event: API Gateway proxy event
        context: Lambda context (unused)

    Returns:
        API Gateway proxy response
    """
    # Handle CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return success_response({})

    # Only allow POST
    if event.get("httpMethod") != "POST":
        return error_response(405, "Method not allowed. Use POST.")

    # Validate bucket configuration
    if not S3_BUCKET:
        return error_response(500, "S3_BUCKET environment variable not configured")

    # Parse request body
    try:
        body_str = event.get("body") or "{}"
        body = json.loads(body_str)
    except json.JSONDecodeError as e:
        return error_response(400, f"Invalid JSON body: {e}")

    # Validate required fields
    filename = body.get("filename")
    if not filename or not isinstance(filename, str):
        return error_response(400, "Field 'filename' is required and must be a string.")

    lower_filename = filename.lower()

    # Route based on file type
    if any(lower_filename.endswith(ext) for ext in SUPPORTED_EXCEL_EXTENSIONS):
        return _handle_excel_upload(filename, body)
    elif lower_filename.endswith(".pdf"):
        return _handle_pdf_presigned_url(filename)
    else:
        return error_response(
            400,
            f"Unsupported file type. Supported: .pdf, {', '.join(SUPPORTED_EXCEL_EXTENSIONS)}",
        )


def _handle_excel_upload(filename: str, body: dict[str, Any]) -> dict[str, Any]:
    """
    Handle Excel file upload - convert to CSV and store in S3.

    Supports two input modes:
    1. file_content (base64) - frontend sends file in request
    2. s3_key - for testing, file already uploaded to S3

    Args:
        filename: Original filename
        body: Request body containing file_content or s3_key

    Returns:
        API Gateway proxy response with CSV location
    """
    file_content_b64 = body.get("file_content")
    s3_key = body.get("s3_key")

    if not file_content_b64 and not s3_key:
        return error_response(
            400,
            "Either 'file_content' (base64) or 's3_key' is required.",
        )

    try:
        if s3_key:
            # Download from S3 (for testing)
            logger.info(f"Downloading Excel from S3: {s3_key}")
            excel_content = s3_service.download_file(S3_BUCKET, s3_key)
            original_key = s3_key
        else:
            # Decode base64 (for frontend)
            excel_content = base64.b64decode(file_content_b64)
            original_key = filename

        logger.info(f"Processing Excel file: {filename}, size: {len(excel_content)} bytes")

        # Convert to CSV
        conversion_result = excel_processor.process_excel_to_csv(
            excel_content=excel_content,
            filename=filename,
        )

        # Upload CSV to S3
        csv_key = s3_service.upload_csv(
            csv_content=conversion_result.csv_content,
            original_filename=filename,
            original_key=original_key,
        )

        logger.info(
            f"Successfully converted {filename} to {csv_key}, "
            f"rows: {conversion_result.rows_processed}"
        )

        return success_response({
            "status": "success",
            "csv_key": csv_key,
            "bucket": S3_BUCKET,
        })

    except ValueError as e:
        # Client errors (validation failures - e.g., file too large, unsupported format)
        logger.warning(f"Validation error: {e}")
        return error_response(400, str(e))
    except Exception as e:
        # Server errors - don't expose internal details to client
        logger.error(f"Failed to process Excel file: {e}", exc_info=True)
        return error_response(500, "Failed to process Excel file. Please contact support.")


def _handle_pdf_presigned_url(filename: str) -> dict[str, Any]:
    """
    Handle PDF file - generate presigned URL for direct upload.

    Args:
        filename: Original filename

    Returns:
        API Gateway proxy response with presigned URL
    """
    try:
        result = s3_service.generate_pdf_upload_url(filename)

        return success_response({
            "upload_url": result.upload_url,
            "key": result.key,
            "bucket": result.bucket,
            "expires_in": result.expires_in,
        })

    except Exception as e:
        # Server errors - don't expose internal details to client
        logger.error(f"Failed to generate presigned URL: {e}", exc_info=True)
        return error_response(500, "Failed to generate presigned URL. Please contact support.")
