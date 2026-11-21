#!/usr/bin/env bash
# Post-production for a generated 360p clip: AI upscale → 60 fps interpolation → word timings → packshot → captions.
# Usage: ./finish.sh <raw_360p.mp4> <packshot_start_sec> [out.mp4] [words.json: known word timings, skips align]
set -euo pipefail
abs() { echo "$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"; }
RAW=$(abs "$1"); PS=$2; BASE=${RAW%.mp4}; OUT=$(abs "${3:-${BASE}_final.mp4}")
cd "$(dirname "$0")"

./upscale.sh "$RAW" "${BASE}_up24.mp4"
echo "🎚️  interpolating to 60 fps..."  # TikTok plays max 60; scd skips blending across hard cuts
ffmpeg -v error -y -i "${BASE}_up24.mp4" -vf "minterpolate=fps=60:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1:scd=fdiff:scd_threshold=8" \
  -c:v libx264 -crf 16 -preset slow -pix_fmt yuv420p -c:a copy "${BASE}_up.mp4"
rm "${BASE}_up24.mp4"
if [ -n "${4:-}" ]; then cp "$4" "${BASE}_words.json"; else python3 align.py "${BASE}_up.mp4" "${BASE}_words.json"; fi
./packshot.sh "${BASE}_up.mp4" "$PS"
uv run -q captions.py "${BASE}_up_final.mp4" "${BASE}_words.json" "$OUT"
rm "${BASE}_up_final.mp4"
echo "🏁 $OUT"
