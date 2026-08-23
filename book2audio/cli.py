from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import process


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="book2audio",
        description="Convert EPUB/PDF books into cleaned text for TTS.",
    )
    p.add_argument("input", type=Path)
    p.add_argument("-o", "--output", type=Path, default=Path("output"))
    p.add_argument("--ocr", action="store_true", help="Force OCR for PDF pages.")
    p.add_argument("--ocr-lang", default="eng")
    p.add_argument(
        "--header-footer-min-pages",
        type=int,
        default=5,
        help="Minimum distinct pages for a repeated edge artifact.",
    )
    p.add_argument(
        "--header-footer-min-frequency",
        type=float,
        default=0.45,
        help="Minimum document frequency for repeated edge artifacts.",
    )
    return p


def main() -> int:
    args = build_parser().parse_args()

    if not args.input.exists():
        raise SystemExit(f"Input does not exist: {args.input}")

    book = process(
        args.input,
        args.output,
        force_ocr=args.ocr,
        ocr_lang=args.ocr_lang,
        min_edge_pages=args.header_footer_min_pages,
        min_edge_frequency=args.header_footer_min_frequency,
    )

    print(f"Title: {book.title}")
    print(f"Sections: {len(book.sections)}")
    print(f"Output: {args.output / 'book.txt'}")
    print(f"Report: {args.output / 'report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
