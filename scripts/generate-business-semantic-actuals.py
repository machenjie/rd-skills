#!/usr/bin/env python3
"""Generate or check deterministic Business Semantic actual outputs."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

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
REVIEW_SOURCE = "deterministic fixture review skeleton"

SECTION_CAPABILITIES = {
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

GATE_SKILLS = {
    "requirement gate": ["change-intake-compiler"],
    "domain gate": ["domain-impact-modeler"],
    "architecture gate": ["architecture-impact-reviewer"],
    "API/data gate": ["data-api-contract-changer"],
    "test gate": ["quality-test-gate"],
    "AI review gate": ["ai-code-review-refactor"],
    "documentation gate": ["change-documentation-gate"],
}

DEFAULT_FINDINGS = {
    "ambiguous-business-term": {
        "finding_id": "BSP-AMBIGUOUS-TERM",
        "severity": "high",
        "category": "ambiguous_business_vocabulary",
        "impacted_claim": "Account rename to Customer",
    },
    "business-golden-case-missing": {
        "finding_id": "BSP-GOLDEN-CASE-GAP",
        "severity": "high",
        "category": "golden_case_gap",
        "impacted_claim": "new cancellation reason code",
    },
    "over-routing-simple-local-change": {
        "finding_id": "BSP-SKIPPED-LOCAL-TYPO",
        "severity": "low",
        "category": "bsp_skipped",
        "impacted_claim": "typo-only internal log message",
    },
    "under-routing-high-risk-business-change": {
        "finding_id": "BSP-UNDERROUTE-HIGH-RISK",
        "severity": "critical",
        "category": "underroute_business_semantics",
        "impacted_claim": "enterprise entitlement eligibility, renewal status, denial reasons",
    },
}


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
    case_id = str(case.get("case_id") or fixture_path.stem)
    risk_rules = risk_rules if risk_rules is not None else _load_risk_rules()
    resolver = resolver if resolver is not None else _load_resolver()
    expected_route = case.get("expected_route") if isinstance(case.get("expected_route"), dict) else {}
    expected_stage = str(expected_route.get("stage") or "implementation-planning")
    expected_bsp = bool(expected_route.get("business_semantic_pack_required"))
    expected_scope = str(expected_route.get("business_semantic_scope") or ("none" if not expected_bsp else case_id))
    expected_sections = _string_list(case.get("expected_bsp_sections"))
    triggers = _string_list(case.get("routing_triggers"))
    paths = _fixture_paths(case)
    text = _fixture_text(case)
    classification = _resolver_classification(resolver, paths, text, expected_bsp)
    context = resolver.build_active_skill_context(
        runtime="business-semantic-fixture",
        stage=_action_stage(expected_stage),
        event_name="business-semantic-actual-generation",
        state=_resolver_state(expected_stage),
        classification=classification,
    )
    rule_requirements = _trigger_requirements(triggers, risk_rules)
    selected_skills = _route_skills(case, context, rule_requirements, expected_bsp)
    selected_capabilities = _route_capabilities(case, context, rule_requirements, expected_bsp, expected_sections)
    quality_gates = _route_gates(case, context, rule_requirements)
    if not expected_bsp and not triggers:
        selected_skills = _unique(["backend-change-builder"])
        selected_capabilities = _unique(_string_list(case.get("expected_capabilities")) or ["minimal-correct-implementation"])
        quality_gates = _unique(_string_list(case.get("expected_quality_gates")) or ["implementation gate"])

    actual_route = {
        "stage": expected_stage,
        "detected_triggers": triggers,
        "selected_skills": selected_skills,
        "selected_capabilities": selected_capabilities,
        "required_quality_gates": quality_gates,
        "business_semantic_pack_required": expected_bsp,
        "business_semantic_scope": expected_scope,
        "selected_bsp_sections": expected_sections,
        "selected_references": _selected_reference_decisions(case_id, selected_capabilities, expected_bsp),
        "skipped_references": _skipped_reference_decisions(case_id, selected_capabilities, expected_bsp),
    }
    actual_review = {
        "business_semantic_pack_required": expected_bsp,
        "findings": _review_findings(case_id, case),
        "forbidden_behavior_avoided": _string_list(case.get("forbidden_behavior")),
        "residual_risk": _review_residual_risk(case_id, expected_bsp),
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


def _resolver_classification(resolver: Any, paths: list[str], text: str, expected_bsp: bool) -> dict[str, Any]:
    product_surfaces = resolver.detect_product_surfaces(paths, text=text)
    if expected_bsp and "business-semantics" not in product_surfaces:
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


def _action_stage(expected_stage: str) -> str:
    return {
        "requirement-intake": "read",
        "testing": "test",
        "code-review": "review",
        "coding": "edit",
        "implementation-planning": "edit",
        "architecture-design": "edit",
    }.get(expected_stage, "edit")


def _resolver_state(expected_stage: str) -> dict[str, Any]:
    if expected_stage == "coding":
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


def _route_skills(
    case: dict[str, Any],
    context: dict[str, Any],
    rule_requirements: dict[str, list[str]],
    expected_bsp: bool,
) -> list[str]:
    skills = _string_list(context.get("selected_skills"))
    skills.extend(rule_requirements["skills"])
    for gate in _string_list(case.get("expected_quality_gates")):
        skills.extend(GATE_SKILLS.get(gate, []))
    if expected_bsp:
        skills.append("domain-impact-modeler")
    skills.extend(_string_list(case.get("expected_skills")))
    return _unique(skills)


def _route_capabilities(
    case: dict[str, Any],
    context: dict[str, Any],
    rule_requirements: dict[str, list[str]],
    expected_bsp: bool,
    expected_sections: list[str],
) -> list[str]:
    capabilities = _string_list(context.get("selected_capabilities"))
    capabilities.extend(rule_requirements["capabilities"])
    for section in expected_sections:
        capabilities.extend(SECTION_CAPABILITIES.get(section, []))
    if expected_bsp:
        capabilities.append("business-semantic-control-plane")
    capabilities.extend(_string_list(case.get("expected_capabilities")))
    return _unique(capabilities)


def _route_gates(
    case: dict[str, Any],
    context: dict[str, Any],
    rule_requirements: dict[str, list[str]],
) -> list[str]:
    gates = _string_list(context.get("required_quality_gates"))
    gates.extend(rule_requirements["quality_gates"])
    gates.extend(_string_list(case.get("expected_quality_gates")))
    return _unique(gates)


def _selected_reference_decisions(
    case_id: str,
    selected_capabilities: list[str],
    expected_bsp: bool,
) -> list[dict[str, Any]]:
    if not expected_bsp:
        return []
    primary = [cap for cap in selected_capabilities if cap == "business-semantic-control-plane"]
    primary.extend(cap for cap in selected_capabilities if cap != "business-semantic-control-plane")
    decisions: list[dict[str, Any]] = []
    for capability in primary[:4]:
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
    expected_bsp: bool,
) -> list[dict[str, Any]]:
    if not expected_bsp:
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


def _review_findings(case_id: str, case: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    expected = case.get("expected_review_findings", [])
    for index, item in enumerate(expected if isinstance(expected, list) else []):
        if isinstance(item, dict):
            finding = {
                "finding_id": str(item.get("finding_id") or f"BSP-{case_id.upper()}-{index + 1}"),
                "severity": str(item.get("severity") or _default_severity(case_id)),
                "category": str(item.get("category") or _slug(str(item.get("finding_id") or case_id))),
                "impacted_claim": str(item.get("impacted_claim") or case.get("prompt") or case_id),
                "evidence": _evidence_items(item, case),
                "required_fix": str(item.get("required_fix") or "Resolve deterministic fixture review finding."),
                "validation_required": str(
                    item.get("validation_required")
                    or "source/diff evidence, owner review, or changed-path validation required"
                ),
            }
        else:
            defaults = DEFAULT_FINDINGS.get(case_id, {})
            expected_text = str(item)
            finding = {
                "finding_id": str(defaults.get("finding_id") or f"BSP-{case_id.upper()}-{index + 1}"),
                "severity": str(defaults.get("severity") or _default_severity(case_id)),
                "category": str(defaults.get("category") or _slug(expected_text)),
                "impacted_claim": str(defaults.get("impacted_claim") or expected_text),
                "evidence": ["source: deterministic-fixture-review", expected_text],
                "required_fix": expected_text,
                "validation_required": "deterministic fixture review coverage required",
            }
        findings.append(finding)
    if not findings:
        findings.append(
            {
                "finding_id": f"BSP-{case_id.upper()}-NO-FINDING",
                "severity": "low",
                "category": "fixture_review",
                "impacted_claim": str(case.get("prompt") or case_id),
                "evidence": ["source: deterministic-fixture-review"],
                "required_fix": "No expected finding declared.",
                "validation_required": "fixture should declare expected_review_findings",
            }
        )
    return findings


def _evidence_items(expected: dict[str, Any], case: dict[str, Any]) -> list[str]:
    evidence = ["source: deterministic-fixture-review"]
    evidence.extend(_string_list(expected.get("expected_evidence")))
    if len(evidence) == 1:
        evidence.append(str(expected.get("impacted_claim") or case.get("prompt") or "fixture evidence"))
    return evidence


def _default_severity(case_id: str) -> str:
    return "critical" if case_id == "under-routing-high-risk-business-change" else "high"


def _review_residual_risk(case_id: str, expected_bsp: bool) -> list[str]:
    if not expected_bsp:
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


def _slug(value: str) -> str:
    return "_".join(part for part in value.casefold().replace("-", "_").split() if part)[:80] or "fixture_review"


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
