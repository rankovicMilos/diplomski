"""Factory that creates a fetcher from a source's `fetch_mode`."""
from typing import Callable

from ..exceptions import ConfigError
from ..models import FetchOptions


class FetcherFactory:
    """Registry of fetcher classes keyed by fetch mode ("http", "browser", ...)."""

    _registry: dict[str, type] = {}

    @classmethod
    def register(cls, mode: str) -> Callable[[type], type]:
        def decorator(fetcher_cls: type) -> type:
            cls._registry[mode] = fetcher_cls
            return fetcher_cls
        return decorator

    @classmethod
    def create(cls, mode: str, options: FetchOptions):
        if mode not in cls._registry:
            raise ConfigError(f"Unknown fetch_mode '{mode}'. Available: {cls.available()}")
        return cls._registry[mode](options)

    @classmethod
    def available(cls) -> list[str]:
        return sorted(cls._registry)
