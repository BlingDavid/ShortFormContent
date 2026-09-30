"""Decode clips to normalised RGB frames; encode the finished picture."""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np

import ffutil
from timeline import Timeline

MATRIX = {None: "bt709", "bt709": "bt709", "smpte170m": "bt601", "bt470bg": "bt601", "bt2020nc": "bt2020"}


def decode_filter(tl: Timeline, clip: dict) -> str:
    """Scale-to-cover + crop to the project frame, constant fps, RGB. Untagged HD is treated as Rec.709."""
    W, H = tl.format["width"], tl.format["height"]
    info = ffutil.probe(tl.path(clip["file"]))
    cx, cy = clip.get("focus", [0.5, 0.5])
    chain = []
    if clip["_speed"] != 1.0:
        chain.append(f"setpts=PTS/{clip['_speed']}")
    # One exact YUV->RGB step first (explicit matrix), then geometry in RGB. Measured within +-1 code
    # value on an 8-colour Rec.709 chart; the naive scale-then-format chain came out 2 values dark.
    chain += [f"fps={tl.fps}",
              f"scale=in_color_matrix={MATRIX.get(info['colorspace'], 'auto')}:out_range=full:"
              "flags=accurate_rnd+full_chroma_int+bicubic",
              "format=rgb24",
              f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos",
              f"crop={W}:{H}:(iw-{W})*{cx}:(ih-{H})*{cy}",
              "setsar=1"]
    return ",".join(chain)


def read_clip_frames(tl: Timeline, clip: dict, n_frames: int, source_start: float | None = None):
    """Yield exactly n_frames HxWx3 uint8 frames. If the source runs short, the last frame repeats."""
    W, H = tl.format["width"], tl.format["height"]
    size = W * H * 3
    ss = clip["_in"] if source_start is None else source_start
    want = n_frames / tl.fps * clip["_speed"]
    cmd = [ffutil.ffmpeg_exe(), "-v", "error", "-ss", f"{ss:.4f}", "-t", f"{want + 0.5:.4f}",
           "-i", str(tl.path(clip["file"])), "-an", "-vf", decode_filter(tl, clip),
           "-frames:v", str(n_frames), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    last = None
    got = 0
    try:
        while got < n_frames:
            buf = proc.stdout.read(size)
            if len(buf) < size:
                break
            last = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()
            got += 1
            yield last
    finally:
        proc.stdout.close()
        proc.kill()
        err = proc.stderr.read().decode(errors="replace").strip()
        proc.stderr.close()
        proc.wait()
    if got < n_frames:
        if last is None:
            raise RuntimeError(f"could not decode {clip['file']}: {err[-400:]}")
        tl.problem(f"clip {clip['id']} ran {n_frames - got} frame(s) short; last frame repeated")
        for _ in range(n_frames - got):
            yield last.copy()


class Encoder:
    """Raw RGB frames in, H.264/yuv420p (Rec.709, limited range) out."""

    def __init__(self, path: Path, W: int, H: int, fps: float, crf: int = 17, preset: str = "medium"):
        self.log = Path(str(path) + ".log")
        cmd = [ffutil.ffmpeg_exe(), "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{W}x{H}", "-r", f"{fps}", "-i", "-",
               "-vf", "scale=in_range=full:out_range=tv:out_color_matrix=bt709:flags=lanczos+accurate_rnd,format=yuv420p",
               "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-profile:v", "high", "-level", "4.2",
               "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
               "-movflags", "+faststart", "-an", str(path)]
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=open(self.log, "wb"))

    def write(self, frame: np.ndarray) -> None:
        self.proc.stdin.write(frame.data)

    def close(self) -> None:
        self.proc.stdin.close()
        rc = self.proc.wait()
        if rc:
            raise RuntimeError(f"encoder failed ({rc}): {self.log.read_text()[-600:]}")
        self.log.unlink(missing_ok=True)
