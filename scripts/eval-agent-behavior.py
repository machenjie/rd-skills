#!/usr/bin/env python3
"""Offline ChangeForge agent-behavior evaluation.

Reads human-reviewed behavior samples under ``evals/agent-behavior/`` and scores
the captured ``changeforge_route`` manifest against each sample's expectations.
It validates route recall/precision, capability recall, reference adherence,
quality-gate closure, validation evidence, and the ``changeforge_stage_route``
stage projection (presence, stage correctness, stage capability alignment,
skipped-capability rationale, and context-budget validity). Missing router
self-use references in the manifest are a hard error. Samples can also opt in to
``runtime_prompt_flow`` scoring so the eval can verify clarification,
read-before-plan evidence, TDD signal, action owner/review mapping,
repair/re-review, validation evidence, and residual risk. It never calls a
model, never reaches the network, and never edits skills, routing rules, or
capabilities.

With no samples it prints ``no samples found`` and exits 0 so it can sit in the
standard validation workflow without blocking fresh checkouts.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from telemetry_utils import (
    dump_yaml,
    extract_route_manifest,
    extract_stage_manifest,
    load_registry_names,
    manifest_runtime_prompt_flow,
    manifest_string_list,
    runtime_flow_actions,
)
from validation_utils import load_yaml_file, ValidationProblem


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_DIR = ROOT / "src" / "registry"
DEFAULT_SAMPLE_DIRS = (
    ROOT / "evals" / "agent-behavior" / "samples",
    ROOT / "evals" / "agent-behavior" / "promoted",
)
DEFAULT_OUTPUT_DIR = ROOT / "evals" / "agent-behavior" / "outputs"
REPORT_FORMATS = ("markdown", "json", "yaml")
ROUTER_SELF_REFERENCES = (
    "references/routing-rules.md",
    "references/skill-registry.md",
    "references/capability-index.md",
    "references/domain-extension-index.md",
)
VALID_BUDGET_MODES = {"minimal", "single-stage", "staged-plan"}
STAGE_SCORE_KEYS = (
    "stage_presence",
    "stage_correctness",
    "stage_capability_alignment",
    "skipped_capability_rationale",
    "context_budget_validity",
)
RUNTIME_FLOW_SCORE_KEYS = (
    "runtime_clarification",
    "runtime_inspection",
    "runtime_tdd_signal",
    "runtime_action_review",
    "runtime_repair_rereview",
    "runtime_validation_residual",
)
SCORE_KEYS = (
    "route_recall",
    "route_precision",
    "capability_recall",
    "reference_adherence",
    "gate_closure",
    "validation_evidence_score",
    *RUNTIME_FLOW_SCORE_KEYS,
    *STAGE_SCORE_KEYS,
)


@dataclass
class SampleResult:
    """Per-sample scores and hard-error findings."""

    sample_id: str
    scores: dict[str, float]
    forbidden_violations: list[str]
    missing_self_references: list[str]
    residual_risk_present: bool
    errors: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors and not self.forbidden_violations


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    sample_dirs = [args.samples_dir] if args.samples_dir else list(DEFAULT_SAMPLE_DIRS)
    sample_files = _collect_samples(sample_dirs)
    if not sample_files:
        print("eval-agent-behavior: no samples found")
        return 0

    registry = load_registry_names(REGISTRY_DIR)
    results: list[SampleResult] = []
    errors: list[str] = []
    for path in sample_files:
        try:
            data = load_yaml_file(path)
        except ValidationProblem as exc:
            errors.append(f"{_rel(path)}: {exc}")
            continue
        result = _evaluate_sample(path, data, registry)
        results.append(result)
        errors.extend(f"{_rel(path)}: {message}" for message in result.errors)
        for violation in result.forbidden_violations:
            errors.append(f"{_rel(path)}: forbidden item present in manifest: {violation}")

    aggregate = _aggregate_scores(results)
    output_text = _render(args.format, aggregate, results)
    output_path = _write_output(args.output_dir, args.format, output_text)

    print(
        f"eval-agent-behavior: evaluated {len(results)} sample(s); "
        + ", ".join(f"{key}={aggregate[key]:.2f}" for key in SCORE_KEYS)
    )
    if output_path is not None:
        print(f"- report: {output_path}")

    if errors:
        for message in errors:
            print(f"eval-agent-behavior: ERROR: {message}", file=sys.stderr)
        return 1
    if args.min_score is not None:
        below = [key for key in SCORE_KEYS if aggregate[key] < args.min_score]
        if below:
            print(
                f"eval-agent-behavior: ERROR: scores below {args.min_score}: {', '.join(below)}",
                file=sys.stderr,
            )
            return 1
    return 0


def _evaluate_sample(
    path: Path,
    data: Any,
    registry: dict[str, set[str]],
) -> SampleResult:
    errors: list[str] = []
    if not isinstance(data, dict):
        return SampleResult(_rel(path), _zero_scores(), [], [], False, ["sample must be a mapping"])

    sample_id = data.get("id")
    if not isinstance(sample_id, str) or not sample_id.strip():
        errors.append("missing string 'id'")
        sample_id = _rel(path)

    expected = data.get("expected")
    if not isinstance(expected, dict):
        return SampleResult(str(sample_id), _zero_scores(), [], [], False, ["missing 'expected' mapping"])

    manifest = _resolve_manifest(data)
    if manifest is None:
        return SampleResult(
            str(sample_id),
            _zero_scores(),
            [],
            [],
            False,
            ["no changeforge_route manifest found in actual output"],
        )

    selected_skills = manifest_string_list(manifest, "selected_skills")
    selected_caps = manifest_string_list(manifest, "selected_capabilities")
    selected_exts = manifest_string_list(manifest, "selected_domain_extensions")
    manifest_refs = set(manifest_string_list(manifest, "required_references"))
    required_gates = set(manifest_string_list(manifest, "required_quality_gates"))
    skipped_gates = _skipped_gate_names(manifest)

    errors.extend(_unknown_name_errors(selected_skills, registry["skills"], "skill"))
    errors.extend(_unknown_name_errors(selected_caps, registry["capabilities"], "capability"))
    errors.extend(_unknown_name_errors(selected_exts, registry["extensions"], "domain extension"))

    expected_skills = _expected_list(expected, "selected_skills")
    forbidden_skills = _expected_list(expected, "forbidden_skills")
    expected_caps = _expected_list(expected, "selected_capabilities")
    expected_refs = _expected_list(expected, "required_references")
    expected_gates = _expected_list(expected, "required_quality_gates")

    forbidden_violations = sorted(set(forbidden_skills) & set(selected_skills))

    scores = {
        "route_recall": _recall(expected_skills, selected_skills),
        "route_precision": _precision(expected_skills, selected_skills),
        "capability_recall": _recall(expected_caps, selected_caps),
        "reference_adherence": _recall(expected_refs, manifest_refs),
        "gate_closure": _gate_closure(expected_gates, required_gates, skipped_gates),
        "validation_evidence_score": 1.0 if _has_validation_evidence(data, manifest) else 0.0,
    }
    runtime_scores, runtime_errors = _runtime_flow_scores(
        expected,
        manifest_runtime_prompt_flow(manifest),
    )
    scores.update(runtime_scores)
    errors.extend(runtime_errors)
    scores.update(_stage_scores(expected, _resolve_stage_manifest(data)))
    missing_self_refs = [ref for ref in ROUTER_SELF_REFERENCES if ref not in manifest_refs]
    if missing_self_refs:
        errors.append(
            "route manifest required_references is missing router self-use reference(s): "
            + ", ".join(missing_self_refs)
        )
    residual = _has_residual_risk(data, manifest)

    return SampleResult(
        sample_id=str(sample_id),
        scores=scores,
        forbidden_violations=forbidden_violations,
        missing_self_references=missing_self_refs,
        residual_risk_present=residual,
        errors=errors,
    )


def _resolve_manifest(data: dict[str, Any]) -> dict[str, Any] | None:
    # Primary form: a flat 'manifest' mapping that the repository YAML parser
    # can read without PyYAML.
    manifest = data.get("manifest")
    if isinstance(manifest, dict):
        return manifest
    # Convenience forms (require PyYAML for nested mappings / block scalars).
    actual = data.get("actual")
    if isinstance(actual, dict):
        nested = actual.get("route_manifest")
        if isinstance(nested, dict):
            return nested
        raw = actual.get("raw_output")
        if isinstance(raw, str):
            return extract_route_manifest(raw)
    if isinstance(actual, str):
        return extract_route_manifest(actual)
    return None


def _resolve_stage_manifest(data: dict[str, Any]) -> dict[str, Any] | None:
    # Primary form: a flat 'stage_manifest' mapping (two-level, parser-safe).
    manifest = data.get("stage_manifest")
    if isinstance(manifest, dict):
        return manifest
    actual = data.get("actual")
    if isinstance(actual, dict):
        nested = actual.get("stage_route_manifest")
        if isinstance(nested, dict):
            return nested
        raw = actual.get("raw_output")
        if isinstance(raw, str):
            return extract_stage_manifest(raw)
    if isinstance(actual, str):
        return extract_stage_manifest(actual)
    return None


def _stage_scores(
    expected: dict[str, Any],
    manifest: dict[str, Any] | None,
) -> dict[str, float]:
    """Score the changeforge_stage_route projection.

    Stage scoring is conditional: a sample opts in by declaring
    ``expected_stage``. Samples that do not test stage behavior score 1.0 on
    every stage dimension so the aggregate is not penalized for an untested
    concern. A sample that declares ``expected_stage`` but produced no stage
    manifest scores 0.0 across the stage dimensions.
    """
    expected_stage = str(expected.get("expected_stage", "")).strip()
    if not expected_stage:
        return {key: 1.0 for key in STAGE_SCORE_KEYS}
    if not isinstance(manifest, dict):
        return {key: 0.0 for key in STAGE_SCORE_KEYS}

    current = str(manifest.get("current_stage", "")).strip()
    selected = set(manifest_string_list(manifest, "selected_capabilities"))
    skipped = _stage_skipped(manifest)
    budget = _stage_budget_mode(manifest)

    if skipped:
        with_reason = sum(1 for _cap, reason in skipped if reason)
        rationale = with_reason / len(skipped)
    else:
        rationale = 0.0 if expected.get("require_skipped_rationale") else 1.0

    expected_budget = str(expected.get("expected_context_budget_mode", "")).strip()
    if expected_budget:
        budget_validity = 1.0 if budget == expected_budget else 0.0
    else:
        budget_validity = 1.0 if budget in VALID_BUDGET_MODES else 0.0

    return {
        "stage_presence": 1.0 if current else 0.0,
        "stage_correctness": 1.0 if current == expected_stage else 0.0,
        "stage_capability_alignment": _recall(
            _expected_list(expected, "expected_stage_capabilities"), selected
        ),
        "skipped_capability_rationale": rationale,
        "context_budget_validity": budget_validity,
    }


def _runtime_flow_scores(
    expected: dict[str, Any],
    flow: dict[str, Any] | None,
) -> tuple[dict[str, float], list[str]]:
    """Score the nested runtime prompt-flow projection.

    Runtime-flow scoring is opt-in. Existing samples that do not declare
    ``expected.runtime_prompt_flow`` score 1.0 on every runtime-flow dimension.
    """
    spec = expected.get("runtime_prompt_flow")
    if spec is None:
        return {key: 1.0 for key in RUNTIME_FLOW_SCORE_KEYS}, []
    if not isinstance(spec, dict):
        return (
            {key: 0.0 for key in RUNTIME_FLOW_SCORE_KEYS},
            ["expected.runtime_prompt_flow must be a mapping"],
        )
    if not isinstance(flow, dict):
        errors = []
        if spec.get("required") is True:
            errors.append("expected runtime_prompt_flow missing from route manifest")
        return {key: 0.0 for key in RUNTIME_FLOW_SCORE_KEYS}, errors

    errors: list[str] = []
    clarification_score = _runtime_clarification_score(spec, flow, errors)
    inspection_score = _runtime_inspection_score(spec, flow, errors)
    tdd_score = _runtime_tdd_score(flow, errors, required=bool(spec.get("required")))
    action_score = _runtime_action_review_score(spec, flow, errors)
    repair_score = _runtime_repair_score(spec, flow, errors)
    validation_score = _runtime_validation_residual_score(spec, flow, errors)

    return (
        {
            "runtime_clarification": clarification_score,
            "runtime_inspection": inspection_score,
            "runtime_tdd_signal": tdd_score,
            "runtime_action_review": action_score,
            "runtime_repair_rereview": repair_score,
            "runtime_validation_residual": validation_score,
        },
        errors,
    )


def _runtime_clarification_score(
    spec: dict[str, Any],
    flow: dict[str, Any],
    errors: list[str],
) -> float:
    clarification = flow.get("clarification_status")
    if isinstance(clarification, dict):
        status = str(clarification.get("status", "")).strip()
    elif isinstance(clarification, str):
        status = clarification.strip()
    else:
        status = ""
    expected_status = str(spec.get("clarification_status", "")).strip()
    ok = bool(status) and (not expected_status or status == expected_status)
    if not ok and spec.get("required") is True:
        errors.append("runtime_prompt_flow.clarification_status is missing or mismatched")
    return 1.0 if ok else 0.0


def _runtime_inspection_score(
    spec: dict[str, Any],
    flow: dict[str, Any],
    errors: list[str],
) -> float:
    inspected = flow.get("inspected_boundaries")
    if not isinstance(inspected, dict):
        if spec.get("required") is True:
            errors.append("runtime_prompt_flow.inspected_boundaries is missing")
        return 0.0
    required = _expected_list(spec, "required_inspected_boundaries")
    if required:
        present = [
            key
            for key in required
            if _has_runtime_boundary(inspected.get(key))
        ]
        missing = sorted(set(required) - set(present))
        if missing and spec.get("required") is True:
            errors.append(
                "runtime_prompt_flow.inspected_boundaries missing required field(s): "
                + ", ".join(missing)
            )
        return len(present) / len(required)
    return 1.0 if any(_has_runtime_boundary(value) for value in inspected.values()) else 0.0


def _runtime_tdd_score(flow: dict[str, Any], errors: list[str], *, required: bool) -> float:
    signal = flow.get("tdd_signal")
    if isinstance(signal, dict):
        kind = str(signal.get("kind", "")).strip()
        command = str(signal.get("command_or_check", "")).strip()
        expected = str(signal.get("expected_evidence", "")).strip()
        ok = bool(kind) and bool(command or expected)
    elif isinstance(signal, str):
        ok = bool(signal.strip())
    else:
        ok = False
    if not ok and required:
        errors.append("runtime_prompt_flow.tdd_signal is missing or incomplete")
    return 1.0 if ok else 0.0


def _runtime_action_review_score(
    spec: dict[str, Any],
    flow: dict[str, Any],
    errors: list[str],
) -> float:
    actions = runtime_flow_actions(flow)
    if not actions:
        if spec.get("required") is True:
            errors.append("runtime_prompt_flow.actions is missing")
        return 0.0

    required_ids = _expected_list(spec, "required_actions")
    id_score = _recall(required_ids, [str(action.get("id", "")).strip() for action in actions])
    complete = 0
    for action in actions:
        owner = str(action.get("owner_skill", "")).strip()
        reviewer = str(action.get("review_skill", "")).strip()
        evidence = str(action.get("review_evidence", "")).strip()
        action_id = str(action.get("id", "")).strip()
        if action_id and owner and reviewer and evidence:
            if spec.get("require_owner_review_distinct") is True and owner == reviewer:
                continue
            complete += 1
    completeness = complete / len(actions)
    score = (id_score + completeness) / 2
    if score < 1.0 and spec.get("required") is True:
        errors.append("runtime_prompt_flow.actions lacks required owner/review/evidence mapping")
    return score


def _runtime_repair_score(
    spec: dict[str, Any],
    flow: dict[str, Any],
    errors: list[str],
) -> float:
    require_repair = spec.get("require_repair_route") is True
    require_rereview = spec.get("require_re_review_result") is True
    if not (require_repair or require_rereview):
        return 1.0
    actions = runtime_flow_actions(flow)
    if not actions:
        errors.append("runtime_prompt_flow repair/re-review expected but no actions exist")
        return 0.0
    repair_route = flow.get("repair_route")
    has_top_level_repair = isinstance(repair_route, dict) and bool(
        str(repair_route.get("owner_skill", "")).strip()
    )
    satisfied = 0
    for action in actions:
        has_repair = bool(str(action.get("repair_route_if_review_fails", "")).strip())
        rereview_required = action.get("re_review_required") is True
        rereview_result = str(action.get("re_review_result", "")).strip()
        repair_ok = (not require_repair) or has_repair or has_top_level_repair
        rereview_ok = (not require_rereview) or (rereview_required and bool(rereview_result))
        if repair_ok and rereview_ok:
            satisfied += 1
    score = satisfied / len(actions)
    if score < 1.0:
        errors.append("runtime_prompt_flow repair/re-review evidence is incomplete")
    return score


def _runtime_validation_residual_score(
    spec: dict[str, Any],
    flow: dict[str, Any],
    errors: list[str],
) -> float:
    require_validation = spec.get("require_validation_evidence") is True
    require_residual = spec.get("require_residual_risk") is True
    validation_ok = (not require_validation) or _has_runtime_boundary(flow.get("validation_evidence"))
    residual_ok = (not require_residual) or _has_runtime_boundary(flow.get("residual_risk"))
    if not validation_ok:
        errors.append("runtime_prompt_flow.validation_evidence is missing")
    if not residual_ok:
        errors.append("runtime_prompt_flow.residual_risk is missing")
    checks = []
    if require_validation:
        checks.append(1.0 if validation_ok else 0.0)
    if require_residual:
        checks.append(1.0 if residual_ok else 0.0)
    if not checks:
        return 1.0
    return sum(checks) / len(checks)


def _has_runtime_boundary(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(_has_runtime_boundary(item) for item in value)
    if isinstance(value, dict):
        return any(_has_runtime_boundary(item) for item in value.values())
    return value is True


def _stage_skipped(manifest: dict[str, Any]) -> list[tuple[str, str]]:
    """Return (capability, reason) pairs from either the mapping or string form."""
    entries = manifest.get("skipped_capabilities")
    result: list[tuple[str, str]] = []
    if not isinstance(entries, list):
        return result
    for entry in entries:
        if isinstance(entry, dict):
            cap = str(entry.get("capability", "")).strip()
            reason = str(entry.get("reason", "")).strip()
            if cap:
                result.append((cap, reason))
        elif isinstance(entry, str) and "=>" in entry:
            cap, _, reason = entry.partition("=>")
            if cap.strip():
                result.append((cap.strip(), reason.strip()))
        elif isinstance(entry, str) and entry.strip():
            result.append((entry.strip(), ""))
    return result


def _stage_budget_mode(manifest: dict[str, Any]) -> str:
    mode = manifest.get("context_budget_mode")
    if isinstance(mode, str) and mode.strip():
        return mode.strip()
    budget = manifest.get("context_budget")
    if isinstance(budget, dict):
        nested = budget.get("mode")
        if isinstance(nested, str):
            return nested.strip()
    return ""


def _skipped_gate_names(manifest: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    skipped = manifest.get("skipped_quality_gates")
    if not isinstance(skipped, list):
        return names
    for entry in skipped:
        if isinstance(entry, dict):
            gate = entry.get("gate")
            reason = entry.get("reason")
            if _nonempty(gate) and _nonempty(reason):
                names.add(str(gate).strip())
        elif isinstance(entry, str) and "=>" in entry:
            gate, _, reason = entry.partition("=>")
            if gate.strip() and reason.strip():
                names.add(gate.strip())
    return names


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _expected_list(expected: dict[str, Any], key: str) -> list[str]:
    value = expected.get(key)
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _unknown_name_errors(values: list[str], allowed: set[str], label: str) -> list[str]:
    if not allowed:
        return []
    return [f"unknown {label} '{value}' in manifest" for value in values if value not in allowed]


def _recall(expected: list[str], actual: Any) -> float:
    expected_set = set(expected)
    if not expected_set:
        return 1.0
    actual_set = set(actual)
    return len(expected_set & actual_set) / len(expected_set)


def _precision(expected: list[str], actual: list[str]) -> float:
    actual_set = set(actual)
    if not actual_set:
        return 1.0 if not expected else 0.0
    expected_set = set(expected)
    if not expected_set:
        return 1.0
    return len(expected_set & actual_set) / len(actual_set)


def _gate_closure(expected: list[str], required: set[str], skipped: set[str]) -> float:
    expected_set = set(expected)
    if not expected_set:
        return 1.0
    closed = required | skipped
    return len(expected_set & closed) / len(expected_set)


def _has_validation_evidence(data: dict[str, Any], manifest: dict[str, Any]) -> bool:
    if data.get("validation_evidence") is True:
        return True
    actual = data.get("actual")
    if isinstance(actual, dict):
        if actual.get("validation_evidence") is True:
            return True
        raw = actual.get("raw_output")
        if isinstance(raw, str) and _mentions(raw, ("test", "validation", "verified", "pytest")):
            return True
    return False


def _has_residual_risk(data: dict[str, Any], manifest: dict[str, Any]) -> bool:
    if data.get("residual_risk") is True:
        return True
    actual = data.get("actual")
    if isinstance(actual, dict):
        if actual.get("residual_risk") is True:
            return True
        raw = actual.get("raw_output")
        if isinstance(raw, str) and _mentions(raw, ("residual risk", "residual", "unverified")):
            return True
    return False


def _mentions(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.casefold()
    return any(term in lowered for term in terms)


def _aggregate_scores(results: list[SampleResult]) -> dict[str, float]:
    scored = [result for result in results if not result.errors]
    if not scored:
        return _zero_scores()
    aggregate: dict[str, float] = {}
    for key in SCORE_KEYS:
        aggregate[key] = sum(result.scores[key] for result in scored) / len(scored)
    return aggregate


def _zero_scores() -> dict[str, float]:
    return {key: 0.0 for key in SCORE_KEYS}


def _render(report_format: str, aggregate: dict[str, float], results: list[SampleResult]) -> str:
    payload = {
        "schema_version": "1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "samples": len(results),
        "aggregate": {key: round(aggregate[key], 4) for key in SCORE_KEYS},
        "results": [
            {
                "id": result.sample_id,
                "ok": result.ok,
                "scores": {key: round(result.scores[key], 4) for key in SCORE_KEYS},
                "forbidden_violations": result.forbidden_violations,
                "missing_self_references": result.missing_self_references,
                "residual_risk_present": result.residual_risk_present,
                "errors": result.errors,
            }
            for result in results
        ],
    }
    if report_format == "json":
        return json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if report_format == "yaml":
        return dump_yaml(payload)
    return _render_markdown(payload)


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# ChangeForge Agent Behavior Eval",
        "",
        f"- samples: {payload['samples']}",
        "",
        "## Aggregate Scores",
        "",
    ]
    for key in SCORE_KEYS:
        lines.append(f"- {key}: {payload['aggregate'][key]:.2f}")
    lines.extend(["", "## Per-Sample Results", "", "| id | ok | " + " | ".join(SCORE_KEYS) + " |"])
    lines.append("| --- | --- |" + " --- |" * len(SCORE_KEYS))
    for result in payload["results"]:
        score_cells = " | ".join(f"{result['scores'][key]:.2f}" for key in SCORE_KEYS)
        lines.append(f"| {result['id']} | {result['ok']} | {score_cells} |")
    lines.extend(["", "## Machine-Readable Summary", "", "```json", json.dumps(payload, indent=2, sort_keys=True), "```", ""])
    return "\n".join(lines)


def _collect_samples(sample_dirs: list[Path]) -> list[Path]:
    files: list[Path] = []
    for directory in sample_dirs:
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.yaml")):
            if not path.name.startswith("."):
                files.append(path)
    return files


def _write_output(output_dir: Path | None, report_format: str, text: str) -> Path | None:
    base = (output_dir or DEFAULT_OUTPUT_DIR).expanduser()
    try:
        base.mkdir(parents=True, exist_ok=True)
        extension = {"markdown": "md", "json": "json", "yaml": "yaml"}[report_format]
        date_stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        path = base / f"{date_stamp}-agent-behavior-eval.{extension}"
        path.write_text(text, encoding="utf-8")
        return path
    except OSError:
        return None


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate ChangeForge agent behavior samples.")
    parser.add_argument("--samples-dir", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--format", choices=REPORT_FORMATS, default="markdown")
    parser.add_argument(
        "--min-score",
        type=float,
        default=None,
        help="Optional aggregate score floor; below it the eval exits non-zero.",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
