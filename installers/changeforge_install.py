"""Shared helpers for hookless rd-skills Skill and Agent Profile installers."""

from __future__ import annotations

import json
import hashlib
import importlib.util
import os
import re
import shutil
import sys
import zipfile
import zlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_NAME = ".changeforge-install-manifest.json"
BUILD_MANIFEST_NAME = ".changeforge-build-manifest.json"
COMPILED_LAYER3_FORMAT = "ai-consumption-v1"
HOST_ENFORCEMENT_SOURCE = ROOT / "src" / "agent-profiles" / "host-enforcement.json"
HOST_PRODUCT_SURFACES_SOURCE = (
    ROOT / "src" / "agent-profiles" / "host-product-surfaces.json"
)
CORE_CONTRACTS_SOURCE = ROOT / "src" / "control-model" / "core-contracts.json"
BACKUP_DIR_NAME = ".changeforge-backups"
RUNTIME_PROFILE = "recommended"
RUNTIME_SKILL_COUNT = 26
CURRENT_RUNTIME_PROFILE_COUNTS = {"recommended": 26}
HISTORICAL_PROFILE_COUNTS = {"recommended": 27, "full": 40, "dev": 190}
CURRENT_INVENTORY_GENERATION = "runtime-26"
HISTORICAL_INVENTORY_GENERATION = "runtime-27"
HISTORICAL_UNCHANGED_LAYER_SHA256 = {
    "control": "46f66196a4887257b390bbd6302c1160dab50b6c078b4afacac520b8ee3c04e4",
    "foundation": "bed21019ab7e9e802252638fde77d90b850904620031460f0d6499b01defee66",
    "domain": "3a8d304206971885fe7a6f5cbfdf17ee6c0d3eec8e836de6ab8e7c2b252d231b",
}
HISTORICAL_RUNTIME_27_PROFESSIONAL_SKILLS = frozenset(
    {
        "acceptance-criteria-builder",
        "ai-code-review-refactor",
        "architecture-impact-reviewer",
        "backend-change-builder",
        "change-documentation-gate",
        "change-intake-compiler",
        "data-api-contract-changer",
        "data-middleware-change-builder",
        "delivery-release-gate",
        "domain-impact-modeler",
        "engineering-artifact-review",
        "engineering-change-analysis",
        "experience-impact-modeler",
        "frontend-change-builder",
        "high-risk-design-review",
        "incident-response-coordinator",
        "installed-client-change-builder",
        "integration-change-builder",
        "logging-design-gate",
        "platform-infrastructure-change-builder",
        "quality-test-gate",
        "reliability-observability-gate",
        "repository-tooling-change-builder",
        "routing-quality-review",
        "security-privacy-gate",
        "task-dag-planner",
    }
)
AGENTS = ("codex", "claude", "copilot", "cline", "openai-api")
SCOPES = ("project", "user", "admin")
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
AGENT_PROFILE_NAMES = (
    "main-control-agent",
    "analysis-agent",
    "task-agent",
    "review-agent",
)
ENFORCEMENT_STATUSES = {
    "native-enforced",
    "sandbox-enforced",
    "prompt-enforced",
    "unsupported",
}
PRODUCT_ARTIFACT_DELIVERY = {
    "skills-and-agent-profiles",
    "skills-only",
    "zip-packages",
}
PRODUCT_LIVE_SKILL_INVOCATION = {
    "supported",
    "not-established",
    "not-applicable",
}
PRODUCT_FULL_WORKFLOW = {
    "available",
    "not-established",
    "integration-owned",
}
PRODUCT_LIMITATION_CODES = {
    "artifact-health-only",
    "copilot-cli-only",
    "artifact-delivery-only",
    "api-integration-only",
}
HOST_ENFORCEMENT_CAPABILITIES = {
    "profile_delivery",
    "skill_loading",
    "subagent_dispatch",
    "partial_handoff",
    "isolated_workspace",
}
ROLE_ENFORCEMENT_CAPABILITIES = {
    "tool_allowlist",
    "workspace_write_protection",
    "read_only_command_semantics",
    "external_source_read",
}
LEGACY_PROFILE_NAMES = (
    "analysis-worker",
    "specialist-worker",
    "validation-agent",
    "independent-reviewer",
    "integration-worker",
    "pdd-freezer",
    "ddd-freezer",
    "sdd-contract-freezer",
    "tdd-behavior-freezer",
    "task-implementer",
    "phase-reviewer",
    "context-scout",
)
LEGACY_HOOK_SCRIPT_NAMES = frozenset(
    {
        "changeforge_action_classifier.py",
        "changeforge_adapter_capabilities.py",
        "changeforge_branch_route_summary.py",
        "changeforge_closure_contract.py",
        "changeforge_common.py",
        "changeforge_compaction.py",
        "changeforge_compaction_contract.py",
        "changeforge_compaction_ledger.py",
        "changeforge_compaction_reinject.py",
        "changeforge_compaction_snapshot.py",
        "changeforge_context_control_policy.py",
        "changeforge_engineering_control_bootstrap.py",
        "changeforge_engineering_control_router.py",
        "changeforge_engineering_control_state.py",
        "changeforge_evidence_adapter.py",
        "changeforge_evidence_ledger.py",
        "changeforge_executor_adapter_core.py",
        "changeforge_gate_result.py",
        "changeforge_hook.py",
        "changeforge_hook_policy.py",
        "changeforge_lifecycle_state.py",
        "changeforge_light_ledger.py",
        "changeforge_normalized_event.py",
        "changeforge_permission_policy_gate.py",
        "changeforge_phase_artifact_gate.py",
        "changeforge_phase_capsule.py",
        "changeforge_phase_subagent_dispatch.py",
        "changeforge_post_edit_structure_gate.py",
        "changeforge_post_tool_collector.py",
        "changeforge_pre_edit_structure_gate.py",
        "changeforge_pre_tool_risk_preview.py",
        "changeforge_process_phase_gate.py",
        "changeforge_professional_injector.py",
        "changeforge_read_context_gate.py",
        "changeforge_review_gate.py",
        "changeforge_risk_surface_gate.py",
        "changeforge_runtime_adapters.py",
        "changeforge_runtime_route_resolver.py",
        "changeforge_sdd_material_choice_gate.py",
        "changeforge_session_bootstrap.py",
        "changeforge_skill_index.py",
        "changeforge_state_reducer.py",
        "changeforge_stop_closure_gate.py",
        "changeforge_subagent_review_gate.py",
        "changeforge_subagent_skill_contract.py",
        "changeforge_subagent_stop_reminder.py",
        "changeforge_tool_output_boundary.py",
        "changeforge_tool_output_boundary_gate.py",
        "changeforge_user_prompt_route_reminder.py",
    }
)
LEGACY_SUPPORT_FILES = frozenset(
    {
        "changeforge_professional_contract.md",
        "changeforge_copilot_professional_contract.md",
        "changeforge_copilot_skill_summary.md",
    }
)
LEGACY_SUPPORT_DIRECTORIES = frozenset(
    {"runtime_governance", "validation_broker", "repository_intelligence", "project_memory"}
)
CHANGEFORGE_HOOK_COMMAND_RE = re.compile(r"\bchangeforge_[A-Za-z0-9_]+\.py\b")
MAX_ZIP_FILES = 500
MAX_ZIP_BYTES = 5 * 1024 * 1024
MAX_ZIP_FILE_BYTES = 2 * 1024 * 1024

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
SOURCE_PROFILE_ROOTS = {
    ("codex", "project"): ROOT / "dist" / "codex" / "project" / ".codex" / "agents",
    ("codex", "user"): ROOT / "dist" / "codex" / "user" / ".codex" / "agents",
    ("codex", "admin"): ROOT / "dist" / "codex" / "admin" / "agents",
    ("claude", "project"): ROOT / "dist" / "claude" / "project" / ".claude" / "agents",
    ("claude", "user"): ROOT / "dist" / "claude" / "user" / ".claude" / "agents",
    ("copilot", "project"): ROOT / "dist" / "copilot" / "project" / ".github" / "agents",
    ("copilot", "user"): ROOT / "dist" / "copilot" / "user" / ".copilot" / "agents",
}
PROJECT_SKILL_SUBPATHS = {
    "codex": Path(".agents") / "skills",
    "claude": Path(".claude") / "skills",
    "copilot": Path(".github") / "skills",
    "cline": Path(".cline") / "skills",
}
PROJECT_PROFILE_SUBPATHS = {
    "codex": Path(".codex") / "agents",
    "claude": Path(".claude") / "agents",
    "copilot": Path(".github") / "agents",
}
DEFAULT_SKILL_TARGETS = {
    ("codex", "user"): Path.home() / ".agents" / "skills",
    ("codex", "admin"): Path("/etc/codex/skills"),
    ("claude", "user"): Path.home() / ".claude" / "skills",
    ("copilot", "user"): Path.home() / ".copilot" / "skills",
    ("cline", "user"): Path.home() / ".cline" / "skills",
}
DEFAULT_PROFILE_TARGETS = {
    ("codex", "user"): Path.home() / ".codex" / "agents",
    ("codex", "admin"): Path("/etc/codex/agents"),
    ("claude", "user"): Path.home() / ".claude" / "agents",
    ("copilot", "user"): Path.home() / ".copilot" / "agents",
}


class InstallError(Exception):
    """Raised for unsafe or unsupported installation operations."""


@dataclass(frozen=True)
class InstallTargets:
    skills: Path
    profiles: Path | None


@dataclass(frozen=True)
class InstalledManifestClassification:
    """Validated ownership facts from a current or supported historical manifest."""

    profile: str
    inventory_generation: str
    skill_names: frozenset[str]
    profile_files: frozenset[str]

    @property
    def migration_required(self) -> bool:
        return (
            self.inventory_generation != CURRENT_INVENTORY_GENERATION
            or self.profile != RUNTIME_PROFILE
        )


def _path_lexists(path: Path) -> bool:
    """Return true for regular paths and for live or dangling symlinks."""
    return path.exists() or path.is_symlink()


def _reject_symlink(path: Path, context: str) -> None:
    if path.is_symlink():
        raise InstallError(f"refusing to follow {context} symlink {path}")


def _ensure_parent_within(path: Path, roots: list[Path], context: str) -> None:
    """Reject an ancestor symlink that redirects a managed child outside its roots."""
    try:
        parent = path.parent.resolve(strict=False)
        resolved_roots = [root.expanduser().resolve(strict=False) for root in roots]
    except (OSError, RuntimeError) as exc:
        raise InstallError(f"cannot resolve {context} path {path}: {exc}") from exc
    if not any(parent == root or parent.is_relative_to(root) for root in resolved_roots):
        raise InstallError(f"refusing {context} path outside its managed root: {path}")


def _ensure_path_within(path: Path, root: Path, context: str) -> None:
    """Reject a managed root or one of its ancestors when it redirects outside."""
    try:
        resolved = path.expanduser().resolve(strict=False)
        resolved_root = root.expanduser().resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise InstallError(f"cannot resolve {context} path {path}: {exc}") from exc
    if resolved != resolved_root and not resolved.is_relative_to(resolved_root):
        raise InstallError(f"refusing {context} path outside its managed root: {path}")


def _reject_symlink_chain(path: Path, root: Path, context: str) -> None:
    """Reject symlinks in a lexically bounded built-source path."""
    absolute_path = path.expanduser().absolute()
    absolute_root = root.expanduser().absolute()
    try:
        relative = absolute_path.relative_to(absolute_root)
    except ValueError as exc:
        raise InstallError(f"refusing {context} outside {absolute_root}: {path}") from exc
    current = absolute_root
    _reject_symlink(current, context)
    for part in relative.parts:
        current = current / part
        _reject_symlink(current, context)


def _path_forms(path: Path, context: str) -> tuple[Path, Path]:
    """Return normalized lexical and symlink-resolved forms without mutating paths."""
    try:
        expanded = path.expanduser()
        lexical = Path(os.path.abspath(os.fspath(expanded)))
        resolved = expanded.resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise InstallError(f"cannot resolve {context} path {path}: {exc}") from exc
    return lexical, resolved


def _paths_overlap(left: Path, right: Path) -> bool:
    return (
        left == right
        or left.is_relative_to(right)
        or right.is_relative_to(left)
    )


def validate_install_path_separation(
    source: Path,
    source_profiles: Path | None,
    targets: InstallTargets,
) -> None:
    """Reject equal or ancestor-related build sources and install targets.

    Both lexical paths and symlink-resolved paths are checked. This preflight
    must run before backup, legacy cleanup, replacement, or manifest writes so
    an install can never delete or overwrite the build artifacts it is copying.
    """
    paths = [
        ("built Skill source", source),
        *(
            [("built Agent Profile source", source_profiles)]
            if source_profiles is not None
            else []
        ),
        ("Skill target", targets.skills),
        *(
            [("Agent Profile target", targets.profiles)]
            if targets.profiles is not None
            else []
        ),
    ]
    normalized = [
        (label, path, _path_forms(path, label))
        for label, path in paths
    ]
    for index, (left_label, left_path, left_forms) in enumerate(normalized):
        for right_label, right_path, right_forms in normalized[index + 1:]:
            if any(
                _paths_overlap(left_form, right_form)
                for left_form, right_form in zip(left_forms, right_forms)
            ):
                raise InstallError(
                    f"unsafe overlapping install paths: {left_label} {left_path} "
                    f"and {right_label} {right_path} must be disjoint"
                )


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
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def validate_agent_scope(agent: str, scope: str) -> None:
    if agent not in AGENTS:
        raise InstallError(f"unsupported agent: {agent}")
    if scope not in SCOPES:
        raise InstallError(f"unsupported scope: {scope}")
    if agent == "openai-api":
        return
    if (agent, scope) not in SOURCE_SKILL_ROOTS:
        supported = ", ".join(sorted(value for name, value in SOURCE_SKILL_ROOTS if name == agent))
        raise InstallError(f"{agent} supports scope(s): {supported}")


def resolve_source_profile_dir(agent: str, scope: str) -> Path:
    validate_agent_scope(agent, scope)
    if agent == "openai-api":
        source = ROOT / "dist" / "openai-api" / "zips" / RUNTIME_PROFILE
    else:
        source = SOURCE_SKILL_ROOTS[(agent, scope)] / RUNTIME_PROFILE
    if not source.is_dir():
        raise InstallError(
            f"missing built runtime {source.relative_to(ROOT)}; "
            "run python3 scripts/build.py"
        )
    return source


def validate_openai_bundles(source: Path) -> int:
    _reject_symlink_chain(source, ROOT / "dist", "OpenAI API bundle root")
    _ensure_path_within(source, ROOT / "dist", "OpenAI API bundle root")
    zips = sorted(source.glob("*.zip"))
    if len(zips) != RUNTIME_SKILL_COUNT:
        raise InstallError(
            f"expected {RUNTIME_SKILL_COUNT} OpenAI API zip files, found {len(zips)}"
        )
    manifest_root = (
        ROOT / "dist" / "universal" / "skills" / RUNTIME_PROFILE
    )
    manifest = read_build_manifest(manifest_root)
    validate_authoritative_build_inputs(manifest)
    validate_build_core_model(manifest)
    if manifest.get("profile") != RUNTIME_PROFILE:
        raise InstallError("OpenAI API build manifest is not the runtime build")
    declared_values = manifest.get("top_level_skills")
    if (
        not isinstance(declared_values, list)
        or len(declared_values) != RUNTIME_SKILL_COUNT
        or any(
            not isinstance(name, str) or not _valid_skill_name(name)
            for name in declared_values
        )
        or len(set(declared_values)) != RUNTIME_SKILL_COUNT
    ):
        raise InstallError("OpenAI API build manifest has invalid runtime Skills")
    declared = set(declared_values)
    if declared != {path.stem for path in zips}:
        raise InstallError("OpenAI API zip names do not match the built Skill manifest")
    for path in zips:
        _reject_symlink(path, "OpenAI API bundle")
        _validate_openai_bundle(path)
    return len(zips)


def _validate_openai_bundle(path: Path) -> None:
    try:
        with zipfile.ZipFile(path) as archive:
            entries = [item for item in archive.infolist() if item.filename]
            members = [item for item in entries if not item.is_dir()]
            names = [item.filename for item in members]
            if not names or len(names) > MAX_ZIP_FILES:
                raise InstallError(f"OpenAI API zip {path} has an invalid file count")
            if len(names) != len(set(names)):
                raise InstallError(f"OpenAI API zip {path} contains duplicate file names")
            for entry in entries:
                name = entry.filename
                member_path = PurePosixPath(name)
                if (
                    "\\" in name
                    or member_path.is_absolute()
                    or ".." in member_path.parts
                    or not member_path.parts
                ):
                    raise InstallError(f"OpenAI API zip {path} contains an unsafe path")
            top_levels = {PurePosixPath(item.filename).parts[0] for item in entries}
            if top_levels != {path.stem}:
                raise InstallError(
                    f"OpenAI API zip {path} must contain one matching top-level folder"
                )
            skill_entries = [name for name in names if name.endswith("/SKILL.md")]
            if len(skill_entries) != 1 or skill_entries[0] != f"{path.stem}/SKILL.md":
                raise InstallError(
                    f"OpenAI API zip {path} must contain exactly one root SKILL.md"
                )
            if any(item.file_size > MAX_ZIP_FILE_BYTES for item in members):
                raise InstallError(f"OpenAI API zip {path} contains an oversized file")
            if sum(item.file_size for item in members) > MAX_ZIP_BYTES:
                raise InstallError(f"OpenAI API zip {path} exceeds the uncompressed size limit")
            bad_member = archive.testzip()
            if bad_member is not None:
                raise InstallError(
                    f"OpenAI API zip {path} failed CRC validation at {bad_member}"
                )
    except InstallError:
        raise
    except (EOFError, OSError, RuntimeError, zipfile.BadZipFile, zlib.error) as exc:
        raise InstallError(f"invalid OpenAI API zip {path}: {exc}") from exc


def resolve_targets(agent: str, scope: str, target: Path | None) -> InstallTargets:
    validate_agent_scope(agent, scope)
    if agent == "openai-api":
        raise InstallError("openai-api uses zip output and has no installation target")
    if scope == "project":
        if target is None:
            raise InstallError("--target is required for project installs")
        project = target.expanduser().resolve()
        skills = project / PROJECT_SKILL_SUBPATHS[agent]
        profile_subpath = PROJECT_PROFILE_SUBPATHS.get(agent)
        profiles = project / profile_subpath if profile_subpath is not None else None
        _ensure_path_within(skills, project, "project Skill target")
        _reject_symlink_chain(skills, project, "project Skill target")
        if profiles is not None:
            _ensure_path_within(profiles, project, "project Agent Profile target")
            _reject_symlink_chain(
                profiles,
                project,
                "project Agent Profile target",
            )
        return InstallTargets(
            skills=skills,
            profiles=profiles,
        )
    skill_target = target.expanduser().resolve() if target is not None else DEFAULT_SKILL_TARGETS[(agent, scope)]
    profiles = DEFAULT_PROFILE_TARGETS.get((agent, scope))
    if target is None:
        boundary = Path("/etc/codex") if scope == "admin" else Path.home()
        _ensure_path_within(skill_target, boundary, f"{scope} Skill target")
    if profiles is not None:
        boundary = Path("/etc/codex") if scope == "admin" else Path.home()
        _ensure_path_within(profiles, boundary, f"{scope} Agent Profile target")
    return InstallTargets(skills=skill_target, profiles=profiles)


def resolve_source_profiles(agent: str, scope: str) -> Path | None:
    return SOURCE_PROFILE_ROOTS.get((agent, scope))


def list_skill_dirs(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return [
        path for path in sorted(root.iterdir())
        if path.is_dir() and not path.name.startswith(".") and (path / "SKILL.md").is_file()
    ]


def list_profile_files(root: Path | None) -> list[Path]:
    if root is None or not root.is_dir():
        return []
    return [path for path in sorted(root.iterdir()) if path.is_file()]


def profile_role_from_filename(value: str) -> str:
    if value.endswith(".agent.md"):
        return value.removesuffix(".agent.md")
    return Path(value).stem


def profile_file_sha256(root: Path | None, agent: str) -> dict[str, str]:
    if root is None:
        return {}
    extension = {"codex": ".toml", "claude": ".md", "copilot": ".agent.md"}[agent]
    digests: dict[str, str] = {}
    for role in AGENT_PROFILE_NAMES:
        path = root / f"{role}{extension}"
        if path.is_symlink():
            raise InstallError(f"managed Agent Profile must not be a symlink: {path}")
        if path.is_file():
            digests[role] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digests


def validate_built_source(
    agent: str,
    source: Path,
    source_profiles: Path | None,
) -> dict[str, Any]:
    """Fail before any target mutation when built delivery is incomplete."""
    _reject_symlink_chain(source, ROOT / "dist", "built Skill source")
    _ensure_path_within(source, ROOT / "dist", "built Skill source")
    source_symlinks = [path for path in source.rglob("*") if path.is_symlink()]
    if source_symlinks:
        raise InstallError(
            f"built Skill source cannot contain symlinks: {source_symlinks[0]}"
        )
    build = read_build_manifest(source)
    validate_authoritative_build_inputs(build)
    validate_build_core_model(build)
    enforcement = read_host_enforcement_source()
    if build.get("agent_profile_enforcement") != enforcement["hosts"]:
        raise InstallError("build manifest host enforcement matrix is stale or invalid")
    enforcement_source = build.get("agent_profile_enforcement_source")
    expected_digest = hashlib.sha256(HOST_ENFORCEMENT_SOURCE.read_bytes()).hexdigest()
    if (
        not isinstance(enforcement_source, dict)
        or enforcement_source.get("schema_version") != enforcement["schema_version"]
        or enforcement_source.get("sha256") != expected_digest
    ):
        raise InstallError("build manifest host enforcement source digest is stale or invalid")
    if build.get("profile") != RUNTIME_PROFILE:
        raise InstallError(
            f"built runtime is {build.get('profile')!r}, expected {RUNTIME_PROFILE!r}"
        )
    declared = build.get("top_level_skills")
    if not isinstance(declared, list) or any(not isinstance(name, str) or not _valid_skill_name(name) for name in declared):
        raise InstallError("build manifest has invalid top_level_skills")
    declared_names = set(declared)
    actual_names = {path.name for path in list_skill_dirs(source)}
    visible_directories = {
        path.name for path in source.iterdir()
        if path.is_dir() and not path.name.startswith(".")
    }
    if (
        len(declared) != len(declared_names)
        or len(declared_names) != RUNTIME_SKILL_COUNT
    ):
        raise InstallError(
            f"build manifest must declare exactly {RUNTIME_SKILL_COUNT} unique Skills"
        )
    if actual_names != declared_names or visible_directories != declared_names:
        raise InstallError("built Skill directories do not match the build manifest")
    if source_profiles is not None:
        _reject_symlink_chain(
            source_profiles,
            ROOT / "dist",
            "built Agent Profile root",
        )
        _ensure_path_within(
            source_profiles,
            ROOT / "dist",
            "built Agent Profile source",
        )
        extension = {"codex": ".toml", "claude": ".md", "copilot": ".agent.md"}[agent]
        expected_files = {f"{name}{extension}" for name in AGENT_PROFILE_NAMES}
        profile_entries = list(source_profiles.iterdir())
        if any(path.is_symlink() for path in profile_entries):
            raise InstallError("built Agent Profile directory cannot contain symlinks")
        profile_paths = [path for path in profile_entries if path.is_file()]
        actual_files = {path.name for path in profile_paths}
        if actual_files != expected_files or {path.name for path in profile_entries} != expected_files:
            raise InstallError("built Agent Profile directory must contain exactly the four profile files")
        if set(build.get("agent_profiles") or []) != set(AGENT_PROFILE_NAMES):
            raise InstallError("build manifest must declare exactly the four Agent Profiles")
        declared_digests = build.get("agent_profile_sha256")
        expected_digests = (
            declared_digests.get(agent) if isinstance(declared_digests, dict) else None
        )
        actual_digests = profile_file_sha256(source_profiles, agent)
        if expected_digests != actual_digests:
            raise InstallError("built Agent Profile digests do not match the build manifest")
    return build


def validate_authoritative_build_inputs(build: dict[str, Any]) -> None:
    """Use the build authority's sole comparator and fail closed if unavailable."""

    validation_path = ROOT / "scripts" / "validation_utils.py"
    if not validation_path.is_file():
        raise InstallError(
            "authoritative build input comparator is unavailable; source freshness is unverified"
        )
    module_name = "changeforge_installer_authoritative_build_inputs"
    spec = importlib.util.spec_from_file_location(module_name, validation_path)
    if spec is None or spec.loader is None:
        raise InstallError("cannot load authoritative build input comparator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
        errors = module.authoritative_build_input_snapshot_errors(
            build.get("authoritative_build_inputs"),
            ROOT,
        )
    except Exception as exc:
        raise InstallError(
            f"authoritative build input freshness validation failed: {exc}"
        ) from exc
    finally:
        sys.modules.pop(module_name, None)
    if errors:
        raise InstallError("; ".join(str(error) for error in errors))


def validated_built_profile_sha256(
    agent: str, scope: str
) -> dict[str, str]:
    """Return Profile digests anchored in the current validated build output."""

    source = resolve_source_profile_dir(agent, scope)
    source_profiles = resolve_source_profiles(agent, scope)
    build = validate_built_source(agent, source, source_profiles)
    module = _load_current_build_authority()
    try:
        source_digests = module._agent_profile_digests(
            module._load_agent_profiles(), module._load_host_enforcement()
        )
    except Exception as exc:
        raise InstallError(f"cannot render current authoritative Agent Profiles: {exc}") from exc
    digests = build.get("agent_profile_sha256")
    expected = digests.get(agent) if isinstance(digests, dict) else None
    if not isinstance(expected, dict) or set(expected) != set(AGENT_PROFILE_NAMES):
        raise InstallError("validated build has no complete Agent Profile digest map")
    rendered = source_digests.get(agent)
    if expected != rendered:
        raise InstallError(
            "validated build Agent Profile digests differ from the current source renderer"
        )
    return {str(role): str(digest) for role, digest in rendered.items()}


def validated_built_core_model(agent: str, scope: str) -> dict[str, Any]:
    """Return core-model metadata anchored in the current validated build."""

    source = resolve_source_profile_dir(agent, scope)
    source_profiles = resolve_source_profiles(agent, scope)
    build = validate_built_source(agent, source, source_profiles)
    return dict(validate_build_core_model(build))


def load_json(path: Path) -> dict[str, Any] | None:
    _reject_symlink(path, "JSON")
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InstallError(f"{path} contains invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise InstallError(f"{path} must contain a JSON object")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    _reject_symlink(path, "JSON")
    path.parent.mkdir(parents=True, exist_ok=True)
    _reject_symlink(path, "JSON")
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_manifest(target_dir: Path) -> dict[str, Any] | None:
    return load_json(target_dir / MANIFEST_NAME)


def read_build_manifest(source_dir: Path) -> dict[str, Any]:
    value = load_json(source_dir / BUILD_MANIFEST_NAME)
    if value is None:
        raise InstallError(f"{source_dir} is missing {BUILD_MANIFEST_NAME}")
    if value.get("architecture") != "hookless-control-plane-v1":
        raise InstallError(f"{source_dir} is not a hookless rd-skills build")
    if value.get("compiled_layer3_format") != COMPILED_LAYER3_FORMAT:
        raise InstallError(
            f"{source_dir} compiled_layer3_format must equal "
            f"{COMPILED_LAYER3_FORMAT!r}"
        )
    return value


def read_core_contract_source() -> dict[str, Any]:
    """Read the authoritative core model needed to validate delivery metadata."""

    value = load_json(CORE_CONTRACTS_SOURCE)
    if (
        value is None
        or value.get("schema_version") != 1
        or value.get("kind") != "changeforge.core_contracts"
    ):
        raise InstallError(
            "authoritative core model must use changeforge.core_contracts schema 1"
        )
    return value


def core_model_metadata() -> dict[str, Any]:
    """Return the exact source digest contract copied through build and install."""

    value = read_core_contract_source()
    return {
        "path": CORE_CONTRACTS_SOURCE.relative_to(ROOT).as_posix(),
        "schema_version": value["schema_version"],
        "kind": value["kind"],
        "sha256": hashlib.sha256(CORE_CONTRACTS_SOURCE.read_bytes()).hexdigest(),
    }


def validate_build_core_model(build: dict[str, Any]) -> dict[str, Any]:
    expected = core_model_metadata()
    if build.get("core_model") != expected:
        raise InstallError("build manifest core model digest is stale or invalid")
    return expected


def read_host_enforcement_source() -> dict[str, Any]:
    value = load_json(HOST_ENFORCEMENT_SOURCE)
    if value is None or value.get("schema_version") != 5:
        raise InstallError("host enforcement source must use schema_version 5")
    statuses = value.get("status_values")
    if not isinstance(statuses, list) or set(statuses) != ENFORCEMENT_STATUSES:
        raise InstallError("host enforcement source has an invalid status enum")
    hosts = value.get("hosts")
    if not isinstance(hosts, dict) or set(hosts) != set(AGENTS):
        raise InstallError("host enforcement source must contain every supported agent")
    expected_host_fields = HOST_ENFORCEMENT_CAPABILITIES | {"roles"}
    for agent in AGENTS:
        entry = hosts[agent]
        if not isinstance(entry, dict) or set(entry) != expected_host_fields:
            raise InstallError(f"{agent}: host enforcement fields must match schema v5")
        for capability in HOST_ENFORCEMENT_CAPABILITIES:
            if entry.get(capability) not in ENFORCEMENT_STATUSES:
                raise InstallError(f"{agent}: invalid {capability} enforcement")
        roles = entry.get("roles")
        if not isinstance(roles, dict) or set(roles) != set(AGENT_PROFILE_NAMES):
            raise InstallError(f"{agent}: enforcement roles must be the four static Profiles")
        for role, role_entry in roles.items():
            expected_role_fields = ROLE_ENFORCEMENT_CAPABILITIES | {
                "rendered_tools",
                "limitations",
            }
            if not isinstance(role_entry, dict) or set(role_entry) != expected_role_fields:
                raise InstallError(
                    f"{agent}:{role}: enforcement entry must match schema v5"
                )
            for capability in ROLE_ENFORCEMENT_CAPABILITIES:
                if role_entry.get(capability) not in ENFORCEMENT_STATUSES:
                    raise InstallError(f"{agent}:{role}: invalid {capability} enforcement")
            if not isinstance(role_entry.get("rendered_tools"), list):
                raise InstallError(f"{agent}:{role}: rendered_tools must be a list")
            if not isinstance(role_entry.get("limitations"), list):
                raise InstallError(f"{agent}:{role}: limitations must be a list")
    return value


def host_enforcement_for_agent(agent: str) -> dict[str, Any]:
    if agent not in AGENTS:
        raise InstallError(f"unsupported agent {agent!r}")
    return dict(read_host_enforcement_source()["hosts"][agent])


def read_host_product_surfaces(source: Path | None = None) -> dict[str, Any]:
    """Load the closed product-surface projection over installer agent identities."""

    value = load_json(source or HOST_PRODUCT_SURFACES_SOURCE)
    if value is None:
        raise InstallError("missing host product-surface authority")
    if set(value) != {"schema_version", "kind", "surfaces"}:
        raise InstallError("host product-surface authority has unexpected fields")
    if value.get("schema_version") != 1:
        raise InstallError("host product-surface authority must use schema_version 1")
    if value.get("kind") != "rd-skills-host-product-surfaces":
        raise InstallError("host product-surface authority has an invalid kind")
    surfaces = value.get("surfaces")
    if not isinstance(surfaces, dict) or set(surfaces) != set(AGENTS):
        raise InstallError("host product-surface authority must contain every installer agent")

    expected_fields = {
        "label",
        "artifact_delivery",
        "live_skill_invocation",
        "invocation",
        "full_workflow",
        "host_enforcement_id",
        "limitation_code",
    }
    skill_hosts = {agent for agent, _scope in SOURCE_SKILL_ROOTS}
    profile_hosts = {agent for agent, _scope in SOURCE_PROFILE_ROOTS}
    enforcement_hosts = read_host_enforcement_source()["hosts"]
    enforcement_ids: set[str] = set()
    for agent in AGENTS:
        surface = surfaces[agent]
        if not isinstance(surface, dict) or set(surface) != expected_fields:
            raise InstallError(f"{agent}: product-surface fields must match schema 1")
        label = surface.get("label")
        enforcement_id = surface.get("host_enforcement_id")
        limitation_code = surface.get("limitation_code")
        if not isinstance(label, str) or not label.strip():
            raise InstallError(f"{agent}: product-surface label must be non-empty")
        if enforcement_id != agent or enforcement_id not in enforcement_hosts:
            raise InstallError(f"{agent}: host enforcement reference must match its agent")
        if enforcement_id in enforcement_ids:
            raise InstallError(f"{agent}: duplicate host enforcement reference")
        enforcement_ids.add(enforcement_id)
        if limitation_code not in PRODUCT_LIMITATION_CODES:
            raise InstallError(f"{agent}: invalid product limitation code")

        delivery = surface.get("artifact_delivery")
        live = surface.get("live_skill_invocation")
        invocation = surface.get("invocation")
        workflow = surface.get("full_workflow")
        if delivery not in PRODUCT_ARTIFACT_DELIVERY:
            raise InstallError(f"{agent}: invalid artifact delivery class")
        if live not in PRODUCT_LIVE_SKILL_INVOCATION:
            raise InstallError(f"{agent}: invalid live Skill invocation status")
        if workflow not in PRODUCT_FULL_WORKFLOW:
            raise InstallError(f"{agent}: invalid full workflow status")
        if live == "supported":
            if not isinstance(invocation, str) or not invocation.strip():
                raise InstallError(f"{agent}: supported live invocation requires syntax")
        elif invocation is not None:
            raise InstallError(f"{agent}: invocation syntax requires supported live loading")
        if (
            live == "supported"
            and enforcement_hosts[enforcement_id]["skill_loading"] == "unsupported"
        ):
            raise InstallError(f"{agent}: live invocation exceeds host skill-loading ceiling")

        has_skills = agent in skill_hosts
        has_profiles = agent in profile_hosts
        expected_delivery = (
            "zip-packages"
            if agent == "openai-api"
            else "skills-and-agent-profiles"
            if has_profiles
            else "skills-only"
        )
        if delivery != expected_delivery or (agent != "openai-api" and not has_skills):
            raise InstallError(f"{agent}: artifact delivery conflicts with installer sources")
        if agent == "openai-api" and (has_skills or has_profiles):
            raise InstallError("openai-api: package delivery must not have install sources")
        if workflow == "available" and (live != "supported" or not has_profiles):
            raise InstallError(
                f"{agent}: full workflow requires Agent Profile delivery and live invocation"
            )
        if agent == "openai-api" and workflow != "integration-owned":
            raise InstallError("openai-api: workflow must remain integration-owned")
        if agent != "openai-api" and workflow == "integration-owned":
            raise InstallError(f"{agent}: integration-owned workflow is API-only")
        expected_limit = (
            "api-integration-only"
            if workflow == "integration-owned"
            else "artifact-delivery-only"
            if workflow == "not-established"
            else "copilot-cli-only"
            if agent == "copilot"
            else "artifact-health-only"
        )
        if limitation_code != expected_limit:
            raise InstallError(f"{agent}: product limitation conflicts with surface status")
    if enforcement_ids != set(enforcement_hosts):
        raise InstallError("host product surfaces must map every enforcement host exactly once")
    return value


def host_product_surface_for_agent(agent: str) -> dict[str, Any]:
    if agent not in AGENTS:
        raise InstallError(f"unsupported agent {agent!r}")
    return dict(read_host_product_surfaces()["surfaces"][agent])


def product_next_step_lines(agent: str) -> tuple[str, ...]:
    """Project a truthful successful follow-up from the structured authority."""

    surface = host_product_surface_for_agent(agent)
    workflow = surface["full_workflow"]
    if workflow == "available":
        return (
            f"Open or restart {surface['label']}.",
            f"Start with {surface['invocation']} and describe the task in natural language.",
            f"The full rd-skills workflow is available on {surface['label']}.",
        )
    if workflow == "not-established":
        return (
            f"Installed {surface['label']} Skill artifacts are healthy.",
            f"For {surface['label']}, live Skill invocation and the full rd-skills "
            "workflow are not established.",
        )
    if workflow == "integration-owned":
        return (
            "The rd-skills packages were generated and verified.",
            "Use them through your OpenAI API integration.",
        )
    raise InstallError(f"{agent}: unsupported full workflow status")


def _manifest_names(
    manifest: dict[str, Any] | None,
    field: str,
    validator: Any,
) -> set[str]:
    if not manifest:
        return set()
    values = manifest.get(field)
    if values is None:
        return set()
    if not isinstance(values, list):
        raise InstallError(f"install manifest field {field} must be a list")
    names: set[str] = set()
    for value in values:
        if not isinstance(value, str) or not validator(value):
            raise InstallError(f"install manifest field {field} contains unsafe name {value!r}")
        if value in names:
            raise InstallError(f"install manifest field {field} contains duplicate name {value!r}")
        names.add(value)
    return names


def _valid_skill_name(value: str) -> bool:
    return bool(SKILL_NAME_RE.fullmatch(value)) and Path(value).name == value


def _valid_profile_file_name(value: str) -> bool:
    path = Path(value)
    if value.endswith(".agent.md"):
        profile_name = value.removesuffix(".agent.md")
    elif path.suffix in {".toml", ".md"}:
        profile_name = path.stem
    else:
        return False
    return (
        path.name == value
        and profile_name in AGENT_PROFILE_NAMES
    )


def managed_skill_names(manifest: dict[str, Any] | None) -> set[str]:
    return _manifest_names(manifest, "installed_skills", _valid_skill_name)


def managed_profile_files(manifest: dict[str, Any] | None) -> set[str]:
    return _manifest_names(manifest, "installed_agent_profile_files", _valid_profile_file_name)


def _profile_skill_inventories(layers: dict[str, set[str]]) -> dict[str, set[str]]:
    return {
        "recommended": layers["control"] | layers["professional"],
        "full": layers["control"] | layers["professional"] | layers["domain"],
        "dev": set().union(*layers.values()),
    }


def _inventory_sha256(names: set[str]) -> str:
    payload = "".join(f"{name}\n" for name in sorted(names)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _authoritative_current_skill_inventories() -> dict[str, Any]:
    """Return the current exact ownership sets from the build-owned registries."""

    module = _load_current_build_authority()
    try:
        registries = module._load_registries()
    except Exception as exc:
        raise InstallError(f"cannot load authoritative Skill registries: {exc}") from exc
    expected_counts = {
        "control": 1,
        "professional": 25,
        "foundation": 150,
        "domain": 13,
    }
    layers: dict[str, set[str]] = {}
    all_names: set[str] = set()
    for layer, expected_count in expected_counts.items():
        entries = registries.get(layer)
        if not isinstance(entries, list):
            raise InstallError(f"authoritative {layer} registry is unavailable")
        names: list[str] = []
        for entry in entries:
            name = entry.get("name") if isinstance(entry, dict) else None
            if not isinstance(name, str) or not _valid_skill_name(name):
                raise InstallError(f"authoritative {layer} registry has an unsafe Skill name")
            names.append(name)
        layer_names = set(names)
        if len(names) != expected_count or len(layer_names) != expected_count:
            raise InstallError(
                f"authoritative {layer} registry must contain exactly "
                f"{expected_count} unique Skills"
            )
        overlap = all_names & layer_names
        if overlap:
            raise InstallError(
                "authoritative Skill registries contain duplicate ownership: "
                + ", ".join(sorted(overlap))
            )
        all_names |= layer_names
        layers[layer] = layer_names
    profiles = {
        RUNTIME_PROFILE: layers["control"] | layers["professional"],
    }
    if {
        profile: len(names) for profile, names in profiles.items()
    } != CURRENT_RUNTIME_PROFILE_COUNTS:
        raise InstallError("authoritative current Skill inventories have invalid counts")
    return {"layers": layers, "profiles": profiles}


def _historical_runtime_27_skill_inventories(
    current_layers: dict[str, set[str]],
) -> dict[str, Any]:
    """Return the closed 27-Skill predecessor generation without Git history.

    Control, Foundation, and Domain were unchanged in the 27-to-26 transition.
    Their exact sorted-name fingerprints bind that fact and fail closed if a
    future Registry generation drifts. The historical Professional set is
    explicit because it owns the retired top-level Skill.
    """

    for layer, expected_digest in HISTORICAL_UNCHANGED_LAYER_SHA256.items():
        observed = current_layers.get(layer)
        if not isinstance(observed, set) or _inventory_sha256(observed) != expected_digest:
            raise InstallError(
                "historical Runtime inventory bridge is stale for "
                f"the {layer} Registry"
            )
    layers = {
        "control": set(current_layers["control"]),
        "professional": set(HISTORICAL_RUNTIME_27_PROFESSIONAL_SKILLS),
        "foundation": set(current_layers["foundation"]),
        "domain": set(current_layers["domain"]),
    }
    profiles = _profile_skill_inventories(layers)
    if {
        profile: len(names) for profile, names in profiles.items()
    } != HISTORICAL_PROFILE_COUNTS:
        raise InstallError("historical Runtime inventory bridge has invalid counts")
    return {"layers": layers, "profiles": profiles}


def _expected_manifest_inventory_fields(
    layers: dict[str, set[str]],
    profiles: dict[str, set[str]],
    profile: str,
) -> dict[str, set[str]]:
    return {
        "installed_skills": profiles[profile],
        "installed_control_skills": layers["control"],
        "installed_professional_skills": layers["professional"],
        "installed_foundation_skills": (
            layers["foundation"] if profile == "dev" else set()
        ),
        "installed_domain_skills": (
            layers["domain"] if profile in {"full", "dev"} else set()
        ),
    }


def _manifest_role_names(manifest: dict[str, Any]) -> set[str]:
    return _manifest_names(
        manifest,
        "installed_agent_profiles",
        lambda value: value in AGENT_PROFILE_NAMES,
    )


def expected_agent_profile_files(agent: str) -> set[str]:
    extension = {
        "codex": ".toml",
        "claude": ".md",
        "copilot": ".agent.md",
    }.get(agent)
    if extension is None:
        return set()
    return {f"{role}{extension}" for role in AGENT_PROFILE_NAMES}


def classify_installed_manifest(
    manifest: dict[str, Any],
    *,
    agent: str,
    scope: str,
    targets: InstallTargets,
) -> InstalledManifestClassification:
    """Validate exact current/legacy ownership before any managed deletion."""

    if manifest.get("architecture") != "hookless-control-plane-v1":
        raise InstallError("installed manifest is not hookless-control-plane-v1")
    if manifest.get("compiled_layer3_format") != COMPILED_LAYER3_FORMAT:
        raise InstallError(
            f"installed manifest compiled_layer3_format must equal {COMPILED_LAYER3_FORMAT!r}"
        )
    profile = manifest.get("profile")
    if not isinstance(profile, str) or profile not in HISTORICAL_PROFILE_COUNTS:
        raise InstallError(f"installed manifest has unsupported profile identity {profile!r}")
    if manifest.get("agent") != agent:
        raise InstallError("installed manifest agent does not match the requested agent")
    if manifest.get("scope") != scope:
        raise InstallError("installed manifest scope does not match the requested scope")
    if manifest.get("target_path") != str(targets.skills):
        raise InstallError("installed manifest target_path does not match the resolved target")
    expected_profile_target = (
        str(targets.profiles) if targets.profiles is not None else None
    )
    if manifest.get("agent_profile_target") != expected_profile_target:
        raise InstallError(
            "installed manifest agent_profile_target does not match the resolved target"
        )

    authority = _authoritative_current_skill_inventories()
    current_layers = authority["layers"]
    current_profiles = authority["profiles"]
    if not isinstance(current_layers, dict) or not isinstance(current_profiles, dict):
        raise InstallError("authoritative current Skill inventories are malformed")
    inventory_fields = (
        "installed_skills",
        "installed_control_skills",
        "installed_professional_skills",
        "installed_foundation_skills",
        "installed_domain_skills",
    )
    observed_fields = {
        field: _manifest_names(manifest, field, _valid_skill_name)
        for field in inventory_fields
    }
    current_fields = (
        _expected_manifest_inventory_fields(
            current_layers,
            current_profiles,
            profile,
        )
        if profile == RUNTIME_PROFILE
        else None
    )
    if current_fields is not None and observed_fields == current_fields:
        generation = CURRENT_INVENTORY_GENERATION
        expected_skills = current_profiles[profile]
    else:
        historical = _historical_runtime_27_skill_inventories(current_layers)
        historical_layers = historical["layers"]
        historical_profiles = historical["profiles"]
        if not isinstance(historical_layers, dict) or not isinstance(
            historical_profiles, dict
        ):
            raise InstallError("historical Runtime inventory bridge is malformed")
        historical_fields = _expected_manifest_inventory_fields(
            historical_layers,
            historical_profiles,
            profile,
        )
        if observed_fields != historical_fields:
            raise InstallError(
                "installed manifest inventory fields do not match one exact "
                f"supported {profile} generation"
            )
        generation = HISTORICAL_INVENTORY_GENERATION
        expected_skills = historical_profiles[profile]

    expected_profile_files = expected_agent_profile_files(agent)
    observed_profile_files = managed_profile_files(manifest)
    if observed_profile_files != expected_profile_files:
        raise InstallError(
            "installed manifest Agent Profile files are not the exact managed host set"
        )
    expected_roles = set(AGENT_PROFILE_NAMES) if expected_profile_files else set()
    if _manifest_role_names(manifest) != expected_roles:
        raise InstallError(
            "installed manifest Agent Profiles are not the exact four-role host set"
        )
    return InstalledManifestClassification(
        profile=profile,
        inventory_generation=generation,
        skill_names=frozenset(expected_skills),
        profile_files=frozenset(expected_profile_files),
    )


def validate_managed_artifact_paths(
    targets: InstallTargets,
    skill_names: set[str],
    profile_files: set[str],
) -> None:
    """Reject link traversal and path-shape failures before backup or deletion."""

    _reject_symlink(targets.skills, "managed Skill root")
    if targets.skills.exists() and not targets.skills.is_dir():
        raise InstallError(f"managed Skill root is not a directory: {targets.skills}")
    if targets.profiles is not None:
        _reject_symlink(targets.profiles, "managed Agent Profile root")
        if targets.profiles.exists() and not targets.profiles.is_dir():
            raise InstallError(
                f"managed Agent Profile root is not a directory: {targets.profiles}"
            )
    for name in sorted(skill_names):
        path = _safe_child(targets.skills, name)
        _reject_symlink(path, "managed Skill")
        if not path.exists():
            continue
        if not path.is_dir():
            raise InstallError(f"managed Skill path is not a directory: {path}")
        try:
            nested_link = next(
                (candidate for candidate in path.rglob("*") if candidate.is_symlink()),
                None,
            )
        except OSError as exc:
            raise InstallError(f"cannot inspect managed Skill path {path}: {exc}") from exc
        if nested_link is not None:
            raise InstallError(
                f"managed Skill directory cannot contain symlinks: {nested_link}"
            )
    if targets.profiles is not None:
        for name in sorted(profile_files):
            path = _safe_child(targets.profiles, name, profile=True)
            _reject_symlink(path, "managed Agent Profile")
            if path.exists() and not path.is_file():
                raise InstallError(
                    f"managed Agent Profile path is not a file: {path}"
                )


def _safe_child(root: Path, name: str, *, profile: bool = False) -> Path:
    valid = _valid_profile_file_name(name) if profile else _valid_skill_name(name)
    if not valid:
        raise InstallError(f"unsafe managed artifact name {name!r}")
    return root / name


def find_unmanaged_conflicts(target: Path, names: set[str], managed: set[str]) -> list[str]:
    conflicts: list[str] = []
    for name in names:
        if Path(name).name != name or name in {".", ".."}:
            raise InstallError(f"unsafe artifact name {name!r}")
        if _path_lexists(target / name) and name not in managed:
            conflicts.append(name)
    return sorted(conflicts)


def backup_existing(
    targets: InstallTargets,
    skill_names: set[str],
    profile_names: set[str],
    action: str,
    dry_run: bool,
    extra_paths: list[Path] | None = None,
) -> Path | None:
    validate_managed_artifact_paths(targets, skill_names, profile_names)
    existing_skills = [
        path for name in sorted(skill_names)
        if _path_lexists(path := _safe_child(targets.skills, name))
    ]
    existing_profiles = []
    if targets.profiles is not None:
        existing_profiles = [
            path for name in sorted(profile_names)
            if _path_lexists(path := _safe_child(targets.profiles, name, profile=True))
        ]
    manifest = targets.skills / MANIFEST_NAME
    if _path_lexists(manifest):
        existing_skills.append(manifest)
    extras = [path for path in (extra_paths or []) if _path_lexists(path)]
    if not existing_skills and not existing_profiles and not extras:
        return None

    for path in existing_skills:
        _reject_symlink(path, "managed backup source")
    for path in existing_profiles:
        _reject_symlink(path, "managed Profile backup source")
    for path in extras:
        _reject_symlink(path, "legacy backup source")

    backup_root = targets.skills / BACKUP_DIR_NAME
    _reject_symlink(backup_root, "backup root")
    backup = backup_root / f"{action}-{utc_stamp()}"
    _ensure_parent_within(backup, [targets.skills], "backup")
    if _path_lexists(backup):
        raise InstallError(f"backup destination already exists: {backup}")
    if dry_run:
        return backup
    try:
        (backup / "skills").mkdir(parents=True, exist_ok=False)
        for path in existing_skills:
            destination = backup / "skills" / path.name
            if path.is_dir():
                shutil.copytree(path, destination)
            else:
                shutil.copy2(path, destination)
        if existing_profiles:
            (backup / "profiles").mkdir(parents=True)
            for path in existing_profiles:
                shutil.copy2(path, backup / "profiles" / path.name)
        if extras:
            (backup / "legacy").mkdir(parents=True)
            seen: set[Path] = set()
            for index, path in enumerate(extras, start=1):
                resolved = path.resolve()
                if resolved in seen:
                    continue
                seen.add(resolved)
                destination = backup / "legacy" / f"{index:03d}-{path.name}"
                if path.is_dir():
                    shutil.copytree(path, destination)
                else:
                    shutil.copy2(path, destination)
    except (OSError, shutil.Error) as exc:
        cleanup_error: OSError | None = None
        try:
            if backup.is_dir() and not backup.is_symlink():
                shutil.rmtree(backup)
            if (
                backup_root.is_dir()
                and not backup_root.is_symlink()
                and not any(backup_root.iterdir())
            ):
                backup_root.rmdir()
        except OSError as cleanup_exc:
            cleanup_error = cleanup_exc
        detail = f"; partial backup cleanup also failed: {cleanup_error}" if cleanup_error else ""
        raise InstallError(f"cannot create complete backup {backup}: {exc}{detail}") from exc
    return backup


def replace_skills(source: Path, target: Path, remove_names: set[str], dry_run: bool) -> None:
    if dry_run:
        return
    target.mkdir(parents=True, exist_ok=True)
    for name in sorted(remove_names):
        path = _safe_child(target, name)
        if path.is_symlink():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            raise InstallError(f"managed Skill path is not a directory: {path}")
    for source_dir in list_skill_dirs(source):
        shutil.copytree(source_dir, target / source_dir.name)


def replace_profiles(
    source: Path | None,
    target: Path | None,
    remove_names: set[str],
    dry_run: bool,
) -> list[str]:
    if source is not None:
        _reject_symlink(source, "built Agent Profile root")
    source_files = list_profile_files(source)
    if not source_files or target is None:
        return []
    for source_file in source_files:
        _reject_symlink(source_file, "built Agent Profile source")
    if not dry_run:
        target.mkdir(parents=True, exist_ok=True)
        for name in sorted(remove_names):
            path = _safe_child(target, name, profile=True)
            if path.is_symlink():
                path.unlink()
            elif path.exists() and path.is_file():
                path.unlink()
            elif path.exists():
                raise InstallError(f"managed Agent Profile path is not a file: {path}")
        for source_file in source_files:
            destination = _safe_child(target, source_file.name, profile=True)
            if _path_lexists(destination):
                raise InstallError(f"Agent Profile destination was not cleared: {destination}")
            shutil.copy2(source_file, destination)
            if hashlib.sha256(source_file.read_bytes()).digest() != hashlib.sha256(destination.read_bytes()).digest():
                raise InstallError(f"installed Agent Profile digest mismatch: {destination}")
    return [path.name for path in source_files]


def make_manifest(
    *,
    agent: str,
    scope: str,
    targets: InstallTargets,
    source_dir: Path,
    profile_files: list[str],
    backup_path: Path | None,
) -> dict[str, Any]:
    build = read_build_manifest(source_dir)
    validate_build_core_model(build)
    installed = [path.name for path in list_skill_dirs(source_dir)]
    installed_set = set(installed)
    def present(key: str) -> list[str]:
        values = build.get(key)
        return sorted(str(value) for value in values or [] if str(value) in installed_set)
    return {
        "architecture": "hookless-control-plane-v1",
        "compiled_layer3_format": str(build["compiled_layer3_format"]),
        "install_time": utc_iso(),
        "source_version": str(build.get("source_version", source_version())),
        "agent": agent,
        "scope": scope,
        "profile": RUNTIME_PROFILE,
        "target_path": str(targets.skills),
        "agent_profile_target": str(targets.profiles) if targets.profiles is not None else None,
        "installed_skills": sorted(installed),
        "installed_control_skills": present("control_skills"),
        "installed_professional_skills": present("professional_skills"),
        "installed_foundation_skills": present("foundation_skills"),
        "installed_domain_skills": present("domain_skills"),
        "installed_agent_profiles": list(AGENT_PROFILE_NAMES) if profile_files else [],
        "installed_agent_profile_files": sorted(profile_files),
        "installed_agent_profile_sha256": (
            dict(build.get("agent_profile_sha256", {}).get(agent, {}))
            if profile_files
            else {}
        ),
        "installed_agent_profile_enforcement": build["agent_profile_enforcement"][agent],
        "agent_profile_enforcement_source": build["agent_profile_enforcement_source"],
        "core_model": dict(build["core_model"]),
        "foundation_mode": build.get("foundation_mode"),
        "backup_path": str(backup_path) if backup_path is not None else None,
    }


def version_changes(old: dict[str, Any] | None, new: dict[str, Any]) -> dict[str, list[str]]:
    old_names = managed_skill_names(old)
    new_names = managed_skill_names(new)
    return {
        "added": sorted(new_names - old_names),
        "removed": sorted(old_names - new_names),
        "changed": sorted(old_names & new_names) if old and old.get("source_version") != new.get("source_version") else [],
    }


def remove_installed(
    targets: InstallTargets,
    skill_names: set[str],
    profile_files: set[str],
    dry_run: bool,
) -> None:
    if dry_run:
        return
    for name in sorted(skill_names):
        path = _safe_child(targets.skills, name)
        if path.is_symlink():
            path.unlink()
        elif path.exists() and path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            raise InstallError(f"managed Skill path is not a directory: {path}")
    if targets.profiles is not None:
        for name in sorted(profile_files):
            path = _safe_child(targets.profiles, name, profile=True)
            if path.is_symlink():
                path.unlink()
            elif path.exists() and path.is_file():
                path.unlink()
            elif path.exists():
                raise InstallError(f"managed Agent Profile path is not a file: {path}")
    manifest = targets.skills / MANIFEST_NAME
    if manifest.is_symlink() or manifest.is_file():
        manifest.unlink()
    elif manifest.exists():
        raise InstallError(f"managed install manifest is not a file: {manifest}")


def cleanup_legacy_residue(
    agent: str,
    scope: str,
    project_target: Path | None,
    skill_target: Path,
    dry_run: bool,
) -> list[Path]:
    """Remove only known artifacts from pre-hookless releases."""
    candidates = _legacy_removal_candidates(agent, scope, project_target, skill_target)
    config_root = _legacy_config_root(agent, scope, project_target)
    shared_config = config_root / "hooks.json" if config_root is not None and agent == "codex" else None
    config_changes = bool(shared_config is not None and _has_changeforge_hook_command(shared_config))
    existing = [path for path in candidates if _path_lexists(path)]
    reported = [*existing, *([shared_config] if config_changes and shared_config is not None else [])]
    if dry_run:
        return reported
    for path in sorted(existing, key=lambda value: len(value.parts), reverse=True):
        if not _path_lexists(path):
            continue
        if path.is_symlink():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    if config_changes and shared_config is not None:
        _remove_changeforge_commands(shared_config)
    _prune_empty_legacy_directories(agent, scope, project_target, config_root)
    return reported


def _legacy_removal_candidates(
    agent: str,
    scope: str,
    project_target: Path | None,
    skill_target: Path,
) -> list[Path]:
    candidates = [skill_target / ".changeforge-packs", skill_target / ".changeforge-control"]
    config_root = _legacy_config_root(agent, scope, project_target)
    boundaries = _legacy_boundaries(scope, project_target, skill_target, config_root)
    if config_root is not None:
        candidates.extend(_legacy_files_under_config(agent, config_root, boundaries))
    if scope == "project" and project_target is not None:
        project = project_target.expanduser().resolve()
        candidates.extend(
            [
                project / ".changeforge" / "changeforge-route-preflight.md",
                project / ".changeforge" / "changeforge-professional-contract.md",
            ]
        )
        if agent == "copilot":
            instructions = project / ".github" / "copilot-instructions.md"
            _ensure_parent_within(instructions, boundaries, "legacy Copilot instructions")
            if _is_legacy_copilot_instructions(instructions):
                candidates.append(instructions)
    unique = list(dict.fromkeys(candidates))
    for path in unique:
        _ensure_parent_within(path, boundaries, "legacy pre-hookless artifact")
    return unique


def _legacy_boundaries(
    scope: str,
    project_target: Path | None,
    skill_target: Path,
    config_root: Path | None,
) -> list[Path]:
    if scope == "project" and project_target is not None:
        return [project_target.expanduser().resolve(strict=False)]
    boundaries = [skill_target]
    if config_root is not None:
        boundaries.append(config_root)
    return boundaries


def _legacy_config_root(agent: str, scope: str, target: Path | None) -> Path | None:
    if agent not in {"codex", "claude", "copilot"}:
        return None
    subdir = {"codex": ".codex", "claude": ".claude", "copilot": ".copilot"}[agent]
    if scope == "project":
        if target is None:
            return None
        if agent == "copilot":
            return target.expanduser().resolve() / ".github"
        return target.expanduser().resolve() / subdir
    if scope == "user":
        return Path.home() / subdir
    return None


def _legacy_files_under_config(
    agent: str,
    root: Path,
    boundaries: list[Path],
) -> list[Path]:
    candidates = [
        root / ".changeforge-hook-manifest.json",
        root / "changeforge-route-preflight.md",
        root / "changeforge-professional-contract.md",
        root / "settings.changeforge-hooks.fragment.json",
        root / "hooks" / "changeforge-hooks.json",
    ]
    scripts = root / "hooks"
    if scripts.is_dir():
        candidates.extend(scripts / name for name in LEGACY_HOOK_SCRIPT_NAMES)
        candidates.extend(scripts / name for name in LEGACY_SUPPORT_FILES)
        candidates.extend(scripts / name for name in LEGACY_SUPPORT_DIRECTORIES)
    if agent == "copilot":
        candidates.append(root / "hooks" / "changeforge")
    profiles = root / "agents"
    extension = ".toml" if agent == "codex" else ".md"
    candidates.extend(
        path
        for name in LEGACY_PROFILE_NAMES
        if _is_legacy_agent_profile(path := profiles / f"{name}{extension}")
    )
    main_profile = profiles / f"main-control-agent{extension}"
    if agent == "copilot":
        # Pre-Hookless and early Hookless builds used plain .md names here.
        # The current Copilot projection uses .agent.md, so these exact reserved
        # names are legacy even when their leaf is a dangling symlink.
        candidates.extend(
            path
            for name in AGENT_PROFILE_NAMES
            if _is_legacy_agent_profile(path := profiles / f"{name}.md")
        )
        old_project_profiles = root / "copilot" / "agents"
        candidates.extend(
            path
            for name in (*LEGACY_PROFILE_NAMES, *AGENT_PROFILE_NAMES)
            if _is_legacy_agent_profile(
                path := old_project_profiles / f"{name}.md"
            )
        )
    else:
        _ensure_parent_within(main_profile, boundaries, "legacy main Agent Profile")
        if _is_legacy_main_profile(main_profile):
            candidates.append(main_profile)
    return candidates


def legacy_managed_profile_files(
    agent: str,
    scope: str,
    project_target: Path | None,
) -> set[str]:
    config_root = _legacy_config_root(agent, scope, project_target)
    if config_root is None:
        return set()
    extension = ".toml" if agent == "codex" else ".md"
    candidate = config_root / "agents" / f"main-control-agent{extension}"
    boundaries = (
        [project_target.expanduser().resolve(strict=False)]
        if scope == "project" and project_target is not None
        else [config_root]
    )
    _ensure_parent_within(candidate, boundaries, "legacy managed Agent Profile")
    return {candidate.name} if _is_legacy_main_profile(candidate) else set()


def _is_legacy_main_profile(path: Path) -> bool:
    if path.is_symlink():
        return False
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    return "runtime-backed evidence" in text and "Analysis Worker" in text


def _is_legacy_agent_profile(path: Path) -> bool:
    if path.is_symlink() or not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    markers = (
        "ChangeForge",
        "change-forge-router",
        "phase_artifact",
        "runtime-backed evidence",
        "Declared tool boundary:",
        "Analysis Worker",
        "Specialist Worker",
        "Independent Reviewer",
        "Contract_ref:",
    )
    return any(marker in text for marker in markers)


def _is_legacy_copilot_instructions(path: Path) -> bool:
    if path.is_symlink():
        return False
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    return (
        "# ChangeForge Copilot Professional Contract" in text
        and "change-forge-router" in text
        and "dispatch_unavailable" in text
    )


def _has_changeforge_hook_command(path: Path) -> bool:
    data = load_json(path)
    if data is None:
        return False
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return False
    for groups in hooks.values():
        if not isinstance(groups, list):
            continue
        for group in groups:
            if not isinstance(group, dict):
                continue
            items = group.get("hooks")
            if isinstance(items, list) and any(_is_changeforge_hook_item(item) for item in items):
                return True
    return False


def _is_changeforge_hook_item(item: Any) -> bool:
    if not isinstance(item, dict) or not isinstance(item.get("command"), str):
        return False
    names = CHANGEFORGE_HOOK_COMMAND_RE.findall(item["command"])
    return any(name in LEGACY_HOOK_SCRIPT_NAMES for name in names)


def _remove_changeforge_commands(path: Path) -> None:
    data = load_json(path)
    if data is None:
        return
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return
    changed = False
    for event, groups in list(hooks.items()):
        if not isinstance(groups, list):
            continue
        kept_groups = []
        for group in groups:
            if not isinstance(group, dict):
                kept_groups.append(group)
                continue
            commands = group.get("hooks")
            if not isinstance(commands, list):
                kept_groups.append(group)
                continue
            kept = [item for item in commands if not _is_changeforge_hook_item(item)]
            if len(kept) != len(commands):
                changed = True
            if kept:
                updated = dict(group)
                updated["hooks"] = kept
                kept_groups.append(updated)
        hooks[event] = kept_groups
    if changed:
        write_json(path, data)


def legacy_residue_paths(agent: str, scope: str, project_target: Path | None, skill_target: Path) -> list[Path]:
    paths = _legacy_removal_candidates(agent, scope, project_target, skill_target)
    config_root = _legacy_config_root(agent, scope, project_target)
    if config_root is not None:
        extension = {
            "codex": ".toml",
            "claude": ".md",
            "copilot": ".agent.md",
        }.get(agent)
        if extension is not None:
            paths.extend(
                path
                for name in AGENT_PROFILE_NAMES
                if (path := config_root / "agents" / f"{name}{extension}").is_symlink()
            )
    if config_root is not None and agent == "codex":
        config = config_root / "hooks.json"
        if _has_changeforge_hook_command(config):
            paths.append(config)
    return [path for path in paths if _path_lexists(path)]


def _prune_empty_legacy_directories(
    agent: str,
    scope: str,
    project_target: Path | None,
    config_root: Path | None,
) -> None:
    candidates: list[Path] = []
    if scope == "project" and project_target is not None:
        project = project_target.expanduser().resolve()
        candidates.append(project / ".changeforge")
        if agent == "copilot":
            candidates.extend([project / ".github" / "copilot" / "agents", project / ".github" / "copilot"])
    if config_root is not None:
        candidates.extend([config_root / "hooks", config_root / "agents"])
    for path in candidates:
        if path.is_symlink():
            continue
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()
