# /// script
# dependencies = ["pillow"]
# ///
"""UGC reaction + app reveal (rule C-UGC-1, ref: GoTall UGC 674K): ~2.5 s of the channel face reacting in disbelief with a ≤4-word hook,
then the real TallPlan screen recording from 04_assets held up on a blurred backdrop with a slight hand shake, ref sound, no voice, packshot.
The reaction clip is a 360p Omni generation (ugc/<x>/react.txt); the low resolution + grain is the amateur phone look.

  uv run ugc.py <work>/spec.json   -> <work>/final.mp4
"""
import json, pathlib, subprocess, sys
from PIL import Image, ImageDraw
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "slides"))
from kit import W, H, MUSIC, font
from assemble import packshot

ASSETS = MUSIC.parent.parent / "04_assets/Screenshots/iOS/promo"
spec_f = pathlib.Path(sys.argv[1]).resolve()
spec, d = json.loads(spec_f.read_text()), spec_f.parent
r, v = spec["react"], spec["reveal"]
PS = r["dur"] + v["dur"]  # packshot starts when the reveal ends

# hook above the face (G01 ≤4 words, G20: below 270 px, ≤80% width)
hook = Image.new("RGBA", (W, H))
ImageDraw.Draw(hook).multiline_text((W / 2, 420), spec["hook"], font=font(92, 800), fill="white", anchor="mm", align="center",
                                    spacing=12, stroke_width=8, stroke_fill="black")
hook.save(d / "hook.png")

cut = str(d / "cut.mp4")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(r["ss"]), "-t", str(r["dur"]), "-i", d / r["file"],
                "-ss", str(v["ss"]), "-t", str(v["dur"]), "-i", ASSETS / v["file"], "-loop", "1", "-i", d / "hook.png",
                "-stream_loop", "-1", "-i", MUSIC / spec["music"],
                "-filter_complex", f"[0]scale={W}:{H},setsar=1,fps=30[r];[r][2]overlay=shortest=1[a];"
                f"[1]fps=30,split[s1][s2];[s1]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=40,eq=brightness=-0.2[bg];"
                f"[s2]scale=-2:{int(H * 0.9)}[ph];[bg][ph]overlay=x='(W-w)/2+6*sin(2.1*t)':y='(H-h)/2+8*sin(1.7*t)',setsar=1[b];"
                f"[a][b]concat=n=2:v=1:a=0,tpad=stop_mode=clone:stop_duration=1.8,noise=alls=9:allf=t,format=yuv420p[v];"
                f"[3:a]afade=t=out:st={PS + 1.2:.2f}:d=0.6,loudnorm=I=-12:TP=-1,aresample=48000[au]",
                "-map", "[v]", "-map", "[au]", "-t", f"{PS + 1.8:.2f}", "-c:v", "libx264", "-crf", "18", "-c:a", "aac", "-b:a", "192k", cut],
               check=True)
packshot(cut, PS, str(d / "final.mp4"))
print(f"✅ {d / 'final.mp4'} · {PS + 1.8:.1f}s")
