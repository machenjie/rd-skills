#!/usr/bin/env python3
"""Collect post-tool ChangeForge evidence through one bounded runtime hook."""

from __future__ import annotations

import sys
from typing import Any

from changeforge_action_classifier import (
    classify_event,
    extract_read_evidence,
    is_read_tool,
    is_review_diff_tool,
)
from changeforge_common import (
    compact_name,
    cwd_from_event,
    detect_runtime,
    event_name,
    extract_bash_command,
    extract_changed_paths,
    hook_mode,
    is_post_tool_use,
    load_state,
    merge_state,
    read_event,
    repo_root,
    save_state,
    session_id_from_event,
    summarize_command_program,
    tool_name,
    write_telemetry_event,
)
from changeforge_executor_adapter_core import (
    snapshot_from_event_state,
    state_update_from_snapshot,
)
from changeforge_post_edit_structure_gate import (
    EDIT_TOOLS as STRUCTURE_EDIT_TOOLS,
    _added_paths,
    _advanced_refactor_findings,
    _comment_findings,
    _extension_reuse_findings,
    _file_naming_findings,
    _patch_file_added_lines,
    _patch_text,
    _post_edit_structure_summaries,
    _reuse_findings,
    _structure_findings,
    _structure_quality_findings,
    _suggested_capabilities as _structure_suggested_capabilities,
    _suggested_skills as _structure_suggested_skills,
    _warning_message as _structure_warning_message,
)
from changeforge_review_gate import _message as _review_message
from changeforge_risk_surface_gate import (
    WATCHED_TOOLS as RISK_TOOLS,
    _collect as _risk_collect,
    _command_evidence_fact,
    _command_risk_class,
    _command_risk_is_closure_relevant,
    _looks_like_validation,
    _merge_findings,
    _risk_findings,
    _special_command_findings,
    _tool_permission_findings,
    _validation_results,
    _warning_message as _risk_warning_message,
)
from changeforge_runtime_adapters import adapter_for
from changeforge_sdd_material_choice_gate import (
    evaluate_review_material_choice,
    render_review_blocker,
)
from changeforge_tool_output_boundary import INPUT_CONTAINER_KEYS, tool_output_boundary_from_event
from changeforge_tool_output_boundary_gate import (
    _artifact_references,
    _finding as _boundary_finding,
    _is_boundary_event,
    _message as _boundary_message,
    _should_emit as _boundary_should_emit,
)


BOUNDARY_FORCE_EVENTS = {"posttoolusefailure", "posttoolbatch", "taskcompleted"}
SUPERPOWERS_ADVISORY_POLICY = (
    "Post-tool collection observes bounded read, edit, validation, review, and repair facts; "
    "it does not execute task plans or ask ordinary agents to maintain runtime state."
)
OUTPUT_SIGNAL_CONTAINER_KEYS = {
    "tool_result",
    "toolResult",
    "tool_response",
    "toolResponse",
    "response",
    "result",
}
OUTPUT_SIGNAL_TEXT_KEYS = {"stdout", "stderr", "output", "content", "text"}
OUTPUT_SIGNAL_METADATA_KEYS = {
    "output_bytes",
    "outputBytes",
    "output_lines",
    "outputLines",
    "artifact_path",
    "artifactPath",
    "privacy_status",
}


def main() -> int:
    try:
        return _main()
    except Exception as exc:  # pragma: no cover - hooks must fail open.
        print(
            f"ChangeForge Hook Runtime warning: post-tool collector failed open: {exc}",
            file=sys.stderr,
        )
        return 0


def _main() -> int:
    event = read_event()
    if not event:
        return 0
    runtime = detect_runtime(event)
    if runtime == "unknown":
        return 0
    mode = hook_mode()
    if mode == "off":
        return 0
    name = compact_name(event_name(event))
    if not (is_post_tool_use(event) or _is_boundary_event(event) or name in BOUNDARY_FORCE_EVENTS):
        return 0

    repo = repo_root(cwd_from_event(event))
    state_before = load_state(repo)
    tool = compact_name(tool_name(event))
    paths = extract_changed_paths(event)
    command = extract_bash_command(event)
    meaningful = False
    output_messages: list[str] = []
    merge_update: dict[str, Any] = {}
    telemetry: dict[str, Any] = {
        "hook_findings": {},
        "suggested_skills": [],
        "suggested_capabilities": [],
        "suggested_domain_extensions": [],
        "suggested_gates": [],
    }

    boundary_record = _boundary_record_if_needed(event, state_before)
    if not _has_meaningful_surface(event, tool, paths, command, boundary_record):
        return 0

    classification = _collector_classification(event, tool, paths, command)
    snapshot = snapshot_from_event_state(
        event,
        state_before,
        classification=classification,
        read_evidence={
            "paths": state_before.get("read_paths", []),
            "patterns": state_before.get("searched_patterns", []),
        },
        gate_name="post_tool_collector",
        gate_mode=mode,
    )
    _merge_mapping(merge_update, state_update_from_snapshot(snapshot))

    if boundary_record:
        meaningful = True
        finding = _boundary_finding(boundary_record)
        references = _artifact_references(boundary_record)
        _append(merge_update, "tool_output_boundaries", [boundary_record])
        _append(merge_update, "artifact_references", references)
        _append(merge_update, "context_budget_findings", [finding])
        _append(merge_update, "suggested_capabilities", ["context-control-plane", "context-packaging"])
        _append(merge_update, "suggested_gates", ["quality-test-gate"])
        telemetry["tool_output_boundaries"] = [boundary_record]
        telemetry["artifact_references"] = references
        telemetry["context_budget_findings"] = [finding]
        if mode != "monitor" and _boundary_should_emit(boundary_record):
            output_messages.append(_boundary_message(boundary_record))

    if is_read_tool(event):
        meaningful = True
        _collect_read(event, merge_update, telemetry)

    if tool in STRUCTURE_EDIT_TOOLS and paths:
        meaningful = True
        structure_message = _collect_structure(event, repo, state_before, tool, paths, merge_update, telemetry)
        if structure_message and mode != "monitor":
            output_messages.append(structure_message)

    if tool in RISK_TOOLS:
        risk_message = _collect_risk(event, state_before, tool, paths, command, merge_update, telemetry)
        risk_evidence_recorded = bool(
            merge_update.get("validation_results")
            or merge_update.get("command_risks")
            or merge_update.get("risk_surfaces")
            or merge_update.get("command_risk_surfaces")
        )
        if risk_message or risk_evidence_recorded:
            meaningful = True
            if risk_message and mode != "monitor":
                output_messages.append(risk_message)

    review_message = _collect_review(event, state_before, merge_update, telemetry)
    if review_message:
        meaningful = True
        if mode != "monitor":
            output_messages.append(review_message)

    if not meaningful:
        return 0

    state = merge_state(repo, runtime, **_merge_state_kwargs(merge_update))
    write_telemetry_event(
        repo,
        runtime=runtime,
        hook_name="post_tool_collector",
        event_name=event_name(event),
        mode=mode,
        session_id=session_id_from_event(event),
        cwd=cwd_from_event(event),
        tool_name=tool_name(event),
        normalized_events=merge_update.get("normalized_events", []),
        **telemetry,
    )
    if output_messages:
        if any(message.startswith("ChangeForge Risk Surface Gate") for message in output_messages):
            state["route_preflight_emitted"] = True
            save_state(repo, state)
        adapter_for(runtime).emit_context(event_name(event) or "PostToolUse", "\n\n".join(output_messages))
    return 0


def _collector_classification(event: dict, tool: str, paths: list[str], command: str) -> dict[str, Any]:
    if is_read_tool(event):
        return {"stage": "read", "paths": paths, "tool": tool_name(event)}
    if tool in STRUCTURE_EDIT_TOOLS:
        return {"stage": "edit", "paths": paths, "tool": tool_name(event)}
    if tool in RISK_TOOLS:
        return {
            "stage": "test" if _looks_like_validation(command) else "edit",
            "paths": paths,
            "tool": tool_name(event),
            "command_program": summarize_command_program(command),
        }
    if _is_boundary_event(event):
        return {"stage": "tool_output_boundary", "tool": tool_name(event)}
    return classify_event(event)


def _has_meaningful_surface(
    event: dict,
    tool: str,
    paths: list[str],
    command: str,
    boundary_record: dict | None,
) -> bool:
    if boundary_record:
        return True
    if is_read_tool(event):
        evidence = extract_read_evidence(event)
        return bool(evidence["paths"] or evidence["patterns"] or is_review_diff_tool(event))
    if tool in STRUCTURE_EDIT_TOOLS and paths:
        return True
    if tool in RISK_TOOLS and (paths or command or _validation_results(command, event)):
        return True
    if is_review_diff_tool(event):
        return True
    classification = classify_event(event)
    return classification.get("stage") in {"review", "repair"} and bool(
        classification.get("prompt_signals") or classification.get("surfaces")
    )


def _boundary_record_if_needed(event: dict, state: dict) -> dict | None:
    name = compact_name(event_name(event))
    force = name in BOUNDARY_FORCE_EVENTS
    has_output_signal = _has_output_signal(event)
    if not force and not has_output_signal:
        return None
    record = tool_output_boundary_from_event(event, state=state)
    if force or _boundary_should_emit(record):
        return record
    return None


def _has_output_signal(event: dict) -> bool:
    def visit(value: Any, key: str = "", *, in_output_container: bool = False) -> bool:
        if key in INPUT_CONTAINER_KEYS:
            return False
        if key in OUTPUT_SIGNAL_METADATA_KEYS:
            return True
        child_in_output_container = in_output_container or key in OUTPUT_SIGNAL_CONTAINER_KEYS
        if isinstance(value, dict):
            return any(
                visit(
                    child_value,
                    str(child_key),
                    in_output_container=child_in_output_container,
                )
                for child_key, child_value in value.items()
            )
        if isinstance(value, list):
            return any(visit(item, "", in_output_container=child_in_output_container) for item in value)
        if isinstance(value, str) and key in OUTPUT_SIGNAL_CONTAINER_KEYS and value.strip():
            return True
        return key in OUTPUT_SIGNAL_TEXT_KEYS and child_in_output_container

    return visit(event)


def _collect_read(event: dict, update: dict[str, Any], telemetry: dict[str, Any]) -> None:
    evidence = extract_read_evidence(event)
    paths = evidence["paths"]
    patterns = evidence["patterns"]
    diff_seen = is_review_diff_tool(event)
    _append(update, "read_paths", paths)
    _append(update, "searched_patterns", patterns)
    _append(update, "read_tools", [tool_name(event) or "read"])
    _append(update, "suggested_capabilities", ["context-packaging"])
    _append(update, "suggested_gates", ["quality-test-gate"])
    _set(update, "turn_stage", "read")
    _set(update, "read_intent_seen", True)
    _set(update, "read_evidence_seen", True)
    if diff_seen:
        _set(update, "reviewed_diff_evidence_seen", True)
        _set(update, "review_artifact_seen", True)
        _set(update, "review_evidence_seen", True)
        _append(update, "review_targets", paths)
    telemetry["read_evidence_seen"] = True
    telemetry["hook_findings"]["read_paths"] = paths
    telemetry["hook_findings"]["searched_patterns"] = patterns


def _collect_structure(
    event: dict,
    repo,
    state_before: dict,
    tool: str,
    paths: list[str],
    update: dict[str, Any],
    telemetry: dict[str, Any],
) -> str:
    added_paths = _added_paths(event)
    patch_text = _patch_text(event)
    added_by_file = _patch_file_added_lines(patch_text)
    structure_findings = _structure_findings(paths, tool, added_paths)
    file_naming_findings = _file_naming_findings(repo, added_paths, tool, paths)
    reuse_findings = _reuse_findings(paths, added_paths)
    extension_reuse_findings = _extension_reuse_findings(patch_text, added_paths, paths)
    advanced_refactor_findings = _advanced_refactor_findings(patch_text, added_paths)
    comment_findings = _comment_findings(added_by_file)
    structure_quality_findings = _structure_quality_findings(added_by_file, added_paths, paths)
    any_findings = bool(
        structure_findings
        or file_naming_findings
        or reuse_findings
        or extension_reuse_findings
        or advanced_refactor_findings
        or comment_findings
        or structure_quality_findings
    )
    preflight_gap = bool(
        state_before.get("implementation_preflight_required")
        and not state_before.get("implementation_preflight_complete")
    )
    post_edit_findings = _post_edit_structure_summaries(
        file_naming_findings=file_naming_findings,
        reuse_findings=reuse_findings,
        extension_reuse_findings=extension_reuse_findings,
        structure_findings=structure_findings,
        structure_quality_findings=structure_quality_findings,
        advanced_refactor_findings=advanced_refactor_findings,
        comment_findings=comment_findings,
    )
    _append(update, "changed_paths", paths)
    _append(update, "structure_findings", structure_findings)
    _append(update, "file_naming_findings", file_naming_findings)
    _append(update, "reuse_findings", reuse_findings)
    _append(update, "extension_reuse_findings", extension_reuse_findings)
    _append(update, "advanced_refactor_findings", advanced_refactor_findings)
    _append(update, "comment_findings", comment_findings)
    _append(update, "structure_quality_findings", structure_quality_findings)
    _append(update, "post_edit_structure_findings", post_edit_findings)
    _append(update, "suggested_skills", _structure_suggested_skills(any_findings))
    _append(
        update,
        "suggested_capabilities",
        _structure_suggested_capabilities(
            structure_findings,
            file_naming_findings,
            reuse_findings,
            extension_reuse_findings,
            advanced_refactor_findings,
            comment_findings,
            structure_quality_findings,
        ),
    )
    _append(update, "suggested_gates", ["code-review"] if any_findings else [])
    _set(update, "edit_without_preflight_seen", preflight_gap)
    _set(update, "post_edit_confirmed_preflight_gap", preflight_gap)
    if preflight_gap:
        _append(update, "pre_edit_structure_findings", ["post-edit confirmed edit without implementation preflight"])
    telemetry["changed_paths"] = paths
    telemetry["added_paths"] = sorted(added_paths)
    telemetry["post_edit_structure_findings"] = post_edit_findings
    telemetry["hook_findings"].update(
        {
            "structure_findings": structure_findings,
            "file_naming_findings": file_naming_findings,
            "reuse_findings": reuse_findings,
            "extension_reuse_findings": extension_reuse_findings,
            "advanced_refactor_findings": advanced_refactor_findings,
            "comment_findings": comment_findings,
            "structure_quality_findings": structure_quality_findings,
        }
    )
    if not any_findings:
        return ""
    return _structure_warning_message(
        structure_findings,
        file_naming_findings,
        reuse_findings,
        extension_reuse_findings,
        advanced_refactor_findings,
        comment_findings,
        structure_quality_findings,
    )


def _collect_risk(
    event: dict,
    state_before: dict,
    tool: str,
    paths: list[str],
    command: str,
    update: dict[str, Any],
    telemetry: dict[str, Any],
) -> str:
    command_risk = _command_risk_class(command, paths)
    command_fact = _command_evidence_fact(command, command_risk)
    validation_results = _validation_results(command, event)
    if not (paths or command or validation_results):
        return ""
    path_findings = _risk_findings(paths, "")
    special_findings = _special_command_findings(command, command_risk)
    advisory_findings = [finding for finding in special_findings if finding.get("advisory")]
    required_special_findings = [finding for finding in special_findings if not finding.get("advisory")]
    command_findings = (
        []
        if command_risk in {"production_readonly_diagnostic", "secret_metadata_read"}
        else _risk_findings([], command)
    )
    tool_permission_findings = _tool_permission_findings(tool, command, paths)
    closure_command_findings = (
        command_findings + required_special_findings
        if _command_risk_is_closure_relevant(paths, command)
        else []
    )
    closure_findings = _merge_findings(path_findings + closure_command_findings + tool_permission_findings)
    display_findings = _merge_findings(closure_findings + advisory_findings)
    path_surfaces = [str(finding["name"]) for finding in path_findings]
    command_surfaces = [
        str(finding["name"])
        for finding in [
            *command_findings,
            *required_special_findings,
            *tool_permission_findings,
            *advisory_findings,
        ]
    ]
    closure_surfaces = [str(finding["name"]) for finding in closure_findings]
    meaningful = bool(paths or command or validation_results or closure_surfaces or command_surfaces)
    if not meaningful:
        return ""
    _append(update, "changed_paths", paths)
    _append(update, "risk_surfaces", closure_surfaces)
    _append(update, "changed_path_risk_surfaces", path_surfaces)
    _append(update, "command_risk_surfaces", command_surfaces)
    _append(update, "closure_risk_surfaces", closure_surfaces)
    _append(update, "command_risks", [f"{command_risk}:{command_fact}"])
    _append(update, "validation_results", validation_results)
    _append(update, "suggested_skills", _risk_collect(closure_findings, "skills"))
    _append(update, "suggested_capabilities", _risk_collect(closure_findings, "capabilities"))
    _append(update, "suggested_domain_extensions", _risk_collect(closure_findings, "domain_extensions"))
    _append(update, "suggested_gates", _risk_collect(closure_findings, "gates"))
    _set(update, "tool_permission_sandbox_seen", bool(tool_permission_findings))
    _set(update, "validation_command_seen", _looks_like_validation(command) or None)
    telemetry.update(
        {
            "changed_paths": paths,
            "command_program": summarize_command_program(command),
            "command_risk": command_risk,
            "risk_surfaces": closure_surfaces,
            "changed_path_risk_surfaces": path_surfaces,
            "command_risk_surfaces": command_surfaces,
            "closure_risk_surfaces": closure_surfaces,
            "validation_command_detected": _looks_like_validation(command),
            "validation_results": validation_results,
            "validation_evidence_detected": False,
            "tool_permission_sandbox_seen": bool(tool_permission_findings),
        }
    )
    telemetry["hook_findings"].update(
        {
            "risk_surfaces": closure_surfaces,
            "changed_path_risk_surfaces": path_surfaces,
            "command_risk_surfaces": command_surfaces,
            "closure_risk_surfaces": closure_surfaces,
        }
    )
    if not display_findings:
        return ""
    include_preflight = bool(closure_findings) and not bool(state_before.get("route_preflight_emitted"))
    return _risk_warning_message(display_findings, include_route_preflight=include_preflight)


def _collect_review(
    event: dict,
    state_before: dict,
    update: dict[str, Any],
    telemetry: dict[str, Any],
) -> str:
    classification = classify_event(event)
    prompt_signals = classification.get("prompt_signals", [])
    review_or_repair = classification["stage"] in {"review", "repair"} or "review" in classification["surfaces"]
    diff_seen = is_review_diff_tool(event)
    if not review_or_repair and not diff_seen and not any(
        signal in prompt_signals for signal in ("review_intent", "repair_intent", "repair_followup")
    ):
        return ""
    evidence = extract_read_evidence(event)
    artifact_seen = bool(evidence["paths"]) or diff_seen
    choice_review = evaluate_review_material_choice(event, state_before, repo_root(cwd_from_event(event)))
    choice_blocker = bool(choice_review.get("material") and choice_review.get("blocks"))
    _append(update, "read_paths", evidence["paths"] if artifact_seen else [])
    _append(update, "searched_patterns", evidence["patterns"])
    _append(update, "review_targets", evidence["paths"] if artifact_seen else [])
    _append(update, "review_findings", ["material_sdd_choice_without_user_resolution"] if choice_blocker else [])
    _append(update, "prompt_signals", prompt_signals)
    _append(update, "suggested_skills", ["ai-code-review-refactor"])
    _append(update, "suggested_gates", ["quality-test-gate", "sdd-material-choice-gate"] if choice_blocker else ["quality-test-gate"])
    _append(update, "choice_ids", choice_review.get("evidence", {}).get("choice_ids") or [])
    _append(update, "choice_triggers", choice_review.get("surfaces", []))
    _append(update, "choice_status", [choice_review.get("evidence_result", {}).get("status", "missing")] if choice_review.get("material") else [])
    _append(update, "material_choice_surfaces", choice_review.get("surfaces", []))
    _append(update, "blocked_tool_category", ["review"] if choice_blocker else [])
    _append(update, "bounded_paths", choice_review.get("changed_paths", []))
    _set(update, "turn_stage", classification["stage"])
    _set(update, "review_intent_seen", True)
    _set(update, "review_artifact_seen", artifact_seen)
    _set(update, "review_evidence_seen", artifact_seen)
    _set(update, "repair_evidence_seen", False)
    _set(update, "choice_gate_seen", bool(choice_review.get("material")))
    _set(update, "choice_gate_blocked", choice_blocker)
    _set(update, "choice_resolution_evidence_seen", not choice_blocker and bool(choice_review.get("material")))
    telemetry["review_evidence_seen"] = artifact_seen
    telemetry["hook_findings"]["review_targets"] = evidence["paths"]
    if not review_or_repair and diff_seen and not choice_blocker:
        return ""
    message = _review_message(classification, choice_review)
    if choice_blocker:
        message += "\n\n" + render_review_blocker(choice_review)
    return message


def _merge_state_kwargs(update: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in update.items() if value not in (None, [], (), {})}


def _merge_mapping(target: dict[str, Any], source: dict[str, Any]) -> None:
    for key, value in source.items():
        if isinstance(value, list):
            _append(target, key, value)
        elif value not in (None, "", {}, ()):
            target[key] = value


def _append(target: dict[str, Any], key: str, values: Any) -> None:
    if values is None:
        return
    if isinstance(values, (str, bytes)) or not isinstance(values, (list, tuple, set)):
        values = [values]
    items = [value for value in values if value not in (None, "", [], {})]
    if not items:
        return
    existing = target.setdefault(key, [])
    if not isinstance(existing, list):
        target[key] = items
        return
    existing.extend(items)


def _set(target: dict[str, Any], key: str, value: Any) -> None:
    if value is not None:
        target[key] = value


if __name__ == "__main__":
    raise SystemExit(main())
