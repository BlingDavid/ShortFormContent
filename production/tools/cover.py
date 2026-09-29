"""Cover frames: a real frame from the footage (or a supplied still) plus one line of type."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

import overlays as ov
from timeline import Timeline
from video import read_clip_frames


def _fit(img: Image.Image, W: int, H: int, focus=(0.5, 0.5)) -> np.ndarray:
    s = max(W / img.width, H / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    x = round((img.width - W) * focus[0])
    y = round((img.height - H) * focus[1])
    return np.asarray(img.crop((x, y, x + W, y + H)).convert("RGB")).copy()


def make_cover(tl: Timeline, out_dir: Path) -> dict | None:
    c = tl.spec.get("cover")
    if not c:
        return None
    W, H = tl.format["width"], tl.format["height"]
    if "image" in c and tl.path(c["image"]).exists():
        frame = _fit(Image.open(tl.path(c["image"])), W, H, c.get("focus", (0.5, 0.5)))
    elif "clip" in c:
        clip = next(x for x in tl.spec["clips"] if x["id"] == c["clip"])
        if not tl.path(clip["file"]).exists():
            return {"skipped": f"source clip {clip['file']} not generated yet"}
        frame = next(read_clip_frames(tl, clip, 1, source_start=float(c.get("at", clip["_in"]))))
    else:
        return {"skipped": "cover has no image or clip"}

    warnings = []
    bbox = None
    for oid in c.get("overlays", []):                         # e.g. lettering that belongs to a physical sign
        spec = next(o for o in tl.spec.get("overlays", []) if o["id"] == oid)
        o = ov.Overlay(spec, 0, 1, tl.spec.get("characters"))
        o.anim = "none"
        ov.blend(frame, *o.at(0.5))
    if c.get("text"):                                         # some covers are the bare frame, by design
        o = ov.Overlay({"kind": "text", "style": "cover", "text": c["text"], "pos": [540, c.get("y", 470)]}, 0, 1)
        o.anim = "none"
        avoid = c.get("avoid")                                # [x0, y0, x1, y1] the type must not touch (e.g. the face)
        x0, y0, x1, y1 = bbox = o.bbox()
        if avoid and not (x1 < avoid[0] or x0 > avoid[2] or y1 < avoid[1] or y0 > avoid[3]):
            warnings.append(f"cover text {bbox} overlaps protected area {avoid}; move `y` or shrink the text")
        if y0 < 270:
            warnings.append("cover text starts above y=270 and would be cropped by 3:4 profile grids")
        ov.blend(frame, *o.at(0.5))
    out_dir.mkdir(parents=True, exist_ok=True)
    img = Image.fromarray(frame)
    img.save(out_dir / "cover.png")
    img.convert("RGB").save(out_dir / "cover.jpg", quality=93)
    top = (H - round(W * 4 / 3)) // 2
    img.crop((0, top, W, top + round(W * 4 / 3))).save(out_dir / "cover_grid_check.png")   # what a 3:4 grid tile shows
    return {"files": ["cover.png", "cover.jpg", "cover_grid_check.png"], "warnings": warnings, "text_bbox": bbox}
