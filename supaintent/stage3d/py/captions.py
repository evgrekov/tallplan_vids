# /// script
# dependencies = ["pillow"]
# ///
"""Burn TikTok karaoke captions (reference style) into a video.
Usage: uv run captions.py <video.mp4> <words.json> [out.mp4]
words.json: [{"w": "word", "s": start, "e": end}, ...] (from align.py)
"""
import json, pathlib, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFilter, ImageFont

YELLOW, WHITE, BLACK = (77, 141, 255), (255, 255, 255), (0, 0, 0)
FONT = pathlib.Path(__file__).parent.parent / "assets/fonts/Display.ttf"
MAX_WORDS, MAX_CHARS = 3, 16

video, words_path = sys.argv[1], sys.argv[2]
out = sys.argv[3] if len(sys.argv) > 3 else video.replace(".mp4", "_cap.mp4")
words = json.load(open(words_path))
W, H = map(int, subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                         "stream=width,height", "-of", "csv=p=0", video], text=True).strip().strip(",").split(",")[:2])

# 2-3 words per chunk, break after punctuation or when the line gets long
chunks, cur = [], []
for w in words:
    if cur and (len(cur) == MAX_WORDS or len(" ".join(x["w"] for x in cur + [w])) > MAX_CHARS):
        chunks.append(cur); cur = []
    cur.append(w)
    if w["w"][-1] in ",.?!":
        chunks.append(cur); cur = []
chunks += [cur] if cur else []

def make_font(size):
    f = ImageFont.truetype(str(FONT), size)
    try: f.set_variation_by_axes([900])  # Black
    except OSError: pass  # static font
    return f

stroke, shadow = max(2, round(H * 0.006)), round(H * 0.004)
y = int(H * 0.555)  # empty band between the data panel and the characters' heads
POP = [(0.92, 0.04), (0.96, 0.04)]  # chunk entry: scale 92%→100% over 0.08s

def render(chunk, active, scale=1.0):
    labels = [x["w"].upper().strip(",.") for x in chunk]
    size = int(H * 0.05)  # shrink until the line fits 90% of width
    while (font := make_font(size)).getlength(" ".join(labels)) + 2 * stroke > W * 0.9:
        size -= 1
    font = make_font(round(size * scale))
    space = font.getlength(" ")
    widths = [font.getlength(t) for t in labels]
    x = (W - sum(widths) - space * (len(labels) - 1)) / 2
    img = Image.new("RGBA", (W, H))
    shade = Image.new("RGBA", (W, H))
    d, ds = ImageDraw.Draw(img), ImageDraw.Draw(shade)
    for i, (t, tw) in enumerate(zip(labels, widths)):
        ds.text((x, y + shadow), t, font=font, fill=(0, 0, 0, 190), stroke_width=stroke, stroke_fill=(0, 0, 0, 190), anchor="lm")
        d.text((x, y), t, font=font, fill=YELLOW if i == active else WHITE, stroke_width=stroke, stroke_fill=BLACK, anchor="lm")
        x += tw + space
    return Image.alpha_composite(shade.filter(ImageFilter.GaussianBlur(shadow)), img)

print(f"🔤 {len(words)} words → {len(chunks)} chunks")
tmp = pathlib.Path(tempfile.mkdtemp())
inputs, overlays, n = [], [], 0
flat = [w for c in chunks for w in c]
for ci, chunk in enumerate(chunks):
    for wi, w in enumerate(chunk):
        idx = flat.index(w)
        end = flat[idx + 1]["s"] if idx + 1 < len(flat) else w["e"] + 0.5
        s = w["s"]
        for scale, dur in (POP if wi == 0 else []) + [(1.0, None)]:
            e = end if dur is None else min(s + dur, end)
            if e <= s: continue
            p = tmp / f"{n:03d}.png"; render(chunk, wi, scale).save(p)
            inputs += ["-i", str(p)]
            overlays.append((n + 1, s, e)); n += 1; s = e

graph, last = [], "0:v"
for i, (inp, s, e) in enumerate(overlays):
    graph.append(f"[{last}][{inp}:v]overlay=enable='between(t,{s},{e - 0.001})'[v{i}]"); last = f"v{i}"
print(f"🎞️  burning {n} caption states...")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, *inputs, "-filter_complex", ";".join(graph),
                "-map", f"[{last}]", "-map", "0:a?", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "copy", out], check=True)
print(f"✅ {out}")
