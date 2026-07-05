"""Resolve validation commands from changed paths and risk surfaces."""

from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path
import re
from typing import Iterable

from .command_registry import (
    UNKNOWN_COMMANDS,
    ValidationCommand,
    commands_for_categories,
    matching_categories,
)
from .skill_behavior_change import classify_skill_behavior_change


def resolve_validation_plan(
    changed_paths: Iterable[str],
    risk_surfaces: Iterable[str] = (),
    stage: str = "",
    repo_context: dict | None = None,
) -> dict[str, object]:
    """Build a deterministic validation plan for a change."""
    paths = _clean_list(changed_paths)
    surfaces = _clean_list(risk_surfaces)
    categories = matching_categories(paths)
    project_candidates, validator_config_issues = _project_validation_candidates(paths, repo_context)
    context_candidates = _context_validation_candidates(repo_context)
    skill_behavior_change = classify_skill_behavior_change(paths)

    recommended = commands_for_categories(categories, level="narrow")
    full = commands_for_categories(categories, level="full")
    if not categories:
        recommended = [UNKNOWN_COMMANDS[0]]
        full = [UNKNOWN_COMMANDS[1]]

    recommended = _merge_commands(project_candidates, _merge_commands(context_candidates, recommended))
    return {
        "schema_version": 1,
        "changed_paths": paths,
        "risk_surfaces": surfaces,
        "stage": str(stage or "").strip(),
        "matched_categories": categories or ["unknown"],
        "recommended_commands": [command.to_dict() for command in recommended],
        "full_commands": [command.to_dict() for command in _dedupe(full)],
        "conservative": not bool(categories),
        "unknown_paths": _unknown_paths(paths, categories, [*project_candidates, *context_candidates]),
        "skill_behavior_change": skill_behavior_change,
        "validator_config_issues": validator_config_issues,
        "notes": _plan_notes(paths, surfaces, categories, stage, skill_behavior_change),
    }




def _project_validation_candidates(paths: list[str], repo_context: dict | None) -> tuple[list[ValidationCommand], list[str]]:
    validators: list[dict[str, object]] = []
    issues: list[str] = []
    for config_path in _project_validators_paths(repo_context):
        if not config_path.is_file():
            continue
        parsed, parse_issues = _read_project_validators(config_path)
        validators.extend(parsed)
        issues.extend(parse_issues)
        break
    result: list[ValidationCommand] = []
    for item in validators:
        patterns = _clean_list(item.get("path_patterns", []))
        if not all(_safe_relative_path(pattern) for pattern in patterns):
            issues.append(f"validator_config_invalid_path:{item.get('id') or 'project_validator'}")
            continue
        if paths and patterns and not any(_path_matches_pattern(path, pattern) for path in paths for pattern in patterns):
            continue
        command = str(item.get("command") or "").strip()
        if not command:
            continue
        cwd = str(item.get("cwd") or "").strip().strip("./")
        if cwd and not _safe_relative_path(cwd):
            issues.append(f"validator_config_invalid_cwd:{item.get('id') or 'project_validator'}")
            continue
        display = f"cd {cwd} && {command}" if cwd and not command.startswith("cd ") else command
        scope = str(item.get("scope") or "module").strip()
        level = "full" if scope == "full" else "module" if scope in {"module", "targeted"} else "narrow"
        result.append(
            ValidationCommand(
                command=display,
                level=level,
                reason="project validator: " + ", ".join(_clean_list(item.get("proves", []))[:3]),
                category=str(item.get("id") or "project_validator"),
                covered_path_patterns=tuple(patterns or ("**",)),
                covered_risk_surfaces=tuple(
                    _clean_list(item.get("covered_risk_surfaces", []))
                    or _clean_list(item.get("proves", []))
                    or ("project-validator",)
                ),
            )
        )
    return result, issues


def _project_validators_paths(repo_context: dict | None) -> list[Path]:
    root = Path.cwd()
    if isinstance(repo_context, dict):
        for key in ("repo_root", "cwd"):
            if repo_context.get(key):
                root = Path(str(repo_context.get(key))).expanduser()
                break
    return [root / ".changeforge" / "validators.yaml", root / ".changeforge" / "validators.yml"]


def _safe_relative_path(value: object) -> bool:
    text = str(value or "").replace("\\", "/").strip()
    if not text or text.startswith("/"):
        return False
    parts = [part for part in text.split("/") if part]
    return ".." not in parts


def _read_project_validators(path: Path) -> tuple[list[dict[str, object]], list[str]]:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [], [f"validator_config_read_error:{path.name}:{exc.__class__.__name__}"]
    if "validators:" not in content:
        return [], []
    if re.search(r"validators:\s*\[[^\]]*$", content):
        return [], [f"validator_config_parse_error:{path.name}"]
    if re.search(r"^\s*(path_patterns|proves|covered_risk_surfaces):\s*\[", content, re.M):
        return [], [f"validator_config_parse_error:{path.name}"]
    validators: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    list_key = ""
    for raw_line in content.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped == "validators:":
            continue
        if stripped.startswith("- id:"):
            current = {"id": _strip_yaml_scalar(stripped.split(":", 1)[1])}
            validators.append(current)
            list_key = ""
            continue
        if current is None:
            continue
        if stripped in {"path_patterns:", "proves:", "covered_risk_surfaces:"}:
            list_key = stripped[:-1]
            current.setdefault(list_key, [])
            continue
        if stripped.startswith("- ") and list_key:
            current.setdefault(list_key, [])
            cast_list = current[list_key]
            if isinstance(cast_list, list):
                cast_list.append(_strip_yaml_scalar(stripped[2:]))
            continue
        if ":" in stripped:
            key, value = stripped.split(":", 1)
            current[key.strip()] = _strip_yaml_scalar(value)
            list_key = ""
    if not validators and content.strip():
        return [], [f"validator_config_parse_error:{path.name}"]
    return validators, []


def _strip_yaml_scalar(value: object) -> str:
    text = str(value or "").strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        return text[1:-1].strip()
    return text

def _context_validation_candidates(repo_context: dict | None) -> list[ValidationCommand]:
    if not isinstance(repo_context, dict):
        return []
    pack = _context_pack_payload(repo_context)
    if not isinstance(pack, dict):
        return []
    result: list[ValidationCommand] = []
    for item in pack.get("validation_candidates", []) or []:
        if not isinstance(item, dict):
            continue
        if _candidate_is_conservative(item):
            continue
        command = str(item.get("command", "")).strip()
        proves = str(item.get("proves", "")).strip()
        if not command or not proves:
            continue
        result.append(_validation_command_from_context_item(item, pack, proves))
    for item in pack.get("graph_validation_candidates", []) or []:
        if not isinstance(item, dict) or _candidate_is_conservative(item):
            continue
        command = str(item.get("command", "")).strip()
        proves = str(item.get("proves") or item.get("reason") or "").strip()
        if not command or not proves:
            continue
        result.append(_validation_command_from_context_item(item, pack, proves))
    return result


def _validation_command_from_context_item(
    item: dict,
    pack: dict,
    proves: str,
) -> ValidationCommand:
    level = str(item.get("scope") or item.get("level") or "module").strip()
    if level not in {"narrow", "module", "full"}:
        level = "module"
    return ValidationCommand(
        command=str(item.get("command") or "").strip(),
        level=level,
        reason=f"context pack candidate: {proves}",
        category=str(item.get("category") or "context_pack"),
        covered_path_patterns=tuple(
            _clean_list(item.get("covered_paths", []))
            or _clean_list(item.get("covered_path_patterns", []))
            or _clean_list(pack.get("changed_paths", []))
        )
        or ("**",),
        covered_risk_surfaces=tuple(_clean_list(item.get("covered_risk_surfaces", []))) or ("context-pack",),
    )


def _candidate_is_conservative(item: dict) -> bool:
    strength = str(item.get("strength") or "").strip()
    freshness = str(item.get("freshness") or "").strip()
    confidence = str(item.get("confidence") or "").strip()
    if strength == "conservative":
        return True
    if freshness in {"stale", "unknown"}:
        return True
    if confidence in {"low", "unknown"}:
        return True
    return False


def _context_pack_payload(repo_context: dict) -> dict | None:
    pack = repo_context.get("task_context_pack")
    if isinstance(pack, dict):
        return pack
    repository_context = repo_context.get("repository_context")
    if isinstance(repository_context, dict):
        nested = repository_context.get("task_context_pack")
        if isinstance(nested, dict):
            return nested
        if isinstance(repository_context.get("validation_candidates"), list):
            return repository_context
    if isinstance(repo_context.get("validation_candidates"), list):
        return repo_context
    return None


def _merge_commands(
    registry_commands: Iterable[ValidationCommand],
    context_commands: Iterable[ValidationCommand],
) -> list[ValidationCommand]:
    return _dedupe([*registry_commands, *context_commands])


def _dedupe(commands: Iterable[ValidationCommand]) -> list[ValidationCommand]:
    result: list[ValidationCommand] = []
    seen: set[str] = set()
    for command in commands:
        key = " ".join(command.command.split())
        if key in seen:
            continue
        seen.add(key)
        result.append(command)
    return result


def _unknown_paths(paths: list[str], categories: list[str], candidate_commands: list[ValidationCommand] | None = None) -> list[str]:
    unknown: list[str] = []
    covered_patterns: list[str] = []
    project_covered_patterns: list[str] = []
    for command in candidate_commands or []:
        patterns = [str(item) for item in command.covered_path_patterns]
        covered_patterns.extend(patterns)
        if command.category != "context_pack":
            project_covered_patterns.extend(patterns)
    for path in paths:
        if not matching_categories([path]) and not any(_path_matches_pattern(path, pattern) for pattern in covered_patterns):
            unknown.append(path)
    if unknown:
        return unknown
    if project_covered_patterns and all(
        any(_path_matches_pattern(path, pattern) for pattern in project_covered_patterns)
        for path in paths
    ):
        return []
    return [] if categories else paths[:]


def _path_matches_pattern(path: str, pattern: str) -> bool:
    clean_path = str(path or "").strip().strip("./")
    clean_pattern = str(pattern or "").strip().strip("./")
    if not clean_path or not clean_pattern:
        return False
    if clean_pattern == "**":
        return True
    if clean_pattern.endswith("/**"):
        prefix = clean_pattern[:-3].rstrip("/")
        return clean_path == prefix or clean_path.startswith(prefix + "/")
    return fnmatch(clean_path, clean_pattern)


def _plan_notes(
    paths: list[str],
    surfaces: list[str],
    categories: list[str],
    stage: str,
    skill_behavior_change: dict[str, object] | None = None,
) -> list[str]:
    notes: list[str] = []
    if not paths:
        notes.append("no changed paths supplied; recommendations are conservative")
    if not categories:
        notes.append("unknown coverage must be explained; it is not a pass")
    if surfaces:
        notes.append("risk surfaces must be covered by the selected command or called out as residual risk")
    if stage:
        notes.append(f"stage={stage}; use narrow commands for local proof and full commands before release handoff")
    if (
        isinstance(skill_behavior_change, dict)
        and skill_behavior_change.get("requires_skill_efficacy_benchmark") is True
    ):
        notes.append(
            "skill behavior change requires a skill_efficacy_benchmark plan; missing benchmark evidence is not closure evidence"
        )
    return notes


def _clean_list(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    if isinstance(values, str):
        values = (values,)
    for value in values or ():
        text = str(value).replace("\\", "/").strip().lstrip("./")
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result
