#!/usr/bin/env python3
"""Routing evaluation for ChangeForge golden cases.

Loads cases from ``evals/routing/*.yaml`` and validates that each case:

* is well-formed (schema, types, unique kebab-case id, valid complexity);
* references real professional skills, foundation capabilities, and domain
  extensions from ``src/registry/``;
* uses risk triggers and quality gates that are declared in
  ``src/registry/routing-rules.yaml``;
* keeps ``expected.*`` and ``forbidden.*`` disjoint;
* satisfies the risk-driven required route rules derived from the routing
    rules (auth/PII → security gate; database migration → data + release;
    payment → payment-trading-extension; wallet → web3; AI prompt → ai-product;
    agent execution risks → agent-execution-discipline and execution discipline
    gate; etc.);
* respects L1 anti-over-routing - heavy gates and design-time skills must
  not appear unless the case opts in through ``risk_triggers``.
* requires L2+ implementation cases that route to backend, frontend, or
  AI review implementation skills to include ``implementation-structure-design``
  unless the case explicitly sets ``expected.structure_required: false``.

By default this remains an offline golden spec check. It does not invoke
any agent or model. When ``--candidate-output`` or ``--candidate-output-dir``
is provided, the script also compares captured router output YAML against
the matching golden case.
"""

from __future__ import annotations

import argparse
import re
import sys
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

VALID_COMPLEXITIES = {"L1", "L2", "L3", "L4", "L5"}
VALID_RISK_LEVELS = {"low", "medium", "high", "critical"}
MIN_ROUTING_CASES = 30
MIN_L1_ANTI_OVER_ROUTING_CASES = 8
MIN_DOMAIN_EXTENSION_CASES = 2
MIN_CANDIDATE_OUTPUTS = 10

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

# Risk-trigger → required professional skill / domain extension rules.
# Each entry maps a risk trigger (matched case-insensitively against the
# routing-rules.yaml ``risk_escalation_triggers`` allow-list) to the set of
# skill or extension names that must appear in ``expected.skills`` or
# ``expected.domain_extensions``.
RISK_REQUIRED_SKILLS: dict[str, tuple[str, ...]] = {
    "auth": ("security-privacy-gate",),
    "authorization": ("security-privacy-gate",),
    "object-level permission": ("security-privacy-gate",),
    "user data": ("security-privacy-gate",),
    "pii": ("security-privacy-gate",),
    "file upload": ("security-privacy-gate",),
    "ai prompt": ("security-privacy-gate",),
    "rag": ("security-privacy-gate",),
    "webhook": ("security-privacy-gate", "integration-change-builder"),
    "external integration": ("integration-change-builder",),
    "secret/config change": ("security-privacy-gate",),
    "dependency upgrade with security impact": ("security-privacy-gate",),
    "database migration": (
        "data-api-contract-changer",
        "delivery-release-gate",
    ),
    "irreversible data operation": (
        "data-api-contract-changer",
        "delivery-release-gate",
    ),
    "production deployment": ("delivery-release-gate",),
    "production incident": (
        "reliability-observability-gate",
        "change-documentation-gate",
    ),
    "cloud iam": ("security-privacy-gate",),
    "public exposure": ("security-privacy-gate",),
    "regulated workload": (
        "security-privacy-gate",
        "delivery-release-gate",
        "change-documentation-gate",
    ),
    "compliance evidence": (
        "security-privacy-gate",
        "delivery-release-gate",
        "change-documentation-gate",
    ),
    "cost anomaly": ("reliability-observability-gate",),
    "missing test evidence": ("quality-test-gate",),
    "hallucinated API risk": ("ai-code-review-refactor",),
    "payment": ("security-privacy-gate",),
    "subscription": ("security-privacy-gate",),
    "billing": ("security-privacy-gate",),
    "wallet": ("security-privacy-gate",),
    "private key": ("security-privacy-gate",),
    "web3 asset": ("security-privacy-gate",),
}

RISK_REQUIRED_DOMAIN_EXTENSIONS: dict[str, str] = {
    "payment": "payment-trading-extension",
    "subscription": "payment-trading-extension",
    "billing": "payment-trading-extension",
    "wallet": "web3-product-extension",
    "private key": "web3-product-extension",
    "web3 asset": "web3-product-extension",
    "ai prompt": "ai-product-extension",
    "rag": "ai-product-extension",
}

RISK_REQUIRED_CAPABILITIES: dict[str, tuple[str, ...]] = {
    "agent claims completion without evidence": ("agent-execution-discipline",),
    "agent diagnosis without verified cause": (
        "agent-execution-discipline",
        "failure-diagnosis",
    ),
    "same agent approach failed twice": (
        "agent-execution-discipline",
        "failure-diagnosis",
    ),
    "local fix without same pattern scan": ("agent-execution-discipline",),
    "new structure without reuse and placement rationale": (
        "agent-execution-discipline",
        "implementation-structure-design",
    ),
    "handoff without risk boundary and validation results": (
        "agent-execution-discipline",
    ),
    "missing test evidence": ("agent-execution-discipline",),
    "environment-blame without inspection": (
        "agent-execution-discipline",
        "failure-diagnosis",
    ),
    "route repair required": ("agent-execution-discipline",),
    "bug may exist in multiple modules": ("agent-execution-discipline",),
    "shared utility pollution risk": (
        "implementation-structure-design",
        "agent-execution-discipline",
    ),
    "business logic in shared utils": (
        "implementation-structure-design",
        "agent-execution-discipline",
    ),
    "hallucinated API risk": ("agent-execution-discipline",),
}

RISK_REQUIRED_QUALITY_GATES: dict[str, tuple[str, ...]] = {
    "agent claims completion without evidence": ("execution discipline gate",),
    "agent diagnosis without verified cause": ("execution discipline gate",),
    "same agent approach failed twice": ("execution discipline gate",),
    "local fix without same pattern scan": ("execution discipline gate",),
    "new structure without reuse and placement rationale": (
        "execution discipline gate",
        "implementation gate",
    ),
    "handoff without risk boundary and validation results": (
        "execution discipline gate",
    ),
}

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
    "skills": ("skills", "skill_path", "professional_skills"),
    "capabilities": (
        "capabilities",
        "foundation_capabilities",
        "capability_path",
    ),
    "domain_extensions": ("domain_extensions", "extensions"),
    "quality_gates": ("quality_gates", "gates"),
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


def _load_routing_allow_lists() -> tuple[set[str], set[str]]:
    """Return (risk_triggers, quality_gates) declared in routing-rules.yaml."""

    path = REGISTRY_DIR / "routing-rules.yaml"
    if not path.is_file():
        return set(), set()
    try:
        data = load_yaml_file(path)
    except ValidationProblem:
        return set(), set()
    if not isinstance(data, dict):
        return set(), set()
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
    return triggers, gates


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


def _validate_case(  # noqa: C901 - branchy validator by design
    path: Path,
    data: Any,
    seen_ids: set[str],
    skills: set[str],
    capabilities: set[str],
    extensions: set[str],
    allowed_triggers: set[str],
    allowed_gates: set[str],
    errors: list[str],
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
    )

    _enforce_l1_anti_over_routing(
        rel,
        complexity,
        normalized_triggers,
        expected_sets,
        errors,
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
        required_skills = RISK_REQUIRED_SKILLS.get(trigger, ())
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
        required_capabilities = RISK_REQUIRED_CAPABILITIES.get(trigger, ())
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
        required_gates = RISK_REQUIRED_QUALITY_GATES.get(trigger, ())
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
        required_extension = RISK_REQUIRED_DOMAIN_EXTENSIONS.get(trigger)
        if required_extension is not None:
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
) -> None:
    if complexity != "L1":
        return

    opt_in_skills: set[str] = set()
    opt_in_capabilities: set[str] = set()
    for trigger in normalized_triggers:
        opt_in_skills.update(RISK_REQUIRED_SKILLS.get(trigger, ()))
        opt_in_capabilities.update(RISK_REQUIRED_CAPABILITIES.get(trigger, ()))

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
    evidence_options = {"implementation gate", "test gate", "documentation gate"}
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


def _enforce_collection_requirements(
    cases: dict[str, tuple[Path, dict[str, Any]]],
    extensions: set[str],
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
) -> None:
    if expected.get("complexity") != "L1":
        return

    risk_triggers = _as_string_list(expected.get("risk_triggers"))
    normalized_triggers = [trigger.casefold() for trigger in risk_triggers or []]
    opt_in_skills: set[str] = set()
    opt_in_capabilities: set[str] = set()
    for trigger in normalized_triggers:
        opt_in_skills.update(RISK_REQUIRED_SKILLS.get(trigger, ()))
        opt_in_capabilities.update(RISK_REQUIRED_CAPABILITIES.get(trigger, ()))

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


def _compare_candidate_output(  # noqa: C901 - schema comparison is branchy.
    case_path: Path,
    case_data: dict[str, Any],
    output_path: Path,
    output_data: Any,
    skills: set[str],
    capabilities: set[str],
    extensions: set[str],
    allowed_gates: set[str],
    errors: list[str],
) -> None:
    rel = relpath(ROOT, output_path)
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
            "{skill, reference} mappings or 'skill:reference' strings"
        )
    else:
        missing_refs = sorted(set(ROUTER_SELF_REFERENCES) - references)
        if missing_refs:
            errors.append(
                f"{rel}: actual.required_references is missing router "
                f"self-use references {missing_refs}"
            )

    _enforce_l1_actual_anti_over_routing(rel, expected, actual_sets, errors)
    _enforce_l4_l5_actual_gate_coverage(rel, expected, actual_sets, errors)


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
    allowed_triggers, allowed_gates = _load_routing_allow_lists()
    if not skills or not capabilities or not extensions:
        errors.append(
            "registry data appears empty or unreadable; run validate-registry first."
        )
    if not allowed_triggers or not allowed_gates:
        errors.append(
            "routing-rules.yaml is missing risk_escalation_triggers or quality_gates."
        )

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
            errors,
        )

    _enforce_collection_requirements(cases, extensions, errors)

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
