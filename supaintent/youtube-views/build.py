# /// script
# dependencies = ["pillow"]
# ///
"""Free local edit for "AI quotes small YouTube videos": every frame is drawn with Pillow and piped to ffmpeg,
music is ducked under out/voice.wav, captions.py burns the captions, the result is slowed 10% (same pitch).
Numbers: SupaIntent YouTube study (162,168 answers, Aug-Oct 2026) and YouTube Radar for a CRM project.
Usage: uv run build.py  →  out/final.mp4
"""
import json, math, pathlib, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).parent
OUT, SS, L = ROOT / "out", ROOT / "screenshots", ROOT / "logos"
W, H, FPS = 1080, 1920, 30
BG, INK, ACC, GREY, LEAD = "#0a0a0a", "#ffffff", "#ff0033", "#9a9a9a", 1.0

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

# ---------- scenes: dark cinematic, YouTube red, condensed caps ----------
CARD = shot("youtube-radar-videos.png", (8, 82, 420, 505), 740)

def vignette(img):
    v = Image.new("RGBA", (W, H)); dv = ImageDraw.Draw(v)
    for k in range(12): dv.rectangle((k * 14, k * 22, W - k * 14, H - k * 22), outline=(0, 0, 0, 22), width=18)
    img.alpha_composite(v)

def s_hook(t):
    img = Image.new("RGBA", (W, H), BG); d = ImageDraw.Draw(img)
    z = 1 + 0.08 * ease(t / 3)  # slow push-in on the real video card
    c = CARD.resize((round(CARD.width * z), round(CARD.height * z)))
    img.alpha_composite(c, ((W - c.width) // 2, 420 - (c.height - CARD.height) // 2))
    lay, dl = layer(); text(dl, 70, "2,288 VIEWS", 170, INK)
    put(img, lay, t, 0, dur=0.2, start=2.3, cy=220)
    tc = at("ten") - 0.1
    if t >= tc:
        lay, dl = layer()
        dl.rectangle((60, 1540, 1020, 1740), fill=ACC)
        dl.text((W / 2, 1640), "10 AI CITATIONS", font=font(140), fill=INK, anchor="mm")
        put(img, lay, t, tc, dur=0.12, start=2.5, cy=1640)
    vignette(img)
    return shake(img, t, tc if t >= tc else 0.03, 30, 0.35)

def s_split(t):
    img = Image.new("RGBA", (W, H), BG); d = ImageDraw.Draw(img)
    logo(img, L / "google-ai-mode.png", 270, 330, 170, disc=True)
    d.text((270, 470), "GOOGLE AI MODE", font=font(56), fill=GREY, anchor="ma")
    put(img, (lambda l: (text(ImageDraw.Draw(l), 560, "1 IN 5", 230, ACC), l)[1])(Image.new("RGBA", (W, H))), t, LINE[1] + 0.3, dur=0.15, start=2, cy=680)
    tc = at("ChatGPT") - 0.1
    if t >= tc:
        logo(img, L / "chatgpt.png", 270, 1580, 130, disc=True)
        d.text((420, 1580), "0.2%", font=font(170), fill=GREY, anchor="lm")
    d.line((80, 1450, 1000, 1450), fill="#2a2a2a", width=4)
    youtube = Image.open(L / "youtube.png").convert("RGBA").resize((150, 150))
    img.alpha_composite(youtube, (800, 255))
    return shake(img, t, tc, 18)

def s_median(t):
    img = Image.new("RGBA", (W, H), BG); d = ImageDraw.Draw(img)
    d.text((W / 2, 150), "MEDIAN CITED VIDEO", font=font(90), fill=GREY, anchor="ma")
    n = round(2665 * ease((t - LINE[2] + 0.4) / 1.6))
    d.text((W / 2, 560), f"{n:,}", font=font(330), fill=INK, anchor="mm")
    d.text((W / 2, 780), "VIEWS", font=font(130), fill=ACC, anchor="ma")
    return img

def s_transcript(t):
    img = Image.new("RGBA", (W, H), BG); d = ImageDraw.Draw(img)
    text(d, 150, "TRANSCRIPT", 170, INK)
    text(d, 340, "> VIEW COUNT", 120, ACC)
    for k in range(8):  # transcript lines being read
        y, w = 620 + k * 80, [820, 700, 860, 640, 780, 720, 840, 560][k]
        p = ease((t - LINE[3] - k * 0.12) / 0.4)
        d.rounded_rectangle((130, y, 130 + w * p, y + 36), 18, fill="#3a3a3a" if k % 3 else ACC)
    return shake(img, t, LINE[3], 20)

s_cta = lambda t: cta(t, "WHICH VIDEOS\nSHAPE YOUR NICHE?", "YouTube Radar")
SCENES = [(0, LINE[1], s_hook), (LINE[1], LINE[2], s_split), (LINE[2], LINE[3], s_median), (LINE[3], LINE[4], s_transcript),
          (LINE[4], VO_END + 0.2, s_cta), (VO_END + 0.2, LENGTH, s_end_factory("Find the videos AI cites"))]

# ---------- audio mix: music ducked under the voice ----------
mix = OUT / "audio_mix.m4a"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", OUT / "voice.wav", "-stream_loop", "-1", "-i", OUT / "music.mp3", "-filter_complex",
                "[0:a]apad[vo];[vo]asplit[v1][v2];[1:a]volume=0.35[m];[m][v1]sidechaincompress=threshold=0.03:ratio=8:release=300[d];"
                "[v2][d]amix=inputs=2:normalize=0,alimiter=limit=0.95,atrim=0:" + str(LENGTH), "-c:a", "aac", "-b:a", "192k", mix], check=True)

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
