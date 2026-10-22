"""Data models shared by the config loader, scrapers, fetchers and storage."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class SourceStatus(str, Enum):
    """Whether a source is scraped, and if not, why."""

    ACTIVE = "active"
    LEGACY = "legacy"                            # still handled by the old scrapers in sources/
    BLOCKED = "blocked"                          # bot protection (e.g. Cloudflare)
    PAYWALL = "paywall"                          # requires login or subscription
    NOT_FOUND = "not_found"                      # URL no longer exists
    NEEDS_CLARIFICATION = "needs_clarification"  # URL is too generic to know what to scrape


@dataclass(frozen=True)
class Usage:
    """Where a source is used in the credit risk report."""

    industry: str
    section: str
    subsection: Optional[str] = None
    topic: Optional[str] = None      # e.g. crop or product, used for filtering and keys
    keyword: Optional[str] = None    # title keyword that assigns a crawled document to this usage


@dataclass
class FetchOptions:
    """Per-source request settings (merged from _defaults.yaml and the source's `fetch` block)."""

    timeout: float = 60.0
    verify_ssl: bool = True
    retries: int = 2
    delay_seconds: float = 0.5
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    )
    headers: dict[str, str] = field(default_factory=dict)
    # Browser fetcher only
    wait_until: str = "networkidle"
    wait_for_selector: Optional[str] = None


@dataclass
class SourceConfig:
    """One entry from config/sources/*.yaml."""

    id: str
    name: str
    strategy: str
    usages: list[Usage]
    url: Optional[str] = None
    fetch_mode: str = "http"
    status: SourceStatus = SourceStatus.ACTIVE
    params: dict[str, Any] = field(default_factory=dict)
    fetch: FetchOptions = field(default_factory=FetchOptions)
    schedule: str = "monthly"
    notes: Optional[str] = None
    config_file: Optional[str] = None

    @property
    def industries(self) -> list[str]:
        return sorted({u.industry for u in self.usages})

    @property
    def primary_industry(self) -> str:
        return self.usages[0].industry if self.usages else "general"

    @property
    def is_active(self) -> bool:
        return self.status == SourceStatus.ACTIVE


@dataclass
class DocumentRef:
    """A document found by a scraper's discover() step, before it is fetched."""

    url: str
    title: Optional[str] = None
    year: Optional[int] = None
    period: Optional[str] = None                 # e.g. "Q4", "2025-07"
    usages: Optional[list[Usage]] = None         # subset of source usages; None means all
    parent_url: Optional[str] = None             # page the link was found on
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class FetchedContent:
    """Raw response of a fetch."""

    url: str
    content: bytes
    content_type: str = ""
    status_code: int = 200

    @property
    def text(self) -> str:
        for encoding in ("utf-8", "cp1250", "latin-1"):
            try:
                return self.content.decode(encoding)
            except UnicodeDecodeError:
                continue
        return self.content.decode("utf-8", errors="replace")


@dataclass
class DataTable:
    """Tabular data returned by dataset and live providers."""

    title: str
    columns: list[str]
    rows: list[list[Any]]
    source_url: str = ""
    notes: list[str] = field(default_factory=list)


def utc_now_iso() -> str:
    """Current UTC time as ISO 8601 with a Z suffix, e.g. 2026-09-23T12:00:05Z."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class LiveSnapshot:
    """
    Current values read from a live price page.

    Two timestamps are kept apart on purpose:
      observed_at       when the scraper read the page (always known, UTC)
      source_timestamp  when the source says the values are valid (quote time); may be missing
    """

    title: str
    summary: str = ""
    tables: list[DataTable] = field(default_factory=list)
    observed_at: str = field(default_factory=utc_now_iso)
    source_timestamp: Optional[str] = None
    source_timestamp_origin: Optional[str] = None   # where source_timestamp was read from


@dataclass
class StoredDocument:
    """A document ready to be written to storage."""

    content: bytes
    extension: str        # with leading dot, e.g. ".pdf"
    content_type: str


@dataclass
class OutputDocument:
    """A document produced by transform() plus where to store it."""

    stem: str             # storage key without extension
    document: StoredDocument


@dataclass
class ScrapeResult:
    """Outcome of running one source."""

    source_id: str
    status: str = "success"             # success | partial | error | skipped
    saved: list[dict[str, Any]] = field(default_factory=list)
    skipped_existing: int = 0
    errors: list[str] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    message: Optional[str] = None
    duration_seconds: Optional[float] = None

    def finalize(self) -> "ScrapeResult":
        if self.status == "skipped":
            return self
        if self.errors and not self.saved and not self.skipped_existing:
            self.status = "error"
        elif self.errors:
            self.status = "partial"
        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "status": self.status,
            "saved": self.saved,
            "saved_count": len(self.saved),
            "skipped_existing": self.skipped_existing,
            "errors": self.errors,
            "message": self.message,
            "duration_seconds": self.duration_seconds,
        }
