from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _load_scorecard_module():
    spec = importlib.util.spec_from_file_location(
        "generate_professional_scorecard_for_test",
        ROOT / "scripts" / "generate-professional-scorecard.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PromotedEvidenceBoundaryTests(unittest.TestCase):
    def test_generated_candidate_does_not_count_as_measured_skill_efficacy(self) -> None:
        module = _load_scorecard_module()
        with tempfile.TemporaryDirectory() as tmp_s:
            root = Path(tmp_s)
            fixture_dir = root / "evals" / "skill-efficacy"
            fixture_dir.mkdir(parents=True)
            for index in range(3):
                (fixture_dir / f"reviewed-{index}.yaml").write_text(
                    "\n".join(
                        [
                            "schema_version: 1",
                            "verdict:",
                            "  status: structural_pass",
                            "metrics:",
                            "  token_overhead_pct: not_collected",
                            "  turn_overhead_pct: not_collected",
                            "",
                        ]
                    ),
                    encoding="utf-8",
                )
            (fixture_dir / "candidate.yaml").write_text(
                "\n".join(
                    [
                        "schema_version: 1",
                        "generated_from_telemetry: true",
                        "requires_human_review: true",
                        "source_suggestion_id: trajectory-sess-stale_validation-5",
                        "verdict:",
                        "  status: measured_pass",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            status, detail_text = module.skill_efficacy_status(root)

        detail = json.loads(detail_text)
        self.assertEqual(status, "pass")
        self.assertEqual(detail["fixtures"], 3)
        self.assertEqual(detail["candidate_fixtures_ignored"], 1)
        self.assertNotIn("measured_pass", detail["verdicts"])
        self.assertEqual(detail["live_pass_rate"], "not_collected")
        self.assertEqual(detail["token_overhead"], "not_collected")
        self.assertEqual(detail["turn_overhead"], "not_collected")


if __name__ == "__main__":
    unittest.main()
