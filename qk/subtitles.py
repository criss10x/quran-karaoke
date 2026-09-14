"""Turn a Timeline into the ASS subtitle file and the ffmpeg command that burns it in.

Styling notes
-------------
* Two bands only: the Arabic line (Amiri Quran, vendored in fonts/) and its Indonesian
  translation under it. No transliteration.
* Both bands use ``Alignment=5`` (middle centre). That centres them on the frame and stacks
  them around the vertical middle with **no** ``\\pos``/``\\an`` overrides in the event text at
  all: align=5 also lifts the bottom-margin clamp, so the translation band is simply offset with
  a negative ``MarginV``.
* The two bands are glued into one event: the Arabic run, then a literal ``\\N`` (hard line
  break), then ``{\\rArti}`` to switch font/size, then the translation. Switching styles mid-event
  keeps both bands one timed unit and lets the karaoke highlight walk through both at once.
* Highlighting works by re-emitting the whole line with a single step recoloured. libass is
  given one shaped run and only swaps fill colours, so RTL word order, ligatures and mark
  positioning stay correct. (libass' ``\\k`` karaoke timing is applied in logical order, which is
  unreliable on right-to-left text, hence this approach.)
* Preview hint: ``ffplay video.mp4 -vf "subtitles=file.ass"``, or use MKV/MP4 soft subs.
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

AR_FRAC = 0.075            # arabic size, fraction of the shorter frame side
ARTI_FRAC = 0.037
# ponytail: lift tuned against 1080x1920; one arabic line height, so it tracks AR_FRAC*unit.
ARTI_LIFT = 0.075
_ARTI_BREAK = "\\N{\\rArti}"


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
        outline=2.0, shadow=0.8, align=5, margin_l=margin, margin_r=margin,
        margin_v=-int(unit * ARTI_LIFT * scale),
    )
    head = ass.Style(
        name="Head", font=FONT_LATIN, size=int(unit * 0.028 * scale), primary=ACTIVE,
        outline=2.0, shadow=0.8, align=8, margin_l=margin, margin_r=margin,
        margin_v=int(height * 0.045),
    )
    return [arabic, arti, head]


def _colourise(tokens: list[str], spans: list[tuple[int, int]], active: int,
               base: str, highlight: str) -> str:
    """Tokens as ASS text: one ``{\\c}`` tag per colour run, words space-separated.

    Words must stay space-separated — Arabic is cursive, so bare concatenation would run
    `غير` and `المغضوب` together into a single word.
    """
    parts, prev = [], None
    for si, (b0, b1) in enumerate(spans):
        colour = highlight if si == active else base
        if colour != prev:
            parts.append(f"{{\\c{colour}}}")
            prev = colour
        parts.extend(f"{ass.esc(tk)} " for tk in tokens[b0:b1])
    return "".join(parts).rstrip()


def _emit(doc: ass.Document, line: Line, ar_tokens: list[str], arti_tokens: list[str], *,
          karaoke: bool, clamp_to: tuple[float, float]) -> None:
    """Emit one two-band event per karaoke step (or a single plain event).

    Step boundaries index the Arabic tokens; the translation is coloured step-by-step only when
    its own word count lines up, and otherwise rides along unhighlighted — guessing a word
    alignment for a translation that doesn't share the Arabic word count would highlight the
    wrong phrase.
    """
    if not ar_tokens:
        return
    lo, hi = clamp_to
    spans, total = [], 0
    for st in line.steps:
        spans.append((total, total + len(st.tokens)))
        total += len(st.tokens)

    tail = f"{_ARTI_BREAK}{ass.esc(' '.join(arti_tokens))}" if arti_tokens else ""
    arti_spans = spans if len(arti_tokens) == total else None

    def frame(active: int | None) -> str:
        if active is None:
            head = ass.esc(" ".join(ar_tokens))
        else:
            head = _colourise(ar_tokens, spans, active, BASE, ACTIVE)
        if not arti_tokens:
            return head
        if active is not None and arti_spans:
            body = _colourise(arti_tokens, arti_spans, active, ARTI, ACTIVE)
        else:
            body = ass.esc(" ".join(arti_tokens))
        return f"{head}{_ARTI_BREAK}{body}"

    if not karaoke or len(ar_tokens) != total:
        # plain band, no highlight (also the safety net when a caller's word count differs)
        s, e = max(line.start, lo), min(line.end, hi)
        doc.events.append(ass.Event(s, max(e, s + MIN_SHOW), "Ar", frame(None)))
        return

    for si, step in enumerate(line.steps):
        s = max(step.start, lo)
        e = min(step.end if si < len(line.steps) - 1 else line.end, hi)
        # a step should stay visible until the next step begins
        if si < len(line.steps) - 1:
            e = min(line.steps[si + 1].start, hi)
        if e < s:
            e = s
        if e - s < MIN_SHOW:
            e = s + MIN_SHOW
        doc.events.append(ass.Event(s, e, "Ar", frame(si)))


def build_document(timeline: Timeline, layout: str = "portrait", *, scale: float = 1.0,
                   karaoke: bool = True, show_arti: bool = True,
                   show_header: bool = True) -> ass.Document:
    if layout not in LAYOUTS:
        raise ValueError(f"layout '{layout}' tidak dikenal (pilih: {', '.join(LAYOUTS)})")
    width, height = LAYOUTS[layout]
    doc = ass.Document(width=width, height=height, styles=styles(width, height, scale),
                       title=f"Quran {timeline.surah} — {timeline.surah_name}")

    if show_header:
        head = f"{timeline.surah_name} · {timeline.surah_arti}" if timeline.surah_arti else timeline.surah_name
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
