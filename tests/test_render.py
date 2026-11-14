"""End-to-end FFmpeg rendering smoke test using generated local test images."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from renderer.render import render


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg/ffprobe required")
class RenderSmokeTests(unittest.TestCase):
    def test_renders_40_panels_to_valid_720p_mp4(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
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
                panels.append(
                    {
                        "seq": f"{number:02d}",
                        "artPrompt": f"Synthetic CI test panel {number}",
                        "image": image_name,
                        "durationSeconds": 0.25,
                        "narration": f"Panel {number}",
                    }
                )

            manifest_path = base / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "title": "Synthetic renderer smoke test",
                        "aspectRatio": "16:9",
                        "panels": panels,
                    }
                ),
                encoding="utf-8",
            )
            output = base / "output" / "smoke-test.mp4"
            render(manifest_path, output)

            self.assertTrue(output.is_file())
            self.assertGreater(output.stat().st_size, 1000)

            probe = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-select_streams", "v:0",
                    "-show_entries", "stream=codec_name,width,height",
                    "-of", "json", str(output),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            stream = json.loads(probe.stdout)["streams"][0]
            self.assertEqual(stream["codec_name"], "h264")
            self.assertEqual(stream["width"], 1280)
            self.assertEqual(stream["height"], 720)


if __name__ == "__main__":
    unittest.main()
