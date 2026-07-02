#!/usr/bin/env python3
"""Gate material SDD choices before mutation and final handoff."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from changeforge_common import (
    compact_name,
    cwd_from_event,
    detect_runtime,
    event_name,
    extract_bash_command,
    extract_changed_paths,
    is_pre_tool_use,
    is_stop,
    is_user_prompt_submit,
    load_state,
    merge_state,
    normalize_path,
    read_event,
    repo_root,
    session_id_from_event,
    summarize_command_program,
    tool_name,
    write_telemetry_event,
)
from changeforge_executor_adapter_core import snapshot_from_event_state, state_update_from_snapshot
from changeforge_hook_policy import gate_mode, run_gate_with_policy, should_emit_context
from changeforge_pre_edit_structure_gate import (
    detect_class_or_object_patch,
    detect_new_helper_like_paths,
    detect_public_api_patch,
    extract_added_paths,
    extract_edit_content_text,
    extract_patch_text,
)
from changeforge_runtime_adapters import adapter_for
from changeforge_runtime_route_resolver import CODE_FILE_EXTENSIONS


GATE_NAME = "sdd_material_choice"
EDIT_TOOLS = {"applypatch", "apply_patch", "edit", "write", "multiedit"}
DOC_EXTENSIONS = {".md", ".mdx", ".rst", ".adoc", ".txt"}
LOW_RISK_TEST_PREFIXES = ("tests/", "test/", "__tests__/", "fixtures/", "fixture/")
HIGH_RISK_SURFACES = {
    "public_api_or_export",
    "schema_data_model_migration_rollback",
    "security_auth_permission_privacy",
    "payment_or_irreversible_operation",
    "user_visible_acceptance_behavior",
}
MATERIAL_STATUSES = {"required", "resolved", "not_required", "assumed_with_rationale"}
GENERIC_RATIONALES = {
    "no choice needed",
    "no decision needed",
    "not needed",
    "not required",
    "none",
    "n/a",
    "na",
    "safe assumption",
    "follow existing pattern",
}
SPECIFIC_EVIDENCE_RE = re.compile(
    r"\b(prompt|fixture|explicit user|user selected|user specified|repository convention|"
    r"repo convention|existing pattern|reuse evidence|source|owner|current code|"
    r"existing entrypoint|existing boundary)\b",
    re.IGNORECASE,
)
SAFE_ASSUMPTION_GROUPS = (
    ("local", "same file", "single file", "module-local", "within existing"),
    ("reversible", "revertible", "can be reverted", "easy to revert"),
    ("conventional", "repository convention", "repo convention", "existing pattern"),
    ("acceptance-neutral", "acceptance neutral", "does not change acceptance", "no acceptance change"),
)
PUBLIC_API_RE = re.compile(
    r"\b(export\s+(?:function|class|const|interface|type)|public\s+(?:class|interface|"
    r"function|def)|pub\s+(?:fn|struct|trait)|interface\s+\w+|protocol\s+\w+)\b",
    re.IGNORECASE,
)
PATTERN_RE = re.compile(
    r"\b(adapter|wrapper|factory|strategy|plugin|registry|inheritance|composition|"
    r"extends|implements)\b",
    re.IGNORECASE,
)
CACHE_QUEUE_WORKER_RE = re.compile(r"\b(cache|queue|worker|async job|background job|consumer|producer)\b", re.IGNORECASE)
SECURITY_RE = re.compile(r"\b(auth|authorization|permission|tenant|privacy|secret|token|credential|rbac)\b", re.IGNORECASE)
PAYMENT_RE = re.compile(r"\b(payment|refund|invoice|billing|ledger|irreversible|charge|payout)\b", re.IGNORECASE)
USER_VISIBLE_RE = re.compile(r"\b(user-visible|acceptance|behavior|ux|workflow|response shape|error message)\b", re.IGNORECASE)
DEPENDENCY_RE = re.compile(r"\b(provider|sdk|dependency|package|client library|vendor)\b", re.IGNORECASE)
MIGRATION_COMMAND_RE = re.compile(
    r"\b(migrate|migration|alembic|prisma\s+migrate|knex\s+migrate|rails\s+db:migrate|"
    r"manage\.py\s+migrate|rollback|schema)\b",
    re.IGNORECASE,
)
READ_ONLY_COMMAND_RE = re.compile(
    r"^\s*(?:[A-Z_][A-Z0-9_]*=\S+\s+)*(?:rg|grep|cat|sed|awk|ls|find|git\s+(?:diff|"
    r"status|show|log)|python3?\s+-m\s+unittest|pytest|npm\s+test|pnpm\s+test)\b",
    re.IGNORECASE,
)


def main() -> int:
    return run_gate_with_policy(GATE_NAME, _main, fail_closed=_fail_closed)


def _fail_closed(exc: Exception) -> None:
    runtime = detect_runtime({})
    adapter_for(runtime).emit_permission_decision(
        "block",
        f"ChangeForge SDD Material Choice Gate failed closed: {exc}",
    )


def _main() -> int:
    event = read_event()
    if not event:
        return 0
    mode = gate_mode(GATE_NAME)
    if mode == "off":
        return 0
    runtime = detect_runtime(event)
    repo = repo_root(cwd_from_event(event))
    state = load_state(repo)
    if is_user_prompt_submit(event):
        return _handle_user_prompt(event, runtime, repo, mode)
    if is_pre_tool_use(event):
        return _handle_pre_tool(event, runtime, repo, state, mode)
    if is_stop(event):
        return _handle_stop(event, runtime, repo, state, mode)
    return 0


def _handle_user_prompt(event: dict, runtime: str, repo: Path, mode: str) -> int:
    text = _event_text(event)
    if not _prompt_may_need_choice(text):
        return 0
    message = (
        "ChangeForge SDD Material Choice Gate: advisory\n"
        "- Material design choices are blocking by default before mutation.\n"
        "- If the request could change public API, module boundaries, data/security, "
        "migration, rollback, payment, user-visible behavior, or dependency/provider "
        "selection, record changeforge_sdd_choice or design_decision_points before editing.\n"
        "- If the prompt already decides the only valid path, record that as resolution_evidence."
    )
    if mode not in {"monitor", "off"} and should_emit_context(GATE_NAME):
        adapter_for(runtime).emit_context(event_name(event) or "UserPromptSubmit", message)
    write_telemetry_event(
        repo,
        runtime=runtime,
        hook_name="sdd_material_choice_gate",
        event_name=event_name(event) or "UserPromptSubmit",
        mode=mode,
        session_id=session_id_from_event(event),
        cwd=cwd_from_event(event),
        choice_gate_seen=False,
    )
    return 0


def _handle_pre_tool(event: dict, runtime: str, repo: Path, state: dict, mode: str) -> int:
    result = evaluate_material_choice(event, state, repo, stage="PreToolUse")
    if not result["material"]:
        return 0
    _record_result(event, runtime, repo, state, mode, result)
    if not result["blocks"]:
        return 0
    if mode == "monitor":
        return 0
    message = render_block_message(result, blocked=mode == "block")
    adapter = adapter_for(runtime)
    if mode == "block" and result["blocks"]:
        adapter.emit_permission_decision("block", message)
    elif should_emit_context(GATE_NAME):
        adapter.emit_context(event_name(event) or "PreToolUse", message)
    return 0


def _handle_stop(event: dict, runtime: str, repo: Path, state: dict, mode: str) -> int:
    result = evaluate_stop_material_choice(event, state, repo)
    if not result["material"]:
        return 0
    _record_result(event, runtime, repo, state, mode, result)
    if not result["blocks"]:
        return 0
    if mode == "monitor":
        return 0
    message = render_block_message(result, blocked=mode == "block")
    adapter = adapter_for(runtime)
    if mode == "block" and result["blocks"]:
        adapter.emit_stop(message, continue_turn=True)
    elif should_emit_context(GATE_NAME):
        adapter.emit_stop(message, continue_turn=False)
    return 0


def evaluate_material_choice(
    event: dict,
    state: dict | None = None,
    repo: Path | None = None,
    *,
    stage: str = "PreToolUse",
) -> dict:
    """Return material-choice gate facts without emitting runtime output."""
    state = state if isinstance(state, dict) else {}
    tool = compact_name(tool_name(event))
    if stage == "PreToolUse" and tool not in EDIT_TOOLS and tool != "bash":
        return _result(material=False)
    command = extract_bash_command(event)
    if tool == "bash" and not _is_material_bash_mutation(command):
        return _result(material=False, tool_category="bash")
    patch_text = extract_patch_text(event)
    content_text = extract_edit_content_text(event)
    changed_paths = [normalize_path(path) for path in extract_changed_paths(event)]
    added_paths = extract_added_paths(event, repo=repo) if stage == "PreToolUse" else []
    paths = _unique([*changed_paths, *added_paths])
    if _is_low_risk_non_choice(paths, patch_text, content_text, command):
        return _result(material=False, changed_paths=paths, tool_category=tool or "unknown")
    surfaces = material_choice_surfaces(paths, added_paths, patch_text, content_text, command)
    if not surfaces:
        return _result(material=False, changed_paths=paths, tool_category=tool or "unknown")
    evidence = extract_choice_evidence(_assistant_text_from_event(event))
    evidence_result = evaluate_choice_evidence(evidence, surfaces)
    blocks = not evidence_result["accepted"]
    return _result(
        material=True,
        blocks=blocks,
        changed_paths=paths,
        added_paths=added_paths,
        surfaces=surfaces,
        evidence=evidence,
        evidence_result=evidence_result,
        tool_category=tool or "unknown",
        stage=stage,
    )


def evaluate_stop_material_choice(event: dict, state: dict | None, repo: Path | None = None) -> dict:
    """Return Stop-stage material-choice facts using current state and final text."""
    state = state if isinstance(state, dict) else {}
    final_evidence = extract_choice_evidence(_assistant_text_from_event(event))
    existing_surfaces = _string_list(state.get("material_choice_surfaces"))
    state_paths = _string_list(state.get("bounded_paths")) or _string_list(state.get("changed_paths"))
    if not existing_surfaces:
        existing_surfaces = material_choice_surfaces(state_paths, [], "", "", "")
    if not existing_surfaces:
        return _result(material=False, changed_paths=state_paths, stage="Stop", tool_category="stop")
    evidence_result = evaluate_choice_evidence(final_evidence, existing_surfaces)
    previously_resolved = bool(state.get("choice_resolution_evidence_seen"))
    blocks = not previously_resolved and not evidence_result["accepted"]
    return _result(
        material=True,
        blocks=blocks,
        changed_paths=state_paths,
        added_paths=[],
        surfaces=existing_surfaces,
        evidence=final_evidence,
        evidence_result=evidence_result if not previously_resolved else {"accepted": True, "reason": "state already has resolution evidence"},
        tool_category="stop",
        stage="Stop",
    )


def evaluate_review_material_choice(event: dict, state: dict | None, repo: Path | None = None) -> dict:
    """Return review/repair blocker facts for material changes without resolution."""
    state = state if isinstance(state, dict) else {}
    event_paths = [normalize_path(path) for path in extract_changed_paths(event)]
    paths = _unique([*event_paths, *_string_list(state.get("changed_paths")), *_string_list(state.get("bounded_paths"))])
    patch_text = extract_patch_text(event)
    content_text = extract_edit_content_text(event)
    surfaces = material_choice_surfaces(paths, [], patch_text, content_text, "")
    if not surfaces:
        return _result(material=False, changed_paths=paths, stage="review", tool_category="review")
    evidence = extract_choice_evidence(_assistant_text_from_event(event))
    evidence_result = evaluate_choice_evidence(evidence, surfaces)
    resolved = bool(state.get("choice_resolution_evidence_seen")) or evidence_result["accepted"]
    return _result(
        material=True,
        blocks=not resolved,
        changed_paths=paths,
        surfaces=surfaces,
        evidence=evidence,
        evidence_result=evidence_result if not resolved else {"accepted": True, "reason": "resolution evidence available"},
        tool_category="review",
        stage="review",
    )


def material_choice_surfaces(
    paths: list[str],
    added_paths: list[str],
    patch_text: str,
    content_text: str,
    command: str,
) -> list[str]:
    """Detect material SDD choice surfaces from bounded path/text/command facts."""
    text = "\n".join([patch_text or "", content_text or "", command or ""])
    lowered_paths = " ".join(paths).casefold()
    surfaces: list[str] = []
    code_paths = [path for path in paths if Path(path).suffix in CODE_FILE_EXTENSIONS]
    if detect_public_api_patch(patch_text, content_text) or PUBLIC_API_RE.search(text) or "/api/" in lowered_paths:
        surfaces.append("public_api_or_export")
    if any(path in code_paths for path in added_paths) or _new_boundary_path(paths):
        surfaces.append("new_module_directory_service_or_boundary")
    if detect_new_helper_like_paths(paths):
        surfaces.append("shared_utility_common_helper_or_owner_boundary")
    if detect_class_or_object_patch(patch_text, content_text) or PATTERN_RE.search(text):
        surfaces.append("object_hierarchy_pattern_or_extension_point")
    if CACHE_QUEUE_WORKER_RE.search(text) or any(token in lowered_paths for token in ("cache", "queue", "worker")):
        surfaces.append("cache_queue_worker_or_async_job")
    if MIGRATION_COMMAND_RE.search(text) or any(token in lowered_paths for token in ("migration", "schema", "models", "model")):
        surfaces.append("schema_data_model_migration_rollback")
    if SECURITY_RE.search(text) or any(token in lowered_paths for token in ("auth", "permission", "tenant", "privacy")):
        surfaces.append("security_auth_permission_privacy")
    if PAYMENT_RE.search(text) or any(token in lowered_paths for token in ("payment", "billing", "ledger")):
        surfaces.append("payment_or_irreversible_operation")
    if USER_VISIBLE_RE.search(text):
        surfaces.append("user_visible_acceptance_behavior")
    if DEPENDENCY_RE.search(text) or _dependency_path(paths):
        surfaces.append("external_dependency_provider_sdk")
    return _unique(surfaces)


def extract_choice_evidence(text: str) -> dict[str, Any]:
    """Parse bounded SDD choice evidence from assistant-visible text."""
    result: dict[str, Any] = {
        "present": False,
        "statuses": [],
        "choice_ids": [],
        "triggers": [],
        "blocking": False,
        "resolution_evidence": "",
        "decision": "",
        "why_user_choice_is_needed": "",
        "recommended_option": "",
        "safe_default_if_user_unavailable": "",
        "residual_risk": "",
        "option_count": 0,
        "rationale_text": "",
    }
    if not isinstance(text, str) or not text.strip():
        return result
    for payload in _json_payloads(text):
        _merge_json_evidence(result, payload)
    block = _choice_block(text)
    if block:
        result["present"] = True
        result["statuses"].extend(_field_values(block, ("status", "user_choice_status")))
        result["choice_ids"].extend(_field_values(block, ("choice_id", "id")))
        result["triggers"].extend(_field_values(block, ("trigger",)))
        result["blocking"] = result["blocking"] or bool(re.search(r"\bblocking:\s*true\b", block, re.I))
        for target, keys in (
            ("resolution_evidence", ("resolution_evidence",)),
            ("decision", ("decision",)),
            ("why_user_choice_is_needed", ("why_user_choice_is_needed",)),
            ("recommended_option", ("recommended_option", "resolved_option")),
            ("safe_default_if_user_unavailable", ("safe_default_if_user_unavailable",)),
            ("residual_risk", ("residual_risk",)),
        ):
            if not result[target]:
                values = _field_values(block, keys)
                result[target] = values[0] if values else ""
        result["option_count"] = max(result["option_count"], len(re.findall(r"^\s*-\s*label:\s*.+$", block, re.M)))
        result["rationale_text"] = _bounded_rationale(block)
    result["statuses"] = _unique([status.casefold() for status in result["statuses"] if status.casefold() in MATERIAL_STATUSES])
    result["choice_ids"] = _unique(result["choice_ids"])
    result["triggers"] = _unique(result["triggers"])
    if not result["rationale_text"]:
        result["rationale_text"] = _bounded_rationale(
            " ".join(
                str(result.get(key, ""))
                for key in (
                    "resolution_evidence",
                    "decision",
                    "why_user_choice_is_needed",
                    "safe_default_if_user_unavailable",
                    "residual_risk",
                )
            )
        )
    return result


def evaluate_choice_evidence(evidence: dict[str, Any], surfaces: list[str]) -> dict[str, Any]:
    if not evidence.get("present"):
        return {"accepted": False, "status": "missing", "reason": "no structured SDD choice evidence"}
    statuses = _string_list(evidence.get("statuses"))
    status = statuses[0] if statuses else ""
    if status == "required" and evidence.get("blocking"):
        return {"accepted": False, "status": status, "reason": "blocking required choice needs user selection"}
    if status == "resolved":
        value = str(evidence.get("resolution_evidence") or "").strip()
        accepted = bool(value and value.casefold() not in {"not resolved", "none", "n/a", "na"})
        return {"accepted": accepted, "status": status, "reason": "resolved evidence present" if accepted else "resolved choice lacks resolution_evidence"}
    if status == "not_required":
        rationale = str(evidence.get("resolution_evidence") or evidence.get("rationale_text") or "")
        accepted = _specific_no_choice_evidence(rationale)
        return {"accepted": accepted, "status": status, "reason": "concrete no-choice evidence present" if accepted else "not_required lacks concrete prompt/fixture/user/repository/reuse evidence"}
    if status == "assumed_with_rationale":
        rationale = str(evidence.get("rationale_text") or "")
        high_risk = [surface for surface in surfaces if surface in HIGH_RISK_SURFACES]
        if high_risk:
            return {"accepted": False, "status": status, "reason": "assumed_with_rationale cannot cover high-risk material choice"}
        accepted = _safe_assumption_rationale_ok(rationale)
        return {"accepted": accepted, "status": status, "reason": "safe low-risk assumption evidence present" if accepted else "safe assumption lacks local/reversible/conventional/acceptance-neutral rationale"}
    return {"accepted": False, "status": status or "missing", "reason": "choice status is missing or unsupported"}


def render_block_message(result: dict, *, blocked: bool = True) -> str:
    title = "ChangeForge SDD Material Choice Gate: BLOCKED" if blocked else "ChangeForge SDD Material Choice Gate: advisory"
    choice_id = (result["evidence"].get("choice_ids") or ["sdd-material-choice"])[0]
    trigger = ", ".join(result["surfaces"][:5]) or "material design choice"
    decision = result["evidence"].get("decision") or "Choose the design direction before mutation or handoff."
    reason = result["evidence_result"].get("reason", "missing resolved choice evidence")
    return (
        f"{title}\n\n"
        "Why blocked:\n"
        f"- Material SDD choice detected at {result['stage']} for: {trigger}.\n"
        f"- {reason}.\n"
        "- No qualified resolved/not_required/assumed_with_rationale evidence is available.\n\n"
        "Required user choice:\n"
        f"- choice_id: {choice_id}\n"
        f"- trigger: {trigger}\n"
        f"- decision: {decision}\n"
        "- why user choice is needed: the wrong answer can change contract, architecture, data/security, "
        "acceptance, or user-visible behavior.\n\n"
        "Options:\n"
        "A. Reuse the existing owner, boundary, or convention.\n"
        "   Pros:\n"
        "   - Minimizes compatibility and ownership risk.\n"
        "   Cons:\n"
        "   - May be less explicit if the user wanted a new public surface.\n"
        "B. Add the new boundary, abstraction, dependency, migration, or behavior surface.\n"
        "   Pros:\n"
        "   - Makes the new capability explicit.\n"
        "   Cons:\n"
        "   - Creates a new contract, ownership, migration, or rollback burden.\n\n"
        "Recommended option:\n"
        "- A, unless the user explicitly wants the broader new surface.\n\n"
        "What to ask the user:\n"
        "\"我需要你选择一个设计方向后再继续：A 复用现有 owner/boundary/convention，"
        "或 B 新增边界/抽象/API/迁移/依赖。我推荐 A，因为它降低兼容和所有权风险。"
        "请选择 A/B，或补充约束。\"\n\n"
        "How to continue after user chooses:\n"
        "- Record resolution_evidence as \"user selected A/B\" or cite the prompt/repository convention that decides it.\n"
        "- Continue only within the selected option."
    )


def render_review_blocker(result: dict) -> str:
    surfaces = ", ".join(result.get("surfaces", [])[:5]) or "material SDD choice"
    return (
        "Review blocker:\n"
        "- Implementation made a material SDD choice without user resolution.\n"
        f"- Detected surface: {surfaces}.\n"
        "- This is not a normal code issue; the agent silently made a user-owned design choice.\n"
        "- Required action: ask user to choose A/B before accepting or repairing this implementation."
    )


def _record_result(event: dict, runtime: str, repo: Path, state: dict, mode: str, result: dict) -> None:
    snapshot = snapshot_from_event_state(
        event,
        state,
        classification={
            "stage": result.get("stage", ""),
            "paths": result.get("changed_paths", []),
            "tool": result.get("tool_category", ""),
        },
        read_evidence={"paths": state.get("read_paths", []), "patterns": state.get("searched_patterns", [])},
        gate_name=GATE_NAME,
        gate_mode=mode,
        gate_facts={"surfaces": result["surfaces"], "blocks": result["blocks"]},
    )
    snapshot_update = state_update_from_snapshot(snapshot)
    paths = result.get("changed_paths", [])
    snapshot_update.pop("changed_paths", None)
    evidence = result.get("evidence", {})
    evidence_result = result.get("evidence_result", {})
    status = evidence_result.get("status") or "missing"
    phase_findings = _phase_review_findings_for_result(result)
    merge_state(
        repo,
        runtime,
        **snapshot_update,
        changed_paths=paths,
        choice_gate_seen=True,
        choice_gate_blocked=bool(result.get("blocks")),
        choice_resolution_evidence_seen=bool(evidence_result.get("accepted")),
        choice_ids=evidence.get("choice_ids") or ["sdd-material-choice"],
        choice_triggers=evidence.get("triggers") or result.get("surfaces", []),
        choice_status=[status],
        phase_review_findings=phase_findings,
        phase_repair_required=bool(phase_findings),
        material_choice_surfaces=result.get("surfaces", []),
        blocked_tool_category=[result.get("tool_category", "unknown")],
        bounded_paths=paths,
        suggested_capabilities=["implementation-structure-design", "agent-execution-discipline"],
        suggested_gates=["sdd-material-choice-gate"],
    )
    write_telemetry_event(
        repo,
        runtime=runtime,
        hook_name="sdd_material_choice_gate",
        event_name=event_name(event) or result.get("stage", ""),
        mode=mode,
        session_id=session_id_from_event(event),
        cwd=cwd_from_event(event),
        tool_name=tool_name(event),
        normalized_events=snapshot_update["normalized_events"],
        changed_paths=paths,
        deleted_paths=snapshot_update["deleted_paths"],
        generated_paths=snapshot_update["generated_paths"],
        external_file_changes=snapshot_update["external_file_changes"],
        config_changes=snapshot_update["config_changes"],
        command_program=summarize_command_program(extract_bash_command(event)),
        hook_findings={"material_choice_surfaces": result.get("surfaces", [])},
        choice_gate_seen=True,
        choice_gate_blocked=bool(result.get("blocks")),
        choice_resolution_evidence_seen=bool(evidence_result.get("accepted")),
        choice_ids=evidence.get("choice_ids") or ["sdd-material-choice"],
        choice_triggers=evidence.get("triggers") or result.get("surfaces", []),
        choice_status=[status],
        phase_review_findings=phase_findings,
        phase_repair_required=bool(phase_findings),
        material_choice_surfaces=result.get("surfaces", []),
        blocked_tool_category=[result.get("tool_category", "unknown")],
        bounded_paths=paths,
        suggested_capabilities=["implementation-structure-design", "agent-execution-discipline"],
        suggested_gates=["sdd-material-choice-gate"],
    )


def _phase_review_findings_for_result(result: dict) -> list[dict[str, Any]]:
    if not result.get("blocks"):
        return []
    surfaces = result.get("surfaces") or []
    reason = str((result.get("evidence_result") or {}).get("reason") or "missing SDD material choice resolution")
    return [
        {
            "finding_id": "sdd-material-choice",
            "phase": "sdd",
            "severity": "high",
            "evidence": f"{reason}: {', '.join(str(item) for item in surfaces[:6])}",
            "required_fix": "add design_decision_points or changeforge_sdd_choice with concrete resolution evidence",
            "blocks_next_stage": True,
            "resolved": False,
        }
    ]


def _is_material_bash_mutation(command: str) -> bool:
    if not command or READ_ONLY_COMMAND_RE.search(command):
        return False
    return bool(MIGRATION_COMMAND_RE.search(command) or SECURITY_RE.search(command) or PAYMENT_RE.search(command))


def _is_low_risk_non_choice(paths: list[str], patch_text: str, content_text: str, command: str) -> bool:
    if command and READ_ONLY_COMMAND_RE.search(command):
        return True
    if paths and all(_is_docs_path(path) or _is_test_path(path) for path in paths):
        return True
    text = "\n".join([patch_text or "", content_text or ""]).strip()
    if not text and paths and all(_is_docs_path(path) for path in paths):
        return True
    if text and len(text) < 180 and re.search(r"\b(typo|format|formatting|whitespace|spelling)\b", text, re.I):
        return True
    return False


def _prompt_may_need_choice(text: str) -> bool:
    if not isinstance(text, str):
        return False
    lowered = text.casefold()[:2000]
    return any(
        token in lowered
        for token in (
            "new public api",
            "shared utility",
            "architecture",
            "refactor",
            "optimize",
            "enhance",
            "migration",
            "auth",
            "permission",
            "schema",
            "dependency",
            "provider",
        )
    )


def _event_text(event: dict) -> str:
    values: list[str] = []
    for key in ("prompt", "message", "userPrompt", "user_prompt"):
        value = event.get(key)
        if isinstance(value, str):
            values.append(value[:2000])
    return "\n".join(values)


def _assistant_text_from_event(event: dict) -> str:
    texts: list[str] = []
    for key in (
        "message",
        "assistant_message",
        "assistantMessage",
        "last_assistant_message",
        "lastAssistantMessage",
        "response",
        "finalResponse",
        "final_response",
    ):
        value = event.get(key)
        if isinstance(value, str):
            texts.append(value)
    transcript = event.get("transcript_path") or event.get("transcriptPath")
    if isinstance(transcript, str) and transcript.strip():
        tail = _transcript_tail(transcript)
        if tail:
            texts.append(tail)
    return "\n".join(texts)


def _transcript_tail(path: str) -> str:
    try:
        transcript_path = Path(path).expanduser()
        with transcript_path.open("rb") as file:
            try:
                file.seek(0, 2)
                size = file.tell()
                file.seek(max(size - 1_000_000, 0))
            except OSError:
                pass
            lines = file.read().decode("utf-8", errors="replace").splitlines()
    except Exception:
        return ""
    for line in reversed(lines[-80:]):
        text = line.strip()
        if not text:
            continue
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return text
        if isinstance(payload, dict) and payload.get("role") == "assistant":
            content = payload.get("content")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                return "\n".join(
                    item.get("text", "")
                    for item in content
                    if isinstance(item, dict) and isinstance(item.get("text"), str)
                )
    return ""


def _choice_block(text: str) -> str:
    markers = ("changeforge_sdd_choice:", "design_decision_points:")
    lowered = text.casefold()
    starts = [lowered.find(marker) for marker in markers if lowered.find(marker) != -1]
    if not starts:
        return ""
    start = min(starts)
    segment = text[start : start + 5000]
    fence_end = segment.find("```", 3)
    if fence_end != -1:
        segment = segment[:fence_end]
    return segment


def _json_payloads(text: str) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for match in re.finditer(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S | re.I):
        try:
            value = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            payloads.append(value)
    return payloads


def _merge_json_evidence(result: dict[str, Any], payload: dict[str, Any]) -> None:
    candidates: list[dict[str, Any]] = []
    direct = payload.get("changeforge_sdd_choice")
    if isinstance(direct, dict):
        candidates.append(direct)
    points = payload.get("design_decision_points")
    if isinstance(points, list):
        candidates.extend(point for point in points if isinstance(point, dict))
    process_points = (
        payload.get("process_trace", {})
        if isinstance(payload.get("process_trace"), dict)
        else {}
    )
    sdd = process_points.get("sdd") if isinstance(process_points.get("sdd"), dict) else {}
    if isinstance(sdd.get("design_decision_points"), list):
        candidates.extend(point for point in sdd["design_decision_points"] if isinstance(point, dict))
    for candidate in candidates:
        result["present"] = True
        status = str(candidate.get("status") or candidate.get("user_choice_status") or "").strip()
        if status:
            result["statuses"].append(status)
        choice_id = str(candidate.get("choice_id") or candidate.get("id") or "").strip()
        if choice_id:
            result["choice_ids"].append(choice_id)
        trigger = str(candidate.get("trigger") or "").strip()
        if trigger:
            result["triggers"].append(trigger)
        result["blocking"] = result["blocking"] or candidate.get("blocking") is True
        for key in (
            "resolution_evidence",
            "decision",
            "why_user_choice_is_needed",
            "recommended_option",
            "safe_default_if_user_unavailable",
            "residual_risk",
        ):
            if not result.get(key) and str(candidate.get(key) or "").strip():
                result[key] = str(candidate.get(key)).strip()
        options = candidate.get("options")
        if isinstance(options, list):
            result["option_count"] = max(result["option_count"], len(options))


def _field_values(block: str, keys: tuple[str, ...]) -> list[str]:
    values: list[str] = []
    key_re = "|".join(re.escape(key) for key in keys)
    for match in re.finditer(rf"^\s*(?:-\s*)?(?:{key_re})\s*:\s*(.+?)\s*$", block, re.M | re.I):
        value = match.group(1).strip().strip("'\"")
        if value and value not in {"[]", "{}"}:
            values.append(value[:300])
    return values


def _bounded_rationale(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", str(text or "")).strip()
    return cleaned[:1000]


def _specific_no_choice_evidence(rationale: str) -> bool:
    lowered = rationale.strip().casefold().strip(".")
    if not lowered or lowered in GENERIC_RATIONALES or len(lowered.split()) < 5:
        return False
    if not SPECIFIC_EVIDENCE_RE.search(lowered):
        return False
    if lowered == "follow existing pattern" or lowered == "safe assumption":
        return False
    return True


def _safe_assumption_rationale_ok(text: str) -> bool:
    lowered = text.casefold()
    return all(any(marker in lowered for marker in group) for group in SAFE_ASSUMPTION_GROUPS)


def _new_boundary_path(paths: list[str]) -> bool:
    for path in paths:
        normalized = path.casefold()
        tokens = set(re.split(r"[^a-z0-9]+", normalized))
        if Path(normalized).suffix not in CODE_FILE_EXTENSIONS:
            continue
        if tokens & {"service", "services", "module", "modules", "package", "packages", "common", "shared", "utils", "adapter", "adapters", "api", "provider", "client"}:
            return True
    return False


def _dependency_path(paths: list[str]) -> bool:
    names = {
        "package.json",
        "pnpm-lock.yaml",
        "package-lock.json",
        "yarn.lock",
        "requirements.txt",
        "pyproject.toml",
        "go.mod",
        "cargo.toml",
        "gemfile",
    }
    return any(Path(path).name.casefold() in names for path in paths)


def _is_docs_path(path: str) -> bool:
    normalized = normalize_path(path).casefold()
    return normalized.startswith(("docs/", "documentation/")) or Path(normalized).suffix in DOC_EXTENSIONS


def _is_test_path(path: str) -> bool:
    normalized = normalize_path(path).casefold()
    return normalized.startswith(LOW_RISK_TEST_PREFIXES) or "/tests/" in normalized or "/test/" in normalized


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        item = str(value).strip()
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _result(
    *,
    material: bool,
    blocks: bool = False,
    changed_paths: list[str] | None = None,
    added_paths: list[str] | None = None,
    surfaces: list[str] | None = None,
    evidence: dict[str, Any] | None = None,
    evidence_result: dict[str, Any] | None = None,
    tool_category: str = "unknown",
    stage: str = "PreToolUse",
) -> dict:
    return {
        "material": bool(material),
        "blocks": bool(blocks),
        "changed_paths": _unique(changed_paths or []),
        "added_paths": _unique(added_paths or []),
        "surfaces": _unique(surfaces or []),
        "evidence": evidence if isinstance(evidence, dict) else {"present": False, "choice_ids": [], "triggers": []},
        "evidence_result": evidence_result if isinstance(evidence_result, dict) else {"accepted": False, "status": "missing", "reason": "not evaluated"},
        "tool_category": tool_category,
        "stage": stage,
    }


if __name__ == "__main__":
    raise SystemExit(main())
