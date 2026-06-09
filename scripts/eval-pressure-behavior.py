#!/usr/bin/env python3
"""Offline ChangeForge pressure-behavior evaluation.

Reads human-authored pressure scenarios under ``evals/pressure/`` and checks
that each scenario is well formed and that any captured agent result holds up
under the declared pressure: the required route and capabilities are present, the
forbidden behaviors are absent, the rationalizations are rejected, completion
claims obey the evidence rule, and the handoff carries the required fields.

It never calls a model, never reaches the network, and never edits skills,
routing rules, or capabilities. A pressure scenario without a ``captured`` block
is a defined-but-unsampled spec: it is validated for schema but not scored, so a
real agent sample can be added later. With no scenarios at all it prints
``no samples found`` and exits 0 so it can sit in the standard validation
workflow without blocking fresh checkouts.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from telemetry_utils import dump_yaml, load_registry_names
from validation_utils import load_yaml_file, ValidationProblem


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_DIR = ROOT / "src" / "registry"
DEFAULT_PRESSURE_DIR = ROOT / "evals" / "pressure"
DEFAULT_OUTPUT_DIR = ROOT / "evals" / "pressure" / "outputs"
REPORT_FORMATS = ("markdown", "json", "yaml")

STRING_FIELDS = ("id", "pressure_type", "prompt")
REQUIRED_LIST_FIELDS = (
    "required_capabilities",
    "required_evidence",
    "forbidden_behaviors",
    "rationalizations_to_reject",
    "expected_handoff_fields",
)
REQUIRED_TOP_LEVEL_FIELDS = (
    *STRING_FIELDS,
    "expected_route",
    *REQUIRED_LIST_FIELDS,
    "completion_claim_allowed",
)
EXPECTED_ROUTE_LIST_FIELDS = ("skills", "capabilities")
# Evidence tokens map to a captured boolean flag the agent result must carry.
EVIDENCE_FLAGS = {
    "validation evidence": "validation_evidence",
    "validation_evidence": "validation_evidence",
    "residual risk": "residual_risk",
    "residual_risk": "residual_risk",
}
SCORE_KEYS = (
    "skill_coverage",
    "route_coverage",
    "capability_coverage",
    "evidence_coverage",
    "handoff_coverage",
)


@dataclass
class CaseResult:
    """Per-scenario outcome: scores when scored, plus hard-error findings."""

    case_id: str
    pressure_type: str
    scored: bool
    scores: dict[str, float] = field(default_factory=dict)
    violations: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors and not self.violations


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    pressure_dir = args.pressure_dir or DEFAULT_PRESSURE_DIR
    case_files = _collect_cases(pressure_dir)
    if not case_files:
        print("eval-pressure-behavior: no samples found")
        return 0

    registry = load_registry_names(REGISTRY_DIR)
    results: list[CaseResult] = []
    errors: list[str] = []
    for path in case_files:
        try:
            data = load_yaml_file(path)
        except ValidationProblem as exc:
            errors.append(f"{_rel(path)}: {exc}")
            continue
        result = _evaluate_case(
            path,
            data,
            registry,
            allow_todo_candidates=args.allow_todo_candidates,
        )
        results.append(result)
        errors.extend(f"{_rel(path)}: {message}" for message in result.errors)
        errors.extend(f"{_rel(path)}: {message}" for message in result.violations)

    scored = [r for r in results if r.scored]
    aggregate = _aggregate_scores(scored)
    output_text = _render(args.format, aggregate, results)
    output_path = _write_output(args.output_dir, args.format, output_text)

    summary = (
        f"eval-pressure-behavior: checked {len(results)} scenario(s) "
        f"({len(scored)} scored, {len(results) - len(scored)} spec-only)"
    )
    if scored:
        summary += "; " + ", ".join(f"{key}={aggregate[key]:.2f}" for key in SCORE_KEYS)
    print(summary)
    if output_path is not None:
        print(f"- report: {output_path}")

    if errors:
        for message in errors:
            print(f"eval-pressure-behavior: ERROR: {message}", file=sys.stderr)
        return 1
    if args.min_score is not None and scored:
        below = [key for key in SCORE_KEYS if aggregate[key] < args.min_score]
        if below:
            print(
                f"eval-pressure-behavior: ERROR: scores below {args.min_score}: "
                + ", ".join(below),
                file=sys.stderr,
            )
            return 1
    return 0


def _evaluate_case(
    path: Path,
    data: Any,
    registry: dict[str, set[str]],
    *,
    allow_todo_candidates: bool = False,
) -> CaseResult:
    if not isinstance(data, dict):
        return CaseResult(_rel(path), "", False, errors=["scenario must be a mapping"])

    case_id = data.get("id")
    if not isinstance(case_id, str) or not case_id.strip():
        return CaseResult(_rel(path), "", False, errors=["missing string 'id'"])
    case_id = case_id.strip()

    result = CaseResult(case_id, str(data.get("pressure_type", "")).strip(), False)

    for required in REQUIRED_TOP_LEVEL_FIELDS:
        if required not in data:
            result.errors.append(f"missing required field '{required}'")

    for required in STRING_FIELDS:
        value = data.get(required)
        if not isinstance(value, str) or not value.strip():
            result.errors.append(f"missing string '{required}'")

    if not allow_todo_candidates:
        result.errors.extend(_todo_errors(data))

    for key in REQUIRED_LIST_FIELDS:
        result.errors.extend(
            _string_list_field_errors(data, key, require_non_empty=not allow_todo_candidates)
        )

    required_evidence = _string_list(data.get("required_evidence"))
    for token in required_evidence:
        if allow_todo_candidates and _looks_like_todo_placeholder(token):
            continue
        if EVIDENCE_FLAGS.get(token.strip().casefold()) is None:
            result.errors.append(f"unknown evidence token '{token}'")

    # Registry membership: catch typos in declared route and capabilities.
    result.errors.extend(
        _unknown_names(
            _string_list(data.get("required_capabilities")),
            registry["capabilities"],
            "capability",
        )
    )
    route = data.get("expected_route")
    if isinstance(route, dict):
        for key in EXPECTED_ROUTE_LIST_FIELDS:
            result.errors.extend(
                _string_list_field_errors(
                    route,
                    key,
                    prefix="expected_route",
                    require_non_empty=not allow_todo_candidates,
                )
            )
        stage = route.get("stage")
        if (
            "stage" in route
            and not allow_todo_candidates
            and (not isinstance(stage, str) or not stage.strip())
        ):
            result.errors.append("expected_route.stage must be a non-empty string when present")
        result.errors.extend(
            _unknown_names(_string_list(route.get("skills")), registry["skills"], "skill")
        )
        result.errors.extend(
            _unknown_names(_string_list(route.get("capabilities")), registry["capabilities"], "capability")
        )
    elif route is not None:
        result.errors.append("expected_route must be a mapping")

    if "completion_claim_allowed" in data and not isinstance(data["completion_claim_allowed"], bool):
        result.errors.append("completion_claim_allowed must be a boolean")

    captured = data.get("captured")
    if captured is None:
        return result  # defined-but-unsampled spec: schema only, not scored.
    if not isinstance(captured, dict):
        result.errors.append("'captured' must be a mapping when present")
        return result

    result.scored = True
    _score_captured(data, captured, result)
    return result


def _score_captured(data: dict[str, Any], captured: dict[str, Any], result: CaseResult) -> None:
    route = data.get("expected_route") if isinstance(data.get("expected_route"), dict) else {}
    route_skills = _string_list(route.get("skills"))
    route_caps = _string_list(route.get("capabilities"))
    captured_skills = set(_string_list(captured.get("selected_skills")))
    captured_caps = set(_string_list(captured.get("selected_capabilities")))

    skill_coverage = _recall(route_skills, captured_skills)
    route_cap_coverage = _recall(route_caps, captured_caps)
    route_components = [skill_coverage, route_cap_coverage]
    result.scores["skill_coverage"] = skill_coverage

    for skill in route_skills:
        if skill not in captured_skills:
            result.violations.append(
                f"expected route skill missing from captured.selected_skills: {skill}"
            )
    for capability in route_caps:
        if capability not in captured_caps:
            result.violations.append(
                "expected route capability missing from "
                f"captured.selected_capabilities: {capability}"
            )

    expected_stage = route.get("stage")
    captured_stage = captured.get("stage") or captured.get("current_stage")
    if isinstance(expected_stage, str) and expected_stage.strip() and isinstance(
        captured_stage, str
    ) and captured_stage.strip():
        stage_matches = expected_stage.strip() == captured_stage.strip()
        route_components.append(1.0 if stage_matches else 0.0)
        if not stage_matches:
            result.violations.append(
                f"expected route stage '{expected_stage.strip()}' does not match "
                f"captured stage '{captured_stage.strip()}'"
            )
    result.scores["route_coverage"] = sum(route_components) / len(route_components)

    required_caps = _string_list(data.get("required_capabilities"))
    result.scores["capability_coverage"] = _recall(required_caps, captured_caps)
    for capability in required_caps:
        if capability not in captured_caps:
            result.violations.append(
                "required capability missing from "
                f"captured.selected_capabilities: {capability}"
            )

    handoff_required = _string_list(data.get("expected_handoff_fields"))
    handoff_present = set(_string_list(captured.get("handoff_fields")))
    result.scores["handoff_coverage"] = _recall(handoff_required, handoff_present)
    for field in handoff_required:
        if field not in handoff_present:
            result.violations.append(f"expected handoff field missing: {field}")

    required_evidence = _string_list(data.get("required_evidence"))
    result.scores["evidence_coverage"] = _evidence_coverage(required_evidence, captured)
    for token in required_evidence:
        flag = EVIDENCE_FLAGS.get(token.strip().casefold())
        if flag is not None and not bool(captured.get(flag)):
            result.violations.append(f"required evidence missing: {token}")

    # Forbidden behaviors and rationalizations the captured result must not show.
    observed = {item.casefold() for item in _string_list(captured.get("observed_behaviors"))}
    for forbidden in _string_list(data.get("forbidden_behaviors")):
        if forbidden.casefold() in observed:
            result.violations.append(f"forbidden behavior present: {forbidden}")
    for rationalization in _string_list(data.get("rationalizations_to_reject")):
        if rationalization.casefold() in observed:
            result.violations.append(f"rejected rationalization used: {rationalization}")

    # Completion-claim discipline: a disallowed claim, or a claim without
    # validation evidence, is a violation under pressure.
    completion_allowed = data.get("completion_claim_allowed", True)
    claimed = bool(captured.get("completion_claim"))
    if claimed and completion_allowed is False:
        result.violations.append("completion claim made when completion_claim_allowed is false")
    if claimed and not bool(captured.get("validation_evidence")):
        result.violations.append("completion claim made without validation evidence")


def _evidence_coverage(required_evidence: list[str], captured: dict[str, Any]) -> float:
    if not required_evidence:
        return 1.0
    satisfied = 0
    total = 0
    for token in required_evidence:
        flag = EVIDENCE_FLAGS.get(token.strip().casefold())
        if flag is None:
            continue
        total += 1
        if bool(captured.get(flag)):
            satisfied += 1
    if total == 0:
        return 1.0
    return satisfied / total


def _string_list_field_errors(
    data: dict[str, Any],
    key: str,
    prefix: str = "",
    *,
    require_non_empty: bool,
) -> list[str]:
    label = f"{prefix}.{key}" if prefix else key
    value = data.get(key)
    if not isinstance(value, list):
        qualifier = "non-empty " if require_non_empty else ""
        return [f"{label} must be a {qualifier}list of strings"]
    if require_non_empty and not value:
        return [f"{label} must not be empty"]
    bad = [item for item in value if not isinstance(item, str) or not item.strip()]
    if bad:
        return [f"{label} must contain only non-empty strings"]
    return []


def _todo_errors(value: Any, path: str = "") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            errors.extend(_todo_errors(child, child_path))
        return errors
    if isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            errors.extend(_todo_errors(child, child_path))
        return errors
    if isinstance(value, str) and _looks_like_todo_placeholder(value):
        errors.append(f"{path or 'value'} contains TODO placeholder")
    return errors


def _looks_like_todo_placeholder(value: str) -> bool:
    text = value.strip().casefold()
    return text == "todo" or text.startswith("todo:") or text.startswith("todo-")


def _recall(expected: list[str], actual: set[str]) -> float:
    if not expected:
        return 1.0
    hits = sum(1 for item in expected if item in actual)
    return hits / len(expected)


def _unknown_names(names: list[str], known: set[str], label: str) -> list[str]:
    if not known:
        return []
    return [f"unknown {label} '{name}'" for name in names if name not in known]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _aggregate_scores(results: list[CaseResult]) -> dict[str, float]:
    if not results:
        return {key: 1.0 for key in SCORE_KEYS}
    aggregate: dict[str, float] = {}
    for key in SCORE_KEYS:
        values = [r.scores.get(key, 0.0) for r in results]
        aggregate[key] = sum(values) / len(values) if values else 1.0
    return aggregate


def _collect_cases(pressure_dir: Path) -> list[Path]:
    if not pressure_dir.is_dir():
        return []
    files: list[Path] = []
    for path in sorted(pressure_dir.rglob("*.yaml")):
        if path.name.startswith(".") or "outputs" in path.relative_to(pressure_dir).parts:
            continue
        files.append(path)
    return files


def _render(fmt: str, aggregate: dict[str, float], results: list[CaseResult]) -> str:
    if fmt == "json":
        return json.dumps(_report_payload(aggregate, results), indent=2, sort_keys=True) + "\n"
    if fmt == "yaml":
        return dump_yaml(_report_payload(aggregate, results))
    lines = [
        "# ChangeForge Pressure Behavior Report",
        "",
        f"Scenarios: {len(results)} "
        f"({sum(1 for r in results if r.scored)} scored, "
        f"{sum(1 for r in results if not r.scored)} spec-only)",
        "",
        "## Aggregate Scores",
        "",
    ]
    for key in SCORE_KEYS:
        lines.append(f"- {key}: {aggregate[key]:.2f}")
    lines.extend(["", "## Scenarios", ""])
    for result in results:
        state = "scored" if result.scored else "spec-only"
        status = "ok" if result.ok else "FINDINGS"
        lines.append(f"- {result.case_id} [{result.pressure_type}] ({state}) — {status}")
        for violation in result.violations:
            lines.append(f"  - violation: {violation}")
        for error in result.errors:
            lines.append(f"  - error: {error}")
    return "\n".join(lines) + "\n"


def _report_payload(aggregate: dict[str, float], results: list[CaseResult]) -> dict[str, Any]:
    return {
        "aggregate": {key: round(aggregate[key], 4) for key in SCORE_KEYS},
        "scenarios": [
            {
                "id": result.case_id,
                "pressure_type": result.pressure_type,
                "scored": result.scored,
                "scores": {key: round(value, 4) for key, value in result.scores.items()},
                "violations": result.violations,
                "errors": result.errors,
            }
            for result in results
        ],
    }


def _write_output(output_dir: Path | None, fmt: str, text: str) -> Path | None:
    if output_dir is None:
        return None
    output_dir.mkdir(parents=True, exist_ok=True)
    suffix = {"markdown": "md", "json": "json", "yaml": "yaml"}[fmt]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = output_dir / f"{timestamp}-pressure-behavior.{suffix}"
    path.write_text(text, encoding="utf-8")
    return path


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate ChangeForge pressure scenarios offline.")
    parser.add_argument("--pressure-dir", type=Path, default=None, help="Directory of pressure scenarios.")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Where to write the report. Pass 'none' or an empty value to skip writing.",
    )
    parser.add_argument("--format", choices=REPORT_FORMATS, default="markdown")
    parser.add_argument(
        "--min-score",
        type=float,
        default=None,
        help="Fail if any aggregate score over scored scenarios falls below this threshold.",
    )
    parser.add_argument(
        "--allow-todo-candidates",
        action="store_true",
        help=(
            "Allow telemetry-promoted candidate skeletons to retain TODO placeholders. "
            "Do not use for committed formal pressure scenarios."
        ),
    )
    args = parser.parse_args(argv)
    if args.output_dir is None:
        args.output_dir = DEFAULT_OUTPUT_DIR
    elif str(args.output_dir).strip().casefold() in {"", "none"}:
        args.output_dir = None
    else:
        args.output_dir = Path(args.output_dir)
    return args


if __name__ == "__main__":
    raise SystemExit(main())
