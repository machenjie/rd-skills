from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def _load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_logging_design_unit",
        ROOT / "scripts" / "validate-logging-design.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _valid_decision(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "needed": True,
        "log_types": ["diagnostic"],
        "placement": ["application service"],
        "events": ["operation_failed"],
        "levels": ["WARN"],
        "fields": ["operation", "error_category", "trace_id"],
        "redaction": ["token", "raw request body"],
        "correlation": ["trace_id", "request_id"],
        "cardinality_controls": ["route_template"],
        "tests_or_validation": ["test_logs_redact_token"],
        "rationale": "Diagnostic failure evidence without secret-bearing input.",
    }
    payload.update(overrides)
    return payload


class LoggingDesignValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = _load_validator()

    def errors(self, decision: dict[str, Any]) -> list[str]:
        return self.validator.validate_logging_decision(decision, label="logging_decision")

    def test_missing_required_design_fields_fails(self) -> None:
        errors = self.errors({"needed": True, "tests_or_validation": ["test_logs"]})
        for field in ("log_types", "placement", "events", "levels", "fields", "redaction", "cardinality_controls"):
            self.assertTrue(any(field in error for error in errors), field)

    def test_expected_validation_error_cannot_be_error_without_terminal_rationale(self) -> None:
        errors = self.errors(
            _valid_decision(
                events=["expected_validation_failed"],
                levels=["ERROR"],
                rationale="Expected validation error for bad request input.",
            )
        )
        self.assertTrue(any("expected validation errors" in error for error in errors))

    def test_retry_intermediate_error_needs_final_failure_distinction(self) -> None:
        errors = self.errors(
            _valid_decision(
                events=["retry_intermediate_attempt_failed"],
                levels=["ERROR"],
                fields=["operation", "error_category", "attempt", "retryable", "trace_id"],
                rationale="Retryable intermediate attempt failed during backoff.",
            )
        )
        self.assertTrue(any("retry intermediate failures" in error for error in errors))

    def test_forbidden_secret_or_raw_fields_fail(self) -> None:
        errors = self.errors(_valid_decision(fields=["operation", "raw URL query", "token", "trace_id"]))
        self.assertTrue(any("forbidden secret-bearing/raw field" in error for error in errors))

    def test_audit_and_diagnostic_need_separate_sink_or_retention(self) -> None:
        errors = self.errors(_valid_decision(log_types=["audit", "diagnostic"]))
        self.assertTrue(any("audit and diagnostic" in error for error in errors))

    def test_high_frequency_info_needs_sampling_or_metric_alternative(self) -> None:
        errors = self.errors(
            _valid_decision(
                events=["per_event_cache_miss"],
                levels=["INFO"],
                rationale="High-frequency hot path log on every request.",
            )
        )
        self.assertTrue(any("high-frequency INFO" in error for error in errors))

    def test_security_log_needs_policy_and_denial_category(self) -> None:
        errors = self.errors(_valid_decision(log_types=["security"], fields=["operation", "trace_id"]))
        self.assertTrue(any("security logs require" in error for error in errors))

    def test_integration_log_needs_dependency_status_duration_and_error_category(self) -> None:
        errors = self.errors(_valid_decision(log_types=["integration/dependency"], fields=["operation", "trace_id"]))
        self.assertTrue(any("integration logs require" in error for error in errors))

    def test_cross_boundary_log_needs_correlation_id(self) -> None:
        errors = self.errors(
            _valid_decision(
                fields=["operation", "error_category"],
                correlation=[],
                rationale="Cross-service request job path requires diagnosis.",
            )
        )
        self.assertTrue(any("cross-service/request/job paths" in error for error in errors))

    def test_no_log_rationale_with_metric_or_trace_alternative_passes(self) -> None:
        self.assertEqual(
            self.errors(
                {
                    "needed": False,
                    "rationale": "No product log is needed because metrics, traces, and public behavior tests cover the path.",
                }
            ),
            [],
        )

    def test_security_denial_log_passes(self) -> None:
        self.assertEqual(
            self.errors(
                _valid_decision(
                    log_types=["security"],
                    placement=["security boundary"],
                    events=["access_denied"],
                    levels=["WARN"],
                    fields=["operation", "policy", "error_category", "trace_id"],
                    redaction=["authorization header", "cookie", "token"],
                    rationale="Policy denial is diagnosable without raw credentials.",
                )
            ),
            [],
        )

    def test_retry_fallback_warn_and_terminal_error_passes(self) -> None:
        self.assertEqual(
            self.errors(
                _valid_decision(
                    events=["retry_attempt_failed", "fallback_final_failure"],
                    levels=["WARN", "ERROR"],
                    fields=["operation", "error_category", "attempt", "retryable", "fallback_used", "trace_id"],
                    rationale="WARN covers intermediate retryable attempts; ERROR is only for terminal final failure.",
                )
            ),
            [],
        )

    def test_audit_and_diagnostic_separated_passes(self) -> None:
        self.assertEqual(
            self.errors(
                _valid_decision(
                    log_types=["audit", "diagnostic"],
                    events=["payment_failed"],
                    levels=["WARN"],
                    fields=["operation", "result", "error_category", "trace_id"],
                    rationale="Audit and diagnostic records use separate sink and separate retention.",
                )
            ),
            [],
        )

    def test_hot_path_info_with_sampling_and_metrics_passes(self) -> None:
        self.assertEqual(
            self.errors(
                _valid_decision(
                    events=["cache_hot_path_summary"],
                    levels=["INFO"],
                    rationale="High-frequency hot path uses sampling and metrics instead of per-event INFO.",
                    cardinality_controls=["sampling", "metric alternative", "route_template"],
                )
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
