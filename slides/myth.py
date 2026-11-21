# /// script
# dependencies = ["pillow"]
# ///
"""Myth → fact ad: two static slides, each with its own music (hard cut), then the packshot.
Usage: uv run myth.py <reference_url> <folder> "<art style>" ["<brief>"] ["<xfade transition, e.g. pixelize>"]  (idempotent: delete a file to redo it)
"""
import json, pathlib, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "3d"))
import api, oai
from api import gemini, data, file

W, H = 1080, 1920
PACKSHOT = 2.2
FONT = HERE.parent / "3d/fonts/Montserrat.ttf"
CTA = "GET YOUR\nPERSONAL ROUTINE"

url, d, style = sys.argv[1], (HERE / sys.argv[2]).resolve(), sys.argv[3]
brief = sys.argv[4] if len(sys.argv) > 4 else "none, follow the reference"
TRANS, XD = (sys.argv[5] if len(sys.argv) > 5 else "fade"), 0.35  # ffmpeg xfade type and its seconds
d.mkdir(parents=True, exist_ok=True)
ref = d / "reference.mp4"
if not ref.exists():
    print("⬇️  downloading reference...")
    subprocess.run(["yt-dlp", "-q", "--no-warnings", "--remux-video", "mp4", "-o", str(d / "reference.%(ext)s"), url], check=True)

plan_f = d / "plan.json"
if not plan_f.exists():
    print("🧭 planning...")
    plan_f.write_text(gemini("gemini-3.8-flash", [file(ref), {"text": (HERE / "myth.txt").read_text().replace("{style}", style).replace("{brief}", brief)}],
                             responseMimeType="application/json")[0]["text"])
plan = json.loads(plan_f.read_text())
print(f"📋 {plan['title']}")

def fit(text, size):
    """Largest Montserrat Black up to size that fits 80% of the frame width (right-side UI icons)."""
    while True:
        f = ImageFont.truetype(str(FONT), size); f.set_variation_by_axes([900])
        if f.getlength(text) <= W * 0.8: return f
        size -= 2

def frame(src, s, out):
    src = Image.open(src).convert("RGB").resize((W, W * 3 // 2), Image.LANCZOS)
    im = Image.new("RGB", (W, H), src.getpixel((4, 4)))
    im.paste(src, (0, H - src.height))
    im.save(out.with_name(out.stem + "_clean.png"))  # shown under the packshot without captions
    dr = ImageDraw.Draw(im)
    head, _, rest = s["caption"].partition(":")  # "MYTH" / "FACT" on its own line, bigger
    words = rest.split()  # claim in two lines so it stays large
    lines = [(head + ":", 120, 130), (" ".join(words[:(len(words) + 1) // 2]), 76, 85), (" ".join(words[(len(words) + 1) // 2:]), 76, 95), (s["sub"].upper(), 42, 70)]
    y = H * 0.14  # below the top UI safe zone (~250 px)
    for text, size, step in lines:
        f = fit(text, size)
        dr.text((W / 2, y), text, font=f, fill=plan["ink"], anchor="mm", stroke_width=round(f.size * 0.08), stroke_fill=plan["outline"])
        y += step
    im.save(out)

parts = []
for k in ("myth", "fact"):
    s, raw, fr, mus = plan[k], d / f"{k}.png", d / f"{k}_frame.png", d / f"{k}.mp3"
    if not raw.exists():
        print(f"🖼️  {k}...")
        oai.image(f"{plan['style']} Character: {plan['character']}. {s['prompt']} Absolutely no text, letters or numbers.", raw)
    if not mus.exists():
        print(f"🎵 {k} music...")
        mus.write_bytes(data(gemini("lyria-3-clip-preview", [{"text": f"Instrumental only, no vocals. {s['music']}"}], responseModalities=["AUDIO"])))
    frame(raw, s, fr)
    t = s["dur"] + (PACKSHOT if k == "fact" else 0)
    out = d / f"{k}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", "30", "-i", fr, "-loop", "1", "-framerate", "30", "-i", fr.with_name(fr.stem + "_clean.png"), "-i", mus, "-filter_complex",
                    f"[0][1]overlay=enable='gte(t,{s['dur']})',format=yuv420p[v];[2:a]atrim=0:{t},afade=t=out:st={t - 0.6}:d=0.6[a]", "-map", "[v]", "-map", "[a]",
                    "-t", f"{t:.3f}", "-c:v", "libx264", "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", out], check=True)
    parts.append(out)

total = plan["myth"]["dur"] + plan["fact"]["dur"] + PACKSHOT - XD
cut = d / "cut.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", parts[0], "-i", parts[1], "-filter_complex", f"[0:v][1:v]xfade=transition={TRANS}:duration={XD}:offset={plan['myth']['dur'] - XD}[v];[0:a][1:a]acrossfade=d={XD}[a]",
                "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "18", "-c:a", "aac", "-b:a", "192k", cut], check=True)
print(f"🎞️  myth {plan['myth']['dur']}s → fact {plan['fact']['dur']}s · {total:.1f}s")
subprocess.run([HERE.parent / "3d/packshot.sh", cut, f"{total - PACKSHOT:.2f}"], check=True)
cta = d / "cta.png"
im = Image.new("RGBA", (W, H))
ImageDraw.Draw(im).multiline_text((W / 2, H * 0.615), CTA, font=fit("PERSONAL ROUTINE", 130), fill="white", anchor="ma", align="center", spacing=10, stroke_width=9, stroke_fill="black")
im.save(cta)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", d / "cut_final.mp4", "-i", cta, "-filter_complex",
                f"[0][1]overlay=enable='gte(t,{total - PACKSHOT + 0.25:.2f})'", "-c:v", "libx264", "-crf", "18", "-c:a", "copy", d / "final.mp4"], check=True)
(d / "cut_final.mp4").unlink()
print(f"🏁 {d / 'final.mp4'}\n💰 Google (Gemini/Lyria) ~${api.spent:.3f} · OpenAI (images/TTS) ~${oai.spent:.3f} · total ~${api.spent + oai.spent:.3f}")
