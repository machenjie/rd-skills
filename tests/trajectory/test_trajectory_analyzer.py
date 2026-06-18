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


class TrajectoryAnalyzerTests(unittest.TestCase):
    def test_edit_before_read(self) -> None:
        trajectory = build_trajectory(
            [
                {
                    "timestamp_utc": "2026-06-01T00:00:00Z",
                    "session_id": "sess",
                    "event_name": "PostToolUse",
                    "runtime": "codex",
                    "turn_stage": "edit",
                    "tool_name": "apply_patch",
                    "changed_paths": ["src/app.py"],
                },
                {
                    "timestamp_utc": "2026-06-01T00:01:00Z",
                    "session_id": "sess",
                    "event_name": "Stop",
                    "runtime": "codex",
                },
            ],
            repo_hash="repo",
            session_id="sess",
        )
        assert trajectory is not None
        report = analyze_trajectory(trajectory)
        self.assertIn("edit_before_read", report["issue_counts"])

    def test_stale_validation(self) -> None:
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
        self.assertIn("stale_validation", report["issue_counts"])
        self.assertEqual(report["validation_freshness"], "stale")

    def test_repair_without_rereview(self) -> None:
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
                "validation_evidence_detected": True,
                "validation_result_outcome": "pass",
            },
        )
        trajectory = build_trajectory(records, repo_hash="repo", session_id="sess")
        assert trajectory is not None
        report = analyze_trajectory(trajectory)
        self.assertIn("repair_without_rereview", report["issue_counts"])
        self.assertEqual(report["review_integrity"], "fail")

    def test_stop_without_residual_risk(self) -> None:
        records = complete_records()
        records[-1] = dict(records[-1])
        records[-1]["residual_risk_detected"] = False
        trajectory = build_trajectory(records, repo_hash="repo", session_id="sess")
        assert trajectory is not None
        report = analyze_trajectory(trajectory)
        self.assertIn("stop_without_residual_risk", report["issue_counts"])

    def test_read_only_command_is_not_material_edit(self) -> None:
        trajectory = build_trajectory(
            [
                {
                    "timestamp_utc": "2026-06-01T00:00:00Z",
                    "session_id": "sess",
                    "event_name": "PostToolUse",
                    "runtime": "codex",
                    "turn_stage": "read",
                    "command_program": "rg",
                    "paths": ["src/app.py"],
                    "read_evidence_seen": True,
                    "risk_surfaces": ["read-only-command"],
                },
                {
                    "timestamp_utc": "2026-06-01T00:01:00Z",
                    "session_id": "sess",
                    "event_name": "Stop",
                    "runtime": "codex",
                },
            ],
            repo_hash="repo",
            session_id="sess",
        )
        assert trajectory is not None
        report = analyze_trajectory(trajectory)
        self.assertNotIn("missing_validation", report["issue_counts"])
        self.assertEqual(report["validation_freshness"], "not_applicable")
        self.assertEqual(report["closure_status"], "pass")

    def test_review_only_session_has_not_applicable_validation_freshness(self) -> None:
        trajectory = build_trajectory(
            [
                {
                    "timestamp_utc": "2026-06-01T00:00:00Z",
                    "session_id": "sess",
                    "event_name": "PostToolUse",
                    "runtime": "codex",
                    "turn_stage": "review",
                    "review_evidence_seen": True,
                    "review_findings": ["no issues"],
                },
                {
                    "timestamp_utc": "2026-06-01T00:01:00Z",
                    "session_id": "sess",
                    "event_name": "Stop",
                    "runtime": "codex",
                },
            ],
            repo_hash="repo",
            session_id="sess",
        )
        assert trajectory is not None
        report = analyze_trajectory(trajectory)
        self.assertEqual(report["validation_freshness"], "not_applicable")
        self.assertEqual(report["closure_status"], "pass")


if __name__ == "__main__":
    unittest.main()
