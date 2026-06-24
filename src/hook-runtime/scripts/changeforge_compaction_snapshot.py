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
from changeforge_compaction_contract import compaction_event_phase, snapshot_from_state
from changeforge_executor_adapter_core import (
    snapshot_from_event_state,
    state_update_from_snapshot,
)


def main() -> int:
    event = read_event()
    if not event or hook_mode() == "off" or not is_compaction_event(event):
        return 0
    phase = compaction_event_phase(event)
    if phase != "pre_compact":
        if phase == "compact":
            print(
                "ChangeForge Compaction Snapshot warning: compact event has no pre_compact phase; snapshot not overwritten",
            )
        return 0
    runtime = detect_runtime(event)
    repo = repo_root(cwd_from_event(event))
    state = load_state(repo)
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
        suggested_capabilities=["context-packaging", "agent-execution-discipline"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
