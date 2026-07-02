#!/usr/bin/env python3
"""Detect review-oriented work and record review-stage closure expectations."""

from __future__ import annotations

from changeforge_action_classifier import classify_event, extract_read_evidence, is_review_diff_tool
from changeforge_common import (
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
from changeforge_sdd_material_choice_gate import (
    evaluate_review_material_choice,
    render_review_blocker,
)
from changeforge_executor_adapter_core import (
    snapshot_from_event_state,
    state_update_from_snapshot,
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
    prompt_signals = classification.get("prompt_signals", [])
    review_or_repair = classification["stage"] in {"review", "repair"} or "review" in classification["surfaces"]
    if not review_or_repair and not any(
        signal in prompt_signals for signal in ("review_intent", "repair_intent", "repair_followup")
    ):
        return 0
    evidence = extract_read_evidence(event)
    artifact_seen = bool(evidence["paths"]) or is_review_diff_tool(event)
    repo = repo_root(cwd_from_event(event))
    state = load_state(repo)
    choice_review = evaluate_review_material_choice(event, state, repo)
    choice_blocker = bool(choice_review.get("material") and choice_review.get("blocks"))
    snapshot = snapshot_from_event_state(
        event,
        state,
        classification=classification,
        read_evidence={"paths": evidence["paths"], "patterns": evidence["patterns"]},
        gate_name="review",
        gate_mode=mode,
    )
    snapshot_update = state_update_from_snapshot(snapshot)
    snapshot_update["read_paths"] = evidence["paths"] if artifact_seen else []
    snapshot_update["searched_patterns"] = evidence["patterns"]
    merge_state(
        repo,
        runtime,
        **snapshot_update,
        review_targets=evidence["paths"] if artifact_seen else (),
        review_findings=["material_sdd_choice_without_user_resolution"] if choice_blocker else (),
        prompt_signals=prompt_signals,
        turn_stage=classification["stage"],
        review_intent_seen=True,
        review_artifact_seen=artifact_seen,
        review_evidence_seen=artifact_seen,
        repair_evidence_seen=False,
        suggested_skills=["ai-code-review-refactor"],
        suggested_gates=["quality-test-gate", "sdd-material-choice-gate"] if choice_blocker else ["quality-test-gate"],
        choice_gate_seen=bool(choice_review.get("material")),
        choice_gate_blocked=choice_blocker,
        choice_resolution_evidence_seen=not choice_blocker and bool(choice_review.get("material")),
        choice_ids=choice_review.get("evidence", {}).get("choice_ids") or (),
        choice_triggers=choice_review.get("surfaces", ()),
        choice_status=[choice_review.get("evidence_result", {}).get("status", "missing")] if choice_review.get("material") else (),
        material_choice_surfaces=choice_review.get("surfaces", ()),
        blocked_tool_category=["review"] if choice_blocker else (),
        bounded_paths=choice_review.get("changed_paths", ()),
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
        normalized_events=snapshot_update["normalized_events"],
        hook_findings={"review_targets": evidence["paths"]},
        turn_stage=classification["stage"],
        review_evidence_seen=artifact_seen,
        choice_gate_seen=bool(choice_review.get("material")),
        choice_gate_blocked=choice_blocker,
        choice_resolution_evidence_seen=not choice_blocker and bool(choice_review.get("material")),
        choice_ids=choice_review.get("evidence", {}).get("choice_ids") or (),
        choice_triggers=choice_review.get("surfaces", ()),
        choice_status=[choice_review.get("evidence_result", {}).get("status", "missing")] if choice_review.get("material") else (),
        material_choice_surfaces=choice_review.get("surfaces", ()),
        blocked_tool_category=["review"] if choice_blocker else (),
        bounded_paths=choice_review.get("changed_paths", ()),
    )
    if mode != "monitor":
        adapter_for(runtime).emit_context(
            event_name(event) or "PostToolUse",
            _message(classification, choice_review),
        )
    return 0


def _message(classification: dict, choice_review: dict | None = None) -> str:
    artifact_note = "- actual reviewed files or PR diff evidence is still required"
    if classification["stage"] in {"review", "repair"}:
        artifact_note = "- review intent recorded separately from reviewed artifact evidence"
    message = (
        "ChangeForge Review Gate\n"
        f"- turn_stage: {classification['stage']}\n"
        f"{artifact_note}\n"
        "- review output must lead with severity-classified findings or explicitly state no findings\n"
        "- repair output must trace each finding to a fix, re-review, validation, and residual risk"
    )
    if isinstance(choice_review, dict) and choice_review.get("material") and choice_review.get("blocks"):
        message += "\n\n" + render_review_blocker(choice_review)
    return message


if __name__ == "__main__":
    raise SystemExit(main())
