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
    backup_existing,
    find_unmanaged_conflicts,
    list_skill_dirs,
    make_manifest,
    managed_names,
    read_manifest,
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
            return 0

        replace_with_source(source_dir, target_dir, source_names | old_managed, dry_run=False)
        write_json(target_dir / ".changeforge-install-manifest.json", new_manifest)
        print(
            f"install: installed {len(source_skill_dirs)} ChangeForge skill directorie(s) "
            f"to {target_dir}"
        )
        if backup_path is not None:
            print(f"install: backup written to {backup_path}")
        return 0
    except InstallError as exc:
        print(f"install: ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
