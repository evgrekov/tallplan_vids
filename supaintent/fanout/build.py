# /// script
# dependencies = ["pillow"]
# ///
"""Free local edit for "ChatGPT doesn't search what you typed": every frame is drawn with Pillow and piped to ffmpeg,
music is ducked under out/voice.wav, captions.py burns the captions, the result is slowed 10% (same pitch).
Numbers: 17,962 recorded ChatGPT searches (get-cited-chatgpt article).
Usage: uv run build.py  →  out/final.mp4
"""
import json, math, pathlib, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).parent
OUT, SS, L = ROOT / "out", ROOT / "screenshots", ROOT / "logos"
W, H, FPS = 1080, 1920, 30
BG, INK, ACC, GREY, RED, LEAD = "#050b05", "#d8ffd0", "#39ff14", "#4f8f4f", "#ff3355", 1.15

# ---------- drawing helpers ----------
def font(size, weight=900):
    f = ImageFont.truetype(str(ROOT / "fonts/Display.ttf"), size)
    try: f.set_variation_by_axes([weight])
    except OSError: pass  # static font
    return f

def text(d, y, s, size, fill=INK, stroke=0, sfill=BG, cx=W / 2):
    """Centered multi-line text; returns the y below it."""
    for line in s.split("\n"):
        d.text((cx, y), line, font=font(size), fill=fill, anchor="ma", stroke_width=stroke, stroke_fill=sfill)
        y += int(size * LEAD)
    return y

def box(d, y, s, size, fg, bg, cx=W / 2, r=24):
    f = font(size); w = f.getlength(s)
    d.rounded_rectangle((cx - w / 2 - 34, y - 18, cx + w / 2 + 34, y + size * LEAD + 4), r, fill=bg)
    d.text((cx, y), s, font=f, fill=fg, anchor="ma")

def logo(img, path, cx, cy, size, disc=False):
    if disc:
        r = size * 0.62
        ImageDraw.Draw(img).ellipse((cx - r, cy - r, cx + r, cy + r), fill="#ffffff")
    l = Image.open(path).convert("RGBA")
    l = l.resize((size, round(size * l.height / l.width)), Image.LANCZOS)
    img.alpha_composite(l, (int(cx - l.width / 2), int(cy - l.height / 2)))

def ease(x):
    x = min(max(x, 0), 1)
    return 1 - (1 - x) ** 3

def put(base, lay, t, t0, dur=0.22, cx=W / 2, cy=H / 2, start=1.35):
    """Composite a full-frame RGBA layer with a pop-in (scale start→1 around cx,cy) from t0."""
    if t < t0: return
    k = start + (1 - start) * ease((t - t0) / dur)
    if abs(k - 1) < 1e-3:
        base.alpha_composite(lay); return
    s = lay.resize((round(W * k), round(H * k)))
    base.alpha_composite(s, (round(cx - cx * k), round(cy - cy * k))) if k <= 1 else \
        base.alpha_composite(s.crop((round(cx * k - cx), round(cy * k - cy), round(cx * k - cx) + W, round(cy * k - cy) + H)))

def shake(img, t, t0, amp=26, dur=0.3):
    if not 0 <= t - t0 < dur: return img
    a = amp * (1 - (t - t0) / dur)
    dx, dy = round(a * math.sin(t * 90)), round(a * math.cos(t * 70))
    out = Image.new("RGBA", (W, H), img.getpixel((5, 5)))
    out.alpha_composite(img, (max(dx, 0), max(dy, 0)), (max(-dx, 0), max(-dy, 0)))
    return out

def layer(): 
    lay = Image.new("RGBA", (W, H)); return lay, ImageDraw.Draw(lay)

def shot(name, crop=None, width=900, radius=28):
    """Screenshot (optionally cropped) scaled to width with rounded corners and a soft frame."""
    s = Image.open(SS / name).convert("RGBA")
    if crop: s = s.crop(crop)
    s = s.resize((width, round(s.height * width / s.width)), Image.LANCZOS)
    m = Image.new("L", s.size); ImageDraw.Draw(m).rounded_rectangle((0, 0, s.width - 1, s.height - 1), radius, fill=255)
    out = Image.new("RGBA", s.size); out.paste(s, (0, 0), m); return out

def place(img, pic, t, t0, y, dur=0.25, start=1.25):
    lay, _ = layer(); lay.alpha_composite(pic, ((W - pic.width) // 2, y))
    put(img, lay, t, t0, dur=dur, start=start, cy=y + pic.height // 2)

# ---------- timing from the voice ----------
SHOTS = json.loads((OUT / "shots.json").read_text())
WORDS = json.loads((OUT / "words.json").read_text())
VO_END = SHOTS[-1]["end"]
LENGTH = math.ceil(VO_END + 3)
LINE = [s["start"] for s in SHOTS] + [VO_END]

def at(word, n=0):
    """Start of the n-th spoken occurrence of a word."""
    return [x["s"] for x in WORDS if x["w"].strip(".,?!:'").lower() == word.lower()][n]

def endcard(line):
    img = Image.new("RGBA", (W, H), "#ffffff"); d = ImageDraw.Draw(img)
    logo(img, L / "supaintent-logo-512.png", W // 2, 420, 300)
    d.text((W / 2, 620), "SupaIntent", font=font(130), fill="#0053db", anchor="ma")
    d.text((W / 2, 820), line, font=font(62, 700), fill="#0b1b3a", anchor="ma")
    d.text((W / 2, 924), "supaintent.com", font=font(52, 700), fill="#0053db", anchor="ma")
    return img

def s_end_factory(line):
    end, t0 = endcard(line), VO_END + 0.2
    def s(t):
        k = 1 + 0.06 * (t - t0) / (LENGTH - t0)
        z = end.resize((round(W * k), round(H * k))); x, y = (z.width - W) // 2, (z.height - H) // 2
        return z.crop((x, y, x + W, y + H))
    return s

def cta(t, big, sub, bg=None):
    img = Image.new("RGBA", (W, H), bg or BG); d = ImageDraw.Draw(img)
    lay, dl = layer(); text(dl, 240, big, 108, ACC)
    put(img, lay, t, LINE[4], dur=0.15, start=1.8, cy=360)
    tl = at("SupaIntent", -1) - 0.3
    if t >= tl:
        lay, dl = layer()
        dl.rounded_rectangle((W / 2 - 330, 780, W / 2 + 330, 1000), 44, fill="#ffffff")
        logo(lay, L / "supaintent-logo-512.png", W / 2 - 205, 890, 130)
        dl.text((W / 2 + 70, 890), "SupaIntent", font=font(76), fill="#0053db", anchor="mm")
        dl.text((W / 2, 1060), sub, font=font(52, 700), fill=INK, anchor="ma")
        put(img, lay, t, tl, cy=890)
    return shake(img, t, LINE[4], 16)

# ---------- scenes: hacker terminal, phosphor green on black, mono ----------
TYPED = "best crm for small business"
SEARCHED = "best CRM software for small businesses 2026 HubSpot Pipedrive Zoho Freshsales pricing"

def scan(img):
    s = Image.new("RGBA", (W, H)); ds = ImageDraw.Draw(s)
    for y in range(0, H, 6): ds.line((0, y, W, y), fill=(0, 0, 0, 70))
    img.alpha_composite(s)

def typed(d, x, y, s, n, size, fill, width=26):
    lines = [s[i:i + width] for i in range(0, min(n, len(s)), width)]
    for k, line in enumerate(lines): d.text((x, y + k * size * 1.3), line, font=font(size), fill=fill)
    return y + len(lines) * size * 1.3

def s_hook(t):
    img = Image.new("RGBA", (W, H), BG); d = ImageDraw.Draw(img)
    text(d, 100, "CHATGPT DOESN'T\nSEARCH WHAT\nYOU TYPED", 92, ACC)
    d.text((80, 560), "> you typed:", font=font(48), fill=GREY)
    y = typed(d, 80, 630, TYPED, len(TYPED), 56, INK, 28)
    if t > 0.5:
        d.line((80, 665, 80 + 28 * 33.6 * min(1, (t - 0.5) / 0.3), 665), fill=RED, width=8)
    if t > 0.7:
        d.text((80, 820), "> it searched:", font=font(48), fill=GREY)
        typed(d, 80, 890, SEARCHED, int((t - 0.7) * 90), 52, ACC, 30)
    scan(img)
    return shake(img, t, 1.0, 20)

def s_repeat(t):
    img = Image.new("RGBA", (W, H), BG); d = ImageDraw.Draw(img)
    d.text((80, 150), "> 17,962 searches logged", font=font(54), fill=GREY)
    typed(d, 80, 300, SEARCHED, len(SEARCHED), 40, GREY, 40)
    tf = at("five") - 0.1
    if t >= tf:
        lay, dl = layer(); text(dl, 640, "5.3%", 240, ACC)
        dl.text((W / 2, 940), "repeat your prompt", font=font(64), fill=INK, anchor="ma")
        put(img, lay, t, tf, dur=0.15, start=2, cy=800)
    scan(img)
    return shake(img, t, tf, 20)

def s_add(t):
    img = Image.new("RGBA", (W, H), BG); d = ImageDraw.Draw(img)
    d.text((80, 150), "> what ChatGPT adds:", font=font(58), fill=GREY)
    for k, (label, v, w) in enumerate((("+ \"2026\"", 27, "Twenty-seven"), ("+ \"official\"", 12, "Twelve"))):
        y, tk = 420 + k * 360, at(w) - 0.1
        if t < tk: continue
        d.text((80, y), label, font=font(84), fill=INK)
        p = ease((t - tk) / 0.5)
        d.rectangle((80, y + 130, 80 + 30 * v * p, y + 220), fill=ACC)
        d.text((100 + 30 * v * p, y + 175), f"{v}%", font=font(80), fill=ACC, anchor="lm")
    scan(img)
    return img

def s_fix(t):
    img = Image.new("RGBA", (W, H), BG); d = ImageDraw.Draw(img)
    d.text((80, 150), "$ ./fix.sh", font=font(64), fill=GREY)
    for k, (label, w) in enumerate((("[x] answer at the top", "top"), ("[x] facts current", "current"))):
        tk = at(w) - 0.3
        if t >= tk: typed(d, 80, 380 + k * 200, label, int((t - tk) * 60), 64, ACC, 24)
    scan(img)
    return img

s_cta = lambda t: cta(t, "SEE THE REAL\nSEARCHES", "fan-out queries, per prompt")
SCENES = [(0, LINE[1], s_hook), (LINE[1], LINE[2], s_repeat), (LINE[2], LINE[3], s_add), (LINE[3], LINE[4], s_fix),
          (LINE[4], VO_END + 0.2, s_cta), (VO_END + 0.2, LENGTH, s_end_factory("See what ChatGPT searches"))]

# ---------- audio mix: music ducked under the voice ----------
mix = OUT / "audio_mix.m4a"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", OUT / "voice.wav", "-stream_loop", "-1", "-i", OUT / "music.mp3", "-filter_complex",
                "[1:a]volume=0.35[m];[m][0:a]sidechaincompress=threshold=0.03:ratio=8:release=300[d];"
                "[0:a][d]amix=inputs=2:normalize=0,alimiter=limit=0.95,atrim=0:" + str(LENGTH), "-c:a", "aac", "-b:a", "192k", mix], check=True)

# ---------- render ----------
edit = OUT / "edit.mp4"
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                       "-i", "-", "-i", mix, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "18",
                       "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", edit], stdin=subprocess.PIPE)
for n in range(LENGTH * FPS):
    t = n / FPS
    frame = next(f for a, b, f in SCENES if a <= t < b)(t)
    ff.stdin.write(frame.convert("RGB").tobytes())
    if n % FPS == 0: print(f"🎬 {t:4.0f}s", end="\r", flush=True)
ff.stdin.close(); assert ff.wait() == 0
fast = OUT / "final_1x.mp4"
subprocess.run(["uv", "run", "-q", ROOT / "captions.py", edit, OUT / "words.json", fast], check=True)
print("\n🐢 slowing down 10%...")  # the voice reads too fast at 1x
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", fast, "-filter_complex", "[0:v]setpts=1.1*PTS,fps=30[v];[0:a]atempo=0.90909[a]",
                "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                OUT / "final.mp4"], check=True)
print(f"🏁 {OUT / 'final.mp4'}")
