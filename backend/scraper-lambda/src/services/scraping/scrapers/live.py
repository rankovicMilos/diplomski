"""Scraper for pages with continuously changing values (commodity prices, fuel prices, quotes)."""
import csv
import io
from typing import Any, Optional

from ..core.file_detector import content_type_for
from ..core.models import DocumentRef, LiveSnapshot, OutputDocument, StoredDocument
from ..core.naming import snapshot_label
from ..providers import BaseLiveProvider, ProviderFactory
from .base import KEY_ROOT, BaseScraper
from .factory import ScraperFactory
from .tables import rows_to_csv, table_to_markdown

HISTORY_COLUMNS = ["observed_at", "source_timestamp", "table"]


@ScraperFactory.register("live")
class LiveScraper(BaseScraper):
    """
    Takes a snapshot of a live page through a provider once per `schedule` period.

    Outputs per run:
      - {period}.md   snapshot for the knowledge base (summary + current tables)
      - history.csv   every snapshot so far, one row per table row

    Every snapshot carries two timestamps:
      observed_at       when the scraper read the page (UTC)
      source_timestamp  the quote time published by the source, if any

    Use `schedule: realtime` for exchange quotes: every run is kept as its own snapshot
    (file name = UTC time of the run). `hourly` keeps one snapshot per hour.

    params:
      provider: html_table | meta_description   (other params: see the provider)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.provider: BaseLiveProvider = ProviderFactory.create(
            self.params.get("provider"), self.fetcher, self.params, BaseLiveProvider
        )
        self._snapshot: Optional[LiveSnapshot] = None

    def discover(self) -> list[DocumentRef]:
        return [DocumentRef(url=self.config.url, title=self.config.name,
                            period=snapshot_label(self.config.schedule))]

    def fetch(self, ref: DocumentRef) -> LiveSnapshot:
        return self.provider.snapshot(ref.url)

    def transform(self, raw: LiveSnapshot, ref: DocumentRef) -> list[OutputDocument]:
        self._snapshot = raw
        body = self.markdown_header(raw.title, ref)
        body += f"- Observed at (UTC): {raw.observed_at}\n"
        body += f"- Source timestamp: {raw.source_timestamp or 'not published by source'}"
        if raw.source_timestamp_origin:
            body += f" (from {raw.source_timestamp_origin})"
        body += "\n\n"
        if raw.summary:
            body += raw.summary + "\n\n"
        body += "\n\n".join(table_to_markdown(t) for t in raw.tables) + "\n"
        snapshot = StoredDocument(body.encode("utf-8"), ".md", content_type_for(".md"))

        return [
            OutputDocument(stem=self.build_stem(ref), document=snapshot),
            OutputDocument(stem=self._history_stem(), document=self._history(raw)),
        ]

    def build_stem(self, ref: DocumentRef) -> str:
        return f"{self._folder()}/{ref.period}"

    def build_metadata(self, ref: DocumentRef, output: OutputDocument) -> dict[str, Any]:
        metadata = super().build_metadata(ref, output)
        if self._snapshot:
            metadata["observed_at"] = self._snapshot.observed_at
            if self._snapshot.source_timestamp:
                metadata["source_timestamp"] = self._snapshot.source_timestamp
                metadata["source_timestamp_origin"] = self._snapshot.source_timestamp_origin
        return metadata

    def _history_stem(self) -> str:
        return f"{self._folder()}/history"

    def _folder(self) -> str:
        return f"{KEY_ROOT}/{self.config.primary_industry}/{self.config.id}"

    def _history(self, snapshot: LiveSnapshot) -> StoredDocument:
        """Append this snapshot's rows to the existing history.csv."""
        existing_key = self.storage.find(self._history_stem())
        existing = self.storage.read(existing_key) if existing_key else None

        new_rows, header = [], None
        for table in snapshot.tables:
            header = header or HISTORY_COLUMNS + table.columns
            new_rows.extend(
                [snapshot.observed_at, snapshot.source_timestamp or "", table.title, *row]
                for row in table.rows
            )

        if existing:
            previous = list(csv.reader(io.StringIO(existing.decode("utf-8"))))
            content = rows_to_csv(previous[0], previous[1:] + new_rows)
        else:
            content = rows_to_csv(header or HISTORY_COLUMNS, new_rows)
        return StoredDocument(content.encode("utf-8"), ".csv", content_type_for(".csv"))
