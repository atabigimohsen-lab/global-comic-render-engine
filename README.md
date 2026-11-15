# Global 40-Panel Persian Audio Comic
- Exactly 40 ordered, cinematic still illustrations in 16:9.
- Persian (fa-IR) narration is generated independently for every slide with Edge TTS.
- Each slide remains visible for the complete duration of its matching narration. The next slide starts when that voice segment finishes.
- Final output: H.264 1280x720 at 24 fps with AAC narration. No animation, on-image text, subtitles, speech bubbles or dialogue overlays.
- Default voice: fa-IR-FaridNeural.
## Local
Python 3.10+, FFmpeg and ffprobe required.
```bash
python -m renderer.validate_manifest path/to/manifest.json
python -m renderer.render path/to/manifest.json --output audio-comic.mp4
```
## Private pipeline
Manual workflow_dispatch only: authenticated private Drive ZIP download, safe extraction, per-slide Persian TTS, strict 40-panel/media validation, synchronized still-image rendering, private Drive upload. Source ZIP retained. No scheduled jobs or public publishing.
GitHub Actions secret N8N_COMIC_BRIDGE_KEY is required; never commit credentials.
