#!/usr/bin/env python3
"""Statically evaluate Hookless ChangeForge skills for AI execution quality.

The evaluator checks source and registry contracts only.  It does not run an
agent and therefore must not be cited as product-accuracy, latency, or adoption
evidence.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Any

from validation_utils import (
    CORE_CONTRACTS,
    ValidationProblem,
    empty_markdown_headings,
    load_yaml_file,
    load_professional_coverage_policy,
    parse_frontmatter,
    professional_review_skill_ids,
    reference_paths,
)


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
DEFAULT_RELEASE_REVIEW_CONFIG = ROOT / "config/professionalism-release-review.yaml"
ROUTING_EVALUATOR = ROOT / "scripts/eval-routing.py"
BENCHMARK_EVALUATOR = ROOT / "scripts/eval-professional-benchmarks.py"
PRESSURE_EVALUATOR = ROOT / "scripts/eval-pressure-behavior.py"
CAPABILITY_ROUTING_FIXTURES = (
    ROOT / "evals/routing/capability-coverage-cases.yaml"
)

REGISTRIES = (
    ("control", ROOT / "src/registry/control-skills.yaml", "control_skills"),
    ("professional", ROOT / "src/registry/professional-skills.yaml", "professional_skills"),
    ("foundation", ROOT / "src/registry/foundation-skills.yaml", "foundation_skills"),
    ("domain", ROOT / "src/registry/domain-skills.yaml", "domain_skills"),
)

PROFESSIONAL_DOMAIN_SECTIONS = (
    "Role",
    "When To Use",
    "Do Not Use",
    "Required Inputs",
    "Professional Decision Rules",
    "High-Value Gotchas",
    "Execution Checklist",
    "Stop / Escalation Conditions",
    "Output Contract",
    "Targeted References",
)
FOUNDATION_SECTIONS = (
    "Registry Trigger",
    "Skill Role",
    "High-Value Rules",
    "Anti-Patterns",
    "Targeted References",
)
CONTROL_SECTIONS = (
    "Role",
    "Decision Rules",
    "Targeted References",
    "Stop and Escalate",
    "Output Contract",
)
REGISTRY_FIELDS = (
    "name",
    "path",
    "role_support",
    "trigger_signals",
    "anti_trigger_signals",
    "required_inputs",
    "output_contract",
    "escalation_signals",
    "reference_index",
)


@dataclass
class SkillResult:
    name: str
    kind: str
    path: str
    status: str
    authoring_score: int
    required_sections: list[str]
    missing_sections: list[str] = field(default_factory=list)
    missing_registry_fields: list[str] = field(default_factory=list)
    broken_references: list[str] = field(default_factory=list)
    unlinked_references: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    role_support: list[str] = field(default_factory=list)
    trigger_signals: list[str] = field(default_factory=list)
    anti_trigger_signals: list[str] = field(default_factory=list)
    layer3_candidates: list[str] = field(default_factory=list)
    line_count: int = 0
    decision_rule_count: int = 0
    gotcha_count: int = 0
    reference_count: int = 0
    routing_coverage_count: int = 0
    benchmark_coverage_count: int = 0


def main(argv: list[str] | None = None) -> int:
    args = _args(sys.argv[1:] if argv is None else argv)
    try:
        entries = _load_entries()
    except ValidationProblem as exc:
        print(f"eval-skill-professionalism: ERROR: {exc}", file=sys.stderr)
        return 1

    results = [_evaluate(kind, entry) for kind, entry in entries]
    professional_entries = [entry for kind, entry in entries if kind == "professional"]
    try:
        review_skill_ids = professional_review_skill_ids(
            professional_entries,
            CORE_CONTRACTS["review_discipline_contract"]["professional_risk_matrix"],
        )
    except ValidationProblem as exc:
        print(f"eval-skill-professionalism: ERROR: {exc}", file=sys.stderr)
        return 1
    try:
        coverage = build_coverage_matrix(
            args.release_review_config,
            results=results,
        )
    except ValidationProblem as exc:
        print(f"eval-skill-professionalism: ERROR: {exc}", file=sys.stderr)
        return 1
    errors = [f"{row.path}: {message}" for row in results for message in row.errors]
    warnings = [f"{row.path}: {message}" for row in results for message in row.warnings]
    payload = {
        "schema_version": 2,
        "architecture": "hookless-control-plane",
        "evaluation_kind": "static-authoring-structure",
        "evidence_limitations": [
            "No model or agent was executed.",
            "Scores measure source and registry completeness, not engineering accuracy.",
            "Efficiency and adoption thresholds are not evaluated by this command.",
        ],
        "skills_checked": len(results),
        "counts_by_kind": {
            kind: sum(row.kind == kind for row in results)
            for kind in ("control", "professional", "foundation", "domain")
        },
        "error_count": len(errors),
        "warning_count": len(warnings),
        "professional_review_risk_matrix": {
            "selector": "professional-skills.yaml role_support contains review-agent",
            "covered_skill_count": len(review_skill_ids),
            "covered_skill_ids": list(review_skill_ids),
        },
        "errors": errors,
        "warnings": warnings,
        "results": [asdict(row) for row in results],
    }

    reports_dir = args.reports_dir or REPORTS
    reports_dir.mkdir(parents=True, exist_ok=True)
    if args.coverage_matrix:
        _write_coverage(reports_dir, coverage)
    else:
        _write_primary(reports_dir, payload)
        _write_depth(reports_dir, payload)
        _write_coverage(reports_dir, coverage)

    print(
        "eval-skill-professionalism: "
        f"checked {len(results)} skills; errors={len(errors)}; "
        f"coverage_errors={len(coverage['errors'])}; warnings={len(warnings)}; "
        "evidence=static-only"
    )
    for error in errors:
        print(f"eval-skill-professionalism: ERROR: {error}", file=sys.stderr)
    for error in coverage["errors"]:
        print(f"eval-skill-professionalism: ERROR: {error}", file=sys.stderr)
    return 1 if errors or coverage["errors"] else 0


def _args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports-dir", type=Path)
    parser.add_argument(
        "--release-review-config",
        type=Path,
        default=DEFAULT_RELEASE_REVIEW_CONFIG,
    )
    parser.add_argument(
        "--coverage-matrix",
        action="store_true",
        help="write only the Layer 1/2/3 coverage matrix reports",
    )
    # Kept for release scripts that previously selected report formats.
    parser.add_argument("--format", choices=("all", "markdown", "json"), default="all")
    return parser.parse_args(argv)


def _load_entries() -> list[tuple[str, dict[str, Any]]]:
    rows: list[tuple[str, dict[str, Any]]] = []
    names: set[str] = set()
    for kind, path, key in REGISTRIES:
        data = load_yaml_file(path)
        if not isinstance(data, dict) or not isinstance(data.get(key), list):
            raise ValidationProblem(f"{path}: expected top-level list '{key}'")
        for raw in data[key]:
            if not isinstance(raw, dict):
                raise ValidationProblem(f"{path}: entries in '{key}' must be mappings")
            name = str(raw.get("name", "")).strip()
            if not name:
                raise ValidationProblem(f"{path}: registry entry is missing name")
            if name in names:
                raise ValidationProblem(f"{path}: duplicate registered skill '{name}'")
            names.add(name)
            rows.append((kind, raw))
    return rows


def _evaluate(kind: str, entry: dict[str, Any]) -> SkillResult:
    name = str(entry.get("name", "")).strip()
    source_dir = ROOT / str(entry.get("path", ""))
    source = source_dir / "SKILL.md"
    if kind == "control":
        required = CONTROL_SECTIONS
    elif kind == "foundation":
        required = FOUNDATION_SECTIONS
    else:
        required = PROFESSIONAL_DOMAIN_SECTIONS
    result = SkillResult(
        name=name,
        kind=kind,
        path=_rel(source),
        status="pass",
        authoring_score=0,
        required_sections=list(required),
        role_support=_strings(entry.get("role_support")),
        trigger_signals=_strings(entry.get("trigger_signals")),
        anti_trigger_signals=_strings(entry.get("anti_trigger_signals")),
        layer3_candidates=_strings(entry.get("layer3_candidates")),
    )
    result.missing_registry_fields = [
        field
        for field in REGISTRY_FIELDS
        if field not in entry or (field != "reference_index" and not _present(entry.get(field)))
    ]
    if result.missing_registry_fields:
        result.errors.append(
            "registry contract missing: " + ", ".join(result.missing_registry_fields)
        )
    if not source.is_file():
        result.errors.append("registered SKILL.md does not exist")
        result.status = "fail"
        return result

    text = source.read_text(encoding="utf-8")
    result.line_count = len(text.splitlines())
    try:
        frontmatter, _raw_frontmatter, body = parse_frontmatter(source)
    except ValidationProblem as exc:
        result.errors.append(str(exc))
        result.status = "fail"
        return result
    if set(frontmatter) != {"name", "description"}:
        result.errors.append("frontmatter must contain only name and description")
    if str(frontmatter.get("name", "")).strip() != name:
        result.errors.append("frontmatter name does not match registry name")

    sections = _sections(body, required)
    headings = set(re.findall(r"^##\s+(.+?)\s*$", body, flags=re.MULTILINE))
    result.missing_sections = [section for section in required if section not in headings]
    if result.missing_sections:
        result.errors.append("missing AI execution sections: " + ", ".join(result.missing_sections))
    empty_headings = empty_markdown_headings(body)
    if empty_headings:
        details = ", ".join(
            f"{title} (line {line_number})"
            for line_number, _level, title in empty_headings
        )
        result.errors.append("empty Markdown sections: " + details)
    result.decision_rule_count = sum(
        _list_count(sections.get(title, ""))
        for title in ("Decision Rules", "Professional Decision Rules", "High-Value Rules")
    )
    result.gotcha_count = sum(
        _list_count(sections.get(title, ""))
        for title in ("High-Value Gotchas", "Anti-Patterns")
    )

    indexed = reference_paths(
        entry.get("reference_index"), f"{kind}:{name}.reference_index", owner=name
    )
    result.reference_count = len(indexed)
    for relative in indexed:
        target = source_dir / relative
        if not target.is_file():
            result.broken_references.append(relative)
        if relative not in body:
            result.unlinked_references.append(relative)
    if result.broken_references:
        result.errors.append("missing targeted references: " + ", ".join(result.broken_references))
    if result.unlinked_references:
        result.warnings.append(
            "registry references are not directly linked from root SKILL.md: "
            + ", ".join(result.unlinked_references)
        )

    if kind == "foundation" and result.decision_rule_count < 2:
        result.warnings.append("fewer than two explicit High-Value Rules")
    elif kind != "control" and result.decision_rule_count < 2:
        result.warnings.append("fewer than two explicit Professional Decision Rules")
    if kind == "foundation" and result.gotcha_count < 1:
        result.warnings.append("Anti-Patterns has no explicit list item")
    elif kind != "control" and result.gotcha_count < 1:
        result.warnings.append("High-Value Gotchas has no explicit list item")
    if kind != "control" and result.line_count > 120:
        result.warnings.append(f"root SKILL.md has {result.line_count} lines; targeted-reference split should be reviewed")
    section_defects = min(
        len(required),
        len(result.missing_sections) + len(empty_headings),
    )
    section_points = round(60 * (len(required) - section_defects) / len(required))
    registry_points = round(20 * (len(REGISTRY_FIELDS) - len(result.missing_registry_fields)) / len(REGISTRY_FIELDS))
    reference_points = 10 if not result.broken_references and not result.unlinked_references else 0
    concise_points = 10 if kind == "control" or result.line_count <= 120 else 5
    result.authoring_score = section_points + registry_points + reference_points + concise_points
    result.status = "fail" if result.errors else ("needs-review" if result.warnings else "pass")
    return result


def _sections(body: str, required: tuple[str, ...]) -> dict[str, str]:
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", body, flags=re.MULTILINE))
    all_sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        all_sections[match.group(1).strip()] = body[start:end].strip()
    return {title: all_sections.get(title, "") for title in required}


def _list_count(text: str) -> int:
    return len(re.findall(r"^(?:\s*[-*]|\s*\d+\.)\s+\S", text, flags=re.MULTILINE))


def build_coverage_matrix(
    release_review_config: Path = DEFAULT_RELEASE_REVIEW_CONFIG,
    *,
    results: list[SkillResult] | None = None,
) -> dict[str, Any]:
    """Build deterministic coverage evidence without reading tracked reports."""

    if results is None:
        results = [_evaluate(kind, entry) for kind, entry in _load_entries()]
    known_skills = {row.name for row in results}
    policy = load_professional_coverage_policy(
        release_review_config,
        known_skills=known_skills,
    )

    routing_evaluator = _load_evaluator(
        ROUTING_EVALUATOR,
        "skill_professionalism_routing_evaluator",
    )
    routing = routing_evaluator.evaluate_routes()
    capability_routes = routing_evaluator.evaluate_routes(
        CAPABILITY_ROUTING_FIXTURES,
        _validate_capability_matrix=False,
    )
    benchmarks = _load_evaluator(
        BENCHMARK_EVALUATOR,
        "skill_professionalism_benchmark_evaluator",
    ).evaluate_benchmarks()
    pressure = _load_evaluator(
        PRESSURE_EVALUATOR,
        "skill_professionalism_pressure_evaluator",
    ).evaluate_pressure_cases()
    source_errors = [
        *[f"routing: {item}" for item in _strings(routing.get("errors"))],
        *[
            f"capability routing: {item}"
            for item in _strings(capability_routes.get("errors"))
        ],
        *[f"benchmarks: {item}" for item in _strings(benchmarks.get("errors"))],
        *[f"pressure: {item}" for item in _strings(pressure.get("errors"))],
    ]

    evidence_by_skill: dict[str, dict[str, list[str]]] = {
        name: {
            "positive_route": [],
            "negative_route": [],
            "behavior": [],
            "pressure": [],
            "release_critical": [],
            "adversarial_negative_control": [],
        }
        for name in known_skills
    }
    for case in routing.get("results", []):
        if not isinstance(case, dict) or case.get("passed") is not True:
            continue
        actual = _mapping(case.get("actual"))
        selected = {
            str(actual.get("primary_skill", "")),
            str(actual.get("review_skill", "")),
            *_strings(actual.get("layer3_skills")),
        }
        case_id = str(case.get("id", "")).strip()
        for name in selected & known_skills:
            evidence_by_skill[name]["positive_route"].append(case_id)
        for name in set(_strings(case.get("excluded_skills"))) & known_skills:
            evidence_by_skill[name]["negative_route"].append(case_id)

    for case in benchmarks.get("results", []):
        if not isinstance(case, dict):
            continue
        selected = {
            str(case.get("primary_skill", "")),
            *_strings(case.get("layer3_skills")),
        }
        selected &= known_skills
        case_id = str(case.get("case_id", "")).strip()
        positive = (
            case.get("expected_status") == "pass"
            and case.get("schema_status") == "pass"
            and case.get("comparison_status") == "pass"
            and not _strings(case.get("forbidden_behavior_hits"))
        )
        adversarial = (
            case.get("expected_status") == "fail"
            and case.get("comparison_status") == "expected-fail-detected"
        )
        if positive:
            for name in selected:
                evidence_by_skill[name]["behavior"].append(case_id)
                if case.get("coverage_class") == "release-critical":
                    evidence_by_skill[name]["release_critical"].append(case_id)
        elif adversarial:
            for name in selected:
                evidence_by_skill[name]["adversarial_negative_control"].append(case_id)

    for case in pressure.get("results", []):
        if not isinstance(case, dict) or case.get("status") != "pass":
            continue
        # A named reviewer is only a planned handoff in the current fixture schema;
        # it does not prove that review behavior executed under pressure.
        selected = {
            str(case.get("primary_skill", "")),
            *_strings(case.get("layer3_skills")),
        }
        case_id = str(case.get("case_id", "")).strip()
        for name in selected & known_skills:
            evidence_by_skill[name]["pressure"].append(case_id)

    rows: list[dict[str, Any]] = []
    for result in results:
        evidence = {
            key: sorted(set(values))
            for key, values in evidence_by_skill[result.name].items()
        }
        result.routing_coverage_count = len(evidence["positive_route"])
        result.benchmark_coverage_count = len(evidence["behavior"])
        states = {
            "registered": True,
            "route_covered": bool(evidence["positive_route"]),
            "negative_route_covered": bool(evidence["negative_route"]),
            "behavior_covered": bool(evidence["behavior"]),
            "pressure_covered": bool(evidence["pressure"]),
            "release_critical_covered": bool(evidence["release_critical"]),
        }
        required = list(policy["requirements"].get(result.name, []))
        unmet = [name for name in required if not states[name]]
        gate_status = (
            "not-required"
            if not required
            else ("pass" if not unmet else "fail")
        )
        rows.append(
            {
                "name": result.name,
                "layer": result.kind,
                "role_support": result.role_support,
                "trigger_contract": "present" if result.trigger_signals else "missing",
                "anti_trigger_contract": (
                    "present" if result.anti_trigger_signals else "missing"
                ),
                "layer3_candidates": result.layer3_candidates,
                "authoring_status": result.status,
                "evidence_case_ids": evidence,
                "evidence_counts": {
                    key: len(values) for key, values in evidence.items()
                },
                "coverage_states": states,
                "required_states": required,
                "unmet_required_states": unmet,
                "coverage_gate_status": gate_status,
            }
        )

    return {
        "schema_version": 3,
        "architecture": "hookless-control-plane",
        "evaluation_kind": "deterministic-coverage-evidence",
        "evidence_limitations": [
            "Registered means Registry presence only; authoring_status reports static source quality separately.",
            "Route coverage uses deterministic fixtures and does not prove live router precision or recall.",
            "Behavior and release-critical coverage use checked-in captured outputs and phrase obligations, not fresh model runs.",
            "Pressure coverage counts executed primary and Layer 3 fixture roles, not a merely declared reviewer.",
            "No wall-clock performance, production accuracy, or installed user experience is proved.",
        ],
        "state_definitions": {
            "registered": "present in the owning source Registry",
            "route_covered": "selected by at least one passing deterministic route",
            "negative_route_covered": "explicitly excluded by at least one passing deterministic route",
            "behavior_covered": "selected by at least one passing positive captured benchmark with no forbidden behavior hit",
            "pressure_covered": "executed as primary or selected Layer 3 in at least one passing pressure fixture",
            "release_critical_covered": "selected by at least one passing release-critical benchmark",
        },
        "coverage_policy": {
            "source": _rel(release_review_config),
            "decision_id": policy["id"],
            "decision_schema_version": policy["schema_version"],
            "fingerprint": policy["fingerprint"],
            "required_skill_count": len(policy["requirements"]),
        },
        "errors": source_errors,
        "gate_summary": {
            "required_skill_count": sum(bool(row["required_states"]) for row in rows),
            "pass_count": sum(row["coverage_gate_status"] == "pass" for row in rows),
            "fail_count": sum(row["coverage_gate_status"] == "fail" for row in rows),
            "not_required_count": sum(
                row["coverage_gate_status"] == "not-required" for row in rows
            ),
        },
        "rows": rows,
    }


@lru_cache(maxsize=3)
def _load_evaluator(path: Path, module_name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ValidationProblem(f"cannot load evaluator: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _write_primary(directory: Path, payload: dict[str, Any]) -> None:
    (directory / "skill-professionalism-eval.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        "# Hookless Skill Professionalism Evaluation",
        "",
        "> Static authoring evidence only. No agent was executed and no efficiency or adoption claim is made.",
        "",
        f"- Skills checked: {payload['skills_checked']}",
        f"- Errors: {payload['error_count']}",
        f"- Warnings: {payload['warning_count']}",
        "",
        "| Layer | Skill | Score | Authoring status | Route cases | Benchmark cases |",
        "|---|---|---:|---|---:|---:|",
    ]
    for row in payload["results"]:
        lines.append(
            f"| {row['kind']} | `{row['name']}` | {row['authoring_score']} | "
            f"{row['status']} | {row['routing_coverage_count']} | {row['benchmark_coverage_count']} |"
        )
    if payload["errors"]:
        lines.extend(["", "## Errors", ""] + [f"- {item}" for item in payload["errors"]])
    if payload["warnings"]:
        lines.extend(["", "## Warnings", ""] + [f"- {item}" for item in payload["warnings"]])
    (directory / "skill-professionalism-eval.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_depth(directory: Path, payload: dict[str, Any]) -> None:
    depth = {
        "schema_version": 2,
        "evaluation_kind": "static-authoring-depth",
        "score_semantics": "section, registry, reference, and root-concision completeness; not model performance",
        "errors": payload["errors"],
        "results": [
            {
                "name": row["name"],
                "kind": row["kind"],
                "path": row["path"],
                "total_score": row["authoring_score"],
                "status": row["status"],
                "decision_rule_count": row["decision_rule_count"],
                "gotcha_count": row["gotcha_count"],
                "line_count": row["line_count"],
            }
            for row in payload["results"]
        ],
    }
    (directory / "skill-professionalism-depth.json").write_text(
        json.dumps(depth, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        "# Hookless Skill Authoring Depth",
        "",
        "> Scores are static completeness heuristics; they are not accuracy or adoption evidence.",
        "",
        "| Skill | Layer | Score | Rules | Gotchas / Anti-patterns | Root lines |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in depth["results"]:
        lines.append(
            f"| `{row['name']}` | {row['kind']} | {row['total_score']} | "
            f"{row['decision_rule_count']} | {row['gotcha_count']} | {row['line_count']} |"
        )
    (directory / "skill-professionalism-depth.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_coverage(directory: Path, coverage: dict[str, Any]) -> None:
    (directory / "professional-coverage-matrix.json").write_text(
        json.dumps(coverage, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        "# Hookless Professional Coverage Matrix",
        "",
        "> Coverage is deterministic and captured-fixture evidence, not observed production or live-agent performance.",
        "",
        f"- Required Skills: {coverage['gate_summary']['required_skill_count']}",
        f"- Coverage gate failures: {coverage['gate_summary']['fail_count']}",
        f"- Source errors: {len(coverage['errors'])}",
        "",
        "| Layer | Skill | Authoring | +Route | -Route | Behavior | Pressure | Release-critical | Coverage gate |",
        "|---|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in coverage["rows"]:
        counts = row["evidence_counts"]
        lines.append(
            f"| {row['layer']} | `{row['name']}` | {row['authoring_status']} | "
            f"{counts['positive_route']} | {counts['negative_route']} | "
            f"{counts['behavior']} | {counts['pressure']} | "
            f"{counts['release_critical']} | {row['coverage_gate_status']} |"
        )
    if coverage["errors"]:
        lines.extend(["", "## Errors", ""] + [f"- {item}" for item in coverage["errors"]])
    (directory / "professional-coverage-matrix.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _strings(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _present(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return value is not None


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
