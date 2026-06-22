#!/usr/bin/env python3
"""Generate a bounded summary for an opt-in Codex CLI live benchmark run."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from statistics import median
from typing import Any

from codex_live_benchmark_lib import (
    CURRENT_HOME_SMOKE_EVIDENCE_LEVEL,
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
    read_json,
    validate_status,
    write_json,
)


METRIC_KEYS = ("event_count", "command_execution_count", "file_change_count", "plan_update_count", "error_count")
USAGE_KEYS = ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens")


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
    variant_order = _variant_order(manifest, real_results, benchmark_mode)
    variants = {variant: _variant_summary(_results_for_variant(real_results, variant)) for variant in variant_order}
    deltas = _variant_deltas(variants)
    for variant in variants:
        variants[variant]["delta_vs_baseline_clean"] = deltas.get(f"{variant}_vs_baseline_clean", {})
    cases_summary = _cases_summary(real_results)

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
        "evidence_scope_detail": evidence_scope_detail,
        "evidence_status": _evidence_status(status),
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
    return summary


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
    security_eligible = [result for result in eligible if "security_checks_passed" in (result.get("grading") or {})]
    security_passed = [
        result for result in security_eligible if (result.get("grading") or {}).get("security_checks_passed") is True
    ]
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
        "security_pass_rate": _rate(len(security_passed), len(security_eligible)),
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


def render_markdown(summary: dict[str, Any]) -> str:
    """Render a concise Markdown summary."""
    lines = [
        "# Codex CLI Live Benchmark Summary",
        "",
        f"- Status: `{summary['status']}`",
        f"- Evidence level: `{summary['evidence_level']}`",
        f"- Evidence scope: `{summary['evidence_scope']}`",
        f"- Evidence scope ready: `{summary['evidence_scope_detail']['evidence_scope_ready']}`",
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
        "",
        "## Variants",
        "",
    ]
    for variant, variant_summary in summary["variants"].items():
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
                f"- Dominant setup failure reason: `{variant_summary['dominant_setup_failure_reason']}`",
                f"- Dominant setup failure subreason: `{variant_summary['dominant_setup_failure_subreason']}`",
                f"- Unknown setup failure rate: `{variant_summary['unknown_setup_failure_rate']}`",
                f"- Average input tokens: `{variant_summary['average_usage']['input_tokens']}`",
                f"- Median input tokens: `{variant_summary['median_usage']['input_tokens']}`",
                f"- Average output tokens: `{variant_summary['average_usage']['output_tokens']}`",
                f"- Average command executions: `{variant_summary['average_metrics']['command_execution_count']}`",
                f"- Average file changes: `{variant_summary['average_metrics']['file_change_count']}`",
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
    write_json(root / "reports" / "codex-live-benchmark-summary.json", summary)
    (root / "reports" / "codex-live-benchmark-summary.md").write_text(markdown, encoding="utf-8")


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
