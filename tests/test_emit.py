"""Self-check: two-band events (Arabic + Indonesian), karaoke on both, no \\pos/\\an per band."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qk import ass, subtitles
from qk.build import Line, Step

BASE, GOLD, ARTI = "&H00FFFFFF", "&H0046C2FE", "&H00E8E8E8"
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


def test_both_bands_present_with_translation_coloured():
    line = _line((["أ", "ب"], 0.0, 1.0), (["ج"], 1.0, 2.0))
    ev = _emit(line, ["أ", "ب", "ج"], ["one", "two", "three"])
    text = ev[0].text
    assert "أ" in text and "one" in text and "three" in text, text
    assert text.count(GOLD) == 2, text      # one arabic step + the matching translation step
    assert _plain(text).index("ج") < _plain(text).index("one"), _plain(text)


def test_translation_without_token_match_still_shown():
    line = _line((["أ", "ب"], 0.0, 1.0), (["ج"], 1.0, 2.0))
    ev = _emit(line, ["أ", "ب", "ج"], ["terjemahan bebas"])
    assert "terjemahan bebas" in ev[0].text, ev[0].text


def test_line_break_every_five_words():
    """Long ayahs must break, or the doubled font runs off both screen edges."""
    words = [f"ك{i}" for i in range(16)]
    ev = _emit(_line((words, 0.0, 1.0)), words, [])
    assert ev[0].text.count("\\N") == 3, ev[0].text          # 16 words -> break after 5, 10, 15
    ev5 = _emit(_line((words[:5], 0.0, 1.0)), words[:5], [])
    assert ev5[0].text.count("\\N") == 0, ev5[0].text


def test_breaks_do_not_split_the_translation_from_the_arabic():
    words = [f"ك{i}" for i in range(7)]
    arti = ["a", "b", "c", "d", "e", "f", "g"]
    ev = _emit(_line((words, 0.0, 1.0)), words, arti)
    text = ev[0].text
    # arabic block (2 lines) then the translation block; order is preserved
    assert _plain(text).index("ك6") < _plain(text).index("a"), _plain(text)
    # 1 break inside the arabic block + 1 joining the blocks + 1 inside the translation
    assert text.count("\\N") == 3, text


def test_no_pos_or_an_codes():
    """Centring comes from Alignment=5 in the style, so events carry no positioning overrides."""
    ev = _emit(_line((["أ"], 0.0, 1.0)), ["أ"], ["satu"])
    assert "\\pos" not in ev[0].text and "\\an" not in ev[0].text, ev[0].text


def test_karaoke_off_emits_plain_line():
    line = _line((["أ", "ب"], 0.0, 1.0))
    ev = _emit(line, ["أ", "ب"], [], karaoke=False)
    assert len(ev) == 1 and GOLD not in ev[0].text


def test_styles_are_centred_and_doubled():
    st = {s.name: s for s in subtitles.styles(1080, 1920)}
    assert st["Ar"].align == 5 and st["Arti"].align == 5
    assert st["Ar"].size >= 160 and st["Arti"].size >= 78      # doubled from 81 / 39


def test_wrapstyle_allows_wrapping():
    doc = ass.Document(width=1080, height=1920, styles=[])
    assert "WrapStyle: 0" in doc.render()


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok: subtitle bands")
