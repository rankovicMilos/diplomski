"""
Keep a generated report inside its analysis period.

The prompt tells the model to report only the analysis years; this is the safety net for
tables and charts: rows and data points that belong only to other years are removed, and
a table or chart left without data is dropped together with its {{table:id}} /
{{chart:id}} placeholder. Values without a year (e.g. a company name) are kept.
"""
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_YEAR = re.compile(r"(?<!\d)(19[89]\d|20\d{2})(?!\d)")
_PERIOD_COLUMNS = ("period", "year", "marketing_year", "date")
# The frontend needs at least two points to draw a chart
MIN_CHART_POINTS = 2


def restrict_to_years(result: dict[str, Any], years: list[int]) -> dict[str, int]:
    """
    Remove table rows and chart points outside `years` from the report, in place.

    Returns:
        Counts of what was removed (for logging and retrieval_stats)
    """
    allowed = set(years)
    removed = {"table_rows": 0, "tables": 0, "chart_points": 0, "charts": 0}
    dropped_ids: list[tuple[str, str]] = []

    tables = []
    for table in result.get("tables") or []:
        index = _period_column(table.get("columns") or [])
        rows = table.get("rows") or []
        if index is not None:
            kept = [r for r in rows if _in_period(r[index] if index < len(r) else None, allowed)]
            removed["table_rows"] += len(rows) - len(kept)
            table["rows"] = kept
        if rows and not table["rows"]:
            removed["tables"] += 1
            dropped_ids.append(("table", table.get("id", "")))
            continue
        tables.append(table)
    if "tables" in result:
        result["tables"] = tables

    charts = []
    for chart in result.get("charts") or []:
        data = chart.get("data") or []
        kept = [p for p in data if _in_period(p.get("label") if isinstance(p, dict) else None, allowed)]
        removed["chart_points"] += len(data) - len(kept)
        chart["data"] = kept
        if len(kept) < MIN_CHART_POINTS:
            removed["charts"] += 1
            dropped_ids.append(("chart", chart.get("id", "")))
            continue
        charts.append(chart)
    if "charts" in result:
        result["charts"] = charts

    if dropped_ids:
        _remove_placeholders(result, dropped_ids)
    if any(removed.values()):
        logger.info(f"Removed content outside the period {sorted(allowed)}: {removed}")
    return removed


def _period_column(columns: list[Any]) -> int | None:
    for i, column in enumerate(columns):
        names = [column.get("id"), column.get("name")] if isinstance(column, dict) else [column]
        for name in names:
            if isinstance(name, str) and name.strip().lower().replace(" ", "_") in _PERIOD_COLUMNS:
                return i
    return None


def _in_period(value: Any, allowed: set[int]) -> bool:
    """True if the value has no year or mentions at least one allowed year."""
    if value is None:
        return True
    found = [int(y) for y in _YEAR.findall(str(value))]
    return not found or any(y in allowed for y in found)


def _remove_placeholders(result: dict[str, Any], dropped: list[tuple[str, str]]) -> None:
    for section in result.get("sections") or []:
        text = section.get("content_md")
        if not isinstance(text, str):
            continue
        for kind, item_id in dropped:
            text = text.replace(f"{{{{{kind}:{item_id}}}}}", "")
        section["content_md"] = re.sub(r"\n{3,}", "\n\n", text)
