#!/usr/bin/env python3
"""Enforce ChangeForge PDD/DDD/SDD/TDD runtime phase evidence."""

from __future__ import annotations

import hashlib
import os
import re
import sys
from pathlib import Path
from typing import Any

from changeforge_adapter_capabilities import adapter_capabilities_for
from changeforge_common import (
    compact_name,
    cwd_from_event,
    detect_runtime,
    event_name,
    extract_bash_command,
    extract_changed_paths,
    is_pre_tool_use,
    is_stop,
    is_user_prompt_submit,
    load_state,
    merge_state,
    normalize_path,
    read_event,
    repo_root,
    session_id_from_event,
    tool_name,
    write_telemetry_event,
)
from changeforge_hook_policy import gate_mode, gate_mode_for_stage, run_gate_with_policy, should_emit_context
from changeforge_runtime_adapters import adapter_for
from changeforge_runtime_route_resolver import CODE_FILE_EXTENSIONS

try:
    from runtime_governance.process_phase import (
        merge_process_phase_ledger,
        normalize_process_phase_ledger,
        phase_blockers,
        phase_review_passes,
        sanitize_phase_review_result,
    )
except ModuleNotFoundError:  # Source-tree hook execution.
    _src_root = Path(__file__).resolve().parents[2]
    if str(_src_root) not in sys.path:
        sys.path.insert(0, str(_src_root))
    from runtime_governance.process_phase import (  # type: ignore[no-redef]
        merge_process_phase_ledger,
        normalize_process_phase_ledger,
        phase_blockers,
        phase_review_passes,
        sanitize_phase_review_result,
    )


GATE_NAME = "process_phase"
SUPERPOWERS_ADVISORY_POLICY = (
    "Superpowers-derived process checks collect bounded facts and advisory risk; "
    "ordinary agents are not asked to repair hook state or internal process artifacts."
)
EDIT_TOOLS = {"applypatch", "apply_patch", "edit", "write", "multiedit", "replace_string_in_file", "create_file"}
DOC_EXTENSIONS = {".md", ".mdx", ".rst", ".adoc", ".txt"}
CONFIG_EXTENSIONS = {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"}
ENGINEERING_PROMPT_RE = re.compile(
    r"\b(add|implement|fix|refactor|change|modify|update|build|create|remove|delete|"
    r"migrate|schema|api|hook|runtime|validator|test|repair|review|code|module|service)\b",
    re.IGNORECASE,
)
CHINESE_ENGINEERING_TRIGGERS = (
    "实现",
    "修复",
    "修改",
    "优化",
    "重构",
    "新增",
    "删除",
    "迁移",
    "调整",
    "接入",
    "改造",
    "审查",
    "检查",
    "验证",
    "测试",
    "提交",
    "代码",
    "模块",
    "接口",
    "运行时",
    "钩子",
    "流程",
    "状态机",
)
READ_ONLY_COMMAND_RE = re.compile(
    r"^\s*(?:[A-Z_][A-Z0-9_]*=\S+\s+)*(?:rg|grep|cat|sed(?!\s+-[^\n]*i\b)|awk|ls|find|pwd|"
    r"git\s+(?:diff|status|show|log)|python3?\s+-m\s+(?:unittest|json\.tool|py_compile)|"
    r"python3?\s+scripts/(?:validate[-_\w.]*|eval[-_\w.]*|audit[-_\w.]*|build\.py|run-codegen-benchmarks\.py)|"
    r"pytest|npm\s+test|pnpm\s+test|yarn\s+test)\b",
    re.IGNORECASE,
)
BASH_MUTATION_RE = re.compile(
    r"(\b(apply_patch|rm|mv|cp|mkdir|touch|tee|chmod|chown|"
    r"git\s+(?:commit|checkout|reset|push|rebase|clean))\b|>>?|\bsed\s+-[^\n]*i\b|\bperl\s+-[^\n]*i\b)",
    re.IGNORECASE,
)
SCRIPT_WRITE_RE = re.compile(
    r"(Path\([^\n]+\)\.(?:write_text|write_bytes)|open\([^\n]+['\"]w['\"]|"
    r"\.write\(|writeFileSync|appendFileSync|File\.write|"
    r"python3?\s+scripts/(?!validate|eval|build|run-codegen-benchmarks)[\w./-]+\.py)",
    re.IGNORECASE,
)
HOOK_STATE_REPAIR_RE = re.compile(
    r"(current-turn\.json|changeforge/hooks|\.cache/changeforge/hooks|stop_closure_attempts|"
    r"process_phase_ledgers|phase_review_results|phase_review_result|"
    r"choice_resolution_evidence_seen|last_user_choice_hash)",
    re.IGNORECASE,
)
INTERNAL_STATE_ACCESS_RISK = "rd_skills_internal_state_access"

def main() -> int:
    return run_gate_with_policy(GATE_NAME, _main, fail_closed=_fail_closed)


def _fail_closed(exc: Exception) -> None:
    runtime = detect_runtime({})
    adapter_for(runtime).emit_permission_decision(
        "block",
        f"ChangeForge Process Phase Gate failed closed: {exc}",
    )


def _main() -> int:
    event = read_event()
    if not event:
        return 0
    runtime = detect_runtime(event)
    repo = repo_root(cwd_from_event(event))
    state = load_state(repo)
    if is_user_prompt_submit(event):
        mode = gate_mode(GATE_NAME)
        if mode == "off":
            return 0
        return _handle_user_prompt(event, runtime, repo, mode)
    if is_pre_tool_use(event):
        mode = gate_mode_for_stage(GATE_NAME, "pretool")
        if mode == "off":
            return 0
        return _handle_pre_tool(event, runtime, repo, state, mode)
    if is_stop(event):
        mode = gate_mode_for_stage(GATE_NAME, "stop")
        if mode == "off":
            return 0
        return _handle_stop(event, runtime, repo, state, mode)
    return 0


def _handle_user_prompt(event: dict, runtime: str, repo: Path, mode: str) -> int:
    text = _event_text(event)
    internal_state_access = _text_has_internal_state_access_signal(text)
    if internal_state_access and not _maintenance_mode_enabled():
        _record_internal_state_access_prompt(event, runtime, repo, mode)
    if not prompt_requires_process(text):
        return 0
    ledger = normalize_process_phase_ledger(
        {
            "route_id": "active-runtime-route",
            "current_phase": "pdd",
            "updated_by_hook": "changeforge_process_phase_gate",
        }
    )
    merge_state(
        repo,
        runtime,
        process_phase_ledgers=[ledger],
        process_current_phase="pdd",
        process_phase_ledger_seen=True,
        prompt_signals=["process_phase_required"],
        risk_surfaces=_internal_state_risks(internal_state_access),
        closure_risk_surfaces=_internal_state_risks(internal_state_access),
        suggested_skills=["development-process-orchestrator"],
        suggested_capabilities=["pdd-ddd-sdd-tdd-runtime-phase-ledger"],
        suggested_gates=["quality-test-gate", "ai-code-review-refactor"],
    )
    write_telemetry_event(
        repo,
        runtime=runtime,
        hook_name="process_phase_gate",
        event_name=event_name(event) or "UserPromptSubmit",
        mode=mode,
        session_id=session_id_from_event(event),
        cwd=cwd_from_event(event),
        process_phase_ledgers=[ledger],
        process_current_phase="pdd",
        process_phase_ledger_seen=True,
        risk_surfaces=_internal_state_risks(internal_state_access),
    )
    if mode not in {"monitor", "off"} and should_emit_context(GATE_NAME):
        adapter_for(runtime).emit_context(event_name(event) or "UserPromptSubmit", render_prompt_message())
    return 0


def _handle_pre_tool(event: dict, runtime: str, repo: Path, state: dict, mode: str) -> int:
    result = evaluate_pre_tool_process_phase(event, state, runtime=runtime)
    if not result["required"]:
        return 0
    _record_result(event, runtime, repo, state, mode, result, event_label="PreToolUse")
    if not result["blocks"] or mode == "monitor":
        return 0
    message = render_pre_tool_message(result)
    capabilities = adapter_capabilities_for(runtime)
    adapter = adapter_for(runtime)
    if mode == "block" and capabilities.supports_pre_tool_block:
        adapter.emit_permission_decision("block", message)
    elif should_emit_context(GATE_NAME):
        adapter.emit_context(event_name(event) or "PreToolUse", message)
    return 0


def _handle_stop(event: dict, runtime: str, repo: Path, state: dict, mode: str) -> int:
    text = _event_text(event)
    stop_state = _state_with_stop_phase_evidence(state, text)
    internal_state_access = _text_has_internal_state_access_signal(text)
    internal_state_access = internal_state_access and not _maintenance_mode_enabled()
    if internal_state_access:
        stop_state = dict(stop_state)
        stop_state["risk_surfaces"] = _unique(
            [
                *[str(item) for item in stop_state.get("risk_surfaces") or []],
                INTERNAL_STATE_ACCESS_RISK,
            ]
        )
        stop_state["closure_risk_surfaces"] = _unique(
            [
                *[str(item) for item in stop_state.get("closure_risk_surfaces") or []],
                INTERNAL_STATE_ACCESS_RISK,
            ]
        )
    result = evaluate_stop_process_phase(stop_state, runtime=runtime)
    if internal_state_access:
        result["internal_state_access"] = True
        result["blocks"] = True
        result["blockers"] = _unique(
            [
                "rd_skills_internal_state_access: ordinary handoff must not use rd-skills hook state as repair evidence",
                *(result.get("blockers") or []),
            ]
        )
    if not result["required"]:
        return 0
    _record_result(event, runtime, repo, state, mode, result, event_label="Stop")
    if not result["blocks"] or mode == "monitor":
        return 0
    message = render_stop_message(result)
    capabilities = adapter_capabilities_for(runtime)
    adapter = adapter_for(runtime)
    if mode == "block" and capabilities.stop_block_supported:
        adapter.emit_stop(message, continue_turn=False)
    elif should_emit_context(GATE_NAME):
        adapter.emit_stop(message, continue_turn=False)
    return 0


def prompt_requires_process(text: str) -> bool:
    """Return whether a user prompt likely starts non-trivial engineering work."""
    stripped = str(text or "").strip()
    if len(stripped) < 16:
        return False
    if any(trigger in stripped for trigger in CHINESE_ENGINEERING_TRIGGERS):
        return True
    return bool(ENGINEERING_PROMPT_RE.search(stripped))


def evaluate_pre_tool_process_phase(event: dict, state: dict | None = None, *, runtime: str = "codex") -> dict:
    """Evaluate whether a mutation is allowed by reviewed phase evidence."""
    state = state if isinstance(state, dict) else {}
    paths = [normalize_path(path) for path in extract_changed_paths(event)]
    tool = compact_name(tool_name(event))
    command = extract_bash_command(event)
    internal_state_access = tool == "bash" and _is_hook_state_repair_command(command)
    if internal_state_access and _maintenance_mode_enabled():
        return _result(
            required=True,
            blocks=False,
            changed_paths=paths,
            tool_category=tool or "unknown",
            degraded=[
                "hook_state_maintenance_report: maintenance-mode rd-skills state access observed; this does not count as engineering evidence"
            ],
        )
    if not _is_engineering_mutation(tool, paths, command):
        return _result(required=False, changed_paths=paths, tool_category=tool or "unknown")
    result = _evaluate_state_for_implementation(state, runtime=runtime)
    if internal_state_access:
        result["internal_state_access"] = True
        result["blocks"] = True
        result["blockers"] = [
            "rd_skills_internal_state_access: ordinary engineering tasks must not inspect or write rd-skills hook state",
            *(result.get("blockers") or []),
        ]
    result.update({"required": True, "changed_paths": paths, "tool_category": tool or "unknown"})
    return result


def evaluate_stop_process_phase(state: dict | None = None, *, runtime: str = "codex") -> dict:
    """Evaluate final closure requirements for phase, repair, and re-review evidence."""
    state = state if isinstance(state, dict) else {}
    if not _state_suggests_engineering_work(state):
        return _result(required=False)
    result = _evaluate_state_for_implementation(state, runtime=runtime)
    closure_blockers = _repair_rereview_blockers(state)
    if closure_blockers:
        result["blockers"].extend(closure_blockers)
        result["blocks"] = True
    result["required"] = True
    return result


def _evaluate_state_for_implementation(state: dict, *, runtime: str) -> dict:
    ledgers = [item for item in state.get("process_phase_ledgers") or [] if isinstance(item, dict)]
    review_results = [item for item in state.get("phase_review_results") or [] if isinstance(item, dict)]
    blockers: list[str] = []
    ledger: dict[str, Any] | None = None
    if not ledgers:
        blockers.append("process_phase_ledger is missing")
    else:
        ledger = merge_process_phase_ledger(ledgers[-1], {}, phase_review_results=review_results)
        blockers.extend(phase_blockers(ledger))
        blockers.extend(_strong_review_provenance_blockers(ledger, review_results))
    blockers.extend(_material_choice_blockers(state, ledger))
    capabilities = adapter_capabilities_for(runtime)
    degraded = []
    if not capabilities.supports_pre_tool_block:
        degraded.append(f"{runtime} lacks PreToolUse hard blocking")
    review_action = _review_required_action(blockers, ledger)
    return _result(
        required=True,
        blocks=bool(blockers),
        blockers=_unique(blockers),
        ledger=ledger or {},
        degraded=degraded,
        phase_artifact_required_action=_phase_artifact_required_action(review_action),
        review_required_action=review_action,
        pdd_reviewed=_phase_reviewed(ledger, "pdd"),
        ddd_reviewed=_phase_reviewed(ledger, "ddd"),
        sdd_reviewed=_phase_reviewed(ledger, "sdd"),
        tdd_reviewed=_phase_reviewed(ledger, "tdd"),
    )


def _record_result(
    event: dict,
    runtime: str,
    repo: Path,
    state: dict,
    mode: str,
    result: dict,
    *,
    event_label: str,
) -> None:
    blockers = result.get("blockers") or []
    degraded = result.get("degraded") or []
    ledger = result.get("ledger") if isinstance(result.get("ledger"), dict) else {}
    internal_state_access = bool(result.get("internal_state_access"))
    risk_surfaces = _internal_state_risks(internal_state_access)
    phase_findings = [
        {
            "finding_id": f"process-phase-{index + 1}",
            "phase": str(ledger.get("current_phase") or "implementation"),
            "severity": "high",
            "evidence": blocker,
            "required_fix": "produce and independently review required PDD/DDD/SDD/TDD phase evidence",
            "blocks_next_stage": True,
            "resolved": False,
        }
        for index, blocker in enumerate(blockers[:10])
    ]
    reason = "; ".join([*blockers, *degraded])[:300]
    merge_state(
        repo,
        runtime,
        process_phase_ledgers=[ledger] if ledger else [],
        phase_review_findings=phase_findings,
        process_phase_blocked=bool(blockers),
        process_phase_blocked_reason=reason,
        process_phase_ledger_seen=bool(ledger),
        phase_disclosures=result.get("phase_disclosures") or [],
        phase_disclosure_seen=bool(result.get("phase_disclosure_seen")),
        phase_evidence_strength=result.get("phase_evidence_strength") or None,
        phase_review_seen=bool(state.get("phase_review_results")),
        pdd_reviewed=bool(result.get("pdd_reviewed")),
        ddd_reviewed=bool(result.get("ddd_reviewed")),
        sdd_reviewed=bool(result.get("sdd_reviewed")),
        tdd_reviewed=bool(result.get("tdd_reviewed")),
        process_current_phase=str(ledger.get("current_phase") or ""),
        validation_freshness_seen=bool(ledger.get("validation_signal_present")),
        prompt_signals=[f"process_phase_{event_label.lower()}"],
        risk_surfaces=risk_surfaces,
        closure_risk_surfaces=risk_surfaces,
    )
    write_telemetry_event(
        repo,
        runtime=runtime,
        hook_name="process_phase_gate",
        event_name=event_name(event) or event_label,
        mode=mode,
        session_id=session_id_from_event(event),
        cwd=cwd_from_event(event),
        tool_name=tool_name(event),
        risk_surfaces=risk_surfaces,
        changed_paths=result.get("changed_paths") or [],
        process_phase_ledgers=[ledger] if ledger else [],
        phase_review_findings=phase_findings,
        process_phase_blocked=bool(blockers),
        process_phase_blocked_reason=reason,
        process_phase_ledger_seen=bool(ledger),
        phase_review_seen=bool(state.get("phase_review_results")),
        pdd_reviewed=bool(result.get("pdd_reviewed")),
        ddd_reviewed=bool(result.get("ddd_reviewed")),
        sdd_reviewed=bool(result.get("sdd_reviewed")),
        tdd_reviewed=bool(result.get("tdd_reviewed")),
        process_current_phase=str(ledger.get("current_phase") or ""),
        hook_findings={"blockers": blockers, "degraded": degraded, "risks": risk_surfaces},
    )



def _state_with_stop_phase_evidence(state: dict, text: str) -> dict:
    """Record final-handoff phase mentions as weak disclosure only."""
    if not isinstance(text, str) or not text.strip():
        return state
    lowered = text.casefold()
    phase_record_seen = any(
        marker in lowered
        for marker in ("process_phase_ledger:", "phase_ledger:", "changeforge_process_phase:")
    )
    phases = ("pdd", "ddd", "sdd", "tdd")
    phases_mentioned = [phase for phase in phases if phase in lowered]
    if not (phase_record_seen and phases_mentioned):
        return state
    updated = dict(state)
    disclosures = [item for item in updated.get("phase_disclosures") or [] if isinstance(item, dict)]
    disclosures.append(
        {
            "source": "final_handoff",
            "strength": "weak",
            "phases_mentioned": phases_mentioned,
            "cannot_satisfy_pretool_readiness": True,
        }
    )
    updated["phase_disclosures"] = disclosures
    updated["phase_disclosure_seen"] = True
    updated["phase_evidence_strength"] = "weak"
    return updated

def _stop_text_has_validation_signal(lowered_text: str) -> bool:
    return any(
        marker in lowered_text
        for marker in (
            "validation_signal_present: true",
            "validation_freshness: fresh",
            "fresh validation",
            "exit 0",
            "passed",
            "通过",
        )
    )

def render_prompt_message() -> str:
    return (
        "Engineering expert note:\n"
        "你正在处理非平凡工程任务。建议先确认当前行为、owner 模块、相关测试、"
        "设计边界和验证计划，再进行实现或交付。"
    )


def render_pre_tool_message(result: dict) -> str:
    lines = ["Engineering expert note:"]
    lines.append("你准备修改代码，但当前工程阶段证据不完整。继续前建议先补足源码阅读、设计边界、测试计划和独立评审证据。")
    for blocker in (result.get("blockers") or [])[:4]:
        lines.append(f"- observed gap: {str(blocker).replace('process_phase_ledger', 'process planning evidence').replace('independently reviewed', 'independently checked').replace('unresolved_blocking_choices', 'unresolved design choices')}")
    for degraded in result.get("degraded") or []:
        lines.append(f"- quality degradation: {degraded}")
    lines.append("Natural next step: inspect the owner module and nearby tests, explain compatibility and validation coverage, then run the smallest meaningful affected check.")
    return "\n".join(lines)


def render_stop_message(result: dict) -> str:
    blockers = [str(item) for item in result.get("blockers") or []]
    if result.get("internal_state_access"):
        status = "fail"
    elif blockers:
        status = "degraded_ready"
    else:
        status = "pass"
    validation = "fresh" if result.get("tdd_reviewed") else "missing_or_stale"
    review = "degraded" if blockers else "independent_review_evidence_present"
    lines = ["engineering_quality_report:"]
    lines.append(f"  status: {status}")
    lines.append(f"  validation_freshness: {validation}")
    lines.append(f"  review_authenticity: {review}")
    lines.append("  residual_risk:")
    if blockers:
        for blocker in blockers[:4]:
            text = blocker.replace("process_phase_ledger", "process planning evidence")
            text = text.replace("independently reviewed", "independently checked")
            text = text.replace("unresolved_blocking_choices", "unresolved choices")
            lines.append(f"    - {text}")
    else:
        lines.append("    - none_detected")
    lines.append("  recommended_human_action:")
    lines.append("    - review the current diff and validation evidence")
    lines.append("    - run the affected validation set")
    lines.append("    - verify outside systems separately when relevant")
    return "\n".join(lines)


def _review_required_action(blockers: list[str], ledger: dict[str, Any] | None) -> dict[str, Any]:
    phase = ""
    for blocker in blockers:
        match = re.search(r"\b(PDD|DDD|SDD|TDD) is not independently reviewed\b", str(blocker))
        if match:
            phase = match.group(1).casefold()
            break
    if not phase and any("process_phase_ledger is missing" in str(item) for item in blockers):
        phase = "pdd"
    if not phase:
        return {}
    digests = ledger.get("artifact_digests") if isinstance(ledger, dict) else {}
    artifact_digest = ""
    if isinstance(digests, dict):
        artifact_digest = str(digests.get(phase) or "")
    return {
        "schema_version": 1,
        "phase": phase,
        "artifact_digest": artifact_digest,
        "required_reviewer": "independent",
        "allowed_modes": [
            "subagent_review",
            "parent_independent_review_when_subagent_unavailable",
        ],
        "expected_event_chain": [
            "SubagentStart",
            "review_capsule",
            "SubagentStop",
            "phase_review_result",
        ],
        "expected_output": {
            "type": "phase_review_result",
            "required_fields": [
                "review_id",
                "phase",
                "reviewer_skill",
                "owner_skill",
                "reviewed_artifact_digest",
                "verdict",
                "score",
                "approved_scope",
            ],
        },
        "fallback_if_subagent_unavailable": {
            "type": "parent_independent_review_result",
            "requires": [
                "review_source",
                "expected_artifact_digest",
                "review_context_strength",
                "reviewer_boundary",
            ],
        },
    }


def _phase_artifact_required_action(review_action: dict[str, Any]) -> dict[str, Any]:
    if not review_action or review_action.get("artifact_digest"):
        return {}
    return {
        "schema_version": 1,
        "phase": review_action.get("phase") or "pdd",
        "next_action": "create_process_phase_artifact",
        "required_fields": [
            "phase",
            "artifact_digest",
            "artifact_summary",
            "source_evidence",
            "traceability",
        ],
        "then": ["create_review_capsule", "run_independent_review"],
        "note": "review cannot pass without a real artifact_digest",
    }


def _render_phase_artifact_required_action(action: dict[str, Any]) -> str:
    lines = ["phase_artifact_required_action:"]
    lines.append("  schema_version: 1")
    lines.append(f"  phase: {action.get('phase')}")
    lines.append("  next_action: create_process_phase_artifact")
    lines.append("  required_fields:")
    for field in action.get("required_fields") or []:
        lines.append(f"    - {field}")
    lines.append("  then:")
    for item in action.get("then") or []:
        lines.append(f"    - {item}")
    lines.append(f"  note: {action.get('note')}")
    return "\n".join(lines)


def _render_review_required_action(action: dict[str, Any]) -> str:
    lines = ["review_required_action:"]
    lines.append("  schema_version: 1")
    lines.append(f"  phase: {action.get('phase')}")
    lines.append(f"  artifact_digest: {action.get('artifact_digest') or ''}")
    lines.append("  required_reviewer: independent")
    lines.append("  allowed_modes:")
    for mode in action.get("allowed_modes") or []:
        lines.append(f"    - {mode}")
    lines.append("  expected_event_chain:")
    for event_name_value in action.get("expected_event_chain") or []:
        lines.append(f"    - {event_name_value}")
    lines.append("  expected_output:")
    lines.append("    type: phase_review_result")
    lines.append("    required_fields:")
    for field in (action.get("expected_output") or {}).get("required_fields") or []:
        lines.append(f"      - {field}")
    lines.append("  fallback_if_subagent_unavailable:")
    lines.append("    type: parent_independent_review_result")
    lines.append("    requires:")
    for field in (action.get("fallback_if_subagent_unavailable") or {}).get("requires") or []:
        lines.append(f"      - {field}")
    return "\n".join(lines)


def _result(**overrides: Any) -> dict[str, Any]:
    result = {
        "required": False,
        "blocks": False,
        "blockers": [],
        "ledger": {},
        "degraded": [],
        "changed_paths": [],
        "tool_category": "unknown",
        "phase_artifact_required_action": {},
        "review_required_action": {},
        "pdd_reviewed": False,
        "ddd_reviewed": False,
        "sdd_reviewed": False,
        "tdd_reviewed": False,
    }
    result.update(overrides)
    return result


def _is_engineering_mutation(tool: str, paths: list[str], command: str) -> bool:
    if tool == "bash":
        if _is_hook_state_repair_command(command):
            return not _maintenance_mode_enabled()
        if not command or READ_ONLY_COMMAND_RE.search(command):
            return False
        return bool(BASH_MUTATION_RE.search(command) or SCRIPT_WRITE_RE.search(command))
    if tool not in EDIT_TOOLS:
        return False
    if not paths:
        return True
    return any(_path_requires_process(path) for path in paths)


def _is_hook_state_repair_command(command: str) -> bool:
    if not command or not HOOK_STATE_REPAIR_RE.search(command):
        return False
    lowered = command.casefold()
    source_write = re.search(
        r"\.(?:py|go|ts|tsx|js|jsx|rs|java|kt|swift|c|cc|cpp|h|hpp|md)['\"]?\)\.(?:write_text|write_bytes)",
        lowered,
    )
    return not bool(source_write)



def _maintenance_mode_enabled() -> bool:
    return os.environ.get("CHANGEFORGE_MAINTENANCE_MODE", "").strip().casefold() in {"1", "true", "yes"}

def _path_requires_process(path: str) -> bool:
    suffix = Path(path).suffix.casefold()
    if suffix in DOC_EXTENSIONS:
        return False
    if suffix in CODE_FILE_EXTENSIONS or suffix in CONFIG_EXTENSIONS:
        return True
    lowered = path.casefold()
    return any(token in lowered for token in ("src/", "scripts/", "tests/", "schema", "hook", "runtime"))


def _state_suggests_engineering_work(state: dict) -> bool:
    path_values = []
    for key in ("changed_paths", "generated_paths", "deleted_paths", "bounded_paths", "config_changes"):
        path_values.extend(str(item) for item in state.get(key) or [])
    if any(_path_requires_process(normalize_path(path)) for path in path_values):
        return True
    return bool(state.get("process_phase_ledgers") or state.get("phase_review_results") or state.get("process_phase_blocked"))


def _material_choice_blockers(state: dict, ledger: dict[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    unresolved = int((ledger or {}).get("unresolved_blocking_choices") or 0)
    if unresolved > 0:
        blockers.append("SDD has unresolved blocking material choices")
    if state.get("choice_gate_blocked") and not state.get("choice_resolution_evidence_seen"):
        surfaces = ", ".join(str(item) for item in (state.get("material_choice_surfaces") or [])[:5])
        suffix = f": {surfaces}" if surfaces else ""
        blockers.append(f"SDD material choice gate is unresolved{suffix}")
    return blockers


def _repair_rereview_blockers(state: dict) -> list[str]:
    findings = [
        item
        for item in state.get("phase_review_findings") or []
        if isinstance(item, dict) and item.get("blocks_next_stage") and not item.get("resolved")
    ]
    repairs = {
        str(item.get("finding_id")): item
        for item in state.get("phase_repair_events") or []
        if isinstance(item, dict) and item.get("finding_id")
    }
    rereviews = {
        str(item.get("finding_id")): item
        for item in state.get("phase_rereview_events") or []
        if isinstance(item, dict) and item.get("finding_id")
    }
    blockers: list[str] = []
    for finding in findings:
        finding_id = str(finding.get("finding_id") or "unknown")
        if finding_id not in repairs:
            blockers.append(f"blocking finding {finding_id} requires repair_event")
            continue
        rereview = rereviews.get(finding_id)
        if not rereview:
            blockers.append(f"blocking finding {finding_id} requires rereview_event")
            continue
        if str(rereview.get("verdict") or "").casefold() != "pass":
            blockers.append(f"blocking finding {finding_id} rereview verdict must be pass")
    if findings and not state.get("validation_freshness_seen"):
        blockers.append("validation freshness after phase repair is missing")
    return blockers


def _phase_reviewed(ledger: dict[str, Any] | None, phase: str) -> bool:
    if not isinstance(ledger, dict):
        return False
    return dict(ledger.get("phase_status") or {}).get(phase) in {"reviewed", "not_applicable"}


def _strong_review_provenance_blockers(ledger: dict[str, Any], reviews: list[dict[str, Any]]) -> list[str]:
    if not ledger:
        return []
    statuses = ledger.get("phase_status") if isinstance(ledger.get("phase_status"), dict) else {}
    digests = ledger.get("artifact_digests") if isinstance(ledger.get("artifact_digests"), dict) else {}
    review_ids = ledger.get("review_ids") if isinstance(ledger.get("review_ids"), dict) else {}
    strong = _strong_phase_reviews(reviews, ledger)
    blockers: list[str] = []
    for phase in ledger.get("required_phases") or ("pdd", "ddd", "sdd", "tdd"):
        if phase not in {"pdd", "ddd", "sdd", "tdd"}:
            continue
        if statuses.get(phase) == "not_applicable":
            continue
        if statuses.get(phase) != "reviewed":
            continue
        expected = (str(review_ids.get(phase) or ""), str(digests.get(phase) or ""))
        if not expected[0] or not expected[1] or strong.get(phase) != expected:
            blockers.append(f"{phase.upper()} reviewed status lacks strong review provenance")
    return blockers


def _strong_phase_reviews(
    reviews: list[dict[str, Any]], ledger: dict[str, Any] | None = None
) -> dict[str, tuple[str, str]]:
    digests = ledger.get("artifact_digests") if isinstance((ledger or {}).get("artifact_digests"), dict) else {}
    result: dict[str, tuple[str, str]] = {}
    for review in reviews:
        if not isinstance(review, dict):
            continue
        clean = sanitize_phase_review_result(review)
        phase = str(clean.get("phase") or "")
        if phase not in {"pdd", "ddd", "sdd", "tdd"}:
            continue
        expected = str(digests.get(phase) or clean.get("expected_artifact_digest") or "")
        if not expected:
            continue
        if not phase_review_passes(clean, artifact_digest=expected, require_strong_source=True):
            continue
        result[phase] = (
            str(clean.get("review_id") or ""),
            str(clean.get("reviewed_artifact_digest") or ""),
        )
    return result


def _event_text(event: dict) -> str:
    parts: list[str] = []
    for key in ("prompt", "message", "input", "response", "last_assistant_message", "lastAssistantMessage"):
        value = event.get(key)
        if isinstance(value, str):
            parts.append(value)
    return "\n".join(parts)[:8000]


def _text_has_internal_state_access_signal(text: str) -> bool:
    return bool(text and HOOK_STATE_REPAIR_RE.search(text))


def _internal_state_risks(seen: bool) -> list[str]:
    return [INTERNAL_STATE_ACCESS_RISK] if seen else []


def _record_internal_state_access_prompt(
    event: dict,
    runtime: str,
    repo: Path,
    mode: str,
) -> None:
    risk_surfaces = [INTERNAL_STATE_ACCESS_RISK]
    merge_state(
        repo,
        runtime,
        risk_surfaces=risk_surfaces,
        closure_risk_surfaces=risk_surfaces,
        prompt_signals=[INTERNAL_STATE_ACCESS_RISK],
    )
    write_telemetry_event(
        repo,
        runtime=runtime,
        hook_name="process_phase_gate",
        event_name=event_name(event) or "UserPromptSubmit",
        mode=mode,
        session_id=session_id_from_event(event),
        cwd=cwd_from_event(event),
        risk_surfaces=risk_surfaces,
        hook_findings={"risks": risk_surfaces},
    )

def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
