#!/usr/bin/env python3
"""Run opt-in local Codex CLI benchmarks against codegen starter repos."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from codex_live_benchmark_lib import (
    AUTH_POLICIES,
    BENCHMARK_MODES,
    CASE_TIERS,
    MODE_DEFAULT_VARIANTS,
    PROFILES,
    ROOT,
    SANDBOXES,
    STRICT_AUTH_POLICIES,
    STRICT_BENCHMARK_MODES,
    VARIANTS,
    CodexLiveCase,
    detect_baseline_contamination,
    load_capability_matrix,
    load_case_registry,
    redact_codex_command,
    redact_report_text,
    safe_case_segment,
    utc_stamp,
    write_json,
)


REFUSAL_MESSAGE = (
    "Refusing to run codex exec without "
    "CHANGEFORGE_ENABLE_CODEX_LIVE_BENCHMARK=1 or --allow-live-codex"
)
CURRENT_CODEX_HOME_REFUSAL_MESSAGE = (
    "auth-policy current-home-full requires "
    "CHANGEFORGE_ALLOW_CURRENT_CODEX_HOME=1 or --allow-current-codex-home"
)
INTERNAL_BORROWED_CODEX_HOME_ENV = "CHANGEFORGE_CODEX_LIVE_INTERNAL_BORROWED_CODEX_HOME"
PROCESS_PHASES = ("pdd", "ddd", "sdd", "tdd", "implementation", "validation", "review", "repair", "rereview")
PROCESS_CORE_PHASES = ("pdd", "ddd", "sdd", "tdd")
PROCESS_PHASE_STATUSES = {"present", "missing", "degraded", "inferred", "not_applicable"}
PROCESS_FALLBACK_FIELD_SOURCE = "case_metadata_fallback"
PROCESS_FALLBACK_SOURCE_ALIASES = {PROCESS_FALLBACK_FIELD_SOURCE, "inferred"}
PROCESS_REQUIRED_FIELDS = {
    "pdd": ("problem", "acceptance_criteria", "constraints", "validation_signal"),
    "ddd": ("domain_terms", "invariants", "ownership_decision", "side_effect_boundaries"),
    "sdd": (
        "modules",
        "public_api",
        "error_contract",
        "failure_modes",
        "logging_decision",
        "design_decision_points",
        "assumption_policy",
    ),
    "tdd": (
        "acceptance_to_tests",
        "invariant_to_tests_or_code",
        "public_api_to_tests",
        "failure_mode_tests",
        "validation_commands",
    ),
}
PROCESS_SDD_CHOICE_GATE_FIELDS = ("design_decision_points", "assumption_policy")
PROCESS_SDD_NO_CHOICE_RATIONALE_FIELDS = (
    "no_design_choice_rationale",
    "no_material_design_choice_rationale",
    "design_choice_rationale",
)
PROCESS_SDD_GENERIC_RATIONALES = {
    "no choice needed",
    "no decision needed",
    "not needed",
    "not required",
    "none",
    "n/a",
    "na",
}
PROCESS_SDD_ASSUMPTION_POLICY = (
    "block_when_wrong_answer_changes_contract_architecture_data_security_acceptance_or_user_visible_behavior"
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
PROCESS_LIST_FIELDS = {
    "pdd": (
        "user_or_system_impact",
        "acceptance_criteria",
        "constraints",
        "non_goals",
        "risk_surfaces",
        "validation_signal",
    ),
    "ddd": (
        "domain_terms",
        "entities",
        "value_objects",
        "domain_services",
        "application_services",
        "adapters",
        "invariants",
        "ownership_decision",
        "side_effect_boundaries",
    ),
    "sdd": (
        "modules",
        "files_to_change",
        "public_api",
        "data_flow",
        "error_contract",
        "failure_modes",
        "design_decision_points",
        "metrics_traces_alerts",
        "performance_or_concurrency_constraints",
        "compatibility_and_migration",
        "rollback_or_recovery",
    ),
    "tdd": (
        "failure_mode_tests",
        "logging_or_security_tests",
        "validation_commands",
        "red_green_refactor_trace",
    ),
}
PROCESS_MAPPING_FIELDS = {
    "tdd": ("acceptance_to_tests", "invariant_to_tests_or_code", "public_api_to_tests"),
}
MAX_STRUCTURED_EVENT_BYTES = 4096
RUN_EVENT_LOCK = threading.Lock()
BUILD_PROFILE_LOCK = threading.Lock()


def live_execution_allowed(args: argparse.Namespace, env: dict[str, str]) -> bool:
    """Return the exact opt-in predicate for live Codex execution."""
    return args.allow_live_codex or env.get("CHANGEFORGE_ENABLE_CODEX_LIVE_BENCHMARK") == "1"


def danger_full_access_allowed(args: argparse.Namespace, env: dict[str, str]) -> bool:
    """Return whether danger-full-access has its second explicit gate."""
    return args.allow_danger_full_access or env.get("CHANGEFORGE_ALLOW_DANGER_FULL_ACCESS") == "1"


def current_codex_home_allowed(args: argparse.Namespace, env: dict[str, str]) -> bool:
    """Return whether the runner may inherit the caller's Codex home/config."""
    return args.allow_current_codex_home or env.get("CHANGEFORGE_ALLOW_CURRENT_CODEX_HOME") == "1"


def resolve_auth_policy(args: argparse.Namespace) -> str:
    """Resolve explicit or compatibility auth policy defaults."""
    explicit = getattr(args, "auth_policy", None)
    if explicit:
        return str(explicit)
    codex_home_mode = getattr(args, "codex_home_mode", None)
    if codex_home_mode == "current":
        return "current-home-full"
    if codex_home_mode == "isolated":
        return "isolated-api-key"
    if getattr(args, "benchmark_mode", "clean-paired") == "current-home-smoke":
        return "current-home-full"
    return "borrow-current"


def codex_environment_policy(auth_policy: str) -> str:
    """Map CLI auth policy onto result/summary environment policy."""
    return {
        "isolated-api-key": "isolated_api_key",
        "borrow-current": "auth_borrowed_clean",
        "current-home-full": "current_home_full",
    }[auth_policy]


def legacy_codex_home_mode(auth_policy: str) -> str:
    """Return the pre-v2 compatibility label for older consumers."""
    return "current" if auth_policy == "current-home-full" else "isolated"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", action="append", default=[])
    parser.add_argument("--category", action="append", default=[])
    parser.add_argument("--tier", action="append", choices=CASE_TIERS, default=[])
    parser.add_argument(
        "--capability-core",
        action="store_true",
        help="Run the core capability linked live cases declared in evals/codex-live/capability-matrix.yaml.",
    )
    parser.add_argument("--benchmark-mode", choices=BENCHMARK_MODES, default="clean-paired")
    parser.add_argument(
        "--auth-policy",
        choices=AUTH_POLICIES,
        help=(
            "Authentication/environment policy. Strict modes default to borrow-current; "
            "current-home-smoke defaults to current-home-full."
        ),
    )
    parser.add_argument("--variant", action="append", choices=VARIANTS)
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--profile", choices=PROFILES, default="recommended")
    parser.add_argument("--sandbox", choices=SANDBOXES, default="workspace-write")
    parser.add_argument("--model")
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--allow-live-codex", action="store_true")
    parser.add_argument("--allow-many-runs", action="store_true")
    parser.add_argument("--allow-danger-full-access", action="store_true")
    parser.add_argument(
        "--codex-home-mode",
        choices=("isolated", "current"),
        help=(
            "Deprecated compatibility option. Prefer --auth-policy isolated-api-key, "
            "borrow-current, or current-home-full."
        ),
    )
    parser.add_argument("--allow-current-codex-home", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--publish-summary", action="store_true")
    parser.add_argument("--publish-current-home-smoke", action="store_true")
    parser.add_argument("--keep-workdirs", action="store_true")
    parser.add_argument("--changed-only", action="store_true")
    parser.add_argument("--failed-only", help="Select failed cells from a previous run id or run directory.")
    parser.add_argument("--rerun-failures-from", help="Rerun failed cells from a previous run id or run directory.")
    parser.add_argument("--max-cases", type=int)
    parser.add_argument("--max-runtime-minutes", type=float)
    parser.add_argument("--case-shard", help="Run a deterministic one-based shard, formatted INDEX/TOTAL.")
    parser.add_argument(
        "--parallel-cases",
        type=int,
        default=1,
        help=(
            "Run independent case/variant/run cells concurrently in-process. "
            "Each cell uses isolated workdirs and Codex homes; use shards for multi-process parallelism."
        ),
    )
    parser.add_argument("--resume-run", type=Path, help="Reuse an existing run directory and skip completed cells.")
    parser.add_argument("--timeout-seconds", type=int, default=3600)
    parser.add_argument(
        "--codex-idle-timeout-seconds",
        type=int,
        default=600,
        help="Terminate a Codex exec child after this many seconds without stdout/stderr progress. Default: 600.",
    )
    parser.add_argument(
        "--codex-exec-retries",
        type=int,
        default=1,
        help="Retry transient no-output Codex exec failures with no candidate changes. Default: 1.",
    )
    parser.add_argument("--list", action="store_true")
    return parser.parse_args(argv)


def select_cases(
    cases: list[CodexLiveCase],
    *,
    benchmarks: list[str],
    categories: list[str],
    tiers: list[str],
    capability_core: bool = False,
) -> list[CodexLiveCase]:
    """Select enabled cases by id or category."""
    selected = [case for case in cases if case.enabled]
    if capability_core:
        capability_case_ids = _capability_core_case_ids()
        selected = [case for case in selected if case.id in capability_case_ids]
    if benchmarks:
        requested = set(benchmarks)
        selected = [case for case in selected if case.id in requested]
    if categories:
        requested_categories = set(categories)
        selected = [case for case in selected if case.category in requested_categories]
    if tiers:
        requested_tiers = set(tiers)
        selected = [case for case in selected if case.tier in requested_tiers]
    return selected


def _capability_core_case_ids() -> set[str]:
    return {
        case_id
        for capability in load_capability_matrix()
        for case_id in capability.linked_live_cases
    }


def selected_variants(args: argparse.Namespace) -> list[str]:
    """Return requested variants with the mode-specific default set."""
    variants = args.variant or list(MODE_DEFAULT_VARIANTS[args.benchmark_mode])
    deduped: list[str] = []
    for variant in variants:
        if variant not in deduped:
            deduped.append(variant)
    return deduped


def apply_runtime_selection(
    args: argparse.Namespace,
    cases: list[CodexLiveCase],
    variants: list[str],
) -> tuple[list[CodexLiveCase], dict[str, Any]]:
    """Apply long-run selection controls while preserving case-level isolation."""
    selected = list(cases)
    metadata: dict[str, Any] = {
        "tier": list(args.tier),
        "changed_only": bool(args.changed_only),
        "failed_only": _run_source_arg_label(args.failed_only),
        "rerun_failures_from": _run_source_arg_label(args.rerun_failures_from),
        "max_cases": args.max_cases,
        "max_runtime_minutes": args.max_runtime_minutes,
        "case_shard": str(args.case_shard or ""),
        "parallel_cases_requested": int(args.parallel_cases or 1),
        "parallel_cases_effective": int(args.parallel_cases or 1),
        "parallel_cases_policy": (
            "parallel_cells_in_process; each cell uses isolated run/candidate/HOME/CODEX_HOME; "
            "shared build and run-event writes are locked"
        ),
        "resume_run": _run_source_label(args.resume_run) if args.resume_run else "",
        "baseline_reuse_policy": "none",
        "reused_baseline_run_id": None,
        "diagnostic_run": False,
        "rerun_cell_count": 0,
    }

    if args.changed_only:
        changed_ids = _changed_case_ids(selected)
        selected = [case for case in selected if case.id in changed_ids]
        metadata["changed_case_ids"] = sorted(changed_ids)
        metadata["diagnostic_run"] = True

    if args.case_shard:
        index, total = _parse_case_shard(args.case_shard)
        ordered = sorted(selected, key=lambda case: case.id)
        selected = [case for position, case in enumerate(ordered) if position % total == index - 1]
        metadata["case_shard_index"] = index
        metadata["case_shard_total"] = total
        metadata["diagnostic_run"] = True

    if args.max_cases is not None:
        selected = selected[: args.max_cases]
        metadata["diagnostic_run"] = True

    rerun_source = args.rerun_failures_from or args.failed_only
    if rerun_source:
        cells = _failed_cells_from_run(str(rerun_source))
        case_ids = {case_id for case_id, _variant, _run_index in cells}
        selected = [case for case in selected if case.id in case_ids]
        metadata["rerun_cells"] = sorted(_cell_label(cell) for cell in cells)
        metadata["rerun_cell_count"] = len(cells)
        metadata["diagnostic_run"] = True
        setattr(args, "_changeforge_rerun_cells", cells)
    else:
        setattr(args, "_changeforge_rerun_cells", None)

    completed_cells = _completed_cells(args.resume_run) if args.resume_run else set()
    setattr(args, "_changeforge_completed_cells", completed_cells)
    if completed_cells:
        metadata["completed_cell_count"] = len(completed_cells)
        metadata["diagnostic_run"] = True

    metadata["selected_case_count"] = len(selected)
    metadata["selected_cases"] = [case.id for case in selected]
    metadata["selected_variants"] = variants
    return selected, metadata


def validate_mode_args(args: argparse.Namespace, variants: list[str]) -> list[str]:
    """Validate benchmark mode, Codex home policy, variants, and publish switches."""
    errors: list[str] = []
    auth_policy = resolve_auth_policy(args)
    if auth_policy not in AUTH_POLICIES:
        errors.append(f"--auth-policy must be one of {', '.join(AUTH_POLICIES)}")
        return errors
    codex_home_mode = getattr(args, "codex_home_mode", None)
    if codex_home_mode == "current" and auth_policy != "current-home-full":
        errors.append("--codex-home-mode current is only compatible with --auth-policy current-home-full")
    if codex_home_mode == "isolated" and auth_policy == "current-home-full":
        errors.append("--auth-policy current-home-full is not compatible with --codex-home-mode isolated")
    if args.benchmark_mode in STRICT_BENCHMARK_MODES:
        if auth_policy not in STRICT_AUTH_POLICIES:
            errors.append("--auth-policy current-home-full is only allowed with --benchmark-mode current-home-smoke")
        if "current_home_smoke" in variants:
            errors.append("current_home_smoke is not a strict comparative benchmark variant")
        if args.publish_current_home_smoke:
            errors.append("--publish-current-home-smoke requires --benchmark-mode current-home-smoke")
    else:
        if auth_policy != "current-home-full":
            errors.append("--benchmark-mode current-home-smoke requires --auth-policy current-home-full")
        invalid = sorted(set(variants) - {"current_home_smoke"})
        if invalid:
            errors.append("current-home-smoke mode only supports current_home_smoke")
        if args.publish_summary:
            errors.append("--publish-summary is only for strict benchmark summaries")
    if args.publish_summary and auth_policy not in STRICT_AUTH_POLICIES:
        errors.append("--publish-summary requires --auth-policy borrow-current or isolated-api-key")
    if getattr(args, "max_cases", None) is not None and args.max_cases < 1:
        errors.append("--max-cases must be at least 1")
    if getattr(args, "max_runtime_minutes", None) is not None and args.max_runtime_minutes <= 0:
        errors.append("--max-runtime-minutes must be positive")
    if int(getattr(args, "parallel_cases", 1) or 1) < 1:
        errors.append("--parallel-cases must be at least 1")
    if getattr(args, "failed_only", None) and getattr(args, "rerun_failures_from", None):
        errors.append("--failed-only and --rerun-failures-from are mutually exclusive")
    if getattr(args, "case_shard", None):
        try:
            _parse_case_shard(args.case_shard)
        except ValueError as exc:
            errors.append(str(exc))
    return errors


def _parse_case_shard(value: str) -> tuple[int, int]:
    parts = value.split("/", 1)
    if len(parts) != 2:
        raise ValueError("--case-shard must be formatted INDEX/TOTAL")
    try:
        index = int(parts[0])
        total = int(parts[1])
    except ValueError as exc:
        raise ValueError("--case-shard INDEX and TOTAL must be integers") from exc
    if total < 1 or index < 1 or index > total:
        raise ValueError("--case-shard requires 1 <= INDEX <= TOTAL")
    return index, total


def _changed_case_ids(cases: list[CodexLiveCase]) -> set[str]:
    changed = _git_changed_paths()
    if "evals/codex-live/cases.yaml" in changed:
        return {case.id for case in cases}
    selected: set[str] = set()
    for case in cases:
        prefixes = {
            _repo_rel(case.task_prompt),
            _repo_rel(case.starter_repo),
            f"evals/codegen/{case.category}/{case.codegen_case}/",
        }
        for path in changed:
            if any(path == prefix.rstrip("/") or path.startswith(prefix.rstrip("/") + "/") for prefix in prefixes):
                selected.add(case.id)
                break
    return selected


def _git_changed_paths() -> set[str]:
    commands = (
        ["git", "diff", "--name-only", "HEAD", "--"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    )
    paths: set[str] = set()
    for command in commands:
        completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, shell=False, check=False)
        if completed.returncode != 0:
            continue
        paths.update(line.strip() for line in completed.stdout.splitlines() if line.strip())
    return paths


def _repo_rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return "<external>"


def _failed_cells_from_run(source: str) -> set[tuple[str, str, int]]:
    run_dir = _resolve_previous_run_dir(source)
    cells: set[tuple[str, str, int]] = set()
    for result_path in sorted(run_dir.glob("cases/*/*/run-*/result.json")):
        try:
            result = json.loads(result_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(result, dict) or not _is_failed_result(result):
            continue
        case_id = str(result.get("case_id") or "")
        variant = str(result.get("variant") or "")
        run_index = int(result.get("run_index", 0) or 0)
        if case_id and variant and run_index > 0:
            cells.add((case_id, variant, run_index))
    return cells


def _resolve_previous_run_dir(source: str) -> Path:
    path = Path(source)
    if path.exists():
        return path.resolve()
    return (ROOT / "reports" / "codex-live-runs" / source).resolve()


def _is_failed_result(result: dict[str, Any]) -> bool:
    if result.get("artifact_status") in {"failed", "partial"}:
        return True
    if result.get("failure_category") not in {None, "none", "telemetry_only"}:
        return True
    return result.get("benchmark_eligible") is True and result.get("benchmark_passed") is not True


def _completed_cells(run_dir: Path) -> set[tuple[str, str, int]]:
    cells: set[tuple[str, str, int]] = set()
    for result_path in sorted(run_dir.glob("cases/*/*/run-*/result.json")):
        try:
            result = json.loads(result_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(result, dict):
            continue
        case_id = str(result.get("case_id") or "")
        variant = str(result.get("variant") or "")
        run_index = int(result.get("run_index", 0) or 0)
        if case_id and variant and run_index > 0:
            cells.add((case_id, variant, run_index))
    return cells


def _cell_label(cell: tuple[str, str, int]) -> str:
    case_id, variant, run_index = cell
    return f"{case_id}|{variant}|run-{run_index:02d}"


def _run_source_label(path: Path) -> str:
    try:
        rel = path.resolve().relative_to((ROOT / "reports" / "codex-live-runs").resolve())
    except ValueError:
        return "<external-run-dir>"
    return rel.as_posix()


def _run_source_arg_label(source: str | None) -> str:
    if not source:
        return ""
    path = Path(source)
    if path.is_absolute() or "/" in source:
        try:
            return _run_source_label(path)
        except OSError:
            return "<external-run-dir>"
    return source


def _selection_metadata(args: argparse.Namespace) -> dict[str, Any]:
    metadata = getattr(args, "_changeforge_selection_metadata", {})
    return dict(metadata) if isinstance(metadata, dict) else {}


def _strategy_manifest_fields(args: argparse.Namespace) -> dict[str, Any]:
    metadata = _selection_metadata(args)
    capability_cases = _capability_core_case_ids() if getattr(args, "capability_core", False) else set()
    selected_capability_cases = (
        sorted(capability_cases)
        if getattr(args, "capability_core", False)
        else [case_id for case_id in metadata.get("selected_cases", []) if case_id in capability_cases]
    )
    return {
        "run_selection": metadata,
        "capability_core_requested": bool(getattr(args, "capability_core", False)),
        "selected_capability_case_count": len(selected_capability_cases),
        "selected_capability_cases": selected_capability_cases,
        "capability_matrix_path": "evals/codex-live/capability-matrix.yaml",
        "baseline_reuse_policy": metadata.get("baseline_reuse_policy", "none"),
        "reused_baseline_run_id": metadata.get("reused_baseline_run_id"),
    }


def _should_run_cell(args: argparse.Namespace, case: CodexLiveCase, variant: str, run_index: int) -> bool:
    cell = (case.id, variant, run_index)
    rerun_cells = getattr(args, "_changeforge_rerun_cells", None)
    if rerun_cells is not None:
        return cell in rerun_cells
    completed_cells = getattr(args, "_changeforge_completed_cells", set())
    return cell not in completed_cells


def _manifest_case_ids(args: argparse.Namespace, cases: list[CodexLiveCase]) -> list[str]:
    if getattr(args, "capability_core", False):
        return sorted(_capability_core_case_ids())
    return [case.id for case in cases]


def _manifest_result_count(out_dir: Path, results: list[dict[str, Any]], *, resume_run: bool) -> int:
    if resume_run:
        return sum(1 for _path in out_dir.glob("cases/*/*/run-*/result.json"))
    return len(results)


def _runtime_budget_exhausted(args: argparse.Namespace, started: float) -> bool:
    minutes = getattr(args, "max_runtime_minutes", None)
    return bool(minutes is not None and (time.monotonic() - started) >= float(minutes) * 60)


def write_skipped_manifest(
    out_dir: Path,
    *,
    args: argparse.Namespace,
    cases: list[CodexLiveCase],
    variants: list[str],
    allowed: bool,
) -> None:
    """Write a skipped or dry-run manifest without planning Codex invocations."""
    _write_run_event(out_dir, phase="summary", event="skipped", status="skipped")
    limitations = [
        "Codex CLI was not invoked.",
        "Dry-run and non-opted-in reports are not publishable benchmark evidence.",
    ]
    if getattr(args, "codex_home_mode", None) == "current":
        limitations.append(_current_home_full_limitation())
    auth_policy = resolve_auth_policy(args)
    environment_policy = codex_environment_policy(auth_policy)
    changeforge_metadata = _manifest_changeforge_metadata(args, variants)
    write_json(
        out_dir / "run-manifest.json",
        {
            "schema_version": 2,
            "generated_by": "scripts/run-codex-live-benchmarks.py",
            "run_id": out_dir.name,
            "status": "skipped_not_opted_in",
            "benchmark_mode": args.benchmark_mode,
            "dry_run": bool(args.dry_run),
            "live_execution_allowed": allowed,
            "live_execution_effective": False,
            "cases": [case.id for case in cases],
            "variants": variants,
            "runs_per_variant": args.runs,
            "profile": args.profile,
            "sandbox": args.sandbox,
            "codex_home_mode": legacy_codex_home_mode(auth_policy),
            "auth_policy": auth_policy,
            "codex_environment_policy": environment_policy,
            **changeforge_metadata,
            **_strategy_manifest_fields(args),
            "codex_invocations": [],
            "result_count": 0,
            "limitations": limitations,
        },
    )


def codex_command(args: argparse.Namespace, final_path: Path) -> list[str]:
    """Build the Codex exec command used for live runs."""
    auth_policy = resolve_auth_policy(args)
    command = [
        args.codex_bin,
        "exec",
        "--json",
        "--sandbox",
        args.sandbox,
    ]
    if auth_policy in STRICT_AUTH_POLICIES:
        command.extend(["--ignore-user-config", "--ignore-rules", "--disable", "plugins"])
    command.extend(
        [
            "--output-last-message",
            str(final_path),
        ]
    )
    if args.model:
        command.extend(["--model", args.model])
    command.append("-")
    return command


def run_codex_exec(
    command: list[str],
    *,
    prompt: str,
    cwd: Path,
    events_path: Path,
    stderr_path: Path,
    args: argparse.Namespace,
    env: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    """Run Codex after checking the live opt-in gate immediately beforehand."""
    if args.dry_run or not live_execution_allowed(args, env):
        raise RuntimeError(REFUSAL_MESSAGE)
    process_env = _subprocess_env(env)
    with events_path.open("w", encoding="utf-8") as events_file, stderr_path.open("w", encoding="utf-8") as stderr_file:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=events_file,
            stderr=stderr_file,
            text=True,
            env=process_env,
            shell=False,
        )
        try:
            return _wait_for_codex_exec(
                process,
                command=command,
                prompt=prompt,
                events_path=events_path,
                stderr_path=stderr_path,
                timeout_seconds=args.timeout_seconds,
                idle_timeout_seconds=getattr(args, "codex_idle_timeout_seconds", 0),
            )
        except Exception:
            _terminate_codex_process(process)
            raise


def _wait_for_codex_exec(
    process: subprocess.Popen[str],
    *,
    command: list[str],
    prompt: str,
    events_path: Path,
    stderr_path: Path,
    timeout_seconds: int | float,
    idle_timeout_seconds: int | float | None,
) -> subprocess.CompletedProcess[str]:
    """Wait for Codex while enforcing both total and no-output timeouts."""
    if process.stdin is not None:
        try:
            process.stdin.write(prompt)
            process.stdin.close()
        except BrokenPipeError:
            pass

    started = time.monotonic()
    last_activity = started
    last_sizes = _codex_exec_progress_sizes(events_path, stderr_path)
    idle_timeout = float(idle_timeout_seconds or 0)
    total_timeout = float(timeout_seconds)

    while True:
        returncode = process.poll()
        current_sizes = _codex_exec_progress_sizes(events_path, stderr_path)
        if current_sizes != last_sizes:
            last_sizes = current_sizes
            last_activity = time.monotonic()
        now = time.monotonic()
        if returncode is not None:
            return subprocess.CompletedProcess(command, returncode, "", "")
        if total_timeout > 0 and now - started > total_timeout:
            raise subprocess.TimeoutExpired(command, total_timeout)
        if idle_timeout > 0 and now - last_activity > idle_timeout:
            raise subprocess.TimeoutExpired(command, idle_timeout, output="codex exec produced no stdout/stderr progress")
        time.sleep(0.5)


def _codex_exec_progress_sizes(*paths: Path) -> tuple[int, ...]:
    return tuple(path.stat().st_size if path.exists() else 0 for path in paths)


def _terminate_codex_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def run_codex_exec_with_retries(
    command: list[str],
    *,
    prompt: str,
    cwd: Path,
    events_path: Path,
    stderr_path: Path,
    final_path: Path,
    args: argparse.Namespace,
    env: dict[str, str],
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    """Run Codex, retrying only empty no-diff transient failures."""
    max_retries = max(0, int(getattr(args, "codex_exec_retries", 0) or 0))
    attempts: list[dict[str, Any]] = []
    attempt_index = 1
    while True:
        completed = run_codex_exec(
            command,
            prompt=prompt,
            cwd=cwd,
            events_path=events_path,
            stderr_path=stderr_path,
            args=args,
            env=env,
        )
        retry_reason = _codex_exec_retry_reason(
            completed,
            cwd=cwd,
            stderr_path=stderr_path,
            final_path=final_path,
        )
        should_retry = len(attempts) < max_retries and retry_reason == "transient_no_output_no_candidate_changes"
        attempts.append(
            _codex_exec_attempt_metadata(
                attempt_index,
                completed,
                retry_reason=retry_reason,
                retried=should_retry,
                stderr_path=stderr_path,
            )
        )
        if not should_retry:
            return completed, {
                "codex_attempt_count": len(attempts),
                "codex_retry_count": max(0, len(attempts) - 1),
                "codex_exec_attempts": attempts,
            }
        _clear_codex_exec_artifacts(events_path, stderr_path, final_path)
        attempt_index += 1


def _codex_exec_retry_reason(
    completed: subprocess.CompletedProcess[str],
    *,
    cwd: Path,
    stderr_path: Path,
    final_path: Path,
) -> str:
    """Classify whether a failed Codex exec is safe to retry once."""
    if completed.returncode == 0:
        return "not_needed"
    if _candidate_has_git_changes(cwd):
        return "candidate_changed"
    if _path_has_text(final_path):
        return "final_message_present"
    if _path_has_text(stderr_path):
        return "stderr_present"
    return "transient_no_output_no_candidate_changes"


def _codex_exec_attempt_metadata(
    attempt_index: int,
    completed: subprocess.CompletedProcess[str],
    *,
    retry_reason: str,
    retried: bool,
    stderr_path: Path,
) -> dict[str, Any]:
    stderr_excerpt = ""
    if stderr_path.exists():
        stderr_excerpt = redact_report_text(stderr_path.read_text(encoding="utf-8", errors="ignore").strip())[:400]
    return {
        "attempt_index": attempt_index,
        "returncode": completed.returncode,
        "retry_reason": retry_reason,
        "retried": retried,
        "stderr_excerpt": stderr_excerpt,
    }


def _path_has_text(path: Path) -> bool:
    return path.exists() and bool(path.read_text(encoding="utf-8", errors="ignore").strip())


def _candidate_has_git_changes(candidate_dir: Path) -> bool:
    status = subprocess.run(
        ["git", "status", "--short"],
        cwd=candidate_dir,
        text=True,
        capture_output=True,
        shell=False,
        check=False,
    )
    if status.returncode != 0:
        return True
    for line in status.stdout.splitlines():
        path = line[3:] if len(line) > 3 else line
        if path.startswith(".agents/") or path.startswith(".codex/"):
            continue
        return True
    return False


def _clear_codex_exec_artifacts(*paths: Path) -> None:
    for path in paths:
        if path.exists():
            path.unlink()


def _runnable_cells(
    args: argparse.Namespace,
    out_dir: Path,
    cases: list[CodexLiveCase],
    variants: list[str],
    started: float,
) -> list[tuple[CodexLiveCase, str, int]]:
    cells: list[tuple[CodexLiveCase, str, int]] = []
    for case in cases:
        for variant in variants:
            if variant not in case.variants:
                continue
            for run_index in range(1, args.runs + 1):
                if _runtime_budget_exhausted(args, started):
                    _write_run_event(
                        out_dir,
                        case=case,
                        variant=variant,
                        run_index=run_index,
                        phase="summary",
                        event="skipped",
                        status="skipped",
                        error_category="max_runtime_minutes",
                    )
                    break
                if not _should_run_cell(args, case, variant, run_index):
                    _write_run_event(
                        out_dir,
                        case=case,
                        variant=variant,
                        run_index=run_index,
                        phase="summary",
                        event="skipped",
                        status="skipped",
                    )
                    continue
                cells.append((case, variant, run_index))
    return cells


def _execute_run_cells(
    args: argparse.Namespace,
    out_dir: Path,
    cells: list[tuple[CodexLiveCase, str, int]],
    built_profiles: set[str],
) -> list[dict[str, Any]]:
    parallel_cases = max(1, int(getattr(args, "parallel_cases", 1) or 1))
    if parallel_cases == 1 or len(cells) <= 1:
        return [
            _run_one_case(args, out_dir, case, variant, run_index, built_profiles)
            for case, variant, run_index in cells
        ]

    results: list[dict[str, Any] | None] = [None] * len(cells)
    with ThreadPoolExecutor(max_workers=parallel_cases) as executor:
        futures = {
            executor.submit(_run_one_case, args, out_dir, case, variant, run_index, built_profiles): index
            for index, (case, variant, run_index) in enumerate(cells)
        }
        for future in as_completed(futures):
            results[futures[future]] = future.result()
    return [result for result in results if result is not None]


def run_live(args: argparse.Namespace, out_dir: Path, cases: list[CodexLiveCase], variants: list[str]) -> dict[str, Any]:
    """Execute selected live benchmark cases."""
    built_profiles: set[str] = set()
    started = time.monotonic()
    _write_run_event(out_dir, phase="summary", event="phase_started", status="ok")
    cells = _runnable_cells(args, out_dir, cases, variants, started)
    results = _execute_run_cells(args, out_dir, cells, built_profiles)

    if not results:
        status = "failed"
    elif any(result["artifact_status"] == "failed" for result in results):
        status = "partial" if any(result["artifact_status"] == "collected" for result in results) else "failed"
    elif any(result["artifact_status"] == "partial" for result in results):
        status = "partial"
    else:
        status = "collected"

    limitations = [
        "Runs use local Codex CLI behavior and local account/model availability.",
        "Candidate grading is delegated to deterministic codegen benchmark checks when real assertions exist.",
        "Telemetry metrics are bounded counts parsed from JSONL and exclude raw messages and command bodies.",
    ]
    auth_policy = resolve_auth_policy(args)
    environment_policy = codex_environment_policy(auth_policy)
    changeforge_metadata = _manifest_changeforge_metadata(args, variants)
    if args.benchmark_mode in STRICT_BENCHMARK_MODES:
        limitations.append(
            "Strict comparative claims may borrow Codex authentication, but user skills, hooks, config, and rules are not loaded."
        )
    if auth_policy == "current-home-full":
        limitations.append(_current_home_full_limitation())

    manifest = {
        "schema_version": 2,
        "generated_by": "scripts/run-codex-live-benchmarks.py",
        "run_id": out_dir.name,
        "status": status,
        "benchmark_mode": args.benchmark_mode,
        "dry_run": False,
        "live_execution_allowed": True,
        "live_execution_effective": True,
        "cases": _manifest_case_ids(args, cases),
        "variants": variants,
        "runs_per_variant": args.runs,
        "profile": args.profile,
        "sandbox": args.sandbox,
        "codex_home_mode": legacy_codex_home_mode(auth_policy),
        "auth_policy": auth_policy,
        "codex_environment_policy": environment_policy,
        **changeforge_metadata,
        **_strategy_manifest_fields(args),
        "result_count": _manifest_result_count(out_dir, results, resume_run=bool(args.resume_run)),
        "limitations": limitations,
    }
    write_json(out_dir / "run-manifest.json", manifest)
    _write_run_event(out_dir, phase="summary", event="phase_completed", status=status)
    _generate_summary(
        out_dir,
        publish=args.publish_summary,
        publish_current_home_smoke=args.publish_current_home_smoke,
    )
    return manifest


def _run_one_case(
    args: argparse.Namespace,
    out_dir: Path,
    case: CodexLiveCase,
    variant: str,
    run_index: int,
    built_profiles: set[str],
) -> dict[str, Any]:
    run_dir = out_dir / "cases" / safe_case_segment(case.id) / variant / f"run-{run_index:02d}"
    candidate_dir = run_dir / "candidate"
    grading_dir = run_dir / "grading"
    run_dir.mkdir(parents=True, exist_ok=True)
    _copy_starter(case.starter_repo, candidate_dir)
    _init_git(candidate_dir)
    prompt = _render_prompt(case, variant)
    (run_dir / "prompt.md").write_text(prompt, encoding="utf-8")
    events_path = run_dir / "events.jsonl"
    events_redacted_path = run_dir / "events.redacted.jsonl"
    stderr_path = run_dir / "codex-stderr.log"
    final_path = run_dir / "final.md"
    _write_process_trace_evaluation_started(out_dir, case=case, variant=variant, run_index=run_index)
    artifact_status = "failed"
    codex_returncode: int | None = None
    codex_attempt_count = 0
    codex_retry_count = 0
    codex_exec_attempts: list[dict[str, Any]] = []
    failure: str | None = None
    failure_stage: str | None = None
    env: dict[str, str] = {}
    environment: dict[str, Any] = {}
    stage = "build_codex_environment"
    try:
        env, environment = build_codex_environment(args, case, variant, run_dir)
        command = codex_command(args, final_path)
        write_json(
            run_dir / "codex-command.redacted.json",
            _command_metadata(args, command, environment),
        )
        if variant in {"skills_only_clean", "skills_with_hooks_clean"}:
            stage = "install_changeforge"
            _install_changeforge(
                args,
                candidate_dir,
                env,
                built_profiles,
                with_hooks=variant == "skills_with_hooks_clean",
            )

        stage = "codex_exec"
        completed, codex_attempt_metadata = run_codex_exec_with_retries(
            command,
            prompt=prompt,
            cwd=candidate_dir,
            events_path=events_path,
            stderr_path=stderr_path,
            final_path=final_path,
            args=args,
            env=env,
        )
        codex_attempt_count = int(codex_attempt_metadata.get("codex_attempt_count", 0) or 0)
        codex_retry_count = int(codex_attempt_metadata.get("codex_retry_count", 0) or 0)
        codex_exec_attempts = list(codex_attempt_metadata.get("codex_exec_attempts", []))
        codex_returncode = completed.returncode
        artifact_status = "collected" if completed.returncode == 0 else "failed"
        if not final_path.exists():
            final_path.touch()
    except Exception as exc:  # live run should preserve artifacts for diagnosis
        failure = redact_report_text(f"{type(exc).__name__}: {exc}")
        failure_stage = stage
        artifact_status = "partial"
        events_path.touch()
        stderr_path.write_text(f"{failure}\n", encoding="utf-8")
        final_path.touch()
    finally:
        _redact_text_artifact(stderr_path)
        _redact_text_artifact(final_path)
        _cleanup_borrowed_codex_home(env)

    _write_git_artifacts(candidate_dir, run_dir)
    _remove_changeforge_support_artifacts_for_grading(candidate_dir)
    metrics = _parse_events(events_path, run_dir / "events.metrics.json", events_redacted_path)
    grading = _grade(case, candidate_dir, grading_dir)
    candidate_artifacts = _copy_candidate_evidence_artifacts(candidate_dir, run_dir)
    contamination = _contamination_for_variant(variant, run_dir)
    grading_status = _grading_status(case, grading, contamination, variant)
    compact_runtime = _run_compaction_runtime_harness(
        case=case,
        variant=variant,
        run_dir=run_dir,
        candidate_dir=candidate_dir,
        events_redacted_path=events_redacted_path,
        env=env,
        grading_status=grading_status,
        candidate_artifacts=candidate_artifacts,
    )
    artifact_status = _artifact_status_after_grading(
        artifact_status=artifact_status,
        codex_returncode=codex_returncode,
        grading_status=grading_status,
        grading=grading,
    )
    benchmark_eligible = _benchmark_eligible(args, case, artifact_status, grading_status, contamination, environment)
    benchmark_passed = benchmark_eligible and grading_status == "passed"
    failure_category = _failure_category(
        artifact_status=artifact_status,
        failure_stage=failure_stage,
        codex_returncode=codex_returncode,
        contamination=contamination,
        grading_status=grading_status,
        grading=grading,
        benchmark_passed=benchmark_passed,
    )
    auth_policy = resolve_auth_policy(args)
    environment_policy = codex_environment_policy(auth_policy)
    changeforge_metadata = _result_changeforge_metadata(args, variant)

    limitations = [
        "Result reflects one local Codex CLI run for this variant.",
        "Raw Codex messages and command bodies are not persisted in parsed metrics.",
    ]
    if auth_policy == "current-home-full":
        limitations.append(_current_home_full_limitation())

    result = {
        "schema_version": 2,
        "generated_by": "scripts/run-codex-live-benchmarks.py",
        "case_id": case.id,
        "variant": variant,
        "run_index": run_index,
        "status": artifact_status,
        "artifact_status": artifact_status,
        "grading_status": grading_status,
        "benchmark_mode": args.benchmark_mode,
        "codex_home_mode": legacy_codex_home_mode(auth_policy),
        "auth_policy": auth_policy,
        "codex_environment_policy": environment_policy,
        **changeforge_metadata,
        "grading_mode": case.grading_mode,
        "publishable_for_strict": case.publishable_for_strict,
        "benchmark_eligible": benchmark_eligible,
        "benchmark_passed": benchmark_passed,
        "failure_category": failure_category,
        "contamination": contamination,
        "environment": environment,
        "codex_returncode": codex_returncode,
        "codex_attempt_count": codex_attempt_count,
        "codex_retry_count": codex_retry_count,
        "codex_exec_attempts": codex_exec_attempts,
        "failure": failure,
        "failure_stage": failure_stage,
        "setup_failure_reason": grading.get("setup_failure_reason", "none"),
        "setup_failure_subreason": grading.get("setup_failure_subreason", "none"),
        "setup_contract": grading.get("setup_contract", {}),
        "test_suite_failure_reason": grading.get("test_suite_failure_reason", "none"),
        "security_failure_reason": grading.get("security_failure_reason", "none"),
        "first_failure_stage": grading.get("first_failure_stage", "none"),
        "first_failure_excerpt": grading.get("first_failure_excerpt", ""),
        "setup_log_excerpt": grading.get("setup_log_excerpt", ""),
        "test_suite_log_excerpt": grading.get("test_suite_log_excerpt", ""),
        "security_log_excerpt": grading.get("security_log_excerpt", ""),
        "paths": {
            "prompt": _artifact_path(run_dir, run_dir / "prompt.md"),
            "events": _artifact_path(run_dir, events_redacted_path),
            "events_redacted": _artifact_path(run_dir, events_redacted_path),
            "events_metrics": _artifact_path(run_dir, run_dir / "events.metrics.json"),
            "final": _artifact_path(run_dir, final_path),
            "diff": _artifact_path(run_dir, run_dir / "diff.patch"),
            "git_status": _artifact_path(run_dir, run_dir / "git-status.txt"),
            "grading": _artifact_path(run_dir, grading_dir / "grading-result.json"),
            "process_trace": _artifact_path(run_dir, run_dir / "process-trace.json"),
            **{
                key: _artifact_path(run_dir, path)
                for key, path in candidate_artifacts.items()
            },
        },
        "grading": grading,
        "metrics": metrics,
        "compact_runtime_evidence": compact_runtime.get("evidence", {}),
        "limitations": limitations,
    }
    if compact_runtime.get("paths"):
        result["paths"].update(compact_runtime["paths"])
    write_json(run_dir / "result.json", result)
    process_trace = _process_trace_payload(
        out_dir,
        run_dir,
        case=case,
        variant=variant,
        run_index=run_index,
        result=result,
    )
    write_json(run_dir / "process-trace.json", process_trace)
    _write_process_phase_events(
        out_dir,
        case=case,
        variant=variant,
        run_index=run_index,
        phase_status=process_trace.get("phase_status", {}),
        evidence_sources=process_trace.get("evidence_sources", []),
    )
    _write_run_event(
        out_dir,
        case=case,
        variant=variant,
        run_index=run_index,
        phase="validation",
        event="artifact_written",
        status="ok",
        artifact=_run_relative_artifact(out_dir, run_dir / "process-trace.json"),
    )
    if not args.keep_workdirs:
        shutil.rmtree(candidate_dir, ignore_errors=True)
    return result


def _artifact_path(run_dir: Path, path: Path) -> str:
    """Return a run-local artifact label without exposing host absolute paths."""
    try:
        rel = path.resolve().relative_to(run_dir.resolve()).as_posix()
    except ValueError:
        return "<artifact>"
    return f"<run-dir>/{rel}"


def _run_relative_artifact(out_dir: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(out_dir.resolve()).as_posix()
    except ValueError:
        return "<artifact>"


def _write_process_trace_evaluation_started(
    out_dir: Path,
    *,
    case: CodexLiveCase,
    variant: str,
    run_index: int,
) -> None:
    _write_run_event(
        out_dir,
        case=case,
        variant=variant,
        run_index=run_index,
        phase="summary",
        event="process_trace_evaluation_started",
        status="collected",
    )


def _write_process_phase_events(
    out_dir: Path,
    *,
    case: CodexLiveCase,
    variant: str,
    run_index: int,
    phase_status: Any,
    evidence_sources: Any,
) -> None:
    statuses = phase_status if isinstance(phase_status, dict) else {}
    sources = [str(source) for source in evidence_sources] if isinstance(evidence_sources, list) else []
    for phase in PROCESS_CORE_PHASES:
        status = str(statuses.get(phase, "missing"))
        if status not in PROCESS_PHASE_STATUSES:
            status = "missing"
        _write_run_event(
            out_dir,
            case=case,
            variant=variant,
            run_index=run_index,
            phase=phase,
            event="process_phase_evaluated",
            status=status,
            error_category=_process_phase_error_category(status, sources),
        )
    _write_run_event(
        out_dir,
        case=case,
        variant=variant,
        run_index=run_index,
        phase="summary",
        event="process_trace_evaluation_completed",
        status=_overall_process_trace_status(statuses),
        error_category=_overall_process_trace_error_category(statuses, sources),
    )


def _process_phase_error_category(status: str, evidence_sources: list[str]) -> str | None:
    if status == "inferred":
        return "metadata_fallback_only" if any("case_metadata_fallback" in source for source in evidence_sources) else None
    if status == "degraded":
        return "partial_trace"
    if status == "missing":
        return "missing_trace"
    return None


def _overall_process_trace_status(phase_status: dict[str, Any]) -> str:
    core_statuses = [str(phase_status.get(phase, "missing")) for phase in PROCESS_CORE_PHASES]
    if all(status == "present" for status in core_statuses):
        return "present"
    if all(status == "inferred" for status in core_statuses):
        return "inferred"
    if all(status == "missing" for status in core_statuses):
        return "missing"
    if any(status == "degraded" for status in core_statuses):
        return "degraded"
    return "partial"


def _overall_process_trace_error_category(phase_status: dict[str, Any], evidence_sources: list[str]) -> str | None:
    status = _overall_process_trace_status(phase_status)
    if status == "inferred":
        return "metadata_fallback_only" if any("case_metadata_fallback" in source for source in evidence_sources) else None
    if status in {"missing", "degraded", "partial"}:
        return "partial_trace"
    return None


def _write_run_event(
    out_dir: Path,
    *,
    phase: str,
    event: str,
    status: str,
    case: CodexLiveCase | None = None,
    variant: str | None = None,
    run_index: int | None = None,
    duration_ms: int | None = None,
    artifact: str | None = None,
    error_category: str | None = None,
) -> None:
    payload = {
        "schema_version": 1,
        "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
        "run_id": out_dir.name,
        "case_id": case.id if case else None,
        "variant": variant,
        "run_index": run_index,
        "tier": getattr(case, "tier", None) if case else None,
        "phase": phase,
        "event": event,
        "status": status,
        "duration_ms": duration_ms,
        "selected_skills": _selected_skills_for_variant(variant, case),
        "selected_capabilities": _selected_capabilities_for_variant(variant, case),
        "hook_guidance_bytes": _hook_guidance_bytes(variant),
        "artifact": artifact,
        "error_category": error_category,
    }
    _append_jsonl(out_dir / "run.log.jsonl", payload)
    _append_jsonl(out_dir / "timeline.jsonl", payload)


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    clean_payload = _bounded_event_payload(payload)
    with RUN_EVENT_LOCK:
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(clean_payload, sort_keys=True) + "\n")


def _bounded_event_payload(payload: dict[str, Any]) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, str):
            value = redact_report_text(value)
            if key == "artifact" and (value.startswith("/") or value.startswith("..")):
                value = "<artifact>"
            clean[key] = value[:512]
        elif isinstance(value, list):
            clean[key] = [str(item)[:120] for item in value[:20]]
        else:
            clean[key] = value
    encoded = json.dumps(clean, sort_keys=True)
    if len(encoded.encode("utf-8")) <= MAX_STRUCTURED_EVENT_BYTES:
        return clean
    clean["error_category"] = "event_truncated"
    return {key: value for key, value in clean.items() if key not in {"selected_capabilities"}}


def _process_trace_payload(
    out_dir: Path,
    run_dir: Path,
    *,
    case: CodexLiveCase,
    variant: str,
    run_index: int,
    result: dict[str, Any],
) -> dict[str, Any]:
    validation_commands = _validation_commands(case)
    facts, phase_status, evidence_sources = _process_trace_evidence(run_dir, case, validation_commands)
    phase_status["implementation"] = "present" if result.get("status") in {"collected", "failed", "partial"} else "missing"
    phase_status["validation"] = "present" if validation_commands and result.get("grading_status") else "missing"
    phase_status["review"] = "present" if _final_mentions_review(run_dir) else "missing"
    phase_status["repair"] = "present" if _final_mentions(run_dir, ("repair", "fixed review finding")) else "missing"
    phase_status["rereview"] = "present" if _final_mentions(run_dir, ("re-review", "rereview", "reviewed again")) else "missing"
    selected_skills = _selected_skills_for_variant(variant, case)
    selected_capabilities = _selected_capabilities_for_variant(variant, case)
    required_quality_gates = _required_quality_gates_for_process_trace(facts)
    artifacts = [
        _run_relative_artifact(out_dir, run_dir / "result.json"),
        _run_relative_artifact(out_dir, run_dir / "grading" / "grading-result.json"),
        _run_relative_artifact(out_dir, run_dir / "events.metrics.json"),
        _run_relative_artifact(out_dir, run_dir / "events.redacted.jsonl"),
    ]
    return {
        "schema_version": 2,
        "run_id": out_dir.name,
        "case_id": case.id,
        "variant": variant,
        "run_index": run_index,
        "route_manifest_present": _final_has_route_manifest(run_dir),
        "phase_status": phase_status,
        "traceability": _process_traceability(facts, validation_commands),
        "process_facts": facts,
        "evidence_sources": evidence_sources,
        "selected_skills": selected_skills,
        "selected_capabilities": selected_capabilities,
        "required_quality_gates": required_quality_gates,
        "stage_ownership": _process_stage_ownership(),
        "validation_commands": validation_commands,
        "read_evidence": _trace_named_evidence(facts, "read_evidence"),
        "repo_graph_evidence": _trace_named_evidence(facts, "repo_graph_evidence"),
        "memory_evidence": _trace_named_evidence(facts, "memory_evidence"),
        "validation_broker_evidence": _trace_named_evidence(facts, "validation_broker_evidence"),
        "trajectory_findings": _trace_named_evidence(facts, "trajectory_findings"),
        "residual_risk": _trace_named_evidence(facts, "residual_risk"),
        "artifacts": artifacts,
        "compaction_context": _compact_context_from_artifact(run_dir) if case.id.startswith("compact/") else {},
        "compact_runtime_evidence": result.get("compact_runtime_evidence", {}) if case.id.startswith("compact/") else {},
        "result_status": result.get("status"),
        "grading_status": result.get("grading_status"),
        "failure_category": result.get("failure_category"),
    }


def _process_trace_evidence(
    run_dir: Path,
    case: CodexLiveCase,
    validation_commands: list[str],
) -> tuple[dict[str, Any], dict[str, str], list[str]]:
    fallback_facts = _mark_process_facts_source(_process_facts(case, validation_commands), PROCESS_FALLBACK_FIELD_SOURCE)
    phase_status = {phase: "missing" for phase in PROCESS_PHASES}
    parsed_sources = _process_trace_sources(run_dir)
    if parsed_sources:
        facts = fallback_facts
        evidence_sources: list[str] = []
        parsed_kinds: list[str] = []
        for parsed_trace in parsed_sources:
            source = str(parsed_trace.get("_evidence_source") or "unknown")
            final_facts = _process_facts_from_trace_payload(parsed_trace)
            if not _phase_has_concrete_content(final_facts):
                continue
            facts, _source_used_fallback = _merge_process_facts(final_facts, facts, source)
            evidence_sources.append(source)
            parsed_kinds.append(str(parsed_trace.get("_trace_kind") or "unknown"))
        if evidence_sources:
            if _has_required_process_field_fallback(facts):
                evidence_sources.append(f"{PROCESS_FALLBACK_FIELD_SOURCE}:missing-fields")
            for phase in PROCESS_CORE_PHASES:
                phase_status[phase] = _phase_status_from_sources(phase, facts.get(phase))
            facts["evidence_source"] = evidence_sources[-1]
            facts.setdefault("evidence", {})["parsed_process_trace"] = parsed_kinds
            return facts, phase_status, evidence_sources

        facts = fallback_facts
        evidence_sources = [PROCESS_FALLBACK_FIELD_SOURCE]
    else:
        facts = fallback_facts
        evidence_sources = [PROCESS_FALLBACK_FIELD_SOURCE]
    for phase in PROCESS_CORE_PHASES:
        phase_status[phase] = _phase_status_from_sources(phase, facts.get(phase))
    return facts, phase_status, evidence_sources


def _has_required_process_field_fallback(facts: dict[str, Any]) -> bool:
    for phase in PROCESS_CORE_PHASES:
        phase_payload = facts.get(phase)
        if not isinstance(phase_payload, dict):
            return True
        if phase == "sdd" and _sdd_choice_gate_uses_fallback(phase_payload):
            return True
        field_sources = phase_payload.get("_field_sources")
        sources = field_sources if isinstance(field_sources, dict) else {}
        inferred = phase_payload.get("_inferred_fields")
        inferred_fields = {str(field) for field in inferred} if isinstance(inferred, list) else set()
        for field in _required_process_fields(phase):
            if field in inferred_fields or _source_is_fallback(str(sources.get(field) or "")):
                return True
    return False


def _process_trace_sources(run_dir: Path) -> list[dict[str, Any]]:
    parsed: list[dict[str, Any]] = []
    for trace in (
        _hook_process_trace(run_dir),
        _final_process_trace(run_dir / "final.md"),
        _artifact_process_trace(run_dir / "candidate-artifacts" / "CAPABILITY_EVIDENCE.md"),
        _artifact_process_trace(run_dir / "candidate-artifacts" / "process-trace.json"),
    ):
        if trace:
            parsed.append(trace)
    return parsed


def _final_process_trace(path: Path) -> dict[str, Any]:
    return _process_trace_from_path(path, "final.md")


def _artifact_process_trace(path: Path) -> dict[str, Any]:
    return _process_trace_from_path(path, f"candidate-artifacts/{path.name}")


def _process_trace_from_path(path: Path, evidence_prefix: str) -> dict[str, Any]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8", errors="ignore")
    parsed = _json_process_trace(text)
    if parsed:
        parsed["_evidence_source"] = parsed.get("_evidence_source") or f"{evidence_prefix}:process-trace-json"
        parsed["_trace_kind"] = parsed.get("_trace_kind") or "json"
        return parsed
    parsed = _compact_process_trace(text)
    if parsed:
        parsed["_evidence_source"] = parsed.get("_evidence_source") or f"{evidence_prefix}:compact-process-trace"
        parsed["_trace_kind"] = parsed.get("_trace_kind") or "compact"
        return parsed
    return {}


def _json_process_trace(text: str) -> dict[str, Any]:
    candidates: list[str] = []
    for match in re.finditer(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.IGNORECASE | re.DOTALL):
        candidates.append(match.group(1))
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        candidates.append(stripped)
    for candidate in candidates:
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and (
            "process_trace" in payload
            or "process_facts" in payload
            or {"phase_status", "traceability"} & set(payload)
        ):
            return _redact_process_trace_payload(payload)
    return {}


def _hook_process_trace(run_dir: Path) -> dict[str, Any]:
    for name in ("events.redacted.jsonl", "events.jsonl"):
        path = run_dir / name
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            parsed = _trace_payload_from_event(payload)
            if parsed:
                parsed["_evidence_source"] = f"hook_telemetry:{name}"
                parsed["_trace_kind"] = parsed.get("_trace_kind") or "hook"
                return parsed
    return {}


def _trace_payload_from_event(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        if "process_trace" in payload or "process_facts" in payload or {"phase_status", "traceability"} & set(payload):
            return _redact_process_trace_payload(payload)
        for key in ("message", "content", "text", "output"):
            value = payload.get(key)
            if isinstance(value, str):
                parsed = _json_process_trace(value) or _compact_process_trace(value)
                if parsed:
                    return parsed
        for value in payload.values():
            parsed = _trace_payload_from_event(value)
            if parsed:
                return parsed
    elif isinstance(payload, list):
        for item in payload:
            parsed = _trace_payload_from_event(item)
            if parsed:
                return parsed
    return {}


def _compact_process_trace(text: str) -> dict[str, Any]:
    if "Process Trace:" not in text:
        return {}
    block = text.split("Process Trace:", 1)[1]
    sections = _trace_sections(block)
    if not sections:
        return {}
    facts: dict[str, Any] = {}
    for phase in PROCESS_CORE_PHASES:
        section = sections.get(phase)
        if section is None:
            continue
        facts[phase] = _section_to_phase_facts(phase, section)
    return {"process_facts": _redact_process_trace_payload(facts), "_trace_kind": "compact-multiline"}


def _trace_sections(block: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    labels = {
        "pdd": "PDD:",
        "ddd": "DDD:",
        "sdd": "SDD:",
        "tdd": "TDD:",
        "validation": "Validation:",
        "residual_risk": "Residual Risk:",
    }
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        matched = None
        for key, marker in labels.items():
            if stripped.casefold().startswith(marker.casefold()):
                matched = key
                value = stripped[len(marker) :].strip()
                sections.setdefault(key, [])
                if value:
                    sections[key].append(value)
                break
        if matched:
            current = matched
            continue
        if current in PROCESS_CORE_PHASES:
            sections.setdefault(current, []).append(line)
    return {key: value for key, value in sections.items() if key in PROCESS_CORE_PHASES and value}


def _section_to_phase_facts(phase: str, lines: list[str]) -> dict[str, Any]:
    parsed = _parse_indented_section(lines)
    if not parsed:
        summary = redact_report_text(" ".join(line.strip() for line in lines if line.strip()))[:800]
        return _summary_phase_facts(phase, summary) if summary else {}
    return _normalize_phase_keys(phase, parsed)


def _parse_indented_section(lines: list[str]) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    current_key: str | None = None
    current_key_indent: int | None = None
    nested_key: str | None = None
    current_list_item: dict[str, Any] | None = None
    current_list_item_indent: int | None = None
    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            continue
        if (
            current_key
            and current_list_item is not None
            and current_list_item_indent is not None
            and isinstance(parsed.get(current_key), list)
            and raw_line.startswith((" ", "\t"))
            and _leading_indent(raw_line) > current_list_item_indent
            and not stripped.startswith("- ")
            and ":" in stripped
        ):
            item_key, item_value = stripped.split(":", 1)
            item_key = _normalize_trace_key(item_key)
            item_value = item_value.strip()
            current_list_item[item_key] = _coerce_trace_scalar(item_value) if item_value else {}
            continue
        if current_key and isinstance(parsed.get(current_key), dict) and nested_key and stripped.startswith("- "):
            target = parsed[current_key].setdefault(nested_key, [])
            if isinstance(target, list):
                target.append(_coerce_trace_scalar(stripped[2:].strip()))
            continue
        if stripped.startswith("- ") and current_key:
            target = parsed.setdefault(current_key, [])
            if isinstance(target, dict) and not target:
                target = []
                parsed[current_key] = target
            if isinstance(target, list):
                item = stripped[2:].strip()
                if ":" in item:
                    item_key, item_value = item.split(":", 1)
                    item_dict = {
                        _normalize_trace_key(item_key): _coerce_trace_scalar(item_value.strip()) if item_value.strip() else {}
                    }
                    target.append(item_dict)
                    current_list_item = item_dict
                    current_list_item_indent = _leading_indent(raw_line)
                else:
                    target.append(_coerce_trace_scalar(item))
                    current_list_item = None
                    current_list_item_indent = None
            continue
        if ":" in stripped:
            key, value = stripped.split(":", 1)
            key = _normalize_trace_key(key)
            value = value.strip()
            if (
                current_key
                and current_key_indent is not None
                and isinstance(parsed.get(current_key), dict)
                and raw_line.startswith((" ", "\t"))
                and _leading_indent(raw_line) > current_key_indent
            ):
                nested_key = key
                parsed[current_key][nested_key] = _coerce_trace_scalar(value) if value else []
                continue
            current_key = key
            current_key_indent = _leading_indent(raw_line)
            nested_key = None
            current_list_item = None
            current_list_item_indent = None
            if value:
                parsed[key] = _coerce_trace_scalar(value)
            else:
                parsed[key] = {}
            continue
        parsed.setdefault("_summary", []).append(_coerce_trace_scalar(stripped))
    return parsed


def _leading_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" \t"))


def _normalize_trace_key(key: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", key.strip().casefold()).strip("_")


def _coerce_trace_scalar(value: str) -> Any:
    clean = redact_report_text(value).strip()
    lowered = clean.casefold()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    return clean[:800]


def _normalize_phase_keys(phase: str, payload: dict[str, Any]) -> dict[str, Any]:
    aliases = {
        "pdd": {
            "acceptance": "acceptance_criteria",
            "validation": "validation_signal",
            "risks": "risk_surfaces",
        },
        "ddd": {
            "ownership": "ownership_decision",
            "side_effect_boundary": "side_effect_boundaries",
            "side_effects": "side_effect_boundaries",
        },
        "sdd": {
            "api": "public_api",
            "failure": "failure_modes",
            "failures": "failure_modes",
            "logging": "logging_decision",
        },
        "tdd": {
            "validation": "validation_commands",
            "tests": "validation_commands",
        },
    }
    normalized: dict[str, Any] = {}
    for key, value in payload.items():
        normalized[aliases.get(phase, {}).get(key, key)] = value
    for field in PROCESS_LIST_FIELDS.get(phase, ()):
        if field in normalized and not isinstance(normalized[field], list):
            normalized[field] = _trace_list(normalized[field])
    for field in PROCESS_MAPPING_FIELDS.get(phase, ()):
        if field in normalized:
            normalized[field] = _trace_mapping(normalized[field])
    if phase == "sdd":
        logging_decision = normalized.get("logging_decision")
        if logging_decision is not None and not isinstance(logging_decision, dict):
            normalized["logging_decision"] = {
                "needed": False,
                "rationale": str(logging_decision).strip(),
            }
    return normalized


def _trace_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return [item for item in value if _has_trace_value(item)]
    if _has_trace_value(value):
        return [value]
    return []


def _trace_mapping(value: Any) -> dict[str, list[Any]]:
    mapping: dict[str, list[Any]] = {}
    if isinstance(value, dict):
        for key, mapped_value in value.items():
            _add_trace_mapping(mapping, str(key), mapped_value)
        return mapping
    values = value if isinstance(value, list) else [value]
    for item in values:
        if isinstance(item, dict):
            for key, mapped_value in item.items():
                _add_trace_mapping(mapping, str(key), mapped_value)
            continue
        text = str(item).strip()
        if "->" not in text:
            continue
        source, mapped_value = text.split("->", 1)
        _add_trace_mapping(mapping, source, mapped_value)
    return mapping


def _add_trace_mapping(mapping: dict[str, list[Any]], source: str, mapped_value: Any) -> None:
    source = source.strip()
    if not source:
        return
    values = _trace_list(mapped_value)
    values = [value.strip() if isinstance(value, str) else value for value in values]
    if not values:
        return
    mapping.setdefault(source, [])
    mapping[source].extend(values)


def _summary_phase_facts(phase: str, summary: str) -> dict[str, Any]:
    if phase == "pdd":
        return {"problem": summary, "_summary": summary}
    if phase == "ddd":
        return {"domain_terms": [summary], "_summary": summary}
    if phase == "sdd":
        return {"modules": [summary], "_summary": summary}
    if phase == "tdd":
        return {"validation_commands": [summary], "_summary": summary}
    return {"_summary": summary}


def _process_facts_from_trace_payload(payload: dict[str, Any]) -> dict[str, Any]:
    facts = payload.get("process_facts")
    if isinstance(facts, dict):
        return _redact_process_trace_payload(facts)
    process_trace = payload.get("process_trace")
    if isinstance(process_trace, dict):
        return _redact_process_trace_payload(process_trace)
    core = {phase: payload.get(phase) for phase in PROCESS_CORE_PHASES if phase in payload}
    return _redact_process_trace_payload(core)


def _redact_process_trace_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {str(key): _redact_process_trace_payload(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [_redact_process_trace_payload(item) for item in payload]
    if isinstance(payload, str):
        return redact_report_text(payload)[:1200]
    return payload


def _merge_process_facts(
    final_facts: dict[str, Any],
    fallback_facts: dict[str, Any],
    evidence_source: str,
) -> tuple[dict[str, Any], bool]:
    merged: dict[str, Any] = {}
    used_fallback = False
    for key, value in fallback_facts.items():
        if key not in PROCESS_CORE_PHASES:
            merged[key] = value
    for key, value in final_facts.items():
        if key not in PROCESS_CORE_PHASES:
            merged[key] = value
    for phase in PROCESS_CORE_PHASES:
        final_phase = final_facts.get(phase)
        fallback_phase = fallback_facts.get(phase)
        if _phase_has_concrete_content(final_phase):
            phase_payload, phase_used_fallback = _merge_phase_facts(phase, final_phase, fallback_phase, evidence_source)
            merged[phase] = phase_payload
            used_fallback = used_fallback or phase_used_fallback
        else:
            merged[phase] = fallback_phase
            used_fallback = True
    return merged, used_fallback


def _merge_phase_facts(
    phase: str,
    final_phase: Any,
    fallback_phase: Any,
    evidence_source: str,
) -> tuple[dict[str, Any], bool]:
    final_payload = final_phase if isinstance(final_phase, dict) else _summary_phase_facts(phase, str(final_phase))
    fallback_payload = fallback_phase if isinstance(fallback_phase, dict) else {}
    merged = json.loads(json.dumps(fallback_payload))
    field_sources = _field_sources_for_payload(fallback_payload, default_source=PROCESS_FALLBACK_FIELD_SOURCE, phase=phase)
    existing_inferred = fallback_payload.get("_inferred_fields")
    inferred_fields = set(str(field) for field in existing_inferred) if isinstance(existing_inferred, list) else set()
    for key, value in fallback_payload.items():
        if key.startswith("_") or not _field_has_trace_value(phase, key, value):
            continue
        if key in inferred_fields or _source_is_fallback(str(field_sources.get(key) or PROCESS_FALLBACK_FIELD_SOURCE)):
            inferred_fields.add(key)
    for key, value in final_payload.items():
        if key.startswith("_"):
            if key not in {"_evidence_source", "_field_sources", "_inferred_fields"} and _has_trace_value(value):
                merged[key] = value
            continue
        if _field_has_trace_value(phase, key, value):
            merged[key] = value
            field_sources[key] = evidence_source
            inferred_fields.discard(key)
    merged["_field_sources"] = dict(sorted(field_sources.items()))
    merged["_evidence_source"] = evidence_source if any(source == evidence_source for source in field_sources.values()) else PROCESS_FALLBACK_FIELD_SOURCE
    if inferred_fields:
        merged["_inferred_fields"] = sorted(inferred_fields)
    else:
        merged.pop("_inferred_fields", None)
    required_fallback = any(field in inferred_fields for field in _required_process_fields(phase))
    return merged, required_fallback


def _mark_process_facts_source(facts: dict[str, Any], source: str) -> dict[str, Any]:
    marked = json.loads(json.dumps(facts))
    for phase in PROCESS_CORE_PHASES:
        phase_payload = marked.get(phase)
        if isinstance(phase_payload, dict):
            phase_payload["_evidence_source"] = source
            phase_payload["_field_sources"] = _field_sources_for_payload(phase_payload, default_source=source, phase=phase)
            if _source_is_fallback(source):
                phase_payload["_inferred_fields"] = sorted(phase_payload["_field_sources"])
    if _source_is_fallback(source):
        marked.setdefault("evidence_source", PROCESS_FALLBACK_FIELD_SOURCE)
    return marked


def _field_sources_for_payload(payload: dict[str, Any], *, default_source: str, phase: str | None = None) -> dict[str, str]:
    existing = payload.get("_field_sources")
    existing_sources = existing if isinstance(existing, dict) else {}
    return {
        str(key): str(existing_sources.get(key) or default_source)
        for key, value in payload.items()
        if not str(key).startswith("_") and _field_has_trace_value(phase, str(key), value)
    }


def _field_has_trace_value(phase: str | None, field: str, value: Any) -> bool:
    if phase == "sdd" and field == "design_decision_points" and isinstance(value, list):
        return True
    return _has_trace_value(value)


def _required_process_fields(phase: str) -> tuple[str, ...]:
    return PROCESS_REQUIRED_FIELDS.get(phase, ())


def _phase_status_from_sources(phase: str, payload: Any) -> str:
    if not isinstance(payload, dict) or not _phase_has_concrete_content(payload):
        return "missing"
    required_fields = _required_process_fields(phase)
    if not required_fields:
        return "present"
    field_sources = payload.get("_field_sources")
    sources = field_sources if isinstance(field_sources, dict) else {}
    raw_inferred_fields = payload.get("_inferred_fields")
    inferred_fields = {str(field) for field in raw_inferred_fields} if isinstance(raw_inferred_fields, list) else set()
    has_real_field = any(not _source_is_fallback(str(source)) for source in sources.values())
    real_required = 0
    invalid_real_required = 0
    fallback_or_inferred_required = 0
    for field in required_fields:
        value = payload.get(field)
        if not _field_has_trace_value(phase, field, value):
            continue
        source = str(sources.get(field) or "")
        if field in inferred_fields or _source_is_fallback(source):
            fallback_or_inferred_required += 1
        elif source and _required_field_shape_valid(phase, field, value):
            real_required += 1
        elif source:
            invalid_real_required += 1
    if real_required == len(required_fields):
        if phase == "sdd" and _sdd_choice_gate_uses_fallback(payload):
            return "degraded"
        return "present"
    if real_required or invalid_real_required or has_real_field:
        return "degraded"
    if fallback_or_inferred_required:
        return "inferred"
    return "missing"


def _required_field_shape_valid(phase: str, field: str, value: Any) -> bool:
    if phase == "pdd" and field == "problem":
        return isinstance(value, str) and bool(value.strip())
    if phase == "pdd" and field in {"acceptance_criteria", "constraints", "validation_signal"}:
        return _non_empty_trace_list(value)
    if phase == "ddd" and field in {"domain_terms", "invariants", "ownership_decision", "side_effect_boundaries"}:
        return _non_empty_trace_list(value)
    if phase == "sdd" and field in {"modules", "public_api", "error_contract", "failure_modes"}:
        return _non_empty_trace_list(value)
    if phase == "sdd" and field == "logging_decision":
        return isinstance(value, dict) and _has_trace_value(value)
    if phase == "sdd" and field == "design_decision_points":
        return isinstance(value, list)
    if phase == "sdd" and field == "assumption_policy":
        return isinstance(value, str) and "block_when_wrong_answer_changes" in value
    if phase == "tdd" and field in {"acceptance_to_tests", "invariant_to_tests_or_code", "public_api_to_tests"}:
        return isinstance(value, dict) and _has_trace_value(value)
    if phase == "tdd" and field in {"failure_mode_tests", "validation_commands"}:
        return _non_empty_trace_list(value)
    return _has_trace_value(value)


def _sdd_choice_gate_uses_fallback(payload: dict[str, Any]) -> bool:
    field_sources = payload.get("_field_sources")
    sources = field_sources if isinstance(field_sources, dict) else {}
    raw_inferred_fields = payload.get("_inferred_fields")
    inferred_fields = {str(field) for field in raw_inferred_fields} if isinstance(raw_inferred_fields, list) else set()
    for field in PROCESS_SDD_CHOICE_GATE_FIELDS:
        if field not in payload:
            return True
        if field == "design_decision_points" and not isinstance(payload.get(field), list):
            return True
        if field == "assumption_policy" and not str(payload.get(field, "")).strip():
            return True
        if field in inferred_fields or _source_is_fallback(str(sources.get(field) or "")):
            return True
    choices = payload.get("design_decision_points")
    if isinstance(choices, list) and not choices:
        rationale_field = _sdd_no_choice_rationale_field(payload)
        if rationale_field is None:
            return True
        rationale = str(payload.get(rationale_field, "")).strip().casefold().strip(".")
        if not rationale or rationale in PROCESS_SDD_GENERIC_RATIONALES or len(rationale.split()) < 4:
            return True
        if rationale_field in inferred_fields or _source_is_fallback(str(sources.get(rationale_field) or "")):
            return True
    if isinstance(choices, list):
        for choice in choices:
            if not isinstance(choice, dict):
                return True
            status = str(choice.get("user_choice_status", "")).strip()
            if choice.get("blocking") is True and status == "required":
                return True
            if status == "assumed_with_rationale":
                if not str(choice.get("safe_default_if_user_unavailable", "")).strip():
                    return True
                if not str(choice.get("residual_risk", "")).strip():
                    return True
                if not _has_trace_value(
                    [
                        choice.get("resolution_evidence"),
                        choice.get("why_user_choice_is_needed"),
                        choice.get("trigger"),
                    ]
                ):
                    return True
    return False


def _sdd_no_choice_rationale_field(payload: dict[str, Any]) -> str | None:
    for field in PROCESS_SDD_NO_CHOICE_RATIONALE_FIELDS:
        if str(payload.get(field, "")).strip():
            return field
    return None


def _non_empty_trace_list(value: Any) -> bool:
    return isinstance(value, list) and any(_has_trace_value(item) for item in value)


def _source_is_fallback(source: str) -> bool:
    normalized = str(source).split(":", 1)[0]
    return normalized in PROCESS_FALLBACK_SOURCE_ALIASES


def _phase_has_concrete_content(value: Any) -> bool:
    if not _has_trace_value(value):
        return False
    text = json.dumps(value, sort_keys=True).casefold() if not isinstance(value, str) else value.casefold()
    placeholders = (
        "problem + acceptance + constraints",
        "domain ownership + invariants + side-effect boundary",
        "modules + public api + error/logging decision",
        "tests/validation mapping",
    )
    return not any(placeholder in text for placeholder in placeholders)


def _has_trace_value(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(_has_trace_value(item) for item in value)
    if isinstance(value, dict):
        return any(not str(key).startswith("_") and _has_trace_value(item) for key, item in value.items())
    return value is True or value not in {None, False}


def _required_quality_gates_for_process_trace(facts: dict[str, Any]) -> list[str]:
    gates = [
        "pdd_acceptance_to_tdd_tests",
        "ddd_invariants_to_tdd_tests",
        "sdd_public_api_to_tdd_tests",
        "sdd_failure_modes_to_tdd_tests",
        "sdd_design_choice_gate",
    ]
    logging_decision = facts.get("sdd", {}).get("logging_decision") if isinstance(facts.get("sdd"), dict) else None
    if isinstance(logging_decision, dict) and logging_decision.get("needed") is True:
        gates.extend(
            [
                "logging_decision_has_type_level_fields_redaction",
                "logging_or_security_tests_present",
                "forbidden_secret_fields_absent",
            ]
        )
    return gates


def _process_stage_ownership() -> dict[str, str]:
    return {
        "pdd": "change-intake-compiler",
        "ddd": "domain-impact-modeler",
        "sdd": "architecture-impact-reviewer",
        "sdd_logging_decision": "logging-design-gate",
        "sdd_design_choice_gate": "development-process-orchestrator",
        "tdd": "quality-test-gate",
        "cross_stage_review": "ai-code-review-refactor",
        "repair": "ai-code-review-refactor",
        "rereview": "ai-code-review-refactor",
    }


def _final_mentions_review(run_dir: Path) -> bool:
    return _final_mentions(run_dir, ("review", "residual risk"))


def _final_mentions(run_dir: Path, needles: tuple[str, ...]) -> bool:
    final_path = run_dir / "final.md"
    if not final_path.exists():
        return False
    text = final_path.read_text(encoding="utf-8", errors="ignore").casefold()
    return any(needle in text for needle in needles)


def _final_has_route_manifest(run_dir: Path) -> bool:
    final_path = run_dir / "final.md"
    if not final_path.exists():
        return False
    text = final_path.read_text(encoding="utf-8", errors="ignore")
    return "changeforge_route" in text or (
        "selected_skills" in text and "selected_capabilities" in text and "required_quality_gates" in text
    )


def _trace_named_evidence(facts: dict[str, Any], field: str) -> Any:
    value = facts.get(field)
    if value is not None:
        return _redact_process_trace_payload(value)
    evidence = facts.get("evidence") if isinstance(facts.get("evidence"), dict) else {}
    value = evidence.get(field) if isinstance(evidence, dict) else None
    if value is not None:
        return _redact_process_trace_payload(value)
    return []


def _process_facts(case: CodexLiveCase, validation_commands: list[str]) -> dict[str, Any]:
    case_specific = _case_specific_process_facts(case, validation_commands)
    if case_specific is not None:
        return case_specific
    category = str(getattr(case, "category", str(case.id).split("/", 1)[0]))
    codegen_case = str(getattr(case, "codegen_case", str(case.id).split("/", 1)[-1]))
    coverage_dimensions = list(getattr(case, "coverage_dimensions", [category]))
    acceptance = [
        f"{case.id} expected behavior is observable through public API or documented setup/test contract",
        f"{case.id} passes deterministic assertion-backed grading benchmark {case.grading_benchmark}",
    ]
    invariants = [
        f"{case.id} keeps business rules in the owning domain, service, or module boundary",
        f"{case.id} keeps side effects outside pure domain/value-object decisions when relevant",
    ]
    public_api = ["candidate public API and executable validation scripts"]
    error_contract = ["grading result categorizes setup, test, security, or execution failure"]
    failure_modes = ["setup_failed", "test_suite_failed", "security_checks_failed", "codex_exec_failed"]
    return {
        "pdd": {
            "problem": f"Implement the benchmark case {case.id} without breaking its harness contract.",
            "user_or_system_impact": [f"benchmark case {case.id}", f"coverage dimensions: {', '.join(coverage_dimensions)}"],
            "acceptance_criteria": acceptance,
            "constraints": [
                "preserve setup.sh and benchmark harness entrypoints unless explicitly required",
                "do not write to HOME or CODEX_HOME",
                "avoid external network and new package dependencies unless explicitly required",
            ],
            "non_goals": ["no user-specific corpus, private archive, or hidden external file dependency"],
            "risk_surfaces": coverage_dimensions,
            "validation_signal": validation_commands,
        },
        "ddd": {
            "domain_terms": [category, codegen_case],
            "entities": [],
            "value_objects": [],
            "domain_services": [],
            "application_services": [],
            "adapters": [],
            "invariants": invariants,
            "ownership_decision": [f"use existing owner for {case.id} behavior"],
            "side_effect_boundaries": ["filesystem writes stay inside the candidate repository", "no HOME/CODEX_HOME writes"],
        },
        "sdd": {
            "modules": ["starter repository public API", "setup/test/security harness scripts"],
            "files_to_change": ["candidate repository files selected by inspection"],
            "public_api": public_api,
            "data_flow": ["task prompt -> candidate implementation -> setup/test/security grading -> result.json"],
            "error_contract": error_contract,
            "failure_modes": failure_modes,
            "logging_decision": {
                "needed": False,
                "rationale": "No product logging requirement is inferred for this generic case fallback; benchmark artifacts provide validation evidence.",
            },
            "design_decision_points": [],
            "no_design_choice_rationale": "Prompt/fixture constraints and repository inspection determine the benchmark implementation path; fallback metadata does not resolve an unresolved material SDD choice.",
            "assumption_policy": PROCESS_SDD_ASSUMPTION_POLICY,
            "metrics_traces_alerts": ["events.metrics.json", "events.redacted.jsonl", "grading-result.json"],
            "performance_or_concurrency_constraints": coverage_dimensions,
            "compatibility_and_migration": ["preserve harness entrypoints"],
            "rollback_or_recovery": ["revert candidate changes and rerun grading"],
        },
        "tdd": {
            "acceptance_to_tests": {criterion: validation_commands for criterion in acceptance},
            "invariant_to_tests_or_code": {invariant: validation_commands for invariant in invariants},
            "public_api_to_tests": {api: validation_commands for api in public_api},
            "failure_mode_tests": [
                {"failure_mode": failure, "tests": validation_commands}
                for failure in [*error_contract, *failure_modes]
            ],
            "logging_or_security_tests": [],
            "validation_commands": validation_commands,
            "red_green_refactor_trace": ["validation command recorded for the candidate result"],
        },
    }


def _case_specific_process_facts(
    case: CodexLiveCase,
    validation_commands: list[str],
) -> dict[str, Any] | None:
    if case.id == "security/ssrf-url-allowlist":
        acceptance = [
            "deny private, metadata, and loopback URLs",
            "revalidate redirect targets before fetching",
            "redact sensitive query values from diagnostics",
        ]
        invariants = [
            "unsafe URL is never fetched",
            "secret-bearing query is never logged",
        ]
        public_api = ["public URL validation/fetch entrypoint used by tests"]
        failure_modes = ["metadata URL denial", "redirect-to-private denial", "token query redaction"]
        return _mapped_process_facts(
            case,
            validation_commands,
            problem="Prevent SSRF by allowlisting safe outbound URLs and redacting sensitive diagnostics.",
            impact=["protect internal metadata, loopback, and private network resources"],
            acceptance=acceptance,
            risk_surfaces=["security", "ssrf", "redaction", "redirects"],
            domain_terms=["URL candidate", "redirect target", "network boundary", "sensitive query"],
            entities=["URL validation decision"],
            value_objects=["normalized URL"],
            invariants=invariants,
            ownership=["URL safety policy belongs to validation/service boundary before network fetch"],
            side_effects=["network fetch occurs only after allowlist and redirect revalidation pass"],
            modules=["URL validation module", "fetch/service entrypoint", "security tests"],
            public_api=public_api,
            data_flow=["raw URL -> normalized URL -> allowlist decision -> optional fetch -> redacted diagnostic"],
            error_contract=["deny unsafe URLs with a stable error category"],
            failure_modes=failure_modes,
            logging_decision={
                "needed": True,
                "log_types": ["security", "diagnostic"],
                "placement": ["security boundary", "service validation boundary"],
                "events": ["url_denied", "redirect_denied", "redaction_applied"],
                "levels": ["WARN"],
                "fields": ["operation", "error_category", "policy", "reason", "trace_id"],
                "redaction": ["raw URL query", "token", "signature", "session identifiers"],
                "correlation": ["trace_id", "request_id"],
                "cardinality_controls": ["route or policy category instead of raw URL", "status/error category instead of full target"],
                "rationale": "Security denial diagnostics must be explainable without leaking raw secret-bearing URL input.",
            },
            logging_tests=["metadata denied", "redirect revalidated", "token redacted"],
        )
    if case.id == "reliability/redis-cache-stampede-protection":
        acceptance = [
            "concurrent same-key miss causes one backend refresh",
            "fallback path is deterministic when refresh fails",
            "TTL jitter prevents synchronized expiration",
        ]
        invariants = [
            "same key shares an in-flight refresh",
            "source-of-truth backend is protected from duplicate concurrent refreshes",
        ]
        public_api = ["cache get/load public API used by tests"]
        failure_modes = ["cache miss storm", "refresh failure fallback", "lock contention"]
        return _mapped_process_facts(
            case,
            validation_commands,
            problem="Prevent cache stampede when concurrent callers miss the same Redis key.",
            impact=["protect source-of-truth backend under concurrent cache misses"],
            acceptance=acceptance,
            risk_surfaces=["reliability", "cache", "concurrency", "fallback"],
            domain_terms=["cache key", "in-flight refresh", "source-of-truth", "TTL jitter"],
            entities=["cache entry"],
            value_objects=["cache key"],
            invariants=invariants,
            ownership=["stampede control belongs to cache service, not callers"],
            side_effects=["backend refresh is coordinated behind per-key concurrency control"],
            modules=["cache service", "backend seam", "concurrency tests"],
            public_api=public_api,
            data_flow=["same-key callers -> cache miss -> shared in-flight refresh -> cache fill or fallback"],
            error_contract=["refresh failure is retryable or fallback-classified without duplicate backend pressure"],
            failure_modes=failure_modes,
            logging_decision={
                "needed": True,
                "log_types": ["diagnostic", "integration/dependency"],
                "placement": ["cache service", "backend dependency seam"],
                "events": ["cache_miss_storm", "refresh_fallback", "lock_contention"],
                "levels": ["WARN"],
                "fields": ["operation", "dependency", "status", "error_category", "entity_id_hash", "attempt", "retryable", "duration_ms", "fallback_used"],
                "redaction": ["raw cache key when it contains user input", "token", "PII"],
                "correlation": ["trace_id", "request_id"],
                "cardinality_controls": ["hash or bucket cache key", "aggregate hot-key events", "prefer metrics for high-frequency misses"],
                "rationale": "Operators need to diagnose stampede, fallback, and lock contention without per-miss noisy INFO logs.",
            },
            logging_tests=["backend.calls == 1", "fallback observable", "TTL jitter covered"],
        )
    if case.id == "structure/object-method-encapsulation-placement":
        acceptance = [
            "allowed, denied, expired, refund hold, and payment failure paths work",
            "pure domain decision has no payment or refund side effects",
            "tests use public API instead of private helper",
        ]
        invariants = [
            "domain cancellation decision remains pure",
            "payment and refund side effects stay in service/adapter orchestration",
        ]
        public_api = ["public cancellation API used by tests"]
        failure_modes = ["denied cancellation", "expired deadline", "refund hold", "payment failure"]
        return _mapped_process_facts(
            case,
            validation_commands,
            problem="Place cancellation behavior on the right object/service boundary without leaking payment side effects into pure domain code.",
            impact=["preserve cancellation correctness and payment/refund side-effect safety"],
            acceptance=acceptance,
            risk_surfaces=["structure", "domain ownership", "side effects", "public tests"],
            domain_terms=["order", "cancellation decision", "refund hold", "payment failure"],
            entities=["order"],
            value_objects=["cancellation window"],
            invariants=invariants,
            ownership=["pure cancellation decision belongs to domain object or domain service; provider calls belong to application service/adapter"],
            side_effects=["payment/refund provider calls remain outside pure domain/value object files"],
            modules=["order domain module", "cancellation service", "payment adapter boundary", "public tests"],
            public_api=public_api,
            data_flow=["public cancellation request -> pure decision -> service orchestrates adapter side effects"],
            error_contract=["denied, expired, refund hold, and payment failure states are distinguishable"],
            failure_modes=failure_modes,
            logging_decision={
                "needed": False,
                "rationale": "This structural benchmark is graded through public behavior and side-effect placement tests; no product logging requirement is needed for the case.",
            },
            logging_tests=[],
        )
    case_specs: dict[str, dict[str, Any]] = {
        "backend/service-method-vs-new-helper": {
            "problem": "Keep service behavior on the owning service method instead of hiding business logic in an unrelated helper.",
            "impact": ["preserve service public behavior and owner-boundary clarity"],
            "acceptance": [
                "requested behavior is implemented on existing service or owning method rather than unrelated helper",
                "existing public behavior remains compatible",
                "changed behavior is validated through service public API or tests",
            ],
            "risk_surfaces": ["backend-service-boundary", "implementation-structure"],
            "domain_terms": ["service method", "business operation", "owner object", "owner service"],
            "entities": ["service"],
            "value_objects": [],
            "invariants": [
                "business rule remains in owning service",
                "helper does not own domain decision",
            ],
            "ownership": ["owning service method or service facade keeps the business decision"],
            "side_effects": ["helper code may hold technical mechanics only, not business-rule authority"],
            "modules": ["service file", "existing helper only if genuinely technical", "service tests"],
            "public_api": ["existing service method or service facade used by tests"],
            "data_flow": ["public service call -> owning service method -> technical helper only for reusable mechanics"],
            "error_contract": ["service behavior remains compatible through the public API"],
            "failure_modes": ["new helper drift", "duplicate logic", "private API testing"],
            "logging_decision": {
                "needed": False,
                "rationale": "Service public behavior and placement tests are the primary evidence; no product log is required for this benchmark.",
            },
            "logging_tests": [],
        },
        "devex/helper-reuse-search": {
            "problem": "Reuse the existing same-pattern helper before adding duplicate implementation.",
            "impact": ["keep repository naming, placement, and helper behavior consistent"],
            "acceptance": [
                "reuse existing same-pattern function before adding new duplicate implementation",
                "change remains minimal and consistent with repository naming and placement",
                "regression test proves the fixed behavior",
            ],
            "risk_surfaces": ["devex-reuse", "implementation-structure"],
            "domain_terms": ["existing helper", "same-pattern implementation", "owner module"],
            "entities": [],
            "value_objects": [],
            "invariants": [
                "reuse preserves behavior and avoids divergent duplicate logic",
                "owner module remains the source of truth for helper behavior",
            ],
            "ownership": ["existing helper owner stays authoritative"],
            "side_effects": ["caller composes existing helper instead of adding new shared utility behavior"],
            "modules": ["existing helper owner", "caller module", "regression tests"],
            "public_api": ["existing helper or owner API used by tests"],
            "data_flow": ["caller input -> existing helper/owner API -> fixed output"],
            "error_contract": ["wrong helper placement or duplicate implementation fails review/grading"],
            "failure_modes": ["duplicate helper", "wrong placement", "unsearched reuse candidate"],
            "logging_decision": {
                "needed": False,
                "rationale": "Reuse-search evidence and regression tests are sufficient; no product logging requirement exists for this devex benchmark.",
            },
            "logging_tests": [],
        },
        "frontend/accessible-form-error-state": {
            "problem": "Expose form validation errors through accessible user-visible state.",
            "impact": ["keyboard and screen reader users receive clear error feedback"],
            "acceptance": ["invalid submit shows accessible error state", "focus and aria semantics remain usable", "valid submit path still works"],
            "risk_surfaces": ["frontend-accessibility", "form-validation", "experience-states"],
            "domain_terms": ["form field", "validation error", "accessible alert"],
            "entities": ["form"],
            "value_objects": ["validation message"],
            "invariants": ["error state is announced through accessible semantics", "valid input does not show stale error"],
            "ownership": ["form component owns interaction state and accessible error rendering"],
            "side_effects": ["DOM state updates stay in the component/view boundary"],
            "modules": ["form component", "validation state", "accessible behavior tests"],
            "public_api": ["rendered form behavior queried through accessible roles or labels"],
            "data_flow": ["user input -> validation -> accessible error state -> corrected submit"],
            "error_contract": ["invalid input maps to visible and announced error"],
            "failure_modes": ["missing role/aria error", "stale error after correction", "private selector-only test"],
            "logging_decision": {"needed": False, "rationale": "Accessible UI state tests are primary evidence; no production log is needed."},
            "logging_tests": [],
        },
        "data-api/backward-compatible-api-field": {
            "problem": "Add an API field without breaking existing consumers or response compatibility.",
            "impact": ["old and new API consumers can read the response safely"],
            "acceptance": ["new field is additive and optional or defaulted", "existing response contract remains valid", "compatibility tests cover old and new shapes"],
            "risk_surfaces": ["api-compatibility", "contract-testing", "data-model"],
            "domain_terms": ["API response", "backward-compatible field", "consumer contract"],
            "entities": ["response DTO"],
            "value_objects": ["optional field"],
            "invariants": ["existing required fields remain unchanged", "new field does not require old consumers to send or read it"],
            "ownership": ["API contract owner controls DTO/schema evolution"],
            "side_effects": ["serialization changes stay at API boundary"],
            "modules": ["DTO/schema", "API handler", "contract tests"],
            "public_api": ["public API response contract used by tests"],
            "data_flow": ["domain data -> DTO/schema -> serialized response -> consumer compatibility check"],
            "error_contract": ["missing optional field remains accepted for old clients"],
            "failure_modes": ["breaking required field", "schema validation failure", "old consumer incompatibility"],
            "logging_decision": {"needed": False, "rationale": "Contract and compatibility tests are sufficient; no product log is required for an additive field."},
            "logging_tests": [],
        },
        "integration/webhook-hmac-raw-body": {
            "problem": "Verify webhook HMAC signatures against the exact raw request body.",
            "impact": ["external webhook authenticity is enforced without corrupting payload verification"],
            "acceptance": ["valid raw-body signature passes", "tampered body or signature fails", "parsed body is not used for HMAC verification"],
            "risk_surfaces": ["integration-webhook", "secret-verification", "security-authenticity"],
            "domain_terms": ["webhook", "HMAC signature", "raw body"],
            "entities": ["webhook event"],
            "value_objects": ["signature digest"],
            "invariants": ["signature verification uses raw bytes", "invalid signature cannot reach handler side effects"],
            "ownership": ["integration boundary owns signature verification before event handling"],
            "side_effects": ["event handling side effects occur only after signature verification"],
            "modules": ["webhook entrypoint", "signature verifier", "integration tests"],
            "public_api": ["webhook handler public entrypoint used by tests"],
            "data_flow": ["raw body + signature header -> HMAC verifier -> event handler"],
            "error_contract": ["invalid signature returns denied/authenticity error"],
            "failure_modes": ["parsed-body HMAC mismatch", "tampered body accepted", "raw body logged"],
            "logging_decision": {
                "needed": True,
                "log_types": ["security", "integration/dependency"],
                "placement": ["webhook security boundary"],
                "events": ["webhook_signature_denied"],
                "levels": ["WARN"],
                "fields": ["operation", "policy", "error_category", "dependency", "status", "duration_ms", "trace_id"],
                "redaction": ["raw webhook body", "signature", "authorization header", "token"],
                "correlation": ["trace_id", "request_id"],
                "cardinality_controls": ["provider name and denial category only"],
                "rationale": "Signature denials need security diagnostics without logging raw body or signature secrets.",
            },
            "logging_tests": ["invalid signature denied", "raw webhook body not logged"],
        },
        "data-middleware/kafka-consumer-offset-dlq": {
            "problem": "Handle Kafka poison messages with correct offset and DLQ behavior.",
            "impact": ["consumer progress is preserved without losing failed messages"],
            "acceptance": ["successful messages commit offsets", "poison messages route to DLQ", "retry/terminal failure is distinguishable"],
            "risk_surfaces": ["message-queue", "idempotency", "observability"],
            "domain_terms": ["consumer offset", "DLQ", "poison message"],
            "entities": ["consumer message"],
            "value_objects": ["offset"],
            "invariants": ["message is committed only after successful handling or DLQ handoff", "poison message does not block the partition forever"],
            "ownership": ["consumer boundary owns offset commit and DLQ routing decisions"],
            "side_effects": ["DLQ publish and offset commit ordering remain explicit"],
            "modules": ["Kafka consumer", "DLQ publisher", "consumer tests"],
            "public_api": ["consumer process/handle entrypoint used by tests"],
            "data_flow": ["message -> handler -> success commit or DLQ publish -> offset decision"],
            "error_contract": ["retryable and terminal poison-message failures are categorized"],
            "failure_modes": ["offset committed before DLQ publish", "poison message loop", "lost message"],
            "logging_decision": {
                "needed": True,
                "log_types": ["diagnostic", "integration/dependency"],
                "placement": ["queue/worker"],
                "events": ["message_retry", "message_dlq"],
                "levels": ["WARN", "ERROR"],
                "fields": ["operation", "dependency", "status", "error_category", "attempt", "retryable", "duration_ms", "trace_id"],
                "redaction": ["raw message body", "token", "PII"],
                "correlation": ["trace_id", "correlation_id"],
                "cardinality_controls": ["topic and error category only", "message id hash only when allowed"],
                "rationale": "WARN covers retryable intermediate failures and ERROR is reserved for terminal DLQ handoff.",
            },
            "logging_tests": ["retry then DLQ distinction", "raw message body not logged"],
        },
        "performance/event-loop-blocking-async-path": {
            "problem": "Remove blocking work from an async path so the event loop remains responsive.",
            "impact": ["concurrent async callers avoid latency stalls"],
            "acceptance": ["blocking operation is moved off the event loop", "async public API remains compatible", "concurrency test proves responsiveness"],
            "risk_surfaces": ["performance-async", "concurrency-control", "reliability-backpressure"],
            "domain_terms": ["event loop", "blocking call", "async path"],
            "entities": ["async service"],
            "value_objects": [],
            "invariants": ["async path does not perform blocking IO or CPU work directly", "public coroutine contract is preserved"],
            "ownership": ["async service owns scheduling and backpressure decision"],
            "side_effects": ["blocking dependency runs through executor or async adapter boundary"],
            "modules": ["async service", "blocking dependency adapter", "concurrency tests"],
            "public_api": ["async public API used by tests"],
            "data_flow": ["async caller -> nonblocking scheduling -> dependency result -> response"],
            "error_contract": ["dependency failure remains categorized without blocking the event loop"],
            "failure_modes": ["event-loop stall", "unbounded executor fanout", "timeout masking"],
            "logging_decision": {"needed": False, "rationale": "Concurrency and latency tests are primary evidence; metrics/traces are better than per-call logs for hot async paths."},
            "logging_tests": [],
        },
        "performance/lock-held-across-io": {
            "problem": "Avoid holding a lock across IO so concurrency does not serialize or deadlock.",
            "impact": ["parallel callers avoid lock contention and deadlock risk"],
            "acceptance": ["lock guards only shared state mutation", "IO happens outside the critical section", "tests cover contention or ordering"],
            "risk_surfaces": ["performance-locking", "concurrency-control", "reliability-deadlock"],
            "domain_terms": ["lock", "critical section", "IO boundary"],
            "entities": ["shared state"],
            "value_objects": [],
            "invariants": ["shared state remains protected", "lock is not held across external IO"],
            "ownership": ["service or repository boundary owns lock scope"],
            "side_effects": ["external IO occurs after releasing the lock or before acquiring it"],
            "modules": ["locked service", "IO dependency", "concurrency tests"],
            "public_api": ["public operation with lock behavior exercised by tests"],
            "data_flow": ["read/update shared state under lock -> release lock -> perform IO"],
            "error_contract": ["IO failure does not leave lock-held state or corrupted shared state"],
            "failure_modes": ["lock contention stall", "deadlock", "partial state after IO failure"],
            "logging_decision": {"needed": False, "rationale": "Lock-scope tests and metrics are primary evidence; no per-operation INFO log is needed on the hot path."},
            "logging_tests": [],
        },
        "devex/bugfix-same-pattern-scan": {
            "problem": "Fix a bug and scan sibling patterns so the same defect is not left behind.",
            "impact": ["bug fix coverage extends to related occurrences without broad unrelated refactor"],
            "acceptance": ["verified defect has regression coverage", "same-pattern scan is recorded", "related occurrence decision is explicit"],
            "risk_surfaces": ["execution-discipline", "same-pattern-scan", "regression-testing"],
            "domain_terms": ["bugfix", "same-pattern scan", "regression test"],
            "entities": [],
            "value_objects": [],
            "invariants": ["local fix does not leave same defect in sibling path", "unchanged behavior remains compatible"],
            "ownership": ["owning module for the defect keeps the fix and related scan decisions"],
            "side_effects": ["scan does not mutate unrelated files unless the same defect is verified"],
            "modules": ["defect owner module", "sibling pattern files", "regression tests"],
            "public_api": ["public behavior or command that reproduces the defect"],
            "data_flow": ["repro input -> failing behavior -> fixed branch -> regression assertion"],
            "error_contract": ["historical failure mode is named and cannot recur under the regression test"],
            "failure_modes": ["local-only fix", "missing sibling defect", "unverified diagnosis"],
            "logging_decision": {"needed": False, "rationale": "Regression test and same-pattern scan are primary evidence; no product log is needed."},
            "logging_tests": [],
        },
    }
    spec = case_specs.get(case.id)
    if spec is not None:
        return _mapped_process_facts(case, validation_commands, **spec)
    return None


def _mapped_process_facts(
    case: CodexLiveCase,
    validation_commands: list[str],
    *,
    problem: str,
    impact: list[str],
    acceptance: list[str],
    risk_surfaces: list[str],
    domain_terms: list[str],
    entities: list[str],
    value_objects: list[str],
    invariants: list[str],
    ownership: list[str],
    side_effects: list[str],
    modules: list[str],
    public_api: list[str],
    data_flow: list[str],
    error_contract: list[str],
    failure_modes: list[str],
    logging_decision: dict[str, Any],
    logging_tests: list[str],
) -> dict[str, Any]:
    failure_tests = [{"failure_mode": failure, "tests": validation_commands} for failure in [*error_contract, *failure_modes]]
    return {
        "pdd": {
            "problem": problem,
            "user_or_system_impact": impact,
            "acceptance_criteria": acceptance,
            "constraints": [
                "preserve setup.sh and benchmark harness entrypoints unless explicitly required",
                "do not write to HOME or CODEX_HOME",
                "avoid external network and new package dependencies unless explicitly required",
            ],
            "non_goals": ["no user-specific corpus, private archive, or hidden external file dependency"],
            "risk_surfaces": risk_surfaces,
            "validation_signal": validation_commands,
        },
        "ddd": {
            "domain_terms": domain_terms,
            "entities": entities,
            "value_objects": value_objects,
            "domain_services": [],
            "application_services": [],
            "adapters": [],
            "invariants": invariants,
            "ownership_decision": ownership,
            "side_effect_boundaries": side_effects,
        },
        "sdd": {
            "modules": modules,
            "files_to_change": ["candidate repository files selected by inspection"],
            "public_api": public_api,
            "data_flow": data_flow,
            "error_contract": error_contract,
            "failure_modes": failure_modes,
            "logging_decision": logging_decision,
            "design_decision_points": [],
            "no_design_choice_rationale": "Prompt/fixture constraints and repository inspection determine the benchmark implementation path; fallback metadata does not resolve an unresolved material SDD choice.",
            "assumption_policy": PROCESS_SDD_ASSUMPTION_POLICY,
            "metrics_traces_alerts": ["grading-result.json", "events.metrics.json"],
            "performance_or_concurrency_constraints": risk_surfaces,
            "compatibility_and_migration": ["preserve benchmark harness contract"],
            "rollback_or_recovery": ["revert candidate change and rerun grading"],
        },
        "tdd": {
            "acceptance_to_tests": {criterion: validation_commands for criterion in acceptance},
            "invariant_to_tests_or_code": {invariant: validation_commands for invariant in invariants},
            "public_api_to_tests": {api: validation_commands for api in public_api},
            "failure_mode_tests": failure_tests,
            "logging_or_security_tests": logging_tests,
            "validation_commands": validation_commands,
            "red_green_refactor_trace": ["validation command recorded for the candidate result"],
        },
        "case_specific": True,
        "case_id": case.id,
    }


def _process_traceability(facts: dict[str, Any], validation_commands: list[str]) -> dict[str, bool]:
    pdd = facts.get("pdd") if isinstance(facts.get("pdd"), dict) else {}
    ddd = facts.get("ddd") if isinstance(facts.get("ddd"), dict) else {}
    sdd = facts.get("sdd") if isinstance(facts.get("sdd"), dict) else {}
    tdd = facts.get("tdd") if isinstance(facts.get("tdd"), dict) else {}
    acceptance_mapped = _mapped_items(pdd.get("acceptance_criteria"), tdd.get("acceptance_to_tests"))
    invariants_mapped = _mapped_items(ddd.get("invariants"), tdd.get("invariant_to_tests_or_code"))
    public_api_mapped = _mapped_items(sdd.get("public_api"), tdd.get("public_api_to_tests"))
    failure_mapped = _failure_modes_mapped(
        _combined_string_items(sdd.get("error_contract"), sdd.get("failure_modes")),
        tdd.get("failure_mode_tests"),
    )
    logging_mapped = _logging_mapped(sdd.get("logging_decision"), tdd, validation_commands)
    return {
        "pdd_acceptance_to_tdd_tests": acceptance_mapped,
        "ddd_invariants_to_tdd_tests": invariants_mapped,
        "sdd_public_api_to_tdd_tests": public_api_mapped,
        "sdd_failure_modes_to_tdd_tests": failure_mapped,
        "sdd_logging_to_tdd_tests": logging_mapped,
        "pdd_to_tests": acceptance_mapped,
        "ddd_invariants_to_code_or_tests": invariants_mapped,
        "sdd_public_api_to_tests": public_api_mapped,
        "tdd_validation_commands_present": bool(validation_commands),
    }


def _mapped_items(items: Any, mapping: Any) -> bool:
    if not isinstance(items, list) or not items or not isinstance(mapping, dict):
        return False
    for item in items:
        mapped = mapping.get(str(item))
        if not mapped:
            return False
    return True


def _failure_modes_mapped(failure_modes: Any, tests: Any) -> bool:
    if not isinstance(failure_modes, list) or not failure_modes or not isinstance(tests, list) or not tests:
        return False
    mapped: set[str] = set()
    for entry in tests:
        if isinstance(entry, dict) and entry.get("tests"):
            mapped.add(str(entry.get("failure_mode")))
        elif isinstance(entry, str) and entry.strip():
            return True
    return all(str(mode) in mapped for mode in failure_modes)


def _combined_string_items(*values: Any) -> list[str]:
    combined: list[str] = []
    for value in values:
        if isinstance(value, list):
            combined.extend(str(item) for item in value if str(item).strip())
        elif isinstance(value, str) and value.strip():
            combined.append(value)
    return combined


def _logging_mapped(logging_decision: Any, tdd: dict[str, Any], validation_commands: list[str]) -> bool:
    if not isinstance(logging_decision, dict):
        return False
    if logging_decision.get("needed") is False:
        return bool(str(logging_decision.get("rationale", "")).strip())
    if logging_decision.get("needed") is not True:
        return False
    required = ("log_types", "events", "levels", "fields", "redaction", "cardinality_controls")
    if any(not logging_decision.get(field) for field in required):
        return False
    logging_tests = tdd.get("logging_or_security_tests")
    if isinstance(logging_tests, list) and logging_tests:
        return True
    evidence_words = ("log", "redact", "security", "audit")
    return any(any(word in command.casefold() for word in evidence_words) for command in validation_commands)


def _validation_commands(case: CodexLiveCase) -> list[str]:
    return [
        f"python3 scripts/run-codegen-benchmarks.py --benchmark {case.grading_benchmark} --candidate-dir <candidate>"
    ]


def _selected_skills_for_variant(variant: str | None, case: CodexLiveCase | None = None) -> list[str]:
    if variant == "baseline_clean" or variant is None:
        return []
    skills = [
        "change-forge-router",
        "development-process-orchestrator",
        "change-intake-compiler",
        "domain-impact-modeler",
        "architecture-impact-reviewer",
        "backend-change-builder",
        "logging-design-gate",
        "quality-test-gate",
    ]
    case_id = getattr(case, "id", "") if case is not None else ""
    if case_id.startswith("reliability/"):
        skills.extend(["reliability-observability-gate", "data-middleware-change-builder"])
    if case_id.startswith(("security/", "logging/")):
        skills.extend(["security-privacy-gate", "logging-design-gate"])
    if case_id.startswith(("repo-intel/", "memory/", "validation/", "process/", "review/")):
        skills.append("ai-code-review-refactor")
    if case_id.startswith("compact/"):
        skills.extend(["quality-test-gate", "ai-code-review-refactor"])
    return list(dict.fromkeys(skills))


def _selected_capabilities_for_variant(variant: str | None, case: CodexLiveCase | None = None) -> list[str]:
    if variant == "baseline_clean" or variant is None:
        return []
    capabilities = [
        "acceptance-standard-definition",
        "module-boundary-design",
        "implementation-structure-design",
        "logging-error-handling",
        "contract-testing",
        "validation-broker",
    ]
    case_id = getattr(case, "id", "") if case is not None else ""
    if case_id.startswith("reliability/"):
        capabilities.extend(["cache-design", "concurrency-control", "observability-design", "fallback-design"])
    if case_id.startswith("logging/"):
        capabilities.extend(["logging-error-handling", "secret-redaction", "threat-modeling"])
    if case_id.startswith("security/"):
        capabilities.extend(["threat-modeling", "secret-configuration-security"])
    if case_id.startswith("repo-intel/"):
        capabilities.extend(["repository-context-map", "repository-graph-analysis"])
    if case_id.startswith("memory/"):
        capabilities.extend(["project-memory-governance"])
    if case_id.startswith("validation/"):
        capabilities.append("validation-broker")
    if case_id.startswith(("process/", "review/")):
        capabilities.extend(["engineering-stage-professionalism", "execution-trajectory-analysis"])
    if case_id.startswith("compact/"):
        capabilities.extend(
            [
                "agent-workflow-state-machine",
                "project-memory-governance",
                "validation-broker",
                "execution-trajectory-analysis",
            ]
        )
    if case_id.startswith("devex/"):
        capabilities.extend(["minimal-correct-implementation", "agent-execution-discipline"])
    if case_id.startswith("pressure/"):
        capabilities.extend(["agent-execution-discipline", "minimal-correct-implementation"])
    return list(dict.fromkeys(capabilities))


def _hook_guidance_bytes(variant: str | None) -> int:
    return 0 if variant != "skills_with_hooks_clean" else 2048


def _result_changeforge_metadata(args: argparse.Namespace, variant: str) -> dict[str, Any]:
    """Return strict-benchmark provenance for one variant."""
    project_install = variant in {"skills_only_clean", "skills_with_hooks_clean"}
    return {
        "changeforge_install_source": "current_repository" if project_install else "none",
        "changeforge_profile": args.profile if project_install else "none",
        "changeforge_hooks_enabled": variant == "skills_with_hooks_clean",
        "user_level_install_used": resolve_auth_policy(args) == "current-home-full",
    }


def _manifest_changeforge_metadata(args: argparse.Namespace, variants: list[str]) -> dict[str, Any]:
    """Return aggregate ChangeForge provenance for a run manifest."""
    project_install = any(variant in {"skills_only_clean", "skills_with_hooks_clean"} for variant in variants)
    return {
        "changeforge_install_source": "current_repository" if project_install else "none",
        "changeforge_profile": args.profile if project_install else "none",
        "changeforge_hooks_enabled": "skills_with_hooks_clean" in variants,
        "user_level_install_used": resolve_auth_policy(args) == "current-home-full",
    }


def _contamination_for_variant(variant: str, run_dir: Path) -> dict[str, Any]:
    if variant in {"baseline_clean", "current_home_smoke"}:
        return detect_baseline_contamination(run_dir)
    return {"contaminated": False, "signals": [], "files": []}


def _grading_status(
    case: CodexLiveCase,
    grading: dict[str, Any],
    contamination: dict[str, Any],
    variant: str,
) -> str:
    if case.grading_mode == "telemetry_only":
        return "telemetry_only"
    if variant == "baseline_clean" and contamination.get("contaminated"):
        return "contaminated"
    explicit = grading.get("grading_status")
    if explicit in {"passed", "failed", "not_collected"}:
        return str(explicit)
    if grading.get("all_passed") is True:
        return "passed"
    if grading.get("returncode") == 0:
        return "failed"
    return "not_collected"


def _artifact_status_after_grading(
    *,
    artifact_status: str,
    codex_returncode: int | None,
    grading_status: str,
    grading: dict[str, Any],
) -> str:
    """Prefer deterministic grading evidence over a late non-zero Codex transport exit."""
    if artifact_status not in {"failed", "partial"} or codex_returncode in {0, None}:
        return artifact_status
    if grading_status not in {"passed", "failed"}:
        return artifact_status
    if not any(key in grading for key in ("all_passed", "setup_passed", "test_suite_passed", "security_checks_passed")):
        return artifact_status
    return "collected"


def _failure_category(
    *,
    artifact_status: str,
    failure_stage: str | None,
    codex_returncode: int | None,
    contamination: dict[str, Any],
    grading_status: str,
    grading: dict[str, Any],
    benchmark_passed: bool,
) -> str:
    """Classify the first material failure for summary aggregation."""
    if artifact_status == "partial" and failure_stage == "install_changeforge":
        return "install_failed"
    if (artifact_status == "partial" and failure_stage == "codex_exec") or (
        artifact_status == "failed" and codex_returncode not in {0, None}
    ):
        return "codex_exec_failed"
    if contamination.get("contaminated"):
        return "contaminated"
    if grading_status == "telemetry_only":
        return "telemetry_only"
    if grading_status == "not_collected":
        return "grading_not_collected"
    if grading.get("setup_passed") is False:
        return "setup_failed"
    if grading.get("test_suite_passed") is False:
        return "test_suite_failed"
    if grading.get("security_checks_passed") is False:
        return "security_checks_failed"
    if benchmark_passed:
        return "none"
    return "grading_not_collected"


def _benchmark_eligible(
    args: argparse.Namespace,
    case: CodexLiveCase,
    artifact_status: str,
    grading_status: str,
    contamination: dict[str, Any],
    environment: dict[str, Any],
) -> bool:
    if args.benchmark_mode not in STRICT_BENCHMARK_MODES or resolve_auth_policy(args) not in STRICT_AUTH_POLICIES:
        return False
    if (
        environment.get("user_skills_visible") is not False
        or environment.get("user_config_loaded") is not False
        or environment.get("user_rules_loaded") is not False
        or environment.get("ignore_user_config") is not True
        or environment.get("ignore_rules") is not True
    ):
        return False
    return bool(
        artifact_status == "collected"
        and case.grading_mode == "assertion"
        and case.publishable_for_strict
        and grading_status in {"passed", "failed"}
        and not contamination.get("contaminated")
    )


def _copy_starter(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))


def _init_git(candidate_dir: Path) -> None:
    commands = (
        ["git", "init"],
        ["git", "config", "user.email", "codex-live-benchmark@example.invalid"],
        ["git", "config", "user.name", "Codex Live Benchmark"],
        ["git", "add", "."],
        ["git", "commit", "-m", "baseline"],
    )
    for command in commands:
        subprocess.run(command, cwd=candidate_dir, text=True, capture_output=True, shell=False, check=False)


def _render_prompt(case: CodexLiveCase, variant: str) -> str:
    prompt_variant = "baseline" if variant == "baseline_clean" else "changeforge"
    system = (ROOT / "evals" / "codex-live" / "prompts" / f"{prompt_variant}-system.md").read_text(encoding="utf-8")
    wrapper = (ROOT / "evals" / "codex-live" / "prompts" / "task-wrapper.md").read_text(encoding="utf-8")
    task = case.task_prompt.read_text(encoding="utf-8")
    return system + "\n\n" + wrapper.replace("{{TASK_PROMPT}}", task)


def build_codex_environment(
    args: argparse.Namespace,
    case: CodexLiveCase,
    variant: str,
    run_dir: Path,
) -> tuple[dict[str, str], dict[str, Any]]:
    """Build the subprocess environment and redacted result metadata."""
    del case, variant  # Reserved for future per-case policy without widening the public helper.
    auth_policy = resolve_auth_policy(args)
    caller_env = os.environ.copy()
    env = caller_env.copy()
    if auth_policy == "current-home-full":
        return env, _environment_metadata(
            auth_policy,
            home_label="<current-home-redacted>",
            codex_home_label="<current-home-redacted>",
            user_visible=True,
        )

    home = run_dir / "_home"
    home.mkdir(parents=True, exist_ok=True)
    env["HOME"] = str(home)
    if auth_policy == "isolated-api-key":
        codex_home = run_dir / "_codex-home"
        codex_home.mkdir(parents=True, exist_ok=True)
        env["CODEX_HOME"] = str(codex_home)
        return env, _environment_metadata(
            auth_policy,
            home_label="<temp>",
            codex_home_label="<temp>",
            user_visible=False,
        )

    current_codex_home = _current_codex_home_source(caller_env)
    borrowed_codex_home = _prepare_borrowed_auth_codex_home(current_codex_home)
    env["CODEX_HOME"] = str(borrowed_codex_home)
    env[INTERNAL_BORROWED_CODEX_HOME_ENV] = str(borrowed_codex_home)
    return env, _environment_metadata(
        auth_policy,
        home_label="<temp>",
        codex_home_label="<borrowed-current-auth>",
        user_visible=False,
    )


def _current_codex_home_source(env: dict[str, str]) -> str:
    if env.get("CODEX_HOME"):
        return str(Path(env["CODEX_HOME"]).expanduser())
    home = env.get("HOME")
    if home:
        return str(Path(home).expanduser() / ".codex")
    return str(Path.home() / ".codex")


def _prepare_borrowed_auth_codex_home(current_codex_home: str) -> Path:
    """Create a temp CODEX_HOME that references only current auth, not user capabilities."""
    borrowed_home = Path(tempfile.mkdtemp(prefix="codex-live-borrowed-auth-"))
    auth_source = Path(current_codex_home).expanduser() / "auth.json"
    if auth_source.exists():
        try:
            (borrowed_home / "auth.json").symlink_to(auth_source)
        except OSError:
            pass
    return borrowed_home


def _subprocess_env(env: dict[str, str]) -> dict[str, str]:
    """Return env for child processes without runner-internal cleanup metadata."""
    return {key: value for key, value in env.items() if key != INTERNAL_BORROWED_CODEX_HOME_ENV}


def _cleanup_borrowed_codex_home(env: dict[str, str]) -> None:
    path = env.get(INTERNAL_BORROWED_CODEX_HOME_ENV)
    if path:
        shutil.rmtree(path, ignore_errors=True)


def _environment_metadata(
    auth_policy: str,
    *,
    home_label: str,
    codex_home_label: str,
    user_visible: bool,
) -> dict[str, Any]:
    strict = auth_policy in STRICT_AUTH_POLICIES
    return {
        "home": home_label,
        "codex_home": codex_home_label,
        "user_home_visible": user_visible,
        "user_skills_visible": user_visible,
        "user_config_loaded": user_visible,
        "user_rules_loaded": user_visible,
        "current_auth_borrowed": auth_policy in {"borrow-current", "current-home-full"},
        "ignore_user_config": strict,
        "ignore_rules": strict,
        "plugins_disabled": strict,
        "auth_json_copied": False,
        "strict_benchmark_eligible": strict and not user_visible,
    }


def _command_metadata(args: argparse.Namespace, command: list[str], environment: dict[str, Any]) -> dict[str, Any]:
    redacted = redact_codex_command(command)
    auth_policy = resolve_auth_policy(args)
    return {
        "schema_version": 2,
        "program": redacted[0] if redacted else "codex",
        "args": redacted[1:],
        "command": redacted,
        "cwd": "<candidate>",
        "auth_policy": auth_policy,
        "codex_environment_policy": codex_environment_policy(auth_policy),
        "codex_home_mode": legacy_codex_home_mode(auth_policy),
        "env": {
            "HOME": environment.get("home", "<redacted>"),
            "CODEX_HOME": environment.get("codex_home", "<redacted>"),
            "CODEX_API_KEY": _secret_env_label("CODEX_API_KEY"),
            "OPENAI_API_KEY": _secret_env_label("OPENAI_API_KEY"),
        },
    }


def _secret_env_label(name: str) -> str:
    return "<redacted-if-present>" if os.environ.get(name) else "<unset>"


def _current_home_full_limitation() -> str:
    return (
        "Current-home-full mode may inherit user-level Codex config, auth, hooks, rules, skills, and trust state; "
        "it is smoke evidence only and cannot support strict comparative claims."
    )


def _install_changeforge(
    args: argparse.Namespace,
    candidate_dir: Path,
    env: dict[str, str],
    built_profiles: set[str],
    *,
    with_hooks: bool,
) -> None:
    if args.profile not in built_profiles:
        with BUILD_PROFILE_LOCK:
            if args.profile not in built_profiles:
                subprocess.run(
                    [sys.executable, str(ROOT / "scripts" / "build.py"), "--profile", args.profile],
                    cwd=ROOT,
                    env=_subprocess_env(env),
                    text=True,
                    capture_output=True,
                    shell=False,
                    check=True,
                )
                built_profiles.add(args.profile)
    command = [
        sys.executable,
        str(ROOT / "installers" / "install.py"),
        "--agent",
        "codex",
        "--scope",
        "project",
        "--target",
        str(candidate_dir),
        "--profile",
        args.profile,
    ]
    if with_hooks:
        command.append("--with-hooks")
    subprocess.run(
        command,
        cwd=ROOT,
        env=_subprocess_env(env),
        text=True,
        capture_output=True,
        shell=False,
        check=True,
    )


def _write_git_artifacts(candidate_dir: Path, run_dir: Path) -> None:
    diff = subprocess.run(
        ["git", "diff", "HEAD", "--"],
        cwd=candidate_dir,
        text=True,
        capture_output=True,
        shell=False,
        check=False,
    )
    status = subprocess.run(
        ["git", "status", "--short"],
        cwd=candidate_dir,
        text=True,
        capture_output=True,
        shell=False,
        check=False,
    )
    (run_dir / "diff.patch").write_text(redact_report_text(diff.stdout), encoding="utf-8")
    (run_dir / "git-status.txt").write_text(redact_report_text(status.stdout), encoding="utf-8")


def _remove_changeforge_support_artifacts_for_grading(candidate_dir: Path) -> None:
    """Keep installed ChangeForge hook support files out of candidate grading scans."""
    for support_dir in (".agents", ".codex"):
        shutil.rmtree(candidate_dir / support_dir, ignore_errors=True)


def _copy_candidate_evidence_artifacts(candidate_dir: Path, run_dir: Path) -> dict[str, Path]:
    """Preserve bounded candidate evidence without retaining the full candidate repo."""
    artifact_names = {
        "candidate_capability_evidence": "CAPABILITY_EVIDENCE.md",
        "candidate_compaction_context": "COMPACTION_CONTEXT.json",
        "candidate_process_trace": "process-trace.json",
    }
    copied: dict[str, Path] = {}
    target_dir = run_dir / "candidate-artifacts"
    for key, name in artifact_names.items():
        source = candidate_dir / name
        if not source.is_file():
            continue
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / name
        target.write_text(redact_report_text(source.read_text(encoding="utf-8", errors="ignore")), encoding="utf-8")
        copied[key] = target
    return copied


def _run_compaction_runtime_harness(
    *,
    case: CodexLiveCase,
    variant: str,
    run_dir: Path,
    candidate_dir: Path,
    events_redacted_path: Path,
    env: dict[str, str],
    grading_status: str,
    candidate_artifacts: dict[str, Path],
) -> dict[str, Any]:
    """Exercise real ChangeForge compact snapshot/reinject scripts for the compact live case."""
    if case.id != "compact/context-retention-after-compaction":
        return {"evidence": {}, "paths": {}}

    compaction_dir = run_dir / "compaction"
    compaction_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = compaction_dir / "hook-cache"
    hook_env = _subprocess_env(env)
    hook_env.update(
        {
            "XDG_CACHE_HOME": str(cache_dir),
            "CHANGEFORGE_AGENT": "codex",
            "CHANGEFORGE_HOOK_MODE": "warn",
            "CHANGEFORGE_TELEMETRY": "off",
            "CHANGEFORGE_MEMORY": "off",
        }
    )
    pre_event = {"hook_event_name": "PreCompact", "cwd": str(candidate_dir), "runtime": "codex"}
    post_event = {"hook_event_name": "PostCompact", "cwd": str(candidate_dir), "runtime": "codex"}
    session_event = {"hook_event_name": "SessionStart", "source": "compact", "cwd": str(candidate_dir), "runtime": "codex"}
    write_json(compaction_dir / "pre-compact-event.json", _redacted_compaction_event(pre_event))
    write_json(compaction_dir / "post-compact-event.json", _redacted_compaction_event(post_event))
    write_json(compaction_dir / "session-compact-event.json", _redacted_compaction_event(session_event))

    common = _load_hook_runtime_module("changeforge_common")
    contract = _load_hook_runtime_module("changeforge_compaction_contract")
    previous_env = {key: os.environ.get(key) for key in hook_env}
    try:
        os.environ.update(hook_env)
        _seed_compaction_harness_state(
            common,
            contract,
            case=case,
            variant=variant,
            candidate_dir=candidate_dir,
            grading_status=grading_status,
            candidate_artifacts=candidate_artifacts,
        )
    finally:
        _restore_env(previous_env)

    pre_completed = _run_hook_runtime_script("changeforge_compaction_snapshot.py", pre_event, hook_env, candidate_dir)
    pre_state = _load_hook_state(common, hook_env, candidate_dir)
    write_json(compaction_dir / "pre-compact-state.json", pre_state)
    post_completed = _run_hook_runtime_script("changeforge_compaction_reinject.py", post_event, hook_env, candidate_dir)
    post_state = _load_hook_state(common, hook_env, candidate_dir)
    write_json(compaction_dir / "post-compact-state.json", post_state)
    session_completed = _run_hook_runtime_script("changeforge_compaction_reinject.py", session_event, hook_env, candidate_dir)
    final_state = _load_hook_state(common, hook_env, candidate_dir)
    reinject_output = {
        "post_compact": _bounded_completed_process(post_completed),
        "session_compact": _bounded_completed_process(session_completed),
    }
    write_json(compaction_dir / "reinject-output.json", reinject_output)
    evidence = _compaction_retention_result(
        contract,
        final_state,
        pre_returncode=pre_completed.returncode,
        post_completed=post_completed,
        session_completed=session_completed,
        grading_status=grading_status,
        candidate_artifacts=candidate_artifacts,
    )
    write_json(compaction_dir / "retention-result.json", evidence)
    _append_compaction_runtime_events(events_redacted_path, evidence)
    return {
        "evidence": evidence,
        "paths": {
            "compaction_pre_event": _artifact_path(run_dir, compaction_dir / "pre-compact-event.json"),
            "compaction_post_event": _artifact_path(run_dir, compaction_dir / "post-compact-event.json"),
            "compaction_session_event": _artifact_path(run_dir, compaction_dir / "session-compact-event.json"),
            "compaction_pre_state": _artifact_path(run_dir, compaction_dir / "pre-compact-state.json"),
            "compaction_post_state": _artifact_path(run_dir, compaction_dir / "post-compact-state.json"),
            "compaction_reinject_output": _artifact_path(run_dir, compaction_dir / "reinject-output.json"),
            "compaction_retention_result": _artifact_path(run_dir, compaction_dir / "retention-result.json"),
        },
    }


def _load_hook_runtime_module(name: str) -> Any:
    scripts_dir = ROOT / "src" / "hook-runtime" / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    spec = importlib.util.spec_from_file_location(name, scripts_dir / f"{name}.py")
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _restore_env(previous_env: dict[str, str | None]) -> None:
    for key, value in previous_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def _seed_compaction_harness_state(
    common: Any,
    contract: Any,
    *,
    case: CodexLiveCase,
    variant: str,
    candidate_dir: Path,
    grading_status: str,
    candidate_artifacts: dict[str, Path],
) -> None:
    changed_paths = _candidate_changed_paths(candidate_dir)
    read_paths = [path for path in ("README.md", "tests/test_compaction_workflow.py") if (candidate_dir / path).exists()]
    if not read_paths:
        read_paths = ["README.md"]
    validation_status = "pass" if grading_status == "passed" else str(grading_status or "not_collected")
    selected_skills = _selected_skills_for_variant(variant, case)
    selected_capabilities = _selected_capabilities_for_variant(variant, case)
    active_context = {
        "route_id": f"codex-live:{case.id}:{variant}",
        "selected_skills": selected_skills,
        "selected_capabilities": selected_capabilities,
        "required_quality_gates": ["implementation gate", "test gate", "AI review gate", "security gate"],
        "current_stage": "rereview",
        "pdd_summary": ["preserve acceptance criteria and continue after compacted context"],
        "ddd_invariants": ["bounded compact state must not contain raw prompts or local absolute paths"],
        "sdd_decisions": ["compact snapshot and reinject remain hook-runtime responsibilities"],
        "tdd_validation_plan": ["run the compact retention assertion suite after repair"],
        "changed_paths": changed_paths,
        "read_paths": read_paths,
        "validation_results": [f"compact-retention validation: {validation_status}"],
        "validation_freshness": "fresh_after_latest_material_change",
        "review_findings": ["finding=post-compact continuation requires runtime reinject evidence"],
        "repair_events": ["repair=finding addressed after compact reinject"],
        "rereview_events": ["rereview=compact continuation evidence accepted"],
        "residual_risk": ["residual risk: live model behavior can still fail the candidate assertion suite"],
        "memory_references": ["memory:repeated-failure-fragile-file"],
        "repo_graph_references": ["repo-graph:compaction_workflow.py->tests/test_compaction_workflow.py"],
    }
    common.merge_state(
        candidate_dir,
        "codex",
        changed_paths=changed_paths,
        read_paths=read_paths,
        active_skill_context=active_context,
        turn_stage="implementation",
        suggested_skills=selected_skills,
        suggested_capabilities=selected_capabilities,
        suggested_gates=active_context["required_quality_gates"],
    )
    state = common.merge_state(
        candidate_dir,
        "codex",
        validation_command_seen=True,
        validation_results=active_context["validation_results"],
        active_skill_context=active_context,
        turn_stage="validation",
    )
    active_context["last_material_edit_index"] = int(state.get("last_material_edit_index") or 0)
    active_context["last_validation_command_index"] = int(state.get("last_validation_command_index") or 0)
    common.merge_state(
        candidate_dir,
        "codex",
        review_findings=active_context["review_findings"],
        repair_events=active_context["repair_events"],
        rereview_events=active_context["rereview_events"],
        closure_risk_surfaces=active_context["residual_risk"],
        reference_loads=active_context["memory_references"],
        reuse_findings=active_context["repo_graph_references"],
        active_skill_context=active_context,
        owner_skill="change-forge-router",
        reviewer_skill="ai-code-review-refactor",
        turn_stage="rereview",
    )
    del contract, candidate_artifacts


def _candidate_changed_paths(candidate_dir: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", "HEAD", "--"],
        cwd=candidate_dir,
        text=True,
        capture_output=True,
        shell=False,
        check=False,
    )
    paths = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if paths:
        return [path for path in paths if not Path(path).is_absolute()][:20]
    return ["compaction_workflow.py"]


def _run_hook_runtime_script(script_name: str, event: dict[str, Any], env: dict[str, str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "src" / "hook-runtime" / "scripts" / script_name)],
        input=json.dumps(event),
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )


def _load_hook_state(common: Any, env: dict[str, str], repo: Path) -> dict[str, Any]:
    previous_env = {key: os.environ.get(key) for key in env}
    try:
        os.environ.update(env)
        return common.load_state(repo)
    finally:
        _restore_env(previous_env)


def _bounded_completed_process(completed: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    return {
        "returncode": completed.returncode,
        "stdout": redact_report_text(completed.stdout or "")[:2000],
        "stderr": redact_report_text(completed.stderr or "")[:2000],
    }


def _compaction_retention_result(
    contract: Any,
    state: dict[str, Any],
    *,
    pre_returncode: int,
    post_completed: subprocess.CompletedProcess[str],
    session_completed: subprocess.CompletedProcess[str],
    grading_status: str,
    candidate_artifacts: dict[str, Path],
) -> dict[str, Any]:
    snapshot = contract.latest_snapshot(state.get("compaction_snapshots", []))
    missing = contract.missing_required_fields(snapshot) if snapshot else list(COMPACTION_REQUIRED_FIELDS)
    redacted = contract.redacted_required_fields(snapshot) if snapshot else []
    unusable = contract.context_unusable_fields(snapshot) if snapshot else []
    restored = contract.restored_required_fields(snapshot) if snapshot else []
    privacy_status = str(snapshot.get("privacy_redaction_status") or "not_collected") if snapshot else "not_collected"
    usable_status = str(snapshot.get("context_usable_status") or "not_collected") if snapshot else "not_collected"
    retention_status = (
        "pass"
        if snapshot
        and not missing
        and not redacted
        and not unusable
        and privacy_status == "pass"
        and usable_status == "pass"
        else ("fail" if privacy_status == "fail" else "partial")
    )
    active = state.get("active_skill_context") if isinstance(state.get("active_skill_context"), dict) else {}
    continuation_status = (
        "pass"
        if active.get("repair_events")
        and active.get("rereview_events")
        and post_completed.returncode == 0
        and session_completed.returncode == 0
        else "partial"
    )
    post_signal = "post_compact_reinject" in (post_completed.stdout or "") or post_completed.returncode == 0
    session_signal = "session_compact_reinject" in (session_completed.stdout or "") or session_completed.returncode == 0
    return {
        "pre_compact_snapshot_written": bool(snapshot and pre_returncode == 0),
        "post_compact_reinject_emitted": bool(post_signal),
        "session_compact_reinject_emitted": bool(session_signal),
        "pre_compact_snapshot_count": len(
            [
                item
                for item in state.get("compaction_snapshots", [])
                if isinstance(item, dict) and item.get("snapshot_kind") == "pre_compact"
            ]
        ),
        "post_compact_reinject_count": 1 if post_signal else 0,
        "session_compact_reinject_count": 1 if session_signal else 0,
        "restored_required_context_fields": restored,
        "missing_required_context_fields": missing,
        "redacted_required_context_fields": redacted,
        "context_unusable_fields": unusable,
        "privacy_redaction_status": privacy_status,
        "context_usable_status": usable_status,
        "context_retention_status": retention_status,
        "compact_after_repair_continuation_status": continuation_status,
        "candidate_compaction_context_present": bool(candidate_artifacts.get("candidate_compaction_context")),
        "candidate_capability_evidence_present": bool(candidate_artifacts.get("candidate_capability_evidence")),
        "grading_status": grading_status,
    }


def _redacted_compaction_event(event: dict[str, Any]) -> dict[str, Any]:
    redacted = dict(event)
    if "cwd" in redacted:
        redacted["cwd"] = "<candidate>"
    return redacted


def _append_compaction_runtime_events(events_redacted_path: Path, evidence: dict[str, Any]) -> None:
    events = [
        {
            "event": "compact_runtime_harness",
            "phase": "pre_compact",
            "status": "collected" if evidence.get("pre_compact_snapshot_written") else "partial",
        },
        {
            "event": "compact_runtime_harness",
            "phase": "post_compact",
            "status": "collected" if evidence.get("post_compact_reinject_emitted") else "partial",
        },
        {
            "event": "compact_runtime_harness",
            "phase": "session_compact",
            "status": "collected" if evidence.get("session_compact_reinject_emitted") else "partial",
        },
    ]
    with events_redacted_path.open("a", encoding="utf-8") as file:
        for event in events:
            file.write(json.dumps(event, sort_keys=True) + "\n")


def _compact_context_from_artifact(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "candidate-artifacts" / "COMPACTION_CONTEXT.json"
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"context_retention_status": "fail", "missing_required_context_fields": list(COMPACTION_REQUIRED_FIELDS)}
    if not isinstance(payload, dict):
        return {"context_retention_status": "fail", "missing_required_context_fields": list(COMPACTION_REQUIRED_FIELDS)}
    missing = [field for field in COMPACTION_REQUIRED_FIELDS if not payload.get(field)]
    restored = [field for field in COMPACTION_REQUIRED_FIELDS if field not in missing]
    return {
        "pre_compact_snapshot_written": payload.get("pre_compact_snapshot_written") is True,
        "post_compact_reinject_emitted": payload.get("post_compact_reinject_emitted") is True,
        "restored_required_context_fields": restored,
        "missing_required_context_fields": missing,
        "privacy_redaction_status": str(payload.get("privacy_redaction_status") or "not_collected"),
        "context_retention_status": str(payload.get("context_retention_status") or ("pass" if not missing else "partial")),
        "compact_after_repair_continuation_status": str(
            payload.get("compact_after_repair_continuation_status") or "not_collected"
        ),
        "compressed_state_not_overwritten_by_session_bootstrap": payload.get(
            "compressed_state_not_overwritten_by_session_bootstrap"
        )
        is True,
    }


def _redact_text_artifact(path: Path) -> None:
    if path.exists() and path.is_file():
        path.write_text(redact_report_text(path.read_text(encoding="utf-8", errors="ignore")), encoding="utf-8")


def _parse_events(events_path: Path, out_path: Path, redacted_path: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "parse-codex-jsonl.py"),
            "--events",
            str(events_path),
            "--out",
            str(out_path),
            "--redacted-out",
            str(redacted_path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        shell=False,
        check=False,
    )
    if completed.returncode != 0:
        return {"event_count": 0, "parse_errors": [{"line": 0, "error": completed.stderr.strip()}]}
    import json

    return json.loads(out_path.read_text(encoding="utf-8"))


def _grade(case: CodexLiveCase, candidate_dir: Path, grading_dir: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "grade-codex-live-benchmarks.py"),
            "--benchmark",
            case.grading_benchmark,
            "--candidate-dir",
            str(candidate_dir),
            "--out-dir",
            str(grading_dir),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        shell=False,
        check=False,
    )
    grading_path = grading_dir / "grading-result.json"
    if grading_path.exists():
        import json

        return json.loads(grading_path.read_text(encoding="utf-8"))
    return {
        "all_passed": False,
        "setup_passed": False,
        "test_suite_passed": False,
        "security_checks_passed": False,
        "setup_failure_reason": "unknown",
        "test_suite_failure_reason": "unknown",
        "security_failure_reason": "unknown",
        "first_failure_stage": "setup",
        "first_failure_excerpt": redact_report_text(completed.stderr.strip())[:1200],
        "setup_log_excerpt": "",
        "test_suite_log_excerpt": "",
        "security_log_excerpt": "",
        "returncode": completed.returncode,
        "error": completed.stderr.strip(),
    }


def _generate_summary(out_dir: Path, *, publish: bool, publish_current_home_smoke: bool) -> None:
    command = [
        sys.executable,
        str(ROOT / "scripts" / "generate-codex-live-summary.py"),
        "--run-dir",
        str(out_dir),
    ]
    if publish:
        command.append("--publish")
    if publish_current_home_smoke:
        command.append("--publish-current-home-smoke")
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, shell=False, check=False)
    if completed.returncode != 0:
        output = redact_report_text((completed.stderr or completed.stdout or "").strip())
        if len(output) > 1200:
            output = output[:1200] + "...<truncated>"
        action = "publish" if publish or publish_current_home_smoke else "generate"
        raise RuntimeError(f"generate-codex-live-summary.py failed during {action}: {output or 'no output'}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.runs < 1:
        print("run-codex-live-benchmarks: ERROR: --runs must be at least 1", file=sys.stderr)
        return 2
    if args.runs > 5 and not args.allow_many_runs:
        print("run-codex-live-benchmarks: ERROR: --runs > 5 requires --allow-many-runs", file=sys.stderr)
        return 2
    if args.codex_exec_retries < 0:
        print("run-codex-live-benchmarks: ERROR: --codex-exec-retries must be non-negative", file=sys.stderr)
        return 2
    if args.codex_idle_timeout_seconds < 0:
        print("run-codex-live-benchmarks: ERROR: --codex-idle-timeout-seconds must be non-negative", file=sys.stderr)
        return 2
    if args.codex_exec_retries > 2 and not args.allow_many_runs:
        print(
            "run-codex-live-benchmarks: ERROR: --codex-exec-retries > 2 requires --allow-many-runs",
            file=sys.stderr,
        )
        return 2
    if args.sandbox == "danger-full-access" and not danger_full_access_allowed(args, os.environ):
        print(
            "run-codex-live-benchmarks: ERROR: danger-full-access requires "
            "CHANGEFORGE_ALLOW_DANGER_FULL_ACCESS=1 or --allow-danger-full-access",
            file=sys.stderr,
        )
        return 2

    try:
        cases = load_case_registry()
    except Exception as exc:
        print(f"run-codex-live-benchmarks: ERROR: {exc}", file=sys.stderr)
        return 1
    if args.list:
        for case in cases:
            state = "enabled" if case.enabled else "disabled"
            dimensions = ",".join(case.coverage_dimensions)
            print(f"{case.id}\t{state}\ttier={case.tier}\tcoverage={dimensions}\tvariants={','.join(case.variants)}")
        return 0

    selected = select_cases(
        cases,
        benchmarks=args.benchmark,
        categories=args.category,
        tiers=args.tier,
        capability_core=args.capability_core,
    )
    variants = selected_variants(args)
    try:
        selected, selection_metadata = apply_runtime_selection(args, selected, variants)
    except ValueError as exc:
        print(f"run-codex-live-benchmarks: ERROR: {exc}", file=sys.stderr)
        return 2
    setattr(args, "_changeforge_selection_metadata", selection_metadata)
    if not selected:
        print("run-codex-live-benchmarks: ERROR: no cases selected", file=sys.stderr)
        return 1
    mode_errors = validate_mode_args(args, variants)
    if mode_errors:
        for error in mode_errors:
            print(f"run-codex-live-benchmarks: ERROR: {error}", file=sys.stderr)
        return 2

    allowed = live_execution_allowed(args, os.environ)
    out_dir = (args.resume_run or args.out or ROOT / "reports" / "codex-live-runs" / f"local-{utc_stamp()}").resolve()
    if args.dry_run or not allowed:
        write_skipped_manifest(out_dir, args=args, cases=selected, variants=variants, allowed=allowed)
        print(f"run-codex-live-benchmarks: wrote skipped manifest to {out_dir / 'run-manifest.json'}")
        return 0
    if resolve_auth_policy(args) == "current-home-full" and not current_codex_home_allowed(args, os.environ):
        print(
            f"run-codex-live-benchmarks: ERROR: {CURRENT_CODEX_HOME_REFUSAL_MESSAGE}",
            file=sys.stderr,
        )
        return 2

    try:
        manifest = run_live(args, out_dir, selected, variants)
    except RuntimeError as exc:
        print(f"run-codex-live-benchmarks: ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"run-codex-live-benchmarks: status={manifest['status']} run_dir={out_dir}")
    return 0 if manifest["status"] in {"collected", "partial"} else 1


if __name__ == "__main__":
    sys.exit(main())
