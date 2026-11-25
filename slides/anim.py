"""Shared helpers of the animated voiceover formats (char.py, facts.py): cut-outs, easing, sprites, per-line voice timing,
word subtitles, music, SFX, ffmpeg encode, packshot + CTA."""
import json, math, pathlib, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "3d"))
import api, oai, voice
from api import gemini, data

W, H, FPS, SR = 1080, 1920, 30, 24000
GAP, PACKSHOT = 0.06, 2.2
FONT = HERE.parent / "3d/fonts/Montserrat.ttf"
CTA = "PREDICT\nYOUR HEIGHT"
SFX = {  # synthesized cartoon sounds (ffmpeg lavfi sources)
    "boing": "aevalsrc='0.6*sin(2*PI*(220+160*sin(2*PI*9*t))*t)*exp(-4*t)':d=0.5",
    "whoosh": "anoisesrc=d=0.35:color=pink:a=0.5,highpass=f=900,lowpass=f=5000,afade=t=in:d=0.15,afade=t=out:st=0.15:d=0.2",
    "pop": "aevalsrc='0.7*sin(2*PI*(900-600*t)*t)*exp(-30*t)':d=0.12",
    "bonk": "aevalsrc='0.8*sin(2*PI*140*t)*exp(-14*t)+0.2*sin(2*PI*420*t)*exp(-20*t)':d=0.35",
    "ding": "aevalsrc='0.4*sin(2*PI*1568*t)*exp(-4*t)+0.2*sin(2*PI*3136*t)*exp(-6*t)':d=0.9",
    "rise": "aevalsrc='0.35*sin(2*PI*(300+900*t)*t)*min(1\\,3*t)':d=0.8,afade=t=out:st=0.6:d=0.2",
}

def font(size, wght=900):
    f = ImageFont.truetype(str(FONT), size); f.set_variation_by_axes([wght]); return f

def cutout(p, height=None, width=None):
    """White background → transparent by flood fill from the border (stops at the black outline, keeps white inside)."""
    im = Image.open(p).convert("RGBA")
    for xy in [(x, y) for x in (0, im.width // 2, im.width - 1) for y in (0, im.height // 2, im.height - 1) if (x, y) != (im.width // 2, im.height // 2)]:
        if im.getpixel(xy)[3]: ImageDraw.floodfill(im, xy, (255, 255, 255, 0), thresh=60)
    im = im.crop(im.getbbox())
    k = min(height / im.height if height else 9, width / im.width if width else 9)
    return im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)

def cover(p, m=1.1):
    im = Image.open(p).convert("RGB")
    k = max(W * m / im.width, H * m / im.height)
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    return im.crop(((im.width - round(W * m)) // 2, (im.height - round(H * m)) // 2, (im.width + round(W * m)) // 2, (im.height + round(H * m)) // 2))

def ease(p): return 1 - (1 - min(max(p, 0), 1)) ** 3
def back(p):  # ease-out with overshoot: the cartoon "pop"
    p = min(max(p, 0), 1); return 1 + 2.7 * (p - 1) ** 3 + 1.7 * (p - 1) ** 2

def sprite(fr, im, cx, bottom, s=1, sx=1, sy=1, rot=0):
    """Paste a cut-out scaled around its feet (bottom center), rotated."""
    w, h = max(1, round(im.width * s * sx)), max(1, round(im.height * s * sy))
    im = im.resize((w, h), Image.BILINEAR)
    if rot: im = im.rotate(rot, Image.BICUBIC, expand=True)
    fr.alpha_composite(im, (round(cx - im.width / 2), round(bottom - im.height + (im.height - h) / 2)))

def camera(im, u, dur):
    """Background: punch-in on the cut, then a slow push."""
    k = (1 + 0.1 * (1 - ease(u / 0.25)) + 0.04 * u / dur) / 1.1
    iw, ih = im.width / 2, im.height / 2
    return im.transform((W, H), Image.AFFINE, (1 / k, 0, iw - W / 2 / k, 0, 1 / k, ih - H / 2 / k), Image.BILINEAR)

def voiceover(d, lines, plan, speed):
    """One TTS clip per line, lines back to back; returns (starts, durations, total). The last line plays under the packshot."""
    vo_f = d / "vo.json"
    if not vo_f.exists():
        print("🎙️  voiceover...")
        for i, s in enumerate(lines):
            (d / f"vo{i}.raw").write_bytes(voice.fx(oai.speech(s, plan["voice"], plan["openai_voice"], speed), f"{voice.TRIM},areverse,{voice.TRIM},areverse"))
        vo_f.write_text(json.dumps([(d / f"vo{i}.raw").stat().st_size / 2 / SR for i in range(len(lines))]))
    dur = json.loads(vo_f.read_text())
    starts, t = [], 0.0
    for v in dur: starts.append(t); t += v + GAP
    total = max(t, starts[-1] + PACKSHOT)
    pcm = bytearray(round(total * SR) * 2)
    for i, st in enumerate(starts):
        c, o = (d / f"vo{i}.raw").read_bytes(), round(st * SR) * 2
        pcm[o:o + len(c)] = c[:len(pcm) - o]
    (d / "vo.raw").write_bytes(pcm)
    return starts, dur, total

class Subs:
    """Word-by-word subtitles: 3-word chunk, current word yellow, above the bottom UI zone; none under the packshot."""
    def __init__(self, starts, dur, lines):
        self.words, self.end, self.f = [], starts[-1], font(84)
        for st, v, s in zip(starts[:-1], dur, lines):  # each line's words spread over its clip by length
            ws = s.split()
            tot, acc = sum(len(w) + 1 for w in ws), 0
            for w in ws:
                self.words.append((st + v * acc / tot, w)); acc += len(w) + 1

    def draw(self, fr, t):
        cur = max((i for i, (a, _) in enumerate(self.words) if a <= t), default=None)
        if cur is None or t >= self.end: return
        first = cur - cur % 3
        chunk = [w.upper() for _, w in self.words[first:first + 3]]
        f = self.f
        while f.getlength(" ".join(chunk)) > W * 0.8: f = font(f.size - 4)
        x, dr = W / 2 - f.getlength(" ".join(chunk)) / 2, ImageDraw.Draw(fr)
        for j, w in enumerate(chunk):
            dr.text((x, H * 0.76 - 60), w, font=f, fill="#FFE14D" if first + j == cur else "white", anchor="lm", stroke_width=9, stroke_fill="black")
            x += f.getlength(w + " ")

def music(d, prompt):
    m = d / "music.mp3"
    if not m.exists():
        print("🎵 music...")
        m.write_bytes(data(gemini("lyria-3-clip-preview", [{"text": f"Instrumental only, no vocals. {prompt}"}], responseModalities=["AUDIO"])))
    return m

def render(d, total, frame, hits, ps):
    """frame(t) → RGB image; hits = [(time, sfx)]; mixes voice, music and SFX, then packshot + CTA from ps."""
    hits = [(st, k) for st, k in hits if k in SFX]
    sfx_in = sum((["-f", "lavfi", "-i", SFX[k]] for _, k in hits), [])
    sfx_mix = "".join(f"[{3 + j}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={round(st * 1000)}:all=1[s{j}];" for j, (st, _) in enumerate(hits))
    print(f"🎞️  {total:.1f}s · {round(total * FPS)} frames...")
    cut = d / "cut.mp4"
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", d / "vo.raw", "-i", d / "music.mp3", *sfx_in, "-filter_complex",
                           f"[1:a]loudnorm=I=-16:TP=-1.5,aresample=48000,aformat=channel_layouts=stereo[vo];"  # tracks and TTS voices differ by up to 20 LU: level both
                           f"[2:a]loudnorm=I=-16,aresample=48000,aformat=channel_layouts=stereo,volume=0.2,"
                           f"atrim=0:{total},afade=t=out:st={total - 1}:d=1[m];{sfx_mix}"
                           f"[vo][m]{''.join(f'[s{j}]' for j in range(len(hits)))}amix=inputs={2 + len(hits)}:normalize=0,alimiter=limit=0.9[a]",
                           "-map", "0:v", "-map", "[a]", "-t", f"{total:.3f}", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "18", "-c:a", "aac", "-b:a", "192k", cut],
                          stdin=subprocess.PIPE)
    for k in range(round(total * FPS)):
        ff.stdin.write(frame(k / FPS).tobytes())
        if k % FPS == 0: print(f"\r   {k / FPS:.0f}/{total:.0f}s", end="", flush=True)
    ff.stdin.close(); ff.wait(); print()
    subprocess.run([HERE.parent / "3d/packshot.sh", cut, f"{ps:.2f}"], check=True)
    im = Image.new("RGBA", (W, H))
    f = font(130)
    while f.getlength("YOUR HEIGHT") > W * 0.8: f = font(f.size - 2)
    ImageDraw.Draw(im).multiline_text((W / 2, H * 0.615), CTA, font=f, fill="white", anchor="ma", align="center", spacing=10, stroke_width=9, stroke_fill="black")
    im.save(d / "cta.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", d / "cut_final.mp4", "-i", d / "cta.png", "-filter_complex",
                    f"[0][1]overlay=enable='gte(t,{ps + 0.25:.2f})'", "-c:v", "libx264", "-crf", "18", "-c:a", "copy", d / "final.mp4"], check=True)
    (d / "cut_final.mp4").unlink()
    print(f"🏁 {d / 'final.mp4'}\n💰 Google (Gemini/Lyria) ~${api.spent:.3f} · OpenAI (images/TTS) ~${oai.spent:.3f} · total ~${api.spent + oai.spent:.3f}")
