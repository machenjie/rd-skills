#!/usr/bin/env python3
"""Evaluate deterministic hookless task-to-Skill routing fixtures."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
import re
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
    authoritative_build_input_snapshot,
    decision_eval_authority,
    fail_many,
    layer3_selector_authority,
    layer3_selector_runtime_projection,
    layer3_selector_runtime_selection,
    layer3_selector_runtime_selection_receipt,
    layer3_selector_runtime_selection_receipt_errors,
    load_yaml_file,
    professional_automatic_routing_policy_fingerprint,
    report_output_paths,
    runtime_asset_build_identity,
    validate_main_assignment,
)


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "routing" / "cases.yaml"
BOUNDARY_RELATIONS = ROOT / "evals" / "routing" / "boundary-relations.yaml"
CAPABILITY_CASES = ROOT / "evals" / "routing" / "capability-coverage-cases.yaml"
DECISION_CASES = ROOT / "evals" / "routing" / "decision-cases.yaml"
CAPABILITY_MATRIX = ROOT / "evals" / "capability-coverage" / "matrix.yaml"
PROFESSIONAL = ROOT / "src" / "registry" / "professional-skills.yaml"
FOUNDATION = ROOT / "src" / "registry" / "foundation-skills.yaml"
DOMAIN = ROOT / "src" / "registry" / "domain-skills.yaml"
REPORT_JSON = ROOT / "reports" / "routing-eval.json"
REPORT_MD = ROOT / "reports" / "routing-eval.md"
DOMAIN_VARIANTS = {"canonical", "paraphrase"}
BOUNDARY_ROLES = ("canonical", "paraphrase", "distractor", "transition")
ROUTE_DIMENSIONS = (
    "path",
    "profile",
    "primary_skill",
    "layer3_skills",
    "review_skill",
)
EVIDENCE_LIMITATIONS = (
    "Deterministic routing fixtures do not measure wall-clock performance.",
    "Fixture agreement does not prove real-host accuracy or the installed user experience.",
    "Prompt matching is a deterministic regression oracle, not a learned or production router.",
)
def _authoritative_build_identity() -> str:
    """Capture one source-bound build identity for a public evaluation."""

    try:
        return runtime_asset_build_identity(
            authoritative_build_input_snapshot(ROOT).get("sha256")
        )
    except ValueError as exc:
        raise ValidationProblem(
            "authoritative build input snapshot sha256 must be 64 lowercase hex"
        ) from exc


def evaluate_decision_document(document: object, authority=None) -> dict[str, Any]:
    """Exercise adjacent behavioral cases against the real routing oracle."""
    errors = []
    results = []
    if not isinstance(document, dict) or not isinstance(document.get("cases"), list) or not document["cases"]:
        return {"status": "fail", "case_count": 0, "passed_count": 0, "results": [], "errors": ["decision cases must be a non-empty list"]}
    seen = set()
    for case in document["cases"]:
        case_errors = []
        if not isinstance(case, dict) or not isinstance(case.get("id"), str) or not case["id"] or case["id"] in seen:
            errors.append("decision case IDs must be non-empty and unique")
            continue
        seen.add(case["id"])
        try:
            if not isinstance(case.get("expected"), dict) or not case["expected"]:
                raise ValueError("decision case requires an observable expected outcome")
            actual = canonical_route(case["prompt"], main_execution={"producer": "main-control-agent", "task_id": case["id"]})["route_result"]
            for field, expected in case["expected"].items():
                if field not in actual or actual[field] != expected:
                    case_errors.append(f"{case['id']}: {field}: expected {expected!r}, got {actual.get(field)!r}")
            for excluded in case.get("excluded_skills", []):
                if excluded in [actual["primary_skill"], actual["review_skill"], *actual["layer3_skills"]]:
                    case_errors.append(f"{case['id']}: selected excluded expertise {excluded}")
        except (KeyError, TypeError, ValueError, ValidationProblem) as exc:
            actual = None
            case_errors.append(f"{case['id']}: {exc}")
        errors.extend(case_errors)
        results.append({"id": case["id"], "actual": actual, "passed": not case_errors, "errors": case_errors})
    return {"schema_version": 1, "status": "fail" if errors else "pass", "case_count": len(results), "passed_count": sum(row["passed"] for row in results), "results": results, "errors": errors}


def _evaluate_decision_cases(cases_path: Path, *, authority=None, build_identity=None) -> dict[str, Any]:
    return evaluate_decision_document(load_yaml_file(cases_path), authority)


def evaluate_decision_cases(cases_path: Path = DECISION_CASES, *, authority=None) -> dict[str, Any]:
    return _evaluate_decision_cases(cases_path, authority=authority)


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


def _boundary_route_projection(
    result: object,
    *,
    context: str,
) -> tuple[dict[str, Any] | None, set[str], list[str]]:
    """Read one fresh route decision and prove its winner-trace binding."""

    errors: list[str] = []
    if not isinstance(result, dict):
        return None, set(), [f"{context}: routing result must be a mapping"]
    decision = result.get("route_decision")
    trace = result.get("winner_trace")
    if not isinstance(decision, dict) or not isinstance(trace, dict):
        return None, set(), [
            f"{context}: fresh route_decision and winner_trace are required"
        ]
    route_result = decision.get("route_result")
    if not isinstance(route_result, dict):
        return None, set(), [f"{context}: route_result must be a mapping"]
    layer3_skills = route_result.get("layer3_skills")
    projection = {
        "path": decision.get("path"),
        "profile": route_result.get("start_profile"),
        "primary_skill": route_result.get("primary_skill"),
        "layer3_skills": copy.deepcopy(layer3_skills),
        "review_skill": route_result.get("review_skill"),
    }
    if (
        any(
            not isinstance(projection[field], str)
            or not projection[field]
            for field in ROUTE_DIMENSIONS
            if field not in {"layer3_skills", "review_skill"}
        )
        or not isinstance(layer3_skills, list)
        or any(
            not isinstance(item, str) or not item
            for item in layer3_skills
        )
    ):
        errors.append(f"{context}: route projection is malformed")
    if decision.get("route_once") is not True:
        errors.append(f"{context}: route_decision.route_once must be true")
    if trace.get("route_once") != "proven":
        errors.append(f"{context}: winner_trace.route_once must be proven")
    if trace.get("candidate_coverage") != "full":
        errors.append(
            f"{context}: winner_trace candidate coverage must be full"
        )

    selected = trace.get("selected_candidate")
    raw_candidates = trace.get("raw_candidates")
    if not isinstance(selected, dict) or not isinstance(raw_candidates, list):
        errors.append(f"{context}: winner_trace must contain one winner")
        return projection, set(), errors
    selected_id = selected.get("candidate_id")
    if not isinstance(selected_id, str) or not selected_id:
        errors.append(f"{context}: winner_trace winner id must be non-empty")
        return projection, set(), errors
    selected_projection = {
        "path": selected.get("path"),
        "profile": selected.get("profile"),
        "primary_skill": selected.get("primary_skill"),
        "layer3_skills": copy.deepcopy(selected.get("layer3_skills")),
        "review_skill": selected.get("review_skill") if selected.get("profile") == "review-agent" else None,
    }
    if selected_projection != projection:
        errors.append(
            f"{context}: winner_trace winner differs from route_decision"
        )
    matching_winners = [
        candidate
        for candidate in raw_candidates
        if isinstance(candidate, dict)
        and candidate.get("candidate_id") == selected_id
        and {
            "path": candidate.get("path"),
            "profile": candidate.get("profile"),
            "primary_skill": candidate.get("primary_skill"),
            "layer3_skills": candidate.get("layer3_skills"),
            "review_skill": candidate.get("review_skill") if candidate.get("profile") == "review-agent" else None,
        }
        == projection
    ]
    if len(matching_winners) != 1:
        errors.append(
            f"{context}: winner_trace must bind exactly one winner to raw candidates"
        )
    selected_skills = {
        str(projection.get("primary_skill", "")),
        *(
            str(item)
            for item in (
                layer3_skills if isinstance(layer3_skills, list) else []
            )
        ),
    }
    selected_skills.discard("")
    return projection, selected_skills, errors


def evaluate_boundary_relations(
    document: object,
    route_results: object,
) -> dict[str, Any]:
    """Validate targeted routing boundaries against fresh route observations."""

    errors: list[str] = []
    relation_results: list[dict[str, Any]] = []
    if (
        not isinstance(document, dict)
        or set(document) != {"version", "relations"}
        or document.get("version") != 1
        or not isinstance(document.get("relations"), list)
    ):
        return {
            "status": "fail",
            "relation_count": 0,
            "passed_count": 0,
            "role_count": 0,
            "candidate_coverage": "unavailable",
            "route_once": "unavailable",
            "results": [],
            "errors": [
                "boundary relation fixture must contain version 1 and relations"
            ],
        }
    relations = document["relations"]
    if len(relations) != 8:
        errors.append("boundary relation fixture must declare exactly 8 relations")

    if not isinstance(route_results, list):
        route_results = []
        errors.append("boundary relation route results must be a list")
    result_ids = [
        result.get("id")
        for result in route_results
        if isinstance(result, dict) and isinstance(result.get("id"), str)
    ]
    duplicate_result_ids = {
        case_id for case_id in result_ids if result_ids.count(case_id) > 1
    }
    if duplicate_result_ids:
        errors.append(
            "boundary relation route results contain duplicate case ids: "
            + ", ".join(sorted(duplicate_result_ids))
        )
    results_by_id = {
        result["id"]: result
        for result in route_results
        if isinstance(result, dict)
        and isinstance(result.get("id"), str)
        and result["id"] not in duplicate_result_ids
    }
    professional = {
        row.get("name")
        for row in load_yaml_file(PROFESSIONAL).get("professional_skills", [])
        if isinstance(row, dict) and isinstance(row.get("name"), str)
    }
    layer3 = {
        row.get("name")
        for row in [
            *load_yaml_file(FOUNDATION).get("foundation_skills", []),
            *load_yaml_file(DOMAIN).get("domain_skills", []),
        ]
        if isinstance(row, dict) and isinstance(row.get("name"), str)
    }
    known_skills = professional | layer3

    relation_ids = [
        relation.get("id")
        for relation in relations
        if isinstance(relation, dict) and isinstance(relation.get("id"), str)
    ]
    duplicate_relation_ids = {
        relation_id
        for relation_id in relation_ids
        if relation_ids.count(relation_id) > 1
    }
    if duplicate_relation_ids:
        errors.append(
            "boundary relation ids must be unique: "
            + ", ".join(sorted(duplicate_relation_ids))
        )

    declared_case_ids: list[str] = []
    for relation in relations:
        if not isinstance(relation, dict):
            continue
        cases = relation.get("cases")
        if isinstance(cases, dict):
            declared_case_ids.extend(
                case_id
                for case_id in cases.values()
                if isinstance(case_id, str)
            )
    duplicate_case_ids = {
        case_id
        for case_id in declared_case_ids
        if declared_case_ids.count(case_id) > 1
    }
    if duplicate_case_ids:
        errors.append(
            "boundary relation case ids must be globally unique: "
            + ", ".join(sorted(duplicate_case_ids))
        )

    exact_relation_fields = {
        "id",
        "cases",
        "stable_dimensions",
        "transition_dimensions",
        "competing_route",
        "competing_skill",
    }
    for index, relation in enumerate(relations):
        relation_error_start = len(errors)
        context = f"boundary relation[{index}]"
        if not isinstance(relation, dict) or set(relation) != exact_relation_fields:
            errors.append(f"{context}: relation fields are malformed")
            continue
        relation_id = relation.get("id")
        if not isinstance(relation_id, str) or not relation_id.strip():
            errors.append(f"{context}: id must be non-empty")
            relation_id = f"invalid-{index}"
        context = str(relation_id)
        cases = relation.get("cases")
        if not isinstance(cases, dict) or set(cases) != set(BOUNDARY_ROLES):
            errors.append(
                f"{context}: cases must contain exactly canonical, paraphrase, "
                "distractor, transition"
            )
            cases = {}
        elif any(
            not isinstance(cases[role], str) or not cases[role].strip()
            for role in BOUNDARY_ROLES
        ):
            errors.append(f"{context}: every role must name one routing case")
            cases = {}

        stable = relation.get("stable_dimensions")
        transition = relation.get("transition_dimensions")
        for label, dimensions in (
            ("stable", stable),
            ("transition", transition),
        ):
            if (
                not isinstance(dimensions, list)
                or not dimensions
                or len(dimensions) != len(set(dimensions))
                or any(item not in ROUTE_DIMENSIONS for item in dimensions)
                or dimensions
                != [item for item in ROUTE_DIMENSIONS if item in dimensions]
            ):
                errors.append(
                    f"{context}: {label} dimensions must be an ordered unique "
                    "non-empty subset of route dimensions"
                )
        competing_route = relation.get("competing_route")
        competing_skill = relation.get("competing_skill")
        if competing_route not in {"direct", "analyzed"}:
            errors.append(f"{context}: competing_route must be direct or analyzed")
        if competing_skill not in known_skills:
            errors.append(f"{context}: competing_skill must name a known Skill")

        projections: dict[str, dict[str, Any]] = {}
        selected_skills: dict[str, set[str]] = {}
        if cases:
            for role in BOUNDARY_ROLES:
                case_id = cases[role]
                result = results_by_id.get(case_id)
                if result is None:
                    errors.append(
                        f"{context}/{role}: unknown routing case {case_id!r}"
                    )
                    continue
                if result.get("passed") is not True:
                    errors.append(
                        f"{context}/{role}: routing case is not passing"
                    )
                projection, skills, projection_errors = (
                    _boundary_route_projection(
                        result,
                        context=f"{context}/{role}",
                    )
                )
                errors.extend(projection_errors)
                if projection is not None:
                    projections[role] = projection
                    selected_skills[role] = skills

        if len(projections) == len(BOUNDARY_ROLES):
            canonical = projections["canonical"]
            observed_stable = [
                dimension
                for dimension in ROUTE_DIMENSIONS
                if canonical[dimension]
                == projections["paraphrase"][dimension]
                == projections["distractor"][dimension]
            ]
            if stable != observed_stable:
                errors.append(
                    f"{context}: stable dimensions drifted; declared {stable!r}, "
                    f"observed {observed_stable!r}"
                )
            observed_transition = [
                dimension
                for dimension in ROUTE_DIMENSIONS
                if canonical[dimension]
                != projections["transition"][dimension]
            ]
            if transition != observed_transition:
                errors.append(
                    f"{context}: transition dimensions differ; declared "
                    f"{transition!r}, observed {observed_transition!r}"
                )
            if competing_skill in selected_skills["distractor"]:
                errors.append(
                    f"{context}: distractor selected competing Skill "
                    f"{competing_skill!r}"
                )
            if (
                projections["transition"]["path"] != competing_route
                or competing_skill not in selected_skills["transition"]
            ):
                errors.append(
                    f"{context}: transition did not select the declared "
                    "competing route and Skill"
                )

        relation_errors = errors[relation_error_start:]
        relation_results.append(
            {
                "id": relation_id,
                "cases": copy.deepcopy(cases),
                "stable_dimensions": copy.deepcopy(stable),
                "transition_dimensions": copy.deepcopy(transition),
                "passed": not relation_errors,
                "errors": list(relation_errors),
            }
        )

    role_count = len(declared_case_ids)
    return {
        "status": "pass" if not errors else "fail",
        "relation_count": len(relations),
        "passed_count": sum(item["passed"] for item in relation_results),
        "role_count": role_count,
        "candidate_coverage": "full" if not errors and role_count == 32 else "unavailable",
        "route_once": "proven" if not errors and role_count == 32 else "unavailable",
        "results": relation_results,
        "errors": errors,
    }


def evaluate_routes(
    cases_path: Path = CASES,
    *,
    _validate_capability_matrix: bool = True,
    _validate_boundary_relations: bool = True,
    professional_registry: object | None = None,
) -> dict[str, Any]:
    """Evaluate current deterministic routes without writing tracked reports."""

    return _evaluate_routes(
        cases_path,
        _validate_capability_matrix=_validate_capability_matrix,
        _validate_boundary_relations=_validate_boundary_relations,
        professional_registry=professional_registry,
        build_identity=_authoritative_build_identity(),
    )


def _evaluate_routes(
    cases_path: Path,
    *,
    _validate_capability_matrix: bool,
    _validate_boundary_relations: bool,
    professional_registry: object | None,
    build_identity: str,
) -> dict[str, Any]:
    """Evaluate routes under one required source-bound build identity."""

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
            "boundary_relations": {
                "status": "unavailable",
                "relation_count": 0,
                "passed_count": 0,
                "role_count": 0,
                "candidate_coverage": "unavailable",
                "route_once": "unavailable",
                "results": [],
                "errors": [],
            },
            "results": [],
            "errors": errors,
        }
    decision_eval = _evaluate_decision_cases(
        DECISION_CASES,
        authority=decision_authority,
        build_identity=build_identity,
    )
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
        if review is not None and review not in professional:
            errors.append(f"{case_id}: unknown Review Skill {review}")
        elif review is not None:
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
            else _evaluate_routes(
                CAPABILITY_CASES,
                _validate_capability_matrix=False,
                _validate_boundary_relations=False,
                professional_registry=professional_registry,
                build_identity=build_identity,
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

    boundary_relations = {
        "status": "not-applicable",
        "relation_count": 0,
        "passed_count": 0,
        "role_count": 0,
        "candidate_coverage": "not-applicable",
        "route_once": "not-applicable",
        "results": [],
        "errors": [],
    }
    if (
        _validate_boundary_relations
        and cases_path.resolve() == CASES.resolve()
    ):
        boundary_relations = evaluate_boundary_relations(
            load_yaml_file(BOUNDARY_RELATIONS),
            results,
        )
        errors.extend(boundary_relations["errors"])

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
        "boundary_relations": boundary_relations,
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
        f"- Decision cases passed: {report['decision_eval']['passed_count']}/"
        f"{report['decision_eval']['case_count']}",
        f"- Compatibility baseline: {report['compatibility_baseline']['routing_cases']}+{report['compatibility_baseline']['capability_cases']}",
        f"- Targeted boundary relations: {report['boundary_relations']['passed_count']}/{report['boundary_relations']['relation_count']}",
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
