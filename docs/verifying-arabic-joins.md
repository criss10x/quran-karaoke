# Verifying the Arabic joins in the DELIVERED video

`python3 tests/test_emit.py` proves the `.ass` *says* `Spacing: 0.0`. It does not prove the
`.mp4` you are about to send has joined letters — the burn could have used a stale `.ass`, a
different `fontsdir`, or the render could have failed halfway. Check the burned pixels.

```bash
python3 scripts/verify_arabic_joins.py \
  --ass work/user_video/s004_148_05/an-nisa-05.ass \
  --video output/kris_annisa_148.mp4 \
  --fonts fonts --times 1 7 11
```

Exit 0 = the delivered file matches the good style on **every** timestamp.

The `--ass` path is gitignored (`work/`), so on a fresh clone build one first — this writes
the `.ass` without encoding a video (~seconds, vs ~20 min for the full render):

```bash
python3 -m qk.cli /tmp/user_video.mp4 --surah 4 --aya 148 --qari 05 --dry-run
# -> work/user_video/s004_148_05/an-nisa-05.ass
```

## Run the second gate too

```bash
python3 scripts/check_join_blocks.py \
  --ass work/user_video/s004_148_05/an-nisa-05.ass \
  --video output/kris_annisa_148.mp4 --times 1 7 11
```

It renders nothing and never looks at the two candidate renders — it isolates the subtitle by
luminance and counts ink blocks in the Arabic band, comparing against the range the text
implies (one block per word, plus one per word-internal detached group: a non-joining letter
`ا د ذ ر ز و` followed by another letter). Measured on the same clip:

| frame | t=1s | t=7s | t=11s |
|---|---|---|---|
| delivered | **9** | **8** | **4** |
| `Spacing 0.4` burn | 19 | 15 | 12 |

Delivered is in range at every timestamp, the broken burn is out of range at every timestamp,
and it exits 1 for the latter. Because its mechanism shares nothing with
`verify_arabic_joins.py`, agreement between the two is real corroboration rather than the same
artefact measured twice. Run both.

Precondition: a 240 luma threshold has to isolate the subtitle. Verify it on your source — on
these renders the background peaks at luma 200 above the bands (dimmed by `--gelap 0.62`). Pass
`--band y0 y1` if auto-detection grabs the wrong region.

## How it decides

A clean re-render proves nothing, so the script renders the real `.ass` twice on black —
once with the one style field forced to `0.0`, once forced to `0.4` — and scores the
delivered frame against both:

1. Build the discriminator set `D` = pixels where the two variants differ by >40. Outside
   `D` they are identical, so those pixels carry no information.
2. Inside `D` only, score the delivered frame against each candidate: mean absolute delta
   and ink recall (`video>120 and cand>120`, over `video>120`).

Measured on An-Nisa 4:148 / Amiri Quran 162 / 1080x1920:

| candidate | mean abs delta | ink recall |
|---|---|---|
| `Spacing 0.0` (correct) | **13.7 – 30.2** | **95 – 98 %** |
| `Spacing 0.4` (broken) | 180 – 195 | 6 – 8 % |

Two orders of magnitude apart, so the verdict does not hinge on a threshold.

## Prove the check can fail

A check that can never fail is decoration. Burn a deliberately broken variant and confirm
the script rejects it:

```bash
python3 - <<'EOF'
import re, subprocess
src = open('work/user_video/s004_148_05/an-nisa-05.ass').read()
new, n = re.subn(r"(?m)^(Style: Ar,.*?,100,100,)[0-9.]+", r"\g<1>0.4", src)
assert n == 1
open('/tmp/bug.ass', 'w').write(new)
subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi",
                "-i", "color=c=black:s=1080x1920:r=10:d=14",
                "-vf", "ass=/tmp/bug.ass:fontsdir=fonts", "-y", "/tmp/bug.mp4"], check=True)
EOF
python3 scripts/verify_arabic_joins.py --ass work/user_video/s004_148_05/an-nisa-05.ass \
  --video /tmp/bug.mp4 --fonts fonts --times 1 7 11    # must exit 1
```

## Traps

- **Frame 0 is empty.** The first `Dialogue` often starts at 0.11 s, so `-ss 0` captures
  nothing and every metric comes back `None`. Sample mid-event.
- **Do not eyeball a raw video crop with a vision model.** It either reports no image or
  invents a reading. Stack the known-broken render, the known-good render and the
  delivered frame into one labelled image and ask which two match — that works.
- **One matching line can be luck.** Score every dialogue line.

## Why it broke at all

`Spacing` is not cosmetic tracking on Arabic: a non-zero value makes libass skip HarfBuzz's
complex shaper and emit isolated per-glyph forms, so the cursive joins break. The Latin
translation band is untouched, which is what makes it look like a font problem. Full
mechanism and the sweep over `Spacing` values: `references/arabic-spacing-kills-shaping.md`
in the `karaoke-subtitle-burn` skill.
