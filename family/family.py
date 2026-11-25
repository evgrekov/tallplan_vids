# /// script
# dependencies = ["pillow"]
# ///
"""Comment reply with a stick-figure family (ref @how.tall.will.i.b, rules C-HTW): a viewer's comment card on top, the whole crooked
family stands on a height scale from frame 1 (each voice line adds that member's height), the mid-parental formula (dad + mom ± 5) ÷ 2 with a big yellow result, a TallPlan-style
prediction card as the refinement, honest/comforting outro + CTA, then packshot. No video or image generation: only TTS (~$0.02).

  uv run family.py <work>/spec.json   -> <work>/final.mp4   (idempotent: delete a wav to redo that line)
"""
import json, pathlib, random, subprocess, sys, wave
from PIL import Image, ImageDraw, ImageFont
HERE = pathlib.Path(__file__).parent
sys.path[:0] = [str(HERE.parent / "slides"), str(HERE.parent / "muscle")]
import oai
from assemble import packshot

W, H, GROUND, PX = 1080, 1920, 1180, 8.2  # PX = pixels per inch; 78 in reaches y≈520, under the comment card
PAPER, YELLOW, BLUE, LIME = "#FBFAF6", "#F7C500", "#2337c9", "#c8f03c"
ICON = HERE.parent / "TallPlan photo/Logo/app-icon.png"
spec_f = pathlib.Path(sys.argv[1]).resolve()
spec, d = json.loads(spec_f.read_text()), spec_f.parent
(d / "vo").mkdir(exist_ok=True)
fam = spec["family"]
kid = next(m for m in fam if m.get("kid"))
dad, mom = (next(m["in"] for m in fam if m["who"] == w) for w in ("DAD", "MOM"))
plus = 5 if spec["sex"] == "boy" else -5
mid, rng, adult = round((dad + mom + plus) / 2), spec["range"], spec["app"]["adult"]
assert abs(adult - mid) <= rng, "the app prediction must sit inside the formula range"

def font(size, wght=800):
    f = ImageFont.truetype(str(HERE.parent / "3d/fonts/Montserrat.ttf"), size); f.set_variation_by_axes([wght]); return f

def ftin(i): return f"{i // 12}'{i % 12}\""

def say(name, text):
    out = d / f"vo/{name}.wav"
    if not out.exists():
        print(f"🎙️  {name}: {text}")
        with wave.open(str(out), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000)
            w.writeframes(oai.speech(text, spec["voice"], spec["openai_voice"], spec.get("speed", 1.0)))
    with wave.open(str(out)) as w: return out, w.getnframes() / w.getframerate()

# 1) voice: intro, one line per family member, formula, result, app card, outro (the outro plays over the app card)
names = ["intro"] + [f"m{i}" for i in range(len(fam))] + ["formula", "result", "app", "outro"]
texts = [spec["intro"]] + [m["say"] for m in fam] + [spec["formula_say"], spec["result_say"], spec["app"]["say"], spec["outro"]]
lines = [say(n, t) for n, t in zip(names, texts)]
t, cues = 0.2, []
for f, dur in lines: cues.append((f, t)); t += dur + 0.15
ps, T = t + 0.5, t + 2.3
app_t = cues[-2][1]

# 2) drawing states. Frame 1 already shows the whole family on the scale (G02: the hook is the figures, not the math);
#    each member's line only adds their height tag, then the formula, then the kid at 18 fills the "?" slot.
xs = [W * (0.17 + 0.69 * k / len(fam)) for k in range(len(fam) + 1)]  # last slot = the kid at 18
INK = "#222"

def figure(im, x, inches, color, seed, hat=False):
    """Crooked pill-body figure with a simple face (ref style), height to scale; a fixed seed keeps the wobble identical in every state."""
    r, dr = random.Random(seed), ImageDraw.Draw(im, "RGBA")
    j = lambda p: (p[0] + r.uniform(-6, 6), p[1] + r.uniform(-4, 4))
    h = inches * PX; top = GROUND - h; hr = h * 0.1; bw = h * 0.09
    neck, hip = top + 2 * hr + 4, top + h * 0.58
    ink = INK if len(color) != 4 else (34, 34, 34, color[3])
    dr.line([j((x - h * 0.08, GROUND)), (x - bw * 0.4, hip - 10)], fill=color, width=20)
    dr.line([j((x + h * 0.08, GROUND)), (x + bw * 0.4, hip - 10)], fill=color, width=20)
    dr.line([j((x - h * 0.16, hip - h * 0.05)), (x, neck + h * 0.05), j((x + h * 0.16, hip - h * 0.05))], fill=color, width=16, joint="curve")
    dr.rounded_rectangle((x - bw, neck, x + bw, hip), bw, fill=color)
    dr.ellipse((x - hr, top, x + hr, top + 2 * hr), fill=color)
    ey, er = top + hr * 0.85, max(4, hr * 0.13)
    for ex in (x - hr * 0.38, x + hr * 0.38): dr.ellipse((ex - er, ey - er, ex + er, ey + er), fill="white")
    dr.arc((x - hr * 0.45, top + hr * 0.75, x + hr * 0.45, top + hr * 1.5), 20, 160, fill="white", width=5)
    if hat: dr.polygon([(x - hr * 1.1, top + hr * 0.35), (x + hr * 1.1, top + hr * 0.35), (x + hr * 1.3, top - hr * 0.7)], fill="#D62828")
    return top

def tag(dr, x, y, text, color, size=44):
    dr.text((x, y), text, font=font(size, 900), fill=color, anchor="mm", stroke_width=5, stroke_fill=PAPER)

base = Image.new("RGB", (W, H), PAPER)
dr = ImageDraw.Draw(base)
for i in range(48, 79, 6):  # scale: dashed line every 6 in, labelled on the left
    y = GROUND - i * PX
    for x0 in range(150, 1010, 28): dr.line((x0, y, x0 + 16, y), fill="#999", width=4)
    dr.text((62, y), ftin(i), font=font(32, 800), fill="#666", anchor="lm")
dr.line((120, GROUND, 1010, GROUND), fill=INK, width=8)
c = spec["comment"]  # comment card: grey avatar, handle, two lines of text
dr.rounded_rectangle((90, 280, W - 90, 470), 34, fill="white", outline="#E2E2E2", width=3)
dr.ellipse((122, 312, 202, 392), fill="#9aa0a6")
dr.text((226, 330), c["user"], font=font(32, 700), fill="#777", anchor="lm")
dr.multiline_text((226, 360), c["text"], font=font(38, 800), fill="#111", spacing=8)

im, tops = base.copy(), []
d2 = ImageDraw.Draw(im)
for k, m in enumerate(fam):
    tops.append(figure(im, xs[k], m["in"], m["color"], k, spec.get("hats", False)))
    tag(d2, xs[k], GROUND + 38, m["who"], m["color"], 36)
tag(d2, xs[-1], GROUND + 38, "AT 18", "#C99A00", 36)

def with_q(frame):  # the empty "kid at 18" slot until the result line
    f = frame.copy()
    ImageDraw.Draw(f).text((xs[-1], GROUND - 300), "?", font=font(260, 900), fill=YELLOW, anchor="mm", stroke_width=8, stroke_fill=INK)
    return f

states = [with_q(im)]
for k, m in enumerate(fam):
    tag(d2, xs[k], tops[k] - (m["in"] * PX * 0.07 + 30 if spec.get("hats") else 34), ftin(m["in"]), m["color"])
    states.append(with_q(im))
d2.text((W / 2, 1282), f"({dad} + {mom} {'+' if plus > 0 else '−'} 5) ÷ 2 = {mid} in", font=font(56, 800), fill="#111", anchor="mm")
states.append(with_q(im))
ghost = Image.new("RGBA", (W, H))
gtop = figure(ghost, xs[-1], mid, (247, 197, 0, 170), 99)
im.paste(ghost, (0, 0), ghost)
tag(d2, xs[-1], gtop - 34, ftin(mid), "#C99A00")
d2.text((W / 2 - 40, 1380), ftin(mid), font=font(150, 900), fill=YELLOW, anchor="mm", stroke_width=8, stroke_fill="#111")
d2.text((W / 2 + 190, 1395), f"± {rng} in", font=font(48, 800), fill="#111", anchor="lm")
states.append(im.copy())
for k, s in enumerate(states): s.save(d / f"s{k}.png")

# 3) TallPlan-style prediction card (the refinement of the formula), slides up over the sheet
cw, ch = 900, 600
face = Image.new("RGB", (cw, ch))
fd = ImageDraw.Draw(face)
for y in range(ch):  # vertical gradient like the app's prediction card
    k = y / ch; fd.line((0, y, cw, y), fill=(int(0x2c - 10 * k), int(0x44 - 20 * k), int(0xc9 - 40 * k)))
icon = Image.open(ICON).convert("RGBA").resize((64, 64))
face.paste(icon, (50, 44), icon)
fd.text((132, 76), "TallPlan", font=font(42, 800), fill="white", anchor="lm")
fd.text((50, 170), "As an adult", font=font(40, 600), fill="#B9C3FF", anchor="lm")
fd.text((46, 290), ftin(adult), font=font(170, 900), fill="white", anchor="lm")
fd.text((cw - 50, 170), "Now", font=font(40, 600), fill="#B9C3FF", anchor="rm")
fd.text((cw - 50, 232), ftin(kid["in"]), font=font(64, 900), fill="white", anchor="rm")
grow = f"+{adult - kid['in']} in to grow"
gw = font(36, 700).getlength(grow)
fd.rounded_rectangle((cw - 50 - gw - 44, 285, cw - 50, 345), 30, fill="#4A5BD8")
fd.text((cw - 72, 315), grow, font=font(36, 700), fill="white", anchor="rm")
for k in range(14):  # dotted growth curve from "you" to the lime dot
    u = k / 13; x, y = 110 + 640 * u, 520 - 130 * (1 - (1 - u) ** 2)
    fd.ellipse((x - 6, y - 6, x + 6, y + 6), fill="white")
fd.ellipse((750 - 22, 390 - 22, 750 + 22, 390 + 22), fill=LIME)
fd.text((110, 565), "you", font=font(34, 700), fill="white", anchor="mm")
mask = Image.new("L", face.size); ImageDraw.Draw(mask).rounded_rectangle((0, 0, cw - 1, ch - 1), 48, fill=255)
card = Image.new("RGBA", (cw + 60, ch + 60))
ImageDraw.Draw(card).rounded_rectangle((30, 44, cw + 30, ch + 44), 48, fill=(0, 0, 0, 90))
card.paste(face, (30, 30), mask)
card.save(d / "app.png")

# 4) video: states switch on their lines, the card slides up on the app line; audio lines placed on the timeline
starts = [cues[1 + k][1] for k in range(len(fam))] + [cues[-4][1], cues[-3][1]]  # state k+1 opens on its line
ov = "".join(f"[v{k}][{k + 1}]overlay=enable='gte(t,{s:.2f})'[v{k + 1}];" for k, s in enumerate(starts))
n = len(states)
mix = ";".join(f"[{n + 1 + i}:a]adelay={int(s * 1000)}|{int(s * 1000)},apad[a{i}]" for i, (_, s) in enumerate(cues))
mix += ";" + "".join(f"[a{i}]" for i in range(len(cues))) + f"amix=inputs={len(cues)}:normalize=0,atrim=0:{T:.2f},loudnorm=I=-14:TP=-1.5,aresample=48000[aout]"
cut = str(d / "cut.mp4")
subprocess.run(["ffmpeg", "-v", "error", "-y", *[x for k in range(n) for x in ("-loop", "1", "-framerate", "30", "-t", f"{T:.2f}", "-i", d / f"s{k}.png")],
                "-loop", "1", "-framerate", "30", "-t", f"{T:.2f}", "-i", d / "app.png", *[x for f, _ in cues for x in ("-i", f)],
                "-filter_complex", f"[0]null[v0];{ov}[v{n - 1}][{n}]overlay=x=(W-w)/2:y='560+1400*(1-clip((t-{app_t:.2f})/0.35,0,1))':enable='gte(t,{app_t:.2f})',"
                f"fade=t=out:st={ps - 0.5:.2f}:d=0.5,format=yuv420p[v];{mix}",
                "-map", "[v]", "-map", "[aout]", "-t", f"{T:.2f}", "-c:v", "libx264", "-crf", "18", "-c:a", "aac", "-b:a", "192k", cut], check=True)
packshot(cut, ps, str(d / "final.mp4"))
print(f"✅ {d / 'final.mp4'} · {T:.1f}s · 💰 OpenAI TTS ~${oai.spent:.3f}")
