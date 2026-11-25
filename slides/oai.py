"""OpenAI image generation (key from ../.env). gpt-image-2.6-flare: text in $5/M, image out $30/M; medium ~$0.035 per 1024x1536 image (low ~$0.02)."""
import base64, json, pathlib, re, subprocess, urllib.request

KEY = re.search(r"OPENAI_API_KEY=(\S+)", (pathlib.Path(__file__).parent.parent / ".env").read_text()).group(1)
spent = 0.0  # $ of this process on the OpenAI account (estimate from usage)
MODEL = "gpt-image-2.6-flare"  # best quality; the price is set by quality (output tokens), not the model

def image(prompt, out, quality="medium", size="1024x1536"):
    """Writes a PNG (default 1024x1536); cost goes to `spent`."""
    req = urllib.request.Request("https://api.openai.com/v1/images/generations",
                                 json.dumps({"model": MODEL, "prompt": prompt, "size": size, "quality": quality}).encode(),
                                 {"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    r = json.load(urllib.request.urlopen(req, timeout=300))
    pathlib.Path(out).write_bytes(base64.b64decode(r["data"][0]["b64_json"]))
    u = r["usage"]
    global spent
    spent += u["input_tokens"] * 5e-6 + u["output_tokens"] * 30e-6

def speech(text, instructions, voice="cedar", speed=1.0):
    """gpt-realtime-2.1-mini via say_rt.py → raw PCM s16le 24 kHz mono (~$0.026 per minute). `instructions` = delivery style;
    `speed` != 1 is applied afterwards with ffmpeg atempo (the Realtime API has no speed setting)."""
    r = subprocess.run(["uv", "run", "-q", str(pathlib.Path(__file__).parent / "say_rt.py")], capture_output=True, check=True,
                       input=json.dumps({"text": text, "instructions": instructions, "voice": voice, "key": KEY}).encode())
    global spent
    for u in json.loads(r.stderr.decode().strip().splitlines()[-1]):
        o, i = u["output_token_details"], u["input_token_details"]
        spent += o["audio_tokens"] * 20e-6 + (u["output_tokens"] - o["audio_tokens"]) * 2.4e-6 + i["text_tokens"] * 0.6e-6
    if speed == 1.0: return r.stdout
    return subprocess.run(["ffmpeg", "-v", "error", "-f", "s16le", "-ar", "24000", "-ac", "1", "-i", "-", "-af", f"atempo={speed}",
                           "-f", "s16le", "-"], input=r.stdout, capture_output=True, check=True).stdout

def edit(prompt, refs, out, quality="medium", size="1024x1536"):
    """Image from reference images (same character in a new scene); JSON /images/edits with base64 data URLs."""
    imgs = [{"image_url": "data:image/png;base64," + base64.b64encode(pathlib.Path(p).read_bytes()).decode()} for p in refs]
    req = urllib.request.Request("https://api.openai.com/v1/images/edits",
                                 json.dumps({"model": MODEL, "prompt": prompt, "images": imgs, "size": size, "quality": quality}).encode(),
                                 {"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    r = json.load(urllib.request.urlopen(req, timeout=300))
    pathlib.Path(out).write_bytes(base64.b64decode(r["data"][0]["b64_json"]))
    u = r["usage"]
    global spent
    spent += u["input_tokens"] * 5e-6 + u["output_tokens"] * 30e-6

def chat(prompt, model="gpt-5.5"):
    """Text answer as a JSON object string (Responses API). Not added to `spent`: chat tokens are covered by our plan."""
    req = urllib.request.Request("https://api.openai.com/v1/responses",
                                 json.dumps({"model": model, "input": prompt, "text": {"format": {"type": "json_object"}}}).encode(),
                                 {"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    r = json.load(urllib.request.urlopen(req, timeout=600))
    return next(c["text"] for o in r["output"] if o["type"] == "message" for c in o["content"] if c["type"] == "output_text")
