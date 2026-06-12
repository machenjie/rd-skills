#!/usr/bin/env python3
"""Validate built runtime installation outputs."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

from validation_utils import (
    EXPECTED_DOMAIN_EXTENSION_COUNT,
    EXPECTED_FOUNDATION_CAPABILITY_COUNT,
    EXPECTED_PROFESSIONAL_SKILL_COUNT,
    EXPECTED_PROFILE_TOP_LEVEL_COUNTS,
    ValidationProblem,
    fail_many,
    load_yaml_file,
    parse_frontmatter,
    relpath,
    validate_expected_count,
    validate_no_personal_references,
)


ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "dist"
REGISTRY_DIR = ROOT / "src" / "registry"
PROFILE_NAMES = ("recommended", "full", "dev")
NON_DEV_PROFILES = {"recommended", "full"}
BUILD_MANIFEST_NAME = ".changeforge-build-manifest.json"
MAX_ZIP_FILES = 500
MAX_ZIP_BYTES = 5 * 1024 * 1024
MAX_ZIP_FILE_BYTES = 2 * 1024 * 1024

REQUIRED_DIST_DIRS = (
    "universal/skills",
    "codex/project/.agents/skills",
    "codex/user/.agents/skills",
    "codex/admin/skills",
    "claude/project/.claude/skills",
    "claude/user/.claude/skills",
    "copilot/project/.github/skills",
    "copilot/user/.copilot/skills",
    "openai-api/zips",
)

REQUIRED_HOOK_DIST_FILES = (
    "codex/project/.codex/hooks.json",
    "codex/project/.codex/.changeforge-hook-manifest.json",
    "codex/project/.codex/changeforge-route-preflight.md",
    "codex/project/.codex/hooks/changeforge_common.py",
    "codex/project/.codex/hooks/changeforge_session_bootstrap.py",
    "codex/project/.codex/hooks/changeforge_user_prompt_route_reminder.py",
    "codex/project/.codex/hooks/changeforge_pre_tool_risk_preview.py",
    "codex/project/.codex/hooks/changeforge_post_edit_structure_gate.py",
    "codex/project/.codex/hooks/changeforge_risk_surface_gate.py",
    "codex/project/.codex/hooks/changeforge_subagent_stop_reminder.py",
    "codex/project/.codex/hooks/changeforge_stop_closure_gate.py",
    "codex/user/.codex/hooks.json",
    "codex/user/.codex/.changeforge-hook-manifest.json",
    "codex/user/.codex/changeforge-route-preflight.md",
    "codex/user/.codex/hooks/changeforge_common.py",
    "codex/user/.codex/hooks/changeforge_session_bootstrap.py",
    "codex/user/.codex/hooks/changeforge_user_prompt_route_reminder.py",
    "codex/user/.codex/hooks/changeforge_pre_tool_risk_preview.py",
    "codex/user/.codex/hooks/changeforge_post_edit_structure_gate.py",
    "codex/user/.codex/hooks/changeforge_risk_surface_gate.py",
    "codex/user/.codex/hooks/changeforge_subagent_stop_reminder.py",
    "codex/user/.codex/hooks/changeforge_stop_closure_gate.py",
    "claude/project/.claude/settings.changeforge-hooks.fragment.json",
    "claude/project/.claude/.changeforge-hook-manifest.json",
    "claude/project/.claude/changeforge-route-preflight.md",
    "claude/project/.claude/hooks/changeforge_common.py",
    "claude/project/.claude/hooks/changeforge_session_bootstrap.py",
    "claude/project/.claude/hooks/changeforge_user_prompt_route_reminder.py",
    "claude/project/.claude/hooks/changeforge_pre_tool_risk_preview.py",
    "claude/project/.claude/hooks/changeforge_post_edit_structure_gate.py",
    "claude/project/.claude/hooks/changeforge_risk_surface_gate.py",
    "claude/project/.claude/hooks/changeforge_subagent_stop_reminder.py",
    "claude/project/.claude/hooks/changeforge_stop_closure_gate.py",
    "claude/user/.claude/settings.changeforge-hooks.fragment.json",
    "claude/user/.claude/.changeforge-hook-manifest.json",
    "claude/user/.claude/changeforge-route-preflight.md",
    "claude/user/.claude/hooks/changeforge_common.py",
    "claude/user/.claude/hooks/changeforge_session_bootstrap.py",
    "claude/user/.claude/hooks/changeforge_user_prompt_route_reminder.py",
    "claude/user/.claude/hooks/changeforge_pre_tool_risk_preview.py",
    "claude/user/.claude/hooks/changeforge_post_edit_structure_gate.py",
    "claude/user/.claude/hooks/changeforge_risk_surface_gate.py",
    "claude/user/.claude/hooks/changeforge_subagent_stop_reminder.py",
    "claude/user/.claude/hooks/changeforge_stop_closure_gate.py",
    "copilot/project/.github/hooks/changeforge-hooks.json",
    "copilot/project/.github/hooks/changeforge/.changeforge-hook-manifest.json",
    "copilot/project/.github/hooks/changeforge/changeforge-route-preflight.md",
    "copilot/project/.github/hooks/changeforge/changeforge_common.py",
    "copilot/project/.github/hooks/changeforge/changeforge_session_bootstrap.py",
    "copilot/project/.github/hooks/changeforge/changeforge_user_prompt_route_reminder.py",
    "copilot/project/.github/hooks/changeforge/changeforge_pre_tool_risk_preview.py",
    "copilot/project/.github/hooks/changeforge/changeforge_post_edit_structure_gate.py",
    "copilot/project/.github/hooks/changeforge/changeforge_risk_surface_gate.py",
    "copilot/project/.github/hooks/changeforge/changeforge_subagent_stop_reminder.py",
    "copilot/project/.github/hooks/changeforge/changeforge_stop_closure_gate.py",
    "copilot/user/.copilot/hooks/changeforge-hooks.json",
    "copilot/user/.copilot/hooks/changeforge/.changeforge-hook-manifest.json",
    "copilot/user/.copilot/hooks/changeforge/changeforge-route-preflight.md",
    "copilot/user/.copilot/hooks/changeforge/changeforge_common.py",
    "copilot/user/.copilot/hooks/changeforge/changeforge_session_bootstrap.py",
    "copilot/user/.copilot/hooks/changeforge/changeforge_user_prompt_route_reminder.py",
    "copilot/user/.copilot/hooks/changeforge/changeforge_pre_tool_risk_preview.py",
    "copilot/user/.copilot/hooks/changeforge/changeforge_post_edit_structure_gate.py",
    "copilot/user/.copilot/hooks/changeforge/changeforge_risk_surface_gate.py",
    "copilot/user/.copilot/hooks/changeforge/changeforge_subagent_stop_reminder.py",
    "copilot/user/.copilot/hooks/changeforge/changeforge_stop_closure_gate.py",
    "universal/bootstrap/changeforge-route-preflight.md",
)
BASE_HOOK_NAMES = {
    "changeforge_post_edit_structure_gate",
    "changeforge_risk_surface_gate",
    "changeforge_stop_closure_gate",
}
# Each runtime wires the route-preflight bootstrap as a SessionStart hook and
# ships the install-time bootstrap fragment. Codex, Claude, and Copilot also
# ship the per-prompt route reminder, pre-edit risk preview, and subagent
# closure reminder scripts for their richer hook events.
RICH_HOOK_NAMES = frozenset(
    BASE_HOOK_NAMES
    | {
        "changeforge_session_bootstrap",
        "changeforge_user_prompt_route_reminder",
        "changeforge_pre_tool_risk_preview",
        "changeforge_subagent_stop_reminder",
    }
)
EXPECTED_HOOK_NAMES_BY_AGENT = {
    "codex": RICH_HOOK_NAMES,
    "claude": RICH_HOOK_NAMES,
    "copilot": RICH_HOOK_NAMES,
}
BOOTSTRAP_FRAGMENT_NAME = "changeforge-route-preflight.md"

PROFILE_SKILL_ROOTS = (
    DIST_DIR / "universal" / "skills",
    DIST_DIR / "codex" / "project" / ".agents" / "skills",
    DIST_DIR / "codex" / "user" / ".agents" / "skills",
    DIST_DIR / "codex" / "admin" / "skills",
    DIST_DIR / "claude" / "project" / ".claude" / "skills",
    DIST_DIR / "claude" / "user" / ".claude" / "skills",
    DIST_DIR / "copilot" / "project" / ".github" / "skills",
    DIST_DIR / "copilot" / "user" / ".copilot" / "skills",
)

ROUTER_INDEX_FILES = (
    "routing-rules.md",
    "skill-registry.md",
    "capability-index.md",
    "domain-extension-index.md",
)


def main() -> int:
    errors: list[str] = []

    registries = _load_registry_sets(errors)
    professional_names = registries["professional_names"]
    capability_names = registries["capability_names"]
    domain_extension_names = registries["domain_extension_names"]
    capability_files_by_skill = registries["capability_files_by_skill"]

    missing = [name for name in REQUIRED_DIST_DIRS if not (DIST_DIR / name).exists()]
    if missing:
        errors.append(f"missing dist output directorie(s): {', '.join(missing)}")

    _validate_dist_guardrails(errors)
    _validate_profile_roots(
        professional_names,
        capability_names,
        domain_extension_names,
        capability_files_by_skill,
        errors,
    )
    _validate_hook_runtime(errors)
    _validate_zips(
        professional_names,
        capability_names,
        domain_extension_names,
        errors,
    )

    if errors:
        return fail_many("validate-installation", errors)

    built_count = sum(
        1
        for root in PROFILE_SKILL_ROOTS
        for profile in PROFILE_NAMES
        for child in (root / profile).iterdir()
        if child.is_dir() and not child.name.startswith(".")
    )
    zip_count = len(sorted((DIST_DIR / "openai-api" / "zips").rglob("*.zip")))
    print(
        "validate-installation: validated "
        f"{len(PROFILE_SKILL_ROOTS)} runtime root(s), {built_count} built skill directory(s), "
        f"{len(REQUIRED_HOOK_DIST_FILES)} hook runtime file(s), and {zip_count} zip(s)."
    )
    return 0


def _load_registry_sets(errors: list[str]) -> dict[str, Any]:
    try:
        skills = _registry_entries("skills.yaml", "skills")
        capabilities = _registry_entries("capabilities.yaml", "capabilities")
        domain_extensions = _registry_entries("domain-extensions.yaml", "domain_extensions")
    except ValidationProblem as exc:
        errors.append(str(exc))
        return {
            "professional_names": set(),
            "capability_names": set(),
            "domain_extension_names": set(),
            "capability_files_by_skill": {},
        }

    professional_names = _entry_names(skills)
    capability_names = _entry_names(capabilities)
    domain_extension_names = _entry_names(domain_extensions)
    capability_files_by_skill: dict[str, set[str]] = {}

    validate_expected_count(
        errors,
        "professional skill registry entrie(s)",
        len(skills),
        EXPECTED_PROFESSIONAL_SKILL_COUNT,
        "src/registry/skills.yaml",
    )
    validate_expected_count(
        errors,
        "foundation capability registry entrie(s)",
        len(capabilities),
        EXPECTED_FOUNDATION_CAPABILITY_COUNT,
        "src/registry/capabilities.yaml",
    )
    validate_expected_count(
        errors,
        "domain extension registry entrie(s)",
        len(domain_extensions),
        EXPECTED_DOMAIN_EXTENSION_COUNT,
        "src/registry/domain-extensions.yaml",
    )
    profile_counts = {
        "recommended": len(skills),
        "full": len(skills) + len(domain_extensions),
        "dev": len(skills) + len(capabilities) + len(domain_extensions),
    }
    for profile, expected_count in EXPECTED_PROFILE_TOP_LEVEL_COUNTS.items():
        validate_expected_count(
            errors,
            f"{profile} profile top-level skill(s)",
            profile_counts[profile],
            expected_count,
            "registry profile counts",
        )

    for entry in capabilities:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        capability_id = entry.get("id")
        used_by = entry.get("used_by", [])
        if not isinstance(name, str) or not isinstance(capability_id, str):
            continue
        if not isinstance(used_by, list):
            continue
        file_name = f"{capability_id}-{name}.md"
        for skill_name in used_by:
            if isinstance(skill_name, str):
                capability_files_by_skill.setdefault(skill_name, set()).add(file_name)

    return {
        "professional_names": professional_names,
        "capability_names": capability_names,
        "domain_extension_names": domain_extension_names,
        "capability_files_by_skill": capability_files_by_skill,
    }


def _registry_entries(file_name: str, key: str) -> list[Any]:
    path = REGISTRY_DIR / file_name
    data = load_yaml_file(path)
    if not isinstance(data, dict):
        raise ValidationProblem(f"{relpath(ROOT, path)} must be a mapping")
    entries = data.get(key, [])
    if not isinstance(entries, list):
        raise ValidationProblem(f"{relpath(ROOT, path)} field '{key}' must be a list")
    return entries


def _entry_names(entries: list[Any]) -> set[str]:
    names: set[str] = set()
    for entry in entries:
        if isinstance(entry, dict) and isinstance(entry.get("name"), str):
            names.add(entry["name"])
    return names


def _validate_dist_guardrails(errors: list[str]) -> None:
    if not DIST_DIR.exists():
        errors.append("missing dist")
        return

    for path in DIST_DIR.rglob("*"):
        relative = relpath(ROOT, path)
        parts = [part.casefold() for part in path.relative_to(DIST_DIR).parts]
        name = path.name.casefold()

        if "toolbox" in parts or name == "toolbox-mapping.md":
            errors.append(f"toolbox content installed in runtime output: {relative}")
        if "registry" in parts:
            errors.append(f"raw registry directory installed in runtime output: {relative}")
        if "src" in parts:
            errors.append(f"raw src content installed in runtime output: {relative}")

        validate_no_personal_references(relative, relative, errors)
        if path.is_file() and path.suffix != ".zip":
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            validate_no_personal_references(text, relative, errors)
            if "src/registry" in text or "src\\registry" in text:
                errors.append(f"{relative}: raw src/registry reference installed")
            if "toolbox-mapping.md" in text:
                errors.append(f"{relative}: toolbox mapping reference installed")


def _validate_profile_roots(
    professional_names: set[str],
    capability_names: set[str],
    domain_extension_names: set[str],
    capability_files_by_skill: dict[str, set[str]],
    errors: list[str],
) -> None:
    for root in PROFILE_SKILL_ROOTS:
        if not root.exists():
            continue
        for profile in PROFILE_NAMES:
            profile_root = root / profile
            if not profile_root.is_dir():
                errors.append(f"{relpath(ROOT, profile_root)}: missing built profile")
                continue

            manifest_path = profile_root / BUILD_MANIFEST_NAME
            _validate_build_manifest(manifest_path, profile, errors)

            expected = _expected_profile_names(
                profile,
                professional_names,
                capability_names,
                domain_extension_names,
            )
            actual = {
                child.name
                for child in profile_root.iterdir()
                if child.is_dir() and not child.name.startswith(".")
            }
            validate_expected_count(
                errors,
                f"{profile} profile top-level skill directorie(s)",
                len(actual),
                EXPECTED_PROFILE_TOP_LEVEL_COUNTS[profile],
                relpath(ROOT, profile_root),
            )
            missing = sorted(expected - actual)
            extra = sorted(actual - expected)
            if missing:
                errors.append(f"{relpath(ROOT, profile_root)}: missing skill(s): {', '.join(missing)}")
            if extra:
                errors.append(f"{relpath(ROOT, profile_root)}: unexpected skill(s): {', '.join(extra)}")

            for skill_dir in sorted(profile_root.iterdir()):
                if not skill_dir.is_dir() or skill_dir.name.startswith("."):
                    continue
                _validate_runtime_skill_dir(
                    skill_dir,
                    profile,
                    professional_names,
                    capability_names,
                    capability_files_by_skill,
                    errors,
                )


def _validate_hook_runtime(errors: list[str]) -> None:
    for relative in REQUIRED_HOOK_DIST_FILES:
        path = DIST_DIR / relative
        if not path.is_file():
            errors.append(f"missing hook runtime file: dist/{relative}")
    _validate_hook_manifest(
        DIST_DIR / "codex/project/.codex/.changeforge-hook-manifest.json",
        agent="codex",
        scope="project",
        errors=errors,
    )
    _validate_hook_manifest(
        DIST_DIR / "codex/user/.codex/.changeforge-hook-manifest.json",
        agent="codex",
        scope="user",
        errors=errors,
    )
    _validate_hook_manifest(
        DIST_DIR / "claude/project/.claude/.changeforge-hook-manifest.json",
        agent="claude",
        scope="project",
        errors=errors,
    )
    _validate_hook_manifest(
        DIST_DIR / "claude/user/.claude/.changeforge-hook-manifest.json",
        agent="claude",
        scope="user",
        errors=errors,
    )
    _validate_hook_manifest(
        DIST_DIR / "copilot/project/.github/hooks/changeforge/.changeforge-hook-manifest.json",
        agent="copilot",
        scope="project",
        errors=errors,
    )
    _validate_hook_manifest(
        DIST_DIR / "copilot/user/.copilot/hooks/changeforge/.changeforge-hook-manifest.json",
        agent="copilot",
        scope="user",
        errors=errors,
    )


def _validate_hook_manifest(path: Path, *, agent: str, scope: str, errors: list[str]) -> None:
    if not path.is_file():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{relpath(ROOT, path)}: invalid JSON: {exc}")
        return
    if not isinstance(data, dict):
        errors.append(f"{relpath(ROOT, path)}: hook manifest must be a JSON object")
        return
    if data.get("kind") != "changeforge-hook-runtime":
        errors.append(f"{relpath(ROOT, path)}: kind must be changeforge-hook-runtime")
    if data.get("agent") != agent:
        errors.append(f"{relpath(ROOT, path)}: agent must be {agent}")
    if data.get("scope") != scope:
        errors.append(f"{relpath(ROOT, path)}: scope must be {scope}")
    hooks = data.get("hooks")
    expected_hooks = EXPECTED_HOOK_NAMES_BY_AGENT[agent]
    if (
        not isinstance(hooks, list)
        or not all(isinstance(hook, str) for hook in hooks)
        or set(hooks) != set(expected_hooks)
    ):
        errors.append(
            f"{relpath(ROOT, path)}: hooks must be {', '.join(sorted(expected_hooks))}"
        )
    if data.get("bootstrap_fragment") != BOOTSTRAP_FRAGMENT_NAME:
        errors.append(
            f"{relpath(ROOT, path)}: bootstrap_fragment must be {BOOTSTRAP_FRAGMENT_NAME}"
        )
    if data.get("session_bootstrap_hook") is not True:
        errors.append(
            f"{relpath(ROOT, path)}: session_bootstrap_hook must be True"
        )


def _expected_profile_names(
    profile: str,
    professional_names: set[str],
    capability_names: set[str],
    domain_extension_names: set[str],
) -> set[str]:
    if profile == "recommended":
        return set(professional_names)
    if profile == "full":
        return set(professional_names | domain_extension_names)
    if profile == "dev":
        return set(professional_names | domain_extension_names | capability_names)
    return set()


def _validate_build_manifest(path: Path, profile: str, errors: list[str]) -> None:
    if not path.is_file():
        errors.append(f"{relpath(ROOT, path)}: missing build manifest")
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{relpath(ROOT, path)}: invalid JSON: {exc}")
        return
    if not isinstance(data, dict):
        errors.append(f"{relpath(ROOT, path)}: build manifest must be a JSON object")
        return
    if data.get("profile") != profile:
        errors.append(f"{relpath(ROOT, path)}: profile must be {profile}")
    if profile in NON_DEV_PROFILES and data.get("foundation_mode") != "compiled-references":
        errors.append(f"{relpath(ROOT, path)}: non-dev foundation_mode must be compiled-references")
    if profile == "dev" and data.get("foundation_mode") != "top-level-and-compiled-references":
        errors.append(
            f"{relpath(ROOT, path)}: dev foundation_mode must be top-level-and-compiled-references"
        )
    _validate_manifest_list_count(
        data,
        path,
        "top_level_skills",
        EXPECTED_PROFILE_TOP_LEVEL_COUNTS[profile],
        errors,
    )
    _validate_manifest_list_count(
        data,
        path,
        "professional_skills",
        EXPECTED_PROFESSIONAL_SKILL_COUNT,
        errors,
    )
    _validate_manifest_list_count(
        data,
        path,
        "foundation_capabilities",
        EXPECTED_FOUNDATION_CAPABILITY_COUNT,
        errors,
    )
    _validate_manifest_list_count(
        data,
        path,
        "compiled_foundation_capabilities",
        EXPECTED_FOUNDATION_CAPABILITY_COUNT,
        errors,
    )
    _validate_manifest_list_count(
        data,
        path,
        "domain_extensions",
        EXPECTED_DOMAIN_EXTENSION_COUNT,
        errors,
    )


def _validate_manifest_list_count(
    data: dict[str, Any],
    path: Path,
    key: str,
    expected: int,
    errors: list[str],
) -> None:
    value = data.get(key)
    if not isinstance(value, list):
        errors.append(f"{relpath(ROOT, path)}: field '{key}' must be a list")
        return
    validate_expected_count(
        errors,
        f"manifest {key} item(s)",
        len(value),
        expected,
        relpath(ROOT, path),
    )


def _validate_runtime_skill_dir(
    skill_dir: Path,
    profile: str,
    professional_names: set[str],
    capability_names: set[str],
    capability_files_by_skill: dict[str, set[str]],
    errors: list[str],
) -> None:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        errors.append(f"{relpath(ROOT, skill_dir)}: installable skill missing root SKILL.md")
        return

    nested_skill_files = sorted(path for path in skill_dir.rglob("SKILL.md") if path != skill_md)
    if nested_skill_files:
        errors.append(f"{relpath(ROOT, skill_dir)}: nested SKILL.md files are not allowed")

    if profile in NON_DEV_PROFILES and skill_dir.name in capability_names:
        errors.append(
            f"{relpath(ROOT, skill_dir)}: {profile} profile may not install foundation "
            "capabilities as top-level skills"
        )

    if skill_dir.name in professional_names:
        _validate_professional_references(skill_dir, capability_files_by_skill, errors)
        if skill_dir.name == "change-forge-router":
            references_dir = skill_dir / "references"
            for file_name in ROUTER_INDEX_FILES:
                if not (references_dir / file_name).is_file():
                    errors.append(f"{relpath(ROOT, references_dir / file_name)}: missing router index")


def _validate_professional_references(
    skill_dir: Path,
    capability_files_by_skill: dict[str, set[str]],
    errors: list[str],
) -> None:
    references_dir = skill_dir / "references" / "capabilities"
    if not references_dir.is_dir():
        errors.append(f"{relpath(ROOT, references_dir)}: missing compiled capability references")
        return
    if not (references_dir / "index.md").is_file():
        errors.append(f"{relpath(ROOT, references_dir / 'index.md')}: missing capability index")

    expected_files = capability_files_by_skill.get(skill_dir.name, set())
    actual_files = {
        path.name
        for path in references_dir.glob("*.md")
        if path.name != "index.md"
    }
    missing = sorted(expected_files - actual_files)
    extra = sorted(actual_files - expected_files)
    if missing:
        errors.append(
            f"{relpath(ROOT, references_dir)}: missing compiled capability file(s): "
            f"{', '.join(missing)}"
        )
    if extra:
        errors.append(
            f"{relpath(ROOT, references_dir)}: unexpected compiled capability file(s): "
            f"{', '.join(extra)}"
        )


def _validate_zips(
    professional_names: set[str],
    capability_names: set[str],
    domain_extension_names: set[str],
    errors: list[str],
) -> None:
    zip_root = DIST_DIR / "openai-api" / "zips"
    if not zip_root.is_dir():
        errors.append("missing dist/openai-api/zips")
        return

    legacy_zip_files = sorted(zip_root.glob("*.zip"))
    if legacy_zip_files:
        joined = ", ".join(relpath(ROOT, path) for path in legacy_zip_files)
        errors.append(
            "dist/openai-api/zips: unprofiled legacy zip bundle(s) found; "
            f"expected zips under profile directories only: {joined}"
        )

    for profile in PROFILE_NAMES:
        profile_zip_root = zip_root / profile
        if not profile_zip_root.is_dir():
            errors.append(f"{relpath(ROOT, profile_zip_root)}: missing OpenAI API zip profile")
            continue

        expected = _expected_profile_names(
            profile,
            professional_names,
            capability_names,
            domain_extension_names,
        )
        zip_files = sorted(profile_zip_root.glob("*.zip"))
        actual = {path.stem for path in zip_files}
        validate_expected_count(
            errors,
            f"{profile} OpenAI API zip(s)",
            len(actual),
            EXPECTED_PROFILE_TOP_LEVEL_COUNTS[profile],
            relpath(ROOT, profile_zip_root),
        )
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        if missing:
            errors.append(
                f"{relpath(ROOT, profile_zip_root)}: missing zip(s): {', '.join(missing)}"
            )
        if extra:
            errors.append(
                f"{relpath(ROOT, profile_zip_root)}: unexpected zip(s): {', '.join(extra)}"
            )

        for zip_path in zip_files:
            _validate_openai_zip(zip_path, errors)


def _validate_openai_zip(path: Path, errors: list[str]) -> None:
    relative_zip = relpath(ROOT, path)
    try:
        with zipfile.ZipFile(path) as archive:
            names = [name for name in archive.namelist() if name and not name.endswith("/")]
            if not names:
                errors.append(f"{relative_zip}: zip is empty")
                return

            if len(names) > MAX_ZIP_FILES:
                errors.append(f"{relative_zip}: zip has {len(names)} files; max is {MAX_ZIP_FILES}")

            total_size = sum(archive.getinfo(name).file_size for name in names)
            if total_size > MAX_ZIP_BYTES:
                errors.append(f"{relative_zip}: zip size is {total_size} bytes; max is {MAX_ZIP_BYTES}")

            top_levels = {name.split("/", 1)[0] for name in names}
            if len(top_levels) != 1:
                errors.append(f"{relative_zip}: zip must contain exactly one top-level skill folder")
                return

            top_level = next(iter(top_levels))
            if any("/" not in name for name in names):
                errors.append(f"{relative_zip}: zip contains top-level files")

            skill_md_entries = [name for name in names if name.endswith("/SKILL.md")]
            if skill_md_entries != [f"{top_level}/SKILL.md"]:
                errors.append(f"{relative_zip}: zip must contain exactly one root SKILL.md")

            for name in names:
                info = archive.getinfo(name)
                if info.file_size > MAX_ZIP_FILE_BYTES:
                    errors.append(
                        f"{relative_zip}:{name}: file is {info.file_size} bytes; "
                        f"max is {MAX_ZIP_FILE_BYTES}"
                    )
                _validate_zip_entry_guardrails(relative_zip, name, errors)
                if name.endswith((".md", ".json", ".txt", ".yaml", ".yml")):
                    try:
                        text = archive.read(name).decode("utf-8")
                    except UnicodeDecodeError:
                        continue
                    validate_no_personal_references(text, f"{relative_zip}:{name}", errors)
                    if "src/registry" in text or "src\\registry" in text:
                        errors.append(f"{relative_zip}:{name}: raw src/registry reference installed")
                    if "toolbox-mapping.md" in text:
                        errors.append(f"{relative_zip}:{name}: toolbox mapping reference installed")
    except zipfile.BadZipFile:
        errors.append(f"{relative_zip}: invalid zip file")


def _validate_zip_entry_guardrails(zip_path: str, name: str, errors: list[str]) -> None:
    validate_no_personal_references(name, f"{zip_path}:{name}", errors)
    lowered_parts = [part.casefold() for part in name.split("/")]
    file_name = lowered_parts[-1] if lowered_parts else ""
    if "toolbox" in lowered_parts or file_name == "toolbox-mapping.md":
        errors.append(f"{zip_path}:{name}: toolbox content installed")
    if "registry" in lowered_parts:
        errors.append(f"{zip_path}:{name}: raw registry directory installed")
    if "src" in lowered_parts:
        errors.append(f"{zip_path}:{name}: raw src content installed")


if __name__ == "__main__":
    raise SystemExit(main())
