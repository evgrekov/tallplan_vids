# /// script
# dependencies = ["pillow"]
# ///
"""Reveal table (ref @todd.f.moir): a plain worksheet, a paper strip covers the answer column and slides down one row per voice line,
last row "You ??" asks for a comment, the tagline shows the real TallPlan prediction screen as the answer, then packshot + CTA.
No video generation: only TTS (~$0.01).

  uv run table.py <work>/spec.json   -> <work>/final.mp4   (idempotent: delete a wav to redo that line)
"""
import json, pathlib, subprocess, sys, wave
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = pathlib.Path(__file__).parent
sys.path[:0] = [str(HERE.parent / "slides"), str(HERE.parent / "muscle")]
import oai
from assemble import packshot

W, H, TOP, BOTTOM, X0, XM, X1 = 1080, 1920, 470, 1450, 110, 390, 970  # table stays inside the TikTok safe zone
APP_SCREEN = HERE.parent / "TallPlan 13:11/Screenshots/iOS/promo/ft/01-home.png"
spec_f = pathlib.Path(sys.argv[1]).resolve()
spec, d = json.loads(spec_f.read_text()), spec_f.parent
(d / "vo").mkdir(exist_ok=True)

def font(size, wght=800):
    f = ImageFont.truetype(str(HERE.parent / "3d/fonts/Montserrat.ttf"), size); f.set_variation_by_axes([wght]); return f

def say(name, text):
    out = d / f"vo/{name}.wav"
    if not out.exists():
        print(f"🎙️  {name}: {text}")
        with wave.open(str(out), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000)
            w.writeframes(oai.speech(text, spec["voice"], spec["openai_voice"], spec.get("speed", 1.0)))
    with wave.open(str(out)) as w: return out, w.getnframes() / w.getframerate()

# 1) voice lines back to back: intro, one per row (the row opens on its line), outro on the "You ??" row,
#    tagline = the answer to "??": the real TallPlan prediction screen slides up over the table, then the packshot
rows = spec["rows"] + [{"age": "YOU", "value": "??", "say": spec["outro"]}]
lines = [say("intro", spec["intro"])] + [say(f"r{i:02d}", r["say"]) for i, r in enumerate(rows)] + [say("tagline", spec["tagline"])]
t, cues = 0.2, []
for f, dur in lines: cues.append((f, t)); t += dur + 0.15
app = cues[-1][1]
ps = t + 0.5
T = ps + 1.8
opens = [c[1] for c in cues[1:-1]]

# 2) worksheet with every answer + the paper strip that hides them
rh = (BOTTOM - TOP) / (len(rows) + 1)
im = Image.new("RGB", (W, H), "#FBFAF6")
dr = ImageDraw.Draw(im)
dr.text((W / 2, 300), spec["title"], font=font(84, 900), fill="#111", anchor="mm")
dr.text((W / 2, 385), spec["subtitle"], font=font(48, 600), fill="#555", anchor="mm")
for i in range(len(rows) + 2): dr.line((X0, TOP + i * rh, X1, TOP + i * rh), fill="#222", width=4)
for x in (X0, XM, X1): dr.line((x, TOP, x, BOTTOM), fill="#222", width=4)
for i, (a, b) in enumerate([spec["header"]] + [(r["age"], r["value"]) for r in rows]):
    y, f = TOP + (i + 0.5) * rh, font(46 if i == 0 else 54, 900 if i == 0 else 700)
    red = "#D62828" if i == len(rows) else "#111"
    dr.text(((X0 + XM) / 2, y), str(a), font=f, fill=red, anchor="mm")
    dr.text(((XM + X1) / 2, y), str(b), font=f, fill=red, anchor="mm")
im.save(d / "sheet.png")
cw, ch = X1 - XM - 4, int(BOTTOM - TOP - rh) + 80
cover = Image.new("RGBA", (cw + 40, ch + 40))
ImageDraw.Draw(cover).rectangle((14, 22, cw + 14, ch + 22), fill=(0, 0, 0, 90))
cover = cover.filter(ImageFilter.GaussianBlur(8))
ImageDraw.Draw(cover).rectangle((10, 10, cw + 10, ch + 10), fill="#E9DCB8")
cover.save(d / "cover.png")
shot = Image.open(APP_SCREEN).convert("RGB").crop((40, 370, 1280, 1200)).resize((900, 602), Image.LANCZOS)  # "As an adult 6'3"" card
mask = Image.new("L", shot.size); ImageDraw.Draw(mask).rounded_rectangle((0, 0, *shot.size), 44, fill=255)
card = Image.new("RGBA", (shot.width + 60, shot.height + 60))
ImageDraw.Draw(card).rounded_rectangle((30, 42, shot.width + 30, shot.height + 42), 44, fill=(0, 0, 0, 120))
card = card.filter(ImageFilter.GaussianBlur(14)); card.paste(shot, (30, 30), mask)
card.save(d / "app.png")

# 3) video: the strip slides one row down (0.25 s ease) on each row's line; audio: lines placed on the timeline
y = f"{TOP + rh + 2 - 10}+{rh:.2f}*(" + "+".join(f"clip((t-{o:.2f})/0.25,0,1)" for o in opens) + ")"
mix = ";".join(f"[{i + 3}:a]adelay={int(s * 1000)}|{int(s * 1000)},apad[a{i}]" for i, (_, s) in enumerate(cues))
mix += ";" + "".join(f"[a{i}]" for i in range(len(cues))) + f"amix=inputs={len(cues)}:normalize=0,atrim=0:{T:.2f},loudnorm=I=-14:TP=-1.5,aresample=48000[aout]"
cut = str(d / "cut.mp4")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", "30", "-t", f"{T:.2f}", "-i", d / "sheet.png", "-loop", "1", "-framerate", "30", "-i", d / "cover.png",
                "-loop", "1", "-framerate", "30", "-i", d / "app.png", *[x for f, _ in cues for x in ("-i", f)],
                "-filter_complex", f"[0][1]overlay=x={XM + 2 - 10}:y='{y}':shortest=1[s];"
                f"[s][2]overlay=x=(W-w)/2:y='640+1400*(1-clip((t-{app:.2f})/0.35,0,1))':enable='gte(t,{app:.2f})':shortest=1,fade=t=out:st={ps - 0.5:.2f}:d=0.5,format=yuv420p[v];{mix}",
                "-map", "[v]", "-map", "[aout]", "-t", f"{T:.2f}", "-c:v", "libx264", "-crf", "18", "-c:a", "aac", "-b:a", "192k", cut], check=True)
packshot(cut, ps, str(d / "final.mp4"))
print(f"✅ {d / 'final.mp4'} · {T:.1f}s · 💰 OpenAI TTS ~${oai.spent:.3f}")
