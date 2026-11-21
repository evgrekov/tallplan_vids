"""Shared kit for Google App campaign videos: one scene timeline rendered in 9:16, 1:1 and 16:9.
Every scene is a phone screen (1320x2868 like the app screenshots) shown in a phone mock; captions follow the voice.
"""
import array, pathlib, subprocess, sys, wave
from PIL import Image, ImageDraw, ImageFilter, ImageFont
ROOT = pathlib.Path(__file__).parent.parent
sys.path[:0] = [str(ROOT / "slides"), str(ROOT / "3d")]
import api, oai
from api import gemini, data

FPS = 30
CAP_Y = 0.8  # portrait caption height; an ad moves it when its own UI lives at the bottom
SW, SH = 1320, 2868  # screenshot size
BG, LIME, INK = (6, 7, 8), (212, 242, 78), (10, 10, 13)
LOGO = ROOT / "TallPlan 13:11/Logo"
SHOTS = ROOT / "TallPlan 13:11/Screenshots/iOS/promo/ft"
FORMATS = {"9x16": (1080, 1920), "1x1": (1080, 1080), "16x9": (1920, 1080)}

def archivo(size, wght=800, wdth=100):
    f = ImageFont.truetype(str(ROOT / "muscle/assets/fonts/Archivo.ttf"), size); f.set_variation_by_axes([wght, wdth]); return f

def ease(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

def zoom(img, z, fx=0.5, fy=0.5):
    """Crop a 1/z part of the screen around (fx, fy) and scale it back: a camera push-in on the UI."""
    w, h = img.width / z, img.height / z
    x = min(max(fx * img.width - w / 2, 0), img.width - w); y = min(max(fy * img.height - h / 2, 0), img.height - h)
    return img.resize(img.size, Image.LANCZOS, (x, y, x + w, y + h))

# ---------- audio ----------
TEEN = "Energetic, upbeat 16-year-old guy, bright young voice, fast and playful, casual Gen Z tone."
CTA = "Download TallPlan"
MAX = 15.0  # Google ads brief: no longer than 15 seconds

def trim(pcm, floor=600, keep=0.05):
    """Cut TTS silence at both ends (s16le mono 24 kHz), keeping 50 ms of air."""
    a = array.array("h", pcm); loud = [i for i, v in enumerate(a) if abs(v) > floor]
    pad = round(24000 * keep)
    return a[max(0, loud[0] - pad):loud[-1] + pad].tobytes()

def say(path, text, how, speed=1.0, voice="verse"):
    if not path.exists():
        print(f"🎙️  {path.name}...")
        path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(trim(oai.speech(text, how, voice, speed)))
    with wave.open(str(path)) as w: return w.getnframes() / w.getframerate()

def music(path, prompt):
    if not path.exists():
        print("🎵 music...")
        path.write_bytes(data(gemini("lyria-3-clip-preview", [{"text": f"Instrumental only, no vocals. {prompt}"}], responseModalities=["AUDIO"])))

def mix(cues, track, total, out, vol=0.2):
    """cues: [(wav, start)] voice lines; track: music under them; loudness for YouTube ads."""
    ins = sum([["-i", str(w)] for w, _ in cues], []) + ["-i", str(track)]
    n = len(cues)
    fc = "".join(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={round(s * 1000)}:all=1,apad[v{i}];" for i, (_, s) in enumerate(cues))
    fc += (f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{total:.3f},afade=t=out:st={total - 1:.3f}:d=1,volume={vol},apad[m];"
           + "".join(f"[v{i}]" for i in range(n)) + f"[m]amix=inputs={n + 1}:normalize=0,atrim=0:{total:.3f},loudnorm=I=-14:TP=-1.5[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", fc, "-map", "[a]", "-ar", "48000", "-ac", "2", str(out)], check=True)

# ---------- layout ----------
def layout(W, H):
    """Phone screen rect and caption box per format: portrait = phone centered with captions over its lower part, others = phone + text side."""
    if H > W: sh = 1580; return dict(phone=((W - sh * SW // SH) // 2, 250, sh), text=(60, int(H * CAP_Y), W - 120), brand=(W // 2, 120))
    if W > H: sh = 940; return dict(phone=(W - 200 - sh * SW // SH, 70, sh), text=(140, 300, 980), brand=(140, 150))
    sh = 960; return dict(phone=(W - 70 - sh * SW // SH, 60, sh), text=(70, 260, 500), brand=(70, 130))

_mock, _bg = {}, {}
def mock(sh):
    """Phone bezel + rounded screen mask for a screen of height sh."""
    if sh not in _mock:
        sw, pad = sh * SW // SH, round(sh * 0.016)
        r = round(sw * 0.13)
        body = Image.new("RGBA", (sw + 2 * pad, sh + 2 * pad))
        ImageDraw.Draw(body).rounded_rectangle((0, 0, body.width - 1, body.height - 1), r + pad, fill=(18, 18, 22), outline=(70, 72, 80), width=3)
        mask = Image.new("L", (sw, sh)); ImageDraw.Draw(mask).rounded_rectangle((0, 0, sw - 1, sh - 1), r, fill=255)
        _mock[sh] = (body, mask, pad)
    return _mock[sh]

def brand(img, x, y, center):
    icon = Image.open(LOGO / "app-icon.png").convert("RGBA").resize((70, 70), Image.LANCZOS)
    m = Image.new("L", icon.size); ImageDraw.Draw(m).rounded_rectangle((0, 0, 69, 69), 16, fill=255); icon.putalpha(m)
    wm = Image.open(LOGO / "wordmark.png"); wm = wm.resize((round(wm.width * 46 / wm.height), 46), Image.LANCZOS)
    x0 = x - (70 + 18 + wm.width) // 2 if center else x
    img.alpha_composite(icon, (x0, y - 35)); img.alpha_composite(wm, (x0 + 88, y - 26))

def words_at(cues, t):
    """(line words, index of the current word) of the voice line playing at t; words spread over the line by length."""
    for text, st, d in cues:
        if st <= t < st + d + 0.35:
            ws = text.split(); tot, acc = sum(len(w) + 1 for w in ws), 0
            cur = 0
            for i, w in enumerate(ws):
                if st + d * acc / tot <= t: cur = i
                acc += len(w) + 1
            return ws, cur
    return None, None

def captions(img, L, cues, t, portrait):
    ws, cur = words_at(cues, t)
    if not ws: return
    d = ImageDraw.Draw(img)
    x0, y0, bw = L["text"]
    if portrait:  # 3-word chunk, current word lime, like our TikTok subtitles
        first = cur - cur % 3; chunk = ws[first:first + 3]
        f = archivo(84, 900)
        while f.getlength(" ".join(chunk)) > bw: f = archivo(f.size - 4, 900)
        x = img.width / 2 - f.getlength(" ".join(chunk)) / 2
        for j, w in enumerate(chunk):
            d.text((x, y0), w, font=f, fill=LIME if first + j == cur else "white", anchor="lm", stroke_width=9, stroke_fill="black")
            x += f.getlength(w + " ")
        return
    f = archivo(64 if img.width > img.height else 54, 850)  # side text: the whole line, spoken words lit
    x, y, lh = x0, y0, f.size * 1.18
    for i, w in enumerate(ws):
        if x > x0 and x + f.getlength(w) > x0 + bw: x, y = x0, y + lh
        d.text((x, y), w, font=f, fill=LIME if i == cur else ("white" if i < cur else (90, 92, 100)))
        x += f.getlength(w + " ")

def frame(W, H, screen, cues, t, card=None):
    """One output frame: background, phone with the scene's screen, brand mark, captions; `card` (RGBA full frame) covers it all for the packshot."""
    L = layout(W, H)
    if (W, H) not in _bg:  # dark background with a soft blue glow behind the phone
        g = Image.new("RGBA", (W, H), BG + (255,))
        ImageDraw.Draw(g).ellipse((W * 0.2, H * 0.2, W * 0.8, H * 0.8) if H > W else (L["phone"][0] - 300, -200, W, H + 200), fill=(30, 45, 150, 255))
        _bg[(W, H)] = Image.blend(Image.new("RGBA", (W, H), BG + (255,)), g.filter(ImageFilter.GaussianBlur(160)), 0.5)
    img = _bg[(W, H)].copy()
    x, y, sh = L["phone"]
    body, mask, pad = mock(sh)
    img.alpha_composite(body, (x - pad, y - pad))
    img.paste(screen.resize(mask.size, Image.LANCZOS), (x, y), mask)
    brand(img, *L["brand"], center=H > W)
    captions(img, L, cues, t, H > W)
    if card is not None: img.alpha_composite(card)
    return img.convert("RGB")

def packshot(W, H, line, small, k):
    """End card over everything, fading in with k 0..1: icon, wordmark, line in lime, App Store badge, small disclaimer."""
    c = Image.new("RGBA", (W, H), BG + (255,))
    s = min(W, H) / 1080
    icon = Image.open(LOGO / "app-icon.png").convert("RGBA").resize((round(260 * s),) * 2, Image.LANCZOS)
    m = Image.new("L", icon.size); ImageDraw.Draw(m).rounded_rectangle((0, 0, icon.width - 1, icon.height - 1), round(58 * s), fill=255); icon.putalpha(m)
    wm = Image.open(LOGO / "wordmark.png"); wm = wm.resize((round(wm.width * 110 * s / wm.height), round(110 * s)), Image.LANCZOS)
    top = H / 2 - 400 * s
    c.alpha_composite(icon, (round(W / 2 - icon.width / 2), round(top)))
    c.alpha_composite(wm, (round(W / 2 - wm.width / 2), round(top + 300 * s)))
    d = ImageDraw.Draw(c)
    d.text((W / 2, top + 480 * s), line, font=archivo(round(72 * s), 850), fill=LIME, anchor="ma")
    badge = Image.open(ROOT / "gads/assets/appstore_badge.png"); badge = badge.resize((round(badge.width * 120 * s / badge.height), round(120 * s)), Image.LANCZOS)
    c.alpha_composite(badge, (round(W / 2 - badge.width / 2), round(top + 590 * s)))
    d.text((W / 2, top + 750 * s), small, font=archivo(round(34 * s), 500), fill=(140, 142, 150), anchor="ma")
    c.putalpha(c.getchannel("A").point(lambda v: int(v * ease(k))))
    return c

def render(name, W, H, total, screen_at, cues, end_at, end_line, end_small, audio, out):
    """Pipe frames into an H.264 file tuned for YouTube ads (High profile, closed GOP of half a second, 8 Mbit/s, AAC 48 kHz)."""
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(audio),
                           "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-b:v", "8M", "-maxrate", "10M", "-bufsize", "16M",
                           "-g", str(FPS // 2), "-bf", "2", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-shortest",
                           "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
    n = round(total * FPS)
    for i in range(n):
        t = i / FPS
        card = packshot(W, H, end_line, end_small, (t - end_at) / 0.35) if t >= end_at else None
        ff.stdin.write(frame(W, H, screen_at(t), cues, t, card).tobytes())
        if i % 90 == 0: print(f"🎞️  {name} {i}/{n}")
    ff.stdin.close(); ff.wait()
    print(f"✅ {out}")

# ---------- screen helpers ----------
EMOJI = ImageFont.truetype("/System/Library/Fonts/Apple Color Emoji.ttc", 160)

def is_emoji(ch): return ord(ch) > 0x1F000

def rich(img, xy, text, f, fill):
    """Text with emoji: emoji are drawn from Apple Color Emoji and scaled to the line height."""
    x, y = xy; d = ImageDraw.Draw(img)
    for ch in text:
        if is_emoji(ch):
            e = Image.new("RGBA", (170, 170)); ImageDraw.Draw(e).text((0, 0), ch, font=EMOJI, embedded_color=True)
            s = round(f.size * 1.05); e = e.crop(e.getbbox()).resize((s, s), Image.LANCZOS)
            img.paste(e, (round(x), round(y + f.size * 0.08)), e); x += s + 6
        else:
            d.text((x, y), ch, font=f, fill=fill); x += f.getlength(ch)
    return x

def width(text, f): return sum(f.size * 1.05 + 6 if is_emoji(ch) else f.getlength(ch) for ch in text)

def bar(clock):
    """The app's iOS status bar with our own clock time."""
    b = Image.open(SHOTS / "01-home.png").convert("RGB").crop((0, 0, SW, 190))
    ImageDraw.Draw(b).rectangle((120, 40, 420, 170), fill=BG)
    ImageDraw.Draw(b).text((215, 100), clock, font=archivo(66, 650), fill="white", anchor="mm")
    return b

def tap(img, x, y, k):
    """Finger tap: a ring growing and fading at (x, y) while k goes 0..1."""
    if not 0 <= k <= 1: return img
    o = Image.new("RGBA", img.size); r = 60 + 160 * k
    ImageDraw.Draw(o).ellipse((x - r, y - r, x + r, y + r), outline=(255, 255, 255, int(220 * (1 - k))), width=14)
    ImageDraw.Draw(o).ellipse((x - 55, y - 55, x + 55, y + 55), fill=(255, 255, 255, int(120 * (1 - k))))
    return Image.alpha_composite(img.convert("RGBA"), o).convert("RGB")

def shot(img, k, u, z=(1, 1.1), f=(0.5, 0.5), at=None, flash=False):
    """An app screenshot at progress k 0..1 (u s into the scene): push-in z0→z1 around f, optional tap at (x, y) near the end, optional reveal flash."""
    if at: img = tap(img, *at, (k - 0.6) / 0.35)
    im = zoom(img, z[0] + (z[1] - z[0]) * ease(k), *f)
    return Image.blend(im, Image.new("RGB", im.size, "white"), 0.7 * (1 - u / 0.2)) if flash and u < 0.2 else im

def shots(t, seq):
    """seq: [(start, end or None = 3 s, kwargs for shot with img)], the scene playing at t."""
    for a, b, kw in seq:
        b = b or a + 3
        if a <= t < b or kw is seq[-1][2]: return shot(k=min(1, (t - a) / (b - a)), u=t - a, **kw)

# ---------- one ad from voice lines + scenes ----------
def timeline(D, lines, speed=1.15):
    """lines: [(key, text, voice direction[, pause after])] → [(key, text, start, duration)] back to back."""
    cues, t = [], 0.2
    for key, text, how, *pause in lines:
        d = say(D / f"{key}.wav", text, how, speed)
        cues.append((key, text, t, d)); t += d + (pause[0] if pause else 0.12)
    return cues

def length(cues): return cues[-1][2] + cues[-1][3] + 0.9

def _build(fmt, D, lines, scenes, small):
    cues = timeline(D, lines)
    st = {k: (s, d) for k, _, s, d in cues}
    render(fmt, *FORMATS[fmt], length(cues), scenes(st), [(x, s, d) for _, x, s, d in cues], cues[-1][2] - 0.3,
           CTA, small, D / "audio.wav", D / f"tallplan_{D.name}_{fmt}.mp4")

def make(D, lines, scenes, small, music_prompt):
    """Voice → music → mix → the three formats in parallel. scenes(st) returns screen(t); the last line is the CTA under the end card."""
    from concurrent.futures import ProcessPoolExecutor
    from functools import partial
    cues = timeline(D, lines)
    assert length(cues) <= MAX, f"{length(cues):.1f}s is longer than {MAX}s"
    music(D / "music.mp3", music_prompt)
    mix([(D / f"{k}.wav", s) for k, _, s, _ in cues], D / "music.mp3", length(cues), D / "audio.wav")
    with ProcessPoolExecutor(3) as ex: list(ex.map(partial(_build, D=D, lines=lines, scenes=scenes, small=small), FORMATS))
    print(f"💰 Google (Lyria) ~${api.spent:.3f} · OpenAI (TTS) ~${oai.spent:.3f}")
