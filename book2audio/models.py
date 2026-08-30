from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Word:
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    block_id: int = -1
    line_id: int = -1
    word_id: int = -1
    confidence: float | None = None

    @property
    def center_x(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def center_y(self) -> float:
        return (self.y0 + self.y1) / 2


@dataclass
class TextBlock:
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    block_id: int
    words: list[Word] = field(default_factory=list)

    @property
    def width(self) -> float:
        return max(0.0, self.x1 - self.x0)

    @property
    def height(self) -> float:
        return max(0.0, self.y1 - self.y0)

    @property
    def center_x(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def center_y(self) -> float:
        return (self.y0 + self.y1) / 2


@dataclass
class Page:
    number: int
    width: float
    height: float
    blocks: list[TextBlock] = field(default_factory=list)
    source: str = "pdf"


@dataclass
class Section:
    title: str | None
    paragraphs: list[str] = field(default_factory=list)


@dataclass
class Chapter:
    """A logical division of a book (preface, introduction, a chapter, ...).

    Each chapter becomes one audio file. For EPUBs it maps to a table-of-contents
    entry; for PDFs the whole book is a single chapter.
    """

    title: str | None
    sections: list[Section] = field(default_factory=list)

    @property
    def paragraphs(self) -> list[str]:
        out: list[str] = []
        for s in self.sections:
            out.extend(s.paragraphs)
        return out


@dataclass
class Book:
    title: str | None
    chapters: list[Chapter] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)

    @property
    def sections(self) -> list[Section]:
        out: list[Section] = []
        for c in self.chapters:
            out.extend(c.sections)
        return out
