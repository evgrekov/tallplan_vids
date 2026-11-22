# /// script
# dependencies = ["pillow"]
# ///
"""Free local edit for "AI trusts what others say": every frame is drawn with Pillow and piped to ffmpeg,
music is ducked under out/voice.wav, captions.py burns the captions, the result is slowed 10% (same pitch).
Numbers: review sites study (167,514 answers) and Reddit study (160,965 answers), 2026.
Usage: uv run build.py  →  out/final.mp4
"""
import json, math, pathlib, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).parent
OUT, SS, L = ROOT / "out", ROOT / "screenshots", ROOT / "logos"
W, H, FPS = 1080, 1920, 30
BG, INK, ACC, GREY, RED, LEAD = "#6d28d9", "#ffffff", "#facc15", "#c4b5fd", "#ff3b3b", 1.08

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

# ---------- scenes: loud purple, yellow, speech bubbles, Syne ----------
QUOTES = ["Switched last year, no regrets", "Best support we've had", "Honestly the easiest setup", "Our team loves it", "Cheaper than the rest"]

def bubble(d, x, y, w, s, fill, ink, size=46):
    d.rounded_rectangle((x, y, x + w, y + size * 2.2), 40, fill=fill)
    d.polygon([(x + 60, y + size * 2.2), (x + 110, y + size * 2.2), (x + 50, y + size * 2.2 + 50)], fill=fill)
    d.text((x + 40, y + size * 1.1), s, font=font(size, 700), fill=ink, anchor="lm")

def s_hook(t):
    img = Image.new("RGBA", (W, H), BG); d = ImageDraw.Draw(img)
    lay, dl = layer(); text(dl, 110, "AI DOESN'T\nTRUST WHAT\nYOU SAY", 120, INK)
    put(img, lay, t, 0, dur=0.2, start=2.0, cy=300)
    bubble(d, 140, 760, 800, "We're the #1 tool!", "#ffffff", BG, 64)
    if t >= 0.9:
        e = ease((t - 0.9) / 0.25)
        d.line((140, 760, 140 + 800 * e, 760 + 200 * e), fill=RED, width=22)
    return shake(img, t, 0.9, 24)

def s_others(t):
    img = Image.new("RGBA", (W, H), BG); d = ImageDraw.Draw(img)
    text(d, 110, "IT TRUSTS\nOTHERS", 130, ACC)
    for k, q in enumerate(QUOTES):
        tk = LINE[1] + 0.3 + k * 0.3
        if t < tk: continue
        lay, dl = layer(); bubble(dl, 80 + (k % 2) * 120, 450 + k * 160, 860, "★★★★★  " + q, "#ffffff", BG, 40)
        put(img, lay, t, tk, dur=0.15, start=1.4, cy=500 + k * 160)
    return img

def s_data(t):
    img = Image.new("RGBA", (W, H), BG); d = ImageDraw.Draw(img)
    for k, (f, label, v, who, w) in enumerate((("g2.png", "Review sites", 15.5, "of ChatGPT answers", "fifteen"), ("reddit.png", "Reddit", 11, "of all AI answers", "eleven"))):
        y, tk = 220 + k * 520, at(w) - 0.2
        logo(img, L / f, 180, y + 60, 140)
        d.text((290, y + 60), label, font=font(76), fill=INK, anchor="lm")
        if t >= tk:
            p = ease((t - tk) / 0.5)
            d.text((W / 2, y + 290), f"{v * p:.1f}%".replace(".0%", "%") if p < 1 else f"{v:g}%", font=font(200), fill=ACC, anchor="mm")
            d.text((W / 2, y + 430), who, font=font(54, 700), fill=INK, anchor="ma")
    return img

def s_site(t):
    img = Image.new("RGBA", (W, H), BG); d = ImageDraw.Draw(img)
    k = 1 - 0.55 * ease((t - LINE[3] - 0.3) / 1.2)  # your site shrinks away
    w, h = 820 * k, 520 * k; x, y = W / 2 - w / 2, 560 - h / 2
    d.rounded_rectangle((x, y, x + w, y + h), 30, fill="#ffffff")
    d.rectangle((x, y, x + w, y + 70 * k), fill="#e9e3ff")
    d.text((W / 2, y + h / 2), "yoursite.com", font=font(max(30, int(80 * k)), 700), fill=BG, anchor="mm")
    if t >= at("Rarely") - 0.1:
        lay, dl = layer(); text(dl, 940, "RARELY\nTHE SOURCE", 120, ACC)
        put(img, lay, t, at("Rarely") - 0.1, dur=0.15, start=1.8, cy=1040)
    return shake(img, t, at("Rarely") - 0.1, 18)

s_cta = lambda t: cta(t, "WHO DOES AI\nTRUST IN\nYOUR NICHE?", "Review Radar · Reddit Radar")
SCENES = [(0, LINE[1], s_hook), (LINE[1], LINE[2], s_others), (LINE[2], LINE[3], s_data), (LINE[3], LINE[4], s_site),
          (LINE[4], VO_END + 0.2, s_cta), (VO_END + 0.2, LENGTH, s_end_factory("See who AI trusts in your niche"))]

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
