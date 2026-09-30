# Characters, voices and house style

The long-term aim is recurring characters, recurring jokes and one identifiable world, so these locks apply to every video.

## Crumb (videos 1, 2, 5)

**Design lock:** palm-sized cream dragon; round face; dark expressive eyes; exactly two short burnt-orange horns; tiny moss-green wings; small claws.
**Personality:** solemn, self-assured, unexpectedly caring. Treats everyday comforts as guarded treasure.
**Reference:** `assets/crumb-heating-fee-opening.png` (rust-orange couch, cushion dent). The 3D rig in `anim3d/crumb3d.py` is modelled on it and used in videos 1, 2 and 5.
**Scale:** always palm-sized. A mug, a slipper and a phone should each look enormous next to him.
**Voice:** small, dry, deadpan; sincere underneath. Never baby-talk. The comedy is that he means every word.
**Sonic motif:** the small register *ding* is Crumb's "fee" sound and can recur across episodes.

## Pip (videos 3, 4)

**Design lock:** small round duck; cobalt-blue raincoat; bright red boots; carries a tiny wooden clipboard (with a pencil).
**Personality:** appointed himself household supervisor; enforces rules earnestly; sometimes breaks them himself.
**Reference:** none exists yet. **Generate and approve a character sheet before any Pip video.**
**Assumption to confirm:** the brief does not give Pip's body colour. Butter-yellow with an orange bill is assumed, so he reads instantly as a duck and stays distinct from cream Crumb. Change it here before generating the sheet if you want something else.
**Voice:** clipped, earnest, officious; a duck who believes his clipboard is law. Not a quack; clear diction.
**Sonic motif:** the music-box lullaby is Pip's bedtime cue; it can be interrupted in future episodes.

Character-sheet prompt (image model):

> Character reference sheet on a plain warm-grey background, polished tactile 3D character design (appealing, not glossy, believable materials): a small round duck with a soft butter-yellow body and orange bill, big dark expressive eyes, wearing a cobalt-blue raincoat (hood down) and bright red rubber boots, holding a tiny wooden clipboard with a pencil. Show front, three-quarter and side views plus three expressions: stern, satisfied nod, guilty. One duck only, consistent proportions in every view. No text, labels, logos or watermark.

## Off-camera human

Never a stable face. Hands, forearms, a mug, knees-down, or the lower half of a face only when a kiss requires it. Voice: warm, amused, a little tired; close to the microphone.

## Opening frames

Every generated clip starts from an approved opening frame (or reference set) that already contains the right character, props and light. Generate that frame first with an image model using the character reference, approve it, then animate it. Keep one action per clip.

## House style (all edits)

- Type: **Lilita One** (SIL Open Font License, `fonts/`). White text with a warm-black outline and soft shadow for hooks and subtitles.
- Fee tag: cream paper tag with dashed border. Stamp: red ink on a cream label. Checklist: cream pills with round green tick / red cross.
- Safe zone for anything readable: x 70-1010, y 230-1480 (clear of Shorts / TikTok / Reels UI). Covers keep type below y = 270 so 3:4 profile grids do not crop it.
- Nothing readable is generated inside a video model. All words are composited in the edit so spelling is exact.
- Dialogue subtitles are burned in (people watch muted) and also exported as `captions.srt`.
- Audio: everything in `audio/` is synthesized from scratch by `tools/make_sfx.py` and `tools/make_music.py`, so there is nothing to license. Final mix is about -14 LUFS with a -1.5 dBTP limiter.

## Review protocol before anything is called finished

1. Watch the contact sheet (`out/<id>/contact_sheet.png`), then scrub the video.
2. Reject on: extra or missing limbs, horn count other than two, wing or raincoat colour drift, props changing between cuts, flicker, morphing hands, any lettering or logo in the footage.
3. Check the opening frame and the payoff read with no explanation.
4. Read `out/<id>/report.json`: duration 10-17 s, roughly -14 LUFS, no black frames, no unexplained frozen picture.
5. Do not publish. Publishing is a separate, explicit decision.
