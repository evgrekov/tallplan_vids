# /// script
# dependencies = ["pillow"]
# ///
"""Facts explainer: flat vector character on blue with a height ruler + live counter (growing, side-by-side comparisons),
popping icons, realistic photo shots with a slow push, pleasant OpenAI voice, word subtitles, music from our saved sounds, packshot.
Usage: uv run facts.py <reference_url> <folder> "<topic>" "<facts>" <sound_id>  (idempotent: delete a file to redo it)
"""
import json, math, subprocess
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw
from anim import *
from api import file

SPEED = 1.22
FEET = H * 0.7  # ground line, above the subtitles
INK = "#0d1b3d"
WHITE = "isolated on a plain pure white background, nothing touching the edges, no shadow, no text"

url, d, topic, facts, sound = sys.argv[1], (HERE / sys.argv[2]).resolve(), sys.argv[3], sys.argv[4], sys.argv[5]
d.mkdir(parents=True, exist_ok=True)
ref = d / "reference.mp4"
if not ref.exists():
    print("⬇️  downloading reference...")
    subprocess.run(["yt-dlp", "-q", "--no-warnings", "--remux-video", "mp4", "-o", str(d / "reference.%(ext)s"), url], check=True)
plan_f = d / "plan.json"
if not plan_f.exists():
    print("🧭 planning...")
    plan_f.write_text(gemini("gemini-3.8-flash", [file(ref), {"text": (HERE / "facts.txt").read_text().replace("{topic}", topic).replace("{facts}", facts)}],
                             responseMimeType="application/json")[0]["text"])
plan = json.loads(plan_f.read_text())
scenes = plan["scenes"]
print(f"📋 {plan['title']} · {len(scenes)} scenes")

sheet = d / "sheet.png"
if not sheet.exists():
    print("🧍 character sheet...")
    oai.image(plan["character"] + " No text.", sheet, size="1024x1024")
jobs = []  # (out, prompt, size, quality)
for i, s in enumerate(scenes):
    if s["kind"] == "photo":
        jobs.append((d / f"photo{i}.png", f"{s['photo']} Vertical, full-bleed, no text, no letters.", "1024x1536", "medium", False))
        continue
    for j, f in enumerate(s["figures"]):
        jobs.append((d / f"fig{i}_{j}.png", f"The character from the reference image exactly (same flat vector style, face, proportions), full body standing on the ground: {f['pose']}. {WHITE}.", "1024x1536", "medium", True))
    for j, c in enumerate(s["icons"]):
        jobs.append((d / f"icon{i}_{j}.png", f"A single flat vector icon in the art style of the reference image: {c['prompt']}. {WHITE}.", "1024x1024", "low", True))

def draw(job):
    out, prompt, size, q, ref = job
    if out.exists(): return
    print(f"🖼️  {out.stem}...")
    (oai.edit(prompt, [sheet], out, quality=q, size=size) if ref else oai.image(prompt, out, quality=q, size=size))
with ThreadPoolExecutor(4) as ex: list(ex.map(draw, jobs))

tallest = max([f["in"] or 0 for s in scenes if s["kind"] == "figure" for f in s["figures"]] + [72])
PX = H * 0.44 / tallest  # tallest head + labels stay below the top UI  # one scale for every scene: the same height is the same size all video long
photos = {i: cover(d / f"photo{i}.png") for i, s in enumerate(scenes) if s["kind"] == "photo"}
figs = {(i, j): cutout(d / f"fig{i}_{j}.png", height=f["in"] * PX if f["in"] else H * 0.4)
        for i, s in enumerate(scenes) if s["kind"] == "figure" for j, f in enumerate(s["figures"])}
icons = {(i, j): cutout(d / f"icon{i}_{j}.png", width=W * 0.16)
         for i, s in enumerate(scenes) if s["kind"] == "figure" for j, _ in enumerate(s["icons"])}
vign = Image.radial_gradient("L").resize((W, H)).point(lambda v: min(255, max(0, (v - 120) * 2)))  # dark center → strong edges
red = Image.new("RGBA", (W, H), (230, 40, 50, 0))

starts, vo_dur, total = voiceover(d, [s["vo"] for s in scenes], plan, SPEED)
ps = starts[-1]
subs = Subs(starts, vo_dur, [s["vo"] for s in scenes])
music(d, sound)

def ftin(v):
    v = round(v); return f"{v // 12}'{v % 12}\""

def figure(fr, i, j, f, u):
    im, dr = figs[i, j], ImageDraw.Draw(fr)
    pop = back((u - 0.25 * j) / 0.35)
    if pop <= 0.01: return
    grow = f["from"] + (f["in"] - f["from"]) * ease((u - 0.3) / 1.0) if f["from"] and f["in"] else f["in"]
    s = pop * (grow / f["in"] if grow else 1)
    n = len(scenes[i]["figures"])
    cx = W * (0.47 if n == 1 else 0.16 + 0.62 * j / (n - 1))  # even spacing, clear of the right-side UI icons
    sy = 1 + 0.012 * math.sin(u * 3 + j)  # idle breathing
    r = im.width * 0.4 * s
    dr.ellipse((cx - r, FEET - 14, cx + r, FEET + 14), fill=(0, 0, 0, 40))
    sprite(fr, im, cx, FEET, s, 1, sy)
    top = FEET - im.height * s * sy
    if grow:  # ruler bracket on the left, live value above the head
        x = cx - im.width * s / 2 - 22
        dr.line((x, FEET, x, top), fill=INK, width=5)
        for y in (FEET, top): dr.line((x - 12, y, x + 12, y), fill=INK, width=5)
        dr.text((cx, top - 52), ftin(grow), font=font(76, 900), fill=INK, anchor="ms")
        dr.text((cx, top - 14), f"{grow * 2.54:.0f} cm", font=font(32, 700), fill=INK, anchor="ms")
        top -= 130
    if f["label"]:
        dr.text((cx, top - 18), f["label"], font=font(48, 800), fill=INK, anchor="ms")

def frame(t):
    i = max(j for j, st in enumerate(starts) if st <= t)
    u, dur, s = t - starts[i], (starts[i + 1] if i + 1 < len(starts) else total) - starts[i], scenes[i]
    if s["kind"] == "photo":
        fr = camera(photos[i], u, dur).convert("RGBA")
    else:
        fr = Image.new("RGBA", (W, H), s["bg"])
        for j, c in enumerate(s["icons"]):
            q = back((u - 0.3 - 0.3 * j) / 0.3)
            if q <= 0.01: continue
            im = icons[i, j]
            x, y = W * 0.75, H * (0.36, 0.52)[j] + 8 * math.sin(u * 3 + j)  # right of the figure: the ruler is on its left
            sprite(fr, im, x, y, q)
            ImageDraw.Draw(fr).text((x, y - im.height * q - 14), c["label"], font=font(40, 800), fill=INK, anchor="ms")
        for j, f in enumerate(s["figures"]): figure(fr, i, j, f, u)
        if s["alarm"]:
            fr.alpha_composite(Image.composite(Image.new("RGBA", (W, H), (230, 40, 50, round(150 * (0.6 + 0.4 * math.sin(u * 7))))), red, vign))
    fr = fr.convert("RGB")
    subs.draw(fr, t)
    return fr

render(d, total, frame, [(st, s["sfx"]) for st, s in zip(starts, scenes)], ps)
