#!/usr/bin/env python3
"""Emit an engineering route-judgment reminder at session start.

This is a bootstrap reminder, not a router and not a planner. It reminds the
agent to classify engineering work before action and to bind
completion claims to validation evidence. It never selects a full route, never
reads compiled references, never calls an LLM, never touches the network, and
never writes project source. It fails open and only ever adds advisory context.

Default templates wire this bootstrap only to ordinary SessionStart.
SubagentStart is handled by the subagent review gate and returns quietly unless
an explicit review capsule or review workflow is present. This script still
accepts SubagentStart when invoked by legacy or manual hook wiring. Default
templates do not wire compact-source SessionStart to this bootstrap or to
compaction; the compaction entrypoint can still recognize that source if a
compatibility wrapper invokes it directly.
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
    "Engineering expert note (bootstrap reminder): for engineering work, make a "
    "concise route judgment before acting. Fixed entry skill: "
    "change-forge-router classifies engineering work before the task hands off "
    "to the smallest specific owner/reviewer path.\n"
    "- Use change-forge-router to classify task type, risk level, owner concern, "
    "and whether the work is code, review, debug, test, refactor, release, or "
    "skill authoring.\n"
    "- Adds or changes a function, class, file, directory, helper, service, "
    "repository, adapter, or utility => make reuse search and placement "
    "rationale explicit before accepting new structure.\n"
    "- Before editing, identify setup/test entrypoints and public API; preserve "
    "setup and test harness scripts unless the task explicitly requires changing "
    "them, and do not add external network or HOME/CODEX_HOME writes.\n"
    "- Name the validation signal before implementation and hand off with fresh "
    "validation evidence plus residual risk.\n"
    "- Back reuse, placement, security, and reliability claims with code or tests "
    "unless documentation-only.\n"
    "- User already named a narrow skill path and the scope is known => respect "
    "it; skip router reclassification only for that complete path, but still "
    "clarify requirements, inspect context, name validation evidence, map "
    "action/review ownership, repair/re-review findings, and hand off with "
    "evidence.\n"
    "- Pure question, explanation, or translation with no engineering action => "
    "no routing needed.\n"
    "When a route summary helps the next reader, keep it natural: task type, "
    "risk, owner concern, source/test context, validation focus, assumptions, "
    "and residual risk. Strong evidence comes from runtime-observed context, "
    "validation records, or replay/evaluation artifacts, not hand-authored "
    "protocol fields. Read only the references relevant to the confirmed risk, "
    "stage, or surface."
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
