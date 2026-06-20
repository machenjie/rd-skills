#!/usr/bin/env python3
"""Run opt-in local Codex CLI benchmarks against codegen starter repos."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from codex_live_benchmark_lib import (
    PROFILES,
    ROOT,
    SANDBOXES,
    VARIANTS,
    CodexLiveCase,
    load_case_registry,
    redact_codex_command,
    relpath,
    safe_case_segment,
    utc_stamp,
    write_json,
)


REFUSAL_MESSAGE = (
    "Refusing to run codex exec without "
    "CHANGEFORGE_ENABLE_CODEX_LIVE_BENCHMARK=1 or --allow-live-codex"
)
CURRENT_CODEX_HOME_REFUSAL_MESSAGE = (
    "current Codex home mode requires "
    "CHANGEFORGE_ALLOW_CURRENT_CODEX_HOME=1 or --allow-current-codex-home"
)


def live_execution_allowed(args: argparse.Namespace, env: dict[str, str]) -> bool:
    """Return the exact opt-in predicate for live Codex execution."""
    return args.allow_live_codex or env.get("CHANGEFORGE_ENABLE_CODEX_LIVE_BENCHMARK") == "1"


def danger_full_access_allowed(args: argparse.Namespace, env: dict[str, str]) -> bool:
    """Return whether danger-full-access has its second explicit gate."""
    return args.allow_danger_full_access or env.get("CHANGEFORGE_ALLOW_DANGER_FULL_ACCESS") == "1"


def current_codex_home_allowed(args: argparse.Namespace, env: dict[str, str]) -> bool:
    """Return whether the runner may inherit the caller's Codex home/config."""
    return args.allow_current_codex_home or env.get("CHANGEFORGE_ALLOW_CURRENT_CODEX_HOME") == "1"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", action="append", default=[])
    parser.add_argument("--category", action="append", default=[])
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
        default="isolated",
        help="Use an isolated Codex home by default, or inherit the caller's current Codex home/config.",
    )
    parser.add_argument("--allow-current-codex-home", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--publish-summary", action="store_true")
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
    """Return requested variants with baseline/changeforge as the default pair."""
    variants = args.variant or ["baseline", "changeforge"]
    deduped: list[str] = []
    for variant in variants:
        if variant not in deduped:
            deduped.append(variant)
    return deduped


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
    if args.codex_home_mode == "current":
        limitations.append(_current_codex_home_limitation())
    write_json(
        out_dir / "run-manifest.json",
        {
            "schema_version": 1,
            "generated_by": "scripts/run-codex-live-benchmarks.py",
            "run_id": out_dir.name,
            "status": "skipped_not_opted_in",
            "dry_run": bool(args.dry_run),
            "live_execution_allowed": allowed,
            "live_execution_effective": False,
            "cases": [case.id for case in cases],
            "variants": variants,
            "runs_per_variant": args.runs,
            "profile": args.profile,
            "sandbox": args.sandbox,
            "codex_home_mode": args.codex_home_mode,
            "codex_invocations": [],
            "limitations": limitations,
        },
    )


def codex_command(args: argparse.Namespace, final_path: Path) -> list[str]:
    """Build the Codex exec command used for live runs."""
    command = [
        args.codex_bin,
        "exec",
        "--json",
        "--sandbox",
        args.sandbox,
        "--output-last-message",
        str(final_path),
    ]
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
    with events_path.open("w", encoding="utf-8") as events_file, stderr_path.open("w", encoding="utf-8") as stderr_file:
        return subprocess.run(
            command,
            cwd=cwd,
            input=prompt,
            stdout=events_file,
            stderr=stderr_file,
            text=True,
            env=env,
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
    elif any(result["status"] == "failed" for result in results):
        status = "partial" if any(result["status"] == "collected" for result in results) else "failed"
    else:
        status = "collected"

    limitations = [
        "Runs use local Codex CLI behavior and local account/model availability.",
        "Candidate grading is delegated to deterministic codegen benchmark checks.",
        "Telemetry metrics are bounded counts parsed from JSONL and exclude raw messages and command bodies.",
    ]
    if args.codex_home_mode == "current":
        limitations.append(_current_codex_home_limitation())

    manifest = {
        "schema_version": 1,
        "generated_by": "scripts/run-codex-live-benchmarks.py",
        "run_id": out_dir.name,
        "status": status,
        "dry_run": False,
        "live_execution_allowed": True,
        "live_execution_effective": True,
        "cases": [case.id for case in cases],
        "variants": variants,
        "runs_per_variant": args.runs,
        "profile": args.profile,
        "sandbox": args.sandbox,
        "codex_home_mode": args.codex_home_mode,
        "result_count": len(results),
        "limitations": limitations,
    }
    write_json(out_dir / "run-manifest.json", manifest)
    _generate_summary(out_dir, publish=args.publish_summary)
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

    env, env_metadata = _codex_env(args, out_dir, case, variant, run_index)
    if variant == "changeforge":
        _install_changeforge(args, candidate_dir, env, built_profiles)

    events_path = run_dir / "events.jsonl"
    stderr_path = run_dir / "codex-stderr.log"
    final_path = run_dir / "final.md"
    command = codex_command(args, final_path)
    write_json(
        run_dir / "codex-command.redacted.json",
        {
            "schema_version": 1,
            "command": redact_codex_command(command),
            "cwd": "<candidate>",
            "codex_home_mode": args.codex_home_mode,
            "env": env_metadata,
        },
    )

    status = "failed"
    codex_returncode: int | None = None
    failure: str | None = None
    try:
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
        status = "collected" if completed.returncode == 0 else "failed"
        if not final_path.exists():
            final_path.touch()
    except Exception as exc:  # live run should preserve artifacts for diagnosis
        failure = f"{type(exc).__name__}: {exc}"
        events_path.touch()
        stderr_path.write_text(f"{failure}\n", encoding="utf-8")
        final_path.touch()

    _write_git_artifacts(candidate_dir, run_dir)
    metrics = _parse_events(events_path, run_dir / "events.metrics.json")
    grading = _grade(case, candidate_dir, grading_dir)
    if not grading.get("all_passed"):
        status = "failed" if status == "failed" else "collected"

    limitations = [
        "Result reflects one local Codex CLI run for this variant.",
        "Raw Codex messages and command bodies are not persisted in parsed metrics.",
    ]
    if args.codex_home_mode == "current":
        limitations.append(_current_codex_home_limitation())

    result = {
        "schema_version": 1,
        "generated_by": "scripts/run-codex-live-benchmarks.py",
        "case_id": case.id,
        "variant": variant,
        "run_index": run_index,
        "status": status,
        "codex_home_mode": args.codex_home_mode,
        "codex_returncode": codex_returncode,
        "failure": failure,
        "paths": {
            "prompt": relpath(ROOT, run_dir / "prompt.md"),
            "events": relpath(ROOT, events_path),
            "final": relpath(ROOT, final_path),
            "diff": relpath(ROOT, run_dir / "diff.patch"),
            "git_status": relpath(ROOT, run_dir / "git-status.txt"),
            "grading": relpath(ROOT, grading_dir / "grading-result.json"),
        },
        "grading": grading,
        "metrics": metrics,
        "limitations": limitations,
    }
    write_json(run_dir / "result.json", result)
    if not args.keep_workdirs:
        shutil.rmtree(candidate_dir, ignore_errors=True)
    return result


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
    system = (ROOT / "evals" / "codex-live" / "prompts" / f"{variant}-system.md").read_text(encoding="utf-8")
    wrapper = (ROOT / "evals" / "codex-live" / "prompts" / "task-wrapper.md").read_text(encoding="utf-8")
    task = case.task_prompt.read_text(encoding="utf-8")
    return system + "\n\n" + wrapper.replace("{{TASK_PROMPT}}", task)


def _isolated_env(out_dir: Path, case: CodexLiveCase, variant: str, run_index: int) -> dict[str, str]:
    env = os.environ.copy()
    home = out_dir / "_isolated-home" / safe_case_segment(case.id) / variant / f"run-{run_index:02d}"
    codex_home = home / ".codex"
    home.mkdir(parents=True, exist_ok=True)
    codex_home.mkdir(parents=True, exist_ok=True)
    env["HOME"] = str(home)
    env["CODEX_HOME"] = str(codex_home)
    return env


def _codex_env(
    args: argparse.Namespace,
    out_dir: Path,
    case: CodexLiveCase,
    variant: str,
    run_index: int,
) -> tuple[dict[str, str], dict[str, str]]:
    if args.codex_home_mode == "current":
        env = os.environ.copy()
        return env, _codex_env_metadata("current", env)

    env = _isolated_env(out_dir, case, variant, run_index)
    return env, _codex_env_metadata("isolated", env)


def _codex_env_metadata(mode: str, env: dict[str, str]) -> dict[str, str]:
    metadata = {
        "HOME": "<isolated>" if mode == "isolated" else _inherited_home_label(env, "HOME"),
        "CODEX_HOME": "<isolated>" if mode == "isolated" else _inherited_codex_home_label(env),
        "CODEX_API_KEY": "<inherited-redacted>" if env.get("CODEX_API_KEY") else "<unset>",
        "OPENAI_API_KEY": "<inherited-redacted>" if env.get("OPENAI_API_KEY") else "<unset>",
    }
    if mode == "current":
        metadata["local_config_warning"] = "current mode may inherit user-level Codex config, auth, hooks, and trust state"
    return metadata


def _inherited_home_label(env: dict[str, str], key: str) -> str:
    return "<inherited-redacted>" if env.get(key) else "<unset>"


def _inherited_codex_home_label(env: dict[str, str]) -> str:
    if env.get("CODEX_HOME"):
        return "<inherited-redacted>"
    if env.get("HOME"):
        return "<default-under-inherited-home-redacted>"
    return "<unset>"


def _current_codex_home_limitation() -> str:
    return (
        "Current Codex home mode may inherit user-level Codex config, auth, hooks, and trust state; "
        "use a controlled Codex home before publishing comparative claims."
    )


def _install_changeforge(
    args: argparse.Namespace,
    candidate_dir: Path,
    env: dict[str, str],
    built_profiles: set[str],
) -> None:
    if args.profile not in built_profiles:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "build.py"), "--profile", args.profile],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            shell=False,
            check=True,
        )
        built_profiles.add(args.profile)
    subprocess.run(
        [
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
            "--with-universal-bootstrap",
        ],
        cwd=ROOT,
        env=env,
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
    (run_dir / "diff.patch").write_text(diff.stdout, encoding="utf-8")
    (run_dir / "git-status.txt").write_text(status.stdout, encoding="utf-8")


def _parse_events(events_path: Path, out_path: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "parse-codex-jsonl.py"),
            "--events",
            str(events_path),
            "--out",
            str(out_path),
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


def _generate_summary(out_dir: Path, *, publish: bool) -> None:
    command = [
        sys.executable,
        str(ROOT / "scripts" / "generate-codex-live-summary.py"),
        "--run-dir",
        str(out_dir),
    ]
    if publish:
        command.append("--publish")
    subprocess.run(command, cwd=ROOT, text=True, capture_output=True, shell=False, check=False)


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

    allowed = live_execution_allowed(args, os.environ)
    out_dir = (args.out or ROOT / "reports" / "codex-live-runs" / f"local-{utc_stamp()}").resolve()
    if args.dry_run or not allowed:
        write_skipped_manifest(out_dir, args=args, cases=selected, variants=variants, allowed=allowed)
        print(f"run-codex-live-benchmarks: wrote skipped manifest to {out_dir / 'run-manifest.json'}")
        return 0
    if args.codex_home_mode == "current" and not current_codex_home_allowed(args, os.environ):
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
