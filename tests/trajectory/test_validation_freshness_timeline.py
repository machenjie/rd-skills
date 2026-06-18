from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from trajectory import analyze_trajectory, build_trajectory


class ValidationFreshnessTimelineTests(unittest.TestCase):
    def test_stop_time_broker_stale_fact_overrides_event_order(self) -> None:
        trajectory = build_trajectory(
            [
                {
                    "timestamp_utc": "2026-06-01T00:00:00Z",
                    "session_id": "sess",
                    "event_name": "PostToolUse",
                    "runtime": "codex",
                    "turn_stage": "edit",
                    "tool_name": "apply_patch",
                    "changed_paths": ["src/validation_broker/validation_policy.py"],
                },
                {
                    "timestamp_utc": "2026-06-01T00:01:00Z",
                    "session_id": "sess",
                    "event_name": "Stop",
                    "runtime": "codex",
                    "validation_broker_result": {
                        "closure_outcome": "blocked",
                        "negative_evidence": ["stale_validation"],
                        "command_ledger": [
                            {
                                "command_kind": "narrow",
                                "command_display_safe": "python3 scripts/validate-validation-broker.py",
                                "scope": "narrow",
                                "outcome": "stale",
                                "finished_at_or_order": "1",
                                "covered_paths": ["src/validation_broker/**"],
                                "covered_risk_surfaces": ["validation-broker"],
                                "evidence_strength": "negative",
                            }
                        ],
                    },
                    "residual_risk_detected": True,
                },
            ],
            repo_hash="repo",
            session_id="sess",
        )
        assert trajectory is not None
        report = analyze_trajectory(trajectory)

        self.assertEqual(report["validation_freshness"], "stale")
        self.assertIn("stale_validation", report["issue_counts"])

    def test_read_only_turn_stays_not_applicable(self) -> None:
        trajectory = build_trajectory(
            [
                {
                    "timestamp_utc": "2026-06-01T00:00:00Z",
                    "session_id": "sess",
                    "event_name": "PostToolUse",
                    "runtime": "codex",
                    "turn_stage": "read",
                    "command_program": "rg",
                    "read_evidence_seen": True,
                    "read_paths": ["src/validation_broker/validation_policy.py"],
                    "command_risk_surfaces": ["validation-broker"],
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
        self.assertNotIn("missing_validation", report["issue_counts"])

    def test_adapter_closure_facts_are_preserved_in_timeline(self) -> None:
        trajectory = build_trajectory(
            [
                {
                    "timestamp_utc": "2026-06-01T00:00:00Z",
                    "session_id": "sess",
                    "event_name": "Stop",
                    "runtime": "copilot",
                    "adapter_name": "copilot",
                    "adapter_supported_checks": ["route_manifest", "changed_files"],
                    "adapter_unsupported_checks": ["pre_tool_advisory_context"],
                    "adapter_degraded_capabilities": [
                        "copilot_pre_tool_advisory_context_unsupported"
                    ],
                    "closure_contract_verdict": "degraded_ready",
                    "closure_contract_residual_risk": [
                        "unsupported runtime checks remain"
                    ],
                },
            ],
            repo_hash="repo",
            session_id="sess",
        )
        assert trajectory is not None
        facts = trajectory["steps"][0]["facts"]

        self.assertEqual(facts["adapter_name"], "copilot")
        self.assertEqual(
            facts["adapter_unsupported_checks"], ["pre_tool_advisory_context"]
        )
        self.assertEqual(facts["closure_contract_verdict"], "degraded_ready")


if __name__ == "__main__":
    unittest.main()
