"""Scraper for a single URL: a direct document (PDF, DOCX, ...) or an article page."""
import re
from typing import Any
from urllib.parse import urlparse

from ..core.file_detector import is_html
from ..core.models import DocumentRef, FetchedContent
from ..core.naming import extract_year, slug_from_url
from ..core.text_extractor import extract_page
from .base import BaseScraper
from .factory import ScraperFactory

DEFAULT_DOC_PATTERN = r"\.(pdf|xlsx?|docx?)($|\?)"


@ScraperFactory.register("single_url")
class SingleUrlScraper(BaseScraper):
    """
    Fetches `url` once. Documents are stored as-is, HTML pages as markdown.

    params:
      year:              edition year for the storage key; default: read from the URL,
                         null: none
      content_selector:  CSS selector of the article body (optional, auto-detected otherwise)
      follow_doc_links:  also download documents linked from the page (optional)
        pattern:         regex matched against the absolute link URL (default: PDF/XLSX/DOCX)
        text_contains:   keep only links whose text or URL contains one of these words
        same_domain:     keep only links on the page's domain (default: false)
        max:             max number of linked documents (default: 5)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache: dict[str, FetchedContent] = {}

    def discover(self) -> list[DocumentRef]:
        url = self.config.url
        # A year in the URL is usually the edition; `year: null` turns this off for URLs
        # where the number means something else (e.g. Eurostat's EU27_2020)
        year = self.params["year"] if "year" in self.params else extract_year(url)
        refs = [DocumentRef(url=url, title=self.config.name, year=year)]

        follow = self.params.get("follow_doc_links")
        if follow:
            page = self.fetcher.get(url)
            self._cache[url] = page
            if is_html(page.content, page.content_type):
                refs.extend(self._linked_documents(page, follow))
        return refs

    def fetch(self, ref: DocumentRef) -> Any:
        return self._cache.pop(ref.url, None) or self.fetcher.get(ref.url)

    def _linked_documents(self, page: FetchedContent, follow: dict) -> list[DocumentRef]:
        pattern = re.compile(follow.get("pattern", DEFAULT_DOC_PATTERN), re.IGNORECASE)
        words = [w.lower() for w in follow.get("text_contains", [])]
        page_domain = urlparse(page.url).netloc
        max_docs = int(follow.get("max", 5))

        refs = []
        for link_url, text in extract_page(page.text, page.url).links:
            if not pattern.search(link_url):
                continue
            if follow.get("same_domain") and urlparse(link_url).netloc != page_domain:
                continue
            if words and not any(w in f"{text} {link_url}".lower() for w in words):
                continue
            refs.append(DocumentRef(
                url=link_url,
                title=text or None,
                # Link text first: URLs often carry the upload date (/2026/02/) instead
                year=extract_year(text, link_url),
                parent_url=page.url,
                extra={"slug": f"linked-{slug_from_url(link_url)}"},
            ))
            if len(refs) >= max_docs:
                break
        return refs
