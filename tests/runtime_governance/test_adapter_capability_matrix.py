from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from runtime_governance.adapters import adapter_capabilities_for, coverage_matrix, runtime_adapter_for  # noqa: E402
from runtime_governance.evidence import EvidenceLedger, EvidenceStrength, Freshness  # noqa: E402
from runtime_governance.gates import GateOutcome  # noqa: E402


class AdapterCapabilityMatrixTests(unittest.TestCase):
    def test_matrix_rows_include_required_machine_fields(self) -> None:
        rows = {row["adapter"]: row for row in coverage_matrix()}
        for runtime in ("codex", "claude", "copilot", "generic", "cline", "roo", "openhands", "gemini-cli", "goose"):
            with self.subTest(runtime=runtime):
                row = rows[runtime]
                self.assertIsInstance(row["supported_events"], list)
                self.assertIsInstance(row["unsupported_events"], list)
                self.assertIsInstance(row["advisory_context_support"], bool)
                self.assertIsInstance(row["stop_block_supported"], bool)
                self.assertIsInstance(row["visibility"], dict)
                for field in (
                    "read_paths",
                    "changed_paths",
                    "command_kind",
                    "command_risk",
                    "validation_outcome",
                    "permission_decision",
                    "rollback_checkpoint",
                ):
                    self.assertIn(row["visibility"][field], {"none", "partial", "full"})
                self.assertEqual(row["fail_open_policy"], "degraded_or_unsupported_checks_require_residual_risk")
                self.assertIsInstance(row["fail_closed_allowed_checks"], list)
                self.assertIsInstance(row["degraded_checks"], list)

    def test_codex_unsupported_event_degrades(self) -> None:
        result = runtime_adapter_for("codex").normalize_event({"runtime": "codex", "hook_event_name": "PostToolBatch"})

        self.assertEqual(result.normalized_event.event_kind, "post_tool_batch")
        self.assertEqual(result.gate_result.outcome, GateOutcome.DEGRADED.value)
        self.assertIn("codex_post_tool_batch_unsupported", result.normalized_event.capability_degradation)

    def test_claude_supported_failure_event_normalizes_supported(self) -> None:
        result = runtime_adapter_for("claude").normalize_event(
            {"runtime": "claude", "hookEventName": "PostToolUseFailure", "toolName": "Bash", "exitCode": 1}
        )

        self.assertEqual(result.normalized_event.event_kind, "post_tool_use_failure")
        self.assertEqual(result.gate_result.outcome, GateOutcome.PASS.value)
        self.assertEqual(result.normalized_event.capability_degradation, [])

    def test_generic_validation_outcome_none_is_weak_unknown(self) -> None:
        event = runtime_adapter_for("generic").normalize_event(
            {
                "runtime": "generic",
                "event_name": "PostToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "pytest"},
                "exit_code": 0,
            }
        ).normalized_event
        ledger = EvidenceLedger()
        ledger.add_normalized_event(event)

        self.assertEqual(event.validation_outcome, "unknown")
        self.assertIn("generic_validation_outcome_visibility_none", event.capability_degradation)
        self.assertEqual(ledger.validation.strength, EvidenceStrength.WEAK.value)
        self.assertEqual(ledger.validation.freshness, Freshness.UNKNOWN.value)

    def test_staged_targets_do_not_claim_lifecycle_hooks_or_fail_closed(self) -> None:
        for runtime in ("cline", "roo"):
            with self.subTest(runtime=runtime):
                capabilities = adapter_capabilities_for(runtime)
                self.assertEqual(capabilities.supported_events, ())
                self.assertFalse(capabilities.stop_block_supported)
                self.assertEqual(capabilities.fail_closed_allowed_checks, ())
                self.assertIn("Stop", capabilities.unsupported_events)


if __name__ == "__main__":
    unittest.main()
