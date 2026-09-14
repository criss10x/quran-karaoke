"""equran.id API client: surah text (Arabic + Latin + Indonesian) and murottal audio URLs.

No API key needed. Responses are cached on disk so re-renders never re-download.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

BASE = "https://equran.id/api/v2"
UA = {"User-Agent": "quran-karaoke/0.1 (+https://github.com/criss10x/quran-karaoke)"}
CACHE = os.environ.get("QK_CACHE", os.path.expanduser("~/.cache/quran-karaoke"))

# equran.id murottal catalog.  key -> (url folder, display name)
QARI = {
    "01": ("Abdullah-Al-Juhany", "Abdullah al-Juhany"),
    "02": ("Abdul-Muhsin-Al-Qasim", "Abdul Muhsin al-Qasim"),
    "03": ("Abdurrahman-as-Sudais", "Abdurrahman as-Sudais"),
    "04": ("Ibrahim-Al-Dossari", "Ibrahim al-Dossari"),
    "05": ("Misyari-Rasyid-Al-Afasi", "Mishari Rashid al-Afasy"),
    "06": ("Yasser-Al-Dosari", "Yasser al-Dosari"),
}
DEFAULT_QARI = "03"


def _mkdir(p: str) -> None:
    os.makedirs(p, exist_ok=True)


def _get(url: str, *, binary: bool = False, retries: int = 3) -> bytes:
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"gagal ambil {url}: {last}")


def fetch_surah(nomor: int, *, refresh: bool = False) -> dict:
    """Return equran surah payload (cached): namaLatin, ayat[] with teksArab/teksLatin/teksIndonesia/audio."""
    path = os.path.join(CACHE, f"surah-{nomor:03d}.json")
    if os.path.exists(path) and not refresh:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    raw = _get(f"{BASE}/surat/{nomor}")
    data = json.loads(raw)
    if data.get("code") != 200:
        raise RuntimeError(f"equran.id menolak surah {nomor}: {data.get('message')}")
    payload = data["data"]
    _mkdir(CACHE)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    return payload


def ayah_audio_url(surah: int, ayah: int, qari: str = DEFAULT_QARI) -> str:
    folder = QARI[qari][0]
    return f"https://cdn.equran.id/audio-partial/{folder}/{surah:03d}{ayah:03d}.mp3"


def download_audio(surah: int, ayah: int, qari: str = DEFAULT_QARI, *, refresh: bool = False) -> str:
    """Download one ayah's murottal mp3; returns the cached local path."""
    folder = QARI[qari][0]
    d = os.path.join(CACHE, "audio", folder)
    path = os.path.join(d, f"{surah:03d}{ayah:03d}.mp3")
    if os.path.exists(path) and os.path.getsize(path) > 1000 and not refresh:
        return path
    _mkdir(d)
    blob = _get(ayah_audio_url(surah, ayah, qari))
    tmp = path + ".part"
    with open(tmp, "wb") as f:
        f.write(blob)
    os.replace(tmp, path)
    return path


def verses(payload: dict) -> list[dict]:
    """Normalise the equran ayah list into plain dicts."""
    out = []
    for a in payload["ayat"]:
        out.append(
            {
                "ayah": int(a["nomorAyat"]),
                "arab": a["teksArab"].strip(),
                "latin": (a.get("teksLatin") or "").strip(),
                "arti": (a.get("teksIndonesia") or "").strip(),
            }
        )
    return out
