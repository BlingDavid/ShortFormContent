"""Audio: lay voice, SFX, music and room tone on the timeline, duck, master."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import numpy as np

import dsp
import ffutil
from dsp import SR
from timeline import Timeline


def load_audio(path) -> np.ndarray:
    """Decode any audio file to mono float32 at 48 kHz."""
    r = subprocess.run([ffutil.ffmpeg_exe(), "-v", "error", "-i", str(path), "-vn", "-ac", "1",
                        "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, dtype="<f4").astype(np.float32)


def pan_gains(p: float) -> tuple[float, float]:
    a = (p + 1) * np.pi / 4
    return float(np.cos(a)), float(np.sin(a))


def declick(x: np.ndarray, ms: float = 3.0) -> np.ndarray:
    n = min(len(x) // 2, int(ms / 1000 * SR))
    if n > 0:
        x = x.copy()
        x[:n] *= np.linspace(0, 1, n)
        x[-n:] *= np.linspace(1, 0, n)
    return x


def keyframe_curve(points: list[tuple[float, float]], n: int) -> np.ndarray:
    """Piecewise-linear-in-dB gain curve over n samples from (time, dB) points."""
    pts = sorted(points)
    t = np.arange(n) / SR
    d = np.interp(t, [p[0] for p in pts], [p[1] for p in pts])
    return 10 ** (d / 20)


def duck_curve(n: int, windows: list[tuple[float, float]], depth_db: float,
               attack: float = 0.06, release: float = 0.35, pad: float = 0.05) -> np.ndarray:
    """Music gain that dips by `depth_db` (negative) while any voice window is active."""
    cs = 200
    m = int(n / SR * cs) + 2
    act = np.zeros(m)
    for a, b in windows:
        act[max(0, int((a - pad) * cs)): int((b + pad) * cs) + 1] = 1
    env = np.zeros(m)
    cur = 0.0
    ka, kr = 1 - np.exp(-1 / (attack * cs)), 1 - np.exp(-1 / (release * cs))
    for i in range(m):
        cur += (ka if act[i] > cur else kr) * (act[i] - cur)
        env[i] = cur
    up = np.interp(np.arange(n) / SR * cs, np.arange(m), env)
    return 10 ** (depth_db * up / 20)


class Mixer:
    def __init__(self, tl: Timeline):
        self.tl = tl
        self.n = int(round(tl.duration * SR))
        self.L = np.zeros(self.n, np.float32)
        self.R = np.zeros(self.n, np.float32)

    def place(self, x: np.ndarray, at: float, gain_db: float = 0.0, pan: float = 0.0) -> None:
        gl, gr = pan_gains(pan)
        g = dsp.db(gain_db)
        dsp.add(self.L, x, at, g * gl)
        dsp.add(self.R, x, at, g * gr)

    def build(self) -> np.ndarray:
        tl, a = self.tl, self.tl.spec.get("audio", {})
        windows = []
        for v in a.get("vo", []):
            x = load_audio(tl.path(v["file"])) if tl.path(v["file"]).exists() else np.zeros(0, np.float32)
            if "trim" in v:
                x = x[int(v["trim"][0] * SR): int(v["trim"][1] * SR)]
            self.place(declick(x), v["_start"], v.get("gain_db", 0.0), v.get("pan", 0.0))
            windows.append((v["_start"], v["_end"]))
        for s in a.get("sfx", []):
            p = tl.sfx_path(s["file"])
            if not p.exists():
                continue
            x = load_audio(p)
            if "dur" in s:
                x = x[: int(s["dur"] * SR)]
            self.place(declick(x), tl.t(s["start"]), s.get("gain_db", 0.0), s.get("pan", 0.0))
        for m in a.get("music", []):
            self._music(m, windows)
        rt = a.get("room_tone")
        if rt:
            p = tl.sfx_path(rt.get("file", "room_tone"))
            if p.exists():
                x = load_audio(p)
                x = np.tile(x, self.n // len(x) + 1)[: self.n]
                fi, fo = rt.get("fade_in", 0.3), rt.get("fade_out", 0.0)
                x = dsp.fade(x.astype(np.float64), fi, fo).astype(np.float32)
                self.place(x, 0.0, rt.get("gain_db", 0.0))
        return np.stack([self.L, self.R], axis=1)

    def _music(self, m: dict, windows: list) -> None:
        tl = self.tl
        p = tl.music_path(m["file"])
        if not p.exists():
            return
        start = tl.t(m.get("start", 0))
        stop = tl.t(m["stop_at"]) if "stop_at" in m else tl.duration
        n = max(0, int(round((stop - start) * SR)))
        x = load_audio(p)[int(m.get("in", 0) * SR):]
        if m.get("loop") and 0 < len(x) < n:
            x = np.tile(x, n // len(x) + 1)
        x = x[:n]
        x = np.pad(x, (0, n - len(x)))
        x = dsp.fade(x.astype(np.float64), m.get("fade_in", 0.05), m.get("fade_out", 0.4)).astype(np.float32)
        curve = np.ones(n)
        if "automation" in m:                                   # [[time_expr, dB], ...] on the timeline
            pts = [(tl.t(t) - start, g) for t, g in m["automation"]]
            curve = keyframe_curve(pts, n)
        if "duck_db" in m:
            full = duck_curve(self.n, windows, m["duck_db"], m.get("duck_attack", 0.06), m.get("duck_release", 0.35))
            i0 = int(round(start * SR))
            curve = curve * full[i0:i0 + n]
        self.place(x * curve.astype(np.float32), start, m.get("gain_db", 0.0), m.get("pan", 0.0))


# --------------------------------------------------------------------------- master

def _pipe_wav(stereo: np.ndarray, args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([ffutil.ffmpeg_exe(), "-hide_banner", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2",
                           "-i", "-", *args], input=stereo.astype("<f4").tobytes(), capture_output=True)


def measure_loudness(stereo: np.ndarray) -> dict:
    r = _pipe_wav(stereo, ["-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr.decode(errors="replace"), re.S)
    return json.loads(m.group(0)) if m else {}


def master(stereo: np.ndarray, out_wav: Path, target_lufs: float = -14.0, tp_db: float = -1.5) -> dict:
    """Gain-only loudness match to target, then a true-peak limiter. No compression pumping."""
    stereo = np.clip(stereo, -8, 8)
    stats = measure_loudness(stereo)
    gain = 0.0
    try:
        li = float(stats["input_i"])
        if np.isfinite(li):
            gain = target_lufs - li
    except (KeyError, ValueError):
        pass
    lim = 10 ** (tp_db / 20)
    r = _pipe_wav(stereo, ["-af", f"volume={gain:.2f}dB,alimiter=limit={lim:.4f}:attack=3:release=40:level=disabled",
                           "-ar", str(SR), "-c:a", "pcm_s16le", str(out_wav)])
    if r.returncode:
        raise RuntimeError(r.stderr.decode(errors="replace")[-800:])
    return {"pre_master_lufs": stats.get("input_i"), "applied_gain_db": round(gain, 2)}
