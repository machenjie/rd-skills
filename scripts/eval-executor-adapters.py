#!/usr/bin/env python3
"""Evaluate deterministic executor adapter fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from validation_utils import ValidationProblem, load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from runtime_governance import ClosureContract, EvidenceLedger  # noqa: E402
from runtime_governance.adapters import runtime_adapter_for  # noqa: E402


BASE_PATH = "/workspace/project"
DEFAULT_FIXTURE_DIR = ROOT / "evals" / "executor-adapter"
DEFAULT_REPORT_MD = ROOT / "reports" / "executor-adapter-eval.md"
DEFAULT_REPORT_JSON = ROOT / "reports" / "executor-adapter-eval.json"
DEFAULT_TELEMETRY_SAMPLE = ROOT / "reports" / "runtime-telemetry-sample.json"
RUNTIMES = ("codex", "claude", "copilot", "cline", "roo", "openhands")
REQUIRED_FIXTURE_FIELDS = (
    "id",
    "runtime",
    "input_payload",
    "expected_normalized_event",
    "expected_gate_result",
    "expected_evidence_delta",
    "expected_closure_effect",
    "privacy_expectations",
)
REQUIRED_COVERAGE_TARGETS = {
    "event_recognition",
    "degradation",
    "tool_category",
    "command_risk",
    "path_normalization",
    "permission_decision",
    "validation_outcome",
    "validation_freshness_after_edits",
    "closure_verdict",
    "privacy_redaction",
}
REQUIRED_PRESSURE_CASES = {
    "unknown_event",
    "unsupported_runtime_event",
    "secret_like_payload_field",
    "absolute_user_path",
    "full_command_output_field",
    "large_path_list_cap",
    "edit_after_validation",
    "failed_validation",
    "review_finding_without_repair",
    "repair_without_rereview",
    "copilot_unsupported_pre_tool",
    "claude_post_tool_failure",
    "codex_destructive_permission_request",
    "ready_closure",
    "ready_after_rereview",
    "required_unsupported_check_degraded_ready",
    "validation_pass_then_file_changed",
    "targeted_test_reported_as_full",
}


def _fixture_paths(fixtures_dir: Path) -> list[Path]:
    return sorted(path for runtime in RUNTIMES for path in (fixtures_dir / runtime).glob("*.yaml"))


def _load_fixture(path: Path) -> dict[str, Any]:
    loaded = load_yaml_file(path)
    if not isinstance(loaded, dict):
        raise ValidationProblem(f"{path}: fixture must be a mapping")
    return loaded


def _split_input_payload(raw_payload: Mapping[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload = deepcopy(dict(raw_payload))
    evidence_facts = payload.pop("evidence_facts", [])
    if not isinstance(evidence_facts, list):
        evidence_facts = []
    generator = payload.pop("generate_path_list", None)
    if isinstance(generator, Mapping):
        field = str(generator.get("field") or "changed_paths")
        prefix = str(generator.get("prefix") or "src/generated/file-")
        suffix = str(generator.get("suffix") or ".py")
        count = int(generator.get("count") or 0)
        start = int(generator.get("start") or 1)
        payload[field] = [f"{prefix}{index}{suffix}" for index in range(start, start + count)]
    return payload, [dict(item) for item in evidence_facts if isinstance(item, Mapping)]


def _evidence_delta(ledger: EvidenceLedger, event: Any) -> dict[str, Any]:
    return {
        "event_count": ledger.event_count,
        "normalized_event_supported": event.is_supported(),
        "read_paths": event.read_paths,
        "changed_files": ledger.changed_files,
        "deleted_files": ledger.deleted_files,
        "generated_files": ledger.generated_files,
        "bounded_path_count": len(event.bounded_paths),
        "privacy_redaction_count": len(event.privacy_redaction),
        "adapter_degradation_strength": ledger.adapter_degradation.strength,
        "validation_strength": ledger.validation.strength,
        "validation_freshness": ledger.validation.freshness,
        "validation_outcome": ledger.validation.outcome or "",
        "permission_strength": ledger.permission.strength,
        "permission_outcome": ledger.permission.outcome or "",
        "command_risk_outcome": ledger.command_risk.outcome or "",
        "review_strength": ledger.review.strength,
        "review_outcome": ledger.review.outcome or "",
        "repair_strength": ledger.repair.strength,
        "rereview_strength": ledger.rereview.strength,
    }


def _closure_effect(contract: ClosureContract) -> dict[str, Any]:
    return {
        "verdict": contract.verdict,
        "missing_evidence": contract.missing_evidence,
        "negative_evidence": contract.negative_evidence,
        "unsupported_checks": contract.unsupported_checks,
        "degraded_capabilities": contract.degraded_capabilities,
        "validation_status": contract.validation_status,
        "review_status": contract.review_status,
        "freshness": contract.freshness,
        "residual_risk": contract.residual_risk,
    }


def _active_unsupported_checks(
    fixture: Mapping[str, Any],
    capabilities: Any,
) -> list[str]:
    raw = fixture.get("active_unsupported_checks") or fixture.get("required_unsupported_checks") or []
    if not isinstance(raw, list):
        return []
    catalog = {str(check) for check in getattr(capabilities, "unsupported_checks", ())}
    values: list[str] = []
    for item in raw:
        check = str(item).strip()
        if check and check in catalog and check not in values:
            values.append(check)
    return values


def _degraded_for_unsupported(runtime: str, unsupported_checks: list[str]) -> list[str]:
    values: list[str] = []
    for check in unsupported_checks:
        token = str(check).strip().replace("-", "_").replace(" ", "_")
        if token:
            values.append(f"{runtime}_{token}_unsupported")
    return values


def _compare_subset(expected: Mapping[str, Any], actual: Mapping[str, Any], prefix: str) -> list[str]:
    failures: list[str] = []
    for key, expected_value in expected.items():
        if key.endswith("_not_contains"):
            actual_key = key[: -len("_not_contains")]
            actual_value = actual.get(actual_key)
            actual_items = actual_value if isinstance(actual_value, list) else []
            present = [item for item in expected_value if item in actual_items]
            if present:
                failures.append(f"{prefix}.{actual_key} unexpectedly contains {present!r}")
            continue
        if key.endswith("_contains"):
            actual_key = key[: -len("_contains")]
            actual_value = actual.get(actual_key)
            actual_items = actual_value if isinstance(actual_value, list) else []
            missing = [item for item in expected_value if item not in actual_items]
            if missing:
                failures.append(f"{prefix}.{actual_key} missing expected items {missing!r}")
            continue
        actual_value = actual.get(key)
        if isinstance(expected_value, Mapping):
            if not isinstance(actual_value, Mapping):
                failures.append(f"{prefix}.{key} expected mapping, got {actual_value!r}")
                continue
            failures.extend(_compare_subset(expected_value, actual_value, f"{prefix}.{key}"))
        elif actual_value != expected_value:
            failures.append(f"{prefix}.{key} expected {expected_value!r}, got {actual_value!r}")
    return failures


def _privacy_failures(
    event_payload: Mapping[str, Any],
    gate_payload: Mapping[str, Any],
    evidence_delta: Mapping[str, Any],
    closure_effect: Mapping[str, Any],
    expectations: Mapping[str, Any],
) -> list[str]:
    failures: list[str] = []
    safe_projection = json.dumps(
        {
            "normalized_event": event_payload,
            "gate_result": gate_payload,
            "evidence_delta": evidence_delta,
            "closure_effect": closure_effect,
        },
        sort_keys=True,
    )
    for blocked in expectations.get("blocked_strings") or []:
        if str(blocked) in safe_projection:
            failures.append(f"privacy blocked string leaked: {blocked!r}")
    redactions = event_payload.get("privacy_redaction")
    redaction_items = redactions if isinstance(redactions, list) else []
    for marker in expectations.get("redactions_include") or []:
        if marker not in redaction_items:
            failures.append(f"privacy marker missing: {marker!r}")
    if expectations.get("forbid_absolute_paths"):
        for field in ("bounded_paths", "read_paths", "changed_paths", "deleted_paths", "generated_paths"):
            for path in event_payload.get(field) or []:
                text = str(path)
                if text.startswith("/") or text.startswith("~/"):
                    failures.append(f"{field} contains absolute path {text!r}")
    max_bounded = expectations.get("max_bounded_path_count")
    if isinstance(max_bounded, int) and len(event_payload.get("bounded_paths") or []) > max_bounded:
        failures.append(f"bounded_paths exceeded cap {max_bounded}")
    return failures


def evaluate_fixture(path: Path) -> dict[str, Any]:
    """Evaluate one fixture and return a bounded case report."""
    failures: list[str] = []
    try:
        fixture = _load_fixture(path)
    except ValidationProblem as exc:
        return {"id": path.stem, "runtime": path.parent.name, "status": "fail", "failures": [str(exc)]}

    for field in REQUIRED_FIXTURE_FIELDS:
        if field not in fixture:
            failures.append(f"missing required field {field}")

    case_id = str(fixture.get("id") or path.stem)
    runtime = str(fixture.get("runtime") or path.parent.name)
    if runtime != path.parent.name:
        failures.append(f"runtime {runtime!r} must match parent directory {path.parent.name!r}")
    if runtime not in RUNTIMES:
        failures.append(f"unsupported fixture runtime {runtime!r}")

    input_payload = fixture.get("input_payload")
    if not isinstance(input_payload, Mapping):
        input_payload = {}
        failures.append("input_payload must be a mapping")
    adapter_payload, evidence_facts = _split_input_payload(input_payload)

    adapter = runtime_adapter_for(runtime)
    result = adapter.normalize_event(adapter_payload, base_path=BASE_PATH)
    event = result.normalized_event
    gate = result.gate_result
    ledger = EvidenceLedger()
    for fact in evidence_facts:
        ledger.add_fact(fact)
    ledger.add_normalized_event(event)
    active_unsupported = _active_unsupported_checks(fixture, result.capabilities)
    contract = ClosureContract.from_ledger(
        ledger,
        adapter=runtime,
        supported_checks=result.capabilities.supported_checks,
        unsupported_checks=active_unsupported,
        degraded_capabilities=[
            *event.capability_degradation,
            *_degraded_for_unsupported(runtime, active_unsupported),
        ],
    )

    event_payload = event.to_json_dict()
    gate_payload = gate.to_json_dict()
    evidence_delta = _evidence_delta(ledger, event)
    closure_effect = _closure_effect(contract)

    expected_normalized = fixture.get("expected_normalized_event")
    if isinstance(expected_normalized, Mapping):
        failures.extend(_compare_subset(expected_normalized, event_payload, "expected_normalized_event"))
    else:
        failures.append("expected_normalized_event must be a mapping")
    expected_gate = fixture.get("expected_gate_result")
    if isinstance(expected_gate, Mapping):
        failures.extend(_compare_subset(expected_gate, gate_payload, "expected_gate_result"))
    else:
        failures.append("expected_gate_result must be a mapping")
    expected_delta = fixture.get("expected_evidence_delta")
    if isinstance(expected_delta, Mapping):
        failures.extend(_compare_subset(expected_delta, evidence_delta, "expected_evidence_delta"))
    else:
        failures.append("expected_evidence_delta must be a mapping")
    expected_closure = fixture.get("expected_closure_effect")
    if isinstance(expected_closure, Mapping):
        failures.extend(_compare_subset(expected_closure, closure_effect, "expected_closure_effect"))
    else:
        failures.append("expected_closure_effect must be a mapping")
    privacy = fixture.get("privacy_expectations")
    if isinstance(privacy, Mapping):
        failures.extend(_privacy_failures(event_payload, gate_payload, evidence_delta, closure_effect, privacy))
    else:
        failures.append("privacy_expectations must be a mapping")

    return {
        "id": case_id,
        "runtime": runtime,
        "path": path.relative_to(ROOT).as_posix(),
        "status": "fail" if failures else "pass",
        "coverage_targets": list(fixture.get("coverage_targets") or []),
        "pressure_cases": list(fixture.get("pressure_cases") or []),
        "normalized_event": event_payload,
        "gate_result": gate_payload,
        "evidence_delta": evidence_delta,
        "closure_effect": closure_effect,
        "failures": failures,
    }


def evaluate_suite(fixtures_dir: Path = DEFAULT_FIXTURE_DIR) -> dict[str, Any]:
    """Evaluate all executor adapter fixtures."""
    paths = _fixture_paths(fixtures_dir)
    cases = [evaluate_fixture(path) for path in paths]
    coverage = {target for case in cases for target in case.get("coverage_targets", [])}
    pressure = {target for case in cases for target in case.get("pressure_cases", [])}
    runtimes = {case.get("runtime") for case in cases}
    suite_failures: list[str] = []
    missing_runtimes = sorted(set(RUNTIMES) - {str(runtime) for runtime in runtimes})
    missing_coverage = sorted(REQUIRED_COVERAGE_TARGETS - coverage)
    missing_pressure = sorted(REQUIRED_PRESSURE_CASES - pressure)
    if missing_runtimes:
        suite_failures.append("missing runtime fixture coverage: " + ", ".join(missing_runtimes))
    if missing_coverage:
        suite_failures.append("missing coverage targets: " + ", ".join(missing_coverage))
    if missing_pressure:
        suite_failures.append("missing pressure cases: " + ", ".join(missing_pressure))

    failed_cases = [case["id"] for case in cases if case.get("status") != "pass"]
    status = "fail" if failed_cases or suite_failures else "pass"
    runtime_counts = Counter(str(case.get("runtime")) for case in cases)
    summary = {
        "status": status,
        "case_count": len(cases),
        "passed": sum(1 for case in cases if case.get("status") == "pass"),
        "failed": len(failed_cases),
        "failed_cases": failed_cases,
        "suite_failures": suite_failures,
        "runtime_counts": dict(sorted(runtime_counts.items())),
        "coverage_targets": sorted(coverage),
        "pressure_cases": sorted(pressure),
        "live_pass_rate": {
            "status": "not_collected",
            "detail": "deterministic local fixtures do not measure real-task success rate",
        },
        "token_overhead": {
            "status": "not_collected",
            "detail": "deterministic local fixture run does not measure token overhead",
        },
        "turn_overhead": {
            "status": "not_collected",
            "detail": "deterministic local fixture run does not measure turn overhead",
        },
        "telemetry_sample": {
            "status": "generated" if cases else "not_collected",
            "detail": "sanitized fixture-derived bounded telemetry sample",
        },
    }
    return {
        "schema_version": 1,
        "generated_by": "scripts/eval-executor-adapters.py",
        "claim_boundary": (
            "Deterministic local fixtures validate adapter structure, bounded privacy behavior, "
            "and closure-policy reactions. They do not measure live pass-rate, empirical performance, "
            "token overhead, or turn overhead."
        ),
        "status": status,
        "summary": summary,
        "cases": cases,
    }


def telemetry_sample_from_eval(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Build a bounded telemetry sample from evaluated fixture facts."""
    cases = [case for case in payload.get("cases", []) if isinstance(case, Mapping)]
    closure_verdicts = Counter(str((case.get("closure_effect") or {}).get("verdict")) for case in cases)
    runtime_counts = Counter(str(case.get("runtime")) for case in cases)
    unsupported_checks = sorted(
        {
            str(check)
            for case in cases
            for check in ((case.get("closure_effect") or {}).get("unsupported_checks") or [])
        }
    )
    validation_freshness_cases = [
        {
            "case_id": str(case.get("id")),
            "validation_freshness": str((case.get("evidence_delta") or {}).get("validation_freshness")),
        }
        for case in cases
        if (case.get("evidence_delta") or {}).get("validation_freshness") not in {None, "", "unknown"}
    ]
    return {
        "schema_version": 1,
        "generated_by": "scripts/eval-executor-adapters.py",
        "source": "deterministic-fixture-bounded-facts",
        "runtime": "mixed-fixture-runtime-sample",
        "runtime_counts": dict(sorted(runtime_counts.items())),
        "event_count": len(cases),
        "normalized_event_kinds": sorted(
            {
                str((case.get("normalized_event") or {}).get("event_kind"))
                for case in cases
                if (case.get("normalized_event") or {}).get("event_kind")
            }
        ),
        "degraded_event_count": sum(
            1
            for case in cases
            if (case.get("normalized_event") or {}).get("capability_degradation")
        ),
        "validation_freshness_cases": validation_freshness_cases,
        "closure_verdicts": dict(sorted(closure_verdicts.items())),
        "unsupported_checks": unsupported_checks,
        "privacy_redaction_count": sum(
            int((case.get("evidence_delta") or {}).get("privacy_redaction_count") or 0)
            for case in cases
        ),
        "token_overhead": {"status": "not_collected"},
        "turn_overhead": {"status": "not_collected"},
    }


def render_markdown(payload: Mapping[str, Any]) -> str:
    """Render a human-readable executor adapter eval report."""
    summary = payload["summary"]
    lines = [
        "# Executor Adapter Evaluation",
        "",
        "This generated report uses deterministic local fixtures. It is structural evidence only; live pass-rate, token overhead, and turn overhead remain `not_collected` unless separately measured.",
        "",
        "## Summary",
        "",
        f"- Status: `{payload['status']}`",
        f"- Cases: {summary['case_count']}",
        f"- Passed: {summary['passed']}",
        f"- Failed: {summary['failed']}",
        f"- Live pass-rate: `{summary['live_pass_rate']['status']}`",
        f"- Token overhead: `{summary['token_overhead']['status']}`",
        f"- Turn overhead: `{summary['turn_overhead']['status']}`",
        f"- Telemetry sample: `{summary['telemetry_sample']['status']}`",
        "",
        "## Coverage",
        "",
        "- Runtimes: " + ", ".join(f"{key}={value}" for key, value in summary["runtime_counts"].items()),
        "- Coverage targets: " + ", ".join(summary["coverage_targets"]),
        "- Pressure cases: " + ", ".join(summary["pressure_cases"]),
        "",
    ]
    if summary["suite_failures"]:
        lines.extend(["## Suite Failures", ""])
        lines.extend(f"- {failure}" for failure in summary["suite_failures"])
        lines.append("")

    lines.extend(
        [
            "## Cases",
            "",
            "| Case | Runtime | Status | Event | Gate | Closure | Privacy Redactions |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for case in payload["cases"]:
        event = case["normalized_event"]
        gate = case["gate_result"]
        closure = case["closure_effect"]
        redactions = ", ".join(event.get("privacy_redaction") or []) or "none"
        lines.append(
            f"| {case['id']} | {case['runtime']} | `{case['status']}` | "
            f"`{event.get('event_kind')}` | `{gate.get('outcome')}` | "
            f"`{closure.get('verdict')}` | {redactions} |"
        )
    failed = [case for case in payload["cases"] if case.get("failures")]
    if failed:
        lines.extend(["", "## Failed Checks", ""])
        for case in failed:
            for failure in case["failures"]:
                lines.append(f"- {case['id']}: {failure}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures-dir", default=str(DEFAULT_FIXTURE_DIR))
    parser.add_argument("--out", default=str(DEFAULT_REPORT_MD))
    parser.add_argument("--json-out", default=str(DEFAULT_REPORT_JSON))
    parser.add_argument("--telemetry-out", default=str(DEFAULT_TELEMETRY_SAMPLE))
    args = parser.parse_args(argv)

    payload = evaluate_suite(Path(args.fixtures_dir))
    telemetry = telemetry_sample_from_eval(payload)
    out = Path(args.out)
    json_out = Path(args.json_out)
    telemetry_out = Path(args.telemetry_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    telemetry_out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_markdown(payload), encoding="utf-8")
    json_out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    telemetry_out.write_text(json.dumps(telemetry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote executor adapter eval to {out} and {json_out}")
    print(f"wrote runtime telemetry sample to {telemetry_out}")
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
