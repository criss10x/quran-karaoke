#!/usr/bin/env python3
"""Independent join check: count ink blocks in the Arabic band of a burned video.

Second, mechanism-independent opinion alongside ``match_delivered_variant.py``.
That script scores the delivered frame against two renders using the pixels where
those two disagree; this one never renders anything -- it isolates the subtitle by
luminance and counts column-projection ink blocks. Agreement between the two is
real corroboration, not the same artefact measured twice.

Usage:
    python3 check_join_blocks.py --video out.mp4 --ass subs.ass --times 1 7 11
                                  [--band 760 1000] [--thr 240]

Exit 0 when the block count is within the range implied by the text (one block per
word plus one per detached group), exit 1 otherwise. Pass --band to pin the y range
if the automatic band detection picks up something else.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys
import tempfile

from PIL import Image

NONJOINING = set("ادذرزوآأإٱ")


def expected_blocks(words: list[str]) -> tuple[int, int]:
    """Lower/upper bound on ink blocks for a correctly shaped line."""
    lo = len(words)
    extra = sum(sum(1 for ch in w[:-1] if ch in NONJOINING) for w in words)
    return lo, lo + extra


def arabic_lines(ass_path: pathlib.Path) -> list[tuple[str, list[str]]]:
    out = []
    for line in ass_path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("Dialogue"):
            continue
        head, body = line.split(",,", 1)
        arabic = body.split("\\N")[0]
        out.append((head.split(",")[1], arabic.split()))
    return out


def mask(path: pathlib.Path, thr: int) -> Image.Image:
    im = Image.open(path).convert("L")
    return im.point(lambda v: 255 if v >= thr else 0, "L")


def ink_bands(m: Image.Image, min_h: int = 8) -> list[tuple[int, int]]:
    px = m.load()
    w, h = m.size
    rows = [any(px[x, y] for x in range(0, w, 2)) for y in range(h)]
    bands, start = [], None
    for y, on in enumerate(rows + [False]):
        if on and start is None:
            start = y
        elif not on and start is not None:
            if y - start >= min_h:
                bands.append((start, y))
            start = None
    return bands


def blocks(m: Image.Image, y0: int, y1: int, min_w: int = 3) -> list[tuple[int, int]]:
    px = m.load()
    w, _ = m.size
    cols = [any(px[x, y] for y in range(y0, y1)) for x in range(w)]
    runs, inrun = [], False
    for x, on in enumerate(cols + [False]):
        if on and not inrun:
            start, inrun = x, True
        elif not on and inrun:
            if x - start >= min_w:
                runs.append((start, x))
            inrun = False
    return runs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--ass", required=True)
    ap.add_argument("--times", nargs="+", type=float, required=True)
    ap.add_argument("--band", nargs=2, type=int, default=None,
                    help="y0 y1 of the Arabic band (skip auto-detection)")
    ap.add_argument("--thr", type=int, default=240,
                    help="luma threshold isolating the subtitle (default 240)")
    args = ap.parse_args()

    lines = arabic_lines(pathlib.Path(args.ass))
    # skip the header event, which has no Arabic
    arabic = [(t, w) for t, w in lines if any(_is_arabic(x) for x in w)]
    if not arabic:
        print("no Arabic dialogue lines found", file=sys.stderr)
        return 1

    fails = 0
    with tempfile.TemporaryDirectory() as td:
        for t in args.times:
            png = pathlib.Path(td) / f"f_{t}.png"
            subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t),
                            "-i", args.video, "-frames:v", "1", "-y", str(png)],
                           check=True)
            m = mask(png, args.thr)

            idx = min(int(t / 4.95), len(arabic) - 1)
            t0, words = arabic[idx]
            lo, hi = expected_blocks(words)

            if args.band:
                y0, y1 = (int(v) for v in args.band)
            else:
                cands = [b for b in ink_bands(m) if b[0] > m.size[1] * 0.35]
                if not cands:
                    print(f"t={t}s: no ink band found", file=sys.stderr)
                    fails += 1
                    continue
                y0, y1 = max(cands, key=lambda b: b[1] - b[0])

            bl = blocks(m, y0, y1)
            ok = lo <= len(bl) <= hi
            fails += 0 if ok else 1
            print(f"t={t:>5}s  line {t0}  y={y0}-{y1}  blocks={len(bl):3d}  "
                  f"expected {lo}..{hi}  {'OK' if ok else 'MISMATCH'}")

    print(f"\n{'OK: every timestamp within the expected block range.' if not fails else f'FAIL: {fails} timestamp(s) out of range.'}")
    return 0 if not fails else 1


def _is_arabic(s: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", s))


if __name__ == "__main__":
    sys.exit(main())
