"""Self-check: every visible step carries the highlight, including single-step lines."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qk import ass, subtitles
from qk.build import Line, Step

BASE, GOLD = "&H00FFFFFF", "&H0046C2FE"


def _line(*steps):
    return Line(steps=[Step(list(t), s, e) for t, s, e in steps], ayah=1, latin="", arti="")


def test_single_step_line_still_highlights():
    """Al-Fatihah's last word is a one-step line — it used to render with no highlight."""
    line = _line((["الضَّآلِّينَ"], 39.9, 46.0))
    doc = ass.Document(width=1080, height=1920, styles=[])
    subtitles._emit(doc, line, "Ar", 540, 1500, line.tokens, BASE, GOLD,
                    karaoke=True, clamp_to=(0.0, 47.0))
    assert doc.events, "no event emitted"
    assert any(GOLD in ev.text for ev in doc.events), doc.events[0].text


def test_each_step_highlighted_exactly_once():
    line = _line((["أ", "ب"], 0.0, 1.0), (["ج"], 1.0, 2.0))
    doc = ass.Document(width=1080, height=1920, styles=[])
    subtitles._emit(doc, line, "Ar", 540, 1500, line.tokens, BASE, GOLD,
                    karaoke=True, clamp_to=(0.0, 3.0))
    assert len(doc.events) == 2, len(doc.events)
    for ev in doc.events:
        assert ev.text.count(GOLD) == 1, ev.text


def test_karaoke_off_emits_plain_line():
    line = _line((["أ", "ب"], 0.0, 1.0))
    doc = ass.Document(width=1080, height=1920, styles=[])
    subtitles._emit(doc, line, "Ar", 540, 1500, line.tokens, BASE, GOLD,
                    karaoke=False, clamp_to=(0.0, 3.0))
    assert len(doc.events) == 1 and GOLD not in doc.events[0].text


if __name__ == "__main__":
    test_single_step_line_still_highlights()
    test_each_step_highlighted_exactly_once()
    test_karaoke_off_emits_plain_line()
    print("ok: karaoke highlight")
