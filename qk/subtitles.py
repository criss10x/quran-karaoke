"""Turn a Timeline into the ASS subtitle file and the ffmpeg command that burns it in.

Golden rule for the Arabic band
------------------------------
The Arabic is emitted as ONE untagged run per screen line, in logical order.

libass splits text into *runs* at every override tag that actually changes something, and
places those runs left-to-right in emission order; bidi only reorders characters *inside* a
run. So a per-word ``{\\c...}`` tag both mirrored the line and broke the letters apart — the
Quran looked wrong. With no tags at all the whole line is a single run, so libass applies
proper bidi and HarfBuzz joining: right-to-left, cursive, exactly like a mushaf.

That is also why the karaoke highlight is gone rather than reworked: any per-word visual
change demands a per-word tag, and a per-word tag is precisely what breaks the script.

The Indonesian translation is left-to-right Latin, so it is emitted plain as well.
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
ACTIVE = "&H0046C2FE"      # warm gold, used by the surah header
ARTI = "&H00E8E8E8"
MIN_SHOW = 0.14            # seconds; keeps a very short line visible

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
        # spacing MUST stay 0.0: any non-zero Spacing makes libass fall back to isolated
        # per-glyph forms and the cursive joins break (measured: 8 ink blocks -> 15).
        align=5, margin_l=margin, margin_r=margin, margin_v=0, spacing=0.0,
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


def _band(tokens: list[str]) -> str:
    """One band of plain text, a hard line break every ``BREAK_EVERY`` words.

    No override tags: a tag per word would split the band into runs and wreck the Arabic.
    """
    lines = []
    for c0 in range(0, len(tokens), BREAK_EVERY):
        lines.append(" ".join(ass.esc(t) for t in tokens[c0:c0 + BREAK_EVERY]))
    return "\\N".join(lines)


def _emit(doc: ass.Document, line: Line, ar_tokens: list[str], arti_tokens: list[str], *,
          clamp_to: tuple[float, float]) -> None:
    """Emit the two bands as one event spanning the whole line."""
    if not ar_tokens:
        return
    lo, hi = clamp_to
    s, e = max(line.start, lo), min(line.end, hi)
    text = _band(ar_tokens)
    if arti_tokens:
        # the translation continues under the Arabic block instead of restarting at centre
        text += f"\\N{{\\rArti}}{_band(arti_tokens)}"
    doc.events.append(ass.Event(s, max(e, s + MIN_SHOW), "Ar", text))


def build_document(timeline: Timeline, layout: str = "portrait", *, scale: float = 1.0,
                   show_arti: bool = True, show_header: bool = True) -> ass.Document:
    if layout not in LAYOUTS:
        raise ValueError(f"layout '{layout}' tidak dikenal (pilih: {', '.join(LAYOUTS)})")
    width, height = LAYOUTS[layout]
    doc = ass.Document(width=width, height=height, styles=styles(width, height, scale),
                       title=f"Quran {timeline.surah} — {timeline.surah_name}")

    if show_header:
        head = (f"{timeline.surah_name} · {timeline.surah_arti}"
                if timeline.surah_arti else timeline.surah_name)
        # placement comes from the Head style (Alignment 8 + MarginV), so no \pos tag
        doc.events.append(
            ass.Event(0.0, min(timeline.duration, 4.0), "Head", ass.esc(head))
        )

    for line in timeline.lines:
        arti = line.arti.split() if show_arti and line.arti else []
        _emit(doc, line, line.tokens, arti, clamp_to=(line.start - 0.25, line.end + 0.25))
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
