"""Spec loading and time resolution.

Times in a spec may be plain numbers (seconds on the finished timeline) or anchor
expressions such as "c3.start+0.2", "v4.end-0.05" or "end-1.5", so that overlays,
SFX and music follow the real length of each clip and voice line rather than
hard-coded seconds.

Anchors: <clip>.start / <clip>.end, <vo>.start / <vo>.end, start, end.
Voice lines are laid out in listed order, so a line may refer to any clip or any
earlier voice line.
"""
from __future__ import annotations

import json
import re
import statistics
from pathlib import Path

import ffutil

EXPR = re.compile(r"^\s*([A-Za-z_][\w.]*)\s*(?:([+-])\s*(\d+(?:\.\d+)?))?\s*$")   # ids: letters/digits/_ only
ROOT = Path(__file__).resolve().parents[1]


def load_spec(path: str | Path) -> dict:
    return json.loads(Path(path).read_text())


class Timeline:
    def __init__(self, spec: dict, root: Path = ROOT, allow_missing: bool = False):
        self.spec = spec
        self.root = Path(root)
        self.allow_missing = allow_missing
        self.problems: list[str] = []
        self.anchors: dict[str, float] = {"start": 0.0}
        self.format = {"width": 1080, "height": 1920, **spec.get("format", {})}
        self._lay_out_clips()
        self._lay_out_vo()

    # ------------------------------------------------------------------ paths
    def path(self, p: str) -> Path:
        q = Path(p)
        return q if q.is_absolute() else self.root / q

    def sfx_path(self, name: str) -> Path:
        return self.path(name) if "/" in name or name.endswith(".wav") else self.root / "audio" / "sfx" / f"{name}.wav"

    def music_path(self, name: str) -> Path:
        return self.path(name) if "/" in name or name.endswith(".wav") else self.root / "audio" / "music" / f"{name}.wav"

    def problem(self, msg: str) -> None:
        self.problems.append(msg)

    # ------------------------------------------------------------------- time
    def t(self, expr) -> float:
        if isinstance(expr, (int, float)):
            return float(expr)
        try:
            return float(expr)
        except (TypeError, ValueError):
            pass
        m = EXPR.match(expr)
        if not m:
            raise ValueError(f"bad time expression {expr!r}")
        name, sign, off = m.groups()
        if name not in self.anchors:
            raise KeyError(f"unknown anchor {name!r} in {expr!r}; known: {sorted(self.anchors)}")
        v = self.anchors[name]
        if sign:
            v += float(off) if sign == "+" else -float(off)
        return v

    # ------------------------------------------------------------------ layout
    def _lay_out_clips(self) -> None:
        clips = self.spec.get("clips", [])
        fps = self.format.get("fps", "auto")
        if fps == "auto":
            seen = [ffutil.probe(self.path(c["file"]))["fps"] for c in clips if self.path(c["file"]).exists()]
            seen = [round(f) for f in seen if f]
            fps = statistics.median_low(seen) if seen else 24
            fps = 30 if fps in (29, 30, 31) else 24 if fps in (23, 24, 25) else fps
        self.fps = float(fps)
        t = 0.0
        for c in clips:
            f = self.path(c["file"])
            if f.exists():
                src = ffutil.probe(f)["duration"] or 0.0
            else:
                self.problem(f"missing clip: {c['file']}")
                src = float(c.get("out", c.get("est_source", 4.0)))
            c_in = float(c.get("in", 0.0))
            c_out = float(c.get("out", src))
            speed = float(c.get("speed", 1.0))
            hold = float(c.get("hold_end", 0.0))
            dur = (c_out - c_in) / speed + hold
            if dur <= 0:
                raise ValueError(f"clip {c['id']} has non-positive duration")
            c.update(_in=c_in, _out=c_out, _speed=speed, _hold=hold, _start=t, _end=t + dur, _src=src)
            self.anchors[f"{c['id']}.start"] = t
            self.anchors[f"{c['id']}.end"] = t + dur
            t += dur
        self.duration = t
        self.anchors["end"] = t

    def _lay_out_vo(self) -> None:
        for v in self.spec.get("audio", {}).get("vo", []):
            start = self.t(v["start"])
            f = self.path(v["file"])
            if f.exists():
                dur = ffutil.probe(f)["duration"] or 0.0
            else:
                self.problem(f"missing voice line: {v['file']}")
                dur = float(v.get("est", 1.0))
            v.update(_start=start, _end=start + dur)
            self.anchors[f"{v['id']}.start"] = start
            self.anchors[f"{v['id']}.end"] = start + dur

    # ------------------------------------------------------------------ frames
    def frame_span(self, clip: dict) -> tuple[int, int]:
        """Frame index range [a, b) a clip occupies (cumulative rounding => no drift)."""
        return round(clip["_start"] * self.fps), round(clip["_end"] * self.fps)

    @property
    def total_frames(self) -> int:
        return round(self.duration * self.fps)

    def missing_assets(self) -> list[str]:
        """Every referenced audio file that does not exist yet."""
        a = self.spec.get("audio", {})
        miss = list(self.problems)
        for s in a.get("sfx", []):
            if not self.sfx_path(s["file"]).exists():
                miss.append(f"missing sfx: {s['file']}")
        for m in a.get("music", []):
            if not self.music_path(m["file"]).exists():
                miss.append(f"missing music: {m['file']}")
        rt = a.get("room_tone")
        if rt and not self.sfx_path(rt.get("file", "room_tone")).exists():
            miss.append("missing room_tone")
        return sorted(set(miss))
