"""Factory that creates a provider from the `provider` param of a source."""
from typing import Any, Callable

from ..core.exceptions import ConfigError
from ..core.fetchers import BaseFetcher


class ProviderFactory:
    """Registry of provider classes keyed by name ("html_table", "meta_description", ...)."""

    _registry: dict[str, type] = {}

    @classmethod
    def register(cls, name: str) -> Callable[[type], type]:
        def decorator(provider_cls: type) -> type:
            cls._registry[name] = provider_cls
            return provider_cls
        return decorator

    @classmethod
    def create(cls, name: str, fetcher: BaseFetcher, params: dict[str, Any], expected: type):
        """Create provider `name`, checking it is the kind the scraper needs."""
        if not name:
            raise ConfigError("Missing params.provider")
        provider_cls = cls._registry.get(name)
        if provider_cls is None:
            raise ConfigError(f"Unknown provider '{name}'. Available: {cls.available()}")
        if not issubclass(provider_cls, expected):
            raise ConfigError(f"Provider '{name}' is not a {expected.__name__}")
        return provider_cls(fetcher, params)

    @classmethod
    def available(cls) -> list[str]:
        return sorted(cls._registry)
