"""Voiceover + music + word timings for the 30 s TikTok (Gemini TTS + OpenAI gpt-4o-transcribe check, Lyria music, align.py).
Voice-first: lines are read back to back with a short gap; their start times become the shot timecodes (out/shots.json).
Usage: python3 vo.py  →  out/voice.wav, out/music.mp3, out/words.json, out/shots.json
"""
import json, pathlib, re, subprocess
import align, oai
from api import gemini, data
import api

SR, LENGTH, VOICE = 24000, 24, "Kore"
PROFILE = "American female, about 40, marketing lead telling a short office story. Dry, deadpan wit with a smile in the voice, confident, lively, ~190 WPM, close-mic."
GAP = 0.15  # pause between lines, s
LINES = [  # one line per shot
    "My CEO asked me one question: are we number one in AI?",
    "I asked back: which AI?",
    "ChatGPT, Gemini and Google AI Mode name the same top brand for only thirty six percent of prompts.",
    "So two times out of three, at least one of them crowns someone else.",
    "Don't check one AI. Track all of them with SupaIntent.",
]
OUT = pathlib.Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)

def pcm(af, raw, fmt=()):
    return subprocess.run(["ffmpeg", "-v", "error", *fmt, "-i", "-", "-af", af, "-f", "s16le", "-ar", str(SR), "-ac", "1", "-"],
                          input=raw, capture_output=True, check=True).stdout

def heard(wav):
    """What the TTS actually said, normalized to lowercase words."""
    t = oai.transcribe(wav, "Brands: SupaIntent, ChatGPT, Gemini, Google AI Mode. Spell numbers as words.")
    return norm(t)

def norm(t):
    return re.sub(r"[^a-z0-9' ]", " ", t.lower().replace("’", "'").replace("-", " ").replace("chat gpt", "chatgpt").replace("super intent", "supaintent").replace("supa intent", "supaintent").replace("soopa intent", "supaintent").replace("201", "two hundred and one").replace("36%", "thirty six percent").replace("30%", "thirty percent").replace("g2", "g two")).split()

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
    prompt = f"# AUDIO PROFILE\n{PROFILE}\n# DIRECTOR'S NOTES\nStay in character. Read ONLY the transcript, once, no extra words.\n# TRANSCRIPT\n{spoken}"
    want = norm(spoken.replace("Soopa Intent", "SupaIntent"))
    for _ in range(8):  # TTS sometimes adds words, repeats the line or reads the profile aloud
        wav = data(gemini("gemini-3.8-flash-tts", [{"text": prompt}], responseModalities=["AUDIO"],
                          speechConfig={"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE}}}))
        if (len(wav) - 44) / 2 / SR > 0.7 * len(want) + 1.5:  # line read more than once (calm ~165 WPM narrator): the transcriber hides repeats, so check length
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
      (OUT / "music.mp3").write_bytes(data(gemini("lyria-3-clip-preview", [{"text":
        "Instrumental only, no vocals. Smart, light office-comedy groove: muted pizzicato strings, soft electric piano, tight brushed drums, round bass, a mischievous turn in the middle, confident ending, 112 BPM, 30 seconds."}],
        responseModalities=["AUDIO"])))

    words = align.words_from_script(str(voice), shots)
    (OUT / "words.json").write_text(json.dumps(words, indent=0))
    print(f"✅ {voice}, music.mp3, words.json ({len(words)} words) · 💰 OpenAI ~${oai.spent:.3f}, Gemini ~${api.spent:.2f}")
