from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from validation_broker import assess_validation_closure


def broker_result(assessment: dict[str, object]) -> dict[str, object]:
    value = assessment.get("validation_broker_result")
    assert isinstance(value, dict)
    return value


class ClosureFreshnessTests(unittest.TestCase):
    def test_command_present_without_outcome_is_not_closure_evidence(self) -> None:
        assessment = assess_validation_closure(
            "Ran python3 scripts/validate-hooks.py. Residual risk: pending outcome.",
            {
                "changed_paths": ["src/hook-runtime/scripts/changeforge_common.py"],
                "risk_surfaces": ["hook-runtime"],
            },
        )
        result = broker_result(assessment)

        self.assertFalse(assessment["strong_evidence"])
        self.assertIn("validation_command_without_outcome", result["negative_evidence"])
        self.assertEqual(result["command_ledger"][0]["outcome"], "not_verified")
        self.assertEqual(result["closure_outcome"], "needs_validation")

    def test_validation_before_final_edit_is_stale(self) -> None:
        assessment = assess_validation_closure(
            "Ran python3 scripts/validate-hooks.py, passed, exit 0. Residual risk: none.",
            {
                "changed_paths": ["src/hook-runtime/scripts/changeforge_common.py"],
                "risk_surfaces": ["hook-runtime"],
                "last_material_edit_index": 5,
                "last_validation_command_index": 4,
            },
        )
        result = broker_result(assessment)

        self.assertIn("stale_validation", result["negative_evidence"])
        self.assertEqual(result["freshness"]["status"], "stale")
        self.assertEqual(result["command_ledger"][0]["outcome"], "stale")
        self.assertEqual(result["closure_outcome"], "blocked")

    def test_targeted_check_reported_as_full_is_coverage_issue(self) -> None:
        assessment = assess_validation_closure(
            (
                "Ran python3 scripts/validate-hooks.py, passed, exit 0. "
                "Full regression passed. Residual risk: narrow check only."
            ),
            {
                "changed_paths": ["src/hook-runtime/scripts/changeforge_common.py"],
                "risk_surfaces": ["hook-runtime"],
            },
        )
        result = broker_result(assessment)

        self.assertIn("targeted_check_reported_as_full", result["negative_evidence"])
        self.assertEqual(result["coverage_alignment"]["aligned"], False)
        self.assertEqual(result["command_ledger"][0]["outcome"], "partial")
        self.assertEqual(result["closure_outcome"], "needs_validation")

    def test_changed_path_without_validator_records_residual_risk(self) -> None:
        assessment = assess_validation_closure(
            (
                "Ran python3 -m unittest discover -s tests, passed, exit 0. "
                "Residual risk: no validator mapping for the changed path."
            ),
            {"changed_paths": ["unmapped/file.xyz"]},
        )
        result = broker_result(assessment)

        self.assertIn("changed_path_without_validator", result["negative_evidence"])
        self.assertIn("no_validator:unmapped/file.xyz", result["residual_risk"])
        self.assertEqual(result["closure_outcome"], "needs_validation")

    def test_failed_command_followed_by_unrelated_pass_keeps_negative_evidence(self) -> None:
        assessment = assess_validation_closure(
            (
                "python3 scripts/validate-validation-broker.py failed with 1 failure. "
                "Then python3 -m unittest discover -s tests/telemetry passed, exit 0. "
                "Residual risk: validation failure remains."
            ),
            {"changed_paths": ["src/validation_broker/validation_policy.py"]},
        )
        result = broker_result(assessment)

        self.assertIn("validation_failed", result["negative_evidence"])
        self.assertEqual(result["command_ledger"][0]["outcome"], "failed")
        self.assertEqual(result["closure_outcome"], "blocked")

    def test_unsupported_adapter_degrades_but_does_not_pass_overclaim(self) -> None:
        assessment = assess_validation_closure(
            "Ran python3 scripts/validate-hooks.py, passed, exit 0. Residual risk: adapter unsupported.",
            {
                "changed_paths": ["src/hook-runtime/scripts/changeforge_common.py"],
                "risk_surfaces": ["hook-runtime"],
                "unsupported_adapter_events": ["PreToolUse"],
            },
        )
        result = broker_result(assessment)

        self.assertIn("unsupported_adapter_check", result["negative_evidence"])
        self.assertIn("unsupported_adapter:PreToolUse", result["residual_risk"])
        self.assertEqual(result["closure_outcome"], "degraded_ready")

    def test_read_only_turn_does_not_report_missing_validation(self) -> None:
        assessment = assess_validation_closure(
            "Reviewed the files. No code changed.",
            {"read_evidence_seen": True},
        )
        result = broker_result(assessment)

        self.assertEqual(result["selected_scope"], "none")
        self.assertEqual(result["negative_evidence"], [])
        self.assertEqual(result["closure_outcome"], "ready")


if __name__ == "__main__":
    unittest.main()
