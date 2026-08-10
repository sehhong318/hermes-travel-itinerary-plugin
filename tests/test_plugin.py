import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "travel-itinerary-builder"
SKILL_MD = SKILL_DIR / "SKILL.md"
RENDERER = SKILL_DIR / "scripts" / "render_itinerary.py"
EXAMPLE = SKILL_DIR / "templates" / "itinerary.example.json"
ALL_SKILLS = {
    "travel-itinerary-builder",
    "tabelog-budget-food-research",
    "japan-transit-routing",
    "jp-restaurant-search",
}
REFERENCES = {
    "existing-itinerary-project-workflow.md",
    "map-linked-itinerary-revisions.md",
    "renderer-verification.md",
    "reusable-travel-artifact-sanitization.md",
    "travel-expense-integration.md",
}
TEXT_SUFFIXES = {".md", ".py", ".yaml", ".yml", ".json", ".txt"}
CREDENTIAL_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    "AWS access key": re.compile(r"AKIA[A-Z0-9]{16}"),
    "bot token": re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{30,}\b"),
}


class FakeContext:
    def __init__(self):
        self.skills = {}

    def register_skill(self, name, path):
        self.skills[name] = Path(path)


class PluginTests(unittest.TestCase):
    def test_registers_bundled_skill(self):
        spec = importlib.util.spec_from_file_location(
            "travel_itinerary_plugin", ROOT / "__init__.py"
        )
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        context = FakeContext()

        module.register(context)

        self.assertEqual(set(context.skills), ALL_SKILLS)
        for name in ALL_SKILLS:
            self.assertTrue(context.skills[name].is_file())

    def test_skill_metadata_matches_plugin_release(self):
        skill = SKILL_MD.read_text(encoding="utf-8")
        manifest = (ROOT / "plugin.yaml").read_text(encoding="utf-8")

        self.assertTrue(skill.startswith("---\n"))
        self.assertIn("name: travel-itinerary-builder", skill)
        self.assertIn("version: 2.0.1", skill)
        self.assertIn("version: 2.0.1", manifest)
        self.assertNotIn("Sheets", manifest)
        self.assertNotIn("OAuth", manifest)
        self.assertNotIn("MCP", manifest)
        self.assertIn("trip-expenses", skill)
        self.assertNotIn("Google Sheets", skill)
        self.assertNotIn("OAuth", skill)

    def test_all_linked_references_are_packaged(self):
        skill = SKILL_MD.read_text(encoding="utf-8")
        packaged = {path.name for path in (SKILL_DIR / "references").glob("*.md")}

        self.assertEqual(packaged, REFERENCES)
        for filename in REFERENCES:
            path = SKILL_DIR / "references" / filename
            self.assertTrue(path.is_file())
            self.assertGreater(path.stat().st_size, 0)
            self.assertIn(f"references/{filename}", skill)

    def test_expense_module_preserves_ledger_and_currency_boundaries(self):
        content = (
            SKILL_DIR / "references" / "travel-expense-integration.md"
        ).read_text(encoding="utf-8")

        self.assertIn("independent ledger", content)
        self.assertIn("Never add unlike currencies", content)
        self.assertIn("examples and hypothetical fixtures as non-production data", content)
        self.assertIn("unauthenticated private access remains denied", content)
        self.assertIn("source and runtime", content)

    def test_readme_documents_complete_install_and_usage(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("hermes plugins install", readme)
        self.assertIn("hermes plugins enable travel-itinerary", readme)
        self.assertIn("/skill travel-itinerary:travel-itinerary-builder", readme)
        self.assertIn("Install as an editable local skill", readme)
        self.assertIn("How to use it", readme)
        self.assertIn("Add a private trip-expense view", readme)
        self.assertIn("packaged Transit client", readme)
        self.assertIn("Tabelog access is best-effort", readme)
        self.assertIn("export_itinerary.py", readme)
        self.assertNotIn("Google Sheets", readme)
        self.assertNotIn("OAuth", readme)
        self.assertNotIn("MCP", readme)
        self.assertNotIn("raw.githubusercontent.com", readme)

    def test_public_tree_has_no_credentials_or_absolute_private_paths(self):
        failures = []
        for path in ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts or path.suffix not in TEXT_SUFFIXES:
                continue
            content = path.read_text(encoding="utf-8")
            if re.search(r"/(?:home|Users|opt/data)/", content):
                failures.append(f"absolute private path in {path.relative_to(ROOT)}")
            for label, pattern in CREDENTIAL_PATTERNS.items():
                if pattern.search(content):
                    failures.append(f"{label} pattern in {path.relative_to(ROOT)}")

        self.assertEqual(failures, [])


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
