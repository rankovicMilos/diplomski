"""
Detect a document's real file type.

Servers often send wrong content types (e.g. minpolj.gov.rs serves .doc files as .docx),
so magic bytes are checked first, then the content-type header, then the URL.
"""
import re
from typing import Optional

OLE_SIGNATURE = b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1"   # legacy .doc / .xls
ZIP_SIGNATURE = b"PK\x03\x04"                          # .docx / .xlsx / .pptx
PDF_SIGNATURE = b"%PDF"

CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".doc": "application/msword",
    ".xls": "application/vnd.ms-excel",
    ".csv": "text/csv; charset=utf-8",
    ".json": "application/json",
    ".md": "text/markdown; charset=utf-8",
    ".html": "text/html; charset=utf-8",
    ".zip": "application/zip",
}

_HEADER_TYPES = [
    ("pdf", ".pdf"),
    ("wordprocessingml", ".docx"),
    ("spreadsheetml", ".xlsx"),
    ("presentationml", ".pptx"),
    ("msword", ".doc"),
    ("ms-excel", ".xls"),
    ("csv", ".csv"),               # text/csv, application/vnd.sdmx.data+csv (Eurostat)
    ("json", ".json"),
    ("html", ".html"),
]

_URL_EXTENSION = re.compile(r"\.(pdf|docx?|xlsx?|pptx|csv|json|zip)(?:$|[?#])", re.IGNORECASE)


def detect_extension(content: bytes, content_type: str = "", url: str = "") -> str:
    """Return the file extension (with dot) that matches the content."""
    return (
        _from_magic_bytes(content)
        or _from_content_type(content_type)
        or _from_url(url)
        or (".html" if looks_like_html(content) else ".bin")
    )


def is_html(content: bytes, content_type: str = "") -> bool:
    if _from_magic_bytes(content):
        return False
    return "html" in content_type or looks_like_html(content)


def looks_like_html(content: bytes) -> bool:
    head = content[:1024].lstrip().lower()
    return head.startswith((b"<!doctype html", b"<html")) or b"<head" in head or b"<body" in head


def content_type_for(extension: str) -> str:
    return CONTENT_TYPES.get(extension, "application/octet-stream")


def _from_magic_bytes(content: bytes) -> Optional[str]:
    if content[:4] == PDF_SIGNATURE:
        return ".pdf"
    if content[:8] == OLE_SIGNATURE:
        if b"W\x00o\x00r\x00k\x00b\x00o\x00o\x00k" in content or b"Workbook" in content:
            return ".xls"
        return ".doc"
    if content[:4] == ZIP_SIGNATURE:
        head = content[:65536]
        if b"word/" in head:
            return ".docx"
        if b"xl/" in head:
            return ".xlsx"
        if b"ppt/" in head:
            return ".pptx"
        return ".zip"
    return None


def _from_content_type(content_type: str) -> Optional[str]:
    content_type = content_type.lower()
    for marker, extension in _HEADER_TYPES:
        if marker in content_type:
            return extension
    return None


def _from_url(url: str) -> Optional[str]:
    match = _URL_EXTENSION.search(url)
    return f".{match.group(1).lower()}" if match else None
