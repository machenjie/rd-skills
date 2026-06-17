#!/usr/bin/env python3
"""Preview ChangeForge risk surfaces before an edit or command runs.

PreToolUse fires before a supported tool runs, so this gives an early, advisory
heads-up when a pending edit or command touches a risk surface (auth, migration,
cache, queue, Kubernetes, Helm, or big-data). It reuses the exact matching of the
PostToolUse risk gate so the pre- and post-edit views agree.

It is advisory only: it adds developer context where the runtime supports that
output, never denies the tool call, never mutates per-turn hook state, never
writes telemetry, never reads compiled references, never calls an LLM, never
touches the network, and never writes project source. Copilot preToolUse only
consumes permission decisions or argument modifications, so the maintained
Copilot templates do not wire it and Copilot warning-only preview output is
suppressed if the script is invoked manually. It fails open. The PostToolUse risk
gate remains the authority that records findings and the closure gate checks;
this preview only nudges the agent to route before the change lands.
"""

from __future__ import annotations

from changeforge_common import (
    compact_name,
    cwd_from_event,
    debug_log,
    detect_runtime,
    emit_warning,
    event_name,
    extract_bash_command,
    extract_changed_paths,
    hook_mode,
    is_pre_tool_use,
    read_event,
    repo_root,
    tool_name,
)
from changeforge_risk_surface_gate import (
    WATCHED_TOOLS,
    _collect,
    _command_risk_is_closure_relevant,
    _merge_findings,
    _risk_findings,
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
    if not is_pre_tool_use(event):
        return 0
    tool = compact_name(tool_name(event))
    if tool not in WATCHED_TOOLS:
        return 0

    try:
        repo = repo_root(cwd_from_event(event))
        paths = extract_changed_paths(event)
        command = extract_bash_command(event)
        path_findings = _risk_findings(paths, "")
        command_findings = _risk_findings([], command)
        closure_command_findings = (
            command_findings if _command_risk_is_closure_relevant(paths, command) else []
        )
        findings = _merge_findings(path_findings + closure_command_findings)
        debug_log(
            repo,
            f"pre-tool risk preview runtime={runtime} tool={tool_name(event)} findings={findings}",
        )
        if not findings or mode == "monitor":
            return 0
        emit_warning(runtime, event_name(event) or "PreToolUse", _preview_message(findings))
        return 0
    except Exception as exc:  # noqa: BLE001 - preview must fail open
        emit_warning(
            runtime,
            event_name(event) or "PreToolUse",
            f"ChangeForge Hook Runtime warning: pre-tool risk preview failed open: {exc}",
        )
        return 0


def _preview_message(findings: list[dict[str, object]]) -> str:
    surfaces = ", ".join(str(finding["name"]) for finding in findings)
    gates = _collect(findings, "gates")
    gate_text = ", ".join(gates) if gates else "the matching ChangeForge gate"
    return (
        "ChangeForge pre-edit risk preview (advisory, does not block): this pending "
        f"change touches {surfaces}. Run change-forge-router and select {gate_text} "
        "before applying it, and emit a changeforge_route manifest. The post-edit risk "
        "gate will re-check after the change lands."
    )


if __name__ == "__main__":
    raise SystemExit(main())
