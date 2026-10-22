"""
Load source definitions from config/sources/*.yaml.

Each file describes one industry:

    industry: electricity
    sources:
      - id: aers-annual-report-2024
        name: "AERS – Godišnji izveštaj 2024"
        url: https://...
        strategy: single_url
        usages:
          - {section: market_analysis, subsection: "Renewable energy"}

`_defaults.yaml` holds settings shared by all sources (fetch options, schedule) and named
presets: a source with `preset: <name>` starts from that preset and overrides what it sets
(nested blocks such as params.csv are merged key by key).
Entries with the same URL, strategy and params are merged into one source with
all usages combined, so a URL cited in several report sections is scraped once.
"""
import logging
from dataclasses import fields
from pathlib import Path
from typing import Any, Iterable, Optional

import yaml

from .exceptions import ConfigError
from .models import FetchOptions, SourceConfig, SourceStatus, Usage

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_DIR = Path(__file__).resolve().parents[3] / "config" / "sources"
DEFAULTS_FILE = "_defaults.yaml"
_FETCH_OPTION_NAMES = {f.name for f in fields(FetchOptions)}


class SourceRegistry:
    """All configured sources, with lookup and filtering."""

    def __init__(self, sources: list[SourceConfig]):
        self._sources = sources
        self._by_id = {s.id: s for s in sources}

    def __iter__(self):
        return iter(self._sources)

    def __len__(self) -> int:
        return len(self._sources)

    def get(self, source_id: str) -> SourceConfig:
        if source_id not in self._by_id:
            raise ConfigError(f"Unknown source_id '{source_id}'")
        return self._by_id[source_id]

    def filter(
        self,
        source_ids: Optional[Iterable[str]] = None,
        industry: Optional[str] = None,
        strategy: Optional[str] = None,
        schedule: Optional[str] = None,
        statuses: Optional[Iterable[SourceStatus]] = (SourceStatus.ACTIVE,),
    ) -> list[SourceConfig]:
        selected = [self.get(i) for i in source_ids] if source_ids else list(self._sources)
        if industry:
            selected = [s for s in selected if industry in s.industries]
        if strategy:
            selected = [s for s in selected if s.strategy == strategy]
        if schedule:
            selected = [s for s in selected if s.schedule == schedule]
        if statuses is not None:
            allowed = set(statuses)
            selected = [s for s in selected if s.status in allowed]
        return selected


class ConfigLoader:
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = Path(config_dir) if config_dir else DEFAULT_CONFIG_DIR

    def load(self, known_strategies: Optional[Iterable[str]] = None) -> SourceRegistry:
        if not self.config_dir.is_dir():
            raise ConfigError(f"Config directory not found: {self.config_dir}")

        defaults = self._read_yaml(self.config_dir / DEFAULTS_FILE) if (
            self.config_dir / DEFAULTS_FILE
        ).exists() else {}

        sources: list[SourceConfig] = []
        for path in sorted(self.config_dir.glob("*.yaml")):
            if path.name == DEFAULTS_FILE:
                continue
            data = self._read_yaml(path)
            industry = data.get("industry") or path.stem
            for raw in data.get("sources") or []:
                sources.append(self._parse_source(raw, industry, defaults, path.name))

        merged = self._merge_duplicates(sources)
        if known_strategies is not None:
            self._validate_strategies(merged, set(known_strategies))
        logger.info(f"Loaded {len(merged)} sources from {self.config_dir}")
        return SourceRegistry(merged)

    @staticmethod
    def _read_yaml(path: Path) -> dict[str, Any]:
        try:
            with path.open(encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in {path.name}: {e}") from e

    def _parse_source(
        self, raw: dict[str, Any], industry: str, defaults: dict[str, Any], file_name: str
    ) -> SourceConfig:
        where = f"{file_name}: source '{raw.get('id', '?')}'"
        if raw.get("preset"):
            presets = defaults.get("presets") or {}
            if raw["preset"] not in presets:
                raise ConfigError(f"{where} uses unknown preset '{raw['preset']}'. "
                                  f"Available: {sorted(presets)}")
            raw = _deep_merge(presets[raw["preset"]], raw)
        for required in ("id", "strategy"):
            if not raw.get(required):
                raise ConfigError(f"{where} is missing '{required}'")

        try:
            status = SourceStatus(raw.get("status", SourceStatus.ACTIVE.value))
        except ValueError as e:
            allowed = [s.value for s in SourceStatus]
            raise ConfigError(f"{where} has invalid status. Allowed: {allowed}") from e

        if status == SourceStatus.ACTIVE and not raw.get("url"):
            raise ConfigError(f"{where} is active but has no 'url'")

        usages = [self._parse_usage(u, industry, where) for u in raw.get("usages") or [{}]]

        fetch_values = {**(defaults.get("fetch") or {}), **(raw.get("fetch") or {})}
        unknown = set(fetch_values) - _FETCH_OPTION_NAMES
        if unknown:
            raise ConfigError(f"{where} has unknown fetch options: {sorted(unknown)}")

        return SourceConfig(
            id=raw["id"],
            name=raw.get("name") or raw["id"],
            strategy=raw["strategy"],
            url=raw.get("url"),
            fetch_mode=raw.get("fetch_mode", defaults.get("fetch_mode", "http")),
            status=status,
            params=raw.get("params") or {},
            fetch=FetchOptions(**fetch_values),
            usages=usages,
            schedule=raw.get("schedule", defaults.get("schedule", "monthly")),
            notes=raw.get("notes"),
            config_file=file_name,
        )

    @staticmethod
    def _parse_usage(raw: dict[str, Any], industry: str, where: str) -> Usage:
        allowed = {"industry", "section", "subsection", "topic", "keyword"}
        unknown = set(raw) - allowed
        if unknown:
            raise ConfigError(f"{where} has unknown usage fields: {sorted(unknown)}")
        return Usage(
            industry=raw.get("industry", industry),
            section=raw.get("section", "general"),
            subsection=raw.get("subsection"),
            topic=raw.get("topic"),
            keyword=raw.get("keyword"),
        )

    @staticmethod
    def _merge_duplicates(sources: list[SourceConfig]) -> list[SourceConfig]:
        by_id: dict[str, SourceConfig] = {}
        by_signature: dict[tuple, SourceConfig] = {}
        result: list[SourceConfig] = []

        for source in sources:
            signature = (
                (source.url or "").rstrip("/"), source.strategy, source.fetch_mode,
                repr(sorted(source.params.items())),
            )
            existing = by_signature.get(signature) if source.url else None
            if existing is not None:
                logger.info(f"Merging '{source.id}' into '{existing.id}' (same URL)")
                existing.usages.extend(u for u in source.usages if u not in existing.usages)
                continue
            if source.id in by_id:
                raise ConfigError(
                    f"Duplicate source id '{source.id}' "
                    f"({by_id[source.id].config_file} and {source.config_file})"
                )
            by_id[source.id] = source
            if source.url:
                by_signature[signature] = source
            result.append(source)
        return result

    @staticmethod
    def _validate_strategies(sources: list[SourceConfig], known: set[str]) -> None:
        for source in sources:
            if source.strategy not in known:
                raise ConfigError(
                    f"{source.config_file}: source '{source.id}' uses unknown strategy "
                    f"'{source.strategy}'. Available: {sorted(known)}"
                )


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Merge override into base; nested dicts are merged, everything else is replaced."""
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged
