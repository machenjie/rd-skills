#!/usr/bin/env python3
"""Evaluate deterministic hookless task-to-Skill routing fixtures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
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
    ValidationProblem,
    fail_many,
    load_yaml_file,
    professional_automatic_routing_policy_fingerprint,
    validate_main_execution,
)


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "routing" / "cases.yaml"
CAPABILITY_CASES = ROOT / "evals" / "routing" / "capability-coverage-cases.yaml"
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

    pipeline_errors = route_once_pipeline_errors()
    if pipeline_errors:
        errors = [
            f"routing-integrity-failure: route-once pipeline: {error}"
            for error in pipeline_errors
        ]
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
            "results": [],
            "errors": errors,
        }
    errors: list[str] = []
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
        main_errors = validate_main_execution(main_execution)
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
        "results": results,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate hookless Skill routing.")
    parser.add_argument("--candidate-output-dir", type=Path)
    args = parser.parse_args()
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
    REPORT_JSON.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    REPORT_MD.write_text(_render_markdown(report), encoding="utf-8")
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
