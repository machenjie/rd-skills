#!/usr/bin/env python3
"""Inspect a hookless ChangeForge installation."""

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
    COMPILED_LAYER3_FORMAT,
    EXPECTED_PROFILE_COUNTS,
    HOST_ENFORCEMENT_SOURCE,
    PROFILES,
    SCOPES,
    InstallError,
    host_enforcement_for_agent,
    legacy_residue_paths,
    managed_profile_files,
    managed_skill_names,
    read_manifest,
    resolve_source_profile_dir,
    resolve_targets,
    source_version,
    validated_built_core_model,
    validated_built_profile_sha256,
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
        expected_modes = (
            "Current host modes: "
            f"diff_input_mode={enforcement['diff_input_mode']}; "
            f"validation_mode={enforcement['validation_mode']}; "
            f"utility_no_edit={enforcement['utility_no_edit']}."
        )
        if "Declared tool boundary:" not in text:
            issues.append(f"{path.name}: missing declared tool boundary")
        if role == "main-control-agent":
            if expected_modes not in text:
                issues.append(f"{path.name}: missing exact current host modes")
        elif any(
            marker in text
            for marker in (
                "Current host modes:",
                "diff_input_mode=",
                "validation_mode=",
                "utility_no_edit=",
            )
        ):
            issues.append(f"{path.name}: worker Profile must not receive host modes")
        if agent == "codex":
            try:
                payload = tomllib.loads(text)
            except tomllib.TOMLDecodeError:
                issues.append(f"invalid Codex Agent Profile TOML: {path.name}")
                continue
            if payload.get("sandbox_mode") != expected_sandbox[role]:
                issues.append(f"{path.name}: sandbox_mode is not the declared default")
            instructions = str(payload.get("developer_instructions") or "")
            if role == "main-control-agent" and expected_modes not in instructions:
                issues.append(f"{path.name}: parsed instructions omit current host modes")
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
    parser = argparse.ArgumentParser(description="Check ChangeForge installation health.")
    parser.add_argument("--agent", choices=AGENTS, required=True)
    parser.add_argument("--scope", choices=SCOPES, required=True)
    parser.add_argument("--target", type=Path)
    parser.add_argument("--profile", choices=PROFILES)
    args = parser.parse_args()
    try:
        expected_enforcement = host_enforcement_for_agent(args.agent)
        if args.agent == "openai-api":
            profile = args.profile or "recommended"
            source = resolve_source_profile_dir(args.agent, args.scope, profile)
            validate_openai_bundles(profile, source)
            _print_enforcement(args.agent, expected_enforcement)
            print(f"doctor: {profile} OpenAI API output is healthy")
            return 0
        targets = resolve_targets(args.agent, args.scope, args.target)
        manifest = read_manifest(targets.skills)
        issues: list[str] = []
        if manifest is None:
            issues.append(f"missing install manifest in {targets.skills}")
        else:
            if manifest.get("architecture") != "hookless-control-plane-v1":
                issues.append("installed manifest is not hookless-control-plane-v1")
            if manifest.get("compiled_layer3_format") != COMPILED_LAYER3_FORMAT:
                issues.append(
                    "installed manifest compiled_layer3_format is not "
                    f"{COMPILED_LAYER3_FORMAT}"
                )
            if manifest.get("source_version") != source_version():
                issues.append("installed source version differs from current source")
            if args.profile and manifest.get("profile") != args.profile:
                issues.append(f"installed profile {manifest.get('profile')!r} does not match {args.profile!r}")
            if manifest.get("installed_agent_profile_enforcement") != expected_enforcement:
                issues.append("installed Agent Profile enforcement matrix is stale or invalid")
            enforcement_source = manifest.get("agent_profile_enforcement_source")
            expected_digest = hashlib.sha256(HOST_ENFORCEMENT_SOURCE.read_bytes()).hexdigest()
            if not isinstance(enforcement_source, dict) or enforcement_source.get("sha256") != expected_digest:
                issues.append("installed Agent Profile enforcement source digest is stale or invalid")
            profile = str(manifest.get("profile") or "")
            expected_core_model = validated_built_core_model(
                args.agent, args.scope, profile
            )
            if manifest.get("core_model") != expected_core_model:
                issues.append(
                    "installed core model digest does not match the validated build"
                )
            installed_skills = managed_skill_names(manifest)
            expected_count = EXPECTED_PROFILE_COUNTS.get(profile)
            if expected_count is None:
                issues.append(f"installed manifest has unsupported profile {profile!r}")
            elif len(installed_skills) != expected_count:
                issues.append(f"installed manifest must contain {expected_count} Skills, found {len(installed_skills)}")
            for name in sorted(installed_skills):
                if not (targets.skills / name / "SKILL.md").is_file():
                    issues.append(f"missing installed Skill {name}")
            if targets.profiles is not None:
                expected_build_digests = validated_built_profile_sha256(
                    args.agent, args.scope, profile
                )
                extension = {"codex": ".toml", "claude": ".md", "copilot": ".agent.md"}[args.agent]
                expected_files = {f"{name}{extension}" for name in AGENT_PROFILE_NAMES}
                installed_files = managed_profile_files(manifest)
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
            issues.append(f"legacy ChangeForge residue remains: {path}")
        if issues:
            print("doctor: issues")
            for issue in issues:
                print(f"- {issue}")
            return 1
        _print_enforcement(args.agent, expected_enforcement)
        if targets.profiles is not None:
            print("doctor: observed-installed Profile files match declared digests and critical fields")
        print("doctor: hookless installation is healthy")
        return 0
    except InstallError as exc:
        print(f"doctor: ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
