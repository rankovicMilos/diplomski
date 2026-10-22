"""
Headless browser fetcher for JavaScript-rendered pages (e.g. pks.rs, stat.gov.rs/oblasti).

Requires the optional dependency group:
    uv sync --extra browser
    uv run playwright install chromium
"""
import logging
from typing import Any, Optional
from urllib.parse import urlencode

from ..exceptions import BlockedError, FetchError, NotFoundError
from ..models import FetchedContent, FetchOptions
from .base import BaseFetcher
from .factory import FetcherFactory
from .http_fetcher import BOT_CHALLENGE_MARKERS, HttpFetcher

logger = logging.getLogger(__name__)


@FetcherFactory.register("browser")
class BrowserFetcher(BaseFetcher):
    """
    Renders HTML pages in headless Chromium.

    Only HTML pages go through the browser. Documents found on those pages (PDF, XLSX)
    are downloaded with a plain HttpFetcher, which is faster and returns the raw bytes.
    """

    def __init__(self, options: FetchOptions):
        super().__init__(options)
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as e:
            raise FetchError(
                "fetch_mode 'browser' requires Playwright: "
                "`uv sync --extra browser` and `uv run playwright install chromium`"
            ) from e

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)
        self._context = self._browser.new_context(
            user_agent=options.user_agent,
            ignore_https_errors=not options.verify_ssl,
            locale="sr-RS",
        )
        self._http = HttpFetcher(options)

    def get(
        self,
        url: str,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        wait_for_selector: Optional[str] = None,
    ) -> FetchedContent:
        wait_for_selector = wait_for_selector or self.options.wait_for_selector
        if params:
            url = f"{url}{'&' if '?' in url else '?'}{urlencode(params, doseq=True)}"
        if self._looks_like_document(url):
            return self._http.get(url, headers=headers)

        page = self._context.new_page()
        try:
            response = page.goto(
                url,
                wait_until=self.options.wait_until,
                timeout=self.options.timeout * 1000,
            )
            if wait_for_selector:
                page.wait_for_selector(wait_for_selector, timeout=self.options.timeout * 1000)
            status = response.status if response else 200
            html = page.content()
            final_url = page.url   # after redirects; read before the page is closed
        except Exception as e:
            raise FetchError(f"Browser navigation failed: {type(e).__name__}: {e}", url=url) from e
        finally:
            page.close()

        if any(marker in html[:5000] for marker in BOT_CHALLENGE_MARKERS):
            raise BlockedError("Blocked by bot protection (browser)", url=url, status_code=status)
        if status in (404, 410):
            raise NotFoundError(f"Not found (HTTP {status})", url=url, status_code=status)
        if status >= 400:
            raise FetchError(f"HTTP {status}", url=url, status_code=status)

        return FetchedContent(
            url=final_url,
            content=html.encode("utf-8"),
            content_type="text/html",
            status_code=status,
        )

    def exists(self, url: str) -> bool:
        return self._http.exists(url)

    def close(self) -> None:
        self._http.close()
        self._context.close()
        self._browser.close()
        self._playwright.stop()

    @staticmethod
    def _looks_like_document(url: str) -> bool:
        path = url.lower().split("?")[0]
        return path.endswith((".pdf", ".xlsx", ".xls", ".docx", ".doc", ".csv", ".zip"))
