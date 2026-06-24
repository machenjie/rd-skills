#!/usr/bin/env python3
"""Persist a compact professional context snapshot before/at compaction."""

from __future__ import annotations

from changeforge_common import (
    cwd_from_event,
    detect_runtime,
    event_name,
    hook_mode,
    is_compaction_event,
    load_state,
    merge_state,
    read_event,
    repo_root,
)
from changeforge_compaction_contract import snapshot_from_state
from changeforge_executor_adapter_core import (
    snapshot_from_event_state,
    state_update_from_snapshot,
)


def main() -> int:
    event = read_event()
    if not event or hook_mode() == "off" or not is_compaction_event(event):
        return 0
    runtime = detect_runtime(event)
    repo = repo_root(cwd_from_event(event))
    state = load_state(repo)
    snapshot = _snapshot_label(state, event_name(event))
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
        compaction_snapshots=[context_snapshot, snapshot],
        turn_stage="compaction",
        suggested_capabilities=["context-packaging", "agent-execution-discipline"],
    )
    return 0


def _snapshot_label(state: dict, hook_event: str) -> str:
    stage = state.get("turn_stage") or "unknown"
    owner = state.get("owner_skill") or "unknown"
    reviewer = state.get("reviewer_skill") or "unknown"
    changed = len(state.get("changed_paths", []))
    reads = len(state.get("read_paths", []))
    validations = len(state.get("validation_results", []))
    review = len(state.get("review_findings", []))
    repair = len(state.get("repair_events", [])) + len(state.get("repair_findings", []))
    rereview = len(state.get("rereview_events", []))
    unsupported = len((state.get("runtime_adapter") or {}).get("unsupported_checks", []))
    residual = len(state.get("closure_risk_surfaces", []))
    gates = len(state.get("suggested_gates", []))
    return (
        f"{hook_event or 'compact'}:stage={stage}:owner={owner}:reviewer={reviewer}:"
        f"changed={changed}:reads={reads}:validation={validations}:review={review}:"
        f"repair={repair}:rereview={rereview}:unsupported={unsupported}:"
        f"gates={gates}:residual={residual}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
