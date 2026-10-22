"""
HTTP response helpers for Lambda functions.

Provides standardized response builders with CORS headers and JSON formatting.
"""
import json
from typing import Any

from src.config.settings import CORS_ALLOWED_ORIGIN


def get_cors_headers(methods: str = "GET, OPTIONS") -> dict[str, str]:
    """
    Get standard CORS headers.

    Args:
        methods: HTTP methods to allow (default: GET, OPTIONS)

    Returns:
        Dictionary of CORS headers
    """
    return {
        "Access-Control-Allow-Origin": CORS_ALLOWED_ORIGIN,
        "Access-Control-Allow-Methods": methods,
        "Access-Control-Allow-Headers": "Content-Type"
    }


def success_response(
    data: dict[str, Any],
    methods: str = "GET, OPTIONS"
) -> dict[str, Any]:
    """
    Build a successful HTTP response.

    Args:
        data: Response data to serialize
        methods: HTTP methods for CORS (default: GET, OPTIONS)

    Returns:
        Lambda response dict with statusCode 200
    """
    return {
        "statusCode": 200,
        "headers": get_cors_headers(methods),
        "body": json.dumps(data, ensure_ascii=False)
    }


def error_response(
    message: str,
    status_code: int = 500,
    methods: str = "GET, OPTIONS"
) -> dict[str, Any]:
    """
    Build an error HTTP response.

    Args:
        message: Error message
        status_code: HTTP status code (default: 500)
        methods: HTTP methods for CORS (default: GET, OPTIONS)

    Returns:
        Lambda response dict with error details
    """
    return {
        "statusCode": status_code,
        "headers": get_cors_headers(methods),
        "body": json.dumps({"error": message})
    }


def validation_error(message: str, methods: str = "POST, OPTIONS") -> dict[str, Any]:
    """
    Build a 400 Bad Request response for validation errors.

    Args:
        message: Validation error message
        methods: HTTP methods for CORS

    Returns:
        Lambda response dict with statusCode 400
    """
    return error_response(message, status_code=400, methods=methods)


def not_found_error(message: str, methods: str = "GET, OPTIONS") -> dict[str, Any]:
    """
    Build a 404 Not Found response.

    Args:
        message: Not found error message
        methods: HTTP methods for CORS

    Returns:
        Lambda response dict with statusCode 404
    """
    return error_response(message, status_code=404, methods=methods)


def server_error(message: str, methods: str = "GET, OPTIONS") -> dict[str, Any]:
    """
    Build a 500 Internal Server Error response.

    Args:
        message: Error message
        methods: HTTP methods for CORS

    Returns:
        Lambda response dict with statusCode 500
    """
    return error_response(message, status_code=500, methods=methods)
