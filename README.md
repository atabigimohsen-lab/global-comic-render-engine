# Global Comic Render Engine

A lightweight, FFmpeg-based renderer for original 30-panel comic videos.

## Current scope

- Validates exactly 30 ordered comic panels before rendering.
- Requires an art prompt, local image, valid duration, and dialogue/narration/SFX or an explicit silent-panel marker for every panel.
- Supports optional narration audio.
- Produces H.264 MP4 at 1280×720 (16:9), 24 fps.
- Keeps generated artwork, audio, manifests, and rendered videos out of this public source repository.

## Requirements

- Python 3.10+
- FFmpeg and ffprobe available on PATH

No Python third-party packages are required for local rendering.

## Validate and render locally

```bash
python -m renderer.validate_manifest path/to/manifest.json
python -m renderer.render path/to/manifest.json --output output/comic.mp4
```

Panel image paths and optional `audio.narrationPath` are resolved relative to the manifest.

## Manifest shape

See [renderer/manifest.schema.json](renderer/manifest.schema.json).

## Private Google Drive bridge

The GitHub Actions workflow `.github/workflows/render-comic.yml` is manual-only (`workflow_dispatch`). It does not publish to YouTube.

The current architecture is:

1. The source ZIP is stored in the private Google Drive input folder.
2. GitHub Actions requests the ZIP from the authenticated n8n webhook bridge.
3. n8n uses the user's Google Drive OAuth credential to locate and stream the private ZIP.
4. GitHub Actions validates the archive and manifest, then renders with FFmpeg.
5. The MP4 is sent to the authenticated n8n upload webhook.
6. n8n stores the MP4 in the separate private Google Drive output folder.
7. The source ZIP is retained; neither input nor output is made public.

### Required GitHub Actions secret

- `N8N_COMIC_BRIDGE_KEY`: the same secret value configured in the n8n Header Auth credential. It is sent only in the HTTPS Authorization header. Never commit or print this value.

The n8n bridge uses the existing private Google Drive OAuth connection. This design does not require a Google service-account JSON key or public Drive links.

## Transfer limits and current verification status

n8n's Webhook documentation lists a 16 MB maximum webhook payload, and n8n Cloud documents a 100-second webhook response timeout. Multipart binary uploads and binary responses have additional hosting-specific behavior, so the current 100 MB workflow caps must not be treated as a verified n8n Cloud guarantee. Large media should use a chunked/resumable transfer design or be proven against the actual Cloud plan before production use.

The local renderer test suite has passed in this environment. The complete GitHub Actions → n8n → private Drive round trip has not yet been run. No cloud render has been claimed as successful.

## Resource and activation safeguards

- Rendering is started manually; no scheduled GitHub runner is started by this repository.
- GitHub Actions usage and billing limits must be checked before dispatching a render.
- The n8n bridge and trend-discovery workflow remain unpublished unless explicitly enabled for a controlled test or production operation.
- YouTube publication is a separate stage and remains disabled.

## Safety boundary

This repository contains rendering code only. It does not discover trends, generate artwork, verify news facts, or publish to YouTube. Those stages must pass their own validation and editorial checks before a rendered video is considered publishable.
