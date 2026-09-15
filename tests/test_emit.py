"""Self-check for the subtitle writer.

The load-bearing rule: the Arabic band carries NO override tags, because libass splits text
into runs at every tag that changes something and lays those runs out left-to-right. A tag per
word (the old karaoke highlight) therefore mirrored the line and broke the cursive joins.
Untagged, the line is one run and libass + HarfBuzz render it right-to-left and connected.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qk import ass, subtitles
from qk.build import Line, Step

TAGS = re.compile(r"\{[^}]*\}")


def _plain(text: str) -> str:
    return TAGS.sub("", text)


def _line(*steps):
    return Line(steps=[Step(list(t), s, e) for t, s, e in steps], ayah=1, arti="")


def _texts(line, ar, arti=()):
    doc = ass.Document(width=1080, height=1920, styles=[])
    subtitles._emit(doc, line, ar, list(arti), clamp_to=(0.0, 60.0))
    return [e.text for e in doc.events]


def test_one_event_per_line():
    ar = ["A", "B", "C"]
    assert len(_texts(_line((ar, 0.0, 1.0)), ar)) == 1


def test_arabic_keeps_logical_order():
    """Untagged text is a single run, so libass reorders it itself — do NOT reverse it here."""
    ar = ["A", "B", "C"]
    assert _plain(_texts(_line((ar, 0.0, 1.0)), ar)[0]) == "A B C"


def test_arabic_band_has_no_override_tags():
    """Any tag that changes something would split the run and break the joins and the order."""
    ar = ["A", "B", "C"]
    first = _texts(_line((ar, 0.0, 1.0)), ar)[0].split("\\N")[0]
    assert "{" not in first and "}" not in first, first


def test_translation_stays_left_to_right():
    ar = ["A", "B", "C"]
    texts = _texts(_line((ar, 0.0, 1.0)), ar, ["satu", "dua", "tiga"])
    assert _plain(texts[0]).split("\\N")[-1] == "satu dua tiga"


def test_line_break_every_five_words():
    ar = [f"w{i}" for i in range(7)]
    first, second = _plain(_texts(_line((ar, 0.0, 1.0)), ar)[0]).split("\\N")
    assert first == "w0 w1 w2 w3 w4" and second == "w5 w6"


def test_both_bands_in_one_event():
    ar = ["A", "B"]
    body = _plain(_texts(_line((ar, 0.0, 1.0)), ar, ["one", "two"])[0])
    assert body.index("A B") < body.index("one two"), body


def test_no_pos_an_k_or_colour_codes():
    """Centring comes from Alignment=5 in the style; \\k is unusable on Arabic anyway."""
    joined = " ".join(_texts(_line((["A"], 0.0, 1.0)), ["A"], ["satu"]))
    for code in ("\\pos", "\\an", "\\k", "\\c"):
        assert code not in joined, (code, joined)


def test_no_arti_drops_the_second_band():
    ar = ["A"]
    body = _plain(_texts(_line((ar, 0.0, 1.0)), ar)[0])
    assert body == "A", body


def test_styles_are_centred_and_doubled():
    st = {s.name: s for s in subtitles.styles(1080, 1920)}
    assert st["Ar"].align == 5 and st["Arti"].align == 5
    assert st["Ar"].size >= 160 and st["Arti"].size >= 78      # doubled from 81 / 39


def test_arabic_spacing_is_zero():
    """Non-zero ASS Spacing kills complex shaping: libass then emits isolated
    per-glyph forms, so the cursive joins break. Measured on the 5-word An-Nisa
    line: Spacing 0.0 -> 8 ink blocks (correct), Spacing 0.4 -> 15 (letters
    pulled apart). Arabic never needs letter tracking."""
    st = {s.name: s for s in subtitles.styles(1080, 1920)}
    assert st["Ar"].spacing == 0.0, st["Ar"].spacing


def test_wrapstyle_allows_wrapping():
    doc = ass.Document(width=1080, height=1920, styles=[])
    assert "WrapStyle: 0" in doc.render()


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok: subtitle bands")
