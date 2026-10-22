"""
Parsing utilities for response processing.

Provides functions for extracting JSON from model responses and other parsing tasks.
"""
import json
import logging
import re
from typing import Any


logger = logging.getLogger(__name__)


def parse_model_response(response: dict[str, Any]) -> dict[str, Any]:
    """
    Parse the model response and extract JSON output.

    Handles cases where the model returns pure JSON or JSON wrapped in markdown.

    Args:
        response: Model response dict with output.text field

    Returns:
        Parsed JSON as dictionary, or error structure if parsing fails
    """
    output_text = response.get("output", {}).get("text", "")

    try:
        # Try direct JSON parse first
        return json.loads(output_text)
    except json.JSONDecodeError:
        # Try to find JSON within markdown code blocks
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', output_text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # If still can't parse, return the raw text wrapped in an error structure
        logger.warning(f"Could not parse JSON from response: {output_text[:500]}")
        return {
            "error": "Failed to parse JSON response",
            "raw_output": output_text
        }


def validate_uuid_format(value: str) -> bool:
    """
    Validate that a string matches UUID.json format.

    Args:
        value: String to validate

    Returns:
        True if valid UUID.json format, False otherwise
    """
    pattern = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\.json$'
    return bool(re.match(pattern, value))
