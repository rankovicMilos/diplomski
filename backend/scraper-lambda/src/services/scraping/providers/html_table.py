"""Live provider that reads price tables from static HTML (indexmundi, autotraveler, ...)."""
from typing import Any

from bs4 import BeautifulSoup

from ..core.exceptions import FetchError
from ..core.models import DataTable, LiveSnapshot
from ..core.text_extractor import table_to_rows
from .base import BaseLiveProvider
from .factory import ProviderFactory
from .timestamps import find_source_timestamp


@ProviderFactory.register("html_table")
class HtmlTableProvider(BaseLiveProvider):
    """
    params:
      tables: list of table specs (default: every table with at least 2 rows)
        header_contains: text that must appear in the table's first row
        title:           title of the table in the output
        titles:          one title per table when count > 1
        count:           how many matching tables to take (default 1)
        max_rows:        cap on rows (default 200)
      timestamp_selector / timestamp_pattern / source_timezone:
                       where to read the quote time (see providers/timestamps.py)
    """

    def snapshot(self, url: str) -> LiveSnapshot:
        page = self.fetcher.get(url)
        soup = BeautifulSoup(page.text, "lxml")
        leaf_tables = [
            rows for t in soup.find_all("table")
            if not t.find("table") and len(rows := table_to_rows(t)) >= 2
        ]

        tables: list[DataTable] = []
        for spec in self.params.get("tables") or [{"count": len(leaf_tables)}]:
            tables.extend(self._select(leaf_tables, spec, page.url))
        if not tables:
            raise FetchError("No matching table found on the page", url=url)

        source_timestamp, origin = find_source_timestamp(soup, self.params)
        return LiveSnapshot(
            title=_meta(soup, "og:title") or (soup.title.get_text(strip=True) if soup.title else url),
            summary=_meta(soup, "description") or "",
            tables=tables,
            source_timestamp=source_timestamp,
            source_timestamp_origin=origin,
        )

    @staticmethod
    def _select(leaf_tables: list[list[list[str]]], spec: dict[str, Any], url: str) -> list[DataTable]:
        needle = (spec.get("header_contains") or "").lower()
        matching = [rows for rows in leaf_tables if needle in " ".join(rows[0]).lower()]
        max_rows = int(spec.get("max_rows", 200))
        count = int(spec.get("count", 1))
        titles = spec.get("titles") or []
        return [
            DataTable(
                title=titles[i] if i < len(titles) else spec.get("title") or f"Table {i + 1}",
                columns=rows[0],
                rows=rows[1: max_rows + 1],
                source_url=url,
            )
            for i, rows in enumerate(matching[:count])
        ]


def _meta(soup: BeautifulSoup, name: str) -> str:
    tag = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
    return tag["content"].strip() if tag and tag.get("content") else ""
