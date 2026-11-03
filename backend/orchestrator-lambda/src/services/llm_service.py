"""
Claude service for report generation via the Anthropic API.

Every call streams (long JSON reports plus thinking would otherwise risk HTTP timeouts)
and returns {"output": {"text": ...}}, the shape the handlers and parsers expect.
"""
import logging
from functools import cache
from typing import Any

import anthropic

from src.config.settings import CLAUDE_EFFORT, CLAUDE_MAX_TOKENS, CLAUDE_MODEL


logger = logging.getLogger(__name__)


@cache
def _client() -> anthropic.Anthropic:
    """Created on first use, so read-only API routes work without ANTHROPIC_API_KEY."""
    return anthropic.Anthropic()

# On a safety decline the API re-runs the request on Anthropic's recommended fallback model
_FALLBACK_BETA = "server-side-fallback-2026-07-01"


class GenerationRefused(RuntimeError):
    """The model (and its fallback) declined the request."""


def _generate(content: list[dict[str, Any]], system_prompt: str) -> dict[str, Any]:
    """Run one streamed request and return the answer text in the handlers' shape."""
    with _client().beta.messages.stream(
        model=CLAUDE_MODEL,
        max_tokens=CLAUDE_MAX_TOKENS,
        system=system_prompt,
        messages=[{"role": "user", "content": content}],
        output_config={"effort": CLAUDE_EFFORT},
        betas=[_FALLBACK_BETA],
        fallbacks="default",
    ) as stream:
        message = stream.get_final_message()

    usage = message.usage
    logger.info(
        f"Claude {message.model}: stop_reason={message.stop_reason}, "
        f"input_tokens={usage.input_tokens}, output_tokens={usage.output_tokens}"
    )

    if message.stop_reason == "refusal":
        details = getattr(message, "stop_details", None)
        raise GenerationRefused(f"Claude declined the request: {details}")
    if message.stop_reason == "max_tokens":
        logger.warning(f"Output hit max_tokens={CLAUDE_MAX_TOKENS}; the JSON is probably cut off")

    # Thinking blocks come before the answer; only the text blocks are the report
    output_text = "".join(block.text for block in message.content if block.type == "text")
    return {"output": {"text": output_text}}


def generate_only(context: str, system_prompt: str) -> dict[str, Any]:
    """
    Generate without retrieval, for analyses whose context is pre-fetched from storage.

    Args:
        context: The context text (with delimited sections)
        system_prompt: The system prompt for the model

    Returns:
        Response dict with output.text field
    """
    return _generate([{"type": "text", "text": context}], system_prompt)


def generate_with_section_context(
    section_chunks: dict[str, list[dict]],
    system_prompt: str,
    user_query: str,
    section_labels: dict[str, str] | None = None
) -> dict[str, Any]:
    """
    Generate with retrieved chunks organized by report section.

    Formats chunks by section (production, price, geopolitical) for clearer
    context organization, helping the model use the right data for each
    report section.

    Args:
        section_chunks: Dict mapping section names to chunk lists
            e.g., {"production": [...], "price": [...], "geopolitical": [...]}
        system_prompt: The system prompt for the model
        user_query: The user's query/request
        section_labels: Optional headers per section name (overrides the crop defaults)

    Returns:
        Response dict with output.text field
    """
    section_labels = {
        "production": "PRODUCTION & DOMESTIC MARKET DATA (for Market Overview section)",
        "price": "PRICE DATA (for Price Analysis section)",
        "geopolitical": "WORLD MARKET & GEOPOLITICAL DATA (for Geopolitical Analysis section)",
        **(section_labels or {}),
    }

    context_parts = []

    for section_name, chunks in section_chunks.items():
        if not chunks:
            continue

        label = section_labels.get(section_name, section_name.upper())
        context_parts.append(f"=== {label} ===\n")

        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("location", "unknown")
            content = chunk.get("content", "")
            context_parts.append(f"[{section_name.upper()} Source {i}: {source}]\n{content}\n")

        context_parts.append("\n")

    context_str = "\n".join(context_parts)

    # Build the user message with organized context
    user_message = f"RETRIEVED CONTEXT (organized by report section)\n\n{context_str}\n\nUSER REQUEST\n\n{user_query}"

    logger.info(f"Generating with section context - total context length: {len(context_str)} chars")

    response = _generate([{"type": "text", "text": user_message}], system_prompt)
    response["citations"] = []  # Citations not available in this flow
    return response
