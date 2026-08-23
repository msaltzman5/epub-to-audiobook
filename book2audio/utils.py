from __future__ import annotations

import re
import unicodedata


def normalize_space(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    return text.strip()


def is_numeric_token(text: str) -> bool:
    s = re.sub(r"[\s\-\u2010\u2011\u2012\u2013\u2014—–·•.()\[\]]", "", text)
    return bool(s) and s.isdigit()


def numeric_value(text: str) -> int | None:
    s = re.sub(r"[\s\-\u2010\u2011\u2012\u2013\u2014—–·•.()\[\]]", "", text)
    return int(s) if s.isdigit() else None


def normalize_artifact_key(text: str) -> str:
    s = normalize_space(text).lower()
    s = re.sub(r"\d+", "#", s)
    s = re.sub(r"[^a-z0-9#]+", " ", s)
    return normalize_space(s)


def repair_hyphenation(text: str) -> str:
    # Only repair a line-break hyphen, not normal prose hyphens.
    return re.sub(r"(?<=[A-Za-z])-\s*\n\s*(?=[a-z])", "", text)


def clean_prose(text: str) -> str:
    text = normalize_text(text)
    text = repair_hyphenation(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return text.strip()


def looks_like_heading(text: str) -> bool:
    s = normalize_space(text)
    if not s or len(s) > 160:
        return False
    if s.endswith((".", ",", ";", ":", "?", "!")):
        return False
    words = s.split()
    if len(words) <= 12 and (s.isupper() or s.istitle()):
        return True
    return False
