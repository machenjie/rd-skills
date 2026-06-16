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


def main() -> int:
    event = read_event()
    if not event or hook_mode() == "off" or not is_compaction_event(event):
        return 0
    runtime = detect_runtime(event)
    repo = repo_root(cwd_from_event(event))
    state = load_state(repo)
    snapshot = _snapshot_label(state, event_name(event))
    merge_state(
        repo,
        runtime,
        compaction_snapshots=[snapshot],
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
    return f"{hook_event or 'compact'}:stage={stage}:owner={owner}:reviewer={reviewer}:changed={changed}:reads={reads}"


if __name__ == "__main__":
    raise SystemExit(main())

