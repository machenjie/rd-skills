#!/usr/bin/env python3
"""Static rule-based router evaluation for ChangeForge golden cases.

Loads cases from ``evals/routing/*.yaml`` and validates that each case:

* is well-formed (schema, types, unique kebab-case id, valid complexity);
* references real professional skills, foundation capabilities, and domain
  extensions from ``src/registry/``;
* uses risk triggers and quality gates that are declared in
  ``src/registry/routing-rules.yaml``;
* keeps ``expected.*`` and ``forbidden.*`` disjoint;
* satisfies the risk-driven required-gate rules derived from the routing
  rules (auth/PII → security gate; database migration → data + release;
  payment → payment-trading-extension; wallet → web3; AI prompt → ai-product;
  etc.);
* respects L1 anti-over-routing — heavy gates and design-time skills must
  not appear unless the case opts in through ``risk_triggers``.

This is an offline spec check. It does not invoke any agent or model. A
future "compare router output to golden" mode can reuse the same case
schema without changing the cases.
"""

from __future__ import annotations

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

VALID_COMPLEXITIES = {"L1", "L2", "L3", "L4", "L5"}

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

EXPECTED_FIELDS: tuple[str, ...] = (
    "skills",
    "capabilities",
    "domain_extensions",
    "quality_gates",
)


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
        rel, "expected.capabilities", expected_sets["capabilities"], capabilities, errors
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
    expected_extensions = set(expected_sets["domain_extensions"])
    forbidden_skills = set(forbidden_sets["skills"])
    forbidden_extensions = set(forbidden_sets["domain_extensions"])

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
    for trigger in normalized_triggers:
        opt_in_skills.update(RISK_REQUIRED_SKILLS.get(trigger, ()))

    expected_skills = set(expected_sets["skills"])
    over_routed = (
        expected_skills.intersection(L1_OVER_ROUTING_SKILLS) - opt_in_skills
    )
    if over_routed:
        errors.append(
            f"{rel}: L1 case over-routes to {sorted(over_routed)} without a "
            f"matching risk_trigger"
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


def main() -> int:
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
    for case_path in case_files:
        try:
            data = load_yaml_file(case_path)
        except ValidationProblem as exc:
            errors.append(str(exc))
            continue
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

    if errors:
        return fail_many("eval-routing", errors)

    print(
        f"eval-routing: {len(case_files)} golden case(s) passed all checks."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
