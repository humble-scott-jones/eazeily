## Demo subtitles

This file describes how to add subtitles to the demo video.

Files created in this change:

- `outputs/demo_subtitles.srt` — SubRip subtitle file used for the short demo.
- `scripts/add_subtitles.sh` — Small helper script that uses `ffmpeg` to add the SRT into the MP4 as a mov_text track.

How to regenerate the narrated MP4 with subtitles locally:

1. Ensure `ffmpeg` is installed (Homebrew):

```bash
brew install ffmpeg
```

2. If you need to regenerate narration (macOS):

```bash
say -o outputs/narration.aiff "<your narration text>"
ffmpeg -y -i outputs/demo.webm -i outputs/narration.aiff -c:v libx264 -pix_fmt yuv420p -preset veryfast -crf 20 -c:a aac -b:a 192k -ar 44100 -shortest -movflags +faststart outputs/demo_narrated.mp4
```

3. Add subtitles (this will create `outputs/demo_narrated_subs.mp4`):

```bash
./scripts/add_subtitles.sh
```

If you prefer burned-in subtitles instead of a selectable subtitle track, let me know and I can add an alternative ffmpeg command that renders the subtitles into the video frames.
