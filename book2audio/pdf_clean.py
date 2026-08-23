from __future__ import annotations

import re

from .artifacts import ArtifactDetector
from .models import Page, Section
from .utils import clean_prose, looks_like_heading, normalize_space


def pdf_to_sections(
    pages: list[Page],
    min_edge_pages: int = 5,
    min_edge_frequency: float = 0.45,
) -> tuple[list[Section], dict]:
    detector = ArtifactDetector(min_edge_pages, min_edge_frequency)
    removed = detector.detect(pages)

    paragraphs: list[str] = []
    headings: list[str] = []

    for page in pages:
        active = [
            (i, b) for i, b in enumerate(page.blocks)
            if (page.number, i) not in removed
        ]
        active.sort(key=lambda pair: (pair[1].y0, pair[1].x0))

        for _, block in active:
            text = clean_prose(block.text)
            if not text:
                continue

            # A block may already contain multiple lines. Normalize line joining.
            lines = [normalize_space(x) for x in text.splitlines() if normalize_space(x)]
            if not lines:
                continue

            joined = _join_lines(lines)

            if looks_like_heading(joined):
                headings.append(joined)
                paragraphs.append(joined)
            else:
                paragraphs.append(joined)

    # Conservative paragraph merging across PDF blocks/pages.
    paragraphs = _merge_paragraphs(paragraphs)

    sections: list[Section] = []
    current = Section(title=None, paragraphs=[])

    for p in paragraphs:
        if looks_like_heading(p) and len(p.split()) <= 12:
            if current.paragraphs:
                sections.append(current)
            current = Section(title=p, paragraphs=[])
        else:
            current.paragraphs.append(p)

    if current.paragraphs or current.title:
        sections.append(current)

    diagnostics = {
        "pages": len(pages),
        "source_types": sorted({p.source for p in pages}),
        "removed_blocks": len(removed),
        "removals": detector.reasons,
    }
    return sections, diagnostics


def _join_lines(lines: list[str]) -> str:
    if len(lines) == 1:
        return lines[0]

    out = lines[0]
    for line in lines[1:]:
        if not out:
            out = line
            continue

        # Join ordinary wrapped lines. Preserve a likely sentence/paragraph break
        # only when the prior line looks complete and the next line looks like
        # a new sentence. This remains intentionally conservative.
        if out.endswith((".", "?", "!", ":", ";", '"', "”", "’")) and line[:1].isupper():
            out += " " + line
        else:
            out += " " + line
    return normalize_space(out)


def _merge_paragraphs(paragraphs: list[str]) -> list[str]:
    if not paragraphs:
        return []

    result = [paragraphs[0]]
    for p in paragraphs[1:]:
        prev = result[-1]

        # Never merge obvious headings.
        if looks_like_heading(p) or looks_like_heading(prev):
            result.append(p)
            continue

        # Don't merge if previous paragraph clearly ends a sentence.
        if prev.endswith((".", "?", "!", "”", '"')):
            result.append(p)
            continue

        # Merge otherwise. This is useful for PDFs whose text blocks split
        # one paragraph across blocks/pages.
        result[-1] = normalize_space(prev + " " + p)

    return result
