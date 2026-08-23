# book2audio

A simple, non-AI EPUB/PDF text extraction and cleanup pipeline designed for audiobook generation.

## What it does

- EPUB: parses XHTML directly instead of OCR.
- PDF: uses the PDF text layer when available.
- PDF fallback: optional Tesseract OCR with word bounding boxes.
- Detects repeated headers/footers.
- Detects likely page numbers using position, repetition, numeric shape, and sequence.
- Reconstructs paragraphs from PDF blocks/lines.
- Repairs common line-end hyphenation.
- Produces clean TXT plus a JSON diagnostics report.
- No AI calls.

PyMuPDF exposes PDF blocks/words with bounding boxes, which is why the PDF cleaner is layout-aware rather than a regex over one giant string.

## Install

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -e .
```

For OCR support:

```bash
pip install -e ".[ocr]"
```

You also need the Tesseract executable installed on your operating system and available on PATH.

## Usage

EPUB:

```bash
book2audio book.epub -o output
```

PDF:

```bash
book2audio book.pdf -o output
```

Force OCR:

```bash
book2audio scanned.pdf -o output --ocr
```

Specify OCR language:

```bash
book2audio scanned.pdf -o output --ocr --ocr-lang eng
```

Useful tuning:

```bash
book2audio book.pdf -o output \
  --header-footer-min-pages 5 \
  --header-footer-min-frequency 0.45
```

The output directory contains:

- `book.txt` — cleaned text suitable for TTS.
- `report.json` — extraction and cleanup diagnostics.

## Important limitation

This is deliberately conservative. It is intended to remove high-confidence page furniture without deleting legitimate book content. No generic extractor can perfectly understand every publisher's layout. The diagnostics report makes questionable cases visible so thresholds can be tuned.

## Architecture

```text
EPUB ──> XHTML parser ───────────────┐
                                     │
PDF ──> text layer / OCR + geometry ─┤
                                     v
                             document model
                                     |
                             artifact profiling
                                     |
                          paragraph reconstruction
                                     |
                              text normalization
                                     |
                               book.txt + report
                                     |
                                     v
                                    TTS
```
