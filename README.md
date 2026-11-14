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

No Python third-party packages are required for local rendering.

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

## Private Google Drive rendering

The GitHub Actions workflow `.github/workflows/render-comic.yml` is manual-only (`workflow_dispatch`). It does not publish to YouTube.

It expects a private ZIP in a Google Drive input folder. The ZIP must contain `manifest.json` at its root plus the 40 panel image files and any optional narration audio referenced by the manifest. The runner:

1. Authenticates as a dedicated Google Cloud service account.
2. Confirms the input file is directly inside the configured input folder and is a ZIP.
3. Rejects unsafe ZIP paths, symlinks, duplicate entries, excessive entry counts and oversized bundles.
4. Runs the manifest validator and FFmpeg renderer.
5. Verifies H.264 1280×720 output and AAC audio when audio exists.
6. Uploads the MP4 to a separate private Google Drive output folder and verifies the saved file metadata.
7. Retains the original input ZIP; it does not delete source material.

### Required GitHub Actions repository secrets

- `GOOGLE_SERVICE_ACCOUNT_JSON`: complete service-account JSON key, stored only as an encrypted GitHub Actions secret.
- `DRIVE_INPUT_FOLDER_ID`: ID of the private folder containing input ZIP files.
- `DRIVE_OUTPUT_FOLDER_ID`: ID of the private folder where rendered MP4 files are stored.

Share only the input and output folders with the dedicated service-account email. Grant Viewer access to the input folder and Editor access to the output folder. Do not share the entire Drive, do not make either folder public, and do not commit service-account keys or generated media to this repository. The service account needs the Google Drive API enabled in its Google Cloud project. Billing is not required for the intended Drive API use; stop if Google Cloud asks to enable paid services or attach a payment method.

To run manually, open GitHub Actions → Render Private Comic Bundle → Run workflow, then provide a job ID and the Drive file ID. This is a rendering test/operation only; YouTube publication remains a separate, disabled stage.

## Safety and publication boundary

This repository contains rendering code only. It does not discover trends, generate images, verify news facts, or upload to YouTube. Those stages must pass their own validation before a rendered video is considered publishable. No workflow in this repository automatically publishes content.
