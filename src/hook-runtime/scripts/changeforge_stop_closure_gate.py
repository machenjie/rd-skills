#!/usr/bin/env python3
"""Remind agents to close ChangeForge handoff evidence before stopping."""

from __future__ import annotations

from changeforge_common import (
    clear_state,
    cwd_from_event,
    detect_runtime,
    emit_block,
    emit_warning,
    hook_mode,
    is_stop,
    load_state,
    read_event,
    repo_root,
)


CLOSURE_KEYWORDS = {
    "skills": ["skill", "ChangeForge", "router", "路由", "技能"],
    "files": ["file", "changed", "修改", "文件"],
    "validation": ["test", "verify", "validation", "验证", "测试"],
    "risk": ["risk", "residual", "风险", "未验证"],
    "next": ["next", "下一步", "后续"],
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
        if not _has_closure_surface(state):
            return 0
        if mode == "monitor":
            clear_state(repo, runtime)
            return 0
        message = _closure_message(state, _final_text(event))
        clear_state(repo, runtime)
        if mode == "block":
            emit_block(runtime, message)
            return 2
        emit_warning(runtime, message)
        return 0
    except Exception as exc:
        emit_warning(runtime, f"ChangeForge Hook Runtime warning: closure gate failed open: {exc}")
        return 0


def _has_closure_surface(state: dict) -> bool:
    return bool(
        state.get("changed_paths")
        or state.get("risk_surfaces")
        or state.get("structure_findings")
    )


def _closure_message(state: dict, final_text: str) -> str:
    missing = _missing_keyword_groups(final_text) if final_text else []
    details: list[str] = []
    if state.get("structure_findings"):
        details.append("- structure gate fired")
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

    return f"""ChangeForge Closure Gate reminder.
{detail_text}
This turn changed files or triggered risk surfaces. Before final handoff, include:
- ChangeForge skill path used
- changed files
- structure/reuse/placement rationale if structure gate fired
- validation commands and results
- residual risks and unverified items
- next actions"""


def _final_text(event: dict) -> str:
    for key in (
        "final_response",
        "finalResponse",
        "assistant_response",
        "assistantResponse",
        "response",
        "message",
        "output",
    ):
        value = event.get(key)
        if isinstance(value, str):
            return value
    return ""


def _missing_keyword_groups(text: str) -> list[str]:
    lowered = text.casefold()
    missing: list[str] = []
    for group, keywords in CLOSURE_KEYWORDS.items():
        if not any(keyword.casefold() in lowered for keyword in keywords):
            missing.append(group)
    return missing


if __name__ == "__main__":
    raise SystemExit(main())
