#!/usr/bin/env python3
"""Generate a bounded summary for an opt-in Codex CLI live benchmark run."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import re
import sys
from pathlib import Path
from statistics import median
from typing import Any

from codegen_benchmark_manifest import EXPECTED_BENCHMARKS
from codex_live_benchmark_lib import (
    CAPABILITY_QUALITY_READY_REQUIRED_IDS,
    CASE_TIERS,
    CURRENT_HOME_SMOKE_EVIDENCE_LEVEL,
    LARGE_QUALITY_IMPROVEMENT_MIN_CAPABILITY_COUNT,
    LIVE_EVIDENCE_LEVEL,
    MODE_DEFAULT_VARIANTS,
    ROOT,
    SETUP_FAILURE_REASONS,
    SETUP_FAILURE_SUBREASONS,
    STRONG_CODEX_LIVE_ASSERTION_CASE_MIN,
    STRONG_CODEX_LIVE_RUNS_PER_VARIANT_MIN,
    STRICT_AUTH_POLICIES,
    STRICT_BENCHMARK_MODES,
    STRICT_CODEX_ENVIRONMENT_POLICIES,
    load_case_registry,
    codex_live_capability_coverage_summary,
    read_json,
    validate_status,
    write_json,
)


METRIC_KEYS = ("event_count", "command_execution_count", "file_change_count", "plan_update_count", "error_count")
USAGE_KEYS = ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens")
REDACTION_ARTIFACT_LABEL_LIMIT = 50
FORBIDDEN_REDACTION_MARKERS = ("/Users/", "/home/", "C:\\Users\\", "auth.json", "CODEX_API_KEY", "OPENAI_API_KEY", "sk-")
REDACTION_MARKER_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("/Users/", re.compile(r"/Users/[^\s\"'<>]+")),
    ("/home/", re.compile(r"/home/[^\s\"'<>]+")),
    ("C:\\Users\\", re.compile(r"[A-Za-z]:\\Users\\[^\s\"'<>]+")),
    ("auth.json", re.compile(r"auth\.json")),
    ("CODEX_API_KEY", re.compile(r"CODEX_API_KEY")),
    ("OPENAI_API_KEY", re.compile(r"OPENAI_API_KEY")),
    ("sk-", re.compile(r"sk-(?=[A-Za-z0-9_-]{10,})(?=[A-Za-z0-9_-]*[A-Z0-9])[A-Za-z0-9_-]+")),
)
PROCESS_CORE_PHASES = ("pdd", "ddd", "sdd", "tdd")
PROCESS_REVIEW_PHASES = ("review", "repair", "rereview")
_PROCESS_TRACE_VALIDATOR: Any = None
PROCESS_FALLBACK_FIELD_SOURCE = "case_metadata_fallback"
PROCESS_FALLBACK_SOURCE_ALIASES = {PROCESS_FALLBACK_FIELD_SOURCE, "inferred"}
KNOWN_UNRESOLVED_RELIABILITY_CASES = (
    {
        "case_id": "reliability/redis-cache-stampede-protection",
        "status": "known_no_improvement_not_run_in_current_core_ablation",
        "reason": "Known reliability weakness remains unresolved; this core capability ablation did not rerun the reliability case.",
    },
)
REQUIRED_CAPABILITY_ARTIFACTS = (
    "process-trace.json",
    "result.json",
    "grading/grading-result.json",
    "events.redacted.jsonl",
    "final.md",
    "diff.patch",
)
COMPACTION_REQUIRED_FIELDS = (
    "route_id",
    "selected_skills",
    "selected_capabilities",
    "required_quality_gates",
    "current_stage",
    "pdd_summary",
    "ddd_invariants",
    "sdd_decisions",
    "tdd_validation_plan",
    "changed_paths",
    "read_paths",
    "validation_results",
    "validation_freshness",
    "review_findings",
    "repair_events",
    "rereview_events",
    "residual_risk",
    "memory_references",
    "repo_graph_references",
    "active_skill_context",
    "last_material_edit_index",
    "last_validation_command_index",
)
CAPABILITY_PRIVACY_PATTERNS = (
    re.compile(r"/Users/[^\s\"'<>]+|/home/[^\s\"'<>]+|/private/var/[^\s\"'<>]+|/var/folders/[^\s\"'<>]+|/tmp/[^\s\"'<>]+"),
    re.compile(r"OPENAI_API_KEY|CODEX_API_KEY|sk-[A-Za-z0-9_-]{10,}", re.IGNORECASE),
)
PROCESS_REQUIRED_FIELDS = {
    "pdd": ("problem", "acceptance_criteria", "constraints", "validation_signal"),
    "ddd": ("domain_terms", "invariants", "ownership_decision", "side_effect_boundaries"),
    "sdd": ("modules", "public_api", "error_contract", "failure_modes", "logging_decision"),
    "tdd": (
        "acceptance_to_tests",
        "invariant_to_tests_or_code",
        "public_api_to_tests",
        "failure_mode_tests",
        "validation_commands",
    ),
}


def generate_summary(run_dir: Path) -> dict[str, Any]:
    """Aggregate run-manifest and result.json files into one schema v2 payload."""
    manifest = read_json(run_dir / "run-manifest.json")
    if not isinstance(manifest, dict):
        manifest = {}
    results = []
    for path in sorted(run_dir.glob("cases/*/*/run-*/result.json")):
        payload = read_json(path)
        if isinstance(payload, dict):
            payload = dict(payload)
            payload["_result_dir"] = path.parent
            results.append(payload)
    real_results = [
        result
        for result in results
        if result.get("artifact_status", result.get("status")) in {"collected", "failed", "partial"}
    ]
    benchmark_mode = str(manifest.get("benchmark_mode") or "clean-paired")
    status = _summary_status(manifest, real_results)
    logging_summary = _logging_summary(run_dir)
    variant_order = _variant_order(manifest, real_results, benchmark_mode)
    variants = {variant: _variant_summary(_results_for_variant(real_results, variant)) for variant in variant_order}
    deltas = _variant_deltas(variants)
    for variant in variants:
        variants[variant]["delta_vs_baseline_clean"] = deltas.get(f"{variant}_vs_baseline_clean", {})
    cases_summary = _cases_summary(real_results)
    capability_artifact_evidence = _capability_artifact_evidence(real_results)
    case_metadata = _case_metadata_by_id()

    cases = sorted({str(result.get("case_id")) for result in real_results if result.get("case_id")})
    if not cases and isinstance(manifest.get("cases"), list):
        cases = [str(case_id) for case_id in manifest["cases"]]
    assertion_cases = sorted(
        {str(result.get("case_id")) for result in real_results if result.get("grading_mode") == "assertion"}
    )
    telemetry_only_cases = sorted(
        {str(result.get("case_id")) for result in real_results if result.get("grading_mode") == "telemetry_only"}
    )
    auth_policy = _common_value(manifest, real_results, "auth_policy", "borrow-current")
    environment_policy = _common_value(manifest, real_results, "codex_environment_policy", "auth_borrowed_clean")
    environment_flags = _environment_flags(real_results)
    changeforge_metadata = _changeforge_summary_metadata(manifest, real_results)
    current_home_full_result_count = sum(
        1
        for result in real_results
        if result.get("auth_policy") == "current-home-full"
        or result.get("codex_environment_policy") == "current_home_full"
    )

    evidence_level = (
        CURRENT_HOME_SMOKE_EVIDENCE_LEVEL if benchmark_mode == "current-home-smoke" else LIVE_EVIDENCE_LEVEL
    )
    evidence_scope_detail = _evidence_scope_detail(
        benchmark_mode,
        variants=variants,
        cases_summary=cases_summary,
    )
    evidence_scope = _evidence_scope(benchmark_mode, evidence_scope_detail)
    failure_categories = _counts(real_results, "failure_category")
    dominant_failure_category, _dominant_failure_count = _dominant_bucket(failure_categories)
    setup_failure_reasons = _reason_counts(real_results, "setup_failure_reason", "setup_failed")
    dominant_setup_failure_reason = _dominant_reason(setup_failure_reasons)
    setup_failure_subreasons = _setup_subreason_counts(real_results)
    dominant_setup_failure_subreason = _dominant_subreason(setup_failure_subreasons)
    unknown_setup_failure_rate = _unknown_setup_failure_rate(setup_failure_reasons)
    effect = _effect_evaluation(
        benchmark_mode,
        variants=variants,
        cases_summary=cases_summary,
        failure_categories=failure_categories,
        setup_failure_reasons=setup_failure_reasons,
        setup_failure_subreasons=setup_failure_subreasons,
        evidence_scope_detail=evidence_scope_detail,
    )
    summary = {
        "schema_version": 2,
        "generated_by": "scripts/generate-codex-live-summary.py",
        "status": status,
        "evidence_level": evidence_level,
        "evidence_scope": evidence_scope,
        "evidence_scope_ready": evidence_scope_detail["evidence_scope_ready"],
        "evidence_scope_detail": evidence_scope_detail,
        "evidence_status": _summary_evidence_status(status, logging_summary),
        "effect_verdict": effect["verdict"],
        "effect_status": effect["status"],
        "effect_summary": effect["summary"],
        "benchmark_mode": benchmark_mode,
        "codex_home_policy": _codex_home_policy(manifest, real_results, benchmark_mode),
        "auth_policy": auth_policy,
        "codex_environment_policy": environment_policy,
        **changeforge_metadata,
        "strict_benchmark_eligible": _strict_benchmark_eligible(
            benchmark_mode,
            auth_policy,
            environment_policy,
            environment_flags,
            changeforge_metadata,
            current_home_full_result_count,
            real_results,
        ),
        "publishable_for_strict_benchmark": benchmark_mode in STRICT_BENCHMARK_MODES,
        "run_id": str(manifest.get("run_id") or run_dir.name),
        "run_dir": "<run-dir>",
        "case_count": len(cases),
        "actual_run_case_count": len(cases),
        "actual_run_cases": cases,
        "capability_core_requested": bool(manifest.get("capability_core_requested")),
        "selected_capability_case_count": int(manifest.get("selected_capability_case_count", 0) or 0),
        "selected_capability_cases": list(manifest.get("selected_capability_cases", []))
        if isinstance(manifest.get("selected_capability_cases"), list)
        else [],
        "capability_matrix_path": str(manifest.get("capability_matrix_path") or "evals/codex-live/capability-matrix.yaml"),
        "assertion_case_count": len(assertion_cases),
        "telemetry_only_case_count": len(telemetry_only_cases),
        "result_count": len(real_results),
        "benchmark_eligible_result_count": sum(1 for result in real_results if result.get("benchmark_eligible") is True),
        "benchmark_passed_result_count": sum(1 for result in real_results if result.get("benchmark_passed") is True),
        "not_collected_grading_count": sum(
            1 for result in real_results if result.get("grading_status") == "not_collected"
        ),
        "telemetry_only_result_count": sum(
            1 for result in real_results if result.get("grading_status") == "telemetry_only"
        ),
        "contaminated_result_count": sum(
            1 for result in real_results if (result.get("contamination") or {}).get("contaminated") is True
        ),
        "failure_categories": failure_categories,
        "dominant_failure_category": dominant_failure_category,
        "setup_failure_reasons": setup_failure_reasons,
        "dominant_setup_failure_reason": dominant_setup_failure_reason,
        "setup_failure_subreasons": setup_failure_subreasons,
        "dominant_setup_failure_subreason": dominant_setup_failure_subreason,
        "unknown_setup_failure_rate": unknown_setup_failure_rate,
        "test_suite_failure_reasons": _reason_counts(real_results, "test_suite_failure_reason", "test_suite_failed"),
        "security_failure_reasons": _reason_counts(
            real_results,
            "security_failure_reason",
            "security_checks_failed",
        ),
        "current_home_result_count": sum(1 for result in real_results if result.get("codex_home_mode") == "current"),
        "current_home_full_result_count": current_home_full_result_count,
        **environment_flags,
        "variants": variants,
        "delta": deltas,
        "cases": cases,
        "cases_summary": cases_summary,
        "capability_artifact_evidence": capability_artifact_evidence,
        "compact_context_summary": _compact_context_summary(capability_artifact_evidence),
        "coverage_summary": _coverage_summary(cases, cases_summary, case_metadata),
        "cost_summary": _cost_summary(real_results, variants),
        "stability_summary": _stability_summary(real_results, variants, cases_summary, manifest),
        "logging_summary": logging_summary,
        "process_compliance_summary": _process_compliance_summary(real_results),
        "telemetry": {
            "event_count": sum(int((result.get("metrics") or {}).get("event_count", 0) or 0) for result in real_results),
            "parse_error_count": sum(len((result.get("metrics") or {}).get("parse_errors", [])) for result in real_results),
        },
        "limitations": _limitations(
            benchmark_mode,
            assertion_case_count=len(assertion_cases),
            variants=variants,
            evidence_scope=evidence_scope,
            unknown_setup_failure_rate=unknown_setup_failure_rate,
        ),
    }
    summary["case_result_summary"] = _case_result_summary(cases_summary)
    summary["capability_coverage_summary"] = codex_live_capability_coverage_summary(summary)
    summary["quality_improvement_summary"] = _quality_improvement_summary(
        variants,
        cases_summary,
        summary["case_result_summary"],
        summary["capability_coverage_summary"],
        capability_artifact_evidence,
    )
    return summary


def _case_metadata_by_id() -> dict[str, dict[str, Any]]:
    try:
        cases = load_case_registry()
    except Exception:
        return {}
    return {
        case.id: {
            "tier": case.tier,
            "coverage_dimensions": list(case.coverage_dimensions),
            "publishable_for_strict": case.publishable_for_strict,
            "grading_mode": case.grading_mode,
            "enabled": case.enabled,
        }
        for case in cases
    }


def _logging_summary(run_dir: Path) -> dict[str, Any]:
    log_paths = [run_dir / "run.log.jsonl", run_dir / "timeline.jsonl"]
    process_traces = sorted(run_dir.glob("cases/*/*/run-*/process-trace.json"))
    redaction_errors: list[dict[str, str]] = []
    max_event_size = 0
    counts = {"run.log.jsonl": 0, "timeline.jsonl": 0}

    def record_redaction_errors(path: Path, text: str) -> None:
        artifact = _bounded_redaction_artifact_label(run_dir, path)
        for error in _redaction_errors(text):
            redaction_errors.append({"artifact": artifact, **error})

    for path in log_paths:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            counts[path.name] += 1
            max_event_size = max(max_event_size, len(line.encode("utf-8")))
            record_redaction_errors(path, line)
    for path in process_traces:
        text = path.read_text(encoding="utf-8", errors="ignore")
        max_event_size = max(max_event_size, len(text.encode("utf-8")))
        record_redaction_errors(path, text)
    redaction_artifacts = sorted({error["artifact"] for error in redaction_errors})
    redaction_markers = sorted({error["marker"] for error in redaction_errors})
    first_error = redaction_errors[0] if redaction_errors else {}
    return {
        "run_log_events": counts["run.log.jsonl"],
        "timeline_events": counts["timeline.jsonl"],
        "process_trace_count": len(process_traces),
        "redaction_status": "pass" if not redaction_errors else "fail",
        "redaction_error_count": len(redaction_errors),
        "redaction_error_markers": redaction_markers,
        "redaction_error_artifact_count": len(redaction_artifacts),
        "redaction_error_artifacts": redaction_artifacts[:REDACTION_ARTIFACT_LABEL_LIMIT],
        "redaction_error_artifacts_truncated": len(redaction_artifacts) > REDACTION_ARTIFACT_LABEL_LIMIT,
        "first_redaction_error_artifact": first_error.get("artifact"),
        "first_redaction_error_marker": first_error.get("marker"),
        "first_redaction_error_excerpt_hash": first_error.get("excerpt_hash"),
        "max_event_size_bytes": max_event_size,
    }


def _process_compliance_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    traces = [_load_process_trace(result) for result in results]
    traces = [trace for trace in traces if isinstance(trace, dict)]
    trace_count = len(traces)

    def phase_rate(phase: str, status: str) -> float:
        return _trace_rate(
            trace_count,
            sum(1 for trace in traces if (trace.get("phase_status") or {}).get(phase) == status),
        )

    def traceability_rate(field: str) -> float:
        return _trace_rate(trace_count, sum(1 for trace in traces if (trace.get("traceability") or {}).get(field) is True))

    def required_field_fallback_rate(phase: str) -> float:
        required_fields = _required_process_fields(phase)
        denominator = trace_count * len(required_fields)
        fallback_fields = 0
        for trace in traces:
            facts = trace.get("process_facts")
            phase_payload = facts.get(phase) if isinstance(facts, dict) else None
            if not isinstance(phase_payload, dict):
                continue
            field_sources = phase_payload.get("_field_sources")
            sources = field_sources if isinstance(field_sources, dict) else {}
            raw_inferred_fields = phase_payload.get("_inferred_fields")
            inferred_fields = {str(field) for field in raw_inferred_fields} if isinstance(raw_inferred_fields, list) else set()
            for field in required_fields:
                source = str(sources.get(field) or "")
                if field in inferred_fields or _source_is_fallback(source):
                    fallback_fields += 1
        return _trace_rate(denominator, fallback_fields)

    def all_core_phase_rate(allowed_statuses: set[str]) -> float:
        return _trace_rate(
            trace_count,
            sum(
                1
                for trace in traces
                if all((trace.get("phase_status") or {}).get(phase) in allowed_statuses for phase in PROCESS_CORE_PHASES)
            ),
        )

    summary = {
        "pdd_present_rate": phase_rate("pdd", "present"),
        "ddd_present_rate": phase_rate("ddd", "present"),
        "sdd_present_rate": phase_rate("sdd", "present"),
        "tdd_present_rate": phase_rate("tdd", "present"),
        "review_present_rate": phase_rate("review", "present"),
        "repair_present_rate": phase_rate("repair", "present"),
        "rereview_present_rate": phase_rate("rereview", "present"),
        "pdd_inferred_rate": phase_rate("pdd", "inferred"),
        "ddd_inferred_rate": phase_rate("ddd", "inferred"),
        "sdd_inferred_rate": phase_rate("sdd", "inferred"),
        "tdd_inferred_rate": phase_rate("tdd", "inferred"),
        "review_inferred_rate": phase_rate("review", "inferred"),
        "repair_inferred_rate": phase_rate("repair", "inferred"),
        "rereview_inferred_rate": phase_rate("rereview", "inferred"),
        "pdd_degraded_rate": phase_rate("pdd", "degraded"),
        "ddd_degraded_rate": phase_rate("ddd", "degraded"),
        "sdd_degraded_rate": phase_rate("sdd", "degraded"),
        "tdd_degraded_rate": phase_rate("tdd", "degraded"),
        "review_degraded_rate": phase_rate("review", "degraded"),
        "repair_degraded_rate": phase_rate("repair", "degraded"),
        "rereview_degraded_rate": phase_rate("rereview", "degraded"),
        "pdd_required_field_fallback_rate": required_field_fallback_rate("pdd"),
        "ddd_required_field_fallback_rate": required_field_fallback_rate("ddd"),
        "sdd_required_field_fallback_rate": required_field_fallback_rate("sdd"),
        "tdd_required_field_fallback_rate": required_field_fallback_rate("tdd"),
        "all_core_phases_present_rate": all_core_phase_rate({"present"}),
        "all_core_phases_degraded_or_present_rate": all_core_phase_rate({"present", "degraded"}),
        "all_core_phases_inferred_only_rate": all_core_phase_rate({"inferred"}),
        "pdd_to_tdd_traceability_rate": traceability_rate("pdd_acceptance_to_tdd_tests"),
        "ddd_invariant_test_or_code_coverage_rate": traceability_rate("ddd_invariants_to_tdd_tests"),
        "sdd_public_api_validation_rate": traceability_rate("sdd_public_api_to_tdd_tests"),
        "sdd_failure_mode_validation_rate": traceability_rate("sdd_failure_modes_to_tdd_tests"),
        "sdd_logging_validation_rate": traceability_rate("sdd_logging_to_tdd_tests"),
        "validation_command_present_rate": _trace_rate(
            trace_count,
            sum(1 for trace in traces if trace.get("validation_commands")),
        ),
        "process_trace_count": trace_count,
    }
    fallback_rates = [
        summary["pdd_required_field_fallback_rate"],
        summary["ddd_required_field_fallback_rate"],
        summary["sdd_required_field_fallback_rate"],
        summary["tdd_required_field_fallback_rate"],
    ]
    summary["required_field_fallback_rate"] = round(sum(fallback_rates) / len(fallback_rates), 4)
    summary["process_trace_inferred_only_rate"] = summary["all_core_phases_inferred_only_rate"]
    summary["review_flow_present_rate"] = _trace_rate(
        trace_count,
        sum(
            1
            for trace in traces
            if all((trace.get("phase_status") or {}).get(phase) == "present" for phase in PROCESS_REVIEW_PHASES)
        ),
    )
    summary["explicit_trace_contract"] = {
        "route_manifest": "changeforge_route or equivalent route manifest",
        "pdd": "PDD acceptance trace",
        "ddd": "DDD invariant trace",
        "sdd": "SDD placement and error-contract trace",
        "tdd": "TDD validation trace",
        "inferred_only_label": "process_trace_inferred_only",
    }
    return summary


def _load_process_trace(result: dict[str, Any]) -> dict[str, Any] | None:
    result_dir = result.get("_result_dir")
    if not isinstance(result_dir, Path):
        return None
    trace_path = result_dir / "process-trace.json"
    payload = read_json(trace_path)
    return payload if isinstance(payload, dict) else None


def _trace_rate(denominator: int, numerator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def _required_process_fields(phase: str) -> tuple[str, ...]:
    return PROCESS_REQUIRED_FIELDS.get(phase, ())


def _source_is_fallback(source: str) -> bool:
    normalized = str(source).split(":", 1)[0]
    return normalized in PROCESS_FALLBACK_SOURCE_ALIASES


def _redaction_errors(text: str) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    for marker, pattern in REDACTION_MARKER_PATTERNS:
        match = pattern.search(text)
        if match is None:
            continue
        start = max(0, match.start() - 64)
        end = min(len(text), match.end() + 64)
        excerpt = text[start:end]
        errors.append(
            {
                "marker": marker,
                "excerpt_hash": hashlib.sha256(excerpt.encode("utf-8", errors="ignore")).hexdigest(),
            }
        )
    return errors


def _bounded_redaction_artifact_label(run_dir: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(run_dir.resolve()).as_posix()
    except ValueError:
        return path.name


def _summary_status(manifest: dict[str, Any], results: list[dict[str, Any]]) -> str:
    if not results:
        return validate_status(manifest.get("status", "not_collected"))
    artifact_statuses = [str(result.get("artifact_status", result.get("status"))) for result in results]
    if any(status == "failed" for status in artifact_statuses):
        return "partial" if any(status == "collected" for status in artifact_statuses) else "failed"
    if any(status == "partial" for status in artifact_statuses):
        return "partial"
    return "collected"


def _variant_order(manifest: dict[str, Any], results: list[dict[str, Any]], benchmark_mode: str) -> list[str]:
    ordered: list[str] = []
    manifest_variants = manifest.get("variants")
    if isinstance(manifest_variants, list):
        ordered.extend(str(variant) for variant in manifest_variants)
    ordered.extend(str(result.get("variant")) for result in results if result.get("variant"))
    if not ordered and benchmark_mode in MODE_DEFAULT_VARIANTS:
        ordered.extend(MODE_DEFAULT_VARIANTS[benchmark_mode])
    return list(dict.fromkeys(ordered))


def _results_for_variant(results: list[dict[str, Any]], variant: str) -> list[dict[str, Any]]:
    return [result for result in results if result.get("variant") == variant]


def _variant_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    eligible = [result for result in results if result.get("benchmark_eligible") is True]
    passed = [result for result in eligible if result.get("benchmark_passed") is True]
    security = _security_metric_buckets(results)
    setup_failure_reasons = _reason_counts(results, "setup_failure_reason", "setup_failed")
    setup_failure_subreasons = _setup_subreason_counts(results)
    changeforge_metadata = _changeforge_variant_metadata(results)
    return {
        "run_count": len({int(result.get("run_index", 0) or 0) for result in results if result.get("run_index")}),
        "case_count": len({str(result.get("case_id")) for result in results if result.get("case_id")}),
        "result_count": len(results),
        **changeforge_metadata,
        "artifact_status_counts": _counts(results, "artifact_status"),
        "grading_status_counts": _counts(results, "grading_status"),
        "failure_categories": _counts(results, "failure_category"),
        "setup_failure_reasons": setup_failure_reasons,
        "dominant_setup_failure_reason": _dominant_reason(setup_failure_reasons),
        "setup_failure_subreasons": setup_failure_subreasons,
        "dominant_setup_failure_subreason": _dominant_subreason(setup_failure_subreasons),
        "unknown_setup_failure_rate": _unknown_setup_failure_rate(setup_failure_reasons),
        "test_suite_failure_reasons": _reason_counts(results, "test_suite_failure_reason", "test_suite_failed"),
        "security_failure_reasons": _reason_counts(results, "security_failure_reason", "security_checks_failed"),
        "benchmark_eligible_result_count": len(eligible),
        "benchmark_passed_result_count": len(passed),
        "pass_rate": _rate(len(passed), len(eligible)),
        "pass_rate_ci_note": "descriptive only; small sample",
        "security_pass_rate": _rate(len(security["passed"]), len(security["eligible"])),
        "security_assertion_failure_rate": _rate(len(security["assertion_failed"]), len(security["eligible"])),
        "security_check_execution_failure_rate": _rate(len(security["execution_failed"]), len(results)),
        "security_failure_rate": _rate(len(security["assertion_failed"]), len(security["eligible"])),
        "security_failure_rate_definition": "alias of security_assertion_failure_rate; execution failures are tracked separately",
        "telemetry_only_result_count": sum(1 for result in results if result.get("grading_status") == "telemetry_only"),
        "not_collected_grading_count": sum(1 for result in results if result.get("grading_status") == "not_collected"),
        "contaminated_result_count": sum(
            1 for result in results if (result.get("contamination") or {}).get("contaminated") is True
        ),
        "average_usage": _average_usage(results),
        "median_usage": _median_usage(results),
        "min_usage": _min_usage(results),
        "max_usage": _max_usage(results),
        "average_metrics": _average_metrics(results),
        "median_metrics": _median_metrics(results),
        "min_metrics": _min_metrics(results),
        "max_metrics": _max_metrics(results),
        "average_event_count": _average_metrics(results)["event_count"],
        "average_file_change_count": _average_metrics(results)["file_change_count"],
        "average_command_execution_count": _average_metrics(results)["command_execution_count"],
    }


def _security_metric_buckets(results: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Separate assertion failures from missing or non-executable security checks."""
    eligible = [result for result in results if "security_checks_passed" in (result.get("grading") or {})]
    passed = [result for result in eligible if (result.get("grading") or {}).get("security_checks_passed") is True]
    assertion_failed = [
        result for result in eligible if (result.get("grading") or {}).get("security_checks_passed") is False
    ]
    execution_failed = [
        result
        for result in results
        if result.get("security_failure_reason") in {"missing_security_script", "unknown"}
        and result.get("failure_category") == "security_checks_failed"
    ]
    return {
        "eligible": eligible,
        "passed": passed,
        "assertion_failed": assertion_failed,
        "execution_failed": execution_failed,
    }


def _counts(results: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    missing_value = "grading_not_collected" if key == "failure_category" else "not_collected"
    for result in results:
        value = str(result.get(key) or missing_value)
        counts[value] = counts.get(value, 0) + 1
    return counts


def _reason_counts(results: list[dict[str, Any]], key: str, matching_failure_category: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for result in results:
        reason = _reason_for_result(result, key, matching_failure_category)
        counts[reason] = counts.get(reason, 0) + 1
    return counts


def _setup_subreason_counts(results: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for result in results:
        subreason = _setup_subreason_for_result(result)
        counts[subreason] = counts.get(subreason, 0) + 1
    return counts


def _reason_for_result(result: dict[str, Any], key: str, matching_failure_category: str) -> str:
    value = result.get(key)
    grading = result.get("grading")
    if not value and isinstance(grading, dict):
        value = grading.get(key)
    if (
        key == "setup_failure_reason"
        and result.get("failure_category") == matching_failure_category
        and (not value or value == "unknown")
    ):
        value = _setup_reason_from_artifacts(result)
    if not value and result.get("failure_category") == matching_failure_category:
        value = "unknown"
    return str(value or "none")


def _setup_subreason_for_result(result: dict[str, Any]) -> str:
    setup_reason = _reason_for_result(result, "setup_failure_reason", "setup_failed")
    if setup_reason == "none":
        return "none"
    value = result.get("setup_failure_subreason")
    grading = result.get("grading")
    if not value and isinstance(grading, dict):
        value = grading.get("setup_failure_subreason")
    if not value or value in {"none", "unknown"}:
        value = _setup_subreason_from_artifacts(result, setup_reason)
    value = str(value or "unknown")
    return value if value in SETUP_FAILURE_SUBREASONS else "unknown"


def _setup_reason_from_artifacts(result: dict[str, Any]) -> str:
    result_dir = result.get("_result_dir")
    if not isinstance(result_dir, Path):
        return "unknown"
    chunks: list[str] = []
    for rel_path in (
        "grading/grading-result.json",
        "grading/setup.log",
        "grading/run-codegen-benchmarks.stdout.log",
        "grading/run-codegen-benchmarks.stderr.log",
    ):
        path = result_dir / rel_path
        if not path.is_file():
            continue
        try:
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    if not chunks:
        return "unknown"
    return _classify_setup_reason_from_text("\n".join(chunks))


def _setup_subreason_from_artifacts(result: dict[str, Any], setup_reason: str) -> str:
    result_dir = result.get("_result_dir")
    if not isinstance(result_dir, Path) or setup_reason == "none":
        return "none" if setup_reason == "none" else "unknown"
    chunks: list[str] = []
    for rel_path in (
        "grading/grading-result.json",
        "grading/setup.log",
        "grading/run-codegen-benchmarks.stderr.log",
    ):
        path = result_dir / rel_path
        if path.is_file():
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    text = "\n".join(chunks).casefold()
    if setup_reason == "missing_env_root":
        return "missing_env_root"
    if setup_reason == "missing_harness":
        return "missing_harness"
    if setup_reason != "setup_script_modified_bad_path":
        return "unknown"
    if "expected starter-repo cwd" in text or "wrong cwd" in text:
        return "wrong_cwd"
    if "../../.." in text or "..\\..\\.." in text:
        return "starter_fragile_path"
    return "classifier_uncertain"


def _classify_setup_reason_from_text(text: str) -> str:
    lowered = text.casefold()
    fixed_parent_harness_missing = (
        "codegen_benchmark_harness.py" in lowered
        and ("../../.." in lowered or "..\\..\\.." in lowered)
        and ("no such file" in lowered or "can't open file" in lowered or "not found" in lowered)
    )
    missing_env_root = (
        "changeforge_codegen_root is unset" in lowered
        or "changeforge_codegen_root is empty" in lowered
        or "set changeforge_codegen_root" in lowered
        or ("changeforge_codegen_root" in lowered and ("unset" in lowered or "empty" in lowered or "not set" in lowered))
    )
    harness_missing = (
        "codegen_benchmark_harness.py" in lowered
        and ("no such file" in lowered or "can't open file" in lowered or "not found" in lowered)
    )
    if (
        "setup.sh is missing" in lowered
        or "candidate/setup.sh missing" in lowered
        or "setup.sh: no such file" in lowered
        or "starter-repo/setup.sh: missing" in lowered
    ):
        return "setup_script_missing"
    if "candidate lacks required starter file" in lowered or (
        "missing starter readme" in lowered or "starter readme" in lowered and "missing" in lowered
    ):
        return "candidate_removed_required_file"
    if fixed_parent_harness_missing:
        return "setup_script_modified_bad_path"
    if missing_env_root:
        return "missing_env_root"
    if harness_missing:
        return "missing_harness"
    if re.search(
        r"(?i)(ModuleNotFoundError:\s*No module named|ImportError:\s*(cannot import|No module named)|"
        r"No module named ['\"][^'\"]+['\"]|package install failed|dependency install failed)",
        text,
    ):
        return "dependency_install_failed"
    if any(token in lowered for token in ("syntaxerror", "compileall", "py_compile", "python compile")):
        return "python_compile_failed"
    if re.search(
        r"(?im)(^(?:bash|sh): [^\n]*permission denied|"
        r"PermissionError:\s*\[Errno 13\][^\n]*permission denied|"
        r"OSError:\s*\[Errno 13\][^\n]*permission denied|errno 13[^\n]*permission denied)",
        text,
    ):
        return "permission_denied"
    if re.search(r"(?im)(^[^\n:]+: command not found|bad interpreter:)", text):
        return "shell_error"
    return "unknown"


def _dominant_reason(reasons: dict[str, int]) -> str:
    buckets = {reason: count for reason, count in reasons.items() if reason != "none" and count > 0}
    if not buckets:
        buckets = {reason: count for reason, count in reasons.items() if count > 0}
    if not buckets:
        return "none"
    reason, _count = max(buckets.items(), key=lambda item: (item[1], item[0]))
    return reason if reason in SETUP_FAILURE_REASONS else "unknown"


def _dominant_subreason(subreasons: dict[str, int]) -> str:
    buckets = {subreason: count for subreason, count in subreasons.items() if subreason != "none" and count > 0}
    if not buckets:
        buckets = {subreason: count for subreason, count in subreasons.items() if count > 0}
    if not buckets:
        return "none"
    subreason, _count = max(buckets.items(), key=lambda item: (item[1], item[0]))
    return subreason if subreason in SETUP_FAILURE_SUBREASONS else "unknown"


def _unknown_setup_failure_rate(reasons: dict[str, int]) -> float:
    denominator = sum(count for reason, count in reasons.items() if reason != "none")
    if denominator <= 0:
        return 0.0
    return round(int(reasons.get("unknown", 0) or 0) / denominator, 4)


def _average_usage(results: list[dict[str, Any]]) -> dict[str, float]:
    return _numeric_summary(results, USAGE_KEYS, source="usage", operation="average")


def _median_usage(results: list[dict[str, Any]]) -> dict[str, float]:
    return _numeric_summary(results, USAGE_KEYS, source="usage", operation="median")


def _min_usage(results: list[dict[str, Any]]) -> dict[str, float]:
    return _numeric_summary(results, USAGE_KEYS, source="usage", operation="min")


def _max_usage(results: list[dict[str, Any]]) -> dict[str, float]:
    return _numeric_summary(results, USAGE_KEYS, source="usage", operation="max")


def _average_metrics(results: list[dict[str, Any]]) -> dict[str, float]:
    return _numeric_summary(results, METRIC_KEYS, source="metrics", operation="average")


def _median_metrics(results: list[dict[str, Any]]) -> dict[str, float]:
    return _numeric_summary(results, METRIC_KEYS, source="metrics", operation="median")


def _min_metrics(results: list[dict[str, Any]]) -> dict[str, float]:
    return _numeric_summary(results, METRIC_KEYS, source="metrics", operation="min")


def _max_metrics(results: list[dict[str, Any]]) -> dict[str, float]:
    return _numeric_summary(results, METRIC_KEYS, source="metrics", operation="max")


def _numeric_summary(
    results: list[dict[str, Any]],
    keys: tuple[str, ...],
    *,
    source: str,
    operation: str,
) -> dict[str, float]:
    values = {key: [] for key in keys}
    for result in results:
        metrics = result.get("metrics") or {}
        source_payload = (metrics.get("usage") or {}) if source == "usage" else metrics
        for key in keys:
            values[key].append(int(source_payload.get(key, 0) or 0))
    if operation == "average":
        return {key: round(sum(series) / max(len(series), 1), 2) for key, series in values.items()}
    if operation == "median":
        return {key: round(float(median(series)), 2) if series else 0.0 for key, series in values.items()}
    if operation == "min":
        return {key: min(series) if series else 0 for key, series in values.items()}
    if operation == "max":
        return {key: max(series) if series else 0 for key, series in values.items()}
    raise ValueError(f"unknown summary operation {operation!r}")


def _rate(numerator: int, denominator: int) -> float | str:
    if denominator == 0:
        return "not_collected"
    return round(numerator / denominator, 4)


def _evidence_scope(benchmark_mode: str, detail: dict[str, Any]) -> str:
    if benchmark_mode == "current-home-smoke":
        return "current_home_smoke"
    if detail.get("evidence_scope_ready") is True:
        return "multi_case_ablation_3_run"
    return "smoke"


def _evidence_scope_detail(
    benchmark_mode: str,
    *,
    variants: dict[str, dict[str, Any]],
    cases_summary: dict[str, Any],
) -> dict[str, Any]:
    required_variants = list(MODE_DEFAULT_VARIANTS["ablation"])
    assertion_cases = {
        case_id: case_summary
        for case_id, case_summary in cases_summary.items()
        if isinstance(case_summary, dict) and case_summary.get("grading_mode") == "assertion"
    }
    per_variant_case_counts: dict[str, int] = {}
    per_variant_min_runs: dict[str, int] = {}
    for variant in required_variants:
        runs: list[int] = []
        for case_summary in assertion_cases.values():
            variant_payload = (case_summary.get("variants") or {}).get(variant)
            if isinstance(variant_payload, dict):
                runs.append(int(variant_payload.get("runs", 0) or 0))
        per_variant_case_counts[variant] = len(runs)
        per_variant_min_runs[variant] = min(runs) if runs else 0

    observed_min_runs = min(per_variant_min_runs.values()) if per_variant_min_runs else 0
    evidence_scope_ready = bool(
        benchmark_mode == "ablation"
        and len(assertion_cases) >= STRONG_CODEX_LIVE_ASSERTION_CASE_MIN
        and all(
            per_variant_case_counts.get(variant, 0) >= STRONG_CODEX_LIVE_ASSERTION_CASE_MIN
            for variant in required_variants
        )
        and observed_min_runs >= STRONG_CODEX_LIVE_RUNS_PER_VARIANT_MIN
    )
    if benchmark_mode == "current-home-smoke":
        reason = "current-home-smoke mode is not strict comparative evidence"
    elif evidence_scope_ready:
        reason = "ablation evidence includes the required assertion-backed case count and repeated runs"
    elif benchmark_mode != "ablation":
        reason = "strict clean-paired evidence is smoke-scale until ablation covers the required cases and runs"
    elif len(assertion_cases) < STRONG_CODEX_LIVE_ASSERTION_CASE_MIN:
        reason = "ablation evidence has too few assertion-backed cases for the stronger claim"
    elif observed_min_runs < STRONG_CODEX_LIVE_RUNS_PER_VARIANT_MIN:
        reason = "ablation evidence has too few runs per required variant for the stronger claim"
    else:
        reason = "ablation evidence is missing one or more required variant/case combinations"
    return {
        "evidence_scope_ready": evidence_scope_ready,
        "required_benchmark_mode": "ablation",
        "required_assertion_case_count": STRONG_CODEX_LIVE_ASSERTION_CASE_MIN,
        "required_runs_per_variant": STRONG_CODEX_LIVE_RUNS_PER_VARIANT_MIN,
        "required_variants": required_variants,
        "observed_benchmark_mode": benchmark_mode,
        "observed_assertion_case_count": len(assertion_cases),
        "observed_variant_case_counts": per_variant_case_counts,
        "observed_min_runs_per_required_variant": observed_min_runs,
        "reason": reason,
    }


def _evidence_status(status: str) -> str:
    if status == "collected":
        return "pass"
    if status == "partial":
        return "partial"
    if status == "failed":
        return "fail"
    return "not_collected"


def _summary_evidence_status(status: str, logging_summary: dict[str, Any]) -> str:
    if logging_summary.get("redaction_status") == "fail":
        return "fail"
    return _evidence_status(status)


def _effect_evaluation(
    benchmark_mode: str,
    *,
    variants: dict[str, dict[str, Any]],
    cases_summary: dict[str, Any],
    failure_categories: dict[str, int],
    setup_failure_reasons: dict[str, int],
    setup_failure_subreasons: dict[str, int],
    evidence_scope_detail: dict[str, Any],
) -> dict[str, Any]:
    required_variants = list(MODE_DEFAULT_VARIANTS["ablation"])
    missing_variants = [variant for variant in required_variants if variant not in variants]
    eligible_counts = {
        variant: int((variants.get(variant) or {}).get("benchmark_eligible_result_count", 0) or 0)
        for variant in required_variants
    }
    rates = {variant: (variants.get(variant) or {}).get("pass_rate") for variant in required_variants}
    setup_counts = {
        variant: int(((variants.get(variant) or {}).get("failure_categories") or {}).get("setup_failed", 0) or 0)
        for variant in required_variants
    }
    result_counts = {
        variant: int((variants.get(variant) or {}).get("result_count", 0) or 0)
        for variant in required_variants
    }
    setup_rates = {variant: _rate(setup_counts[variant], result_counts[variant]) for variant in required_variants}
    dominant_failure_category, dominant_failure_count = _dominant_bucket(failure_categories)
    dominant_setup_failure_reason = _dominant_reason(setup_failure_reasons)
    dominant_setup_failure_subreason = _dominant_subreason(setup_failure_subreasons)
    unknown_setup_failure_rate = _unknown_setup_failure_rate(setup_failure_reasons)
    improved_cases = _case_improvements(cases_summary)
    summary = {
        "required_variants": required_variants,
        "missing_variants": missing_variants,
        "eligible_result_counts": eligible_counts,
        "baseline_clean_pass_rate": rates.get("baseline_clean"),
        "skills_only_clean_pass_rate": rates.get("skills_only_clean"),
        "skills_with_hooks_clean_pass_rate": rates.get("skills_with_hooks_clean"),
        "skills_with_hooks_vs_baseline_pass_rate_delta": _numeric_delta(
            rates.get("skills_with_hooks_clean"),
            rates.get("baseline_clean"),
        ),
        "skills_with_hooks_vs_skills_only_pass_rate_delta": _numeric_delta(
            rates.get("skills_with_hooks_clean"),
            rates.get("skills_only_clean"),
        ),
        "dominant_failure_category": dominant_failure_category,
        "dominant_failure_count": dominant_failure_count,
        "dominant_setup_failure_reason": dominant_setup_failure_reason,
        "dominant_setup_failure_subreason": dominant_setup_failure_subreason,
        "setup_failure_subreasons": setup_failure_subreasons,
        "unknown_setup_failure_rate": unknown_setup_failure_rate,
        "setup_failed_result_count": int(failure_categories.get("setup_failed", 0) or 0),
        "setup_failed_by_variant": setup_counts,
        "setup_failed_rate_by_variant": setup_rates,
        "case_improvements": improved_cases,
        "reason": "",
    }

    if (
        benchmark_mode != "ablation"
        or evidence_scope_detail.get("evidence_scope_ready") is not True
        or missing_variants
        or any(count <= 0 for count in eligible_counts.values())
        or not all(isinstance(rates.get(variant), int | float) for variant in required_variants)
    ):
        summary["reason"] = "missing required ablation variants, repeated runs, or eligible assertion-backed results"
        return {"verdict": "inconclusive", "status": "inconclusive", "summary": summary}

    baseline_rate = float(rates["baseline_clean"])
    skills_only_rate = float(rates["skills_only_clean"])
    hooks_rate = float(rates["skills_with_hooks_clean"])
    setup_dominates = dominant_failure_category == "setup_failed" and dominant_failure_count > 0
    skills_do_not_reduce_setup = (
        isinstance(setup_rates["baseline_clean"], int | float)
        and isinstance(setup_rates["skills_only_clean"], int | float)
        and isinstance(setup_rates["skills_with_hooks_clean"], int | float)
        and setup_rates["skills_only_clean"] >= setup_rates["baseline_clean"]
        and setup_rates["skills_with_hooks_clean"] >= setup_rates["baseline_clean"]
    )

    if hooks_rate < baseline_rate:
        summary["reason"] = "skills_with_hooks_clean pass rate is below baseline_clean"
        return {"verdict": "negative", "status": "regression", "summary": summary}
    if setup_dominates and skills_do_not_reduce_setup:
        summary["reason"] = "setup_failed is dominant and skill variants do not reduce setup failures"
        return {"verdict": "negative", "status": "regression", "summary": summary}
    if dominant_setup_failure_reason == "unknown" and int(setup_failure_reasons.get("unknown", 0) or 0) > 0:
        summary["reason"] = "setup failure diagnostics remain dominated by unknown"
        return {"verdict": "mixed", "status": "mixed", "summary": summary}
    if hooks_rate > baseline_rate and hooks_rate >= skills_only_rate and not setup_dominates:
        summary["reason"] = "skills_with_hooks_clean improves over baseline_clean and is not below skills_only_clean"
        return {"verdict": "positive", "status": "improved", "summary": summary}
    if hooks_rate == baseline_rate:
        summary["reason"] = "skills_with_hooks_clean matches baseline_clean at summary precision"
        return {"verdict": "neutral", "status": "neutral", "summary": summary}
    if improved_cases or setup_dominates:
        summary["reason"] = "some case-level movement exists, but the aggregate effect is not clearly positive"
        return {"verdict": "mixed", "status": "mixed", "summary": summary}
    summary["reason"] = "aggregate effect is not clearly positive"
    return {"verdict": "mixed", "status": "mixed", "summary": summary}


def _dominant_bucket(counts: dict[str, int]) -> tuple[str | None, int]:
    if not counts:
        return None, 0
    category, count = max(counts.items(), key=lambda item: (item[1], item[0]))
    return category, int(count)


def _case_improvements(cases_summary: dict[str, Any]) -> list[str]:
    improved: list[str] = []
    for case_id, case_payload in cases_summary.items():
        if not isinstance(case_payload, dict):
            continue
        variants = case_payload.get("variants") or {}
        baseline_rate = (variants.get("baseline_clean") or {}).get("pass_rate")
        hooks_rate = (variants.get("skills_with_hooks_clean") or {}).get("pass_rate")
        if isinstance(baseline_rate, int | float) and isinstance(hooks_rate, int | float) and hooks_rate > baseline_rate:
            improved.append(str(case_id))
    return improved


def _case_result_summary(cases_summary: dict[str, Any]) -> dict[str, Any]:
    improved: list[dict[str, Any]] = []
    no_improvement: list[dict[str, Any]] = []
    regressed: list[dict[str, Any]] = []
    hooks_below_skills: list[dict[str, Any]] = []
    run_case_ids: set[str] = set()
    for case_id, case_payload in sorted(cases_summary.items()):
        if not isinstance(case_payload, dict):
            continue
        run_case_ids.add(str(case_id))
        variants = case_payload.get("variants") if isinstance(case_payload.get("variants"), dict) else {}
        baseline_rate = _case_variant_rate(variants, "baseline_clean")
        skills_rate = _case_variant_rate(variants, "skills_only_clean")
        hooks_rate = _case_variant_rate(variants, "skills_with_hooks_clean")
        if isinstance(baseline_rate, int | float) and isinstance(hooks_rate, int | float):
            delta = round(float(hooks_rate) - float(baseline_rate), 4)
            row = {
                "case_id": case_id,
                "baseline_clean_pass_rate": baseline_rate,
                "skills_only_clean_pass_rate": skills_rate,
                "skills_with_hooks_clean_pass_rate": hooks_rate,
                "skills_with_hooks_vs_baseline_delta": delta,
            }
            if delta > 0:
                improved.append(row)
            elif delta < 0:
                regressed.append(row)
            else:
                no_improvement.append(row)
        if (
            isinstance(skills_rate, int | float)
            and isinstance(hooks_rate, int | float)
            and float(hooks_rate) < float(skills_rate)
        ):
            hooks_below_skills.append(
                {
                    "case_id": case_id,
                    "skills_only_clean_pass_rate": skills_rate,
                    "skills_with_hooks_clean_pass_rate": hooks_rate,
                    "delta": round(float(hooks_rate) - float(skills_rate), 4),
                }
            )
    reliability_no_improvement = [
        row for row in no_improvement if str(row.get("case_id", "")).startswith("reliability/")
    ]
    known_unresolved_reliability = [
        dict(row)
        for row in KNOWN_UNRESOLVED_RELIABILITY_CASES
        if str(row.get("case_id", "")) not in run_case_ids
    ]
    return {
        "improved_cases": improved,
        "no_improvement_cases": no_improvement,
        "regressed_cases": regressed,
        "skills_with_hooks_below_skills_only_cases": hooks_below_skills,
        "reliability_no_improvement_cases": reliability_no_improvement,
        "known_unresolved_reliability_cases": known_unresolved_reliability,
        "improved_case_count": len(improved),
        "no_improvement_case_count": len(no_improvement),
        "regressed_case_count": len(regressed),
        "reliability_no_improvement_visible": bool(reliability_no_improvement or known_unresolved_reliability),
    }


def _quality_improvement_summary(
    variants: dict[str, dict[str, Any]],
    cases_summary: dict[str, Any],
    case_result_summary: dict[str, Any],
    capability_coverage_summary: dict[str, Any],
    capability_artifact_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    baseline_rate = _summary_variant_rate(variants, "baseline_clean")
    skills_rate = _summary_variant_rate(variants, "skills_only_clean")
    hooks_rate = _summary_variant_rate(variants, "skills_with_hooks_clean")
    hooks_vs_baseline = _numeric_delta(hooks_rate, baseline_rate)
    skills_vs_baseline = _numeric_delta(skills_rate, baseline_rate)
    hooks_vs_skills = _numeric_delta(hooks_rate, skills_rate)
    no_aggregate_regression = (
        isinstance(hooks_rate, int | float)
        and isinstance(skills_rate, int | float)
        and float(hooks_rate) >= float(skills_rate)
    )
    no_case_regression = not case_result_summary.get("skills_with_hooks_below_skills_only_cases")
    no_quality_regression = bool(no_aggregate_regression and no_case_regression)
    pass_ids = set(capability_coverage_summary.get("assertion_backed_covered_capabilities") or [])
    required_ready_missing = sorted(CAPABILITY_QUALITY_READY_REQUIRED_IDS - pass_ids)
    capability_quality_ready = not required_ready_missing
    assertion_backed_coverage_count = int(
        capability_coverage_summary.get("assertion_backed_coverage_count", 0) or 0
    )
    artifact_evidence = capability_artifact_evidence if isinstance(capability_artifact_evidence, dict) else {}
    baseline_artifacts = _variant_artifact_totals(artifact_evidence, "baseline_clean")
    skills_artifacts = _variant_artifact_totals(artifact_evidence, "skills_only_clean")
    hooks_artifacts = _variant_artifact_totals(artifact_evidence, "skills_with_hooks_clean")
    baseline_route_rate = _rate(baseline_artifacts["route"], baseline_artifacts["runs"])
    skills_route_rate = _rate(skills_artifacts["route"], skills_artifacts["runs"])
    skills_strict_rate = _rate(skills_artifacts["strict"], skills_artifacts["runs"])
    skills_artifact_rate = _rate(skills_artifacts["artifact"], skills_artifacts["runs"])
    hooks_route_rate = _rate(hooks_artifacts["route"], hooks_artifacts["runs"])
    hooks_strict_rate = _rate(hooks_artifacts["strict"], hooks_artifacts["runs"])
    hooks_hook_rate = _rate(hooks_artifacts["hook"], hooks_artifacts["runs"])
    pass_rate_saturated = (
        isinstance(baseline_rate, int | float)
        and isinstance(skills_rate, int | float)
        and float(baseline_rate) >= 1.0
        and float(skills_rate) >= float(baseline_rate)
    )
    skill_capability_evidence_improved = bool(
        pass_rate_saturated
        and capability_quality_ready
        and no_quality_regression
        and isinstance(skills_route_rate, int | float)
        and isinstance(baseline_route_rate, int | float)
        and isinstance(skills_strict_rate, int | float)
        and isinstance(skills_artifact_rate, int | float)
        and skills_route_rate > baseline_route_rate
        and skills_strict_rate >= 1.0
        and skills_artifact_rate >= 1.0
    )
    hook_capability_evidence_non_regressing = bool(
        no_quality_regression
        and isinstance(hooks_route_rate, int | float)
        and isinstance(skills_route_rate, int | float)
        and isinstance(hooks_strict_rate, int | float)
        and isinstance(skills_strict_rate, int | float)
        and isinstance(hooks_hook_rate, int | float)
        and hooks_route_rate >= skills_route_rate
        and hooks_strict_rate >= skills_strict_rate
        and hooks_hook_rate >= 1.0
    )
    baseline_quality_improved = isinstance(hooks_vs_baseline, int | float) and hooks_vs_baseline >= 0.20
    skill_pass_rate_improved = isinstance(skills_vs_baseline, int | float) and skills_vs_baseline >= 0.15
    skill_quality_improved = bool(skill_pass_rate_improved or skill_capability_evidence_improved)
    hook_quality_increment_positive = isinstance(hooks_vs_skills, int | float) and hooks_vs_skills >= 0.05
    large_quality_improvement_claim = bool(
        baseline_quality_improved
        and skill_quality_improved
        and hook_quality_increment_positive
        and no_quality_regression
        and assertion_backed_coverage_count >= LARGE_QUALITY_IMPROVEMENT_MIN_CAPABILITY_COUNT
    )
    return {
        "baseline_clean_pass_rate": baseline_rate,
        "skills_only_clean_pass_rate": skills_rate,
        "skills_with_hooks_clean_pass_rate": hooks_rate,
        "skills_only_vs_baseline_delta": skills_vs_baseline,
        "skills_with_hooks_vs_skills_only_delta": hooks_vs_skills,
        "skills_with_hooks_vs_baseline_delta": hooks_vs_baseline,
        "baseline_quality_improved": baseline_quality_improved,
        "skill_quality_improved": skill_quality_improved,
        "skill_pass_rate_improved": skill_pass_rate_improved,
        "skill_capability_evidence_improved": skill_capability_evidence_improved,
        "hook_capability_evidence_non_regressing": hook_capability_evidence_non_regressing,
        "baseline_route_process_evidence_rate": baseline_route_rate,
        "skills_only_route_process_evidence_rate": skills_route_rate,
        "skills_only_strict_process_trace_rate": skills_strict_rate,
        "skills_with_hooks_route_process_evidence_rate": hooks_route_rate,
        "skills_with_hooks_strict_process_trace_rate": hooks_strict_rate,
        "skills_with_hooks_hook_bounded_evidence_rate": hooks_hook_rate,
        "hook_quality_increment_positive": hook_quality_increment_positive,
        "no_quality_regression": no_quality_regression,
        "capability_quality_ready": capability_quality_ready,
        "capability_quality_ready_missing": required_ready_missing,
        "assertion_backed_core_capability_count": assertion_backed_coverage_count,
        "large_quality_improvement_claim": large_quality_improvement_claim,
        "cost_is_quality_gate": False,
        "cost_telemetry_only": True,
        "efficiency_improvement_claim": False,
        "case_regression_count": len(case_result_summary.get("regressed_cases") or []),
        "skills_with_hooks_below_skills_only_case_count": len(
            case_result_summary.get("skills_with_hooks_below_skills_only_cases") or []
        ),
        "case_count": len(cases_summary),
    }


def _variant_artifact_totals(evidence: dict[str, Any], variant: str) -> dict[str, int]:
    totals = {"runs": 0, "route": 0, "strict": 0, "hook": 0, "artifact": 0}
    for case_payload in evidence.values():
        if not isinstance(case_payload, dict):
            continue
        payload = case_payload.get(variant)
        if not isinstance(payload, dict):
            continue
        totals["runs"] += int(payload.get("runs", 0) or 0)
        totals["route"] += int(payload.get("route_process_evidence_count", 0) or 0)
        totals["strict"] += int(payload.get("strict_process_trace_valid_count", 0) or 0)
        totals["hook"] += int(payload.get("hook_bounded_evidence_count", 0) or 0)
        totals["artifact"] += int(payload.get("artifact_backed_run_count", 0) or 0)
    return totals


def _case_variant_rate(variants: dict[str, Any], variant: str) -> Any:
    payload = variants.get(variant) if isinstance(variants, dict) else None
    return payload.get("pass_rate") if isinstance(payload, dict) else "not_collected"


def _summary_variant_rate(variants: dict[str, dict[str, Any]], variant: str) -> Any:
    payload = variants.get(variant) if isinstance(variants, dict) else None
    return payload.get("pass_rate") if isinstance(payload, dict) else "not_collected"


def _variant_deltas(variants: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    deltas: dict[str, dict[str, Any]] = {}
    pairs = (
        ("skills_only_clean", "baseline_clean"),
        ("skills_with_hooks_clean", "skills_only_clean"),
        ("skills_with_hooks_clean", "baseline_clean"),
    )
    for variant, baseline in pairs:
        if variant in variants and baseline in variants:
            deltas[f"{variant}_vs_{baseline}"] = _delta_from_baseline(variants[baseline], variants[variant])
    for variant, summary in variants.items():
        if variant == "baseline_clean" or f"{variant}_vs_baseline_clean" in deltas:
            continue
        baseline = variants.get("baseline_clean")
        if baseline:
            deltas[f"{variant}_vs_baseline_clean"] = _delta_from_baseline(baseline, summary)
    return deltas


def _delta_from_baseline(baseline: dict[str, Any], variant: dict[str, Any]) -> dict[str, Any]:
    base_usage = baseline["average_usage"]
    variant_usage = variant["average_usage"]
    base_metrics = baseline["average_metrics"]
    variant_metrics = variant["average_metrics"]
    return {
        "pass_rate_delta": _numeric_delta(variant["pass_rate"], baseline["pass_rate"]),
        "security_pass_rate_delta": _numeric_delta(variant["security_pass_rate"], baseline["security_pass_rate"]),
        "input_tokens_delta_pct": _pct_delta(variant_usage["input_tokens"], base_usage["input_tokens"]),
        "output_tokens_delta_pct": _pct_delta(variant_usage["output_tokens"], base_usage["output_tokens"]),
        "reasoning_output_tokens_delta_pct": _pct_delta(
            variant_usage["reasoning_output_tokens"],
            base_usage["reasoning_output_tokens"],
        ),
        "command_execution_count_delta": round(
            variant_metrics["command_execution_count"] - base_metrics["command_execution_count"], 2
        ),
        "file_change_count_delta": round(variant_metrics["file_change_count"] - base_metrics["file_change_count"], 2),
    }


def _numeric_delta(value: Any, baseline: Any) -> float | str:
    if not isinstance(value, int | float) or not isinstance(baseline, int | float):
        return "not_collected"
    return round(float(value) - float(baseline), 4)


def _pct_delta(value: float, baseline: float) -> float | None:
    if baseline == 0:
        return None
    return round((value - baseline) / baseline, 4)


def _cases_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for case_id in sorted({str(result.get("case_id")) for result in results if result.get("case_id")}):
        case_results = [result for result in results if result.get("case_id") == case_id]
        variants: dict[str, Any] = {}
        for variant in sorted({str(result.get("variant")) for result in case_results if result.get("variant")}):
            variant_results = _results_for_variant(case_results, variant)
            eligible = [result for result in variant_results if result.get("benchmark_eligible") is True]
            passed = [result for result in eligible if result.get("benchmark_passed") is True]
            setup_failure_reasons = _reason_counts(
                variant_results,
                "setup_failure_reason",
                "setup_failed",
            )
            setup_failure_subreasons = _setup_subreason_counts(variant_results)
            variants[variant] = {
                "runs": len(variant_results),
                "benchmark_eligible_result_count": len(eligible),
                "benchmark_passed_result_count": len(passed),
                "pass_rate": _rate(len(passed), len(eligible)),
                "failure_categories": _counts(variant_results, "failure_category"),
                "setup_failure_reasons": setup_failure_reasons,
                "dominant_setup_failure_reason": _dominant_reason(setup_failure_reasons),
                "setup_failure_subreasons": setup_failure_subreasons,
                "dominant_setup_failure_subreason": _dominant_subreason(setup_failure_subreasons),
                "unknown_setup_failure_rate": _unknown_setup_failure_rate(setup_failure_reasons),
                "test_suite_failure_reasons": _reason_counts(
                    variant_results,
                    "test_suite_failure_reason",
                    "test_suite_failed",
                ),
                "security_failure_reasons": _reason_counts(
                    variant_results,
                    "security_failure_reason",
                    "security_checks_failed",
                ),
            }
        grading_modes = {str(result.get("grading_mode")) for result in case_results if result.get("grading_mode")}
        case_setup_failure_reasons = _reason_counts(case_results, "setup_failure_reason", "setup_failed")
        case_setup_failure_subreasons = _setup_subreason_counts(case_results)
        summary[case_id] = {
            "grading_mode": next(iter(grading_modes)) if len(grading_modes) == 1 else "mixed",
            "setup_failure_reasons": case_setup_failure_reasons,
            "dominant_setup_failure_reason": _dominant_reason(case_setup_failure_reasons),
            "setup_failure_subreasons": case_setup_failure_subreasons,
            "dominant_setup_failure_subreason": _dominant_subreason(case_setup_failure_subreasons),
            "unknown_setup_failure_rate": _unknown_setup_failure_rate(case_setup_failure_reasons),
            "variants": variants,
        }
    return summary


def _capability_artifact_evidence(results: list[dict[str, Any]]) -> dict[str, Any]:
    evidence: dict[str, Any] = {}
    for result in results:
        case_id = str(result.get("case_id") or "")
        variant = str(result.get("variant") or "")
        result_dir = result.get("_result_dir")
        if not case_id or not variant or not isinstance(result_dir, Path):
            continue
        run_evidence = _run_artifact_evidence(result, result_dir)
        variant_bucket = evidence.setdefault(case_id, {}).setdefault(
            variant,
            {
                "runs": 0,
                "artifact_backed_run_count": 0,
                "route_process_evidence_count": 0,
                "strict_process_trace_valid_count": 0,
                "strict_process_trace_error_count": 0,
                "strict_process_trace_error_examples": [],
                "hook_bounded_evidence_count": 0,
                "self_report_only_count": 0,
                "privacy_redaction_status": "pass",
                "missing_required_artifacts": {},
                "compact": {
                    "pre_compact_snapshot_count": 0,
                    "post_compact_reinject_count": 0,
                    "session_compact_reinject_count": 0,
                    "compact_runtime_evidence_count": 0,
                    "compact_after_repair_continuation_count": 0,
                    "restored_required_context_fields": [],
                    "missing_required_context_fields": [],
                    "redacted_required_context_fields": [],
                    "context_unusable_fields": [],
                    "privacy_redaction_status": "not_collected",
                    "context_usable_status": "not_collected",
                    "context_retention_status": "not_collected",
                    "compact_after_repair_continuation_status": "not_collected",
                    "candidate_context_status": "not_collected",
                    "candidate_context_present_count": 0,
                },
            },
        )
        variant_bucket["runs"] += 1
        if run_evidence["artifact_backed"]:
            variant_bucket["artifact_backed_run_count"] += 1
        if run_evidence["route_process_evidence"]:
            variant_bucket["route_process_evidence_count"] += 1
        if run_evidence["strict_process_trace_valid"]:
            variant_bucket["strict_process_trace_valid_count"] += 1
        else:
            variant_bucket["strict_process_trace_error_count"] += 1
            examples = variant_bucket["strict_process_trace_error_examples"]
            for error in run_evidence.get("strict_process_trace_errors", []):
                if len(examples) >= 5:
                    break
                examples.append(str(error)[:240])
        if run_evidence["hook_bounded_evidence"]:
            variant_bucket["hook_bounded_evidence_count"] += 1
        if run_evidence["self_report_only"]:
            variant_bucket["self_report_only_count"] += 1
        if run_evidence["privacy_redaction_status"] == "fail":
            variant_bucket["privacy_redaction_status"] = "fail"
        for artifact in run_evidence["missing_required_artifacts"]:
            missing = variant_bucket["missing_required_artifacts"]
            missing[artifact] = int(missing.get(artifact, 0) or 0) + 1
        _merge_compact_evidence(variant_bucket["compact"], run_evidence.get("compact", {}))
    return evidence


def _run_artifact_evidence(result: dict[str, Any], result_dir: Path) -> dict[str, Any]:
    missing = [relative for relative in REQUIRED_CAPABILITY_ARTIFACTS if not (result_dir / relative).is_file()]
    process_trace = read_json(result_dir / "process-trace.json")
    process_trace = process_trace if isinstance(process_trace, dict) else {}
    route_process = _route_process_evidence(process_trace)
    strict_trace_errors = _strict_process_trace_errors(result_dir, process_trace)
    privacy_status = "fail" if _privacy_findings(result_dir) else "pass"
    candidate_evidence = (result_dir / "candidate-artifacts" / "CAPABILITY_EVIDENCE.md").is_file()
    compact = _compact_run_evidence(result_dir, process_trace)
    return {
        "artifact_backed": not missing,
        "missing_required_artifacts": missing,
        "route_process_evidence": route_process,
        "strict_process_trace_valid": bool(process_trace and not strict_trace_errors),
        "strict_process_trace_errors": strict_trace_errors[:5],
        "hook_bounded_evidence": bool(
            result.get("changeforge_hooks_enabled") is True
            and not missing
            and privacy_status == "pass"
            and (result_dir / "events.redacted.jsonl").is_file()
        ),
        "self_report_only": bool(candidate_evidence and missing),
        "privacy_redaction_status": privacy_status,
        "compact": compact,
    }


def _route_process_evidence(process_trace: dict[str, Any]) -> bool:
    if not process_trace:
        return False
    evidence_sources = [str(source) for source in process_trace.get("evidence_sources", []) if str(source).strip()]
    explicit_source = any(source != PROCESS_FALLBACK_FIELD_SOURCE for source in evidence_sources)
    phases = process_trace.get("phase_status") if isinstance(process_trace.get("phase_status"), dict) else {}
    core_present = any(phases.get(phase) in {"present", "degraded"} for phase in PROCESS_CORE_PHASES)
    route_manifest = process_trace.get("route_manifest_present") is True
    selected = bool(process_trace.get("selected_skills") and process_trace.get("selected_capabilities"))
    return bool((route_manifest or selected) and core_present and explicit_source)


def _strict_process_trace_errors(result_dir: Path, process_trace: dict[str, Any]) -> list[str]:
    if not process_trace:
        return ["process-trace.json missing or invalid"]
    validator = _load_process_trace_validator()
    if validator is None:
        return ["process trace validator unavailable"]
    try:
        run_dir = result_dir.parents[3]
    except IndexError:
        run_dir = result_dir
    trace_path = result_dir / "process-trace.json"
    return [
        str(error)
        for error in validator._trace_errors(trace_path, run_dir, process_trace, require_present=True)
    ]


def _load_process_trace_validator() -> Any:
    global _PROCESS_TRACE_VALIDATOR
    if _PROCESS_TRACE_VALIDATOR is not None:
        return _PROCESS_TRACE_VALIDATOR
    path = ROOT / "scripts" / "validate-process-traces.py"
    spec = importlib.util.spec_from_file_location("changeforge_process_trace_validator", path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _PROCESS_TRACE_VALIDATOR = module
    return module


def _privacy_findings(result_dir: Path) -> list[str]:
    findings: list[str] = []
    for relative in REQUIRED_CAPABILITY_ARTIFACTS:
        path = result_dir / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in CAPABILITY_PRIVACY_PATTERNS:
            if pattern.search(text):
                findings.append(relative)
                break
    for path in sorted((result_dir / "candidate-artifacts").glob("*")):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern in CAPABILITY_PRIVACY_PATTERNS:
                if pattern.search(text):
                    findings.append(f"candidate-artifacts/{path.name}")
                    break
    return findings


def _compact_run_evidence(result_dir: Path, process_trace: dict[str, Any]) -> dict[str, Any]:
    result_payload = read_json(result_dir / "result.json")
    result_payload = result_payload if isinstance(result_payload, dict) else {}
    context = (
        result_payload.get("compact_runtime_evidence")
        if isinstance(result_payload.get("compact_runtime_evidence"), dict)
        else {}
    )
    trace_runtime = (
        process_trace.get("compact_runtime_evidence")
        if isinstance(process_trace.get("compact_runtime_evidence"), dict)
        else {}
    )
    if trace_runtime:
        context = {**context, **trace_runtime}
    artifact_context = read_json(result_dir / "candidate-artifacts" / "COMPACTION_CONTEXT.json")
    candidate_context = artifact_context if isinstance(artifact_context, dict) else {}
    candidate_missing = [field for field in COMPACTION_REQUIRED_FIELDS if not candidate_context.get(field)]
    candidate_context_status = (
        "pass"
        if candidate_context
        and not candidate_missing
        and _compact_status_allows_pass(candidate_context.get("context_retention_status"), default=True)
        and _compact_status_allows_pass(candidate_context.get("privacy_redaction_status"), default=True)
        and _compact_status_allows_pass(candidate_context.get("context_usable_status"), default=True)
        else ("fail" if candidate_context else "not_collected")
    )
    if isinstance(context.get("missing_required_context_fields"), list):
        missing = [str(field) for field in context["missing_required_context_fields"]]
    else:
        missing = list(COMPACTION_REQUIRED_FIELDS)
    restored = (
        [str(field) for field in context.get("restored_required_context_fields", [])]
        if isinstance(context.get("restored_required_context_fields"), list)
        else [field for field in COMPACTION_REQUIRED_FIELDS if field not in missing]
    )
    runtime_artifact_present = (result_dir / "compaction" / "reinject-output.json").is_file()
    return {
        "compact_runtime_evidence_present": bool(context and runtime_artifact_present),
        "candidate_context_present": bool(candidate_context),
        "candidate_context_status": candidate_context_status,
        "pre_compact_snapshot_written": context.get("pre_compact_snapshot_written") is True,
        "post_compact_reinject_emitted": context.get("post_compact_reinject_emitted") is True,
        "session_compact_reinject_emitted": context.get("session_compact_reinject_emitted") is True,
        "compact_after_repair_continuation": str(context.get("compact_after_repair_continuation_status") or "") == "pass",
        "restored_required_context_fields": restored,
        "missing_required_context_fields": missing,
        "redacted_required_context_fields": list(context.get("redacted_required_context_fields") or []),
        "context_unusable_fields": list(context.get("context_unusable_fields") or []),
        "privacy_redaction_status": str(context.get("privacy_redaction_status") or "not_collected"),
        "context_usable_status": str(context.get("context_usable_status") or "not_collected"),
        "context_retention_status": str(context.get("context_retention_status") or "not_collected"),
        "compact_after_repair_continuation_status": str(
            context.get("compact_after_repair_continuation_status") or "not_collected"
        ),
    }


def _merge_compact_evidence(target: dict[str, Any], compact: dict[str, Any]) -> None:
    if compact.get("pre_compact_snapshot_written"):
        target["pre_compact_snapshot_count"] += 1
    if compact.get("post_compact_reinject_emitted"):
        target["post_compact_reinject_count"] += 1
    if compact.get("session_compact_reinject_emitted"):
        target["session_compact_reinject_count"] += 1
    if compact.get("compact_runtime_evidence_present"):
        target["compact_runtime_evidence_count"] += 1
    if compact.get("candidate_context_present"):
        target["candidate_context_present_count"] += 1
    if compact.get("compact_after_repair_continuation"):
        target["compact_after_repair_continuation_count"] += 1
    target["restored_required_context_fields"] = sorted(
        set(target.get("restored_required_context_fields", [])) | set(compact.get("restored_required_context_fields", []))
    )
    target["missing_required_context_fields"] = sorted(
        set(target.get("missing_required_context_fields", [])) | set(compact.get("missing_required_context_fields", []))
    )
    target["redacted_required_context_fields"] = sorted(
        set(target.get("redacted_required_context_fields", [])) | set(compact.get("redacted_required_context_fields", []))
    )
    target["context_unusable_fields"] = sorted(
        set(target.get("context_unusable_fields", [])) | set(compact.get("context_unusable_fields", []))
    )
    for field in (
        "privacy_redaction_status",
        "context_usable_status",
        "context_retention_status",
        "compact_after_repair_continuation_status",
        "candidate_context_status",
    ):
        value = str(compact.get(field) or "not_collected")
        if value == "fail" or target.get(field) in {"not_collected", "partial"}:
            target[field] = value


def _compact_context_summary(evidence: dict[str, Any]) -> dict[str, Any]:
    case = evidence.get("compact/context-retention-after-compaction")
    if not isinstance(case, dict):
        return {
            "case_id": "compact/context-retention-after-compaction",
            "run_status": "not_run",
            "pre_compact_snapshot_count": 0,
            "post_compact_reinject_count": 0,
            "session_compact_reinject_count": 0,
            "compact_runtime_evidence_count": 0,
            "restored_required_context_fields": [],
            "missing_required_context_fields": list(COMPACTION_REQUIRED_FIELDS),
            "redacted_required_context_fields": [],
            "context_unusable_fields": [],
            "privacy_redaction_status": "not_collected",
            "context_usable_status": "not_collected",
            "context_retention_status": "not_collected",
            "compact_after_repair_continuation_status": "not_collected",
            "candidate_context_status": "not_collected",
        }
    combined = {
        "case_id": "compact/context-retention-after-compaction",
        "run_status": "run",
        "pre_compact_snapshot_count": 0,
        "post_compact_reinject_count": 0,
        "session_compact_reinject_count": 0,
        "compact_runtime_evidence_count": 0,
        "compact_after_repair_continuation_count": 0,
        "restored_required_context_fields": [],
        "missing_required_context_fields": [],
        "redacted_required_context_fields": [],
        "context_unusable_fields": [],
        "privacy_redaction_status": "pass",
        "context_usable_status": "pass",
        "context_retention_status": "pass",
        "compact_after_repair_continuation_status": "pass",
        "candidate_context_status": "pass",
    }
    variant_payloads = (
        [case["skills_with_hooks_clean"]]
        if isinstance(case.get("skills_with_hooks_clean"), dict)
        else [payload for payload in case.values() if isinstance(payload, dict)]
    )
    for variant_payload in variant_payloads:
        if not isinstance(variant_payload, dict):
            continue
        compact = variant_payload.get("compact") if isinstance(variant_payload.get("compact"), dict) else {}
        combined["pre_compact_snapshot_count"] += int(compact.get("pre_compact_snapshot_count", 0) or 0)
        combined["post_compact_reinject_count"] += int(compact.get("post_compact_reinject_count", 0) or 0)
        combined["session_compact_reinject_count"] += int(compact.get("session_compact_reinject_count", 0) or 0)
        combined["compact_runtime_evidence_count"] += int(compact.get("compact_runtime_evidence_count", 0) or 0)
        combined["compact_after_repair_continuation_count"] += int(
            compact.get("compact_after_repair_continuation_count", 0) or 0
        )
        combined["restored_required_context_fields"] = sorted(
            set(combined["restored_required_context_fields"]) | set(compact.get("restored_required_context_fields", []))
        )
        combined["missing_required_context_fields"] = sorted(
            set(combined["missing_required_context_fields"]) | set(compact.get("missing_required_context_fields", []))
        )
        combined["redacted_required_context_fields"] = sorted(
            set(combined["redacted_required_context_fields"]) | set(compact.get("redacted_required_context_fields", []))
        )
        combined["context_unusable_fields"] = sorted(
            set(combined["context_unusable_fields"]) | set(compact.get("context_unusable_fields", []))
        )
        for field in (
            "privacy_redaction_status",
            "context_usable_status",
            "context_retention_status",
            "compact_after_repair_continuation_status",
            "candidate_context_status",
        ):
            value = str(compact.get(field) or "not_collected")
            if value in {"fail", "partial", "not_collected"}:
                combined[field] = value
    return combined


def _compact_status_allows_pass(value: Any, *, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, dict):
        for key in ("status", "result", "value"):
            if key in value:
                return _compact_status_allows_pass(value.get(key), default=default)
        text = json.dumps(value, sort_keys=True)
    else:
        text = str(value)
    normalized = text.strip().casefold()
    if not normalized:
        return default
    failure_markers = ("fail", "partial", "not_collected", "not collected", "missing", "stale", "unusable", "leak")
    return not any(marker in normalized for marker in failure_markers)


def _coverage_summary(
    cases: list[str],
    cases_summary: dict[str, Any],
    case_metadata: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    actual_case_ids = sorted(dict.fromkeys(cases))
    registered_live_case_ids = sorted(
        case_id for case_id, metadata in case_metadata.items() if metadata.get("enabled") is not False
    )
    registered_publishable_assertion_case_ids = [
        case_id
        for case_id in registered_live_case_ids
        if case_metadata.get(case_id, {}).get("grading_mode") == "assertion"
        and case_metadata.get(case_id, {}).get("publishable_for_strict") is True
    ]
    manifest_case_count = sum(len(case_names) for case_names in EXPECTED_BENCHMARKS.values())
    manifest_categories = sorted(EXPECTED_BENCHMARKS)
    actual_counts = _coverage_case_counts(actual_case_ids, cases_summary, case_metadata)
    registered_counts = _coverage_case_counts(registered_live_case_ids, {}, case_metadata)
    registered_publishable_categories = _category_counts(registered_publishable_assertion_case_ids)
    actual_categories = actual_counts["categories"]
    return {
        "case_count": len(actual_case_ids),
        "assertion_case_count": actual_counts["assertion_case_count"],
        "telemetry_only_case_count": actual_counts["telemetry_only_case_count"],
        "publishable_assertion_case_count": actual_counts["publishable_assertion_case_count"],
        "tiers": actual_counts["tiers"],
        "categories": actual_categories,
        "coverage_dimensions": actual_counts["coverage_dimensions"],
        "unregistered_case_count": actual_counts["unregistered_case_count"],
        "manifest_category_count": len(manifest_categories),
        "manifest_case_count": manifest_case_count,
        "manifest_categories": manifest_categories,
        "registered_live_case_count": len(registered_live_case_ids),
        "registered_assertion_case_count": registered_counts["assertion_case_count"],
        "registered_telemetry_only_case_count": registered_counts["telemetry_only_case_count"],
        "registered_publishable_assertion_case_count": len(registered_publishable_assertion_case_ids),
        "registered_category_count": len(registered_publishable_categories),
        "registered_case_coverage_rate": _coverage_rate(len(registered_live_case_ids), manifest_case_count),
        "registered_publishable_case_coverage_rate": _coverage_rate(
            len(registered_publishable_assertion_case_ids),
            manifest_case_count,
        ),
        "tiers_registered": registered_counts["tiers"],
        "categories_registered": registered_counts["categories"],
        "publishable_categories_registered": registered_publishable_categories,
        "coverage_dimensions_registered": registered_counts["coverage_dimensions"],
        "actual_run_case_count": len(actual_case_ids),
        "actual_run_assertion_case_count": actual_counts["assertion_case_count"],
        "actual_run_publishable_assertion_case_count": actual_counts["publishable_assertion_case_count"],
        "actual_run_category_count": len(actual_categories),
        "actual_run_case_coverage_rate": _coverage_rate(len(actual_case_ids), manifest_case_count),
        "tiers_run": actual_counts["tiers"],
        "categories_run": actual_categories,
        "coverage_dimensions_run": actual_counts["coverage_dimensions"],
        "registered_but_not_run_cases": sorted(set(registered_publishable_assertion_case_ids) - set(actual_case_ids)),
        "missing_manifest_categories": sorted(set(manifest_categories) - set(registered_publishable_categories)),
    }


def _coverage_case_counts(
    case_ids: list[str],
    cases_summary: dict[str, Any],
    case_metadata: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    tiers: dict[str, int] = {tier: 0 for tier in CASE_TIERS}
    dimensions: dict[str, int] = {}
    categories = _category_counts(case_ids)
    assertion_case_count = 0
    telemetry_only_case_count = 0
    publishable_assertion_case_count = 0
    for case_id in case_ids:
        metadata = case_metadata.get(case_id, {})
        tier = str(metadata.get("tier") or "unregistered")
        tiers[tier] = tiers.get(tier, 0) + 1
        category = _case_category(case_id)
        for dimension in metadata.get("coverage_dimensions") or [category]:
            dimension_text = str(dimension)
            dimensions[dimension_text] = dimensions.get(dimension_text, 0) + 1
        grading_mode = _coverage_grading_mode(case_id, cases_summary, metadata)
        if grading_mode == "assertion":
            assertion_case_count += 1
            if metadata.get("publishable_for_strict") is True:
                publishable_assertion_case_count += 1
        elif grading_mode == "telemetry_only":
            telemetry_only_case_count += 1
    return {
        "assertion_case_count": assertion_case_count,
        "telemetry_only_case_count": telemetry_only_case_count,
        "publishable_assertion_case_count": publishable_assertion_case_count,
        "tiers": {key: value for key, value in sorted(tiers.items()) if value > 0 or key in CASE_TIERS},
        "categories": categories,
        "coverage_dimensions": dict(sorted(dimensions.items())),
        "unregistered_case_count": sum(1 for case_id in case_ids if case_id not in case_metadata),
    }


def _coverage_grading_mode(case_id: str, cases_summary: dict[str, Any], metadata: dict[str, Any]) -> str:
    case_payload = cases_summary.get(case_id)
    if isinstance(case_payload, dict) and case_payload.get("grading_mode"):
        return str(case_payload["grading_mode"])
    return str(metadata.get("grading_mode") or "unregistered")


def _category_counts(case_ids: list[str]) -> dict[str, int]:
    categories: dict[str, int] = {}
    for case_id in case_ids:
        category = _case_category(case_id)
        categories[category] = categories.get(category, 0) + 1
    return dict(sorted(categories.items()))


def _case_category(case_id: str) -> str:
    return case_id.split("/", 1)[0] if "/" in case_id else "unknown"


def _coverage_rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def _cost_summary(results: list[dict[str, Any]], variants: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "result_count": len(results),
        "total_usage": _total_usage(results),
        "average_usage_per_result": _average_usage(results),
        "by_variant": {
            variant: {
                "result_count": int(variant_summary.get("result_count", 0) or 0),
                "total_usage": _total_usage(_results_for_variant(results, variant)),
                "average_usage_per_result": variant_summary.get("average_usage", {}),
                "median_usage_per_result": variant_summary.get("median_usage", {}),
                "pass_rate_per_100k_input_tokens": _pass_rate_per_usage_unit(
                    variant_summary,
                    "input_tokens",
                    100000,
                ),
                "pass_rate_per_100_commands": _pass_rate_per_metric_unit(
                    variant_summary,
                    "command_execution_count",
                    100,
                ),
            }
            for variant, variant_summary in variants.items()
        },
        "cost_adjusted_delta": {
            "skills_only_clean_vs_baseline_clean": _cost_adjusted_delta(
                variants,
                "skills_only_clean",
                "baseline_clean",
            ),
            "skills_with_hooks_clean_vs_baseline_clean": _cost_adjusted_delta(
                variants,
                "skills_with_hooks_clean",
                "baseline_clean",
            ),
            "skills_with_hooks_clean_vs_skills_only_clean": _cost_adjusted_delta(
                variants,
                "skills_with_hooks_clean",
                "skills_only_clean",
            ),
        },
        "case_cost_outliers": _case_cost_outliers(results),
        "cost_is_telemetry_only": True,
        "quality_gate_uses_cost": False,
        "telemetry_only_note": (
            "Cost is telemetry only in this quality-first phase; token, command, and file-change overhead "
            "do not gate pass-rate or capability quality conclusions, and no efficiency improvement claim is made."
        ),
        "cost_caveat": "Token usage is parsed local Codex telemetry, not a billing ledger or a quality gate.",
    }


def _pass_rate_per_usage_unit(variant_summary: dict[str, Any], usage_key: str, unit: int) -> float | str:
    pass_rate = variant_summary.get("pass_rate")
    average_usage = variant_summary.get("average_usage")
    if not isinstance(pass_rate, int | float) or not isinstance(average_usage, dict):
        return "not_collected"
    average_value = average_usage.get(usage_key)
    if not isinstance(average_value, int | float) or average_value <= 0:
        return "not_collected"
    return round(float(pass_rate) * unit / float(average_value), 4)


def _pass_rate_per_metric_unit(variant_summary: dict[str, Any], metric_key: str, unit: int) -> float | str:
    pass_rate = variant_summary.get("pass_rate")
    average_metrics = variant_summary.get("average_metrics")
    if not isinstance(pass_rate, int | float) or not isinstance(average_metrics, dict):
        return "not_collected"
    average_value = average_metrics.get(metric_key)
    if not isinstance(average_value, int | float) or average_value <= 0:
        return "not_collected"
    return round(float(pass_rate) * unit / float(average_value), 4)


def _cost_adjusted_delta(
    variants: dict[str, dict[str, Any]],
    variant: str,
    baseline: str,
) -> dict[str, Any]:
    variant_summary = variants.get(variant)
    baseline_summary = variants.get(baseline)
    if not isinstance(variant_summary, dict) or not isinstance(baseline_summary, dict):
        return {"status": "not_collected"}
    pass_rate_delta = _numeric_delta(variant_summary.get("pass_rate"), baseline_summary.get("pass_rate"))
    variant_usage = variant_summary.get("average_usage") if isinstance(variant_summary.get("average_usage"), dict) else {}
    baseline_usage = baseline_summary.get("average_usage") if isinstance(baseline_summary.get("average_usage"), dict) else {}
    variant_metrics = (
        variant_summary.get("average_metrics") if isinstance(variant_summary.get("average_metrics"), dict) else {}
    )
    baseline_metrics = (
        baseline_summary.get("average_metrics") if isinstance(baseline_summary.get("average_metrics"), dict) else {}
    )
    input_overhead_pct = _pct_delta(
        float(variant_usage.get("input_tokens", 0) or 0),
        float(baseline_usage.get("input_tokens", 0) or 0),
    )
    output_overhead_pct = _pct_delta(
        float(variant_usage.get("output_tokens", 0) or 0),
        float(baseline_usage.get("output_tokens", 0) or 0),
    )
    reasoning_overhead_pct = _pct_delta(
        float(variant_usage.get("reasoning_output_tokens", 0) or 0),
        float(baseline_usage.get("reasoning_output_tokens", 0) or 0),
    )
    command_overhead_delta = _numeric_delta(
        variant_metrics.get("command_execution_count"),
        baseline_metrics.get("command_execution_count"),
    )
    return {
        "status": "collected",
        "pass_rate_delta": pass_rate_delta,
        "average_input_token_overhead_pct": input_overhead_pct,
        "average_output_token_overhead_pct": output_overhead_pct,
        "average_reasoning_token_overhead_pct": reasoning_overhead_pct,
        "average_command_execution_delta": command_overhead_delta,
        "pass_rate_per_100k_input_tokens_delta": _numeric_delta(
            _pass_rate_per_usage_unit(variant_summary, "input_tokens", 100000),
            _pass_rate_per_usage_unit(baseline_summary, "input_tokens", 100000),
        ),
        "pass_rate_per_100_commands_delta": _numeric_delta(
            _pass_rate_per_metric_unit(variant_summary, "command_execution_count", 100),
            _pass_rate_per_metric_unit(baseline_summary, "command_execution_count", 100),
        ),
        "cost_efficiency_note": (
            "Compatibility telemetry only: these parsed token and command ratios are not used to claim "
            "cost reduction or efficiency improvement."
        ),
    }


def _case_cost_outliers(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[int]] = {}
    for result in results:
        usage = ((result.get("metrics") or {}).get("usage") or {})
        input_tokens = usage.get("input_tokens")
        if not isinstance(input_tokens, int | float):
            continue
        key = (str(result.get("case_id") or "unknown"), str(result.get("variant") or "unknown"))
        grouped.setdefault(key, []).append(int(input_tokens))
    averages = [
        sum(values) / len(values)
        for values in grouped.values()
        if values
    ]
    if not averages:
        return []
    baseline = median(averages)
    if baseline <= 0:
        return []
    outliers: list[dict[str, Any]] = []
    for (case_id, variant), values in sorted(grouped.items()):
        average_input_tokens = round(sum(values) / len(values), 2)
        if average_input_tokens > max(baseline * 2, baseline + 50000):
            outliers.append(
                {
                    "case_id": case_id,
                    "variant": variant,
                    "average_input_tokens": average_input_tokens,
                    "median_cell_average_input_tokens": round(baseline, 2),
                }
            )
    return outliers[:10]


def _stability_summary(
    results: list[dict[str, Any]],
    variants: dict[str, dict[str, Any]],
    cases_summary: dict[str, Any],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    del variants  # Variant aggregates remain embedded in cases_summary.
    result_count = len(results)
    failure_categories = _counts(results, "failure_category")
    artifact_status_counts = _counts(results, "artifact_status")
    grading_status_counts = _counts(results, "grading_status")
    cell_runs = [
        int(variant_payload.get("runs", 0) or 0)
        for case_payload in cases_summary.values()
        if isinstance(case_payload, dict)
        for variant_payload in (case_payload.get("variants") or {}).values()
        if isinstance(variant_payload, dict)
    ]
    failed_run_reasons_by_case = _failed_run_reasons_by_case(results)
    codex_exec_failed_by_case = _failed_run_reasons_by_case(results, only_failure_category="codex_exec_failed")
    codex_exec_retries_by_case = _codex_exec_retries_by_case(results)
    flaky_case_variant_cells = _flaky_case_variant_cells(cases_summary)
    skills_with_hooks_regression_cases = _skills_with_hooks_regression_cases(cases_summary)
    codex_exec_retry_count = sum(int(result.get("codex_retry_count", 0) or 0) for result in results)
    security = _security_metric_buckets(results)
    return {
        "requested_runs_per_variant": int(manifest.get("runs_per_variant", 0) or 0),
        "observed_case_variant_cell_count": len(cell_runs),
        "observed_min_runs_per_case_variant": min(cell_runs) if cell_runs else 0,
        "observed_max_runs_per_case_variant": max(cell_runs) if cell_runs else 0,
        "artifact_status_counts": artifact_status_counts,
        "grading_status_counts": grading_status_counts,
        "setup_failure_rate": _count_rate(failure_categories, "setup_failed", result_count),
        "test_suite_failure_rate": _count_rate(failure_categories, "test_suite_failed", result_count),
        "security_assertion_failure_rate": _rate(len(security["assertion_failed"]), len(security["eligible"])),
        "security_check_execution_failure_rate": _rate(len(security["execution_failed"]), result_count),
        "security_failure_rate": _rate(len(security["assertion_failed"]), len(security["eligible"])),
        "security_failure_rate_definition": "alias of security_assertion_failure_rate; execution failures are tracked separately",
        "codex_exec_failure_rate": _count_rate(failure_categories, "codex_exec_failed", result_count),
        "not_collected_grading_rate": _count_rate(grading_status_counts, "not_collected", result_count),
        "contamination_rate": _count_rate(failure_categories, "contaminated", result_count),
        "codex_exec_retry_count": codex_exec_retry_count,
        "codex_exec_failed_by_case": codex_exec_failed_by_case,
        "codex_exec_retries_by_case": codex_exec_retries_by_case,
        "failed_run_reasons_by_case": failed_run_reasons_by_case,
        "flaky_case_variant_cells": flaky_case_variant_cells,
        "case_regression_count": len(skills_with_hooks_regression_cases),
        "skills_with_hooks_regression_cases": skills_with_hooks_regression_cases,
        "partial_status_reasons": _partial_status_reasons(
            artifact_status_counts=artifact_status_counts,
            failure_categories=failure_categories,
            grading_status_counts=grading_status_counts,
            codex_exec_retry_count=codex_exec_retry_count,
            skills_with_hooks_regression_cases=skills_with_hooks_regression_cases,
            cell_runs=cell_runs,
            requested_runs=int(manifest.get("runs_per_variant", 0) or 0),
        ),
    }


def _failed_run_reasons_by_case(
    results: list[dict[str, Any]],
    *,
    only_failure_category: str | None = None,
) -> dict[str, dict[str, dict[str, int]]]:
    nested: dict[str, dict[str, dict[str, int]]] = {}
    for result in results:
        failure_category = str(result.get("failure_category") or "grading_not_collected")
        if failure_category in {"none", "telemetry_only"}:
            continue
        if only_failure_category is not None and failure_category != only_failure_category:
            continue
        case_id = str(result.get("case_id") or "unknown")
        variant = str(result.get("variant") or "unknown")
        nested.setdefault(case_id, {}).setdefault(variant, {})
        bucket = nested[case_id][variant]
        bucket[failure_category] = bucket.get(failure_category, 0) + 1
    return nested


def _codex_exec_retries_by_case(results: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    nested: dict[str, dict[str, int]] = {}
    for result in results:
        retry_count = int(result.get("codex_retry_count", 0) or 0)
        if retry_count <= 0:
            continue
        case_id = str(result.get("case_id") or "unknown")
        variant = str(result.get("variant") or "unknown")
        nested.setdefault(case_id, {})
        nested[case_id][variant] = nested[case_id].get(variant, 0) + retry_count
    return nested


def _flaky_case_variant_cells(cases_summary: dict[str, Any]) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    for case_id, case_payload in sorted(cases_summary.items()):
        if not isinstance(case_payload, dict):
            continue
        for variant, variant_payload in sorted((case_payload.get("variants") or {}).items()):
            if not isinstance(variant_payload, dict):
                continue
            failure_categories = variant_payload.get("failure_categories") or {}
            if not isinstance(failure_categories, dict):
                continue
            passed_count = int(failure_categories.get("none", 0) or 0)
            failed_count = sum(
                int(count or 0)
                for category, count in failure_categories.items()
                if category not in {"none", "telemetry_only"}
            )
            if passed_count > 0 and failed_count > 0:
                cells.append(
                    {
                        "case_id": case_id,
                        "variant": variant,
                        "passed_count": passed_count,
                        "failed_count": failed_count,
                        "failure_categories": failure_categories,
                    }
                )
    return cells


def _skills_with_hooks_regression_cases(cases_summary: dict[str, Any]) -> list[dict[str, Any]]:
    regressions: list[dict[str, Any]] = []
    for case_id, case_payload in sorted(cases_summary.items()):
        if not isinstance(case_payload, dict):
            continue
        variants = case_payload.get("variants") or {}
        if not isinstance(variants, dict):
            continue
        baseline = variants.get("baseline_clean")
        hooks = variants.get("skills_with_hooks_clean")
        if not isinstance(baseline, dict) or not isinstance(hooks, dict):
            continue
        baseline_rate = baseline.get("pass_rate")
        hooks_rate = hooks.get("pass_rate")
        if isinstance(baseline_rate, int | float) and isinstance(hooks_rate, int | float) and hooks_rate < baseline_rate:
            regressions.append(
                {
                    "case_id": case_id,
                    "baseline_pass_rate": baseline_rate,
                    "skills_with_hooks_pass_rate": hooks_rate,
                    "pass_rate_delta": round(float(hooks_rate) - float(baseline_rate), 4),
                }
            )
    return regressions


def _partial_status_reasons(
    *,
    artifact_status_counts: dict[str, int],
    failure_categories: dict[str, int],
    grading_status_counts: dict[str, int],
    codex_exec_retry_count: int,
    skills_with_hooks_regression_cases: list[dict[str, Any]],
    cell_runs: list[int],
    requested_runs: int,
) -> list[str]:
    reasons: list[str] = []
    for status in ("failed", "partial"):
        count = int(artifact_status_counts.get(status, 0) or 0)
        if count:
            reasons.append(f"artifact_status_{status}:{count}")
    for category in ("codex_exec_failed", "setup_failed", "test_suite_failed", "security_checks_failed"):
        count = int(failure_categories.get(category, 0) or 0)
        if count:
            reasons.append(f"{category}:{count}")
    not_collected = int(grading_status_counts.get("not_collected", 0) or 0)
    if not_collected:
        reasons.append(f"grading_not_collected:{not_collected}")
    if codex_exec_retry_count:
        reasons.append(f"codex_exec_retried:{codex_exec_retry_count}")
    if skills_with_hooks_regression_cases:
        reasons.append(f"skills_with_hooks_regression_cases:{len(skills_with_hooks_regression_cases)}")
    if cell_runs and requested_runs > 0 and min(cell_runs) < requested_runs:
        reasons.append(f"observed_min_runs_below_requested:{min(cell_runs)}/{requested_runs}")
    return reasons


def _total_usage(results: list[dict[str, Any]]) -> dict[str, int]:
    totals = {key: 0 for key in USAGE_KEYS}
    for result in results:
        usage = ((result.get("metrics") or {}).get("usage") or {})
        for key in USAGE_KEYS:
            totals[key] += int(usage.get(key, 0) or 0)
    return totals


def _count_rate(counts: dict[str, int], key: str, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(int(counts.get(key, 0) or 0) / denominator, 4)


def _common_value(
    manifest: dict[str, Any],
    results: list[dict[str, Any]],
    key: str,
    fallback: str,
) -> str:
    values = {str(result.get(key)) for result in results if result.get(key)}
    if not values and manifest.get(key):
        values.add(str(manifest[key]))
    if len(values) == 1:
        return next(iter(values))
    if not values:
        return fallback
    return "mixed"


def _changeforge_summary_metadata(manifest: dict[str, Any], results: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate strict benchmark provenance without treating baseline no-install as mixed."""
    install_sources = {
        str(result.get("changeforge_install_source"))
        for result in results
        if result.get("changeforge_install_source") and result.get("changeforge_install_source") != "none"
    }
    if not install_sources and manifest.get("changeforge_install_source"):
        manifest_source = str(manifest["changeforge_install_source"])
        if manifest_source != "none":
            install_sources.add(manifest_source)
    profiles = {
        str(result.get("changeforge_profile"))
        for result in results
        if result.get("changeforge_profile") and result.get("changeforge_profile") != "none"
    }
    if not profiles and manifest.get("changeforge_profile"):
        manifest_profile = str(manifest["changeforge_profile"])
        if manifest_profile != "none":
            profiles.add(manifest_profile)
    return {
        "changeforge_install_source": _single_or_mixed(install_sources, fallback="none"),
        "changeforge_profile": _single_or_mixed(profiles, fallback="none"),
        "changeforge_hooks_enabled": any(
            result.get("changeforge_hooks_enabled") is True for result in results
        )
        or manifest.get("changeforge_hooks_enabled") is True,
        "user_level_install_used": any(result.get("user_level_install_used") is True for result in results)
        or manifest.get("user_level_install_used") is True,
    }


def _changeforge_variant_metadata(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Return exact provenance for one variant summary."""
    install_sources = {
        str(result.get("changeforge_install_source"))
        for result in results
        if result.get("changeforge_install_source")
    }
    profiles = {str(result.get("changeforge_profile")) for result in results if result.get("changeforge_profile")}
    return {
        "changeforge_install_source": _single_or_mixed(install_sources, fallback="none"),
        "changeforge_profile": _single_or_mixed(profiles, fallback="none"),
        "changeforge_hooks_enabled": any(result.get("changeforge_hooks_enabled") is True for result in results),
        "user_level_install_used": any(result.get("user_level_install_used") is True for result in results),
    }


def _single_or_mixed(values: set[str], *, fallback: str) -> str:
    if not values:
        return fallback
    if len(values) == 1:
        return next(iter(values))
    return "mixed"


def _environment_flags(results: list[dict[str, Any]]) -> dict[str, bool]:
    environments = [result.get("environment") for result in results if isinstance(result.get("environment"), dict)]
    return {
        "user_skills_visible": any(env.get("user_skills_visible") is True for env in environments),
        "user_config_loaded": any(env.get("user_config_loaded") is True for env in environments),
        "user_rules_loaded": any(env.get("user_rules_loaded") is True for env in environments),
        "ignore_user_config": bool(environments) and all(env.get("ignore_user_config") is True for env in environments),
        "ignore_rules": bool(environments) and all(env.get("ignore_rules") is True for env in environments),
        "plugins_disabled": bool(environments) and all(env.get("plugins_disabled") is True for env in environments),
    }


def _strict_benchmark_eligible(
    benchmark_mode: str,
    auth_policy: str,
    environment_policy: str,
    environment_flags: dict[str, bool],
    changeforge_metadata: dict[str, Any],
    current_home_full_result_count: int,
    results: list[dict[str, Any]],
) -> bool:
    return bool(
        benchmark_mode in STRICT_BENCHMARK_MODES
        and auth_policy in STRICT_AUTH_POLICIES
        and environment_policy in STRICT_CODEX_ENVIRONMENT_POLICIES
        and current_home_full_result_count == 0
        and environment_flags.get("user_skills_visible") is False
        and environment_flags.get("user_config_loaded") is False
        and environment_flags.get("user_rules_loaded") is False
        and environment_flags.get("ignore_user_config") is True
        and environment_flags.get("ignore_rules") is True
        and environment_flags.get("plugins_disabled") is True
        and changeforge_metadata.get("user_level_install_used") is False
        and any(result.get("benchmark_eligible") is True for result in results)
    )


def _codex_home_policy(manifest: dict[str, Any], results: list[dict[str, Any]], benchmark_mode: str) -> str:
    env_policy = _common_value(manifest, results, "codex_environment_policy", "")
    if env_policy == "auth_borrowed_clean":
        return "auth_borrowed_clean"
    if env_policy == "isolated_api_key":
        return "isolated_only"
    if env_policy == "current_home_full":
        return "current_home_smoke_only"
    modes = {str(result.get("codex_home_mode")) for result in results if result.get("codex_home_mode")}
    if not modes and manifest.get("codex_home_mode"):
        modes.add(str(manifest["codex_home_mode"]))
    if benchmark_mode in STRICT_BENCHMARK_MODES and modes <= {"isolated"}:
        return "isolated_only"
    if benchmark_mode == "current-home-smoke" and modes <= {"current"}:
        return "current_home_smoke_only"
    return "mixed_or_unknown"


def _limitations(
    benchmark_mode: str,
    *,
    assertion_case_count: int,
    variants: dict[str, dict[str, Any]],
    evidence_scope: str,
    unknown_setup_failure_rate: float,
) -> list[str]:
    base = [
        "Local Codex CLI runs depend on the installed CLI, configured model, account access, and local machine state.",
        "Parsed telemetry excludes raw command bodies and assistant/user message content.",
        "Pass rates include only benchmark_eligible assertion-backed results; telemetry-only cases are counted separately.",
    ]
    if benchmark_mode == "current-home-smoke":
        base.append(
            "Current-home smoke runs may inherit user-level Codex config, auth, skills, hooks, and trust state; they are not baseline comparisons."
        )
    else:
        base.append(
            "Strict comparative claims may borrow Codex authentication only; user skills, hooks, config, and rules are not loaded."
        )
        base.append("Baseline contamination blocks publishing, and pass rates include assertion-backed eligible results only.")
        eligible_counts = [
            int(payload.get("benchmark_eligible_result_count", 0) or 0)
            for payload in variants.values()
            if isinstance(payload, dict)
        ]
        if evidence_scope == "multi_case_ablation_3_run":
            base.append(
                "Current strict live evidence covers ablation across at least 5 assertion-backed cases and 3 runs "
                "per required variant, "
                "but remains local Codex CLI evidence."
            )
        elif assertion_case_count < 3 or not eligible_counts or min(eligible_counts) < 3:
            base.append(
                "Current strict live evidence is a smoke sample only: it supports only the listed case and variants, "
                "not a broad rd-skills pass-rate improvement claim. Stronger claims require at least 3-5 "
                "assertion-backed cases with 3 runs per variant."
            )
        else:
            base.append(
                "Current strict live evidence covers multiple assertion-backed cases, but repeated-run evidence is "
                "still limited; keep small-sample limitations until each variant has at least 3 runs."
            )
    if unknown_setup_failure_rate > 0.2:
        base.append("Setup failure diagnostics remain incomplete.")
    return base


def _markdown_pct(value: Any) -> str:
    if not isinstance(value, int | float):
        return "not_collected"
    return f"{float(value) * 100:+.2f}%"


def _render_process_warning(process: dict[str, Any]) -> str | None:
    if not process:
        return "process evidence not collected"
    raw_trace_count = process.get("process_trace_count", "not_collected")
    if raw_trace_count == "not_collected":
        return "process_trace_count not_collected"
    trace_count = int(raw_trace_count or 0)
    if trace_count <= 0:
        return "process_trace_count is 0"
    present_rates = (
        process.get("pdd_present_rate"),
        process.get("ddd_present_rate"),
        process.get("sdd_present_rate"),
        process.get("tdd_present_rate"),
    )
    if all(isinstance(value, int | float) and float(value) == 0.0 for value in present_rates):
        return "explicit PDD/DDD/SDD/TDD traces were not captured"
    fallback_rate = process.get("required_field_fallback_rate")
    if isinstance(fallback_rate, int | float) and float(fallback_rate) > 0.5:
        return "required field fallback rate exceeds 0.5"
    return None


def render_markdown(summary: dict[str, Any]) -> str:
    """Render a concise Markdown summary."""
    process = summary.get("process_compliance_summary") if isinstance(summary.get("process_compliance_summary"), dict) else {}
    coverage = summary.get("coverage_summary") if isinstance(summary.get("coverage_summary"), dict) else {}
    quality = (
        summary.get("quality_improvement_summary")
        if isinstance(summary.get("quality_improvement_summary"), dict)
        else {}
    )
    capability = (
        summary.get("capability_coverage_summary")
        if isinstance(summary.get("capability_coverage_summary"), dict)
        else {}
    )
    case_results = (
        summary.get("case_result_summary")
        if isinstance(summary.get("case_result_summary"), dict)
        else {}
    )
    compact = (
        summary.get("compact_context_summary")
        if isinstance(summary.get("compact_context_summary"), dict)
        else {}
    )
    cost = summary.get("cost_summary") if isinstance(summary.get("cost_summary"), dict) else {}
    total_usage = cost.get("total_usage") if isinstance(cost.get("total_usage"), dict) else {}
    stability = summary.get("stability_summary") if isinstance(summary.get("stability_summary"), dict) else {}
    cost_delta = (
        ((cost or {}).get("cost_adjusted_delta") or {}).get(
            "skills_with_hooks_clean_vs_baseline_clean",
            {},
        )
        if isinstance(cost, dict)
        else {}
    )
    cost_delta = cost_delta if isinstance(cost_delta, dict) else {}
    process_warning = _render_process_warning(process)
    lines = [
        "# Codex CLI Live Benchmark Summary",
        "",
        f"- Status: `{summary['status']}`",
        f"- Evidence level: `{summary['evidence_level']}`",
        f"- Evidence scope: `{summary['evidence_scope']}`",
        f"- Evidence scope ready: `{summary.get('evidence_scope_ready', summary['evidence_scope_detail']['evidence_scope_ready'])}`",
        f"- Evidence scope reason: {summary['evidence_scope_detail']['reason']}",
        f"- Evidence status: `{summary['evidence_status']}`",
        f"- Effect verdict: `{summary['effect_verdict']}`",
        f"- Effect status: `{summary['effect_status']}`",
        f"- Effect reason: {summary['effect_summary']['reason']}",
        f"- Dominant failure category: `{summary['effect_summary'].get('dominant_failure_category')}`",
        f"- Dominant setup failure reason: `{summary['dominant_setup_failure_reason']}`",
        f"- Dominant setup failure subreason: `{summary['dominant_setup_failure_subreason']}`",
        f"- Unknown setup failure rate: `{summary['unknown_setup_failure_rate']}`",
        f"- Benchmark mode: `{summary['benchmark_mode']}`",
        f"- Auth policy: `{summary['auth_policy']}`",
        f"- Environment policy: `{summary['codex_environment_policy']}`",
        f"- ChangeForge install source: `{summary['changeforge_install_source']}`",
        f"- ChangeForge profile: `{summary['changeforge_profile']}`",
        f"- ChangeForge hooks enabled: `{summary['changeforge_hooks_enabled']}`",
        f"- User-level install used: `{summary['user_level_install_used']}`",
        f"- Strict benchmark eligible: `{summary['strict_benchmark_eligible']}`",
        f"- Run id: `{summary['run_id']}`",
        f"- Assertion-backed cases: `{summary['assertion_case_count']}`",
        f"- Telemetry-only cases: `{summary['telemetry_only_case_count']}`",
        f"- Results: `{summary['result_count']}`",
        f"- Benchmark eligible results: `{summary['benchmark_eligible_result_count']}`",
        f"- Telemetry-only results: `{summary['telemetry_only_result_count']}`",
        f"- Contaminated results: `{summary['contaminated_result_count']}`",
        f"- Coverage tiers: `{coverage.get('tiers', 'not_collected')}`",
        f"- Registered live cases: `{coverage.get('registered_live_case_count', 'not_collected')}`",
        f"- Registered publishable assertion cases: `{coverage.get('registered_publishable_assertion_case_count', 'not_collected')}`",
        f"- Actual run case coverage: `{coverage.get('actual_run_case_count', 'not_collected')}/{coverage.get('manifest_case_count', 'not_collected')}`",
        f"- Coverage dimensions: `{coverage.get('coverage_dimensions', 'not_collected')}`",
        f"- Total input tokens: `{total_usage.get('input_tokens', 'not_collected')}`",
        f"- Total output tokens: `{total_usage.get('output_tokens', 'not_collected')}`",
        f"- Observed min runs per case/variant: `{stability.get('observed_min_runs_per_case_variant', 'not_collected')}`",
        f"- Test-suite failure rate: `{stability.get('test_suite_failure_rate', 'not_collected')}`",
        f"- Codex exec retries: `{stability.get('codex_exec_retry_count', 'not_collected')}`",
        f"- Partial status reasons: `{stability.get('partial_status_reasons', 'not_collected')}`",
        f"- Structured log events: `{summary.get('logging_summary', {}).get('run_log_events', 0)}`",
        f"- Timeline events: `{summary.get('logging_summary', {}).get('timeline_events', 0)}`",
        f"- Process trace count: `{process.get('process_trace_count', 'not_collected')}`",
        "",
        "## Quality Improvement",
        "",
        f"- baseline_clean pass rate: `{quality.get('baseline_clean_pass_rate', 'not_collected')}`",
        f"- skills_only_clean pass rate: `{quality.get('skills_only_clean_pass_rate', 'not_collected')}`",
        f"- skills_with_hooks_clean pass rate: `{quality.get('skills_with_hooks_clean_pass_rate', 'not_collected')}`",
        f"- skills_only vs baseline delta: `{quality.get('skills_only_vs_baseline_delta', 'not_collected')}`",
        f"- skills_with_hooks vs skills_only delta: `{quality.get('skills_with_hooks_vs_skills_only_delta', 'not_collected')}`",
        f"- skills_with_hooks vs baseline delta: `{quality.get('skills_with_hooks_vs_baseline_delta', 'not_collected')}`",
        f"- no_quality_regression: `{quality.get('no_quality_regression', 'not_collected')}`",
        f"- large_quality_improvement_claim: `{quality.get('large_quality_improvement_claim', 'not_collected')}`",
        "",
        "## Capability Coverage",
        "",
        f"- Status: `{capability.get('status', 'not_collected')}`",
        f"- Core capabilities: `{capability.get('core_capability_count', 'not_collected')}`",
        f"- Pass/partial/fail/not_collected: `{capability.get('pass_count', 'not_collected')}`/`{capability.get('partial_count', 'not_collected')}`/`{capability.get('fail_count', 'not_collected')}`/`{capability.get('not_collected_count', 'not_collected')}`",
        f"- Assertion-backed covered capabilities: `{capability.get('assertion_backed_coverage_count', 'not_collected')}`",
        "",
        "| Capability | Linked cases | Run status | Assertion status | Evidence collected | Status |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in capability.get("items", []) if isinstance(capability.get("items"), list) else []:
        lines.append(
            "| "
            + f"{item.get('id')} | "
            + f"{', '.join(str(case) for case in item.get('linked_cases', [])) or 'not_collected'} | "
            + f"`{item.get('run_status', 'not_collected')}` | "
            + f"`{item.get('assertion_status', 'not_collected')}` | "
            + f"`{item.get('evidence_collected', False)}` | "
            + f"`{item.get('status', 'not_collected')}` |"
        )
    lines.extend(
        [
            "",
            "## Context Compaction Retention",
            "",
            f"- Compact case run status: `{compact.get('run_status', 'not_collected')}`",
            f"- pre_compact_snapshot_count: `{compact.get('pre_compact_snapshot_count', 'not_collected')}`",
            f"- post_compact_reinject_count: `{compact.get('post_compact_reinject_count', 'not_collected')}`",
            f"- session_compact_reinject_count: `{compact.get('session_compact_reinject_count', 'not_collected')}`",
            f"- compact_runtime_evidence_count: `{compact.get('compact_runtime_evidence_count', 'not_collected')}`",
            f"- restored_required_context_fields: `{compact.get('restored_required_context_fields', 'not_collected')}`",
            f"- missing_required_context_fields: `{compact.get('missing_required_context_fields', 'not_collected')}`",
            f"- redacted_required_context_fields: `{compact.get('redacted_required_context_fields', 'not_collected')}`",
            f"- context_unusable_fields: `{compact.get('context_unusable_fields', 'not_collected')}`",
            f"- privacy_redaction_status: `{compact.get('privacy_redaction_status', 'not_collected')}`",
            f"- context_usable_status: `{compact.get('context_usable_status', 'not_collected')}`",
            f"- context_retention_status: `{compact.get('context_retention_status', 'not_collected')}`",
            f"- compact_after_repair_continuation_status: `{compact.get('compact_after_repair_continuation_status', 'not_collected')}`",
            f"- candidate_context_status: `{compact.get('candidate_context_status', 'not_collected')}`",
        ]
    )
    lines.extend(
        [
            "",
        "## Process Compliance",
        "",
        f"- pdd_present_rate: `{process.get('pdd_present_rate', 'not_collected')}`",
        f"- ddd_present_rate: `{process.get('ddd_present_rate', 'not_collected')}`",
        f"- sdd_present_rate: `{process.get('sdd_present_rate', 'not_collected')}`",
        f"- tdd_present_rate: `{process.get('tdd_present_rate', 'not_collected')}`",
        f"- review_present_rate: `{process.get('review_present_rate', 'not_collected')}`",
        f"- repair_present_rate: `{process.get('repair_present_rate', 'not_collected')}`",
        f"- rereview_present_rate: `{process.get('rereview_present_rate', 'not_collected')}`",
        f"- inferred_rate: `{process.get('process_trace_inferred_only_rate', process.get('all_core_phases_inferred_only_rate', 'not_collected'))}`",
        f"- required_field_fallback_rate: `{process.get('required_field_fallback_rate', 'not_collected')}`",
        f"- validation_command_present_rate: `{process.get('validation_command_present_rate', 'not_collected')}`",
        "- Explicit trace contract: `changeforge_route`, PDD acceptance, DDD invariants, SDD placement/error contract, and TDD validation trace.",
        ]
    )
    if process_warning:
        lines.append(f"- Warning: {process_warning}; inferred/fallback traces do not prove full process compliance.")
    lines.extend(
        [
            "",
            "## Case-Level Result",
            "",
            f"- Improved cases: `{[row.get('case_id') for row in case_results.get('improved_cases', [])]}`",
            f"- No improvement cases: `{[row.get('case_id') for row in case_results.get('no_improvement_cases', [])]}`",
            f"- Regressed cases: `{[row.get('case_id') for row in case_results.get('regressed_cases', [])]}`",
            f"- Reliability no-improvement cases: `{[row.get('case_id') for row in case_results.get('reliability_no_improvement_cases', [])]}`",
            f"- Known unresolved reliability cases: `{[row.get('case_id') for row in case_results.get('known_unresolved_reliability_cases', [])]}`",
            "",
            "## Cost Telemetry",
            "",
            f"- skills_with_hooks_clean_vs_baseline_clean input token overhead: `{_markdown_pct(cost_delta.get('average_input_token_overhead_pct'))}`",
            f"- skills_with_hooks_clean_vs_baseline_clean output token overhead: `{_markdown_pct(cost_delta.get('average_output_token_overhead_pct'))}`",
            f"- skills_with_hooks_clean_vs_baseline_clean reasoning token overhead: `{_markdown_pct(cost_delta.get('average_reasoning_token_overhead_pct'))}`",
            f"- skills_with_hooks_clean_vs_baseline_clean command execution delta: `{cost_delta.get('average_command_execution_delta', 'not_collected')}`",
            f"- skills_with_hooks_clean_vs_baseline_clean pass rate delta: `{cost_delta.get('pass_rate_delta', 'not_collected')}`",
            f"- Cost is telemetry only: `{cost.get('cost_is_telemetry_only', 'not_collected')}`",
            "- Quality-first benchmark does not gate on cost.",
            "- No cost reduction or efficiency improvement claim is made.",
            f"- Cost caveat: {cost.get('cost_caveat', 'parsed local Codex telemetry, not a billing ledger or quality gate.')}",
            "",
            "## Variants",
            "",
        ]
    )
    for variant, variant_summary in summary["variants"].items():
        average_usage = variant_summary.get("average_usage") if isinstance(variant_summary.get("average_usage"), dict) else {}
        median_usage = variant_summary.get("median_usage") if isinstance(variant_summary.get("median_usage"), dict) else {}
        average_metrics = (
            variant_summary.get("average_metrics") if isinstance(variant_summary.get("average_metrics"), dict) else {}
        )
        lines.extend(
            [
                f"### {variant}",
                "",
                f"- Results: `{variant_summary['result_count']}`",
                f"- Runs: `{variant_summary['run_count']}`",
                f"- Cases: `{variant_summary['case_count']}`",
                f"- Eligible results: `{variant_summary['benchmark_eligible_result_count']}`",
                f"- Pass rate: `{variant_summary['pass_rate']}`",
                f"- Security pass rate: `{variant_summary['security_pass_rate']}`",
                f"- Security assertion failure rate: `{variant_summary.get('security_assertion_failure_rate', 'not_collected')}`",
                f"- Security check execution failure rate: `{variant_summary.get('security_check_execution_failure_rate', 'not_collected')}`",
                f"- Dominant setup failure reason: `{variant_summary['dominant_setup_failure_reason']}`",
                f"- Dominant setup failure subreason: `{variant_summary['dominant_setup_failure_subreason']}`",
                f"- Unknown setup failure rate: `{variant_summary['unknown_setup_failure_rate']}`",
                f"- Average input tokens: `{average_usage.get('input_tokens', 'not_collected')}`",
                f"- Average output tokens: `{average_usage.get('output_tokens', 'not_collected')}`",
                f"- Average reasoning tokens: `{average_usage.get('reasoning_output_tokens', 'not_collected')}`",
                f"- Median input tokens: `{median_usage.get('input_tokens', 'not_collected')}`",
                f"- Average command executions: `{average_metrics.get('command_execution_count', 'not_collected')}`",
                f"- Average file changes: `{average_metrics.get('file_change_count', 'not_collected')}`",
                "",
            ]
        )
    if summary.get("cases_summary"):
        lines.extend(["## Cases", ""])
        for case_id, case_summary in summary["cases_summary"].items():
            lines.extend([f"### {case_id}", "", f"- Grading mode: `{case_summary['grading_mode']}`"])
            for variant, payload in case_summary["variants"].items():
                lines.append(f"- {variant}: runs `{payload['runs']}`, pass rate `{payload['pass_rate']}`")
            lines.append("")
    lines.extend(["## Limitations", "", *[f"- {item}" for item in summary["limitations"]], ""])
    return "\n".join(lines)


def publish_summary(summary: dict[str, Any], markdown: str, *, root: Path = ROOT) -> None:
    """Publish a strict validated live summary into reports for scorecard ingestion."""
    errors = strict_publish_errors(summary)
    if errors:
        raise ValueError("; ".join(errors))
    if not _canonical_publish_ready(summary):
        publish_smoke_summary(summary, markdown, root=root)
        return
    write_json(root / "reports" / "codex-live-benchmark-summary.json", summary)
    (root / "reports" / "codex-live-benchmark-summary.md").write_text(markdown, encoding="utf-8")


def publish_smoke_summary(summary: dict[str, Any], markdown: str, *, root: Path = ROOT) -> None:
    """Publish strict smoke diagnostics without replacing canonical benchmark evidence."""
    if summary.get("benchmark_mode") not in STRICT_BENCHMARK_MODES:
        raise ValueError("Codex live smoke publication requires clean-paired or ablation mode")
    write_json(root / "reports" / "codex-live-smoke-summary.json", summary)
    (root / "reports" / "codex-live-smoke-summary.md").write_text(markdown, encoding="utf-8")


def _canonical_publish_ready(summary: dict[str, Any]) -> bool:
    detail = summary.get("evidence_scope_detail")
    return (
        summary.get("benchmark_mode") == "ablation"
        and summary.get("evidence_scope") == "multi_case_ablation_3_run"
        and isinstance(detail, dict)
        and detail.get("evidence_scope_ready") is True
        and summary.get("effect_status") != "inconclusive"
        and summary.get("effect_verdict") != "inconclusive"
    )


def strict_publish_errors(summary: dict[str, Any]) -> list[str]:
    """Return why a summary cannot support a strict public benchmark claim."""
    errors: list[str] = []
    benchmark_mode = summary.get("benchmark_mode")
    if summary.get("status") in {"not_collected", "skipped_not_opted_in"}:
        errors.append("dry-run, skipped, or not-collected summaries cannot be published")
    if benchmark_mode not in STRICT_BENCHMARK_MODES:
        errors.append("strict benchmark publication requires clean-paired or ablation mode")
    if summary.get("evidence_level") != LIVE_EVIDENCE_LEVEL:
        errors.append(f"strict benchmark publication requires evidence_level {LIVE_EVIDENCE_LEVEL}")
    if summary.get("auth_policy") not in STRICT_AUTH_POLICIES:
        errors.append("strict benchmark publication requires auth_policy borrow-current or isolated-api-key")
    if summary.get("codex_environment_policy") not in STRICT_CODEX_ENVIRONMENT_POLICIES:
        errors.append("strict benchmark publication requires a strict Codex environment policy")
    if summary.get("strict_benchmark_eligible") is not True:
        errors.append("strict benchmark publication requires strict_benchmark_eligible=true")
    if int(summary.get("current_home_result_count", 0) or 0) != 0 or int(
        summary.get("current_home_full_result_count", 0) or 0
    ) != 0:
        errors.append("strict benchmark publication cannot include current-home-full results")
    if summary.get("user_skills_visible") is not False:
        errors.append("strict benchmark publication requires user_skills_visible=false")
    if summary.get("user_config_loaded") is not False:
        errors.append("strict benchmark publication requires user_config_loaded=false")
    if summary.get("user_rules_loaded") is not False:
        errors.append("strict benchmark publication requires user_rules_loaded=false")
    if summary.get("ignore_user_config") is not True or summary.get("ignore_rules") is not True:
        errors.append("strict benchmark publication requires --ignore-user-config and --ignore-rules")
    if summary.get("plugins_disabled") is not True:
        errors.append("strict benchmark publication requires --disable plugins")
    if summary.get("user_level_install_used") is not False:
        errors.append("strict benchmark publication requires user_level_install_used=false")
    if summary.get("changeforge_install_source") != "current_repository":
        errors.append("strict benchmark publication requires current_repository ChangeForge install source")
    if int(summary.get("contaminated_result_count", 0) or 0) != 0:
        errors.append("strict benchmark publication cannot include contaminated results")
    if int(summary.get("benchmark_eligible_result_count", 0) or 0) <= 0:
        errors.append("strict benchmark publication requires assertion-backed eligible results")
    if summary.get("effect_verdict") == "positive" and summary.get("dominant_setup_failure_reason") == "unknown":
        errors.append("strict benchmark publication cannot claim positive effect while unknown setup failures dominate")
    variants = summary.get("variants") or {}
    for variant in MODE_DEFAULT_VARIANTS.get(str(benchmark_mode), ()):
        variant_summary = variants.get(variant) or {}
        if int(variant_summary.get("benchmark_eligible_result_count", 0) or 0) <= 0:
            errors.append(f"strict benchmark publication requires eligible assertion results for {variant}")
        if variant == "baseline_clean" and variant_summary.get("changeforge_install_source") != "none":
            errors.append("baseline_clean must not install ChangeForge")
        if variant == "skills_only_clean":
            if variant_summary.get("changeforge_install_source") != "current_repository":
                errors.append("skills_only_clean must install ChangeForge from current_repository")
            if variant_summary.get("changeforge_hooks_enabled") is not False:
                errors.append("skills_only_clean must not enable ChangeForge hooks")
        if variant == "skills_with_hooks_clean":
            if variant_summary.get("changeforge_install_source") != "current_repository":
                errors.append("skills_with_hooks_clean must install ChangeForge from current_repository")
            if variant_summary.get("changeforge_hooks_enabled") is not True:
                errors.append("skills_with_hooks_clean must enable project-level ChangeForge hooks")
        if variant_summary.get("user_level_install_used") is not False:
            errors.append(f"{variant} must not use user-level install state")
    if benchmark_mode == "ablation":
        delta = summary.get("delta") or {}
        required_delta = (
            "skills_only_clean_vs_baseline_clean",
            "skills_with_hooks_clean_vs_skills_only_clean",
            "skills_with_hooks_clean_vs_baseline_clean",
        )
        for key in required_delta:
            if key not in delta:
                errors.append(f"ablation summary requires delta.{key}")
    return errors


def publish_current_home_smoke(summary: dict[str, Any], markdown: str, *, root: Path = ROOT) -> None:
    """Publish current-home smoke evidence separately from strict benchmark reports."""
    if summary.get("benchmark_mode") != "current-home-smoke":
        raise ValueError("current-home smoke publication requires current-home-smoke mode")
    if summary.get("evidence_level") != CURRENT_HOME_SMOKE_EVIDENCE_LEVEL:
        raise ValueError(f"current-home smoke publication requires evidence_level {CURRENT_HOME_SMOKE_EVIDENCE_LEVEL}")
    if summary.get("strict_benchmark_eligible") is not False:
        raise ValueError("current-home smoke publication must not be strict benchmark eligible")
    write_json(root / "reports" / "codex-current-home-smoke-summary.json", summary)
    (root / "reports" / "codex-current-home-smoke-summary.md").write_text(markdown, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--publish-current-home-smoke", action="store_true")
    args = parser.parse_args(argv)

    summary = generate_summary(args.run_dir)
    markdown = render_markdown(summary)
    json_out = args.json_out or args.run_dir / "summary.json"
    md_out = args.out or args.run_dir / "summary.md"
    write_json(json_out, summary)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.write_text(markdown, encoding="utf-8")
    if args.publish:
        try:
            publish_summary(summary, markdown)
        except ValueError as exc:
            print(f"generate-codex-live-summary: ERROR: {exc}", file=sys.stderr)
            return 1
    if args.publish_current_home_smoke:
        try:
            publish_current_home_smoke(summary, markdown)
        except ValueError as exc:
            print(f"generate-codex-live-summary: ERROR: {exc}", file=sys.stderr)
            return 1
    print(f"wrote Codex live benchmark summary to {md_out} and {json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
