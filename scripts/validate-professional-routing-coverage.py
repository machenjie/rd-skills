#!/usr/bin/env python3
"""Validate route-once coverage across Hookless skill registries and fixtures."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from capability_coverage import (
    EXPECTED_ADMISSION_COMBINATIONS,
    evaluate_admission_evidence,
)
from deterministic_route_oracle import ALL_DOMAIN_ROUTE_SPECS, DOMAIN_ROUTE_SPECS
from validation_utils import (
    DOMAIN_MODIFIER_ONLY_ROUTING_MODE,
    ValidationProblem,
    domain_modifier_routing_authority,
    domain_routing_mode_map,
    load_yaml_file,
    professional_automatic_routing_authority,
)


ROOT = Path(__file__).resolve().parents[1]
PROFILES = {"analysis-agent", "task-agent", "review-agent"}
ROUTING_EVALUATOR = ROOT / "scripts" / "eval-routing.py"
DOMAIN_VARIANTS = {"canonical", "paraphrase"}


def _canonical_domain_specs() -> dict[str, dict[str, Any]]:
    """Return modifier-only Domains governed by the canonical family suite."""

    return dict(DOMAIN_ROUTE_SPECS)


@dataclass
class CaseResult:
    case_id: str
    profile: str
    path: str
    primary_skill: str
    layer3_skills: list[str]
    review_skill: str
    excluded_skills: list[str]
    passed: bool
    domain_family: dict[str, str] | None
    domain_transition: dict[str, str] | None
    domain_anti: str | None
    domain_anti_variant: str | None
    errors: list[str] = field(default_factory=list)


ADMISSION_MISSING_PREFIX = (
    "capability admission evidence: missing obligations="
)


def main(argv: list[str] | None = None) -> int:
    args = _args(sys.argv[1:] if argv is None else argv)
    try:
        professional, layer3, domain_names = _registries()
        routing = _load_routing_evaluator().evaluate_routes(
            args.routing_dir / "cases.yaml"
        )
    except ValidationProblem as exc:
        print(f"validate-professional-routing-coverage: ERROR: {exc}", file=sys.stderr)
        return 1
    if not isinstance(routing, dict) or not isinstance(routing.get("results"), list):
        print(
            "validate-professional-routing-coverage: ERROR: fresh routing report is invalid",
            file=sys.stderr,
        )
        return 1
    results = [
        _case(raw, professional, layer3)
        for raw in routing["results"]
        if isinstance(raw, dict)
    ]
    errors = [f"{row.case_id}: {message}" for row in results for message in row.errors]
    errors.extend(
        f"fresh routing oracle: {message}"
        for message in _strings(routing.get("errors"))
        if not message.startswith(ADMISSION_MISSING_PREFIX)
    )
    if len(results) < 10:
        errors.append("routing suite must contain at least ten cases")
    ids = [row.case_id for row in results]
    if len(ids) != len(set(ids)):
        errors.append("routing case ids must be unique")

    coverage: list[dict[str, Any]] = []
    for name, entry in sorted(professional.items()):
        passing = [row for row in results if row.passed and not row.errors]
        primary = sum(row.primary_skill == name for row in passing)
        review = sum(row.review_skill == name for row in passing)
        negative = sum(name in row.excluded_skills for row in passing)
        task_routable = bool(entry.get("task_routable", True))
        if task_routable and primary + review == 0:
            errors.append(f"professional Skill '{name}' has no primary or review routing fixture")
        coverage.append(
            {
                "name": name,
                "role_support": _strings(entry.get("role_support")),
                "task_routable": task_routable,
                "primary_case_count": primary,
                "review_case_count": review,
                "negative_case_count": negative,
            }
        )
    layer3_counts = {
        name: sum(
            name in row.layer3_skills
            for row in results
            if row.passed and not row.errors
        )
        for name in sorted(layer3)
    }
    layer3_negative_counts = {
        name: sum(
            name in row.excluded_skills
            for row in results
            if row.passed and not row.errors
        )
        for name in sorted(layer3)
    }
    domain_family_coverage = _domain_family_coverage(results, domain_names)
    domain_transition_case_ids = {
        name: sorted(
            row.case_id
            for row in results
            if row.passed
            and not row.errors
            and row.domain_transition is not None
            and row.domain_transition.get("domain") == name
            and name in row.layer3_skills
        )
        for name in sorted(domain_names)
    }
    domain_unchanged_case_ids = {
        name: sorted(
            row.case_id
            for row in results
            if row.passed
            and not row.errors
            and row.domain_anti == name
            and row.domain_anti_variant == "unchanged-paraphrase"
            and name in row.excluded_skills
        )
        for name in sorted(domain_names)
    }
    errors.extend(
        _domain_coverage_errors(
            domain_names,
            layer3_counts,
            layer3_negative_counts,
            domain_family_coverage,
            domain_transition_case_ids,
            domain_unchanged_case_ids,
        )
    )
    admission_coverage = _admission_coverage()
    errors.extend(admission_coverage["errors"])
    payload = {
        "schema_version": 5,
        "architecture": "hookless-control-plane",
        "evaluation_kind": "fresh-actual-route-fixture-coverage",
        "routing_evidence_source": "eval-routing.evaluate_routes actual",
        "evidence_limitations": [
            "Fixture coverage does not prove live router precision or recall.",
            "No latency, context-size, accuracy, or adoption threshold is evaluated.",
        ],
        "routing_cases_checked": len(results),
        "professional_skills_checked": len(professional),
        "layer3_skills_checked": len(layer3),
        "errors": errors,
        "cases": [asdict(row) for row in results],
        "professional_coverage": coverage,
        "layer3_fixture_counts": layer3_counts,
        "layer3_negative_fixture_counts": layer3_negative_counts,
        "domain_family_coverage": domain_family_coverage,
        "domain_transition_case_ids": domain_transition_case_ids,
        "domain_unchanged_case_ids": domain_unchanged_case_ids,
        "admission_coverage": admission_coverage,
    }
    _write(args.reports_dir, payload)
    print(
        "validate-professional-routing-coverage: "
        f"cases={len(results)}; professional={len(professional)}; "
        f"layer3={len(layer3)}; errors={len(errors)}; evidence=fresh-actual-only"
    )
    for error in errors:
        print(f"validate-professional-routing-coverage: ERROR: {error}", file=sys.stderr)
    return 1 if errors else 0


def _admission_coverage() -> dict[str, Any]:
    """Return exact current admission coverage against registry obligations."""

    fixture_path = (
        ROOT / "evals" / "capability-coverage" / "admission-cases.yaml"
    )
    document = load_yaml_file(fixture_path)
    rows = (
        document.get("cases")
        if isinstance(document, dict)
        and isinstance(document.get("cases"), list)
        else []
    )
    passing_ids, evaluation_errors = evaluate_admission_evidence(root=ROOT)
    covered = {
        (
            str(row.get("layer")),
            str(row.get("skill")),
            str(row.get("case_kind")),
        )
        for row in rows
        if isinstance(row, dict)
        and isinstance(row.get("id"), str)
        and row["id"] in passing_ids
    }
    missing = sorted(EXPECTED_ADMISSION_COMBINATIONS - covered)
    non_inventory_errors = [
        error
        for error in evaluation_errors
        if not error.startswith(ADMISSION_MISSING_PREFIX)
    ]
    errors = list(non_inventory_errors)
    if missing:
        errors.append(
            "admission coverage missing obligations="
            f"{missing!r}"
        )
    return {
        "schema_version": 1,
        "evaluation_kind": "registry-derived-actual-route-admission",
        "expected_obligation_count": len(EXPECTED_ADMISSION_COMBINATIONS),
        "current_case_count": len(rows),
        "passing_case_count": len(passing_ids),
        "covered_obligation_count": len(covered),
        "missing_obligation_count": len(missing),
        "missing_obligations": [
            {
                "layer": layer,
                "skill": skill,
                "case_kind": case_kind,
            }
            for layer, skill, case_kind in missing
        ],
        "errors": errors,
    }


def _args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--routing-dir", type=Path, default=ROOT / "evals/routing")
    parser.add_argument("--benchmarks-dir", type=Path, default=ROOT / "evals/professional-benchmarks")
    parser.add_argument("--reports-dir", type=Path, default=ROOT / "reports")
    parser.add_argument("--baseline", type=Path, help="deprecated; Hookless coverage is current-fixture based")
    return parser.parse_args(argv)


def _load_routing_evaluator():
    """Load the shared deterministic evaluator without writing a report."""

    name = "professional_coverage_fresh_routing_evaluator"
    spec = importlib.util.spec_from_file_location(name, ROUTING_EVALUATOR)
    if spec is None or spec.loader is None:
        raise ValidationProblem(
            f"cannot load deterministic routing evaluator: {ROUTING_EVALUATOR}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _registries() -> tuple[
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    set[str],
]:
    professional_data = load_yaml_file(ROOT / "src/registry/professional-skills.yaml")
    foundation_data = load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
    domain_data = load_yaml_file(ROOT / "src/registry/domain-skills.yaml")
    if not all(isinstance(item, dict) for item in (professional_data, foundation_data, domain_data)):
        raise ValidationProblem("three-layer Skill registry documents must be mappings")
    professional_automatic_routing_authority(
        professional_data,
        "professional-skills.yaml",
    )
    domain_modifier_routing_authority(
        domain_data,
        professional_data,
    )
    professional = {
        str(row.get("name", "")): row
        for row in professional_data.get("professional_skills", [])
        if isinstance(row, dict)
    }
    layer3 = {
        str(row.get("name", "")): row
        for row in foundation_data.get("foundation_skills", [])
        if isinstance(row, dict)
    }
    domain = {
        str(row.get("name", "")): row
        for row in domain_data.get("domain_skills", [])
        if isinstance(row, dict)
    }
    modes = domain_routing_mode_map(domain_data)
    layer3.update(domain)
    canonical_names = set(_canonical_domain_specs())
    return professional, layer3, {
        name
        for name, mode in modes.items()
        if mode == DOMAIN_MODIFIER_ONLY_ROUTING_MODE and name in canonical_names
    }


def _domain_family_coverage(
    results: list[CaseResult],
    domain_names: set[str],
) -> list[dict[str, Any]]:
    """Project passing actual routes into Domain family and variant evidence."""

    rows: list[dict[str, Any]] = []
    for domain in sorted(domain_names):
        spec = DOMAIN_ROUTE_SPECS.get(domain, {})
        families = spec.get("families", {}) if isinstance(spec, dict) else {}
        for family in sorted(families):
            case_ids_by_variant = {
                variant: sorted(
                    row.case_id
                    for row in results
                    if row.passed
                    and not row.errors
                    and row.domain_family
                    == {
                        "domain": domain,
                        "family": family,
                        "variant": variant,
                    }
                    and domain in row.layer3_skills
                )
                for variant in sorted(DOMAIN_VARIANTS)
            }
            rows.append(
                {
                    "domain": domain,
                    "family": family,
                    "required_variants": sorted(DOMAIN_VARIANTS),
                    "case_ids_by_variant": case_ids_by_variant,
                    "passing_case_count": sum(
                        len(case_ids) for case_ids in case_ids_by_variant.values()
                    ),
                }
            )
    return rows


def _domain_coverage_errors(
    domain_names: set[str],
    positive_counts: dict[str, int],
    negative_counts: dict[str, int],
    family_coverage: list[dict[str, Any]] | None = None,
    transition_case_ids: dict[str, list[str]] | None = None,
    unchanged_case_ids: dict[str, list[str]] | None = None,
) -> list[str]:
    """Require actual family, transition, and unchanged anti-route evidence."""

    errors: list[str] = []
    canonical_specs = _canonical_domain_specs()
    spec_names = set(canonical_specs)
    if spec_names != domain_names:
        errors.append(
            "Domain routing oracle names differ from Registry; "
            f"missing={sorted(domain_names - spec_names)}; "
            f"extra={sorted(spec_names - domain_names)}"
        )
    for name in sorted(domain_names):
        if positive_counts.get(name, 0) == 0:
            errors.append(
                f"Domain Skill '{name}' has no positive Layer 3 routing fixture"
            )
        if negative_counts.get(name, 0) == 0:
            errors.append(
                f"Domain Skill '{name}' has no negative anti-route fixture"
            )
        if transition_case_ids is not None and not transition_case_ids.get(name):
            errors.append(
                f"Domain Skill '{name}' has no passing actual transition route fixture"
            )
        if unchanged_case_ids is not None and not unchanged_case_ids.get(name):
            errors.append(
                f"Domain Skill '{name}' has no passing unchanged-paraphrase control"
            )
    if family_coverage is None:
        return errors
    actual_family_keys = {
        (str(row.get("domain", "")), str(row.get("family", "")))
        for row in family_coverage
        if isinstance(row, dict)
    }
    expected_family_keys = {
        (domain, family)
        for domain, spec in canonical_specs.items()
        for family in spec["families"]
    }
    if actual_family_keys != expected_family_keys:
        errors.append(
            "Domain family coverage keys differ from the deterministic oracle"
        )
    for row in family_coverage:
        domain = str(row.get("domain", ""))
        family = str(row.get("family", ""))
        case_ids = row.get("case_ids_by_variant")
        if not isinstance(case_ids, dict):
            errors.append(f"{domain}/{family}: family evidence is invalid")
            continue
        for variant in sorted(DOMAIN_VARIANTS):
            values = case_ids.get(variant)
            if not isinstance(values, list) or not values:
                errors.append(
                    f"{domain}/{family}: no passing actual {variant} route fixture"
                )
    return errors


def _case(
    raw: dict[str, Any],
    professional: dict[str, dict[str, Any]],
    layer3: dict[str, dict[str, Any]],
) -> CaseResult:
    actual = raw.get("actual") if isinstance(raw.get("actual"), dict) else {}
    raw_family = raw.get("domain_family")
    domain_family = (
        {key: str(raw_family.get(key, "")).strip() for key in ("domain", "family", "variant")}
        if isinstance(raw_family, dict)
        else None
    )
    raw_transition = raw.get("domain_transition")
    domain_transition = (
        {key: str(raw_transition.get(key, "")).strip() for key in ("domain", "family")}
        if isinstance(raw_transition, dict)
        else None
    )
    raw_anti = raw.get("domain_anti")
    domain_anti = raw_anti.strip() if isinstance(raw_anti, str) else None
    raw_anti_variant = raw.get("domain_anti_variant")
    domain_anti_variant = (
        raw_anti_variant.strip() if isinstance(raw_anti_variant, str) else None
    )
    result = CaseResult(
        case_id=str(raw.get("id", "")).strip() or "<missing-id>",
        profile=str(actual.get("profile", "")).strip(),
        path=str(actual.get("path", "")).strip(),
        primary_skill=str(actual.get("primary_skill", "")).strip(),
        layer3_skills=_strings(actual.get("layer3_skills")),
        review_skill=str(actual.get("review_skill", "")).strip(),
        excluded_skills=_strings(raw.get("excluded_skills")),
        passed=raw.get("passed") is True,
        domain_family=domain_family,
        domain_transition=domain_transition,
        domain_anti=domain_anti,
        domain_anti_variant=domain_anti_variant,
    )
    if raw.get("passed") is not True:
        route_errors = _strings(raw.get("errors"))
        result.errors.append(
            "fresh route did not pass"
            + (": " + "; ".join(route_errors) if route_errors else "")
        )
    if not actual:
        result.errors.append("fresh route result lacks actual output")
    raw_excluded = raw.get("excluded_skills", [])
    if not isinstance(raw_excluded, list):
        result.errors.append("excluded_skills must be a list")
    elif not all(isinstance(item, str) and item.strip() for item in raw_excluded):
        result.errors.append("excluded_skills must contain non-blank Skill names")
    if len(result.excluded_skills) != len(set(result.excluded_skills)):
        result.errors.append("excluded_skills must be unique")
    if result.profile not in PROFILES:
        result.errors.append(f"invalid dispatched profile '{result.profile}'")
    if result.path not in {"direct", "analyzed"}:
        result.errors.append(f"invalid path '{result.path}'")
    elif result.path == "analyzed" and result.profile != "analysis-agent":
        result.errors.append("Analyzed Work must start with analysis-agent")
    elif result.path == "direct" and result.profile not in {"task-agent", "review-agent"}:
        result.errors.append("Direct work must start with task-agent or review-agent")
    primary = professional.get(result.primary_skill)
    if primary is None:
        result.errors.append(f"unknown primary Professional Skill '{result.primary_skill}'")
    elif not bool(primary.get("task_routable", True)):
        result.errors.append(f"primary Professional Skill is not task-routable: '{result.primary_skill}'")
    elif result.profile not in _strings(primary.get("role_support")):
        result.errors.append(
            f"profile '{result.profile}' is not supported by primary Skill '{result.primary_skill}'"
        )
    if len(result.layer3_skills) > 3:
        result.errors.append("route selects more than three Layer 3 Skills without a fixture-specific risk rationale")
    if len(result.layer3_skills) != len(set(result.layer3_skills)):
        result.errors.append("Layer 3 Skills must be unique")
    for name in result.layer3_skills:
        if name not in layer3:
            result.errors.append(f"unknown Layer 3 Skill '{name}'")
        elif primary is not None and name not in _strings(primary.get("layer3_candidates")):
            result.errors.append(
                f"Layer 3 Skill '{name}' is not targeted by '{result.primary_skill}'"
            )
        elif result.profile not in _strings(layer3[name].get("role_support")):
            result.errors.append(
                f"Layer 3 Skill '{name}' does not support profile '{result.profile}'"
            )
    review = professional.get(result.review_skill)
    if review is None:
        result.errors.append(f"unknown Review Skill '{result.review_skill}'")
    elif "review-agent" not in _strings(review.get("role_support")):
        result.errors.append(f"Review Skill '{result.review_skill}' does not support review-agent")
    if result.primary_skill == "routing-quality-review":
        result.errors.append("compatibility router cannot own a product task")
    known = set(professional) | set(layer3)
    unknown_excluded = sorted(set(result.excluded_skills) - known)
    if unknown_excluded:
        result.errors.append(
            "excluded_skills contains unknown Skill(s): " + ", ".join(unknown_excluded)
        )
    selected = {
        result.primary_skill,
        result.review_skill,
        *result.layer3_skills,
    }
    selected_excluded = sorted(selected & set(result.excluded_skills))
    if selected_excluded:
        result.errors.append(
            "selected route contains explicitly excluded Skill(s): "
            + ", ".join(selected_excluded)
        )
    if result.domain_family is not None:
        domain = result.domain_family["domain"]
        family = result.domain_family["family"]
        variant = result.domain_family["variant"]
        spec = ALL_DOMAIN_ROUTE_SPECS.get(domain)
        if spec is None or family not in spec["families"]:
            result.errors.append("fresh route carries unknown Domain family metadata")
        if variant not in DOMAIN_VARIANTS:
            result.errors.append("fresh route carries unknown Domain variant metadata")
        if domain not in result.layer3_skills:
            result.errors.append(
                f"fresh actual route omits declared Domain family owner '{domain}'"
            )
    if result.domain_transition is not None:
        domain = result.domain_transition["domain"]
        family = result.domain_transition["family"]
        spec = ALL_DOMAIN_ROUTE_SPECS.get(domain)
        if spec is None or family not in spec["families"]:
            result.errors.append("fresh route carries unknown Domain transition metadata")
        if domain not in result.layer3_skills:
            result.errors.append(
                f"fresh actual route omits declared Domain transition owner '{domain}'"
            )
    if result.domain_anti is not None:
        if result.domain_anti not in ALL_DOMAIN_ROUTE_SPECS:
            result.errors.append("fresh route carries unknown Domain anti-route metadata")
        if result.domain_anti not in result.excluded_skills:
            result.errors.append(
                "fresh Domain anti-route is not present in excluded_skills"
            )
    if result.domain_anti_variant is not None:
        if result.domain_anti is None:
            result.errors.append("fresh Domain anti variant lacks a Domain anti-route")
        elif result.domain_anti_variant != "unchanged-paraphrase":
            result.errors.append("fresh route carries unknown Domain anti variant")
    return result


def _write(directory: Path, payload: dict[str, Any]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "professional-routing-coverage.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        "# Hookless Professional Routing Coverage",
        "",
        "> Fresh deterministic actual-route coverage only; no live precision, recall, latency, or adoption claim is made.",
        "",
        f"- Routing evidence: `{payload['routing_evidence_source']}`",
        f"- Routing cases: {payload['routing_cases_checked']}",
        f"- Professional Skills: {payload['professional_skills_checked']}",
        f"- Layer 3 Skills: {payload['layer3_skills_checked']}",
        f"- Errors: {len(payload['errors'])}",
        "",
        "| Professional Skill | Profiles | Task routable | Primary cases | Review cases | Negative cases |",
        "|---|---|---|---:|---:|---:|",
    ]
    for row in payload["professional_coverage"]:
        lines.append(
            f"| `{row['name']}` | {', '.join(row['role_support'])} | "
            f"{str(row['task_routable']).lower()} | {row['primary_case_count']} | "
            f"{row['review_case_count']} | {row['negative_case_count']} |"
        )
    lines.extend(
        [
            "",
            "## Domain Family Coverage",
            "",
            "| Domain | Family | Canonical actual cases | Paraphrase actual cases |",
            "|---|---|---|---|",
        ]
    )
    for row in payload["domain_family_coverage"]:
        cases = row["case_ids_by_variant"]
        lines.append(
            f"| `{row['domain']}` | `{row['family']}` | "
            f"{', '.join(cases['canonical']) or '-'} | "
            f"{', '.join(cases['paraphrase']) or '-'} |"
        )
    lines.extend(
        [
            "",
            "## Domain Transition and Unchanged Controls",
            "",
            "| Domain | Transition actual cases | Unchanged excluded cases |",
            "|---|---|---|",
        ]
    )
    for domain in sorted(payload["domain_transition_case_ids"]):
        lines.append(
            f"| `{domain}` | "
            f"{', '.join(payload['domain_transition_case_ids'][domain]) or '-'} | "
            f"{', '.join(payload['domain_unchanged_case_ids'][domain]) or '-'} |"
        )
    if payload["errors"]:
        lines.extend(["", "## Errors", ""] + [f"- {item}" for item in payload["errors"]])
    (directory / "professional-routing-coverage.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _strings(value: Any) -> list[str]:
    return [str(item).strip() for item in value if str(item).strip()] if isinstance(value, list) else []


if __name__ == "__main__":
    raise SystemExit(main())
