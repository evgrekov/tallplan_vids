"""Re-voice a finished 3d/ ad without regenerating video: new OpenAI voice in the old line windows, same SFX + music,
alternating punch-in per line, new packshot, fresh captions.
Usage: python3 remake3d.py <3d/adN> <sfx_video.mp4> <out_dir> [openai_voice=cedar]
"""
import json, pathlib, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "3d"), str(ROOT / "slides")]
import align, oai, voice

SR, ZOOM = 24000, 0.07
INSTR = "Confident, energetic young male TikTok narrator, crisp and clear, natural American accent, punchy educational delivery."
src, sfx, out = pathlib.Path(sys.argv[1]), sys.argv[2], pathlib.Path(sys.argv[3])
name = sys.argv[4] if len(sys.argv) > 4 else "cedar"
out.mkdir(parents=True, exist_ok=True)
video = src / "mixed_up.mp4"
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video]))
ps = json.loads((src / "plan.json").read_text())["packshot"]

# old voice lines = sentences of the old word timings; each new line keeps the old line's window
lines, cur = [], []
for w in json.loads((src / "voice_words.json").read_text()):
    cur.append(w)
    if w["w"][-1] in ".?!": lines.append(cur); cur = []
lines += [cur] if cur else []
starts = [l[0]["s"] for l in lines]
ends = [b - 0.1 for b in starts[1:]] + [dur - 0.3]
texts = [" ".join(w["w"] for w in l) for l in lines]

print(f"🎙️  {src.name}: {len(texts)} lines → voice {name}")
track, prev, windows = bytearray(round(dur * SR) * 2), 0.0, []
for i, (s, e, t) in enumerate(zip(starts, ends, texts)):
    f = out / f"vo{i}.raw"
    if not f.exists():
        f.write_bytes(voice.fx(oai.speech(t, INSTR, name), f"{voice.TRIM},areverse,{voice.TRIM},areverse"))
    c = f.read_bytes()
    s = max(s, prev + 0.08)  # never overlap the previous line: a late line shifts instead of being cut
    if len(c) / 2 / SR > e - s:  # longer than the old window: speed up, but not into chipmunk speed
        c = voice.fx(c, f"atempo={min(1.3, len(c) / 2 / SR / max(e - s, 0.1)):.3f}")
    prev = s + len(c) / 2 / SR
    assert prev <= dur, f"line {i + 1} runs past the video end"
    o = round(s * SR) * 2
    track[o:o + len(c)] = c
    windows.append((s, prev, t))
    print(f"   {i + 1}/{len(texts)} {s:.2f}–{prev:.2f}s {t}")
ps = max(ps, windows[-1][0] - 0.05)  # the packshot comes in with the CTA line
vo = out / "voice.wav"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-", vo], input=bytes(track), check=True)

# punch-in on every other line until the packshot (the new cut), mix as in auto.py step 9
z = "+".join(f"between(t,{a},{b})" for a, b in list(zip(starts, starts[1:] + [ps]))[1::2])
body = out / "body.mp4"
print("🎞️  recut + mix...")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", sfx, "-i", src / "music.mp3", "-i", vo, "-filter_complex",
                f"[0:v]scale=w='trunc(iw*(1+{ZOOM}*({z}))/2)*2':h=-2:eval=frame,crop=720:1280[v];"
                f"[3:a]loudnorm=I=-16:TP=-1.5,asplit[v1][sc];[2:a]atrim=0:{dur},afade=t=out:st={dur - 1.5}:d=1.5,volume=0.3[m];"
                f"[m][sc]sidechaincompress=threshold=0.03:ratio=6:release=300[md];[1:a]volume=0.6[fx];"
                "[fx][md][v1]amix=inputs=3:normalize=0:duration=longest,alimiter=limit=0.89:level=false[a]",
                "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", body], check=True)

words = out / "words.json"
words.write_text(json.dumps(align.words_from_script(vo, windows)))
subprocess.run([ROOT / "3d/packshot.sh", body, str(ps)], check=True)
subprocess.run(["uv", "run", "-q", ROOT / "3d/captions.py", out / "body_final.mp4", words, out / "final.mp4"], check=True)
for f in [body, out / "body_final.mp4"]: f.unlink()
print(f"🏁 {out / 'final.mp4'} · 💰 OpenAI TTS ~${oai.spent:.3f}")
