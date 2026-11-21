#!/usr/bin/env bash
# Overlay packshot.png on the end of a generated video, keeping its audio.
# Usage: ./packshot.sh <video.mp4> [start_sec=3.6] [packshot.png]
set -euo pipefail
IN=$1; ST=${2:-3.6}; PS=${3:-$(dirname "$0")/packshot.png}
OUT="${IN%.mp4}_final.mp4"
W=$(ffprobe -v error -select_streams v:0 -show_entries stream=width -of csv=p=0 "$IN")

echo "🎞️  $IN → $OUT (packshot from ${ST}s)"
# Card: 70% of width (its bottom stays above the CTA at 0.615H) (clear of the right-side UI icons), pop 80%→100% over 0.25s with ease-out, background dimmed 40%
ffmpeg -v error -y -i "$IN" -loop 1 -i "$PS" -filter_complex "
[0:v]eq=brightness=-0.25:enable='gte(t,$ST)'[bg];
[1:v]scale=w='trunc($W*0.7*(0.8+0.2*(1-pow(1-min(1,max(0,(t-$ST)/0.25)),3)))/2)*2':h=-2:eval=frame[card];
[bg][card]overlay=x=(W-w)/2:y=(H-h)*0.3:enable='gte(t,$ST)':shortest=1[v]" \
  -map "[v]" -map 0:a? -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a copy "$OUT"
echo "✅ $OUT"
