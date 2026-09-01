#!/usr/bin/env python3
"""Inspect a hookless rd-skills installation."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tomllib
from pathlib import Path

from changeforge_install import (
    AGENT_PROFILE_NAMES,
    AGENTS,
    HOST_ENFORCEMENT_SOURCE,
    RUNTIME_SKILL_COUNT,
    SCOPES,
    InstallError,
    classify_installed_manifest,
    host_enforcement_for_agent,
    legacy_residue_paths,
    product_next_step_lines,
    read_manifest,
    resolve_source_profile_dir,
    resolve_targets,
    source_version,
    validated_built_core_model,
    validated_built_profile_sha256,
    validate_managed_artifact_paths,
    validate_openai_bundles,
)


def _print_enforcement(agent: str, enforcement: dict) -> None:
    print(
        "doctor: declared-default profile enforcement "
        f"host={agent} delivery={enforcement['profile_delivery']} "
        f"diff_input_mode={enforcement['diff_input_mode']} "
        f"validation_mode={enforcement['validation_mode']} "
        f"utility_no_edit={enforcement['utility_no_edit']}"
    )
    for role, capabilities in enforcement["roles"].items():
        print(
            f"- {role}: tool_allowlist={capabilities['tool_allowlist']}; "
            "workspace_write_protection="
            f"{capabilities['workspace_write_protection']}; "
            "read_only_command_semantics="
            f"{capabilities['read_only_command_semantics']}"
        )
        for limitation in capabilities.get("limitations", []):
            print(f"  limitation: {limitation}")


def _print_success(
    agent: str,
    next_step: tuple[str, ...] | None = None,
) -> None:
    if agent == "openai-api":
        print("✓ rd-skills package found")
        print("✓ expected package contents found")
        print("✓ package healthy")
    else:
        print("✓ rd-skills installed")
        print("✓ expected configuration found")
        print("✓ installation healthy")
    print()
    if agent == "openai-api":
        print(
            "Doctor verifies package artifacts. It does not prove a real host "
            "loaded rd-skills."
        )
    else:
        print(
            "Doctor verifies installation artifacts. It does not prove your AI "
            "coding tool loaded rd-skills."
        )
    print()
    print("Next:")
    for line in next_step or product_next_step_lines(agent):
        print(line)


def _profile_projection_issues(
    agent: str,
    profile_root: Path,
    manifest: dict,
    enforcement: dict,
    expected_build_digests: dict[str, str],
) -> list[str]:
    issues: list[str] = []
    suffix = {"codex": ".toml", "claude": ".md", "copilot": ".agent.md"}[agent]
    payloads: dict[str, bytes] = {}
    for role in AGENT_PROFILE_NAMES:
        path = profile_root / f"{role}{suffix}"
        if path.is_symlink():
            issues.append(f"installed Agent Profile must not be a symlink: {path.name}")
            continue
        if path.is_file():
            payloads[role] = path.read_bytes()
    actual_digests = {
        role: hashlib.sha256(raw).hexdigest() for role, raw in payloads.items()
    }
    declared_digests = manifest.get("installed_agent_profile_sha256")
    if actual_digests != declared_digests:
        issues.append("installed Agent Profile file digests do not match the install manifest")
    if declared_digests != expected_build_digests:
        issues.append("install manifest Agent Profile digests do not match the validated build")
    if actual_digests != expected_build_digests:
        issues.append("installed Agent Profile files do not match the validated build")
    expected_sandbox = {
        "main-control-agent": "read-only",
        "analysis-agent": "read-only",
        "task-agent": "workspace-write",
        "review-agent": "read-only",
    }
    static_runtime_capability_markers = (
        "Current capability facts:",
        "Current external-read mode:",
        "external_source_read=",
    )
    legacy_mode_markers = (
        "Current host modes:",
        "diff_input_mode=",
        "validation_mode=",
        "utility_no_edit=",
    )
    for role in AGENT_PROFILE_NAMES:
        path = profile_root / f"{role}{suffix}"
        raw = payloads.get(role)
        if raw is None:
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            issues.append(f"installed Agent Profile is not UTF-8: {path.name}")
            continue
        expected_tools = enforcement["roles"][role]["rendered_tools"]
        if "Declared tool boundary:" not in text:
            issues.append(f"{path.name}: missing declared tool boundary")
        if any(marker in text for marker in static_runtime_capability_markers):
            issues.append(
                f"{path.name}: static runtime capability projection is forbidden"
            )
        if any(marker in text for marker in legacy_mode_markers):
            issues.append(f"{path.name}: legacy host mode projection is forbidden")
        if agent == "codex":
            try:
                payload = tomllib.loads(text)
            except tomllib.TOMLDecodeError:
                issues.append(f"invalid Codex Agent Profile TOML: {path.name}")
                continue
            if payload.get("sandbox_mode") != expected_sandbox[role]:
                issues.append(f"{path.name}: sandbox_mode is not the declared default")
        elif agent == "claude":
            match = re.search(r"^tools:\s*(.*)$", text, re.MULTILINE)
            actual_tools = [item.strip() for item in match.group(1).split(",")] if match else []
            if actual_tools != expected_tools:
                issues.append(f"{path.name}: Claude tools differ from the declared default")
        else:
            match = re.search(r"^tools:\s*(\[[^\n]*\])$", text, re.MULTILINE)
            try:
                actual_tools = json.loads(match.group(1)) if match else []
            except json.JSONDecodeError:
                actual_tools = []
            if actual_tools != expected_tools:
                issues.append(f"{path.name}: Copilot tools differ from the declared default")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Check rd-skills installation health.")
    parser.add_argument("--agent", choices=AGENTS, required=True)
    parser.add_argument("--scope", choices=SCOPES, required=True)
    parser.add_argument("--target", type=Path)
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show inventory, source binding, and host enforcement details.",
    )
    args = parser.parse_args()
    try:
        expected_enforcement = host_enforcement_for_agent(args.agent)
        next_step = product_next_step_lines(args.agent)
        if args.agent == "openai-api":
            source = resolve_source_profile_dir(args.agent, args.scope)
            validate_openai_bundles(source)
            if args.verbose:
                print(f"doctor: source binding package_root={source}")
                _print_enforcement(args.agent, expected_enforcement)
            _print_success(args.agent, next_step)
            return 0
        targets = resolve_targets(args.agent, args.scope, args.target)
        manifest = read_manifest(targets.skills)
        issues: list[str] = []
        if manifest is None:
            issues.append(f"missing install manifest in {targets.skills}")
        else:
            classified = classify_installed_manifest(
                manifest,
                agent=args.agent,
                scope=args.scope,
                targets=targets,
            )
            installed_skills = set(classified.skill_names)
            installed_files = set(classified.profile_files)
            validate_managed_artifact_paths(
                targets,
                installed_skills,
                installed_files,
            )
            if classified.migration_required:
                print("doctor: issues")
                print(
                    f"- migration required: installed legacy {classified.profile} "
                    "profile must be upgraded to the single runtime"
                )
                return 1
            if manifest.get("source_version") != source_version():
                issues.append("installed source version differs from current source")
            if manifest.get("installed_agent_profile_enforcement") != expected_enforcement:
                issues.append("installed Agent Profile enforcement matrix is stale or invalid")
            enforcement_source = manifest.get("agent_profile_enforcement_source")
            expected_digest = hashlib.sha256(HOST_ENFORCEMENT_SOURCE.read_bytes()).hexdigest()
            if not isinstance(enforcement_source, dict) or enforcement_source.get("sha256") != expected_digest:
                issues.append("installed Agent Profile enforcement source digest is stale or invalid")
            expected_core_model = validated_built_core_model(
                args.agent, args.scope
            )
            if manifest.get("core_model") != expected_core_model:
                issues.append(
                    "installed core model digest does not match the validated build"
                )
            if len(installed_skills) != RUNTIME_SKILL_COUNT:
                issues.append(
                    f"installed manifest must contain {RUNTIME_SKILL_COUNT} Skills, "
                    f"found {len(installed_skills)}"
                )
            for name in sorted(installed_skills):
                if not (targets.skills / name / "SKILL.md").is_file():
                    issues.append(f"missing installed Skill {name}")
            if targets.profiles is not None:
                expected_build_digests = validated_built_profile_sha256(
                    args.agent, args.scope
                )
                extension = {"codex": ".toml", "claude": ".md", "copilot": ".agent.md"}[args.agent]
                expected_files = {f"{name}{extension}" for name in AGENT_PROFILE_NAMES}
                if installed_files != expected_files:
                    issues.append("installed Agent Profile files are not the exact four-role set")
                for name in sorted(installed_files):
                    if not (targets.profiles / name).is_file():
                        issues.append(f"missing installed Agent Profile file {name}")
                installed_names = set(manifest.get("installed_agent_profiles") or [])
                if installed_names != set(AGENT_PROFILE_NAMES):
                    issues.append("installed Agent Profile set is not the four-role model")
                issues.extend(
                    _profile_projection_issues(
                        args.agent,
                        targets.profiles,
                        manifest,
                        expected_enforcement,
                        expected_build_digests,
                    )
                )
        for path in legacy_residue_paths(args.agent, args.scope, args.target, targets.skills):
            issues.append(f"legacy pre-hookless residue remains: {path}")
        if issues:
            print("doctor: issues")
            for issue in issues:
                print(f"- {issue}")
            return 1
        if args.verbose:
            print(
                "doctor: installed inventory "
                f"Skills={len(installed_skills)} Agent Profiles={len(installed_files)}"
            )
            core_model = manifest.get("core_model") if manifest is not None else None
            core_digest = (
                core_model.get("sha256", "missing")
                if isinstance(core_model, dict)
                else "missing"
            )
            print(
                "doctor: source binding "
                f"source_version={manifest.get('source_version') if manifest else 'missing'} "
                f"core_model_sha256={core_digest}"
            )
            _print_enforcement(args.agent, expected_enforcement)
            if targets.profiles is not None:
                print(
                    "doctor: observed-installed Profile files match declared "
                    "digests and critical fields"
                )
        _print_success(args.agent, next_step)
        return 0
    except InstallError as exc:
        print(f"doctor: ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
