#!/usr/bin/env python3
"""Evaluate behavior and structural cost from deterministic, visible task traces.

This evaluator is not a runtime task engine. Trace events are test inputs, and
negative controls deliberately violate a single engineering requirement.
"""
from __future__ import annotations

import argparse
import fnmatch
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


def _owner_discovery_errors(case: dict[str, Any]) -> list[str]:
    """Judge fixture decisions against a separate source-anchored oracle.

    The repository contains tiny authored source examples, not owner labels.
    The oracle is evaluator-only: no paths from it are inserted into dispatch,
    search results, or reads. This is trace grading, not a runtime resolver or
    evidence that a live model would produce the accepted trace.
    """
    if "repository" not in case:
        return []
    repository = case["repository"]
    oracle = case["owner_oracle"]
    steps = case["steps"]
    errors = []
    if case.get("needed_sources") or any(s.get("needed_sources") for s in steps):
        errors.append("owner-oracle-leaked-as-needed-sources")
    decisions = [(i, s) for i, s in enumerate(steps) if s.get("action") == "owner-decision"]
    if len(decisions) != 1:
        return errors + ["missing-owner-decision"]
    index, decision = decisions[0]
    actor = decision.get("agent_id")
    before = [s for s in steps[:index] if s.get("agent_id") == actor]
    if not any(s.get("action") == "dispatch" and s.get("profile") == "task-agent" for s in before):
        errors.append("owner-discovery-not-task")
    reads = [s for s in before if s.get("action") == "read"]
    observed = {s.get("path") for s in reads if s.get("current") is True
                and s.get("content") == repository.get(s.get("path"))
                and s.get("path") in repository}
    if len(observed) != len({s.get("path") for s in reads}):
        errors.append("owner-source-not-current")

    def anchored(anchor: dict[str, str], *, read: bool = True) -> bool:
        path, quote = anchor.get("path"), anchor.get("quote")
        return bool(quote and path in repository and quote in repository[path]
                    and (not read or path in observed))

    evidence = decision.get("evidence", [])
    if not evidence or not all(anchored(anchor) for anchor in evidence):
        errors.append("owner-evidence-not-read")
    required = oracle["authority"]
    if not required or not all(anchored(anchor, read=False) for anchor in required):
        errors.append("owner-oracle-source-mismatch")
    if any(anchor not in evidence for anchor in required):
        errors.append("owner-authority-not-established")
    if (set(decision.get("owners", [])) != set(oracle["owners"])
            or decision.get("outcome") != oracle.get("outcome", "edit")):
        errors.append("wrong-owner-decision")
    if not set(oracle["impact"]) <= observed:
        errors.append("owner-impact-not-closed")
    candidates = [s for s in before if s.get("action") == "candidate-owner"]
    if not candidates or any(s.get("path") not in observed for s in candidates):
        errors.append("candidate-not-read")
    searches = [s for s in before if s.get("action") == "search"]
    for search in searches:
        scope, query = search.get("path", ""), search.get("query", "")
        scanned = [path for path in repository if fnmatch.fnmatchcase(path, scope)]
        hits = {path for path in scanned if query and query in repository[path]}
        if not query or set(search.get("results", [])) != hits:
            errors.append("owner-search-not-source-backed")
        if scope in {"*", "**", "**/*", "."} or len(scanned) > oracle.get("max_search_files", 6):
            errors.append("owner-search-unbounded")
    competing = [s for s in searches if s.get("purpose") == "competing-owner"]
    signal = oracle.get("competing_signal")
    if signal:
        # A targeted scan follows the source that exposes the alternative.
        valid_scans = [s for s in competing if any(
            r.get("action") == "read" and r.get("current") is True
            and r.get("path") == signal["path"]
            and r.get("content") == repository.get(signal["path"])
            for r in before[:before.index(s)])]
        if not anchored(signal) or not set(oracle["competing_hits"]) <= {
            path for s in valid_scans for path in s.get("results", [])
        }:
            errors.append("competing-owner-scan-missing")
    elif competing:
        errors.append("unsignaled-competing-owner-scan")
    if len(reads) > oracle["max_reads"] or len(searches) > oracle["max_searches"]:
        errors.append("owner-discovery-budget-exceeded")
    analyses = [i for i, s in enumerate(steps) if s.get("profile") == "analysis-agent"]
    reviews = [s for s in steps if s.get("profile") == "review-agent"]
    if oracle.get("outcome", "edit") == "analysis":
        if not analyses or min(analyses) <= index or any(s.get("action") == "edit" for s in steps):
            errors.append("unresolved-owner-not-escalated")
    elif analyses:
        errors.append("resolved-owner-escalated")
    if oracle.get("outcome", "edit") == "edit" and not set(oracle["owners"]) <= {
        s.get("path") for s in steps[index + 1:] if s.get("action") == "edit"
    }:
        errors.append("owner-enforcement-not-edited")
    if reviews:
        errors.append("routine-owner-review")
    if any(i <= index for i, s in enumerate(steps) if s.get("action") == "edit"):
        errors.append("edit-before-owner-confirmed")
    return errors


def evaluate_case(case: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    steps = case.get("steps", [])
    errors: list[str] = _owner_discovery_errors(case)
    dispatches = [(i, s) for i, s in enumerate(steps) if s.get("action") == "dispatch"]
    reads = [s for s in steps if s.get("action") in {"read", "search"}]
    edits = [(i, s) for i, s in enumerate(steps) if s.get("action") == "edit"]
    validations = [(i, s) for i, s in enumerate(steps) if s.get("action") == "validate"]
    unavailable = case.get("reproduction_unavailable")
    validation_assertion = case.get("assertion")
    if unavailable:
        # These are authored observations, not an agent-controlled waiver of RED.
        first_edit = min((i for i, _ in edits), default=len(steps))
        user_evidence = unavailable.get("user_evidence")
        supplied_limit = isinstance(user_evidence, str) and bool(user_evidence.strip()) and user_evidence in case.get("user_request", "")
        observed_limit = all(unavailable.get(k) for k in ("invocation", "output")) and any(
            s.get("action") == "tool-failure" and s.get("invocation") == unavailable.get("invocation")
            and s.get("output") == unavailable.get("output") for s in steps[:first_edit]
        )
        if not all(unavailable.get(k) for k in ("proof_limit", "available_assertion")) or not (supplied_limit or observed_limit):
            errors.append("unobserved-reproduction-limit")
        completions = [s for s in steps if s.get("action") == "complete"]
        if not completions or any(s.get("status") != "partial" or
                s.get("proof_limit") != unavailable.get("proof_limit") for s in completions):
            errors.append("unverified-completion-claim")
        validation_assertion = unavailable.get("available_assertion")
    for index, dispatch in dispatches:
        try:
            validate_and_render_fixture_capsule(dispatch)
        except (FixtureCapsuleError, TypeError) as exc:
            errors.append(f"selection: {exc}")
        profile = dispatch.get("profile")
        asset_read = dispatch.get("purpose") == "routing-asset-read"
        if asset_read:
            assets = case.get("routing_assets", {})
            named = dispatch.get("asset_paths", [])
            if (profile != "analysis-agent" or dispatch.get("primary_skill") != "engineering-change-analysis"
                    or dispatch.get("layer3_skills") or not named or not set(named) <= set(assets)):
                errors.append("invalid-routing-asset-read")
            for step in steps[index + 1:]:
                if step.get("agent_id") != dispatch.get("agent_id"):
                    continue
                if step.get("action") == "route":
                    errors.append("routing-reader-rerouted")
                if step.get("action") in {"read", "search"} and (
                    step.get("action") != "read" or step.get("path") not in named
                    or step.get("content") != assets.get(step.get("path")) or step.get("current") is not True
                ):
                    errors.append("routing-reader-outside-assets")
        if profile in {"analysis-agent", "review-agent"}:
            request_pattern = r"\breview\b" if profile == "review-agent" else r"\b(analy[sz]e|design|diagnose)\b"
            requested = bool(re.search(request_pattern, case.get("user_request", ""), re.I))
            question = any(s.get("action") == "question" and s.get("changes_implementation")
                           and s.get("evidence") for s in steps[:index])
            if not dispatch.get("reason") or not (requested or question or asset_read):
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
            diff_requested = bool(re.search(r"\bdiff\b", case.get("user_request", "") + " " + dispatch.get("goal", ""), re.I))
            if not changed <= diff_paths or diff_requested and not diff_paths:
                errors.append("review-missing-actual-diff")
            if not diff_paths <= observed:
                errors.append("review-missing-current-source")
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
        if (case.get("bugfix") and not unavailable) or case.get("test_first_reason"):
            red = [s for i, s in validations if i < index and s.get("result") == "fail"]
            if not any(s.get("failure") == "target-behavior-missing" and s.get("assertion") == case.get("assertion")
                       and s.get("output") for s in red):
                errors.append("missing-target-red")
    if edits:
        last_edit = max(i for i, _ in edits)
        passed = [s for i, s in validations if i > last_edit and s.get("result") == "pass" and s.get("output")]
        relevant = [s for i, s in validations if i > last_edit and
                    (not validation_assertion or s.get("assertion") == validation_assertion)]
        if relevant and relevant[-1].get("result") != "pass":
            errors.append("latest-validation-failed")
        if not passed:
            errors.append("missing-post-final-edit-validation")
        elif validation_assertion and not any(s.get("assertion") == validation_assertion for s in passed):
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
            if s.get("retry_target"):
                previous = [p for p in steps[:index] if p.get("action") == "execute"
                            and p.get("retry_target") == s["retry_target"]]
                # Compare the command and actual supplied material, never Task ID,
                # agent name, or a claimed new approach label.
                failures = []
                for prior in reversed(previous):
                    if prior.get("result") != "fail" or failures and any(
                        prior.get(k) != failures[0].get(k) for k in ("invocation", "material")
                    ):
                        break
                    failures.append(prior)
                if len(failures) >= 2:
                    if all(s.get(k) == failures[0].get(k) for k in ("invocation", "material")):
                        errors.append("unchanged-retry-after-two-failures")
                    elif not s.get("basis") or not any(
                        p.get("action") == "read" and p.get("current") is True and p.get("content") == s["basis"]
                        or p.get("action") in {"execute", "validate", "tool-failure"} and p.get("output") == s["basis"]
                        for p in steps[steps.index(failures[-1]) + 1:index]
                    ):
                        errors.append("retry-change-without-evidence")
        if s.get("action") == "user-update":
            active = {d["agent_id"] for i, d in dispatches if i < index and d.get("profile") == "task-agent"
                      and not any(p.get("action") in {"complete", "stop"} and p.get("agent_id") == d["agent_id"]
                                  for p in steps[i + 1:index])}
            following = steps[index + 1:]
            if any(not any(p.get("action") == "notify" and p.get("agent_id") == agent
                           and p.get("request") == s.get("request") for p in following) for agent in active):
                errors.append("user-update-not-propagated")
            for p in following:
                if p.get("action") == "user-update":
                    break
                paths = [p.get("path", "")] if p.get("action") in {"edit", "accept-result"} else p.get("write_targets", [])
                if any(not _in_scope(path, s.get("write_scope", [])) for path in paths):
                    if p.get("action") in {"edit", "execute"}:
                        errors.append("write-after-user-scope-change")
                    elif p.get("action") == "accept-result":
                        errors.append("superseded-result-accepted")
        if s.get("action") == "finding" and not all(s.get(k) for k in ("defect", "evidence", "reachable_failure", "required_action")):
            errors.append("finding-without-failure-mechanism")
        if s.get("action") == "tool-failure" and not all(s.get(k) for k in ("invocation", "output")):
            errors.append("unobserved-tool-failure")
        if s.get("action") == "external-read" and (actor_assignment.get("profile") != "analysis-agent" or s.get("sensitive_data_sent")):
            errors.append("external-read-boundary")
    # Different queries over one bounded scope are distinct observations;
    # relabeling a repeated query's purpose does not make it fresh evidence.
    keys = [(s.get("agent_id"), s.get("action"), s.get("path"), s.get("revision"),
             s.get("query") if s.get("action") == "search" else None) for s in reads]
    metrics = {
        "subagent_count": len(dispatches),
        "control_turn_count": len(dispatches) + 1,
        "duplicate_read_count": len(keys) - len(set(keys)),
        "verification_action_count": len(validations),
        "first_edit_step": min((i+1 for i, _ in edits), default=None),
        "analysis_dispatch_count": sum(s.get("profile") == "analysis-agent" for _, s in dispatches),
        "review_dispatch_count": sum(s.get("profile") == "review-agent" for _, s in dispatches),
        "loaded_skill_count": sum(1 + len(s.get("layer3_skills", [])) for _, s in dispatches),
        "source_read_count": sum(s.get("action") == "read" for s in reads),
        "source_search_count": sum(s.get("action") == "search" for s in reads),
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
