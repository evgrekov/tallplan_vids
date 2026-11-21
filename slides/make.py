# /// script
# dependencies = ["pillow"]
# ///
"""Exercise slideshow ad: OpenAI plan → two key poses per exercise (pose b edited from pose a) alternating on the beat
from frame 0, 2 exercises + result, OpenAI voice with word subtitles, a reused music track, packshot. Google $0.
Usage: uv run make.py <folder> "<brief: topic, hook, art style, voice>" <music folder with music.mp3 + plan.json (BPM)> <plan.txt|form.txt>
form.txt: exercise 1 is shown as WRONG (red ✗) vs RIGHT (green ✓) form, switching every 2 beats; exercise 2 = correct reps.
Steps are idempotent: delete a file to redo it.
"""
import json, pathlib, re, shutil
from PIL import Image, ImageDraw
from anim import *

SPEED = 1.2
d, brief, src, prompt_f = (HERE / sys.argv[1]).resolve(), sys.argv[2], HERE / sys.argv[3], HERE / sys.argv[4]
d.mkdir(parents=True, exist_ok=True)
plan_f = d / "plan.json"
if not plan_f.exists():
    print("🧭 planning...")
    plan_f.write_text(oai.chat(prompt_f.read_text().replace("{brief}", brief)))
plan = json.loads(plan_f.read_text())
print(f"📋 {plan['title']}")

def draw(name, prompt, ref=None, change="a CLEARLY different pose: the opposite end of the movement, with a big visible change in the arms, legs or torso (not the same pose)"):
    p = d / f"{name}.png"
    if not p.exists():
        print(f"🖼️  {name}...")
        full = f"{plan['style']} Character: {plan['character']}. {prompt} Anatomically correct: exactly two arms and two legs, every limb clearly attached. Absolutely no text, letters or numbers."
        oai.edit(f"Same character, same art style, background and framing as the reference image, but {change}. {full}", [ref], p) if ref else oai.image(full, p)
    return p

ex = plan["exercises"]
poses = []
for i, e in enumerate(ex):
    a = draw(f"ex{i}a", e["a"])
    poses.append((a, draw(f"ex{i}b", e["b"], a, *(["the same exercise done with correct form exactly as described"] if e.get("marks") else []))))
result = draw("result", plan["result"])

def slide(p):
    """2:3 image at full width on the bottom of the 9:16 frame, the band above filled with its corner color."""
    im = Image.open(p).convert("RGB").resize((W, W * 3 // 2), Image.LANCZOS)
    fr = Image.new("RGB", (W, H), im.getpixel((4, 4)))
    fr.paste(im, (0, H - im.height))
    return fr

def caption(fr, top, sub=""):
    dr, f = ImageDraw.Draw(fr), font(110)
    while f.getlength(top) > W * 0.8: f = font(f.size - 4)
    dr.text((W / 2, 300), top, font=f, fill=plan["ink"], anchor="ma", stroke_width=round(f.size * 0.08), stroke_fill=plan["outline"])
    if sub:
        g = font(64)
        while g.getlength(sub) > W * 0.8: g = font(g.size - 4)
        dr.text((W / 2, 300 + f.size * 1.25), sub, font=g, fill=plan["ink"], anchor="ma", stroke_width=round(g.size * 0.08), stroke_fill=plan["outline"])
    return fr

def mark(fr, ok):
    """Round ✗ / ✓ badge on the right, drawn (the caption font has no such glyphs)."""
    dr, x, y, r = ImageDraw.Draw(fr), W - 190, 640, 85
    dr.ellipse((x - r, y - r, x + r, y + r), fill="#21C55D" if ok else "#EF4444", outline="white", width=8)
    pts = [(x - 40, y + 2), (x - 10, y + 32), (x + 42, y - 30)] if ok else None
    if ok: dr.line(pts, fill="white", width=20, joint="curve")
    else:
        for a, b in (((x - 36, y - 36), (x + 36, y + 36)), ((x - 36, y + 36), (x + 36, y - 36))): dr.line((a, b), fill="white", width=20)
    return fr

def marked(frames):
    return [mark(f, k == 1) for k, f in enumerate(frames)] if ex[0].get("marks") else frames

c = plan["captions"]
segs = [  # (pose pair, caption) per voice line; the last line plays under the packshot
    marked([caption(slide(p), c["hook"]) for p in poses[0]]),
    marked([caption(slide(p), f"1. {ex[0]['name']}", ex[0]["dose"]) for p in poses[0]]),
    ([caption(slide(p), f"2. {ex[1]['name']}", ex[1]["dose"]) for p in poses[1]]),
    ([caption(slide(result), c["takeaway"])] * 2),
    ([slide(result)] * 2),
]
L = plan["lines"]
lines = [L["hook"], L["ex1"], L["ex2"], L["takeaway"], "Get your personal routine in TallPlan."]
starts, dur, total = voiceover(d, lines, plan, SPEED)
subs = Subs(starts, dur, lines)
shutil.copy(src / "music.mp3", d / "music.mp3")
beat = 60 / int(re.search(r"(\d{2,3})\s*BPM", json.loads((src / "plan.json").read_text())["music"]).group(1))

def frame(t):
    i = max(j for j, st in enumerate(starts) if st <= t)
    k = 2 if i < 2 and ex[0].get("marks") else 1  # wrong/right switches slower than reps so both read
    fr = segs[i][int(t / beat / k) % 2].copy()  # pose a / pose b on every beat: reps
    subs.draw(fr, t)
    return fr

render(d, total, frame, [(st, "whoosh") for st in starts[1:3]], starts[-1])
