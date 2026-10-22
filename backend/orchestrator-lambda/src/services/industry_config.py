"""
Industry profiles for the industry market analysis, read from the scraper's source configs
(backend/scraper-lambda/src/config/sources/<industry>.yaml).

The same YAML drives the scraper and the report, so adding an industry file there gives
both the data and the report outline:
- report sections come from usages[].section of the active sources
- what each section covers comes from usages[].subsection / topic / keyword
- the source names tell the model where the data comes from

Files are read from SOURCES_CONFIG_S3_URI (the folder the scraper reads) and, if that is
not set or the file is missing there, from SOURCES_CONFIG_DIR (by default the scraper's
own config folder, backend/scraper-lambda/src/config/sources).
"""
import logging
import re
from dataclasses import dataclass, field
from typing import Any

import boto3
import yaml
from botocore.exceptions import ClientError

from src.config.settings import AWS_REGION, SOURCES_CONFIG_DIR, SOURCES_CONFIG_S3_URI


logger = logging.getLogger(__name__)

BUNDLED_CONFIG_DIR = SOURCES_CONFIG_DIR
ACTIVE_STATUS = "active"


@dataclass(frozen=True)
class SectionTemplate:
    id: str
    title: str
    focus: str
    query_terms: str


# Report sections in report order, keyed by usages[].section in the source YAML.
# Usages without a section ("general") belong to the market overview.
SECTION_TEMPLATES: dict[str, SectionTemplate] = {
    "market_analysis": SectionTemplate(
        id="market_overview",
        title="Market Overview",
        focus=(
            "market size, production and output, supply and demand, market structure and "
            "year-over-year trends"
        ),
        query_terms="market production output volume supply demand consumption growth trend statistics",
    ),
    "price_analysis": SectionTemplate(
        id="price_analysis",
        title="Price Dynamics",
        focus=(
            "price levels, price changes between periods and their drivers. Report prices with "
            "the currency and unit exactly as in the source (e.g. RSD/l, EUR/t, USD/t) and never "
            "convert currencies"
        ),
        query_terms="price prices cost index change increase decrease per unit EUR USD RSD",
    ),
    "industry_analysis": SectionTemplate(
        id="industry_analysis",
        title="Industry Analysis",
        focus=(
            "industry structure, capacity, investment, key developments, regulation and outlook"
        ),
        query_terms="industry sector capacity investment companies regulation outlook forecast",
    ),
    "market_position": SectionTemplate(
        id="market_position",
        title="Market Players",
        focus="leading companies, their business results and market shares",
        query_terms="company companies revenue results market share leading producers",
    ),
}
SECTION_ALIASES = {"general": "market_analysis"}


@dataclass
class SectionPlan:
    key: str
    template: SectionTemplate
    subsections: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)

    @property
    def id(self) -> str:
        return self.template.id

    @property
    def title(self) -> str:
        return self.template.title

    @property
    def metadata_sections(self) -> set[str]:
        """Values of the documents' `sections` metadata that belong to this section."""
        return {self.key} | {alias for alias, key in SECTION_ALIASES.items() if key == self.key}


@dataclass
class IndustryProfile:
    industry: str
    display_name: str
    sections: list[SectionPlan]
    source_names: list[str]
    config_origin: str


def load_industry_profile(industry: str, config_s3_uri: str | None = None) -> IndustryProfile:
    """
    Build the report outline for an industry from its source YAML.

    Raises:
        ValueError: unknown industry or no active sources
    """
    industry = (industry or "").strip().lower()
    if not re.fullmatch(r"[a-z0-9_]+", industry):
        raise ValueError(f"Invalid industry '{industry}'. Use the YAML file name, e.g. 'livestock'.")

    data, origin = _read_industry_yaml(industry, config_s3_uri or SOURCES_CONFIG_S3_URI)
    industry = data.get("industry") or industry

    plans: dict[str, SectionPlan] = {}
    source_names: list[str] = []
    for source in data.get("sources") or []:
        if source.get("status", ACTIVE_STATUS) != ACTIVE_STATUS:
            continue
        name = source.get("name") or source.get("id")
        used = False
        for usage in source.get("usages") or [{}]:
            if usage.get("industry", industry) != industry:
                continue
            key = SECTION_ALIASES.get(usage.get("section", "general"), usage.get("section"))
            if key not in SECTION_TEMPLATES:
                logger.warning(f"{industry}: source '{source.get('id')}' uses unknown section '{key}'")
                continue
            plan = plans.setdefault(key, SectionPlan(key=key, template=SECTION_TEMPLATES[key]))
            _append_unique(plan.subsections, usage.get("subsection"))
            _append_unique(plan.topics, usage.get("topic"))
            _append_unique(plan.keywords, usage.get("keyword"))
            _append_unique(plan.sources, name)
            used = True
        if used:
            _append_unique(source_names, name)

    if not plans:
        raise ValueError(f"Industry '{industry}' has no active sources in {origin}")

    # The market overview opens every report, even when all sources are tagged otherwise
    plans.setdefault("market_analysis", SectionPlan(key="market_analysis",
                                                    template=SECTION_TEMPLATES["market_analysis"]))
    sections = [plans[key] for key in SECTION_TEMPLATES if key in plans]

    profile = IndustryProfile(
        industry=industry,
        display_name=data.get("name") or _display_name(industry),
        sections=sections,
        source_names=source_names,
        config_origin=origin,
    )
    logger.info(
        f"Industry profile '{industry}' from {origin}: sections={[s.id for s in sections]}, "
        f"sources={len(source_names)}"
    )
    return profile


def available_industries() -> list[str]:
    return sorted(p.stem for p in BUNDLED_CONFIG_DIR.glob("*.yaml") if not p.stem.startswith("_"))


def industry_for_nace(nace_code: str | None) -> tuple[str, str] | None:
    """
    (industry id, display name) whose `nace_codes` cover a client's NACE category.

    Codes match by prefix in either direction, as in the frontend: "D35" and "D35.14" both
    belong to an industry listing "D35.14".
    """
    code = (nace_code or "").strip().split(" ")[0].upper()
    if not code:
        return None
    for industry in available_industries():
        data, _ = _read_industry_yaml(industry, None)
        for industry_code in data.get("nace_codes") or []:
            industry_code = str(industry_code).upper()
            if industry_code.startswith(code) or code.startswith(industry_code):
                return data.get("industry") or industry, data.get("name") or _display_name(industry)
    return None


def _read_industry_yaml(industry: str, config_s3_uri: str | None) -> tuple[dict[str, Any], str]:
    if config_s3_uri:
        bucket, _, prefix = config_s3_uri.removeprefix("s3://").partition("/")
        key = f"{prefix.strip('/')}/{industry}.yaml" if prefix.strip("/") else f"{industry}.yaml"
        try:
            body = boto3.client("s3", region_name=AWS_REGION).get_object(Bucket=bucket, Key=key)["Body"]
            return _parse_yaml(body.read(), key), f"s3://{bucket}/{key}"
        except ClientError as e:
            logger.warning(
                f"Cannot read s3://{bucket}/{key} ({e.response['Error']['Code']}); "
                f"trying the bundled config"
            )

    path = BUNDLED_CONFIG_DIR / f"{industry}.yaml"
    if not path.exists():
        raise ValueError(
            f"Unknown industry '{industry}'. Available: {', '.join(available_industries()) or 'none'}"
        )
    return _parse_yaml(path.read_bytes(), path.name), f"bundled:{path.name}"


def _parse_yaml(content: bytes, name: str) -> dict[str, Any]:
    try:
        return yaml.safe_load(content) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {name}: {e}") from e


def _display_name(industry: str) -> str:
    words = industry.split("_")
    return " ".join(w.upper() if len(w) <= 2 else w.capitalize() for w in words)


def _append_unique(values: list[str], value: str | None) -> None:
    if value and value not in values:
        values.append(value)
