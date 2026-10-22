"""
Lambda handler for market analysis orchestration.

This is the main entry point that routes requests to appropriate handlers.
Supports three analysis types:
- market_analysis: Crop market and price analysis (RAG)
- peer_analysis: Multi-company financial peer comparison (generate-only, CSV input)
- market_position: Client market position analysis (generate-only, PDF input)
"""
import logging
from datetime import datetime, timezone

# Re-export API handlers for Lambda entry points
from src.handlers.api_handlers import (
    get_analyses as getAnalyses,
    get_analysis_by_category as getAnalysisByCategory,
    get_client_analyses as getClientAnalyses,
)

__all__ = [
    "lambda_handler",
    "s3_trigger_peer_analysis",
    "getAnalyses",
    "getAnalysisByCategory",
    "getClientAnalyses",
]

from src.config.settings import (
    CLIENT_DATA_BUCKET,
    MARKET_ANALYSIS_BUCKET,
    PEER_DATA_BUCKET,
    DEFAULT_CROPS,
    DEFAULT_COUNTRY,
    DEFAULT_YEARS,
    DEFAULT_RESULTS_PER_SECTION,
)
from src.config.prompts import (
    MARKET_ANALYSIS_SYSTEM_PROMPT,
    MARKET_POSITION_PROMPT,
    build_peer_analysis_prompt,
    build_industry_market_analysis_prompt,
    format_period,
)
from src.services import storage, llm_service
from src.services.industry_config import industry_for_nace, load_industry_profile
from src.handlers.api_handlers import get_analyses, get_analysis_by_category, get_client_analyses
from src.utils.response import success_response, validation_error, server_error
from src.utils.parsers import parse_model_response
from src.utils.query_builder import retrieve_by_section
from src.utils.industry_retrieval import retrieve_by_industry_section, section_label
from src.utils.period_filter import restrict_to_years


import urllib.parse

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def parse_s3_trigger_event(event: dict) -> dict | None:
    """
    Parse S3 trigger event and construct analysis event.

    Supports S3 trigger for:
    - peer_data/ prefix (.csv) -> peer_analysis

    Args:
        event: The raw Lambda event (may be S3 trigger or direct invocation)

    Returns:
        A constructed analysis event dict, or None if not an S3 trigger
    """
    records = event.get("Records", [])
    if not records:
        return None

    first_record = records[0]

    # Verify it's an S3 event
    if first_record.get("eventSource") != "aws:s3":
        return None

    # Extract bucket and key from S3 event
    s3_info = first_record.get("s3", {})
    bucket = s3_info.get("bucket", {}).get("name")
    key = s3_info.get("object", {}).get("key")

    if not bucket or not key:
        logger.warning("S3 event missing bucket or key")
        return None

    # URL decode the key (S3 events URL-encode special characters)
    key = urllib.parse.unquote_plus(key)

    logger.info(f"S3 trigger detected: bucket={bucket}, key={key}")

    # Only handle peer_data/ prefix for peer_analysis
    if key.startswith("peer_data/"):
        return _build_peer_analysis_event(bucket, key)
    else:
        logger.info(f"Ignoring S3 event for key outside peer_data/ prefix: {key}")
        return None


def _build_peer_analysis_event(bucket: str, key: str) -> dict | None:
    """Build peer_analysis event from S3 trigger."""
    if not key.lower().endswith(".csv"):
        logger.info(f"Ignoring S3 event for non-CSV file in peer_data/: {key}")
        return None

    # Extract base name from CSV filename for linking
    # peer_data/silbo_2024_report.csv → silbo_2024_report
    filename = key.split("/")[-1]  # silbo_2024_report.csv
    base_name = filename.rsplit(".csv", 1)[0]  # silbo_2024_report

    # Build IDs from the CSV filename
    market_position_id = f"market_position/{base_name}.json"
    analysis_id = base_name

    logger.info(f"Linking peer_analysis to market_position by filename: {market_position_id}")

    return {
        "analysis_type": "peer_analysis",
        "peer_data_key": key,
        "analysis_id": analysis_id,
        "market_position_id": market_position_id,
        "country": "Serbia",
        "years": DEFAULT_YEARS,
        "_s3_trigger": True,
        "_s3_source_bucket": bucket,
    }


def handle_market_analysis(event: dict, context) -> dict:
    """
    Handle market analysis request using RAG with per-section retrieval.

    Args:
        event: Lambda event with crops, country, years
        context: Lambda context

    Returns:
        HTTP response dict
    """
    if event.get("industry"):
        return handle_industry_market_analysis(event, context)

    crops = event.get("crops", DEFAULT_CROPS)
    country = event.get("country", DEFAULT_COUNTRY)
    years = event.get("years", DEFAULT_YEARS)
    results_per_section = event.get("results_per_section", DEFAULT_RESULTS_PER_SECTION)

    if not crops:
        return validation_error("crops list cannot be empty")

    logger.info(f"Generating market analysis for crops={crops}, country={country}, years={years}")
    logger.info(f"Using per-section retrieval with {results_per_section} results per section")

    # Per-section retrieval: 3 targeted calls (production, price, geopolitical)
    section_chunks = retrieve_by_section(crops, country, years, results_per_section)

    user_query = f"Generate market analysis report for crops: {', '.join(crops)} in {country} for years {years}"

    response = llm_service.generate_with_section_context(
        section_chunks,
        MARKET_ANALYSIS_SYSTEM_PROMPT,
        user_query
    )
    logger.info("Received response from Claude")

    result = parse_model_response(response)
    period_removed = {}
    if "error" not in result:
        period_removed = restrict_to_years(result, years)
        meta = result.get("meta") if isinstance(result.get("meta"), dict) else {}
        meta["period"] = format_period(years)
        result["meta"] = meta

    # Save - Override AI-generated fields with actual values
    file_id = context.aws_request_id if context else "local-test"
    original_analysis_id = result.get("analysis_id")
    result["analysis_id"] = f"market_analysis/{file_id}.json"
    result["generated_at"] = datetime.now(timezone.utc).isoformat()
    logger.info(f"Overriding analysis_id: {original_analysis_id} -> {result['analysis_id']}")

    s3_location = storage.save_json(result, file_id, "market_analysis")
    if s3_location:
        result["s3_location"] = s3_location

    result["retrieval_stats"] = {
        "crops_queried": crops,
        "results_per_section": results_per_section,
        "chunks_by_section": {k: len(v) for k, v in section_chunks.items()},
        "total_chunks": sum(len(v) for v in section_chunks.values()),
        "removed_outside_period": period_removed,
    }

    return success_response(result, methods="POST, OPTIONS")


def handle_industry_market_analysis(event: dict, context) -> dict:
    """
    Market analysis for any industry configured in the scraper's source YAML.

    The report outline (sections, topics, sources) comes from <industry>.yaml and retrieval
    is limited to that industry's documents. The output has the same JSON structure as the
    crop market analysis.

    Saved to industry_analysis/<industry>/<id>.json; with "show_in_frontend": true it is
    saved to market_analysis/<id>.json instead, where the frontend picks up the latest file.
    """
    country = event.get("country", DEFAULT_COUNTRY)
    years = event.get("years", DEFAULT_YEARS)
    results_per_section = event.get("results_per_section", DEFAULT_RESULTS_PER_SECTION)

    try:
        profile = load_industry_profile(event["industry"], event.get("config_s3_uri"))
    except ValueError as e:
        return validation_error(str(e))

    logger.info(
        f"Generating industry market analysis: industry={profile.industry}, country={country}, "
        f"years={years}, sections={[s.id for s in profile.sections]}"
    )

    section_chunks = retrieve_by_industry_section(profile, country, years, results_per_section)
    if not any(section_chunks.values()):
        return validation_error(
            f"No documents for industry '{profile.industry}' in the knowledge base. "
            f"Run the scraper for this industry and sync the knowledge base first."
        )

    user_query = (
        f"Generate the market and price analysis report for the {profile.display_name} industry "
        f"in {country} for years {years}"
    )
    response = llm_service.generate_with_section_context(
        section_chunks,
        build_industry_market_analysis_prompt(profile, country, years),
        user_query,
        section_labels={s.id: section_label(s) for s in profile.sections},
    )
    logger.info("Received response from Claude")

    result = parse_model_response(response)
    parsed = "error" not in result

    # Only a parsed report may replace what the frontend shows
    publish = bool(event.get("show_in_frontend")) and parsed
    prefix = "market_analysis" if publish else f"industry_analysis/{profile.industry}"
    file_id = context.aws_request_id if context else "local-test"

    result["analysis_id"] = f"{prefix}/{file_id}.json"
    result["generated_at"] = datetime.now(timezone.utc).isoformat()
    result["industry"] = profile.industry
    period_removed = {}
    if parsed:
        period_removed = restrict_to_years(result, years)
        meta = result.get("meta") if isinstance(result.get("meta"), dict) else {}
        meta["sector"] = profile.display_name
        meta["country"] = country
        meta["period"] = format_period(years)
        result["meta"] = meta

    s3_location = storage.save_json(result, file_id, prefix)
    if s3_location:
        result["s3_location"] = s3_location

    result["retrieval_stats"] = {
        "industry": profile.industry,
        "config_source": profile.config_origin,
        "sections": [s.id for s in profile.sections],
        "results_per_section": results_per_section,
        "chunks_by_section": {k: len(v) for k, v in section_chunks.items()},
        "total_chunks": sum(len(v) for v in section_chunks.values()),
        "documents": sorted({c.get("location", "") for v in section_chunks.values() for c in v}),
        "removed_outside_period": period_removed,
    }

    return success_response(result, methods="POST, OPTIONS")


def handle_peer_analysis(event: dict, context) -> dict:
    """
    Handle peer analysis request from CSV data.

    Args:
        event: Lambda event with peer_data_key
        context: Lambda context

    Returns:
        HTTP response dict
    """
    peer_data_key = event.get("peer_data_key")
    market_position_id = event.get("market_position_id")
    analysis_id = event.get("analysis_id")  # Optional: from FE or extracted from CSV filename

    if not peer_data_key:
        return validation_error("peer_data_key is required for peer_analysis")

    logger.info(f"Generating peer analysis from CSV: {peer_data_key}")

    # Read CSV data
    csv_data = storage.read_file(PEER_DATA_BUCKET, peer_data_key)

    # Build context with CSV data
    csv_context = (
        "<<<PEER_ANALYSIS_CSV>>>\n"
        f"{csv_data}\n"
        "<<<END_PEER_ANALYSIS_CSV>>>"
    )

    sector_name, nace_code = _peer_sector(market_position_id)
    logger.info(f"Peer analysis sector: {sector_name or 'unknown'} ({nace_code or 'no NACE code'})")

    response = llm_service.generate_only(csv_context, build_peer_analysis_prompt(sector_name, nace_code))
    logger.info("Received response from Claude (peer analysis generate-only mode)")

    result = parse_model_response(response)

    # Save - Override AI-generated fields with actual values
    # Extract file_id from CSV filename: peer_data/silbo_2024_report.csv → silbo_2024_report
    csv_filename = peer_data_key.split("/")[-1]
    file_id = csv_filename.rsplit(".csv", 1)[0] if csv_filename.lower().endswith(".csv") else (context.aws_request_id if context else "local-test")
    original_analysis_id = result.get("analysis_id")
    result["analysis_id"] = f"peer_analysis/{file_id}.json"
    result["market_position_id"] = market_position_id
    result["generated_at"] = datetime.now(timezone.utc).isoformat()
    logger.info(f"Overriding analysis_id: {original_analysis_id} -> {result['analysis_id']}")

    s3_location = storage.save_json(result, file_id, "peer_analysis")
    if s3_location:
        result["s3_location"] = s3_location

    return success_response(result, methods="POST, OPTIONS")


def _peer_sector(market_position_id: str | None) -> tuple[str | None, str | None]:
    """
    Sector of a peer analysis, from the linked market position's NACE code.

    The frontend uploads the peer sheet while the market position is still being generated,
    so the market position may not exist yet; the prompt then asks for the sector generically.
    """
    if not market_position_id:
        return None, None
    try:
        nace_code = storage.read_json(MARKET_ANALYSIS_BUCKET, market_position_id).get("nace_code")
    except Exception:
        return None, None
    industry = industry_for_nace(nace_code)
    return (industry[1] if industry else None), nace_code


def handle_market_position(event: dict, context) -> dict:
    """
    Handle market position analysis request.

    Args:
        event: Lambda event with client_data_key, market_analysis_key (optional)
        context: Lambda context

    Returns:
        HTTP response dict
    """
    client_data_key = event.get("client_data_key")
    market_analysis_key = event.get("market_analysis_key")
    nace_code = event.get("nace_code", "A1.11")
    client_name = event.get("client_name")  # Optional override for model extraction
    analysis_id = event.get("analysis_id")  # Optional UUID from FE for custom file naming

    if not client_data_key:
        return validation_error("client_data_key is required for market_position")

    # Auto-select latest market analysis if not provided: the client's industry first
    # (industry_analysis/<industry>/), then the published market_analysis/ reports
    if not market_analysis_key:
        logger.info("No market_analysis_key provided, auto-selecting latest...")
        industry = industry_for_nace(nace_code)
        files = []
        if industry:
            files = storage.list_json_files(MARKET_ANALYSIS_BUCKET, f"industry_analysis/{industry[0]}/")
        if not files:
            files = storage.list_json_files(MARKET_ANALYSIS_BUCKET, "market_analysis/")
        if not files:
            return validation_error(
                "No market analysis available. Generate a market_analysis first, "
                "or provide market_analysis_key explicitly."
            )
        market_analysis_key = files[0]["key"]
        logger.info(f"Auto-selected latest market analysis: {market_analysis_key}")

    # Multi-commodity support (new) or single commodity (legacy)
    commodities = event.get("commodities")
    primary_commodity = event.get("commodity", "wheat")  # Legacy fallback
    primary_currency = event.get("primary_currency", "RSD")
    fx_rate_eur_rsd = event.get("fx_rate_eur_rsd")
    fx_rate_date = event.get("fx_rate_date")

    # Format commodities for logging and prompt
    if commodities:
        commodities_str = ", ".join([f"{c['name']} ({c['revenue_pct']}%)" for c in commodities])
        logger.info(
            "Generating market position analysis with client_data=%s, market_analysis=%s, "
            "commodities=%s, primary_currency=%s",
            client_data_key, market_analysis_key, commodities_str, primary_currency,
        )
    else:
        logger.info(
            "Generating market position analysis with client_data=%s, market_analysis=%s, "
            "fx_rate_eur_rsd=%s, fx_rate_date=%s, primary_commodity=%s, primary_currency=%s",
            client_data_key, market_analysis_key, fx_rate_eur_rsd, fx_rate_date,
            primary_commodity, primary_currency,
        )

    # Read market analysis
    market_analysis = storage.read_file(MARKET_ANALYSIS_BUCKET, market_analysis_key)

    # Build PARAMETERS block with multi-commodity support
    if commodities:
        # Format example: "wheat: 60%, corn: 40%"
        commodities_formatted = "\n".join([
            f"  - {c['name']}: {c['revenue_pct']}% of revenue"
            for c in commodities
        ])
        parameters_block = (
            "=== PARAMETERS ===\n"
            f"commodities (with estimated revenue share):\n{commodities_formatted}\n"
            f"primary_currency: {primary_currency}\n"
            f"fx_rate_eur_rsd: {fx_rate_eur_rsd if fx_rate_eur_rsd is not None else 'null'}\n"
            f"fx_rate_date: {fx_rate_date if fx_rate_date is not None else 'null'}\n\n"
            "IMPORTANT: Calculate weighted market position based on revenue percentages.\n"
            "For each commodity, estimate the client's market share, then calculate\n"
            "the weighted average market position using the revenue percentages above.\n\n"
        )
    else:
        # Legacy single commodity
        parameters_block = (
            "=== PARAMETERS ===\n"
            f"primary_commodity: {primary_commodity}\n"
            f"primary_currency: {primary_currency}\n"
            f"fx_rate_eur_rsd: {fx_rate_eur_rsd if fx_rate_eur_rsd is not None else 'null'}\n"
            f"fx_rate_date: {fx_rate_date if fx_rate_date is not None else 'null'}\n\n"
        )

    # Check if client data is PDF or markdown
    if client_data_key.lower().endswith(".pdf"):
        logger.info("Using PDF document flow for client data")
        client_pdf_bytes = storage.read_pdf(CLIENT_DATA_BUCKET, client_data_key)

        pdf_context = (
            f"{parameters_block}"
            "<<<MARKET_ANALYSIS_JSON>>>\n"
            f"{market_analysis}\n"
            "<<<END_MARKET_ANALYSIS_JSON>>>"
        )

        response = llm_service.generate_with_pdf(
            client_pdf_bytes,
            pdf_context,
            MARKET_POSITION_PROMPT
        )
    else:
        logger.info("Using markdown text flow for client data")
        client_data = storage.read_file(CLIENT_DATA_BUCKET, client_data_key)

        combined_context = (
            f"{parameters_block}"
            "<<<CLIENT_KEY_FINANCIALS_MD>>>\n"
            f"{client_data}\n"
            "<<<END_CLIENT_KEY_FINANCIALS_MD>>>\n\n"
            "<<<MARKET_ANALYSIS_JSON>>>\n"
            f"{market_analysis}\n"
            "<<<END_MARKET_ANALYSIS_JSON>>>"
        )

        response = llm_service.generate_only(combined_context, MARKET_POSITION_PROMPT)

    logger.info("Received response from Claude (generate-only mode)")

    model_result = parse_model_response(response)

    # Save - Use FE-provided analysis_id or fallback to Lambda request UUID
    file_id = analysis_id if analysis_id else (context.aws_request_id if context else "local-test")
    original_analysis_id = model_result.get("analysis_id")

    # Remove keys we want to control from model_result to prevent overwrites
    model_result.pop("nace_code", None)
    model_result.pop("analysis_id", None)
    model_result.pop("market_analysis_id", None)
    model_result.pop("generated_at", None)

    # If client_name provided in event, override model extraction
    if client_name:
        model_result.pop("client_name", None)

    # Build result with our metadata at top, then model fields
    result = {
        "nace_code": nace_code,
        "analysis_id": f"market_position/{file_id}.json",
        "market_analysis_id": market_analysis_key,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        **model_result,  # Remaining model fields after our metadata
    }

    # Override client_name if provided in event
    if client_name:
        result["client_name"] = client_name
        logger.info(f"Using client_name from event: {client_name}")

    logger.info(f"Setting nace_code: {nace_code}")
    logger.info(f"Overriding analysis_id: {original_analysis_id} -> {result['analysis_id']}")

    s3_location = storage.save_json(result, file_id, "market_position")
    if s3_location:
        result["s3_location"] = s3_location

    return success_response(result, methods="POST, OPTIONS")


# Analysis type to handler mapping
ANALYSIS_HANDLERS = {
    "market_analysis": handle_market_analysis,
    "peer_analysis": handle_peer_analysis,
    "market_position": handle_market_position,
}


def lambda_handler(event: dict, context) -> dict:
    """
    AWS Lambda entry point.

    Expected event structure for market_analysis:
    {
        "analysis_type": "market_analysis",
        "crops": ["corn", "wheat", "soybean", "sunflower"],
        "country": "Serbia",
        "years": [2024, 2025]
    }

    Expected event structure for an industry market_analysis (industry = source YAML name):
    {
        "analysis_type": "market_analysis",
        "industry": "livestock",
        "country": "Serbia",               # optional
        "years": [2024, 2025],             # optional
        "show_in_frontend": false          # optional, true saves under market_analysis/
    }

    Expected event structure for peer_analysis:
    {
        "analysis_type": "peer_analysis",
        "peer_data_key": "peer_data/peer_data.csv"
    }

    Expected event structure for market_position:
    {
        "analysis_type": "market_position",
        "client_data_key": "client_data/client_data.pdf",
        "market_analysis_key": "market_analysis/uuid.json",  # Optional - uses latest if omitted
        "commodities": [
            {"name": "wheat", "revenue_pct": 60},
            {"name": "corn", "revenue_pct": 40}
        ],
        "primary_currency": "RSD"
    }

    Returns:
        HTTP response with analysis result
    """
    try:
        # Parse body if coming from API Gateway (Lambda proxy integration)
        if "body" in event:
            import json as json_module
            body = event.get("body")
            if isinstance(body, str):
                try:
                    body = json_module.loads(body)
                except json_module.JSONDecodeError:
                    body = None
            if isinstance(body, dict):
                event.update(body)

        # Check if this is an S3 trigger event
        if event.get("Records"):
            # This is an S3 event - must be handled by S3 trigger logic
            s3_triggered_event = parse_s3_trigger_event(event)
            if s3_triggered_event:
                logger.info("Processing S3-triggered analysis")
                event = s3_triggered_event
            else:
                # S3 event but couldn't build analysis event (wrong prefix, file type, etc.)
                logger.info("S3 event received but no matching trigger handler")
                return success_response({"message": "S3 event ignored - no matching handler"})

        analysis_type = event.get("analysis_type")
        years = event.get("years", DEFAULT_YEARS)

        # Validate analysis_type is provided
        if not analysis_type:
            return validation_error(
                f"analysis_type is required. Must be one of: {', '.join(ANALYSIS_HANDLERS.keys())}"
            )

        # Validate common inputs
        if not isinstance(years, list) or not years:
            return validation_error("years must be a non-empty list")

        # Route to appropriate handler
        handler = ANALYSIS_HANDLERS.get(analysis_type)
        if handler:
            return handler(event, context)
        else:
            return validation_error(
                f"Invalid analysis_type: {analysis_type}. "
                f"Must be one of: {', '.join(ANALYSIS_HANDLERS.keys())}"
            )

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return validation_error(str(e))

    except Exception as e:
        logger.error(f"Error generating analysis: {str(e)}", exc_info=True)
        return server_error(str(e))


def s3_trigger_peer_analysis(event: dict, context) -> dict:
    """
    S3 trigger handler for peer analysis.

    Triggered when a new CSV file is uploaded to the peer_data/ prefix.
    Automatically runs peer analysis on the uploaded file.

    Expected S3 event structure:
    {
        "Records": [
            {
                "eventSource": "aws:s3",
                "eventName": "ObjectCreated:Put",
                "s3": {
                    "bucket": {"name": "sra-thesis-client-data"},
                    "object": {"key": "peer_data/company_peers.csv"}
                }
            }
        ]
    }

    Args:
        event: S3 event notification
        context: Lambda context

    Returns:
        dict with processing results for each record
    """
    import urllib.parse

    results = []
    records = event.get("Records", [])

    if not records:
        logger.warning("No records found in S3 event")
        return {"statusCode": 200, "body": "No records to process"}

    for record in records:
        try:
            # Validate event source
            event_source = record.get("eventSource", "")
            if event_source != "aws:s3":
                logger.info(f"Skipping non-S3 event: {event_source}")
                continue

            # Only process fresh PUT uploads (not copies, multipart, etc.)
            event_name = record.get("eventName", "")
            if event_name != "ObjectCreated:Put":
                logger.info(f"Skipping non-PUT event: {event_name}")
                continue

            # Extract S3 object info
            s3_info = record.get("s3", {})
            bucket_name = s3_info.get("bucket", {}).get("name", "")
            object_key = s3_info.get("object", {}).get("key", "")

            # URL decode the key (S3 encodes special characters)
            object_key = urllib.parse.unquote_plus(object_key)

            logger.info(f"Processing S3 event: bucket={bucket_name}, key={object_key}")

            # Validate file is a CSV in peer_data/ prefix
            if not object_key.startswith("peer_data/"):
                logger.info(f"Skipping file not in peer_data/ prefix: {object_key}")
                continue

            if not object_key.lower().endswith(".csv"):
                logger.info(f"Skipping non-CSV file: {object_key}")
                continue

            # Build peer analysis event
            peer_event = {
                "analysis_type": "peer_analysis",
                "peer_data_key": object_key,
            }

            logger.info(f"Triggering peer analysis for: {object_key}")

            # Call peer analysis handler
            result = handle_peer_analysis(peer_event, context)
            results.append({
                "key": object_key,
                "status": "success",
                "response": result
            })

        except Exception as e:
            logger.error(f"Error processing S3 record: {str(e)}", exc_info=True)
            results.append({
                "key": object_key if 'object_key' in locals() else "unknown",
                "status": "error",
                "error": str(e)
            })

    return {
        "statusCode": 200,
        "body": {
            "message": f"Processed {len(results)} record(s)",
            "results": results
        }
    }
