# quran-karaoke — notes for coding agents

Burn word-synced Quran subtitles (Arabic RTL + Indonesian translation) into a video.
Pipeline: `qk/build.py` (timings) → `qk/subtitles.py` (ASS) → `qk/render.py` (ffmpeg burn).

## Hard invariants — do not "clean these up"

- **`Spacing` must stay `0.0` on the `Ar` style** (`qk/subtitles.py`). Any non-zero value
  makes libass drop HarfBuzz's complex shaper and draw isolated per-glyph forms, so every
  cursive join inside every word breaks. The Latin band is unaffected, which is what makes it
  look like a font bug. Guarded by `tests/test_emit.py::test_arabic_spacing_is_zero`.
- **The Arabic band carries no override tags.** One untagged run per screen line, in logical
  order; a single `\N` and one `{\rArti}` before the translation. libass splits text into runs
  at every tag that *changes* something and lays the runs out in emission order, which mirrors
  the line and breaks the joins — so the per-word karaoke highlight is gone by design, not
  broken. A tag repeating the style's own colour is a no-op libass drops, and that is exactly
  how the join bug hid. Details: `docs/verifying-arabic-joins.md`.
- **Anything under `work/` is regenerated** by `build_document()` on the next run. Fix the
  emitter, never the generated `.ass`.

## Checks

```bash
python3 tests/test_qalign.py && python3 tests/test_emit.py   # unit, plain asserts, no pytest

python3 scripts/verify_arabic_joins.py --ass <file.ass> --video <out.mp4> \
    --fonts fonts --times 1 7 11                              # exit 0 = joins intact
```

The second one is the real gate: it renders the same `.ass` twice (one style field forced to
`0.0` and to `0.4`) and scores the **delivered** frame against both, inside the pixels where
only those two disagree. A clean re-render is not evidence. Before trusting it, prove it can
fail — burn a `Spacing: 0.4` variant and confirm exit 1. Method and measured numbers:
`docs/verifying-arabic-joins.md`.

## Render

```bash
python3 -m qk.cli /tmp/user_video.mp4 --surah 4 --aya 148 --qari 05 \
    --out output/kris_annisa_148.mp4 --force
```

~20 min for a 13 s clip (`tpad` + `libx264 medium`). Run it in the background, not in a
foreground shell — the terminal cap is 600 s and the process is killed silently at the cap.
`--dry-run` writes the `.ass` + audio without encoding (seconds), which is how to get the
`--ass` input for the join check on a fresh clone (`work/` is gitignored).
