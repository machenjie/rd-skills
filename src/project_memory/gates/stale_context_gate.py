"""Stale Context Gate for Project Memory Governance."""

from __future__ import annotations

from typing import Any, Iterable

from project_memory.store.append_log import parse_iso_datetime


def evaluate_stale_context_gate(
    context_pack: dict[str, Any],
    *,
    changed_files: Iterable[dict[str, Any]] = (),
    drift_triggers: Iterable[str] = (),
    mode: str = "warn",
) -> dict[str, Any]:
    """Detect context packs that are too old to be treated as facts."""
    markers = context_pack.get("freshness_markers") if isinstance(context_pack, dict) else {}
    indexed_at = parse_iso_datetime(markers.get("indexed_at") if isinstance(markers, dict) else None)
    projection_status = ""
    if isinstance(context_pack, dict):
        projection = context_pack.get("project_memory_projection")
        if isinstance(projection, dict):
            projection_status = str(projection.get("stale_context_gate") or "").strip()
    stale_paths: list[str] = []
    for item in changed_files:
        if not isinstance(item, dict):
            continue
        changed_at = parse_iso_datetime(item.get("changed_at") or item.get("mtime"))
        if indexed_at is not None and changed_at is not None and indexed_at < changed_at:
            path = str(item.get("path", "")).strip()
            if path:
                stale_paths.append(path)
    triggers = [str(trigger).strip() for trigger in drift_triggers if str(trigger).strip()]
    if projection_status in {"warn", "block"}:
        triggers.append(f"project_memory_projection:{projection_status}")
    stale = bool(stale_paths or triggers)
    status = "block" if projection_status == "block" else "warn" if stale else "pass"
    return {
        "stale_context_gate": {
            "status": status,
            "stale": stale,
            "stale_paths": stale_paths[:50],
            "drift_triggers": triggers[:50],
            "allowed_as_fact": not stale,
            "allowed_to_continue": not (stale and mode == "block"),
            "required_action": (
                "refresh_repository_graph_or_mark_stale_assumption"
                if stale
                else "none"
            ),
        }
    }
