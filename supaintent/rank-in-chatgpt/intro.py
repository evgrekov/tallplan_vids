"""Prepends the spoken question to the existing voice without regenerating the rest (one TTS call, ~$0.01).
Usage: python3 intro.py  →  out/voice.wav, out/shots.json, out/words.json with the intro line first
"""
import json, subprocess
import align, api
from vo import say, SR, GAP, OUT

TEXT = "How to rank your brand in ChatGPT? Here are three concrete steps."
shots = json.loads((OUT / "shots.json").read_text())
assert shots[0]["vo"] != TEXT, "intro already added"
clip = say(TEXT)
d = len(clip) / 2 / SR + GAP  # everything after the intro moves by this much
voice = OUT / "voice.wav"
old = subprocess.run(["ffmpeg", "-v", "error", "-i", voice, "-f", "s16le", "-ar", str(SR), "-ac", "1", "-"], capture_output=True, check=True).stdout
lead = int(0.2 * SR) * 2
track = old[:lead] + clip + bytes(int(GAP * SR) * 2) + old[lead:]
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-", voice], input=track, check=True)
shots = [{"start": 0.2, "end": round(0.2 + len(clip) / 2 / SR, 2), "vo": TEXT}] + \
        [{**s, "start": round(s["start"] + d, 2), "end": round(s["end"] + d, 2)} for s in shots]
(OUT / "shots.json").write_text(json.dumps(shots, indent=1))
words = align.words_from_script(str(voice), [(s["start"], s["end"], s["vo"]) for s in shots])
(OUT / "words.json").write_text(json.dumps(words, indent=0))
print(f"✅ intro {d:.2f}s added, {len(words)} words · 💰 ~${api.spent:.2f}")
