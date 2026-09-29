#!/usr/bin/env python3
"""End-to-end check of the finishing pipeline on SYNTHETIC footage.

The footage here is test patterns and a beep-voice, watermarked, written to a temp
directory. It exists only to prove the tooling works; it is never a deliverable.

    python production/tools/selftest.py [--workdir DIR] [--keep]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

import dsp
import ffutil
import make_sfx
from timeline import ROOT


CHART = [(200, 100, 46), (255, 255, 255), (30, 30, 30), (240, 240, 240), (16, 200, 90), (250, 30, 30), (70, 120, 220), (190, 170, 120)]


def sh(*args):
    ffutil.run([str(a) for a in args])


def make_footage(d: Path) -> None:
    sh("-f", "lavfi", "-i", "testsrc2=size=720x1280:rate=24:duration=4", "-pix_fmt", "yuv420p", "-c:v", "libx264",
       "-colorspace", "bt709", d / "a_portrait_24.mp4")
    sh("-f", "lavfi", "-i", "color=c=0xC8642E:size=1280x720:rate=30:duration=3.5", "-vf",
       "drawbox=x=100+t*0:y=200:w=200:h=200:color=white@1:t=fill", "-pix_fmt", "yuv420p", "-c:v", "libx264", d / "b_landscape_30.mp4")
    sh("-f", "lavfi", "-i", "smptebars=size=720x1280:rate=24:duration=3", "-pix_fmt", "yuv420p", "-c:v", "libx264", d / "c_bars.mp4")
    # 8-colour chart encoded as true Rec.709, for the colour-fidelity check
    from PIL import Image
    chart = np.zeros((1280, 720, 3), np.uint8)
    for i, c in enumerate(CHART):
        chart[i * 160:(i + 1) * 160] = c
    Image.fromarray(chart).save(d / "chart.png")
    sh("-loop", "1", "-i", d / "chart.png", "-t", "1", "-r", "24", "-vf",
       "scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int,format=yuv420p",
       "-c:v", "libx264", "-crf", "10", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
       "-color_range", "tv", d / "chart709.mp4")


def make_voice(path: Path, syllables: int, seed: int) -> float:
    rng = np.random.default_rng(seed)
    y = np.zeros(int(syllables * 0.19 * dsp.SR) + 2000)
    for i in range(syllables):
        g = make_sfx._grunt(rng, 0.14, 150 + 30 * rng.random(), 140, [(700, 90, 1.0), (1200, 110, .6), (2500, 160, .25)], 0.2)
        dsp.add(y, g, i * 0.19)
    dsp.write_wav(path, dsp.peak_norm(y, -6))
    return len(y) / dsp.SR


def test_spec(d: Path) -> dict:
    vo = d / "vo"
    vo.mkdir(exist_ok=True)
    for i, n in enumerate([5, 7, 4], 1):
        make_voice(vo / f"v{i}.wav", n, i)
    A = lambda name: str(d / name)
    return {
        "id": "selftest", "title": "Pipeline self-test (synthetic)", "status": "test",
        "format": {"width": 1080, "height": 1920, "fps": "auto"},
        "caption": "self-test caption",
        "characters": {"crumb": {"color": "#FFE9C2", "outline": "#7A3B16"}, "human": {"color": "#FFFFFF"}},
        "clips": [
            {"id": "c1", "file": A("a_portrait_24.mp4"), "in": 0.0, "out": 2.0, "speed": 0.5},   # 2 s of source at half speed = 4 s
            {"id": "c2", "file": A("b_landscape_30.mp4"), "in": 0.0, "out": 3.5, "focus": [0.3, 0.5]},
            {"id": "c3", "file": A("c_bars.mp4"), "in": 0.0, "out": 2.5, "hold_end": 0.5},
        ],
        "audio": {
            "vo": [
                {"id": "v1", "who": "human", "text": "That's my seat.", "file": A("vo/v1.wav"), "start": "c1.start+0.6"},
                {"id": "v2", "who": "crumb", "text": "I kept it warm.", "file": A("vo/v2.wav"), "start": "v1.end+0.3"},
                {"id": "v3", "who": "crumb", "text": "There.", "file": A("vo/v3.wav"), "start": "c3.start+0.2"},
            ],
            "sfx": [
                {"file": "glass_set_down", "start": "v1.start-0.35", "gain_db": -3},
                {"file": "register_ding", "start": "v2.end-0.05", "gain_db": -2},
                {"file": "kiss_soft", "start": "c2.start+1.0"},
                {"file": "stamp_thud", "start": "c3.start+0.25", "gain_db": -6},
                {"file": "phone_ring", "start": "c2.start+2.0"},
            ],
            "music": [
                {"file": "lullaby_bed", "start": 0, "stop_at": "v3.start-0.1", "gain_db": -6, "fade_out": 0.4,
                 "duck_db": -8, "automation": [[0, 0], ["c2.start", -6], ["c2.end", 0]]},
            ],
            "room_tone": {"gain_db": 6},
        },
        "overlays": [
            {"id": "hook", "kind": "text", "style": "hook", "text": "I was gone for 10 seconds.", "start": 0.0, "end": "c1.end-0.5"},
            {"id": "fee", "kind": "tag", "lines": ["HEATING FEE", "1 KISS"], "start": "v2.end-0.05", "end": "c2.end", "pos": [540, 1000]},
            {"id": "ok", "kind": "checkitem", "icon": "check", "text": "Fought the vacuum", "start": "c2.start+0.3", "end": "c2.end", "pos": [540, 560]},
            {"id": "no", "kind": "checkitem", "icon": "cross", "text": "Call the dentist", "start": "c2.start+1.2", "end": "c2.end", "pos": [540, 700]},
            {"id": "stamp", "kind": "stamp", "text": "EYE CONTACT\nDETECTED", "start": "c3.start+0.25", "end": "c3.end", "pos": [540, 950]},
            {"id": "sign", "kind": "text", "style": "sign", "text": "CLOSED", "start": 0.0, "end": "c1.end", "pos": [540, 1100], "rot": -3, "anim": "none"},
        ],
        "cover": {"clip": "c1", "at": 1.0, "text": "I WAS GONE 10 SECONDS", "y": 480, "avoid": [300, 700, 800, 1300], "overlays": ["sign"]},
    }


def expect(cond: bool, msg: str, fails: list) -> None:
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond:
        fails.append(msg)


def spec_smoke(d: Path) -> int:
    """Render every REAL spec end to end with watermarked stand-in clips and voices.

    Catches typos in cue names, anchors, overlay positions and cover settings before any
    money is spent on generation. Stand-ins live in a temp root, never in production/.
    """
    import finish

    fails: list[str] = []
    for path in sorted((ROOT / "specs").glob("*.json")):
        spec = json.loads(path.read_text())
        root = d / spec["id"] / "root"
        (root / "audio").mkdir(parents=True, exist_ok=True)
        for sub in ("sfx", "music"):
            link = root / "audio" / sub
            if not link.exists():
                link.symlink_to(ROOT / "audio" / sub)
        for c in spec["clips"]:
            p = root / c["file"]
            p.parent.mkdir(parents=True, exist_ok=True)
            sh("-f", "lavfi", "-i", f"testsrc2=size=720x1280:rate=24:duration={c['gen']['seconds']}", "-pix_fmt", "yuv420p",
               "-c:v", "libx264", "-preset", "ultrafast", "-colorspace", "bt709", p)
        for v in spec["audio"].get("vo", []):
            p = root / v["file"]
            p.parent.mkdir(parents=True, exist_ok=True)
            make_voice(p, max(1, round(v["est"] / 0.19)), sum(map(ord, v["id"])))
        out = d / spec["id"] / "out"
        print(f"\n##### {spec['id']}")
        rc = finish.main([str(path), "--root", str(root), "--out", str(out), "--watermark", "SPEC TEST - NOT FOOTAGE",
                          "--preset", "ultrafast"])
        rep = json.loads((out / "report.json").read_text()) if (out / "report.json").exists() else {}
        flags = rep.get("qc", {}).get("flags", []) + rep.get("problems", [])
        ok = rc == 0 and (out / f"{spec['id']}.mp4").exists()
        expect(ok, f"{spec['id']} renders end to end", fails)
        expect(not [f for f in flags if "safe zone" in f or "duration" in f or "size" in f or "black" in f],
               f"{spec['id']} has no safe-zone / duration / size / black-frame flags", fails)
        cov = rep.get("cover") or {}
        expect(not cov.get("warnings") and "skipped" not in cov, f"{spec['id']} cover builds cleanly {cov.get('warnings', '')}", fails)
    print("\nSPEC SMOKE:", "PASS" if not fails else f"FAIL ({len(fails)})")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir")
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--specs", action="store_true", help="instead, render every real spec with stand-in footage")
    a = ap.parse_args()
    d = Path(a.workdir or tempfile.mkdtemp(prefix="sfc_selftest_"))
    d.mkdir(parents=True, exist_ok=True)
    print("workdir:", d)
    if a.specs:
        return spec_smoke(d)
    make_footage(d)
    spec = test_spec(d)
    (d / "spec.json").write_text(json.dumps(spec, indent=2))
    fails: list[str] = []
    out = d / "out"

    import finish
    rc = finish.main([str(d / "spec.json"), "--out", str(out), "--watermark", "PIPELINE TEST - NOT FOOTAGE", "--preset", "veryfast"])
    expect(rc == 0, "finish.py exits 0", fails)
    final = out / "selftest.mp4"
    expect(final.exists(), "final mp4 written", fails)
    info = ffutil.probe(final)
    expect((info["width"], info["height"]) == (1080, 1920), f"1080x1920 (got {info['width']}x{info['height']})", fails)
    expect(info["has_audio"], "has audio stream", fails)
    expect(abs(info["duration"] - 10.5) < 0.15, f"duration ~10.5s (got {info['duration']:.2f})", fails)
    rep = json.loads((out / "report.json").read_text())
    lufs = rep["qc"]["facts"]["lufs"]
    expect(lufs is not None and abs(lufs + 14) < 1.5, f"integrated loudness near -14 LUFS (got {lufs})", fails)
    tp = rep["qc"]["facts"]["true_peak_db"]
    expect(tp is not None and tp <= -1.0, f"true peak <= -1 dBFS (got {tp})", fails)
    for f in ("captions.srt", "caption.txt", "contact_sheet.png", "cover.png", "cover_grid_check.png"):
        expect((out / f).exists(), f"{f} written", fails)

    # colour fidelity: an 8-colour Rec.709 chart must come out of the whole pipeline as the same RGB
    chart = dict(spec, id="chart", clips=[{"id": "f", "file": str(d / "chart709.mp4"), "in": 0, "out": 1.0}],
                 audio={}, overlays=[], cover=None)
    (d / "chart.json").write_text(json.dumps(chart))
    finish.main([str(d / "chart.json"), "--out", str(d / "chart_out"), "--no-subtitles", "--preset", "veryfast"])
    raw = subprocess.run([ffutil.ffmpeg_exe(), "-v", "error", "-i", str(d / "chart_out" / "chart.mp4"), "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"], capture_output=True).stdout
    W, H = 1080, 1920
    worst = 0.0
    for i, want in enumerate(CHART):
        r, c = i * 240 + 120, W // 2                      # band centre, luma row/col
        Y = raw[r * W + c]
        U = raw[W * H + (r // 2) * (W // 2) + c // 2]
        V = raw[W * H + W * H // 4 + (r // 2) * (W // 2) + c // 2]
        y = 1.164 * (Y - 16)
        got = (y + 1.793 * (V - 128), y - 0.213 * (U - 128) - 0.533 * (V - 128), y + 2.112 * (U - 128))
        worst = max(worst, *(abs(g - w) for g, w in zip(got, want)))
    expect(worst <= 3.0, f"colour chart survives the pipeline (worst channel error {worst:.1f} <= 3 code values)", fails)

    print("\nRESULT:", "PASS" if not fails else f"FAIL ({len(fails)})")
    if a.keep or fails:
        print("artifacts kept in", d)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
