#!/usr/bin/env python3
"""Inject active ChangeForge professional skill context for the current action."""

from __future__ import annotations

import hashlib
import json
import os
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
from changeforge_hook_policy import run_gate_with_policy
from changeforge_runtime_adapters import adapter_for
from changeforge_skill_index import build_active_skill_context, context_lines


CONTRACT_FILE_BY_RUNTIME = {
    "copilot": "changeforge_copilot_professional_contract.md",
}
DEFAULT_CONTRACT_FILE = "changeforge_professional_contract.md"


def main() -> int:
    return run_gate_with_policy(
        "professional_injector",
        _main,
        fail_closed=_write_degraded_telemetry,
        fail_open=_write_degraded_telemetry,
    )


def _main() -> int:
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
    digest = _active_context_digest(context, hook_event=hook_event)
    if not _force_emit_context(context, state, hook_event) and digest == state.get("professional_injection_digest"):
        return 0

    merge_state(
        repo,
        runtime,
        professional_injections=[f"{hook_event}:{context['stage']}"],
        professional_injection_digests=[digest],
        professional_injection_digest=digest,
        last_professional_injection_event=hook_event,
        prompt_signals=classification.get("prompt_signals", []),
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


def _active_context_digest(context: dict, *, hook_event: str) -> str:
    """Hash bounded active-context facts without raw prompt or command output."""
    control = context.get("context_control") if isinstance(context.get("context_control"), dict) else {}
    allowed = {
        "current_stage",
        "owner_skill",
        "reviewer_skill",
        "selected_skills",
        "selected_capabilities",
        "required_quality_gates",
        "required_references",
        "skipped_references",
        "risk_surfaces",
    }
    payload = {key: context.get(key) for key in sorted(allowed) if key in context}
    payload["hook_event"] = hook_event
    payload["context_budget_mode"] = control.get("budget_mode") or context.get("context_budget_mode")
    payload["context_control"] = {
        "budget_mode": control.get("budget_mode"),
        "selected_reference_count": control.get("selected_reference_count", 0),
        "skipped_reference_count": control.get("skipped_reference_count", 0),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:24]


def _force_emit_context(context: dict, state: dict, hook_event: str) -> bool:
    if hook_event in {"SessionStart", "SubagentStart"}:
        return True
    control = context.get("context_control") if isinstance(context.get("context_control"), dict) else {}
    if control.get("over_budget_findings"):
        return True
    if state.get("turn_stage") and context.get("current_stage") != state.get("turn_stage"):
        return True
    if state.get("owner_skill") and context.get("owner_skill") != state.get("owner_skill"):
        return True
    if state.get("reviewer_skill") and context.get("reviewer_skill") != state.get("reviewer_skill"):
        return True
    previous_risks = {str(item) for item in state.get("risk_surfaces", []) if isinstance(item, str)}
    current_risks = {str(item) for item in context.get("risk_surfaces", []) if isinstance(item, str)}
    if previous_risks and previous_risks != current_risks:
        return True
    adapter = state.get("runtime_adapter") if isinstance(state.get("runtime_adapter"), dict) else {}
    if adapter.get("active_degradation") and hook_event != state.get("last_professional_injection_event"):
        return True
    return False


def _write_degraded_telemetry(exc: Exception) -> None:
    """Record bounded degraded-hook telemetry without blocking the agent turn."""
    try:
        repo = repo_root(os.getcwd())
        write_telemetry_event(
            repo,
            runtime=detect_runtime({}),
            hook_name="professional_injector",
            event_name="unknown",
            mode=hook_mode(),
            cwd=os.getcwd(),
            risk_surfaces=["hook-runtime-degraded"],
            suggested_capabilities=["agent-tool-permission-sandbox"],
            suggested_gates=["security-privacy-gate"],
            hook_findings={"degraded": [type(exc).__name__[:120]]},
            turn_stage="hook-degraded",
            owner_skill="change-forge-router",
            reviewer_skill="security-privacy-gate",
        )
    except Exception:
        return


def _contract_text(runtime: str) -> str:
    name = CONTRACT_FILE_BY_RUNTIME.get(runtime, DEFAULT_CONTRACT_FILE)
    path = Path(__file__).with_name(name)
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
