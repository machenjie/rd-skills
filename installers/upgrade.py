#!/usr/bin/env python3
"""Upgrade installed ChangeForge skills from built dist/ artifacts."""

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
    version_changes,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Upgrade installed ChangeForge skills.")
    parser.add_argument("--agent", choices=AGENTS, required=True)
    parser.add_argument("--scope", choices=SCOPES, required=True)
    parser.add_argument("--target", type=Path, help="Project root, or explicit user/admin skills dir.")
    parser.add_argument("--profile", choices=PROFILES, default="recommended")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow installing a new ChangeForge skill over an unmanaged directory of the same name.",
    )
    args = parser.parse_args()

    try:
        if args.agent == "openai-api":
            print("upgrade: openai-api uses rebuilt zip bundles; run scripts/package.py after build.")
            return 0

        source_dir = resolve_source_profile_dir(args.agent, args.scope, args.profile)
        target_dir = resolve_target_dir(args.agent, args.scope, args.target)
        old_manifest = read_manifest(target_dir)
        if old_manifest is None:
            raise InstallError(f"no ChangeForge manifest found in {target_dir}; run install first")

        old_managed = managed_names(old_manifest)
        source_skill_dirs = list_skill_dirs(source_dir)
        source_names = {path.name for path in source_skill_dirs}
        conflicts = find_unmanaged_conflicts(target_dir, source_names - old_managed, old_managed)
        if conflicts and not args.force:
            joined = ", ".join(conflicts)
            raise InstallError(
                f"target has unmanaged skill directorie(s) with new ChangeForge names: {joined}; "
                "rerun with --force after reviewing the conflict"
            )

        backup_path = backup_existing(target_dir, old_managed, "upgrade", args.dry_run)
        new_manifest = make_manifest(
            agent=args.agent,
            scope=args.scope,
            profile=args.profile,
            target_dir=target_dir,
            source_dir=source_dir,
            backup_path=backup_path,
        )
        changes = version_changes(old_manifest, new_manifest)
        old_profile = old_manifest.get("profile")
        profile_changed = old_profile != args.profile
        source_changed = old_manifest.get("source_version") != new_manifest.get("source_version")

        if args.dry_run:
            print(f"upgrade: dry run for {args.agent} {args.scope} {args.profile}")
            print(f"upgrade: source {source_dir}")
            print(f"upgrade: target {target_dir}")
            print(f"upgrade: would replace {len(old_managed)} managed skill directorie(s)")
            print(f"upgrade: would install {len(source_skill_dirs)} built skill directorie(s)")
            if backup_path is not None:
                print(f"upgrade: would create backup at {backup_path}")
            _print_change_summary(changes, source_changed, profile_changed, old_profile, args.profile)
            return 0

        replace_with_source(source_dir, target_dir, old_managed | source_names, dry_run=False)
        write_json(target_dir / ".changeforge-install-manifest.json", new_manifest)
        print(
            f"upgrade: replaced {len(old_managed)} managed skill directorie(s) "
            f"with {len(source_skill_dirs)} built skill directorie(s)."
        )
        if backup_path is not None:
            print(f"upgrade: backup written to {backup_path}")
        _print_change_summary(changes, source_changed, profile_changed, old_profile, args.profile)
        return 0
    except InstallError as exc:
        print(f"upgrade: ERROR: {exc}", file=sys.stderr)
        return 1


def _print_change_summary(
    changes: dict[str, list[str]],
    source_changed: bool,
    profile_changed: bool,
    old_profile: object,
    new_profile: str,
) -> None:
    if source_changed:
        print("upgrade: source version changed.")
    else:
        print("upgrade: source version unchanged.")
    if profile_changed:
        print(f"upgrade: profile changed from {old_profile!r} to {new_profile!r}.")
    if changes["changed"]:
        print("upgrade: skill version changes: " + ", ".join(changes["changed"]))
    if changes["added"]:
        print("upgrade: added skills: " + ", ".join(changes["added"]))
    if changes["removed"]:
        print("upgrade: removed skills: " + ", ".join(changes["removed"]))
    if not any(changes.values()) and not source_changed and not profile_changed:
        print("upgrade: no version, source, or profile changes detected.")


if __name__ == "__main__":
    raise SystemExit(main())
