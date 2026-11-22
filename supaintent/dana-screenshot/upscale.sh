#!/usr/bin/env bash
# AI upscale 360p → 720p locally with Real-ESRGAN, keeps audio. realesr-animevideov3 x2 for every style:
# realesrgan-x4plus keeps realistic skin better but is ~4x slower, too slow for batches.
# Usage: ./upscale.sh <in.mp4> [out.mp4]
set -euo pipefail
IN=$1; OUT=${2:-${IN%.mp4}_ai720.mp4}
BIN=$(dirname "$0")/../../3d/tools/realesrgan
TMP=$(mktemp -d); mkdir -p "$TMP/in" "$TMP/out"
FPS=$(ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 "$IN")

echo "🎞️  extracting frames..."
ffmpeg -v error -i "$IN" "$TMP/in/%05d.png"
echo "🧠 upscaling $(ls "$TMP/in" | wc -l | tr -d ' ') frames..."
"$BIN/realesrgan-ncnn-vulkan" -i "$TMP/in" -o "$TMP/out" -n realesr-animevideov3 -s 2 -m "$BIN/models" -f png 2>/dev/null
echo "📦 encoding..."
ffmpeg -v error -y -framerate "$FPS" -i "$TMP/out/%05d.png" -i "$IN" -map 0:v -map 1:a? \
  -vf "scale=720:1280:flags=lanczos" -c:v libx264 -crf 16 -preset slow -pix_fmt yuv420p -c:a copy -shortest "$OUT"
rm -rf "$TMP"
echo "✅ $OUT"
