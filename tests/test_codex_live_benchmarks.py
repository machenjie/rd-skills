from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _load_script(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _variant_payload(*, variant: str = "baseline_clean", **overrides: object) -> dict[str, object]:
    project_install = variant in {"skills_only_clean", "skills_with_hooks_clean"}
    usage = {
        "input_tokens": 10,
        "cached_input_tokens": 0,
        "output_tokens": 5,
        "reasoning_output_tokens": 0,
    }
    metrics = {
        "event_count": 1,
        "command_execution_count": 1,
        "file_change_count": 1,
        "plan_update_count": 0,
        "error_count": 0,
    }
    payload: dict[str, object] = {
        "run_count": 1,
        "case_count": 1,
        "result_count": 1,
        "changeforge_install_source": "current_repository" if project_install else "none",
        "changeforge_profile": "recommended" if project_install else "none",
        "changeforge_hooks_enabled": variant == "skills_with_hooks_clean",
        "user_level_install_used": False,
        "artifact_status_counts": {"collected": 1},
        "grading_status_counts": {"passed": 1},
        "failure_categories": {"none": 1},
        "setup_failure_reasons": {"none": 1},
        "dominant_setup_failure_reason": "none",
        "setup_failure_subreasons": {"none": 1},
        "dominant_setup_failure_subreason": "none",
        "unknown_setup_failure_rate": 0.0,
        "test_suite_failure_reasons": {"none": 1},
        "security_failure_reasons": {"none": 1},
        "benchmark_eligible_result_count": 1,
        "benchmark_passed_result_count": 1,
        "pass_rate": 1.0,
        "pass_rate_ci_note": "descriptive only; small sample",
        "security_pass_rate": 1.0,
        "security_assertion_failure_rate": 0.0,
        "security_check_execution_failure_rate": 0.0,
        "security_failure_rate": 0.0,
        "security_failure_rate_definition": "alias of security_assertion_failure_rate; execution failures are tracked separately",
        "telemetry_only_result_count": 0,
        "not_collected_grading_count": 0,
        "contaminated_result_count": 0,
        "average_usage": usage,
        "median_usage": usage,
        "min_usage": usage,
        "max_usage": usage,
        "average_metrics": metrics,
        "median_metrics": metrics,
        "min_metrics": metrics,
        "max_metrics": metrics,
        "average_event_count": 1,
        "average_file_change_count": 1,
        "average_command_execution_count": 1,
        "delta_vs_baseline_clean": {},
    }
    payload.update(overrides)
    return payload


def _scope_detail(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "evidence_scope_ready": False,
        "required_benchmark_mode": "ablation",
        "required_assertion_case_count": 5,
        "required_runs_per_variant": 3,
        "required_variants": ["baseline_clean", "skills_only_clean", "skills_with_hooks_clean"],
        "observed_benchmark_mode": "clean-paired",
        "observed_assertion_case_count": 1,
        "observed_variant_case_counts": {
            "baseline_clean": 1,
            "skills_only_clean": 0,
            "skills_with_hooks_clean": 1,
        },
        "observed_min_runs_per_required_variant": 0,
        "reason": "strict clean-paired evidence is smoke-scale until ablation covers the required cases and runs",
    }
    payload.update(overrides)
    return payload


def _process_summary(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "pdd_present_rate": 0.0,
        "ddd_present_rate": 0.0,
        "sdd_present_rate": 0.0,
        "tdd_present_rate": 0.0,
        "pdd_inferred_rate": 1.0,
        "ddd_inferred_rate": 1.0,
        "sdd_inferred_rate": 1.0,
        "tdd_inferred_rate": 1.0,
        "pdd_degraded_rate": 0.0,
        "ddd_degraded_rate": 0.0,
        "sdd_degraded_rate": 0.0,
        "tdd_degraded_rate": 0.0,
        "pdd_required_field_fallback_rate": 1.0,
        "ddd_required_field_fallback_rate": 1.0,
        "sdd_required_field_fallback_rate": 1.0,
        "tdd_required_field_fallback_rate": 1.0,
        "required_field_fallback_rate": 1.0,
        "all_core_phases_present_rate": 0.0,
        "all_core_phases_degraded_or_present_rate": 0.0,
        "all_core_phases_inferred_only_rate": 1.0,
        "process_trace_inferred_only_rate": 1.0,
        "pdd_to_tdd_traceability_rate": 1.0,
        "ddd_invariant_test_or_code_coverage_rate": 1.0,
        "sdd_public_api_validation_rate": 1.0,
        "sdd_failure_mode_validation_rate": 1.0,
        "sdd_logging_validation_rate": 1.0,
        "validation_command_present_rate": 1.0,
        "process_trace_count": 2,
    }
    payload.update(overrides)
    return payload


def _strict_summary_payload(**overrides: object) -> dict[str, object]:
    usage = {
        "input_tokens": 10,
        "cached_input_tokens": 0,
        "output_tokens": 5,
        "reasoning_output_tokens": 0,
    }
    payload: dict[str, object] = {
        "schema_version": 2,
        "generated_by": "scripts/generate-codex-live-summary.py",
        "status": "collected",
        "evidence_level": "local_codex_cli_live_benchmark",
        "evidence_scope": "smoke",
        "evidence_scope_ready": False,
        "evidence_scope_detail": _scope_detail(),
        "evidence_status": "pass",
        "effect_verdict": "inconclusive",
        "effect_status": "inconclusive",
        "effect_summary": {
            "required_variants": ["baseline_clean", "skills_only_clean", "skills_with_hooks_clean"],
            "missing_variants": ["skills_only_clean"],
            "eligible_result_counts": {
                "baseline_clean": 1,
                "skills_only_clean": 0,
                "skills_with_hooks_clean": 1,
            },
            "reason": "missing required ablation variants, repeated runs, or eligible assertion-backed results",
            "dominant_setup_failure_reason": "none",
            "dominant_setup_failure_subreason": "none",
            "setup_failure_subreasons": {"none": 1},
            "unknown_setup_failure_rate": 0.0,
        },
        "benchmark_mode": "clean-paired",
        "codex_home_policy": "auth_borrowed_clean",
        "auth_policy": "borrow-current",
        "codex_environment_policy": "auth_borrowed_clean",
        "changeforge_install_source": "current_repository",
        "changeforge_profile": "recommended",
        "changeforge_hooks_enabled": True,
        "user_level_install_used": False,
        "strict_benchmark_eligible": True,
        "publishable_for_strict_benchmark": True,
        "run_id": "local-test",
        "run_dir": "<run-dir>",
        "case_count": 1,
        "assertion_case_count": 1,
        "telemetry_only_case_count": 0,
        "result_count": 2,
        "benchmark_eligible_result_count": 2,
        "benchmark_passed_result_count": 2,
        "not_collected_grading_count": 0,
        "telemetry_only_result_count": 0,
        "contaminated_result_count": 0,
        "failure_categories": {"none": 2},
        "dominant_failure_category": "none",
        "setup_failure_reasons": {"none": 2},
        "dominant_setup_failure_reason": "none",
        "setup_failure_subreasons": {"none": 2},
        "dominant_setup_failure_subreason": "none",
        "unknown_setup_failure_rate": 0.0,
        "test_suite_failure_reasons": {"none": 2},
        "security_failure_reasons": {"none": 2},
        "current_home_result_count": 0,
        "current_home_full_result_count": 0,
        "user_skills_visible": False,
        "user_config_loaded": False,
        "user_rules_loaded": False,
        "ignore_user_config": True,
        "ignore_rules": True,
        "plugins_disabled": True,
        "variants": {
            "baseline_clean": _variant_payload(),
            "skills_with_hooks_clean": _variant_payload(
                variant="skills_with_hooks_clean",
                delta_vs_baseline_clean={
                    "pass_rate_delta": 0.0,
                    "security_pass_rate_delta": 0.0,
                }
            ),
        },
        "delta": {
            "skills_with_hooks_clean_vs_baseline_clean": {
                "pass_rate_delta": 0.0,
                "security_pass_rate_delta": 0.0,
            }
        },
        "cases": ["security/ssrf-url-allowlist"],
        "cases_summary": {
            "security/ssrf-url-allowlist": {
                "grading_mode": "assertion",
                "setup_failure_reasons": {"none": 2},
                "dominant_setup_failure_reason": "none",
                "setup_failure_subreasons": {"none": 2},
                "dominant_setup_failure_subreason": "none",
                "unknown_setup_failure_rate": 0.0,
                "variants": {
                    "baseline_clean": {
                        "runs": 1,
                        "benchmark_eligible_result_count": 1,
                        "benchmark_passed_result_count": 1,
                        "pass_rate": 1.0,
                        "failure_categories": {"none": 1},
                        "setup_failure_reasons": {"none": 1},
                        "dominant_setup_failure_reason": "none",
                        "setup_failure_subreasons": {"none": 1},
                        "dominant_setup_failure_subreason": "none",
                        "unknown_setup_failure_rate": 0.0,
                        "test_suite_failure_reasons": {"none": 1},
                        "security_failure_reasons": {"none": 1},
                    },
                    "skills_with_hooks_clean": {
                        "runs": 1,
                        "benchmark_eligible_result_count": 1,
                        "benchmark_passed_result_count": 1,
                        "pass_rate": 1.0,
                        "failure_categories": {"none": 1},
                        "setup_failure_reasons": {"none": 1},
                        "dominant_setup_failure_reason": "none",
                        "setup_failure_subreasons": {"none": 1},
                        "dominant_setup_failure_subreason": "none",
                        "unknown_setup_failure_rate": 0.0,
                        "test_suite_failure_reasons": {"none": 1},
                        "security_failure_reasons": {"none": 1},
                    },
                },
            }
        },
        "coverage_summary": {
            "case_count": 1,
            "assertion_case_count": 1,
            "telemetry_only_case_count": 0,
            "publishable_assertion_case_count": 1,
            "tiers": {"core": 1, "level1": 0, "experimental": 0},
            "categories": {"security": 1},
            "coverage_dimensions": {"security-ssrf": 1},
            "unregistered_case_count": 0,
            "manifest_category_count": 19,
            "manifest_case_count": 60,
            "manifest_categories": ["security"],
            "registered_live_case_count": 1,
            "registered_assertion_case_count": 1,
            "registered_telemetry_only_case_count": 0,
            "registered_publishable_assertion_case_count": 1,
            "registered_category_count": 1,
            "registered_case_coverage_rate": 0.0167,
            "registered_publishable_case_coverage_rate": 0.0167,
            "tiers_registered": {"core": 1, "level1": 0, "experimental": 0},
            "categories_registered": {"security": 1},
            "publishable_categories_registered": {"security": 1},
            "coverage_dimensions_registered": {"security-ssrf": 1},
            "actual_run_case_count": 1,
            "actual_run_assertion_case_count": 1,
            "actual_run_publishable_assertion_case_count": 1,
            "actual_run_category_count": 1,
            "actual_run_case_coverage_rate": 0.0167,
            "tiers_run": {"core": 1, "level1": 0, "experimental": 0},
            "categories_run": {"security": 1},
            "coverage_dimensions_run": {"security-ssrf": 1},
            "registered_but_not_run_cases": [],
            "missing_manifest_categories": [],
        },
        "cost_summary": {
            "result_count": 2,
            "total_usage": {
                "input_tokens": 20,
                "cached_input_tokens": 0,
                "output_tokens": 10,
                "reasoning_output_tokens": 0,
            },
            "average_usage_per_result": {
                "input_tokens": 10.0,
                "cached_input_tokens": 0.0,
                "output_tokens": 5.0,
                "reasoning_output_tokens": 0.0,
            },
            "by_variant": {
                "baseline_clean": {
                    "result_count": 1,
                    "total_usage": {
                        "input_tokens": 10,
                        "cached_input_tokens": 0,
                        "output_tokens": 5,
                        "reasoning_output_tokens": 0,
                    },
                    "average_usage_per_result": usage,
                    "median_usage_per_result": usage,
                    "pass_rate_per_100k_input_tokens": 10000.0,
                    "pass_rate_per_100_commands": 100.0,
                },
                "skills_with_hooks_clean": {
                    "result_count": 1,
                    "total_usage": {
                        "input_tokens": 10,
                        "cached_input_tokens": 0,
                        "output_tokens": 5,
                        "reasoning_output_tokens": 0,
                    },
                    "average_usage_per_result": usage,
                    "median_usage_per_result": usage,
                    "pass_rate_per_100k_input_tokens": 10000.0,
                    "pass_rate_per_100_commands": 100.0,
                },
            },
            "cost_adjusted_delta": {
                "skills_only_clean_vs_baseline_clean": {"status": "not_collected"},
                "skills_with_hooks_clean_vs_baseline_clean": {
                    "status": "collected",
                    "pass_rate_delta": 0.0,
                    "average_input_token_overhead_pct": 0.0,
                    "average_output_token_overhead_pct": 0.0,
                    "average_reasoning_token_overhead_pct": 0.0,
                    "average_command_execution_delta": 0.0,
                    "pass_rate_per_100k_input_tokens_delta": 0.0,
                    "pass_rate_per_100_commands_delta": 0.0,
                    "cost_efficiency_note": "fixture",
                },
                "skills_with_hooks_clean_vs_skills_only_clean": {"status": "not_collected"},
            },
            "case_cost_outliers": [],
            "cost_caveat": "Token usage is parsed local Codex telemetry, not a billing ledger.",
        },
        "stability_summary": {
            "requested_runs_per_variant": 1,
            "observed_case_variant_cell_count": 2,
            "observed_min_runs_per_case_variant": 1,
            "observed_max_runs_per_case_variant": 1,
            "artifact_status_counts": {"collected": 2},
            "grading_status_counts": {"passed": 2},
            "setup_failure_rate": 0.0,
            "test_suite_failure_rate": 0.0,
            "security_assertion_failure_rate": 0.0,
            "security_check_execution_failure_rate": 0.0,
            "security_failure_rate": 0.0,
            "security_failure_rate_definition": "alias of security_assertion_failure_rate; execution failures are tracked separately",
            "codex_exec_failure_rate": 0.0,
            "not_collected_grading_rate": 0.0,
            "contamination_rate": 0.0,
            "codex_exec_retry_count": 0,
            "codex_exec_failed_by_case": {},
            "codex_exec_retries_by_case": {},
            "failed_run_reasons_by_case": {},
            "flaky_case_variant_cells": [],
            "case_regression_count": 0,
            "skills_with_hooks_regression_cases": [],
            "partial_status_reasons": [],
        },
        "process_compliance_summary": _process_summary(),
        "telemetry": {"event_count": 2, "parse_error_count": 0},
        "limitations": ["strict local evidence"],
    }
    payload.update(overrides)
    return payload


def _strong_ablation_summary_payload(**overrides: object) -> dict[str, object]:
    cases = [
        "devex/helper-reuse-search",
        "structure/object-method-encapsulation-placement",
        "backend/service-method-vs-new-helper",
        "reliability/redis-cache-stampede-protection",
        "security/ssrf-url-allowlist",
    ]

    def variant_payload(variant: str, passed: int, pass_rate: float) -> dict[str, object]:
        return _variant_payload(
            variant=variant,
            run_count=3,
            case_count=5,
            result_count=15,
            artifact_status_counts={"collected": 15},
            grading_status_counts={"passed": passed, "failed": 15 - passed},
            failure_categories={"none": passed, "test_suite_failed": 15 - passed},
            setup_failure_reasons={"none": 15},
            setup_failure_subreasons={"none": 15},
            test_suite_failure_reasons={"none": passed, "assertion_failed": 15 - passed},
            security_failure_reasons={"none": 15},
            benchmark_eligible_result_count=15,
            benchmark_passed_result_count=passed,
            pass_rate=pass_rate,
            security_pass_rate=1.0,
            average_usage={
                "input_tokens": 100,
                "cached_input_tokens": 0,
                "output_tokens": 50,
                "reasoning_output_tokens": 5,
            },
            median_usage={
                "input_tokens": 100,
                "cached_input_tokens": 0,
                "output_tokens": 50,
                "reasoning_output_tokens": 5,
            },
            min_usage={
                "input_tokens": 100,
                "cached_input_tokens": 0,
                "output_tokens": 50,
                "reasoning_output_tokens": 5,
            },
            max_usage={
                "input_tokens": 100,
                "cached_input_tokens": 0,
                "output_tokens": 50,
                "reasoning_output_tokens": 5,
            },
        )

    payload = _strict_summary_payload(
        benchmark_mode="ablation",
        evidence_scope="multi_case_ablation_3_run",
        evidence_scope_ready=True,
        evidence_scope_detail=_scope_detail(
            evidence_scope_ready=True,
            observed_benchmark_mode="ablation",
            observed_assertion_case_count=5,
            observed_variant_case_counts={
                "baseline_clean": 5,
                "skills_only_clean": 5,
                "skills_with_hooks_clean": 5,
            },
            observed_min_runs_per_required_variant=3,
            reason="ablation evidence includes the required assertion-backed case count and repeated runs",
        ),
        effect_verdict="positive",
        effect_status="improved",
        effect_summary={
            "required_variants": ["baseline_clean", "skills_only_clean", "skills_with_hooks_clean"],
            "missing_variants": [],
            "eligible_result_counts": {
                "baseline_clean": 15,
                "skills_only_clean": 15,
                "skills_with_hooks_clean": 15,
            },
            "pass_rates": {
                "baseline_clean": 0.8,
                "skills_only_clean": 0.9333,
                "skills_with_hooks_clean": 1.0,
            },
            "reason": "skills_with_hooks_clean improved over baseline and skills_only_clean",
            "dominant_setup_failure_reason": "none",
            "dominant_setup_failure_subreason": "none",
            "setup_failure_subreasons": {"none": 45},
            "unknown_setup_failure_rate": 0.0,
        },
        case_count=5,
        assertion_case_count=5,
        result_count=45,
        benchmark_eligible_result_count=45,
        benchmark_passed_result_count=42,
        failure_categories={"none": 42, "test_suite_failed": 3},
        variants={
            "baseline_clean": variant_payload("baseline_clean", 12, 0.8),
            "skills_only_clean": variant_payload("skills_only_clean", 14, 0.9333),
            "skills_with_hooks_clean": variant_payload("skills_with_hooks_clean", 15, 1.0),
        },
        delta={
            "skills_only_clean_vs_baseline_clean": {"pass_rate_delta": 0.1333, "security_pass_rate_delta": 0.0},
            "skills_with_hooks_clean_vs_skills_only_clean": {
                "pass_rate_delta": 0.0667,
                "security_pass_rate_delta": 0.0,
            },
            "skills_with_hooks_clean_vs_baseline_clean": {"pass_rate_delta": 0.2, "security_pass_rate_delta": 0.0},
        },
        cases=cases,
        cases_summary={
            case_id: {
                "grading_mode": "assertion",
                "setup_failure_reasons": {"none": 9},
                "dominant_setup_failure_reason": "none",
                "setup_failure_subreasons": {"none": 9},
                "dominant_setup_failure_subreason": "none",
                "unknown_setup_failure_rate": 0.0,
                "variants": {
                    "baseline_clean": {
                        "runs": 3,
                        "benchmark_eligible_result_count": 3,
                        "benchmark_passed_result_count": 2,
                        "pass_rate": 0.6667,
                        "failure_categories": {"none": 2, "test_suite_failed": 1},
                        "setup_failure_reasons": {"none": 3},
                        "dominant_setup_failure_reason": "none",
                        "setup_failure_subreasons": {"none": 3},
                        "dominant_setup_failure_subreason": "none",
                        "unknown_setup_failure_rate": 0.0,
                        "test_suite_failure_reasons": {"none": 2, "assertion_failed": 1},
                        "security_failure_reasons": {"none": 3},
                    },
                    "skills_only_clean": {
                        "runs": 3,
                        "benchmark_eligible_result_count": 3,
                        "benchmark_passed_result_count": 3,
                        "pass_rate": 1.0,
                        "failure_categories": {"none": 3},
                        "setup_failure_reasons": {"none": 3},
                        "dominant_setup_failure_reason": "none",
                        "setup_failure_subreasons": {"none": 3},
                        "dominant_setup_failure_subreason": "none",
                        "unknown_setup_failure_rate": 0.0,
                        "test_suite_failure_reasons": {"none": 3},
                        "security_failure_reasons": {"none": 3},
                    },
                    "skills_with_hooks_clean": {
                        "runs": 3,
                        "benchmark_eligible_result_count": 3,
                        "benchmark_passed_result_count": 3,
                        "pass_rate": 1.0,
                        "failure_categories": {"none": 3},
                        "setup_failure_reasons": {"none": 3},
                        "dominant_setup_failure_reason": "none",
                        "setup_failure_subreasons": {"none": 3},
                        "dominant_setup_failure_subreason": "none",
                        "unknown_setup_failure_rate": 0.0,
                        "test_suite_failure_reasons": {"none": 3},
                        "security_failure_reasons": {"none": 3},
                    },
                },
            }
            for case_id in cases
        },
        coverage_summary={
            **_strict_summary_payload()["coverage_summary"],
            "case_count": 5,
            "assertion_case_count": 5,
            "publishable_assertion_case_count": 5,
            "actual_run_case_count": 5,
            "actual_run_assertion_case_count": 5,
            "actual_run_publishable_assertion_case_count": 5,
        },
        process_compliance_summary=_process_summary(
            pdd_present_rate=1.0,
            ddd_present_rate=1.0,
            sdd_present_rate=1.0,
            tdd_present_rate=1.0,
            pdd_inferred_rate=0.0,
            ddd_inferred_rate=0.0,
            sdd_inferred_rate=0.0,
            tdd_inferred_rate=0.0,
            pdd_required_field_fallback_rate=0.0,
            ddd_required_field_fallback_rate=0.0,
            sdd_required_field_fallback_rate=0.0,
            tdd_required_field_fallback_rate=0.0,
            required_field_fallback_rate=0.0,
            all_core_phases_present_rate=1.0,
            all_core_phases_inferred_only_rate=0.0,
            process_trace_inferred_only_rate=0.0,
            process_trace_count=45,
        ),
    )
    payload.update(overrides)
    return payload


def _codex_report_detail(summary: dict[str, object], *, status: str = "pass") -> dict[str, object]:
    variants = summary.get("variants")
    hooks = variants.get("skills_with_hooks_clean", {}) if isinstance(variants, dict) else {}
    return {
        "run_id": summary.get("run_id"),
        "evidence_status": status,
        "effect_verdict": summary.get("effect_verdict"),
        "benchmark_passed_result_count": summary.get("benchmark_passed_result_count"),
        "benchmark_eligible_result_count": summary.get("benchmark_eligible_result_count"),
        "variants": {
            "skills_with_hooks_clean": {
                "pass_rate": hooks.get("pass_rate") if isinstance(hooks, dict) else None,
            }
        },
    }


def _split_codex_live_items(
    summary: dict[str, object],
    *,
    pass_rate_status: str = "pass",
    capability_status: str = "partial",
    pass_rate_detail: dict[str, object] | None = None,
    capability_detail: dict[str, object] | None = None,
) -> list[dict[str, object]]:
    return [
        {
            "name": "Codex CLI live pass-rate benchmark",
            "status": pass_rate_status,
            "detail": json.dumps(pass_rate_detail or _codex_report_detail(summary, status=pass_rate_status)),
        },
        {
            "name": "Codex CLI live capability coverage",
            "status": capability_status,
            "detail": json.dumps(capability_detail or _codex_report_detail(summary, status=capability_status)),
        },
    ]


def _case_summary_payload(
    *,
    baseline_passed: int = 3,
    skills_only_passed: int = 3,
    hooks_passed: int = 3,
    eligible: int = 3,
) -> dict[str, object]:
    def variant_payload(variant: str, passed: int) -> dict[str, object]:
        return _variant_payload(
            variant=variant,
            run_count=eligible,
            result_count=eligible,
            benchmark_eligible_result_count=eligible,
            benchmark_passed_result_count=passed,
            pass_rate=round(passed / eligible, 4) if eligible else 0.0,
            artifact_status_counts={"collected": eligible},
            grading_status_counts={"passed": passed, "failed": eligible - passed},
            failure_categories={"none": passed, "test_suite_failed": eligible - passed},
            setup_failure_reasons={"none": eligible},
            setup_failure_subreasons={"none": eligible},
            test_suite_failure_reasons={"none": passed, "assertion_failed": eligible - passed},
            security_failure_reasons={"none": eligible},
        )

    return {
        "grading_mode": "assertion",
        "setup_failure_reasons": {"none": eligible * 3},
        "dominant_setup_failure_reason": "none",
        "setup_failure_subreasons": {"none": eligible * 3},
        "dominant_setup_failure_subreason": "none",
        "unknown_setup_failure_rate": 0.0,
        "variants": {
            "baseline_clean": variant_payload("baseline_clean", baseline_passed),
            "skills_only_clean": variant_payload("skills_only_clean", skills_only_passed),
            "skills_with_hooks_clean": variant_payload("skills_with_hooks_clean", hooks_passed),
        },
    }


def _write_profile_manifests(root: Path, counts: dict[str, int]) -> None:
    for profile, count in counts.items():
        path = root / "dist" / "universal" / "skills" / profile / ".changeforge-build-manifest.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"top_level_skills": [f"skill-{index}" for index in range(count)]}), encoding="utf-8")


def _environment_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "home": "<temp>",
        "codex_home": "<borrowed-current-auth>",
        "user_home_visible": False,
        "user_skills_visible": False,
        "user_config_loaded": False,
        "user_rules_loaded": False,
        "current_auth_borrowed": True,
        "ignore_user_config": True,
        "ignore_rules": True,
        "plugins_disabled": True,
        "auth_json_copied": False,
        "strict_benchmark_eligible": True,
    }
    payload.update(overrides)
    return payload


def _result_payload(**overrides: object) -> dict[str, object]:
    variant = str(overrides.get("variant", "baseline_clean"))
    project_install = variant in {"skills_only_clean", "skills_with_hooks_clean"}
    setup_contract = {
        "candidate_setup_exists": True,
        "candidate_setup_hash_changed": False,
        "candidate_setup_mentions_changeforge_codegen_root": True,
        "candidate_setup_uses_fixed_parent_traversal": False,
        "candidate_setup_invokes_codegen_harness": True,
    }
    payload: dict[str, object] = {
        "schema_version": 2,
        "generated_by": "scripts/run-codex-live-benchmarks.py",
        "case_id": "security/ssrf-url-allowlist",
        "variant": variant,
        "run_index": 1,
        "status": "collected",
        "artifact_status": "collected",
        "grading_status": "passed",
        "benchmark_mode": "clean-paired",
        "codex_home_mode": "isolated",
        "auth_policy": "borrow-current",
        "codex_environment_policy": "auth_borrowed_clean",
        "changeforge_install_source": "current_repository" if project_install else "none",
        "changeforge_profile": "recommended" if project_install else "none",
        "changeforge_hooks_enabled": variant == "skills_with_hooks_clean",
        "user_level_install_used": False,
        "grading_mode": "assertion",
        "publishable_for_strict": True,
        "benchmark_eligible": True,
        "benchmark_passed": True,
        "failure_category": "none",
        "setup_failure_reason": "none",
        "setup_failure_subreason": "none",
        "setup_contract": setup_contract,
        "test_suite_failure_reason": "none",
        "security_failure_reason": "none",
        "first_failure_stage": "none",
        "first_failure_excerpt": "",
        "setup_log_excerpt": "",
        "test_suite_log_excerpt": "",
        "security_log_excerpt": "",
        "contamination": {"contaminated": False, "signals": [], "files": []},
        "environment": _environment_payload(),
        "codex_returncode": 0,
        "failure": None,
        "paths": {"final": "<run-dir>/final.md"},
        "grading": {
            "all_passed": True,
            "setup_passed": True,
            "test_suite_passed": True,
            "security_checks_passed": True,
        },
        "metrics": {
            "event_count": 1,
            "command_execution_count": 1,
            "file_change_count": 1,
            "plan_update_count": 0,
            "error_count": 0,
            "usage": {
                "input_tokens": 10,
                "cached_input_tokens": 0,
                "output_tokens": 5,
                "reasoning_output_tokens": 0,
            },
            "parse_errors": [],
        },
        "limitations": ["local"],
    }
    payload.update(overrides)
    return payload


def _trace_value_present(value: object) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(_trace_value_present(item) for item in value)
    if isinstance(value, dict):
        return any(not str(key).startswith("_") and _trace_value_present(item) for key, item in value.items())
    return value is True or value not in {None, False}


def _with_process_field_sources(trace: dict[str, object], source: str = "final.md:compact-process-trace") -> dict[str, object]:
    facts = trace.get("process_facts")
    if not isinstance(facts, dict):
        return trace
    for phase in ("pdd", "ddd", "sdd", "tdd"):
        payload = facts.get(phase)
        if not isinstance(payload, dict):
            continue
        payload["_evidence_source"] = source
        payload["_field_sources"] = {
            str(field): source
            for field, value in payload.items()
            if not str(field).startswith("_") and _trace_value_present(value)
        }
        payload.setdefault("_inferred_fields", [])
    return trace


class CodexLiveBenchmarkTests(unittest.TestCase):
    def test_default_variants_for_clean_paired_ablation_and_smoke(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_defaults", "scripts/run-codex-live-benchmarks.py")
        self.assertEqual(
            runner.selected_variants(SimpleNamespace(benchmark_mode="clean-paired", variant=None)),
            ["baseline_clean", "skills_with_hooks_clean"],
        )
        self.assertEqual(
            runner.selected_variants(SimpleNamespace(benchmark_mode="ablation", variant=None)),
            ["baseline_clean", "skills_only_clean", "skills_with_hooks_clean"],
        )
        self.assertEqual(
            runner.selected_variants(SimpleNamespace(benchmark_mode="current-home-smoke", variant=None)),
            ["current_home_smoke"],
        )

    def test_default_auth_policy_is_borrow_current_for_strict_and_current_home_for_smoke(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_auth_defaults", "scripts/run-codex-live-benchmarks.py")
        self.assertEqual(runner.resolve_auth_policy(SimpleNamespace(benchmark_mode="clean-paired")), "borrow-current")
        self.assertEqual(runner.resolve_auth_policy(SimpleNamespace(benchmark_mode="ablation")), "borrow-current")
        self.assertEqual(
            runner.resolve_auth_policy(SimpleNamespace(benchmark_mode="current-home-smoke")),
            "current-home-full",
        )

    def test_borrow_current_uses_temp_home_and_redacted_current_auth(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_borrow_env", "scripts/run-codex-live-benchmarks.py")
        args = SimpleNamespace(auth_policy="borrow-current", benchmark_mode="clean-paired")
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            current_codex = Path(tmp) / "current-codex"
            current_codex.mkdir()
            (current_codex / "auth.json").write_text("{}", encoding="utf-8")
            with patch.dict("os.environ", {"HOME": "/Users/raw-home", "CODEX_HOME": str(current_codex)}, clear=True):
                env, metadata = runner.build_codex_environment(args, SimpleNamespace(id="x/y"), "baseline_clean", run_dir)
            borrowed_codex_home = Path(env["CODEX_HOME"])
            self.assertEqual(Path(env["HOME"]).name, "_home")
            self.assertNotEqual(borrowed_codex_home, current_codex)
            self.assertTrue(borrowed_codex_home.name.startswith("codex-live-borrowed-auth-"))
            self.assertTrue((borrowed_codex_home / "auth.json").is_symlink())
            self.assertFalse((borrowed_codex_home / "plugins").exists())
            runner._cleanup_borrowed_codex_home(env)
            self.assertFalse(borrowed_codex_home.exists())
        self.assertEqual(metadata["home"], "<temp>")
        self.assertEqual(metadata["codex_home"], "<borrowed-current-auth>")
        self.assertFalse(metadata["user_skills_visible"])
        self.assertFalse(metadata["user_config_loaded"])
        self.assertFalse(metadata["user_rules_loaded"])
        self.assertTrue(metadata["current_auth_borrowed"])
        self.assertTrue(metadata["ignore_user_config"])
        self.assertTrue(metadata["ignore_rules"])
        self.assertTrue(metadata["plugins_disabled"])

    def test_isolated_api_key_uses_temp_codex_home_and_redacts_secret_metadata(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_isolated_env", "scripts/run-codex-live-benchmarks.py")
        args = SimpleNamespace(auth_policy="isolated-api-key", benchmark_mode="clean-paired", codex_bin="codex", sandbox="workspace-write", model=None)
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            with patch.dict("os.environ", {"CODEX_API_KEY": "sk-raw-secret-value-12345"}, clear=True):
                env, metadata = runner.build_codex_environment(args, SimpleNamespace(id="x/y"), "baseline_clean", run_dir)
                command = runner.codex_command(args, run_dir / "final.md")
                command_metadata = runner._command_metadata(args, command, metadata)
        self.assertEqual(Path(env["HOME"]).name, "_home")
        self.assertEqual(Path(env["CODEX_HOME"]).name, "_codex-home")
        encoded = json.dumps(command_metadata) + json.dumps(metadata)
        self.assertNotIn("sk-raw-secret", encoded)
        self.assertEqual(command_metadata["env"]["CODEX_API_KEY"], "<redacted-if-present>")
        self.assertFalse(metadata["auth_json_copied"])

    def test_strict_codex_command_ignores_user_config_and_rules(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_command_flags", "scripts/run-codex-live-benchmarks.py")
        args = SimpleNamespace(
            auth_policy="borrow-current",
            benchmark_mode="clean-paired",
            codex_bin="codex",
            sandbox="workspace-write",
            model=None,
        )
        command = runner.codex_command(args, Path("/tmp/final.md"))
        self.assertIn("--ignore-user-config", command)
        self.assertIn("--ignore-rules", command)
        self.assertIn("--disable", command)
        self.assertIn("plugins", command)

    def test_current_home_full_is_only_valid_for_smoke_mode(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_current_mode", "scripts/run-codex-live-benchmarks.py")
        errors = runner.validate_mode_args(
            SimpleNamespace(
                benchmark_mode="clean-paired",
                auth_policy="current-home-full",
                codex_home_mode=None,
                publish_summary=False,
                publish_current_home_smoke=False,
            ),
            ["baseline_clean", "skills_with_hooks_clean"],
        )
        self.assertTrue(any("current-home-smoke" in error for error in errors))

    def test_current_home_full_requires_second_gate_for_live_runs(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_current_home_required", "scripts/run-codex-live-benchmarks.py")
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "current-home"
            with patch.dict("os.environ", {"CHANGEFORGE_ENABLE_CODEX_LIVE_BENCHMARK": "1"}):
                with patch.object(runner, "run_live") as run_live:
                    result = runner.main(
                        [
                            "--benchmark",
                            "security/ssrf-url-allowlist",
                            "--benchmark-mode",
                            "current-home-smoke",
                            "--auth-policy",
                            "current-home-full",
                            "--out",
                            str(out_dir),
                        ]
                    )
        self.assertEqual(result, 2)
        run_live.assert_not_called()

    def test_danger_full_access_still_requires_second_gate(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_danger_gate", "scripts/run-codex-live-benchmarks.py")
        result = runner.main(["--sandbox", "danger-full-access", "--dry-run"])
        self.assertEqual(result, 2)

    def test_live_execution_allowed_requires_env_or_cli_gate(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_allowed", "scripts/run-codex-live-benchmarks.py")
        args = SimpleNamespace(allow_live_codex=False)
        self.assertFalse(runner.live_execution_allowed(args, {}))
        self.assertTrue(runner.live_execution_allowed(args, {"CHANGEFORGE_ENABLE_CODEX_LIVE_BENCHMARK": "1"}))
        self.assertFalse(runner.live_execution_allowed(args, {"CHANGEFORGE_ENABLE_CODEX_LIVE_BENCHMARK": "true"}))
        self.assertTrue(runner.live_execution_allowed(SimpleNamespace(allow_live_codex=True), {}))

    def test_unauthorized_codex_exec_raises_before_subprocess(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_unauthorized", "scripts/run-codex-live-benchmarks.py")
        args = SimpleNamespace(allow_live_codex=False, dry_run=False, timeout_seconds=1)
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            with patch.object(runner.subprocess, "run") as subprocess_run:
                with self.assertRaisesRegex(RuntimeError, runner.REFUSAL_MESSAGE):
                    runner.run_codex_exec(
                        ["codex", "exec", "--json", "-"],
                        prompt="task",
                        cwd=tmp_path,
                        events_path=tmp_path / "events.jsonl",
                        stderr_path=tmp_path / "stderr.log",
                        args=args,
                        env={},
                    )
            subprocess_run.assert_not_called()

    def test_codex_exec_retries_empty_no_diff_failure_once(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_retry_empty_failure", "scripts/run-codex-live-benchmarks.py")
        args = SimpleNamespace(allow_live_codex=True, dry_run=False, timeout_seconds=1, codex_exec_retries=1)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = root / "candidate"
            candidate.mkdir()
            (candidate / "README.md").write_text("starter\n", encoding="utf-8")
            runner._init_git(candidate)
            support_dir = candidate / ".agents" / "skills" / "change-forge-router"
            support_dir.mkdir(parents=True)
            (support_dir / "SKILL.md").write_text("support artifact\n", encoding="utf-8")
            events_path = root / "events.jsonl"
            stderr_path = root / "stderr.log"
            final_path = root / "final.md"
            calls = []

            def fake_exec(command, *, prompt, cwd, events_path, stderr_path, args, env):
                del prompt, cwd, args, env
                calls.append(command)
                events_path.write_text('{"type": "turn.failed"}\n', encoding="utf-8")
                stderr_path.write_text("", encoding="utf-8")
                if len(calls) == 1:
                    return subprocess.CompletedProcess(command, 1, "", "")
                final_path.write_text("done\n", encoding="utf-8")
                return subprocess.CompletedProcess(command, 0, "", "")

            with patch.object(runner, "run_codex_exec", side_effect=fake_exec):
                completed, metadata = runner.run_codex_exec_with_retries(
                    ["codex", "exec"],
                    prompt="task",
                    cwd=candidate,
                    events_path=events_path,
                    stderr_path=stderr_path,
                    final_path=final_path,
                    args=args,
                    env={},
                )
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(len(calls), 2)
        self.assertEqual(metadata["codex_attempt_count"], 2)
        self.assertEqual(metadata["codex_retry_count"], 1)
        self.assertTrue(metadata["codex_exec_attempts"][0]["retried"])
        self.assertEqual(
            metadata["codex_exec_attempts"][0]["retry_reason"],
            "transient_no_output_no_candidate_changes",
        )

    def test_codex_exec_does_not_retry_after_candidate_changes(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_retry_changed_candidate", "scripts/run-codex-live-benchmarks.py")
        args = SimpleNamespace(allow_live_codex=True, dry_run=False, timeout_seconds=1, codex_exec_retries=1)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = root / "candidate"
            candidate.mkdir()
            (candidate / "README.md").write_text("starter\n", encoding="utf-8")
            runner._init_git(candidate)
            events_path = root / "events.jsonl"
            stderr_path = root / "stderr.log"
            final_path = root / "final.md"
            calls = []

            def fake_exec(command, *, prompt, cwd, events_path, stderr_path, args, env):
                del prompt, args, env
                calls.append(command)
                (cwd / "changed.txt").write_text("partial work\n", encoding="utf-8")
                events_path.write_text('{"type": "turn.failed"}\n', encoding="utf-8")
                stderr_path.write_text("", encoding="utf-8")
                return subprocess.CompletedProcess(command, 1, "", "")

            with patch.object(runner, "run_codex_exec", side_effect=fake_exec):
                completed, metadata = runner.run_codex_exec_with_retries(
                    ["codex", "exec"],
                    prompt="task",
                    cwd=candidate,
                    events_path=events_path,
                    stderr_path=stderr_path,
                    final_path=final_path,
                    args=args,
                    env={},
                )
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(len(calls), 1)
        self.assertEqual(metadata["codex_retry_count"], 0)
        self.assertEqual(metadata["codex_exec_attempts"][0]["retry_reason"], "candidate_changed")

    def test_codex_exec_idle_timeout_terminates_child(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_idle_timeout", "scripts/run-codex-live-benchmarks.py")
        args = SimpleNamespace(
            allow_live_codex=True,
            dry_run=False,
            timeout_seconds=100,
            codex_idle_timeout_seconds=1,
        )

        class FakeStdin:
            def __init__(self) -> None:
                self.writes: list[str] = []
                self.closed = False

            def write(self, text: str) -> None:
                self.writes.append(text)

            def close(self) -> None:
                self.closed = True

        class FakeProcess:
            def __init__(self) -> None:
                self.stdin = FakeStdin()
                self.terminated = False
                self.killed = False

            def poll(self):
                return None

            def terminate(self) -> None:
                self.terminated = True

            def wait(self, timeout=None):
                return -15

            def kill(self) -> None:
                self.killed = True

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            process = FakeProcess()
            with patch.object(runner.subprocess, "Popen", return_value=process):
                with patch.object(runner.time, "monotonic", side_effect=[0.0, 2.0]):
                    with patch.object(runner.time, "sleep") as sleep:
                        with self.assertRaises(runner.subprocess.TimeoutExpired):
                            runner.run_codex_exec(
                                ["codex", "exec", "--json", "-"],
                                prompt="task",
                                cwd=tmp_path,
                                events_path=tmp_path / "events.jsonl",
                                stderr_path=tmp_path / "stderr.log",
                                args=args,
                                env={},
                            )
        self.assertTrue(process.terminated)
        self.assertFalse(process.killed)
        self.assertEqual(process.stdin.writes, ["task"])
        self.assertTrue(process.stdin.closed)
        sleep.assert_not_called()

    def test_dry_run_has_priority_and_does_not_spawn_codex(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_dry_run", "scripts/run-codex-live-benchmarks.py")
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "dry-run"
            with patch.dict("os.environ", {"CHANGEFORGE_ENABLE_CODEX_LIVE_BENCHMARK": "1"}):
                with patch.object(runner.subprocess, "run") as subprocess_run:
                    result = runner.main(
                        [
                            "--benchmark",
                            "devex/helper-reuse-search",
                            "--dry-run",
                            "--out",
                            str(out_dir),
                        ]
                    )
            manifest = json.loads((out_dir / "run-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(result, 0)
        subprocess_run.assert_not_called()
        self.assertEqual(manifest["auth_policy"], "borrow-current")
        self.assertEqual(manifest["codex_environment_policy"], "auth_borrowed_clean")
        self.assertEqual(manifest["variants"], ["baseline_clean", "skills_with_hooks_clean"])
        self.assertFalse(manifest["live_execution_effective"])

    def test_prompt_mapping_keeps_baseline_clean_free_of_changeforge(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_prompts", "scripts/run-codex-live-benchmarks.py")
        with tempfile.TemporaryDirectory() as tmp:
            task = Path(tmp) / "task.md"
            task.write_text("Implement the requested change.\n", encoding="utf-8")
            case = SimpleNamespace(task_prompt=task)
            baseline = runner._render_prompt(case, "baseline_clean")
            skills = runner._render_prompt(case, "skills_only_clean")
        self.assertNotIn("ChangeForge", baseline)
        self.assertNotIn("rd-skills", baseline)
        self.assertIn("ChangeForge", skills)
        self.assertIn("Object-Method Encapsulation Decision", skills)
        self.assertIn("no side effects", skills)
        self.assertIn("before deadline", skills)
        self.assertIn("at deadline", skills)
        self.assertIn("after deadline", skills)
        self.assertIn("FakeBackend/source-of-truth seam", skills)
        self.assertIn("backend.calls == 1", skills)
        self.assertIn("live Redis", skills)
        self.assertIn("PaymentAdapter", skills)
        self.assertIn("refund_payment", skills)
        self.assertIn("domain/value object", skills)

    def test_backend_service_method_prompt_preserves_boundary_terms_for_assertions(self) -> None:
        prompt = (
            ROOT
            / "evals"
            / "codegen"
            / "backend"
            / "service-method-vs-new-helper"
            / "prompt.md"
        ).read_text(encoding="utf-8")
        self.assertIn("before deadline", prompt)
        self.assertIn("at deadline", prompt)
        self.assertIn("after deadline", prompt)
        self.assertIn("CamelCase", prompt)

    def test_object_method_prompt_preserves_payment_boundary_terms_for_assertions(self) -> None:
        prompt = (
            ROOT
            / "evals"
            / "codegen"
            / "structure"
            / "object-method-encapsulation-placement"
            / "prompt.md"
        ).read_text(encoding="utf-8")
        self.assertIn("orders/order.py", prompt)
        self.assertIn("PaymentAdapter", prompt)
        self.assertIn("payment provider", prompt)
        self.assertIn("refund_payment", prompt)
        self.assertIn("domain/value object", prompt)

    def test_redis_stampede_assertion_allows_markdown_network_requests_prose(self) -> None:
        assertion = (
            ROOT
            / "evals"
            / "codegen"
            / "reliability"
            / "redis-cache-stampede-protection"
            / "test-suite"
            / "tests"
            / "test_cache_stampede_protection.py"
        )
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp)
            (candidate / "README.md").write_text(
                "Redis outage degrades cleanly without external network requests.\n"
                "The cache key includes tenant, permission, and variant dimensions.\n"
                "Metrics cover hot keys, miss storms, fallback usage, and contention.\n",
                encoding="utf-8",
            )
            (candidate / "product_cache.py").write_text(
                "class ProductDetailCache:\n"
                "    def get(self):\n"
                "        # single-flight lock with ttl jitter and bounded timeout\n"
                "        return 'fallback'\n",
                encoding="utf-8",
            )
            tests_dir = candidate / "tests"
            tests_dir.mkdir()
            (tests_dir / "test_product_cache.py").write_text(
                "class FakeBackend:\n"
                "    calls = 0\n"
                "class InMemoryCache:\n"
                "    pass\n"
                "def test_redis_down_fallback_single_flight():\n"
                "    assert 'redis down fallback single flight only one concurrent lock'\n",
                encoding="utf-8",
            )
            env = dict(os.environ)
            env["CHANGEFORGE_CODEGEN_CANDIDATE_DIR"] = str(candidate)
            completed = subprocess.run(
                [sys.executable, str(assertion)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp)
            (candidate / "README.md").write_text(
                "Redis outage degrades cleanly with tenant permission variant cache keys.\n"
                "Metrics cover hot keys, miss storms, fallback usage, and contention.\n",
                encoding="utf-8",
            )
            (candidate / "product_cache.py").write_text(
                "import requests\n"
                "def get_product():\n"
                "    # single-flight lock with ttl jitter and bounded timeout\n"
                "    return requests.get('example')\n",
                encoding="utf-8",
            )
            tests_dir = candidate / "tests"
            tests_dir.mkdir()
            (tests_dir / "test_product_cache.py").write_text(
                "class FakeBackend:\n"
                "    calls = 0\n"
                "class InMemoryCache:\n"
                "    pass\n"
                "def test_redis_down_fallback_single_flight():\n"
                "    assert 'redis down fallback single flight only one concurrent lock'\n",
                encoding="utf-8",
            )
            env = dict(os.environ)
            env["CHANGEFORGE_CODEGEN_CANDIDATE_DIR"] = str(candidate)
            completed = subprocess.run(
                [sys.executable, str(assertion)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertNotEqual(completed.returncode, 0)

    def test_helper_reuse_assertion_accepts_existing_customer_as_normal_case(self) -> None:
        # Regression fixture for a live candidate that named the normal case as an existing customer label.
        assertion = (
            ROOT
            / "evals"
            / "codegen"
            / "devex"
            / "helper-reuse-search"
            / "test-suite"
            / "tests"
            / "test_helper_reuse_search.py"
        )
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp)
            docs_dir = candidate / "docs"
            docs_dir.mkdir()
            docs_dir.joinpath("execution-discipline-report.md").write_text(
                "Execution Discipline Report\n"
                "Implementation Structure Plan\n"
                "Reuse candidates: orderFormatter and customerFormatter.\n"
                "Validation command: npm test.\n",
                encoding="utf-8",
            )
            src = candidate / "src"
            (src / "orders" / "__tests__").mkdir(parents=True)
            (src / "customers").mkdir()
            (src / "shared").mkdir()
            (src / "orders" / "orderFormatter.ts").write_text(
                "export function formatOrderNumber(value: string): string { return value.trim(); }\n",
                encoding="utf-8",
            )
            (src / "customers" / "customerFormatter.ts").write_text(
                "export function formatCustomerLabel(value: string): string { return value.trim(); }\n",
                encoding="utf-8",
            )
            (src / "shared" / "stringUtils.ts").write_text(
                "export function normalizeWhitespace(value: string): string { return value.trim(); }\n",
                encoding="utf-8",
            )
            (src / "orders" / "__tests__" / "orderService.test.ts").write_text(
                'test("public order API formats display name with the existing customer label", () => {});\n'
                'test("public order API formats display name for a missing-customer order", () => {});\n'
                'test("public order API formats display name for an archived-order display case", () => {});\n',
                encoding="utf-8",
            )
            env = dict(os.environ)
            env["CHANGEFORGE_CODEGEN_CANDIDATE_DIR"] = str(candidate)
            completed = subprocess.run(
                [sys.executable, str(assertion)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_object_method_assertion_allows_rejected_anemic_object_prose(self) -> None:
        assertion = (
            ROOT
            / "evals"
            / "codegen"
            / "structure"
            / "object-method-encapsulation-placement"
            / "test-suite"
            / "tests"
            / "test_object_method_encapsulation_placement.py"
        )
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp)
            (candidate / "docs").mkdir()
            (candidate / "docs" / "review-note.md").write_text(
                "Object-Method Encapsulation Decision\n"
                "Object candidates include a value object and a domain object.\n"
                "Rejected: a helper bag and an anemic object.\n"
                "The value object owns a pure decision with no side effects.\n",
                encoding="utf-8",
            )
            (candidate / "orders").mkdir()
            (candidate / "orders" / "order.py").write_text(
                "class CancellationWindow:\n"
                "    def is_expired(self):\n"
                "        return False\n"
                "class Order:\n"
                "    def cancel(self):\n"
                "        self.cancelled = True\n",
                encoding="utf-8",
            )
            (candidate / "orders" / "payment_adapter.py").write_text(
                "class PaymentAdapter:\n"
                "    def refund(self):\n"
                "        return 'payment provider refund adapter'\n",
                encoding="utf-8",
            )
            tests_dir = candidate / "tests"
            tests_dir.mkdir()
            (tests_dir / "test_order_cancellation.py").write_text(
                "def test_allowed_denied_expired_refund_hold_payment_failure():\n"
                "    assert 'allowed denied expired refund hold payment failure'\n",
                encoding="utf-8",
            )
            env = dict(os.environ)
            env["CHANGEFORGE_CODEGEN_CANDIDATE_DIR"] = str(candidate)
            completed = subprocess.run(
                [sys.executable, str(assertion)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp)
            (candidate / "docs").mkdir()
            (candidate / "docs" / "review-note.md").write_text(
                "Object-Method Encapsulation Decision\n"
                "Object candidates include a value object and a domain object.\n"
                "Rejected alternatives are documented. Pure decision with no side effects.\n",
                encoding="utf-8",
            )
            (candidate / "orders").mkdir()
            (candidate / "orders" / "order.py").write_text(
                "class CancellationHelper:\n"
                "    pass\n",
                encoding="utf-8",
            )
            (candidate / "orders" / "payment_adapter.py").write_text(
                "class PaymentAdapter:\n"
                "    pass\n",
                encoding="utf-8",
            )
            tests_dir = candidate / "tests"
            tests_dir.mkdir()
            (tests_dir / "test_order_cancellation.py").write_text(
                "def test_allowed_denied_expired_refund_hold_payment_failure():\n"
                "    assert 'allowed denied expired refund hold payment failure'\n",
                encoding="utf-8",
            )
            env = dict(os.environ)
            env["CHANGEFORGE_CODEGEN_CANDIDATE_DIR"] = str(candidate)
            completed = subprocess.run(
                [sys.executable, str(assertion)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertNotEqual(completed.returncode, 0)

    def test_installer_variants_split_skills_only_and_hooks(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_install_flags", "scripts/run-codex-live-benchmarks.py")
        args = SimpleNamespace(profile="recommended")
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "candidate"
            candidate.mkdir()
            completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
            with patch.object(runner.subprocess, "run", return_value=completed) as subprocess_run:
                runner._install_changeforge(args, candidate, {}, set(), with_hooks=False)
            install_command = subprocess_run.call_args_list[-1].args[0]
            self.assertNotIn("--with-hooks", install_command)

            with patch.object(runner.subprocess, "run", return_value=completed) as subprocess_run:
                runner._install_changeforge(args, candidate, {}, {"recommended"}, with_hooks=True)
            install_command = subprocess_run.call_args_list[-1].args[0]
            self.assertIn("--with-hooks", install_command)

    def test_grading_removes_installed_changeforge_hook_support_artifacts(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_grading_isolation", "scripts/run-codex-live-benchmarks.py")
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "candidate"
            hook_dir = candidate / ".codex" / "hooks"
            hook_dir.mkdir(parents=True)
            (hook_dir / "changeforge_professional_injector.py").write_text(
                "raw hook runtime support\n",
                encoding="utf-8",
            )
            skill_dir = candidate / ".agents" / "skills" / "change-forge-router"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("installed skill support\n", encoding="utf-8")
            (candidate / "README.md").write_text("candidate solution\n", encoding="utf-8")

            runner._remove_changeforge_support_artifacts_for_grading(candidate)

            self.assertFalse((candidate / ".codex").exists())
            self.assertFalse((candidate / ".agents").exists())
            self.assertEqual((candidate / "README.md").read_text(encoding="utf-8"), "candidate solution\n")

    def test_strict_variant_metadata_records_current_repository_project_install(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_strict_metadata", "scripts/run-codex-live-benchmarks.py")
        args = SimpleNamespace(profile="recommended", auth_policy="borrow-current", benchmark_mode="ablation")
        self.assertEqual(
            runner._result_changeforge_metadata(args, "baseline_clean"),
            {
                "changeforge_install_source": "none",
                "changeforge_profile": "none",
                "changeforge_hooks_enabled": False,
                "user_level_install_used": False,
            },
        )
        self.assertEqual(
            runner._result_changeforge_metadata(args, "skills_only_clean"),
            {
                "changeforge_install_source": "current_repository",
                "changeforge_profile": "recommended",
                "changeforge_hooks_enabled": False,
                "user_level_install_used": False,
            },
        )
        self.assertEqual(
            runner._result_changeforge_metadata(args, "skills_with_hooks_clean"),
            {
                "changeforge_install_source": "current_repository",
                "changeforge_profile": "recommended",
                "changeforge_hooks_enabled": True,
                "user_level_install_used": False,
            },
        )

    def test_install_failure_writes_partial_result(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_install_partial", "scripts/run-codex-live-benchmarks.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            starter = root / "starter"
            starter.mkdir()
            (starter / "README.md").write_text("starter\n", encoding="utf-8")
            task = root / "task.md"
            task.write_text("Do the task.\n", encoding="utf-8")
            out_dir = root / "out"
            args = SimpleNamespace(
                profile="recommended",
                benchmark_mode="clean-paired",
                auth_policy="borrow-current",
                sandbox="workspace-write",
                model=None,
                codex_bin="codex",
                keep_workdirs=True,
            )
            case = SimpleNamespace(
                id="security/ssrf-url-allowlist",
                starter_repo=starter,
                task_prompt=task,
                grading_benchmark="security/ssrf-url-allowlist",
                grading_mode="assertion",
                publishable_for_strict=True,
            )
            with patch.object(runner, "build_codex_environment", return_value=({}, _environment_payload())):
                with patch.object(runner, "_install_changeforge", side_effect=RuntimeError("install failed")):
                    with patch.object(
                        runner,
                        "_grade",
                        return_value={
                            "all_passed": False,
                            "grading_status": "not_collected",
                            "security_checks_passed": False,
                        },
                    ):
                        result = runner._run_one_case(
                            args,
                            out_dir,
                            case,
                            "skills_with_hooks_clean",
                            1,
                            set(),
                        )
            result_path = (
                out_dir
                / "cases"
                / "security__ssrf-url-allowlist"
                / "skills_with_hooks_clean"
                / "run-01"
                / "result.json"
            )
            persisted = json.loads(result_path.read_text(encoding="utf-8"))
        self.assertEqual(result["artifact_status"], "partial")
        self.assertEqual(result["failure_stage"], "install_changeforge")
        self.assertFalse(result["benchmark_eligible"])
        self.assertFalse(result["benchmark_passed"])
        self.assertEqual(result["failure_category"], "install_failed")
        self.assertEqual(persisted["artifact_status"], "partial")
        self.assertEqual(persisted["failure_stage"], "install_changeforge")
        self.assertEqual(persisted["failure_category"], "install_failed")

    def test_generate_summary_failure_raises_for_publish(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_publish_failure", "scripts/run-codex-live-benchmarks.py")
        completed = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="publish failed")
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(runner.subprocess, "run", return_value=completed):
                with self.assertRaisesRegex(RuntimeError, "publish failed"):
                    runner._generate_summary(Path(tmp), publish=True, publish_current_home_smoke=False)

    def test_baseline_contamination_detector_finds_changeforge_route(self) -> None:
        helper = _load_script("codex_live_helper_contamination", "scripts/codex_live_benchmark_lib.py")
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "final.md").write_text("changeforge_route selected_skills", encoding="utf-8")
            result = helper.detect_baseline_contamination(run_dir)
        self.assertTrue(result["contaminated"])
        self.assertIn("changeforge_route", result["signals"])

    def test_baseline_contamination_detector_ignores_codegen_harness_env(self) -> None:
        helper = _load_script("codex_live_helper_harness_env", "scripts/codex_live_benchmark_lib.py")
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "diff.patch").write_text('ROOT="${CHANGEFORGE_CODEGEN_ROOT:-/tmp/root}"\n', encoding="utf-8")
            (run_dir / "final.md").write_text(
                "\n".join(
                    [
                        '`CHANGEFORGE_CODEGEN_CANDIDATE_DIR="$PWD" python3 test_helper.py` passed.',
                        "`CHANGEFORGE_CODEGEN_EVALUATE=1 bash ../test-suite/run.sh` could not run.",
                    ]
                ),
                encoding="utf-8",
            )
            result = helper.detect_baseline_contamination(run_dir)
        self.assertFalse(result["contaminated"])

    def test_baseline_contamination_detector_ignores_prompt_terms(self) -> None:
        helper = _load_script("codex_live_helper_prompt_terms", "scripts/codex_live_benchmark_lib.py")
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "prompt.md").write_text("Build rd-skills ChangeForge capability evidence.", encoding="utf-8")
            (run_dir / "final.md").write_text("Implemented bounded evidence without route leakage.", encoding="utf-8")
            result = helper.detect_baseline_contamination(run_dir)
        self.assertFalse(result["contaminated"])

    def test_report_redaction_handles_macos_temp_paths(self) -> None:
        helper = _load_script("codex_live_helper_report_redaction", "scripts/codex_live_benchmark_lib.py")
        text = "path=/private/var/folders/x/codex-live-borrowed-auth-abc/.tmp/plugin.json"
        self.assertNotIn("/private/var/", helper.redact_report_text(text))

    def test_publish_summary_rejects_current_home_full_and_contamination(self) -> None:
        summary_module = _load_script("generate_codex_live_summary_publish_rules", "scripts/generate-codex-live-summary.py")
        current_home = _strict_summary_payload(
            auth_policy="current-home-full",
            codex_environment_policy="current_home_full",
            current_home_full_result_count=1,
            strict_benchmark_eligible=False,
            user_skills_visible=True,
        )
        with self.assertRaisesRegex(ValueError, "current-home-full|auth_policy|strict_benchmark"):
            summary_module.publish_summary(current_home, "# current-home\n")
        contaminated = _strict_summary_payload(contaminated_result_count=1)
        with self.assertRaisesRegex(ValueError, "contaminated"):
            summary_module.publish_summary(contaminated, "# contaminated\n")

    def test_current_home_smoke_summary_is_not_strict_valid(self) -> None:
        validator = _load_script("validate_codex_live_reports_smoke", "scripts/validate-codex-live-benchmark-reports.py")
        payload = _strict_summary_payload(
            benchmark_mode="current-home-smoke",
            evidence_level="current_home_integration_smoke",
            codex_home_policy="current_home_smoke_only",
            auth_policy="current-home-full",
            codex_environment_policy="current_home_full",
            strict_benchmark_eligible=False,
            publishable_for_strict_benchmark=False,
            current_home_result_count=1,
            current_home_full_result_count=1,
            user_skills_visible=True,
            user_config_loaded=True,
            user_rules_loaded=True,
            ignore_user_config=False,
            ignore_rules=False,
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            errors = validator.validate_summary(path, publishable=True)
        self.assertTrue(any("strict summary" in error or "evidence_level" in error for error in errors))

    def test_strict_validator_rejects_user_level_install_metadata(self) -> None:
        validator = _load_script(
            "validate_codex_live_reports_strict_metadata",
            "scripts/validate-codex-live-benchmark-reports.py",
        )
        result_errors = validator._result_environment_errors(
            _result_payload(user_level_install_used=True)
        )
        summary_errors = validator._strict_summary_errors(
            _strict_summary_payload(user_level_install_used=True)
        )
        self.assertTrue(any("user_level_install_used=false" in error for error in result_errors))
        self.assertTrue(any("user_level_install_used=false" in error for error in summary_errors))

    def test_validator_rejects_ablation_summary_without_required_deltas(self) -> None:
        validator = _load_script(
            "validate_codex_live_reports_ablation_delta",
            "scripts/validate-codex-live-benchmark-reports.py",
        )
        payload = _strict_summary_payload(
            benchmark_mode="ablation",
            result_count=3,
            benchmark_eligible_result_count=3,
            benchmark_passed_result_count=3,
            failure_categories={"none": 3},
            variants={
                "baseline_clean": _variant_payload(),
                "skills_only_clean": _variant_payload(variant="skills_only_clean"),
                "skills_with_hooks_clean": _variant_payload(variant="skills_with_hooks_clean"),
            },
            delta={
                "skills_only_clean_vs_baseline_clean": {"pass_rate_delta": 0.0},
                "skills_with_hooks_clean_vs_baseline_clean": {"pass_rate_delta": 0.0},
            },
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            errors = validator.validate_summary(path, publishable=True)
        self.assertTrue(any("delta.skills_with_hooks_clean_vs_skills_only_clean" in error for error in errors))

    def test_validator_rejects_invalid_failure_category_buckets(self) -> None:
        validator = _load_script(
            "validate_codex_live_reports_failure_category",
            "scripts/validate-codex-live-benchmark-reports.py",
        )
        payload = _strict_summary_payload(failure_categories={"mystery_failure": 1})
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            errors = validator.validate_summary(path, publishable=True)
        self.assertTrue(any("invalid failure category mystery_failure" in error for error in errors))

    def test_summary_counts_assertion_cases_only_for_pass_rate_and_groups_delta(self) -> None:
        summary_module = _load_script("generate_codex_live_summary_rates", "scripts/generate-codex-live-summary.py")
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "run-manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "generated_by": "scripts/run-codex-live-benchmarks.py",
                        "run_id": "local-test",
                        "status": "collected",
                        "benchmark_mode": "clean-paired",
                        "dry_run": False,
                        "live_execution_allowed": True,
                        "live_execution_effective": True,
                        "cases": ["security/ssrf-url-allowlist"],
                        "variants": ["baseline_clean", "skills_with_hooks_clean"],
                        "runs_per_variant": 1,
                        "sandbox": "workspace-write",
                        "auth_policy": "borrow-current",
                        "codex_environment_policy": "auth_borrowed_clean",
                        "limitations": ["local"],
                    }
                ),
                encoding="utf-8",
            )
            base = run_dir / "cases" / "security__ssrf-url-allowlist" / "baseline_clean" / "run-01"
            skill = run_dir / "cases" / "security__ssrf-url-allowlist" / "skills_with_hooks_clean" / "run-01"
            base.mkdir(parents=True)
            skill.mkdir(parents=True)
            (base / "result.json").write_text(
                json.dumps(
                    _result_payload(
                        case_id="devex/helper-reuse-search",
                        grading_status="telemetry_only",
                        grading_mode="telemetry_only",
                        publishable_for_strict=False,
                        benchmark_eligible=False,
                        benchmark_passed=False,
                    )
                ),
                encoding="utf-8",
            )
            (skill / "result.json").write_text(
                json.dumps(_result_payload(variant="skills_with_hooks_clean")),
                encoding="utf-8",
            )
            summary = summary_module.generate_summary(run_dir)
        self.assertEqual(summary["variants"]["baseline_clean"]["pass_rate"], "not_collected")
        self.assertEqual(summary["variants"]["skills_with_hooks_clean"]["pass_rate"], 1.0)
        self.assertEqual(summary["assertion_case_count"], 1)
        self.assertEqual(summary["telemetry_only_case_count"], 1)
        self.assertIn("skills_with_hooks_clean_vs_baseline_clean", summary["delta"])
        self.assertEqual(summary["evidence_scope"], "smoke")
        self.assertEqual(summary["changeforge_install_source"], "current_repository")
        self.assertEqual(summary["changeforge_profile"], "recommended")
        self.assertTrue(summary["changeforge_hooks_enabled"])
        self.assertFalse(summary["user_level_install_used"])
        self.assertEqual(summary["variants"]["baseline_clean"]["changeforge_install_source"], "none")
        self.assertEqual(
            summary["variants"]["skills_with_hooks_clean"]["changeforge_install_source"],
            "current_repository",
        )
        self.assertTrue(summary["variants"]["skills_with_hooks_clean"]["changeforge_hooks_enabled"])
        self.assertFalse(summary["evidence_scope_detail"]["evidence_scope_ready"])
        self.assertEqual(summary["coverage_summary"]["case_count"], 2)
        self.assertEqual(summary["coverage_summary"]["tiers"]["core"], 2)
        self.assertEqual(summary["coverage_summary"]["assertion_case_count"], 1)
        self.assertEqual(summary["coverage_summary"]["telemetry_only_case_count"], 1)
        self.assertEqual(summary["coverage_summary"]["manifest_case_count"], 70)
        self.assertEqual(summary["coverage_summary"]["registered_live_case_count"], 23)
        self.assertEqual(summary["coverage_summary"]["registered_publishable_assertion_case_count"], 22)
        self.assertEqual(summary["coverage_summary"]["actual_run_case_count"], 2)
        self.assertEqual(summary["coverage_summary"]["tiers_registered"], {"core": 15, "experimental": 1, "level1": 7})
        self.assertEqual(summary["coverage_summary"]["actual_run_case_coverage_rate"], 0.0286)
        self.assertIn("frontend/accessible-form-error-state", summary["coverage_summary"]["registered_but_not_run_cases"])
        self.assertIn("delivery", summary["coverage_summary"]["missing_manifest_categories"])
        self.assertEqual(summary["cost_summary"]["total_usage"]["input_tokens"], 20)
        self.assertEqual(summary["cost_summary"]["total_usage"]["output_tokens"], 10)
        self.assertEqual(
            summary["cost_summary"]["by_variant"]["skills_with_hooks_clean"]["pass_rate_per_100k_input_tokens"],
            10000.0,
        )
        self.assertIn("skills_with_hooks_clean_vs_baseline_clean", summary["cost_summary"]["cost_adjusted_delta"])
        self.assertEqual(summary["stability_summary"]["observed_min_runs_per_case_variant"], 1)
        self.assertEqual(summary["stability_summary"]["test_suite_failure_rate"], 0.0)
        self.assertEqual(summary["stability_summary"]["codex_exec_retry_count"], 0)
        self.assertEqual(summary["stability_summary"]["failed_run_reasons_by_case"], {})
        self.assertTrue(any("smoke sample only" in item for item in summary["limitations"]))

    def test_summary_aggregates_ablation_runs_usage_cases_and_failure_categories(self) -> None:
        summary_module = _load_script("generate_codex_live_summary_ablation_stats", "scripts/generate-codex-live-summary.py")
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "run-manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "generated_by": "scripts/run-codex-live-benchmarks.py",
                        "run_id": "local-ablation",
                        "status": "collected",
                        "benchmark_mode": "ablation",
                        "dry_run": False,
                        "live_execution_allowed": True,
                        "live_execution_effective": True,
                        "cases": ["security/ssrf-url-allowlist"],
                        "variants": ["baseline_clean", "skills_only_clean", "skills_with_hooks_clean"],
                        "runs_per_variant": 3,
                        "sandbox": "workspace-write",
                        "auth_policy": "borrow-current",
                        "codex_environment_policy": "auth_borrowed_clean",
                        "limitations": ["local"],
                    }
                ),
                encoding="utf-8",
            )
            for variant, passed_runs in (
                ("baseline_clean", {3}),
                ("skills_only_clean", {1, 2, 3}),
                ("skills_with_hooks_clean", {1, 2, 3}),
            ):
                for run_index in range(1, 4):
                    result_dir = (
                        run_dir
                        / "cases"
                        / "security__ssrf-url-allowlist"
                        / variant
                        / f"run-{run_index:02d}"
                    )
                    result_dir.mkdir(parents=True)
                    passed = run_index in passed_runs
                    failure_category = "none" if passed else "test_suite_failed"
                    result = _result_payload(
                        variant=variant,
                        run_index=run_index,
                        grading_status="passed" if passed else "failed",
                        benchmark_passed=passed,
                        failure_category=failure_category,
                        grading={
                            "all_passed": passed,
                            "setup_passed": True,
                            "test_suite_passed": passed,
                            "security_checks_passed": True,
                        },
                    )
                    result["metrics"]["usage"]["input_tokens"] = run_index * 10
                    result["metrics"]["command_execution_count"] = run_index
                    (result_dir / "result.json").write_text(json.dumps(result), encoding="utf-8")
            summary = summary_module.generate_summary(run_dir)
        baseline = summary["variants"]["baseline_clean"]
        self.assertEqual(baseline["run_count"], 3)
        self.assertEqual(baseline["case_count"], 1)
        self.assertEqual(baseline["pass_rate"], 0.3333)
        self.assertEqual(baseline["failure_categories"], {"test_suite_failed": 2, "none": 1})
        self.assertEqual(baseline["average_usage"]["input_tokens"], 20.0)
        self.assertEqual(baseline["median_usage"]["input_tokens"], 20.0)
        self.assertEqual(baseline["min_usage"]["input_tokens"], 10)
        self.assertEqual(baseline["max_usage"]["input_tokens"], 30)
        self.assertIn("skills_only_clean_vs_baseline_clean", summary["delta"])
        self.assertIn("skills_with_hooks_clean_vs_skills_only_clean", summary["delta"])
        self.assertIn("skills_with_hooks_clean_vs_baseline_clean", summary["delta"])
        self.assertEqual(summary["evidence_scope"], "smoke")
        self.assertFalse(summary["evidence_scope_detail"]["evidence_scope_ready"])
        self.assertEqual(
            summary["cases_summary"]["security/ssrf-url-allowlist"]["variants"]["baseline_clean"]["pass_rate"],
            0.3333,
        )

    def test_summary_marks_strong_scope_only_for_five_case_three_run_ablation(self) -> None:
        summary_module = _load_script(
            "generate_codex_live_summary_strong_scope",
            "scripts/generate-codex-live-summary.py",
        )
        cases = [
            "devex/helper-reuse-search",
            "structure/object-method-encapsulation-placement",
            "backend/service-method-vs-new-helper",
            "reliability/redis-cache-stampede-protection",
            "security/ssrf-url-allowlist",
        ]
        variants = ["baseline_clean", "skills_only_clean", "skills_with_hooks_clean"]
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "run-manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "generated_by": "scripts/run-codex-live-benchmarks.py",
                        "run_id": "local-ablation",
                        "status": "collected",
                        "benchmark_mode": "ablation",
                        "dry_run": False,
                        "live_execution_allowed": True,
                        "live_execution_effective": True,
                        "cases": cases,
                        "variants": variants,
                        "runs_per_variant": 3,
                        "sandbox": "workspace-write",
                        "auth_policy": "borrow-current",
                        "codex_environment_policy": "auth_borrowed_clean",
                        "limitations": ["local"],
                    }
                ),
                encoding="utf-8",
            )
            # This synthetic matrix exercises scope classification only; it is not live Codex evidence.
            for case_id in cases:
                for variant in variants:
                    for run_index in range(1, 4):
                        result_dir = (
                            run_dir
                            / "cases"
                            / case_id.replace("/", "__")
                            / variant
                            / f"run-{run_index:02d}"
                        )
                        result_dir.mkdir(parents=True)
                        (result_dir / "result.json").write_text(
                            json.dumps(
                                _result_payload(
                                    case_id=case_id,
                                    variant=variant,
                                    run_index=run_index,
                                )
                            ),
                            encoding="utf-8",
                        )
            summary = summary_module.generate_summary(run_dir)

        self.assertEqual(summary["evidence_scope"], "multi_case_ablation_3_run")
        self.assertTrue(summary["evidence_scope_detail"]["evidence_scope_ready"])
        self.assertEqual(summary["evidence_scope_detail"]["observed_assertion_case_count"], 5)
        self.assertEqual(summary["evidence_scope_detail"]["observed_min_runs_per_required_variant"], 3)

    def test_summary_marks_negative_effect_when_setup_failures_dominate(self) -> None:
        summary_module = _load_script(
            "generate_codex_live_summary_effect_regression",
            "scripts/generate-codex-live-summary.py",
        )
        cases = [
            "devex/helper-reuse-search",
            "structure/object-method-encapsulation-placement",
            "backend/service-method-vs-new-helper",
            "reliability/redis-cache-stampede-protection",
            "security/ssrf-url-allowlist",
        ]
        variants = ["baseline_clean", "skills_only_clean", "skills_with_hooks_clean"]
        pass_budget = {"baseline_clean": 3, "skills_only_clean": 1, "skills_with_hooks_clean": 1}
        seen_by_variant = {variant: 0 for variant in variants}
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "run-manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "generated_by": "scripts/run-codex-live-benchmarks.py",
                        "run_id": "local-ablation",
                        "status": "collected",
                        "benchmark_mode": "ablation",
                        "dry_run": False,
                        "live_execution_allowed": True,
                        "live_execution_effective": True,
                        "cases": cases,
                        "variants": variants,
                        "runs_per_variant": 3,
                        "sandbox": "workspace-write",
                        "auth_policy": "borrow-current",
                        "codex_environment_policy": "auth_borrowed_clean",
                        "limitations": ["local"],
                    }
                ),
                encoding="utf-8",
            )
            for case_id in cases:
                for variant in variants:
                    for run_index in range(1, 4):
                        seen_by_variant[variant] += 1
                        passed = seen_by_variant[variant] <= pass_budget[variant]
                        result_dir = (
                            run_dir
                            / "cases"
                            / case_id.replace("/", "__")
                            / variant
                            / f"run-{run_index:02d}"
                        )
                        result_dir.mkdir(parents=True)
                        (result_dir / "result.json").write_text(
                            json.dumps(
                                _result_payload(
                                    case_id=case_id,
                                    variant=variant,
                                    run_index=run_index,
                                    grading_status="passed" if passed else "failed",
                                    benchmark_passed=passed,
                                    failure_category="none" if passed else "setup_failed",
                                    setup_failure_reason="none" if passed else "unknown",
                                    grading={
                                        "all_passed": passed,
                                        "setup_passed": passed,
                                        "test_suite_passed": True,
                                        "security_checks_passed": True,
                                    },
                                )
                            ),
                            encoding="utf-8",
                        )
            summary = summary_module.generate_summary(run_dir)
        self.assertEqual(summary["evidence_scope"], "multi_case_ablation_3_run")
        self.assertEqual(summary["effect_verdict"], "negative")
        self.assertEqual(summary["effect_status"], "regression")
        self.assertEqual(summary["failure_categories"], {"none": 5, "setup_failed": 40})
        self.assertEqual(summary["setup_failure_reasons"], {"none": 5, "unknown": 40})
        self.assertEqual(summary["setup_failure_subreasons"], {"none": 5, "unknown": 40})
        self.assertEqual(summary["dominant_failure_category"], "setup_failed")
        self.assertEqual(summary["dominant_setup_failure_reason"], "unknown")
        self.assertEqual(summary["dominant_setup_failure_subreason"], "unknown")
        self.assertEqual(summary["unknown_setup_failure_rate"], 1.0)
        self.assertTrue(any("Setup failure diagnostics remain incomplete" in item for item in summary["limitations"]))
        self.assertEqual(summary["effect_summary"]["dominant_failure_category"], "setup_failed")
        self.assertEqual(summary["effect_summary"]["dominant_setup_failure_reason"], "unknown")
        self.assertEqual(summary["effect_summary"]["dominant_setup_failure_subreason"], "unknown")

    def test_summary_classifies_historical_setup_logs_when_reason_was_unknown(self) -> None:
        summary_module = _load_script(
            "generate_codex_live_summary_setup_log_fallback",
            "scripts/generate-codex-live-summary.py",
        )
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "run-manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "generated_by": "scripts/run-codex-live-benchmarks.py",
                        "run_id": "local-ablation",
                        "status": "collected",
                        "benchmark_mode": "ablation",
                        "dry_run": False,
                        "live_execution_allowed": True,
                        "live_execution_effective": True,
                        "cases": ["backend/service-method-vs-new-helper"],
                        "variants": ["baseline_clean"],
                        "runs_per_variant": 1,
                        "sandbox": "workspace-write",
                        "auth_policy": "borrow-current",
                        "codex_environment_policy": "auth_borrowed_clean",
                        "limitations": ["local"],
                    }
                ),
                encoding="utf-8",
            )
            result_dir = run_dir / "cases" / "backend__service-method-vs-new-helper" / "baseline_clean" / "run-01"
            grading_dir = result_dir / "grading"
            grading_dir.mkdir(parents=True)
            (result_dir / "result.json").write_text(
                json.dumps(
                    _result_payload(
                        case_id="backend/service-method-vs-new-helper",
                        grading_status="failed",
                        benchmark_passed=False,
                        failure_category="setup_failed",
                        setup_failure_reason="unknown",
                        grading={"all_passed": False, "setup_passed": False},
                    )
                ),
                encoding="utf-8",
            )
            (grading_dir / "setup.log").write_text(
                "python3: can't open file '<candidate>/../../../../../scripts/codegen_benchmark_harness.py': "
                "No such file\n",
                encoding="utf-8",
            )
            summary = summary_module.generate_summary(run_dir)
        self.assertEqual(summary["setup_failure_reasons"], {"setup_script_modified_bad_path": 1})
        self.assertEqual(summary["setup_failure_subreasons"], {"starter_fragile_path": 1})
        self.assertEqual(summary["dominant_setup_failure_reason"], "setup_script_modified_bad_path")
        self.assertEqual(summary["dominant_setup_failure_subreason"], "starter_fragile_path")
        self.assertEqual(summary["unknown_setup_failure_rate"], 0.0)

    def test_failure_category_priority_is_stable(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_failure_category", "scripts/run-codex-live-benchmarks.py")
        self.assertEqual(
            runner._failure_category(
                artifact_status="partial",
                failure_stage="install_changeforge",
                codex_returncode=None,
                contamination={"contaminated": False},
                grading_status="not_collected",
                grading={},
                benchmark_passed=False,
            ),
            "install_failed",
        )
        normalized_status = runner._artifact_status_after_grading(
            artifact_status="failed",
            codex_returncode=1,
            grading_status="passed",
            grading={"all_passed": True},
        )
        self.assertEqual(normalized_status, "collected")
        self.assertEqual(
            runner._failure_category(
                artifact_status=normalized_status,
                failure_stage=None,
                codex_returncode=1,
                contamination={"contaminated": False},
                grading_status="passed",
                grading={"all_passed": True},
                benchmark_passed=True,
            ),
            "none",
        )
        self.assertEqual(
            runner._artifact_status_after_grading(
                artifact_status="failed",
                codex_returncode=1,
                grading_status="not_collected",
                grading={},
            ),
            "failed",
        )
        self.assertEqual(
            runner._failure_category(
                artifact_status="failed",
                failure_stage=None,
                codex_returncode=1,
                contamination={"contaminated": False},
                grading_status="failed",
                grading={},
                benchmark_passed=False,
            ),
            "codex_exec_failed",
        )
        self.assertEqual(
            runner._failure_category(
                artifact_status="collected",
                failure_stage=None,
                codex_returncode=0,
                contamination={"contaminated": True},
                grading_status="failed",
                grading={"test_suite_passed": False},
                benchmark_passed=False,
            ),
            "contaminated",
        )
        self.assertEqual(
            runner._failure_category(
                artifact_status="collected",
                failure_stage=None,
                codex_returncode=0,
                contamination={"contaminated": False},
                grading_status="failed",
                grading={"setup_passed": True, "test_suite_passed": False},
                benchmark_passed=False,
            ),
            "test_suite_failed",
        )

    def test_validator_rejects_secret_patterns_and_absolute_paths_but_not_raw_events(self) -> None:
        validator = _load_script("validate_codex_live_reports_secret", "scripts/validate-codex-live-benchmark-reports.py")
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "run-manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "generated_by": "scripts/run-codex-live-benchmarks.py",
                        "run_id": "dry-run",
                        "status": "skipped_not_opted_in",
                        "benchmark_mode": "clean-paired",
                        "dry_run": True,
                        "live_execution_allowed": False,
                        "live_execution_effective": False,
                        "cases": ["devex/helper-reuse-search"],
                        "variants": ["baseline_clean", "skills_with_hooks_clean"],
                        "runs_per_variant": 1,
                        "sandbox": "workspace-write",
                        "auth_policy": "borrow-current",
                        "codex_environment_policy": "auth_borrowed_clean",
                        "limitations": ["dry-run"],
                    }
                ),
                encoding="utf-8",
            )
            leak_dir = run_dir / "cases" / "devex__helper-reuse-search" / "baseline_clean" / "run-01"
            leak_dir.mkdir(parents=True)
            (leak_dir / "events.jsonl").write_text('{"path": "/Users/raw/events-only"}\n', encoding="utf-8")
            (leak_dir / "events.redacted.jsonl").write_text('{"path": "/Users/raw/redacted"}\n', encoding="utf-8")
            fake_secret = "CODEX" + "_API" + "_KEY=" + "sk-" + "ThisShouldFail123"
            (leak_dir / "result.json").write_text(fake_secret, encoding="utf-8")
            (leak_dir / "final.md").write_text("/Users/raw/final", encoding="utf-8")
            errors = validator.validate_run_dir(run_dir)
        self.assertTrue(any("forbidden secret pattern" in error for error in errors))
        self.assertTrue(any("absolute path" in error for error in errors))
        self.assertTrue(any("events.redacted.jsonl" in error for error in errors))
        self.assertFalse(any("events-only" in error for error in errors))

    def test_generated_summary_and_result_do_not_store_host_paths_or_auth_json(self) -> None:
        summary_module = _load_script("generate_codex_live_summary_no_paths", "scripts/generate-codex-live-summary.py")
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "run-manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "generated_by": "scripts/run-codex-live-benchmarks.py",
                        "run_id": "local-test",
                        "status": "collected",
                        "benchmark_mode": "clean-paired",
                        "dry_run": False,
                        "live_execution_allowed": True,
                        "live_execution_effective": True,
                        "cases": ["security/ssrf-url-allowlist"],
                        "variants": ["baseline_clean", "skills_with_hooks_clean"],
                        "runs_per_variant": 1,
                        "sandbox": "workspace-write",
                        "auth_policy": "borrow-current",
                        "codex_environment_policy": "auth_borrowed_clean",
                        "limitations": ["local"],
                    }
                ),
                encoding="utf-8",
            )
            result_dir = run_dir / "cases" / "security__ssrf-url-allowlist" / "baseline_clean" / "run-01"
            result_dir.mkdir(parents=True)
            result = _result_payload()
            (result_dir / "result.json").write_text(json.dumps(result), encoding="utf-8")
            summary = summary_module.generate_summary(run_dir)
        encoded = json.dumps(summary) + json.dumps(result)
        self.assertNotIn("/Users/", encoded)
        self.assertNotIn("/home/", encoded)
        self.assertNotIn("C:/Users", encoded)
        self.assertNotIn("auth.json", encoded)

    def test_auth_json_is_not_copied_to_run_artifacts(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_no_auth_copy", "scripts/run-codex-live-benchmarks.py")
        args = SimpleNamespace(auth_policy="borrow-current", benchmark_mode="clean-paired")
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            with patch.dict("os.environ", {"HOME": "/Users/raw-home", "CODEX_HOME": "/Users/raw-codex"}, clear=True):
                env, metadata = runner.build_codex_environment(args, SimpleNamespace(id="x/y"), "baseline_clean", run_dir)
            artifact_names = [path.name for path in run_dir.rglob("*")]
            runner._cleanup_borrowed_codex_home(env)
        self.assertFalse(metadata["auth_json_copied"])
        self.assertNotIn("auth.json", artifact_names)

    def test_parser_counts_usage_without_raw_command_or_message(self) -> None:
        parser = _load_script("parse_codex_jsonl_test", "scripts/parse-codex-jsonl.py")
        with tempfile.TemporaryDirectory() as tmp:
            events = Path(tmp) / "events.jsonl"
            events.write_text(
                "\n".join(
                    [
                        json.dumps({"type": "turn.started"}),
                        json.dumps({"type": "tool_call", "command": "echo SHOULD_NOT_LEAK", "usage": {"input_tokens": 10}}),
                        json.dumps({"type": "message", "role": "assistant", "message": "SHOULD_NOT_LEAK"}),
                        "{bad json",
                    ]
                ),
                encoding="utf-8",
            )
            metrics = parser.parse_events(events)
        self.assertEqual(metrics["event_count"], 3)
        self.assertEqual(metrics["command_execution_count"], 1)
        self.assertEqual(metrics["usage"]["input_tokens"], 10)
        self.assertNotIn("SHOULD_NOT_LEAK", json.dumps(metrics))
        self.assertEqual(len(metrics["parse_errors"]), 1)

    def test_parser_writes_bounded_redacted_events_without_raw_payloads(self) -> None:
        parser = _load_script("parse_codex_jsonl_redacted", "scripts/parse-codex-jsonl.py")
        with tempfile.TemporaryDirectory() as tmp:
            events = Path(tmp) / "events.jsonl"
            redacted = Path(tmp) / "events.redacted.jsonl"
            events.write_text(
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {
                            "type": "command_execution",
                            "status": "completed",
                            "command": "/bin/zsh -lc 'cat /Users/raw/secret.txt'",
                            "aggregated_output": "SHOULD_NOT_LEAK /Users/raw/project",
                            "usage": {"input_tokens": 10, "output_tokens": 5},
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            parser.write_redacted_events(events, redacted)
            text = redacted.read_text(encoding="utf-8")
        self.assertIn("command_execution", text)
        self.assertIn("input_tokens", text)
        self.assertNotIn("SHOULD_NOT_LEAK", text)
        self.assertNotIn("/Users/raw", text)

    def test_grader_marks_cases_without_assertions_not_collected_and_redacts_paths(self) -> None:
        grader = _load_script("grade_codex_live_redaction", "scripts/grade-codex-live-benchmarks.py")
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "candidate"
            out_dir = Path(tmp) / "grading"
            candidate.mkdir()
            result = grader.grade_candidate("devex/minimal-correct-implementation-ladder", candidate, out_dir)
            redacted = grader._redact_output(
                f"{candidate}/file.py {Path(tmp)}/other.py /private/var/folders/sample /tmp/sample",
                root=Path(tmp),
                candidate_dir=candidate,
            )
        self.assertEqual(result["grading_status"], "not_collected")
        self.assertEqual(result["candidate_dir"], "<candidate>")
        self.assertNotIn(str(candidate), redacted)
        self.assertNotIn(str(Path(tmp)), redacted)
        self.assertNotIn("/private/var/", redacted)
        self.assertNotIn("/tmp/", redacted)

    def test_grader_classifies_stage_failures_and_redacts_excerpts(self) -> None:
        grader = _load_script("grade_codex_live_stage_diagnostics", "scripts/grade-codex-live-benchmarks.py")
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="/Users/raw-home/.codex/auth.json CODEX_API_KEY=sk-ThisShouldBeRedacted12345\n",
            stderr=(
                "run-codegen-benchmarks: ERROR: security/ssrf-url-allowlist: setup exited 1\n"
                "python3: can't open file '/Users/raw/repo/scripts/codegen_benchmark_harness.py': No such file\n"
                "run-codegen-benchmarks: ERROR: security/ssrf-url-allowlist: assertion "
                "evals/codegen/security/ssrf-url-allowlist/test-suite/tests/test_behavior.py exited 1\n"
                "AssertionError: token=sk-AlsoRedacted12345\n"
            ),
        )
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "candidate"
            out_dir = Path(tmp) / "grading"
            candidate.mkdir()
            with patch.object(grader.subprocess, "run", return_value=completed):
                result = grader.grade_candidate("security/ssrf-url-allowlist", candidate, out_dir)
        self.assertFalse(result["setup_passed"])
        self.assertFalse(result["test_suite_passed"])
        self.assertTrue(result["security_checks_passed"])
        self.assertEqual(result["first_failure_stage"], "setup")
        self.assertEqual(result["setup_failure_reason"], "missing_harness")
        self.assertEqual(result["setup_failure_subreason"], "missing_harness")
        self.assertEqual(
            set(result["setup_contract"]),
            {
                "candidate_setup_exists",
                "candidate_setup_hash_changed",
                "candidate_setup_mentions_changeforge_codegen_root",
                "candidate_setup_uses_fixed_parent_traversal",
                "candidate_setup_invokes_codegen_harness",
            },
        )
        self.assertFalse(result["setup_contract"]["candidate_setup_exists"])
        self.assertEqual(result["test_suite_failure_reason"], "assertion_failed")
        encoded = json.dumps(result)
        self.assertNotIn("/Users/", encoded)
        self.assertNotIn("auth.json", encoded)
        self.assertNotIn("CODEX_API_KEY", encoded)
        self.assertNotIn("OPENAI_API_KEY", encoded)
        self.assertNotIn("sk-ThisShouldBeRedacted", encoded)
        self.assertLessEqual(len(result["first_failure_excerpt"]), 1200)

    def test_setup_failure_reason_classifier_covers_common_causes(self) -> None:
        grader = _load_script("grade_codex_live_setup_reason_classifier", "scripts/grade-codex-live-benchmarks.py")
        examples = {
            "missing_harness": "codegen_benchmark_harness.py: No such file",
            "missing_env_root": "could not locate scripts/codegen_benchmark_harness.py; set CHANGEFORGE_CODEGEN_ROOT",
            "setup_script_missing": "candidate/setup.sh missing",
            "setup_script_modified_bad_path": (
                "python3: can't open file '<candidate>/../../../../../scripts/codegen_benchmark_harness.py': "
                "No such file"
            ),
            "dependency_install_failed": "ModuleNotFoundError: No module named 'requests'",
            "python_compile_failed": "py_compile failed with SyntaxError",
            "candidate_removed_required_file": "candidate lacks required starter file README.md",
            "permission_denied": "bash: setup.sh: Permission denied",
            "shell_error": "bad interpreter: No such file or command not found",
            "unknown": "setup exited 1 with no recognizable diagnostic",
        }
        for expected, text in examples.items():
            with self.subTest(expected=expected):
                self.assertEqual(grader._setup_failure_reason(text, failed=True), expected)
        self.assertEqual(grader._setup_failure_reason("setup exited 1", failed=False), "none")
        self.assertEqual(
            grader._setup_failure_reason("AssertionError: external network dependency is not allowed", failed=True),
            "unknown",
        )
        self.assertEqual(
            grader._setup_failure_reason("Policy text mentions permission denied behavior", failed=True),
            "unknown",
        )

        fixed_path_contract = {
            "candidate_setup_exists": True,
            "candidate_setup_hash_changed": False,
            "candidate_setup_mentions_changeforge_codegen_root": False,
            "candidate_setup_uses_fixed_parent_traversal": True,
            "candidate_setup_invokes_codegen_harness": True,
        }
        modified_contract = dict(fixed_path_contract)
        modified_contract["candidate_setup_hash_changed"] = True
        self.assertEqual(
            grader._setup_failure_subreason(
                "../../../../../scripts/codegen_benchmark_harness.py: No such file",
                failed=True,
                setup_failure_reason="setup_script_modified_bad_path",
                setup_contract=fixed_path_contract,
            ),
            "starter_fragile_path",
        )
        self.assertEqual(
            grader._setup_failure_subreason(
                "../../../../../scripts/codegen_benchmark_harness.py: No such file",
                failed=True,
                setup_failure_reason="setup_script_modified_bad_path",
                setup_contract=modified_contract,
            ),
            "candidate_modified_setup",
        )
        self.assertEqual(
            grader._setup_failure_subreason(
                "CHANGEFORGE_CODEGEN_ROOT is unset",
                failed=True,
                setup_failure_reason="missing_env_root",
                setup_contract=fixed_path_contract,
            ),
            "missing_env_root",
        )

    def test_grader_does_not_classify_robust_setup_fallback_as_fragile_path(self) -> None:
        grader = _load_script("grade_codex_live_robust_setup_fallback", "scripts/grade-codex-live-benchmarks.py")
        helper = _load_script("codex_live_helper_robust_setup_fallback", "scripts/codex_live_benchmark_lib.py")
        case = next(
            case
            for case in helper.load_case_registry()
            if case.enabled and case.publishable_for_strict and case.grading_mode == "assertion"
        )
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "candidate"
            shutil.copytree(case.starter_repo, candidate)
            contract = grader._setup_contract(case.grading_benchmark, candidate, root=ROOT)
        text = "could not locate scripts/codegen_benchmark_harness.py; set CHANGEFORGE_CODEGEN_ROOT"
        reason = grader._setup_failure_reason(text, failed=True)
        subreason = grader._setup_failure_subreason(
            text,
            failed=True,
            setup_failure_reason=reason,
            setup_contract=contract,
        )
        self.assertIn(reason, {"missing_env_root", "missing_harness"})
        self.assertIn(subreason, {"missing_env_root", "missing_harness"})
        self.assertNotEqual(reason, "setup_script_modified_bad_path")
        self.assertNotEqual(subreason, "starter_fragile_path")

    def test_grading_result_validator_checks_diagnostic_fields(self) -> None:
        validator = _load_script(
            "validate_codex_live_reports_grading_result_fields",
            "scripts/validate-codex-live-benchmark-reports.py",
        )
        payload = {
            "setup_failure_reason": "missing_harness",
            "setup_failure_subreason": "missing_harness",
            "setup_contract": {"candidate_setup_exists": "yes"},
            "test_suite_failure_reason": "none",
            "security_failure_reason": "none",
            "first_failure_stage": "setup",
            "first_failure_excerpt": "/Users/raw CODEX_API_KEY=sk-SecretShouldFail12345",
            "setup_log_excerpt": "x" * 1201,
            "test_suite_log_excerpt": "",
            "security_log_excerpt": "",
        }
        errors = validator._grading_result_errors(payload)
        self.assertTrue(any("unredacted marker /Users/" in error for error in errors))
        self.assertTrue(any("unredacted marker CODEX_API_KEY" in error for error in errors))
        self.assertTrue(any("bounded to 1200" in error for error in errors))
        self.assertTrue(any("setup_contract.candidate_setup_exists must be boolean" in error for error in errors))

    def test_positive_effect_is_rejected_when_unknown_setup_dominates(self) -> None:
        summary_module = _load_script(
            "generate_codex_live_summary_unknown_positive_claim",
            "scripts/generate-codex-live-summary.py",
        )
        payload = _strict_summary_payload(
            effect_verdict="positive",
            effect_status="improved",
            dominant_setup_failure_reason="unknown",
            unknown_setup_failure_rate=1.0,
        )
        errors = summary_module.strict_publish_errors(payload)
        self.assertTrue(any("unknown setup failures dominate" in error for error in errors))

    def test_case_registry_requires_assertions_for_publishable_cases(self) -> None:
        helper = _load_script("codex_live_helper_bad_registry", "scripts/codex_live_benchmark_lib.py")
        data = {
            "schema_version": 1,
            "kind": "changeforge.codex_live_benchmark_cases",
            "cases": [
                {
                    "id": "devex/minimal-correct-implementation-ladder",
                    "category": "devex",
                    "codegen_case": "minimal-correct-implementation-ladder",
                    "enabled": True,
                    "variants": ["baseline_clean"],
                    "task_prompt": "evals/codegen/devex/minimal-correct-implementation-ladder/prompt.md",
                    "starter_repo": "evals/codegen/devex/minimal-correct-implementation-ladder/starter-repo",
                    "grading_benchmark": "devex/minimal-correct-implementation-ladder",
                    "grading_mode": "assertion",
                    "publishable_for_strict": True,
                }
            ],
        }
        errors = helper.validate_case_registry(data, ROOT)
        self.assertTrue(any("requires real pytest assertion files" in error for error in errors))

    def test_case_registry_has_core_and_level1_publishable_assertion_backed_cases(self) -> None:
        helper = _load_script("codex_live_helper_registry_coverage", "scripts/codex_live_benchmark_lib.py")
        cases = helper.load_case_registry()
        publishable = [
            case
            for case in cases
            if case.enabled and case.publishable_for_strict and case.grading_mode == "assertion"
        ]
        self.assertGreaterEqual(len(publishable), 12)
        self.assertGreaterEqual(sum(1 for case in publishable if case.tier == "core"), 5)
        self.assertGreaterEqual(sum(1 for case in publishable if case.tier == "level1"), 7)
        self.assertTrue(all(case.coverage_dimensions for case in cases))
        self.assertIn(
            "reliability/redis-cache-stampede-protection",
            {case.id for case in publishable},
        )
        self.assertTrue(
            all(helper.case_assertion_files(case.category, case.codegen_case) for case in publishable)
        )
        telemetry_only = [case for case in cases if case.grading_mode == "telemetry_only"]
        self.assertTrue(telemetry_only)
        self.assertTrue(all(not case.publishable_for_strict for case in telemetry_only))

    def test_runner_filters_cases_by_tier(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_tier_filter", "scripts/run-codex-live-benchmarks.py")
        helper = _load_script("codex_live_helper_tier_filter", "scripts/codex_live_benchmark_lib.py")
        cases = helper.load_case_registry()

        core_cases = runner.select_cases(cases, benchmarks=[], categories=[], tiers=["core"])
        level1_cases = runner.select_cases(cases, benchmarks=[], categories=[], tiers=["level1"])

        self.assertTrue(core_cases)
        self.assertTrue(level1_cases)
        self.assertTrue(all(case.tier == "core" for case in core_cases))
        self.assertTrue(all(case.tier == "level1" for case in level1_cases))
        self.assertNotIn("devex/minimal-correct-implementation-ladder", {case.id for case in core_cases})

    def test_runner_selects_failed_cells_and_shards_cases_deterministically(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_runtime_selection", "scripts/run-codex-live-benchmarks.py")
        helper = _load_script("codex_live_helper_runtime_selection", "scripts/codex_live_benchmark_lib.py")
        cases = helper.load_case_registry()
        with tempfile.TemporaryDirectory() as tmp:
            previous = Path(tmp) / "previous"
            failed_dir = previous / "cases" / "security__ssrf-url-allowlist" / "baseline_clean" / "run-02"
            failed_dir.mkdir(parents=True)
            failed_dir.joinpath("result.json").write_text(
                json.dumps(
                    _result_payload(
                        case_id="security/ssrf-url-allowlist",
                        variant="baseline_clean",
                        run_index=2,
                        benchmark_passed=False,
                        failure_category="test_suite_failed",
                    )
                ),
                encoding="utf-8",
            )
            args = SimpleNamespace(
                tier=[],
                changed_only=False,
                failed_only=None,
                rerun_failures_from=str(previous),
                max_cases=None,
                max_runtime_minutes=None,
                case_shard=None,
                parallel_cases=1,
                resume_run=None,
            )
            selected, metadata = runner.apply_runtime_selection(args, cases, ["baseline_clean"])
        self.assertEqual([case.id for case in selected], ["security/ssrf-url-allowlist"])
        self.assertEqual(metadata["rerun_cell_count"], 1)
        self.assertIn(("security/ssrf-url-allowlist", "baseline_clean", 2), args._changeforge_rerun_cells)

        shard_args = SimpleNamespace(
            tier=[],
            changed_only=False,
            failed_only=None,
            rerun_failures_from=None,
            max_cases=None,
            max_runtime_minutes=None,
            case_shard="1/2",
            parallel_cases=1,
            resume_run=None,
        )
        shard, shard_metadata = runner.apply_runtime_selection(shard_args, cases, ["baseline_clean"])
        self.assertTrue(shard)
        self.assertEqual(shard_metadata["case_shard_index"], 1)
        self.assertTrue(all(case.id in shard_metadata["selected_cases"] for case in shard))

    def test_structured_logs_process_traces_and_summary_validate(self) -> None:
        summary_module = _load_script(
            "generate_codex_live_summary_process_logging",
            "scripts/generate-codex-live-summary.py",
        )
        logs_validator = _load_script("validate_codex_live_logs_fixture", "scripts/validate-codex-live-logs.py")
        trace_validator = _load_script("validate_process_traces_fixture", "scripts/validate-process-traces.py")
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "run-manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "generated_by": "scripts/run-codex-live-benchmarks.py",
                        "run_id": "synthetic-run",
                        "status": "collected",
                        "benchmark_mode": "clean-paired",
                        "dry_run": False,
                        "live_execution_allowed": True,
                        "live_execution_effective": True,
                        "cases": ["security/ssrf-url-allowlist"],
                        "variants": ["baseline_clean"],
                        "runs_per_variant": 1,
                        "sandbox": "workspace-write",
                        "auth_policy": "borrow-current",
                        "codex_environment_policy": "auth_borrowed_clean",
                        "limitations": ["local"],
                    }
                ),
                encoding="utf-8",
            )
            event = {
                "schema_version": 1,
                "ts": "2026-06-23T07:31:37+08:00",
                "run_id": "synthetic-run",
                "case_id": "security/ssrf-url-allowlist",
                "variant": "baseline_clean",
                "run_index": 1,
                "tier": "core",
                "phase": "pdd",
                "event": "process_phase_evaluated",
                "status": "present",
                "duration_ms": 1,
                "selected_skills": [],
                "selected_capabilities": [],
                "hook_guidance_bytes": 0,
                "artifact": None,
                "error_category": None,
            }
            (run_dir / "run.log.jsonl").write_text(json.dumps(event) + "\n", encoding="utf-8")
            (run_dir / "timeline.jsonl").write_text(json.dumps(event) + "\n", encoding="utf-8")
            result_dir = run_dir / "cases" / "security__ssrf-url-allowlist" / "baseline_clean" / "run-01"
            result_dir.mkdir(parents=True)
            result_dir.joinpath("result.json").write_text(json.dumps(_result_payload()), encoding="utf-8")
            command = "python3 scripts/run-codegen-benchmarks.py --benchmark security/ssrf-url-allowlist --candidate-dir <candidate>"
            acceptance = ["deny private, metadata, and loopback URLs"]
            invariants = ["unsafe URL is never fetched"]
            public_api = ["public URL validation/fetch entrypoint used by tests"]
            error_contract = ["deny unsafe URLs with a stable error category"]
            failure_modes = ["metadata URL denial"]
            trace = {
                "schema_version": 1,
                "run_id": "synthetic-run",
                "case_id": "security/ssrf-url-allowlist",
                "variant": "baseline_clean",
                "run_index": 1,
                "phase_status": {
                    "pdd": "present",
                    "ddd": "present",
                    "sdd": "present",
                    "tdd": "present",
                    "implementation": "present",
                    "validation": "present",
                    "review": "present",
                },
                "traceability": {
                    "pdd_acceptance_to_tdd_tests": True,
                    "ddd_invariants_to_tdd_tests": True,
                    "sdd_public_api_to_tdd_tests": True,
                    "sdd_failure_modes_to_tdd_tests": True,
                    "sdd_logging_to_tdd_tests": True,
                    "pdd_to_tests": True,
                    "ddd_invariants_to_code_or_tests": True,
                    "sdd_public_api_to_tests": True,
                    "tdd_validation_commands_present": True,
                },
                "process_facts": {
                    "pdd": {
                        "problem": "Prevent SSRF with URL allowlist and safe diagnostics.",
                        "user_or_system_impact": ["protect internal metadata services"],
                        "acceptance_criteria": acceptance,
                        "constraints": ["preserve setup"],
                        "non_goals": ["private corpus"],
                        "risk_surfaces": ["security"],
                        "validation_signal": [command],
                    },
                    "ddd": {
                        "domain_terms": ["URL candidate", "network boundary"],
                        "entities": ["URL validation decision"],
                        "value_objects": ["normalized URL"],
                        "domain_services": [],
                        "application_services": [],
                        "adapters": [],
                        "invariants": invariants,
                        "ownership_decision": ["URL safety policy belongs before network fetch"],
                        "side_effect_boundaries": ["no network fetch until allowlist passes"],
                    },
                    "sdd": {
                        "modules": ["URL validation module"],
                        "files_to_change": ["candidate repository files selected by inspection"],
                        "public_api": public_api,
                        "data_flow": ["request -> validation"],
                        "error_contract": error_contract,
                        "failure_modes": failure_modes,
                        "logging_decision": {
                            "needed": True,
                            "log_types": ["security"],
                            "placement": ["security boundary"],
                            "events": ["url_denied"],
                            "levels": ["WARN"],
                            "fields": ["operation", "error_category", "policy", "trace_id"],
                            "redaction": ["raw URL query", "token"],
                            "correlation": ["trace_id", "request_id"],
                            "cardinality_controls": ["policy category instead of raw URL"],
                            "rationale": "Security denial diagnostics must not leak query secrets.",
                        },
                        "metrics_traces_alerts": ["grading-result.json"],
                        "performance_or_concurrency_constraints": ["security"],
                        "compatibility_and_migration": ["preserve harness"],
                        "rollback_or_recovery": ["revert candidate change"],
                    },
                    "tdd": {
                        "acceptance_to_tests": {acceptance[0]: [command]},
                        "invariant_to_tests_or_code": {invariants[0]: [command]},
                        "public_api_to_tests": {public_api[0]: [command]},
                        "failure_mode_tests": [
                            {"failure_mode": error_contract[0], "tests": [command]},
                            {"failure_mode": failure_modes[0], "tests": [command]},
                        ],
                        "logging_or_security_tests": ["metadata denied without raw query token"],
                        "validation_commands": [command],
                        "red_green_refactor_trace": ["recorded"],
                    },
                },
                "evidence_sources": ["final.md:compact-process-trace"],
                "validation_commands": [command],
                "artifacts": ["cases/security__ssrf-url-allowlist/baseline_clean/run-01/result.json"],
            }
            trace = _with_process_field_sources(trace)
            result_dir.joinpath("process-trace.json").write_text(json.dumps(trace), encoding="utf-8")
            summary = summary_module.generate_summary(run_dir)
            log_errors = logs_validator.validate_run_logs(run_dir)
            trace_errors = trace_validator.validate_process_traces(run_dir)
        self.assertEqual(log_errors, [])
        self.assertEqual(trace_errors, [])
        self.assertEqual(summary["logging_summary"]["run_log_events"], 1)
        self.assertEqual(summary["logging_summary"]["process_trace_count"], 1)
        self.assertEqual(summary["process_compliance_summary"]["pdd_present_rate"], 1.0)
        self.assertEqual(summary["process_compliance_summary"]["pdd_inferred_rate"], 0.0)
        self.assertEqual(summary["process_compliance_summary"]["validation_command_present_rate"], 1.0)

    def _trace_case(self) -> SimpleNamespace:
        return SimpleNamespace(
            id="security/ssrf-url-allowlist",
            category="security",
            codegen_case="ssrf-url-allowlist",
            grading_benchmark="security/ssrf-url-allowlist",
            tier="core",
            coverage_dimensions=("security", "ssrf"),
        )

    def test_process_trace_payload_uses_json_final_trace_before_metadata_fallback(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_json_trace", "scripts/run-codex-live-benchmarks.py")
        case = self._trace_case()
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "run"
            run_dir = out_dir / "cases" / "security__ssrf-url-allowlist" / "skills_only_clean" / "run-01"
            run_dir.mkdir(parents=True)
            run_dir.joinpath("final.md").write_text(
                """Result

```json
{
  "process_trace": {
    "pdd": {"problem": "Block SSRF metadata URLs", "acceptance_criteria": ["deny metadata URL"]},
    "ddd": {"invariants": ["unsafe URL is never fetched"]},
    "sdd": {"public_api": ["URL validation public entrypoint"], "failure_modes": ["metadata URL denial"]},
    "tdd": {"validation_commands": ["python3 scripts/run-codegen-benchmarks.py --benchmark security/ssrf-url-allowlist --candidate-dir <candidate>"]}
  }
}
```
""",
                encoding="utf-8",
            )
            trace = runner._process_trace_payload(
                out_dir,
                run_dir,
                case=case,
                variant="skills_only_clean",
                run_index=1,
                result={"status": "collected", "grading_status": "passed"},
            )
        self.assertEqual(trace["phase_status"]["pdd"], "degraded")
        self.assertEqual(trace["process_facts"]["pdd"]["problem"], "Block SSRF metadata URLs")
        self.assertEqual(trace["process_facts"]["pdd"]["_evidence_source"], "final.md:process-trace-json")
        self.assertEqual(trace["process_facts"]["pdd"]["_field_sources"]["problem"], "final.md:process-trace-json")
        self.assertEqual(trace["process_facts"]["pdd"]["_field_sources"]["constraints"], "case_metadata_fallback")
        self.assertIn("constraints", trace["process_facts"]["pdd"]["_inferred_fields"])
        self.assertIn("case_metadata_fallback:missing-fields", trace["evidence_sources"])
        self.assertIn("pdd_acceptance_to_tdd_tests", trace["required_quality_gates"])
        self.assertEqual(trace["stage_ownership"]["pdd"], "change-intake-compiler")
        for skill in (
            "development-process-orchestrator",
            "change-intake-compiler",
            "domain-impact-modeler",
            "architecture-impact-reviewer",
            "quality-test-gate",
        ):
            self.assertIn(skill, trace["selected_skills"])

    def test_process_trace_payload_parses_multiline_compact_trace(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_multiline_trace", "scripts/run-codex-live-benchmarks.py")
        case = self._trace_case()
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "run"
            run_dir = out_dir / "cases" / "security__ssrf-url-allowlist" / "skills_only_clean" / "run-01"
            run_dir.mkdir(parents=True)
            run_dir.joinpath("final.md").write_text(
                """Process Trace:
PDD:
  problem: Block SSRF metadata URLs
  acceptance: deny metadata URL
  constraints: preserve harness
  validation_signal: python3 scripts/run-codegen-benchmarks.py --benchmark security/ssrf-url-allowlist --candidate-dir <candidate>
DDD:
  domain_terms: URL candidate and network boundary
  invariants: unsafe URL is never fetched
  ownership_decision: URL safety policy owns deny decision
  side_effect_boundaries: no fetch before allowlist
SDD:
  modules: URL validation module
  public_api: URL validation public entrypoint
  error_contract: deny unsafe URLs with stable error
  failure_modes: metadata URL denial
  logging_decision:
    needed: true
    log_types:
      - security
    placement:
      - security boundary
    events:
      - url_denied
    levels:
      - WARN
    fields:
      - operation
      - error_category
      - policy
      - trace_id
    redaction:
      - raw URL query
    correlation:
      - trace_id
    cardinality_controls:
      - policy category instead of raw URL
TDD:
  acceptance_to_tests: deny metadata URL -> benchmark command
  invariant_to_tests_or_code: unsafe URL is never fetched -> benchmark command
  public_api_to_tests: public entrypoint -> benchmark command
  failure_mode_tests: metadata URL denial covered
  validation_commands: python3 scripts/run-codegen-benchmarks.py --benchmark security/ssrf-url-allowlist --candidate-dir <candidate>
Validation:
  python3 scripts/run-codegen-benchmarks.py --benchmark security/ssrf-url-allowlist --candidate-dir <candidate>
Residual Risk:
  none
""",
                encoding="utf-8",
            )
            trace = runner._process_trace_payload(
                out_dir,
                run_dir,
                case=case,
                variant="skills_only_clean",
                run_index=1,
                result={"status": "collected", "grading_status": "passed"},
            )
        self.assertEqual(trace["phase_status"]["sdd"], "present")
        self.assertEqual(trace["process_facts"]["sdd"]["logging_decision"]["needed"], True)
        self.assertIn("final.md:compact-process-trace", trace["evidence_sources"])
        self.assertIn("logging_decision_has_type_level_fields_redaction", trace["required_quality_gates"])

    def test_metadata_fallback_is_inferred_and_run_log_is_evidence_aware(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_inferred_trace", "scripts/run-codex-live-benchmarks.py")
        case = SimpleNamespace(
            id="experimental/no-final-trace",
            category="experimental",
            codegen_case="no-final-trace",
            grading_benchmark="experimental/no-final-trace",
            tier="experimental",
            coverage_dimensions=("experimental",),
        )
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "run"
            run_dir = out_dir / "cases" / "experimental__no-final-trace" / "skills_only_clean" / "run-01"
            run_dir.mkdir(parents=True)
            trace = runner._process_trace_payload(
                out_dir,
                run_dir,
                case=case,
                variant="skills_only_clean",
                run_index=1,
                result={"status": "collected", "grading_status": "passed"},
            )
            runner._write_process_trace_evaluation_started(out_dir, case=case, variant="skills_only_clean", run_index=1)
            runner._write_process_phase_events(
                out_dir,
                case=case,
                variant="skills_only_clean",
                run_index=1,
                phase_status=trace["phase_status"],
                evidence_sources=trace["evidence_sources"],
            )
            events = [
                json.loads(line)
                for line in out_dir.joinpath("run.log.jsonl").read_text(encoding="utf-8").splitlines()
            ]
        self.assertEqual(trace["phase_status"]["pdd"], "inferred")
        self.assertEqual(trace["process_facts"]["pdd"]["_evidence_source"], "case_metadata_fallback")
        self.assertEqual(trace["evidence_sources"], ["case_metadata_fallback"])
        self.assertFalse(
            any(event["event"] == "phase_completed" and event["phase"] in {"pdd", "ddd", "sdd", "tdd"} for event in events)
        )
        pdd_event = next(event for event in events if event["event"] == "process_phase_evaluated" and event["phase"] == "pdd")
        self.assertEqual(pdd_event["status"], "inferred")
        self.assertEqual(pdd_event["error_category"], "metadata_fallback_only")

    def test_publishable_starter_setup_runs_from_candidate_root_with_exported_root(self) -> None:
        helper = _load_script("codex_live_helper_candidate_setup_contract", "scripts/codex_live_benchmark_lib.py")
        grader = _load_script("grade_codex_live_candidate_setup_contract", "scripts/grade-codex-live-benchmarks.py")
        cases = [
            case
            for case in helper.load_case_registry()
            if case.enabled and case.publishable_for_strict and case.grading_mode == "assertion"
        ]
        self.assertGreaterEqual(len(cases), 5)
        for case in cases:
            with self.subTest(case=case.id):
                with tempfile.TemporaryDirectory() as tmp:
                    candidate = Path(tmp) / "candidate"
                    shutil.copytree(case.starter_repo, candidate)
                    env = os.environ.copy()
                    env["CHANGEFORGE_CODEGEN_ROOT"] = str(ROOT)
                    completed = subprocess.run(
                        ["bash", str(candidate / "setup.sh")],
                        cwd=candidate,
                        env=env,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        check=False,
                    )
                self.assertEqual(completed.returncode, 0, completed.stdout)
                self.assertEqual(grader._setup_failure_reason(completed.stdout, failed=False), "none")
                self.assertNotIn("setup_script_modified_bad_path", completed.stdout)

    def test_publishable_starter_setup_no_env_fallback_is_not_fragile_path(self) -> None:
        helper = _load_script("codex_live_helper_candidate_setup_no_env", "scripts/codex_live_benchmark_lib.py")
        grader = _load_script("grade_codex_live_candidate_setup_no_env", "scripts/grade-codex-live-benchmarks.py")
        cases = [
            case
            for case in helper.load_case_registry()
            if case.enabled and case.publishable_for_strict and case.grading_mode == "assertion"
        ]
        for case in cases:
            with self.subTest(case=case.id):
                with tempfile.TemporaryDirectory() as tmp:
                    candidate = Path(tmp) / "candidate"
                    shutil.copytree(case.starter_repo, candidate)
                    env = os.environ.copy()
                    env.pop("CHANGEFORGE_CODEGEN_ROOT", None)
                    completed = subprocess.run(
                        ["bash", str(candidate / "setup.sh")],
                        cwd=candidate,
                        env=env,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        check=False,
                    )
                    contract = grader._setup_contract(case.grading_benchmark, candidate, root=ROOT)
                self.assertNotEqual(completed.returncode, 0, completed.stdout)
                self.assertIn(
                    "could not locate scripts/codegen_benchmark_harness.py; set CHANGEFORGE_CODEGEN_ROOT",
                    completed.stdout,
                )
                reason = grader._setup_failure_reason(completed.stdout, failed=True)
                subreason = grader._setup_failure_subreason(
                    completed.stdout,
                    failed=True,
                    setup_failure_reason=reason,
                    setup_contract=contract,
                )
                self.assertIn(reason, {"missing_env_root", "missing_harness"})
                self.assertIn(subreason, {"missing_env_root", "missing_harness"})
                self.assertNotEqual(subreason, "starter_fragile_path")

    def test_publishable_starter_setup_contract_has_no_fixed_depth_lookup(self) -> None:
        helper = _load_script("codex_live_helper_setup_contract_scan", "scripts/codex_live_benchmark_lib.py")
        fixed_depth = re.compile(r"(\.\./){2,}|(\.\.\\){2,}|parents\[[1-9]")
        cases = [
            case
            for case in helper.load_case_registry()
            if case.enabled and case.publishable_for_strict and case.grading_mode == "assertion"
        ]
        for case in cases:
            with self.subTest(case=case.id):
                text = (case.starter_repo / "setup.sh").read_text(encoding="utf-8")
                self.assertIn("CHANGEFORGE_CODEGEN_ROOT", text)
                self.assertIn("codegen_benchmark_harness.py", text)
                self.assertFalse(fixed_depth.search(text))
                self.assertTrue(".parents" in text or "find_codegen_root" in text)

    def test_codegen_candidate_mode_cli_exports_root_candidate_and_stage_records(self) -> None:
        runner = _load_script("run_codegen_benchmark_candidate_cli_env", "scripts/run-codegen-benchmarks.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            codegen_dir = root / "evals" / "codegen"
            case_dir = codegen_dir / "sample" / "candidate-env"
            starter = case_dir / "starter-repo"
            test_suite = case_dir / "test-suite"
            security_checks = case_dir / "security-checks"
            tests_dir = test_suite / "tests"
            candidate = root / "candidate"
            for path in (starter, test_suite, security_checks, tests_dir, candidate):
                path.mkdir(parents=True, exist_ok=True)
            (starter / "README.md").write_text("starter\n", encoding="utf-8")
            (candidate / "README.md").write_text("candidate\n", encoding="utf-8")
            (starter / "setup.sh").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            (candidate / "setup.sh").write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env bash",
                        "set -euo pipefail",
                        "python3 - <<'PY'",
                        "import json, os",
                        "from pathlib import Path",
                        "root = Path(os.environ['CHANGEFORGE_CODEGEN_ROOT'])",
                        "candidate = Path(os.environ['CHANGEFORGE_CODEGEN_CANDIDATE_DIR'])",
                        "payload = {",
                        "    'root': str(root),",
                        "    'candidate': str(candidate),",
                        "    'cwd': str(Path.cwd()),",
                        "    'harness_exists': (root / 'scripts' / 'codegen_benchmark_harness.py').is_file(),",
                        "}",
                        "(candidate / 'setup-observed.json').write_text(json.dumps(payload), encoding='utf-8')",
                        "assert payload['harness_exists']",
                        "assert Path.cwd().resolve() == candidate.resolve()",
                        "PY",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (test_suite / "README.md").write_text(
                "# Test Suite\n\n## Expected Commands\n\n- `bash test-suite/run.sh`\n",
                encoding="utf-8",
            )
            (test_suite / "run.sh").write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env bash",
                        "# expected-command: bash test-suite/run.sh",
                        "set -euo pipefail",
                        'test -n "${CHANGEFORGE_CODEGEN_ROOT:-}"',
                        'test -n "${CHANGEFORGE_CODEGEN_CANDIDATE_DIR:-}"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (security_checks / "run.sh").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            (tests_dir / "test_candidate.py").write_text(
                "\n".join(
                    [
                        "import json, os",
                        "from pathlib import Path",
                        "candidate = Path(os.environ['CHANGEFORGE_CODEGEN_CANDIDATE_DIR'])",
                        "payload = {'candidate': str(candidate), 'cwd': str(Path.cwd())}",
                        "(candidate / 'assertion-observed.json').write_text(json.dumps(payload), encoding='utf-8')",
                        "assert Path.cwd().resolve() == candidate.resolve()",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            stage_dir = root / "stages"
            with patch.object(runner, "CODEGEN_DIR", codegen_dir):
                with patch.object(runner, "EXPECTED_BENCHMARKS", {"sample": ["candidate-env"]}):
                    result = runner.main(
                        [
                            "--benchmark",
                            "sample/candidate-env",
                            "--candidate-dir",
                            str(candidate),
                            "--stage-log-dir",
                            str(stage_dir),
                        ]
                    )
            setup_observed = json.loads((candidate / "setup-observed.json").read_text(encoding="utf-8"))
            assertion_observed = json.loads((candidate / "assertion-observed.json").read_text(encoding="utf-8"))
            records = json.loads(
                (stage_dir / "sample__candidate-env" / "stage-results.json").read_text(encoding="utf-8")
            )
        self.assertEqual(result, 0)
        self.assertEqual(Path(setup_observed["root"]), ROOT)
        self.assertEqual(Path(setup_observed["candidate"]).resolve(), candidate.resolve())
        self.assertEqual(Path(setup_observed["cwd"]).resolve(), candidate.resolve())
        self.assertEqual(Path(assertion_observed["candidate"]).resolve(), candidate.resolve())
        self.assertEqual(Path(assertion_observed["cwd"]).resolve(), candidate.resolve())
        self.assertEqual(
            [record["stage"] for record in records],
            ["setup", "test-suite", "security-checks", "assertion-files"],
        )
        self.assertTrue(all(record["passed"] is True for record in records))

    def test_codegen_candidate_mode_executes_real_assertion_files(self) -> None:
        runner = _load_script("run_codegen_benchmark_assertions", "scripts/run-codegen-benchmarks.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            case_dir = root / "case"
            starter = case_dir / "starter-repo"
            test_suite = case_dir / "test-suite"
            security_checks = case_dir / "security-checks"
            tests_dir = test_suite / "tests"
            candidate = root / "candidate"
            for path in (starter, test_suite, security_checks, tests_dir, candidate):
                path.mkdir(parents=True, exist_ok=True)
            for script in (
                starter / "setup.sh",
                candidate / "setup.sh",
                test_suite / "run.sh",
                security_checks / "run.sh",
            ):
                script.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            (candidate / "sentinel.txt").write_text("ok", encoding="utf-8")
            (tests_dir / "test_candidate.py").write_text(
                "\n".join(
                    [
                        "import os",
                        "from pathlib import Path",
                        "candidate = Path(os.environ['CHANGEFORGE_CODEGEN_CANDIDATE_DIR'])",
                        "assert (candidate / 'sentinel.txt').read_text(encoding='utf-8') == 'ok'",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            self.assertEqual(runner._run_case("sample", "assertion-case", case_dir, candidate), [])
            (candidate / "sentinel.txt").write_text("bad", encoding="utf-8")
            errors = runner._run_case("sample", "assertion-case", case_dir, candidate)
        self.assertTrue(any("assertion" in error and "test_candidate.py" in error for error in errors))

    def test_codegen_candidate_setup_uses_exported_root_and_candidate_dir(self) -> None:
        runner = _load_script("run_codegen_benchmark_candidate_env", "scripts/run-codegen-benchmarks.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            case_dir = root / "case"
            starter = case_dir / "starter-repo"
            test_suite = case_dir / "test-suite"
            security_checks = case_dir / "security-checks"
            tests_dir = test_suite / "tests"
            candidate = root / "candidate"
            for path in (starter, test_suite, security_checks, tests_dir, candidate):
                path.mkdir(parents=True, exist_ok=True)
            (starter / "setup.sh").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            (candidate / "setup.sh").write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env bash",
                        "set -euo pipefail",
                        'test -n "${CHANGEFORGE_CODEGEN_ROOT:-}"',
                        'test -f "$CHANGEFORGE_CODEGEN_ROOT/scripts/codegen_benchmark_harness.py"',
                        'python3 - <<\'PY\'',
                        "import os",
                        "from pathlib import Path",
                        "assert Path.cwd().resolve() == Path(os.environ['CHANGEFORGE_CODEGEN_CANDIDATE_DIR']).resolve()",
                        "PY",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (test_suite / "run.sh").write_text(
                "#!/usr/bin/env bash\nset -euo pipefail\ntest -n \"${CHANGEFORGE_CODEGEN_CANDIDATE_DIR:-}\"\n",
                encoding="utf-8",
            )
            (security_checks / "run.sh").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            (tests_dir / "test_candidate.py").write_text("assert True\n", encoding="utf-8")
            errors = runner._run_case("sample", "candidate-env", case_dir, candidate)
        self.assertEqual(errors, [])

    def test_codegen_candidate_mode_classifies_setup_contract_failures(self) -> None:
        runner = _load_script("run_codegen_benchmark_candidate_contract", "scripts/run-codegen-benchmarks.py")
        grader = _load_script("grade_codex_live_candidate_contract", "scripts/grade-codex-live-benchmarks.py")

        def make_case(root: Path) -> tuple[Path, Path]:
            case_dir = root / "case"
            starter = case_dir / "starter-repo"
            test_suite = case_dir / "test-suite"
            security_checks = case_dir / "security-checks"
            tests_dir = test_suite / "tests"
            candidate = root / "candidate"
            for path in (starter, test_suite, security_checks, tests_dir, candidate):
                path.mkdir(parents=True, exist_ok=True)
            (starter / "setup.sh").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            (starter / "README.md").write_text("starter contract\n", encoding="utf-8")
            (candidate / "README.md").write_text("candidate contract\n", encoding="utf-8")
            (test_suite / "run.sh").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            (security_checks / "run.sh").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            (tests_dir / "test_candidate.py").write_text("assert True\n", encoding="utf-8")
            return case_dir, candidate

        with tempfile.TemporaryDirectory() as tmp:
            case_dir, candidate = make_case(Path(tmp))
            (candidate / "setup.sh").write_text(
                "#!/usr/bin/env bash\npython3 ../../../../../scripts/codegen_benchmark_harness.py setup \"$PWD\"\n",
                encoding="utf-8",
            )
            errors = runner._run_case("sample", "bad-fixed-path", case_dir, candidate)
        fixed_path_output = "\n".join(errors)
        self.assertIn("../../../../../scripts/codegen_benchmark_harness.py", fixed_path_output)
        self.assertEqual(
            grader._setup_failure_reason(fixed_path_output, failed=True),
            "setup_script_modified_bad_path",
        )

        with tempfile.TemporaryDirectory() as tmp:
            case_dir, candidate = make_case(Path(tmp))
            errors = runner._run_case("sample", "missing-setup", case_dir, candidate)
        self.assertTrue(any("candidate/setup.sh missing" in error for error in errors))
        self.assertEqual(grader._setup_failure_reason("\n".join(errors), failed=True), "setup_script_missing")

        with tempfile.TemporaryDirectory() as tmp:
            case_dir, candidate = make_case(Path(tmp))
            (candidate / "setup.sh").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            (candidate / "README.md").unlink()
            errors = runner._run_case("sample", "removed-required-file", case_dir, candidate)
        self.assertTrue(any("candidate lacks required starter file README.md" in error for error in errors))
        self.assertEqual(
            grader._setup_failure_reason("\n".join(errors), failed=True),
            "candidate_removed_required_file",
        )

    def test_scorecard_and_public_summary_mark_smoke_summary_partial(self) -> None:
        scorecard = _load_script("generate_professional_scorecard_codex_live", "scripts/generate-professional-scorecard.py")
        public = _load_script("generate_public_summary_codex_live", "scripts/generate-public-benchmark-summary.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "reports").mkdir()
            (root / "reports" / "codex-live-benchmark-summary.json").write_text(
                json.dumps(_strict_summary_payload()),
                encoding="utf-8",
            )
            status, detail = scorecard.codex_live_benchmark_status(root)
            item = public._codex_live_benchmark_item(root)
        self.assertEqual(status, "partial")
        self.assertIn("auth_borrowed_clean", detail)
        self.assertIn('"evidence_status": "partial"', detail)
        self.assertIn('"effect_status": "inconclusive"', detail)
        self.assertEqual(item.status, "partial")
        self.assertIn("scope=smoke", item.detail)
        self.assertIn("effect=inconclusive/inconclusive", item.detail)
        self.assertEqual(item.evidence_level, "local_codex_cli_live_benchmark")

    def test_scorecard_and_public_summary_accept_strong_ablation_summary(self) -> None:
        scorecard = _load_script(
            "generate_professional_scorecard_codex_live_strong",
            "scripts/generate-professional-scorecard.py",
        )
        public = _load_script("generate_public_summary_codex_live_strong", "scripts/generate-public-benchmark-summary.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "reports").mkdir()
            (root / "reports" / "codex-live-benchmark-summary.json").write_text(
                json.dumps(_strong_ablation_summary_payload()),
                encoding="utf-8",
            )
            pass_status, pass_detail = scorecard.codex_live_pass_rate_benchmark_status(root)
            capability_status, capability_detail = scorecard.codex_live_capability_coverage_benchmark_status(root)
            aggregate_status, aggregate_detail = scorecard.codex_live_benchmark_status(root)
            item = public._codex_live_pass_rate_benchmark_item(root)
            capability_item = public._codex_live_capability_coverage_item(root)
        self.assertEqual(pass_status, "pass")
        self.assertIn('"evidence_scope": "multi_case_ablation_3_run"', pass_detail)
        self.assertIn('"evidence_status": "pass"', pass_detail)
        self.assertEqual(capability_status, "partial")
        self.assertIn("linked case was not run", capability_detail)
        self.assertEqual(aggregate_status, "partial")
        self.assertIn("capability_coverage", aggregate_detail)
        self.assertEqual(item.status, "pass")
        self.assertIn("mode=ablation", item.detail)
        self.assertIn("ready=True", item.detail)
        self.assertEqual(capability_item.status, "partial")

    def test_public_summary_syncs_codex_live_evidence_level_from_live_summary(self) -> None:
        public = _load_script(
            "generate_public_summary_codex_live_evidence_level_sync",
            "scripts/generate-public-benchmark-summary.py",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports = root / "reports"
            reports.mkdir()
            (reports / "codex-live-benchmark-summary.json").write_text(
                json.dumps(_strong_ablation_summary_payload(run_id="current-positive")),
                encoding="utf-8",
            )
            (reports / "professional-scorecard.json").write_text(
                json.dumps(
                    {
                        "evidence_levels": {
                            "local_codex_cli_live_benchmark": {
                                "status": "partial",
                                "meaning": "stale copied level",
                            }
                        },
                        "dimensions": [],
                    }
                ),
                encoding="utf-8",
            )
            payload = public.generate_summary(root)
        self.assertEqual(payload["evidence_levels"]["local_codex_cli_live_benchmark"]["status"], "partial")

    def test_report_consistency_rejects_stale_scorecard_run_id(self) -> None:
        validator = _load_script(
            "validate_codex_live_report_consistency_stale_scorecard",
            "scripts/validate-codex-live-benchmark-reports.py",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports = root / "reports"
            reports.mkdir()
            summary_path = reports / "codex-live-benchmark-summary.json"
            scorecard_path = reports / "professional-scorecard.json"
            summary = _strong_ablation_summary_payload(run_id="positive-run")
            summary_path.write_text(json.dumps(summary), encoding="utf-8")
            scorecard_path.write_text(
                json.dumps(
                    {
                        "dimensions": _split_codex_live_items(
                            summary,
                            pass_rate_detail={
                                "run_id": "old-partial-run",
                                "evidence_status": "pass",
                                "effect_verdict": "positive",
                            },
                        )
                    }
                ),
                encoding="utf-8",
            )
            errors = validator.validate_report_consistency(summary_path, scorecard_path=scorecard_path)
        self.assertTrue(any("detail run_id" in error for error in errors))

    def test_report_consistency_rejects_stale_public_partial_status(self) -> None:
        validator = _load_script(
            "validate_codex_live_report_consistency_stale_public",
            "scripts/validate-codex-live-benchmark-reports.py",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports = root / "reports"
            reports.mkdir()
            summary_path = reports / "codex-live-benchmark-summary.json"
            public_path = reports / "public-benchmark-summary.json"
            summary = _strong_ablation_summary_payload(run_id="positive-run")
            summary_path.write_text(json.dumps(summary), encoding="utf-8")
            public_path.write_text(
                json.dumps(
                    {
                        "items": _split_codex_live_items(
                            summary,
                            pass_rate_status="partial",
                            pass_rate_detail={
                                "run_id": "positive-run",
                                "evidence_status": "partial",
                                "effect_verdict": "mixed",
                            },
                        ),
                        "evidence_levels": {
                            "local_codex_cli_live_benchmark": {
                                "status": "partial",
                                "meaning": "stale",
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            errors = validator.validate_report_consistency(summary_path, public_summary_path=public_path)
        self.assertTrue(any("status 'partial' does not match strict evidence status 'pass'" in error for error in errors))
        self.assertTrue(any("effect_verdict" in error for error in errors))

    def test_report_consistency_rejects_stale_public_counts_and_hook_rate(self) -> None:
        validator = _load_script(
            "validate_codex_live_report_consistency_stale_public_counts",
            "scripts/validate-codex-live-benchmark-reports.py",
        )
        summary = _strong_ablation_summary_payload(
            run_id="positive-run",
            benchmark_passed_result_count=40,
            benchmark_eligible_result_count=45,
        )
        detail = {
            "run_id": "positive-run",
            "evidence_status": "pass",
            "effect_verdict": "positive",
            "benchmark_passed_result_count": 28,
            "benchmark_eligible_result_count": 44,
            "variants": {
                "skills_with_hooks_clean": {
                    "pass_rate": 0.7857,
                }
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            reports = Path(tmp) / "reports"
            reports.mkdir()
            summary_path = reports / "codex-live-benchmark-summary.json"
            public_path = reports / "public-benchmark-summary.json"
            summary_path.write_text(json.dumps(summary), encoding="utf-8")
            public_path.write_text(
                json.dumps(
                    {
                        "items": _split_codex_live_items(summary, pass_rate_detail=detail),
                        "evidence_levels": {
                            "local_codex_cli_live_benchmark": {
                                "status": "partial",
                                "meaning": "Opt-in local Codex CLI benchmark run.",
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            errors = validator.validate_report_consistency(summary_path, public_summary_path=public_path)
        self.assertTrue(any("benchmark_passed_result_count" in error for error in errors))
        self.assertTrue(any("benchmark_eligible_result_count" in error for error in errors))
        self.assertTrue(any("skills_with_hooks_clean.pass_rate" in error for error in errors))

    def test_report_consistency_rejects_stale_scorecard_counts_and_hook_rate(self) -> None:
        validator = _load_script(
            "validate_codex_live_report_consistency_stale_scorecard_counts",
            "scripts/validate-codex-live-benchmark-reports.py",
        )
        summary = _strong_ablation_summary_payload(
            run_id="positive-run",
            benchmark_passed_result_count=40,
            benchmark_eligible_result_count=45,
        )
        detail = {
            "run_id": "positive-run",
            "evidence_status": "pass",
            "effect_verdict": "positive",
            "benchmark_passed_result_count": 28,
            "benchmark_eligible_result_count": 44,
            "variants": {
                "skills_with_hooks_clean": {
                    "pass_rate": 0.7857,
                }
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            reports = Path(tmp) / "reports"
            reports.mkdir()
            summary_path = reports / "codex-live-benchmark-summary.json"
            scorecard_path = reports / "professional-scorecard.json"
            summary_path.write_text(json.dumps(summary), encoding="utf-8")
            scorecard_path.write_text(
                json.dumps(
                    {
                        "dimensions": _split_codex_live_items(summary, pass_rate_detail=detail)
                    }
                ),
                encoding="utf-8",
            )
            errors = validator.validate_report_consistency(summary_path, scorecard_path=scorecard_path)
        self.assertTrue(any("benchmark_passed_result_count" in error for error in errors))
        self.assertTrue(any("benchmark_eligible_result_count" in error for error in errors))
        self.assertTrue(any("skills_with_hooks_clean.pass_rate" in error for error in errors))

    def test_report_consistency_accepts_consistent_positive_summary(self) -> None:
        validator = _load_script(
            "validate_codex_live_report_consistency_positive",
            "scripts/validate-codex-live-benchmark-reports.py",
        )
        summary = _strong_ablation_summary_payload(run_id="positive-run")
        detail = _codex_report_detail(summary)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports = root / "reports"
            reports.mkdir()
            summary_path = reports / "codex-live-benchmark-summary.json"
            scorecard_path = reports / "professional-scorecard.json"
            public_path = reports / "public-benchmark-summary.json"
            summary_path.write_text(json.dumps(summary), encoding="utf-8")
            scorecard_path.write_text(
                json.dumps({"dimensions": _split_codex_live_items(summary, pass_rate_detail=detail)}),
                encoding="utf-8",
            )
            public_path.write_text(
                json.dumps(
                    {
                        "items": _split_codex_live_items(summary, pass_rate_detail=detail),
                        "evidence_levels": {
                            "local_codex_cli_live_benchmark": {
                                "status": "partial",
                                "meaning": "Opt-in local Codex CLI benchmark run.",
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            errors = validator.validate_report_consistency(
                summary_path,
                scorecard_path=scorecard_path,
                public_summary_path=public_path,
            )
        self.assertEqual(errors, [])

    def test_report_consistency_accepts_consistent_partial_mixed_summary(self) -> None:
        validator = _load_script(
            "validate_codex_live_report_consistency_partial",
            "scripts/validate-codex-live-benchmark-reports.py",
        )
        summary = _strong_ablation_summary_payload(
            run_id="partial-run",
            status="partial",
            effect_verdict="mixed",
            effect_status="mixed",
        )
        detail = _codex_report_detail(summary, status="partial")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports = root / "reports"
            reports.mkdir()
            summary_path = reports / "codex-live-benchmark-summary.json"
            scorecard_path = reports / "professional-scorecard.json"
            public_path = reports / "public-benchmark-summary.json"
            summary_path.write_text(json.dumps(summary), encoding="utf-8")
            scorecard_path.write_text(
                json.dumps(
                    {
                        "dimensions": _split_codex_live_items(
                            summary,
                            pass_rate_status="partial",
                            capability_status="partial",
                            pass_rate_detail=detail,
                            capability_detail=detail,
                        )
                    }
                ),
                encoding="utf-8",
            )
            public_path.write_text(
                json.dumps(
                    {
                        "items": _split_codex_live_items(
                            summary,
                            pass_rate_status="partial",
                            capability_status="partial",
                            pass_rate_detail=detail,
                            capability_detail=detail,
                        ),
                        "evidence_levels": {
                            "local_codex_cli_live_benchmark": {
                                "status": "partial",
                                "meaning": "Opt-in local Codex CLI benchmark run.",
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            errors = validator.validate_report_consistency(
                summary_path,
                scorecard_path=scorecard_path,
                public_summary_path=public_path,
            )
        self.assertEqual(errors, [])

    def test_report_consistency_rejects_readme_profile_count_mismatch(self) -> None:
        validator = _load_script(
            "validate_codex_live_report_consistency_readme_profiles",
            "scripts/validate-codex-live-benchmark-reports.py",
        )
        summary = _strong_ablation_summary_payload(run_id="profile-run")
        detail = _codex_report_detail(summary)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports = root / "reports"
            docs = root / "docs"
            reports.mkdir()
            docs.mkdir()
            summary_path = reports / "codex-live-benchmark-summary.json"
            scorecard_path = reports / "professional-scorecard.json"
            dashboard_path = docs / "SCORECARD_DASHBOARD.md"
            readme_path = root / "README.md"
            summary_path.write_text(json.dumps(summary), encoding="utf-8")
            scorecard_path.write_text(
                json.dumps(
                    {
                        "status_summary": {"pass": 1, "partial": 0, "fail": 0, "unknown": 0, "not_collected": 0},
                        "dimensions": [
                            {"name": "Codex CLI live benchmark", "status": "pass", "detail": json.dumps(detail)}
                        ],
                        "profile_counts": {
                            "recommended": {"detail": "recommended top-level count is 21"},
                            "full": {"detail": "full top-level count is 28"},
                            "dev": {"detail": "dev top-level count is 155"},
                        },
                    }
                ),
                encoding="utf-8",
            )
            _write_profile_manifests(root, {"recommended": 21, "full": 28, "dev": 155})
            dashboard_path.write_text(
                "\n".join(
                    [
                        "# Scorecard Dashboard",
                        "## Status Summary",
                        "- `pass`: 1",
                        "- `partial`: 0",
                        "- `fail`: 0",
                        "- `unknown`: 0",
                        "- `not_collected`: 0",
                        "| Evidence | Status | Detail |",
                        "| --- | --- | --- |",
                        "| Codex CLI live benchmark | `pass` | ok |",
                    ]
                ),
                encoding="utf-8",
            )
            readme_path.write_text(
                "\n".join(
                    [
                        "Stable profile counts are recommended=19, full=26, and dev=153; these generated manifests are the authoritative runtime profile count source.",
                        "<!-- changeforge-scorecard-summary:start -->",
                        "| Evidence | Status | Source |",
                        "| --- | --- | --- |",
                        "| Codex CLI live benchmark | `pass` | reports/codex-live-benchmark-summary.json |",
                        "<!-- changeforge-scorecard-summary:end -->",
                    ]
                ),
                encoding="utf-8",
            )
            errors = validator.validate_report_consistency(
                summary_path,
                scorecard_path=scorecard_path,
                dashboard_path=dashboard_path,
                readme_path=readme_path,
            )
        self.assertTrue(any("README profile counts" in error for error in errors))

    def test_report_consistency_rejects_dashboard_count_mismatch(self) -> None:
        validator = _load_script(
            "validate_codex_live_report_consistency_dashboard_counts",
            "scripts/validate-codex-live-benchmark-reports.py",
        )
        summary = _strong_ablation_summary_payload(run_id="dashboard-run")
        detail = _codex_report_detail(summary)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports = root / "reports"
            docs = root / "docs"
            reports.mkdir()
            docs.mkdir()
            summary_path = reports / "codex-live-benchmark-summary.json"
            scorecard_path = reports / "professional-scorecard.json"
            dashboard_path = docs / "SCORECARD_DASHBOARD.md"
            summary_path.write_text(json.dumps(summary), encoding="utf-8")
            scorecard_path.write_text(
                json.dumps(
                    {
                        "status_summary": {"pass": 1, "partial": 0, "fail": 0, "unknown": 0, "not_collected": 0},
                        "dimensions": [
                            {"name": "Codex CLI live benchmark", "status": "pass", "detail": json.dumps(detail)}
                        ],
                    }
                ),
                encoding="utf-8",
            )
            dashboard_path.write_text(
                "\n".join(
                    [
                        "# Scorecard Dashboard",
                        "## Status Summary",
                        "- `pass`: 0",
                        "- `partial`: 1",
                        "- `fail`: 0",
                        "- `unknown`: 0",
                        "- `not_collected`: 0",
                    ]
                ),
                encoding="utf-8",
            )
            errors = validator.validate_report_consistency(
                summary_path,
                scorecard_path=scorecard_path,
                dashboard_path=dashboard_path,
            )
        self.assertTrue(any("SCORECARD_DASHBOARD.md status counts" in error for error in errors))

    def test_report_consistency_rejects_stale_public_markdown_run_id(self) -> None:
        validator = _load_script(
            "validate_codex_live_report_consistency_stale_markdown",
            "scripts/validate-codex-live-benchmark-reports.py",
        )
        detail = {
            "run_id": "current-run",
            "evidence_status": "pass",
            "effect_verdict": "positive",
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports = root / "reports"
            reports.mkdir()
            summary_path = reports / "codex-live-benchmark-summary.json"
            public_path = reports / "public-benchmark-summary.json"
            public_md_path = reports / "public-benchmark-summary.md"
            summary_path.write_text(
                json.dumps(_strong_ablation_summary_payload(run_id="current-run")),
                encoding="utf-8",
            )
            public_path.write_text(
                json.dumps(
                    {
                        "items": _split_codex_live_items(
                            _strong_ablation_summary_payload(run_id="current-run"),
                            pass_rate_detail=detail,
                        ),
                        "evidence_levels": {
                            "local_codex_cli_live_benchmark": {
                                "status": "partial",
                                "meaning": "Opt-in local Codex CLI benchmark run.",
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            public_md_path.write_text(
                '| Codex CLI live pass-rate benchmark | `pass` | {"run_id": "old-run", "effect_verdict": "positive"} |\n',
                encoding="utf-8",
            )
            errors = validator.validate_report_consistency(summary_path, public_summary_path=public_path)
        self.assertTrue(any("does not reference current live run_id" in error for error in errors))

    def test_public_summary_rejects_current_home_smoke_as_strict_file(self) -> None:
        public = _load_script("generate_public_summary_codex_live_smoke", "scripts/generate-public-benchmark-summary.py")
        payload = _strict_summary_payload(
            benchmark_mode="current-home-smoke",
            evidence_level="current_home_integration_smoke",
            auth_policy="current-home-full",
            codex_environment_policy="current_home_full",
            strict_benchmark_eligible=False,
            current_home_full_result_count=1,
            user_skills_visible=True,
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "reports").mkdir()
            (root / "reports" / "codex-live-benchmark-summary.json").write_text(json.dumps(payload), encoding="utf-8")
            item = public._codex_live_benchmark_item(root)
        self.assertEqual(item.status, "fail")
        self.assertIn("current-home-full", item.detail)

    def test_scorecard_and_public_summary_reject_contaminated_summary(self) -> None:
        scorecard = _load_script(
            "generate_professional_scorecard_codex_live_contaminated",
            "scripts/generate-professional-scorecard.py",
        )
        public = _load_script(
            "generate_public_summary_codex_live_contaminated",
            "scripts/generate-public-benchmark-summary.py",
        )
        payload = _strong_ablation_summary_payload(
            contaminated_result_count=1,
            user_skills_visible=True,
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "reports").mkdir()
            (root / "reports" / "codex-live-benchmark-summary.json").write_text(
                json.dumps(payload),
                encoding="utf-8",
            )
            status, detail = scorecard.codex_live_benchmark_status(root)
            item = public._codex_live_benchmark_item(root)
        self.assertEqual(status, "fail")
        self.assertIn("contaminated results", detail)
        self.assertEqual(item.status, "fail")

    def test_scorecard_and_public_summary_mark_inconclusive_ablation_partial(self) -> None:
        scorecard = _load_script(
            "generate_professional_scorecard_codex_live_inconclusive_ablation",
            "scripts/generate-professional-scorecard.py",
        )
        public = _load_script(
            "generate_public_summary_codex_live_inconclusive_ablation",
            "scripts/generate-public-benchmark-summary.py",
        )
        payload = _strong_ablation_summary_payload(
            effect_verdict="inconclusive",
            effect_status="inconclusive",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "reports").mkdir()
            (root / "reports" / "codex-live-benchmark-summary.json").write_text(
                json.dumps(payload),
                encoding="utf-8",
            )
            status, detail = scorecard.codex_live_benchmark_status(root)
            item = public._codex_live_benchmark_item(root)
        self.assertEqual(status, "partial")
        self.assertIn("effect_status/effect_verdict is inconclusive", detail)
        self.assertEqual(item.status, "partial")

    def test_scorecard_and_public_summary_reject_ablation_missing_delta(self) -> None:
        scorecard = _load_script(
            "generate_professional_scorecard_codex_live_ablation_delta",
            "scripts/generate-professional-scorecard.py",
        )
        public = _load_script(
            "generate_public_summary_codex_live_ablation_delta",
            "scripts/generate-public-benchmark-summary.py",
        )
        payload = _strict_summary_payload(
            benchmark_mode="ablation",
            result_count=3,
            benchmark_eligible_result_count=3,
            benchmark_passed_result_count=3,
            failure_categories={"none": 3},
            variants={
                "baseline_clean": _variant_payload(),
                "skills_only_clean": _variant_payload(variant="skills_only_clean"),
                "skills_with_hooks_clean": _variant_payload(variant="skills_with_hooks_clean"),
            },
            delta={
                "skills_only_clean_vs_baseline_clean": {"pass_rate_delta": 0.0},
                "skills_with_hooks_clean_vs_baseline_clean": {"pass_rate_delta": 0.0},
            },
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "reports").mkdir()
            (root / "reports" / "codex-live-benchmark-summary.json").write_text(
                json.dumps(payload),
                encoding="utf-8",
            )
            status, detail = scorecard.codex_live_benchmark_status(root)
            item = public._codex_live_benchmark_item(root)
        self.assertEqual(status, "fail")
        self.assertIn("delta.skills_with_hooks_clean_vs_skills_only_clean", detail)
        self.assertEqual(item.status, "fail")
        self.assertIn("ablation delta.skills_with_hooks_clean_vs_skills_only_clean", item.detail)

    def test_process_missing_does_not_block_pass_rate_but_blocks_capability_coverage(self) -> None:
        lib = _load_script("codex_live_lib_process_missing", "scripts/codex_live_benchmark_lib.py")
        summary = _strong_ablation_summary_payload()
        summary.pop("process_compliance_summary", None)
        pass_status, pass_errors, pass_warnings = lib.codex_live_pass_rate_status(summary)
        capability_status, capability_errors, capability_warnings = lib.codex_live_capability_coverage_status(summary)
        self.assertEqual(pass_status, "pass")
        self.assertEqual(pass_errors, [])
        self.assertEqual(pass_warnings, [])
        self.assertEqual(capability_status, "partial")
        self.assertEqual(capability_errors, [])
        self.assertTrue(any("process_compliance_summary missing" in warning for warning in capability_warnings))

    def test_process_trace_zero_blocks_process_capability(self) -> None:
        lib = _load_script("codex_live_lib_process_zero", "scripts/codex_live_benchmark_lib.py")
        summary = _strong_ablation_summary_payload(
            cases_summary={
                "process/full-pdd-ddd-sdd-tdd-review-repair": _case_summary_payload(),
            },
            process_compliance_summary=_process_summary(
                process_trace_count=0,
                pdd_present_rate=1.0,
                ddd_present_rate=1.0,
                sdd_present_rate=1.0,
                tdd_present_rate=1.0,
                required_field_fallback_rate=0.0,
            ),
        )
        coverage = lib.codex_live_capability_coverage_summary(summary)
        item = next(row for row in coverage["items"] if row["id"] == "pdd_ddd_sdd_tdd_review_flow")
        self.assertNotEqual(item["status"], "pass")
        self.assertTrue(any("process_trace_count is 0" in reason for reason in item["reasons"]))

    def test_inferred_only_not_explicit_compliance(self) -> None:
        lib = _load_script("codex_live_lib_inferred_only", "scripts/codex_live_benchmark_lib.py")
        summary = _strong_ablation_summary_payload(
            cases_summary={
                "process/full-pdd-ddd-sdd-tdd-review-repair": _case_summary_payload(),
            },
            process_compliance_summary=_process_summary(
                process_trace_count=3,
                pdd_present_rate=0.0,
                ddd_present_rate=0.0,
                sdd_present_rate=0.0,
                tdd_present_rate=0.0,
                pdd_inferred_rate=1.0,
                ddd_inferred_rate=1.0,
                sdd_inferred_rate=1.0,
                tdd_inferred_rate=1.0,
                required_field_fallback_rate=0.0,
            ),
        )
        coverage = lib.codex_live_capability_coverage_summary(summary)
        item = next(row for row in coverage["items"] if row["id"] == "pdd_ddd_sdd_tdd_review_flow")
        self.assertNotEqual(item["status"], "pass")
        self.assertTrue(any("explicit PDD/DDD/SDD/TDD traces were not captured" in reason for reason in item["reasons"]))

    def test_capability_matrix_missing_core_case_partial(self) -> None:
        lib = _load_script("codex_live_lib_capability_missing_case", "scripts/codex_live_benchmark_lib.py")
        capability = lib.CodexLiveCapability(
            id="professional_injection_activation",
            title="Professional Injection Activation",
            description="fixture",
            expected_runtime_signal="fixture",
            linked_live_cases=(),
            linked_assertions=(),
            required_variants=("baseline_clean", "skills_only_clean", "skills_with_hooks_clean"),
            publishable_for_strict=True,
            quality_pass_criteria="fixture",
            evidence_kind="fixture",
            failure_interpretation="fixture",
            current_status="partial",
        )
        coverage = lib.codex_live_capability_coverage_summary(
            _strong_ablation_summary_payload(),
            capabilities=[capability],
        )
        item = next(row for row in coverage["items"] if row["id"] == "professional_injection_activation")
        self.assertEqual(item["status"], "partial")
        self.assertIn("capability has no linked live case", item["reasons"])

    def test_capability_case_assertion_fail(self) -> None:
        lib = _load_script("codex_live_lib_capability_case_fail", "scripts/codex_live_benchmark_lib.py")
        summary = _strong_ablation_summary_payload(
            cases_summary={
                "injection/professional-route-manifest-activation": _case_summary_payload(
                    skills_only_passed=2,
                    hooks_passed=3,
                ),
            },
            process_compliance_summary=_process_summary(
                pdd_present_rate=1.0,
                ddd_present_rate=1.0,
                sdd_present_rate=1.0,
                tdd_present_rate=1.0,
                required_field_fallback_rate=0.0,
                process_trace_inferred_only_rate=0.0,
            ),
        )
        coverage = lib.codex_live_capability_coverage_summary(summary)
        item = next(row for row in coverage["items"] if row["id"] == "professional_injection_activation")
        self.assertEqual(item["status"], "fail")
        self.assertEqual(item["assertion_status"], "fail")

    def test_quality_improvement_ignores_cost(self) -> None:
        lib = _load_script("codex_live_lib_quality_ignores_cost", "scripts/codex_live_benchmark_lib.py")
        public = _load_script("public_summary_quality_ignores_cost", "scripts/generate-public-benchmark-summary.py")
        summary = _strong_ablation_summary_payload(
            cost_summary={
                "total_usage": {"input_tokens": 999999, "output_tokens": 999999, "reasoning_output_tokens": 999999},
                "cost_is_telemetry_only": True,
                "quality_gate_uses_cost": False,
            }
        )
        status, errors, warnings = lib.codex_live_pass_rate_status(summary)
        self.assertEqual(status, "pass")
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "reports").mkdir()
            (root / "reports" / "codex-live-benchmark-summary.json").write_text(json.dumps(summary), encoding="utf-8")
            item = public._codex_live_pass_rate_benchmark_item(root)
        self.assertEqual(item.status, "pass")
        self.assertNotIn("efficiency improved", item.detail.casefold())

    def test_large_quality_improvement_requires_capability_coverage(self) -> None:
        generator = _load_script("codex_live_summary_large_quality", "scripts/generate-codex-live-summary.py")
        quality = generator._quality_improvement_summary(
            {
                "baseline_clean": {"pass_rate": 0.4},
                "skills_only_clean": {"pass_rate": 0.7333},
                "skills_with_hooks_clean": {"pass_rate": 0.8667},
            },
            {},
            {"skills_with_hooks_below_skills_only_cases": [], "regressed_cases": []},
            {
                "assertion_backed_coverage_count": 5,
                "assertion_backed_covered_capabilities": [
                    "professional_injection_activation",
                    "staged_injection_precision",
                    "pdd_ddd_sdd_tdd_review_flow",
                    "validation_broker_freshness",
                    "minimal_correct_implementation_ladder",
                ],
            },
        )
        self.assertTrue(quality["baseline_quality_improved"])
        self.assertTrue(quality["skill_quality_improved"])
        self.assertTrue(quality["hook_quality_increment_positive"])
        self.assertFalse(quality["large_quality_improvement_claim"])

    def test_reliability_no_improvement_visible(self) -> None:
        generator = _load_script("codex_live_summary_reliability_no_improvement", "scripts/generate-codex-live-summary.py")
        result = generator._case_result_summary(
            {
                "reliability/redis-cache-stampede-protection": _case_summary_payload(
                    baseline_passed=1,
                    skills_only_passed=1,
                    hooks_passed=1,
                )
            }
        )
        self.assertTrue(result["reliability_no_improvement_visible"])
        self.assertEqual(result["reliability_no_improvement_cases"][0]["case_id"], "reliability/redis-cache-stampede-protection")

    def test_smoke_not_canonical(self) -> None:
        validator = _load_script("validate_codex_live_report_smoke_not_canonical", "scripts/validate-codex-live-benchmark-reports.py")
        summary = _strict_summary_payload(evidence_scope="smoke", evidence_scope_ready=False)
        with tempfile.TemporaryDirectory() as tmp:
            reports = Path(tmp) / "reports"
            reports.mkdir()
            summary_path = reports / "codex-live-benchmark-summary.json"
            summary_path.write_text(json.dumps(summary), encoding="utf-8")
            errors = validator.validate_report_consistency(summary_path)
        self.assertTrue(any("canonical codex-live-benchmark-summary.json cannot contain a collected smoke artifact" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
