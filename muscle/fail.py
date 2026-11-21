# /// script
# dependencies = ["pillow"]
# ///
"""Fail opener for a muscle reel: the mannequin does a silly made-up "growth exercise" (silly music, hook caption),
then a freeze with shattered glass, flash, shake and "YOU'RE DOING IT WRONG!!!"; prepended to the reel's final.mp4.
Usage: uv run fail.py <work>/reel.json  (after gen.py, render_overlay.py, assemble.py; reads the "fail" block)
"""
import json, math, pathlib, random, subprocess, sys, wave
from PIL import Image, ImageDraw, ImageFont
HERE = pathlib.Path(__file__).parent
sys.path[:0] = [str(HERE.parent / "slides"), str(HERE.parent / "3d")]
import api, oai
from api import gemini, data

W, H, FPS = 1080, 1920, 30
cfg_f = pathlib.Path(sys.argv[1]).resolve()
cfg, d = json.loads(cfg_f.read_text()), cfg_f.parent
f = cfg["fail"]
STYLE = (HERE / "style.txt").read_text().strip()

def run(*a): subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, a)], check=True)

def font(size):
    ft = ImageFont.truetype(str(HERE.parent / "3d/fonts/Montserrat.ttf"), size); ft.set_variation_by_axes([900]); return ft

# assets
still, clip, music = d / "stills/fail.png", d / "clips/fail.mp4", d / "vo/music_fail.mp3"
if not still.exists():
    print("🖼️  fail still...")
    oai.edit(f"{STYLE}\nInstead of a glowing muscle, the strained body part glows alarm red. SHOT: {f['shot']}",
             [HERE / "assets/style_ref_full.png", HERE / "assets/style_ref_close.png"], still, size="1024x1536")
if not clip.exists():
    p = d / "clips/fail.txt"
    p.write_text(f"Comedic: the grey faceless mannequin clumsily and very seriously attempts {f['move']}, wobbling, overdoing it, clearly doing it wrong. "
                 "The strained body part glows alarm red. Dark charcoal studio, same mannequin, lighting and colors as the start frame. "
                 f"At least {f['dur'] + 0.5:.0f} seconds long. No text, no logos, no extra people, no cuts.")
    subprocess.run([sys.executable, HERE.parent / "3d/omni.py", p, clip, "--image", still, "--res", cfg["res"]], check=True)
lines = {}
for k in ("hook", "wrong"):
    out = d / f"vo/fail_{k}.wav"
    if not out.exists():
        print(f"🎙️  {k}...")
        with wave.open(str(out), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000)
            w.writeframes(oai.speech(f[k], f["voice"], cfg["openai_voice"], cfg["speed"]))
    with wave.open(str(out)) as w: lines[k] = (out, w.getnframes() / w.getframerate())
if not music.exists():
    print("🎵 silly music...")
    music.write_bytes(data(gemini("lyria-3-clip-preview", [{"text": f"Instrumental only, no vocals. {f['music']}"}], responseModalities=["AUDIO"])))

# timeline: silly clip, then the freeze for as long as the "wrong" line lasts
T0 = f["dur"]
freeze = max(1.6, lines["wrong"][1] + 0.3)
total = T0 + freeze
random.seed(7)
cx, cy = W / 2, H * 0.47
cracks = []  # jagged radial lines from the impact point + a few ring chips between them
for k in range(16):
    a, r, pts = k / 16 * 2 * math.pi + random.uniform(-0.15, 0.15), 0, [(cx, cy)]
    while r < 1500:
        r += random.uniform(60, 160); a += random.uniform(-0.2, 0.2)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    cracks.append(pts)
rings = [[(cx + r * math.cos(a), cy + r * math.sin(a)) for a in (k / 16 * 2 * math.pi + random.uniform(-0.1, 0.1), (k + 1) / 16 * 2 * math.pi)]
         for r in (120, 260, 430) for k in range(16) if random.random() < 0.6]
glass = Image.new("RGBA", (W, H))
g = ImageDraw.Draw(glass)
for pts in cracks + rings: g.line(pts, fill=(0, 0, 0, 140), width=9, joint="curve")
for pts in cracks + rings: g.line(pts, fill=(255, 255, 255, 235), width=3, joint="curve")
g.ellipse((cx - 40, cy - 40, cx + 40, cy + 40), fill=(255, 255, 255, 200))
title = Image.new("RGBA", (W, H))
ft = font(140)
while ft.getlength("DOING IT WRONG!!!") > W * 0.84: ft = font(ft.size - 4)
ImageDraw.Draw(title).multiline_text((W / 2, 300), "YOU'RE\nDOING IT WRONG!!!", font=ft, fill="#FF3B3B", anchor="ma", align="center", spacing=12, stroke_width=12, stroke_fill="white")
hook = Image.new("RGBA", (W, H))
fh = font(80)
while max(fh.getlength(l) for l in f["caption"].split("\n")) > W * 0.8: fh = font(fh.size - 4)
ImageDraw.Draw(hook).multiline_text((W / 2, 300), f["caption"], font=fh, fill="white", anchor="ma", align="center", spacing=10, stroke_width=9, stroke_fill="black")

src = d / "build/fail_src.mp4"
src.parent.mkdir(exist_ok=True)
run("-i", clip, "-vf", f"scale={W}:{H}:flags=lanczos,fps={FPS}", "-frames:v", round(T0 * FPS), "-an", "-c:v", "libx264", "-crf", 15, src)
frames = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
n_src = len(frames) // (W * H * 3)
vid = d / "build/fail_v.mp4"
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", vid], stdin=subprocess.PIPE)
for n in range(round(total * FPS)):
    t = n / FPS
    im = Image.frombytes("RGB", (W, H), frames[min(n, n_src - 1) * W * H * 3:(min(n, n_src - 1) + 1) * W * H * 3]).convert("RGBA")
    if t < T0:
        im.alpha_composite(hook)
    else:
        u = t - T0
        im = Image.blend(im, Image.new("RGBA", (W, H), (200, 20, 30, 255)), 0.25)  # red alarm tint on the frozen frame
        k = min(1, u / 0.12)
        gl = glass if k >= 1 else glass.crop((cx - W * k, cy - H * k, cx + W * k, cy + H * k)).resize((round(2 * W * k) or 1, round(2 * H * k) or 1))
        im.alpha_composite(gl, (0, 0) if k >= 1 else (round(cx - W * k), round(cy - H * k)))
        im.alpha_composite(title)
        if u < 0.25: im = Image.blend(im, Image.new("RGBA", (W, H), "white"), 0.8 * (1 - u / 0.25))  # impact flash
        s = 30 * math.exp(-u * 6)  # decaying shake
        im = im.transform((W, H), Image.AFFINE, (1, 0, s * math.sin(u * 70), 0, 1, s * math.cos(u * 55)), Image.BILINEAR)
    ff.stdin.write(im.convert("RGB").tobytes())
ff.stdin.close(); ff.wait()

# audio: silly music under the hook line, then glass shatter + record scratch + the "wrong" line; silence cut before the reel
shatter = "anoisesrc=d=0.9:color=white:a=0.9,highpass=f=2500,afade=t=out:st=0.05:d=0.85"
scratch = "aevalsrc='0.6*sin(2*PI*(900*exp(-6*t))*t*8)*exp(-3*t)':d=0.5"
fc = (f"[1:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{T0:.3f},afade=t=out:st={T0 - 0.15:.3f}:d=0.15,volume=0.3,apad[m];"
      f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay=300:all=1,apad[h];"
      f"[3:a]aresample=48000,aformat=channel_layouts=stereo,adelay={round((T0 + 0.25) * 1000)}:all=1,apad[w];"
      f"[4:a]aresample=48000,aformat=channel_layouts=stereo,adelay={round(T0 * 1000)}:all=1,apad[s1];"
      f"[5:a]aresample=48000,aformat=channel_layouts=stereo,adelay={round(T0 * 1000)}:all=1,apad[s2];"
      f"[m][h][w][s1][s2]amix=inputs=5:normalize=0,atrim=0:{total:.3f},loudnorm=I=-14:TP=-1.5[a]")
pre = d / "build/fail.mp4"
run("-i", vid, "-i", music, "-i", lines["hook"][0], "-i", lines["wrong"][0], "-f", "lavfi", "-i", shatter, "-f", "lavfi", "-i", scratch,
    "-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-t", f"{total:.3f}", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", 48000, pre)
out = d / cfg["fail_out"]
run("-i", pre, "-i", d / cfg["out"], "-filter_complex", "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]", "-map", "[v]", "-map", "[a]",
    "-c:v", "libx264", "-crf", 18, "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out)
print(f"🏁 {out}\n💰 Google (Lyria; omni above) ~${api.spent:.3f} · OpenAI (image/TTS) ~${oai.spent:.3f}")
