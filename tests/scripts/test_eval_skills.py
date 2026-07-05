from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "eval-skills.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("eval_skills", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class EvalSkillsTests(unittest.TestCase):
    def _write_dimension_reports(self, reports: Path) -> None:
        reports.mkdir(parents=True, exist_ok=True)
        (reports / "skill-professionalism-depth.json").write_text(
            json.dumps(
                {
                    "average_professionalism_score": 90.0,
                    "items_checked": 2,
                    "items": [
                        {
                            "warnings": [
                                {"severity": "review-required"},
                                {"severity": "advisory"},
                            ]
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        (reports / "skill-efficacy-eval.json").write_text(
            json.dumps(
                {
                    "average_efficacy_score": 80.0,
                    "benchmarks_checked": 3,
                    "measured_count": 0,
                    "structural_count": 3,
                    "warning_count": 1,
                }
            ),
            encoding="utf-8",
        )

    def test_aggregates_existing_dimension_reports_without_running_generators(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            reports = Path(tmp)
            self._write_dimension_reports(reports)
            report = module.build_skill_evaluation_report(
                reports,
                ["professionalism_depth", "efficacy"],
                run_generators=False,
            )
        self.assertEqual(report.dimensions_checked, 2)
        self.assertEqual(report.overall_score, 86.0)
        self.assertEqual(report.overall_status, "partial")

    def test_cli_writes_aggregate_reports_from_existing_dimension_reports(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            reports = Path(tmp)
            self._write_dimension_reports(reports)
            exit_code = module.main(["--reports-dir", tmp, "--no-run"])
            payload = json.loads((reports / "skill-evaluation.json").read_text(encoding="utf-8"))
            markdown = (reports / "skill-evaluation.md").read_text(encoding="utf-8")
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["overall_score"], 86.0)
        self.assertIn("professionalism_depth", markdown)
        self.assertIn("efficacy", markdown)


if __name__ == "__main__":
    unittest.main()
