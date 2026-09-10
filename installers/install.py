#!/usr/bin/env python3
"""Install built hookless rd-skills Skills and Agent Profiles."""

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
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Install built hookless rd-skills artifacts.")
    parser.add_argument("--agent", choices=AGENTS, required=True)
    parser.add_argument("--scope", choices=SCOPES)
    parser.add_argument("--target", type=Path, help="Project root, or explicit user/admin Skill directory.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--backup", action="store_true")
    args = parser.parse_args()

    try:
        scope = args.scope or ("project" if args.agent == "openai-api" else None)
        if scope is None:
            raise InstallError("--scope is required for runtime installs")
        source = resolve_source_profile_dir(args.agent, scope)
        if args.agent == "openai-api":
            count = validate_openai_bundles(source)
            print(f"install: {count} runtime zip(s) are available in {source}")
            return 0
        targets = resolve_targets(args.agent, scope, args.target)
        source_profiles = resolve_source_profiles(args.agent, scope)
        validate_install_path_separation(source, source_profiles, targets)
        validate_built_source(args.agent, source, source_profiles)
        skill_names = {path.name for path in list_skill_dirs(source)}
        profile_files = {path.name for path in list_profile_files(source_profiles)}
        old = read_manifest(targets.skills)
        if old is None:
            old_skills: set[str] = set()
            old_profiles: set[str] = set()
        else:
            classified = classify_installed_manifest(
                old,
                agent=args.agent,
                scope=scope,
                targets=targets,
            )
            old_skills = set(classified.skill_names)
            old_profiles = set(classified.profile_files)
        old_profiles |= legacy_managed_profile_files(args.agent, scope, args.target)
        validate_managed_artifact_paths(
            targets,
            skill_names | old_skills,
            profile_files | old_profiles,
        )
        conflicts = find_unmanaged_conflicts(targets.skills, skill_names, old_skills)
        if targets.profiles is not None:
            conflicts.extend(find_unmanaged_conflicts(targets.profiles, profile_files, old_profiles))
        if conflicts and not args.force:
            raise InstallError(
                "target contains unmanaged rd-skills-named artifacts: "
                + ", ".join(sorted(set(conflicts)))
            )
        legacy_paths = legacy_residue_paths(args.agent, scope, args.target, targets.skills)
        backup = backup_existing(
            targets,
            skill_names | old_skills,
            profile_files | old_profiles,
            "install",
            args.dry_run,
            legacy_paths,
        ) if args.backup else None
        removed = cleanup_legacy_residue(args.agent, scope, args.target, targets.skills, args.dry_run)
        installed_profiles = [path.name for path in list_profile_files(source_profiles)]
        manifest = make_manifest(
            agent=args.agent,
            scope=scope,
            targets=targets,
            source_dir=source,
            profile_files=installed_profiles,
            backup_path=backup,
        )
        if args.dry_run:
            print(f"install: dry run; would install {len(skill_names)} Skill(s) to {targets.skills}")
            print(f"install: dry run; would install {len(profile_files)} Agent Profile(s) to {targets.profiles}")
            print(f"install: dry run; would remove {len(removed)} legacy artifact(s)")
            return 0
        replace_skills(source, targets.skills, skill_names | old_skills, False)
        replace_profiles(source_profiles, targets.profiles, profile_files | old_profiles, False)
        write_json(targets.skills / ".changeforge-install-manifest.json", manifest)
        print(f"install: installed {len(skill_names)} Skill(s) and {len(profile_files)} Agent Profile(s)")
        if removed:
            print(f"install: removed {len(removed)} legacy artifact(s)")
        if backup is not None:
            print(f"install: backup written to {backup}")
        return 0
    except InstallError as exc:
        print(f"install: ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
