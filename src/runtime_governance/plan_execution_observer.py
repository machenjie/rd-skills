"""Bounded observations for plan execution advisory checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .visible_plan_parser import canonicalize_plan_path


@dataclass(frozen=True)
class PlanExecutionObservation:
    """A bounded, source-agnostic view of one execution handoff."""

    current_task: str = ""
    planned_files: tuple[str, ...] = ()
    changed_files: tuple[str, ...] = ()
    validation_commands: tuple[str, ...] = ()
    validation_fresh_after_last_edit: bool | None = None
    review_text: str = ""
    repair_text: str = ""
    rereview_text: str = ""
    final_handoff: str = ""
    user_gate_text: str = ""


def observation_from_mapping(data: dict[str, Any] | None) -> PlanExecutionObservation:
    """Normalize a fixture or hook-derived mapping into bounded observation fields."""

    source = data if isinstance(data, dict) else {}
    return PlanExecutionObservation(
        current_task=_string(source.get("current_task")),
        planned_files=_path_strings(source.get("planned_files")),
        changed_files=_path_strings(source.get("changed_files")),
        validation_commands=_strings(source.get("validation_commands")),
        validation_fresh_after_last_edit=_optional_bool(source.get("validation_fresh_after_last_edit")),
        review_text=_string(source.get("review_text")),
        repair_text=_string(source.get("repair_text")),
        rereview_text=_string(source.get("rereview_text")),
        final_handoff=_string(source.get("final_handoff")),
        user_gate_text=_string(source.get("user_gate_text")),
    )


def _strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    result = []
    for item in value:
        text = _string(item)
        if text:
            result.append(text)
    return tuple(result[:50])


def _path_strings(value: object) -> tuple[str, ...]:
    result: list[str] = []
    for item in _strings(value):
        path = canonicalize_plan_path(item)
        if path:
            result.append(path)
    return tuple(dict.fromkeys(result[:50]))


def _string(value: object) -> str:
    return str(value).strip() if value is not None else ""


def _optional_bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in {"true", "yes", "fresh", "current"}:
            return True
        if normalized in {"false", "no", "stale"}:
            return False
    return None
