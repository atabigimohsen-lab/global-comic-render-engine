# Global 40-Panel Persian Audio Comic
- Exactly 40 still comic images in 16:9.
- Persian narration (fa-IR) is generated per slide using Edge TTS.
- Each image remains on screen for the full duration of its own narration; slides advance automatically at the end of the voice segment.
- Output: H.264 1280x720, 24 fps, AAC audio. No animation, captions, dialogue balloons or on-image text.
- Default voice: fa-IR-FaridNeural (configurable in manifest audio.voice).
## Local
Requires Python 3.10+, FFmpeg and ffprobe. GitHub workflow installs requests and edge-tts.
```bash
python -m renderer.validate_manifest path/to/manifest.json
python -m renderer.render path/to/manifest.json --output audio-comic.mp4
```
## Private pipeline
Manual workflow_dispatch only: download private ZIP through authenticated n8n bridge, validate archive, generate 40 Persian TTS tracks, validate manifest and media, render synchronized still slides, upload MP4 privately to Drive. Input ZIP is retained. No public publishing or scheduled runs.
Required GitHub secret: N8N_COMIC_BRIDGE_KEY. Never commit credentials.
