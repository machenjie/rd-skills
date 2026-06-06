#!/usr/bin/env python3
"""Remind agents to close ChangeForge handoff evidence before stopping."""

from __future__ import annotations

from changeforge_common import (
    clear_state,
    cwd_from_event,
    debug_log,
    detect_runtime,
    emit_stop_reminder,
    event_name,
    hook_mode,
    is_stop,
    load_state,
    read_event,
    repo_root,
    session_id_from_event,
    write_telemetry_event,
)


CLOSURE_KEYWORDS = {
    "skills": ["skill", "ChangeForge", "router", "路由", "技能"],
    "files": ["file", "changed", "修改", "文件"],
    "validation": ["test", "verify", "validation", "验证", "测试"],
    "risk": ["risk", "residual", "风险", "未验证"],
    "next": ["next", "下一步", "后续"],
}

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
}
CONDITIONAL_GROUP_BY_STATE = {
    "file_naming_findings": "naming",
    "reuse_findings": "reuse",
    "extension_reuse_findings": "extension_safety",
    "advanced_refactor_findings": "refactor",
    "comment_findings": "comments",
}


def main() -> int:
    event = read_event()
    if not event:
        return 0
    runtime = detect_runtime(event)
    if runtime == "unknown":
        return 0
    mode = hook_mode()
    if mode == "off":
        return 0
    if not is_stop(event):
        return 0

    try:
        repo = repo_root(cwd_from_event(event))
        state = load_state(repo)
        debug_log(
            repo,
            f"stop gate runtime={runtime} event={event_name(event)} has_surface={_has_closure_surface(state)} validation_seen={state.get('validation_seen')}",
        )
        if not _has_closure_surface(state):
            return 0
        final_text = _final_text(event)
        signals = _closure_signals(final_text, state)
        write_telemetry_event(
            repo,
            runtime=runtime,
            hook_name="stop_closure_gate",
            event_name=event_name(event),
            mode=mode,
            session_id=session_id_from_event(event),
            cwd=cwd_from_event(event),
            changed_paths=state.get("changed_paths", []),
            hook_findings=_stop_findings(state),
            suggested_skills=state.get("suggested_skills", []),
            suggested_capabilities=state.get("suggested_capabilities", []),
            suggested_gates=state.get("suggested_gates", []),
            suggested_domain_extensions=state.get("suggested_domain_extensions", []),
            risk_surfaces=state.get("risk_surfaces", []),
            route_manifest_detected=signals["route_manifest"],
            required_references_detected=signals["references"],
            validation_evidence_detected=signals["validation"],
            residual_risk_detected=signals["risk"],
        )
        if mode == "monitor":
            clear_state(repo, runtime)
            return 0
        missing = _missing_keyword_groups(final_text, state) if final_text else []
        stop_hook_active = bool(event.get("stop_hook_active") or event.get("stopHookActive"))
        should_block = mode == "block" and bool(missing) and not stop_hook_active
        message = _closure_message(state, final_text)
        if should_block:
            emit_stop_reminder(runtime, message, continue_turn=True)
        else:
            clear_state(repo, runtime)
            emit_stop_reminder(runtime, message, continue_turn=False)
        return 0
    except Exception as exc:
        emit_stop_reminder(
            runtime,
            f"ChangeForge Hook Runtime warning: closure gate failed open: {exc}",
            continue_turn=False,
        )
        return 0




def _has_closure_surface(state: dict) -> bool:
    return bool(
        state.get("changed_paths")
        or state.get("risk_surfaces")
        or state.get("structure_findings")
        or state.get("file_naming_findings")
        or state.get("reuse_findings")
        or state.get("extension_reuse_findings")
        or state.get("advanced_refactor_findings")
        or state.get("comment_findings")
    )


def _closure_signals(final_text: str, state: dict) -> dict[str, bool]:
    """Completeness flags for telemetry. This is presence detection only.

    The Stop gate does not judge semantic correctness; it records whether the
    final handoff text contains each kind of closure evidence so offline review
    can spot missing route manifests, validation, references, or residual risk.
    """
    lowered = final_text.casefold()

    def has(group: str) -> bool:
        return any(keyword.casefold() in lowered for keyword in CLOSURE_KEYWORDS[group])

    return {
        "route_manifest": "changeforge_route" in lowered,
        "validation": bool(state.get("validation_seen")) or has("validation"),
        "risk": has("risk"),
        "references": "reference" in lowered,
        "skills": has("skills"),
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
        )
    }


def _closure_message(state: dict, final_text: str) -> str:
    missing = _missing_keyword_groups(final_text, state) if final_text else []
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
    if state.get("risk_surfaces"):
        details.append(f"- risk surfaces: {', '.join(state['risk_surfaces'])}")
    if state.get("changed_paths"):
        details.append(f"- changed paths: {', '.join(state['changed_paths'])}")
    if state.get("validation_seen"):
        details.append("- validation command was observed")
    if state.get("suggested_domain_extensions"):
        details.append(
            f"- suggested domain extensions: {', '.join(state['suggested_domain_extensions'])}"
        )
    if missing:
        details.append(f"- missing closure signals: {', '.join(missing)}")
    detail_text = "\n".join(details)
    if detail_text:
        detail_text = f"\nObserved this turn:\n{detail_text}\n"
    evidence_text = _structure_evidence_block(state)

    return f"""ChangeForge Closure Gate reminder.
{detail_text}
This turn changed files or triggered risk surfaces. Before final handoff, include:
- ChangeForge skill path used
- changed files
- structure/reuse/placement rationale if structure gate fired
- validation commands and results
- residual risks and unverified items
- next actions{evidence_text}"""


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
    return ""


def _missing_keyword_groups(text: str, state: dict) -> list[str]:
    lowered = text.casefold()
    missing: list[str] = []
    for group, keywords in CLOSURE_KEYWORDS.items():
        if not any(keyword.casefold() in lowered for keyword in keywords):
            missing.append(group)
    for state_key, group in CONDITIONAL_GROUP_BY_STATE.items():
        if not state.get(state_key):
            continue
        keywords = CONDITIONAL_KEYWORDS[group]
        if not any(keyword.casefold() in lowered for keyword in keywords) and group not in missing:
            missing.append(group)
    return missing


if __name__ == "__main__":
    raise SystemExit(main())
