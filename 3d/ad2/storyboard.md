# ad2 — TallPlan "Tibialis" reel (~18s)

Remake of `ad2/reference.mp4` (Grow app, tibialis / shin training) for TallPlan. Analysis: `analysis.md`. Character: `characters/athlete.png`.
Pipeline (`../rules.md`): 10 s base (`prompts/base.txt`) + 8 s extension (`prompts/ext.txt`) at 360p → QA → `../finish.sh <ext.mp4> <packshot_start>`.

## Overview
- **Duration:** ~18 s · **Aspect:** 9:16 · generate 360p → AI upscale 720p
- **Style:** semi-realistic digital painting / medical illustration, soft painterly shading, clean linework, pale blue-grey seamless studio. Anatomy shown as glowing muscle overlays on skin.
- **Brand accent:** TallPlan mint green replaces the reference red (muscle highlights, arrows, ruler).
- **Pacing:** calm-confident explainer, cut every ~2–3 s, slow push-ins.
- **Structure:** hook — height + shin (0–3) → mechanism: tibialis → ankle → knees → hips stacking (3–10) → tease "one foot angle" (10–15) → CTA (15–18, packshot).

## Audio
- **Voice (from reference):** American male, mid-20s–early 30s, clear resonant, lightly compressed, confident informational delivery, ~175 WPM, moderate-high energy, dry studio.
- **Music:** ambient electronic / synth-pop, ~118 BPM, soft pads + light plucks, ducked under voice.
- **SFX:** soft whoosh at start, riser on the kinetic-chain arrows (~8.5 s), whoosh + UI pop on packshot.
- **VO (~55 words):**
  - base: "To stand taller, train the muscle on the front of your shin. A weak tibialis limits ankle control and pushes compensation up through your knees and hips. Rebuild that control, and your whole body stacks taller."
  - ext: "But normal reps aren't the full method. There's one foot angle that matters. Get the full routine in TallPlan."

## Captions (from reference)
2 words per chunk, ALL CAPS heavy sans (Montserrat Black), white + black stroke + soft shadow, active word yellow `#FFEA00`, centered ~60% from top. Rendered by `captions.py` (current defaults: 3 words, `#F7FF14`, 55% — close enough; tune if needed).

## Shots
| # | Time | Shot | Keyframe |
|---|---|---|---|
| 1 | 0–3 | Full-body profile next to a mint-green height ruler, he stands tall, a mint arrow sweeps up over his head | `keyframes/hook.png` |
| 2 | 3–6 | Seated on a bench (tibialis raise), close-up knee→toes, toes pull up toward the shin and lower, tibialis glows mint green | `keyframes/shin.png` |
| 3 | 6–10 | Medium-full profile, glowing arrows climb ankle → knee → hip → spine, body straightens and stacks | `characters/athlete.png` |
| 4 | 10–13 | Low close-up of the foot, a hand presses the ankle/tendon area | — |
| 5 | 13–15.5 | Seated tibialis raise with skeletal foot overlay, toes up, curved mint arrow | `keyframes/foot.png` |
| 6 | 15.5–18 | Full body standing tall by the ruler (packshot covers from the CTA) | `keyframes/hook.png` |
