# /// script
# dependencies = ["pillow"]
# ///
"""Selfie + height table (refs @heightible, @gotall.abdul, rules C-SELF): a still front-camera selfie with a slow push-in, one age per video,
a white-on-black-outline table "if you're N and X → ~Y at 18" above the eyes from frame 1, a loud ref sound, no voice; the TallPlan card
for the middle row slides up for the last 2 s, then packshot. ≤12 s. Remix: the selfie comes from earlier generations, nothing paid.

  uv run selfie.py <work>/spec.json   -> <work>/final.mp4   (<work>/photo.png = the selfie)
"""
import json, pathlib, subprocess, sys
from PIL import Image, ImageDraw
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "slides"))
from kit import W, H, MUSIC, PCT, font, ftin, tallcard
from assemble import packshot

APP, PS = 7.5, 9.6  # card slides up at APP, packshot from PS (C-SELF-1: ≤12 s in all)
spec_f = pathlib.Path(sys.argv[1]).resolve()
spec, d = json.loads(spec_f.read_text()), spec_f.parent
age, rows = spec["age"], spec["rows"]
at18 = [round(i * 100 / PCT[age]) for i in rows]  # same share-of-adult-height curve as path/ (CDC boys' medians)

# 1) the table above the face (G02: readable in the first second, G20: inside 270 px .. 0.76 H, ≤80% width)
lines = [f"If you're {age} and:"] + [f"{ftin(a)} → ~{ftin(b)} at 18" for a, b in zip(rows, at18)]
ov = Image.new("RGBA", (W, H))
dr = ImageDraw.Draw(ov)
for k, l in enumerate(lines):
    dr.text((W / 2, 340 + 100 * k), l, font=font(76 if k else 70, 800), fill="white", anchor="mm", stroke_width=7, stroke_fill="black")
dr.text((W / 2, 730), "estimate · genes set the range", font=font(38, 700), fill="white", anchor="mm", stroke_width=5, stroke_fill="black")
ov.save(d / "table.png")
mid = len(rows) // 2
tallcard(d / "app.png", at18[mid], rows[mid])

# 2) video: selfie with a slow push-in + table, the card slides up, the ref sound loud from 0 s
cut = str(d / "cut.mp4")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", "30", "-t", f"{PS + 1.8:.2f}", "-i", d / "photo.png",
                "-loop", "1", "-framerate", "30", "-i", d / "table.png", "-loop", "1", "-framerate", "30", "-i", d / "app.png",
                "-ss", str(spec.get("music_start", 0)), "-i", MUSIC / spec["music"],
                "-filter_complex", f"[0]scale=-2:{H},crop={W}:{H},scale=w='{W}*(1+0.05*t/{PS})':h=-2:eval=frame,crop={W}:{H}[bg];"
                f"[bg][1]overlay=shortest=1[s];[s][2]overlay=x=(W-w)/2:y='560+1400*(1-clip((t-{APP})/0.35,0,1))':enable='gte(t,{APP})',"
                f"fade=t=out:st={PS - 0.4:.2f}:d=0.4,format=yuv420p[v];[3:a]afade=t=out:st={PS + 1.2:.2f}:d=0.6,loudnorm=I=-12:TP=-1,aresample=48000[a]",
                "-map", "[v]", "-map", "[a]", "-t", f"{PS + 1.8:.2f}", "-c:v", "libx264", "-crf", "18", "-c:a", "aac", "-b:a", "192k", cut], check=True)
packshot(cut, PS, str(d / "final.mp4"))
print(f"✅ {d / 'final.mp4'} · {PS + 1.8:.1f}s · 💰 $0 (remix)")
