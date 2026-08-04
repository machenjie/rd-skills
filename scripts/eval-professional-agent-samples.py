#!/usr/bin/env python3
"""Evaluate captured Hookless professional-agent handoff samples.

Samples are checked-in, human-reviewed fixtures.  They are never represented as
fresh live-agent evidence.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from validation_utils import ValidationProblem, load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
HANDOFF_FIELDS = (
    "result",
    "changed_files",
    "commands_run",
    "validation_results",
    "findings",
    "unverified_scope",
    "residual_risk",
    "recommended_next_step",
)
DISPATCHED_PROFILES = {"analysis-agent", "task-agent", "review-agent"}


@dataclass
class SampleResult:
    sample_id: str
    path: str
    promotion_status: str
    status: str = "fail"
    profile: str = ""
    primary_skill: str = ""
    layer3_skills: list[str] = field(default_factory=list)
    review_skill: str = ""
    obligations_covered: list[str] = field(default_factory=list)
    missing_obligations: list[str] = field(default_factory=list)
    forbidden_hits: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def main(argv: list[str] | None = None) -> int:
    args = _args(sys.argv[1:] if argv is None else argv)
    try:
        professional, layer3 = _registries()
    except ValidationProblem as exc:
        print(f"eval-professional-agent-samples: ERROR: {exc}", file=sys.stderr)
        return 1
    paths = sorted(
        path for path in args.samples_dir.rglob("*.yaml") if "raw" not in path.parts
    )
    results: list[SampleResult] = []
    for path in paths:
        data = load_yaml_file(path)
        if not isinstance(data, dict):
            continue
        promotion = str(_mapping(data.get("review")).get("promotion_status", "candidate"))
        if args.promoted_only and promotion != "promoted":
            continue
        if args.candidates_only and promotion != "candidate":
            continue
        results.append(_sample(path, data, professional, layer3))
    errors = [f"{row.path}: {message}" for row in results for message in row.errors]
    if args.strict:
        if args.promoted_only and len(results) < 2:
            errors.append("strict promoted evaluation requires at least two promoted samples")
        if not results:
            errors.append("strict evaluation selected no samples")
    payload = {
        "schema_version": 2,
        "architecture": "hookless-control-plane",
        "evaluation_kind": "captured-human-reviewed-samples",
        "evidence_limitations": [
            "Samples are checked-in captures, not fresh agent executions.",
            "Promotion proves fixture review status, not live model accuracy.",
            "No efficiency or adoption threshold is evaluated.",
        ],
        "strict": args.strict,
        "promoted_only": args.promoted_only,
        "candidates_only": args.candidates_only,
        "samples_checked": len(results),
        "promoted_checked": sum(row.promotion_status == "promoted" for row in results),
        "candidate_checked": sum(row.promotion_status == "candidate" for row in results),
        "errors": errors,
        "results": [asdict(row) for row in results],
    }
    _write(args.reports_dir, payload, args.format)
    print(
        "eval-professional-agent-samples: "
        f"checked={len(results)}; promoted={payload['promoted_checked']}; "
        f"errors={len(errors)}; evidence=captured"
    )
    for error in errors:
        print(f"eval-professional-agent-samples: ERROR: {error}", file=sys.stderr)
    return 1 if errors else 0


def _args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--samples-dir",
        type=Path,
        default=ROOT / "evals/agent-behavior/professional-samples",
    )
    parser.add_argument("--reports-dir", type=Path, default=ROOT / "reports")
    parser.add_argument("--promoted-only", action="store_true")
    parser.add_argument("--candidates-only", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--format", choices=("all", "markdown", "json"), default="all")
    return parser.parse_args(argv)


def _registries() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    pro_data = load_yaml_file(ROOT / "src/registry/professional-skills.yaml")
    foundation_data = load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
    domain_data = load_yaml_file(ROOT / "src/registry/domain-skills.yaml")
    if not all(isinstance(item, dict) for item in (pro_data, foundation_data, domain_data)):
        raise ValidationProblem("three-layer Skill registries must be mappings")
    professional = {
        str(row.get("name", "")): row
        for row in pro_data.get("professional_skills", [])
        if isinstance(row, dict)
    }
    layer3 = {
        str(row.get("name", "")): row
        for row in foundation_data.get("foundation_skills", [])
        if isinstance(row, dict)
    }
    layer3.update(
        {
            str(row.get("name", "")): row
            for row in domain_data.get("domain_skills", [])
            if isinstance(row, dict)
        }
    )
    return professional, layer3


def _sample(
    path: Path,
    data: dict[str, Any],
    professional: dict[str, dict[str, Any]],
    layer3: dict[str, dict[str, Any]],
) -> SampleResult:
    expected = _mapping(data.get("expected"))
    actual = _mapping(data.get("actual"))
    review = _mapping(data.get("review"))
    result = SampleResult(
        sample_id=str(data.get("id", "")).strip() or _rel(path),
        path=_rel(path),
        promotion_status=str(review.get("promotion_status", "candidate")).strip(),
        profile=str(actual.get("profile", "")).strip(),
        primary_skill=str(actual.get("primary_skill", "")).strip(),
        layer3_skills=_strings(actual.get("layer3_skills")),
        review_skill=str(actual.get("review_skill", "")).strip(),
    )
    if not str(data.get("prompt", "")).strip():
        result.errors.append("prompt is required")
    for field in ("profile", "primary_skill", "layer3_skills", "review_skill"):
        expected_value = expected.get(field)
        actual_value = actual.get(field)
        if expected_value != actual_value:
            result.errors.append(f"actual.{field} does not match expected.{field}")
    if result.profile not in DISPATCHED_PROFILES:
        result.errors.append(f"invalid dispatched profile '{result.profile}'")
    primary = professional.get(result.primary_skill)
    if primary is None:
        result.errors.append(f"unknown primary Professional Skill '{result.primary_skill}'")
    elif result.profile not in _strings(primary.get("role_support")):
        result.errors.append(
            f"profile '{result.profile}' is not supported by primary Skill '{result.primary_skill}'"
        )
    if len(result.layer3_skills) > 3:
        result.errors.append("captured task loads more than three Layer 3 Skills")
    if len(result.layer3_skills) != len(set(result.layer3_skills)):
        result.errors.append("captured task repeats a Layer 3 Skill")
    primary_candidates = set(_strings(_mapping(primary).get("layer3_candidates")))
    for name in result.layer3_skills:
        if name not in layer3:
            result.errors.append(f"unknown Layer 3 Skill '{name}'")
        elif name not in primary_candidates:
            result.errors.append(
                f"Layer 3 Skill '{name}' is not a candidate of primary Skill "
                f"'{result.primary_skill}'"
            )
        elif result.profile not in _strings(layer3[name].get("role_support")):
            result.errors.append(
                f"Layer 3 Skill '{name}' does not support profile '{result.profile}'"
            )
    review_entry = professional.get(result.review_skill)
    if review_entry is None:
        result.errors.append(f"unknown Review Skill '{result.review_skill}'")
    elif "review-agent" not in _strings(review_entry.get("role_support")):
        result.errors.append(f"Review Skill '{result.review_skill}' does not support review-agent")

    handoff = _mapping(actual.get("handoff"))
    for field in HANDOFF_FIELDS:
        if field not in handoff or handoff[field] is None or handoff[field] == "":
            result.errors.append(f"actual.handoff.{field} is required")
    handoff_text = _fold(json.dumps(handoff, ensure_ascii=False))
    obligations = _strings(expected.get("required_professional_obligations"))
    result.obligations_covered = [item for item in obligations if _fold(item) in handoff_text]
    result.missing_obligations = [item for item in obligations if item not in result.obligations_covered]
    if result.missing_obligations:
        result.errors.append("missing captured obligation(s): " + ", ".join(result.missing_obligations))
    result.forbidden_hits = [
        item
        for item in _strings(expected.get("forbidden_behaviors"))
        if _fold(item) in handoff_text
    ]
    if result.forbidden_hits:
        result.errors.append("captured handoff contains forbidden behavior(s): " + ", ".join(result.forbidden_hits))
    if result.promotion_status not in {"candidate", "promoted"}:
        result.errors.append("review.promotion_status must be candidate or promoted")
    if result.promotion_status == "promoted" and bool(review.get("human_review_required")):
        result.errors.append("promoted fixture cannot still require human review")
    result.status = "pass" if not result.errors else "fail"
    return result


def _write(directory: Path, payload: dict[str, Any], report_format: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    if report_format in {"all", "json"}:
        (directory / "professional-agent-samples-report.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    if report_format in {"all", "markdown"}:
        lines = [
            "# Hookless Professional Agent Samples",
            "",
            "> Checked-in captured samples only; no fresh agent execution or adoption claim.",
            "",
            f"- Samples checked: {payload['samples_checked']}",
            f"- Promoted checked: {payload['promoted_checked']}",
            f"- Errors: {len(payload['errors'])}",
            "",
            "| Sample | Status | Profile | Primary | Layer 3 | Review |",
            "|---|---|---|---|---:|---|",
        ]
        for row in payload["results"]:
            lines.append(
                f"| `{row['sample_id']}` | {row['status']} | `{row['profile']}` | "
                f"`{row['primary_skill']}` | {len(row['layer3_skills'])} | `{row['review_skill']}` |"
            )
        if payload["errors"]:
            lines.extend(["", "## Errors", ""] + [f"- {item}" for item in payload["errors"]])
        (directory / "professional-agent-samples-report.md").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )


def _strings(value: Any) -> list[str]:
    return [str(item).strip() for item in value if str(item).strip()] if isinstance(value, list) else []


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _fold(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
