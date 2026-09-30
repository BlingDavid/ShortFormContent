"""Locate ffmpeg and probe media without needing ffprobe."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from functools import lru_cache


@lru_cache(maxsize=1)
def ffmpeg_exe() -> str:
    if os.environ.get("FFMPEG"):
        return os.environ["FFMPEG"]
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        sys.exit("ffmpeg not found. Install it (apt/brew) or run: pip install imageio-ffmpeg")


def run(args: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run([ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y", *args],
                          check=True, **kw)


def probe(path) -> dict:
    """Duration, size, fps, audio presence and colour tags, parsed from `ffmpeg -i`."""
    r = subprocess.run([ffmpeg_exe(), "-hide_banner", "-i", str(path)],
                       capture_output=True, text=True)
    s = r.stderr
    info: dict = {"path": str(path), "duration": None, "width": None, "height": None,
                  "fps": None, "has_audio": "Audio:" in s, "colorspace": None}
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", s)
    if m:
        info["duration"] = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])
    v = re.search(r"Video:.*", s)
    if v:
        line = v.group(0)
        d = re.search(r"[\s,](\d{2,5})x(\d{2,5})[\s,\[]", line)
        if d:
            info["width"], info["height"] = int(d[1]), int(d[2])
        f = re.search(r"([\d.]+)\s*fps", line)
        if f:
            info["fps"] = float(f[1])
        for tag in ("bt709", "smpte170m", "bt470bg", "bt2020nc"):
            if tag in line:
                info["colorspace"] = tag
                break
    return info
