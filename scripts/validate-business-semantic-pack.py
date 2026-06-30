#!/usr/bin/env python3
"""Validate Business Semantic Pack schemas, samples, and fixtures."""

from __future__ import annotations

import copy
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    from jsonschema import Draft202012Validator as _JsonschemaDraft202012Validator
except Exception:  # pragma: no cover - depends on local environment
    _JsonschemaDraft202012Validator = None

from validation_utils import fail_many, load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "src" / "business_intelligence" / "schemas"
EVAL_DIR = ROOT / "evals" / "business-semantic"
SAMPLE_DIR = EVAL_DIR / "samples"
SCHEMAS = {
    "business-semantic-pack.v1.schema.json": "business_semantic_pack",
    "business-rule-record.v1.schema.json": "business_rule_record",
    "business-memory-event.v1.schema.json": "business_memory_event",
    "business-golden-case.v1.schema.json": "business_golden_case",
}
BSP_SCHEMA = "business-semantic-pack.v1.schema.json"
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

SAMPLE_SCHEMA_BY_FILE = {
    "valid-business-semantic-pack.json": BSP_SCHEMA,
    "invalid-fact-from-memory.json": BSP_SCHEMA,
    "invalid-fact-from-graph.json": BSP_SCHEMA,
    "invalid-rule-missing-owner.json": BSP_SCHEMA,
    "invalid-rule-missing-enforcement-path.json": BSP_SCHEMA,
    "invalid-rule-empty-reason-codes.json": BSP_SCHEMA,
    "invalid-rule-empty-entry-points.json": BSP_SCHEMA,
    "invalid-workflow-no-forbidden-transition.json": BSP_SCHEMA,
    "invalid-selected-reference-no-reason.json": BSP_SCHEMA,
    "valid-business-rule-record.json": "business-rule-record.v1.schema.json",
    "invalid-business-rule-record.json": "business-rule-record.v1.schema.json",
    "valid-business-memory-event.json": "business-memory-event.v1.schema.json",
    "invalid-business-memory-event.json": "business-memory-event.v1.schema.json",
    "valid-business-golden-case.json": "business-golden-case.v1.schema.json",
    "invalid-business-golden-case.json": "business-golden-case.v1.schema.json",
}
VALID_SAMPLES = {
    "valid-business-semantic-pack.json",
    "valid-business-rule-record.json",
    "valid-business-memory-event.json",
    "valid-business-golden-case.json",
}
INVALID_SAMPLES = set(SAMPLE_SCHEMA_BY_FILE) - VALID_SAMPLES


@dataclass
class _FallbackValidationError(Exception):
    message: str
    path: tuple[Any, ...]


class _FallbackDraft202012Validator:
    """Small local validator for the JSON Schema subset used in this repo.

    The real `jsonschema` package remains the primary path. This fallback keeps
    local validation runnable in minimal Python environments without network
    dependency installation.
    """

    def __init__(self, schema: dict[str, Any]) -> None:
        self.schema = schema

    def iter_errors(self, instance: Any) -> Iterable[_FallbackValidationError]:
        yield from self._validate(instance, self.schema, ())

    def _validate(
        self,
        instance: Any,
        schema: Any,
        path: tuple[Any, ...],
    ) -> Iterable[_FallbackValidationError]:
        if not isinstance(schema, dict):
            return
        if "$ref" in schema:
            target = self._resolve_ref(str(schema["$ref"]))
            yield from self._validate(instance, target, path)
            return
        if "allOf" in schema:
            for child in schema["allOf"]:
                yield from self._validate(instance, child, path)
        if "if" in schema:
            if not list(self._validate(instance, schema["if"], path)):
                if "then" in schema:
                    yield from self._validate(instance, schema["then"], path)
        if "not" in schema:
            if not list(self._validate(instance, schema["not"], path)):
                yield _FallbackValidationError("must not match forbidden schema", path)
        if "type" in schema and not self._type_matches(instance, schema["type"]):
            yield _FallbackValidationError(f"expected type {schema['type']}", path)
            return
        if "const" in schema and instance != schema["const"]:
            yield _FallbackValidationError(f"expected const {schema['const']!r}", path)
        if "enum" in schema and instance not in schema["enum"]:
            yield _FallbackValidationError(f"expected one of {schema['enum']}", path)
        if isinstance(instance, str):
            if "minLength" in schema and len(instance) < int(schema["minLength"]):
                yield _FallbackValidationError(f"string shorter than {schema['minLength']}", path)
            if "maxLength" in schema and len(instance) > int(schema["maxLength"]):
                yield _FallbackValidationError(f"string longer than {schema['maxLength']}", path)
            if "pattern" in schema and not re.search(str(schema["pattern"]), instance):
                yield _FallbackValidationError(f"string does not match {schema['pattern']}", path)
        if isinstance(instance, list):
            if "minItems" in schema and len(instance) < int(schema["minItems"]):
                yield _FallbackValidationError(f"array shorter than {schema['minItems']}", path)
            if "maxItems" in schema and len(instance) > int(schema["maxItems"]):
                yield _FallbackValidationError(f"array longer than {schema['maxItems']}", path)
            if "items" in schema:
                for index, item in enumerate(instance):
                    yield from self._validate(item, schema["items"], (*path, index))
            if "contains" in schema and not any(
                not list(self._validate(item, schema["contains"], (*path, index)))
                for index, item in enumerate(instance)
            ):
                yield _FallbackValidationError("array does not contain required item", path)
        if isinstance(instance, dict):
            required = schema.get("required") or []
            for key in required:
                if key not in instance:
                    yield _FallbackValidationError(f"missing required property {key}", (*path, key))
            properties = schema.get("properties") or {}
            for key, child_schema in properties.items():
                if key in instance:
                    yield from self._validate(instance[key], child_schema, (*path, key))
            if schema.get("additionalProperties") is False:
                extra = sorted(set(instance) - set(properties))
                for key in extra:
                    yield _FallbackValidationError("additional property is not allowed", (*path, key))

    def _resolve_ref(self, ref: str) -> Any:
        if not ref.startswith("#/"):
            raise ValueError(f"unsupported JSON schema ref: {ref}")
        current: Any = self.schema
        for part in ref[2:].split("/"):
            token = part.replace("~1", "/").replace("~0", "~")
            current = current[token]
        return current

    @staticmethod
    def _type_matches(instance: Any, expected: Any) -> bool:
        if isinstance(expected, list):
            return any(_FallbackDraft202012Validator._type_matches(instance, item) for item in expected)
        return {
            "object": isinstance(instance, dict),
            "array": isinstance(instance, list),
            "string": isinstance(instance, str),
            "integer": isinstance(instance, int) and not isinstance(instance, bool),
            "number": (isinstance(instance, int | float) and not isinstance(instance, bool)),
            "boolean": isinstance(instance, bool),
            "null": instance is None,
        }.get(str(expected), True)


Draft202012Validator = (
    _JsonschemaDraft202012Validator
    if _JsonschemaDraft202012Validator is not None
    else _FallbackDraft202012Validator
)


def main() -> int:
    errors: list[str] = []
    schemas = _validate_schema_files(errors)
    _validate_sample_files(schemas, errors)
    _validate_sample_pack(errors)
    _validate_eval_fixtures(schemas, errors)
    return fail_many("validate-business-semantic-pack", errors) or _ok()


def _ok() -> int:
    engine = "jsonschema" if _JsonschemaDraft202012Validator is not None else "fallback-jsonschema-subset"
    print(f"validate-business-semantic-pack: OK schema_engine={engine}")
    return 0


def _validate_schema_files(errors: list[str]) -> dict[str, dict[str, Any]]:
    schemas: dict[str, dict[str, Any]] = {}
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
        schemas[name] = data
        if data.get("type") != "object":
            errors.append(f"{path.relative_to(ROOT)} must be a root object schema")
        if data.get("additionalProperties") is not False:
            errors.append(f"{path.relative_to(ROOT)} must set additionalProperties=false")
        _validate_additional_properties_false(data, str(path.relative_to(ROOT)), errors)
    pack_schema = schemas.get(BSP_SCHEMA)
    if pack_schema:
        required = set(pack_schema["properties"]["business_semantic_pack"]["required"])
        missing = BSP_SECTIONS - required
        if missing:
            errors.append("business semantic pack schema missing sections: " + ", ".join(sorted(missing)))
        evidence_enum = set(pack_schema["$defs"]["evidence"]["properties"]["evidence_class"]["enum"])
        if evidence_enum != EVIDENCE_CLASSES:
            errors.append("business semantic pack schema evidence_class enum drifted")
    memory_schema = schemas.get("business-memory-event.v1.schema.json")
    if memory_schema:
        event_types = set(
            memory_schema["properties"]["business_memory_event"]["properties"]["event_type"]["enum"]
        )
        if event_types != BUSINESS_MEMORY_EVENT_TYPES:
            errors.append("business memory event type enum drifted from policy")
    return schemas


def _validate_additional_properties_false(schema: Any, context: str, errors: list[str]) -> None:
    if isinstance(schema, dict):
        if (
            schema.get("type") == "object"
            and "properties" in schema
            and "/contains" not in context
            and schema.get("additionalProperties") is not False
        ):
            errors.append(f"{context}: object schema must set additionalProperties=false")
        for key, value in schema.items():
            _validate_additional_properties_false(value, f"{context}/{key}", errors)
    elif isinstance(schema, list):
        for index, item in enumerate(schema):
            _validate_additional_properties_false(item, f"{context}[{index}]", errors)


def _validate_sample_files(schemas: dict[str, dict[str, Any]], errors: list[str]) -> None:
    for filename, schema_name in SAMPLE_SCHEMA_BY_FILE.items():
        path = SAMPLE_DIR / filename
        context = str(path.relative_to(ROOT))
        if not path.is_file():
            errors.append(f"missing sample: {context}")
            continue
        try:
            instance = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{context}: invalid JSON: {exc}")
            continue
        schema = schemas.get(schema_name)
        if not schema:
            errors.append(f"{context}: schema {schema_name} unavailable")
            continue
        schema_errors = _schema_errors(schema, instance)
        if filename in VALID_SAMPLES:
            if schema_errors:
                errors.extend(f"{context}: valid sample failed schema: {item}" for item in schema_errors)
            if filename == "valid-business-semantic-pack.json":
                _validate_bsp_semantics(instance, context, errors)
        else:
            if not schema_errors:
                errors.append(f"{context}: invalid sample unexpectedly passed schema validation")
    unexpected = sorted(
        path.name
        for path in SAMPLE_DIR.glob("*.json")
        if path.name not in SAMPLE_SCHEMA_BY_FILE
    )
    for filename in unexpected:
        errors.append(f"unexpected sample file: {SAMPLE_DIR.relative_to(ROOT) / filename}")


def _schema_errors(schema: dict[str, Any], instance: Any) -> list[str]:
    validator = Draft202012Validator(schema)
    return [_format_schema_error(error) for error in validator.iter_errors(instance)]


def _format_schema_error(error: Any) -> str:
    path = "/".join(str(part) for part in getattr(error, "path", ()))
    message = getattr(error, "message", str(error))
    return f"{path or '<root>'}: {message}"


def _validate_sample_pack(errors: list[str]) -> None:
    _validate_bsp_semantics(_sample_pack(), "_sample_pack()", errors)


def _validate_bsp_semantics(instance: dict[str, Any], context: str, errors: list[str]) -> None:
    pack = instance.get("business_semantic_pack")
    if not isinstance(pack, dict):
        errors.append(f"{context}: missing business_semantic_pack")
        return
    for section in BSP_SECTIONS:
        if section not in pack:
            errors.append(f"{context}: sample pack missing section {section}")
    rule_ids: set[str] = set()
    for rule in pack.get("business_rules", []) or []:
        if not isinstance(rule, dict):
            errors.append(f"{context}: business_rules item must be object")
            continue
        rule_id = str(rule.get("rule_id") or "")
        if rule_id in rule_ids:
            errors.append(f"{context}: duplicate rule_id {rule_id}")
        rule_ids.add(rule_id)
        for field in ("owner", "enforcement_layer"):
            if not rule.get(field):
                errors.append(f"{context}: rule {rule_id} missing {field}")
        if not rule.get("reason_codes"):
            errors.append(f"{context}: rule {rule_id} missing reason_codes")
        if not rule.get("entry_points"):
            errors.append(f"{context}: rule {rule_id} missing entry_points")
        if not rule.get("tests") and not rule.get("residual_risk"):
            errors.append(f"{context}: rule {rule_id} must have tests or residual_risk")
        if rule.get("enforcement_layer") not in {"manual_owner_review", "not_decided"} and not rule.get("authoritative_enforcement_paths"):
            errors.append(f"{context}: rule {rule_id} must have authoritative_enforcement_paths")
    for workflow in pack.get("workflows", []) or []:
        transitions = workflow.get("transitions", []) if isinstance(workflow, dict) else []
        workflow_id = workflow.get("workflow_id") if isinstance(workflow, dict) else "<unknown>"
        if not any(item.get("allowed") is True for item in transitions if isinstance(item, dict)):
            errors.append(f"{context}: workflow {workflow_id} has no allowed transition")
        if not any(item.get("allowed") is False for item in transitions if isinstance(item, dict)):
            errors.append(f"{context}: workflow {workflow_id} has no forbidden transition")
    memory = pack.get("memory_projection", {})
    if not isinstance(memory, dict):
        errors.append(f"{context}: memory_projection must be object")
    else:
        for verdict in ("accepted", "rejected", "stale", "not_verified"):
            if verdict not in memory:
                errors.append(f"{context}: memory_projection missing {verdict}")
    for evidence in _walk_evidence(pack):
        evidence_class = evidence.get("evidence_class")
        source_kind = evidence.get("source_kind")
        if evidence_class == "FACT" and source_kind in FACT_SELECTOR_SOURCES:
            errors.append(f"{context}: FACT evidence cannot rely on {source_kind}")
    for item in pack.get("validation_map", []) or []:
        if not isinstance(item, dict):
            errors.append(f"{context}: validation_map item must be object")
            continue
        if item.get("status") == "mapped":
            evidence = item.get("evidence") or []
            if not evidence:
                errors.append(f"{context}: mapped claim {item.get('claim_id')} must have evidence")
            elif all(ev.get("evidence_class") == "MEMORY_SIGNAL" for ev in evidence if isinstance(ev, dict)):
                errors.append(f"{context}: mapped claim {item.get('claim_id')} evidence cannot be only MEMORY_SIGNAL")
    context_control = pack.get("context_control", {})
    if not isinstance(context_control, dict):
        errors.append(f"{context}: context_control must be object")
    else:
        for ref_field in ("selected_references", "skipped_references"):
            refs = context_control.get(ref_field)
            if not isinstance(refs, list):
                errors.append(f"{context}: context_control.{ref_field} must be a list")
                continue
            for index, item in enumerate(refs):
                if not isinstance(item, dict):
                    errors.append(f"{context}: context_control.{ref_field}[{index}] must be object")
                    continue
                for required in ("reference", "reason", "evidence_limit"):
                    if not item.get(required):
                        errors.append(f"{context}: context_control.{ref_field}[{index}] missing {required}")


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


def _validate_eval_fixtures(schemas: dict[str, dict[str, Any]], errors: list[str]) -> None:
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
            "expected_skills",
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
        if not isinstance(route, dict) or "business_semantic_scope" not in route:
            errors.append(f"{context}: expected_route must declare business_semantic_scope")
        elif route.get("business_semantic_pack_required") is False and route.get("business_semantic_scope") != "none":
            errors.append(f"{context}: non-BSP case must set business_semantic_scope to none")
        sections = set(str(item) for item in fixture.get("expected_bsp_sections", []) or [])
        invalid_sections = sections - BSP_SECTIONS
        if invalid_sections:
            errors.append(f"{context}: invalid BSP sections {sorted(invalid_sections)}")
        if route.get("business_semantic_pack_required") is True and "business-semantic-control-plane" not in fixture.get("expected_capabilities", []):
            errors.append(f"{context}: BSP-required case must select business-semantic-control-plane")
        if not fixture.get("forbidden_behavior"):
            errors.append(f"{context}: forbidden_behavior must be non-empty")
        sample_bsp_path = fixture.get("sample_bsp_path")
        if sample_bsp_path:
            _validate_fixture_sample_bsp(str(sample_bsp_path), schemas, context, errors)


def _validate_fixture_sample_bsp(
    sample_bsp_path: str,
    schemas: dict[str, dict[str, Any]],
    context: str,
    errors: list[str],
) -> None:
    path = ROOT / sample_bsp_path
    if not path.is_file():
        errors.append(f"{context}: sample_bsp_path does not exist: {sample_bsp_path}")
        return
    try:
        instance = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{context}: sample_bsp_path invalid JSON: {exc}")
        return
    schema = schemas.get(BSP_SCHEMA)
    if not schema:
        errors.append(f"{context}: BSP schema unavailable for sample_bsp_path")
        return
    schema_errors = _schema_errors(schema, instance)
    if schema_errors:
        errors.extend(f"{context}: sample_bsp_path schema error: {item}" for item in schema_errors)
    _validate_bsp_semantics(instance, f"{context}:sample_bsp_path", errors)


def _sample_pack() -> dict[str, Any]:
    pack_path = SAMPLE_DIR / "valid-business-semantic-pack.json"
    if pack_path.is_file():
        return json.loads(pack_path.read_text(encoding="utf-8"))
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
                    "authoritative_enforcement_paths": ["src/domain/order.py"],
                    "preview_paths": ["src/api/orders.py"],
                    "defense_paths": ["src/db/order_constraints.sql"],
                    "audit_paths": ["src/audit/order_events.py"],
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
            "memory_projection": {"accepted": ["mem_current_owner"], "rejected": ["mem_wrong_layer"], "stale": ["mem_prior_cancel_rule"], "not_verified": ["mem_unknown_admin_path"]},
            "validation_map": [{"claim_id": "ORDER.CANCEL.AFTER_SHIP_DENIED", "claim_type": "rule", "validation_target": "tests/domain/test_order.py::test_shipped_order_cannot_cancel", "status": "mapped", "residual_risk": [], "evidence": [fact]}],
            "context_control": {
                "budget_mode": "single-stage",
                "selected_references": [{"reference": "135-business-semantic-control-plane", "reason": "rule authority mapping required", "budget_mode": "single-stage", "evidence_limit": "current source and mapped validation only", "residual_risk": []}],
                "skipped_references": [{"reference": "payment-trading-extension", "reason": "no payment behavior changed", "budget_mode": "single-stage", "evidence_limit": "not evidence for payment behavior", "residual_risk": ["payment edge not inspected"]}],
                "evidence_limits": ["memory is selector only"],
                "residual_context_risk": [],
            },
        }
    }


if __name__ == "__main__":
    raise SystemExit(main())
