"""Voiceover + music + word timings for the 30 s TikTok (approach from go_tall_tiktok/3d: Gemini TTS, Lyria, align.py).
Voice-first: lines are read back to back with a short gap; their start times become the shot timecodes (out/shots.json).
Usage: python3 vo.py  →  out/voice.wav, out/music.mp3, out/words.json, out/shots.json
"""
import base64, json, pathlib, re, subprocess
import align
from api import gemini, data
import api

SR, LENGTH, VOICE = 24000, 26, "Fenrir"
PROFILE = "American male, late 20s, excitable hacker-style tech explainer, fast and intense, ~195 WPM, dry close-mic."
GAP = 0.15  # pause between lines, s
LINES = [  # one line per shot
    "ChatGPT doesn't search what you typed.",
    'In eighteen thousand ChatGPT searches, only five percent repeat the prompt word for word.',
    'Twenty-seven percent add the year. Twelve percent ask for official info.',
    'So put the answer at the top and keep your facts current.',
    'See the real searches behind your prompts with SupaIntent.',
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
    return re.sub(r"[^a-z0-9' ]", " ", t.lower().replace("-", " ").replace("chat gpt", "chatgpt").replace("super intent", "supaintent").replace("g2", "g two")).split()

def first_half(wav):
    log = subprocess.run(["ffmpeg", "-i", "-", "-af", "silencedetect=n=-35dB:d=0.15", "-f", "null", "-"], input=wav, capture_output=True).stderr.decode()
    ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", log)]
    dur = (len(wav) - 44) / 2 / SR  # TTS returns 16-bit mono wav at SR
    cut = min(ends, key=lambda e: abs(e - dur / 2))
    return subprocess.run(["ffmpeg", "-v", "error", "-i", "-", "-t", str(cut), "-f", "wav", "-"], input=wav, capture_output=True, check=True).stdout

def say(text):
    cache = OUT / "clips" / (re.sub(r"\W+", "_", text)[:60] + ".pcm")  # accepted reads are reused on rerun
    if cache.exists(): return cache.read_bytes()
    # spoken form: numbers as words, brand spelled phonetically (TTS says "Superintent" otherwise)
    spoken = text.replace("SupaIntent", "Soopa Intent").replace("162,000", "one hundred sixty-two thousand")
    prompt = f"# AUDIO PROFILE\n{PROFILE}\n# DIRECTOR'S NOTES\nStay in character. Read ONLY the transcript, once, no extra words.\n# TRANSCRIPT\n{spoken}"
    want = norm(spoken.replace("Soopa Intent", "SupaIntent"))
    for _ in range(6):  # TTS sometimes adds words, repeats the line or reads the profile aloud
        wav = data(gemini("gemini-3.8-flash-tts", [{"text": prompt}], responseModalities=["AUDIO"],
                          speechConfig={"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE}}}))
        got = heard(wav)
        if abs(len(got) - 2 * len(want)) <= 2 and len(set(got) ^ set(want)) <= 2:  # the line read twice: keep the first read, cut at the pause nearest the middle
            wav = first_half(wav); break
        if len(set(got) ^ set(want)) <= 2 and abs(len(got) - len(want)) <= 1: break  # small slack for brand/ASR spelling
        print(f"🔁 heard \"{' '.join(got)}\", retrying")
    else:
        raise SystemExit(f"❌ TTS failed on: {text}")
    trim = "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse"
    cache.parent.mkdir(exist_ok=True)
    cache.write_bytes(clip := pcm(trim, wav))
    return clip

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
        "Instrumental only, no vocals. Retro synthwave, driving arpeggiated bass, gated snare, neon 80s vibe, 118 BPM, 30 seconds."}],
        responseModalities=["AUDIO"])))

    words = align.words_from_script(str(voice), shots)
    (OUT / "words.json").write_text(json.dumps(words, indent=0))
    print(f"✅ {voice}, music.mp3, words.json ({len(words)} words) · 💰 ~${api.spent:.2f}")
