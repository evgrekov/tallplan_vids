"""Voiceover + music + word timings for the 30 s TikTok (approach from go_tall_tiktok/3d: Gemini TTS, Lyria, align.py).
Voice-first: lines are read back to back with a short gap; their start times become the shot timecodes (out/shots.json).
Usage: python3 vo.py  →  out/voice.wav, out/music.mp3, out/words.json, out/shots.json
"""
import base64, json, pathlib, re, subprocess
import align
from api import gemini, data
import api

SR, LENGTH, VOICE = 24000, 32, "Puck"  # Puck = upbeat male
PROFILE = "American male, late 20s, bright and playful TikTok explainer, very energetic, ~190 WPM, dry close-mic."
GAP = 0.15  # pause between lines, s
LINES = [  # one line per shot, same order as SCRIPT.md
    "ChatGPT isn't reading your website.",
    "We checked 162,000 AI answers. It reads G2, Trustpilot, Capterra and Reddit.",
    "So, step one: reviews on G2 and Capterra, and real answers in Reddit threads.",
    "Step two: get into the best tools lists. ChatGPT copies them.",
    "Step three: on your site, answer the question in one sentence, with a real number. That's the line it quotes.",
    "And check daily: about a third of today's brands are gone tomorrow.",
    "See who ChatGPT cites in your niche, free, at SupaIntent.",
]
OUT = pathlib.Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)

def pcm(af, raw, fmt=()):
    return subprocess.run(["ffmpeg", "-v", "error", *fmt, "-i", "-", "-af", af, "-f", "s16le", "-ar", str(SR), "-ac", "1", "-"],
                          input=raw, capture_output=True, check=True).stdout

def heard(wav):
    """What the TTS actually said, normalized to lowercase words."""
    t = gemini("gemini-3.8-flash", [{"inline_data": {"mime_type": "audio/wav", "data": base64.b64encode(wav).decode()}},
                                    {"text": "Transcribe this speech verbatim, numbers spelled as words. Output only the words."}], temperature=0)[0]["text"]
    return norm(t)

def norm(t):
    return re.sub(r"[^a-z0-9' ]", " ", t.lower().replace("-", " ").replace("chat gpt", "chatgpt").replace("g2", "g two")).split()

def say(text):
    # spoken form: numbers as words, brand spelled phonetically (TTS says "Superintent" otherwise)
    spoken = text.replace("SupaIntent", "Soopa Intent").replace("162,000", "one hundred sixty-two thousand")
    prompt = f"# AUDIO PROFILE\n{PROFILE}\n# DIRECTOR'S NOTES\nPunchy TikTok narrator. Read ONLY the transcript, once, no extra words.\n# TRANSCRIPT\n{spoken}"
    want = norm(spoken.replace("Soopa Intent", "SupaIntent"))
    for _ in range(6):  # TTS sometimes adds words, repeats the line or reads the profile aloud
        wav = data(gemini("gemini-3.8-flash-tts", [{"text": prompt}], responseModalities=["AUDIO"],
                          speechConfig={"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE}}}))
        got = heard(wav)
        if len(set(got) ^ set(want)) <= 2 and abs(len(got) - len(want)) <= 1: break  # small slack for brand/ASR spelling
        print(f"🔁 heard \"{' '.join(got)}\", retrying")
    else:
        raise SystemExit(f"❌ TTS failed on: {text}")
    trim = "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse"
    return pcm(trim, wav)

if __name__ == "__main__":
    clips = []
    for text in LINES:
        print(f"🎙️  {text}")
        clips.append(say(text))
    total = sum(len(c) for c in clips) / 2 / SR + GAP * (len(clips) - 1) + 0.2
    tempo = max(1, total / (LENGTH - 0.5))
    assert tempo <= 1.35, f"voice is {total:.1f}s, too long for {LENGTH}s: shorten the lines"
    if tempo > 1:
        print(f"⏩ speeding voice up x{tempo:.2f}")
        clips = [pcm(f"atempo={tempo:.3f}", c, ("-f", "s16le", "-ar", str(SR), "-ac", "1")) for c in clips]
    track, t, shots = bytearray(LENGTH * SR * 2), 0.2, []
    for text, c in zip(LINES, clips):
        i = int(t * SR) * 2
        track[i:i + len(c)] = c
        shots.append((round(t, 2), round(t + len(c) / 2 / SR, 2), text))
        t += len(c) / 2 / SR + GAP
    (OUT / "shots.json").write_text(json.dumps([{"start": a, "end": b, "vo": x} for a, b, x in shots], indent=1))
    voice = OUT / "voice.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-", voice], input=bytes(track), check=True)

    print("🎵 music...")
    (OUT / "music.mp3").write_bytes(data(gemini("lyria-3-clip-preview", [{"text":
        "Instrumental only, no vocals. Upbeat bouncy TikTok tech-explainer beat, 120 BPM, playful synth plucks, punchy drums, 30 seconds."}],
        responseModalities=["AUDIO"])))

    words = align.words_from_script(str(voice), shots)
    (OUT / "words.json").write_text(json.dumps(words, indent=0))
    print(f"✅ {voice}, music.mp3, words.json ({len(words)} words) · 💰 ~${api.spent:.2f}")
