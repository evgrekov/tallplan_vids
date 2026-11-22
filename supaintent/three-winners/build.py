# /// script
# dependencies = ["pillow"]
# ///
"""Free local edit for "3 AIs, 3 winners": every frame is drawn with Pillow and piped to ffmpeg,
music is ducked under out/voice.wav, captions.py burns the captions, the result is slowed 10% (same pitch).
Leaders are real rank-1 brands from SupaIntent's sensor data (Oct 11 and Sep 27, 2026); word onsets are snapped to voice pauses.
Usage: uv run build.py  →  out/final.mp4
"""
import math, pathlib, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).parent
OUT, SS, L = ROOT / "out", ROOT / "screenshots", ROOT / "logos"
W, H, FPS, LENGTH = 1080, 1920, 30, 23
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

# ---------- engines and slot reels ----------
COLS = [W / 6 + 10, W / 2, 5 * W / 6 - 10]
ENGINES = [("chatgpt.png", "ChatGPT"), ("gemini.png", "Gemini"), ("google-ai-mode.png", "Google AI")]
POOL = ["Asana", "Monday", "ClickUp", "Jira", "Notion", "Trello", "Wrike", "Mailchimp", "Omnisend", "ActiveCampaign", "Klaviyo", "Brevo"]

def L_engines():
    lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay)
    for cx, (f, name) in zip(COLS, ENGINES):
        d.ellipse((cx - 105, 520 - 105, cx + 105, 520 + 105), fill=WHITE)
        logo(lay, L / f, cx, 520, 130)
        d.text((cx, 650), name, font=font(42), fill=WHITE, anchor="ma")
    return lay

ENGINE_LAYER = L_engines()

def reel(img, cx, cy, t, t_stop, final, spin_from=0):
    """Slot reel: names scroll fast until t_stop, then the winner pops in yellow."""
    w, h = 320, 150
    win = Image.new("RGBA", (w, h), NAVY); d = ImageDraw.Draw(win)
    if t < t_stop:
        off = (t - spin_from) * 14 + COLS.index(cx) * 2.3
        for k in range(-1, 2):
            name = POOL[int(off + k) % len(POOL)]
            d.text((w / 2, h / 2 + (k - off % 1) * 70), name, font=font(40), fill=GREY, anchor="mm")
    else:
        e = ease((t - t_stop) / 0.15)
        d.rounded_rectangle((8, 8, w - 8, h - 8), 26, fill=YELLOW)
        d.text((w / 2, h / 2 + (1 - e) * 40), final, font=font(44 if len(final) < 10 else 34), fill=NAVY, anchor="mm")
    mask = Image.new("L", (w, h)); ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), 26, fill=255)
    img.paste(win, (round(cx - w / 2), round(cy - h / 2)), mask)

# ---------- scenes ----------
# 1. Hook: "3 AIs. 3 WINNERS." on frame 0, logos slam in, reels spin and land on "?" at "winners"
def s_hook(t):
    img = Image.new("RGBA", (W, H), BLUE); d = ImageDraw.Draw(img)
    text(d, 70, "3 AIs.", 140, WHITE)
    text(d, 220, "3 WINNERS.", 120, YELLOW)
    put(img, ENGINE_LAYER, t, 0, dur=0.18, start=2.2, cy=560) if t < 0.2 else img.alpha_composite(ENGINE_LAYER, (0, 60))
    for cx in COLS: reel(img, cx, 860, t, 2.94, "?")
    if t >= 2.94: d.text((W / 2, 1010), "same question", font=font(54), fill=WHITE, anchor="ma")
    return shake(img, t, 2.94, 26) if t >= 2.94 else shake(img, t, 0.02, 30, 0.25)

# 2/3. Real rank-1 answers, reels stop on each brand as it is named
def s_topic(title, date, stops, t0):
    def scene(t):
        img = Image.new("RGBA", (W, H), BLUE); d = ImageDraw.Draw(img)
        put(img, titled(title, 70, y=150), t, t0, dur=0.15, start=1.6)
        img.alpha_composite(ENGINE_LAYER, (0, 40))
        for cx, (ts, brand) in zip(COLS, stops): reel(img, cx, 900, t, ts, brand, t0)
        d.text((W / 2, 1040), f"same prompt · {date}", font=font(40, 600), fill="#b9c8ff", anchor="ma")
        return shake(img, t, max([ts for ts, _ in stops if ts <= t], default=-9), 18, 0.25)
    return scene

s_pm = s_topic("Best PM tool?", "Oct 11, 2026", [(5.85, "Asana"), (7.15, "Monday"), (8.25, "ClickUp")], 3.82)
s_email = s_topic("Best email marketing?", "Sep 27, 2026", [(9.65, "Omnisend"), (10.2, "ActiveCampaign"), (10.9, "Mailchimp")], 8.75)

# 4. Our data: all three agree on #1 only about a third of the time
def s_third(t):
    img = Image.new("RGBA", (W, H), NAVY); d = ImageDraw.Draw(img)
    pill(d, 150, "All 3 AIs agree on #1:", 72)
    for n in range(9):  # one row per prompt: three engine dots, matching rows go green
        y, agree = 330 + n * 70, n in (1, 4, 7)
        if t < 12.9 + n * 0.12: continue
        for k, cx in enumerate((W / 2 - 90, W / 2, W / 2 + 90)):
            on = t >= 13.8
            col = ("#28c840" if agree else (YELLOW, "#7cc4ff", RED)[k]) if on else GREY
            d.ellipse((cx - 26, y - 26, cx + 26, y + 26), fill=col)
    if t >= 15.5: put(img, L_THIRD, t, 15.5, dur=0.15, start=1.8, cy=1000)
    return shake(img, t, 15.53, 22)

# 5. One AI is not enough → SupaIntent
def s_cta(t):
    img = Image.new("RGBA", (W, H), NAVY); d = ImageDraw.Draw(img)
    text(d, 200, "1 AI ISN'T\nENOUGH", 140, YELLOW)
    img.alpha_composite(ENGINE_LAYER, (0, 120))
    for k, cx in enumerate(COLS):  # every engine gets checked, one by one
        if t >= 18.69 + k * 0.15:
            d.ellipse((cx + 50, 540, cx + 130, 620), fill="#28c840")
            d.line((cx + 70, 582, cx + 85, 598, cx + 112, 562), fill=WHITE, width=10, joint="curve")
    if t >= 19.7:
        lay = Image.new("RGBA", (W, H)); logo(lay, L / "supaintent-logo-512.png", W / 2, 1050, 200)
        put(img, lay, t, 19.7, cy=1050)
    return shake(img, t, 18.72, 18)

def endcard():
    img, d = canvas("#ffffff")
    logo(img, L / "supaintent-logo-512.png", W // 2, 420, 300)
    d.text((W / 2, 620), "SupaIntent", font=font(130), fill=BLUE, anchor="ma")
    d.text((W / 2, 820), "Track every AI engine", font=font(64, 700), fill=NAVY, anchor="ma")
    d.text((W / 2, 820 + 74 + 30), "supaintent.com", font=font(52, 700), fill=BLUE, anchor="ma")
    return img.convert("RGBA")

END = endcard()

def s_end(t):
    k = 1 + 0.06 * (t - 20.2) / (LENGTH - 20.2)
    s = END.resize((round(W * k), round(H * k)))
    x, y = (s.width - W) // 2, (s.height - H) // 2
    return s.crop((x, y, x + W, y + H))

L_THIRD = L_text("only ~1/3", 960, 170, YELLOW)

SCENES = [(0, 3.82, s_hook), (3.82, 8.75, s_pm), (8.75, 12.9, s_email), (12.9, 16.69, s_third), (16.69, 20.2, s_cta), (20.2, LENGTH, s_end)]
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
