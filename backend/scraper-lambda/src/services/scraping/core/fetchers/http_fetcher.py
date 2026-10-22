"""Plain HTTP fetcher based on httpx."""
import logging
import time
from typing import Any, Optional

import httpx

from ..exceptions import BlockedError, FetchError, NotFoundError
from ..models import FetchedContent, FetchOptions
from .base import BaseFetcher
from .factory import FetcherFactory

logger = logging.getLogger(__name__)

RETRY_STATUS_CODES = {429, 500, 502, 503, 504}
BOT_CHALLENGE_MARKERS = ("Just a moment...", "cf-chl", "challenge-platform", "Access Denied")


@FetcherFactory.register("http")
class HttpFetcher(BaseFetcher):
    """Fetches with httpx. Retries transient errors and detects bot-protection pages."""

    def __init__(self, options: FetchOptions):
        super().__init__(options)
        self._last_request_at = 0.0
        self.client = httpx.Client(
            verify=options.verify_ssl,
            timeout=options.timeout,
            follow_redirects=True,
            headers={
                "User-Agent": options.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en,sr;q=0.8",
                **options.headers,
            },
        )

    def get(
        self,
        url: str,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        wait_for_selector: Optional[str] = None,
    ) -> FetchedContent:
        attempts = self.options.retries + 1

        for attempt in range(1, attempts + 1):
            is_last_attempt = attempt == attempts
            self._throttle()
            try:
                response = self.client.get(url, params=params, headers=headers)
            except httpx.TransportError as e:
                if is_last_attempt:
                    raise FetchError(f"Request failed: {type(e).__name__}: {e}", url=url) from e
                logger.warning(f"Attempt {attempt}/{attempts} failed for {url}: {type(e).__name__}")
                self._backoff(attempt)
                continue

            retryable = (
                response.status_code in RETRY_STATUS_CODES
                and not self._is_bot_challenge(response)
            )
            if retryable and not is_last_attempt:
                logger.warning(f"Attempt {attempt}/{attempts}: HTTP {response.status_code} for {url}")
                self._backoff(attempt)
                continue

            return self._to_content(url, response)

        raise FetchError("Request failed", url=url)  # unreachable, loop always returns or raises

    def exists(self, url: str) -> bool:
        self._throttle()
        try:
            response = self.client.head(url)
            if response.status_code == 405:
                with self.client.stream("GET", url) as streamed:
                    return streamed.status_code < 400
            return response.status_code < 400
        except httpx.HTTPError:
            return False

    def close(self) -> None:
        self.client.close()

    def _to_content(self, url: str, response: httpx.Response) -> FetchedContent:
        if self._is_bot_challenge(response):
            raise BlockedError(
                f"Blocked by bot protection (HTTP {response.status_code})",
                url=url,
                status_code=response.status_code,
            )
        if response.status_code in (404, 410):
            raise NotFoundError(f"Not found (HTTP {response.status_code})", url=url,
                                status_code=response.status_code)
        if response.status_code >= 400:
            raise FetchError(f"HTTP {response.status_code}", url=url,
                             status_code=response.status_code)
        return FetchedContent(
            url=str(response.url),
            content=response.content,
            content_type=response.headers.get("content-type", "").split(";")[0].strip().lower(),
            status_code=response.status_code,
        )

    @staticmethod
    def _is_bot_challenge(response: httpx.Response) -> bool:
        if response.status_code not in (202, 403, 429, 503):
            return False
        if response.status_code == 202 and not response.content:
            return True
        head = response.text[:5000] if response.content else ""
        return any(marker in head for marker in BOT_CHALLENGE_MARKERS)

    def _throttle(self) -> None:
        wait = self.options.delay_seconds - (time.monotonic() - self._last_request_at)
        if wait > 0:
            time.sleep(wait)
        self._last_request_at = time.monotonic()

    @staticmethod
    def _backoff(attempt: int) -> None:
        time.sleep(min(2 ** attempt, 10))
