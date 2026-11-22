"""Mux the rendered 3D visual with voice + ducked music, then burn captions → out/final.mp4.
Usage: uv run --with pillow python py/finish.py <id>"""
import pathlib, subprocess, sys
OUT = pathlib.Path(__file__).parent.parent / "videos" / sys.argv[1] / "out"
mix, edit = OUT / "audio_mix.m4a", OUT / "edit.mp4"
length = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", OUT / "visual.mp4"], capture_output=True, text=True).stdout.strip()
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", OUT / "voice.wav", "-stream_loop", "-1", "-i", OUT / "music.mp3", "-filter_complex",
                "[0:a]apad[vo];[vo]asplit[v1][v2];[1:a]volume=0.35[m];[m][v1]sidechaincompress=threshold=0.03:ratio=8:release=300[d];"
                f"[v2][d]amix=inputs=2:normalize=0,alimiter=limit=0.95,atrim=0:{length},afade=t=out:st={float(length) - 1}:d=1", "-c:a", "aac", "-b:a", "192k", mix], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", OUT / "visual.mp4", "-i", mix, "-c:v", "copy", "-c:a", "copy", "-shortest", edit], check=True)
subprocess.run(["uv", "run", "-q", pathlib.Path(__file__).parent / "captions.py", edit, OUT / "words.json", OUT / "final.mp4"], check=True)
print(f"🏁 {OUT / 'final.mp4'}")
