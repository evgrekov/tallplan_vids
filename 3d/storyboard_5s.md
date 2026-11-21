# TallPlan — 3D Anatomy Stretch Reel (5s test)

Fast test cut of `storyboard.md`. One generated 5 s clip with voice + karaoke captions; `packshot.png` overlaid on the last ~1.5 s in edit. Character: `man.png`.

## Overview
- **Duration:** 5.0 s · **Aspect:** 9:16 · **Test resolution:** 360p (final: 720p/1080p)
- **Style:** stylized Pixar-like 3D anatomy character from `man.png`, grey shorts always on, dark slate studio, rim light, TallPlan mint-green glow.
- **Pacing:** fast, 3 camera angles in 5 s (a cut every ~1.5 s), caption chunk every ~0.7 s, snappy body motion — no slow holds.

## Audio
- **Voice:** American male, late 20s, warm baritone, **very energetic, punchy, hype fitness-coach delivery, fast ~220 WPM**, no pauses, dry studio close-mic. Emphasis on WALL, HEELS, SPINE, TALLPLAN.
- **Music:** driving 128 BPM electronic fitness beat, synth plucks + sub-bass, under the voice.
- **SFX:** fast whoosh on every cut, deep riser on spine glow, UI pop at 3.6 s (packshot).
- **VO (15 words):** "Kneel at a wall, hands to your heels, and stretch that spine! Get your plan in TallPlan!"

## Captions (from reference, recognized by gemini-3.8-flash)
- Montserrat Black (800–900), ALL CAPS, ~5% frame height, centered, ~55% from top, single line.
- Inactive words white `#FFFFFF`, **spoken word lemon yellow `#F7FF14`** (karaoke, word-by-word).
- Black stroke ~8–10 px, soft drop shadow (0 4px 8px rgba(0,0,0,.75)), no background box.
- 2–3 words per chunk, pop-in scale 92%→100% in 0.08 s, hard cut to next chunk.

| Time | Chunk | Yellow word timing |
|---|---|---|
| 0.0–0.8 | KNEEL AT A WALL | KNEEL 0.0–0.3 · AT A 0.3–0.5 · WALL 0.5–0.8 |
| 0.8–1.6 | HANDS TO YOUR HEELS | HANDS 0.8–1.0 · TO YOUR 1.0–1.3 · HEELS 1.3–1.6 |
| 1.6–2.6 | AND STRETCH THAT SPINE | AND 1.6–1.7 · STRETCH 1.7–2.0 · THAT 2.0–2.2 · SPINE 2.2–2.6 |
| 2.6–3.4 | GET YOUR PLAN | GET 2.6–2.8 · YOUR 2.8–3.0 · PLAN 3.0–3.4 |
| 3.4–4.2 | IN TALLPLAN | IN 3.4–3.6 · TALLPLAN 3.6–4.2 |

## Shots
1. **0.0–1.5s · Drop to wall** — side profile, quick push-in. Character snaps down onto his knees facing the wall, hips pressed in; thighs flash mint green. Whoosh.
2. **1.5–3.0s · Snap to camel** — whip-cut to low 3/4 angle. He arches back fast, hands slap onto heels; green glow shoots up the spine, vertebrae pop apart. Riser.
3. **3.0–5.0s · Orbit + CTA** — fast orbit around the arched skeleton, spine pulsing green. `packshot.png` card pops in over 3.6–5.0s in edit (covers the action — fine).

## Working full prompt (v3, image input `man.png`, 360p test)
> Fast-paced educational 3D medical animation for TikTok, stylized Pixar-like cartoon style, 5 seconds, energetic editing with 3 quick camera cuts. This exact anatomy character keeps his grey shorts on the whole time. Shot 1 (0-1.5s): side profile, quick push-in, he snaps down onto his knees facing a flat grey studio wall, hips pressed to the wall, thighs flash mint green. Shot 2 (1.5-3s): whip cut to a low 3/4 angle, he quickly arches back into a yoga camel pose and slaps his hands onto his heels, a bright mint green glow shoots up his spine. Shot 3 (3-5s): fast orbiting camera around his arched body, spine pulsing mint green. Dark slate-grey studio, rim lighting. Burned-in TikTok karaoke captions centered slightly below the middle of the frame: bold ALL CAPS Montserrat Black, white text with thick black outline and soft shadow, 2-3 words at a time, the currently spoken word highlighted in bright lemon yellow, synced to the voice: "KNEEL AT A WALL" / "HANDS TO YOUR HEELS" / "AND STRETCH THAT SPINE" / "GET YOUR PLAN" / "IN TALLPLAN". Audio: American male voiceover in his late 20s, warm baritone, very energetic, punchy hype fitness-coach delivery, fast about 220 words per minute, no pauses, dry studio close-mic, saying exactly: "Kneel at a wall, hands to your heels, and stretch that spine! Get your plan in TallPlan!" Driving 128 BPM electronic fitness beat underneath, fast whooshes on every cut, a deep riser as the spine glows.
