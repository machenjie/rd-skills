#!/usr/bin/env python3
"""Explicit reducer rules for ChangeForge per-turn hook state."""

from __future__ import annotations

import json
from typing import Any

try:
    from changeforge_compaction_contract import (
        latest_snapshot,
        merge_active_context,
        preserve_required_snapshots,
        sanitize_compaction_snapshot,
    )
except (ImportError, ModuleNotFoundError):  # pragma: no cover - importlib test loading fallback
    import importlib.util
    from pathlib import Path

    _contract_path = Path(__file__).with_name("changeforge_compaction_contract.py")
    _contract_spec = importlib.util.spec_from_file_location(
        "changeforge_compaction_contract", _contract_path
    )
    if _contract_spec is None or _contract_spec.loader is None:
        raise
    _contract_module = importlib.util.module_from_spec(_contract_spec)
    _contract_spec.loader.exec_module(_contract_module)
    latest_snapshot = _contract_module.latest_snapshot
    merge_active_context = _contract_module.merge_active_context
    preserve_required_snapshots = _contract_module.preserve_required_snapshots
    sanitize_compaction_snapshot = _contract_module.sanitize_compaction_snapshot

try:
    from changeforge_branch_route_summary import sanitize_route_repair_summary
except (ImportError, ModuleNotFoundError):  # pragma: no cover - importlib test loading fallback
    import importlib.util
    from pathlib import Path

    _summary_path = Path(__file__).with_name("changeforge_branch_route_summary.py")
    _summary_spec = importlib.util.spec_from_file_location(
        "changeforge_branch_route_summary", _summary_path
    )
    if _summary_spec is None or _summary_spec.loader is None:
        raise
    _summary_module = importlib.util.module_from_spec(_summary_spec)
    _summary_spec.loader.exec_module(_summary_module)
    sanitize_route_repair_summary = _summary_module.sanitize_route_repair_summary


MAX_STATE_ITEMS = 50
MAX_STATE_VALUE_LEN = 300

STATE_REDUCERS = {
    "runtime_adapter": "merge_runtime_adapter_facts",
    "normalized_events": "additive_unique",
    "changed_paths": "risk_priority_then_recent",
    "deleted_paths": "additive_unique",
    "generated_paths": "additive_unique",
    "read_paths": "risk_priority_then_recent",
    "read_tools": "additive_unique",
    "searched_patterns": "additive_unique",
    "external_file_changes": "additive_unique",
    "config_changes": "additive_unique",
    "structure_findings": "additive_unique",
    "file_naming_findings": "additive_unique",
    "reuse_findings": "additive_unique",
    "extension_reuse_findings": "additive_unique",
    "advanced_refactor_findings": "additive_unique",
    "comment_findings": "additive_unique",
    "structure_quality_findings": "additive_unique",
    "post_edit_structure_findings": "additive_unique",
    "review_targets": "additive_unique",
    "review_findings": "unresolved_findings_first",
    "repair_findings": "additive_unique",
    "repair_events": "latest_by_finding",
    "rereview_events": "latest_by_finding",
    "validation_results": "latest_by_command_or_path_preserve_stale_state",
    "risk_surfaces": "additive_unique",
    "changed_path_risk_surfaces": "additive_unique",
    "command_risk_surfaces": "additive_unique",
    "command_risks": "additive_unique",
    "closure_risk_surfaces": "additive_unique",
    "professional_injections": "additive_unique",
    "professional_injection_digests": "additive_unique",
    "permission_decisions": "additive_unique",
    "rollback_points": "additive_unique",
    "reference_loads": "additive_unique",
    "subagent_contracts": "additive_unique",
    "compaction_snapshots": "latest_checkpoint_preserve_required_fields",
    "prompt_signals": "additive_unique",
    "suggested_skills": "additive_unique",
    "suggested_capabilities": "additive_unique",
    "suggested_domain_extensions": "additive_unique",
    "suggested_gates": "additive_unique",
    "context_control_records": "latest_context_control_records",
    "tool_output_boundaries": "latest_tool_output_boundaries",
    "artifact_references": "artifact_references",
    "branch_route_repair_summaries": "latest_branch_route_repair_summaries",
    "route_repair_forbidden_retries": "route_repair_forbidden_retries",
    "context_budget_findings": "additive_unique",
    "skipped_references": "additive_unique",
    "implementation_preflights": "additive_unique",
    "senior_programming_judgments": "additive_unique",
    "pre_edit_structure_findings": "additive_unique",
    "choice_ids": "additive_unique",
    "choice_triggers": "additive_unique",
    "choice_status": "additive_unique",
    "material_choice_surfaces": "additive_unique",
    "blocked_tool_category": "additive_unique",
    "bounded_paths": "additive_unique",
    "stage_route_present": "bool_or",
    "read_intent_seen": "bool_or",
    "read_evidence_seen": "bool_or",
    "reviewed_diff_evidence_seen": "bool_or",
    "review_intent_seen": "bool_or",
    "review_artifact_seen": "bool_or",
    "review_evidence_seen": "bool_or",
    "repair_evidence_seen": "bool_or",
    "permission_gate_seen": "bool_or",
    "professional_contract_seen": "bool_or",
    "repository_context_seen": "bool_or",
    "workflow_state_seen": "bool_or",
    "tool_permission_sandbox_seen": "bool_or",
    "skill_efficacy_benchmark_seen": "bool_or",
    "plan_execution_consistency_seen": "bool_or",
    "validation_freshness_seen": "bool_or",
    "validation_command_seen": "bool_or",
    "validation_seen": "bool_or",
    "implementation_preflight_seen": "bool_or",
    "implementation_preflight_complete": "bool_or",
    "implementation_preflight_required": "bool_or",
    "implementation_preflight_blocked": "bool_or",
    "senior_programming_judgment_seen": "bool_or",
    "senior_programming_judgment_complete": "bool_or",
    "senior_programming_judgment_required": "bool_or",
    "senior_programming_judgment_blocked": "bool_or",
    "choice_gate_seen": "bool_or",
    "choice_gate_blocked": "bool_or",
    "choice_resolution_evidence_seen": "bool_or",
    "pre_edit_missing_read_evidence": "bool_or",
    "pre_edit_missing_reuse_decision": "bool_or",
    "pre_edit_missing_placement_decision": "bool_or",
    "pre_edit_missing_test_plan": "bool_or",
    "pre_edit_missing_senior_programming_judgment": "bool_or",
    "edit_without_preflight_seen": "bool_or",
    "post_edit_confirmed_preflight_gap": "bool_or",
    "route_preflight_emitted": "bool_or",
    "turn_stage": "last_non_empty",
    "owner_skill": "last_non_empty",
    "reviewer_skill": "last_non_empty",
    "professional_injection_digest": "last_non_empty",
    "last_professional_injection_event": "last_non_empty",
    "active_skill_context": "merge_preserve_required_fields",
}


def reduce_state_update(state: dict, update: dict) -> dict:
    """Apply explicit field reducers to a state update.

    Unknown fields are ignored so accidental hook output cannot expand the state
    schema or turn cache into a content corpus.
    """
    if not isinstance(state, dict):
        state = {}
    if not isinstance(update, dict):
        return dict(state)
    next_state = dict(state)
    for field, reducer in STATE_REDUCERS.items():
        if field not in update:
            continue
        value = update.get(field)
        if reducer == "additive_unique":
            next_state[field] = _additive_unique(next_state.get(field, []), value)
        elif reducer == "bool_or":
            next_state[field] = bool(next_state.get(field)) or bool(value)
        elif reducer == "last_non_empty":
            text = str(value).strip() if value is not None else ""
            if text:
                next_state[field] = text[:MAX_STATE_VALUE_LEN]
        elif reducer == "mapping_replace":
            if isinstance(value, dict) and value:
                next_state[field] = _clean_mapping(value)
        elif reducer == "merge_runtime_adapter_facts":
            if isinstance(value, dict) and value:
                next_state[field] = _merge_runtime_adapter_facts(next_state.get(field), value)
        elif reducer == "merge_preserve_required_fields":
            if isinstance(value, dict) and value:
                snapshot = latest_snapshot(next_state.get("compaction_snapshots", []))
                merged = _clean_mapping({**_mapping_value(next_state.get(field)), **value})
                if snapshot:
                    merged = merge_active_context(merged, snapshot)
                next_state[field] = merged
        elif reducer == "latest_checkpoint_preserve_required_fields":
            next_state[field] = _latest_checkpoint_preserve_required_fields(next_state.get(field, []), value)
        elif reducer == "latest_by_command_or_path_preserve_stale_state":
            next_state[field] = _latest_by_key_preserve_stale(next_state.get(field, []), value)
        elif reducer == "unresolved_findings_first":
            next_state[field] = _unresolved_findings_first(next_state.get(field, []), value)
        elif reducer == "latest_by_finding":
            next_state[field] = _latest_by_key(next_state.get(field, []), value)
        elif reducer == "risk_priority_then_recent":
            next_state[field] = _risk_priority_then_recent(next_state.get(field, []), value)
        elif reducer == "latest_context_control_records":
            next_state[field] = _latest_context_control_records(next_state.get(field, []), value)
        elif reducer == "latest_tool_output_boundaries":
            next_state[field] = _latest_tool_output_boundaries(next_state.get(field, []), value)
        elif reducer == "artifact_references":
            next_state[field] = _artifact_references(next_state.get(field, []), value)
        elif reducer == "latest_branch_route_repair_summaries":
            next_state[field] = _latest_branch_route_repair_summaries(
                next_state.get(field, []),
                value,
            )
        elif reducer == "route_repair_forbidden_retries":
            next_state[field] = _route_repair_forbidden_retries(next_state.get(field, []), value)
    return next_state


def _additive_unique(existing: Any, incoming: Any) -> list[str]:
    values: list[str] = []
    for source in (_as_iterable(existing), _as_iterable(incoming)):
        for raw in source:
            text = str(raw).strip()
            if not text:
                continue
            values.append(text[:MAX_STATE_VALUE_LEN])
            if len(values) >= MAX_STATE_ITEMS * 2:
                break
    return _unique(values)[:MAX_STATE_ITEMS]


def _as_iterable(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _clean_mapping(value: dict) -> dict:
    cleaned: dict[str, Any] = {}
    for key, raw in value.items():
        name = str(key).strip()[:80]
        if not name:
            continue
        if isinstance(raw, (list, tuple)):
            cleaned[name] = _additive_unique([], raw)
        elif isinstance(raw, dict):
            child: dict[str, str] = {}
            for child_key, child_value in raw.items():
                child_name = str(child_key).strip()[:80]
                if child_name:
                    child[child_name] = str(child_value).strip()[:MAX_STATE_VALUE_LEN]
            cleaned[name] = child
        else:
            cleaned[name] = str(raw).strip()[:MAX_STATE_VALUE_LEN]
    return cleaned


def _latest_context_control_records(existing: Any, incoming: Any) -> list[dict]:
    records: dict[tuple[str, str], dict] = {}
    order: list[tuple[str, str]] = []
    for raw in [*_as_iterable(existing), *_as_iterable(incoming)]:
        if not isinstance(raw, dict):
            continue
        record = _clean_context_control_record(raw)
        if not record:
            continue
        key = (
            str(record.get("route_id") or "active-runtime-route"),
            str(record.get("current_stage") or record.get("stage") or ""),
        )
        if key not in records:
            order.append(key)
        records[key] = record
    ordered = [records[key] for key in order if key in records]
    ordered.sort(key=_context_record_priority)
    return ordered[:10]


def _latest_tool_output_boundaries(existing: Any, incoming: Any) -> list[dict]:
    records: dict[tuple[str, str, str], dict] = {}
    order: list[tuple[str, str, str]] = []
    for raw in [*_as_iterable(existing), *_as_iterable(incoming)]:
        if not isinstance(raw, dict):
            continue
        record = _clean_tool_output_record(raw)
        if not record:
            continue
        key = (
            str(record.get("event_name") or "unknown"),
            str(record.get("tool_name") or "unknown"),
            str(record.get("digest") or len(order)),
        )
        if key not in records:
            order.append(key)
        records[key] = record
    return [records[key] for key in order[-10:] if key in records]


def _artifact_references(existing: Any, incoming: Any) -> list[str]:
    return _additive_unique(
        [],
        [
            ref
            for ref in (
                _clean_artifact_reference(item)
                for item in [*_as_iterable(existing), *_as_iterable(incoming)]
            )
            if ref
        ],
    )


def _latest_branch_route_repair_summaries(existing: Any, incoming: Any) -> list[dict]:
    records: dict[str, dict] = {}
    order: list[str] = []
    for raw in [*_as_iterable(existing), *_as_iterable(incoming)]:
        if not isinstance(raw, dict):
            continue
        record = sanitize_route_repair_summary(raw)
        summary_id = str(record.get("summary_id") or "").strip()
        if not summary_id:
            continue
        if summary_id not in records:
            order.append(summary_id)
        records[summary_id] = record
    ordered = [records[key] for key in order if key in records]
    ordered.sort(key=_route_repair_summary_priority)
    return ordered[:10]


def _route_repair_forbidden_retries(existing: Any, incoming: Any) -> list[str]:
    values = _additive_unique(existing, incoming)
    values.sort(key=_forbidden_retry_priority)
    return values[:10]


def _clean_context_control_record(raw: dict) -> dict:
    forbidden = {
        "prompt",
        "prompt_text",
        "raw_prompt",
        "raw_output",
        "raw_command_output",
        "full_output",
        "full_diff",
        "full_file",
        "file_contents",
        "environment",
        "env",
        "secret",
        "secrets",
        "credential",
        "credentials",
    }
    cleaned: dict[str, Any] = {}
    for key, value in raw.items():
        name = str(key).strip()[:80]
        if not name or name.casefold() in forbidden:
            continue
        if isinstance(value, bool) or isinstance(value, int):
            cleaned[name] = value
        elif isinstance(value, dict):
            cleaned[name] = _clean_mapping(value)
        elif isinstance(value, (list, tuple)):
            items: list[Any] = []
            for item in list(value)[:20]:
                if isinstance(item, dict):
                    items.append(_clean_mapping(item))
                else:
                    items.append(str(item).strip()[:MAX_STATE_VALUE_LEN])
            cleaned[name] = items
        else:
            cleaned[name] = str(value).strip()[:MAX_STATE_VALUE_LEN]
    return cleaned


def _clean_tool_output_record(raw: dict) -> dict:
    forbidden = {
        "stdout",
        "stderr",
        "command_output",
        "raw_output",
        "full_output",
        "full_diff",
        "file_contents",
        "raw_prompt",
        "prompt",
        "environment",
        "env",
        "secret",
        "secrets",
        "credential",
        "credentials",
        "password",
        "api_key",
        "apikey",
        "token",
    }
    allowed = {
        "schema_version",
        "tool_name",
        "event_name",
        "output_size_class",
        "output_bytes",
        "output_lines",
        "artifact_path",
        "artifact_path_source",
        "digest",
        "bounded_summary",
        "truncation_advice",
        "llm_context_policy",
        "privacy_status",
        "unsupported_reason",
    }
    cleaned: dict[str, Any] = {}
    privacy_failed = _record_has_forbidden_key(raw, forbidden)
    for key, value in raw.items():
        name = str(key).strip()[:80]
        if not name or name not in allowed or _forbidden_key_name(name, forbidden):
            continue
        if name in {"schema_version", "output_bytes", "output_lines"}:
            try:
                cleaned[name] = max(0, int(value)) if value is not None else None
            except (TypeError, ValueError):
                cleaned[name] = None
        elif name == "bounded_summary":
            cleaned[name] = _additive_unique([], value)[:10]
        elif name == "artifact_path":
            cleaned[name] = _clean_artifact_reference(value)
            if not cleaned[name]:
                cleaned[name] = ""
        else:
            cleaned[name] = str(value).strip()[:MAX_STATE_VALUE_LEN]
    if privacy_failed or cleaned.get("privacy_status") == "fail":
        cleaned["privacy_status"] = "fail"
    elif cleaned:
        cleaned.setdefault("privacy_status", "pass")
    if not cleaned.get("artifact_path"):
        cleaned["artifact_path"] = ""
        cleaned["artifact_path_source"] = "not_available"
    return cleaned


def _clean_artifact_reference(value: Any) -> str:
    text = str(value or "").strip().strip("'\"").replace("\\", "/")
    if not text or "\n" in text or "\0" in text or "://" in text:
        return ""
    if text.startswith("./"):
        text = text[2:]
    if not text.startswith(("/", "~")) and not _windows_absolute(text):
        if text.startswith("../") or "/../" in text or text == "..":
            return ""
        return text[:MAX_STATE_VALUE_LEN]
    for marker in ("/.cache/changeforge/", "/Library/Caches/changeforge/"):
        if marker in text:
            return ("${CACHE}/changeforge/" + text.split(marker, 1)[1].lstrip("/"))[
                :MAX_STATE_VALUE_LEN
            ]
    return "<local-artifact-path-redacted>"


def _record_has_forbidden_key(value: Any, forbidden: set[str]) -> bool:
    if not isinstance(value, dict):
        return False
    for key, child in value.items():
        if _forbidden_key_name(str(key), forbidden):
            return True
        if isinstance(child, dict) and _record_has_forbidden_key(child, forbidden):
            return True
        if isinstance(child, (list, tuple)) and any(
            _record_has_forbidden_key(item, forbidden) for item in child
        ):
            return True
    return False


def _forbidden_key_name(key: str, forbidden: set[str]) -> bool:
    lowered = key.casefold()
    return lowered in forbidden or any(token in lowered for token in forbidden)


def _windows_absolute(text: str) -> bool:
    return len(text) >= 3 and text[1:3] == ":/"


def _context_record_priority(record: dict) -> tuple[int, int]:
    findings = record.get("over_budget_findings")
    skipped = record.get("skipped_reference_count")
    finding_count = len(findings) if isinstance(findings, list) else 0
    try:
        skipped_count = int(skipped or 0)
    except (TypeError, ValueError):
        skipped_count = 0
    return (0 if finding_count or skipped_count else 1, -finding_count - skipped_count)


def _route_repair_summary_priority(record: dict) -> tuple[int, int, str]:
    text = json.dumps(record, sort_keys=True).casefold()
    severe = any(term in text for term in ("p0", "critical", "security", "data loss"))
    unresolved = not any(term in text for term in ("resolved", "fixed", "closed", "rereview passed"))
    forbidden = bool(record.get("forbidden_retries"))
    privacy_fail = str(record.get("privacy_status") or "") == "fail"
    residual = bool(record.get("residual_risk"))
    return (
        0 if severe or unresolved or forbidden or privacy_fail or residual else 1,
        -len(_as_iterable(record.get("forbidden_retries"))) - len(_as_iterable(record.get("residual_risk"))),
        str(record.get("summary_id") or ""),
    )


def _forbidden_retry_priority(value: str) -> tuple[int, str]:
    lowered = value.casefold()
    severe = any(term in lowered for term in ("p0", "critical", "security", "data loss", "same-path"))
    return (0 if severe else 1, lowered)


def _merge_runtime_adapter_facts(existing: Any, incoming: dict) -> dict:
    current = _mapping_value(existing)
    update = _clean_mapping(incoming)
    if not update:
        return dict(current)
    merged = dict(current)
    for key, value in update.items():
        if key in {
            "unsupported_checks",
            "active_unsupported_checks",
            "required_unsupported_checks",
            "active_degradation",
            "degraded_capabilities",
            "degraded_checks",
            "fail_closed_allowed_checks",
        }:
            merged[key] = _additive_unique(current.get(key, []), value)
        elif key == "visibility" and isinstance(value, dict):
            merged[key] = {**_mapping_value(current.get(key)), **value}
        elif key in {"adapter", "fail_open_policy"}:
            if str(value).strip():
                merged[key] = value
        elif isinstance(value, list):
            merged[key] = value or current.get(key, [])
        elif value:
            merged[key] = value
    return _clean_mapping(merged)


def _mapping_value(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _latest_checkpoint_preserve_required_fields(existing: Any, incoming: Any) -> list[dict[str, Any]]:
    return preserve_required_snapshots(existing, incoming, limit=5)


def _latest_by_key_preserve_stale(existing: Any, incoming: Any) -> list[str]:
    values = _latest_by_key(existing, incoming)
    stale = [value for value in values if "stale" in value.casefold()]
    fresh = [value for value in values if value not in stale]
    return _unique([*stale, *fresh])[:MAX_STATE_ITEMS]


def _unresolved_findings_first(existing: Any, incoming: Any) -> list[str]:
    values = _unique([*_string_items(existing), *_string_items(incoming)])

    def score(value: str) -> tuple[int, int]:
        lowered = value.casefold()
        unresolved = not any(term in lowered for term in ("resolved", "closed", "fixed", "rereview passed"))
        severity = 0 if any(term in lowered for term in ("critical", "p0", "security", "data loss")) else 1
        return (0 if unresolved else 1, severity)

    return sorted(values, key=score)[:MAX_STATE_ITEMS]


def _latest_by_key(existing: Any, incoming: Any) -> list[str]:
    values = [*_string_items(existing), *_string_items(incoming)]
    by_key: dict[str, str] = {}
    order: list[str] = []
    for value in values:
        key = _record_key(value)
        if key not in order:
            order.append(key)
        by_key[key] = value
    return [by_key[key] for key in order[-MAX_STATE_ITEMS:]]


def _risk_priority_then_recent(existing: Any, incoming: Any) -> list[str]:
    values = _unique([*_string_items(existing), *_string_items(incoming)])
    values = values[-MAX_STATE_ITEMS * 2 :]
    if not any(
        any(term in value.casefold() for term in ("security", "schema", "migration", "auth", "hook", "runtime", "state"))
        for value in values
    ):
        return values[:MAX_STATE_ITEMS]

    def score(value: str) -> tuple[int, int]:
        lowered = value.casefold()
        risky = any(term in lowered for term in ("security", "schema", "migration", "auth", "hook", "runtime", "state"))
        recent_index = values.index(value)
        return (0 if risky else 1, -recent_index)

    return sorted(values, key=score)[:MAX_STATE_ITEMS]


def _string_items(value: Any) -> list[str]:
    items: list[str] = []
    for raw in _as_iterable(value):
        if isinstance(raw, dict):
            text = json.dumps(_clean_mapping(raw), sort_keys=True)
        else:
            text = str(raw).strip()
        if text:
            items.append(text[:MAX_STATE_VALUE_LEN])
    return items


def _record_key(value: str) -> str:
    lowered = value.casefold()
    for marker in ("finding=", "finding:", "path=", "path:", "command=", "command:"):
        if marker in lowered:
            return lowered.split(marker, 1)[1].split()[0][:120]
    return lowered[:120]


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


__all__ = ["STATE_REDUCERS", "reduce_state_update"]
