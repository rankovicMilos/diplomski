"""
Retrieval service: semantic search over the scraped documents.

RETRIEVAL_BACKEND selects where the search runs:
- local:   on-disk Chroma index built by `python -m src.retrieval.indexer`
- bedrock: Amazon Bedrock Knowledge Base (KNOWLEDGE_BASE_ID)

Both return the same chunk shape, so the query builders do not depend on the backend.
The backend is imported on first use, so routes that never retrieve skip loading the
embedding model.
"""
import importlib
from functools import cache
from typing import Any

from src.config.settings import RETRIEVAL_BACKEND


BACKENDS = {
    "local": "src.retrieval.local",
    "bedrock": "src.retrieval.bedrock",
}


@cache
def _backend():
    if RETRIEVAL_BACKEND not in BACKENDS:
        raise ValueError(
            f"Unknown RETRIEVAL_BACKEND '{RETRIEVAL_BACKEND}'. Use one of: {', '.join(BACKENDS)}"
        )
    return importlib.import_module(BACKENDS[RETRIEVAL_BACKEND])


def retrieve_only(
    query: str,
    num_results: int = 30,
    metadata_filter: dict[str, Any] | None = None
) -> list[dict]:
    """
    Retrieve the chunks most similar to the query.

    Args:
        query: The search query text
        num_results: Number of results to retrieve
        metadata_filter: Optional filter, e.g.
            {"equals": {"key": "industry", "value": "livestock"}}

    Returns:
        List of chunks: {"content", "location", "score", "metadata"}
    """
    return _backend().retrieve_only(query, num_results=num_results, metadata_filter=metadata_filter)
