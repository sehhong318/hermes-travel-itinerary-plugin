import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "travel-itinerary-builder"
RENDERER = SKILL_DIR / "scripts" / "render_itinerary.py"
EXAMPLE = SKILL_DIR / "templates" / "itinerary.example.json"


class FakeContext:
    def __init__(self):
        self.skills = {}

    def register_skill(self, name, path):
        self.skills[name] = Path(path)


class PluginTests(unittest.TestCase):
    def test_registers_bundled_skill(self):
        spec = importlib.util.spec_from_file_location("travel_itinerary_plugin", ROOT / "__init__.py")
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        context = FakeContext()

        module.register(context)

        self.assertEqual(set(context.skills), {"travel-itinerary-builder"})
        self.assertTrue(context.skills["travel-itinerary-builder"].is_file())

    def test_skill_frontmatter_and_scope(self):
        content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(content.startswith("---\n"))
        self.assertIn("name: travel-itinerary-builder", content)
        self.assertIn("description:", content)
        self.assertNotIn("session-specific", content.lower())
        self.assertNotIn("private repository", content.lower())


class RendererTests(unittest.TestCase):
    def run_renderer(self, source, output):
        return subprocess.run(
            [sys.executable, str(RENDERER), str(source), str(output)],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_renders_generic_example_as_self_contained_html(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "itinerary.html"
            result = self.run_renderer(EXAMPLE, output)

            self.assertEqual(result.returncode, 0, result.stderr)
            html = output.read_text(encoding="utf-8")
            data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
            self.assertIn("<!doctype html>", html.lower())
            self.assertIn('<meta name="viewport"', html)
            self.assertEqual(html.count('class="day"'), len(data["days"]))
            self.assertNotIn("<script", html.lower())
            self.assertNotIn("javascript:", html.lower())
            for day in data["days"]:
                self.assertIn(day["title"], html)
                for item in day["items"]:
                    self.assertEqual(html.count(f">{item['name']}<"), 1)

    def test_rejects_non_https_links_without_replacing_output(self):
        data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        data["days"][0]["items"][0]["map_url"] = "javascript:alert(1)"
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "bad.json"
            output = Path(directory) / "itinerary.html"
            source.write_text(json.dumps(data), encoding="utf-8")
            output.write_text("keep me", encoding="utf-8")

            result = self.run_renderer(source, output)

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(output.read_text(encoding="utf-8"), "keep me")

    def test_rejects_duplicate_or_out_of_range_days(self):
        data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        data["days"][1]["date"] = data["days"][0]["date"]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "bad.json"
            output = Path(directory) / "itinerary.html"
            source.write_text(json.dumps(data), encoding="utf-8")

            result = self.run_renderer(source, output)

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
