"""OpenAI speech + transcription (key from repo-root .env, never printed)."""
import json, pathlib, re, urllib.request, uuid

KEY = re.search(r"OPENAI_API_KEY=(\S+)", (pathlib.Path(__file__).parents[2] / ".env").read_text()).group(1)
spent = 0.0  # $ of this process (estimate)

def _post(path, body, ctype):
    req = urllib.request.Request(f"https://api.openai.com/v1/{path}", body, {"Content-Type": ctype, "Authorization": f"Bearer {KEY}"})
    return urllib.request.urlopen(req, timeout=300).read()

def speech(text, instructions, voice, speed=1.0):
    """gpt-4o-mini-tts → raw PCM s16le 24 kHz mono (~$0.015 per minute)."""
    global spent
    pcm = _post("audio/speech", json.dumps({"model": "gpt-4o-mini-tts", "input": text, "voice": voice, "instructions": instructions,
                                            "response_format": "pcm", "speed": speed}).encode(), "application/json")
    spent += len(pcm) / 2 / 24000 / 60 * 0.015
    return pcm

def transcribe(wav, prompt=""):
    """gpt-4o-transcribe on WAV bytes (~$0.006 per minute)."""
    global spent
    b = uuid.uuid4().hex
    body = b"".join([f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
                     for k, v in (("model", "gpt-4o-transcribe"), ("prompt", prompt))]
                    + [f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="a.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode(), wav, f"\r\n--{b}--\r\n".encode()])
    spent += (len(wav) - 44) / 2 / 24000 / 60 * 0.006
    return json.loads(_post("audio/transcriptions", body, f"multipart/form-data; boundary={b}"))["text"]
