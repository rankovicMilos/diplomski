"""
API handlers for GET endpoints.

Provides handlers for listing and retrieving analyses from S3.
"""
import logging
import re
import urllib.parse

from src.config.settings import MARKET_ANALYSIS_BUCKET
from src.services import storage
from src.utils.response import (
    success_response,
    validation_error,
    not_found_error,
    server_error,
)
from src.utils.parsers import validate_uuid_format


logger = logging.getLogger(__name__)

# Industry ids are the source YAML names (see services/industry_config.py)
INDUSTRY_ID_PATTERN = re.compile(r"[a-z0-9_]+")


def get_analyses(event: dict, context) -> dict:
    """
    List all JSON files in the market_position directory.

    Expected event structure:
    {
        "action": "list_market_position_files",
        "queryStringParameters": {
            "clientName": "optional client name filter",
            "category": "optional NACE code filter"
        }
    }

    Returns:
    {
        "statusCode": 200,
        "body": {
            "files": [...],
            "count": 5,
            "bucket": "...",
            "prefix": "market_position/"
        }
    }
    """
    prefix = "market_position/"

    query_params = event.get("queryStringParameters") or {}
    client_name = query_params.get("clientName")
    category_code = query_params.get("category")
    logger.info(f"clientName query parameter: {client_name}")
    logger.info(f"category query parameter: {category_code}")

    try:
        files = storage.fetch_files_with_metadata(
            bucket=MARKET_ANALYSIS_BUCKET,
            prefix=prefix,
            limit=10,
            client_name_filter=client_name,
            category_code_filter=category_code,
        )

        logger.info(f"Returning {len(files)} JSON files with content from s3 market_analysis")

        return success_response({
            "files": files,
            "count": len(files),
            "bucket": MARKET_ANALYSIS_BUCKET,
            "prefix": prefix
        })

    except Exception as e:
        logger.error(f"Error listing files from S3: {str(e)}", exc_info=True)
        return server_error(str(e))


def get_analysis_by_category(event: dict, context) -> dict:
    """
    Get the latest market analysis for a category.

    An industry id as category (source YAML name, e.g. "electricity") returns the latest
    report from industry_analysis/<industry>/. Any other category returns the latest file
    from market_analysis/ (the crop market analysis).

    Expected event structure:
    {
        "pathParameters": {
            "category": "electricity"
        }
    }

    Returns:
    {
        "statusCode": 200,
        "body": { ... full JSON content of the analysis ... }
    }
    """
    path_params = event.get("pathParameters") or {}
    category = urllib.parse.unquote(path_params.get("category") or "").strip()
    logger.info(f"category path parameter: {category}")

    is_industry = bool(INDUSTRY_ID_PATTERN.fullmatch(category))
    prefix = f"industry_analysis/{category}/" if is_industry else "market_analysis/"

    try:
        files = storage.list_json_files(MARKET_ANALYSIS_BUCKET, prefix)

        # Newest first; a report the LLM output couldn't be parsed for is stored as { error, raw_output }
        for file_info in files:
            content = storage.read_json(MARKET_ANALYSIS_BUCKET, file_info["key"])
            if "error" in content:
                logger.warning(f"Skipping unparsed analysis file: {file_info['key']}")
                continue

            logger.info(f"Returning latest analysis file: {file_info['key']}")
            return success_response(content)

        return not_found_error(f"No analysis files found in {prefix}")

    except Exception as e:
        logger.error(f"Error reading analysis from S3: {str(e)}", exc_info=True)
        return server_error(str(e))


def get_client_analyses(event: dict, context) -> dict:
    """
    Get client analyses by market_position_id.

    Retrieves the market_position analysis and its associated peer_analysis.

    Expected event structure:
    {
        "pathParameters": {
            "id": "b1c9785f-e5a2-4017-8d1e-ab3d2a1ff2c7.json"
        }
    }

    Returns:
    {
        "statusCode": 200,
        "body": {
            "market_position": { ... },
            "peer_analysis": { ... } or null
        }
    }
    """
    try:
        path_params = event.get("pathParameters", {})
        market_position_id = path_params.get("id")

        if not market_position_id:
            return validation_error("market_position_id path parameter is required")

        if not validate_uuid_format(market_position_id):
            return validation_error(
                "Invalid market_position_id format. "
                "Expected format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.json"
            )

        if len(market_position_id) > 100:
            return validation_error("market_position_id exceeds maximum length")

        market_position_key = f"market_position/{market_position_id}"

        logger.info(f"Fetching market position from: {market_position_key}")

        # Read market_position file
        try:
            market_position = storage.read_json(MARKET_ANALYSIS_BUCKET, market_position_key)
        except Exception:
            logger.warning(f"Market position not found: {market_position_key}")
            return not_found_error(f"Market position not found: {market_position_id}")

        logger.info(f"Successfully read market position: {market_position_key}")

        # Search for peer_analysis with matching market_position_id
        peer_analysis = _find_linked_peer_analysis(market_position_id)

        return success_response({
            "market_position": market_position,
            "peer_analysis": peer_analysis
        })

    except Exception as e:
        logger.error(f"Error in getClientAnalyses: {str(e)}", exc_info=True)
        return server_error(str(e))


def _find_linked_peer_analysis(market_position_id: str) -> dict | None:
    """
    Find peer_analysis linked to a market_position_id.

    Args:
        market_position_id: The market position ID to match

    Returns:
        Peer analysis content if found, None otherwise
    """
    peer_analysis_prefix = "peer_analysis/"

    try:
        files = storage.list_json_files(MARKET_ANALYSIS_BUCKET, peer_analysis_prefix)

        for file_info in files:
            key = file_info["key"]
            try:
                peer_content = storage.read_json(MARKET_ANALYSIS_BUCKET, key)

                if peer_content.get("market_position_id") == f"market_position/{market_position_id}":
                    logger.info(f"Found matching peer analysis: {key}")
                    return peer_content
            except Exception as e:
                logger.warning(f"Failed to read peer analysis file {key}: {str(e)}")
                continue

        logger.info(f"No peer analysis found for market_position_id: {market_position_id}")
        return None

    except Exception as e:
        logger.warning(f"Error searching for peer analysis: {str(e)}")
        return None
