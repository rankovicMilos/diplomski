"""
Local retrieval (RETRIEVAL_BACKEND=local): Chroma on disk + a multilingual embedding model.

The index is built by `python -m src.retrieval.indexer` from the documents the scraper
saves locally. Each chunk carries the document's sidecar metadata (industry, sections,
year, ...) so retrieval can be filtered exactly like the Bedrock Knowledge Base.
"""
import logging
from functools import cache
from typing import Any

from src.config.settings import CHROMA_DIR, EMBEDDING_MODEL


logger = logging.getLogger(__name__)

COLLECTION_NAME = "documents"
# Chroma metadata values must be scalars: list fields are stored comma-joined
LIST_FIELDS = ("industries", "sections")
LIST_SEPARATOR = ","


@cache
def embedding_model():
    from sentence_transformers import SentenceTransformer

    logger.info(f"Loading embedding model {EMBEDDING_MODEL}...")
    return SentenceTransformer(EMBEDDING_MODEL)


@cache
def collection():
    import chromadb

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})


def embed(texts: list[str]) -> list[list[float]]:
    vectors = embedding_model().encode(
        texts, batch_size=16, normalize_embeddings=True, show_progress_bar=len(texts) > 64
    )
    return vectors.tolist()


def to_chroma_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Flatten sidecar metadata into Chroma's scalar-only metadata."""
    flat = {}
    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, list):
            flat[key] = LIST_SEPARATOR.join(str(v) for v in value)
        elif isinstance(value, (str, int, float, bool)):
            flat[key] = value
        else:
            flat[key] = str(value)
    return flat


def from_chroma_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    restored = dict(metadata)
    for key in LIST_FIELDS:
        if isinstance(restored.get(key), str):
            restored[key] = [v for v in restored[key].split(LIST_SEPARATOR) if v]
    return restored


def to_chroma_where(metadata_filter: dict[str, Any] | None) -> dict[str, Any] | None:
    """
    Translate a Bedrock Knowledge Base filter into a Chroma `where` clause.

    Supports the operators the report code uses: equals, notEquals, in, andAll, orAll.
    """
    if not metadata_filter:
        return None
    (operator, operand), = metadata_filter.items()
    if operator == "equals":
        return {operand["key"]: operand["value"]}
    if operator == "notEquals":
        return {operand["key"]: {"$ne": operand["value"]}}
    if operator == "in":
        return {operand["key"]: {"$in": operand["value"]}}
    if operator in ("andAll", "orAll"):
        clauses = [to_chroma_where(f) for f in operand]
        return {"$and" if operator == "andAll" else "$or": clauses}
    raise ValueError(f"Unsupported metadata filter operator '{operator}'")


def retrieve_only(
    query: str,
    num_results: int = 30,
    metadata_filter: dict[str, Any] | None = None
) -> list[dict]:
    """
    Search the local index.

    Returns:
        List of chunks: {"content", "location", "score", "metadata"}; score is cosine
        similarity (1 = identical)
    """
    docs = collection()
    if docs.count() == 0:
        raise ValueError(
            f"The local index in {CHROMA_DIR} is empty. "
            f"Run `uv run python -m src.retrieval.indexer` first."
        )

    result = docs.query(
        query_embeddings=embed([query]),
        n_results=num_results,
        where=to_chroma_where(metadata_filter),
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for content, metadata, distance in zip(
        result["documents"][0], result["metadatas"][0], result["distances"][0]
    ):
        metadata = from_chroma_metadata(metadata or {})
        chunks.append({
            "content": content,
            "location": metadata.pop("location", ""),
            "score": 1 - distance,
            "metadata": metadata,
        })
    return chunks
