#!/usr/bin/env python3
"""Re-inject active professional context after context compaction."""

from __future__ import annotations

from changeforge_compaction_contract import (
    compaction_event_phase,
    format_compaction_lines,
    latest_snapshot,
    merge_active_context,
    missing_required_fields,
    snapshot_from_state,
)
from changeforge_common import (
    cwd_from_event,
    detect_runtime,
    event_name,
    hook_mode,
    is_compaction_event,
    load_state,
    read_event,
    repo_root,
    save_state,
)
from changeforge_runtime_adapters import adapter_for
from changeforge_skill_index import context_lines


def main() -> int:
    event = read_event()
    if not event or hook_mode() == "off" or not is_compaction_event(event):
        return 0
    runtime = detect_runtime(event)
    repo = repo_root(cwd_from_event(event))
    state = load_state(repo)
    phase = compaction_event_phase(event)
    if phase == "pre_compact":
        snapshot = snapshot_from_state(state, event, snapshot_kind=phase)
        state.setdefault("compaction_snapshots", [])
        state["compaction_snapshots"] = [*state.get("compaction_snapshots", []), snapshot]
        save_state(repo, state)
        return 0

    snapshot = latest_snapshot(state.get("compaction_snapshots", []))
    context = state.get("active_skill_context") if isinstance(state.get("active_skill_context"), dict) else {}
    if snapshot:
        restored_context = merge_active_context(context, snapshot)
        if restored_context != context:
            state["active_skill_context"] = restored_context
            save_state(repo, state)
            context = restored_context
    state_lines = _bounded_state_lines(state, snapshot)
    if not context and not state_lines:
        return 0
    missing = missing_required_fields(snapshot) if snapshot else []
    message = "\n".join(
        [
            "ChangeForge Compaction Reinject",
            "- context was compacted; continue from the active professional context below",
            f"- compaction_phase: {phase}",
            f"- context_retention_status: {'partial' if missing else 'pass'}",
            *context_lines(context),
            *state_lines,
        ]
    )
    if hook_mode() != "monitor":
        adapter_for(runtime).emit_context(event_name(event) or "SessionStart", message)
    return 0


def _bounded_state_lines(state: dict, snapshot: dict | None = None) -> list[str]:
    adapter = state.get("runtime_adapter") if isinstance(state.get("runtime_adapter"), dict) else {}
    unsupported = adapter.get("unsupported_checks") if isinstance(adapter, dict) else []
    lines: list[str] = []
    if snapshot:
        lines.extend(format_compaction_lines(snapshot, state))
    for label, key in (
        ("changed_paths", "changed_paths"),
        ("validation_results", "validation_results"),
        ("review_findings", "review_findings"),
        ("repair_events", "repair_events"),
        ("rereview_events", "rereview_events"),
        ("closure_risk_surfaces", "closure_risk_surfaces"),
        ("compaction_snapshots", "compaction_snapshots"),
    ):
        values = state.get(key)
        if isinstance(values, list) and values:
            rendered = []
            for item in values[:6]:
                if isinstance(item, dict):
                    rendered.append(str(item.get("snapshot_id") or item.get("snapshot_kind") or "<snapshot>")[:80])
                else:
                    rendered.append(str(item)[:80])
            lines.append(f"- {label}: {', '.join(rendered)}")
    if isinstance(unsupported, list) and unsupported:
        lines.append(f"- unsupported_runtime_checks: {', '.join(str(item)[:80] for item in unsupported[:6])}")
    return lines


if __name__ == "__main__":
    raise SystemExit(main())
