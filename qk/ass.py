"""Minimal ASS (Advanced SubStation Alpha) writer with word-karaoke helpers.

The karaoke strategy implemented here is "re-emit the line": every time the active word
changes, the whole line is emitted again with that one word drawn in the highlight colour.
Each event gets a fixed \\pos, so a line stays put while the highlight walks across it.

This is used instead of libass \\k tags on purpose: \\k timing is applied in logical (pre-bidi)
order, which makes word-accurate highlighting of right-to-left Arabic unreliable. Re-emitting
keeps the text a single shaped run and only swaps colours, so shaping, ligatures and mark
positioning stay correct.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field


def ts(seconds: float) -> str:
    """ASS timestamp H:MM:SS.cc"""
    if seconds < 0:
        seconds = 0.0
    cs = int(round(seconds * 100))
    h, rem = divmod(cs, 360000)
    m, rem = divmod(rem, 6000)
    s, c = divmod(rem, 100)
    return f"{h:d}:{m:02d}:{s:02d}.{c:02d}"


def esc(text: str) -> str:
    """Escape ASS-special characters and collapse newlines."""
    return (
        text.replace("\\", "\\\\")
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace("\r", " ")
        .replace("\n", " ")
    )


@dataclass
class Style:
    name: str
    font: str
    size: int
    primary: str = "&H00FFFFFF"       # fill colour (&HAABBGGRR)
    secondary: str = "&H00FFFFFF"
    outline_colour: str = "&H00000000"
    back_colour: str = "&H00000000"
    bold: int = 0
    italic: int = 0
    outline: float = 3.0
    shadow: float = 1.0
    align: int = 2                    # 2 = bottom centre
    margin_l: int = 40
    margin_r: int = 40
    margin_v: int = 40
    spacing: float = 0.0
    border_style: int = 1

    def line(self) -> str:
        return (
            f"Style: {self.name},{self.font},{self.size},{self.primary},{self.secondary},"
            f"{self.outline_colour},{self.back_colour},{self.bold},{self.italic},0,0,100,100,"
            f"{self.spacing},{0},{self.border_style},{self.outline},{self.shadow},{self.align},"
            f"{self.margin_l},{self.margin_r},{self.margin_v},1"
        )


@dataclass
class Event:
    start: float
    end: float
    style: str
    text: str
    layer: int = 0


@dataclass
class Document:
    width: int
    height: int
    styles: list[Style] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    title: str = "quran-karaoke"

    def render(self) -> str:
        head = [
            "[Script Info]",
            f"Title: {self.title}",
            "ScriptType: v4.00+",
            "WrapStyle: 2",
            "ScaledBorderAndShadow: yes",
            "YCbCr Matrix: TV.709",
            f"PlayResX: {self.width}",
            f"PlayResY: {self.height}",
            "",
            "[V4+ Styles]",
            "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,"
            "Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,"
            "Alignment,MarginL,MarginR,MarginV,Encoding",
        ]
        head += [s.line() for s in self.styles]
        head += [
            "",
            "[Events]",
            "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text",
        ]
        body = [
            f"Dialogue: {e.layer},{ts(e.start)},{ts(e.end)},{e.style},,0,0,0,,{e.text}"
            for e in sorted(self.events, key=lambda x: (x.start, x.layer))
        ]
        return "\n".join(head + body) + "\n"


def pos(x: int, y: int, align: int) -> str:
    return f"\\an{align}\\pos({x},{y})"


def karaoke_line(tokens: list[str], active: int | None, highlight: str, base: str = "&H00FFFFFF") -> str:
    """Colour-override each token, drawing `active` in `highlight`."""
    parts = []
    for i, t in enumerate(tokens):
        colour = highlight if i == active else base
        parts.append(f"{{\\c{colour}}}{esc(t)}")
    return "".join(parts)
