# Slides pipeline — silent slideshow ads

Separate from `3d/` (video pipeline). For references that are a sequence of static images cut on the beat of music, no voice.

`uv run make.py <reference_url> <folder> "<art style>" ["<brief: other exercises, music>"]`

1. `plan.txt` → gemini-3.8-flash plans from the reference: style, character, slide prompts (hook + exercises), captions, music prompt.
2. `oai.py` → OpenAI `gpt-image-2.5-flare`, 1024×1536, quality medium (~$0.011 per image, ~$0.019 with a reference image; 2.6 was ~2–3× pricier at the same look, A/B 2026-11-27). The model draws no text.
3. Captions in edit (Montserrat Black, colors from the plan) in the empty top band; the image is fit to full width at the bottom of the 9:16 frame.
4. Music: Lyria 3 clip ($0.04). Slides cut every 4 beats of the planned BPM; the last slide is held 2.2 s under `../3d/packshot.sh`, with the CTA caption below the card.

Cost: ~$0.23 per ad (plan ~$0.01 + 5 images ~$0.18 + music $0.04). Steps are idempotent: delete a file to redo it.
Vary the look between ads with the style argument only; structure stays the reference's.

Hooks: every plan follows the scroll-stopping hook rule in `plan.txt`, but plans made in one batch drift to the same idea (they copy the rule's examples). In a batch, give each ad its own hook idea + caption in the brief.

## Other formats
- `myth.py` — myth → fact: two slides, two music tracks, xfade transition (5th arg), packshot without captions.
- `stopmo.py` — stop-motion explainer: OpenAI table/hand/paper cutouts (keyed from magenta), tags drawn in Pillow, a hand places items at 12 fps with jitter, OpenAI gpt-4o-mini-tts voice (Gemini TTS has a 100 requests/day cap), lo-fi, packshot. ~$0.44 per ad.
- `char.py` — mascot cut-out animation: model sheet → per scene bg + mascot pose + props drawn from it (`oai.edit`), cut out (flood fill from the white border) and animated separately: entrances with overshoot, bounce/hop/wiggle/float/spin, squash & stretch, props popping in, contact shadow; OpenAI TTS, word subtitles, synthesized SFX, a saved sound from Drive 02_sources/music (`<sound_id>` arg, sheet tab Music), packshot.
- `grid.py grid/<spec>.json` — 2×2 photo-grid slideshow (looksmaxxing style): title + 4 labeled photos per slide, beat cuts, packshot. ~$0.24.
- `quiz.py quiz/<spec>.json` — UGC quiz ad, no voice: photo bobbing to the beat + hook card (`table` = height chart / mom's height, or `comment`), app-style quiz screens with typed answers, the real store screen from `TallPlan photo/7nov` with the TallPlan icon + name, packshot. ~$0.07. Photoreal minors are blocked by OpenAI moderation: the photo is a ~19-year-old.
- `char.py` takes an optional 4th arg brief that replaces the default story arc (e.g. "signs you're still growing").
See FORMATS.md for the five formats.
- `facts.py <url> <folder> "<topic>" "<facts>"` — facts explainer (ref: maxphilipstudio): flat vector character on blue, height ruler with live ft/cm value (grows, side-by-side comparisons, one scale for the whole video), icons, realistic photo shots with a push, pleasant OpenAI voice, word subtitles, a saved sound (`<sound_id>`), packshot. Only the given facts are used. ~$0.3 per ad. Keep ~90 words for ~30 s.
- `anim.py` — helpers shared by char.py and facts.py (cut-outs, easing, voice timing, subtitles, music, SFX, render + packshot).
