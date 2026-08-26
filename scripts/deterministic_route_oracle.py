"""Shared deterministic routing oracle for validation fixtures only.

This module is intentionally outside ``src/``. It supports repository tests and
reports; it is not installed and is not a runtime router.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from validation_utils import (
    CORE_CONTRACTS,
    DOMAIN_MODIFIER_ONLY_ROUTING_MODE,
    ValidationProblem,
    domain_modifier_routing_authority,
    domain_routing_mode_map,
    foundation_runtime_matcher_authority,
    layer3_selector_authority,
    load_yaml_file,
    professional_automatic_routing_authority,
    professional_routing_authority,
    validate_main_assignment,
    validate_main_execution,
    validate_route_decision,
)

_canonical_foundation_runtime_matcher_authority = (
    foundation_runtime_matcher_authority
)

ROOT = Path(__file__).resolve().parents[1]
DOMAIN_REGISTRY = ROOT / "src" / "registry" / "domain-skills.yaml"
FOUNDATION_REGISTRY = ROOT / "src" / "registry" / "foundation-skills.yaml"
PROFESSIONAL_REGISTRY = ROOT / "src" / "registry" / "professional-skills.yaml"
CROSS_PLATFORM_MODIFIER = "cross-platform-client-extension"
DOMAIN_CLASSIFIER_FIELDS = frozenset(
    {
        "skill",
        "eligible",
        "evidence_ids",
        "rejection_reasons",
    }
)
DOMAIN_REJECTION_REASONS = frozenset(
    {
        "concrete-platform-evidence-missing",
        "unchanged-or-anti-trigger",
        "boundary-evidence-missing",
        "conflicting-domain-evidence",
        "domain-evidence-missing",
    }
)
CONCRETE_CLIENT_PLATFORM_ORDER = (
    "android-platform-extension",
    "ios-ipados-platform-extension",
    "windows-platform-extension",
    "macos-platform-extension",
    "linux-desktop-platform-extension",
)


class RoutingIntegrityError(ValidationProblem):
    """Fail one public route closed when typed routing authority is invalid."""

    code = "routing-integrity-failure"


ORACLE_ADMISSION_AUTHORITY_CONTRACT = (
    "changeforge.oracle-admission-authority/v1"
)
_FOUNDATION_SOURCE_KINDS = (
    "direct-static",
    "dynamic-helper-only",
    "runtime-matcher",
)
_FOUNDATION_SOURCE_SYMBOLS = {
    "direct-static": frozenset({"_route_impl"}),
    "dynamic-helper-only": frozenset(
        {
            "_accessibility_behavior_requested",
            "_build_route_candidates",
            "_implementation_owner_layer3",
            "_review_risk_layer3",
        }
    ),
    "runtime-matcher": frozenset(
        {"foundation_runtime_matcher_authority"}
    ),
}
_EXPECTED_PRIMARY_TASK_SKILLS = (
    "acceptance-criteria-builder",
    "ai-code-review-refactor",
    "architecture-impact-reviewer",
    "backend-change-builder",
    "change-documentation-gate",
    "change-intake-compiler",
    "data-api-contract-changer",
    "data-middleware-change-builder",
    "delivery-release-gate",
    "domain-impact-modeler",
    "engineering-artifact-review",
    "engineering-change-analysis",
    "experience-impact-modeler",
    "frontend-change-builder",
    "incident-response-coordinator",
    "installed-client-change-builder",
    "integration-change-builder",
    "logging-design-gate",
    "platform-infrastructure-change-builder",
    "quality-test-gate",
    "reliability-observability-gate",
    "repository-tooling-change-builder",
    "security-privacy-gate",
    "task-dag-planner",
)
_EXPECTED_REVIEW_TASK_SKILLS = (
    "ai-code-review-refactor",
    "architecture-impact-reviewer",
    "change-documentation-gate",
    "delivery-release-gate",
    "engineering-artifact-review",
    "high-risk-design-review",
    "logging-design-gate",
    "quality-test-gate",
    "reliability-observability-gate",
    "security-privacy-gate",
)
_KNOWN_TASK_SKILLS = frozenset(
    {
        *_EXPECTED_PRIMARY_TASK_SKILLS,
        *_EXPECTED_REVIEW_TASK_SKILLS,
    }
)
_SELECTOR_REGISTRY_METADATA: dict[str, Any] | None = None


def _selector_registry_metadata() -> dict[str, Any]:
    """Load declarative selector records without importing Runtime matchers."""

    global _SELECTOR_REGISTRY_METADATA
    if _SELECTOR_REGISTRY_METADATA is not None:
        return _SELECTOR_REGISTRY_METADATA
    data = load_yaml_file(FOUNDATION_REGISTRY)
    domain_data = load_yaml_file(DOMAIN_REGISTRY)
    authority = data.get("selector_authority") if isinstance(data, dict) else None
    selectors = authority.get("selectors") if isinstance(authority, dict) else None
    aliases = authority.get("aliases") if isinstance(authority, dict) else None
    subsets = (
        authority.get("alias_member_subsets")
        if isinstance(authority, dict)
        else None
    )
    if (
        not isinstance(selectors, list)
        or not isinstance(aliases, list)
        or not isinstance(subsets, dict)
    ):
        raise RoutingIntegrityError(
            "registry-owned selector declarations are unavailable"
        )
    route_bindings = {
        record["selector_id"]: tuple(
            (
                binding["candidate_id"],
                binding["rule_id"],
                binding["routing_family"],
                binding["primary_skill"],
                binding["review_skill"],
            )
            for binding in record["route_bindings"]
        )
        for record in selectors
    }
    alias_bindings: dict[str, tuple[tuple[object, ...], ...]] = {}
    for alias in aliases:
        alias_bindings.setdefault(alias["candidate_id"], ())
        alias_bindings[alias["candidate_id"]] = (
            *alias_bindings[alias["candidate_id"]],
            (
                tuple(alias["source_selector_ids"]),
                alias["primary_skill"],
                alias["review_skill"],
            ),
        )
    _SELECTOR_REGISTRY_METADATA = {
        "route_bindings": route_bindings,
        "alias_bindings": alias_bindings,
        "alias_member_subsets": {
            candidate_id: tuple(layer3)
            for candidate_id, layer3 in subsets.items()
        },
        "admitted_foundations": frozenset(
            layer3
            for record in selectors
            for layer3 in record["selectable_layer3"]
        ),
        "runtime_foundations": tuple(
            record["selectable_layer3"][0]
            for record in selectors
            if record["source"]["kind"] == "runtime-matcher"
        ),
        "dynamic_sources": {
            record["selectable_layer3"][0]: record["source"]["symbol"]
            for record in selectors
            if record["source"]["kind"] == "dynamic-helper-only"
        },
        "direct_blueprints": tuple(
            (
                record["selector_id"],
                tuple(record["selectable_layer3"]),
                tuple(record["positive_evidence"][:-1]),
                record["owner_bindings"][0]["primary_skill"],
                record["owner_bindings"][0]["review_skill"],
            )
            for record in selectors
            if record["source"]["kind"] == "direct-static"
        ),
        "domain_registry": domain_data,
    }
    return _SELECTOR_REGISTRY_METADATA


_SELECTOR_DECLARATIONS = _selector_registry_metadata()
_RUNTIME_FOUNDATION_SELECTORS = _SELECTOR_DECLARATIONS["runtime_foundations"]
_ADMITTED_FOUNDATION_SKILLS = _SELECTOR_DECLARATIONS["admitted_foundations"]
_DYNAMIC_FOUNDATION_SOURCES = _SELECTOR_DECLARATIONS["dynamic_sources"]
_DIRECT_FOUNDATION_SELECTOR_BLUEPRINTS = (
    _SELECTOR_DECLARATIONS["direct_blueprints"]
)
_FOUNDATION_SELECTOR_ADDITIONAL_OWNER_BINDINGS = {
    selector_id: bindings
    for selector_id, bindings in _SELECTOR_DECLARATIONS["route_bindings"].items()
    if bindings and not selector_id.startswith("dynamic-foundation:")
}
_DYNAMIC_FOUNDATION_OWNER_BINDINGS = {
    selector_id: bindings
    for selector_id, bindings in _SELECTOR_DECLARATIONS["route_bindings"].items()
    if bindings and selector_id.startswith("dynamic-foundation:")
}
_FOUNDATION_ALIAS_SOURCE_BINDINGS = _SELECTOR_DECLARATIONS["alias_bindings"]
_FOUNDATION_ALIAS_MEMBER_SUBSETS = (
    _SELECTOR_DECLARATIONS["alias_member_subsets"]
)
_DIRECT_ONLY_FOUNDATION_TASK_EVIDENCE = frozenset(
    {"review-ambiguous-structure-repository-first"}
)
_IMPLEMENTATION_OWNER_FAMILY_EVIDENCE = {
    "backend": "backend-surface",
    "data-middleware": "middleware-surface",
    "frontend": "browser-ui-surface",
    "installed-client": "installed-application-surface",
    "integration": "integration-edge",
    "logging": "diagnostic-record-surface",
    "platform-infrastructure": "infrastructure-definition",
    "repository-tooling": "repository-developer-tool",
    "test-validation": "behavior-proof-surface",
}


@dataclass(frozen=True, slots=True)
class _FoundationRouteOrigin:
    kind: str
    candidate_id: str
    rule_id: str | None
    routing_family: str | None
    primary_skill: str
    review_skill: str
    evidence_ids: tuple[str, ...]


def _validated_text(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
    ):
        raise RoutingIntegrityError(f"{label} must be nonblank trimmed text")
    return value


@dataclass(frozen=True, slots=True)
class FoundationSelectorSource:
    kind: str
    symbol: str
    source_id: str

    def __post_init__(self) -> None:
        kind = _validated_text(self.kind, label="selector source kind")
        symbol = _validated_text(self.symbol, label="selector source symbol")
        _validated_text(self.source_id, label="selector source id")
        if (
            kind not in _FOUNDATION_SOURCE_KINDS
            or symbol not in _FOUNDATION_SOURCE_SYMBOLS[kind]
        ):
            raise RoutingIntegrityError(
                "Foundation selector source is outside the closed authority"
            )


@dataclass(frozen=True, slots=True)
class FoundationSelectorOwnerBinding:
    primary_skill: str
    review_skill: str

    def __post_init__(self) -> None:
        primary = _validated_text(
            self.primary_skill,
            label="selector primary Skill",
        )
        review = _validated_text(
            self.review_skill,
            label="selector review Skill",
        )
        if primary not in _KNOWN_TASK_SKILLS or review not in _KNOWN_TASK_SKILLS:
            raise RoutingIntegrityError(
                "Foundation selector owner binding is undeclared"
            )


@dataclass(frozen=True, slots=True)
class FoundationSelectorRecord:
    selector_id: str
    foundations: tuple[str, ...]
    source: FoundationSelectorSource
    evidence_ids: tuple[str, ...]
    owner_bindings: tuple[FoundationSelectorOwnerBinding, ...]

    def __post_init__(self) -> None:
        selector_id = _validated_text(
            self.selector_id,
            label="Foundation selector id",
        )
        if self.source.source_id != selector_id:
            raise RoutingIntegrityError(
                "Foundation selector source id must equal selector id"
            )
        for label, values in (
            ("Foundation selector Foundations", self.foundations),
            ("Foundation selector evidence", self.evidence_ids),
        ):
            if (
                not isinstance(values, tuple)
                or not values
                or len(values) != len(set(values))
            ):
                raise RoutingIntegrityError(
                    f"{label} must be a non-empty unique tuple"
                )
            for value in values:
                _validated_text(value, label=label)
        if len(self.foundations) > 3:
            raise RoutingIntegrityError(
                "Foundation selector may admit at most three Foundations"
            )
        terminal = f"foundation-selector:{selector_id}"
        if self.evidence_ids[-1] != terminal or self.evidence_ids.count(
            terminal
        ) != 1:
            raise RoutingIntegrityError(
                "Foundation selector evidence must end in one terminal marker"
            )
        if (
            not isinstance(self.owner_bindings, tuple)
            or not self.owner_bindings
            or len(self.owner_bindings) != len(set(self.owner_bindings))
        ):
            raise RoutingIntegrityError(
                "Foundation selector owner bindings must be non-empty unique"
            )


@dataclass(frozen=True, slots=True)
class OracleAdmissionAuthority:
    contract: str
    foundation_selectors: tuple[FoundationSelectorRecord, ...]
    primary_task_skills: tuple[str, ...]
    review_task_skills: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.contract != ORACLE_ADMISSION_AUTHORITY_CONTRACT:
            raise RoutingIntegrityError(
                "Oracle admission authority contract is invalid"
            )
        selector_ids = [
            record.selector_id for record in self.foundation_selectors
        ]
        foundations = [
            foundation
            for record in self.foundation_selectors
            for foundation in record.foundations
        ]
        expected_order = sorted(
            self.foundation_selectors,
            key=lambda record: (
                _FOUNDATION_SOURCE_KINDS.index(record.source.kind),
                record.selector_id,
            ),
        )
        if (
            not self.foundation_selectors
            or list(self.foundation_selectors) != expected_order
            or len(selector_ids) != len(set(selector_ids))
            or len(foundations) != len(set(foundations))
            or frozenset(foundations) != _ADMITTED_FOUNDATION_SKILLS
        ):
            raise RoutingIntegrityError(
                "Foundation selector inventory is incomplete, duplicate, or "
                "out of canonical order"
            )
        if self.primary_task_skills != _EXPECTED_PRIMARY_TASK_SKILLS:
            raise RoutingIntegrityError(
                "Oracle primary task Skill authority is not canonical"
            )
        if self.review_task_skills != _EXPECTED_REVIEW_TASK_SKILLS:
            raise RoutingIntegrityError(
                "Oracle review task Skill authority is not canonical"
            )


@dataclass(frozen=True, slots=True)
class _FoundationSelectorOwnerBindingSpec:
    primary_skill: str
    review_skill: str


@dataclass(frozen=True, slots=True)
class _FoundationSelectorSpec:
    selector_id: str
    foundations: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    owner_bindings: tuple[_FoundationSelectorOwnerBindingSpec, ...]


def oracle_admission_authority(
    foundation_registry: object | None = None,
    professional_registry: object | None = None,
) -> OracleAdmissionAuthority:
    """Project the closed, JIT selector and Professional route authority."""

    foundation_data = (
        load_yaml_file(FOUNDATION_REGISTRY)
        if foundation_registry is None
        else foundation_registry
    )
    professional_data = (
        load_yaml_file(PROFESSIONAL_REGISTRY)
        if professional_registry is None
        else professional_registry
    )
    domain_data = _SELECTOR_DECLARATIONS["domain_registry"]
    if not isinstance(foundation_data, dict):
        raise RoutingIntegrityError(
            "Foundation selector registry must be a mapping"
        )
    if not isinstance(professional_data, dict):
        raise RoutingIntegrityError(
            "Professional selector registry must be a mapping"
        )
    try:
        selector_authority = layer3_selector_authority(
            foundation_data,
            professional_data,
            domain_data,
            context="Oracle admission selector authority",
        )
        professional_automatic_routing_authority(
            professional_data,
            context="Oracle admission Professional authority",
        )
    except ValidationProblem as exc:
        raise RoutingIntegrityError(str(exc)) from exc

    professional_rows = professional_data.get("professional_skills")
    if not isinstance(professional_rows, list):
        raise RoutingIntegrityError(
            "Oracle admission registries lack canonical Skill rows"
        )
    professional_by_name = {
        row.get("name"): row
        for row in professional_rows
        if isinstance(row, dict) and isinstance(row.get("name"), str)
    }
    primary_skills = tuple(
        sorted(
            name
            for name, row in professional_by_name.items()
            if row.get("task_routable") is True
            and name != "high-risk-design-review"
        )
    )
    review_skills = tuple(
        sorted(
            name
            for name, row in professional_by_name.items()
            if row.get("task_routable") is True
            and "review-agent" in row.get("role_support", [])
        )
    )
    if (
        primary_skills != _EXPECTED_PRIMARY_TASK_SKILLS
        or review_skills != _EXPECTED_REVIEW_TASK_SKILLS
    ):
        raise RoutingIntegrityError(
            "Professional task routing inventory is not canonical"
        )
    records = [
        FoundationSelectorRecord(
            selector_id=record["selector_id"],
            foundations=tuple(record["selectable_layer3"]),
            source=FoundationSelectorSource(
                kind=record["source"]["kind"],
                symbol=record["source"]["symbol"],
                source_id=record["selector_id"],
            ),
            evidence_ids=tuple(record["positive_evidence"]),
            owner_bindings=tuple(
                FoundationSelectorOwnerBinding(
                    primary_skill=binding["primary_skill"],
                    review_skill=binding["review_skill"],
                )
                for binding in record["owner_bindings"]
            ),
        )
        for record in selector_authority["selectors"]
    ]
    return OracleAdmissionAuthority(
        contract=ORACLE_ADMISSION_AUTHORITY_CONTRACT,
        foundation_selectors=tuple(records),
        primary_task_skills=primary_skills,
        review_task_skills=review_skills,
    )


def _foundation_records_for_payload(
    admission_authority: OracleAdmissionAuthority,
    foundations: list[str],
) -> list[FoundationSelectorRecord]:
    if (
        not isinstance(admission_authority, OracleAdmissionAuthority)
        or not isinstance(foundations, list)
        or any(
            not isinstance(foundation, str)
            or not foundation
            or foundation != foundation.strip()
            for foundation in foundations
        )
        or len(foundations) != len(set(foundations))
    ):
        raise RoutingIntegrityError(
            "Foundation payload authority requires ordered unique names"
        )
    records_by_foundation = {
        foundation: record
        for record in admission_authority.foundation_selectors
        for foundation in record.foundations
    }
    unknown = [
        foundation
        for foundation in foundations
        if foundation not in records_by_foundation
    ]
    if unknown:
        raise RoutingIntegrityError(
            f"Foundation payload is absent from selector authority: {unknown!r}"
        )
    selected = set(foundations)
    return [
        record
        for record in admission_authority.foundation_selectors
        if selected.intersection(record.foundations)
    ]


def _foundation_route_spec_matches(
    candidate: dict[str, Any],
    spec: tuple[object, ...],
) -> bool:
    if len(spec) != 5:
        raise RoutingIntegrityError(
            "Foundation route binding spec lacks exact route scope"
        )
    (
        candidate_id,
        rule_id,
        routing_family,
        primary_skill,
        review_skill,
    ) = spec
    if (
        candidate.get("candidate_id"),
        candidate.get("rule_id"),
        candidate.get("routing_family"),
        candidate.get("primary_skill"),
        candidate.get("review_skill"),
    ) != (
        candidate_id,
        rule_id,
        routing_family,
        primary_skill,
        review_skill,
    ):
        return False
    if (
        isinstance(candidate_id, str)
        and candidate_id.startswith("implementation-owner:")
    ):
        required_evidence = _IMPLEMENTATION_OWNER_FAMILY_EVIDENCE.get(
            routing_family
        )
        evidence = candidate.get("evidence")
        observed_family_evidence = (
            {
                marker
                for marker
                in _IMPLEMENTATION_OWNER_FAMILY_EVIDENCE.values()
                if marker in evidence
            }
            if isinstance(evidence, list)
            else set()
        )
        return (
            isinstance(required_evidence, str)
            and observed_family_evidence == {required_evidence}
        )
    return True


def _foundation_preparation_binding_matches(
    candidate: dict[str, Any],
) -> bool:
    if (
        candidate.get("candidate_id") != "implementation-preparation"
        or candidate.get("rule_id")
        != "implementation-preparation-candidate"
        or candidate.get("routing_family") is not None
    ):
        return False
    context = candidate.get("candidate_layer3_context")
    if not isinstance(context, dict) or context.get("kind") != "preparation":
        return False
    risk = context.get("risk")
    owners = context.get("owners")
    if risk is not None:
        review_skill = (
            risk.get("review_skill")
            if isinstance(risk, dict)
            else None
        )
    elif isinstance(owners, list) and len(owners) == 1:
        owner = owners[0]
        review_skill = (
            owner.get("review_skill")
            if isinstance(owner, dict)
            else None
        )
    else:
        review_skill = "architecture-impact-reviewer"
    return (
        candidate.get("primary_skill"),
        candidate.get("review_skill"),
    ) == ("engineering-change-analysis", review_skill)


def _foundation_route_binding_declared(
    candidate: dict[str, Any],
    records: list[FoundationSelectorRecord],
) -> bool:
    if not records:
        return False
    source_ids = tuple(record.selector_id for record in records)
    candidate_id = candidate.get("candidate_id")
    rule_id = candidate.get("rule_id")
    routing_family = candidate.get("routing_family")
    pair = (
        candidate.get("primary_skill"),
        candidate.get("review_skill"),
    )
    if (
        len(records) == 1
        and candidate_id == rule_id == records[0].selector_id
        and routing_family is None
    ):
        preferred = records[0].owner_bindings[0]
        return pair == (
            preferred.primary_skill,
            preferred.review_skill,
        )
    if (
        isinstance(candidate_id, str)
        and candidate_id == rule_id
        and candidate_id in _FOUNDATION_ALIAS_SOURCE_BINDINGS
    ):
        binding_declared = (
            source_ids,
            candidate.get("primary_skill"),
            candidate.get("review_skill"),
        ) in _FOUNDATION_ALIAS_SOURCE_BINDINGS[candidate_id]
        member_subset = _FOUNDATION_ALIAS_MEMBER_SUBSETS.get(candidate_id)
        return (
            binding_declared
            and (
                member_subset is None
                or tuple(candidate.get("layer3_skills", ()))
                == member_subset
            )
        )
    if rule_id == "implementation-dependency-risk":
        dependency_selector_id = (
            "dynamic-foundation:dependency-vulnerability-scanning"
        )
        dependency_specs = _DYNAMIC_FOUNDATION_OWNER_BINDINGS[
            dependency_selector_id
        ]
        return (
            dependency_selector_id in source_ids
            and any(
                _foundation_route_spec_matches(candidate, spec)
                for spec in dependency_specs
            )
            and all(
                pair
                in {
                    (binding.primary_skill, binding.review_skill)
                    for binding in record.owner_bindings
                }
                for record in records
            )
        )
    if _foundation_preparation_binding_matches(candidate):
        return True
    fixed_derived = {
        "critical-unknown": (
            "critical-unknown-candidate",
            "engineering-change-analysis",
            "architecture-impact-reviewer",
        ),
        "ordinary-ambiguity": (
            "ordinary-ambiguity-candidate",
            "engineering-change-analysis",
            "architecture-impact-reviewer",
        ),
        "review-generic": (
            "review-generic-candidate",
            "ai-code-review-refactor",
            "ai-code-review-refactor",
        ),
    }
    if candidate_id in fixed_derived:
        expected_rule, primary_skill, review_skill = fixed_derived[
            candidate_id
        ]
        return (
            rule_id,
            routing_family,
            *pair,
        ) == (
            expected_rule,
            None,
            primary_skill,
            review_skill,
        )
    if candidate_id in REVIEW_RISK_PRIMARY:
        skill = REVIEW_RISK_PRIMARY[candidate_id]
        return (
            rule_id,
            routing_family,
            *pair,
        ) == (
            f"{candidate_id}-candidate",
            None,
            skill,
            skill,
        )
    return all(
        any(
            _foundation_route_spec_matches(candidate, spec)
            for spec in (
                *_FOUNDATION_SELECTOR_ADDITIONAL_OWNER_BINDINGS.get(
                    record.selector_id,
                    (),
                ),
                *_DYNAMIC_FOUNDATION_OWNER_BINDINGS.get(
                    record.selector_id,
                    (),
                ),
            )
        )
        for record in records
    )


def _foundation_route_identity_declared(
    candidate: dict[str, Any],
    records: list[FoundationSelectorRecord],
) -> bool:
    if not records:
        return False
    candidate_id = candidate.get("candidate_id")
    rule_id = candidate.get("rule_id")
    routing_family = candidate.get("routing_family")
    if (
        len(records) == 1
        and candidate_id == rule_id == records[0].selector_id
        and routing_family is None
    ):
        return True
    if (
        isinstance(candidate_id, str)
        and candidate_id == rule_id
        and candidate_id in _FOUNDATION_ALIAS_SOURCE_BINDINGS
    ):
        return True
    if candidate_id in {
        "critical-unknown",
        "ordinary-ambiguity",
        "implementation-preparation",
        "review-generic",
        *REVIEW_RISK_PRIMARY,
    }:
        return True
    return any(
        (
            candidate_id,
            rule_id,
            routing_family,
        )
        == spec[:3]
        for record in records
        for spec in (
            *_FOUNDATION_SELECTOR_ADDITIONAL_OWNER_BINDINGS.get(
                record.selector_id,
                (),
            ),
            *_DYNAMIC_FOUNDATION_OWNER_BINDINGS.get(
                record.selector_id,
                (),
            ),
        )
    )


def _foundation_source_rows(
    records: list[FoundationSelectorRecord],
    *,
    candidate: dict[str, Any],
) -> list[dict[str, Any]]:
    binding = (
        candidate.get("primary_skill"),
        candidate.get("review_skill"),
    )
    if not all(isinstance(value, str) and value for value in binding):
        raise RoutingIntegrityError(
            "Foundation payload owner binding must be non-empty text"
        )
    if not _foundation_route_binding_declared(candidate, records):
        if (
            candidate.get("candidate_type")
            in {
                "explicit-route",
                "fallback-route",
                "artifact-review-route",
            }
            and not _foundation_route_identity_declared(candidate, records)
        ):
            raise RoutingIntegrityError(
                f"unknown Foundation route rule "
                f"{candidate.get('rule_id')!r} for selector sources "
                f"{tuple(record.selector_id for record in records)!r}"
            )
        raise RoutingIntegrityError(
            f"Foundation selectors "
            f"{tuple(record.selector_id for record in records)!r} used an "
            f"undeclared selector owner binding for exact route scope: "
            f"{binding!r}"
        )
    rows = []
    for record in records:
        rows.append(
            {
                "candidate_id": record.selector_id,
                "foundations": list(record.foundations),
                "evidence": list(record.evidence_ids),
                "owner_binding": {
                    "primary_skill": binding[0],
                    "review_skill": binding[1],
                },
            }
        )
    return rows


def _canonical_foundation_evidence(
    records: list[FoundationSelectorRecord],
) -> list[str]:
    """Merge selector evidence while preserving every record-local order."""

    first_seen: dict[str, int] = {}
    outgoing: dict[str, set[str]] = {}
    indegree: dict[str, int] = {}
    for record in records:
        for evidence_id in record.evidence_ids:
            if evidence_id not in first_seen:
                first_seen[evidence_id] = len(first_seen)
                outgoing[evidence_id] = set()
                indegree[evidence_id] = 0
        for before, after in zip(
            record.evidence_ids,
            record.evidence_ids[1:],
        ):
            if after not in outgoing[before]:
                outgoing[before].add(after)
                indegree[after] += 1

    ready = sorted(
        (
            evidence_id
            for evidence_id, degree in indegree.items()
            if degree == 0
        ),
        key=first_seen.__getitem__,
    )
    ordered: list[str] = []
    while ready:
        evidence_id = ready.pop(0)
        ordered.append(evidence_id)
        for successor in sorted(
            outgoing[evidence_id],
            key=first_seen.__getitem__,
        ):
            indegree[successor] -= 1
            if indegree[successor] == 0:
                ready.append(successor)
                ready.sort(key=first_seen.__getitem__)
    if len(ordered) != len(first_seen):
        raise RoutingIntegrityError(
            "Foundation selector evidence order is contradictory"
        )
    return ordered


def _foundation_task_evidence_records(
    candidate: dict[str, Any],
    records: list[FoundationSelectorRecord],
) -> list[FoundationSelectorRecord]:
    direct_selector_id = (
        candidate.get("candidate_id")
        if (
            len(records) == 1
            and candidate.get("candidate_id") == candidate.get("rule_id")
            and candidate.get("routing_family") is None
        )
        else None
    )
    return [
        record
        for record in records
        if (
            record.selector_id
            not in _DIRECT_ONLY_FOUNDATION_TASK_EVIDENCE
            or record.selector_id == direct_selector_id
        )
    ]


def _bind_foundation_candidate(
    candidate: dict[str, Any],
    foundations: list[str],
    *,
    admission_authority: OracleAdmissionAuthority,
) -> None:
    records = _foundation_records_for_payload(
        admission_authority,
        foundations,
    )
    if not records:
        return
    evidence = candidate.get("evidence")
    if not isinstance(evidence, list) or not all(
        isinstance(item, str) and item for item in evidence
    ):
        raise RoutingIntegrityError(
            "Foundation candidate evidence must be non-empty text"
        )
    rows = _foundation_source_rows(
        records,
        candidate=candidate,
    )
    allowed_terminals = {
        record.evidence_ids[-1] for record in records
    }
    undeclared_terminals = [
        item
        for item in evidence
        if item.startswith("foundation-selector:")
        and item not in allowed_terminals
    ]
    if undeclared_terminals:
        raise RoutingIntegrityError(
            "Foundation candidate used an undeclared selector terminal: "
            f"{undeclared_terminals!r}"
        )
    canonical_evidence = _canonical_foundation_evidence(records)
    task_evidence_records = _foundation_task_evidence_records(
        candidate,
        records,
    )
    evidence[:] = [
        item
        for item in evidence
        if item not in canonical_evidence
    ]
    evidence.extend(
        _canonical_foundation_evidence(task_evidence_records)
    )
    candidate["source_foundation_candidates"] = rows


def _validate_foundation_route_origin(
    candidate: dict[str, Any],
    origin: _FoundationRouteOrigin | None,
) -> None:
    candidate_id = candidate.get("candidate_id")
    requires_origin = (
        isinstance(candidate_id, str)
        and (
            candidate_id.startswith("implementation-owner:")
            or candidate_id in REVIEW_RISK_PRIMARY
        )
    )
    if origin is None:
        if requires_origin:
            raise RoutingIntegrityError(
                "Foundation candidate lacks classifier origin"
            )
        return
    if not isinstance(origin, _FoundationRouteOrigin):
        raise RoutingIntegrityError(
            "Foundation candidate classifier origin is malformed"
        )
    expected = (
        origin.candidate_id,
        origin.rule_id,
        origin.routing_family,
        origin.primary_skill,
        origin.review_skill,
    )
    observed = (
        candidate_id,
        candidate.get("rule_id"),
        candidate.get("routing_family"),
        candidate.get("primary_skill"),
        candidate.get("review_skill"),
    )
    if observed != expected:
        raise RoutingIntegrityError(
            "Foundation candidate changed its classifier origin scope"
        )
    if origin.kind not in {"implementation-owner", "review-risk"}:
        raise RoutingIntegrityError(
            "Foundation candidate classifier origin kind is undeclared"
        )
    evidence = candidate.get("evidence")
    if (
        not isinstance(evidence, list)
        or evidence[: len(origin.evidence_ids)]
        != list(origin.evidence_ids)
    ):
        raise RoutingIntegrityError(
            "Foundation candidate changed its classifier origin evidence"
        )


def _validate_foundation_candidate(
    candidate: dict[str, Any],
    foundations: list[str],
    *,
    admission_authority: OracleAdmissionAuthority,
) -> None:
    records = _foundation_records_for_payload(
        admission_authority,
        foundations,
    )
    if not records:
        if "source_foundation_candidates" in candidate:
            raise RoutingIntegrityError(
                "empty Foundation payload retained selector source rows"
            )
        return
    expected_rows = _foundation_source_rows(
        records,
        candidate=candidate,
    )
    if candidate.get("source_foundation_candidates") != expected_rows:
        raise RoutingIntegrityError(
            "Foundation candidate did not resolve exact selector source rows"
        )
    evidence = candidate.get("evidence")
    if not isinstance(evidence, list) or not all(
        isinstance(item, str) and item for item in evidence
    ):
        raise RoutingIntegrityError(
            "Foundation candidate evidence must be non-empty text"
        )
    task_evidence_records = _foundation_task_evidence_records(
        candidate,
        records,
    )
    expected_terminals = [
        record.evidence_ids[-1] for record in task_evidence_records
    ]
    actual_terminals = [
        item
        for item in evidence
        if item.startswith("foundation-selector:")
    ]
    undeclared = [
        terminal
        for terminal in actual_terminals
        if terminal not in expected_terminals
    ]
    if undeclared:
        raise RoutingIntegrityError(
            "Foundation candidate used an undeclared selector terminal: "
            f"{undeclared!r}"
        )
    if (
        len(actual_terminals) != len(set(actual_terminals))
        or set(actual_terminals) != set(expected_terminals)
    ):
        raise RoutingIntegrityError(
            "Foundation candidate lost exact selector evidence"
        )
    for record in task_evidence_records:
        position = 0
        for evidence_id in record.evidence_ids:
            try:
                position = evidence.index(evidence_id, position) + 1
            except ValueError as exc:
                raise RoutingIntegrityError(
                    "Foundation candidate lost exact selector evidence"
                ) from exc


def _synchronize_foundation_candidate(
    candidate: dict[str, Any],
    foundations: list[str],
    *,
    admission_authority: OracleAdmissionAuthority,
) -> None:
    expected_records = _foundation_records_for_payload(
        admission_authority,
        foundations,
    )
    expected_ids = [
        record.selector_id for record in expected_records
    ]
    current_rows = candidate.get("source_foundation_candidates")
    current_ids = (
        [
            row.get("candidate_id")
            for row in current_rows
            if isinstance(row, dict)
        ]
        if isinstance(current_rows, list)
        else []
    )
    if current_ids == expected_ids:
        return
    if current_rows is not None and (
        not isinstance(current_rows, list)
        or len(current_ids) != len(current_rows)
    ):
        raise RoutingIntegrityError(
            "Foundation candidate source rows are malformed"
        )
    evidence = candidate.get("evidence")
    if not isinstance(evidence, list):
        raise RoutingIntegrityError(
            "Foundation candidate evidence must be a list"
        )
    stale_terminals = {
        row["evidence"][-1]
        for row in current_rows or []
        if (
            isinstance(row.get("evidence"), list)
            and row["evidence"]
        )
    }
    candidate["evidence"] = [
        item for item in evidence if item not in stale_terminals
    ]
    candidate.pop("source_foundation_candidates", None)
    if expected_records:
        _bind_foundation_candidate(
            candidate,
            foundations,
            admission_authority=admission_authority,
        )


_DOMAIN_ROUTE_SPEC_CATALOG: dict[str, dict[str, Any]] = {
    "ai-product-extension": {
        "anti_atoms": (
            "no ai surface",
            "without a model decision",
        ),
        "families": {
            "retrieval-data": {
                "trigger_atoms": ("prompt", "retrieval", "embedding", "ai data"),
                "domain_signals": (
                    "prompt",
                    "retrieval",
                    "embedding",
                    "ai data",
                    "rag",
                ),
                "boundary_signals": (
                    "tenant",
                    "permission",
                    "model context",
                    "prompt injection",
                    "data authority",
                ),
                "boundary_atoms": ("permission", "model context"),
            },
            "agent-model-authority": {
                "trigger_atoms": ("model", "evaluation"),
                "domain_signals": (
                    "agent",
                    "tool call",
                    "tool-calling",
                    "model decision",
                    "model prediction",
                    "model inference",
                ),
                "qualified_domain_signals": {
                    "model": (
                        "ai",
                        "agent",
                        "inference",
                        "model context",
                        "prediction",
                        "prompt",
                        "safety policy",
                        "tool call",
                    ),
                    "evaluation": (
                        "ai",
                        "agent",
                        "inference",
                        "model decision",
                        "prediction",
                        "prompt",
                        "safety policy",
                    ),
                },
                "boundary_signals": (
                    "delegated authority",
                    "side-effect",
                    "side effect",
                    "consequential",
                    "eligibility",
                    "safety policy",
                    "principal",
                    "approval",
                ),
                "boundary_atoms": ("delegated authority", "consequential"),
            },
        },
    },
    "bigdata-product-extension": {
        "anti_atoms": (
            "ordinary transactional persistence",
            "without a distributed pipeline",
        ),
        "families": {
            "stream-cdc-replay": {
                "trigger_atoms": ("stream",),
                "domain_signals": ("cdc", "stream", "replay"),
                "boundary_signals": (
                    "cutover",
                    "backfill",
                    "live event",
                    "downstream",
                    "ordering",
                    "checkpoint",
                    "failover",
                ),
                "boundary_atoms": ("checkpoint", "downstream"),
            },
            "distributed-batch-schema": {
                "trigger_atoms": (
                    "batch",
                    "data lake",
                    "distributed compute",
                    "schema evolution",
                    "high-volume pipeline",
                ),
                "domain_signals": (
                    "batch",
                    "distributed backfill",
                    "batch pipeline",
                    "data lake",
                    "distributed compute",
                    "schema evolution",
                    "high-volume pipeline",
                ),
                "boundary_signals": (
                    "partition",
                    "consumer",
                    "ownership",
                    "reprocessing",
                    "schema compatibility",
                    "checkpoint",
                ),
                "boundary_atoms": (
                    "partition",
                    "consumer",
                    "schema compatibility",
                ),
            },
        },
    },
    "iot-embedded-extension": {
        "anti_atoms": (
            "ordinary cloud",
            "without device or firmware behavior",
        ),
        "families": {
            "firmware-update-recovery": {
                "trigger_atoms": ("firmware",),
                "domain_signals": ("ota", "firmware", "bootloader"),
                "boundary_signals": (
                    "power loss",
                    "brownout",
                    "boot",
                    "rollback",
                    "recovery",
                    "activation",
                    "image signature",
                ),
                "boundary_atoms": ("recovery", "activation"),
            },
            "device-physical-runtime": {
                "trigger_atoms": (
                    "device",
                    "edge",
                    "protocol",
                    "sensor",
                    "actuator",
                    "physical safety",
                    "constrained runtime",
                ),
                "domain_signals": (
                    "device",
                    "edge",
                    "actuator",
                    "sensor",
                    "physical safety",
                    "edge device",
                    "device provisioning",
                    "constrained runtime",
                ),
                "qualified_domain_signals": {
                    "protocol": (
                        "actuator",
                        "constrained runtime",
                        "device",
                        "edge",
                        "firmware",
                        "hardware",
                        "physical safety",
                        "sensor",
                    ),
                },
                "boundary_signals": (
                    "safe-state",
                    "physical safety",
                    "timing",
                    "deadline",
                    "hardware",
                    "credential",
                    "connectivity",
                ),
                "boundary_atoms": ("physical safety", "timing", "hardware"),
            },
        },
    },
    "low-level-systems-extension": {
        "anti_atoms": (
            "no systems boundary",
            "without a native abi, os, or resource boundary",
        ),
        "families": {
            "abi-ffi-memory": {
                "trigger_atoms": ("c", "c++", "rust", "memory", "abi"),
                "domain_signals": (
                    "c",
                    "c++",
                    "rust",
                    "memory",
                    "abi",
                    "ffi",
                    "public abi",
                    "native memory",
                    "unsafe memory",
                ),
                "boundary_signals": (
                    "ownership",
                    "allocator",
                    "lifetime",
                    "unwind",
                    "callback",
                    "publication",
                    "undefined behavior",
                    "os",
                    "operating system",
                    "resource",
                ),
                "boundary_atoms": ("ownership", "resource"),
            },
            "kernel-realtime-concurrency": {
                "trigger_atoms": (
                    "kernel",
                    "driver",
                    "real-time",
                    "systems concurrency",
                ),
                "domain_signals": (
                    "kernel",
                    "driver",
                    "syscall",
                    "real-time",
                    "systems concurrency",
                    "lock-free",
                ),
                "boundary_signals": (
                    "privilege",
                    "resource",
                    "deadline",
                    "timing",
                    "reclamation",
                    "race",
                    "interrupt",
                    "platform",
                ),
                "boundary_atoms": ("deadline", "platform"),
            },
        },
    },
    "android-platform-extension": {
        "anti_atoms": (
            "without a confirmed android target",
            "release approval",
        ),
        "families": {
            "platform-lifecycle-authority": {
                "trigger_atoms": ("android",),
                "domain_signals": ("android",),
                "boundary_signals": (
                    "application lifecycle",
                    "activity",
                    "background work",
                    "foreground service",
                    "mobile lifecycle",
                    "process recreation",
                    "saved-state",
                    "saved state",
                    "screen",
                    "state",
                ),
                "boundary_atoms": ("application lifecycle",),
            },
            "accessibility-platform-authority": {
                "trigger_atoms": ("platform accessibility behavior",),
                "domain_signals": (
                    "android",
                    "platform accessibility behavior",
                ),
                "boundary_signals": (
                    "accessibility behavior",
                    "accessibility focus",
                    "compose semantics",
                    "d-pad navigation",
                    "display scaling",
                    "font scaling",
                    "keyboard navigation",
                    "keyboard focus",
                    "pointer alternative",
                    "switch access",
                    "talkback",
                    "voice access",
                ),
                "boundary_atoms": ("accessibility behavior",),
            },
        },
    },
    "cloud-platform-extension": {
        "anti_atoms": (
            "unknown cloud scope",
            "without cloud control-plane dependency",
        ),
        "families": {
            "cloud-account-authority": {
                "trigger_atoms": ("cloud control plane",),
                "domain_signals": (
                    "cloud control plane",
                    "cloud account",
                    "cloud accounts",
                ),
                "boundary_signals": (
                    "account authority",
                    "iam",
                    "source change",
                ),
                "boundary_atoms": ("account authority",),
            },
        },
    },
    "cross-platform-client-extension": {
        "anti_atoms": (
            "framework name without repository build release or published-artifact target evidence",
            "unknown target",
        ),
        "families": {
            "shared-target-ownership": {
                "trigger_atoms": ("shared installed client",),
                "domain_signals": ("shared installed client",),
                "boundary_signals": ("concrete platform targets",),
                "boundary_atoms": ("concrete platform targets",),
            },
        },
    },
    "ios-ipados-platform-extension": {
        "anti_atoms": (
            "without a confirmed ios/ipados target",
            "release approval",
        ),
        "families": {
            "platform-lifecycle-authority": {
                "trigger_atoms": ("ios/ipados",),
                "domain_signals": ("ios/ipados", "ios", "ipados"),
                "boundary_signals": (
                    "application lifecycle",
                    "mobile lifecycle",
                    "scene",
                    "restoration",
                    "swiftui",
                    "view",
                    "state",
                ),
                "boundary_atoms": ("application lifecycle",),
            },
        },
    },
    "linux-desktop-platform-extension": {
        "anti_atoms": (
            "linux server",
            "without a confirmed linux desktop target",
        ),
        "families": {
            "desktop-session-authority": {
                "trigger_atoms": ("linux graphical desktop",),
                "domain_signals": ("linux graphical desktop",),
                "boundary_signals": (
                    "app",
                    "d-bus",
                    "desktop session",
                    "state",
                    "window",
                ),
                "boundary_atoms": ("desktop session",),
            },
        },
    },
    "macos-platform-extension": {
        "anti_atoms": (
            "without a confirmed macos target",
            "release signing",
        ),
        "families": {
            "platform-lifecycle-authority": {
                "trigger_atoms": ("macos installed application",),
                "domain_signals": (
                    "macos installed application",
                    "macos appkit",
                ),
                "boundary_signals": (
                    "application lifecycle",
                    "window lifecycle",
                    "window-lifecycle",
                    "window",
                    "state",
                ),
                "boundary_atoms": ("application lifecycle",),
            },
        },
    },
    "windows-platform-extension": {
        "anti_atoms": (
            "generic backend",
            "without a confirmed windows target",
        ),
        "families": {
            "application-identity-authority": {
                "trigger_atoms": ("windows packaged desktop application",),
                "domain_signals": (
                    "windows packaged desktop application",
                    "windows packaged desktop app",
                    "windows msix",
                ),
                "boundary_signals": (
                    "application identity",
                    "protocol handler",
                    "protocol-handler",
                    "window",
                    "state",
                ),
                "boundary_atoms": ("application identity",),
            },
            "service-lifecycle-authority": {
                "trigger_atoms": ("windows service",),
                "domain_signals": ("windows service",),
                "boundary_signals": ("service lifecycle",),
                "boundary_atoms": ("service lifecycle",),
            },
        },
    },
    "web3-product-extension": {
        "anti_atoms": (
            "ordinary non-web3",
            "without chain or custody behavior",
        ),
        "families": {
            "chain-custody-finality": {
                "trigger_atoms": (
                    "blockchain",
                    "wallet",
                    "key",
                    "chain transaction",
                    "custody behavior",
                ),
                "domain_signals": (
                    "blockchain",
                    "chain transaction",
                    "custody behavior",
                    "on-chain signing",
                ),
                "qualified_domain_signals": {
                    "key": (
                        "blockchain",
                        "chain",
                        "custody",
                        "on-chain",
                        "wallet",
                    ),
                    "wallet": (
                        "asset",
                        "blockchain",
                        "chain",
                        "custody",
                        "on-chain",
                        "signing",
                        "smart contract",
                    ),
                },
                "boundary_signals": (
                    "finality",
                    "reorg",
                    "recovery",
                    "authority",
                    "nonce",
                    "asset",
                    "key isolation",
                ),
                "boundary_atoms": ("recovery", "finality"),
            },
            "contract-cross-chain": {
                "trigger_atoms": ("smart contract",),
                "domain_signals": (
                    "smart-contract",
                    "smart contract",
                    "cross-chain",
                    "bridge",
                    "layer 2",
                    "governance proposal",
                    "oracle feed",
                ),
                "boundary_signals": (
                    "upgrade",
                    "replay",
                    "proof",
                    "challenge window",
                    "privileged",
                    "pause",
                    "reentrancy",
                ),
                "boundary_atoms": ("upgrade", "replay"),
            },
        },
    },
    "payment-trading-extension": {
        "anti_atoms": (
            "no monetary invariant",
            "without funds, ledger, settlement, or execution state",
        ),
        "families": {
            "money-ledger-settlement": {
                "trigger_atoms": (
                    "payment",
                    "ledger",
                    "balance",
                    "settlement",
                    "wallet",
                    "money movement",
                ),
                "domain_signals": (
                    "payment",
                    "money movement",
                    "ledger",
                    "balance",
                    "settlement",
                    "wallet",
                    "financial wallet",
                ),
                "boundary_signals": (
                    "authorization",
                    "idempotency",
                    "reconciliation",
                    "conservation",
                    "capture",
                    "refund",
                    "custody",
                    "accounting",
                ),
                "boundary_atoms": ("accounting", "reconciliation"),
            },
            "trading-order-execution": {
                "trigger_atoms": ("trading", "order"),
                "domain_signals": (
                    "order",
                    "trading",
                    "trade execution",
                    "market order",
                    "venue order",
                    "partial fill",
                ),
                "boundary_signals": (
                    "cancel",
                    "sequence",
                    "fill",
                    "kill switch",
                    "allocation",
                    "settlement",
                ),
                "boundary_atoms": ("fill", "settlement"),
            },
        },
    },
}


def domain_route_specs(
    registry_data: object,
    *,
    catalog: dict[str, dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    """Return oracle specs after registry-owned routing validation."""

    source = _DOMAIN_ROUTE_SPEC_CATALOG if catalog is None else catalog
    modes = domain_routing_mode_map(registry_data)
    registry_names = set(modes)
    catalog_names = set(source)
    if registry_names != catalog_names:
        raise ValidationProblem(
            "Domain routing spec catalog differs from Registry membership; "
            f"missing={sorted(registry_names - catalog_names)}; "
            f"extra={sorted(catalog_names - registry_names)}"
        )
    nonautomatic = sorted(
        name
        for name, mode in modes.items()
        if mode != DOMAIN_MODIFIER_ONLY_ROUTING_MODE
    )
    if nonautomatic:
        raise ValidationProblem(
            "Domain routing membership must be modifier-only; "
            f"non_modifier_only={nonautomatic}"
        )
    return {
        name: source[name]
        for name in modes
    }


ALL_DOMAIN_ROUTE_SPECS = dict(_DOMAIN_ROUTE_SPEC_CATALOG)
DOMAIN_ROUTE_SPECS = domain_route_specs(load_yaml_file(DOMAIN_REGISTRY))


def _declared_layer3_candidates(primary_skill: str) -> frozenset[str]:
    """Read one Professional's Layer 3 eligibility from its owning registry."""

    entries = load_yaml_file(PROFESSIONAL_REGISTRY).get(
        "professional_skills",
        [],
    )
    matches = [
        entry
        for entry in entries
        if isinstance(entry, dict) and entry.get("name") == primary_skill
    ]
    if len(matches) != 1:
        raise ValidationProblem(
            f"Professional registry must contain exactly one {primary_skill!r}"
        )
    candidates = matches[0].get("layer3_candidates", [])
    if not isinstance(candidates, list) or not all(
        isinstance(item, str) and item for item in candidates
    ):
        raise ValidationProblem(
            f"{primary_skill} layer3_candidates must be literal non-empty text"
        )
    return frozenset(candidates)


ENGINEERING_CHANGE_ANALYSIS_LAYER3 = _declared_layer3_candidates(
    "engineering-change-analysis"
)
AI_CODE_REVIEW_LAYER3 = _declared_layer3_candidates(
    "ai-code-review-refactor"
)
REVIEW_RISK_PRIMARY = {
    "review-security-risk": "security-privacy-gate",
    "review-release-risk": "delivery-release-gate",
    "review-logging-risk": "logging-design-gate",
    "review-reliability-risk": "reliability-observability-gate",
}
REVIEW_RISK_PRIMARY_LAYER3 = {
    candidate_id: _declared_layer3_candidates(primary_skill)
    for candidate_id, primary_skill in REVIEW_RISK_PRIMARY.items()
}


def _normalize_route_prompt(prompt: str) -> str:
    """Normalize one prompt exactly once inside the route-once pipeline."""

    return " ".join(prompt.casefold().split())


_FOUNDATION_MATCHER_CLAUSE_RE = re.compile(
    r"[.!?;]+|\b(?:while|but|although|whereas|yet)\b"
)
_FOUNDATION_MATCHER_ANALYSIS_ACTIONS = frozenset(
    {
        "analyze",
        "analyse",
    }
)
_FOUNDATION_MATCHER_SELECTION_ACTIONS = frozenset(
    {
        "select",
        "selects",
        "selected",
        "selecting",
        "choose",
        "chooses",
        "chosen",
        "choosing",
    }
)
_FOUNDATION_MATCHER_MUTATION_ACTIONS = frozenset(
    {
        "add",
        "build",
        "change",
        "create",
        "fix",
        "implement",
        "migrate",
        "plan",
        "prepare",
        "refactor",
        "repair",
        "update",
        "write",
    }
)
_FOUNDATION_MATCHER_NEGATORS = (
    "do not",
    "must not",
    "should not",
    "will not",
    "never",
    "not to",
    "without",
)
_FOUNDATION_OCCURRENCE_REQUEST_PREFIXES = (
    (),
    ("please",),
    ("please", "carefully"),
    ("kindly",),
    ("could", "you"),
    ("could", "you", "please"),
    ("would", "you"),
    ("can", "you"),
    ("we", "need", "to"),
    ("we", "should"),
)
_FOUNDATION_OCCURRENCE_FUNCTION_TOKENS = frozenset(
    {
        "a",
        "an",
        "the",
        "whether",
        "why",
        "how",
        "which",
        "what",
        "if",
    }
)
_FOUNDATION_OCCURRENCE_NEUTRAL_FILLERS = frozenset(
    {"one", "two", "three", "four", "five"}
)
_FOUNDATION_OCCURRENCE_CONNECTORS = frozenset({"and", "or"})
_FOUNDATION_OCCURRENCE_ACTIONS = frozenset(
    {"analyze", "analyse", "extract", "model"}
)
_FOUNDATION_OCCURRENCE_BARRIERS = frozenset(
    {
        "document",
        "documents",
        "documented",
        "documenting",
        "skip",
        "skips",
        "skipped",
        "skipping",
        "ignore",
        "ignores",
        "ignored",
        "ignoring",
        "exclude",
        "excludes",
        "excluded",
        "excluding",
        "omit",
        "omits",
        "omitted",
        "omitting",
        "leave",
        "leaves",
        "left",
        "leaving",
        "keep",
        "keeps",
        "kept",
        "keeping",
    }
)


def _normalize_foundation_matcher_value(value: str) -> str:
    """Casefold matcher input and reduce non-alphanumerics to one space."""

    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.casefold()).split())


def _foundation_matcher_clauses(value: str) -> tuple[str, ...]:
    """Return the closed set of normalized semantic matcher clauses."""

    return tuple(
        normalized
        for raw_clause in _FOUNDATION_MATCHER_CLAUSE_RE.split(
            value.casefold()
        )
        if (normalized := _normalize_foundation_matcher_value(raw_clause))
    )


def _foundation_matcher_contains(clause: str, term: str) -> bool:
    normalized_term = _normalize_foundation_matcher_value(term)
    return bool(
        normalized_term
        and f" {normalized_term} " in f" {clause} "
    )


def _foundation_matcher_has_non_negated_action(
    clause: str,
    actions: frozenset[str],
) -> bool:
    if not actions:
        return False
    action_re = re.compile(
        r"\b(?:" + "|".join(re.escape(action) for action in sorted(actions)) + r")\b"
    )
    for action_match in action_re.finditer(clause):
        prefix = clause[: action_match.start()].rstrip()
        negated = any(
            prefix == negator or prefix.endswith(f" {negator}")
            for negator in _FOUNDATION_MATCHER_NEGATORS
        )
        if not negated:
            return True
    return False


def _foundation_matcher_subject_is_absent(
    clause: str,
    subject: str,
) -> bool:
    escaped_subject = re.escape(
        _normalize_foundation_matcher_value(subject)
    ).replace(r"\ ", r"\s+")
    if not escaped_subject:
        return False
    article = r"(?:(?:a|an|the)\s+)?"
    absence_forms = (
        rf"\bno\s+{article}{escaped_subject}\b",
        rf"\bwithout\s+{article}{escaped_subject}\b",
        rf"\bunfixed\s+{escaped_subject}\b",
        rf"\b{escaped_subject}\s+unfixed\b",
        rf"\b{escaped_subject}\s+(?:is\s+)?not\s+fixed\b",
        rf"\b{escaped_subject}\s+(?:(?:has|have)\s+)?not\s+been\s+fixed\b",
    )
    return any(re.search(pattern, clause) for pattern in absence_forms)


def _foundation_occurrence_action_is_request(
    tokens: tuple[str, ...],
    action_index: int,
    valid_action_indexes: tuple[int, ...],
) -> bool:
    """Return whether an action is a closed request or coordinated action."""

    prefix = tokens[:action_index]
    if prefix in _FOUNDATION_OCCURRENCE_REQUEST_PREFIXES:
        return True
    return bool(
        valid_action_indexes
        and action_index > 0
        and tokens[action_index - 1]
        in _FOUNDATION_OCCURRENCE_CONNECTORS
    )


def _foundation_occurrence_object_spans(
    tokens: tuple[str, ...],
    objects: list[str],
) -> tuple[tuple[int, int], ...]:
    """Return non-overlapping object spans in longest-leftmost order."""

    object_tokens = sorted(
        (
            tuple(_normalize_foundation_matcher_value(item).split())
            for item in objects
        ),
        key=lambda item: (-len(item), item),
    )
    spans: list[tuple[int, int]] = []
    index = 0
    while index < len(tokens):
        match = next(
            (
                candidate
                for candidate in object_tokens
                if tokens[index:index + len(candidate)] == candidate
            ),
            None,
        )
        if match is None:
            index += 1
            continue
        spans.append((index, index + len(match)))
        index += len(match)
    return tuple(spans)


def _foundation_occurrence_has_suppressed_postfix(
    tokens: tuple[str, ...],
    object_end: int,
    *,
    query_tokens: set[str],
) -> bool:
    """Reject unchanged/background/workflow mentions not governed as work."""

    suffix = tokens[object_end:object_end + 6]
    if "background" in suffix:
        return True
    if "historical" in suffix and "context" in suffix:
        return True
    if (
        "workflow" in suffix
        and any(token == "for" for token in suffix[:4])
    ):
        return True
    if query_tokens & {"whether", "why"}:
        return False
    suppressed_sequences = (
        ("is", "unchanged"),
        ("are", "unchanged"),
        ("remain", "unchanged"),
        ("remains", "unchanged"),
        ("is", "not", "required"),
        ("are", "not", "required"),
        ("out", "of", "scope"),
        ("is", "out", "of", "scope"),
        ("are", "out", "of", "scope"),
    )
    return any(
        suffix[:len(sequence)] == sequence
        for sequence in suppressed_sequences
    )


def _foundation_occurrence_relation_matches(
    clause: str,
    relation: dict[str, Any],
) -> bool:
    """Evaluate one validated governed-object relation."""

    tokens = tuple(clause.split())
    if not tokens:
        return False

    relation_actions = frozenset(relation["actions"])
    governance_tokens = {
        *_FOUNDATION_OCCURRENCE_ACTIONS,
        *_FOUNDATION_MATCHER_MUTATION_ACTIONS,
        *_FOUNDATION_OCCURRENCE_BARRIERS,
    }
    valid_action_indexes: list[int] = []
    for index, token in enumerate(tokens):
        if token not in _FOUNDATION_OCCURRENCE_ACTIONS:
            continue
        if _foundation_occurrence_action_is_request(
            tokens,
            index,
            tuple(valid_action_indexes),
        ):
            valid_action_indexes.append(index)
    if not valid_action_indexes:
        return False

    qualifiers = frozenset(relation["owner_relation"]["qualifiers"])
    modifiers = frozenset(relation["non_owner_modifiers"])
    neutral_gap_tokens = {
        *_FOUNDATION_OCCURRENCE_FUNCTION_TOKENS,
        *_FOUNDATION_OCCURRENCE_NEUTRAL_FILLERS,
        *_FOUNDATION_OCCURRENCE_CONNECTORS,
        *qualifiers,
        *modifiers,
    }
    object_spans = _foundation_occurrence_object_spans(
        tokens,
        relation["objects"],
    )
    for object_start, object_end in object_spans:
        governing_indexes = [
            index
            for index, token in enumerate(tokens[:object_start])
            if token in governance_tokens
        ]
        if not governing_indexes:
            continue
        action_index = governing_indexes[-1]
        if (
            action_index not in valid_action_indexes
            or tokens[action_index] not in relation_actions
        ):
            continue

        gap_start = action_index + 1
        for index in range(action_index + 1, object_start):
            if tokens[index] not in _FOUNDATION_OCCURRENCE_CONNECTORS:
                continue
            preceding = tokens[gap_start:index]
            if any(
                token not in neutral_gap_tokens
                for token in preceding
            ):
                gap_start = index + 1
        gap = tokens[gap_start:object_start]
        if any(token not in neutral_gap_tokens for token in gap):
            continue
        filler_count = sum(
            token in _FOUNDATION_OCCURRENCE_NEUTRAL_FILLERS
            for token in gap
        )
        if filler_count > 4:
            continue

        query_tokens = set(tokens[action_index + 1:object_start])
        background_window = tokens[
            max(action_index + 1, object_start - 4):object_start
        ]
        if (
            "background" in background_window
            or (
                "historical" in background_window
                and "context" in background_window
            )
        ):
            continue
        if _foundation_occurrence_has_suppressed_postfix(
            tokens,
            object_end,
            query_tokens=query_tokens,
        ):
            continue
        return True
    return False


def _foundation_occurrence_matcher_matches(
    value: str,
    runtime_matcher: dict[str, Any],
) -> bool:
    """Evaluate one validated registry-owned occurrence matcher."""

    clauses = _foundation_matcher_clauses(value)
    if not clauses:
        return False
    if any(
        _foundation_matcher_has_non_negated_action(
            clause,
            _FOUNDATION_MATCHER_MUTATION_ACTIONS,
        )
        for clause in clauses
    ):
        return False
    relation_results = [
        _foundation_occurrence_relation_matches(clause, relation)
        for relation in runtime_matcher["relations"]
        for clause in clauses
    ]
    return (
        any(relation_results)
        if runtime_matcher["combine"] == "any"
        else all(relation_results)
    )


def _foundation_runtime_matcher_matches(
    value: str,
    runtime_matcher: dict[str, Any],
) -> bool:
    """Evaluate one validated registry-owned semantic matcher."""

    if (
        runtime_matcher.get("contract")
        == "foundation-occurrence-matcher/v1"
    ):
        return _foundation_occurrence_matcher_matches(
            value,
            runtime_matcher,
        )

    clauses = _foundation_matcher_clauses(value)
    if not clauses:
        return False
    if not any(
        _foundation_matcher_has_non_negated_action(
            clause,
            _FOUNDATION_MATCHER_ANALYSIS_ACTIONS,
        )
        for clause in clauses
    ):
        return False
    if any(
        _foundation_matcher_has_non_negated_action(
            clause,
            _FOUNDATION_MATCHER_MUTATION_ACTIONS,
        )
        for clause in clauses
    ):
        return False

    for predicate in runtime_matcher["predicates"]:
        predicate_matches = False
        for clause in clauses:
            group_hits = [
                [
                    term
                    for term in group
                    if _foundation_matcher_contains(clause, term)
                ]
                for group in predicate["term_groups"]
            ]
            if not all(group_hits):
                continue
            if (
                predicate["action"] == "selection"
                and not _foundation_matcher_has_non_negated_action(
                    clause,
                    _FOUNDATION_MATCHER_SELECTION_ACTIONS,
                )
            ):
                continue
            if predicate["polarity"] == "absent" and not all(
                any(
                    _foundation_matcher_subject_is_absent(clause, term)
                    for term in hits
                )
                for hits in group_hits
            ):
                continue
            predicate_matches = True
            break
        if not predicate_matches:
            return False
    return True


def _build_route_candidates(
    raw_candidates: list[dict[str, Any]],
    route_candidates: list[dict[str, Any]],
    *,
    normalized_text: str,
    implementation_policy: dict[str, Any],
    domain_specs: dict[str, dict[str, Any]],
    admission_authority: OracleAdmissionAuthority | None = None,
) -> list[dict[str, Any]]:
    """Finalize the complete typed candidate cohort once."""

    domain_classification = classify_domain_modifiers(
        normalized_text,
        specs=domain_specs,
    )
    domain_requests = _validated_domain_classifier_snapshot(
        domain_classification,
        domain_specs=domain_specs,
    )
    reserved_reason = "domain-layer3-authorization-conflict"
    reserved_prefix = "domain-layer3-incompatible:"
    private_fields = {
        "candidate_layer3_context",
        "eligible_foundation_layer3_skills",
        "eligible_domain_layer3_skills",
        "eligible_layer3_skills",
        "reserved_domain_capacity",
        "layer3_overflow",
        "source_candidate_ids",
        *ROUTE_CANDIDATE_CONTRACT_FIELDS,
    }

    def sanitized(candidate: dict[str, Any]) -> dict[str, Any]:
        copied = copy.deepcopy(candidate)
        for field in private_fields:
            copied.pop(field, None)
        evidence = copied.get("evidence")
        if isinstance(evidence, list):
            copied["evidence"] = [
                item
                for item in evidence
                if not (
                    isinstance(item, str)
                    and item.startswith(reserved_prefix)
                )
            ]
        if copied.get("reason") == reserved_reason:
            copied.pop("reason")
        return copied

    raw = [sanitized(candidate) for candidate in raw_candidates]
    routes = [sanitized(candidate) for candidate in route_candidates]
    if admission_authority is not None:
        for candidate in raw:
            candidate_id = candidate.get("candidate_id")
            foundations = (
                list(candidate.get("layer3_skills", []))
                if (
                    isinstance(candidate_id, str)
                    and candidate_id.startswith("implementation-owner:")
                )
                else []
            )
            if foundations:
                _bind_foundation_candidate(
                    candidate,
                    foundations,
                    admission_authority=admission_authority,
                )
    risks = [
        candidate
        for candidate in raw
        if candidate.get("candidate_id") in REVIEW_RISK_PRIMARY
    ]
    owners = [
        candidate
        for candidate in raw
        if isinstance(candidate.get("candidate_id"), str)
        and candidate["candidate_id"].startswith("implementation-owner:")
    ]
    support_foundations = list(
        dict.fromkeys(
            skill
            for candidate in routes
            for skill in candidate.get("layer3_skills", [])
            if skill not in domain_specs and skill != "regression-testing"
        )
    )
    if _accessibility_behavior_requested(normalized_text):
        support_foundations.append("accessibility-inclusive-design")
        support_foundations = list(dict.fromkeys(support_foundations))
    support_rule_ids = [
        candidate["candidate_id"]
        for candidate in routes
        if candidate.get("layer3_skills")
    ]
    review_regression = any(
        "review-regression-tests" in candidate.get("evidence", [])
        for candidate in raw
    )
    repeated_failure_subject = any(
        subject in normalized_text
        for subject in (
            "same path",
            "same repair path",
            "same cause",
            "same patch shape",
            "same validator",
        )
    )
    repeat_failure = (
        "failed twice" in normalized_text and repeated_failure_subject
    ) or all(
        signal in normalized_text
        for signal in ("repair repeats", "contradicted", "evidence")
    )
    owner_internal_refactor = "owner-internal refactor" in normalized_text

    materialized: list[dict[str, Any]] = []
    for candidate in [*raw, *routes]:
        candidate_id = candidate.get("candidate_id")
        evidence = candidate.get("evidence", [])
        automatic_owner = (
            isinstance(candidate_id, str)
            and candidate_id.startswith("implementation-owner:")
        )
        if automatic_owner:
            foundations = list(candidate.get("layer3_skills", []))
            candidate.update(
                {
                    "candidate_type": "automatic-implementation-owner",
                    "precedence": 4,
                    "path": implementation_policy["accepted"]["path"],
                    "profile": implementation_policy["accepted"]["profile"],
                    "layer3_skills": [*domain_requests, *foundations],
                    "candidate_layer3_context": {
                        "kind": "fixed",
                        "foundation_requests": foundations,
                        "domain_requests": list(domain_requests),
                    },
                }
            )
        elif candidate_id == "critical-unknown":
            critical_foundations = ["repository-context-map"]
            if (
                "critical-owner-unknown" in evidence
                and _configuration_runtime_policy_risk(normalized_text)
            ):
                critical_foundations.append(
                    "configuration-runtime-policy"
                )
            candidate.update(
                {
                    "candidate_type": "converted-cohort",
                    "precedence": ROUTE_COHORT_PRECEDENCE[candidate_id],
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": [
                        *domain_requests,
                        *critical_foundations,
                    ],
                    "review_skill": "architecture-impact-reviewer",
                    "rule_id": "critical-unknown-candidate",
                    "stage": "critical-unknown",
                    "precedence_class": "critical-boundary",
                    "candidate_layer3_context": {
                        "kind": "fixed",
                        "foundation_requests": critical_foundations,
                        "domain_requests": list(domain_requests),
                    },
                }
            )
        elif candidate_id == "ordinary-ambiguity":
            ordinary_foundations = ["repository-context-map"]
            candidate.update(
                {
                    "candidate_type": "converted-cohort",
                    "precedence": ROUTE_COHORT_PRECEDENCE[candidate_id],
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": [
                        *domain_requests,
                        *ordinary_foundations,
                    ],
                    "review_skill": "architecture-impact-reviewer",
                    "rule_id": "ordinary-ambiguity-candidate",
                    "stage": "proof-limit",
                    "precedence_class": "unresolved-boundary",
                    "candidate_layer3_context": {
                        "kind": "fixed",
                        "foundation_requests": ordinary_foundations,
                        "domain_requests": list(domain_requests),
                    },
                }
            )
        elif candidate_id == "implementation-preparation":
            if len(risks) > 1:
                raise RoutingIntegrityError(
                    "implementation preparation cannot contain multiple "
                    "material review risks"
                )
            risk = risks[0] if risks else None
            owner_context = [
                {
                    "candidate_id": owner["candidate_id"],
                    "routing_family": owner.get("routing_family"),
                    "primary_skill": owner.get("primary_skill"),
                    "foundation_requests": list(
                        owner.get("layer3_skills", [])
                    ),
                    "review_skill": owner.get("review_skill"),
                    "evidence": list(owner.get("evidence", [])),
                }
                for owner in owners
            ]
            risk_context = (
                {
                    "candidate_id": risk["candidate_id"],
                    "evidence": list(risk.get("evidence", [])),
                    "foundation_requests": _review_risk_layer3(
                        risk["candidate_id"],
                        risk.get("evidence", []),
                    ),
                    "review_skill": REVIEW_RISK_PRIMARY[
                        risk["candidate_id"]
                    ],
                }
                if risk is not None
                else None
            )
            if risk_context is not None:
                foundations = list(risk_context["foundation_requests"])
                review_skill = risk_context["review_skill"]
            elif len(owner_context) == 1:
                foundations = list(
                    owner_context[0]["foundation_requests"]
                )
                review_skill = owner_context[0]["review_skill"]
            else:
                foundations = list(support_foundations)
                review_skill = "architecture-impact-reviewer"
            if not foundations:
                foundations = ["repository-context-map"]
            candidate.update(
                {
                    "candidate_type": "converted-cohort",
                    "precedence": ROUTE_COHORT_PRECEDENCE[candidate_id],
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "engineering-change-analysis",
                    "layer3_skills": [*domain_requests, *foundations],
                    "review_skill": review_skill,
                    "rule_id": "implementation-preparation-candidate",
                    "stage": "preparation",
                    "precedence_class": "task-phase",
                    "candidate_layer3_context": {
                        "kind": "preparation",
                        "domain_requests": list(domain_requests),
                        "risk": risk_context,
                        "owners": owner_context,
                        "support_foundations": list(support_foundations),
                        "support_rule_ids": list(support_rule_ids),
                    },
                }
            )
        elif candidate_id == "review-generic":
            foundations = list(support_foundations)
            if repeat_failure:
                foundations = ["repeat-failure-analysis"]
            elif owner_internal_refactor:
                foundations = ["refactoring"]
            elif review_regression:
                foundations.append("regression-testing")
            foundations = list(dict.fromkeys(foundations)) or ["code-review"]
            candidate.update(
                {
                    "candidate_type": "converted-cohort",
                    "precedence": ROUTE_COHORT_PRECEDENCE[candidate_id],
                    "path": "direct",
                    "profile": "review-agent",
                    "primary_skill": "ai-code-review-refactor",
                    "layer3_skills": [*domain_requests, *foundations],
                    "review_skill": "ai-code-review-refactor",
                    "rule_id": "review-generic-candidate",
                    "stage": "review",
                    "precedence_class": "review-default",
                    "candidate_layer3_context": {
                        "kind": "review-generic",
                        "domain_requests": list(domain_requests),
                        "support_foundations": list(support_foundations),
                        "review_regression": review_regression,
                        "repeat_failure": repeat_failure,
                        "owner_internal_refactor": owner_internal_refactor,
                    },
                }
            )
        elif candidate_id in REVIEW_RISK_PRIMARY:
            risk_foundations = _review_risk_layer3(
                candidate_id,
                evidence,
            )
            risk_support = [
                skill
                for skill in support_foundations
                if skill not in risk_foundations
            ]
            foundations = [
                *risk_foundations,
                *risk_support,
                *(
                    ["regression-testing"]
                    if review_regression
                    else []
                ),
            ]
            foundations = list(dict.fromkeys(foundations))
            primary = REVIEW_RISK_PRIMARY[candidate_id]
            candidate.update(
                {
                    "candidate_type": "converted-cohort",
                    "precedence": ROUTE_COHORT_PRECEDENCE[candidate_id],
                    "path": "direct",
                    "profile": "review-agent",
                    "primary_skill": primary,
                    "layer3_skills": [*domain_requests, *foundations],
                    "review_skill": primary,
                    "rule_id": f"{candidate_id}-candidate",
                    "stage": "review",
                    "precedence_class": "review-risk",
                    "candidate_layer3_context": {
                        "kind": "review-risk",
                        "domain_requests": list(domain_requests),
                        "risk_candidate_id": candidate_id,
                        "risk_evidence": list(evidence),
                        "risk_foundations": risk_foundations,
                        "support_foundations": risk_support,
                        "review_regression": review_regression,
                    },
                }
            )
        else:
            foundations = [
                skill
                for skill in candidate.get("layer3_skills", [])
                if skill not in domain_specs
            ]
            candidate["layer3_skills"] = [
                *domain_requests,
                *foundations,
            ]
            candidate["candidate_layer3_context"] = {
                "kind": "fixed",
                "foundation_requests": foundations,
                "domain_requests": list(domain_requests),
            }
        if admission_authority is not None:
            foundation_payload = [
                skill
                for skill in candidate.get("layer3_skills", [])
                if skill not in domain_specs
            ]
            if (
                foundation_payload
                and candidate.get("candidate_id")
                not in {
                    "implementation-preparation",
                    "review-generic",
                    *REVIEW_RISK_PRIMARY,
                }
            ):
                _bind_foundation_candidate(
                    candidate,
                    foundation_payload,
                    admission_authority=admission_authority,
                )
        materialized.append(candidate)
    return materialized


def _enrich_route_candidates(
    candidates: list[dict[str, Any]],
    *,
    domain_specs: dict[str, dict[str, Any]],
    domain_authority: dict[str, Any],
    layer3_authority_by_primary: dict[str, list[str]],
    maximum_layer3: int,
    admission_authority: OracleAdmissionAuthority | None = None,
) -> list[dict[str, Any]]:
    if not isinstance(candidates, list):
        raise RoutingIntegrityError(
            "route candidate enrichment requires a candidate list"
        )

    context_schemas = {
        "fixed": {
            "kind",
            "foundation_requests",
            "domain_requests",
        },
        "preparation": {
            "kind",
            "domain_requests",
            "risk",
            "owners",
            "support_foundations",
            "support_rule_ids",
        },
        "review-generic": {
            "kind",
            "domain_requests",
            "support_foundations",
            "review_regression",
            "repeat_failure",
            "owner_internal_refactor",
        },
        "review-risk": {
            "kind",
            "domain_requests",
            "risk_candidate_id",
            "risk_evidence",
            "risk_foundations",
            "support_foundations",
            "review_regression",
        },
    }
    contextual_candidates: list[
        tuple[dict[str, Any], dict[str, Any]]
    ] = []
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            raise RoutingIntegrityError(
                f"route candidate {index} must be an object"
            )
        if "candidate_layer3_context" not in candidate:
            continue
        context = candidate["candidate_layer3_context"]
        kind = context.get("kind") if isinstance(context, dict) else None
        if (
            not isinstance(context, dict)
            or kind not in context_schemas
            or set(context) != context_schemas[kind]
        ):
            raise RoutingIntegrityError(
                f"route candidate {index} must use one closed Layer 3 context"
            )
        contextual_candidates.append((candidate, context))

    if not contextual_candidates:
        return candidates

    if (
        not isinstance(domain_specs, dict)
        or not domain_specs
        or any(
            not isinstance(name, str)
            or not name.strip()
            or name != name.strip()
            or not isinstance(spec, dict)
            for name, spec in domain_specs.items()
        )
    ):
        raise RoutingIntegrityError(
            "Domain route specs must map non-empty Skill names to objects"
        )
    authority_fields = {
        "domain_order",
        "domains_by_name",
        "domains_by_professional",
        "edge_count",
    }
    if (
        not isinstance(domain_authority, dict)
        or set(domain_authority) != authority_fields
    ):
        raise RoutingIntegrityError(
            "Domain modifier authority must use the closed routing schema"
        )
    domain_order = domain_authority["domain_order"]
    domains_by_name = domain_authority["domains_by_name"]
    domains_by_professional = domain_authority[
        "domains_by_professional"
    ]
    edge_count = domain_authority["edge_count"]
    if (
        not isinstance(domain_order, list)
        or not domain_order
        or any(
            not isinstance(name, str)
            or not name.strip()
            or name != name.strip()
            for name in domain_order
        )
        or len(domain_order) != len(set(domain_order))
        or list(domain_specs) != domain_order
    ):
        raise RoutingIntegrityError(
            "Domain modifier authority must preserve the unique registry order"
        )
    if (
        not isinstance(domains_by_name, dict)
        or list(domains_by_name) != domain_order
        or not isinstance(domains_by_professional, dict)
        or any(
            not isinstance(owner, str)
            or not owner.strip()
            or owner != owner.strip()
            for owner in domains_by_professional
        )
        or type(edge_count) is not int
        or edge_count < 0
    ):
        raise RoutingIntegrityError(
            "Domain modifier authority has an invalid ownership projection"
        )

    supported_profiles = {
        "analysis-agent",
        "task-agent",
        "review-agent",
    }
    owners_by_domain: dict[str, list[str]] = {}
    roles_by_domain: dict[str, list[str]] = {}
    for domain in domain_order:
        entry = domains_by_name.get(domain)
        owners = entry.get("used_by") if isinstance(entry, dict) else None
        roles = (
            entry.get("role_support")
            if isinstance(entry, dict)
            else None
        )
        if (
            not isinstance(entry, dict)
            or entry.get("name") != domain
            or entry.get("routing_mode")
            != DOMAIN_MODIFIER_ONLY_ROUTING_MODE
            or not isinstance(owners, list)
            or not owners
            or any(
                not isinstance(owner, str)
                or not owner.strip()
                or owner != owner.strip()
                for owner in owners
            )
            or len(owners) != len(set(owners))
            or owners != sorted(owners)
            or not isinstance(roles, list)
            or not roles
            or any(role not in supported_profiles for role in roles)
            or len(roles) != len(set(roles))
        ):
            raise RoutingIntegrityError(
                f"Domain modifier authority has an invalid {domain!r} entry"
            )
        owners_by_domain[domain] = owners
        roles_by_domain[domain] = roles

    projected_edges = 0
    for owner, declared_domains in domains_by_professional.items():
        if (
            not isinstance(declared_domains, list)
            or any(
                not isinstance(domain, str)
                or domain not in domains_by_name
                for domain in declared_domains
            )
            or len(declared_domains) != len(set(declared_domains))
        ):
            raise RoutingIntegrityError(
                f"Domain modifier authority has invalid edges for {owner!r}"
            )
        expected_domains = [
            domain
            for domain in domain_order
            if owner in owners_by_domain[domain]
        ]
        if declared_domains != expected_domains:
            raise RoutingIntegrityError(
                f"Domain modifier reciprocity differs for {owner!r}"
            )
        projected_edges += len(declared_domains)
    if (
        any(
            owner not in domains_by_professional
            for owners in owners_by_domain.values()
            for owner in owners
        )
        or edge_count != projected_edges
    ):
        raise RoutingIntegrityError(
            "Domain modifier authority edge count or ownership is incomplete"
        )

    if (
        not isinstance(layer3_authority_by_primary, dict)
        or not layer3_authority_by_primary
        or any(
            not isinstance(primary, str)
            or not primary.strip()
            or primary != primary.strip()
            or not isinstance(declared, list)
            or any(
                not isinstance(skill, str)
                or not skill.strip()
                or skill != skill.strip()
                for skill in declared
            )
            or len(declared) != len(set(declared))
            for primary, declared in layer3_authority_by_primary.items()
        )
    ):
        raise RoutingIntegrityError(
            "Professional Layer 3 authority must map owners to unique Skill lists"
        )
    if type(maximum_layer3) is not int or maximum_layer3 <= 0:
        raise RoutingIntegrityError(
            "maximum Layer 3 capacity must be a positive integer"
        )

    domain_names = set(domain_order)
    reserved_prefix = "domain-layer3-incompatible:"
    plans: list[tuple[dict[str, Any], dict[str, Any]]] = []
    def unique_text_list(value: object, *, label: str) -> list[str]:
        if (
            not isinstance(value, list)
            or any(
                not isinstance(item, str)
                or not item.strip()
                or item != item.strip()
                for item in value
            )
            or len(value) != len(set(value))
        ):
            raise RoutingIntegrityError(
                f"{label} must contain unique non-empty trimmed text"
            )
        return value

    def nonempty_text(value: object, *, label: str) -> str:
        if (
            not isinstance(value, str)
            or not value.strip()
            or value != value.strip()
        ):
            raise RoutingIntegrityError(
                f"{label} must be non-empty trimmed text"
            )
        return value

    for candidate, context in contextual_candidates:
        primary = candidate.get("primary_skill")
        profile = candidate.get("profile")
        if (
            not isinstance(primary, str)
            or not primary.strip()
            or primary != primary.strip()
            or primary not in layer3_authority_by_primary
            or primary not in domains_by_professional
        ):
            raise RoutingIntegrityError(
                f"Layer 3 candidate has unknown Professional {primary!r}"
            )
        if profile not in supported_profiles:
            raise RoutingIntegrityError(
                f"Layer 3 candidate has invalid profile {profile!r}"
            )

        kind = context["kind"]
        domains = unique_text_list(
            context["domain_requests"],
            label=f"{kind} domain_requests",
        )
        unknown_domains = sorted(set(domains) - domain_names)
        if unknown_domains:
            raise RoutingIntegrityError(
                f"{kind} Layer 3 context names unknown Domain Skills: "
                f"{unknown_domains!r}"
            )
        expected_domain_order = [
            domain for domain in domain_order if domain in set(domains)
        ]
        if kind != "fixed" and domains != expected_domain_order:
            raise RoutingIntegrityError(
                f"{kind} Domain requests must preserve registry order"
            )

        raw_foundations: list[str]
        review_skill = candidate.get("review_skill")
        if kind == "fixed":
            raw_foundations = unique_text_list(
                context["foundation_requests"],
                label="fixed foundation_requests",
            )
        elif kind == "preparation":
            risk = context["risk"]
            owners = context["owners"]
            support = unique_text_list(
                context["support_foundations"],
                label="preparation support_foundations",
            )
            unique_text_list(
                context["support_rule_ids"],
                label="preparation support_rule_ids",
            )
            if not isinstance(owners, list):
                raise RoutingIntegrityError(
                    "preparation owners must be a list"
                )
            validated_owners: list[dict[str, Any]] = []
            owner_identities: list[tuple[str, str]] = []
            owner_fields = {
                "candidate_id",
                "routing_family",
                "primary_skill",
                "foundation_requests",
                "review_skill",
                "evidence",
            }
            for owner in owners:
                if not isinstance(owner, dict) or set(owner) != owner_fields:
                    raise RoutingIntegrityError(
                        "preparation owner must use the closed owner schema"
                    )
                owner_primary = nonempty_text(
                    owner["primary_skill"],
                    label="preparation owner primary_skill",
                )
                owner_family = nonempty_text(
                    owner["routing_family"],
                    label="preparation owner routing_family",
                )
                owner_id = nonempty_text(
                    owner["candidate_id"],
                    label="preparation owner candidate_id",
                )
                if owner_id != f"implementation-owner:{owner_primary}":
                    raise RoutingIntegrityError(
                        "preparation owner candidate ID is not canonical"
                    )
                owner_foundations = unique_text_list(
                    owner["foundation_requests"],
                    label="preparation owner foundation_requests",
                )
                unique_text_list(
                    owner["evidence"],
                    label="preparation owner evidence",
                )
                nonempty_text(
                    owner["review_skill"],
                    label="preparation owner review_skill",
                )
                if owner_primary not in layer3_authority_by_primary or any(
                    skill not in layer3_authority_by_primary[owner_primary]
                    or skill in domain_names
                    for skill in owner_foundations
                ):
                    raise RoutingIntegrityError(
                        "preparation owner requested ineligible Foundations"
                    )
                owner_identities.append((owner_family, owner_primary))
                validated_owners.append(owner)
            if (
                len(owner_identities) != len(set(owner_identities))
                or owner_identities != sorted(owner_identities)
            ):
                raise RoutingIntegrityError(
                    "preparation owners must use unique deterministic identity "
                    "order"
                )
            if risk is not None:
                risk_fields = {
                    "candidate_id",
                    "evidence",
                    "foundation_requests",
                    "review_skill",
                }
                if not isinstance(risk, dict) or set(risk) != risk_fields:
                    raise RoutingIntegrityError(
                        "preparation risk must use the closed risk schema"
                    )
                risk_id = nonempty_text(
                    risk["candidate_id"],
                    label="preparation risk candidate_id",
                )
                if risk_id not in REVIEW_RISK_PRIMARY:
                    raise RoutingIntegrityError(
                        "preparation risk candidate is unknown"
                    )
                risk_evidence = unique_text_list(
                    risk["evidence"],
                    label="preparation risk evidence",
                )
                risk_foundations = unique_text_list(
                    risk["foundation_requests"],
                    label="preparation risk foundation_requests",
                )
                expected_risk_foundations = _review_risk_layer3(
                    risk_id,
                    risk_evidence,
                )
                if (
                    risk_foundations != expected_risk_foundations
                    or risk["review_skill"] != REVIEW_RISK_PRIMARY[risk_id]
                ):
                    raise RoutingIntegrityError(
                        "preparation risk contradicts its registered contract"
                    )
                raw_foundations = list(risk_foundations)
                review_skill = risk["review_skill"]
            elif len(validated_owners) == 1:
                raw_foundations = list(
                    validated_owners[0]["foundation_requests"]
                )
                review_skill = validated_owners[0]["review_skill"]
            else:
                raw_foundations = list(support)
                review_skill = "architecture-impact-reviewer"
            if not raw_foundations:
                raw_foundations = ["repository-context-map"]
        elif kind == "review-generic":
            support = unique_text_list(
                context["support_foundations"],
                label="review-generic support_foundations",
            )
            if "regression-testing" in support:
                raise RoutingIntegrityError(
                    "review regression must use its exact boolean flag"
                )
            for flag in (
                "review_regression",
                "repeat_failure",
                "owner_internal_refactor",
            ):
                if type(context[flag]) is not bool:
                    raise RoutingIntegrityError(
                        f"review-generic {flag} must be an exact boolean"
                    )
            if context["repeat_failure"]:
                raw_foundations = ["repeat-failure-analysis"]
            elif context["owner_internal_refactor"]:
                raw_foundations = ["refactoring"]
            else:
                raw_foundations = list(support)
                if context["review_regression"]:
                    raw_foundations.append("regression-testing")
                raw_foundations = list(dict.fromkeys(raw_foundations))
                if not raw_foundations:
                    raw_foundations = ["code-review"]
            review_skill = "ai-code-review-refactor"
        else:
            risk_id = nonempty_text(
                context["risk_candidate_id"],
                label="review-risk risk_candidate_id",
            )
            risk_evidence = unique_text_list(
                context["risk_evidence"],
                label="review-risk risk_evidence",
            )
            risk_foundations = unique_text_list(
                context["risk_foundations"],
                label="review-risk risk_foundations",
            )
            support = unique_text_list(
                context["support_foundations"],
                label="review-risk support_foundations",
            )
            if "regression-testing" in support:
                raise RoutingIntegrityError(
                    "review regression must use its exact boolean flag"
                )
            if type(context["review_regression"]) is not bool:
                raise RoutingIntegrityError(
                    "review-risk review_regression must be an exact boolean"
                )
            if (
                risk_id != candidate.get("candidate_id")
                or risk_id not in REVIEW_RISK_PRIMARY
                or primary != REVIEW_RISK_PRIMARY[risk_id]
                or candidate.get("review_skill")
                != REVIEW_RISK_PRIMARY[risk_id]
                or candidate.get("evidence") != risk_evidence
                or risk_foundations
                != _review_risk_layer3(risk_id, risk_evidence)
            ):
                raise RoutingIntegrityError(
                    "review-risk context contradicts its selected risk"
                )
            raw_foundations = [
                *risk_foundations,
                *support,
                *(
                    ["regression-testing"]
                    if context["review_regression"]
                    else []
                ),
            ]
            raw_foundations = list(dict.fromkeys(raw_foundations))
            review_skill = REVIEW_RISK_PRIMARY[risk_id]

        if set(raw_foundations) & set(domains):
            raise RoutingIntegrityError(
                f"{kind} Foundation and Domain requests must not overlap"
            )

        declared_layer3 = layer3_authority_by_primary[primary]
        incompatible_foundations = [
            skill
            for skill in raw_foundations
            if skill in domain_names or skill not in declared_layer3
        ]
        deferred_foundation_activation_conflict = (
            kind == "fixed"
            and candidate.get("candidate_type") == "explicit-route"
            and isinstance(candidate.get("candidate_id"), str)
            and candidate["candidate_id"].startswith(
                "foundation-activation-"
            )
            and (
                candidate.get("stage") == "foundation-activation"
                or candidate.get("precedence_class")
                == "foundation-activation"
            )
        )
        if (
            kind == "fixed"
            and incompatible_foundations
            and not deferred_foundation_activation_conflict
        ):
            raise RoutingIntegrityError(
                "fixed Layer 3 context names ineligible Foundations: "
                f"{incompatible_foundations!r}"
            )
        foundations = [
            skill
            for skill in raw_foundations
            if skill not in incompatible_foundations
        ]
        if kind == "review-generic" and not foundations:
            fallback_skill = "code-review"
            if fallback_skill not in declared_layer3:
                raise RoutingIntegrityError(
                    "review-generic post-filter fallback "
                    f"{fallback_skill!r} is not authorized for {primary!r}"
                )
            foundations = [fallback_skill]
        unsupported_domains = [
            domain
            for domain in domains
            if profile not in roles_by_domain[domain]
        ]
        if unsupported_domains:
            raise RoutingIntegrityError(
                "fixed Layer 3 Domains do not support the routed profile: "
                f"{unsupported_domains!r}"
            )
        compose_domain_extensions(
            domains,
            registered_domains=domain_order,
            max_domains=len(domain_order),
        )

        evidence = candidate.get("evidence")
        if (
            not isinstance(evidence, list)
            or any(
                not isinstance(item, str)
                or not item.strip()
                or item != item.strip()
                for item in evidence
            )
            or len(evidence) != len(set(evidence))
        ):
            raise RoutingIntegrityError(
                "fixed Layer 3 candidate evidence must contain unique strings"
            )
        if "reason" in candidate and (
            not isinstance(candidate["reason"], str)
            or not candidate["reason"].strip()
            or candidate["reason"] != candidate["reason"].strip()
        ):
            raise RoutingIntegrityError(
                "fixed Layer 3 candidate reason must be non-empty text"
            )

        markers: set[str] = set()
        compatible_domains: list[str] = []
        requested_domain_set = set(domains)
        for domain in domain_order:
            if domain not in requested_domain_set:
                continue
            incompatibilities: list[str] = []
            if domain not in declared_layer3:
                incompatibilities.append("professional-layer3")
            if domain not in domains_by_professional[primary]:
                incompatibilities.append("reciprocity")
            if incompatibilities:
                markers.update(
                    f"{reserved_prefix}{domain}:{reason}"
                    for reason in incompatibilities
                )
            else:
                compatible_domains.append(domain)
        domain_composition = compose_domain_extensions(
            compatible_domains,
            registered_domains=domain_order,
            max_domains=len(domain_order),
        )
        eligible_domains = domain_composition["ordered_domains"]

        eligible_layer3 = [*eligible_domains, *foundations]
        existing_layer3 = candidate.get("layer3_skills")
        if (
            not isinstance(existing_layer3, list)
            or any(
                not isinstance(skill, str)
                or not skill.strip()
                or skill != skill.strip()
                for skill in existing_layer3
            )
            or len(existing_layer3) != len(set(existing_layer3))
        ):
            raise RoutingIntegrityError(
                f"{kind} Layer 3 candidate differs from its request context"
            )
        existing_domains: list[str] = []
        existing_foundations: list[str] = []
        foundation_prefix_started = False
        for skill in existing_layer3:
            if skill in domain_names:
                if foundation_prefix_started:
                    raise RoutingIntegrityError(
                        f"{kind} Layer 3 Domains must form one continuous prefix"
                    )
                existing_domains.append(skill)
            else:
                foundation_prefix_started = True
                existing_foundations.append(skill)
        requested_form = (
            existing_domains == domains
            and existing_foundations == raw_foundations
        )
        final_form = (
            existing_domains == eligible_domains
            and existing_foundations == foundations
        )
        if not requested_form and not final_form:
            raise RoutingIntegrityError(
                f"{kind} Layer 3 candidate differs from its request context"
            )

        generated_markers = [
            marker
            for marker in sorted(markers)
            if marker not in evidence
        ]
        plans.append(
            (
                candidate,
                {
                    "eligible_foundation_layer3_skills": list(foundations),
                    "eligible_domain_layer3_skills": eligible_domains,
                    "eligible_layer3_skills": eligible_layer3,
                    "reserved_domain_capacity": len(eligible_domains),
                    "layer3_overflow": (
                        len(eligible_layer3) > maximum_layer3
                    ),
                    "layer3_skills": eligible_layer3,
                    "evidence": [
                        *evidence,
                        *generated_markers,
                    ],
                    "review_skill": review_skill,
                },
            )
        )

    for candidate, enrichment in plans:
        candidate.update(enrichment)
        if admission_authority is not None:
            _synchronize_foundation_candidate(
                candidate,
                candidate["eligible_foundation_layer3_skills"],
                admission_authority=admission_authority,
            )
    return candidates


def _compose_foundation_activation_candidates(
    candidates: list[dict[str, Any]],
    *,
    candidate_origins: tuple[_FoundationRouteOrigin | None, ...],
    admission_authority: OracleAdmissionAuthority,
    maximum_layer3: int,
) -> list[dict[str, Any]]:
    """Compose compatible Foundation activations in authority order."""

    if not isinstance(candidates, list):
        raise RoutingIntegrityError(
            "Foundation activation composition requires a candidate list"
        )
    if not isinstance(admission_authority, OracleAdmissionAuthority):
        raise RoutingIntegrityError(
            "Foundation activation composition requires admission authority"
        )
    if (
        not isinstance(candidate_origins, tuple)
        or len(candidate_origins) != len(candidates)
        or any(
            origin is not None
            and not isinstance(origin, _FoundationRouteOrigin)
            for origin in candidate_origins
        )
    ):
        raise RoutingIntegrityError(
            "Foundation activation composition requires aligned classifier "
            "origins"
        )
    registry_activation_ids = [
        record.selector_id
        for record in admission_authority.foundation_selectors
    ]
    records_by_id = {
        record.selector_id: record
        for record in admission_authority.foundation_selectors
    }
    if (
        not isinstance(registry_activation_ids, list)
        or not registry_activation_ids
        or any(
            not isinstance(candidate_id, str)
            or not candidate_id.strip()
            or candidate_id != candidate_id.strip()
            for candidate_id in registry_activation_ids
        )
        or len(registry_activation_ids) != len(set(registry_activation_ids))
    ):
        raise RoutingIntegrityError(
            "Foundation activation IDs must be ordered unique text"
        )
    if type(maximum_layer3) is not int or maximum_layer3 <= 0:
        raise RoutingIntegrityError(
            "Foundation activation composition requires a positive Layer 3 "
            "maximum"
        )

    copied = copy.deepcopy(candidates)
    admitted_foundations = {
        foundation
        for record in admission_authority.foundation_selectors
        for foundation in record.foundations
    }
    for candidate, origin in zip(copied, candidate_origins):
        _validate_foundation_route_origin(candidate, origin)
        eligible_foundations = candidate.get(
            "eligible_foundation_layer3_skills"
        )
        foundations = (
            list(eligible_foundations)
            if isinstance(eligible_foundations, list)
            else [
                skill
                for skill in candidate.get("layer3_skills", [])
                if skill in admitted_foundations
            ]
        )
        if foundations:
            _validate_foundation_candidate(
                candidate,
                foundations,
                admission_authority=admission_authority,
            )
    activation_order = {
        candidate_id: index
        for index, candidate_id in enumerate(registry_activation_ids)
    }
    unknown = [
        candidate.get("candidate_id")
        for candidate in copied
        if (
            candidate.get("stage") == "foundation-activation"
            or candidate.get("precedence_class")
            == "foundation-activation"
        )
        and candidate.get("candidate_id") not in activation_order
    ]
    if unknown:
        raise RoutingIntegrityError(
            "Foundation activation candidates are absent from registry "
            f"authority: {unknown!r}"
        )

    indexed = [
        (index, candidate)
        for index, candidate in enumerate(copied)
        if candidate.get("candidate_id") in activation_order
    ]
    candidate_ids = [
        candidate["candidate_id"]
        for _index, candidate in indexed
    ]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise RoutingIntegrityError(
            "Foundation activation candidates must be unique"
        )
    if len(indexed) <= 1:
        return copied

    ordered = sorted(
        (candidate for _index, candidate in indexed),
        key=lambda candidate: activation_order[candidate["candidate_id"]],
    )
    source_foundation_candidates = []
    for candidate in ordered:
        record = records_by_id[candidate["candidate_id"]]
        if tuple(candidate.get("layer3_skills", [])) != record.foundations:
            raise RoutingIntegrityError(
                f"Foundation candidate {record.selector_id!r} changed identity"
            )
        if not all(
            evidence in candidate.get("evidence", [])
            for evidence in record.evidence_ids
        ):
            raise RoutingIntegrityError(
                f"Foundation candidate {record.selector_id!r} lost evidence"
            )
        source_foundation_candidates.append(
            {
                "candidate_id": record.selector_id,
                "foundations": list(record.foundations),
                "evidence": list(record.evidence_ids),
                "owner_binding": {
                    "primary_skill": candidate.get("primary_skill"),
                    "review_skill": candidate.get("review_skill"),
                },
            }
        )
    comparison_fields = (
        "precedence",
        "path",
        "profile",
        "primary_skill",
        "review_skill",
        "stage",
        "precedence_class",
    )
    comparison_keys = {
        tuple(candidate.get(field) for field in comparison_fields)
        for candidate in ordered
    }

    first_index = min(index for index, _candidate in indexed)
    activation_indexes = {index for index, _candidate in indexed}
    without_activations = [
        candidate
        for index, candidate in enumerate(copied)
        if index not in activation_indexes
    ]

    def insert_at_first(
        replacements: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        before_count = sum(
            index < first_index and index not in activation_indexes
            for index in range(len(copied))
        )
        return [
            *without_activations[:before_count],
            *replacements,
            *without_activations[before_count:],
        ]

    if len(comparison_keys) != 1:
        conflicts = copy.deepcopy(ordered)
        for candidate in conflicts:
            candidate["precedence"] = EXPLICIT_ROUTE_PRECEDENCE
        return insert_at_first(conflicts)

    def ordered_union(field: str) -> list[str]:
        return list(
            dict.fromkeys(
                item
                for candidate in ordered
                for item in candidate.get(field, [])
            )
        )

    layer3_skills = ordered_union("layer3_skills")
    source_candidate_ids = [
        candidate["candidate_id"]
        for candidate in ordered
    ]
    if len(layer3_skills) > maximum_layer3:
        overflow = {
            "candidate_id": "foundation-layer3-overflow",
            "candidate_type": "explicit-route",
            "evidence": [
                *list(
                    dict.fromkeys(
                        evidence
                        for row in source_foundation_candidates
                        for evidence in row["evidence"]
                    )
                ),
                "foundation-layer3-overflow",
            ],
            "source_candidate_ids": source_candidate_ids,
            "source_foundation_candidates": source_foundation_candidates,
            "precedence": EXPLICIT_ROUTE_PRECEDENCE,
            "reason": "foundation-layer3-overflow",
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
            "rule_id": "foundation-layer3-overflow",
            "stage": "foundation-activation",
            "precedence_class": "layer-budget",
            "candidate_layer3_context": {
                "kind": "fixed",
                "foundation_requests": ["repository-context-map"],
                "domain_requests": [],
            },
            "eligible_foundation_layer3_skills": [
                "repository-context-map"
            ],
            "eligible_domain_layer3_skills": [],
            "eligible_layer3_skills": ["repository-context-map"],
            "reserved_domain_capacity": 0,
            "layer3_overflow": True,
        }
        return insert_at_first([overflow])

    composite = copy.deepcopy(ordered[0])
    composite.update(
        {
            "candidate_id": "foundation-activation-composite",
            "candidate_type": "explicit-route",
            "evidence": ordered_union("evidence"),
            "source_candidate_ids": source_candidate_ids,
            "source_foundation_candidates": source_foundation_candidates,
            "layer3_skills": layer3_skills,
            "rule_id": "foundation-activation-composite",
            "semantic_atoms": ordered_union("semantic_atoms"),
            "eligible_foundation_layer3_skills": ordered_union(
                "eligible_foundation_layer3_skills"
            ),
            "eligible_domain_layer3_skills": ordered_union(
                "eligible_domain_layer3_skills"
            ),
            "eligible_layer3_skills": ordered_union(
                "eligible_layer3_skills"
            ),
            "reserved_domain_capacity": len(
                ordered_union("eligible_domain_layer3_skills")
            ),
            "layer3_overflow": False,
        }
    )
    contexts = [
        candidate.get("candidate_layer3_context")
        for candidate in ordered
    ]
    if all(
        isinstance(context, dict)
        and context.get("kind") == "fixed"
        for context in contexts
    ):
        composite["candidate_layer3_context"] = {
            "kind": "fixed",
            "foundation_requests": list(
                dict.fromkeys(
                    item
                    for context in contexts
                    for item in context["foundation_requests"]
                )
            ),
            "domain_requests": list(
                dict.fromkeys(
                    item
                    for context in contexts
                    for item in context["domain_requests"]
                )
            ),
        }
    return insert_at_first([composite])


def _project_route_selection(
    projector: Any,
    cohort_selection: dict[str, Any],
) -> dict[str, Any]:
    """Invoke the sole final route projector."""

    return projector(cohort_selection)


def route_once_pipeline_errors(
    source_text: str | None = None,
    eval_source_text: str | None = None,
) -> list[str]:
    """Reject a second route-once stage or public-wrapper pipeline call."""

    source = (
        Path(__file__).read_text(encoding="utf-8")
        if source_text is None
        else source_text
    )
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [f"route-once source is invalid: {exc}"]
    function_nodes = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    ]
    route_impls = [
        node for node in function_nodes if node.name == "_route_impl"
    ]
    if len(route_impls) != 1:
        return [
            "route-once source must contain exactly one _route_impl, "
            f"found {len(route_impls)}"
        ]
    route_impl = route_impls[0]
    expected_stage_calls = (
        "_normalize_route_prompt",
        "_build_route_candidates",
        "_enrich_route_candidates",
        "_compose_foundation_activation_candidates",
        "_select_route_cohort_candidate",
        "_project_route_selection",
        "validate_route_decision",
    )
    errors: list[str] = []
    for stage in expected_stage_calls:
        count = sum(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == stage
            for node in ast.walk(route_impl)
        )
        if count != 1:
            errors.append(
                f"_route_impl must call {stage} exactly once, found {count}"
            )
    stage_lines = [
        (
            node.lineno,
            node.func.id,
        )
        for node in ast.walk(route_impl)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in expected_stage_calls
    ]
    if (
        len(stage_lines) == len(expected_stage_calls)
        and tuple(
            name for _line, name in sorted(stage_lines)
        )
        != expected_stage_calls
    ):
        errors.append(
            "_route_impl route-once stages must preserve canonical order"
        )
    for public_name in ("route", "route_with_trace"):
        matches = [
            node for node in function_nodes if node.name == public_name
        ]
        if len(matches) != 1:
            errors.append(
                f"route-once source must contain exactly one {public_name}, "
                f"found {len(matches)}"
            )
            continue
        function = matches[0]
        count = sum(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_route_impl"
            for node in ast.walk(function)
        )
        if count != 1:
            errors.append(
                f"{public_name} must call _route_impl exactly once, found {count}"
            )

    eval_source = (
        (ROOT / "scripts" / "eval-routing.py").read_text(encoding="utf-8")
        if eval_source_text is None
        else eval_source_text
    )
    try:
        eval_tree = ast.parse(eval_source)
    except SyntaxError as exc:
        errors.append(f"eval route wrapper source is invalid: {exc}")
        return errors
    eval_routes = [
        node
        for node in eval_tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "route"
    ]
    if len(eval_routes) != 1:
        errors.append(
            "eval route wrapper source must contain exactly one route, "
            f"found {len(eval_routes)}"
        )
    else:
        canonical_calls = sum(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "canonical_route"
            for node in ast.walk(eval_routes[0])
        )
        if canonical_calls != 1:
            errors.append(
                "eval route wrapper must call canonical_route exactly once, "
                f"found {canonical_calls}"
            )
    return errors


def compose_domain_extensions(
    candidates: list[str] | tuple[str, ...],
    *,
    registered_domains: list[str] | tuple[str, ...],
    modifier_domains: set[str] | frozenset[str] = frozenset(
        {CROSS_PLATFORM_MODIFIER}
    ),
    concrete_platform_domains: set[str] | frozenset[str] = frozenset(
        CONCRETE_CLIENT_PLATFORM_ORDER
    ),
    max_domains: int = 3,
) -> dict[str, Any]:
    """Return one ordered, bounded Domain composition or fail closed."""

    if not isinstance(registered_domains, (list, tuple)):
        raise RoutingIntegrityError(
            "Domain registry order must be an ordered list or tuple"
        )
    registry_order = list(registered_domains)
    if (
        not registry_order
        or any(
            not isinstance(name, str) or not name.strip()
            for name in registry_order
        )
        or len(registry_order) != len(set(registry_order))
    ):
        raise RoutingIntegrityError(
            "Domain registry order must contain unique non-empty Skill names"
        )
    registered = set(registry_order)
    modifiers = set(modifier_domains)
    concrete = set(concrete_platform_domains)
    supplied = list(candidates)
    if any(
        not isinstance(name, str) or not name.strip()
        for name in supplied
    ):
        raise RoutingIntegrityError(
            f"Domain modifier candidates must be non-empty Skill names: {supplied!r}"
        )
    if len(supplied) != len(set(supplied)):
        raise RoutingIntegrityError(
            f"duplicate Domain modifier candidates are invalid: {supplied!r}"
        )
    unknown = sorted(set(supplied) - registered)
    if unknown:
        raise RoutingIntegrityError(
            f"unregistered Domain modifier candidates are invalid: {unknown!r}"
        )
    selected_modifiers = [name for name in supplied if name in modifiers]
    selected_concrete = [name for name in supplied if name in concrete]
    if selected_modifiers and not selected_concrete:
        raise RoutingIntegrityError(
            "cross-platform Domain modifier requires at least one concrete "
            "platform modifier"
        )
    registry_index = {
        name: index for index, name in enumerate(registry_order)
    }
    ordered = sorted(supplied, key=registry_index.__getitem__)
    if CROSS_PLATFORM_MODIFIER in ordered:
        ordered.remove(CROSS_PLATFORM_MODIFIER)
        first_concrete = next(
            index
            for index, name in enumerate(ordered)
            if name in concrete
        )
        ordered.insert(first_concrete, CROSS_PLATFORM_MODIFIER)
    if len(ordered) > max_domains:
        raise RoutingIntegrityError(
            f"Domain modifier budget exceeded: {ordered!r}"
        )
    return {
        "outcome": "selected",
        "ordered_domains": ordered,
        "candidate_domains": ordered,
        "reasons": [],
        "unknown_domains": [],
    }


def _validated_domain_classifier_snapshot(
    candidates: object,
    *,
    domain_specs: dict[str, dict[str, Any]],
) -> list[str]:
    """Validate one complete classifier snapshot without mutating it."""

    if (
        not isinstance(domain_specs, dict)
        or not domain_specs
        or any(
            not isinstance(skill, str)
            or not skill.strip()
            or skill != skill.strip()
            or not isinstance(spec, dict)
            or not isinstance(spec.get("families"), dict)
            or not spec["families"]
            or any(
                not isinstance(family, str)
                or not family.strip()
                or family != family.strip()
                or not isinstance(contract, dict)
                for family, contract in spec["families"].items()
            )
            for skill, spec in domain_specs.items()
        )
    ):
        raise RoutingIntegrityError(
            "Domain classifier specs must use ordered Skills with family objects"
        )
    domain_order = list(domain_specs)
    if not isinstance(candidates, list):
        raise RoutingIntegrityError(
            "Domain modifier candidate snapshot must be a list"
        )
    if len(candidates) != len(domain_order):
        raise RoutingIntegrityError(
            "Domain modifier candidate snapshot must cover every registered Domain"
        )
    seen: set[str] = set()
    selected: set[str] = set()
    for index, row in enumerate(candidates):
        context = f"Domain modifier candidate snapshot row {index}"
        if not isinstance(row, dict) or set(row) != DOMAIN_CLASSIFIER_FIELDS:
            raise RoutingIntegrityError(
                f"{context} must use the closed classifier schema"
            )
        skill = row["skill"]
        if (
            not isinstance(skill, str)
            or skill not in domain_specs
        ):
            raise RoutingIntegrityError(
                f"{context} names an unknown Domain Skill {skill!r}"
            )
        if skill in seen:
            raise RoutingIntegrityError(
                f"{context} duplicates Domain Skill {skill!r}"
            )
        seen.add(skill)
        eligible = row["eligible"]
        evidence_ids = row["evidence_ids"]
        rejection_reasons = row["rejection_reasons"]
        if type(eligible) is not bool:
            raise RoutingIntegrityError(
                f"{context}.eligible must be an exact bool"
            )
        for field, values in (
            ("evidence_ids", evidence_ids),
            ("rejection_reasons", rejection_reasons),
        ):
            if (
                not isinstance(values, list)
                or any(
                    not isinstance(value, str)
                    or not value.strip()
                    or value != value.strip()
                    for value in values
                )
                or len(values) != len(set(values))
            ):
                raise RoutingIntegrityError(
                    f"{context}.{field} must contain unique non-empty identifiers"
                )
        allowed_evidence = {
            f"domain-family:{family}"
            for family in domain_specs[skill]["families"]
        }
        if skill in CONCRETE_CLIENT_PLATFORM_ORDER:
            allowed_evidence.add("domain-family:concrete-platform-target")
        if not set(evidence_ids).issubset(allowed_evidence):
            raise RoutingIntegrityError(
                f"{context}.evidence_ids contains stale Domain evidence"
            )
        if not set(rejection_reasons).issubset(DOMAIN_REJECTION_REASONS):
            raise RoutingIntegrityError(
                f"{context}.rejection_reasons contains an unknown reason"
            )
        if eligible:
            if not evidence_ids or rejection_reasons:
                raise RoutingIntegrityError(
                    f"{context} eligible result requires evidence and no rejection"
                )
            selected.add(skill)
        elif evidence_ids or not rejection_reasons:
            raise RoutingIntegrityError(
                f"{context} rejected result requires reasons and no evidence"
            )
    if seen != set(domain_order):
        raise RoutingIntegrityError(
            "Domain modifier candidate snapshot is incomplete"
        )
    return [
        domain
        for domain in domain_order
        if domain in selected
    ]


_DOMAIN_CONTRAST_SPLIT_RE = re.compile(
    r"[;.!?]+"
    r"|(?:,\s*|\s+)(?:while|but|although|whereas|yet)\s+"
    r"|,\s+(?!(?:and|or|nor)\b)"
    r"(?=[^,;.!?]{1,96}\b(?:is|are|remain|remains)\s+"
    r"(?:all\s+)?(?:absent|unchanged|the[- ]same)\b)"
)
_WEB3_STRONG_CHAIN_ANCHORS = (
    "blockchain",
    "chain transaction",
    "on-chain",
    "smart contract",
    "smart-contract",
    "cross-chain",
    "bridge",
    "layer 2",
    "governance proposal",
    "oracle feed",
)
_WEB3_CHAIN_QUALIFIERS = ("key", "wallet", "custody", "finality", "reorg")
_PAYMENT_CONTEXT_SIGNALS = (
    "payment",
    "funds",
    "ledger",
    "balance",
    "settlement",
    "accounting",
    "reconciliation",
    "money movement",
    "trade execution",
    "partial fill",
    "market order",
    "venue order",
    "execution state",
)
_BACKEND_IMPLEMENTATION_SURFACE_SIGNALS = (
    "backend",
    "service behavior",
    "service implementation",
    "service lifecycle",
    "worker behavior",
    "worker implementation",
    "linux server",
    "server-side",
    "server side",
    "server behavior",
    "server daemon",
    "server implementation",
    "command-line service",
    "command line service",
    "java jvm service",
    "kotlin coroutine",
    "net service",
    "backend utility",
)
_CLIENT_APPLICATION_SURFACE_SIGNALS = (
    "installed app",
    "installed application",
    "installed client",
    "installed-client",
    "client-side",
    "client side",
    "phone app",
)
_CLIENT_PLATFORM_DOMAIN_SIGNALS = {
    "android-platform-extension": ("android",),
    "ios-ipados-platform-extension": ("ios", "ipados", "iphone", "ipad"),
    "linux-desktop-platform-extension": (
        "linux graphical desktop",
        "linux desktop",
    ),
    "macos-platform-extension": ("macos",),
    "windows-platform-extension": ("windows",),
}
_CLIENT_PLATFORM_MATERIAL_SIGNALS = {
    "android-platform-extension": (
        "accessibility behavior",
        "accessibility focus",
        "application lifecycle",
        "activity",
        "background work",
        "compose semantics",
        "display scaling",
        "font scaling",
        "foreground service",
        "keyboard focus",
        "process recreation",
        "saved-state",
        "saved state",
        "screen",
        "state payload",
        "switch access",
        "talkback",
        "view",
        "voice access",
    ),
    "ios-ipados-platform-extension": (
        "application lifecycle",
        "background task",
        "mobile lifecycle",
        "restoration",
        "scene",
        "state payload",
        "view",
    ),
    "linux-desktop-platform-extension": (
        "d-bus",
        "desktop session",
        "graphical desktop",
        "window",
    ),
    "macos-platform-extension": (
        "appkit",
        "application lifecycle",
        "state payload",
        "swiftui",
        "window",
        "window lifecycle",
        "window-lifecycle",
    ),
    "windows-platform-extension": (
        "application identity",
        "msix",
        "packaged desktop app",
        "packaged desktop application",
        "protocol handler",
        "protocol-handler",
        "state payload",
        "view",
        "window",
    ),
}
_CLIENT_FRAMEWORK_DOMAIN_CONTRACTS = {
    "android-platform-extension": {
        "family": "platform-lifecycle-authority",
        "platform_signals": ("android",),
        "framework_signals": ("jetpack compose",),
    },
    "macos-platform-extension": {
        "family": "platform-lifecycle-authority",
        "platform_signals": ("macos",),
        "framework_signals": ("swiftui",),
    },
    "windows-platform-extension": {
        "family": "application-identity-authority",
        "platform_signals": ("windows",),
        "framework_signals": ("wpf", "winui"),
    },
}
_INSTALLED_CLIENT_PLATFORM_SIGNALS = (
    "android",
    "ios",
    "ipados",
    "windows packaged",
    "windows msix",
    "windows registry",
    "macos",
    "linux desktop",
    "linux graphical desktop",
    "installed application",
    "installed client",
    "installed-client",
    "offline sync",
    "online-only client",
    "process-death",
    "swift actor",
    "flutter",
    "react native",
    "electron",
    "tauri",
    "net maui",
    "kotlin multiplatform",
    "qt graphical",
)
_INSTALLED_CLIENT_SURFACE_SIGNALS = (
    "app",
    "application",
    "activity",
    "back-stack",
    "background task",
    "background work",
    "backgroundtasks",
    "client",
    "desktop",
    "device api",
    "entitlement",
    "lifecycle",
    "manifest",
    "msix",
    "native",
    "offline sync",
    "process-death",
    "registry",
    "restoration",
    "screen",
    "scene",
    "state",
    "swift actor",
    "foreground service",
    "view",
    "voiceover",
    "window",
)


def _contains_signal(text: str, signal: str) -> bool:
    """Match one normalized signal without accepting identifier substrings."""

    pattern = rf"(?<![a-z0-9]){re.escape(signal)}(?![a-z0-9])"
    return re.search(pattern, text) is not None


def _backend_implementation_subject(text: str) -> bool:
    """Recognize an explicit backend/service/server implementation surface."""

    normalized = _normalize_effect_scope(text)
    return (
        _owner_placement_backend_subject(normalized)
        or any(
            _contains_signal(
                normalized,
                _normalize_effect_scope(signal),
            )
            for signal in _BACKEND_IMPLEMENTATION_SURFACE_SIGNALS
        )
    )


def _domain_clauses(text: str) -> tuple[str, ...]:
    """Split one normalized prompt into bounded decision clauses."""

    return tuple(
        clause.strip()
        for clause in _DOMAIN_CONTRAST_SPLIT_RE.split(
            " ".join(text.casefold().split())
        )
        if clause.strip()
    )


def _explicit_absence_or_unchanged(text: str) -> bool:
    """Recognize explicit absence or unchanged-behavior evidence."""

    if re.search(
        r"\b(?:is|are|remain|remains)\s+(?:all\s+)?"
        r"(?:absent|unchanged|the[- ]same)\b",
        text,
    ):
        return True
    if re.search(
        r"\b(?:behaviou?r|boundar(?:y|ies)|state)\b.{0,32}"
        r"\b(?:is|are)\s+(?:absent|unchanged|the[- ]same)\b",
        text,
    ):
        return True
    return re.search(
        r"\b(?:no|without)\b.{0,120}\b(?:behaviou?r(?:\s+changes?)?|"
        r"state(?:\s+changes?)?|boundar(?:y|ies)|model decision|monetary invariant)\b",
        text,
    ) is not None


def _documentation_only(text: str) -> bool:
    """Recognize a copy or documentation action with no behavior change."""

    documentation_change = re.search(
        r"\b(?:edit|implement|migrate|reword|revise|update)\b.{0,120}\b"
        r"(?:copy|documentation|docs|guide|help text|label|wording)\b",
        text,
    )
    documentation_inspection = re.search(
        r"\b(?:(?:only|solely|exclusively|just)\s+"
        r"(?:analyze|inspect|review)\b.{0,120}\b"
        r"(?:documentation|docs|guide)\b|"
        r"(?:analyze|inspect|review)\b.{0,120}\b"
        r"(?:(?:documentation|docs|guide)\b.{0,80}\b"
        r"(?:nam(?:e|es|ing)|only)\b|"
        r"only\b.{0,80}\b(?:documentation|docs|guide)\b))",
        text,
    )
    material_analysis = re.search(
        r"\b(?:analyze|inspect|review)\b.{0,160}\b"
        r"(?:lifecycle|rendering|platform behaviou?r|constraints?)\b",
        text,
    )
    behavior_change = re.search(
        r"\b(?:change|changed|changes|changing|modify|modified|modifies)\b"
        r".{0,80}\b(?:behaviou?r|boundary|rollback|state)\b",
        text,
    )
    return (
        documentation_change is not None
        or documentation_inspection is not None
    ) and material_analysis is None and behavior_change is None


def _explicit_non_domain_change(text: str) -> bool:
    """Recognize an anti-route clause without inspecting unrelated clauses."""

    return _explicit_absence_or_unchanged(text) or _documentation_only(text)


def _client_platform_domain_relevance(
    clause: str,
    domain: str,
    spec: dict[str, Any],
) -> bool:
    """Require scope-local professional relevance for a client Domain."""

    return any(
        _client_platform_domain_scope_relevant(scope, domain, spec)
        for _scope_id, scope in _bounded_effect_scopes(clause)
    )


def _domain_candidate_effect_scope(scope: str, domain: str) -> str:
    """Remove behavior anti qualifiers owned by other platform candidates."""

    candidate_scope = scope
    for platform_domain, platform_signals in (
        _CLIENT_PLATFORM_DOMAIN_SIGNALS.items()
    ):
        if platform_domain == domain:
            continue
        for signal in platform_signals:
            candidate_scope = re.sub(
                rf"\b(?:with\s+)?no\s+{re.escape(signal)}\s+"
                r"behaviou?r\b(?:\s+changes?)?",
                " ",
                candidate_scope,
            )
    return _normalize_effect_scope(candidate_scope)


def _independent_change_scope(scope: str) -> bool:
    """Require a local action or explicit accepted-change semantics."""

    action_intent = _task_action_intent(scope)
    accepted_change = re.search(
        r"\baccepted\b.{0,160}\b(?:change|fix|repair|update)\b",
        scope,
    )
    return (
        not _explicit_non_domain_change(scope)
        and not _scope_is_unchanged(scope)
        and (
            (
                action_intent["implementation"]
                and not action_intent["implementation_ambiguous"]
            )
            or accepted_change is not None
        )
    )


def _client_platform_domain_scope_relevant(
    scope: str,
    domain: str,
    spec: dict[str, Any],
) -> bool:
    """Bind platform and professional material inside one valid scope."""

    candidate_scope = _domain_candidate_effect_scope(scope, domain)
    platform_signals = _CLIENT_PLATFORM_DOMAIN_SIGNALS.get(domain, ())
    material_signals = _CLIENT_PLATFORM_MATERIAL_SIGNALS.get(domain, ())
    framework_signals = frozenset(
        _CLIENT_FRAMEWORK_DOMAIN_CONTRACTS.get(
            domain,
            {},
        ).get("framework_signals", ())
    )
    boundary_signals = tuple(
        signal
        for family, contract in spec.get("families", {}).items()
        if family != "service-lifecycle-authority"
        for signal in contract.get("boundary_signals", ())
    )
    professional_signals = tuple(
        dict.fromkeys(
            signal
            for signal in (*material_signals, *boundary_signals)
            if signal not in framework_signals
        )
    )
    accessibility_behavior = (
        domain == "android-platform-extension"
        and _accessibility_behavior_requested(scope)
    )
    return (
        not _scope_is_unchanged(candidate_scope)
        and not _domain_clause_suppressed(scope, domain, spec)
        and not _backend_implementation_subject(scope)
        and any(
            _contains_signal(scope, signal)
            for signal in platform_signals
        )
        and (
            accessibility_behavior
            or any(
                _contains_signal(scope, signal)
                for signal in professional_signals
            )
        )
    )


def _client_framework_domain_candidates(
    clauses: tuple[str, ...],
    *,
    specs: dict[str, dict[str, Any]],
) -> list[tuple[str, str, str]]:
    """Match platform/framework pairs only with a material client change."""

    candidates: list[tuple[str, str, str]] = []
    for domain, contract in _CLIENT_FRAMEWORK_DOMAIN_CONTRACTS.items():
        spec = specs.get(domain)
        family = contract["family"]
        if (
            not isinstance(spec, dict)
            or family not in spec.get("families", {})
        ):
            continue
        for index, clause in enumerate(clauses):
            if _domain_candidate_suppressed(
                clauses,
                index,
                domain,
                spec,
            ):
                continue
            for _scope_id, scope in _bounded_effect_scopes(clause):
                platform_hit = any(
                    _contains_signal(scope, signal)
                    for signal in contract["platform_signals"]
                )
                framework_hit = any(
                    _contains_signal(scope, signal)
                    for signal in contract["framework_signals"]
                )
                if (
                    platform_hit
                    and framework_hit
                    and _client_platform_domain_scope_relevant(
                        scope,
                        domain,
                        spec,
                    )
                ):
                    candidates.append((domain, family, clause))
    return candidates


def _installed_client_scope_subject(scope: str) -> bool:
    """Recognize one independently changed installed-client scope."""

    normalized_scope = _normalize_effect_scope(scope)
    return (
        any(
            _contains_signal(
                normalized_scope,
                _normalize_effect_scope(signal),
            )
            for signal in _INSTALLED_CLIENT_PLATFORM_SIGNALS
        )
        and any(
            _contains_signal(
                normalized_scope,
                _normalize_effect_scope(signal),
            )
            for signal in _INSTALLED_CLIENT_SURFACE_SIGNALS
        )
    ) or bool(
        _client_framework_domain_candidates(
            (scope,),
            specs=DOMAIN_ROUTE_SPECS,
        )
    )


def _domain_clause_suppressed(
    clause: str,
    domain: str,
    spec: dict[str, Any],
) -> bool:
    """Apply one Domain's declared anti-atoms on the candidate clause."""

    anti_hit = any(
        _contains_signal(clause, atom) for atom in spec.get("anti_atoms", ())
    )
    candidate_clause = _domain_candidate_effect_scope(clause, domain)
    return anti_hit or _explicit_non_domain_change(candidate_clause)


def _domain_subject_hit(clause: str, spec: dict[str, Any]) -> bool:
    """Match Domain-owned nouns in an explicit adjacent unchanged clause."""

    for contract in spec.get("families", {}).values():
        signals = (
            *contract.get("trigger_atoms", ()),
            *contract.get("domain_signals", ()),
            *contract.get("qualified_domain_signals", {}).keys(),
        )
        if any(_contains_signal(clause, signal) for signal in signals):
            return True
    return False


def _domain_adjacent_clause_suppressed(
    clause: str,
    spec: dict[str, Any],
) -> bool:
    """Accept only Domain-specific anti evidence from an adjacent clause."""

    adjacent_evidence = re.sub(
        r"\b(?:no|without(?:\s+(?:a|an|the))?)\s+monetary invariant\b",
        "",
        clause,
        flags=re.IGNORECASE,
    )
    if any(
        _contains_signal(adjacent_evidence, atom)
        for atom in spec.get("anti_atoms", ())
    ):
        return True
    return (
        _explicit_absence_or_unchanged(adjacent_evidence)
        and _domain_subject_hit(adjacent_evidence, spec)
    )


def _domain_candidate_suppressed(
    clauses: tuple[str, ...],
    index: int,
    domain: str,
    spec: dict[str, Any],
) -> bool:
    """Apply local and immediately adjacent anti evidence to one candidate."""

    if _domain_clause_suppressed(clauses[index], domain, spec):
        return True
    adjacent = (
        position
        for position in (index - 1, index + 1)
        if 0 <= position < len(clauses)
    )
    return any(
        _domain_adjacent_clause_suppressed(clauses[position], spec)
        for position in adjacent
    )


def _web3_strong_chain_anchor(clause: str) -> bool:
    """Distinguish chain-bound Web3 authority from ambiguous wallet custody."""

    if any(_contains_signal(clause, signal) for signal in _WEB3_STRONG_CHAIN_ANCHORS):
        return True
    return _contains_signal(clause, "chain") and any(
        _contains_signal(clause, signal) for signal in _WEB3_CHAIN_QUALIFIERS
    )


def _payment_context(clause: str) -> bool:
    """Recognize monetary ownership without treating wallet alone as decisive."""

    return any(
        _contains_signal(clause, signal) for signal in _PAYMENT_CONTEXT_SIGNALS
    )


def _contract_domain_hit(text: str, contract: dict[str, Any]) -> bool:
    """Match direct or context-qualified signals for one Domain family."""

    direct = any(
        _contains_signal(text, signal) for signal in contract["domain_signals"]
    )
    qualified = any(
        _contains_signal(text, signal)
        and any(_contains_signal(text, qualifier) for qualifier in qualifiers)
        for signal, qualifiers in contract.get("qualified_domain_signals", {}).items()
    )
    return direct or qualified


def domain_transition_marker(text: str, domain: str, family: str) -> bool:
    """Prove a transition marker on the same positive Domain clause."""

    spec = ALL_DOMAIN_ROUTE_SPECS.get(domain)
    contract = spec.get("families", {}).get(family) if isinstance(spec, dict) else None
    if not isinstance(contract, dict):
        return False
    clauses = _domain_clauses(text)
    return any(
        _contains_signal(clause, "migrate")
        and _contract_domain_hit(clause, contract)
        and any(
            _contains_signal(clause, signal)
            for signal in contract["boundary_signals"]
        )
        and not _domain_candidate_suppressed(
            clauses,
            index,
            domain,
            spec,
        )
        for index, clause in enumerate(clauses)
    )


def domain_unchanged_marker(text: str, domain: str) -> bool:
    """Prove unchanged, absent, or documentation-only Domain evidence."""

    spec = ALL_DOMAIN_ROUTE_SPECS.get(domain)
    families = spec.get("families", {}) if isinstance(spec, dict) else {}
    clauses = _domain_clauses(text)
    return any(
        _domain_candidate_suppressed(
            clauses,
            index,
            domain,
            spec,
        )
        and any(
            _contract_domain_hit(clause, contract)
            for contract in families.values()
            if isinstance(contract, dict)
        )
        for index, clause in enumerate(clauses)
    )


def _eligible_domain_family_rows(
    text: str,
    *,
    specs: dict[str, dict[str, Any]] | None = None,
) -> list[tuple[str, str, str]]:
    """Return evidence-bound Domain family rows before public projection."""

    candidates: list[tuple[str, str, str]] = []
    clauses = _domain_clauses(text)
    selected_specs = DOMAIN_ROUTE_SPECS if specs is None else specs
    for domain, spec in selected_specs.items():
        for family, contract in spec["families"].items():
            for index, clause in enumerate(clauses):
                accessibility_family = (
                    domain == "android-platform-extension"
                    and family == "accessibility-platform-authority"
                )
                accessibility_behavior = (
                    accessibility_family
                    and _accessibility_behavior_requested(clause)
                )
                domain_hit = (
                    accessibility_behavior
                    and _contains_signal(clause, "android")
                ) or (
                    not accessibility_family
                    and _contract_domain_hit(clause, contract)
                )
                boundary_hit = accessibility_behavior or (
                    not accessibility_family
                    and any(
                        _contains_signal(clause, signal)
                        for signal in contract["boundary_signals"]
                    )
                )
                client_application_family = (
                    domain in CONCRETE_CLIENT_PLATFORM_ORDER
                    and family != "service-lifecycle-authority"
                )
                if (
                    domain_hit
                    and boundary_hit
                    and (
                        not client_application_family
                        or _client_platform_domain_relevance(
                            clause,
                            domain,
                            spec,
                        )
                    )
                    and not _domain_candidate_suppressed(
                        clauses,
                        index,
                        domain,
                        spec,
                    )
                ):
                    candidates.append((domain, family, clause))
    candidates.extend(
        _client_framework_domain_candidates(
            clauses,
            specs=selected_specs,
        )
    )

    eligible = [
        candidate
        for candidate in candidates
        if not (
            candidate[0] == "web3-product-extension"
            and _payment_context(candidate[2])
            and not _web3_strong_chain_anchor(candidate[2])
        )
    ]
    strong_web3_clauses = {
        clause
        for domain, _family, clause in eligible
        if domain == "web3-product-extension"
        and _web3_strong_chain_anchor(clause)
    }
    eligible = [
        candidate
        for candidate in eligible
        if not (
            candidate[0] == "payment-trading-extension"
            and candidate[2] in strong_web3_clauses
            and not _payment_context(candidate[2])
        )
    ]
    return list(dict.fromkeys(eligible))


def _classify_domain_modifier_snapshot(
    text: str,
    *,
    specs: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Classify every Domain from co-located semantic boundary evidence."""

    selected_specs = DOMAIN_ROUTE_SPECS if specs is None else specs
    normalized_text = " ".join(text.casefold().split())
    clauses = _domain_clauses(normalized_text)
    eligible_rows = _eligible_domain_family_rows(
        normalized_text,
        specs=selected_specs,
    )
    selected_families = {
        domain: [
            family
            for matched_domain, family, _clause in eligible_rows
            if matched_domain == domain
        ]
        for domain in selected_specs
    }
    concrete_targets = (
        [
            domain
            for domain in _installed_target_domains(normalized_text)
            if not domain_unchanged_marker(normalized_text, domain)
        ]
        if (
            not _platform_target_unknown(normalized_text)
            and any(
                marker in normalized_text
                for marker in (
                    "concrete platform target",
                    "release target",
                    "target platform",
                    "targeting ",
                )
            )
        )
        else []
    )
    for domain in concrete_targets:
        selected_families[domain].append("concrete-platform-target")
    if (
        concrete_targets
        and _shared_client_framework(normalized_text)
        and not domain_unchanged_marker(
            normalized_text,
            CROSS_PLATFORM_MODIFIER,
        )
    ):
        selected_families[CROSS_PLATFORM_MODIFIER].append(
            "shared-target-ownership"
        )
    concrete = {
        domain
        for domain in CONCRETE_CLIENT_PLATFORM_ORDER
        if selected_families.get(domain)
    }
    rows: list[dict[str, Any]] = []
    for domain, spec in selected_specs.items():
        families = selected_families[domain]
        reasons: list[str] = []
        if domain == CROSS_PLATFORM_MODIFIER and families and not concrete:
            families = []
            reasons.append("concrete-platform-evidence-missing")
        if not families and not reasons:
            domain_hit = any(
                _contract_domain_hit(clause, contract)
                for contract in spec["families"].values()
                for clause in clauses
            )
            boundary_hit = any(
                _contract_domain_hit(clause, contract)
                and any(
                    _contains_signal(clause, signal)
                    for signal in contract["boundary_signals"]
                )
                for contract in spec["families"].values()
                for clause in clauses
            )
            if domain_unchanged_marker(normalized_text, domain):
                reasons.append("unchanged-or-anti-trigger")
            elif domain_hit and not boundary_hit:
                reasons.append("boundary-evidence-missing")
            elif boundary_hit:
                reasons.append("conflicting-domain-evidence")
            else:
                reasons.append("domain-evidence-missing")
        rows.append(
            {
                "skill": domain,
                "eligible": bool(families),
                "evidence_ids": [
                    f"domain-family:{family}"
                    for family in dict.fromkeys(families)
                ],
                "rejection_reasons": reasons,
            }
        )
    return rows


def classify_domain_modifiers(
    text: str,
    *,
    specs: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return the public closed Domain modifier candidate snapshot."""

    return _classify_domain_modifier_snapshot(text, specs=specs)


def domain_route_families(
    text: str,
    *,
    specs: dict[str, dict[str, Any]] | None = None,
) -> list[tuple[str, str]]:
    """Return ordered evidence-bound Domain matches for fixture annotations."""

    return list(
        dict.fromkeys(
            (domain, family)
            for domain, family, _clause in _eligible_domain_family_rows(
                text,
                specs=specs,
            )
        )
    )


def domain_route_family(text: str) -> tuple[str, str] | None:
    """Return the first evidence-bound Domain match for fixture annotations."""

    matches = domain_route_families(text)
    return matches[0] if matches else None


EFFECT_CHANGED = "changed"
EFFECT_UNCHANGED = "unchanged"
EFFECT_ADJACENT_ONLY = "adjacent-only"
EFFECT_AMBIGUOUS = "ambiguous"

_EffectRecord = tuple[str, str, int]
_EffectScope = tuple[int, str]
_NODE_RUNTIME_FAMILIES = (
    "process-child-signal",
    "timer-cancellation",
    "module-runtime",
    "worker-resource",
    "stream-backpressure",
    "buffer-binary",
    "event-loop-context",
)


def _normalize_effect_scope(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.casefold()).split())


_EFFECT_STATEMENT_BOUNDARY_RE = re.compile(
    r"(?:[!?;]+|[.](?=\s|$)|\b(?:but|while|whereas|yet|although)\b)"
)


def _bounded_effect_scopes(value: str) -> tuple[_EffectScope, ...]:
    """Return normalized scopes without moving effect terms between scopes."""

    sentence_scopes = _EFFECT_STATEMENT_BOUNDARY_RE.split(
        value.casefold()
    )
    result: list[_EffectScope] = []
    scope_id = 0
    for sentence_scope in sentence_scopes:
        protected = re.sub(
            r"\band\s+(?=(?:remains?|stays?)\s+unchanged\b)",
            " __effect_same_scope__ ",
            sentence_scope,
        )
        parts = re.split(
            r"(\s*/\s*|,+|\bplus\b|\band\b|\bor\b|\bwithout\b)",
            protected,
        )
        carry_no = False
        connector = ""
        for index, raw_part in enumerate(parts):
            if index % 2:
                connector = _normalize_effect_scope(raw_part)
                continue
            raw_part = raw_part.replace("__effect_same_scope__", " and ")
            normalized = _normalize_effect_scope(raw_part)
            if not normalized:
                continue
            if connector == "without":
                normalized = f"without {normalized}"
            elif connector in ("", "or") and carry_no:
                if not normalized.startswith(("no ", "without ")):
                    normalized = f"no {normalized}"
            elif "/" in connector or "," in connector:
                if carry_no and not normalized.startswith(("no ", "without ")):
                    normalized = f"no {normalized}"
            if normalized.startswith("no ") or re.search(r"\bno\b", normalized):
                carry_no = True
            elif connector not in ("or",) and "/" not in connector and "," not in connector:
                carry_no = False
            result.append((scope_id, normalized))
            scope_id += 1
    return tuple(result)


def _scope_is_unchanged(scope: str) -> bool:
    return (
        scope.startswith(("no ", "without "))
        or scope.endswith(" unchanged")
        or " remains unchanged" in f" {scope}"
        or " remain unchanged" in f" {scope}"
        or " stays unchanged" in f" {scope}"
        or bool(re.search(r"\b(?:do|does)\s+not\s+change\b", scope))
        or bool(re.search(r"\bnot\s+changing\b", scope))
        or bool(
            re.search(
                r"\b(?:background(?:\s+context)?|context)\s+only\b",
                scope,
            )
        )
        or bool(
            re.search(
                r"\bno\b.*\b(?:behavior|change|decision|effect|mutation|runtime|state|work)\b",
                scope,
            )
        )
    )


def _scope_is_ambiguous(scope: str) -> bool:
    return (
        "both" in scope
        and bool(re.search(r"\bchanges?\b", scope))
        and "unchanged" in scope
    )


def _effect_family_states(
    records: tuple[_EffectRecord, ...],
) -> tuple[tuple[str, str], ...]:
    """Aggregate records per family while preserving same-scope conflicts."""

    grouped: dict[str, list[tuple[str, int]]] = {}
    for family, polarity, scope_id in records:
        grouped.setdefault(family, []).append((polarity, scope_id))
    result: list[tuple[str, str]] = []
    for family, observations in grouped.items():
        changed_scopes = {
            scope_id
            for polarity, scope_id in observations
            if polarity == EFFECT_CHANGED
        }
        unchanged_scopes = {
            scope_id
            for polarity, scope_id in observations
            if polarity == EFFECT_UNCHANGED
        }
        if (
            any(
                polarity == EFFECT_AMBIGUOUS
                for polarity, _scope_id in observations
            )
            or changed_scopes.intersection(unchanged_scopes)
        ):
            state = EFFECT_AMBIGUOUS
        elif changed_scopes:
            state = EFFECT_CHANGED
        elif unchanged_scopes:
            state = EFFECT_UNCHANGED
        else:
            state = EFFECT_ADJACENT_ONLY
        result.append((family, state))
    return tuple(result)


def _overall_effect_state(records: tuple[_EffectRecord, ...]) -> str:
    states = tuple(state for _family, state in _effect_family_states(records))
    if EFFECT_AMBIGUOUS in states:
        return EFFECT_AMBIGUOUS
    if EFFECT_CHANGED in states:
        return EFFECT_CHANGED
    if EFFECT_UNCHANGED in states:
        return EFFECT_UNCHANGED
    return EFFECT_ADJACENT_ONLY


def _filesystem_process_effect_state(
    records: tuple[_EffectRecord, ...],
) -> str:
    """Combine the independent axes while honoring an explicit two-axis no."""

    overall = _overall_effect_state(records)
    if overall == EFFECT_AMBIGUOUS:
        return overall
    unchanged_families = {
        family
        for family, polarity, _scope_id in records
        if polarity == EFFECT_UNCHANGED
    }
    if {"filesystem-path", "child-process"}.issubset(unchanged_families):
        return EFFECT_UNCHANGED
    return overall


def _filesystem_process_effect_records(
    value: str,
) -> tuple[_EffectRecord, ...]:
    """Classify filesystem/path and child-process decisions independently."""

    records: list[_EffectRecord] = []
    for scope_id, scope in _bounded_effect_scopes(value):
        filesystem_scope = any(
            signal in scope
            for signal in (
                "filesystem",
                "local file",
                "atomic file",
                "settings file",
                "temporary file",
                "path authority",
                "path containment",
                "file containment",
                "file protection",
                "file permission",
                "file ownership",
                "file cleanup",
                "file replacement",
                "replace files",
                "replaces files",
                "symlink",
                "reparse",
            )
        )
        child_process_scope = any(
            signal in scope
            for signal in (
                "child process",
                "subprocess",
                "process executable",
                "process argv",
                "process environment",
                "process cwd",
                "process stdio",
                "process exit",
                "process timeout",
                "process cancellation",
                "process descendant",
                "process result",
                "process lifecycle",
                "process behavior",
                "process contract",
                "process safety decision",
            )
        )
        if filesystem_scope:
            filesystem_changed = any(
                signal in scope
                for signal in (
                    "file create",
                    "file creation",
                    "temporary commit",
                    "file replace",
                    "file replacement",
                    "replace files",
                    "replaces files",
                    "replaces a local settings file",
                    "replace a local settings file",
                    "atomically replace",
                    "atomically replaces",
                    "filesystem durability",
                    "file durability",
                    "file cleanup",
                    "file protection",
                    "file permission",
                    "file ownership",
                    "path authority",
                    "path containment",
                    "file containment",
                    "link behavior",
                    "symlink",
                    "reparse",
                    "filesystem mutation",
                    "local filesystem mutation",
                    "local file mutation",
                )
            )
            polarity = (
                EFFECT_AMBIGUOUS
                if _scope_is_ambiguous(scope)
                else EFFECT_UNCHANGED
                if _scope_is_unchanged(scope)
                else EFFECT_CHANGED
                if filesystem_changed
                else EFFECT_ADJACENT_ONLY
            )
            records.append(("filesystem-path", polarity, scope_id))
        if child_process_scope:
            child_process_changed = any(
                signal in scope
                for signal in (
                    "executable",
                    "argv",
                    "environment",
                    "working directory",
                    "cwd",
                    "stdio",
                    "exit",
                    "timeout",
                    "cancel",
                    "descendant",
                    "result",
                    "lifecycle",
                    "behavior",
                    "contract",
                    "spawn",
                    "shutdown",
                    "safety decision",
                    "control",
                )
            )
            polarity = (
                EFFECT_AMBIGUOUS
                if _scope_is_ambiguous(scope)
                else EFFECT_UNCHANGED
                if _scope_is_unchanged(scope)
                else EFFECT_CHANGED
                if child_process_changed
                else EFFECT_ADJACENT_ONLY
            )
            records.append(("child-process", polarity, scope_id))
    return tuple(records)


def _node_scope_families(scope: str) -> tuple[str, ...]:
    families: list[str] = []
    if any(
        signal in scope
        for signal in (
            "child process",
            "process signal",
            "process stdio",
            "process shutdown",
            "process state",
        )
    ):
        families.append("process-child-signal")
    if any(
        signal in scope
        for signal in (
            "abortsignal",
            "abort signal",
            "timer",
            "cancellation",
        )
    ):
        families.append("timer-cancellation")
    if any(
        signal in scope
        for signal in (
            "esm",
            "commonjs",
            "cjs",
            "runtime flag",
            "entrypoint",
            "module export",
            "module mode",
            "cache identity",
        )
    ):
        families.append("module-runtime")
    if any(
        signal in scope
        for signal in (
            "worker",
            "active resource",
            "active handle",
            "resource handle",
        )
    ):
        families.append("worker-resource")
    if any(
        signal in scope
        for signal in (
            "stream",
            "backpressure",
            "highwatermark",
            "high watermark",
        )
    ):
        families.append("stream-backpressure")
    if "buffer" in scope or (
        "binary" in scope
        and any(signal in scope for signal in ("byte", "encoding", "alias"))
    ):
        families.append("buffer-binary")
    if any(
        signal in scope
        for signal in (
            "event loop",
            "nexttick",
            "microtask",
            "async context",
            "asynclocalstorage",
        )
    ):
        families.append("event-loop-context")
    return tuple(dict.fromkeys(families))


def _node_owner_adjacent(scope: str) -> bool:
    policy_owner = any(
        signal in scope
        for signal in (
            "package policy",
            "build policy",
        )
    )
    policy_artifact_only = bool(
        re.search(
            r"\b(?:metadata|config|manifest)(?:\s+change)?\s+only"
            r"(?:\s+change)?\b",
            scope,
        )
    )
    independent_runtime_effect = any(
        signal in scope
        for signal in (
            "runtime resolution",
            "runtime behavior",
            "runtime flag",
            "entrypoint runtime",
            "esm runtime",
            "commonjs runtime",
            "cjs runtime",
            "module mode",
            "cache identity",
        )
    )
    policy_adjacent = (
        policy_owner
        and policy_artifact_only
        and not independent_runtime_effect
    )
    non_policy_owner = any(
        signal in scope
        for signal in (
            "typescript only",
            "browser only",
            "business rule",
        )
    )
    non_policy_adjacent = non_policy_owner and any(
        signal in scope
        for signal in (
            "interface",
            "api",
            "allocation state",
            "process state",
            "calculation only",
        )
    )
    return policy_adjacent or non_policy_adjacent


def _node_family_changed(family: str, scope: str) -> bool:
    family_signals = {
        "process-child-signal": (
            "child process",
            "process signal",
            "stdio",
            "shutdown",
            "spawn",
            "ipc",
            "exit",
        ),
        "timer-cancellation": (
            "abortsignal",
            "abort signal",
            "timer cancellation",
            "timer timeout",
            "cancellation",
        ),
        "module-runtime": (
            "runtime flag",
            "entrypoint",
            "module mode",
            "cache identity",
            "esm",
            "commonjs",
            "cjs",
        ),
        "worker-resource": (
            "active resource",
            "active handle",
            "resource handle",
            "worker resource",
            "worker thread",
            "worker shutdown",
            "worker termination",
            "worker failure",
        ),
        "stream-backpressure": (
            "backpressure",
            "stream completion",
            "stream destroy",
            "stream error",
            "stream flow",
            "stream pipeline",
        ),
        "buffer-binary": (
            "buffer encoding",
            "buffer alias",
            "buffer byte",
            "buffer binary",
        ),
        "event-loop-context": (
            "event loop",
            "nexttick",
            "microtask",
            "async context",
            "asynclocalstorage",
        ),
    }
    return any(signal in scope for signal in family_signals[family])


def _node_runtime_effect_records(value: str) -> tuple[_EffectRecord, ...]:
    """Return the shared seven-family Node.js runtime decision records."""

    records: list[_EffectRecord] = []
    for scope_id, scope in _bounded_effect_scopes(value):
        explicit_unchanged = (
            any(
                signal in scope
                for signal in (
                    "runtime",
                    "core library",
                    "node js behavior",
                    "node js semantics",
                )
            )
            and _scope_is_unchanged(scope)
        )
        if explicit_unchanged:
            records.extend(
                (family, EFFECT_UNCHANGED, scope_id)
                for family in _NODE_RUNTIME_FAMILIES
            )
            continue
        for family in _node_scope_families(scope):
            if _scope_is_ambiguous(scope):
                polarity = EFFECT_AMBIGUOUS
            elif _node_owner_adjacent(scope):
                polarity = EFFECT_ADJACENT_ONLY
            elif _scope_is_unchanged(scope):
                polarity = EFFECT_UNCHANGED
            elif _node_family_changed(family, scope):
                polarity = EFFECT_CHANGED
            else:
                polarity = EFFECT_ADJACENT_ONLY
            records.append((family, polarity, scope_id))
    return tuple(records)


def _negates_limiter(scope: str, limiter: str) -> bool:
    qualifier = r"(?:(?:merely|just|a)\s+)*"
    restriction = r"(?:(?:limited|restricted)\s+to\s+)?"
    return bool(
        re.search(
            rf"\bnot\s+{qualifier}{restriction}{limiter}\b",
            scope,
        )
    )


def _distributed_limiter(scope: str) -> bool:
    local_retry = bool(
        re.search(
            r"\b(?:(?:limited|restricted)\s+to\s+local\s+retr(?:y|ies)|"
            r"local\s+retr(?:y|ies)\s+only)\b",
            scope,
        )
    ) and not _negates_limiter(scope, r"local\s+retr(?:y|ies)(?:\s+only)?")
    schema_only = (
        "schema only" in scope
        and not _negates_limiter(scope, r"schema\s+only")
    )
    engine_only = any(
        signal in scope
        for signal in (
            "engine mechanics only",
            "workflow engine scheduler mechanics",
        )
    ) and not (
        _negates_limiter(scope, r"engine\s+mechanics(?:\s+only)?")
        or _negates_limiter(
            scope,
            r"workflow\s+engine\s+scheduler\s+mechanics(?:\s+only)?",
        )
    )
    atomic_only = any(
        signal in scope
        for signal in (
            "one atomic transaction",
            "one atomic database transaction",
        )
    )
    return local_retry or schema_only or engine_only or atomic_only


def _distributed_workflow_effect_records(
    value: str,
) -> tuple[_EffectRecord, ...]:
    """Classify durable workflow effects without cross-scope co-occurrence."""

    records: list[_EffectRecord] = []
    for scope_id, scope in _bounded_effect_scopes(value):
        workflow_context = any(
            signal in scope
            for signal in (
                "cross service",
                "distributed workflow",
                "independently committed",
                "durable workflow",
                "active workflow",
                "desired workflow state",
                "participant state",
                "participant effect",
                "service effect",
            )
        )
        workflow_decision = any(
            signal in scope
            for signal in (
                "unknown outcome",
                "unknown effect",
                "compensation",
                "reconciliation",
                "recovery",
                "stuck",
                "repair",
                "definition evolution",
                "workflow evolution",
                "version evolution",
            )
        )
        local_retry_without_context = (
            "local retry" in scope
            and workflow_decision
            and not workflow_context
        )
        limited = _distributed_limiter(scope)
        explicit_unchanged = _scope_is_unchanged(scope) and any(
            signal in scope
            for signal in (
                "independently committed",
                "durable workflow",
                "participant effect",
                "service effect",
                "workflow state",
            )
        )
        if explicit_unchanged:
            polarity = EFFECT_UNCHANGED
        elif workflow_context and workflow_decision and _scope_is_ambiguous(scope):
            polarity = EFFECT_AMBIGUOUS
        elif limited or local_retry_without_context:
            polarity = EFFECT_ADJACENT_ONLY
        elif workflow_context and workflow_decision:
            polarity = EFFECT_CHANGED
        elif workflow_decision and any(
            signal in scope
            for signal in (
                "local retry",
                "schema only",
                "engine mechanics",
                "workflow engine",
                "atomic transaction",
            )
        ):
            polarity = EFFECT_ADJACENT_ONLY
        else:
            continue
        records.append(("distributed-workflow", polarity, scope_id))
    return tuple(records)


_STRUCTURE_DECISION_SPECS: dict[
    str,
    tuple[tuple[str, ...], tuple[str, ...]],
] = {
    "domain-object": (
        (
            "domain identity",
            "domain object",
            "entity",
            "value object",
            "aggregate root",
            "writer authority",
            "invariant entry point",
        ),
        (
            "classif",
            "analy",
            "whether",
            "identify",
            "implement",
            "immutable value",
            "replacement semantics",
        ),
    ),
    "pattern": (
        (
            "design pattern",
            "provider pattern",
            "provider variants",
            "singleton",
            "substitution contract",
            "variation",
            "protocol",
            "extension force",
        ),
        (
            "provider variants",
            "substitution contract",
            "initialization",
            "synchronization",
            "reset",
            "teardown",
            "concurrent caller",
            "current variation",
            "current protocol",
            "current extension",
        ),
    ),
    "minimality": (
        (
            "complexity delete list",
            "pass through wrapper",
            "new wrapper",
            "delete or omit",
            "new structure",
            "capability gap",
        ),
        (
            "review",
            "decid",
            "whether",
            "no current variation",
            "no current lifecycle",
            "capability gap",
        ),
    ),
    "module-boundary": (
        (
            "module ownership",
            "cross module",
            "public export",
            "dependency edge",
            "shared module",
        ),
        (
            "change",
            "cross module",
            "public export",
            "dependency edge",
            "new export",
            "new dependency",
        ),
    ),
    "refactoring": (
        (
            "behavior preserving move",
            "behavior preserved",
            "private class moved",
            "structural relocation",
            "fixed placement",
            "placement were already accepted",
            "placement was already accepted",
        ),
        (
            "move",
            "moved",
            "relocat",
            "consolidat",
            "behavior preserv",
            "placement were already accepted",
            "placement was already accepted",
        ),
    ),
    "readability": (
        (
            "guard clause",
            "local naming",
            "readability",
        ),
        (
            "review",
            "rename",
            "naming",
            "readability",
        ),
    ),
}


_OWNER_PLACEMENT_SUBJECT_HEADS = frozenset(
    {
        "placement",
        "implementation-structure",
        "helper",
        "method",
        "class",
        "function",
        "implementation",
        "copy",
    }
)
_OWNER_PLACEMENT_SELECTION_PREDICATES = frozenset(
    {"decide", "choose", "select", "determine", "establish"}
)
_OWNER_PLACEMENT_OPEN_OPERATORS = frozenset(
    {
        "if",
        "whether",
        "which",
        "where",
        "between",
        "one-of",
        "to-keep",
        "alternative",
        "option",
        "choice",
        "tradeoff",
    }
)
_OWNER_PLACEMENT_RESOLUTION_PREDICATES = frozenset(
    {
        "fixed",
        "resolved",
        "accepted",
        "selected",
        "decided",
        "chosen",
        "determined",
        "known",
        "resolved-unknown",
    }
)
_OWNER_PLACEMENT_MUTATION_PREDICATES = frozenset(
    {
        "put",
        "move",
        "place",
        "extract",
        "consolidate",
        "co-locate",
        "keep",
        "retain",
        "reuse",
    }
)
_OWNER_PLACEMENT_DESTINATION_RELATIONS = frozenset(
    {"to", "in", "within", "inside", "into", "as"}
)
_OWNER_PLACEMENT_UNKNOWN_MARKERS = frozenset(
    {
        "unknown",
        "unresolved",
        "undecided",
        "open",
        "not-yet-known",
        "to-be-selected",
    }
)
_OWNER_PLACEMENT_ANAPHORA_DETERMINERS = frozenset(
    {"this", "that", "the", "its"}
)
_OWNER_PLACEMENT_ANAPHORA_HEADS = frozenset(
    {"placement", "decision", "structure"}
)
_OWNER_PLACEMENT_PREDICATE_CLASSES = frozenset(
    {"selection", "resolution", "mutation", "unchanged", "unsupported"}
)
_OWNER_PLACEMENT_NAMED_SUBJECTS = frozenset({"alpha", "beta"})
_OWNER_PLACEMENT_MULTIWORD_TERMINALS = {
    ("implementation", "structure"): "implementation-structure",
    ("not", "yet", "known"): "not-yet-known",
    ("to", "be", "selected"): "to-be-selected",
    ("no", "longer", "unknown"): "resolved-unknown",
    ("not", "unknown"): "resolved-unknown",
    ("same", "file", "function"): "same-file-function",
    ("accepted", "owner"): "accepted-owner",
    ("repository", "owned"): "repository-owned",
    ("behavior", "preserving"): "behavior-preserving",
    ("same", "module"): "same-module",
    ("owner", "private"): "owner-private",
    ("one", "of"): "one-of",
    ("to", "keep"): "to-keep",
    ("same", "file"): "same-file",
    ("co", "locate"): "co-locate",
    ("co", "located"): "co-locate",
}
_OWNER_PLACEMENT_MULTIWORD_ORDER = tuple(
    sorted(
        _OWNER_PLACEMENT_MULTIWORD_TERMINALS,
        key=lambda terminal: (-len(terminal), terminal),
    )
)
_OWNER_PLACEMENT_LEMMAS = {
    "alternatives": "alternative",
    "choices": "choice",
    "classes": "class",
    "copies": "copy",
    "decides": "decide",
    "deciding": "decide",
    "determines": "determine",
    "determining": "determine",
    "establishes": "establish",
    "establishing": "establish",
    "extracts": "extract",
    "extracted": "extract",
    "extracting": "extract",
    "functions": "function",
    "helpers": "helper",
    "implementations": "implementation",
    "keeps": "keep",
    "keeping": "keep",
    "kept": "keep",
    "methods": "method",
    "mentioning": "mention",
    "mentions": "mention",
    "moves": "move",
    "moved": "move",
    "moving": "move",
    "options": "option",
    "placements": "placement",
    "places": "place",
    "placed": "place",
    "placing": "place",
    "puts": "put",
    "putting": "put",
    "remains": "remain",
    "retains": "retain",
    "retained": "retain",
    "retaining": "retain",
    "reuses": "reuse",
    "reused": "reuse",
    "reusing": "reuse",
    "selects": "select",
    "selecting": "select",
    "stays": "stay",
    "structures": "structure",
    "tradeoffs": "tradeoff",
    "changes": "change",
    "consolidates": "consolidate",
    "consolidated": "consolidate",
    "consolidating": "consolidate",
    "chooses": "choose",
    "choosing": "choose",
}
_OWNER_PLACEMENT_RESOLUTION_CONTEXT = frozenset(
    {
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "has",
        "have",
        "had",
        "already",
        "previously",
    }
)
_OWNER_PLACEMENT_CONNECTORS = frozenset({"and", "then"})
_OWNER_PLACEMENT_MUTATION_ADVERBS = frozenset(
    {"deliberately", "intentionally"}
)
_OWNER_PLACEMENT_TARGETS = {
    "same-file": "same-file",
    "same-file-function": "same-file",
    "same-module": "same-module",
    "accepted-owner": "accepted-owner",
    "method": "method",
    "class": "class",
    "function": "function",
    "file": "file",
    "owner": "owner",
    "separate": "separate",
}


@dataclass(frozen=True)
class _OwnerPlacementFact:
    scope_id: int
    decision_id: int
    subject_key: str
    predicate_class: str
    alternatives: tuple[str, ...]
    destination: str | None
    anaphora_of: int | None
    requested_action: bool = False


@dataclass(frozen=True)
class _OwnerPlacementDecision:
    decision_id: int
    subject_key: str
    facts: tuple[_OwnerPlacementFact, ...]
    polarity: str


@dataclass(frozen=True)
class _OwnerPlacementSubject:
    start: int
    end: int
    subject_key: str
    named: bool
    strong: bool
    anaphora: bool


def _owner_placement_tokens(value: str) -> tuple[str, ...]:
    """Normalize one hard scope through closed finite terminals."""

    raw = tuple(_normalize_effect_scope(value).split())
    result: list[str] = []
    index = 0
    while index < len(raw):
        matched = False
        for terminal in _OWNER_PLACEMENT_MULTIWORD_ORDER:
            width = len(terminal)
            if raw[index:index + width] != terminal:
                continue
            result.append(_OWNER_PLACEMENT_MULTIWORD_TERMINALS[terminal])
            index += width
            matched = True
            break
        if matched:
            continue
        result.append(_OWNER_PLACEMENT_LEMMAS.get(raw[index], raw[index]))
        index += 1
    return tuple(result)


def _owner_placement_subject_key(
    tokens: tuple[str, ...],
    start: int,
    end: int,
    *,
    default_head: str,
) -> tuple[str, bool]:
    phrase = tokens[max(0, start - 4):min(len(tokens), end + 1)]
    name = next(
        (token for token in reversed(phrase) if token in _OWNER_PLACEMENT_NAMED_SUBJECTS),
        None,
    )
    if name is not None:
        return f"named:{name}", True
    qualifier = (
        "owner-private"
        if "owner-private" in phrase
        else "private"
        if "private" in phrase
        else "generic"
    )
    return f"{qualifier}:{default_head}", False


def _owner_placement_subject_candidates(
    tokens: tuple[str, ...],
) -> tuple[_OwnerPlacementSubject, ...]:
    """Find explicit and candidate subjects without interpreting predicates."""

    subjects: list[_OwnerPlacementSubject] = []
    covered: set[int] = set()
    for index in range(len(tokens) - 1):
        if (
            tokens[index] in _OWNER_PLACEMENT_ANAPHORA_DETERMINERS
            and tokens[index + 1] in _OWNER_PLACEMENT_ANAPHORA_HEADS
        ):
            subjects.append(
                _OwnerPlacementSubject(
                    index,
                    index + 2,
                    f"anaphora:{index}",
                    False,
                    True,
                    True,
                )
            )
            covered.update((index, index + 1))

    for index, token in enumerate(tokens):
        if index in covered or token not in {"placement", "implementation-structure"}:
            continue
        lookback_start = max(0, index - 5)
        phrase = tokens[lookback_start:index + 1]
        if "documentation" in phrase and "mention" in phrase:
            continue
        start = index
        for offset, candidate in enumerate(phrase[:-1]):
            if candidate in {
                "owner-private",
                "private",
                "alpha",
                "beta",
                "helper",
                "method",
                "class",
                "function",
                "implementation",
                "copy",
                "file",
                "object",
                "final",
            }:
                start = lookback_start + offset
                break
        head = next(
            (
                candidate
                for candidate in reversed(phrase[:-1])
                if candidate in _OWNER_PLACEMENT_SUBJECT_HEADS
                and candidate != "placement"
            ),
            token,
        )
        key, named = _owner_placement_subject_key(
            tokens,
            start,
            index + 1,
            default_head=head,
        )
        subjects.append(
            _OwnerPlacementSubject(start, index + 1, key, named, True, False)
        )
        covered.update(range(start, index + 1))

    strong_starts = tuple(subject.start for subject in subjects if subject.strong)
    for index, token in enumerate(tokens):
        if index in covered or token not in _OWNER_PLACEMENT_SUBJECT_HEADS:
            continue
        if token in {"placement", "implementation-structure"}:
            continue
        lookback = tokens[max(0, index - 4):index]
        if any(
            relation in lookback
            for relation in _OWNER_PLACEMENT_DESTINATION_RELATIONS
        ):
            continue
        qualified = any(
            qualifier in lookback
            for qualifier in (
                "owner-private",
                "private",
                "invariant",
                "alpha",
                "beta",
                "separate",
            )
        )
        if not qualified:
            continue
        alternative_prefix = any(
            operator in tokens[:index]
            for operator in ("between", "one-of")
        )
        if alternative_prefix and any(start < index for start in strong_starts):
            continue
        start = index
        while start > 0 and index - start < 4 and tokens[start - 1] in {
            "owner-private",
            "private",
            "invariant",
            "alpha",
            "beta",
            "generator",
            "duplicate",
            "separate",
        }:
            start -= 1
        key, named = _owner_placement_subject_key(
            tokens,
            start,
            index + 1,
            default_head=token,
        )
        subjects.append(
            _OwnerPlacementSubject(start, index + 1, key, named, False, False)
        )
        covered.update(range(start, index + 1))
    return tuple(sorted(subjects, key=lambda subject: (subject.start, subject.end)))


def _owner_placement_targets(tokens: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            _OWNER_PLACEMENT_TARGETS[token]
            for token in tokens
            if token in _OWNER_PLACEMENT_TARGETS
        )
    )


def _owner_placement_destination_after(
    tokens: tuple[str, ...],
    start: int,
) -> str | None:
    for relation_index in range(start, len(tokens)):
        if tokens[relation_index] not in _OWNER_PLACEMENT_DESTINATION_RELATIONS:
            continue
        for token in tokens[relation_index + 1:relation_index + 8]:
            destination = _OWNER_PLACEMENT_TARGETS.get(token)
            if destination is not None:
                return destination
    return None


def _owner_placement_prefix_binds(
    prefix: tuple[str, ...],
    predicates: frozenset[str],
    *,
    strong_subject: bool,
    allow_wh: bool = False,
) -> bool:
    positions = [
        index for index, token in enumerate(prefix) if token in predicates
    ]
    if not positions:
        if not strong_subject or not allow_wh:
            return False
        wh_positions = [
            index
            for index, token in enumerate(prefix)
            if token in {"if", "whether", "which", "where"}
        ]
        return bool(wh_positions and len(prefix) - wh_positions[-1] <= 4)
    tail = prefix[positions[-1]:]
    connector_positions = [
        index
        for index, token in enumerate(tail)
        if token in _OWNER_PLACEMENT_CONNECTORS
    ]
    if connector_positions:
        last_connector = connector_positions[-1]
        if "for" not in tail[last_connector + 1:]:
            return False
    if "for" in tail or any(
        token in _OWNER_PLACEMENT_OPEN_OPERATORS for token in tail
    ):
        return True
    return len(tail) <= 5


def _owner_placement_resolution_is_destination_modifier(
    tokens: tuple[str, ...],
    predicate_index: int,
    *,
    mutation_present: bool,
) -> bool:
    if not mutation_present or tokens[predicate_index] != "selected":
        return False
    relation_before = any(
        token in _OWNER_PLACEMENT_DESTINATION_RELATIONS
        for token in tokens[:predicate_index]
    )
    destination_after = any(
        token in _OWNER_PLACEMENT_TARGETS
        for token in tokens[predicate_index + 1:predicate_index + 6]
    )
    return relation_before and destination_after


def _owner_placement_unknown_state(
    tokens: tuple[str, ...],
) -> tuple[bool, bool]:
    """Return positive-unknown and explicitly-resolved marker states."""

    positive = False
    resolved = "resolved-unknown" in tokens
    for index, token in enumerate(tokens):
        if token not in _OWNER_PLACEMENT_UNKNOWN_MARKERS:
            continue
        if token == "unknown" and "no" in tokens[max(0, index - 4):index]:
            resolved = True
            continue
        positive = True
    return positive, resolved


def _owner_placement_bound_suffix(
    suffix: tuple[str, ...],
) -> tuple[str, ...]:
    """Return the one suffix region owned by the current placement subject."""

    boundary = next(
        (
            index
            for index, token in enumerate(suffix)
            if token == "that" or token in _OWNER_PLACEMENT_CONNECTORS
        ),
        len(suffix),
    )
    if boundary < len(suffix) and suffix[boundary] == "and":
        coordinated_head = suffix[:boundary]
        coordinated_tail = suffix[boundary + 1:]
        relation_tokens = (
            _OWNER_PLACEMENT_SELECTION_PREDICATES
            | _OWNER_PLACEMENT_OPEN_OPERATORS
            | _OWNER_PLACEMENT_RESOLUTION_PREDICATES
            | _OWNER_PLACEMENT_MUTATION_PREDICATES
            | _OWNER_PLACEMENT_DESTINATION_RELATIONS
            | _OWNER_PLACEMENT_UNKNOWN_MARKERS
        )
        shared_resolution = (
            bool(coordinated_head)
            and bool(coordinated_tail)
            and not any(token in relation_tokens for token in coordinated_head)
            and (
                (
                    coordinated_tail[-1]
                    in _OWNER_PLACEMENT_RESOLUTION_PREDICATES
                    and any(
                        token in _OWNER_PLACEMENT_RESOLUTION_CONTEXT
                        for token in coordinated_tail[:-1]
                    )
                )
                or (
                    coordinated_tail[-1] == "unchanged"
                    and any(
                        token in {"is", "are", "was", "were", "remain", "stay"}
                        for token in coordinated_tail[:-1]
                    )
                )
            )
        )
        if shared_resolution:
            return suffix
    return suffix[:boundary]


def _owner_placement_facts_for_subject(
    tokens: tuple[str, ...],
    subject: _OwnerPlacementSubject,
    *,
    scope_id: int,
    decision_id: int,
    prefix_start: int,
    window_end: int,
    subject_key: str | None = None,
    anaphora_of: int | None = None,
) -> tuple[_OwnerPlacementFact, ...]:
    prefix = tokens[prefix_start:subject.start]
    suffix = tokens[subject.end:window_end]
    bounded_suffix = _owner_placement_bound_suffix(suffix)
    subject_tokens = tokens[subject.start:subject.end]
    relation_tokens = prefix + subject_tokens + bounded_suffix
    requested_task_action = bool(
        _task_action_matches(" ".join(relation_tokens))
    )
    key = subject_key or subject.subject_key
    facts: list[_OwnerPlacementFact] = []

    def add(
        predicate_class: str,
        *,
        alternatives: tuple[str, ...] = (),
        destination: str | None = None,
        requested_action: bool = False,
    ) -> None:
        if predicate_class not in _OWNER_PLACEMENT_PREDICATE_CLASSES:
            raise RoutingIntegrityError(
                f"unsupported owner-placement predicate class {predicate_class!r}"
            )
        fact = _OwnerPlacementFact(
            scope_id,
            decision_id,
            key,
            predicate_class,
            alternatives,
            destination,
            anaphora_of,
            requested_action,
        )
        if fact not in facts:
            facts.append(fact)

    unknown_positive, unknown_resolved = _owner_placement_unknown_state(
        relation_tokens
    )
    if unknown_positive:
        add("unsupported")
    if unknown_resolved:
        add("resolution")

    compound_resolution_subject = (
        subject_tokens == ("placement",)
        and bool(prefix)
        and prefix[-1] in _OWNER_PLACEMENT_MUTATION_PREDICATES
        and bool(bounded_suffix)
        and bounded_suffix[0]
        in {"is", "are", "was", "were", "remain", "stay"}
        and any(
            token in {"fixed", "resolved"}
            for token in bounded_suffix[1:]
        )
        and not any(
            token in _OWNER_PLACEMENT_DESTINATION_RELATIONS
            for token in bounded_suffix
        )
    )
    prefix_mutation = (
        not compound_resolution_subject
        and _owner_placement_prefix_binds(
            prefix,
            _OWNER_PLACEMENT_MUTATION_PREDICATES,
            strong_subject=subject.strong,
        )
    )
    mutation_positions = [
        index
        for index, token in enumerate(bounded_suffix)
        if token in _OWNER_PLACEMENT_MUTATION_PREDICATES
    ]
    mutation_present = prefix_mutation or bool(mutation_positions)
    if prefix_mutation:
        predicate_index = max(
            index
            for index, token in enumerate(prefix)
            if token in _OWNER_PLACEMENT_MUTATION_PREDICATES
        )
        imperative_prefix = predicate_index == 0 or (
            prefix[predicate_index - 1] in _OWNER_PLACEMENT_CONNECTORS
        ) or (
            predicate_index == 1
            and prefix[0] in _OWNER_PLACEMENT_MUTATION_ADVERBS
        ) or (
            predicate_index >= 2
            and prefix[predicate_index - 1]
            in _OWNER_PLACEMENT_MUTATION_ADVERBS
            and prefix[predicate_index - 2]
            in _OWNER_PLACEMENT_CONNECTORS
        )
        if imperative_prefix:
            coordinated_alternative = (
                predicate_index > 0
                and prefix[predicate_index - 1]
                in _OWNER_PLACEMENT_CONNECTORS
                and any(
                    token in _OWNER_PLACEMENT_OPEN_OPERATORS
                    for token in tokens[:prefix_start]
                )
            )
        if imperative_prefix and not coordinated_alternative:
            mutation_window = (
                prefix[predicate_index:]
                + subject_tokens
                + bounded_suffix
            )
            add(
                "mutation",
                destination=_owner_placement_destination_after(
                    mutation_window,
                    0,
                ),
                requested_action=True,
            )
    for predicate_index in mutation_positions:
        add(
            "mutation",
            destination=_owner_placement_destination_after(
                bounded_suffix,
                predicate_index + 1,
            ),
        )

    prefix_selection = _owner_placement_prefix_binds(
        prefix,
        _OWNER_PLACEMENT_SELECTION_PREDICATES,
        strong_subject=subject.strong,
        allow_wh=True,
    )
    suffix_open = any(
        token in {"between", "one-of", "alternative", "option", "choice", "tradeoff"}
        for token in bounded_suffix
    )
    suffix_selection = any(
        token in _OWNER_PLACEMENT_SELECTION_PREDICATES
        and any(
            candidate in _OWNER_PLACEMENT_OPEN_OPERATORS
            for candidate in bounded_suffix[predicate_index + 1:]
        )
        and bool(
            _owner_placement_targets(
                bounded_suffix[predicate_index + 1:]
            )
        )
        for predicate_index, token in enumerate(bounded_suffix)
    )
    wh_bound = (
        subject.strong
        and bool(bounded_suffix)
        and bounded_suffix[0] in {"if", "whether", "which", "where"}
    )
    if prefix_selection or suffix_open or suffix_selection or wh_bound:
        add(
            "selection",
            alternatives=_owner_placement_targets(relation_tokens),
            requested_action=requested_task_action,
        )

    for predicate_index, token in enumerate(bounded_suffix):
        if token not in _OWNER_PLACEMENT_RESOLUTION_PREDICATES:
            continue
        context = bounded_suffix[max(0, predicate_index - 4):predicate_index]
        if token == "selected" and not any(
            candidate in _OWNER_PLACEMENT_RESOLUTION_CONTEXT
            for candidate in context
        ):
            continue
        if _owner_placement_resolution_is_destination_modifier(
            bounded_suffix,
            predicate_index,
            mutation_present=mutation_present,
        ):
            continue
        add(
            "resolution",
            destination=_owner_placement_destination_after(
                bounded_suffix,
                predicate_index + 1,
            ),
            requested_action=requested_task_action,
        )

    explicit_unchanged = "unchanged" in relation_tokens and any(
        token in {"is", "are", "was", "were", "remain", "stay"}
        for token in relation_tokens
    )
    explicit_no_change = (
        "no" in relation_tokens and "change" in relation_tokens
    )
    if explicit_unchanged or explicit_no_change:
        add("unchanged", requested_action=requested_task_action)
    if requested_task_action and not facts:
        destination = _owner_placement_destination_after(
            bounded_suffix,
            0,
        )
        if destination is not None:
            add(
                "resolution",
                destination=destination,
                requested_action=True,
            )
    return tuple(facts)


def _owner_placement_decision_polarity(
    facts: tuple[_OwnerPlacementFact, ...],
) -> str:
    classes = {fact.predicate_class for fact in facts}
    destinations = {
        fact.destination for fact in facts if fact.destination is not None
    }
    if "unsupported" in classes:
        return EFFECT_AMBIGUOUS
    if "selection" in classes and (
        "resolution" in classes or "mutation" in classes
    ):
        return EFFECT_AMBIGUOUS
    if "selection" in classes:
        return EFFECT_AMBIGUOUS
    if len(destinations) > 1:
        return EFFECT_AMBIGUOUS
    if "mutation" in classes and "unchanged" in classes:
        return EFFECT_AMBIGUOUS
    if "mutation" in classes:
        return EFFECT_CHANGED
    if "resolution" in classes or "unchanged" in classes:
        return EFFECT_UNCHANGED
    return EFFECT_AMBIGUOUS


def _owner_placement_decisions(
    value: str,
) -> tuple[_OwnerPlacementDecision, ...]:
    """Build finite owner-placement facts and decisions inside existing hard scopes."""

    facts_by_decision: dict[int, list[_OwnerPlacementFact]] = {}
    subject_by_decision: dict[int, str] = {}
    decision_by_subject: dict[str, int] = {}
    next_decision_id = 0
    recent_decisions: tuple[int, ...] = ()

    def ensure_decision(subject_key: str) -> int:
        nonlocal next_decision_id
        decision_id = decision_by_subject.get(subject_key)
        if decision_id is not None:
            return decision_id
        decision_id = next_decision_id
        next_decision_id += 1
        decision_by_subject[subject_key] = decision_id
        subject_by_decision[decision_id] = subject_key
        facts_by_decision[decision_id] = []
        return decision_id

    for scope_id, raw_scope in enumerate(
        _EFFECT_STATEMENT_BOUNDARY_RE.split(value.casefold())
    ):
        tokens = _owner_placement_tokens(raw_scope)
        if not tokens:
            recent_decisions = ()
            continue
        subjects = _owner_placement_subject_candidates(tokens)
        explicit_subjects = tuple(
            subject for subject in subjects if not subject.anaphora
        )
        anaphora_subjects = tuple(
            subject for subject in subjects if subject.anaphora
        )
        current_decisions: list[int] = []
        explicit_decisions: list[tuple[_OwnerPlacementSubject, int]] = []
        for index, subject in enumerate(explicit_subjects):
            prefix_start = (
                explicit_subjects[index - 1].end if index else 0
            )
            window_end = (
                explicit_subjects[index + 1].start
                if index + 1 < len(explicit_subjects)
                else len(tokens)
            )
            provisional_id = decision_by_subject.get(
                subject.subject_key,
                next_decision_id,
            )
            facts = _owner_placement_facts_for_subject(
                tokens,
                subject,
                scope_id=scope_id,
                decision_id=provisional_id,
                prefix_start=prefix_start,
                window_end=window_end,
            )
            if not facts and not subject.strong:
                continue
            decision_id = ensure_decision(subject.subject_key)
            if not facts:
                facts = (
                    _OwnerPlacementFact(
                        scope_id,
                        decision_id,
                        subject.subject_key,
                        "unsupported",
                        (),
                        None,
                        None,
                    ),
                )
            elif provisional_id != decision_id:
                facts = tuple(
                    _OwnerPlacementFact(
                        fact.scope_id,
                        decision_id,
                        fact.subject_key,
                        fact.predicate_class,
                        fact.alternatives,
                        fact.destination,
                        fact.anaphora_of,
                        fact.requested_action,
                    )
                    for fact in facts
                )
            facts_by_decision[decision_id].extend(facts)
            current_decisions.append(decision_id)
            explicit_decisions.append((subject, decision_id))

        for subject in anaphora_subjects:
            same_scope_candidates = tuple(
                dict.fromkeys(
                    decision_id
                    for explicit_subject, decision_id in explicit_decisions
                    if explicit_subject.end <= subject.start
                )
            )
            candidates = same_scope_candidates or tuple(
                dict.fromkeys(recent_decisions)
            )
            if len(candidates) != 1:
                subject_key = f"unsupported-anaphora:{scope_id}:{subject.start}"
                decision_id = ensure_decision(subject_key)
                facts_by_decision[decision_id].append(
                    _OwnerPlacementFact(
                        scope_id,
                        decision_id,
                        subject_key,
                        "unsupported",
                        (),
                        None,
                        None,
                    )
                )
                current_decisions.append(decision_id)
                continue
            decision_id = candidates[0]
            subject_key = subject_by_decision[decision_id]
            facts = _owner_placement_facts_for_subject(
                tokens,
                subject,
                scope_id=scope_id,
                decision_id=decision_id,
                prefix_start=0,
                window_end=len(tokens),
                subject_key=subject_key,
                anaphora_of=decision_id,
            )
            if not facts:
                facts = (
                    _OwnerPlacementFact(
                        scope_id,
                        decision_id,
                        subject_key,
                        "unsupported",
                        (),
                        None,
                        decision_id,
                    ),
                )
            facts_by_decision[decision_id].extend(facts)
            current_decisions.append(decision_id)
        recent_decisions = tuple(dict.fromkeys(current_decisions))

    return tuple(
        _OwnerPlacementDecision(
            decision_id,
            subject_by_decision[decision_id],
            tuple(facts_by_decision[decision_id]),
            _owner_placement_decision_polarity(
                tuple(facts_by_decision[decision_id])
            ),
        )
        for decision_id in sorted(facts_by_decision)
    )


def _owner_placement_has_relation_mutation(value: str) -> bool:
    return any(
        fact.predicate_class == "mutation"
        for decision in _owner_placement_decisions(value)
        for fact in decision.facts
    )


def _owner_placement_has_requested_mutation(value: str) -> bool:
    return any(
        fact.predicate_class == "mutation" and fact.requested_action
        for decision in _owner_placement_decisions(value)
        for fact in decision.facts
    )


def _owner_placement_has_requested_action(value: str) -> bool:
    return any(
        fact.requested_action
        for decision in _owner_placement_decisions(value)
        for fact in decision.facts
    )


def _owner_placement_backend_subject(value: str) -> bool:
    tokens = _owner_placement_tokens(value)
    repository_tooling = (
        "generator" in tokens
        and (
            "repository-owned" in tokens
            or "repository" in tokens
        )
    )
    return (
        not repository_tooling
        and _owner_placement_has_requested_action(value)
    )


def _owner_placement_decision_records(
    value: str,
    anchors: tuple[str, ...],
) -> tuple[_EffectRecord, ...]:
    del anchors
    return tuple(
        ("owner-placement", decision.polarity, decision.decision_id)
        for decision in _owner_placement_decisions(value)
    )


def _semantic_decision_records(
    value: str,
    family: str,
    anchors: tuple[str, ...],
    forces: tuple[str, ...],
) -> tuple[_EffectRecord, ...]:
    """Classify a decision only when its subject and force share a bounded scope."""

    records: list[_EffectRecord] = []
    for scope_id, scope in _bounded_effect_scopes(value):
        if not any(
            re.search(
                rf"\b{escaped_anchor}\b",
                scope,
            )
            for escaped_anchor in (
                re.escape(anchor).replace(r"\\ ", r"\\s+")
                for anchor in anchors
            )
        ):
            continue
        if _scope_is_ambiguous(scope) or re.search(
            r"\b(?:unknown|unresolved|undecided)\b",
            scope,
        ):
            polarity = EFFECT_AMBIGUOUS
        elif _scope_is_unchanged(scope) or (
            family == "pattern"
            and bool(
                re.search(
                    r"\b(?:has|have|with)\s+no\s+current\s+"
                    r"(?:variation|lifecycle|protocol|extension force)\b",
                    scope,
                )
            )
        ):
            polarity = EFFECT_UNCHANGED
        elif any(force in scope for force in forces):
            polarity = EFFECT_CHANGED
        else:
            polarity = EFFECT_ADJACENT_ONLY
        records.append((family, polarity, scope_id))
    return tuple(records)


def _domain_object_facts_explicitly_unchanged(value: str) -> bool:
    """Honor the complete domain-fact anti-contract over incidental mapping nouns."""

    normalized = _normalize_effect_scope(value)
    required_facts = (
        "domain identity",
        "lifecycle",
        "aggregate",
        "invariant",
        "writer authority",
    )
    if not all(fact in normalized for fact in required_facts):
        return False
    start = normalized.find("domain identity")
    unchanged = re.search(
        r"\b(?:remain|remains|stay|stays|are)\s+unchanged\b",
        normalized[start:],
    )
    return unchanged is not None


def _structure_decision_states(value: str) -> dict[str, str]:
    """Return effect-aware structure decisions without cross-clause keyword joins."""

    states = {
        "owner-placement": _overall_effect_state(
            _owner_placement_decision_records(value, ())
        )
    }
    states.update(
        {
            family: _overall_effect_state(
                _semantic_decision_records(
                    value,
                    family,
                    anchors,
                    forces,
                )
            )
            for family, (anchors, forces) in _STRUCTURE_DECISION_SPECS.items()
        }
    )
    if _domain_object_facts_explicitly_unchanged(value):
        states["domain-object"] = EFFECT_UNCHANGED
    return states


def _owner_internal_structure_decision_evidence(
    value: str,
) -> tuple[str, ...]:
    """Bind a known owner to one unresolved reuse-versus-separation decision."""

    statements = tuple(
        normalized
        for part in re.split(
            r"(?:[!?;]+|[.](?=\s|$)|\bbut\b|\bwhile\b|\bwhereas\b)",
            value.casefold(),
        )
        if (normalized := _normalize_effect_scope(part))
    )
    known_owner = any(
        re.search(
            r"\b(?:accepted|established|fixed|known)\s+"
            r"(?:[a-z0-9]+\s+){0,2}owner\b"
            r"|\bowner\s+(?:is|was|remains)\s+"
            r"(?:accepted|established|fixed|known)\b",
            statement,
        )
        for statement in statements
    )
    unknown_owner = any(
        re.search(
            r"\b(?:unknown|unresolved|undecided)\s+owner\b"
            r"(?!\s+(?:internal|private)\b)"
            r"|\bowner\s+(?:is|remains)\s+"
            r"(?:unknown|unresolved|undecided|not yet known)\b",
            statement,
        )
        for statement in statements
    )
    if not known_owner or unknown_owner:
        return ()

    structure_statements = tuple(
        statement
        for statement in statements
        if re.search(r"\bowner\s+(?:internal|private)\b", statement)
        and (
            "implementation structure" in statement
            or re.search(
                r"\b(?:structural|structure)\s+"
                r"(?:alternatives?|choice|decision|tradeoff)\b",
                statement,
            )
        )
    )
    if not structure_statements:
        return ()

    def has_deliberate_separation(statement: str) -> bool:
        return bool(
            re.search(
                r"\b(?:deliberat\w*|intentional\w*)\b"
                r"(?:\s+[a-z0-9]+){0,3}\s+\bseparat\w*\b"
                r"|\bseparat\w*\b(?:\s+[a-z0-9]+){0,3}\s+"
                r"\b(?:deliberat\w*|intentional\w*)\b",
                statement,
            )
        )

    alternatives_bound = any(
        re.search(r"\breus\w*\b", statement)
        and has_deliberate_separation(statement)
        for statement in structure_statements
    )
    if not alternatives_bound:
        return ()

    unresolved_bound = any(
        re.search(r"\b(?:unresolved|undecided|not yet decided)\b", statement)
        for statement in structure_statements
    ) or any(
        re.search(r"\b(?:unresolved|undecided|not yet decided)\b", statement)
        and re.search(
            r"\b(?:alternatives?|choice|decision|reuse|separation|"
            r"structural|structure|tradeoff)\b",
            statement,
        )
        for statement in statements
    )
    if not unresolved_bound:
        return ()

    return (
        "explicit-known-owner",
        "owner-internal-implementation-structure",
        "reuse-and-deliberate-separation-alternatives",
        "unresolved-structure-decision",
    )


def _fixed_refactoring_destination(value: str) -> bool:
    normalized = _normalize_effect_scope(value)
    destination = (
        all(signal in normalized for signal in ("destination owner", "final placement"))
        or "placement were already accepted" in normalized
        or "placement was already accepted" in normalized
    )
    fixed = any(
        signal in normalized
        for signal in (
            "already fixed",
            "already accepted",
            "fixed destination",
            "fixed placement",
        )
    )
    return destination and fixed


def _generated_authority_state(value: str) -> str:
    """Classify editable/generated authority, preserving explicit unknowns."""

    normalized = " ".join(value.casefold().split())
    if re.search(
        r"\bunknown whether\b[^.;!?]{0,240}\b"
        r"(?:template|generated file|derived artifact|checked in artifact)\b",
        normalized,
    ):
        return EFFECT_AMBIGUOUS
    records: list[_EffectRecord] = []
    for scope_id, scope in _bounded_effect_scopes(value):
        authority_subject = any(
            signal in scope
            for signal in (
                "editable template",
                "editable source",
                "generator",
                "generated file",
                "derived artifact",
                "checked in artifact",
                "committed policy",
                "freshness check",
            )
        )
        if not authority_subject:
            continue
        if any(
            signal in scope
            for signal in (
                "unknown whether",
                "authority is unknown",
                "authoritative source is unknown",
                "unknown authority",
            )
        ):
            polarity = EFFECT_AMBIGUOUS
        elif _scope_is_unchanged(scope):
            polarity = EFFECT_UNCHANGED
        elif any(
            signal in scope
            for signal in (
                "editable template",
                "editable source",
                "derived artifact",
                "committed policy",
                "freshness check",
                "are known",
                "is known",
            )
        ):
            polarity = EFFECT_CHANGED
        else:
            polarity = EFFECT_ADJACENT_ONLY
        records.append(("generated-authority", polarity, scope_id))
    return _overall_effect_state(tuple(records))


ROUTE_COHORT_PRECEDENCE = {
    "critical-unknown": 0,
    "ordinary-ambiguity": 0,
    "implementation-preparation": 1,
    "review-logging-risk": 2,
    "review-release-risk": 2,
    "review-reliability-risk": 2,
    "review-security-risk": 2,
    "review-generic": 3,
}
EXPLICIT_ROUTE_PRECEDENCE = 5
FALLBACK_ROUTE_PRECEDENCE = 6
ROUTE_CONTRACT_FIELDS = (
    "path",
    "profile",
    "primary_skill",
    "layer3_skills",
    "review_skill",
)
ROUTE_CANDIDATE_CONTRACT_FIELDS = (
    "artifact_binding_id",
)
ROUTE_CANDIDATE_LAYER3_FIELDS = (
    "eligible_foundation_layer3_skills",
    "eligible_domain_layer3_skills",
    "eligible_layer3_skills",
    "reserved_domain_capacity",
    "layer3_overflow",
)
_BRIEF_REVIEW_BINDING_NAMESPACE_STEM = "cf.brief-review-binding"
_BRIEF_REVIEW_BINDING_VERSION = "cf.brief-review-binding/v1"
_BRIEF_REVIEW_BINDING_FIELDS = (
    "task_id",
    "assignment_id",
    "review_skill",
    "artifact_kind",
    "artifact_id",
    "artifact_sha256",
    "source_state_sha256",
    "currentness_status",
    "currentness_proof_sha256",
    "acceptance_status",
    "acceptance_evidence_sha256",
    "binding_sha256",
)
_BRIEF_REVIEW_COMPATIBLE_SPECIALIST_IDS = frozenset(
    {
        "high-risk-module-boundary-review",
        "high-risk-technology-stack-review",
    }
)
_BRIEF_REVIEW_BINDING_WRITER_IDS = frozenset(
    {
        "engineering-artifact-review",
        "high-risk-architecture-plan",
        *_BRIEF_REVIEW_COMPATIBLE_SPECIALIST_IDS,
    }
)
_LOWER_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_BRIEF_REVIEW_BINDING_TOKEN_PATTERN = re.compile(r"brb1:[0-9a-f]{64}")


def _coalesce_professional_family_matches(
    matches: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Union duplicate semantic-family evidence before owner resolution."""

    evidence_by_family: dict[str, set[str]] = {}
    for match in matches:
        family = match.get("routing_family")
        evidence = match.get("match_evidence")
        if (
            not isinstance(family, str)
            or not family
            or not isinstance(evidence, list)
            or not evidence
            or not all(isinstance(item, str) and item for item in evidence)
        ):
            raise RoutingIntegrityError(
                f"invalid Professional family match {match!r}"
            )
        evidence_by_family.setdefault(family, set()).update(evidence)
    return [
        {
            "routing_family": family,
            "match_evidence": sorted(evidence_by_family[family]),
        }
        for family in sorted(evidence_by_family)
    ]


_TASK_ACTION_RE = re.compile(
    r"\b(?P<verb>add|analy[sz]e|build|change|create|fix|implement|migrate|"
    r"plan|prepare|refactor|repair|select|update|write)\b"
)
_TASK_CLAUSE_BOUNDARY_RE = re.compile(r";|[.!?](?=\s|$)")
_TASK_ACTION_PREFIX_RE = re.compile(
    r"\b(?:can|could|do\s+not|must(?:\s+not)?|need\s+to|needs\s+to|"
    r"never|not\s+to|please|should(?:\s+not)?|to|will(?:\s+not)?)\s*$"
)
_TEST_VALIDATION_TASK_OBJECT_SIGNALS = (
    "regression test",
    "regression tests",
    "test proof",
    "test coverage",
    "validation freshness",
)


@dataclass(frozen=True)
class _TaskSpan:
    normalized: tuple[int, int]
    source: tuple[int, int]


@dataclass(frozen=True)
class _TaskActionNode:
    action_id: str
    statement_id: str
    clause_id: str
    role: str
    verb: str
    polarity: str
    prefix_kind: str
    parent_action_id: str | None
    clause_span: _TaskSpan
    verb_span: _TaskSpan
    prefix_span: _TaskSpan | None
    subject_span: _TaskSpan | None
    object_span: _TaskSpan | None
    referent_marker_span: _TaskSpan | None
    coordinator_span: _TaskSpan | None


@dataclass(frozen=True)
class _TaskObjectNode:
    object_id: str
    parent_action_id: str
    parent_object_id: str | None
    role: str
    span: _TaskSpan
    complete: bool


@dataclass(frozen=True)
class _TaskLexeme:
    lexeme: str
    raw_match_span: _TaskSpan
    legacy_recognized: bool
    disposition: str
    action_id: str | None
    issue_code: str | None


@dataclass(frozen=True)
class _TaskActionIssue:
    code: str
    span: _TaskSpan
    action_id: str | None


@dataclass(frozen=True)
class _TaskActionParse:
    source_text: str
    normalized_text: str
    actions: tuple[_TaskActionNode, ...]
    objects: tuple[_TaskObjectNode, ...]
    lexemes: tuple[_TaskLexeme, ...]
    issues: tuple[_TaskActionIssue, ...]
    blocking_terminal_spans: tuple[_TaskSpan, ...]


@dataclass(frozen=True)
class _ParsedTaskRequest:
    value: str
    task_actions: _TaskActionParse


@dataclass(frozen=True)
class _RoutingBoundaryFacts:
    """One action-local routing snapshot; it never supplies execution level."""

    action_id: str
    clause_id: str
    repository_owner: bool
    filesystem_behavior: str
    path_mutation: str
    writer_identity: str
    writer_trust: str
    sensitive_asset: str
    privileged_consumption: str
    authority_delta: str
    reachable_path: str
    evidence_ids: tuple[str, ...]


_TASK_REFERENT_MARKER_RE = re.compile(r"\b(?P<marker>for|proving)\b")
_TASK_COORDINATOR_SUFFIX_RE = re.compile(
    r"\b(?P<coordinator>and\s+then|then|and|or)\b"
    r"(?P<tail>\s+(?:we\s+)?(?:need\s+to|do\s+not)?)?\s*$"
)
_TASK_REFERENT_PREFIX_SUFFIX_RE = re.compile(
    r"(?:(?P<subject>\S(?:.*\S)?)\s+)?"
    r"(?P<prefix>can|to|need\s+to)\s*$"
)
_TASK_MULTIPLE_PREFIX_RE = re.compile(
    r"\b(?:can|could|need\s+to|needs\s+to|to)\b"
)
_TASK_UNBALANCED_DELIMITERS = ('"', "'")


def _task_span(start: int, end: int) -> _TaskSpan:
    coordinates = (start, end)
    return _TaskSpan(normalized=coordinates, source=coordinates)


def _trimmed_task_span(
    value: str,
    start: int,
    end: int,
) -> _TaskSpan | None:
    while start < end and value[start].isspace():
        start += 1
    while end > start and (
        value[end - 1].isspace()
        or value[end - 1] in ".,;:!?"
    ):
        end -= 1
    return _task_span(start, end) if start < end else None


def _task_statement_id(value: str, offset: int) -> str:
    statement = 1 + len(
        re.findall(r"[.!?;]+", value[:offset])
    )
    return f"statement-{statement}"


def _parse_normalized_task_request(
    value: str,
) -> _ParsedTaskRequest:
    """Parse normalized task actions before effect scopes lose relationships."""

    raw_matches = tuple(_TASK_ACTION_RE.finditer(value))
    action_records: list[dict[str, Any]] = []
    issues: list[_TaskActionIssue] = []

    def add_issue(
        code: str,
        span: _TaskSpan,
        action_id: str | None,
    ) -> None:
        if any(
            issue.code == code
            and issue.span == span
            and issue.action_id == action_id
            for issue in issues
        ):
            return
        issues.append(
            _TaskActionIssue(
                code=code,
                span=span,
                action_id=action_id,
            )
        )

    for delimiter in _TASK_UNBALANCED_DELIMITERS:
        if value.count(delimiter) % 2:
            offset = value.index(delimiter)
            add_issue(
                "unbalanced-delimiter",
                _task_span(offset, offset + 1),
                None,
            )

    for raw_match in raw_matches:
        verb = raw_match.group("verb")
        verb_start, verb_end = raw_match.span()
        role: str | None = None
        polarity = EFFECT_CHANGED
        prefix_kind = "none"
        prefix_span: _TaskSpan | None = None
        subject_span: _TaskSpan | None = None
        referent_marker_span: _TaskSpan | None = None
        coordinator_span: _TaskSpan | None = None
        parent_action_id: str | None = None
        relation_start = verb_start

        statement_boundaries = tuple(
            _TASK_CLAUSE_BOUNDARY_RE.finditer(value[:verb_start])
        )
        statement_start = (
            statement_boundaries[-1].end()
            if statement_boundaries
            else 0
        )
        statement_prefix = value[statement_start:verb_start]
        has_statement_action = any(
            record["verb_start"] >= statement_start
            for record in action_records
        )
        explicit_direct_prefix = re.fullmatch(
            r"\s*(?P<prefix>can|could|do\s+not|must(?:\s+not)?|"
            r"need\s+to|needs\s+to|never|not\s+to|please|"
            r"should(?:\s+not)?|to|will(?:\s+not)?)\s*",
            statement_prefix,
        )
        structural_direct_prefix = (
            _TASK_ACTION_PREFIX_RE.search(statement_prefix.rstrip())
            if not has_statement_action
            else None
        )
        leading_separator = (
            re.search(r",\s*$", statement_prefix)
            if not has_statement_action
            else None
        )
        leading_coordinator = (
            re.search(
                r"\b(?P<coordinator>and|then)\s*$",
                statement_prefix,
            )
            if not has_statement_action
            else None
        )
        if (
            not statement_prefix.strip()
            or explicit_direct_prefix is not None
            or structural_direct_prefix is not None
            or leading_separator is not None
            or leading_coordinator is not None
        ):
            role = "direct"
            prefix_kind = "directive"
            if explicit_direct_prefix is not None:
                prefix_text = explicit_direct_prefix.group("prefix")
                prefix_start = (
                    statement_start
                    + explicit_direct_prefix.start("prefix")
                )
                prefix_span = _task_span(
                    prefix_start,
                    prefix_start + len(prefix_text),
                )
                if any(
                    negator in prefix_text
                    for negator in ("not", "never")
                ):
                    polarity = EFFECT_UNCHANGED
                    prefix_kind = "negative"
                elif prefix_text in {
                    "can",
                    "could",
                    "need to",
                    "needs to",
                    "must",
                    "should",
                    "will",
                }:
                    prefix_kind = "modal"
                elif prefix_text == "to":
                    prefix_kind = "infinitive"
            elif structural_direct_prefix is not None:
                prefix_text = structural_direct_prefix.group(0).strip()
                prefix_start = (
                    statement_start
                    + structural_direct_prefix.start()
                )
                prefix_span = _task_span(
                    prefix_start,
                    statement_start + structural_direct_prefix.end(),
                )
                if any(
                    negator in prefix_text
                    for negator in ("not", "never")
                ):
                    polarity = EFFECT_UNCHANGED
                    prefix_kind = "negative"
                elif prefix_text == "to":
                    prefix_kind = "infinitive"
                else:
                    prefix_kind = "modal"
            elif leading_coordinator is not None:
                coordinator_start = (
                    statement_start
                    + leading_coordinator.start("coordinator")
                )
                coordinator_span = _task_span(
                    coordinator_start,
                    statement_start
                    + leading_coordinator.end("coordinator"),
                )
        elif action_records:
            previous = action_records[-1]
            between_start = previous["verb_end"]
            between = value[between_start:verb_start]
            coordinator = _TASK_COORDINATOR_SUFFIX_RE.search(between)
            if coordinator is not None:
                coordinator_text = coordinator.group("coordinator")
                coordinator_start = (
                    between_start + coordinator.start("coordinator")
                )
                coordinator_end = (
                    between_start + coordinator.end("coordinator")
                )
                coordinator_span = _task_span(
                    coordinator_start,
                    coordinator_end,
                )
                relation_start = coordinator_start
                role = (
                    "ambiguous"
                    if coordinator_text == "or"
                    else "coordinated"
                )
                parent_action_id = action_records[0]["action_id"]
                tail = coordinator.group("tail") or ""
                tail_start = between_start + coordinator.start("tail")
                stripped_tail = tail.strip()
                if stripped_tail.startswith("we "):
                    subject_offset = tail.find("we")
                    subject_span = _task_span(
                        tail_start + subject_offset,
                        tail_start + subject_offset + 2,
                    )
                    stripped_tail = stripped_tail[3:]
                if stripped_tail:
                    prefix_offset = between.rfind(stripped_tail)
                    prefix_span = _task_span(
                        between_start + prefix_offset,
                        between_start + prefix_offset + len(stripped_tail),
                    )
                    if stripped_tail == "do not":
                        polarity = EFFECT_UNCHANGED
                        prefix_kind = "negative"
                    elif stripped_tail == "need to":
                        prefix_kind = "modal"
                if coordinator_text == "or":
                    add_issue(
                        "ambiguous-weak-coordination",
                        coordinator_span,
                        previous["action_id"],
                    )
            else:
                markers = tuple(
                    _TASK_REFERENT_MARKER_RE.finditer(between)
                )
                marker = markers[-1] if markers else None
                if marker is not None:
                    marker_start = between_start + marker.start("marker")
                    marker_end = between_start + marker.end("marker")
                    marker_span = _task_span(marker_start, marker_end)
                    complement = between[marker.end():]
                    prefix = _TASK_REFERENT_PREFIX_SUFFIX_RE.search(
                        complement
                    )
                    if prefix is not None:
                        role = "referent-complement"
                        relation_start = marker_start
                        referent_marker_span = marker_span
                        parent_action_id = previous["action_id"]
                        prefix_text = prefix.group("prefix")
                        prefix_start = (
                            between_start
                            + marker.end()
                            + prefix.start("prefix")
                        )
                        prefix_span = _task_span(
                            prefix_start,
                            prefix_start + len(prefix_text),
                        )
                        prefix_kind = (
                            "infinitive"
                            if prefix_text == "to"
                            else "modal"
                        )
                        subject_text = prefix.group("subject")
                        if subject_text:
                            subject_start = (
                                between_start
                                + marker.end()
                                + prefix.start("subject")
                            )
                            subject_span = _task_span(
                                subject_start,
                                subject_start + len(subject_text),
                            )
                            earlier_prefix = _TASK_MULTIPLE_PREFIX_RE.search(
                                subject_text
                            )
                            if earlier_prefix is not None:
                                role = "ambiguous"
                                add_issue(
                                    "multiple-action-prefixes",
                                    _task_span(
                                        subject_start + earlier_prefix.start(),
                                        prefix_span.normalized[1],
                                    ),
                                    previous["action_id"],
                                )
                        else:
                            role = "ambiguous"
                            add_issue(
                                "missing-referent-subject",
                                prefix_span,
                                previous["action_id"],
                            )
                        if previous["role"] == "referent-complement":
                            add_issue(
                                "unsupported-referent-nesting",
                                marker_span,
                                previous["action_id"],
                            )
                if role is None:
                    infinitive = re.search(r"\bto\s*$", between)
                    if infinitive is not None:
                        role = "coordinated"
                        parent_action_id = action_records[0]["action_id"]
                        relation_start = between_start + infinitive.start()
                        prefix_span = _task_span(
                            relation_start,
                            between_start + infinitive.end(),
                        )
                        prefix_kind = "infinitive"
                        coordinator_span = prefix_span

        if role is None:
            continue
        action_id = f"action-{len(action_records) + 1}"
        action_records.append(
            {
                "action_id": action_id,
                "statement_id": _task_statement_id(value, verb_start),
                "clause_id": f"clause-{len(action_records) + 1}",
                "role": role,
                "verb": verb,
                "polarity": polarity,
                "prefix_kind": prefix_kind,
                "parent_action_id": parent_action_id,
                "verb_start": verb_start,
                "verb_end": verb_end,
                "relation_start": relation_start,
                "prefix_span": prefix_span,
                "subject_span": subject_span,
                "referent_marker_span": referent_marker_span,
                "coordinator_span": coordinator_span,
            }
        )

    actions: list[_TaskActionNode] = []
    objects: list[_TaskObjectNode] = []
    for index, record in enumerate(action_records):
        next_relation = (
            action_records[index + 1]["relation_start"]
            if index + 1 < len(action_records)
            else len(value)
        )
        statement_boundary = _TASK_CLAUSE_BOUNDARY_RE.search(
            value[record["verb_end"]:next_relation],
        )
        clause_end = (
            record["verb_end"] + statement_boundary.start()
            if statement_boundary is not None
            else next_relation
        )
        clause_span = _trimmed_task_span(
            value,
            record["verb_start"],
            clause_end,
        )
        assert clause_span is not None
        object_span = _trimmed_task_span(
            value,
            record["verb_end"],
            clause_end,
        )
        action = _TaskActionNode(
            action_id=record["action_id"],
            statement_id=record["statement_id"],
            clause_id=record["clause_id"],
            role=record["role"],
            verb=record["verb"],
            polarity=record["polarity"],
            prefix_kind=record["prefix_kind"],
            parent_action_id=record["parent_action_id"],
            clause_span=clause_span,
            verb_span=_task_span(
                record["verb_start"],
                record["verb_end"],
            ),
            prefix_span=record["prefix_span"],
            subject_span=record["subject_span"],
            object_span=object_span,
            referent_marker_span=record["referent_marker_span"],
            coordinator_span=record["coordinator_span"],
        )
        actions.append(action)
        if object_span is None:
            add_issue("missing-object", action.verb_span, action.action_id)
            continue
        object_text = value[
            object_span.normalized[0]:object_span.normalized[1]
        ]
        object_node = _TaskObjectNode(
            object_id=f"object-{len(objects) + 1}",
            parent_action_id=action.action_id,
            parent_object_id=None,
            role=(
                "test-object"
                if any(
                    _contains_signal(object_text, signal)
                    for signal in _TEST_VALIDATION_TASK_OBJECT_SIGNALS
                )
                else "ordinary-object"
            ),
            span=object_span,
            complete=True,
        )
        objects.append(object_node)

    action_by_span = {
        action.verb_span.normalized: action
        for action in actions
    }
    blocking_spans: list[_TaskSpan] = []
    lexemes: list[_TaskLexeme] = []
    for raw_match in raw_matches:
        raw_span = _task_span(*raw_match.span())
        action = action_by_span.get(raw_span.normalized)
        if action is not None:
            lexemes.append(
                _TaskLexeme(
                    lexeme=raw_match.group("verb"),
                    raw_match_span=raw_span,
                    legacy_recognized=True,
                    disposition="action-node",
                    action_id=action.action_id,
                    issue_code=None,
                )
            )
            continue

        parent_action = next(
            (
                candidate
                for candidate in reversed(actions)
                if candidate.verb_span.normalized[0] < raw_match.start()
            ),
            None,
        )
        between = (
            value[
                parent_action.verb_span.normalized[1]:raw_match.start()
            ]
            if parent_action is not None
            else value[:raw_match.start()]
        )
        deepest_owning_object = min(
            (
                item
                for item in objects
                if (
                    item.span.normalized[0] <= raw_match.start()
                    and raw_match.end() <= item.span.normalized[1]
                )
            ),
            key=lambda item: (
                item.span.normalized[1] - item.span.normalized[0],
                -item.span.normalized[0],
                item.object_id,
            ),
            default=None,
        )
        background_shadow = bool(
            re.search(r"\bbackground\b", between)
        )
        if background_shadow:
            disposition = "blocking-unconsumed"
            issue_code = "unconsumed-action-lexeme"
            add_issue(issue_code, raw_span, None)
            blocking_spans.append(raw_span)
        elif (
            deepest_owning_object is not None
            and deepest_owning_object.role == "test-object"
        ):
            disposition = "blocking-ambiguous"
            issue_code = None
            blocking_spans.append(raw_span)
        else:
            disposition = "non-action-object-lexeme"
            issue_code = None
        lexemes.append(
            _TaskLexeme(
                lexeme=raw_match.group("verb"),
                raw_match_span=raw_span,
                legacy_recognized=False,
                disposition=disposition,
                action_id=(
                    parent_action.action_id
                    if parent_action is not None
                    else None
                ),
                issue_code=issue_code,
            )
        )

    task_actions = _TaskActionParse(
        source_text=value,
        normalized_text=value,
        actions=tuple(actions),
        objects=tuple(objects),
        lexemes=tuple(lexemes),
        issues=tuple(issues),
        blocking_terminal_spans=tuple(dict.fromkeys(blocking_spans)),
    )
    return _ParsedTaskRequest(value=value, task_actions=task_actions)


def _routing_boundary_fact_snapshots(
    value: str,
    *,
    parsed: _ParsedTaskRequest,
) -> tuple[_RoutingBoundaryFacts, ...]:
    """Build action-local path and security facts without cross-clause joins."""

    text = " ".join(value.casefold().split())
    local_scopes: list[tuple[str, str, str, str, str | None]] = []
    action_scope_by_id: dict[str, str] = {}
    for action in parsed.task_actions.actions:
        if (
            action.role not in {"direct", "coordinated"}
            or action.object_span is None
        ):
            continue
        start = action.verb_span.normalized[0]
        end = action.object_span.normalized[1]
        qualifier = re.match(r"\s*;\s*[^.!?]*", text[end:])
        if qualifier is not None:
            end += qualifier.end()
        action_scope_by_id[action.action_id] = text[start:end]
        local_scopes.append(
            (
                action.action_id,
                action.clause_id,
                action.verb,
                text[start:end],
                action.parent_action_id,
            )
        )
    if not local_scopes and re.match(r"^review\b", text):
        # A review action owns its whole actual-diff object. Connectors within
        # that object separate propositions, not independent task actions.
        local_scopes.append(("scope-0", "scope-0", "review", text, None))
    elif not local_scopes:
        for index, raw_scope in enumerate(
            _EFFECT_STATEMENT_BOUNDARY_RE.split(text)
        ):
            scope = _normalize_effect_scope(raw_scope)
            if re.match(r"^(?:assess|audit|inspect|review)\b", scope):
                local_scopes.append(
                    (
                        f"scope-{index}",
                        f"scope-{index}",
                        "review",
                        scope,
                        None,
                    )
                )

    snapshots: list[_RoutingBoundaryFacts] = []

    def coordinated_negation_denies(
        action_scope: str,
        targets: tuple[str, ...],
    ) -> bool:
        for clause in re.split(r"[.!?;]", action_scope):
            for negation in re.finditer(
                r"\b(?:neither|no|without)\b",
                clause,
            ):
                tail = clause[negation.end():]
                boundary = re.search(
                    r",|\b(?:but|however|yet|is|are|was|were|"
                    r"remains?|stays?|exists?|occurs?|changes?|changed|"
                    r"becomes?|became|will|would|can|could|may|might|"
                    r"must|should)\b",
                    tail,
                )
                noun_list = (
                    tail[:boundary.start()]
                    if boundary is not None
                    else tail
                )
                if not re.search(r"\b(?:and|nor|or)\b", noun_list):
                    continue
                if any(
                    _contains_signal(noun_list, target)
                    for target in targets
                ):
                    return True
        return False

    for action_id, clause_id, action_verb, scope, parent_action_id in local_scopes:
        evidence: list[str] = [
            f"{action_id}:action",
            f"{clause_id}:clause",
        ]
        repository_owner = any(
            signal in scope
            for signal in (
                "repository cli",
                "repository-owned",
                "repository owned",
                "repository tooling",
                "repository tool",
                "internal cli",
                "maintenance utility",
                "monorepo automation",
                "test harness",
                "benchmark harness",
                "compiler plugin",
                "linter plugin",
                "formatter plugin",
            )
        )
        if not repository_owner and parent_action_id is not None:
            parent_scope = action_scope_by_id.get(parent_action_id, "")
            repository_owner = any(
                signal in parent_scope
                for signal in (
                    "repository cli",
                    "repository-owned",
                    "repository owned",
                    "repository tooling",
                    "repository tool",
                    "internal cli",
                    "maintenance utility",
                    "monorepo automation",
                )
            )
        if repository_owner:
            evidence.append(f"{action_id}:repository-owner")

        help_or_copy = any(
            signal in scope
            for signal in (
                "help text",
                "help copy",
                "documentation",
                "description",
                "terminology",
            )
        )
        filesystem_records = _filesystem_process_effect_records(scope)
        explicit_two_axis_unchanged = {
            family
            for family, polarity, _scope_id in filesystem_records
            if polarity == EFFECT_UNCHANGED
        }.issuperset({"filesystem-path", "child-process"})
        filesystem_unchanged = bool(
            re.search(
                r"\bno\b[^.;!?]{0,120}\b(?:path|file(?:system)?)\b"
                r"[^.;!?]{0,120}\bbehaviou?r\b[^.;!?]{0,30}\bchanges?\b",
                scope,
            )
            or re.search(
                r"\b(?:path|file(?:system)?)\b[^.;!?]{0,80}"
                r"\bbehaviou?r\b[^.;!?]{0,30}\b(?:unchanged|not changed)\b",
                scope,
            )
            or explicit_two_axis_unchanged
        )
        path_mutation = "none"
        if not (help_or_copy and filesystem_unchanged):
            if any(
                signal in scope
                for signal in (
                    "--add-dir",
                    "--add dir",
                    "path registration",
                    "path-registration",
                    "registers a",
                    "register a",
                    "register the",
                    "add a bounded local",
                    "add a user-owned",
                    "add a local",
                )
            ) and any(
                subject in scope
                for subject in ("path", "directory", "folder", "--add-dir")
            ):
                path_mutation = "register"
            elif any(
                signal in scope
                for signal in (
                    "atomic replacement",
                    "atomically replace",
                    "atomically swap",
                    "atomic swap",
                    "replace a local",
                    "replace local",
                    "file replacement",
                )
            ):
                path_mutation = "replace"
            elif re.search(
                r"\b(?:create|creation|write)\b[^.;!?]{0,80}"
                r"\b(?:file|path|directory|folder)\b",
                scope,
            ):
                path_mutation = "create"
            elif any(
                signal in scope
                for signal in (
                    "path resolution",
                    "resolve path",
                    "resolve the path",
                )
            ):
                path_mutation = "resolve"
            elif any(
                signal in scope
                for signal in (
                    "path containment",
                    "file containment",
                    "contain the path",
                )
            ):
                path_mutation = "contain"
            elif any(
                signal in scope
                for signal in (
                    "file protection",
                    "permission behavior",
                    "permission policy",
                    "file ownership",
                )
            ):
                path_mutation = "protect"
            elif any(
                signal in scope
                for signal in ("file cleanup", "path cleanup", "cleanup file")
            ):
                path_mutation = "cleanup"
            elif (
                any(
                    subject in scope
                    for subject in ("path", "local file", "directory", "folder")
                )
                and any(
                    state in scope
                    for state in ("unknown", "unresolved", "undecided")
                )
            ):
                path_mutation = "unknown"
        evidence.append(f"{action_id}:path-mutation:{path_mutation}")

        filesystem_state = _filesystem_process_effect_state(filesystem_records)
        if path_mutation == "unknown" or filesystem_state == EFFECT_AMBIGUOUS:
            filesystem_behavior = "ambiguous"
        elif filesystem_unchanged:
            filesystem_behavior = "unchanged"
        elif path_mutation != "none":
            filesystem_behavior = "changed"
        elif filesystem_state == EFFECT_CHANGED:
            filesystem_behavior = "changed"
        elif filesystem_state == EFFECT_UNCHANGED:
            filesystem_behavior = "unchanged"
        else:
            filesystem_behavior = "adjacent"
        evidence.append(
            f"{action_id}:filesystem-behavior:{filesystem_behavior}"
        )

        same_principal = any(
            signal in scope
            for signal in (
                "same os user",
                "same user",
                "same principal",
                "current os account",
                "current account",
                "user-owned",
                "user owned",
            )
        )
        explicit_writer_unknown = bool(
            re.search(
                r"\bwriter(?: identity| trust)?\b[^.;!?]{0,30}"
                r"\b(?:unknown|unresolved|undecided)\b",
                scope,
            )
        )
        same_trust = any(
            signal in scope
            for signal in (
                "no less-trusted writer",
                "no less trusted writer",
                "no lower-trust writer",
                "no lower trust writer",
                "same-trust",
                "same trust",
                "cannot be written by a less-trusted",
                "cannot be written by a less trusted",
            )
        )
        less_trusted = not same_trust and bool(
            re.search(
                r"\b(?:less|lower)[- ]trust(?:ed)?\b"
                r"(?:\s+[a-z0-9-]+){0,2}\s+"
                r"(?:writer|actor|principal)\b|"
                r"\buntrusted(?:\s+[a-z0-9-]+){0,2}\s+"
                r"(?:writer|actor|principal)\b",
                scope,
            )
        )
        writer_identity = (
            "unknown"
            if explicit_writer_unknown
            else "same_principal"
            if same_principal
            else "distinct_principal"
            if less_trusted
            else "unknown"
        )
        writer_trust = (
            "unknown"
            if explicit_writer_unknown
            else "same_trust"
            if same_trust or (same_principal and not less_trusted)
            else "less_trusted"
            if less_trusted
            else "unknown"
        )
        evidence.extend(
            (
                f"{action_id}:writer-identity:{writer_identity}",
                f"{action_id}:writer-trust:{writer_trust}",
            )
        )
        if explicit_writer_unknown:
            evidence.append(f"{action_id}:writer-identity:unknown-explicit")

        sensitive_absent = any(
            signal in scope
            for signal in (
                "non-sensitive",
                "non sensitive",
                "no sensitive data",
                "no personal data",
                "no credentials",
                "no credential",
                "no secrets",
                "no secret",
            )
        ) or coordinated_negation_denies(
            scope,
            (
                "sensitive data",
                "personal data",
                "credential",
                "secret",
                "authentication token",
                "session token",
            ),
        )
        sensitive_unknown = bool(
            re.search(
                r"\b(?:sensitive asset|sensitive data|credential|secret)\b"
                r"[^.;!?]{0,30}\b(?:unknown|unresolved|undecided)\b",
                scope,
            )
        )
        sensitive_present = not sensitive_absent and any(
            signal in scope
            for signal in (
                "sensitive data",
                "personal data",
                "credential",
                "secret",
                "authentication token",
                "session token",
            )
        )
        if (
            not sensitive_absent
            and "telemetry" in scope
            and any(
                signal in scope
                for signal in ("retention", "deletion", "recipient", "export")
            )
        ):
            sensitive_present = True
        sensitive_asset = (
            "unknown"
            if sensitive_unknown
            else "absent"
            if sensitive_absent
            else "present"
            if sensitive_present
            else "unknown"
        )
        evidence.append(f"{action_id}:sensitive-asset:{sensitive_asset}")

        privileged_absent = any(
            signal in scope
            for signal in (
                "unprivileged",
                "non-privileged",
                "non privileged",
                "no privilege elevation",
                "no privileged consumption",
                "no elevated consumer",
            )
        ) or coordinated_negation_denies(
            scope,
            (
                "privilege elevation",
                "privileged consumption",
                "privileged service",
                "privileged consumer",
                "elevated consumer",
                "elevated service",
                "root service",
            ),
        )
        privileged_unknown = bool(
            re.search(
                r"\b(?:privileged|elevated)\b[^.;!?]{0,40}"
                r"\b(?:unknown|unresolved|undecided)\b",
                scope,
            )
        )
        privileged_present = not privileged_absent and any(
            signal in scope
            for signal in (
                "privileged consumption",
                "privileged service",
                "privileged consumer",
                "elevated consumer",
                "elevated service",
                "root service",
            )
        )
        privileged_consumption = (
            "unknown"
            if privileged_unknown
            else "absent"
            if privileged_absent
            else "present"
            if privileged_present
            else "unknown"
        )
        evidence.append(
            f"{action_id}:privileged-consumption:{privileged_consumption}"
        )

        explicit_boundary_analysis = (
            action_verb in {"analyze", "analyse", "prepare", "review"}
            and (
                (
                    "tenant authorization" in scope
                    and any(
                        signal in scope
                        for signal in (
                            "implementation",
                            "object permission",
                            "permission bypass",
                            "security boundaries",
                            "trust boundary",
                            "trust-boundary",
                        )
                    )
                )
                or (
                    "permission bypass" in scope
                    and any(
                        signal in scope
                        for signal in ("material", "risk", "actual diff")
                    )
                )
                or (
                    "authentication" in scope
                    and "authorization" in scope
                    and any(
                        signal in scope
                        for signal in ("boundary", "handoff", "decision")
                    )
                )
            )
        )
        if explicit_boundary_analysis:
            evidence.append(f"{action_id}:explicit-boundary-analysis")

        authority_unknown = bool(
            re.search(
                r"\b(?:authority|authorization|permission)\b[^.;!?]{0,40}"
                r"\b(?:unknown|unresolved|undecided)\b",
                scope,
            )
        )
        if authority_unknown:
            authority_delta = "unknown"
            evidence.append(f"{action_id}:authority:unknown-explicit")
        elif any(
            signal in scope
            for signal in (
                "authority remains unchanged",
                "authority stays unchanged",
                "authority is unchanged",
                "authorization remains unchanged",
                "permission behavior remains unchanged",
                "no authority change",
                "no authorization change",
            )
        ):
            authority_delta = "unchanged"
        elif any(
            signal in scope
            for signal in (
                "authority is reduced",
                "authority reduced",
                "restricts an existing",
                "restriction of an existing",
                "revokes",
                "closes the boundary",
                "tightens the boundary",
                "hardens the boundary",
            )
        ):
            authority_delta = "reduced"
        elif any(
            signal in scope
            for signal in (
                "authority expands",
                "authority is expanded",
                "grants access",
                "broadens access",
                "permission bypass",
                "privilege elevation",
            )
        ) and not privileged_absent:
            authority_delta = "expanded"
        elif (
            action_verb in {"analyze", "analyse", "review"}
            and "boundary" in scope
            and any(signal in scope for signal in ("existing", "proved", "proven"))
        ):
            authority_delta = "existing_boundary_review"
        else:
            authority_delta = "unknown"
        evidence.append(f"{action_id}:authority-delta:{authority_delta}")

        reachable_denied = any(
            signal in scope
            for signal in (
                "no reachable",
                "not reachable",
                "cannot reach",
                "denied from reaching",
                "no concrete privileged",
                "no concrete sensitive",
                "no security sink",
                "reachable path is denied",
            )
        )
        reachable_unknown = bool(
            re.search(
                r"\breachable(?: impact)? path\b[^.;!?]{0,40}"
                r"\b(?:unknown|unresolved|undecided)\b",
                scope,
            )
        )
        reachable_proved = not reachable_denied and (
            explicit_boundary_analysis
            or
            any(
                signal in scope
                for signal in (
                    "proved reachable",
                    "proven reachable",
                    "existing reachable",
                    "reachable authorization boundary",
                    "reachable permission boundary",
                    "reachable trust boundary",
                    "reaching a privileged",
                    "reaching the privileged",
                    "writer controls content consumed",
                    "can replace content that a privileged",
                    "can replace a local path before privileged",
                )
            )
            or (
                "reachable" in scope
                and any(
                    sink in scope
                    for sink in ("privileged", "sensitive", "credential", "secret")
                )
            )
        )
        reachable_path = (
            "unknown"
            if reachable_unknown
            else "denied"
            if reachable_denied
            else "proved"
            if reachable_proved
            else "unknown"
        )
        evidence.append(f"{action_id}:reachable-path:{reachable_path}")

        security_behavior_unchanged = bool(
            re.search(
                r"\b(?:credential|session|token|secret|security|privacy)"
                r"(?:\s+[a-z0-9-]+){0,8}\s+behaviou?r(?:s)?\b"
                r"[^.;!?]{0,30}\b(?:is|are|remains?|stays?)\b"
                r"[^.;!?]{0,15}\b(?:all\s+)?unchanged\b",
                scope,
            )
            or (
                any(
                    signal in scope
                    for signal in (
                        "credential",
                        "session",
                        "token",
                        "secret",
                        "security",
                        "privacy",
                    )
                )
                and re.search(
                    r"\bbehaviou?r(?:s)?\s+"
                    r"(?:is|are|remains?|stays?)\s+"
                    r"(?:all\s+)?unchanged\b",
                    scope,
                )
            )
            or "security behavior remains unchanged" in scope
            or "lifecycle behavior remains unchanged" in scope
        )
        sensitive_lifecycle_unchanged = bool(
            re.search(
                r"\bno\b[^.;!?]{0,80}"
                r"\b(?:retention|sharing|recipient|disclosure|deletion)\b"
                r"[^.;!?]{0,40}\bchanges?\b",
                scope,
            )
        )
        if (
            not security_behavior_unchanged
            and
            not sensitive_lifecycle_unchanged
            and
            sensitive_asset == "present"
            and any(
                signal in scope
                for signal in (
                    "collection",
                    "collects",
                    "access",
                    "disclosure",
                    "discloses",
                    "processing",
                    "retention",
                    "deletion",
                    "recipient",
                    "export",
                )
            )
        ):
            evidence.append(f"{action_id}:sensitive-lifecycle-change")
        if (
            not security_behavior_unchanged
            and
            not (
                "secret rotation" in scope
                and "no cryptographic construction change" in scope
            )
            and
            sensitive_asset == "present"
            and any(
                signal in scope
                for signal in (
                    "credential lifecycle",
                    "session lifecycle",
                    "token validation",
                    "secret rotation",
                    "credential rotation",
                    "session revocation",
                )
            )
        ):
            evidence.append(f"{action_id}:credential-lifecycle-change")
        if explicit_boundary_analysis or any(
            signal in scope
            for signal in (
                "trust boundary",
                "authorization boundary",
                "permission boundary",
                "permission bypass",
                "privacy boundary",
                "credential boundary",
                "secret boundary",
                "security boundary",
            )
        ):
            evidence.append(f"{action_id}:boundary-signal")
        for signal, material_evidence in (
            ("tenant authorization", "material-tenant-authorization"),
            ("tenant isolation", "material-tenant-isolation"),
            ("permission bypass", "material-permission-boundary"),
            ("permission boundary", "material-permission-boundary"),
            ("object permission", "material-permission-boundary"),
            ("trust boundary", "material-trust-boundary"),
            ("trust-boundary", "material-trust-boundary"),
        ):
            if signal in scope:
                evidence.append(f"{action_id}:{material_evidence}")

        snapshots.append(
            _RoutingBoundaryFacts(
                action_id=action_id,
                clause_id=clause_id,
                repository_owner=repository_owner,
                filesystem_behavior=filesystem_behavior,
                path_mutation=path_mutation,
                writer_identity=writer_identity,
                writer_trust=writer_trust,
                sensitive_asset=sensitive_asset,
                privileged_consumption=privileged_consumption,
                authority_delta=authority_delta,
                reachable_path=reachable_path,
                evidence_ids=tuple(dict.fromkeys(evidence)),
            )
        )
    return tuple(snapshots)


def _security_boundary_is_proved(facts: _RoutingBoundaryFacts) -> bool:
    """Return whether one snapshot proves a routable Security boundary."""

    evidence = set(facts.evidence_ids)
    less_trusted_reachable_sink = (
        facts.writer_trust == "less_trusted"
        and facts.reachable_path == "proved"
        and (
            facts.privileged_consumption == "present"
            or facts.sensitive_asset == "present"
        )
    )
    sensitive_lifecycle = any(
        item.endswith(
            ("sensitive-lifecycle-change", "credential-lifecycle-change")
        )
        for item in evidence
    )
    reachable_boundary_hardening = (
        facts.reachable_path == "proved"
        and facts.authority_delta in {
            "reduced",
            "existing_boundary_review",
        }
        and any(item.endswith("boundary-signal") for item in evidence)
    )
    explicit_boundary_analysis = (
        facts.reachable_path == "proved"
        and any(
            item.endswith("explicit-boundary-analysis")
            for item in evidence
        )
    )
    same_principal_nonmaterial = (
        facts.writer_identity == "same_principal"
        and facts.writer_trust == "same_trust"
        and facts.sensitive_asset == "absent"
        and facts.privileged_consumption == "absent"
        and facts.authority_delta in {"unchanged", "reduced"}
    )
    return bool(
        sensitive_lifecycle
        or reachable_boundary_hardening
        or explicit_boundary_analysis
        or (less_trusted_reachable_sink and not same_principal_nonmaterial)
    )


def _security_boundary_has_explicit_unknown(
    facts: _RoutingBoundaryFacts,
) -> bool:
    """Return whether one boundary signal has an explicit ordinary unknown."""

    return (
        any(item.endswith("boundary-signal") for item in facts.evidence_ids)
        or facts.repository_owner
    ) and any(
        item.endswith(
            (
                "writer-identity:unknown-explicit",
                "authority:unknown-explicit",
            )
        )
        for item in facts.evidence_ids
    )


def _parsed_task_objects_are_test_validation_only(
    task: _TaskActionParse,
) -> bool:
    """Return whether every changed direct/coordinated action owns tests."""

    changed_actions = [
        action
        for action in task.actions
        if action.role in {"direct", "coordinated"}
        and action.polarity == EFFECT_CHANGED
    ]
    if not changed_actions:
        return False
    objects_by_action = {
        item.parent_action_id: item
        for item in task.objects
    }
    return all(
        action.action_id in objects_by_action
        and objects_by_action[action.action_id].role == "test-object"
        and objects_by_action[action.action_id].complete
        for action in changed_actions
    )


def _task_action_matches(scope: str) -> tuple[re.Match[str], ...]:
    """Return controlling task actions without treating object nouns as verbs."""

    return tuple(
        action_match
        for action_match in _TASK_ACTION_RE.finditer(scope)
        if (
            action_match.start() == 0
            or _TASK_ACTION_PREFIX_RE.search(
                scope[: action_match.start()].rstrip()
            )
            is not None
        )
    )


def _task_action_intent(text: str) -> dict[str, bool]:
    """Return the shared clause-local action intent used by route classifiers."""

    value = " ".join(text.casefold().split())
    implementation_records: list[_EffectRecord] = []
    audit_analysis_records: list[_EffectRecord] = []
    audit_implementation_records: list[_EffectRecord] = []
    analysis_action = False
    preparation_action = False

    def action_is_negated(prefix: str) -> bool:
        return _scope_is_unchanged(prefix) or bool(
            re.search(
                r"\b(?:(?:do|must|should|will)\s+not|never|not\s+to)\s*$",
                prefix,
            )
        )

    for scope_id, scope in _bounded_effect_scopes(value):
        action_matches = _task_action_matches(scope)
        if not action_matches:
            continue
        controlling_verb = action_matches[0].group("verb")
        analysis_scope = controlling_verb in ("analyze", "analyse")
        preparation_scope = controlling_verb == "prepare"
        analysis_action = analysis_action or analysis_scope
        preparation_action = preparation_action or (
            (
                preparation_scope
                and any(
                    subject in scope
                    for subject in ("implementation", "repair")
                )
            )
            or (
                analysis_scope
                and any(
                    subject in scope
                    for subject in ("implementation", "repair")
                )
                and "before editing" in scope
            )
        )
        controlling_prefix = scope[: action_matches[0].start()].rstrip()
        controlling_negated = action_is_negated(controlling_prefix)
        if (
            analysis_scope
            and any(
                subject in scope
                for subject in (
                    "audit evidence integrity",
                    "tamper evident audit",
                )
            )
        ):
            audit_analysis_records.append(
                (
                    "audit-analysis",
                    (
                        EFFECT_UNCHANGED
                        if controlling_negated
                        else EFFECT_CHANGED
                    ),
                    scope_id,
                )
            )
        if analysis_scope or preparation_scope:
            continue
        for action_match in action_matches:
            if (
                action_match.group("verb") == "plan"
                and "accepted" not in scope
            ):
                continue
            prefix = scope[: action_match.start()].rstrip()
            negated = action_is_negated(prefix)
            polarity = (
                EFFECT_UNCHANGED if negated else EFFECT_CHANGED
            )
            implementation_records.append(
                ("task-implementation", polarity, scope_id)
            )
            if any(
                subject in scope
                for subject in (
                    "audit evidence integrity",
                    "tamper evident audit",
                )
            ):
                audit_implementation_records.append(
                    ("audit-implementation", polarity, scope_id)
                )
    if _owner_placement_has_requested_mutation(value):
        implementation_records.append(
            ("task-implementation", EFFECT_CHANGED, -1)
        )
    implementation_state = _overall_effect_state(
        tuple(implementation_records)
    )
    audit_analysis_state = _overall_effect_state(
        tuple(audit_analysis_records)
    )
    audit_implementation_state = _overall_effect_state(
        tuple(audit_implementation_records)
    )
    return {
        "analysis": analysis_action,
        "audit_analysis": audit_analysis_state == EFFECT_CHANGED,
        "audit_analysis_ambiguous": (
            audit_analysis_state == EFFECT_AMBIGUOUS
        ),
        "audit_implementation": (
            audit_implementation_state == EFFECT_CHANGED
        ),
        "audit_implementation_ambiguous": (
            audit_implementation_state == EFFECT_AMBIGUOUS
        ),
        "implementation": implementation_state == EFFECT_CHANGED,
        "implementation_ambiguous": (
            implementation_state == EFFECT_AMBIGUOUS
        ),
        "preparation": preparation_action,
    }


def _coordinated_implementation_change_scopes(
    value: str,
) -> tuple[str, ...]:
    """Inherit one leading implementation action only across local objects."""

    changed: list[str] = []
    for statement in _EFFECT_STATEMENT_BOUNDARY_RE.split(
        value.casefold()
    ):
        scopes = tuple(
            scope
            for _scope_id, scope in _bounded_effect_scopes(statement)
        )
        if not scopes:
            continue
        leading_action = _task_action_intent(scopes[0])
        inherit_implementation = (
            leading_action["implementation"]
            and not leading_action["implementation_ambiguous"]
        )
        for index, scope in enumerate(scopes):
            if _independent_change_scope(scope):
                changed.append(scope)
                continue
            if (
                index > 0
                and inherit_implementation
                and not _task_action_matches(scope)
                and not _explicit_non_domain_change(scope)
                and not _scope_is_unchanged(scope)
                and not re.search(
                    r"\b(?:background(?:\s+context)?|context)\s+only\b",
                    scope,
                )
            ):
                changed.append(scope)
    return tuple(changed)


def _changed_task_objects_are_test_validation_only(
    changed_scopes: tuple[str, ...],
) -> bool:
    """Return whether every changed task object is a test artifact."""

    test_object_seen = False
    referent_context = False
    for scope in changed_scopes:
        action_matches = _task_action_matches(scope)
        if not action_matches:
            if not referent_context:
                return False
            continue
        action_intent = _task_action_intent(scope)
        if action_intent["implementation_ambiguous"]:
            return False
        if not action_intent["implementation"]:
            referent_context = False
            continue
        raw_matches = tuple(_TASK_ACTION_RE.finditer(scope))
        recognized_action_starts = {
            match.start() for match in action_matches
        }
        referent_context = False
        same_scope_subordinate = False
        index = 0
        while index < len(raw_matches):
            action_match = raw_matches[index]
            object_end = (
                raw_matches[index + 1].start()
                if index + 1 < len(raw_matches)
                else len(scope)
            )
            object_scope = scope[action_match.end():object_end].strip()
            recognized_action = (
                action_match.start() in recognized_action_starts
            )
            consume_subordinate = (
                same_scope_subordinate and recognized_action
            )
            same_scope_subordinate = False
            if consume_subordinate:
                referent_context = False
                index += 1
                continue
            if not object_scope:
                if (
                    not recognized_action
                    and index + 1 == len(raw_matches)
                ):
                    index += 1
                    continue
                return False
            test_object = any(
                _contains_signal(object_scope, signal)
                for signal in _TEST_VALIDATION_TASK_OBJECT_SIGNALS
            )
            if (
                not test_object
                and index + 1 < len(raw_matches)
                and raw_matches[index + 1].start()
                not in recognized_action_starts
            ):
                following_index = index + 1
                following_end = (
                    raw_matches[following_index + 1].start()
                    if following_index + 1 < len(raw_matches)
                    else len(scope)
                )
                coalesced_scope = scope[
                    action_match.end():following_end
                ].strip()
                test_object = any(
                    _contains_signal(coalesced_scope, signal)
                    for signal in _TEST_VALIDATION_TASK_OBJECT_SIGNALS
                )
                if test_object:
                    object_scope = coalesced_scope
                    index = following_index
            if not test_object:
                return False
            test_object_seen = True
            referent_match = re.search(
                r"\b(?:for|proving)\b",
                object_scope,
            )
            referent_context = referent_match is not None
            if referent_match is not None:
                complement = object_scope[referent_match.end():].strip()
                prefix_match = _TASK_ACTION_PREFIX_RE.search(complement)
                same_scope_subordinate = (
                    prefix_match is not None
                    and len(
                        complement[:prefix_match.start()].split()
                    )
                    <= 1
                )
            index += 1
    return test_object_seen


def _classify_professional_families(
    value: str,
    parsed: _ParsedTaskRequest,
) -> list[dict[str, Any]]:
    """Classify changed implementation surfaces into semantic owner families."""

    effect_statements: list[str] = []
    projected_changed_scopes: list[str] = []
    for statement in _EFFECT_STATEMENT_BOUNDARY_RE.split(value):
        projected_statement = statement
        tail_anti = re.search(
            r"\s+with\s+no\s+[^.;!?]{1,80}$",
            statement,
        )
        if tail_anti is not None and _scope_is_unchanged(
            _normalize_effect_scope(statement[tail_anti.start():])
        ):
            candidate = " ".join(
                statement[: tail_anti.start()].split()
            )
            candidate_action_matches = _task_action_matches(candidate)
            candidate_post_action_subject = (
                _normalize_effect_scope(
                    candidate[candidate_action_matches[0].end():]
                )
                if candidate_action_matches
                else ""
            )
            candidate_intent = _task_action_intent(candidate)
            if (
                candidate
                and candidate_post_action_subject
                and candidate_intent["implementation"]
                and not candidate_intent["implementation_ambiguous"]
                and not _scope_is_unchanged(candidate)
            ):
                projected_statement = candidate
                projected_changed_scopes.append(candidate)
        effect_scopes: list[str] = []
        for _scope_id, scope in _bounded_effect_scopes(projected_statement):
            if not _scope_is_unchanged(scope):
                effect_scopes.append(scope)
                continue
            without_inline_anti = _normalize_effect_scope(
                re.sub(
                    r"\bwith\s+no\b[^.;!?]{0,80}?\bbehaviou?r\b"
                    r"(?:\s+changes?)?",
                    " ",
                    scope,
                )
            )
            remainder_intent = _task_action_intent(without_inline_anti)
            if (
                without_inline_anti != scope
                and remainder_intent["implementation"]
                and not remainder_intent["implementation_ambiguous"]
                and not _scope_is_unchanged(without_inline_anti)
            ):
                effect_scopes.append(without_inline_anti)
        if effect_scopes:
            effect_statements.append(" and ".join(effect_scopes))
    effect_value = " ; ".join(effect_statements)
    action_intent = _task_action_intent(value)
    implementation_action = action_intent["implementation"]
    preparation_action = action_intent["preparation"]
    action = implementation_action or preparation_action
    documentation_only = (
        value.startswith("update ")
        and ("documentation" in value or "comments" in value)
    ) or any(
        signal in value
        for signal in (
            "documentation-only",
            "documentation only",
            "docs only",
            "without editing anything",
        )
    )
    review_only = value.startswith("review ") or bool(
        re.search(r"\bindependent\s+review\b", value)
    )
    results: list[dict[str, Any]] = []

    def add(
        family: str,
        subject: bool,
        *,
        anti: bool = False,
        evidence: tuple[str, ...] = (),
    ) -> None:
        if (
            action
            and subject
            and not (anti or documentation_only or review_only)
            and not (
                family == "test-validation"
                and parsed.task_actions.issues
            )
            and (
                not test_validation_task_only
                or family == "test-validation"
            )
        ):
            results.append(
                {
                    "routing_family": family,
                    "match_evidence": sorted(
                        {
                            "effect-changed",
                            (
                                "explicit-implementation-action"
                                if implementation_action
                                else "explicit-preparation-action"
                            ),
                            *evidence,
                        }
                    ),
                }
            )

    changed_scopes = _coordinated_implementation_change_scopes(
        effect_value
    )
    changed_scopes = tuple(
        dict.fromkeys((*changed_scopes, *projected_changed_scopes))
    )
    test_validation_task_only = (
        _parsed_task_objects_are_test_validation_only(
            parsed.task_actions
        )
    )
    backend_subject = _backend_implementation_subject(effect_value)
    add(
        "backend",
        backend_subject,
        anti=(
            bool(re.search(r"\bfrontend\s+only\b", value))
            or "source only" in value
            or "source inspection" in value
            or bool(
                re.search(
                    r"\b(?:backend|service|worker)\b[^.;!?]{0,100}"
                    r"\bbehavior\b[^.;!?]{0,40}\bunchanged\b",
                    value,
                )
            )
            or "retry idempotency" in value
            or bool(
                re.search(
                    r"\bpure\s+backend\b[^.;!?]{0,80}\bregression\s+test\b",
                    value,
                )
            )
        ),
        evidence=("backend-surface",),
    )
    frontend_subject = any(
        signal in effect_value
        for signal in (
            "browser frontend",
            "frontend component",
            "browser component",
            "web component",
            "pwa",
        )
    )
    add(
        "frontend",
        frontend_subject,
        anti=(
            "without implementation" in value
            or "design exploration" in value
            or bool(
                re.search(
                    r"\bmigrate\b[^.;!?]{0,100}\bpwa\b"
                    r"[^.;!?]{0,100}\bto\b[^.;!?]{0,80}\b"
                    r"(?:android|ios|ipados|installed)\b",
                    value,
                )
            )
        ),
        evidence=("browser-ui-surface",),
    )
    installed_subject = any(
        _installed_client_scope_subject(scope)
        and not _backend_implementation_subject(scope)
        for scope in changed_scopes
    )
    add(
        "installed-client",
        installed_subject,
        anti=(
            "pwa-only" in value
            or "pwa only" in value
            or "browser-only" in value
            or "browser only" in value
            or "no installed-client target" in value
            or "no installed-client surface" in value
            or bool(
                re.search(
                    r"\bwithout\s+(?:a\s+)?confirmed\b[^.;!?]{0,80}\btarget\b",
                    value,
                )
            )
            or bool(
                re.search(
                    r"\b(?:android|ios|ipados|installed[- ]client|macos|"
                    r"windows|linux\s+desktop)\b[^.;!?]{0,100}"
                    r"\bbehavior\b[^.;!?]{0,40}\bunchanged\b",
                    value,
                )
            )
            or any(
                signal in value
                for signal in (
                    "store approval",
                    "release approval",
                    "rollback approval",
                )
            )
        ),
        evidence=("installed-application-surface",),
    )
    middleware_subject = any(
        signal in effect_value
        for signal in (
            "database",
            "middleware",
            "queue",
            "cache",
            "search index",
            "search cluster",
        )
    )
    add(
        "data-middleware",
        middleware_subject,
        anti=(
            bool(re.search(r"\bno\s+middleware\s+impact\b", value))
            or bool(re.search(r"\bunrelated\s+source\s+inspection\b", value))
            or "terminology" in value
            or (
                "already-decided retry-count/backoff constant" in value
                and all(
                    boundary in value
                    for boundary in (
                        "retry identity",
                        "idempotency",
                        "replay",
                        "lease ownership",
                        "terminal resolution",
                        "queue topology",
                        "failure contract",
                        "cross-service workflow",
                    )
                )
                and "are unchanged" in value
            )
        ),
        evidence=("middleware-surface",),
    )
    integration_subject = any(
        signal in effect_value
        for signal in (
            "external integration",
            "integration contract",
            "cross worker",
            "shared contract",
            "webhook integration",
        )
    )
    add(
        "integration",
        integration_subject and "accepted" in effect_value,
        anti=(
            "no integration edge" in value
            or bool(re.search(r"\bunrelated\s+source\s+inspection\b", value))
        ),
        evidence=("integration-edge",),
    )
    repository_subject = (
        "repository" in effect_value
        and any(
            signal in effect_value
            for signal in (
                "generator",
                "compiler",
                "linter",
                "formatter",
                "harness",
                "internal cli",
                "repository cli",
                "automation",
                "maintenance utility",
                "tooling",
            )
        )
    )
    add(
        "repository-tooling",
        repository_subject,
        anti=(
            any(
                signal in value
                for signal in (
                    "product business logic",
                    "production mutation",
                    "production deployment",
                    "routing control",
                )
            )
            or "tooling is unchanged" in value
        ),
        evidence=("repository-developer-tool",),
    )
    infrastructure_subject = any(
        signal in effect_value
        for signal in (
            "terraform",
            "opentofu",
            "cloudformation",
            "pulumi",
            "kustomize",
            "helm chart",
            "helm source",
            "infrastructure source",
            "infrastructure script",
            "cloud iam",
            "environment definition",
            "kubernetes manifest",
        )
    )
    add(
        "platform-infrastructure",
        infrastructure_subject,
        anti=any(
            signal in value
            for signal in (
                "production apply",
                "deployment approval",
                "release approval",
                "rollback approval",
            )
        ),
        evidence=("infrastructure-definition",),
    )
    testing_subject = any(
        signal in effect_value
        for signal in _TEST_VALIDATION_TASK_OBJECT_SIGNALS
    )
    add(
        "test-validation",
        testing_subject
        and (
            action
            or value.startswith("select ")
        ),
        anti=(
            bool(re.search(r"\bno\s+material\s+change\b", value))
            or "already fresh and complete" in value
        ),
        evidence=("behavior-proof-surface",),
    )
    logging_subject = any(
        signal in effect_value
        for signal in (
            "implement logs",
            "logging schema",
            "structured log",
            "redacted logging",
            "diagnostic",
        )
    ) or bool(
        re.search(r"\bstructured\b[^.;!?]{0,60}\blogs?\b", effect_value)
    ) or (
        action_intent["audit_implementation"]
        and any(
            subject in effect_value
            for subject in (
                "audit evidence integrity",
                "tamper evident audit",
            )
        )
    )
    add(
        "logging",
        logging_subject,
        anti=(
            bool(re.search(r"\bno\s+logging\s+impact\b", value))
            or "self review" in value
        ),
        evidence=("diagnostic-record-surface",),
    )
    return _coalesce_professional_family_matches(results)


def classify_professional_families(
    text: str,
) -> list[dict[str, Any]]:
    """Classify changed implementation surfaces into semantic owner families."""

    if isinstance(text, _ParsedTaskRequest):
        return _classify_professional_families(text.value, text)
    value = " ".join(text.casefold().split())
    parsed = _parse_normalized_task_request(value)
    return _classify_professional_families(value, parsed)


_RUNTIME_POLICY_IMPLEMENTATION_FAMILIES = frozenset(
    {
        "backend",
        "data-middleware",
        "frontend",
        "installed-client",
        "integration",
        "platform-infrastructure",
        "repository-tooling",
    }
)


def _technology_stack_commitment_risk(text: str) -> bool:
    """Return one material framework/platform/datastore commitment."""

    if any(
        signal in text
        for signal in (
            "no new technology-stack commitment",
            "technology choices are fixed",
            "technology stack meets a documented constraint",
            "remain fixed with no new",
            "no framework, platform, datastore, or managed-service change is proposed",
        )
    ):
        return False
    technology = any(
        signal in text
        for signal in (
            "new web framework",
            "new framework",
            "new deployment platform",
            "new platform",
            "new datastore",
            "managed datastore",
            "new managed service",
        )
    )
    commitment = any(
        signal in text
        for signal in (
            "commits",
            "commitment",
            "migration",
            "operational ownership",
            "exit costs",
        )
    )
    return technology and commitment


def _major_module_boundary_review(text: str) -> bool:
    """Return one material accepted-Brief module boundary review."""

    return (
        "material architecture critical path" in text
        and "module ownership" in text
        and any(
            signal in text
            for signal in (
                "public surface",
                "dependency direction",
                "shared-state authority",
            )
        )
    )


def _configuration_runtime_policy_risk(text: str) -> bool:
    """Return exact behavior-changing runtime configuration evidence."""

    if "runtime configuration policy" not in text:
        return False
    if any(
        signal in text
        for signal in (
            "without changing any runtime behavior",
            "runtime behavior, defaults, flags, modes, and reload semantics do not change",
            "typed runtime defaults, feature flags, modes, hot reload, and config precedence remain unchanged",
        )
    ):
        return False
    return any(
        signal in text
        for signal in (
            "typed",
            "default",
            "precedence",
            "feature flag",
            "mode",
            "hot reload",
            "kill switch",
        )
    )


def _dependency_package_risk(text: str) -> bool:
    """Return exact material dependency-risk decision evidence."""

    package_subject = any(
        signal in text
        for signal in (
            "dependency graph change",
            "install a new package",
            "new package because of a current capability gap",
        )
    )
    if not package_subject:
        return False

    vulnerability_absent = any(
        signal in text
        for signal in (
            "no vulnerability",
            "no known vulnerability",
        )
    )
    vulnerability_risk = not vulnerability_absent and any(
        signal in text
        for signal in (
            "vulnerability reachability",
            "vulnerability remediation",
            "dependency remediation",
            "package remediation",
        )
    )
    independent_material_risk = any(
        signal in text
        for signal in (
            "incompatible license decision",
            "incompatible-license decision",
            "license incompatibility decision",
            "package-provenance trust failure",
            "package provenance trust failure",
            "provenance trust failure",
            "signature verification failure",
            "signature trust failure",
            "package provenance and signature verification",
            "malicious-package detection",
            "malicious package detection",
            "install-time execution hook",
            "malicious install hook",
            "sbom exception",
            "package-risk acceptance",
            "accepted dependency risk",
            "accepted package risk",
        )
    )
    return vulnerability_risk or independent_material_risk


def _accessibility_behavior_requested(value: str) -> bool:
    """Return one explicit UI inclusive-interaction behavior change."""

    interaction_signals = (
        "accessibility behavior",
        "accessibility focus",
        "accessibility semantics",
        "accessible name",
        "assistive technology",
        "compose semantics",
        "display scaling",
        "d pad input",
        "d pad navigation",
        "font scaling",
        "keyboard focus",
        "keyboard input",
        "keyboard navigation",
        "interaction alternative",
        "interaction alternatives",
        "pointer alternative",
        "pointer alternatives",
        "screen reader",
        "screen-reader",
        "switch access",
        "talkback",
        "voice access",
        "voiceover",
    )
    ui_surfaces = (
        "android",
        "app",
        "application",
        "browser",
        "desktop",
        "flutter",
        "form",
        "frontend",
        "ios",
        "ipados",
        "macos",
        "react native",
        "screen",
        "user interface",
        "view",
        "web",
        "window",
        "windows",
    )
    excluded_phrases = (
        "accessibility api names only",
        "accessibility api name only",
        "no accessibility behavior",
        "no user interface",
        "talkback api names only",
        "talkback api name only",
    )
    clauses = _domain_clauses(value)
    for index, clause in enumerate(clauses):
        scope = _normalize_effect_scope(clause)
        adjacent_scopes = tuple(
            _normalize_effect_scope(clauses[position])
            for position in (index - 1, index + 1)
            if 0 <= position < len(clauses)
        )
        identifier_rename = re.search(
            r"\b(?:rename|renaming)\b.{0,100}\b"
            r"(?:api(?:\s+(?:name|symbol|constant))?|symbol|constant)\b|"
            r"\b(?:api(?:\s+(?:name|symbol|constant))?|symbol|constant)\b"
            r".{0,100}\b(?:rename|renaming)\b",
            scope,
        )
        runtime_unchanged = any(
            _scope_is_unchanged(candidate)
            or _explicit_absence_or_unchanged(candidate)
            for candidate in (scope, *adjacent_scopes)
        )
        if (
            not scope
            or _documentation_only(scope)
            or _explicit_non_domain_change(scope)
            or _scope_is_unchanged(scope)
            or _backend_implementation_subject(scope)
            or any(phrase in scope for phrase in excluded_phrases)
            or (identifier_rename is not None and runtime_unchanged)
        ):
            continue
        if not any(_contains_signal(scope, signal) for signal in ui_surfaces):
            continue
        interaction = any(
            _contains_signal(scope, signal) for signal in interaction_signals
        )
        dynamic_type_contract = (
            _contains_signal(scope, "dynamic type")
            and any(
                _contains_signal(scope, signal)
                for signal in (
                    "font",
                    "font scaling",
                    "screen",
                    "text",
                    "text scaling",
                    "user interface",
                    "view",
                )
            )
        )
        input_alternative_contract = (
            any(
                _contains_signal(scope, signal)
                for signal in (
                    "d pad",
                    "drag",
                    "gesture",
                    "keyboard",
                    "interaction",
                    "pointer",
                    "swipe",
                    "touch",
                )
            )
            and any(
                _contains_signal(scope, signal)
                for signal in (
                    "alternative",
                    "focus",
                    "input",
                    "navigation",
                    "operation",
                )
            )
        )
        change_semantics = _independent_change_scope(scope) or bool(
            re.search(
                r"\b(?:accessibility|behaviou?r|focus|input|navigation|"
                r"representation|semantics?|scaling)\b.{0,100}\b"
                r"(?:change|changed|changes|fix|repair|update)\b|"
                r"\b(?:change|changed|changes|fix|repair|update)\b.{0,100}\b"
                r"(?:accessibility|behaviou?r|focus|input|navigation|"
                r"representation|semantics?|scaling)\b",
                scope,
            )
        )
        if (
            change_semantics
            and (interaction or dynamic_type_contract or input_alternative_contract)
        ):
            return True
    return False


def _implementation_owner_layer3(
    family: str,
    text: str,
    *,
    audit_implementation: bool,
    filesystem_effect_state: str,
    node_effect_state: str,
    structure_states: dict[str, str],
) -> list[str]:
    """Derive a bounded Layer 3 selection from task-local semantic evidence."""

    selected: list[str] = []
    if family == "backend":
        if structure_states["domain-object"] == EFFECT_CHANGED:
            selected.append("domain-object-identification")
        if structure_states["pattern"] == EFFECT_CHANGED:
            selected.append("design-pattern-selection")
            if any(
                signal in text
                for signal in (
                    "concurrent caller",
                    "concurrency",
                    "synchronization",
                )
            ):
                selected.append("concurrency-control")
        if structure_states["minimality"] == EFFECT_CHANGED:
            selected.append("minimal-correct-implementation")
        if structure_states["owner-placement"] == EFFECT_CHANGED:
            selected.append("implementation-structure-design")
        if filesystem_effect_state == EFFECT_CHANGED:
            selected.append("filesystem-process-safety")
        if node_effect_state == EFFECT_CHANGED:
            selected.append("nodejs-runtime-professional-usage")
        if (
            "kotlin" in text
            and any(
                signal in text
                for signal in ("coroutine", "stateflow", "kotlin code")
            )
        ):
            selected.append("kotlin-professional-usage")
        if (
            ("c#" in text or ".net" in text)
            and any(
                signal in text
                for signal in (
                    "async disposal",
                    "cancellationtoken",
                    "trimming",
                    "aot behavior",
                )
            )
        ):
            selected.append("csharp-dotnet-professional-usage")
        if "regression test" in text:
            selected.append("regression-testing")
    elif family == "frontend":
        browser_specific = any(
            signal in text
            for signal in ("browser", "pwa", "react web", "web platform")
        )
        frontend_changed_scopes = _coordinated_implementation_change_scopes(
            text
        )
        frontend_effect_text = " ".join(frontend_changed_scopes)
        frontend_has_anti_scope = any(
            _scope_is_unchanged(scope)
            for _scope_id, scope in _bounded_effect_scopes(text)
        )
        explicit_state_effect = re.search(
            r"\bstate\b.{0,32}\b(?:change|fix|update|management|transition|"
            r"synchronization|ownership|restoration)\b|"
            r"\b(?:change|fix|update|management|transition|synchronization|"
            r"ownership|restoration)\b.{0,32}\bstate\b",
            frontend_effect_text,
        )
        if (
            "state" in frontend_effect_text
            and (
                not frontend_has_anti_scope
                or explicit_state_effect is not None
            )
        ) or (
            "frontend component" in text
            and not browser_specific
        ):
            selected.append("state-management-design")
        if _accessibility_behavior_requested(text):
            selected.append("accessibility-inclusive-design")
        if browser_specific and "state" not in text:
            selected.append("web-platform-professional-usage")
    elif family == "installed-client":
        if _accessibility_behavior_requested(text):
            selected.append("accessibility-inclusive-design")
        if any(
            signal in text
            for signal in (
                "state-restoration",
                "state restoration",
                "process termination",
            )
        ):
            selected.append("client-lifecycle-state-restoration")
        if (
            all(
                signal in text
                for signal in ("offline", "conflict")
            )
            and any(
                signal in text
                for signal in ("pending-operation", "reconnect")
            )
            and "no offline synchronization" not in text
        ):
            selected.append("offline-sync-conflict-resolution")
        if (
            "swift" in text
            and any(
                signal in text
                for signal in (
                    "actor isolation",
                    "mainactor",
                    "sendable",
                )
            )
            and "no swift source" not in text
        ):
            selected.append("swift-professional-usage")
        if filesystem_effect_state == EFFECT_CHANGED:
            selected.append("filesystem-process-safety")
    elif family == "data-middleware":
        if "consistency" in text:
            selected.append("transaction-consistency")
        if "queue" in text:
            selected.append("idempotency-retry-design")
        if "migration" in text:
            selected.append("data-migration-design")
    elif family == "integration":
        if "contract" in text:
            selected.append("contract-testing")
        if "failure" in text:
            selected.append("failure-contract-design")
        if "idempot" in text:
            selected.append("idempotency-retry-design")
    elif family == "repository-tooling":
        if any(
            signal in text
            for signal in ("generator", "compiler", "linter", "build")
        ):
            selected.append("build-tool-professional-usage")
        if structure_states["owner-placement"] == EFFECT_CHANGED:
            selected.append("implementation-structure-design")
        elif structure_states["pattern"] == EFFECT_CHANGED:
            selected.append("design-pattern-selection")
        elif structure_states["minimality"] == EFFECT_CHANGED:
            selected.append("minimal-correct-implementation")
        if filesystem_effect_state == EFFECT_CHANGED:
            selected.append("filesystem-process-safety")
        if any(
            signal in text
            for signal in (
                "generator",
                "compiler",
                "linter",
                "harness",
                "validation",
                "test",
            )
        ):
            selected.append("targeted-validation-selection")
    elif family == "platform-infrastructure":
        if any(
            signal in text
            for signal in (
                "terraform",
                "opentofu",
                "cloudformation",
                "pulumi",
                "helm",
                "kustomize",
            )
        ):
            selected.append("infrastructure-as-code-safety")
        if "powershell" in text:
            selected.append("powershell-professional-usage")
    elif family == "test-validation":
        if "regression" in text:
            selected.append("regression-testing")
        if any(
            signal in text
            for signal in (
                "client application",
                "installed-client",
                "device matrix",
            )
        ) and all(
            anti not in text
            for anti in (
                "no installed-client surface",
                "no client lifecycle or device matrix",
            )
        ):
            selected.append("client-application-testing")
        if all(
            signal in text
            for signal in (
                "process death",
                "permission revocation",
                "offline reconnect",
                "client upgrade",
            )
        ):
            selected.append("client-application-testing")
        if "targeted" in text:
            selected.append("targeted-validation-selection")
    elif family == "logging":
        if audit_implementation:
            selected.append("audit-evidence-integrity")
        else:
            selected.append("logging-error-handling")
        if "secret" in text:
            selected.append("secret-configuration-security")
    else:
        raise RoutingIntegrityError(f"unknown implementation family {family!r}")
    if family in _RUNTIME_POLICY_IMPLEMENTATION_FAMILIES:
        if _configuration_runtime_policy_risk(text):
            selected.append("configuration-runtime-policy")
        if _dependency_package_risk(text):
            selected.append("dependency-vulnerability-scanning")
    return list(dict.fromkeys(selected))


def _validated_implementation_owner_layer3(
    selected: list[str],
    *,
    allowed: list[str],
    known: set[str],
    maximum: int,
    family: str,
) -> tuple[list[str], bool]:
    """Validate complete owner evidence and report a legitimate budget overflow."""

    if (
        not isinstance(selected, list)
        or not all(isinstance(item, str) and item for item in selected)
    ):
        raise RoutingIntegrityError(
            f"{family!r} selected corrupt Layer 3 evidence {selected!r}"
        )
    if len(selected) != len(set(selected)):
        raise RoutingIntegrityError(
            f"{family!r} selected duplicate Layer 3 evidence {selected!r}"
        )
    stale = sorted(name for name in selected if name not in known)
    if stale:
        raise RoutingIntegrityError(
            f"{family!r} selected stale Layer 3 evidence {stale!r}"
        )
    unauthorized = sorted(name for name in selected if name not in allowed)
    if unauthorized:
        raise RoutingIntegrityError(
            f"{family!r} selected unauthorized Layer 3 evidence "
            f"{unauthorized!r}"
        )
    if type(maximum) is not int or maximum < 0:
        raise RoutingIntegrityError(
            f"{family!r} has corrupt Layer 3 maximum {maximum!r}"
        )
    return list(selected), len(selected) > maximum


def _installed_target_domains(value: str) -> list[str]:
    """Return concrete installed-client targets using the existing route grammar."""

    domains: list[str] = []
    if (
        "android" in value
        and "no android platform behavior" not in value
        and "no android native" not in value
    ):
        domains.append("android-platform-extension")
    if (
        any(signal in value for signal in ("ios", "ipados", "iphone", "ipad"))
        and "no apple client behavior" not in value
        and "ios-only" not in value.replace("accepted ios-only", "ios-only")
    ):
        domains.append("ios-ipados-platform-extension")
    if "ios-only" in value:
        domains.append("ios-ipados-platform-extension")
    if "windows" in value and "no windows behavior" not in value:
        domains.append("windows-platform-extension")
    if "macos" in value and "no macos behavior" not in value:
        domains.append("macos-platform-extension")
    if (
        any(
            signal in value
            for signal in ("linux graphical desktop", "linux desktop")
        )
        and "no desktop behavior" not in value
    ):
        domains.append("linux-desktop-platform-extension")
    return list(dict.fromkeys(domains))


def _shared_client_framework(value: str) -> bool:
    """Return whether the task names one shared installed-client framework."""

    shared = any(
        signal in value
        for signal in (
            "flutter",
            "react native",
            "electron",
            "tauri",
            ".net maui",
            "kotlin multiplatform",
            "qt graphical client",
        )
    )
    if "native android-only" in value and "no shared client framework" in value:
        return False
    return shared


def _platform_target_unknown(value: str) -> bool:
    """Return explicit unresolved target evidence from the converted branch."""

    return (
        "target platform is unknown" in value
        or "target platforms are unknown" in value
        or "target platforms are not yet known" in value
        or "target operating system is unknown" in value
        or "apple target platform is unknown" in value
        or "macos or catalyst target is unknown" in value
        or "linux desktop target is unknown" in value
        or "target platform is not stated" in value
        or (
            "cloud account" in value
            and "provider" in value
            and "unknown" in value
        )
    )


def _critical_unknown_evidence(
    value: str,
    *,
    parsed: _ParsedTaskRequest,
    filesystem_effect_state: str,
    node_effect_state: str,
    structure_states: dict[str, str],
    owner_internal_structure_evidence: list[str],
    generated_authority_state: str,
    target_domains: list[str],
    shared_framework: bool,
) -> list[str]:
    """Collect Core critical-unknown evidence without computing execution level."""

    unknown_state = r"(?:unknown|unresolved|undecided|not\s+yet\s+known)"
    fields = {
        "owner": (
            r"(?<!destination\s)(?:"
            r"owner(?![-\s]+(?:internal|private)\b)|module\s+ownership)"
        ),
        "authority": r"(?:authority|authoritative(?:\s+source)?)",
        "placement": (
            r"(?:placement|destination\s+owner|target\s+platforms?|"
            r"target\s+operating\s+system)"
        ),
        "acceptance": r"acceptance",
        "verification": r"verification",
        "rollback": r"(?:rollback|revert(?:\s+plan)?)",
    }
    evidence: list[str] = []
    for field, field_pattern in fields.items():
        field_then_state = re.search(
            rf"(?<!no\s)\b{field_pattern}\b"
            rf"\s+(?:is|remains)\s+{unknown_state}\b",
            value,
        )
        state_then_field = re.search(
            rf"(?<!no\s)(?<!not\s)(?<!no\slonger\s)"
            rf"\b{unknown_state}\s+{field_pattern}\b",
            value,
        )
        if field_then_state or state_then_field:
            evidence.append(f"critical-{field}-unknown")
    if (
        structure_states["owner-placement"] == EFFECT_AMBIGUOUS
        and not owner_internal_structure_evidence
    ):
        evidence.append("critical-placement-unknown")
    if structure_states["module-boundary"] == EFFECT_AMBIGUOUS:
        evidence.append("critical-owner-unknown")
        evidence.append("critical-source:module-boundary")
    if generated_authority_state == EFFECT_AMBIGUOUS:
        evidence.append("critical-authority-unknown")
    if filesystem_effect_state == EFFECT_AMBIGUOUS:
        evidence.append("critical-verification-unknown")
    if node_effect_state == EFFECT_AMBIGUOUS:
        evidence.append("critical-verification-unknown")
    if _platform_target_unknown(value) or (
        shared_framework and not target_domains
    ):
        evidence.append("critical-placement-unknown")
    return list(dict.fromkeys(evidence))


def _generic_preparation_evidence(value: str) -> list[str]:
    """Collect explicit generic implementation/repair preparation evidence."""

    specialist_or_artifact = any(
        signal in value
        for signal in (
            "review the actual diff",
            "dedicated security review",
            "security review artifact",
            "engineering brief",
            "task plan",
            "architecture artifact",
            "migration artifact",
            "release artifact",
        )
    )
    if specialist_or_artifact:
        return []
    prepare = re.search(
        r"\bprepare\b[^.;!?]{0,160}\b(implementation|repair)\b",
        value,
    )
    analyze_before_editing = re.search(
        r"\banaly[sz]e\b[^.;!?]{0,160}\b(implementation|repair)\b"
        r"[^.;!?]{0,120}\bbefore editing\b",
        value,
    )
    match = prepare or analyze_before_editing
    if match is None:
        return []
    return [
        "explicit-repair-preparation"
        if match.group(1) == "repair"
        else "explicit-implementation-preparation"
    ]


def _review_risk_nonmaterial_ranges(
    candidate_id: str,
    value: str,
) -> list[tuple[int, int]]:
    """Return exact nonmaterial proposition ranges for one risk family."""

    family_subjects = {
        "review-security-risk": (
            r"tenant authorization(?: behavior)?",
            r"tenant isolation(?: behavior)?",
            r"permission (?:bypass|boundar(?:y|ies)|behavior|changes?)",
            r"object permission(?: behavior)?",
            r"trust[- ]boundar(?:y|ies)",
            r"security(?: risk| behavior)?",
        ),
        "review-release-risk": (
            r"production rollout(?: decision| behavior)?",
            r"production apply(?: behavior)?",
            r"production release(?: behavior)?",
            r"release rollback(?: behavior)?",
            r"release decisions?",
            r"release behavior",
            r"release risk",
            r"release",
        ),
        "review-logging-risk": (
            r"logging secret exposure",
            r"logging redaction",
            r"logging content",
            r"logging behavior",
            r"logging risk",
            r"logging",
            r"secret exposure",
            r"secret",
            r"redaction behavior",
            r"redaction",
            r"redacted log",
        ),
        "review-reliability-risk": (
            r"slo recovery behavior",
            r"slo recovery risk",
            r"slo recovery",
            r"slo behavior",
            r"slo risk",
            r"slo",
            r"outage behavior",
            r"outage risk",
            r"outage",
            r"degradation behavior",
            r"degradation risk",
            r"degradation",
            r"recovery behavior",
            r"recovery risk",
            r"recovery",
            r"reliability behavior",
            r"reliability risk",
            r"reliability",
        ),
    }
    if candidate_id not in family_subjects:
        raise ValidationProblem(
            f"unknown review risk candidate {candidate_id!r}"
        )
    subject = r"(?:" + "|".join(family_subjects[candidate_id]) + r")"
    compound_subject = (
        subject
        + r"(?:\s+(?:and|or)\s+"
        + subject
        + r")*"
    )
    nonmaterial_state = (
        r"(?:unchanged|out[- ]of[- ]scope|"
        r"background context only|background[- ]only|"
        r"context only|not material)"
    )
    patterns = (
        (
            r"\b"
            + compound_subject
            + r"\s+(?:is|are)\s+(?:explicitly\s+)?"
            + nonmaterial_state
            + r"\b"
        ),
        (
            r"\b"
            + compound_subject
            + r"\s+(?:does|do)\s+not\s+change\b"
        ),
        (
            r"\b"
            + compound_subject
            + r"\s+appear(?:s)? only as unchanged background context\b"
        ),
        (
            r"\bno\s+"
            + compound_subject
            + r"(?:\s+(?:risk|change|changes|behavior|exposure))?"
            + r"(?:\s+(?:exists|occurs|changes?))?\b"
        ),
    )
    return sorted(
        {
            match.span()
            for pattern in patterns
            for match in re.finditer(pattern, value)
        }
    )


def _risk_signal_is_nonmaterial_context(
    value: str,
    start: int,
    end: int,
) -> bool:
    """Exclude risk words used only by documentation or all-unchanged clauses."""

    left = max(
        value.rfind(separator, 0, start)
        for separator in (".", ";", "!", "?")
    )
    right_candidates = [
        position
        for separator in (".", ";", "!", "?")
        if (position := value.find(separator, end)) >= 0
    ]
    right = min(right_candidates) if right_candidates else len(value)
    clause = value[left + 1 : right]
    if any(
        signal in clause
        for signal in ("documentation", "guide", "help text")
    ):
        return True
    tail = value[start:right]
    return " but " not in tail and bool(
        re.search(
            r"\bbehavior\s+(?:is|are|remains?)\s+all\s+unchanged\b",
            tail,
        )
    )


def _material_review_risk_candidates(
    value: str,
    *,
    boundary_facts: tuple[_RoutingBoundaryFacts, ...],
) -> list[dict[str, Any]]:
    """Collect closed material risk predicates for review or preparation."""

    definitions = (
        (
            "review-release-risk",
            (
                ("production rollout", "material-production-rollout"),
                ("production apply", "material-production-apply"),
                ("production release", "material-production-release"),
                ("release rollback", "material-release-rollback"),
                ("release decision", "material-release-decision"),
            ),
        ),
        (
            "review-logging-risk",
            (
                ("logging", "material-logging-change"),
                ("redaction", "material-log-redaction"),
                ("redacted log", "material-log-redaction"),
                ("secret", "material-secret-exposure"),
            ),
        ),
        (
            "review-reliability-risk",
            (
                ("slo", "material-slo-risk"),
                ("outage", "material-outage-risk"),
                ("degradation", "material-degradation-risk"),
                ("recovery", "material-recovery-risk"),
            ),
        ),
    )
    candidates: list[dict[str, Any]] = []
    proved_security_facts = tuple(
        facts
        for facts in boundary_facts
        if _security_boundary_is_proved(facts)
    )
    security_evidence = list(
        dict.fromkeys(
            evidence_id.rsplit(":", 1)[-1]
            for facts in proved_security_facts
            for evidence_id in facts.evidence_ids
            if ":material-" in evidence_id
        )
    )
    if proved_security_facts and not security_evidence:
        security_evidence.append("material-trust-boundary")
    if security_evidence:
        candidates.append(
            {
                "candidate_id": "review-security-risk",
                "evidence": security_evidence,
            }
        )
    for candidate_id, signals in definitions:
        if (
            candidate_id == "review-reliability-risk"
            and any(
                any(
                    item.endswith("credential-lifecycle-change")
                    for item in facts.evidence_ids
                )
                for facts in proved_security_facts
            )
        ):
            continue
        evidence: list[str] = []
        nonmaterial_ranges = _review_risk_nonmaterial_ranges(
            candidate_id,
            value,
        )
        for signal, evidence_id in signals:
            offset = 0
            while True:
                start = value.find(signal, offset)
                if start < 0:
                    break
                end = start + len(signal)
                offset = end
                if any(
                    range_start <= start and end <= range_end
                    for range_start, range_end in nonmaterial_ranges
                ) or _risk_signal_is_nonmaterial_context(
                    value,
                    start,
                    end,
                ):
                    continue
                evidence.append(evidence_id)
        if evidence:
            candidates.append(
                {
                    "candidate_id": candidate_id,
                    "evidence": list(dict.fromkeys(evidence)),
                }
            )
    return candidates


def _review_stage_evidence(
    value: str,
    *,
    has_material_risk: bool,
) -> list[str]:
    """Return explicit review-stage evidence for the T2C closed surfaces."""

    if "review the actual diff" in value:
        return ["actual-diff-review"]
    if value.startswith("review ") and (
        "regression test" in value or has_material_risk
    ):
        return [
            "review-regression-tests"
            if "regression test" in value
            else "explicit-risk-review-task"
        ]
    return []


def _review_risk_layer3(
    candidate_id: str,
    evidence: list[str],
) -> list[str]:
    """Return the registry-owned Layer 3 set for one selected review risk."""

    if candidate_id == "review-security-risk":
        layer3 = [
            "permission-boundary-modeling",
            "threat-modeling",
        ]
        if "material-tenant-isolation" in evidence:
            layer3.append("tenant-isolation")
    elif candidate_id == "review-release-risk":
        layer3 = ["release-rollback", "version-compatibility"]
    elif candidate_id == "review-logging-risk":
        layer3 = [
            "logging-error-handling",
            "secret-configuration-security",
        ]
    elif candidate_id == "review-reliability-risk":
        layer3 = ["degradation-circuit-breaking", "observability"]
        if "material-recovery-risk" in evidence:
            layer3.append("backup-recovery")
    else:
        raise ValidationProblem(
            f"unknown review risk candidate {candidate_id!r}"
        )
    undeclared = [
        name
        for name in layer3
        if name not in REVIEW_RISK_PRIMARY_LAYER3[candidate_id]
    ]
    if undeclared:
        raise ValidationProblem(
            f"{candidate_id} selected undeclared Layer 3 {undeclared}"
        )
    return layer3


def _copy_route_candidate_with_reason(
    candidate: dict[str, Any],
    reason: str,
) -> dict[str, Any]:
    copied = copy.deepcopy(candidate)
    copied["reason"] = reason
    return copied


def _route_contract_conflict_candidate(
    candidates: list[dict[str, Any]],
    *,
    precedence: int,
) -> dict[str, Any]:
    """Build the canonical fail-closed route-contract conflict."""

    return {
        "candidate_id": "route-contract-conflict",
        "candidate_type": "derived-conflict",
        "evidence": sorted(
            {
                evidence
                for candidate in candidates
                for evidence in candidate["evidence"]
            }
        ),
        "source_candidate_ids": sorted(
            candidate["candidate_id"] for candidate in candidates
        ),
        "precedence": precedence,
        "reason": "equal-precedence-route-contract-conflict",
        "path": "analyzed",
        "profile": "analysis-agent",
        "primary_skill": "engineering-change-analysis",
        "layer3_skills": ["repository-context-map"],
        "review_skill": "architecture-impact-reviewer",
    }


def _merge_bound_high_risk_artifact_specialists(
    candidates: list[dict[str, Any]],
    *,
    layer3_authority_by_primary: dict[str, Any] | None,
    maximum_layer3: int | None,
) -> dict[str, Any]:
    """Merge the exact same-binding high-risk specialist pair."""

    source_candidate_ids = sorted(
        {
            source_id
            for candidate in candidates
            for source_id in candidate.get(
                "source_candidate_ids",
                [candidate["candidate_id"]],
            )
        }
    )
    if (
        len(candidates) != 2
        or frozenset(
            candidate.get("candidate_id") for candidate in candidates
        )
        != _BRIEF_REVIEW_COMPATIBLE_SPECIALIST_IDS
    ):
        raise RoutingIntegrityError(
            "bound high-risk specialist merge requires the exact pair"
        )
    compatibility_fields = (
        "candidate_type",
        "path",
        "profile",
        "primary_skill",
        "review_skill",
        "stage",
        "precedence_class",
        "precedence",
        "artifact_binding_id",
    )
    contracts = {
        tuple(candidate.get(field) for field in compatibility_fields)
        for candidate in candidates
    }
    if len(contracts) != 1:
        return _route_contract_conflict_candidate(
            candidates,
            precedence=min(
                candidate["precedence"] for candidate in candidates
            ),
        )
    contract = next(iter(contracts))
    if (
        contract[0] != "explicit-route"
        or not all(
            isinstance(value, str) and value
            for value in contract[1:7]
        )
        or contract[7] != EXPLICIT_ROUTE_PRECEDENCE
        or not isinstance(contract[8], str)
        or _BRIEF_REVIEW_BINDING_TOKEN_PATTERN.fullmatch(contract[8]) is None
    ):
        raise RoutingIntegrityError(
            "bound high-risk specialist contract is not canonical"
        )
    primary_skill = contract[3]
    if not isinstance(layer3_authority_by_primary, dict):
        raise RoutingIntegrityError(
            "bound high-risk specialist merge lacks Layer 3 authority"
        )
    authority_order = layer3_authority_by_primary.get(primary_skill)
    if (
        not isinstance(authority_order, (list, tuple))
        or not authority_order
        or any(
            not isinstance(skill, str) or not skill
            for skill in authority_order
        )
        or len(authority_order) != len(set(authority_order))
    ):
        raise RoutingIntegrityError(
            "bound high-risk specialist Layer 3 authority is invalid"
        )
    if not isinstance(maximum_layer3, int) or maximum_layer3 < 1:
        raise RoutingIntegrityError(
            "bound high-risk specialist merge lacks Layer 3 budget authority"
        )

    requested: set[str] = set()
    source_foundation_candidates: list[dict[str, Any]] = []
    for candidate in candidates:
        layer3 = candidate.get("layer3_skills")
        context = candidate.get("candidate_layer3_context")
        if (
            not isinstance(layer3, list)
            or not layer3
            or len(layer3) != len(set(layer3))
            or candidate.get("eligible_foundation_layer3_skills") != layer3
            or candidate.get("eligible_domain_layer3_skills") != []
            or candidate.get("eligible_layer3_skills") != layer3
            or candidate.get("reserved_domain_capacity") != 0
            or candidate.get("layer3_overflow") is not False
            or not isinstance(context, dict)
            or context.get("kind") != "fixed"
            or context.get("foundation_requests") != layer3
            or context.get("domain_requests") != []
        ):
            raise RoutingIntegrityError(
                "bound high-risk specialist Layer 3 contract is invalid"
            )
        requested.update(layer3)
        rows = candidate.get("source_foundation_candidates", [])
        if not isinstance(rows, list) or any(
            not isinstance(row, dict) for row in rows
        ):
            raise RoutingIntegrityError(
                "bound high-risk specialist source authority is invalid"
            )
        source_foundation_candidates.extend(copy.deepcopy(rows))
    authority_set = set(authority_order)
    if not requested.issubset(authority_set):
        raise RoutingIntegrityError(
            "bound high-risk specialist selected undeclared Layer 3"
        )
    merged_layer3 = [
        skill for skill in authority_order if skill in requested
    ]
    evidence = sorted(
        {
            item
            for candidate in candidates
            for item in candidate["evidence"]
        }
    )
    if len(merged_layer3) > maximum_layer3:
        return {
            "candidate_id": "foundation-layer3-overflow",
            "candidate_type": "derived-conflict",
            "evidence": ["foundation-layer3-overflow"],
            "eligible_foundation_layer3_skills": merged_layer3,
            "eligible_domain_layer3_skills": [],
            "eligible_layer3_skills": merged_layer3,
            "source_candidate_ids": source_candidate_ids,
            "precedence": contract[7],
            "reason": "foundation-layer3-overflow",
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
            "reserved_domain_capacity": 0,
            "layer3_overflow": True,
        }

    authority_position = {
        skill: index for index, skill in enumerate(authority_order)
    }
    source_foundation_candidates.sort(
        key=lambda row: (
            min(
                (
                    authority_position.get(skill, len(authority_position))
                    for skill in row.get("foundations", [])
                ),
                default=len(authority_position),
            ),
            row.get("candidate_id", ""),
        )
    )
    return {
        "candidate_id": "merged-route-candidate",
        "candidate_type": "merged-route",
        "evidence": evidence,
        "source_candidate_ids": source_candidate_ids,
        "precedence": contract[7],
        "reason": "same-binding-compatible-specialist-merge",
        "path": contract[1],
        "profile": contract[2],
        "primary_skill": primary_skill,
        "layer3_skills": merged_layer3,
        "review_skill": contract[4],
        "stage": contract[5],
        "precedence_class": contract[6],
        "candidate_layer3_context": {
            "kind": "fixed",
            "foundation_requests": merged_layer3,
            "domain_requests": [],
        },
        "eligible_foundation_layer3_skills": merged_layer3,
        "eligible_domain_layer3_skills": [],
        "eligible_layer3_skills": merged_layer3,
        "reserved_domain_capacity": 0,
        "layer3_overflow": False,
        **(
            {
                "source_foundation_candidates": (
                    source_foundation_candidates
                )
            }
            if source_foundation_candidates
            else {}
        ),
    }


def _validated_audit_analysis_conflict_candidates(
    raw_candidates: list[dict[str, Any]],
    normalized_candidates: list[dict[str, Any]],
    *,
    admission_authority: OracleAdmissionAuthority | None,
) -> list[dict[str, Any]]:
    """Validate the exact automatic-logging and explicit-audit pair."""

    if not isinstance(admission_authority, OracleAdmissionAuthority):
        raise RoutingIntegrityError(
            "audit analysis conflict lacks exact admission authority"
        )
    if len(raw_candidates) != 2 or len(normalized_candidates) != 2:
        raise RoutingIntegrityError(
            "audit analysis conflict requires exactly two route candidates"
        )
    expected = {
        "implementation-owner:logging-design-gate": {
            "candidate_type": "automatic-implementation-owner",
            "routing_family": "logging",
            "rule_id": None,
            "precedence": 4,
            "path": "direct",
            "profile": "task-agent",
            "primary_skill": "logging-design-gate",
            "layer3_skills": ["logging-error-handling"],
            "review_skill": "logging-design-gate",
            "evidence": [
                "diagnostic-record-surface",
                "effect-changed",
                "explicit-implementation-action",
                "dynamic-helper:_review_risk_layer3",
                "foundation-selector:"
                "dynamic-foundation:logging-error-handling",
            ],
            "candidate_layer3_context": {
                "kind": "fixed",
                "foundation_requests": ["logging-error-handling"],
                "domain_requests": [],
            },
            "eligible_foundation_layer3_skills": [
                "logging-error-handling"
            ],
            "eligible_domain_layer3_skills": [],
            "eligible_layer3_skills": ["logging-error-handling"],
            "reserved_domain_capacity": 0,
            "layer3_overflow": False,
        },
        "audit-integrity-change": {
            "candidate_type": "explicit-route",
            "routing_family": None,
            "rule_id": "audit-integrity-change",
            "precedence": 5,
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "security-privacy-gate",
            "layer3_skills": ["audit-evidence-integrity"],
            "review_skill": "security-privacy-gate",
            "evidence": [
                "audit-evidence-integrity",
                "foundation-selector:audit-integrity-change",
            ],
            "candidate_layer3_context": {
                "kind": "fixed",
                "foundation_requests": ["audit-evidence-integrity"],
                "domain_requests": [],
            },
            "eligible_foundation_layer3_skills": [
                "audit-evidence-integrity"
            ],
            "eligible_domain_layer3_skills": [],
            "eligible_layer3_skills": ["audit-evidence-integrity"],
            "reserved_domain_capacity": 0,
            "layer3_overflow": False,
        },
    }
    expected_ids = set(expected)
    for label, candidates in (
        ("raw", raw_candidates),
        ("normalized", normalized_candidates),
    ):
        candidate_ids = [
            candidate.get("candidate_id") for candidate in candidates
        ]
        if (
            len(candidate_ids) != len(set(candidate_ids))
            or set(candidate_ids) != expected_ids
        ):
            raise RoutingIntegrityError(
                f"audit analysis conflict {label} candidates are not exact"
            )
        for candidate in candidates:
            candidate_id = candidate["candidate_id"]
            contract = expected[candidate_id]
            observed = {
                field: candidate.get(field)
                for field in contract
            }
            if observed != contract:
                raise RoutingIntegrityError(
                    "audit analysis conflict candidate changed exact "
                    f"route contract: {candidate_id!r}"
                )
    ordered = sorted(
        normalized_candidates,
        key=lambda candidate: (
            candidate["precedence"],
            candidate["candidate_id"],
        ),
    )
    for candidate in ordered:
        _validate_foundation_candidate(
            candidate,
            candidate["layer3_skills"],
            admission_authority=admission_authority,
        )
    return ordered


def _select_route_cohort_candidate(
    raw_candidates: list[dict[str, Any]],
    *,
    implementation_policy: dict[str, Any] | None = None,
    audit_analysis_conflict: bool = False,
    admission_authority: OracleAdmissionAuthority | None = None,
    layer3_authority_by_primary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Apply semantic cohort precedence independently of candidate source order."""

    normalized: list[dict[str, Any]] = []
    for candidate in raw_candidates:
        candidate_id = candidate.get("candidate_id")
        has_artifact_binding = (
            "artifact_binding_id" in candidate
        )
        if (
            has_artifact_binding
            and candidate_id not in _BRIEF_REVIEW_BINDING_WRITER_IDS
        ):
            raise RoutingIntegrityError(
                "only Brief159 artifact writers may carry a binding token"
            )
        if has_artifact_binding:
            artifact_binding = candidate["artifact_binding_id"]
            if (
                artifact_binding is not None
                and (
                    not isinstance(artifact_binding, str)
                    or _BRIEF_REVIEW_BINDING_TOKEN_PATTERN.fullmatch(
                        artifact_binding
                    )
                    is None
                )
            ):
                raise RoutingIntegrityError(
                    "artifact writer binding token is not canonical"
                )
        automatic_owner = (
            isinstance(candidate_id, str)
            and candidate_id.startswith("implementation-owner:")
        )
        if automatic_owner:
            primary_skill = candidate.get("primary_skill")
            routing_family = candidate.get("routing_family")
            if (
                not isinstance(primary_skill, str)
                or not primary_skill
                or candidate_id
                != f"implementation-owner:{primary_skill}"
                or not isinstance(routing_family, str)
                or not routing_family
            ):
                raise RoutingIntegrityError(
                    "implementation owner identity is not canonical"
                )
        explicit_route = candidate.get("candidate_type") in {
            "artifact-review-route",
            "explicit-route",
            "fallback-route",
        }
        if (
            candidate_id not in ROUTE_COHORT_PRECEDENCE
            and not automatic_owner
            and not explicit_route
        ):
            raise ValidationProblem(
                f"unknown route cohort candidate {candidate_id!r}"
            )
        evidence = candidate.get("evidence")
        if (
            not isinstance(evidence, list)
            or not evidence
            or not all(isinstance(item, str) and item for item in evidence)
        ):
            raise ValidationProblem(
                f"{candidate_id} route cohort evidence must be non-empty text"
            )
        if explicit_route:
            precedence = candidate.get("precedence")
            expected_precedence = (
                FALLBACK_ROUTE_PRECEDENCE
                if candidate.get("candidate_type") == "fallback-route"
                else 3
                if candidate.get("candidate_type") == "artifact-review-route"
                else EXPLICIT_ROUTE_PRECEDENCE
            )
            if precedence != expected_precedence:
                raise RoutingIntegrityError(
                    f"{candidate_id} explicit route precedence must be "
                    f"{expected_precedence}, found {precedence!r}"
                )
            for field in ROUTE_CONTRACT_FIELDS:
                if field not in candidate:
                    raise RoutingIntegrityError(
                        f"{candidate_id} explicit route lacks {field!r}"
                    )
        normalized_candidate = {
            "candidate_id": candidate_id,
            "candidate_type": (
                "automatic-implementation-owner"
                if automatic_owner
                else candidate.get("candidate_type", "converted-cohort")
            ),
            "evidence": (
                list(dict.fromkeys(evidence))
                if (
                    automatic_owner
                    or "semantic_atoms" in candidate
                    or "source_foundation_candidates" in candidate
                )
                else sorted(set(evidence))
            ),
            "precedence": (
                4
                if automatic_owner
                else candidate["precedence"]
                if explicit_route
                else ROUTE_COHORT_PRECEDENCE[candidate_id]
            ),
        }
        for field in ROUTE_CONTRACT_FIELDS:
            if field in candidate:
                normalized_candidate[field] = copy.deepcopy(candidate[field])
        for field in (
            *ROUTE_CANDIDATE_CONTRACT_FIELDS,
            "routing_family",
            "rule_id",
            "stage",
            "precedence_class",
            "candidate_layer3_context",
            *ROUTE_CANDIDATE_LAYER3_FIELDS,
            "source_candidate_ids",
            "source_foundation_candidates",
        ):
            if field in candidate:
                normalized_candidate[field] = copy.deepcopy(candidate[field])
        if automatic_owner:
            normalized_candidate["path"] = (
                implementation_policy["accepted"]["path"]
                if isinstance(implementation_policy, dict)
                else "direct"
            )
            normalized_candidate["profile"] = (
                implementation_policy["accepted"]["profile"]
                if isinstance(implementation_policy, dict)
                else "task-agent"
            )
        if "semantic_atoms" in candidate:
            normalized_candidate["semantic_atoms"] = copy.deepcopy(
                candidate["semantic_atoms"]
            )
        normalized.append(normalized_candidate)

    if audit_analysis_conflict:
        ordered = _validated_audit_analysis_conflict_candidates(
            raw_candidates,
            normalized,
            admission_authority=admission_authority,
        )
        selected = _route_contract_conflict_candidate(
            ordered,
            precedence=min(
                candidate["precedence"] for candidate in ordered
            ),
        )
        excluded = [
            _copy_route_candidate_with_reason(
                candidate,
                "ambiguous-route-contract",
            )
            for candidate in ordered
        ]
        return {
            "raw_candidates": ordered,
            "selected_candidate": selected,
            "excluded_candidates": excluded,
        }

    artifact_preexcluded: list[dict[str, Any]] = []
    artifact_candidates = sorted(
        (
            candidate
            for candidate in normalized
            if candidate["candidate_id"]
            in _BRIEF_REVIEW_BINDING_WRITER_IDS
        ),
        key=lambda candidate: candidate["candidate_id"],
    )
    artifact_binding_active = any(
        "artifact_binding_id" in candidate
        for candidate in artifact_candidates
    )
    if artifact_candidates and artifact_binding_active:
        writer_ids = [
            candidate["candidate_id"]
            for candidate in artifact_candidates
        ]
        if len(writer_ids) != len(set(writer_ids)):
            raise RoutingIntegrityError(
                "Brief159 artifact writer candidates must be unique"
            )
        minimum_precedence = min(
            candidate["precedence"]
            for candidate in artifact_candidates
        )
        binding_tokens = [
            candidate.get("artifact_binding_id")
            for candidate in artifact_candidates
        ]
        source_writer_ids = sorted(
            {
                source_id
                for candidate in artifact_candidates
                for source_id in candidate.get(
                    "source_candidate_ids",
                    [candidate["candidate_id"]],
                )
            }
        )
        missing_binding = any(
            token is None for token in binding_tokens
        )
        same_binding = (
            not missing_binding
            and len(set(binding_tokens)) == 1
        )
        high_risk = next(
            (
                candidate
                for candidate in artifact_candidates
                if candidate["candidate_id"]
                == "high-risk-architecture-plan"
            ),
            None,
        )
        ordinary = next(
            (
                candidate
                for candidate in artifact_candidates
                if candidate["candidate_id"]
                == "engineering-artifact-review"
            ),
            None,
        )
        compatible_specialists = [
            candidate
            for candidate in artifact_candidates
            if candidate["candidate_id"]
            in _BRIEF_REVIEW_COMPATIBLE_SPECIALIST_IDS
        ]

        if len(artifact_candidates) == 1 and not missing_binding:
            resolved_artifact = copy.deepcopy(artifact_candidates[0])
            resolved_artifact.pop("artifact_binding_id", None)
        elif (
            same_binding
            and compatible_specialists
            and high_risk is None
        ):
            if len(compatible_specialists) == 1:
                resolved_artifact = copy.deepcopy(
                    compatible_specialists[0]
                )
                resolved_artifact.pop("artifact_binding_id", None)
            else:
                maximum_layer3 = (
                    implementation_policy.get("accepted", {})
                    .get("layer3", {})
                    .get("max")
                    if isinstance(implementation_policy, dict)
                    else None
                )
                resolved_artifact = (
                    _merge_bound_high_risk_artifact_specialists(
                        compatible_specialists,
                        layer3_authority_by_primary=(
                            layer3_authority_by_primary
                        ),
                        maximum_layer3=maximum_layer3,
                    )
                )
                specialist_reason = (
                    resolved_artifact["reason"]
                    if resolved_artifact["candidate_type"]
                    == "derived-conflict"
                    else "merged-into-route-contract"
                )
                for specialist in compatible_specialists:
                    specialist_exclusion = (
                        _copy_route_candidate_with_reason(
                            specialist,
                            specialist_reason,
                        )
                    )
                    specialist_exclusion.pop("artifact_binding_id", None)
                    artifact_preexcluded.append(
                        specialist_exclusion
                    )
            resolved_artifact["precedence"] = minimum_precedence
            resolved_artifact["source_candidate_ids"] = source_writer_ids
            if ordinary is not None:
                generic_exclusion = _copy_route_candidate_with_reason(
                    ordinary,
                    "specialist-refinement-same-artifact",
                )
                generic_exclusion.pop("artifact_binding_id", None)
                artifact_preexcluded.append(generic_exclusion)
        elif (
            same_binding
            and high_risk is not None
            and not compatible_specialists
        ):
            resolved_artifact = copy.deepcopy(high_risk)
            resolved_artifact.pop("artifact_binding_id", None)
            resolved_artifact["precedence"] = minimum_precedence
            resolved_artifact["source_candidate_ids"] = source_writer_ids
            if ordinary is not None:
                generic_exclusion = _copy_route_candidate_with_reason(
                    ordinary,
                    "specialist-refinement-same-artifact",
                )
                generic_exclusion.pop("artifact_binding_id", None)
                artifact_preexcluded.append(generic_exclusion)
        else:
            reason = (
                "binding-missing"
                if missing_binding
                else "artifact-binding-conflict"
            )
            resolved_artifact = {
                "candidate_id": "route-contract-conflict",
                "candidate_type": "derived-conflict",
                "evidence": sorted(
                    {
                        item
                        for candidate in artifact_candidates
                        for item in candidate["evidence"]
                    }
                ),
                "source_candidate_ids": source_writer_ids,
                "precedence": minimum_precedence,
                "reason": reason,
                "path": "analyzed",
                "profile": "analysis-agent",
                "primary_skill": "engineering-change-analysis",
                "layer3_skills": ["repository-context-map"],
                "review_skill": "architecture-impact-reviewer",
            }
            for candidate in artifact_candidates:
                exclusion = _copy_route_candidate_with_reason(
                    candidate,
                    reason,
                )
                exclusion.pop("artifact_binding_id", None)
                artifact_preexcluded.append(exclusion)

        normalized = [
            candidate
            for candidate in normalized
            if candidate["candidate_id"]
            not in _BRIEF_REVIEW_BINDING_WRITER_IDS
        ]
        normalized.append(resolved_artifact)

    def frozen(value: Any) -> Any:
        if isinstance(value, dict):
            return tuple(
                (key, frozen(item))
                for key, item in sorted(value.items())
            )
        if isinstance(value, list):
            return tuple(frozen(item) for item in value)
        return value

    owner_contract_fields = (
        *ROUTE_CONTRACT_FIELDS,
        *ROUTE_CANDIDATE_LAYER3_FIELDS,
        "candidate_layer3_context",
    )
    owner_groups: dict[
        tuple[str, str],
        list[dict[str, Any]],
    ] = {}
    nonowners: list[dict[str, Any]] = []
    for candidate in normalized:
        candidate_id = candidate["candidate_id"]
        if isinstance(candidate_id, str) and candidate_id.startswith(
            "implementation-owner:"
        ):
            identity = (
                candidate["routing_family"],
                candidate["primary_skill"],
            )
            owner_groups.setdefault(identity, []).append(candidate)
        else:
            nonowners.append(candidate)
    owner_contract_conflicts: set[tuple[str, str]] = set()
    merged_owners: list[dict[str, Any]] = []
    for identity, candidates_for_owner in owner_groups.items():
        contracts = {
            tuple(
                frozen(candidate.get(field))
                for field in owner_contract_fields
            )
            for candidate in candidates_for_owner
        }
        if len(contracts) != 1:
            owner_contract_conflicts.add(identity)
            merged_owners.extend(candidates_for_owner)
            continue
        merged = copy.deepcopy(candidates_for_owner[0])
        if len(candidates_for_owner) > 1:
            merged["evidence"] = sorted(
                {
                    item
                    for candidate in candidates_for_owner
                    for item in candidate["evidence"]
                }
            )
        merged["source_candidate_ids"] = sorted(
            {
                source_id
                for candidate in candidates_for_owner
                for source_id in candidate.get(
                    "source_candidate_ids",
                    [candidate["candidate_id"]],
                )
            }
        )
        merged_owners.append(merged)
    normalized = [*nonowners, *merged_owners]
    ordered = sorted(
        normalized,
        key=lambda item: (
            item["precedence"],
            item["candidate_id"],
        ),
    )
    top_precedence = ordered[0]["precedence"] if ordered else None
    top_review_risks = [
        candidate
        for candidate in ordered
        if candidate["precedence"] == top_precedence
        and candidate["candidate_id"] in REVIEW_RISK_PRIMARY
    ]
    distinct_review_owners = {
        REVIEW_RISK_PRIMARY[candidate["candidate_id"]]
        for candidate in top_review_risks
    }
    top_implementation_owners = [
        candidate
        for candidate in ordered
        if candidate["precedence"] == top_precedence
        and candidate["candidate_id"].startswith("implementation-owner:")
    ]
    distinct_implementation_identities = {
        (
            candidate.get("routing_family"),
            candidate.get("primary_skill"),
        )
        for candidate in top_implementation_owners
    }
    overflow_owners = [
        candidate
        for candidate in top_implementation_owners
        if candidate.get("layer3_overflow")
    ]
    top_explicit_routes = [
        candidate
        for candidate in ordered
        if candidate["precedence"] == top_precedence
        and candidate["candidate_type"]
        in {
            "artifact-review-route",
            "explicit-route",
            "fallback-route",
        }
    ]
    if overflow_owners:
        eligible = list(
            dict.fromkeys(
                layer3
                for candidate in overflow_owners
                for layer3 in candidate["eligible_layer3_skills"]
            )
        )
        if not any(
            candidate["eligible_domain_layer3_skills"]
            for candidate in overflow_owners
        ):
            eligible = sorted(eligible)
        selected = {
            "candidate_id": "foundation-layer3-overflow",
            "candidate_type": "derived-conflict",
            "evidence": ["foundation-layer3-overflow"],
            "eligible_layer3_skills": eligible,
            "source_candidate_ids": sorted(
                candidate["candidate_id"]
                for candidate in overflow_owners
            ),
            "precedence": top_precedence,
            "reason": "foundation-layer3-overflow",
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
            "eligible_foundation_layer3_skills": [
                "repository-context-map"
            ],
            "eligible_domain_layer3_skills": [],
            "reserved_domain_capacity": 0,
            "layer3_overflow": True,
        }
        excluded = [
            _copy_route_candidate_with_reason(
                candidate,
                (
                    "foundation-layer3-overflow"
                    if candidate in overflow_owners
                    else "lower-precedence-than-foundation-layer3-overflow"
                ),
            )
            for candidate in ordered
        ]
    elif any(
        identity in owner_contract_conflicts
        for identity in distinct_implementation_identities
    ):
        conflicting_owners = [
            candidate
            for candidate in top_implementation_owners
            if (
                candidate.get("routing_family"),
                candidate.get("primary_skill"),
            )
            in owner_contract_conflicts
        ]
        selected = {
            "candidate_id": "route-contract-conflict",
            "candidate_type": "derived-conflict",
            "evidence": sorted(
                {
                    item
                    for candidate in conflicting_owners
                    for item in candidate["evidence"]
                }
            ),
            "source_candidate_ids": sorted(
                {
                    candidate["candidate_id"]
                    for candidate in conflicting_owners
                }
            ),
            "precedence": top_precedence,
            "reason": "equal-precedence-route-contract-conflict",
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
            "eligible_foundation_layer3_skills": [
                "repository-context-map"
            ],
            "eligible_domain_layer3_skills": [],
            "eligible_layer3_skills": ["repository-context-map"],
            "reserved_domain_capacity": 0,
            "layer3_overflow": False,
        }
        conflicting_ids = {
            id(candidate) for candidate in conflicting_owners
        }
        excluded = [
            _copy_route_candidate_with_reason(
                candidate,
                (
                    "ambiguous-route-contract"
                    if id(candidate) in conflicting_ids
                    else "lower-precedence-than-route-contract-conflict"
                ),
            )
            for candidate in ordered
        ]
    elif (
        len(top_implementation_owners) >= 2
        and len(distinct_implementation_identities) >= 2
    ):
        if not isinstance(implementation_policy, dict):
            raise RoutingIntegrityError(
                "implementation-owner conflict lacks typed policy authority"
            )
        conflict = implementation_policy.get("conflict")
        if not isinstance(conflict, dict):
            raise RoutingIntegrityError(
                "implementation-owner conflict policy is malformed"
            )
        selected = {
            "candidate_id": "implementation-owner-conflict",
            "candidate_type": "derived-conflict",
            "evidence": sorted(
                f"{candidate['routing_family']}:{candidate['primary_skill']}"
                for candidate in top_implementation_owners
            ),
            "precedence": top_precedence,
            "reason": conflict["reason"],
            "path": conflict["path"],
            "profile": conflict["profile"],
            "primary_skill": conflict["primary_skill"],
            "layer3_skills": list(conflict["layer3_skills"]),
            "review_skill": conflict["review_skill"],
        }
        tied_ids = {
            candidate["candidate_id"]
            for candidate in top_implementation_owners
        }
        excluded = [
            _copy_route_candidate_with_reason(
                candidate,
                (
                    "ambiguous-implementation-owner"
                    if candidate["candidate_id"] in tied_ids
                    else "lower-precedence-than-implementation-owner-conflict"
                ),
            )
            for candidate in ordered
        ]
    elif len(top_review_risks) >= 2 and len(distinct_review_owners) >= 2:
        selected = {
            "candidate_id": "review-risk-owner-conflict",
            "candidate_type": "derived-conflict",
            "evidence": sorted(
                f"{candidate['candidate_id']}:"
                f"{REVIEW_RISK_PRIMARY[candidate['candidate_id']]}"
                for candidate in top_review_risks
            ),
            "precedence": top_precedence,
            "reason": "equal-semantic-precedence-owner-conflict",
        }
        tied_risk_ids = {
            candidate["candidate_id"]
            for candidate in top_review_risks
        }
        excluded = [
            _copy_route_candidate_with_reason(
                candidate,
                (
                    "ambiguous-review-owner"
                    if candidate["candidate_id"] in tied_risk_ids
                    else "lower-precedence-than-review-risk-owner-conflict"
                ),
            )
            for candidate in ordered
        ]
    elif len(top_explicit_routes) >= 2:
        contracts: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
        for candidate in top_explicit_routes:
            contract = tuple(
                tuple(candidate[field])
                if field == "layer3_skills"
                else candidate[field]
                for field in ROUTE_CONTRACT_FIELDS
            )
            contracts.setdefault(contract, []).append(candidate)
        source_ids = sorted(
            candidate["candidate_id"]
            for candidate in top_explicit_routes
        )
        if len(contracts) == 1:
            contract_candidates = next(iter(contracts.values()))
            contract = contract_candidates[0]
            selected = {
                **contract,
                "candidate_id": "merged-route-candidate",
                "candidate_type": "merged-route",
                "evidence": sorted(
                    {
                        evidence
                        for candidate in contract_candidates
                        for evidence in candidate["evidence"]
                    }
                ),
                "source_candidate_ids": source_ids,
                "reason": "equal-precedence-same-contract-merge",
            }
            selected.pop("semantic_atoms", None)
            excluded = [
                _copy_route_candidate_with_reason(
                    candidate,
                    (
                        "merged-into-route-contract"
                        if candidate in contract_candidates
                        else "lower-precedence-than-merged-route-candidate"
                    ),
                )
                for candidate in ordered
            ]
        else:
            selected = _route_contract_conflict_candidate(
                top_explicit_routes,
                precedence=top_precedence,
            )
            excluded = [
                _copy_route_candidate_with_reason(
                    candidate,
                    (
                        "ambiguous-route-contract"
                        if candidate in top_explicit_routes
                        else "lower-precedence-than-route-contract-conflict"
                    ),
                )
                for candidate in ordered
            ]
    else:
        selected = (
            {
                **copy.deepcopy(ordered[0]),
                "reason": (
                    ordered[0]["reason"]
                    if (
                        ordered[0]["candidate_type"] == "derived-conflict"
                        and "reason" in ordered[0]
                    )
                    else "highest-semantic-precedence"
                ),
            }
            if ordered
            else None
        )
        excluded = [
            _copy_route_candidate_with_reason(
                candidate,
                (
                    f"lower-precedence-than-{selected['candidate_id']}"
                    if selected is not None
                    else "not-selected"
                ),
            )
            for candidate in ordered[1:]
        ]

    if isinstance(selected, dict) and "source_candidate_ids" not in selected:
        selected["source_candidate_ids"] = [selected["candidate_id"]]

    marker_prefix = "domain-layer3-incompatible:"
    if (
        isinstance(selected, dict)
        and selected.get("candidate_type") != "derived-conflict"
    ):
        markers = [
            item
            for item in selected.get("evidence", [])
            if isinstance(item, str) and item.startswith(marker_prefix)
        ]
        if markers:
            marker_source = next(
                (
                    candidate
                    for candidate in ordered
                    if any(
                        isinstance(item, str)
                        and item.startswith(marker_prefix)
                        for item in candidate.get("evidence", [])
                    )
                    and (
                        candidate["candidate_id"]
                        == selected["candidate_id"]
                        or candidate["candidate_id"]
                        in selected.get("source_candidate_ids", [])
                    )
                ),
                selected,
            )
            source_candidate_ids = sorted(
                set(
                    selected.get(
                        "source_candidate_ids",
                        [selected["candidate_id"]],
                    )
                )
            )
            selected = {
                "candidate_id": "route-contract-conflict",
                "candidate_type": "derived-conflict",
                "evidence": list(markers),
                "source_candidate_ids": source_candidate_ids,
                "precedence": selected.get("precedence"),
                "reason": "domain-layer3-authorization-conflict",
                "path": "analyzed",
                "profile": "analysis-agent",
                "primary_skill": "engineering-change-analysis",
                "layer3_skills": ["repository-context-map"],
                "review_skill": "architecture-impact-reviewer",
            }
            for field in (
                "candidate_layer3_context",
                *ROUTE_CANDIDATE_LAYER3_FIELDS,
            ):
                if field in marker_source:
                    selected[field] = copy.deepcopy(marker_source[field])
            excluded = [
                _copy_route_candidate_with_reason(
                    candidate,
                    (
                        "domain-layer3-authorization-conflict"
                        if candidate["candidate_id"]
                        in source_candidate_ids
                        else "lower-precedence-than-route-contract-conflict"
                    ),
                )
                for candidate in ordered
            ]
    excluded.extend(artifact_preexcluded)
    selection = {
        "raw_candidates": ordered,
        "selected_candidate": selected,
        "excluded_candidates": excluded,
    }
    private_value = object()

    def scrub_binding(value: Any) -> Any:
        if (
            isinstance(value, str)
            and value.startswith("brb1:")
        ):
            return private_value
        if isinstance(value, dict):
            scrubbed_mapping: dict[str, Any] = {}
            for key, item in value.items():
                if key == "artifact_binding_id":
                    continue
                scrubbed_item = scrub_binding(item)
                if scrubbed_item is not private_value:
                    scrubbed_mapping[key] = scrubbed_item
            return scrubbed_mapping
        if isinstance(value, list):
            scrubbed_list = [
                scrub_binding(item)
                for item in value
            ]
            return [
                item
                for item in scrubbed_list
                if item is not private_value
            ]
        if isinstance(value, tuple):
            scrubbed_tuple = tuple(
                scrub_binding(item)
                for item in value
            )
            return tuple(
                item
                for item in scrubbed_tuple
                if item is not private_value
            )
        return value

    scrubbed_selection = scrub_binding(selection)
    assert isinstance(scrubbed_selection, dict)
    return scrubbed_selection


def _validated_brief_review_binding(
    main_execution: dict[str, Any],
) -> str | None:
    """Return one private token for an exact accepted Brief159 authority."""

    if "level_basis" not in main_execution:
        return None

    trigger_evaluations = main_execution["level_basis"][
        "trigger_evaluations"
    ]
    binding_rows = [
        row
        for row in trigger_evaluations
        if isinstance(row, dict)
        and isinstance(row.get("source_anchor"), str)
        and row["source_anchor"].startswith(
            _BRIEF_REVIEW_BINDING_NAMESPACE_STEM
        )
    ]
    if not binding_rows:
        return None
    if len(binding_rows) != 1:
        raise RoutingIntegrityError(
            "Main must provide exactly one Brief159 binding authority"
        )

    row = binding_rows[0]
    record = row["source_anchor"]
    if (
        main_execution["execution_level"] not in {"L4", "L5"}
        or "high-risk pre-implementation evidence"
        not in main_execution["level_basis"]["obligations"]
        or row.get("id") != "major-architecture-or-physical-safety"
        or row.get("status") != "matched"
        or row.get("evidence_kind") != "analysis_handoff"
        or row.get("plausible_critical") is not False
    ):
        raise RoutingIntegrityError(
            "Brief159 binding authority context is not exact"
        )
    if (
        not record.isascii()
        or any(character.isspace() for character in record)
    ):
        raise RoutingIntegrityError(
            "Brief159 binding record must be whitespace-free ASCII"
        )

    parts = record.split("|")
    if (
        len(parts) != len(_BRIEF_REVIEW_BINDING_FIELDS) + 1
        or parts[0] != _BRIEF_REVIEW_BINDING_VERSION
    ):
        raise RoutingIntegrityError(
            "Brief159 binding record version or field count is invalid"
        )
    values: dict[str, str] = {}
    for field, part in zip(
        _BRIEF_REVIEW_BINDING_FIELDS,
        parts[1:],
        strict=True,
    ):
        prefix = f"{field}="
        if not part.startswith(prefix):
            raise RoutingIntegrityError(
                "Brief159 binding record field order is invalid"
            )
        value = part[len(prefix) :]
        if not value:
            raise RoutingIntegrityError(
                f"Brief159 binding field {field!r} must be non-empty"
            )
        values[field] = value

    if (
        values["task_id"] != main_execution["task_id"]
        or values["review_skill"] != "high-risk-design-review"
        or values["artifact_kind"] != "engineering-brief"
        or values["currentness_status"] != "verified"
        or values["acceptance_status"] != "accepted"
    ):
        raise RoutingIntegrityError(
            "Brief159 binding record contradicts its fixed authority"
        )
    for field in (
        "artifact_sha256",
        "source_state_sha256",
        "currentness_proof_sha256",
        "acceptance_evidence_sha256",
        "binding_sha256",
    ):
        if _LOWER_SHA256_PATTERN.fullmatch(values[field]) is None:
            raise RoutingIntegrityError(
                f"Brief159 binding field {field!r} is not lowercase SHA-256"
            )

    unsigned = "|".join(parts[:-1])
    expected_digest = hashlib.sha256(unsigned.encode("utf-8")).hexdigest()
    if values["binding_sha256"] != expected_digest:
        raise RoutingIntegrityError(
            "Brief159 binding digest does not match its canonical record"
        )
    return f"brb1:{values['binding_sha256']}"


def _validated_main_execution_copy(
    main_execution: object,
) -> dict[str, Any]:
    """Fail closed on Main Analysis assignment or executable input."""

    errors = validate_main_assignment(main_execution)
    if errors:
        raise RoutingIntegrityError("; ".join(errors))
    try:
        copied = copy.deepcopy(main_execution)
    except (RecursionError, TypeError, ValueError, OverflowError) as exc:
        raise RoutingIntegrityError(
            f"main execution input cannot be copied: {exc}"
        ) from exc
    assert isinstance(copied, dict)
    return copied


_TERMINAL_ACTION_AMBIGUITY_MAIN_ERROR = (
    "terminal task-action ambiguity requires Main-provided L3 Proof Limit provenance"
)


def _validate_terminal_action_ambiguity_main(
    main_execution: dict[str, Any],
) -> None:
    """Validate selected terminal ambiguity provenance without recomputing it."""

    contract = CORE_CONTRACTS["execution_level_contract"]
    target = "no-unresolved-owner-placement-verification-or-rollback-gap"
    task_id = main_execution["task_id"]
    expected_triggers = [
        {
            "id": row["id"],
            "status": "not_matched",
            "evidence_kind": "analysis_handoff",
            "source_anchor": f"task:{task_id}:trigger:{row['id']}",
            "plausible_critical": False,
        }
        for row in contract["trigger_registry"]
    ]
    expected_l2 = [
        {
            "id": row["id"],
            "status": "unknown" if row["id"] == target else "false",
            "evidence_kind": "analysis_handoff",
            "source_anchor": (
                f"task:{task_id}:terminal-task-action-ambiguity-proof-limit"
                if row["id"] == target
                else f"task:{task_id}:l2:{row['id']}"
            ),
        }
        for row in contract["l2_eligibility"]
    ]
    expected_obligations = list(
        dict.fromkeys(
            [
                obligation
                for level in contract["levels"]
                if level["rank"] <= 3
                for obligation in level["obligations"]
            ]
            + list(contract["non_bypassable"])
        )
    )
    basis = main_execution["level_basis"]
    valid = (
        isinstance(basis, dict)
        and main_execution["execution_level"] == "L3"
        and basis.get("trigger_evaluations") == expected_triggers
        and basis.get("l2_eligibility") == expected_l2
        and basis.get("unresolved") == [target]
        and basis.get("edit_status") == "allowed"
        and basis.get("obligations") == expected_obligations
    )
    if not valid:
        raise RoutingIntegrityError(
            _TERMINAL_ACTION_AMBIGUITY_MAIN_ERROR
        )


def _professional_automatic_decision_authority(
    data: object,
    *,
    context: str,
) -> dict[str, Any]:
    """Canonicalize every automatic-owner field used by routing decisions."""

    authority = professional_automatic_routing_authority(
        data,
        context=context,
    )
    owners = authority["owners_by_family"]
    policy = authority["policy"]
    assert isinstance(owners, dict)
    assert isinstance(policy, dict)
    implementation_policy = policy["implementation_owner"]
    accepted = implementation_policy["accepted"]
    conflict = implementation_policy["conflict"]
    return {
        "owners_by_family": {
            family: {
                "name": owners[family]["name"],
                "layer3_candidates": sorted(
                    owners[family]["layer3_candidates"]
                ),
            }
            for family in sorted(owners)
        },
        "implementation_owner_policy": {
            "accepted_path": accepted["path"],
            "accepted_profile": accepted["profile"],
            "max_layer3": accepted["layer3"]["max"],
            "default_review_skill": accepted["review"]["default"],
            "conflict": {
                "path": conflict["path"],
                "profile": conflict["profile"],
                "primary_skill": conflict["primary_skill"],
                "layer3_skills": list(conflict["layer3_skills"]),
                "review_skill": conflict["review_skill"],
                "reason": conflict["reason"],
            },
        },
    }


def _domain_modifier_decision_authority(
    domain_data: object,
    professional_data: object,
    *,
    domain_context: str,
    professional_context: str,
) -> dict[str, Any]:
    """Canonicalize Domain mode, ownership, and role relationships."""

    authority = domain_modifier_routing_authority(
        domain_data,
        professional_data,
        domain_context=domain_context,
        professional_context=professional_context,
    )
    assert isinstance(domain_data, dict)
    assert isinstance(professional_data, dict)
    domain_entries = domain_data["domain_skills"]
    professional_entries = professional_data["professional_skills"]
    assert isinstance(domain_entries, list)
    assert isinstance(professional_entries, list)
    domains_by_name = {
        entry["name"]: entry
        for entry in domain_entries
        if isinstance(entry, dict)
    }
    professionals_by_name = {
        entry["name"]: entry
        for entry in professional_entries
        if isinstance(entry, dict)
    }
    domains_by_professional = authority["domains_by_professional"]
    assert isinstance(domains_by_professional, dict)
    owning_professionals = sorted(
        name
        for name, domains in domains_by_professional.items()
        if domains
    )
    return {
        "domains_by_name": {
            name: {
                "routing_mode": domains_by_name[name]["routing_mode"],
                "used_by": sorted(domains_by_name[name]["used_by"]),
                "role_support": sorted(
                    domains_by_name[name]["role_support"]
                ),
            }
            for name in sorted(domains_by_name)
        },
        "domains_by_professional": {
            name: sorted(domains_by_professional[name])
            for name in owning_professionals
        },
        "professional_role_support_by_owner": {
            name: sorted(professionals_by_name[name]["role_support"])
            for name in owning_professionals
        },
    }


def _route_decision_envelope(
    route_projection: dict[str, Any],
    winner_trace: dict[str, Any],
    *,
    main_execution: dict[str, Any],
    routing_authority: dict[str, object],
) -> dict[str, Any]:
    """Project one selected route into the exact Core decision envelope."""

    profile = route_projection["profile"]
    primary_skill = route_projection["primary_skill"]
    review_skill = route_projection["review_skill"]
    selected_layer3 = list(route_projection["layer3_skills"])
    primary_authority = list(
        routing_authority["primary_skills_by_profile"][profile]
    )
    review_authority = list(routing_authority["review_skills"])
    layer3_authority = list(
        routing_authority["layer3_candidates_by_primary"][primary_skill]
    )
    if primary_skill not in primary_authority:
        raise RoutingIntegrityError(
            "selected primary Skill is absent from current profile authority"
        )
    if review_skill not in review_authority:
        raise RoutingIntegrityError(
            "selected review Skill is absent from current review authority"
        )
    if not set(selected_layer3) <= set(layer3_authority):
        raise RoutingIntegrityError(
            "selected Layer 3 Skill is absent from current primary authority"
        )

    raw_evidence = winner_trace.get("match_evidence")
    evidence_anchors = (
        list(dict.fromkeys(raw_evidence))
        if isinstance(raw_evidence, list)
        and raw_evidence
        and all(isinstance(item, str) and item for item in raw_evidence)
        else ["no-eligible-specific-candidate"]
    )
    evidence_ids = [
        f"route-evidence-{index}"
        for index in range(1, len(evidence_anchors) + 1)
    ]
    task_evidence = [
        {
            "id": evidence_id,
            "kind": "routing_candidate",
            "task_id": main_execution["task_id"],
            "source_anchor": source_anchor,
        }
        for evidence_id, source_anchor in zip(
            evidence_ids,
            evidence_anchors,
            strict=True,
        )
    ]

    def partition(
        authority: list[str],
        selected: list[str],
        rejection_reason: str,
    ) -> list[dict[str, Any]]:
        ordered = [*selected, *(name for name in authority if name not in selected)]
        return [
            {
                "skill": name,
                "eligible": name in selected,
                "evidence_ids": list(evidence_ids),
                "rejection_reasons": (
                    []
                    if name in selected
                    else [rejection_reason]
                ),
            }
            for name in ordered
        ]

    analysis_path = route_projection["path"] == "analyzed"
    level_basis = (
        None
        if analysis_path
        else copy.deepcopy(main_execution["level_basis"])
    )
    return {
        "path": route_projection["path"],
        "route_result": {
            "start_profile": profile,
            "primary_skill": primary_skill,
            "layer3_skills": selected_layer3,
            "review_skill": review_skill,
            "execution_level": (
                None if analysis_path else main_execution["execution_level"]
            ),
            "level_basis": level_basis,
        },
        "selection_evidence": {
            "task_evidence": task_evidence,
            "primary_candidates": partition(
                primary_authority,
                [primary_skill],
                "not-selected-by-primary-route-precedence",
            ),
            "review_candidates": partition(
                review_authority,
                [review_skill],
                "not-selected-by-review-route-precedence",
            ),
            "layer3_candidates": partition(
                layer3_authority,
                selected_layer3,
                "not-selected-by-layer3-route-evidence",
            ),
            "eligible_primary_count": 1,
        },
        "main_execution_provenance": (
            None if analysis_path else copy.deepcopy(main_execution)
        ),
        "route_once": True,
    }


@dataclass(frozen=True)
class _ExperienceDecisionRecord:
    scope: str
    effect: str
    force: str | None
    action_verb: str | None
    action_polarity: str | None
    subject: str
    family: str


@dataclass(frozen=True)
class _ExperienceAnalysisSubject:
    subject: str
    scope: str
    reference_only: bool
    records: tuple[_ExperienceDecisionRecord, ...]


_EXPERIENCE_ADJACENT_REFERENCE_RE = re.compile(
    r"\b(?:documentation(?:\s+(?:and\s+)?reference)?|"
    r"reference)\s+only\b"
)
_EXPERIENCE_FAMILY_SPECS = {
    "interaction": (
        (
            "interaction state",
            "interaction states",
            "state transition",
            "state transitions",
            "loading state",
            "loading states",
            "error state",
            "error states",
            "focus state",
            "focus states",
            "permission state",
            "permission states",
            "accessibility state",
            "accessibility states",
            "loading",
            "error",
            "focus",
            "permission",
            "accessibility",
            "transition",
            "transitions",
            "transition behavior",
            "recovery",
        ),
        ("decision", "decide", "define", "model", "change"),
    ),
    "design-system": (
        (
            "design token",
            "design tokens",
            "component",
            "components",
            "design system",
            "spacing",
            "typography",
            "variant",
            "variants",
        ),
        (
            "decision",
            "decide",
            "choose",
            "define",
            "apply",
            "select",
            "change",
        ),
    ),
}


def _experience_analysis_subjects(
    value: str,
    *,
    parsed: _ParsedTaskRequest,
) -> tuple[_ExperienceAnalysisSubject, ...]:
    """Build bounded experience records from the parsed action graph."""

    text = " ".join(value.casefold().split())
    analysis_actions = tuple(
        action
        for action in parsed.task_actions.actions
        if action.role in {"direct", "coordinated"}
        and action.verb in {"analyze", "analyse"}
        and action.polarity == EFFECT_CHANGED
        and action.object_span is not None
        and "user flow"
        in text[
            action.object_span.normalized[0]:action.object_span.normalized[1]
        ]
    )
    subjects: list[_ExperienceAnalysisSubject] = []
    for action in analysis_actions:
        subject = f"experience:{action.action_id}"
        root_scope = text[
            action.object_span.normalized[0]:
            action.object_span.normalized[1]
        ]
        owned_scopes = [(root_scope, None, None)]
        owned_scopes.extend(
            (
                text[
                    child.object_span.normalized[0]:
                    child.object_span.normalized[1]
                ],
                child.verb,
                child.polarity,
            )
            for child in parsed.task_actions.actions
            if child.parent_action_id == action.action_id
            and child.role == "coordinated"
            and child.object_span is not None
        )
        records: list[_ExperienceDecisionRecord] = []
        for object_scope, action_verb, action_polarity in owned_scopes:
            for _scope_id, bounded_scope in _bounded_effect_scopes(
                object_scope
            ):
                for family, (
                    anchors,
                    forces,
                ) in _EXPERIENCE_FAMILY_SPECS.items():
                    if not any(
                        _contains_signal(bounded_scope, anchor)
                        for anchor in anchors
                    ):
                        continue
                    if action_verb is None:
                        local_forces = tuple(
                            force
                            for force in forces
                            if _contains_signal(bounded_scope, force)
                        )
                        effect_records = _semantic_decision_records(
                            bounded_scope,
                            f"experience-{family}",
                            anchors,
                            forces,
                        )
                        if not effect_records:
                            continue
                        effect = effect_records[0][1]
                        force = "|".join(local_forces) or None
                    else:
                        force = action_verb
                        if _scope_is_ambiguous(bounded_scope):
                            effect = EFFECT_AMBIGUOUS
                        elif _scope_is_unchanged(bounded_scope):
                            effect = EFFECT_UNCHANGED
                        elif action_polarity in {
                            EFFECT_CHANGED,
                            EFFECT_UNCHANGED,
                            EFFECT_AMBIGUOUS,
                        }:
                            effect = action_polarity
                        else:
                            effect = EFFECT_ADJACENT_ONLY
                    records.append(
                        _ExperienceDecisionRecord(
                            scope=bounded_scope,
                            effect=effect,
                            force=force,
                            action_verb=action_verb,
                            action_polarity=action_polarity,
                            subject=subject,
                            family=family,
                        )
                    )
        subject_scope = "; ".join(
            object_scope
            for object_scope, _action_verb, _action_polarity in owned_scopes
        )
        subjects.append(
            _ExperienceAnalysisSubject(
                subject=subject,
                scope=subject_scope,
                reference_only=(
                    _EXPERIENCE_ADJACENT_REFERENCE_RE.search(
                        _normalize_effect_scope(subject_scope)
                    )
                    is not None
                ),
                records=tuple(records),
            )
        )
    return tuple(subjects)


def _experience_analysis_foundations(
    value: str,
    *,
    parsed: _ParsedTaskRequest,
) -> tuple[str, ...]:
    """Return the exact declared user-flow Foundation member subset."""

    analysis_subjects = _experience_analysis_subjects(
        value,
        parsed=parsed,
    )
    interaction_semantics = False
    design_semantics = False
    for analysis_subject in analysis_subjects:
        scope = analysis_subject.scope
        interaction_effects = {
            record.effect
            for record in analysis_subject.records
            if record.family == "interaction"
        }
        interaction_subject = (
            (
                re.search(r"\bstates?\b", scope) is not None
                and any(
                    signal in scope
                    for signal in (
                        "loading",
                        "error",
                        "focus",
                        "permission",
                        "accessibility",
                    )
                )
            )
            or (
                re.search(r"\b(?:state\s+)?transitions?\b", scope)
                is not None
                and any(
                    signal in scope
                    for signal in (
                        "loading",
                        "error",
                        "focus",
                        "permission",
                        "accessibility",
                    )
                )
            )
        )
        interaction_semantics = interaction_semantics or (
            interaction_subject
            and not interaction_effects.intersection(
                {EFFECT_UNCHANGED, EFFECT_AMBIGUOUS}
            )
            and (
                not analysis_subject.reference_only
                or EFFECT_CHANGED in interaction_effects
            )
        )

        design_effects = {
            record.effect
            for record in analysis_subject.records
            if record.family == "design-system"
        }
        design_subject = (
            (
                "design token" in scope
                and "component" in scope
                and (
                    any(
                        rule_dimension in scope
                        for rule_dimension in ("spacing", "typography")
                    )
                    or "variant" in scope
                )
            )
            or (
                "design system" in scope
                and re.search(
                    r"\b(?:decision|rules?|constraints?)\b",
                    scope,
                )
                is not None
            )
        )
        design_semantics = design_semantics or (
            design_subject
            and not design_effects.intersection(
                {EFFECT_UNCHANGED, EFFECT_AMBIGUOUS}
            )
            and (
                not analysis_subject.reference_only
                or EFFECT_CHANGED in design_effects
            )
        )

    selected = []
    if interaction_semantics:
        selected.append("interaction-state-modeling")
    if design_semantics:
        selected.append("design-system-rules")
    return tuple(selected)


_EXTERNAL_CONCERN_ORDER = (
    "consumer",
    "failure",
    "reliability",
)
_EXTERNAL_INTEGRATION_SUBJECT_RE = re.compile(
    r"\bexternal integration\b"
)
_EXTERNAL_SESSION_TERMINATOR_RE = re.compile(r"[.!?]+")
_EXTERNAL_LEXICAL_TOKEN_RE = re.compile(r"[a-z0-9]+")
_EXTERNAL_SCOPE_NEGATIVE_PREFIX_RE = re.compile(
    r"(?:no|without)\b(?:\s+changing)?"
    r"(?:\s+(?:a|an|the))?\s*"
)
_EXTERNAL_CONSUMER_ALIASES = (
    ("downstream", re.compile(r"\bdownstream\b")),
    ("consumer", re.compile(r"\bconsumer\b")),
    ("compatibility", re.compile(r"\bcompatibility\b")),
    ("schema", re.compile(r"\bschema\b")),
)
_EXTERNAL_RELIABILITY_SUBJECT_ALIASES = (
    ("outage", re.compile(r"\boutages?\b")),
    ("slo", re.compile(r"\bslos?\b")),
    ("degradation", re.compile(r"\bdegradation\b")),
    ("timeout", re.compile(r"\btimeouts?\b")),
    ("retry", re.compile(r"\bretr(?:y|ies)\b")),
    ("backoff", re.compile(r"\bbackoff\b")),
    ("fallback", re.compile(r"\bfallback\b")),
    ("recovery", re.compile(r"\brecovery\b")),
    ("bulkhead", re.compile(r"\bbulkheads?\b")),
    (
        "circuit-breaker",
        re.compile(
            r"\b(?:circuit[- ]breakers?|circuit[- ]breaking)\b"
        ),
    ),
)
_EXTERNAL_RELIABILITY_HEAD_ALIASES = (
    ("behavior", re.compile(r"\bbehaviors?\b")),
    ("mechanics", re.compile(r"\bmechanics?\b")),
    ("policy", re.compile(r"\bpolic(?:y|ies)\b")),
    ("risk", re.compile(r"\brisks?\b")),
)
_EXTERNAL_FAILURE_SUBJECT_RE = re.compile(
    r"\b(?:failure\s+contract|retryable|terminal|timeouts?|"
    r"cancellation|(?:safe|error|failure)\s+representation)\b"
)
_EXTERNAL_RELATION_SEMANTICS = MappingProxyType(
    {
        "direct_effect_nominals": frozenset(
            {
                "change",
                "modification",
            }
        ),
        "wrapper_operators": frozenset(
            {
                ("reference", "to"),
                ("documentation", "about"),
                ("example", "mentioning"),
            }
        ),
        "different_owner_heads": frozenset(
            {
                "service",
                "database",
                "queue",
            }
        ),
        "same_context_heads": frozenset(
            {
                "deployment",
                "client",
                "failover",
            }
        ),
        "owner_modifiers": frozenset(
            {
                "local",
                "internal",
            }
        ),
        "uncertain_owner_modifiers": frozenset(
            {
                "unrelated",
            }
        ),
        "metadata_head_surfaces": frozenset(
            {
                "field",
                "fields",
                "label",
                "labels",
                "identifier",
                "identifiers",
                "enum",
                "enums",
                "key",
                "keys",
                "property",
                "properties",
                "column",
                "columns",
            }
        ),
        "owner_relations": frozenset(
            {
                "for",
                "in",
            }
        ),
        "articles": frozenset(
            {
                "a",
                "an",
                "the",
            }
        ),
        "surface_to_canonical": MappingProxyType(
            {
                "clients": "client",
            }
        ),
        "effect_action_surfaces": MappingProxyType(
            {
                "change": "change",
                "changes": "change",
                "changed": "change",
                "changing": "change",
                "choose": "choose",
                "decide": "decide",
                "define": "define",
                "implement": "implement",
                "model": "model",
                "redesign": "redesign",
                "update": "update",
                "updates": "update",
                "updated": "update",
            }
        ),
    }
)
_EXTERNAL_METADATA_HEAD_RE = re.compile(
    r"^\s+(?:"
    + "|".join(
        sorted(
            _EXTERNAL_RELATION_SEMANTICS[
                "metadata_head_surfaces"
            ],
            key=lambda item: (-len(item), item),
        )
    )
    + r")\b"
)


@dataclass(frozen=True, slots=True)
class _ExternalConcernEffectRecord:
    """One clause-local external concern observation."""

    session_id: int
    clause_id: int
    concern: str
    subject_alias: str
    semantic_head: str
    effect: str
    scope: str


@dataclass(frozen=True, slots=True)
class _ExternalRelationSemanticClassification:
    """One closed external-only semantic classification."""

    category: str
    member: str | None
    evidence: tuple[str, ...]
    span: tuple[int, int] | None


@dataclass(frozen=True, slots=True)
class _ExternalEffectScopeBinding:
    """Bind one concern to parsed action and continuation ownership."""

    session_id: int
    clause_id: int
    scope: str
    external_subject_span: tuple[int, int] | None
    concern: str
    subject_alias: str
    semantic_head: str
    subject_span: tuple[int, int]
    head_span: tuple[int, int]
    concern_prefix_span: tuple[int, int] | None
    shared_terminal_effect_span: tuple[int, int] | None
    action_id: str | None
    action_verb: str | None
    action_span: tuple[int, int] | None
    action_polarity: str | None
    action_prefix_span: _TaskSpan | None
    action_relation: str
    continuation_owner: str
    semantic_category: str
    semantic_evidence: tuple[str, ...]
    owner_candidate_spans: tuple[tuple[int, int], ...]
    effect_window_span: tuple[int, int]
    barrier_span: tuple[int, int]
    predicate_scope: str


def _classify_external_relation_semantics(
    phrase: str,
    *,
    relation_context: str,
    concern: str | None = None,
    span: tuple[int, int] | None = None,
) -> _ExternalRelationSemanticClassification:
    """Classify one fully bounded phrase from the closed semantic SSOT."""

    normalized = _normalize_effect_scope(phrase)
    raw_tokens = tuple(normalized.split())
    surface_to_canonical = _EXTERNAL_RELATION_SEMANTICS[
        "surface_to_canonical"
    ]
    tokens = tuple(
        surface_to_canonical.get(token, token)
        for token in raw_tokens
    )
    evidence_span = (
        span
        if span is not None
        else ((0, len(normalized)) if normalized else None)
    )

    if relation_context == "action-object":
        articles = _EXTERNAL_RELATION_SEMANTICS["articles"]
        bounded = list(tokens)
        if bounded and bounded[0] in articles:
            bounded.pop(0)
        if bounded and bounded[-1] in articles:
            bounded.pop()
        if not bounded:
            return _ExternalRelationSemanticClassification(
                category="direct-immediate",
                member=None,
                evidence=tokens,
                span=evidence_span,
            )
        if (
            len(bounded) == 2
            and bounded[0]
            in _EXTERNAL_RELATION_SEMANTICS[
                "direct_effect_nominals"
            ]
            and bounded[1] == "to"
        ):
            return _ExternalRelationSemanticClassification(
                category="direct-effect",
                member=bounded[0],
                evidence=tuple(bounded),
                span=evidence_span,
            )
        if (
            len(bounded) == 2
            and tuple(bounded)
            in _EXTERNAL_RELATION_SEMANTICS["wrapper_operators"]
        ):
            return _ExternalRelationSemanticClassification(
                category="wrapper",
                member=" ".join(bounded),
                evidence=tuple(bounded),
                span=evidence_span,
            )
        return _ExternalRelationSemanticClassification(
            category="unknown",
            member=None,
            evidence=tuple(bounded),
            span=evidence_span,
        )

    if relation_context != "continuation-owner":
        raise ValueError(
            f"unknown external relation context {relation_context!r}"
        )

    bounded = list(tokens)
    effect_actions = _EXTERNAL_RELATION_SEMANTICS[
        "effect_action_surfaces"
    ]
    if bounded and bounded[0] in effect_actions:
        bounded.pop(0)
    if bounded and bounded[-1] in effect_actions:
        bounded.pop()
    elif (
        len(bounded) >= 2
        and bounded[-1] == "unchanged"
        and bounded[-2] in {"remain", "remains", "stay", "stays"}
    ):
        del bounded[-2:]
    if not bounded:
        return _ExternalRelationSemanticClassification(
            category="none",
            member=None,
            evidence=(),
            span=evidence_span,
        )

    owner_relations = _EXTERNAL_RELATION_SEMANTICS[
        "owner_relations"
    ]
    articles = _EXTERNAL_RELATION_SEMANTICS["articles"]
    owner_modifiers = _EXTERNAL_RELATION_SEMANTICS[
        "owner_modifiers"
    ]
    uncertain_modifiers = _EXTERNAL_RELATION_SEMANTICS[
        "uncertain_owner_modifiers"
    ]
    all_modifiers = owner_modifiers | uncertain_modifiers
    different_heads = _EXTERNAL_RELATION_SEMANTICS[
        "different_owner_heads"
    ]
    context_heads = _EXTERNAL_RELATION_SEMANTICS[
        "same_context_heads"
    ]
    all_heads = different_heads | context_heads
    metadata_heads = _EXTERNAL_RELATION_SEMANTICS[
        "metadata_head_surfaces"
    ]
    relation = (
        bounded[0] if bounded[0] in owner_relations else None
    )
    relation_body = (
        list(bounded[1:]) if relation is not None else list(bounded)
    )
    if relation_body and relation_body[0] in articles:
        relation_body.pop(0)

    metadata_candidate = (
        concern in {"consumer", "failure"}
        and any(token in metadata_heads for token in bounded)
        and any(
            pattern.search(" ".join(bounded)) is not None
            for _alias, pattern
            in _EXTERNAL_RELIABILITY_SUBJECT_ALIASES
        )
    )
    if metadata_candidate:
        metadata_body = list(
            bounded[1:]
            if bounded and bounded[0] == "for"
            else bounded
        )
        if metadata_body and metadata_body[0] in articles:
            metadata_body.pop(0)
        metadata_valid = (
            bool(metadata_body)
            and bounded[0] == "for"
            and metadata_body[-1] in metadata_heads
            and sum(
                token in metadata_heads for token in metadata_body
            )
            == 1
        )
        descriptor_exclusions = (
            set(owner_relations)
            | set(articles)
            | set(all_modifiers)
            | set(all_heads)
            | set(metadata_heads)
            | set(effect_actions)
            | {
                "remain",
                "remains",
                "stay",
                "stays",
                "unchanged",
            }
        )
        subject_descriptor = " ".join(metadata_body[:-1])
        subject_matches: list[tuple[str, ...]] = []
        if metadata_valid:
            for _alias, pattern in (
                _EXTERNAL_RELIABILITY_SUBJECT_ALIASES
            ):
                subject_match = pattern.match(subject_descriptor)
                if (
                    subject_match is None
                    or subject_match.start() != 0
                ):
                    continue
                remainder = tuple(
                    subject_descriptor[
                        subject_match.end():
                    ].strip().split()
                )
                if len(remainder) <= 1:
                    subject_matches.append(remainder)
        metadata_valid = (
            metadata_valid
            and len(subject_matches) == 1
            and not any(
                token in descriptor_exclusions
                or any(
                    pattern.fullmatch(token) is not None
                    for _alias, pattern
                    in _EXTERNAL_RELIABILITY_HEAD_ALIASES
                )
                for token in subject_matches[0]
            )
        )
        return _ExternalRelationSemanticClassification(
            category=(
                "metadata-qualifier"
                if metadata_valid
                else "unknown"
            ),
            member=(
                metadata_body[-1]
                if metadata_valid
                else None
            ),
            evidence=tuple(bounded),
            span=evidence_span,
        )

    if (
        relation is None
        and len(bounded) >= 2
        and bounded[1] in articles
    ):
        return _ExternalRelationSemanticClassification(
            category="unknown",
            member=None,
            evidence=tuple(
                token for token in bounded if token not in articles
            ),
            span=evidence_span,
        )

    if len(relation_body) == 2:
        modifier, head = relation_body
        if modifier in all_modifiers:
            if modifier in uncertain_modifiers:
                category = (
                    "ambiguous-owner"
                    if head in different_heads
                    else "unknown"
                )
            elif head in different_heads:
                category = "different-owner"
            elif head in context_heads:
                category = "same-context"
            else:
                category = "unknown"
            return _ExternalRelationSemanticClassification(
                category=category,
                member=(
                    head
                    if category
                    in {
                        "ambiguous-owner",
                        "different-owner",
                        "same-context",
                    }
                    else None
                ),
                evidence=(modifier, head),
                span=evidence_span,
            )
        if head in all_heads:
            return _ExternalRelationSemanticClassification(
                category="unknown",
                member=None,
                evidence=(modifier, head),
                span=evidence_span,
            )

    if (
        relation is not None
        and len(relation_body) == 1
        and relation_body[0] in all_heads
    ):
        return _ExternalRelationSemanticClassification(
            category="none",
            member=relation_body[0],
            evidence=tuple(relation_body),
            span=evidence_span,
        )

    if any(
        token in all_modifiers or token in all_heads
        for token in relation_body
    ):
        return _ExternalRelationSemanticClassification(
            category="unknown",
            member=None,
            evidence=tuple(relation_body),
            span=evidence_span,
        )

    if relation == "for":
        after_relation = list(bounded[1:])
        article_is_exact = (
            bool(after_relation)
            and after_relation[0] in articles
            and (
                len(after_relation) == 1
                or after_relation[1] not in articles
            )
        )
        opaque_tokens = (
            after_relation[1:] if article_is_exact else ()
        )
        forbidden_opaque_tokens = (
            set(owner_relations)
            | set(articles)
            | set(effect_actions)
            | {
                "remain",
                "remains",
                "stay",
                "stays",
                "unchanged",
            }
        )
        _for_shape_is_exact = (
            article_is_exact
            and 1 <= len(opaque_tokens) <= 3
            and all(
                re.fullmatch(r"[a-z0-9]+", token) is not None
                and token not in forbidden_opaque_tokens
                for token in opaque_tokens
            )
        )
        return _ExternalRelationSemanticClassification(
            category="unknown",
            member=None,
            evidence=tuple(bounded),
            span=evidence_span,
        )

    return _ExternalRelationSemanticClassification(
        category="none",
        member=None,
        evidence=tuple(bounded),
        span=evidence_span,
    )


def _external_subject_session_start(
    parsed: _ParsedTaskRequest,
    subject_span: tuple[int, int],
) -> int:
    """Retain the parser-owned action clause for one external subject."""

    owning_objects = [
        item
        for item in parsed.task_actions.objects
        if (
            item.span.normalized[0] <= subject_span[0]
            and subject_span[1] <= item.span.normalized[1]
        )
    ]
    if len(owning_objects) != 1:
        return subject_span[0]
    action_by_id = {
        action.action_id: action
        for action in parsed.task_actions.actions
    }
    owner = action_by_id.get(owning_objects[0].parent_action_id)
    if owner is None:
        return subject_span[0]
    action_boundaries = [
        span.normalized[0]
        for span in (
            owner.coordinator_span,
            owner.prefix_span,
            owner.subject_span,
            owner.verb_span,
            owner.clause_span,
        )
        if span is not None
    ]
    return min(action_boundaries)


def _external_evidence_action_edge(
    parsed: _ParsedTaskRequest,
    *evidence_spans: tuple[int, int],
) -> tuple[_TaskActionNode, _TaskObjectNode] | None:
    """Return the sole parser object/action edge containing all evidence."""

    owning_objects = [
        item
        for item in parsed.task_actions.objects
        if evidence_spans
        and all(
            item.span.normalized[0] <= evidence_span[0]
            and evidence_span[1] <= item.span.normalized[1]
            for evidence_span in evidence_spans
        )
    ]
    if len(owning_objects) != 1:
        return None
    action = next(
        (
            candidate
            for candidate in parsed.task_actions.actions
            if candidate.action_id
            == owning_objects[0].parent_action_id
        ),
        None,
    )
    return (
        (action, owning_objects[0])
        if action is not None
        else None
    )


def _external_concern_cluster_start(
    scope: str,
    concern: str,
    subject_span: tuple[int, int],
    head_span: tuple[int, int],
    *,
    lower_bound: int,
) -> int:
    """Include only contiguous registered aliases before selected evidence."""

    evidence_start = min(subject_span[0], head_span[0])
    if concern != "consumer":
        return evidence_start
    alias_order = tuple(
        alias for alias, _pattern in _EXTERNAL_CONSUMER_ALIASES
    )
    evidence_match = _EXTERNAL_LEXICAL_TOKEN_RE.match(
        scope,
        evidence_start,
    )
    if (
        evidence_match is None
        or evidence_match.group(0) not in alias_order
    ):
        return evidence_start
    cluster_start = evidence_match.start()
    expected_index = alias_order.index(evidence_match.group(0))
    for token_match in reversed(
        tuple(
            _EXTERNAL_LEXICAL_TOKEN_RE.finditer(
                scope,
                lower_bound,
                evidence_start,
            )
        )
    ):
        if (
            scope[token_match.end():cluster_start].strip()
            or token_match.group(0) not in alias_order
        ):
            break
        token_index = alias_order.index(token_match.group(0))
        if token_index != expected_index - 1:
            return evidence_start
        cluster_start = token_match.start()
        expected_index = token_index
    return cluster_start


def _external_session_scopes(
    value: str,
    *,
    parsed: _ParsedTaskRequest | None = None,
) -> tuple[tuple[int, int, str], ...]:
    """Return normalized scopes owned by explicit external sessions."""

    text = " ".join(value.casefold().split())
    parsed_request = (
        parsed
        if parsed is not None
        else _parse_normalized_task_request(text)
    )
    sessions: list[tuple[int, int, str]] = []
    session_id = 0
    sentence_start = 0
    sentence_spans: list[tuple[int, int]] = []
    for terminator in _EXTERNAL_SESSION_TERMINATOR_RE.finditer(text):
        sentence_spans.append((sentence_start, terminator.start()))
        sentence_start = terminator.end()
    sentence_spans.append((sentence_start, len(text)))
    for sentence_start, sentence_end in sentence_spans:
        subject_matches = list(
            _EXTERNAL_INTEGRATION_SUBJECT_RE.finditer(
                text,
                sentence_start,
                sentence_end,
            )
        )
        session_starts: list[int] = []
        for index, subject_match in enumerate(subject_matches):
            start = _external_subject_session_start(
                parsed_request,
                subject_match.span(),
            )
            if (
                index
                and start <= subject_matches[index - 1].start()
            ):
                start = subject_match.start()
            session_starts.append(start)
        for index, subject_match in enumerate(subject_matches):
            end = (
                session_starts[index + 1]
                if index + 1 < len(subject_matches)
                else sentence_end
            )
            session = text[session_starts[index] : end]
            session = re.sub(
                r"\b(timeout|cancellation)\s*"
                r"(?:/|\band\b|\bor\b)\s*"
                r"(timeout|cancellation)\b",
                r"\1 \2",
                session,
            )
            session = re.sub(
                r"\b(timeout|cancellation)\s+(?:and|/)\s+"
                r"(contract\s+(?:change[ds]?|changing|"
                r"remains?\s+unchanged|stays?\s+unchanged))\b",
                r"\1 \2",
                session,
            )
            effect_surface_pattern = "|".join(
                re.escape(surface)
                for surface in sorted(
                    _EXTERNAL_RELATION_SEMANTICS[
                        "effect_action_surfaces"
                    ],
                    key=lambda item: (-len(item), item),
                )
            )
            session = re.sub(
                r"\b((?:downstream\s+)?consumer\s+compatibility)"
                r"\s+and\s+"
                r"((?:retryable\s+(?:versus|and|/)\s+terminal|"
                r"terminal\s+(?:versus|and|/)\s+retryable)"
                r"(?:\s+(?:outcomes?|meanings?|semantics?|"
                r"classification|contract|representation))*"
                rf"\s+(?:(?:{effect_surface_pattern})|"
                r"remains?\s+unchanged|stays?\s+unchanged))\b",
                r"\1 \2",
                session,
            )
            session = re.sub(
                r"\bwithout\b([^,;!?]*?)\bor\b",
                r"without\1 or no ",
                session,
                count=1,
            )
            for clause_id, scope in _bounded_effect_scopes(session):
                sessions.append(
                    (
                        session_id,
                        clause_id,
                        scope,
                    )
                )
            session_id += 1
    return tuple(sessions)


def _latest_alias(
    scope: str,
    aliases: tuple[tuple[str, re.Pattern[str]], ...],
) -> tuple[str, re.Match[str]] | None:
    """Return the latest finite alias occurrence in one normalized scope."""

    matches = [
        (alias, match)
        for alias, pattern in aliases
        for match in pattern.finditer(scope)
    ]
    return max(matches, key=lambda item: item[1].start()) if matches else None


def _external_concern_selections(
    scope: str,
) -> tuple[
    tuple[
        str,
        str,
        str,
        tuple[int, int],
        tuple[int, int],
    ],
    ...,
]:
    """Select finite concern subjects and heads without deciding effects."""

    selections: list[
        tuple[
            str,
            str,
            str,
            tuple[int, int],
            tuple[int, int],
        ]
    ] = []

    consumer_alias = _latest_alias(
        scope,
        _EXTERNAL_CONSUMER_ALIASES,
    )
    timeout_match = re.search(
        r"\b(?:timeout|cancellation)\b",
        scope,
    )
    contract_match = re.search(r"\bcontract\b", scope)
    timeout_contract = (
        timeout_match is not None
        and contract_match is not None
        and "contract change" in scope
    )
    if consumer_alias is not None or timeout_contract:
        if consumer_alias is None:
            assert timeout_match is not None
            assert contract_match is not None
            consumer_subject_alias = timeout_match.group(0)
            consumer_subject_span = timeout_match.span()
            consumer_head = "contract"
            consumer_head_span = contract_match.span()
        else:
            consumer_subject_alias, consumer_subject_match = (
                consumer_alias
            )
            consumer_subject_span = consumer_subject_match.span()
            consumer_head_match = _latest_alias(
                scope,
                (
                    (
                        "compatibility",
                        re.compile(r"\bcompatibility\b"),
                    ),
                    ("schema", re.compile(r"\bschema\b")),
                    ("contract", re.compile(r"\bcontract\b")),
                ),
            )
            if consumer_head_match is None:
                consumer_head = consumer_subject_alias
                consumer_head_span = consumer_subject_span
            else:
                consumer_head, matched_head = consumer_head_match
                consumer_head_span = matched_head.span()
        selections.append(
            (
                "consumer",
                consumer_subject_alias,
                consumer_head,
                consumer_subject_span,
                consumer_head_span,
            )
        )

    failure_subject_alias = ""
    failure_head = ""
    failure_subject_span = (0, 0)
    failure_head_span = (0, 0)
    failure_contract_match = re.search(
        r"\bfailure\s+contract\b",
        scope,
    )
    if failure_contract_match is not None:
        failure_subject_alias = "failure contract"
        failure_subject_span = failure_contract_match.span()
        contract_head = re.search(
            r"\bcontract\b",
            failure_contract_match.group(0),
        )
        assert contract_head is not None
        failure_head = "contract"
        failure_head_span = (
            failure_contract_match.start() + contract_head.start(),
            failure_contract_match.start() + contract_head.end(),
        )
    elif "retryable" in scope and "terminal" in scope:
        retryable_match = re.search(r"\bretryable\b", scope)
        terminal_match = re.search(r"\bterminal\b", scope)
        assert retryable_match is not None
        assert terminal_match is not None
        failure_subject_alias = "retryable/terminal"
        failure_subject_span = (
            min(retryable_match.start(), terminal_match.start()),
            max(retryable_match.end(), terminal_match.end()),
        )
        matched_head = re.search(
            r"\b(?:classification|contract|meanings?|outcomes?|"
            r"representation|semantics?)\b",
            scope,
        )
        if matched_head is None:
            failure_head = "outcome"
            failure_head_span = failure_subject_span
        else:
            failure_head = matched_head.group(0)
            failure_head_span = matched_head.span()
    else:
        semantic_match = re.search(
            r"\b(?:classification|contract|meanings?|outcomes?|"
            r"representation|semantics?)\b",
            scope,
        )
        representation_match = (
            re.search(r"\b(?:safe|error|failure)\b", scope)
            if "representation" in scope
            else None
        )
        if timeout_match is not None and (
            semantic_match is not None
            or timeout_contract
        ):
            failure_subject_alias = timeout_match.group(0)
            failure_subject_span = timeout_match.span()
            if semantic_match is None:
                assert contract_match is not None
                failure_head = "contract"
                failure_head_span = contract_match.span()
            else:
                failure_head = semantic_match.group(0)
                failure_head_span = semantic_match.span()
        elif representation_match is not None:
            representation_head = re.search(
                r"\brepresentation\b",
                scope,
            )
            assert representation_head is not None
            failure_subject_alias = representation_match.group(0)
            failure_subject_span = representation_match.span()
            failure_head = "representation"
            failure_head_span = representation_head.span()
    if failure_subject_alias:
        selections.append(
            (
                "failure",
                failure_subject_alias,
                failure_head,
                failure_subject_span,
                failure_head_span,
            )
        )

    reliability_subjects = [
        (alias, match)
        for alias, pattern in _EXTERNAL_RELIABILITY_SUBJECT_ALIASES
        for match in pattern.finditer(scope)
    ]
    reliability_heads = [
        (alias, match)
        for alias, pattern in _EXTERNAL_RELIABILITY_HEAD_ALIASES
        for match in pattern.finditer(scope)
        if _EXTERNAL_METADATA_HEAD_RE.match(scope[match.end() :])
        is None
    ]
    for alias, pattern, allowed_subjects in (
        (
            "attempt",
            re.compile(r"\battempts?\b"),
            {"retry"},
        ),
        (
            "budget",
            re.compile(r"\bbudgets?\b"),
            {"retry", "backoff"},
        ),
        (
            "schedule",
            re.compile(r"\bschedules?\b"),
            {"backoff"},
        ),
    ):
        reliability_heads.extend(
            (alias, match)
            for match in pattern.finditer(scope)
            if _EXTERNAL_METADATA_HEAD_RE.match(scope[match.end() :])
            is None
            and any(
                subject_alias in allowed_subjects
                and subject_match.end() <= match.start()
                for subject_alias, subject_match in reliability_subjects
            )
        )
    eligible_pairs = [
        (head_alias, head_match, subject_alias, subject_match)
        for head_alias, head_match in reliability_heads
        for subject_alias, subject_match in reliability_subjects
        if subject_match.end() <= head_match.start()
        and (
            head_alias not in {"attempt", "budget", "schedule"}
            or (
                head_alias == "attempt"
                and subject_alias == "retry"
            )
            or (
                head_alias == "budget"
                and subject_alias in {"retry", "backoff"}
            )
            or (
                head_alias == "schedule"
                and subject_alias == "backoff"
            )
        )
    ]
    if eligible_pairs:
        latest_head_start = max(
            pair[1].start() for pair in eligible_pairs
        )
        head_pairs = [
            pair
            for pair in eligible_pairs
            if pair[1].start() == latest_head_start
        ]
        (
            reliability_head,
            reliability_head_match,
            reliability_subject_alias,
            reliability_subject_match,
        ) = max(head_pairs, key=lambda pair: pair[3].start())
        selections.append(
            (
                "reliability",
                reliability_subject_alias,
                reliability_head,
                reliability_subject_match.span(),
                reliability_head_match.span(),
            )
        )
    return tuple(selections)


def _external_owner_relation_phrases(
    scope: str,
    *,
    explicit_subject_end: int,
    concern_subject_start: int,
    concern_head_end: int,
    effect_window_end: int,
) -> tuple[tuple[str, tuple[int, int]], ...]:
    """Extract exact local owner candidates for one selected concern."""

    modifier_tokens = (
        _EXTERNAL_RELATION_SEMANTICS["owner_modifiers"]
        | _EXTERNAL_RELATION_SEMANTICS[
            "uncertain_owner_modifiers"
        ]
    )
    owner_heads = (
        _EXTERNAL_RELATION_SEMANTICS["different_owner_heads"]
        | _EXTERNAL_RELATION_SEMANTICS["same_context_heads"]
    )
    owner_relations = _EXTERNAL_RELATION_SEMANTICS[
        "owner_relations"
    ]
    metadata_heads = _EXTERNAL_RELATION_SEMANTICS[
        "metadata_head_surfaces"
    ]
    articles = _EXTERNAL_RELATION_SEMANTICS["articles"]
    candidates: list[tuple[str, tuple[int, int]]] = []

    pre_matches = list(
        _EXTERNAL_LEXICAL_TOKEN_RE.finditer(
            scope,
            max(0, explicit_subject_end),
            max(explicit_subject_end, concern_subject_start),
        )
    )
    pre_span: tuple[int, int] | None = None
    if pre_matches and pre_matches[-1].group(0) in modifier_tokens:
        pre_span = pre_matches[-1].span()
    elif (
        len(pre_matches) >= 2
        and pre_matches[-1].group(0) in owner_heads
        and pre_matches[-2].group(0) not in articles
    ):
        pre_span = (
            pre_matches[-2].start(),
            pre_matches[-1].end(),
        )
    if pre_span is not None:
        candidates.append((scope[slice(*pre_span)], pre_span))

    post_matches = list(
        _EXTERNAL_LEXICAL_TOKEN_RE.finditer(
            scope,
            concern_head_end,
            max(concern_head_end, effect_window_end),
        )
    )
    candidate_markers = (
        modifier_tokens
        | owner_heads
        | owner_relations
        | metadata_heads
    )
    if any(
        match.group(0) in candidate_markers
        for match in post_matches
    ):
        post_span = (
            post_matches[0].start(),
            post_matches[-1].end(),
        )
        candidates.append((scope[slice(*post_span)], post_span))
    return tuple(candidates)


def _build_external_effect_scope_bindings(
    value: str,
    *,
    parsed: _ParsedTaskRequest | None = None,
) -> tuple[_ExternalEffectScopeBinding, ...]:
    """Build the sole parser-bound external concern representation."""

    text = " ".join(value.casefold().split())
    parsed_request = (
        parsed
        if parsed is not None
        else _parse_normalized_task_request(text)
    )
    bindings: list[_ExternalEffectScopeBinding] = []
    for (
        session_id,
        clause_id,
        scope,
    ) in _external_session_scopes(text, parsed=parsed_request):
        local_parse = _parse_normalized_task_request(scope)
        local_external_subjects = tuple(
            _EXTERNAL_INTEGRATION_SUBJECT_RE.finditer(scope)
        )
        scope_external_subject = (
            local_external_subjects[0]
            if len(local_external_subjects) == 1
            else None
        )
        external_subject_span = (
            scope_external_subject.span()
            if scope_external_subject is not None
            else None
        )
        explicit_subject_end = (
            scope_external_subject.end()
            if scope_external_subject is not None
            else 0
        )

        scope_action: _TaskActionNode | None = None
        scope_action_relation = "no-action"
        scope_action_semantics = (
            _ExternalRelationSemanticClassification(
                category="none",
                member=None,
                evidence=(),
                span=None,
            )
        )
        if clause_id == 0 and external_subject_span is not None:
            edge = _external_evidence_action_edge(
                local_parse,
                external_subject_span,
            )
            containing_objects = [
                item
                for item in local_parse.task_actions.objects
                if (
                    item.span.normalized[0]
                    <= external_subject_span[0]
                    and external_subject_span[1]
                    <= item.span.normalized[1]
                )
            ]
            if edge is not None:
                scope_action, owning_object = edge
                object_prefix = scope[
                    owning_object.span.normalized[0]:
                    external_subject_span[0]
                ]
                scope_action_semantics = (
                    _classify_external_relation_semantics(
                        object_prefix,
                        relation_context="action-object",
                    )
                )
                if scope_action_semantics.category in {
                    "direct-immediate",
                    "direct-effect",
                }:
                    scope_action_relation = "direct"
                elif scope_action_semantics.category == "wrapper":
                    scope_action_relation = "wrapper-reference"
                else:
                    scope_action_relation = "unbound"
            elif containing_objects:
                scope_action_relation = "unbound"
                scope_action_semantics = (
                    _ExternalRelationSemanticClassification(
                        category="unknown",
                        member=None,
                        evidence=(),
                        span=None,
                    )
                )

        selections = _external_concern_selections(scope)
        selection_edges = {
            concern: _external_evidence_action_edge(
                local_parse,
                subject_span,
                head_span,
            )
            for (
                concern,
                _subject_alias,
                _semantic_head,
                subject_span,
                head_span,
            ) in selections
        }
        shared_terminal_effect_span: tuple[int, int] | None = None
        consumer_selections = [
            selection
            for selection in selections
            if selection[0] == "consumer"
        ]
        failure_selections = [
            selection
            for selection in selections
            if selection[0] == "failure"
        ]
        if (
            len(consumer_selections) == 1
            and len(failure_selections) == 1
        ):
            consumer_edge = selection_edges.get("consumer")
            failure_edge = selection_edges.get("failure")
            if (
                consumer_edge is not None
                and failure_edge is not None
                and consumer_edge[0].action_id
                == failure_edge[0].action_id
                and consumer_edge[1].object_id
                == failure_edge[1].object_id
            ):
                shared_action, shared_object = consumer_edge
                later_head_end = max(
                    consumer_selections[0][4][1],
                    failure_selections[0][4][1],
                )
                object_start, object_end = (
                    shared_object.span.normalized
                )
                parser_effect_spans = [
                    lexeme.raw_match_span.normalized
                    for lexeme in local_parse.task_actions.lexemes
                    if (
                        lexeme.lexeme
                        in _EXTERNAL_RELATION_SEMANTICS[
                            "effect_action_surfaces"
                        ]
                        and lexeme.disposition
                        == "non-action-object-lexeme"
                        and lexeme.action_id
                        == shared_action.action_id
                        and later_head_end
                        <= lexeme.raw_match_span.normalized[0]
                        and object_start
                        <= lexeme.raw_match_span.normalized[0]
                        and lexeme.raw_match_span.normalized[1]
                        <= object_end
                    )
                ]
                registered_effect_spans = [
                    token_match.span()
                    for token_match in (
                        _EXTERNAL_LEXICAL_TOKEN_RE.finditer(
                            scope,
                            max(later_head_end, object_start),
                            object_end,
                        )
                    )
                    if (
                        token_match.group(0)
                        in _EXTERNAL_RELATION_SEMANTICS[
                            "effect_action_surfaces"
                        ]
                    )
                ]
                eligible_terminal_effects = sorted(
                    set(
                        (
                            *parser_effect_spans,
                            *registered_effect_spans,
                        )
                    )
                )
                if len(eligible_terminal_effects) == 1:
                    candidate_span = eligible_terminal_effects[0]
                    if not scope[candidate_span[1]:object_end].strip():
                        shared_terminal_effect_span = candidate_span

        for (
            concern,
            subject_alias,
            semantic_head,
            subject_span,
            head_span,
        ) in selections:
            action = scope_action
            action_relation = scope_action_relation
            action_semantics = scope_action_semantics
            concern_edge = selection_edges.get(concern)
            if (
                scope_external_subject is None
                and concern_edge is not None
            ):
                action, owning_object = concern_edge
                cluster_start = _external_concern_cluster_start(
                    scope,
                    concern,
                    subject_span,
                    head_span,
                    lower_bound=owning_object.span.normalized[0],
                )
                object_prefix = scope[
                    owning_object.span.normalized[0]:cluster_start
                ]
                action_semantics = (
                    _classify_external_relation_semantics(
                        object_prefix,
                        relation_context="action-object",
                    )
                )
                if action_semantics.category in {
                    "direct-immediate",
                    "direct-effect",
                }:
                    action_relation = "direct"
                elif action_semantics.category == "wrapper":
                    action_relation = "wrapper-reference"
                else:
                    action_relation = "unbound"
                if action_relation == "unbound":
                    continue

            concern_prefix_match = (
                _EXTERNAL_SCOPE_NEGATIVE_PREFIX_RE.match(scope)
            )
            concern_prefix_span: tuple[int, int] | None = None
            if concern_prefix_match is not None:
                cluster_start = _external_concern_cluster_start(
                    scope,
                    concern,
                    subject_span,
                    head_span,
                    lower_bound=concern_prefix_match.end(),
                )
                if cluster_start == concern_prefix_match.end():
                    concern_prefix_span = (
                        concern_prefix_match.span()
                    )
            predicate_match = re.match(
                r"\s*(?P<token>[a-z0-9]+)\b",
                scope[head_span[1]:],
            )
            current_predicate_span: tuple[int, int] | None = None
            if (
                predicate_match is not None
                and predicate_match.group("token")
                in _EXTERNAL_RELATION_SEMANTICS[
                    "effect_action_surfaces"
                ]
            ):
                current_predicate_span = (
                    head_span[1]
                    + predicate_match.start("token"),
                    head_span[1]
                    + predicate_match.end("token"),
                )

            barrier_candidates: list[
                tuple[int, int, int]
            ] = [(len(scope), len(scope), 3)]
            for parsed_action in local_parse.task_actions.actions:
                if (
                    current_predicate_span is not None
                    and parsed_action.verb_span.normalized
                    == current_predicate_span
                ):
                    continue
                action_spans = [
                    item.normalized
                    for item in (
                        parsed_action.coordinator_span,
                        parsed_action.prefix_span,
                        parsed_action.subject_span,
                        parsed_action.verb_span,
                    )
                    if (
                        item is not None
                        and item.normalized[0] > head_span[1]
                    )
                ]
                if action_spans:
                    action_boundary = min(
                        action_spans,
                        key=lambda item: (item[0], item[1]),
                    )
                    barrier_candidates.append(
                        (
                            action_boundary[0],
                            action_boundary[1],
                            0,
                        )
                    )
            barrier_candidates.extend(
                (
                    match.start(),
                    match.end(),
                    1,
                )
                for match in local_external_subjects
                if match.start() > head_span[1]
            )
            barrier_candidates.extend(
                (
                    other_subject_span[0],
                    other_subject_span[1],
                    2,
                )
                for (
                    other_concern,
                    _other_alias,
                    _other_head,
                    other_subject_span,
                    _other_head_span,
                ) in selections
                if (
                    other_concern != concern
                    and other_subject_span[0] > head_span[1]
                )
            )
            barrier_start, barrier_end, _barrier_kind = min(
                barrier_candidates,
                key=lambda item: (item[0], item[2], item[1]),
            )
            effect_window_span = (head_span[1], barrier_start)
            owner_candidates = _external_owner_relation_phrases(
                scope,
                explicit_subject_end=explicit_subject_end,
                concern_subject_start=subject_span[0],
                concern_head_end=head_span[1],
                effect_window_end=barrier_start,
            )
            owner_classifications = [
                _classify_external_relation_semantics(
                    phrase,
                    relation_context="continuation-owner",
                    concern=concern,
                    span=candidate_span,
                )
                for phrase, candidate_span in owner_candidates
            ]
            if len(local_external_subjects) > 1:
                owner_classifications.append(
                    _ExternalRelationSemanticClassification(
                        category="unknown",
                        member=None,
                        evidence=(),
                        span=None,
                    )
                )
            material_owner_classifications = [
                item
                for item in owner_classifications
                if item.category != "none"
            ]
            if not material_owner_classifications:
                owner_semantics = (
                    _ExternalRelationSemanticClassification(
                        category="none",
                        member=None,
                        evidence=(),
                        span=None,
                    )
                )
            elif len(material_owner_classifications) == 1:
                owner_semantics = (
                    material_owner_classifications[0]
                )
            else:
                owner_semantics = (
                    _ExternalRelationSemanticClassification(
                        category="unknown",
                        member=None,
                        evidence=tuple(
                            token
                            for item
                            in material_owner_classifications
                            for token in item.evidence
                        ),
                        span=None,
                    )
                )
            if owner_semantics.category == "different-owner":
                continuation_owner = "explicit-different"
            elif owner_semantics.category == "same-context":
                continuation_owner = "same-external-context"
            elif owner_semantics.category in {
                "ambiguous-owner",
                "unknown",
            }:
                continuation_owner = "ambiguous"
            else:
                continuation_owner = (
                    "explicit-external"
                    if scope_external_subject is not None
                    else "inherited-external"
                )
            semantic_category = (
                owner_semantics.category
                if owner_semantics.category != "none"
                else action_semantics.category
            )
            semantic_evidence = tuple(
                dict.fromkeys(
                    (
                        *action_semantics.evidence,
                        *owner_semantics.evidence,
                    )
                )
            )
            binding_shared_terminal_effect_span = (
                shared_terminal_effect_span
                if (
                    concern in {"consumer", "failure"}
                    and action_relation == "direct"
                    and owner_semantics.category
                    != "metadata-qualifier"
                    and continuation_owner
                    not in {"ambiguous", "explicit-different"}
                )
                else None
            )
            bindings.append(
                _ExternalEffectScopeBinding(
                    session_id=session_id,
                    clause_id=clause_id,
                    scope=scope,
                    external_subject_span=external_subject_span,
                    concern=concern,
                    subject_alias=subject_alias,
                    semantic_head=semantic_head,
                    subject_span=subject_span,
                    head_span=head_span,
                    concern_prefix_span=concern_prefix_span,
                    shared_terminal_effect_span=(
                        binding_shared_terminal_effect_span
                    ),
                    action_id=(
                        action.action_id
                        if action is not None
                        else None
                    ),
                    action_verb=(
                        action.verb if action is not None else None
                    ),
                    action_span=(
                        action.verb_span.normalized
                        if action is not None
                        else None
                    ),
                    action_polarity=(
                        action.polarity if action is not None else None
                    ),
                    action_prefix_span=(
                        action.prefix_span
                        if action is not None
                        else None
                    ),
                    action_relation=action_relation,
                    continuation_owner=continuation_owner,
                    semantic_category=semantic_category,
                    semantic_evidence=semantic_evidence,
                    owner_candidate_spans=tuple(
                        candidate_span
                        for _phrase, candidate_span
                        in owner_candidates
                    ),
                    effect_window_span=effect_window_span,
                    barrier_span=(barrier_start, barrier_end),
                    predicate_scope=scope[
                        slice(*effect_window_span)
                    ],
                )
            )
    return tuple(bindings)


def _resolve_external_binding_effect(
    binding: _ExternalEffectScopeBinding,
) -> str:
    """Resolve one concern from binding evidence in strict fail-closed order."""

    if binding.action_relation == "unbound":
        return EFFECT_AMBIGUOUS
    if binding.continuation_owner == "ambiguous":
        return EFFECT_AMBIGUOUS
    if binding.continuation_owner == "explicit-different":
        return EFFECT_ADJACENT_ONLY

    observations: set[str] = set()
    effect_actions = _EXTERNAL_RELATION_SEMANTICS[
        "effect_action_surfaces"
    ]
    if (
        binding.action_relation == "direct"
        and binding.action_verb in effect_actions
        and binding.action_polarity is not None
    ):
        observations.add(binding.action_polarity)
    if binding.shared_terminal_effect_span is not None:
        shared_effect_tokens = _normalize_effect_scope(
            binding.scope[
                slice(*binding.shared_terminal_effect_span)
            ]
        ).split()
        observations.add(
            EFFECT_CHANGED
            if (
                len(shared_effect_tokens) == 1
                and shared_effect_tokens[0] in effect_actions
            )
            else EFFECT_AMBIGUOUS
        )

    predicate_scope = binding.predicate_scope
    if _scope_is_ambiguous(predicate_scope):
        observations.add(EFFECT_AMBIGUOUS)
    elif (
        binding.concern_prefix_span is not None
        or _scope_is_unchanged(predicate_scope)
        or (
            re.search(r"\b(?:no|without)\b", predicate_scope)
            is not None
            and re.search(
                r"\b(?:change|decision|effect|semantics?|behavior)\b",
                predicate_scope,
            )
            is not None
        )
    ):
        observations.add(EFFECT_UNCHANGED)
    else:
        predicate_tokens = _normalize_effect_scope(
            predicate_scope
        ).split()
        if any(token in effect_actions for token in predicate_tokens):
            observations.add(EFFECT_CHANGED)

    if (
        EFFECT_AMBIGUOUS in observations
        or {
            EFFECT_CHANGED,
            EFFECT_UNCHANGED,
        }.issubset(observations)
    ):
        return EFFECT_AMBIGUOUS
    if EFFECT_CHANGED in observations:
        return EFFECT_CHANGED
    if EFFECT_UNCHANGED in observations:
        return EFFECT_UNCHANGED
    return EFFECT_ADJACENT_ONLY


def _build_external_concern_effect_records(
    value: str,
    *,
    parsed: _ParsedTaskRequest | None = None,
) -> tuple[_ExternalConcernEffectRecord, ...]:
    """Build finite clause-local records for explicit external sessions."""

    records: list[_ExternalConcernEffectRecord] = []
    terminated_at: dict[int, int] = {}
    for binding in _build_external_effect_scope_bindings(
        value,
        parsed=parsed,
    ):
        terminated_clause = terminated_at.get(binding.session_id)
        if (
            terminated_clause is not None
            and binding.clause_id > terminated_clause
        ):
            continue
        if binding.continuation_owner == "explicit-different":
            terminated_at.setdefault(
                binding.session_id,
                binding.clause_id,
            )
            continue
        records.append(
            _ExternalConcernEffectRecord(
                session_id=binding.session_id,
                clause_id=binding.clause_id,
                concern=binding.concern,
                subject_alias=binding.subject_alias,
                semantic_head=binding.semantic_head,
                effect=_resolve_external_binding_effect(binding),
                scope=binding.scope,
            )
        )
    return tuple(records)


def _aggregate_external_concern_effect_records(
    records: tuple[_ExternalConcernEffectRecord, ...],
    *,
    latest_session_id: int | None = None,
) -> tuple[str, str, str]:
    """Aggregate the latest normalized external session by concern."""

    if latest_session_id is None and records:
        latest_session_id = max(record.session_id for record in records)
    effects: list[str] = []
    for concern in _EXTERNAL_CONCERN_ORDER:
        observed = {
            record.effect
            for record in records
            if (
                record.session_id == latest_session_id
                and record.concern == concern
            )
        }
        if (
            EFFECT_AMBIGUOUS in observed
            or {
                EFFECT_CHANGED,
                EFFECT_UNCHANGED,
            }.issubset(observed)
        ):
            effects.append(EFFECT_AMBIGUOUS)
        elif EFFECT_CHANGED in observed:
            effects.append(EFFECT_CHANGED)
        elif EFFECT_UNCHANGED in observed:
            effects.append(EFFECT_UNCHANGED)
        else:
            effects.append(EFFECT_ADJACENT_ONLY)
    return effects[0], effects[1], effects[2]


def _external_integration_effects(
    value: str,
    *,
    parsed: _ParsedTaskRequest | None = None,
) -> tuple[str, str, str]:
    """Return one structured effect tuple for the latest external session."""

    session_scopes = _external_session_scopes(value, parsed=parsed)
    latest_session_id = (
        max(
            session_id
            for (
                session_id,
                _clause_id,
                _scope,
            ) in session_scopes
        )
        if session_scopes
        else None
    )
    return _aggregate_external_concern_effect_records(
        _build_external_concern_effect_records(value, parsed=parsed),
        latest_session_id=latest_session_id,
    )


def _external_integration_analysis_foundations(
    value: str,
    consumer_effect: str,
    failure_effect: str,
) -> tuple[str, ...]:
    """Return the exact changed member subset for one external boundary."""

    text = value.casefold()
    if "external integration" not in text:
        return ()
    if re.search(
        r"\b(?:external integration|provider|contract)\b"
        r"[^.;!?]{0,80}\b(?:owner|ownership|subject)\b"
        r"[^.;!?]{0,40}\b(?:ambiguous|unknown|unresolved|undecided)\b",
        text,
    ) is not None:
        return ()
    if EFFECT_AMBIGUOUS in (consumer_effect, failure_effect):
        return ()

    selected: list[str] = []
    if consumer_effect == EFFECT_CHANGED:
        selected.append("consumer-impact-analysis")
    if failure_effect == EFFECT_CHANGED:
        selected.append("failure-contract-design")
    return tuple(selected)


def _route_impl(
    prompt: str,
    *,
    main_execution: object,
    domain_registry: object = None,
    professional_registry: object = None,
) -> dict[str, Any]:
    """Run one complete deterministic route and validate its Core projection."""

    validated_main = _validated_main_execution_copy(main_execution)
    artifact_binding_id = _validated_brief_review_binding(validated_main)
    winner_trace: list[dict[str, Any]] = []
    canonical_domain_data = load_yaml_file(DOMAIN_REGISTRY)
    canonical_foundation_data = load_yaml_file(FOUNDATION_REGISTRY)
    canonical_professional_data = load_yaml_file(PROFESSIONAL_REGISTRY)
    registry_data = (
        canonical_domain_data
        if domain_registry is None
        else domain_registry
    )
    professional_data = (
        canonical_professional_data
        if professional_registry is None
        else professional_registry
    )
    try:
        foundation_matcher_projections = (
            foundation_runtime_matcher_authority(
                canonical_foundation_data,
                context="Canonical Foundation runtime matcher authority",
            )
        )
        admission_authority = oracle_admission_authority(
            foundation_registry=canonical_foundation_data,
            professional_registry=canonical_professional_data,
        )
        injected_professional_authority = (
            _professional_automatic_decision_authority(
                professional_data,
                context="Injected Professional routing authority",
            )
        )
        canonical_professional_authority = (
            _professional_automatic_decision_authority(
                canonical_professional_data,
                context="Canonical Professional routing authority",
            )
        )
        injected_domain_authority = _domain_modifier_decision_authority(
            registry_data,
            professional_data,
            domain_context="Injected Domain modifier routing authority",
            professional_context=(
                "Injected Professional modifier routing authority"
            ),
        )
        canonical_domain_authority = _domain_modifier_decision_authority(
            canonical_domain_data,
            canonical_professional_data,
            domain_context="Canonical Domain modifier routing authority",
            professional_context=(
                "Canonical Professional modifier routing authority"
            ),
        )
    except ValidationProblem as exc:
        raise RoutingIntegrityError(str(exc)) from exc
    if (
        injected_professional_authority
        != canonical_professional_authority
    ):
        raise RoutingIntegrityError(
            "Professional automatic-owner authority differs from current "
            "canonical registry projection"
        )
    if injected_domain_authority != canonical_domain_authority:
        raise RoutingIntegrityError(
            "Domain modifier authority differs from current canonical "
            "registry projection"
        )
    domain_specs = domain_route_specs(canonical_domain_data)
    professional_authority = professional_automatic_routing_authority(
        canonical_professional_data,
        context="Canonical Professional routing authority",
    )
    domain_authority = domain_modifier_routing_authority(
        canonical_domain_data,
        canonical_professional_data,
        domain_context="Canonical Domain modifier routing authority",
        professional_context="Canonical Professional modifier routing authority",
    )
    owners_by_family = professional_authority["owners_by_family"]
    implementation_policy = professional_authority["policy"][
        "implementation_owner"
    ]
    if not isinstance(canonical_professional_data, dict):
        raise RoutingIntegrityError(
            "Canonical Professional routing authority source must be a mapping"
        )
    professional_entries = canonical_professional_data.get(
        "professional_skills"
    )
    if not isinstance(professional_entries, list):
        raise RoutingIntegrityError(
            "Canonical Professional routing authority lacks professional_skills"
        )
    known_foundation_layer3 = {
        name
        for entry in professional_entries
        if isinstance(entry, dict)
        for name in entry.get("layer3_candidates", [])
        if isinstance(name, str) and name
    }
    text = _normalize_route_prompt(prompt)
    parsed = _parse_normalized_task_request(text)
    routing_boundary_facts = _routing_boundary_fact_snapshots(
        text,
        parsed=parsed,
    )
    filesystem_effect_state = _filesystem_process_effect_state(
        _filesystem_process_effect_records(text)
    )
    repository_filesystem_states = {
        facts.filesystem_behavior
        for facts in routing_boundary_facts
        if facts.repository_owner
    }
    if "ambiguous" in repository_filesystem_states:
        filesystem_effect_state = EFFECT_AMBIGUOUS
    elif "changed" in repository_filesystem_states:
        filesystem_effect_state = EFFECT_CHANGED
    elif (
        filesystem_effect_state == EFFECT_ADJACENT_ONLY
        and "unchanged" in repository_filesystem_states
    ):
        filesystem_effect_state = EFFECT_UNCHANGED
    node_effect_state = (
        _overall_effect_state(_node_runtime_effect_records(text))
        if "node.js" in text
        else EFFECT_ADJACENT_ONLY
    )
    distributed_effect_state = _overall_effect_state(
        _distributed_workflow_effect_records(text)
    )
    structure_states = _structure_decision_states(text)
    action_intent = _task_action_intent(text)
    audit_integrity_subject = any(
        subject in text
        for subject in (
            "audit evidence integrity",
            "tamper-evident audit",
        )
    )
    audit_review_task = (
        audit_integrity_subject
        and (
            text.startswith("review ")
            or "review the actual diff" in text
        )
    )
    audit_analysis_conflict = (
        action_intent["implementation"]
        and not action_intent["implementation_ambiguous"]
        and action_intent["audit_analysis"]
        and not action_intent["audit_analysis_ambiguous"]
        and not action_intent["audit_implementation"]
        and not action_intent["audit_implementation_ambiguous"]
    )
    analysis_only_action = (
        not action_intent["implementation"]
        and not action_intent["implementation_ambiguous"]
        and not action_intent["preparation"]
    )
    analysis_decision_statements: list[str] = []
    for statement in _EFFECT_STATEMENT_BOUNDARY_RE.split(text):
        statement = statement.strip()
        statement_intent = _task_action_intent(statement)
        if (
            statement
            and statement_intent["analysis"]
            and not statement_intent["implementation"]
            and not statement_intent["implementation_ambiguous"]
            and not statement_intent["preparation"]
        ):
            analysis_decision_statements.append(statement)
    owner_internal_structure_evidence = (
        _owner_internal_structure_decision_evidence(text)
    )
    owner_internal_structure_analysis_evidence = (
        [
            "analysis-only-action",
            *owner_internal_structure_evidence,
        ]
        if owner_internal_structure_evidence
        and action_intent["analysis"]
        and not action_intent["implementation"]
        and not action_intent["implementation_ambiguous"]
        else []
    )
    domain_object_analysis_intent = (
        structure_states["domain-object"] == EFFECT_CHANGED
        and action_intent["analysis"]
        and not action_intent["implementation"]
        and not action_intent["implementation_ambiguous"]
    )
    generated_authority_state = _generated_authority_state(text)
    technology_stack_risk = _technology_stack_commitment_risk(text)
    major_module_review = _major_module_boundary_review(text)
    dependency_package_risk = _dependency_package_risk(text)
    target_domains = _installed_target_domains(text)
    shared_framework = _shared_client_framework(text)
    raw_cohort_candidates: list[dict[str, Any]] = []
    critical_evidence = _critical_unknown_evidence(
        text,
        parsed=parsed,
        filesystem_effect_state=filesystem_effect_state,
        node_effect_state=node_effect_state,
        structure_states=structure_states,
        owner_internal_structure_evidence=(
            owner_internal_structure_analysis_evidence
        ),
        generated_authority_state=generated_authority_state,
        target_domains=target_domains,
        shared_framework=shared_framework,
    )
    if critical_evidence:
        raw_cohort_candidates.append(
            {
                "candidate_id": "critical-unknown",
                "evidence": critical_evidence,
            }
        )
    if parsed.task_actions.blocking_terminal_spans:
        raw_cohort_candidates.append(
            {
                "candidate_id": "ordinary-ambiguity",
                "evidence": ["proof-limit:terminal-task-action-ambiguity"],
            }
        )
    preparation_evidence = _generic_preparation_evidence(text)
    if preparation_evidence:
        raw_cohort_candidates.append(
            {
                "candidate_id": "implementation-preparation",
                "evidence": preparation_evidence,
            }
        )
    material_review_risks = _material_review_risk_candidates(
        text,
        boundary_facts=routing_boundary_facts,
    )
    if (
        not any(
            _security_boundary_is_proved(facts)
            for facts in routing_boundary_facts
        )
        and any(
            _security_boundary_has_explicit_unknown(facts)
            for facts in routing_boundary_facts
        )
        and not any(
            candidate.get("candidate_id") == "ordinary-ambiguity"
            for candidate in raw_cohort_candidates
        )
    ):
        raw_cohort_candidates.append(
            {
                "candidate_id": "ordinary-ambiguity",
                "evidence": ["proof-limit:security-boundary-unknown"],
            }
        )
    review_risk_origins: dict[str, _FoundationRouteOrigin] = {}
    for risk in material_review_risks:
        risk_id = risk.get("candidate_id")
        evidence = risk.get("evidence")
        skill = REVIEW_RISK_PRIMARY.get(risk_id)
        if (
            not isinstance(risk_id, str)
            or not isinstance(evidence, list)
            or not all(
                isinstance(item, str) and item
                for item in evidence
            )
            or not isinstance(skill, str)
            or risk_id in review_risk_origins
        ):
            raise RoutingIntegrityError(
                "review-risk classifier origin is malformed"
            )
        review_risk_origins[risk_id] = _FoundationRouteOrigin(
            kind="review-risk",
            candidate_id=risk_id,
            rule_id=f"{risk_id}-candidate",
            routing_family=None,
            primary_skill=skill,
            review_skill=skill,
            evidence_ids=tuple(evidence),
        )
    review_stage_evidence = _review_stage_evidence(
        text,
        has_material_risk=bool(material_review_risks),
    )
    if preparation_evidence or review_stage_evidence:
        raw_cohort_candidates.extend(material_review_risks)
    elif len(material_review_risks) >= 2:
        raw_cohort_candidates.extend(material_review_risks)
    direct_owner_review = (
        REVIEW_RISK_PRIMARY[material_review_risks[0]["candidate_id"]]
        if (
            not preparation_evidence
            and not review_stage_evidence
            and len(material_review_risks) == 1
        )
        else implementation_policy["accepted"]["review"]["default"]
    )
    review_structure_ambiguous = EFFECT_AMBIGUOUS in (
        structure_states["refactoring"],
        structure_states["owner-placement"],
        structure_states["minimality"],
        structure_states["readability"],
    )
    if (
        review_stage_evidence
        and not audit_review_task
        and (
            material_review_risks or not review_structure_ambiguous
        )
    ):
        raw_cohort_candidates.append(
            {
                "candidate_id": "review-generic",
                "evidence": review_stage_evidence,
            }
        )
    classified_families = _coalesce_professional_family_matches(
        classify_professional_families(parsed)
    )
    repository_implementation_facts = tuple(
        facts
        for facts in routing_boundary_facts
        if facts.repository_owner
    )
    repository_action_family_names: set[str] = set()
    repository_action_ids = {
        facts.action_id for facts in repository_implementation_facts
    }
    changed_implementation_action_ids = {
        action.action_id
        for action in parsed.task_actions.actions
        if action.role in {"direct", "coordinated"}
        and action.polarity == EFFECT_CHANGED
    }
    all_changed_actions_repository_owned = bool(
        changed_implementation_action_ids
        and changed_implementation_action_ids.issubset(
            repository_action_ids
        )
    )
    for action in parsed.task_actions.actions:
        if (
            action.action_id not in repository_action_ids
            or action.object_span is None
        ):
            continue
        action_scope = text[
            action.verb_span.normalized[0] : action.object_span.normalized[1]
        ]
        repository_action_family_names.update(
            match["routing_family"]
            for match in _coalesce_professional_family_matches(
                classify_professional_families(
                    _parse_normalized_task_request(action_scope)
                )
            )
        )
    if (
        action_intent["implementation"]
        and repository_implementation_facts
        and not classified_families
    ):
        classified_families = [
            {
                "routing_family": "repository-tooling",
                "match_evidence": [
                    "effect-changed",
                    "explicit-implementation-action",
                    "repository-developer-tool",
                ],
            }
        ]
    elif (
        action_intent["implementation"]
        and repository_implementation_facts
        and all_changed_actions_repository_owned
        and repository_action_family_names == {"repository-tooling"}
    ):
        classified_families = [
            match
            for match in classified_families
            if match["routing_family"] == "repository-tooling"
        ]
    if (
        "node.js backend" in text
        and action_intent["implementation"]
        and not any(
            item["routing_family"] == "backend"
            for item in classified_families
        )
        and node_effect_state in {EFFECT_ADJACENT_ONLY, EFFECT_UNCHANGED}
    ):
        classified_families.append(
            {
                "routing_family": "backend",
                "match_evidence": [
                    "backend-surface",
                    "explicit-implementation-action",
                    "node-runtime-effect-nonmaterial",
                ],
            }
        )
    if (
        not classified_families
        and filesystem_effect_state == EFFECT_CHANGED
        and action_intent["implementation"]
    ):
        classified_families.append(
            {
                "routing_family": "backend",
                "match_evidence": [
                    "backend-surface",
                    "explicit-implementation-action",
                    "filesystem-or-child-process-effect-changed",
                ],
            }
        )
    if (
        "multiple dependent tasks" in text
        and len(classified_families) < 2
    ):
        classified_families = []
    implementation_owner_origins: dict[str, _FoundationRouteOrigin] = {}
    for classified in classified_families:
        family = classified["routing_family"]
        if (
            family == "backend"
            and (
                filesystem_effect_state == EFFECT_AMBIGUOUS
                or node_effect_state == EFFECT_AMBIGUOUS
                or any(
                    structure_states[name] == EFFECT_AMBIGUOUS
                    for name in (
                        "domain-object",
                        "minimality",
                        "owner-placement",
                        "pattern",
                    )
                )
            )
        ):
            continue
        if (
            family == "repository-tooling"
            and (
                filesystem_effect_state == EFFECT_AMBIGUOUS
                or any(
                    structure_states[name] == EFFECT_AMBIGUOUS
                    for name in (
                        "minimality",
                        "owner-placement",
                        "pattern",
                    )
                )
            )
        ):
            continue
        if (
            family == "installed-client"
            and (
                filesystem_effect_state == EFFECT_AMBIGUOUS
                or (shared_framework and not target_domains)
                or domain_object_analysis_intent
            )
        ):
            continue
        owner = owners_by_family.get(family)
        if not isinstance(owner, dict):
            raise RoutingIntegrityError(
                f"no registry implementation owner for family {family!r}"
            )
        primary = owner.get("name")
        allowed_layer3 = owner.get("layer3_candidates")
        if not isinstance(primary, str) or not isinstance(
            allowed_layer3,
            list,
        ):
            raise RoutingIntegrityError(
                f"registry implementation owner for {family!r} is malformed"
            )
        layer3 = _implementation_owner_layer3(
            family,
            text,
            audit_implementation=action_intent["audit_implementation"],
            filesystem_effect_state=filesystem_effect_state,
            node_effect_state=node_effect_state,
            structure_states=structure_states,
        )
        layer3, foundation_layer3_overflow = (
            _validated_implementation_owner_layer3(
                layer3,
                allowed=allowed_layer3,
                known=known_foundation_layer3,
                maximum=implementation_policy["accepted"]["layer3"]["max"],
                family=family,
            )
        )
        implementation_rule_id = (
            "audit-integrity-change"
            if (
                family == "logging"
                and action_intent["audit_implementation"]
                and layer3 == ["audit-evidence-integrity"]
            )
            else "implementation-dependency-risk"
            if dependency_package_risk
            else None
        )
        owner_review = (
            "security-privacy-gate"
            if dependency_package_risk
            else "logging-design-gate"
            if family == "logging"
            else direct_owner_review
        )
        raw_cohort_candidates.append(
            {
                "candidate_id": f"implementation-owner:{primary}",
                "rule_id": implementation_rule_id,
                "evidence": classified["match_evidence"],
                "routing_family": family,
                "primary_skill": primary,
                "layer3_skills": layer3,
                "review_skill": owner_review,
                "eligible_layer3_skills": sorted(layer3),
                "foundation_layer3_overflow": foundation_layer3_overflow,
            }
        )
        candidate_id = f"implementation-owner:{primary}"
        if candidate_id in implementation_owner_origins:
            raise RoutingIntegrityError(
                "implementation-owner classifier origin is duplicated"
            )
        implementation_owner_origins[candidate_id] = (
            _FoundationRouteOrigin(
                kind="implementation-owner",
                candidate_id=candidate_id,
                rule_id=implementation_rule_id,
                routing_family=family,
                primary_skill=primary,
                review_skill=owner_review,
                evidence_ids=tuple(classified["match_evidence"]),
            )
        )

    route_candidates: list[dict[str, Any]] = []
    foundation_selector_by_id = {
        record.selector_id: record
        for record in admission_authority.foundation_selectors
    }

    def add_candidate(
        path: str,
        profile: str,
        primary: str,
        layer3: list[str],
        review: str,
        *,
        rule_id: str,
        stage: str,
        precedence_class: str,
        match_evidence: list[str],
        semantic_atoms: list[str] | None = None,
    ) -> None:
        evidence = list(match_evidence)
        authority_record = foundation_selector_by_id.get(rule_id)
        if authority_record is not None:
            if tuple(layer3) != authority_record.foundations:
                raise RoutingIntegrityError(
                    f"selector {rule_id!r} changed its Foundation projection"
                )
            terminal = f"foundation-selector:{rule_id}"
            if terminal not in evidence:
                evidence.append(terminal)
            if tuple(evidence) != authority_record.evidence_ids:
                raise RoutingIntegrityError(
                    f"selector {rule_id!r} changed its evidence projection"
                )
        artifact_review = rule_id == "engineering-artifact-review"
        fallback = rule_id == "repository-first-default"
        candidate = {
            "candidate_id": rule_id,
            "candidate_type": (
                "fallback-route"
                if fallback
                else "artifact-review-route"
                if artifact_review
                else "explicit-route"
            ),
            "evidence": evidence,
            "precedence": (
                FALLBACK_ROUTE_PRECEDENCE
                if fallback
                else 3
                if artifact_review
                else EXPLICIT_ROUTE_PRECEDENCE
            ),
            "path": path,
            "profile": profile,
            "primary_skill": primary,
            "layer3_skills": list(layer3),
            "review_skill": review,
            "rule_id": rule_id,
            "stage": stage,
            "precedence_class": precedence_class,
        }
        if semantic_atoms is not None:
            candidate["semantic_atoms"] = copy.deepcopy(semantic_atoms)
        if layer3:
            _bind_foundation_candidate(
                candidate,
                list(layer3),
                admission_authority=admission_authority,
            )
        route_candidates.append(candidate)

    def add_foundation_selector(
        spec: _FoundationSelectorSpec,
        path: str,
        profile: str,
        stage: str,
        precedence_class: str,
        semantic_atoms: list[str] | None = None,
    ) -> None:
        binding = spec.owner_bindings[0]
        add_candidate(
            path,
            profile,
            binding.primary_skill,
            list(spec.foundations),
            binding.review_skill,
            rule_id=spec.selector_id,
            stage=stage,
            precedence_class=precedence_class,
            match_evidence=list(spec.evidence_ids),
            semantic_atoms=[] if semantic_atoms is None else semantic_atoms,
        )

    selector_review_repeat_failure = _FoundationSelectorSpec(
        "review-repeat-failure",
        ("repeat-failure-analysis",),
        (
            "actual-diff",
            "repeated-failure",
            "foundation-selector:review-repeat-failure",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "ai-code-review-refactor",
                "ai-code-review-refactor",
            ),
        ),
    )
    selector_review_ambiguous_structure = _FoundationSelectorSpec(
        "review-ambiguous-structure-repository-first",
        ("repository-context-map",),
        (
            "actual-diff",
            "ambiguous-structure",
            "foundation-selector:review-ambiguous-structure-repository-first",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "engineering-change-analysis",
                "architecture-impact-reviewer",
            ),
        ),
    )
    selector_review_minimality = _FoundationSelectorSpec(
        "review-minimality-change",
        ("minimal-correct-implementation",),
        (
            "actual-diff",
            "minimality-change",
            "foundation-selector:review-minimality-change",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "ai-code-review-refactor",
                "ai-code-review-refactor",
            ),
        ),
    )
    selector_review_readability = _FoundationSelectorSpec(
        "review-readability-change",
        ("code-clarity-maintainability",),
        (
            "actual-diff",
            "readability-change",
            "foundation-selector:review-readability-change",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "ai-code-review-refactor",
                "ai-code-review-refactor",
            ),
        ),
    )
    selector_security_anti_reliability = _FoundationSelectorSpec(
        "security-anti-reliability-only",
        ("degradation-circuit-breaking", "observability"),
        (
            "reliability-only",
            "no-abuse-or-privacy-risk",
            "foundation-selector:security-anti-reliability-only",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "reliability-observability-gate",
                "reliability-observability-gate",
            ),
            _FoundationSelectorOwnerBindingSpec(
                "engineering-change-analysis",
                "reliability-observability-gate",
            ),
        ),
    )
    selector_security_anti_input = _FoundationSelectorSpec(
        "security-anti-input-shape",
        ("api-contract-design",),
        (
            "input-shape-change",
            "no-security-sink",
            "foundation-selector:security-anti-input-shape",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "data-api-contract-changer",
                "architecture-impact-reviewer",
            ),
        ),
    )
    selector_security_anti_scanner = _FoundationSelectorSpec(
        "security-anti-scanner-report",
        ("documentation-generation",),
        (
            "scanner-report-organization",
            "no-security-verdict",
            "foundation-selector:security-anti-scanner-report",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "change-documentation-gate",
                "change-documentation-gate",
            ),
        ),
    )
    selector_security_credential_session = _FoundationSelectorSpec(
        "security-credential-session-lifecycle",
        ("authentication-security",),
        (
            "credential-or-session-lifecycle-change",
            "foundation-selector:security-credential-session-lifecycle",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "security-privacy-gate",
                "security-privacy-gate",
            ),
        ),
    )
    selector_refactor_fixed = _FoundationSelectorSpec(
        "refactor-fixed-destination",
        ("refactoring",),
        (
            "refactoring-change",
            "fixed-destination",
            "foundation-selector:refactor-fixed-destination",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "engineering-change-analysis",
                "architecture-impact-reviewer",
            ),
        ),
    )
    selector_module_boundary = _FoundationSelectorSpec(
        "module-boundary-analysis",
        ("module-boundary-design",),
        (
            "module-boundary-change",
            "foundation-selector:module-boundary-analysis",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "architecture-impact-reviewer",
                "architecture-impact-reviewer",
            ),
        ),
    )
    selector_technology_stack = _FoundationSelectorSpec(
        "technology-stack-commitment",
        ("technology-stack-selection",),
        (
            "technology-stack-commitment",
            "foundation-selector:technology-stack-commitment",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "architecture-impact-reviewer",
                "architecture-impact-reviewer",
            ),
        ),
    )
    selector_domain_object = _FoundationSelectorSpec(
        "domain-object-analysis",
        ("domain-object-identification",),
        (
            "domain-object-change",
            "analysis-only",
            "foundation-selector:domain-object-analysis",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "domain-impact-modeler",
                "architecture-impact-reviewer",
            ),
        ),
    )
    selector_design_pattern = _FoundationSelectorSpec(
        "design-pattern-analysis",
        ("design-pattern-selection",),
        (
            "design-pattern-change",
            "analysis-only",
            "foundation-selector:design-pattern-analysis",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "architecture-impact-reviewer",
                "architecture-impact-reviewer",
            ),
        ),
    )
    selector_dto_boundary = _FoundationSelectorSpec(
        "dto-model-boundary-analysis",
        ("model-boundary-mapping",),
        (
            "accepted-brief",
            "dto-mapping",
            "foundation-selector:dto-model-boundary-analysis",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "data-api-contract-changer",
                "architecture-impact-reviewer",
            ),
        ),
    )
    selector_sdk_contract = _FoundationSelectorSpec(
        "sdk-contract-analysis",
        ("sdk-library-contract-design",),
        (
            "accepted-brief",
            "sdk-contract",
            "foundation-selector:sdk-contract-analysis",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "data-api-contract-changer",
                "architecture-impact-reviewer",
            ),
        ),
    )
    selector_package_dependency = _FoundationSelectorSpec(
        "package-dependency-analysis",
        ("package-dependency-management",),
        (
            "package-capability-gap",
            "supply-chain-decision",
            "foundation-selector:package-dependency-analysis",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "engineering-change-analysis",
                "architecture-impact-reviewer",
            ),
        ),
    )
    selector_production_release = _FoundationSelectorSpec(
        "production-release-decision",
        ("release-rollback", "version-compatibility"),
        (
            "production-apply-or-rollout",
            "foundation-selector:production-release-decision",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "delivery-release-gate",
                "delivery-release-gate",
            ),
        ),
    )
    selector_incident_response = _FoundationSelectorSpec(
        "incident-response-coordination",
        ("failure-diagnosis",),
        (
            "active-multi-responder-incident",
            "coordination",
            "foundation-selector:incident-response-coordination",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "incident-response-coordinator",
                "reliability-observability-gate",
            ),
        ),
    )
    selector_tenant_isolation = _FoundationSelectorSpec(
        "tenant-isolation-security",
        ("permission-boundary-modeling", "tenant-isolation"),
        (
            "tenant-isolation",
            "propagated-boundary",
            "foundation-selector:tenant-isolation-security",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "security-privacy-gate",
                "security-privacy-gate",
            ),
        ),
    )
    selector_personal_data = _FoundationSelectorSpec(
        "personal-data-lifecycle",
        ("privacy-data-lifecycle",),
        (
            "personal-data-purpose",
            "retention",
            "foundation-selector:personal-data-lifecycle",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "security-privacy-gate",
                "security-privacy-gate",
            ),
        ),
    )
    selector_cryptography = _FoundationSelectorSpec(
        "cryptography-key-lifecycle",
        ("secret-configuration-security", "cryptography-key-lifecycle"),
        (
            "cryptographic-construction-or-key-lifecycle",
            "foundation-selector:cryptography-key-lifecycle",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "security-privacy-gate",
                "security-privacy-gate",
            ),
        ),
    )
    selector_audit_integrity = _FoundationSelectorSpec(
        "audit-integrity-change",
        ("audit-evidence-integrity",),
        (
            "audit-evidence-integrity",
            "foundation-selector:audit-integrity-change",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "security-privacy-gate",
                "security-privacy-gate",
            ),
            _FoundationSelectorOwnerBindingSpec(
                "logging-design-gate",
                "logging-design-gate",
            ),
        ),
    )
    selector_distributed_workflow = _FoundationSelectorSpec(
        "distributed-workflow-analysis",
        ("transaction-consistency",),
        (
            "distributed-effect-change",
            "foundation-selector:distributed-workflow-analysis",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "data-middleware-change-builder",
                "quality-test-gate",
            ),
        ),
    )
    selector_distributed_consistency = _FoundationSelectorSpec(
        "distributed-workflow-consistency-analysis",
        ("distributed-workflow-consistency",),
        (
            "distributed-effect-change",
            "foundation-selector:distributed-workflow-consistency-analysis",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "data-middleware-change-builder",
                "quality-test-gate",
            ),
        ),
    )
    selector_ssrf = _FoundationSelectorSpec(
        "ssrf-url-fetch-analysis",
        ("threat-modeling", "web-security"),
        ("ssrf", "url-fetch", "foundation-selector:ssrf-url-fetch-analysis"),
        (
            _FoundationSelectorOwnerBindingSpec(
                "engineering-change-analysis",
                "security-privacy-gate",
            ),
        ),
    )
    selector_ambiguous_intake = _FoundationSelectorSpec(
        "ambiguous-intake",
        ("requirement-clarification",),
        (
            "ambiguous-request",
            "foundation-selector:ambiguous-intake",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "change-intake-compiler",
                "ai-code-review-refactor",
            ),
        ),
    )
    selector_acceptance = _FoundationSelectorSpec(
        "acceptance-definition",
        ("acceptance-standard-definition",),
        (
            "observable-acceptance",
            "foundation-selector:acceptance-definition",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "acceptance-criteria-builder",
                "ai-code-review-refactor",
            ),
        ),
    )
    selector_architecture_tradeoff = _FoundationSelectorSpec(
        "explicit-architecture-tradeoff",
        ("architecture-tradeoff-analysis",),
        (
            "explicit-architecture-tradeoff",
            "foundation-selector:explicit-architecture-tradeoff",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "architecture-impact-reviewer",
                "architecture-impact-reviewer",
            ),
        ),
    )
    selector_test_data = _FoundationSelectorSpec(
        "explicit-test-data-analysis",
        ("test-data-management",),
        (
            "explicit-test-data-decision",
            "foundation-selector:explicit-test-data-analysis",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "quality-test-gate",
                "quality-test-gate",
            ),
        ),
    )
    selector_authentication_authorization = _FoundationSelectorSpec(
        "explicit-authentication-authorization-analysis",
        ("authentication-authorization",),
        (
            "explicit-authentication-authorization-handoff",
            "foundation-selector:explicit-authentication-authorization-analysis",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "security-privacy-gate",
                "security-privacy-gate",
            ),
        ),
    )
    selector_task_dag = _FoundationSelectorSpec(
        "accepted-brief-task-dag",
        ("task-dag-decomposition",),
        (
            "accepted-engineering-brief",
            "explicit-task-dag",
            "foundation-selector:accepted-brief-task-dag",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "task-dag-planner",
                "engineering-artifact-review",
            ),
        ),
    )
    selector_owner_internal_structure = _FoundationSelectorSpec(
        "owner-internal-structure-analysis",
        ("implementation-structure-design",),
        (
            "analysis-only-action",
            "explicit-known-owner",
            "owner-internal-implementation-structure",
            "reuse-and-deliberate-separation-alternatives",
            "unresolved-structure-decision",
            "foundation-selector:owner-internal-structure-analysis",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "architecture-impact-reviewer",
                "architecture-impact-reviewer",
            ),
        ),
    )
    selector_user_flow = _FoundationSelectorSpec(
        "user-flow-analysis",
        ("interaction-state-modeling", "design-system-rules"),
        ("user-flow", "foundation-selector:user-flow-analysis"),
        (
            _FoundationSelectorOwnerBindingSpec(
                "experience-impact-modeler",
                "ai-code-review-refactor",
            ),
        ),
    )
    selector_database_migration = _FoundationSelectorSpec(
        "database-migration-analysis",
        ("data-migration-design",),
        (
            "database-migration",
            "foundation-selector:database-migration-analysis",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "engineering-change-analysis",
                "delivery-release-gate",
            ),
        ),
    )
    selector_integration_handoff = _FoundationSelectorSpec(
        "integration-handoff-artifact",
        ("contract-testing",),
        (
            "accepted-brief",
            "integration-handoff",
            "foundation-selector:integration-handoff-artifact",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "integration-change-builder",
                "ai-code-review-refactor",
            ),
        ),
    )
    selector_external_integration = _FoundationSelectorSpec(
        "external-integration-analysis",
        ("consumer-impact-analysis", "failure-contract-design"),
        (
            "external-integration",
            "foundation-selector:external-integration-analysis",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "engineering-change-analysis",
                "ai-code-review-refactor",
            ),
        ),
    )
    selector_concurrency_control = _FoundationSelectorSpec(
        "concurrency-control-analysis",
        ("concurrency-control",),
        (
            "cache-stampede-or-lease-stale-ownership",
            "foundation-selector:concurrency-control-analysis",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "engineering-change-analysis",
                "reliability-observability-gate",
            ),
        ),
    )
    selector_backend_idempotency = _FoundationSelectorSpec(
        "backend-idempotency-analysis",
        ("idempotency-retry-design",),
        (
            "backend-retry-idempotency",
            "retry-replay-or-duplicate-side-effect",
            "foundation-selector:backend-idempotency-analysis",
        ),
        (
            _FoundationSelectorOwnerBindingSpec(
                "engineering-change-analysis",
                "ai-code-review-refactor",
            ),
            _FoundationSelectorOwnerBindingSpec(
                "engineering-change-analysis",
                "reliability-observability-gate",
            ),
        ),
    )
    authority_repository_foundations = list(
        selector_review_ambiguous_structure.foundations
    )
    authority_minimality_foundations = list(
        selector_review_minimality.foundations
    )
    authority_reliability_foundations = list(
        selector_security_anti_reliability.foundations
    )
    authority_api_foundations = list(
        selector_security_anti_input.foundations
    )
    authority_documentation_foundations = list(
        selector_security_anti_scanner.foundations
    )
    authority_failure_foundations = list(
        selector_incident_response.foundations
    )
    authority_privacy_foundations = list(
        selector_personal_data.foundations
    )
    authority_secret_foundations = list(
        selector_cryptography.foundations[:1]
    )
    authority_transaction_foundations = list(
        selector_distributed_workflow.foundations[:1]
    )
    authority_generic_security_foundations = [
        selector_tenant_isolation.foundations[0],
        selector_ssrf.foundations[0],
    ]
    authority_release_foundations = list(
        selector_production_release.foundations
    )
    authority_version_foundations = list(
        selector_production_release.foundations[1:]
    )
    authority_public_api_foundations = [
        *selector_security_anti_input.foundations,
        selector_production_release.foundations[1],
    ]
    authority_incident_response_observability_foundations = [
        selector_incident_response.foundations[0],
        selector_security_anti_reliability.foundations[1],
    ]
    authority_database_migration_coexistence_rollback_foundations = [
        selector_database_migration.foundations[0],
        selector_distributed_workflow.foundations[0],
        selector_production_release.foundations[0],
    ]
    authority_cache_stampede_reliability_foundations = [
        selector_concurrency_control.foundations[0],
        *selector_security_anti_reliability.foundations,
    ]
    authority_retry_lease_foundations = [
        selector_concurrency_control.foundations[0],
        selector_backend_idempotency.foundations[0],
    ]
    if tuple(authority_retry_lease_foundations) != (
        _FOUNDATION_ALIAS_MEMBER_SUBSETS[
            "retry-lease-terminal-resolution-analysis"
        ]
    ):
        raise RoutingIntegrityError(
            "retry/lease alias differs from its member authority"
        )
    dependency_vulnerability_authority = foundation_selector_by_id.get(
        "dynamic-foundation:dependency-vulnerability-scanning"
    )
    if dependency_vulnerability_authority is None:
        raise RoutingIntegrityError(
            "package supply-chain alias lacks dependency selector authority"
        )
    authority_package_supply_chain_foundations = [
        selector_package_dependency.foundations[0],
        dependency_vulnerability_authority.foundations[0],
    ]
    if tuple(authority_package_supply_chain_foundations) != (
        _FOUNDATION_ALIAS_MEMBER_SUBSETS["package-supply-chain-analysis"]
    ):
        raise RoutingIntegrityError(
            "package supply-chain alias differs from its member authority"
        )
    test_strategy_authority = foundation_selector_by_id.get(
        "foundation-activation-test-strategy"
    )
    if test_strategy_authority is None:
        raise RoutingIntegrityError(
            "test strategy Professional precedence lacks activation authority"
        )
    authority_test_strategy_foundations = list(
        test_strategy_authority.foundations
    )

    matched_foundation_projections = [
        projection
        for projection in foundation_matcher_projections
        if _foundation_runtime_matcher_matches(
            text,
            projection["runtime_matcher"],
        )
    ]
    matched_foundation_names = {
        projection["name"]
        for projection in matched_foundation_projections
    }
    for projection in matched_foundation_projections:
        add_candidate(
            projection["path"],
            projection["profile"],
            projection["primary_skill"],
            [projection["name"]],
            projection["review_skill"],
            rule_id=projection["activation_id"],
            stage="foundation-activation",
            precedence_class="foundation-activation",
            match_evidence=projection["matcher_evidence"],
            semantic_atoms=projection["semantic_atoms"],
        )

    def project_selection(
        cohort_selection: dict[str, Any],
    ) -> dict[str, Any]:
        raw_candidates = cohort_selection["raw_candidates"]
        selected_candidate = cohort_selection["selected_candidate"]
        excluded_candidates = cohort_selection["excluded_candidates"]
        if selected_candidate is None:
            raise RoutingIntegrityError("route selection produced no candidate")
        selected_id = selected_candidate["candidate_id"]
        path = selected_candidate.get("path")
        profile = selected_candidate.get("profile")
        primary = selected_candidate.get("primary_skill")
        review = selected_candidate.get("review_skill")
        rule_id = selected_candidate.get("rule_id", selected_id)
        stage = selected_candidate.get("stage", "candidate-selection")
        precedence_class = selected_candidate.get(
            "precedence_class",
            "candidate-selection",
        )
        derived = selected_candidate.get("candidate_type") == "derived-conflict"
        layer3 = list(
            selected_candidate.get(
                "layer3_skills"
                if derived
                else "eligible_layer3_skills",
                selected_candidate.get("layer3_skills", []),
            )
        )
        if selected_id in {
            "foundation-layer3-overflow",
            "implementation-owner-conflict",
            "route-contract-conflict",
        }:
            rule_id = f"{selected_id}-candidate"
            stage = (
                "implementation-owner"
                if selected_id != "route-contract-conflict"
                else "candidate-selection"
            )
            precedence_class = (
                "layer-budget"
                if selected_id == "foundation-layer3-overflow"
                else "unresolved-boundary"
            )
        elif selected_id == "review-risk-owner-conflict":
            path = "analyzed"
            profile = "analysis-agent"
            primary = "engineering-change-analysis"
            layer3 = ["repository-context-map"]
            review = "architecture-impact-reviewer"
            rule_id = "review-risk-owner-conflict-candidate"
            stage = "review"
            precedence_class = "unresolved-boundary"
        elif selected_id == "merged-route-candidate":
            rule_id = "merged-route-candidate"
            stage = "candidate-selection"
            precedence_class = "same-contract-merge"
        if not all(
            isinstance(value, str) and value
            for value in (path, profile, primary, review)
        ):
            raise RoutingIntegrityError(
                f"selected route {selected_id!r} has an incomplete contract"
            )
        if len(layer3) != len(set(layer3)):
            raise RoutingIntegrityError(
                f"duplicate total Layer 3 selection is invalid: {layer3!r}"
            )
        if len(layer3) > implementation_policy["accepted"]["layer3"]["max"]:
            raise RoutingIntegrityError(
                f"total Layer 3 budget exceeded: {layer3!r}"
            )
        if winner_trace:
            raise RoutingIntegrityError(
                "route-once pipeline projected more than one winner"
            )
        match_evidence = (
            [selected_candidate["reason"]]
            if selected_candidate.get("reason")
            == "domain-layer3-authorization-conflict"
            else list(selected_candidate["evidence"])
        )
        trace: dict[str, Any] = {
            "rule_id": rule_id,
            "stage": stage,
            "precedence_class": precedence_class,
            "match_evidence": list(match_evidence),
            "raw_candidates": raw_candidates,
            "selected_candidate": selected_candidate,
            "excluded_candidates": excluded_candidates,
        }
        if "semantic_atoms" in selected_candidate:
            trace["semantic_atoms"] = copy.deepcopy(
                selected_candidate["semantic_atoms"]
            )
        if selected_id == "foundation-layer3-overflow":
            trace["deferred_handoff"] = {
                "status": "unresolved",
                "cohorts": [
                    "layer3",
                    "review",
                    "execution-level",
                ],
                "source_rule_id": "foundation-layer3-overflow",
                "retained_layer3": list(layer3),
                "deferred_layer3": list(
                    selected_candidate["eligible_layer3_skills"]
                ),
                "review_skill": review,
                "reason": "foundation-layer3-overflow",
            }
        context = selected_candidate.get("candidate_layer3_context")
        if (
            selected_id == "implementation-preparation"
            and isinstance(context, dict)
        ):
            risk = context["risk"]
            owners = context["owners"]
            if risk is not None:
                desired = list(risk["foundation_requests"])
            elif len(owners) == 1:
                desired = list(owners[0]["foundation_requests"])
            else:
                desired = list(context["support_foundations"])
            if not desired:
                desired = ["repository-context-map"]
            source_rule_ids = context["support_rule_ids"]
            deferred_handoff = {
                "status": "unresolved",
                "cohorts": [
                    "layer3",
                    "review",
                    "execution-level",
                ],
                "source_rule_id": (
                    source_rule_ids[0]
                    if len(source_rule_ids) == 1
                    else "candidate-set"
                ),
                "retained_layer3": list(layer3),
                "deferred_layer3": [
                    name
                    for name in desired
                    if name not in ENGINEERING_CHANGE_ANALYSIS_LAYER3
                ],
                "review_skill": review,
                "reason": (
                    "candidate-layer3-not-authorized-by-"
                    "engineering-change-analysis"
                ),
            }
            if risk is not None:
                deferred_handoff["risk_candidate_id"] = risk["candidate_id"]
            trace["deferred_handoff"] = deferred_handoff
        winner_trace.append(trace)
        return {
            "path": path,
            "profile": profile,
            "primary_skill": primary,
            "layer3_skills": layer3,
            "review_skill": review,
        }

    repeated_failure_subject = any(
        subject in text
        for subject in (
            "same path",
            "same repair path",
            "same cause",
            "same patch shape",
            "same validator",
        )
    )
    failed_twice = "failed twice" in text and repeated_failure_subject
    contradicted_repair = all(
        signal in text for signal in ("repair repeats", "contradicted", "evidence")
    )
    if "review the actual diff" in text and (failed_twice or contradicted_repair):
        add_foundation_selector(
            selector_review_repeat_failure,
            "direct",
            "review-agent",
            stage="review",
            precedence_class="review-risk",
        )
    if "review the actual diff" in text:
        refactoring_state = structure_states["refactoring"]
        placement_state = structure_states["owner-placement"]
        minimality_state = structure_states["minimality"]
        readability_state = structure_states["readability"]
        if EFFECT_AMBIGUOUS in (
            refactoring_state,
            placement_state,
            minimality_state,
            readability_state,
        ):
            add_foundation_selector(
                selector_review_ambiguous_structure,
                "analyzed",
                "analysis-agent",
                stage="review",
                precedence_class="unresolved-boundary",
            )
        if minimality_state == EFFECT_CHANGED:
            add_foundation_selector(
                selector_review_minimality,
                "direct",
                "review-agent",
                stage="review",
                precedence_class="review-structure",
            )
        review_structure_layers: list[str] = []
        if structure_states["domain-object"] == EFFECT_CHANGED:
            review_structure_layers.append("domain-object-identification")
        if structure_states["pattern"] == EFFECT_CHANGED:
            review_structure_layers.append("design-pattern-selection")
        if review_structure_layers:
            add_candidate(
                "direct",
                "review-agent",
                "ai-code-review-refactor",
                review_structure_layers,
                "ai-code-review-refactor",
                rule_id="review-domain-pattern-structure",
                stage="review",
                precedence_class="review-structure",
                match_evidence=["actual-diff", "domain-or-pattern-change"],
            )
        placement_relation_review = (
            _owner_placement_has_relation_mutation(text)
        )
        if (
            refactoring_state == EFFECT_CHANGED
            or placement_relation_review
        ):
            layers = ["refactoring"]
            if (
                placement_state == EFFECT_CHANGED
                and not _fixed_refactoring_destination(text)
            ):
                layers.insert(0, "implementation-structure-design")
            add_candidate(
                "direct",
                "review-agent",
                "ai-code-review-refactor",
                layers,
                "ai-code-review-refactor",
                rule_id="review-refactoring-change",
                stage="review",
                precedence_class="review-structure",
                match_evidence=["actual-diff", "refactoring-change"],
            )
        if readability_state == EFFECT_CHANGED:
            add_foundation_selector(
                selector_review_readability,
                "direct",
                "review-agent",
                stage="review",
                precedence_class="review-quality",
            )
    if "reliability-only failure with no abuse or privacy risk" in text:
        add_foundation_selector(
            selector_security_anti_reliability,
            "analyzed",
            "analysis-agent",
            stage="specialist-negative",
            precedence_class="explicit-anti-trigger",
        )
    if "input shape change with no security sink" in text:
        add_foundation_selector(
            selector_security_anti_input,
            "analyzed",
            "analysis-agent",
            stage="specialist-negative",
            precedence_class="explicit-anti-trigger",
        )
    if "scanner report organization without a security verdict" in text:
        add_foundation_selector(
            selector_security_anti_scanner,
            "direct",
            "task-agent",
            stage="specialist-negative",
            precedence_class="explicit-anti-trigger",
        )
    if "credential or session lifecycle behavior change" in text:
        add_foundation_selector(
            selector_security_credential_session,
            "analyzed",
            "analysis-agent",
            stage="risk",
            precedence_class="security-boundary",
        )

    documentation_change = (
        (
            all(
                signal in text
                for signal in (
                    "documentation",
                    "module ownership",
                    "dependency direction",
                    "runtime behavior",
                    "architecture",
                )
            )
            and bool(
                re.search(
                    r"\b(?:runtime behavior and architecture|"
                    r"architecture and runtime behavior)\s+"
                    r"(?:remain|remains|stay|stays|are)\s+unchanged\b",
                    text,
                )
            )
        )
        or
        (
            any(signal in text for signal in ("documentation", "source comment"))
            and any(
                signal in text
                for signal in (
                    "without changing",
                    "no personal or sensitive data handling",
                    "no desired-state source change",
                )
            )
        )
        or "source comments" in text
        or "comments with no" in text
        or (
            "source comment" in text
            and "unchanged" in text
            and structure_states["pattern"] != EFFECT_CHANGED
        )
    )
    if documentation_change:
        add_candidate(
            "direct",
            "task-agent",
            "change-documentation-gate",
            authority_documentation_foundations,
            "change-documentation-gate",
            rule_id="documentation-only-change",
            stage="documentation",
            precedence_class="non-runtime-change",
            match_evidence=["documentation-change", "runtime-behavior-unchanged"],
        )
    if structure_states["refactoring"] == EFFECT_CHANGED:
        if _fixed_refactoring_destination(text):
            add_foundation_selector(
                selector_refactor_fixed,
                "analyzed",
                "analysis-agent",
                stage="structure",
                precedence_class="analysis-artifact",
            )
    module_boundary_ownership_analysis = any(
        all(
            (
                "module boundary" in statement,
                "ownership change" in statement,
                "historical context" not in statement,
                re.search(
                    r"\b(?:module boundary|module ownership|dependency edges?)\b"
                    r"[^.;!?]{0,100}\b(?:remain|remains|are)\s+unchanged\b",
                    statement,
                )
                is None,
            )
        )
        for statement in analysis_decision_statements
    )
    if technology_stack_risk:
        if artifact_binding_id is not None:
            add_candidate(
                "direct",
                "review-agent",
                "high-risk-design-review",
                list(selector_technology_stack.foundations),
                "high-risk-design-review",
                rule_id="high-risk-technology-stack-review",
                stage="review",
                precedence_class="high-risk-analysis",
                match_evidence=list(
                    selector_technology_stack.evidence_ids
                ),
            )
        elif text.startswith("analyze "):
            add_foundation_selector(
                selector_technology_stack,
                "analyzed",
                "analysis-agent",
                stage="structure",
                precedence_class="architecture-boundary",
            )
    if artifact_binding_id is not None and major_module_review:
        add_candidate(
            "direct",
            "review-agent",
            "high-risk-design-review",
            list(selector_module_boundary.foundations),
            "high-risk-design-review",
            rule_id="high-risk-module-boundary-review",
            stage="review",
            precedence_class="high-risk-analysis",
            match_evidence=list(selector_module_boundary.evidence_ids),
        )
    elif artifact_binding_id is None and (
        structure_states["module-boundary"] == EFFECT_CHANGED
        or module_boundary_ownership_analysis
        or (
            ("module ownership" in text or "dependency direction" in text)
            and "runtime behavior and architecture" in text
            and not documentation_change
        )
    ):
        add_foundation_selector(
            selector_module_boundary,
            "analyzed",
            "analysis-agent",
            stage="structure",
            precedence_class="architecture-boundary",
        )
    if domain_object_analysis_intent:
        add_foundation_selector(
            selector_domain_object,
            "analyzed",
            "analysis-agent",
            stage="structure",
            precedence_class="domain-model",
        )
    if (
        structure_states["pattern"] == EFFECT_CHANGED
        and analysis_only_action
    ):
        add_foundation_selector(
            selector_design_pattern,
            "analyzed",
            "analysis-agent",
            stage="structure",
            precedence_class="architecture-boundary",
        )
    dto_mapping_subject = all(
        signal in text for signal in ("accepted engineering brief", "dto")
    ) and any(signal in text for signal in ("table", "ui label", "mapping"))
    if (
        dto_mapping_subject
        and structure_states["domain-object"] != EFFECT_CHANGED
    ):
        add_foundation_selector(
            selector_dto_boundary,
            "analyzed",
            "analysis-agent",
            stage="contract",
            precedence_class="analysis-artifact",
        )
    sdk_contract_subject = all(
        signal in text
        for signal in ("accepted engineering brief", "distributable sdk")
    ) and any(signal in text for signal in ("public contract", "compatibility"))
    if sdk_contract_subject:
        add_foundation_selector(
            selector_sdk_contract,
            "analyzed",
            "analysis-agent",
            stage="contract",
            precedence_class="analysis-artifact",
        )
    package_decision_subject = (
        any(
            signal in text
            for signal in (
                "install a new package",
                "new package because of a current capability gap",
            )
        )
        and any(
            signal in text
            for signal in ("license", "vulnerability", "supply chain")
        )
    )
    if package_decision_subject:
        if _dependency_package_risk(text):
            add_candidate(
                "analyzed",
                "analysis-agent",
                "engineering-change-analysis",
                authority_package_supply_chain_foundations,
                "architecture-impact-reviewer",
                rule_id="package-supply-chain-analysis",
                stage="dependency",
                precedence_class="analysis-artifact",
                match_evidence=[
                    "package-capability-gap",
                    "material-package-risk-decision",
                ],
            )
        else:
            add_foundation_selector(
                selector_package_dependency,
                "analyzed",
                "analysis-agent",
                stage="dependency",
                precedence_class="analysis-artifact",
            )
    if (
        structure_states["minimality"] == EFFECT_CHANGED
        and analysis_only_action
        and not package_decision_subject
    ):
        add_candidate(
            "analyzed",
            "analysis-agent",
            "engineering-change-analysis",
            authority_minimality_foundations,
            "architecture-impact-reviewer",
            rule_id="minimality-analysis",
            stage="structure",
            precedence_class="analysis-artifact",
            match_evidence=["minimality-change", "analysis-only"],
        )
    if "multiple dependent tasks" in text:
        add_candidate(
            "analyzed",
            "analysis-agent",
            "engineering-change-analysis",
            [],
            "ai-code-review-refactor",
            rule_id="dependent-task-analysis-early",
            stage="planning",
            precedence_class="task-decomposition",
            match_evidence=["multiple-dependent-tasks"],
        )
    if any(
        signal in text
        for signal in (
            "production apply",
            "production rollout",
            "already-built production rollout",
        )
    ):
        add_foundation_selector(
            selector_production_release,
            "analyzed",
            "analysis-agent",
            stage="release",
            precedence_class="production-boundary",
        )
    repository_tooling_change = any(
        signal in text
        for signal in (
            "repository-owned generator",
            "compiler plugin source",
            "linter plugin source",
            "formatter plugin source",
            "test harness source",
            "benchmark harness source",
            "internal cli source",
            "repository cli",
            "monorepo automation source",
            "maintenance utility source",
        )
    )
    if repository_tooling_change:
        if (
            filesystem_effect_state == EFFECT_AMBIGUOUS
            or structure_states["owner-placement"] == EFFECT_AMBIGUOUS
            or structure_states["pattern"] == EFFECT_AMBIGUOUS
            or structure_states["minimality"] == EFFECT_AMBIGUOUS
        ):
            add_candidate(
                "analyzed",
                "analysis-agent",
                "engineering-change-analysis",
                authority_repository_foundations,
                "architecture-impact-reviewer",
                rule_id="repository-tooling-ambiguous",
                stage="repository-tooling",
                precedence_class="unresolved-boundary",
                match_evidence=["repository-tooling-change", "ambiguous-effect"],
            )
        repository_layers = [
            "build-tool-professional-usage",
            "targeted-validation-selection",
        ]
        if structure_states["owner-placement"] == EFFECT_CHANGED:
            repository_layers.insert(1, "implementation-structure-design")
        elif structure_states["pattern"] == EFFECT_CHANGED:
            repository_layers.insert(1, "design-pattern-selection")
        elif structure_states["minimality"] == EFFECT_CHANGED:
            repository_layers.insert(1, "minimal-correct-implementation")
        if filesystem_effect_state == EFFECT_CHANGED:
            repository_layers.insert(1, "filesystem-process-safety")
        if len(repository_layers) > 3:
            add_candidate(
                "analyzed",
                "analysis-agent",
                "engineering-change-analysis",
                authority_repository_foundations,
                "architecture-impact-reviewer",
                rule_id="repository-tooling-layer-budget",
                stage="repository-tooling",
                precedence_class="layer-budget",
                match_evidence=["repository-tooling-change", "layer-budget-exceeded"],
            )
    if (
        "active multi-responder incident" in text
        and any(
            signal in text
            for signal in (
                "coordinate",
                "command",
                "mitigation",
                "communications",
                "handoff",
            )
        )
    ):
        add_candidate(
            "analyzed",
            "analysis-agent",
            "incident-response-coordinator",
            authority_incident_response_observability_foundations,
            "reliability-observability-gate",
            rule_id="incident-response-coordination-observability",
            stage="incident",
            precedence_class="active-incident",
            match_evidence=list(selector_incident_response.evidence_ids),
            semantic_atoms=[],
        )
    backend_subject = any(
        signal in text
        for signal in (
            "backend service",
            "backend utility",
            "backend provider",
            "linux server",
            "server daemon",
            "command-line service",
            "node.js backend",
            "dart backend",
            "go backend",
            "jvm service",
            "kotlin coroutine behavior",
            ".net service",
            "windows service",
        )
    ) or (
        action_intent["implementation"]
        and "backend" in text
        and all(
            signal in text
            for signal in ("entity", "table", "dto")
        )
    ) or (
        action_intent["implementation"]
        and "backend" in text
        and any(
            structure_states[family] == EFFECT_CHANGED
            for family in (
                "owner-placement",
                "domain-object",
                "pattern",
                "minimality",
            )
        )
    )
    backend_change = backend_subject
    if backend_change:
        if (
            filesystem_effect_state == EFFECT_AMBIGUOUS
            or node_effect_state == EFFECT_AMBIGUOUS
            or any(
                structure_states[family] == EFFECT_AMBIGUOUS
                for family in (
                    "owner-placement",
                    "domain-object",
                    "pattern",
                    "minimality",
                )
            )
        ):
            add_candidate(
                "analyzed",
                "analysis-agent",
                "engineering-change-analysis",
                authority_repository_foundations,
                "architecture-impact-reviewer",
                rule_id="backend-effects-ambiguous",
                stage="backend",
                precedence_class="unresolved-boundary",
                match_evidence=["backend-subject", "ambiguous-effect"],
            )
        language_layers: list[str] = []
        if node_effect_state == EFFECT_CHANGED:
            language_layers.append("nodejs-runtime-professional-usage")
        if filesystem_effect_state == EFFECT_CHANGED:
            language_layers.append("filesystem-process-safety")
        if (
            "kotlin" in text
            and "no kotlin source" not in text
            and any(
                signal in text
                for signal in ("coroutine", "stateflow", "kotlin code")
            )
        ):
            language_layers.append("kotlin-professional-usage")
        if (
            ("c#" in text or ".net" in text)
            and "no c# or .net source" not in text
            and any(
                signal in text
                for signal in (
                    "async disposal",
                    "cancellationtoken",
                    "trimming",
                    "aot behavior",
                )
            )
        ):
            language_layers.append("csharp-dotnet-professional-usage")
        if structure_states["domain-object"] == EFFECT_CHANGED:
            language_layers.insert(0, "domain-object-identification")
        if structure_states["pattern"] == EFFECT_CHANGED:
            language_layers.append("design-pattern-selection")
            if any(
                signal in text
                for signal in (
                    "synchronization",
                    "concurrent caller",
                    "concurrency",
                )
            ):
                language_layers.append("concurrency-control")
        if structure_states["minimality"] == EFFECT_CHANGED:
            language_layers.append("minimal-correct-implementation")
        if structure_states["owner-placement"] == EFFECT_CHANGED:
            language_layers.append("implementation-structure-design")
        language_layers = list(dict.fromkeys(language_layers))
        if len(language_layers) > 3:
            add_candidate(
                "analyzed",
                "analysis-agent",
                "engineering-change-analysis",
                authority_repository_foundations,
                "architecture-impact-reviewer",
                rule_id="backend-layer-budget",
                stage="backend",
                precedence_class="layer-budget",
                match_evidence=["backend-subject", "layer-budget-exceeded"],
            )

    if (
        "tenant isolation" in text
        and "no tenant identity propagation" not in text
        and any(
            signal in text
            for signal in (
                "storage",
                "cache",
                "queue",
                "execution context",
                "telemetry",
                "administrative",
                "migration",
                "deletion",
                "export",
            )
        )
    ):
        add_foundation_selector(
            selector_tenant_isolation,
            "analyzed",
            "analysis-agent",
            stage="risk",
            precedence_class="security-boundary",
        )
    if any(
        signal in text
        for signal in (
            "cryptographic provider api mechanics only",
            "custom cryptographic primitive",
            "legal compliance claim about encryption",
        )
    ):
        add_candidate(
            "analyzed",
            "analysis-agent",
            "security-privacy-gate",
            [],
            "security-privacy-gate",
            rule_id="cryptography-specialist-boundary",
            stage="risk",
            precedence_class="security-boundary",
            match_evidence=["cryptography-specialist-decision"],
        )
    if "personal-data collection purpose and retention" in text:
        add_foundation_selector(
            selector_personal_data,
            "analyzed",
            "analysis-agent",
            stage="risk",
            precedence_class="privacy-boundary",
        )
    if "legal admissibility of records" in text:
        add_candidate(
            "analyzed",
            "analysis-agent",
            "security-privacy-gate",
            [],
            "security-privacy-gate",
            rule_id="legal-record-admissibility",
            stage="risk",
            precedence_class="security-boundary",
            match_evidence=["legal-admissibility"],
        )
    if (
        (
            "cryptographic construction" in text
            and "no cryptographic construction" not in text
        )
        or (
            "key lifecycle decision" in text
            and "no key lifecycle decision" not in text
        )
        or (
            all(signal in text for signal in ("nonce", "ciphertext envelope"))
            and "no nonce" not in text
            and "no ciphertext envelope" not in text
        )
    ):
        add_foundation_selector(
            selector_cryptography,
            "analyzed",
            "analysis-agent",
            stage="risk",
            precedence_class="security-boundary",
        )
    if (
        "secret rotation" in text
        and (
            "cryptographic construction" not in text
            or "no cryptographic construction" in text
        )
    ):
        add_candidate(
            "analyzed",
            "analysis-agent",
            "security-privacy-gate",
            authority_secret_foundations,
            "security-privacy-gate",
            rule_id="secret-rotation",
            stage="risk",
            precedence_class="security-boundary",
            match_evidence=["secret-rotation", "no-cryptographic-construction"],
        )
    if (
        audit_integrity_subject
        and not action_intent["audit_implementation_ambiguous"]
    ):
        implementation = action_intent["audit_implementation"]
        if (
            audit_review_task
            or (
                not implementation
                and (
                    action_intent["audit_analysis"]
                    or not action_intent["implementation"]
                )
            )
        ):
            add_foundation_selector(
                selector_audit_integrity,
                "direct" if audit_review_task else "analyzed",
                "review-agent" if audit_review_task else "analysis-agent",
                stage="risk",
                precedence_class="audit-boundary",
            )
    if distributed_effect_state == EFFECT_AMBIGUOUS:
        add_candidate(
            "analyzed",
            "analysis-agent",
            "engineering-change-analysis",
            authority_repository_foundations,
            "architecture-impact-reviewer",
            rule_id="distributed-effect-ambiguous",
            stage="distributed-workflow",
            precedence_class="unresolved-boundary",
            match_evidence=["distributed-effect-ambiguous"],
        )
    if distributed_effect_state == EFFECT_CHANGED:
        add_foundation_selector(
            selector_distributed_workflow,
            "analyzed",
            "analysis-agent",
            stage="distributed-workflow",
            precedence_class="data-boundary",
        )
        add_foundation_selector(
            selector_distributed_consistency,
            "analyzed",
            "analysis-agent",
            stage="distributed-workflow",
            precedence_class="data-boundary",
        )

    dedicated_credential_lifecycle = (
        "credential or session lifecycle behavior change" in text
    )
    privacy_decision = not dedicated_credential_lifecycle and any(
        _security_boundary_is_proved(facts)
        and any(
            item.endswith("sensitive-lifecycle-change")
            for item in facts.evidence_ids
        )
        for facts in routing_boundary_facts
    )
    credential_lifecycle_decision = not dedicated_credential_lifecycle and any(
        _security_boundary_is_proved(facts)
        and any(
            item.endswith("credential-lifecycle-change")
            for item in facts.evidence_ids
        )
        for facts in routing_boundary_facts
    )
    if (
        (privacy_decision or credential_lifecycle_decision)
        and not action_intent["implementation"]
    ):
        add_candidate(
            "analyzed",
            "analysis-agent",
            "security-privacy-gate",
            (
                authority_privacy_foundations
                if privacy_decision
                else []
            ),
            "security-privacy-gate",
            rule_id="privacy-or-token-security",
            stage="risk",
            precedence_class="security-boundary",
            match_evidence=["privacy-decision-or-token-validation"],
        )

    infrastructure_change = any(
        signal in text
        for signal in (
            "terraform",
            "opentofu",
            "cloudformation",
            "pulumi",
            "helm source",
            "kustomize",
            "kubernetes manifest source",
            "powershell infrastructure",
        )
    )
    if infrastructure_change:
        infrastructure_layers: list[str] = []
        if any(
            signal in text
            for signal in ("terraform", "opentofu", "cloudformation", "pulumi")
        ):
            infrastructure_layers.append("infrastructure-as-code-safety")
        if "powershell infrastructure" in text:
            infrastructure_layers.append("powershell-professional-usage")

    installed_change = bool(target_domains) or any(
        signal in text
        for signal in (
            "installed-client",
            "installed client",
            "native android-only application",
            "swift actor isolation",
            "offline sync",
            "online-only client copy",
            "process-death state restoration",
        )
    )
    if installed_change:
        if filesystem_effect_state == EFFECT_AMBIGUOUS:
            add_candidate(
                "analyzed",
                "analysis-agent",
                "engineering-change-analysis",
                authority_repository_foundations,
                "architecture-impact-reviewer",
                rule_id="installed-filesystem-ambiguous",
                stage="installed-client",
                precedence_class="unresolved-boundary",
                match_evidence=["installed-client", "filesystem-effect-ambiguous"],
            )
        client_layers: list[str] = []
        if filesystem_effect_state == EFFECT_CHANGED:
            client_layers.append("filesystem-process-safety")
        if (
            any(
                signal in text
                for signal in ("state-restoration", "process termination")
            )
            and "no lifecycle" not in text
            and "no shared restoration" not in text
        ):
            client_layers.append("client-lifecycle-state-restoration")
        if (
            all(signal in text for signal in ("offline", "conflict"))
            and any(signal in text for signal in ("reconnect", "pending-operation"))
            and "no offline synchronization" not in text
        ):
            client_layers.append("offline-sync-conflict-resolution")
        if (
            "swift actor isolation" in text
            and "no swift source" not in text
        ):
            client_layers.append("swift-professional-usage")
        client_layers = list(dict.fromkeys(client_layers))
        if len(client_layers) > 3:
            raise RoutingIntegrityError(
                f"installed-client Layer 3 budget exceeded: {client_layers!r}"
            )

    test_strategy_professional_analysis = any(
        all(
            (
                "proof portfolio" in statement,
                "failure mechanism" in statement,
                "test level" in statement,
                "failure oracle" in statement,
                any(
                    action in statement
                    for action in ("choose", "select")
                ),
                re.search(
                    r"\b(?:proof portfolio|test levels?|failure oracles?)\b"
                    r"[^.;!?]{0,80}\b(?:already )?fixed\b",
                    statement,
                )
                is None,
            )
        )
        for statement in analysis_decision_statements
    )
    if (
        test_strategy_professional_analysis
        and "test-strategy" not in matched_foundation_names
    ):
        add_candidate(
            "analyzed",
            "analysis-agent",
            "quality-test-gate",
            authority_test_strategy_foundations,
            "quality-test-gate",
            rule_id="test-strategy-professional-precedence",
            stage="specialist-precedence",
            precedence_class="quality-proof-strategy",
            match_evidence=[
                "analysis-action",
                "proof-portfolio-level-oracle-selection",
            ],
        )
    ssrf_threat_professional_analysis = any(
        all(
            (
                "ssrf" in statement,
                "url fetch" in statement,
                "threat" in statement,
                "threat terminology" not in statement,
                "without analyzing" not in statement,
                "no abuse path" not in statement,
                "security behavior remains unchanged" not in statement,
            )
        )
        for statement in analysis_decision_statements
    )
    if "ssrf" in text and "url fetch" in text:
        if ssrf_threat_professional_analysis:
            add_candidate(
                "analyzed",
                "analysis-agent",
                "security-privacy-gate",
                list(selector_ssrf.foundations),
                "security-privacy-gate",
                rule_id="ssrf-threat-professional-precedence",
                stage="specialist-precedence",
                precedence_class="security-boundary",
                match_evidence=["ssrf-url-fetch-threat-analysis"],
            )
        else:
            add_foundation_selector(
                selector_ssrf,
                "analyzed",
                "analysis-agent",
                stage="risk",
                precedence_class="security-boundary",
            )
    dedicated_auth_handoff = (
        "explicit authentication and authorization handoff decision" in text
    )
    proved_security_boundary = any(
        _security_boundary_is_proved(facts)
        for facts in routing_boundary_facts
    )
    if (
        proved_security_boundary
        and not action_intent["implementation"]
        and not privacy_decision
        and not credential_lifecycle_decision
        and not dedicated_credential_lifecycle
        and not dedicated_auth_handoff
    ):
        add_candidate(
            "analyzed",
            "analysis-agent",
            "security-privacy-gate",
            authority_generic_security_foundations,
            "security-privacy-gate",
            rule_id="generic-security-risk",
            stage="risk",
            precedence_class="security-boundary",
            match_evidence=["authorization-permission-privacy-or-security"],
        )
    if any(signal in text for signal in ("diagnose the root cause", "failure diagnosis")):
        add_candidate(
            "analyzed",
            "analysis-agent",
            "engineering-change-analysis",
            authority_failure_foundations,
            "reliability-observability-gate",
            rule_id="failure-diagnosis-analysis",
            stage="diagnosis",
            precedence_class="analysis-mode",
            match_evidence=["root-cause-or-failure-diagnosis"],
        )
    if "repository source evidence" in text and any(
        signal in text for signal in ("explain", "question")
    ):
        add_candidate(
            "analyzed",
            "analysis-agent",
            "engineering-change-analysis",
            authority_repository_foundations,
            "architecture-impact-reviewer",
            rule_id="source-backed-repository-question",
            stage="source-analysis",
            precedence_class="analysis-mode",
            match_evidence=["repository-source-evidence", "question-or-explanation"],
        )
    if "ambiguous" in text:
        add_foundation_selector(
            selector_ambiguous_intake,
            "analyzed",
            "analysis-agent",
            stage="intake",
            precedence_class="unresolved-boundary",
        )
    if "observable acceptance" in text:
        add_foundation_selector(
            selector_acceptance,
            "analyzed",
            "analysis-agent",
            stage="intake",
            precedence_class="analysis-artifact",
        )
    if "owner and blast radius" in text:
        add_candidate(
            "analyzed",
            "analysis-agent",
            "engineering-change-analysis",
            authority_repository_foundations,
            "architecture-impact-reviewer",
            rule_id="owner-blast-radius-analysis",
            stage="source-analysis",
            precedence_class="analysis-mode",
            match_evidence=["owner-and-blast-radius"],
        )
    if "explicit architecture tradeoff" in text:
        add_foundation_selector(
            selector_architecture_tradeoff,
            "analyzed",
            "analysis-agent",
            stage="structure",
            precedence_class="architecture-boundary",
        )
    if "explicit test-data decision" in text:
        add_foundation_selector(
            selector_test_data,
            "analyzed",
            "analysis-agent",
            stage="quality",
            precedence_class="analysis-artifact",
        )
    if "explicit authentication and authorization handoff decision" in text:
        add_foundation_selector(
            selector_authentication_authorization,
            "analyzed",
            "analysis-agent",
            stage="risk",
            precedence_class="security-boundary",
        )
    if "accepted engineering brief" in text and "explicit task dag" in text:
        add_foundation_selector(
            selector_task_dag,
            "analyzed",
            "analysis-agent",
            stage="planning",
            precedence_class="analysis-artifact",
        )
    if (
        "high-risk multiple tasks" in text
        and "architecture, module boundaries, and dependency graph are accepted and fixed"
        in text
    ):
        add_candidate(
            "analyzed",
            "analysis-agent",
            "engineering-change-analysis",
            authority_release_foundations[:1],
            "high-risk-design-review",
            rule_id="high-risk-architecture-plan",
            stage="planning",
            precedence_class="high-risk-analysis",
            match_evidence=[
                "high-risk-multiple-tasks",
                "architecture-module-and-dependency-fixed",
            ],
        )
    if "multiple dependent tasks" in text:
        add_candidate(
            "analyzed",
            "analysis-agent",
            "engineering-change-analysis",
            [],
            "ai-code-review-refactor",
            rule_id="dependent-task-analysis-fallback",
            stage="planning",
            precedence_class="task-decomposition",
            match_evidence=["multiple-dependent-tasks"],
        )
    if (
        owner_internal_structure_analysis_evidence
        and structure_states["module-boundary"] != EFFECT_CHANGED
        and not documentation_change
    ):
        add_foundation_selector(
            selector_owner_internal_structure,
            "analyzed",
            "analysis-agent",
            stage="structure",
            precedence_class="analysis-mode",
        )
    experience_foundations = _experience_analysis_foundations(
        text,
        parsed=parsed,
    )
    if experience_foundations == selector_user_flow.foundations:
        add_foundation_selector(
            selector_user_flow,
            "analyzed",
            "analysis-agent",
            stage="experience",
            precedence_class="analysis-mode",
        )
    elif experience_foundations == ("interaction-state-modeling",):
        add_candidate(
            "analyzed",
            "analysis-agent",
            "experience-impact-modeler",
            list(experience_foundations),
            "ai-code-review-refactor",
            rule_id="experience-interaction-analysis",
            stage="experience",
            precedence_class="analysis-mode",
            match_evidence=[
                "user-flow",
                "interaction-state-semantics",
            ],
        )
    elif experience_foundations == ("design-system-rules",):
        add_candidate(
            "analyzed",
            "analysis-agent",
            "experience-impact-modeler",
            list(experience_foundations),
            "ai-code-review-refactor",
            rule_id="experience-design-system-analysis",
            stage="experience",
            precedence_class="analysis-mode",
            match_evidence=[
                "user-flow",
                "design-system-semantics",
            ],
        )
    if "accepted engineering brief" in text and "api compatibility artifact" in text:
        add_candidate(
            "analyzed",
            "analysis-agent",
            "data-api-contract-changer",
            authority_version_foundations,
            "architecture-impact-reviewer",
            rule_id="api-compatibility-artifact",
            stage="contract",
            precedence_class="analysis-artifact",
            match_evidence=["accepted-brief", "api-compatibility-artifact"],
        )
    if "public api" in text or "old consumers" in text:
        add_candidate(
            "analyzed",
            "analysis-agent",
            "engineering-change-analysis",
            authority_public_api_foundations,
            "architecture-impact-reviewer",
            rule_id="public-api-analysis",
            stage="contract",
            precedence_class="public-contract",
            match_evidence=["public-api-or-old-consumers"],
        )
    if "accepted engineering brief" in text and "data consistency and recovery artifact" in text:
        add_candidate(
            "analyzed",
            "analysis-agent",
            "data-middleware-change-builder",
            authority_transaction_foundations,
            "quality-test-gate",
            rule_id="data-consistency-artifact",
            stage="data",
            precedence_class="analysis-artifact",
            match_evidence=["accepted-brief", "data-consistency-recovery"],
        )
    if "database migration" in text:
        add_candidate(
            "analyzed",
            "analysis-agent",
            "engineering-change-analysis",
            authority_database_migration_coexistence_rollback_foundations,
            "delivery-release-gate",
            rule_id="database-migration-coexistence-rollback",
            stage="data",
            precedence_class="migration-boundary",
            match_evidence=list(selector_database_migration.evidence_ids),
            semantic_atoms=[],
        )
    if "accepted engineering brief" in text and "integration handoff artifact" in text:
        add_foundation_selector(
            selector_integration_handoff,
            "analyzed",
            "analysis-agent",
            stage="integration",
            precedence_class="analysis-artifact",
        )
    (
        external_consumer_effect,
        external_failure_effect,
        external_reliability_effect,
    ) = _external_integration_effects(text, parsed=parsed)
    external_ambiguity_evidence = [
        "critical-source:external-integration-"
        f"{concern}-effect-contradiction"
        for concern, effect in (
            ("consumer", external_consumer_effect),
            ("failure", external_failure_effect),
            ("reliability", external_reliability_effect),
        )
        if effect == EFFECT_AMBIGUOUS
    ]
    if external_ambiguity_evidence:
        critical_unknown = next(
            (
                candidate
                for candidate in raw_cohort_candidates
                if candidate.get("candidate_id") == "critical-unknown"
            ),
            None,
        )
        if critical_unknown is None:
            raw_cohort_candidates.append(
                {
                    "candidate_id": "critical-unknown",
                    "evidence": external_ambiguity_evidence,
                }
            )
        else:
            critical_unknown["evidence"] = list(
                dict.fromkeys(
                    [
                        *critical_unknown["evidence"],
                        *external_ambiguity_evidence,
                    ]
                )
            )
    external_integration_foundations = (
        _external_integration_analysis_foundations(
            text,
            external_consumer_effect,
            external_failure_effect,
        )
    )
    if external_integration_foundations == (
        "consumer-impact-analysis",
        "failure-contract-design",
    ):
        add_foundation_selector(
            selector_external_integration,
            "analyzed",
            "analysis-agent",
            stage="integration",
            precedence_class="external-contract",
        )
    elif external_integration_foundations == (
        "consumer-impact-analysis",
    ):
        add_candidate(
            "analyzed",
            "analysis-agent",
            "engineering-change-analysis",
            list(external_integration_foundations),
            "ai-code-review-refactor",
            rule_id=(
                "external-integration-consumer-impact-analysis"
            ),
            stage="integration",
            precedence_class="external-contract",
            match_evidence=[
                "external-integration-consumer-impact-semantics",
            ],
        )
    elif external_integration_foundations == (
        "failure-contract-design",
    ):
        add_candidate(
            "analyzed",
            "analysis-agent",
            "engineering-change-analysis",
            list(external_integration_foundations),
            "ai-code-review-refactor",
            rule_id=(
                "external-integration-failure-contract-analysis"
            ),
            stage="integration",
            precedence_class="external-contract",
            match_evidence=[
                "external-integration-failure-contract-semantics",
            ],
        )
    if "cache stampede" in text and "single-flight" in text:
        add_candidate(
            "analyzed",
            "analysis-agent",
            "engineering-change-analysis",
            authority_cache_stampede_reliability_foundations,
            "reliability-observability-gate",
            rule_id="cache-stampede-reliability-controls",
            stage="reliability",
            precedence_class="runtime-risk",
            match_evidence=list(selector_concurrency_control.evidence_ids),
            semantic_atoms=[],
        )
    repeated_side_effect_risk = (
        "same side effect may occur twice" in text
        and (
            "retry/replay" in text
            or "duplicate delivery" in text
        )
        and not re.search(
            r"same side effect may occur twice[^.;!?]{0,80}"
            r"(?:is|are|remain|remains) unchanged",
            text,
        )
    )
    lease_stale_overlap_risk = (
        "lease expiry" in text
        and (
            "stale worker" in text
            or "stale-worker ownership" in text
        )
        and (
            "overlap another execution" in text
            or "overlapping execution" in text
        )
        and not re.search(
            r"lease expiry[^.;!?]{0,180}(?:stale worker|stale-worker "
            r"ownership)[^.;!?]{0,180}(?:overlap another execution|"
            r"overlapping execution)[^.;!?]{0,80}"
            r"(?:is|are|remain|remains) unchanged",
            text,
        )
    )
    retry_unknown_outcome_risk = (
        "duplicate delivery has an unknown side-effect outcome" in text
        and "terminal resolution is required" in text
    )
    reliability_contrast_boundaries_fixed = (
        all(
            boundary in text
            for boundary in (
                "queue topology",
                "failure contract",
                "cross-service workflow",
            )
        )
        and (
            "are unchanged" in text
            or "remain unchanged" in text
        )
    )
    combined_retry_lease_risk = (
        "owner is known" in text
        and retry_unknown_outcome_risk
        and lease_stale_overlap_risk
        and reliability_contrast_boundaries_fixed
    )
    if combined_retry_lease_risk:
        add_candidate(
            "analyzed",
            "analysis-agent",
            "engineering-change-analysis",
            authority_retry_lease_foundations,
            "reliability-observability-gate",
            rule_id="retry-lease-terminal-resolution-analysis",
            stage="reliability",
            precedence_class="runtime-risk",
            match_evidence=[
                *selector_concurrency_control.evidence_ids,
                *selector_backend_idempotency.evidence_ids,
            ],
            semantic_atoms=[],
        )
    elif lease_stale_overlap_risk:
        add_foundation_selector(
            selector_concurrency_control,
            "analyzed",
            "analysis-agent",
            stage="reliability",
            precedence_class="runtime-risk",
        )
    legacy_reliability_signal_match = any(
        word in text for word in ("outage", "slo", "degradation")
    )
    external_reliability_mechanics = (
        external_reliability_effect == EFFECT_CHANGED
    )
    reliability_signal_match = (
        external_reliability_mechanics
        if "external integration" in text
        else legacy_reliability_signal_match
    )
    if (
        reliability_signal_match
        and not ("cache stampede" in text and "single-flight" in text)
    ):
        add_candidate(
            "analyzed",
            "analysis-agent",
            "reliability-observability-gate",
            authority_reliability_foundations,
            "reliability-observability-gate",
            rule_id="reliability-signal-analysis",
            stage="reliability",
            precedence_class="runtime-risk",
            match_evidence=(
                ["outage-slo-or-degradation"]
                if legacy_reliability_signal_match
                else ["external-integration-reliability-mechanics"]
            ),
        )
    if "production rollout" in text:
        add_candidate(
            "analyzed",
            "analysis-agent",
            "delivery-release-gate",
            authority_release_foundations,
            "delivery-release-gate",
            rule_id="production-rollout-fallback",
            stage="release",
            precedence_class="production-boundary",
            match_evidence=["production-rollout"],
        )
    if "migration documentation" in text:
        add_candidate(
            "direct",
            "task-agent",
            "change-documentation-gate",
            authority_documentation_foundations,
            "change-documentation-gate",
            rule_id="migration-documentation",
            stage="documentation",
            precedence_class="non-runtime-change",
            match_evidence=["migration-documentation"],
        )
    if "engineering brief and task plan" in text:
        add_candidate(
            "direct",
            "review-agent",
            "engineering-artifact-review",
            [],
            "engineering-artifact-review",
            rule_id="engineering-artifact-review",
            stage="review",
            precedence_class="artifact-review",
            match_evidence=["engineering-brief", "task-plan"],
        )
    if (
        (
            "backend retry idempotency" in text
            or repeated_side_effect_risk
        )
        and not combined_retry_lease_risk
        and not lease_stale_overlap_risk
    ):
        add_foundation_selector(
            selector_backend_idempotency,
            "analyzed",
            "analysis-agent",
            stage="backend",
            precedence_class="analysis-mode",
        )
    if not raw_cohort_candidates and not route_candidates:
        add_candidate(
            "analyzed",
            "analysis-agent",
            "engineering-change-analysis",
            authority_repository_foundations,
            "architecture-impact-reviewer",
            rule_id="repository-first-default",
            stage="fallback",
            precedence_class="repository-first",
            match_evidence=["no-eligible-specific-candidate"],
        )
    origin_by_candidate_id = {
        **review_risk_origins,
        **implementation_owner_origins,
    }
    candidate_origins = tuple(
        origin_by_candidate_id.get(candidate.get("candidate_id"))
        for candidate in [
            *raw_cohort_candidates,
            *route_candidates,
        ]
    )
    built_candidates = _build_route_candidates(
        raw_cohort_candidates,
        route_candidates,
        normalized_text=text,
        implementation_policy=implementation_policy,
        domain_specs=domain_specs,
        admission_authority=admission_authority,
    )
    if artifact_binding_id:
        for candidate in built_candidates:
            if (
                candidate.get("candidate_id")
                in _BRIEF_REVIEW_BINDING_WRITER_IDS
            ):
                candidate["artifact_binding_id"] = artifact_binding_id
    professional_authority = professional_routing_authority()
    layer3_authority_by_primary = professional_authority[
        "layer3_candidates_by_primary"
    ]
    enriched_candidates = _enrich_route_candidates(
        built_candidates,
        domain_specs=domain_specs,
        domain_authority=domain_authority,
        layer3_authority_by_primary=layer3_authority_by_primary,
        maximum_layer3=implementation_policy["accepted"]["layer3"]["max"],
        admission_authority=admission_authority,
    )
    composed_candidates = _compose_foundation_activation_candidates(
        enriched_candidates,
        candidate_origins=candidate_origins,
        admission_authority=admission_authority,
        maximum_layer3=implementation_policy["accepted"]["layer3"]["max"],
    )
    cohort_selection = _select_route_cohort_candidate(
        composed_candidates,
        implementation_policy=implementation_policy,
        audit_analysis_conflict=audit_analysis_conflict,
        admission_authority=admission_authority,
        layer3_authority_by_primary=layer3_authority_by_primary,
    )
    projected = _project_route_selection(
        project_selection,
        cohort_selection,
    )
    analysis_fields = set(
        CORE_CONTRACTS["route_decision_contract"][
            "main_analysis_assignment_fields"
        ]
    )
    is_analysis_assignment = set(validated_main) == analysis_fields
    if projected["path"] != "analyzed" and is_analysis_assignment:
        raise RoutingIntegrityError(
            "executable route requires Main execution input"
        )
    if len(winner_trace) != 1:
        raise RoutingIntegrityError(
            "route-once pipeline must project exactly one winner trace"
        )
    authority = professional_authority
    decision_main = (
        {
            "producer": validated_main["producer"],
            "task_id": validated_main["task_id"],
        }
        if projected["path"] == "analyzed"
        else validated_main
    )
    envelope = _route_decision_envelope(
        projected,
        winner_trace[0],
        main_execution=decision_main,
        routing_authority=authority,
    )
    decision_errors = validate_route_decision(
        envelope,
        main_execution=decision_main,
        routing_authority=authority,
    )
    if decision_errors:
        raise RoutingIntegrityError("; ".join(decision_errors))
    winner_trace[0]["candidate_coverage"] = "full"
    winner_trace[0]["route_once"] = "proven"
    return {
        "route_decision": envelope,
        "winner_trace": winner_trace[0],
    }


def route(
    prompt: str,
    *,
    main_execution: object,
    domain_registry: object = None,
    professional_registry: object = None,
) -> dict[str, Any]:
    """Return one exact validated Core route-decision envelope."""

    return _route_impl(
        prompt,
        main_execution=main_execution,
        domain_registry=domain_registry,
        professional_registry=professional_registry,
    )["route_decision"]


def route_with_trace(
    prompt: str,
    *,
    main_execution: object,
    domain_registry: object = None,
    professional_registry: object = None,
) -> dict[str, Any]:
    """Return one canonical route decision plus its proven winner trace."""

    return _route_impl(
        prompt,
        main_execution=main_execution,
        domain_registry=domain_registry,
        professional_registry=professional_registry,
    )
