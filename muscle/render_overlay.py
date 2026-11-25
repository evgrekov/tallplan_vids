# /// script
# dependencies = ["pillow"]
# ///
"""Render the UI overlay for a 3D muscle workout reel as a transparent PNG sequence.

  uv run render_overlay.py reel.json            -> <workdir>/ov/00000.png ... + <workdir>/timeline.json

What it draws (all measured from the reference reel, scaled to 1080x1920):
  - the muscle name near the top: wipes in with a light flare when it's spoken, smears out before the switch
  - word-by-word subtitles of the voice lines (3-word chunk, current word yellow) above the bottom UI zone
  - fade to black at the end (assemble.py adds the TallPlan packshot + CTA)
Timing comes from the clip durations in reel.json, so the overlay always matches the cut.
"""
import json, math, os, sys, wave
from concurrent.futures import ProcessPoolExecutor
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, 'assets', 'fonts', 'Archivo.ttf')
SUB_FONT = os.path.join(HERE, '..', '3d', 'fonts', 'Montserrat.ttf')  # same subtitles as the other formats  # variable font: wdth 62-125, wght 100-900

W, H = 1080, 1920
LABEL_CY = 296


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def font(size, wdth=125, wght=850):
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_axes([wght, wdth])
    except Exception:
        pass
    return f


def load_config(path):
    cfg = json.load(open(path))
    base = os.path.dirname(os.path.abspath(path))
    cfg['_base'] = base
    fps = cfg.get('fps', 30)
    t = 0.0
    secs = []
    for s in cfg['sections']:
        d = sum(c['dur'] for c in s['clips'])
        secs.append({**s, 'start': t, 'end': t + d})
        t += d
    end_start = t
    intro = cfg.get('intro_seconds', 4.6)  # first label waits for the intro line
    for i, s in enumerate(secs):
        s['label_in'] = s['start'] + (intro if i == 0 else cfg.get('label_delay', 1.3))
        s['label_out'] = s['end'] - (0.7 if i < len(secs) - 1 else 0.5)
    tl = {'fps': fps, 'sections': secs, 'end_start': end_start, 'end_seconds': cfg.get('end_card_seconds', 3.0)}
    # voice lines back to back from 0.1s (question, each section's explanation, conclusion); the tagline plays under the packshot
    a, t, cues = cfg['audio'], 0.1, []
    for f, text, st in [(a['intro'], cfg['script']['intro'], 0)] + [(s['vo'], s['say'], s['start'] + 0.2) for s in secs] + [(a['outro'], cfg['script']['outro'], 0)]:
        t = max(t, st)  # a section's line never starts before its clip
        with wave.open(os.path.join(base, f)) as w:
            d = w.getnframes() / w.getframerate()
        cues.append((f, t, d, text)); t += d + 0.15
    assert t < end_start, f'voice ({t:.1f}s) is longer than the clips ({end_start:.1f}s)'
    with wave.open(os.path.join(base, a['tagline'])) as w:
        d = w.getnframes() / w.getframerate()
    cues.append((a['tagline'], end_start + 0.75, d, ''))
    tl['end_seconds'] = max(tl['end_seconds'], 0.75 + d + 0.6)  # the packshot lasts until the tagline is fully said
    tl['total'] = end_start + tl['end_seconds']
    tl['cues'] = cues
    return cfg, tl


# ---------- assets prepared once per process ----------
_A = {}


def prep(cfg, tl):
    if _A:
        return _A
    # label images: white wide bold caps with a soft shadow
    lf = font(cfg.get('label_size', 38))
    labels = []
    for s in tl['sections']:
        txt = s['name'].upper()
        bb = lf.getbbox(txt)
        tw, th = bb[2] - bb[0] + 40, bb[3] - bb[1] + 40
        im = Image.new('RGBA', (tw, th), (0, 0, 0, 0))
        sh = Image.new('RGBA', (tw, th), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((20 - bb[0], 22 - bb[1]), txt, font=lf, fill=(0, 0, 0, 170))
        ImageDraw.Draw(im).text((20 - bb[0], 20 - bb[1]), txt, font=lf, fill=(255, 255, 255, 255))
        labels.append(Image.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5)), im))
    _A['labels'] = labels
    words = []  # (start, word, chunk): each line's words spread over its clip by length, 3-word chunks never cross lines
    for li, (_, st, d, text) in enumerate(tl['cues']):
        ws = text.split()
        tot, acc = sum(len(w) + 1 for w in ws), 0
        for j, w in enumerate(ws):
            words.append((st + d * acc / tot, w.upper(), (li, j // 3))); acc += len(w) + 1
    _A['words'] = words
    return _A


def draw_label(frame, t, tl):
    for i, s in enumerate(tl['sections']):
        if not (s['label_in'] <= t < s['label_out'] + 0.32):
            continue
        lab = _A['labels'][i]
        x0, y0 = int(W / 2 - lab.width / 2), int(LABEL_CY - lab.height / 2)
        if t < s['label_in'] + 0.28:  # wipe in with a light flare at the edge
            q = ease((t - s['label_in']) / 0.28)
            cut = int(lab.width * q)
            part = lab.crop((0, 0, max(1, cut), lab.height))
            frame.alpha_composite(part, (x0, y0))
            fl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(fl).ellipse((x0 + cut - 90, LABEL_CY - 7, x0 + cut + 90, LABEL_CY + 7), fill=(255, 255, 255, int(230 * (1 - q * 0.6))))
            frame.alpha_composite(fl.filter(ImageFilter.GaussianBlur(6)))
        elif t >= s['label_out']:  # smear out to the right
            q = ease((t - s['label_out']) / 0.32)
            cut = int(lab.width * q)
            part = lab.crop((cut, 0, lab.width, lab.height))
            smear = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            for c in range(6):
                ghost = part.copy()
                ghost.putalpha(part.getchannel('A').point(lambda v, c=c: int(v * (1 - c / 6) * 0.6)))
                smear.alpha_composite(ghost, (x0 + cut + int(c * 22 * q), y0))
            frame.alpha_composite(smear)
        else:
            frame.alpha_composite(lab, (x0, y0))


def sub_font(size):
    f = ImageFont.truetype(SUB_FONT, size); f.set_variation_by_axes([900]); return f


def draw_subs(frame, t, tl):
    words = _A['words']
    cur = max((i for i, (a, _, _) in enumerate(words) if a <= t), default=None)
    if cur is None or t >= tl['cues'][-2][1] + tl['cues'][-2][2] + 0.3: return
    first = next(i for i, x in enumerate(words) if x[2] == words[cur][2])
    chunk = [w for _, w, c in words if c == words[cur][2]]
    f = sub_font(84)
    while f.getlength(' '.join(chunk)) > W * 0.8: f = sub_font(f.size - 4)
    x, dr = W / 2 - f.getlength(' '.join(chunk)) / 2, ImageDraw.Draw(frame)
    for j, w in enumerate(chunk):
        dr.text((x, H * 0.76 - 60), w, font=f, fill='#FFE14D' if first + j == cur else 'white', anchor='lm', stroke_width=9, stroke_fill='black')
        x += f.getlength(w + ' ')


def render(args):
    path, f0, f1, outdir = args
    cfg, tl = load_config(path)
    prep(cfg, tl)
    fps = tl['fps']
    E = tl['end_start']
    for f in range(f0, f1):
        t = f / fps
        frame = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ui_alpha = 1.0 if t < E - 0.45 else max(0.0, 1 - (t - (E - 0.45)) / 0.35)
        if ui_alpha > 0:
            ui = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            draw_label(ui, t, tl)
            draw_subs(ui, t, tl)
            if ui_alpha < 1:
                ui.putalpha(ui.getchannel('A').point(lambda v: int(v * ui_alpha)))
            frame.alpha_composite(ui)
        if t >= E - 0.5:  # fade to black; assemble.py lays our packshot + CTA on it
            k = min(1.0, (t - (E - 0.5)) / 0.5)
            black = Image.new('RGBA', (W, H), (0, 0, 0, int(255 * k)))
            frame = Image.alpha_composite(frame, black) if k < 1 else black
        frame.save(os.path.join(outdir, f'{f:05d}.png'), compress_level=1)
    return f1 - f0


def main():
    path = sys.argv[1]
    cfg, tl = load_config(path)
    outdir = os.path.join(cfg['_base'], cfg.get('overlay_dir', 'ov'))
    os.makedirs(outdir, exist_ok=True)
    total = int(round(tl['total'] * tl['fps']))
    workers = os.cpu_count() or 4
    step = math.ceil(total / workers)
    jobs = [(path, a, min(total, a + step), outdir) for a in range(0, total, step)]
    with ProcessPoolExecutor(workers) as ex:
        done = sum(ex.map(render, jobs))
    json.dump({k: v for k, v in tl.items()}, open(os.path.join(cfg['_base'], 'timeline.json'), 'w'), indent=1)
    print(f'overlay: {done} frames -> {outdir}  ({tl["total"]:.2f}s)')


if __name__ == '__main__':
    main()
