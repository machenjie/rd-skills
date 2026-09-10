#!/usr/bin/env python3
"""Build, install, and inspect the hookless rd-skills runtime."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
INSTALLER_DIR = ROOT / "installers"
if str(INSTALLER_DIR) not in sys.path:
    sys.path.insert(0, str(INSTALLER_DIR))

from changeforge_install import InstallError, product_next_step_lines  # noqa: E402

AGENTS = ("codex", "claude", "copilot", "cline", "openai-api")
SCOPES = ("project", "user", "admin")
EXPECTED_RUNTIME_SKILL_COUNT = 26
MATERIAL_SUCCESS_RE = re.compile(
    r"\b(?:warn(?:ing)?|legacy|backup|recover(?:y|able)?|restore|rollback|"
    r"migration|migrated|cleanup|cleaned\s+up|removed?)\b",
    re.IGNORECASE,
)
MATERIAL_CONTINUATION_RE = re.compile(r"^(?:\s+\S|\s*[-*]\s+\S)")


@dataclass(frozen=True)
class QuickstartPlan:
    expected_skill_count: int
    commands: tuple[tuple[str, ...], ...]
    doctor_expected: bool
    agent_profiles: tuple[str, ...]


def build_plan(args: argparse.Namespace) -> QuickstartPlan:
    scope = args.scope or ("project" if args.agent == "openai-api" else None)
    if scope is None:
        raise ValueError("--scope is required for runtime installs")
    if scope == "project" and args.agent != "openai-api" and args.target is None:
        raise ValueError("--target is required for project installs")
    build = ("python3", "scripts/build.py")
    install = [
        "python3", "installers/install.py", "--agent", args.agent,
        "--scope", scope,
    ]
    if args.target is not None:
        install.extend(("--target", str(args.target)))
    if args.dry_run:
        install.append("--dry-run")
    commands: list[tuple[str, ...]] = [build, tuple(install)]
    doctor_expected = args.agent != "openai-api" and not args.no_doctor
    if doctor_expected:
        doctor = [
            "python3", "installers/doctor.py", "--agent", args.agent,
            "--scope", scope,
        ]
        if args.target is not None:
            doctor.extend(("--target", str(args.target)))
        commands.append(tuple(doctor))
    return QuickstartPlan(
        expected_skill_count=EXPECTED_RUNTIME_SKILL_COUNT,
        commands=tuple(commands),
        doctor_expected=doctor_expected,
        agent_profiles=(
            ("main-control-agent", "analysis-agent", "task-agent", "review-agent")
            if args.agent in {"codex", "claude", "copilot"}
            else ()
        ),
    )


def run_plan(
    plan: QuickstartPlan,
    *,
    dry_run: bool,
    verbose: bool = False,
    runner: Callable[[list[str]], object] | None = None,
) -> int:
    if dry_run:
        return 0
    for command in plan.commands:
        argv = list(command)
        try:
            if runner is not None:
                runner(argv)
            elif verbose:
                subprocess.check_call(argv)
            else:
                completed = subprocess.run(
                    argv,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                if completed.returncode:
                    if completed.stdout:
                        print(completed.stdout, end="")
                    if completed.stderr:
                        print(completed.stderr, end="", file=sys.stderr)
                    return int(completed.returncode)
                material = _material_success_output(completed.stdout)
                if material:
                    print(material, end="")
                if completed.stderr:
                    print(completed.stderr, end="", file=sys.stderr)
        except subprocess.CalledProcessError as exc:
            return int(exc.returncode)
    return 0


def _material_success_output(output: str) -> str:
    """Keep successful mutation, warning, and recovery effects plus continuations."""

    kept: list[str] = []
    material_precedes = False
    for line in output.splitlines(keepends=True):
        if MATERIAL_SUCCESS_RE.search(line):
            kept.append(line)
            material_precedes = True
            continue
        if material_precedes and MATERIAL_CONTINUATION_RE.match(line):
            kept.append(line)
            continue
        material_precedes = False
    return "".join(kept)


def _print_plan(plan: QuickstartPlan) -> None:
    print("quickstart: command plan")
    for command in plan.commands:
        print("- " + " ".join(command))
    print("quickstart: diagnostics")
    print(f"- expected standard Skills: {plan.expected_skill_count}")
    if plan.agent_profiles:
        print("- Agent Profiles: " + ", ".join(plan.agent_profiles))
    else:
        print("- Agent Profiles: not emitted for this host; standard Skills only")


def _print_next_step(lines: tuple[str, ...]) -> None:
    print("Next:")
    for line in lines:
        print(line)


def main() -> int:
    parser = argparse.ArgumentParser(description="One-command hookless rd-skills setup.")
    parser.add_argument("--agent", choices=AGENTS, required=True)
    parser.add_argument("--scope", choices=SCOPES)
    parser.add_argument("--target", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-doctor", action="store_true")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show the command plan and detailed command output.",
    )
    args = parser.parse_args()
    try:
        plan = build_plan(args)
        next_step = product_next_step_lines(args.agent)
    except (ValueError, InstallError) as exc:
        print(f"quickstart: ERROR: {exc}", file=sys.stderr)
        return 2
    if args.dry_run or args.verbose:
        _print_plan(plan)
    result = run_plan(plan, dry_run=args.dry_run, verbose=args.verbose)
    if result:
        print(
            f"quickstart: ERROR: setup stopped after a command failed (exit {result}).",
            file=sys.stderr,
        )
        return result
    if args.dry_run:
        print("✓ dry run complete; no files changed")
        return 0
    print("✓ rd-skills setup complete")
    print()
    _print_next_step(next_step)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
