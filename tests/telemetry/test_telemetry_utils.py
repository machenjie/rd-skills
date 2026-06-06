from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"


def load_telemetry_utils():
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    spec = importlib.util.spec_from_file_location(
        "telemetry_utils_for_test", SCRIPTS_DIR / "telemetry_utils.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TelemetryUtilsTests(unittest.TestCase):
    def test_dump_yaml_round_trips_nested_structure(self) -> None:
        telemetry_utils = load_telemetry_utils()
        from validation_utils import load_yaml_text

        data = {
            "id": "case-1",
            "flag": True,
            "expected": {
                "skills": ["backend-change-builder", "security-privacy-gate"],
                "quality_gates": ["security gate", "test gate"],
            },
            "suggestions": [
                {"id": "s1", "type": "missed_router", "severity": "high"},
            ],
        }
        text = telemetry_utils.dump_yaml(data)
        back = load_yaml_text(text, Path("x"))
        self.assertEqual(back["id"], "case-1")
        self.assertTrue(back["flag"])
        self.assertEqual(
            back["expected"]["skills"],
            ["backend-change-builder", "security-privacy-gate"],
        )
        self.assertEqual(back["expected"]["quality_gates"], ["security gate", "test gate"])
        self.assertEqual(back["suggestions"][0]["id"], "s1")

    def test_extract_route_manifest_from_fenced_block(self) -> None:
        telemetry_utils = load_telemetry_utils()
        text = (
            "Some prose.\n\n"
            "```yaml\n"
            "changeforge_route:\n"
            "  schema_version: 1\n"
            "  selected_skills:\n"
            "    - backend-change-builder\n"
            "  required_quality_gates:\n"
            "    - security gate\n"
            "```\n"
        )
        manifest = telemetry_utils.extract_route_manifest(text)
        self.assertIsNotNone(manifest)
        self.assertEqual(manifest["selected_skills"], ["backend-change-builder"])

    def test_extract_route_manifest_absent(self) -> None:
        telemetry_utils = load_telemetry_utils()
        self.assertIsNone(telemetry_utils.extract_route_manifest("no manifest here"))

    def test_read_report_summary_from_json(self) -> None:
        telemetry_utils = load_telemetry_utils()
        import json
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            path.write_text(
                json.dumps({"summary": {"sessions": 3, "missed_router": 1}}),
                encoding="utf-8",
            )
            summary = telemetry_utils.read_report_summary(path)
        self.assertEqual(summary["sessions"], 3)
        self.assertEqual(summary["missed_router"], 1)

    def test_load_registry_names_returns_real_skills(self) -> None:
        telemetry_utils = load_telemetry_utils()
        names = telemetry_utils.load_registry_names(ROOT / "src" / "registry")
        self.assertIn("backend-change-builder", names["skills"])
        self.assertIn("security gate", names["gates"])


if __name__ == "__main__":
    unittest.main()
