# /// script
# dependencies = ["pillow"]
# ///
"""Free local edit for "Same question, different answer": every frame is drawn with Pillow and piped to ffmpeg,
music is ducked under out/voice.wav, captions.py burns the captions, the result is slowed 10% (same pitch).
Word onsets come from a timestamped transcription of out/voice.wav, snapped to its pauses.
Usage: uv run build.py  →  out/final.mp4
"""
import json, math, pathlib, random, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).parent
OUT, SS, L = ROOT / "out", ROOT / "screenshots", ROOT / "logos"
W, H, FPS, LENGTH = 1080, 1920, 30, 21
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

GPT = Image.open(L / "chatgpt.png").convert("RGBA").resize((110, 110))

def gpt_disc(img, cx, cy):
    ImageDraw.Draw(img).ellipse((cx - 80, cy - 80, cx + 80, cy + 80), fill=WHITE)
    img.alpha_composite(GPT, (round(cx - 55), round(cy - 55)))

# ---------- scenes ----------
# 1. Hook: "Think ChatGPT gives the same answer every day?" → the screen shatters on "You're wrong"
WRONG_AT, HOOK_END = 2.66, json.loads((OUT / "shots.json").read_text())[1]["start"]
SHIFT = 3.52 - HOOK_END  # scenes below were timed for a hook that ended at 3.52

def hook_frame(t):
    img = Image.new("RGBA", (W, H), NAVY); d = ImageDraw.Draw(img)
    pill(d, 130, "ChatGPT gives the", 80, WHITE)  # whole question readable on frame 0
    text(d, 280, "SAME\nANSWER", 190, YELLOW)
    pill(d, 750, "every day?", 80, WHITE)
    k = 1 + 0.6 * (1 - ease(t / 0.35)) + 0.04 * math.sin(t * 9)  # punch-in, then a pulse
    put(img, BIG_GPT, 2, 1, start=k, cy=HIT[1])
    g = ease((t - 1.3) / (WRONG_AT - 1.3))  # cracks spread from the logo before the hit
    for crack in CRACKS:
        n = max(1, round(len(crack) * g))
        if g > 0: d.line(crack[:n + 1], fill=WHITE, width=7, joint="curve")
    return img

HIT = (W / 2, 1080)
BIG_GPT = Image.new("RGBA", (W, H))
ImageDraw.Draw(BIG_GPT).ellipse((HIT[0] - 165, HIT[1] - 165, HIT[0] + 165, HIT[1] + 165), fill=WHITE)
BIG_GPT.alpha_composite(Image.open(L / "chatgpt.png").convert("RGBA").resize((230, 230)), (round(HIT[0] - 115), round(HIT[1] - 115)))

def make_cracks(n=9, seed=5):
    rnd, out = random.Random(seed), []
    for i in range(n):
        a, (x, y), line = i / n * 2 * math.pi + rnd.uniform(-0.3, 0.3), HIT, [HIT]
        for _ in range(8):
            a += rnd.uniform(-0.5, 0.5); r = rnd.uniform(90, 180)
            x, y = x + r * math.cos(a), y + r * math.sin(a); line.append((x, y))
        out.append(line)
    return out

CRACKS = make_cracks()

def make_shards(img, hit=HIT, cols=7, rows=12, seed=3):
    """Cut the frame into jittered triangles; each flies away from the hit point."""
    rnd = random.Random(seed)
    pts = [[(x * W / cols + (rnd.uniform(-40, 40) if 0 < x < cols else 0), y * H / rows + (rnd.uniform(-40, 40) if 0 < y < rows else 0))
            for x in range(cols + 1)] for y in range(rows + 1)]
    shards = []
    for y in range(rows):
        for x in range(cols):
            a, b, c, e = pts[y][x], pts[y][x + 1], pts[y + 1][x + 1], pts[y + 1][x]
            for tri in ((a, b, c), (a, c, e)):
                xs, ys = [p[0] for p in tri], [p[1] for p in tri]
                box = tuple(map(round, (min(xs), min(ys), max(xs), max(ys))))
                mask = Image.new("L", (box[2] - box[0] + 1, box[3] - box[1] + 1))
                ImageDraw.Draw(mask).polygon([(px - box[0], py - box[1]) for px, py in tri], fill=255)
                piece = img.crop((box[0], box[1], box[0] + mask.width, box[1] + mask.height)); piece.putalpha(mask)
                cx, cy = sum(xs) / 3, sum(ys) / 3
                dx, dy = cx - hit[0], cy - hit[1]; n = math.hypot(dx, dy) + 1
                v = rnd.uniform(1800, 3200)
                shards.append((piece, box[0], box[1], dx / n * v, dy / n * v + rnd.uniform(-300, 300), rnd.uniform(-400, 400)))
    return shards

SHARDS = make_shards(hook_frame(WRONG_AT))

def s_hook(t):
    if t < WRONG_AT: return hook_frame(t)
    img = Image.new("RGBA", (W, H), RED)
    put(img, L_WRONG, t, WRONG_AT, dur=0.15, start=2.2, cy=900)
    u = t - WRONG_AT
    for piece, x, y, vx, vy, spin in SHARDS:  # glass flies out with gravity
        px, py = x + vx * u, y + vy * u + 2500 * u * u
        if not (-piece.width < px < W and py < H): continue
        pr = piece.rotate(spin * u, expand=True)
        img.alpha_composite(pr, (round(px - (pr.width - piece.width) / 2), round(py - (pr.height - piece.height) / 2)))
    if u < 0.07: img = Image.new("RGBA", (W, H), WHITE)  # impact flash
    return shake(img, t, WRONG_AT, 40, 0.4)

# 2. Real ChatGPT answers, Nov 3 → Nov 4: HubSpot overtakes Attio, Salesforce disappears
NOV3 = ["Attio", "HubSpot", "Pipedrive", "Zoho", "Close", "Salesforce"]
NOV4 = ["HubSpot", "Attio", "Pipedrive", "Zoho", "Close"]

def s_rank(t):
    img = Image.new("RGBA", (W, H), BLUE); d = ImageDraw.Draw(img)
    gpt_disc(img, W / 2, 240)
    d.text((W / 2, 380), "NOV 3" if t < 5.04 else "NOV 4", font=font(84), fill=YELLOW, anchor="ma")
    k = ease((t - 5.3) / 0.45)  # HubSpot and Attio swap places on "HubSpot"
    for i, b in enumerate(NOV3):
        j = NOV4.index(b) if b in NOV4 else i
        cy = 560 + 125 * lerp(i, j, k)
        gone = b not in NOV4 and t >= 5.85
        fade = ease((t - 7.06) / 0.4) if gone else 0
        if fade >= 1: continue
        lay = Image.new("RGBA", (W, H)); ld = ImageDraw.Draw(lay)
        ld.text((W / 2 - 300, cy), f"{round(lerp(i, j, k)) + 1}", font=font(56), fill=WHITE, anchor="mm")
        top = lerp(i, j, k) < 0.5 and t >= 4.38
        chip(ld, W / 2 + 40, cy, b, RED if gone else (YELLOW if top else NAVY), 520, gone, NAVY if top else WHITE)
        img.alpha_composite(lay, (round(fade * 900), 0))
    if t >= 5.85: put(img, L_GONE_SF, t, 7.06, dur=0.15, start=1.6, cy=1560)
    return shake(img, t, 5.88 if t < 7.06 else 7.08, 20)

# 3. Our data: about a third of today's brands are gone tomorrow
GRID = ["Attio", "HubSpot", "Pipedrive", "Zoho", "Close", "Salesforce", "Freshsales", "Copper", "Folk"]
DROP = {"Zoho", "Freshsales", "Folk"}

def s_third(t):
    img = Image.new("RGBA", (W, H), NAVY); d = ImageDraw.Draw(img)
    pill(d, 150, "We track this daily", 76)
    for n, b in enumerate(GRID):
        cx, cy = W / 2 + (n % 3 - 1) * 330, 470 + (n // 3) * 150
        if t < 8.33 + n * 0.08: continue
        out = b in DROP and t >= 11.17
        chip(d, cx, cy, b, RED if out else BLUE, 300, out)
    if t >= 9.38: put(img, L_THIRD, t, 9.38, dur=0.15, start=1.8, cy=1000)
    if t >= 11.17: put(img, L_TOMORROW, t, 11.17, dur=0.12, start=1.6, cy=1560)
    return shake(img, t, 11.2, 22)

# 4. One check is noise: a week of daily checks lights up, then SupaIntent
def s_daily(t):
    img = Image.new("RGBA", (W, H), YELLOW); d = ImageDraw.Draw(img)
    if t < 14.76:
        text(d, 260, "1 CHECK =", 150, NAVY)
        if t >= 13.73: put(img, L_NOTHING, t, 13.73, dur=0.12, start=2, cy=520)
    else: text(d, 260, "TRACK IT\nDAILY", 150, NAVY)
    for n in range(7):  # one dot per day, filled on "daily"
        cx = W / 2 + (n - 3) * 135
        on = t >= 14.76 + n * 0.1
        d.ellipse((cx - 50, 820, cx + 50, 920), fill=BLUE if on else WHITE, outline=NAVY, width=6)
        if on: d.line((cx - 22, 872, cx - 5, 890, cx + 25, 852), fill=WHITE, width=10, joint="curve")
        d.text((cx, 950), "MTWTFSS"[n], font=font(40), fill=NAVY, anchor="ma")
    if t >= 16.2:
        lay = Image.new("RGBA", (W, H)); logo(lay, L / "supaintent-logo-512.png", W / 2, 1160, 200)
        put(img, lay, t, 16.2, cy=1160)
    return shake(img, t, 13.76, 22)

# 5. End card
def endcard():
    img, d = canvas("#ffffff")
    logo(img, L / "supaintent-logo-512.png", W // 2, 420, 300)
    d.text((W / 2, 620), "SupaIntent", font=font(130), fill=BLUE, anchor="ma")
    d.text((W / 2, 820), "Track your brand in AI answers", font=font(60, 700), fill=NAVY, anchor="ma")
    d.text((W / 2, 820 + 74 + 30), "supaintent.com", font=font(52, 700), fill=BLUE, anchor="ma")
    return img.convert("RGBA")

END = endcard()

def s_end(t):
    k = 1 + 0.06 * (t - 17.3) / (LENGTH - 17.3)
    s = END.resize((round(W * k), round(H * k)))
    x, y = (s.width - W) // 2, (s.height - H) // 2
    return s.crop((x, y, x + W, y + H))

L_WRONG = L_text("YOU'RE\nWRONG", 640, 230, WHITE)
L_GONE_SF = titled("Salesforce: gone", 90, "#ff5c7a", y=1520)
L_THIRD = L_text("~1/3", 880, 260, YELLOW)
L_TOMORROW = titled("gone by tomorrow", 96, y=1520)
L_NOTHING = L_text("NOTHING", 440, 170, RED)

SCENES = [(0, 3.52, s_hook), (3.52, 8.33, s_rank), (8.33, 12.86, s_third), (12.86, 17.3, s_daily), (17.3, LENGTH, s_end)]
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
for n in range(math.ceil(LENGTH - SHIFT) * FPS):
    t = n / FPS
    lt = t if t < HOOK_END else min(t + SHIFT, LENGTH - 0.01)
    frame = next(f for a, b, f in SCENES if a <= lt < b)(lt)
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
