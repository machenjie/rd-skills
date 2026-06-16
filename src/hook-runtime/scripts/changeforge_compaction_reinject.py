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
    if not context:
        return 0
    message = "\n".join(
        [
            "ChangeForge Compaction Reinject",
            "- context was compacted; continue from the active professional context below",
            *context_lines(context),
        ]
    )
    if hook_mode() != "monitor":
        adapter_for(runtime).emit_context(event_name(event) or "SessionStart", message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

