# /// script
# dependencies = ["pillow", "numpy"]
# ///
"""Stop-motion explainer: top-down white table, an index finger slides paper cutouts and tags into place at 12 fps,
OpenAI-planned script, TTS voiceover, word subtitles, reused lo-fi track, packshot.
Usage: uv run stopmo.py <folder> "<brief: topic, hook, style, voice>" <music.mp3>  (idempotent: delete a file to redo it)
"""
import json, math, pathlib, random, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "3d"))
import oai, voice
from anim import Subs

W, H, FPS = 1080, 1920, 12
CARRY, LEAVE, SWEEP = 0.3, 0.25, 0.35  # s: hand brings an item / hand leaves / hand sweeps the table
PACKSHOT = 2.2
SPEED = 1.2  # voice played faster than the TTS pace
FONT = HERE.parent / "3d/fonts/Montserrat.ttf"
CTA = "PREDICT\nYOUR HEIGHT"
KEY = "isolated on a solid flat pure magenta #FF00FF background, nothing else"

d, brief, music_src = (HERE / sys.argv[1]).resolve(), sys.argv[2], pathlib.Path(sys.argv[3])
d.mkdir(parents=True, exist_ok=True)
plan_f = d / "plan.json"
if not plan_f.exists():
    print("🧭 planning...")
    plan_f.write_text(oai.chat((HERE / "stopmo.txt").read_text() + f"\nBrief for this ad: {brief}"))
plan = json.loads(plan_f.read_text())
print(f"📋 {plan['title']} · {len(plan['scenes'])} scenes")

def gen(name, prompt, size="1024x1024"):
    p = d / f"{name}.png"
    if not p.exists():
        print(f"🖼️  {name}...")
        oai.image(prompt, p, size=size)
    return Image.open(p).convert("RGBA")

def keyed(im):
    """Magenta background → transparent, cropped to the subject."""
    a = np.array(im)
    r, g, b = (a[..., i].astype(int) for i in range(3))
    a[..., 3] = np.where((r - g > 90) & (b - g > 90), 0, 255)
    im = Image.fromarray(a)
    return im.crop(im.getbbox())

def font(size):
    f = ImageFont.truetype(str(FONT), size); f.set_variation_by_axes([900]); return f

def tag(text, color, w):
    """Paper label: colored rectangle with black text fitted to it."""
    size = 110
    while font(size).getlength(text) > w * 0.85: size -= 2
    im = Image.new("RGBA", (round(w), round(size * 1.6)), color)
    ImageDraw.Draw(im).text((im.width / 2, im.height / 2), text, font=font(size), fill="#111111", anchor="mm")
    return im

def shadowed(im, rot):
    im = im.rotate(rot, Image.BICUBIC, expand=True)
    sh = Image.new("RGBA", (im.width + 40, im.height + 40))
    sh.paste((0, 0, 0, 90), (14, 18), im.split()[3])
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    sh.alpha_composite(im, (6, 6))
    return sh

# assets
table = gen("table", f"Top-down photo of an empty {plan['surface']}, nothing on it, no objects.", "1024x1536")
table = table.convert("RGB").resize((round(H * 2 / 3), H), Image.LANCZOS)
table = table.crop(((table.width - W) // 2, 0, (table.width - W) // 2 + W, H))
hand = keyed(gen("hand", f"Top-down photo of a real human right hand reaching in from the bottom edge, only the index finger extended straight up as if pushing a small card with its fingertip, the other fingers and thumb curled into the palm, wrist and plain sleeve cut by the bottom edge, {KEY}.", "1024x1536"))
hand = hand.resize((round(W * 0.42), round(W * 0.42 * hand.height / hand.width)), Image.LANCZOS)
arm = Image.new("RGBA", (hand.width, hand.height + H))  # stretch the sleeve's last row so the arm always reaches the bottom edge
arm.paste(hand, (0, 0)); arm.paste(hand.crop((0, hand.height - 2, hand.width, hand.height - 1)).resize((hand.width, H)), (0, hand.height))
hand = arm
tip = np.array(hand)[..., 3][:12].nonzero()[1].mean()  # fingertip x in the hand image
sweeper = hand.rotate(90, expand=True)  # fingertips pointing left, enters from the right
cuts = {k: keyed(gen(f"cut_{k}", f"Paper cutout: {p}. Style: {plan['cut_style']}. Cut out with a thin white paper border, no text, letters or numbers, {KEY}.")) for k, p in plan["cuts"].items()}

# voice + timeline
vo_f = d / "vo.json"
if not vo_f.exists():
    print("🎙️  voiceover...")
    clips = [voice.fx(oai.speech(s["vo"], plan["voice"], plan["openai_voice"], SPEED), f"{voice.TRIM},areverse,{voice.TRIM},areverse") for s in plan["scenes"]]
    for i, c in enumerate(clips): (d / f"vo{i}.raw").write_bytes(c)
    vo_f.write_text(json.dumps([len(c) / 2 / voice.SR for c in clips]))
vo_dur = json.loads(vo_f.read_text())

random.seed(1)
items, sweeps, starts, t, onboard = [], [], [], 0.1, []
for s, dur in zip(plan["scenes"], vo_dur):
    if s["clear"] and onboard:
        sweeps.append(t + SWEEP)
        for it in onboard: it["r"] = t + SWEEP
        onboard, t = [], t + SWEEP
    starts.append(t)
    n = len(s["items"])
    placed = []
    for i, it in enumerate(s["items"]):
        if "tag" in it: img = tag(it["tag"], it.get("color", "#FFE14D"), it["w"] * W)
        else:  # cutouts come out small at the planner's width
            c = cuts[it["cut"]]; w = min(it["w"] * 1.5, 0.6, 0.32 * H * c.width / c.height / W) * W  # tall cutouts capped at 32% of the frame height
            img = c.resize((round(w), round(w * c.height / c.width)), Image.LANCZOS)
        img = shadowed(img, random.uniform(-6, 6))
        x, y = it["x"] * W, it["y"] * H
        for o in placed:  # push down below anything it would overlap
            if abs(x - o["x"]) < (img.width + o["img"].width) / 2 and abs(y - o["y"]) < (img.height + o["img"].height) / 2:
                y = o["y"] + (o["img"].height + img.height) / 2 + 10
        y = min(y, H * 0.68 - img.height / 2)  # keep above the subtitles and the bottom UI zone
        e = {"img": img, "x": x, "y": y, "h": img.height, "a": -1 if not items else t + CARRY + i * min(0.7, dur / n), "r": 1e9}  # the first item is on the table from frame 0
        items.append(e); onboard.append(e); placed.append(e)
    t += dur + 0.15
ps = starts[-1]  # packshot under the last line (CTA)
total = max(t, ps + PACKSHOT)

def ease(p): return 1 - (1 - min(max(p, 0), 1)) ** 3

def paste(fr, im, cx, cy):
    fr.alpha_composite(im, (round(cx - im.width / 2), round(cy - im.height / 2)))

def render(t):
    fr = table.copy().convert("RGBA")
    rnd = random.Random(int(t * FPS))  # same jitter within a frame, new each frame: stop-motion boil
    hands = []
    for e in items:
        if t < e["a"] - CARRY or t > e["r"]: continue
        x, y = e["x"], e["y"]
        if t < e["a"]:
            y = H + e["img"].height - (H + e["img"].height - y) * ease((t - e["a"] + CARRY) / CARRY)
            hands.append((x, y + e["h"] * 0.3))
        elif t < e["a"] + LEAVE:
            hands.append((x, y + e["h"] * 0.3 + (H - y) * ease((t - e["a"]) / LEAVE)))
        if t > e["r"] - SWEEP:
            x -= W * 1.4 * ((t - e["r"] + SWEEP) / SWEEP) ** 2
        paste(fr, e["img"], x + rnd.uniform(-2, 2), y + rnd.uniform(-2, 2))
    for hx, hy in hands:  # fingertips at the item center, arm off the bottom edge
        fr.alpha_composite(hand, (round(hx - tip), round(hy - 30)))
    for r in sweeps:
        if r - SWEEP <= t <= r:
            fr.alpha_composite(sweeper, (round(W - (W * 1.4) * (t - r + SWEEP) / SWEEP), H // 2 - sweeper.height // 2))
    fr = fr.convert("RGB")
    subs.draw(fr, t)
    return fr

# audio: VO lines at scene starts + quiet lo-fi
subs = Subs(starts, vo_dur, [s["vo"] for s in plan["scenes"]])
music = d / "music.mp3"
if not music.exists(): music.write_bytes(music_src.read_bytes())
pcm = bytearray(round(total * voice.SR) * 2)
for i, st in enumerate(starts):
    c = (d / f"vo{i}.raw").read_bytes()
    o = round(st * voice.SR) * 2
    pcm[o:o + len(c)] = c[:len(pcm) - o]
(d / "vo.raw").write_bytes(pcm)

print(f"🎞️  {total:.1f}s · {round(total * FPS)} frames...")
cut = d / "cut.mp4"
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-f", "s16le", "-ar", str(voice.SR), "-ac", "1", "-i", d / "vo.raw", "-i", music, "-filter_complex",
                       f"[0:v]fps=30,format=yuv420p[v];[1:a]aresample=48000,pan=stereo|c0=c0|c1=c0[vo];[2:a]aresample=48000,volume=0.16,atrim=0:{total},afade=t=out:st={total - 1}:d=1[m];[vo][m]amix=inputs=2:normalize=0,alimiter=limit=0.9[a]",
                       "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}", "-c:v", "libx264", "-crf", "18", "-c:a", "aac", "-b:a", "192k", cut], stdin=subprocess.PIPE)
for k in range(round(total * FPS)):
    ff.stdin.write(render(k / FPS).tobytes())
    if k % FPS == 0: print(f"\r   {k / FPS:.0f}/{total:.0f}s", end="", flush=True)
ff.stdin.close(); ff.wait(); print()
subprocess.run([HERE.parent / "3d/packshot.sh", cut, f"{ps:.2f}"], check=True)
cta = d / "cta.png"
im = Image.new("RGBA", (W, H))
f = font(130)
while f.getlength("YOUR HEIGHT") > W * 0.8: f = font(f.size - 2)
ImageDraw.Draw(im).multiline_text((W / 2, H * 0.615), CTA, font=f, fill="white", anchor="ma", align="center", spacing=10, stroke_width=9, stroke_fill="black")
im.save(cta)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", d / "cut_final.mp4", "-i", cta, "-filter_complex",
                f"[0][1]overlay=enable='gte(t,{ps + 0.25:.2f})'", "-c:v", "libx264", "-crf", "18", "-c:a", "copy", d / "final.mp4"], check=True)
(d / "cut_final.mp4").unlink()
print(f"🏁 {d / 'final.mp4'}\n💰 Google $0 · OpenAI (images/TTS) ~${oai.spent:.3f}")
