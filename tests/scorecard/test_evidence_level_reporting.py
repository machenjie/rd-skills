from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _load_script(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class EvidenceLevelReportingTests(unittest.TestCase):
    def test_professional_scorecard_renders_not_collected_live_metrics(self) -> None:
        module = _load_script(
            "generate_professional_scorecard_for_reporting_test",
            "scripts/generate-professional-scorecard.py",
        )
        payload = {
            "status_summary": {
                "pass": 1,
                "partial": 0,
                "fail": 0,
                "unknown": 0,
                "not_collected": 1,
            },
            "evidence_levels": {
                "structural fixture": {
                    "status": "pass",
                    "meaning": "Local deterministic structure sample passed.",
                },
                "live pass-rate": {
                    "status": "not_collected",
                    "meaning": "Measured real-task success rate.",
                },
                "token overhead": {
                    "status": "not_collected",
                    "meaning": "Measured additional token cost.",
                },
                "turn overhead": {
                    "status": "not_collected",
                    "meaning": "Measured additional turn cost.",
                },
            },
            "dimensions": [],
            "profile_counts": {},
        }
        markdown = module.render_markdown(payload)
        self.assertIn("| live pass-rate | `not_collected` |", markdown)
        self.assertIn("| token overhead | `not_collected` |", markdown)
        self.assertIn("| turn overhead | `not_collected` |", markdown)
        self.assertNotIn("| live pass-rate | `pass` |", markdown)

    def test_public_benchmark_summary_has_evidence_level_column(self) -> None:
        module = _load_script(
            "generate_public_benchmark_summary_for_reporting_test",
            "scripts/generate-public-benchmark-summary.py",
        )
        payload = {
            "repository": {
                "name": "machenjie/rd-skills",
                "version": "0.1.0",
                "source_commit": "test",
            },
            "status_counts": {
                "pass": 1,
                "partial": 0,
                "fail": 0,
                "unknown": 0,
                "not_collected": 0,
            },
            "evidence_levels": {
                "structural fixture": {
                    "status": "pass",
                    "meaning": "Local deterministic structure sample passed.",
                },
                "live pass-rate": {
                    "status": "not_collected",
                    "meaning": "Measured real-task success rate.",
                },
            },
            "items": [
                {
                    "name": "Skill efficacy structural fixtures",
                    "status": "pass",
                    "evidence_level": "structural fixture",
                    "source": "reports/professional-scorecard.json",
                    "detail": '{"live_pass_rate": "not_collected"}',
                    "command": "python3 scripts/validate-skill-efficacy-benchmarks.py",
                }
            ],
            "known_unknowns": [],
            "refresh_commands": [],
        }
        markdown = module.render_markdown(payload)
        self.assertIn("| Area | Status | Evidence Level | Source | Detail | Refresh Command |", markdown)
        self.assertIn("| live pass-rate | `not_collected` |", markdown)
        self.assertIn("| Skill efficacy structural fixtures | `pass` | structural fixture |", markdown)


if __name__ == "__main__":
    unittest.main()
