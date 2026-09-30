# Social Battery Inspection  (`04-social-battery-inspection`)

- Status: **rendered-procedural**
- Planned length: **13.4 s** vertical 9:16 (provisional until real clip and voice lengths exist)
- Final caption: *Pip counts grocery-store eye contact as an outing.*
- Cover: bare frame from clip `c1`

## Notes

- Concept: Pip refuses to let his human leave after an exhausting day.
- Shoot c1-c3 with a locked-off camera and identical framing so the CLOSED lettering (added in editing) sits on the blank sign in the same place. Adjust the sign overlay's pos/rot/scale after the footage exists.
- Human is only ever knees-down. No sign lettering is generated in the footage.

## Clips to generate

### c1 - generate 4 s, use source 0.2-3.2 s (timeline 0.0-3.0 s)

Opening frame / reference: `assets/v4-entryway-opening.png`

```
Vertical 9:16 tactile 3D animated comedy in a cozy apartment entryway, locked-off camera. Preserve the exact small round duck from the reference image: cobalt-blue raincoat, bright red boots, orange bill, expressive eyes, carrying a tiny wooden clipboard with a pencil. A front door behind him. The off-camera human is visible only from the knees down (sneakers, jeans). Any sign is plain blank white cardboard with no writing. Simple physical actions, warm playful tone; no morphing, extra limbs, changing outfit, text, subtitles, or logos. Wide locked-off shot. Pip stands planted in front of the door, red boots wide apart, holding a large blank white cardboard sign upright beside him, as tall as he is. The human's sneakers stand a few feet away, one foot tapping. A hand reaches in from the side, tries the door handle; it rattles once and the door stays shut.
```

### c2 - generate 4 s, use source 0.2-2.2 s (timeline 3.0-5.0 s)

Opening frame / reference: `assets/v4-entryway-opening.png`

```
Vertical 9:16 tactile 3D animated comedy in a cozy apartment entryway, locked-off camera. Preserve the exact small round duck from the reference image: cobalt-blue raincoat, bright red boots, orange bill, expressive eyes, carrying a tiny wooden clipboard with a pencil. A front door behind him. The off-camera human is visible only from the knees down (sneakers, jeans). Any sign is plain blank white cardboard with no writing. Simple physical actions, warm playful tone; no morphing, extra limbs, changing outfit, text, subtitles, or logos. Same framing. Pip stays planted with the blank sign, chin up, looking sternly up at the human off-camera above him, then gives one small firm nod.
```

### c3 - generate 4 s, use source 0.2-2.4 s (timeline 5.0-7.2 s)

Opening frame / reference: `assets/v4-entryway-shoes-opening.png`

```
Vertical 9:16 tactile 3D animated comedy in a cozy apartment entryway, locked-off camera. Preserve the exact small round duck from the reference image: cobalt-blue raincoat, bright red boots, orange bill, expressive eyes, carrying a tiny wooden clipboard with a pencil. A front door behind him. The off-camera human is visible only from the knees down (sneakers, jeans). Any sign is plain blank white cardboard with no writing. Simple physical actions, warm playful tone; no morphing, extra limbs, changing outfit, text, subtitles, or logos. Knees-down shot of the entryway floor: the human's sneakers shift, then pause, toes pointing at the door; one heel lifts slightly and settles, as if reluctantly considering the question. Pip's red boots are visible at the edge of frame.
```

### c4 - generate 4 s, use source 0.2-3.4 s (timeline 7.2-10.4 s)

Opening frame / reference: `assets/v4-clipboard-opening.png`

```
Vertical 9:16 tactile 3D animated comedy in a cozy apartment entryway, locked-off camera. Preserve the exact small round duck from the reference image: cobalt-blue raincoat, bright red boots, orange bill, expressive eyes, carrying a tiny wooden clipboard with a pencil. A front door behind him. The off-camera human is visible only from the knees down (sneakers, jeans). Any sign is plain blank white cardboard with no writing. Simple physical actions, warm playful tone; no morphing, extra limbs, changing outfit, text, subtitles, or logos. Close on Pip flipping a page on his tiny clipboard and scribbling with a pencil, then pressing a small rubber stamp firmly onto the page, and lifting it away. The page stays blank and unreadable.
```

### c5 - generate 4 s, use source 0.2-3.2 s (timeline 10.4-13.4 s)

Opening frame / reference: `assets/v4-blanket-opening.png`

```
Vertical 9:16 tactile 3D animated comedy in a cozy apartment entryway, locked-off camera. Preserve the exact small round duck from the reference image: cobalt-blue raincoat, bright red boots, orange bill, expressive eyes, carrying a tiny wooden clipboard with a pencil. A front door behind him. The off-camera human is visible only from the knees down (sneakers, jeans). Any sign is plain blank white cardboard with no writing. Simple physical actions, warm playful tone; no morphing, extra limbs, changing outfit, text, subtitles, or logos. Pip turns and pushes a folded blanket across the floor; it slides into frame toward the human's sneakers and stops against them. Pip gives a small satisfied nod.
```

## Voice lines

| id | time | who | line | direction |
|---|---|---|---|---|
| v1 | 1.30-3.26 | human | Pip, I have plans. | Tired but trying to be reasonable. Almost a sigh. |
| v2 | 3.15-4.79 | pip | You were social yesterday. | Clipped, earnest, reading from the official record. |
| v3 | 5.20-7.28 | human | I went to the grocery store. | Defensive, a little sheepish; this is their entire alibi. |
| v4 | 7.60-9.22 | pip | And you made eye contact. | Grave. Announcing a verdict. Slight pause before 'eye contact'. |

## Overlays

| time | overlay |
|---|---|
| 0.00-3.00 | text: Social battery inspection. |
| 0.00-5.00 | text: CLOSED |
| 9.34-13.40 | stamp: EYE CONTACT DETECTED |

Dialogue subtitles are burned in from the voice lines (turn off with `--no-subtitles`).

## Sound

| time | cue |
|---|---|
| 0.20 | SFX `door_handle_rattle` -3 dB |
| 7.30 | SFX `pencil_scratch` -4 dB |
| 9.34 | SFX `stamp_thud` -1 dB |
| 10.70 | SFX `blanket_drag` -3 dB |

## Review checklist (run on the finished file before calling it done)

- [ ] OPENING (0.0s): a tiny duck blocking the front door with a sign taller than he is; 'CLOSED' is readable on the sign and 'Social battery inspection.' frames the bit.
- [ ] PAYOFF: 'And you made eye contact.' -> stamp lands exactly on the stamp sound -> 'EYE CONTACT DETECTED' -> the blanket slides into the human's shoes. Reads without explanation.
- [ ] CONTINUITY: identical Pip and clipboard in every clip; the door, sign and lighting do not change; shoes stay the same sneakers; CLOSED lettering sits flat on the sign in c1-c2.
- [ ] GENERATION ERRORS TO REJECT: any writing on the sign or clipboard, the door changing, extra feet on the human, blanket morphing, Pip losing the clipboard between cuts.
- [ ] Contact sheet (`out/<id>/contact_sheet.png`) shows no morphing, extra limbs, flicker or stray lettering.
- [ ] Overlays are legible on a phone-size preview and never cover the character's face.
- [ ] `report.json` has no unexplained flags (duration 10-17 s, ~-14 LUFS, no black frames).
