"""
Amazon Bedrock Knowledge Base retrieval (RETRIEVAL_BACKEND=bedrock).

Kept from the original AWS deployment for comparison with the local backend. The
Knowledge Base embeds the documents the scraper writes to S3, using the
<file>.metadata.json sidecars for filtering.
"""
from typing import Any

import boto3

from src.config.settings import AWS_REGION, KNOWLEDGE_BASE_ID


bedrock_agent_runtime = boto3.client(
    "bedrock-agent-runtime",
    region_name=AWS_REGION
)


def retrieve_only(
    query: str,
    num_results: int = 30,
    metadata_filter: dict[str, Any] | None = None
) -> list[dict]:
    """
    Call Bedrock Knowledge Base retrieve API (no generation).

    Args:
        query: The search query text
        num_results: Number of results to retrieve
        metadata_filter: Optional Knowledge Base filter, e.g.
            {"equals": {"key": "industry", "value": "livestock"}}

    Returns:
        List of retrieved chunks with content and metadata

    Raises:
        ValueError: If KNOWLEDGE_BASE_ID is not configured
    """
    if not KNOWLEDGE_BASE_ID:
        raise ValueError("KNOWLEDGE_BASE_ID environment variable not set")

    vector_search: dict[str, Any] = {"numberOfResults": num_results}
    if metadata_filter:
        vector_search["filter"] = metadata_filter

    response = bedrock_agent_runtime.retrieve(
        knowledgeBaseId=KNOWLEDGE_BASE_ID,
        retrievalQuery={"text": query},
        retrievalConfiguration={"vectorSearchConfiguration": vector_search}
    )

    chunks = []
    for result in response.get("retrievalResults", []):
        chunk = {
            "content": result.get("content", {}).get("text", ""),
            "location": result.get("location", {}).get("s3Location", {}).get("uri", ""),
            "score": result.get("score", 0),
            "metadata": result.get("metadata", {}),
        }
        chunks.append(chunk)

    return chunks
