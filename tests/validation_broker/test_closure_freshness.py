from __future__ import annotations

import sys
import tempfile
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
        self.assertEqual(result["closure_outcome"], "degraded_ready")

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


    def test_generic_go_package_command_keeps_package_path(self) -> None:
        assessment = assess_validation_closure(
            "Ran cd crypto-common && go test -count=1 ./exchange, passed, exit 0. Residual risk: targeted package validation only.",
            {},
        )
        result = assessment["validation_result"]
        self.assertEqual(result["command"], "cd crypto-common && go test -count=1 ./exchange")
        self.assertEqual(result["outcome"], "pass")
        self.assertEqual(result["covered_paths"], ["crypto-common/exchange/**"])

    def test_multi_go_command_ledger_combines_crypto_module_coverage(self) -> None:
        assessment = assess_validation_closure(
            """Validation freshness: fresh after latest material edit. Residual risk: full suite not run; live integration not run.
validation_command_ledger:
  - command: cd crypto-common && go test -count=1 ./exchange
    outcome: pass
    scope: module
    covered_paths:
      - crypto-common/exchange/**
  - command: cd crypto-one && go test -count=1 ./collector/coininfo ./processor/cryptoai/app/notification
    outcome: pass
    scope: targeted
    covered_paths:
      - crypto-one/collector/coininfo/**
      - crypto-one/processor/cryptoai/app/notification/**
  - command: git diff --check
    outcome: pass
    scope: narrow
    covered_checks:
      - whitespace
""",
            {
                "changed_paths": [
                    "crypto-common/exchange/market_tape.go",
                    "crypto-one/collector/coininfo/fetcher.go",
                    "crypto-one/processor/cryptoai/app/notification/render.go",
                ],
            },
        )
        result = broker_result(assessment)

        self.assertEqual(result["coverage_alignment"]["aligned"], True)
        self.assertEqual(result["closure_outcome"], "degraded_ready")
        self.assertEqual(len(result["command_ledger"]), 3)

    def test_validation_command_ledger_keeps_covered_checks_separate_from_paths(self) -> None:
        assessment = assess_validation_closure(
            """Validation freshness: fresh after latest material edit.
validation_command_ledger:
  - command: git diff --check
    outcome: pass
    scope: narrow
    covered_checks:
      - whitespace
""",
            {"changed_paths": ["crypto-one/processor/cryptoai/app/notification/render.go"]},
        )
        result = broker_result(assessment)
        entry = result["command_ledger"][0]
        self.assertEqual(entry["covered_checks"], ["whitespace"])
        self.assertEqual(entry["covered_paths"], [])

    def test_git_diff_check_covers_whitespace_not_changed_path_behavior(self) -> None:
        assessment = assess_validation_closure(
            """Validation freshness: fresh after latest material edit.
validation_command_ledger:
  - command: git diff --check
    outcome: pass
    scope: narrow
    covered_checks:
      - whitespace
""",
            {"changed_paths": ["crypto-one/processor/cryptoai/app/notification/render.go"]},
        )
        result = broker_result(assessment)
        self.assertFalse(result["coverage_alignment"]["aligned"])
        self.assertIn(
            "crypto-one/processor/cryptoai/app/notification/render.go",
            result["coverage_alignment"]["unknown_paths"],
        )

    def test_targeted_go_validation_with_residual_risk_degraded_ready(self) -> None:
        assessment = assess_validation_closure(
            (
                "Ran cd crypto-one && go test -count=1 ./processor/cryptoai/app/notification, passed, exit 0. "
                "Residual risk: targeted package validation only; full suite not run; live integration not run."
            ),
            {"changed_paths": ["crypto-one/processor/cryptoai/app/notification/render.go"]},
        )
        result = broker_result(assessment)

        self.assertEqual(result["coverage_alignment"]["aligned"], True)
        self.assertEqual(result["closure_outcome"], "degraded_ready")

    def test_structured_failed_command_followed_by_pass_stays_blocked(self) -> None:
        assessment = assess_validation_closure(
            """Residual risk: validation failure remains.
validation_command_ledger:
  - command: cd crypto-one && go test -count=1 ./processor/cryptoai/app/notification
    outcome: fail
    scope: targeted
  - command: git diff --check
    outcome: pass
    scope: narrow
""",
            {"changed_paths": ["crypto-one/processor/cryptoai/app/notification/render.go"]},
        )
        result = broker_result(assessment)

        self.assertIn("validation_failed", result["negative_evidence"])
        self.assertEqual(result["closure_outcome"], "blocked")

    def test_generic_go_and_cargo_commands_stop_at_result_sentence(self) -> None:
        go_assessment = assess_validation_closure("Ran go test -count=1 ./exchange. It passed.", {})
        cargo_assessment = assess_validation_closure("Ran cargo test -p foo.bar. It passed.", {})
        wildcard_assessment = assess_validation_closure("Ran go test ./..., passed, exit 0.", {})
        self.assertEqual(go_assessment["validation_result"]["command"], "go test -count=1 ./exchange")
        self.assertEqual(cargo_assessment["validation_result"]["command"], "cargo test -p foo.bar")
        self.assertEqual(wildcard_assessment["validation_result"]["command"], "go test ./...")

    def test_read_only_turn_does_not_report_missing_validation(self) -> None:
        assessment = assess_validation_closure(
            "Reviewed the files. No code changed.",
            {"read_evidence_seen": True},
        )
        result = broker_result(assessment)

        self.assertEqual(result["selected_scope"], "none")
        self.assertEqual(result["negative_evidence"], [])
        self.assertEqual(result["closure_outcome"], "ready")

    def test_project_validators_yaml_go_command_covers_crypto_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_dir = root / ".changeforge"
            config_dir.mkdir()
            (config_dir / "validators.yaml").write_text(
                """validators:
  - id: crypto-one-notification
    path_patterns:
      - crypto-one/processor/cryptoai/app/notification/**
    cwd: crypto-one
    command: go test -count=1 ./processor/cryptoai/app/notification
    scope: targeted
    proves:
      - notification formatting behavior
    covered_risk_surfaces:
      - user-visible-notification
""",
                encoding="utf-8",
            )
            assessment = assess_validation_closure(
                "Ran cd crypto-one && go test -count=1 ./processor/cryptoai/app/notification, passed, exit 0. Residual risk: targeted package validation only; full suite not run.",
                {
                    "repo_root": str(root),
                    "changed_paths": ["crypto-one/processor/cryptoai/app/notification/messages.go"],
                },
            )
        result = broker_result(assessment)
        self.assertNotIn("changed_path_without_validator", result["negative_evidence"])
        self.assertEqual(result["coverage_alignment"]["unknown_paths"], [])

    def test_invalid_validators_yaml_degrades_not_crash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_dir = root / ".changeforge"
            config_dir.mkdir()
            (config_dir / "validators.yaml").write_text("validators: [", encoding="utf-8")
            assessment = assess_validation_closure(
                "Ran python3 -m unittest discover -s tests, passed, exit 0. Residual risk: validator config parse issue.",
                {"repo_root": str(root), "changed_paths": ["service/foo.py"]},
            )
        result = broker_result(assessment)
        self.assertIn("validator_config_parse_error:validators.yaml", result["residual_risk"])


if __name__ == "__main__":
    unittest.main()
