"""Resolve validation commands from changed paths and risk surfaces."""

from __future__ import annotations

from typing import Iterable

from .command_registry import (
    UNKNOWN_COMMANDS,
    ValidationCommand,
    commands_for_categories,
    matching_categories,
)


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
        "notes": _plan_notes(paths, surfaces, categories, stage),
    }


def _context_validation_candidates(repo_context: dict | None) -> list[ValidationCommand]:
    if not isinstance(repo_context, dict):
        return []
    pack = repo_context.get("task_context_pack")
    if not isinstance(pack, dict):
        return []
    result: list[ValidationCommand] = []
    for item in pack.get("validation_candidates", []) or []:
        if not isinstance(item, dict):
            continue
        command = str(item.get("command", "")).strip()
        proves = str(item.get("proves", "")).strip()
        if not command or not proves:
            continue
        result.append(
            ValidationCommand(
                command=command,
                level="module",
                reason=f"context pack candidate: {proves}",
                category="context_pack",
                covered_path_patterns=tuple(_clean_list(pack.get("changed_paths", []))) or ("**",),
                covered_risk_surfaces=("context-pack",),
            )
        )
    return result


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
    if categories:
        return []
    return paths[:]


def _plan_notes(
    paths: list[str],
    surfaces: list[str],
    categories: list[str],
    stage: str,
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
    return notes


def _clean_list(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values or ():
        text = str(value).replace("\\", "/").strip().lstrip("./")
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result
