# /// script
# dependencies = ["pillow"]
# ///
"""Free local edit for "ChatGPT and Google read a different internet": every frame is drawn with Pillow and piped to ffmpeg,
music is ducked under out/voice.wav, captions.py burns the captions, the result is slowed 10% (same pitch).
Numbers from SupaIntent answer data, Aug-Oct 2026 (blog: ai-mode-tools).
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
def s_hook(t):
    img = Image.new("RGBA", (W, H), BLUE); d = ImageDraw.Draw(img)
    split = ease(t / 0.35) * 40  # the two halves drift apart: two internets
    d.rectangle((0, 0, W / 2 - split, H), fill=NAVY); d.rectangle((W / 2 + split, 0, W, H), fill="#123d9e")
    text(d, 120, "CHATGPT & GOOGLE", 84, WHITE)
    text(d, 250, "READ A DIFFERENT\nINTERNET", 88, YELLOW)
    lay = Image.new("RGBA", (W, H))
    disc_logo(lay, "chatgpt.png", W / 4, 760, 220); disc_logo(lay, "google-ai-mode.png", 3 * W / 4, 760, 220)
    put(img, lay, t, 0, dur=0.2, start=2.0, cy=760)
    d.text((W / 2, 760), "≠", font=font(200), fill=YELLOW, anchor="mm", stroke_width=6, stroke_fill=NAVY)
    return shake(img, t, 0.05, 30, 0.35)

def s_overlap(t):
    img = Image.new("RGBA", (W, H), NAVY); d = ImageDraw.Draw(img)
    pill(d, 140, "Same question, sources:", 70)
    gap = 300 - 90 * ease((t - LINE[1]) / 0.8)  # circles slide together but barely overlap
    for cx, f, col in ((W / 2 - gap, "chatgpt.png", "#10a37f"), (W / 2 + gap, "google-ai-mode.png", "#4285f4")):
        d.ellipse((cx - 260, 700 - 260, cx + 260, 700 + 260), outline=col, width=14)
        disc_logo(img, f, cx + (-120 if cx < W / 2 else 120), 700, 120)
    t1 = at("four") - 0.15
    if t >= t1:
        put(img, L_text("1 in 4", 600, 120, YELLOW), t, t1, dur=0.15, start=2, cy=660)
        d.text((W / 2, 1050), "only 26.5% overlap", font=font(64), fill=WHITE, anchor="ma")
    return shake(img, t, t1, 22)

def s_youtube(t):
    img = Image.new("RGBA", (W, H), BLUE); d = ImageDraw.Draw(img)
    logo(img, L / "youtube.png", W / 2, 260, 200)
    pill(d, 420, "cited by YouTube", 70)
    bar(img, 700, "google-ai-mode.png", "Google AI answers", 19.8, 20, t, LINE[2] + 0.4, RED)
    bar(img, 960, "chatgpt.png", "ChatGPT answers", 0.2, 20, t, at("ChatGPT", 1) - 0.1, GREY)
    return shake(img, t, at("ChatGPT", 1) - 0.1, 16)

def s_reddit(t):
    img = Image.new("RGBA", (W, H), BLUE); d = ImageDraw.Draw(img)
    g2 = t >= at("G2") - 0.3 if any(w["w"].strip(".,") == "G2" for w in WORDS) else t >= LINE[4] - 1.2
    logo(img, L / ("g2.png" if g2 else "reddit.png"), W / 2, 260, 200)
    if g2:
        bar(img, 700, "chatgpt.png", "ChatGPT answers", 9.5, 20, t, 0, "#10a37f")
        bar(img, 960, "google-ai-mode.png", "Google AI answers", 5.2, 20, t, 0, GREY)
        pill(d, 420, "ChatGPT trusts review sites", 62)
    else:
        bar(img, 700, "google-ai-mode.png", "Google AI answers", 18.3, 20, t, LINE[3] + 0.4, ORANGE)
        bar(img, 960, "chatgpt.png", "ChatGPT answers", 8.4, 20, t, at("eight") - 0.1, GREY)
    return img

s_cta = lambda t: cta(t, LINE[4], "1 STRATEGY\nWON'T WIN BOTH")
SCENES = [(0, LINE[1], s_hook), (LINE[1], LINE[2], s_overlap), (LINE[2], LINE[3], s_youtube), (LINE[3], LINE[4], s_reddit),
          (LINE[4], VO_END + 0.2, s_cta), (VO_END + 0.2, LENGTH, s_end_factory("See who each AI cites"))]
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
