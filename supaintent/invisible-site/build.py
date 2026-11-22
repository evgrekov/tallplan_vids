# /// script
# dependencies = ["pillow"]
# ///
"""Free local edit for "Your website is invisible to ChatGPT": every frame is drawn with Pillow and piped to ffmpeg,
music is ducked under out/voice.wav, captions.py burns the captions, the result is slowed 10% (same pitch).
Screenshots: ChatGPT (logged out) "best CRM for startups" and Top AI Citation Domains, Nov 2026.
Usage: uv run build.py  →  out/final.mp4
"""
import json, math, pathlib, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).parent
OUT, SS, L = ROOT / "out", ROOT / "screenshots", ROOT / "logos"
W, H, FPS = 1080, 1920, 30
BG, INK, ACC, GREY, LEAD = "#f4f1ea", "#111111", "#ff3b30", "#8a8a8a", 1.08

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

# ---------- scenes: paper editorial, black ink, red marker ----------
CHAT, SRC, TOP = shot("chatgpt-best-crm-answer-mobile.jpg", (0, 120, 750, 1100), 820), shot("chatgpt-best-crm-sources-mobile.jpg", (0, 120, 750, 1100), 820), shot("top-domains-chatgpt-tab-mobile.jpg", (0, 200, 750, 1150), 820)

def s_hook(t):
    img = Image.new("RGBA", (W, H), BG); d = ImageDraw.Draw(img)
    text(d, 120, "YOUR WEBSITE IS", 92, INK)
    # browser card fades and glitches away: the site ChatGPT never reads
    a = 1 - ease((t - 0.8) / 1.6)
    lay, dl = layer()
    dl.rounded_rectangle((140, 430, 940, 1000), 30, fill="#ffffff", outline=INK, width=6)
    dl.rectangle((140, 430, 940, 500), fill=INK)
    for k in range(3): dl.ellipse((170 + k * 40, 452, 194 + k * 40, 476), fill=BG)
    dl.text((W / 2, 520), "yourbrand.com", font=font(54), fill=INK, anchor="ma")
    for k in range(5): dl.rounded_rectangle((200, 640 + k * 64, 880 - (k % 2) * 160, 670 + k * 64), 12, fill="#d9d4c7")
    lay.putalpha(lay.getchannel("A").point(lambda v: int(v * max(a, 0.12))))
    off = int(30 * math.sin(t * 50)) if 0.8 < t < 2.2 else 0
    img.alpha_composite(lay, (off, 0))
    lay, dl = layer(); text(dl, 230, "INVISIBLE", 170, ACC)
    put(img, lay, t, 0, dur=0.2, start=2.2, cy=320)
    tg = at("ChatGPT") - 0.1
    if t >= tg:
        lay, dl = layer(); logo(lay, L / "chatgpt.png", W / 2, 1120, 150, disc=True)
        dl.text((W / 2, 1210), "to ChatGPT", font=font(64), fill=INK, anchor="ma")
        put(img, lay, t, tg, cy=1120)
    return shake(img, t, 0.05, 28, 0.35)

def s_sources(t):
    img = Image.new("RGBA", (W, H), BG); d = ImageDraw.Draw(img)
    ts = at("sources") - 0.1
    if t < ts:
        place(img, CHAT, t, LINE[1], 120)
        box(d, 1520, "“Best CRM for startups?”", 64, BG, INK)
    else:
        place(img, SRC, t, ts, 120)
        if t >= at("list") - 0.1:
            lay, dl = layer()
            dl.rounded_rectangle((W / 2 - 400, 1500, W / 2 + 400, 1680), 30, fill=ACC)
            dl.text((W / 2, 1590), "0 VENDOR SITES", font=font(74), fill="#ffffff", anchor="mm")
            put(img, lay.rotate(-4, center=(W / 2, 1590)), t, at("list") - 0.1, dur=0.15, start=2, cy=1590)
    return shake(img, t, at("list") - 0.1, 18)

def s_g2(t):
    img = Image.new("RGBA", (W, H), BG); d = ImageDraw.Draw(img)
    place(img, TOP, t, LINE[2], 120)
    tg = at("G2") - 0.1
    if t >= tg:
        lay, dl = layer()
        dl.rounded_rectangle((90, 1480, 990, 1760), 36, fill=INK)
        logo(lay, L / "g2.png", 230, 1620, 150)
        dl.text((640, 1560), "≈ 1 in 4", font=font(110), fill=ACC, anchor="mm")
        dl.text((640, 1680), "ChatGPT answers", font=font(54), fill=BG, anchor="mm")
        put(img, lay, t, tg, cy=1620)
    return shake(img, t, tg, 16)

def s_todo(t):
    img = Image.new("RGBA", (W, H), BG); d = ImageDraw.Draw(img)
    text(d, 160, "THE FIX", 140, INK)
    for k, (label, w) in enumerate((("Reviews on G2", "reviews"), ("Get into the lists", "lists"))):
        y, tw = 520 + k * 240, at(w) - 0.1
        d.rounded_rectangle((120, y, 220, y + 100), 18, outline=INK, width=8)
        d.text((260, y + 50), label, font=font(72), fill=INK, anchor="lm")
        if t >= tw:  # red marker tick
            e = ease((t - tw) / 0.2)
            pts = [(135, y + 50), (165, y + 85), (165 + 60 * e, y + 85 - 85 * e)]
            d.line(pts, fill=ACC, width=18, joint="curve")
    return img

s_cta = lambda t: cta(t, "SEE WHAT\nCHATGPT READS", "free · Top AI Citation Domains")
SCENES = [(0, LINE[1], s_hook), (LINE[1], LINE[2], s_sources), (LINE[2], LINE[3], s_g2), (LINE[3], LINE[4], s_todo),
          (LINE[4], VO_END + 0.2, s_cta), (VO_END + 0.2, LENGTH, s_end_factory("See what ChatGPT reads"))]

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
