import tempfile
import unittest
from pathlib import Path

from renderer.validate_manifest import validate_manifest


class ManifestValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.panels = []
        for number in range(1, 31):
            image = f"panel-{number:02d}.png"
            (self.base / image).write_bytes(b"test-image-placeholder")
            self.panels.append({
                "seq": f"{number:02d}",
                "artPrompt": f"Comic panel {number}",
                "image": image,
                "durationSeconds": 2.0,
                "narration": f"Panel {number}"
            })
        self.manifest = {
            "title": "Test comic",
            "aspectRatio": "16:9",
            "panels": self.panels
        }

    def tearDown(self):
        self.temp.cleanup()

    def test_accepts_exactly_30_ordered_panels(self):
        self.assertEqual(validate_manifest(self.manifest, self.base), [])

    def test_rejects_missing_panel(self):
        self.manifest["panels"] = self.panels[:-1]
        errors = validate_manifest(self.manifest, self.base)
        self.assertTrue(any("exactly 30" in error for error in errors))

    def test_rejects_duplicate_or_out_of_order_sequence(self):
        self.manifest["panels"][1]["seq"] = "01"
        errors = validate_manifest(self.manifest, self.base)
        self.assertTrue(any("Panel 02 must have seq '02'" in error for error in errors))

    def test_rejects_missing_image(self):
        self.manifest["panels"][0]["image"] = "missing.png"
        errors = validate_manifest(self.manifest, self.base)
        self.assertTrue(any("file does not exist" in error for error in errors))

    def test_factual_story_requires_two_domains(self):
        self.manifest["isFactual"] = True
        self.manifest["sourceFactRefs"] = [{"url": "https://news.example.com/story"}]
        errors = validate_manifest(self.manifest, self.base)
        self.assertTrue(any("two distinct domains" in error for error in errors))

    def test_factual_story_accepts_distinct_publishers_with_google_news_redirect_urls(self):
        self.manifest["isFactual"] = True
        self.manifest["sourceFactRefs"] = [
            {"publisher": "ncaa.org", "url": "https://news.google.com/rss/articles/source-one"},
            {"publisher": "ferris.edu", "url": "https://news.google.com/rss/articles/source-two"},
        ]
        errors = validate_manifest(self.manifest, self.base)
        self.assertEqual(errors, [])

    def test_rejects_parent_directory_image_traversal(self):
        outside = self.base.parent / "outside.png"
        outside.write_bytes(b"not-an-image")
        try:
            self.manifest["panels"][0]["image"] = "../outside.png"
            errors = validate_manifest(self.manifest, self.base)
            self.assertTrue(any("stay inside" in error for error in errors))
        finally:
            outside.unlink(missing_ok=True)

    def test_rejects_missing_narration_audio(self):
        self.manifest["audio"] = {"narrationPath": "missing.wav"}
        errors = validate_manifest(self.manifest, self.base)
        self.assertTrue(any("Narration audio file does not exist" in error for error in errors))

    def test_rejects_audio_path_traversal(self):
        outside = self.base.parent / "outside.wav"
        outside.write_bytes(b"not-audio")
        try:
            self.manifest["audio"] = {"narrationPath": "../outside.wav"}
            errors = validate_manifest(self.manifest, self.base)
            self.assertTrue(any("Narration audio must stay inside" in error for error in errors))
        finally:
            outside.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
