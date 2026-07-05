from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from trajectory import analyze_trajectory, build_trajectory

from tests.trajectory.test_trajectory_builder import complete_records


class TrajectoryValidationFreshnessTests(unittest.TestCase):
    def test_validation_before_final_edit_is_stale(self) -> None:
        records = complete_records()
        records.insert(
            -1,
            {
                "timestamp_utc": "2026-06-01T00:05:30Z",
                "session_id": "sess",
                "event_name": "PostToolUse",
                "runtime": "codex",
                "turn_stage": "edit",
                "tool_name": "apply_patch",
                "changed_paths": ["src/app.py"],
            },
        )
        trajectory = build_trajectory(records, repo_hash="repo", session_id="sess")
        assert trajectory is not None
        report = analyze_trajectory(trajectory)
        self.assertEqual(report["validation_freshness"], "stale")
        self.assertEqual(report["verdict"], "needs_validation")
        self.assertIn("stale_validation", report["issue_counts"])

    def test_stale_broker_outcome_not_overwritten_by_later_unrelated_pass(self) -> None:
        records = complete_records()
        records[4] = dict(records[4])
        records[4]["validation_broker_command_ledger"] = [
            {
                "command_kind": "python3",
                "scope": "narrow",
                "outcome": "stale",
                "covered_paths": ["src/app.py"],
            }
        ]
        records.insert(
            -1,
            {
                "timestamp_utc": "2026-06-01T00:05:30Z",
                "session_id": "sess",
                "event_name": "PostToolUse",
                "runtime": "codex",
                "turn_stage": "test",
                "command_program": "python3",
                "validation_command_detected": True,
                "validation_evidence_detected": True,
                "validation_result_outcome": "pass",
                "changed_paths": [],
                "paths": ["docs/README.md"],
            },
        )
        trajectory = build_trajectory(records, repo_hash="repo", session_id="sess")
        assert trajectory is not None
        report = analyze_trajectory(trajectory)
        self.assertIn("stale_validation", report["issue_counts"])
        self.assertEqual(report["verdict"], "needs_validation")
        self.assertEqual(trajectory["validation_timeline"][0]["freshness"], "stale")


if __name__ == "__main__":
    unittest.main()
