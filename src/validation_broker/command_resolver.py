"""Resolve validation commands from changed paths and risk surfaces."""

from __future__ import annotations

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
    context_candidates = _context_validation_candidates(repo_context)
    skill_behavior_change = classify_skill_behavior_change(paths)

    recommended = commands_for_categories(categories, level="narrow")
    full = commands_for_categories(categories, level="full")
    if not categories:
        recommended = [UNKNOWN_COMMANDS[0]]
        full = [UNKNOWN_COMMANDS[1]]

    recommended = _merge_commands(recommended, context_candidates)
    return {
        "schema_version": 1,
        "changed_paths": paths,
        "risk_surfaces": surfaces,
        "stage": str(stage or "").strip(),
        "matched_categories": categories or ["unknown"],
        "recommended_commands": [command.to_dict() for command in recommended],
        "full_commands": [command.to_dict() for command in _dedupe(full)],
        "conservative": not bool(categories),
        "unknown_paths": _unknown_paths(paths, categories),
        "skill_behavior_change": skill_behavior_change,
        "notes": _plan_notes(paths, surfaces, categories, stage, skill_behavior_change),
    }


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


def _unknown_paths(paths: list[str], categories: list[str]) -> list[str]:
    unknown: list[str] = []
    for path in paths:
        if not matching_categories([path]):
            unknown.append(path)
    if unknown:
        return unknown
    return [] if categories else paths[:]


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
