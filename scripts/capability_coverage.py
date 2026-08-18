"""Validate the non-scoring capability coverage inventory and its projections."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from deterministic_route_oracle import (
    oracle_admission_authority,
    route,
    route_with_trace,
)
from validation_utils import (
    ValidationProblem,
    load_yaml_file,
    validate_main_assignment,
)


SCHEMA_VERSION = 1
KIND = "changeforge.capability_coverage_matrix"
TOP_LEVEL_FIELDS = {
    "schema_version",
    "kind",
    "required_space",
    "entries",
}
REQUIRED_SPACE_FIELDS = {
    "engineering_tasks",
    "platforms",
    "language_runtimes",
    "cross_cutting_risks",
    "product_domains",
    "routing_combinations",
}
ENTRY_FIELDS = {
    "id",
    "axis",
    "surface",
    "task_type",
    "language_runtime",
    "cross_cutting_risks",
    "expected_professional_owner",
    "expected_domain_extensions",
    "expected_foundation_skills",
    "coverage_status",
    "disposition",
    "reason",
    "evidence_fixtures",
}


def _route_projection(decision: dict[str, object]) -> dict[str, object]:
    """Project one canonical route envelope to capability fixture fields."""

    result = decision["route_result"]
    assert isinstance(result, dict)
    return {
        "path": decision["path"],
        "profile": result["start_profile"],
        "primary_skill": result["primary_skill"],
        "layer3_skills": result["layer3_skills"],
        "review_skill": result["review_skill"],
    }
AXES = {
    "engineering-task",
    "platform",
    "language-runtime",
    "cross-cutting-risk",
    "product-domain",
    "routing-combination",
}
COVERAGE_STATUSES = {
    "covered",
    "partial",
    "missing",
    "intentionally-unsupported",
}
DISPOSITIONS = {
    "retain-existing",
    "retain-partial",
    "implement-phase-1",
    "do-not-support",
}
LIST_FIELDS = {
    "language_runtime",
    "cross_cutting_risks",
    "expected_domain_extensions",
    "expected_foundation_skills",
    "evidence_fixtures",
}
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
UNSUPPORTED_GAP_TOKENS = {
    "gap:official-primary-source",
    "gap:qualified-reviewer",
}
UNSUPPORTED_REASON_STATES = {"missing", "unavailable"}
UNSUPPORTED_SURFACE_FORBIDDEN_TOKENS = {
    "available",
    "missing",
    "no",
    "not",
    "unavailable",
    "without",
}
ADMISSION_SCHEMA_VERSION = 1
ADMISSION_KIND = "changeforge.capability_admission_cases"
ADMISSION_TOP_LEVEL_FIELDS = {
    "schema_version",
    "kind",
    "description",
    "cases",
}
ADMISSION_ROW_FIELDS = {
    "id",
    "layer",
    "skill",
    "case_kind",
    "prompt",
    "expected",
    "main_execution",
}
ADMISSION_EXPECTED_FIELDS = {"selected", "primary_skill"}
ADMISSION_EFFECT_PRECEDENCE = {
    "professional": (
        "true-conflict",
        "multitask",
        "direct-task",
        "selected",
        "alternate-owner",
    ),
    "foundation": (
        "selected",
        "domain-owned",
        "adjacent",
        "simple",
    ),
    "domain": ("selected", "not-selected"),
}
ADMISSION_DOMAIN_CASE_KINDS = (
    "explicit",
    "unknown",
    "non-target",
    "cross-platform",
    "language-negative",
    "release-framework-mismatch",
)
_ADMISSION_BASE_PROFESSIONAL_EFFECTS = tuple(
    effect
    for effect in ADMISSION_EFFECT_PRECEDENCE["professional"]
    if effect != "true-conflict"
)
_ADMISSION_DOMAIN_OWNER_FAMILIES = {
    "installed-client",
    "platform-infrastructure",
}


def _registry_entries(
    data: object,
    key: str,
) -> dict[str, Mapping[str, object]]:
    if not isinstance(data, dict):
        return {}
    raw_entries = data.get(key)
    if not isinstance(raw_entries, list):
        return {}
    return {
        str(entry["name"]): entry
        for entry in raw_entries
        if isinstance(entry, dict)
        and isinstance(entry.get("name"), str)
        and entry["name"]
    }


def _admission_case_contract(
    professional_registry: object,
    foundation_registry: object,
    domain_registry: object,
) -> dict[str, dict[str, object]]:
    """Derive admission obligations from the three source registries."""

    admission_authority = oracle_admission_authority(
        foundation_registry=foundation_registry,
        professional_registry=professional_registry,
    )
    professional = _registry_entries(
        professional_registry,
        "professional_skills",
    )
    domain = _registry_entries(domain_registry, "domain_skills")
    primary_task_skills = {
        name: professional[name]
        for name in admission_authority.primary_task_skills
    }
    admitted_foundations = {
        foundation
        for selector in admission_authority.foundation_selectors
        for foundation in selector.foundations
    }
    current_domain_names = {
        candidate
        for row in professional.values()
        if row.get("routing_family") in _ADMISSION_DOMAIN_OWNER_FAMILIES
        for candidate in row.get("layer3_candidates", [])
        if isinstance(candidate, str) and candidate in domain
    }
    professional_effects = {
        name: (
            ADMISSION_EFFECT_PRECEDENCE["professional"]
            if isinstance(row.get("routing_family"), str)
            and bool(row.get("routing_family"))
            else _ADMISSION_BASE_PROFESSIONAL_EFFECTS
        )
        for name, row in primary_task_skills.items()
    }
    foundation_effects = {
        name: ADMISSION_EFFECT_PRECEDENCE["foundation"]
        for name in admitted_foundations
    }
    domain_effects = {
        name: ADMISSION_DOMAIN_CASE_KINDS
        for name in current_domain_names
    }
    effects_by_layer = {
        "professional": professional_effects,
        "foundation": foundation_effects,
        "domain": domain_effects,
    }
    return {
        layer: {
            "case_kinds": (
                ADMISSION_DOMAIN_CASE_KINDS
                if layer == "domain"
                else ADMISSION_EFFECT_PRECEDENCE[layer]
            ),
            "skill_prefixes": {
                name: f"capcov-admission-{layer}-{name}"
                for name in sorted(effects_by_skill)
            },
            "applicable_effects": {
                name: tuple(effects)
                for name, effects in sorted(effects_by_skill.items())
            },
        }
        for layer, effects_by_skill in effects_by_layer.items()
    }


def _admission_case_kinds(
    layer: str,
    skill: str,
    contract: Mapping[str, Mapping[str, object]] | None = None,
) -> tuple[str, ...]:
    resolved = ADMISSION_CASE_CONTRACT if contract is None else contract
    layer_contract = resolved.get(layer)
    if not isinstance(layer_contract, Mapping):
        return ()
    applicable = layer_contract.get("applicable_effects")
    if not isinstance(applicable, Mapping):
        return ()
    raw = applicable.get(skill)
    return tuple(raw) if isinstance(raw, Sequence) else ()


def _admission_combinations(
    contract: Mapping[str, Mapping[str, object]],
) -> frozenset[tuple[str, str, str]]:
    return frozenset(
        (layer, skill, case_kind)
        for layer, layer_contract in contract.items()
        for skill in layer_contract.get("skill_prefixes", {})
        for case_kind in _admission_case_kinds(
            layer,
            str(skill),
            contract,
        )
    )


_ADMISSION_REGISTRY_ROOT = Path(__file__).resolve().parents[1] / "src" / "registry"
_ADMISSION_DEFAULT_REGISTRIES = (
    load_yaml_file(_ADMISSION_REGISTRY_ROOT / "professional-skills.yaml"),
    load_yaml_file(_ADMISSION_REGISTRY_ROOT / "foundation-skills.yaml"),
    load_yaml_file(_ADMISSION_REGISTRY_ROOT / "domain-skills.yaml"),
)
ADMISSION_CASE_CONTRACT = _admission_case_contract(
    *_ADMISSION_DEFAULT_REGISTRIES
)
EXPECTED_ADMISSION_COMBINATIONS = _admission_combinations(
    ADMISSION_CASE_CONTRACT
)
EXPECTED_ADMISSION_IDS = frozenset(
    f"{ADMISSION_CASE_CONTRACT[layer]['skill_prefixes'][skill]}-{case_kind}"
    for layer, skill, case_kind in EXPECTED_ADMISSION_COMBINATIONS
)
EXPECTED_ADMISSION_BINDINGS = {
    f"{ADMISSION_CASE_CONTRACT[layer]['skill_prefixes'][skill]}-{case_kind}": (
        layer,
        skill,
        case_kind,
    )
    for layer, skill, case_kind in EXPECTED_ADMISSION_COMBINATIONS
}


def _admission_trace_projection(
    *,
    route_decision: Mapping[str, object],
    winner_trace: Mapping[str, object],
) -> tuple[dict[str, object] | None, list[str]]:
    """Reconstruct the final route projection from trace-bound evidence."""

    selected = winner_trace.get("selected_candidate")
    selection = route_decision.get("selection_evidence")
    if not isinstance(selected, dict):
        return None, ["winner_trace.selected_candidate must be a mapping"]
    if not isinstance(selection, dict):
        return None, ["route_decision.selection_evidence must be a mapping"]

    errors: list[str] = []

    def eligible_skills(field: str) -> list[str]:
        raw = selection.get(field)
        if not isinstance(raw, list):
            errors.append(f"selection_evidence.{field} must be a list")
            return []
        return [
            str(row["skill"])
            for row in raw
            if isinstance(row, dict)
            and row.get("eligible") is True
            and isinstance(row.get("skill"), str)
        ]

    primary = eligible_skills("primary_candidates")
    review = eligible_skills("review_candidates")
    layer3 = eligible_skills("layer3_candidates")
    if len(primary) != 1:
        errors.append(
            "selection_evidence must contain exactly one eligible primary"
        )
    if len(review) != 1:
        errors.append(
            "selection_evidence must contain exactly one eligible review"
        )
    transformed_policy = {
        "critical-unknown": ("analyzed", "analysis-agent"),
        "review-release-risk": ("direct", "review-agent"),
    }
    candidate_id = selected.get("candidate_id")
    path = selected.get("path")
    profile = selected.get("profile")
    if not isinstance(path, str) or not isinstance(profile, str):
        transformed = transformed_policy.get(str(candidate_id))
        if transformed is None:
            errors.append(
                "winner trace lacks a known path/profile projection"
            )
        else:
            path, profile = transformed
    if errors:
        return None, errors
    projection = {
        "path": path,
        "profile": profile,
        "primary_skill": primary[0],
        "layer3_skills": layer3,
        "review_skill": review[0],
    }
    for field in ("path", "profile", "primary_skill", "review_skill"):
        selected_value = selected.get(field)
        if selected_value is not None and selected_value != projection[field]:
            errors.append(
                f"winner_trace.selected_candidate.{field} must equal "
                "selection evidence"
            )
    selected_layer3 = selected.get("layer3_skills")
    if (
        isinstance(selected_layer3, list)
        and any(item not in layer3 for item in selected_layer3)
    ):
        errors.append(
            "winner_trace selected Layer 3 projection must be retained in "
            "the final selection evidence"
        )
    return (None, errors) if errors else (projection, [])


def _admission_conflict_identity_errors(
    *,
    winner_trace: Mapping[str, object],
) -> list[str]:
    """Validate canonical, distinct conflict participants and their bindings."""

    selected = winner_trace.get("selected_candidate")
    raw_candidates = winner_trace.get("raw_candidates")
    excluded = winner_trace.get("excluded_candidates")
    if (
        not isinstance(selected, dict)
        or not isinstance(raw_candidates, list)
        or not isinstance(excluded, list)
    ):
        return ["true-conflict identity structures must be mappings/lists"]

    errors: list[str] = []
    automatic = [
        candidate
        for candidate in raw_candidates
        if isinstance(candidate, dict)
        and candidate.get("candidate_type")
        == "automatic-implementation-owner"
    ]
    if len(automatic) != 2 or len(raw_candidates) != 2:
        errors.append(
            "true-conflict must contain exactly two automatic participants"
        )

    owners: list[str] = []
    candidate_ids: list[str] = []
    evidence_identities: list[str] = []
    for index, candidate in enumerate(automatic):
        owner = candidate.get("primary_skill")
        candidate_id = candidate.get("candidate_id")
        family = candidate.get("routing_family")
        if not isinstance(owner, str) or not owner.strip():
            errors.append(
                f"true-conflict participant[{index}].primary_skill must be "
                "non-blank"
            )
        else:
            owners.append(owner)
            expected_id = f"implementation-owner:{owner}"
            if candidate_id != expected_id:
                errors.append(
                    f"true-conflict participant[{index}].candidate_id must "
                    f"equal {expected_id!r}"
                )
        if not isinstance(candidate_id, str) or not candidate_id.strip():
            errors.append(
                f"true-conflict participant[{index}].candidate_id must be "
                "non-blank"
            )
        else:
            candidate_ids.append(candidate_id)
        if (
            isinstance(family, str)
            and family.strip()
            and isinstance(owner, str)
            and owner.strip()
        ):
            evidence_identities.append(f"{family}:{owner}")
        else:
            errors.append(
                f"true-conflict participant[{index}].routing_family must be "
                "non-blank"
            )

    if len(owners) == 2 and len(set(owners)) != 2:
        errors.append(
            "true-conflict participants must have two distinct primary_skill "
            "owners"
        )
    if len(candidate_ids) == 2 and len(set(candidate_ids)) != 2:
        errors.append(
            "true-conflict participants must have two distinct canonical "
            "candidate IDs"
        )
    if (
        len(evidence_identities) == 2
        and selected.get("evidence") != sorted(evidence_identities)
    ):
        errors.append(
            "true-conflict selected evidence must exactly bind both distinct "
            "participant identities"
        )
    expected_exclusions = [
        {
            **candidate,
            "reason": "ambiguous-implementation-owner",
        }
        for candidate in automatic
    ]
    if excluded != expected_exclusions:
        errors.append(
            "true-conflict exclusions must exactly bind both distinct "
            "participant identities"
        )
    return errors


def _admission_route_integrity_errors(
    *,
    main_execution: object,
    route_decision: object,
    winner_trace: object,
) -> list[str]:
    """Return fail-closed integrity errors for one actual admission route."""

    if not isinstance(main_execution, dict):
        return ["main_execution must be a mapping"]
    if not isinstance(route_decision, dict):
        return ["route_decision must be a mapping"]
    if not isinstance(winner_trace, dict):
        return ["winner_trace must be a mapping"]
    route_result = route_decision.get("route_result")
    selected = winner_trace.get("selected_candidate")
    if not isinstance(route_result, dict):
        return ["route_decision.route_result must be a mapping"]
    if not isinstance(selected, dict):
        return ["winner_trace.selected_candidate must be a mapping"]

    errors: list[str] = []
    analysis_path = route_decision.get("path") == "analyzed"
    if analysis_path:
        if route_decision.get("main_execution_provenance") is not None:
            errors.append(
                "analyzed route main_execution_provenance must be null"
            )
        if route_result.get("execution_level") is not None or route_result.get(
            "level_basis"
        ) is not None:
            errors.append("analyzed route must not carry executable Level or Basis")
    else:
        if route_decision.get("main_execution_provenance") != main_execution:
            errors.append(
                "route_decision.main_execution_provenance must deep-equal "
                "main_execution"
            )
        if route_result.get("execution_level") != main_execution.get(
            "execution_level"
        ):
            errors.append(
                "route_result.execution_level must equal "
                "main_execution.execution_level"
            )
        if route_result.get("level_basis") != main_execution.get("level_basis"):
            errors.append(
                "route_result.level_basis must deep-equal "
                "main_execution.level_basis"
            )
    if route_decision.get("route_once") is not True:
        errors.append("route_decision.route_once must be true")
    if winner_trace.get("route_once") != "proven":
        errors.append("winner_trace.route_once must equal 'proven'")
    if winner_trace.get("candidate_coverage") != "full":
        errors.append("winner_trace.candidate_coverage must equal 'full'")
    if (
        selected.get("candidate_id") == "implementation-owner-conflict"
        or selected.get("reason") == "implementation-owner-conflict"
    ):
        errors.extend(
            _admission_conflict_identity_errors(
                winner_trace=winner_trace,
            )
        )

    trace_projection, trace_errors = _admission_trace_projection(
        route_decision=route_decision,
        winner_trace=winner_trace,
    )
    errors.extend(trace_errors)
    decision_projection = _route_projection(route_decision)
    if trace_projection is not None:
        for field, decision_value in decision_projection.items():
            if decision_value == trace_projection.get(field):
                continue
            errors.append(
                f"route projection {field!r} must equal the winner trace"
            )
    return errors


def _strict_admission_conflict_errors(
    *,
    skill: str,
    route_decision: Mapping[str, object],
    winner_trace: Mapping[str, object],
) -> list[str]:
    """Validate the exact two-owner conflict policy for one target Skill."""

    selected = winner_trace.get("selected_candidate")
    raw_candidates = winner_trace.get("raw_candidates")
    excluded = winner_trace.get("excluded_candidates")
    route_result = route_decision.get("route_result")
    if (
        not isinstance(selected, dict)
        or not isinstance(raw_candidates, list)
        or not isinstance(excluded, list)
        or not isinstance(route_result, dict)
    ):
        return ["true-conflict route structures must be mappings/lists"]

    errors = _admission_conflict_identity_errors(
        winner_trace=winner_trace,
    )
    exact_selected = {
        "candidate_id": "implementation-owner-conflict",
        "candidate_type": "derived-conflict",
        "reason": "implementation-owner-conflict",
    }
    for field, expected in exact_selected.items():
        if selected.get(field) != expected:
            errors.append(
                f"true-conflict selected {field} must equal {expected!r}"
            )
    expected_policy = {
        "path": "analyzed",
        "profile": "analysis-agent",
        "primary_skill": "engineering-change-analysis",
        "layer3_skills": ["repository-context-map"],
        "review_skill": "architecture-impact-reviewer",
    }
    actual_policy = {
        "path": route_decision.get("path"),
        "profile": route_result.get("start_profile"),
        "primary_skill": route_result.get("primary_skill"),
        "layer3_skills": route_result.get("layer3_skills"),
        "review_skill": route_result.get("review_skill"),
    }
    if actual_policy != expected_policy:
        errors.append(
            "true-conflict policy route must equal the exact analyzed "
            "engineering-change-analysis contract"
        )

    automatic = [
        candidate
        for candidate in raw_candidates
        if isinstance(candidate, dict)
        and candidate.get("candidate_type")
        == "automatic-implementation-owner"
    ]
    precedences = {
        candidate.get("precedence")
        for candidate in automatic
    }
    all_precedences = [
        candidate.get("precedence")
        for candidate in raw_candidates
        if isinstance(candidate, dict)
        and isinstance(candidate.get("precedence"), int)
    ]
    if (
        len(automatic) != 2
        or len(precedences) != 1
        or not all(isinstance(value, int) for value in precedences)
        or not all_precedences
        or next(iter(precedences), None) != max(all_precedences)
    ):
        errors.append(
            "true-conflict automatic participants must share the highest "
            "precedence"
        )
    participant_skills = {
        candidate.get("primary_skill")
        for candidate in automatic
    }
    if skill not in participant_skills:
        errors.append(
            f"true-conflict target Skill {skill!r} must be an automatic "
            "participant"
        )
    return errors


def _admission_multitask_trace_assessment(
    *,
    route_decision: Mapping[str, object],
    winner_trace: Mapping[str, object],
    owner_authorized_domains: set[str],
) -> tuple[bool, list[str]]:
    """Validate one closed, supported multi-task trace template."""

    route_result = route_decision.get("route_result")
    selected = winner_trace.get("selected_candidate")
    raw_candidates = winner_trace.get("raw_candidates")
    if (
        not isinstance(route_result, dict)
        or not isinstance(selected, dict)
        or not isinstance(raw_candidates, list)
    ):
        return False, ["multitask trace structures must be mappings/lists"]

    accepted_common = {
        "candidate_layer3_context": {
            "kind": "fixed",
            "domain_requests": [],
            "foundation_requests": ["task-dag-decomposition"],
        },
        "eligible_domain_layer3_skills": [],
        "eligible_foundation_layer3_skills": [
            "task-dag-decomposition"
        ],
        "eligible_layer3_skills": ["task-dag-decomposition"],
        "evidence": [
            "accepted-engineering-brief",
            "explicit-task-dag",
            "foundation-selector:accepted-brief-task-dag",
        ],
        "layer3_overflow": False,
        "layer3_skills": ["task-dag-decomposition"],
        "path": "analyzed",
        "precedence": 5,
        "precedence_class": "analysis-artifact",
        "primary_skill": "task-dag-planner",
        "profile": "analysis-agent",
        "reserved_domain_capacity": 0,
        "review_skill": "engineering-artifact-review",
        "rule_id": "accepted-brief-task-dag",
        "semantic_atoms": [],
        "source_foundation_candidates": [
            {
                "candidate_id": "accepted-brief-task-dag",
                "foundations": ["task-dag-decomposition"],
                "evidence": [
                    "accepted-engineering-brief",
                    "explicit-task-dag",
                    "foundation-selector:accepted-brief-task-dag",
                ],
                "owner_binding": {
                    "primary_skill": "task-dag-planner",
                    "review_skill": "engineering-artifact-review",
                },
            }
        ],
        "stage": "planning",
    }
    if selected.get("candidate_id") == "accepted-brief-task-dag":
        expected_raw = [
            {
                "candidate_id": "accepted-brief-task-dag",
                "candidate_type": "explicit-route",
                **accepted_common,
            }
        ]
        expected_selected = {
            "candidate_id": "accepted-brief-task-dag",
            "candidate_type": "explicit-route",
            **accepted_common,
            "reason": "highest-semantic-precedence",
            "source_candidate_ids": ["accepted-brief-task-dag"],
        }
        errors: list[str] = []
        if route_result.get("layer3_skills") != [
            "task-dag-decomposition"
        ]:
            errors.append(
                "accepted-Brief multitask route must select exactly the "
                "task-dag-decomposition Layer 3 Skill"
            )
        if raw_candidates != expected_raw:
            errors.append(
                "accepted-Brief multitask raw trace must exactly equal the "
                "single canonical planner candidate"
            )
        if selected != expected_selected:
            errors.append(
                "accepted-Brief multitask selected trace must exactly bind "
                "the canonical raw planner candidate"
            )
        return not errors, errors

    dependent_source_ids = [
        "dependent-task-analysis-early",
        "dependent-task-analysis-fallback",
    ]
    dependent_signal = (
        selected.get("candidate_id") == "merged-route-candidate"
        and (
            selected.get("evidence") == ["multiple-dependent-tasks"]
            or any(
                source_id in dependent_source_ids
                for source_id in (
                    selected.get("source_candidate_ids")
                    if isinstance(
                        selected.get("source_candidate_ids"),
                        list,
                    )
                    else []
                )
            )
        )
    )
    if not dependent_signal:
        return False, []

    route_layer3 = route_result.get("layer3_skills")
    errors = []
    if (
        not isinstance(route_layer3, list)
        or any(
            not isinstance(item, str) or not item
            for item in route_layer3
        )
        or len(route_layer3) != len(set(route_layer3))
    ):
        errors.append(
            "dependent-task multitask route Layer 3 must be an ordered, "
            "unique string list"
        )
        expected_domains: list[str] = []
    else:
        expected_domains = list(route_layer3)
        unauthorized = [
            item
            for item in expected_domains
            if item not in owner_authorized_domains
        ]
        if unauthorized:
            errors.append(
                "dependent-task multitask route Layer 3 must contain only "
                "reciprocal engineering-change-analysis Domain Skills"
            )

    dependent_layer3 = {
        "candidate_layer3_context": {
            "kind": "fixed",
            "domain_requests": expected_domains,
            "foundation_requests": [],
        },
        "eligible_domain_layer3_skills": expected_domains,
        "eligible_foundation_layer3_skills": [],
        "eligible_layer3_skills": expected_domains,
        "layer3_overflow": False,
        "layer3_skills": expected_domains,
        "reserved_domain_capacity": len(expected_domains),
    }
    dependent_common = {
        "evidence": ["multiple-dependent-tasks"],
        "path": "analyzed",
        "precedence": 5,
        "precedence_class": "task-decomposition",
        "primary_skill": "engineering-change-analysis",
        "profile": "analysis-agent",
        "review_skill": "ai-code-review-refactor",
        "stage": "planning",
        **dependent_layer3,
    }
    expected_raw = [
        {
            "candidate_id": source_id,
            "candidate_type": "explicit-route",
            **dependent_common,
            "rule_id": source_id,
        }
        for source_id in dependent_source_ids
    ]
    expected_selected = {
        **expected_raw[0],
        "candidate_id": "merged-route-candidate",
        "candidate_type": "merged-route",
        "reason": "equal-precedence-same-contract-merge",
        "source_candidate_ids": dependent_source_ids,
    }
    if raw_candidates != expected_raw:
        errors.append(
            "dependent-task multitask raw trace must exactly equal two "
            "ordered, unique canonical candidates"
        )
    if selected != expected_selected:
        errors.append(
            "dependent-task multitask selected trace must exactly bind all "
            "canonical raw semantic fields and source identities"
        )
    return not errors, errors


def _admission_typed_direct_task_proven(
    *,
    route_decision: Mapping[str, object],
    selected: Mapping[str, object],
) -> bool:
    """Return whether final and typed trace projections prove a direct task."""

    route_result = route_decision.get("route_result")
    if not isinstance(route_result, dict):
        return False
    return (
        route_decision.get("path") == "direct"
        and route_result.get("start_profile") == "task-agent"
        and selected.get("path") == "direct"
        and selected.get("profile") == "task-agent"
        and selected.get("primary_skill")
        == route_result.get("primary_skill")
        and selected.get("layer3_skills")
        == route_result.get("layer3_skills")
        and selected.get("review_skill")
        == route_result.get("review_skill")
    )


def _classify_admission_effect(
    *,
    layer: str,
    skill: str,
    declared_case_kind: str,
    main_execution: object,
    route_decision: object,
    winner_trace: object,
    professional_registry: object,
    foundation_registry: object,
    domain_registry: object,
) -> dict[str, object]:
    """Compute one mutually exclusive admission effect from actual routing."""

    integrity_errors = _admission_route_integrity_errors(
        main_execution=main_execution,
        route_decision=route_decision,
        winner_trace=winner_trace,
    )
    if integrity_errors:
        return {"computed_effect": None, "errors": integrity_errors}
    assert isinstance(route_decision, dict)
    assert isinstance(winner_trace, dict)
    route_result = route_decision["route_result"]
    selected = winner_trace["selected_candidate"]
    assert isinstance(route_result, dict)
    assert isinstance(selected, dict)

    professional = _registry_entries(
        professional_registry,
        "professional_skills",
    )
    foundation = _registry_entries(
        foundation_registry,
        "foundation_skills",
    )
    domain = _registry_entries(domain_registry, "domain_skills")
    registry_by_layer = {
        "professional": professional,
        "foundation": foundation,
        "domain": domain,
    }
    if layer not in registry_by_layer:
        return {
            "computed_effect": None,
            "errors": [f"unknown admission layer {layer!r}"],
        }
    if skill not in registry_by_layer[layer]:
        return {
            "computed_effect": None,
            "errors": [
                f"admission Skill {skill!r} is not registered in {layer!r}"
            ],
        }
    if (
        layer == "foundation"
        and foundation[skill].get("delivery_scope") != "product"
    ):
        return {
            "computed_effect": None,
            "errors": [
                f"Foundation Skill {skill!r} is not product-delivered"
            ],
        }

    computed_effect: str | None
    classifier_errors: list[str] = []
    selected_id = selected.get("candidate_id")
    selected_reason = selected.get("reason")
    if layer == "professional":
        selected_layer3 = route_result.get("layer3_skills")
        layer3 = (
            selected_layer3
            if isinstance(selected_layer3, list)
            else []
        )
        role_selected = (
            route_result.get("primary_skill") == skill
            or route_result.get("review_skill") == skill
        )
        multitask_owner = "engineering-change-analysis"
        multitask_owner_row = professional.get(multitask_owner)
        declared_candidates = (
            multitask_owner_row.get("layer3_candidates")
            if isinstance(multitask_owner_row, Mapping)
            else None
        )
        owner_authorized_domains = {
            candidate
            for candidate in (
                declared_candidates
                if isinstance(declared_candidates, list)
                else []
            )
            if isinstance(candidate, str)
            and candidate in domain
            and isinstance(domain[candidate].get("used_by"), list)
            and multitask_owner in domain[candidate]["used_by"]
        }
        (
            multitask_proven,
            multitask_errors,
        ) = _admission_multitask_trace_assessment(
            route_decision=route_decision,
            winner_trace=winner_trace,
            owner_authorized_domains=owner_authorized_domains,
        )
        conflict_signal = (
            selected_id == "implementation-owner-conflict"
            or selected_reason == "implementation-owner-conflict"
        )
        if conflict_signal:
            classifier_errors.extend(
                _strict_admission_conflict_errors(
                    skill=skill,
                    route_decision=route_decision,
                    winner_trace=winner_trace,
                )
            )
            computed_effect = (
                "true-conflict" if not classifier_errors else None
            )
        elif (
            role_selected
            and skill == multitask_owner
            and multitask_errors
        ):
            computed_effect = None
            classifier_errors.extend(multitask_errors)
        elif (
            role_selected
            and skill == multitask_owner
            and multitask_proven
        ):
            computed_effect = "multitask"
        elif role_selected:
            computed_effect = "selected"
        elif skill in layer3:
            computed_effect = None
            classifier_errors.append(
                "Professional target must be absent from Layer 3 when it is "
                "not selected as the actual primary or review role"
            )
        elif multitask_errors:
            computed_effect = None
            classifier_errors.extend(multitask_errors)
        elif multitask_proven:
            computed_effect = "multitask"
        elif (
            selected.get("candidate_type")
            == "automatic-implementation-owner"
            and isinstance(
                professional[skill].get("routing_family"),
                str,
            )
            and bool(professional[skill].get("routing_family"))
        ):
            computed_effect = "alternate-owner"
        elif _admission_typed_direct_task_proven(
            route_decision=route_decision,
            selected=selected,
        ):
            computed_effect = "direct-task"
        else:
            computed_effect = "alternate-owner"
    elif layer == "foundation":
        selected_layer3 = route_result.get("layer3_skills")
        layer3 = (
            selected_layer3
            if isinstance(selected_layer3, list)
            else []
        )
        product_foundation_names = {
            name
            for name, row in foundation.items()
            if row.get("delivery_scope") == "product"
        }
        if skill in layer3:
            computed_effect = "selected"
        elif any(item in domain for item in layer3):
            computed_effect = "domain-owned"
        elif any(item in product_foundation_names for item in layer3):
            computed_effect = "adjacent"
        else:
            computed_effect = "simple"
    else:
        selected_layer3 = route_result.get("layer3_skills")
        computed_effect = (
            "selected"
            if isinstance(selected_layer3, list) and skill in selected_layer3
            else "not-selected"
        )

    if (
        computed_effect is not None
        and declared_case_kind != computed_effect
    ):
        classifier_errors.append(
            f"declared case_kind {declared_case_kind!r} does not match "
            f"computed effect {computed_effect!r}"
        )
    return {
        "computed_effect": computed_effect,
        "errors": classifier_errors,
    }


def _problem(context: str, message: str) -> str:
    return f"{context}: {message}"


def _unsupported_reason_templates(
    entry: Mapping[str, object],
) -> set[str]:
    """Return exact affirmative reason templates for this inventory surface."""

    reviewer_descriptors = [""]
    raw_surface = entry.get("surface")
    if isinstance(raw_surface, str):
        surface = " ".join(raw_surface.split()).casefold()
        surface_tokens = set(re.findall(r"[a-z0-9]+", surface))
        if (
            re.fullmatch(r"[a-z0-9]+(?:[ -][a-z0-9]+)*", surface)
            and not surface_tokens & UNSUPPORTED_SURFACE_FORBIDDEN_TOKENS
        ):
            reviewer_descriptors.append(f" {surface}")
    return {
        "reliable official or primary source contract evidence is "
        f"{source_state}, and qualified{descriptor} reviewer evidence is "
        f"{reviewer_state}."
        for source_state in UNSUPPORTED_REASON_STATES
        for reviewer_state in UNSUPPORTED_REASON_STATES
        for descriptor in reviewer_descriptors
    }


def _nonblank_strings(
    value: object,
    *,
    context: str,
    field: str,
    errors: list[str],
    nonempty: bool = False,
) -> list[str]:
    if not isinstance(value, list):
        errors.append(_problem(context, f"{field} must be an ordered list[str]"))
        return []
    if nonempty and not value:
        errors.append(_problem(context, f"{field} must not be empty"))
    strings: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            errors.append(
                _problem(context, f"{field}[{index}] must be a non-blank string")
            )
            continue
        strings.append(item.strip())
    if len(strings) != len(set(strings)):
        errors.append(_problem(context, f"{field} must be unique"))
    return strings


def _inventory_values(
    required_space: Mapping[str, object],
    field: str,
    errors: list[str],
    context: str,
) -> list[str]:
    return _nonblank_strings(
        required_space.get(field),
        context=context,
        field=field,
        errors=errors,
        nonempty=True,
    )


def _entry_inventory(
    entries: Sequence[Mapping[str, object]],
    axis: str,
) -> set[str]:
    values: set[str] = set()
    for entry in entries:
        if entry.get("axis") != axis:
            continue
        if axis == "engineering-task":
            value = entry.get("task_type")
            if isinstance(value, str):
                values.add(value.strip())
        elif axis in {"platform", "product-domain"}:
            value = entry.get("surface")
            if isinstance(value, str):
                values.add(value.strip())
        elif axis == "language-runtime":
            raw = entry.get("language_runtime")
            if isinstance(raw, list):
                values.update(
                    item.strip()
                    for item in raw
                    if isinstance(item, str) and item.strip()
                )
        elif axis == "cross-cutting-risk":
            raw = entry.get("cross_cutting_risks")
            if isinstance(raw, list):
                values.update(
                    item.strip()
                    for item in raw
                    if isinstance(item, str) and item.strip()
                )
        elif axis == "routing-combination":
            value = entry.get("id")
            if isinstance(value, str):
                values.add(value.strip())
    return values


def _validate_required_space(
    required_space: object,
    entries: Sequence[Mapping[str, object]],
    *,
    context: str,
    errors: list[str],
) -> None:
    if not isinstance(required_space, dict):
        errors.append(_problem(context, "required_space must be a mapping"))
        return
    if set(required_space) != REQUIRED_SPACE_FIELDS:
        errors.append(
            _problem(
                context,
                "required_space fields must equal "
                f"{sorted(REQUIRED_SPACE_FIELDS)!r}; found {sorted(required_space)!r}",
            )
        )
        return
    inventory = {
        field: _inventory_values(required_space, field, errors, context)
        for field in sorted(REQUIRED_SPACE_FIELDS)
    }
    projections = {
        "engineering_tasks": "engineering-task",
        "platforms": "platform",
        "language_runtimes": "language-runtime",
        "cross_cutting_risks": "cross-cutting-risk",
        "product_domains": "product-domain",
        "routing_combinations": "routing-combination",
    }
    for field, axis in projections.items():
        declared = set(inventory[field])
        covered = _entry_inventory(entries, axis)
        missing = sorted(declared - covered)
        unexpected = sorted(covered - declared)
        if missing:
            errors.append(
                _problem(
                    context,
                    f"required_space.{field} has uncovered value(s): {missing!r}",
                )
            )
        if unexpected:
            errors.append(
                _problem(
                    context,
                    f"{axis} entries contain undeclared value(s): {unexpected!r}",
                )
            )


def _validate_status_contract(
    entry: Mapping[str, object],
    *,
    context: str,
    errors: list[str],
) -> None:
    status = entry.get("coverage_status")
    disposition = entry.get("disposition")
    owner = entry.get("expected_professional_owner")
    domains = entry.get("expected_domain_extensions")
    foundations = entry.get("expected_foundation_skills")
    evidence = entry.get("evidence_fixtures")
    reason = str(entry.get("reason") or "").strip()
    folded_reason = reason.casefold()

    if status == "covered":
        if disposition != "retain-existing":
            errors.append(
                _problem(
                    context,
                    "covered entries require disposition=retain-existing",
                )
            )
        if not isinstance(owner, str) or not owner.strip():
            errors.append(
                _problem(context, "covered entries require a Professional owner")
            )
    elif status == "partial":
        if disposition != "retain-partial":
            errors.append(
                _problem(
                    context,
                    "partial entries require disposition=retain-partial",
                )
            )
        if not isinstance(owner, str) or not owner.strip():
            errors.append(
                _problem(context, "partial entries require a stable Professional owner")
            )
        if "gap" not in folded_reason:
            errors.append(
                _problem(context, "partial entries must name the remaining gap")
            )
    elif status == "missing":
        if disposition != "implement-phase-1":
            errors.append(
                _problem(
                    context,
                    "missing entries require disposition=implement-phase-1",
                )
            )
        if "absent" not in folded_reason and "unsafe" not in folded_reason:
            errors.append(
                _problem(
                    context,
                    "missing entries must state that the capability is absent or unsafe",
                )
            )
    elif status == "intentionally-unsupported":
        if disposition != "do-not-support":
            errors.append(
                _problem(
                    context,
                    "intentionally-unsupported entries require "
                    "disposition=do-not-support",
                )
            )
        if owner is not None:
            errors.append(
                _problem(
                    context,
                    "intentionally-unsupported entries require a null owner",
                )
            )
        if domains not in ([], None) or foundations not in ([], None):
            errors.append(
                _problem(
                    context,
                    "intentionally-unsupported entries require empty Skill lists",
                )
            )
        if not isinstance(evidence, list) or any(
            not isinstance(item, str) or not item.startswith("gap:")
            for item in evidence
        ):
            errors.append(
                _problem(
                    context,
                    "intentionally-unsupported entries may reference only "
                    "non-passing gap evidence",
                )
            )
        evidence_tokens = {
            item for item in evidence or [] if isinstance(item, str)
        }
        if not UNSUPPORTED_GAP_TOKENS.issubset(evidence_tokens):
            errors.append(
                _problem(
                    context,
                    "intentionally-unsupported structured evidence must include "
                    "both gap:official-primary-source and gap:qualified-reviewer",
                )
            )
        normalized_reason = " ".join(reason.split()).casefold()
        if normalized_reason not in _unsupported_reason_templates(entry):
            errors.append(
                _problem(
                    context,
                    "intentionally-unsupported reason must use the affirmative "
                    "official/primary-source and qualified-reviewer gap contract",
                )
            )


def _validate_entry(
    entry: object,
    *,
    index: int,
    errors: list[str],
) -> Mapping[str, object] | None:
    context = f"entries[{index}]"
    if not isinstance(entry, dict):
        errors.append(_problem(context, "entry must be a mapping"))
        return None
    if set(entry) != ENTRY_FIELDS:
        errors.append(
            _problem(
                context,
                f"fields must equal {sorted(ENTRY_FIELDS)!r}; found {sorted(entry)!r}",
            )
        )
    entry_id = entry.get("id")
    if not isinstance(entry_id, str) or ID_PATTERN.fullmatch(entry_id) is None:
        errors.append(_problem(context, "id must be unique lower-kebab"))
    axis = entry.get("axis")
    if axis not in AXES:
        errors.append(
            _problem(context, f"axis must be one of {sorted(AXES)!r}")
        )
    for field in ("surface", "task_type", "reason"):
        value = entry.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(_problem(context, f"{field} must be a non-blank string"))
    owner = entry.get("expected_professional_owner")
    if owner is not None and (
        not isinstance(owner, str) or not owner.strip()
    ):
        errors.append(
            _problem(context, "expected_professional_owner must be string|null")
        )
    validated_lists: dict[str, list[str]] = {}
    for field in sorted(LIST_FIELDS):
        validated_lists[field] = _nonblank_strings(
            entry.get(field),
            context=context,
            field=field,
            errors=errors,
            nonempty=field == "evidence_fixtures",
        )
    domain_count = len(validated_lists["expected_domain_extensions"])
    foundation_count = len(validated_lists["expected_foundation_skills"])
    layer3_count = domain_count + foundation_count
    if layer3_count > 3:
        errors.append(
            _problem(
                context,
                "combined expected Domain+Foundation Skill count must be at "
                f"most 3 for one JIT capsule; found domains={domain_count}, "
                f"foundations={foundation_count}, total={layer3_count}",
            )
        )
    if entry.get("coverage_status") not in COVERAGE_STATUSES:
        errors.append(
            _problem(
                context,
                "coverage_status must be one of "
                f"{sorted(COVERAGE_STATUSES)!r}",
            )
        )
    if entry.get("disposition") not in DISPOSITIONS:
        errors.append(
            _problem(
                context,
                f"disposition must be one of {sorted(DISPOSITIONS)!r}",
            )
        )
    _validate_status_contract(entry, context=context, errors=errors)
    return entry


def evaluate_admission_evidence(
    *,
    root: Path,
    professional_registry: object | None = None,
    foundation_registry: object | None = None,
    domain_registry: object | None = None,
) -> tuple[set[str], list[str]]:
    """Evaluate current admission fixtures against registries and routing."""

    registry_specs = {
        "professional": (
            "professional-skills.yaml",
            "professional_skills",
            professional_registry,
        ),
        "foundation": (
            "foundation-skills.yaml",
            "foundation_skills",
            foundation_registry,
        ),
        "domain": (
            "domain-skills.yaml",
            "domain_skills",
            domain_registry,
        ),
    }
    registries: dict[str, dict[str, Mapping[str, object]]] = {}
    resolved_documents: dict[str, object] = {}
    errors: list[str] = []
    for layer, (filename, key, supplied) in registry_specs.items():
        path = root / "src" / "registry" / filename
        if supplied is None:
            if not path.is_file():
                errors.append(
                    f"capability admission evidence: missing registry {path}"
                )
                resolved = None
            else:
                try:
                    resolved = load_yaml_file(path)
                except (OSError, ValidationProblem) as exc:
                    errors.append(
                        "capability admission evidence: cannot load "
                        f"registry {path}: {exc}"
                    )
                    resolved = None
        else:
            resolved = supplied
        resolved_documents[layer] = resolved
        registries[layer] = _registry_entries(resolved, key)

    fixture_path = (
        root / "evals" / "capability-coverage" / "admission-cases.yaml"
    )
    if not fixture_path.is_file():
        errors.append(
            f"capability admission evidence: missing fixture {fixture_path}"
        )
        return set(), errors
    try:
        document = load_yaml_file(fixture_path)
    except (OSError, ValidationProblem) as exc:
        errors.append(
            f"capability admission evidence: cannot load {fixture_path}: {exc}"
        )
        return set(), errors
    if not isinstance(document, dict):
        errors.append(
            f"capability admission evidence: {fixture_path} must be a mapping"
        )
        return set(), errors
    if set(document) != ADMISSION_TOP_LEVEL_FIELDS:
        errors.append(
            "capability admission evidence: top-level fields must equal "
            f"{sorted(ADMISSION_TOP_LEVEL_FIELDS)!r}; "
            f"found {sorted(document)!r}"
        )
    if (
        type(document.get("schema_version")) is not int
        or document.get("schema_version") != ADMISSION_SCHEMA_VERSION
    ):
        errors.append(
            "capability admission evidence: schema_version must be the exact "
            f"integer {ADMISSION_SCHEMA_VERSION}"
        )
    if document.get("kind") != ADMISSION_KIND:
        errors.append(
            "capability admission evidence: kind must equal "
            f"{ADMISSION_KIND!r}"
        )
    description = document.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append(
            "capability admission evidence: description must be a non-blank "
            "string"
        )
    cases = document.get("cases")
    if not isinstance(cases, list):
        errors.append(
            f"capability admission evidence: {fixture_path}:cases must be a list"
        )
        return set(), errors
    admission_contract = _admission_case_contract(
        resolved_documents["professional"],
        resolved_documents["foundation"],
        resolved_documents["domain"],
    )
    expected_combinations = _admission_combinations(admission_contract)

    ids: list[str] = []
    combinations: list[tuple[str, str, str]] = []
    for index, case in enumerate(cases):
        context = f"capability admission evidence cases[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{context}: case must be a mapping")
            continue
        if set(case) != ADMISSION_ROW_FIELDS:
            errors.append(
                f"{context}: row fields must equal "
                f"{sorted(ADMISSION_ROW_FIELDS)!r}; found {sorted(case)!r}"
            )
        case_id = case.get("id")
        layer = case.get("layer")
        skill = case.get("skill")
        case_kind = case.get("case_kind")
        prompt = case.get("prompt")
        expected = case.get("expected")
        if (
            not isinstance(case_id, str)
            or ID_PATTERN.fullmatch(case_id) is None
        ):
            errors.append(f"{context}: id must be closed lower-kebab")
        else:
            ids.append(case_id)
        for field, value in (
            ("layer", layer),
            ("skill", skill),
            ("case_kind", case_kind),
            ("prompt", prompt),
        ):
            if not isinstance(value, str) or not value.strip():
                errors.append(
                    f"{context}: {field} must be a non-blank string"
                )
        if (
            isinstance(layer, str)
            and isinstance(skill, str)
            and isinstance(case_kind, str)
        ):
            allowed_kinds = set(
                _admission_case_kinds(
                    layer,
                    skill,
                    admission_contract,
                )
            )
            if not allowed_kinds or case_kind not in allowed_kinds:
                errors.append(
                    f"{context}: case_kind {case_kind!r} is not allowed for "
                    f"layer {layer!r} and Skill {skill!r}"
                )
        if all(
            isinstance(value, str)
            for value in (layer, skill, case_kind)
        ):
            combination = (layer, skill, case_kind)
            combinations.append(combination)
        if not isinstance(expected, dict):
            errors.append(f"{context}: expected must be a mapping")
        else:
            if set(expected) != ADMISSION_EXPECTED_FIELDS:
                errors.append(
                    f"{context}: expected fields must equal "
                    f"{sorted(ADMISSION_EXPECTED_FIELDS)!r}; "
                    f"found {sorted(expected)!r}"
                )
            if type(expected.get("selected")) is not bool:
                errors.append(
                    f"{context}: expected.selected must be a boolean"
                )
            expected_owner = expected.get("primary_skill")
            if (
                not isinstance(expected_owner, str)
                or not expected_owner.strip()
            ):
                errors.append(
                    f"{context}: expected.primary_skill must be a non-blank "
                    "string"
                )

    duplicate_ids = sorted(
        {case_id for case_id in ids if ids.count(case_id) > 1}
    )
    if duplicate_ids:
        errors.append(
            "capability admission evidence: case ids must be unique; "
            f"duplicate ids={duplicate_ids!r}"
        )
    duplicate_combinations = sorted(
        {
            combination
            for combination in combinations
            if combinations.count(combination) > 1
        }
    )
    if duplicate_combinations:
        errors.append(
            "capability admission evidence: layer/skill/case_kind "
            "combinations must be unique; duplicate="
            f"{duplicate_combinations!r}"
        )
    if errors:
        return set(), errors

    passing: set[str] = set()
    covered_combinations: set[tuple[str, str, str]] = set()
    domain_document = resolved_documents["domain"]
    for index, case in enumerate(cases):
        context = f"capability admission evidence cases[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{context}: case must be a mapping")
            continue
        case_id = case.get("id")
        layer = case.get("layer")
        skill = case.get("skill")
        prompt = case.get("prompt")
        expected = case.get("expected")
        if not isinstance(case_id, str) or not case_id.strip():
            errors.append(f"{context}: id must be a non-blank string")
            continue
        context = case_id
        if layer not in registries:
            errors.append(f"{context}: unknown admission layer {layer!r}")
            continue
        if not isinstance(skill, str) or skill not in registries[layer]:
            errors.append(
                f"{context}: admission Skill {skill!r} is not registered "
                f"in layer {layer!r}"
            )
            continue
        if not isinstance(prompt, str) or not prompt.strip():
            errors.append(f"{context}: prompt must be a non-blank string")
            continue
        if not isinstance(expected, dict):
            errors.append(f"{context}: expected must be a mapping")
            continue
        main_execution = case.get("main_execution")
        main_errors = validate_main_assignment(main_execution)
        if main_errors:
            errors.extend(
                f"{context}: {error}"
                for error in main_errors
            )
            continue
        expected_owner = expected.get("primary_skill")
        expected_selected = expected.get("selected")
        if not isinstance(expected_owner, str) or type(expected_selected) is not bool:
            errors.append(
                f"{context}: expected requires primary_skill=str and selected=bool"
            )
            continue

        observed = route_with_trace(
            prompt,
            main_execution=main_execution,
            domain_registry=domain_document,
        )
        decision = observed["route_decision"]
        winner_trace = observed["winner_trace"]
        actual = _route_projection(decision)
        case_errors: list[str] = []
        actual_owner = actual.get("primary_skill")
        if actual_owner != expected_owner:
            case_errors.append(
                f"expected primary_skill={expected_owner!r}; "
                f"actual={actual_owner!r}"
            )
        selected = (
            actual_owner == skill
            if layer == "professional"
            else skill in (actual.get("layer3_skills") or [])
        )
        if selected is not expected_selected:
            case_errors.append(
                f"expected selected={expected_selected!r}; actual={selected!r}"
            )
        if layer in {"domain", "foundation"} and expected_selected:
            owner_record = registries["professional"].get(expected_owner)
            candidates = (
                owner_record.get("layer3_candidates")
                if owner_record is not None
                else None
            )
            if not isinstance(candidates, list) or skill not in candidates:
                case_errors.append(
                    f"selected Skill {skill!r} is not a JIT candidate of "
                    f"{expected_owner!r}"
                )
        declared_effect = (
            ("selected" if expected_selected else "not-selected")
            if layer == "domain"
            else case.get("case_kind")
        )
        if not isinstance(declared_effect, str):
            case_errors.append("declared admission effect must be a string")
        else:
            classification = _classify_admission_effect(
                layer=str(layer),
                skill=skill,
                declared_case_kind=declared_effect,
                main_execution=main_execution,
                route_decision=decision,
                winner_trace=winner_trace,
                professional_registry=resolved_documents["professional"],
                foundation_registry=resolved_documents["foundation"],
                domain_registry=resolved_documents["domain"],
            )
            case_errors.extend(
                str(message)
                for message in classification["errors"]
            )
        if case_errors:
            errors.extend(f"{context}: {message}" for message in case_errors)
        else:
            passing.add(case_id)
            case_kind = case.get("case_kind")
            if isinstance(case_kind, str):
                covered_combinations.add((str(layer), skill, case_kind))
    missing_combinations = sorted(
        expected_combinations - covered_combinations
    )
    if missing_combinations:
        errors.append(
            "capability admission evidence: missing obligations="
            f"{missing_combinations!r}"
        )
    return passing, errors


def _evaluate_route_evidence(
    *,
    root: Path,
    relative_path: str,
    domain_registry: object | None,
) -> tuple[dict[str, dict[str, object]], list[str]]:
    """Return passing deterministic route claims for one fixture document."""

    path = root / relative_path
    if not path.is_file():
        return {}, [f"capability route evidence: missing fixture {path}"]
    try:
        document = load_yaml_file(path)
    except (OSError, ValidationProblem) as exc:
        return {}, [f"capability route evidence: cannot load {path}: {exc}"]
    cases = document.get("cases") if isinstance(document, dict) else None
    if not isinstance(cases, list):
        return {}, [f"capability route evidence: {path}:cases must be a list"]
    if domain_registry is None:
        registry_path = root / "src" / "registry" / "domain-skills.yaml"
        if not registry_path.is_file():
            return {}, [
                "capability route evidence: missing domain registry "
                f"{registry_path}"
            ]
        try:
            domain_registry = load_yaml_file(registry_path)
        except (OSError, ValidationProblem) as exc:
            return {}, [
                "capability route evidence: cannot load domain registry "
                f"{registry_path}: {exc}"
            ]

    claims: dict[str, dict[str, object]] = {}
    errors: list[str] = []
    ids: list[str] = []
    for index, case in enumerate(cases):
        context = f"{relative_path}:cases[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{context}: route case must be a mapping")
            continue
        case_id = case.get("id")
        prompt = case.get("prompt")
        expected = case.get("expected")
        if (
            not isinstance(case_id, str)
            or not case_id.strip()
            or not isinstance(prompt, str)
            or not prompt.strip()
            or not isinstance(expected, dict)
        ):
            errors.append(
                f"{context}: route case requires id, prompt, and expected"
            )
            continue
        ids.append(case_id)
        main_execution = case.get("main_execution")
        main_errors = validate_main_assignment(main_execution)
        if main_errors:
            errors.extend(
                f"{context}: {error}"
                for error in main_errors
            )
            continue
        decision = route(
            prompt,
            main_execution=main_execution,
            domain_registry=domain_registry,
        )
        actual = _route_projection(decision)
        if not isinstance(actual, dict):
            errors.append(f"{case_id}: route result must be a mapping")
            continue
        case_errors: list[str] = []
        if actual != expected:
            case_errors.append(
                f"expected route {expected!r}; actual={actual!r}"
            )
        excluded = case.get("excluded_skills", [])
        if not isinstance(excluded, list) or not all(
            isinstance(item, str) and item.strip() for item in excluded
        ):
            case_errors.append(
                "excluded_skills must be a list of non-blank Skill names"
            )
        else:
            selected = {
                actual.get("primary_skill"),
                actual.get("review_skill"),
                *(actual.get("layer3_skills") or []),
            }
            selected_exclusions = sorted(selected & set(excluded))
            if selected_exclusions:
                case_errors.append(
                    "selected excluded Skill(s): "
                    + ", ".join(selected_exclusions)
                )
        if case_errors:
            errors.extend(
                f"{case_id}: {message}" for message in case_errors
            )
            continue
        claims[case_id] = {
            "source": relative_path,
            "expected_professional_owner": actual.get("primary_skill"),
            "expected_layer3_skills": list(
                actual.get("layer3_skills") or []
            ),
        }
    duplicate_ids = sorted(
        {case_id for case_id in ids if ids.count(case_id) > 1}
    )
    if duplicate_ids:
        errors.append(
            f"{relative_path}: route case ids must be unique; "
            f"duplicates={duplicate_ids!r}"
        )
        return {}, errors
    return claims, errors


def _admission_evidence_claims(
    *,
    root: Path,
    passing_ids: set[str],
) -> dict[str, dict[str, object]]:
    """Return owner and selected-Skill claims for validated admissions."""

    path = root / "evals" / "capability-coverage" / "admission-cases.yaml"
    document = load_yaml_file(path)
    claims: dict[str, dict[str, object]] = {}
    for case in document.get("cases", []):
        if not isinstance(case, dict) or case.get("id") not in passing_ids:
            continue
        expected = case.get("expected")
        if not isinstance(expected, dict):
            continue
        selected_skills = (
            [case["skill"]]
            if case.get("layer") in {"domain", "foundation"}
            and expected.get("selected") is True
            and isinstance(case.get("skill"), str)
            else []
        )
        claims[str(case["id"])] = {
            "source": "evals/capability-coverage/admission-cases.yaml",
            "expected_professional_owner": expected.get("primary_skill"),
            "expected_layer3_skills": selected_skills,
        }
    return claims


def _validate_professional_projection(
    entries: Sequence[Mapping[str, object]],
    professional_registry: object,
    *,
    errors: list[str],
) -> None:
    professional = _registry_entries(
        professional_registry,
        "professional_skills",
    )
    for entry in entries:
        status = entry.get("coverage_status")
        owner = entry.get("expected_professional_owner")
        if status not in {"covered", "partial"} or not isinstance(owner, str):
            continue
        context = str(entry.get("id"))
        record = professional.get(owner)
        if record is None:
            errors.append(
                _problem(
                    context,
                    f"{status} Professional owner {owner!r} does not exist",
                )
            )
            continue
        roles = record.get("role_support")
        if not isinstance(roles, list) or not roles:
            errors.append(
                _problem(context, f"Professional owner {owner!r} has no Profile")
            )
        if record.get("task_routable") is not True:
            errors.append(
                _problem(
                    context,
                    f"Professional owner {owner!r} is not task-routable",
                )
            )


def _validate_layer_projection(
    entries: Sequence[Mapping[str, object]],
    professional_registry: object,
    foundation_registry: object,
    domain_registry: object,
    *,
    errors: list[str],
) -> None:
    professional = _registry_entries(
        professional_registry,
        "professional_skills",
    )
    foundations = _registry_entries(foundation_registry, "foundation_skills")
    domains = _registry_entries(domain_registry, "domain_skills")
    for entry in entries:
        status = entry.get("coverage_status")
        if status not in {"covered", "partial"}:
            continue
        context = str(entry.get("id"))
        owner = entry.get("expected_professional_owner")
        owner_record = professional.get(str(owner))
        candidates = (
            set(owner_record.get("layer3_candidates") or [])
            if owner_record is not None
            else set()
        )
        for field, registry, layer_name in (
            ("expected_foundation_skills", foundations, "Foundation"),
            ("expected_domain_extensions", domains, "Domain"),
        ):
            raw = entry.get(field)
            values = raw if isinstance(raw, list) else []
            for skill in values:
                if skill not in registry:
                    errors.append(
                        _problem(
                            context,
                            f"{status} {layer_name} Skill {skill!r} does not exist",
                        )
                    )
                elif owner_record is not None and skill not in candidates:
                    errors.append(
                        _problem(
                            context,
                            f"{layer_name} Skill {skill!r} is not owned by "
                            f"Professional {owner!r}",
                        )
                    )


def _validate_evidence_projection(
    entries: Sequence[Mapping[str, object]],
    *,
    root: Path,
    evidence_ids: Mapping[str, Sequence[str]] | set[str] | None,
    passing_exact_ids: set[str],
    evidence_claims: Mapping[str, Mapping[str, object]],
    errors: list[str],
) -> None:
    known_ids = set(evidence_ids or ())
    try:
        resolved_root = root.resolve(strict=True)
    except OSError as exc:
        errors.append(_problem(str(root), f"cannot resolve evidence root: {exc}"))
        return
    for entry in entries:
        context = str(entry.get("id"))
        status = entry.get("coverage_status")
        evidence = entry.get("evidence_fixtures")
        if not isinstance(evidence, list):
            continue
        exact_ids: list[str] = []
        for item in evidence:
            if not isinstance(item, str):
                continue
            if item.startswith("gap:"):
                if status == "covered":
                    errors.append(
                        _problem(
                            context,
                            "covered entries cannot use non-passing gap evidence",
                        )
                    )
                continue
            looks_like_path = "/" in item or Path(item).suffix in {".yaml", ".json"}
            if looks_like_path:
                if status == "covered":
                    errors.append(
                        _problem(
                            context,
                            "covered entries require exact current passing "
                            "fixture IDs; an existing evidence file path cannot "
                            f"satisfy coverage: {item!r}",
                        )
                    )
                    continue
                relative = Path(item)
                if relative.is_absolute():
                    errors.append(
                        _problem(
                            context,
                            "evidence_fixtures path must be canonical "
                            f"repository-relative: {item!r}",
                        )
                    )
                    continue
                if ".." in relative.parts or "." in relative.parts:
                    errors.append(
                        _problem(
                            context,
                            "evidence_fixtures path must not contain parent or "
                            f"current-directory traversal: {item!r}",
                        )
                    )
                    continue
                if relative.as_posix() != item:
                    errors.append(
                        _problem(
                            context,
                            "evidence_fixtures path must use canonical "
                            f"repository-relative form: {item!r}",
                        )
                    )
                    continue
                candidate = root / relative
                try:
                    resolved = candidate.resolve(strict=True)
                except OSError:
                    errors.append(
                        _problem(
                            context,
                            f"evidence_fixtures references stale path {item!r}",
                        )
                    )
                    continue
                try:
                    resolved.relative_to(resolved_root)
                except ValueError:
                    errors.append(
                        _problem(
                            context,
                            "evidence_fixtures path resolves outside repository "
                            f"root: {item!r}",
                        )
                    )
                    continue
                if not resolved.is_file():
                    errors.append(
                        _problem(
                            context,
                            f"evidence_fixtures path is not a file: {item!r}",
                        )
                    )
                continue
            if item not in known_ids:
                errors.append(
                    _problem(
                        context,
                        f"evidence_fixtures references stale id {item!r}",
                    )
                )
            elif status == "covered":
                exact_ids.append(item)
                if item not in passing_exact_ids:
                    errors.append(
                        _problem(
                            context,
                            f"covered exact evidence fixture {item!r} is not "
                            "passing current behavior",
                        )
                    )
        if status != "covered":
            continue
        if not exact_ids:
            errors.append(
                _problem(
                    context,
                    "covered entries require at least one exact current "
                    "passing fixture ID",
                )
            )
            continue
        owner = entry.get("expected_professional_owner")
        owner_claim_ids = [
            item
            for item in exact_ids
            if item in passing_exact_ids
            and item in evidence_claims
            and evidence_claims[item].get(
                "expected_professional_owner"
            )
            == owner
        ]
        owner_claims = [
            evidence_claims[item] for item in owner_claim_ids
        ]
        if not owner_claims:
            errors.append(
                _problem(
                    context,
                    "covered evidence has no current passing owner/trigger "
                    f"claim for {owner!r}",
                )
            )
        if entry.get("axis") != "routing-combination":
            if owner_claims:
                declared_layer3 = [
                    *(entry.get("expected_domain_extensions") or []),
                    *(entry.get("expected_foundation_skills") or []),
                ]
                selected_layer3 = {
                    skill
                    for claim in owner_claims
                    for skill in (
                        claim.get("expected_layer3_skills") or []
                    )
                    if isinstance(skill, str)
                }
                missing_layer3 = [
                    skill
                    for skill in declared_layer3
                    if skill not in selected_layer3
                ]
                if missing_layer3:
                    claim_summary = [
                        {
                            "fixture": fixture_id,
                            "owner": claim.get(
                                "expected_professional_owner"
                            ),
                            "layer3": list(
                                claim.get("expected_layer3_skills") or []
                            ),
                        }
                        for fixture_id, claim in zip(
                            owner_claim_ids,
                            owner_claims,
                            strict=True,
                        )
                    ]
                    errors.append(
                        _problem(
                            context,
                            "covered evidence owner-bound passing Layer 3 "
                            "union is missing declared Skill(s) "
                            f"{missing_layer3!r}; owner={owner!r}; "
                            f"fixture claims={claim_summary!r}",
                        )
                    )
            continue
        if len(exact_ids) != 1:
            errors.append(
                _problem(
                    context,
                    "covered routing-combination entries require exactly one "
                    "passing fixture ID",
                )
            )
            continue
        claim = evidence_claims.get(exact_ids[0])
        expected_layer3 = [
            *(entry.get("expected_domain_extensions") or []),
            *(entry.get("expected_foundation_skills") or []),
        ]
        if claim is None or (
            claim.get("expected_professional_owner") != owner
            or claim.get("expected_layer3_skills") != expected_layer3
        ):
            errors.append(
                _problem(
                    context,
                    "covered routing-combination evidence must exactly match "
                    "the declared Professional owner and ordered "
                    "Domain/Foundation tuple",
                )
            )


def _validate_route_projection(
    entries: Sequence[Mapping[str, object]],
    route_results: Mapping[str, object],
    *,
    errors: list[str],
) -> None:
    for entry in entries:
        if (
            entry.get("axis") != "routing-combination"
            or entry.get("coverage_status") != "covered"
        ):
            continue
        context = str(entry.get("id"))
        evidence = entry.get("evidence_fixtures")
        evidence_ids = evidence if isinstance(evidence, list) else []
        matching = [
            route_results[item]
            for item in evidence_ids
            if isinstance(item, str) and item in route_results
        ]
        if not matching:
            errors.append(
                _problem(context, "covered route has no current route result")
            )
            continue
        expected_owner = entry.get("expected_professional_owner")
        expected_layer3 = [
            *(entry.get("expected_domain_extensions") or []),
            *(entry.get("expected_foundation_skills") or []),
        ]
        for result in matching:
            if not isinstance(result, dict):
                errors.append(_problem(context, "route result must be a mapping"))
                continue
            actual = result.get("actual")
            if not isinstance(actual, dict):
                errors.append(_problem(context, "route result lacks actual route"))
                continue
            if result.get("passed") is not True:
                errors.append(_problem(context, "covered route evidence is not passing"))
            if actual.get("primary_skill") != expected_owner:
                errors.append(
                    _problem(
                        context,
                        "actual route Professional owner differs from matrix",
                    )
                )
            if actual.get("layer3_skills") != expected_layer3:
                errors.append(
                    _problem(
                        context,
                        "actual route Layer 3 order differs from matrix",
                    )
                )


def validate_capability_coverage(
    matrix_path: Path,
    *,
    root: Path,
    professional_registry: object | None = None,
    foundation_registry: object | None = None,
    domain_registry: object | None = None,
    evidence_ids: Mapping[str, Sequence[str]] | set[str] | None = None,
    passing_evidence_ids: set[str] | None = None,
    route_results: Mapping[str, object] | None = None,
) -> list[str]:
    """Return deterministic, non-writing matrix and projection errors."""

    try:
        data = load_yaml_file(matrix_path)
    except (OSError, ValidationProblem) as exc:
        return [f"YAML parse failure for {matrix_path}: {exc}"]
    context = str(matrix_path)
    errors: list[str] = []
    if not isinstance(data, dict):
        return [_problem(context, "document must be a mapping")]
    if set(data) != TOP_LEVEL_FIELDS:
        errors.append(
            _problem(
                context,
                f"top-level fields must equal {sorted(TOP_LEVEL_FIELDS)!r}; "
                f"found {sorted(data)!r}",
            )
        )
    schema_version = data.get("schema_version")
    if type(schema_version) is not int or schema_version != SCHEMA_VERSION:
        errors.append(
            _problem(context, "schema_version must be the exact integer 1")
        )
    if data.get("kind") != KIND:
        errors.append(_problem(context, f"kind must equal {KIND!r}"))
    raw_entries = data.get("entries")
    if not isinstance(raw_entries, list):
        errors.append(_problem(context, "entries must be a list"))
        return errors
    entries: list[Mapping[str, object]] = []
    for index, raw_entry in enumerate(raw_entries):
        entry = _validate_entry(raw_entry, index=index, errors=errors)
        if entry is not None:
            entries.append(entry)
    ids = [
        entry.get("id")
        for entry in entries
        if isinstance(entry.get("id"), str)
    ]
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    if duplicates:
        errors.append(_problem(context, f"entry ids must be unique: {duplicates!r}"))
    _validate_required_space(
        data.get("required_space"),
        entries,
        context=context,
        errors=errors,
    )

    registry_inputs = (
        (
            professional_registry,
            root / "src" / "registry" / "professional-skills.yaml",
        ),
        (
            foundation_registry,
            root / "src" / "registry" / "foundation-skills.yaml",
        ),
        (
            domain_registry,
            root / "src" / "registry" / "domain-skills.yaml",
        ),
    )
    resolved_registries: list[object | None] = []
    for supplied, path in registry_inputs:
        resolved_registries.append(
            supplied
            if supplied is not None
            else load_yaml_file(path)
            if path.is_file()
            else None
        )
    (
        effective_professional_registry,
        effective_foundation_registry,
        effective_domain_registry,
    ) = resolved_registries

    effective_catalog: dict[str, tuple[str, ...]] | set[str]
    if isinstance(evidence_ids, Mapping):
        effective_catalog = {
            case_id: tuple(locations)
            for case_id, locations in evidence_ids.items()
        }
        canonical_path = root / "evals" / "routing" / "cases.yaml"
        if canonical_path.is_file():
            canonical_source = canonical_path.relative_to(root).as_posix()
            canonical_catalog, canonical_catalog_errors = fixture_ids(
                (canonical_source, load_yaml_file(canonical_path))
            )
            errors.extend(canonical_catalog_errors)
            for case_id, locations in canonical_catalog.items():
                if case_id in effective_catalog:
                    errors.append(
                        f"fixture id {case_id!r} must be globally unique "
                        "across canonical, capability, and admission evidence"
                    )
                else:
                    effective_catalog[case_id] = locations
    else:
        effective_catalog = set(evidence_ids or ())

    referenced_ids = {
        item
        for entry in entries
        for item in (entry.get("evidence_fixtures") or [])
        if isinstance(item, str)
        and not item.startswith("gap:")
        and "/" not in item
        and Path(item).suffix not in {".yaml", ".json"}
    }

    def source_referenced(source: str) -> bool:
        if not isinstance(effective_catalog, Mapping):
            return False
        return any(
            any(
                location.startswith(f"{source}:")
                for location in effective_catalog.get(item, ())
            )
            for item in referenced_ids
        )

    passing_exact_ids = set(passing_evidence_ids or ())
    evidence_claims: dict[str, Mapping[str, object]] = {}
    canonical_source = "evals/routing/cases.yaml"
    if source_referenced(canonical_source):
        canonical_claims, canonical_errors = _evaluate_route_evidence(
            root=root,
            relative_path=canonical_source,
            domain_registry=effective_domain_registry,
        )
        evidence_claims.update(canonical_claims)
        passing_exact_ids.update(canonical_claims)
        errors.extend(canonical_errors)

    capability_source = "evals/routing/capability-coverage-cases.yaml"
    if source_referenced(capability_source):
        if route_results is not None:
            capability_claims = {
                case_id: {
                    "source": capability_source,
                    "expected_professional_owner": result["actual"].get(
                        "primary_skill"
                    ),
                    "expected_layer3_skills": list(
                        result["actual"].get("layer3_skills") or []
                    ),
                }
                for case_id, result in route_results.items()
                if isinstance(case_id, str)
                and isinstance(result, dict)
                and result.get("passed") is True
                and isinstance(result.get("actual"), dict)
            }
            evidence_claims.update(capability_claims)
            passing_exact_ids.update(capability_claims)
        elif passing_evidence_ids is None:
            capability_claims, capability_errors = _evaluate_route_evidence(
                root=root,
                relative_path=capability_source,
                domain_registry=effective_domain_registry,
            )
            evidence_claims.update(capability_claims)
            passing_exact_ids.update(capability_claims)
            errors.extend(capability_errors)

    admission_source = "evals/capability-coverage/admission-cases.yaml"
    if source_referenced(admission_source):
        passing_admission_ids, admission_errors = (
            evaluate_admission_evidence(
                root=root,
                professional_registry=effective_professional_registry,
                foundation_registry=effective_foundation_registry,
                domain_registry=effective_domain_registry,
            )
        )
        passing_exact_ids.update(passing_admission_ids)
        evidence_claims.update(
            _admission_evidence_claims(
                root=root,
                passing_ids=passing_admission_ids,
            )
        )
        errors.extend(admission_errors)

    _validate_evidence_projection(
        entries,
        root=root,
        evidence_ids=effective_catalog,
        passing_exact_ids=passing_exact_ids,
        evidence_claims=evidence_claims,
        errors=errors,
    )
    if effective_professional_registry is not None:
        _validate_professional_projection(
            entries,
            effective_professional_registry,
            errors=errors,
        )
    if (
        effective_professional_registry is not None
        and effective_foundation_registry is not None
        and effective_domain_registry is not None
    ):
        _validate_layer_projection(
            entries,
            effective_professional_registry,
            effective_foundation_registry,
            effective_domain_registry,
            errors=errors,
        )
    if route_results is not None:
        _validate_route_projection(entries, route_results, errors=errors)
    return errors


def fixture_ids(
    *documents: tuple[str, object],
) -> tuple[dict[str, tuple[str, ...]], list[str]]:
    """Return fixture IDs with source locations and deterministic duplicate errors."""

    locations: dict[str, list[str]] = {}
    errors: list[str] = []
    for source, document in documents:
        if not isinstance(document, dict):
            errors.append(f"{source}: fixture document must be a mapping")
            continue
        cases = document.get("cases")
        if not isinstance(cases, list):
            errors.append(f"{source}:cases must be a list")
            continue
        for index, case in enumerate(cases):
            location = f"{source}:cases[{index}]"
            if not isinstance(case, dict):
                errors.append(f"{location}: fixture case must be a mapping")
                continue
            case_id = case.get("id")
            if not isinstance(case_id, str) or not case_id.strip():
                errors.append(f"{location}: fixture id must be a non-blank string")
                continue
            locations.setdefault(case_id.strip(), []).append(location)
    for case_id in sorted(locations):
        found = locations[case_id]
        if len(found) > 1:
            errors.append(
                f"fixture id {case_id!r} must be globally unique; "
                f"found at {', '.join(found)}"
            )
    catalog = {
        case_id: tuple(found)
        for case_id, found in sorted(locations.items())
    }
    return catalog, errors
