"""Self-check: two-band events (Arabic + Indonesian), karaoke on both, no \\pos/\\an per band."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qk import ass, subtitles
from qk.build import Line, Step

import re

BASE, GOLD, ARTI = "&H00FFFFFF", "&H0046C2FE", "&H00E8E8E8"
BREAK = "\\N{\\rArti}"
TAGS = re.compile(r"\{[^}]*\}")


def _plain(text: str) -> str:
    """Event text with every ASS override block removed."""
    return TAGS.sub("", text)


def _line(*steps):
    return Line(steps=[Step(list(t), s, e) for t, s, e in steps], ayah=1, arti="")


def _emit(line, ar, arti, karaoke=True):
    doc = ass.Document(width=1080, height=1920, styles=[])
    subtitles._emit(doc, line, ar, arti, karaoke=karaoke, clamp_to=(0.0, 60.0))
    return doc.events


def test_single_step_line_still_highlights():
    """Al-Fatihah's last word is a one-step line — it used to render with no highlight."""
    ev = _emit(_line((["الضَّآلِّينَ"], 39.9, 46.0)), ["الضَّآلِّينَ"], [])
    assert ev and GOLD in ev[0].text, ev


def test_each_step_highlighted_exactly_once():
    line = _line((["أ", "ب"], 0.0, 1.0), (["ج"], 1.0, 2.0))
    ev = _emit(line, ["أ", "ب", "ج"], [])
    assert len(ev) == 2, len(ev)
    for e in ev:
        assert e.text.count(GOLD) == 1, e.text
        assert e.text.count(BASE) == 1, e.text


def test_arabic_words_keep_their_spaces():
    """Bare concatenation glues cursive Arabic words into one (`غير`+`المغضوب`)."""
    ev = _emit(_line((["غير", "المغضوب"], 0.0, 1.0)), ["غير", "المغضوب"], [])
    assert "غير المغضوب" in ev[0].text, ev[0].text


def test_two_bands_in_one_event():
    line = _line((["أ", "ب"], 0.0, 1.0), (["ج"], 1.0, 2.0))
    ev = _emit(line, ["أ", "ب", "ج"], ["one", "two", "three"])
    assert BREAK in ev[0].text, ev[0].text
    head, body = ev[0].text.split(BREAK, 1)
    assert body.count(GOLD) == 1, body
    assert head.count(GOLD) == 1, head
    assert "one two three" in _plain(body), body


def test_translation_without_token_match_rides_along_plain():
    line = _line((["أ", "ب"], 0.0, 1.0), (["ج"], 1.0, 2.0))
    ev = _emit(line, ["أ", "ب", "ج"], ["terjemahan bebas"])
    body = ev[0].text.split(BREAK, 1)[1]
    # no invented word alignment: the translation shows plain, colour coming from the Arti style
    assert GOLD not in body, body
    assert "terjemahan bebas" in body, body


def test_no_pos_or_an_codes():
    """Centring comes from Alignment=5 in the style, so events carry no positioning overrides."""
    line = _line((["أ"], 0.0, 1.0))
    ev = _emit(line, ["أ"], ["satu"])
    assert "\\pos" not in ev[0].text and "\\an" not in ev[0].text, ev[0].text


def test_karaoke_off_emits_plain_line():
    line = _line((["أ", "ب"], 0.0, 1.0))
    ev = _emit(line, ["أ", "ب"], [], karaoke=False)
    assert len(ev) == 1 and GOLD not in ev[0].text


def test_styles_are_centred():
    st = {s.name: s for s in subtitles.styles(1080, 1920)}
    assert st["Ar"].align == 5 and st["Arti"].align == 5
    assert st["Arti"].margin_v < 0            # lifts the translation above the arabic band
    assert st["Ar"].size > 60 and st["Ar"].size > st["Arti"].size


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok: subtitle bands")
