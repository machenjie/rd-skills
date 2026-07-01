#!/usr/bin/env python3
"""Validate Codex CLI live benchmark reports and published summaries."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from codex_live_benchmark_lib import (
    CASE_TIERS,
    CODEX_LIVE_CAPABILITY_COVERAGE_NAME,
    CODEX_LIVE_EVIDENCE_SCOPES,
    CODEX_LIVE_LEGACY_BENCHMARK_NAME,
    CODEX_LIVE_PASS_RATE_BENCHMARK_NAME,
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
    codex_live_capability_coverage_status,
    codex_live_evidence_scope_ready,
    codex_live_logging_redaction_errors,
    codex_live_pass_rate_status,
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
CODEX_LIVE_EVIDENCE_KEY = "local_codex_cli_live_benchmark"
REPORT_STATUSES = ("pass", "partial", "fail", "unknown", "not_collected")


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
        for log_file in ("run.log.jsonl", "timeline.jsonl"):
            if not (run_dir / log_file).exists():
                errors.append(f"live run manifest is missing {log_file}")
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
            if not (case_dir / "process-trace.json").exists():
                errors.append(f"{case_dir}: missing required result artifact process-trace.json")
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
    if isinstance(detail, dict) and summary.get("evidence_scope_ready") != detail.get("evidence_scope_ready"):
        errors.append("summary evidence_scope_ready must match evidence_scope_detail.evidence_scope_ready")
    if publishable:
        errors.extend(_strict_summary_errors(summary))
    if "limitations" not in summary or not summary.get("limitations"):
        errors.append("summary limitations are required")
    errors.extend(_variant_rate_errors(summary))
    errors.extend(_summary_structure_errors(summary))
    return errors


def validate_report_consistency(
    summary_path: Path,
    *,
    scorecard_path: Path | None = None,
    public_summary_path: Path | None = None,
    dashboard_path: Path | None = None,
    readme_path: Path | None = None,
) -> list[str]:
    """Validate that generated scorecard/public reports reference the live summary."""
    summary = read_json(summary_path)
    if not isinstance(summary, dict):
        return [f"{summary_path} missing or invalid"]
    errors: list[str] = []
    root = summary_path.parent.parent
    scorecard_report = read_json(scorecard_path) if scorecard_path is not None else None
    public_report = read_json(public_summary_path) if public_summary_path is not None else None
    errors.extend(_report_evidence_consistency_errors(summary_path, summary))
    if summary_path.name == "codex-live-benchmark-summary.json" and summary.get("evidence_scope") == "smoke":
        errors.append("canonical codex-live-benchmark-summary.json cannot contain a collected smoke artifact")
    if scorecard_path is not None:
        errors.extend(
            _derived_live_report_errors(
                summary,
                scorecard_path,
                report_kind="scorecard",
                item_collection="dimensions",
            )
        )
        errors.extend(_derived_markdown_report_errors(summary, scorecard_path.with_suffix(".md"), "scorecard"))
        errors.extend(_scorecard_markdown_count_errors(scorecard_path, scorecard_report))
    if public_summary_path is not None:
        errors.extend(
            _derived_live_report_errors(
                summary,
                public_summary_path,
                report_kind="public summary",
                item_collection="items",
            )
        )
        errors.extend(
            _derived_markdown_report_errors(summary, public_summary_path.with_suffix(".md"), "public summary")
        )
        errors.extend(_public_markdown_count_errors(public_summary_path, public_report))
    if isinstance(scorecard_report, dict) and isinstance(public_report, dict):
        errors.extend(_codex_public_scorecard_status_errors(scorecard_report, public_report))
    dashboard = dashboard_path or root / "docs" / "SCORECARD_DASHBOARD.md"
    if isinstance(scorecard_report, dict) and dashboard.exists():
        errors.extend(_dashboard_count_errors(dashboard, scorecard_report))
    readme = readme_path or root / "README.md"
    if isinstance(scorecard_report, dict) and readme.exists():
        errors.extend(_readme_profile_count_errors(readme, scorecard_report, root))
        if dashboard.exists():
            errors.extend(_readme_dashboard_summary_errors(readme, dashboard))
    return errors


def _report_evidence_consistency_errors(summary_path: Path, summary: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    coverage = summary.get("coverage_summary")
    if isinstance(coverage, dict):
        registered_count = coverage.get("registered_live_case_count")
        actual_count = coverage.get("actual_run_case_count")
        registered_rate = coverage.get("registered_case_coverage_rate")
        actual_rate = coverage.get("actual_run_case_coverage_rate")
        registered_but_not_run = coverage.get("registered_but_not_run_cases")
        if (
            isinstance(registered_but_not_run, list)
            and registered_but_not_run
            and isinstance(registered_count, int)
            and isinstance(actual_count, int)
            and registered_count != actual_count
            and registered_rate == actual_rate
        ):
            errors.append(
                "coverage_summary registered_case_coverage_rate must not mirror actual_run_case_coverage_rate when registered-but-not-run cases exist"
            )
        if (
            isinstance(registered_but_not_run, list)
            and registered_but_not_run
            and registered_count == actual_count
        ):
            errors.append(
                "coverage_summary registered_live_case_count cannot equal actual_run_case_count when registered_but_not_run_cases is non-empty"
            )

    benchmark_mode = str(summary.get("benchmark_mode") or summary.get("run_mode") or "").casefold()
    dry_run = bool(summary.get("dry_run")) or "dry" in benchmark_mode
    if dry_run and summary.get("evidence_level") == LIVE_EVIDENCE_LEVEL:
        errors.append("dry-run benchmark summaries cannot claim live benchmark evidence_level")

    capability_summary = summary.get("capability_coverage_summary")
    if isinstance(capability_summary, dict) and capability_summary.get("status") == "pass":
        items = capability_summary.get("items") if isinstance(capability_summary.get("items"), list) else []
        failed = [
            str(item.get("id") or item.get("capability") or "unknown")
            for item in items
            if isinstance(item, dict) and item.get("status") in {"fail", "blocked"}
        ]
        if failed:
            errors.append(
                "capability_coverage_summary.status cannot be pass when capability items failed: "
                + ", ".join(sorted(failed))
            )

    improvement = summary.get("quality_improvement_summary")
    if isinstance(improvement, dict) and _has_improvement_claim(summary, improvement):
        actual_cases = summary.get("actual_run_cases")
        if not isinstance(actual_cases, list) or not actual_cases:
            errors.append("quality improvement claims require actual_run_cases evidence")
        if not isinstance(summary.get("run_id"), str) or not summary.get("run_id").strip():
            errors.append("quality improvement claims require a run_id")
        if not isinstance(summary.get("generated_by"), str) or not summary.get("generated_by").strip():
            errors.append("quality improvement claims require generated_by command provenance")
        if isinstance(coverage, dict) and int(coverage.get("actual_run_case_count", 0) or 0) <= 0:
            errors.append("quality improvement claims require actual_run_case_count > 0")

    if summary_path.name == "codex-live-benchmark-summary.json":
        generated_by = summary.get("generated_by")
        if not isinstance(generated_by, str) or not generated_by.startswith("scripts/"):
            errors.append("canonical codex-live-benchmark-summary.json must include generated_by script provenance")
    return errors


def _has_improvement_claim(summary: dict[str, Any], improvement: dict[str, Any]) -> bool:
    for key, value in improvement.items():
        if key.endswith("_claim") and value is True:
            return True
    positive_verdicts = {"improved", "positive", "pass", "win"}
    return (
        str(summary.get("effect_verdict") or "").casefold() in positive_verdicts
        or str(summary.get("effect_status") or "").casefold() in positive_verdicts
    )


def _default_existing_derived_report_paths(summary_path: Path) -> tuple[Path | None, Path | None]:
    reports_dir = summary_path.parent
    scorecard = reports_dir / "professional-scorecard.json"
    public_summary = reports_dir / "public-benchmark-summary.json"
    return (
        scorecard if scorecard.exists() else None,
        public_summary if public_summary.exists() else None,
    )


def _scorecard_markdown_count_errors(scorecard_path: Path, report: Any) -> list[str]:
    if not isinstance(report, dict):
        return []
    if not scorecard_path.with_suffix(".md").exists():
        return []
    expected = _normal_counts(report.get("status_summary") or _status_counts_from_items(report.get("dimensions")))
    actual = _markdown_status_counts(scorecard_path.with_suffix(".md"))
    return _count_compare_errors("professional-scorecard.json", "professional-scorecard.md", expected, actual)


def _public_markdown_count_errors(public_path: Path, report: Any) -> list[str]:
    if not isinstance(report, dict):
        return []
    if not public_path.with_suffix(".md").exists():
        return []
    expected = _normal_counts(report.get("status_counts") or _status_counts_from_items(report.get("items")))
    actual = _markdown_status_counts(public_path.with_suffix(".md"))
    return _count_compare_errors("public-benchmark-summary.json", "public-benchmark-summary.md", expected, actual)


def _dashboard_count_errors(dashboard_path: Path, scorecard_report: dict[str, Any]) -> list[str]:
    expected = _normal_counts(scorecard_report.get("status_summary") or _status_counts_from_items(scorecard_report.get("dimensions")))
    actual = _markdown_status_counts(dashboard_path)
    return _count_compare_errors("professional-scorecard.json", "SCORECARD_DASHBOARD.md", expected, actual)


def _codex_public_scorecard_status_errors(
    scorecard_report: dict[str, Any],
    public_report: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    for name in (CODEX_LIVE_PASS_RATE_BENCHMARK_NAME, CODEX_LIVE_CAPABILITY_COVERAGE_NAME):
        scorecard_item = _find_live_report_item(scorecard_report.get("dimensions"), name)
        public_item = _find_live_report_item(public_report.get("items"), name)
        if not isinstance(scorecard_item, dict) or not isinstance(public_item, dict):
            continue
        if scorecard_item.get("status") != public_item.get("status"):
            errors.append(
                f"public summary {name} status {public_item.get('status')!r} "
                f"does not match scorecard {scorecard_item.get('status')!r}"
            )
    return errors


def _readme_profile_count_errors(readme_path: Path, scorecard_report: dict[str, Any], root: Path) -> list[str]:
    text = readme_path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"Stable profile counts are `?recommended=(\d+)`?, `?full=(\d+)`?, and `?dev=(\d+)`?", text)
    if not match:
        return ["README stable profile counts sentence is missing"]
    readme_counts = {
        "recommended": int(match.group(1)),
        "full": int(match.group(2)),
        "dev": int(match.group(3)),
    }
    expected = _scorecard_profile_counts(scorecard_report)
    errors: list[str] = []
    if expected and readme_counts != expected:
        errors.append(f"README profile counts {readme_counts} do not match scorecard profile counts {expected}")
    manifest_counts = _build_manifest_profile_counts(root)
    if manifest_counts and readme_counts != manifest_counts:
        errors.append(f"README profile counts {readme_counts} do not match build manifests {manifest_counts}")
    if expected and manifest_counts and expected != manifest_counts:
        errors.append(f"scorecard profile counts {expected} do not match build manifests {manifest_counts}")
    return errors


def _readme_dashboard_summary_errors(readme_path: Path, dashboard_path: Path) -> list[str]:
    readme_statuses = _table_statuses(readme_path.read_text(encoding="utf-8", errors="ignore"))
    dashboard_statuses = _table_statuses(dashboard_path.read_text(encoding="utf-8", errors="ignore"))
    errors: list[str] = []
    for label, status in readme_statuses.items():
        dashboard_status = dashboard_statuses.get(label)
        if dashboard_status is not None and dashboard_status != status:
            errors.append(
                f"README scorecard summary {label} status {status!r} does not match dashboard {dashboard_status!r}"
            )
    return errors


def _normal_counts(value: Any) -> dict[str, int]:
    counts = {status: 0 for status in REPORT_STATUSES}
    if isinstance(value, dict):
        for status in REPORT_STATUSES:
            raw = value.get(status, 0)
            counts[status] = int(raw) if isinstance(raw, int) else 0
    return counts


def _status_counts_from_items(items: Any) -> dict[str, int]:
    counts = {status: 0 for status in REPORT_STATUSES}
    if not isinstance(items, list):
        return counts
    for item in items:
        status = item.get("status") if isinstance(item, dict) else None
        counts[status if status in counts else "unknown"] += 1
    return counts


def _markdown_status_counts(path: Path) -> dict[str, int] | None:
    if not path.exists():
        return None
    counts: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = re.match(r"- `(?P<status>pass|partial|fail|unknown|not_collected)`: (?P<count>\d+)$", line.strip())
        if match:
            counts[match.group("status")] = int(match.group("count"))
    if not counts:
        return None
    return _normal_counts(counts)


def _count_compare_errors(
    expected_label: str,
    actual_label: str,
    expected: dict[str, int],
    actual: dict[str, int] | None,
) -> list[str]:
    if actual is None:
        return [f"{actual_label} status counts are missing"]
    if expected != actual:
        return [f"{actual_label} status counts {actual} do not match {expected_label} {expected}"]
    return []


def _table_statuses(text: str) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for line in text.splitlines():
        if not line.startswith("|") or "`" not in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 2 or cells[0] in {"Evidence", "Area", "---"}:
            continue
        match = re.search(r"`(pass|partial|fail|unknown|not_collected)`", cells[1])
        if match:
            statuses[cells[0]] = match.group(1)
    return statuses


def _scorecard_profile_counts(scorecard_report: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    profile_counts = scorecard_report.get("profile_counts")
    if not isinstance(profile_counts, dict):
        return counts
    for profile in ("recommended", "full", "dev"):
        detail = profile_counts.get(profile)
        text = str(detail.get("detail", "")) if isinstance(detail, dict) else ""
        match = re.search(r"top-level count is (\d+)", text)
        if match:
            counts[profile] = int(match.group(1))
    return counts


def _build_manifest_profile_counts(root: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for profile in ("recommended", "full", "dev"):
        manifest = read_json(root / "dist" / "universal" / "skills" / profile / ".changeforge-build-manifest.json")
        if isinstance(manifest, dict) and isinstance(manifest.get("top_level_skills"), list):
            counts[profile] = len(manifest["top_level_skills"])
    return counts


def _derived_live_report_errors(
    summary: dict[str, Any],
    report_path: Path,
    *,
    report_kind: str,
    item_collection: str,
) -> list[str]:
    report = read_json(report_path)
    if not isinstance(report, dict):
        return [f"{report_kind} {report_path} missing or invalid"]
    errors: list[str] = []
    expected_statuses: list[str] = []
    for name, status_func in (
        (CODEX_LIVE_PASS_RATE_BENCHMARK_NAME, codex_live_pass_rate_status),
        (CODEX_LIVE_CAPABILITY_COVERAGE_NAME, codex_live_capability_coverage_status),
    ):
        item = _find_live_report_item(report.get(item_collection), name)
        if item is None:
            errors.append(f"{report_kind} missing {name} item")
            continue
        expected_status, strict_errors, readiness_warnings = status_func(summary)
        expected_statuses.append(expected_status)
        errors.extend(
            _derived_live_report_item_errors(
                summary,
                item,
                report_kind=report_kind,
                item_name=name,
                expected_status=expected_status,
                strict_errors=strict_errors,
                readiness_warnings=readiness_warnings,
            )
        )
    if expected_statuses and report_kind in {"public summary", "scorecard"}:
        evidence_level = (report.get("evidence_levels") or {}).get(CODEX_LIVE_EVIDENCE_KEY)
        evidence_status = evidence_level.get("status") if isinstance(evidence_level, dict) else None
        expected_evidence_status = _weaker_status(*expected_statuses)
        if evidence_status is not None and evidence_status != expected_evidence_status:
            errors.append(
                f"{report_kind} evidence_levels.{CODEX_LIVE_EVIDENCE_KEY}.status "
                f"{evidence_status!r} does not match combined live evidence status "
                f"{expected_evidence_status!r}"
            )
    return errors


def _derived_live_report_item_errors(
    summary: dict[str, Any],
    item: dict[str, Any],
    *,
    report_kind: str,
    item_name: str,
    expected_status: str,
    strict_errors: list[str],
    readiness_warnings: list[str],
) -> list[str]:
    errors: list[str] = []
    detail = _load_item_detail(item, report_kind)
    item_status = item.get("status")
    if item_status != expected_status:
        errors.append(
            f"{report_kind} {item_name} status {item_status!r} "
            f"does not match strict evidence status {expected_status!r}"
        )
    if not isinstance(detail, dict):
        errors.append(f"{report_kind} {item_name} detail must be JSON object")
        return errors
    for field in ("run_id", "effect_verdict"):
        if detail.get(field) != summary.get(field):
            errors.append(
                f"{report_kind} {item_name} detail {field} "
                f"{detail.get(field)!r} does not match summary {summary.get(field)!r}"
            )
    if detail.get("evidence_status") != expected_status:
        errors.append(
            f"{report_kind} {item_name} detail evidence_status "
            f"{detail.get('evidence_status')!r} does not match strict evidence status {expected_status!r}"
        )
    if item_status == "pass" and strict_errors:
        errors.append(f"{report_kind} cannot show pass while strict artifact errors exist: {strict_errors}")
    if item_status == "pass" and readiness_warnings:
        errors.append(f"{report_kind} cannot show pass while readiness warnings exist: {readiness_warnings}")
    if item_status == "pass" and summary.get("evidence_scope") == "smoke":
        errors.append(f"{report_kind} cannot show pass for smoke Codex live benchmark evidence")
    if item_status == "pass" and codex_live_evidence_scope_ready(summary) is not True:
        errors.append(f"{report_kind} cannot show pass when evidence_scope_ready=false")
    if item_status == "pass" and (
        summary.get("effect_status") == "inconclusive" or summary.get("effect_verdict") == "inconclusive"
    ):
        errors.append(f"{report_kind} cannot show pass when effect_status/effect_verdict is inconclusive")
    if summary.get("effect_verdict") == "positive" and detail.get("effect_verdict") != "positive":
        errors.append(f"{report_kind} cannot reference a non-positive live result when summary effect_verdict is positive")
    for field in ("benchmark_passed_result_count", "benchmark_eligible_result_count"):
        if detail.get(field) != summary.get(field):
            errors.append(
                f"{report_kind} {item_name} detail {field} "
                f"{detail.get(field)!r} does not match summary {summary.get(field)!r}"
            )
    detail_hooks_rate = _variant_pass_rate(detail, "skills_with_hooks_clean")
    summary_hooks_rate = _variant_pass_rate(summary, "skills_with_hooks_clean")
    if detail_hooks_rate != summary_hooks_rate:
        errors.append(
            f"{report_kind} {item_name} detail "
            f"skills_with_hooks_clean.pass_rate {detail_hooks_rate!r} "
            f"does not match summary {summary_hooks_rate!r}"
        )
    return errors


def _derived_markdown_report_errors(summary: dict[str, Any], report_path: Path, report_kind: str) -> list[str]:
    if not report_path.exists():
        return []
    text = report_path.read_text(encoding="utf-8", errors="ignore")
    live_names = (
        CODEX_LIVE_PASS_RATE_BENCHMARK_NAME,
        CODEX_LIVE_CAPABILITY_COVERAGE_NAME,
        CODEX_LIVE_LEGACY_BENCHMARK_NAME,
    )
    if not any(name in text for name in live_names):
        return []
    errors: list[str] = []
    run_id = str(summary.get("run_id") or "")
    if ("run_id" in text or "Run id" in text) and run_id and run_id not in text:
        errors.append(f"{report_kind} markdown {report_path} does not reference current live run_id {run_id!r}")
    for stale_run_id in _live_run_ids_in_markdown(text):
        if run_id and stale_run_id != run_id:
            errors.append(
                f"{report_kind} markdown {report_path} references stale live run_id "
                f"{stale_run_id!r}; expected {run_id!r}"
            )
    effect_verdict = str(summary.get("effect_verdict") or "")
    if "effect_verdict" in text and effect_verdict and effect_verdict not in text:
        errors.append(
            f"{report_kind} markdown {report_path} does not reference current effect_verdict {effect_verdict!r}"
        )
    evidence_status = str(summary.get("evidence_status") or "")
    if "evidence_status" in text and evidence_status and evidence_status not in text:
        errors.append(
            f"{report_kind} markdown {report_path} does not reference current evidence_status {evidence_status!r}"
        )
    for field in ("benchmark_passed_result_count", "benchmark_eligible_result_count"):
        expected = summary.get(field)
        if field in text and expected is not None and str(expected) not in text:
            errors.append(f"{report_kind} markdown {report_path} does not reference current {field} {expected!r}")
    hooks_rate = _variant_pass_rate(summary, "skills_with_hooks_clean")
    if "skills_with_hooks_clean" in text and "pass_rate" in text and hooks_rate is not None and str(hooks_rate) not in text:
        errors.append(
            f"{report_kind} markdown {report_path} does not reference current "
            f"skills_with_hooks_clean.pass_rate {hooks_rate!r}"
        )
    return errors


def _live_run_ids_in_markdown(text: str) -> set[str]:
    run_ids: set[str] = set()
    for line in text.splitlines():
        if (
            CODEX_LIVE_LEGACY_BENCHMARK_NAME not in line
            and CODEX_LIVE_PASS_RATE_BENCHMARK_NAME not in line
            and CODEX_LIVE_CAPABILITY_COVERAGE_NAME not in line
            and "local_codex_cli_live_benchmark" not in line
            and "run_id" not in line
        ):
            continue
        for marker in ('"run_id": "', "'run_id': '", "run_id="):
            if marker not in line:
                continue
            remainder = line.split(marker, 1)[1]
            delimiter = '"' if '"' in marker else "'" if "'" in marker else " "
            value = remainder.split(delimiter, 1)[0].strip()
            if value:
                run_ids.add(value)
    return run_ids


def _find_live_report_item(items: Any, name: str) -> dict[str, Any] | None:
    if not isinstance(items, list):
        return None
    for item in items:
        if isinstance(item, dict) and item.get("name") == name:
            return item
    return None


def _weaker_status(*statuses: str) -> str:
    order = ("fail", "partial", "not_collected", "unknown", "pass")
    cleaned = [status if status in REPORT_STATUSES else "unknown" for status in statuses]
    for status in order:
        if status in cleaned:
            return status
    return "unknown"


def _load_item_detail(item: dict[str, Any], report_kind: str) -> dict[str, Any] | None:
    detail_data = item.get("detail_data")
    if isinstance(detail_data, dict):
        return detail_data
    detail = item.get("detail")
    if isinstance(detail, dict):
        return detail
    if not isinstance(detail, str):
        return None
    try:
        payload = json.loads(detail)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _variant_pass_rate(payload: dict[str, Any], variant: str) -> Any:
    variants = payload.get("variants")
    variant_payload = variants.get(variant) if isinstance(variants, dict) else None
    if not isinstance(variant_payload, dict):
        return None
    return variant_payload.get("pass_rate")


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
    if not isinstance(summary.get("logging_summary"), dict):
        errors.append("strict summary requires logging_summary")
    errors.extend(codex_live_logging_redaction_errors(summary))
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
    errors.extend(_coverage_summary_errors(summary.get("coverage_summary")))
    if "cost_summary" in summary:
        errors.extend(_cost_summary_errors(summary.get("cost_summary")))
    if "stability_summary" in summary:
        errors.extend(_stability_summary_errors(summary.get("stability_summary")))
    if "logging_summary" in summary:
        errors.extend(_logging_summary_errors(summary.get("logging_summary")))
    if "process_compliance_summary" in summary:
        errors.extend(_process_compliance_summary_errors(summary.get("process_compliance_summary")))
    errors.extend(_capability_semantic_errors(summary))
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


def _capability_semantic_errors(summary: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    capability = summary.get("capability_coverage_summary")
    if not isinstance(capability, dict):
        return errors
    items = capability.get("items") if isinstance(capability.get("items"), list) else []
    compact_summary = summary.get("compact_context_summary") if isinstance(summary.get("compact_context_summary"), dict) else {}
    process = (
        summary.get("process_compliance_summary")
        if isinstance(summary.get("process_compliance_summary"), dict)
        else {}
    )
    process_trace_count = process.get("process_trace_count")
    for item in items:
        if not isinstance(item, dict) or item.get("status") != "pass":
            continue
        capability_id = str(item.get("id") or "")
        if item.get("run_status") != "run":
            errors.append(f"capability {capability_id} cannot pass when linked cases were not run")
        case_results = item.get("case_results") if isinstance(item.get("case_results"), list) else []
        for case in case_results:
            if isinstance(case, dict) and case.get("run_status") != "run":
                errors.append(
                    f"capability {capability_id} cannot pass with linked case "
                    f"{case.get('case_id')} run_status={case.get('run_status')}"
                )
        if capability_id == "context_compaction_retention":
            if compact_summary.get("run_status") != "run":
                errors.append("context_compaction_retention cannot pass when compact case was not run")
            if int(compact_summary.get("compact_runtime_evidence_count", 0) or 0) <= 0:
                errors.append("context_compaction_retention cannot pass without compact runtime evidence")
            if int(compact_summary.get("pre_compact_snapshot_count", 0) or 0) <= 0:
                errors.append("context_compaction_retention cannot pass without pre_compact snapshots")
            reinject_count = int(compact_summary.get("post_compact_reinject_count", 0) or 0) + int(
                compact_summary.get("session_compact_reinject_count", 0) or 0
            )
            if reinject_count <= 0:
                errors.append("context_compaction_retention cannot pass without post/session compact reinject evidence")
        if capability_id == "pdd_ddd_sdd_tdd_review_flow":
            if not isinstance(process_trace_count, int) or process_trace_count <= 0:
                errors.append("pdd_ddd_sdd_tdd_review_flow cannot pass when process_trace_count is zero or not_collected")
    return errors


def _coverage_summary_errors(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ["summary coverage_summary must be an object"]
    errors: list[str] = []
    for field in (
        "case_count",
        "assertion_case_count",
        "telemetry_only_case_count",
        "publishable_assertion_case_count",
        "unregistered_case_count",
        "manifest_category_count",
        "manifest_case_count",
        "registered_live_case_count",
        "registered_assertion_case_count",
        "registered_telemetry_only_case_count",
        "registered_publishable_assertion_case_count",
        "registered_category_count",
        "actual_run_case_count",
        "actual_run_assertion_case_count",
        "actual_run_publishable_assertion_case_count",
        "actual_run_category_count",
    ):
        if not isinstance(payload.get(field), int):
            errors.append(f"summary coverage_summary.{field} must be an integer")
    for field in ("registered_case_coverage_rate", "registered_publishable_case_coverage_rate", "actual_run_case_coverage_rate"):
        value = payload.get(field)
        if not isinstance(value, int | float) or value < 0 or value > 1:
            errors.append(f"summary coverage_summary.{field} must be a numeric rate from 0 to 1")
    for field in ("tiers", "tiers_registered", "tiers_run"):
        tiers = payload.get(field)
        if not isinstance(tiers, dict):
            errors.append(f"summary coverage_summary.{field} must be an object")
        else:
            invalid_tiers = sorted(set(str(tier) for tier in tiers) - {*CASE_TIERS, "unregistered"})
            if invalid_tiers:
                errors.append(f"summary coverage_summary.{field} has invalid tiers {', '.join(invalid_tiers)}")
            errors.extend(_int_count_errors(f"summary coverage_summary.{field}", tiers))
    for field in (
        "categories",
        "coverage_dimensions",
        "categories_registered",
        "publishable_categories_registered",
        "coverage_dimensions_registered",
        "categories_run",
        "coverage_dimensions_run",
    ):
        value = payload.get(field)
        if not isinstance(value, dict):
            errors.append(f"summary coverage_summary.{field} must be an object")
        else:
            errors.extend(_int_count_errors(f"summary coverage_summary.{field}", value))
    for field in ("manifest_categories", "registered_but_not_run_cases", "missing_manifest_categories"):
        value = payload.get(field)
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            errors.append(f"summary coverage_summary.{field} must be a list of strings")
    if not errors:
        registered_live = payload["registered_live_case_count"]
        registered_publishable = payload["registered_publishable_assertion_case_count"]
        actual_run = payload["actual_run_case_count"]
        actual_publishable = payload["actual_run_publishable_assertion_case_count"]
        missing_publishable = payload["registered_but_not_run_cases"]
        if registered_publishable > registered_live:
            errors.append(
                "summary coverage_summary.registered_publishable_assertion_case_count cannot exceed registered_live_case_count"
            )
        if actual_publishable > actual_run:
            errors.append(
                "summary coverage_summary.actual_run_publishable_assertion_case_count cannot exceed actual_run_case_count"
            )
        if actual_publishable > registered_publishable:
            errors.append(
                "summary coverage_summary.actual_run_publishable_assertion_case_count cannot exceed registered_publishable_assertion_case_count"
            )
        expected_missing_count = registered_publishable - actual_publishable
        if expected_missing_count < 0:
            expected_missing_count = 0
        if len(missing_publishable) != expected_missing_count:
            errors.append(
                "summary coverage_summary.registered_but_not_run_cases count must equal "
                "registered_publishable_assertion_case_count - actual_run_publishable_assertion_case_count"
            )
        if actual_publishable < registered_publishable and not missing_publishable:
            errors.append(
                "summary coverage_summary.registered_but_not_run_cases must list missing publishable assertion cases"
            )
        if actual_publishable == registered_publishable and missing_publishable:
            errors.append(
                "summary coverage_summary.registered_but_not_run_cases must be empty when all publishable assertion cases ran"
            )
    return errors


def _cost_summary_errors(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ["summary cost_summary must be an object"]
    errors: list[str] = []
    if not isinstance(payload.get("result_count"), int):
        errors.append("summary cost_summary.result_count must be an integer")
    for field in ("total_usage", "average_usage_per_result"):
        errors.extend(_usage_payload_errors(f"summary cost_summary.{field}", payload.get(field)))
    by_variant = payload.get("by_variant")
    if not isinstance(by_variant, dict):
        errors.append("summary cost_summary.by_variant must be an object")
    else:
        for variant, variant_payload in by_variant.items():
            if not isinstance(variant_payload, dict):
                errors.append(f"summary cost_summary.by_variant.{variant} must be an object")
                continue
            if not isinstance(variant_payload.get("result_count"), int):
                errors.append(f"summary cost_summary.by_variant.{variant}.result_count must be an integer")
            for field in ("total_usage", "average_usage_per_result", "median_usage_per_result"):
                errors.extend(
                    _usage_payload_errors(
                        f"summary cost_summary.by_variant.{variant}.{field}",
                        variant_payload.get(field),
                    )
                )
            for field in ("pass_rate_per_100k_input_tokens", "pass_rate_per_100_commands"):
                value = variant_payload.get(field)
                if not (isinstance(value, int | float) or value == "not_collected"):
                    errors.append(
                        f"summary cost_summary.by_variant.{variant}.{field} must be numeric or not_collected"
                    )
    cost_adjusted_delta = payload.get("cost_adjusted_delta")
    if not isinstance(cost_adjusted_delta, dict):
        errors.append("summary cost_summary.cost_adjusted_delta must be an object")
    else:
        for key, value in cost_adjusted_delta.items():
            if not isinstance(key, str) or not isinstance(value, dict):
                errors.append(f"summary cost_summary.cost_adjusted_delta.{key} must be an object")
                continue
            if value.get("status") not in {"collected", "not_collected"}:
                errors.append(f"summary cost_summary.cost_adjusted_delta.{key}.status is invalid")
            if value.get("status") == "collected" and not isinstance(value.get("cost_efficiency_note"), str):
                errors.append(f"summary cost_summary.cost_adjusted_delta.{key}.cost_efficiency_note must be a string")
    if not isinstance(payload.get("case_cost_outliers"), list):
        errors.append("summary cost_summary.case_cost_outliers must be a list")
    if not isinstance(payload.get("cost_caveat"), str):
        errors.append("summary cost_summary.cost_caveat must be a string")
    return errors


def _stability_summary_errors(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ["summary stability_summary must be an object"]
    errors: list[str] = []
    for field in (
        "requested_runs_per_variant",
        "observed_case_variant_cell_count",
        "observed_min_runs_per_case_variant",
        "observed_max_runs_per_case_variant",
        "codex_exec_retry_count",
        "case_regression_count",
    ):
        if not isinstance(payload.get(field), int):
            errors.append(f"summary stability_summary.{field} must be an integer")
    for field in (
        "artifact_status_counts",
        "grading_status_counts",
        "codex_exec_failed_by_case",
        "codex_exec_retries_by_case",
        "failed_run_reasons_by_case",
    ):
        value = payload.get(field)
        if not isinstance(value, dict):
            errors.append(f"summary stability_summary.{field} must be an object")
        elif field in {"artifact_status_counts", "grading_status_counts"}:
            errors.extend(_int_count_errors(f"summary stability_summary.{field}", value))
    for field in ("flaky_case_variant_cells", "skills_with_hooks_regression_cases", "partial_status_reasons"):
        if not isinstance(payload.get(field), list):
            errors.append(f"summary stability_summary.{field} must be a list")
    for field in (
        "setup_failure_rate",
        "test_suite_failure_rate",
        "codex_exec_failure_rate",
        "not_collected_grading_rate",
        "contamination_rate",
    ):
        value = payload.get(field)
        if not isinstance(value, int | float) or value < 0 or value > 1:
            errors.append(f"summary stability_summary.{field} must be a numeric rate from 0 to 1")
    for field in (
        "security_assertion_failure_rate",
        "security_check_execution_failure_rate",
        "security_failure_rate",
    ):
        value = payload.get(field)
        if not (isinstance(value, int | float) and 0 <= float(value) <= 1) and value != "not_collected":
            errors.append(f"summary stability_summary.{field} must be a numeric rate from 0 to 1 or not_collected")
    definition = payload.get("security_failure_rate_definition")
    if definition is not None and not isinstance(definition, str):
        errors.append("summary stability_summary.security_failure_rate_definition must be a string")
    return errors


def _logging_summary_errors(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ["summary logging_summary must be an object"]
    errors: list[str] = []
    for field in (
        "run_log_events",
        "timeline_events",
        "process_trace_count",
        "redaction_error_count",
        "redaction_error_artifact_count",
        "max_event_size_bytes",
    ):
        value = payload.get(field)
        if not isinstance(value, int) or value < 0:
            errors.append(f"summary logging_summary.{field} must be a non-negative integer")
    redaction_status = payload.get("redaction_status")
    if redaction_status not in {"pass", "fail"}:
        errors.append("summary logging_summary.redaction_status must be pass or fail")
    redaction_error_count = payload.get("redaction_error_count")
    if not isinstance(redaction_error_count, int):
        redaction_error_count = 0
    redaction_error_artifact_count = payload.get("redaction_error_artifact_count")
    if not isinstance(redaction_error_artifact_count, int):
        redaction_error_artifact_count = 0
    redaction_error_markers = payload.get("redaction_error_markers")
    if not isinstance(redaction_error_markers, list):
        redaction_error_markers = []
    redaction_error_artifacts = payload.get("redaction_error_artifacts")
    if not isinstance(redaction_error_artifacts, list):
        redaction_error_artifacts = []
    for field in ("redaction_error_markers", "redaction_error_artifacts"):
        value = payload.get(field)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            errors.append(f"summary logging_summary.{field} must be a list of strings")
    if not isinstance(payload.get("redaction_error_artifacts_truncated"), bool):
        errors.append("summary logging_summary.redaction_error_artifacts_truncated must be a boolean")
    for field in (
        "first_redaction_error_artifact",
        "first_redaction_error_marker",
        "first_redaction_error_excerpt_hash",
    ):
        value = payload.get(field)
        if value is not None and not isinstance(value, str):
            errors.append(f"summary logging_summary.{field} must be a string or null")
    if redaction_status == "pass":
        if redaction_error_count != 0:
            errors.append("summary logging_summary.redaction_error_count must be 0 when redaction_status is pass")
        if redaction_error_artifact_count != 0:
            errors.append(
                "summary logging_summary.redaction_error_artifact_count must be 0 when redaction_status is pass"
            )
        if redaction_error_markers:
            errors.append("summary logging_summary.redaction_error_markers must be empty when redaction_status is pass")
        if redaction_error_artifacts:
            errors.append("summary logging_summary.redaction_error_artifacts must be empty when redaction_status is pass")
    if redaction_status == "fail":
        if redaction_error_count <= 0:
            errors.append("summary logging_summary.redaction_error_count must be positive when redaction_status is fail")
        if not redaction_error_markers and not redaction_error_artifacts:
            errors.append(
                "summary logging_summary.redaction_error_markers or redaction_error_artifacts are required when redaction_status is fail"
            )
        excerpt_hash = payload.get("first_redaction_error_excerpt_hash")
        if not isinstance(excerpt_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", excerpt_hash):
            errors.append(
                "summary logging_summary.first_redaction_error_excerpt_hash must be a sha256 hex string when redaction_status is fail"
            )
    return errors


def _process_compliance_summary_errors(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ["summary process_compliance_summary must be an object"]
    errors: list[str] = []
    for field in (
        "pdd_present_rate",
        "ddd_present_rate",
        "sdd_present_rate",
        "tdd_present_rate",
        "pdd_inferred_rate",
        "ddd_inferred_rate",
        "sdd_inferred_rate",
        "tdd_inferred_rate",
        "pdd_degraded_rate",
        "ddd_degraded_rate",
        "sdd_degraded_rate",
        "tdd_degraded_rate",
        "pdd_required_field_fallback_rate",
        "ddd_required_field_fallback_rate",
        "sdd_required_field_fallback_rate",
        "tdd_required_field_fallback_rate",
        "all_core_phases_present_rate",
        "all_core_phases_degraded_or_present_rate",
        "all_core_phases_inferred_only_rate",
        "pdd_to_tdd_traceability_rate",
        "ddd_invariant_test_or_code_coverage_rate",
        "sdd_public_api_validation_rate",
        "sdd_failure_mode_validation_rate",
        "sdd_logging_validation_rate",
        "validation_command_present_rate",
        "required_field_fallback_rate",
        "process_trace_inferred_only_rate",
    ):
        value = payload.get(field)
        if not isinstance(value, int | float) or value < 0 or value > 1:
            errors.append(f"summary process_compliance_summary.{field} must be a numeric rate from 0 to 1")
    trace_count = payload.get("process_trace_count")
    if not isinstance(trace_count, int) or trace_count < 0:
        errors.append("summary process_compliance_summary.process_trace_count must be a non-negative integer")
    return errors


def _usage_payload_errors(label: str, payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return [f"{label} must be an object"]
    errors: list[str] = []
    for field in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens"):
        value = payload.get(field)
        if not isinstance(value, int | float):
            errors.append(f"{label}.{field} must be numeric")
    return errors


def _int_count_errors(label: str, payload: dict[Any, Any]) -> list[str]:
    errors: list[str] = []
    for key, value in payload.items():
        if not isinstance(key, str):
            errors.append(f"{label} keys must be strings")
        if not isinstance(value, int):
            errors.append(f"{label}.{key} must be an integer")
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
    parser.add_argument("--scorecard", type=Path)
    parser.add_argument("--public-summary", type=Path)
    args = parser.parse_args(argv)
    if not args.run_dir and not args.summary:
        print("validate-codex-live-benchmark-reports: ERROR: --run-dir or --summary is required", file=sys.stderr)
        return 2
    errors: list[str] = []
    if args.run_dir:
        errors.extend(validate_run_dir(args.run_dir))
    if args.summary:
        errors.extend(validate_summary(args.summary))
        scorecard_path = args.scorecard
        public_summary_path = args.public_summary
        if (
            args.summary.name == "codex-live-benchmark-summary.json"
            and scorecard_path is None
            and public_summary_path is None
        ):
            scorecard_path, public_summary_path = _default_existing_derived_report_paths(args.summary)
        errors.extend(
            validate_report_consistency(
                args.summary,
                scorecard_path=scorecard_path,
                public_summary_path=public_summary_path,
            )
        )
    return print_errors("validate-codex-live-benchmark-reports", errors)


if __name__ == "__main__":
    sys.exit(main())
