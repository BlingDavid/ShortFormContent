#!/usr/bin/env python3
"""Render 3D (Blender Cycles) clips for a spec into raw/<id>/cN.mp4, in sync with the timeline.

    PYTHONPATH=<bpy>:<pillow> python production/anim3d/render3d.py 01-heating-fee [--clip c1]
    ... --still c4=1.2 --stills-dir DIR      # preview frames (source seconds)
    ... --res 720x1280 --samples 6

Frames before the clip's `in` point are never shown, so they are copies of the first
rendered frame. Output files keep source timing so the spec's in/out points still apply.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "tools"))

import bpy  # noqa: E402
import numpy as np  # noqa: E402

import ffutil  # noqa: E402
import lib3d as L  # noqa: E402
import mix  # noqa: E402
import scenes3d  # noqa: E402
from timeline import ROOT, Timeline, load_spec  # noqa: E402


def talk_fn(tl):
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
                return float(np.clip(e[int((t - s) / dt)] * 1.2, 0, 1)) ** 0.8
        return 0.0
    return talk


def setup(video, shot, res, samples):
    spec = load_spec(ROOT / "specs" / f"{video}.json")
    tl = Timeline(spec, ROOT, allow_missing=True)
    L.reset()
    import props3d
    props3d._M.clear()
    w, h = res
    L.setup_render(w, h, samples)
    os.environ.setdefault("SIGN_DIR", tempfile.gettempdir())
    sc = scenes3d.SCENES[video](tl, talk_fn(tl))
    sc.build(shot)
    clip = next(c for c in spec["clips"] if c["id"] == shot)
    return spec, tl, sc, clip


def render_clip(video, shot, res=(720, 1280), samples=6, fps=24, log=print):
    spec, tl, sc, clip = setup(video, shot, res, samples)
    out = tl.path(clip["file"])
    out.parent.mkdir(parents=True, exist_ok=True)
    n = int(np.ceil((clip["_out"] + 0.05) * fps))
    first = int(np.floor(clip["_in"] * fps))
    tmp = Path(tempfile.mkdtemp(prefix=f"r3d_{video}_{shot}_"))
    scene = bpy.context.scene
    t0 = time.time()
    for k in range(first, n):
        t = clip["_start"] + (k / fps - clip["_in"])
        sc.frame(shot, t)
        scene.render.filepath = str(tmp / f"f{k:05d}.png")
        bpy.ops.render.render(write_still=True)
        done = k - first + 1
        if done % 10 == 0 or k == n - 1:
            el = time.time() - t0
            log(f"{video} {shot}: {done}/{n - first} frames, {el / done:.1f}s/frame, eta {el / done * (n - first - done) / 60:.1f} min")
    for k in range(first):
        shutil.copy(tmp / f"f{first:05d}.png", tmp / f"f{k:05d}.png")
    ffutil.run(["-framerate", str(fps), "-i", str(tmp / "f%05d.png"), "-vf",
                "scale=in_range=full:out_range=tv:out_color_matrix=bt709,format=yuv420p", "-c:v", "libx264", "-preset",
                "medium", "-crf", "15", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                "-color_range", "tv", "-movflags", "+faststart", str(out)])
    shutil.rmtree(tmp, ignore_errors=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--clip", action="append")
    ap.add_argument("--still", action="append", help="clip=source_seconds")
    ap.add_argument("--stills-dir", default=".")
    ap.add_argument("--res", default="720x1280")
    ap.add_argument("--samples", type=int, default=6)
    a = ap.parse_args()
    res = tuple(int(v) for v in a.res.split("x"))
    if a.still:
        by_clip = {}
        for st in a.still:
            cid, sec = st.split("=")
            by_clip.setdefault(cid, []).append(sec)
        for cid, secs in by_clip.items():
            spec, tl, sc, clip = setup(a.video, cid, res, a.samples)
            for sec in secs:
                t = clip["_start"] + (float(sec) - clip["_in"])
                sc.frame(cid, t)
                p = Path(a.stills_dir) / f"{a.video}_{cid}_{sec}.png"
                bpy.context.scene.render.filepath = str(p)
                bpy.ops.render.render(write_still=True)
                print("STILL", p, flush=True)
        return
    spec = load_spec(ROOT / "specs" / f"{a.video}.json")
    for c in spec["clips"]:
        if a.clip and c["id"] not in a.clip:
            continue
        out = render_clip(a.video, c["id"], res, a.samples, log=lambda m: print(m, flush=True))
        print("CLIP", out, flush=True)


if __name__ == "__main__":
    main()
