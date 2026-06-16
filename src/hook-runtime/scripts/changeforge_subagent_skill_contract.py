#!/usr/bin/env python3
"""Inject a bounded ChangeForge skill contract for subagents."""

from __future__ import annotations

from changeforge_action_classifier import classify_event
from changeforge_common import (
    cwd_from_event,
    detect_runtime,
    event_name,
    hook_mode,
    is_subagent_start,
    merge_state,
    read_event,
    repo_root,
    session_id_from_event,
    write_telemetry_event,
)
from changeforge_runtime_adapters import adapter_for
from changeforge_skill_index import build_active_skill_context, context_lines


def main() -> int:
    event = read_event()
    if not event or not is_subagent_start(event):
        return 0
    runtime = detect_runtime(event)
    mode = hook_mode()
    if mode == "off":
        return 0
    classification = classify_event(event)
    classification["stage"] = "subagent"
    context = build_active_skill_context(
        runtime=runtime,
        stage="subagent",
        surfaces=classification["surfaces"],
        event_name=event_name(event) or "SubagentStart",
    )
    repo = repo_root(cwd_from_event(event))
    merge_state(
        repo,
        runtime,
        subagent_contracts=[f"{context['owner_skill']}->{context['reviewer_skill']}"],
        suggested_skills=[context["owner_skill"], context["reviewer_skill"]],
        suggested_capabilities=context.get("selected_capabilities", []),
        turn_stage="subagent",
        active_skill_context=context,
        owner_skill=context["owner_skill"],
        reviewer_skill=context["reviewer_skill"],
    )
    write_telemetry_event(
        repo,
        runtime=runtime,
        hook_name="subagent_skill_contract",
        event_name=event_name(event),
        mode=mode,
        session_id=session_id_from_event(event),
        cwd=cwd_from_event(event),
        turn_stage="subagent",
        owner_skill=context["owner_skill"],
        reviewer_skill=context["reviewer_skill"],
    )
    if mode != "monitor":
        adapter_for(runtime).emit_context(event_name(event) or "SubagentStart", "\n".join(context_lines(context)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

