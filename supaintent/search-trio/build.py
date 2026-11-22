# /// script
# dependencies = ["pillow"]
# ///
"""Free local edit for "Same question, three engines": every frame is drawn with Pillow and piped to ffmpeg,
music is ducked under out/voice.wav, captions.py burns the captions, the result is slowed 10% (same pitch).
Screenshots: Google (Nov 9, 2026), Google AI Overview and ChatGPT for "best crm for small business".
Usage: uv run build.py  →  out/final.mp4
"""
import json, math, pathlib, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).parent
OUT, SS, L = ROOT / "out", ROOT / "screenshots", ROOT / "logos"
W, H, FPS = 1080, 1920, 30
BG, INK, ACC, GREY, LEAD = "#f6f7fb", "#101828", "#2563eb", "#667085", 1.1

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

# ---------- scenes: clean light UI, blue accent, Manrope; camera moves over real screenshots ----------
from camera import Shot, smooth
FONT = str(ROOT / "fonts/Brand.ttf")
ORG = Shot(SS / "google-organic.jpg", FONT, [(860, 285, 1240, 385)])
AIO, GPT = (Shot(SS / f, FONT) for f in ("google-ai-overview.png", "chatgpt-answer-crm.png"))
ACC_RGB = (37, 99, 235)
VIEW, VY = (1000, 940), 300
ENGINES = (("google-ai-mode.png", "Google"), ("google-ai-mode.png", "AI Overview"), ("chatgpt.png", "ChatGPT"))

def s_hook(t):
    img = Image.new("RGBA", (W, H), BG); d = ImageDraw.Draw(img)
    lay, dl = layer(); text(dl, 110, "SAME QUESTION.", 104, INK); text(dl, 240, "3 ANSWERS.", 150, ACC)
    put(img, lay, t, 0, dur=0.2, start=2.0, cy=260)
    q = "best crm for small business"; n = min(len(q), int(t / 0.04))  # typed in ~1 s
    box(d, 520, q[:n] + ("|" if int(t * 3) % 2 else " "), 58, "#ffffff", INK, r=40)
    for k, (f, name) in enumerate(ENGINES):
        tk, cx = 1.0 + k * 0.3, 200 + k * 340
        if t < tk: continue
        cy = 830 + 14 * math.sin((t - tk) * 5 + k)  # logos bob while waiting for their turn
        lay, dl = layer(); logo(lay, L / f, cx, cy, 150, disc=True)
        dl.text((cx, cy + 110), name, font=bfont(48), fill=INK, anchor="ma")
        put(img, lay, t, tk, dur=0.15, start=1.8, cx=cx, cy=cy)
    return shake(img, t, 1.0, 14)

def screen(shot, eng, keys, marks, i):
    """Engine label + camera view; the view whips in from the right at the scene start."""
    def s(t):
        img = Image.new("RGBA", (W, H), BG); d = ImageDraw.Draw(img)
        f, name = ENGINES[eng]; w = bfont(64).getlength(name) + 190
        d.rounded_rectangle((W / 2 - w / 2, 150, W / 2 + w / 2, 250), 50, fill=INK)
        logo(img, L / f, W / 2 - w / 2 + 62, 200, 60, disc=True)
        d.text((W / 2 + 50, 200), name, font=bfont(64), fill="#ffffff", anchor="mm")
        view = shot.render(t, keys, marks, VIEW, ACC_RGB)
        x = 40 + round(W * (1 - smooth((t - LINE[i]) / 0.3)))
        img.alpha_composite(view, (x, VY))
        return shake(img, t, marks[-1][0], 10, 0.2) if marks else img
    return s

s_org = screen(ORG, 0,
    [(LINE[1], (650, 345, 780)), (at("links") - 0.25, (470, 420, 700)), (at("Reddit") - 0.25, (430, 330, 620)),
     (at("Forbes") - 0.25, (385, 572, 520)), (at("Slack") - 0.25, (335, 720, 470))],
    [(at("Reddit") - 0.05, (150, 295, 705, 365), "1"), (at("Forbes") - 0.05, (150, 538, 612, 606), "2"),
     (at("Slack") - 0.05, (150, 686, 515, 755), "3")], 1)
s_aio = screen(AIO, 1,
    [(LINE[2], (300, 200, 600)), (at("HubSpot") - 0.3, (320, 260, 600)), (at("Pipedrive") - 0.3, (320, 360, 600))],
    [(at("HubSpot") - 0.05, (50, 218, 590, 245), "1"), (at("Pipedrive") - 0.05, (50, 335, 585, 362), "2")], 2)
s_gpt = screen(GPT, 2,
    [(LINE[3], (720, 220, 1340)), (at("HubSpot", 1) - 0.3, (470, 380, 820))],
    [(at("HubSpot", 1) - 0.05, (148, 312, 290, 352), "1"), (at("Attio") - 0.05, (148, 364, 225, 404), "2"),
     (at("Pipedrive", 1) - 0.05, (148, 416, 298, 456), "3")], 3)

PICKS = (("Reddit", "Forbes", "Slack"), ("HubSpot", "Pipedrive"), ("HubSpot", "Attio", "Pipedrive"))

def s_cta(t):
    img = Image.new("RGBA", (W, H), BG); d = ImageDraw.Draw(img)
    lay, dl = layer(); text(dl, 130, "3 ENGINES.", 110, INK); text(dl, 260, "3 DIFFERENT LISTS.", 84, ACC)
    put(img, lay, t, LINE[4], dur=0.15, start=1.8, cy=240)
    for k, ((f, name), picks) in enumerate(zip(ENGINES, PICKS)):
        tk = LINE[4] + 0.35 + k * 0.2
        if t < tk: continue
        x = 40 + k * 340; y = 420 + round(400 * (1 - smooth((t - tk) / 0.3)))  # cards slide up one by one
        lay, dl = layer()
        dl.rounded_rectangle((x, y, x + 320, y + 560), 32, fill="#ffffff", outline="#e4e7ec", width=3)
        logo(lay, L / f, x + 160, y + 90, 90, disc=True)
        dl.text((x + 160, y + 160), name, font=bfont(40), fill=INK, anchor="ma")
        for j, p in enumerate(picks):
            dl.rounded_rectangle((x + 30, y + 240 + j * 100, x + 290, y + 320 + j * 100), 40, fill="#eef4ff")
            dl.text((x + 160, y + 280 + j * 100), p, font=bfont(40, 700), fill=ACC, anchor="mm")
        img.alpha_composite(lay)
    tl = at("SupaIntent", -1) - 0.3
    if t >= tl:
        lay, dl = layer(); pw = lockup_w(72) / 2 + 60
        dl.rounded_rectangle((W / 2 - pw, 1060, W / 2 + pw, 1220), 44, fill="#ffffff", outline=ACC, width=4)
        lockup(lay, W / 2, 1140, 72)
        put(img, lay, t, tl, cy=1140)
    return shake(img, t, tl, 16)

SCENES = [(0, LINE[1], s_hook), (LINE[1], LINE[2], s_org), (LINE[2], LINE[3], s_aio), (LINE[3], LINE[4], s_gpt),
          (LINE[4], VO_END + 0.2, s_cta), (VO_END + 0.2, LENGTH, s_end_factory("See what AI recommends in your niche"))]

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
