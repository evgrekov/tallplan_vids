#!/usr/bin/env bash
# Remove a time range from video+audio (e.g. a repeated word in the VO). Best under the packshot, where the jump is hidden.
# Usage: ./cut.sh <in.mp4> <from_sec> <to_sec> [out.mp4]
set -euo pipefail
IN=$1; A=$2; B=$3; OUT=${4:-${IN%.mp4}_cut.mp4}
X=0.08  # audio crossfade, s: removes the splice click, total length stays in sync with video
A2=$(echo "$A + $X / 2" | bc -l); B2=$(echo "$B - $X / 2" | bc -l)
echo "✂️  $IN: removing ${A}s–${B}s → $OUT"
ffmpeg -v error -y -i "$IN" -filter_complex "
[0:v]trim=end=$A,setpts=PTS-STARTPTS[v0];[0:v]trim=start=$B,setpts=PTS-STARTPTS[v1];
[v0][v1]concat=n=2:v=1:a=0[v];
[0:a]atrim=end=$A2,asetpts=PTS-STARTPTS[a0];[0:a]atrim=start=$B2,asetpts=PTS-STARTPTS[a1];
[a0][a1]acrossfade=d=$X:c1=tri:c2=tri[a]" -map "[v]" -map "[a]" -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k "$OUT"
echo "✅ $OUT"
