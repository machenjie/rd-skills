#!/usr/bin/env python3
"""Upgrade an rd-skills installation to the built hookless runtime."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from changeforge_install import (
    AGENTS,
    SCOPES,
    InstallError,
    backup_existing,
    cleanup_legacy_residue,
    classify_installed_manifest,
    find_unmanaged_conflicts,
    list_profile_files,
    list_skill_dirs,
    legacy_managed_profile_files,
    legacy_residue_paths,
    make_manifest,
    read_manifest,
    replace_profiles,
    replace_skills,
    resolve_source_profile_dir,
    resolve_source_profiles,
    resolve_targets,
    validate_built_source,
    validate_install_path_separation,
    validate_managed_artifact_paths,
    validate_openai_bundles,
    version_changes,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Upgrade installed rd-skills artifacts.")
    parser.add_argument("--agent", choices=AGENTS, required=True)
    parser.add_argument("--scope", choices=SCOPES, required=True)
    parser.add_argument("--target", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    try:
        if args.agent == "openai-api":
            source = resolve_source_profile_dir(args.agent, args.scope)
            validate_openai_bundles(source)
            print(f"upgrade: rebuilt zip bundles are available in {source}")
            return 0
        source = resolve_source_profile_dir(args.agent, args.scope)
        source_profiles = resolve_source_profiles(args.agent, args.scope)
        targets = resolve_targets(args.agent, args.scope, args.target)
        validate_install_path_separation(source, source_profiles, targets)
        validate_built_source(args.agent, source, source_profiles)
        old = read_manifest(targets.skills)
        if old is None:
            raise InstallError(f"no rd-skills manifest found in {targets.skills}; run install first")
        classified = classify_installed_manifest(
            old,
            agent=args.agent,
            scope=args.scope,
            targets=targets,
        )
        old_skills = set(classified.skill_names)
        old_profiles = set(classified.profile_files)
        old_profiles |= legacy_managed_profile_files(args.agent, args.scope, args.target)
        new_skills = {path.name for path in list_skill_dirs(source)}
        new_profiles = {path.name for path in list_profile_files(source_profiles)}
        validate_managed_artifact_paths(
            targets,
            old_skills | new_skills,
            old_profiles | new_profiles,
        )
        conflicts = find_unmanaged_conflicts(targets.skills, new_skills - old_skills, old_skills)
        if targets.profiles is not None:
            conflicts.extend(find_unmanaged_conflicts(targets.profiles, new_profiles - old_profiles, old_profiles))
        if conflicts and not args.force:
            raise InstallError("unmanaged conflicts: " + ", ".join(sorted(set(conflicts))))
        legacy_paths = legacy_residue_paths(args.agent, args.scope, args.target, targets.skills)
        manifest = make_manifest(
            agent=args.agent,
            scope=args.scope,
            targets=targets,
            source_dir=source,
            profile_files=sorted(new_profiles),
            backup_path=None,
        )
        backup = backup_existing(
            targets,
            old_skills,
            old_profiles,
            "upgrade",
            args.dry_run,
            legacy_paths,
        )
        if not args.dry_run and (backup is None or not backup.is_dir()):
            raise InstallError("upgrade requires a complete backup before live mutation")
        manifest["backup_path"] = str(backup) if backup is not None else None
        changes = version_changes(old, manifest)
        if args.dry_run:
            print(f"upgrade: dry run; {len(new_skills)} Skill(s), {len(new_profiles)} Profile(s), {len(legacy_paths)} legacy removal(s)")
            _print_changes(changes)
            return 0
        removed = cleanup_legacy_residue(
            args.agent,
            args.scope,
            args.target,
            targets.skills,
            False,
        )
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
