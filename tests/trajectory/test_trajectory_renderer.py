from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from trajectory import analyze_trajectory, build_trajectory, render_json, render_markdown

from tests.trajectory.test_trajectory_builder import complete_records


class TrajectoryRendererTests(unittest.TestCase):
    def test_markdown_contains_required_sections(self) -> None:
        trajectory = build_trajectory(complete_records(), repo_hash="repo", session_id="sess")
        assert trajectory is not None
        report = analyze_trajectory(trajectory)
        text = render_markdown(trajectory, report)
        self.assertIn("## Stage Timeline", text)
        self.assertIn("## Changed/Read Paths", text)
        self.assertIn("## Validation Freshness", text)
        self.assertIn("## Review/Repair", text)
        self.assertIn("## Issues", text)
        self.assertIn("## Suggested Next Gates", text)

    def test_json_contains_report_and_trajectory(self) -> None:
        trajectory = build_trajectory(complete_records(), repo_hash="repo", session_id="sess")
        assert trajectory is not None
        report = analyze_trajectory(trajectory)
        payload = json.loads(render_json(trajectory, report))
        self.assertIn("trajectory", payload)
        self.assertIn("trajectory_report", payload)
        self.assertEqual(payload["trajectory_report"]["closure_status"], "pass")


if __name__ == "__main__":
    unittest.main()
