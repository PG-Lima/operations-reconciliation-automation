"""Text and schedule normalization helpers."""

from __future__ import annotations

import re
import unicodedata


def normalize_text(value: object) -> str:
    """Normalize case, accents, and whitespace without changing display values."""
    text = str(value or "").strip().casefold()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(character for character in text if not unicodedata.combining(character))
    return re.sub(r"\s+", " ", text)


def normalize_company(value: object) -> str:
    """Build a comparison key that ignores accents, punctuation, and repeated spaces."""
    text = normalize_text(value).upper()
    text = re.sub(r"[^A-Z0-9]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_scheduled_days(value: object) -> tuple[int, ...]:
    """Extract distinct calendar days from a reference cell, ignoring values outside 1–31."""
    found = re.findall(r"\d{1,2}", str(value or ""))
    return tuple(sorted({int(item) for item in found if 1 <= int(item) <= 31}))
