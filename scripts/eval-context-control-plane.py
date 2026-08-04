#!/usr/bin/env python3
"""Evaluate hookless context boundaries and early productive action."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validation_utils import PROMPT_CONTRACT_MODEL


ROOT = Path(__file__).resolve().parents[1]
SOURCE_REPORT = ROOT / "reports" / "hookless-control-plane-eval.json"
RENDERED_CONTEXT_REPORT = ROOT / "reports" / "rendered-context-budget.json"
HOST_ENFORCEMENT = ROOT / "src" / "agent-profiles" / "host-enforcement.json"
CONTROL_PROMPT = ROOT / "src" / "control-prompts" / "main-control-agent.md"
REPORT_JSON = ROOT / "reports" / "context-control-plane-eval.json"
REPORT_MD = ROOT / "reports" / "context-control-plane-eval.md"
EXPECTED_EVIDENCE_SCOPE = "deterministic-fixtures"
EXPECTED_REPORT_SCHEMA_VERSION = 2
EXPECTED_FIXTURE_SCHEMA_VERSION = 2


def _load_source_report() -> dict[str, Any]:
    try:
        raw = SOURCE_REPORT.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValueError(
            f"missing prerequisite report: {SOURCE_REPORT}; "
            "run scripts/eval-agent-lightweight.py first"
        ) from exc
    except OSError as exc:
        raise ValueError(f"cannot read prerequisite report {SOURCE_REPORT}: {exc}") from exc

    try:
        source = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"malformed prerequisite report {SOURCE_REPORT}: invalid JSON: {exc}"
        ) from exc
    if not isinstance(source, dict):
        raise ValueError(
            f"malformed prerequisite report {SOURCE_REPORT}: root must be an object"
        )
    if source.get("schema_version") != EXPECTED_REPORT_SCHEMA_VERSION:
        raise ValueError(
            f"prerequisite report must use schema_version {EXPECTED_REPORT_SCHEMA_VERSION}"
        )
    if source.get("fixture_schema_version") != EXPECTED_FIXTURE_SCHEMA_VERSION:
        raise ValueError(
            "prerequisite report has stale fixture_schema_version"
        )

    status = source.get("status")
    if status != "pass":
        raise ValueError(
            f"prerequisite report did not pass: expected status 'pass', got {status!r}"
        )
    evidence_scope = source.get("evidence_scope")
    if evidence_scope != EXPECTED_EVIDENCE_SCOPE:
        raise ValueError(
            "prerequisite report has wrong evidence_scope: "
            f"expected {EXPECTED_EVIDENCE_SCOPE!r}, got {evidence_scope!r}"
        )

    cases = source.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError(
            f"malformed prerequisite report {SOURCE_REPORT}: cases must be a non-empty list"
        )
    if source.get("fixture_count") != len(cases):
        raise ValueError(
            f"malformed prerequisite report {SOURCE_REPORT}: "
            "fixture_count must equal the number of cases"
        )
    limitations = source.get("limitations")
    if not isinstance(limitations, list) or any(
        not isinstance(item, str) for item in limitations
    ):
        raise ValueError(
            f"malformed prerequisite report {SOURCE_REPORT}: limitations must be a list of strings"
        )

    required_metrics = {
        "preparation_loop_detected": bool,
        "parallel_write_conflict": bool,
        "loaded_skill_count": int,
        "loaded_layer3_reference_count": int,
        "required_multi_agent_progress_satisfied": bool,
    }
    for index, item in enumerate(cases):
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
            raise ValueError(
                f"malformed prerequisite report {SOURCE_REPORT}: case {index} needs a non-empty id"
            )
        metrics = item.get("metrics")
        if not isinstance(metrics, dict):
            raise ValueError(
                f"malformed prerequisite report {SOURCE_REPORT}: "
                f"case {item['id']!r} needs a metrics object"
            )
        for field, expected_type in required_metrics.items():
            value = metrics.get(field)
            if not isinstance(value, expected_type) or (
                expected_type is int and isinstance(value, bool)
            ):
                raise ValueError(
                    f"malformed prerequisite report {SOURCE_REPORT}: "
                    f"case {item['id']!r} metric {field!r} must be "
                    f"{expected_type.__name__}"
                )
    return source


def _load_host_enforcement() -> dict[str, Any]:
    try:
        matrix = json.loads(HOST_ENFORCEMENT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read host enforcement matrix {HOST_ENFORCEMENT}: {exc}") from exc
    if not isinstance(matrix, dict) or matrix.get("schema_version") != 3:
        raise ValueError("host enforcement matrix must use schema_version 3")
    hosts = matrix.get("hosts")
    if not isinstance(hosts, dict):
        raise ValueError("host enforcement matrix must contain hosts")
    for host in ("codex", "claude", "copilot"):
        entry = hosts.get(host)
        if not isinstance(entry, dict):
            raise ValueError(f"host enforcement matrix is missing {host}")
        if entry.get("utility_no_edit") != "prompt-enforced":
            raise ValueError(f"{host}: utility_no_edit must be prompt-enforced")
    return matrix


def _load_rendered_context_report(
    expected_case_ids: set[str],
    expected_fixture_schema_version: int,
) -> dict[str, Any]:
    try:
        raw = RENDERED_CONTEXT_REPORT.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValueError(
            f"missing rendered-context report: {RENDERED_CONTEXT_REPORT}; "
            "run all three builds and scripts/eval-rendered-context-budget.py first"
        ) from exc
    except OSError as exc:
        raise ValueError(
            f"cannot read rendered-context report {RENDERED_CONTEXT_REPORT}: {exc}"
        ) from exc
    try:
        report = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"malformed rendered-context report {RENDERED_CONTEXT_REPORT}: {exc}"
        ) from exc
    if not isinstance(report, dict):
        raise ValueError("rendered-context report root must be an object")
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
            "rendered-context report did not pass: "
            f"expected status 'pass', got {report.get('status')!r}"
        )
    if report.get("evidence_scope") != "deterministic-rendered-artifacts":
        raise ValueError(
            "rendered-context report has wrong evidence_scope: "
            f"{report.get('evidence_scope')!r}"
        )
    if report.get("tokenizer") != "o200k_base":
        raise ValueError("rendered-context report must use tokenizer='o200k_base'")
    cases = report.get("cases")
    if not isinstance(cases, list):
        raise ValueError("rendered-context report cases must be a list")
    actual_case_ids = {
        item.get("id")
        for item in cases
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    if actual_case_ids != expected_case_ids or report.get("fixture_count") != len(cases):
        raise ValueError(
            "rendered-context report fixture IDs/count do not match the lightweight report"
        )
    if report.get("build_profiles") != ["recommended", "full", "dev"]:
        raise ValueError("rendered-context report must cover recommended/full/dev")
    if report.get("hosts") != ["codex", "claude", "copilot"]:
        raise ValueError("rendered-context report must cover codex/claude/copilot")
    if report.get("errors") != []:
        raise ValueError("passing rendered-context report must have no errors")
    return report


def main() -> int:
    try:
        source = _load_source_report()
        enforcement = _load_host_enforcement()
        rendered = _load_rendered_context_report(
            {str(item["id"]) for item in source.get("cases", [])},
            int(source["fixture_schema_version"]),
        )
    except ValueError as exc:
        print(f"eval-context-control-plane: ERROR: {exc}", file=sys.stderr)
        return 1
    cases = source.get("cases", [])
    errors: list[str] = []
    for item in cases:
        metrics = item.get("metrics", {})
        if metrics.get("preparation_loop_detected"):
            errors.append(f"{item.get('id')}: preparation loop detected")
        if metrics.get("parallel_write_conflict"):
            errors.append(f"{item.get('id')}: parallel write conflict detected")
        if metrics.get("loaded_skill_count", 0) > 9:
            errors.append(f"{item.get('id')}: more than nine bounded Skill loads")
        if metrics.get("required_progress_for_multi_agent") and not metrics.get(
            "required_multi_agent_progress_satisfied"
        ):
            errors.append(f"{item.get('id')}: required multi-agent progress gate failed")

    by_id = {str(item.get("id")): item for item in cases}
    conditional = by_id.get("isolated-write-parallel-contract", {}).get("metrics", {})
    shared = by_id.get("shared-workspace-serial-write", {}).get("metrics", {})
    utility_rows = [
        item for item in cases if item.get("fixture_group") == "utility"
    ]
    if not conditional.get("conditional_isolated_write_contract"):
        errors.append("missing passing conditional isolated-write parallel contract")
    if not shared.get("shared_workspace_writes_serial"):
        errors.append("missing passing shared-workspace serial-write contract")
    if not utility_rows or any(
        not item.get("metrics", {}).get("utility_workspace_diff_unchanged")
        for item in utility_rows
    ):
        errors.append("utility no-edit workspace diff gate did not pass for every utility")

    supported_hosts = enforcement["hosts"]
    current_write_parallelism_unsupported = all(
        supported_hosts[host].get("isolated_workspace") == "unsupported"
        for host in ("codex", "claude", "copilot")
    )
    if not current_write_parallelism_unsupported:
        errors.append("declared supported hosts unexpectedly claim isolated write workspaces")
    prompt_text = CONTROL_PROMPT.read_text(encoding="utf-8")
    normalized_prompt_text = prompt_text.casefold()
    serial_shared_writes = next(
        concept
        for concept in PROMPT_CONTRACT_MODEL["concepts"]
        if concept["id"] == "serial-shared-writes"
    )
    current_read_parallelism_declared = all(
        term.casefold() in normalized_prompt_text
        for term in serial_shared_writes["required_terms"]
    )
    if not current_read_parallelism_declared:
        errors.append("control prompt does not declare current read-only parallelism")

    required_sources = (
        ROOT / "src" / "control-prompts" / "main-control-agent.md",
        ROOT / "src" / "agent-profiles" / "role-agents.json",
        ROOT / "src" / "control-skills" / "engineering-control-plane" / "references" / "professional-skill-router.md",
    )
    for path in required_sources:
        if not path.is_file():
            errors.append(f"missing source: {path.relative_to(ROOT)}")

    report = {
        "schema_version": 2,
        "status": "pass" if not errors else "fail",
        "evidence_scope": "deterministic-fixtures",
        "limitations": list(
            dict.fromkeys(
                [
                    *source.get("limitations", []),
                    *rendered.get("limitations", []),
                ]
            )
        ),
        "fixture_count": len(cases),
        "checks": {
            "bounded_rendered_instruction_context": rendered.get("status") == "pass",
            "no_preparation_loop": not any("preparation loop" in error for error in errors),
            "current_read_only_parallelism_declared": current_read_parallelism_declared,
            "current_write_parallelism_unsupported": current_write_parallelism_unsupported,
            "shared_workspace_serial_write": bool(
                shared.get("shared_workspace_writes_serial")
            ),
            "conditional_isolated_write_contract": bool(
                conditional.get("conditional_isolated_write_contract")
            ),
            "utility_no_edit_workspace_gate": bool(utility_rows)
            and all(
                item.get("metrics", {}).get("utility_workspace_diff_unchanged")
                for item in utility_rows
            ),
            "route_once_skill_budget": not any("Skill loads" in error for error in errors),
        },
        "rendered_context_summary": rendered.get("aggregate"),
        "errors": errors,
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Context Control Plane Evaluation",
        "",
        f"Status: **{report['status']}**",
        "",
        f"Evidence scope: **{report['evidence_scope']}**",
        "",
        f"Observable fixture count: **{len(cases)}**",
        "",
        "This evaluation combines deterministic rendered instruction-token budgets with route-once loading, progress density, prompt-enforced Utility workspace checks, current shared-workspace serial writes, and a conditional isolated-write contract. It does not claim current isolated-write support.",
        "",
        "## Limitations",
        "",
        *[f"- {item}" for item in report["limitations"]],
        "",
    ]
    if errors:
        lines.extend(["## Errors", "", *[f"- {error}" for error in errors], ""])
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    if errors:
        for error in errors:
            print(f"eval-context-control-plane: ERROR: {error}", file=sys.stderr)
        return 1
    print(f"eval-context-control-plane: validated {len(cases)} bounded hookless trajectories.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
