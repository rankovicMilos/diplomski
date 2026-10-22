"""
Convert HTML pages to clean markdown for the knowledge base.

Strips navigation, cookie banners, sidebars and scripts, picks the main content block
and renders headings, paragraphs, lists and tables as markdown.
"""
import re
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urljoin

from bs4 import (
    BeautifulSoup,
    Comment,
    Declaration,
    Doctype,
    NavigableString,
    ProcessingInstruction,
    Tag,
)

# <form> is deliberately kept: ASP.NET / SharePoint sites (e.g. eps.rs) wrap the whole page in one
REMOVE_TAGS = [
    "script", "style", "noscript", "iframe", "svg", "nav", "header", "footer",
    "aside", "button", "select", "input", "textarea", "template", "picture", "video", "audio",
]
SKIPPED_STRINGS = (Comment, Declaration, Doctype, ProcessingInstruction)
NOISE_PATTERN = re.compile(
    r"(cookie|consent|newsletter|subscribe|share|social|related|comment|sidebar|"
    r"breadcrumb|advert|banner|popup|modal|menu|navbar|pagination|promo)",
    re.IGNORECASE,
)
MAIN_CANDIDATES = ["article", "main", "[role=main]", "#content", ".content", ".entry-content",
                   ".post-content", ".article-body"]
BLOCK_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "table", "blockquote",
              "pre", "dl"}
MIN_MAIN_TEXT = 400
# An element whose class looks like noise is only removed if it holds less than this share
# of the main content's text. Themes often wrap the whole page in e.g. "content-sidebar-wrap".
MAX_NOISE_SHARE = 0.5
# While descending to the main block, follow a child that holds at least this share of text.
DOMINANT_CHILD_SHARE = 0.6


@dataclass
class ExtractedPage:
    title: str
    markdown: str
    published: Optional[str] = None
    links: list[tuple[str, str]] = field(default_factory=list)   # (absolute url, link text)
    page_text_chars: int = 0     # visible text on the whole page, to judge extraction quality


def extract_page(html: str, base_url: str, content_selector: Optional[str] = None) -> ExtractedPage:
    soup = BeautifulSoup(html, "lxml")
    title = _title(soup)
    published = _meta(soup, "article:published_time") or _meta(soup, "datePublished")
    links = extract_links(soup, base_url)

    for tag in soup.find_all(REMOVE_TAGS):
        tag.decompose()
    page_text_chars = _text_len(soup.body or soup)

    root = _main_content(soup, content_selector)
    if root is None:
        return ExtractedPage(title, "", published, links, page_text_chars)
    _remove_noise(root)
    return ExtractedPage(title, _render(root), published, links, page_text_chars)


def extract_links(soup_or_html, base_url: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(soup_or_html, "lxml") if isinstance(soup_or_html, str) else soup_or_html
    seen, links = set(), []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "mailto:", "javascript:", "tel:")):
            continue
        url = urljoin(base_url, href)
        if url in seen:
            continue
        seen.add(url)
        links.append((url, _clean(a.get_text(" ", strip=True))))
    return links


def table_to_rows(table: Tag) -> list[list[str]]:
    rows = []
    for tr in table.find_all("tr"):
        cells = [_clean(c.get_text(" ", strip=True)) for c in tr.find_all(["th", "td"])]
        if any(cells):
            rows.append(cells)
    return rows


def rows_to_markdown(rows: list[list[str]], header: Optional[list[str]] = None) -> str:
    if not rows and not header:
        return ""
    if header is None:
        header, rows = rows[0], rows[1:]
    width = max([len(header)] + [len(r) for r in rows])
    header = list(header) + [""] * (width - len(header))
    lines = [
        "| " + " | ".join(_cell(h) for h in header) + " |",
        "|" + "---|" * width,
    ]
    for row in rows:
        row = list(row) + [""] * (width - len(row))
        lines.append("| " + " | ".join(_cell(c) for c in row) + " |")
    return "\n".join(lines)


def _title(soup: BeautifulSoup) -> str:
    og = _meta(soup, "og:title")
    if og:
        return og
    if soup.title and soup.title.string:
        return _clean(soup.title.string)
    h1 = soup.find("h1")
    return _clean(h1.get_text(" ", strip=True)) if h1 else ""


def _meta(soup: BeautifulSoup, name: str) -> Optional[str]:
    tag = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
    return _clean(tag["content"]) if tag and tag.get("content") else None


def _remove_noise(root: Tag) -> None:
    """Remove menus, share buttons, related posts etc. inside the main content."""
    total = _text_len(root) or 1
    for tag in root.find_all(True):
        if tag.decomposed or tag.name in ("article", "main"):
            continue
        attrs = " ".join(tag.get("class", [])) + " " + (tag.get("id") or "")
        if not attrs.strip() or not NOISE_PATTERN.search(attrs):
            continue
        if _text_len(tag) < total * MAX_NOISE_SHARE:
            tag.decompose()


def _main_content(soup: BeautifulSoup, content_selector: Optional[str]) -> Optional[Tag]:
    if content_selector:
        selected = soup.select_one(content_selector)
        if selected:
            return selected
    for selector in MAIN_CANDIDATES:
        candidate = soup.select_one(selector)
        if candidate and _text_len(candidate) >= MIN_MAIN_TEXT:
            return candidate
    return _dominant_block(soup.body) if soup.body else None


def _dominant_block(node: Tag) -> Tag:
    """Descend from <body> while a single child holds most of the text."""
    while True:
        total = _text_len(node)
        children = [c for c in node.find_all(True, recursive=False)]
        if not children or total == 0:
            return node
        best = max(children, key=_text_len)
        if _text_len(best) < total * DOMINANT_CHILD_SHARE:
            return node
        node = best


def _text_len(tag: Tag) -> int:
    return len(tag.get_text(" ", strip=True))


def _render(root: Tag) -> str:
    blocks: list[str] = []
    _render_into(root, blocks)
    deduped, previous = [], None
    for block in blocks:
        if block and block != previous:
            deduped.append(block)
        previous = block
    return "\n\n".join(deduped).strip()


def _render_into(node: Tag, blocks: list[str]) -> None:
    pending_inline: list[str] = []

    def flush() -> None:
        text = _clean(" ".join(pending_inline))
        if text:
            blocks.append(text)
        pending_inline.clear()

    for child in node.children:
        if isinstance(child, SKIPPED_STRINGS):
            continue
        if isinstance(child, NavigableString):
            if child.strip():
                pending_inline.append(str(child))
            continue
        if not isinstance(child, Tag):
            continue
        name = child.name
        if name in BLOCK_TAGS:
            flush()
            rendered = _render_block(child)
            if rendered:
                blocks.append(rendered)
        elif name == "br":
            flush()
        elif child.find(list(BLOCK_TAGS) + ["div", "section"]):
            flush()
            _render_into(child, blocks)
        else:
            pending_inline.append(child.get_text(" ", strip=True))
    flush()


def _render_block(tag: Tag) -> str:
    name = tag.name
    if name in ("h1", "h2", "h3", "h4", "h5", "h6"):
        text = _clean(tag.get_text(" ", strip=True))
        return f"{'#' * int(name[1])} {text}" if text else ""
    if name in ("ul", "ol"):
        items = []
        for i, li in enumerate(tag.find_all("li", recursive=False), start=1):
            text = _clean(li.get_text(" ", strip=True))
            if text:
                items.append(f"{i}. {text}" if name == "ol" else f"- {text}")
        return "\n".join(items)
    if name == "table":
        if tag.find("table"):
            inner: list[str] = []
            _render_into(tag, inner)
            return "\n\n".join(inner)
        return rows_to_markdown(table_to_rows(tag))
    if name == "blockquote":
        text = _clean(tag.get_text(" ", strip=True))
        return f"> {text}" if text else ""
    if name == "pre":
        return f"```\n{tag.get_text()}\n```"
    return _clean(tag.get_text(" ", strip=True))


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _cell(text: str) -> str:
    # A line break inside a cell would end the markdown table row
    return _clean(str(text)).replace("|", "\\|")
