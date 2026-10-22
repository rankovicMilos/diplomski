"""
Local HTTP server for the trigger-upload Lambda (replaces API Gateway and S3 locally).

- POST /upload               -> the unchanged Lambda handler
- PUT  /local-upload/<key>   -> stands in for the S3 presigned PUT URL (PDF uploads)

After an Excel file is converted into peer_data/<name>.csv, an S3 ObjectCreated event is
sent to the local orchestrator, as the S3 bucket notification does on AWS.

    uv run uvicorn local_server:app --port 8002
"""
import json
import logging
import os
import threading
from types import SimpleNamespace

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.concurrency import run_in_threadpool

from src.config import CONVERSION_OUTPUT_PREFIX, S3_BUCKET
from src.handlers.ingestion import lambda_handler
from src.services.local_storage_service import local_path

logger = logging.getLogger("uvicorn.error")

ORCHESTRATOR_URL = os.environ.get("ORCHESTRATOR_URL", "http://localhost:8001")

app = FastAPI(title="Trigger upload (local)")


@app.post("/upload")
async def upload(request: Request):
    event = {
        "httpMethod": "POST",
        "path": "/upload",
        "headers": dict(request.headers),
        "body": (await request.body()).decode("utf-8"),
    }
    result = await run_in_threadpool(lambda_handler, event, SimpleNamespace(aws_request_id="local"))

    if result["statusCode"] == 200:
        csv_key = json.loads(result["body"]).get("csv_key")
        if csv_key and csv_key.startswith(f"{CONVERSION_OUTPUT_PREFIX}/"):
            threading.Thread(target=_notify_orchestrator, args=(csv_key,), daemon=True).start()

    return Response(content=result["body"], status_code=result["statusCode"],
                    headers=result.get("headers") or {}, media_type="application/json")


@app.put("/local-upload/{key:path}")
async def local_upload(key: str, request: Request):
    path = local_path(S3_BUCKET, key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(await request.body())
    logger.info(f"Stored upload {S3_BUCKET}/{key}")
    return Response(status_code=200)


def _notify_orchestrator(key: str) -> None:
    """S3 ObjectCreated:Put notification for the peer analysis trigger."""
    event = {"Records": [{
        "eventSource": "aws:s3",
        "eventName": "ObjectCreated:Put",
        "s3": {"bucket": {"name": S3_BUCKET}, "object": {"key": key}},
    }]}
    try:
        # Peer analysis is a full Claude call; wait for it like the S3 trigger would
        response = httpx.post(f"{ORCHESTRATOR_URL}/_events/s3", json=event, timeout=900)
        logger.info(f"Peer analysis for {key}: HTTP {response.status_code}")
    except httpx.HTTPError as e:
        logger.error(f"Could not trigger peer analysis for {key}: {e}")
