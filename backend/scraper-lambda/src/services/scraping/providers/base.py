"""Base classes for providers used by LiveScraper."""
from abc import ABC, abstractmethod
from typing import Any

from ..core.fetchers import BaseFetcher
from ..core.models import LiveSnapshot


class BaseProvider(ABC):
    """A format-specific adapter. Generic scrapers delegate reading the page to it."""

    def __init__(self, fetcher: BaseFetcher, params: dict[str, Any]):
        self.fetcher = fetcher
        self.params = params


class BaseLiveProvider(BaseProvider):
    """Reads current values from a page that changes continuously (prices, rates)."""

    @abstractmethod
    def snapshot(self, url: str) -> LiveSnapshot:
        """Current state of the page."""
