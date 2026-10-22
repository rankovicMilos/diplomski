"""
Analysis period: the last N completed calendar years (N = ANALYSIS_YEARS_BACK, default 2).

In 2026 that is [2024, 2025]; the window moves on by itself every January. Scrapers use it
to keep only data and documents from the period (CSV rows, crawled listings).
"""
import os
import re
from datetime import datetime, timezone
from typing import Optional

DEFAULT_YEARS_BACK = 2

_YEAR = re.compile(r"(?<!\d)(19[89]\d|20\d{2})(?!\d)")


def analysis_years(now: Optional[datetime] = None) -> list[int]:
    years_back = int(os.environ.get("ANALYSIS_YEARS_BACK", DEFAULT_YEARS_BACK))
    current = (now or datetime.now(timezone.utc)).year
    return list(range(current - years_back, current))


def years_in(text: str) -> list[int]:
    """All years in a period value, e.g. "2024" -> [2024], "2024M03" -> [2024], "2023/24" -> [2023]."""
    return [int(y) for y in _YEAR.findall(text or "")]
