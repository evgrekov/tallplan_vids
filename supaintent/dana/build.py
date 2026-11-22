# /// script
# dependencies = ["pillow"]
# ///
"""Dana, Head of Growth: animated character clips (clips/*.mp4, Omni 1.2 360p + Real-ESRGAN) cut with real-screenshot inserts.
Every frame is drawn with Pillow and piped to ffmpeg, music is ducked under out/voice.wav, captions.py burns the captions.
Screenshots: Google (Nov 9, 2026) and ChatGPT for "best crm for small business"; Salesmate 0 of 201 CRM answers (SupaIntent DB).
Usage: uv run build.py  →  out/final.mp4
"""
import json, math, pathlib, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).parent
OUT, SS, L, CLIPS = ROOT / "out", ROOT / "screenshots", ROOT / "logos", ROOT / "clips"
W, H, FPS = 1080, 1920, 30
BG, INK, ACC, GREY, RED, LEAD = "#0b1220", "#ffffff", "#4d8dff", "#94a3b8", "#ff4d4d", 1.05

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

# ---------- scenes: Dana clips + dark navy inserts with real screenshots ----------
from camera import Shot, smooth
FONT = str(ROOT / "fonts/Brand.ttf")
ORG = Shot(SS / "google-organic.jpg", FONT, [(860, 285, 1240, 385)])
GPT = Shot(SS / "chatgpt-answer-crm.png", FONT)
BLUE, YEL = (77, 141, 255), (255, 204, 0)

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

def shade_top(img, h=760, a=200):
    """Dark gradient behind top text."""
    g = Image.linear_gradient("L").rotate(180).resize((W, h)).point(lambda v: v * a // 255)
    img.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, h), 8)] * 3, g)), (0, 0))

def btext(d, y, s, size, fill):
    d.text((W / 2, y), s, font=fit_b(s, size), fill=fill, anchor="ma")

def fit_b(s, size, weight=820, maxw=W - 100):
    f = bfont(size, weight)
    return f if f.getlength(s) <= maxw else bfont(int(size * maxw / f.getlength(s)), weight)

def clip_scene(name, i, over=None):
    c = Clip(name, LINE[i], LINE[i + 1])
    def s(t):
        img = c.frame()
        if over: over(img, t)
        return img
    return s

def hook(img, t):
    shade_top(img)
    lay, dl = layer(); btext(dl, 150, "RANK #1 ON GOOGLE.", 92, INK); btext(dl, 270, "LEADS −30%.", 170, RED)
    put(img, lay, t, 0, dur=0.2, start=1.8, cy=300)

def typing(img, t):
    shade_top(img, 520, 170)
    q = "best CRM for a small business"; t0 = at("best")
    n = max(0, min(len(q), int((t - t0) / 0.045)))
    d = ImageDraw.Draw(img); f = bfont(50, 600)
    d.rounded_rectangle((70, 180, W - 70, 300), 60, fill="#ffffff")
    logo(img, L / "chatgpt.png", 140, 240, 56)
    d.text((190, 240), (q[:n] if n else "Ask anything") + ("|" if int(t * 3) % 2 else ""), font=f, fill="#0b1220" if n else "#98a2b3", anchor="lm")

def thesis(img, t):
    shade_top(img, 640, 210)
    d = ImageDraw.Draw(img)
    if t >= at("Google", -1) - 0.1: btext(d, 160, "GOOGLE RANKS PAGES.", 84, GREY)
    if t >= at("AI", 0) - 0.1:
        lay, dl = layer(); btext(dl, 270, "AI RECOMMENDS BRANDS.", 96, ACC)
        put(img, lay, t, at("AI", 0) - 0.1, dur=0.15, start=1.6, cy=320)

def outro(img, t):
    tl = at("SupaIntent", -1) - 0.3
    if t < tl: return
    lay, dl = layer(); pw = lockup_w(72) / 2 + 60
    dl.rounded_rectangle((W / 2 - pw, 1060, W / 2 + pw, 1220), 44, fill="#ffffff")
    lockup(lay, W / 2, 1140, 72)
    put(img, lay, t, tl, cy=1140)

def pill(img, f, name):
    d = ImageDraw.Draw(img); w = bfont(64).getlength(name) + 190
    d.rounded_rectangle((W / 2 - w / 2, 150, W / 2 + w / 2, 250), 50, fill="#ffffff")
    logo(img, L / f, W / 2 - w / 2 + 62, 200, 60, disc=True)
    d.text((W / 2 + 50, 200), name, font=bfont(64), fill=BG, anchor="mm")

def stamp(img, t, t0, s, cy=1190):
    if t < t0: return
    lay, dl = layer(); w = bfont(84).getlength(s) + 90
    dl.rounded_rectangle((W / 2 - w / 2, cy - 75, W / 2 + w / 2, cy + 75), 24, fill=RED)
    dl.text((W / 2, cy), s, font=bfont(84), fill="#ffffff", anchor="mm")
    put(img, lay.rotate(-5, center=(W / 2, cy)), t, t0, dur=0.12, start=2.2, cy=cy)

def s_gpt(t):
    img = Image.new("RGBA", (W, H), BG); pill(img, "chatgpt.png", "ChatGPT")
    t0 = at("Three")
    view = GPT.render(t, [(LINE[2], (720, 220, 1340)), (t0 - 0.3, (470, 380, 820))],
                      [(t0 + 0.1, (148, 312, 290, 352), "1"), (t0 + 0.35, (148, 364, 225, 404), "2"), (t0 + 0.6, (148, 416, 298, 456), "3")], (1000, 860), BLUE)
    img.alpha_composite(view, (40 + round(W * (1 - smooth((t - LINE[2]) / 0.3))), 300))
    stamp(img, t, at("us") - 0.15, "WE'RE NOT ON IT")
    return shake(img, t, at("us") - 0.15, 24)

T_DOTS = at("In") - 0.1

def s_forbes(t):
    img = Image.new("RGBA", (W, H), BG); d = ImageDraw.Draw(img)
    btext(d, 140, "FORBES: SALESMATE IS #1", 80, "#ffcc00")
    view = ORG.render(t, [(LINE[4], (440, 560, 640)), (at("Salesmate") - 0.3, (520, 622, 440))],
                      [(at("Forbes") - 0.05, (150, 538, 612, 606), None), (at("Salesmate") - 0.05, (388, 612, 660, 632), None)], (1000, 860), YEL)
    img.alpha_composite(view, (40 + round(W * (1 - smooth((t - LINE[4]) / 0.3))), 300))
    return img

def s_dots(t):
    img = Image.new("RGBA", (W, H), BG); d = ImageDraw.Draw(img)
    btext(d, 120, "201 AI ANSWERS ABOUT CRM", 84, INK)
    n = round(201 * smooth((t - T_DOTS) / 1.0))
    tz = at("zero") - 0.1; fade = 1 - 0.75 * smooth((t - tz) / 0.2)
    for k in range(n):
        x, y = 120 + k % 15 * 60, 300 + k // 15 * 60
        d.ellipse((x - 21, y - 21, x + 21, y + 21), fill=tuple(int(v * fade + 11 * (1 - fade)) for v in (70, 90, 130)))
    if t >= tz:
        lay, dl = layer(); dl.text((W / 2, 640), "0", font=bfont(560), fill=RED, anchor="mm")
        btext(dl, 950, "TIMES SALESMATE APPEARED", 70, INK)
        put(img, lay, t, tz, dur=0.15, start=2.4, cy=700)
    return shake(img, t, tz, 30, 0.35)

SCENES = [(0, LINE[1], clip_scene("s1.mp4", 0, hook)), (LINE[1], LINE[2], clip_scene("s2.mp4", 1, typing)),
          (LINE[2], LINE[3], s_gpt), (LINE[3], LINE[4], clip_scene("s4.mp4", 3, thesis)),
          (LINE[4], T_DOTS, s_forbes), (T_DOTS, LINE[5], s_dots),
          (LINE[5], VO_END + 0.2, clip_scene("s6.mp4", 5, outro)), (VO_END + 0.2, LENGTH, s_end_factory("Does AI recommend your brand?"))]

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
