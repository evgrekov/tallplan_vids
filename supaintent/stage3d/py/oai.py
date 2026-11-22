"""OpenAI image generation (key from repo-root .env). gpt-image-2.6-flare: text in $5/M, image out $30/M; medium ~$0.035 per 1024x1536 image (low ~$0.02)."""
import base64, json, pathlib, re, urllib.request, uuid

KEY = re.search(r"OPENAI_API_KEY=(\S+)", (pathlib.Path(__file__).parents[3] / ".env").read_text()).group(1)
spent = 0.0  # $ of this process on the OpenAI account (estimate from usage)
MODEL = "gpt-image-2.6-flare"  # best quality; the price is set by quality (output tokens), not the model

def image(prompt, out, quality="medium", size="1024x1536", background="auto"):
    """Writes a PNG (default 1024x1536); cost goes to `spent`."""
    req = urllib.request.Request("https://api.openai.com/v1/images/generations",
                                 json.dumps({"model": MODEL, "prompt": prompt, "size": size, "quality": quality, "background": background}).encode(),
                                 {"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    r = json.load(urllib.request.urlopen(req, timeout=300))
    pathlib.Path(out).write_bytes(base64.b64decode(r["data"][0]["b64_json"]))
    u = r["usage"]
    global spent
    spent += u["input_tokens"] * 5e-6 + u["output_tokens"] * 30e-6

def speech(text, instructions, voice="ash", speed=1.0):
    """gpt-4o-mini-tts → raw PCM s16le 24 kHz mono (~$0.015 per minute)."""
    req = urllib.request.Request("https://api.openai.com/v1/audio/speech",
                                 json.dumps({"model": "gpt-4o-mini-tts", "input": text, "voice": voice, "instructions": instructions,
                                             "response_format": "pcm", "speed": speed}).encode(),
                                 {"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    global spent
    pcm = urllib.request.urlopen(req, timeout=300).read()
    spent += len(pcm) / 2 / 24000 / 60 * 0.015
    return pcm

def edit(prompt, refs, out, quality="medium", size="1024x1536", background="auto"):
    """Image from reference images (same character in a new scene); JSON /images/edits with base64 data URLs."""
    imgs = [{"image_url": "data:image/png;base64," + base64.b64encode(pathlib.Path(p).read_bytes()).decode()} for p in refs]
    req = urllib.request.Request("https://api.openai.com/v1/images/edits",
                                 json.dumps({"model": MODEL, "prompt": prompt, "images": imgs, "size": size, "quality": quality, "background": background}).encode(),
                                 {"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    r = json.load(urllib.request.urlopen(req, timeout=300))
    pathlib.Path(out).write_bytes(base64.b64decode(r["data"][0]["b64_json"]))
    u = r["usage"]
    global spent
    spent += u["input_tokens"] * 5e-6 + u["output_tokens"] * 30e-6

def transcribe(wav, prompt=""):
    """gpt-4o-transcribe on WAV bytes (~$0.006 per minute)."""
    global spent
    b = uuid.uuid4().hex
    body = b"".join([f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
                     for k, v in (("model", "gpt-4o-transcribe"), ("prompt", prompt))]
                    + [f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="a.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode(), wav, f"\r\n--{b}--\r\n".encode()])
    spent += (len(wav) - 44) / 2 / 24000 / 60 * 0.006
    return json.loads(urllib.request.urlopen(urllib.request.Request("https://api.openai.com/v1/audio/transcriptions", body, {"Content-Type": f"multipart/form-data; boundary={b}", "Authorization": f"Bearer {KEY}"}), timeout=300).read())["text"]
