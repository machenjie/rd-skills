#!/usr/bin/env python3
"""Run opt-in local Codex CLI benchmarks against codegen starter repos."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from codex_live_benchmark_lib import (
    AUTH_POLICIES,
    BENCHMARK_MODES,
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
    parser.add_argument("--timeout-seconds", type=int, default=3600)
    parser.add_argument("--list", action="store_true")
    return parser.parse_args(argv)


def select_cases(
    cases: list[CodexLiveCase],
    *,
    benchmarks: list[str],
    categories: list[str],
) -> list[CodexLiveCase]:
    """Select enabled cases by id or category."""
    selected = [case for case in cases if case.enabled]
    if benchmarks:
        requested = set(benchmarks)
        selected = [case for case in selected if case.id in requested]
    if categories:
        requested_categories = set(categories)
        selected = [case for case in selected if case.category in requested_categories]
    return selected


def selected_variants(args: argparse.Namespace) -> list[str]:
    """Return requested variants with the mode-specific default set."""
    variants = args.variant or list(MODE_DEFAULT_VARIANTS[args.benchmark_mode])
    deduped: list[str] = []
    for variant in variants:
        if variant not in deduped:
            deduped.append(variant)
    return deduped


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
    return errors


def write_skipped_manifest(
    out_dir: Path,
    *,
    args: argparse.Namespace,
    cases: list[CodexLiveCase],
    variants: list[str],
    allowed: bool,
) -> None:
    """Write a skipped or dry-run manifest without planning Codex invocations."""
    limitations = [
        "Codex CLI was not invoked.",
        "Dry-run and non-opted-in reports are not publishable benchmark evidence.",
    ]
    if getattr(args, "codex_home_mode", None) == "current":
        limitations.append(_current_home_full_limitation())
    auth_policy = resolve_auth_policy(args)
    environment_policy = codex_environment_policy(auth_policy)
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
        return subprocess.run(
            command,
            cwd=cwd,
            input=prompt,
            stdout=events_file,
            stderr=stderr_file,
            text=True,
            env=process_env,
            timeout=args.timeout_seconds,
            shell=False,
            check=False,
        )


def run_live(args: argparse.Namespace, out_dir: Path, cases: list[CodexLiveCase], variants: list[str]) -> dict[str, Any]:
    """Execute selected live benchmark cases."""
    built_profiles: set[str] = set()
    results: list[dict[str, Any]] = []
    for case in cases:
        for variant in variants:
            if variant not in case.variants:
                continue
            for run_index in range(1, args.runs + 1):
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
        "result_count": len(results),
        "limitations": limitations,
    }
    write_json(out_dir / "run-manifest.json", manifest)
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
    artifact_status = "failed"
    codex_returncode: int | None = None
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
        completed = run_codex_exec(
            command,
            prompt=prompt,
            cwd=candidate_dir,
            events_path=events_path,
            stderr_path=stderr_path,
            args=args,
            env=env,
        )
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
    metrics = _parse_events(events_path, run_dir / "events.metrics.json", events_redacted_path)
    grading = _grade(case, candidate_dir, grading_dir)
    contamination = _contamination_for_variant(variant, run_dir)
    grading_status = _grading_status(case, grading, contamination, variant)
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
        "grading_mode": case.grading_mode,
        "publishable_for_strict": case.publishable_for_strict,
        "benchmark_eligible": benchmark_eligible,
        "benchmark_passed": benchmark_passed,
        "failure_category": failure_category,
        "contamination": contamination,
        "environment": environment,
        "codex_returncode": codex_returncode,
        "failure": failure,
        "failure_stage": failure_stage,
        "paths": {
            "prompt": _artifact_path(run_dir, run_dir / "prompt.md"),
            "events": _artifact_path(run_dir, events_redacted_path),
            "events_redacted": _artifact_path(run_dir, events_redacted_path),
            "events_metrics": _artifact_path(run_dir, run_dir / "events.metrics.json"),
            "final": _artifact_path(run_dir, final_path),
            "diff": _artifact_path(run_dir, run_dir / "diff.patch"),
            "git_status": _artifact_path(run_dir, run_dir / "git-status.txt"),
            "grading": _artifact_path(run_dir, grading_dir / "grading-result.json"),
        },
        "grading": grading,
        "metrics": metrics,
        "limitations": limitations,
    }
    write_json(run_dir / "result.json", result)
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
            print(f"{case.id}\t{state}\tvariants={','.join(case.variants)}")
        return 0

    selected = select_cases(cases, benchmarks=args.benchmark, categories=args.category)
    variants = selected_variants(args)
    if not selected:
        print("run-codex-live-benchmarks: ERROR: no cases selected", file=sys.stderr)
        return 1
    mode_errors = validate_mode_args(args, variants)
    if mode_errors:
        for error in mode_errors:
            print(f"run-codex-live-benchmarks: ERROR: {error}", file=sys.stderr)
        return 2

    allowed = live_execution_allowed(args, os.environ)
    out_dir = (args.out or ROOT / "reports" / "codex-live-runs" / f"local-{utc_stamp()}").resolve()
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
