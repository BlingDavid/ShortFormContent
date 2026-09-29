"""Automated checks on a finished video, plus a labelled contact sheet for human review."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import ffutil


def run_qc(video: Path, expect: dict | None = None) -> dict:
    """Technical QC. Returns {'facts': {...}, 'flags': [...]}. Flags are things a human must look at."""
    expect = {"width": 1080, "height": 1920, "min_s": 10.0, "max_s": 17.0, "lufs": -14.0, **(expect or {})}
    info = ffutil.probe(video)
    r = subprocess.run([ffutil.ffmpeg_exe(), "-hide_banner", "-i", str(video),
                        "-vf", "blackdetect=d=0.1:pix_th=0.06,freezedetect=n=0.001:d=0.75",
                        "-af", "ebur128=peak=true,silencedetect=n=-50dB:d=0.3", "-f", "null", "-"],
                       capture_output=True, text=True)
    s = r.stderr
    facts = {"duration_s": info["duration"], "size": f"{info['width']}x{info['height']}", "fps": info["fps"],
             "has_audio": info["has_audio"]}
    summ = s[s.rfind("Summary:"):] if "Summary:" in s else ""
    for key, pat in (("lufs", r"I:\s+(-?[\d.]+)\s+LUFS"), ("lra", r"LRA:\s+([\d.]+)\s+LU"),
                     ("true_peak_db", r"Peak:\s+(-?[\d.]+)\s+dBFS")):
        m = re.search(pat, summ)
        facts[key] = float(m[1]) if m else None
    facts["black_segments"] = [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+)\s+black_end:([\d.]+)", s)]
    starts = [float(x) for x in re.findall(r"freeze_start:\s*([\d.]+)", s)]
    durs = [float(x) for x in re.findall(r"freeze_duration:\s*([\d.]+)", s)]
    facts["frozen_segments"] = [(a, round(a + d, 2)) for a, d in zip(starts, durs)]
    ss = [float(x) for x in re.findall(r"silence_start:\s*([\d.]+)", s)]
    se = [float(x) for x in re.findall(r"silence_end:\s*([\d.]+)", s)]
    facts["silent_segments"] = list(zip(ss, se + [info["duration"]] * (len(ss) - len(se))))

    flags = []
    d = info["duration"] or 0
    if not (expect["min_s"] <= d <= expect["max_s"]):
        flags.append(f"duration {d:.1f}s outside {expect['min_s']:.0f}-{expect['max_s']:.0f}s target")
    if (info["width"], info["height"]) != (expect["width"], expect["height"]):
        flags.append(f"size {info['width']}x{info['height']} is not {expect['width']}x{expect['height']}")
    if not info["has_audio"]:
        flags.append("no audio stream")
    if facts["lufs"] is not None and abs(facts["lufs"] - expect["lufs"]) > 1.5:
        flags.append(f"integrated loudness {facts['lufs']} LUFS is >1.5 LU from {expect['lufs']}")
    if facts["true_peak_db"] is not None and facts["true_peak_db"] > -1.0:
        flags.append(f"true peak {facts['true_peak_db']} dBFS is hotter than -1.0")
    if facts["black_segments"]:
        flags.append(f"black frames at {facts['black_segments']}")
    if facts["frozen_segments"]:
        flags.append(f"frozen picture at {facts['frozen_segments']} (fine only if it is an intended hold)")
    return {"facts": facts, "flags": flags}


def contact_sheet(video: Path, out_png: Path, every: float = 0.5, cols: int = 9) -> None:
    """Frames every `every` seconds, labelled with their time, for continuity review."""
    from PIL import Image, ImageDraw

    info = ffutil.probe(video)
    n = int((info["duration"] or 0) / every) + 1
    tw, th = 216, 384
    rows = (n + cols - 1) // cols
    raw = out_png.with_suffix(".raw.png")
    ffutil.run(["-i", str(video), "-vf", f"fps={1 / every},scale={tw}:{th},tile={cols}x{rows}:padding=4:margin=4:color=0x18181c",
                "-frames:v", "1", str(raw)])
    img = Image.open(raw).convert("RGB")
    d = ImageDraw.Draw(img)
    for i in range(n):
        x, y = 4 + (i % cols) * (tw + 4), 4 + (i // cols) * (th + 4)
        d.rectangle((x, y, x + 62, y + 20), fill=(0, 0, 0))
        d.text((x + 4, y + 4), f"{i * every:.1f}s", fill=(255, 255, 255))
    img.save(out_png)
    raw.unlink(missing_ok=True)
