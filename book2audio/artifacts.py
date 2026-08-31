from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

from .models import Page, TextBlock
from .utils import (
    is_numeric_token,
    normalize_artifact_key,
    normalize_space,
    numeric_value,
)


class ArtifactDetector:
    def __init__(self, min_pages: int = 5, min_frequency: float = 0.45):
        self.min_pages = min_pages
        self.min_frequency = min_frequency
        self.reasons: list[dict] = []

    def detect(self, pages: list[Page]) -> set[tuple[int, int]]:
        if not pages:
            return set()

        candidates: set[tuple[int, int]] = set()
        candidates |= self._repeated_edge_blocks(pages)
        candidates |= self._numeric_page_numbers(pages)
        return candidates

    def _edge(self, block: TextBlock, page: Page) -> str | None:
        top = block.y0 / max(page.height, 1)
        bottom = (page.height - block.y1) / max(page.height, 1)
        if top <= 0.12:
            return "header"
        if bottom <= 0.12:
            return "footer"
        return None

    def _repeated_edge_blocks(self, pages: list[Page]) -> set[tuple[int, int]]:
        # Normalize text but replace digits so page-number variants can still cluster.
        occurrences: dict[str, list[tuple[int, int]]] = defaultdict(list)
        for page in pages:
            for idx, block in enumerate(page.blocks):
                edge = self._edge(block, page)
                if not edge:
                    continue
                key = f"{edge}|{normalize_artifact_key(block.text)}"
                if not key or key.endswith("|"):
                    continue
                occurrences[key].append((page.number, idx))

        removed: set[tuple[int, int]] = set()
        page_count = len(pages)

        for key, refs in occurrences.items():
            distinct_pages = len({p for p, _ in refs})
            freq = distinct_pages / page_count
            if distinct_pages < self.min_pages or freq < self.min_frequency:
                continue

            for p, idx in refs:
                removed.add((p, idx))
                self.reasons.append({
                    "page": p,
                    "block": idx,
                    "type": "repeated_edge_block",
                    "key": key,
                    "confidence": round(min(0.99, 0.55 + 0.4 * freq), 3),
                })
        return removed

    def _numeric_page_numbers(self, pages: list[Page]) -> set[tuple[int, int]]:
        # Collect isolated numeric candidates in edge zones.
        candidates = []
        for page in pages:
            for idx, block in enumerate(page.blocks):
                edge = self._edge(block, page)
                if not edge:
                    continue

                text = normalize_space(block.text)
                if len(text) > 30:
                    continue

                # Permit common decorative forms: "— 123 —", "Page 123", etc.
                nums = re.findall(r"\d{1,5}", text)
                if not nums:
                    continue

                # A candidate must be mostly numeric or explicitly "page N".
                stripped = re.sub(r"(?i)\bpage\b", "", text)
                stripped = re.sub(r"[\s\-—–_.:·•|()\[\]]+", "", stripped)
                if not stripped.isdigit():
                    continue

                val = int(nums[-1])
                candidates.append((page.number, idx, val, edge))

        if len(candidates) < self.min_pages:
            return set()

        # Look for a mostly sequential sequence across document pages.
        by_page = {p: (idx, val, edge) for p, idx, val, edge in candidates}
        removed: set[tuple[int, int]] = set()

        for page_no, (idx, val, edge) in by_page.items():
            score = 0
            neighbors = 0
            for delta in (-2, -1, 1, 2):
                ref = by_page.get(page_no + delta)
                if ref:
                    neighbors += 1
                    expected = val + delta
                    if ref[1] == expected:
                        score += 1

            # Also accept page number close to physical page index with an offset.
            index_delta = val - page_no
            if neighbors and score >= 1:
                removed.add((page_no, idx))
                self.reasons.append({
                    "page": page_no,
                    "block": idx,
                    "type": "sequential_page_number",
                    "value": val,
                    "confidence": round(min(0.99, 0.72 + 0.08 * score), 3),
                })
            elif abs(index_delta) <= 20 and len(candidates) >= self.min_pages * 2:
                # Weak secondary signal. Require many candidates to avoid deleting
                # legitimate short numeric content.
                removed.add((page_no, idx))
                self.reasons.append({
                    "page": page_no,
                    "block": idx,
                    "type": "page_index_offset",
                    "value": val,
                    "confidence": 0.76,
                })

        return removed
