#!/usr/bin/env python3
"""Evaluate behavior and structural cost from deterministic, visible task traces.

This evaluator is not a runtime task engine. Trace events are test inputs, and
negative controls deliberately violate a single engineering requirement.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from fixture_capsule_contract import FixtureCapsuleError, validate_and_render_fixture_capsule
from validation_utils import _target_in_task_scope, report_output_paths, unified_diff_paths

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "evals/agent-light-trajectories/cases.yaml"
REPORT_JSON = ROOT / "reports/hookless-control-plane-eval.json"
REPORT_MD = ROOT / "reports/hookless-control-plane-eval.md"
LIMITATIONS = [
    "Deterministic traces test authored behavior and structural counts, not live Agent dispatch or wall-clock performance.",
    "Fixture tool outcomes are simulated; they do not prove Host startup, sandbox enforcement, real-host accuracy, production behavior, or installed user experience.",
]


def _in_scope(path: str, scope: list[str]) -> bool:
    return _target_in_task_scope(path, scope, ROOT)


def evaluate_case(case: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    steps = case.get("steps", [])
    errors: list[str] = []
    dispatches = [(i, s) for i, s in enumerate(steps) if s.get("action") == "dispatch"]
    reads = [s for s in steps if s.get("action") in {"read", "search"}]
    edits = [(i, s) for i, s in enumerate(steps) if s.get("action") == "edit"]
    validations = [(i, s) for i, s in enumerate(steps) if s.get("action") == "validate"]
    for index, dispatch in dispatches:
        try:
            validate_and_render_fixture_capsule(dispatch)
        except (FixtureCapsuleError, TypeError) as exc:
            errors.append(f"selection: {exc}")
        profile = dispatch.get("profile")
        if profile in {"analysis-agent", "review-agent"}:
            request_pattern = r"\breview\b" if profile == "review-agent" else r"\b(analy[sz]e|design|diagnose)\b"
            requested = bool(re.search(request_pattern, case.get("user_request", ""), re.I))
            question = any(s.get("action") == "question" and s.get("changes_implementation")
                           and s.get("evidence") for s in steps[:index])
            if not dispatch.get("reason") or not (requested or question):
                errors.append("extra-agent-without-question")
        if profile == "review-agent":
            if dispatch.get("agent_id") in {s.get("agent_id") for _, s in edits}:
                errors.append("review-not-independent")
            required = {s.get("path") for i, s in edits if i < index} | set(dispatch.get("needed_sources", []))
            observed = {s.get("path") for s in steps[index + 1:] if s.get("action") == "read"
                        and s.get("current") is True and s.get("agent_id") == dispatch.get("agent_id")}
            if not required or not required <= observed:
                errors.append("review-missing-current-source")
            changed = {s.get("path") for i, s in edits if i < index}
            diff_paths = set()
            for s in steps[index + 1:]:
                if (s.get("action") == "read" and s.get("current") is True
                        and s.get("agent_id") == dispatch.get("agent_id")):
                    diff_paths.update(unified_diff_paths(s.get("diff")) or [])
            if not changed <= diff_paths:
                errors.append("review-missing-actual-diff")
        if profile == "analysis-agent" and not any(
            s.get("action") == "read" and s.get("current") is True and
            s.get("agent_id") == dispatch.get("agent_id") for s in steps[index + 1:]
        ):
            errors.append("analysis-missing-current-source")
        if profile == "analysis-agent" and any(s.get("action") == "edit" and
               s.get("agent_id") == dispatch.get("agent_id") for s in steps):
            errors.append("analysis-write")
        earlier = [s for _, s in dispatches if s is not dispatch and steps.index(s) < index]
        if profile in {"analysis-agent", "review-agent"} and any(
            s.get("profile") == profile and s.get("reason") == dispatch.get("reason") for s in earlier
        ) and not dispatch.get("new_evidence"):
            errors.append("repeated-judgment-without-new-evidence")
    for index, edit in edits:
        assignment = next((s for i, s in reversed(dispatches) if i < index and
                           s.get("agent_id") == edit.get("agent_id")), None)
        if not assignment or assignment.get("profile") != "task-agent":
            errors.append("edit-without-task-owner")
            continue
        if not _in_scope(edit.get("path", ""), assignment.get("write_scope", [])):
            errors.append("write-outside-scope")
        earlier = steps[:index]
        current_reads = [s for s in earlier if s.get("action") == "read" and s.get("current") is True
                         and s.get("agent_id") == edit.get("agent_id")]
        for needed in case.get("needed_sources", []):
            if not any(s.get("path") == needed for s in current_reads):
                errors.append("missing-current-source:" + needed)
        questions = [s for s in earlier if s.get("action") == "question" and s.get("changes_implementation")]
        for question in questions:
            if not any(s.get("action") == "answer" and s.get("question") == question.get("question")
                       and s.get("evidence") for s in earlier[earlier.index(question) + 1:]):
                errors.append("important-decision-unresolved")
        if edit.get("new_structure") and not any(
            s.get("action") == "read" and s.get("path") in case.get("structure_required_by", [])
            and s.get("current") is True for s in current_reads
        ):
            errors.append("unsupported-new-structure")
        if edit.get("uses_new_helper") and case.get("compatible_helper"):
            errors.append("compatible-owner-not-reused")
        if edit.get("test_only_public_api"):
            errors.append("test-only-api-widening")
        if edit.get("destructive") or edit.get("production") or edit.get("privilege_change"):
            if not edit.get("authorized"):
                errors.append("effect-not-authorized")
        if edit.get("untrusted_source") and edit.get("executable_sink") and edit.get("reachable"):
            if not edit.get("boundary_control"):
                errors.append("reachable-boundary-unprotected")
        if case.get("bugfix"):
            if not any(s.get("action") == "cause" and s.get("mechanism") == case.get("failure_mechanism")
                       and s.get("evidence") for s in earlier):
                errors.append("unproved-cause")
            if not any(s.get("action") == "search" and s.get("same_pattern") and s.get("complete") for s in earlier):
                errors.append("missing-same-pattern-scan")
        if case.get("bugfix") or case.get("test_first_reason"):
            red = [s for i, s in validations if i < index and s.get("result") == "fail"]
            if not any(s.get("failure") == "target-behavior-missing" and s.get("assertion") == case.get("assertion")
                       and s.get("output") for s in red):
                errors.append("missing-target-red")
    if edits:
        last_edit = max(i for i, _ in edits)
        passed = [s for i, s in validations if i > last_edit and s.get("result") == "pass" and s.get("output")]
        relevant = [s for i, s in validations if i > last_edit and
                    (not case.get("assertion") or s.get("assertion") == case["assertion"])]
        if relevant and relevant[-1].get("result") != "pass":
            errors.append("latest-validation-failed")
        if not passed:
            errors.append("missing-post-final-edit-validation")
        elif case.get("assertion") and not any(s.get("assertion") == case["assertion"] for s in passed):
            errors.append("changed-validation-oracle")
    # Actual temporal overlap, workspace isolation, and dependencies determine safe parallel writes.
    for i, left in edits:
        for j, right in edits:
            if i >= j or left.get("agent_id") == right.get("agent_id"):
                continue
            if max(left.get("start", i), right.get("start", j)) < min(left.get("end", i+1), right.get("end", j+1)):
                if (not left.get("isolated") or not right.get("isolated") or
                    left.get("workspace") == right.get("workspace") or
                    left.get("path") == right.get("path") or case.get("dependency")):
                    errors.append("parallel-write-conflict")
    for index, s in enumerate(steps):
        actor_assignment = next((d for i, d in reversed(dispatches) if i < index and
                                 d.get("agent_id") == s.get("agent_id")), {})
        if s.get("action") == "execute":
            if actor_assignment.get("profile") != "task-agent":
                errors.append("execute-without-task-owner")
            if (s.get("destructive") or s.get("production") or s.get("privilege_change")) and not s.get("authorized"):
                errors.append("effect-not-authorized")
            if any(not _in_scope(path, actor_assignment.get("write_scope", [])) for path in s.get("write_targets", [])):
                errors.append("write-outside-scope")
            if s.get("untrusted_source") and s.get("executable_sink") and s.get("reachable") and not s.get("boundary_control"):
                errors.append("reachable-boundary-unprotected")
        if s.get("action") == "finding" and not all(s.get(k) for k in ("defect", "evidence", "reachable_failure", "required_action")):
            errors.append("finding-without-failure-mechanism")
        if s.get("action") == "tool-failure" and not all(s.get(k) for k in ("invocation", "output")):
            errors.append("unobserved-tool-failure")
        if s.get("action") == "external-read" and (actor_assignment.get("profile") != "analysis-agent" or s.get("sensitive_data_sent")):
            errors.append("external-read-boundary")
    keys = [(s.get("agent_id"), s.get("path"), s.get("revision")) for s in reads]
    metrics = {
        "subagent_count": len(dispatches),
        "control_turn_count": len(dispatches) + 1,
        "duplicate_read_count": len(keys) - len(set(keys)),
        "verification_action_count": len(validations),
        "first_edit_step": min((i+1 for i, _ in edits), default=None),
        "analysis_dispatch_count": sum(s.get("profile") == "analysis-agent" for _, s in dispatches),
        "review_dispatch_count": sum(s.get("profile") == "review-agent" for _, s in dispatches),
        "loaded_skill_count": sum(1 + len(s.get("layer3_skills", [])) for _, s in dispatches),
        "parallel_write_conflict": "parallel-write-conflict" in errors,
        "preparation_loop_detected": "repeated-judgment-without-new-evidence" in errors,
    }
    return metrics, list(dict.fromkeys(errors))


def evaluate(document: dict[str, Any]) -> dict[str, Any]:
    cases = document.get("cases", [])
    negatives = document.get("negative_cases", [])
    errors = []
    results = []
    negative_results = []
    seen = set()
    if document.get("schema_version") != 2 or not cases or not negatives:
        errors.append("non-empty positive and negative behavioral fixtures required")
    for group, rows in (("cases", cases), ("negative_cases", negatives)):
        for case in rows:
            if not case.get("id") or case["id"] in seen:
                errors.append("duplicate or missing fixture ID")
            seen.add(case.get("id"))
            metrics, found = evaluate_case(case)
            expected = case.get("expected_errors", [])
            if group == "cases" and (expected or not case.get("steps") or not any(
                step.get("action") == "dispatch" for step in case.get("steps", [])
            )):
                errors.append(f"{case.get('id')}: positive fixture must exercise valid behavior")
            if group == "negative_cases" and not expected:
                errors.append(f"{case.get('id')}: negative fixture must reject a concrete defect")
            matches = sorted(found) == sorted(expected)
            if not matches:
                errors.append(f"{case.get('id')}: expected {expected!r}, got {found!r}")
            row = {"id": case.get("id"), "metrics": metrics, "errors": found, "matches_expected": matches}
            (results if group == "cases" else negative_results).append(row)
    aggregates = {key: {"max": max((row["metrics"][key] for row in results), default=0)} for key in (
        "subagent_count", "control_turn_count", "duplicate_read_count", "verification_action_count")}
    return {"schema_version": 2, "fixture_schema_version": 2,
            "status": "pass" if not errors else "fail", "evidence_scope": "deterministic-fixtures",
            "fixture_count": len(results), "negative_fixture_count": len(negative_results),
            "cases": results, "negative_cases": negative_results,
            "aggregate_structural_proxies": aggregates, "limitations": LIMITATIONS, "errors": errors}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports-dir", type=Path, default=REPORT_JSON.parent)
    parser.add_argument("--release-projection", action="store_true")
    parser.add_argument("--no-write-report", action="store_true")
    args = parser.parse_args(argv)
    report = evaluate(json.loads(FIXTURES.read_text()))
    if not args.no_write_report:
        out_json, out_md = report_output_paths(args.reports_dir, REPORT_JSON.name, REPORT_MD.name)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2) + "\n")
        if args.release_projection:
            out_md.write_text("# Control Plane Behavior\n\nStatus: " + report["status"] + "\n\n" +
                              "\n".join("- " + item for item in LIMITATIONS) + "\n")
    for error in report["errors"]:
        print("eval-agent-lightweight: ERROR: " + error)
    print(f"eval-agent-lightweight: {report['fixture_count']} positive and {report['negative_fixture_count']} negative fixtures: {report['status']}")
    return int(bool(report["errors"]))


if __name__ == "__main__":
    raise SystemExit(main())
