# /// script
# dependencies = ["pillow"]
# ///
"""Muscle reel assets on our accounts: stills (OpenAI images), clips (gemini-omni from each still),
voice (OpenAI TTS), music (Lyria). Everything is read from reel.json.
Usage: uv run gen.py <work>/reel.json  (idempotent: delete a file to redo it)
"""
import json, pathlib, subprocess, sys, wave
from concurrent.futures import ThreadPoolExecutor
HERE = pathlib.Path(__file__).parent
sys.path[:0] = [str(HERE.parent / "slides"), str(HERE.parent / "3d")]
import api, oai
from api import gemini, data

cfg_f = pathlib.Path(sys.argv[1]).resolve()
cfg, d = json.loads(cfg_f.read_text()), cfg_f.parent
for sub in ("stills", "clips", "vo"): (d / sub).mkdir(exist_ok=True)
STYLE = (HERE / "style.txt").read_text().strip()
REFS = [HERE / "assets/style_ref_full.png", HERE / "assets/style_ref_close.png"]
clips = [c for s in cfg["sections"] for c in s["clips"]]

def still(c):
    out = d / c["file"].replace("clips/", "stills/").replace(".mp4", ".png")
    if not out.exists():
        print(f"🖼️  {out.name}...")
        oai.edit(f"{STYLE}\nSHOT: {c['shot']}", REFS, out, size="1024x1536")
    return out

def clip(c):
    out, p = d / c["file"], d / c["file"].replace(".mp4", ".txt")
    if out.exists(): return
    p.write_text(f"The grey faceless mannequin athlete performs slow, controlled {c['move']} with perfect form. The working muscle glows red-orange and pulses brighter "
                 "with a hot yellow core at the top of each rep. A thin blue-white electric rim light flickers along the body's edges. "
                 f"{c.get('camera', 'Slow subtle camera push-in')}. Dark charcoal studio. At least {c['dur'] + 0.5:.0f} seconds long. Keep the exact look of the start frame: "
                 "same mannequin, same lighting, same colors. No text, no logos, no extra people, no cuts.")
    subprocess.run([sys.executable, HERE.parent / "3d/omni.py", p, out, "--image", still(c), "--res", cfg["res"]], check=True)

def say(path, text):
    out = d / path
    if out.exists(): return
    print(f"🎙️  {out.name}...")
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000)
        w.writeframes(oai.speech(text, cfg["voice"], cfg["openai_voice"], cfg["speed"]))

todo = [c for c in clips if not (d / c["file"]).exists()]  # remix: existing clips need no still
with ThreadPoolExecutor(4) as ex: list(ex.map(still, todo))
with ThreadPoolExecutor(3) as ex: list(ex.map(clip, todo))
a = cfg["audio"]
for key in ("intro", "outro", "tagline"): say(a[key], cfg["script"][key])
for s in cfg["sections"]: say(s["vo"], s["say"])
m = d / a["music"]
if not m.exists():
    print("🎵 music...")  # the clip model is ~30s, the reel is ~55s
    m.write_bytes(data(gemini("lyria-3-pro-preview", [{"text": f"Instrumental only, no vocals. {cfg['music']}"}], responseModalities=["AUDIO"])))
print(f"✅ assets ready · 💰 Google (Lyria) ~${api.spent:.3f} · OpenAI (images/TTS) ~${oai.spent:.3f} · omni clips: see each 💰 line above (Google)")
