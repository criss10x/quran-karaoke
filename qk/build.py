"""Turn (surah, ayah range, qari) into a renderable timeline: concatenated murottal audio
plus word-level timings and the display text taken from equran.id.

How the timing works
--------------------
The quran-align dataset (see qalign.py) stores, for every ayah of a specific recording, a list
of segments `[word_start_index, word_end_index, start_ms, end_ms]`. Those word indices point
into the mark-stripped Tanzil uthmani word list of the ayah (basmalah prefix removed for the
opening ayah of every surah other than al-Fatihah). A segment is usually a single word, but
madd/waqf groups can span two or three.

So the model here is:

    ayah  ->  segments (timing steps, 10 ms precision)  ->  display lines (what is on screen)

A *line* is what the viewer sees; a *step* inside a line is one segment and is what the karaoke
highlight walks through. Long ayahs are split into several consecutive lines so a line never
overflows the frame, and lines are emitted in time order without overlapping.

Qari without a bundled dataset (01, 02, 04, 06) get "proportional" timing instead: the ayah's
audio duration is divided evenly across its words. That keeps the pipeline usable for every
qari, but only 03 (as-Sudais) and 05 (al-Afasy) give true word-accurate karaoke.
"""
from __future__ import annotations

import dataclasses
import os
import shutil
import subprocess
import tempfile

from . import api, qalign, tanzil

DEFAULT_MAX_CHARS = 44
DEFAULT_MAX_STEPS = 9


class AlignmentError(RuntimeError):
    pass


@dataclasses.dataclass
class Step:
    """One karaoke step: the tokens that light up together."""
    tokens: list[str]
    start: float
    end: float

    @property
    def text(self) -> str:
        return " ".join(self.tokens)


@dataclasses.dataclass
class Line:
    """What is on screen at once (one page of an ayah)."""
    steps: list[Step]
    ayah: int
    latin: str = ""
    arti: str = ""

    @property
    def tokens(self) -> list[str]:
        return [t for s in self.steps for t in s.tokens]

    @property
    def arab(self) -> str:
        return " ".join(self.tokens)

    @property
    def start(self) -> float:
        return self.steps[0].start

    @property
    def end(self) -> float:
        return self.steps[-1].end


@dataclasses.dataclass
class AyahSpan:
    ayah: int
    arab: str
    latin: str
    arti: str
    start: float
    end: float


@dataclasses.dataclass
class Timeline:
    surah: int
    surah_name: str
    surah_arti: str
    qari: str
    qari_name: str
    align: str
    audio: str
    duration: float
    lines: list[Line]
    ayahs: list[AyahSpan]

    @property
    def steps(self) -> list[Step]:
        return [s for ln in self.lines for s in ln.steps]


# --------------------------------------------------------------------------- helpers


def _ffprobe_duration(path: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def _concat_audio(paths: list[str], out: str) -> str:
    """Losslessly concatenate mp3 parts into `out` (stream copy, identical encoder throughout)."""
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        for p in paths:
            f.write(f"file '{os.path.abspath(p)}'\n")
        listing = f.name
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", listing,
             "-c", "copy", out],
            check=True,
        )
    finally:
        os.unlink(listing)
    return out


def _reference_words(surah: int, ayah: int, ref: dict) -> list[str]:
    """The ayah's words in the dataset's own index space (mark tokens and basmalah removed)."""
    raw = ref[(surah, ayah)].split()
    words = [t for t in raw if not tanzil.is_mark(t)]
    if surah != 1 and ayah == 1 and tanzil.is_basmalah(words):
        words = words[4:]
    return words


def _display_tokens(surah: int, ayah: int, eq_arab: str, ref_words: list[str]) -> list[str]:
    """Prefer equran's orthography (richer vowels/waqf marks) when it lines up with the index space."""
    eq = [t for t in eq_arab.split() if not tanzil.is_mark(t)]
    if surah != 1 and ayah == 1 and tanzil.is_basmalah(eq):
        eq = eq[4:]
    return eq if len(eq) == len(ref_words) else ref_words


def _page(steps: list[Step], max_chars: int, max_steps: int) -> list[list[Step]]:
    """Split an ayah's steps into screen-sized pages."""
    pages, cur, chars = [], [], 0
    for st in steps:
        add = len(st.text) + 1
        if cur and (chars + add > max_chars or len(cur) >= max_steps):
            pages.append(cur)
            cur, chars = [], 0
        cur.append(st)
        chars += add
    if cur:
        pages.append(cur)
    return pages


def _split_text(text: str, weights: list[int]) -> list[str]:
    """Split a latin/translation string across pages proportionally to their arabic weight."""
    toks = text.split()
    if len(weights) <= 1 or not toks:
        return [text]
    total = sum(weights) or len(weights)
    out, prev, cum = [], 0, 0
    for i, w in enumerate(weights):
        cum += w
        end = len(toks) if i == len(weights) - 1 else round(len(toks) * cum / total)
        end = max(end, prev)
        out.append(" ".join(toks[prev:end]))
        prev = end
    for i in range(len(out) - 1):                       # never leave an early page empty
        if not out[i] and out[i + 1]:
            bits = out[i + 1].split()
            out[i], out[i + 1] = bits[0], " ".join(bits[1:])
    return out


# --------------------------------------------------------------------------- main


def build(
    surah: int,
    ayah_from: int = 1,
    ayah_to: int | None = None,
    *,
    qari: str = api.DEFAULT_QARI,
    align: str = "auto",
    workdir: str,
    force: bool = False,
    max_chars: int = DEFAULT_MAX_CHARS,
    max_steps: int = DEFAULT_MAX_STEPS,
) -> Timeline:
    """Assemble murottal audio + word timings + equran text for one selection."""
    if qari not in api.QARI:
        raise ValueError(f"qari '{qari}' tidak dikenal (pilih: {', '.join(api.QARI)})")

    payload = api.fetch_surah(surah)
    verses = [v for v in api.verses(payload) if ayah_from <= v["ayah"] <= (ayah_to or 10**6)]
    if not verses:
        raise ValueError(f"tidak ada ayat di rentang {ayah_from}-{ayah_to}")

    resolved = align
    if align == "auto":
        resolved = "qalign" if qalign.has_qari(qari) else "proportional"
    if resolved == "qalign" and not qalign.has_qari(qari):
        raise AlignmentError(
            f"qari {qari} ({api.QARI[qari][1]}) tidak punya data word-timing presisi. "
            "Pakai qari 03 (as-Sudais) atau 05 (al-Afasy), atau --align proportional."
        )

    # 1. murottal audio per ayah, concatenated into one continuous bed
    parts = [api.download_audio(surah, v["ayah"], qari, refresh=force) for v in verses]
    os.makedirs(workdir, exist_ok=True)
    audio = _concat_audio(parts, os.path.join(workdir, "murottal.mp3"))

    spans: list[tuple[dict, float, float]] = []
    cursor = 0.0
    for v, p in zip(verses, parts):
        dur = _ffprobe_duration(p)
        spans.append((v, cursor, cursor + dur))
        cursor += dur
    total = cursor

    ref = tanzil.verses()
    dataset = qalign.QARI_DATASET.get(qari)
    lines: list[Line] = []
    ayahs: list[AyahSpan] = []

    for v, a_start, a_end in spans:
        ayah = v["ayah"]
        ref_words = _reference_words(surah, ayah, ref)
        display = _display_tokens(surah, ayah, v["arab"], ref_words)
        steps: list[Step] = []

        if resolved == "qalign":
            segs = qalign.for_qari(qari).get((surah, ayah))
            if not segs:
                raise AlignmentError(f"tidak ada timing quran-align untuk {surah}:{ayah}")
            for ws, we, s0, e0 in segs:
                ws = max(0, min(ws, len(display)))
                we = max(ws + 1, min(we, len(display)))
                toks = display[ws:we]
                if not toks:
                    continue
                start = max(a_start, a_start + min(s0, e0) / 1000.0)
                end = max(start + 0.05, min(a_start + max(s0, e0) / 1000.0, a_end))
                steps.append(Step(toks, start, end))
            if steps:                                   # hold the last step until the ayah ends
                steps[-1].end = max(steps[-1].end, min(a_end, steps[-1].end + 0.45))
        else:
            words = display or ref_words
            step_s = (a_end - a_start) / max(1, len(words))
            for i, t in enumerate(words):
                steps.append(Step([t], a_start + i * step_s, a_start + (i + 1) * step_s))

        pages = _page(steps, max_chars, max_steps)
        weights = [sum(len(s.text) for s in pg) for pg in pages]
        latins = _split_text(v["latin"].strip(), weights) if v["latin"] else [""] * len(pages)
        artis = _split_text(v["arti"].strip(), weights) if v["arti"] else [""] * len(pages)
        for pg, lc, ac in zip(pages, latins, artis):
            lines.append(Line(steps=pg, ayah=ayah, latin=lc, arti=ac))

        ayahs.append(AyahSpan(ayah, v["arab"], v["latin"], v["arti"], a_start, a_end))

    return Timeline(
        surah=surah,
        surah_name=payload["namaLatin"],
        surah_arti=payload.get("arti", ""),
        qari=qari,
        qari_name=api.QARI[qari][1],
        align=resolved,
        audio=audio,
        duration=total,
        lines=lines,
        ayahs=ayahs,
    )


def cleanup(timeline: Timeline) -> None:
    """Drop the intermediate concatenated bed (cached per-ayah mp3s stay for reuse)."""
    if timeline.audio and os.path.exists(timeline.audio):
        shutil.rmtree(os.path.dirname(timeline.audio), ignore_errors=True)
