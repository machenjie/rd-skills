#!/usr/bin/env python3
"""Generate a bounded summary for an opt-in Codex CLI live benchmark run."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from codex_live_benchmark_lib import (
    CURRENT_HOME_SMOKE_EVIDENCE_LEVEL,
    LIVE_EVIDENCE_LEVEL,
    MODE_DEFAULT_VARIANTS,
    ROOT,
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
    results = [
        payload
        for payload in (read_json(path) for path in sorted(run_dir.glob("cases/*/*/run-*/result.json")))
        if isinstance(payload, dict)
    ]
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
    current_home_full_result_count = sum(
        1
        for result in real_results
        if result.get("auth_policy") == "current-home-full"
        or result.get("codex_environment_policy") == "current_home_full"
    )

    evidence_level = (
        CURRENT_HOME_SMOKE_EVIDENCE_LEVEL if benchmark_mode == "current-home-smoke" else LIVE_EVIDENCE_LEVEL
    )
    summary = {
        "schema_version": 2,
        "generated_by": "scripts/generate-codex-live-summary.py",
        "status": status,
        "evidence_level": evidence_level,
        "benchmark_mode": benchmark_mode,
        "codex_home_policy": _codex_home_policy(manifest, real_results, benchmark_mode),
        "auth_policy": auth_policy,
        "codex_environment_policy": environment_policy,
        "strict_benchmark_eligible": _strict_benchmark_eligible(
            benchmark_mode,
            auth_policy,
            environment_policy,
            environment_flags,
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
        "current_home_result_count": sum(1 for result in real_results if result.get("codex_home_mode") == "current"),
        "current_home_full_result_count": current_home_full_result_count,
        **environment_flags,
        "variants": variants,
        "delta": deltas,
        "cases": cases,
        "telemetry": {
            "event_count": sum(int((result.get("metrics") or {}).get("event_count", 0) or 0) for result in real_results),
            "parse_error_count": sum(len((result.get("metrics") or {}).get("parse_errors", [])) for result in real_results),
        },
        "limitations": _limitations(benchmark_mode),
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
    return {
        "result_count": len(results),
        "artifact_status_counts": _counts(results, "artifact_status"),
        "grading_status_counts": _counts(results, "grading_status"),
        "benchmark_eligible_result_count": len(eligible),
        "benchmark_passed_result_count": len(passed),
        "pass_rate": _rate(len(passed), len(eligible)),
        "security_pass_rate": _rate(len(security_passed), len(security_eligible)),
        "telemetry_only_result_count": sum(1 for result in results if result.get("grading_status") == "telemetry_only"),
        "not_collected_grading_count": sum(1 for result in results if result.get("grading_status") == "not_collected"),
        "contaminated_result_count": sum(
            1 for result in results if (result.get("contamination") or {}).get("contaminated") is True
        ),
        "average_usage": _average_usage(results),
        "average_metrics": _average_metrics(results),
        "average_event_count": _average_metrics(results)["event_count"],
        "average_file_change_count": _average_metrics(results)["file_change_count"],
        "average_command_execution_count": _average_metrics(results)["command_execution_count"],
    }


def _counts(results: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for result in results:
        value = str(result.get(key) or "not_collected")
        counts[value] = counts.get(value, 0) + 1
    return counts


def _average_usage(results: list[dict[str, Any]]) -> dict[str, float]:
    totals = {key: 0 for key in USAGE_KEYS}
    for result in results:
        usage = ((result.get("metrics") or {}).get("usage") or {})
        for key in USAGE_KEYS:
            totals[key] += int(usage.get(key, 0) or 0)
    return _average(totals, len(results))


def _average_metrics(results: list[dict[str, Any]]) -> dict[str, float]:
    totals = {key: 0 for key in METRIC_KEYS}
    for result in results:
        metrics = result.get("metrics") or {}
        for key in METRIC_KEYS:
            totals[key] += int(metrics.get(key, 0) or 0)
    return _average(totals, len(results))


def _average(totals: dict[str, int], count: int) -> dict[str, float]:
    divisor = max(count, 1)
    return {key: round(value / divisor, 2) for key, value in totals.items()}


def _rate(numerator: int, denominator: int) -> float | str:
    if denominator == 0:
        return "not_collected"
    return round(numerator / denominator, 4)


def _variant_deltas(variants: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    baseline = variants.get("baseline_clean")
    deltas: dict[str, dict[str, Any]] = {}
    for variant, summary in variants.items():
        if variant == "baseline_clean" or not baseline:
            continue
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


def _pct_delta(value: float, baseline: float) -> float | str:
    if baseline == 0:
        return None
    return round((value - baseline) / baseline, 4)


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


def _limitations(benchmark_mode: str) -> list[str]:
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
    return base


def render_markdown(summary: dict[str, Any]) -> str:
    """Render a concise Markdown summary."""
    lines = [
        "# Codex CLI Live Benchmark Summary",
        "",
        f"- Status: `{summary['status']}`",
        f"- Evidence level: `{summary['evidence_level']}`",
        f"- Benchmark mode: `{summary['benchmark_mode']}`",
        f"- Auth policy: `{summary['auth_policy']}`",
        f"- Environment policy: `{summary['codex_environment_policy']}`",
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
                f"- Eligible results: `{variant_summary['benchmark_eligible_result_count']}`",
                f"- Pass rate: `{variant_summary['pass_rate']}`",
                f"- Security pass rate: `{variant_summary['security_pass_rate']}`",
                f"- Average input tokens: `{variant_summary['average_usage']['input_tokens']}`",
                f"- Average output tokens: `{variant_summary['average_usage']['output_tokens']}`",
                f"- Average command executions: `{variant_summary['average_metrics']['command_execution_count']}`",
                f"- Average file changes: `{variant_summary['average_metrics']['file_change_count']}`",
                "",
            ]
        )
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
    if int(summary.get("contaminated_result_count", 0) or 0) != 0:
        errors.append("strict benchmark publication cannot include contaminated results")
    if int(summary.get("benchmark_eligible_result_count", 0) or 0) <= 0:
        errors.append("strict benchmark publication requires assertion-backed eligible results")
    variants = summary.get("variants") or {}
    for variant in MODE_DEFAULT_VARIANTS.get(str(benchmark_mode), ()):
        variant_summary = variants.get(variant) or {}
        if int(variant_summary.get("benchmark_eligible_result_count", 0) or 0) <= 0:
            errors.append(f"strict benchmark publication requires eligible assertion results for {variant}")
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
