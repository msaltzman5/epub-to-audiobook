from __future__ import annotations

import re
from pathlib import Path

import fitz

from .models import Page, TextBlock, Word
from .utils import normalize_text


def _words_from_block(block, block_id: int) -> list[Word]:
    # PyMuPDF block tuples contain x0,y0,x1,y1,text,block_no,block_type.
    text = block[4] if len(block) > 4 else ""
    return [
        Word(
            text=line.strip(),
            x0=block[0],
            y0=block[1],
            x1=block[2],
            y1=block[3],
            block_id=block_id,
            line_id=i,
            word_id=i,
        )
        for i, line in enumerate(text.splitlines())
        if line.strip()
    ]


def extract_pdf_text(path: str | Path, force_ocr: bool = False, ocr_lang: str = "eng") -> list[Page]:
    path = Path(path)
    doc = fitz.open(path)

    pages: list[Page] = []
    for page_no, page in enumerate(doc, start=1):
        rect = page.rect
        blocks = page.get_text("blocks", sort=True)

        text_chars = sum(len(str(b[4]).strip()) for b in blocks if len(b) >= 7 and b[6] == 0)

        if force_ocr or text_chars < 40:
            page_model = _ocr_page(page, page_no, ocr_lang)
        else:
            page_model = _page_from_blocks(page_no, rect.width, rect.height, blocks)

        pages.append(page_model)

    doc.close()
    return pages


def _page_from_blocks(page_no, width, height, blocks) -> Page:
    result = Page(page_no, width, height, source="pdf")
    for i, b in enumerate(blocks):
        if len(b) < 7 or b[6] != 0:
            continue
        text = normalize_text(str(b[4]))
        if not text:
            continue
        result.blocks.append(
            TextBlock(
                text=text,
                x0=float(b[0]),
                y0=float(b[1]),
                x1=float(b[2]),
                y1=float(b[3]),
                block_id=i,
            )
        )
    return result


def _ocr_page(page, page_no: int, lang: str) -> Page:
    try:
        import pytesseract
    except ImportError as exc:
        raise RuntimeError(
            "OCR was required but pytesseract is not installed. "
            "Install with: pip install -e '.[ocr]'"
        ) from exc

    from PIL import Image

    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)

    sx = page.rect.width / pix.width
    sy = page.rect.height / pix.height

    # Group OCR words by (block, paragraph, line).
    groups: dict[tuple[int, int, int], list[Word]] = {}
    n = len(data["text"])
    for i in range(n):
        text = data["text"][i].strip()
        conf_raw = data["conf"][i]
        try:
            conf = float(conf_raw)
        except (TypeError, ValueError):
            conf = None
        if not text or (conf is not None and conf < 0):
            continue

        x = float(data["left"][i]) * sx
        y = float(data["top"][i]) * sy
        w = float(data["width"][i]) * sx
        h = float(data["height"][i]) * sy
        key = (
            int(data["block_num"][i]),
            int(data["par_num"][i]),
            int(data["line_num"][i]),
        )
        groups.setdefault(key, []).append(
            Word(text, x, y, x + w, y + h, confidence=conf)
        )

    result = Page(page_no, page.rect.width, page.rect.height, source="ocr")
    for block_id, words in enumerate(groups.values()):
        if not words:
            continue
        words.sort(key=lambda w: w.x0)
        text = " ".join(w.text for w in words)
        result.blocks.append(
            TextBlock(
                text=text,
                x0=min(w.x0 for w in words),
                y0=min(w.y0 for w in words),
                x1=max(w.x1 for w in words),
                y1=max(w.y1 for w in words),
                block_id=block_id,
                words=words,
            )
        )
    result.blocks.sort(key=lambda b: (b.y0, b.x0))
    return result
