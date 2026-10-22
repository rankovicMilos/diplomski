"""Base class for all config-driven scrapers."""
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional

from ..core.csv_table import parse_csv
from ..core.exceptions import FetchError, NotFoundError, ScraperError
from ..core.fetchers import BaseFetcher
from ..core.file_detector import content_type_for, detect_extension, is_html
from ..core.models import (
    DocumentRef,
    FetchedContent,
    OutputDocument,
    ScrapeResult,
    SourceConfig,
    StoredDocument,
    Usage,
)
from ..core.naming import slug_from_url, slugify, snapshot_label
from ..core.storage import BaseStorage
from ..core.text_extractor import extract_page
from .tables import table_to_markdown

logger = logging.getLogger(__name__)

KEY_ROOT = "raw"
MIN_ARTICLE_CHARS = 200
# Extracted article text must be at least this share of all visible text on the page;
# below it the extractor most likely picked a footer or a teaser instead of the article.
MIN_TEXT_SHARE = 0.2


class BaseScraper(ABC):
    """
    Template for a scraper: discover -> fetch -> transform -> save.

    `run()` holds the shared flow (skipping existing documents, error handling, metadata)
    and must not be overridden. Subclasses implement `discover()` and override `fetch()`,
    `transform()` or `build_stem()` only where their source type differs.

    params shared by all strategies:
      refresh:  true = store a new copy every `schedule` period (data revised over time);
                default: a stored document is never downloaded again
      csv:      options for CSV downloads, which are stored as markdown tables
                (see core/csv_table.py)
    """

    def __init__(
        self,
        config: SourceConfig,
        fetcher: BaseFetcher,
        storage: BaseStorage,
        force: bool = False,
    ):
        self.config = config
        self.params = config.params
        self.fetcher = fetcher
        self.storage = storage
        self.force = force

    def run(self, limit: Optional[int] = None) -> ScrapeResult:
        result = ScrapeResult(source_id=self.config.id)
        logger.info(f"[{self.config.id}] {type(self).__name__} starting")

        try:
            refs = self._dedupe(self.discover())
        except ScraperError as e:
            result.errors.append(f"discover: {type(e).__name__}: {e}")
            return result.finalize()

        if limit:
            refs = refs[:limit]
        if not refs:
            # A configured source that yields nothing is broken (selector, site change, ...)
            result.errors.append("No documents found; check the source's selectors/filters")
        logger.info(f"[{self.config.id}] {len(refs)} document(s) to process")

        for ref in refs:
            self._process(ref, result)

        return result.finalize()

    def _process(self, ref: DocumentRef, result: ScrapeResult) -> None:
        stem = self.build_stem(ref)
        if not self.force and self.storage.exists(stem):
            logger.info(f"[{self.config.id}] exists, skipping: {stem}")
            result.skipped_existing += 1
            return

        try:
            raw = self.fetch(ref)
            outputs = self.transform(raw, ref)
        except NotFoundError as e:
            if ref.extra.get("optional"):
                logger.info(f"[{self.config.id}] optional document not published yet: {ref.url}")
                return
            result.errors.append(f"{ref.url}: {e}")
            return
        except ScraperError as e:
            result.errors.append(f"{ref.url}: {type(e).__name__}: {e}")
            return
        except Exception as e:
            logger.exception(f"[{self.config.id}] unexpected error for {ref.url}")
            result.errors.append(f"{ref.url}: unexpected {type(e).__name__}: {e}")
            return

        for output in outputs:
            try:
                location = self.storage.save(
                    output.stem, output.document, self.build_metadata(ref, output)
                )
            except Exception as e:
                # A failed write (disk, path length, S3) must not stop the other sources
                logger.exception(f"[{self.config.id}] could not save {output.stem}")
                result.errors.append(f"{ref.url}: save failed: {type(e).__name__}: {e}")
                continue
            logger.info(f"[{self.config.id}] saved {location}")
            result.saved.append({
                "location": location,
                "url": ref.url,
                "title": ref.title,
                "size_bytes": len(output.document.content),
            })

    @abstractmethod
    def discover(self) -> list[DocumentRef]:
        """Find the documents this source provides."""

    def fetch(self, ref: DocumentRef) -> Any:
        return self.fetcher.get(ref.url)

    def transform(self, raw: Any, ref: DocumentRef) -> list[OutputDocument]:
        return [OutputDocument(stem=self.build_stem(ref), document=self.to_document(raw, ref))]

    def build_stem(self, ref: DocumentRef) -> str:
        """Storage key without extension: raw/{industry}/{source_id}/[{year}/]{slug}."""
        parts = [KEY_ROOT, self.config.primary_industry, self.config.id]
        if ref.year:
            parts.append(str(ref.year))
        slug = self.slug_for(ref)
        if self.params.get("refresh"):
            # Data that is revised over time: one stored copy per schedule period
            slug = f"{slug}_{snapshot_label(self.config.schedule)}"
        parts.append(slug)
        return "/".join(parts)

    def build_metadata(self, ref: DocumentRef, output: OutputDocument) -> dict[str, Any]:
        usages = self.usages_for(ref)
        metadata: dict[str, Any] = {
            "source_id": self.config.id,
            "source_name": self.config.name,
            "source_url": ref.url,
            "parent_url": ref.parent_url,
            "strategy": self.config.strategy,
            "industry": self.config.primary_industry,
            "industries": sorted({u.industry for u in usages}),
            "sections": sorted({u.section for u in usages}),
            "subsections": sorted({u.subsection for u in usages if u.subsection}),
            "topics": sorted({u.topic for u in usages if u.topic}),
            "document_title": (ref.title or "")[:200],
            "year": ref.year,
            "period": ref.period,
            "scraped_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        return {k: v for k, v in metadata.items() if v not in (None, "", [])}

    def usages_for(self, ref: DocumentRef) -> list[Usage]:
        return ref.usages or self.config.usages

    def slug_for(self, ref: DocumentRef) -> str:
        if ref.extra.get("slug"):
            return ref.extra["slug"]
        if ref.title:
            return slugify(ref.title)
        return slug_from_url(ref.url)

    def to_document(self, raw: FetchedContent, ref: DocumentRef) -> StoredDocument:
        """
        Keep documents (PDF, DOCX, ...) as they are; convert HTML pages and CSV exports
        to markdown, so the knowledge base gets readable text with a provenance header.
        """
        if is_html(raw.content, raw.content_type):
            return self.html_to_markdown(raw, ref)
        extension = detect_extension(raw.content, raw.content_type, raw.url)
        if extension == ".csv":
            return self.csv_to_markdown(raw, ref)
        return StoredDocument(raw.content, extension, content_type_for(extension))

    def csv_to_markdown(self, raw: FetchedContent, ref: DocumentRef) -> StoredDocument:
        title = ref.title or self.config.name
        table = parse_csv(raw.content, title, raw.url, self.params.get("csv") or {})
        body = self.markdown_header(title, ref) + table_to_markdown(table) + "\n"
        return StoredDocument(body.encode("utf-8"), ".md", content_type_for(".md"))

    def html_to_markdown(self, raw: FetchedContent, ref: DocumentRef) -> StoredDocument:
        page = extract_page(raw.text, raw.url, self.params.get("content_selector"))
        if len(page.markdown) < MIN_ARTICLE_CHARS:
            raise FetchError(
                f"Page has almost no text ({len(page.markdown)} chars); it may need "
                f"fetch_mode: browser or a content_selector",
                url=raw.url,
            )
        if page.page_text_chars > 2000 and len(page.markdown) < page.page_text_chars * MIN_TEXT_SHARE:
            raise FetchError(
                f"Extracted only {len(page.markdown)} of {page.page_text_chars} chars on the page; "
                f"the main content was probably missed. Set params.content_selector",
                url=raw.url,
            )
        title = page.title or ref.title or self.config.name
        body = self.markdown_header(title, ref, published=page.published) + page.markdown + "\n"
        return StoredDocument(body.encode("utf-8"), ".md", content_type_for(".md"))

    def markdown_header(self, title: str, ref: DocumentRef, published: Optional[str] = None) -> str:
        """Context block at the top of every markdown file, so retrieved chunks carry provenance."""
        usages = self.usages_for(ref)
        sections = sorted({
            " > ".join(filter(None, [u.section.replace("_", " ").title(), u.subsection]))
            for u in usages
        })
        lines = [
            f"# {title}",
            "",
            f"- Source: {self.config.name}",
            f"- URL: {ref.url}",
            f"- Industry: {', '.join(sorted({u.industry for u in usages}))}",
            f"- Report sections: {'; '.join(sections)}",
        ]
        if published:
            lines.append(f"- Published: {published}")
        lines.append(f"- Retrieved: {datetime.now(timezone.utc).date().isoformat()}")
        return "\n".join(lines) + "\n\n---\n\n"

    @staticmethod
    def _dedupe(refs: list[DocumentRef]) -> list[DocumentRef]:
        seen, unique = set(), []
        for ref in refs:
            if ref.url not in seen:
                seen.add(ref.url)
                unique.append(ref)
        return unique

    def close(self) -> None:
        self.fetcher.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
