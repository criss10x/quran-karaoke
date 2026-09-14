"""quran-align dataset: word-level timings (10 ms resolution) for classic murottal recordings.

Data: github.com/cpfair/quran-align (CC-BY-4.0). Each entry maps (surah, ayah) to a list of
segments [word_start_index, word_end_index, start_msec, end_msec] where the indices point
into the Tanzil uthmani word list (see tanzil.py).

Only two of the bundled recordings are byte-identical to equran.id's CDN — checked by exact
decoded-PCM comparison of the per-ayah files:

    equran "05" (Mishary Rashid al-Afasy)  ==  Alafasy_128kbps
    equran "03" (Abdurrahman as-Sudais)    ==  Abdurrahmaan_As-Sudais_192kbps

Those two get true word-karaoke for free. Every other qari falls back to Whisper alignment.
"""
from __future__ import annotations

import io
import json
import os
import re
import zipfile

from .api import CACHE, _get, _mkdir

RELEASE = "https://github.com/cpfair/quran-align/releases/download/release-2016-11-24/quran-align-data-2016-11-24.zip"
DIR = os.path.join(CACHE, "quran-align")

# equran qari id -> bundled dataset file stem
QARI_DATASET = {
    "05": "Alafasy_128kbps",
    "03": "Abdurrahmaan_As-Sudais_192kbps",
}
DATASET_LABEL = {
    "Alafasy_128kbps": "Mishary Rashid al-Afasy (murattal)",
    "Abdurrahmaan_As-Sudais_192kbps": "Abdurrahman as-Sudais (murattal)",
}

_cache: dict[str, dict[tuple[int, int], list[list[int]]]] = {}


def ensure_data(refresh: bool = False) -> str:
    """Download + unpack the dataset once; returns the directory holding the JSON files."""
    if os.path.isdir(DIR) and os.listdir(DIR) and not refresh:
        return DIR
    _mkdir(DIR)
    blob = _get(RELEASE)
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        for name in z.namelist():
            if name.endswith(".json"):
                with z.open(name) as src, open(os.path.join(DIR, name), "wb") as dst:
                    dst.write(src.read())
    return DIR


def load(dataset: str, refresh: bool = False) -> dict[tuple[int, int], list[list[int]]]:
    """{(surah, ayah): [[w_start, w_end, start_ms, end_ms], ...]}

    Some files in the upstream release carry a stray prefix before the JSON array (the Sudais
    file has ~150 kB of crash-log text prepended, which is why reading it as plain JSON fails).
    The array itself is complete, so parsing starts at the first `[`.
    """
    if dataset in _cache and not refresh:
        return _cache[dataset]
    path = os.path.join(ensure_data(), f"{dataset}.json")
    if not os.path.exists(path):
        raise RuntimeError(f"dataset quran-align tidak ada: {dataset}")
    raw = open(path, encoding="utf-8").read()
    # upstream Sudais file has crash-log text prepended; skip to the first array-of-objects start.
    m = re.search(r'\[\{"(?:ayah|surah)"', raw)
    if not m:
        raise RuntimeError(f"dataset quran-align rusak: {dataset}")
    rows = json.loads(raw[m.start():])
    out = {(r["surah"], r["ayah"]): r["segments"] for r in rows}
    if len(out) < 6000:
        raise RuntimeError(f"dataset quran-align tidak lengkap: {dataset} ({len(out)} ayat)")
    _cache[dataset] = out
    return out


def has_qari(qari: str) -> bool:
    return qari in QARI_DATASET


def for_qari(qari: str, refresh: bool = False) -> dict[tuple[int, int], list[list[int]]]:
    """Word timings for an equran qari id. Raises KeyError if the qari has no dataset."""
    return load(QARI_DATASET[qari], refresh=refresh)


def spans_for_tanzil(dataset: str, tanzil_tokens: list[str], surah: int, ayah: int):
    """Rebuild the dataset's units as (phrase_tokens, start_s, end_s) using Tanzil word indices.

    The dataset stores indices into the *compacted* Tanzil word list (mark-only tokens
    removed, basmalah prefix of a surah-opening ayah dropped).
    """
    segs = load(dataset).get((surah, ayah))
    if segs is None:
        return None
    compact = [t for t in tanzil_tokens if t.strip()]
    if surah != 1 and ayah == 1 and len(compact) > 5:
        from .tanzil import is_basmalah

        if is_basmalah(compact):
            compact = compact[4:]
    out = []
    for ws, we, s0, e0 in segs:
        phrase = compact[ws:we] if we <= len(compact) else compact[ws:]
        out.append((phrase, s0 / 1000.0, e0 / 1000.0))
    return out
