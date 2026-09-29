# Production: five Crumb & Pip shorts

## Status: no finished videos yet

The finishing kit, original audio, scripts and generation prompts for all five videos are built and tested. **The animated clips themselves do not exist**, because the cloud session that built this folder had no video generator it could call. Nothing here is a finished video, no stills have been passed off as animation, and nothing has been published.

| # | Video | Length (planned) | State |
|---|---|---|---|
| 1 | The Heating Fee (primary) | 13.4 s | spec, prompts, cues ready; needs reference image + footage + voices |
| 2 | The Phone Call | 13.2 s | spec ready; needs armored-Crumb opening frame + footage + voices |
| 3 | One More Video | 12.2 s | spec ready; needs Pip character sheet + footage + voices |
| 4 | Social Battery Inspection | 13.4 s | spec ready; needs Pip character sheet + footage + voices |
| 5 | The Comfort Hoard | 13.0 s | spec ready; needs slipper/pile opening frames + footage + voices |

Lengths are computed from estimated voice-line durations and clip windows; they become exact once real clips and voice lines exist.

## What blocks the finished videos (and the exact fix)

1. **The two reference files.** `crumb-heating-fee-opening.png` and `heating-fee-production.md` are on the local Mac (`.../production/`), which the cloud workspace cannot see. The Google Drive connector is connected but returns an OAuth-scope error, so it cannot read files either.
   *Fix:* commit them to this repo as `production/assets/crumb-heating-fee-opening.png` and `production/heating-fee-production.md`, or attach them in chat. The Video 1 timings are provisional until that brief is read.
2. **A video generator.** Nothing enabled can generate video. Checked: connectors (Google Drive only), plugin catalog (none enabled), and the network policy, which blocks the Runway, Luma, Kling, fal, Replicate, Together, OpenAI, ElevenLabs and Hugging Face hosts. `generativelanguage.googleapis.com` (the Gemini API, which serves Veo) **is reachable**, but no API key is present. There is no GPU here.
   *Fix (recommended):* in the cloud environment settings (environment menu in the session title bar, then Edit), add `GEMINI_API_KEY` for a paid Google AI account with Veo access, then start a new session. No network change is needed. Veo takes an opening frame and returns a 9:16 clip. That account should also offer image generation and text-to-speech, which would cover the missing opening frames and the voices; that has to be confirmed once a key exists.
   *Alternatives:* add another provider's API host to the environment's allowed domains plus its key, or enable a video-generation connector. Say which and I will adapt the generation step.
3. **Character voices.** Crumb, Pip and the off-camera human need spoken lines (`specs/*.json` has each line with delivery notes). Either the same Gemini key supplies text-to-speech, or drop recordings at `audio/vo/<video-id>/<line-id>.wav`.
4. **A spend cap.** Video generation bills per second of output. The five specs need 21 clips, 92 s of generated footage for a single take of everything; choosing the best of a few takes each is a few hundred seconds. Cost depends on the model (roughly tens to low hundreds of dollars); current pricing should be checked and quoted before anything is generated.

Never paste keys into chat; the environment settings are the place for them.

## Once unblocked

```bash
pip install -r production/tools/requirements.txt
python production/tools/finish.py production/specs/01-heating-fee.json --dry-run   # resolved timeline + missing assets
python production/tools/finish.py production/specs/01-heating-fee.json             # renders production/out/01-heating-fee/
```

Order of work: reference files -> approve opening frames (Pip sheet first) -> generate one short clip per action -> voices -> `finish.py` -> review the contact sheet and `report.json` -> fix or regenerate -> next video. Video 1 goes first.

Outputs per video in `out/<id>/`: `<id>.mp4` (1080x1920, H.264/AAC, about -14 LUFS), `cover.png` / `cover.jpg`, `cover_grid_check.png` (what a 3:4 profile grid shows), `captions.srt`, `caption.txt`, `contact_sheet.png`, `report.json`.

## What is in this folder

| Path | What |
|---|---|
| `specs/*.json` | One spec per video: clips and per-clip generation prompts, voice lines with direction, overlay / SFX / music cues, cover, caption, QA checklist. Single source of truth. |
| `shotlists/*.md`, `captions.md` | Human-readable exports of the specs (`tools/export_docs.py`). |
| `characters.md` | Crumb and Pip design locks, voice direction, Pip character-sheet prompt, house style, review protocol. |
| `audio/sfx`, `audio/music` | Original synthesized sound effects and three music pieces. Nothing sampled, nothing to license. |
| `fonts/` | Lilita One (SIL OFL) for all on-screen type. |
| `tools/` | `finish.py` (assemble, overlays, subtitles, mix, master, cover, QC), `make_sfx.py`, `make_music.py`, `export_docs.py`, `selftest.py`. |
| `raw/`, `out/`, `assets/` | Where generated clips, finished files and reference images go. |

## What was and was not verified

Verified by `tools/selftest.py` on **synthetic test-pattern footage** (watermarked, kept out of this folder, never a deliverable): 1080x1920 output, timing anchors, animated overlays, burned-in subtitles and SRT, slow-motion and hold, audio mixing and ducking, loudness (about -14 LUFS, true peak under -1 dBFS), cover generation with the 3:4 grid check, and colour fidelity (worst error 0.9 of 255 on an 8-colour Rec.709 chart).

Not verified: anything about real generated footage (character consistency, morphing, continuity), and how the synthesized sound effects and music actually sound. They were checked by level and spectrogram only, not auditioned. The effort grunts in particular are placeholders for a performed take.

Design assumption to confirm: Pip's body colour is not in the brief; butter-yellow is assumed (see `characters.md`).
