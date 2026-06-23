#!/usr/bin/env python3
"""One-command local ChangeForge build, install, and doctor flow."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from validation_utils import EXPECTED_PROFILE_TOP_LEVEL_COUNTS


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ("codex", "claude", "copilot", "cline", "openai-api")
SCOPES = ("project", "user", "admin")
PROFILES = ("auto", "recommended", "full", "dev")
ACTIVATION_LEVELS = ("none", "bootstrap", "hooks", "professional-injection")
HOOK_AGENTS = ("codex", "claude", "copilot")
HOOK_SCOPES = ("project", "user")
BOOTSTRAP_AGENTS = ("codex", "claude", "copilot", "cline")
EXPECTED_SKILL_COUNTS = dict(EXPECTED_PROFILE_TOP_LEVEL_COUNTS)
NEXT_PROMPTS = {
    "codex": "Use change-forge-router to classify this request before implementation.",
    "claude": "Use change-forge-router to classify this request before implementation.",
    "copilot": "Use change-forge-router to classify this request before implementation.",
    "cline": "Use change-forge-router to classify this request before implementation.",
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
    activation_level: str
    activation_status: str


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
        raise ValueError("--scope is required for runtime skill installs")
    if scope == "project" and target is None:
        raise ValueError("--target is required for project scope")


@dataclass(frozen=True)
class ActivationPlan:
    """Resolved quickstart activation behavior for installer and doctor commands."""

    level: str
    install_hooks: bool
    install_bootstrap: bool
    professional_injection: bool
    status: str


def resolve_activation(args: argparse.Namespace) -> ActivationPlan:
    """Resolve activation flags while keeping executable hooks opt-in."""
    if args.activation_level is not None and (args.with_hooks or args.with_bootstrap):
        raise ValueError(
            "--activation-level cannot be combined with --with-hooks or --with-bootstrap"
        )

    if args.activation_level is not None:
        level = args.activation_level
        legacy_bootstrap = False
    elif args.with_hooks:
        level = "hooks"
        legacy_bootstrap = bool(args.with_bootstrap)
    elif args.with_bootstrap:
        level = "bootstrap"
        legacy_bootstrap = False
    elif args.scope == "project" and args.agent in BOOTSTRAP_AGENTS:
        level = "bootstrap"
        legacy_bootstrap = False
    else:
        level = "none"
        legacy_bootstrap = False

    if args.agent == "openai-api" and level != "none":
        raise ValueError("--activation-level is not supported for openai-api zip output")

    install_hooks = level in {"hooks", "professional-injection"}
    professional_injection = level == "professional-injection"
    install_bootstrap = level == "bootstrap" or legacy_bootstrap

    if install_hooks and (args.agent not in HOOK_AGENTS or args.scope not in HOOK_SCOPES):
        raise ValueError(
            "hooks activation is supported only for codex, claude, or copilot project/user scope"
        )
    if install_bootstrap and not (args.scope == "project" and args.agent in BOOTSTRAP_AGENTS):
        raise ValueError(
            "bootstrap activation is supported only for codex, claude, copilot, "
            "or cline project scope"
        )

    status = _activation_status(level, install_hooks, install_bootstrap, professional_injection)
    return ActivationPlan(
        level=level,
        install_hooks=install_hooks,
        install_bootstrap=install_bootstrap,
        professional_injection=professional_injection,
        status=status,
    )


def _activation_status(
    level: str,
    install_hooks: bool,
    install_bootstrap: bool,
    professional_injection: bool,
) -> str:
    if level == "none":
        return "none (skills only; no bootstrap or hooks requested)"
    if professional_injection:
        return "professional-injection (executable hooks requested; runtime trust must be confirmed)"
    if install_hooks and install_bootstrap:
        return "hooks + bootstrap (executable hooks and advisory bootstrap requested)"
    if install_hooks:
        return "hooks (executable hooks requested; runtime trust must be confirmed)"
    if install_bootstrap:
        return "bootstrap (non-executable route-preflight fragment)"
    return level


def build_plan(args: argparse.Namespace) -> CommandPlan:
    """Build the command sequence without executing it."""
    validate_request(args.agent, args.scope, args.target)
    activation = resolve_activation(args)
    selected_profile = resolve_profile(args.agent, args.scope, args.profile)
    commands: list[list[str]] = [
        ["python3", "scripts/build.py", "--profile", selected_profile],
    ]

    install_command = ["python3", "installers/install.py", "--agent", args.agent]
    if args.agent != "openai-api":
        install_command.extend(["--scope", str(args.scope), "--profile", selected_profile])
        if args.target is not None:
            install_command.extend(["--target", str(args.target)])
        if activation.install_hooks:
            install_command.append("--with-hooks")
        if activation.professional_injection:
            install_command.append("--professional-injection")
        if activation.install_bootstrap:
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
        if activation.install_hooks:
            doctor_command.append("--check-hooks")
        if activation.install_bootstrap:
            doctor_command.append("--check-bootstrap")
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
        activation_level=activation.level,
        activation_status=activation.status,
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
    print(f"- activation status: {plan.activation_status}")
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
    parser.add_argument(
        "--activation-level",
        choices=ACTIVATION_LEVELS,
        help=(
            "Activation behavior: none, bootstrap, hooks, or professional-injection. "
            "Defaults to bootstrap for project scope and none elsewhere."
        ),
    )
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
