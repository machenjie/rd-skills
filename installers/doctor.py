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


COMMON_HOOK_SUPPORT_FILES = ("changeforge_professional_contract.md",)
COPILOT_HOOK_SUPPORT_FILES = (
    "changeforge_copilot_skill_summary.md",
    "changeforge_copilot_professional_contract.md",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check ChangeForge runtime installation health.")
    parser.add_argument("--agent", choices=AGENTS)
    parser.add_argument("--scope", choices=SCOPES)
    parser.add_argument("--target", type=Path, help="Project root, or explicit user/admin skills dir.")
    parser.add_argument("--profile", choices=PROFILES, help="Expected installed profile.")
    parser.add_argument(
        "--telemetry-report",
        type=Path,
        help="Optional review report to summarize (markdown, json, or yaml).",
    )
    parser.add_argument(
        "--telemetry-root",
        type=Path,
        help="Optional telemetry root; doctor finds the latest review report under it.",
    )
    parser.add_argument(
        "--repo-hash",
        help="Optional repo hash to scope --telemetry-root report discovery.",
    )
    parser.add_argument(
        "--check-hooks",
        action="store_true",
        help="Inspect optional project hook files, manifest, and config references.",
    )
    parser.add_argument(
        "--check-bootstrap",
        action="store_true",
        help="Inspect the optional advisory route-preflight bootstrap fragment.",
    )
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

    if args.telemetry_report is not None or args.telemetry_root is not None:
        _report_telemetry(args.telemetry_report, args.telemetry_root, args.repo_hash)

    if args.check_hooks:
        _check_project_hooks(args.target, issues)

    if args.check_bootstrap:
        _check_project_bootstrap(args.target, issues)

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


def _report_telemetry(
    report_arg: Path | None,
    telemetry_root: Path | None,
    repo_hash: str | None,
) -> None:
    """Show an informational telemetry summary. This never changes doctor's exit.

    Telemetry is optional. Doctor reads a generated review report and prints its
    counts; it does not fix telemetry, never reads prompts, and never mutates
    skills. When no report is available it points to review-agent-telemetry.py.
    """
    # Lazy import: changeforge_install puts scripts/ on sys.path when it loads.
    from telemetry_utils import find_latest_report, read_report_summary, resolve_telemetry_root

    print("doctor: telemetry summary")
    report_path = report_arg
    if report_path is None and telemetry_root is not None:
        report_path = find_latest_report(resolve_telemetry_root(telemetry_root), repo_hash)

    if report_path is None:
        print("- no review report found; run scripts/review-agent-telemetry.py to generate one")
        return

    summary = read_report_summary(report_path)
    if summary is None:
        print(f"- could not read telemetry summary from {report_path}")
        print("- run scripts/review-agent-telemetry.py to regenerate the report")
        return

    print(f"- report: {report_path}")
    adoption = summary.get("route_manifest_adoption")
    closures = summary.get("code_change_closures")
    if adoption is not None and closures is not None:
        present = summary.get("route_manifest_closures", 0)
        print(
            f"- route manifest adoption: {present}/{closures} "
            f"({float(adoption) * 100:.0f}%)"
        )
    for label, key in (
        ("sessions", "sessions"),
        ("missed router", "missed_router"),
        ("missed reference", "missed_reference"),
        ("missed gate", "missed_gate"),
        ("validation evidence missing", "validation_evidence_missing"),
        ("unverified completion claims", "unverified_completion_claims"),
        ("incomplete required references", "incomplete_required_references"),
        ("residual risk missing", "residual_risk_missing"),
        ("pressure candidate suggestions", "pressure_candidate_suggestions"),
        ("high severity suggestions", "high_severity_suggestions"),
    ):
        print(f"- {label}: {summary.get(key, 'n/a')}")
    print("- telemetry is advisory; review suggestions before any human promotion")


def _check_project_hooks(target: Path | None, issues: list[str]) -> None:
    """Inspect optional project hook files and config references.

    Hooks are never required. This reports presence of hook scripts, the hook
    manifest, and whether the project hook config references the generated hook
    scripts. It only adds an issue when hooks look partially installed.
    """
    project_root = (target.expanduser().resolve() if target is not None else Path.cwd().resolve())
    print(f"doctor: project hooks ({project_root})")
    # Each spec: agent, config dir, scripts dir, manifest/bootstrap dir, config file.
    # Codex/Claude keep scripts and aux files at the agent config root; VS Code
    # Copilot nests them under .github/hooks/changeforge/ with the config json at
    # .github/hooks/changeforge-hooks.json.
    codex_root = project_root / ".codex"
    claude_root = project_root / ".claude"
    copilot_hooks = project_root / ".github" / "hooks"
    copilot_scripts = copilot_hooks / "changeforge"
    hook_specs = (
        ("codex", codex_root, codex_root / "hooks", codex_root, codex_root / "hooks.json"),
        (
            "claude",
            claude_root,
            claude_root / "hooks",
            claude_root,
            claude_root / "settings.changeforge-hooks.fragment.json",
        ),
        (
            "copilot",
            copilot_hooks,
            copilot_scripts,
            copilot_scripts,
            copilot_hooks / "changeforge-hooks.json",
        ),
    )
    any_present = False
    for agent, _config_root, scripts_dir, aux_dir, config_path in hook_specs:
        manifest_path = aux_dir / ".changeforge-hook-manifest.json"
        config_name = config_path.name
        present_signals = [scripts_dir.is_dir(), manifest_path.is_file(), config_path.is_file()]
        if not any(present_signals):
            continue
        any_present = True
        scripts = sorted(scripts_dir.glob("changeforge_*.py")) if scripts_dir.is_dir() else []
        print(f"- {agent}: hook scripts: {len(scripts)} found in {scripts_dir}")
        if not scripts:
            issues.append(f"{agent}: hook config or manifest present but no changeforge_* hook scripts")
        if manifest_path.is_file():
            print(f"- {agent}: manifest present")
        else:
            issues.append(f"{agent}: missing {manifest_path.name}")
        expected_support = list(COMMON_HOOK_SUPPORT_FILES)
        if agent == "copilot":
            expected_support.extend(COPILOT_HOOK_SUPPORT_FILES)
        for support_file in expected_support:
            support_path = scripts_dir / support_file
            if support_path.is_file():
                print(f"- {agent}: support file present: {support_file}")
            else:
                issues.append(f"{agent}: missing {support_file}")
        if not (scripts_dir / "changeforge_professional_injector.py").is_file():
            issues.append(f"{agent}: missing professional injection hook")
        if not (scripts_dir / "changeforge_pre_edit_structure_gate.py").is_file():
            issues.append(f"{agent}: missing pre-edit structure gate")
        if not (scripts_dir / "changeforge_hook_policy.py").is_file():
            issues.append(f"{agent}: missing hook policy support")
        if not (scripts_dir / "changeforge_state_reducer.py").is_file():
            issues.append(f"{agent}: missing state reducer support")
        if not (scripts_dir / "changeforge_stop_closure_gate.py").is_file():
            issues.append(f"{agent}: missing stage-aware Stop closure hook")
        if config_path.is_file():
            references = _config_references_hooks(config_path)
            state = "references generated hooks" if references else "does NOT reference changeforge hooks"
            print(f"- {agent}: {config_name} {state}")
            if not references:
                issues.append(f"{agent}: {config_name} does not reference changeforge hook scripts")
            config_text = config_path.read_text(encoding="utf-8", errors="replace")
            if agent in {"codex", "claude"} and "changeforge_pre_edit_structure_gate" not in config_text:
                issues.append(f"{agent}: {config_name} does not reference pre-edit structure gate")
            if agent == "copilot" and (
                '"PreToolUse"' in config_text or "changeforge_pre_edit_structure_gate" in config_text
            ):
                issues.append(f"{agent}: {config_name} wires unsupported PreToolUse advisory")
        else:
            print(f"- {agent}: {config_name} not found (manual merge may be pending)")
        bootstrap_path = aux_dir / "changeforge-route-preflight.md"
        if bootstrap_path.is_file():
            wired = (scripts_dir / "changeforge_session_bootstrap.py").is_file()
            detail = "SessionStart hook script present" if wired else "SessionStart hook script missing"
            print(f"- {agent}: route-preflight bootstrap fragment present ({detail})")
        else:
            print(f"- {agent}: route-preflight bootstrap fragment not found (optional)")
        professional_path = scripts_dir / "changeforge_professional_contract.md"
        if professional_path.is_file():
            print(f"- {agent}: professional contract support present")
    if not any_present:
        print("- no project hooks installed (this is fine; hooks are optional)")


def _check_project_bootstrap(target: Path | None, issues: list[str]) -> None:
    """Inspect the optional standalone advisory route-preflight fragment.

    The advisory fragment installed by ``install.py --with-bootstrap`` lives at
    ``.changeforge/changeforge-route-preflight.md``. It is never required; this
    only reports presence and never adds an issue for a missing optional file.
    """
    project_root = (target.expanduser().resolve() if target is not None else Path.cwd().resolve())
    fragment = project_root / ".changeforge" / "changeforge-route-preflight.md"
    professional = project_root / ".changeforge" / "changeforge-professional-contract.md"
    print(f"doctor: route-preflight bootstrap ({project_root})")
    if fragment.is_file():
        print(f"- advisory fragment present: {fragment}")
        if "change-forge-router" not in _safe_read(fragment):
            issues.append(
                "bootstrap fragment present but does not reference change-forge-router"
            )
    else:
        print("- no advisory bootstrap fragment installed (this is fine; bootstrap is optional)")
    if professional.is_file():
        print(f"- professional bootstrap fragment present: {professional}")
        if "owner skill" not in _safe_read(professional):
            issues.append(
                "professional bootstrap fragment present but does not reference owner skill"
            )
    else:
        print("- no professional bootstrap fragment installed (this is fine; bootstrap is optional)")


def _safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _config_references_hooks(config_path: Path) -> bool:
    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError:
        return False
    return "changeforge_" in text


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
