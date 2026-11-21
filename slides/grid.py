# /// script
# dependencies = ["pillow"]
# ///
"""2x2 photo-grid slideshow: per slide a title and 4 labeled photos (OpenAI), cut on the beat of Lyria music, packshot.
Usage: uv run grid.py grid/<spec>.json  (outputs next to the spec in a folder of its name; idempotent)
"""
import json, pathlib, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "3d"))
import api, oai
from api import gemini, data

W, H = 1080, 1920
BEATS, PACKSHOT = 8, 2.2
GX, GY, GAP = 24, int(H * 0.255), 12  # grid stays clear of the right-side UI icons and the bottom description
TILE = (W - 150 - GX - GAP) // 2
FONT = HERE.parent / "3d/fonts/Montserrat.ttf"
CTA = "GET YOUR\nPERSONAL ROUTINE"

spec_f = pathlib.Path(sys.argv[1]).resolve()
spec, d = json.loads(spec_f.read_text()), spec_f.with_suffix("")
d.mkdir(exist_ok=True)

def font(size):
    f = ImageFont.truetype(str(FONT), size); f.set_variation_by_axes([900]); return f

def fit(text, size, width):
    while max(font(size).getlength(l) for l in text.split("\n")) > width: size -= 2
    return font(size)

def text(dr, xy, s, size, width, anchor="ma", fill="white"):
    f = fit(s, size, width)
    dr.multiline_text(xy, s, font=f, fill=fill, anchor=anchor, align="center", spacing=8, stroke_width=round(f.size * 0.09), stroke_fill="black")

def slide(i, s, out, title=True):
    im = Image.new("RGB", (W, H), spec["bg"])
    dr = ImageDraw.Draw(im)
    for j, (label, _) in enumerate(s["tiles"]):
        x, y = GX + j % 2 * (TILE + GAP), GY + j // 2 * (TILE + GAP)
        im.paste(Image.open(d / f"t{i}_{j}.png").convert("RGB").resize((TILE, TILE), Image.LANCZOS), (x, y))
        text(dr, (x + TILE / 2, y + TILE - 24), label.upper(), 44, TILE * 0.9, anchor="md")
    if title: text(dr, (W / 2, 280), s["title"], 92, W * 0.8)
    im.save(out)

frames = []
for i, s in enumerate(spec["slides"]):
    for j, (label, prompt) in enumerate(s["tiles"]):
        t = d / f"t{i}_{j}.png"
        if not t.exists():
            print(f"🖼️  slide {i + 1} tile {j + 1}: {label}...")
            oai.image(f"{spec['style']} {prompt} Absolutely no text, letters or numbers.", t, quality="low", size="1024x1024")
    slide(i, s, d / f"frame{i}.png")
    frames.append(d / f"frame{i}.png")
slide(len(spec["slides"]) - 1, spec["slides"][-1], d / "clean.png", title=False)  # under the packshot: no old captions

music = d / "music.mp3"
if not music.exists():
    print("🎵 music...")
    music.write_bytes(data(gemini("lyria-3-clip-preview", [{"text": f"Instrumental only, no vocals. {spec['music']}"}], responseModalities=["AUDIO"])))

bpm = int(re.search(r"(\d{2,3})\s*BPM", spec["music"]).group(1))
dur = [BEATS * 60 / bpm] * len(frames) + [PACKSHOT]
frames.append(d / "clean.png")
total = sum(dur)
(d / "frames.txt").write_text("".join(f"file '{f}'\nduration {t:.3f}\n" for f, t in zip(frames, dur)) + f"file '{frames[-1]}'\n")
print(f"🎞️  {len(frames)} slides · {bpm} BPM · {total:.1f}s")
cut = d / "cut.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", d / "frames.txt", "-i", music, "-filter_complex",
                f"[0:v]fps=30,format=yuv420p[v];[1:a]atrim=0:{total},afade=t=out:st={total - 1}:d=1,aresample=48000,aformat=channel_layouts=stereo[a]",
                "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}", "-c:v", "libx264", "-crf", "18", "-c:a", "aac", "-b:a", "192k", cut], check=True)
subprocess.run([HERE.parent / "3d/packshot.sh", cut, f"{total - PACKSHOT:.2f}"], check=True)
im = Image.new("RGBA", (W, H))
ImageDraw.Draw(im).multiline_text((W / 2, H * 0.615), CTA, font=fit("PERSONAL ROUTINE", 130, W * 0.8), fill="white", anchor="ma", align="center", spacing=10, stroke_width=9, stroke_fill="black")
im.save(d / "cta.png")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", d / "cut_final.mp4", "-i", d / "cta.png", "-filter_complex",
                f"[0][1]overlay=enable='gte(t,{total - PACKSHOT + 0.25:.2f})'", "-c:v", "libx264", "-crf", "18", "-c:a", "copy", d / "final.mp4"], check=True)
(d / "cut_final.mp4").unlink()
print(f"🏁 {d / 'final.mp4'}\n💰 Google (Lyria) ~${api.spent:.3f} · OpenAI (images) ~${oai.spent:.3f} · total ~${api.spent + oai.spent:.3f}")
