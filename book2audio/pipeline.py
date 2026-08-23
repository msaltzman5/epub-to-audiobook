from __future__ import annotations

import json
from pathlib import Path

from .epub import extract_epub
from .pdf import extract_pdf_text
from .pdf_clean import pdf_to_sections
from .models import Book


def process(
    input_path: str | Path,
    output_dir: str | Path,
    *,
    force_ocr: bool = False,
    ocr_lang: str = "eng",
    min_edge_pages: int = 5,
    min_edge_frequency: float = 0.45,
) -> Book:
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

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
            sections=sections,
            metadata={"format": "pdf", "source": str(input_path)},
            diagnostics=diagnostics,
        )
    else:
        raise ValueError(f"Unsupported input format: {suffix}. Use .pdf or .epub.")

    text = render_text(book)
    (output_dir / "book.txt").write_text(text, encoding="utf-8")

    report = {
        "title": book.title,
        "metadata": book.metadata,
        "diagnostics": book.diagnostics,
        "sections": len(book.sections),
        "paragraphs": sum(len(s.paragraphs) for s in book.sections),
        "characters": len(text),
    }
    (output_dir / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return book


def render_text(book: Book) -> str:
    chunks: list[str] = []

    if book.title:
        chunks.append(book.title)

    for section in book.sections:
        if section.title:
            chunks.append(section.title)
        chunks.extend(section.paragraphs)

    return "\n\n".join(x.strip() for x in chunks if x and x.strip()) + "\n"
