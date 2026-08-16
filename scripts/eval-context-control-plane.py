#!/usr/bin/env python3
"""Evaluate hookless context boundaries and early productive action."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validation_utils import report_output_paths


ROOT = Path(__file__).resolve().parents[1]
SOURCE_REPORT = ROOT / "reports" / "hookless-control-plane-eval.json"
RENDERED_CONTEXT_REPORT = ROOT / "reports" / "rendered-context-budget.json"
CORE_CONTRACTS = ROOT / "src" / "control-model" / "core-contracts.json"
HOST_ENFORCEMENT = ROOT / "src" / "agent-profiles" / "host-enforcement.json"
REPORT_JSON = ROOT / "reports" / "context-control-plane-eval.json"
REPORT_MD = ROOT / "reports" / "context-control-plane-eval.md"
EXPECTED_EVIDENCE_SCOPE = "deterministic-fixtures"
EXPECTED_REPORT_SCHEMA_VERSION = 2
EXPECTED_FIXTURE_SCHEMA_VERSION = 2
EXPECTED_DEPENDENCIES = ["eval-agent-lightweight", "eval-rendered-context"]
TRANSFER_SUMMARY_FIELDS = (
    "semantic_baseline",
    "gross_tokens",
    "non_compressible_tokens",
    "compressible_tokens",
    "compressible_ratio",
    "long_task_selector_join_count",
    "conservative_long_task_ratio",
    "before_gross_tokens",
    "after_gross_tokens",
    "realized_reduction_tokens",
    "realized_reduction_ratio",
    "proof_limits",
)


def _read_json(path: Path, label: str, missing_hint: str = "") -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        suffix = f"; {missing_hint}" if missing_hint else ""
        raise ValueError(f"missing {label}: {path}{suffix}") from exc
    except OSError as exc:
        raise ValueError(f"cannot read {label} {path}: {exc}") from exc
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"malformed {label} {path}: invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"malformed {label} {path}: root must be an object")
    return value


def _load_source_report(path: Path | None = None) -> dict[str, Any]:
    source_report = SOURCE_REPORT if path is None else path
    source = _read_json(
        source_report,
        "prerequisite report",
        "run scripts/eval-agent-lightweight.py first",
    )
    if source.get("schema_version") != EXPECTED_REPORT_SCHEMA_VERSION:
        raise ValueError(
            f"prerequisite report must use schema_version {EXPECTED_REPORT_SCHEMA_VERSION}"
        )
    if source.get("fixture_schema_version") != EXPECTED_FIXTURE_SCHEMA_VERSION:
        raise ValueError("prerequisite report has stale fixture_schema_version")
    if source.get("status") != "pass":
        raise ValueError(
            "prerequisite report did not pass: expected status 'pass', "
            f"got {source.get('status')!r}"
        )
    if source.get("evidence_scope") != EXPECTED_EVIDENCE_SCOPE:
        raise ValueError(
            "prerequisite report has wrong evidence_scope: "
            f"expected {EXPECTED_EVIDENCE_SCOPE!r}, got {source.get('evidence_scope')!r}"
        )
    cases = source.get("cases")
    if not isinstance(cases, list) or not cases or source.get("fixture_count") != len(cases):
        raise ValueError("malformed prerequisite report: cases/count are inconsistent")
    limitations = source.get("limitations")
    if not isinstance(limitations, list) or any(not isinstance(item, str) for item in limitations):
        raise ValueError("malformed prerequisite report: limitations must be strings")
    required_metrics = {
        "preparation_loop_detected": bool,
        "parallel_write_conflict": bool,
        "loaded_skill_count": int,
        "required_multi_agent_progress_satisfied": bool,
        "required_progress_for_multi_agent": bool,
    }
    seen_ids: set[str] = set()
    for index, item in enumerate(cases):
        case_id = item.get("id") if isinstance(item, dict) else None
        if not isinstance(case_id, str) or not case_id or case_id in seen_ids:
            raise ValueError(f"malformed prerequisite report: case {index} has invalid identity")
        seen_ids.add(case_id)
        metrics = item.get("metrics")
        if not isinstance(metrics, dict):
            raise ValueError(f"malformed prerequisite report: case {case_id!r} needs metrics")
        for field, expected_type in required_metrics.items():
            value = metrics.get(field)
            if not isinstance(value, expected_type) or (
                expected_type is int and isinstance(value, bool)
            ):
                raise ValueError(
                    f"malformed prerequisite report: case {case_id!r} metric "
                    f"{field!r} must be {expected_type.__name__}"
                )
    return source


def _load_host_enforcement() -> dict[str, Any]:
    matrix = _read_json(HOST_ENFORCEMENT, "host enforcement matrix")
    if matrix.get("schema_version") != 3 or not isinstance(matrix.get("hosts"), dict):
        raise ValueError("host enforcement matrix must use schema_version 3 and contain hosts")
    for host in ("codex", "claude", "copilot"):
        entry = matrix["hosts"].get(host)
        if not isinstance(entry, dict) or entry.get("utility_no_edit") != "prompt-enforced":
            raise ValueError(f"{host}: utility_no_edit must be prompt-enforced")
    return matrix


def _validate_declared_dependency() -> None:
    core = _read_json(CORE_CONTRACTS, "Core contract")
    contract = core.get("principle_acceptance_contract")
    producers = contract.get("producers") if isinstance(contract, dict) else None
    producer = next(
        (
            item
            for item in producers or []
            if isinstance(item, dict) and item.get("id") == "eval-context-control"
        ),
        None,
    )
    if not isinstance(producer, dict) or producer.get("depends_on") != EXPECTED_DEPENDENCIES:
        raise ValueError(
            "Core eval-context-control dependency must be "
            "eval-agent-lightweight then eval-rendered-context"
        )


def _load_rendered_context_report(
    expected_case_ids: set[str],
    expected_long_case_ids: set[str],
    expected_fixture_schema_version: int,
    path: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    report_path = RENDERED_CONTEXT_REPORT if path is None else path
    report = _read_json(
        report_path,
        "rendered-context report",
        "run all three builds and scripts/eval-rendered-context-budget.py first",
    )
    if report.get("schema_version") != EXPECTED_REPORT_SCHEMA_VERSION:
        raise ValueError(
            f"rendered-context report must use schema_version {EXPECTED_REPORT_SCHEMA_VERSION}"
        )
    if report.get("fixture_schema_version") != expected_fixture_schema_version:
        raise ValueError(
            "rendered-context report fixture_schema_version does not match the lightweight report"
        )
    if report.get("status") != "pass":
        raise ValueError(
            "rendered-context report did not pass: expected status 'pass', "
            f"got {report.get('status')!r}"
        )
    if report.get("evidence_scope") != "deterministic-rendered-artifacts":
        raise ValueError("rendered-context report has wrong evidence_scope")
    if report.get("tokenizer") != "o200k_base":
        raise ValueError("rendered-context report must use tokenizer='o200k_base'")
    if report.get("build_profiles") != ["recommended", "full", "dev"]:
        raise ValueError("rendered-context report must cover recommended/full/dev")
    if report.get("hosts") != ["codex", "claude", "copilot"]:
        raise ValueError("rendered-context report must cover codex/claude/copilot")
    if report.get("errors") != [] or not isinstance(report.get("aggregate"), dict):
        raise ValueError("passing rendered-context report has malformed outer evidence")
    limitations = report.get("limitations")
    if not isinstance(limitations, list) or any(not isinstance(item, str) for item in limitations):
        raise ValueError("rendered-context report limitations must be strings")
    cases = report.get("cases")
    case_ids = [item.get("id") for item in cases or [] if isinstance(item, dict)]
    if (
        not isinstance(cases, list)
        or len(case_ids) != len(cases)
        or len(case_ids) != len(set(case_ids))
        or set(case_ids) != expected_case_ids
        or report.get("fixture_count") != len(cases)
    ):
        raise ValueError("rendered-context report fixture IDs/count do not match lightweight report")
    transfer = report.get("transferred_context")
    if not isinstance(transfer, dict):
        raise ValueError("rendered-context report needs transferred_context summary")
    source_scope = transfer.get("source_scope")
    if not isinstance(source_scope, dict) or not source_scope or any(
        not isinstance(value, str) or not value for value in source_scope.values()
    ):
        raise ValueError("rendered-context transferred_context source scope is missing")
    rows = transfer.get("long_task_rows")
    row_ids = [item.get("id") for item in rows or [] if isinstance(item, dict)]
    if (
        not isinstance(rows, list)
        or len(row_ids) != len(rows)
        or len(row_ids) != len(set(row_ids))
        or set(row_ids) != expected_long_case_ids
        or transfer.get("long_task_selector_join_count") != len(rows)
    ):
        raise ValueError("rendered-context long-task rows do not match lightweight required progress")
    missing_summary = [field for field in TRANSFER_SUMMARY_FIELDS if field not in transfer]
    if missing_summary:
        raise ValueError(
            "rendered-context transferred_context summary is missing: "
            + ", ".join(missing_summary)
        )
    semantic = transfer["semantic_baseline"]
    if not isinstance(semantic, dict) or semantic.get("retained_semantic_equality") is not True:
        raise ValueError("rendered-context semantic equality evidence is missing")
    decision = transfer.get("context_compaction_decision")
    if not isinstance(decision, dict) or not {
        "classification",
        "observed_conservative_ratio",
        "minimum_realized_reduction_ratio",
        "target_realized_reduction_ratio",
    }.issubset(decision):
        raise ValueError("rendered-context context compaction decision is missing")
    summary = {field: transfer[field] for field in TRANSFER_SUMMARY_FIELDS}
    return report, summary, decision


def _args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-projection", action="store_true")
    parser.add_argument("--reports-dir", type=Path, default=REPORT_JSON.parent)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _args(argv)
    source_path = args.reports_dir / SOURCE_REPORT.name
    rendered_path = args.reports_dir / RENDERED_CONTEXT_REPORT.name
    report_json, report_markdown = report_output_paths(
        args.reports_dir, REPORT_JSON.name, REPORT_MD.name
    )
    try:
        source = _load_source_report(source_path)
        enforcement = _load_host_enforcement()
        _validate_declared_dependency()
        cases = source["cases"]
        expected_long_case_ids = {
            str(item["id"])
            for item in cases
            if item["metrics"].get("required_progress_for_multi_agent")
        }
        rendered, transfer_summary, compaction_decision = _load_rendered_context_report(
            {str(item["id"]) for item in cases},
            expected_long_case_ids,
            int(source["fixture_schema_version"]),
            rendered_path,
        )
    except ValueError as exc:
        print(f"eval-context-control-plane: ERROR: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    for item in cases:
        metrics = item["metrics"]
        if metrics.get("preparation_loop_detected"):
            errors.append(f"{item['id']}: preparation loop detected")
        if metrics.get("parallel_write_conflict"):
            errors.append(f"{item['id']}: parallel write conflict detected")
        if metrics.get("loaded_skill_count", 0) > 9:
            errors.append(f"{item['id']}: more than nine bounded Skill loads")
        if metrics.get("required_progress_for_multi_agent") and not metrics.get(
            "required_multi_agent_progress_satisfied"
        ):
            errors.append(f"{item['id']}: required multi-agent progress gate failed")
    by_id = {str(item["id"]): item for item in cases}
    conditional = by_id.get("isolated-write-parallel-contract", {}).get("metrics", {})
    shared = by_id.get("shared-workspace-serial-write", {}).get("metrics", {})
    utility_rows = [item for item in cases if item.get("fixture_group") == "utility"]
    if not conditional.get("conditional_isolated_write_contract"):
        errors.append("missing passing conditional isolated-write parallel contract")
    if not shared.get("shared_workspace_writes_serial"):
        errors.append("missing passing shared-workspace serial-write contract")
    if not utility_rows or any(
        not item["metrics"].get("utility_workspace_diff_unchanged") for item in utility_rows
    ):
        errors.append("utility no-edit workspace diff gate did not pass for every utility")
    hosts = enforcement["hosts"]
    unsupported = all(
        hosts[host].get("isolated_workspace") == "unsupported"
        for host in ("codex", "claude", "copilot")
    )
    if not unsupported:
        errors.append("declared supported hosts unexpectedly claim isolated write workspaces")
    for path in (
        ROOT / "src" / "agent-profiles" / "role-agents.json",
        ROOT
        / "src"
        / "control-skills"
        / "engineering-control-plane"
        / "references"
        / "professional-skill-router.md",
    ):
        if not path.is_file():
            errors.append(f"missing source: {path.relative_to(ROOT)}")

    report = {
        "schema_version": EXPECTED_REPORT_SCHEMA_VERSION,
        "status": "pass" if not errors else "fail",
        "evidence_scope": EXPECTED_EVIDENCE_SCOPE,
        "limitations": list(
            dict.fromkeys(
                [
                    *source["limitations"],
                    *rendered["limitations"],
                    *transfer_summary["proof_limits"],
                ]
            )
        ),
        "fixture_count": len(cases),
        "checks": {
            "bounded_rendered_instruction_context": True,
            "no_preparation_loop": not any("preparation loop" in error for error in errors),
            "current_write_parallelism_unsupported": unsupported,
            "shared_workspace_serial_write": bool(shared.get("shared_workspace_writes_serial")),
            "conditional_isolated_write_contract": bool(
                conditional.get("conditional_isolated_write_contract")
            ),
            "utility_no_edit_workspace_gate": bool(utility_rows)
            and all(item["metrics"].get("utility_workspace_diff_unchanged") for item in utility_rows),
            "route_once_skill_budget": not any("Skill loads" in error for error in errors),
            "transferred_context_measurement_valid": True,
        },
        "rendered_context_summary": rendered["aggregate"],
        "transferred_context_summary": transfer_summary,
        "context_compaction_decision": compaction_decision,
        "errors": errors,
    }
    args.reports_dir.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    classification = compaction_decision["classification"]
    observed_ratio = compaction_decision["observed_conservative_ratio"]
    lines = [
        "# Context Control Plane Evaluation",
        "",
        f"Status: **{report['status']}**",
        "",
        f"Evidence scope: **{report['evidence_scope']}**",
        "",
        f"Observable fixture count: **{len(cases)}**",
        "",
        "This evaluation consumes the current rendered context measurement and verifies the remaining deterministic control-plane boundaries.",
        "",
        "## Context Compaction Continuation Decision",
        "",
        f"Producer-observed conservative ratio: **{observed_ratio}**; classification: **{classification}**.",
        "",
        "The producer classification is measurement-only and does not add a Gate.",
        "",
        "## Limitations",
        "",
        *[f"- {item}" for item in report["limitations"]],
        "",
    ]
    if errors:
        lines.extend(["## Errors", "", *[f"- {error}" for error in errors], ""])
    if args.release_projection:
        report_markdown.write_text("\n".join(lines), encoding="utf-8")
    if errors:
        for error in errors:
            print(f"eval-context-control-plane: ERROR: {error}", file=sys.stderr)
        return 1
    print(f"eval-context-control-plane: validated {len(cases)} bounded hookless trajectories.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
