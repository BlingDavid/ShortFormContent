#!/usr/bin/env python3
"""Synthesize the original sound-effect library (no samples, nothing to license).

Deterministic: the same seed produces the same files.

    python production/tools/make_sfx.py            # writes production/audio/sfx/*.wav
    python production/tools/make_sfx.py --report   # also writes a spectrogram sheet
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

import dsp
from dsp import SR, add, fft_filter, tt

ROOT = Path(__file__).resolve().parents[1]


def noise(rng, n: int) -> np.ndarray:
    return rng.standard_normal(n)


def ring(rng, freqs, amps, taus, dur: float) -> np.ndarray:
    """Sum of exponentially decaying sines (struck glass / ceramic / metal)."""
    t = tt(dur)
    y = np.zeros_like(t)
    for f, a, tau in zip(freqs, amps, taus):
        y += a * np.sin(2 * np.pi * f * t + rng.uniform(0, 2 * np.pi)) * np.exp(-t / tau)
    return y * np.minimum(1, t / 0.0008)


def click(rng, dur: float, lo: float, hi: float, tau: float) -> np.ndarray:
    n = int(dur * SR)
    tn = np.arange(n) / SR
    return fft_filter(noise(rng, n), lo, hi) * np.exp(-tn / tau)


# --------------------------------------------------------------------------- sounds

def glass_set_down(rng):
    y = np.zeros(int(0.7 * SR))

    def contact(at, amp):
        tn = tt(0.012)
        thump = np.sin(2 * np.pi * 240 * tn) * np.exp(-tn / 0.010) * 0.6
        add(y, click(rng, 0.012, 900, 7000, 0.003) + thump, at, amp)

    def glass(at, amp):
        r = ring(rng, [2210, 3560, 5120, 6890, 9100], [1, .7, .45, .3, .15],
                 [.16, .11, .07, .05, .03], 0.5)
        add(y, r, at, amp)

    contact(0.02, 1.0); glass(0.02, 0.35)
    contact(0.095, 0.35); glass(0.095, 0.10)          # glass settles: second tiny tick
    return dsp.peak_norm(y, -7)


def register_ding(rng):
    """Tiny shop-bell 'ding' with a soft mechanical clack in front of it."""
    t = tt(0.9)
    f0 = 2600
    y = sum(a * np.sin(2 * np.pi * f0 * r * t) * np.exp(-t / tau)
            for r, a, tau in zip([1, 2.02, 2.76, 4.1, 5.4], [1, .45, .5, .22, .1],
                                 [.30, .18, .16, .08, .05]))
    y *= np.minimum(1, t / 0.001)
    add(y, click(rng, 0.006, 1200, 6000, 0.0018), 0.0, 0.7)
    return dsp.peak_norm(y, -10)


def kiss_soft(rng):
    y = np.zeros(int(0.35 * SR))
    n = int(0.09 * SR)
    tn = np.arange(n) / SR
    press = fft_filter(noise(rng, n), None, 900) * np.sin(np.pi * tn / 0.09) ** 2 * 0.18
    add(y, press, 0.02)
    n = int(0.14 * SR)
    tn = np.arange(n) / SR
    f = 900 * np.exp(-tn / 0.045) + 280
    chirp = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tn / 0.03) * np.minimum(1, tn / 0.003)
    wet = fft_filter(noise(rng, n), 1200, 5200) * np.exp(-tn / 0.012) * 0.8
    pop = np.zeros(n)
    m = int(0.002 * SR)
    pop[:m] = fft_filter(noise(rng, m), 1500, 5000)
    add(y, chirp * 0.9 + wet + pop * 0.5, 0.10)
    return dsp.peak_norm(fft_filter(y, 120, 6500), -13)


def cushion_squeak(rng):
    y = np.zeros(int(0.5 * SR))
    n = int(0.25 * SR)
    tn = np.arange(n) / SR
    fw = fft_filter(noise(rng, n), None, 700) * np.minimum(1, tn / 0.05) * np.exp(-tn / 0.09)
    add(y, fw * 0.8, 0.02)
    n = int(0.16 * SR)
    tn = np.arange(n) / SR
    f = (1450 + 500 * np.sin(np.pi * tn / 0.16)) * (1 + 0.02 * np.sin(2 * np.pi * 38 * tn))
    sq = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.65 + 0.35 * np.sin(2 * np.pi * 75 * tn))
    sq *= np.sin(np.pi * tn / 0.16) ** 0.7
    add(y, fft_filter(sq, None, 3500), 0.06, 0.28)
    return dsp.peak_norm(y, -12)


def phone_ring(rng):
    """One ring burst of an original two-tone digital ringer (E6/A6 quad-chirp)."""
    y = np.zeros(int(0.75 * SR))
    for i, f in enumerate([1319, 1760, 1319, 1760]):
        n = int(0.075 * SR)
        tn = np.arange(n) / SR
        env = np.minimum(1, tn / 0.004) * np.minimum(1, (0.075 - tn) / 0.006)
        add(y, (np.sin(2 * np.pi * f * tn) + 0.25 * np.sin(4 * np.pi * f * tn)) * env, i * 0.085)
    tail = fft_filter(y, 600, 6000) * 0.0
    return dsp.peak_norm(y + tail, -8)


def mug_clink(rng):
    y = np.zeros(int(0.5 * SR))
    tn = tt(0.02)
    thump = np.sin(2 * np.pi * 300 * tn) * np.exp(-tn / 0.015)
    add(y, thump, 0.0, 0.5)
    add(y, click(rng, 0.01, 800, 5000, 0.003), 0.0)
    add(y, ring(rng, [1510, 2790, 4300, 5800], [1, .55, .3, .12], [.09, .06, .035, .02], 0.45), 0.0)
    return dsp.peak_norm(y, -14)


def phone_slide(rng):
    n = int(0.5 * SR)
    tn = np.arange(n) / SR
    env = np.minimum(1, tn / 0.05) * np.exp(-np.maximum(0, tn - 0.10) / 0.11)
    sh = fft_filter(noise(rng, n), 600, 5000, 2) * 0.6
    rub = fft_filter(noise(rng, n), 80, 350) * np.exp(-tn / 0.2) * 0.5
    y = (sh + rub) * env
    add(y, click(rng, 0.008, 1000, 4500, 0.002), 0.30, 0.25)     # comes to rest
    return dsp.peak_norm(y, -9)


def phone_set_tap(rng):
    y = np.zeros(int(0.3 * SR))
    tn = tt(0.15)
    body = np.sin(2 * np.pi * 165 * tn) * np.exp(-tn / 0.04)
    add(y, body, 0.0)
    add(y, click(rng, 0.012, 1800, 6000, 0.003), 0.0, 0.8)
    add(y, ring(rng, [1250, 2400], [.25, .12], [.05, .03], 0.15), 0.0)
    return dsp.peak_norm(y, -6)


def scroll_swipes(rng):
    y = np.zeros(int(2.3 * SR))
    for at in [0.10, 0.42, 0.95, 1.20, 1.62, 2.02]:
        dur = rng.uniform(0.07, 0.13)
        n = int(dur * SR)
        tn = np.arange(n) / SR
        sw = fft_filter(noise(rng, n), 2200, 6500, 2) * np.sin(np.pi * tn / dur) ** 2
        add(y, sw, at, 0.5)
        add(y, click(rng, 0.006, 1500, 4500, 0.002), at, 0.25)
    return dsp.peak_norm(y, -22)


def door_handle_rattle(rng):
    y = np.zeros(int(1.1 * SR))
    at = 0.02
    for i in range(6):
        amp = rng.uniform(0.6, 1.0)
        add(y, click(rng, 0.02, 600, 6000, 0.004), at, amp)
        add(y, ring(rng, [1100, 2870, 4200], [.6, .4, .2], [.04, .03, .02], 0.15), at, amp * 0.7)
        at += rng.uniform(0.08, 0.14)
    tn = tt(0.2)                                            # latch refuses to give: dull clunk
    add(y, np.sin(2 * np.pi * 210 * tn) * np.exp(-tn / 0.05), at + 0.05, 0.9)
    add(y, click(rng, 0.01, 500, 4000, 0.003), at + 0.05, 0.9)
    return dsp.peak_norm(y, -9)


def pencil_scratch(rng):
    n = int(0.9 * SR)
    tn = np.arange(n) / SR
    strokes = np.abs(np.sin(2 * np.pi * (9 + 2 * np.sin(2 * np.pi * 1.3 * tn)) * tn)) ** 1.5
    strokes *= 0.5 + 0.5 * rng.random(n // 2000 + 2)[np.minimum(tn * SR // 2000, n // 2000 + 1).astype(int)]
    sc = fft_filter(noise(rng, n), 2500, 8000, 2) * strokes
    env = np.minimum(1, tn / 0.03) * np.minimum(1, (0.9 - tn) / 0.08)
    return dsp.peak_norm(sc * env, -14)


def stamp_thud(rng):
    y = np.zeros(int(0.5 * SR))
    add(y, click(rng, 0.03, 300, 2500, 0.008), 0.0, 0.5)             # ink-pad squish
    tn = tt(0.35)
    f = 85 + 60 * np.exp(-tn / 0.03)
    thump = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tn / 0.09)
    add(y, thump, 0.02)
    add(y, click(rng, 0.008, 1500, 6000, 0.002), 0.02, 0.6)          # rubber-on-paper crack
    add(y, ring(rng, [1600], [.15], [.03], 0.1), 0.02)
    return dsp.peak_norm(y, -3)


def blanket_drag(rng):
    n = int(1.3 * SR)
    tn = np.arange(n) / SR
    nz = fft_filter(noise(rng, n), 120, 1800, 2)
    env = np.minimum(1, tn / 0.15) * np.minimum(1, (1.3 - tn) / 0.25)
    stutter = 0.7 + 0.3 * np.sin(2 * np.pi * 3.5 * tn) ** 2
    return dsp.peak_norm(nz * env * stutter, -14)


def slipper_drag(rng):
    """Short strained drag: three heave-and-slide pulses."""
    y = np.zeros(int(1.4 * SR))
    for at in [0.05, 0.50, 0.95]:
        n = int(0.32 * SR)
        tn = np.arange(n) / SR
        nz = fft_filter(noise(rng, n), 150, 2200, 2)
        add(y, nz * np.sin(np.pi * tn / 0.32) ** 1.5, at)
    return dsp.peak_norm(y, -14)


def _grunt(rng, dur, f0, f0_end, formants, breath):
    n = int(dur * SR)
    tn = np.arange(n) / SR
    f = np.linspace(f0, f0_end, n) * (1 + 0.015 * np.sin(2 * np.pi * 9 * tn))
    ph = np.cumsum(f) / SR
    src = (2 * (ph % 1.0) - 1)                                      # sawtooth glottal source
    src = 0.85 * src + 0.15 * noise(rng, n) * breath
    y = sum(a * dsp.resonator(src, ff, bw) for ff, bw, a in formants)
    env = np.minimum(1, tn / 0.02) * np.exp(-np.maximum(0, tn - dur * 0.45) / (dur * 0.25))
    puff = fft_filter(noise(rng, n), 1000, 5000) * np.exp(-((tn - dur * 0.9) / 0.03) ** 2) * 0.25
    return y * env + puff


def effort_grunt(rng, variant: int):
    """Tiny 'hnnf' effort grunt (placeholder; swap for a performed take if preferred)."""
    setups = [(0.20, 330, 290), (0.26, 300, 360), (0.32, 280, 250)]
    dur, a, b = setups[variant]
    y = _grunt(rng, dur, a, b, [(620, 90, 1.0), (1150, 110, 0.6), (2450, 160, 0.25)], 0.5)
    return dsp.peak_norm(fft_filter(y, 150, 6000), -9)


def cloth_plop(rng):
    """Soft slipper landing on a pile of cloth."""
    n = int(0.4 * SR)
    tn = np.arange(n) / SR
    body = np.sin(2 * np.pi * 100 * tn) * np.exp(-tn / 0.06)
    puff = fft_filter(noise(rng, n), 200, 2200, 2) * np.exp(-tn / 0.09)
    return dsp.peak_norm(fft_filter(body * 0.7 + puff * 0.8, 60, 3000), -10)


def heavy_breath(rng):
    n = int(0.7 * SR)
    tn = np.arange(n) / SR
    y = fft_filter(noise(rng, n), 400, 3500, 2) * np.sin(np.pi * tn / 0.7) ** 2
    return dsp.peak_norm(y, -22)


def room_tone(rng):
    """Quiet living-room air, loop-safe (20 s with equal-power seam crossfade)."""
    n = int(22 * SR)
    y = fft_filter(noise(rng, n), 40, 900, 2)
    y += 0.4 * fft_filter(noise(rng, n), 30, 120, 2)
    xf = int(2 * SR)
    fade_in = np.sin(np.linspace(0, np.pi / 2, xf))
    fade_out = np.cos(np.linspace(0, np.pi / 2, xf))
    body = y[: n - xf].copy()
    body[:xf] = body[:xf] * fade_in + y[n - xf:] * fade_out
    return dsp.peak_norm(body, -40)


LIBRARY = {
    "glass_set_down": glass_set_down,
    "register_ding": register_ding,
    "kiss_soft": kiss_soft,
    "cushion_squeak": cushion_squeak,
    "phone_ring": phone_ring,
    "mug_clink": mug_clink,
    "phone_slide": phone_slide,
    "phone_set_tap": phone_set_tap,
    "scroll_swipes": scroll_swipes,
    "door_handle_rattle": door_handle_rattle,
    "pencil_scratch": pencil_scratch,
    "stamp_thud": stamp_thud,
    "blanket_drag": blanket_drag,
    "slipper_drag": slipper_drag,
    "cloth_plop": cloth_plop,
    "heavy_breath": heavy_breath,
    "room_tone": room_tone,
}


def build(out_dir: Path, seed: int = 7) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    report = {}
    made = {}
    for i, (name, fn) in enumerate(LIBRARY.items()):
        made[name] = fn(np.random.default_rng(seed + i))
    for v in range(3):
        made[f"effort_grunt_{v + 1}"] = effort_grunt(np.random.default_rng(seed + 100 + v), v)
    for name, y in made.items():
        y = y.astype(np.float64)
        assert np.all(np.isfinite(y)), name
        dsp.write_wav(out_dir / f"{name}.wav", y)
        rms = float(np.sqrt(np.mean(y ** 2)))
        report[name] = {"seconds": round(len(y) / SR, 3),
                        "peak_dbfs": round(dsp.to_db(float(np.max(np.abs(y)))), 1),
                        "rms_dbfs": round(dsp.to_db(rms), 1)}
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "audio" / "sfx"))
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--report", action="store_true", help="write a spectrogram contact sheet")
    a = ap.parse_args()
    out = Path(a.out)
    rep = build(out, a.seed)
    (out / "manifest.json").write_text(json.dumps(rep, indent=2))
    for k, v in rep.items():
        print(f"{k:22s} {v['seconds']:5.2f}s  peak {v['peak_dbfs']:6.1f}  rms {v['rms_dbfs']:6.1f}")
    if a.report:
        from PIL import Image, ImageDraw
        names = list(rep)
        cols = 4
        rows = (len(names) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * 380, rows * 150), (20, 20, 24))
        d = ImageDraw.Draw(sheet)
        for i, n in enumerate(names):
            x = dsp.read_wav_mono(out / f"{n}.wav")
            sheet.paste(dsp.spectrogram_image(x, 360, 120).convert("RGB"), ((i % cols) * 380 + 10, (i // cols) * 150 + 24))
            d.text(((i % cols) * 380 + 10, (i // cols) * 150 + 6), f"{n}  {rep[n]['seconds']}s", fill=(230, 230, 230))
        sheet.save(out.parent / "sfx_spectrograms.png")
        print("wrote", out.parent / "sfx_spectrograms.png")


if __name__ == "__main__":
    main()
