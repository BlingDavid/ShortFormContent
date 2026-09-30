# The Comfort Hoard  (`05-comfort-hoard`)

- Status: **rendered-procedural**
- Planned length: **13.0 s** vertical 9:16 (provisional until real clip and voice lengths exist)
- Final caption: *He understood the assignment eventually.*
- Cover: bare frame from clip `c1`

## Notes

- Concept: after a bad day, Crumb gathers the human's comfort items into a dragon's treasure pile.
- Needs new first frames (slipper haul with the pile softly visible behind; pile reveal) generated from the Crumb reference and approved before video generation.
- The last line lands with no overlay and no sound effect underneath; the final shot is quiet.
- The grunts in audio/sfx are synthesized placeholders; a performed take in Crumb's voice will read better.

## Clips to generate

### c1 - generate 4 s, use source 0.2-3.8 s (timeline 0.0-3.6 s)

Opening frame / reference: `assets/v5-slipper-haul-opening.png`

```
Vertical 9:16 tactile 3D animated comedy in an intimate living room at soft evening light. Preserve the exact palm-sized cream dragon from the reference image: round face, dark expressive eyes, two short burnt-orange horns, tiny moss-green wings, small claws. Props stay stable throughout: one human slipper (enormous next to the dragon), a folded blanket, a mug of tea, a small box of tissues. An off-camera human; only a hand may appear at the very end. Gentle humor that turns warm; no morphing, extra limbs, extra horns, changing props, text, subtitles, or logos. The small dragon strains, leaning back with his claws gripping the heel of an enormous human slipper, dragging it across a wooden floor toward a neat pile that is softly out of focus in the background. His whole body shakes with effort; he pauses to catch his breath, then heaves again.
```

### c2 - generate 4 s, use source 0.2-3.4 s (timeline 3.6-6.8 s)

Opening frame / reference: `assets/v5-pile-reveal-opening.png`

```
Vertical 9:16 tactile 3D animated comedy in an intimate living room at soft evening light. Preserve the exact palm-sized cream dragon from the reference image: round face, dark expressive eyes, two short burnt-orange horns, tiny moss-green wings, small claws. Props stay stable throughout: one human slipper (enormous next to the dragon), a folded blanket, a mug of tea, a small box of tissues. An off-camera human; only a hand may appear at the very end. Gentle humor that turns warm; no morphing, extra limbs, extra horns, changing props, text, subtitles, or logos. Reveal: the neat pile is now in focus (a folded blanket, a mug of tea with a wisp of steam, a small box of tissues), arranged carefully like treasure. The dragon hauls the slipper the last bit, hops up, hoists it on top of the pile, and smooths it into place with his claws.
```

### c3 - generate 4 s, use source 0.2-3.4 s (timeline 6.8-10.0 s)

Opening frame / reference: `assets/v5-blanket-closeup-opening.png`

```
Vertical 9:16 tactile 3D animated comedy in an intimate living room at soft evening light. Preserve the exact palm-sized cream dragon from the reference image: round face, dark expressive eyes, two short burnt-orange horns, tiny moss-green wings, small claws. Props stay stable throughout: one human slipper (enormous next to the dragon), a folded blanket, a mug of tea, a small box of tissues. An off-camera human; only a hand may appear at the very end. Gentle humor that turns warm; no morphing, extra limbs, extra horns, changing props, text, subtitles, or logos. Close view of the dragon sitting on the folded blanket. He pats the blanket beside him with one claw and looks up expectantly with solemn eyes, then holds still.
```

### c4 - generate 4 s, use source 0.2-3.2 s (timeline 10.0-13.0 s)

Opening frame / reference: `assets/v5-blanket-closeup-opening.png`

```
Vertical 9:16 tactile 3D animated comedy in an intimate living room at soft evening light. Preserve the exact palm-sized cream dragon from the reference image: round face, dark expressive eyes, two short burnt-orange horns, tiny moss-green wings, small claws. Props stay stable throughout: one human slipper (enormous next to the dragon), a folded blanket, a mug of tea, a small box of tissues. An off-camera human; only a hand may appear at the very end. Gentle humor that turns warm; no morphing, extra limbs, extra horns, changing props, text, subtitles, or logos. Quiet final shot: a human hand slowly enters from the edge of frame and settles on the blanket beside the dragon. He leans gently against one finger and closes his eyes contentedly. Warm light, almost no movement.
```

## Voice lines

| id | time | who | line | direction |
|---|---|---|---|---|
| v1 | 2.50-4.37 | human | Why are you stealing my stuff? | Amused disbelief; they have just walked in on it. |
| v2 | 4.50-5.29 | crumb | You had a bad day. | Simple, sincere, slightly out of breath from hauling. No joke in the delivery. |
| v3 | 6.90-7.72 | human | So? | Soft, a little raw; the joke is over and they know it. |
| v4 | 8.22-9.13 | crumb | I only hoard treasure. | Solemn and gentle. This is the whole heart of the video; do not play it as a punchline. |

## Overlays

| time | overlay |
|---|---|
| 0.00-3.60 | text: Caught my dragon stealing my stuff. |

Dialogue subtitles are burned in from the voice lines (turn off with `--no-subtitles`).

## Sound

| time | cue |
|---|---|
| 0.15 | SFX `slipper_drag` -4 dB |
| 0.35 | SFX `effort_grunt_1` -4 dB |
| 0.85 | SFX `effort_grunt_2` -5 dB |
| 1.40 | SFX `effort_grunt_3` -4 dB |
| 1.95 | SFX `effort_grunt_1` -6 dB |
| 2.40 | SFX `effort_grunt_2` -6 dB |
| 2.85 | SFX `heavy_breath` -6 dB |
| 5.50 | SFX `cloth_plop` -3 dB |
| 0.00-13.00 | Music `warm_bed` -17 dB, ducks under voice |

## Review checklist (run on the finished file before calling it done)

- [ ] OPENING (0.0s): a tiny dragon visibly straining to drag an enormous slipper; the hook line makes the crime clear before any dialogue.
- [ ] PAYOFF: the careful pile (blanket, tea, tissues) reads as a treasure hoard, not clutter; 'You had a bad day.' recontextualises the theft; 'I only hoard treasure.' lands with no overlay or SFX; the hand joining him on the blanket is the last thing we see, in quiet.
- [ ] CONTINUITY: same slipper, blanket, mug and tissue box in every clip; the pile is arranged identically in c2-c4; same dragon; evening light stays warm.
- [ ] GENERATION ERRORS TO REJECT: props changing between cuts, a second slipper appearing, extra fingers on the hand, steam or tea colour flickering, the dragon changing size relative to the slipper.
- [ ] Contact sheet (`out/<id>/contact_sheet.png`) shows no morphing, extra limbs, flicker or stray lettering.
- [ ] Overlays are legible on a phone-size preview and never cover the character's face.
- [ ] `report.json` has no unexplained flags (duration 10-17 s, ~-14 LUFS, no black frames).
