# /// script
# dependencies = ["websockets"]
# ///
"""One voice-over line on gpt-realtime-2.1-mini (Realtime API, the replacement of the deprecated Speech API models).
Called by oai.speech: JSON {text, instructions, voice, key} on stdin -> raw PCM s16le 24 kHz mono on stdout, usage JSON on stderr.
The model is conversational, so its transcript is compared with the text and the line is redone if it changed the words.
"""
import asyncio, base64, difflib, json, re, sys
import websockets

MODEL = "gpt-realtime-2.1-mini"
job = json.load(sys.stdin)
words = lambda s: re.findall(r"[a-z0-9']+", s.lower())

async def read():
    async with websockets.connect(f"wss://api.openai.com/v1/realtime?model={MODEL}",
                                  additional_headers={"Authorization": f"Bearer {job['key']}"}, max_size=None) as ws:
        await ws.send(json.dumps({"type": "session.update", "session": {
            "type": "realtime", "output_modalities": ["audio"],
            "instructions": "You are a voice-over reader. Read the user's text aloud exactly as written, word for word, "
                            f"nothing added, nothing answered. Style: {job['instructions']}",
            "audio": {"output": {"voice": job["voice"], "format": {"type": "audio/pcm", "rate": 24000}}}}}))
        await ws.send(json.dumps({"type": "conversation.item.create", "item": {
            "type": "message", "role": "user", "content": [{"type": "input_text", "text": job["text"]}]}}))
        await ws.send(json.dumps({"type": "response.create"}))
        pcm, said = b"", ""
        async for m in ws:
            e = json.loads(m)
            if e["type"] == "response.output_audio.delta": pcm += base64.b64decode(e["delta"])
            elif e["type"] == "response.output_audio_transcript.delta": said += e["delta"]
            elif e["type"] == "error": raise RuntimeError(e["error"])
            elif e["type"] == "response.done": return pcm, said, e["response"]["usage"]

usage = []
for _ in range(3):
    pcm, said, u = asyncio.run(read())
    usage.append(u)
    if difflib.SequenceMatcher(None, words(said), words(job["text"])).ratio() >= 0.9: break
    print(f"⚠️  reworded, retry: {said!r}", file=sys.stderr)
else:
    sys.exit(f"❌ model keeps rewording: {said!r}")
sys.stdout.buffer.write(pcm)
print(json.dumps(usage), file=sys.stderr)
