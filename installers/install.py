#!/usr/bin/env python3
"""Install built ChangeForge skills from dist/ into a supported target."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from changeforge_install import (
    AGENTS,
    PROFILES,
    SCOPES,
    InstallError,
    apply_bootstrap_install,
    apply_hook_install,
    backup_existing,
    bootstrap_supported,
    find_unmanaged_conflicts,
    hooks_supported,
    list_skill_dirs,
    make_manifest,
    managed_names,
    plan_bootstrap_install,
    plan_hook_install,
    read_manifest,
    render_bootstrap_plan,
    render_hook_plan,
    replace_with_source,
    resolve_source_profile_dir,
    resolve_target_dir,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Install built ChangeForge skills from dist/.")
    parser.add_argument("--agent", choices=AGENTS, required=True)
    parser.add_argument(
        "--scope",
        choices=SCOPES,
        help="Install scope. Required for agent runtimes; optional for openai-api zip-only output.",
    )
    parser.add_argument("--target", type=Path, help="Project root, or explicit user/admin skills dir.")
    parser.add_argument("--profile", choices=PROFILES, default="recommended")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--backup", action="store_true")
    parser.add_argument(
        "--with-hooks",
        action="store_true",
        help="Also install optional hooks (codex/claude/copilot project or user).",
    )
    parser.add_argument(
        "--hooks-dry-run",
        action="store_true",
        help="Show the hook install plan without writing hook files.",
    )
    parser.add_argument(
        "--with-bootstrap",
        action="store_true",
        help="Also install the advisory route-preflight bootstrap fragment (any project install).",
    )
    parser.add_argument(
        "--bootstrap-dry-run",
        action="store_true",
        help="Show the bootstrap install plan without writing the fragment.",
    )
    args = parser.parse_args()

    try:
        scope = args.scope or ("project" if args.agent == "openai-api" else None)
        if scope is None:
            raise InstallError("--scope is required for codex, claude, and copilot installs")

        if args.agent == "openai-api":
            source_dir = resolve_source_profile_dir(args.agent, scope, args.profile)
            zip_count = len(sorted(source_dir.glob("*.zip"))) if source_dir.exists() else 0
            print(
                "install: openai-api is zip-only; "
                f"{zip_count} {args.profile} zip(s) are available in {source_dir}."
            )
            return 0

        source_dir = resolve_source_profile_dir(args.agent, scope, args.profile)
        target_dir = resolve_target_dir(args.agent, scope, args.target)
        source_skill_dirs = list_skill_dirs(source_dir)
        if not source_skill_dirs:
            print(f"install: no built skills found in {source_dir}; nothing to install.")
            return 0

        old_manifest = read_manifest(target_dir)
        old_managed = managed_names(old_manifest)
        source_names = {path.name for path in source_skill_dirs}
        conflicts = find_unmanaged_conflicts(target_dir, source_names, old_managed)
        if conflicts and not args.force:
            joined = ", ".join(conflicts)
            raise InstallError(
                f"target has unmanaged skill directorie(s) with ChangeForge names: {joined}; "
                "rerun with --force or choose a clean target"
            )

        backup_names = source_names | old_managed if args.backup else set()
        backup_path = backup_existing(target_dir, backup_names, "install", args.dry_run)
        new_manifest = make_manifest(
            agent=args.agent,
            scope=scope,
            profile=args.profile,
            target_dir=target_dir,
            source_dir=source_dir,
            backup_path=backup_path,
        )

        if args.dry_run:
            print(f"install: dry run for {args.agent} {scope} {args.profile}")
            print(f"install: source {source_dir}")
            print(f"install: target {target_dir}")
            print(f"install: would install {len(source_skill_dirs)} skill directorie(s)")
            if backup_path is not None:
                print(f"install: would create backup at {backup_path}")
            if args.with_hooks:
                _install_hooks(args, scope)
            if args.with_bootstrap:
                _install_bootstrap(args, scope)
            return 0

        replace_with_source(source_dir, target_dir, source_names | old_managed, dry_run=False)
        write_json(target_dir / ".changeforge-install-manifest.json", new_manifest)
        print(
            f"install: installed {len(source_skill_dirs)} ChangeForge skill directorie(s) "
            f"to {target_dir}"
        )
        if backup_path is not None:
            print(f"install: backup written to {backup_path}")
        if args.with_hooks:
            _install_hooks(args, scope)
        if args.with_bootstrap:
            _install_bootstrap(args, scope)
        return 0
    except InstallError as exc:
        print(f"install: ERROR: {exc}", file=sys.stderr)
        return 1


def _install_hooks(args: argparse.Namespace, scope: str) -> None:
    """Install optional hooks, preserving existing hook config.

    Hooks are never installed unless --with-hooks is passed, and they are only
    supported for Codex, Claude, and Copilot project and user scopes. Project
    hooks install under the project root (--target); user hooks install under the
    agent home directory (~/.codex, ~/.claude, ~/.copilot) regardless of --target.
    Files are written only when neither --dry-run nor --hooks-dry-run is set.
    """
    if not hooks_supported(args.agent, scope):
        raise InstallError(
            "--with-hooks is only supported for codex, claude, and copilot project or user installs"
        )
    if scope == "project" and args.target is None:
        raise InstallError("--with-hooks requires --target (the project root) for project installs")

    plan = plan_hook_install(args.agent, scope, args.target)
    for line in render_hook_plan(plan):
        print(f"install: {line}")

    if args.dry_run or args.hooks_dry_run:
        print("install: hooks: dry run; no hook files written")
        return
    apply_hook_install(plan, dry_run=False)
    print("install: hooks: installed hooks; review and trust before enabling")


def _install_bootstrap(args: argparse.Namespace, scope: str) -> None:
    """Install the advisory route-preflight fragment, preserving user files.

    The bootstrap fragment is plain guidance text, never an executable hook, so
    it is safe for any project install. It is the bootstrap path for runtimes
    without a session-start hook (such as Codex).
    """
    if not bootstrap_supported(args.agent, scope):
        raise InstallError("--with-bootstrap is only supported for project installs")
    if args.target is None:
        raise InstallError("--with-bootstrap requires --target (the project root)")

    plan = plan_bootstrap_install(args.agent, scope, args.target)
    for line in render_bootstrap_plan(plan):
        print(f"install: {line}")

    if args.dry_run or args.bootstrap_dry_run:
        print("install: bootstrap: dry run; no bootstrap fragment written")
        return
    apply_bootstrap_install(plan, dry_run=False)
    print("install: bootstrap: installed advisory route-preflight fragment")


if __name__ == "__main__":
    raise SystemExit(main())
