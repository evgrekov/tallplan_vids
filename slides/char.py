# /// script
# dependencies = ["pillow"]
# ///
"""Mascot cut-out animation: model sheet → per scene a background, a mascot pose and props (OpenAI edits, same art style),
cut out and animated separately (entrances with overshoot, bounce/hop/wiggle..., squash & stretch, props popping in), OpenAI TTS, word-by-word subtitles, synthesized cartoon SFX, Lyria music, packshot.
Usage: uv run char.py <reference_url> <folder> "<mascot idea>" ["<brief: topic/story that overrides the default arc>"]  (idempotent: delete a file to redo it)
"""
import json, math, subprocess
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw
from anim import *
from api import file

SPEED = 1.27
WHITE = "isolated on a plain pure white background, bold black outline all around, nothing touching the edges, no shadow, no text"

url, d, mascot = sys.argv[1], (HERE / sys.argv[2]).resolve(), sys.argv[3]
brief = sys.argv[4] if len(sys.argv) > 4 else "none, use the default story arc"
d.mkdir(parents=True, exist_ok=True)
ref = d / "reference.mp4"
if not ref.exists():
    print("⬇️  downloading reference...")
    subprocess.run(["yt-dlp", "-q", "--no-warnings", "--remux-video", "mp4", "-o", str(d / "reference.%(ext)s"), url], check=True)
plan_f = d / "plan.json"
if not plan_f.exists():
    print("🧭 planning...")
    plan_f.write_text(gemini("gemini-3.8-flash", [file(ref), {"text": (HERE / "char.txt").read_text().replace("{mascot}", mascot).replace("{brief}", brief)}],
                             responseMimeType="application/json")[0]["text"])
plan = json.loads(plan_f.read_text())
scenes = plan["scenes"]
print(f"📋 {plan['title']} · {len(scenes)} scenes")

# images: the model sheet, then every layer drawn from it (same mascot, same art style)
sheet = d / "sheet.png"
if not sheet.exists():
    print("🧸 mascot sheet...")
    oai.image(plan["mascot_sheet"] + " No text.", sheet, size="1024x1024")
jobs = []  # (out, prompt, size, quality)
for i, s in enumerate(scenes):
    jobs.append((d / f"bg{i}.png", f"Background only in the exact art style of the reference image, NO characters, no mascot: {s['bg']}. Flat 2D cartoon, full-bleed, no text.", "1024x1536", "low"))
    jobs.append((d / f"pose{i}.png", f"The mascot from the reference image exactly (same design, colors, proportions, style), full body: {s['pose']}. {WHITE}.", "1024x1024", "medium"))
    for j, p in enumerate(s["props"]):
        jobs.append((d / f"prop{i}_{j}.png", f"A single object in the exact art style of the reference image, no mascot: {p['prompt']}. {WHITE}.", "1024x1024", "low"))

def draw(job):
    out, prompt, size, q = job
    if out.exists(): return
    print(f"🖼️  {out.stem}...")
    oai.edit(prompt, [sheet], out, quality=q, size=size)
with ThreadPoolExecutor(4) as ex: list(ex.map(draw, jobs))

bgs = [cover(d / f"bg{i}.png") for i in range(len(scenes))]
poses = [cutout(d / f"pose{i}.png", height=H * 0.46, width=W * 0.78) for i in range(len(scenes))]
props = [[cutout(d / f"prop{i}_{j}.png", width=W * p["w"] * 1.2) for j, p in enumerate(s["props"])] for i, s in enumerate(scenes)]

starts, vo_dur, total = voiceover(d, [s["vo"] for s in scenes], plan, SPEED)
ps = starts[-1]  # packshot under the last line

def mascot_at(fr, i, u):
    m, act = poses[i], scenes[i]["action"]
    cx, bottom, s, sx, sy, rot = W / 2, H * 0.72, 1.0, 1.0, 1.0, 0.0
    p = back(u / 0.35)
    enter = scenes[i]["enter"]
    if enter == "pop": s = max(p, 0.01)
    elif enter == "drop": bottom -= (1 - p) * H * 0.8
    elif enter == "left": cx -= (1 - p) * W
    elif enter == "right": cx += (1 - p) * W
    elif enter == "bottom": bottom += (1 - p) * H * 0.7
    a = max(u - 0.35, 0)
    lift = 0
    if act in ("bounce", "hop"):
        f, amp = (6, 45) if act == "bounce" else (4.5, 110)
        ph = abs(math.sin(a * f)); lift = ph * amp
        sy = 0.86 + 0.14 * min(1, ph * 3); sx = 1 / sy  # squash on landing
        if act == "hop": rot = 6 * math.cos(a * f)
    elif act == "wiggle": rot = 8 * math.sin(a * 9)
    elif act == "float": lift = 25 + 18 * math.sin(a * 3); rot = 3 * math.sin(a * 2)
    elif act == "shake": rot = 5 * math.sin(a * 5)  # gentle sway, no jitter
    elif act == "stretch": sy = 1 + 0.13 * math.sin(a * 5); sx = 1 / sy
    elif act == "spin": rot = 360 * ease(u / 0.7) if u < 0.7 else 5 * math.sin(a * 6)
    sh = Image.new("RGBA", (W, H))  # contact shadow shrinks while airborne
    r = m.width * 0.38 * (1 - min(lift, 120) / 240) * s
    ImageDraw.Draw(sh).ellipse((cx - r, bottom - 18, cx + r, bottom + 18), fill=(0, 0, 0, 70))
    fr.alpha_composite(sh)
    sprite(fr, m, cx, bottom - lift, s, sx, sy, rot)

def props_at(fr, i, u):
    for j, (im, p) in enumerate(zip(props[i], scenes[i]["props"])):
        q = back((u - 0.4 - j * 0.3) / 0.3)
        if q <= 0.01: continue
        cy = p["y"] * H + im.height / 2 + 10 * math.sin(u * 4 + j)
        sprite(fr, im, p["x"] * W, cy, q, rot=4 * math.sin(u * 3 + j))

subs = Subs(starts, vo_dur, [s["vo"] for s in scenes])
music(d, plan["music"])

def frame(t):
    i = max(j for j, st in enumerate(starts) if st <= t)
    u, dur = t - starts[i], (starts[i + 1] if i + 1 < len(starts) else total) - starts[i]
    fr = camera(bgs[i], u, dur).convert("RGBA")
    props_at(fr, i, u)
    mascot_at(fr, i, u)
    fr = fr.convert("RGB")
    subs.draw(fr, t)
    return fr

render(d, total, frame, [(st, s["sfx"]) for st, s in zip(starts, scenes)], ps)
