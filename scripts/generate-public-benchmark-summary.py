#!/usr/bin/env python3
"""Generate a public, conservative benchmark summary from local evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tomllib
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from codex_live_benchmark_lib import (
    CODEX_LIVE_CAPABILITY_COVERAGE_NAME,
    CODEX_LIVE_PASS_RATE_BENCHMARK_NAME,
    LIVE_EVIDENCE_LEVEL,
    MODE_DEFAULT_VARIANTS,
    STRICT_AUTH_POLICIES,
    STRICT_BENCHMARK_MODES,
    STRICT_CODEX_ENVIRONMENT_POLICIES,
    codex_live_capability_coverage_status,
    codex_live_capability_repair_hints,
    codex_live_compact_detail,
    codex_live_evidence_scope_ready,
    codex_live_pass_rate_status,
    codex_live_repair_hints,
    public_status_from_live,
)
from validation_utils import EXPECTED_PROFILE_TOP_LEVEL_COUNTS


ROOT = Path(__file__).resolve().parents[1]
PROFILES = ("recommended", "full", "dev")
STATUS_ORDER = ("pass", "partial", "fail", "unknown", "not_collected")
COMMITTED_SOURCE_COMMIT = "provided by release artifact / CI metadata"
MARKETPLACE_DIMENSION = "Marketplace index validation"
SKILL_EFFICACY_DIMENSION = "Skill efficacy structural fixtures"
RUNTIME_GOVERNANCE_DIMENSION = "Runtime governance structural fixtures"
EXECUTOR_ADAPTER_DIMENSION = "Executor adapter structural fixtures"
ACTIVATION_PRECISION_DIMENSION = "Activation precision benchmark"
RUNTIME_TELEMETRY_FIXTURE_DIMENSION = "Runtime telemetry fixture sample"
LIVE_RUNTIME_TELEMETRY_DIMENSION = "Live runtime telemetry sample"
EXECUTOR_LIVE_PASS_RATE_DIMENSION = "Executor adapter live pass-rate"
EXECUTOR_TOKEN_OVERHEAD_DIMENSION = "Executor adapter token overhead"
EXECUTOR_TURN_OVERHEAD_DIMENSION = "Executor adapter turn overhead"
CODEX_LIVE_PASS_RATE_DIMENSION = CODEX_LIVE_PASS_RATE_BENCHMARK_NAME
CODEX_LIVE_CAPABILITY_COVERAGE_DIMENSION = CODEX_LIVE_CAPABILITY_COVERAGE_NAME
HOOK_SAFETY_DIMENSION = "Hook safety"
INSTALLATION_VALIDATION_DIMENSION = "Installation validation"
SCORECARD_REFRESH_COMMAND = (
    "python3 scripts/generate-professional-scorecard.py "
    "--out reports/professional-scorecard.md "
    "--json-out reports/professional-scorecard.json"
)
REFRESH_COMMANDS = [
    "python3 scripts/eval-routing.py",
    "python3 scripts/eval-skill-professionalism.py",
    "python3 scripts/eval-skill-professionalism.py --coverage-matrix",
    "python3 scripts/eval-professional-benchmarks.py",
    "python3 scripts/validate-skill-efficacy-benchmarks.py",
    "python3 scripts/eval-executor-adapters.py",
    "python3 scripts/eval-activation-precision.py --mode built --runtime-root dist/codex/project/.codex/hooks",
    "python3 scripts/run-codex-live-benchmarks.py --list",
    "python3 scripts/run-codex-live-benchmarks.py --benchmark-mode ablation --auth-policy borrow-current --benchmark security/ssrf-url-allowlist --dry-run --out /tmp/changeforge-codex-live-ablation-dry-run",
    "python3 scripts/validate-codex-live-benchmark-reports.py --run-dir /tmp/changeforge-codex-live-ablation-dry-run",
    "python3 scripts/validate-report-consistency.py",
    "python3 scripts/validate-professionalism-regression.py --strict",
    "python3 scripts/validate-professional-routing-coverage.py",
    "python3 scripts/validate-hooks.py --json-out reports/hook-validation.json --out reports/hook-validation.md",
    "python3 scripts/build.py --profile recommended",
    "python3 scripts/build.py --profile full",
    "python3 scripts/build.py --profile dev",
    "python3 scripts/validate-runtime-reference-links.py",
    "python3 scripts/validate-installation.py --json-out reports/installation-validation.json --out reports/installation-validation.md",
    "python3 scripts/validate-marketplace-index.py --profile recommended",
    "python3 scripts/validate-marketplace-index.py --profile full",
    "python3 scripts/validate-marketplace-index.py --profile dev",
    "python3 scripts/generate-public-benchmark-summary.py --out reports/public-benchmark-summary.md --json-out reports/public-benchmark-summary.json",
]


@dataclass(frozen=True)
class EvidenceItem:
    """One summarized evidence row."""

    name: str
    status: str
    source: str
    detail: str
    command: str
    evidence_level: str = "structural fixture"
    detail_data: dict[str, Any] | None = None


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _scorecard_path_and_source(root: Path, scorecard_path: Path | None) -> tuple[Path, str]:
    """Return the scorecard path to read and the source label to render."""
    path = scorecard_path or Path("reports") / "professional-scorecard.json"
    if not path.is_absolute():
        path = root / path
    try:
        source = path.relative_to(root).as_posix()
    except ValueError:
        source = str(path)
    return path, source


def _project_version(root: Path) -> str:
    path = root / "pyproject.toml"
    if not path.exists():
        return "unknown"
    try:
        parsed = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError:
        return "unknown"
    project = parsed.get("project", {})
    return str(project.get("version", "unknown")) if isinstance(project, dict) else "unknown"


def _status_from_summary(summary: dict[str, Any] | None, *, pass_key: str = "cases_checked") -> str:
    if summary is None:
        return "unknown"
    if summary.get("quality_failures") or summary.get("fail") or summary.get("missing"):
        return "fail"
    statuses = summary.get("statuses")
    if isinstance(statuses, dict):
        if statuses.get("fail") or statuses.get("missing"):
            return "fail"
        if statuses.get("needs-review") or statuses.get("partial") or statuses.get("sample-grade"):
            return "partial"
    if summary.get(pass_key) or summary.get("count"):
        return "pass"
    return "unknown"


def _release_readiness_items(root: Path) -> list[EvidenceItem]:
    path = root / "reports" / "professionalism-release-readiness.json"
    readiness = _read_json(path)
    if not isinstance(readiness, dict):
        return [
            EvidenceItem(
            "Release readiness",
            "unknown",
            "reports/professionalism-release-readiness.json",
            "report missing or invalid",
            "python3 scripts/validate-professionalism-regression.py --strict",
            "structural fixture",
        )
        ]

    routing = readiness.get("routing_coverage_summary")
    skill = readiness.get("professional_skill_coverage_summary")
    foundation = readiness.get("key_foundation_capability_coverage_summary")
    strict = readiness.get("strict_regression_status")
    return [
        EvidenceItem(
            "Routing coverage",
            _status_from_summary(routing if isinstance(routing, dict) else None),
            "reports/professionalism-release-readiness.json",
            json.dumps(routing, sort_keys=True) if isinstance(routing, dict) else "routing summary missing",
            "python3 scripts/validate-professional-routing-coverage.py",
        ),
        EvidenceItem(
            "Professional skill coverage",
            _status_from_summary(skill if isinstance(skill, dict) else None, pass_key="count"),
            "reports/professionalism-release-readiness.json",
            json.dumps(skill, sort_keys=True) if isinstance(skill, dict) else "professional skill summary missing",
            "python3 scripts/eval-skill-professionalism.py",
        ),
        EvidenceItem(
            "Foundation capability coverage",
            _status_from_summary(foundation if isinstance(foundation, dict) else None, pass_key="count"),
            "reports/professionalism-release-readiness.json",
            json.dumps(foundation, sort_keys=True) if isinstance(foundation, dict) else "foundation coverage summary missing",
            "python3 scripts/eval-skill-professionalism.py --coverage-matrix",
        ),
        EvidenceItem(
            "Strict regression",
            "pass" if strict == "pass" else ("fail" if strict in {"fail", "blocked"} else "unknown"),
            "reports/professionalism-release-readiness.json",
            f"strict_regression_status={strict}",
            "python3 scripts/validate-professionalism-regression.py --strict",
            "promoted golden case",
        ),
    ]


def _direct_report_items(root: Path) -> list[EvidenceItem]:
    skill_eval = _read_json(root / "reports" / "skill-professionalism-eval.json")
    coverage = _read_json(root / "reports" / "professional-coverage-matrix.json")
    return [
        EvidenceItem(
            "Skill professionalism report",
            "pass" if isinstance(skill_eval, dict) and skill_eval.get("items") else "unknown",
            "reports/skill-professionalism-eval.json",
            f"average_score={skill_eval.get('average_score')}" if isinstance(skill_eval, dict) else "report missing",
            "python3 scripts/eval-skill-professionalism.py",
        ),
        EvidenceItem(
            "Professional coverage matrix",
            "pass" if isinstance(coverage, dict) and coverage.get("rows") else "unknown",
            "reports/professional-coverage-matrix.json",
            f"rows={len(coverage.get('rows', []))}" if isinstance(coverage, dict) else "report missing",
            "python3 scripts/eval-skill-professionalism.py --coverage-matrix",
        ),
    ]


def _profile_build_items(root: Path) -> list[EvidenceItem]:
    items: list[EvidenceItem] = []
    for profile in PROFILES:
        path = root / "dist" / "universal" / "skills" / profile / ".changeforge-build-manifest.json"
        manifest = _read_json(path)
        if not isinstance(manifest, dict):
            items.append(
                EvidenceItem(
                    f"Profile build: {profile}",
                    "unknown",
                    str(path.relative_to(root)),
                    "build manifest missing",
                    f"python3 scripts/build.py --profile {profile}",
                )
            )
            continue
        top_level = len(manifest.get("top_level_skills", []))
        expected = EXPECTED_PROFILE_TOP_LEVEL_COUNTS[profile]
        status = "pass" if top_level == expected else "fail"
        items.append(
            EvidenceItem(
                f"Profile build: {profile}",
                status,
                str(path.relative_to(root)),
                f"top_level={top_level}, expected={expected}",
                f"python3 scripts/build.py --profile {profile}",
            )
        )
    return items


def _scorecard_dimension_item(
    root: Path,
    dimension_name: str,
    public_name: str,
    scorecard_path: Path | None = None,
    evidence_level: str = "structural fixture",
    missing_status: str = "unknown",
) -> EvidenceItem:
    """Return one public evidence item from the generated professional scorecard."""
    path, source = _scorecard_path_and_source(root, scorecard_path)
    scorecard = _read_json(path)
    if not isinstance(scorecard, dict):
        return EvidenceItem(
            public_name,
            missing_status,
            source,
            "scorecard report missing or invalid",
            SCORECARD_REFRESH_COMMAND,
        )

    dimensions = scorecard.get("dimensions")
    if not isinstance(dimensions, list):
        return EvidenceItem(
            public_name,
            missing_status,
            source,
            "scorecard dimensions missing or invalid",
            SCORECARD_REFRESH_COMMAND,
        )

    for dimension in dimensions:
        if not isinstance(dimension, dict) or dimension.get("name") != dimension_name:
            continue
        status = str(dimension.get("status", "unknown"))
        if status not in STATUS_ORDER:
            status = "unknown"
        return EvidenceItem(
            public_name,
            status,
            source,
            str(dimension.get("detail", "detail missing")),
            str(dimension.get("verification_command", "")) or SCORECARD_REFRESH_COMMAND,
            evidence_level,
        )

    return EvidenceItem(
        public_name,
        missing_status,
        source,
        f"{dimension_name} dimension missing",
        SCORECARD_REFRESH_COMMAND,
    )


def _codex_live_benchmark_item(
    root: Path,
    *,
    dimension_name: str = CODEX_LIVE_PASS_RATE_DIMENSION,
    status_func=codex_live_pass_rate_status,
    repair_hints_func=codex_live_repair_hints,
) -> EvidenceItem:
    """Return public evidence directly from the published Codex live summary."""
    source = "reports/codex-live-benchmark-summary.json"
    summary = _read_json(root / source)
    if not isinstance(summary, dict):
        return EvidenceItem(
            dimension_name,
            "not_collected",
            source,
            "Codex live benchmark summary missing or invalid",
            "python3 scripts/run-codex-live-benchmarks.py --list",
            LIVE_EVIDENCE_LEVEL,
        )
    status, strict_errors, readiness_warnings = status_func(summary)
    detail = codex_live_compact_detail(
        summary,
        status=status,
        strict_errors=strict_errors,
        readiness_warnings=readiness_warnings,
    )
    comparison = _codex_live_previous_comparison(
        previous=_read_previous_committed_json(root, source),
        current=summary,
    )
    if comparison:
        detail["previous_current_comparison"] = comparison
    detail["repair_hints"] = repair_hints_func(summary)
    return EvidenceItem(
        dimension_name,
        status,
        source,
        _codex_live_public_detail(summary, detail),
        "python3 scripts/validate-codex-live-benchmark-reports.py --summary reports/codex-live-benchmark-summary.json",
        LIVE_EVIDENCE_LEVEL,
        detail,
    )


def _codex_live_pass_rate_benchmark_item(root: Path) -> EvidenceItem:
    return _codex_live_benchmark_item(
        root,
        dimension_name=CODEX_LIVE_PASS_RATE_DIMENSION,
        status_func=codex_live_pass_rate_status,
        repair_hints_func=codex_live_repair_hints,
    )


def _codex_live_capability_coverage_item(root: Path) -> EvidenceItem:
    return _codex_live_benchmark_item(
        root,
        dimension_name=CODEX_LIVE_CAPABILITY_COVERAGE_DIMENSION,
        status_func=codex_live_capability_coverage_status,
        repair_hints_func=codex_live_capability_repair_hints,
    )


def _codex_live_public_detail(summary: dict[str, Any], detail: dict[str, Any]) -> str:
    """Render a compact human detail for the public Markdown table."""
    variants = detail.get("variants") if isinstance(detail.get("variants"), dict) else {}
    variant_names = ", ".join(sorted(variants)) if variants else "not_collected"
    hooks = variants.get("skills_with_hooks_clean") if isinstance(variants, dict) else None
    hooks_pass_rate = hooks.get("pass_rate") if isinstance(hooks, dict) else "not_collected"
    run_counts = ", ".join(
        f"{variant}:{payload.get('run_count')}"
        for variant, payload in sorted(variants.items())
        if isinstance(payload, dict)
    ) or "not_collected"
    delta = ((detail.get("cost_summary") or {}).get("cost_adjusted_delta") or {}).get(
        "skills_with_hooks_clean_vs_baseline_clean",
        {},
    )
    input_overhead = _format_pct(delta.get("average_input_token_overhead_pct") if isinstance(delta, dict) else None)
    output_overhead = _format_pct(delta.get("average_output_token_overhead_pct") if isinstance(delta, dict) else None)
    command_delta = (
        delta.get("average_command_execution_delta")
        if isinstance(delta, dict)
        else "not_collected"
    )
    limitations = detail.get("limitations") if isinstance(detail.get("limitations"), list) else []
    warnings = detail.get("readiness_warnings") if isinstance(detail.get("readiness_warnings"), list) else []
    strict_errors = detail.get("strict_errors") if isinstance(detail.get("strict_errors"), list) else []
    overhead_warning = _codex_live_overhead_warning(summary, delta if isinstance(delta, dict) else {})
    if overhead_warning:
        warnings = [*warnings, overhead_warning]
    parts = [
        f"mode={detail.get('benchmark_mode')}",
        f"scope={detail.get('evidence_scope')}",
        f"ready={detail.get('evidence_scope_ready')}",
        f"cases={detail.get('assertion_case_count')}/{detail.get('case_count')}",
        f"results={detail.get('benchmark_eligible_result_count')}/{detail.get('result_count')}",
        f"runs={run_counts}",
        f"variants={variant_names}",
        f"skills_with_hooks_clean.pass_rate={hooks_pass_rate}",
        f"effect={detail.get('effect_status')}/{detail.get('effect_verdict')}",
        f"token_overhead=input {input_overhead}, output {output_overhead}",
        f"command_delta={command_delta}",
    ]
    if strict_errors:
        parts.append("errors=" + "; ".join(str(item) for item in strict_errors[:4]))
    if warnings:
        parts.append("warnings=" + "; ".join(str(item) for item in warnings[:4]))
    if limitations:
        parts.append("limitations=" + "; ".join(str(item) for item in limitations[:3]))
    return "; ".join(parts)


def _format_pct(value: Any) -> str:
    if not isinstance(value, int | float):
        return "not_collected"
    return f"{float(value) * 100:+.2f}%"


def _codex_live_overhead_warning(summary: dict[str, Any], delta: dict[str, Any]) -> str | None:
    input_overhead = delta.get("average_input_token_overhead_pct")
    if (
        not codex_live_evidence_scope_ready(summary)
        and isinstance(input_overhead, int | float)
        and float(input_overhead) > 0.5
    ):
        return "Smoke run shows high overhead; do not claim efficiency improvement."
    return None


def _read_previous_committed_json(root: Path, source: str) -> dict[str, Any] | None:
    """Return the committed copy of a report when this workspace has a newer one."""
    try:
        completed = subprocess.run(
            ["git", "show", f"HEAD:{source}"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    if completed.returncode != 0 or not completed.stdout.strip():
        return None
    try:
        parsed = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _codex_live_previous_comparison(
    *,
    previous: dict[str, Any] | None,
    current: dict[str, Any],
) -> dict[str, Any] | None:
    """Build a bounded before/after payload for a replaced live benchmark summary."""
    if not isinstance(previous, dict):
        return None
    previous_run_id = previous.get("run_id")
    current_run_id = current.get("run_id")
    if not previous_run_id or not current_run_id or previous_run_id == current_run_id:
        return None
    return {
        "previous_run_id": previous_run_id,
        "current_run_id": current_run_id,
        "setup_script_modified_bad_path": {
            "before": _count_nested(previous, "setup_failure_reasons", "setup_script_modified_bad_path"),
            "after": _count_nested(current, "setup_failure_reasons", "setup_script_modified_bad_path"),
        },
        "starter_fragile_path": {
            "before": _count_nested(previous, "setup_failure_subreasons", "starter_fragile_path"),
            "after": _count_nested(current, "setup_failure_subreasons", "starter_fragile_path"),
        },
        "unknown_setup_failure_rate": {
            "before": previous.get("unknown_setup_failure_rate"),
            "after": current.get("unknown_setup_failure_rate"),
        },
        "skills_with_hooks_vs_baseline": {
            "before": _variant_pass_rate_comparison(previous),
            "after": _variant_pass_rate_comparison(current),
        },
        "setup_failed_by_variant": {
            "before": _setup_failed_by_variant(previous),
            "after": _setup_failed_by_variant(current),
        },
    }


def _count_nested(payload: dict[str, Any], field: str, key: str) -> int:
    values = payload.get(field)
    if not isinstance(values, dict):
        return 0
    value = values.get(key, 0)
    return int(value) if isinstance(value, int) else 0


def _variant_pass_rate_comparison(summary: dict[str, Any]) -> dict[str, Any]:
    variants = summary.get("variants") if isinstance(summary.get("variants"), dict) else {}
    baseline = variants.get("baseline_clean") if isinstance(variants, dict) else None
    hooks = variants.get("skills_with_hooks_clean") if isinstance(variants, dict) else None
    baseline_rate = baseline.get("pass_rate") if isinstance(baseline, dict) else None
    hooks_rate = hooks.get("pass_rate") if isinstance(hooks, dict) else None
    delta = None
    if isinstance(baseline_rate, int | float) and isinstance(hooks_rate, int | float):
        delta = round(float(hooks_rate) - float(baseline_rate), 4)
    return {
        "baseline_clean_pass_rate": baseline_rate,
        "skills_with_hooks_clean_pass_rate": hooks_rate,
        "pass_rate_delta": delta,
    }


def _setup_failed_by_variant(summary: dict[str, Any]) -> dict[str, int]:
    effect_summary = summary.get("effect_summary")
    setup_failed = effect_summary.get("setup_failed_by_variant") if isinstance(effect_summary, dict) else None
    if isinstance(setup_failed, dict):
        return {str(variant): int(count) for variant, count in setup_failed.items() if isinstance(count, int)}
    variants = summary.get("variants") if isinstance(summary.get("variants"), dict) else {}
    return {
        variant: _count_nested(payload, "failure_categories", "setup_failed")
        for variant, payload in variants.items()
        if isinstance(payload, dict)
    }


def _codex_live_strict_summary_errors(summary: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    benchmark_mode = summary.get("benchmark_mode")
    if summary.get("evidence_level") != LIVE_EVIDENCE_LEVEL:
        errors.append(f"evidence_level must be {LIVE_EVIDENCE_LEVEL}")
    if benchmark_mode not in STRICT_BENCHMARK_MODES:
        errors.append("benchmark_mode must be clean-paired or ablation")
    if summary.get("auth_policy") not in STRICT_AUTH_POLICIES:
        errors.append("auth_policy must be borrow-current or isolated-api-key")
    if summary.get("codex_environment_policy") not in STRICT_CODEX_ENVIRONMENT_POLICIES:
        errors.append("codex_environment_policy must be auth_borrowed_clean or isolated_api_key")
    if summary.get("strict_benchmark_eligible") is not True:
        errors.append("strict_benchmark_eligible must be true")
    if int(summary.get("current_home_result_count", 0) or 0) != 0 or int(
        summary.get("current_home_full_result_count", 0) or 0
    ) != 0:
        errors.append("current-home-full results are not public benchmark evidence")
    if summary.get("user_skills_visible") is not False:
        errors.append("user skills must not be visible")
    if summary.get("user_config_loaded") is not False:
        errors.append("user config must not be loaded")
    if summary.get("user_rules_loaded") is not False:
        errors.append("user rules must not be loaded")
    if summary.get("ignore_user_config") is not True or summary.get("ignore_rules") is not True:
        errors.append("--ignore-user-config and --ignore-rules are required")
    if summary.get("plugins_disabled") is not True:
        errors.append("--disable plugins is required")
    if int(summary.get("contaminated_result_count", 0) or 0) != 0:
        errors.append("contaminated results are not public benchmark evidence")
    if int(summary.get("benchmark_eligible_result_count", 0) or 0) <= 0:
        errors.append("assertion-backed eligible results are required")
    if not isinstance(summary.get("failure_categories"), dict):
        errors.append("failure_categories are required")
    if summary.get("dominant_failure_category") not in {
        "none",
        "codex_exec_failed",
        "install_failed",
        "setup_failed",
        "test_suite_failed",
        "security_checks_failed",
        "contaminated",
        "grading_not_collected",
        "telemetry_only",
    }:
        errors.append("dominant_failure_category is required")
    if summary.get("dominant_setup_failure_reason") not in {
        "none",
        "missing_env_root",
        "missing_harness",
        "setup_script_missing",
        "setup_script_modified_bad_path",
        "dependency_install_failed",
        "python_compile_failed",
        "candidate_removed_required_file",
        "permission_denied",
        "shell_error",
        "unknown",
    }:
        errors.append("dominant_setup_failure_reason is required")
    if summary.get("dominant_setup_failure_subreason") not in {
        "none",
        "candidate_modified_setup",
        "starter_fragile_path",
        "missing_env_root",
        "wrong_cwd",
        "missing_harness",
        "classifier_uncertain",
        "unknown",
    }:
        errors.append("dominant_setup_failure_subreason is required")
    if not isinstance(summary.get("setup_failure_subreasons"), dict):
        errors.append("setup_failure_subreasons are required")
    unknown_rate = summary.get("unknown_setup_failure_rate")
    if not isinstance(unknown_rate, int | float) or not 0 <= float(unknown_rate) <= 1:
        errors.append("unknown_setup_failure_rate is required")
    if summary.get("effect_verdict") not in {"inconclusive", "positive", "mixed", "neutral", "negative"}:
        errors.append("effect_verdict is required")
    if summary.get("effect_status") not in {"inconclusive", "improved", "mixed", "neutral", "regression"}:
        errors.append("effect_status is required")
    if not isinstance(summary.get("effect_summary"), dict):
        errors.append("effect_summary is required")
    if summary.get("effect_verdict") == "positive" and summary.get("dominant_setup_failure_reason") == "unknown":
        errors.append("positive effect cannot be claimed while unknown setup failures dominate")
    if not isinstance(summary.get("cases_summary"), dict):
        errors.append("cases_summary is required")
    variants = summary.get("variants") or {}
    for variant in MODE_DEFAULT_VARIANTS.get(str(benchmark_mode), ()):
        payload = variants.get(variant)
        if not isinstance(payload, dict) or int(payload.get("benchmark_eligible_result_count", 0) or 0) <= 0:
            errors.append(f"eligible assertion results are required for {variant}")
    if benchmark_mode == "ablation":
        delta = summary.get("delta") or {}
        for key in (
            "skills_only_clean_vs_baseline_clean",
            "skills_with_hooks_clean_vs_skills_only_clean",
            "skills_with_hooks_clean_vs_baseline_clean",
        ):
            if key not in delta:
                errors.append(f"ablation delta {key} is required")
    return errors


def _additional_status_items(root: Path, scorecard_path: Path | None = None) -> list[EvidenceItem]:
    return [
        _scorecard_dimension_item(
            root,
            HOOK_SAFETY_DIMENSION,
            HOOK_SAFETY_DIMENSION,
            scorecard_path,
            missing_status="not_collected",
        ),
        _scorecard_dimension_item(
            root,
            INSTALLATION_VALIDATION_DIMENSION,
            INSTALLATION_VALIDATION_DIMENSION,
            scorecard_path,
            missing_status="not_collected",
        ),
        _scorecard_dimension_item(root, SKILL_EFFICACY_DIMENSION, SKILL_EFFICACY_DIMENSION, scorecard_path),
        _scorecard_dimension_item(root, RUNTIME_GOVERNANCE_DIMENSION, RUNTIME_GOVERNANCE_DIMENSION, scorecard_path),
        _scorecard_dimension_item(root, EXECUTOR_ADAPTER_DIMENSION, EXECUTOR_ADAPTER_DIMENSION, scorecard_path),
        _scorecard_dimension_item(root, ACTIVATION_PRECISION_DIMENSION, ACTIVATION_PRECISION_DIMENSION, scorecard_path),
        _scorecard_dimension_item(
            root,
            RUNTIME_TELEMETRY_FIXTURE_DIMENSION,
            RUNTIME_TELEMETRY_FIXTURE_DIMENSION,
            scorecard_path,
            "runtime telemetry fixture sample",
        ),
        _scorecard_dimension_item(
            root,
            LIVE_RUNTIME_TELEMETRY_DIMENSION,
            LIVE_RUNTIME_TELEMETRY_DIMENSION,
            scorecard_path,
            "live runtime telemetry sample",
            missing_status="not_collected",
        ),
        _scorecard_dimension_item(
            root,
            EXECUTOR_LIVE_PASS_RATE_DIMENSION,
            EXECUTOR_LIVE_PASS_RATE_DIMENSION,
            scorecard_path,
            "live pass-rate",
        ),
        _scorecard_dimension_item(
            root,
            EXECUTOR_TOKEN_OVERHEAD_DIMENSION,
            EXECUTOR_TOKEN_OVERHEAD_DIMENSION,
            scorecard_path,
            "token overhead",
        ),
        _scorecard_dimension_item(
            root,
            EXECUTOR_TURN_OVERHEAD_DIMENSION,
            EXECUTOR_TURN_OVERHEAD_DIMENSION,
            scorecard_path,
            "turn overhead",
        ),
        _codex_live_pass_rate_benchmark_item(root),
        _codex_live_capability_coverage_item(root),
        _scorecard_dimension_item(root, MARKETPLACE_DIMENSION, MARKETPLACE_DIMENSION, scorecard_path),
    ]


def _scorecard_dimension_items(root: Path, scorecard_path: Path | None = None) -> list[EvidenceItem] | None:
    path, source = _scorecard_path_and_source(root, scorecard_path)
    scorecard = _read_json(path)
    if not isinstance(scorecard, dict):
        return None
    dimensions = scorecard.get("dimensions")
    if not isinstance(scorecard.get("status_summary"), dict) or not isinstance(dimensions, list):
        return None
    items: list[EvidenceItem] = []
    for dimension in dimensions:
        if not isinstance(dimension, dict):
            continue
        name = str(dimension.get("name", "unknown"))
        if name == CODEX_LIVE_PASS_RATE_DIMENSION:
            items.append(_codex_live_pass_rate_benchmark_item(root))
            continue
        if name == CODEX_LIVE_CAPABILITY_COVERAGE_DIMENSION:
            items.append(_codex_live_capability_coverage_item(root))
            continue
        status = str(dimension.get("status", "unknown"))
        if status not in STATUS_ORDER:
            status = "unknown"
        items.append(
            EvidenceItem(
                name,
                status,
                str(dimension.get("source") or source),
                str(dimension.get("detail", "detail missing")),
                str(dimension.get("verification_command", "")) or SCORECARD_REFRESH_COMMAND,
                _dimension_evidence_level(name),
            )
        )
    return items


def _dimension_evidence_level(name: str) -> str:
    mapping = {
        "Promoted agent samples": "promoted golden case",
        RUNTIME_TELEMETRY_FIXTURE_DIMENSION: "runtime telemetry fixture sample",
        LIVE_RUNTIME_TELEMETRY_DIMENSION: "live runtime telemetry sample",
        EXECUTOR_LIVE_PASS_RATE_DIMENSION: "live pass-rate",
        EXECUTOR_TOKEN_OVERHEAD_DIMENSION: "token overhead",
        EXECUTOR_TURN_OVERHEAD_DIMENSION: "turn overhead",
        CODEX_LIVE_PASS_RATE_DIMENSION: LIVE_EVIDENCE_LEVEL,
        CODEX_LIVE_CAPABILITY_COVERAGE_DIMENSION: LIVE_EVIDENCE_LEVEL,
    }
    return mapping.get(name, "structural fixture")


def generate_summary(
    root: Path,
    *,
    source_commit: str = COMMITTED_SOURCE_COMMIT,
    scorecard_path: Path | None = None,
) -> dict[str, Any]:
    """Generate the public benchmark summary payload."""
    items = _scorecard_dimension_items(root, scorecard_path)
    if items is None:
        items = [
            *_release_readiness_items(root),
            *_direct_report_items(root),
            *_profile_build_items(root),
            *_additional_status_items(root, scorecard_path),
        ]
    status_counts = {status: 0 for status in STATUS_ORDER}
    for item in items:
        status_counts[item.status] += 1
    evidence_levels = _sync_codex_live_evidence_level(_scorecard_evidence_levels(root, scorecard_path), items)
    known_unknowns = _known_unknowns(items, evidence_levels)
    return {
        "schema_version": 1,
        "generated_by": "scripts/generate-public-benchmark-summary.py",
        "repository": {
            "name": "machenjie/rd-skills",
            "version": _project_version(root),
            "source_commit": source_commit,
        },
        "status_counts": status_counts,
        "items": [asdict(item) for item in items],
        "evidence_levels": evidence_levels,
        "known_unknowns": known_unknowns,
        "refresh_commands": REFRESH_COMMANDS,
        "claim_boundary": "Local deterministic evidence only; strict Codex live A/B claims may borrow Codex authentication, but must not borrow user skills, hooks, config, or rules. Current-home smoke evidence is not a baseline comparison. Skill efficacy, activation precision, and executor adapter fixtures are structural/local evidence, not live runtime telemetry, empirical before/after performance, external popularity, adoption, marketplace availability, or market claim evidence.",
    }


def _known_unknowns(
    items: list[EvidenceItem],
    evidence_levels: dict[str, dict[str, str]],
) -> list[str]:
    """Return de-duplicated unknown/not-collected item and evidence-level names."""
    names: list[str] = []
    for item in items:
        if item.status in {"unknown", "not_collected"}:
            names.append(_known_unknown_name(item.name))
    for level, detail in evidence_levels.items():
        if detail.get("status") in {"unknown", "not_collected"}:
            names.append(_known_unknown_name(level))
    deduped: list[str] = []
    seen: set[str] = set()
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        deduped.append(name)
    return deduped


def _known_unknown_name(name: str) -> str:
    mapping = {
        "runtime telemetry fixture sample": "Runtime telemetry fixture sample",
        RUNTIME_TELEMETRY_FIXTURE_DIMENSION: "Runtime telemetry fixture sample",
        "live runtime telemetry sample": "Live runtime telemetry sample",
        LIVE_RUNTIME_TELEMETRY_DIMENSION: "Live runtime telemetry sample",
        "live pass-rate": "Live pass-rate",
        EXECUTOR_LIVE_PASS_RATE_DIMENSION: "Live pass-rate",
        "token overhead": "Token overhead",
        EXECUTOR_TOKEN_OVERHEAD_DIMENSION: "Token overhead",
        "turn overhead": "Turn overhead",
        EXECUTOR_TURN_OVERHEAD_DIMENSION: "Turn overhead",
        "local_codex_cli_live_benchmark": "Codex CLI live benchmark",
        CODEX_LIVE_PASS_RATE_DIMENSION: "Codex CLI live pass-rate benchmark",
        CODEX_LIVE_CAPABILITY_COVERAGE_DIMENSION: "Codex CLI live capability coverage",
    }
    return mapping.get(name, name)


def _sync_codex_live_evidence_level(
    evidence_levels: dict[str, dict[str, str]],
    items: list[EvidenceItem],
) -> dict[str, dict[str, str]]:
    """Keep the public live evidence-level status tied to the live summary item."""
    synced = {
        str(level): dict(detail) if isinstance(detail, dict) else {"status": "unknown", "meaning": ""}
        for level, detail in evidence_levels.items()
    }
    codex_statuses = [
        item.status
        for item in items
        if item.name in {CODEX_LIVE_PASS_RATE_DIMENSION, CODEX_LIVE_CAPABILITY_COVERAGE_DIMENSION}
    ]
    if not codex_statuses:
        return synced
    live_level = synced.setdefault(
        LIVE_EVIDENCE_LEVEL,
        {
            "status": "not_collected",
            "meaning": "Opt-in local Codex CLI benchmark run with sanitized bounded artifacts.",
        },
    )
    live_level["status"] = _weaker_status(*codex_statuses)
    live_level.setdefault("meaning", "Opt-in local Codex CLI benchmark run with sanitized bounded artifacts.")
    return synced


def _weaker_status(*statuses: str) -> str:
    order = ("fail", "partial", "not_collected", "unknown", "pass")
    cleaned = [status if status in STATUS_ORDER else "unknown" for status in statuses]
    for status in order:
        if status in cleaned:
            return status
    return "unknown"


def render_markdown(payload: dict[str, Any]) -> str:
    """Render the summary payload as Markdown."""
    repo = payload["repository"]
    lines = [
        "# Public Benchmark Summary",
        "",
        "This generated summary reports local deterministic ChangeForge evidence. Skill efficacy, activation precision, and executor adapter fixtures are structural/local evidence, not live runtime telemetry, live pass-rate, or empirical before/after agent-performance proof. It does not claim external popularity, marketplace availability, or market adoption.",
        "",
        "## Repository",
        "",
        f"- Repository: `{repo['name']}`",
        f"- Version: `{repo['version']}`",
        f"- Source commit: `{repo['source_commit']}`",
        "",
        "## Status Counts",
        "",
    ]
    for status, count in payload["status_counts"].items():
        lines.append(f"- `{status}`: {count}")
    lines.extend(["", "## Evidence Levels", "", "| Evidence | Status | Meaning |", "| --- | --- | --- |"])
    for level, detail in payload.get("evidence_levels", {}).items():
        lines.append(f"| {level} | `{detail.get('status', 'unknown')}` | {detail.get('meaning', '')} |")
    lines.extend(
        [
            "",
            "## Evidence",
            "",
            "| Area | Status | Evidence Level | Source | Detail | Refresh Command |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in payload["items"]:
        lines.append(
            f"| {item['name']} | `{item['status']}` | {item.get('evidence_level', 'structural fixture')} | "
            f"{item['source']} | {item['detail']} | `{item['command']}` |"
        )
    _append_codex_live_sections(lines, payload)
    lines.extend(["", "## Known Unknowns / Not Collected", ""])
    if payload["known_unknowns"]:
        for name in payload["known_unknowns"]:
            lines.append(f"- {name}")
    else:
        lines.append("- None")
    lines.extend(["", "## Refresh Commands", "", "```bash"])
    lines.extend(payload["refresh_commands"])
    lines.extend(["```", ""])
    return "\n".join(lines)


def _append_codex_live_sections(lines: list[str], payload: dict[str, Any]) -> None:
    detail = _public_codex_live_detail(payload)
    if not detail:
        return
    quality = detail.get("quality_improvement_summary") if isinstance(detail.get("quality_improvement_summary"), dict) else {}
    capability = detail.get("capability_coverage_summary") if isinstance(detail.get("capability_coverage_summary"), dict) else {}
    process = detail.get("process_compliance_summary") if isinstance(detail.get("process_compliance_summary"), dict) else None
    cases = detail.get("case_result_summary") if isinstance(detail.get("case_result_summary"), dict) else {}
    cost = detail.get("cost_summary") if isinstance(detail.get("cost_summary"), dict) else {}

    lines.extend(["", "## Quality Improvement", ""])
    for label, field in (
        ("baseline pass rate", "baseline_clean_pass_rate"),
        ("skills_only pass rate", "skills_only_clean_pass_rate"),
        ("skills_with_hooks pass rate", "skills_with_hooks_clean_pass_rate"),
        ("skills_only vs baseline delta", "skills_only_vs_baseline_delta"),
        ("skills_with_hooks vs skills_only delta", "skills_with_hooks_vs_skills_only_delta"),
        ("skills_with_hooks vs baseline delta", "skills_with_hooks_vs_baseline_delta"),
        ("no_quality_regression", "no_quality_regression"),
        ("large_quality_improvement_claim", "large_quality_improvement_claim"),
    ):
        lines.append(f"- {label}: `{quality.get(field, 'not_collected')}`")

    lines.extend(["", "## Capability Coverage", "", "| Capability | Linked Cases | Evidence | Status |", "| --- | --- | --- | --- |"])
    for item in capability.get("items", []) if isinstance(capability.get("items"), list) else []:
        if not isinstance(item, dict):
            continue
        linked_cases = ", ".join(str(case) for case in item.get("linked_cases", []) if isinstance(case, str))
        lines.append(
            f"| {item.get('id', 'unknown')} | {linked_cases or 'not_collected'} | "
            f"{item.get('run_status', 'not_collected')}/{item.get('assertion_status', 'not_collected')} | "
            f"`{item.get('status', 'unknown')}` |"
        )

    lines.extend(["", "## Process Compliance", ""])
    if isinstance(process, dict):
        for field in (
            "process_trace_count",
            "pdd_present_rate",
            "ddd_present_rate",
            "sdd_present_rate",
            "tdd_present_rate",
            "review_present_rate",
            "repair_present_rate",
            "rereview_present_rate",
            "required_field_fallback_rate",
        ):
            lines.append(f"- {field}: `{process.get(field, 'not_collected')}`")
    else:
        lines.append("- process evidence not collected")

    lines.extend(["", "## Case-Level Result", ""])
    lines.append(
        "- improved_cases: "
        + (", ".join(row["case_id"] for row in cases.get("improved_cases", []) if isinstance(row, dict) and "case_id" in row) or "none")
    )
    lines.append(
        "- no_improvement_cases: "
        + (", ".join(row["case_id"] for row in cases.get("no_improvement_cases", []) if isinstance(row, dict) and "case_id" in row) or "none")
    )
    lines.append(
        "- regressed_cases: "
        + (", ".join(row["case_id"] for row in cases.get("regressed_cases", []) if isinstance(row, dict) and "case_id" in row) or "none")
    )
    lines.append(
        "- reliability_no_improvement_visible: "
        f"`{cases.get('reliability_no_improvement_visible', 'not_collected')}`"
    )

    lines.extend(["", "## Cost Telemetry", ""])
    lines.append("- cost is telemetry only in this phase")
    lines.append("- quality-first benchmark does not gate on cost")
    lines.append("- no cost reduction or efficiency improvement claim is made")
    total_usage = cost.get("total_usage") if isinstance(cost.get("total_usage"), dict) else {}
    for field in ("input_tokens", "output_tokens", "reasoning_output_tokens"):
        lines.append(f"- {field}: `{total_usage.get(field, 'not_collected')}`")


def _public_codex_live_detail(payload: dict[str, Any]) -> dict[str, Any] | None:
    for item in payload.get("items", []):
        if not isinstance(item, dict) or item.get("name") != CODEX_LIVE_PASS_RATE_DIMENSION:
            continue
        detail = item.get("detail_data")
        return detail if isinstance(detail, dict) else None
    return None


def _scorecard_evidence_levels(root: Path, scorecard_path: Path | None) -> dict[str, dict[str, str]]:
    path, _source = _scorecard_path_and_source(root, scorecard_path)
    scorecard = _read_json(path)
    if isinstance(scorecard, dict) and isinstance(scorecard.get("evidence_levels"), dict):
        return scorecard["evidence_levels"]
    return {
        "structural fixture": {
            "status": "unknown",
            "meaning": "Local deterministic structure sample passed; not evidence of live task success.",
        },
        "runtime telemetry fixture sample": {
            "status": "not_collected",
            "meaning": "Deterministic executor-adapter fixture-derived bounded facts; not live runtime telemetry.",
        },
        "live runtime telemetry sample": {
            "status": "not_collected",
            "meaning": "Sanitized bounded facts from an actual hook runtime execution.",
        },
        "promoted golden case": {
            "status": "unknown",
            "meaning": "Human-reviewed case admitted to regression coverage.",
        },
        "live pass-rate": {
            "status": "not_collected",
            "meaning": "Measured real-task success rate.",
        },
        "token overhead": {
            "status": "not_collected",
            "meaning": "Measured additional token cost.",
        },
        "turn overhead": {
            "status": "not_collected",
            "meaning": "Measured additional turn cost.",
        },
        "local_codex_cli_live_benchmark": {
            "status": "not_collected",
            "meaning": "Opt-in local Codex CLI benchmark run with sanitized bounded artifacts.",
        },
    }


def _check_file(path: Path, expected: str) -> list[str]:
    if not path.exists():
        return [f"{path} does not exist"]
    actual = path.read_text(encoding="utf-8")
    if actual != expected:
        return [f"{path} is stale"]
    return []


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for writing or checking public benchmark summaries."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out", required=True)
    parser.add_argument(
        "--source-commit",
        default=COMMITTED_SOURCE_COMMIT,
        help="Source commit metadata for release artifacts. Committed snapshots use a stable non-HEAD label.",
    )
    parser.add_argument(
        "--scorecard",
        help="Professional scorecard JSON used for scorecard-derived dimensions. Defaults to reports/professional-scorecard.json.",
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    scorecard_path = Path(args.scorecard) if args.scorecard else None
    payload = generate_summary(ROOT, source_commit=args.source_commit, scorecard_path=scorecard_path)
    json_text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    md_text = render_markdown(payload)
    out = Path(args.out)
    json_out = Path(args.json_out)
    if args.check:
        errors = [*_check_file(out, md_text), *_check_file(json_out, json_text)]
        if errors:
            for error in errors:
                print(f"generate-public-benchmark-summary: ERROR: {error}", file=sys.stderr)
            return 1
        print("generate-public-benchmark-summary: committed outputs are fresh")
        return 0

    out.parent.mkdir(parents=True, exist_ok=True)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md_text, encoding="utf-8")
    json_out.write_text(json_text, encoding="utf-8")
    print(f"wrote public benchmark summary to {out} and {json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
