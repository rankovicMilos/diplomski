"""
Find the time a live page says its values are valid for (the quote time).

Lookup order:
  1. params.timestamp_selector  CSS selector of an element holding the time
  2. params.timestamp_pattern   regex on the page text; the first group is the time
  3. JSON-LD dateModified / datePublished
  4. meta tags (article:modified_time, og:updated_time, ...)

Steps 3 and 4 describe when the *page* changed, which is not always when the prices
changed. Set params.page_metadata_timestamp: false for sources where they are misleading.

The result is normalized to ISO 8601 when the format is recognized. Times without a
zone are kept without one; set params.source_timezone to document the source's zone.
"""
import json
import re
from datetime import datetime
from typing import Any, Optional

from bs4 import BeautifulSoup

META_TIME_TAGS = ["article:modified_time", "og:updated_time", "article:published_time",
                  "dateModified", "last-modified"]

_FORMATS = [
    ("%Y%m%dT%H:%M:%S.%fZ", True),    # 20260923T12:00:00.00Z (Trading Economics)
    ("%Y-%m-%dT%H:%M:%S.%fZ", True),
    ("%Y-%m-%dT%H:%M:%SZ", True),
    ("%Y-%m-%dT%H:%M:%S%z", False),
    ("%Y-%m-%dT%H:%M:%S", False),
    ("%Y-%m-%d %H:%M:%S", False),     # 2026-05-12 10:00:02 (Autotraveler)
    ("%Y-%m-%d %H:%M", False),
    ("%Y-%m-%d", False),
    ("%B %d, %Y", False),             # September 23, 2026
    ("%b %d, %Y", False),
    ("%d.%m.%Y %H:%M", False),
    ("%d.%m.%Y", False),
    ("%B %Y", False),                 # May 2026 (IndexMundi "Data as of")
    ("%b %Y", False),
]


def find_source_timestamp(
    soup: BeautifulSoup, params: dict[str, Any]
) -> tuple[Optional[str], Optional[str]]:
    """Return (timestamp, origin) or (None, None)."""
    selector = params.get("timestamp_selector")
    if selector:
        node = soup.select_one(selector)
        if node:
            raw = node.get("datetime") or node.get("content") or node.get_text(" ", strip=True)
            return normalize(raw, params), f"selector {selector}"

    pattern = params.get("timestamp_pattern")
    if pattern:
        match = re.search(pattern, soup.get_text(" ", strip=True))
        if match:
            return normalize(match.group(1), params), "timestamp_pattern"

    if not params.get("page_metadata_timestamp", True):
        return None, None

    for key in ("dateModified", "datePublished"):
        value = _json_ld_value(soup, key)
        if value:
            return normalize(value, params), f"JSON-LD {key}"

    for name in META_TIME_TAGS:
        tag = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return normalize(tag["content"], params), f"meta {name}"
    return None, None


def normalize(raw: str, params: Optional[dict[str, Any]] = None) -> str:
    """ISO 8601 when the format is known, otherwise the original text."""
    text = re.sub(r"\s+", " ", raw or "").strip()
    for fmt, is_utc in _FORMATS:
        try:
            parsed = datetime.strptime(text, fmt)
        except ValueError:
            continue
        if is_utc:
            return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")
        if parsed.tzinfo:
            return parsed.isoformat()
        if "%H" not in fmt:
            return parsed.strftime("%Y-%m" if "%d" not in fmt else "%Y-%m-%d")
        zone = (params or {}).get("source_timezone")
        iso = parsed.strftime("%Y-%m-%dT%H:%M:%S")
        return f"{iso} ({zone})" if zone else iso
    return text


def _json_ld_value(soup: BeautifulSoup, key: str) -> Optional[str]:
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        for item in data if isinstance(data, list) else [data]:
            if isinstance(item, dict) and item.get(key):
                return str(item[key])
    return None
