"""Turn a Timeline into the ASS subtitle file and the ffmpeg command that burns it in.

Why the Arabic is emitted backwards
----------------------------------
libass lays out the text as a sequence of *runs*, where a run is broken by any override tag
that actually changes something (a ``{\\c...}`` that repeats the style's own colour is a no-op
and gets dropped, which is why this subtlety hid for so long). Runs are then placed
left-to-right in emission order; bidi only reorders the characters *inside* a run.

So for right-to-left Arabic with a per-word colour highlight:

* emitting the words in logical order mirrors the line, and the highlight walks the wrong way;
* emitting each line's words in **reverse** logical order restores the correct right-to-left
  layout, and the highlight then walks right-to-left as it should.

Each word keeps its own ``{\\c}`` tag, so the karaoke highlight is a plain colour swap — no
``\\k`` timing (libass applies ``\\k`` in logical order, unusable on Arabic) and no clip
geometry to measure.

The Indonesian translation underneath is left-to-right text, so it is emitted in logical
order, one colour tag per word, exactly as it reads.
"""
from __future__ import annotations

import os

from . import ass
from .build import Line, Timeline

LAYOUTS = {
    "portrait": (1080, 1920),
    "landscape": (1920, 1080),
    "square": (1080, 1080),
}

FONT_ARABIC = "Amiri Quran"
FONT_LATIN = "Poppins SemiBold"

BASE = "&H00FFFFFF"        # white
ACTIVE = "&H0046C2FE"      # warm gold (ASS is &HAABBGGRR, so this is R=254 G=194 B=70)
ARTI = "&H00E8E8E8"
MIN_SHOW = 0.14            # seconds; keeps very short steps visible

AR_FRAC = 0.150            # arabic size, fraction of the shorter frame side
ARTI_FRAC = 0.074
BREAK_EVERY = 5            # words per screen line; keeps long ayahs off the frame edges


def styles(width: int, height: int, scale: float = 1.0) -> list[ass.Style]:
    unit = min(width, height)
    ar_size = int(unit * AR_FRAC * scale)
    arti_size = int(unit * ARTI_FRAC * scale)
    margin = int(width * 0.055)

    arabic = ass.Style(
        name="Ar", font=FONT_ARABIC, size=ar_size, primary=BASE,
        outline=max(2.0, ar_size * 0.045), shadow=max(1.0, ar_size * 0.02),
        align=5, margin_l=margin, margin_r=margin, margin_v=0, spacing=0.4,
    )
    arti = ass.Style(
        name="Arti", font=FONT_LATIN, size=arti_size, primary=ARTI,
        outline=2.0, shadow=0.8, align=5, margin_l=margin, margin_r=margin, margin_v=0,
    )
    head = ass.Style(
        name="Head", font=FONT_LATIN, size=int(unit * 0.028 * scale), primary=ACTIVE,
        outline=2.0, shadow=0.8, align=8, margin_l=margin, margin_r=margin,
        margin_v=int(height * 0.045),
    )
    return [arabic, arti, head]


def _token_colours(count: int, spans: list[tuple[int, int]], active: int | None,
                   base: str, highlight: str) -> list[str]:
    out = [base] * count
    if active is not None and 0 <= active < len(spans):
        for i in range(*spans[active]):
            if i < count:
                out[i] = highlight
    return out


def _arabic(tokens: list[str], colours: list[str]) -> str:
    """Arabic band: a hard line break every ``BREAK_EVERY`` words, each screen line's words
    emitted in reverse logical order so libass' run placement produces right-to-left text."""
    lines = []
    for c0 in range(0, len(tokens), BREAK_EVERY):
        chunk = list(range(c0, min(c0 + BREAK_EVERY, len(tokens))))
        lines.append(" ".join(f"{{\\c{colours[i]}}}{ass.esc(tokens[i])}" for i in reversed(chunk)))
    return "\\N".join(lines) or ""


def _arti(tokens: list[str], colours: list[str]) -> str:
    """Translation band: ordinary left-to-right text, so logical order and one tag per word."""
    lines = []
    for c0 in range(0, len(tokens), BREAK_EVERY):
        chunk = range(c0, min(c0 + BREAK_EVERY, len(tokens)))
        lines.append(" ".join(f"{{\\c{colours[i]}}}{ass.esc(tokens[i])}" for i in chunk))
    return "\\N".join(lines) or ""


def _emit(doc: ass.Document, line: Line, ar_tokens: list[str], arti_tokens: list[str], *,
          karaoke: bool, clamp_to: tuple[float, float]) -> None:
    """Emit one two-band event per karaoke step (or a single plain event).

    Step boundaries index the Arabic tokens. The translation is highlighted step-by-step only
    when its word count lines up; otherwise it rides along unhighlighted, because guessing an
    alignment would light up the wrong phrase.
    """
    if not ar_tokens:
        return
    lo, hi = clamp_to
    spans, total = [], 0
    for st in line.steps:
        spans.append((total, total + len(st.tokens)))
        total += len(st.tokens)

    arti_spans = spans if (arti_tokens and len(arti_tokens) == total) else None

    def frame(si: int | None) -> str:
        ar = _arabic(ar_tokens, _token_colours(len(ar_tokens), spans, si, BASE, ACTIVE))
        if not arti_tokens:
            return ar
        arti_cols = _token_colours(len(arti_tokens), arti_spans or [], si if arti_spans else None,
                                   ARTI, ACTIVE)
        # the translation sits under the Arabic block; its lines continue from where the
        # Arabic lines ended instead of restarting at the frame centre
        return f"{ar}\\N{{\\rArti}}{_arti(arti_tokens, arti_cols)}"

    if not karaoke or total != len(ar_tokens):
        # plain band, no highlight (also the safety net when a caller's word count differs)
        s, e = max(line.start, lo), min(line.end, hi)
        doc.events.append(ass.Event(s, max(e, s + MIN_SHOW), "Ar", frame(None)))
        return

    for si, step in enumerate(line.steps):
        s = max(step.start, lo)
        e = min(step.end if si < len(line.steps) - 1 else line.end, hi)
        if si < len(line.steps) - 1:                 # keep a step on screen until the next one
            e = min(line.steps[si + 1].start, hi)
        if e < s:
            e = s
        if e - s < MIN_SHOW:
            e = s + MIN_SHOW
        doc.events.append(ass.Event(s, e, "Ar", frame(si)))


def build_document(timeline: Timeline, layout: str = "portrait", *, scale: float = 1.0,
                   karaoke: bool = True, show_arti: bool = True,
                   show_header: bool = True, fonts_dir: str | None = None) -> ass.Document:
    if layout not in LAYOUTS:
        raise ValueError(f"layout '{layout}' tidak dikenal (pilih: {', '.join(LAYOUTS)})")
    width, height = LAYOUTS[layout]
    doc = ass.Document(width=width, height=height, styles=styles(width, height, scale),
                       title=f"Quran {timeline.surah} — {timeline.surah_name}")

    if show_header:
        head = (f"{timeline.surah_name} · {timeline.surah_arti}"
                if timeline.surah_arti else timeline.surah_name)
        doc.events.append(
            ass.Event(0.0, min(timeline.duration, 4.0), "Head",
                      f"{ass.pos(width // 2, int(height * 0.045), 8)}{ass.esc(head)}")
        )

    for line in timeline.lines:
        window = (line.start - 0.25, line.end + 0.25)
        arti = line.arti.split() if show_arti and line.arti else []
        _emit(doc, line, line.tokens, arti, karaoke=karaoke, clamp_to=window)
    return doc


def write_ass(doc: ass.Document, path: str) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc.render())
    return path


def burn_command(video: str, ass_path: str, out: str, *, crf: int = 19, preset: str = "medium",
                 fonts_dir: str | None = None) -> list[str]:
    """ffmpeg command that burns the ASS file into `video` (libass handles RTL shaping)."""
    bad = "".join(ch for ch in ass_path if ch in "\\':[],=")
    if bad:
        raise ValueError(f"path subtitle mengandung karakter yang menyulitkan filter ffmpeg: {bad!r}")
    filt = f"ass={ass_path}"
    if fonts_dir:
        filt += f":fontsdir={fonts_dir}"
    return [
        "ffmpeg", "-y", "-v", "warning", "-stats",
        "-i", video,
        "-vf", filt,
        "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        out,
    ]
