from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from .epub import extract_epub
from .pdf import extract_pdf_text
from .pdf_clean import pdf_to_sections
from .models import Book, Chapter
from .utils import safe_filename


def process(
    input_path: str | Path,
    output_dir: str | Path,
    *,
    force_ocr: bool = False,
    ocr_lang: str = "eng",
    min_edge_pages: int = 5,
    min_edge_frequency: float = 0.45,
) -> Book:
    """Extract and clean ``input_path`` (EPUB or PDF).

    Writes ``book.txt``, ``report.json`` and (for multi-chapter books) one
    ``NN - Title.txt`` per chapter into ``output_dir/debug``, then returns the
    parsed :class:`Book`. Audio generation is handled separately by
    :func:`book2audio.tts.synthesize_book` and stays in ``output_dir`` itself.
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    debug_dir = output_dir / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)

    suffix = input_path.suffix.lower()

    if suffix == ".epub":
        book = extract_epub(input_path)
        book.diagnostics.setdefault("format", "epub")
    elif suffix == ".pdf":
        pages = extract_pdf_text(input_path, force_ocr=force_ocr, ocr_lang=ocr_lang)
        sections, diagnostics = pdf_to_sections(
            pages,
            min_edge_pages=min_edge_pages,
            min_edge_frequency=min_edge_frequency,
        )
        book = Book(
            title=input_path.stem,
            chapters=[Chapter(title=None, sections=sections)],
            metadata={"format": "pdf", "source": str(input_path)},
            diagnostics=diagnostics,
        )
    else:
        raise ValueError(f"Unsupported input format: {suffix}. Use .pdf or .epub.")

    text = render_text(book)
    (debug_dir / "book.txt").write_text(text, encoding="utf-8")

    chapter_outputs = list(iter_chapter_outputs(book))
    if len(chapter_outputs) > 1:
        for stem, _title, chapter_text in chapter_outputs:
            (debug_dir / f"{stem}.txt").write_text(chapter_text, encoding="utf-8")

    report = {
        "title": book.title,
        "metadata": book.metadata,
        "diagnostics": book.diagnostics,
        "chapters": [
            {"index": i, "title": title, "characters": len(chapter_text), "file": f"debug/{stem}.txt"}
            for i, (stem, title, chapter_text) in enumerate(chapter_outputs, 1)
        ],
        "sections": len(book.sections),
        "paragraphs": sum(len(s.paragraphs) for s in book.sections),
        "characters": len(text),
    }
    (debug_dir / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return book


def iter_chapter_outputs(book: Book) -> Iterator[tuple[str, str, str]]:
    """Yield ``(file_stem, title, text)`` for each chapter of ``book``."""
    total = len(book.chapters)
    for i, chapter in enumerate(book.chapters, 1):
        title = chapter.title or f"Part {i:02d}"
        stem = "book" if total <= 1 else f"{i:02d} - {safe_filename(title)}"
        yield stem, title, render_chapter(chapter)


def render_chapter(chapter: Chapter) -> str:
    chunks: list[str] = []
    if chapter.title:
        chunks.append(chapter.title)
    for section in chapter.sections:
        if section.title:
            chunks.append(section.title)
        chunks.extend(section.paragraphs)
    return "\n\n".join(x.strip() for x in chunks if x and x.strip()) + "\n"


def render_text(book: Book) -> str:
    parts: list[str] = []
    if book.title:
        parts.append(book.title)
    for chapter in book.chapters:
        parts.append(render_chapter(chapter))
    return "\n\n".join(p.strip() for p in parts if p and p.strip()) + "\n"
