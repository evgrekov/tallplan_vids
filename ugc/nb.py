#!/usr/bin/env python3
"""One-shot image edit with Nano Banana Pro (all changes in one prompt, never layered edits).
Usage: nb.py <prompt.txt> <out_prefix> <image> [<image> ...] [--n 4]
Writes <out_prefix>_1.png … _n.png (existing files are kept).
"""
import argparse, base64, json, pathlib, re, urllib.request

ap = argparse.ArgumentParser()
ap.add_argument("prompt"); ap.add_argument("out"); ap.add_argument("images", nargs="+"); ap.add_argument("--n", type=int, default=4)
a = ap.parse_args()

key = re.search(r"GEMINI_API_KEY=(\S+)", (pathlib.Path(__file__).resolve().parent.parent / ".env").read_text()).group(1)
parts = [{"inline_data": {"mime_type": "image/png", "data": base64.b64encode(open(p, "rb").read()).decode()}} for p in a.images]
body = {"contents": [{"parts": [*parts, {"text": pathlib.Path(a.prompt).read_text().strip()}]}],
        "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "9:16"}}}

for i in range(1, a.n + 1):
    out = pathlib.Path(f"{a.out}_{i}.png")
    if out.exists(): continue
    print(f"🍌 {out} ({i}/{a.n})...", flush=True)
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/nano-banana-pro-preview:generateContent",
                                 json.dumps(body).encode(), {"Content-Type": "application/json", "x-goog-api-key": key})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=300))
        img = next(p["inlineData"]["data"] for p in r["candidates"][0]["content"]["parts"] if "inlineData" in p)
    except (urllib.error.HTTPError, KeyError, StopIteration) as e:
        print(f"❌ {e.read().decode()[:300] if hasattr(e, 'read') else r}"); continue
    out.write_bytes(base64.b64decode(img))
    print(f"✅ {out}  tokens={r.get('usageMetadata', {}).get('candidatesTokenCount')}")
