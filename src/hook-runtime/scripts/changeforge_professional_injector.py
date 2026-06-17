#!/usr/bin/env python3
"""Inject active ChangeForge professional skill context for the current action."""

from __future__ import annotations

from pathlib import Path

from changeforge_action_classifier import classify_event
from changeforge_common import (
    cwd_from_event,
    detect_runtime,
    event_name,
    hook_mode,
    load_state,
    merge_state,
    read_event,
    repo_root,
    reset_state_for_new_prompt,
    session_id_from_event,
    write_telemetry_event,
)
from changeforge_runtime_adapters import adapter_for
from changeforge_skill_index import build_active_skill_context, context_lines


CONTRACT_FILE_BY_RUNTIME = {
    "copilot": "changeforge_copilot_professional_contract.md",
}
DEFAULT_CONTRACT_FILE = "changeforge_professional_contract.md"


def main() -> int:
    event = read_event()
    if not event:
        return 0
    runtime = detect_runtime(event)
    mode = hook_mode()
    if mode == "off":
        return 0
    hook_event = event_name(event) or "PostToolUse"
    repo = repo_root(cwd_from_event(event))
    reset_state_for_new_prompt(repo, runtime, event)
    state = load_state(repo)
    classification = classify_event(event)
    if not classification.get("should_inject", True):
        return 0
    context = build_active_skill_context(
        runtime=runtime,
        stage=classification["stage"],
        surfaces=classification["surfaces"],
        event_name=hook_event,
        state=state,
        classification=classification,
    )
    contract_text = _contract_text(runtime)
    message = "\n".join(context_lines(context))
    if contract_text and hook_event in {"SessionStart", "SubagentStart"}:
        message = f"{message}\n\n{contract_text}"

    merge_state(
        repo,
        runtime,
        professional_injections=[f"{hook_event}:{context['stage']}"],
        prompt_signals=classification.get("prompt_signals", []),
        suggested_skills=context.get("selected_skills", []),
        suggested_capabilities=context.get("selected_capabilities", []),
        suggested_domain_extensions=context.get("selected_domain_extensions", []),
        suggested_gates=context.get("required_quality_gates", []),
        reference_loads=context.get("required_references", []),
        risk_surfaces=context.get("risk_surfaces", []),
        turn_stage=context["current_stage"],
        active_skill_context=context,
        owner_skill=context["owner_skill"],
        reviewer_skill=context["reviewer_skill"],
        professional_contract_seen=bool(contract_text),
    )
    write_telemetry_event(
        repo,
        runtime=runtime,
        hook_name="professional_injector",
        event_name=hook_event,
        mode=mode,
        session_id=session_id_from_event(event),
        cwd=cwd_from_event(event),
        tool_name=classification.get("tool", ""),
        risk_surfaces=context.get("risk_surfaces", []),
        suggested_skills=context.get("selected_skills", []),
        suggested_capabilities=context.get("selected_capabilities", []),
        suggested_gates=context.get("required_quality_gates", []),
        suggested_domain_extensions=context.get("selected_domain_extensions", []),
        turn_stage=context["current_stage"],
        owner_skill=context["owner_skill"],
        reviewer_skill=context["reviewer_skill"],
        professional_contract_seen=bool(contract_text),
    )
    if mode != "monitor":
        adapter_for(runtime).emit_context(hook_event, message)
    return 0


def _contract_text(runtime: str) -> str:
    name = CONTRACT_FILE_BY_RUNTIME.get(runtime, DEFAULT_CONTRACT_FILE)
    path = Path(__file__).with_name(name)
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
