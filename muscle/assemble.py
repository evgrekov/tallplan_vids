# /// script
# dependencies = ["pillow"]
# ///
"""Cut the clips, lay the overlay on top, mix voice + music, export a social-ready 1080x1920 mp4.

  uv run assemble.py reel.json

Needs: render_overlay.py run first (ov/ frames), ffmpeg on PATH.
Voice timing comes from render_overlay.load_config (lines back to back, tagline under the packshot). Music ducks under the voice.
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from PIL import Image, ImageDraw, ImageFont  # noqa: E402
from render_overlay import load_config  # noqa: E402


def run(args):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *args], check=True)


def main():
    cfg, tl = load_config(sys.argv[1])
    base = cfg['_base']
    P = lambda p: os.path.join(base, p)  # noqa: E731
    fps = tl['fps']
    work = P('build')
    os.makedirs(work, exist_ok=True)

    # 1) every clip trimmed to its slot, upscaled to 1080x1920 at the reel's frame rate
    parts = []
    for s in tl['sections']:
        for c in s['clips']:
            n = int(round(c['dur'] * fps))
            out = os.path.join(work, f'p{len(parts):02d}.mp4')
            run(['-i', P(c['file']), '-vf', f'scale=1080:1920:flags=lanczos,fps={fps},setsar=1', '-frames:v', str(n),
                 '-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '15', '-pix_fmt', 'yuv420p', out])
            parts.append(out)
    tail = os.path.join(work, 'tail.mp4')
    run(['-f', 'lavfi', '-i', f'color=black:s=1080x1920:r={fps}', '-frames:v', str(int(round(tl['end_seconds'] * fps))),
         '-c:v', 'libx264', '-preset', 'medium', '-crf', '15', '-pix_fmt', 'yuv420p', tail])
    parts.append(tail)
    with open(os.path.join(work, 'list.txt'), 'w') as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    base_v = os.path.join(work, 'base.mp4')
    run(['-f', 'concat', '-safe', '0', '-i', os.path.join(work, 'list.txt'), '-c', 'copy', base_v])

    # 2) overlay frames on top
    total_frames = int(round(tl['total'] * fps))
    ovd = P(cfg.get('overlay_dir', 'ov'))
    video = os.path.join(work, 'video.mp4')
    run(['-i', base_v, '-framerate', str(fps), '-i', os.path.join(ovd, '%05d.png'),
         '-filter_complex', '[0:v][1:v]overlay=0:0:format=auto,format=yuv420p', '-frames:v', str(total_frames),
         '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-r', str(fps), video])

    # 3) audio: voice lines placed on the timeline, music ducked underneath
    a = cfg['audio']
    cues = [(f, t) for f, t, _, _ in tl['cues']]
    inputs, chains = [], []
    for i, (f, t) in enumerate(cues):
        inputs += ['-i', P(f)]
        ms = max(0, int(t * 1000))
        chains.append(f'[{i}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms},apad[v{i}]')
    mi = len(cues)
    inputs += ['-i', P(a['music'])]
    T = tl['total']
    vol = a.get('music_volume', 0.32)
    fc = ';'.join(chains)
    fc += ';' + ''.join(f'[v{i}]' for i in range(len(cues))) + f'amix=inputs={len(cues)}:normalize=0:duration=longest,atrim=0:{T:.3f},asplit[vo][sc]'
    fc += f';[{mi}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{T:.3f},afade=t=in:d=0.2,afade=t=out:st={T - 1.3:.3f}:d=1.3,volume={vol}[mus]'
    fc += ';[mus][sc]sidechaincompress=threshold=0.04:ratio=5:attack=15:release=350[duck]'
    fc += ';[duck][vo]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]'
    audio = os.path.join(work, 'audio.m4a')
    run([*inputs, '-filter_complex', fc, '-map', '[aout]', '-t', f'{T:.3f}', '-c:a', 'aac', '-b:a', '192k', '-ac', '2', audio])

    # 4) mux
    out = P(cfg.get('out', 'out/reel.mp4'))
    cut = os.path.join(work, 'cut.mp4')
    run(['-i', video, '-i', audio, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'copy', '-shortest', cut])

    packshot(cut, tl['end_start'] - 0.3, out)
    print('done:', out, f'{T:.2f}s')


def packshot(cut, ps, out):
    """Our ending on a 1080x1920 cut: TallPlan packshot card from `ps` s + two-line CTA (same as every other format)."""
    subprocess.run([os.path.join(HERE, '..', '3d', 'packshot.sh'), cut, f'{ps:.2f}'], check=True)
    f = ImageFont.truetype(os.path.join(HERE, '..', '3d', 'fonts', 'Montserrat.ttf'), 130)
    f.set_variation_by_axes([900])
    while f.getlength('YOUR HEIGHT') > 1080 * 0.8:
        f = f.font_variant(size=f.size - 2); f.set_variation_by_axes([900])
    cta = Image.new('RGBA', (1080, 1920))
    ImageDraw.Draw(cta).multiline_text((540, 1920 * 0.615), 'PREDICT\nYOUR HEIGHT', font=f, fill='white', anchor='ma', align='center',
                                       spacing=10, stroke_width=9, stroke_fill='black')
    cta_f = cut.replace('.mp4', '_cta.png')
    cta.save(cta_f)
    run(['-i', cut.replace('.mp4', '_final.mp4'), '-i', cta_f, '-filter_complex', f"[0][1]overlay=enable='gte(t,{ps + 0.25:.2f})'",
         '-c:v', 'libx264', '-crf', '18', '-c:a', 'copy', '-movflags', '+faststart', out])


if __name__ == '__main__':
    main()
