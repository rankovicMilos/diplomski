"""Scraper for document listing pages and multi-level navigation."""
import logging
import re
from typing import Any, Optional
from urllib.parse import unquote, urljoin

from bs4 import BeautifulSoup

from ..core.exceptions import FetchError
from ..core.models import DocumentRef
from ..core.naming import extract_quarter, extract_year, slug_from_url, slugify
from ..core.period import analysis_years
from .base import BaseScraper
from .factory import ScraperFactory

logger = logging.getLogger(__name__)

DOCUMENT_URL = re.compile(r"\.(pdf|xlsx?|docx?|csv|zip)($|\?)", re.IGNORECASE)


@ScraperFactory.register("crawl")
class CrawlScraper(BaseScraper):
    """
    Follows links from `url` through one or more steps.

    One step is a document listing page (links on the page are the documents).
    Several steps are navigation: every step but the last selects pages to open,
    the last step selects the documents. Filters of the first step apply to the whole
    start page; filters of later steps apply to each opened page separately. Documents
    inherit usages, year, quarter and title from the page they were found on.

    params:
      content_selector: CSS selector of the article body when a document is an HTML page
      steps:            list of steps, each with:
        wait_for_selector: (fetch_mode browser) wait for this element before reading the page
        item_selector:  CSS selector of one entry (optional; then link/title are searched in it)
        link_selector:  CSS selector of the link (default "a[href]")
        link_attr:      attribute holding the URL (default "href")
        title_selector: CSS selector of the title inside the entry (default: link text)
        link_pattern:   regex the absolute URL must match
        title_filter:   keep entries whose title or URL contains one of these words
        exclude:        drop entries whose title or URL contains one of these words
        match_usages:   keep entries whose title contains a usage `keyword` and tag them with it
        years:          keep entries from these years
        min_year:       keep entries from this year onward; default: the start of the
                        analysis period (core/period.py), entries without a year are kept;
                        null keeps all years
        latest:         keep the N newest entries (per usage when match_usages is set)
        max:            keep at most N entries in page order
    """

    def discover(self) -> list[DocumentRef]:
        steps: list[dict[str, Any]] = self.params.get("steps") or [{}]
        pages: list[Optional[DocumentRef]] = [None]   # None = the source's own url

        for index, step in enumerate(steps):
            entries: list[DocumentRef] = []
            if index == 0:
                # First step: filters apply to all links on the start page together
                entries = self._apply_filters(
                    self._dedupe(self._entries_on_page(self.config.url, step, is_root=True)), step
                )
            else:
                # Later steps: filters apply per opened page ("first PDF on each report page")
                for parent in pages:
                    children = self._entries_on_page(parent.url, step, is_root=False)
                    children = self._apply_filters(self._dedupe(children), step)
                    entries.extend(self._inherit(parent, children))
            entries = self._dedupe(entries)
            logger.info(f"[{self.config.id}] step {index + 1}/{len(steps)}: {len(entries)} link(s)")
            pages = entries
        return pages

    @staticmethod
    def _inherit(parent: DocumentRef, children: list[DocumentRef]) -> list[DocumentRef]:
        """
        Documents found on a page take over what the page already knew.

        E.g. a CBRE report page "Belgrade Office Figures Q2 2026" links a PDF named
        "Belgrade_Office_Figures_Q2_202.pdf" with the link text "Download": the PDF keeps
        the page's segment (usages), year, quarter and title.
        """
        parent_slug = parent.extra.get("slug") or slugify(parent.title or parent.url)
        for child in children:
            if child.usages is None:
                child.usages = parent.usages
            if parent.year and (child.year is None or child.year < parent.year):
                child.year, child.period = parent.year, parent.period
                child.extra["quarter"] = parent.extra.get("quarter", 0)
            if parent.title:
                child.title = parent.title
            child.extra["slug"] = (
                parent_slug if len(children) == 1 else f"{parent_slug}-{child.extra['slug']}"
            )
        return children

    def _entries_on_page(self, page_url: str, step: dict[str, Any], is_root: bool) -> list[DocumentRef]:
        try:
            page = self.fetcher.get(page_url, wait_for_selector=step.get("wait_for_selector"))
        except FetchError as e:
            if is_root:
                raise
            logger.warning(f"[{self.config.id}] skipping page {page_url}: {e}")
            return []

        soup = BeautifulSoup(page.text, "lxml")
        link_selector = step.get("link_selector", "a[href]")
        link_attr = step.get("link_attr", "href")
        item_selector = step.get("item_selector")

        entries = []
        containers = soup.select(item_selector) if item_selector else [soup]
        for container in containers:
            links = container.select(link_selector)
            if item_selector:
                links = links[:1]
            for link in links:
                raw_url = (link.get(link_attr) or "").strip()
                if not raw_url or raw_url.startswith(("#", "javascript:", "mailto:")):
                    continue
                url = urljoin(page.url, raw_url)
                title = self._title(container, link, step) if item_selector else self._link_text(link)
                entries.append(self._make_ref(url, title, page.url, order=len(entries)))
        return entries

    @staticmethod
    def _title(container, link, step: dict[str, Any]) -> str:
        selector = step.get("title_selector")
        node = container.select_one(selector) if selector else None
        return (node.get_text(" ", strip=True) if node else "") or CrawlScraper._link_text(link)

    @staticmethod
    def _link_text(link) -> str:
        return link.get_text(" ", strip=True) or link.get("title") or ""

    @staticmethod
    def _make_ref(url: str, title: str, parent_url: str, order: int) -> DocumentRef:
        quarter = extract_quarter(title, url)
        year = extract_year(title, url)
        slug = slug_from_url(url) if DOCUMENT_URL.search(url) or not title else slugify(title)
        return DocumentRef(
            url=url,
            title=title or None,
            year=year,
            period=f"Q{quarter}" if quarter else None,
            parent_url=parent_url,
            extra={"slug": slug, "order": order, "quarter": quarter or 0},
        )

    def _apply_filters(self, entries: list[DocumentRef], step: dict[str, Any]) -> list[DocumentRef]:
        if step.get("link_pattern"):
            pattern = re.compile(step["link_pattern"], re.IGNORECASE)
            entries = [e for e in entries if pattern.search(e.url)]

        if step.get("title_filter"):
            words = [w.lower() for w in step["title_filter"]]
            entries = [e for e in entries if any(w in self._haystack(e) for w in words)]

        if step.get("exclude"):
            words = [w.lower() for w in step["exclude"]]
            entries = [e for e in entries if not any(w in self._haystack(e) for w in words)]

        if step.get("match_usages"):
            entries = self._match_usages(entries)

        if step.get("years"):
            years = {int(y) for y in step["years"]}
            entries = [e for e in entries if e.year in years]

        if step.get("min_year"):
            entries = [e for e in entries if e.year and e.year >= int(step["min_year"])]
        elif "min_year" not in step:
            start = min(analysis_years())
            entries = [e for e in entries if not e.year or e.year >= start]

        if step.get("latest"):
            entries = self._latest(entries, int(step["latest"]))

        if step.get("max"):
            entries = entries[: int(step["max"])]
        return entries

    def _match_usages(self, entries: list[DocumentRef]) -> list[DocumentRef]:
        keyed = [u for u in self.config.usages if u.keyword]
        matched = []
        for entry in entries:
            haystack = self._haystack(entry)
            usages = [u for u in keyed if u.keyword.lower() in haystack]
            if usages:
                entry.usages = usages
                matched.append(entry)
        return matched

    @staticmethod
    def _latest(entries: list[DocumentRef], count: int) -> list[DocumentRef]:
        groups: dict[Optional[tuple], list[DocumentRef]] = {}
        for entry in entries:
            key = tuple(u.keyword for u in entry.usages) if entry.usages else None
            groups.setdefault(key, []).append(entry)

        selected = []
        for group in groups.values():
            group.sort(
                key=lambda e: (e.year or 0, e.extra.get("quarter", 0), -e.extra.get("order", 0)),
                reverse=True,
            )
            selected.extend(group[:count])
        return selected

    @staticmethod
    def _haystack(entry: DocumentRef) -> str:
        return f"{entry.title or ''} {unquote(entry.url)}".lower()
