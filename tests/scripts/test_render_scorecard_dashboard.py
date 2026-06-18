from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "render-scorecard-dashboard.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("render_scorecard_dashboard", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status_summary": {"pass": 2, "partial": 1, "fail": 1, "unknown": 1, "not_collected": 1},
        "profile_counts": {
            "recommended": {"status": "pass", "detail": "recommended top-level count is 19"},
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
        "dimensions": [
            {
                "name": "Profile build reproducibility",
                "status": "pass",
                "detail": "all profiles match",
                "source": "dist/universal",
                "fix_hint": "Rebuild profiles.",
            },
            {
                "name": "Open-source readiness",
                "status": "partial",
                "detail": "owner license decision required",
                "source": "docs/OPEN_SOURCE_READINESS.md",
                "fix_hint": "Owner must choose a license.",
            },
            {
                "name": "Example coverage",
                "status": "fail",
                "detail": "example route drift",
                "source": "examples/",
                "fix_hint": "Repair showcase examples.",
            },
            {
                "name": "Marketplace index validation",
                "status": "unknown",
                "detail": "not run",
                "source": "scripts/validate-marketplace-index.py",
                "fix_hint": "Run marketplace validators.",
            },
            {
                "name": "Installation validation",
                "status": "not_collected",
                "detail": "not collected",
                "source": "scripts/validate-installation.py",
                "fix_hint": "Run installation validation.",
            },
        ],
        "validation_commands": [{"command": "python3 scripts/validate-examples.py"}],
    }


class RenderScorecardDashboardTests(unittest.TestCase):
    def test_fail_statuses_appear_in_repair_hints(self) -> None:
        module = _load_module()
        rendered = module.render_dashboard(_payload())
        self.assertIn("`fail` Example coverage: Repair showcase examples.", rendered)
        self.assertIn("### High", rendered)

    def test_unknown_and_not_collected_are_not_rendered_as_pass(self) -> None:
        module = _load_module()
        rendered = module.render_dashboard(_payload())
        self.assertIn("| Marketplace index validation | `unknown` |", rendered)
        self.assertIn("- Installation validation: scripts/validate-installation.py", rendered)
        self.assertNotIn("| Marketplace index validation | `pass` |", rendered)

    def test_evidence_levels_render_not_collected_live_metrics(self) -> None:
        module = _load_module()
        rendered = module.render_dashboard(_payload())
        self.assertIn("## Evidence Levels", rendered)
        self.assertIn("| live pass-rate | `not_collected` |", rendered)
        self.assertIn("| token overhead | `not_collected` |", rendered)
        self.assertIn("| turn overhead | `not_collected` |", rendered)
        self.assertNotIn("| live pass-rate | `pass` |", rendered)

    def test_open_source_partial_is_visible(self) -> None:
        module = _load_module()
        rendered = module.render_dashboard(_payload())
        self.assertIn("| Open-source readiness | `partial` | owner license decision required |", rendered)

    def test_dashboard_generation_is_deterministic_for_fixed_payload(self) -> None:
        module = _load_module()
        payload = _payload()
        self.assertEqual(module.render_dashboard(payload), module.render_dashboard(payload))

    def test_readme_generated_block_check_catches_stale_content(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            scorecard = tmp_path / "scorecard.json"
            dashboard = tmp_path / "dashboard.md"
            readme = tmp_path / "README.md"
            scorecard.write_text(json.dumps(_payload()), encoding="utf-8")
            dashboard.write_text(module.render_dashboard(_payload()), encoding="utf-8")
            readme.write_text(
                "# README\n\n"
                f"{module.README_START}\n"
                "| Evidence | Status | Source |\n"
                "| --- | --- | --- |\n"
                "| stale | `pass` | stale |\n"
                f"{module.README_END}\n",
                encoding="utf-8",
            )
            self.assertEqual(
                module.main(
                    [
                        "--scorecard",
                        str(scorecard),
                        "--out",
                        str(dashboard),
                        "--readme",
                        str(readme),
                        "--check",
                    ]
                ),
                1,
            )


if __name__ == "__main__":
    unittest.main()
