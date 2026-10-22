"""
Build the local retrieval index from the scraped documents.

Replaces the Bedrock Knowledge Base ingestion job: extracts text from every document the
scraper saved, splits it into chunks, embeds them and stores them in Chroma together
with the document's sidecar metadata (<file>.metadata.json, written by the scraper).

Run from backend/orchestrator-lambda:

    uv run python -m src.retrieval.indexer                       # all documents
    uv run python -m src.retrieval.indexer --industry electricity
    uv run python -m src.retrieval.indexer --rebuild             # drop the index first

Documents whose content did not change since the last run are skipped.
"""
import argparse
import hashlib
import json
import logging
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from src.config.settings import CHROMA_DIR, LOCAL_DATA_DIR, RAW_DATA_BUCKET
from src.retrieval import local


logger = logging.getLogger(__name__)

METADATA_SUFFIX = ".metadata.json"
TEXT_EXTENSIONS = {".md", ".txt", ".csv"}
# ~500 tokens; Serbian averages a little under 4 characters per token
CHUNK_CHARS = 2000
OVERLAP_CHARS = 300
# Less text than this usually means a scanned PDF (images only)
MIN_DOCUMENT_CHARS = 200
HEADING = re.compile(r"^#{1,6}\s", re.MULTILINE)


def extract_text(path: Path) -> str | None:
    """Text of a document as markdown, or None if the format is not supported."""
    suffix = path.suffix.lower()
    if suffix in TEXT_EXTENSIONS:
        return path.read_text(encoding="utf-8", errors="replace")
    if suffix == ".pdf":
        import pymupdf4llm

        return pymupdf4llm.to_markdown(str(path), show_progress=False)
    if suffix == ".docx":
        return _docx_to_markdown(path)
    if suffix == ".doc":
        return _doc_to_text(path)
    if suffix == ".xlsx":
        return _xlsx_to_markdown(path)
    if suffix == ".xls":
        return _xls_to_markdown(path)
    return None


def _doc_to_text(path: Path) -> str | None:
    """Legacy Word files: macOS textutil, or antiword where installed."""
    for command in (["textutil", "-convert", "txt", "-stdout", str(path)], ["antiword", str(path)]):
        if shutil.which(command[0]):
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return result.stdout
    logger.warning(f"{path.name}: no .doc converter found (install antiword)")
    return None


def _xls_to_markdown(path: Path) -> str:
    import xlrd

    workbook = xlrd.open_workbook(str(path))
    parts = []
    for sheet in workbook.sheets():
        rows = [
            [str(value) if value != "" else "" for value in sheet.row_values(i)]
            for i in range(sheet.nrows)
            if any(value != "" for value in sheet.row_values(i))
        ]
        if rows:
            parts.append(f"## {sheet.name}\n\n{_markdown_table(rows)}")
    return "\n\n".join(parts)


def _docx_to_markdown(path: Path) -> str:
    import docx

    document = docx.Document(str(path))
    parts = []
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue
        style = (paragraph.style.name or "").lower() if paragraph.style else ""
        if style.startswith("heading"):
            level = style.removeprefix("heading").strip()
            parts.append(f"{'#' * int(level) if level.isdigit() else '#'} {text}")
        else:
            parts.append(text)
    for table in document.tables:
        rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
        parts.append(_markdown_table(rows))
    return "\n\n".join(parts)


def _xlsx_to_markdown(path: Path) -> str:
    import openpyxl

    workbook = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
    parts = []
    for sheet in workbook.worksheets:
        rows = [
            ["" if value is None else str(value) for value in row]
            for row in sheet.iter_rows(values_only=True)
            if any(value is not None for value in row)
        ]
        if rows:
            parts.append(f"## {sheet.title}\n\n{_markdown_table(rows)}")
    return "\n\n".join(parts)


def _markdown_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    lines = ["| " + " | ".join(rows[0]) + " |", "|" + " --- |" * width]
    lines += ["| " + " | ".join(row) + " |" for row in rows[1:]]
    return "\n".join(lines)


def split_into_chunks(text: str) -> list[str]:
    """
    Split text into ~CHUNK_CHARS chunks, preferring markdown headings and paragraph breaks
    as boundaries. Consecutive chunks overlap by ~OVERLAP_CHARS.
    """
    # Blocks: heading sections, then paragraphs; oversized blocks are cut by length
    blocks = []
    for section in _split_keep_headings(text):
        for paragraph in re.split(r"\n\s*\n", section):
            paragraph = paragraph.strip()
            while len(paragraph) > CHUNK_CHARS:
                blocks.append(paragraph[:CHUNK_CHARS])
                paragraph = paragraph[CHUNK_CHARS - OVERLAP_CHARS:]
            if paragraph:
                blocks.append(paragraph)

    chunks: list[str] = []
    current = ""
    for block in blocks:
        starts_section = bool(HEADING.match(block))
        if current and (len(current) + len(block) + 2 > CHUNK_CHARS or
                        (starts_section and len(current) > CHUNK_CHARS // 2)):
            chunks.append(current)
            current = current[-OVERLAP_CHARS:] if not starts_section else ""
        current = f"{current}\n\n{block}" if current else block
    if current.strip():
        chunks.append(current)
    return chunks


def _split_keep_headings(text: str) -> list[str]:
    """Split before every markdown heading, keeping the heading with its section."""
    starts = [m.start() for m in HEADING.finditer(text)]
    if not starts or starts[0] != 0:
        starts = [0] + starts
    return [text[a:b] for a, b in zip(starts, starts[1:] + [len(text)])]


def read_sidecar(path: Path) -> dict[str, Any]:
    sidecar = path.with_name(path.name + METADATA_SUFFIX)
    if not sidecar.exists():
        return {}
    data = json.loads(sidecar.read_text(encoding="utf-8"))
    return data.get("metadataAttributes", data)


def iter_documents(source_dir: Path, industry: str | None):
    for path in sorted(source_dir.rglob("*")):
        if not path.is_file() or path.name.endswith(METADATA_SUFFIX) or path.name.startswith("."):
            continue
        if "_reports" in path.relative_to(source_dir).parts[:1]:
            continue  # the scraper CLI's run reports
        metadata = read_sidecar(path)
        if industry and industry != metadata.get("industry") \
                and industry not in (metadata.get("industries") or []):
            continue
        yield path, metadata


def index_document(path: Path, location: str, metadata: dict[str, Any]) -> tuple[str, int]:
    """Index one document. Returns (status, number of chunks)."""
    docs = local.collection()
    content_hash = hashlib.sha256(path.read_bytes()).hexdigest()[:16]

    existing = docs.get(where={"location": location}, limit=1, include=["metadatas"])
    if existing["metadatas"] and existing["metadatas"][0].get("content_hash") == content_hash:
        return "unchanged", 0

    text = extract_text(path)
    if text is None:
        return "unsupported", 0
    if len(text.strip()) < MIN_DOCUMENT_CHARS:
        logger.warning(f"{location}: only {len(text.strip())} characters of text (scanned PDF?)")
        if not text.strip():
            return "empty", 0

    chunks = split_into_chunks(text)
    chunk_metadata = local.to_chroma_metadata(
        {**metadata, "location": location, "content_hash": content_hash}
    )

    # Replace all chunks of the document, so a shorter new version leaves no stale chunks
    docs.delete(where={"location": location})
    docs.add(
        ids=[f"{location}#{i}" for i in range(len(chunks))],
        documents=chunks,
        embeddings=local.embed(chunks),
        metadatas=[{**chunk_metadata, "chunk": i} for i in range(len(chunks))],
    )
    return "indexed", len(chunks)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build the local retrieval index.")
    parser.add_argument("--source", type=Path, default=LOCAL_DATA_DIR / RAW_DATA_BUCKET,
                        help="Folder with the scraped documents (default: %(default)s)")
    parser.add_argument("--industry", help="Only index documents of this industry")
    parser.add_argument("--rebuild", action="store_true", help="Delete the index first")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s",
                        datefmt="%H:%M:%S")
    if not args.source.is_dir():
        print(f"No documents folder at {args.source}. Run the scraper first.", file=sys.stderr)
        return 2

    if args.rebuild:
        import chromadb

        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        if local.COLLECTION_NAME in [c.name for c in client.list_collections()]:
            client.delete_collection(local.COLLECTION_NAME)
        local.collection.cache_clear()

    counts: dict[str, int] = {}
    total_chunks = 0
    bucket = args.source.name
    for path, metadata in iter_documents(args.source, args.industry):
        location = f"{bucket}/{path.relative_to(args.source).as_posix()}"
        try:
            status, n_chunks = index_document(path, location, metadata)
        except Exception as e:  # one broken file must not stop the run
            logger.error(f"{location}: {e}")
            status, n_chunks = "failed", 0
        counts[status] = counts.get(status, 0) + 1
        total_chunks += n_chunks
        if status == "indexed":
            logger.info(f"{location}: {n_chunks} chunks")
        elif status in ("unsupported", "empty"):
            logger.warning(f"{location}: {status}, skipped")

    print(f"Documents: {counts}. New chunks: {total_chunks}. "
          f"Index size: {local.collection().count()} chunks in {CHROMA_DIR}")
    return 0 if not counts.get("failed") else 1


if __name__ == "__main__":
    sys.exit(main())
