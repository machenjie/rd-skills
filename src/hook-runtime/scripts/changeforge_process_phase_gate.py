#!/usr/bin/env python3
"""Enforce ChangeForge PDD/DDD/SDD/TDD runtime phase evidence."""

from __future__ import annotations

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
from changeforge_hook_policy import gate_mode, run_gate_with_policy, should_emit_context
from changeforge_runtime_adapters import adapter_for
from changeforge_runtime_route_resolver import CODE_FILE_EXTENSIONS

try:
    from runtime_governance.process_phase import (
        merge_process_phase_ledger,
        normalize_process_phase_ledger,
        phase_blockers,
    )
except ModuleNotFoundError:  # Source-tree hook execution.
    _src_root = Path(__file__).resolve().parents[2]
    if str(_src_root) not in sys.path:
        sys.path.insert(0, str(_src_root))
    from runtime_governance.process_phase import (  # type: ignore[no-redef]
        merge_process_phase_ledger,
        normalize_process_phase_ledger,
        phase_blockers,
    )


GATE_NAME = "process_phase"
EDIT_TOOLS = {"applypatch", "apply_patch", "edit", "write", "multiedit", "replace_string_in_file", "create_file"}
DOC_EXTENSIONS = {".md", ".mdx", ".rst", ".adoc", ".txt"}
CONFIG_EXTENSIONS = {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"}
ENGINEERING_PROMPT_RE = re.compile(
    r"\b(add|implement|fix|refactor|change|modify|update|build|create|remove|delete|"
    r"migrate|schema|api|hook|runtime|validator|test|repair|review|code|module|service)\b",
    re.IGNORECASE,
)
READ_ONLY_COMMAND_RE = re.compile(
    r"^\s*(?:[A-Z_][A-Z0-9_]*=\S+\s+)*(?:rg|grep|cat|sed|awk|ls|find|pwd|"
    r"git\s+(?:diff|status|show|log)|python3?\s+-m\s+(?:unittest|json\.tool|py_compile)|"
    r"pytest|npm\s+test|pnpm\s+test|yarn\s+test)\b",
    re.IGNORECASE,
)
BASH_MUTATION_RE = re.compile(
    r"(\b(apply_patch|rm|mv|cp|mkdir|touch|tee|chmod|chown|"
    r"git\s+(?:commit|checkout|reset|push|rebase|clean))\b|>>?)",
    re.IGNORECASE,
)


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
    mode = gate_mode(GATE_NAME)
    if mode == "off":
        return 0
    runtime = detect_runtime(event)
    repo = repo_root(cwd_from_event(event))
    state = load_state(repo)
    if is_user_prompt_submit(event):
        return _handle_user_prompt(event, runtime, repo, mode)
    if is_pre_tool_use(event):
        return _handle_pre_tool(event, runtime, repo, state, mode)
    if is_stop(event):
        return _handle_stop(event, runtime, repo, state, mode)
    return 0


def _handle_user_prompt(event: dict, runtime: str, repo: Path, mode: str) -> int:
    if not prompt_requires_process(_event_text(event)):
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
    result = evaluate_stop_process_phase(state, runtime=runtime)
    if not result["required"]:
        return 0
    _record_result(event, runtime, repo, state, mode, result, event_label="Stop")
    if not result["blocks"] or mode == "monitor":
        return 0
    message = render_stop_message(result)
    capabilities = adapter_capabilities_for(runtime)
    adapter = adapter_for(runtime)
    if mode == "block" and capabilities.stop_block_supported:
        adapter.emit_stop(message, continue_turn=True)
    elif should_emit_context(GATE_NAME):
        adapter.emit_stop(message, continue_turn=False)
    return 0


def prompt_requires_process(text: str) -> bool:
    """Return whether a user prompt likely starts non-trivial engineering work."""
    stripped = str(text or "").strip()
    if len(stripped) < 16:
        return False
    return bool(ENGINEERING_PROMPT_RE.search(stripped))


def evaluate_pre_tool_process_phase(event: dict, state: dict | None = None, *, runtime: str = "codex") -> dict:
    """Evaluate whether a mutation is allowed by reviewed phase evidence."""
    state = state if isinstance(state, dict) else {}
    paths = [normalize_path(path) for path in extract_changed_paths(event)]
    tool = compact_name(tool_name(event))
    command = extract_bash_command(event)
    if not _is_engineering_mutation(tool, paths, command):
        return _result(required=False, changed_paths=paths, tool_category=tool or "unknown")
    result = _evaluate_state_for_implementation(state, runtime=runtime)
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
    blockers.extend(_material_choice_blockers(state, ledger))
    capabilities = adapter_capabilities_for(runtime)
    degraded = []
    if not capabilities.supports_pre_tool_block:
        degraded.append(f"{runtime} lacks PreToolUse hard blocking")
    return _result(
        required=True,
        blocks=bool(blockers),
        blockers=_unique(blockers),
        ledger=ledger or {},
        degraded=degraded,
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
        phase_review_seen=bool(state.get("phase_review_results")),
        pdd_reviewed=bool(result.get("pdd_reviewed")),
        ddd_reviewed=bool(result.get("ddd_reviewed")),
        sdd_reviewed=bool(result.get("sdd_reviewed")),
        tdd_reviewed=bool(result.get("tdd_reviewed")),
        process_current_phase=str(ledger.get("current_phase") or ""),
        validation_freshness_seen=bool(ledger.get("validation_signal_present")),
        prompt_signals=[f"process_phase_{event_label.lower()}"],
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
        hook_findings={"blockers": blockers, "degraded": degraded},
    )


def render_prompt_message() -> str:
    return (
        "ChangeForge Process Phase Gate: runtime phase ledger initialized\n"
        "- Start with a PDD draft, then independent PDD review before DDD.\n"
        "- DDD, SDD, and TDD each need independent review before implementation.\n"
        "- Store only bounded summaries, digests, review IDs, and phase status in state."
    )


def render_pre_tool_message(result: dict) -> str:
    label = "BLOCKED" if result.get("blocks") else "advisory"
    lines = [f"ChangeForge Process Phase Gate: {label}"]
    lines.append("- Non-trivial engineering mutation requires reviewed PDD, DDD, SDD, and TDD evidence.")
    for blocker in (result.get("blockers") or [])[:8]:
        lines.append(f"- {blocker}")
    for degraded in result.get("degraded") or []:
        lines.append(f"- degraded enforcement: {degraded}")
    return "\n".join(lines)


def render_stop_message(result: dict) -> str:
    lines = ["ChangeForge Process Phase Gate: closure blocked"]
    lines.append("- Final handoff requires phase ledger, phase reviews, repair/re-review closure, and validation signal.")
    for blocker in (result.get("blockers") or [])[:10]:
        lines.append(f"- {blocker}")
    for degraded in result.get("degraded") or []:
        lines.append(f"- degraded enforcement: {degraded}")
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
        "pdd_reviewed": False,
        "ddd_reviewed": False,
        "sdd_reviewed": False,
        "tdd_reviewed": False,
    }
    result.update(overrides)
    return result


def _is_engineering_mutation(tool: str, paths: list[str], command: str) -> bool:
    if tool == "bash":
        if not command or READ_ONLY_COMMAND_RE.search(command):
            return False
        return bool(BASH_MUTATION_RE.search(command))
    if tool not in EDIT_TOOLS:
        return False
    if not paths:
        return True
    return any(_path_requires_process(path) for path in paths)


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


def _event_text(event: dict) -> str:
    parts: list[str] = []
    for key in ("prompt", "message", "input", "response", "last_assistant_message", "lastAssistantMessage"):
        value = event.get(key)
        if isinstance(value, str):
            parts.append(value)
    return "\n".join(parts)[:8000]


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
