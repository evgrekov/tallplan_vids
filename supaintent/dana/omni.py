#!/usr/bin/env python3
"""Animate a keyframe with gemini-omni-1.2-flash (Interactions API), image = first frame. 360p by default, then ./upscale.sh.
Usage: omni.py <prompt.txt> <out.mp4> --image keyframes/s1.png [--res 360p] [--dur 5s]
"""
import argparse, base64, json, pathlib, re, urllib.request

ap = argparse.ArgumentParser()
ap.add_argument("prompt"); ap.add_argument("out")
ap.add_argument("--image", action="append", default=[]); ap.add_argument("--res", default="360p"); ap.add_argument("--dur", default="5s")
a = ap.parse_args()

key = re.search(r"GEMINI_API_KEY=(\S+)", (pathlib.Path(__file__).parents[2] / ".env").read_text()).group(1)
inp = [{"type": "image", "mime_type": "image/png", "data": base64.b64encode(open(p, "rb").read()).decode()} for p in a.image]
inp.append({"type": "text", "text": pathlib.Path(a.prompt).read_text().strip()})
body = {"model": "gemini-omni-1.2-flash", "input": inp,
        "response_format": {"type": "video", "aspect_ratio": "9:16", "resolution": a.res, "duration": a.dur}}

print(f"🎬 generating {a.out} ({a.res}, {a.dur})...")
req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/interactions",
                             json.dumps(body).encode(), {"Content-Type": "application/json", "x-goog-api-key": key})
try:
    r = json.load(urllib.request.urlopen(req, timeout=900))
except urllib.error.HTTPError as e:
    raise SystemExit(f"❌ {e.code} {e.read().decode()}")

u = r["usage"]  # 1.2 Flash: output $12/M, input $1.50/M
cost = u["total_output_tokens"] * 12e-6 + u.get("total_thought_tokens", 0) * 12e-6 + u["total_input_tokens"] * 1.5e-6
video = next(c["data"] for s in r["steps"] if s["type"] == "model_output" for c in s["content"] if c["type"] == "video")
pathlib.Path(a.out).write_bytes(base64.b64decode(video))
print(f"✅ {a.out} · 💰 ~${cost:.3f}")
