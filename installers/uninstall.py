#!/usr/bin/env python3
"""Uninstall only ChangeForge-managed skills from a target directory."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from changeforge_install import (
    AGENTS,
    SCOPES,
    InstallError,
    apply_bootstrap_uninstall,
    apply_hook_uninstall,
    bootstrap_supported,
    hooks_supported,
    managed_names,
    plan_bootstrap_uninstall,
    plan_hook_uninstall,
    read_manifest,
    remove_managed,
    render_bootstrap_uninstall_plan,
    render_hook_uninstall_plan,
    resolve_target_dir,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Uninstall ChangeForge-managed skills.")
    parser.add_argument("--agent", choices=AGENTS)
    parser.add_argument("--scope", choices=SCOPES)
    parser.add_argument(
        "--target",
        type=Path,
        help=(
            "Project root when --agent/--scope project are supplied, explicit user/admin "
            "skills dir override, or exact skills dir when no agent/scope is supplied."
        ),
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--keep-hooks",
        action="store_true",
        help="Keep ChangeForge-managed hook runtime artifacts for hook-capable agents.",
    )
    parser.add_argument(
        "--keep-bootstrap",
        action="store_true",
        help="Keep standalone .changeforge advisory bootstrap fragments for project installs.",
    )
    args = parser.parse_args()

    try:
        agent_scope_supplied = bool(args.agent or args.scope)
        if args.agent or args.scope:
            if not args.agent or not args.scope:
                raise InstallError("--agent and --scope must be supplied together")
            if args.agent == "openai-api":
                print("uninstall: openai-api uses zip bundles; no runtime skills are removed.")
                return 0
            target_dir = resolve_target_dir(args.agent, args.scope, args.target)
        else:
            if args.target is None:
                raise InstallError("--target is required when --agent/--scope are not supplied")
            target_dir = args.target.expanduser().resolve()

        manifest = read_manifest(target_dir)
        names = managed_names(manifest) if manifest is not None else set()
        existing = sorted(name for name in names if (target_dir / name).exists())
        hook_plan = None
        bootstrap_plan = None

        if agent_scope_supplied and args.agent is not None and args.scope is not None:
            if args.keep_hooks:
                print("uninstall: hooks: kept because --keep-hooks was requested")
            elif hooks_supported(args.agent, args.scope):
                hook_plan = plan_hook_uninstall(args.agent, args.scope, args.target)
            else:
                print(f"uninstall: hooks: unsupported for {args.agent} {args.scope}; skipped")

            if args.keep_bootstrap:
                print("uninstall: bootstrap: kept because --keep-bootstrap was requested")
            elif bootstrap_supported(args.agent, args.scope) and args.target is not None:
                bootstrap_plan = plan_bootstrap_uninstall(args.target)

        if args.dry_run:
            print(f"uninstall: dry run for {target_dir}")
            if manifest is None:
                print(f"uninstall: no ChangeForge skill manifest found in {target_dir}")
            else:
                print(f"uninstall: would remove {len(existing)} managed skill directorie(s)")
                for name in existing:
                    print(f"uninstall: would remove {target_dir / name}")
                print(f"uninstall: would remove {target_dir / '.changeforge-install-manifest.json'}")
            _print_hook_plan(hook_plan)
            _print_bootstrap_plan(bootstrap_plan)
            return 0

        if manifest is None:
            print(f"uninstall: no ChangeForge skill manifest found in {target_dir}.")
        else:
            remove_managed(target_dir, names, dry_run=False)
            print(f"uninstall: removed {len(existing)} ChangeForge-managed skill directorie(s).")
        _print_hook_plan(hook_plan)
        if hook_plan is not None:
            hook_actions = bool(
                hook_plan.files or hook_plan.directories or hook_plan.config_target
            )
            apply_hook_uninstall(hook_plan, dry_run=False)
            if hook_actions:
                print("uninstall: hooks: removed ChangeForge-managed hook artifacts.")
        _print_bootstrap_plan(bootstrap_plan)
        if bootstrap_plan is not None:
            bootstrap_actions = bool(bootstrap_plan.files)
            apply_bootstrap_uninstall(bootstrap_plan, dry_run=False)
            if bootstrap_actions:
                print("uninstall: bootstrap: removed standalone ChangeForge bootstrap fragments.")
        return 0
    except InstallError as exc:
        print(f"uninstall: ERROR: {exc}", file=sys.stderr)
        return 1


def _print_hook_plan(plan: object) -> None:
    if plan is None:
        return
    for line in render_hook_uninstall_plan(plan):
        print(f"uninstall: {line}")


def _print_bootstrap_plan(plan: object) -> None:
    if plan is None:
        return
    for line in render_bootstrap_uninstall_plan(plan):
        print(f"uninstall: {line}")


if __name__ == "__main__":
    raise SystemExit(main())
