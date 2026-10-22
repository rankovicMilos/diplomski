"""
Config-driven scrapers. Importing this package registers every strategy with ScraperFactory.

| strategy     | class              | use for                                                   |
|--------------|--------------------|-----------------------------------------------------------|
| single_url   | SingleUrlScraper   | direct documents and data exports (PDF, CSV), articles    |
| crawl        | CrawlScraper       | document listing pages and multi-level navigation         |
| live         | LiveScraper        | pages with changing prices (snapshots + history)          |
"""
from .base import BaseScraper
from .crawl import CrawlScraper
from .factory import ScraperFactory
from .live import LiveScraper
from .single_url import SingleUrlScraper

__all__ = [
    "BaseScraper",
    "CrawlScraper",
    "LiveScraper",
    "ScraperFactory",
    "SingleUrlScraper",
]
