#!/usr/bin/env python3
"""Detect review-oriented work and record review-stage closure expectations."""

from __future__ import annotations

from changeforge_action_classifier import classify_event, extract_read_evidence
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
from changeforge_runtime_adapters import adapter_for


def main() -> int:
    event = read_event()
    if not event:
        return 0
    runtime = detect_runtime(event)
    mode = hook_mode()
    if mode == "off":
        return 0
    classification = classify_event(event)
    if classification["stage"] not in {"review", "repair"} and "review" not in classification["surfaces"]:
        return 0
    evidence = extract_read_evidence(event)
    repo = repo_root(cwd_from_event(event))
    merge_state(
        repo,
        runtime,
        review_targets=evidence["paths"],
        review_findings=[classification["stage"]],
        prompt_signals=classification.get("prompt_signals", []),
        turn_stage=classification["stage"],
        review_evidence_seen=True,
        suggested_skills=["ai-code-review-refactor"],
        suggested_gates=["quality-test-gate"],
    )
    write_telemetry_event(
        repo,
        runtime=runtime,
        hook_name="review_gate",
        event_name=event_name(event),
        mode=mode,
        session_id=session_id_from_event(event),
        cwd=cwd_from_event(event),
        tool_name=tool_name(event),
        hook_findings={"review_targets": evidence["paths"]},
        turn_stage=classification["stage"],
        review_evidence_seen=True,
    )
    if mode != "monitor":
        adapter_for(runtime).emit_context(event_name(event) or "PostToolUse", _message(classification))
    return 0


def _message(classification: dict) -> str:
    return (
        "ChangeForge Review Gate\n"
        f"- turn_stage: {classification['stage']}\n"
        "- review output must lead with severity-classified findings or explicitly state no findings\n"
        "- repair output must trace each finding to a fix, re-review, validation, and residual risk"
    )


if __name__ == "__main__":
    raise SystemExit(main())

