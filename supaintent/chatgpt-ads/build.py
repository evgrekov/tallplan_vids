# /// script
# dependencies = ["pillow"]
# ///
"""Free local edit for "Ads are already in ChatGPT": every frame is drawn with Pillow and piped to ffmpeg,
music is ducked under out/voice.wav, captions.py burns the captions, the result is slowed 10% (same pitch).
Ad cards are real mobile screenshots of SupaIntent's ChatGPT Ads Library, Nov 4, 2026.
Usage: uv run build.py  →  out/final.mp4
"""
import json, math, pathlib, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).parent
OUT, SS, L = ROOT / "out", ROOT / "screenshots", ROOT / "logos"
W, H, FPS = 1080, 1920, 30
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

def logo(img, path, cx, cy, size, disc=False):
    if disc:  # white disc so a dark logo stays visible on dark backgrounds
        r = size * 0.62
        ImageDraw.Draw(img).ellipse((cx - r, cy - r, cx + r, cy + r), fill=WHITE)
    l = Image.open(path).convert("RGBA")
    l.thumbnail((size, size), Image.LANCZOS) if max(l.size) > size else (l := l.resize((size, round(size * l.height / l.width)), Image.LANCZOS))
    img.paste(l, (int(cx - l.width / 2), int(cy - l.height / 2)), l)

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

def pill(lay_d, y, s, size, fill=YELLOW):
    """Title on a dark pill so it reads over any screenshot."""
    f = font(size)
    w = f.getlength(s)
    lay_d.rounded_rectangle((W / 2 - w / 2 - 40, y - 24, W / 2 + w / 2 + 40, y + size * 1.15 + 6), 30, fill=NAVY + "ee")
    lay_d.text((W / 2, y), s, font=f, fill=fill, anchor="ma")

def titled(s, size=78, fill=YELLOW, y=130):
    lay = Image.new("RGBA", (W, H)); pill(ImageDraw.Draw(lay), y, s, size, fill); return lay

# ---------- helpers ----------
def L_text(lines, y, size, fill=WHITE):
    lay = Image.new("RGBA", (W, H)); text(ImageDraw.Draw(lay), y, lines, size, fill); return lay

def chip(d, cx, cy, s, fill=BLUE, w=420, strike=False, ink=WHITE):
    d.rounded_rectangle((cx - w / 2, cy - 52, cx + w / 2, cy + 52), 52, fill=fill)
    d.text((cx, cy), s, font=font(52), fill=ink, anchor="mm")
    if strike: d.line((cx - w / 2 + 40, cy, cx + w / 2 - 40, cy), fill=WHITE, width=8)

def lerp(a, b, k): return a + (b - a) * k

# ---------- timing from the voice ----------
SHOTS = json.loads((OUT / "shots.json").read_text())
WORDS = json.loads((OUT / "words.json").read_text())
VO_END = SHOTS[-1]["end"]
LENGTH = math.ceil(VO_END + 3)
LINE = [s["start"] for s in SHOTS] + [VO_END]

def at(word, n=0):
    """Start of the n-th spoken occurrence of a word."""
    return [x["s"] for x in WORDS if x["w"].strip(".,?!'").lower() == word.lower()][n]

def disc_logo(img, f, cx, cy, size):
    logo(img, L / f, cx, cy, size, disc=True)

def bar(img, y, f, label, val, vmax, t, t0, col):
    """Engine logo + bar growing to val% from t0."""
    d = ImageDraw.Draw(img)
    disc_logo(img, f, 150, y, 90)
    w = 640 * val / vmax * ease((t - t0) / 0.5) if t >= t0 else 0
    d.rounded_rectangle((240, y - 45, 240 + max(w, 12), y + 45), 22, fill=col)
    if t >= t0: d.text((260 + max(w, 12), y), f"{val}%".replace(".0%", "%"), font=font(64), fill=WHITE, anchor="lm")
    d.text((240, y - 60), label, font=font(36, 700), fill="#b9c8ff", anchor="ls")

def endcard(line="Track every AI engine"):
    img, d = canvas("#ffffff")
    logo(img, L / "supaintent-logo-512.png", W // 2, 420, 300)
    d.text((W / 2, 620), "SupaIntent", font=font(130), fill=BLUE, anchor="ma")
    d.text((W / 2, 820), line, font=font(64, 700), fill=NAVY, anchor="ma")
    d.text((W / 2, 924), "supaintent.com", font=font(52, 700), fill=BLUE, anchor="ma")
    return img.convert("RGBA")

def s_end_factory(line):
    end, t0 = endcard(line), VO_END + 0.2
    def s(t):
        k = 1 + 0.06 * (t - t0) / (LENGTH - t0)
        z = end.resize((round(W * k), round(H * k))); x, y = (z.width - W) // 2, (z.height - H) // 2
        return z.crop((x, y, x + W, y + H))
    return s

def cta(t, t0, big):
    img = Image.new("RGBA", (W, H), NAVY); d = ImageDraw.Draw(img)
    put(img, L_text(big, 260, 100, YELLOW), t, t0, dur=0.15, start=1.8, cy=400)
    tl = at("SupaIntent", -1) - 0.3
    if t >= tl:
        lay = Image.new("RGBA", (W, H)); logo(lay, L / "supaintent-logo-512.png", W / 2, 900, 220)
        ImageDraw.Draw(lay).text((W / 2, 1040), "SupaIntent", font=font(90), fill=WHITE, anchor="ma")
        put(img, lay, t, tl, cy=950)
    return shake(img, t, t0, 18)

# ---------- scenes ----------
def card(i, wdt=980):
    c = Image.open(SS / f"ad{i}.png").convert("RGBA")
    c = c.resize((wdt, round(c.height * wdt / c.width)), Image.LANCZOS)
    m = Image.new("L", c.size); ImageDraw.Draw(m).rounded_rectangle((0, 0, c.width - 1, c.height - 1), 36, fill=255)
    out = Image.new("RGBA", c.size); out.paste(c, (0, 0), m); return out

CARDS = {i: card(i) for i in (1, 2, 3)}

def show(img, i, t, t0, y=200):
    if t < t0: return
    lay = Image.new("RGBA", (W, H)); lay.alpha_composite(CARDS[i], ((W - CARDS[i].width) // 2, y))
    put(img, lay, t, t0, dur=0.2, start=1.3, cy=y + 400)

def s_hook(t):
    img = Image.new("RGBA", (W, H), NAVY); d = ImageDraw.Draw(img)
    text(d, 110, "ADS ARE ALREADY", 88, WHITE)
    text(d, 240, "IN CHATGPT", 150, YELLOW)
    lay = Image.new("RGBA", (W, H)); disc_logo(lay, "chatgpt.png", W / 2, 720, 260)
    put(img, lay, t, 0, dur=0.2, start=2.2, cy=720)
    if t >= 0.6:  # "Sponsored" stamp slams over the logo
        st = Image.new("RGBA", (W, H)); ds = ImageDraw.Draw(st)
        ds.rounded_rectangle((W / 2 - 300, 900, W / 2 + 300, 1040), 30, fill=RED)
        ds.text((W / 2, 970), "SPONSORED", font=font(90), fill=WHITE, anchor="mm")
        put(img, st.rotate(-6, center=(W / 2, 970)), t, 0.6, dur=0.15, start=2.5, cy=970)
    return shake(img, t, 0.6, 30, 0.35)

def s_count(t):
    img = Image.new("RGBA", (W, H), BLUE); d = ImageDraw.Draw(img)
    pill(d, 150, "Ads logged in ChatGPT", 72)
    n = round(3920 * ease((t - LINE[1]) / 1.8))
    d.text((W / 2, 600), f"{n:,}", font=font(250), fill=YELLOW, anchor="mm")
    d.text((W / 2, 780), "ad creatives", font=font(80), fill=WHITE, anchor="ma")
    if t >= LINE[1] + 1.8: d.text((W / 2, 920), "9,368 appearances", font=font(60, 700), fill="#b9c8ff", anchor="ma")
    return shake(img, t, LINE[1] + 1.8, 20)

def s_ads(t):
    img = Image.new("RGBA", (W, H), "#eef2fb"); d = ImageDraw.Draw(img)
    t2 = at("StackAdapt") - 0.2
    show(img, 1 if t < t2 else 2, t, LINE[2] if t < t2 else t2)
    if t >= at("inside", -1) - 0.1:  # payoff: an ad for ChatGPT ads, shown inside ChatGPT
        put(img, titled("ChatGPT ads... in ChatGPT", 70, y=1140), t, at("inside", -1) - 0.1, dur=0.15, start=1.8, cy=1180)
    return shake(img, t, t2, 18)

def s_cc(t):
    img = Image.new("RGBA", (W, H), "#eef2fb"); d = ImageDraw.Draw(img)
    show(img, 3, t, LINE[3])
    t1 = at("twelve") - 0.1
    if t >= t1: put(img, titled("from $12/mo", 90, y=1140), t, t1, dur=0.15, start=1.8, cy=1180)
    return shake(img, t, t1, 16)

s_cta = lambda t: cta(t, LINE[4], "WHO ADVERTISES\nNEXT TO YOU?")
SCENES = [(0, LINE[1], s_hook), (LINE[1], LINE[2], s_count), (LINE[2], LINE[3], s_ads), (LINE[3], LINE[4], s_cc),
          (LINE[4], VO_END + 0.2, s_cta), (VO_END + 0.2, LENGTH, s_end_factory("Free ChatGPT Ads Library"))]
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
