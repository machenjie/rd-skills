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
        classification=classification,
    )
    repo = repo_root(cwd_from_event(event))
    merge_state(
        repo,
        runtime,
        subagent_contracts=[f"{context['owner_skill']}->{context['reviewer_skill']}"],
        suggested_skills=context.get("selected_skills", []),
        suggested_capabilities=context.get("selected_capabilities", []),
        suggested_domain_extensions=context.get("selected_domain_extensions", []),
        suggested_gates=context.get("required_quality_gates", []),
        context_control_records=[context.get("context_control", {})],
        context_budget_findings=context.get("context_control", {}).get("over_budget_findings", []),
        skipped_references=[
            f"{item.get('reference')}: {item.get('reason')}"
            for item in context.get("skipped_references", [])
            if isinstance(item, dict)
        ],
        reference_loads=context.get("required_references", []),
        risk_surfaces=context.get("risk_surfaces", []),
        turn_stage=context["current_stage"],
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
        suggested_skills=context.get("selected_skills", []),
        suggested_capabilities=context.get("selected_capabilities", []),
        suggested_gates=context.get("required_quality_gates", []),
        suggested_domain_extensions=context.get("selected_domain_extensions", []),
        risk_surfaces=context.get("risk_surfaces", []),
        turn_stage=context["current_stage"],
        owner_skill=context["owner_skill"],
        reviewer_skill=context["reviewer_skill"],
    )
    if mode != "monitor":
        adapter_for(runtime).emit_context(event_name(event) or "SubagentStart", "\n".join(context_lines(context)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
