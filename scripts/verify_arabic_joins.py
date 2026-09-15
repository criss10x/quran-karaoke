#!/usr/bin/env python3
"""Which ASS variant does the DELIVERED video actually contain?

A clean re-render proves nothing about the file the user has. This answers the real
question: does the burned frame match the FIXED style or the broken one?

Method
------
1. Take the real production `.ass` and override ONE style field (Spacing 0.0 vs 0.4),
   asserting the regex substitution actually fired (re.subn n == 1) — a silent no-op
   otherwise fakes a pass.
2. Render each variant to black at 10 fps, then grab a mid-event frame. Frame 0 is a
   trap: the first Dialogue often starts at 0.11 s, so t=0 captures nothing and every
   metric comes back None.
3. Build the discriminator set D = pixels where the two variants differ by >40.
   Outside D they are identical, so those pixels carry no information.
4. Inside D only, score the delivered frame against each candidate: mean |delta| plus
   ink recall (video>120 and cand>120, over video>120).

Measured on An-Nisa 4:148, Amiri Quran 162, 1080x1920:

    FIXED 0.0    mean|delta| 13.8-30.3   ink_recall 98-99%
    OLD BUG 0.4  mean|delta| 180-195     ink_recall  6-7%

Two orders of magnitude apart, so the verdict does not hinge on a threshold. Repeat
for EVERY dialogue line — one matching line can be luck.

Usage:
    python3 match_delivered_variant.py --ass subs.ass --video out.mp4 --times 1 7 11
    python3 match_delivered_variant.py --ass subs.ass --video out.mp4 --fonts /path/fonts \
        --style Ar --field spacing --a 0.0 --b 0.4

Exit 0 = delivered file matches variant A (the expected good one) on every timestamp.
Exit 1 = it matches B, or the variants are indistinguishable (vacuous test).
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile

from PIL import Image

W, H = 1080, 1920
DIFF_THR = 40          # variants "disagree" above this
INK_THR = 120          # pixel counts as ink


def ass_with(ass_path, style, spacing):
    """Return (temp_ass_path, n_subs) with the style's Spacing field overridden."""
    src = open(ass_path, encoding="utf-8").read()
    # Style line: ... Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,...
    pat = re.compile(r"(?m)^(Style: " + re.escape(style) + r",.*?,100,100,)[0-9.]+")
    new, n = pat.subn(lambda m: m.group(1) + spacing, src)
    if n != 1:
        raise SystemExit(f"override matched {n} style lines, expected 1 — check --style")
    d = tempfile.mkdtemp()
    p = os.path.join(d, "variant.ass")
    open(p, "w", encoding="utf-8").write(new)
    return p, d


def render_variant(ass_path, fonts, dur):
    d = tempfile.mkdtemp()
    mp4 = os.path.join(d, "v.mp4")
    vf = f"ass={ass_path}" + (f":fontsdir={fonts}" if fonts else "")
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi",
                    "-i", f"color=c=black:s={W}x{H}:r=10:d={dur}",
                    "-vf", vf, "-y", mp4], check=True)
    return mp4


def grab(src, t):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", str(t), "-i", src, "-frames:v", "1",
         "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
    if len(raw) != W * H:
        raise SystemExit(f"frame at t={t} is {len(raw)} bytes, expected {W * H}")
    return Image.frombytes("L", (W, H), raw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ass", required=True)
    ap.add_argument("--video", required=True)
    ap.add_argument("--fonts")
    ap.add_argument("--style", default="Ar")
    ap.add_argument("--a", default="0.0", help="expected-good Spacing")
    ap.add_argument("--b", default="0.4", help="known-broken Spacing")
    ap.add_argument("--times", nargs="+", type=float, default=[1.0, 7.0, 11.0])
    args = ap.parse_args()

    a_ass, _ = ass_with(args.ass, args.style, args.a)
    b_ass, _ = ass_with(args.ass, args.style, args.b)
    dur = max(args.times) + 1
    a_mp4 = render_variant(a_ass, args.fonts, dur)
    b_mp4 = render_variant(b_ass, args.fonts, dur)

    verdicts = []
    for t in args.times:
        a, b, v = grab(a_mp4, t), grab(b_mp4, t), grab(args.video, t)
        ap_, bp_, vp_ = a.load(), b.load(), v.load()
        diff = [(x, y) for y in range(H) for x in range(W)
                if abs(ap_[x, y] - bp_[x, y]) > DIFF_THR]
        if not diff:
            print(f"t={t}: variants indistinguishable — test is vacuous")
            verdicts.append("none")
            continue
        ys = [p[1] for p in diff]
        print(f"\nt={t}: discriminating px={len(diff)} y={min(ys)}-{max(ys)}")
        scores = {}
        for name, im in ((f"A {args.a} (expected good)", a), (f"B {args.b} (broken)", b)):
            p = im.load()
            delta = sum(abs(vp_[x, y] - p[x, y]) for x, y in diff) / len(diff)
            ink = sum(1 for x, y in diff if vp_[x, y] > INK_THR)
            recall = sum(1 for x, y in diff
                         if vp_[x, y] > INK_THR and p[x, y] > INK_THR)
            scores[name] = delta
            print(f"  {name:24s} mean|delta|={delta:7.2f}  "
                  f"ink_recall={recall}/{ink}"
                  + (f" = {100 * recall / ink:.0f}%" if ink else ""))
        lo = min(scores, key=scores.get)
        verdicts.append("A" if lo.startswith("A") else "B" if lo.startswith("B") else "?")
        print(f"  -> delivered matches {'A' if lo.startswith('A') else 'B'}")

    if verdicts and all(v == "A" for v in verdicts):
        print("\nOK: delivered file matches the expected-good style on every timestamp.")
        return 0
    print(f"\nFAIL: verdicts per timestamp = {verdicts}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
