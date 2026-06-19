#!/usr/bin/env python3
"""Re-inject active professional context after context compaction."""

from __future__ import annotations

from changeforge_common import (
    cwd_from_event,
    detect_runtime,
    event_name,
    hook_mode,
    is_compaction_event,
    load_state,
    read_event,
    repo_root,
)
from changeforge_runtime_adapters import adapter_for
from changeforge_skill_index import context_lines


def main() -> int:
    event = read_event()
    if not event or hook_mode() == "off" or not is_compaction_event(event):
        return 0
    runtime = detect_runtime(event)
    state = load_state(repo_root(cwd_from_event(event)))
    context = state.get("active_skill_context") if isinstance(state.get("active_skill_context"), dict) else {}
    state_lines = _bounded_state_lines(state)
    if not context and not state_lines:
        return 0
    message = "\n".join(
        [
            "ChangeForge Compaction Reinject",
            "- context was compacted; continue from the active professional context below",
            *context_lines(context),
            *state_lines,
        ]
    )
    if hook_mode() != "monitor":
        adapter_for(runtime).emit_context(event_name(event) or "SessionStart", message)
    return 0


def _bounded_state_lines(state: dict) -> list[str]:
    adapter = state.get("runtime_adapter") if isinstance(state.get("runtime_adapter"), dict) else {}
    unsupported = adapter.get("unsupported_checks") if isinstance(adapter, dict) else []
    lines: list[str] = []
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
            lines.append(f"- {label}: {', '.join(str(item)[:80] for item in values[:6])}")
    if isinstance(unsupported, list) and unsupported:
        lines.append(f"- unsupported_runtime_checks: {', '.join(str(item)[:80] for item in unsupported[:6])}")
    return lines


if __name__ == "__main__":
    raise SystemExit(main())
