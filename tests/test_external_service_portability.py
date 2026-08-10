import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.error import URLError


ROOT = Path(__file__).resolve().parents[1]
TRANSIT_SCRIPT = (
    ROOT / "skills" / "japan-transit-routing" / "scripts" / "transit_client.py"
)
TABELOG_GUARD = (
    ROOT
    / "skills"
    / "tabelog-budget-food-research"
    / "scripts"
    / "tabelog_guard.py"
)
FALLBACK_EXPORTER = (
    ROOT
    / "skills"
    / "travel-itinerary-builder"
    / "scripts"
    / "export_itinerary.py"
)
EXAMPLE = (
    ROOT
    / "skills"
    / "travel-itinerary-builder"
    / "templates"
    / "itinerary.example.json"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeResponse:
    def __init__(self, payload: object):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        return self.payload


def valid_route_payload():
    return {
        "timezone": "Asia/Tokyo",
        "from": {"name": "梅田"},
        "to": {"name": "京都"},
        "journeys": [
            {
                "departureSecs": 100,
                "arrivalSecs": 200,
                "durationSecs": 100,
                "transferCount": 0,
                "legs": [
                    {
                        "departureSecs": 100,
                        "arrivalSecs": 200,
                        "mode": "RAIL",
                        "from": {"name": "梅田"},
                        "to": {"name": "京都"},
                        "routeName": "JR京都線",
                    }
                ],
            }
        ],
    }


class ExternalServicePortabilityTests(unittest.TestCase):
    def test_transit_client_returns_validated_suggestions(self):
        transit = load_module("transit_client", TRANSIT_SCRIPT)
        seen = []

        def opener(request, timeout):
            seen.append((request.full_url, timeout))
            return FakeResponse(
                {"places": [{"name": "梅田", "endpoint": "geo:34.7,135.5"}]}
            )

        result = transit.suggest_places("梅田", limit=3, opener=opener)

        self.assertEqual(result["places"][0]["endpoint"], "geo:34.7,135.5")
        self.assertIn("limit=3", seen[0][0])
        self.assertLessEqual(seen[0][1], 15)

    def test_transit_client_uses_keyword_timeout_with_standard_opener_contract(self):
        transit = load_module("transit_client_timeout", TRANSIT_SCRIPT)
        seen = []

        def keyword_only_opener(request, *, timeout):
            seen.append(timeout)
            return FakeResponse(
                {"places": [{"name": "梅田", "endpoint": "geo:34.7,135.5"}]}
            )

        transit.suggest_places("梅田", opener=keyword_only_opener)

        self.assertEqual(seen, [10])

    def test_transit_client_fails_with_actionable_error_when_service_is_down(self):
        transit = load_module("transit_client_error", TRANSIT_SCRIPT)

        def unavailable(_request, timeout):
            del timeout
            raise URLError("offline")

        with self.assertRaisesRegex(
            transit.TransitServiceError,
            "unavailable.*official operator",
        ):
            transit.suggest_places("梅田", opener=unavailable)

    def test_transit_client_rejects_malformed_payload(self):
        transit = load_module("transit_client_payload", TRANSIT_SCRIPT)

        with self.assertRaisesRegex(transit.TransitServiceError, "unexpected response"):
            transit.suggest_places(
                "梅田", opener=lambda _request, timeout: FakeResponse({"places": "bad"})
            )

    def test_transit_client_filters_walk_only_routes(self):
        transit = load_module("transit_client_route", TRANSIT_SCRIPT)
        payload = valid_route_payload()
        payload["journeys"].insert(
            0,
            {
                "departureSecs": 100,
                "arrivalSecs": 200,
                "durationSecs": 100,
                "transferCount": 0,
                "legs": [
                    {
                        "departureSecs": 100,
                        "arrivalSecs": 200,
                        "mode": None,
                        "from": {"name": "梅田"},
                        "to": {"name": "京都"},
                    }
                ],
            },
        )

        result = transit.plan_route(
            "geo:34.7,135.5",
            "geo:35.0,135.7",
            date="20260825",
            time="09:30",
            opener=lambda _request, timeout: FakeResponse(payload),
        )

        self.assertEqual(len(result["journeys"]), 1)
        self.assertEqual(result["journeys"][0]["legs"][0]["mode"], "RAIL")

    def test_transit_client_validates_route_inputs(self):
        transit = load_module("transit_client_validation", TRANSIT_SCRIPT)

        with self.assertRaisesRegex(ValueError, "YYYYMMDD"):
            transit.plan_route("geo:1,2", "geo:3,4", date="2026-08-25", time="09:30")
        with self.assertRaisesRegex(ValueError, "HH:MM"):
            transit.plan_route("geo:1,2", "geo:3,4", date="20260825", time="930")

    def test_transit_client_rejects_incomplete_nested_route_data(self):
        transit = load_module("transit_client_nested", TRANSIT_SCRIPT)
        malformed = valid_route_payload()
        del malformed["journeys"][0]["legs"][0]["departureSecs"]

        with self.assertRaisesRegex(transit.TransitServiceError, "unexpected response"):
            transit.plan_route(
                "geo:34.7,135.5",
                "geo:35.0,135.7",
                date="20260825",
                time="09:30",
                opener=lambda _request, timeout: FakeResponse(malformed),
            )

    def test_tabelog_guard_detects_challenges_and_wrong_pages(self):
        guard = load_module("tabelog_guard", TABELOG_GUARD)

        self.assertEqual(guard.classify_html("<title>Just a moment...</title>"), "blocked")
        self.assertEqual(
            guard.classify_html("<title>Checking your browser</title> CAPTCHA"),
            "blocked",
        )
        self.assertEqual(
            guard.classify_html("<title>Dining Hida | Tabelog</title>", "Expected Shop"),
            "wrong_page",
        )
        self.assertEqual(
            guard.classify_html("<title>Expected Shop | Tabelog</title>", "Expected Shop"),
            "ok",
        )
        self.assertEqual(
            guard.classify_html(
                "<title>Expected Shop Annex | Tabelog</title>", "Expected Shop"
            ),
            "wrong_page",
        )
        self.assertEqual(
            guard.classify_html(
                "<title>Expected Shop - Annex | Tabelog</title>", "Expected Shop"
            ),
            "wrong_page",
        )
        self.assertEqual(guard.classify_html("<title>Unrelated page</title>"), "invalid")

    def test_tabelog_guard_cli_reports_status_and_nonzero_on_block(self):
        blocked = subprocess.run(
            [sys.executable, str(TABELOG_GUARD), "--expected-title", "Expected Shop"],
            input="<title>Just a moment...</title>",
            text=True,
            capture_output=True,
            check=False,
        )
        ok = subprocess.run(
            [sys.executable, str(TABELOG_GUARD), "--expected-title", "Expected Shop"],
            input="<title>Expected Shop | Tabelog</title>",
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(blocked.returncode, 2)
        self.assertEqual(json.loads(blocked.stdout)["status"], "blocked")
        self.assertEqual(ok.returncode, 0)
        self.assertEqual(json.loads(ok.stdout)["status"], "ok")

    def test_local_fallback_exporter_preserves_source_and_writes_all_formats(self):
        original = EXAMPLE.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "itinerary.json"
            source.write_text(original, encoding="utf-8")
            for output_format in ("json", "csv", "markdown"):
                output = Path(directory) / f"exported-itinerary.{output_format}"
                result = subprocess.run(
                    [
                        sys.executable,
                        str(FALLBACK_EXPORTER),
                        str(source),
                        str(output),
                        "--format",
                        output_format,
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(output.is_file())
                self.assertGreater(output.stat().st_size, 20)
            self.assertEqual(source.read_text(encoding="utf-8"), original)
            overwrite = subprocess.run(
                [
                    sys.executable,
                    str(FALLBACK_EXPORTER),
                    str(source),
                    str(source),
                    "--format",
                    "json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(overwrite.returncode, 0)
            self.assertEqual(source.read_text(encoding="utf-8"), original)

    def test_skills_document_optional_dependencies_and_fallbacks(self):
        transit = (ROOT / "skills/japan-transit-routing/SKILL.md").read_text(
            encoding="utf-8"
        )
        transit_notes = (
            ROOT / "skills/japan-transit-routing/references/transit-api-notes.md"
        ).read_text(encoding="utf-8")
        award = (ROOT / "skills/jp-restaurant-search/SKILL.md").read_text(
            encoding="utf-8"
        )
        budget = (ROOT / "skills/tabelog-budget-food-research/SKILL.md").read_text(
            encoding="utf-8"
        )
        travel = (ROOT / "skills/travel-itinerary-builder/SKILL.md").read_text(
            encoding="utf-8"
        )
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        manifest = (ROOT / "plugin.yaml").read_text(encoding="utf-8")
        combined = "\n".join(
            [transit, transit_notes, award, budget, travel, readme, manifest]
        )

        self.assertNotIn("registered in `~/.hermes/config.yaml`", transit)
        self.assertNotIn("Get REAL Japan", transit)
        self.assertNotIn("Registered state:", transit_notes)
        self.assertNotIn("Transit API is the replacement", transit_notes)
        self.assertIn("Historical observations", transit_notes)
        self.assertNotIn("Stealth + residential-proxy Browserbase session", award)
        self.assertNotIn("proxies: true", award)
        self.assertNotIn("curl-only", budget)
        for stale_claim in (
            "20260824",
            "svt=1900",
            "sleep 4-5",
            "load with plain curl",
            "Silver ≈",
            "list-rst__",
            "≥3.4",
            "3+ ⭐",
            "user-verified Aug 2026",
            "Midosuji every",
            "LstCos=",
            "Pg=",
        ):
            self.assertNotIn(stale_claim, budget)
        folded = combined.casefold()
        for unsupported in ("mcp", "google sheets", "oauth", "gsheets-sync"):
            self.assertNotIn(unsupported, folded)
        self.assertIn("scripts/export_itinerary.py", travel)
        self.assertNotIn("api=1?query=", combined)
        for document in (transit, award, budget):
            self.assertIn("Fallback", document)


if __name__ == "__main__":
    unittest.main()
