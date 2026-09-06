# book2audio

A simple, non-AI EPUB/PDF text extraction and cleanup pipeline that turns books
into clean text and a spoken audio file.

## What it does

- **EPUB:** parses the XHTML directly (no OCR).
- **PDF:** uses the embedded text layer when present.
- **PDF fallback:** optional Tesseract OCR with word bounding boxes.
- Detects repeated headers/footers and likely page numbers and removes them.
- Reconstructs paragraphs from PDF blocks/lines and repairs line-end hyphenation.
- Writes clean `debug/book.txt` plus a `debug/report.json` diagnostics file.
- Generates `book.wav` (Piper) or `book.mp3` (edge-tts).
- Combines the audio into one chaptered `.m4b` audiobook by default (needs ffmpeg; `--no-m4b` to skip).
- No AI calls.

## Setup

```bash
python -m venv .venv

# activate it:
#   Windows (PowerShell):  .venv\Scripts\Activate.ps1
#   Windows (cmd):         .venv\Scripts\activate.bat
#   macOS/Linux:           source .venv/bin/activate

pip install -r requirements.txt
```

The default Piper voice model (`en_US-kusal-medium.onnx`) is included in this
repo. To use a different one:

```bash
python -m piper.download_voices en_US-lessac-medium
# then pass it with:  --model en_US-lessac-medium.onnx
```

## Usage

```bash
python book2audio.py book.epub -o output
python book2audio.py book.pdf  -o output
```

The output directory gets:

- `<Book Title>.m4b` — one chaptered audiobook combining every chapter (unless
  you pass `--no-m4b`; see "M4B audiobook" below).

A `debug/` subfolder holds the text, diagnostics, and the raw per-chapter audio
that went into the `.m4b`:

- `debug/book.txt` — the whole book as cleaned text.
- `debug/report.json` — extraction and cleanup diagnostics, including the chapter list.
- `debug/NN - Title.txt` — one per chapter, matching the per-chapter audio files.
- One audio file **per chapter** for EPUBs — `debug/01 - Preface.wav`,
  `debug/02 - Introduction.wav`, `debug/03 - Birth of a NERD.wav`, ... (`.mp3`
  with `--tts edge`).
- A single `debug/book.wav` when there is only one chapter (all PDFs), or when
  you pass `--single-file`.

Chapters come from the EPUB's table of contents. Numbered sub-entries (`I`, `II`,
`3.`, ...) are folded into the titled part above them, so a book with parts like
"Birth of a NERD" containing chapters I–VII produces one file for that part, not
eight. PDFs are always one file.

### Common options

| Option | Purpose |
|---|---|
| `-o, --output DIR` | Output directory (default: `./output`). |
| `--tts {piper,edge,none}` | TTS engine. `none` writes text only. Default: `piper`. |
| `--single-file` | One audio file for the whole book instead of one per chapter. |
| `--model PATH` | Piper `.onnx` voice model. Default: `en_US-kusal-medium.onnx`. |
| `--voice NAME` | edge-tts voice (default: `en-US-AndrewNeural`). |
| `--cuda` | Use the GPU for Piper (see "GPU" below). |
| `--no-m4b` | Skip building the combined `.m4b` audiobook (see "M4B audiobook" below). On by default whenever audio is generated. |
| `--ocr` | Force OCR on every PDF page. |
| `--ocr-lang CODE` | Tesseract language (default: `eng`). |
| `--header-footer-min-pages N` | Min distinct pages for a repeated header/footer. |
| `--header-footer-min-frequency F` | Min document frequency for repeated edge text. |

Examples:

```bash
# Text only, no audio (also writes the per-chapter debug/*.txt files)
python book2audio.py book.epub -o output --tts none

# One combined audio file instead of one per chapter
python book2audio.py book.epub -o output --single-file

# edge-tts instead of Piper
python book2audio.py book.epub -o output --tts edge --voice en-US-AriaNeural

# Scanned PDF
python book2audio.py scanned.pdf -o output --ocr --ocr-lang eng

# Tune header/footer removal
python book2audio.py book.pdf -o output \
  --header-footer-min-pages 5 \
  --header-footer-min-frequency 0.45

# Skip the combined .m4b and keep only the per-chapter files
python book2audio.py book.epub -o output --no-m4b
```

## M4B audiobook

Whenever audio is generated, book2audio also combines the per-chapter
`debug/*.wav`/`.mp3` files into a single chaptered `.m4b` (each chapter file
becomes one chapter marker), written to `output/<Book Title>.m4b`. It works
with either TTS engine and with `--single-file` (in which case the `.m4b` has
one chapter). Pass `--no-m4b` to skip it and keep only the per-chapter files
in `debug/`.

If ffmpeg isn't installed, the `.m4b` step is skipped automatically with a
notice — the text and per-chapter audio in `debug/` are unaffected.

Building the `.m4b` shells out to `ffmpeg`/`ffprobe`, which must be on your
`PATH`:

- Windows: `winget install Gyan.FFmpeg`
- Arch: `sudo pacman -S ffmpeg`
- Debian/Ubuntu: `sudo apt install ffmpeg`
- macOS: `brew install ffmpeg`

## OCR (scanned PDFs)

`pytesseract` is installed by `requirements.txt`, but you also need the Tesseract
program itself on your `PATH`:

- Windows: install from https://github.com/UB-Mannheim/tesseract/wiki
- Arch: `sudo pacman -S tesseract tesseract-data-eng`
- Debian/Ubuntu: `sudo apt install tesseract-ocr tesseract-ocr-eng`
- macOS: `brew install tesseract`

## GPU (Piper, optional)

`--cuda` needs an NVIDIA GPU with a CUDA-enabled `onnxruntime`:

```bash
pip uninstall onnxruntime
pip install onnxruntime-gpu
```

The GPU build is version-sensitive to your installed CUDA toolkit; see
https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html#requirements

## Project layout

```
book2audio.py            script you run
book2audio/              the package
  cli.py                 argument parsing, ties the steps together
  pipeline.py            process(): extract -> clean -> write debug/book.txt + chapter files
  epub.py                EPUB XHTML extraction + table-of-contents chapter grouping
  pdf.py                 PDF text-layer / OCR extraction
  artifacts.py           header / footer / page-number detection
  pdf_clean.py           paragraph reconstruction from PDF geometry
  tts.py                 Piper / edge-tts audio output into debug/ (one file per chapter)
  m4b.py                 ffmpeg concat + chapter-metadata muxing into one .m4b
  models.py              dataclasses (Word, TextBlock, Page, Section, Chapter, Book)
  utils.py               text normalization helpers
```

Pipeline:

```text
EPUB ──> XHTML parser ───────────────┐
                                     │
PDF ──> text layer / OCR + geometry ─┤
                                     v
                             document model
                                     │
                             artifact profiling
                                     │
                          paragraph reconstruction
                                     │
                              text normalization
                                     │
                        chapter grouping (EPUB table of contents)
                                     │
                    debug/ : book.txt + report.json + per-chapter .txt
                                     │
                                     v
                     TTS  ->  one .wav / .mp3 per chapter
                                     │
                                     v
                    .m4b (ffmpeg)  ->  one chaptered audiobook (skip with --no-m4b)
```

## Limitations

Header/footer removal is deliberately conservative: it targets high-confidence
page furniture and avoids deleting real content. No generic extractor understands
every publisher's layout perfectly — `report.json` surfaces the questionable
cases so you can tune the thresholds.
