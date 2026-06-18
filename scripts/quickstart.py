#!/usr/bin/env python3
"""One-command local ChangeForge build, install, and doctor flow."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ("codex", "claude", "copilot", "openai-api")
SCOPES = ("project", "user", "admin")
PROFILES = ("auto", "recommended", "full", "dev")
EXPECTED_SKILL_COUNTS = {
    "recommended": 19,
    "full": 26,
    "dev": 148,
}
NEXT_PROMPTS = {
    "codex": "Use change-forge-router to classify this request before implementation.",
    "claude": "Use change-forge-router to classify this request before implementation.",
    "copilot": "Use change-forge-router to classify this request before implementation.",
    "openai-api": "Upload the desired skill zip, then ask the model to use change-forge-router.",
}


@dataclass(frozen=True)
class CommandPlan:
    """Resolved quickstart command plan for tests and execution."""

    agent: str
    scope: str | None
    target: Path | None
    requested_profile: str
    selected_profile: str
    commands: list[list[str]]
    doctor_expected: bool
    installed_target: str
    expected_skill_count: int
    next_prompt: str


def resolve_profile(agent: str, scope: str | None, requested_profile: str) -> str:
    """Resolve `auto` to the smallest profile that fits the requested target."""
    if requested_profile != "auto":
        return requested_profile
    if agent == "openai-api":
        return "recommended"
    if scope == "project":
        return "full"
    return "recommended"


def validate_request(agent: str, scope: str | None, target: Path | None) -> None:
    """Validate quickstart-specific argument requirements before planning."""
    if agent != "openai-api" and scope is None:
        raise ValueError("--scope is required for codex, claude, and copilot")
    if scope == "project" and target is None:
        raise ValueError("--target is required for project scope")


def build_plan(args: argparse.Namespace) -> CommandPlan:
    """Build the command sequence without executing it."""
    validate_request(args.agent, args.scope, args.target)
    selected_profile = resolve_profile(args.agent, args.scope, args.profile)
    commands: list[list[str]] = [
        ["python3", "scripts/build.py", "--profile", selected_profile],
    ]

    install_command = ["python3", "installers/install.py", "--agent", args.agent]
    if args.agent != "openai-api":
        install_command.extend(["--scope", str(args.scope), "--profile", selected_profile])
        if args.target is not None:
            install_command.extend(["--target", str(args.target)])
        if args.with_hooks:
            install_command.append("--with-hooks")
        if args.with_bootstrap:
            install_command.append("--with-bootstrap")
        if args.dry_run:
            install_command.append("--dry-run")
    else:
        install_command.extend(["--profile", selected_profile, "--dry-run"])
    commands.append(install_command)

    doctor_expected = args.agent != "openai-api" and not args.no_doctor
    if doctor_expected:
        doctor_command = [
            "python3",
            "installers/doctor.py",
            "--agent",
            args.agent,
            "--scope",
            str(args.scope),
            "--profile",
            selected_profile,
        ]
        if args.target is not None:
            doctor_command.extend(["--target", str(args.target)])
        commands.append(doctor_command)

    return CommandPlan(
        agent=args.agent,
        scope=args.scope,
        target=args.target,
        requested_profile=args.profile,
        selected_profile=selected_profile,
        commands=commands,
        doctor_expected=doctor_expected,
        installed_target=_installed_target(args.agent, args.scope, args.target),
        expected_skill_count=EXPECTED_SKILL_COUNTS[selected_profile],
        next_prompt=NEXT_PROMPTS[args.agent],
    )


def _installed_target(agent: str, scope: str | None, target: Path | None) -> str:
    if agent == "openai-api":
        return "dist/openai-api/zips/<profile>"
    if scope == "project":
        return str(target)
    if target is not None:
        return str(target)
    return f"{agent} {scope} default target"


def render_command(command: Sequence[str]) -> str:
    """Render a simple shell-safe command for human dry-run output."""
    return " ".join(command)


def print_plan(plan: CommandPlan) -> None:
    """Print the commands quickstart will run."""
    print("quickstart: command plan")
    for command in plan.commands:
        print(f"- {render_command(command)}")


def print_summary(plan: CommandPlan, doctor_status: str) -> None:
    """Print the concise final summary required by the quickstart contract."""
    print("quickstart: summary")
    print(f"- selected profile: {plan.selected_profile}")
    print(f"- installed target: {plan.installed_target}")
    print(f"- expected top-level skills: {plan.expected_skill_count}")
    print(f"- doctor status: {doctor_status}")
    print(f"- next prompt: {plan.next_prompt}")


def run_plan(
    plan: CommandPlan,
    *,
    dry_run: bool,
    runner: Callable[[Sequence[str]], subprocess.CompletedProcess[str] | None],
) -> int:
    """Execute the command plan, returning a process-style exit code."""
    print_plan(plan)
    if dry_run:
        print_summary(plan, "not run (dry-run)")
        return 0

    try:
        for command in plan.commands:
            runner(command)
    except subprocess.CalledProcessError as exc:
        print(
            "quickstart: ERROR: command failed with exit "
            f"{exc.returncode}: {render_command(exc.cmd)}",
            file=sys.stderr,
        )
        return int(exc.returncode) if exc.returncode else 1

    if plan.agent == "openai-api":
        doctor_status = "not applicable (zip output)"
    elif plan.doctor_expected:
        doctor_status = "passed"
    else:
        doctor_status = "skipped (--no-doctor)"
    print_summary(plan, doctor_status)
    return 0


def _subprocess_runner(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, cwd=ROOT)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", choices=AGENTS, required=True)
    parser.add_argument("--scope", choices=SCOPES)
    parser.add_argument("--target", type=Path)
    parser.add_argument("--profile", choices=PROFILES, default="auto")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--with-hooks", action="store_true")
    parser.add_argument("--with-bootstrap", action="store_true")
    parser.add_argument("--no-doctor", action="store_true")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Reserved for future confirmation prompts; current quickstart is non-interactive.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    args = parse_args(argv)
    try:
        plan = build_plan(args)
    except ValueError as exc:
        print(f"quickstart: ERROR: {exc}", file=sys.stderr)
        return 2
    return run_plan(plan, dry_run=args.dry_run, runner=_subprocess_runner)


if __name__ == "__main__":
    sys.exit(main())
