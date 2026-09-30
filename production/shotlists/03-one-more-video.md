# One More Video  (`03-one-more-video`)

- Status: **rendered-procedural**
- Planned length: **12.2 s** vertical 9:16 (provisional until real clip and voice lengths exist)
- Final caption: *The bedtime supervisor has been compromised.*
- Cover: bare frame from clip `c4`

## Notes

- Concept: Pip enforces bedtime, then gets caught breaking his own rule.
- Pip has no reference image yet. Generate and approve a Pip character sheet first (production/characters.md has the prompt), then use it as the reference for videos 3 and 4.
- The lullaby bed is cut before Pip's last line so the final joke lands in silence.

## Clips to generate

### c1 - generate 4 s, use source 0.2-3.6 s (timeline 0.0-3.4 s)

Opening frame / reference: `assets/v3-bedside-opening.png`

```
Vertical 9:16 tactile 3D animated comedy in a dim bedroom lit by a warm bedside lamp. Preserve the exact small round duck from the reference image: cobalt-blue raincoat, bright red boots, orange bill, expressive eyes. An off-camera human is shown only as a hand on the duvet. The smartphone is large next to the duck and its screen shows only a blank glow (no readable interface, no text). One room, restrained movement; no morphing, extra limbs, changing outfit, text, subtitles, or logos. Bedside close shot: a human hand loosely holds a smartphone on the duvet. Stern-faced Pip marches into frame, grips the phone's edge with both wings, and slides it out of the hand.
```

### c2 - generate 4 s, use source 0.2-2.8 s (timeline 3.4-6.0 s)

Opening frame / reference: `assets/v3-bedside-opening.png`

```
Vertical 9:16 tactile 3D animated comedy in a dim bedroom lit by a warm bedside lamp. Preserve the exact small round duck from the reference image: cobalt-blue raincoat, bright red boots, orange bill, expressive eyes. An off-camera human is shown only as a hand on the duvet. The smartphone is large next to the duck and its screen shows only a blank glow (no readable interface, no text). One room, restrained movement; no morphing, extra limbs, changing outfit, text, subtitles, or logos. Pip carries the phone to the far side of the nightstand and sets it down out of reach with a decisive tap, gives one satisfied nod, and folds his wings.
```

### c3 - generate 4 s, use source 0.2-3.2 s (timeline 6.0-9.0 s)

Opening frame / reference: `assets/v3-glow-opening.png`

```
Vertical 9:16 tactile 3D animated comedy in a dim bedroom lit by a warm bedside lamp. Preserve the exact small round duck from the reference image: cobalt-blue raincoat, bright red boots, orange bill, expressive eyes. An off-camera human is shown only as a hand on the duvet. The smartphone is large next to the duck and its screen shows only a blank glow (no readable interface, no text). One room, restrained movement; no morphing, extra limbs, changing outfit, text, subtitles, or logos. Later, the room is darker. Pip sits in a fold of the blanket lit only by the cool glow of a phone in front of him, scrolling with one wing, eyes flicking up and down, completely absorbed.
```

### c4 - generate 4 s, use source 0.2-3.4 s (timeline 9.0-12.2 s)

Opening frame / reference: `assets/v3-glow-opening.png`

```
Vertical 9:16 tactile 3D animated comedy in a dim bedroom lit by a warm bedside lamp. Preserve the exact small round duck from the reference image: cobalt-blue raincoat, bright red boots, orange bill, expressive eyes. An off-camera human is shown only as a hand on the duvet. The smartphone is large next to the duck and its screen shows only a blank glow (no readable interface, no text). One room, restrained movement; no morphing, extra limbs, changing outfit, text, subtitles, or logos. Close on Pip's face lit by the glow. Without looking up from the screen he freezes; his eyes flick sideways once toward the camera, then back to the screen. Guilty stillness, one tiny blink.
```

## Voice lines

| id | time | who | line | direction |
|---|---|---|---|---|
| v1 | 0.30-1.77 | human | One more video. | Sleepy, pleading, half-whispered. |
| v2 | 2.02-2.83 | pip | Denied. | Crisp, officious, zero room for appeal. |
| v3 | 7.90-8.69 | human | Pip. | Flat and knowing. One syllable of 'I see you'. |
| v4 | 9.19-10.44 | pip | One more video. | Distracted, eyes still on the screen, not even defending himself. The same words as the human's, in a completely different mood. |

## Overlays

| time | overlay |
|---|---|
| 0.00-3.40 | text: Pip's bedtime rule. |
| 9.19-12.20 | text: Pip's exception. |

Dialogue subtitles are burned in from the voice lines (turn off with `--no-subtitles`).

## Sound

| time | cue |
|---|---|
| 0.15 | SFX `phone_slide` -3 dB |
| 4.35 | SFX `phone_set_tap` -2 dB |
| 6.25 | SFX `scroll_swipes` -2 dB |
| 0.00-7.85 | Music `lullaby_bed` -17 dB, ducks under voice |

## Review checklist (run on the finished file before calling it done)

- [ ] OPENING (0.0s): a stern duck in red boots sliding a phone out of a hand; 'Pip's bedtime rule.' makes the rule explicit.
- [ ] PAYOFF: the hard cut to the glow on Pip's face reads instantly as 'he is watching it himself'; the music is gone before 'One more video.'; 'Pip's exception.' lands with the line; the last beat is his guilty stillness.
- [ ] CONTINUITY: identical Pip (cobalt raincoat, red boots, bill colour, proportions) in all four clips; phone is the same size relative to him; the cut from lamp-lit bedside to blue glow feels like time has passed, not like a different duck.
- [ ] GENERATION ERRORS TO REJECT: readable text on the phone screen, extra wings/legs, raincoat changing shade, the phone changing size.
- [ ] Contact sheet (`out/<id>/contact_sheet.png`) shows no morphing, extra limbs, flicker or stray lettering.
- [ ] Overlays are legible on a phone-size preview and never cover the character's face.
- [ ] `report.json` has no unexplained flags (duration 10-17 s, ~-14 LUFS, no black frames).
