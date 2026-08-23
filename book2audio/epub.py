from __future__ import annotations

import re
from pathlib import Path

from bs4 import BeautifulSoup
from ebooklib import epub, ITEM_DOCUMENT

from .models import Book, Section
from .utils import clean_prose, looks_like_heading, normalize_space


def extract_epub(path: str | Path) -> Book:
    book = epub.read_epub(str(path))
    title = book.get_metadata("DC", "title")
    title_text = title[0][0] if title else Path(path).stem

    sections: list[Section] = []

    for item in book.get_items_of_type(ITEM_DOCUMENT):
        # EbookLib's document items are XHTML/HTML content.
        soup = BeautifulSoup(item.get_content(), "lxml")

        # Remove elements that should not become spoken prose.
        for tag in soup(["script", "style", "nav", "svg"]):
            tag.decompose()

        # EPUB page-break elements from print editions.
        for el in soup.find_all(attrs={"epub:type": re.compile(r"pagebreak", re.I)}):
            el.decompose()

        for el in soup.find_all(class_=re.compile(r"(?i)(page[-_ ]?break|page[-_ ]?number)")):
            el.decompose()

        body = soup.body or soup

        current_title = None
        paragraphs: list[str] = []

        for el in body.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "blockquote", "li"]):
            text = clean_prose(el.get_text(" ", strip=True))
            if not text:
                continue

            if el.name.startswith("h"):
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

    # Drop completely empty sections.
    sections = [s for s in sections if s.title or s.paragraphs]

    return Book(
        title=title_text,
        sections=sections,
        metadata={
            "format": "epub",
            "source": str(path),
            "document_items": len(list(book.get_items_of_type(ITEM_DOCUMENT))),
        },
    )
