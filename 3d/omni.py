#!/usr/bin/env python3
"""Generate or extend a video with Gemini Omni (Interactions API), gemini-omni-1.1-flash by default.
Usage: omni.py <prompt.txt> <out.mp4> [--image man.png --image keyframes/pose.png ...] [--res 360p] [--prev <interaction_id>] [--model gemini-omni-1.2-flash]
"""
import argparse, base64, json, pathlib, re, urllib.request

ap = argparse.ArgumentParser()
ap.add_argument("prompt"); ap.add_argument("out")
ap.add_argument("--image", action="append", default=[]); ap.add_argument("--res", default="360p"); ap.add_argument("--prev")
ap.add_argument("--model", default="gemini-omni-1.1-flash")
a = ap.parse_args()

here = pathlib.Path(__file__).parent
key = re.search(r"GEMINI_API_KEY=(\S+)", (here.parent / ".env").read_text()).group(1)
inp = [{"type": "text", "text": pathlib.Path(a.prompt).read_text().strip()}]
inp[:0] = [{"type": "image", "mime_type": "image/png", "data": base64.b64encode(open(p, "rb").read()).decode()} for p in a.image]
body = {"model": a.model, "input": inp,
        "response_format": {"type": "video", "aspect_ratio": "9:16", "resolution": a.res}}
if a.prev:
    body["previous_interaction_id"] = a.prev

print(f"🎬 generating {a.out} ({a.res}{', extending ' + a.prev if a.prev else ''})...")
req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/interactions",
                             json.dumps(body).encode(), {"Content-Type": "application/json", "x-goog-api-key": key})
try:
    r = json.load(urllib.request.urlopen(req, timeout=900))
except urllib.error.HTTPError as e:
    raise SystemExit(f"❌ {e.code} {e.read().decode()}")

u = r["usage"]
cost = u["total_output_tokens"] * 17.5e-6 + u.get("total_thought_tokens", 0) * 9e-6 + u["total_input_tokens"] * 1.5e-6
video = next(c["data"] for s in r["steps"] if s["type"] == "model_output" for c in s["content"] if c["type"] == "video")
pathlib.Path(a.out).write_bytes(base64.b64decode(video))
print(f"✅ {a.out} · id={r['id']} · 💰 ~${cost:.3f}")
