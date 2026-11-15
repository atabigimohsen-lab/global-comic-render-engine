"""End-to-end FFmpeg smoke tests for 30 synchronized still/audio panels."""
import json, shutil, subprocess, tempfile, unittest
from pathlib import Path
from renderer.render import render

@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg/ffprobe required")
class RenderSmokeTests(unittest.TestCase):
    def _manifest(self, base: Path) -> Path:
        seed = base / "seed.png"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=c=navy:s=320x180:d=1", "-frames:v", "1", str(seed)], check=True)
        panels = []
        audio = base / "narration.wav"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=0.35", "-ar", "22050", str(audio)], check=True)
        for n in range(1, 31):
            img = f"panel-{n:02d}.png"
            shutil.copyfile(seed, base / img)
            aud = f"narration-{n:02d}.wav"
            shutil.copyfile(audio, base / aud)
            panels.append({"seq": f"{n:02d}", "artPrompt": f"CI panel {n}", "image": img, "durationSeconds": 5, "narration": f"روایت آزمایشی اسلاید {n}", "narrationAudio": aud})
        m = {"title": "30 panel test", "aspectRatio": "16:9", "audio": {"narrationMode": "per_panel_tts", "language": "fa-IR", "voice": "fa-IR-FaridNeural"}, "panels": panels}
        path = base / "manifest.json"
        path.write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
        return path

    def _probe(self, path: Path) -> dict:
        p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height:format=duration", "-of", "json", str(path)], check=True, capture_output=True, text=True)
        return json.loads(p.stdout)

    def test_renders_30_panel_720p_mp4(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            manifest = self._manifest(base)
            out = base / "out.mp4"
            render(manifest, out)
            self.assertTrue(out.is_file())
            self.assertGreater(out.stat().st_size, 1000)
            data = self._probe(out)
            video = next(s for s in data["streams"] if s["codec_type"] == "video")
            audio = next(s for s in data["streams"] if s["codec_type"] == "audio")
            self.assertEqual((video["codec_name"], video["width"], video["height"]), ("h264", 1280, 720))
            self.assertEqual(audio["codec_name"], "aac")
            self.assertLessEqual(float(data["format"]["duration"]), 180)

    def test_every_slide_has_matching_narration_audio(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            manifest = self._manifest(base)
            out = base / "out.mp4"
            render(manifest, out)
            audio = next(s for s in self._probe(out)["streams"] if s["codec_type"] == "audio")
            self.assertEqual(audio["codec_name"], "aac")

if __name__ == "__main__":
    unittest.main()
