from __future__ import annotations

import argparse
from pathlib import Path

from .m4b import combine_to_m4b
from .pipeline import iter_chapter_outputs, process, render_text
from .tts import DEFAULT_EDGE_VOICE, synthesize_book
from .utils import safe_filename


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="book2audio",
        description="Convert EPUB/PDF books into cleaned text and audio for TTS.",
    )
    p.add_argument("input", type=Path, help="Path to a .epub or .pdf file.")
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output"),
        help="Output directory (default: ./output).",
    )

    ocr = p.add_argument_group("OCR (scanned PDFs)")
    ocr.add_argument("--ocr", action="store_true", help="Force OCR for every PDF page.")
    ocr.add_argument("--ocr-lang", default="eng", help="Tesseract language code (default: eng).")

    tuning = p.add_argument_group("header/footer detection")
    tuning.add_argument(
        "--header-footer-min-pages",
        type=int,
        default=5,
        help="Minimum distinct pages for a repeated edge artifact.",
    )
    tuning.add_argument(
        "--header-footer-min-frequency",
        type=float,
        default=0.45,
        help="Minimum document frequency for repeated edge artifacts.",
    )

    tts = p.add_argument_group("text-to-speech")
    tts.add_argument(
        "--tts",
        choices=["piper", "edge", "none"],
        default="piper",
        help="TTS engine (default: piper). Use 'none' to write text only.",
    )
    tts.add_argument(
        "--single-file",
        action="store_true",
        help="Write one audio file for the whole book instead of one per chapter.",
    )
    tts.add_argument(
        "--model",
        type=Path,
        default=None,
        help="Piper .onnx voice model (default: en_US-kusal-medium.onnx in the project root).",
    )
    tts.add_argument(
        "--voice",
        default=None,
        help=f"edge-tts voice name (default: {DEFAULT_EDGE_VOICE}).",
    )
    tts.add_argument(
        "--cuda",
        action="store_true",
        help="Use CUDA GPU acceleration for Piper.",
    )
    tts.add_argument(
        "--m4b",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Also combine the generated audio into one chaptered .m4b audiobook "
        "(requires ffmpeg). On by default unless --tts none; use --no-m4b to skip.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

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

    print(f"Title:    {book.title}")
    print(f"Chapters: {len(book.chapters)}")
    print(f"Text:     {args.output / 'debug' / 'book.txt'}")
    print(f"Report:   {args.output / 'debug' / 'report.json'}")

    chapter_outputs = list(iter_chapter_outputs(book))
    if args.single_file or len(chapter_outputs) <= 1:
        labeled_jobs = [("book", book.title or args.input.stem, render_text(book))]
    else:
        labeled_jobs = chapter_outputs
    # synthesize_book drops blank-text jobs; filter here too so titles stay
    # aligned with the audio paths it actually returns.
    labeled_jobs = [(stem, title, text) for stem, title, text in labeled_jobs if text.strip()]

    paths = synthesize_book(
        [(stem, text) for stem, _title, text in labeled_jobs],
        args.output,
        engine=args.tts,
        model=args.model,
        voice=args.voice,
        use_cuda=args.cuda,
    )
    for path in paths:
        print(f"Audio:    {path}")

    build_m4b = args.m4b if args.m4b is not None else args.tts != "none"
    if build_m4b:
        if not paths:
            raise SystemExit("--m4b requires audio output; pass --tts piper or --tts edge.")
        titles = [title for _stem, title, _text in labeled_jobs]
        m4b_path = args.output / f"{safe_filename(book.title or args.input.stem)}.m4b"
        combine_to_m4b(paths, titles, m4b_path)
        print(f"M4B:      {m4b_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
