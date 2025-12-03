#!/usr/bin/env bash
set -euo pipefail

# Add SRT subtitles into MP4 as a mov_text subtitle track (no video re-encode)
# Usage: ./scripts/add_subtitles.sh

INPUT="outputs/demo_narrated.mp4"
SRT="outputs/demo_subtitles.srt"
OUT="outputs/demo_narrated_subs.mp4"

if [[ ! -f "$INPUT" ]]; then
  echo "Input file $INPUT not found" >&2
  exit 1
fi

if [[ ! -f "$SRT" ]]; then
  echo "Subtitle file $SRT not found" >&2
  exit 1
fi

ffmpeg -y -i "$INPUT" -i "$SRT" -c copy -c:s mov_text "$OUT"
echo "Created $OUT"
