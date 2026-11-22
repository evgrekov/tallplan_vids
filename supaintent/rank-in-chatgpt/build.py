# /// script
# dependencies = ["pillow"]
# ///
"""Free local edit: every frame is drawn with Pillow (pop-ins, counters, shakes, a keyframed camera that zooms into the
screenshots on the spoken word) and piped to ffmpeg; out/audio_mix.m4a goes under it, captions.py burns the captions.
Timings are word onsets measured from pauses in out/voice.wav (silencedetect). The result is slowed 10% (same pitch) into out/final.mp4.
Usage: uv run build.py  →  out/final.mp4
"""
import json, math, pathlib, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).parent
OUT, SS, L = ROOT / "out", ROOT / "screenshots", ROOT / "logos"
W, H, FPS, LENGTH = 1080, 1920, 30, 32
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

class Cam:
    """Keyframed camera over a screenshot: keys = [(t, x, y, view_width)] in screenshot px; moves ease in 0.35 s.
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

# ---------- layers ----------
def L_text(lines, y, size, fill=WHITE):
    lay = Image.new("RGBA", (W, H)); text(ImageDraw.Draw(lay), y, lines, size, fill); return lay

def L_logo(path, cx, cy, size, label):
    lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay)
    r = size * 0.72
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=WHITE)
    logo(lay, path, cx, cy, size)
    d.text((cx, cy + r + 30), label, font=font(54), fill=WHITE, anchor="ma")
    return lay

def boxes(rows, x0=16, x1=734, h=95):
    """[(t0, t1, y)] → Cam highlight boxes over full-width rows of a 750 px mobile screenshot."""
    return [(t0, t1, (x0, y - h, x1, y + h)) for t0, t1, y in rows]

# ---------- scenes (start, end, draw(t) → RGBA) ----------
# 0. Intro question (voice line 1, before everything else): words slam in, ChatGPT logo spins in, giant "3" on a sunburst
INTRO = json.loads((OUT / "shots.json").read_text())[1]["start"] - 0.2  # the rest of the timeline starts after the question
L_Q1, L_Q2, L_Q3 = L_text("HOW TO RANK", 230, 118, YELLOW), L_text("YOUR BRAND", 410, 118), L_text("IN", 640, 110)
GPT_BIG = Image.open(L / "chatgpt.png").convert("RGBA").resize((300, 300))
def L_badge():
    """Navy disc with a white 3 and a hard drop shadow."""
    lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay)
    d.ellipse((W / 2 - 290, 330 - 290 + 24, W / 2 + 290, 330 + 290 + 24), fill="#00000040")
    d.ellipse((W / 2 - 290, 330 - 290, W / 2 + 290, 330 + 290), fill=NAVY)
    d.text((W / 2 + 10, 330 + 14), "3", font=font(430, 800), fill=BLUE, anchor="mm")
    d.text((W / 2, 330), "3", font=font(430, 800), fill=WHITE, anchor="mm")
    return lay

L_THREE, L_STEPS = L_badge(), titled("CONCRETE STEPS", 96, y=760)

def s_intro(t):
    if t < 2.01:
        img = Image.new("RGBA", (W, H), NAVY)
        put(img, L_Q1, t, 0.15, dur=0.12, start=2.2, cy=300)
        put(img, L_Q2, t, 0.75, dur=0.12, start=2.2, cy=480)
        if t >= 1.2:
            put(img, L_Q3, t, 1.2, dur=0.1, start=1.8, cy=700)
            k = ease((t - 1.2) / 0.3)
            disc = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(disc)
            r = 230 * k
            d.ellipse((W / 2 - r, 1000 - r, W / 2 + r, 1000 + r), fill=WHITE)
            g = GPT_BIG.rotate(-360 * (1 - k), resample=Image.BICUBIC).resize((max(1, round(300 * k)),) * 2)
            disc.alpha_composite(g, (round(W / 2 - g.width / 2), round(1000 - g.height / 2)))
            img.alpha_composite(disc)
        return shake(img, t, max(x for x in (0.15, 0.75, 1.2) if x <= t) if t >= 0.15 else 9, 22, 0.2)
    img = Image.new("RGBA", (W, H), YELLOW); d = ImageDraw.Draw(img)
    a0 = (t - 2.01) * 40  # rotating sunburst behind the 3
    for i in range(16):
        a = math.radians(a0 + i * 22.5)
        d.polygon([(W / 2, 330), (W / 2 + 1600 * math.cos(a), 330 + 1600 * math.sin(a)),
                   (W / 2 + 1600 * math.cos(a + 0.2), 330 + 1600 * math.sin(a + 0.2))], fill="#ffe600")
    put(img, L_THREE, t, 2.39, dur=0.14, start=0.2, cy=330)
    put(img, L_STEPS, t, 2.71, dur=0.12, start=1.8, cy=820)
    return shake(img, t, 2.39 if t < 2.71 else 2.71, 30, 0.25)

# 1. Hook (animated): ChatGPT ignores your website, reads "best CRM" lists instead
def L_site(cx, cy, w, url, title, dim=False):
    """Generic browser card: url bar + headline lines."""
    lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay)
    h, x0, y0 = w * 0.62, cx - w / 2, cy - w * 0.31
    d.rounded_rectangle((x0, y0, x0 + w, y0 + h), 28, fill="#c9cfdb" if dim else WHITE)
    for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        d.ellipse((x0 + 26 + i * 34, y0 + 24, x0 + 48 + i * 34, y0 + 46), fill=GREY if dim else c)
    d.rounded_rectangle((x0 + 140, y0 + 18, x0 + w - 26, y0 + 54), 18, fill="#e8ecf3")
    d.text((x0 + 160, y0 + 36), url, font=font(round(w / 20), 600), fill=GREY, anchor="lm")
    d.text((x0 + 30, y0 + 90), title, font=font(round(w / 13)), fill=GREY if dim else NAVY)
    for i, k in enumerate((0.85, 0.7, 0.78)):
        d.rounded_rectangle((x0 + 30, y0 + 190 + i * 44, x0 + 30 + (w - 60) * k, y0 + 212 + i * 44), 11, fill="#dfe4ee")
    return lay

def L_icon(fn):
    lay = Image.new("RGBA", (W, H)); fn(lay, ImageDraw.Draw(lay)); return lay

SPOTS = [(W / 2 - 250, 1010), (W / 2 + 250, 1010), (W / 2, 1170)]
GPT_HOOK = L_logo(L / "chatgpt.png", W / 2, 660, 200, "")
SITE, SITE_DIM = L_site(W / 2, 1030, 620, "yourwebsite.com", "Your website"), L_site(W / 2, 1030, 620, "yourwebsite.com", "Your website", True)
LISTS = [L_site(cx, cy, 420, url, "Best CRM 2026") for (cx, cy), url in zip(SPOTS, ("techradar.com", "emergent.sh", "saaslete.com"))]
CROSS = L_icon(lambda i, d: (d.line((W / 2 - 260, 870, W / 2 + 260, 1190), fill=RED, width=34),
                             d.line((W / 2 + 260, 870, W / 2 - 260, 1190), fill=RED, width=34)))
L_HOOK_A, L_HOOK_B = L_text("ChatGPT isn't\nreading", 110, 120), L_text("your website", 390, 120, YELLOW)

def s_hook(t):
    img = Image.new("RGBA", (W, H), BLUE)
    put(img, L_HOOK_A, t, 0, dur=0.15, start=1.5)
    put(img, GPT_HOOK, t, 0.1, cy=660)
    if t < 1.75:
        put(img, SITE if t < 1.39 else SITE_DIM, t, 0.5, cy=1030, start=0.6)
        put(img, L_HOOK_B, t, 1.2, dur=0.15, start=1.6)
        put(img, CROSS, t, 1.39, dur=0.12, start=1.8, cy=1030)
        return shake(img, t, 1.42, 24)
    put(img, L_HOOK_B, t, 0)
    d = ImageDraw.Draw(img)
    for i, lay in enumerate(LISTS):  # the pages it does read: list cards fly in, beams from the logo
        t0 = 1.75 + i * 0.15
        if t < t0: continue
        cx, cy = SPOTS[i]
        d.line((W / 2, 800, cx, cy), fill=YELLOW, width=10)
        put(img, lay, t, t0, cx=cx, cy=cy, start=0.4)
    return img

# 2. 162,000 answers → Top Domains, ChatGPT tab: G2 → Trustpilot → Capterra → Reddit
R = {"g2": 955, "trustpilot": 1075, "capterra": 1195, "reddit": 1440}
cam_rank = Cam(SS / "top-domains-chatgpt-tab-mobile.jpg",
               [(4.87, 375, 500, 750), (5.2, 375, R["g2"], 750), (5.64, 375, R["trustpilot"], 750),
                (6.26, 375, R["capterra"], 750), (7.11, 375, R["reddit"], 750)], bg=WHITE,
               boxes=boxes([(5.2, 5.64, R["g2"] - 15), (5.64, 6.26, R["trustpilot"] - 15),
                            (6.26, 7.11, R["capterra"] - 15), (7.11, 9, R["reddit"] - 15)], h=60))
gpt = L_logo(L / "chatgpt.png", W / 2, 420, 200, "")

def counter(img, t, t0, t1, end, fmt, y, size, fill=YELLOW):
    text(ImageDraw.Draw(img), y, fmt(end * ease((t - t0) / (t1 - t0))), size, fill)

def s_data(t):
    if t < 4.87:  # word onsets from a timestamped transcription of this line
        img = Image.new("RGBA", (W, H), NAVY)
        put(img, gpt, t, 2.36)
        counter(img, t, 2.72, 3.9, 162000, lambda v: f"{round(v):,}", 760, 190)
        put(img, L_ANSWERS, t, 3.8)
        return shake(img, t, 3.9, 14)
    img = cam_rank(t)
    put(img, titled("What ChatGPT reads"), t, 4.87)
    return img

# 3. Step 1: real review-site logos, then Reddit
LOGOS = [(L_logo(L / "g2.png", W / 2 - 250, 600, 190, "G2"), 9.3), (L_logo(L / "capterra.png", W / 2 + 250, 600, 190, "Capterra"), 9.73),
         (L_logo(L / "reddit.png", W / 2, 980, 190, "Reddit threads"), 11.54)]

def s_step1(t):
    img = Image.new("RGBA", (W, H), BLUE)
    put(img, titled("1. Reviews + Reddit", 84, y=200), t, 7.75)
    for lay, t0 in LOGOS: put(img, lay, t, t0)
    return shake(img, t, 11.54, 16)

# 4. Step 2: the listicle ChatGPT cited, same brands as its answer
cam_title = Cam(SS / "listicle-emergent-title-mobile.jpg", [(12.43, 375, 500, 750), (13.17, 375, 420, 750)], bg=WHITE,
                boxes=[(13.17, 99, (24, 280, 726, 430))])
cam_list = Cam(SS / "listicle-emergent-list-mobile.jpg", [(14.73, 375, 640, 750)], bg=WHITE,
               boxes=[(t0, 99, (90, y0, 724, y1)) for t0, y0, y1 in  # Attio, Pipedrive, Zoho, Close: exact text blocks
                      ((14.73, 530, 635), (14.95, 340, 505), (15.17, 905, 1072), (15.39, 1095, 1202))])

def s_step2(t):
    img = cam_title(t) if t < 14.73 else cam_list(t)
    put(img, titled("2. Get on \"best X\" lists", 76), t, 12.43)
    if t >= 14.73: put(img, titled("Same brands ChatGPT picked", 60, "#7cf29c", y=1720), t, 14.73)
    return img

# 5. Step 3: your page answers in one sentence with a number (illustration of the advice, not a real site)
def L_page(hl_answer, hl_number):
    lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((70, 470, W - 70, 1330), 40, fill=WHITE)
    d.text((130, 540), "yourcrm.com/startups", font=font(40, 600), fill=GREY)
    d.multiline_text((130, 640), "What is the best CRM\nfor startups?", font=font(68, 800), fill=NAVY, spacing=14)
    y, f, fb = 880, font(48, 600), font(48, 900)
    if hl_answer: d.rounded_rectangle((105, y - 25, W - 105, y + 3 * 72 + 5), 22, fill="#fff9b0", outline=YELLOW, width=8)
    for line in (("YourCRM is free for teams up to", ""), ("", "10 users"), (" and sets up in ", "15 minutes.")):
        x = 130
        for i, part in enumerate(line):
            num = i == 1 and hl_number
            d.text((x, y), part, font=fb if num else f, fill=BLUE if num else NAVY); x += (fb if num else f).getlength(part)
        y += 72
    return lay

PAGES = [L_page(False, False), L_page(True, False), L_page(True, True)]

def s_step3(t):
    img = Image.new("RGBA", (W, H), BLUE)
    put(img, titled("3. One sentence + a number", 60, y=200), t, 15.88)
    put(img, PAGES[(t >= 16.62) + (t >= 18.79)], t, 15.95, start=1.15)
    if t >= 19.95: put(img, L_ARROW, t, 19.95, start=1.6)
    return shake(img, t, 19.95, 14)

# 6. Check daily: a third of today's brands are gone tomorrow (brand names as text, no logos drawn)
TODAY, GONE = ["Attio", "HubSpot", "Pipedrive", "Zoho", "Close", "Salesforce"], {"Zoho", "Close"}

def s_daily(t):
    img = Image.new("RGBA", (W, H), NAVY); d = ImageDraw.Draw(img)
    put(img, titled("Check every day", 84, y=170), t, 20.96)
    for col, (cx, head) in enumerate(((W / 4 + 20, "Today"), (3 * W / 4 - 20, "Tomorrow"))):
        if t < 20.96 + col * 0.7: continue
        d.text((cx, 400), head, font=font(64), fill=YELLOW, anchor="ma")
        for i, b in enumerate(TODAY):
            y = 500 + i * 112
            gone = col == 1 and b in GONE and t >= 22.71
            d.rounded_rectangle((cx - 210, y, cx + 210, y + 100), 50, fill=RED if gone else BLUE)
            d.text((cx, y + 50), b, font=font(50), fill=WHITE, anchor="mm")
            if gone: d.line((cx - 180, y + 50, cx + 180, y + 50), fill=WHITE, width=8)
    if t >= 22.71: put(img, L_GONE, t, 22.71, start=1.6)
    return shake(img, t, 22.75, 18)

# 7. End card (same as the YouTube video)
def endcard():
    img, d = canvas("#ffffff")
    logo(img, L / "supaintent-logo-512.png", W // 2, 420, 300)
    d.text((W / 2, 620), "SupaIntent", font=font(130), fill=BLUE, anchor="ma")
    d.text((W / 2, 820), "See who ChatGPT cites", font=font(64, 700), fill=NAVY, anchor="ma")
    d.text((W / 2, 820 + 74 + 30), "supaintent.com/tools/top-domains", font=font(46, 700), fill=BLUE, anchor="ma")
    return img.convert("RGBA")

END = endcard()

def s_end(t):
    k = 1 + 0.06 * (t - 23.8) / (LENGTH - 23.8)
    s = END.resize((round(W * k), round(H * k)))
    x, y = (s.width - W) // 2, (s.height - H) // 2
    return s.crop((x, y, x + W, y + H))

L_ANSWERS = L_text("AI answers\nchecked", 1000, 100)
L_ARROW = titled("ChatGPT quotes THIS", 76, y=1500)
L_GONE = titled("~1/3 gone overnight", 80, y=1500)

SCENES = [(0, 2.36, s_hook), (2.36, 7.75, s_data), (7.75, 12.43, s_step1), (12.43, 15.88, s_step2),
          (15.88, 20.96, s_step3), (20.96, 23.8, s_daily), (23.8, LENGTH, s_end)]

TOTAL = math.ceil(LENGTH + INTRO)

# ---------- audio mix: music ducked under the voice ----------
mix = OUT / "audio_mix.m4a"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", OUT / "voice.wav", "-stream_loop", "-1", "-i", OUT / "music.mp3", "-filter_complex",
                "[1:a]volume=0.35[m];[m][0:a]sidechaincompress=threshold=0.03:ratio=8:release=300[d];"
                "[0:a][d]amix=inputs=2:normalize=0,alimiter=limit=0.95,atrim=0:" + str(TOTAL), "-c:a", "aac", "-b:a", "192k", mix], check=True)

# ---------- render ----------
edit = OUT / "edit.mp4"
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                       "-i", "-", "-i", mix, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "18",
                       "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", edit], stdin=subprocess.PIPE)
for n in range(TOTAL * FPS):
    t = n / FPS
    if t < INTRO: frame = s_intro(t)
    else:
        lt = min(t - INTRO, LENGTH - 0.01)
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
