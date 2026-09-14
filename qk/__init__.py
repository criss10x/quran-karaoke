"""quran-karaoke: burn word-synced Quran subtitles into a video.

One call does everything: pull the murottal + verse text from equran.id, align the words,
build the karaoke subtitle file, and burn it into the video you supply.

    from qk import render
    result = render.render(
        video="input.mp4",
        surah=1, ayah_from=1, ayah_to=7,
        qari="05",                 # 05 = al-Afasy (has true word timings)
        layout="portrait",
    )
"""
from .api import QARI, DEFAULT_QARI, download_audio, fetch_surah  # noqa: F401
from .build import AlignmentError, Timeline  # noqa: F401
from .build import build as build_timeline  # noqa: F401
from .render import render  # noqa: F401

__all__ = [
    "QARI",
    "DEFAULT_QARI",
    "AlignmentError",
    "Timeline",
    "build_timeline",
    "download_audio",
    "fetch_surah",
    "render",
]
