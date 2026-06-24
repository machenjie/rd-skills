#!/usr/bin/env python3
"""Validate a structured logging design decision."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_LOGGING_FIELDS = (
    "log_types",
    "placement",
    "events",
    "levels",
    "fields",
    "redaction",
    "cardinality_controls",
)
FORBIDDEN_FIELD_MARKERS = (
    "raw url query",
    "raw query",
    "token",
    "password",
    "authorization header",
    "cookie",
    "raw request body",
    "raw webhook body",
    "raw body",
    "api key",
    "secret",
    "private key",
    "signature",
    "session identifier",
)
CORRELATION_FIELDS = {"trace_id", "span_id", "request_id", "correlation_id"}


def validate_logging_decision(
    decision: Any,
    *,
    context: dict[str, Any] | None = None,
    label: str = "logging_decision",
) -> list[str]:
    """Return validation errors for one logging decision object."""
    if not isinstance(decision, dict):
        return [f"{label}: decision must be an object"]
    context = context or {}
    needed = decision.get("needed")
    if needed is False:
        return _no_log_errors(label, decision)
    if needed is not True:
        return [f"{label}: needed must be true or false"]

    errors: list[str] = []
    for field in REQUIRED_LOGGING_FIELDS:
        if not _string_list(decision.get(field)):
            errors.append(f"{label}: {field} must be non-empty when needed=true")

    log_types = {item.casefold() for item in _string_list(decision.get("log_types"))}
    levels = {item.upper() for item in _string_list(decision.get("levels"))}
    fields = {item.casefold() for item in _string_list(decision.get("fields"))}
    text = _decision_text(decision, context)
    rationale = str(decision.get("rationale", "")).casefold()

    errors.extend(_forbidden_field_errors(label, fields))
    if "ERROR" in levels and _looks_like_expected_validation(text) and not _terminal_failure_rationale(rationale):
        errors.append(f"{label}: expected validation errors must not be ERROR without terminal failure rationale")
    if "ERROR" in levels and _looks_like_retry_intermediate(text) and not _has_final_failure_distinction(decision):
        errors.append(f"{label}: retry intermediate failures must not be ERROR without final-failure distinction")
    if {"audit", "diagnostic"} <= log_types and not _audit_diagnostic_separated(text):
        errors.append(f"{label}: audit and diagnostic logs require separate sink/retention/rationale")
    if "INFO" in levels and _looks_high_frequency(text) and not _has_hot_path_control(text):
        errors.append(f"{label}: high-frequency INFO logs require sampling, rate limit, aggregation, or metric alternative")
    if "security" in log_types and not _security_fields_present(fields):
        errors.append(f"{label}: security logs require denial category/reason and policy fields")
    if _is_integration_log(log_types, text) and not _integration_fields_present(fields):
        errors.append(f"{label}: integration logs require dependency, status, duration, and error_category/error_code fields")
    if _cross_boundary_path(text) and not (fields | {item.casefold() for item in _string_list(decision.get("correlation"))}) & CORRELATION_FIELDS:
        errors.append(f"{label}: cross-service/request/job paths require trace_id, span_id, request_id, or correlation_id")
    if not _string_list(decision.get("tests_or_validation")) and not _string_list(context.get("tests_or_validation")):
        errors.append(f"{label}: needed=true requires tests_or_validation or process TDD logging/security tests")
    return errors


def _no_log_errors(label: str, decision: dict[str, Any]) -> list[str]:
    rationale = str(decision.get("rationale", "")).strip()
    if not rationale:
        return [f"{label}: needed=false requires rationale"]
    text = _decision_text(decision, {})
    alternatives = ("metric", "trace", "validation", "test", "assertion", "public behavior", "grading")
    if not any(marker in text for marker in alternatives):
        return [f"{label}: needed=false requires metric, trace, validation, test, or public-behavior alternative"]
    return []


def _forbidden_field_errors(label: str, fields: set[str]) -> list[str]:
    errors: list[str] = []
    for field in sorted(fields):
        normalized = field.replace("_", " ").replace("-", " ")
        if any(marker in normalized for marker in FORBIDDEN_FIELD_MARKERS):
            errors.append(f"{label}: forbidden secret-bearing/raw field {field!r}")
    return errors


def _looks_like_expected_validation(text: str) -> bool:
    return any(marker in text for marker in ("expected validation", "validation error", "invalid input", "bad request", "ordinary 404", "not found"))


def _terminal_failure_rationale(rationale: str) -> bool:
    return any(marker in rationale for marker in ("terminal", "final failure", "operation finally failed", "user impact", "data impact", "lost side effect", "requires investigation"))


def _looks_like_retry_intermediate(text: str) -> bool:
    return "retry" in text and any(marker in text for marker in ("intermediate", "attempt", "retryable", "backoff"))


def _has_final_failure_distinction(decision: dict[str, Any]) -> bool:
    text = _decision_text(decision, {})
    levels = {item.upper() for item in _string_list(decision.get("levels"))}
    return "WARN" in levels and any(marker in text for marker in ("terminal", "final", "dlq", "exhausted", "final_failure"))


def _audit_diagnostic_separated(text: str) -> bool:
    return any(marker in text for marker in ("separate sink", "separate retention", "separated sink", "separated retention")) or (
        "separate" in text and "retention" in text
    )


def _looks_high_frequency(text: str) -> bool:
    return any(marker in text for marker in ("high-frequency", "hot path", "per-event", "per call", "loop", "every request", "per iteration"))


def _has_hot_path_control(text: str) -> bool:
    return any(marker in text for marker in ("sampling", "sample", "rate limit", "rate-limit", "aggregate", "metric", "debug-only"))


def _security_fields_present(fields: set[str]) -> bool:
    has_policy = "policy" in fields
    has_category = bool(fields & {"denial_category", "category", "error_category", "reason"})
    return has_policy and has_category


def _is_integration_log(log_types: set[str], text: str) -> bool:
    return any("integration" in item or "dependency" in item for item in log_types) or "dependency call" in text


def _integration_fields_present(fields: set[str]) -> bool:
    has_duration = bool(fields & {"duration", "duration_ms", "latency_ms"})
    has_error = bool(fields & {"error_category", "error_code"})
    return {"dependency", "status"} <= fields and has_duration and has_error


def _cross_boundary_path(text: str) -> bool:
    return any(marker in text for marker in ("cross-service", "request", "job", "queue", "worker", "retry", "dependency", "webhook"))


def _decision_text(*values: Any) -> str:
    parts: list[str] = []
    for value in values:
        parts.extend(_flatten_text(value))
    return " ".join(parts).casefold()


def _flatten_text(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [part for key, item in value.items() for part in [str(key), *_flatten_text(item)]]
    if isinstance(value, list):
        return [part for item in value for part in _flatten_text(item)]
    if value is None:
        return []
    return [str(value)]


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _read_payload(path: Path | None) -> Any:
    text = sys.stdin.read() if path is None or str(path) == "-" else path.read_text(encoding="utf-8")
    payload = json.loads(text)
    if isinstance(payload, dict) and isinstance(payload.get("logging_decision"), dict):
        return payload["logging_decision"]
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decision", nargs="?", type=Path, help="Logging decision JSON file, or stdin when omitted.")
    args = parser.parse_args(argv)
    try:
        decision = _read_payload(args.decision)
    except Exception as exc:
        print(f"validate-logging-design: ERROR: invalid JSON: {exc}", file=sys.stderr)
        return 1
    errors = validate_logging_decision(decision)
    if errors:
        for error in errors:
            print(f"validate-logging-design: ERROR: {error}", file=sys.stderr)
        return 1
    print("validate-logging-design: logging decision is valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
