"""
Local HTTP server for the orchestrator Lambda (replaces API Gateway when running locally).

Each request becomes an API Gateway proxy event and goes to the unchanged Lambda handler.
Routes mirror infrastructure/modules/api_gateway/specs/openapi.yaml.

    uv run uvicorn local_server:app --port 8001
"""
import json
import uuid
from types import SimpleNamespace
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.concurrency import run_in_threadpool

from src.handlers.orchestrator import (
    getAnalyses,
    getAnalysisByCategory,
    getClientAnalyses,
    lambda_handler,
)

app = FastAPI(title="Orchestrator (local)")


async def _invoke(handler: Callable, request: Request, path_params: dict | None = None) -> Response:
    body = (await request.body()).decode("utf-8") or None
    event = {
        "httpMethod": request.method,
        "path": request.url.path,
        "headers": dict(request.headers),
        "pathParameters": path_params or None,
        "queryStringParameters": dict(request.query_params) or None,
        "body": body,
    }
    # Handlers name output files after the Lambda request id
    context = SimpleNamespace(aws_request_id=str(uuid.uuid4()))
    # Report generation takes minutes; the thread pool keeps the other routes responsive
    result = await run_in_threadpool(handler, event, context)

    body_out = result.get("body", "")
    if not isinstance(body_out, str):
        body_out = json.dumps(body_out, ensure_ascii=False)
    return Response(
        content=body_out,
        status_code=result.get("statusCode", 200),
        headers=result.get("headers") or {},
        media_type="application/json",
    )


@app.get("/analyses")
async def get_analyses(request: Request):
    return await _invoke(getAnalyses, request)


@app.post("/analyses")
async def post_analyses(request: Request):
    return await _invoke(lambda_handler, request)


@app.get("/analyses/client/{id}")
async def get_client_analyses(id: str, request: Request):
    return await _invoke(getClientAnalyses, request, {"id": id})


@app.get("/analyses/{category}")
async def get_analysis_by_category(category: str, request: Request):
    return await _invoke(getAnalysisByCategory, request, {"category": category})


@app.post("/_events/s3")
async def s3_event(request: Request):
    """S3 ObjectCreated notifications, sent by the local upload server (peer_data/ CSVs)."""
    event = await request.json()
    context = SimpleNamespace(aws_request_id=str(uuid.uuid4()))
    result = await run_in_threadpool(lambda_handler, event, context)
    return Response(content=json.dumps(result.get("body", result), ensure_ascii=False, default=str),
                    status_code=result.get("statusCode", 200), media_type="application/json")
