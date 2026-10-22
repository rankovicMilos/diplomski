"""Factory that creates the scraper for a source based on its `strategy`."""
from typing import Callable

from ..core.exceptions import ConfigError
from ..core.fetchers import FetcherFactory
from ..core.models import SourceConfig
from ..core.storage import BaseStorage


class ScraperFactory:
    """
    Registry of scraper classes keyed by strategy name.

    Scrapers register themselves with a decorator:

        @ScraperFactory.register("crawl")
        class CrawlScraper(BaseScraper): ...

    Adding a new strategy only needs a new class; the runner and handler do not change.
    """

    _registry: dict[str, type] = {}

    @classmethod
    def register(cls, strategy: str) -> Callable[[type], type]:
        def decorator(scraper_cls: type) -> type:
            if strategy in cls._registry:
                raise ConfigError(f"Strategy '{strategy}' is already registered")
            cls._registry[strategy] = scraper_cls
            return scraper_cls
        return decorator

    @classmethod
    def create(cls, config: SourceConfig, storage: BaseStorage, force: bool = False):
        if config.strategy not in cls._registry:
            raise ConfigError(
                f"Unknown strategy '{config.strategy}' for source '{config.id}'. "
                f"Available: {cls.available()}"
            )
        fetcher = FetcherFactory.create(config.fetch_mode, config.fetch)
        return cls._registry[config.strategy](config, fetcher, storage, force=force)

    @classmethod
    def available(cls) -> list[str]:
        return sorted(cls._registry)
