# /// script
# dependencies = ["pillow"]
# ///
"""Free local edit for "Same question, 10 weeks": every frame is drawn with Pillow and piped to ffmpeg,
music is ducked under out/voice.wav, captions.py burns the captions, the result is slowed 10% (same pitch).
Data: ChatGPT answers for "CRM Software", 10 weekly SupaIntent snapshots, Aug 23 - Oct 25, 2026.
Usage: uv run build.py  →  out/final.mp4
"""
import json, math, pathlib, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).parent
OUT, SS, L = ROOT / "out", ROOT / "screenshots", ROOT / "logos"
W, H, FPS = 1080, 1920, 30
BG, INK, ACC, GREY, LEAD = "#00000000", "#2b1a5a", "#7b2ff7", "#9a8fc0", 1.1

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

# ---------- scenes: pastel gradient, soft grotesk, calendar grid ----------
# ChatGPT, "CRM Software", 10 weekly snapshots Aug 23 - Oct 25, 2026: rank per week, None = not mentioned
DATA = [("Salesforce", [None, 1, 1, 1, 2, 1, 1, 1, 1, 1]), ("HubSpot", [None, None, 2, 2, 1, 2, 2, 2, 2, 2]),
        ("Close", [4, None, None, 5, 8, None, 8, 10, 9, 10]), ("Freshsales", [None, 8, None, 10, 7, None, 6, None, 7, 6]),
        ("ActiveCampaign", [5, None, 10, 6, None, None, None, 9, 8, None])]
assert [sum(r is not None for r in w) for _, w in DATA] == [9, 8, 7, 6, 5]

def grad():
    g = Image.new("RGBA", (1, 2)); g.putpixel((0, 0), (201, 184, 255, 255)); g.putpixel((0, 1), (255, 214, 232, 255))
    return g.resize((W, H), Image.BILINEAR)

GRAD = grad()

def bg(): return GRAD.copy()

def grid(img, t, rows, t_rows, x0=300, y0=380):
    d = ImageDraw.Draw(img)
    for c in range(10): d.text((x0 + c * 64 + 28, y0 - 60), f"W{c + 1}", font=font(26, 600), fill=INK, anchor="ma")
    for k, (name, weeks) in enumerate(DATA[:rows]):
        y = y0 + k * 150
        d.text((x0 - 24, y + 28), name, font=font(46 if len(name) < 11 else 34, 700), fill=INK, anchor="rm")
        for c, r in enumerate(weeks):
            if t < t_rows[k] + c * 0.06: continue
            cx = x0 + c * 64 + 28
            if r: d.ellipse((cx - 28, y, cx + 28, y + 56), fill=ACC)
            else: d.ellipse((cx - 26, y + 2, cx + 26, y + 54), outline="#ffffff", width=5)
        n = sum(r is not None for r in weeks)
        if t >= t_rows[k] + 0.7: d.text((x0 + 660, y + 28), f"{n}/10", font=font(48), fill=INK, anchor="lm")

def s_hook(t):
    img = bg(); d = ImageDraw.Draw(img)
    text(d, 120, "Same question.", 104, INK)
    lay, dl = layer(); text(dl, 260, "10 weeks.", 150, ACC)
    put(img, lay, t, 0, dur=0.2, start=2.2, cy=340)
    for c in range(10):  # calendar pages flip in one by one
        tc = 0.2 + c * 0.22
        if t < tc: continue
        x, y = 120 + (c % 5) * 175, 620 + (c // 5) * 260
        s = ease((t - tc) / 0.2)
        d.rounded_rectangle((x, y + 100 * (1 - s), x + 150, y + 210), 22, fill="#ffffff")
        d.rectangle((x, y + 100 * (1 - s), x + 150, y + 40 + 100 * (1 - s)), fill=ACC)
        d.text((x + 75, y + 130), str(c + 1), font=font(80), fill=INK, anchor="mm")
    logo(img, L / "chatgpt.png", W / 2, 1220, 110, disc=True)
    return img

def s_grid(t):
    img = bg(); d = ImageDraw.Draw(img)
    box(d, 130, "“Best CRM software?”", 64, "#ffffff", INK, r=40)
    cues = [at("Salesforce"), at("HubSpot"), at("Close"), at("Freshsales"), at("ActiveCampaign")]
    grid(img, t, sum(t >= c - 0.1 for c in cues), [c - 0.1 for c in cues])
    return img

def s_screenshot(t):
    img = bg(); d = ImageDraw.Draw(img)
    grid(img, t, 5, [0] * 5)
    tc = LINE[3] + 0.2
    lay, dl = layer()  # one week highlighted: what a single screenshot would show
    dl.rounded_rectangle((300 + 4 * 64 - 6, 300, 300 + 4 * 64 + 62, 1150), 20, outline=INK, width=8)
    put(img, lay, t, tc, cy=700)
    if t >= tc + 0.4: box(d, 1500, "1 screenshot = 1 week", 70, "#ffffff", INK, r=40)
    return img

s_cta = lambda t: cta(t, "Track it\nevery week", "ChatGPT · Gemini · Google", bg=None)
SCENES = [(0, LINE[1], s_hook), (LINE[1], LINE[3], s_grid), (LINE[3], LINE[4], s_screenshot),
          (LINE[4], VO_END + 0.2, lambda t: Image.alpha_composite(bg(), s_cta(t))), (VO_END + 0.2, LENGTH, s_end_factory("Track your brand every week"))]

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
