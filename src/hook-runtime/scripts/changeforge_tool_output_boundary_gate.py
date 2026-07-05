#!/usr/bin/env python3
"""Record bounded tool-output boundary facts after tool execution."""

from __future__ import annotations

import sys

from changeforge_common import (
    compact_name,
    cwd_from_event,
    detect_runtime,
    event_name,
    hook_mode,
    load_state,
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
from changeforge_tool_output_boundary import tool_output_boundary_from_event


BOUNDARY_EVENTS = {"posttooluse", "posttoolusefailure", "posttoolbatch", "taskcompleted"}
ADVISORY_SIZE_CLASSES = {"large", "unsupported", "unknown"}


def main() -> int:
    try:
        return _main()
    except Exception as exc:  # pragma: no cover - hook runtime must fail open.
        print(
            f"ChangeForge Hook Runtime warning: tool output boundary gate failed open: {exc}",
            file=sys.stderr,
        )
        return 0


def _main() -> int:
    event = read_event()
    if not event or not _is_boundary_event(event):
        return 0
    runtime = detect_runtime(event)
    mode = hook_mode()
    if mode == "off":
        return 0
    repo = repo_root(cwd_from_event(event))
    state = load_state(repo)
    record = tool_output_boundary_from_event(event, state=state)
    finding = _finding(record)
    artifact_references = _artifact_references(record)
    snapshot = snapshot_from_event_state(
        event,
        state,
        classification={
            "stage": "tool_output_boundary",
            "tool": tool_name(event),
            "output_size_class": record["output_size_class"],
        },
        gate_name="tool_output_boundary",
        gate_mode=mode,
        gate_facts={
            "output_size_class": record["output_size_class"],
            "llm_context_policy": record["llm_context_policy"],
            "privacy_status": record["privacy_status"],
        },
    )
    snapshot_update = state_update_from_snapshot(snapshot)
    merge_state(
        repo,
        runtime,
        **snapshot_update,
        tool_output_boundaries=[record],
        artifact_references=artifact_references,
        context_budget_findings=[finding],
        suggested_capabilities=["context-control-plane", "context-packaging"],
        suggested_gates=["quality-test-gate"],
    )
    write_telemetry_event(
        repo,
        runtime=runtime,
        hook_name="tool_output_boundary_gate",
        event_name=event_name(event),
        mode=mode,
        session_id=session_id_from_event(event),
        cwd=cwd_from_event(event),
        tool_name=tool_name(event),
        normalized_events=snapshot_update["normalized_events"],
        tool_output_boundaries=[record],
        artifact_references=artifact_references,
        context_budget_findings=[finding],
        suggested_capabilities=["context-control-plane", "context-packaging"],
        suggested_gates=["quality-test-gate"],
    )
    if mode != "monitor" and _should_emit(record):
        adapter_for(runtime).emit_context(event_name(event) or "PostToolUse", _message(record))
    return 0


def _is_boundary_event(event: dict) -> bool:
    name = compact_name(event_name(event))
    if name in BOUNDARY_EVENTS:
        return True
    return bool(name and tool_name(event) and "tool" in name and "post" in name)


def _should_emit(record: dict) -> bool:
    return (
        record.get("output_size_class") in ADVISORY_SIZE_CLASSES
        or record.get("llm_context_policy") in {"artifact_reference_only", "rerun_with_redirect", "unsupported_runtime"}
        or record.get("privacy_status") == "fail"
    )


def _artifact_references(record: dict) -> list[str]:
    path = str(record.get("artifact_path") or "").strip()
    if not path or path == "<local-artifact-path-redacted>":
        return []
    return [path]


def _finding(record: dict) -> str:
    parts = [
        "tool_output_boundary",
        f"size={record.get('output_size_class', 'unknown')}",
        f"policy={record.get('llm_context_policy', 'unsupported_runtime')}",
        f"privacy={record.get('privacy_status', 'pass')}",
    ]
    if record.get("unsupported_reason"):
        parts.append(f"unsupported={record['unsupported_reason']}")
    if record.get("artifact_path"):
        parts.append("artifact=available")
    return ";".join(parts)


def _message(record: dict) -> str:
    lines = [
        "ChangeForge Tool Output Boundary Gate",
        f"- tool: {record.get('tool_name') or 'unknown'}",
        f"- output_size_class: {record.get('output_size_class')}",
        f"- llm_context_policy: {record.get('llm_context_policy')}",
        f"- privacy_status: {record.get('privacy_status')}",
    ]
    if record.get("artifact_path"):
        lines.append(f"- artifact_path: {record.get('artifact_path')}")
    if record.get("unsupported_reason"):
        lines.append(f"- unsupported_reason: {record.get('unsupported_reason')}")
    lines.append(
        "- evidence: do not paste full output; rerun with redirect or inspect bounded slices if full evidence is needed"
    )
    lines.append(
        "- closure: final evidence must cite bounded summary, artifact/slice path when available, and validation status"
    )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
