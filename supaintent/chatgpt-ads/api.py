"""Gemini REST helpers shared by the pipeline; `spent` accumulates the estimated $ of this process."""
import base64, json, os, pathlib, re, urllib.request

KEY = re.search(r"GEMINI_API_KEY=(\S+)", (pathlib.Path(__file__).parents[2] / ".env").read_text()).group(1)
spent = 0.0
LIMIT = float(os.environ.get("AD_BUDGET_LEFT", "inf"))  # hard $ cap; auto.py sets it for itself and for its subprocesses

def guard(cost):
    if spent + cost > LIMIT:
        raise SystemExit(f"💸 budget cap reached (spent ~${spent:.2f} of ${LIMIT:.2f}), stopping")

def gemini(model, parts, **cfg):
    global spent
    guard(0.08 if model.startswith("lyria") else 0.05)  # worst single call of that kind
    req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                                 json.dumps({"contents": [{"parts": parts}], "generationConfig": cfg}).encode(),
                                 {"Content-Type": "application/json", "X-goog-api-key": KEY})
    for _ in range(3):  # generation models sometimes return an empty candidate: retry
        r = json.load(urllib.request.urlopen(req, timeout=900))
        if "content" in r["candidates"][0]: break
        print(f"🔁 {model}: empty answer ({r['candidates'][0].get('finishReason')}), retrying")
    u = r["usageMetadata"]
    if model.startswith("lyria"):
        spent += 0.08 if "pro" in model else 0.04  # Lyria 3: flat per request (clip / full song)
    else:  # shortcut: image output ~$30/M and TTS at text rates are estimates, verify in billing
        image = "image" in model
        spent += u["promptTokenCount"] * (0.5e-6 if image else 0.75e-6) + \
                 (u.get("candidatesTokenCount", 0) + u.get("thoughtsTokenCount", 0)) * (30e-6 if image else 3.75e-6)
    return r["candidates"][0]["content"]["parts"]

def data(parts):
    return base64.b64decode(next(p["inlineData"]["data"] for p in parts if "inlineData" in p))

def file(path, mime=None):
    mime = mime or {"mp4": "video/mp4", "png": "image/png", "jpg": "image/jpeg"}[str(path).rsplit(".", 1)[1]]
    return {"inline_data": {"mime_type": mime, "data": base64.b64encode(pathlib.Path(path).read_bytes()).decode()}}
