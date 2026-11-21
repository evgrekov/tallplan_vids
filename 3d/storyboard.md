# TallPlan — 3D Anatomy Stretch Reel (long, ~15s)

Remake of `reference.mp4` for TallPlan, following the proven workflow in `rules.md`. Generated as 10 s base (`prompts/long_base.txt`) + 5 s extension (`prompts/long_ext.txt`) without on-screen text; packshot via `./packshot.sh <video> 12.2`, then captions via `captions.py` + `long_v2_words.json`. Result: `long_v2_final.mp4`. The single prompt below is legacy (one-shot caps at 10 s, captions garble). Character: `man.png`.

## Overview
- **Duration:** 15 s · **Aspect:** 9:16 · **Test:** 360p (final 720p/1080p)
- **Style:** stylized Pixar-like 3D anatomy character from `man.png`, grey shorts always on, dark slate studio, rim light, TallPlan mint-green glow.
- **Pacing:** fast, a cut every ~1.5–2 s, snappy motion, caption chunk every ~0.7 s.
- **Structure:** hook (0–2) → stretch demo (2–6) → anatomy breakdown (6–12) → CTA (12–15, packshot from 12.5).

## Audio
- **Voice:** American male, late 20s, warm baritone, very energetic hype fitness-coach, ~220 WPM, no pauses, dry close-mic. Emphasis: TALLER, WALL, HEELS, SPINE, TALLPLAN.
- **Music:** driving 128 BPM electronic fitness beat, synth plucks + sub-bass, under the voice.
- **SFX:** whoosh on every cut, deep riser on muscle glow, shimmering riser on spine, UI pop at 12.5 s.
- **VO (~50 words):** "Want to stand taller? Kneel at a wall, press your hips in, and drop your hands to your heels! This deep stretch opens your psoas, quads and hip flexors, so your spine decompresses and your posture lifts. But to reach your full height, get your personalized plan in TallPlan!"

## Captions
Montserrat Black ALL CAPS, white + thick black stroke + soft shadow, spoken word lemon yellow `#F7FF14`, 2–3 words per chunk, single line, centered ~55% from top, pop-in 92→100% in 0.08 s.

Chunks: WANT TO / STAND TALLER? / KNEEL AT A WALL / PRESS YOUR HIPS IN / DROP YOUR HANDS / TO YOUR HEELS / THIS DEEP STRETCH / OPENS YOUR PSOAS / QUADS AND HIP FLEXORS / SO YOUR SPINE / DECOMPRESSES / AND POSTURE LIFTS / TO REACH YOUR FULL HEIGHT / GET YOUR PLAN / IN TALLPLAN

## Shots
1. **0–2s · Hook** — front medium shot, fast push-in, character looks up at a height ruler of green tick marks rising beside him.
2. **2–4s · Drop to wall** — whip cut to side profile; he snaps onto his knees facing the wall, hips pressed in, thighs flash mint green.
3. **4–6s · Camel** — cut to low 3/4 back angle; he arches back fast, hands slap onto heels, green glow shoots up the spine.
4. **6–9s · Cutaway** — close-up on pelvis and spine, slow orbit; psoas glows orange, quads and hip flexors pulse mint green in sequence.
5. **9–12s · Spine decompress** — fast orbit around the arched skeleton, vertebrae gently pop apart, spine glows lavender → mint, green ruler ticks rise along the spine.
6. **12–15s · CTA hold** — wide side shot, he holds the pose, glow pulses; packshot covers from 12.5 s in edit.

## Working full prompt (image input `man.png`, 360p test)
> Fast-paced educational 3D medical animation for TikTok, stylized Pixar-like cartoon style, 15 seconds, energetic editing with 6 quick camera cuts. This exact anatomy character keeps his grey shorts on the whole time. Shot 1 (0-2s): front medium shot, fast push-in, he looks up at a glowing mint green height ruler rising beside him. Shot 2 (2-4s): whip cut to side profile, he snaps down onto his knees facing a flat grey studio wall, hips pressed to the wall, thighs flash mint green. Shot 3 (4-6s): cut to a low 3/4 back angle, he quickly arches back into a yoga camel pose and slaps his hands onto his heels, a bright mint green glow shoots up his spine. Shot 4 (6-9s): close-up on the pelvis and spine with a slow orbit, the psoas glows orange, quadriceps and hip flexors pulse mint green one after another. Shot 5 (9-12s): fast orbiting camera around the arched skeleton, vertebrae gently decompress, the spine glows from lavender to mint green, green ruler tick marks rise along the spine. Shot 6 (12-15s): wide side shot, he holds the camel pose, glow pulsing. Dark slate-grey studio, rim lighting. Burned-in TikTok karaoke captions centered slightly below the middle of the frame, always on a single line: bold ALL CAPS Montserrat Black, white text with thick black outline and soft shadow, 2-3 words at a time, the currently spoken word highlighted in bright lemon yellow, synced to the voice. Audio: American male voiceover in his late 20s, warm baritone, very energetic, punchy hype fitness-coach delivery, fast about 220 words per minute, no pauses, dry studio close-mic, saying exactly: "Want to stand taller? Kneel at a wall, press your hips in, and drop your hands to your heels! This deep stretch opens your psoas, quads and hip flexors, so your spine decompresses and your posture lifts. But to reach your full height, get your personalized plan in TallPlan!" Driving 128 BPM electronic fitness beat underneath, fast whooshes on every cut, deep risers as muscles and spine glow.
