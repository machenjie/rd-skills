#!/usr/bin/env python3
"""Remind agents to close ChangeForge handoff evidence before stopping."""

from __future__ import annotations

import json
import hashlib
import re
import sys
from dataclasses import replace
from pathlib import Path

from changeforge_common import (
    clear_state,
    cwd_from_event,
    debug_log,
    detect_runtime,
    emit_stop_reminder,
    extract_diagnosis_closure_fields,
    event_name,
    extract_implementation_preflight_fields,
    extract_manifest_fields,
    extract_repository_context_fields,
    extract_senior_programming_judgment_fields,
    is_stop,
    load_state,
    merge_state,
    memory_closure_advice,
    read_event,
    repo_root,
    session_id_from_event,
    write_telemetry_event,
)
from changeforge_adapter_capabilities import adapter_capabilities_for
from changeforge_closure_contract import ClosureContract
from changeforge_executor_adapter_core import (
    snapshot_from_event_state,
    state_update_from_snapshot,
)
from changeforge_hook_policy import gate_mode_for_stage, run_gate_with_policy

try:
    from validation_broker import assess_validation_closure, classify_skill_behavior_change
except ModuleNotFoundError:  # Source tree layout: hook scripts live under src/hook-runtime.
    _src_root = Path(__file__).resolve().parents[2]
    if str(_src_root) not in sys.path:
        sys.path.insert(0, str(_src_root))
    try:
        from validation_broker import assess_validation_closure, classify_skill_behavior_change
    except Exception:  # pragma: no cover - hook runtime must fail open.
        assess_validation_closure = None
        classify_skill_behavior_change = None
except Exception:  # pragma: no cover - hook runtime must fail open.
    assess_validation_closure = None
    classify_skill_behavior_change = None


MAX_TRANSCRIPT_BYTES = 1_000_000
_GATE_RUNTIME = ""
MATERIAL_CHOICE_REVIEW_FINDING = "material_sdd_choice_without_user_resolution"

CLOSURE_KEYWORDS = {
    "skills": ["skill", "ChangeForge", "router", "路由", "技能"],
    "files": ["file", "changed", "修改", "文件"],
    "validation": ["test", "verify", "validation", "验证", "测试"],
    "risk": ["risk", "residual", "风险", "未验证"],
    "next": ["next", "下一步", "后续"],
}
WORKFLOW_CLOSURE_KEYWORDS = {
    "repository_context": [
        "repository context",
        "owning surface",
        "caller/callee",
        "caller-callee",
        "local convention",
    ],
    "workflow_state": [
        "workflow state",
        "current stage",
        "allowed transition",
        "owner/reviewer",
        "repair/re-review",
    ],
    "tool_permission_sandbox": [
        "tool permission",
        "sandbox",
        "permission state",
        "dry-run",
        "dry run",
        "redaction",
    ],
    "skill_efficacy": [
        "skill efficacy",
        "baseline",
        "treatment",
        "overhead",
        "eval fixture",
    ],
    "plan_execution_consistency": [
        "plan-execution consistency",
        "plan execution consistency",
        "accepted plan",
        "actual changed files",
        "plan vs",
    ],
    "validation_freshness": [
        "validation freshness",
        "fresh validation",
        "stale",
        "re-run",
        "rerun",
        "latest edit",
    ],
    "senior_programming_judgment": [
        "senior programming judgment",
        "senior_programming_judgment",
        "purpose",
        "facts",
        "objects",
        "states",
        "behaviors",
        "rules",
        "invariants",
        "failure contract",
        "validation map",
        "observability map",
    ],
}

# Success-implying completion language. Presence detection only: the gate never
# judges whether a claim is true, it only notices a completion claim so the
# closure can be checked for matching validation evidence.
COMPLETION_LANGUAGE = [
    "done",
    "completed",
    "complete",
    "fixed",
    "resolved",
    "ready for review",
    "all tests pass",
    "should pass",
    "should work",
    "works now",
    "everything works",
    "完成",
    "修复完毕",
    "已修复",
]

NEGATIVE_VALIDATION_PHRASES = [
    "not verified",
    "not run",
    "not tested",
    "unable to run",
    "unable to verify",
    "could not run",
    "cannot run",
    "did not run",
    "validation not run",
    "tests not run",
    "tests are unavailable",
    "test runner is not installed",
    "未验证",
    "没有运行",
    "无法运行",
    "未运行",
]
VALIDATION_COMMAND_RE = re.compile(
    r"\b("
    r"pytest|unittest|go\s+test|cargo\s+test|npm\s+test|pnpm\s+test|"
    r"yarn\s+test|python3?\s+-m\s+unittest|scripts/validate[\w./-]*|"
    r"validate[-_\w./]*|eval-routing|eval-agent-behavior|"
    r"eval-pressure-behavior|run-codegen-benchmarks|validate-installation|"
    r"build\.py"
    r")\b",
    re.IGNORECASE,
)
VALIDATION_OUTCOME_RE = re.compile(
    r"\b("
    r"exit\s*(code)?\s*0|return\s*code\s*0|0\s+errors?|0\s+failures?|"
    r"\d+\s+passed|passed|passes|succeeded|success|green|validated|ok|"
    r"通过|成功|退出码\s*0"
    r")\b",
    re.IGNORECASE,
)
VALIDATION_ARTIFACT_RE = re.compile(
    r"\b("
    r"output|artifact|report|log|junit|coverage|snapshot|build artifact"
    r")\b",
    re.IGNORECASE,
)

# Conditional keyword groups checked only when the matching structure gate fired
# this turn. They keep the closure reminder targeted instead of always demanding
# every kind of evidence.
CONDITIONAL_KEYWORDS = {
    "naming": ["naming", "命名", "filename", "文件名"],
    "reuse": ["reuse", "复用", "placement", "放置", "归属", "extension", "扩展"],
    "extension_safety": [
        "compatibility",
        "兼容",
        "behavior preserved",
        "旧行为",
        "行为保持",
        "extension",
        "扩展",
    ],
    "refactor": ["refactor", "重构", "class", "object", "inheritance", "reflection", "invariant"],
    "comments": [
        "comment",
        "doc comment",
        "注释",
        "文档注释",
        "godoc",
        "jsdoc",
        "javadoc",
        "docstring",
        "rustdoc",
        "test scenario",
        "regression",
        "edge case",
    ],
    "clarity": [
        "clarity",
        "main flow",
        "readability",
        "maintainability",
        "signature",
        "side effect",
        "cleanup",
        "deprecation",
        "feature flag",
        "change locality",
    ],
}
CONDITIONAL_GROUP_BY_STATE = {
    "file_naming_findings": "naming",
    "reuse_findings": "reuse",
    "extension_reuse_findings": "extension_safety",
    "advanced_refactor_findings": "refactor",
    "comment_findings": "comments",
    "structure_quality_findings": "clarity",
}
NO_CLOSURE_STAGES = {"", "question", "unknown", "no_engineering_action"}
ENGINEERING_STAGES = {
    "read",
    "plan",
    "edit",
    "test",
    "review",
    "repair",
    "refactor",
    "release",
    "skill_authoring",
    "hook_runtime",
    "permission",
    "subagent",
    "requirement-intake",
    "architecture-design",
    "implementation-planning",
    "coding",
    "debugging-diagnosis",
    "bug-fix",
    "code-review",
    "release-delivery",
    "documentation-handoff",
    "skill-authoring",
}
STAGE_REQUIRED_STATE = {
    "plan": ("active_skill_context",),
    "edit": ("changed_paths",),
    "implementation-planning": ("active_skill_context",),
    "coding": ("changed_paths",),
    "refactor": ("changed_paths",),
    "refactoring": ("changed_paths",),
    "skill_authoring": ("changed_paths",),
    "skill-authoring": ("changed_paths",),
    "hook_runtime": ("changed_paths",),
    "repair": ("review_evidence_seen", "review_findings"),
    "bug-fix": ("review_evidence_seen", "review_findings"),
    "test": ("validation_command_seen",),
    "testing": ("validation_command_seen",),
    "permission": ("permission_gate_seen", "permission_decisions"),
    "release": ("risk_surfaces", "suggested_gates"),
    "release-delivery": ("risk_surfaces", "suggested_gates"),
    "subagent": ("subagent_contracts",),
    "compaction": ("compaction_snapshots",),
}
READ_INSPECTION_KEYWORDS = [
    "inspected",
    "read",
    "searched",
    "reviewed",
    "looked at",
    "检查",
    "读取",
    "搜索",
]
READ_CONCLUSION_KEYWORDS = [
    "conclusion",
    "unknown",
    "found",
    "not found",
    "remaining",
    "limit",
    "结论",
    "未知",
    "发现",
    "未确认",
    "限制",
]
REVIEW_FINDING_KEYWORDS = [
    "finding",
    "severity",
    "no issues",
    "no findings",
    "p0",
    "p1",
    "p2",
    "风险",
    "发现",
    "问题",
    "严重",
    "无问题",
    "无发现",
]
READ_REVIEW_RISK_KEYWORDS = CLOSURE_KEYWORDS["risk"] + [
    "unknown",
    "unknowns",
    "limit",
    "limits",
    "limitation",
    "limitations",
    "not verified",
    "not checked",
    "未知",
    "限制",
    "未确认",
]
STAGE_HANDOFF_KEYWORDS = {
    "plan": ["plan", "scope", "validation", "risk", "计划", "范围"],
    "edit": ["changed", "validation", "risk", "修改", "验证", "风险"],
    "implementation-planning": ["plan", "scope", "validation", "risk", "计划", "范围"],
    "coding": ["changed", "validation", "risk", "修改", "验证", "风险"],
    "review": ["finding", "severity", "no issues", "review", "risk"],
    "code-review": ["finding", "severity", "no issues", "review", "risk"],
    "repair": ["fixed", "repaired", "re-review", "validated", "residual"],
    "debugging-diagnosis": ["cause", "diagnosis", "reproduction", "validated", "risk"],
    "bug-fix": ["fixed", "repaired", "re-review", "validated", "residual"],
    "refactor": ["refactor", "behavior", "validation", "risk", "重构"],
    "refactoring": ["refactor", "behavior", "validation", "risk", "重构"],
    "skill_authoring": ["skill", "capability", "registry", "validation", "技能"],
    "skill-authoring": ["skill", "capability", "registry", "validation", "技能"],
    "hook_runtime": ["hook", "runtime", "validation", "risk", "钩子"],
    "test": ["command", "exit", "passed", "failed", "not run", "validation"],
    "testing": ["command", "exit", "passed", "failed", "not run", "validation"],
    "permission": ["permission", "security", "approval", "rollback", "risk"],
    "release": ["rollback", "deploy", "release", "validation", "risk"],
    "release-delivery": ["rollback", "deploy", "release", "validation", "risk"],
    "documentation-handoff": ["documentation", "docs", "handoff", "validation", "risk"],
    "subagent": ["subagent", "owner", "reviewer", "handoff"],
    "compaction": ["compaction", "context", "resume", "stage"],
}


def main() -> int:
    return run_gate_with_policy(
        "stop_closure",
        _main,
        fail_closed=_fail_closed,
        fail_open=_fail_open,
    )


def _failure_runtime() -> str:
    return _GATE_RUNTIME or detect_runtime({})


def _fail_closed(exc: Exception) -> None:
    emit_stop_reminder(
        _failure_runtime(),
        f"ChangeForge Stop Closure gate failed closed: {exc}",
        continue_turn=True,
    )


def _fail_open(exc: Exception) -> None:
    emit_stop_reminder(
        _failure_runtime(),
        f"ChangeForge Hook Runtime warning: closure gate failed open: {exc}",
        continue_turn=False,
    )


def _main() -> int:
    global _GATE_RUNTIME
    event = read_event()
    if not event:
        return 0
    runtime = detect_runtime(event)
    _GATE_RUNTIME = runtime
    if runtime == "unknown":
        return 0
    mode = gate_mode_for_stage("stop_closure", "stop")
    if mode == "off":
        return 0
    if not is_stop(event):
        return 0

    repo = repo_root(cwd_from_event(event))
    state = load_state(repo)
    debug_log(
        repo,
        f"stop gate runtime={runtime} event={event_name(event)} has_surface={_has_closure_surface(state)} validation_command_seen={state.get('validation_command_seen')}",
    )
    if not _has_closure_surface(state):
        return 0
    final_text = _final_text(event)
    manifest = extract_manifest_fields(final_text)
    validation_assessment = _validation_broker_assessment(final_text, state, mode, manifest, runtime)
    validation_result = _validation_result(validation_assessment)
    validation_broker_result = _validation_broker_result(validation_assessment)
    memory_advice = memory_closure_advice(repo, state)
    signals = _closure_signals(final_text, state, manifest, validation_assessment)
    contract = _closure_contract(
        final_text,
        state,
        manifest,
        runtime,
        mode,
        signals,
        validation_assessment=validation_assessment,
    )
    missing = _missing_keyword_groups(
        final_text,
        state,
        manifest,
        contract,
        validation_assessment,
    )
    contract = _contract_with_unenforceable_stop_status(contract, mode, missing)
    liveness = _stop_liveness_state(state, missing, contract, validation_broker_result)
    if liveness["force_advisory"]:
        contract = _degraded_liveness_contract(contract)
    if (
        _compact_handoff_present(final_text)
        and not _compact_handoff_validation_failed(final_text)
        and not _validation_failed(validation_broker_result)
    ):
        clear_state(repo, runtime, preserve_liveness=True)
        return 0
    snapshot = snapshot_from_event_state(
        event,
        state,
        classification={"stage": "stop"},
        read_evidence={
            "paths": state.get("read_paths", []),
            "patterns": state.get("searched_patterns", []),
        },
        gate_name="stop_closure",
        gate_mode=mode,
        closure_contract=contract,
    )
    snapshot_update = state_update_from_snapshot(snapshot)
    write_telemetry_event(
        repo,
        runtime=runtime,
        hook_name="stop_closure_gate",
        event_name=event_name(event),
        mode=mode,
        session_id=session_id_from_event(event),
        cwd=cwd_from_event(event),
        normalized_events=snapshot_update["normalized_events"],
        changed_paths=state.get("changed_paths", []),
        deleted_paths=state.get("deleted_paths", []),
        generated_paths=state.get("generated_paths", []),
        external_file_changes=state.get("external_file_changes", []),
        config_changes=state.get("config_changes", []),
        hook_findings=_stop_findings(state),
        suggested_skills=state.get("suggested_skills", []),
        suggested_capabilities=state.get("suggested_capabilities", []),
        suggested_gates=state.get("suggested_gates", []),
        suggested_domain_extensions=state.get("suggested_domain_extensions", []),
        risk_surfaces=state.get("risk_surfaces", []),
        changed_path_risk_surfaces=state.get("changed_path_risk_surfaces", []),
        command_risk_surfaces=state.get("command_risk_surfaces", []),
        closure_risk_surfaces=state.get("closure_risk_surfaces", [])
        or state.get("risk_surfaces", []),
        branch_route_repair_summaries=state.get("branch_route_repair_summaries", []),
        route_repair_forbidden_retries=state.get("route_repair_forbidden_retries", []),
        route_manifest_detected=signals["route_manifest"],
        required_references_detected=signals["references"],
        validation_command_detected=bool(
            state.get("validation_command_seen") or state.get("validation_seen")
        ),
        validation_results=state.get("validation_results", []),
        validation_evidence_detected=signals["validation"],
        validation_result_outcome=str(validation_result.get("outcome", "")),
        validation_result_evidence_strength=str(
            validation_result.get("evidence_strength", "")
        ),
        validation_result_negative_reason=str(
            validation_result.get("negative_evidence_reason", "")
        ),
        validation_result_command_kind=str(validation_result.get("command_kind", "")),
        validation_result_fresh_after_last_edit=_telemetry_truth(
            validation_result.get("fresh_after_last_edit")
        ),
        validation_result_coverage_aligned=_telemetry_truth(
            validation_result.get("coverage_aligned")
        ),
        validation_result_covered_paths=validation_result.get("covered_paths", []),
        validation_result_covered_risk_surfaces=validation_result.get(
            "covered_risk_surfaces", []
        ),
        validation_broker_closure_outcome=str(
            validation_broker_result.get("closure_outcome", "")
        ),
        validation_broker_selected_scope=str(
            validation_broker_result.get("selected_scope", "")
        ),
        validation_broker_negative_evidence=validation_broker_result.get(
            "negative_evidence", []
        ),
        validation_broker_residual_risk=validation_broker_result.get("residual_risk", []),
        validation_broker_command_ledger=validation_broker_result.get(
            "command_ledger", []
        ),
        adapter_name=contract.adapter,
        adapter_supported_checks=contract.supported_checks,
        adapter_unsupported_checks=contract.unsupported_checks,
        adapter_degraded_capabilities=contract.degraded_capabilities,
        closure_contract_verdict=contract.verdict,
        closure_contract_residual_risk=contract.residual_risk,
        changeforge_closure=contract.changeforge_closure,
        project_memory_available=bool(memory_advice.get("available", True)),
        project_memory_projection_key=str(memory_advice.get("projection_key", "")),
        project_memory_included_events=memory_advice.get("included_events", []),
        project_memory_excluded_events=memory_advice.get("excluded_events", []),
        project_memory_stale_context_gate=str(memory_advice.get("stale_context_gate", "")),
        project_memory_residual_risk=memory_advice.get("residual_risk", []),
        residual_risk_detected=signals["risk"],
        completion_language_detected=signals["completion_language"],
        stage_manifest_detected=bool(manifest.get("stage_present")),
        manifest_current_stage=manifest.get("current_stage", ""),
        manifest_selected_skills=manifest.get("selected_skills", []),
        manifest_selected_capabilities=manifest.get("selected_capabilities", []),
        manifest_selected_domain_extensions=manifest.get("selected_domain_extensions", []),
        manifest_required_references=manifest.get("required_references", []),
        manifest_required_quality_gates=manifest.get("required_quality_gates", []),
        manifest_skipped_quality_gates=manifest.get("skipped_quality_gates", []),
        turn_stage=state.get("turn_stage", ""),
        owner_skill=state.get("owner_skill", ""),
        reviewer_skill=state.get("reviewer_skill", ""),
        read_evidence_seen=bool(state.get("read_evidence_seen")),
        review_evidence_seen=bool(state.get("review_evidence_seen")),
        repair_evidence_seen=bool(state.get("repair_evidence_seen")),
        permission_gate_seen=bool(state.get("permission_gate_seen")),
        professional_contract_seen=bool(state.get("professional_contract_seen")),
        repository_context_seen=signals["repository_context"],
        workflow_state_seen=signals["workflow_state"],
        tool_permission_sandbox_seen=signals["tool_permission_sandbox"],
        skill_efficacy_benchmark_seen=signals["skill_efficacy"],
        plan_execution_consistency_seen=signals["plan_execution_consistency"],
        validation_freshness_seen=signals["validation_freshness"],
        senior_programming_judgment_required=_senior_programming_judgment_required(state),
        senior_programming_judgment_seen=bool(
            state.get("senior_programming_judgment_seen")
            or extract_senior_programming_judgment_fields(final_text).get("present")
        ),
        senior_programming_judgment_complete=signals["senior_programming_judgment"],
        senior_programming_judgment_blocked=bool(
            _senior_programming_judgment_required(state)
            and not signals["senior_programming_judgment"]
        ),
        implementation_preflight_required=bool(
            state.get("implementation_preflight_required")
        ),
        implementation_preflight_seen=bool(state.get("implementation_preflight_seen")),
        implementation_preflight_complete=bool(
            state.get("implementation_preflight_complete")
        ),
        implementation_preflight_blocked=bool(
            state.get("implementation_preflight_blocked")
        ),
        edit_without_preflight_seen=bool(state.get("edit_without_preflight_seen")),
        post_edit_confirmed_preflight_gap=bool(
            state.get("post_edit_confirmed_preflight_gap")
        ),
    )
    if mode == "monitor":
        clear_state(repo, runtime)
        return 0
    if _closure_profile(state) == "read_review" and not missing:
        clear_state(repo, runtime)
        return 0
    if liveness["compact"]:
        message = _compact_closure_message(contract, validation_broker_result, liveness)
    else:
        message = _closure_message(
            state,
            final_text,
            manifest,
            contract,
            validation_assessment,
            memory_advice,
        )
    merge_state(
        repo,
        runtime,
        stop_closure_attempts=int(liveness["attempts"]),
        same_stop_missing_count=int(liveness["same_count"]),
        last_stop_missing_hash=str(liveness["missing_hash"]),
        stop_closure_advisory_emitted=bool(liveness["advisory_emitted"]),
    )
    will_block = (
        _should_block_stop(mode, contract, missing)
        and bool(liveness["hard_blocker"])
        and not liveness["force_advisory"]
    )
    clear_state(
        repo,
        runtime,
        preserve_liveness=True,
        preserve_closure_surface=will_block,
    )
    emit_stop_reminder(
        runtime,
        message,
        continue_turn=will_block,
    )
    return 0




def _should_block_stop(mode: str, contract: ClosureContract, missing: list[str]) -> bool:
    if mode != "block":
        return False
    if not contract.adapter_supports_blocking:
        return False
    if missing:
        return True
    if contract.missing_items:
        return True
    return contract.verdict in {"blocked", "needs_validation", "needs_review", "needs_repair"}


def _stop_liveness_state(
    state: dict,
    missing: list[str],
    contract: ClosureContract,
    validation_broker_result: dict,
) -> dict[str, object]:
    missing_payload = {
        "missing_keyword_groups": sorted(_unique_strings(list(missing))),
        "closure_contract": {
            "verdict": contract.verdict,
            "status": contract.closure_status,
            "missing_items": sorted(_unique_strings(list(contract.missing_items))),
            "closure_status": contract.changeforge_closure.get("status", ""),
            "closure_verdict": contract.changeforge_closure.get("verdict", ""),
        },
        "validation_broker": {
            "closure_outcome": validation_broker_result.get("closure_outcome", ""),
            "selected_scope": validation_broker_result.get("selected_scope", ""),
            "negative_evidence": sorted(
                _unique_strings(list(validation_broker_result.get("negative_evidence") or []))
            ),
        },
        "material_choice": {
            "choice_ids": sorted(_unique_strings(list(state.get("choice_ids") or []))),
            "surfaces": sorted(
                _unique_strings(list(state.get("material_choice_surfaces") or []))
            ),
            "bounded_paths": sorted(_unique_strings(list(state.get("bounded_paths") or []))),
            "last_user_choice_hash": str(state.get("last_user_choice_hash") or ""),
            "choice_status": sorted(_unique_strings(list(state.get("choice_status") or []))),
        },
        "process_phase": {
            "blocked": bool(state.get("process_phase_blocked")),
            "reason": str(state.get("process_phase_blocked_reason") or ""),
            "findings": sorted(_unique_strings(list(state.get("phase_review_findings") or []))),
        },
    }
    missing_hash = hashlib.sha256(
        json.dumps(missing_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    attempts = int(state.get("stop_closure_attempts") or 0) + 1
    same_count = (
        int(state.get("same_stop_missing_count") or 0) + 1
        if str(state.get("last_stop_missing_hash") or "") == missing_hash
        else 1
    )
    validation_failed = _validation_failed(validation_broker_result)
    hard_blocker = _stop_liveness_hard_blocker(state, contract, validation_broker_result)
    force_advisory = same_count >= 2 and not hard_blocker
    return {
        "attempts": attempts,
        "same_count": same_count,
        "missing_hash": missing_hash,
        "force_advisory": force_advisory,
        "compact": same_count >= 2 or bool(state.get("stop_closure_advisory_emitted")),
        "advisory_emitted": force_advisory or bool(state.get("stop_closure_advisory_emitted")),
        "validation_failed": validation_failed,
        "hard_blocker": hard_blocker,
    }


# Hard blockers stay enforceable even when repeated Stop closure gaps are degraded for IDE liveness.
def _stop_liveness_hard_blocker(
    state: dict,
    contract: ClosureContract,
    validation_broker_result: dict,
) -> bool:
    if _validation_failed(validation_broker_result):
        return True
    text = " ".join(
        _unique_strings(
            [
                *list(state.get("permission_decisions") or []),
                *list(state.get("command_risks") or []),
                *list(state.get("command_risk_surfaces") or []),
                *list(state.get("closure_risk_surfaces") or []),
                *list(state.get("risk_surfaces") or []),
                *list(state.get("review_findings") or []),
                *list(state.get("phase_review_findings") or []),
                *list(contract.missing_items),
                *list(contract.residual_risk),
                json.dumps(contract.changeforge_closure, sort_keys=True),
            ]
        )
    ).casefold()
    if "denied" in text and any(term in text for term in ("destructive", "dangerous", "permission")):
        return True
    if any(term in text for term in ("destructive", "migration")) and "failed" in text and "rollback" not in text:
        return True
    if any(term in text for term in ("security", "privacy")) and any(
        term in text for term in ("blocker", "blocked", "failed", "deny", "denied")
    ):
        return True
    return False


def _validation_failed(validation_broker_result: dict) -> bool:
    negative = [str(item) for item in validation_broker_result.get("negative_evidence") or []]
    if any("validation_failed" in item or "command_failed" in item for item in negative):
        return True
    for item in validation_broker_result.get("command_ledger") or []:
        if isinstance(item, dict) and str(item.get("outcome") or "").casefold() in {"fail", "failed", "failure"}:
            return True
    return str(validation_broker_result.get("closure_outcome") or "") == "blocked"


def _degraded_liveness_contract(contract: ClosureContract) -> ClosureContract:
    residual = _unique_strings(
        [
            *contract.residual_risk,
            "repeated Stop closure gaps converted to degraded_ready for IDE liveness; next owner must review residual evidence gaps",
        ]
    )
    closure_payload = dict(contract.changeforge_closure)
    closure_payload["status"] = "degraded_ready"
    closure_payload["verdict"] = "degraded_ready"
    closure_payload["residual_risk"] = residual
    closure_payload["next_owner"] = closure_payload.get("next_owner") or "user"
    return replace(
        contract,
        verdict="degraded_ready",
        closure_status="warn",
        residual_risk=residual,
        missing_items=[],
        changeforge_closure=closure_payload,
    )


def _engineering_quality_report_text(
    contract: ClosureContract | None,
    missing: list[str],
    validation_broker_result: dict | None = None,
) -> str:
    broker = validation_broker_result if isinstance(validation_broker_result, dict) else {}
    residual: list[str] = []
    residual.extend(str(item) for item in missing if item)
    if contract is not None:
        residual.extend(str(item) for item in contract.missing_items if item)
        residual.extend(str(item) for item in contract.residual_risk if item)
    residual.extend(str(item) for item in broker.get("negative_evidence") or [] if item)
    residual = _unique_strings(_ai_visible_evidence_item(item) for item in residual)
    hard_fail = _validation_failed(broker)
    if hard_fail:
        status = "fail"
    elif residual:
        status = "degraded_ready"
    else:
        status = "pass"
    validation = str(broker.get("closure_outcome") or "not_verified")
    if validation == "not_verified":
        if broker.get("selected_scope"):
            validation = "available"
    review = "degraded" if residual else "available"
    lines = ["engineering_quality_report:"]
    lines.append(f"  status: {status}")
    lines.append(f"  validation_freshness: {validation}")
    lines.append(f"  review_authenticity: {review}")
    lines.append("  residual_risk:")
    if residual:
        for item in residual[:8]:
            lines.append(f"    - {item}")
    else:
        lines.append("    - none_detected")
    lines.append("  recommended_human_action:")
    lines.append("    - review the handoff evidence and current diff")
    lines.append("    - rerun or spot-check validation when freshness is uncertain")
    lines.append("    - verify external systems separately when relevant")
    return "\n".join(lines)


AI_VISIBLE_EVIDENCE_ITEM_LABELS = {
    "route_manifest": "route context",
    "stage_route": "stage context",
    "required_references": "source and test context",
    "required_quality_gates": "validation focus",
    "selected_capabilities": "engineering focus areas",
    "selected_skills": "professional concerns",
}


def _ai_visible_evidence_item(item: object) -> str:
    text = str(item)
    return AI_VISIBLE_EVIDENCE_ITEM_LABELS.get(text, text)


def _ai_visible_evidence_items(items: list[str] | tuple[str, ...] | set[str]) -> list[str]:
    return [_ai_visible_evidence_item(item) for item in items]


def _closure_review_actions_text(contract: ClosureContract | None) -> str:
    return ""


def _render_action_yaml(name: str, action: dict) -> list[str]:
    lines = [f"{name}:"]
    _append_yaml_mapping(lines, action, 2)
    return lines


def _append_yaml_mapping(lines: list[str], mapping: dict, indent: int) -> None:
    prefix = " " * indent
    for key, value in mapping.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            _append_yaml_mapping(lines, value, indent + 2)
        elif isinstance(value, list):
            lines.append(f"{prefix}{key}:")
            for item in value:
                if isinstance(item, dict):
                    lines.append(f"{prefix}  -")
                    _append_yaml_mapping(lines, item, indent + 4)
                else:
                    lines.append(f"{prefix}  - {_yaml_scalar(item)}")
        else:
            lines.append(f"{prefix}{key}: {_yaml_scalar(value)}")


def _yaml_scalar(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return str(value)


def _compact_closure_message(
    contract: ClosureContract,
    validation_broker_result: dict,
    liveness: dict[str, object],
) -> str:
    lines = [_engineering_quality_report_text(contract, [], validation_broker_result)]
    lines.append("compact_advisory:")
    lines.append(f"  repeated_missing_count: {liveness.get('same_count')}")
    if liveness.get("force_advisory"):
        lines.append("  liveness: repeated identical gaps were downgraded")
    if validation_broker_result.get("closure_outcome"):
        outcome = validation_broker_result.get("closure_outcome")
        lines.append(f"  validation_note: {outcome}")
    lines.append("  next_owner: user_or_reviewer")
    return "\n".join(lines)


def _contract_with_unenforceable_stop_status(
    contract: ClosureContract,
    mode: str,
    missing: list[str],
) -> ClosureContract:
    if mode != "block" or contract.adapter_supports_blocking:
        return contract
    if not (missing or contract.missing_items or contract.verdict in {"blocked", "needs_validation", "needs_review", "needs_repair"}):
        return contract
    residual = _unique_strings(
        [
            *contract.residual_risk,
            "blocked_but_unenforceable: adapter does not support hard Stop decisions",
        ]
    )
    closure_payload = dict(contract.changeforge_closure)
    closure_payload["verdict"] = "blocked_but_unenforceable"
    closure_payload["residual_risk"] = residual
    closure_payload["missing_evidence"] = _unique_strings(
        [
            *[str(item) for item in closure_payload.get("missing_evidence", []) if str(item).strip()],
            *contract.missing_items,
            *missing,
        ]
    )
    return replace(
        contract,
        verdict="blocked_but_unenforceable",
        residual_risk=residual,
        closure_status="warn",
        changeforge_closure=closure_payload,
    )


def _unique_strings(values: list[object]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _has_closure_surface(state: dict) -> bool:
    stage = str(state.get("turn_stage") or "").strip()
    explicit_engineering_stage = stage in ENGINEERING_STAGES
    return bool(
        state.get("changed_paths")
        or state.get("deleted_paths")
        or state.get("generated_paths")
        or state.get("validation_results")
        or state.get("validation_command_ledger")
        or _has_non_safe_command_risk(state)
        or state.get("closure_risk_surfaces")
        or state.get("risk_surfaces")
        or state.get("structure_findings")
        or state.get("file_naming_findings")
        or state.get("reuse_findings")
        or state.get("extension_reuse_findings")
        or state.get("advanced_refactor_findings")
        or state.get("comment_findings")
        or state.get("structure_quality_findings")
        or state.get("implementation_preflight_required")
        or state.get("implementation_preflight_seen")
        or state.get("implementation_preflight_complete")
        or state.get("senior_programming_judgment_required")
        or state.get("senior_programming_judgment_seen")
        or state.get("senior_programming_judgment_complete")
        or state.get("pre_edit_structure_findings")
        or state.get("edit_without_preflight_seen")
        or state.get("post_edit_confirmed_preflight_gap")
        or state.get("read_evidence_seen")
        or state.get("review_evidence_seen")
        or state.get("reviewed_diff_evidence_seen")
        or state.get("process_phase_ledgers")
        or state.get("phase_review_results")
        or state.get("review_capsules")
        or state.get("implementation_review_results")
        or state.get("implementation_review_required")
        or state.get("implementation_review_seen")
        or _has_unresolved_material_choice_review_finding(state)
        or state.get("repair_evidence_seen")
        or state.get("permission_gate_seen")
        or explicit_engineering_stage
        or state.get("subagent_contracts")
        or state.get("compaction_snapshots")
        or state.get("branch_route_repair_summaries")
        or state.get("route_repair_forbidden_retries")
    )


def _has_non_safe_command_risk(state: dict) -> bool:
    for value in state.get("command_risks", []):
        risk = str(value).split(":", 1)[0].strip()
        if risk and risk != "safe":
            return True
    return False


def _closure_profile(state: dict) -> str:
    stage = str(state.get("turn_stage") or "").strip()
    if stage in {"question", "unknown", "no_engineering_action"}:
        return "silent"
    if stage in {"read", "review", "requirement-intake", "code-review"} and not state.get("changed_paths"):
        return "read_review"
    return "engineering"


def _closure_signals(
    final_text: str,
    state: dict,
    manifest: dict,
    validation_assessment: dict | None = None,
) -> dict[str, bool]:
    """Completeness flags for telemetry. This is presence detection only.

    The Stop gate does not judge semantic correctness; it records whether the
    final handoff text contains each kind of closure evidence so offline review
    can spot missing route context, validation, references, or residual risk.
    The parsed compatibility record sharpens route and reference detection
    beyond a bare keyword scan.
    """
    lowered = final_text.casefold()
    compact_handoff = _compact_handoff_present(final_text)
    repository_context = extract_repository_context_fields(final_text)
    senior_judgment = extract_senior_programming_judgment_fields(final_text)
    diagnosis_closure = extract_diagnosis_closure_fields(final_text)

    def has(group: str) -> bool:
        return any(keyword.casefold() in lowered for keyword in CLOSURE_KEYWORDS[group])

    return {
        "route_manifest": bool(manifest.get("route_present")) or compact_handoff,
        "validation": _has_validation_evidence(final_text, state, validation_assessment) or compact_handoff,
        "risk": has("risk") or compact_handoff,
        "references": bool(manifest.get("required_references")) or "reference" in lowered,
        "skills": has("skills") or compact_handoff,
        "repository_context": bool(repository_context.get("complete")) or compact_handoff,
        "workflow_state": _has_workflow_keyword(lowered, "workflow_state")
        or bool(state.get("workflow_state_seen")),
        "tool_permission_sandbox": _has_workflow_keyword(
            lowered, "tool_permission_sandbox"
        )
        or bool(state.get("tool_permission_sandbox_seen")),
        "skill_efficacy": _has_workflow_keyword(lowered, "skill_efficacy")
        or bool(state.get("skill_efficacy_benchmark_seen")),
        "plan_execution_consistency": _has_workflow_keyword(
            lowered, "plan_execution_consistency"
        )
        or bool(state.get("plan_execution_consistency_seen")),
        "validation_freshness": _has_workflow_keyword(lowered, "validation_freshness")
        or bool(state.get("validation_freshness_seen")),
        "senior_programming_judgment": bool(senior_judgment.get("complete"))
        or bool(state.get("senior_programming_judgment_complete"))
        or (
            senior_judgment.get("allowed_skip")
            and _has_workflow_keyword(lowered, "senior_programming_judgment")
        ),
        "diagnosis_closure": bool(diagnosis_closure.get("complete")),
        "completion_language": any(
            phrase.casefold() in lowered for phrase in COMPLETION_LANGUAGE
        ),
    }


def _stop_findings(state: dict) -> dict[str, list[str]]:
    return {
        key: list(state.get(key, []))
        for key in (
            "structure_findings",
            "file_naming_findings",
            "reuse_findings",
            "extension_reuse_findings",
            "advanced_refactor_findings",
            "comment_findings",
            "structure_quality_findings",
            "post_edit_structure_findings",
            "read_paths",
            "searched_patterns",
            "review_targets",
            "review_findings",
            "repair_findings",
            "repair_events",
            "rereview_events",
            "choice_ids",
            "choice_triggers",
            "choice_status",
            "material_choice_surfaces",
            "blocked_tool_category",
            "bounded_paths",
            "validation_results",
            "changed_path_risk_surfaces",
            "command_risk_surfaces",
            "command_risks",
            "closure_risk_surfaces",
            "professional_injections",
            "permission_decisions",
            "rollback_points",
            "reference_loads",
            "subagent_contracts",
            "compaction_snapshots",
            "branch_route_repair_summaries",
            "route_repair_forbidden_retries",
            "implementation_preflights",
            "senior_programming_judgments",
            "pre_edit_structure_findings",
        )
    }


def _closure_message(
    state: dict,
    final_text: str,
    manifest: dict | None = None,
    contract: ClosureContract | None = None,
    validation_assessment: dict | None = None,
    memory_advice: dict | None = None,
) -> str:
    profile = _closure_profile(state)
    missing = _missing_keyword_groups(
        final_text,
        state,
        manifest,
        contract,
        validation_assessment,
    )
    route_present = bool(manifest and manifest.get("route_present"))
    details: list[str] = []
    if state.get("structure_findings"):
        details.append("- structure gate fired")
    if state.get("file_naming_findings"):
        details.append("- file naming gate fired")
    if state.get("reuse_findings"):
        details.append("- reuse gate fired")
    if state.get("extension_reuse_findings"):
        details.append("- extension reuse gate fired")
    if state.get("advanced_refactor_findings"):
        details.append("- advanced refactor gate fired")
    if state.get("comment_findings"):
        details.append("- comment quality gate fired")
    if state.get("structure_quality_findings"):
        details.append("- structure quality gate fired")
    if state.get("implementation_preflight_required"):
        details.append("- implementation preflight required")
    if state.get("implementation_preflights"):
        details.append(
            f"- implementation preflights: {', '.join(state['implementation_preflights'][:4])}"
        )
    if state.get("senior_programming_judgments"):
        details.append(
            f"- senior programming judgments: {', '.join(state['senior_programming_judgments'][:4])}"
        )
    if state.get("edit_without_preflight_seen"):
        details.append("- edit occurred without complete implementation preflight")
    if state.get("risk_surfaces"):
        details.append(f"- risk surfaces: {', '.join(state['risk_surfaces'])}")
    if state.get("turn_stage"):
        details.append(f"- active stage: {state['turn_stage']}")
    if state.get("owner_skill") or state.get("reviewer_skill"):
        details.append(
            f"- owner/reviewer: {state.get('owner_skill', 'unknown')} / {state.get('reviewer_skill', 'unknown')}"
        )
    if state.get("read_paths"):
        details.append(f"- read paths: {', '.join(state['read_paths'][:8])}")
    if state.get("review_targets"):
        details.append(f"- review targets: {', '.join(state['review_targets'][:8])}")
    if state.get("review_findings"):
        details.append(f"- review findings: {', '.join(state['review_findings'][:8])}")
    if state.get("material_choice_surfaces"):
        details.append(
            f"- material choice surfaces: {', '.join(state['material_choice_surfaces'][:8])}"
        )
    if state.get("permission_decisions"):
        details.append(f"- permission decisions: {', '.join(state['permission_decisions'][:8])}")
    for label, state_key in (
        ("repository context", "repository_context_seen"),
        ("workflow state", "workflow_state_seen"),
        ("tool permission/sandbox", "tool_permission_sandbox_seen"),
        ("skill efficacy benchmark", "skill_efficacy_benchmark_seen"),
        ("plan-execution consistency", "plan_execution_consistency_seen"),
        ("validation freshness", "validation_freshness_seen"),
        ("senior programming judgment", "senior_programming_judgment_complete"),
    ):
        if state.get(state_key):
            details.append(f"- {label} signal was observed")
    if state.get("changed_paths"):
        details.append(f"- changed paths: {', '.join(state['changed_paths'])}")
    if state.get("deleted_paths"):
        details.append(f"- deleted paths: {', '.join(state['deleted_paths'][:8])}")
    if state.get("generated_paths"):
        details.append(f"- generated paths: {', '.join(state['generated_paths'][:8])}")
    if state.get("validation_results"):
        details.append(f"- validation results: {', '.join(state['validation_results'][:8])}")
    if state.get("command_risks"):
        details.append(f"- command risks: {', '.join(state['command_risks'][:8])}")
    if state.get("validation_command_seen") or state.get("validation_seen"):
        details.append("- validation command was observed")
    broker_assessment = (
        validation_assessment
        if isinstance(validation_assessment, dict)
        else _validation_broker_assessment(final_text, state, "warn")
    )
    broker_issues = broker_assessment.get("issues", []) if broker_assessment else []
    if isinstance(broker_issues, list) and broker_issues:
        details.append(
            f"- validation broker issues: {', '.join(str(issue) for issue in broker_issues[:6])}"
        )
    broker_result = _validation_broker_result(broker_assessment)
    if broker_result.get("closure_outcome"):
        details.append(f"- validation broker closure: {broker_result.get('closure_outcome')}")
    if contract is not None:
        details.append(f"- closure contract verdict: {contract.verdict}")
        if contract.unsupported_checks:
            details.append(
                f"- unsupported runtime checks: {', '.join(contract.unsupported_checks[:8])}"
            )
        if contract.degraded_capabilities:
            details.append(
                f"- degraded runtime capabilities: {', '.join(contract.degraded_capabilities[:8])}"
            )
        if contract.residual_risk:
            details.append(
                f"- closure residual risk: {', '.join(contract.residual_risk[:8])}"
            )
    memory = memory_advice if isinstance(memory_advice, dict) else {}
    memory_residual = memory.get("residual_risk") if isinstance(memory, dict) else []
    if memory.get("status") == "disabled_by_policy":
        details.append("- project memory: disabled_by_policy")
    elif memory.get("available") is False:
        details.append("- project memory unavailable; closure is degraded, not a pass")
    if memory.get("stale_context_gate") in {"warn", "block"}:
        details.append(f"- project memory stale-context gate: {memory.get('stale_context_gate')}")
    if isinstance(memory_residual, list) and memory_residual:
        details.append(
            f"- project memory residual risk: {', '.join(str(item) for item in memory_residual[:6])}"
        )
    if state.get("suggested_domain_extensions"):
        details.append(
            f"- suggested domain extensions: {', '.join(state['suggested_domain_extensions'])}"
        )
    if missing:
        details.append(
            f"- missing closure signals: {', '.join(_ai_visible_evidence_items(missing))}"
        )
    superpowers_advisory = _superpowers_advisory_text(state, final_text)
    detail_text = "\n".join(details)
    if detail_text:
        detail_text = f"\nObserved this turn:\n{detail_text}\n"
    evidence_text = _structure_evidence_block(state)
    review_actions_text = ""
    headline = _engineering_quality_report_text(contract, missing, broker_result)
    if profile == "engineering" and not route_present:
        headline += (
            " MISSING: route context is incomplete."
            " Real changes were observed but the handoff does not clearly summarize"
            " the task type, risk level, professional concerns, source and test"
            " context, validation focus, assumptions, and residual risk."
            " Add a concise route summary for the next reader; strong route evidence"
            " comes from runtime-observed context, selected skill injection,"
            " validation records, or replay/evaluation artifacts."
        )
    if _unverified_completion(final_text, state):
        headline += (
            " MISSING: this handoff uses completion language but shows no validation"
            " evidence. State the fresh command and outcome that back the claim, or"
            " replace the claim with a not-verified disclosure (status, why not run,"
            " residual risk, exact command)."
        )
    if _implementation_preflight_required(state) and not _has_implementation_preflight_evidence(
        final_text, state
    ):
        headline += (
            " MISSING: implementation preflight evidence is incomplete."
            " Before final handoff, include the changeforge_implementation_preflight"
            " summary with read evidence, placement decision, reuse decision,"
            " object/module boundary rationale when relevant, test plan, residual"
            " risk, and rollback/revert path."
        )
    if _senior_programming_judgment_required(state) and not _has_senior_programming_judgment_evidence(
        final_text, state
    ):
        headline += (
            " MISSING: senior programming judgment evidence is incomplete."
            " Before final handoff, include the senior_programming_judgment"
            " summary with purpose, facts, objects, states, behaviors, rules,"
            " invariants, boundaries, failure contract, side effects, reuse and"
            " placement, minimality decision, validation map, observability map,"
            " and residual risk, or an allowed skip_reason: trivial-local-edit,"
            " no-semantic-impact, no-engineering-action, formatting-only, or"
            " documentation-only-no-behavior-change."
        )
    if "material_choice_resolution" in missing:
        headline += (
            " MISSING: review found an unresolved material SDD choice."
            " Ask the user to choose the design direction or include structured"
            " changeforge_sdd_choice resolution_evidence before ready handoff."
        )
    stage_missing = _stage_missing_groups(final_text, state)
    if stage_missing:
        headline += (
            " MISSING: stage-aware handoff evidence is incomplete for"
            f" {state.get('turn_stage') or 'current'} stage"
            f" ({', '.join(stage_missing)})."
        )

    if profile == "read_review":
        return f"""{headline}
{detail_text}{review_actions_text}
This turn read code, reviewed artifacts, or triggered risk surfaces. Before final handoff, include:
- read/review evidence: inspected files, searches, or reviewed artifact
- findings, explicit no-findings, or unknowns/limits
- residual risks and unverified items
- next action or explicit no-next-action rationale{evidence_text}{superpowers_advisory}"""

    return f"""{headline}
{detail_text}{review_actions_text}
This turn changed files, read code, reviewed artifacts, or triggered risk surfaces. Before final handoff, include:
- route context: task type, risk level, professional concerns, source and test context, validation focus, assumptions, and residual risk
- stage context for non-trivial engineering work: current stage, launched and explicitly skipped capabilities, skipped rationale, and next-stage handoff
- source and test context: router self-use references, selected capability references, inspected files, and nearby tests
- changed files
- structured repository_context: context_pack or source_of_truth, reuse_candidates or no_reuse_candidate_found, test_candidates or validation_candidates, graph_freshness, and residual_risk
- workflow state summary: current stage, allowed transition, owner/reviewer split, validation freshness, and repair/re-review state
- tool permission/sandbox record when risky tools, connectors, network writes, deploys, migrations, destructive actions, or secret-bearing commands were used
- changeforge_implementation_preflight summary when edits occurred: read evidence, placement decision, reuse ladder, object/module boundary, test plan, risk and rollback/revert path
- senior_programming_judgment summary when non-trivial engineering edits occurred: purpose, facts, objects, states, behaviors, rules, invariants, boundaries, failure contract, side effects, reuse and placement, minimality decision, validation map, observability map, and residual risk
- structure/reuse/placement rationale if structure gate fired
- plan-execution consistency: accepted plan vs actual changed files, validation commands, skipped work, stale evidence, and residual risk
- skill-efficacy benchmark evidence when skill, routing, stage, hook, eval, or benchmark behavior changed
- validation commands and results
- validation freshness after the final material edit
- residual risks and unverified items
- next actions{evidence_text}{superpowers_advisory}"""


def _superpowers_advisory_text(state: dict, final_text: str) -> str:
    try:
        _runtime_root = Path(__file__).resolve().parents[2]
        _runtime_pkg = (_runtime_root / "runtime_governance").resolve()
        cached = sys.modules.get("runtime_governance")
        cached_file = Path(str(getattr(cached, "__file__", ""))).resolve() if cached else None
        if cached_file and _runtime_pkg.is_dir() and not cached_file.is_relative_to(_runtime_pkg):
            for name in list(sys.modules):
                if name == "runtime_governance" or name.startswith("runtime_governance."):
                    del sys.modules[name]
        runtime_root_text = str(_runtime_root)
        if _runtime_pkg.is_dir():
            if runtime_root_text in sys.path:
                sys.path.remove(runtime_root_text)
            sys.path.insert(0, runtime_root_text)
        from runtime_governance import observation_from_mapping, reduce_execution_evidence
        from runtime_governance.visible_plan_parser import planned_files_from_visible_plan
    except Exception:
        return ""
    validation_commands = list(state.get("validation_results") or [])
    if not validation_commands and state.get("validation_command_seen"):
        validation_commands = ["observed validation command"]
    validation_fresh = None
    if state.get("validation_freshness_seen"):
        validation_fresh = True
    elif state.get("validation_command_seen") or state.get("changed_paths"):
        validation_fresh = False
    text = str(final_text or "")
    planned_files = state.get("planned_files") or state.get("planned_paths") or []
    if not planned_files:
        planned_files = list(planned_files_from_visible_plan(text))
    observation = observation_from_mapping(
        {
            "planned_files": planned_files,
            "changed_files": state.get("changed_paths") or [],
            "validation_commands": validation_commands,
            "validation_fresh_after_last_edit": validation_fresh,
            "review_text": text if state.get("review_evidence_seen") or "review" in text.casefold() else "",
            "repair_text": text if state.get("repair_evidence_seen") or "repair" in text.casefold() else "",
            "rereview_text": text if "re-review" in text.casefold() or "rereview" in text.casefold() else "",
            "final_handoff": text,
            "user_gate_text": text,
        }
    )
    report = reduce_execution_evidence(observation)
    if report.passed:
        return ""
    lines = ["\n\nEngineering quality note:"]
    for gap in report.observed_gaps[:4]:
        lines.append(f"- {gap}")
    for action in report.recommended_next_actions[:3]:
        lines.append(f"- Natural next step: {action}")
    return "\n".join(lines)


def _structure_evidence_block(state: dict) -> str:
    blocks: list[str] = []
    if state.get("file_naming_findings"):
        blocks.append(
            "- file naming convention evidence:\n"
            "  - same-directory files inspected\n"
            "  - parent-module naming pattern\n"
            "  - selected filename rationale\n"
            "  - rejected filename alternatives"
        )
    if state.get("reuse_findings"):
        blocks.append(
            "- reuse ladder record:\n"
            "  - direct reuse\n"
            "  - extension reuse\n"
            "  - composition/wrapper\n"
            "  - extraction\n"
            "  - new code justification"
        )
    if state.get("extension_reuse_findings"):
        blocks.append(
            "- extension safety record:\n"
            "  - old behavior preserved\n"
            "  - compatibility risk\n"
            "  - old behavior tests\n"
            "  - new behavior tests"
        )
    if state.get("advanced_refactor_findings"):
        blocks.append(
            "- advanced refactor decision:\n"
            "  - object/function/module choice\n"
            "  - class/interface/inheritance/reflection justification\n"
            "  - state/invariant/lifecycle/collaborator rationale\n"
            "  - public behavior tests"
        )
    if state.get("comment_findings"):
        blocks.append(
            "- comment quality evidence:\n"
            "  - exported/public doc comments added\n"
            "  - class/function/method comments added where required\n"
            "  - non-trivial test comments added\n"
            "  - critical internal logic comments added\n"
            "  - redundant comments avoided or removed"
        )
    if state.get("structure_quality_findings"):
        blocks.append(
            "- code clarity evidence:\n"
            "  - main flow assessment\n"
            "  - nested branch and signature trap review\n"
            "  - side-effect boundary review\n"
            "  - cleanup/deprecation owner and expiry\n"
            "  - change locality or deletion-path review"
        )
    if _implementation_preflight_required(state):
        blocks.append(
            "- implementation preflight evidence:\n"
            "  - changeforge_implementation_preflight summary\n"
            "  - read evidence: target, sibling, caller/callee, tests, config/docs\n"
            "  - placement decision and rejected locations\n"
            "  - reuse ladder decision\n"
            "  - object/module boundary rationale when relevant\n"
            "  - test plan and validation command result\n"
            "  - residual risk and rollback/revert path"
        )
    if not blocks:
        return ""
    return "\n\nProvide stronger structure evidence:\n" + "\n".join(blocks)


def _final_text(event: dict) -> str:
    for key in (
        "final_response",
        "finalResponse",
        "assistant_response",
        "assistantResponse",
        "response",
        "message",
        "output",
        "last_assistant_message",
        "lastAssistantMessage",
    ):
        value = event.get(key)
        if isinstance(value, str):
            return value
    return _final_text_from_transcript(event)


def _final_text_from_transcript(event: dict) -> str:
    path_value = event.get("transcript_path") or event.get("transcriptPath")
    if not isinstance(path_value, str) or not path_value.strip():
        return ""
    try:
        path = Path(path_value).expanduser()
        with path.open("rb") as file:
            try:
                file.seek(0, 2)
                size = file.tell()
                file.seek(max(size - MAX_TRANSCRIPT_BYTES, 0))
            except OSError:
                pass
            transcript = file.read().decode("utf-8", errors="replace")
    except Exception:
        return ""

    assistant_texts: list[str] = []
    for line in transcript.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        candidate = _assistant_text_from_record(record)
        if candidate:
            assistant_texts.append(candidate)
    if assistant_texts:
        return assistant_texts[-1]
    return transcript


def _assistant_text_from_record(record: object) -> str:
    if not isinstance(record, dict):
        return ""
    role = _record_role(record)
    if role and role not in {"assistant", "assistant_message", "assistantmessage"}:
        return ""
    if not role and not _record_has_assistant_message(record):
        return ""

    for key in ("content", "text", "message", "response", "final_response"):
        text = _text_from_value(record.get(key))
        if text:
            return text
    return ""


def _record_role(record: dict) -> str:
    for key in ("role", "type", "speaker"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().casefold()
    author = record.get("author")
    if isinstance(author, dict):
        value = author.get("role") or author.get("name")
        if isinstance(value, str) and value.strip():
            return value.strip().casefold()
    message = record.get("message")
    if isinstance(message, dict):
        return _record_role(message)
    return ""


def _record_has_assistant_message(record: dict) -> bool:
    message = record.get("message")
    return isinstance(message, dict) and _record_role(message) in {
        "assistant",
        "assistant_message",
        "assistantmessage",
    }


def _text_from_value(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = [_text_from_value(item) for item in value]
        return "\n".join(part for part in parts if part)
    if isinstance(value, dict):
        for key in ("text", "content", "value", "message"):
            text = _text_from_value(value.get(key))
            if text:
                return text
    return ""


def _missing_keyword_groups(
    text: str,
    state: dict,
    manifest: dict | None = None,
    contract: ClosureContract | None = None,
    validation_assessment: dict | None = None,
) -> list[str]:
    lowered = text.casefold()
    repository_context = extract_repository_context_fields(text)
    missing: list[str] = []
    profile = _closure_profile(state)
    if profile == "silent":
        return missing
    if profile == "read_review":
        for group in _stage_missing_groups(text, state):
            if group not in missing:
                missing.append(group)
        if _has_unresolved_material_choice_review_finding(state) and not _has_material_choice_resolution(
            text, state
        ):
            missing.append("material_choice_resolution")
        if not _has_any_keyword(lowered, READ_REVIEW_RISK_KEYWORDS):
            missing.append("risk")
        if _unverified_completion(text, state) and "completion_evidence" not in missing:
            missing.append("completion_evidence")
        return missing
    parsed_manifest = manifest if manifest is not None else extract_manifest_fields(text)
    if _compact_handoff_present(text):
        broker_result = _validation_broker_result(validation_assessment)
        broker_outcome = str(broker_result.get("closure_outcome") or "")
        if broker_outcome == "blocked" or _compact_handoff_validation_failed(text):
            return ["validation_broker_blocked"]
        return []
    if not parsed_manifest.get("route_present"):
        missing.append("route_manifest")
    for group, keywords in CLOSURE_KEYWORDS.items():
        if group == "validation":
            if not _has_validation_evidence(text, state):
                missing.append(group)
            continue
        if not any(keyword.casefold() in lowered for keyword in keywords):
            missing.append(group)
    if profile == "engineering":
        workflow_required = ("repository_context", "workflow_state", "plan_execution_consistency", "validation_freshness")
        for group in workflow_required:
            if group == "repository_context":
                if not repository_context.get("complete"):
                    missing.append(group)
                continue
            if not _has_workflow_keyword(lowered, group) and not state.get(_workflow_state_key(group)):
                missing.append(group)
        if _tool_permission_required(state) and not (
            _has_workflow_keyword(lowered, "tool_permission_sandbox")
            or state.get("tool_permission_sandbox_seen")
        ):
            missing.append("tool_permission_sandbox")
        if _skill_efficacy_required(state) and not (
            _has_workflow_keyword(lowered, "skill_efficacy")
            or state.get("skill_efficacy_benchmark_seen")
        ):
            missing.append("skill_efficacy")
    for state_key, group in CONDITIONAL_GROUP_BY_STATE.items():
        if not state.get(state_key):
            continue
        keywords = CONDITIONAL_KEYWORDS[group]
        if not any(keyword.casefold() in lowered for keyword in keywords) and group not in missing:
            missing.append(group)
    if _unverified_completion(text, state) and "completion_evidence" not in missing:
        missing.append("completion_evidence")
    if _has_unresolved_material_choice_review_finding(state) and not _has_material_choice_resolution(
        text, state
    ):
        missing.append("material_choice_resolution")
    if _implementation_preflight_required(state) and not _has_implementation_preflight_evidence(
        text, state
    ):
        missing.append("implementation_preflight")
    if _senior_programming_judgment_required(state) and not _has_senior_programming_judgment_evidence(
        text, state
    ):
        missing.append("senior_programming_judgment")
    for group in _stage_missing_groups(text, state):
        if group not in missing:
            missing.append(group)
    for group in _contract_missing_groups(contract):
        if group not in missing:
            missing.append(group)
    broker_result = _validation_broker_result(validation_assessment)
    broker_outcome = str(broker_result.get("closure_outcome") or "")
    if broker_outcome in {"blocked", "needs_validation"}:
        validation_result = _validation_result(validation_assessment)
        if not _soft_validation_coverage_gap(
            final_text=text,
            state=state,
            validation_result=validation_result,
            broker_result=broker_result,
        ) and not _state_validation_satisfies_broker_gap(text, state, broker_result):
            missing.append(f"validation_broker_{broker_outcome}")
    return missing


def _has_unresolved_material_choice_review_finding(state: dict) -> bool:
    if state.get("choice_resolution_evidence_seen"):
        return False
    findings = state.get("review_findings", [])
    if not isinstance(findings, (list, tuple, set)):
        return False
    return MATERIAL_CHOICE_REVIEW_FINDING in {str(item) for item in findings}


def _has_material_choice_resolution(text: str, state: dict) -> bool:
    if state.get("choice_resolution_evidence_seen"):
        return True
    lowered = text.casefold()
    return (
        "changeforge_sdd_choice" in lowered
        and "resolution_evidence" in lowered
        and (
            "status: resolved" in lowered
            or "user selected" in lowered
            or "user chose" in lowered
            or "用户选择" in lowered
        )
    )


def _closure_contract(
    final_text: str,
    state: dict,
    manifest: dict,
    runtime: str,
    mode: str,
    signals: dict[str, bool] | None = None,
    validation_assessment: dict | None = None,
) -> ClosureContract:
    signals = signals if isinstance(signals, dict) else _closure_signals(final_text, state, manifest)
    broker_result = _validation_broker_result(validation_assessment)
    validation_result = _validation_result(validation_assessment)
    compact_handoff = _compact_handoff_present(final_text)
    review_evidence_present = bool(
        state.get("review_evidence_seen")
        or state.get("review_artifact_seen")
        or state.get("review_targets")
        or state.get("reviewed_diff_evidence_seen")
    )
    # Manifest requirements are active closure inputs even when reducer state
    # did not see them earlier in the turn.
    closure_state = dict(state)
    diagnosis_closure = extract_diagnosis_closure_fields(final_text)
    closure_state.update(
        {
            "diagnosis_closure_present": bool(diagnosis_closure.get("present")),
            "diagnosis_closure_complete": bool(diagnosis_closure.get("complete")),
            "diagnosis_closure_status": str(diagnosis_closure.get("status") or ""),
            "diagnosis_closure_missing": list(diagnosis_closure.get("missing", []) or []),
            "diagnosis_independent_review_status": str(
                diagnosis_closure.get("review_status") or ""
            ),
            "diagnosis_selected_skills_only_review": bool(
                diagnosis_closure.get("selected_skills_only_review")
            ),
        }
    )
    closure_required_checks: list[object] = []
    existing_required = closure_state.get("closure_required_checks")
    if isinstance(existing_required, (list, tuple, set)):
        closure_required_checks.extend(existing_required)
    elif existing_required:
        closure_required_checks.append(existing_required)
    for key in ("required_quality_gates", "required_references", "selected_capabilities"):
        values = manifest.get(key, [])
        if isinstance(values, (list, tuple, set)):
            closure_required_checks.extend(values)
        elif values:
            closure_required_checks.append(values)
    if closure_required_checks:
        closure_state["closure_required_checks"] = closure_required_checks
    contract = ClosureContract.from_state(
        closure_state,
        route_manifest_complete=bool(manifest.get("route_present")) or compact_handoff,
        stage_route_present=bool(manifest.get("stage_present")) or compact_handoff,
        repository_context_present=bool(signals.get("repository_context")),
        implementation_preflight_complete=(
            not _implementation_preflight_required(state)
            or _has_implementation_preflight_evidence(final_text, state)
        ),
        validation_evidence_present=bool(signals.get("validation")),
        review_evidence_present=review_evidence_present,
        residual_risk_present=bool(signals.get("risk")),
        capabilities=adapter_capabilities_for(runtime),
        block_mode=mode == "block",
        validation_broker_outcome=str(broker_result.get("closure_outcome") or ""),
        validation_broker_residual_risk=list(broker_result.get("residual_risk", []) or []),
        validation_result_outcome=str(validation_result.get("outcome", "")),
        validation_result_freshness=(
            "current"
            if state.get("validation_freshness_seen")
            else _validation_freshness_label(validation_result.get("fresh_after_last_edit"))
        ),
        validation_result_scope=str(broker_result.get("selected_scope", "")),
        validation_result_command_kind=str(validation_result.get("command_kind", "")),
    )
    if compact_handoff and not _compact_handoff_validation_failed(final_text) and broker_result.get("closure_outcome") != "blocked":
        closure_payload = dict(contract.changeforge_closure)
        closure_payload["status"] = closure_payload.get("status") or "degraded_ready"
        closure_payload["verdict"] = "degraded_ready"
        closure_payload["next_owner"] = closure_payload.get("next_owner") or "user"
        return replace(
            contract,
            verdict="degraded_ready",
            closure_status="warn",
            missing_items=[],
            changeforge_closure=closure_payload,
        )
    return contract


def _compact_handoff_present(text: str) -> bool:
    lowered = str(text or "").casefold()
    if "changeforge_handoff:" not in lowered:
        return False
    required = ("route_id:", "status:", "validation:", "residual_risk:", "next_owner:")
    return all(item in lowered for item in required)


def _compact_handoff_validation_failed(text: str) -> bool:
    lowered = str(text or "").casefold()
    if "changeforge_handoff:" not in lowered:
        return False
    return bool(re.search(r"\bvalidation:\s*(?:\n\s*)?status:\s*fail\b", lowered))


def _contract_missing_groups(contract: ClosureContract | None) -> list[str]:
    if contract is None:
        return []
    groups: list[str] = []
    for item in contract.missing_items:
        if item == "review_evidence":
            continue
        groups.append(item)
    return groups


def _stage_missing_groups(text: str, state: dict) -> list[str]:
    stage = str(state.get("turn_stage") or "").strip()
    if stage in NO_CLOSURE_STAGES:
        return []
    lowered = text.casefold()
    if stage in {"read", "requirement-intake"}:
        return _read_stage_missing_groups(lowered, state)
    if stage in {"review", "code-review"}:
        return _review_stage_missing_groups(lowered, state)
    missing: list[str] = []
    for state_key in STAGE_REQUIRED_STATE.get(stage, ()):
        if not state.get(state_key):
            missing.append(f"{stage}_state")
            break
    keywords = STAGE_HANDOFF_KEYWORDS.get(stage, ())
    if keywords and not any(keyword.casefold() in lowered for keyword in keywords):
        missing.append(f"{stage}_handoff")
    return missing


def _read_stage_missing_groups(lowered_text: str, state: dict) -> list[str]:
    missing: list[str] = []
    has_location = bool(state.get("read_paths") or state.get("searched_patterns"))
    if not state.get("read_evidence_seen") or not has_location:
        missing.append("read_state")
    if not _has_any_keyword(lowered_text, READ_INSPECTION_KEYWORDS) or not _has_any_keyword(
        lowered_text, READ_CONCLUSION_KEYWORDS
    ):
        missing.append("read_handoff")
    return missing


def _review_stage_missing_groups(lowered_text: str, state: dict) -> list[str]:
    missing: list[str] = []
    has_reviewed_artifact = bool(
        state.get("review_artifact_seen")
        or state.get("review_targets")
        or state.get("reviewed_diff_evidence_seen")
    )
    if not has_reviewed_artifact:
        missing.append("review_artifact")
    if not _has_any_keyword(lowered_text, REVIEW_FINDING_KEYWORDS):
        missing.append("review_findings")
    return missing


def _has_workflow_keyword(lowered_text: str, group: str) -> bool:
    return _has_any_keyword(lowered_text, WORKFLOW_CLOSURE_KEYWORDS.get(group, []))


def _workflow_state_key(group: str) -> str:
    return {
        "repository_context": "repository_context_seen",
        "workflow_state": "workflow_state_seen",
        "tool_permission_sandbox": "tool_permission_sandbox_seen",
        "skill_efficacy": "skill_efficacy_benchmark_seen",
        "plan_execution_consistency": "plan_execution_consistency_seen",
        "validation_freshness": "validation_freshness_seen",
        "senior_programming_judgment": "senior_programming_judgment_complete",
    }.get(group, "")


def _tool_permission_required(state: dict) -> bool:
    return bool(
        state.get("permission_gate_seen")
        or state.get("permission_decisions")
        or state.get("command_risk_surfaces")
        or state.get("closure_risk_surfaces")
    )


def _skill_efficacy_required(state: dict) -> bool:
    raw_paths = state.get("changed_paths", [])
    if classify_skill_behavior_change is not None:
        try:
            result = classify_skill_behavior_change(raw_paths)
        except Exception:
            result = {}
        if isinstance(result, dict) and result.get("requires_skill_efficacy_benchmark") is True:
            return True
    paths = [str(path).casefold() for path in raw_paths]
    registry_path_marker = "/".join(("src", "registry")) + "/"
    return any(
        "skill.md" in path
        or registry_path_marker in path
        or "routing-rules.yaml" in path
        or "stage-model.yaml" in path
        or "hook-runtime" in path
        or path.startswith("evals/")
        or "benchmark" in path
        for path in paths
    )


def _has_any_keyword(lowered_text: str, keywords: list[str]) -> bool:
    return any(keyword.casefold() in lowered_text for keyword in keywords)


def _implementation_preflight_required(state: dict) -> bool:
    profile = _closure_profile(state)
    if profile in {"silent", "read_review"}:
        return False
    return bool(
        state.get("implementation_preflight_required")
        or state.get("edit_without_preflight_seen")
        or state.get("post_edit_confirmed_preflight_gap")
        or state.get("pre_edit_structure_findings")
        or state.get("changed_paths")
    )


def _has_implementation_preflight_evidence(text: str, state: dict) -> bool:
    if not text:
        return False
    manifest = extract_implementation_preflight_fields(text)
    if manifest.get("present"):
        complete = bool(
            manifest.get("read_evidence")
            and manifest.get("placement_decision")
            and manifest.get("reuse_decision")
            and manifest.get("test_plan")
            and manifest.get("risk")
        )
        if state.get("advanced_refactor_findings") or state.get("pre_edit_structure_findings"):
            complete = complete and bool(manifest.get("object_boundary"))
        return complete
    lowered = text.casefold()
    required_terms = (
        "preflight",
        "read evidence",
        "placement",
        "reuse",
        "test plan",
        "risk",
    )
    if not all(term in lowered for term in required_terms):
        return False
    if state.get("advanced_refactor_findings") or state.get("pre_edit_structure_findings"):
        return "object" in lowered or "boundary" in lowered or "module" in lowered
    return True


def _senior_programming_judgment_required(state: dict) -> bool:
    profile = _closure_profile(state)
    if profile in {"silent", "read_review"}:
        return False
    return bool(
        state.get("senior_programming_judgment_required")
        or state.get("pre_edit_missing_senior_programming_judgment")
        or state.get("changed_paths")
    )


def _has_senior_programming_judgment_evidence(text: str, state: dict) -> bool:
    if state.get("senior_programming_judgment_complete"):
        return True
    if not text:
        return False
    manifest = extract_senior_programming_judgment_fields(text)
    if manifest.get("present"):
        return bool(manifest.get("complete"))
    lowered = text.casefold()
    required_terms = (
        "senior programming judgment",
        "purpose",
        "facts",
        "objects",
        "states",
        "behaviors",
        "rules",
        "invariants",
        "boundaries",
        "failure contract",
        "side effects",
        "reuse",
        "placement",
        "minimality",
        "validation map",
        "observability map",
        "residual risk",
    )
    return all(term in lowered for term in required_terms)


def _validation_broker_assessment(
    final_text: str,
    state: dict,
    mode: str,
    manifest: dict | None = None,
    runtime: str | None = None,
) -> dict:
    if assess_validation_closure is None:
        return {}
    try:
        assessment_state = dict(state)
        active_unsupported = _active_manifest_unsupported_checks(
            state,
            manifest or {},
            runtime or _GATE_RUNTIME,
        )
        existing_raw = assessment_state.get("unsupported_adapter_events") or []
        if isinstance(existing_raw, (list, tuple, set)):
            existing = list(existing_raw)
        elif existing_raw:
            existing = [existing_raw]
        else:
            existing = []
        unsupported = _unique_strings([*existing, *active_unsupported])
        if unsupported:
            assessment_state["unsupported_adapter_events"] = unsupported
        return assess_validation_closure(
            final_text,
            assessment_state,
            block_mode=mode == "block",
        )
    except Exception:
        return {}


def _active_manifest_unsupported_checks(state: dict, manifest: dict, runtime: str | None) -> list[str]:
    capabilities = adapter_capabilities_for(runtime or _GATE_RUNTIME)
    unsupported = list(getattr(capabilities, "unsupported_checks", ()) or [])
    if not unsupported:
        return []
    requested: list[object] = []
    for key in ("closure_required_checks", "active_unsupported_checks", "required_unsupported_checks"):
        requested.extend(_list_values(state.get(key)))
    adapter = state.get("runtime_adapter")
    if isinstance(adapter, dict):
        requested.extend(_list_values(adapter.get("active_unsupported_checks")))
        requested.extend(_list_values(adapter.get("required_unsupported_checks")))
    for key in ("required_quality_gates", "required_references", "selected_capabilities"):
        requested.extend(_list_values(manifest.get(key)))
    requested_norm = [_unsupported_check_token(item) for item in requested]
    active: list[str] = []
    for check in unsupported:
        check_norm = _unsupported_check_token(check)
        if check_norm and any(check_norm in item or item in check_norm for item in requested_norm if item):
            active.append(str(check))
    return _unique_strings(active)


def _list_values(value: object) -> list[object]:
    if isinstance(value, (list, tuple, set)):
        return list(value)
    if value:
        return [value]
    return []


def _unsupported_check_token(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").casefold())


def _validation_result(assessment: dict | None) -> dict:
    if not isinstance(assessment, dict):
        return {}
    result = assessment.get("validation_result")
    return result if isinstance(result, dict) else {}


def _validation_broker_result(assessment: dict | None) -> dict:
    if not isinstance(assessment, dict):
        return {}
    result = assessment.get("validation_broker_result")
    return result if isinstance(result, dict) else {}


def _telemetry_truth(value: object) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value == "unknown":
        return "unknown"
    return ""


def _validation_freshness_label(value: object) -> str:
    if value is True:
        return "current"
    if value is False:
        return "stale"
    if value == "unknown":
        return "unknown"
    return ""


def _unverified_completion(text: str, state: dict) -> bool:
    """Presence check: completion language with no validation evidence.

    This never judges whether the claim is true. It notices a completion claim
    in the final handoff and pairs it with the absence of any validation signal,
    so the closure reminder can ask for evidence or a not-verified disclosure.
    The Stop gate stays presence-only and fails open.
    """
    if not text:
        return False
    lowered = text.casefold()
    has_completion = any(phrase.casefold() in lowered for phrase in COMPLETION_LANGUAGE)
    if not has_completion:
        return False
    return not _has_validation_evidence(text, state)


def _has_validation_evidence(
    text: str,
    state: dict,
    validation_assessment: dict | None = None,
) -> bool:
    """Return true only for strong validation evidence in the closure text.

    A command-like string in hook state means a validation command was observed,
    not that it succeeded. The final handoff still needs an outcome, exit code,
    output, or artifact signal. Negative validation disclosures explicitly block
    this from being counted as evidence.
    """
    if not text:
        return False
    lowered = text.casefold()
    if _has_negative_validation_phrase(lowered):
        return False
    state_validation_pass = _state_has_fresh_validation_pass(state)
    if validation_assessment is None and assess_validation_closure is not None:
        validation_assessment = _validation_broker_assessment(text, state, "warn")
    broker_result = _validation_broker_result(validation_assessment)
    result = _validation_result(validation_assessment)
    soft_gap = False
    if broker_result:
        soft_gap = _soft_validation_coverage_gap(
            final_text=text,
            state=state,
            validation_result=result,
            broker_result=broker_result,
        )
        validation_blockers = {
            "missing_validation",
            "validation_command_without_outcome",
            "validation_not_run",
            "validation_failed",
            "stale_validation",
        }
        negatives = set(str(item) for item in broker_result.get("negative_evidence", []) or [])
        if negatives & validation_blockers and not soft_gap:
            if not _state_validation_satisfies_broker_gap(text, state, broker_result):
                return False
    if result:
        if result.get("fresh_after_last_edit") is False:
            return False
        if result.get("outcome") == "pass":
            return result.get("evidence_strength") == "strong"
        if result.get("outcome") == "fail":
            return False
    if state_validation_pass:
        return True
    command_seen = bool(state.get("validation_command_seen") or state.get("validation_seen"))
    command_in_text = bool(VALIDATION_COMMAND_RE.search(text))
    outcome_in_text = bool(VALIDATION_OUTCOME_RE.search(text))
    artifact_in_text = bool(VALIDATION_ARTIFACT_RE.search(text))
    if outcome_in_text and (command_seen or command_in_text or artifact_in_text):
        return True
    if command_in_text and artifact_in_text:
        return True
    return False



def _state_has_fresh_validation_pass(state: dict) -> bool:
    last_validation_index = _int_state_value(state.get("last_validation_command_index"))
    last_material_index = _int_state_value(state.get("last_material_edit_index"))
    if last_material_index and (not last_validation_index or last_validation_index < last_material_index):
        return False
    results = [str(item).strip() for item in state.get("validation_results") or [] if str(item).strip()]
    if not results:
        return False
    for raw in reversed(results):
        lowered = raw.casefold()
        if _validation_result_is_negative(lowered):
            return False
        if _validation_result_is_pass(lowered):
            if state.get("validation_freshness_seen") or any(
                marker in lowered for marker in ("current", "fresh", "fresh_after_last_edit:true")
            ):
                return True
            return not bool(state.get("changed_paths") or state.get("generated_paths") or state.get("deleted_paths"))
    return False


def _state_validation_satisfies_broker_gap(text: str, state: dict, broker_result: dict) -> bool:
    if not _state_has_fresh_validation_pass(state):
        return False
    negatives = {str(item) for item in broker_result.get("negative_evidence", []) or []}
    hard_blockers = {
        "validation_failed",
        "stale_validation",
        "targeted_check_reported_as_full",
        "repair_without_rereview",
    }
    if negatives & hard_blockers:
        return False
    allowed = {
        "missing_validation",
        "not_run",
        "validation_command_without_outcome",
        "validation_not_run",
        "freshness_unknown",
        "coverage_mismatch",
        "changed_path_without_validator",
        "missed_residual_risk",
        "unsupported_adapter_check",
    }
    if not negatives <= allowed:
        return False
    scoped_negatives = {
        "coverage_mismatch",
        "changed_path_without_validator",
        "missed_residual_risk",
        "unsupported_adapter_check",
    }
    if negatives & scoped_negatives:
        lowered = str(text or "").casefold()
        return "residual" in lowered or "risk" in lowered or "风险" in lowered or bool(state.get("residual_risk_seen"))
    return True


def _validation_result_is_negative(lowered_result: str) -> bool:
    return (
        lowered_result.startswith(("fail", "failed", "not_run", "not run", "unknown", "stale"))
        or "stale_after_material_change" in lowered_result
        or "validation_before_latest_edit" in lowered_result
        or lowered_result.startswith("unknown:")
    )


def _validation_result_is_pass(lowered_result: str) -> bool:
    return (
        lowered_result.startswith("pass")
        or lowered_result.endswith(":pass")
        or ": pass" in lowered_result
        or " passed" in lowered_result
        or "exit 0" in lowered_result
        or "退出码 0" in lowered_result
    )


def _int_state_value(value: object) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _soft_validation_coverage_gap(
    *,
    final_text: str,
    state: dict,
    validation_result: dict,
    broker_result: dict,
) -> bool:
    negatives = {str(item) for item in broker_result.get("negative_evidence", []) or []}
    if not negatives:
        return False
    hard_blockers = {
        "missing_validation",
        "validation_command_without_outcome",
        "validation_not_run",
        "validation_failed",
        "stale_validation",
        "targeted_check_reported_as_full",
        "repair_without_rereview",
    }
    if negatives & hard_blockers:
        return False
    allowed_soft = {
        "freshness_unknown",
        "coverage_mismatch",
        "changed_path_without_validator",
        "missed_residual_risk",
        "unsupported_adapter_check",
    }
    if not negatives <= allowed_soft:
        return False
    if validation_result.get("outcome") != "pass" or validation_result.get("evidence_strength") != "strong":
        return False
    lowered = str(final_text or "").casefold()
    residual_disclosed = "residual" in lowered or "风险" in lowered or bool(state.get("residual_risk_seen"))
    scoped_evidence = (
        "repository_context:" in lowered
        or "validation:" in lowered
        or "fresh_commands:" in lowered
        or "targeted" in lowered
        or "受影响" in lowered
    )
    return bool(residual_disclosed and scoped_evidence)

def _has_negative_validation_phrase(lowered_text: str) -> bool:
    return any(phrase.casefold() in lowered_text for phrase in NEGATIVE_VALIDATION_PHRASES)


if __name__ == "__main__":
    raise SystemExit(main())
