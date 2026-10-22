"""Factory that creates a storage backend by name."""
from typing import Any, Callable

from ..exceptions import ConfigError


class StorageFactory:
    """Registry of storage classes keyed by name ("s3", "local", ...)."""

    _registry: dict[str, type] = {}

    @classmethod
    def register(cls, name: str) -> Callable[[type], type]:
        def decorator(storage_cls: type) -> type:
            cls._registry[name] = storage_cls
            return storage_cls
        return decorator

    @classmethod
    def create(cls, name: str, **kwargs: Any):
        if name not in cls._registry:
            raise ConfigError(f"Unknown storage '{name}'. Available: {sorted(cls._registry)}")
        return cls._registry[name](**kwargs)
