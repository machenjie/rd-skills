"""Shared helpers for ChangeForge runtime installers."""

from __future__ import annotations

import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from validation_utils import ValidationProblem, parse_frontmatter  # noqa: E402


MANIFEST_NAME = ".changeforge-install-manifest.json"
BUILD_MANIFEST_NAME = ".changeforge-build-manifest.json"
BACKUP_DIR_NAME = ".changeforge-backups"
PROFILES = ("recommended", "full", "dev")
AGENTS = ("codex", "claude", "copilot", "cline", "openai-api")
SCOPES = ("project", "user", "admin")

SOURCE_SKILL_ROOTS = {
    ("codex", "project"): ROOT / "dist" / "codex" / "project" / ".agents" / "skills",
    ("codex", "user"): ROOT / "dist" / "codex" / "user" / ".agents" / "skills",
    ("codex", "admin"): ROOT / "dist" / "codex" / "admin" / "skills",
    ("claude", "project"): ROOT / "dist" / "claude" / "project" / ".claude" / "skills",
    ("claude", "user"): ROOT / "dist" / "claude" / "user" / ".claude" / "skills",
    ("copilot", "project"): ROOT / "dist" / "copilot" / "project" / ".github" / "skills",
    ("copilot", "user"): ROOT / "dist" / "copilot" / "user" / ".copilot" / "skills",
    ("cline", "project"): ROOT / "dist" / "cline" / "project" / ".cline" / "skills",
    ("cline", "user"): ROOT / "dist" / "cline" / "user" / ".cline" / "skills",
}

PROJECT_SUBPATHS = {
    "codex": Path(".agents") / "skills",
    "claude": Path(".claude") / "skills",
    "copilot": Path(".github") / "skills",
    "cline": Path(".cline") / "skills",
}

DEFAULT_TARGET_DIRS = {
    ("codex", "user"): Path.home() / ".agents" / "skills",
    ("codex", "admin"): Path("/etc/codex/skills"),
    ("claude", "user"): Path.home() / ".claude" / "skills",
    ("copilot", "user"): Path.home() / ".copilot" / "skills",
    ("cline", "user"): Path.home() / ".cline" / "skills",
}

FOUNDATION_MODES = {
    "recommended": "compiled-references",
    "full": "compiled-references",
    "dev": "top-level-and-compiled-references",
}

# Project and user hook runtime. Supported Codex, Claude, and Copilot scopes are
# installed by default unless the installer receives --without-hooks. Material
# SDD choices and pre-edit structure are blocking by default. Stop closure is
# advisory by default unless a maintainer explicitly overrides policy;
# lower-risk advisory context remains warning-oriented. Existing hook
# configuration is always preserved.
HOOK_SOURCE_ROOTS = {
    ("codex", "project"): ROOT / "dist" / "codex" / "project" / ".codex",
    ("codex", "user"): ROOT / "dist" / "codex" / "user" / ".codex",
    ("claude", "project"): ROOT / "dist" / "claude" / "project" / ".claude",
    ("claude", "user"): ROOT / "dist" / "claude" / "user" / ".claude",
    ("copilot", "project"): ROOT / "dist" / "copilot" / "project" / ".github",
    ("copilot", "user"): ROOT / "dist" / "copilot" / "user" / ".copilot",
}
HOOK_AGENTS = ("codex", "claude", "copilot")
HOOK_SCOPES = ("project", "user")
# Project hooks install under the project root; user hooks install under the
# agent home directory (Codex ~/.codex, Claude ~/.claude, Copilot ~/.copilot).
HOOK_PROJECT_SUBPATH = {
    "codex": Path(".codex"),
    "claude": Path(".claude"),
    "copilot": Path(".github"),
}
HOOK_USER_HOME_SUBDIR = {
    "codex": Path(".codex"),
    "claude": Path(".claude"),
    "copilot": Path(".copilot"),
}
# Per-agent hook layout relative to the agent config root. Codex and Claude keep
# scripts in hooks/ with the manifest and bootstrap fragment at the root. VS Code
# Copilot loads every *.json in the hook folder, so the managed config lives at
# hooks/changeforge-hooks.json while scripts, manifest, and bootstrap live in a
# hooks/changeforge/ subfolder VS Code does not scan for config.
HOOK_SCRIPTS_SUBDIR = {
    "codex": Path("hooks"),
    "claude": Path("hooks"),
    "copilot": Path("hooks") / "changeforge",
}
HOOK_AUX_SUBDIR = {
    "codex": Path("."),
    "claude": Path("."),
    "copilot": Path("hooks") / "changeforge",
}
HOOK_MANIFEST_NAME = ".changeforge-hook-manifest.json"
COMMON_HOOK_SUPPORT_FILES = ("changeforge_professional_contract.md",)
COPILOT_HOOK_SUPPORT_FILES = (
    "changeforge_copilot_skill_summary.md",
    "changeforge_copilot_professional_contract.md",
)
COMMON_HOOK_SUPPORT_PACKAGES = (
    "validation_broker",
    "runtime_governance",
    "repository_intelligence",
    "project_memory",
)
HOOK_SUPPORT_PACKAGE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Advisory route-preflight bootstrap. The fragment is plain guidance text, not an
# executable hook, so it can be installed for any project scope and never needs
# to be trusted. It is also the bootstrap path for users who prefer not to trust
# executable hooks.
BOOTSTRAP_FRAGMENT_NAME = "changeforge-route-preflight.md"
PROFESSIONAL_BOOTSTRAP_FRAGMENT_NAME = "changeforge-professional-contract.md"
UNIVERSAL_BOOTSTRAP_SOURCE = (
    ROOT / "dist" / "universal" / "bootstrap" / BOOTSTRAP_FRAGMENT_NAME
)
UNIVERSAL_PROFESSIONAL_BOOTSTRAP_SOURCE = (
    ROOT / "dist" / "universal" / "bootstrap" / PROFESSIONAL_BOOTSTRAP_FRAGMENT_NAME
)
BOOTSTRAP_PROJECT_SUBPATH = Path(".changeforge")
BOOTSTRAP_AGENTS = ("codex", "claude", "copilot", "cline")


class InstallError(Exception):
    """Raised for unsafe or unsupported install operations."""


@dataclass
class HookPlan:
    """Describes how project hooks would be installed without writing anything."""

    agent: str
    source_root: Path
    target_root: Path
    script_actions: list[tuple[Path, Path, str]] = field(default_factory=list)
    support_actions: list[tuple[Path, Path, str]] = field(default_factory=list)
    support_package_actions: list[tuple[Path, Path, str]] = field(default_factory=list)
    manifest_action: tuple[Path, Path, str] | None = None
    bootstrap_action: tuple[Path, Path, str] | None = None
    config_target: Path | None = None
    config_payload: dict[str, Any] | None = None
    config_summary: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def source_version() -> str:
    pyproject = ROOT / "pyproject.toml"
    if not pyproject.is_file():
        return "unknown"
    for line in pyproject.read_text(encoding="utf-8").splitlines():
        match = re.match(r'^version\s*=\s*"([^"]+)"', line.strip())
        if match:
            return match.group(1)
    return "unknown"


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def supported_scopes(agent: str) -> tuple[str, ...]:
    if agent == "openai-api":
        return ("project", "user", "admin")
    return tuple(scope for candidate, scope in SOURCE_SKILL_ROOTS if candidate == agent)


def validate_agent_scope(agent: str, scope: str) -> None:
    if agent not in AGENTS:
        raise InstallError(f"unsupported agent: {agent}")
    if scope not in SCOPES:
        raise InstallError(f"unsupported scope: {scope}")
    if agent != "openai-api" and (agent, scope) not in SOURCE_SKILL_ROOTS:
        scopes = ", ".join(supported_scopes(agent))
        raise InstallError(f"{agent} supports scope(s): {scopes}")


def resolve_target_dir(agent: str, scope: str, target: Path | None) -> Path:
    validate_agent_scope(agent, scope)
    if agent == "openai-api":
        return ROOT / "dist" / "openai-api" / "zips"

    if scope == "project":
        if target is None:
            raise InstallError("--target is required for project installs")
        return target.expanduser().resolve() / PROJECT_SUBPATHS[agent]

    if target is not None:
        return target.expanduser().resolve()

    default = DEFAULT_TARGET_DIRS.get((agent, scope))
    if default is None:
        raise InstallError(f"{agent} {scope} installs are not supported")
    return default.expanduser()


def resolve_source_profile_dir(agent: str, scope: str, profile: str) -> Path:
    validate_agent_scope(agent, scope)
    if profile not in PROFILES:
        raise InstallError(f"unsupported profile: {profile}")
    if agent == "openai-api":
        source_root = ROOT / "dist" / "openai-api" / "zips" / profile
        if not source_root.is_dir():
            raise InstallError(
                f"missing OpenAI API zip profile {source_root.relative_to(ROOT)}; "
                f"run python3 scripts/build.py --profile {profile}"
            )
        return source_root
    source_root = SOURCE_SKILL_ROOTS[(agent, scope)] / profile
    if not source_root.is_dir():
        raise InstallError(
            f"missing built profile {source_root.relative_to(ROOT)}; "
            f"run python3 scripts/build.py --profile {profile}"
        )
    return source_root


def list_skill_dirs(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return [
        path
        for path in sorted(root.iterdir())
        if path.is_dir() and not path.name.startswith(".")
    ]


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise InstallError(f"{path} contains invalid JSON: {exc}") from exc
    if not isinstance(loaded, dict):
        raise InstallError(f"{path} must contain a JSON object")
    return loaded


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_manifest(target_dir: Path) -> dict[str, Any] | None:
    return load_json(target_dir / MANIFEST_NAME)


def read_build_manifest(source_dir: Path) -> dict[str, Any]:
    manifest = load_json(source_dir / BUILD_MANIFEST_NAME)
    if manifest is None:
        raise InstallError(f"{source_dir.relative_to(ROOT)} is missing {BUILD_MANIFEST_NAME}")
    return manifest


def skill_metadata(skill_dir: Path) -> dict[str, Any]:
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        raise InstallError(f"{skill_dir} is missing SKILL.md")
    try:
        metadata, _raw_frontmatter, _body = parse_frontmatter(skill_file)
    except ValidationProblem as exc:
        raise InstallError(str(exc)) from exc
    return metadata


def classify_source_skills(skill_dirs: list[Path]) -> dict[str, list[str]]:
    names = {
        "professional_skills": [],
        "foundation_capabilities": [],
        "domain_extensions": [],
        "all": [],
    }
    for skill_dir in skill_dirs:
        metadata = skill_metadata(skill_dir)
        name = str(metadata.get("name") or skill_dir.name)
        kind = metadata.get("changeforge_kind")
        names["all"].append(name)
        if kind == "domain-extension":
            names["domain_extensions"].append(name)
        elif kind == "foundation-capability":
            names["foundation_capabilities"].append(name)
        else:
            names["professional_skills"].append(name)

    for key, values in names.items():
        names[key] = sorted(values)
    return names


def managed_names(manifest: dict[str, Any] | None) -> set[str]:
    if not manifest:
        return set()
    names: set[str] = set()
    for key in (
        "installed_skills",
        "installed_professional_skills",
        "installed_domain_extensions",
        "installed_foundation_capabilities",
    ):
        value = manifest.get(key, [])
        if isinstance(value, list):
            names.update(str(item) for item in value if isinstance(item, str))
    return names


def make_manifest(
    *,
    agent: str,
    scope: str,
    profile: str,
    target_dir: Path,
    source_dir: Path,
    backup_path: Path | None,
) -> dict[str, Any]:
    skill_dirs = list_skill_dirs(source_dir)
    classified = classify_source_skills(skill_dirs)
    versions: dict[str, str] = {}
    for skill_dir in skill_dirs:
        metadata = skill_metadata(skill_dir)
        name = str(metadata.get("name") or skill_dir.name)
        version = metadata.get("changeforge_version")
        versions[name] = str(version) if version is not None else "unknown"

    build_manifest = read_build_manifest(source_dir)
    return {
        "install_time": utc_iso(),
        "source_version": str(build_manifest.get("source_version", source_version())),
        "agent": agent,
        "scope": scope,
        "profile": profile,
        "target_path": str(target_dir),
        "installed_professional_skills": classified["professional_skills"],
        "installed_foundation_capabilities": classified["foundation_capabilities"],
        "installed_domain_extensions": classified["domain_extensions"],
        "installed_skills": classified["all"],
        "foundation_mode": FOUNDATION_MODES[profile],
        "backup_path": str(backup_path) if backup_path is not None else None,
        "skill_versions": versions,
    }


def backup_existing(
    target_dir: Path,
    names: set[str],
    action: str,
    dry_run: bool,
) -> Path | None:
    existing = [target_dir / name for name in sorted(names) if (target_dir / name).exists()]
    manifest_path = target_dir / MANIFEST_NAME
    if manifest_path.exists():
        existing.append(manifest_path)
    if not existing:
        return None

    backup_path = target_dir / BACKUP_DIR_NAME / f"{action}-{utc_stamp()}"
    if dry_run:
        return backup_path

    backup_path.mkdir(parents=True, exist_ok=False)
    for path in existing:
        destination = backup_path / path.name
        if path.is_dir():
            shutil.copytree(path, destination)
        else:
            shutil.copy2(path, destination)
    return backup_path


def find_unmanaged_conflicts(
    target_dir: Path,
    source_names: set[str],
    managed: set[str],
) -> list[str]:
    return sorted(
        name
        for name in source_names
        if (target_dir / name).exists() and name not in managed
    )


def replace_with_source(
    source_dir: Path,
    target_dir: Path,
    remove_names: set[str],
    dry_run: bool,
) -> None:
    source_skill_dirs = list_skill_dirs(source_dir)
    if dry_run:
        return

    target_dir.mkdir(parents=True, exist_ok=True)
    for name in sorted(remove_names):
        destination = target_dir / name
        if destination.exists():
            shutil.rmtree(destination)

    for skill_dir in source_skill_dirs:
        shutil.copytree(skill_dir, target_dir / skill_dir.name)


def remove_managed(target_dir: Path, names: set[str], dry_run: bool) -> None:
    if dry_run:
        return
    for name in sorted(names):
        path = target_dir / name
        if path.exists():
            shutil.rmtree(path)
    manifest_path = target_dir / MANIFEST_NAME
    if manifest_path.exists():
        manifest_path.unlink()


def version_changes(
    old_manifest: dict[str, Any] | None,
    new_manifest: dict[str, Any],
) -> dict[str, list[str]]:
    old_versions = old_manifest.get("skill_versions", {}) if old_manifest else {}
    if not isinstance(old_versions, dict):
        old_versions = {}
    new_versions = new_manifest.get("skill_versions", {})
    if not isinstance(new_versions, dict):
        new_versions = {}

    old_names = {str(name) for name in old_versions}
    new_names = {str(name) for name in new_versions}
    changed = sorted(
        name
        for name in old_names & new_names
        if str(old_versions.get(name)) != str(new_versions.get(name))
    )
    return {
        "added": sorted(new_names - old_names),
        "removed": sorted(old_names - new_names),
        "changed": changed,
    }


def hooks_supported(agent: str, scope: str) -> bool:
    """Hooks are supported for Codex, Claude, and Copilot project/user installs."""
    return agent in HOOK_AGENTS and scope in HOOK_SCOPES


def _default_hook_support_files(agent: str) -> tuple[str, ...]:
    if agent == "copilot":
        return (*COMMON_HOOK_SUPPORT_FILES, *COPILOT_HOOK_SUPPORT_FILES)
    return COMMON_HOOK_SUPPORT_FILES


def _hook_support_files_from_manifest(manifest_source: Path, agent: str) -> tuple[str, ...]:
    if not manifest_source.is_file():
        return _default_hook_support_files(agent)
    try:
        manifest = json.loads(manifest_source.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _default_hook_support_files(agent)
    support_files = manifest.get("support_files") if isinstance(manifest, dict) else None
    if not isinstance(support_files, list):
        return _default_hook_support_files(agent)
    files: list[str] = []
    for item in support_files:
        if not isinstance(item, str) or not item.strip():
            return _default_hook_support_files(agent)
        files.append(item.strip())
    return tuple(dict.fromkeys(files))


def _hook_support_packages_from_manifest(manifest_source: Path) -> tuple[str, ...]:
    if not manifest_source.is_file():
        return COMMON_HOOK_SUPPORT_PACKAGES
    try:
        manifest = json.loads(manifest_source.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return COMMON_HOOK_SUPPORT_PACKAGES
    support_packages = manifest.get("support_packages") if isinstance(manifest, dict) else None
    if not isinstance(support_packages, list):
        return COMMON_HOOK_SUPPORT_PACKAGES
    packages: list[str] = []
    for item in support_packages:
        if not isinstance(item, str) or not HOOK_SUPPORT_PACKAGE_RE.fullmatch(item.strip()):
            return COMMON_HOOK_SUPPORT_PACKAGES
        packages.append(item.strip())
    return tuple(dict.fromkeys(packages))


def plan_hook_install(agent: str, scope: str, target: Path | None) -> HookPlan:
    """Compute a merge-safe hook install plan without writing anything.

    Project hooks install under the project root (``--target``). User hooks
    install under the agent home directory (Codex ``~/.codex``, Claude
    ``~/.claude``, Copilot ``~/.copilot``); ``--target`` does not relocate user
    hooks, so the skills ``--target`` override never accidentally redirects them.
    Set ``HOME`` (or the agent's home variable) to sandbox a user-scope hook
    install.
    """
    source_root = HOOK_SOURCE_ROOTS.get((agent, scope))
    if source_root is None:
        raise InstallError(
            f"hooks are only supported for codex, claude, and copilot project or user "
            f"installs, not {agent} {scope}"
        )
    if not source_root.is_dir():
        raise InstallError(
            f"missing built hook runtime {source_root.relative_to(ROOT)}; "
            "run python3 scripts/build.py --profile <profile>"
        )

    if scope == "project":
        if target is None:
            raise InstallError("project hook install requires the project root target")
        target_root = target.expanduser().resolve() / HOOK_PROJECT_SUBPATH[agent]
    else:
        target_root = (Path.home() / HOOK_USER_HOME_SUBDIR[agent]).expanduser().resolve()
    plan = HookPlan(agent=agent, source_root=source_root, target_root=target_root)

    scripts_subdir = HOOK_SCRIPTS_SUBDIR[agent]
    aux_subdir = HOOK_AUX_SUBDIR[agent]
    manifest_source = source_root / aux_subdir / HOOK_MANIFEST_NAME
    scripts_root = source_root / scripts_subdir
    script_names = tuple(
        path.name
        for path in sorted(scripts_root.glob("changeforge_*.py"))
        if path.is_file()
    )
    if not script_names:
        raise InstallError(f"no built hook scripts found in {scripts_root}")
    for script_name in script_names:
        source_script = source_root / scripts_subdir / script_name
        if not source_script.is_file():
            raise InstallError(f"missing built hook script {source_script.relative_to(ROOT)}")
        destination = target_root / scripts_subdir / script_name
        action = "overwrite" if destination.exists() else "create"
        plan.script_actions.append((source_script, destination, action))

    support_files = _hook_support_files_from_manifest(manifest_source, agent)
    for file_name in support_files:
        source_file = source_root / scripts_subdir / file_name
        if not source_file.is_file():
            raise InstallError(f"missing built hook support file {source_file.relative_to(ROOT)}")
        destination = target_root / scripts_subdir / file_name
        action = "overwrite" if destination.exists() else "create"
        plan.support_actions.append((source_file, destination, action))

    support_packages = _hook_support_packages_from_manifest(manifest_source)
    for package_name in support_packages:
        source_package = source_root / scripts_subdir / package_name
        if not source_package.is_dir():
            raise InstallError(f"missing built hook support package {source_package.relative_to(ROOT)}")
        destination = target_root / scripts_subdir / package_name
        action = "overwrite" if destination.exists() else "create"
        plan.support_package_actions.append((source_package, destination, action))

    manifest_target = target_root / aux_subdir / HOOK_MANIFEST_NAME
    plan.manifest_action = (
        manifest_source,
        manifest_target,
        "overwrite" if manifest_target.exists() else "create",
    )

    bootstrap_source = source_root / aux_subdir / BOOTSTRAP_FRAGMENT_NAME
    if bootstrap_source.is_file():
        bootstrap_target = target_root / aux_subdir / BOOTSTRAP_FRAGMENT_NAME
        plan.bootstrap_action = (
            bootstrap_source,
            bootstrap_target,
            "overwrite" if bootstrap_target.exists() else "create",
        )

    if agent == "codex":
        _plan_codex_config(plan)
    elif agent == "copilot":
        _plan_copilot_config(plan)
    else:
        _plan_claude_config(plan)
    plan.notes.extend(_hook_activation_notes(agent, scope))
    return plan


def _plan_copilot_config(plan: HookPlan) -> None:
    # VS Code Copilot reads every *.json in the hook folder, so the managed config
    # is a dedicated, ChangeForge-owned file. Place it (overwrite the managed copy)
    # without touching any other hook JSON the user authored in the same folder.
    config_relpath = Path("hooks") / "changeforge-hooks.json"
    source_config = load_json(plan.source_root / config_relpath)
    if not isinstance(source_config, dict):
        raise InstallError("built copilot changeforge-hooks.json is malformed")
    plan.config_target = plan.target_root / config_relpath
    plan.config_payload = source_config
    plan.config_summary.append("place hooks/changeforge-hooks.json (other hook JSON is untouched)")
    plan.config_summary.append("VS Code loads every *.json in .github/hooks; user hook files are preserved")


def _plan_codex_config(plan: HookPlan) -> None:
    source_config = load_json(plan.source_root / "hooks.json")
    if not isinstance(source_config, dict):
        raise InstallError("built codex hooks.json is malformed")
    target_config_path = plan.target_root / "hooks.json"
    plan.config_target = target_config_path
    existing = load_json(target_config_path)
    if existing is None:
        plan.config_payload = source_config
        plan.config_summary.append("create new .codex/hooks.json from ChangeForge template")
        return
    merged, summary = _merge_codex_hooks(existing, source_config)
    plan.config_payload = merged
    plan.config_summary.extend(summary)
    plan.config_summary.append("existing .codex/hooks.json hooks are preserved")


def _plan_claude_config(plan: HookPlan) -> None:
    fragment_name = "settings.changeforge-hooks.fragment.json"
    source_fragment = load_json(plan.source_root / fragment_name)
    if not isinstance(source_fragment, dict):
        raise InstallError("built claude settings fragment is malformed")
    plan.config_target = plan.target_root / fragment_name
    plan.config_payload = source_fragment
    plan.config_summary.append(f"place {fragment_name} (settings.json is never modified)")
    plan.config_summary.append(
        "merge the fragment 'hooks' into .claude/settings.json manually after review"
    )


def _merge_codex_hooks(
    existing: dict[str, Any],
    source: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    merged = json.loads(json.dumps(existing))
    existing_hooks = merged.get("hooks")
    if not isinstance(existing_hooks, dict):
        raise InstallError(
            "existing .codex/hooks.json 'hooks' is not an object; merge ChangeForge hooks manually"
        )
    source_hooks = source.get("hooks", {})
    if not isinstance(source_hooks, dict):
        raise InstallError("built codex hooks.json 'hooks' is not an object")

    known_commands = _collect_hook_commands(existing_hooks)
    summary: list[str] = []
    for event, groups in source_hooks.items():
        if not isinstance(groups, list):
            continue
        target_groups = existing_hooks.setdefault(event, [])
        if not isinstance(target_groups, list):
            raise InstallError(f"existing hooks.{event} is not a list; merge manually")
        for group in groups:
            new_group = _group_with_new_commands(group, known_commands)
            if new_group is not None:
                target_groups.append(new_group)
                summary.append(f"add {event} hook group: {group.get('matcher', '(stop)')}")
    if not summary:
        summary.append("ChangeForge hooks already present; no command added")
    return merged, summary


def _collect_hook_commands(value: Any) -> set[str]:
    commands: set[str] = set()
    if isinstance(value, dict):
        command = value.get("command")
        if isinstance(command, str):
            commands.add(command)
        for child in value.values():
            commands |= _collect_hook_commands(child)
    elif isinstance(value, list):
        for child in value:
            commands |= _collect_hook_commands(child)
    return commands


def _group_with_new_commands(group: Any, known_commands: set[str]) -> dict[str, Any] | None:
    if not isinstance(group, dict):
        return None
    hooks = group.get("hooks")
    if not isinstance(hooks, list):
        return None
    fresh = [
        hook
        for hook in hooks
        if isinstance(hook, dict)
        and isinstance(hook.get("command"), str)
        and hook["command"] not in known_commands
    ]
    if not fresh:
        return None
    for hook in fresh:
        known_commands.add(hook["command"])
    new_group = {key: value for key, value in group.items() if key != "hooks"}
    new_group["hooks"] = fresh
    return new_group


def _hook_activation_notes(agent: str, scope: str) -> list[str]:
    notes = ["hooks are not auto-trusted"]
    hook_label = "user hook" if scope == "user" else "project hook"
    if agent == "codex":
        notes.insert(
            0,
            "default policy: SDD material choice and pre-edit structure block; Stop closure is advisory",
        )
        notes.append(f"run /hooks in Codex and trust the {hook_label} after reviewing the command")
        if scope == "user":
            notes.append("user hooks were written to ~/.codex; they apply to every Codex project")
    elif agent == "copilot":
        notes.insert(
            0,
            "Copilot receives context and Stop closure compensation; Stop closure remains advisory",
        )
        notes.append("VS Code loads .json hook files automatically; review them before enabling")
        notes.append("use /hooks or 'Chat: Configure Hooks' in VS Code to inspect loaded hooks")
        if scope == "project":
            notes.append("project hooks live in .github/hooks; other hook JSON there is preserved")
        else:
            notes.append("user hooks live in ~/.copilot/hooks; they apply to every workspace")
    else:
        notes.insert(
            0,
            "default policy: SDD material choice and pre-edit structure block; Stop closure is advisory",
        )
        notes.append("merge settings.changeforge-hooks.fragment.json into settings.json")
        if scope == "user":
            notes.append(
                "user hooks live in ~/.claude; merge the fragment into ~/.claude/settings.json"
            )
    return notes


def apply_hook_install(plan: HookPlan, dry_run: bool) -> None:
    """Write the planned hook files. Preserves existing project hook config."""
    if dry_run:
        return
    # Create each destination parent so layouts that nest scripts (Copilot uses
    # hooks/changeforge/) are handled the same as the flat Codex/Claude layout.
    for source_script, destination, _action in plan.script_actions:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_script, destination)
        destination.chmod(0o755)
    for source_file, destination, _action in plan.support_actions:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, destination)
    for source_package, destination, _action in plan.support_package_actions:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source_package, destination)
    if plan.manifest_action is not None:
        manifest_source, manifest_target, _ = plan.manifest_action
        manifest_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(manifest_source, manifest_target)
    if plan.bootstrap_action is not None:
        bootstrap_source, bootstrap_target, _ = plan.bootstrap_action
        bootstrap_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(bootstrap_source, bootstrap_target)
    if plan.config_target is not None and plan.config_payload is not None:
        plan.config_target.parent.mkdir(parents=True, exist_ok=True)
        write_json(plan.config_target, plan.config_payload)


def render_hook_plan(plan: HookPlan) -> list[str]:
    """Human-readable description of a hook plan for dry-run output."""
    lines = [
        f"hooks: agent {plan.agent}",
        f"hooks: target {plan.target_root}",
    ]
    for _source, destination, action in plan.script_actions:
        lines.append(f"hooks: {action} script {destination.name}")
    for _source, destination, action in plan.support_actions:
        lines.append(f"hooks: {action} support {destination.name}")
    for _source, destination, action in plan.support_package_actions:
        lines.append(f"hooks: {action} support package {destination.name}")
    if plan.manifest_action is not None:
        lines.append(f"hooks: {plan.manifest_action[2]} {HOOK_MANIFEST_NAME}")
    if plan.bootstrap_action is not None:
        lines.append(f"hooks: {plan.bootstrap_action[2]} {BOOTSTRAP_FRAGMENT_NAME}")
    for summary in plan.config_summary:
        lines.append(f"hooks: config: {summary}")
    for note in plan.notes:
        lines.append(f"hooks: note: {note}")
    return lines


@dataclass
class BootstrapPlan:
    """Describes how the advisory route-preflight fragment would be installed."""

    agent: str
    scope: str
    source: Path
    target: Path
    action: str
    professional_source: Path | None = None
    professional_target: Path | None = None
    professional_action: str = ""
    notes: list[str] = field(default_factory=list)


def bootstrap_supported(agent: str, scope: str) -> bool:
    """The advisory bootstrap fragment can be installed for any project scope."""
    return scope == "project" and agent in BOOTSTRAP_AGENTS


def plan_bootstrap_install(
    agent: str,
    scope: str,
    project_root: Path,
    *,
    include_professional: bool = False,
) -> BootstrapPlan:
    """Plan a standalone advisory bootstrap install without writing anything.

    This installs only the route-preflight guidance fragment. It is the
    bootstrap path for runtimes without a session-start hook (such as Codex) and
    for users who want the preflight reminder without trusting executable hooks.
    """
    if not bootstrap_supported(agent, scope):
        raise InstallError("--with-bootstrap is only supported for project installs")
    if not UNIVERSAL_BOOTSTRAP_SOURCE.is_file():
        raise InstallError(
            f"missing built bootstrap fragment {UNIVERSAL_BOOTSTRAP_SOURCE.relative_to(ROOT)}; "
            "run python3 scripts/build.py --profile <profile>"
        )
    target = (
        project_root.expanduser().resolve()
        / BOOTSTRAP_PROJECT_SUBPATH
        / BOOTSTRAP_FRAGMENT_NAME
    )
    action = "overwrite" if target.exists() else "create"
    professional_source: Path | None = None
    professional_target: Path | None = None
    professional_action = ""
    if include_professional:
        if not UNIVERSAL_PROFESSIONAL_BOOTSTRAP_SOURCE.is_file():
            raise InstallError(
                "missing built professional bootstrap fragment "
                f"{UNIVERSAL_PROFESSIONAL_BOOTSTRAP_SOURCE.relative_to(ROOT)}; "
                "run python3 scripts/build.py --profile <profile>"
            )
        professional_source = UNIVERSAL_PROFESSIONAL_BOOTSTRAP_SOURCE
        professional_target = (
            project_root.expanduser().resolve()
            / BOOTSTRAP_PROJECT_SUBPATH
            / PROFESSIONAL_BOOTSTRAP_FRAGMENT_NAME
        )
        professional_action = "overwrite" if professional_target.exists() else "create"
    notes = [
        "bootstrap is advisory route-preflight guidance, not an executable hook",
        "reference this file from your agent instructions (for example AGENTS.md) to enable it",
    ]
    if agent == "claude":
        notes.append(
            "Claude project hooks can also wire this as a SessionStart hook via --with-hooks"
        )
    elif agent == "codex":
        notes.append(
            "Codex project hooks can also wire this as a SessionStart hook via --with-hooks; "
            "this advisory fragment is the no-trust alternative"
        )
    return BootstrapPlan(
        agent=agent,
        scope=scope,
        source=UNIVERSAL_BOOTSTRAP_SOURCE,
        target=target,
        action=action,
        professional_source=professional_source,
        professional_target=professional_target,
        professional_action=professional_action,
        notes=notes,
    )


def apply_bootstrap_install(plan: BootstrapPlan, dry_run: bool) -> None:
    """Write the planned bootstrap fragment. Only touches the managed fragment file."""
    if dry_run:
        return
    plan.target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(plan.source, plan.target)
    if plan.professional_source is not None and plan.professional_target is not None:
        plan.professional_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(plan.professional_source, plan.professional_target)


def render_bootstrap_plan(plan: BootstrapPlan) -> list[str]:
    """Human-readable description of a bootstrap plan for dry-run output."""
    lines = [
        f"bootstrap: agent {plan.agent}",
        f"bootstrap: target {plan.target}",
        f"bootstrap: {plan.action} {BOOTSTRAP_FRAGMENT_NAME}",
    ]
    if plan.professional_target is not None:
        lines.append(
            f"bootstrap: {plan.professional_action} {PROFESSIONAL_BOOTSTRAP_FRAGMENT_NAME}"
        )
    for note in plan.notes:
        lines.append(f"bootstrap: note: {note}")
    return lines
