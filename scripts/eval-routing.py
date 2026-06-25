#!/usr/bin/env python3
"""Routing evaluation for ChangeForge golden cases.

Loads cases from ``evals/routing/*.yaml`` and validates that each case:

* is well-formed (schema, types, unique kebab-case id, valid complexity);
* references real professional skills, foundation capabilities, and domain
  extensions from ``src/registry/``;
* uses risk triggers and quality gates that are declared in
  ``src/registry/routing-rules.yaml``;
* keeps ``expected.*`` and ``forbidden.*`` disjoint;
* satisfies the risk-driven required route rules declared in
  ``routing-rules.yaml:risk_trigger_rules``;
* respects L1 anti-over-routing - heavy gates and design-time skills must
  not appear unless the case opts in through ``risk_triggers``.
* requires L2+ implementation cases that route to backend, frontend, or
  AI review implementation skills to include ``implementation-structure-design``
  unless the case explicitly sets ``expected.structure_required: false``.
* requires L2-L5 stage-aware cases to declare the expected canonical
  engineering stage from ``stage-model.yaml`` unless they explicitly opt out
  with a skip reason.

By default this remains an offline golden spec check. It does not invoke
any agent or model. When ``--candidate-output`` or ``--candidate-output-dir``
is provided, the script also compares captured router output YAML against
the matching golden case.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from validation_utils import (
    NAME_RE,
    ValidationProblem,
    fail_many,
    load_yaml_file,
    registry_items,
    relpath,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_DIR = ROOT / "src" / "registry"
EVALS_DIR = ROOT / "evals" / "routing"
OUTPUTS_DIR = ROOT / "evals" / "routing-outputs"
STAGE_MODEL_REGISTRY = REGISTRY_DIR / "stage-model.yaml"
ROUTING_RULES_REGISTRY = REGISTRY_DIR / "routing-rules.yaml"

VALID_COMPLEXITIES = {"L1", "L2", "L3", "L4", "L5"}
VALID_RISK_LEVELS = {"low", "medium", "high", "critical"}
VALID_CONTEXT_BUDGET_MODES = {"minimal", "single-stage", "staged-plan", "full"}
CONTEXT_BUDGET_REFERENCE_LIMITS = {
    "minimal": 4,
    "single-stage": 8,
    "staged-plan": 16,
    "full": 64,
}
MIN_ROUTING_CASES = 30
MIN_L1_ANTI_OVER_ROUTING_CASES = 8
MIN_DOMAIN_EXTENSION_CASES = 2
MIN_CANDIDATE_OUTPUTS = 24
MIN_CASES_PER_STAGE = 2
MIN_CONFLICT_CASES = 12
MIN_STAGE_ACTUAL_OUTPUTS = 24

ROUTER_SELF_REFERENCES: tuple[tuple[str, str], ...] = (
    ("change-forge-router", "references/routing-rules.md"),
    ("change-forge-router", "references/skill-registry.md"),
    ("change-forge-router", "references/capability-index.md"),
    ("change-forge-router", "references/domain-extension-index.md"),
)

L4_L5_GATE_SKILLS: dict[str, str] = {
    "security gate": "security-privacy-gate",
    "reliability gate": "reliability-observability-gate",
    "delivery gate": "delivery-release-gate",
    "documentation gate": "change-documentation-gate",
}

IMPLEMENTATION_GATE = "implementation gate"
STRUCTURE_CAPABILITY = "implementation-structure-design"
IMPLEMENTATION_SKILLS_REQUIRE_STRUCTURE: tuple[str, ...] = (
    "backend-change-builder",
    "frontend-change-builder",
    "ai-code-review-refactor",
)

RiskRule = dict[str, tuple[str, ...]]

# Skills and extensions that are explicitly forbidden at L1 unless the case
# opts in by declaring a risk trigger that requires them.
L1_OVER_ROUTING_SKILLS: tuple[str, ...] = (
    "change-intake-compiler",
    "change-impact-analyzer",
    "task-dag-planner",
    "domain-impact-modeler",
    "architecture-impact-reviewer",
    "data-api-contract-changer",
    "data-middleware-change-builder",
    "integration-change-builder",
    "security-privacy-gate",
    "reliability-observability-gate",
    "delivery-release-gate",
)

L1_OVER_ROUTING_CAPABILITIES: tuple[str, ...] = (
    "agent-execution-discipline",
    "implementation-structure-design",
    "failure-diagnosis",
    "solution-optimality-evaluation",
)

EXPECTED_FIELDS: tuple[str, ...] = (
    "skills",
    "capabilities",
    "domain_extensions",
    "quality_gates",
)

ACTUAL_LIST_ALIASES: dict[str, tuple[str, ...]] = {
    "skills": ("skills", "skill_path", "professional_skills", "selected_skills"),
    "capabilities": (
        "capabilities",
        "foundation_capabilities",
        "capability_path",
        "selected_capabilities",
    ),
    "domain_extensions": (
        "domain_extensions",
        "extensions",
        "selected_domain_extensions",
    ),
    "quality_gates": ("quality_gates", "gates", "required_quality_gates"),
}


def _load_registry_names() -> tuple[set[str], set[str], set[str]]:
    """Return (skill_names, capability_names, extension_names) from registries."""

    def _names(path: Path, key: str, ref_keys: tuple[str, ...]) -> set[str]:
        if not path.is_file():
            return set()
        try:
            data = load_yaml_file(path)
        except ValidationProblem:
            return set()
        names: set[str] = set()
        for entry in registry_items(data, key, path, []):
            if not isinstance(entry, dict):
                continue
            for ref_key in ref_keys:
                value = entry.get(ref_key)
                if isinstance(value, str) and value:
                    names.add(value)
                    break
        return names

    skills = _names(
        REGISTRY_DIR / "skills.yaml",
        "skills",
        ("name", "skill", "id"),
    )
    capabilities = _names(
        REGISTRY_DIR / "capabilities.yaml",
        "capabilities",
        ("name", "changeforge_capability_id", "id"),
    )
    extensions = _names(
        REGISTRY_DIR / "domain-extensions.yaml",
        "domain_extensions",
        ("name", "domain_extension", "id"),
    )
    return skills, capabilities, extensions


def _load_capability_metadata() -> dict[str, dict[str, Any]]:
    """Return capability name -> {id, used_by} from capabilities.yaml."""

    path = REGISTRY_DIR / "capabilities.yaml"
    if not path.is_file():
        return {}
    try:
        data = load_yaml_file(path)
    except ValidationProblem:
        return {}
    metadata: dict[str, dict[str, Any]] = {}
    for entry in registry_items(data, "capabilities", path, []):
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        capability_id = entry.get("id")
        used_by = entry.get("used_by")
        if not isinstance(name, str) or not isinstance(capability_id, str):
            continue
        if not isinstance(used_by, list):
            used_by = []
        metadata[name] = {
            "id": capability_id.strip(),
            "route_level_capability": entry.get("route_level_capability") is True,
            "used_by": {
                item.strip()
                for item in used_by
                if isinstance(item, str) and item.strip()
            },
        }
    return metadata


def _capability_reference_path(
    capability: str,
    capability_metadata: dict[str, dict[str, Any]],
) -> str | None:
    entry = capability_metadata.get(capability)
    if not entry:
        return None
    capability_id = entry.get("id")
    if not isinstance(capability_id, str) or not capability_id:
        return None
    return f"references/capabilities/{capability_id}-{capability}.md"


def _string_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        return ()
    out: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
    return tuple(out)


def _load_stage_model() -> dict[str, Any]:
    if not STAGE_MODEL_REGISTRY.is_file():
        return {}
    try:
        data = load_yaml_file(STAGE_MODEL_REGISTRY)
    except ValidationProblem:
        return {}
    return data if isinstance(data, dict) else {}


def _stage_model_stages(stage_model: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    model = stage_model if stage_model is not None else _load_stage_model()
    stages: dict[str, dict[str, Any]] = {}
    for entry in model.get("stages", []) or []:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        if isinstance(name, str) and name.strip():
            stages[name.strip()] = entry
    return stages


def _stage_model_surfaces(stage_model: dict[str, Any]) -> dict[str, dict[str, Any]]:
    surfaces: dict[str, dict[str, Any]] = {}
    for entry in stage_model.get("product_surfaces", []) or []:
        if not isinstance(entry, dict):
            continue
        surface = entry.get("surface")
        if isinstance(surface, str) and surface.strip():
            surfaces[surface.strip()] = entry
    return surfaces


def _stage_model_languages(stage_model: dict[str, Any]) -> dict[str, dict[str, Any]]:
    languages: dict[str, dict[str, Any]] = {}
    for entry in stage_model.get("language_surfaces", []) or []:
        if not isinstance(entry, dict):
            continue
        language = entry.get("language")
        if isinstance(language, str) and language.strip():
            languages[language.strip()] = entry
    return languages


def _stage_model_transitions(stage_model: dict[str, Any]) -> dict[str, set[str]]:
    transitions: dict[str, set[str]] = {}
    for entry in stage_model.get("stage_transitions", []) or []:
        if not isinstance(entry, dict):
            continue
        source = entry.get("from")
        targets = entry.get("to")
        if not isinstance(source, str) or not isinstance(targets, list):
            continue
        transitions[source.strip()] = {
            target.strip()
            for target in targets
            if isinstance(target, str) and target.strip()
        }
    return transitions


def _load_risk_trigger_rules() -> dict[str, RiskRule]:
    if not ROUTING_RULES_REGISTRY.is_file():
        return {}
    try:
        data = load_yaml_file(ROUTING_RULES_REGISTRY)
    except ValidationProblem:
        return {}
    if not isinstance(data, dict):
        return {}
    rules: dict[str, RiskRule] = {}
    for entry in data.get("risk_trigger_rules", []) or []:
        if not isinstance(entry, dict):
            continue
        trigger = entry.get("trigger")
        if not isinstance(trigger, str) or not trigger.strip():
            continue
        rules[trigger.strip().casefold()] = {
            "skills": _string_tuple(entry.get("required_skills")),
            "capabilities": _string_tuple(entry.get("required_capabilities")),
            "domain_extensions": _string_tuple(entry.get("required_domain_extensions")),
            "quality_gates": _string_tuple(entry.get("required_quality_gates")),
        }
    return rules


def _load_routing_allow_lists() -> tuple[set[str], set[str], set[str]]:
    """Return (risk_triggers, quality_gates, stages) from registry YAML."""

    path = ROUTING_RULES_REGISTRY
    if not path.is_file():
        return set(), set(), set()
    try:
        data = load_yaml_file(path)
    except ValidationProblem:
        return set(), set(), set()
    if not isinstance(data, dict):
        return set(), set(), set()
    triggers = {
        str(item).strip().casefold()
        for item in data.get("risk_escalation_triggers", []) or []
        if isinstance(item, (str, int))
    }
    gates = {
        str(item).strip().casefold()
        for item in data.get("quality_gates", []) or []
        if isinstance(item, (str, int))
    }
    stages = set(_stage_model_stages().keys())
    if not stages:
        for entry in data.get("engineering_stage_signals", []) or []:
            if not isinstance(entry, dict):
                continue
            stage = entry.get("stage")
            if isinstance(stage, str) and stage.strip():
                stages.add(stage.strip())
    return triggers, gates, stages


def _as_string_list(value: Any) -> list[str] | None:
    if value is None:
        return []
    if not isinstance(value, list):
        return None
    out: list[str] = []
    for item in value:
        if not isinstance(item, str):
            return None
        out.append(item.strip())
    return out


def context_budget_for_route(
    *,
    mode: str,
    selected_skills: Iterable[str],
    selected_capabilities: Iterable[str],
    required_references: Iterable[str],
    skipped_references: Iterable[Any] = (),
    rationale: str = "",
) -> dict[str, Any]:
    """Return deterministic context budget metrics for a route selection.

    The token value is a proxy, not tokenizer output. It uses path text length
    and fixed route item weights so offline routing fixtures stay reproducible.
    """
    if mode not in VALID_CONTEXT_BUDGET_MODES:
        raise ValueError(f"unknown context budget mode: {mode}")
    skill_count = len(_unique_strings(selected_skills))
    capability_count = len(_unique_strings(selected_capabilities))
    reference_paths = _unique_strings(required_references)
    skipped_count = len(list(skipped_references or ()))
    estimated = (
        sum(max(1, len(reference)) // 4 for reference in reference_paths)
        + skill_count * 120
        + capability_count * 80
    )
    selected_reference_count = len(reference_paths)
    return {
        "mode": mode,
        "selected_skill_count": skill_count,
        "selected_capability_count": capability_count,
        "selected_reference_count": selected_reference_count,
        "skipped_reference_count": skipped_count,
        "estimated_token_cost": estimated,
        "estimate_method": "deterministic_proxy:path_chars_div_4_plus_fixed_skill_capability_weights",
        "over_budget": selected_reference_count > CONTEXT_BUDGET_REFERENCE_LIMITS[mode],
        "rationale": str(rationale or "").strip(),
    }


def _unique_strings(values: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values or ():
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _as_expected_surface_list(value: Any) -> list[str] | None:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else None
    return _as_string_list(value)


def _validate_case(  # noqa: C901 - branchy validator by design
    path: Path,
    data: Any,
    seen_ids: set[str],
    skills: set[str],
    capabilities: set[str],
    extensions: set[str],
    allowed_triggers: set[str],
    allowed_gates: set[str],
    allowed_stages: set[str],
    errors: list[str],
    risk_rules: dict[str, RiskRule] | None = None,
) -> None:
    rel = relpath(ROOT, path)
    if not isinstance(data, dict):
        errors.append(f"{rel}: top-level must be a mapping")
        return

    case_id = data.get("id")
    if not isinstance(case_id, str) or not NAME_RE.fullmatch(case_id):
        errors.append(f"{rel}: 'id' must be lowercase kebab-case")
    else:
        if case_id in seen_ids:
            errors.append(f"{rel}: duplicate case id '{case_id}'")
        seen_ids.add(case_id)

    for key in ("description", "prompt"):
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{rel}: '{key}' must be a non-empty string")

    expected = data.get("expected")
    if not isinstance(expected, dict):
        errors.append(f"{rel}: 'expected' must be a mapping")
        return

    complexity = expected.get("complexity")
    if complexity not in VALID_COMPLEXITIES:
        errors.append(
            f"{rel}: expected.complexity must be one of {sorted(VALID_COMPLEXITIES)}"
        )
        complexity = None

    risk_level = expected.get("risk_level")
    if risk_level is not None:
        if (
            not isinstance(risk_level, str)
            or risk_level.casefold() not in VALID_RISK_LEVELS
        ):
            errors.append(
                f"{rel}: expected.risk_level must be one of "
                f"{sorted(VALID_RISK_LEVELS)} when present"
            )

    structure_required = expected.get("structure_required")
    if structure_required is not None and not isinstance(structure_required, bool):
        errors.append(f"{rel}: expected.structure_required must be a boolean")

    stage_route_required = expected.get("stage_route_required")
    if stage_route_required is not None and not isinstance(stage_route_required, bool):
        errors.append(f"{rel}: expected.stage_route_required must be a boolean")
    if stage_route_required is False:
        reason = expected.get("stage_route_skip_reason")
        if not isinstance(reason, str) or not reason.strip():
            errors.append(
                f"{rel}: expected.stage_route_skip_reason is required when "
                "expected.stage_route_required is false"
            )

    expected_stage = expected.get("expected_stage")
    stage_required = (
        complexity in {"L2", "L3", "L4", "L5"} and stage_route_required is not False
    )
    if stage_required and expected_stage is None:
        errors.append(
            f"{rel}: expected.expected_stage is required for {complexity} cases "
            "unless expected.stage_route_required is false"
        )
    if expected_stage is not None:
        if not isinstance(expected_stage, str) or not expected_stage.strip():
            errors.append(f"{rel}: expected.expected_stage must be a non-empty string")
        elif expected_stage.strip() not in allowed_stages:
            errors.append(
                f"{rel}: expected.expected_stage must be one of "
                f"{sorted(allowed_stages)}, found '{expected_stage.strip()}'"
            )

    stage_model = _load_stage_model()
    allowed_product_surfaces = set(_stage_model_surfaces(stage_model)) | {"none"}
    expected_product_surfaces = _as_expected_surface_list(
        expected.get("expected_product_surface")
    )
    if expected_product_surfaces is None:
        errors.append(
            f"{rel}: expected.expected_product_surface must be a string or list of strings"
        )
        expected_product_surfaces = []
    for surface in expected_product_surfaces:
        if surface not in allowed_product_surfaces:
            errors.append(
                f"{rel}: expected.expected_product_surface must be one of "
                f"{sorted(allowed_product_surfaces)}, found '{surface}'"
            )

    allowed_language_surfaces = set(_stage_model_languages(stage_model)) | {"none"}
    expected_language_surfaces = _as_expected_surface_list(
        expected.get("expected_language_surface")
    )
    if expected_language_surfaces is None:
        errors.append(
            f"{rel}: expected.expected_language_surface must be a string or list of strings"
        )
        expected_language_surfaces = []
    for language in expected_language_surfaces:
        if language not in allowed_language_surfaces:
            errors.append(
                f"{rel}: expected.expected_language_surface must be one of "
                f"{sorted(allowed_language_surfaces)}, found '{language}'"
            )

    expected_budget = expected.get("expected_context_budget_mode")
    if expected_budget is not None:
        if (
            not isinstance(expected_budget, str)
            or expected_budget not in VALID_CONTEXT_BUDGET_MODES
        ):
            errors.append(
                f"{rel}: expected.expected_context_budget_mode must be one of "
                f"{sorted(VALID_CONTEXT_BUDGET_MODES)}"
            )

    expected_refs = _as_string_list(expected.get("expected_required_references"))
    if expected_refs is None:
        errors.append(
            f"{rel}: expected.expected_required_references must be a list of strings"
        )

    risk_triggers = _as_string_list(expected.get("risk_triggers"))
    if risk_triggers is None:
        errors.append(f"{rel}: expected.risk_triggers must be a list of strings")
        risk_triggers = []

    normalized_triggers = [trigger.casefold() for trigger in risk_triggers]
    for trigger in risk_triggers:
        if trigger.casefold() not in allowed_triggers:
            errors.append(
                f"{rel}: expected.risk_triggers contains unknown trigger '{trigger}'"
            )

    expected_sets: dict[str, list[str]] = {}
    for field in EXPECTED_FIELDS:
        values = _as_string_list(expected.get(field))
        if values is None:
            errors.append(f"{rel}: expected.{field} must be a list of strings")
            values = []
        expected_sets[field] = values

    forbidden = data.get("forbidden", {})
    if forbidden is None:
        forbidden = {}
    if not isinstance(forbidden, dict):
        errors.append(f"{rel}: 'forbidden' must be a mapping or omitted")
        forbidden = {}

    forbidden_sets: dict[str, list[str]] = {}
    for field in EXPECTED_FIELDS:
        values = _as_string_list(forbidden.get(field))
        if values is None:
            errors.append(f"{rel}: forbidden.{field} must be a list of strings")
            values = []
        forbidden_sets[field] = values

    _validate_membership(
        rel, "expected.skills", expected_sets["skills"], skills, errors
    )
    _validate_membership(
        rel,
        "expected.capabilities",
        expected_sets["capabilities"],
        capabilities,
        errors,
    )
    _validate_membership(
        rel,
        "expected.domain_extensions",
        expected_sets["domain_extensions"],
        extensions,
        errors,
    )
    _validate_membership(
        rel, "forbidden.skills", forbidden_sets["skills"], skills, errors
    )
    _validate_membership(
        rel,
        "forbidden.capabilities",
        forbidden_sets["capabilities"],
        capabilities,
        errors,
    )
    _validate_membership(
        rel,
        "forbidden.domain_extensions",
        forbidden_sets["domain_extensions"],
        extensions,
        errors,
    )

    for gate in expected_sets["quality_gates"]:
        if gate.casefold() not in allowed_gates:
            errors.append(
                f"{rel}: expected.quality_gates contains unknown gate '{gate}'"
            )
    for gate in forbidden_sets["quality_gates"]:
        if gate.casefold() not in allowed_gates:
            errors.append(
                f"{rel}: forbidden.quality_gates contains unknown gate '{gate}'"
            )

    for field in EXPECTED_FIELDS:
        overlap = set(expected_sets[field]) & set(forbidden_sets[field])
        if overlap:
            errors.append(
                f"{rel}: expected.{field} and forbidden.{field} overlap on "
                f"{sorted(overlap)}"
            )

    _check_unique(rel, expected_sets, "expected", errors)
    _check_unique(rel, forbidden_sets, "forbidden", errors)

    _enforce_risk_required(
        rel,
        normalized_triggers,
        expected_sets,
        forbidden_sets,
        errors,
        risk_rules or _load_risk_trigger_rules(),
    )

    _enforce_l1_anti_over_routing(
        rel,
        complexity,
        normalized_triggers,
        expected_sets,
        errors,
        risk_rules or _load_risk_trigger_rules(),
    )

    _enforce_evidence_gates(rel, complexity, expected_sets, errors)

    _enforce_implementation_structure_required(
        rel,
        complexity,
        structure_required,
        expected_sets,
        forbidden_sets,
        errors,
    )


def _validate_membership(
    rel: str,
    field: str,
    values: Iterable[str],
    allowed: set[str],
    errors: list[str],
) -> None:
    for value in values:
        if value not in allowed:
            errors.append(f"{rel}: {field} contains unknown name '{value}'")


def _check_unique(
    rel: str,
    sets: dict[str, list[str]],
    prefix: str,
    errors: list[str],
) -> None:
    for field, values in sets.items():
        seen: set[str] = set()
        for value in values:
            if value in seen:
                errors.append(f"{rel}: {prefix}.{field} has duplicate '{value}'")
            seen.add(value)


def _enforce_risk_required(
    rel: str,
    normalized_triggers: list[str],
    expected_sets: dict[str, list[str]],
    forbidden_sets: dict[str, list[str]],
    errors: list[str],
    risk_rules: dict[str, RiskRule],
) -> None:
    expected_skills = set(expected_sets["skills"])
    expected_capabilities = set(expected_sets["capabilities"])
    expected_extensions = set(expected_sets["domain_extensions"])
    expected_gates = {gate.casefold() for gate in expected_sets["quality_gates"]}
    forbidden_skills = set(forbidden_sets["skills"])
    forbidden_capabilities = set(forbidden_sets["capabilities"])
    forbidden_extensions = set(forbidden_sets["domain_extensions"])
    forbidden_gates = {gate.casefold() for gate in forbidden_sets["quality_gates"]}

    for trigger in normalized_triggers:
        rule = risk_rules.get(trigger, {})
        required_skills = rule.get("skills", ())
        for skill in required_skills:
            if skill not in expected_skills:
                errors.append(
                    f"{rel}: risk_trigger '{trigger}' requires "
                    f"expected.skills to include '{skill}'"
                )
            if skill in forbidden_skills:
                errors.append(
                    f"{rel}: risk_trigger '{trigger}' requires '{skill}' "
                    f"but it is listed in forbidden.skills"
                )
        required_capabilities = rule.get("capabilities", ())
        for capability in required_capabilities:
            if capability not in expected_capabilities:
                errors.append(
                    f"{rel}: risk_trigger '{trigger}' requires "
                    f"expected.capabilities to include '{capability}'"
                )
            if capability in forbidden_capabilities:
                errors.append(
                    f"{rel}: risk_trigger '{trigger}' requires '{capability}' "
                    f"but it is listed in forbidden.capabilities"
                )
        required_gates = rule.get("quality_gates", ())
        for gate in required_gates:
            gate_key = gate.casefold()
            if gate_key not in expected_gates:
                errors.append(
                    f"{rel}: risk_trigger '{trigger}' requires "
                    f"expected.quality_gates to include '{gate}'"
                )
            if gate_key in forbidden_gates:
                errors.append(
                    f"{rel}: risk_trigger '{trigger}' requires '{gate}' "
                    f"but it is listed in forbidden.quality_gates"
                )
        for required_extension in rule.get("domain_extensions", ()):
            if required_extension not in expected_extensions:
                errors.append(
                    f"{rel}: risk_trigger '{trigger}' requires "
                    f"expected.domain_extensions to include "
                    f"'{required_extension}'"
                )
            if required_extension in forbidden_extensions:
                errors.append(
                    f"{rel}: risk_trigger '{trigger}' requires "
                    f"'{required_extension}' but it is listed in "
                    f"forbidden.domain_extensions"
                )


def _enforce_l1_anti_over_routing(
    rel: str,
    complexity: str | None,
    normalized_triggers: list[str],
    expected_sets: dict[str, list[str]],
    errors: list[str],
    risk_rules: dict[str, RiskRule],
) -> None:
    if complexity != "L1":
        return

    opt_in_skills: set[str] = set()
    opt_in_capabilities: set[str] = set()
    for trigger in normalized_triggers:
        rule = risk_rules.get(trigger, {})
        opt_in_skills.update(rule.get("skills", ()))
        opt_in_capabilities.update(rule.get("capabilities", ()))

    expected_skills = set(expected_sets["skills"])
    over_routed = (
        expected_skills.intersection(L1_OVER_ROUTING_SKILLS) - opt_in_skills
    )
    if over_routed:
        errors.append(
            f"{rel}: L1 case over-routes to {sorted(over_routed)} without a "
            f"matching risk_trigger"
        )

    expected_capabilities = set(expected_sets["capabilities"])
    over_routed_capabilities = (
        expected_capabilities.intersection(L1_OVER_ROUTING_CAPABILITIES)
        - opt_in_capabilities
    )
    if over_routed_capabilities:
        errors.append(
            f"{rel}: L1 case over-routes to capabilities "
            f"{sorted(over_routed_capabilities)} without a matching risk_trigger"
        )

    if expected_sets["domain_extensions"]:
        errors.append(
            f"{rel}: L1 case must not include domain_extensions "
            f"({expected_sets['domain_extensions']})"
        )


def _enforce_evidence_gates(
    rel: str,
    complexity: str | None,
    expected_sets: dict[str, list[str]],
    errors: list[str],
) -> None:
    if complexity in (None, "L1"):
        return
    gates_lower = {gate.casefold() for gate in expected_sets["quality_gates"]}
    evidence_options = {
        "requirement gate",
        "architecture gate",
        "api/data gate",
        "implementation gate",
        "test gate",
        "documentation gate",
    }
    if not gates_lower & evidence_options:
        errors.append(
            f"{rel}: {complexity} case must list at least one of "
            f"{sorted(evidence_options)} in expected.quality_gates"
        )


def _enforce_implementation_structure_required(
    rel: str,
    complexity: str | None,
    structure_required: bool | None,
    expected_sets: dict[str, list[str]],
    forbidden_sets: dict[str, list[str]],
    errors: list[str],
) -> None:
    if structure_required is False:
        return

    expected_skills = set(expected_sets["skills"])
    gates_lower = {gate.casefold() for gate in expected_sets["quality_gates"]}
    matching_skills = sorted(
        expected_skills.intersection(IMPLEMENTATION_SKILLS_REQUIRE_STRUCTURE)
    )
    default_required = (
        complexity != "L1"
        and bool(matching_skills)
        and IMPLEMENTATION_GATE in gates_lower
    )
    if not (structure_required is True or default_required):
        return

    if STRUCTURE_CAPABILITY not in expected_sets["capabilities"]:
        errors.append(
            f"{rel}: expected.capabilities must include "
            f"'{STRUCTURE_CAPABILITY}' when expected.skills includes "
            f"{matching_skills or sorted(IMPLEMENTATION_SKILLS_REQUIRE_STRUCTURE)} "
            f"with '{IMPLEMENTATION_GATE}'"
        )
    if STRUCTURE_CAPABILITY in forbidden_sets["capabilities"]:
        errors.append(
            f"{rel}: forbidden.capabilities must not include "
            f"'{STRUCTURE_CAPABILITY}' when structure is required"
        )


def _case_expected(data: dict[str, Any]) -> dict[str, Any]:
    expected = data.get("expected")
    return expected if isinstance(expected, dict) else {}


def _case_expected_list(data: dict[str, Any], field: str) -> list[str]:
    values = _as_string_list(_case_expected(data).get(field))
    return values if values is not None else []


def _case_expected_required_references(
    data: dict[str, Any],
    capability_metadata: dict[str, dict[str, Any]],
) -> list[str]:
    expected = _case_expected(data)
    explicit = _as_string_list(expected.get("expected_required_references"))
    references = set(explicit if explicit is not None else [])
    for capability in _case_expected_list(data, "capabilities"):
        reference = _capability_reference_path(capability, capability_metadata)
        if reference is not None:
            references.add(reference)
    return sorted(references)


def _case_forbidden_list(data: dict[str, Any], field: str) -> list[str]:
    forbidden = data.get("forbidden")
    if not isinstance(forbidden, dict):
        return []
    values = _as_string_list(forbidden.get(field))
    return values if values is not None else []


def _is_l1_anti_over_routing_case(data: dict[str, Any]) -> bool:
    expected = _case_expected(data)
    if expected.get("complexity") != "L1":
        return False
    forbidden_skills = set(_case_forbidden_list(data, "skills"))
    forbidden_capabilities = set(_case_forbidden_list(data, "capabilities"))
    forbidden_gates = {
        gate.casefold()
        for gate in _case_forbidden_list(data, "quality_gates")
    }
    return bool(
        forbidden_skills.intersection(L1_OVER_ROUTING_SKILLS)
        or forbidden_capabilities.intersection(L1_OVER_ROUTING_CAPABILITIES)
        or forbidden_gates.intersection(
            {
                "architecture gate",
                "api/data gate",
                "security gate",
                "reliability gate",
                "delivery gate",
                "ai review gate",
            }
        )
        or _case_forbidden_list(data, "domain_extensions")
    )


def _is_negative_over_stage_case(data: dict[str, Any]) -> bool:
    if not _case_expected(data).get("expected_stage"):
        return False
    return any(_case_forbidden_list(data, field) for field in EXPECTED_FIELDS)


def _is_stage_conflict_case(data: dict[str, Any]) -> bool:
    expected = _case_expected(data)
    return expected.get("stage_conflict_case") is True


def _actual_output_stage_counts(output_dir: Path, errors: list[str]) -> Counter[str]:
    counts: Counter[str] = Counter()
    if not output_dir.exists():
        errors.append(f"{_display_path(output_dir)}: stage actual output directory not found")
        return counts
    for output_path in _iter_output_files(output_dir):
        try:
            data = load_yaml_file(output_path)
        except ValidationProblem as exc:
            errors.append(str(exc))
            continue
        if not isinstance(data, dict):
            errors.append(f"{_display_path(output_path)}: top-level must be a mapping")
            continue
        actual = _extract_actual_payload(data)
        if actual is None:
            errors.append(f"{_display_path(output_path)}: actual router output must be a mapping")
            continue
        manifest = _actual_stage_manifest(data, actual)
        if manifest is None:
            continue
        current = manifest.get("current_stage")
        if isinstance(current, str) and current.strip():
            counts[current.strip()] += 1
    return counts


def _enforce_collection_requirements(
    cases: dict[str, tuple[Path, dict[str, Any]]],
    extensions: set[str],
    allowed_stages: set[str],
    errors: list[str],
) -> None:
    if len(cases) < MIN_ROUTING_CASES:
        errors.append(
            f"evals/routing: expected at least {MIN_ROUTING_CASES} golden cases, "
            f"found {len(cases)}"
        )

    l1_anti_cases = [
        case_id
        for case_id, (_, data) in cases.items()
        if _is_l1_anti_over_routing_case(data)
    ]
    if len(l1_anti_cases) < MIN_L1_ANTI_OVER_ROUTING_CASES:
        errors.append(
            "evals/routing: expected at least "
            f"{MIN_L1_ANTI_OVER_ROUTING_CASES} L1 anti-over-routing cases, "
            f"found {len(l1_anti_cases)}"
        )

    for extension in sorted(extensions):
        count = sum(
            1
            for _, data in cases.values()
            if extension in _case_expected_list(data, "domain_extensions")
        )
        if count < MIN_DOMAIN_EXTENSION_CASES:
            errors.append(
                f"evals/routing: domain extension '{extension}' must appear in "
                f"at least {MIN_DOMAIN_EXTENSION_CASES} golden cases; found {count}"
            )

    for stage in sorted(allowed_stages):
        stage_cases = [
            case_id
            for case_id, (_, data) in cases.items()
            if _case_expected(data).get("expected_stage") == stage
        ]
        if len(stage_cases) < MIN_CASES_PER_STAGE:
            errors.append(
                f"evals/routing: stage '{stage}' must appear in at least "
                f"{MIN_CASES_PER_STAGE} golden cases; found {len(stage_cases)}"
            )
        negative_cases = [
            case_id
            for case_id, (_, data) in cases.items()
            if _case_expected(data).get("expected_stage") == stage
            and _is_negative_over_stage_case(data)
        ]
        if not negative_cases:
            errors.append(
                f"evals/routing: stage '{stage}' must have at least one "
                "negative over-stage case with forbidden coverage"
            )

    conflict_cases = [
        case_id for case_id, (_, data) in cases.items() if _is_stage_conflict_case(data)
    ]
    if len(conflict_cases) < MIN_CONFLICT_CASES:
        errors.append(
            f"evals/routing: expected at least {MIN_CONFLICT_CASES} stage "
            f"conflict-resolution cases; found {len(conflict_cases)}"
        )

    output_counts = _actual_output_stage_counts(OUTPUTS_DIR, errors)
    total_outputs = sum(output_counts.values())
    if total_outputs < MIN_STAGE_ACTUAL_OUTPUTS:
        errors.append(
            f"{_display_path(OUTPUTS_DIR)}: expected at least "
            f"{MIN_STAGE_ACTUAL_OUTPUTS} stage actual output fixture(s), found "
            f"{total_outputs}"
        )
    for stage in sorted(allowed_stages):
        if output_counts.get(stage, 0) < 1:
            errors.append(
                f"{_display_path(OUTPUTS_DIR)}: stage '{stage}' must have at "
                "least one actual output fixture"
            )


def _lookup_actual_value(actual: dict[str, Any], field: str) -> Any:
    for key in ACTUAL_LIST_ALIASES[field]:
        if key in actual:
            return actual.get(key)
    return None


def _extract_string_items(value: Any, item_key: str | None = None) -> list[str] | None:
    if value is None:
        return []
    if isinstance(value, dict):
        out = []
        for key, item in value.items():
            if isinstance(item, str) and item.strip().casefold().startswith("skipped"):
                continue
            out.append(str(key).strip())
        return out
    if not isinstance(value, list):
        return None
    out: list[str] = []
    for item in value:
        if isinstance(item, str):
            out.append(item.strip())
            continue
        if isinstance(item, dict) and item_key is not None:
            raw = item.get(item_key)
            if isinstance(raw, str):
                out.append(raw.strip())
                continue
        return None
    return out


def _actual_string_list(
    actual: dict[str, Any],
    field: str,
    item_key: str | None = None,
) -> list[str] | None:
    return _extract_string_items(_lookup_actual_value(actual, field), item_key)


def _extract_actual_payload(data: Any) -> dict[str, Any] | None:
    if not isinstance(data, dict):
        return None
    actual = data.get("actual")
    if isinstance(actual, dict):
        return actual
    return data


def _actual_case_id(data: dict[str, Any], path: Path) -> str | None:
    raw = data.get("case_id") or data.get("id")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    stem = path.stem
    if stem.endswith(".actual"):
        stem = stem[: -len(".actual")]
    return stem if NAME_RE.fullmatch(stem) else None


def _actual_risk_level(actual: dict[str, Any]) -> str | None:
    raw = actual.get("risk_level")
    if raw is None:
        raw = actual.get("risk")
    if isinstance(raw, dict):
        raw = raw.get("level")
    if isinstance(raw, str) and raw.strip():
        return raw.strip().casefold()
    return None


def _reference_pairs(value: Any) -> set[tuple[str, str]] | None:
    if value is None:
        return set()
    if not isinstance(value, list):
        return None

    pairs: set[tuple[str, str]] = set()
    for item in value:
        if isinstance(item, dict):
            skill = item.get("skill")
            reference = item.get("reference") or item.get("path") or item.get("ref")
            if not isinstance(skill, str) or not isinstance(reference, str):
                return None
            pairs.add((skill.strip(), reference.strip()))
            continue
        if isinstance(item, str):
            raw = item.strip()
            if ":" in raw:
                skill, reference = raw.split(":", 1)
            elif "|" in raw:
                skill, reference = raw.split("|", 1)
            elif raw:
                skill, reference = "", raw
            else:
                return None
            pairs.add((skill.strip(), reference.strip()))
            continue
        return None
    return pairs


def _actual_reference_pairs(actual: dict[str, Any]) -> set[tuple[str, str]] | None:
    value = (
        actual.get("required_references")
        or actual.get("requiredReferences")
        or actual.get("references")
    )
    return _reference_pairs(value)


def _actual_stage_manifest(output_data: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any] | None:
    for container in (actual, output_data):
        for key in ("stage_route_manifest", "stage_manifest", "changeforge_stage_route"):
            value = container.get(key)
            if isinstance(value, dict):
                return value
    return None


def _expected_context_budget_mode(expected: dict[str, Any]) -> str | None:
    explicit = expected.get("expected_context_budget_mode")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    complexity = expected.get("complexity")
    if complexity == "L1":
        return "minimal"
    if complexity == "L2":
        return "single-stage"
    if complexity in {"L3", "L4", "L5"}:
        return "staged-plan"
    return None


def _stage_route_required(expected: dict[str, Any]) -> bool:
    explicit = expected.get("stage_route_required")
    if isinstance(explicit, bool):
        return explicit
    return expected.get("complexity") in {"L2", "L3", "L4", "L5"}


def _stage_skipped_without_reason(manifest: dict[str, Any]) -> list[str]:
    entries = manifest.get("skipped_capabilities")
    if not isinstance(entries, list):
        return []
    missing: list[str] = []
    for entry in entries:
        if isinstance(entry, dict):
            capability = str(entry.get("capability", "")).strip()
            reason = str(entry.get("reason", "")).strip()
            if capability and not reason:
                missing.append(capability)
        elif isinstance(entry, str):
            if "=>" in entry:
                capability, _sep, reason = entry.partition("=>")
                if capability.strip() and not reason.strip():
                    missing.append(capability.strip())
            elif entry.strip():
                missing.append(entry.strip())
    return missing


def _stage_skipped_unknown_capabilities(
    manifest: dict[str, Any],
    capabilities: set[str],
) -> list[str]:
    entries = manifest.get("skipped_capabilities")
    if not isinstance(entries, list):
        return []
    unknown: list[str] = []
    for entry in entries:
        capability = ""
        if isinstance(entry, dict):
            capability = str(entry.get("capability", "")).strip()
        elif isinstance(entry, str):
            raw = entry.strip()
            capability = raw.partition("=>")[0].strip() if "=>" in raw else raw
        if capability and capability not in capabilities:
            unknown.append(capability)
    return unknown


def _reference_paths(references: set[tuple[str, str]]) -> set[str]:
    return {reference for _skill, reference in references}


def _missing_router_self_references(
    references: set[tuple[str, str]],
) -> list[tuple[str, str]]:
    paths = _reference_paths(references)
    missing: list[tuple[str, str]] = []
    for skill, reference in ROUTER_SELF_REFERENCES:
        if (skill, reference) not in references and reference not in paths:
            missing.append((skill, reference))
    return missing


def _compare_required_subset(
    rel: str,
    field: str,
    expected_values: Iterable[str],
    actual_values: Iterable[str],
    errors: list[str],
) -> None:
    missing = sorted(set(expected_values) - set(actual_values))
    if missing:
        errors.append(f"{rel}: actual.{field} is missing expected {missing}")


def _compare_forbidden_absent(
    rel: str,
    field: str,
    forbidden_values: Iterable[str],
    actual_values: Iterable[str],
    errors: list[str],
) -> None:
    present = sorted(set(forbidden_values) & set(actual_values))
    if present:
        errors.append(f"{rel}: actual.{field} contains forbidden {present}")


def _validate_actual_membership(
    rel: str,
    actual_sets: dict[str, list[str]],
    skills: set[str],
    capabilities: set[str],
    extensions: set[str],
    allowed_gates: set[str],
    errors: list[str],
) -> None:
    _validate_membership(rel, "actual.skills", actual_sets["skills"], skills, errors)
    _validate_membership(
        rel,
        "actual.capabilities",
        actual_sets["capabilities"],
        capabilities,
        errors,
    )
    _validate_membership(
        rel,
        "actual.domain_extensions",
        actual_sets["domain_extensions"],
        extensions,
        errors,
    )
    for gate in actual_sets["quality_gates"]:
        if gate.casefold() not in allowed_gates:
            errors.append(f"{rel}: actual.quality_gates contains unknown gate '{gate}'")


def _enforce_l1_actual_anti_over_routing(
    rel: str,
    expected: dict[str, Any],
    actual_sets: dict[str, list[str]],
    errors: list[str],
    risk_rules: dict[str, RiskRule],
) -> None:
    if expected.get("complexity") != "L1":
        return

    risk_triggers = _as_string_list(expected.get("risk_triggers"))
    normalized_triggers = [trigger.casefold() for trigger in risk_triggers or []]
    opt_in_skills: set[str] = set()
    opt_in_capabilities: set[str] = set()
    for trigger in normalized_triggers:
        rule = risk_rules.get(trigger, {})
        opt_in_skills.update(rule.get("skills", ()))
        opt_in_capabilities.update(rule.get("capabilities", ()))

    over_routed = (
        set(actual_sets["skills"]).intersection(L1_OVER_ROUTING_SKILLS)
        - opt_in_skills
    )
    if over_routed:
        errors.append(
            f"{rel}: actual L1 output over-routes to {sorted(over_routed)} "
            "without a matching risk_trigger"
        )

    over_routed_capabilities = (
        set(actual_sets["capabilities"]).intersection(L1_OVER_ROUTING_CAPABILITIES)
        - opt_in_capabilities
    )
    if over_routed_capabilities:
        errors.append(
            f"{rel}: actual L1 output over-routes to capabilities "
            f"{sorted(over_routed_capabilities)} without a matching risk_trigger"
        )
    if actual_sets["domain_extensions"]:
        errors.append(
            f"{rel}: actual L1 output must not include domain_extensions "
            f"({actual_sets['domain_extensions']})"
        )


def _enforce_l4_l5_actual_gate_coverage(
    rel: str,
    expected: dict[str, Any],
    actual_sets: dict[str, list[str]],
    errors: list[str],
) -> None:
    if expected.get("complexity") not in {"L4", "L5"}:
        return
    expected_gates = {
        gate.casefold()
        for gate in _as_string_list(expected.get("quality_gates")) or []
    }
    expected_skills = set(_as_string_list(expected.get("skills")) or [])
    actual_gates = {gate.casefold() for gate in actual_sets["quality_gates"]}
    actual_skills = set(actual_sets["skills"])

    for gate, skill in L4_L5_GATE_SKILLS.items():
        gate_expected = gate in expected_gates
        skill_expected = skill in expected_skills
        if not gate_expected and not skill_expected:
            continue
        if gate_expected and gate not in actual_gates:
            errors.append(f"{rel}: actual L4/L5 output is missing '{gate}'")
        if skill_expected and skill not in actual_skills:
            errors.append(f"{rel}: actual L4/L5 output is missing '{skill}'")


def _enforce_actual_capability_references(
    rel: str,
    actual_sets: dict[str, list[str]],
    reference_paths: set[str],
    capability_metadata: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    selected_owners = set(actual_sets["skills"]) | set(
        actual_sets["domain_extensions"]
    )
    for capability in actual_sets["capabilities"]:
        metadata = capability_metadata.get(capability)
        if metadata is None:
            continue
        if metadata.get("route_level_capability") is True:
            reference = _capability_reference_path(capability, capability_metadata)
            if reference is not None and reference not in reference_paths:
                errors.append(
                    f"{rel}: actual.required_references is missing selected capability "
                    f"reference '{reference}'"
                )
            continue
        used_by = metadata.get("used_by")
        if (
            isinstance(used_by, set)
            and selected_owners
            and not selected_owners & used_by
        ):
            errors.append(
                f"{rel}: selected capability '{capability}' does not map to any "
                "actual selected skill or domain extension through used_by"
            )
        reference = _capability_reference_path(capability, capability_metadata)
        if reference is not None and reference not in reference_paths:
            errors.append(
                f"{rel}: actual.required_references is missing selected capability "
                f"reference '{reference}'"
            )


def _manifest_string_list(
    manifest: dict[str, Any],
    field: str,
    item_key: str | None = None,
) -> list[str] | None:
    return _extract_string_items(manifest.get(field), item_key)


def _stage_manifest_required_schema_errors(rel: str, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required_string_fields = (
        "current_stage",
        "next_stage",
        "product_surface",
        "language_surface",
        "context_budget_mode",
        "context_budget_rationale",
        "handoff_target",
    )
    required_list_fields = (
        "selected_skills",
        "selected_capabilities",
        "selected_domain_extensions",
        "skipped_capabilities",
        "required_evidence",
        "required_quality_gates",
    )
    optional_string_fields = (
        "primary_product_surface",
        "primary_language_surface",
    )
    optional_list_fields = (
        "product_surfaces",
        "language_surfaces",
        "skipped_skills",
        "skipped_routes",
        "skipped_references",
    )
    optional_mapping_fields = ("context_budget",)
    if manifest.get("schema_version") != 1:
        errors.append(f"{rel}: changeforge_stage_route.schema_version must be 1")
    for field in required_string_fields:
        value = manifest.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{rel}: changeforge_stage_route.{field} is required")
    for field in required_list_fields:
        if not isinstance(manifest.get(field), list):
            errors.append(f"{rel}: changeforge_stage_route.{field} must be a list")
    for field in optional_string_fields:
        value = manifest.get(field)
        if value is not None and not isinstance(value, str):
            errors.append(f"{rel}: changeforge_stage_route.{field} must be a string")
    for field in optional_list_fields:
        value = manifest.get(field)
        if value is not None and not isinstance(value, list):
            errors.append(f"{rel}: changeforge_stage_route.{field} must be a list")
    for field in optional_mapping_fields:
        value = manifest.get(field)
        if value is not None and not isinstance(value, dict):
            errors.append(f"{rel}: changeforge_stage_route.{field} must be an object")
    return errors


def _stage_context_budget_errors(rel: str, manifest: dict[str, Any]) -> list[str]:
    payload = manifest.get("context_budget")
    if payload is None:
        return []
    if not isinstance(payload, dict):
        return [f"{rel}: changeforge_stage_route.context_budget must be an object"]
    errors: list[str] = []
    mode = payload.get("mode")
    if mode not in VALID_CONTEXT_BUDGET_MODES:
        errors.append(
            f"{rel}: changeforge_stage_route.context_budget.mode must be one of {sorted(VALID_CONTEXT_BUDGET_MODES)}"
        )
    if mode != manifest.get("context_budget_mode"):
        errors.append(
            f"{rel}: changeforge_stage_route.context_budget.mode must match context_budget_mode"
        )
    for field in (
        "selected_skill_count",
        "selected_capability_count",
        "selected_reference_count",
        "skipped_reference_count",
        "estimated_token_cost",
    ):
        value = payload.get(field)
        if not isinstance(value, int) or value < 0:
            errors.append(f"{rel}: changeforge_stage_route.context_budget.{field} must be a non-negative integer")
    if not isinstance(payload.get("over_budget"), bool):
        errors.append(f"{rel}: changeforge_stage_route.context_budget.over_budget must be boolean")
    if not isinstance(payload.get("rationale"), str) or not payload.get("rationale").strip():
        errors.append(f"{rel}: changeforge_stage_route.context_budget.rationale is required")
    method = payload.get("estimate_method")
    if not isinstance(method, str) or "proxy" not in method.casefold():
        errors.append(
            f"{rel}: changeforge_stage_route.context_budget.estimate_method must identify the estimate as a proxy"
        )
    return errors


def _folded_items(values: Iterable[str]) -> set[str]:
    return {value.strip().casefold() for value in values if value.strip()}


def _required_phrase_missing(required: Iterable[str], actual: Iterable[str]) -> list[str]:
    actual_folded = [item.casefold() for item in actual]
    missing: list[str] = []
    for phrase in required:
        key = phrase.casefold()
        if not any(key in item or item in key for item in actual_folded):
            missing.append(phrase)
    return missing


def _stage_allowed_capabilities(
    current_stage: str,
    product_surfaces: Iterable[str],
    language_surfaces: Iterable[str],
    expected: dict[str, Any],
    stage_model: dict[str, Any],
    risk_rules: dict[str, RiskRule],
) -> set[str]:
    stages = _stage_model_stages(stage_model)
    surfaces = _stage_model_surfaces(stage_model)
    languages = _stage_model_languages(stage_model)
    allowed: set[str] = {"engineering-stage-professionalism"}

    stage_entry = stages.get(current_stage, {})
    allowed.update(_string_tuple(stage_entry.get("default_capabilities")))
    allowed.update(_string_tuple(stage_entry.get("conditional_capabilities")))

    for product_surface in product_surfaces:
        surface_entry = surfaces.get(product_surface)
        if surface_entry is not None:
            allowed.update(_string_tuple(surface_entry.get("default_capabilities")))

    for language_surface in language_surfaces:
        language_entry = languages.get(language_surface)
        if language_entry is not None:
            capability = language_entry.get("capability")
            if isinstance(capability, str) and capability.strip():
                allowed.add(capability.strip())

    for trigger in _as_string_list(expected.get("risk_triggers")) or []:
        rule = risk_rules.get(trigger.casefold(), {})
        allowed.update(rule.get("capabilities", ()))
    return allowed


def _language_capability_by_surface(stage_model: dict[str, Any]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for language, entry in _stage_model_languages(stage_model).items():
        capability = entry.get("capability")
        if isinstance(capability, str) and capability.strip():
            mapping[language] = capability.strip()
    return mapping


def _expected_surface_values(expected: dict[str, Any], field: str) -> set[str]:
    values = _as_expected_surface_list(expected.get(field))
    return set(values or [])


def _manifest_surface_list(
    manifest: dict[str, Any],
    field: str,
    fallback: str,
) -> list[str] | None:
    value = manifest.get(field)
    if value is None:
        return [fallback] if fallback else []
    values = _manifest_string_list(manifest, field)
    if values is None:
        return None
    return list(dict.fromkeys(values))


def _enforce_actual_language_domain_exclusion(
    rel: str,
    expected: dict[str, Any],
    actual_sets: dict[str, list[str]],
    stage_model: dict[str, Any],
    errors: list[str],
) -> None:
    language_capabilities = set(_language_capability_by_surface(stage_model).values())
    actual_language_capabilities = set(actual_sets["capabilities"]) & language_capabilities
    expected_language_surfaces = _expected_surface_values(expected, "expected_language_surface")
    capability_by_language = _language_capability_by_surface(stage_model)
    if expected_language_surfaces:
        allowed_language_capabilities = {
            capability_by_language[language]
            for language in expected_language_surfaces
            if language in capability_by_language
        }
    else:
        allowed_language_capabilities = (
            set(_as_string_list(expected.get("capabilities")) or [])
            & language_capabilities
        )
    extra_language_capabilities = sorted(
        actual_language_capabilities - allowed_language_capabilities
    )
    if extra_language_capabilities:
        errors.append(
            f"{rel}: actual.capabilities contains unselected language capability "
            f"{extra_language_capabilities}"
        )

    expected_extensions = set(_as_string_list(expected.get("domain_extensions")) or [])
    if expected.get("allow_additional_domain_extensions") is True:
        return
    extra_extensions = sorted(set(actual_sets["domain_extensions"]) - expected_extensions)
    if extra_extensions:
        errors.append(
            f"{rel}: actual.domain_extensions contains unselected domain extension "
            f"{extra_extensions}"
        )


def _enforce_actual_stage_route(  # noqa: C901 - manifest schema is intentionally explicit.
    rel: str,
    expected: dict[str, Any],
    output_data: dict[str, Any],
    actual: dict[str, Any],
    actual_sets: dict[str, list[str]],
    capabilities: set[str],
    allowed_stages: set[str],
    allowed_gates: set[str],
    stage_model: dict[str, Any],
    risk_rules: dict[str, RiskRule],
    errors: list[str],
) -> None:
    manifest = _actual_stage_manifest(output_data, actual)
    if _stage_route_required(expected) and manifest is None:
        errors.append(f"{rel}: actual output is missing changeforge_stage_route")
        return
    if manifest is None:
        return

    errors.extend(_stage_manifest_required_schema_errors(rel, manifest))
    errors.extend(_stage_context_budget_errors(rel, manifest))

    stages = _stage_model_stages(stage_model)
    surfaces = _stage_model_surfaces(stage_model)
    languages = _stage_model_languages(stage_model)
    transitions = _stage_model_transitions(stage_model)

    current = manifest.get("current_stage")
    if not isinstance(current, str) or not current.strip():
        errors.append(f"{rel}: changeforge_stage_route.current_stage is required")
        current_stage = ""
    elif current.strip() not in allowed_stages:
        errors.append(
            f"{rel}: changeforge_stage_route.current_stage must be one of "
            f"{sorted(allowed_stages)}, found '{current.strip()}'"
        )
        current_stage = current.strip()
    else:
        current_stage = current.strip()
    expected_stage = expected.get("expected_stage")
    if (
        isinstance(expected_stage, str)
        and expected_stage.strip()
        and current_stage != expected_stage
    ):
        errors.append(
            f"{rel}: changeforge_stage_route.current_stage must be "
            f"{expected_stage!r}, found {current_stage!r}"
        )

    next_stage = manifest.get("next_stage")
    if isinstance(next_stage, str) and next_stage.strip() and current_stage:
        next_stage = next_stage.strip()
        allowed_next = transitions.get(current_stage) or set(
            _string_tuple(stages.get(current_stage, {}).get("allowed_next_stages"))
        )
        if next_stage not in allowed_next:
            errors.append(
                f"{rel}: changeforge_stage_route.next_stage {next_stage!r} is not "
                f"allowed from {current_stage!r}; expected one of {sorted(allowed_next)}"
            )

    product_surface = manifest.get("product_surface")
    if isinstance(product_surface, str) and product_surface.strip():
        product_surface = product_surface.strip()
    else:
        product_surface = ""
    primary_product_surface = manifest.get("primary_product_surface")
    if isinstance(primary_product_surface, str) and primary_product_surface.strip():
        primary_product_surface = primary_product_surface.strip()
    else:
        primary_product_surface = product_surface
    product_surfaces = _manifest_surface_list(
        manifest,
        "product_surfaces",
        product_surface,
    )
    if product_surfaces is None:
        errors.append(f"{rel}: changeforge_stage_route.product_surfaces must be a list")
        product_surfaces = []
    if product_surface and primary_product_surface != product_surface:
        errors.append(
            f"{rel}: changeforge_stage_route.product_surface must match "
            "primary_product_surface for compatibility"
        )
    if (
        primary_product_surface
        and primary_product_surface != "none"
        and primary_product_surface not in product_surfaces
    ):
        errors.append(
            f"{rel}: changeforge_stage_route.primary_product_surface must be present "
            "in product_surfaces"
        )
    if not product_surfaces and product_surface:
        product_surfaces = [product_surface]
    selected_owners = set(actual_sets["skills"]) | set(actual_sets["domain_extensions"])
    for surface in product_surfaces:
        if surface == "none":
            continue
        if surface not in surfaces:
            errors.append(
                f"{rel}: changeforge_stage_route.product_surfaces must contain only "
                f"{sorted(surfaces)} or 'none', found {surface!r}"
            )
        surface_entry = surfaces.get(surface)
        required_skill = surface_entry.get("required_skill") if surface_entry else None
        if isinstance(required_skill, str) and required_skill not in selected_owners:
            errors.append(
                f"{rel}: product_surface {surface!r} requires selected "
                f"skill or extension {required_skill!r}"
            )
    expected_product_surfaces = _expected_surface_values(expected, "expected_product_surface")
    actual_product_surface_values = set(product_surfaces)
    actual_product_surface_values.update(
        surface for surface in (product_surface, primary_product_surface) if surface
    )
    if expected_product_surfaces and not actual_product_surface_values & expected_product_surfaces:
        errors.append(
            f"{rel}: changeforge_stage_route.product_surfaces must include one of "
            f"{sorted(expected_product_surfaces)}, found {sorted(actual_product_surface_values)}"
        )

    language_surface = manifest.get("language_surface")
    if isinstance(language_surface, str) and language_surface.strip():
        language_surface = language_surface.strip()
    else:
        language_surface = ""
    primary_language_surface = manifest.get("primary_language_surface")
    if isinstance(primary_language_surface, str) and primary_language_surface.strip():
        primary_language_surface = primary_language_surface.strip()
    else:
        primary_language_surface = language_surface
    language_surfaces = _manifest_surface_list(
        manifest,
        "language_surfaces",
        language_surface,
    )
    if language_surfaces is None:
        errors.append(f"{rel}: changeforge_stage_route.language_surfaces must be a list")
        language_surfaces = []
    if language_surface and primary_language_surface != language_surface:
        errors.append(
            f"{rel}: changeforge_stage_route.language_surface must match "
            "primary_language_surface for compatibility"
        )
    if (
        primary_language_surface
        and primary_language_surface != "none"
        and primary_language_surface not in language_surfaces
    ):
        errors.append(
            f"{rel}: changeforge_stage_route.primary_language_surface must be present "
            "in language_surfaces"
        )
    if not language_surfaces and language_surface:
        language_surfaces = [language_surface]
    for language in language_surfaces:
        if language == "none":
            continue
        if language not in languages:
            errors.append(
                f"{rel}: changeforge_stage_route.language_surfaces must contain only "
                f"{sorted(languages)} or 'none', found {language!r}"
            )
        language_entry = languages.get(language)
        if language_entry is not None:
            language_stages = set(_string_tuple(language_entry.get("stages")))
            if current_stage and current_stage not in language_stages:
                errors.append(
                    f"{rel}: language_surface {language!r} is not valid for "
                    f"stage {current_stage!r}"
                )
    expected_language_surfaces = _expected_surface_values(expected, "expected_language_surface")
    actual_language_surface_values = set(language_surfaces)
    actual_language_surface_values.update(
        surface for surface in (language_surface, primary_language_surface) if surface
    )
    if expected_language_surfaces and not actual_language_surface_values & expected_language_surfaces:
        errors.append(
            f"{rel}: changeforge_stage_route.language_surfaces must include one of "
            f"{sorted(expected_language_surfaces)}, found {sorted(actual_language_surface_values)}"
        )

    actual_budget = manifest.get("context_budget_mode")
    expected_budget = _expected_context_budget_mode(expected)
    if expected_budget is not None and actual_budget != expected_budget:
        errors.append(
            f"{rel}: changeforge_stage_route.context_budget_mode must be "
            f"{expected_budget!r}, found {actual_budget!r}"
        )

    selected_skills = _manifest_string_list(manifest, "selected_skills", "skill")
    if selected_skills is None:
        errors.append(f"{rel}: changeforge_stage_route.selected_skills must be a list")
        selected_skills = []
    else:
        missing = sorted(set(selected_skills) - set(actual_sets["skills"]))
        if missing:
            errors.append(
                f"{rel}: changeforge_stage_route.selected_skills are not present "
                f"in actual.skills: {missing}"
            )

    selected_extensions = _manifest_string_list(
        manifest,
        "selected_domain_extensions",
        "extension",
    )
    if selected_extensions is None:
        errors.append(
            f"{rel}: changeforge_stage_route.selected_domain_extensions must be a list"
        )
        selected_extensions = []
    else:
        missing = sorted(set(selected_extensions) - set(actual_sets["domain_extensions"]))
        if missing:
            errors.append(
                f"{rel}: changeforge_stage_route.selected_domain_extensions are not "
                f"present in actual.domain_extensions: {missing}"
            )

    selected_capabilities = _manifest_string_list(
        manifest,
        "selected_capabilities",
        "capability",
    )
    if selected_capabilities is None:
        errors.append(
            f"{rel}: changeforge_stage_route.selected_capabilities must be a list"
        )
        selected_capabilities = []
    else:
        missing = sorted(set(selected_capabilities) - set(actual_sets["capabilities"]))
        if missing:
            errors.append(
                f"{rel}: changeforge_stage_route.selected_capabilities are not present "
                f"in actual.capabilities: {missing}"
            )
        allowed_capabilities = _stage_allowed_capabilities(
            current_stage,
            product_surfaces,
            language_surfaces,
            expected,
            stage_model,
            risk_rules,
        )
        outside_stage = sorted(set(selected_capabilities) - allowed_capabilities)
        if outside_stage:
            errors.append(
                f"{rel}: changeforge_stage_route.selected_capabilities are not allowed "
                f"for stage/surface/language/risk: {outside_stage}"
            )
        forbidden_default = set(
            _string_tuple(stages.get(current_stage, {}).get("forbidden_default_capabilities"))
        )
        forbidden_selected = sorted(set(selected_capabilities) & forbidden_default)
        if forbidden_selected:
            errors.append(
                f"{rel}: changeforge_stage_route selected default-forbidden "
                f"capabilities for {current_stage!r}: {forbidden_selected}"
            )

    if current_stage == "debugging-diagnosis" and "refactoring" in selected_capabilities:
        reason = manifest.get("verified_root_cause_reason")
        if not isinstance(reason, str) or not reason.strip():
            errors.append(
                f"{rel}: debugging-diagnosis may select 'refactoring' only with "
                "verified_root_cause_reason"
            )

    required_evidence = _manifest_string_list(manifest, "required_evidence")
    if required_evidence is None:
        errors.append(f"{rel}: changeforge_stage_route.required_evidence must be a list")
        required_evidence = []
    if not required_evidence:
        errors.append(f"{rel}: changeforge_stage_route.required_evidence must be non-empty")
    elif current_stage in stages:
        missing_evidence = _required_phrase_missing(
            _string_tuple(stages[current_stage].get("required_evidence")),
            required_evidence,
        )
        if missing_evidence:
            errors.append(
                f"{rel}: changeforge_stage_route.required_evidence is missing "
                f"stage evidence {missing_evidence}"
            )

    required_gates = _manifest_string_list(manifest, "required_quality_gates")
    if required_gates is None:
        errors.append(
            f"{rel}: changeforge_stage_route.required_quality_gates must be a list"
        )
        required_gates = []
    gates_folded = _folded_items(required_gates)
    if not gates_folded:
        errors.append(
            f"{rel}: changeforge_stage_route.required_quality_gates must be non-empty"
        )
    for gate in required_gates:
        if gate.casefold() not in allowed_gates:
            errors.append(
                f"{rel}: changeforge_stage_route.required_quality_gates contains "
                f"unknown gate '{gate}'"
            )
    stage_gates = {
        gate.casefold()
        for gate in _string_tuple(stages.get(current_stage, {}).get("required_quality_gates"))
    }
    missing_stage_gates = sorted(stage_gates - gates_folded)
    if missing_stage_gates:
        errors.append(
            f"{rel}: changeforge_stage_route.required_quality_gates missing stage "
            f"gate(s) {missing_stage_gates}"
        )
    expected_gates = {
        gate.casefold()
        for gate in _as_string_list(expected.get("quality_gates")) or []
    }
    missing_expected_gates = sorted(expected_gates - gates_folded)
    if missing_expected_gates:
        errors.append(
            f"{rel}: changeforge_stage_route.required_quality_gates missing expected "
            f"route gate(s) {missing_expected_gates}"
        )

    skipped_missing_reason = _stage_skipped_without_reason(manifest)
    if skipped_missing_reason:
        errors.append(
            f"{rel}: changeforge_stage_route.skipped_capabilities missing reason for "
            f"{skipped_missing_reason}"
        )
    skipped_unknown = _stage_skipped_unknown_capabilities(manifest, capabilities)
    if skipped_unknown:
        errors.append(
            f"{rel}: changeforge_stage_route.skipped_capabilities contains unknown "
            f"capability {skipped_unknown}"
        )

    handoff = manifest.get("handoff_target")
    if isinstance(handoff, str) and handoff.strip():
        handoff = handoff.strip()
        legal_targets = (
            set(allowed_stages)
            | {"blocked", "closed"}
            | set(actual_sets["skills"])
            | set(actual_sets["domain_extensions"])
        )
        if handoff not in legal_targets:
            errors.append(
                f"{rel}: changeforge_stage_route.handoff_target {handoff!r} is not "
                f"a legal stage, selected owner, 'blocked', or 'closed'"
            )


def _compare_candidate_output(  # noqa: C901 - schema comparison is branchy.
    case_path: Path,
    case_data: dict[str, Any],
    output_path: Path,
    output_data: Any,
    skills: set[str],
    capabilities: set[str],
    extensions: set[str],
    allowed_gates: set[str],
    allowed_stages: set[str],
    capability_metadata: dict[str, dict[str, Any]],
    stage_model: dict[str, Any],
    risk_rules: dict[str, RiskRule],
    errors: list[str],
) -> None:
    rel = _display_path(output_path)
    if not isinstance(output_data, dict):
        errors.append(f"{rel}: top-level must be a mapping")
        return

    case_id = case_data.get("id")
    output_case_id = _actual_case_id(output_data, output_path)
    if output_case_id != case_id:
        errors.append(
            f"{rel}: case_id must match '{case_id}', found '{output_case_id}'"
        )

    actual = _extract_actual_payload(output_data)
    if actual is None:
        errors.append(f"{rel}: actual router output must be a mapping")
        return

    expected = _case_expected(case_data)
    actual_complexity = actual.get("complexity")
    if actual_complexity != expected.get("complexity"):
        errors.append(
            f"{rel}: actual.complexity must be {expected.get('complexity')}, "
            f"found {actual_complexity!r}"
        )

    expected_risk = expected.get("risk_level")
    if not isinstance(expected_risk, str) or not expected_risk.strip():
        errors.append(
            f"{relpath(ROOT, case_path)}: expected.risk_level is required for "
            "candidate output comparison"
        )
    else:
        actual_risk = _actual_risk_level(actual)
        if actual_risk != expected_risk.casefold():
            errors.append(
                f"{rel}: actual.risk_level must be "
                f"{expected_risk.casefold()}, found {actual_risk!r}"
            )

    actual_sets: dict[str, list[str]] = {}
    item_keys = {
        "skills": "skill",
        "capabilities": "capability",
        "domain_extensions": "extension",
        "quality_gates": "gate",
    }
    for field in EXPECTED_FIELDS:
        values = _actual_string_list(actual, field, item_keys[field])
        if values is None:
            errors.append(f"{rel}: actual.{field} must be a list of strings")
            values = []
        actual_sets[field] = values

    _validate_actual_membership(
        rel,
        actual_sets,
        skills,
        capabilities,
        extensions,
        allowed_gates,
        errors,
    )

    for field in EXPECTED_FIELDS:
        _compare_required_subset(
            rel,
            field,
            _case_expected_list(case_data, field),
            actual_sets[field],
            errors,
        )
        _compare_forbidden_absent(
            rel,
            field,
            _case_forbidden_list(case_data, field),
            actual_sets[field],
            errors,
        )

    references = _actual_reference_pairs(actual)
    if references is None:
        errors.append(
            f"{rel}: actual.required_references must be a list of "
            "{skill, reference} mappings, 'skill:reference' strings, or plain reference paths"
        )
        reference_paths: set[str] = set()
    else:
        reference_paths = _reference_paths(references)
        missing_refs = _missing_router_self_references(references)
        if missing_refs:
            errors.append(
                f"{rel}: actual.required_references is missing router "
                f"self-use references {missing_refs}"
            )
        _compare_required_subset(
            rel,
            "required_references",
            _case_expected_required_references(case_data, capability_metadata),
            reference_paths,
            errors,
        )
        _enforce_actual_capability_references(
            rel,
            actual_sets,
            reference_paths,
            capability_metadata,
            errors,
        )

    _enforce_l1_actual_anti_over_routing(
        rel,
        expected,
        actual_sets,
        errors,
        risk_rules,
    )
    _enforce_l4_l5_actual_gate_coverage(rel, expected, actual_sets, errors)
    _enforce_actual_language_domain_exclusion(
        rel,
        expected,
        actual_sets,
        stage_model,
        errors,
    )
    _enforce_actual_stage_route(
        rel,
        expected,
        output_data,
        actual,
        actual_sets,
        capabilities,
        allowed_stages,
        allowed_gates,
        stage_model,
        risk_rules,
        errors,
    )


def _iter_case_files() -> list[Path]:
    if not EVALS_DIR.exists():
        return []
    return sorted(
        path
        for path in EVALS_DIR.iterdir()
        if path.is_file()
        and path.suffix in {".yaml", ".yml"}
        and not path.name.startswith(".")
    )


def _iter_output_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(
        path
        for path in directory.iterdir()
        if path.is_file()
        and path.suffix in {".yaml", ".yml"}
        and not path.name.startswith(".")
    )


def _repo_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def _display_path(path: Path) -> str:
    try:
        return relpath(ROOT, path)
    except ValueError:
        return str(path)


def _resolve_case_for_output(
    output_path: Path,
    output_data: Any,
    cases: dict[str, tuple[Path, dict[str, Any]]],
    errors: list[str],
) -> tuple[Path, dict[str, Any]] | None:
    rel = _display_path(output_path)
    if not isinstance(output_data, dict):
        errors.append(f"{rel}: top-level must be a mapping")
        return None
    case_id = _actual_case_id(output_data, output_path)
    if case_id is None:
        errors.append(f"{rel}: unable to infer case_id from file or output data")
        return None
    case = cases.get(case_id)
    if case is None:
        errors.append(f"{rel}: no matching golden case for case_id '{case_id}'")
        return None
    return case


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate routing golden cases and optional router outputs."
    )
    parser.add_argument(
        "--candidate-output",
        action="append",
        default=[],
        type=Path,
        help=(
            "Router output YAML to compare against the matching golden case. "
            "May be passed multiple times."
        ),
    )
    parser.add_argument(
        "--candidate-output-dir",
        nargs="?",
        const=OUTPUTS_DIR,
        type=Path,
        help=(
            "Directory of router output YAML files to compare. Defaults to "
            "evals/routing-outputs when provided without an explicit path."
        ),
    )
    parser.add_argument(
        "--min-candidate-outputs",
        default=MIN_CANDIDATE_OUTPUTS,
        type=int,
        help=(
            "Minimum number of candidate outputs required when "
            "--candidate-output-dir is used."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    errors: list[str] = []

    if not EVALS_DIR.exists():
        print(
            "eval-routing: no evals/routing directory found; expected golden cases.",
            file=sys.stderr,
        )
        return 1

    case_files = _iter_case_files()
    if not case_files:
        print(
            "eval-routing: no golden cases found under evals/routing/*.yaml.",
            file=sys.stderr,
        )
        return 1

    skills, capabilities, extensions = _load_registry_names()
    capability_metadata = _load_capability_metadata()
    allowed_triggers, allowed_gates, allowed_stages = _load_routing_allow_lists()
    stage_model = _load_stage_model()
    risk_rules = _load_risk_trigger_rules()
    if not skills or not capabilities or not extensions:
        errors.append(
            "registry data appears empty or unreadable; run validate-registry first."
        )
    if not capability_metadata:
        errors.append(
            "capability metadata appears empty or unreadable; run validate-registry first."
        )
    if not allowed_triggers or not allowed_gates:
        errors.append(
            "routing-rules.yaml is missing risk_escalation_triggers or quality_gates."
        )
    if not allowed_stages:
        errors.append("stage-model.yaml is missing canonical stages.")
    if not stage_model:
        errors.append("stage-model.yaml appears empty or unreadable.")
    if not risk_rules:
        errors.append("routing-rules.yaml is missing risk_trigger_rules.")

    seen_ids: set[str] = set()
    cases: dict[str, tuple[Path, dict[str, Any]]] = {}
    for case_path in case_files:
        try:
            data = load_yaml_file(case_path)
        except ValidationProblem as exc:
            errors.append(str(exc))
            continue
        if isinstance(data, dict):
            case_id = data.get("id")
            if isinstance(case_id, str) and NAME_RE.fullmatch(case_id):
                cases.setdefault(case_id, (case_path, data))
        _validate_case(
            case_path,
            data,
            seen_ids,
            skills,
            capabilities,
            extensions,
            allowed_triggers,
            allowed_gates,
            allowed_stages,
            errors,
            risk_rules,
        )

    _enforce_collection_requirements(cases, extensions, allowed_stages, errors)

    output_files = [_repo_path(path) for path in args.candidate_output]
    if args.candidate_output_dir is not None:
        output_dir = _repo_path(args.candidate_output_dir)
        if not output_dir.exists():
            errors.append(
                f"{_display_path(output_dir)}: candidate output directory not found"
            )
        else:
            directory_outputs = _iter_output_files(output_dir)
            if len(directory_outputs) < args.min_candidate_outputs:
                errors.append(
                    f"{_display_path(output_dir)}: expected at least "
                    f"{args.min_candidate_outputs} candidate output(s), found "
                    f"{len(directory_outputs)}"
                )
            output_files.extend(directory_outputs)

    compared_outputs = 0
    for output_path in output_files:
        try:
            output_data = load_yaml_file(output_path)
        except ValidationProblem as exc:
            errors.append(str(exc))
            continue
        except OSError as exc:
            errors.append(f"{_display_path(output_path)}: {exc}")
            continue
        case = _resolve_case_for_output(output_path, output_data, cases, errors)
        if case is None:
            continue
        case_path, case_data = case
        _compare_candidate_output(
            case_path,
            case_data,
            output_path,
            output_data,
            skills,
            capabilities,
            extensions,
            allowed_gates,
            allowed_stages,
            capability_metadata,
            stage_model,
            risk_rules,
            errors,
        )
        compared_outputs += 1

    if errors:
        return fail_many("eval-routing", errors)

    message = f"eval-routing: {len(case_files)} golden case(s) passed all checks."
    if output_files:
        message += f" {compared_outputs} router output(s) matched golden cases."
    print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
