#!/usr/bin/env python3
"""Render code-animated clips for a spec into raw/<id>/cN.mp4, in sync with the timeline.

    python production/anim/render.py 01-heating-fee                # all clips
    python production/anim/render.py 01-heating-fee --still c4=8.2 # preview stills to scratch
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "tools"))

import ffutil  # noqa: E402
import mix  # noqa: E402
import scenes  # noqa: E402
from timeline import ROOT, Timeline, load_spec  # noqa: E402

SCENES = {"01-heating-fee": "HeatingFee", "02-phone-call": "PhoneCall", "03-one-more-video": "OneMoreVideo",
          "04-social-battery-inspection": "SocialBattery", "05-comfort-hoard": "ComfortHoard"}


def talk_fn(tl):
    """talk(who, t) -> mouth openness 0..1 from the recorded voice lines' loudness."""
    env = []
    for v in tl.spec.get("audio", {}).get("vo", []):
        p = tl.path(v["file"])
        if not p.exists():
            continue
        x = mix.load_audio(p)
        hop = int(0.03 * 48000)
        e = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2)) for i in range(0, len(x) - hop, hop)])
        e = np.clip(e / (np.percentile(e, 90) + 1e-9), 0, 1)
        env.append((v["who"], v["_start"], hop / 48000, e))

    def talk(who, t):
        for w, s, dt, e in env:
            if w == who and s <= t < s + len(e) * dt:
                i = int((t - s) / dt)
                return float(np.clip(e[i] * 1.2, 0, 1)) ** 0.8
        return 0.0
    return talk


def make(video_id):
    spec = load_spec(ROOT / "specs" / f"{video_id}.json")
    tl = Timeline(spec, ROOT, allow_missing=True)
    return spec, tl, getattr(scenes, SCENES[video_id])(tl, talk_fn(tl))


def clip_time(tl, clip, s):
    """Global timeline time shown at source time s of a clip file."""
    return clip["_start"] + (s - clip["_in"])


def render_clip(video_id, clip_id, fps=24, out=None):
    spec, tl, sc = make(video_id)
    clip = next(c for c in spec["clips"] if c["id"] == clip_id)
    dur = clip["_out"] + 0.3
    out = Path(out or tl.path(clip["file"]))
    out.parent.mkdir(parents=True, exist_ok=True)
    n = int(round(dur * fps))
    cmd = [ffutil.ffmpeg_exe(), "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920",
           "-r", str(fps), "-i", "-", "-vf", "scale=in_range=full:out_range=tv:out_color_matrix=bt709,format=yuv420p",
           "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-colorspace", "bt709", "-color_primaries", "bt709",
           "-color_trc", "bt709", "-color_range", "tv", "-movflags", "+faststart", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k in range(n):
        img = sc.frame(clip_id, clip_time(tl, clip, k / fps))
        p.stdin.write(np.asarray(img.convert("RGB"), np.uint8).tobytes())
    p.stdin.close()
    if p.wait():
        raise RuntimeError("encode failed")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--clip")
    ap.add_argument("--still", action="append", help="clipid=source_seconds; writes PNG to --stills-dir")
    ap.add_argument("--stills-dir", default=".")
    a = ap.parse_args()
    spec, tl, sc = make(a.video)
    if a.still:
        for st in a.still:
            cid, sec = st.split("=")
            clip = next(c for c in spec["clips"] if c["id"] == cid)
            img = sc.frame(cid, clip_time(tl, clip, float(sec)))
            p = Path(a.stills_dir) / f"{a.video}_{cid}_{sec}.png"
            img.save(p)
            print(p)
        return
    for c in spec["clips"]:
        if a.clip and c["id"] != a.clip:
            continue
        print("rendering", c["id"], "->", render_clip(a.video, c["id"]))


if __name__ == "__main__":
    main()
