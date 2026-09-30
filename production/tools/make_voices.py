#!/usr/bin/env python3
"""Stand-in character voices with espeak-ng (robotic, but consistent per character).

    python production/tools/make_voices.py            # all specs
    python production/tools/make_voices.py 01-heating-fee

Replace any file in audio/vo/<video>/ with a performed or TTS take and the edit picks it up.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import ffutil
from timeline import ROOT, load_spec

# espeak-ng voice, pitch 0-99, speed wpm, amplitude, then an ffmpeg post filter.
# Kept in natural adult speaking ranges (median F0: Crumb ~100 Hz, Pip ~125 Hz, human ~170 Hz); the Klatt
# variants are less buzzy than the default formant voices. No pitch-shifting, which is what made it sound squeaky.
TRIM = "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,apad=pad_dur=0.06"
WARM = TRIM + ",lowpass=f=6000,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,aecho=0.8:0.5:18|31:0.10|0.06"
PROFILES = {
    "crumb": ("en-us+klatt4", 45, 158, 150, WARM),
    "pip": ("en-gb-x-rp+klatt2", 60, 168, 150, WARM),
    "human": ("en-us+f2", 36, 170, 150, WARM),
}


def speak(text: str, who: str, out: Path) -> None:
    voice, pitch, speed, amp, post = PROFILES[who]
    with tempfile.TemporaryDirectory() as d:
        raw = Path(d) / "raw.wav"
        subprocess.run(["espeak-ng", "-g", "1", "-v", voice, "-p", str(pitch), "-s", str(speed), "-a", str(amp), "-w", str(raw), text],
                       check=True)
        out.parent.mkdir(parents=True, exist_ok=True)
        ffutil.run(["-i", str(raw), "-af", f"{post},highpass=f=90,loudnorm=I=-18:TP=-3:LRA=7", "-ar", "48000", "-ac", "1",
                    "-c:a", "pcm_s16le", str(out)])


def main() -> None:
    which = sys.argv[1:] or [p.stem for p in sorted((ROOT / "specs").glob("*.json"))]
    for vid in which:
        spec = load_spec(ROOT / "specs" / f"{vid}.json")
        for v in spec["audio"]["vo"]:
            out = ROOT / v["file"]
            speak(v["text"], v["who"], out)
            print(f"{vid} {v['id']:3s} {v['who']:6s} {v['text']}")


if __name__ == "__main__":
    main()
