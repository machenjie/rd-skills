#!/usr/bin/env python3
"""Handle ChangeForge compaction snapshot and reinjection in one hook entrypoint."""

from __future__ import annotations

import json

from changeforge_common import (
    bounded_hook_text,
    cwd_from_event,
    detect_runtime,
    event_name,
    hook_mode,
    is_compaction_event,
    load_state,
    merge_state,
    read_event,
    repo_root,
    save_state,
)
from changeforge_compaction_contract import (
    compaction_event_phase,
    context_unusable_fields,
    format_compaction_lines,
    latest_snapshot,
    merge_active_context,
    missing_required_fields,
    redacted_required_fields,
    snapshot_from_state,
)
from changeforge_compaction_snapshot import _record_generic_compaction
from changeforge_executor_adapter_core import (
    snapshot_from_event_state,
    state_update_from_snapshot,
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
        _record_pre_compact(event, runtime, repo, state)
        return 0
    _record_generic_compaction(repo, runtime, state, phase)
    if phase in {"compact", "post_compact", "session_compact"}:
        _reinject(event, runtime, repo, phase)
    return 0


def _record_pre_compact(event: dict, runtime: str, repo, state: dict) -> None:
    context_snapshot = snapshot_from_state(state, event, snapshot_kind="pre_compact")
    adapter_snapshot = snapshot_from_event_state(
        event,
        state,
        classification={"stage": "compaction"},
        read_evidence={
            "paths": state.get("read_paths", []),
            "patterns": state.get("searched_patterns", []),
        },
        gate_name="compaction",
    )
    merge_state(
        repo,
        runtime,
        **state_update_from_snapshot(adapter_snapshot),
        compaction_snapshots=[context_snapshot],
        turn_stage="compaction",
        context_control_records=[context_snapshot.get("context_control", {})],
        suggested_capabilities=[
            "context-packaging",
            "agent-execution-discipline",
            "context-control-plane",
        ],
    )


def _reinject(event: dict, runtime: str, repo, phase: str) -> None:
    state = load_state(repo)
    snapshot = latest_snapshot(state.get("compaction_snapshots", []))
    context = state.get("active_skill_context") if isinstance(state.get("active_skill_context"), dict) else {}
    if snapshot:
        restored_context = merge_active_context(context, snapshot)
        if restored_context != context:
            state["active_skill_context"] = restored_context
            save_state(repo, state)
            context = restored_context
    state_lines = _bounded_state_lines(state, snapshot)
    missing = missing_required_fields(snapshot) if snapshot else []
    redacted = redacted_required_fields(snapshot) if snapshot else []
    unusable = context_unusable_fields(snapshot) if snapshot else []
    if not snapshot:
        state_lines.append("- warning compaction_snapshot_missing: latest pre_compact snapshot is not available")
    status = "partial" if phase == "compact" or missing or redacted or unusable or not snapshot else "pass"
    message = "\n".join(
        [
            "ChangeForge Compaction",
            "- context was compacted; continue from the active professional context below",
            f"- compaction_phase: {phase}",
            f"- context_retention_status: {status}",
            f"- compaction_reinject_signal: {phase}_reinject",
            *context_lines(context),
            *state_lines,
        ]
    )
    if hook_mode() == "monitor":
        return
    if runtime in {"codex", "claude"} and phase == "post_compact":
        print(json.dumps({"systemMessage": bounded_hook_text(message)}, sort_keys=True))
        return
    adapter = adapter_for(runtime)
    target_event = event_name(event) or "Compact"
    if adapter.supports_context_event(target_event):
        adapter.emit_context(target_event, message)
    else:
        print(bounded_hook_text(message))


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
