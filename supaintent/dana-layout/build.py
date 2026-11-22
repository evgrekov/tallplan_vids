# /// script
# dependencies = ["pillow"]
# ///
"""Layout episode "Which AI?": code-drawn CEO and marketing lead on one stage (people.py) under changing data panels.
Numbers: SupaIntent AI prompt tracking study (2026): ChatGPT, Gemini and Google AI Mode name the same first brand for 36% of prompts.
Usage: uv run build.py  →  out/final.mp4
"""
import json, math, pathlib, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).parent
OUT, L = ROOT / "out", ROOT / "logos"
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

def fit_b(s, size, weight=820, maxw=W - 100):
    f = bfont(size, weight)
    return f if f.getlength(s) <= maxw else bfont(int(size * maxw / f.getlength(s)), weight)

def btext(d, y, s, size, fill):
    d.text((W / 2, y), s, font=fit_b(s, size), fill=fill, anchor="ma")

# ---------- stage: two actors at the bottom, data panels on top ----------
from people import CEO, CMO, Actor, smooth

FLOOR = 1860
GRID = Image.new("RGBA", (W, H), BG); _g = ImageDraw.Draw(GRID)
for x in range(30, W, 60):
    for y in range(30, H, 60): _g.ellipse((x - 2, y - 2, x + 2, y + 2), fill="#dde2ec")
ENG = (("chatgpt", "ChatGPT"), ("gemini", "Gemini"), ("google-ai-mode", "AI Mode"))
QUOTE = (at("are"), at("AI") + 0.4)  # CEO's question inside the narrator's line: her mouth stays shut
TALK = [(LINE[0], QUOTE[0])] + [(a["start"], a["end"]) for a in SHOTS[1:]]

ceo = Actor(CEO, [(0, {"prop": "phone", "ra": (12, 130), "brows": -1, "look": 1}),
                  (at("which"), {"brows": 1, "look": 1}),
                  (at("ChatGPT"), {"look": 0.4, "tilt": -2, "brows": 0}),
                  (LINE[3], {"prop": None, "ra": (150, 115), "brows": 1.3, "look": 0}),
                  (LINE[4], {"ra": (8, 6), "brows": 0, "look": 1, "tilt": 2})],
            [(0, -260), (0.05, 290)], height=620, seed=1.3)
cmo = Actor(CMO, [(0, {"look": -1, "la": (10, 25), "ra": (10, 25)}),
                  (at("which") - 0.2, {"la": (22, 55), "ra": (22, 55), "brows": 1, "tilt": -2}),
                  (at("ChatGPT"), {"la": (150, 10), "ra": (8, 6), "brows": 0, "tilt": 0}),
                  (at("thirty"), {"la": (8, 6), "brows": 1}),
                  (LINE[3], {"la": (40, 60), "ra": (40, 60), "brows": -0.6}),
                  (LINE[4], {"la": (140, 15), "ra": (8, 6), "brows": 0.6, "look": -0.5})],
            [(0, 800)], height=620, talk=TALK)

def crown(d, cx, cy, s, fill="#f5b301"):
    d.polygon([(cx - s, cy + s * 0.6), (cx - s, cy - s * 0.4), (cx - s * 0.5, cy + s * 0.05), (cx, cy - s * 0.7),
               (cx + s * 0.5, cy + s * 0.05), (cx + s, cy - s * 0.4), (cx + s, cy + s * 0.6)], fill=fill)

def chip(d, cx, cy, s, size, bg, fg="#ffffff"):
    f = bfont(size, 800); w = f.getlength(s) / 2 + size * 0.7
    d.rounded_rectangle((cx - w, cy - size * 0.85, cx + w, cy + size * 0.85), size * 0.5, fill=bg)
    d.text((cx, cy), s, font=f, fill=fg, anchor="mm")

def card(img, d, x, y, w, h, eng):
    d.rounded_rectangle((x + 6, y + 10, x + w + 6, y + h + 10), 32, fill="#d5dbe8")
    d.rounded_rectangle((x, y, x + w, y + h), 32, fill="#ffffff")
    logo(img, L / f"{eng}.png", x + w / 2, y + 80, 92)

def bubble(img, t, t0, t1, s, x, y, tail):
    if not t0 <= t < t1: return
    lay, d = layer(); f = bfont(56, 800); w = f.getlength(s)
    d.rounded_rectangle((x - w / 2 - 40, y - 52, x + w / 2 + 40, y + 52), 52, fill=INK)
    d.polygon([(tail - 22, y + 40), (tail + 22, y + 40), (tail + 4, y + 100)], fill=INK)
    d.text((x, y), s, font=f, fill="#ffffff", anchor="mm")
    put(img, lay, t, t0, dur=0.16, start=0.5, cx=tail, cy=y + 90)

def p_question(img, t):
    lay, d = layer(); btext(d, 210, "ARE WE #1", 170, INK); btext(d, 390, "IN AI?", 170, ACC)
    put(img, lay, t, 0, dur=0.3, start=1.12, cy=350)
    if t >= at("CEO"):
        lay, d = layer(); btext(d, 610, "the CEO asked", 56, GREY); put(img, lay, t, at("CEO"), dur=0.15, start=0.6, cy=640)
    return shake(img, t, QUOTE[0], 18)

def p_which(img, t):
    lay, d = layer(); btext(d, 200, "WHICH AI?", 170, INK); put(img, lay, t, LINE[1], dur=0.18, start=1.8, cy=290)
    for k, (eng, name) in enumerate(ENG):
        tk = at("which") + 0.12 * k
        if t < tk: continue
        lay, d = layer(); cx = 220 + k * 320
        d.ellipse((cx - 110, 470, cx + 110, 690), fill="#ffffff"); logo(lay, L / f"{eng}.png", cx, 580, 120)
        d.text((cx, 760), name, font=bfont(48, 760), fill=INK, anchor="mm")
        put(img, lay, t, tk, dur=0.18, start=0.3, cx=cx, cy=580)
    return img

BRANDS = (("Brand A", ACC), ("Brand C", "#7c3aed"), ("Brand B", "#0f766e"))

def p_agree(img, t):
    d = ImageDraw.Draw(img); btext(d, 120, "WHO IS #1?", 96, INK)
    for k, (eng, name) in enumerate(ENG):
        tk = at(("ChatGPT", "Gemini", "Google")[k]) - 0.1
        if t < tk: continue
        lay, dl = layer(); x = 60 + k * 330
        card(lay, dl, x, 260, 300, 330, eng)
        if t >= at("top") + 0.1 * k:
            b, c = BRANDS[k]; crown(dl, x + 150, 410, 30); chip(dl, x + 150, 500, b, 44, c)
        put(img, lay, t, tk, dur=0.2, start=0.4, cx=x + 150, cy=420)
    if t >= at("thirty"):
        lay, dl = layer(); n = round(36 * smooth((t - at("thirty")) / 0.8))
        btext(dl, 630, f"{n}%", 210, ACC); btext(dl, 860, "of prompts get the same #1", 52, INK)
        btext(dl, 925, "in all three engines", 52, INK)
        put(img, lay, t, at("thirty"), dur=0.2, start=1.6, cy=760)
    return img

ROWS = ((("Brand A",) * 3, None), (("Brand A", "Brand C", "Brand A"), 1), (("Brand B", "Brand B", "Brand A"), 2))  # (#1 per engine, the odd one)

def p_others(img, t):
    lay, d = layer(); btext(d, 110, "2 OUT OF 3 PROMPTS", 104, RED); btext(d, 240, "at least one AI crowns someone else", 50, INK)
    put(img, lay, t, LINE[3], dur=0.18, start=1.8, cy=200)
    tc = at("crowns")
    for r, (row, odd_k) in enumerate(ROWS):
        tr = at("two") + 0.25 * r
        if t < tr: continue
        lay, d = layer(); y = 360 + r * 200
        d.rounded_rectangle((60, y, W - 60, y + 160), 36, fill="#ffffff")
        for k, (eng, _) in enumerate(ENG):
            cx = 230 + k * 310; b = row[k]; odd = k == odd_k
            logo(lay, L / f"{eng}.png", cx - 95, y + 80, 56)
            chip(d, cx + 45, y + 80, b, 36, RED if odd and t >= tc else "#101828")
            if odd and t >= tc: crown(d, cx + 45, y + 22 - 40 * (1 - smooth((t - tc) / 0.25)), 22, RED)
        put(img, lay, t, tr, dur=0.16, start=0.6, cy=y + 80)
    return shake(img, t, tc, 14)

def p_cta(img, t):
    lay, d = layer(); btext(d, 130, "DON'T CHECK", 140, INK); btext(d, 280, "ONE AI.", 140, RED)
    put(img, lay, t, LINE[4], dur=0.18, start=1.8, cy=270)
    tl = at("Track") - 0.1
    if t >= tl:
        lay, d = layer(); pw = lockup_w(72) / 2 + 60
        d.rounded_rectangle((W / 2 - pw, 480, W / 2 + pw, 640), 44, fill="#ffffff")
        lockup(lay, W / 2, 560, 72)
        for k, (eng, _) in enumerate(ENG):
            cx = W / 2 + (k - 1) * 170; d.ellipse((cx - 62, 700, cx + 62, 824), fill="#ffffff"); logo(lay, L / f"{eng}.png", cx, 762, 80)
        btext(d, 880, "+ Perplexity, tracked daily", 50, GREY)
        put(img, lay, t, tl, dur=0.2, start=0.6, cy=640)
    return img

PANELS = ((LINE[1], p_question), (LINE[2], p_which), (LINE[3], p_agree), (LINE[4], p_others), (99, p_cta))

def stage(t):
    img = GRID.copy()
    img = next(f for end, f in PANELS if t < end)(img, t)
    ceo.draw(img, t, FLOOR); cmo.draw(img, t, FLOOR)
    bubble(img, t, at("which") - 0.15, LINE[2], "Which AI?", 640, 1215, 740)
    return img

SCENES = [(0, VO_END + 0.2, stage), (VO_END + 0.2, LENGTH, s_end_factory("See who AI puts first in your niche."))]

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
subprocess.run(["uv", "run", "-q", ROOT / "captions.py", edit, OUT / "words.json", OUT / "final.mp4"], check=True)
print(f"🏁 {OUT / 'final.mp4'}")
