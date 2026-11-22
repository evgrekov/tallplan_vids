"""Voiceover + music + word timings (Gemini TTS checked by OpenAI gpt-4o-transcribe, Lyria music, align.py).
Reads videos/<id>/script.json: {"lines": [...], "profile": "...", "voice": "Kore", "music": "...", "length": 24}.
Usage: uv run --with pillow python py/vo.py <id>  →  out/voice.wav, out/music.mp3, out/words.json, out/shots.json
"""
import json, pathlib, re, subprocess, sys
import align, oai
from api import gemini, data
import api

CFG = json.loads((pathlib.Path(__file__).parent.parent / "videos" / sys.argv[1] / "script.json").read_text())
SR, LENGTH, VOICE, PROFILE, LINES = 24000, CFG["length"], CFG["voice"], CFG["profile"], CFG["lines"]
GAP = 0.15  # pause between lines, s
OUT = pathlib.Path(__file__).parent.parent / "videos" / sys.argv[1] / "out"
OUT.mkdir(parents=True, exist_ok=True)

def pcm(af, raw, fmt=()):
    return subprocess.run(["ffmpeg", "-v", "error", *fmt, "-i", "-", "-af", af, "-f", "s16le", "-ar", str(SR), "-ac", "1", "-"],
                          input=raw, capture_output=True, check=True).stdout

def heard(wav):
    """What the TTS actually said, normalized to lowercase words."""
    t = oai.transcribe(wav, f"Brands: SupaIntent, ChatGPT, Gemini, Google AI Mode, G2, Reddit, Perplexity, GPTBot, OpenAI, {', '.join(CFG.get('brands', []))}. Spell numbers as words.")
    return norm(t)

def norm(t):
    return re.sub(r"[^a-z0-9' ]", " ", t.lower().replace("’", "'").replace("-", " ").replace("chat gpt", "chatgpt").replace("super intent", "supaintent").replace("supa intent", "supaintent").replace("soopa intent", "supaintent").replace("201", "two hundred and one").replace("403", "four oh three").replace("200", "two hundred").replace("gpt bot", "gptbot").replace("ecommerce", "e commerce").replace("19%", "nineteen percent").replace("18%", "eighteen percent").replace("36%", "thirty six percent").replace("30%", "thirty percent").replace("g2", "g two")).split()

def max_pause(wav):
    """Longest silence inside the line (edges ignored), s."""
    log = subprocess.run(["ffmpeg", "-i", "-", "-af", "silencedetect=n=-35dB:d=0.3", "-f", "null", "-"], input=wav, capture_output=True).stderr.decode()
    dur = (len(wav) - 44) / 2 / SR
    gaps = [(float(a), float(b)) for a, b in re.findall(r"silence_start: ([0-9.]+).*?silence_end: ([0-9.]+)", log, re.S)]
    return max([b - a for a, b in gaps if a > 0.15 and b < dur - 0.15], default=0)

def say(text):
    cache = OUT / "clips" / (re.sub(r"\W+", "_", text)[:60] + ".pcm")  # accepted reads are reused on rerun
    if cache.exists(): return cache.read_bytes()
    # spoken form: numbers as words, brand spelled phonetically (TTS says "Superintent" otherwise)
    spoken = text.replace("SupaIntent", "Soopa Intent").replace("201", "two hundred and one")
    prompt = f"# AUDIO PROFILE\n{PROFILE}\n# DIRECTOR'S NOTES\nStay in character. American English only. Read ONLY the transcript, once, at an even pace, no extra words.\n# TRANSCRIPT\n{spoken}"
    want = norm(spoken.replace("Soopa Intent", "SupaIntent"))
    for _ in range(8):  # TTS sometimes adds words, repeats the line or reads the profile aloud
        wav = data(gemini("gemini-3.8-flash-tts", [{"text": prompt}], responseModalities=["AUDIO"],
                          speechConfig={"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE}}}))
        if (len(wav) - 44) / 2 / SR > 0.42 * len(want) + 0.9:  # line read more than once (calm ~165 WPM narrator): the transcriber hides repeats, so check length
            print(f"🔁 {(len(wav) - 44) / 2 / SR:.1f}s is too long, retrying"); continue
        got = heard(wav)
        if got != want and not (len(got) == len(want) and sum(a != b for a, b in zip(got, want)) <= 1):  # exact words, one substitution for brand spelling
            print(f"🔁 heard \"{' '.join(got)}\", retrying"); continue
        if (gap := max_pause(wav)) > 0.6:
            print(f"🔁 {gap:.1f}s pause inside the line, retrying"); continue
        break
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

    if not (OUT / "music.mp3").exists():
      print("🎵 music...")
      (OUT / "music.mp3").write_bytes(data(gemini("lyria-3-clip-preview", [{"text": CFG["music"]}],
        responseModalities=["AUDIO"])))

    words = align.words_from_script(str(voice), shots)
    (OUT / "words.json").write_text(json.dumps(words, indent=0))
    print(f"✅ {voice}, music.mp3, words.json ({len(words)} words) · 💰 OpenAI ~${oai.spent:.3f}, Gemini ~${api.spent:.2f}")
