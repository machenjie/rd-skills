#!/usr/bin/env python3
"""Uninstall ChangeForge-managed Skills and Agent Profiles."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from changeforge_install import (
    AGENTS,
    SCOPES,
    InstallError,
    cleanup_legacy_residue,
    managed_profile_files,
    managed_skill_names,
    read_manifest,
    remove_installed,
    resolve_targets,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Uninstall ChangeForge-managed artifacts.")
    parser.add_argument("--agent", choices=AGENTS, required=True)
    parser.add_argument("--scope", choices=SCOPES, required=True)
    parser.add_argument("--target", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        if args.agent == "openai-api":
            print("uninstall: openai-api uses build output only")
            return 0
        targets = resolve_targets(args.agent, args.scope, args.target)
        manifest = read_manifest(targets.skills)
        skills = managed_skill_names(manifest)
        profiles = managed_profile_files(manifest)
        legacy = cleanup_legacy_residue(args.agent, args.scope, args.target, targets.skills, args.dry_run)
        if args.dry_run:
            print(f"uninstall: dry run; would remove {len(skills)} Skill(s), {len(profiles)} Profile(s), and {len(legacy)} legacy artifact(s)")
            return 0
        remove_installed(targets, skills, profiles, False)
        print(f"uninstall: removed {len(skills)} Skill(s) and {len(profiles)} Agent Profile(s)")
        if legacy:
            print(f"uninstall: removed {len(legacy)} legacy artifact(s)")
        return 0
    except InstallError as exc:
        print(f"uninstall: ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
