"""
Knowledge Base retrieval for the industry market analysis.

One retrieve call per report section, filtered to the industry's documents via the
`industry` metadata the scraper writes next to every document (<file>.metadata.json).
Chunks tagged for the section (`sections` metadata) are preferred; if none are tagged,
all chunks of the industry that the section query returned are used.
"""
import logging
from typing import Any

from src.services import retrieval_service
from src.services.industry_config import IndustryProfile, SectionPlan


logger = logging.getLogger(__name__)

# Bedrock rejects very long retrieval queries (kept for both backends)
MAX_QUERY_CHARS = 1000
# Retrieve allows at most 100 results per call
MAX_RESULTS = 100


def build_section_query(
    profile: IndustryProfile,
    section: SectionPlan,
    country: str,
    years: list[int],
) -> str:
    """Query text: industry, country, section terms and the YAML topics/sources of the section."""
    parts = [
        f"{profile.display_name} {country}",
        section.template.query_terms,
        *section.subsections,
        *section.topics,
        *section.keywords,
        *section.sources,
        " ".join(str(y) for y in sorted(years)),
    ]
    return "\n".join(p for p in parts if p)[:MAX_QUERY_CHARS]


def section_label(section: SectionPlan) -> str:
    return f"{section.title.upper()} DATA (for the \"{section.id}\" section)"


def retrieve_by_industry_section(
    profile: IndustryProfile,
    country: str,
    years: list[int],
    results_per_section: int,
) -> dict[str, list[dict[str, Any]]]:
    """
    Returns:
        Dict keyed by report section id (e.g. "market_overview") with the chunks for it
    """
    metadata_filter = {"equals": {"key": "industry", "value": profile.industry}}
    num_results = max(1, min(results_per_section, MAX_RESULTS))
    sections: dict[str, list[dict[str, Any]]] = {}

    for section in profile.sections:
        query = build_section_query(profile, section, country, years)
        logger.info(f"Retrieving '{section.id}' chunks for industry '{profile.industry}'...")
        chunks = retrieval_service.retrieve_only(
            query, num_results=num_results, metadata_filter=metadata_filter
        )
        tagged = [c for c in chunks if _tagged_for(c, section)]
        selected = tagged or chunks
        sections[section.id] = _deduplicate(selected, section.id)
        logger.info(
            f"  {len(chunks)} retrieved, {len(tagged)} tagged for the section, "
            f"{len(sections[section.id])} kept"
        )

    return sections


def _tagged_for(chunk: dict[str, Any], section: SectionPlan) -> bool:
    value = (chunk.get("metadata") or {}).get("sections")
    if isinstance(value, list):
        return any(v in section.metadata_sections for v in value)
    if isinstance(value, str):
        return any(s in value for s in section.metadata_sections)
    return False


def _deduplicate(chunks: list[dict[str, Any]], section_id: str) -> list[dict[str, Any]]:
    seen = set()
    unique = []
    for chunk in chunks:
        content_hash = hash(chunk.get("content", "")[:500])
        if content_hash not in seen:
            chunk["section_query"] = section_id
            unique.append(chunk)
            seen.add(content_hash)
    return unique
