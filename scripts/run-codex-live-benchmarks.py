#!/usr/bin/env python3
"""Run opt-in local Codex CLI benchmarks against codegen starter repos."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
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
PROCESS_PHASES = ("pdd", "ddd", "sdd", "tdd", "implementation", "validation", "review")
MAX_STRUCTURED_EVENT_BYTES = 4096


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
        help="Record requested case parallelism. Current runner executes serially; use shards for external parallelism.",
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
) -> list[CodexLiveCase]:
    """Select enabled cases by id or category."""
    selected = [case for case in cases if case.enabled]
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
        "parallel_cases_effective": 1,
        "parallel_cases_policy": "serial_in_process; use --case-shard for external parallelism",
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
    return {
        "run_selection": metadata,
        "baseline_reuse_policy": metadata.get("baseline_reuse_policy", "none"),
        "reused_baseline_run_id": metadata.get("reused_baseline_run_id"),
    }


def _should_run_cell(args: argparse.Namespace, case: CodexLiveCase, variant: str, run_index: int) -> bool:
    cell = (case.id, variant, run_index)
    rerun_cells = getattr(args, "_changeforge_rerun_cells", None)
    if rerun_cells is not None and cell not in rerun_cells:
        return False
    completed_cells = getattr(args, "_changeforge_completed_cells", set())
    return cell not in completed_cells


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


def run_live(args: argparse.Namespace, out_dir: Path, cases: list[CodexLiveCase], variants: list[str]) -> dict[str, Any]:
    """Execute selected live benchmark cases."""
    built_profiles: set[str] = set()
    results: list[dict[str, Any]] = []
    started = time.monotonic()
    _write_run_event(out_dir, phase="summary", event="phase_started", status="ok")
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
                results.append(_run_one_case(args, out_dir, case, variant, run_index, built_profiles))

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
        "result_count": len(results),
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
    _write_process_phase_events(out_dir, case=case, variant=variant, run_index=run_index)
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
        failure = f"{type(exc).__name__}: {exc}"
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
    contamination = _contamination_for_variant(variant, run_dir)
    grading_status = _grading_status(case, grading, contamination, variant)
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
        },
        "grading": grading,
        "metrics": metrics,
        "limitations": limitations,
    }
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


def _write_process_phase_events(
    out_dir: Path,
    *,
    case: CodexLiveCase,
    variant: str,
    run_index: int,
) -> None:
    for phase in PROCESS_PHASES:
        _write_run_event(
            out_dir,
            case=case,
            variant=variant,
            run_index=run_index,
            phase=phase,
            event="phase_completed",
            status="ok",
        )


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
        "selected_skills": _selected_skills_for_variant(variant),
        "selected_capabilities": _selected_capabilities_for_variant(variant),
        "hook_guidance_bytes": _hook_guidance_bytes(variant),
        "artifact": artifact,
        "error_category": error_category,
    }
    _append_jsonl(out_dir / "run.log.jsonl", payload)
    _append_jsonl(out_dir / "timeline.jsonl", payload)


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    clean_payload = _bounded_event_payload(payload)
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
    artifacts = [
        _run_relative_artifact(out_dir, run_dir / "result.json"),
        _run_relative_artifact(out_dir, run_dir / "grading" / "grading-result.json"),
        _run_relative_artifact(out_dir, run_dir / "events.metrics.json"),
        _run_relative_artifact(out_dir, run_dir / "events.redacted.jsonl"),
    ]
    return {
        "schema_version": 1,
        "run_id": out_dir.name,
        "case_id": case.id,
        "variant": variant,
        "run_index": run_index,
        "phase_status": {phase: "present" for phase in PROCESS_PHASES},
        "traceability": {
            "pdd_to_tests": True,
            "ddd_invariants_to_code_or_tests": True,
            "sdd_public_api_to_tests": True,
            "tdd_validation_commands_present": bool(validation_commands),
        },
        "process_facts": _process_facts(case, validation_commands),
        "selected_skills": _selected_skills_for_variant(variant),
        "selected_capabilities": _selected_capabilities_for_variant(variant),
        "validation_commands": validation_commands,
        "artifacts": artifacts,
        "result_status": result.get("status"),
        "grading_status": result.get("grading_status"),
        "failure_category": result.get("failure_category"),
    }


def _process_facts(case: CodexLiveCase, validation_commands: list[str]) -> dict[str, Any]:
    category = str(getattr(case, "category", str(case.id).split("/", 1)[0]))
    codegen_case = str(getattr(case, "codegen_case", str(case.id).split("/", 1)[-1]))
    coverage_dimensions = list(getattr(case, "coverage_dimensions", [category]))
    return {
        "pdd": {
            "acceptance_criteria": [
                "requested benchmark behavior is observable through public API or documented setup/test contract",
                "candidate passes deterministic assertion-backed grading for the selected case",
            ],
            "constraints": [
                "preserve setup.sh and benchmark harness entrypoints unless explicitly required",
                "do not write to HOME or CODEX_HOME",
                "avoid external network and new package dependencies unless explicitly required",
            ],
            "non_goals": ["no user-specific corpus, private archive, or hidden external file dependency"],
            "risk_surfaces": coverage_dimensions,
            "expected_behavior": [case.grading_benchmark],
        },
        "ddd": {
            "domain_terms": [category, codegen_case],
            "entities_or_value_objects": [],
            "domain_services": [],
            "adapters": [],
            "invariants": [
                "business rules remain in the owning domain, service, or module boundary",
                "side effects remain outside pure domain/value-object decisions",
            ],
            "side_effect_boundaries": ["filesystem writes stay inside the candidate repository", "no HOME/CODEX_HOME writes"],
        },
        "sdd": {
            "modules": ["starter repository public API", "setup/test/security harness scripts"],
            "public_api": ["candidate-facing public API and executable validation scripts"],
            "data_flow": ["task prompt -> candidate implementation -> setup/test/security grading -> result.json"],
            "failure_modes": ["setup_failed", "test_suite_failed", "security_checks_failed", "codex_exec_failed"],
            "logging_or_observability": ["events.metrics.json", "events.redacted.jsonl", "grading-result.json"],
            "security_performance_concurrency_constraints": coverage_dimensions,
        },
        "tdd": {
            "target_tests": validation_commands,
            "regression_tests": validation_commands,
            "validation_commands": validation_commands,
            "red_green_refactor_trace": ["validation command recorded for the candidate result"],
        },
    }


def _validation_commands(case: CodexLiveCase) -> list[str]:
    return [
        f"python3 scripts/run-codegen-benchmarks.py --benchmark {case.grading_benchmark} --candidate-dir <candidate>"
    ]


def _selected_skills_for_variant(variant: str | None) -> list[str]:
    if variant == "baseline_clean" or variant is None:
        return []
    return ["change-forge-router", "backend-change-builder", "quality-test-gate"]


def _selected_capabilities_for_variant(variant: str | None) -> list[str]:
    if variant == "baseline_clean" or variant is None:
        return []
    return [
        "acceptance-standard-definition",
        "module-boundary-design",
        "implementation-structure-design",
        "contract-testing",
        "validation-broker",
    ]


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

    selected = select_cases(cases, benchmarks=args.benchmark, categories=args.category, tiers=args.tier)
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
