# The Heating Fee  (`01-heating-fee`)

- Status: **awaiting-generation**
- Planned length: **13.4 s** vertical 9:16 (provisional until real clip and voice lengths exist)
- Final caption: *He charges rent on my own couch.*
- Cover: text "I WAS GONE 10 SECONDS" over a frame from clip `c1`

## Notes

- PRIMARY production candidate. Concept: Crumb claims the warm couch spot the moment its owner stands up.
- Reference frame: assets/crumb-heating-fee-opening.png (rust-orange couch, cushion dent, hand with glass at the edge). It was not reachable from the cloud workspace and must be added before generation.
- Beat timings are PROVISIONAL. Reconcile with production/heating-fee-production.md once that brief is attached; only the numbers in this file need to change.
- Voice lines: Crumb speaks over voiceover, so dragon lip-sync is not required. Human is always off camera.

## Clips to generate

### c1 - generate 4 s, use source 0.3-3.7 s (timeline 0.0-3.4 s)

Opening frame / reference: `assets/crumb-heating-fee-opening.png`

```
Vertical 9:16 tactile 3D animated comedy in the exact rust-orange couch setting of the reference image. Preserve the same palm-sized cream dragon, moss-green wings, two short burnt-orange horns, dark eyes, warm late-afternoon light, and cushion dent. Natural tiny movements; no morphing, extra limbs, changing furniture, text, or subtitles. Crumb lies curled in the cushion dent. He notices the returning human: his head lifts slightly and his dark eyes swivel up toward a hand holding a drinking glass that enters at the far edge of frame, and his expression settles into calm, possessive confidence. He does not get up.
```

### c2 - generate 4 s, use source 0.2-2.4 s (timeline 3.4-5.6 s)

Opening frame / reference: `assets/crumb-heating-fee-opening.png`

```
Vertical 9:16 tactile 3D animated comedy in the exact rust-orange couch setting of the reference image. Preserve the same palm-sized cream dragon, moss-green wings, two short burnt-orange horns, dark eyes, warm late-afternoon light, and cushion dent. Natural tiny movements; no morphing, extra limbs, changing furniture, text, or subtitles. A human hand (no face) enters from the upper right edge of frame and points down at the cushion dent. Crumb tips his chin up and looks at the pointing finger, unbothered, then blinks slowly once.
```

### c3 - generate 4 s, use source 0.2-2.0 s (timeline 5.6-7.4 s)

Opening frame / reference: `assets/crumb-heating-fee-opening.png`

```
Vertical 9:16 tactile 3D animated comedy in the exact rust-orange couch setting of the reference image. Preserve the same palm-sized cream dragon, moss-green wings, two short burnt-orange horns, dark eyes, warm late-afternoon light, and cushion dent. Natural tiny movements; no morphing, extra limbs, changing furniture, text, or subtitles. Close view of Crumb. He slowly raises one small claw to shoulder height, like a tiny official making a formal announcement, holds it steady while looking straight ahead, and blinks once.
```

### c4 - generate 8 s, use source 0.2-6.2 s (timeline 7.4-13.4 s)

Opening frame / reference: `assets/crumb-heating-fee-opening.png`

```
Vertical 9:16 tactile 3D animated comedy in the exact rust-orange couch setting of the reference image. Preserve the same palm-sized cream dragon, moss-green wings, two short burnt-orange horns, dark eyes, warm late-afternoon light, and cushion dent. Natural tiny movements; no morphing, extra limbs, changing furniture, text, or subtitles. The lower half of a human face (chin and lips only, no eyes) lowers from the top edge of frame and gives Crumb one soft kiss on the forehead between his horns, then lifts away out of frame. Crumb's eyes close briefly, then open. He scoots sideways about one inch on the cushion, pats the small empty space he made with one claw, looks up, and then holds still, breathing gently.
```

Fallback: If the scoot is not clean, regenerate it as its own clip from the last frame of the kiss take and cut the two together.

## Voice lines

| id | time | who | line | direction |
|---|---|---|---|---|
| v1 | 0.55-1.55 | human | That's my seat. | Mock-offended, warm, half a laugh. Not angry. |
| v2 | 1.85-3.15 | crumb | I kept it warm. | Solemn, matter-of-fact, slightly proud. A tiny voice that means every word. |
| v3 | 3.55-5.15 | human | I was gone ten seconds. | Incredulous but amused. |
| v4 | 5.90-6.90 | crumb | Heating fee. | Quiet, official, unarguable. Leave a beat of silence before it. The overlay carries the text. |
| v5 | 10.60-11.20 | crumb | There. | Gentle and satisfied; the softest line in the video. |

## Overlays

| time | overlay |
|---|---|
| 0.00-3.50 | text: I was gone for 10 seconds. |
| 6.05-9.00 | tag: HEATING FEE / 1 KISS |

Dialogue subtitles are burned in from the voice lines (turn off with `--no-subtitles`).

## Sound

| time | cue |
|---|---|
| 0.30 | SFX `glass_set_down` -4 dB |
| 6.65 | SFX `register_ding` -3 dB |
| 8.15 | SFX `kiss_soft` -2 dB |
| 9.25 | SFX `cushion_squeak` -4 dB |
| 9.90 | SFX `cushion_squeak` -10 dB |

## Review checklist (run on the finished file before calling it done)

- [ ] OPENING (0.0s): Crumb already curled in a human-sized cushion dent, hand with glass entering at the edge; the hook overlay is readable and clear of his face. It reads as 'he took my seat' with no explanation.
- [ ] PAYOFF: 'Heating fee' -> fee tag -> kiss -> the one-inch scoot and pat are clearly visible; 'There.' lands on a calm frame; the last ~1.8 s are quiet.
- [ ] CONTINUITY: same cream dragon, two burnt-orange horns, moss-green wings, dark eyes; same rust-orange couch, cushion dent and light in all four clips; five fingers on the hand; kiss shows chin/lips only.
- [ ] GENERATION ERRORS TO REJECT: extra limbs/horns, dragon changing size between cuts, glass or hand morphing, any lettering or logo in the footage, face detail on the human.
- [ ] Contact sheet (`out/<id>/contact_sheet.png`) shows no morphing, extra limbs, flicker or stray lettering.
- [ ] Overlays are legible on a phone-size preview and never cover the character's face.
- [ ] `report.json` has no unexplained flags (duration 10-17 s, ~-14 LUFS, no black frames).
