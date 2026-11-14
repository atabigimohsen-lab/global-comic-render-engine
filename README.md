# Global Comic Render Engine

A lightweight, FFmpeg-based renderer for original 40-panel comic videos.

## Current scope

- Validates a 40-panel production manifest before rendering.
- Requires panel sequence numbers `01` through `40`, an art prompt, a local image, a valid duration, and dialogue/narration/SFX or an explicit silent-panel marker.
- Supports optional narration audio.
- Produces H.264 MP4 at 1280×720 (16:9), 24 fps.
- Keeps generated images, audio, manifests containing private URLs, and finished videos out of this public source repository.

## Requirements

- Python 3.10+
- FFmpeg available on `PATH`

No Python third-party packages are required.

## Validate a manifest

```bash
python -m renderer.validate_manifest path/to/manifest.json
```

## Render a video

```bash
python -m renderer.render path/to/manifest.json --output output/comic.mp4
```

The manifest's panel image paths are resolved relative to the manifest file. Optional audio is configured with `audio.narrationPath`, also relative to the manifest.

## Manifest shape

See [renderer/manifest.schema.json](renderer/manifest.schema.json).

## Safety and publication boundary

This repository contains rendering code only. It does not discover trends, generate images, verify news facts, or upload to YouTube. Those stages must pass their own validation before a rendered video is considered publishable. No workflow in this repository automatically publishes content.
