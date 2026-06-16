#!/usr/bin/env python3
"""Remind a stopping subagent to hand off ChangeForge closure evidence.

SubagentStop fires when a subagent finishes. This emits a concise, advisory
reminder that the subagent's handoff to the parent should carry the same closure
discipline the parent Stop gate enforces: the route manifest, validation
evidence, and residual risk.

It is advisory only. It never returns ``decision: block`` (which would force the
subagent to keep running) and never ``continue: false``. Copilot SubagentStop
only consumes decision output, so the maintained Copilot templates do not wire
it and Copilot warning-only output is suppressed if the script is invoked
manually. It deliberately does not load, mutate, or clear the per-turn hook
state, because that state belongs to the parent turn and the parent Stop closure
gate still needs it. It writes no telemetry, reads no references, makes no
network call, and never writes project source. It fails open.
"""

from __future__ import annotations

from changeforge_common import (
    cwd_from_event,
    debug_log,
    detect_runtime,
    emit_subagent_stop_reminder,
    hook_mode,
    is_subagent_stop,
    read_event,
    repo_root,
)


SUBAGENT_CLOSURE_REMINDER = (
    "ChangeForge subagent closure reminder (advisory): when this subagent hands "
    "results back, carry the closure evidence the parent turn needs — the "
    "changeforge_route manifest for any routed change, the validation commands and "
    "outcomes actually run (or an honest not-verified disclosure), and the residual "
    "risk. Do not report completion without fresh validation evidence."
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
    if not is_subagent_stop(event):
        return 0

    repo = None
    try:
        repo = repo_root(cwd_from_event(event))
        debug_log(repo, f"subagent stop reminder runtime={runtime} mode={mode}")
        if mode == "monitor":
            return 0
        emit_subagent_stop_reminder(runtime, SUBAGENT_CLOSURE_REMINDER)
    except Exception as exc:  # noqa: BLE001 - reminder must fail open
        if repo is not None:
            debug_log(repo, f"subagent stop reminder failed open: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
