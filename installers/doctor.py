#!/usr/bin/env python3
"""Inspect ChangeForge build outputs and installed runtime targets."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from changeforge_install import (
    AGENTS,
    DEFAULT_TARGET_DIRS,
    MANIFEST_NAME,
    PROFILES,
    PROJECT_SUBPATHS,
    SCOPES,
    SOURCE_SKILL_ROOTS,
    InstallError,
    read_manifest,
    resolve_target_dir,
    source_version,
    skill_metadata,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check ChangeForge runtime installation health.")
    parser.add_argument("--agent", choices=AGENTS)
    parser.add_argument("--scope", choices=SCOPES)
    parser.add_argument("--target", type=Path, help="Project root, or explicit user/admin skills dir.")
    parser.add_argument("--profile", choices=PROFILES, help="Expected installed profile.")
    args = parser.parse_args()

    try:
        targets = _selected_targets(args.agent, args.scope, args.target)
    except InstallError as exc:
        print(f"doctor: ERROR: {exc}")
        return 1

    current_version = source_version()
    issues: list[str] = []
    duplicate_index: dict[str, list[str]] = {}

    print("doctor: supported target directories")
    for label, path in targets:
        state = "present" if path.is_dir() else "missing"
        print(f"- {label}: {path} ({state})")
        if not path.is_dir():
            continue

        manifest = read_manifest(path)
        if manifest is not None:
            _inspect_manifest(label, path, manifest, current_version, args.profile, issues)

        _inspect_skill_dirs(label, path, duplicate_index, issues)

    _inspect_duplicates(duplicate_index, issues)

    if issues:
        print("doctor: issues")
        for issue in issues:
            print(f"- {issue}")
        print("doctor: remediation")
        _print_remediation(issues)
        return 1

    print("doctor: no installation issues detected.")
    return 0


def _selected_targets(
    agent: str | None,
    scope: str | None,
    target: Path | None,
) -> list[tuple[str, Path]]:
    if agent or scope:
        if not agent or not scope:
            raise InstallError("--agent and --scope must be supplied together")
        return [(f"{agent}:{scope}", resolve_target_dir(agent, scope, target))]

    project_root = target.expanduser().resolve() if target is not None else Path.cwd().resolve()
    targets: list[tuple[str, Path]] = []
    for agent_name, subpath in PROJECT_SUBPATHS.items():
        targets.append((f"{agent_name}:project", project_root / subpath))
    for key, default_path in DEFAULT_TARGET_DIRS.items():
        agent_name, scope_name = key
        targets.append((f"{agent_name}:{scope_name}", default_path.expanduser()))
    for key, source_root in SOURCE_SKILL_ROOTS.items():
        agent_name, scope_name = key
        if scope_name == "admin":
            targets.append((f"{agent_name}:{scope_name}", Path("/etc/codex/skills")))
    return _dedupe_targets(targets)


def _dedupe_targets(targets: list[tuple[str, Path]]) -> list[tuple[str, Path]]:
    deduped: list[tuple[str, Path]] = []
    seen: set[Path] = set()
    for label, path in targets:
        resolved = path.expanduser()
        key = resolved.resolve() if resolved.exists() else resolved
        if key in seen:
            continue
        seen.add(key)
        deduped.append((label, resolved))
    return deduped


def _inspect_manifest(
    label: str,
    path: Path,
    manifest: dict[str, Any],
    current_version: str,
    expected_profile: str | None,
    issues: list[str],
) -> None:
    installed_version = manifest.get("source_version")
    if installed_version != current_version:
        issues.append(
            f"{label}: installed source version {installed_version!r} differs from current {current_version!r}"
        )

    profile = manifest.get("profile")
    if expected_profile is not None and profile != expected_profile:
        issues.append(
            f"{label}: installed profile {profile!r} does not match expected {expected_profile!r}"
        )

    target_path = manifest.get("target_path")
    if isinstance(target_path, str) and Path(target_path) != path:
        issues.append(f"{label}: manifest target_path points at {target_path}, expected {path}")

    installed_names = _manifest_names(manifest)
    for name in installed_names:
        if not (path / name).exists():
            issues.append(f"{label}: manifest lists missing skill directory {name}")


def _inspect_skill_dirs(
    label: str,
    path: Path,
    duplicate_index: dict[str, list[str]],
    issues: list[str],
) -> None:
    for child in sorted(path.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        skill_file = child / "SKILL.md"
        if not skill_file.is_file():
            issues.append(f"{label}: {child.name} is missing SKILL.md")
            continue
        try:
            metadata = skill_metadata(child)
        except InstallError as exc:
            issues.append(f"{label}: {child.name} has invalid SKILL.md: {exc}")
            continue
        name = metadata.get("name")
        skill_name = str(name) if isinstance(name, str) else child.name
        duplicate_index.setdefault(skill_name, []).append(f"{label}:{child}")


def _manifest_names(manifest: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for key in (
        "installed_skills",
        "installed_professional_skills",
        "installed_domain_extensions",
        "installed_foundation_capabilities",
    ):
        value = manifest.get(key)
        if isinstance(value, list):
            names.extend(str(item) for item in value if isinstance(item, str))
    return sorted(set(names))


def _inspect_duplicates(duplicate_index: dict[str, list[str]], issues: list[str]) -> None:
    for name, locations in sorted(duplicate_index.items()):
        if len(locations) > 1:
            issues.append(f"duplicate skill name {name!r} found in: {', '.join(locations)}")


def _print_remediation(issues: list[str]) -> None:
    printed: set[str] = set()
    for issue in issues:
        if "missing SKILL.md" in issue:
            message = "Remove or repair the malformed skill directory before using this target."
        elif "differs from current" in issue:
            message = "Run installers/upgrade.py with the intended --agent, --scope, --target, and --profile."
        elif "profile" in issue and "does not match" in issue:
            message = "Reinstall or upgrade with the expected --profile."
        elif "duplicate skill name" in issue:
            message = "Keep one active copy in the intended scope and uninstall the duplicate ChangeForge-managed copy."
        elif "manifest lists missing" in issue:
            message = "Run installers/upgrade.py to refresh the manifest and managed directories."
        else:
            message = "Review the reported path and rerun doctor after remediation."
        if message not in printed:
            print(f"- {message}")
            printed.add(message)


if __name__ == "__main__":
    raise SystemExit(main())
