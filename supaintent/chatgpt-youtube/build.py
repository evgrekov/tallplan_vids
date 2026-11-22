# /// script
# dependencies = ["pillow"]
# ///
"""Free local edit: every frame is drawn with Pillow (pop-ins, counters, shakes, a keyframed camera that zooms into the
screenshots on the spoken word) and piped to ffmpeg; out/audio_mix.m4a goes under it, captions.py burns the captions.
Audio, captions and the end card are unchanged; only the visuals move. Timings are word onsets measured from pauses in out/voice.wav (silencedetect).
Usage: uv run build.py  →  out/final.mp4
"""
import math, pathlib, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).parent
OUT, SS, L = ROOT / "out", ROOT / "screenshots", ROOT / "logos"
W, H, FPS, LENGTH = 1080, 1920, 30, 30
BLUE, NAVY, WHITE, YELLOW, RED, ORANGE, GREY = "#0053db", "#0b1b3a", "#ffffff", "#f7ff14", "#ff0033", "#ff4500", "#8a93a6"
FOCUS_Y = 0.36  # zoom targets land at 36% height: captions sit at 70%

# ---------- drawing helpers ----------
def font(size, weight=900):
    f = ImageFont.truetype(str(ROOT / "fonts/Montserrat.ttf"), size)
    f.set_variation_by_axes([weight])
    return f

def canvas(bg=BLUE):
    img = Image.new("RGB", (W, H), bg)
    return img, ImageDraw.Draw(img)

def text(d, y, s, size, fill=WHITE, weight=900, cx=W / 2):
    """Centered multi-line text; returns the y below it."""
    f = font(size, weight)
    for line in s.split("\n"):
        d.text((cx, y), line, font=f, fill=fill, anchor="ma", stroke_width=max(2, size // 22), stroke_fill=NAVY)
        y += int(size * 1.15)
    return y

def youtube(d, cx, cy, w, color=RED):
    h = w * 0.7
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), h * 0.28, fill=color)
    t = h * 0.28
    d.polygon([(cx - t * 0.8, cy - t), (cx - t * 0.8, cy + t), (cx + t * 1.1, cy)], fill=WHITE)

def reddit(d, cx, cy, r):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ORANGE)
    d.text((cx, cy), "r/", font=font(int(r)), fill=WHITE, anchor="mm")

def logo(img, path, cx, cy, size, disc=False):
    if disc:  # white disc so a dark logo stays visible on dark backgrounds
        r = size * 0.62
        ImageDraw.Draw(img).ellipse((cx - r, cy - r, cx + r, cy + r), fill=WHITE)
    l = Image.open(path).convert("RGBA").resize((size, size))
    img.paste(l, (int(cx - size / 2), int(cy - size / 2)), l)

def layer():
    return Image.new("RGBA", (W, H)), None

# ---------- motion helpers ----------
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

class Cam:
    """Keyframed camera over a screenshot: keys = [(t, x, y, view_width)] in screenshot px; moves ease in 0.35 s, drift zoom between.
    boxes = [(t0, t1, (x0, y0, x1, y1))]: highlight in screenshot px, shown while t0 <= t < t1."""
    def __init__(self, path, keys, bg=NAVY, pad=1400, boxes=()):
        s = Image.open(path).convert("RGB")
        self.src = Image.new("RGB", (s.width + 2 * pad, s.height + 2 * pad), bg)
        self.src.paste(s, (pad, pad))
        self.keys, self.pad, self.boxes = keys, pad, boxes

    def __call__(self, t):
        ks = self.keys
        i = max(j for j in range(len(ks)) if ks[j][0] <= t) if t >= ks[0][0] else 0
        p, k = ks[max(i - 1, 0)], ks[i]
        e = ease((t - k[0]) / 0.35) if i else 1
        x, y, vw = (p[n] + (k[n] - p[n]) * e for n in (1, 2, 3))
        vw *= 1 - 0.025 * max(t - k[0], 0)  # slow push-in while holding
        vh = vw * H / W
        cx, cy = x + self.pad, y + self.pad + (0.5 - FOCUS_Y) * vh
        box = (cx - vw / 2, cy - vh / 2, cx + vw / 2, cy + vh / 2)
        img = self.src.resize((W, H), Image.BILINEAR, box=tuple(map(round, box))).convert("RGBA")
        hl = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(hl)
        f = lambda x, y: ((x + self.pad - box[0]) * W / vw, (y + self.pad - box[1]) * H / vh)
        for t0, t1, (x0, y0, x1, y1) in self.boxes:
            if t0 <= t < t1:
                a = ease((t - t0) / 0.15)
                d.rounded_rectangle((*f(x0, y0), *f(x1, y1)), 18, fill=(247, 255, 20, round(90 * a)), outline=(247, 255, 20, round(255 * a)), width=9)
        img.alpha_composite(hl)
        return img

def pill(lay_d, y, s, size, fill=YELLOW):
    """Title on a dark pill so it reads over any screenshot."""
    f = font(size)
    w = f.getlength(s)
    lay_d.rounded_rectangle((W / 2 - w / 2 - 40, y - 24, W / 2 + w / 2 + 40, y + size * 1.15 + 6), 30, fill=NAVY + "ee")
    lay_d.text((W / 2, y), s, font=f, fill=fill, anchor="ma")

def titled(s, size=78, fill=YELLOW, y=130):
    lay = Image.new("RGBA", (W, H)); pill(ImageDraw.Draw(lay), y, s, size, fill); return lay

# ---------- static layers ----------
def L_text(lines, y, size, fill=WHITE):
    lay = Image.new("RGBA", (W, H)); text(ImageDraw.Draw(lay), y, lines, size, fill); return lay

def L_icon(fn):
    lay = Image.new("RGBA", (W, H)); fn(lay, ImageDraw.Draw(lay)); return lay

yt_big = L_icon(lambda i, d: youtube(d, W / 2, 560, 420))
gpt_big = L_icon(lambda i, d: logo(i, L / "chatgpt.png", W / 2, 560, 300, True))
cross = L_icon(lambda i, d: (d.line((W / 2 - 300, 300, W / 2 + 300, 820), fill=WHITE, width=40),
                             d.line((W / 2 + 300, 300, W / 2 - 300, 820), fill=WHITE, width=40)))
gpt_small = L_icon(lambda i, d: logo(i, L / "chatgpt.png", W / 2 - 190, 380, 180, True))
yt_small = L_icon(lambda i, d: youtube(d, W / 2 + 190, 380, 220))
yt_grey = L_icon(lambda i, d: youtube(d, W / 2, 470, 340, GREY))
gpt_mid = L_icon(lambda i, d: logo(i, L / "chatgpt.png", W / 2, 330, 170, True))

def counter(img, t, t0, t1, end, fmt, y, size, fill=YELLOW):
    v = end * ease((t - t0) / (t1 - t0))
    text(ImageDraw.Draw(img), y, fmt(v), size, fill)

# ---------- scenes (start, end, draw(t) → RGBA) ----------
def s_hook(t):
    img = Image.new("RGBA", (W, H), BLUE)
    if t < 1.55:
        put(img, yt_big, t, 0.0)
        put(img, L_HOOK1, t, 0.3)
    elif t < 2.32:
        put(img, gpt_big, t, 1.55)
        put(img, L_HOOK2, t, 1.65)
    else:
        img = Image.new("RGBA", (W, H), RED)
        put(img, yt_big, t, 2.32, start=1)
        put(img, cross, t, 2.32, dur=0.12, start=2)
        put(img, L_STOP, t, 2.32, dur=0.12, start=1.8)
        img = shake(img, t, 2.37)
    return img

def s_data(t):
    img = Image.new("RGBA", (W, H), NAVY)
    put(img, gpt_small, t, 2.96)
    put(img, yt_small, t, 3.15)
    counter(img, t, 3.3, 4.6, 162000, lambda v: f"{round(v):,}", 640, 190)
    put(img, L_ANSWERS, t, 4.5)
    return shake(img, t, 4.6, 14)

def s_zero(t):
    img = Image.new("RGBA", (W, H), BLUE)
    if t < 7.84:
        put(img, gpt_small, t, 6.07)
        put(img, yt_small, t, 6.07 + 0.15)
        put(img, L_Q, t, 6.4)
    elif t < 9.28:
        put(img, gpt_mid, t, 7.84)
        counter(img, t, 7.84, 8.7, 0.2, lambda v: f"{v:.1f}%", 520, 320)
        put(img, L_CITE, t, 8.4)
        img = shake(img, t, 8.7, 18)
    else:
        img = Image.new("RGBA", (W, H), NAVY)
        put(img, yt_grey, t, 9.28, start=1)
        put(img, L_NEVER, t, 9.29, dur=0.15, start=1.6)
        img = shake(img, t, 9.33)
    return img

# ChatGPT ranking: tab → G2 → Trustpilot → Capterra → Reddit, then the whole list
cam_tab = Cam(SS / "top-domains-chatgpt-header.png", [(10.11, 576, 300, 1000), (10.8, 577, 245, 480)])
ROW = {"g2": 192, "trustpilot": 282, "capterra": 373, "bbb": 463, "reddit": 554}
cam_rank = Cam(SS / "top-domains-chatgpt-table.png",
               [(11.6, 664, 380, 1150), (12.11, 380, ROW["g2"], 560), (12.45, 380, ROW["trustpilot"], 560),
                (12.93, 380, ROW["capterra"], 560), (13.46, 380, ROW["reddit"], 560), (14.33, 330, ROW["reddit"], 440),
                (15.22, 664, 400, 1150)],
               boxes=[(t0, t1, (8, ROW[k] - 44, 1321, ROW[k] + 44)) for k, t0, t1 in
                      (("g2", 12.11, 12.45), ("trustpilot", 12.45, 12.93), ("capterra", 12.93, 13.46), ("reddit", 13.46, 99))])

def s_rank(t):
    if t < 11.6:
        img = cam_tab(t)
        put(img, titled("What does ChatGPT cite?"), t, 10.2)
    else:
        img = cam_rank(t)
        if t < 14.33: put(img, titled("ChatGPT's top sources"), t, 11.6)
        elif t < 15.22: put(img, titled("Reddit = YES", 92), t, 14.33, start=1.6)
        else: put(img, titled("YouTube? Not in the list", 70, "#ff5c7a"), t, 15.22, start=1.6)
        img = shake(img, t, 15.27, 16)
    return img

def s_but(t):
    img = Image.new("RGBA", (W, H), YELLOW)
    put(img, L_BUT, t, 16.4, dur=0.1, start=1.8)
    return shake(img, t, 16.45, 30)

# Google AI Mode ranking: tab → YouTube row → 28%
cam_google = Cam(SS / "top-domains-google-ai-mode.png",
                 [(16.82, 518, 300, 1000), (17.0, 788, 221, 460), (18.4, 280, 709, 520), (19.81, 470, 709, 360)],
                 boxes=[(18.4, 19.81, (8, 674, 1028, 744)), (19.81, 99, (446, 682, 522, 736))])

def s_google(t):
    img = cam_google(t)
    if t < 18.4: put(img, titled("Google's AI answers"), t, 16.9)
    elif t < 19.81: put(img, titled("YouTube = #1", 92), t, 18.4, start=1.6)
    else:
        put(img, titled("28% of answers", 92), t, 19.81, start=1.6)
        img = shake(img, t, 19.86, 16)
    return img

def s_split(t):
    img = Image.new("RGBA", (W, H), BLUE)
    ImageDraw.Draw(img).rectangle((W // 2, 0, W, H), fill=NAVY)
    # left half slides in on "Reddit", right half on "YouTube"
    for lay, t0, dx in ((L_LEFT, 20.85, -W // 2), (L_RIGHT, 22.85, W // 2)):
        if t >= t0: img.alpha_composite(lay, (round(dx * (1 - ease((t - t0) / 0.3))), 0))
    return img

# ---------- end card (unchanged) ----------
def endcard():
    img, d = canvas("#ffffff")
    logo(img, L / "supaintent-logo-512.png", W // 2, 420, 300)
    d.text((W / 2, 620), "SupaIntent", font=font(130), fill=BLUE, anchor="ma")
    d.text((W / 2, 820), "See what every AI cites", font=font(64, 700), fill=NAVY, anchor="ma")
    d.text((W / 2, 820 + 74 + 30), "supaintent.com/tools/top-domains", font=font(46, 700), fill=BLUE, anchor="ma")
    return img.convert("RGBA")

END = endcard()

def s_end(t):
    k = 1 + 0.06 * (t - 24.38) / (LENGTH - 24.38)  # same slow push-in as before
    s = END.resize((round(W * k), round(H * k)))
    x, y = (s.width - W) // 2, (s.height - H) // 2
    return s.crop((x, y, x + W, y + H))

L_HOOK1 = L_text("Making YouTube\nvideos?", 860, 104)
L_HOOK2 = L_text("…to show up\nin ChatGPT?", 860, 104)
L_STOP = L_text("STOP", 900, 260, YELLOW)
L_ANSWERS = L_text("AI answers\nanalyzed", 880, 100)
L_Q = L_text("YouTube in\nChatGPT answers?", 640, 100)
L_CITE = L_text("of ChatGPT answers\ncite YouTube", 900, 76)
L_NEVER = L_text("BASICALLY\nNEVER", 760, 170, YELLOW)
L_BUT = L_text("BUT…", 640, 300, NAVY)

def L_side(cx, title, lines, icon):
    lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay)
    logo(lay, *title, True)
    yy = 640
    for s in lines:
        d.text((cx, yy), s, font=font(80), fill=WHITE, anchor="ma"); yy += 100
    icon(d)
    return lay

L_LEFT = L_side(W // 4, (L / "chatgpt.png", W // 4, 420, 170), ["Reddit", "+ reviews"], lambda d: reddit(d, W // 4, 960, 95))
L_RIGHT = L_side(3 * W // 4, (L / "google-ai-mode.png", 3 * W // 4, 420, 170), ["YouTube"], lambda d: youtube(d, 3 * W // 4, 900, 220))

SCENES = [(0, 2.96, s_hook), (2.96, 6.06, s_data), (6.06, 10.11, s_zero), (10.11, 16.4, s_rank),
          (16.4, 16.82, s_but), (16.82, 20.8, s_google), (20.8, 24.38, s_split), (24.38, LENGTH, s_end)]

# ---------- render ----------
edit = OUT / "edit.mp4"
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                       "-i", "-", "-i", OUT / "audio_mix.m4a", "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "18",
                       "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", edit], stdin=subprocess.PIPE)
for n in range(LENGTH * FPS):
    t = n / FPS
    draw = next(f for a, b, f in SCENES if a <= t < b)
    ff.stdin.write(draw(t).convert("RGB").tobytes())
    if n % FPS == 0: print(f"🎬 {t:4.0f}s", end="\r", flush=True)
ff.stdin.close(); assert ff.wait() == 0
subprocess.run(["uv", "run", "-q", ROOT / "captions.py", edit, OUT / "words.json", OUT / "final.mp4"], check=True)
print(f"\n🏁 {OUT / 'final.mp4'}")
