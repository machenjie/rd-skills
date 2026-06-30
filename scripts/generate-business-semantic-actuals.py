#!/usr/bin/env python3
"""Generate or check deterministic Business Semantic actual outputs."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from validation_utils import fail_many, load_yaml_file

try:
    import yaml as _yaml
except Exception:  # pragma: no cover - depends on local environment
    _yaml = None


ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = ROOT / "evals" / "business-semantic"
OUTPUT_DIR = ROOT / "evals" / "business-semantic-outputs"
RESOLVER_DIR = ROOT / "src" / "hook-runtime" / "scripts"
EVAL_ROUTING_PATH = ROOT / "scripts" / "eval-routing.py"

GENERATOR = "scripts/generate-business-semantic-actuals.py"
ROUTE_SOURCE = "current deterministic route resolver / fixture route adapter"
REVIEW_SOURCE = "deterministic source/diff/prompt/trigger review skeleton"

_FORBIDDEN_GENERATOR_INPUT_KEYS = {
    "expected_route",
    "expected_skills",
    "expected_capabilities",
    "expected_quality_gates",
    "expected_bsp_sections",
    "expected_review_findings",
}

_ALLOWED_GENERATOR_INPUT_KEYS = {
    "case_id",
    "prompt",
    "routing_triggers",
    "source_context",
    "diff_context",
    "input_route_hint",
    "review_input_hint",
}

BSP_SECTIONS = [
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
]

SECTION_CAPABILITIES = {
    "task_business_intent": ["business-semantic-control-plane"],
    "business_vocabulary": ["domain-object-identification"],
    "business_objects": ["domain-object-identification"],
    "business_rules": ["business-rule-extraction"],
    "workflows": ["state-machine-modeling", "business-rule-extraction"],
    "data_and_signal_semantics": ["business-rule-extraction"],
    "code_mapping": ["implementation-structure-design"],
    "memory_projection": ["project-memory-governance", "repository-graph-analysis"],
    "validation_map": ["validation-broker"],
    "context_control": ["context-control-plane"],
}

REFERENCE_PRIORITY = [
    "business-semantic-control-plane",
    "business-rule-extraction",
    "domain-object-identification",
    "state-machine-modeling",
    "repository-graph-analysis",
    "validation-broker",
    "context-control-plane",
    "implementation-structure-design",
    "sql-professional-usage",
    "model-boundary-mapping",
]

FRONTEND_SKILLS = {"frontend-change-builder"}
FRONTEND_CAPABILITIES = {
    "page-component-decomposition",
    "routing-navigation-design",
    "state-management-design",
    "form-validation-design",
    "frontend-api-integration",
    "frontend-testing",
}
DELIVERY_SKILLS = {"delivery-release-gate"}
DELIVERY_CAPABILITIES = {
    "containerization",
    "kubernetes-gateway",
    "release-rollback",
    "ci-cd",
    "backup-recovery",
}


@dataclass(frozen=True)
class ReviewDetector:
    name: str
    category: str
    trigger_terms: tuple[str, ...]
    path_terms: tuple[str, ...]
    source_terms: tuple[str, ...]
    patch_terms: tuple[str, ...]
    builder: Callable[[str, dict[str, Any]], dict[str, Any]]


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    eval_dir = _repo_path(args.eval_dir)
    output_dir = _repo_path(args.output_dir)
    errors: list[str] = []
    cases = [(path, load_yaml_file(path)) for path in sorted(eval_dir.glob("*.yaml"))]
    if not cases:
        errors.append(f"{_display_path(eval_dir)}: no business-semantic fixtures found")
    risk_rules = _load_risk_rules()
    resolver = _load_resolver()
    generated: dict[Path, dict[str, Any]] = {}
    for path, case in cases:
        if not isinstance(case, dict):
            errors.append(f"{_display_path(path)}: fixture must be a mapping")
            continue
        case_id = str(case.get("case_id") or path.stem)
        generated[output_dir / f"{case_id}.actual.yaml"] = build_actual(path, case, risk_rules, resolver)

    if args.check:
        _check_outputs(generated, errors)
    else:
        output_dir.mkdir(parents=True, exist_ok=True)
        for path, actual in generated.items():
            path.write_text(_dump_yaml(actual), encoding="utf-8")
        print(f"generate-business-semantic-actuals: wrote {len(generated)} actual output(s)")

    if errors:
        return fail_many("generate-business-semantic-actuals", errors)
    if args.check:
        print(f"generate-business-semantic-actuals: OK checked {len(generated)} actual output(s)")
    return 0


def build_actual(
    fixture_path: Path,
    case: dict[str, Any],
    risk_rules: dict[str, dict[str, tuple[str, ...]]] | None = None,
    resolver: Any | None = None,
) -> dict[str, Any]:
    case_input = _generator_input(case)
    case_id = str(case_input.get("case_id") or fixture_path.stem)
    risk_rules = risk_rules if risk_rules is not None else _load_risk_rules()
    resolver = resolver if resolver is not None else _load_resolver()
    route_hint = case_input.get("input_route_hint") if isinstance(case_input.get("input_route_hint"), dict) else {}
    triggers = _string_list(case_input.get("routing_triggers"))
    paths = _fixture_paths(case_input)
    text = _fixture_text(case_input)
    stage = _input_stage(route_hint, triggers, text)
    bsp_required = _input_bsp_required(route_hint, triggers, text)
    scope = _input_scope(route_hint, case_id, bsp_required)
    selected_bsp_sections = _infer_bsp_sections(
        triggers=triggers,
        paths=paths,
        text=text,
        stage=stage,
        bsp_required=bsp_required,
    )
    classification = _resolver_classification(resolver, paths, text, bsp_required)
    context = resolver.build_active_skill_context(
        runtime="business-semantic-fixture",
        stage=_action_stage(stage),
        event_name="business-semantic-actual-generation",
        state=_resolver_state(stage),
        classification=classification,
    )
    rule_requirements = _trigger_requirements(triggers, risk_rules)
    selected_skills = _route_skills(context, rule_requirements, bsp_required, stage, selected_bsp_sections, triggers, paths, text)
    selected_capabilities = _route_capabilities(context, rule_requirements, bsp_required, selected_bsp_sections, triggers, paths, text)
    quality_gates = _route_gates(context, rule_requirements, bsp_required, stage, selected_bsp_sections, triggers, selected_skills, paths, text)
    if not bsp_required and not triggers:
        selected_skills = _unique(["backend-change-builder"])
        selected_capabilities = _unique(["minimal-correct-implementation"])
        quality_gates = _unique(["implementation gate"])

    actual_route = {
        "stage": stage,
        "detected_triggers": triggers,
        "selected_skills": selected_skills,
        "selected_capabilities": selected_capabilities,
        "required_quality_gates": quality_gates,
        "business_semantic_pack_required": bsp_required,
        "business_semantic_scope": scope,
        "selected_bsp_sections": selected_bsp_sections,
        "selected_references": _selected_reference_decisions(case_id, selected_capabilities, selected_bsp_sections, triggers, bsp_required),
        "skipped_references": _skipped_reference_decisions(case_id, selected_capabilities, bsp_required),
    }
    actual_review = {
        "business_semantic_pack_required": bsp_required,
        "findings": _review_findings(case_id, case_input),
        "forbidden_behavior_avoided": _forbidden_behavior_avoided(case_id, triggers, text, bsp_required),
        "residual_risk": _review_residual_risk(case_id, bsp_required),
    }
    return {
        "actual_metadata": {
            "generated_by": GENERATOR,
            "generation_mode": "deterministic",
            "source_fixture": _source_fixture_path(fixture_path),
            "route_source": ROUTE_SOURCE,
            "review_source": REVIEW_SOURCE,
        },
        "actual_route": actual_route,
        "actual_review": actual_review,
    }


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate deterministic Business Semantic actual outputs.")
    parser.add_argument("--check", action="store_true", help="Compare generated outputs with checked-in actual files.")
    parser.add_argument("--eval-dir", default=EVAL_DIR, type=Path, help="Directory containing business semantic YAML fixtures.")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, type=Path, help="Directory containing or receiving actual outputs.")
    return parser.parse_args(argv)


def _load_resolver() -> Any:
    if str(RESOLVER_DIR) not in sys.path:
        sys.path.insert(0, str(RESOLVER_DIR))
    import changeforge_runtime_route_resolver as resolver  # type: ignore[import-not-found]

    return resolver


def _load_risk_rules() -> dict[str, dict[str, tuple[str, ...]]]:
    spec = importlib.util.spec_from_file_location("eval_routing_for_business_semantic_actuals", EVAL_ROUTING_PATH)
    if spec is None or spec.loader is None:
        return {}
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module._load_risk_trigger_rules()  # type: ignore[attr-defined]


def _generator_input(case: dict[str, Any]) -> dict[str, Any]:
    # Expected fields are eval oracle. The generator must not read them.
    return {key: case.get(key) for key in _ALLOWED_GENERATOR_INPUT_KEYS if key in case}


def _resolver_classification(resolver: Any, paths: list[str], text: str, bsp_required: bool) -> dict[str, Any]:
    product_surfaces = resolver.detect_product_surfaces(paths, text=text)
    if bsp_required and "business-semantics" not in product_surfaces:
        product_surfaces.append("business-semantics")
    return {
        "product_surfaces": product_surfaces,
        "language_surfaces": resolver.detect_language_surfaces(paths, text=text),
        "risk_surfaces": resolver.detect_risk_surfaces(paths, text=text),
        "domain_extensions": resolver.detect_domain_extensions(paths, text=text),
        "conditional_capabilities": resolver.detect_conditional_capabilities(paths, text=text),
    }


def _fixture_paths(case: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for section_name, item_name in (("source_context", "files"), ("diff_context", "changed_files")):
        section = case.get(section_name)
        items = section.get(item_name, []) if isinstance(section, dict) else []
        for item in items if isinstance(items, list) else []:
            if isinstance(item, dict) and isinstance(item.get("path"), str):
                paths.append(item["path"])
    return _unique(paths)


def _fixture_text(case: dict[str, Any]) -> str:
    parts = [str(case.get("prompt") or "")]
    parts.extend(_string_list(case.get("routing_triggers")))
    for section_name, item_name in (("source_context", "files"), ("diff_context", "changed_files")):
        section = case.get(section_name)
        items = section.get(item_name, []) if isinstance(section, dict) else []
        for item in items if isinstance(items, list) else []:
            if isinstance(item, dict):
                parts.extend(str(item.get(key) or "") for key in ("path", "language", "content", "patch"))
    return "\n".join(part for part in parts if part)


def _action_stage(stage: str) -> str:
    return {
        "requirement-intake": "read",
        "testing": "test",
        "code-review": "review",
        "coding": "edit",
        "implementation-planning": "edit",
        "architecture-design": "edit",
    }.get(stage, "edit")


def _resolver_state(stage: str) -> dict[str, Any]:
    if stage == "coding":
        return {
            "read_evidence_seen": True,
            "implementation_preflight_complete": True,
            "test_plan_seen": True,
        }
    return {}


def _trigger_requirements(
    triggers: list[str],
    risk_rules: dict[str, dict[str, tuple[str, ...]]],
) -> dict[str, list[str]]:
    by_trigger = {key.casefold(): value for key, value in risk_rules.items()}
    result = {"skills": [], "capabilities": [], "quality_gates": []}
    for trigger in triggers:
        rule = by_trigger.get(trigger.casefold())
        if not rule:
            continue
        result["skills"].extend(rule.get("skills", ()))
        result["capabilities"].extend(rule.get("capabilities", ()))
        result["quality_gates"].extend(rule.get("quality_gates", ()))
    return {key: _unique(value) for key, value in result.items()}


def _input_stage(route_hint: dict[str, Any], triggers: list[str], text: str) -> str:
    stage = route_hint.get("stage")
    if isinstance(stage, str) and stage.strip():
        return stage
    lowered = _search_text(triggers, text)
    if "no behavior change" in lowered or "typo" in lowered:
        return "coding"
    if "requirement" in lowered or "business vocabulary ambiguous" in lowered:
        return "requirement-intake"
    if "golden case" in lowered:
        return "testing"
    if "technical refactor" in lowered or "code review" in lowered:
        return "code-review"
    if "workflow" in lowered or "authority unknown" in lowered or "business invariant changed" in lowered:
        return "architecture-design"
    return "implementation-planning"


def _input_bsp_required(route_hint: dict[str, Any], triggers: list[str], text: str) -> bool:
    if "business_semantic_pack_required" in route_hint:
        return bool(route_hint.get("business_semantic_pack_required"))
    lowered = _search_text(triggers, text)
    if "no behavior change" in lowered and not triggers:
        return False
    return any(
        token in lowered
        for token in (
            "business ",
            "dto ",
            "semantic",
            "eligibility",
            "entitlement",
            "renewal",
            "denial",
            "reason code",
            "workflow",
            "memory",
            "golden case",
            "sql",
        )
    )


def _input_scope(route_hint: dict[str, Any], case_id: str, bsp_required: bool) -> str:
    scope = route_hint.get("business_semantic_scope")
    if isinstance(scope, str) and scope.strip():
        return scope
    return case_id if bsp_required else "none"


def _infer_bsp_sections(
    *,
    triggers: list[str],
    paths: list[str],
    text: str,
    stage: str,
    bsp_required: bool,
) -> list[str]:
    if not bsp_required:
        return []
    lowered = _search_text(triggers, text)
    sections: list[str] = []
    if _has_high_risk_business_signal(lowered):
        sections.extend(BSP_SECTIONS)
    if "business context missing" in lowered:
        sections.extend(["task_business_intent", "business_vocabulary", "context_control"])
    if "business vocabulary ambiguous" in lowered or "business term ambiguous" in lowered:
        sections.extend(
            [
                "task_business_intent",
                "business_vocabulary",
                "business_objects",
                "code_mapping",
                "validation_map",
                "context_control",
            ]
        )
    if "business object ownership unclear" in lowered or "dto used as business object" in lowered:
        sections.extend(["business_vocabulary", "business_objects", "code_mapping", "validation_map", "context_control"])
    if (
        "business rule authority unknown" in lowered
        or "business invariant changed" in lowered
        or "hidden rule" in lowered
        or "hidden in sql" in lowered
        or "hidden in sql/controller/ui/test" in lowered
    ):
        sections.extend(["business_rules", "code_mapping", "validation_map", "context_control"])
        if "controller" in lowered or "customer" in lowered or "order" in lowered:
            sections.append("business_objects")
    if "business workflow state unclear" in lowered or "status transition" in lowered or "workflow transition" in lowered:
        sections.extend(["workflows", "business_rules", "validation_map", "context_control"])
    if "business memory affects decision" in lowered or "stale business memory" in lowered or "memory used as business fact" in lowered:
        sections.extend(["memory_projection", "business_rules", "validation_map", "context_control", "code_mapping"])
        if "workflow" in lowered or "status transition" in lowered:
            sections.append("workflows")
    if "graph used as business fact" in lowered:
        sections.extend(["code_mapping", "validation_map", "context_control"])
    if _has_sql_signal(paths, text):
        sections.append("data_and_signal_semantics")
    if "golden case" in lowered or "reason code" in lowered or "rule changed" in lowered:
        sections.extend(["business_rules", "validation_map", "context_control"])
    if stage in {"implementation-planning", "code-review", "architecture-design"} and (
        "rule" in lowered or "semantic" in lowered or "dto" in lowered
    ):
        sections.append("code_mapping")
    return _ordered_sections(sections)


def _route_skills(
    context: dict[str, Any],
    rule_requirements: dict[str, list[str]],
    bsp_required: bool,
    stage: str,
    selected_bsp_sections: list[str],
    triggers: list[str],
    paths: list[str],
    text: str,
) -> list[str]:
    search = _search_text(triggers, text)
    skills = _filtered_context_skills(context, paths, search)
    skills.extend(rule_requirements["skills"])
    if stage == "requirement-intake":
        skills.append("change-intake-compiler")
    if stage == "architecture-design":
        skills.append("architecture-impact-reviewer")
    if stage == "code-review":
        skills.append("ai-code-review-refactor")
    if bsp_required and any(
        section in selected_bsp_sections
        for section in ("business_vocabulary", "business_objects", "business_rules", "workflows", "memory_projection")
    ):
        skills.append("domain-impact-modeler")
    if _has_sql_signal(paths, text):
        skills.append("data-middleware-change-builder")
    if _has_controller_signal(paths, text) or "controller" in search:
        skills.append("backend-change-builder")
    if "dto used as business object" in search or "dto" in search:
        skills.append("data-api-contract-changer")
    if any(token in search for token in ("golden case", "workflow", "hidden rule", "hidden in sql", "semantic review", "memory")):
        skills.append("quality-test-gate")
    if "technical refactor" in search or "refactor" in search:
        skills.extend(["ai-code-review-refactor", "quality-test-gate"])
    if "business vocabulary ambiguous" in search:
        skills.append("change-documentation-gate")
    if _has_high_risk_business_signal(search):
        skills.extend(["change-intake-compiler", "domain-impact-modeler", "quality-test-gate", "ai-code-review-refactor"])
    return _filter_unrelated_surfaces(_unique(skills), paths, search, kind="skills")


def _route_capabilities(
    context: dict[str, Any],
    rule_requirements: dict[str, list[str]],
    bsp_required: bool,
    selected_bsp_sections: list[str],
    triggers: list[str],
    paths: list[str],
    text: str,
) -> list[str]:
    search = _search_text(triggers, text)
    capabilities = _filtered_context_capabilities(context, paths, search)
    capabilities.extend(rule_requirements["capabilities"])
    for section in selected_bsp_sections:
        capabilities.extend(SECTION_CAPABILITIES.get(section, []))
    if bsp_required:
        capabilities.append("business-semantic-control-plane")
    if any(token in search for token in ("business rule", "golden case", "hidden rule", "semantic review", "invariant")):
        capabilities.append("business-rule-extraction")
    if any(token in search for token in ("business vocabulary", "business object", "dto used", "entitlement", "eligibility")):
        capabilities.append("domain-object-identification")
    if any(token in search for token in ("workflow", "status transition", "renewal status")):
        capabilities.append("state-machine-modeling")
    if "validation_map" in selected_bsp_sections or "golden case" in search or _has_high_risk_business_signal(search):
        capabilities.append("validation-broker")
    if "context_control" in selected_bsp_sections or "memory" in search or "graph" in search:
        capabilities.append("context-control-plane")
    if "memory" in search:
        capabilities.extend(["project-memory-governance", "repository-graph-analysis"])
    if "code_mapping" in selected_bsp_sections or "hidden rule" in search:
        capabilities.append("repository-graph-analysis")
    if _has_sql_signal(paths, text):
        capabilities.append("sql-professional-usage")
    if "dto used as business object" in search or "partnerorderresponse" in search:
        capabilities.append("model-boundary-mapping")
    if "code_mapping" in selected_bsp_sections or "controller" in search:
        capabilities.append("implementation-structure-design")
    if "technical refactor" in search or "refactor" in search:
        capabilities.extend(["ai-code-review-refactor", "plan-execution-consistency"])
    return _filter_unrelated_surfaces(_unique(capabilities), paths, search, kind="capabilities")


def _route_gates(
    context: dict[str, Any],
    rule_requirements: dict[str, list[str]],
    bsp_required: bool,
    stage: str,
    selected_bsp_sections: list[str],
    triggers: list[str],
    selected_skills: list[str],
    paths: list[str],
    text: str,
) -> list[str]:
    search = _search_text(triggers, text)
    gates = _filtered_context_gates(context, paths, search)
    gates.extend(rule_requirements["quality_gates"])
    if stage == "requirement-intake":
        gates.append("requirement gate")
    if stage == "architecture-design":
        gates.append("architecture gate")
    if stage in {"coding", "implementation-planning", "code-review"}:
        gates.append("implementation gate")
    if bsp_required and "domain-impact-modeler" in selected_skills:
        gates.append("domain gate")
    if _has_sql_signal(paths, text) or "data_and_signal_semantics" in selected_bsp_sections or "data-api-contract-changer" in selected_skills:
        gates.append("API/data gate")
    if "quality-test-gate" in selected_skills or "validation_map" in selected_bsp_sections or "golden case" in search:
        gates.append("test gate")
    if "ai-code-review-refactor" in selected_skills or "semantic review" in search:
        gates.append("AI review gate")
    if "change-documentation-gate" in selected_skills:
        gates.append("documentation gate")
    if "memory" in search or "graph" in search:
        gates.append("execution discipline gate")
    if _has_high_risk_business_signal(search):
        gates.extend(["requirement gate", "domain gate", "architecture gate", "API/data gate", "test gate", "AI review gate"])
    return _unique(gates)


def _selected_reference_decisions(
    case_id: str,
    selected_capabilities: list[str],
    selected_bsp_sections: list[str],
    triggers: list[str],
    bsp_required: bool,
) -> list[dict[str, Any]]:
    if not bsp_required:
        return []
    selected = set(selected_capabilities)
    search = _search_text(triggers, "")
    related: list[str] = []
    for capability in REFERENCE_PRIORITY:
        if capability not in selected:
            continue
        if capability == "business-semantic-control-plane":
            related.append(capability)
        elif capability == "business-rule-extraction" and (
            "business_rules" in selected_bsp_sections or "hidden" in search or "golden" in search
        ):
            related.append(capability)
        elif capability == "domain-object-identification" and (
            "business_vocabulary" in selected_bsp_sections or "business_objects" in selected_bsp_sections
        ):
            related.append(capability)
        elif capability == "state-machine-modeling" and "workflows" in selected_bsp_sections:
            related.append(capability)
        elif capability == "repository-graph-analysis" and (
            "memory_projection" in selected_bsp_sections or "code_mapping" in selected_bsp_sections
        ):
            related.append(capability)
        elif capability == "validation-broker" and "validation_map" in selected_bsp_sections:
            related.append(capability)
        elif capability == "context-control-plane" and "context_control" in selected_bsp_sections:
            related.append(capability)
        elif capability == "implementation-structure-design" and "code_mapping" in selected_bsp_sections:
            related.append(capability)
        elif capability == "sql-professional-usage" and "sql" in search:
            related.append(capability)
        elif capability == "model-boundary-mapping" and "dto" in search:
            related.append(capability)
    decisions: list[dict[str, Any]] = []
    for capability in related[:4]:
        decisions.append(
            {
                "reference": _capability_reference(capability),
                "reason": f"{capability} selected by deterministic resolver/trigger adapter for {case_id}",
                "evidence_limit": "deterministic fixture source/diff snippets and routing triggers only",
                "residual_risk": ["does not prove live LLM behavior or live business correctness"],
            }
        )
    return decisions


def _skipped_reference_decisions(
    case_id: str,
    selected_capabilities: list[str],
    bsp_required: bool,
) -> list[dict[str, Any]]:
    if not bsp_required:
        return [
            {
                "reference": "references/capabilities/135-business-semantic-control-plane.md",
                "reason": f"{case_id} has no business semantic trigger and does not require BSP",
                "evidence_limit": "skip applies only to this deterministic local fixture",
                "residual_risk": [],
            }
        ]
    skipped = []
    for capability, reason in (
        ("payment-trading-extension", "no payment, ledger, settlement, or trading signal in the fixture"),
        ("live-business-correctness", "deterministic fixture checks structure, not live domain truth"),
    ):
        if capability not in selected_capabilities:
            skipped.append(
                {
                    "reference": capability,
                    "reason": reason,
                    "evidence_limit": "not evidence for omitted surface correctness",
                    "residual_risk": ["route separately if the omitted surface appears in current source"],
                }
            )
    return skipped


def _capability_reference(name: str) -> str:
    resolver = _load_resolver()
    cap_id = getattr(resolver, "CAPABILITY_IDS", {}).get(name)
    if cap_id:
        return f"references/capabilities/{cap_id}-{name}.md"
    return name


def _search_text(triggers: list[str], text: str) -> str:
    return "\n".join([*triggers, text]).casefold()


def _ordered_sections(sections: list[str]) -> list[str]:
    selected = set(sections)
    return [section for section in BSP_SECTIONS if section in selected]


def _has_sql_signal(paths: list[str], text: str) -> bool:
    lowered = text.casefold()
    return any(path.endswith(".sql") or "/sql/" in path for path in paths) or any(
        token in lowered for token in ("select ", " where ", "\nwhere ", " join ", "language: sql")
    )


def _has_controller_signal(paths: list[str], text: str) -> bool:
    lowered = text.casefold()
    return any("controller" in path.casefold() for path in paths) or "controller" in lowered


def _has_frontend_signal(paths: list[str], search: str) -> bool:
    return any(path.endswith((".tsx", ".jsx")) for path in paths) or any(
        token in search
        for token in (
            "/frontend/",
            "/components/",
            "/ui/",
            "react component",
            "browser route",
            "frontend route",
            "user interface",
        )
    )


def _has_delivery_signal(paths: list[str], search: str) -> bool:
    return any(
        token in search or any(token in path.casefold() for path in paths)
        for token in ("deployment", "kubernetes", "k8s", "helm", "rollout", "container", "docker", "ci-cd", "github actions")
    )


def _has_payment_signal(paths: list[str], search: str) -> bool:
    return any(
        token in search or any(token in path.casefold() for path in paths)
        for token in ("payment", "ledger", "settlement", "trading", "checkout", "invoice", "refund", "chargeback")
    )


def _has_high_risk_business_signal(search: str) -> bool:
    return any(token in search for token in ("entitlement", "eligibility", "denial", "reason code")) or (
        "renewal" in search and ("transition" in search or "reason" in search)
    )


def _filtered_context_skills(context: dict[str, Any], paths: list[str], search: str) -> list[str]:
    return _filter_unrelated_surfaces(_string_list(context.get("selected_skills")), paths, search, kind="skills")


def _filtered_context_capabilities(context: dict[str, Any], paths: list[str], search: str) -> list[str]:
    return _filter_unrelated_surfaces(
        _string_list(context.get("selected_capabilities")),
        paths,
        search,
        kind="capabilities",
    )


def _filtered_context_gates(context: dict[str, Any], paths: list[str], search: str) -> list[str]:
    gates = _string_list(context.get("required_quality_gates"))
    if not _has_delivery_signal(paths, search):
        gates = [gate for gate in gates if gate != "delivery gate"]
    return gates


def _filter_unrelated_surfaces(values: list[str], paths: list[str], search: str, *, kind: str) -> list[str]:
    blocked: set[str] = set()
    if not _has_frontend_signal(paths, search):
        blocked.update(FRONTEND_SKILLS if kind == "skills" else FRONTEND_CAPABILITIES)
    if not _has_delivery_signal(paths, search):
        blocked.update(DELIVERY_SKILLS if kind == "skills" else DELIVERY_CAPABILITIES)
    if not _has_payment_signal(paths, search):
        blocked.add("payment-trading-extension")
    if kind == "capabilities":
        if "memory" not in search:
            blocked.add("project-memory-governance")
        if "workflow" not in search and "transition" not in search:
            blocked.add("state-machine-modeling")
    return [value for value in values if value not in blocked]


def _source_items(case: dict[str, Any]) -> list[dict[str, Any]]:
    section = case.get("source_context")
    items = section.get("files", []) if isinstance(section, dict) else []
    return [item for item in items if isinstance(item, dict)]


def _changed_items(case: dict[str, Any]) -> list[dict[str, Any]]:
    section = case.get("diff_context")
    items = section.get("changed_files", []) if isinstance(section, dict) else []
    return [item for item in items if isinstance(item, dict)]


def _flatten(value: Any) -> str:
    return " ".join(str(value or "").split())


def _patch_lines(case: dict[str, Any]) -> list[tuple[str, str]]:
    lines: list[tuple[str, str]] = []
    for item in _changed_items(case):
        path = str(item.get("path") or "diff")
        for line in str(item.get("patch") or "").splitlines():
            stripped = line.strip()
            if stripped.startswith(("+", "-")):
                lines.append((path, stripped[1:].strip()))
    return lines


def _finding(
    *,
    finding_id: str,
    severity: str,
    category: str,
    impacted_claim: str,
    evidence: list[str],
    required_fix: str,
    validation_required: str = "source/diff evidence, owner review, or changed-path validation required",
) -> dict[str, Any]:
    return {
        "finding_id": finding_id,
        "severity": severity,
        "category": category,
        "impacted_claim": impacted_claim,
        "evidence": _unique(["source: deterministic-fixture-review", *evidence]),
        "required_fix": required_fix,
        "validation_required": validation_required,
    }


def _hidden_sql_rule_finding(case_id: str, case: dict[str, Any]) -> dict[str, Any]:
    evidence = _sql_evidence(case)
    return _finding(
        finding_id="BSP-HIDDEN-SQL-RULE",
        severity=_default_severity(case_id),
        category="hidden_sql_rule",
        impacted_claim="subscription renewal eligibility status filter",
        evidence=evidence,
        required_fix=(
            "SQL condition is a hidden business rule and needs rule_id, owner, authoritative enforcement layer, "
            "golden case, changed-path validation."
        ),
    )


def _controller_only_rule_finding(case_id: str, case: dict[str, Any]) -> dict[str, Any]:
    evidence = _controller_evidence(case)
    return _finding(
        finding_id="BSP-CONTROLLER-ONLY-RULE",
        severity=_default_severity(case_id),
        category="controller_only_rule",
        impacted_claim="order cancellation after shipped",
        evidence=evidence,
        required_fix=(
            "controller-only rule can be bypassed by jobs/admin/import path; route to business-rule-extraction "
            "and domain enforcement."
        ),
    )


def _dto_as_domain_object_finding(case_id: str, case: dict[str, Any]) -> dict[str, Any]:
    return _finding(
        finding_id="BSP-DTO-AS-DOMAIN",
        severity=_default_severity(case_id),
        category="dto_as_domain_object",
        impacted_claim="PartnerOrderResponse internal order model",
        evidence=[
            "external DTO passed into domain service without mapper",
            "PartnerOrderResponse replaces Order",
            *_matching_patch_lines(case, ("PartnerOrderResponse", "Order")),
        ],
        required_fix=(
            "DTO/table/resource model is being used as domain object; requires model-boundary-mapping and "
            "domain-object-identification."
        ),
    )


def _workflow_transition_finding(case_id: str, case: dict[str, Any]) -> dict[str, Any]:
    return _finding(
        finding_id="BSP-WORKFLOW-FORBIDDEN-GAP",
        severity=_default_severity(case_id),
        category="workflow_transition_gap",
        impacted_claim="approved claim can return to draft",
        evidence=[
            "enum/status change lacks forbidden transition tests",
            "APPROVED to DRAFT transition added",
            *_matching_patch_lines(case, ("ClaimStatus.APPROVED", "ClaimStatus.DRAFT", "REFUNDED", "CANCELLED")),
        ],
        required_fix="workflow transition table and invalid transition tests required.",
    )


def _semantic_refactor_finding(case_id: str, case: dict[str, Any]) -> dict[str, Any]:
    return _finding(
        finding_id="BSP-SEMANTIC-REFACTOR",
        severity=_default_severity(case_id),
        category="semantic_diff",
        impacted_claim="eligibility helper refactor preserves behavior",
        evidence=[
            "condition precedence and denial reason changed",
            "enterprise_discount changed to discount_eligible",
            *_matching_patch_lines(case, ("enterprise_discount", "discount_eligible", "trial_accounts_ineligible")),
        ],
        required_fix=(
            "refactor changes business semantics and cannot be approved as behavior-preserving without golden case / "
            "characterization test."
        ),
    )


def _stale_memory_finding(case_id: str, case: dict[str, Any]) -> dict[str, Any]:
    evidence = [
        "memory signal conflicts with current source owner",
        "billing/owners.yaml declares revenue-platform",
        *_matching_source_lines(case, ("owner: revenue-platform", "remembered_owner", "source_check_required")),
        *_matching_patch_lines(case, ("owner assumed from memory", "DISCOUNT_RULE_OWNER")),
    ]
    return _finding(
        finding_id="BSP-STALE-MEMORY",
        severity=_default_severity(case_id),
        category="stale_memory_source_truth",
        impacted_claim="prior discount owner from memory",
        evidence=evidence,
        required_fix="memory is stale selector, not source truth; current source must win or residual risk must be recorded.",
    )


def _golden_case_gap_finding(case_id: str, case: dict[str, Any]) -> dict[str, Any]:
    return _finding(
        finding_id="BSP-GOLDEN-CASE-GAP",
        severity=_default_severity(case_id),
        category="golden_case_gap",
        impacted_claim="new cancellation reason code",
        evidence=["business golden case missing for reason code", _prompt_evidence(case)],
        required_fix="business golden case missing for reason code",
        validation_required="business golden case and reason-code regression required",
    )


def _underroute_business_semantics_finding(case_id: str, case: dict[str, Any]) -> dict[str, Any]:
    return _finding(
        finding_id="BSP-UNDERROUTE-HIGH-RISK",
        severity="critical",
        category="underroute_business_semantics",
        impacted_claim="enterprise entitlement eligibility, renewal status, denial reasons",
        evidence=["BSP required", "rule/workflow/object/golden coverage required", _prompt_evidence(case)],
        required_fix="BSP required, rule/workflow/object/golden coverage required",
    )


def _bsp_skipped_finding(case_id: str, case: dict[str, Any]) -> dict[str, Any]:
    return _finding(
        finding_id="BSP-SKIPPED-LOCAL-TYPO",
        severity="low",
        category="bsp_skipped",
        impacted_claim="typo-only internal log message",
        evidence=["BSP should be skipped with rationale", _prompt_evidence(case)],
        required_fix="BSP should be skipped with rationale",
        validation_required="minimal implementation verification only",
    )


def _ambiguous_term_finding(case_id: str, case: dict[str, Any]) -> dict[str, Any]:
    return _finding(
        finding_id="BSP-AMBIGUOUS-TERM",
        severity=_default_severity(case_id),
        category="ambiguous_business_vocabulary",
        impacted_claim="Account rename to Customer",
        evidence=["same term has multiple owning contexts", "owner review required", _prompt_evidence(case)],
        required_fix="same term has multiple owning contexts, owner review required",
    )


REVIEW_DETECTORS = (
    ReviewDetector(
        name="hidden-rule-in-sql",
        category="hidden_sql_rule",
        trigger_terms=("business rule hidden in sql/controller/ui/test", "business rule authority unknown", "hidden sql rule"),
        path_terms=(".sql", "/sql/"),
        source_terms=("select ", " where ", "status", "eligibility"),
        patch_terms=("where", "status", "eligibility"),
        builder=_hidden_sql_rule_finding,
    ),
    ReviewDetector(
        name="controller-only-business-rule",
        category="controller_only_rule",
        trigger_terms=("business rule hidden in sql/controller/ui/test", "business rule authority unknown", "hidden controller rule"),
        path_terms=("controller",),
        source_terms=("if ", "return ", "status", "permission", "order.cancel()"),
        patch_terms=("if ", "status", "permission", "customer_tier", "age_days"),
        builder=_controller_only_rule_finding,
    ),
    ReviewDetector(
        name="dto-as-domain-object",
        category="dto_as_domain_object",
        trigger_terms=("dto used as business object", "dto used as domain object", "business object ownership unclear"),
        path_terms=("models.py", "/api/", "/domain/"),
        source_terms=("partnerorderresponse", "class order", "refund_allowed"),
        patch_terms=("partnerorderresponse", "order:", "return_window"),
        builder=_dto_as_domain_object_finding,
    ),
    ReviewDetector(
        name="workflow-transition-added",
        category="workflow_transition_gap",
        trigger_terms=("business workflow state unclear", "business invariant changed", "workflow transition"),
        path_terms=("status", "transition"),
        source_terms=("claimstatus", "approved", "submitted"),
        patch_terms=("claimstatus.approved", "claimstatus.draft", "refunded", "cancelled"),
        builder=_workflow_transition_finding,
    ),
    ReviewDetector(
        name="refactor-changes-business-semantics",
        category="semantic_diff",
        trigger_terms=("technical refactor may change business semantics", "business semantic review required", "refactor"),
        path_terms=("eligibility",),
        source_terms=("enterprise_discount", "trial_accounts_ineligible", "minimum_invoice_total"),
        patch_terms=("enterprise_discount", "discount_eligible", "trial_accounts_ineligible"),
        builder=_semantic_refactor_finding,
    ),
    ReviewDetector(
        name="stale-business-memory",
        category="stale_memory_source_truth",
        trigger_terms=("business memory affects decision", "memory used as business fact", "stale business memory"),
        path_terms=("memory", "owners"),
        source_terms=("owner: revenue-platform", "remembered_owner", "source_check_required"),
        patch_terms=("owner assumed from memory", "discount_rule_owner"),
        builder=_stale_memory_finding,
    ),
    ReviewDetector(
        name="business-golden-case-missing",
        category="golden_case_gap",
        trigger_terms=("business golden case missing", "reason code", "golden case missing"),
        path_terms=(),
        source_terms=(),
        patch_terms=(),
        builder=_golden_case_gap_finding,
    ),
    ReviewDetector(
        name="under-routing-high-risk-business-change",
        category="underroute_business_semantics",
        trigger_terms=("entitlement", "eligibility", "denial", "reason code", "business semantic review required"),
        path_terms=(),
        source_terms=(),
        patch_terms=(),
        builder=_underroute_business_semantics_finding,
    ),
    ReviewDetector(
        name="over-routing-simple-local-change",
        category="bsp_skipped",
        trigger_terms=("no behavior change", "typo"),
        path_terms=(),
        source_terms=(),
        patch_terms=(),
        builder=_bsp_skipped_finding,
    ),
    ReviewDetector(
        name="ambiguous-business-term",
        category="ambiguous_business_vocabulary",
        trigger_terms=("business vocabulary ambiguous", "business term ambiguous"),
        path_terms=(),
        source_terms=(),
        patch_terms=(),
        builder=_ambiguous_term_finding,
    ),
)


def _fixture_review_finding(case_id: str, case: dict[str, Any]) -> dict[str, Any]:
    return _finding(
        finding_id=f"BSP-{case_id.upper()}-NO-FINDING",
        severity="low",
        category="fixture_review",
        impacted_claim=str(case.get("prompt") or case_id),
        evidence=[_prompt_evidence(case)],
        required_fix="Resolve deterministic fixture review finding.",
        validation_required="fixture should expose source, diff, prompt, or routing-trigger evidence",
    )


def _sql_evidence(case: dict[str, Any]) -> list[str]:
    evidence: list[str] = []
    for item in _source_items(case):
        path = str(item.get("path") or "source")
        source = _flatten(item.get("content"))
        if "select " in source.casefold() or " where " in source.casefold():
            evidence.append(f"{path}: {source[:220]}")
    for path, line in _patch_lines(case):
        if any(token in line.casefold() for token in ("where", "join", "status", "eligibility")):
            evidence.append(f"{path}: {line}")
    return evidence or [_prompt_evidence(case)]


def _controller_evidence(case: dict[str, Any]) -> list[str]:
    evidence: list[str] = []
    for item in _source_items(case):
        path = str(item.get("path") or "source")
        lines = [line.strip() for line in str(item.get("content") or "").splitlines()]
        for index, line in enumerate(lines):
            if line.startswith("if ") and index + 1 < len(lines) and lines[index + 1].startswith("return "):
                evidence.append(f"{path}: {line} {lines[index + 1]}")
            elif "order.cancel()" in line and "job" in path.casefold():
                evidence.append(f"{path} bypass path calls order.cancel()")
    evidence.extend(_matching_patch_lines(case, ("customer_tier", "premium", "age_days")))
    return evidence or [_prompt_evidence(case)]


def _matching_source_lines(case: dict[str, Any], tokens: tuple[str, ...]) -> list[str]:
    matches: list[str] = []
    lowered_tokens = tuple(token.casefold() for token in tokens)
    for item in _source_items(case):
        path = str(item.get("path") or "source")
        for line in str(item.get("content") or "").splitlines():
            stripped = line.strip()
            if any(token in stripped.casefold() for token in lowered_tokens):
                matches.append(f"{path}: {stripped}")
    return matches


def _matching_patch_lines(case: dict[str, Any], tokens: tuple[str, ...]) -> list[str]:
    lowered_tokens = tuple(token.casefold() for token in tokens)
    return [f"{path}: {line}" for path, line in _patch_lines(case) if any(token in line.casefold() for token in lowered_tokens)]


def _prompt_evidence(case: dict[str, Any]) -> str:
    prompt = str(case.get("prompt") or "fixture prompt")
    triggers = ", ".join(_string_list(case.get("routing_triggers")))
    if triggers:
        return f"prompt/triggers: {prompt} | {triggers}"
    return f"prompt: {prompt}"


def _forbidden_behavior_avoided(case_id: str, triggers: list[str], text: str, bsp_required: bool) -> list[str]:
    by_case = {
        "hidden-rule-in-sql": ["approve SQL condition without rule catalog", "skip changed-path validation"],
        "controller-only-business-rule": ["leave rule only in controller", "no bypass path scan"],
        "dto-as-domain-object": ["treat external DTO as aggregate", "skip compatibility risk"],
        "workflow-transition-added": ["add enum value only", "skip invalid transition coverage"],
        "refactor-changes-business-semantics": ["approve as behavior-preserving without rule golden cases"],
        "stale-business-memory": ["treat memory as current owner", "skip source reread"],
        "business-golden-case-missing": ["claim green suite proves new business behavior without golden case"],
        "over-routing-simple-local-change": ["select business-semantic-control-plane", "require full BSP"],
        "ambiguous-business-term": ["treat term rename as text-only refactor", "memory as FACT"],
        "under-routing-high-risk-business-change": ["route directly to coding", "skip semantic review"],
    }
    if case_id in by_case:
        return by_case[case_id]
    search = _search_text(triggers, text)
    avoided: list[str] = []
    if not bsp_required:
        avoided.extend(["select business-semantic-control-plane", "require full BSP"])
    if "memory" in search:
        avoided.extend(["treat memory as current owner", "skip source reread"])
    if "golden case" in search:
        avoided.append("claim green suite proves new business behavior without golden case")
    return _unique(avoided)


def _detector_matches(detector: ReviewDetector, case: dict[str, Any]) -> bool:
    signal_text = _search_text(_string_list(case.get("routing_triggers")), str(case.get("prompt") or ""))
    path_text = "\n".join(_fixture_paths(case)).casefold()
    source_text = "\n".join(
        "\n".join(str(item.get(key) or "") for key in ("path", "language", "content"))
        for item in _source_items(case)
    ).casefold()
    patch_text = "\n".join(
        "\n".join(str(item.get(key) or "") for key in ("path", "patch"))
        for item in _changed_items(case)
    ).casefold()
    return (
        _terms_match(detector.trigger_terms, signal_text)
        and _terms_match(detector.path_terms, path_text)
        and _terms_match(detector.source_terms, source_text)
        and _terms_match(detector.patch_terms, patch_text)
    )


def _terms_match(terms: tuple[str, ...], text: str) -> bool:
    return not terms or any(term.casefold() in text for term in terms)


def _case_id_fallback_matches(detector: ReviewDetector, case_id: str) -> bool:
    # Compatibility tie-breaker only: business semantic evidence must come from
    # prompt, routing triggers, source context, or diff context.
    return detector.name == case_id


def _review_findings(case_id: str, case: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for detector in REVIEW_DETECTORS:
        if _detector_matches(detector, case) or _case_id_fallback_matches(detector, case_id):
            findings.append(detector.builder(case_id, case))
    if not findings:
        findings.append(_fixture_review_finding(case_id, case))
    return findings


def _default_severity(case_id: str) -> str:
    return "critical" if case_id == "under-routing-high-risk-business-change" else "high"


def _review_residual_risk(case_id: str, bsp_required: bool) -> list[str]:
    if not bsp_required:
        return ["none for business semantic coverage"]
    return [
        f"{case_id} actual is deterministic fixture evidence only",
        "does not prove live LLM behavior or live business correctness",
    ]


def _check_outputs(generated: dict[Path, dict[str, Any]], errors: list[str]) -> None:
    for path, expected in generated.items():
        if not path.is_file():
            errors.append(f"{_display_path(path)}: missing checked-in actual output")
            continue
        actual = load_yaml_file(path)
        if actual != expected:
            errors.append(f"{_display_path(path)}: checked-in actual output is stale; rerun {GENERATOR}")


def _dump_yaml(data: dict[str, Any]) -> str:
    if _yaml is not None:
        return _yaml.safe_dump(data, sort_keys=False, allow_unicode=False, default_flow_style=False)
    return "\n".join(_dump_yaml_lines(data, 0)) + "\n"


def _dump_yaml_lines(value: Any, indent: int) -> list[str]:
    prefix = " " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, item in value.items():
            if isinstance(item, dict):
                if item:
                    lines.append(f"{prefix}{key}:")
                    lines.extend(_dump_yaml_lines(item, indent + 2))
                else:
                    lines.append(f"{prefix}{key}: {{}}")
            elif isinstance(item, list):
                if item:
                    lines.append(f"{prefix}{key}:")
                    lines.extend(_dump_yaml_lines(item, indent + 2))
                else:
                    lines.append(f"{prefix}{key}: []")
            else:
                lines.append(f"{prefix}{key}: {_yaml_scalar(item)}")
        return lines
    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, dict):
                lines.append(f"{prefix}-")
                lines.extend(_dump_yaml_lines(item, indent + 2))
            elif isinstance(item, list):
                lines.append(f"{prefix}-")
                lines.extend(_dump_yaml_lines(item, indent + 2))
            else:
                lines.append(f"{prefix}- {_yaml_scalar(item)}")
        return lines
    return [f"{prefix}{_yaml_scalar(value)}"]


def _yaml_scalar(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    if isinstance(value, int | float):
        return str(value)
    return json.dumps(str(value), ensure_ascii=True)


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if value is None:
        return []
    return [str(value)] if str(value).strip() else []


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = str(value).strip()
        if not key or key in seen:
            continue
        result.append(key)
        seen.add(key)
    return result


def _repo_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _source_fixture_path(path: Path) -> str:
    parts = path.parts
    for index, part in enumerate(parts[:-1]):
        if part == "evals" and parts[index + 1] == "business-semantic":
            return str(Path(*parts[index:]))
    return _display_path(path)


if __name__ == "__main__":
    raise SystemExit(main())
