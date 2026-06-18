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


class TrajectoryRepairRereviewTests(unittest.TestCase):
    def test_repair_after_review_requires_later_rereview(self) -> None:
        records = complete_records()
        records.insert(
            -1,
            {
                "timestamp_utc": "2026-06-01T00:05:30Z",
                "session_id": "sess",
                "event_name": "PostToolUse",
                "runtime": "codex",
                "turn_stage": "repair",
                "tool_name": "apply_patch",
                "changed_paths": ["src/app.py"],
                "repair_evidence_seen": True,
                "validation_command_detected": True,
                "validation_evidence_detected": True,
                "validation_result_outcome": "pass",
            },
        )
        records.insert(
            -1,
            {
                "timestamp_utc": "2026-06-01T00:05:40Z",
                "session_id": "sess",
                "event_name": "PostToolUse",
                "runtime": "codex",
                "turn_stage": "test",
                "command_program": "python3",
                "validation_command_detected": True,
                "validation_evidence_detected": True,
                "validation_result_outcome": "pass",
            },
        )
        trajectory = build_trajectory(records, repo_hash="repo", session_id="sess")
        assert trajectory is not None
        report = analyze_trajectory(trajectory)
        self.assertEqual(report["verdict"], "needs_repair")
        self.assertEqual(report["repair_rereview_status"], "needs_review")
        self.assertIn("repair_without_rereview", report["issue_counts"])

    def test_repair_followed_by_independent_rereview_is_not_repair_gap(self) -> None:
        records = complete_records()
        records.insert(
            -1,
            {
                "timestamp_utc": "2026-06-01T00:05:30Z",
                "session_id": "sess",
                "event_name": "PostToolUse",
                "runtime": "codex",
                "turn_stage": "repair",
                "tool_name": "apply_patch",
                "changed_paths": ["src/app.py"],
                "repair_evidence_seen": True,
                "validation_command_detected": True,
                "validation_evidence_detected": True,
                "validation_result_outcome": "pass",
            },
        )
        records.insert(
            -1,
            {
                "timestamp_utc": "2026-06-01T00:05:45Z",
                "session_id": "sess",
                "event_name": "PostToolUse",
                "runtime": "codex",
                "turn_stage": "review",
                "review_evidence_seen": True,
                "owner_skill": "backend-change-builder",
                "reviewer_skill": "ai-code-review-refactor",
            },
        )
        trajectory = build_trajectory(records, repo_hash="repo", session_id="sess")
        assert trajectory is not None
        report = analyze_trajectory(trajectory)
        self.assertNotIn("repair_without_rereview", report["issue_counts"])
        self.assertEqual(report["repair_rereview_status"], "passed")


if __name__ == "__main__":
    unittest.main()
