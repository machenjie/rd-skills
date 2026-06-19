from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from runtime_governance import (  # noqa: E402
    EventKind,
    EvidenceLedger,
    EvidenceStrength,
    Freshness,
    NormalizedEvent,
)


class EvidenceLedgerTests(unittest.TestCase):
    def test_builds_strong_evidence_from_structured_facts(self) -> None:
        ledger = EvidenceLedger.from_telemetry_facts(
            [
                {
                    "event_name": "Stop",
                    "runtime": "codex",
                    "route_manifest_detected": True,
                    "manifest_selected_skills": ["change-forge-router"],
                    "manifest_selected_capabilities": ["implementation-structure-design"],
                    "manifest_required_references": ["references/routing-rules.md"],
                    "manifest_required_quality_gates": ["test gate"],
                    "read_evidence_seen": True,
                    "read_paths": ["src/runtime_governance/events.py"],
                    "implementation_preflight_complete": True,
                    "changed_paths": ["src/runtime_governance/events.py"],
                    "validation_command_detected": True,
                    "validation_evidence_detected": True,
                    "validation_result_outcome": "pass",
                    "validation_result_evidence_strength": "strong",
                    "validation_result_fresh_after_last_edit": "true",
                    "residual_risk_detected": True,
                }
            ]
        )
        self.assertEqual(ledger.route_manifest.strength, EvidenceStrength.STRONG.value)
        self.assertEqual(ledger.validation.strength, EvidenceStrength.STRONG.value)
        self.assertEqual(ledger.validation.freshness, Freshness.CURRENT.value)
        self.assertEqual(ledger.changed_files, ["src/runtime_governance/events.py"])

    def test_repository_context_seen_is_canonical_evidence(self) -> None:
        ledger = EvidenceLedger.from_telemetry_facts(
            [{"event_name": "Stop", "repository_context_seen": True}]
        )
        self.assertEqual(ledger.repository_context.strength, EvidenceStrength.STRONG.value)
        self.assertEqual(ledger.repository_context.freshness, Freshness.CURRENT.value)

    def test_permission_request_does_not_degrade_adapter(self) -> None:
        ledger = EvidenceLedger.from_telemetry_facts(
            [{"event_name": "PermissionRequest", "runtime": "codex"}]
        )
        self.assertEqual(ledger.adapter_degradation.strength, EvidenceStrength.NONE.value)

    def test_validation_command_without_outcome_is_weak(self) -> None:
        ledger = EvidenceLedger.from_telemetry_facts(
            [{"event_name": "PostToolUse", "validation_command_detected": True}]
        )
        self.assertEqual(ledger.validation.strength, EvidenceStrength.WEAK.value)
        self.assertEqual(ledger.validation.outcome, "no_outcome")
        self.assertFalse(ledger.validation.is_closure_evidence)

    def test_stale_validation_is_negative(self) -> None:
        ledger = EvidenceLedger.from_telemetry_facts(
            [
                {
                    "event_name": "Stop",
                    "validation_command_detected": True,
                    "validation_evidence_detected": True,
                    "validation_result_outcome": "pass",
                    "validation_result_evidence_strength": "strong",
                    "validation_result_fresh_after_last_edit": "false",
                }
            ]
        )
        self.assertEqual(ledger.validation.strength, EvidenceStrength.NEGATIVE.value)
        self.assertEqual(ledger.validation.freshness, Freshness.STALE.value)

    def test_later_edit_stales_prior_validation_event(self) -> None:
        ledger = EvidenceLedger()
        ledger.add_normalized_event(
            NormalizedEvent(
                event_id="validate-1",
                adapter="codex",
                event_kind=EventKind.POST_TOOL_USE.value,
                tool_category="test",
                command_outcome="pass",
                validation_candidate=True,
            )
        )
        ledger.add_normalized_event(
            NormalizedEvent(
                event_id="edit-1",
                adapter="codex",
                event_kind=EventKind.POST_TOOL_USE.value,
                tool_category="edit",
                changed_paths=["src/runtime_governance/evidence.py"],
            )
        )
        self.assertEqual(ledger.validation.strength, EvidenceStrength.NEGATIVE.value)
        self.assertEqual(ledger.validation.freshness, Freshness.STALE.value)
        self.assertEqual(ledger.validation.outcome, "stale")

    def test_changed_deleted_and_generated_paths_are_kept_separate(self) -> None:
        ledger = EvidenceLedger.from_telemetry_facts(
            [
                {
                    "event_name": "PostToolUse",
                    "changed_paths": ["src/a.py"],
                    "deleted_paths": ["src/old.py"],
                    "generated_paths": ["dist/a.py"],
                }
            ]
        )
        self.assertEqual(ledger.changed_files, ["src/a.py"])
        self.assertEqual(ledger.deleted_files, ["src/old.py"])
        self.assertEqual(ledger.generated_files, ["dist/a.py"])
        self.assertEqual(
            ledger.changed_files_by_status,
            {"changed": ["src/a.py"], "deleted": ["src/old.py"], "generated": ["dist/a.py"]},
        )

    def test_permission_denial_records_bounded_decision_without_raw_command(self) -> None:
        ledger = EvidenceLedger.from_telemetry_facts(
            [
                {
                    "event_name": "PermissionRequest",
                    "runtime": "codex",
                    "permission_decision": "deny",
                    "permission_reason": "raw command rm -rf /tmp/x --token=SECRET",
                    "command": "rm -rf /tmp/x --token=SECRET",
                }
            ]
        )
        serialized = ledger.to_json()
        self.assertEqual(ledger.permission.outcome, "deny")
        self.assertEqual(ledger.command_risk.outcome, "destructive")
        self.assertNotIn("SECRET", serialized)
        self.assertNotIn("--token", serialized)

    def test_config_change_after_validation_marks_validation_stale(self) -> None:
        ledger = EvidenceLedger()
        ledger.add_normalized_event(
            NormalizedEvent(
                event_id="validate-1",
                adapter="codex",
                event_kind=EventKind.POST_TOOL_USE.value,
                tool_category="test",
                command_outcome="pass",
                validation_candidate=True,
            )
        )
        ledger.add_normalized_event(
            NormalizedEvent(
                event_id="config-1",
                adapter="codex",
                event_kind=EventKind.CONFIG_CHANGED.value,
                changed_paths=["pyproject.toml"],
            )
        )
        self.assertEqual(ledger.config_change.strength, EvidenceStrength.PARTIAL.value)
        self.assertEqual(ledger.validation.freshness, Freshness.STALE.value)

    def test_broker_coverage_blocker_overrides_flat_pass(self) -> None:
        ledger = EvidenceLedger.from_telemetry_facts(
            [
                {
                    "event_name": "Stop",
                    "validation_command_detected": True,
                    "validation_evidence_detected": True,
                    "validation_result_outcome": "pass",
                    "validation_result_evidence_strength": "strong",
                    "validation_result_fresh_after_last_edit": "true",
                    "validation_broker_closure_outcome": "needs_validation",
                    "validation_broker_negative_evidence": [
                        "targeted_check_reported_as_full"
                    ],
                    "validation_broker_command_ledger": [
                        {
                            "outcome": "partial",
                            "evidence_strength": "partial",
                        }
                    ],
                }
            ]
        )
        self.assertEqual(ledger.validation.strength, EvidenceStrength.WEAK.value)
        self.assertFalse(ledger.validation.is_closure_evidence)

    def test_prose_mention_is_not_strong_evidence(self) -> None:
        ledger = EvidenceLedger.from_telemetry_facts(
            [{"event_name": "Stop", "message": "validation passed in prose"}]
        )
        self.assertEqual(ledger.validation.strength, EvidenceStrength.NONE.value)

    def test_json_round_trip(self) -> None:
        ledger = EvidenceLedger.from_telemetry_facts(
            [{"event_name": "Stop", "residual_risk_detected": True}]
        )
        self.assertEqual(EvidenceLedger.from_json(ledger.to_json()), ledger)


if __name__ == "__main__":
    unittest.main()
