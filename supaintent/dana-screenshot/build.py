# /// script
# dependencies = ["pillow"]
# ///
"""Dana ep. 2 "One screenshot proves nothing": morning character clips (clips/*.mp4, Omni 1.2 360p + Real-ESRGAN) cut with data inserts.
Numbers: SupaIntent AI prompt tracking study (2026): ~30% of brands gone next day; first brand changes 23% ChatGPT, 25% AI Mode, 32% Gemini.
Usage: uv run build.py  →  out/final.mp4
"""
import json, math, pathlib, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).parent
OUT, SS, L, CLIPS = ROOT / "out", ROOT / "screenshots", ROOT / "logos", ROOT / "clips"
W, H, FPS = 1080, 1920, 30
BG, INK, ACC, GREY, RED, LEAD = "#f6f7fb", "#101828", "#2563eb", "#667085", "#ef4444", 1.05

# ---------- drawing helpers ----------
def font(size, weight=900):
    f = ImageFont.truetype(str(ROOT / "fonts/Display.ttf"), size)
    try: f.set_variation_by_axes([weight])
    except OSError: pass  # static font
    return f

def fit(s, size, weight=900, maxw=W - 100):
    """Font shrunk so one line of s fits maxw."""
    f = font(size, weight)
    return f if f.getlength(s) <= maxw else font(int(size * maxw / f.getlength(s)), weight)

def text(d, y, s, size, fill=INK, stroke=0, sfill=BG, cx=W / 2):
    """Centered multi-line text; returns the y below it."""
    for line in s.split("\n"):
        d.text((cx, y), line, font=fit(line, size), fill=fill, anchor="ma", stroke_width=stroke, stroke_fill=sfill)
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

# ---------- timing from the voice ----------
SHOTS = json.loads((OUT / "shots.json").read_text())
WORDS = json.loads((OUT / "words.json").read_text())
VO_END = SHOTS[-1]["end"]
LENGTH = math.ceil(VO_END + 3)
LINE = [s["start"] for s in SHOTS] + [VO_END]

def at(word, n=0):
    """Start of the n-th spoken occurrence of a word."""
    return [x["s"] for x in WORDS if x["w"].strip(".,?!:'").lower() == word.lower()][n]

def bfont(size, weight=820):
    """Manrope, the site's display font."""
    f = ImageFont.truetype(str(ROOT / "fonts/Brand.ttf"), size); f.set_variation_by_axes([weight]); return f

def lockup_w(size):
    return size * 1.8 + bfont(size).getlength("SupaIntent")

def lockup(img, cx, cy, size, intent="#10202b"):
    """SupaIntent lockup as on the site: icon + Manrope 820, "Supa" in brand blue."""
    f, g = bfont(size), size * 1.5
    x = cx - lockup_w(size) / 2
    logo(img, L / "supaintent-logo-512.png", x + g / 2, cy, int(g))
    d = ImageDraw.Draw(img); x += size * 1.8
    d.text((x, cy), "Supa", font=f, fill="#0053db", anchor="lm")
    d.text((x + f.getlength("Supa"), cy), "Intent", font=f, fill=intent, anchor="lm")

def endcard(line):
    img = Image.new("RGBA", (W, H), "#ffffff"); d = ImageDraw.Draw(img)
    lockup(img, W / 2, 600, 120)
    f = bfont(62, 700); f = f if f.getlength(line) <= W - 120 else bfont(int(62 * (W - 120) / f.getlength(line)), 700)
    d.text((W / 2, 760), line, font=f, fill="#10202b", anchor="ma")
    d.text((W / 2, 870), "supaintent.com", font=bfont(54, 700), fill="#0053db", anchor="ma")
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
        pw = lockup_w(72) / 2 + 60
        dl.rounded_rectangle((W / 2 - pw, 800, W / 2 + pw, 980), 44, fill="#ffffff")
        lockup(lay, W / 2, 890, 72)
        dl.text((W / 2, 1060), sub, font=fit(sub, 52, 700), fill=INK, anchor="ma")
        put(img, lay, t, tl, cy=890)
    return shake(img, t, LINE[4], 16)

# ---------- scenes: Dana morning clips + light inserts; numbers from SupaIntent AI prompt tracking data (2026) ----------
from camera import smooth
import random

class Clip:
    """Streams a character clip at 1080x1920, slowed down to fill the shot when the line is longer than the clip."""
    def __init__(self, name, a, b):
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", CLIPS / name],
                                   capture_output=True, text=True).stdout)
        self.args = ["ffmpeg", "-v", "quiet", "-i", CLIPS / name, "-vf", f"setpts={max(1, (b - a) / dur):.3f}*PTS,fps={FPS},scale={W}:{H}:flags=lanczos",
                     "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
        self.p = self.last = None
    def frame(self):
        self.p = self.p or subprocess.Popen(self.args, stdout=subprocess.PIPE)
        buf = self.p.stdout.read(W * H * 3)
        if len(buf) == W * H * 3: self.last = Image.frombytes("RGB", (W, H), buf).convert("RGBA")
        return self.last.copy()

def fit_b(s, size, weight=820, maxw=W - 100):
    f = bfont(size, weight)
    return f if f.getlength(s) <= maxw else bfont(int(size * maxw / f.getlength(s)), weight)

def btext(d, y, s, size, fill):
    d.text((W / 2, y), s, font=fit_b(s, size), fill=fill, anchor="ma")

def shade_top(img, h=720, a=235):
    g = Image.linear_gradient("L").rotate(180).resize((W, h)).point(lambda v: v * a // 255)
    img.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, h), 12)] * 3, g)), (0, 0))

def clip_scene(name, a, b, over=None):
    c = Clip(name, a, b)
    def s(t):
        img = c.frame()
        if over: over(img, t)
        return img
    return s

def title(img, t, t0, day, line, col):
    shade_top(img)
    lay, dl = layer(); btext(dl, 140, day, 80, "#ffffff"); btext(dl, 240, line, 120, col)
    put(img, lay, t, t0, dur=0.18, start=1.8, cy=280)

def monday(img, t):
    title(img, t, 0, "MONDAY:", "WE'RE #1 IN CHATGPT.", "#ffd84d")
    ts = at("screenshot") - 0.05
    if ts <= t < ts + 0.25:  # camera flash
        img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(230 * (1 - (t - ts) / 0.25)))))
    if t >= at("whole"):
        lay, dl = layer(); f = bfont(46, 700)
        dl.rounded_rectangle((140, 1060, W - 140, 1180), 30, fill="#ffffff")
        dl.text((W / 2, 1120), "Screenshot sent to #everyone", font=f, fill="#0b1220", anchor="mm")
        put(img, lay, t, at("whole"), dur=0.15, start=0.6, cy=1120)

def tuesday(img, t):
    title(img, t, LINE[1], "TUESDAY:", "SAME QUESTION.", "#ffffff")
    if t >= at("list") - 0.1:
        lay, dl = layer(); btext(dl, 400, "NOT ON THE LIST.", 110, RED)
        put(img, lay, t, at("list") - 0.1, dur=0.12, start=2.2, cy=450)

T_DROP = at("About") - 0.1
random.seed(4); GONE = set(random.sample(range(10), 3))

def s_drop(t):
    img = Image.new("RGBA", (W, H), BG); d = ImageDraw.Draw(img)
    btext(d, 120, "SAME PROMPT, NEXT DAY", 70, GREY)
    n = round(30 * smooth((t - at("thirty")) / 0.6))
    btext(d, 210, f"{n}% OF BRANDS GONE", 110, RED if n else INK)
    tf = at("drop") - 0.1
    for k in range(10):
        y0 = 400 + k * 90; lay, dl = layer()
        dl.rounded_rectangle((120, y0, W - 120, y0 + 72), 36, fill="#ffffff", outline="#e4e7ec", width=3)
        dl.text((175, y0 + 36), f"{k + 1}.", font=bfont(40, 700), fill=GREY, anchor="lm")
        dl.rounded_rectangle((250, y0 + 26, 250 + 220 + (k * 53) % 380, y0 + 46), 10, fill="#cbd5e1")
        if k in GONE and t > tf:  # dropped brands fall off with a spin
            e = (t - tf - 0.12 * sorted(GONE).index(k)); e = max(e, 0)
            dl.rounded_rectangle((120, y0, W - 120, y0 + 72), 36, outline=RED, width=6)
            lay = lay.rotate(-25 * e, center=(W / 2, y0 + 36)); img.alpha_composite(lay, (0, int(1400 * e * e)))
        else:
            img.alpha_composite(lay)
    return shake(img, t, tf, 14)

ENG = (("chatgpt.png", "ChatGPT", 23), ("google-ai-mode.png", "Google AI Mode", 25), ("gemini.png", "Gemini", 32))

def s_engines(t):
    img = Image.new("RGBA", (W, H), BG); d = ImageDraw.Draw(img)
    btext(d, 120, "TOP PICK CHANGED", 100, INK); btext(d, 240, "from one day to the next", 60, GREY)
    for k, (f, name, v) in enumerate(ENG):
        y, tk = 440 + k * 270, LINE[3] + 0.2 + k * 0.15
        if t < tk: continue
        hot = k == 0
        logo(img, L / f, 160, y + 50, 110, disc=True)
        d.text((250, y + 50), name, font=bfont(60, 760), fill=INK, anchor="lm")
        p = smooth((t - tk) / 0.6)
        d.rounded_rectangle((110, y + 130, W - 110, y + 190), 30, fill="#e4e7ec")
        d.rounded_rectangle((110, y + 130, 110 + (W - 220) * v / 40 * p, y + 190), 30, fill=ACC if hot else "#94a3b8")
        d.text((W - 110, y + 50), f"{round(v * p)}%", font=bfont(76), fill=ACC if hot else GREY, anchor="rm")
    return img

def outro(img, t):
    tl = at("SupaIntent", -1) - 0.3
    if t < tl: return
    lay, dl = layer(); pw = lockup_w(72) / 2 + 60
    dl.rounded_rectangle((W / 2 - pw, 1060, W / 2 + pw, 1220), 44, fill="#ffffff")
    lockup(lay, W / 2, 1140, 72)
    put(img, lay, t, tl, cy=1140)

SCENES = [(0, LINE[1], clip_scene("k1.mp4", 0, LINE[1], monday)), (LINE[1], LINE[2], clip_scene("k2.mp4", LINE[1], LINE[2], tuesday)),
          (LINE[2], T_DROP, clip_scene("k3.mp4", LINE[2], T_DROP)), (T_DROP, LINE[3], s_drop), (LINE[3], LINE[4], s_engines),
          (LINE[4], VO_END + 0.2, clip_scene("k4.mp4", LINE[4], VO_END + 0.2, outro)), (VO_END + 0.2, LENGTH, s_end_factory("One screenshot proves nothing."))]

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
subprocess.run(["uv", "run", "-q", ROOT / "captions.py", edit, OUT / "words.json", OUT / "final.mp4"], check=True)  # calm narrator: no slowdown
print(f"🏁 {OUT / 'final.mp4'}")
