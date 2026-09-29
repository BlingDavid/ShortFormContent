#!/usr/bin/env python3
"""Original music, synthesized from scratch (nothing sampled, nothing to license).

    python production/tools/make_music.py     # writes production/audio/music/*.wav

heroic_flourish  Video 2: brass-ish fanfare that the edit cuts dead on the first phone ring
lullaby_bed      Video 3: music-box bedtime tune (the edit drops it before Pip's last line)
warm_bed         Video 5: soft plucked chords (the edit lets it fall away for the last line)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

import dsp
from dsp import SR, add, fft_filter, midi_hz, tt

ROOT = Path(__file__).resolve().parents[1]


def music_box(freq, dur, vel=1.0):
    t = tt(dur)
    y = np.zeros_like(t)
    for r, a, tau in zip([1, 2.756, 5.404, 8.933], [1, .30, .10, .04], [1.4, .55, .22, .10]):
        if freq * r < 12000:
            y += a * np.sin(2 * np.pi * freq * r * t) * np.exp(-t / tau)
    return y * np.minimum(1, t / 0.002) * vel


def nylon_pluck(rng, freq, dur, vel=1.0):
    t = tt(dur)
    y = np.zeros_like(t)
    for n in range(1, 14):
        f = freq * n * np.sqrt(1 + 0.0004 * n * n)
        if f > 9000:
            break
        y += (1.0 / n ** 1.15) * (1.0 if n < 7 else 0.6) * np.sin(2 * np.pi * f * t) * np.exp(-t / (0.9 / (1 + 0.45 * n)))
    y *= np.minimum(1, t / 0.002) * np.minimum(1, np.maximum(0, dur - t) / 0.03)
    m = int(0.012 * SR)
    y[:m] += fft_filter(rng.standard_normal(m), 1500, 6000) * np.exp(-np.arange(m) / SR / 0.003) * 0.12
    return y * vel


def soft_pad(freqs, dur, vel=1.0):
    t = tt(dur)
    y = sum(np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t) for f in freqs) / len(freqs)
    return y * np.minimum(1, t / 0.6) * np.minimum(1, np.maximum(0, dur - t) / 0.8) * vel


def brass(freq, dur, vel=1.0, vibrato=0.0):
    t = tt(dur)
    y = np.zeros_like(t)
    for det in (0.996, 1.004):                                # two-voice ensemble
        vib = 1 + vibrato * np.sin(2 * np.pi * 5.5 * t) * np.minimum(1, t / 0.4)
        ph = 2 * np.pi * np.cumsum(freq * det * vib) / SR
        for n in range(1, 16):
            if freq * n > 10000:
                break
            y += (1 / n) * np.sin(n * ph + n * 0.3) * (1 - np.exp(-t / (0.015 + 0.012 * n)))
    return y * np.minimum(1, t / 0.03) * np.minimum(1, np.maximum(0, dur - t) / 0.06) * vel * 0.5


def timpani(rng, vel=1.0):
    t = tt(0.6)
    f = 70 + 45 * np.exp(-t / 0.05)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.22)
    n = int(0.03 * SR)
    y[:n] += fft_filter(rng.standard_normal(n), None, 800) * np.exp(-np.arange(n) / SR / 0.01) * 0.6
    return y * vel


def reverb(rng, x, rt60=1.3, wet=0.18):
    n = int(rt60 * SR)
    ir = fft_filter(rng.standard_normal(n), 200, 5000) * np.exp(-np.arange(n) / SR * 6.9 / rt60)
    ir /= np.sqrt(np.sum(ir ** 2))
    size = 1 << (len(x) + n).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[: len(x)]
    return x * (1 - wet) + y * wet * 1.2


# ---------------------------------------------------------------------------------

def heroic_flourish(rng):
    """Rising fanfare that keeps swelling; the edit cuts it dead on the first phone ring."""
    dur = 6.6
    y = np.zeros(int(dur * SR))
    add(y, timpani(rng, 0.9), 0.0)
    for i, n in enumerate([60, 64, 67]):
        add(y, brass(midi_hz(n), 0.16), i * 0.15)
    add(y, timpani(rng, 1.0), 0.45)
    length = dur - 0.45
    crescendo = 0.55 + 0.45 * np.minimum(1, tt(length) / 4.0)
    for n, v in [(72, 1.0), (67, .55), (64, .45), (60, .6)]:
        add(y, brass(midi_hz(n), length, v, vibrato=0.006) * crescendo, 0.45)
    t = 0.9                                                  # timpani roll, getting louder
    while t < dur - 0.3:
        add(y, timpani(rng, 0.25 + 0.45 * t / dur)[: int(0.25 * SR)], t)
        t += 0.11
    n = int(5.0 * SR)
    swell = fft_filter(rng.standard_normal(n), 4000, 12000) * np.sin(np.pi * np.linspace(0, 1, n) ** 1.4) * 0.05
    add(y, swell, 0.45)
    return dsp.peak_norm(reverb(rng, y, 0.9, 0.12), -6)


def lullaby_bed(rng):
    bpm = 76
    beat = 60 / bpm
    y = np.zeros(int((32 * beat + 3) * SR))
    melody = [(0, 72, 1.5), (1.5, 76, .5), (2, 79, 2), (4, 81, 1.5), (5.5, 79, .5), (6, 76, 2),
              (8, 74, 1.5), (9.5, 76, .5), (10, 79, 1), (11, 76, 1), (12, 72, 4),
              (16, 76, 1.5), (17.5, 79, .5), (18, 81, 2), (20, 79, 1.5), (21.5, 76, .5), (22, 74, 2),
              (24, 76, 1), (25, 74, 1), (26, 72, 2), (28, 72, 4)]
    for b, n, d in melody:
        add(y, music_box(midi_hz(n), 2.5), b * beat, 0.55)
    chords = [(48, 55, 64), (45, 52, 60), (41, 48, 57), (48, 55, 64)] * 2      # C, Am, F, C
    for bar, (r, f, o) in enumerate(chords):
        for k, note in enumerate([r, f, o, f, r + 12, f, o, f]):                  # gentle 8th arpeggio
            add(y, music_box(midi_hz(note), 1.6), (bar * 4 + k * 0.5) * beat, 0.16)
    return dsp.peak_norm(reverb(rng, y, 1.6, 0.22), -12)


def warm_bed(rng):
    bpm = 84
    beat = 60 / bpm
    y = np.zeros(int((32 * beat + 3) * SR))
    chords = [(48, 55, 59, 64), (45, 52, 55, 60), (41, 48, 52, 57), (43, 50, 59, 64)] * 2
    for bar, ch in enumerate(chords):
        for k, i in enumerate([0, 1, 2, 3, 2, 1, 3, 1]):
            add(y, nylon_pluck(rng, midi_hz(ch[i]), 1.4, 0.8 if k % 4 == 0 else 0.5), (bar * 4 + k * 0.5) * beat)
        add(y, soft_pad([midi_hz(n) for n in ch[1:]], 4 * beat + 0.8, 0.18), bar * 4 * beat)
    tops = [(2, 76), (6, 72), (10, 77), (14, 74), (18, 76), (22, 72), (26, 77), (30, 72)]
    for b, n in tops:
        add(y, nylon_pluck(rng, midi_hz(n), 1.8, 0.55), b * beat)
    return dsp.peak_norm(reverb(rng, y, 1.4, 0.2), -12)


def main():
    out = ROOT / "audio" / "music"
    out.mkdir(parents=True, exist_ok=True)
    for i, (name, fn) in enumerate([("heroic_flourish", heroic_flourish), ("lullaby_bed", lullaby_bed),
                                    ("warm_bed", warm_bed)]):
        x = fn(np.random.default_rng(11 + i))
        assert np.all(np.isfinite(x))
        dsp.write_wav(out / f"{name}.wav", x)
        print(f"{name:16s} {len(x) / SR:5.1f}s  peak {dsp.to_db(np.max(np.abs(x))):6.1f}  "
              f"rms {dsp.to_db(np.sqrt(np.mean(x ** 2))):6.1f}")


if __name__ == "__main__":
    main()
