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
    managed_names,
    read_manifest,
    remove_managed,
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
    args = parser.parse_args()

    try:
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
        if manifest is None:
            print(f"uninstall: no ChangeForge manifest found in {target_dir}; nothing to remove.")
            return 0

        names = managed_names(manifest)
        existing = sorted(name for name in names if (target_dir / name).exists())

        if args.dry_run:
            print(f"uninstall: dry run for {target_dir}")
            print(f"uninstall: would remove {len(existing)} managed skill directorie(s)")
            for name in existing:
                print(f"uninstall: would remove {target_dir / name}")
            print(f"uninstall: would remove {target_dir / '.changeforge-install-manifest.json'}")
            return 0

        remove_managed(target_dir, names, dry_run=False)
        print(f"uninstall: removed {len(existing)} ChangeForge-managed skill directorie(s).")
        return 0
    except InstallError as exc:
        print(f"uninstall: ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
