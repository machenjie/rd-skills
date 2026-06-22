#!/usr/bin/env python3
"""Emit a ChangeForge route-preflight reminder at session or subagent start.

This is a bootstrap reminder, not a router and not a planner. It reminds the
agent to run a ChangeForge route preflight before engineering work and to bind
completion claims to validation evidence. It never selects a full route, never
reads compiled references, never calls an LLM, never touches the network, and
never writes project source. It fails open and only ever adds advisory context.

It is wired to SessionStart (including the post-compaction ``compact`` source)
and to SubagentStart, so a spawned subagent inherits the same route-preflight
discipline as the parent session.
"""

from __future__ import annotations

from pathlib import Path

from changeforge_common import (
    cwd_from_event,
    debug_log,
    detect_runtime,
    emit_session_context,
    event_name,
    hook_mode,
    is_session_start,
    is_subagent_start,
    read_event,
    repo_root,
)


COPILOT_SKILL_SUMMARY = Path(__file__).with_name("changeforge_copilot_skill_summary.md")

PREFLIGHT_MESSAGE = (
    "ChangeForge route preflight (bootstrap reminder, not a route): classify the "
    "change first, then load the minimum sufficient skill path.\n"
    "- Possible engineering change (code, review, debug, test, refactor, release, "
    "or skill authoring) => run change-forge-router preflight before acting; do "
    "not skip routing.\n"
    "- Adds or changes a function, class, file, directory, helper, service, "
    "repository, adapter, or utility => require implementation-structure-design "
    "(reuse search and placement rationale) before new structure is accepted.\n"
    "- Before editing, identify setup/test entrypoints and public API; preserve "
    "setup and test harness scripts unless the task explicitly requires changing "
    "them, and do not add external network or HOME/CODEX_HOME writes.\n"
    "- Professional evidence cannot be prose-only: back reuse, placement, "
    "security, and reliability claims with code or tests unless documentation-only.\n"
    "- A completion claim is coming => bind it to agent-execution-discipline: no "
    "completion claim without fresh validation evidence and residual risk.\n"
    "- User already named a narrow skill path and the scope is known => respect "
    "it; do not re-route, but still run requirement clarification, "
    "read-before-plan, TDD/validation signal, action/review mapping, "
    "repair/re-review, and evidence handoff through that skill path.\n"
    "- Pure question, explanation, or translation with no engineering action => "
    "no routing needed.\n"
    "When you route an engineering change, emit a changeforge_route manifest "
    "(selected_skills, selected_capabilities, required_references, "
    "required_quality_gates) and restate it at handoff; a route described only in "
    "prose is not closure evidence.\n"
    "Confirmed risk, stage, or surface signal selects the path; load only the "
    "selected references, never every reference."
)


def _context_message(runtime: str, target_event: str) -> str:
    if runtime != "copilot" or target_event not in {"SessionStart", "SubagentStart"}:
        return PREFLIGHT_MESSAGE
    try:
        summary = COPILOT_SKILL_SUMMARY.read_text(encoding="utf-8").strip()
    except OSError:
        return PREFLIGHT_MESSAGE
    if not summary:
        return PREFLIGHT_MESSAGE
    return f"{PREFLIGHT_MESSAGE}\n\n{summary}"


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
    is_session = is_session_start(event)
    is_subagent = is_subagent_start(event)
    if not (is_session or is_subagent):
        return 0

    repo = None
    try:
        repo = repo_root(cwd_from_event(event))
        debug_log(repo, f"session bootstrap runtime={runtime} mode={mode} event={event_name(event)}")
        if mode == "monitor":
            return 0
        target_event = "SubagentStart" if is_subagent else "SessionStart"
        emit_session_context(runtime, _context_message(runtime, target_event), event_name=target_event)
    except Exception as exc:  # noqa: BLE001 - bootstrap must fail open
        if repo is not None:
            debug_log(repo, f"session bootstrap failed open: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
