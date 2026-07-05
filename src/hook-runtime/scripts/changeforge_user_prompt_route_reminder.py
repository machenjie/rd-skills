#!/usr/bin/env python3
"""Legacy concise engineering route-judgment reminder for user prompts.

This compatibility entrypoint is not wired by the default compact templates.
Codex and Claude default to `changeforge_professional_injector.py` on
UserPromptSubmit so pure questions can suppress injection through
`should_inject=false`. This legacy script remains advisory developer context
for maintenance tests and opt-in local configurations.

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
    "Engineering expert note (advisory): for engineering work, make a concise "
    "route judgment before acting. Fixed entry skill: change-forge-router "
    "classifies the request before handoff to the smallest specific owner and "
    "reviewer path:\n"
    "- task type / risk / owner concern\n"
    "- files/tests to inspect\n"
    "- validation focus\n"
    "- residual risk\n"
    "Then clarify requirements, inspect repository context before planning, name "
    "the test or validator before implementation, preserve setup/test harnesses "
    "unless explicitly changing them, avoid external network and HOME/CODEX_HOME "
    "writes, and hand off with validation freshness plus remaining risk. For "
    "material design choices, state the trigger, decision, options or rationale, "
    "validation evidence, and residual risk in normal prose. For skill/routing/"
    "eval changes, include baseline and treatment evidence. Skip this only for "
    "pure questions, explanations, or translations with no engineering action."
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
