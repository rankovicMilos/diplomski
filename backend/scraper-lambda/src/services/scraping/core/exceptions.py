"""Exceptions raised by the scraping framework."""
from typing import Optional


class ScraperError(Exception):
    """Base class for all scraping errors."""


class ConfigError(ScraperError):
    """Source configuration is missing or invalid."""


class FetchError(ScraperError):
    """A request failed."""

    def __init__(self, message: str, url: str = "", status_code: Optional[int] = None):
        super().__init__(message)
        self.url = url
        self.status_code = status_code


class NotFoundError(FetchError):
    """The resource does not exist (HTTP 404/410)."""


class BlockedError(FetchError):
    """The site blocked the request (bot protection, e.g. Cloudflare challenge)."""
