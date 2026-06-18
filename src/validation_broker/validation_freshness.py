"""Freshness checks for validation evidence."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable


MATERIAL_EDIT_EVENT_TYPES = {
    "edit",
    "write",
    "apply_patch",
    "file_edit",
    "material_edit",
    "post_edit_structure_gate",
    "risk_surface_gate",
}


def apply_freshness(
    validation_result: dict[str, object],
    *,
    lifecycle_events: Iterable[dict[str, object]] = (),
    material_edit_cutoff: int | str | None = None,
    validation_finish: int | str | None = None,
) -> dict[str, object]:
    """Return a result copy annotated with freshness after the last material edit."""
    result = dict(validation_result)
    cutoff = material_edit_cutoff
    if cutoff is None:
        cutoff = last_material_edit_cutoff(lifecycle_events)
    finish = validation_finish
    if finish is None:
        finish = result.get("finished_index") or result.get("finished_at") or last_validation_finish(
            lifecycle_events
        )

    fresh = fresh_after_cutoff(finish, cutoff)
    result["material_edit_cutoff"] = cutoff if cutoff is not None else ""
    result["fresh_after_last_edit"] = fresh
    if fresh is False:
        result["evidence_strength"] = "negative"
        result["negative_evidence_reason"] = "stale"
    return result


def last_material_edit_cutoff(events: Iterable[dict[str, object]]) -> int | str | None:
    """Return the latest material edit index or timestamp from lifecycle events."""
    latest: int | str | None = None
    for index, event in enumerate(events, start=1):
        if not _is_material_edit(event):
            continue
        candidate = event.get("index") or event.get("event_index") or event.get("timestamp") or index
        latest = _max_cutoff(latest, candidate)
    return latest


def last_validation_finish(events: Iterable[dict[str, object]]) -> int | str | None:
    """Return the latest validation command/result index or timestamp."""
    latest: int | str | None = None
    for index, event in enumerate(events, start=1):
        if not _is_validation_event(event):
            continue
        candidate = (
            event.get("finished_index")
            or event.get("index")
            or event.get("event_index")
            or event.get("finished_at")
            or event.get("timestamp")
            or index
        )
        latest = _max_cutoff(latest, candidate)
    return latest


def fresh_after_cutoff(finish: int | str | object, cutoff: int | str | object) -> bool | str:
    """Compare validation finish position to material edit cutoff."""
    if finish in (None, "") or cutoff in (None, ""):
        return "unknown"
    finish_int = _to_int(finish)
    cutoff_int = _to_int(cutoff)
    if finish_int is not None and cutoff_int is not None:
        return finish_int > cutoff_int
    finish_time = _to_datetime(finish)
    cutoff_time = _to_datetime(cutoff)
    if finish_time is not None and cutoff_time is not None:
        return finish_time > cutoff_time
    return "unknown"


def _is_material_edit(event: dict[str, object]) -> bool:
    event_type = str(event.get("type") or event.get("hook_name") or event.get("event_type") or "")
    if event_type in MATERIAL_EDIT_EVENT_TYPES:
        return True
    if event.get("changed_paths"):
        return True
    tool = str(event.get("tool_name") or event.get("tool") or "")
    return tool in {"apply_patch", "Edit", "Write", "MultiEdit"}


def _is_validation_event(event: dict[str, object]) -> bool:
    if event.get("validation_command_detected") or event.get("validation_looking"):
        return True
    event_type = str(event.get("type") or event.get("hook_name") or "")
    return event_type in {"validation_result", "validated_command"}


def _max_cutoff(existing: int | str | None, incoming: object) -> int | str | None:
    if incoming in (None, ""):
        return existing
    if existing is None:
        return incoming if isinstance(incoming, (int, str)) else str(incoming)
    return incoming if fresh_after_cutoff(incoming, existing) is True else existing


def _to_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _to_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None
