"""Render exactly 30 still-image panels with synchronized Persian narration."""
from __future__ import annotations
import argparse, json, shutil, subprocess, tempfile
from pathlib import Path
from renderer.validate_manifest import validate_manifest

MAX_TOTAL_SECONDS = 180.0

def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)

def probe(probe_bin: str, path: Path) -> dict:
    q = subprocess.run([probe_bin, "-v", "error", "-show_entries",
        "stream=codec_type,codec_name,width,height:format=duration", "-of", "json", str(path)],
        check=True, capture_output=True, text=True)
    return json.loads(q.stdout)

def render(manifest_path: Path, output_path: Path) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("Manifest root must be a JSON object.")
    base = manifest_path.resolve().parent
    errors = validate_manifest(manifest, base)
    if errors:
        raise ValueError("Manifest validation failed:\n- " + "\n- ".join(errors))
    ff, fp = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ff or not fp:
        raise RuntimeError("FFmpeg and ffprobe are required.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    clips, total_duration = [], 0.0
    with tempfile.TemporaryDirectory(prefix="comic-30-") as td:
        tmp = Path(td)
        for i, panel in enumerate(manifest["panels"], 1):
            image = (base / panel["image"]).resolve()
            audio = (base / panel["narrationAudio"]).resolve()
            if not image.is_file() or not audio.is_file():
                raise FileNotFoundError(f"Panel {i:02d}: image or narration audio missing.")
            audio_info = probe(fp, audio)
            audio_duration = float(audio_info["format"]["duration"])
            if not 0 < audio_duration <= 30:
                raise ValueError(f"Panel {i:02d}: narration duration is invalid.")
            slide_duration = max(5.0, audio_duration)
            total_duration += slide_duration
            if total_duration > MAX_TOTAL_SECONDS:
                raise ValueError(f"Slideshow would be {total_duration:.1f}s; maximum is 180s.")
            clip = tmp / f"slide_{i:02d}.mp4"
            clips.append(clip)
            run([ff, "-hide_banner", "-loglevel", "error", "-y",
                "-loop", "1", "-framerate", "24", "-i", str(image),
                "-i", str(audio),
                "-vf", "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,format=yuv420p",
                "-af", "apad", "-t", f"{slide_duration:.3f}", "-r", "24",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2",
                "-movflags", "+faststart", str(clip)])
        concat = tmp / "slides.ffconcat"
        lines = ["ffconcat version 1.0"]
        for clip in clips:
            lines.append("file '" + str(clip.resolve()).replace("'", "'\\''") + "'")
        concat.write_text("\n".join(lines) + "\n", encoding="utf-8")
        run([ff, "-hide_banner", "-loglevel", "error", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat),
            "-c", "copy", "-movflags", "+faststart", str(output_path.resolve())])
    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise RuntimeError("FFmpeg did not produce a non-empty MP4.")
    final = probe(fp, output_path)
    streams = final.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    duration = float(final["format"]["duration"])
    if not video or video.get("codec_name") != "h264" or video.get("width") != 1280 or video.get("height") != 720:
        raise RuntimeError("Final MP4 video stream validation failed.")
    if not audio or audio.get("codec_name") != "aac":
        raise RuntimeError("Final MP4 audio stream validation failed.")
    if duration > MAX_TOTAL_SECONDS:
        raise RuntimeError(f"Final MP4 duration {duration:.2f}s exceeds 180 seconds.")

def main() -> int:
    parser = argparse.ArgumentParser(description="Render a 30-panel Persian audio slideshow.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        render(args.manifest, args.output)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(f"RENDER FAILED: {exc}")
        return 1
    print(f"30-panel slideshow complete (maximum 180 seconds): {args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
