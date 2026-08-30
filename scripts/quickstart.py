#!/usr/bin/env python3
"""Build, install, and inspect the hookless rd-skills runtime."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

AGENTS = ("codex", "claude", "copilot", "cline", "openai-api")
SCOPES = ("project", "user", "admin")
EXPECTED_RUNTIME_SKILL_COUNT = 26


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
    runner: Callable[[list[str]], object] = subprocess.check_call,
) -> int:
    if dry_run:
        return 0
    for command in plan.commands:
        try:
            runner(list(command))
        except subprocess.CalledProcessError as exc:
            return int(exc.returncode)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="One-command hookless rd-skills setup.")
    parser.add_argument("--agent", choices=AGENTS, required=True)
    parser.add_argument("--scope", choices=SCOPES)
    parser.add_argument("--target", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-doctor", action="store_true")
    args = parser.parse_args()
    try:
        plan = build_plan(args)
    except ValueError as exc:
        print(f"quickstart: ERROR: {exc}", file=sys.stderr)
        return 2
    print("quickstart: command plan")
    for command in plan.commands:
        print("- " + " ".join(command))
    print("quickstart: summary")
    print(f"- expected standard Skills: {plan.expected_skill_count}")
    if plan.agent_profiles:
        print("- Agent Profiles: " + ", ".join(plan.agent_profiles))
    else:
        print("- Agent Profiles: not emitted for this host; standard Skills only")
    print("- next prompt: Use engineering-control-plane for bounded engineering work.")
    return run_plan(plan, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
