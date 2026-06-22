#!/usr/bin/env python3
"""Validate Codex CLI live benchmark reports and published summaries."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from codex_live_benchmark_lib import (
    CODEX_LIVE_EVIDENCE_SCOPES,
    CURRENT_HOME_SMOKE_EVIDENCE_LEVEL,
    EFFECT_STATUSES,
    EFFECT_VERDICTS,
    FAILURE_CATEGORIES,
    FIRST_FAILURE_STAGES,
    LIVE_EVIDENCE_LEVEL,
    MODE_DEFAULT_VARIANTS,
    ROOT,
    SECURITY_FAILURE_REASONS,
    SETUP_CONTRACT_FIELDS,
    SETUP_FAILURE_REASONS,
    SETUP_FAILURE_SUBREASONS,
    STRICT_AUTH_POLICIES,
    STRICT_BENCHMARK_MODES,
    STRICT_CODEX_ENVIRONMENT_POLICIES,
    TEST_SUITE_FAILURE_REASONS,
    load_case_registry,
    print_errors,
    read_json,
    scan_forbidden_absolute_user_paths,
    scan_forbidden_secrets,
    validate_required_fields,
)


REAL_RESULT_REQUIRED_FILES = (
    "prompt.md",
    "codex-command.redacted.json",
    "events.redacted.jsonl",
    "events.metrics.json",
    "final.md",
    "diff.patch",
    "git-status.txt",
    "grading/grading-result.json",
    "result.json",
)


def validate_run_dir(run_dir: Path) -> list[str]:
    """Validate a run directory without requiring dry-run reports to be publishable."""
    errors: list[str] = []
    try:
        load_case_registry()
    except Exception as exc:
        errors.append(f"case registry invalid: {exc}")
    manifest_path = run_dir / "run-manifest.json"
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict):
        return [f"{manifest_path} missing or invalid"]
    errors.extend(validate_required_fields(manifest, "run-manifest"))
    errors.extend(scan_forbidden_secrets(manifest_path))
    errors.extend(scan_forbidden_absolute_user_paths(manifest_path))
    cases_dir = run_dir / "cases"
    if cases_dir.exists():
        errors.extend(scan_forbidden_secrets(cases_dir))
        errors.extend(scan_forbidden_absolute_user_paths(cases_dir))

    result_paths = sorted(run_dir.glob("cases/*/*/run-*/result.json"))
    live_effective = bool(manifest.get("live_execution_effective"))
    if live_effective and not result_paths:
        errors.append("live run manifest has no result.json files")
    if live_effective:
        for summary_file in ("summary.json", "summary.md"):
            if not (run_dir / summary_file).exists():
                errors.append(f"live run manifest is missing {summary_file}")
    if (run_dir / "summary.json").exists():
        errors.extend(f"summary.json: {error}" for error in validate_summary(run_dir / "summary.json", publishable=False))
    for result_path in result_paths:
        try:
            result = read_json(result_path)
        except Exception as exc:
            errors.append(f"{result_path}: invalid JSON: {exc}")
            continue
        if not isinstance(result, dict):
            errors.append(f"{result_path}: invalid JSON")
            continue
        errors.extend(f"{result_path}: {error}" for error in validate_required_fields(result, "case-result"))
        errors.extend(f"{result_path}: {error}" for error in _diagnostic_field_errors("case-result", result))
        if int(result.get("schema_version", 0) or 0) < 2:
            errors.append(f"{result_path}: schema_version must be at least 2")
        if result.get("artifact_status", result.get("status")) in {"collected", "failed", "partial"}:
            case_dir = result_path.parent
            for rel_file in REAL_RESULT_REQUIRED_FILES:
                if not (case_dir / rel_file).exists():
                    errors.append(f"{case_dir}: missing required result artifact {rel_file}")
            grading_payload = read_json(case_dir / "grading" / "grading-result.json")
            if not isinstance(grading_payload, dict):
                errors.append(f"{case_dir}: grading/grading-result.json must be JSON object")
            else:
                errors.extend(f"{case_dir}: {error}" for error in _grading_result_errors(grading_payload))
            command_payload = read_json(case_dir / "codex-command.redacted.json")
            if not isinstance(command_payload, dict):
                errors.append(f"{case_dir}: codex-command.redacted.json must be JSON object")
            else:
                errors.extend(f"{case_dir}: {error}" for error in _command_metadata_errors(command_payload))
        if result.get("grading_mode") == "telemetry_only" and result.get("benchmark_eligible") is True:
            errors.append(f"{result_path}: telemetry-only result cannot be benchmark_eligible")
        if result.get("benchmark_mode") == "current-home-smoke" and result.get("benchmark_eligible") is True:
            errors.append(f"{result_path}: current-home smoke result cannot be benchmark_eligible")
        if result.get("auth_policy") == "current-home-full" and result.get("benchmark_eligible") is True:
            errors.append(f"{result_path}: current-home-full result cannot be benchmark_eligible")
        errors.extend(f"{result_path}: {error}" for error in _result_environment_errors(result))
    return errors


def validate_summary(summary_path: Path, *, publishable: bool = True) -> list[str]:
    """Validate a summary JSON used by scorecard/public reporting."""
    summary = read_json(summary_path)
    if not isinstance(summary, dict):
        return [f"{summary_path} missing or invalid"]
    errors = validate_required_fields(summary, "summary")
    if int(summary.get("schema_version", 0) or 0) < 2:
        errors.append("summary schema_version must be at least 2")
    errors.extend(scan_forbidden_secrets(summary_path))
    errors.extend(scan_forbidden_absolute_user_paths(summary_path))
    if summary.get("evidence_level") not in {LIVE_EVIDENCE_LEVEL, CURRENT_HOME_SMOKE_EVIDENCE_LEVEL}:
        errors.append(f"summary evidence_level must be {LIVE_EVIDENCE_LEVEL} or {CURRENT_HOME_SMOKE_EVIDENCE_LEVEL}")
    evidence_scope = summary.get("evidence_scope")
    if evidence_scope not in CODEX_LIVE_EVIDENCE_SCOPES:
        errors.append(f"summary evidence_scope must be one of {', '.join(CODEX_LIVE_EVIDENCE_SCOPES)}")
    detail = summary.get("evidence_scope_detail")
    if not isinstance(detail, dict):
        errors.append("summary evidence_scope_detail must be an object")
    elif evidence_scope == "multi_case_ablation_3_run" and detail.get("evidence_scope_ready") is not True:
        errors.append("summary evidence_scope multi_case_ablation_3_run requires evidence_scope_ready=true")
    elif evidence_scope == "smoke" and detail.get("evidence_scope_ready") is True:
        errors.append("summary evidence_scope smoke conflicts with evidence_scope_ready=true")
    if publishable:
        errors.extend(_strict_summary_errors(summary))
    if "limitations" not in summary or not summary.get("limitations"):
        errors.append("summary limitations are required")
    errors.extend(_variant_rate_errors(summary))
    errors.extend(_summary_structure_errors(summary))
    return errors


def _strict_summary_errors(summary: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    benchmark_mode = summary.get("benchmark_mode")
    if summary.get("status") in {"not_collected", "skipped_not_opted_in"}:
        errors.append("dry-run, skipped, or not-collected summaries cannot be published")
    if benchmark_mode not in STRICT_BENCHMARK_MODES:
        errors.append("strict summary must use clean-paired or ablation benchmark_mode")
    if summary.get("evidence_level") != LIVE_EVIDENCE_LEVEL:
        errors.append(f"strict summary evidence_level must be {LIVE_EVIDENCE_LEVEL}")
    if summary.get("auth_policy") not in STRICT_AUTH_POLICIES:
        errors.append("strict summary auth_policy must be borrow-current or isolated-api-key")
    if summary.get("codex_environment_policy") not in STRICT_CODEX_ENVIRONMENT_POLICIES:
        errors.append("strict summary codex_environment_policy must be auth_borrowed_clean or isolated_api_key")
    if summary.get("strict_benchmark_eligible") is not True:
        errors.append("strict summary requires strict_benchmark_eligible=true")
    if int(summary.get("current_home_result_count", 0) or 0) != 0 or int(
        summary.get("current_home_full_result_count", 0) or 0
    ) != 0:
        errors.append("strict summary must not include current-home-full results")
    if summary.get("user_skills_visible") is not False:
        errors.append("strict summary requires user_skills_visible=false")
    if summary.get("user_config_loaded") is not False:
        errors.append("strict summary requires user_config_loaded=false")
    if summary.get("user_rules_loaded") is not False:
        errors.append("strict summary requires user_rules_loaded=false")
    if summary.get("ignore_user_config") is not True or summary.get("ignore_rules") is not True:
        errors.append("strict summary requires --ignore-user-config and --ignore-rules")
    if summary.get("plugins_disabled") is not True:
        errors.append("strict summary requires --disable plugins")
    if summary.get("user_level_install_used") is not False:
        errors.append("strict summary requires user_level_install_used=false")
    if summary.get("changeforge_install_source") != "current_repository":
        errors.append("strict summary requires changeforge_install_source=current_repository")
    if int(summary.get("contaminated_result_count", 0) or 0) != 0:
        errors.append("strict summary must not include contaminated results")
    if int(summary.get("benchmark_eligible_result_count", 0) or 0) <= 0:
        errors.append("strict summary requires assertion-backed eligible results")
    if summary.get("effect_verdict") == "positive" and summary.get("dominant_setup_failure_reason") == "unknown":
        errors.append("strict summary cannot claim positive effect while unknown setup failures dominate")
    if summary.get("dominant_setup_failure_subreason") not in SETUP_FAILURE_SUBREASONS:
        errors.append("dominant_setup_failure_subreason is required")
    variants = summary.get("variants")
    delta = summary.get("delta")
    if not isinstance(variants, dict) or not variants:
        errors.append("strict summary requires grouped variants")
        variants = {}
    if not isinstance(delta, dict):
        errors.append("strict summary requires delta object")
        delta = {}
    for variant in MODE_DEFAULT_VARIANTS.get(str(benchmark_mode), ()):
        variant_summary = variants.get(variant) if isinstance(variants, dict) else None
        if not isinstance(variant_summary, dict):
            errors.append(f"strict summary missing variant {variant}")
            continue
        if int(variant_summary.get("benchmark_eligible_result_count", 0) or 0) <= 0:
            errors.append(f"strict summary requires eligible assertion results for {variant}")
        if variant == "baseline_clean" and variant_summary.get("changeforge_install_source") != "none":
            errors.append("strict summary baseline_clean must not install ChangeForge")
        if variant == "skills_only_clean":
            if variant_summary.get("changeforge_install_source") != "current_repository":
                errors.append("strict summary skills_only_clean must use current_repository install source")
            if variant_summary.get("changeforge_hooks_enabled") is not False:
                errors.append("strict summary skills_only_clean must not enable ChangeForge hooks")
        if variant == "skills_with_hooks_clean":
            if variant_summary.get("changeforge_install_source") != "current_repository":
                errors.append("strict summary skills_with_hooks_clean must use current_repository install source")
            if variant_summary.get("changeforge_hooks_enabled") is not True:
                errors.append("strict summary skills_with_hooks_clean must enable project-level hooks")
        if variant_summary.get("user_level_install_used") is not False:
            errors.append(f"strict summary {variant} requires user_level_install_used=false")
    if benchmark_mode == "ablation":
        for key in (
            "skills_only_clean_vs_baseline_clean",
            "skills_with_hooks_clean_vs_skills_only_clean",
            "skills_with_hooks_clean_vs_baseline_clean",
        ):
            if key not in delta:
                errors.append(f"strict ablation summary requires delta.{key}")
    return errors


def _command_metadata_errors(command_payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if int(command_payload.get("schema_version", 0) or 0) < 2:
        errors.append("codex-command.redacted.json schema_version must be at least 2")
    for field in ("program", "args", "cwd", "auth_policy", "codex_environment_policy", "env"):
        if field not in command_payload:
            errors.append(f"codex-command.redacted.json missing {field}")
    env = command_payload.get("env")
    if isinstance(env, dict):
        for key, value in env.items():
            if isinstance(value, str) and ("/Users/" in value or "/home/" in value or "auth.json" in value):
                errors.append(f"codex-command.redacted.json env {key} is not redacted")
    else:
        errors.append("codex-command.redacted.json env must be an object")
    if command_payload.get("auth_policy") in STRICT_AUTH_POLICIES:
        command = command_payload.get("command")
        if not isinstance(command, list):
            command = [command_payload.get("program"), *(command_payload.get("args") or [])]
        if "--disable" not in command or "plugins" not in command:
            errors.append("strict codex command must include --disable plugins")
    return errors


def _result_environment_errors(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    environment = result.get("environment")
    if not isinstance(environment, dict):
        return ["environment must be an object"]
    auth_policy = result.get("auth_policy")
    if result.get("benchmark_mode") in STRICT_BENCHMARK_MODES and auth_policy in STRICT_AUTH_POLICIES:
        if environment.get("home") != "<temp>":
            errors.append("strict result HOME metadata must be <temp>")
        if environment.get("codex_home") not in {"<temp>", "<borrowed-current-auth>"}:
            errors.append("strict result CODEX_HOME metadata must be redacted")
        for flag in ("user_skills_visible", "user_config_loaded", "user_rules_loaded"):
            if environment.get(flag) is not False:
                errors.append(f"strict result requires {flag}=false")
        if environment.get("ignore_user_config") is not True or environment.get("ignore_rules") is not True:
            errors.append("strict result requires ignore_user_config=true and ignore_rules=true")
        if environment.get("plugins_disabled") is not True:
            errors.append("strict result requires plugins_disabled=true")
        if environment.get("auth_json_copied") is not False:
            errors.append("strict result must not copy auth.json")
        if result.get("user_level_install_used") is not False:
            errors.append("strict result requires user_level_install_used=false")
        variant = result.get("variant")
        if variant == "baseline_clean" and result.get("changeforge_install_source") != "none":
            errors.append("strict baseline_clean result must not install ChangeForge")
        if variant == "skills_only_clean":
            if result.get("changeforge_install_source") != "current_repository":
                errors.append("strict skills_only_clean result must use current_repository install source")
            if result.get("changeforge_hooks_enabled") is not False:
                errors.append("strict skills_only_clean result must not enable ChangeForge hooks")
        if variant == "skills_with_hooks_clean":
            if result.get("changeforge_install_source") != "current_repository":
                errors.append("strict skills_with_hooks_clean result must use current_repository install source")
            if result.get("changeforge_hooks_enabled") is not True:
                errors.append("strict skills_with_hooks_clean result must enable project-level hooks")
    if auth_policy == "current-home-full":
        if result.get("codex_environment_policy") != "current_home_full":
            errors.append("current-home-full result must use current_home_full environment policy")
        if environment.get("strict_benchmark_eligible") is not False:
            errors.append("current-home-full environment must not be strict eligible")
    return errors


def _variant_rate_errors(summary: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    variants = summary.get("variants")
    if not isinstance(variants, dict):
        return errors
    for variant, variant_summary in variants.items():
        if not isinstance(variant_summary, dict):
            errors.append(f"variant {variant}: summary must be an object")
            continue
        eligible = int(variant_summary.get("benchmark_eligible_result_count", 0) or 0)
        pass_rate = variant_summary.get("pass_rate")
        if eligible == 0 and pass_rate != "not_collected":
            errors.append(f"variant {variant}: pass_rate must be not_collected when no eligible results exist")
        if eligible > 0 and not isinstance(pass_rate, int | float):
            errors.append(f"variant {variant}: pass_rate must be numeric when eligible results exist")
    return errors


def _summary_structure_errors(summary: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(_failure_category_errors("summary.failure_categories", summary.get("failure_categories")))
    dominant_failure_category = summary.get("dominant_failure_category")
    if dominant_failure_category is not None and dominant_failure_category not in FAILURE_CATEGORIES:
        errors.append("summary dominant_failure_category is invalid")
    errors.extend(_setup_diagnostic_summary_errors("summary", summary))
    errors.extend(
        _reason_bucket_errors(
            "summary.setup_failure_reasons",
            summary.get("setup_failure_reasons"),
            SETUP_FAILURE_REASONS,
        )
    )
    errors.extend(
        _reason_bucket_errors(
            "summary.setup_failure_subreasons",
            summary.get("setup_failure_subreasons"),
            SETUP_FAILURE_SUBREASONS,
        )
    )
    errors.extend(
        _reason_bucket_errors(
            "summary.test_suite_failure_reasons",
            summary.get("test_suite_failure_reasons"),
            TEST_SUITE_FAILURE_REASONS,
        )
    )
    errors.extend(
        _reason_bucket_errors(
            "summary.security_failure_reasons",
            summary.get("security_failure_reasons"),
            SECURITY_FAILURE_REASONS,
        )
    )
    if summary.get("effect_verdict") not in EFFECT_VERDICTS:
        errors.append("summary effect_verdict is invalid")
    if summary.get("effect_status") not in EFFECT_STATUSES:
        errors.append("summary effect_status is invalid")
    if not isinstance(summary.get("effect_summary"), dict):
        errors.append("summary effect_summary must be an object")
    else:
        errors.extend(_setup_diagnostic_summary_errors("summary.effect_summary", summary["effect_summary"]))
    variants = summary.get("variants")
    if not isinstance(variants, dict):
        errors.append("summary variants must be an object")
    else:
        for variant, payload in variants.items():
            if not isinstance(payload, dict):
                errors.append(f"variant {variant}: summary must be an object")
                continue
            for field in (
                "run_count",
                "case_count",
                "result_count",
                "benchmark_eligible_result_count",
                "benchmark_passed_result_count",
                "telemetry_only_result_count",
                "not_collected_grading_count",
                "contaminated_result_count",
            ):
                if not isinstance(payload.get(field), int):
                    errors.append(f"variant {variant}: {field} must be an integer")
            for field in (
                "average_usage",
                "median_usage",
                "min_usage",
                "max_usage",
                "average_metrics",
                "median_metrics",
                "min_metrics",
                "max_metrics",
            ):
                if not isinstance(payload.get(field), dict):
                    errors.append(f"variant {variant}: {field} must be an object")
            if not isinstance(payload.get("pass_rate_ci_note"), str):
                errors.append(f"variant {variant}: pass_rate_ci_note must be a string")
            errors.extend(_setup_diagnostic_summary_errors(f"variant {variant}", payload))
            errors.extend(_failure_category_errors(f"variant {variant}.failure_categories", payload.get("failure_categories")))
            errors.extend(
                _reason_bucket_errors(
                    f"variant {variant}.setup_failure_reasons",
                    payload.get("setup_failure_reasons"),
                    SETUP_FAILURE_REASONS,
                )
            )
            errors.extend(
                _reason_bucket_errors(
                    f"variant {variant}.setup_failure_subreasons",
                    payload.get("setup_failure_subreasons"),
                    SETUP_FAILURE_SUBREASONS,
                )
            )
            errors.extend(
                _reason_bucket_errors(
                    f"variant {variant}.test_suite_failure_reasons",
                    payload.get("test_suite_failure_reasons"),
                    TEST_SUITE_FAILURE_REASONS,
                )
            )
            errors.extend(
                _reason_bucket_errors(
                    f"variant {variant}.security_failure_reasons",
                    payload.get("security_failure_reasons"),
                    SECURITY_FAILURE_REASONS,
                )
            )
    cases_summary = summary.get("cases_summary")
    if not isinstance(cases_summary, dict):
        errors.append("summary cases_summary must be an object")
    else:
        for case_id, case_payload in cases_summary.items():
            if not isinstance(case_payload, dict):
                errors.append(f"case {case_id}: summary must be an object")
                continue
            if case_payload.get("grading_mode") not in {"assertion", "telemetry_only", "mixed"}:
                errors.append(f"case {case_id}: grading_mode must be assertion, telemetry_only, or mixed")
            errors.extend(_setup_diagnostic_summary_errors(f"case {case_id}", case_payload))
            errors.extend(
                _reason_bucket_errors(
                    f"case {case_id}.setup_failure_reasons",
                    case_payload.get("setup_failure_reasons"),
                    SETUP_FAILURE_REASONS,
                )
            )
            errors.extend(
                _reason_bucket_errors(
                    f"case {case_id}.setup_failure_subreasons",
                    case_payload.get("setup_failure_subreasons"),
                    SETUP_FAILURE_SUBREASONS,
                )
            )
            case_variants = case_payload.get("variants")
            if not isinstance(case_variants, dict):
                errors.append(f"case {case_id}: variants must be an object")
                continue
            for variant, variant_payload in case_variants.items():
                if not isinstance(variant_payload, dict):
                    errors.append(f"case {case_id} variant {variant}: summary must be an object")
                    continue
                for field in ("runs", "benchmark_eligible_result_count", "benchmark_passed_result_count"):
                    if not isinstance(variant_payload.get(field), int):
                        errors.append(f"case {case_id} variant {variant}: {field} must be an integer")
                pass_rate = variant_payload.get("pass_rate")
                if not (isinstance(pass_rate, int | float) or pass_rate == "not_collected"):
                    errors.append(f"case {case_id} variant {variant}: pass_rate must be numeric or not_collected")
                errors.extend(
                    _failure_category_errors(
                        f"case {case_id} variant {variant}.failure_categories",
                        variant_payload.get("failure_categories"),
                    )
                )
                errors.extend(
                    _reason_bucket_errors(
                        f"case {case_id} variant {variant}.setup_failure_reasons",
                        variant_payload.get("setup_failure_reasons"),
                        SETUP_FAILURE_REASONS,
                    )
                )
                errors.extend(
                    _reason_bucket_errors(
                        f"case {case_id} variant {variant}.setup_failure_subreasons",
                        variant_payload.get("setup_failure_subreasons"),
                        SETUP_FAILURE_SUBREASONS,
                    )
                )
                errors.extend(_setup_diagnostic_summary_errors(f"case {case_id} variant {variant}", variant_payload))
                errors.extend(
                    _reason_bucket_errors(
                        f"case {case_id} variant {variant}.test_suite_failure_reasons",
                        variant_payload.get("test_suite_failure_reasons"),
                        TEST_SUITE_FAILURE_REASONS,
                    )
                )
                errors.extend(
                    _reason_bucket_errors(
                        f"case {case_id} variant {variant}.security_failure_reasons",
                        variant_payload.get("security_failure_reasons"),
                        SECURITY_FAILURE_REASONS,
                    )
                )
    return errors


def _grading_result_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = (
        "setup_failure_reason",
        "setup_failure_subreason",
        "setup_contract",
        "test_suite_failure_reason",
        "security_failure_reason",
        "first_failure_stage",
        "first_failure_excerpt",
        "setup_log_excerpt",
        "test_suite_log_excerpt",
        "security_log_excerpt",
    )
    for field in required:
        if field not in payload:
            errors.append(f"grading-result missing {field}")
    reason_sets = {
        "setup_failure_reason": SETUP_FAILURE_REASONS,
        "setup_failure_subreason": SETUP_FAILURE_SUBREASONS,
        "test_suite_failure_reason": TEST_SUITE_FAILURE_REASONS,
        "security_failure_reason": SECURITY_FAILURE_REASONS,
    }
    for field, allowed in reason_sets.items():
        value = payload.get(field)
        if value is not None and value not in allowed:
            errors.append(f"grading-result invalid {field} {value}")
    first_failure_stage = payload.get("first_failure_stage")
    if first_failure_stage is not None and first_failure_stage not in FIRST_FAILURE_STAGES:
        errors.append(f"grading-result invalid first_failure_stage {first_failure_stage}")
    errors.extend(_setup_contract_errors("grading-result", payload.get("setup_contract")))
    errors.extend(_diagnostic_field_errors("grading-result", payload))
    return errors


def _diagnostic_field_errors(label: str, payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    forbidden = ("/Users/", "/home/", "C:\\Users\\", "auth.json", "CODEX_API_KEY", "OPENAI_API_KEY", "sk-")
    for field in (
        "first_failure_excerpt",
        "setup_log_excerpt",
        "test_suite_log_excerpt",
        "security_log_excerpt",
    ):
        value = payload.get(field)
        if value is None:
            continue
        if not isinstance(value, str):
            errors.append(f"{label}: {field} must be a string")
            continue
        if len(value) > 1200:
            errors.append(f"{label}: {field} must be bounded to 1200 characters")
        for marker in forbidden:
            if marker in value:
                errors.append(f"{label}: {field} contains unredacted marker {marker}")
    return errors


def _setup_diagnostic_summary_errors(label: str, payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    dominant = payload.get("dominant_setup_failure_reason")
    if dominant is not None and dominant not in SETUP_FAILURE_REASONS:
        errors.append(f"{label}: dominant_setup_failure_reason is invalid")
    subreason = payload.get("dominant_setup_failure_subreason")
    if subreason is None:
        errors.append(f"{label}: dominant_setup_failure_subreason is required")
    elif subreason not in SETUP_FAILURE_SUBREASONS:
        errors.append(f"{label}: dominant_setup_failure_subreason is invalid")
    rate = payload.get("unknown_setup_failure_rate")
    if rate is not None and not (isinstance(rate, int | float) and 0 <= float(rate) <= 1):
        errors.append(f"{label}: unknown_setup_failure_rate must be numeric between 0 and 1")
    return errors


def _setup_contract_errors(label: str, payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return [f"{label}: setup_contract must be an object"]
    errors: list[str] = []
    for field in SETUP_CONTRACT_FIELDS:
        if not isinstance(payload.get(field), bool):
            errors.append(f"{label}: setup_contract.{field} must be boolean")
    return errors


def _failure_category_errors(label: str, payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return [f"{label} must be an object"]
    errors: list[str] = []
    for category, count in payload.items():
        if category not in FAILURE_CATEGORIES:
            errors.append(f"{label}: invalid failure category {category}")
        if not isinstance(count, int) or count < 0:
            errors.append(f"{label}: count for {category} must be a non-negative integer")
    return errors


def _reason_bucket_errors(label: str, payload: Any, allowed: tuple[str, ...]) -> list[str]:
    if not isinstance(payload, dict):
        return [f"{label} must be an object"]
    errors: list[str] = []
    for reason, count in payload.items():
        if reason not in allowed:
            errors.append(f"{label}: invalid reason {reason}")
        if not isinstance(count, int) or count < 0:
            errors.append(f"{label}: count for {reason} must be a non-negative integer")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args(argv)
    if not args.run_dir and not args.summary:
        print("validate-codex-live-benchmark-reports: ERROR: --run-dir or --summary is required", file=sys.stderr)
        return 2
    errors: list[str] = []
    if args.run_dir:
        errors.extend(validate_run_dir(args.run_dir))
    if args.summary:
        errors.extend(validate_summary(args.summary))
    return print_errors("validate-codex-live-benchmark-reports", errors)


if __name__ == "__main__":
    sys.exit(main())
