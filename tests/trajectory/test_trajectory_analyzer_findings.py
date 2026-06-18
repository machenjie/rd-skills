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


class TrajectoryAnalyzerFindingTests(unittest.TestCase):
    def test_plan_before_repository_context_has_finding_and_next_gate(self) -> None:
        records = complete_records()
        records[1] = dict(records[1])
        records[1].pop("repository_context_seen", None)
        trajectory = build_trajectory(records, repo_hash="repo", session_id="sess")
        assert trajectory is not None
        report = analyze_trajectory(trajectory)
        finding = _finding(report, "plan_before_repo_context")
        self.assertEqual(finding["required_next_gate"], "repository-context-map")
        self.assertEqual(report["verdict"], "degraded_ready")

    def test_command_without_outcome_needs_validation(self) -> None:
        records = complete_records()
        records[4] = dict(records[4])
        records[4].pop("validation_result_outcome", None)
        records[4]["validation_evidence_detected"] = False
        trajectory = build_trajectory(records, repo_hash="repo", session_id="sess")
        assert trajectory is not None
        report = analyze_trajectory(trajectory)
        self.assertIn("validation_without_outcome", report["issue_counts"])
        self.assertEqual(report["verdict"], "needs_validation")

    def test_self_review_requires_independent_review(self) -> None:
        records = complete_records()
        records[5] = dict(records[5])
        records[5]["reviewer_skill"] = "backend-change-builder"
        trajectory = build_trajectory(records, repo_hash="repo", session_id="sess")
        assert trajectory is not None
        report = analyze_trajectory(trajectory)
        self.assertIn("self_review", report["issue_counts"])
        self.assertEqual(report["verdict"], "needs_review")
        self.assertEqual(report["repair_rereview_status"], "needs_independent_review")

    def test_unsupported_adapter_closure_is_degraded_not_ready(self) -> None:
        records = complete_records()
        records[-1] = dict(records[-1])
        records[-1].update(
            {
                "adapter_name": "copilot",
                "adapter_unsupported_checks": ["pre_tool_advisory_context"],
                "adapter_degraded_capabilities": ["copilot_pre_tool_advisory_unsupported"],
                "closure_contract_verdict": "degraded_ready",
                "closure_contract_residual_risk": ["unsupported adapter check"],
            }
        )
        trajectory = build_trajectory(records, repo_hash="repo", session_id="sess")
        assert trajectory is not None
        report = analyze_trajectory(trajectory)
        self.assertIn("unsupported_adapter_overclaim", report["issue_counts"])
        self.assertEqual(report["verdict"], "degraded_ready")
        self.assertEqual(trajectory["adapter_degradations"][0]["adapter_name"], "copilot")

    def test_read_only_task_does_not_report_missing_validation(self) -> None:
        trajectory = build_trajectory(
            [
                {
                    "timestamp_utc": "2026-06-01T00:00:00Z",
                    "session_id": "sess",
                    "event_name": "PostToolUse",
                    "runtime": "codex",
                    "turn_stage": "read",
                    "tool_name": "rg",
                    "read_paths": ["src/app.py"],
                    "read_evidence_seen": True,
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
        self.assertEqual(report["verdict"], "ready")


def _finding(report: dict[str, object], issue_type: str) -> dict[str, object]:
    findings = report.get("findings")
    assert isinstance(findings, list)
    for finding in findings:
        if isinstance(finding, dict) and finding.get("type") == issue_type:
            return finding
    raise AssertionError(f"missing finding {issue_type}")


if __name__ == "__main__":
    unittest.main()
