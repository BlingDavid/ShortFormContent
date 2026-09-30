#!/usr/bin/env python3
"""Assemble one finished short from a spec.

    python production/tools/finish.py production/specs/01-heating-fee.json --dry-run
    python production/tools/finish.py production/specs/01-heating-fee.json

Inputs (all referenced from the spec):
    production/raw/<video>/<clip>.mp4      generated clips (audio ignored)
    production/audio/vo/<video>/<line>.wav voice lines
    production/audio/{sfx,music}/*.wav     from make_sfx.py / make_music.py
Outputs in production/out/<video>/:
    <video>.mp4  cover.png/jpg  cover_grid_check.png  captions.srt  caption.txt
    contact_sheet.png  report.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import cover
import ffutil
import mix
import qc
import video
from overlays import Overlay, blend
from timeline import ROOT, Timeline, load_spec


def srt_time(t: float) -> str:
    t = max(0.0, t)
    return f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{int(t % 60):02d},{int(round((t % 1) * 1000)):03d}".replace(",1000", ",999")


def build_overlays(tl: Timeline, subtitles: bool = True, watermark: str | None = None) -> list[Overlay]:
    chars = tl.spec.get("characters", {})
    out = [Overlay(o, tl.t(o["start"]), tl.t(o["end"]), chars) for o in tl.spec.get("overlays", [])]
    if subtitles:
        live: list[tuple[float, float, Overlay]] = []
        for v in tl.spec.get("audio", {}).get("vo", []):
            if not v.get("text") or v.get("subtitle", True) is False:
                continue
            s = v["_start"] - 0.05
            e = max(v["_end"] + 0.20, s + 0.7)
            sub = Overlay({"kind": "text", "style": "subtitle", "text": v["text"], "who": v.get("who", ""),
                           "pos": [540, v.get("sub_y", tl.spec.get("subtitle_y", 1300))]}, s, e, chars)
            for ps, pe, po in live:                            # keep overlapping lines from colliding
                if s < pe and e > ps:
                    sub.cy = po.cy - po.img.size[1] - 6
            live.append((s, e, sub))
            out.append(sub)
    if watermark:
        out.append(Overlay({"kind": "text", "style": "watermark", "text": watermark, "pos": [540, 960]},
                           0, tl.duration + 1, chars))
    return out


def print_plan(tl: Timeline, overlays: list[Overlay]) -> None:
    sp = tl.spec
    print(f"== {sp['id']}: {sp.get('title', '')}   {tl.duration:.2f}s @ {tl.fps:g}fps  "
          f"{tl.format['width']}x{tl.format['height']}  status={sp.get('status', '?')}")
    print("CLIPS")
    for c in sp["clips"]:
        flag = "" if tl.path(c["file"]).exists() else "   [not generated yet]"
        print(f"  {c['id']:4s} src {c['_in']:.2f}-{c['_out']:.2f}s x{c['_speed']:g} hold {c['_hold']:.2f}"
              f" -> {c['_start']:.2f}-{c['_end']:.2f}s  {c['file']}{flag}")
    print("VOICE")
    for v in sp.get("audio", {}).get("vo", []):
        flag = "" if tl.path(v["file"]).exists() else "   [no recording yet]"
        print(f"  {v['id']:4s} {v.get('who', ''):6s} {v['_start']:.2f}-{v['_end']:.2f}s  \"{v.get('text', '')}\"{flag}")
    print("OVERLAYS")
    for o in overlays:
        if o.spec.get("style") == "subtitle":
            continue
        txt = o.spec.get("text") or " / ".join(o.spec.get("lines", []))
        warn = "  (outside safe zone!)" if o.outside_safe() else ""
        warn += "  (position is a placeholder: set it on the real footage)" if o.spec.get("placeholder_position") else ""
        print(f"  {o.start:5.2f}-{o.end:5.2f}s  {o.spec.get('kind', 'text')}/{o.anim:5s} \"{txt}\"{warn}")
    print("SFX / MUSIC")
    for s in sp.get("audio", {}).get("sfx", []):
        print(f"  {tl.t(s['start']):5.2f}s  sfx   {s['file']}  {s.get('gain_db', 0):+.0f}dB")
    for m in sp.get("audio", {}).get("music", []):
        stop = f"{tl.t(m['stop_at']):.2f}s" if "stop_at" in m else "end"
        print(f"  {tl.t(m.get('start', 0)):5.2f}-{stop}  music {m['file']}  {m.get('gain_db', 0):+.0f}dB"
              f"{'  duck ' + str(m['duck_db']) + 'dB' if 'duck_db' in m else ''}")
    miss = tl.missing_assets()
    print(f"MISSING ({len(miss)}):", *(["none"] if not miss else ["\n  " + x for x in miss]))


def _composite(frame, t: float, overlays: list[Overlay]) -> None:
    for o in overlays:
        r = o.at(t)
        if r:
            blend(frame, *r)


def render_picture(tl: Timeline, overlays: list[Overlay], path: Path, crf: int, preset: str) -> None:
    enc = video.Encoder(path, tl.format["width"], tl.format["height"], tl.fps, crf, preset)
    try:
        for clip in tl.spec["clips"]:
            a, b = tl.frame_span(clip)
            hold = round(clip["_hold"] * tl.fps)
            play = (b - a) - hold
            base = None
            for i, frame in enumerate(video.read_clip_frames(tl, clip, play)):
                if hold and i == play - 1:
                    base = frame.copy()
                _composite(frame, (a + i) / tl.fps, overlays)
                enc.write(frame)
            for j in range(hold):
                frame = base.copy()
                _composite(frame, (a + play + j) / tl.fps, overlays)
                enc.write(frame)
    finally:
        enc.close()


def write_srt(tl: Timeline, path: Path) -> None:
    rows = []
    for v in tl.spec.get("audio", {}).get("vo", []):
        if v.get("text"):
            rows.append((v["_start"], max(v["_end"], v["_start"] + 0.7), v["text"]))
    path.write_text("".join(f"{i}\n{srt_time(s)} --> {srt_time(e)}\n{t}\n\n" for i, (s, e, t) in enumerate(rows, 1)))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--root", help="directory that spec paths (raw/, audio/, assets/) resolve against (default production/)")
    ap.add_argument("--out", help="output directory (default production/out/<id>)")
    ap.add_argument("--dry-run", action="store_true", help="print the resolved timeline and missing assets, render nothing")
    ap.add_argument("--no-subtitles", action="store_true", help="skip burned-in dialogue captions")
    ap.add_argument("--watermark", help="burn a diagonal-free label over the picture (used only by self-tests)")
    ap.add_argument("--allow-missing", action="store_true", help="render even if audio assets are missing (silent gaps)")
    ap.add_argument("--crf", type=int, default=17)
    ap.add_argument("--preset", default="medium")
    ap.add_argument("--keep-temp", action="store_true")
    a = ap.parse_args(argv)

    spec = load_spec(a.spec)
    root = Path(a.root) if a.root else ROOT
    tl = Timeline(spec, root, allow_missing=a.allow_missing)
    overlays = build_overlays(tl, not a.no_subtitles, a.watermark)
    print_plan(tl, overlays)
    if a.dry_run:
        return 0
    missing = tl.missing_assets()
    if missing and not a.allow_missing:
        print("\nCannot render yet: the assets above are missing. (Use --allow-missing to render anyway.)", file=sys.stderr)
        return 2

    out = Path(a.out) if a.out else root / "out" / spec["id"]
    out.mkdir(parents=True, exist_ok=True)
    pic, wav, final = out / "_picture.mp4", out / "_master.wav", out / f"{spec['id']}.mp4"
    t0 = time.time()
    print(f"\nrendering picture ({tl.total_frames} frames)...")
    render_picture(tl, overlays, pic, a.crf, a.preset)
    print("mixing audio...")
    master_info = mix.master(mix.Mixer(tl).build(), wav)
    ffutil.run(["-i", str(pic), "-i", str(wav), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
                "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", str(final)])
    if not a.keep_temp:
        pic.unlink(missing_ok=True)
        wav.unlink(missing_ok=True)

    write_srt(tl, out / "captions.srt")
    (out / "caption.txt").write_text(spec.get("caption", "") + "\n")
    cov = cover.make_cover(tl, out)
    qc.contact_sheet(final, out / "contact_sheet.png")
    result = qc.run_qc(final)
    outside = [o.spec.get("text") or o.spec.get("lines") for o in overlays if o.outside_safe()]
    if outside:
        result["flags"].append(f"overlays outside the platform-safe zone: {outside}")
    report = {"id": spec["id"], "seconds_to_render": round(time.time() - t0, 1), "master": master_info,
              "qc": result, "cover": cov, "problems": tl.problems}
    (out / "report.json").write_text(json.dumps(report, indent=2, default=str))
    print(f"\nfinished: {final}")
    print(json.dumps(result["facts"], indent=1, default=str))
    for f in result["flags"] + tl.problems:
        print("  FLAG:", f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
