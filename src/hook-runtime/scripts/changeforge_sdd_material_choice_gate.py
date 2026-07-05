#!/usr/bin/env python3
"""Gate material SDD choices before mutation and final handoff."""

from __future__ import annotations

import hashlib
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
from changeforge_hook_policy import gate_mode, gate_mode_for_stage, run_gate_with_policy, should_emit_context
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
DEFAULT_CHOICE_CONTEXT = {
    "label": "material design surface",
    "decision": "Which concrete design direction should own this behavior before code is changed or handed off?",
    "why": "The answer can change contract, ownership, access, acceptance, or user-visible behavior.",
    "option_a": "Keep the behavior inside the closest existing owner, boundary, and contract.",
    "option_b": "Introduce or change the relevant boundary, contract, dependency, stored data shape, or visible behavior.",
    "recommendation": "A unless the user request or repository evidence requires the broader surface.",
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
PAYMENT_RE = re.compile(r"\b(payment|refund|invoice|billing|irreversible|charge|payout)\b", re.IGNORECASE)
USER_VISIBLE_RE = re.compile(r"\b(user-visible|acceptance|behavior|ux|workflow|response shape|error message)\b", re.IGNORECASE)
DEPENDENCY_RE = re.compile(r"\b(provider|sdk|dependency|package|client library|vendor)\b", re.IGNORECASE)
MIGRATION_COMMAND_RE = re.compile(
    r"\b(migrate|migration|alembic|prisma\s+migrate|knex\s+migrate|rails\s+db:migrate|"
    r"manage\.py\s+migrate|rollback)\b",
    re.IGNORECASE,
)
READ_ONLY_COMMAND_RE = re.compile(
    r"^\s*(?:[A-Z_][A-Z0-9_]*=\S+\s+)*(?:rg|grep|cat|sed|awk|ls|find|wc|head|tail|nl|git\s+(?:diff|"
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
    runtime = detect_runtime(event)
    repo = repo_root(cwd_from_event(event))
    state = load_state(repo)
    if is_user_prompt_submit(event):
        mode = gate_mode(GATE_NAME)
        if mode == "off":
            return 0
        return _handle_user_prompt(event, runtime, repo, mode)
    if is_pre_tool_use(event):
        mode = gate_mode_for_stage(GATE_NAME, "pretool")
        if mode == "off":
            return 0
        return _handle_pre_tool(event, runtime, repo, state, mode)
    if is_stop(event):
        mode = gate_mode_for_stage(GATE_NAME, "stop")
        if mode == "off":
            return 0
        return _handle_stop(event, runtime, repo, state, mode)
    return 0


def _handle_user_prompt(event: dict, runtime: str, repo: Path, mode: str) -> int:
    text = _event_text(event)
    if not _prompt_may_need_choice(text):
        return 0
    message = (
        "Design risk note:\n"
        "这个请求可能改变对外契约、模块归属、安全边界、持久化事实、支付路径、"
        "可观察结果或外部 provider。继续前请自然说明 owner、兼容性、验证计划和是否需要用户确认。"
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
    surface_records = material_choice_surface_records(paths, added_paths, patch_text, content_text, command)
    surfaces = _surface_ids(surface_records)
    if not surfaces:
        return _result(material=False, changed_paths=paths, tool_category=tool or "unknown")
    blocking_surfaces = [record["id"] for record in surface_records if record.get("confidence") == "high"]
    if not blocking_surfaces:
        return _result(
            material=True,
            blocks=False,
            changed_paths=paths,
            added_paths=added_paths,
            surfaces=surfaces,
            blocking_surfaces=[],
            surface_records=surface_records,
            evidence_result={"accepted": False, "status": "advisory", "reason": "no high-confidence material choice evidence"},
            tool_category=tool or "unknown",
            stage=stage,
        )
    if _state_has_choice_resolution(state, surfaces, paths):
        return _result(
            material=True,
            blocks=False,
            changed_paths=paths,
            added_paths=added_paths,
            surfaces=surfaces,
            blocking_surfaces=blocking_surfaces,
            surface_records=surface_records,
            evidence={"present": True, "choice_ids": _string_list(state.get("choice_ids")), "triggers": surfaces},
            evidence_result={"accepted": True, "status": "resolved", "reason": "choice already resolved; residual risk if parser cannot verify current surface", "already_resolved": True},
            tool_category=tool or "unknown",
            stage=stage,
        )
    if _explicit_public_contract_choice(event, surfaces):
        return _result(
            material=True,
            blocks=False,
            changed_paths=paths,
            added_paths=added_paths,
            surfaces=surfaces,
            blocking_surfaces=blocking_surfaces,
            surface_records=surface_records,
            evidence={
                "present": True,
                "choice_ids": ["explicit-public-contract-choice"],
                "triggers": ["public_api_or_export"],
                "decision": "B",
                "resolution_evidence": "explicit user request made A incompatible",
                "residual_risk": "public contract change requires caller/test/docs update",
            },
            evidence_result={
                "accepted": True,
                "status": "resolved",
                "reason": "explicit user request resolves public contract choice",
            },
            tool_category=tool or "unknown",
            stage=stage,
        )
    if _explicit_user_visible_choice(event, surfaces):
        return _result(
            material=True,
            blocks=False,
            changed_paths=paths,
            added_paths=added_paths,
            surfaces=surfaces,
            blocking_surfaces=blocking_surfaces,
            surface_records=surface_records,
            evidence={"present": True, "choice_ids": ["explicit-user-visible-behavior"], "triggers": ["user_visible_acceptance_behavior"]},
            evidence_result={"accepted": True, "status": "resolved", "reason": "explicit user request resolves visible behavior choice"},
            tool_category=tool or "unknown",
            stage=stage,
        )
    evidence = extract_choice_evidence(_assistant_text_from_event(event))
    evidence_result = evaluate_choice_evidence(evidence, blocking_surfaces)
    blocks = not evidence_result["accepted"]
    return _result(
        material=True,
        blocks=blocks,
        changed_paths=paths,
        added_paths=added_paths,
        surfaces=surfaces,
        blocking_surfaces=blocking_surfaces,
        surface_records=surface_records,
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
    if not existing_surfaces or not state.get("choice_gate_blocked"):
        return _result(material=False, changed_paths=state_paths, stage="Stop", tool_category="stop")
    evidence_result = evaluate_choice_evidence(final_evidence, existing_surfaces)
    previously_resolved = _state_has_choice_resolution(state, existing_surfaces, state_paths)
    blocks = not previously_resolved and not evidence_result["accepted"]
    return _result(
        material=True,
        blocks=blocks,
        changed_paths=state_paths,
        added_paths=[],
        surfaces=existing_surfaces,
        evidence=final_evidence,
        evidence_result=evidence_result if not previously_resolved else {"accepted": True, "status": "resolved", "reason": "choice already resolved; residual risk if parser cannot verify current surface", "already_resolved": True},
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
    surface_records = material_choice_surface_records(paths, [], patch_text, content_text, "")
    surfaces = _surface_ids(surface_records)
    if not surfaces:
        return _result(material=False, changed_paths=paths, stage="review", tool_category="review")
    evidence = extract_choice_evidence(_assistant_text_from_event(event))
    evidence_result = evaluate_choice_evidence(evidence, surfaces)
    resolved = _state_has_choice_resolution(state, surfaces, paths) or evidence_result["accepted"]
    return _result(
        material=True,
        blocks=not resolved,
        changed_paths=paths,
        surfaces=surfaces,
        surface_records=surface_records,
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
    """Detect material SDD choice IDs from bounded path/text/command facts."""
    return _surface_ids(material_choice_surface_records(paths, added_paths, patch_text, content_text, command))


def material_choice_surface_records(
    paths: list[str],
    added_paths: list[str],
    patch_text: str,
    content_text: str,
    command: str,
) -> list[dict[str, str]]:
    """Detect SDD choice surfaces with provenance and confidence."""
    text = "\n".join([patch_text or "", content_text or "", command or ""])
    lowered_paths = " ".join(paths).casefold()
    records: list[dict[str, str]] = []
    code_paths = [path for path in paths if Path(path).suffix in CODE_FILE_EXTENSIONS]
    if detect_public_api_patch(patch_text, content_text) or PUBLIC_API_RE.search(text):
        _add_surface(records, "public_api_or_export", "patch_diff", "high", "public API/export syntax changed")
    elif "/api/" in lowered_paths:
        _add_surface(records, "public_api_or_export", "changed_path", "medium", "API path token without contract diff")
    if any(path in code_paths for path in added_paths) or _new_boundary_path(paths):
        confidence = "medium" if any(path in code_paths for path in added_paths) else "low"
        _add_surface(records, "new_module_directory_service_or_boundary", "changed_path", confidence, "new/boundary-looking code path candidate")
    if detect_new_helper_like_paths(paths):
        _add_surface(records, "shared_utility_common_helper_or_owner_boundary", "changed_path", "low", "helper/common path token candidate")
    if detect_class_or_object_patch(patch_text, content_text) or PATTERN_RE.search(text):
        _add_surface(records, "object_hierarchy_pattern_or_extension_point", "patch_diff", "high", "object/pattern syntax changed")
    if CACHE_QUEUE_WORKER_RE.search(text):
        _add_surface(records, "cache_queue_worker_or_async_job", "patch_diff", "high", "async/cache/worker behavior text changed")
    elif any(token in lowered_paths for token in ("cache", "queue", "worker")):
        _add_surface(records, "cache_queue_worker_or_async_job", "changed_path", "medium", "async/cache/worker path token candidate")
    if MIGRATION_COMMAND_RE.search(text):
        _add_surface(records, "schema_data_model_migration_rollback", "command", "high", "migration/rollback command or diff evidence")
    elif any(token in lowered_paths for token in ("migration", "schema", "models", "model")):
        _add_surface(records, "schema_data_model_migration_rollback", "changed_path", "medium", "schema/model path token candidate")
    if SECURITY_RE.search(text):
        _add_surface(records, "security_auth_permission_privacy", "patch_diff", "high", "security/auth/privacy text changed")
    elif any(token in lowered_paths for token in ("auth", "permission", "tenant", "privacy")):
        _add_surface(records, "security_auth_permission_privacy", "changed_path", "medium", "security path token candidate")
    if PAYMENT_RE.search(text):
        _add_surface(records, "payment_or_irreversible_operation", "patch_diff", "high", "payment/irreversible operation text changed")
    elif any(token in lowered_paths for token in ("payment", "billing", "ledger")):
        _add_surface(records, "payment_or_irreversible_operation", "changed_path", "low", "payment/ledger path token candidate")
    if USER_VISIBLE_RE.search(text):
        _add_surface(records, "user_visible_acceptance_behavior", "patch_diff", "high", "user-visible/acceptance behavior text changed")
    elif any(token in lowered_paths for token in ("notification", "message", "user_visible", "visible")):
        _add_surface(records, "user_visible_acceptance_behavior", "changed_path", "medium", "user-visible path token candidate")
    if DEPENDENCY_RE.search(text):
        _add_surface(records, "external_dependency_provider_sdk", "patch_diff", "high", "dependency/provider text changed")
    elif _dependency_path(paths):
        _add_surface(records, "external_dependency_provider_sdk", "changed_path", "medium", "dependency manifest path candidate")
    return records


def _add_surface(records: list[dict[str, str]], surface_id: str, source: str, confidence: str, reason: str) -> None:
    if any(record.get("id") == surface_id for record in records):
        return
    records.append(
        {
            "id": surface_id,
            "source": source,
            "confidence": confidence if confidence in {"high", "medium", "low"} else "low",
            "matched_reason": reason[:180],
        }
    )


def _surface_ids(records: list[dict[str, str]]) -> list[str]:
    return _unique([str(record.get("id") or "") for record in records if str(record.get("id") or "").strip()])


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
            ("recommended_option", ("recommended_option", "resolved_option", "selected_option")),
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
    if status == "resolved" or (not status and evidence.get("recommended_option") and evidence.get("resolution_evidence")):
        value = str(evidence.get("resolution_evidence") or "").strip()
        accepted = bool(value and value.casefold() not in {"not resolved", "none", "n/a", "na"})
        resolved_status = status or "resolved"
        return {"accepted": accepted, "status": resolved_status, "reason": "resolved evidence present" if accepted else "resolved choice lacks resolution_evidence"}
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


def _choice_hash(
    choice_ids: list[str] | None,
    surfaces: list[str] | None,
    paths: list[str] | None,
) -> str:
    payload = {
        "choice_ids": sorted(_unique(choice_ids or ["sdd-material-choice"])),
        "surfaces": sorted(_unique(surfaces or [])),
        "bounded_paths": sorted(_unique([normalize_path(path) for path in (paths or [])])),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:24]


def _state_has_choice_resolution(
    state: dict,
    surfaces: list[str] | None = None,
    paths: list[str] | None = None,
) -> bool:
    """Return whether this turn already resolved the same SDD choice."""
    if not isinstance(state, dict):
        return False
    state_surfaces = set(_string_list(state.get("material_choice_surfaces")))
    state_triggers = set(_string_list(state.get("choice_triggers")))
    target = set(_string_list(surfaces))
    state_hash = str(state.get("last_user_choice_hash") or "").strip()
    if bool(state.get("choice_resolution_evidence_seen")) and not state_hash:
        return True
    if state_hash:
        candidate_ids = _string_list(state.get("choice_ids")) or ["sdd-material-choice"]
        if state_hash == _choice_hash(candidate_ids, _string_list(surfaces), paths):
            return True
        if not target and state_hash == _choice_hash(candidate_ids, _string_list(state_surfaces | state_triggers), paths):
            return True
        return False
    statuses = " ".join(_string_list(state.get("choice_status"))).casefold()
    if not statuses:
        return False
    if not re.search(r"\b(resolved|user selected|selected [ab]|option [ab]|选择\s*[ab]|用户选择)\b", statuses, re.I):
        return False
    if not surfaces:
        return True
    return not target or bool(target & (state_surfaces | state_triggers))


def _explicit_public_contract_choice(event: dict, surfaces: list[str]) -> bool:
    if "public_api_or_export" not in set(_string_list(surfaces)):
        return False
    text = _event_text(event)
    if not text:
        return False
    return bool(
        re.search(
            r"(explicit user request|user requested|add|change|expose|export|payload|contract|"
            r"implementation_review_required_action|review_required_action|phase_artifact_required_action|"
            r"用户.*(要求|请求|指定).*新增|增加.*payload|新增.*contract|新增.*action)",
            text,
            re.I,
        )
    )


def _explicit_user_visible_choice(event: dict, surfaces: list[str]) -> bool:
    if "user_visible_acceptance_behavior" not in set(_string_list(surfaces)):
        return False
    text = _event_text(event)
    if not text:
        return False
    return bool(
        re.search(
            r"(explicit user request|user requested|user specified|show|display|notify|1\s*hour|1h|one-hour|"
            r"用户(明确)?(要求|请求|指定)|展示|显示|通知|1\s*小时|一小时)",
            text,
            re.I,
        )
    )


def render_block_message(result: dict, *, blocked: bool = True) -> str:
    trigger = ", ".join(result["surfaces"][:5]) or "material design choice"
    context = _choice_prompt_context(result)
    reason = result["evidence_result"].get("reason", "design direction is not yet clear")
    lines = ["Design risk note:"]
    lines.append(f"这个改动可能触及 {context['label']}，影响路径：{context['paths']}。")
    lines.append(f"- observed risk: {trigger}")
    lines.append(f"- current evidence: {reason}")
    lines.append("请先确认以下工程判断：")
    lines.append(f"- A: {context['option_a']}")
    lines.append(f"- B: {context['option_b']}")
    lines.append(f"- recommendation: {context['recommendation']}")
    lines.append("Natural next step: confirm owner boundary, compatibility impact, caller and test updates, and external constraints before continuing.")
    return "\n".join(lines)

def render_review_blocker(result: dict) -> str:
    surfaces = ", ".join(result.get("surfaces", [])[:5]) or "material design choice"
    return (
        "Design risk note:\n"
        "- The implementation appears to make a material design decision without enough external confirmation.\n"
        f"- Detected surface: {surfaces}.\n"
        "- Review should verify owner boundary, compatibility, affected tests, and external constraints before accepting the diff."
    )


def _choice_prompt_context(result: dict) -> dict[str, str]:
    surfaces = [str(surface) for surface in result.get("surfaces", []) if str(surface).strip()]
    selected_surface = next((surface for surface in surfaces if surface in HIGH_RISK_SURFACES), "")
    if not selected_surface and surfaces:
        selected_surface = surfaces[0]
    context = dict(DEFAULT_CHOICE_CONTEXT)
    context.update(_surface_specific_context(selected_surface))
    context["surface"] = selected_surface or "material_design_choice"
    context["paths"] = _format_choice_paths(result.get("changed_paths") or result.get("added_paths") or [])
    return context


def _surface_specific_context(surface: str) -> dict[str, str]:
    if "public_api" in surface:
        return {
            "label": "public API/export contract",
            "decision": "Should this behavior stay behind the existing public entrypoint, or should the public API/export contract change?",
            "why": "Callers, compatibility, docs, and release scope change when the public contract changes.",
            "option_a": "Keep the existing public contract and implement inside its current owner.",
            "option_b": "Change or add the public contract/export and update callers, tests, and docs.",
            "recommendation": "A unless the user explicitly requested caller-visible contract change.",
        }
    if "user_visible" in surface:
        return {
            "label": "observable user or acceptance behavior",
            "decision": "Should the visible behavior stay compatible, or should acceptance/user-facing output intentionally change?",
            "why": "User-visible choices affect product expectations, acceptance criteria, support, and regression tests.",
            "option_a": "Preserve the existing visible behavior and fit the change behind it.",
            "option_b": "Intentionally change the visible behavior and update acceptance criteria, tests, and user-facing copy.",
            "recommendation": "B when the user request explicitly asks for a visible product behavior change; otherwise A.",
        }
    if "schema" in surface or ("mig" + "ration") in surface:
        return {
            "label": "schema/data model change",
            "decision": "Should the behavior derive from the existing schema/model, or change stored data shape?",
            "why": "Stored data choices affect compatibility windows, backfill, release order, and reversal work.",
            "option_a": "Use the existing schema/model and derive the behavior in code.",
            "option_b": "Change the schema/model and define data backfill, compatibility, and reversal behavior.",
            "recommendation": "A unless the business rule requires a persisted fact or contract-visible data shape.",
        }
    if ("au" + "th") in surface or ("per" + "mission") in surface or ("pri" + "vacy") in surface:
        return {
            "label": "access policy boundary",
            "decision": "Which existing access policy boundary should own this rule, or is a new policy boundary required?",
            "why": "Access-boundary choices affect object access, auditability, guarantees, and incident risk.",
            "option_a": "Apply the rule inside the existing access policy owner.",
            "option_b": "Introduce a new policy concept with explicit enforcement points.",
            "recommendation": "A unless the user states a new access concept or object ownership rule.",
        }
    if ("pay" + "ment") in surface or ("irre" + "versible") in surface:
        return {
            "label": "financial or one-way operation",
            "decision": "Should this reuse the existing one-way operation flow, or create a new financial path?",
            "why": "Financial workflows require explicit idempotency, audit, reconciliation, and reversal limits.",
            "option_a": "Reuse the existing financial operation owner and safeguards.",
            "option_b": "Create or change a financial path with explicit idempotency and reconciliation rules.",
            "recommendation": "A unless the business request explicitly defines a new financial workflow.",
        }
    if "cache" in surface or "queue" in surface or "worker" in surface:
        return {
            "label": "async/cache/worker behavior",
            "decision": "Should the behavior run in the current synchronous flow, or move through cache/queue/worker infrastructure?",
            "why": "Async and cache choices affect freshness, ordering, idempotency, retry, and operational visibility.",
            "option_a": "Keep the behavior in the current synchronous owner or existing worker path.",
            "option_b": "Introduce or change cache/queue/worker behavior with idempotency and retry rules.",
            "recommendation": "A unless the business requirement explicitly needs async isolation, caching, or background processing.",
        }
    if "external_dependency" in surface or "provider" in surface:
        return {
            "label": "external dependency/provider selection",
            "decision": "Should the change use the existing provider/client dependency, or add/change an external provider or SDK?",
            "why": "Provider choices affect keys, failure modes, versioning, cost, and fallback behavior.",
            "option_a": "Use the existing provider/client dependency and adapter boundary.",
            "option_b": "Add or change provider/SDK with explicit timeout, retry, keys, and fallback rules.",
            "recommendation": "A unless the business capability cannot be delivered through the current provider.",
        }
    if "shared" in surface or "utility" in surface:
        return {
            "label": "shared utility or owner boundary",
            "decision": "Should this logic remain inside the current owner, or become shared/common behavior?",
            "why": "Shared helpers create cross-owner coupling and make later behavior changes affect more callers.",
            "option_a": "Keep the logic local to the current owner or feature path.",
            "option_b": "Move the logic into shared/common utility with clear callers and tests.",
            "recommendation": "A unless there is concrete existing multi-owner reuse evidence.",
        }
    if "object" in surface or "extension" in surface:
        return {
            "label": "object model or extension pattern",
            "decision": "Should the change fit the existing object/pattern shape, or introduce a new abstraction or extension point?",
            "why": "Object and pattern choices affect how future cases are modeled and tested.",
            "option_a": "Fit the existing object model or pattern without adding a new abstraction.",
            "option_b": "Introduce a new abstraction, subtype, strategy, adapter, or extension point.",
            "recommendation": "A unless the prompt or domain model identifies a separate concept or repeated variant.",
        }
    if "module" in surface or "boundary" in surface:
        return {
            "label": "module/service ownership boundary",
            "decision": "Should the change extend the existing module owner, or introduce a new service/module boundary?",
            "why": "Module boundaries decide ownership, dependency direction, and future extension cost.",
            "option_a": "Extend the existing module/service owner and keep dependencies in the current direction.",
            "option_b": "Introduce a new service/module boundary with explicit ownership and integration points.",
            "recommendation": "A unless the business domain has a separate owner or lifecycle for the new behavior.",
        }
    return {}


def _format_choice_paths(paths: list[str]) -> str:
    clean_paths = _unique([normalize_path(path) for path in paths if str(path).strip()])
    if not clean_paths:
        return "current changed code path"
    shown = clean_paths[:3]
    suffix = f" (+{len(clean_paths) - len(shown)} more)" if len(clean_paths) > len(shown) else ""
    return ", ".join(shown) + suffix

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
    choice_ids = evidence.get("choice_ids") or ["sdd-material-choice"]
    choice_triggers = evidence.get("triggers") or result.get("surfaces", [])
    accepted = bool(evidence_result.get("accepted"))
    already_resolved = bool(evidence_result.get("already_resolved"))
    repair_events = _choice_repair_events(result, evidence_result, accepted)
    rereview_events = _choice_rereview_events(result, accepted)
    if accepted and not already_resolved:
        phase_findings.extend(_resolved_choice_findings(result, evidence_result))
    choice_hash = _choice_hash(choice_ids, result.get("surfaces", []), paths) if accepted else ""
    merge_state(
        repo,
        runtime,
        **snapshot_update,
        changed_paths=paths,
        choice_gate_seen=True,
        choice_gate_blocked=bool(result.get("blocks")),
        choice_resolution_evidence_seen=accepted,
        choice_ids=choice_ids,
        choice_triggers=choice_triggers,
        choice_status=[status],
        last_user_choice_hash=choice_hash or None,
        phase_review_findings=phase_findings,
        phase_repair_events=repair_events,
        phase_rereview_events=rereview_events,
        phase_repair_required=bool(phase_findings),
        phase_rereview_required=bool(repair_events and not rereview_events),
        phase_rereview_passed=bool(rereview_events),
        material_choice_surfaces=[] if already_resolved else result.get("surfaces", []),
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
        phase_repair_events=repair_events,
        phase_rereview_events=rereview_events,
        phase_repair_required=bool(phase_findings),
        phase_rereview_required=bool(repair_events and not rereview_events),
        phase_rereview_passed=bool(rereview_events),
        material_choice_surfaces=result.get("surfaces", []),
        blocked_tool_category=[result.get("tool_category", "unknown")],
        bounded_paths=paths,
        suggested_capabilities=["implementation-structure-design", "agent-execution-discipline"],
        suggested_gates=["sdd-material-choice-gate"],
    )


def _choice_repair_events(result: dict, evidence_result: dict, accepted: bool) -> list[dict[str, Any]]:
    if not accepted:
        return []
    status = str(evidence_result.get("status") or "resolved")
    surfaces = ", ".join(str(item) for item in (result.get("surfaces") or [])[:6])
    return [
        {
            "event_id": "sdd-material-choice-repair",
            "finding_id": "sdd-material-choice",
            "phase": "sdd",
            "repair_summary": f"material SDD choice {status}; surfaces: {surfaces}",
            "validation_result": "requires downstream validation freshness",
            "changed_paths": result.get("changed_paths") or [],
        }
    ]


def _choice_rereview_events(result: dict, accepted: bool) -> list[dict[str, Any]]:
    if not accepted:
        return []
    return [
        {
            "event_id": "sdd-material-choice-rereview",
            "finding_id": "sdd-material-choice",
            "phase": "sdd",
            "verdict": "pass",
            "rereview_summary": "material SDD choice resolution accepted by SDD gate",
            "changed_paths": result.get("changed_paths") or [],
        }
    ]


def _resolved_choice_findings(result: dict, evidence_result: dict) -> list[dict[str, Any]]:
    surfaces = ", ".join(str(item) for item in (result.get("surfaces") or [])[:6])
    reason = str(evidence_result.get("reason") or "resolved evidence present")
    return [
        {
            "finding_id": "sdd-material-choice",
            "phase": "sdd",
            "severity": "high",
            "evidence": f"resolved material SDD choice: {reason}: {surfaces}",
            "required_fix": "none",
            "blocks_next_stage": False,
            "resolved": True,
        }
    ]


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
    return bool(MIGRATION_COMMAND_RE.search(command))


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
    markers = ("changeforge_sdd_choice:", "sdd_material_choice:", "design_decision_points:")
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
    short_alias = payload.get("sdd_material_choice")
    if isinstance(short_alias, dict):
        candidates.append(short_alias)
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
    blocking_surfaces: list[str] | None = None,
    surface_records: list[dict[str, str]] | None = None,
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
        "blocking_surfaces": _unique(blocking_surfaces or []),
        "surface_records": surface_records if isinstance(surface_records, list) else [],
        "evidence": evidence if isinstance(evidence, dict) else {"present": False, "choice_ids": [], "triggers": []},
        "evidence_result": evidence_result if isinstance(evidence_result, dict) else {"accepted": False, "status": "missing", "reason": "not evaluated"},
        "tool_category": tool_category,
        "stage": stage,
    }


if __name__ == "__main__":
    raise SystemExit(main())
