# TikTok script: "Your YouTube videos are invisible to ChatGPT"

Format: vertical 9:16 (1080×1920), 30 seconds, fast cuts every 2–4 s, voiceover + big on-screen captions.
Tone: fast, playful, "wait, what?" energy. Brand color: #0053db. Data: SupaIntent, 162k AI answers, Aug–Oct 2026; Top AI Citation Domains tool, Nov 1, 2026.

## Files in this folder

| File | What it is |
|---|---|
| `logos/supaintent-logo.svg`, `logos/supaintent-logo-512.png` | Official SupaIntent logo (from the site repo) |
| `logos/chatgpt.png`, `logos/google-ai-mode.png` | AI engine icons used on supaintent.com |
| `screenshots/top-domains-chatgpt-header.png` | supaintent.com/tools/top-domains, ChatGPT tab, Nov 1, 2026 |
| `screenshots/top-domains-chatgpt-table.png` | Same, ranking close-up: g2 24%, trustpilot 12%, capterra 11%, bbb 6%, reddit 6%. No YouTube in the list |
| `screenshots/top-domains-google-ai-mode.png` | Same tool, Google AI Mode tab, Oct 31: youtube.com #1 (28%), reddit #2 (22%) |
| `screenshots/top-domains-all-models.png` | Same tool, All models |
| `screenshots/google-ai-mode-answer.png` | Real Google AI Mode answer citing Reddit + YouTube |
| `screenshots/youtube-radar-channels.png` | SupaIntent YouTube Radar inside the product |

## Script

Timecodes come from the generated voice (`out/shots.json`): cut each shot on the start of its line. The voice ends at 27.1 s, the last ~3 s are the logo end card under the music.

| Time | Visual | Voiceover | On-screen text |
|---|---|---|---|
| 0.2–3.0 s | **Hook.** Creator-style face/hand shot or bold text on #0053db. Quick zoom-in. | "Making YouTube videos to show up in ChatGPT? Stop." | **STOP making YouTube videos for ChatGPT ✋** |
| 3.0–6.1 s | ChatGPT logo pops in, YouTube play button shatters / fades to grey. | "We checked 162,000 AI answers." | **162,000 AI answers analyzed** |
| 6.1–10.1 s | Big counter animates 0 → **0.2%** next to ChatGPT icon. | "YouTube in ChatGPT answers? Zero point two percent. Basically never." | **ChatGPT → YouTube: 0.2% 😬** |
| 10.1–14.3 s | `top-domains-chatgpt-table.png` slides up. Scroll down the list; circle the empty space where YouTube "should" be. | "Here's what ChatGPT actually reads: G2, Trustpilot, Capterra, and Reddit." | **YouTube? Not even in the list.** |
| 14.3–16.4 s | Highlight / glow row 5 `reddit.com 6%`. Reddit icon bounces. | "Reddit makes the cut. Your video doesn't." | **Reddit ✅ YouTube ❌** |
| 16.4–16.8 s | Whip-pan / record-scratch sound. Text "BUT…" | "But wait." | **BUT…** |
| 16.8–20.8 s | Switch tab to `top-domains-google-ai-mode.png`; youtube.com #1 at 28% zooms in. Optionally flash `google-ai-mode-answer.png`. | "In Google's AI answers, YouTube is number one. Twenty-eight percent." | **Google AI → YouTube #1 (28%) 🔥** |
| 20.8–24.4 s | Split screen: ChatGPT side with Reddit/G2 icons, Google side with YouTube icon. | "So: Reddit and reviews for ChatGPT. YouTube for Google." | **ChatGPT = Reddit & reviews · Google = YouTube** |
| 24.4–30.0 s | `top-domains-chatgpt-header.png` with cursor clicking the engine tabs, then SupaIntent logo end card. | "Check what every AI cites, free, at SupaIntent." | **Free tool: supaintent.com/tools/top-domains** + logo |

## Notes for the edit

- Keep every claim tied to a screenshot; the numbers are real (0.2% and 162k from our dataset, 28% and the ChatGPT list from the tool on Oct 31 / Nov 1, 2026).
- Don't say "YouTube is useless": the twist (YouTube wins Google) is what makes the video honest and shareable.
- Suggested caption: "ChatGPT ignores your YouTube channel. Google doesn't. 👀 #SEO #ChatGPT #AISearch #GEO #marketingtips"
- Suggested sound: trending upbeat track, record-scratch at 17 s.

## Audio and captions (ready, same pipeline as go_tall_tiktok/3d)

| File | What it is |
|---|---|
| `out/voice.wav` | Voiceover, 30.0 s, Gemini TTS voice "Puck". Every line was checked by transcription: no repeats or extra words (one small "Okay" before "so Reddit and reviews…") |
| `out/music.mp3` | Instrumental bed, Lyria 3 clip, ~30.8 s |
| `out/audio_mix.m4a` | Voice + music ducked under the voice, limiter: drop it straight onto the timeline |
| `out/shots.json` | Start/end of every VO line = shot timecodes |
| `out/words.json` | Word timings for karaoke captions |
| `out/preview_captions.mp4` | Blank blue preview with mix + burned captions, to check sync |

Workflow:
1. Edit the visuals to `out/shots.json`, put `out/audio_mix.m4a` under them, export 1080×1920 → `edit.mp4` (audio included).
2. Burn captions: `uv run captions.py edit.mp4 out/words.json final.mp4` (Montserrat Black, white + black stroke, spoken word yellow #F7FF14, 2–3 words, at 70% height).
3. Need to change a line? Edit `LINES` in `vo.py`, run `python3 vo.py` (~$0.10, regenerates voice, music, shots, words), then step 2.

Notes: the TTS pronounces the brand closer to "Super Intent" even with a phonetic hint; captions always show "SUPAINTENT". The Gemini key is in `rules.md` (read by `api.py` and `align.py`).
