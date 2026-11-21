Keys: `GEMINI_API_KEY` (Google AI Studio) and `OPENAI_API_KEY` in the repo root `.env` (gitignored). API: `https://generativelanguage.googleapis.com/v1beta/...` with header `X-goog-api-key`.

Models:
gemini-3.8-flash для распознания видео

Our most intelligent Flash model, engineered for long-horizon software engineering, autonomous agents, and complex enterprise workflows.

Free Tier Paid Tier, per 1M tokens in USD
Input price Free of charge  $0.75 through December 31, 2026.
$1.50 starting January 1, 2027.
Output price (including thinking tokens)  Free of charge  $3.75 through December 31, 2026.
$7.50 starting January 1, 2027.



gemini-omni-1.1-flash для генерации видео
Our next-generation video generation and editing model, now generally available to developers on the paid tier of the Gemini API.


Free Tier Paid Tier, per 1M tokens in USD
Input price Not available $1.50 (text / image / video / audio)
Output price (including thinking tokens)  Not available $9.00 (text)
$17.50 (video)*
Used to improve our products  Yes No
* Billing is based on total output token consumption, calculated at a rate of 5,792 tokens per second of 720p video. Under Standard pricing, this equates to an effective price of approximately $0.10 per second.

Правила: всегда пиши в ответах итоговую стоимость

## Automated pipeline
`python3 auto.py <url> <folder>` (budget cap $2 per ad, `BUDGET` in auto.py) — download → plan (Gemini, `pipeline/prompts/plan.txt`) → character + keyframes (QA) → base + extension (QA) → finish.sh → API review `report.md`. Agent work = read report, fix templates in `pipeline/prompts/`. Creative rules (exaggerate the problem, off-screen narrator, constant motion + SFX, graphic numbers OK) live in plan.txt/guards.txt.

## Tools
- **yt-dlp** (`/opt/homebrew/bin/yt-dlp`) — download references: `yt-dlp -o "<folder>/reference.%(ext)s" --write-info-json <url>`. Each new ad lives in its own folder (`ad2/`, `ad3/`…) with `reference.mp4` inside.

## Workflow: reference → brand video (proven, v3)

1. **Recognize with Google, never invent.** Analyze `reference.mp4` with gemini-3.8-flash (generateContent, inline base64 video) in separate passes:
   - shots/storyboard (timecodes, camera, action, VFX)
   - audio (VO verbatim + voice: gender, age, accent, timbre, energy, WPM; music BPM; SFX timecodes)
   - captions (`mediaResolution: MEDIA_RESOLUTION_HIGH`): font, colors, stroke, position, chunking, karaoke timing
2. **Create characters (before any video):** from the reference's character description + brand, generate a character sheet with gemini-3.1-flash-image into `<ad>/characters/` — `<name>.png` (full body, neutral pose, plain studio bg, 9:16), plus keyframes for every key pose (`<ad>/keyframes/<pose>.png`). QA each (`qa.py <png> -`). Style refs = reference close-ups (not the hook frame), prompt says "style only, not composition" + "ONLY ONE PERSON" — otherwise the model copies ghost silhouettes/poses. Unusual poses (e.g. "standing on heels, toes up") flip to the common one (tiptoes) — describe them as a well-known exercise instead ("seated tibialis raise"). Reuse an existing brand character (`man.png`) when the style fits; a new one only when the reference style differs. All video generations get the character image as image 1.
3. **Write storyboard** into `storyboard*.md`: overview, audio, captions table, shots, one full ready-to-run prompt.
4. **Generate** with gemini-omni-1.1-flash — **Interactions API only**: `POST /v1beta/interactions`, body `{model, input:[{type:image,data,mime_type},{type:text,text}], response_format:{type:video, aspect_ratio:"9:16", resolution}}`. Video comes back base64 in `steps[type=model_output].content[type=video].data`.
5. **One prompt = visuals + voice + music + SFX, NO text** ("No text or captions on screen"). Voice is generated inside the video; the packshot is overlaid on the last ~1.5 s in edit (covering the action is fine, the voice must stay).
   - Script: `python3 omni.py prompts/<x>.txt <out.mp4> --image man.png [--res 360p]` (prints interaction id + cost).
   - Max ~10 s per generation. Longer → **extend**: `python3 omni.py prompts/<ext>.txt <out.mp4> --prev <id>` — returns the FULL video (base + continuation), voice continues seamlessly.
   - AI-rendered captions break after ~15 words → captions are always burned by script (step 6).
6. **Post-production in one command:** `./finish.sh <raw_360p.mp4> <packshot_start>` → upscale (Real-ESRGAN → 720p) → 60 fps (ffmpeg minterpolate, scene-cut aware; model outputs 24 fps, TikTok max is 60 — never 120) → align → packshot → captions → `<raw>_final.mp4`. Steps below are what it runs.
   **Packshot:** `./packshot.sh <video.mp4> [start=3.6]` → `<video>_final.mp4` (ffmpeg: dims bg, pops `packshot.png` card 80→100%, keeps audio).
7. **Captions:** `python3 align.py <video.mp4> <words.json>` — voice-band (300–3400 Hz) loudness envelope finds speech regions (music does not extend them), Gemini transcribes each region separately, words spread by syllables and boundaries snapped to loudness dips (raw Gemini word timestamps drift up to ~1 s, never use them). Then `uv run captions.py <video_final.mp4> <words.json> <out.mp4> <packshot_start>` — Pillow renders reference style (Montserrat Black, yellow active word, auto-fit to 90% width, pop 92→100% in 0.08s, always at 70% height: lower half, clear of faces, below the packshot card), ffmpeg overlays. Run AFTER packshot so captions stay on top. Start the packshot on the CTA phrase.
8. **QA gate (before every next paid step):** `python3 qa.py <video> "<expected VO>" [--from SEC]` — Gemini checks face (no skull), shorts, no text, pose, voice. FAIL → first look at the flagged frames yourself (QA gives false positives, e.g. ruler ticks read as "text"), regenerate only on a real defect, max 2 tries, then stop and report. For an extension check only the new part (`--from 9.5`).
9. **Fix VO glitches without regenerating:** a repeated/extra word → `./cut.sh <video> <from> <to>` (cut A+V, best under the packshot), find the range on the voice-band envelope, then re-run align → packshot → captions.
10. **Verify** the result: contact sheet via ffmpeg + transcribe the VO with gemini-3.8-flash.

### Defaults
- **Production = generate 360p + local AI upscale** (`./upscale.sh`, part of finish.sh). Native 720p only on explicit request. Upscale (local Real-ESRGAN realesr-animevideov3 x2, ~20 s per 5 s clip): crisp edges, but less fine detail than native 720p.
- Generate at **360p** (~3× cheaper than 720p: ~$0.18 vs ~$0.51 per 5 s).
- Character: `man.png` as image input. Always say "keeps his grey shorts on the whole time".
- Pacing: fast, a cut every ~1.5 s, snappy motion, no slow holds.
- Voice: American male, late 20s, warm baritone, **very energetic hype fitness-coach, ~220 WPM, no pauses**, dry close-mic.
- Captions (captions.py): Montserrat Black ALL CAPS, white + thick black stroke + soft shadow, **spoken word lemon yellow #F7FF14**, 2–3 words per chunk, centered ~55% from top.
- Brand: TallPlan, mint-green glow accents. Do not write the packshot UI with AI.

### Prompt guards (known failures → fixes)
- Head turns into a bare skull in anatomy shots → "CHARACTER LOCK: cartoon face, big eyes, dark hair always visible, never a bare skull"; anatomy close-ups frame the body only ("head out of frame").
- Model writes the VO as on-screen text → "CLEAN FRAME: no text, subtitles, letters, numbers, UI. The voiceover is audio only and is never written on screen."
- Wrong pose (hands on wall, standing up) → describe the pose mechanically (knees on floor, thighs vertical, hands grip own heels, chest to ceiling) + "Hands are NOT on the wall", "He does not stand up".
- Extension drifts → repeat CHARACTER LOCK + CLEAN FRAME + current pose in the extension prompt.
- Reversed knees (shins/feet in front, on the side he faces) and spine drawn on the chest → "ANATOMY LOCK" line in every prompt + QA check `anatomy`.
- **Keyframe for every key pose (solves pose + anatomy):** generate a still with gemini-3.1-flash-image from `man.png` (`prompts/kf_<pose>.txt`, mechanical pose description, side profile), QA it (`qa.py keyframes/<pose>.png -`), then pass it as 2nd image: base `--image man.png --image keyframes/<pose>.png` ("image 2 = exact target pose"), extension `--image keyframes/<pose>.png`. v4 passed QA first try for base and extension.
- QA judges joints on full-res stills every 0.5 s (video sampling alone misses reversed knees).

### Safety filter
Words like "organs", "boxer briefs", "translucent skin" → `prohibited_content`. Use "educational 3D medical animation", "anatomy character", "grey shorts".

## Voice-first audio (auto.py default)
- Length follows the reference: 10 s base + 8 s extensions (parts = 1 + round((ref − 10) / 8), max 4 = 34 s for the $2 budget). Files: part0.mp4, part1.mp4… (each extension returns the full video).
- Order: plan (`parts[].shots[]`, one VO line per shot) → TTS per line (gemini-3.8-flash-tts, voice = plan `tts_voice` picked from pipeline/prompts/voices.txt, reference WPM from plan `voice` "~N WPM") → lines fitted into each part's window (speed-up ≤ ×1.35, else Gemini rewrites the lines) → shot timecodes + packshot (= last line start) → music (Lyria 3: clip ≤30 s $0.04, pro for longer $0.08) → video with SFX ONLY → mix (music ducked under voice, limiter) → captions aligned on the clean voice.wav.
- Always off-screen narration: references with on-camera talking or dialogue are remade as narration (lip-sync ads are out of scope of this pipeline).
- Upscaler: always realesr-animevideov3 x2 (fast, for every style; realistic x4 model is ~4x slower, too slow for batches).
- Not universal yet: English only (align.py syllables), one character (hero.png).
- Code: voice.py (timing), api.py (Gemini calls + cost), auto.py (orchestration).
- TTS prompt format: `# AUDIO PROFILE / # DIRECTOR'S NOTES / # TRANSCRIPT` + "Read ONLY the transcript", otherwise it reads the notes aloud.
- Safety: character is a 19–20 y.o. adult; if a generation is blocked the next try drops the keyframes (body close-up keyframes trip the filter). Lyria sometimes returns empty — api.gemini retries.

## QA gate and budget (cut regenerations)
- qa.py checks only the NEW segment (re-encoded cut from --from; stream copy dragged approved parts in).
- Only creepy defects block: no_text, face (no realistic/creepy skull; cartoon x-ray overlays are fine), anatomy, artifacts (melting faces, ghosts, smears). Speech in the clip doesn't block: qa.py prints speech=1, auto.py marks partN.speech and the mix mutes that part's sound effects. Lip movement isn't checked. Clothes, extra people, off-script poses are NOT checked: viewers don't notice. No per-ad planner checks.
- A failed hard check costs a regeneration only if a second skeptical pass confirms it (first pass hallucinates text/timecodes).
- If no try passes, auto.py keeps the try with the fewest confirmed fails (part0_try1.mp4… kept for inspection).
- Keyframes: full body / waist-up only; body-part close-ups as image input trip the safety filter.
- Hard cap $2 per ad: auto.py keeps a ledger <folder>/spent.txt across reruns; every API call (api.guard) and subprocess (AD_BUDGET_LEFT) stops before exceeding it; video tries are pre-checked at worst-case $0.40.

## Fidelity to the reference (planner rules)
- Character design copies the reference's construction (stick figure stays a stick figure), only small details change; style refs = frames where the character is biggest.
- Scene density matches the reference's cut rate: a VO line carries 1–3 quick visuals (`shots[].visuals`), its time split evenly; never fewer shots than the reference.
- Cartoon x-ray/bones only INSIDE the body outline; anything sticking out of the body fails QA anatomy.

- Quota: gemini-omni-1.1-flash on Tier 1 = 20 video requests per day (≈ 8 ads with 2 parts and some retries). On 429 auto.py stops; rerun the same command later to continue from where it stopped.
