from __future__ import annotations

import re
import warnings
from pathlib import Path

from bs4 import BeautifulSoup
from bs4 import XMLParsedAsHTMLWarning
from ebooklib import epub, ITEM_DOCUMENT

from .models import Book, Chapter, Section
from .utils import clean_prose, looks_like_heading, normalize_space

# EbookLib document items are XHTML; we parse them with the lenient lxml HTML
# parser on purpose, so silence its "this looks like XML" advisory.
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# Block-level tags we turn into prose. `div` is included because many EPUBs
# (especially ones converted from print) wrap every paragraph in a <div>
# instead of a <p>.
BLOCK_TAGS = ["h1", "h2", "h3", "h4", "h5", "h6", "p", "blockquote", "li", "div"]

# A table-of-contents label like "I", "IV", "12", or "V: The Beauty of Programming"
# is a numbered sub-chapter that belongs under the preceding titled part rather
# than being its own file.
_SUBCHAPTER_RE = re.compile(r"^\s*(?:[IVXLCDM]+|\d+)\s*(?:[:.\-–—)]|$)", re.IGNORECASE)


def extract_epub(path: str | Path) -> Book:
    book = epub.read_epub(str(path))
    meta_title = book.get_metadata("DC", "title")
    title_text = meta_title[0][0] if meta_title else Path(path).stem

    toc = _flatten_toc(getattr(book, "toc", []) or [])
    chapters = _group_chapters(_spine_documents(book), toc)
    chapters = [c for c in chapters if c.paragraphs]

    # No usable table of contents: fall back to one chapter per spine document.
    if not chapters:
        chapters = [
            c
            for item in _spine_documents(book)
            for c in [Chapter(title=None, sections=_sections_from_html(item.get_content()))]
            if c.paragraphs
        ]

    return Book(
        title=title_text,
        chapters=chapters,
        metadata={
            "format": "epub",
            "source": str(path),
            "document_items": len(_spine_documents(book)),
            "chapters": len(chapters),
        },
    )


def _spine_documents(book: epub.EpubBook) -> list:
    """Document items in reading (spine) order, with a manifest-order fallback."""
    docs = []
    for idref, _linear in getattr(book, "spine", []) or []:
        item = book.get_item_with_id(idref)
        if item is not None and item.get_type() == ITEM_DOCUMENT:
            docs.append(item)
    if not docs:
        docs = list(book.get_items_of_type(ITEM_DOCUMENT))
    return docs


def _flatten_toc(entries) -> list[tuple[str, str]]:
    """Flatten book.toc into an ordered [(title, target_filename), ...] list."""
    out: list[tuple[str, str]] = []

    def walk(node) -> None:
        for entry in node:
            if isinstance(entry, (list, tuple)):
                # (Section, [children]) or a plain nested list.
                if len(entry) == 2 and not isinstance(entry[0], (list, tuple)):
                    section, children = entry
                    href = getattr(section, "href", None)
                    if href:
                        out.append((getattr(section, "title", "") or "", href))
                    walk(children)
                else:
                    walk(entry)
            else:
                href = getattr(entry, "href", None)
                if href:
                    out.append((getattr(entry, "title", "") or "", href))

    walk(entries)
    return [(title, href.split("#")[0].rsplit("/", 1)[-1]) for title, href in out]


def _group_chapters(items: list, toc: list[tuple[str, str]]) -> list[Chapter]:
    title_for: dict[str, str] = {}
    for title, name in toc:
        title_for.setdefault(name, title)

    chapters: list[Chapter] = []
    current: Chapter | None = None
    current_is_part = False  # current chapter was opened by a titled (non-numbered) entry

    for item in items:
        name = item.get_name().rsplit("/", 1)[-1]
        toc_title = title_for.get(name)
        sections = _sections_from_html(item.get_content())

        if toc_title is not None:
            is_sub = bool(_SUBCHAPTER_RE.match(toc_title))
            if is_sub and current is not None and current_is_part:
                current.sections.extend(sections)
                continue
            current = Chapter(title=_clean_title(toc_title), sections=list(sections))
            current_is_part = not is_sub
            chapters.append(current)
        elif current is not None:
            current.sections.extend(sections)
        else:
            current = Chapter(title="Front Matter", sections=list(sections))
            current_is_part = False
            chapters.append(current)

    return chapters


def _clean_title(title: str) -> str | None:
    title = re.sub(r"\[\d+\]", "", title or "")  # drop footnote refs like "[1]"
    title = normalize_space(title)
    return title or None


def _sections_from_html(content: bytes) -> list[Section]:
    soup = BeautifulSoup(content, "lxml")

    for tag in soup(["script", "style", "nav", "svg"]):
        tag.decompose()
    for el in soup.find_all(attrs={"epub:type": re.compile(r"pagebreak", re.I)}):
        el.decompose()
    for el in soup.find_all(class_=re.compile(r"(?i)(page[-_ ]?break|page[-_ ]?number)")):
        el.decompose()

    body = soup.body or soup

    sections: list[Section] = []
    current_title: str | None = None
    paragraphs: list[str] = []

    for el in body.find_all(BLOCK_TAGS):
        # A wrapper <div> holding other block elements would double-count its
        # text; only take a <div> that directly contains the prose.
        if el.name == "div" and el.find(BLOCK_TAGS):
            continue

        text = clean_prose(el.get_text(" ", strip=True))
        if not text:
            continue

        is_heading = el.name.startswith("h") or (
            el.name == "div" and looks_like_heading(text)
        )

        if is_heading:
            if paragraphs or current_title:
                sections.append(Section(current_title, paragraphs))
            current_title = text
            paragraphs = []
        elif el.name == "li":
            paragraphs.append(" ".join(["•", normalize_space(text)]))
        else:
            paragraphs.append(normalize_space(text))

    if paragraphs or current_title:
        sections.append(Section(current_title, paragraphs))

    return [s for s in sections if s.title or s.paragraphs]
