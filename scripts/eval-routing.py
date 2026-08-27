#!/usr/bin/env python3
"""Evaluate deterministic hookless task-to-Skill routing fixtures."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

from capability_coverage import fixture_ids, validate_capability_coverage
from deterministic_route_oracle import (
    ALL_DOMAIN_ROUTE_SPECS,
    DOMAIN_ROUTE_SPECS,
    domain_route_family,
    domain_transition_marker,
    domain_unchanged_marker,
    RoutingIntegrityError,
    route as canonical_route,
    route_once_pipeline_errors,
    route_with_trace,
)
from validation_utils import (
    CORE_CONTRACTS,
    ValidationProblem,
    compute_execution_level,
    decision_eval_authority,
    direct_bounded_discovery_outcome,
    fail_many,
    layer3_selector_authority,
    layer3_selector_runtime_projection,
    layer3_selector_runtime_selection,
    layer3_selector_runtime_selection_receipt,
    layer3_selector_runtime_selection_receipt_errors,
    load_yaml_file,
    professional_automatic_routing_policy_fingerprint,
    report_output_paths,
    resolve_evidence_gap,
    validate_main_assignment,
)
from fixture_capsule_contract import (
    engineering_brief_execution_transition_errors,
    engineering_brief_protected_fields,
    project_engineering_brief_task_execution,
)


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "routing" / "cases.yaml"
CAPABILITY_CASES = ROOT / "evals" / "routing" / "capability-coverage-cases.yaml"
DECISION_CASES = ROOT / "evals" / "routing" / "decision-cases.yaml"
CAPABILITY_MATRIX = ROOT / "evals" / "capability-coverage" / "matrix.yaml"
PROFESSIONAL = ROOT / "src" / "registry" / "professional-skills.yaml"
FOUNDATION = ROOT / "src" / "registry" / "foundation-skills.yaml"
DOMAIN = ROOT / "src" / "registry" / "domain-skills.yaml"
REPORT_JSON = ROOT / "reports" / "routing-eval.json"
REPORT_MD = ROOT / "reports" / "routing-eval.md"
DOMAIN_VARIANTS = {"canonical", "paraphrase"}
EVIDENCE_LIMITATIONS = (
    "Deterministic routing fixtures do not measure wall-clock performance.",
    "Fixture agreement does not prove real-host accuracy or the installed user experience.",
    "Prompt matching is a deterministic regression oracle, not a learned or production router.",
)
DECISION_FIELDS = {
    "path_decision",
    "gap_ownership",
    "discovery_decision",
    "professional_layer3_decision",
    "execution_level",
    "action_authority",
    "review_decision",
}
LEVEL_RANK = {f"L{rank}": rank for rank in range(1, 6)}
DECISION_LEVEL_BASIS_FIELDS = {
    "evidence_profile",
    "prior_historical_max_floor",
    "prior_historical_max_effective",
}
DECISION_LEVEL_EVIDENCE_PROFILES = {
    "strict-l1",
    "l2-eligible",
    "l3-default",
    "material-l4",
    "material-l5",
}
def _deep_merge(base: object, overlay: object) -> object:
    """Return a detached recursive mapping merge for compact eval fixtures."""

    if not isinstance(base, dict) or not isinstance(overlay, dict):
        return copy.deepcopy(overlay)
    merged = copy.deepcopy(base)
    for key, value in overlay.items():
        merged[key] = (
            _deep_merge(merged[key], value)
            if key in merged
            else copy.deepcopy(value)
        )
    return merged


def decision_case_baseline(
    document: dict[str, Any],
    case: dict[str, Any],
) -> dict[str, Any]:
    """Project one case's compact override onto the fixture defaults."""

    merged = _deep_merge(document.get("defaults"), case.get("decision"))
    return merged if isinstance(merged, dict) else {}


def _decision_schema_invalid(decision: object) -> bool:
    if not isinstance(decision, dict) or set(decision) != DECISION_FIELDS:
        return True
    exact_fields = {
        "path_decision": {"path"},
        "gap_ownership": {"kind", "resolution"},
        "discovery_decision": {"mode", "boundary", "after_invalidation"},
        "professional_layer3_decision": {
            "primary_skill",
            "implementation_layer3",
            "domain",
            "required_layer3",
            "context_overflow",
            "route_fingerprint",
            "rerouted_after_level_confirmation",
        },
        "execution_level": {
            "requested_level",
            "requested_or_automatic",
            "automatic_level",
            "minimum_eligible_level",
            "mandatory_risk_floor",
            "historical_max",
            "effective_level",
            "l5_basis",
            "l5_confirmation",
            "computation_basis",
        },
        "action_authority": {"outcome"},
        "review_decision": {
            "review_skill",
            "review_layer3",
            "selection_basis",
            "selection_provenance",
        },
    }
    if any(
        not isinstance(decision[field], dict)
        or set(decision[field]) != fields
        for field, fields in exact_fields.items()
    ):
        return True
    path = decision["path_decision"]
    gap = decision["gap_ownership"]
    discovery = decision["discovery_decision"]
    professional = decision["professional_layer3_decision"]
    level = decision["execution_level"]
    action = decision["action_authority"]
    review = decision["review_decision"]
    scalar_checks = (
        path["path"] in {"direct", "analyzed"},
        gap["kind"]
        in {"repo-resolvable-fact", "user-owned-choice", "route-or-material-unknown"},
        gap["resolution"]
        in {"source", "discovery", "ask-user", "analysis", "fail-closed"},
        discovery["mode"] in {"none", "direct-bounded"},
        discovery["boundary"]
        in {"not-applicable", "confirmed", "invalidated"},
        discovery["after_invalidation"]
        in {"not-applicable", "return-main", "continue-edit"},
        isinstance(professional["primary_skill"], str)
        and bool(professional["primary_skill"]),
        isinstance(professional["context_overflow"], bool),
        isinstance(professional["route_fingerprint"], str)
        and bool(professional["route_fingerprint"]),
        isinstance(professional["rerouted_after_level_confirmation"], bool),
        isinstance(level["requested_level"], str)
        and bool(level["requested_level"]),
        level["requested_or_automatic"] in LEVEL_RANK,
        level["automatic_level"] in LEVEL_RANK,
        all(level[field] in LEVEL_RANK for field in (
            "minimum_eligible_level",
            "mandatory_risk_floor",
            "historical_max",
            "effective_level",
        )),
        level["l5_basis"]
        in {"none", "keyword-only", "analysis-handoff", "user-explicit"},
        level["l5_confirmation"]
        in {"not-required", "pending", "confirmed", "rejected"},
        action["outcome"] in {"execute", "ask", "block"},
        isinstance(review["review_skill"], str) and bool(review["review_skill"]),
        review["selection_basis"]
        in {"independent-review-risk", "copied-implementation"},
        review["selection_provenance"]
        in {"review-risk-selector", "implementation-layer3-copy"},
    )
    if not all(scalar_checks):
        return True
    for field in ("implementation_layer3", "domain", "required_layer3"):
        values = professional[field]
        if not isinstance(values, list) or any(
            not isinstance(item, str) or not item for item in values
        ):
            return True
    review_values = review["review_layer3"]
    return not isinstance(review_values, list) or any(
        not isinstance(item, str) or not item for item in review_values
    )


def _decision_selector_authority() -> dict[str, Any]:
    """Return the current registry-backed selector authority for Decision Eval."""

    return layer3_selector_authority(
        load_yaml_file(FOUNDATION),
        load_yaml_file(PROFESSIONAL),
        load_yaml_file(DOMAIN),
        context="Decision Eval selector authority",
    )


def _decision_level_derivation(
    level: object,
) -> tuple[dict[str, object] | None, list[str]]:
    """Recompute one compact Decision Level through the canonical Core owner."""

    if not isinstance(level, dict):
        return None, ["execution Level decision must be a mapping"]
    basis = level.get("computation_basis")
    if not isinstance(basis, dict) or set(basis) != DECISION_LEVEL_BASIS_FIELDS:
        return None, ["execution Level computation basis is missing or malformed"]
    profile = basis.get("evidence_profile")
    prior_floor = basis.get("prior_historical_max_floor")
    prior_effective = basis.get("prior_historical_max_effective")
    if profile not in DECISION_LEVEL_EVIDENCE_PROFILES:
        return None, ["execution Level evidence profile is invalid"]
    if prior_floor not in LEVEL_RANK or prior_effective not in LEVEL_RANK:
        return None, ["execution Level historical basis is invalid"]
    try:
        result = _compute_decision_level(
            str(level.get("requested_level")),
            evidence_profile=str(profile),
            confirmation=str(level.get("l5_confirmation")),
            prior_historical_max_floor=str(prior_floor),
            prior_historical_max_effective=str(prior_effective),
        )
    except ValueError as exc:
        return None, [str(exc)]
    expected = {
        "requested_level": result["requested"],
        "requested_or_automatic": result["requested_or_automatic"],
        "automatic_level": result["automatic_level"],
        "minimum_eligible_level": result["minimum_eligible_level"],
        "mandatory_risk_floor": result["mandatory_floor"],
        "historical_max": prior_effective,
        "effective_level": result["effective_level"],
        "l5_confirmation": result["l5_confirmation"],
    }
    errors = [
        f"execution Level {field} does not match compute_execution_level"
        for field, value in expected.items()
        if level.get(field) != value
    ]
    expected_basis = (
        "user-explicit"
        if result["requested"] == "L5"
        else (
            "analysis-handoff"
            if result["assurance_recommendation"] == "L5"
            and result["l5_confirmation"] == "confirmed"
            else (
                "keyword-only"
                if profile == "material-l4"
                else "none"
            )
        )
    )
    if level.get("l5_basis") != expected_basis:
        errors.append("execution Level L5 basis does not match canonical evidence")
    return result, errors


def decision_baseline_failure_ids(decision: object) -> list[str]:
    """Reject noncanonical Decision baselines before applying a mutant."""

    if _decision_schema_invalid(decision):
        return ["decision-eval-schema-invalid"]
    assert isinstance(decision, dict)
    professional = decision["professional_layer3_decision"]
    review = decision["review_decision"]
    execution = decision["execution_level"]
    failures: list[str] = []

    _computed_level, derivation_errors = _decision_level_derivation(execution)
    if derivation_errors:
        if any("basis" in error for error in derivation_errors):
            failures.append("decision-baseline-execution-basis-invalid")
        else:
            failures.append("decision-baseline-execution-derivation-invalid")

    if execution["requested_level"] not in CORE_CONTRACTS[
        "execution_level_contract"
    ]["requested_values"]:
        failures.append("decision-baseline-requested-level-invalid")

    professional_data = load_yaml_file(PROFESSIONAL)
    foundation_data = load_yaml_file(FOUNDATION)
    domain_data = load_yaml_file(DOMAIN)
    professional_rows = {
        row.get("name"): row
        for row in professional_data.get("professional_skills", [])
        if isinstance(row, dict)
    }
    foundation_rows = {
        row.get("name"): row
        for row in foundation_data.get("foundation_skills", [])
        if isinstance(row, dict)
    }
    domain_rows = {
        row.get("name"): row
        for row in domain_data.get("domain_skills", [])
        if isinstance(row, dict)
    }
    layer3_rows = {**foundation_rows, **domain_rows}
    profile = (
        "analysis-agent"
        if decision["path_decision"]["path"] == "analyzed"
        else "task-agent"
    )
    primary = professional_rows.get(professional["primary_skill"])
    if (
        not isinstance(primary, dict)
        or primary.get("task_routable") is not True
        or profile not in primary.get("role_support", [])
    ):
        failures.append("decision-baseline-primary-role-invalid")
    review_skill = professional_rows.get(review["review_skill"])
    if (
        not isinstance(review_skill, dict)
        or review_skill.get("task_routable") is not True
        or "review-agent" not in review_skill.get("role_support", [])
    ):
        failures.append("decision-baseline-review-role-invalid")

    implementation = professional["implementation_layer3"]
    domains = professional["domain"]
    required = professional["required_layer3"]
    layer3_lists = [implementation, domains, required, review["review_layer3"]]
    if any(
        not 0 <= len(values) <= 3 or len(values) != len(set(values))
        for values in layer3_lists
    ):
        failures.append("decision-layer3-cardinality-invalid")
    if required != [*domains, *implementation]:
        failures.append("decision-baseline-required-layer3-mismatch")

    if isinstance(primary, dict):
        candidates = set(primary.get("layer3_candidates", []))
        if any(
            item not in foundation_rows
            or item not in candidates
            or profile not in foundation_rows[item].get("role_support", [])
            for item in implementation
        ):
            failures.append(
                "decision-baseline-implementation-layer3-unauthorized"
            )
        if any(
            item not in domain_rows
            or item not in candidates
            or profile not in domain_rows[item].get("role_support", [])
            for item in domains
        ):
            failures.append("decision-baseline-domain-nonreciprocal")
    if isinstance(review_skill, dict):
        review_candidates = set(review_skill.get("layer3_candidates", []))
        if any(
            item not in layer3_rows
            or item not in review_candidates
            or "review-agent"
            not in layer3_rows[item].get("role_support", [])
            for item in review["review_layer3"]
        ):
            failures.append("decision-baseline-review-layer3-unauthorized")

    try:
        selector_authority = _decision_selector_authority()
        layer3_selector_runtime_projection(
            selector_authority,
            professional_skill=professional["primary_skill"],
            profile=profile,
            selection_owner="main-control-agent",
            exact_layer3=[*domains, *implementation],
        )
    except (ValidationProblem, ValueError):
        if "decision-baseline-primary-role-invalid" not in failures:
            failures.append(
                "decision-baseline-implementation-layer3-unauthorized"
            )
    try:
        selector_authority = _decision_selector_authority()
        layer3_selector_runtime_projection(
            selector_authority,
            professional_skill=review["review_skill"],
            profile="review-agent",
            selection_owner="main-control-agent",
            exact_layer3=review["review_layer3"],
        )
    except (ValidationProblem, ValueError):
        if "decision-baseline-review-role-invalid" not in failures:
            failures.append("decision-baseline-review-layer3-unauthorized")

    gap = decision["gap_ownership"]
    discovery = decision["discovery_decision"]
    action = decision["action_authority"]["outcome"]
    action_valid = True
    if discovery["mode"] == "direct-bounded" and discovery["boundary"] == "invalidated":
        actual = direct_bounded_discovery_outcome(
            "route-or-risk-invalidated"
        )
        action_valid = (
            action == "block"
            and discovery["after_invalidation"] == "return-main"
            and actual["may_edit"] is False
            and actual["return_to_main"] is True
        )
    elif gap["kind"] == "user-owned-choice":
        actual = resolve_evidence_gap(
            "user-owned-choice", choice_kind="semantic-choice"
        )
        action_valid = (
            gap["resolution"] == actual["resolution"]
            and action == actual["action_authority"]
        )
    elif gap["kind"] == "route-or-material-unknown":
        actual = resolve_evidence_gap("route-or-material-unknown")
        action_valid = (
            decision["path_decision"]["path"] == actual["path"]
            and gap["resolution"] in {"analysis", actual["resolution"]}
            and action == actual["action_authority"]
        )
    else:
        action_valid = (
            decision["path_decision"]["path"] == "direct"
            and gap["resolution"] in {"source", "discovery"}
            and action == "execute"
        )
    if not action_valid:
        failures.append("decision-baseline-action-authority-invalid")
    return list(dict.fromkeys(failures))


def decision_state_failure_ids(decision: object) -> list[str]:
    """Return stable invariant failures for one seven-axis decision state."""

    if _decision_schema_invalid(decision):
        return ["decision-eval-schema-invalid"]
    assert isinstance(decision, dict)
    gap = decision["gap_ownership"]
    discovery = decision["discovery_decision"]
    professional = decision["professional_layer3_decision"]
    level = decision["execution_level"]
    action = decision["action_authority"]
    review = decision["review_decision"]
    failures: list[str] = []
    layer3_lists = [
        professional["implementation_layer3"],
        professional["domain"],
        professional["required_layer3"],
        review["review_layer3"],
    ]
    if any(
        not 0 <= len(values) <= 3 or len(values) != len(set(values))
        for values in layer3_lists
    ):
        failures.append("decision-layer3-cardinality-invalid")
    if gap["kind"] == "repo-resolvable-fact" and (
        gap["resolution"] == "ask-user" or action["outcome"] == "ask"
    ):
        failures.append("decision-source-fact-not-user-question")
    if gap["kind"] == "user-owned-choice" and (
        gap["resolution"] != "ask-user" or action["outcome"] != "ask"
    ):
        failures.append("decision-user-choice-not-source-inference")
    if (
        gap["kind"] == "route-or-material-unknown"
        and decision["path_decision"]["path"] == "direct"
    ):
        failures.append("decision-material-unknown-not-direct")
    if discovery["boundary"] == "invalidated" and (
        discovery["after_invalidation"] != "return-main"
        or action["outcome"] != "block"
    ):
        failures.append("decision-discovery-invalidated-stop-before-edit")
    floor = max(
        LEVEL_RANK[level["minimum_eligible_level"]],
        LEVEL_RANK[level["mandatory_risk_floor"]],
        LEVEL_RANK[level["historical_max"]],
        LEVEL_RANK.get(level["requested_level"], 0),
    )
    if LEVEL_RANK[level["effective_level"]] < floor:
        failures.append("decision-level-no-unsupported-downgrade")
    if level["effective_level"] == "L5" and not (
        level["l5_basis"] == "user-explicit"
        or (
            level["l5_basis"] == "analysis-handoff"
            and level["l5_confirmation"] == "confirmed"
        )
    ):
        failures.append("decision-level-l5-not-keyword-only")
    if (
        level["l5_confirmation"] == "confirmed"
        and professional["rerouted_after_level_confirmation"] is True
    ):
        failures.append("decision-level-confirmation-route-invariant")
    if (
        professional["context_overflow"] is True
        and [
            *professional["domain"],
            *professional["implementation_layer3"],
        ]
        != professional["required_layer3"]
    ):
        failures.append("decision-context-preserve-required-layer3")
    _computed_level, derivation_errors = _decision_level_derivation(level)
    if derivation_errors and not {
        "decision-level-no-unsupported-downgrade",
        "decision-level-l5-not-keyword-only",
    } & set(failures):
        failures.append("decision-level-computation-invalid")
    return failures


def _apply_decision_mutation(
    baseline: dict[str, Any], mutation: object
) -> dict[str, Any] | None:
    if not isinstance(mutation, dict) or set(mutation) != {"pointer", "value"}:
        return None
    pointer = mutation["pointer"]
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        return None
    parts = pointer[1:].split("/")
    if len(parts) != 2 or any(not part for part in parts):
        return None
    mutated = copy.deepcopy(baseline)
    owner = mutated.get(parts[0])
    if not isinstance(owner, dict) or parts[1] not in owner:
        return None
    owner[parts[1]] = copy.deepcopy(mutation["value"])
    return mutated


def _execution_evidence(
    *,
    evidence_profile: str,
) -> tuple[
    dict[str, dict[str, object]],
    dict[str, dict[str, object]],
    dict[str, dict[str, object]],
    dict[str, dict[str, object]],
]:
    """Build complete source-backed Core evidence for eval-only Level calls."""

    if evidence_profile not in DECISION_LEVEL_EVIDENCE_PROFILES:
        raise ValueError(f"unknown Decision Level evidence profile {evidence_profile!r}")

    contract = CORE_CONTRACTS["execution_level_contract"]
    source = "analysis_handoff"
    material_trigger = "public-api-event-schema-compatibility"
    material_l4 = evidence_profile in {"material-l4", "material-l5"}
    l1_true = evidence_profile == "strict-l1"
    l2_true = evidence_profile in {"strict-l1", "l2-eligible"}
    l5_true = evidence_profile == "material-l5"
    triggers: dict[str, dict[str, object]] = {}
    for row in contract["trigger_registry"]:
        identifier = row["id"]
        evaluation: dict[str, object] = {
            "status": (
                "matched"
                if material_l4 and identifier == material_trigger
                else "not_matched"
            ),
            "evidence_kind": source,
            "source_anchor": f"decision-eval:{identifier}",
            "plausible_critical": False,
        }
        if material_l4 and identifier == material_trigger:
            evaluation["material_assessment"] = {
                field: f"decision-eval:{identifier}:{field}"
                for field in contract["material_assessment_fields"]
            }
        triggers[identifier] = evaluation
    l2 = {
        row["id"]: {
            "status": "true" if l2_true else "false",
            "evidence_kind": source,
            "source_anchor": f"decision-eval:{row['id']}",
        }
        for row in contract["l2_eligibility"]
    }
    l1 = {
        row["id"]: {
            "status": "true" if l1_true else "false",
            "evidence_kind": source,
            "source_anchor": f"decision-eval:{row['id']}",
        }
        for row in contract["l1_eligibility"]
    }
    l5 = {
        row["id"]: {
            "status": "true" if l5_true else "false",
            "evidence_kind": source,
            "source_anchor": f"decision-eval:{row['id']}",
        }
        for row in contract["l5_assurance_eligibility"]
    }
    return triggers, l1, l2, l5


def _compute_decision_level(
    requested: str,
    *,
    evidence_profile: str = "strict-l1",
    confirmation: str = "not-required",
    prior_historical_max_floor: str | None = None,
    prior_historical_max_effective: str | None = None,
) -> dict[str, object]:
    triggers, l1, l2, l5 = _execution_evidence(
        evidence_profile=evidence_profile
    )
    return compute_execution_level(
        requested=requested,
        trigger_evaluations=triggers,
        l1_evaluations=l1,
        l2_evaluations=l2,
        l5_assurance_evaluations=l5,
        l5_confirmation=confirmation,
        prior_historical_max_floor=prior_historical_max_floor,
        prior_historical_max_effective=prior_historical_max_effective,
    )


def _main_execution_from_level(
    result: dict[str, object],
    *,
    task_id: str,
) -> dict[str, object]:
    return {
        "producer": "main-control-agent",
        "task_id": task_id,
        "execution_level": result["effective_level"],
        "level_basis": result["level_basis"],
    }


def _route_fixed_fields(route_decision: dict[str, Any]) -> dict[str, object]:
    result = route_decision["route_result"]
    domain_names = {
        row["name"]
        for row in load_yaml_file(DOMAIN).get("domain_skills", [])
        if isinstance(row, dict) and isinstance(row.get("name"), str)
    }
    return {
        "primary_professional_skill": result["primary_skill"],
        "implementation_layer3": [
            item for item in result["layer3_skills"] if item not in domain_names
        ],
        "domain": [
            item for item in result["layer3_skills"] if item in domain_names
        ],
        "required_review_skills": [result["review_skill"]],
    }


def _evaluate_level_invariance(
    invariance: object,
) -> tuple[dict[str, Any], list[str]]:
    """Run one semantic route through real Level and route consumers six times."""

    errors: list[str] = []
    expected_fields = {"requested_levels", "semantic_route"}
    if not isinstance(invariance, dict) or set(invariance) != expected_fields:
        return {}, [
            "Decision Eval level_invariance must contain requested_levels and semantic_route"
        ]
    requested_levels = invariance["requested_levels"]
    expected_levels = CORE_CONTRACTS["execution_level_contract"][
        "routing_invariance"
    ]["requested_levels"]
    if requested_levels != expected_levels:
        errors.append(
            "Decision Eval level invariance must cover current Core requested values exactly"
        )
        requested_levels = []
    semantic_route = invariance["semantic_route"]
    semantic_fields = {
        "task_id",
        "prompt",
        "review_layer3",
        "brief_semantics",
    }
    if (
        not isinstance(semantic_route, dict)
        or set(semantic_route) != semantic_fields
        or not isinstance(semantic_route.get("task_id"), str)
        or not semantic_route.get("task_id", "").strip()
        or not isinstance(semantic_route.get("prompt"), str)
        or not semantic_route.get("prompt", "").strip()
        or not isinstance(semantic_route.get("review_layer3"), list)
        or not isinstance(semantic_route.get("brief_semantics"), dict)
        or tuple(semantic_route.get("brief_semantics", {}))
        != engineering_brief_protected_fields()
    ):
        errors.append("Decision Eval semantic_route is malformed")
        return {}, errors

    selector_authority = _decision_selector_authority()
    projections: list[dict[str, Any]] = []
    baseline_route: dict[str, object] | None = None
    for requested in requested_levels:
        try:
            level = _compute_decision_level(requested)
            route_decision = canonical_route(
                semantic_route["prompt"],
                main_execution=_main_execution_from_level(
                    level, task_id=semantic_route["task_id"]
                ),
            )
            fixed_route = _route_fixed_fields(route_decision)
            layer3_selector_runtime_projection(
                selector_authority,
                professional_skill=str(
                    fixed_route["primary_professional_skill"]
                ),
                profile=route_decision["route_result"]["start_profile"],
                selection_owner="main-control-agent",
                exact_layer3=[
                    *fixed_route["domain"],
                    *fixed_route["implementation_layer3"],
                ],
            )
            review_skill = fixed_route["required_review_skills"][0]
            review_projection = layer3_selector_runtime_projection(
                selector_authority,
                professional_skill=str(review_skill),
                profile="review-agent",
                selection_owner="main-control-agent",
                exact_layer3=semantic_route["review_layer3"],
            )
        except (RoutingIntegrityError, ValidationProblem, ValueError) as exc:
            errors.append(
                f"Decision Eval canonical route failed for {requested}: {exc}"
            )
            continue
        if baseline_route is None:
            baseline_route = fixed_route
        elif fixed_route != baseline_route:
            errors.append(
                "Decision Eval requested Level changed a canonical expertise route field"
            )
        projections.append(
            {
                "requested_level": requested,
                "effective_level": level["effective_level"],
                "fixed_route": fixed_route,
                "route_once": route_decision["route_once"],
                "review_selection_basis": review_projection[
                    "selection_basis"
                ],
            }
        )
    return {
        "requested_levels": list(requested_levels),
        "canonical_route_invocation_count": len(projections),
        "fixed_route_equal": not errors and len(projections) == 6,
        "projections": projections,
        "semantic_route": copy.deepcopy(semantic_route),
    }, errors


def _evaluate_l5_confirmation(
    semantic_route: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """Run automatic L5 confirmation through Level, extension, route, and selector consumers."""

    errors: list[str] = []
    results: dict[str, dict[str, object]] = {}
    public_projections: dict[str, dict[str, object]] = {}
    routes: dict[str, dict[str, object]] = {}
    selector_views: dict[str, dict[str, object]] = {}
    authority = _decision_selector_authority()
    for state in ("pending", "confirmed", "rejected"):
        try:
            result = _compute_decision_level(
                "unspecified",
                evidence_profile="material-l5",
                confirmation=state,
                prior_historical_max_floor="L4",
                prior_historical_max_effective="L4",
            )
            results[state] = result
            public_projections[state] = project_engineering_brief_task_execution(
                semantic_route["brief_semantics"], result
            )
            if state == "pending":
                continue
            route_decision = canonical_route(
                semantic_route["prompt"],
                main_execution=_main_execution_from_level(
                    result, task_id=semantic_route["task_id"]
                ),
            )
            routes[state] = _route_fixed_fields(route_decision)
            fixed = routes[state]
            selector_views[state] = {
                "implementation": layer3_selector_runtime_projection(
                    authority,
                    professional_skill=str(
                        fixed["primary_professional_skill"]
                    ),
                    profile=route_decision["route_result"]["start_profile"],
                    selection_owner="main-control-agent",
                    exact_layer3=[
                        *fixed["domain"], *fixed["implementation_layer3"]
                    ],
                ),
                "review": layer3_selector_runtime_projection(
                    authority,
                    professional_skill=str(
                        fixed["required_review_skills"][0]
                    ),
                    profile="review-agent",
                    selection_owner="main-control-agent",
                    exact_layer3=semantic_route["review_layer3"],
                ),
            }
        except (RoutingIntegrityError, ValidationProblem, ValueError) as exc:
            errors.append(f"Decision Eval L5 {state} consumer failed: {exc}")
    route_preserved = (
        set(routes) == {"confirmed", "rejected"}
        and routes["confirmed"] == routes["rejected"]
    )
    selector_preserved = (
        set(selector_views) == {"confirmed", "rejected"}
        and selector_views["confirmed"] == selector_views["rejected"]
    )
    changed_fields: dict[str, list[str]] = {}
    transition_errors: dict[str, list[str]] = {}
    pending_projection = public_projections.get("pending", {})
    for state in ("confirmed", "rejected"):
        projection = public_projections.get(state, {})
        changed_fields[f"pending-to-{state}"] = [
            field
            for field in pending_projection
            if pending_projection.get(field) != projection.get(field)
        ]
        transition_errors[f"pending-to-{state}"] = (
            engineering_brief_execution_transition_errors(
                pending_projection,
                projection,
            )
        )
    all_protected_fields_preserved = (
        set(public_projections) == {"pending", "confirmed", "rejected"}
        and all(
            all(
                public_projections[state]
                .get("brief_semantics", {})
                .get(field)
                == semantic_route["brief_semantics"].get(field)
                for field in engineering_brief_protected_fields()
            )
            for state in public_projections
        )
    )
    if not route_preserved:
        errors.append("Decision Eval L5 confirmation changed route fields")
    if not selector_preserved:
        errors.append("Decision Eval L5 confirmation changed selector fields")
    if any(
        value.get("execution_level_extension", {}).get("version")
        != "execution-level/v2"
        for value in public_projections.values()
    ):
        errors.append("Decision Eval L5 confirmation did not use execution-level/v2")
    if not all_protected_fields_preserved:
        errors.append("Decision Eval L5 confirmation changed protected Brief fields")
    if any(transition_errors.values()):
        errors.append(
            "Decision Eval L5 confirmation violated the source-owned Brief transition contract"
        )
    if any(
        fields != ["execution_level_extension"]
        for fields in changed_fields.values()
    ):
        errors.append(
            "Decision Eval L5 confirmation changed fields outside execution_level_extension"
        )
    return {
        "consumer": "fixture_capsule_contract:engineering-brief-task-projection/v1",
        "protected_fields": list(engineering_brief_protected_fields()),
        "public_projection_count": len(public_projections),
        "changed_fields_by_transition": changed_fields,
        "transition_errors": transition_errors,
        "all_protected_fields_preserved": all_protected_fields_preserved,
        "pending_action": results.get("pending", {}).get(
            "confirmation_action"
        ),
        "confirmed_effective": results.get("confirmed", {}).get(
            "effective_level"
        ),
        "rejected_effective": results.get("rejected", {}).get(
            "effective_level"
        ),
        "execution_extension_versions": {
            state: value.get("execution_level_extension", {}).get("version")
            for state, value in public_projections.items()
        },
        "route_preserved": route_preserved,
        "selector_preserved": selector_preserved,
        "brief_semantics_preserved": all_protected_fields_preserved,
    }, errors


def _evaluate_review_copy(
    document: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    cases = document.get("cases", [])
    case = next(
        (
            item
            for item in cases
            if isinstance(item, dict)
            and item.get("id") == "review-copies-implementation-layer3"
        ),
        None,
    )
    if not isinstance(case, dict):
        return {}, ["Decision Eval review-copy case is missing"]
    baseline = decision_case_baseline(document, case)
    baseline_failures = [
        *decision_baseline_failure_ids(baseline),
        *decision_state_failure_ids(baseline),
    ]
    if baseline_failures:
        return {
            "baseline_failure_ids": list(dict.fromkeys(baseline_failures)),
            "mutant_evaluated": False,
        }, ["Decision Eval review-copy baseline is invalid"]
    mutant = _apply_decision_mutation(baseline, case.get("mutation"))
    if mutant is None:
        return {}, ["Decision Eval review-copy mutation is malformed"]
    authority = _decision_selector_authority()
    selector_id = "dynamic-foundation:regression-testing"

    def select_with_receipt(
        *, professional_skill: str, profile: str
    ) -> dict[str, Any]:
        projection = layer3_selector_runtime_projection(
            authority,
            professional_skill=professional_skill,
            profile=profile,
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        record = next(
            row
            for row in projection["selectors"]
            if row.get("selector_id") == selector_id
        )
        signals = [group[0] for group in record["positive_signal_groups"]]
        return layer3_selector_runtime_selection_receipt(
            projection,
            evidence_signals=signals,
        )

    try:
        implementation_receipt = select_with_receipt(
            professional_skill=baseline["professional_layer3_decision"][
                "primary_skill"
            ],
            profile="task-agent",
        )
        review_receipt = select_with_receipt(
            professional_skill=baseline["review_decision"]["review_skill"],
            profile="review-agent",
        )
    except (ValidationProblem, ValueError, StopIteration) as exc:
        return {
            "baseline_failure_ids": ["decision-review-layer3-independent"],
            "mutant_failure_ids": [],
            "mutant_evaluated": False,
            "selection_call_count": 0,
        }, [f"Decision Eval Review receipt selection failed: {exc}"]

    implementation_errors = layer3_selector_runtime_selection_receipt_errors(
        implementation_receipt,
        expected_owner="main-control-agent",
        expected_profile="task-agent",
        expected_professional=baseline["professional_layer3_decision"][
            "primary_skill"
        ],
        expected_selection_kind="implementation-risk",
        expected_selected_layer3=baseline["professional_layer3_decision"][
            "implementation_layer3"
        ],
    )
    review_errors = layer3_selector_runtime_selection_receipt_errors(
        review_receipt,
        expected_owner="main-control-agent",
        expected_profile="review-agent",
        expected_professional=baseline["review_decision"]["review_skill"],
        expected_selection_kind="review-risk",
        expected_selected_layer3=baseline["review_decision"]["review_layer3"],
    )
    receipts_distinct = (
        implementation_receipt["receipt_sha256"]
        != review_receipt["receipt_sha256"]
    )
    baseline_receipt_errors = [*implementation_errors, *review_errors]
    if not receipts_distinct:
        baseline_receipt_errors.append(
            "implementation and Review selector receipts must be distinct"
        )
    if baseline_receipt_errors:
        errors.append(
            "Decision Eval Review baseline receipt binding failed: "
            + "; ".join(baseline_receipt_errors)
        )

    copied_review_assignment = {
        "review_layer3": list(implementation_receipt["selected_layer3"]),
        "selection_receipt": copy.deepcopy(implementation_receipt),
    }
    mutant_receipt_errors = layer3_selector_runtime_selection_receipt_errors(
        copied_review_assignment["selection_receipt"],
        expected_owner="main-control-agent",
        expected_profile="review-agent",
        expected_professional=baseline["review_decision"]["review_skill"],
        expected_selection_kind="review-risk",
        expected_selected_layer3=copied_review_assignment["review_layer3"],
    )
    mutant_failure_ids = (
        ["decision-review-layer3-independent"]
        if mutant_receipt_errors
        else []
    )
    if mutant_failure_ids != ["decision-review-layer3-independent"]:
        errors.append("Decision Eval copied Review receipt was accepted")
    return {
        "baseline_failure_ids": (
            ["decision-review-layer3-independent"]
            if baseline_receipt_errors
            else []
        ),
        "implementation_layer3": baseline[
            "professional_layer3_decision"
        ]["implementation_layer3"],
        "baseline_review_layer3": review_receipt["selected_layer3"],
        "mutant_review_layer3": copied_review_assignment["review_layer3"],
        "implementation_selection_receipt": implementation_receipt,
        "review_selection_receipt": review_receipt,
        "baseline_receipt_errors": baseline_receipt_errors,
        "mutant_receipt_errors": mutant_receipt_errors,
        "receipts_distinct": receipts_distinct,
        "fixture_labels_consulted": False,
        "selection_call_count": 2,
        "mutant_failure_ids": mutant_failure_ids,
        "mutant_evaluated": True,
    }, errors


def _load_context_pressure_consumer() -> Any:
    path = ROOT / "scripts" / "eval-rendered-context-budget.py"
    name = "decision_eval_context_pressure_consumer"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError("cannot load rendered context pressure consumer")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _evaluate_token_pressure(
    fixed_route: dict[str, object],
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    consumer = _load_context_pressure_consumer()
    obligations = {
        "primary_professional_skill": fixed_route[
            "primary_professional_skill"
        ],
        "implementation_layer3": copy.deepcopy(
            fixed_route["implementation_layer3"]
        ),
        "domain": copy.deepcopy(fixed_route["domain"]),
        "required_review_skills": copy.deepcopy(
            fixed_route["required_review_skills"]
        ),
    }
    budget = consumer.CONTEXT_BUDGET_LIMITS["task"]["hard_ceiling"]
    components = [
        consumer._component(
            "route-obligations",
            "decision-eval/route-obligations.json",
            json.dumps(obligations, sort_keys=True),
        ),
        consumer._component(
            "pressure",
            "decision-eval/token-pressure.txt",
            "overflow-pressure-evidence " * (budget * 2),
        ),
    ]
    measurement = consumer.evaluate_route_obligation_context(
        components,
        required_route_obligations=obligations,
        budget_class="task",
    )
    preserved = measurement["route_obligations_preserved"]
    overflow = measurement["within_hard_ceiling"] is False
    if not overflow:
        errors.append("Decision Eval token pressure did not exceed the real budget")
    if not preserved:
        errors.append("Decision Eval token pressure changed route obligations")
    return {
        "consumer": (
            "eval-rendered-context-budget:evaluate_route_obligation_context"
        ),
        "hard_ceiling": measurement["hard_ceiling"],
        "total_tokens": measurement["total_tokens"],
        "overflow_observed": overflow,
        "failure_id": measurement["failure_id"],
        "outcome": measurement["outcome"],
        "continue_allowed": measurement["continue_allowed"],
        "route_obligations_preserved": preserved,
        "route_obligations": obligations,
        "required_route_obligations": measurement[
            "required_route_obligations"
        ],
        "observed_route_obligations": measurement[
            "observed_route_obligations"
        ],
    }, errors


def _evaluate_review_domain_consumers(
    cases: object,
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    expected_fields = {
        "id",
        "review_skill",
        "domain",
        "positive_signals",
        "nearest_negative_signal",
        "background_signals",
    }
    expected_pairs = {
        ("ai-code-review-refactor", "web3-product-extension"),
        ("ai-code-review-refactor", "low-level-systems-extension"),
        ("quality-test-gate", "bigdata-product-extension"),
    }
    if not isinstance(cases, list) or len(cases) != 3:
        return {}, ["Decision Eval must bind exactly three Review Domain cases"]
    observed_pairs = {
        (item.get("review_skill"), item.get("domain"))
        for item in cases
        if isinstance(item, dict)
    }
    if observed_pairs != expected_pairs:
        errors.append("Decision Eval Review Domain pairs differ from R1-03 authority")
    authority = _decision_selector_authority()
    outcomes: list[dict[str, object]] = []
    for index, case in enumerate(cases):
        if not isinstance(case, dict) or set(case) != expected_fields:
            errors.append(f"Decision Eval Review Domain case {index} is malformed")
            continue
        try:
            projection = layer3_selector_runtime_projection(
                authority,
                professional_skill=case["review_skill"],
                profile="review-agent",
                selection_owner="main-control-agent",
                exact_layer3=None,
            )
            positive = layer3_selector_runtime_selection(
                projection, evidence_signals=case["positive_signals"]
            )
            nearest_negative = layer3_selector_runtime_selection(
                projection,
                evidence_signals=[
                    *case["positive_signals"],
                    case["nearest_negative_signal"],
                ],
            )
            background = layer3_selector_runtime_selection(
                projection, evidence_signals=case["background_signals"]
            )
        except (ValidationProblem, ValueError) as exc:
            errors.append(
                f"Decision Eval Review Domain {case.get('id')} failed: {exc}"
            )
            continue
        passed = {
            "positive": positive == [case["domain"]],
            "nearest-negative": nearest_negative == [],
            "background": background == [],
        }
        for outcome, is_passed in passed.items():
            if not is_passed:
                errors.append(
                    f"Decision Eval Review Domain {case['id']} {outcome} failed"
                )
        outcomes.append(
            {
                "id": case["id"],
                "review_skill": case["review_skill"],
                "domain": case["domain"],
                "passed": passed,
            }
        )
    return {
        "case_count": len(outcomes),
        "passed_outcome_count": sum(
            sum(result["passed"].values()) for result in outcomes
        ),
        "outcomes": outcomes,
        "errors": list(errors),
    }, errors


def evaluate_decision_document(
    document: object,
    authority: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate compact baselines and one controlled mutation per invariant."""

    errors: list[str] = []
    expected_document_fields = {
        "schema_version",
        "defaults",
        "level_invariance",
        "review_domain_cases",
        "cases",
    }
    if not isinstance(document, dict) or set(document) != expected_document_fields:
        errors.append(
            "Decision Eval document fields must be schema_version, defaults, level_invariance, review_domain_cases, and cases"
        )
        document = {}
    if document.get("schema_version") != 1:
        errors.append("Decision Eval fixture schema_version must be 1")
    defaults = document.get("defaults")
    if _decision_schema_invalid(defaults):
        errors.append("Decision Eval defaults do not match the seven-axis schema")
    invariance = document.get("level_invariance")
    level_evidence, level_errors = _evaluate_level_invariance(invariance)
    errors.extend(level_errors)
    invariance_count = level_evidence.get(
        "canonical_route_invocation_count", 0
    )
    semantic_route = level_evidence.get("semantic_route", {})
    if isinstance(defaults, dict) and level_evidence.get("projections"):
        canonical_fixed = level_evidence["projections"][0]["fixed_route"]
        default_professional = defaults["professional_layer3_decision"]
        default_review = defaults["review_decision"]
        default_fixed = {
            "primary_professional_skill": default_professional[
                "primary_skill"
            ],
            "implementation_layer3": default_professional[
                "implementation_layer3"
            ],
            "domain": default_professional["domain"],
            "required_review_skills": [default_review["review_skill"]],
        }
        if default_fixed != canonical_fixed:
            errors.append(
                "Decision Eval defaults must equal the canonical semantic route"
            )
        if default_review["review_layer3"] != semantic_route.get(
            "review_layer3"
        ):
            errors.append(
                "Decision Eval default Review Layer 3 must equal the fixed review-risk projection"
            )
    l5_evidence: dict[str, Any] = {}
    l5_errors: list[str] = []
    token_evidence: dict[str, Any] = {}
    token_errors: list[str] = []
    if isinstance(semantic_route, dict) and level_evidence.get("projections"):
        l5_evidence, l5_errors = _evaluate_l5_confirmation(semantic_route)
        fixed_route = level_evidence["projections"][0]["fixed_route"]
        token_evidence, token_errors = _evaluate_token_pressure(fixed_route)
    else:
        l5_errors.append("Decision Eval L5 evidence lacks a canonical semantic route")
        token_errors.append("Decision Eval token evidence lacks a canonical semantic route")
    errors.extend(l5_errors)
    errors.extend(token_errors)
    review_domain_evidence, review_domain_errors = (
        _evaluate_review_domain_consumers(document.get("review_domain_cases"))
    )
    errors.extend(review_domain_errors)
    cases = document.get("cases")
    if not isinstance(cases, list):
        errors.append("Decision Eval cases must be a list")
        cases = []
    bindings = {
        item["mutant_id"]: item for item in authority["invariant_bindings"]
    }
    ids = [
        case.get("id")
        for case in cases
        if isinstance(case, dict) and isinstance(case.get("id"), str)
    ]
    if len(ids) != len(cases):
        errors.append("Decision Eval every case must have one string id")
    if len(ids) != len(set(ids)):
        errors.append("Decision Eval controlled mutant ids must be unique")
    if set(ids) != set(bindings):
        errors.append(
            "Decision Eval controlled mutant ids must exactly match source authority"
        )
    results: list[dict[str, Any]] = []
    level_derivation_rows: list[dict[str, object]] = []
    case_fields = {
        "id",
        "axis",
        "invariant_id",
        "failure_id",
        "decision",
        "mutation",
    }
    review_copy_evidence, review_copy_errors = _evaluate_review_copy(document)
    errors.extend(review_copy_errors)
    for index, case in enumerate(cases):
        context = f"Decision Eval cases[{index}]"
        if not isinstance(case, dict) or set(case) != case_fields:
            errors.append(f"{context} fields must be exactly {sorted(case_fields)}")
            continue
        case_id = case["id"]
        binding = bindings.get(case_id)
        if binding is None:
            continue
        for field in ("axis", "invariant_id", "failure_id"):
            if case[field] != binding[field]:
                errors.append(
                    f"{case_id}: {field} must equal its source authority binding"
                )
        if not isinstance(case["decision"], dict):
            errors.append(f"{case_id}: decision override must be an object")
            continue
        baseline = decision_case_baseline(document, case)
        computed_level, derivation_errors = _decision_level_derivation(
            baseline.get("execution_level")
        )
        declared_level = baseline.get("execution_level", {})
        computation_basis = (
            declared_level.get("computation_basis", {})
            if isinstance(declared_level, dict)
            else {}
        )
        projection_fields = (
            "requested_or_automatic",
            "automatic_level",
            "minimum_eligible_level",
            "mandatory_risk_floor",
            "historical_max",
            "effective_level",
        )
        computed_projection = (
            {
                "requested_or_automatic": computed_level[
                    "requested_or_automatic"
                ],
                "automatic_level": computed_level["automatic_level"],
                "minimum_eligible_level": computed_level[
                    "minimum_eligible_level"
                ],
                "mandatory_risk_floor": computed_level["mandatory_floor"],
                "historical_max": computation_basis.get(
                    "prior_historical_max_effective"
                ),
                "effective_level": computed_level["effective_level"],
            }
            if isinstance(computed_level, dict)
            else None
        )
        level_derivation_rows.append(
            {
                "case_id": case_id,
                "requested_level": declared_level.get("requested_level"),
                "declared_projection": {
                    field: declared_level.get(field)
                    for field in projection_fields
                },
                "computed_projection": computed_projection,
                "errors": derivation_errors,
            }
        )
        baseline_failures = [
            *decision_baseline_failure_ids(baseline),
            *decision_state_failure_ids(baseline),
        ]
        if case_id == "review-copies-implementation-layer3":
            baseline_failures.extend(
                review_copy_evidence.get("baseline_failure_ids", [])
            )
        baseline_failures = list(dict.fromkeys(baseline_failures))
        expected_failure = binding["failure_id"]
        if baseline_failures:
            errors.append(
                f"{case_id}: baseline fails {baseline_failures}"
            )
            results.append(
                {
                    "id": case_id,
                    "axis": binding["axis"],
                    "invariant_id": binding["invariant_id"],
                    "expected_failure_id": expected_failure,
                    "baseline_failure_ids": baseline_failures,
                    "mutant_failure_ids": [],
                    "mutant_evaluated": False,
                    "passed": False,
                }
            )
            continue
        mutant = _apply_decision_mutation(baseline, case["mutation"])
        if mutant is None:
            errors.append(f"{case_id}: mutation must target one existing decision field")
            continue
        mutant_failures = (
            list(review_copy_evidence.get("mutant_failure_ids", []))
            if case_id == "review-copies-implementation-layer3"
            else decision_state_failure_ids(mutant)
        )
        passed = mutant_failures == [expected_failure]
        if mutant_failures != [expected_failure]:
            errors.append(
                f"{case_id}: mutant must fail only {expected_failure}, got "
                f"{mutant_failures}"
            )
        results.append(
            {
                "id": case_id,
                "axis": binding["axis"],
                "invariant_id": binding["invariant_id"],
                "expected_failure_id": expected_failure,
                "baseline_failure_ids": baseline_failures,
                "mutant_failure_ids": mutant_failures,
                "mutant_evaluated": True,
                "passed": passed,
            }
        )
    level_derivation_errors = [
        f"{row['case_id']}: {error}"
        for row in level_derivation_rows
        for error in row["errors"]
    ]
    level_derivation_evidence = {
        "consumer": "validation_utils:compute_execution_level",
        "call_count": len(level_derivation_rows),
        "rows": level_derivation_rows,
        "errors": level_derivation_errors,
    }
    mechanism_evidence = {
        "level_invariance": level_evidence,
        "level_derivation": level_derivation_evidence,
        "l5_confirmation": l5_evidence,
        "review_copy": review_copy_evidence,
        "token_pressure": token_evidence,
        "review_domain_consumers": review_domain_evidence,
    }
    return {
        "schema_version": 1,
        "status": "pass" if not errors else "fail",
        "axis_count": len(authority["decision_axes"]),
        "axes": list(authority["decision_axes"]),
        "case_count": len(results),
        "level_invariance_count": invariance_count,
        "passed_count": sum(result["passed"] for result in results),
        "mechanism_evidence": mechanism_evidence,
        "results": results,
        "errors": errors,
    }


def evaluate_decision_cases(
    cases_path: Path = DECISION_CASES,
    *,
    authority: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Load and evaluate the source-bound Decision Eval fixture."""

    selected_authority = (
        decision_eval_authority(CORE_CONTRACTS)
        if authority is None
        else copy.deepcopy(authority)
    )
    return evaluate_decision_document(
        load_yaml_file(cases_path), selected_authority
    )


def _compatibility_projection(
    route_decision: dict[str, Any],
) -> dict[str, Any]:
    """Project the canonical envelope to the evaluator's five fixture fields."""

    route_result = route_decision["route_result"]
    return {
        "path": route_decision["path"],
        "profile": route_result["start_profile"],
        "primary_skill": route_result["primary_skill"],
        "layer3_skills": route_result["layer3_skills"],
        "review_skill": route_result["review_skill"],
    }


def route(
    prompt: str,
    *,
    main_execution: object,
    domain_registry: object = None,
    professional_registry: object = None,
) -> dict[str, Any]:
    """Call the canonical route once and return only five fixture fields."""

    route_decision = canonical_route(
        prompt,
        main_execution=main_execution,
        domain_registry=domain_registry,
        professional_registry=professional_registry,
    )
    return _compatibility_projection(route_decision)


def validate_capability_coverage_matrix(
    matrix_path: Path = CAPABILITY_MATRIX,
    *,
    root: Path = ROOT,
    professional_registry: object | None = None,
    foundation_registry: object | None = None,
    domain_registry: object | None = None,
    route_results: dict[str, object] | None = None,
) -> list[str]:
    """Validate matrix evidence against current deterministic route results."""

    registry_root = root / "src" / "registry"
    registry_inputs = (
        ("professional-skills.yaml", professional_registry),
        ("foundation-skills.yaml", foundation_registry),
        ("domain-skills.yaml", domain_registry),
    )
    resolved: list[object | None] = []
    for filename, supplied in registry_inputs:
        path = registry_root / filename
        resolved.append(
            supplied
            if supplied is not None
            else load_yaml_file(path)
            if path.is_file()
            else None
        )
    evidence_documents = [
        (path.relative_to(root).as_posix(), load_yaml_file(path))
        for path in (
            root / "evals" / "capability-coverage" / "admission-cases.yaml",
            root / "evals" / "routing" / "capability-coverage-cases.yaml",
        )
        if path.is_file()
    ]
    evidence_catalog, evidence_errors = fixture_ids(*evidence_documents)
    current_results = route_results or {}
    passing_ids = {
        case_id
        for case_id, result in current_results.items()
        if isinstance(result, dict) and result.get("passed") is True
    }
    return [
        *evidence_errors,
        *validate_capability_coverage(
            matrix_path,
            root=root,
            professional_registry=resolved[0],
            foundation_registry=resolved[1],
            domain_registry=resolved[2],
            evidence_ids=evidence_catalog,
            passing_evidence_ids=passing_ids if route_results is not None else None,
            route_results=current_results if route_results is not None else None,
        ),
    ]


def _domain_metadata(
    case: dict[str, Any],
    case_id: str,
    prompt: str,
    expected: dict[str, Any],
    known_skills: set[str],
    excluded: list[str],
    errors: list[str],
) -> tuple[
    dict[str, str] | None,
    str | None,
    dict[str, str] | None,
    dict[str, str] | None,
    str | None,
]:
    """Validate optional table-driven Domain family and anti-route metadata."""

    raw_family = case.get("domain_family")
    raw_anti = case.get("domain_anti")
    raw_transition = case.get("domain_transition")
    raw_anti_variant = case.get("domain_anti_variant")
    family: dict[str, str] | None = None
    anti: str | None = None
    transition: dict[str, str] | None = None
    anti_variant: str | None = None
    normalized_prompt = " ".join(prompt.casefold().split())
    matched = domain_route_family(normalized_prompt)
    matched_mapping = (
        {"domain": matched[0], "family": matched[1]}
        if matched is not None
        else None
    )
    combined_material = raw_family is not None and raw_transition is not None
    if raw_anti is not None and (
        raw_family is not None or raw_transition is not None
    ):
        errors.append(
            f"{case_id}: Domain fixture cannot combine material positive and "
            "unchanged evidence"
        )
    if raw_family is not None:
        expected_fields = {
            "domain",
            "family",
            "variant",
            *(("evidence_id",) if combined_material else ()),
        }
        if not isinstance(raw_family, dict) or set(raw_family) != expected_fields:
            errors.append(
                f"{case_id}: domain_family must contain exactly "
                + ", ".join(sorted(expected_fields))
            )
        else:
            family = {
                key: str(raw_family.get(key, "")).strip()
                for key in sorted(expected_fields)
            }
            domain = family["domain"]
            family_name = family["family"]
            variant = family["variant"]
            if combined_material and not family["evidence_id"]:
                errors.append(
                    f"{case_id}: domain_family.evidence_id must be non-empty"
                )
            spec = ALL_DOMAIN_ROUTE_SPECS.get(domain)
            if spec is None:
                errors.append(f"{case_id}: domain_family names unknown Domain {domain!r}")
            elif family_name not in spec["families"]:
                errors.append(
                    f"{case_id}: domain_family names unknown family {family_name!r} for {domain}"
                )
            if variant not in DOMAIN_VARIANTS:
                errors.append(
                    f"{case_id}: domain_family.variant must be canonical or paraphrase"
                )
            if domain not in expected.get("layer3_skills", []):
                errors.append(
                    f"{case_id}: positive Domain fixture expected route omits {domain}"
                )
            if matched != (domain, family_name):
                errors.append(
                    f"{case_id}: oracle matched {matched!r}, expected Domain family "
                    f"{(domain, family_name)!r}"
                )
    if raw_transition is not None:
        expected_fields = {
            "domain",
            "family",
            *(("evidence_id",) if combined_material else ()),
        }
        if not isinstance(raw_transition, dict) or set(raw_transition) != expected_fields:
            errors.append(
                f"{case_id}: domain_transition must contain exactly "
                + ", ".join(sorted(expected_fields))
            )
        else:
            transition = {
                key: str(raw_transition.get(key, "")).strip()
                for key in sorted(expected_fields)
            }
            domain = transition["domain"]
            family_name = transition["family"]
            if combined_material and not transition["evidence_id"]:
                errors.append(
                    f"{case_id}: domain_transition.evidence_id must be non-empty"
                )
            spec = ALL_DOMAIN_ROUTE_SPECS.get(domain)
            if spec is None:
                errors.append(
                    f"{case_id}: domain_transition names unknown Domain {domain!r}"
                )
            elif family_name not in spec["families"]:
                errors.append(
                    f"{case_id}: domain_transition names unknown family "
                    f"{family_name!r} for {domain}"
                )
            if domain not in expected.get("layer3_skills", []):
                errors.append(
                    f"{case_id}: Domain transition expected route omits {domain}"
                )
            if matched != (domain, family_name):
                errors.append(
                    f"{case_id}: oracle matched {matched!r}, expected Domain transition "
                    f"{(domain, family_name)!r}"
                )
            if not domain_transition_marker(
                normalized_prompt,
                domain,
                family_name,
            ):
                errors.append(
                    f"{case_id}: domain_transition lacks a same-clause migration marker"
                )
    if combined_material and family is not None and transition is not None:
        family_key = (family["domain"], family["family"])
        transition_key = (transition["domain"], transition["family"])
        if family_key != transition_key:
            errors.append(
                f"{case_id}: combined Domain evidence must name the same "
                "Domain and family"
            )
        if family["evidence_id"] == transition["evidence_id"]:
            errors.append(
                f"{case_id}: combined Domain contracts require distinct evidence_id values"
            )
    if raw_anti is not None:
        if (
            not isinstance(raw_anti, str)
            or raw_anti not in ALL_DOMAIN_ROUTE_SPECS
        ):
            errors.append(f"{case_id}: domain_anti must name one known Domain")
        else:
            anti = raw_anti
            if anti not in excluded:
                errors.append(
                    f"{case_id}: domain_anti {anti!r} must also be explicitly excluded"
                )
            if matched is not None and matched[0] == anti:
                errors.append(
                    f"{case_id}: Domain anti-route still matched {matched!r}"
                )
    if raw_anti_variant is not None:
        if raw_anti is None:
            errors.append(f"{case_id}: domain_anti_variant requires domain_anti")
        elif raw_anti_variant != "unchanged-paraphrase":
            errors.append(
                f"{case_id}: domain_anti_variant must be unchanged-paraphrase"
            )
        else:
            anti_variant = raw_anti_variant
            if isinstance(raw_anti, str) and not domain_unchanged_marker(
                normalized_prompt,
                raw_anti,
            ):
                errors.append(
                    f"{case_id}: unchanged-paraphrase lacks related anti-route evidence"
                )
    if raw_family is not None or raw_transition is not None or raw_anti is not None:
        prompt_skill_names = sorted(
            name for name in known_skills if name.casefold() in normalized_prompt
        )
        if prompt_skill_names:
            errors.append(
                f"{case_id}: Domain fixture prompt embeds Skill name(s): "
                + ", ".join(prompt_skill_names)
            )
    return family, anti, matched_mapping, transition, anti_variant


def evaluate_routes(
    cases_path: Path = CASES,
    *,
    _validate_capability_matrix: bool = True,
    professional_registry: object | None = None,
) -> dict[str, Any]:
    """Evaluate current deterministic routes without writing tracked reports."""

    decision_authority = decision_eval_authority(CORE_CONTRACTS)
    compatibility_baseline: dict[str, int] = {}
    compatibility_errors: list[str] = []
    for key, path in (
        ("routing_cases", CASES),
        ("capability_cases", CAPABILITY_CASES),
    ):
        fixture = load_yaml_file(path)
        fixture_cases = fixture.get("cases") if isinstance(fixture, dict) else None
        if not isinstance(fixture_cases, list):
            compatibility_errors.append(
                f"Decision Eval compatibility fixture {path} has no cases list"
            )
            compatibility_baseline[key] = 0
        else:
            compatibility_baseline[key] = len(fixture_cases)
    if compatibility_baseline != decision_authority["compatibility_baseline"]:
        compatibility_errors.append(
            "Decision Eval compatibility baseline drifted: expected "
            f"{decision_authority['compatibility_baseline']}, got "
            f"{compatibility_baseline}"
        )
    pipeline_errors = route_once_pipeline_errors()
    if pipeline_errors:
        decision_eval = {
            "status": "unavailable",
            "case_count": 0,
            "passed_count": 0,
            "results": [],
            "errors": [],
        }
        errors = [
            f"routing-integrity-failure: route-once pipeline: {error}"
            for error in pipeline_errors
        ]
        errors.extend(compatibility_errors)
        errors.extend(decision_eval["errors"])
        return {
            "schema_version": 6,
            "architecture": "hookless-control-plane-v1",
            "status": "fail",
            "evidence_scope": "deterministic-fixtures",
            "limitations": list(EVIDENCE_LIMITATIONS),
            "case_count": 0,
            "passed_count": 0,
            "negative_case_count": 0,
            "domain_family_case_count": 0,
            "domain_anti_case_count": 0,
            "domain_transition_case_count": 0,
            "domain_unchanged_case_count": 0,
            "candidate_coverage": "unavailable",
            "route_once": "unavailable",
            "legacy_route_count": None,
            "automatic_routing_policy_fingerprint": "unavailable",
            "max_layer3_per_case": 0,
            "compatibility_baseline": compatibility_baseline,
            "decision_eval": decision_eval,
            "results": [],
            "errors": errors,
        }
    decision_eval = evaluate_decision_cases(authority=decision_authority)
    errors: list[str] = [*compatibility_errors, *decision_eval["errors"]]
    cases_data = load_yaml_file(cases_path)
    pro_data = (
        load_yaml_file(PROFESSIONAL)
        if professional_registry is None
        else professional_registry
    )
    try:
        policy_fingerprint = (
            professional_automatic_routing_policy_fingerprint(pro_data)
        )
    except ValidationProblem:
        policy_fingerprint = "unavailable"
    foundation_data = load_yaml_file(FOUNDATION)
    domain_data = load_yaml_file(DOMAIN)
    cases = cases_data.get("cases") if isinstance(cases_data, dict) else None
    if not isinstance(cases, list):
        raise ValidationProblem(f"{cases_path}:cases must be a list")
    professional = {
        entry.get("name"): entry
        for entry in pro_data.get("professional_skills", [])
        if isinstance(entry, dict)
    }
    layer3 = {
        entry.get("name"): entry
        for entry in [
            *foundation_data.get("foundation_skills", []),
            *domain_data.get("domain_skills", []),
        ]
        if isinstance(entry, dict)
    }
    known_skills = set(professional) | set(layer3)
    case_id_counts: dict[str, int] = {}
    for case in cases:
        if isinstance(case, dict) and isinstance(case.get("id"), str):
            case_id = case["id"]
            case_id_counts[case_id] = case_id_counts.get(case_id, 0) + 1
    duplicate_case_ids = {
        case_id for case_id, count in case_id_counts.items() if count > 1
    }
    results = []
    for case in cases:
        if not isinstance(case, dict):
            errors.append("routing case must be a mapping")
            continue
        case_id = case.get("id")
        expected = case.get("expected")
        prompt = case.get("prompt")
        if (
            not isinstance(case_id, str)
            or not isinstance(prompt, str)
            or not isinstance(expected, dict)
        ):
            errors.append(f"invalid routing case {case_id!r}")
            continue
        case_error_start = len(errors)
        if case_id in duplicate_case_ids:
            errors.append(f"{case_id}: routing case id must be unique")
        raw_excluded = case.get("excluded_skills", [])
        if not isinstance(raw_excluded, list) or not all(
            isinstance(item, str) and item.strip() for item in raw_excluded
        ):
            errors.append(
                f"{case_id}: excluded_skills must be a list of non-blank Skill names"
            )
            excluded: list[str] = []
        else:
            excluded = [item.strip() for item in raw_excluded]
        if len(excluded) != len(set(excluded)):
            errors.append(f"{case_id}: excluded_skills must not contain duplicates")
        unknown_excluded = sorted(set(excluded) - known_skills)
        if unknown_excluded:
            errors.append(
                f"{case_id}: excluded_skills names unknown Skill(s): "
                + ", ".join(unknown_excluded)
            )
        family, anti, matched_family, transition, anti_variant = _domain_metadata(
            case,
            case_id,
            prompt,
            expected,
            known_skills,
            excluded,
            errors,
        )
        main_execution = case.get("main_execution")
        main_errors = validate_main_assignment(main_execution)
        if main_errors:
            errors.extend(
                f"{case_id}: {error}"
                for error in main_errors
            )
        try:
            observed = route_with_trace(
                prompt,
                main_execution=main_execution,
                domain_registry=domain_data,
                professional_registry=pro_data,
            )
        except RoutingIntegrityError as exc:
            integrity_error = f"{case_id}: {exc.code}: {exc}"
            errors.append(integrity_error)
            results.append(
                {
                    "id": case_id,
                    "prompt": prompt,
                    "expected": expected,
                    "actual": None,
                    "route_decision": None,
                    "winner_trace": {
                        "candidate_coverage": "unavailable",
                        "route_once": "unavailable",
                    },
                    "excluded_skills": excluded,
                    "domain_family": family,
                    "domain_transition": transition,
                    "domain_anti": anti,
                    "domain_anti_variant": anti_variant,
                    "matched_domain_family": matched_family,
                    "positive_passed": False,
                    "negative_passed": False,
                    "passed": False,
                    "errors": [integrity_error],
                }
            )
            continue
        route_decision = observed["route_decision"]
        actual = _compatibility_projection(route_decision)
        winner_trace = observed["winner_trace"]
        positive_passed = actual == expected
        if not positive_passed:
            errors.append(f"{case_id}: expected {expected}, got {actual}")
        selected = {
            actual["primary_skill"],
            actual["review_skill"],
            *actual["layer3_skills"],
        }
        selected_exclusions = sorted(selected & set(excluded))
        negative_passed = not selected_exclusions
        if selected_exclusions:
            errors.append(
                f"{case_id}: actual route selected explicitly excluded Skill(s): "
                + ", ".join(selected_exclusions)
            )
        if actual["path"] == "analyzed" and actual["profile"] != "analysis-agent":
            errors.append(f"{case_id}: Analyzed Work must start with analysis-agent")
        if actual["path"] == "direct" and actual["profile"] not in {
            "task-agent",
            "review-agent",
        }:
            errors.append(
                f"{case_id}: Direct work must start with task-agent or review-agent"
            )
        primary = actual["primary_skill"]
        review = actual["review_skill"]
        if primary not in professional or professional[primary].get("task_routable") is not True:
            errors.append(f"{case_id}: primary Skill is not task-routable: {primary}")
        elif actual["profile"] not in professional[primary].get("role_support", []):
            errors.append(
                f"{case_id}: {primary} does not support {actual['profile']}"
            )
        if review not in professional:
            errors.append(f"{case_id}: unknown Review Skill {review}")
        else:
            if professional[review].get("task_routable") is not True:
                errors.append(f"{case_id}: Review Skill is not task-routable: {review}")
            if "review-agent" not in professional[review].get("role_support", []):
                errors.append(
                    f"{case_id}: Review Skill {review} does not support review-agent"
                )
        if len(actual["layer3_skills"]) > 3:
            errors.append(f"{case_id}: ordinary route exceeds three Layer 3 Skills")
        if len(actual["layer3_skills"]) != len(set(actual["layer3_skills"])):
            errors.append(f"{case_id}: route selects duplicate Layer 3 Skills")
        for name in actual["layer3_skills"]:
            if name not in layer3:
                errors.append(f"{case_id}: unknown Layer 3 Skill {name}")
            elif name not in professional[primary].get("layer3_candidates", []):
                errors.append(
                    f"{case_id}: Layer 3 Skill {name} is not targeted by {primary}"
                )
            elif actual["profile"] not in layer3[name].get("role_support", []):
                errors.append(
                    f"{case_id}: Layer 3 Skill {name} does not support {actual['profile']}"
                )
        case_errors = errors[case_error_start:]
        results.append(
            {
                "id": case_id,
                "prompt": prompt,
                "expected": expected,
                "actual": actual,
                "route_decision": route_decision,
                "winner_trace": winner_trace,
                "excluded_skills": excluded,
                "domain_family": family,
                "domain_transition": transition,
                "domain_anti": anti,
                "domain_anti_variant": anti_variant,
                "matched_domain_family": matched_family,
                "positive_passed": positive_passed,
                "negative_passed": negative_passed,
                "passed": positive_passed and negative_passed and not case_errors,
                "errors": list(case_errors),
            }
        )

    if _validate_capability_matrix:
        capability_results = (
            results
            if cases_path.resolve() == CAPABILITY_CASES.resolve()
            else evaluate_routes(
                CAPABILITY_CASES,
                _validate_capability_matrix=False,
            )["results"]
        )
        errors.extend(
            validate_capability_coverage_matrix(
                professional_registry=pro_data,
                foundation_registry=foundation_data,
                domain_registry=domain_data,
                route_results={
                    str(item["id"]): item
                    for item in capability_results
                    if isinstance(item, dict)
                    and isinstance(item.get("id"), str)
                },
            )
        )

    coverage_states = {
        item["winner_trace"]["candidate_coverage"]
        for item in results
        if isinstance(item.get("winner_trace"), dict)
    }
    route_once_states = {
        item["winner_trace"]["route_once"]
        for item in results
        if isinstance(item.get("winner_trace"), dict)
    }
    candidate_coverage = (
        next(iter(coverage_states))
        if len(coverage_states) == 1
        else "unavailable"
        if not coverage_states
        else "mixed"
    )
    route_once = (
        next(iter(route_once_states))
        if len(route_once_states) == 1
        else "unavailable"
    )
    return {
        "schema_version": 6,
        "architecture": "hookless-control-plane-v1",
        "status": "pass" if not errors else "fail",
        "evidence_scope": "deterministic-fixtures",
        "limitations": list(EVIDENCE_LIMITATIONS),
        "case_count": len(results),
        "passed_count": sum(1 for item in results if item["passed"]),
        "negative_case_count": sum(bool(item["excluded_skills"]) for item in results),
        "domain_family_case_count": sum(
            item["domain_family"] is not None for item in results
        ),
        "domain_anti_case_count": sum(item["domain_anti"] is not None for item in results),
        "domain_transition_case_count": sum(
            item["domain_transition"] is not None for item in results
        ),
        "domain_unchanged_case_count": sum(
            item["domain_anti_variant"] == "unchanged-paraphrase"
            for item in results
        ),
        "candidate_coverage": candidate_coverage,
        "route_once": route_once,
        "legacy_route_count": 0,
        "automatic_routing_policy_fingerprint": policy_fingerprint,
        "max_layer3_per_case": max(
            (
                len(item["actual"]["layer3_skills"])
                for item in results
                if isinstance(item.get("actual"), dict)
            ),
            default=0,
        ),
        "compatibility_baseline": compatibility_baseline,
        "decision_eval": decision_eval,
        "results": results,
        "errors": errors,
    }


def _args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate hookless Skill routing.")
    parser.add_argument("--candidate-output-dir", type=Path)
    parser.add_argument("--release-projection", action="store_true")
    parser.add_argument("--reports-dir", type=Path, default=REPORT_JSON.parent)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _args(argv)
    try:
        report = evaluate_routes()
    except ValidationProblem as exc:
        return fail_many("eval-routing", [str(exc)])
    errors = report["errors"]

    if args.candidate_output_dir is not None:
        captured = args.candidate_output_dir / "routes.json"
        if not captured.is_file():
            errors.append(f"candidate output is missing {captured}")
        else:
            try:
                candidate = json.loads(captured.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"invalid candidate routes.json: {exc}")
            else:
                expected_candidate = {
                    item["id"]: item["actual"] for item in report["results"]
                }
                if candidate != expected_candidate:
                    errors.append(
                        "captured candidate routes differ from current deterministic outputs"
                    )
    report["status"] = "pass" if not errors else "fail"
    report_json, report_markdown = report_output_paths(
        args.reports_dir, REPORT_JSON.name, REPORT_MD.name
    )
    args.reports_dir.mkdir(parents=True, exist_ok=True)
    report_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if args.release_projection:
        report_markdown.write_text(_render_markdown(report), encoding="utf-8")
    if errors:
        return fail_many("eval-routing", errors)
    print(f"eval-routing: {report['passed_count']} hookless routing case(s) passed.")
    return 0


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Hookless Routing Evaluation",
        "",
        f"- Cases: {report['case_count']}",
        f"- Passed: {report['passed_count']}",
        f"- Evidence scope: `{report['evidence_scope']}`",
        f"- Explicit negative-route cases: {report['negative_case_count']}",
        f"- Domain family cases: {report['domain_family_case_count']}",
        f"- Domain anti-route cases: {report['domain_anti_case_count']}",
        f"- Domain transition cases: {report['domain_transition_case_count']}",
        f"- Domain unchanged-paraphrase controls: {report['domain_unchanged_case_count']}",
        f"- Maximum Layer 3 Skills in one route: {report['max_layer3_per_case']}",
        f"- Decision axes: {report['decision_eval']['axis_count']}",
        f"- Controlled Decision mutants: {report['decision_eval']['case_count']}",
        f"- Compatibility baseline: {report['compatibility_baseline']['routing_cases']}+{report['compatibility_baseline']['capability_cases']}",
        "",
        "| Case | Domain family | Path | Profile | Primary | Layer 3 | Review | Excluded | Pass |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["results"]:
        actual = item["actual"]
        family = item["domain_family"]
        transition = item["domain_transition"]
        family_label = (
            f"{family['domain']}:{family['family']}:{family['variant']}"
            if family is not None
            else f"transition:{transition['domain']}:{transition['family']}"
            if transition is not None
            else f"anti:{item['domain_anti']}"
            if item["domain_anti"] is not None
            else "-"
        )
        lines.append(
            f"| {item['id']} | {family_label} | {actual['path']} | "
            f"{actual['profile']} | {actual['primary_skill']} | "
            f"{', '.join(actual['layer3_skills']) or '-'} | "
            f"{actual['review_skill']} | "
            f"{', '.join(item['excluded_skills']) or '-'} | {item['passed']} |"
        )
    lines.extend(
        ["", "## Limitations", "", *[f"- {item}" for item in report["limitations"]]]
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
