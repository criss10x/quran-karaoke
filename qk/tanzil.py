"""Tanzil uthmani reference text — word indices of the quran-align dataset point into this text.

Downloaded once from tanzil.net (outType=txt-2 => `surah|ayah|text`). Mark-only tokens
(waqf signs, sajdah marks, standalone vowel signs) are stripped for alignment; the raw
text is kept so callers can decide what to display.
"""
from __future__ import annotations

import os
import re
import unicodedata

from .api import CACHE, _get, _mkdir

URL = (
    "https://tanzil.net/pub/download/index.php"
    "?quranType=uthmani&outType=txt-2&agree=1&accents=1&marks=0&sajdah=1&rub=0&tatweel=0&preface=0"
)
PATH = os.path.join(CACHE, "quran-uthmani-tanzil.txt")

# characters that carry no phonetic word content on their own
COMBINING = (
    set(range(0x0600, 0x0606))
    | set(range(0x0610, 0x061B))
    | {0x061C, 0x0640, 0x0670}
    | set(range(0x064B, 0x0660))
    | set(range(0x06D6, 0x06EE))
    | set(range(0x06F0, 0x06FA))
    | set(range(0x08F0, 0x08FF))
)
_ALEF = "اأإآٱ"
_BASMALAH = ["بسم", "الله", "الرحمن", "الرحيم"]


def norm(token: str) -> str:
    """Reduce an Arabic token to a comparison key (no harakat, no marks, unified alef)."""
    out = []
    for ch in token:
        if ord(ch) in COMBINING or unicodedata.category(ch) == "Mn":
            continue
        out.append(ch)
    s = "".join(out)
    s = re.sub(f"[{_ALEF}]", "ا", s)
    s = s.replace("ى", "ي").replace("ئ", "ي").replace("ؤ", "و")
    s = s.replace("ة", "ه").replace("ء", "").replace("ـ", "")
    s = re.sub(r"[^\u0620-\u064A]", "", s)
    return s.strip()


def is_mark(token: str) -> bool:
    """True if the token holds no letters at all (pure waqf sign / standalone mark)."""
    return norm(token) == ""


def is_basmalah(tokens: list[str]) -> bool:
    return [norm(t) for t in tokens[:4]] == _BASMALAH


def fetch(refresh: bool = False) -> str:
    """Return the path of the cached Tanzil text, downloading it if needed."""
    if os.path.exists(PATH) and os.path.getsize(PATH) > 100_000 and not refresh:
        return PATH
    _mkdir(CACHE)
    blob = _get(URL)
    if b"|" not in blob[:2000]:
        raise RuntimeError("unduhan Tanzil tidak sesuai format (minta persetujuan lisensi?)")
    with open(PATH, "wb") as f:
        f.write(blob)
    return PATH


def verses(refresh: bool = False) -> dict[tuple[int, int], str]:
    """{(surah, ayah): arabic text} for all 6236 ayahs."""
    out: dict[tuple[int, int], str] = {}
    with open(fetch(refresh), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("|", 2)
            if len(parts) != 3 or not parts[0].isdigit():
                continue
            s, a, text = parts
            out[(int(s), int(a))] = text.strip()
    return out
