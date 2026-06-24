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


MAX_STATE_ITEMS = 50
MAX_STATE_VALUE_LEN = 300

STATE_REDUCERS = {
    "runtime_adapter": "mapping_replace",
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
    "implementation_preflights": "additive_unique",
    "pre_edit_structure_findings": "additive_unique",
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
    "pre_edit_missing_read_evidence": "bool_or",
    "pre_edit_missing_reuse_decision": "bool_or",
    "pre_edit_missing_placement_decision": "bool_or",
    "pre_edit_missing_test_plan": "bool_or",
    "edit_without_preflight_seen": "bool_or",
    "post_edit_confirmed_preflight_gap": "bool_or",
    "route_preflight_emitted": "bool_or",
    "turn_stage": "last_non_empty",
    "owner_skill": "last_non_empty",
    "reviewer_skill": "last_non_empty",
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
