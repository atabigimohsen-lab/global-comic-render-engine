"""End-to-end FFmpeg rendering smoke tests using generated local media."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from renderer.render import render


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg/ffprobe required")
class RenderSmokeTests(unittest.TestCase):
    def _make_manifest(self, base: Path, with_audio: bool = False) -> Path:
        seed = base / "seed.png"
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", "color=c=navy:s=320x180:d=1",
                "-frames:v", "1", str(seed),
            ],
            check=True,
        )

        panels = []
        for number in range(1, 41):
            image_name = f"panel-{number:02d}.png"
            shutil.copyfile(seed, base / image_name)
            panels.append({
                "seq": f"{number:02d}",
                "artPrompt": f"Synthetic CI test panel {number}",
                "image": image_name,
                "durationSeconds": 0.25,
                "narration": f"Panel {number}",
            })

        manifest = {
            "title": "Synthetic renderer smoke test",
            "aspectRatio": "16:9",
            "panels": panels,
        }
        if with_audio:
            audio_path = base / "narration.wav"
            subprocess.run(
                [
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                    "-t", "1", str(audio_path),
                ],
                check=True,
            )
            manifest["audio"] = {"narrationPath": audio_path.name}

        manifest_path = base / "manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        return manifest_path

    def _probe(self, output: Path) -> dict:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "stream=codec_type,codec_name,width,height",
                "-of", "json", str(output),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout)

    def test_renders_40_panels_to_valid_720p_mp4(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            manifest = self._make_manifest(base)
            output = base / "output" / "smoke-test.mp4"
            render(manifest, output)

            self.assertTrue(output.is_file())
            self.assertGreater(output.stat().st_size, 1000)
            streams = self._probe(output)["streams"]
            video = next(stream for stream in streams if stream["codec_type"] == "video")
            self.assertEqual(video["codec_name"], "h264")
            self.assertEqual(video["width"], 1280)
            self.assertEqual(video["height"], 720)

    def test_renders_narration_audio_as_aac(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            manifest = self._make_manifest(base, with_audio=True)
            output = base / "output" / "smoke-test-audio.mp4"
            render(manifest, output)

            streams = self._probe(output)["streams"]
            audio = next(stream for stream in streams if stream["codec_type"] == "audio")
            self.assertEqual(audio["codec_name"], "aac")


if __name__ == "__main__":
    unittest.main()
