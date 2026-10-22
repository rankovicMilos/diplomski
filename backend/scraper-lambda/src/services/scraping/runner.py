"""
Run config-driven scrapers.

    registry = load_registry()
    results = run_sources(registry.filter(industry="electricity"), storage)

The runner does not know any concrete scraper: ScraperFactory picks the class
from each source's `strategy`.
"""
import logging
import time
from pathlib import Path
from typing import Iterable, Optional

from .core.config_loader import ConfigLoader, SourceRegistry
from .core.exceptions import ScraperError
from .core.models import ScrapeResult, SourceConfig
from .core.storage import BaseStorage
from .scrapers import ScraperFactory

logger = logging.getLogger(__name__)


def load_registry(config_dir: Optional[Path] = None) -> SourceRegistry:
    return ConfigLoader(config_dir).load(known_strategies=ScraperFactory.available())


def run_source(
    config: SourceConfig,
    storage: BaseStorage,
    force: bool = False,
    limit: Optional[int] = None,
) -> ScrapeResult:
    started = time.monotonic()
    try:
        with ScraperFactory.create(config, storage, force=force) as scraper:
            result = scraper.run(limit=limit)
    except ScraperError as e:
        # Raised while building the scraper, e.g. missing Playwright or unknown provider
        result = ScrapeResult(source_id=config.id, status="error")
        result.errors.append(f"{type(e).__name__}: {e}")
    result.duration_seconds = round(time.monotonic() - started, 1)
    return result


def run_sources(
    configs: Iterable[SourceConfig],
    storage: BaseStorage,
    force: bool = False,
    limit: Optional[int] = None,
    run_inactive: bool = False,
) -> list[ScrapeResult]:
    """Run each source. Non-active sources are reported as skipped unless run_inactive is set."""
    results = []
    for config in configs:
        if not config.is_active and not (run_inactive and config.url):
            results.append(ScrapeResult(
                source_id=config.id,
                status="skipped",
                message=f"status={config.status.value}" + (f": {config.notes}" if config.notes else ""),
            ))
            continue
        results.append(run_source(config, storage, force=force, limit=limit))
    return results
