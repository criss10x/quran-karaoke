"""Top-level orchestration: timeline -> subtitles -> one burnt-in video file."""
from __future__ import annotations

import dataclasses
import os
import re
import subprocess

from . import subtitles
from .build import build as build_timeline


@dataclasses.dataclass
class RenderResult:
    video: str
    ass: str
    audio: str
    duration: float
    align: str
    qari: str
    surah: str
    lines: int
    steps: int


def render(
    video: str,
    surah: int,
    ayah_from: int = 1,
    ayah_to: int | None = None,
    *,
    qari: str = "03",
    layout: str = "portrait",
    out: str | None = None,
    workdir: str | None = None,
    align: str = "auto",
    scale: float = 1.0,
    karaoke: bool = True,
    show_arti: bool = True,
    show_header: bool = True,
    fit: str = "audio",
    cover: bool = True,
    crf: int = 19,
    preset: str = "medium",
    fonts_dir: str | None = None,
    brightness: float = 1.0,
    dry_run: bool = False,
    force: bool = False,
) -> RenderResult:
    """Burn word-synced Quran subtitles into `video`.

    fit="audio" -> output length follows the murottal (video trimmed, last frame held)
    fit="video" -> output length follows the video (murottal padded with silence)
    brightness  -> multiply the source video by this factor (<1 darkens it, subtitles keep
                   their own colours because libass runs after the grade)
    """
    if not os.path.exists(video):
        raise FileNotFoundError(video)
    stem = os.path.splitext(os.path.basename(video))[0]
    if workdir is None:
        span = f"{ayah_from}-{ayah_to}" if ayah_to and ayah_to != ayah_from else str(ayah_from)
        # one directory per selection, so different surahs never overwrite each other's
        # murottal.mp3 / .ass while sharing the same source clip
        workdir = os.path.join("work", stem, f"s{surah:03d}_{span}_{qari}")
    os.makedirs(workdir, exist_ok=True)

    timeline = build_timeline(
        surah, ayah_from, ayah_to, qari=qari, align=align, workdir=workdir, force=force
    )
    ass_path = os.path.join(workdir, f"{_slug(timeline.surah_name)}-{timeline.qari}.ass")
    doc = subtitles.build_document(
        timeline, layout=layout, scale=scale, karaoke=karaoke,
        show_arti=show_arti, show_header=show_header,
        # the highlight is measured by rendering with the very same fonts ffmpeg will use
        fonts_dir=fonts_dir or _fonts_dir(),
    )
    subtitles.write_ass(doc, ass_path)

    out = out or os.path.join("output", f"{stem}_{_slug(timeline.surah_name)}.mp4")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)

    if not dry_run:
        _burn(
            video, timeline.audio, ass_path, out,
            layout=layout, fit=fit, cover=cover,
            crf=crf, preset=preset, fonts_dir=fonts_dir or _fonts_dir(),
            brightness=brightness,
        )
    return RenderResult(
        video=out, ass=ass_path, audio=timeline.audio, duration=timeline.duration,
        align=timeline.align, qari=timeline.qari_name, surah=timeline.surah_name,
        lines=len(timeline.lines), steps=len(timeline.steps),
    )


def _fonts_dir() -> str | None:
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    d = os.path.join(here, "fonts")
    return d if os.path.isdir(d) else None


def _slug(name: str) -> str:
    """Filesystem- and ffmpeg-filter-safe form of a surah name.

    Some names carry punctuation ("An-Nisa'"), which the ass= filter path rejects, so keep
    only alphanumerics and hyphens.
    """
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _burn(video, audio, ass_path, out, *, layout, fit, cover, crf, preset, fonts_dir,
          brightness=1.0):
    """Compose: scale/crop the video, darken it, lay the murottal under it, burn the subtitles."""
    width, height = subtitles.LAYOUTS[layout]
    vf = []
    if cover:
        vf.append(f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}")
    else:
        vf.append(f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                  f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black")
    vf.append("setsar=1")
    if brightness != 1.0:
        # multiply each channel: `eq` applied a near-black gamma crush, lutrgb is exactly the
        # factor the caller asked for. Subtitles keep full white — libass runs after this.
        b = round(brightness, 3)
        vf.append(f"lutrgb=r=val*{b}:g=val*{b}:b=val*{b}")
    bad = "".join(ch for ch in ass_path if ch in "\\':[],=")
    if bad:
        raise ValueError(f"path subtitle mengandung karakter aneh: {bad!r}")
    ass_filter = f"ass={ass_path}"
    if fonts_dir:
        ass_filter += f":fontsdir={fonts_dir}"
    vf.append(ass_filter)

    common = ["-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p",
              "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart"]
    if fit == "audio":
        # trim video to the murottal; if the video is short, hold its last frame.
        # ponytail: clone-pad for an hour so the murottal is never cut short; -shortest ends the
        # output when the audio does, so no extra frames are actually encoded.
        cmd = ["ffmpeg", "-y", "-v", "warning", "-stats", "-i", video, "-i", audio,
               "-filter_complex",
               f"[0:v]trim=0,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=3600,"
               f"{','.join(vf)}[v]",
               "-map", "[v]", "-map", "1:a", "-shortest"] + common + [out]
    elif fit == "video":
        cmd = ["ffmpeg", "-y", "-v", "warning", "-stats", "-i", video, "-i", audio,
               "-filter_complex", f"[0:v]{','.join(vf)}[v]",
               "-map", "[v]", "-map", "1:a", "-apad"] + common + [out]
    else:
        raise ValueError("fit harus 'audio' atau 'video'")
    subprocess.run(cmd, check=True)
    return out
