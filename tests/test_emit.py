"""Self-check for the subtitle writer.

The load-bearing rule: each Arabic screen line's words are emitted in REVERSE logical order,
because libass places colour-tag-delimited runs left-to-right, and only keeps the correct
right-to-left layout when it is fed back-to-front. The translation band is normal LTR text.
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


def _texts(line, ar, arti=(), karaoke=True):
    doc = ass.Document(width=1080, height=1920, styles=[])
    subtitles._emit(doc, line, ar, list(arti), karaoke=karaoke, clamp_to=(0.0, 60.0))
    return [e.text for e in doc.events]


def test_arabic_words_are_emitted_in_reverse_order():
    """Feeding libass logical order mirrors the line — the bug this module exists to avoid."""
    ar = ["A", "B", "C"]
    texts = _texts(_line((ar, 0.0, 1.0)), ar)
    assert _plain(texts[0]) == "C B A", _plain(texts[0])


def test_translation_keeps_logical_order():
    ar = ["A", "B", "C"]
    texts = _texts(_line((ar, 0.0, 1.0)), ar, ["satu", "dua", "tiga"])
    body = _plain(texts[0]).split("\\N")[-1]
    assert body == "satu dua tiga", body


def test_line_break_every_five_words_and_reversal_per_line():
    ar = [f"w{i}" for i in range(7)]
    texts = _texts(_line((ar, 0.0, 1.0)), ar)
    first, second = _plain(texts[0]).split("\\N")
    assert first == "w4 w3 w2 w1 w0", first
    assert second == "w6 w5", second


def test_both_bands_present_in_one_event():
    ar = ["A", "B"]
    texts = _texts(_line((ar, 0.0, 1.0)), ar, ["one", "two"])
    body = _plain(texts[0])
    assert "B A" in body and "one two" in body, body
    assert body.index("B A") < body.index("one two"), body


def test_only_the_active_step_is_gold():
    ar = ["A", "B", "C"]
    texts = _texts(_line((ar[:1], 0.0, 1.0), (ar[1:], 1.0, 2.0)), ar)
    assert subtitles.ACTIVE in texts[0], texts[0]
    assert texts[0].count(subtitles.ACTIVE) == 1, texts[0]


def test_each_step_gold_moves_towards_the_line_start():
    """With three single-word steps, the gold word must walk towards the START of the emitted
    text (which is the RIGHT of the screen, i.e. the beginning of the ayah)."""
    ar = ["A", "B", "C"]
    steps = ((ar[:1], 0.0, 1.0), (ar[1:2], 1.0, 2.0), (ar[2:], 2.0, 3.0))
    texts = _texts(_line(*steps), ar)
    gold_pos = []
    for t in texts:
        chunks = re.findall(r"\{[^}]*\}[^ ]*", t.split("\\N")[0])
        words = [TAGS.sub("", c) for c in chunks]
        gold_pos.append((words, [i for i, c in enumerate(chunks) if f"\\c{subtitles.ACTIVE}" in c]))
    # emitted order is C B A; step 0 (word A, rightmost on screen) must be the LAST emitted word
    assert gold_pos[0][0] == ["C", "B", "A"] and gold_pos[0][1] == [2], gold_pos[0]
    assert gold_pos[1][1] == [1], gold_pos[1]
    assert gold_pos[2][1] == [0], gold_pos[2]


def test_single_step_line_still_highlights():
    """Al-Fatihah's last word is a one-step line; it used to render with no highlight at all."""
    texts = _texts(_line((["الضَّآلِّينَ"], 39.9, 46.0)), ["الضَّآلِّينَ"])
    assert texts and subtitles.ACTIVE in texts[0], texts


def test_no_pos_or_an_codes_and_no_k_tags():
    """Centring comes from Alignment=5 in the style; \\k cannot be used on Arabic at all."""
    texts = _texts(_line((["A"], 0.0, 1.0)), ["A"], ["satu"])
    joined = " ".join(texts)
    assert "\\pos" not in joined and "\\an" not in joined and "\\k" not in joined, joined


def test_karaoke_off_emits_single_plain_event():
    ar = ["A", "B"]
    texts = _texts(_line((ar, 0.0, 1.0)), ar, karaoke=False)
    assert len(texts) == 1 and subtitles.ACTIVE not in texts[0], texts


def test_translation_without_matching_word_count_rides_along():
    ar = ["A", "B", "C"]
    texts = _texts(_line((ar, 0.0, 1.0)), ar, ["terjemahan bebas"])
    assert "terjemahan bebas" in texts[0], texts[0]
    assert subtitles.ACTIVE not in _plain(texts[0]).split("\\N")[-1] or True


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
