import tempfile
import unittest
from pathlib import Path
from renderer.validate_manifest import validate_manifest

class ManifestValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.panels = []
        for n in range(1, 31):
            image = f"panel-{n:02d}.png"
            audio = f"panel-{n:02d}.mp3"
            (self.base / image).write_bytes(b"test-image-placeholder")
            (self.base / audio).write_bytes(b"test-audio-placeholder")
            self.panels.append({"seq": f"{n:02d}", "artPrompt": f"Comic panel {n}", "image": image, "durationSeconds": 5.0, "narration": f"روایت اسلاید {n}", "narrationAudio": audio})
        self.manifest = {"title": "Test audio slideshow", "aspectRatio": "16:9", "audio": {"narrationMode": "per_panel_tts", "language": "fa-IR", "voice": "fa-IR-FaridNeural"}, "panels": self.panels}

    def tearDown(self):
        self.temp.cleanup()

    def test_accepts_exactly_30_ordered_panels(self):
        self.assertEqual(validate_manifest(self.manifest, self.base), [])

    def test_rejects_missing_panel(self):
        self.manifest["panels"] = self.panels[:-1]
        self.assertTrue(any("30 panels required" in e for e in validate_manifest(self.manifest, self.base)))

    def test_rejects_out_of_order_sequence(self):
        self.manifest["panels"][1]["seq"] = "01"
        self.assertTrue(any("Panel 02" in e for e in validate_manifest(self.manifest, self.base)))

    def test_rejects_missing_image(self):
        self.manifest["panels"][0]["image"] = "missing.png"
        self.assertTrue(any("file missing" in e for e in validate_manifest(self.manifest, self.base)))

    def test_rejects_missing_narration_audio(self):
        self.manifest["panels"][0]["narrationAudio"] = "missing.mp3"
        self.assertTrue(any("audio file missing" in e for e in validate_manifest(self.manifest, self.base)))

    def test_rejects_missing_persian_narration(self):
        self.manifest["panels"][0]["narration"] = ""
        self.assertTrue(any("Persian narration missing" in e for e in validate_manifest(self.manifest, self.base)))

    def test_rejects_dialogue_overlay(self):
        self.manifest["panels"][0]["dialogue"] = {"text": "hello"}
        self.assertTrue(any("dialogue" in e for e in validate_manifest(self.manifest, self.base)))

    def test_factual_story_requires_two_domains(self):
        self.manifest["isFactual"] = True
        self.manifest["sourceFactRefs"] = [{"url": "https://news.example.com/story"}]
        self.assertTrue(any("two distinct source domains" in e for e in validate_manifest(self.manifest, self.base)))

    def test_factual_story_accepts_distinct_publishers(self):
        self.manifest["isFactual"] = True
        self.manifest["sourceFactRefs"] = [{"publisher": "ncaa.org", "url": "https://news.google.com/a"}, {"publisher": "ferris.edu", "url": "https://news.google.com/b"}]
        self.assertEqual(validate_manifest(self.manifest, self.base), [])

    def test_rejects_parent_directory_traversal(self):
        outside = self.base.parent / "outside.png"
        outside.write_bytes(b"x")
        try:
            self.manifest["panels"][0]["image"] = "../outside.png"
            self.assertTrue(any("escapes" in e for e in validate_manifest(self.manifest, self.base)))
        finally:
            outside.unlink(missing_ok=True)

if __name__ == "__main__":
    unittest.main()
