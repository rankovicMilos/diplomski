"""Helpers for building storage keys and reading dates from titles and URLs."""
import re
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import unquote, urlparse

_CYRILLIC_TO_LATIN = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "ђ": "dj", "е": "e", "ж": "z",
    "з": "z", "и": "i", "ј": "j", "к": "k", "л": "l", "љ": "lj", "м": "m", "н": "n",
    "њ": "nj", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "ћ": "c", "у": "u",
    "ф": "f", "х": "h", "ц": "c", "ч": "c", "џ": "dz", "ш": "s",
}
_LATIN_DIACRITICS = {"č": "c", "ć": "c", "š": "s", "ž": "z", "đ": "dj"}

_YEAR = re.compile(r"(?<!\d)(19[89]\d|20\d{2})(?!\d)")
_QUARTER_PATTERNS = [
    (re.compile(r"\bQ([1-4])\b", re.IGNORECASE), None),
    (re.compile(r"\b([1-4])\s*\.?\s*(?:kvartal|квартал|quarter)", re.IGNORECASE), None),
    (re.compile(r"\b(prvi|први|first)\s+(?:kvartal|квартал|quarter)", re.IGNORECASE), "1"),
    (re.compile(r"\b(drugi|други|second)\s+(?:kvartal|квартал|quarter)", re.IGNORECASE), "2"),
    (re.compile(r"\b(tre[cć]i|трећи|third)\s+(?:kvartal|квартал|quarter)", re.IGNORECASE), "3"),
    (re.compile(r"\b([čc]etvrti|четврти|fourth)\s+(?:kvartal|квартал|quarter)", re.IGNORECASE), "4"),
]


def slugify(text: str, max_length: int = 80) -> str:
    """Lowercase ASCII slug; transliterates Serbian Cyrillic and Latin diacritics."""
    text = unquote(text).lower()
    text = "".join(_CYRILLIC_TO_LATIN.get(ch, _LATIN_DIACRITICS.get(ch, ch)) for ch in text)
    text = re.sub(r"\.(pdf|docx?|xlsx?|pptx|csv|html?|aspx|php)$", "", text)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:max_length].rstrip("-") or "document"


def slug_from_url(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    last = path.split("/")[-1] if path else urlparse(url).netloc
    return slugify(last)


def extract_year(*texts: Optional[str]) -> Optional[int]:
    """Latest plausible year found in the given texts (first text that has one wins)."""
    max_year = datetime.now().year + 1
    for text in texts:
        if not text:
            continue
        years = [int(y) for y in _YEAR.findall(unquote(text)) if int(y) <= max_year]
        if years:
            return max(years)
    return None


def snapshot_label(schedule: str, now: Optional[datetime] = None) -> str:
    """
    Period label for data that changes over time (datasets, live prices).

    One stored file per period: a daily source gets a new file every day, a monthly
    source overwrites nothing and is fetched again only in the next month.
    `realtime` gives every run its own file (for exchange quotes). Labels are in UTC.
    """
    now = now or datetime.now(timezone.utc)
    if schedule == "realtime":
        return now.strftime("%Y-%m-%dT%H%M%SZ")
    if schedule == "hourly":
        return now.strftime("%Y-%m-%dT%H00Z")
    if schedule == "daily":
        return now.strftime("%Y-%m-%d")
    if schedule == "weekly":
        year, week, _ = now.isocalendar()
        return f"{year}-W{week:02d}"
    if schedule == "quarterly":
        return f"{now.year}-Q{(now.month - 1) // 3 + 1}"
    if schedule == "yearly":
        return str(now.year)
    return now.strftime("%Y-%m")


def extract_quarter(*texts: Optional[str]) -> Optional[int]:
    for text in texts:
        if not text:
            continue
        text = unquote(text)
        for pattern, fixed in _QUARTER_PATTERNS:
            match = pattern.search(text)
            if match:
                return int(fixed or match.group(1))
    return None
