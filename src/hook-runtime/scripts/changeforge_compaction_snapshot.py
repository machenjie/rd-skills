#!/usr/bin/env python3
"""Persist a bounded professional context snapshot before compaction."""

from __future__ import annotations

from changeforge_common import (
    cwd_from_event,
    detect_runtime,
    hook_mode,
    is_compaction_event,
    load_state,
    merge_state,
    read_event,
    repo_root,
)
from changeforge_compaction_contract import (
    compaction_event_phase,
    latest_snapshot,
    merge_active_context,
    missing_required_fields,
    snapshot_from_state,
)
from changeforge_context_control_policy import compaction_budget_mode
from changeforge_executor_adapter_core import (
    snapshot_from_event_state,
    state_update_from_snapshot,
)


def main() -> int:
    event = read_event()
    if not event or hook_mode() == "off" or not is_compaction_event(event):
        return 0
    phase = compaction_event_phase(event)
    runtime = detect_runtime(event)
    repo = repo_root(cwd_from_event(event))
    state = load_state(repo)
    if phase != "pre_compact":
        _record_generic_compaction(repo, runtime, state, phase)
        if phase == "compact":
            print(
                "ChangeForge Compaction Snapshot warning: compact event has no pre_compact phase; snapshot not overwritten",
            )
        elif phase == "session_compact":
            print(
                "ChangeForge Compaction Snapshot warning: session compact used existing snapshot only; snapshot not overwritten",
            )
        return 0
    context_snapshot = snapshot_from_state(state, event, snapshot_kind="pre_compact")
    adapter_snapshot = snapshot_from_event_state(
        event,
        state,
        classification={"stage": "compaction"},
        read_evidence={
            "paths": state.get("read_paths", []),
            "patterns": state.get("searched_patterns", []),
        },
        gate_name="compaction_snapshot",
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
    return 0


def _record_generic_compaction(repo, runtime: str, state: dict, phase: str) -> None:
    snapshot = _latest_complete_snapshot(state.get("compaction_snapshots", []))
    context = state.get("active_skill_context") if isinstance(state.get("active_skill_context"), dict) else {}
    restored_context = merge_active_context(context, snapshot) if snapshot else context
    support = "degraded" if snapshot else "unsupported"
    degraded = phase in {"compact", "session_compact"}
    if degraded:
        budget_exception_reason = (
            "degraded compaction without pre_compact snapshot requires staged-plan continuity review"
        )
    else:
        budget_exception_reason = "non-precompact compaction event reused existing bounded snapshot"
    merge_state(
        repo,
        runtime,
        runtime_adapter={
            "adapter": runtime,
            "active_unsupported_checks": ["pre_compact"],
            "required_unsupported_checks": ["pre_compact"],
            "active_degradation": [f"compaction_{support}:{phase}"],
            "degraded_capabilities": [f"compaction_snapshot_{support}"],
            "fail_open_policy": "advisory",
        },
        active_skill_context=restored_context if restored_context else None,
        turn_stage="compaction",
        closure_risk_surfaces=[
            f"compaction_support:{support}",
            f"compaction_phase:{phase}",
        ],
        context_control_records=[
            {
                "route_id": "active-runtime-route",
                "current_stage": "compaction",
                "budget_mode": compaction_budget_mode(degraded=degraded),
                "budget_exception_reason": budget_exception_reason,
                "selected_reference_count": 0,
                "skipped_reference_count": 0,
                "over_budget_findings": [],
                "jit_retrieval_required": False,
                "tool_output_boundary_required": bool(state.get("tool_output_boundaries")),
                "compaction_support": support,
            }
        ],
        suggested_capabilities=[
            "context-packaging",
            "agent-execution-discipline",
            "context-control-plane",
        ],
    )


def _latest_complete_snapshot(values) -> dict:
    snapshot = latest_snapshot(values)
    if snapshot and not missing_required_fields(snapshot):
        return snapshot
    return {}


if __name__ == "__main__":
    raise SystemExit(main())
