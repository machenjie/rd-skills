#!/usr/bin/env python3
"""Upgrade an rd-skills installation to a built hookless profile."""

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
    cleanup_legacy_residue,
    find_unmanaged_conflicts,
    list_profile_files,
    list_skill_dirs,
    legacy_managed_profile_files,
    legacy_residue_paths,
    make_manifest,
    managed_profile_files,
    managed_skill_names,
    read_manifest,
    replace_profiles,
    replace_skills,
    resolve_source_profile_dir,
    resolve_source_profiles,
    resolve_targets,
    validate_built_source,
    validate_install_path_separation,
    validate_openai_bundles,
    version_changes,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Upgrade installed rd-skills artifacts.")
    parser.add_argument("--agent", choices=AGENTS, required=True)
    parser.add_argument("--scope", choices=SCOPES, required=True)
    parser.add_argument("--target", type=Path)
    parser.add_argument("--profile", choices=PROFILES, default="recommended")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    try:
        if args.agent == "openai-api":
            source = resolve_source_profile_dir(args.agent, args.scope, args.profile)
            validate_openai_bundles(args.profile, source)
            print(f"upgrade: rebuilt zip bundles are available in {source}")
            return 0
        source = resolve_source_profile_dir(args.agent, args.scope, args.profile)
        source_profiles = resolve_source_profiles(args.agent, args.scope)
        targets = resolve_targets(args.agent, args.scope, args.target)
        validate_install_path_separation(source, source_profiles, targets)
        validate_built_source(args.agent, args.profile, source, source_profiles)
        old = read_manifest(targets.skills)
        if old is None:
            raise InstallError(f"no rd-skills manifest found in {targets.skills}; run install first")
        old_skills = managed_skill_names(old)
        old_profiles = managed_profile_files(old)
        old_profiles |= legacy_managed_profile_files(args.agent, args.scope, args.target)
        new_skills = {path.name for path in list_skill_dirs(source)}
        new_profiles = {path.name for path in list_profile_files(source_profiles)}
        conflicts = find_unmanaged_conflicts(targets.skills, new_skills - old_skills, old_skills)
        if targets.profiles is not None:
            conflicts.extend(find_unmanaged_conflicts(targets.profiles, new_profiles - old_profiles, old_profiles))
        if conflicts and not args.force:
            raise InstallError("unmanaged conflicts: " + ", ".join(sorted(set(conflicts))))
        legacy_paths = legacy_residue_paths(args.agent, args.scope, args.target, targets.skills)
        backup = backup_existing(
            targets,
            old_skills,
            old_profiles,
            "upgrade",
            args.dry_run,
            legacy_paths,
        )
        removed = cleanup_legacy_residue(args.agent, args.scope, args.target, targets.skills, args.dry_run)
        manifest = make_manifest(
            agent=args.agent,
            scope=args.scope,
            profile=args.profile,
            targets=targets,
            source_dir=source,
            profile_files=sorted(new_profiles),
            backup_path=backup,
        )
        changes = version_changes(old, manifest)
        if args.dry_run:
            print(f"upgrade: dry run; {len(new_skills)} Skill(s), {len(new_profiles)} Profile(s), {len(removed)} legacy removal(s)")
            _print_changes(changes)
            return 0
        replace_skills(source, targets.skills, old_skills | new_skills, False)
        replace_profiles(source_profiles, targets.profiles, old_profiles | new_profiles, False)
        write_json(targets.skills / ".changeforge-install-manifest.json", manifest)
        print(f"upgrade: installed {len(new_skills)} Skill(s) and {len(new_profiles)} Agent Profile(s)")
        if removed:
            print(f"upgrade: removed {len(removed)} legacy artifact(s)")
        if backup is not None:
            print(f"upgrade: backup written to {backup}")
        _print_changes(changes)
        return 0
    except InstallError as exc:
        print(f"upgrade: ERROR: {exc}", file=sys.stderr)
        return 1


def _print_changes(changes: dict[str, list[str]]) -> None:
    for key in ("added", "removed", "changed"):
        if changes[key]:
            print(f"upgrade: {key}: " + ", ".join(changes[key]))


if __name__ == "__main__":
    raise SystemExit(main())
