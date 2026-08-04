#!/usr/bin/env python3
"""Score captured Hookless agent handoffs against observable task contracts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from validation_utils import ValidationProblem, load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SAMPLES = ROOT / "evals/agent-behavior/professional-samples"
DEFAULT_OUTPUT = ROOT / "evals/agent-behavior/outputs"
SCORE_KEYS = (
    "route_once",
    "profile_boundary",
    "layer3_jit",
    "independent_review_boundary",
    "handoff_contract",
    "obligation_coverage",
    "validation_honesty",
    "forbidden_behavior_absence",
)
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


@dataclass
class Result:
    sample_id: str
    path: str
    ok: bool
    scores: dict[str, float]
    errors: list[str] = field(default_factory=list)


def main(argv: list[str] | None = None) -> int:
    args = _args(sys.argv[1:] if argv is None else argv)
    samples = args.samples_dir or DEFAULT_SAMPLES
    try:
        professional, layer3 = _registries()
    except ValidationProblem as exc:
        print(f"eval-agent-behavior: ERROR: {exc}", file=sys.stderr)
        return 1
    paths = sorted(path for path in samples.rglob("*.yaml") if "raw" not in path.parts)
    results: list[Result] = []
    for path in paths:
        data = load_yaml_file(path)
        if isinstance(data, dict) and isinstance(data.get("expected"), dict):
            results.append(_score(path, data, professional, layer3))
    if not results:
        print("eval-agent-behavior: no Hookless captured samples found", file=sys.stderr)
        return 1
    aggregate = {
        key: sum(row.scores[key] for row in results) / len(results) for key in SCORE_KEYS
    }
    errors = [f"{row.path}: {message}" for row in results for message in row.errors]
    if args.min_score is not None:
        below = [key for key, value in aggregate.items() if value < args.min_score]
        if below:
            errors.append(
                f"static captured-score floor {args.min_score:.2f} missed: {', '.join(below)}"
            )
    payload = {
        "schema_version": 2,
        "architecture": "hookless-control-plane",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evaluation_kind": "captured-observable-handoff",
        "evidence_limitations": [
            "No agent was executed; samples are checked-in captures.",
            "Scores measure fixture conformance, not host performance, production accuracy, or adoption.",
        ],
        "samples_checked": len(results),
        "errors": errors,
        "aggregate": aggregate,
        "results": [asdict(row) for row in results],
    }
    output = _write(args.output_dir or DEFAULT_OUTPUT, args.format, payload)
    print(
        "eval-agent-behavior: "
        f"evaluated {len(results)} captured sample(s); errors={len(errors)}; "
        f"evidence=captured; report={output}"
    )
    for error in errors:
        print(f"eval-agent-behavior: ERROR: {error}", file=sys.stderr)
    return 1 if errors else 0


def _args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--format", choices=("markdown", "json", "yaml"), default="markdown")
    parser.add_argument(
        "--min-score",
        type=float,
        help="optional floor for static captured-fixture conformance; not a host-performance or product-quality threshold",
    )
    return parser.parse_args(argv)


def _registries() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    pro = load_yaml_file(ROOT / "src/registry/professional-skills.yaml")
    foundation = load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
    domain = load_yaml_file(ROOT / "src/registry/domain-skills.yaml")
    if not all(isinstance(item, dict) for item in (pro, foundation, domain)):
        raise ValidationProblem("three-layer Skill registries must be mappings")
    professional = {
        str(row.get("name", "")): row
        for row in pro.get("professional_skills", [])
        if isinstance(row, dict)
    }
    layer3 = {
        str(row.get("name", "")): row
        for row in foundation.get("foundation_skills", [])
        if isinstance(row, dict)
    } | {
        str(row.get("name", "")): row
        for row in domain.get("domain_skills", [])
        if isinstance(row, dict)
    }
    return professional, layer3


def _score(
    path: Path,
    data: dict[str, Any],
    professional: dict[str, dict[str, Any]],
    layer3: dict[str, dict[str, Any]],
) -> Result:
    expected = _mapping(data.get("expected"))
    actual = _mapping(data.get("actual"))
    profile = str(actual.get("profile", ""))
    primary = str(actual.get("primary_skill", ""))
    review = str(actual.get("review_skill", ""))
    selected_layer3 = _strings(actual.get("layer3_skills"))
    scores = {key: 0.0 for key in SCORE_KEYS}
    errors: list[str] = []

    route_match = all(
        actual.get(field) == expected.get(field)
        for field in ("profile", "primary_skill", "layer3_skills", "review_skill")
    )
    scores["route_once"] = float(route_match and primary in professional)
    if not scores["route_once"]:
        errors.append("actual route does not match the one-primary expected route")

    primary_roles = _strings(_mapping(professional.get(primary)).get("role_support"))
    scores["profile_boundary"] = float(profile in primary_roles)
    if not scores["profile_boundary"]:
        errors.append(f"profile '{profile}' is not supported by primary Skill '{primary}'")

    scores["layer3_jit"] = float(
        len(selected_layer3) <= 3
        and len(selected_layer3) == len(set(selected_layer3))
        and all(name in layer3 for name in selected_layer3)
        and all(
            name
            in set(_strings(_mapping(professional.get(primary)).get("layer3_candidates")))
            for name in selected_layer3
        )
        and all(
            profile in _strings(_mapping(layer3.get(name)).get("role_support"))
            for name in selected_layer3
        )
    )
    if not scores["layer3_jit"]:
        errors.append(
            "Layer 3 selection is unknown, duplicated, exceeds the JIT budget, "
            "is not declared by the primary Skill, or is incompatible with the dispatch profile"
        )

    review_roles = _strings(_mapping(professional.get(review)).get("role_support"))
    scores["independent_review_boundary"] = float("review-agent" in review_roles)
    if not scores["independent_review_boundary"]:
        errors.append(f"Review Skill '{review}' does not support review-agent")

    handoff = _mapping(actual.get("handoff"))
    scores["handoff_contract"] = float(
        all(field in handoff and handoff[field] is not None and handoff[field] != "" for field in HANDOFF_FIELDS)
    )
    if not scores["handoff_contract"]:
        errors.append("natural-language handoff is missing required observable fields")

    folded_handoff = _fold(json.dumps(handoff, ensure_ascii=False))
    obligations = _strings(expected.get("required_professional_obligations"))
    scores["obligation_coverage"] = (
        sum(_fold(item) in folded_handoff for item in obligations) / len(obligations)
        if obligations
        else 0.0
    )
    if scores["obligation_coverage"] < 1.0:
        errors.append("captured handoff misses a professional obligation")

    validation = _fold(str(handoff.get("validation_results", "")))
    honest_unverified = (
        "not run" not in validation
        and "not verified" not in validation
        or bool(str(handoff.get("unverified_scope", "")).strip())
        and bool(str(handoff.get("residual_risk", "")).strip())
    )
    scores["validation_honesty"] = float(bool(validation) and honest_unverified)
    if not scores["validation_honesty"]:
        errors.append("validation result is absent or an unverified result lacks proof limits")

    forbidden = _strings(expected.get("forbidden_behaviors"))
    scores["forbidden_behavior_absence"] = float(
        not any(_fold(item) in folded_handoff for item in forbidden)
    )
    if not scores["forbidden_behavior_absence"]:
        errors.append("captured handoff contains a forbidden shortcut")
    return Result(
        sample_id=str(data.get("id", _rel(path))),
        path=_rel(path),
        ok=not errors,
        scores=scores,
        errors=errors,
    )


def _write(directory: Path, report_format: str, payload: dict[str, Any]) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    extension = {"markdown": "md", "json": "json", "yaml": "yaml"}[report_format]
    path = directory / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-agent-behavior-eval.{extension}"
    if report_format == "json":
        text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    elif report_format == "yaml":
        # JSON is valid YAML and avoids a serializer dependency.
        text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    else:
        lines = [
            "# Hookless Agent Behavior Captures",
            "",
            "> Checked-in captures only; no host-performance, production-accuracy, or adoption claim.",
            "",
            f"- Samples checked: {payload['samples_checked']}",
            f"- Errors: {len(payload['errors'])}",
            "",
            "| Sample | OK | " + " | ".join(SCORE_KEYS) + " |",
            "|---|---|" + "---:|" * len(SCORE_KEYS),
        ]
        for row in payload["results"]:
            scores = " | ".join(f"{row['scores'][key]:.2f}" for key in SCORE_KEYS)
            lines.append(f"| `{row['sample_id']}` | {row['ok']} | {scores} |")
        text = "\n".join(lines) + "\n"
    path.write_text(text, encoding="utf-8")
    return path


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _strings(value: Any) -> list[str]:
    return [str(item).strip() for item in value if str(item).strip()] if isinstance(value, list) else []


def _fold(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
