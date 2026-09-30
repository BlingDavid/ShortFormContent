# Production: five Crumb & Pip shorts

## Status: five videos rendered (code-animated, stand-in voices)

All five shorts exist as finished 1080x1920 files in `out/<id>/` with covers, captions and QC reports. **How they were made matters:** no AI video generator was reachable from the cloud session, so the characters are animated in code (`anim/`): drawn frame by frame, keyed to the same timeline as the voice, SFX and overlays. That is real animation, but it is a stylised vector look, **not** the tactile 3D style of your reference image (which was not available here). Voices are robotic espeak-ng stand-ins. Nothing has been published.

| # | Video | Length | File |
|---|---|---|---|
| 1 | The Heating Fee | 13.4 s | `out/01-heating-fee/01-heating-fee.mp4` |
| 2 | The Phone Call | 13.2 s | `out/02-phone-call/02-phone-call.mp4` |
| 3 | One More Video | 12.2 s | `out/03-one-more-video/03-one-more-video.mp4` |
| 4 | Social Battery Inspection | 13.4 s | `out/04-social-battery-inspection/04-social-battery-inspection.mp4` |
| 5 | The Comfort Hoard | 13.0 s | `out/05-comfort-hoard/05-comfort-hoard.mp4` |

Rebuild any video: `python production/tools/make_voices.py <id>` (voices), `python production/anim/render.py <id>` (clips into `raw/`, git-ignored), `python production/tools/finish.py production/specs/<id>.json` (edit, mix, cover, QC).

Known limits: Crumb and Pip are designed from the text brief, so their look is provisional; the espeak voices are placeholders (drop recorded or TTS WAVs into `audio/vo/<id>/` and re-run `finish.py`); sound effects and music were checked by level and spectrogram, not by ear; Video 5's last line has its caption switched off to honour "no overlay on the final line".

## Upgrading to true AI-generated footage (optional)

### What that needs (and the exact fix)

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

`python production/tools/selftest.py --specs` renders **all five real specs** end to end with watermarked stand-in clips and voice lines (in a temp directory, never in `out/`). All five pass: cue names, anchors, overlay positions and covers resolve, lengths come out at 12.2-13.4 s, no overlay leaves the platform-safe zone. It also confirmed the Video 2 fanfare stops on exactly the first ring. Run it after editing any spec, before spending anything on generation.

Not verified: anything about real generated footage (character consistency, morphing, continuity), and how the synthesized sound effects and music actually sound. They were checked by level and spectrogram only, not auditioned. The effort grunts in particular are placeholders for a performed take.

Design assumption to confirm: Pip's body colour is not in the brief; butter-yellow is assumed (see `characters.md`).
