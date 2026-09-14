#!/usr/bin/env python3
"""quran-karaoke CLI.

    python -m qk.cli video.mp4 --surah 1 --qari 05
    python -m qk.cli video.mp4 --surah 112 --qari 03 --layout portrait --aya 1-4
"""
from __future__ import annotations

import argparse
import glob
import os
import shutil
import subprocess
import sys

from . import api
from .render import render as render_video


def parse_aya(spec: str) -> tuple[int, int | None]:
    spec = spec.strip()
    if "-" in spec:
        a, b = spec.split("-", 1)
        return int(a), int(b)
    return int(spec), int(spec)


def list_qari() -> None:
    from .qalign import QARI_DATASET

    print("Qari murottal (equran.id):")
    for k, (_, name) in api.QARI.items():
        mark = "  <- word-timing presisi" if k in QARI_DATASET else ""
        print(f"  {k}  {name}{mark}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="qk", description="Burn word-synced Quran subtitles into a video.")
    p.add_argument("video", nargs="?", help="video sumber (mp4/mov/mkv)")
    p.add_argument("--daftar-qari", action="store_true", help="tampilkan daftar qari lalu keluar")
    p.add_argument("--surah", type=int, help="nomor surah (1-114)")
    p.add_argument("--aya", default=None, help="ayat: '5' atau '1-7' (default: semua ayat)")
    p.add_argument("--qari", default=None, help=f"id qari equran (default {api.DEFAULT_QARI})")
    p.add_argument("--layout", default="portrait", choices=["portrait", "landscape", "square"])
    p.add_argument("--align", default="auto", choices=["auto", "qalign", "proportional"],
                   help="qalign = timing per kata (butuh qari 03/05); proportional = bagi rata")
    p.add_argument("--fit", default="audio", choices=["audio", "video"],
                   help="audio = durasi video mengikuti murottal; video = sebaliknya")
    p.add_argument("--no-karaoke", action="store_true", help="matikan highlight per kata")
    p.add_argument("--no-latin", action="store_true", help="sembunyikan teks latin")
    p.add_argument("--no-arti", action="store_true", help="sembunyikan terjemahan")
    p.add_argument("--no-header", action="store_true", help="sembunyikan judul surah")
    p.add_argument("--scale", type=float, default=1.0, help="skala ukuran teks (mis. 0.9)")
    p.add_argument("--out", default=None, help="path output mp4")
    p.add_argument("--workdir", default=None, help="folder kerja (default work/<video>/s<no>_<ayat>_<qari>)")
    p.add_argument("--crf", type=int, default=19, help="kualitas x264 (kecil = lebih bagus)")
    p.add_argument("--preset", default="medium")
    p.add_argument("--audio-out", default=None, help="hanya tulis audio murottal ke path ini lalu keluar")
    p.add_argument("--dry-run", action="store_true", help="buat .ass + audio saja, tanpa encode")
    p.add_argument("--force", action="store_true", help="unduh ulang audio/teks")
    a = p.parse_args(argv)

    if a.daftar_qari:
        list_qari()
        return 0

    if not a.video:
        p.error("perlu path video (atau pakai --daftar-qari)")
    if not a.surah:
        p.error("perlu --surah")

    qari = a.qari or api.DEFAULT_QARI
    if qari not in api.QARI:
        p.error(f"qari '{qari}' tidak dikenal; jalankan --daftar-qari")
    af, at = parse_aya(a.aya) if a.aya else (1, None)

    if a.audio_out:
        from .build import build

        tl = build(a.surah, af, at, qari=qari, align=a.align, workdir="work/_audio", force=a.force)
        shutil.copyfile(tl.audio, a.audio_out)
        print(f"audio murottal -> {a.audio_out}  ({tl.duration:.2f}s)")
        return 0

    want_video = bool(shutil.which("ffmpeg"))
    if not want_video:
        print("ffmpeg tidak ada di PATH", file=sys.stderr)
        return 2

    res = render_video(
        a.video, a.surah, af, at,
        qari=qari, layout=a.layout, out=a.out, align=a.align, scale=a.scale,
        workdir=a.workdir,
        karaoke=not a.no_karaoke, show_latin=not a.no_latin, show_arti=not a.no_arti,
        show_header=not a.no_header, fit=a.fit, crf=a.crf, preset=a.preset,
        dry_run=a.dry_run, force=a.force,
    )
    mode = {"qalign": "per kata (quran-align)", "proportional": "bagi rata (perkiraan)"}[res.align]
    print(f"\nSelesai!")
    print(f"  video    : {res.video}{'  (dry-run, tidak di-encode)' if a.dry_run else ''}")
    print(f"  subtitle : {res.ass}")
    print(f"  audio    : {res.audio}")
    print(f"  surah    : {res.surah} · {res.qari} · {res.duration:.1f}s")
    print(f"  baris    : {res.lines} baris, {res.steps} langkah karaoke")
    print(f"  timing   : {mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
