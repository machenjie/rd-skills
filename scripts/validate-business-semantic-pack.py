#!/usr/bin/env python3
"""Validate Business Semantic Pack schemas and deterministic fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from validation_utils import fail_many, load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "src" / "business_intelligence" / "schemas"
EVAL_DIR = ROOT / "evals" / "business-semantic"
SCHEMAS = (
    "business-semantic-pack.v1.schema.json",
    "business-rule-record.v1.schema.json",
    "business-memory-event.v1.schema.json",
    "business-golden-case.v1.schema.json",
)
BSP_SECTIONS = {
    "task_business_intent",
    "business_vocabulary",
    "business_objects",
    "business_rules",
    "workflows",
    "data_and_signal_semantics",
    "code_mapping",
    "memory_projection",
    "validation_map",
    "context_control",
}
EVIDENCE_CLASSES = {"FACT", "INFERENCE", "ASSUMPTION", "OPEN_QUESTION", "MEMORY_SIGNAL"}
FACT_SELECTOR_SOURCES = {"repository_graph", "memory_projection", "agent_inference"}
BUSINESS_MEMORY_EVENT_TYPES = {
    "business_rule_changed",
    "business_rule_rejected",
    "business_object_ownership_changed",
    "business_term_ambiguous",
    "workflow_transition_bug",
    "missing_entry_point_bug",
    "hidden_sql_rule_bug",
    "stale_business_context",
    "golden_case_added",
    "golden_case_failed",
    "owner_decision_superseded",
}


def main() -> int:
    errors: list[str] = []
    _validate_schema_files(errors)
    _validate_sample_pack(errors)
    _validate_eval_fixtures(errors)
    return fail_many("validate-business-semantic-pack", errors) or _ok()


def _ok() -> int:
    print("validate-business-semantic-pack: OK")
    return 0


def _validate_schema_files(errors: list[str]) -> None:
    for name in SCHEMAS:
        path = SCHEMA_DIR / name
        if not path.is_file():
            errors.append(f"missing schema: {path.relative_to(ROOT)}")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{path.relative_to(ROOT)} invalid JSON: {exc}")
            continue
        if data.get("type") != "object":
            errors.append(f"{path.relative_to(ROOT)} must be a root object schema")
        if data.get("additionalProperties") is not False:
            errors.append(f"{path.relative_to(ROOT)} must set additionalProperties=false")
    pack_schema = _load_schema("business-semantic-pack.v1.schema.json", errors)
    if pack_schema:
        required = set(
            pack_schema["properties"]["business_semantic_pack"]["required"]
        )
        missing = BSP_SECTIONS - required
        if missing:
            errors.append("business semantic pack schema missing sections: " + ", ".join(sorted(missing)))
        evidence_enum = set(
            pack_schema["$defs"]["evidence"]["properties"]["evidence_class"]["enum"]
        )
        if evidence_enum != EVIDENCE_CLASSES:
            errors.append("business semantic pack schema evidence_class enum drifted")
    memory_schema = _load_schema("business-memory-event.v1.schema.json", errors)
    if memory_schema:
        event_types = set(
            memory_schema["properties"]["business_memory_event"]["properties"]["event_type"]["enum"]
        )
        if event_types != BUSINESS_MEMORY_EVENT_TYPES:
            errors.append("business memory event type enum drifted from policy")


def _load_schema(name: str, errors: list[str]) -> dict[str, Any] | None:
    try:
        return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{name} could not be loaded for semantic checks: {exc}")
        return None


def _validate_sample_pack(errors: list[str]) -> None:
    pack = _sample_pack()["business_semantic_pack"]
    for section in BSP_SECTIONS:
        if section not in pack:
            errors.append(f"sample pack missing section {section}")
    rule_ids: set[str] = set()
    for rule in pack.get("business_rules", []):
        rule_id = rule.get("rule_id")
        if rule_id in rule_ids:
            errors.append(f"duplicate rule_id in sample pack: {rule_id}")
        rule_ids.add(rule_id)
        for field in ("owner", "enforcement_layer", "reason_codes", "entry_points", "effective_dating"):
            if not rule.get(field):
                errors.append(f"rule {rule_id} missing {field}")
        if not rule.get("tests") and not rule.get("residual_risk"):
            errors.append(f"rule {rule_id} must have tests or residual_risk")
    for workflow in pack.get("workflows", []):
        transitions = workflow.get("transitions", [])
        if not any(item.get("allowed") is True for item in transitions):
            errors.append(f"workflow {workflow.get('workflow_id')} has no allowed transition")
        if not any(item.get("allowed") is False for item in transitions):
            errors.append(f"workflow {workflow.get('workflow_id')} has no forbidden transition")
    memory = pack.get("memory_projection", {})
    for verdict in ("accepted", "rejected", "stale", "not_verified"):
        if verdict not in memory:
            errors.append(f"memory_projection missing {verdict}")
    for evidence in _walk_evidence(pack):
        evidence_class = evidence.get("evidence_class")
        source_kind = evidence.get("source_kind")
        if evidence_class == "FACT" and source_kind in FACT_SELECTOR_SOURCES:
            errors.append("FACT evidence cannot rely on graph, memory, or agent inference alone")
        if evidence_class == "FACT" and not evidence.get("source_paths") and source_kind == "current_source":
            errors.append("current_source FACT evidence must include source_paths")
    mapped_claims = {item.get("claim_id") for item in pack.get("validation_map", [])}
    for rule in pack.get("business_rules", []):
        if rule.get("rule_id") not in mapped_claims and not rule.get("residual_risk"):
            errors.append(f"rule {rule.get('rule_id')} lacks validation_map or residual_risk")
    context = pack.get("context_control", {})
    if context.get("budget_mode") not in {"minimal", "single-stage", "staged-plan", "full"}:
        errors.append("context_control budget_mode is invalid")
    for ref_field in ("selected_references", "skipped_references"):
        if not isinstance(context.get(ref_field), list):
            errors.append(f"context_control {ref_field} must be a list with rationale")


def _walk_evidence(value: Any) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    if isinstance(value, dict):
        if "evidence_class" in value:
            result.append(value)
        for child in value.values():
            result.extend(_walk_evidence(child))
    elif isinstance(value, list):
        for item in value:
            result.extend(_walk_evidence(item))
    return result


def _validate_eval_fixtures(errors: list[str]) -> None:
    paths = sorted(EVAL_DIR.glob("*.yaml"))
    if len(paths) != 10:
        errors.append(f"expected 10 business-semantic fixtures, found {len(paths)}")
    seen_ids: set[str] = set()
    for path in paths:
        fixture = load_yaml_file(path)
        context = str(path.relative_to(ROOT))
        for field in (
            "case_id",
            "prompt",
            "expected_route",
            "expected_capabilities",
            "expected_quality_gates",
            "expected_bsp_sections",
            "expected_review_findings",
            "forbidden_behavior",
            "scoring",
        ):
            if field not in fixture:
                errors.append(f"{context}: missing {field}")
        case_id = str(fixture.get("case_id", ""))
        if case_id in seen_ids:
            errors.append(f"{context}: duplicate case_id {case_id}")
        seen_ids.add(case_id)
        route = fixture.get("expected_route", {})
        if not isinstance(route, dict) or "business_semantic_pack_required" not in route:
            errors.append(f"{context}: expected_route must declare business_semantic_pack_required")
        sections = set(str(item) for item in fixture.get("expected_bsp_sections", []) or [])
        invalid_sections = sections - BSP_SECTIONS
        if invalid_sections:
            errors.append(f"{context}: invalid BSP sections {sorted(invalid_sections)}")
        if route.get("business_semantic_pack_required") is True and "business-semantic-control-plane" not in fixture.get("expected_capabilities", []):
            errors.append(f"{context}: BSP-required case must select business-semantic-control-plane")
        if not fixture.get("forbidden_behavior"):
            errors.append(f"{context}: forbidden_behavior must be non-empty")


def _sample_pack() -> dict[str, Any]:
    fact = {
        "evidence_class": "FACT",
        "source_kind": "current_source",
        "source_paths": ["src/domain/order.py"],
        "summary": "Order aggregate owns cancellation.",
        "freshness": "current",
        "confidence": "high",
        "verification_status": "verified",
    }
    memory = {
        "evidence_class": "MEMORY_SIGNAL",
        "source_kind": "memory_projection",
        "summary": "Prior cancellation rule may be stale.",
        "freshness": "stale",
        "confidence": "low",
        "verification_status": "stale",
    }
    return {
        "business_semantic_pack": {
            "schema_version": 1,
            "pack_id": "bsp_order_cancel",
            "pack_version": "1",
            "created_at": "2026-06-30T00:00:00Z",
            "task_business_intent": {
                "business_outcome": "Reject cancellation after shipment.",
                "non_goals": ["No refund behavior change."],
                "success_signals": ["shipped order cancel is denied"],
                "failure_signals": ["shipped order is cancelled"],
                "evidence": [fact],
            },
            "business_vocabulary": [
                {"term": "Order", "meaning": "Customer purchase aggregate.", "owning_context": "commerce", "aliases_or_conflicts": [], "evidence": [fact]}
            ],
            "business_objects": [
                {"object_id": "OBJ.ORDER", "name": "Order", "category": "aggregate_root", "owner": "commerce", "identity": "order id", "lifecycle": "draft to shipped", "evidence": [fact]}
            ],
            "business_rules": [
                {
                    "rule_id": "ORDER.CANCEL.AFTER_SHIP_DENIED",
                    "rule_name": "Deny shipped cancellation",
                    "owner": "Order aggregate",
                    "enforcement_layer": "domain",
                    "rule_statement": "A shipped order cannot be cancelled.",
                    "reason_codes": ["ORDER_ALREADY_SHIPPED"],
                    "entry_points": ["Order.cancel"],
                    "effective_dating": {"effective_from": None, "effective_to": None, "timezone_or_calendar": "UTC"},
                    "tests": ["tests/domain/test_order.py::test_shipped_order_cannot_cancel"],
                    "residual_risk": [],
                    "evidence": [fact],
                }
            ],
            "workflows": [
                {
                    "workflow_id": "ORDER_LIFECYCLE",
                    "name": "Order lifecycle",
                    "owner": "Order aggregate",
                    "states": ["PENDING", "CANCELLED", "SHIPPED"],
                    "transitions": [
                        {"from": "PENDING", "to": "CANCELLED", "trigger": "customer_cancel", "actor": "customer", "guard_rule_ids": ["ORDER.CANCEL.AFTER_SHIP_DENIED"], "allowed": True, "reason_code": "", "evidence": [fact]},
                        {"from": "SHIPPED", "to": "CANCELLED", "trigger": "customer_cancel", "actor": "customer", "guard_rule_ids": ["ORDER.CANCEL.AFTER_SHIP_DENIED"], "allowed": False, "reason_code": "ORDER_ALREADY_SHIPPED", "evidence": [fact]},
                    ],
                    "evidence": [fact],
                }
            ],
            "data_and_signal_semantics": {"data_sources": ["orders.status"], "events": ["OrderCancellationDenied"], "metrics": ["cancel_denial_count"], "evidence": [fact]},
            "code_mapping": {"object_to_files": ["OBJ.ORDER -> src/domain/order.py"], "rule_to_enforcement": ["ORDER.CANCEL.AFTER_SHIP_DENIED -> Order.cancel"], "workflow_to_state_machine": ["ORDER_LIFECYCLE -> Order.cancel"], "forbidden_placements": ["controllers must not own cancellation rule"], "evidence": [fact]},
            "memory_projection": {"accepted": [], "rejected": [], "stale": ["mem_prior_cancel_rule"], "not_verified": []},
            "validation_map": [{"claim_id": "ORDER.CANCEL.AFTER_SHIP_DENIED", "claim_type": "rule", "validation_target": "tests/domain/test_order.py::test_shipped_order_cannot_cancel", "status": "mapped", "residual_risk": []}],
            "context_control": {"budget_mode": "single-stage", "selected_references": ["135-business-semantic-control-plane: rule authority mapping"], "skipped_references": ["payment-trading-extension: no payment behavior changed"], "evidence_limits": ["memory is selector only"], "residual_context_risk": []},
        }
    }


if __name__ == "__main__":
    raise SystemExit(main())
