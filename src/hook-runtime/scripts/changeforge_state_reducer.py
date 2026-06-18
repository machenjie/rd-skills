#!/usr/bin/env python3
"""Explicit reducer rules for ChangeForge per-turn hook state."""

from __future__ import annotations

from typing import Any


MAX_STATE_ITEMS = 50
MAX_STATE_VALUE_LEN = 300

STATE_REDUCERS = {
    "changed_paths": "additive_unique",
    "read_paths": "additive_unique",
    "read_tools": "additive_unique",
    "searched_patterns": "additive_unique",
    "structure_findings": "additive_unique",
    "file_naming_findings": "additive_unique",
    "reuse_findings": "additive_unique",
    "extension_reuse_findings": "additive_unique",
    "advanced_refactor_findings": "additive_unique",
    "comment_findings": "additive_unique",
    "structure_quality_findings": "additive_unique",
    "review_targets": "additive_unique",
    "review_findings": "additive_unique",
    "repair_findings": "additive_unique",
    "risk_surfaces": "additive_unique",
    "changed_path_risk_surfaces": "additive_unique",
    "command_risk_surfaces": "additive_unique",
    "closure_risk_surfaces": "additive_unique",
    "professional_injections": "additive_unique",
    "permission_decisions": "additive_unique",
    "reference_loads": "additive_unique",
    "subagent_contracts": "additive_unique",
    "compaction_snapshots": "additive_unique",
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
    "active_skill_context": "mapping_replace",
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
