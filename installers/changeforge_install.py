"""Shared helpers for ChangeForge runtime installers."""

from __future__ import annotations

import json
import re
import shutil
import sys
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
AGENTS = ("codex", "claude", "copilot", "openai-api")
SCOPES = ("project", "user", "admin")

SOURCE_SKILL_ROOTS = {
    ("codex", "project"): ROOT / "dist" / "codex" / "project" / ".agents" / "skills",
    ("codex", "user"): ROOT / "dist" / "codex" / "user" / ".agents" / "skills",
    ("codex", "admin"): ROOT / "dist" / "codex" / "admin" / "skills",
    ("claude", "project"): ROOT / "dist" / "claude" / "project" / ".claude" / "skills",
    ("claude", "user"): ROOT / "dist" / "claude" / "user" / ".claude" / "skills",
    ("copilot", "project"): ROOT / "dist" / "copilot" / "project" / ".github" / "skills",
    ("copilot", "user"): ROOT / "dist" / "copilot" / "user" / ".copilot" / "skills",
}

PROJECT_SUBPATHS = {
    "codex": Path(".agents") / "skills",
    "claude": Path(".claude") / "skills",
    "copilot": Path(".github") / "skills",
}

DEFAULT_TARGET_DIRS = {
    ("codex", "user"): Path.home() / ".agents" / "skills",
    ("codex", "admin"): Path("/etc/codex/skills"),
    ("claude", "user"): Path.home() / ".claude" / "skills",
    ("copilot", "user"): Path.home() / ".copilot" / "skills",
}

FOUNDATION_MODES = {
    "recommended": "compiled-references",
    "full": "compiled-references",
    "dev": "top-level-and-compiled-references",
}


class InstallError(Exception):
    """Raised for unsafe or unsupported install operations."""


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
