"""
Response utilities for API Gateway Lambda proxy integration.
"""
import json
from typing import Any

from src.config import ALLOWED_ORIGIN


def api_response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    """
    Build a standard API Gateway proxy response with JSON body.

    Args:
        status_code: HTTP status code
        body: Response body (will be JSON serialized)

    Returns:
        API Gateway proxy response dictionary
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
        "body": json.dumps(body),
    }


def error_response(status_code: int, message: str) -> dict[str, Any]:
    """Build an error response."""
    return api_response(status_code, {"error": message})


def success_response(body: dict[str, Any]) -> dict[str, Any]:
    """Build a success response (200 OK)."""
    return api_response(200, body)
