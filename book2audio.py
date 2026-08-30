#!/usr/bin/env python3
"""Command-line entry point for book2audio.

Run it directly, no packaging step required:

    python book2audio.py path/to/book.epub -o output
    python book2audio.py path/to/book.pdf  -o output --tts none

All the real work lives in the ``book2audio/`` package next to this file;
this module just forwards command-line arguments to it.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from book2audio.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
