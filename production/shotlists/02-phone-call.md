# The Phone Call  (`02-phone-call`)

- Status: **rendered-procedural**
- Planned length: **13.2 s** vertical 9:16 (provisional until real clip and voice lengths exist)
- Final caption: *A brave warrior with one very specific weakness.*
- Cover: bare frame from clip `c1`

## Notes

- Concept: Crumb can face frightening household objects but cannot make an ordinary phone call.
- Needs a new first frame: armored Crumb on a phone on a kitchen counter, generated from the Crumb reference (assets/crumb-heating-fee-opening.png) and approved before any video is generated.
- The fanfare is a building cue that the edit cuts dead on the first ring; that hard stop is the joke's turn.

## Clips to generate

### c1 - generate 4 s, use source 0.2-3.6 s (timeline 0.0-3.4 s)

Opening frame / reference: `assets/v2-crumb-armor-opening.png`

```
Vertical 9:16 tactile 3D animated comedy on a warm kitchen counter in soft natural light. Preserve the exact palm-sized cream dragon from the reference image: round face, dark expressive eyes, two short burnt-orange horns, tiny moss-green wings, small claws. He wears simple hand-made cardboard armor. A smartphone lies on the counter with a dark blank screen (no interface, no text). Natural tiny movements, clear readable action; no morphing, extra limbs, extra horns, changing props, text, subtitles, or logos. Low-angle hero shot: the armored dragon stands with his chest out and one foot up on a smartphone lying on the counter, wings slightly spread, chin lifted, gazing into the distance like a statue. Very slow push-in. Warm light behind him.
```

### c2 - generate 4 s, use source 0.2-1.6 s (timeline 3.4-4.8 s)

Opening frame / reference: `assets/v2-crumb-armor-opening.png`

```
Vertical 9:16 tactile 3D animated comedy on a warm kitchen counter in soft natural light. Preserve the exact palm-sized cream dragon from the reference image: round face, dark expressive eyes, two short burnt-orange horns, tiny moss-green wings, small claws. He wears simple hand-made cardboard armor. A smartphone lies on the counter with a dark blank screen (no interface, no text). Natural tiny movements, clear readable action; no morphing, extra limbs, extra horns, changing props, text, subtitles, or logos. An off-camera human's hand enters from the right edge and gestures toward the smartphone with an open palm, as if saying 'go ahead'. The armored dragon glances from the hand to the phone, his heroic posture softening slightly.
```

### c3 - generate 6 s, use source 0.2-4.6 s (timeline 4.8-9.2 s)

Opening frame / reference: `assets/v2-crumb-armor-opening.png`

```
Vertical 9:16 tactile 3D animated comedy on a warm kitchen counter in soft natural light. Preserve the exact palm-sized cream dragon from the reference image: round face, dark expressive eyes, two short burnt-orange horns, tiny moss-green wings, small claws. He wears simple hand-made cardboard armor. A smartphone lies on the counter with a dark blank screen (no interface, no text). Natural tiny movements, clear readable action; no morphing, extra limbs, extra horns, changing props, text, subtitles, or logos. The smartphone screen lights up with a soft white glow and vibrates gently on the counter. The armored dragon freezes mid-pose, eyes widening, then his shoulders and wings slowly slump as his confidence collapses; his gaze stays locked on the phone.
```

### c4 - generate 6 s, use source 0.2-4.2 s (timeline 9.2-13.2 s)

Opening frame / reference: `assets/v2-mug-opening.png`

```
Vertical 9:16 tactile 3D animated comedy on a warm kitchen counter in soft natural light. Preserve the exact palm-sized cream dragon from the reference image: round face, dark expressive eyes, two short burnt-orange horns, tiny moss-green wings, small claws. He wears simple hand-made cardboard armor. A smartphone lies on the counter with a dark blank screen (no interface, no text). Natural tiny movements, clear readable action; no morphing, extra limbs, extra horns, changing props, text, subtitles, or logos. An overturned ceramic mug sits on the counter beside the phone. The mug trembles slightly; then two tiny burnt-orange horns and a pair of dark eyes peek out from the gap under the rim, and the mug settles back down. Nothing else moves.
```

## Voice lines

| id | time | who | line | direction |
|---|---|---|---|---|
| v1 | 0.40-2.44 | human | You fought the vacuum cleaner. | Proud-parent tone, a little amazed. |
| v2 | 2.64-3.40 | crumb | It attacked first. | Grim, heroic, deadpan. A veteran reciting a battle report. |
| v3 | 3.45-5.16 | human | So call the dentist. | Light, breezy, as if it were nothing. |
| v4 | 6.20-7.78 | crumb | The vacuum never asked for my date of birth. | Small and shaky; the voice of someone whose confidence just left the building. Steady pace, no rush. |

## Overlays

| time | overlay |
|---|---|
| 0.00-3.40 | text: He fought the vacuum. Then I asked him to call the dentist. |
| 3.40-13.20 | checkitem: Fought the vacuum |
| 5.10-13.20 | checkitem: Call the dentist |

Dialogue subtitles are burned in from the voice lines (turn off with `--no-subtitles`).

## Sound

| time | cue |
|---|---|
| 5.10 | SFX `phone_ring` -6 dB |
| 6.55 | SFX `phone_ring` -10 dB |
| 8.00 | SFX `phone_ring` -13 dB |
| 9.70 | SFX `mug_clink` -4 dB |
| 0.00-5.10 | Music `heroic_flourish` -9 dB, ducks under voice |

## Review checklist (run on the finished file before calling it done)

- [ ] OPENING (0.0s): armored Crumb standing on a phone, heroic low angle, fanfare already rising; the hook overlay explains the bit before the first line.
- [ ] PAYOFF: fanfare stops dead on the first ring, his posture collapses, then the mug reveal; 'Call the dentist' cross lands with the ring; the last beat is the quiet mug clink.
- [ ] CONTINUITY: same cream dragon and cardboard armor in every clip; phone size stays roughly twice his size; mug is the same mug; kitchen light is consistent.
- [ ] GENERATION ERRORS TO REJECT: armor changing shape, phone screen showing readable UI/text, extra limbs, the dragon visible through the mug in the reveal beyond eyes and horns.
- [ ] Contact sheet (`out/<id>/contact_sheet.png`) shows no morphing, extra limbs, flicker or stray lettering.
- [ ] Overlays are legible on a phone-size preview and never cover the character's face.
- [ ] `report.json` has no unexplained flags (duration 10-17 s, ~-14 LUFS, no black frames).
