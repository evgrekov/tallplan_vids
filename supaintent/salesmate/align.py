"""Word timings from real audio: voice-band loudness envelope splits speech into regions,
gemini-3.8-flash transcribes each region separately, words are spread by syllables and snapped to loudness dips.
(Raw Gemini word timestamps drift up to ~1 s — never use them.)
Usage: python3 align.py <video.mp4> <words.json>
"""
import base64, json, pathlib, re, subprocess, sys, tempfile, urllib.request

STEP = 0.01  # envelope resolution, s

def envelope(video):
    """Voice-band (300–3400 Hz) RMS in dB every 10 ms — music outside the band does not count as speech."""
    log = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vn", "-ac", "1", "-af",
                          "aresample=16000,highpass=f=300,lowpass=f=3400,asetnsamples=160,astats=metadata=1:reset=1,"
                          "ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-", "-f", "null", "-"],
                         capture_output=True, text=True).stdout
    return [float(x) if x != "-inf" else -99.0 for x in re.findall(r"RMS_level=(\S+)", log)]

def speech_regions(env, thr=-36, gap=0.12, min_len=0.1):
    on = [v > thr for v in env]
    regions, i = [], 0
    while i < len(on):
        if on[i]:
            j = i
            while j < len(on) and (on[j] or any(on[j:j + int(gap / STEP)])): j += 1
            if (j - i) * STEP >= min_len: regions.append((i * STEP, j * STEP))
            i = j
        else: i += 1
    return regions

def transcribe(video, regions):
    tmp, parts = pathlib.Path(tempfile.mkdtemp()), []
    for i, (s, e) in enumerate(regions):
        p = tmp / f"{i}.flac"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(max(0, s - 0.05)), "-to", str(e + 0.05), "-i", video,
                        "-vn", "-ac", "1", "-ar", "16000", str(p)], check=True)
        parts += [{"text": f"Segment {i}:"}, {"inline_data": {"mime_type": "audio/flac", "data": base64.b64encode(p.read_bytes()).decode()}}]
    parts.append({"text": f"Transcribe each of the {len(regions)} audio segments verbatim (only speech actually in it; empty string if no speech). "
                          "Write the brand as one word SupaIntent. Return ONLY a JSON array of strings, one per segment in order."})
    key = re.search(r"GEMINI_API_KEY=(\S+)", (pathlib.Path(__file__).parents[2] / ".env").read_text()).group(1)
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent",
                                 json.dumps({"contents": [{"parts": parts}], "generationConfig": {"responseMimeType": "application/json", "temperature": 0}}).encode(),
                                 {"Content-Type": "application/json", "X-goog-api-key": key})
    r = json.load(urllib.request.urlopen(req, timeout=300))
    u = r["usageMetadata"]
    print(f"🗣️  transcribed {len(regions)} speech regions · 💰 ~${u['promptTokenCount'] * 0.75e-6 + (u['candidatesTokenCount'] + u.get('thoughtsTokenCount', 0)) * 3.75e-6:.4f}")
    return json.loads(r["candidates"][0]["content"]["parts"][0]["text"])

def syllables(w):
    return max(1, len(re.findall(r"[aeiouy]+", w.lower().rstrip("e")))) + 0.3

def snap(t, env, win=0.15):
    """Move a word boundary to the quietest 10 ms within ±win."""
    i0, i1 = max(0, int((t - win) / STEP)), min(len(env), int((t + win) / STEP))
    return min(range(i0, i1), key=lambda i: env[i]) * STEP if i1 > i0 else t

def spread(env, regions, texts):
    """Words of each region spread by syllables, boundaries snapped to loudness dips."""
    out = []
    for (s, e), ws in zip(regions, texts):
        if not ws: continue
        wts = [syllables(w) for w in ws]
        k, acc, cuts = (e - s) / sum(wts), s, [s]
        for x in wts[:-1]:
            acc += x * k
            cuts.append(max(cuts[-1] + 0.06, snap(acc, env)))
        cuts.append(e)
        out += [{"w": w, "s": round(a, 3), "e": round(b, 3)} for w, a, b in zip(ws, cuts, cuts[1:])]
    return out

def words_from_audio(video):
    env = envelope(video)
    regions = speech_regions(env)
    texts = [x.split() for x in transcribe(video, regions)]
    for a, b in zip(texts, texts[1:]):  # ±0.05 s padding can let a boundary word be heard in both segments
        if a and b and a[-1].lower().strip(",.?!") == b[0].lower().strip(",.?!"):
            a.pop()
    return spread(env, regions, texts)

def words_from_script(wav, lines):
    """Voice-first: the text is known, only timing comes from the audio. lines = [(window_start, window_end, text)]."""
    env = envelope(wav)
    regions = speech_regions(env)
    spans = []
    for a, b, _ in lines:  # speech actually spoken inside the line's window
        inside = [(s, e) for s, e in regions if s < b and e > a]
        spans.append((max(a, inside[0][0]), min(b, inside[-1][1])) if inside else (a, b))
    return spread(env, spans, [t.split() for *_, t in lines])

if __name__ == "__main__":
    words = words_from_audio(sys.argv[1])
    json.dump(words, open(sys.argv[2], "w"), indent=0)
    print(f"🎯 {len(words)} words → {sys.argv[2]}")
