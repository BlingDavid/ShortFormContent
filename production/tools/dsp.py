"""Small numpy DSP kit shared by the SFX, music and mixing tools.

Everything here is original synthesis code; no samples are used anywhere.
"""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

SR = 48000


def tt(dur: float) -> np.ndarray:
    """Time axis in seconds for `dur` seconds."""
    return np.arange(int(round(dur * SR))) / SR


def db(x: float) -> float:
    return 10 ** (x / 20.0)


def to_db(x: float) -> float:
    return 20 * np.log10(max(x, 1e-12))


def add(dst: np.ndarray, src: np.ndarray, at: float, gain: float = 1.0) -> None:
    """Mix `src` into `dst` starting at `at` seconds (clipped to dst length)."""
    i = int(round(at * SR))
    if i >= len(dst) or i + len(src) <= 0:
        return
    s0 = max(0, -i)
    d0 = max(0, i)
    n = min(len(src) - s0, len(dst) - d0)
    dst[d0:d0 + n] += src[s0:s0 + n] * gain


def fft_filter(x: np.ndarray, lo: float | None = None, hi: float | None = None,
               order: int = 3) -> np.ndarray:
    """Zero-phase Butterworth-shaped band/low/high-pass done in the frequency domain."""
    n = len(x)
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    m = np.ones_like(f)
    if lo:
        m *= 1.0 / (1.0 + (lo / np.maximum(f, 1e-9)) ** (2 * order))
    if hi:
        m *= 1.0 / (1.0 + (f / hi) ** (2 * order))
    return np.fft.irfft(spec * m, n)


def resonator(x: np.ndarray, freq: float, bw: float) -> np.ndarray:
    """Two-pole resonant filter (used for vowel formants). Unity gain at the peak."""
    r = np.exp(-np.pi * bw / SR)
    a1 = 2 * r * np.cos(2 * np.pi * freq / SR)
    a2 = -r * r
    g = 1 - r
    y = np.zeros_like(x)
    y1 = y2 = 0.0
    for i, v in enumerate(x):
        y0 = g * v + a1 * y1 + a2 * y2
        y[i] = y0
        y2, y1 = y1, y0
    return y


def fade(x: np.ndarray, fade_in: float = 0.0, fade_out: float = 0.0) -> np.ndarray:
    y = x.copy()
    ni, no = int(fade_in * SR), int(fade_out * SR)
    if ni:
        y[:ni] *= np.linspace(0, 1, ni, endpoint=False) ** 1.5
    if no:
        y[-no:] *= np.linspace(1, 0, no, endpoint=True) ** 1.5
    return y


def peak_norm(x: np.ndarray, peak_dbfs: float) -> np.ndarray:
    p = np.max(np.abs(x))
    return x if p == 0 else x * (db(peak_dbfs) / p)


def midi_hz(n: float) -> float:
    return 440.0 * 2 ** ((n - 69) / 12)


def write_wav(path: str | Path, x: np.ndarray) -> None:
    """Write mono 16-bit PCM at SR."""
    x = np.clip(x, -1.0, 1.0)
    pcm = (x * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def read_wav_mono(path: str | Path) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        assert w.getsampwidth() == 2, "read_wav_mono only handles 16-bit PCM"
        raw = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768
        if w.getnchannels() > 1:
            raw = raw.reshape(-1, w.getnchannels()).mean(axis=1)
        return raw


def spectrogram_image(x: np.ndarray, width: int = 360, height: int = 120):
    """Log-magnitude spectrogram as a PIL image (for eyeballing synthesized sounds)."""
    from PIL import Image

    n_fft, hop = 1024, max(1, len(x) // width)
    win = np.hanning(n_fft)
    frames = []
    for s in range(0, max(1, len(x) - n_fft), hop):
        seg = x[s:s + n_fft]
        if len(seg) < n_fft:
            seg = np.pad(seg, (0, n_fft - len(seg)))
        frames.append(np.abs(np.fft.rfft(seg * win)))
    S = np.array(frames).T
    S = 20 * np.log10(S + 1e-6)
    S = np.clip((S - (S.max() - 80)) / 80, 0, 1)[::-1]
    img = Image.fromarray((S * 255).astype("uint8"), "L").resize((width, height))
    return img
