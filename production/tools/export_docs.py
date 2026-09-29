#!/usr/bin/env python3
"""Write human-readable shot lists and a captions sheet from production/specs/*.json.

The specs stay the single source of truth; regenerate these after editing a spec.

    python production/tools/export_docs.py
"""
from __future__ import annotations

from pathlib import Path

from timeline import ROOT, Timeline, load_spec


def compose(spec: dict, clip: dict) -> str:
    return f"{spec['gen_base']} {clip['gen']['action']}"


def shotlist(spec: dict) -> str:
    tl = Timeline(spec, ROOT, allow_missing=True)
    L = [f"# {spec['title']}  (`{spec['id']}`)", "",
         f"- Status: **{spec.get('status', '?')}**",
         f"- Planned length: **{tl.duration:.1f} s** vertical 9:16 (provisional until real clip and voice lengths exist)",
         f"- Final caption: *{spec['caption']}*"]
    cv = spec.get("cover", {})
    cover_kind = f'text "{cv["text"]}" over a frame' if cv.get("text") else "bare frame"
    L.append(f"- Cover: {cover_kind} from clip `{cv.get('clip', '-')}`")
    L += ["", "## Notes", ""] + [f"- {n}" for n in spec.get("notes", [])]

    L += ["", "## Clips to generate", ""]
    for c in spec["clips"]:
        g = c["gen"]
        L += [f"### {c['id']} - generate {g['seconds']} s, use source {c['_in']:.1f}-{c['_out']:.1f} s "
              f"(timeline {c['_start']:.1f}-{c['_end']:.1f} s)", "",
              f"Opening frame / reference: `{g['first_frame']}`", "", "```", compose(spec, c), "```"]
        if g.get("fallback"):
            L += ["", f"Fallback: {g['fallback']}"]
        L.append("")

    L += ["## Voice lines", "", "| id | time | who | line | direction |", "|---|---|---|---|---|"]
    for v in spec["audio"].get("vo", []):
        L.append(f"| {v['id']} | {v['_start']:.2f}-{v['_end']:.2f} | {v['who']} | {v['text']} | {v.get('direction', '')} |")

    L += ["", "## Overlays", "", "| time | overlay |", "|---|---|"]
    for o in spec.get("overlays", []):
        txt = (o.get("text") or " / ".join(o.get("lines", []))).replace("\n", " ")
        L.append(f"| {tl.t(o['start']):.2f}-{tl.t(o['end']):.2f} | {o.get('kind', 'text')}: {txt} |")
    L += ["", "Dialogue subtitles are burned in from the voice lines (turn off with `--no-subtitles`).", ""]

    L += ["## Sound", "", "| time | cue |", "|---|---|"]
    for s in spec["audio"].get("sfx", []):
        L.append(f"| {tl.t(s['start']):.2f} | SFX `{s['file']}` {s.get('gain_db', 0):+.0f} dB |")
    for m in spec["audio"].get("music", []):
        stop = f"{tl.t(m['stop_at']):.2f}" if "stop_at" in m else "end"
        L.append(f"| {tl.t(m.get('start', 0)):.2f}-{stop} | Music `{m['file']}` {m.get('gain_db', 0):+.0f} dB"
                 f"{', ducks under voice' if 'duck_db' in m else ''} |")
    L += ["", "## Review checklist (run on the finished file before calling it done)", ""]
    L += [f"- [ ] {q}" for q in spec.get("qa", [])]
    L += ["- [ ] Contact sheet (`out/<id>/contact_sheet.png`) shows no morphing, extra limbs, flicker or stray lettering.",
          "- [ ] Overlays are legible on a phone-size preview and never cover the character's face.",
          "- [ ] `report.json` has no unexplained flags (duration 10-17 s, ~-14 LUFS, no black frames).", ""]
    return "\n".join(L)


def main() -> None:
    specs = [load_spec(p) for p in sorted((ROOT / "specs").glob("*.json"))]
    out = ROOT / "shotlists"
    out.mkdir(exist_ok=True)
    for s in specs:
        (out / f"{s['id']}.md").write_text(shotlist(s))
        print("wrote", out / f"{s['id']}.md")
    rows = ["# Final captions and covers", "", "Do not publish anything from this list until each video has passed its review checklist.", "",
            "| # | Video | Caption | Cover |", "|---|---|---|---|"]
    for i, s in enumerate(specs, 1):
        cv = s.get("cover", {})
        cover = f'text "{cv["text"]}" over clip {cv["clip"]}' if cv.get("text") else f"frame from clip {cv.get('clip', '-')}"
        rows.append(f"| {i} | {s['title']} | {s['caption']} | {cover} |")
    (ROOT / "captions.md").write_text("\n".join(rows) + "\n")
    print("wrote", ROOT / "captions.md")


if __name__ == "__main__":
    main()
