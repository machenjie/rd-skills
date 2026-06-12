#!/usr/bin/env python3
"""Emit a concise ChangeForge route reminder when a user prompt is submitted.

UserPromptSubmit fires once per new prompt, so this is the per-task nudge that
keeps route-manifest discipline visible across a long session, not only at
session start. It is advisory developer context, not a router: it never selects
a route, never blocks the prompt, never reads the prompt content for storage,
never reads compiled references, never calls an LLM, never touches the network,
and never writes project source. It fails open.

Privacy: the prompt text is never read, recorded, logged, or echoed. The hook
emits a fixed reminder regardless of prompt content, so no telemetry is written.
"""

from __future__ import annotations

from changeforge_common import (
    cwd_from_event,
    debug_log,
    detect_runtime,
    emit_session_context,
    hook_mode,
    is_user_prompt_submit,
    read_event,
    repo_root,
)


ROUTE_REMINDER = (
    "ChangeForge route reminder (advisory, not a route): if this prompt is an "
    "engineering change (code, review, debug, test, refactor, release, or skill "
    "authoring), run change-forge-router before acting and emit a changeforge_route "
    "manifest naming selected_skills, selected_capabilities, required_references, and "
    "required_quality_gates; restate it at handoff. A route described only in prose is "
    "not closure evidence. Skip routing only for a pure question, explanation, or "
    "translation with no engineering action."
)


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
    if not is_user_prompt_submit(event):
        return 0

    repo = None
    try:
        repo = repo_root(cwd_from_event(event))
        debug_log(repo, f"user prompt route reminder runtime={runtime} mode={mode}")
        if mode == "monitor":
            return 0
        emit_session_context(runtime, ROUTE_REMINDER, event_name="UserPromptSubmit")
    except Exception as exc:  # noqa: BLE001 - reminder must fail open
        if repo is not None:
            debug_log(repo, f"user prompt route reminder failed open: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
