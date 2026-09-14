"""Turn a Timeline into the ASS subtitle file and the ffmpeg command that burns it in.

Styling notes
-------------
* The Arabic line uses Amiri Quran (vendored in fonts/). Amiri Quran is cut specifically for
  Quranic text, so the marks equran.id ships (and Tanzil's) sit correctly.
* Highlighting works by re-emitting the whole line with a single step recoloured. libass is
  given one shaped run and only swaps fill colours, so RTL word order, ligatures and mark
  positioning stay correct. (libass' \\k karaoke timing is applied in logical order, which is
  unreliable on right-to-left text, hence this approach.)
* Preview hint: `ffplay video.mp4 -vf "subtitles=file.ass"`, or use MKV/MP4 soft subs.
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
DIM = "&H00B8B8B8"
LATIN = "&H00EAEAEA"
OUTLINE = "&H00000000"
MIN_SHOW = 0.14            # seconds; keeps very short steps visible


def styles(width: int, height: int, scale: float = 1.0) -> list[ass.Style]:
    unit = min(width, height)
    ar_size = int(unit * 0.060 * scale)
    lat_size = int(unit * 0.026 * scale)
    art_size = int(unit * 0.024 * scale)
    margin = int(width * 0.055)
    ar_base = int(height * 0.175)          # arabic block baseline (bottom of the text)

    arabic = ass.Style(
        name="Ar", font=FONT_ARABIC, size=ar_size, primary=BASE,
        outline=max(2.0, ar_size * 0.045), shadow=max(1.0, ar_size * 0.02),
        align=2, margin_l=margin, margin_r=margin, margin_v=ar_base, spacing=0.4,
    )
    latin = ass.Style(
        name="Lat", font=FONT_LATIN, size=lat_size, primary=LATIN,
        outline=2.0, shadow=1.0, align=2, margin_l=margin, margin_r=margin,
        margin_v=ar_base + int(ar_size * 2.15),
    )
    arti = ass.Style(
        name="Id", font=FONT_LATIN, size=art_size, primary=DIM,
        outline=1.8, shadow=0.8, align=2, margin_l=margin, margin_r=margin,
        margin_v=ar_base + int(ar_size * 2.15 + lat_size * 1.75),
    )
    head = ass.Style(
        name="Head", font=FONT_LATIN, size=int(unit * 0.028 * scale), primary=ACTIVE,
        outline=2.0, shadow=0.8, align=8, margin_l=margin, margin_r=margin,
        margin_v=int(height * 0.045),
    )
    return [arabic, latin, arti, head]


def _emit(doc: ass.Document, line: Line, style: str, x: int, y: int, tokens: list[str],
          base: str, highlight: str, *, karaoke: bool, clamp_to: tuple[float, float]) -> None:
    """One visible line, re-emitted per karaoke step so exactly one group is coloured."""
    if not tokens:
        return
    lo, hi = clamp_to
    if len(tokens) <= 1 or len(line.steps) <= 1 or not karaoke:
        s, e = max(line.start, lo), min(line.end, hi)
        text = f"{ass.pos(x, y, 2)}{ass.esc(' '.join(tokens))}"
        doc.events.append(ass.Event(s, max(e, s + MIN_SHOW), style, text))
        return

    idx = 0
    for si, step in enumerate(line.steps):
        count = len(step.tokens)
        groups = []
        for gi in range(count):
            active = idx + gi
            groups.append((active, si == si))
        # build the token list with only this step's token range highlighted
        parts = []
        cursor = 0
        for sj, st in enumerate(line.steps):
            for tk in st.tokens:
                colour = highlight if sj == si else base
                parts.append(f"{{\\c{colour}}}{ass.esc(tk)}")
                cursor += 1
        s = max(step.start, lo)
        e = min(step.end if si < len(line.steps) - 1 else line.end, hi)
        # a step should stay visible until the next step begins
        if si < len(line.steps) - 1:
            e = min(line.steps[si + 1].start, hi)
        if e < s:
            e = s
        if e - s < MIN_SHOW:
            e = s + MIN_SHOW
        doc.events.append(ass.Event(s, e, style, f"{ass.pos(x, y, 2)}{''.join(parts)}"))


def build_document(timeline: Timeline, layout: str = "portrait", *, scale: float = 1.0,
                   karaoke: bool = True, show_latin: bool = True, show_arti: bool = True,
                   show_header: bool = True) -> ass.Document:
    if layout not in LAYOUTS:
        raise ValueError(f"layout '{layout}' tidak dikenal (pilih: {', '.join(LAYOUTS)})")
    width, height = LAYOUTS[layout]
    st = styles(width, height, scale)
    doc = ass.Document(width=width, height=height, styles=st,
                       title=f"Quran {timeline.surah} — {timeline.surah_name}")

    unit = min(width, height)
    ar_size = int(unit * 0.060 * scale)
    lat_size = int(unit * 0.026 * scale)
    cx = width // 2
    ar_y = height - int(height * 0.175)
    lat_y = ar_y - int(ar_size * 2.15)
    arti_y = lat_y - int(lat_size * 1.75)

    if show_header:
        head = f"{timeline.surah_name} · {timeline.surah_arti}" if timeline.surah_arti else timeline.surah_name
        doc.events.append(
            ass.Event(0.0, min(timeline.duration, 4.0), "Head",
                      f"{ass.pos(cx, int(height * 0.045), 8)}{ass.esc(head)}")
        )

    for line in timeline.lines:
        tokens = line.tokens
        window = (line.start - 0.25, line.end + 0.25)
        _emit(doc, line, "Ar", cx, ar_y, tokens, BASE, ACTIVE,
              karaoke=karaoke, clamp_to=window)
        if show_latin and line.latin:
            lat_tokens = line.latin.split()
            _emit(doc, line, "Lat", cx, lat_y, lat_tokens, LATIN, ACTIVE,
                  karaoke=karaoke and len(lat_tokens) == len(tokens), clamp_to=window)
        if show_arti and line.arti:
            arti_tokens = line.arti.split()
            _emit(doc, line, "Id", cx, arti_y, arti_tokens, DIM, ACTIVE,
                  karaoke=karaoke and len(arti_tokens) == len(tokens), clamp_to=window)
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
