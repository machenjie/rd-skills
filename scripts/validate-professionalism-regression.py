#!/usr/bin/env python3
"""Gate professionalism regressions against a recorded authoring baseline.

This script is intentionally separate from the warning-only professionalism
evaluations. The evals keep producing advisory reports; this validator compares
the latest reports with config/professionalism-baseline.yaml and fails only on
new regressions or malformed inputs.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from validation_utils import ValidationProblem, load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = ROOT / "config" / "professionalism-baseline.yaml"
DEFAULT_REPORTS_DIR = ROOT / "reports"
DEFAULT_ROUTING_DIR = ROOT / "evals" / "routing"
DEFAULT_CONTENT_EXCEPTIONS = ROOT / "config" / "skill-content-exceptions.yaml"
DEFAULT_RELEASE_REVIEW_CONFIG = ROOT / "config" / "professionalism-release-review.yaml"

SKILL_EVAL_JSON = "skill-professionalism-eval.json"
COVERAGE_MATRIX_JSON = "professional-coverage-matrix.json"
BENCHMARKS_JSON = "professional-benchmarks-report.json"
CONTENT_AUDIT_JSON = "skill-content-audit.json"
AGENT_SAMPLES_JSON = "professional-agent-samples-report.json"
ROUTING_COVERAGE_JSON = "professional-routing-coverage.json"

REGRESSION_MD = "professionalism-regression-report.md"
REGRESSION_JSON = "professionalism-regression-report.json"
READINESS_MD = "professionalism-release-readiness.md"
READINESS_JSON = "professionalism-release-readiness.json"

GOOD_STATUSES = {"acceptable", "sample-grade"}
WEAK_STATUS = "weak"
EXPECTED_ROUTING_FIELDS = ("skills", "capabilities", "domain_extensions", "quality_gates")

DEFAULT_GLOBAL_THRESHOLDS = {
    "no_new_weak_professional_skill": True,
    "no_score_regression_more_than": 1.0,
    "max_new_warnings_count": 0,
    "max_known_warnings": {
        "evidence_contract_missing_what_proves": 0,
        "trigger_lacks_concrete_route_or_evidence": 0,
        "body_bloat_exception": None,
    },
    "no_new_missing_mode_matrix_for_professional_skill": True,
    "no_new_missing_proactive_triggers_for_core_skill": True,
    "no_new_missing_evidence_contract_for_core_skill": True,
    "no_new_reference_without_loading_hint": True,
    "no_new_empty_benchmark_case": True,
    "no_new_routing_case_without_forbidden": True,
}

KNOWN_WARNING_METADATA_FIELDS = (
    "owner",
    "accepted_reason",
    "review_after",
    "target_fix_phase",
    "is_release_blocking",
)

RELEASE_REVIEW_DECISIONS = {
    "accepted_for_current_release",
    "blocks_release",
    "defer_to_followup",
}

ENHANCED_FOUNDATION_CAPABILITIES = {
    "engineering-stage-professionalism",
    "agent-execution-discipline",
    "implementation-structure-design",
    "code-clarity-maintainability",
    "skill-authoring-expert",
}

KEY_FOUNDATION_CAPABILITIES = {
    "failure-diagnosis",
    "refactoring",
    "code-review",
    "test-strategy",
    "unit-testing",
    "integration-testing",
    "contract-testing",
    "e2e-testing",
    "regression-testing",
    "logging-error-handling",
    "idempotency-retry-design",
    "async-job-design",
    "transaction-consistency",
    "cache-design",
    "message-queue-design",
    "relational-database",
    "observability",
    "release-rollback",
    "language-idiom-enforcement",
    "language-testing-strategy",
    "language-performance-safety",
    "go-professional-usage",
    "python-professional-usage",
    "typescript-professional-usage",
    "java-jvm-professional-usage",
    "rust-professional-usage",
    "cpp-professional-usage",
    "sql-professional-usage",
    "shell-cli-professional-usage",
}


@dataclass
class Finding:
    category: str
    target: str
    message: str
    baseline_value: Any = None
    current_value: Any = None
    severity: str = "error"


@dataclass
class RegressionResult:
    generated_at: str
    mode: str
    status: str
    strict: bool
    report_only: bool
    blockers: list[Finding] = field(default_factory=list)
    warnings: list[Finding] = field(default_factory=list)
    known_warnings: list[Finding] = field(default_factory=list)
    baseline_changes: list[Finding] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)


class RegressionInputError(Exception):
    """Raised when required reports or baseline data are malformed."""


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    reports_dir = args.reports_dir
    reports_dir.mkdir(parents=True, exist_ok=True)
    try:
        reports = _load_required_reports(reports_dir)
        current = build_baseline_snapshot(
            reports,
            routing_dir=args.routing_dir,
            content_exceptions_path=args.content_exceptions,
        )
        if args.update_baseline:
            old = _load_optional_baseline(args.baseline)
            changes = diff_snapshots(old, current) if old else [
                Finding(
                    "baseline-created",
                    str(args.baseline),
                    "created professionalism baseline from current reports",
                    None,
                    "created",
                    "info",
                )
            ]
            args.baseline.parent.mkdir(parents=True, exist_ok=True)
            args.baseline.write_text(dump_yaml(current), encoding="utf-8")
            result = RegressionResult(
                generated_at=_now(),
                mode="update-baseline",
                status="updated",
                strict=args.strict,
                report_only=args.report_only,
                baseline_changes=changes,
            )
            result.summary = _summary(result)
            agent_strict = _run_promoted_agent_samples_strict(reports_dir)
            reports["agent_samples_strict"] = agent_strict.get("report", {})
            reports["routing_coverage"] = _load_optional_json_mapping(reports_dir / ROUTING_COVERAGE_JSON)
            _write_reports(
                result,
                current,
                reports,
                reports_dir,
                default_result=None,
                strict_result=None,
                agent_samples_strict=agent_strict,
                release_review_config_path=args.release_review_config,
            )
            _print_summary(result)
            return 0

        baseline = _load_baseline(args.baseline)
        result = compare_against_baseline(
            baseline,
            current,
            strict=args.strict,
            report_only=args.report_only,
        )
        default_result = result if not args.strict else compare_against_baseline(
            baseline,
            current,
            strict=False,
            report_only=args.report_only,
        )
        strict_result = result if args.strict else compare_against_baseline(
            baseline,
            current,
            strict=True,
            report_only=False,
        )
        agent_strict = _run_promoted_agent_samples_strict(reports_dir)
        reports["agent_samples_strict"] = agent_strict.get("report", {})
        reports["routing_coverage"] = _load_optional_json_mapping(reports_dir / ROUTING_COVERAGE_JSON)
        _write_reports(
            result,
            current,
            reports,
            reports_dir,
            default_result=default_result,
            strict_result=strict_result,
            agent_samples_strict=agent_strict,
            release_review_config_path=args.release_review_config,
        )
        _print_summary(result)
        if result.blockers and not args.report_only:
            return 1
        return 0
    except (RegressionInputError, OSError, json.JSONDecodeError, ValidationProblem) as exc:
        message = f"validate-professionalism-regression: ERROR: {exc}"
        print(message, file=sys.stderr)
        _write_input_error_report(reports_dir, str(exc), args)
        return 1


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS_DIR)
    parser.add_argument("--routing-dir", type=Path, default=DEFAULT_ROUTING_DIR)
    parser.add_argument("--content-exceptions", type=Path, default=DEFAULT_CONTENT_EXCEPTIONS)
    parser.add_argument("--release-review-config", type=Path, default=DEFAULT_RELEASE_REVIEW_CONFIG)
    parser.add_argument("--update-baseline", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--report-only", action="store_true")
    return parser.parse_args(argv)


def _load_required_reports(reports_dir: Path) -> dict[str, dict[str, Any]]:
    return {
        "skill_eval": _load_json_mapping(reports_dir / SKILL_EVAL_JSON),
        "coverage_matrix": _load_json_mapping(reports_dir / COVERAGE_MATRIX_JSON),
        "benchmarks": _load_json_mapping(reports_dir / BENCHMARKS_JSON),
        "content_audit": _load_optional_json_mapping(reports_dir / CONTENT_AUDIT_JSON),
        "agent_samples": _load_optional_json_mapping(reports_dir / AGENT_SAMPLES_JSON),
    }


def _load_json_mapping(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RegressionInputError(f"missing required report: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RegressionInputError(f"{path}: expected JSON object")
    return data


def _load_optional_json_mapping(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return _load_json_mapping(path)


def _run_promoted_agent_samples_strict(reports_dir: Path) -> dict[str, Any]:
    command = [
        sys.executable,
        str(ROOT / "scripts" / "eval-professional-agent-samples.py"),
        "--promoted-only",
        "--strict",
        "--reports-dir",
        str(reports_dir),
    ]
    completed = subprocess.run(
        command,
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=False,
    )
    report = _load_optional_json_mapping(reports_dir / AGENT_SAMPLES_JSON)
    return {
        "ran": True,
        "command": "python3 scripts/eval-professional-agent-samples.py --promoted-only --strict",
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "report": report,
    }


def _load_baseline(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RegressionInputError(
            f"missing baseline: {path}; run with --update-baseline after refreshing reports"
        )
    data = load_yaml_file(path)
    if not isinstance(data, dict):
        raise RegressionInputError(f"{path}: expected YAML mapping")
    return data


def _load_optional_baseline(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return _load_baseline(path)


def build_baseline_snapshot(
    reports: dict[str, dict[str, Any]],
    *,
    routing_dir: Path,
    content_exceptions_path: Path,
) -> dict[str, Any]:
    skill_eval = reports["skill_eval"]
    coverage_matrix = reports["coverage_matrix"]
    benchmarks = reports["benchmarks"]
    items = _mapping_list(skill_eval, "items", "skill professionalism report")
    rows = _mapping_list(coverage_matrix, "rows", "coverage matrix report")
    benchmark_results = _mapping_list(benchmarks, "results", "professional benchmarks report")
    items_by_name = {str(item.get("name")): item for item in items if item.get("name")}
    rows_by_name = {str(row.get("name")): row for row in rows if row.get("name")}

    professional_skills: dict[str, Any] = {}
    foundation_capabilities: dict[str, Any] = {}
    for name in sorted(rows_by_name):
        row = rows_by_name[name]
        item = items_by_name.get(name, {})
        entry = _skill_baseline_entry(item, row)
        if row.get("kind") == "professional-skill":
            professional_skills[name] = entry
        elif row.get("kind") == "foundation-capability":
            foundation_capabilities[name] = entry

    snapshot = {
        "schema_version": 1,
        "generated_at": _now(),
        "source_reports": {
            "skill_professionalism": f"reports/{SKILL_EVAL_JSON}",
            "professional_coverage_matrix": f"reports/{COVERAGE_MATRIX_JSON}",
            "professional_benchmarks": f"reports/{BENCHMARKS_JSON}",
        },
        "global_thresholds": dict(DEFAULT_GLOBAL_THRESHOLDS),
        "professional_skills": professional_skills,
        "foundation_capabilities": foundation_capabilities,
        "benchmarks": {
            "cases": _benchmark_case_baselines(benchmark_results),
            "cases_checked": int(benchmarks.get("cases_checked") or 0),
            "comparison_cases_checked": int(benchmarks.get("comparison_cases_checked") or 0),
            "errors_count": len(_string_list(benchmarks.get("errors"))),
        },
        "routing": _routing_baseline(routing_dir),
        "content_bloat": {
            "recorded_exceptions": _content_exception_paths(content_exceptions_path),
        },
    }
    snapshot["global_thresholds"]["max_known_warnings"] = _known_warning_type_budget(snapshot)
    return snapshot


def _mapping_list(report: dict[str, Any], key: str, context: str) -> list[dict[str, Any]]:
    value = report.get(key)
    if not isinstance(value, list):
        raise RegressionInputError(f"{context}: expected list field '{key}'")
    if not all(isinstance(item, dict) for item in value):
        raise RegressionInputError(f"{context}: field '{key}' must contain mappings")
    return value


def _skill_baseline_entry(item: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    warning_records = _warning_record_list(item.get("warnings")) or _warning_record_list(row.get("warnings"))
    likely_missing = _string_list(item.get("likely_missing_sections"))
    coverage = {
        "mode_matrix": _string(row.get("mode_matrix")),
        "proactive_triggers": _string(row.get("proactive_triggers")),
        "evidence_contract": _string(row.get("evidence_contract")),
        "output_contract": _string(row.get("output_contract")),
        "failure_modes": _string(row.get("failure_modes")),
        "quality_gate": _string(row.get("quality_gate")),
        "reference_loading_hint": _string(row.get("reference_loading_hint")),
        "anti_bloat_status": _string(row.get("anti_bloat_status")),
    }
    return {
        "path": _string(row.get("path") or item.get("path")),
        "kind": _string(row.get("kind") or item.get("kind")),
        "total_score": int(item.get("total") if item.get("total") is not None else row.get("score") or 0),
        "status": _string(item.get("status") or row.get("status")),
        "known_warnings_count": len(warning_records),
        "known_warnings": [
            _known_warning_record(record, _string(row.get("path") or item.get("path")))
            for record in warning_records
        ],
        "required_sections_present": not bool(likely_missing),
        "missing_required_sections": likely_missing,
        "benchmark_coverage_count": _coverage_count(row.get("benchmark_coverage")),
        "routing_coverage_count": _coverage_count(row.get("routing_coverage")),
        "coverage": coverage,
    }


def _benchmark_case_baselines(results: list[dict[str, Any]]) -> dict[str, Any]:
    cases: dict[str, Any] = {}
    for result in sorted(results, key=lambda item: str(item.get("path") or item.get("case_id"))):
        path = _string(result.get("path") or result.get("case_id"))
        if not path:
            continue
        summary = result.get("professional_delta_summary")
        if not isinstance(summary, dict):
            summary = {}
        cases[path] = {
            "expected_stage": _string(result.get("expected_stage")),
            "expected_skills": _string_list(result.get("expected_skills")),
            "expected_capabilities": _string_list(result.get("expected_capabilities")),
            "schema_status": _string(result.get("schema_status")),
            "comparison_status": _string(result.get("comparison_status")),
            "benchmark_quality_status": _string(result.get("benchmark_quality_status") or ("pass" if not result.get("errors") else "fail")),
            "baseline_defect_hits_count": len(_string_list(result.get("baseline_defect_hits"))),
            "with_skill_obligation_coverage_count": len(_string_list(result.get("with_skill_obligation_coverage"))),
            "with_skill_obligation_coverage": _string_list(result.get("with_skill_obligation_coverage")),
            "delta_score": int(result.get("delta_score") if result.get("delta_score") is not None else summary.get("delta_score") or 0),
            "remaining_gaps_count": len(_string_list(result.get("remaining_gaps") or summary.get("remaining_gaps"))),
            "remaining_gaps": _string_list(result.get("remaining_gaps") or summary.get("remaining_gaps")),
            "errors_count": len(_string_list(result.get("errors"))),
            "errors": _string_list(result.get("errors")),
        }
    return cases


def _known_warning_record(warning: Any, path: str) -> dict[str, Any]:
    source = _dict(warning)
    message = _warning_message(warning)
    warning_type = _string(source.get("type")) or _warning_type(message)
    release_relevance = _string(source.get("release_relevance")) or _inferred_release_relevance(
        path,
        warning_type,
        message,
    )
    release_blocking = release_relevance == "release-blocking" or warning_type in {
        "evidence_contract_missing_what_proves",
        "trigger_lacks_concrete_route_or_evidence",
    }
    return {
        "message": message,
        "type": warning_type,
        "scope": _string(source.get("scope")) or _inferred_warning_scope(path),
        "release_relevance": release_relevance,
        "reason": _string(source.get("reason")) or _inferred_warning_reason(release_relevance),
        "owner": _warning_owner(path),
        "accepted_reason": "Existing advisory finding retained only for regression visibility.",
        "review_after": "2026-07-15",
        "target_fix_phase": _warning_fix_phase(warning_type),
        "is_release_blocking": release_blocking,
    }


def _warning_owner(path: str) -> str:
    if "/professional-skills/" in path:
        return "changeforge-professional-skills-maintainers"
    if "/foundation/capabilities/" in path:
        return "changeforge-foundation-capability-maintainers"
    return "changeforge-maintainers"


def _warning_fix_phase(warning_type: str) -> str:
    return {
        "evidence_contract_missing_what_proves": "P0 evidence-contract-hardening",
        "trigger_lacks_concrete_route_or_evidence": "P0 proactive-trigger-hardening",
        "body_bloat_exception": "P2 content-bloat-review",
    }.get(warning_type, "P1 professionalism-warning-review")


def _routing_baseline(routing_dir: Path) -> dict[str, Any]:
    cases: dict[str, Any] = {}
    if not routing_dir.is_dir():
        return {"cases": cases, "l1_anti_over_routing_count": 0}
    for path in sorted(routing_dir.glob("*.yaml")):
        try:
            data = load_yaml_file(path)
        except ValidationProblem:
            continue
        if not isinstance(data, dict):
            continue
        case_id = _string(data.get("id") or path.stem)
        expected = data.get("expected")
        if not isinstance(expected, dict):
            expected = {}
        forbidden = data.get("forbidden")
        if not isinstance(forbidden, dict):
            forbidden = {}
        forbidden_counts = {
            field_name: len(_string_list(forbidden.get(field_name)))
            for field_name in EXPECTED_ROUTING_FIELDS
        }
        cases[case_id] = {
            "path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
            "complexity": _string(expected.get("complexity")),
            "risk_level": _string(expected.get("risk_level")),
            "expected_skills_count": len(_string_list(expected.get("skills"))),
            "expected_capabilities_count": len(_string_list(expected.get("capabilities"))),
            "forbidden_counts": forbidden_counts,
            "forbidden_present": any(count > 0 for count in forbidden_counts.values()),
            "forbidden_complete": all(count > 0 for count in forbidden_counts.values()),
            "l1_anti_over_routing": _is_l1_anti_over_routing(expected, forbidden),
        }
    return {
        "cases": cases,
        "l1_anti_over_routing_count": sum(1 for case in cases.values() if case["l1_anti_over_routing"]),
    }


def compare_against_baseline(
    baseline: dict[str, Any],
    current: dict[str, Any],
    *,
    strict: bool,
    report_only: bool,
) -> RegressionResult:
    blockers: list[Finding] = []
    warnings: list[Finding] = []
    known_warnings: list[Finding] = []
    thresholds = dict(DEFAULT_GLOBAL_THRESHOLDS)
    thresholds.update(baseline.get("global_thresholds") or {})
    score_threshold = float(thresholds.get("no_score_regression_more_than", 1.0))

    _compare_skill_group(
        "professional_skills",
        baseline,
        current,
        blockers,
        warnings,
        known_warnings,
        score_threshold,
        strict=strict,
        thresholds=thresholds,
    )
    _compare_skill_group(
        "foundation_capabilities",
        baseline,
        current,
        blockers,
        warnings,
        known_warnings,
        score_threshold,
        strict=strict,
        thresholds=thresholds,
    )
    _compare_benchmarks(baseline, current, blockers, warnings, thresholds)
    _compare_routing(baseline, current, blockers, thresholds)
    _compare_warning_budget(blockers, warnings, known_warnings, thresholds, strict=strict)

    status = "fail" if blockers else "pass"
    if report_only and blockers:
        status = "report-only"
    result = RegressionResult(
        generated_at=_now(),
        mode="strict" if strict else "default",
        status=status,
        strict=strict,
        report_only=report_only,
        blockers=blockers,
        warnings=warnings,
        known_warnings=known_warnings,
    )
    result.summary = _summary(result)
    return result


def _compare_skill_group(
    group: str,
    baseline: dict[str, Any],
    current: dict[str, Any],
    blockers: list[Finding],
    warnings: list[Finding],
    known_warnings: list[Finding],
    score_threshold: float,
    *,
    strict: bool,
    thresholds: dict[str, Any],
) -> None:
    base_items = _dict(baseline.get(group))
    current_items = _dict(current.get(group))
    professional_group = group == "professional_skills"
    recorded_exceptions = set(_string_list(_dict(current.get("content_bloat")).get("recorded_exceptions")))
    for name in sorted(current_items):
        current_entry = _dict(current_items[name])
        base_entry = _dict(base_items.get(name))
        target = current_entry.get("path") or name
        current_status = _string(current_entry.get("status"))
        base_status = _string(base_entry.get("status"))
        if strict and current_status == WEAK_STATUS:
            blockers.append(Finding("strict-weak-status", target, "strict mode rejects weak status", base_status, current_status))
        if (
            professional_group
            and thresholds.get("no_new_weak_professional_skill", True)
            and base_status in GOOD_STATUSES
            and current_status == WEAK_STATUS
        ):
            blockers.append(Finding("professional-status-regression", target, "professional skill regressed from acceptable/sample-grade to weak", base_status, current_status))
        if base_entry:
            base_score = float(base_entry.get("total_score") or 0)
            current_score = float(current_entry.get("total_score") or 0)
            if base_score - current_score > score_threshold:
                blockers.append(Finding("score-regression", target, f"score decreased by more than {score_threshold}", base_score, current_score))
        _compare_warning_sets(base_entry, current_entry, target, blockers, warnings, known_warnings, recorded_exceptions)
        _compare_coverage(base_entry, current_entry, target, blockers, thresholds, professional_group)


def _compare_warning_sets(
    baseline_entry: dict[str, Any],
    current_entry: dict[str, Any],
    target: str,
    blockers: list[Finding],
    warnings: list[Finding],
    known_warnings: list[Finding],
    recorded_exceptions: set[str],
) -> None:
    base_warning_records = _warning_record_map(baseline_entry.get("known_warnings"))
    current_warnings = set(_warning_messages(current_entry.get("known_warnings")))
    for warning in sorted(current_warnings & set(base_warning_records)):
        record = base_warning_records[warning]
        _validate_known_warning_metadata(record, target, warning, blockers)
        severity = "error" if record.get("is_release_blocking") is True else "info"
        known_warnings.append(Finding("known-warning", target, warning, record, warning, severity))
    for warning in sorted(current_warnings - set(base_warning_records)):
        finding = Finding("new-warning", target, warning, None, warning, "warning")
        warnings.append(finding)
        if _is_anti_bloat_warning(warning) and _string(current_entry.get("path")) not in recorded_exceptions:
            blockers.append(Finding("anti-bloat-regression", target, "new anti-bloat warning without recorded exception", None, warning))


def _validate_known_warning_metadata(
    record: dict[str, Any],
    target: str,
    warning: str,
    blockers: list[Finding],
) -> None:
    missing = [
        field_name
        for field_name in KNOWN_WARNING_METADATA_FIELDS
        if field_name not in record
        or (field_name != "is_release_blocking" and not _string(record.get(field_name)))
        or (field_name == "is_release_blocking" and not isinstance(record.get(field_name), bool))
    ]
    if missing:
        blockers.append(
            Finding(
                "known-warning-metadata-missing",
                target,
                f"known warning lacks required metadata fields: {', '.join(missing)}",
                warning,
                record,
            )
        )


def _compare_warning_budget(
    blockers: list[Finding],
    warnings: list[Finding],
    known_warnings: list[Finding],
    thresholds: dict[str, Any],
    *,
    strict: bool,
) -> None:
    max_new = thresholds.get("max_new_warnings_count")
    if max_new is not None and len(warnings) > int(max_new):
        blockers.append(
            Finding(
                "new-warning-budget",
                "professionalism-baseline",
                f"new warning count exceeds max_new_warnings_count={int(max_new)}",
                int(max_new),
                len(warnings),
            )
        )
    if strict:
        for known in known_warnings:
            if known.severity == "error":
                blockers.append(
                    Finding(
                        "known-warning-release-blocking",
                        known.target,
                        "strict mode rejects release-blocking accepted warning",
                        known.baseline_value,
                        known.current_value,
                    )
                )
        max_by_type = thresholds.get("max_known_warnings")
        if isinstance(max_by_type, dict):
            counts = _known_warning_type_counts(known_warnings)
            for warning_type, maximum in sorted(max_by_type.items()):
                if maximum is None:
                    continue
                current_count = counts.get(str(warning_type), 0)
                if current_count > int(maximum):
                    blockers.append(
                        Finding(
                            "known-warning-type-budget",
                            f"professionalism-baseline.{warning_type}",
                            f"known warning type exceeds max_known_warnings.{warning_type}={int(maximum)}",
                            int(maximum),
                            current_count,
                        )
                    )


def _compare_coverage(
    baseline_entry: dict[str, Any],
    current_entry: dict[str, Any],
    target: str,
    blockers: list[Finding],
    thresholds: dict[str, Any],
    professional_group: bool,
) -> None:
    base_coverage = _dict(baseline_entry.get("coverage"))
    current_coverage = _dict(current_entry.get("coverage"))
    if (
        professional_group
        and thresholds.get("no_new_missing_mode_matrix_for_professional_skill", True)
        and _is_missing(current_coverage.get("mode_matrix"))
        and not _is_missing(base_coverage.get("mode_matrix"))
    ):
        blockers.append(Finding("missing-mode-matrix", target, "new missing Mode Matrix", base_coverage.get("mode_matrix"), current_coverage.get("mode_matrix")))
    if (
        thresholds.get("no_new_missing_proactive_triggers_for_core_skill", True)
        and _is_missing(current_coverage.get("proactive_triggers"))
        and not _is_missing(base_coverage.get("proactive_triggers"))
    ):
        blockers.append(Finding("missing-proactive-triggers", target, "new missing Proactive Professional Triggers", base_coverage.get("proactive_triggers"), current_coverage.get("proactive_triggers")))
    if (
        thresholds.get("no_new_missing_evidence_contract_for_core_skill", True)
        and _is_weak_evidence(current_coverage.get("evidence_contract"))
        and not _is_weak_evidence(base_coverage.get("evidence_contract"))
    ):
        blockers.append(Finding("weak-evidence-contract", target, "new weak Evidence Contract", base_coverage.get("evidence_contract"), current_coverage.get("evidence_contract")))
    if (
        thresholds.get("no_new_reference_without_loading_hint", True)
        and _is_without_reference_hint(current_coverage.get("reference_loading_hint"))
        and not _is_without_reference_hint(base_coverage.get("reference_loading_hint"))
    ):
        blockers.append(Finding("reference-loading-hint-regression", target, "new reference without loading hint", base_coverage.get("reference_loading_hint"), current_coverage.get("reference_loading_hint")))
    if current_entry.get("required_sections_present") is False and baseline_entry.get("required_sections_present") is True:
        blockers.append(Finding("required-section-regression", target, "new missing required section", True, current_entry.get("missing_required_sections")))


def _compare_benchmarks(
    baseline: dict[str, Any],
    current: dict[str, Any],
    blockers: list[Finding],
    warnings: list[Finding],
    thresholds: dict[str, Any],
) -> None:
    base_cases = _dict(_dict(baseline.get("benchmarks")).get("cases"))
    current_cases = _dict(_dict(current.get("benchmarks")).get("cases"))
    for case_id in sorted(current_cases):
        current_case = _dict(current_cases[case_id])
        base_case = _dict(base_cases.get(case_id))
        current_errors = _string_list(current_case.get("errors"))
        base_errors = set(_string_list(base_case.get("errors")))
        new_errors = [error for error in current_errors if error not in base_errors]
        if current_case.get("benchmark_quality_status") == "fail" and (
            not base_case or base_case.get("benchmark_quality_status") != "fail" or new_errors
        ):
            blockers.append(Finding("benchmark-quality-regression", case_id, "benchmark quality failed or gained new errors", base_case.get("errors"), current_errors))
        if (
            thresholds.get("no_new_empty_benchmark_case", True)
            and int(current_case.get("baseline_defect_hits_count") or 0) < 1
            and int(base_case.get("baseline_defect_hits_count") or 0) >= 1
        ):
            blockers.append(Finding("empty-benchmark-regression", case_id, "baseline_output.md no longer demonstrates a forbidden behavior", base_case.get("baseline_defect_hits_count"), current_case.get("baseline_defect_hits_count")))
        if not base_case and int(current_case.get("baseline_defect_hits_count") or 0) < 1:
            blockers.append(Finding("empty-benchmark-case", case_id, "new benchmark baseline_output.md does not demonstrate a forbidden behavior", None, current_case.get("baseline_defect_hits_count")))
        if base_case:
            base_delta = int(base_case.get("delta_score") or 0)
            current_delta = int(current_case.get("delta_score") or 0)
            if current_delta < base_delta:
                blockers.append(Finding("benchmark-delta-regression", case_id, "benchmark comparison delta decreased", base_delta, current_delta))
        if current_errors and not new_errors:
            warnings.append(Finding("known-benchmark-errors", case_id, "benchmark retains baseline errors", base_case.get("errors"), current_errors, "warning"))


def _compare_routing(
    baseline: dict[str, Any],
    current: dict[str, Any],
    blockers: list[Finding],
    thresholds: dict[str, Any],
) -> None:
    base_routing = _dict(baseline.get("routing"))
    current_routing = _dict(current.get("routing"))
    base_cases = _dict(base_routing.get("cases"))
    current_cases = _dict(current_routing.get("cases"))
    for case_id in sorted(current_cases):
        current_case = _dict(current_cases[case_id])
        base_case = _dict(base_cases.get(case_id))
        if not thresholds.get("no_new_routing_case_without_forbidden", True):
            continue
        if not current_case.get("forbidden_present") and not base_case:
            blockers.append(Finding("routing-case-without-forbidden", case_id, "new routing case has no forbidden.* coverage", None, current_case.get("forbidden_counts")))
        if base_case.get("forbidden_present") and not current_case.get("forbidden_present"):
            blockers.append(Finding("routing-forbidden-regression", case_id, "routing case lost forbidden.* coverage", base_case.get("forbidden_counts"), current_case.get("forbidden_counts")))
    base_l1 = int(base_routing.get("l1_anti_over_routing_count") or 0)
    current_l1 = int(current_routing.get("l1_anti_over_routing_count") or 0)
    if current_l1 < base_l1:
        blockers.append(Finding("l1-anti-over-routing-regression", "evals/routing", "L1 anti-over-routing case count decreased", base_l1, current_l1))


def diff_snapshots(old: dict[str, Any], new: dict[str, Any]) -> list[Finding]:
    changes: list[Finding] = []
    for group in ("professional_skills", "foundation_capabilities"):
        old_items = _dict(old.get(group))
        new_items = _dict(new.get(group))
        for name in sorted(set(old_items) | set(new_items)):
            if name not in old_items:
                changes.append(Finding("baseline-added", f"{group}.{name}", "added to baseline", None, "added", "info"))
                continue
            if name not in new_items:
                changes.append(Finding("baseline-removed", f"{group}.{name}", "removed from baseline", "present", None, "info"))
                continue
            for field_name in ("total_score", "status", "known_warnings_count", "required_sections_present", "benchmark_coverage_count", "routing_coverage_count"):
                old_value = _dict(old_items[name]).get(field_name)
                new_value = _dict(new_items[name]).get(field_name)
                if old_value != new_value:
                    changes.append(Finding("baseline-changed", f"{group}.{name}.{field_name}", "baseline value changed", old_value, new_value, "info"))
    old_cases = _dict(_dict(old.get("benchmarks")).get("cases"))
    new_cases = _dict(_dict(new.get("benchmarks")).get("cases"))
    for case_id in sorted(set(old_cases) | set(new_cases)):
        if case_id not in old_cases:
            changes.append(Finding("baseline-added", f"benchmarks.{case_id}", "added benchmark case", None, "added", "info"))
        elif case_id not in new_cases:
            changes.append(Finding("baseline-removed", f"benchmarks.{case_id}", "removed benchmark case", "present", None, "info"))
        else:
            for field_name in ("benchmark_quality_status", "delta_score", "baseline_defect_hits_count", "remaining_gaps_count"):
                old_value = _dict(old_cases[case_id]).get(field_name)
                new_value = _dict(new_cases[case_id]).get(field_name)
                if old_value != new_value:
                    changes.append(Finding("baseline-changed", f"benchmarks.{case_id}.{field_name}", "baseline benchmark value changed", old_value, new_value, "info"))
    return changes


def _write_reports(
    result: RegressionResult,
    current: dict[str, Any],
    reports: dict[str, dict[str, Any]],
    reports_dir: Path,
    *,
    default_result: RegressionResult | None,
    strict_result: RegressionResult | None,
    agent_samples_strict: dict[str, Any],
    release_review_config_path: Path,
) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    payload = _result_payload(result)
    (reports_dir / REGRESSION_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (reports_dir / REGRESSION_MD).write_text(_render_regression_markdown(result), encoding="utf-8")
    readiness = _release_readiness_payload(
        result,
        current,
        reports,
        default_result=default_result,
        strict_result=strict_result,
        agent_samples_strict=agent_samples_strict,
        release_review_config_path=release_review_config_path,
    )
    (reports_dir / READINESS_JSON).write_text(
        json.dumps(readiness, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (reports_dir / READINESS_MD).write_text(_render_readiness_markdown(readiness), encoding="utf-8")


def _write_input_error_report(reports_dir: Path, error: str, args: argparse.Namespace) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    result = RegressionResult(
        generated_at=_now(),
        mode="input-error",
        status="fail",
        strict=bool(args.strict),
        report_only=bool(args.report_only),
        blockers=[Finding("input-error", "reports", error)],
    )
    result.summary = _summary(result)
    (reports_dir / REGRESSION_JSON).write_text(
        json.dumps(_result_payload(result), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (reports_dir / REGRESSION_MD).write_text(_render_regression_markdown(result), encoding="utf-8")


def _result_payload(result: RegressionResult) -> dict[str, Any]:
    payload = asdict(result)
    return payload


def _render_regression_markdown(result: RegressionResult) -> str:
    lines = [
        "# Professionalism Regression Report",
        "",
        f"- Generated: {result.generated_at}",
        f"- Mode: {result.mode}",
        f"- Status: {result.status}",
        f"- Strict: {str(result.strict).lower()}",
        f"- Report only: {str(result.report_only).lower()}",
        f"- Blockers: {len(result.blockers)}",
        f"- Warnings: {len(result.warnings)}",
        f"- Known accepted warnings: {len(result.known_warnings)}",
        f"- Baseline changes: {len(result.baseline_changes)}",
    ]
    _append_findings(lines, "Blockers", result.blockers)
    _append_findings(lines, "Warnings", result.warnings)
    _append_findings(lines, "Known Accepted Warnings", result.known_warnings)
    _append_findings(lines, "Baseline Changes", result.baseline_changes)
    return "\n".join(lines).rstrip() + "\n"


def _append_findings(lines: list[str], title: str, findings: list[Finding]) -> None:
    lines.extend(["", f"## {title}", ""])
    if not findings:
        lines.append("- None")
        return
    for finding in findings:
        lines.append(
            f"- `{finding.category}` `{finding.target}`: {finding.message} "
            f"(baseline: {_display(finding.baseline_value)}, current: {_display(finding.current_value)})"
        )


def _release_readiness_payload(
    result: RegressionResult,
    current: dict[str, Any],
    reports: dict[str, dict[str, Any]],
    *,
    default_result: RegressionResult | None,
    strict_result: RegressionResult | None,
    agent_samples_strict: dict[str, Any],
    release_review_config_path: Path,
) -> dict[str, Any]:
    professional = _dict(current.get("professional_skills"))
    foundation = _dict(current.get("foundation_capabilities"))
    benchmarks = _dict(current.get("benchmarks"))
    routing = _dict(current.get("routing"))
    routing_coverage = _dict(reports.get("routing_coverage"))
    content_audit = _dict(reports.get("content_audit"))
    content_summary = _dict(content_audit.get("summary"))
    benchmark_cases = _dict(benchmarks.get("cases"))
    default_result = default_result or (result if not result.strict else None)
    strict_run_available = strict_result is not None
    strict_blockers = strict_result.blockers if strict_result else []
    agent_strict_report = _dict(agent_samples_strict.get("report"))
    agent_strict_returncode = agent_samples_strict.get("returncode")
    agent_strict_ran = bool(agent_samples_strict.get("ran"))
    agent_strict_failures = int(agent_strict_report.get("failures") or 0)
    benchmark_errors = len(_string_list(reports["benchmarks"].get("errors")))
    benchmark_quality_failures = sum(
        1 for case in benchmark_cases.values()
        if _dict(case).get("benchmark_quality_status") == "fail"
    )
    routing_uncovered = int(routing_coverage.get("hidden_risks_needing_manual_review") or 0)
    default_blocked = bool(default_result and default_result.blockers)
    strict_blocked = bool(strict_blockers)
    agent_strict_blocked = (
        (agent_strict_ran and int(agent_strict_returncode or 0) != 0)
        or agent_strict_failures > 0
    )
    checklist = _readiness_checklist(
        default_result=default_result,
        strict_result=strict_result,
        benchmarks=benchmarks,
        reports=reports,
        routing_coverage=routing_coverage,
        content_summary=content_summary,
        agent_samples_strict=agent_samples_strict,
    )
    warning_reconciliation = _skill_professionalism_warning_reconciliation(reports["skill_eval"], result)
    release_review = _release_review_reconciliation(
        warning_reconciliation,
        release_review_config_path,
    )
    release_blockers = list(result.blockers)
    if strict_blockers and not result.strict:
        release_blockers.extend(
            Finding(
                "strict-release-regression",
                item.target,
                item.message,
                item.baseline_value,
                item.current_value,
                item.severity,
            )
            for item in strict_blockers
        )
    if agent_strict_blocked:
        release_blockers.append(
            Finding(
                "promoted-agent-samples-strict",
                "professional-agent-samples",
                "promoted professional agent samples failed under --strict",
                0,
                agent_strict_failures or agent_strict_returncode,
            )
        )
    if benchmark_errors or benchmark_quality_failures:
        release_blockers.append(
            Finding(
                "professional-benchmarks",
                "reports/professional-benchmarks-report.json",
                "professional benchmark schema, comparison, or quality status failed",
                0,
                {"errors": benchmark_errors, "quality_failures": benchmark_quality_failures},
            )
        )
    if routing_uncovered:
        release_blockers.append(
            Finding(
                "routing-hidden-risk-coverage",
                "reports/professional-routing-coverage.json",
                "professional routing coverage has hidden risks needing manual review",
                0,
                routing_uncovered,
            )
        )
    for blocker in release_review["blockers"]:
        release_blockers.append(
            Finding(
                blocker["category"],
                blocker["target"],
                blocker["message"],
                blocker.get("baseline_value"),
                blocker.get("current_value"),
            )
        )
    authoring_ready_status = "blocked" if default_blocked else "ready"
    if not strict_run_available or not agent_strict_ran:
        release_ready_status = "not-release-certified"
        strict_release_ready_status = "not-run"
        status = "ready-for-authoring / not-release-certified" if not default_blocked else "blocked"
    elif release_blockers or strict_blocked or agent_strict_blocked:
        release_ready_status = "blocked"
        strict_release_ready_status = "blocked"
        status = "blocked" if default_blocked else "ready-for-authoring / not-release-certified"
    else:
        release_ready_status = "ready"
        strict_release_ready_status = "ready"
        status = "strict-release-ready"
    followups = _readiness_followups(result, foundation)
    return {
        "generated_at": _now(),
        "status": status,
        "authoring_ready": authoring_ready_status,
        "release_ready": release_ready_status,
        "strict_release_ready": strict_release_ready_status,
        "professional_skill_coverage_summary": _status_summary(professional),
        "key_foundation_capability_coverage_summary": _status_summary(foundation),
        "benchmark_coverage_summary": {
            "cases_checked": benchmarks.get("cases_checked", 0),
            "comparison_cases_checked": benchmarks.get("comparison_cases_checked", 0),
            "quality_failures": sum(1 for case in benchmark_cases.values() if _dict(case).get("benchmark_quality_status") == "fail"),
            "empty_baseline_cases": sum(1 for case in benchmark_cases.values() if int(_dict(case).get("baseline_defect_hits_count") or 0) < 1),
        },
        "routing_coverage_summary": {
            "cases_checked": len(_dict(routing.get("cases"))),
            "l1_anti_over_routing_count": routing.get("l1_anti_over_routing_count", 0),
            "cases_without_forbidden": sum(1 for case in _dict(routing.get("cases")).values() if not _dict(case).get("forbidden_present")),
            "hidden_risks_strongly_covered": routing_coverage.get("hidden_risks_covered", "not-run"),
            "hidden_risks_checked": routing_coverage.get("hidden_risks_checked", "not-run"),
            "hidden_risks_needing_manual_review": routing_coverage.get("hidden_risks_needing_manual_review", "not-run"),
        },
        "regression_status": result.status,
        "default_regression_status": default_result.status if default_result else "not-run",
        "strict_regression_status": strict_result.status if strict_result else "not-run",
        "promoted_agent_samples_strict_status": _agent_strict_status(agent_samples_strict),
        "release_blocking_professionalism_warnings": warning_reconciliation["release_blocking_warnings"],
        "release_review_required_warnings": release_review["release_review_required_warnings"],
        "release_review_decisions": release_review["summary"],
        "release_review_decision": release_review["decision"],
        "release_review_reason": release_review["reason"],
        "release_review_decision_records": release_review["records"],
        "release_review_config": str(release_review_config_path.relative_to(ROOT)) if release_review_config_path.is_relative_to(ROOT) else str(release_review_config_path),
        "checklist": checklist,
        "known_accepted_warnings": [asdict(item) for item in result.known_warnings],
        "warning_reconciliation": warning_reconciliation,
        "out_of_scope_non_key_skill_eval_warnings": _legacy_warning_scope(warning_reconciliation),
        "content_bloat_status": {
            "heavy_professional": content_summary.get("heavy_professional", "unknown"),
            "heavy_foundation": content_summary.get("heavy_foundation", "unknown"),
            "heavy_domain": content_summary.get("heavy_domain", "unknown"),
            "split_candidates": content_summary.get("split_candidates", "unknown"),
            "low_professionalism": content_summary.get("low_professionalism", "unknown"),
        },
        "required_validation_commands": [
            "python3 scripts/eval-skill-professionalism.py",
            "python3 scripts/eval-skill-professionalism.py --coverage-matrix",
            "python3 scripts/eval-professional-benchmarks.py",
            "python3 scripts/validate-professionalism-regression.py",
            "python3 scripts/validate-professionalism-regression.py --strict",
            "python3 scripts/validate-professional-routing-coverage.py",
            "python3 scripts/eval-professional-agent-samples.py",
            "python3 scripts/eval-professional-agent-samples.py --promoted-only --strict",
        ],
        "latest_results_available": {
            "skill_professionalism_warnings": reports["skill_eval"].get("warning_count"),
            "release_blocking_professionalism_warnings": warning_reconciliation["release_blocking_warnings"],
            "skill_professionalism_average_score": reports["skill_eval"].get("average_score"),
            "coverage_rows_checked": reports["coverage_matrix"].get("rows_checked"),
            "benchmark_errors": len(_string_list(reports["benchmarks"].get("errors"))),
            "professional_agent_sample_warnings": reports["agent_samples"].get("warnings", "not-run"),
            "professional_agent_samples_checked": reports["agent_samples"].get("samples_checked", "not-run"),
            "promoted_agent_sample_strict_warnings": agent_strict_report.get("warnings", "not-run"),
            "promoted_agent_samples_strict_checked": agent_strict_report.get("samples_checked", "not-run"),
        },
        "release_blockers": [asdict(item) for item in release_blockers],
        "non_blocking_followups": followups,
    }


def _render_readiness_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Professionalism Release Readiness",
        "",
        f"- Generated: {payload['generated_at']}",
        f"- Status: {payload['status']}",
        f"- Authoring ready: {payload['authoring_ready']}",
        f"- Release ready: {payload['release_ready']}",
        f"- Strict release ready: {payload['strict_release_ready']}",
        f"- Release-blocking professionalism warnings: {payload['release_blocking_professionalism_warnings']}",
        f"- Release review required warnings: {payload['release_review_required_warnings']}",
        f"- Release review decision: {payload['release_review_decision']}",
        f"- Release review reason: {payload['release_review_reason']}",
        f"- Regression status: {payload['regression_status']}",
        f"- Default regression status: {payload['default_regression_status']}",
        f"- Strict regression status: {payload['strict_regression_status']}",
        f"- Promoted agent samples strict status: {payload['promoted_agent_samples_strict_status']}",
        "",
        "## Professional Skill Coverage Summary",
        "",
        _summary_line(payload["professional_skill_coverage_summary"]),
        "",
        "## Key Foundation Capability Coverage Summary",
        "",
        _summary_line(payload["key_foundation_capability_coverage_summary"]),
        "",
        "## Release Checklist",
        "",
        "| Checklist Item | Status | Evidence Source | Blocking? | Notes |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in payload["checklist"]:
        lines.append(
            f"| {row['item']} | {row['status']} | `{row['evidence_source']}` | "
            f"{str(row['blocking']).lower()} | {row['notes']} |"
        )
    lines.extend(
        [
        "",
        "## Benchmark Coverage Summary",
        "",
        _mapping_lines(payload["benchmark_coverage_summary"]),
        "",
        "## Routing Coverage Summary",
        "",
        _mapping_lines(payload["routing_coverage_summary"]),
        "",
        "## Known Accepted Warnings",
        "",
        ]
    )
    if payload["known_accepted_warnings"]:
        for item in payload["known_accepted_warnings"]:
            lines.append(f"- `{item['target']}`: {item['message']}")
    else:
        lines.append("- None")
    warning_reconciliation = _dict(payload.get("warning_reconciliation"))
    warning_reconciliation_summary = {
        key: value
        for key, value in warning_reconciliation.items()
        if key != "warnings"
    }
    lines.extend(
        [
            "",
            "## Skill Professionalism Warning Reconciliation",
            "",
            _mapping_lines(warning_reconciliation_summary),
            "",
            "| Warning | Scope | Release Relevance | Reason | Follow-up |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    scoped_warnings = [
        item for item in warning_reconciliation.get("warnings", [])
        if isinstance(item, dict)
    ]
    if scoped_warnings:
        for item in scoped_warnings:
            lines.append(
                f"| `{item.get('target', '')}`: {item.get('message', '')} | "
                f"{item.get('scope', '')} | {item.get('release_relevance', '')} | "
                f"{item.get('reason', '')} | {item.get('follow_up', '')} |"
            )
    else:
        lines.append("| None | - | - | - | - |")
    lines.extend(
        [
            "",
            "## Release Review Decisions",
            "",
            _mapping_lines(payload["release_review_decisions"]),
            "",
            f"- Decision: {payload['release_review_decision']}",
            f"- Reason: {payload['release_review_reason']}",
            f"- Config: `{payload['release_review_config']}`",
            "",
            "| Target | Warning | Decision | Reason | Follow-up | Review After |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    release_review_records = [
        item for item in payload.get("release_review_decision_records", [])
        if isinstance(item, dict)
    ]
    if release_review_records:
        for item in release_review_records:
            lines.append(
                f"| `{item.get('target', '')}` | {item.get('warning_message', '')} | "
                f"{item.get('decision', '')} | {item.get('reason', '')} | "
                f"{item.get('follow_up_phase', '')} | {item.get('review_after', '')} |"
            )
    else:
        lines.append("| None | - | - | - | - | - |")
    lines.extend(
        [
            "",
            "## Content Bloat Status",
            "",
            _mapping_lines(payload["content_bloat_status"]),
            "",
            "## Required Validation Commands",
            "",
        ]
    )
    for command in payload["required_validation_commands"]:
        lines.append(f"- `{command}`")
    lines.extend(["", "## Latest Results Available", "", _mapping_lines(payload["latest_results_available"]), "", "## Release Blockers", ""])
    if payload["release_blockers"]:
        for item in payload["release_blockers"]:
            lines.append(f"- `{item['category']}` `{item['target']}`: {item['message']}")
    else:
        lines.append("- None")
    lines.extend(["", "## Non-Blocking Follow-Ups", ""])
    if payload["non_blocking_followups"]:
        for item in payload["non_blocking_followups"]:
            lines.append(f"- `{item['category']}` `{item['target']}`: {item['message']}")
    else:
        lines.append("- None")
    return "\n".join(lines).rstrip() + "\n"


def _readiness_checklist(
    *,
    default_result: RegressionResult | None,
    strict_result: RegressionResult | None,
    benchmarks: dict[str, Any],
    reports: dict[str, dict[str, Any]],
    routing_coverage: dict[str, Any],
    content_summary: dict[str, Any],
    agent_samples_strict: dict[str, Any],
) -> list[dict[str, Any]]:
    benchmark_cases = _dict(benchmarks.get("cases"))
    benchmark_errors = len(_string_list(reports["benchmarks"].get("errors")))
    benchmark_quality_failures = sum(
        1 for case in benchmark_cases.values()
        if _dict(case).get("benchmark_quality_status") == "fail"
    )
    empty_baseline_cases = sum(
        1 for case in benchmark_cases.values()
        if int(_dict(case).get("baseline_defect_hits_count") or 0) < 1
    )
    routing_manual = int(routing_coverage.get("hidden_risks_needing_manual_review") or 0)
    agent_report = _dict(agent_samples_strict.get("report"))
    agent_returncode = int(agent_samples_strict.get("returncode") or 0)
    known_budget_blockers = [
        item for item in (strict_result.blockers if strict_result else [])
        if item.category in {"known-warning-type-budget", "known-warning-release-blocking", "known-warning-budget"}
    ]
    content_blockers = [
        item for item in (default_result.blockers if default_result else [])
        if item.category == "anti-bloat-regression"
    ]
    rows = [
        _checklist_row(
            "default regression",
            "pass" if default_result and not default_result.blockers else "fail",
            "reports/professionalism-regression-report.json",
            True,
            f"status={default_result.status if default_result else 'not-run'}",
        ),
        _checklist_row(
            "strict regression",
            "pass" if strict_result and not strict_result.blockers else ("not-run" if not strict_result else "fail"),
            "internal strict comparison equivalent to python3 scripts/validate-professionalism-regression.py --strict",
            True,
            f"blockers={len(strict_result.blockers) if strict_result else 'not-run'}",
        ),
        _checklist_row(
            "professional benchmarks",
            "pass" if benchmark_errors == 0 and benchmark_quality_failures == 0 and empty_baseline_cases == 0 else "fail",
            "reports/professional-benchmarks-report.json",
            True,
            f"errors={benchmark_errors}; quality_failures={benchmark_quality_failures}; empty_baseline_cases={empty_baseline_cases}",
        ),
        _checklist_row(
            "routing coverage",
            "pass" if routing_coverage and routing_manual == 0 and routing_coverage.get("status") == "pass" else ("not-run" if not routing_coverage else "fail"),
            "reports/professional-routing-coverage.json",
            True,
            f"needs_manual_review={routing_manual if routing_coverage else 'not-run'}",
        ),
        _checklist_row(
            "promoted agent samples strict",
            "pass" if agent_samples_strict.get("ran") and agent_returncode == 0 and int(agent_report.get("failures") or 0) == 0 else "fail",
            "reports/professional-agent-samples-report.json from python3 scripts/eval-professional-agent-samples.py --promoted-only --strict",
            True,
            f"returncode={agent_returncode}; failures={agent_report.get('failures', 'not-run')}",
        ),
        _checklist_row(
            "content bloat exceptions",
            "pass" if not content_blockers else "fail",
            "config/skill-content-exceptions.yaml and reports/skill-content-audit.json",
            True,
            _mapping_lines(content_summary).replace("\n", "; ") if content_summary else "not-run",
        ),
        _checklist_row(
            "known warnings budget",
            "pass" if strict_result and not known_budget_blockers else ("not-run" if not strict_result else "fail"),
            "config/professionalism-baseline.yaml global_thresholds.max_known_warnings",
            True,
            f"budget_blockers={len(known_budget_blockers) if strict_result else 'not-run'}",
        ),
        _checklist_row(
            "baseline update drift",
            "pass" if default_result and not default_result.baseline_changes else "not-run",
            "reports/professionalism-regression-report.json baseline_changes",
            False,
            f"baseline_changes={len(default_result.baseline_changes) if default_result else 'not-run'}",
        ),
    ]
    return rows


def _checklist_row(
    item: str,
    status: str,
    evidence_source: str,
    blocking: bool,
    notes: str,
) -> dict[str, Any]:
    return {
        "item": item,
        "status": status,
        "evidence_source": evidence_source,
        "blocking": blocking,
        "notes": notes,
    }


def _skill_professionalism_warning_reconciliation(
    skill_eval: dict[str, Any],
    result: RegressionResult,
) -> dict[str, Any]:
    all_records = _skill_eval_warning_records(skill_eval)
    accepted_records = {
        (item.target, item.message): _dict(item.baseline_value)
        for item in result.known_warnings
    }
    new_records = {
        (item.target, item.message)
        for item in result.warnings
    }
    reconciled: list[dict[str, Any]] = []
    for record in all_records:
        key = (record["target"], record["message"])
        payload = dict(record)
        accepted = accepted_records.get(key)
        if accepted and accepted.get("is_release_blocking") is not True:
            payload["release_relevance"] = "accepted-known-warning"
            payload["reason"] = (
                _string(accepted.get("accepted_reason"))
                or "Accepted known warning is tracked in the professionalism baseline."
            )
            payload["accepted_warning"] = True
            payload["accepted_warning_metadata"] = accepted
        else:
            payload["accepted_warning"] = False
        payload["tracked_release_warning"] = bool(accepted or key in new_records)
        payload["follow_up"] = _warning_follow_up(payload)
        reconciled.append(payload)

    source_warning_count = skill_eval.get("warning_count")
    total_warning_count = (
        int(source_warning_count)
        if isinstance(source_warning_count, int)
        else len(all_records)
    )
    release_blocking = [
        record for record in reconciled
        if record.get("release_relevance") == "release-blocking"
    ]
    accepted_known = [
        record for record in reconciled
        if record.get("release_relevance") == "accepted-known-warning"
    ]
    release_review_required = [
        record for record in reconciled
        if record.get("release_relevance") == "release-review-required"
    ]
    key_follow_up = [
        record for record in reconciled
        if record.get("scope") == "key-foundation-capability"
        and record.get("release_relevance") == "non-blocking-follow-up"
    ]
    non_key_advisory = [
        record for record in reconciled
        if record.get("scope") == "non-key-foundation-capability"
        and record.get("release_relevance") == "advisory-only"
    ]
    enhanced_review = [
        record for record in reconciled
        if record.get("scope") == "enhanced-foundation-capability"
        and record.get("release_relevance") == "release-review-required"
    ]
    return {
        "total_skill_professionalism_warnings": total_warning_count,
        "release_blocking_warnings": len(release_blocking),
        "accepted_known_warnings": len(accepted_known),
        "release_review_required_warnings": len(release_review_required),
        "enhanced_foundation_review_warnings": len(enhanced_review),
        "key_foundation_follow_up_warnings": len(key_follow_up),
        "non_key_foundation_advisory_warnings": len(non_key_advisory),
        "tracked_release_warnings": len(result.known_warnings) + len(result.warnings),
        "new_unaccepted_release_warnings": len(result.warnings),
        "policy": (
            "Professional skill warnings block release. Enhanced foundation warnings require release review. "
            "Key foundation warnings are follow-up unless evidence or reference precision is weak. "
            "Non-key foundation warnings are advisory-only."
        ),
        "warnings": reconciled,
    }


def _release_review_reconciliation(
    warning_reconciliation: dict[str, Any],
    release_review_config_path: Path,
) -> dict[str, Any]:
    required_warnings = [
        dict(record)
        for record in warning_reconciliation.get("warnings", [])
        if isinstance(record, dict)
        and record.get("release_relevance") == "release-review-required"
    ]
    required_keys = {
        (_string(record.get("target")), _string(record.get("message")))
        for record in required_warnings
    }
    config = _load_release_review_config(release_review_config_path)
    decisions = _release_review_decision_records(config)
    decisions_by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}
    records: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    summary = {
        "accepted_for_current_release": 0,
        "blocks_release": 0,
        "defer_to_followup": 0,
        "missing": 0,
        "stale": 0,
    }

    for decision in decisions:
        key = (_string(decision.get("target")), _string(decision.get("warning_message")))
        if key in required_keys:
            decisions_by_key.setdefault(key, []).append(decision)
            continue
        summary["stale"] += 1
        stale_record = _release_review_record(
            decision,
            None,
            "stale",
            "Decision target and warning_message do not match a current release-review-required warning.",
        )
        records.append(stale_record)
        blockers.append(_release_review_blocker("release-review-decision-stale", stale_record))

    for warning in required_warnings:
        key = (_string(warning.get("target")), _string(warning.get("message")))
        matching_decisions = decisions_by_key.get(key, [])
        if not matching_decisions:
            summary["missing"] += 1
            missing_record = _release_review_record(
                {},
                warning,
                "missing",
                "No matching release review decision exists for this release-review-required warning.",
            )
            records.append(missing_record)
            blockers.append(_release_review_blocker("release-review-decision-missing", missing_record))
            continue

        decision = matching_decisions[0]
        value = _string(decision.get("decision"))
        invalid_reason = _invalid_release_review_decision_reason(decision, warning)
        if invalid_reason:
            summary["stale"] += 1
            invalid_record = _release_review_record(decision, warning, "stale", invalid_reason)
            records.append(invalid_record)
            blockers.append(_release_review_blocker("release-review-decision-stale", invalid_record))
            continue
        if value == "accepted_for_current_release":
            summary["accepted_for_current_release"] += 1
            records.append(_release_review_record(decision, warning, value, _string(decision.get("reason"))))
        elif value == "blocks_release":
            summary["blocks_release"] += 1
            blocked_record = _release_review_record(decision, warning, value, _string(decision.get("reason")))
            records.append(blocked_record)
            blockers.append(_release_review_blocker("release-review-decision-blocks-release", blocked_record))
        elif value == "defer_to_followup":
            summary["defer_to_followup"] += 1
            deferred_record = _release_review_record(decision, warning, value, _string(decision.get("reason")))
            records.append(deferred_record)
            blockers.append(_release_review_blocker("release-review-decision-deferred", deferred_record))

        for duplicate in matching_decisions[1:]:
            summary["stale"] += 1
            duplicate_record = _release_review_record(
                duplicate,
                warning,
                "stale",
                "Duplicate release review decision for the same target and warning_message.",
            )
            records.append(duplicate_record)
            blockers.append(_release_review_blocker("release-review-decision-stale", duplicate_record))

    if summary["missing"]:
        decision_status = "missing"
        reason = (
            f"{summary['missing']} release-review-required warning(s) lack a matching release review decision."
        )
    elif summary["blocks_release"] or summary["defer_to_followup"] or summary["stale"]:
        decision_status = "blocked"
        reason = (
            "Release review decisions contain blocking, deferred, stale, or invalid entries; "
            "strict release is not certified."
        )
    elif required_warnings:
        decision_status = "accepted"
        reason = (
            f"All {len(required_warnings)} release-review-required warning(s) have "
            "accepted_for_current_release decisions."
        )
    else:
        decision_status = "accepted"
        reason = "No release-review-required warnings are present."

    return {
        "release_review_required_warnings": len(required_warnings),
        "summary": summary,
        "decision": decision_status,
        "reason": reason,
        "records": records,
        "blockers": blockers,
    }


def _load_release_review_config(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data = load_yaml_file(path)
    if not isinstance(data, dict):
        raise RegressionInputError(f"{path}: expected YAML mapping")
    return data


def _release_review_decision_records(config: dict[str, Any]) -> list[dict[str, Any]]:
    decisions = config.get("decisions")
    if decisions is None:
        return []
    if not isinstance(decisions, list) or not all(isinstance(item, dict) for item in decisions):
        raise RegressionInputError("release review config: decisions must be a list of mappings")
    records: list[dict[str, Any]] = []
    review_owner = _string(config.get("review_owner"))
    reviewed_at = _string(config.get("reviewed_at"))
    for item in decisions:
        record = dict(item)
        if "warning_message" not in record and "message" in record:
            record["warning_message"] = record.get("message")
        record["warning_message"] = _string(record.get("warning_message"))
        record["target"] = _string(record.get("target"))
        record["decision"] = _string(record.get("decision"))
        record["review_owner"] = _string(record.get("review_owner")) or review_owner
        record["reviewed_at"] = _string(record.get("reviewed_at")) or reviewed_at
        records.append(record)
    return records


def _invalid_release_review_decision_reason(
    decision: dict[str, Any],
    warning: dict[str, Any],
) -> str:
    value = _string(decision.get("decision"))
    if value not in RELEASE_REVIEW_DECISIONS:
        return f"Decision value must be one of {', '.join(sorted(RELEASE_REVIEW_DECISIONS))}."
    if _string(decision.get("scope")) and _string(decision.get("scope")) != _string(warning.get("scope")):
        return "Decision scope does not match the current warning scope."
    if (
        _string(decision.get("release_relevance"))
        and _string(decision.get("release_relevance")) != _string(warning.get("release_relevance"))
    ):
        return "Decision release_relevance does not match the current warning release_relevance."
    if value == "accepted_for_current_release":
        missing = [
            field_name
            for field_name in ("reason", "follow_up_phase", "review_after")
            if not _string(decision.get(field_name))
        ]
        if missing:
            return "accepted_for_current_release decision is missing required field(s): " + ", ".join(missing)
    return ""


def _release_review_record(
    decision: dict[str, Any],
    warning: dict[str, Any] | None,
    status: str,
    reason: str,
) -> dict[str, Any]:
    warning_data = warning or {}
    target = _string(warning_data.get("target")) or _string(decision.get("target"))
    message = _string(warning_data.get("message")) or _string(decision.get("warning_message"))
    return {
        "target": target,
        "warning_message": message,
        "warning_type": _string(warning_data.get("warning_type") or warning_data.get("type") or decision.get("warning_type")),
        "scope": _string(warning_data.get("scope") or decision.get("scope")),
        "release_relevance": _string(warning_data.get("release_relevance") or decision.get("release_relevance")),
        "decision": status,
        "reason": reason,
        "follow_up_phase": _string(decision.get("follow_up_phase")),
        "review_after": _string(decision.get("review_after")),
        "review_owner": _string(decision.get("review_owner")),
        "reviewed_at": _string(decision.get("reviewed_at")),
    }


def _release_review_blocker(category: str, record: dict[str, Any]) -> dict[str, Any]:
    return {
        "category": category,
        "target": record.get("target", ""),
        "message": _string(record.get("warning_message")) or _string(record.get("reason")),
        "baseline_value": record.get("decision"),
        "current_value": record,
    }


def _skill_eval_warning_records(skill_eval: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item in _mapping_list(skill_eval, "items", "skill professionalism report"):
        path = _string(item.get("path"))
        target = path or _string(item.get("name"))
        name = _string(item.get("name"))
        kind = _string(item.get("kind"))
        for warning in _warning_record_list(item.get("warnings")):
            message = _string(warning.get("message"))
            warning_type = _string(warning.get("type")) or _warning_type(message)
            scope = _string(warning.get("scope")) or _inferred_warning_scope(path)
            release_relevance = _string(warning.get("release_relevance")) or _inferred_release_relevance(
                path,
                warning_type,
                message,
            )
            records.append(
                {
                    "name": name,
                    "target": target,
                    "path": path,
                    "kind": kind,
                    "message": message,
                    "type": warning_type,
                    "warning_type": warning_type,
                    "item": _string(warning.get("item")) or name,
                    "item_kind": _string(warning.get("item_kind")) or kind,
                    "scope": scope,
                    "release_relevance": release_relevance,
                    "reason": _string(warning.get("reason")) or _inferred_warning_reason(release_relevance),
                    "release_blocking": release_relevance == "release-blocking",
                }
            )
    return records


def _legacy_warning_scope(reconciliation: dict[str, Any]) -> dict[str, Any]:
    warnings = [
        record for record in reconciliation.get("warnings", [])
        if isinstance(record, dict)
        and record.get("release_relevance") not in {"accepted-known-warning", "release-blocking"}
    ]
    non_key_count = sum(
        1
        for record in warnings
        if record.get("scope") == "non-key-foundation-capability"
    )
    return {
        "total_skill_professionalism_warnings": reconciliation.get("total_skill_professionalism_warnings", 0),
        "tracked_release_warnings": reconciliation.get("tracked_release_warnings", 0),
        "non_key_capability_advisory_warnings": non_key_count,
        "other_untracked_skill_eval_warnings": len(warnings) - non_key_count,
        "policy": reconciliation.get("policy", ""),
        "warnings": warnings,
    }


def _readiness_followups(result: RegressionResult, foundation: dict[str, Any]) -> list[dict[str, Any]]:
    followups: list[dict[str, Any]] = [asdict(item) for item in result.warnings]
    for item in result.known_warnings:
        payload = asdict(item)
        payload["followup_kind"] = "known accepted warning"
        followups.append(payload)
    for name, entry in sorted(foundation.items()):
        data = _dict(entry)
        if _string(data.get("status")) == "needs-review":
            followups.append(
                asdict(
                    Finding(
                        "key-foundation-capability-needs-review",
                        _string(data.get("path")) or name,
                        "key foundation capability remains needs-review",
                        "acceptable",
                        data.get("status"),
                        "info",
                    )
                )
            )
    return followups


def _agent_strict_status(agent_samples_strict: dict[str, Any]) -> str:
    if not agent_samples_strict.get("ran"):
        return "not-run"
    report = _dict(agent_samples_strict.get("report"))
    if int(agent_samples_strict.get("returncode") or 0) == 0 and int(report.get("failures") or 0) == 0:
        return "pass"
    return "fail"


def _summary(result: RegressionResult) -> dict[str, Any]:
    return {
        "blockers": len(result.blockers),
        "warnings": len(result.warnings),
        "known_warnings": len(result.known_warnings),
        "baseline_changes": len(result.baseline_changes),
    }


def _status_summary(items: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {"count": len(items), "statuses": {}}
    for entry in items.values():
        status = _string(_dict(entry).get("status")) or "unknown"
        summary["statuses"][status] = summary["statuses"].get(status, 0) + 1
    return summary


def _summary_line(summary: dict[str, Any]) -> str:
    statuses = ", ".join(f"{key}: {value}" for key, value in sorted(_dict(summary.get("statuses")).items()))
    return f"- Count: {summary.get('count', 0)}; Statuses: {statuses or '-'}"


def _mapping_lines(mapping: dict[str, Any]) -> str:
    if not mapping:
        return "- No data"
    return "\n".join(f"- {key}: {value}" for key, value in sorted(mapping.items()))


def _print_summary(result: RegressionResult) -> None:
    print(
        "validate-professionalism-regression: "
        f"status={result.status}; blockers={len(result.blockers)}; "
        f"warnings={len(result.warnings)}; known_warnings={len(result.known_warnings)}"
    )


def _is_missing(value: Any) -> bool:
    text = _string(value).casefold()
    return text in {"", "no", "missing", "absent", "weak"}


def _is_weak_evidence(value: Any) -> bool:
    text = _string(value).casefold()
    return text in {"", "no", "missing", "absent", "weak", "partial"}


def _is_without_reference_hint(value: Any) -> bool:
    text = _string(value).casefold()
    return text in {"", "no", "missing", "absent", "weak"}


def _is_anti_bloat_warning(warning: str) -> bool:
    folded = warning.casefold()
    return any(token in folded for token in ("bloat", "long markdown table", "body", "duplicate", "repeated", "move", "reference"))


def _coverage_count(value: Any) -> int:
    text = _string(value)
    match = re.search(r"\((\d+)\)", text)
    if match:
        return int(match.group(1))
    return 1 if text.casefold().startswith("yes") else 0


def _content_exception_paths(path: Path) -> list[str]:
    if not path.is_file():
        return []
    try:
        data = load_yaml_file(path)
    except ValidationProblem:
        return []
    if not isinstance(data, dict):
        return []
    paths: list[str] = []
    for entry in data.get("exceptions", []) or []:
        if isinstance(entry, dict) and isinstance(entry.get("path"), str):
            paths.append(entry["path"].strip())
    return sorted(paths)


def _known_warning_total(snapshot: dict[str, Any]) -> int:
    total = 0
    for group in ("professional_skills", "foundation_capabilities"):
        for entry in _dict(snapshot.get(group)).values():
            total += int(_dict(entry).get("known_warnings_count") or 0)
    return total


def _known_warning_type_budget(snapshot: dict[str, Any]) -> dict[str, int | None]:
    counts: dict[str, int] = {}
    for group in ("professional_skills", "foundation_capabilities"):
        for entry in _dict(snapshot.get(group)).values():
            for record in _warning_record_map(_dict(entry).get("known_warnings")).values():
                warning_type = _string(record.get("type")) or _warning_type(_string(record.get("message")))
                counts[warning_type] = counts.get(warning_type, 0) + 1
    return {
        "evidence_contract_missing_what_proves": 0,
        "trigger_lacks_concrete_route_or_evidence": 0,
        "body_bloat_exception": counts.get("body_bloat_exception", 0),
    }


def _known_warning_type_counts(findings: list[Finding]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for finding in findings:
        record = _dict(finding.baseline_value)
        warning_type = _string(record.get("type")) or _warning_type(finding.message)
        counts[warning_type] = counts.get(warning_type, 0) + 1
    return counts


def _warning_record_list(value: Any) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                message = _string(item.get("message"))
                if message:
                    record = dict(item)
                    record["message"] = message
                    records.append(record)
            elif isinstance(item, str) and item.strip():
                message = item.strip()
                records.append({"message": message, "type": _warning_type(message)})
    elif isinstance(value, str) and value.strip():
        message = value.strip()
        records.append({"message": message, "type": _warning_type(message)})
    return records


def _warning_record_map(value: Any) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                message = _string(item.get("message"))
                if message:
                    records[message] = dict(item)
            elif isinstance(item, str) and item.strip():
                message = item.strip()
                records[message] = {
                    "message": message,
                    "type": _warning_type(message),
                }
    elif isinstance(value, str) and value.strip():
        records[value.strip()] = {
            "message": value.strip(),
            "type": _warning_type(value),
        }
    return records


def _warning_message(value: Any) -> str:
    if isinstance(value, dict):
        return _string(value.get("message"))
    return _string(value)


def _warning_messages(value: Any) -> list[str]:
    if isinstance(value, list):
        messages: list[str] = []
        for item in value:
            if isinstance(item, dict):
                message = _string(item.get("message"))
                if message:
                    messages.append(message)
            elif isinstance(item, str) and item.strip():
                messages.append(item.strip())
        return messages
    return _string_list(value)


def _inferred_warning_scope(path: str) -> str:
    if "/professional-skills/" in path:
        return "professional-skill"
    name = Path(path).parent.name
    if name in ENHANCED_FOUNDATION_CAPABILITIES:
        return "enhanced-foundation-capability"
    if name in KEY_FOUNDATION_CAPABILITIES:
        return "key-foundation-capability"
    if "/foundation/capabilities/" in path:
        return "non-key-foundation-capability"
    return "authoring-template"


def _inferred_release_relevance(path: str, warning_type: str, warning: str) -> str:
    scope = _inferred_warning_scope(path)
    if scope == "professional-skill":
        return "release-blocking"
    if scope == "enhanced-foundation-capability":
        if warning_type in {"missing_failure_modes", "missing_quality_gate"}:
            return "release-blocking"
        return "release-review-required"
    if scope == "key-foundation-capability":
        if warning_type in {
            "weak_evidence_contract_strength",
            "weak_reference_precision",
            "evidence_contract_missing_term",
            "reference_loading_hint",
            "evidence_contract_missing_what_proves",
        }:
            return "release-review-required"
        folded = warning.casefold()
        if "evidence_contract_strength score" in folded or "reference_precision score" in folded:
            return "release-review-required"
        return "non-blocking-follow-up"
    return "advisory-only"


def _inferred_warning_reason(release_relevance: str) -> str:
    if release_relevance == "release-blocking":
        return "Release policy treats this professionalism warning as blocking for the affected top-level or required gate surface."
    if release_relevance == "release-review-required":
        return "Warning requires explicit release review because it affects an enhanced or key foundation capability surface."
    if release_relevance == "non-blocking-follow-up":
        return "Warning is tracked for key foundation follow-up and does not block release under current policy."
    return "Warning is advisory-only for this scope and does not block release under current policy."


def _warning_follow_up(record: dict[str, Any]) -> str:
    relevance = _string(record.get("release_relevance"))
    if relevance == "release-blocking":
        return "Fix before release."
    if relevance == "accepted-known-warning":
        return "Keep accepted-warning metadata and review on the recorded schedule."
    if relevance == "release-review-required":
        return "Review during release readiness; promote to blocker only if evidence/reference weakness affects the selected release surface."
    if relevance == "non-blocking-follow-up":
        return "Track as key foundation hardening follow-up."
    return "Track as advisory cleanup; no release action required."


def _warning_type(warning: str) -> str:
    folded = warning.casefold()
    if "evidence contract is missing 'what evidence proves'" in folded:
        return "evidence_contract_missing_what_proves"
    if "lacks concrete hidden risk, action, route, or evidence" in folded:
        return "trigger_lacks_concrete_route_or_evidence"
    if " weak: " in folded and " score " in folded:
        if "evidence_contract_strength" in folded:
            return "weak_evidence_contract_strength"
        if "reference_precision" in folded:
            return "weak_reference_precision"
        return "weak_dimension_score"
    if "evidence contract is missing" in folded:
        return "evidence_contract_missing_term"
    if "reference" in folded and ("hint" in folded or "linked" in folded or "governed" in folded):
        return "reference_loading_hint"
    if "missing failure modes" in folded:
        return "missing_failure_modes"
    if "missing quality gate" in folded:
        return "missing_quality_gate"
    if _is_anti_bloat_warning(warning):
        return "body_bloat_exception"
    return "other"


def _is_l1_anti_over_routing(expected: dict[str, Any], forbidden: dict[str, Any]) -> bool:
    if expected.get("complexity") != "L1":
        return False
    forbidden_text = " ".join(
        item
        for field_name in EXPECTED_ROUTING_FIELDS
        for item in _string_list(forbidden.get(field_name))
    ).casefold()
    return any(
        token in forbidden_text
        for token in (
            "change-impact-analyzer",
            "architecture-impact-reviewer",
            "security-privacy-gate",
            "delivery-release-gate",
            "payment-trading-extension",
            "web3-product-extension",
            "security gate",
            "delivery gate",
            "architecture gate",
        )
    )


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _display(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True)
    return str(value)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def dump_yaml(data: dict[str, Any]) -> str:
    lines: list[str] = []
    _emit_yaml_value(data, 0, lines)
    return "\n".join(lines).rstrip() + "\n"


def _emit_yaml_value(value: Any, indent: int, lines: list[str]) -> None:
    pad = " " * indent
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, dict):
                lines.append(f"{pad}{_yaml_key(key)}:")
                _emit_yaml_value(item, indent + 2, lines)
            elif isinstance(item, list):
                if not item:
                    lines.append(f"{pad}{_yaml_key(key)}: []")
                else:
                    lines.append(f"{pad}{_yaml_key(key)}:")
                    _emit_yaml_value(item, indent + 2, lines)
            else:
                lines.append(f"{pad}{_yaml_key(key)}: {_yaml_scalar(item)}")
        return
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                lines.append(f"{pad}-")
                _emit_yaml_value(item, indent + 2, lines)
            elif isinstance(item, list):
                lines.append(f"{pad}-")
                _emit_yaml_value(item, indent + 2, lines)
            else:
                lines.append(f"{pad}- {_yaml_scalar(item)}")
        return
    lines.append(f"{pad}{_yaml_scalar(value)}")


def _yaml_key(value: Any) -> str:
    text = str(value)
    if re.fullmatch(r"[A-Za-z0-9_.+/-]+", text):
        return text
    return _yaml_scalar(text)


def _yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(value)
    if value is None:
        return "null"
    text = str(value)
    if text == "":
        return '""'
    if re.fullmatch(r"[A-Za-z0-9_.+/@()-]+", text) and text.lower() not in {"true", "false", "null"}:
        return text
    escaped = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
    return f'"{escaped}"'


if __name__ == "__main__":
    raise SystemExit(main())
