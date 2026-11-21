"""Voice-first timing: every shot has one TTS line and lasts as long as that line, so voice, captions and packshot never drift.
Timeline (s): base video 0–10, each extension +8; the last line (CTA) plays under the packshot."""
import base64, json, re, subprocess
from api import gemini, data

SR = 24000  # TTS output: s16 mono
BASE, EXT = 10, 8  # video model: base clip and extension length, s
GAP, MAX_GAP = 0.12, 0.6  # pause between lines: minimum / maximum when spreading spare time
FAST, EMPTY = 1.35, 0.7  # rewrite the lines if they need more speed-up than FAST or fill less than EMPTY of the window
TRIM = "silenceremove=start_periods=1:start_threshold=-45dB"

def fx(pcm, af):
    return subprocess.run(["ffmpeg", "-v", "error", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af", af,
                           "-f", "s16le", "-"], input=pcm, capture_output=True, check=True).stdout

def heard(wav):
    """Word count of what the TTS actually said."""
    t = gemini("gemini-3.8-flash", [{"inline_data": {"mime_type": "audio/wav", "data": base64.b64encode(wav).decode()}},
                                    {"text": "Transcribe this speech verbatim. Output only the words."}], temperature=0)[0]["text"]
    return len(t.split())

def say(text, plan):
    wpm_ref = int(re.search(r"(\d+)\s*WPM", plan["voice"]).group(1))  # pace measured from the reference by the planner
    prompt = (f"# AUDIO PROFILE\n{plan['voice']}\n# DIRECTOR'S NOTES\nPunchy TikTok narrator, ~{wpm_ref} words per minute. "
              f"Read ONLY the transcript.\n# TRANSCRIPT\n{text}")
    for _ in range(3):
        wav = data(gemini("gemini-3.8-flash-tts", [{"text": prompt}], responseModalities=["AUDIO"],
                          speechConfig={"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": plan["tts_voice"]}}}))
        # TTS returns a WAV file: decode it, raw-reading its header bytes makes clicks
        pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", "-", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-"],
                             input=wav, capture_output=True, check=True).stdout
        if heard(wav) <= len(text.split()) + 1: break  # more words than the line = it also read the profile/notes aloud
        print(f"🔁 TTS read extra words for \"{text[:40]}…\", retrying")
    tempo = max(0.85, min(wpm_ref * len(pcm) / 2 / SR / 60 / len(text.split()), 1.3))  # model ignores exact pace: fit to reference
    # short fades: a clip cut mid-waveform clicks at its edges
    return fx(pcm, f"{TRIM},areverse,{TRIM},afade=t=in:d=0.02,areverse,afade=t=in:d=0.01,atempo={tempo:.3f}")

def rewrite(lines, words):
    q = (f"Rewrite these TikTok voiceover lines (one per shot) to about {words} words in total. Keep the meaning, the order and "
         f"exactly {len(lines)} lines; the last line still ends with \"in TallPlan.\" if it did. Output a JSON array of strings.\n{json.dumps(lines)}")
    return json.loads(gemini("gemini-3.8-flash", [{"text": q}], responseMimeType="application/json")[0]["text"])

def part(shots, window, plan):
    """TTS each line, fit the lines into the window; returns clips + absolute start times, rewriting lines when they don't fit."""
    span = window[1] - window[0]
    for _ in range(3):
        lines = [s["vo"] for s in shots]
        clips = [say(l, plan) for l in lines]
        avail = span - GAP * (len(lines) - 1)
        ratio = sum(map(len, clips)) / 2 / SR / avail
        if EMPTY <= ratio <= FAST: break
        words = round(sum(len(l.split()) for l in lines) / ratio * (1 if ratio > FAST else 0.9))
        print(f"✍️  lines fill {ratio:.0%} of the window → rewriting to ~{words} words")
        for s, l in zip(shots, rewrite(lines, words)): s["vo"] = l
    else:
        print("⚠️  lines still don't fit, using the last take")
    if ratio > 1:
        clips = [fx(c, f"atempo={ratio:.3f}") for c in clips]
    dur = [len(c) / 2 / SR for c in clips]
    gap = min(MAX_GAP, (span - sum(dur)) / (len(dur) - 1)) if len(dur) > 1 else 0
    starts = [window[0] + sum(dur[:i]) + gap * i for i in range(len(dur))]
    return clips, starts

def spans(n):
    """(start, end) of each video part on the timeline."""
    return [(0, BASE)] + [(BASE + EXT * i, BASE + EXT * (i + 1)) for i in range(n - 1)]

def build(plan, out):
    """Writes the voice track and stores per-shot timecodes ("t", part-relative) and the packshot start in the plan."""
    parts = spans(len(plan["parts"]))
    track = bytearray(parts[-1][1] * SR * 2)
    for k, (p, (lo, hi)) in enumerate(zip(plan["parts"], parts)):
        shots = p["shots"]
        last = k == len(parts) - 1  # the last part keeps a tail so the CTA ends before the video does
        clips, starts = part(shots, (lo + (0.2 if k == 0 else 0), hi - (0.4 if last else 0.2)), plan)
        for c, s in zip(clips, starts):
            i = int(s * SR) * 2
            track[i:i + len(c)] = c
        bounds = [lo] + starts[1:] + [hi]
        for s, a, b in zip(shots, bounds, bounds[1:]): s["t"] = [round(a - lo, 2), round(b - lo, 2)]
        if last: plan["packshot"] = round(starts[-1] - 0.05, 2)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-", out], input=bytes(track), check=True)
    print(f"🎙️  {out.name}: shots timed to voice, packshot at {plan['packshot']}s")
