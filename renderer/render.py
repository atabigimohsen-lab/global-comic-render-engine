"""Render a validated 30-panel manifest to an MP4 using FFmpeg."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from renderer.validate_manifest import validate_manifest


def _ffconcat_quote(path: Path) -> str:
    value = str(path.resolve())
    if "\n" in value or "\r" in value:
        raise ValueError("File paths must not contain newline characters.")
    return "'" + value.replace("'", "'\\''") + "'"


def render(manifest_path: Path, output_path: Path) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("Manifest root must be a JSON object.")

    base_dir = manifest_path.resolve().parent
    errors = validate_manifest(manifest, base_dir)
    if errors:
        raise ValueError("Manifest validation failed:\n- " + "\n- ".join(errors))

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg was not found on PATH.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    panels = manifest["panels"]

    with tempfile.TemporaryDirectory(prefix="comic-render-") as temp_dir:
        concat_file = Path(temp_dir) / "panels.ffconcat"
        lines = ["ffconcat version 1.0"]
        for panel in panels:
            image_path = (base_dir / panel["image"]).resolve()
            lines.append(f"file {_ffconcat_quote(image_path)}")
            lines.append(f"duration {float(panel['durationSeconds']):.3f}")
        lines.append(f"file {_ffconcat_quote((base_dir / panels[-1]['image']).resolve())}")
        concat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        command = [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_file),
        ]

        audio = manifest.get("audio", {})
        narration = audio.get("narrationPath") if isinstance(audio, dict) else None
        if narration:
            narration_path = (base_dir / narration).resolve()
            if not narration_path.is_file():
                raise FileNotFoundError(f"Narration audio does not exist: {narration}")
            command += ["-i", str(narration_path)]

        command += [
            "-vf", "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,fps=24,format=yuv420p",
            "-map", "0:v:0",
        ]
        if narration:
            command += ["-map", "1:a:0", "-af", "apad", "-shortest", "-c:a", "aac", "-b:a", "160k"]

        command += [
            "-c:v", "libx264", "-preset", "medium", "-crf", "21",
            "-movflags", "+faststart", str(output_path.resolve()),
        ]
        subprocess.run(command, check=True)

    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise RuntimeError("FFmpeg finished without producing a non-empty MP4.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a validated 30-panel comic to MP4.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        render(args.manifest, args.output)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(f"RENDER FAILED: {exc}")
        return 1

    print(f"Render complete: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
