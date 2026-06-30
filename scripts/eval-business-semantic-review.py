#!/usr/bin/env python3
"""Compare Business Semantic review fixtures with deterministic actual outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from validation_utils import fail_many, load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVAL_DIR = ROOT / "evals" / "business-semantic"
DEFAULT_OUTPUT_DIR = ROOT / "evals" / "business-semantic-outputs"
EVAL_DIR = DEFAULT_EVAL_DIR
OUTPUT_DIR = DEFAULT_OUTPUT_DIR

EXPECTED_METADATA = {
    "generated_by": "scripts/generate-business-semantic-actuals.py",
    "generation_mode": "deterministic",
    "route_source": "current deterministic route resolver / fixture route adapter",
    "review_source": "deterministic fixture review skeleton",
}

REQUIRED_CATEGORIES = {
    "hidden-rule-in-sql": {"hidden_sql_rule"},
    "controller-only-business-rule": {"controller_only_rule"},
    "dto-as-domain-object": {"dto_as_domain_object"},
    "workflow-transition-added": {"workflow_transition_gap"},
    "refactor-changes-business-semantics": {"semantic_diff"},
}


def main() -> int:
    errors: list[str] = []
    cases = [(path, load_yaml_file(path)) for path in sorted(EVAL_DIR.glob("*.yaml"))]
    if _using_default_dirs() and len(cases) != 10:
        errors.append(f"expected 10 fixtures, found {len(cases)}")
    metrics = {
        "expected_findings": 0,
        "finding_hits": 0,
        "expected_evidence_items": 0,
        "expected_evidence_hits": 0,
        "forbidden_expected": 0,
        "forbidden_hits": 0,
        "memory_source_separation_coverage": 0,
        "golden_case_gap_coverage": 0,
        "semantic_diff_detection_coverage": 0,
    }
    for path, case in cases:
        _validate_case(path, case, metrics, errors)
    if errors:
        return fail_many("eval-business-semantic-review", errors)
    print(
        "eval-business-semantic-review: OK "
        f"cases={len(cases)} "
        f"finding_recall={_ratio(metrics['finding_hits'], metrics['expected_findings']):.2f} "
        f"expected_evidence_items={metrics['expected_evidence_items']} "
        f"expected_evidence_hits={metrics['expected_evidence_hits']} "
        f"expected_evidence_recall={_ratio(metrics['expected_evidence_hits'], metrics['expected_evidence_items']):.2f} "
        f"forbidden_behavior_avoidance={_ratio(metrics['forbidden_hits'], metrics['forbidden_expected']):.2f} "
        f"memory_source_separation_coverage={metrics['memory_source_separation_coverage']} "
        f"golden_case_gap_coverage={metrics['golden_case_gap_coverage']} "
        f"semantic_diff_detection_coverage={metrics['semantic_diff_detection_coverage']}"
    )
    return 0


def _validate_case(
    path: Path,
    case: dict[str, Any],
    metrics: dict[str, int],
    errors: list[str],
) -> None:
    case_id = str(case.get("case_id") or path.stem)
    actual_path = OUTPUT_DIR / f"{case_id}.actual.yaml"
    if not actual_path.is_file():
        errors.append(f"{case_id}: missing actual output {actual_path.relative_to(ROOT)}")
        return
    actual_doc = load_yaml_file(actual_path)
    _validate_actual_metadata(case_id, actual_doc, errors)
    actual_review = actual_doc.get("actual_review") if isinstance(actual_doc, dict) else None
    if not isinstance(actual_review, dict):
        errors.append(f"{case_id}: actual output must contain actual_review")
        return
    findings = actual_review.get("findings", [])
    if not isinstance(findings, list):
        errors.append(f"{case_id}: actual_review.findings must be a list")
        return
    expected_findings = case.get("expected_review_findings", [])
    if not isinstance(expected_findings, list) or not expected_findings:
        errors.append(f"{case_id}: expected_review_findings must be non-empty")
        return
    actual_findings = [item for item in findings if isinstance(item, dict)]
    actual_texts = [_finding_text(item) for item in actual_findings]
    for expected in expected_findings:
        metrics["expected_findings"] += 1
        if _finding_is_covered(expected, actual_texts):
            metrics["finding_hits"] += 1
        else:
            errors.append(f"{case_id}: missing expected review finding {expected!r}")
        evidence_items = _as_list(expected.get("expected_evidence")) if isinstance(expected, dict) else []
        metrics["expected_evidence_items"] += len(evidence_items)
        if evidence_items:
            evidence_covered, missing_evidence = _expected_evidence_covered(expected, actual_findings)
            metrics["expected_evidence_hits"] += len(evidence_items) - len(missing_evidence)
            if not evidence_covered:
                errors.append(f"{case_id}: missing expected evidence {missing_evidence}")
    forbidden = _as_list(case.get("forbidden_behavior"))
    avoided = _as_list(actual_review.get("forbidden_behavior_avoided"))
    avoided_text = " | ".join(_normalize(item) for item in avoided)
    for item in forbidden:
        metrics["forbidden_expected"] += 1
        if _normalize(item) in avoided_text:
            metrics["forbidden_hits"] += 1
        else:
            errors.append(f"{case_id}: forbidden behavior not avoided: {item}")
    _validate_case_specific_categories(case_id, findings, actual_review, errors, metrics)


def _finding_is_covered(expected: Any, actual_texts: list[str]) -> bool:
    if isinstance(expected, dict):
        probes = [
            str(expected.get("category") or ""),
            str(expected.get("impacted_claim") or ""),
            str(expected.get("required_fix") or ""),
        ]
        probes = [_normalize(item) for item in probes if item]
        return all(any(probe in text for text in actual_texts) for probe in probes)
    expected_text = _normalize(str(expected))
    return any(expected_text in text or text in expected_text for text in actual_texts)


def _expected_evidence_covered(
    expected: dict[str, Any],
    actual_findings: list[dict[str, Any]],
) -> tuple[bool, list[str]]:
    expected_items = _as_list(expected.get("expected_evidence"))
    matching_texts = [
        _finding_text(finding)
        for finding in actual_findings
        if _finding_is_covered(expected, [_finding_text(finding)])
    ]
    if not matching_texts:
        matching_texts = [_finding_text(finding) for finding in actual_findings]
    missing = [
        item
        for item in expected_items
        if not any(_normalize(item) in text for text in matching_texts)
    ]
    return not missing, missing


def _validate_case_specific_categories(
    case_id: str,
    findings: list[Any],
    actual_review: dict[str, Any],
    errors: list[str],
    metrics: dict[str, int],
) -> None:
    categories = {str(item.get("category")) for item in findings if isinstance(item, dict)}
    missing = REQUIRED_CATEGORIES.get(case_id, set()) - categories
    if missing:
        errors.append(f"{case_id}: missing required review categories {sorted(missing)}")
    residual_text = " ".join(_as_list(actual_review.get("residual_risk"))).casefold()
    finding_text = " ".join(_finding_text(item) for item in findings if isinstance(item, dict))
    combined = f"{finding_text} {residual_text}"
    if case_id == "stale-business-memory":
        if "memory" in combined and ("source truth" in combined or "stale" in combined):
            metrics["memory_source_separation_coverage"] += 1
        else:
            errors.append(f"{case_id}: missing memory-not-source-truth or stale verdict coverage")
    if case_id == "business-golden-case-missing":
        if "golden" in combined and "missing" in combined:
            metrics["golden_case_gap_coverage"] += 1
        else:
            errors.append(f"{case_id}: missing business golden case gap coverage")
    if case_id == "refactor-changes-business-semantics":
        if "semantic" in combined and ("golden" in combined or "characterization" in combined):
            metrics["semantic_diff_detection_coverage"] += 1
        else:
            errors.append(f"{case_id}: missing semantic diff detection coverage")
    if case_id == "over-routing-simple-local-change":
        route = actual_review.get("business_semantic_pack_required")
        if route is True or "bsp_required" in categories:
            errors.append(f"{case_id}: review must not require BSP for simple local change")


def _finding_text(item: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("finding_id", "severity", "category", "impacted_claim", "required_fix", "validation_required"):
        value = item.get(key)
        if value:
            parts.append(str(value))
    evidence = item.get("evidence")
    if isinstance(evidence, list):
        parts.extend(str(value) for value in evidence)
    elif evidence:
        parts.append(str(evidence))
    return _normalize(" ".join(parts))


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if value is None:
        return []
    return [str(value)]


def _normalize(value: str) -> str:
    return " ".join(value.casefold().replace("-", " ").replace("_", " ").split())


def _ratio(hit: int, expected: int) -> float:
    return 1.0 if expected == 0 else hit / expected


def _validate_actual_metadata(case_id: str, actual_doc: Any, errors: list[str]) -> None:
    metadata = actual_doc.get("actual_metadata") if isinstance(actual_doc, dict) else None
    if not isinstance(metadata, dict):
        errors.append(f"{case_id}: actual output missing actual_metadata")
        return
    for key, expected in EXPECTED_METADATA.items():
        if metadata.get(key) != expected:
            errors.append(f"{case_id}: actual_metadata.{key} expected {expected!r}, actual {metadata.get(key)!r}")
    if not metadata.get("source_fixture"):
        errors.append(f"{case_id}: actual_metadata.source_fixture must be non-empty")


def _using_default_dirs() -> bool:
    return EVAL_DIR == DEFAULT_EVAL_DIR and OUTPUT_DIR == DEFAULT_OUTPUT_DIR


if __name__ == "__main__":
    raise SystemExit(main())
