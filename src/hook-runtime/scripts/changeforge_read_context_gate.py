#!/usr/bin/env python3
"""Record read/search context evidence so closure can distinguish analysis work."""

from __future__ import annotations

from changeforge_action_classifier import extract_read_evidence, is_read_tool, is_review_diff_tool
from changeforge_common import (
    cwd_from_event,
    detect_runtime,
    event_name,
    hook_mode,
    merge_state,
    read_event,
    repo_root,
    session_id_from_event,
    tool_name,
    write_telemetry_event,
)
from changeforge_executor_adapter_core import (
    snapshot_from_event_state,
    state_update_from_snapshot,
)
from changeforge_runtime_adapters import adapter_for


def main() -> int:
    event = read_event()
    if not event or not is_read_tool(event):
        return 0
    runtime = detect_runtime(event)
    mode = hook_mode()
    if mode == "off":
        return 0
    repo = repo_root(cwd_from_event(event))
    evidence = extract_read_evidence(event)
    paths = evidence["paths"]
    patterns = evidence["patterns"]
    diff_seen = is_review_diff_tool(event)
    snapshot = snapshot_from_event_state(
        event,
        {},
        classification={"stage": "read", "paths": paths, "tool": tool_name(event)},
        read_evidence={"paths": paths, "patterns": patterns},
        gate_name="read_context",
        gate_mode=mode,
    )
    snapshot_update = state_update_from_snapshot(snapshot)
    snapshot_update["read_paths"] = paths
    snapshot_update["searched_patterns"] = patterns
    state = merge_state(
        repo,
        runtime,
        **snapshot_update,
        read_tools=[tool_name(event) or "read"],
        turn_stage="read",
        read_intent_seen=True,
        read_evidence_seen=True,
        reviewed_diff_evidence_seen=diff_seen,
        review_artifact_seen=diff_seen,
        review_evidence_seen=diff_seen,
        review_targets=paths if diff_seen else (),
        suggested_capabilities=["context-packaging"],
        suggested_gates=["quality-test-gate"],
    )
    write_telemetry_event(
        repo,
        runtime=runtime,
        hook_name="read_context_gate",
        event_name=event_name(event),
        mode=mode,
        session_id=session_id_from_event(event),
        cwd=cwd_from_event(event),
        tool_name=tool_name(event),
        normalized_events=snapshot_update["normalized_events"],
        hook_findings={"read_paths": paths, "searched_patterns": patterns},
        turn_stage="read",
        read_evidence_seen=True,
    )
    if mode != "monitor":
        message = _message(paths, patterns, state)
        adapter_for(runtime).emit_context(event_name(event) or "PostToolUse", message)
    return 0


def _message(paths: list[str], patterns: list[str], state: dict) -> str:
    path_text = ", ".join(paths[:6]) if paths else "not detected"
    pattern_text = ", ".join(patterns[:6]) if patterns else "not detected"
    return (
        "ChangeForge Read Context Gate\n"
        f"- read_paths: {path_text}\n"
        f"- searched_patterns: {pattern_text}\n"
        f"- turn_stage: {state.get('turn_stage', 'read')}\n"
        "- closure: final handoff should state what was inspected, what remains unknown, and validation limits"
    )


if __name__ == "__main__":
    raise SystemExit(main())
