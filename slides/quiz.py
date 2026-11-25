# /// script
# dependencies = ["pillow"]
# ///
"""UGC quiz ad: teen photo bobbing to the beat + hook card (table, odds lines or comment) → app-style quiz screens with typed answers →
real store screen with the result (+ TallPlan name and icon) → packshot. No voice, Lyria music.
Usage: uv run quiz.py quiz/<spec>.json  ("answers": [] skips the quiz; outputs in a folder named after the spec; idempotent: delete a file to redo it)
"""
import json, math, pathlib, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "3d"))
import api, oai
from api import gemini, data

W, H, FPS = 1080, 1920, 30
HOOK, STEP, RESULT, PACKSHOT = 7.0, 1.1, 3.0, 2.2
FONT = HERE.parent / "3d/fonts/Montserrat.ttf"
PHOTOS = HERE.parent / "TallPlan photo"
LIME, BLUE, CARD = "#c8f03c", "#2337c9", "#1c1d21"
CTA = "GET YOUR\nPERSONAL ROUTINE"
QUIZ = "TAKE THE QUIZ TO FIND\nYOUR HEIGHT POTENTIAL"

spec_f = pathlib.Path(sys.argv[1]).resolve()
spec, d = json.loads(spec_f.read_text()), spec_f.with_suffix("")
d.mkdir(exist_ok=True)

def font(size, wght=900):
    f = ImageFont.truetype(str(FONT), size); f.set_variation_by_axes([wght]); return f

def fit(text, size, width, wght=900):
    while max(font(size, wght).getlength(l) for l in text.split("\n")) > width: size -= 2
    return font(size, wght)

def caption(dr, text, y=270, size=86):
    f = fit(text, size, W * 0.8)
    dr.multiline_text((W / 2, y), text, font=f, fill="white", anchor="ma", align="center", spacing=8, stroke_width=round(f.size * 0.09), stroke_fill="black")

def ease(u):  # back ease-out: slight overshoot
    u = min(1, max(0, u)); return 1 + 2.7 * (u - 1) ** 3 + 1.7 * (u - 1) ** 2

# assets
photo = d / "photo.png"
if not photo.exists():
    print("🖼️  photo...")
    oai.image(spec["photo"] + " Absolutely no text, letters or numbers.", photo)
music = d / "music.mp3"
if not music.exists():
    print("🎵 music...")
    music.write_bytes(data(gemini("lyria-3-clip-preview", [{"text": f"Instrumental only, no vocals. {spec['music']}"}], responseModalities=["AUDIO"])))
bpm = int(re.search(r"(\d{2,3})\s*BPM", spec["music"]).group(1))
src = Image.open(photo).convert("RGB")
src = src.resize((round(src.width * H / src.height), H), Image.LANCZOS)
icon = Image.open(PHOTOS / "Logo/app-icon.png").convert("RGBA").resize((76, 76), Image.LANCZOS)
mask = Image.new("L", icon.size); ImageDraw.Draw(mask).rounded_rectangle((0, 0, 75, 75), 18, fill=255); icon.putalpha(mask)
shot = Image.open(PHOTOS / "7nov" / spec["result"]).convert("RGB").crop((98, 280, 622, 1280))  # phone only: no store headline, no seams with our background
shot = shot.resize((720, round(shot.height * 720 / 524)), Image.LANCZOS)

def badge(im, y=480):
    """TallPlan icon + name: the store screens carry no branding of their own."""
    dr, f = ImageDraw.Draw(im), font(54, 800)
    x = (W - 76 - 18 - f.getlength("TallPlan")) / 2
    im.paste(icon, (round(x), y), icon)
    dr.text((x + 94, y + 38), "TallPlan", font=f, fill="white", anchor="lm")

def hook_card(im, t):
    """Table rows pop in one by one, the viewer's row lit; odds lines over the face; or a comment bubble."""
    dr, x0, y = ImageDraw.Draw(im, "RGBA"), 70, 980
    if "odds" in spec:
        for k, line in enumerate(spec["odds"]):
            if t > 1.0 + 0.6 * k:
                f = fit(line, 64, W * 0.86, 700)
                dr.text((W / 2, 620 + 115 * k), line, font=f, fill="white", anchor="mm", stroke_width=5, stroke_fill="black")
    elif "table" in spec:
        tb = spec["table"]
        rows = [r for k, r in enumerate(tb["rows"]) if t > 1.2 + 0.35 * k]
        if not rows: return
        dr.rounded_rectangle((x0, y, W - 190, y + 120 + 76 * len(rows)), 28, fill=(255, 255, 255, 235))
        dr.text((x0 + 36, y + 40), tb["title"], font=fit(tb["title"], 40, W - 330), fill="#111", anchor="lm")
        for k, (a, b) in enumerate(rows):
            ry = y + 110 + 76 * k
            if k == tb["hl"]: dr.rounded_rectangle((x0 + 16, ry - 6, W - 206, ry + 66), 18, fill=LIME)
            dr.text((x0 + 40, ry + 30), a, font=font(42, 700), fill="#111", anchor="lm")
            dr.text((W - 230, ry + 30), b, font=font(44, 900), fill="#111", anchor="rm")
    elif t > 1.0:
        c, s = spec["comment"], ease((t - 1.0) / 0.4)
        bub = Image.new("RGBA", (W - 260, 250))
        bd = ImageDraw.Draw(bub)
        bd.rounded_rectangle((0, 0, bub.width - 1, 249), 36, fill=(255, 255, 255, 245))
        bd.ellipse((30, 30, 110, 110), fill="#9aa0a6")
        bd.text((130, 50), c["user"], font=font(34, 700), fill="#666", anchor="lm")
        bd.multiline_text((130, 90), c["text"], font=fit(c["text"], 44, bub.width - 170, 800), fill="#111", spacing=8)
        bub = bub.resize((max(1, round(bub.width * s)), max(1, round(250 * s))))
        im.paste(bub, (round(x0 + (W - 260) * (1 - s) / 2), round(y + 125 * (1 - s))), bub)

def hook(t):
    beat = t * bpm / 60
    z = 1.04 + 0.025 * (0.5 + 0.5 * math.cos(2 * math.pi * beat))  # head-bob to the beat: smooth, no jitter
    p = src.resize((round(src.width * z), round(H * z)))
    im = p.crop(((p.width - W) // 2, (p.height - H) // 2 + round(10 * math.sin(math.pi * beat)), (p.width + W) // 2, (p.height + H) // 2 + round(10 * math.sin(math.pi * beat))))
    caption(ImageDraw.Draw(im), spec["hook"])
    hook_card(im, t)
    return im

def screen(t, k):
    """App-style quiz step k with its answer typed in; the phone slides up on the first step."""
    q, a = spec["answers"][k]
    im = Image.new("RGB", (W, H), BLUE)
    dr = ImageDraw.Draw(im)
    caption(dr, QUIZ)
    badge(im)
    y = 600 + round(1400 * (1 - ease(t / 0.45))) if k == 0 else 600
    dr.rounded_rectangle((120, y, W - 120, H + 80), 56, fill="#0a0a0b")
    dr.rounded_rectangle((180, y + 60, W - 180, y + 72), 6, fill="#333")
    dr.rounded_rectangle((180, y + 60, 180 + (W - 360) * (k + 1) // len(spec["answers"]), y + 72), 6, fill=LIME)
    dr.text((W / 2, y + 170), q, font=fit(q, 56, W - 340, 800), fill="white", anchor="mm")
    dr.rounded_rectangle((180, y + 260, W - 180, y + 500), 36, fill=CARD)
    dr.text((W / 2, y + 380), a[:max(0, min(len(a), int((t - 0.3) / 0.12) + 1))], font=font(150, 900), fill="white", anchor="mm")
    dr.rounded_rectangle((180, y + 600, W - 180, y + 710), 55, fill=LIME)
    dr.text((W / 2, y + 655), "Continue", font=font(46, 800), fill="#111", anchor="mm")
    return im

def result(t, text=True):
    im = Image.new("RGB", (W, H), BLUE)
    if text: caption(ImageDraw.Draw(im), "HERE'S YOUR\nHEIGHT POTENTIAL", size=70)
    badge(im)
    s = ease(t / 0.4)
    sh = shot.resize((round(shot.width * (0.85 + 0.15 * s)), round(shot.height * (0.85 + 0.15 * s))))
    im.paste(sh, ((W - sh.width) // 2, 600))
    return im

steps = len(spec["answers"])
total = HOOK + STEP * steps + RESULT + PACKSHOT
print(f"🎞️  {spec['hook']!r} · {bpm} BPM · {total:.1f}s")
cut = d / "cut.mp4"
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", music,
                       "-filter_complex", f"[1:a]atrim=0:{total},afade=t=out:st={total - 1}:d=1,aresample=48000,aformat=channel_layouts=stereo[a]",
                       "-map", "0:v", "-map", "[a]", "-t", f"{total:.3f}", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", cut], stdin=subprocess.PIPE)
for n in range(round(total * FPS)):
    t = n / FPS
    if t < HOOK: im = hook(t)
    elif t < HOOK + STEP * steps: k = int((t - HOOK) / STEP); im = screen(t - HOOK - STEP * k, k)
    else: im = result(t - HOOK - STEP * steps, text=t < total - PACKSHOT)  # clean frame under the packshot
    ff.stdin.write(im.tobytes())
    if n % 90 == 0: print(f"⏳ {t:.0f}/{total:.0f}s")
ff.stdin.close(); ff.wait()
subprocess.run([HERE.parent / "3d/packshot.sh", cut, f"{total - PACKSHOT:.2f}"], check=True)
im = Image.new("RGBA", (W, H))
ImageDraw.Draw(im).multiline_text((W / 2, H * 0.615), CTA, font=fit("PERSONAL ROUTINE", 130, W * 0.8), fill="white", anchor="ma", align="center", spacing=10, stroke_width=9, stroke_fill="black")
im.save(d / "cta.png")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", d / "cut_final.mp4", "-i", d / "cta.png", "-filter_complex",
                f"[0][1]overlay=enable='gte(t,{total - PACKSHOT + 0.25:.2f})'", "-c:v", "libx264", "-crf", "18", "-c:a", "copy", d / "final.mp4"], check=True)
(d / "cut_final.mp4").unlink()
for t, name in ((3.5, "hook"), (HOOK + 0.9, "quiz"), (HOOK + STEP * steps + 1, "result")):  # stills for a quick visual check
    (hook(t) if t < HOOK else screen(0.9, 0) if t < HOOK + STEP * steps else result(1)).save(d / f"check_{name}.png")
print(f"🏁 {d / 'final.mp4'}\n💰 Google (Lyria) ~${api.spent:.3f} · OpenAI (images) ~${oai.spent:.3f} · total ~${api.spent + oai.spent:.3f}")
