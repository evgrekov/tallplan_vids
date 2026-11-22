# /// script
# dependencies = ["pillow"]
# ///
"""Free local edit for "Ranked on Google, ignored by AI": every frame is drawn with Pillow and piped to ffmpeg,
music is ducked under out/voice.wav, captions.py burns the captions, the result is slowed 10% (same pitch).
Forbes result on Google (Nov 9, 2026); AI answers from SupaIntent sensor data, CRM categories.
Usage: uv run build.py  →  out/final.mp4
"""
import json, math, pathlib, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).parent
OUT, SS, L = ROOT / "out", ROOT / "screenshots", ROOT / "logos"
W, H, FPS = 1080, 1920, 30
BG, INK, ACC, GREY, RED, LEAD = "#0d1117", "#ffffff", "#ffcc00", "#8b949e", "#ff3b3b", 1.0

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

# ---------- scenes: dark newsroom, yellow evidence marker, Bebas Neue; camera moves over real screenshots ----------
from camera import Shot, smooth
FONT = str(ROOT / "fonts/Display.ttf")
ORG = Shot(SS / "google-organic.jpg", FONT, [(860, 285, 1240, 385)])
AIM, GPT = (Shot(SS / f, FONT) for f in ("google-ai-mode-answer.png", "chatgpt-answer-crm.png"))
YEL = (255, 204, 0)
TOTAL, HUBSPOT = 201, 116

def pill(img, f, name):
    d = ImageDraw.Draw(img); w = font(70).getlength(name) + 190
    d.rounded_rectangle((W / 2 - w / 2, 150, W / 2 + w / 2, 250), 50, fill="#ffffff")
    logo(img, L / f, W / 2 - w / 2 + 62, 200, 60, disc=True)
    d.text((W / 2 + 50, 202), name, font=font(70), fill=BG, anchor="mm")

def stamp(img, t, t0, cy=1120):
    """Red NO SALESMATE stamp slammed over the evidence."""
    if t < t0: return
    lay, dl = layer(); s = "NO SALESMATE"; w = font(110).getlength(s) + 80
    dl.rounded_rectangle((W / 2 - w / 2, cy - 85, W / 2 + w / 2, cy + 85), 24, fill=RED)
    dl.text((W / 2, cy + 4), s, font=font(110), fill="#ffffff", anchor="mm")
    put(img, lay.rotate(-6, center=(W / 2, cy)), t, t0, dur=0.12, start=2.2, cy=cy)

def s_hook(t):
    img = Image.new("RGBA", (W, H), BG)
    view = ORG.render(t, [(0, (560, 330, 760)), (0.6, (400, 572, 560)), (at("best") - 0.3, (500, 622, 440))],
                      [(at("Forbes", 0) + 0.5, (150, 538, 612, 606), None), (at("best") - 0.1, (388, 612, 660, 632), None)], (1000, 860), YEL)
    img.alpha_composite(view, (40, 430))
    lay, dl = layer(); text(dl, 90, "GOOGLE PAGE ONE SAYS", 84, GREY); text(dl, 190, "SALESMATE IS #1", 160, ACC)
    put(img, lay, t, 0, dur=0.2, start=2.0, cy=250)
    return shake(img, t, at("Salesmate") - 0.1, 22)

def screen(shot, f, name, keys, marks, i, t_stamp):
    def s(t):
        img = Image.new("RGBA", (W, H), BG); pill(img, f, name)
        x = 40 + round(W * (1 - smooth((t - LINE[i]) / 0.3)))  # whip in from the right
        img.alpha_composite(shot.render(t, keys, marks, (1000, 940), YEL), (x, 300))
        stamp(img, t, t_stamp)
        return shake(img, t, t_stamp, 26)
    return s

s_aim = screen(AIM, "google-ai-mode.png", "GOOGLE AI MODE",
    [(LINE[1], (380, 250, 640)), (at("HubSpot") - 0.35, (250, 520, 520))],
    [(at("HubSpot") - 0.05, (35, 385, 330, 447), "1"), (at("Pipedrive") - 0.05, (35, 455, 330, 517), "2"),
     (at("Zoho") - 0.05, (35, 527, 330, 589), "3"), (at("Salesforce") - 0.05, (35, 597, 330, 659), "4")], 1, at("Salesforce") + 0.55)
s_gpt = screen(GPT, "chatgpt.png", "CHATGPT",
    [(LINE[2], (720, 220, 1340)), (at("HubSpot", 1) - 0.3, (470, 380, 820))],
    [(at("HubSpot", 1) - 0.05, (148, 312, 290, 352), "1"), (at("Attio") - 0.05, (148, 364, 225, 404), "2"),
     (at("Pipedrive", 1) - 0.05, (148, 416, 298, 456), "3")], 2, at("Pipedrive", 1) + 0.5)

def s_count(t):
    img = Image.new("RGBA", (W, H), BG); d = ImageDraw.Draw(img)
    d.text((W / 2, 120), f"{TOTAL} AI ANSWERS ABOUT CRM", font=font(90), fill=INK, anchor="ma")
    n = round(TOTAL * smooth((t - at("two")) / 1.0))  # answers pour in
    hub = round(HUBSPOT * smooth((t - at("CRM", -1)) / 0.6))
    tz = at("Salesmate", -1) - 0.1
    fade = 1 - 0.75 * smooth((t - tz) / 0.2)
    for k in range(n):
        x, y = 120 + k % 15 * 60, 300 + k // 15 * 60
        c = YEL if k < hub else (70, 78, 90)
        d.ellipse((x - 21, y - 21, x + 21, y + 21), fill=tuple(int(v * fade + 13 * (1 - fade)) for v in c))
    if hub: d.text((W / 2, 1150), f"HUBSPOT: {hub}", font=font(84), fill=ACC, anchor="ma")
    if t >= tz:
        lay, dl = layer(); dl.text((W / 2, 640), "0", font=font(600), fill=RED, anchor="mm")
        dl.text((W / 2, 930), "SALESMATE MENTIONS", font=font(110), fill=INK, anchor="ma")
        put(img, lay, t, tz, dur=0.15, start=2.4, cy=700)
    return shake(img, t, tz, 30, 0.35)

def s_cta(t):
    img = Image.new("RGBA", (W, H), BG); d = ImageDraw.Draw(img); t0 = LINE[4]
    e = smooth((t - t0) / 0.35)
    d.text((W / 2 - 700 * (1 - e), 260), "RANKED", font=font(230), fill=INK, anchor="ma")
    d.text((W / 2 + 700 * (1 - e), 680), "PICKED", font=font(230), fill=ACC, anchor="ma")
    tn = at("same") - 0.1
    if t >= tn:
        lay, dl = layer(); dl.text((W / 2, 590), "≠", font=bfont(260), fill=RED, anchor="mm")
        put(img, lay, t, tn, dur=0.12, start=2.5, cy=590)
    tl = at("SupaIntent", -1) - 0.3
    if t >= tl:
        lay, dl = layer(); pw = lockup_w(72) / 2 + 60
        dl.rounded_rectangle((W / 2 - pw, 1040, W / 2 + pw, 1200), 44, fill="#ffffff")
        lockup(lay, W / 2, 1120, 72)
        put(img, lay, t, tl, cy=1120)
    return shake(shake(img, t, tn, 28), t, tl, 14)
SCENES = [(0, LINE[1], s_hook), (LINE[1], LINE[2], s_aim), (LINE[2], LINE[3], s_gpt), (LINE[3], LINE[4], s_count),
          (LINE[4], VO_END + 0.2, s_cta), (VO_END + 0.2, LENGTH, s_end_factory("Ranked on Google ≠ picked by AI"))]

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
