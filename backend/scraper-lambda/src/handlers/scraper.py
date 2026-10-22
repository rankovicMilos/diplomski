"""
Lambda handler for scraping market reports.
Thin wrapper that delegates to business logic in backend/src/services/scraping.
"""
import json
import logging
import os
import tempfile
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from src.services.scraping import pipeline
from src.services.scraping.core.config_loader import DEFAULT_CONFIG_DIR as BUNDLED_CONFIG_DIR
from src.services.scraping.core.storage import StorageFactory
from src.services.scraping.runner import load_registry, run_sources

logger = logging.getLogger()
logger.setLevel(logging.INFO)

VALID_SOURCES = {"minpolj", "nscomex", "statgov", "all"}

# CORS configuration: allows cross-origin requests from CloudFront distribution
ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "http://localhost:3000")


def _cors_headers() -> dict:
    """Return standardized CORS headers for all responses."""
    return {
        "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
    }


def _download_configs(s3_uri: str) -> Path:
    """Copy s3://bucket/prefix/*.yaml into a temp dir the ConfigLoader can read."""
    bucket, _, prefix = s3_uri.removeprefix("s3://").partition("/")
    prefix = prefix.strip("/") + "/"
    target = Path(tempfile.mkdtemp(prefix="sources-"))
    s3 = boto3.client("s3")
    try:
        keys = [
            obj["Key"]
            for page in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=prefix)
            for obj in page.get("Contents", [])
            if obj["Key"].endswith(".yaml")
        ]
    except ClientError as e:
        if e.response["Error"]["Code"] != "AccessDenied":
            raise
        # No s3:ListBucket: fetch the files by the names of the configs bundled with the code
        logger.warning(f"Cannot list {s3_uri} (no s3:ListBucket); using bundled config file names")
        keys = [prefix + p.name for p in sorted(BUNDLED_CONFIG_DIR.glob("*.yaml"))]

    for key in keys:
        try:
            s3.download_file(bucket, key, str(target / Path(key).name))
        except ClientError as e:
            logger.warning(f"Skipping s3://{bucket}/{key}: {e.response['Error']['Code']}")
    downloaded = sorted(p.name for p in target.glob("*.yaml"))
    if not downloaded:
        raise RuntimeError(f"No source configs could be read from {s3_uri}")
    logger.info(f"Downloaded {len(downloaded)} source configs from {s3_uri}: {downloaded}")
    return target


def _run_config_driven(event: dict) -> dict:
    """
    Run the YAML-configured scrapers (services/scraping/runner.py).

    Configs are read from SCRAPER_CONFIG_S3_URI (or event "config_s3_uri") when set,
    otherwise from the config/sources directory bundled with the code.
    Without industry/source_ids/strategy every active source is run.
    """
    config_uri = event.get("config_s3_uri") or os.environ.get("SCRAPER_CONFIG_S3_URI")
    registry = load_registry(_download_configs(config_uri) if config_uri else None)
    configs = registry.filter(
        source_ids=event.get("source_ids"),
        industry=event.get("industry"),
        strategy=event.get("strategy"),
    )
    logger.info(f"Running {len(configs)} configured source(s)")
    results = run_sources(
        configs,
        StorageFactory.create("s3"),
        force=event.get("force", False),
        limit=event.get("limit"),
    )

    counts: dict[str, int] = {}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1
    return {
        "config_source": config_uri or "bundled",
        "summary": counts,
        "failed": [r.source_id for r in results if r.status not in ("success", "skipped")],
        "results": [r.to_dict() for r in results],
    }


def lambda_handler(event: dict, context) -> dict:
    """
    AWS Lambda entry point.
    Triggered by EventBridge on schedule or API Gateway.

    Event can specify:
    - source: "minpolj", "nscomex", "statgov", "zitasrbije", "eurostat", or "all" (default: "all")
    - sections: list of sections for minpolj (default: all configured)
    - years: list of years to filter (default: the last two completed years)
    - limit: max files per section/source (default: None = unlimited)
    - result_url: stat.gov.rs dataset ID or URL for statgov (e.g., "130102")

    With "mode": "config" the YAML-configured scrapers run instead; optional
    industry, source_ids, strategy, limit, force, config_s3_uri.
    """
    # Handle CORS preflight requests
    if event.get("httpMethod") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                **_cors_headers(),
                "Access-Control-Max-Age": "86400",
            },
            "body": "",
        }

    try:
        if event.get("mode") == "config":
            result = _run_config_driven(event)
            logger.info(f"Config-driven scraping completed: {result['summary']}")
            return {
                "statusCode": 200,
                "headers": _cors_headers(),
                "body": json.dumps(result, ensure_ascii=False)
            }

        source = event.get("source", "all").lower()
        sections = event.get("sections")
        years = event.get("years")
        limit = event.get("limit")

        if source not in VALID_SOURCES:
            return {
                "statusCode": 400,
                "headers": _cors_headers(),
                "body": json.dumps({"error": f"Invalid source: {source}. Valid: {VALID_SOURCES}"})
            }

        result = {}

        if source in ("minpolj", "all"):
            logger.info(f"Scraping minpolj: sections={sections}, years={years}, limit={limit}")
            result["minpolj"] = pipeline.run_scraping(
                sections=sections,
                years=years,
                limit=limit
            )

        if source in ("nscomex", "all"):
            logger.info(f"Scraping nscomex: years={years}, limit={limit}")
            nscomex_result = pipeline.run_nscomex_scraping(
                years=years,
                limit=limit
            )
            result.update(nscomex_result)

        if source in ("statgov", "all"):
            result_url = event.get("result_url", "130102")  # Default to crop statistics dataset
            logger.info(f"Scraping statgov: result_url={result_url}")
            statgov_result = pipeline.run_statgov_scraping(
                result_url=result_url,
                years=years
            )
            result.update(statgov_result)

        if source in ("zitasrbije", "all"):
            logger.info(f"Scraping zitasrbije: years={years}, limit={limit}")
            zitasrbije_result = pipeline.run_zitasrbije_scraping(
                years=years,
                limit=limit
            )
            result.update(zitasrbije_result)

        if source in ("eurostat", "all"):
            logger.info(f"Scraping eurostat: years={years}, limit={limit}")
            eurostat_result = pipeline.run_eurostat_scraping(
                years=years,
                limit=limit
            )
            result.update(eurostat_result)

        logger.info(f"Scraping completed: {result}")

        return {
            "statusCode": 200,
            "headers": _cors_headers(),
            "body": json.dumps(result)
        }

    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}")
        return {
            "statusCode": 500,
            "headers": _cors_headers(),
            "body": json.dumps({"error": str(e)})
        }
