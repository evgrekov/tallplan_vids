"""Shared drawing + assembly for the voice-over "state" formats (family/, path/): fonts, the crooked pill figure,
the TallPlan-style prediction card, TTS lines and the ffmpeg cut where full-frame states switch on their voice lines."""
import pathlib, random, subprocess, sys, wave
from PIL import Image, ImageDraw, ImageFont
ROOT = pathlib.Path(__file__).parent.parent
sys.path[:0] = [str(ROOT / "slides"), str(ROOT / "muscle")]
import oai
from assemble import packshot

W, H, LIME = 1080, 1920, "#c8f03c"
ICON = ROOT / "TallPlan photo/Logo/app-icon.png"

def font(size, wght=800):
    f = ImageFont.truetype(str(ROOT / "3d/fonts/Montserrat.ttf"), size); f.set_variation_by_axes([wght]); return f

def ftin(i): return f"{i // 12}'{i % 12}\""

def say(d, spec, name, text):
    """One TTS line → <d>/vo/<name>.wav (cached), returns (path, seconds)."""
    out = d / f"vo/{name}.wav"
    out.parent.mkdir(exist_ok=True)
    if not out.exists():
        print(f"🎙️  {name}: {text}")
        with wave.open(str(out), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000)
            w.writeframes(oai.speech(text, spec["voice"], spec["openai_voice"], spec.get("speed", 1.0)))
    with wave.open(str(out)) as w: return out, w.getnframes() / w.getframerate()

def timeline(lines, gap=0.15):
    """Voice lines back to back from 0.2 s → [(wav, start)], end time."""
    t, cues = 0.2, []
    for f, dur in lines: cues.append((f, t)); t += dur + gap
    return cues, t

def figure(im, x, ground, h, color, seed, hat=False, face="white"):
    """Crooked pill-body figure with a simple face, h px tall standing on `ground`; a fixed seed keeps the wobble identical in every state."""
    r, dr = random.Random(seed), ImageDraw.Draw(im, "RGBA")
    j = lambda p: (p[0] + r.uniform(-6, 6), p[1] + r.uniform(-4, 4))
    top = ground - h; hr = h * 0.1; bw = h * 0.09
    neck, hip = top + 2 * hr + 4, top + h * 0.58
    dr.line([j((x - h * 0.08, ground)), (x - bw * 0.4, hip - 10)], fill=color, width=20)
    dr.line([j((x + h * 0.08, ground)), (x + bw * 0.4, hip - 10)], fill=color, width=20)
    dr.line([j((x - h * 0.16, hip - h * 0.05)), (x, neck + h * 0.05), j((x + h * 0.16, hip - h * 0.05))], fill=color, width=16, joint="curve")
    dr.rounded_rectangle((x - bw, neck, x + bw, hip), bw, fill=color)
    dr.ellipse((x - hr, top, x + hr, top + 2 * hr), fill=color)
    if face:
        ey, er = top + hr * 0.85, max(4, hr * 0.13)
        for ex in (x - hr * 0.38, x + hr * 0.38): dr.ellipse((ex - er, ey - er, ex + er, ey + er), fill=face)
        dr.arc((x - hr * 0.45, top + hr * 0.75, x + hr * 0.45, top + hr * 1.5), 20, 160, fill=face, width=5)
    if hat: dr.polygon([(x - hr * 1.1, top + hr * 0.35), (x + hr * 1.1, top + hr * 0.35), (x + hr * 1.3, top - hr * 0.7)], fill="#D62828")
    return top

def tallcard(out, adult, now=None):
    """TallPlan-style prediction card (blue gradient, "As an adult", dotted curve to the lime dot); `now` adds the right-hand block."""
    cw, ch = 900, 600
    face = Image.new("RGB", (cw, ch))
    fd = ImageDraw.Draw(face)
    for y in range(ch):
        k = y / ch; fd.line((0, y, cw, y), fill=(int(0x2c - 10 * k), int(0x44 - 20 * k), int(0xc9 - 40 * k)))
    icon = Image.open(ICON).convert("RGBA").resize((64, 64))
    face.paste(icon, (50, 44), icon)
    fd.text((132, 76), "TallPlan", font=font(42, 800), fill="white", anchor="lm")
    fd.text((50, 170), "As an adult", font=font(40, 600), fill="#B9C3FF", anchor="lm")
    fd.text((46, 290), ftin(adult), font=font(170, 900), fill="white", anchor="lm")
    if now:
        fd.text((cw - 50, 170), "Now", font=font(40, 600), fill="#B9C3FF", anchor="rm")
        fd.text((cw - 50, 232), ftin(now), font=font(64, 900), fill="white", anchor="rm")
        grow = f"+{adult - now} in to grow"
        gw = font(36, 700).getlength(grow)
        fd.rounded_rectangle((cw - 50 - gw - 44, 285, cw - 50, 345), 30, fill="#4A5BD8")
        fd.text((cw - 72, 315), grow, font=font(36, 700), fill="white", anchor="rm")
    for k in range(14):  # dotted growth curve from "you" to the lime dot
        u = k / 13; x, y = 110 + 640 * u, 520 - 130 * (1 - (1 - u) ** 2)
        fd.ellipse((x - 6, y - 6, x + 6, y + 6), fill="white")
    fd.ellipse((750 - 22, 390 - 22, 750 + 22, 390 + 22), fill=LIME)
    fd.text((110, 565), "you", font=font(34, 700), fill="white", anchor="mm")
    mask = Image.new("L", face.size); ImageDraw.Draw(mask).rounded_rectangle((0, 0, cw - 1, ch - 1), 48, fill=255)
    card = Image.new("RGBA", (cw + 60, ch + 60))
    ImageDraw.Draw(card).rounded_rectangle((30, 44, cw + 30, ch + 44), 48, fill=(0, 0, 0, 90))
    card.paste(face, (30, 30), mask)
    card.save(out)

def render(d, states, starts, cues, end, app_t, card, music=None, music_db=-22):
    """states[0] from 0 s, states[k] from starts[k-1]; `card` slides up at app_t and stays; voice lines at their cues,
    optional music bed under the voice; packshot after the last line → <d>/final.mp4."""
    ps, T = end + 0.5, end + 2.3
    for k, s in enumerate(states): s.save(d / f"s{k}.png")
    n = len(states)
    ov = "".join(f"[v{k}][{k + 1}]overlay=enable='gte(t,{s:.2f})'[v{k + 1}];" for k, s in enumerate(starts))
    mix = ";".join(f"[{n + 1 + i}:a]adelay={int(s * 1000)}|{int(s * 1000)},apad[a{i}]" for i, (_, s) in enumerate(cues))
    ins = [f"[a{i}]" for i in range(len(cues))]
    if music:
        mix += f";[{n + 1 + len(cues)}:a]volume={music_db}dB,afade=t=out:st={T - 1:.2f}:d=1[mb]"; ins.append("[mb]")
    mix += ";" + "".join(ins) + f"amix=inputs={len(ins)}:normalize=0,atrim=0:{T:.2f},loudnorm=I=-14:TP=-1.5,aresample=48000[aout]"
    cut = str(d / "cut.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *[x for k in range(n) for x in ("-loop", "1", "-framerate", "30", "-t", f"{T:.2f}", "-i", d / f"s{k}.png")],
                    "-loop", "1", "-framerate", "30", "-t", f"{T:.2f}", "-i", card, *[x for f, _ in cues for x in ("-i", f)],
                    *(["-stream_loop", "-1", "-i", music] if music else []),
                    "-filter_complex", f"[0]null[v0];{ov}[v{n - 1}][{n}]overlay=x=(W-w)/2:y='560+1400*(1-clip((t-{app_t:.2f})/0.35,0,1))':enable='gte(t,{app_t:.2f})',"
                    f"fade=t=out:st={ps - 0.5:.2f}:d=0.5,format=yuv420p[v];{mix}",
                    "-map", "[v]", "-map", "[aout]", "-t", f"{T:.2f}", "-c:v", "libx264", "-crf", "18", "-c:a", "aac", "-b:a", "192k", cut], check=True)
    packshot(cut, ps, str(d / "final.mp4"))
    print(f"✅ {d / 'final.mp4'} · {T:.1f}s · 💰 OpenAI TTS ~${oai.spent:.3f}")
