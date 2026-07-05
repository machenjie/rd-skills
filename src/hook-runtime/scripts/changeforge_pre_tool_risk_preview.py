#!/usr/bin/env python3
"""Legacy pre-tool risk preview for opt-in local configurations.

This advisory-only script is no longer wired by the default compact templates.
Default PreToolUse keeps hard-value structure, material-choice, and permission
gates, while PostToolUse records risk evidence through
`changeforge_post_tool_collector.py`.

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
    _command_has_high_tool_permission_risk,
    _command_risk_is_closure_relevant,
    _merge_findings,
    _risk_findings,
    _tool_permission_findings,
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
        tool_permission_findings = _tool_permission_findings(tool, command, paths)
        closure_command_findings = (
            command_findings if _command_risk_is_closure_relevant(paths, command) else []
        )
        findings = _merge_findings(
            path_findings + closure_command_findings + tool_permission_findings
        )
        debug_log(
            repo,
            f"pre-tool risk preview runtime={runtime} tool={tool_name(event)} findings={findings}",
        )
        if not findings or mode == "monitor":
            return 0
        emit_warning(
            runtime,
            event_name(event) or "PreToolUse",
            _preview_message(findings, tool=tool, command=command, paths=paths),
        )
        return 0
    except Exception as exc:  # noqa: BLE001 - preview must fail open
        emit_warning(
            runtime,
            event_name(event) or "PreToolUse",
            f"ChangeForge Hook Runtime warning: pre-tool risk preview failed open: {exc}",
        )
        return 0


def _preview_message(
    findings: list[dict[str, object]],
    *,
    tool: str,
    command: str,
    paths: list[str],
) -> str:
    surfaces = ", ".join(str(finding["name"]) for finding in findings)
    gates = _collect(findings, "gates")
    gate_text = ", ".join(gates) if gates else "the matching professional gate"
    capabilities = _collect(findings, "capabilities")
    capability_text = (
        f" Professional focus areas: {', '.join(capabilities)}." if capabilities else ""
    )
    sandbox = _sandbox_classification(tool=tool, command=command, paths=paths)
    return (
        "Engineering expert note:\n"
        f"This pending change touches {surfaces}. Before applying it, make the "
        "routing judgment explicit. Fixed entry skill: change-forge-router "
        "classifies the risk before the specific owner/reviewer path acts:\n"
        "- task type and risk level\n"
        "- owner skill or professional concern\n"
        "- source/test context\n"
        "- validation plan and residual risk\n"
        f"Include {gate_text} in the validation focus when relevant."
        f"{capability_text} Tool permission/sandbox: {sandbox}. Re-check the "
        "resulting diff and validation evidence after the change lands."
    )


def _sandbox_classification(tool: str, command: str, paths: list[str]) -> str:
    """Return a short permission/sandbox classification without storing content."""
    lowered_command = command.casefold()
    lowered_tool = tool.casefold()
    if lowered_command:
        if _command_has_high_tool_permission_risk(command):
            return "high-risk command; record permission state, dry-run or rollback path, and redaction rule"
        if any(
            marker in lowered_command
            for marker in (
                " rm ",
                "rm -",
                "git " + "clean",
                "git " + "reset",
                "git " + "checkout --",
                " mv ",
                "mv ",
                " chmod",
                "chmod ",
                " chown",
                "chown ",
                "kubectl apply",
                "kubectl delete",
                "helm upgrade",
                "helm rollback",
                "terraform apply",
                "terraform destroy",
                "aws ",
                "gcloud ",
                "az ",
                "psql ",
                "mysql ",
            )
        ):
            return "high-risk command; record permission state, dry-run or rollback path, and redaction rule"
        return "shell command; record whether it is read-only or state-mutating and what sandbox applies"
    if paths:
        if lowered_tool in {"apply_patch", "edit", "multiedit", "write"}:
            return "filesystem edit; record changed-path boundary and rollback/revert path"
        return "path-scoped tool action; record changed-path boundary"
    return "tool action; record permission state and sandbox boundary if it can mutate state or expose sensitive output"


if __name__ == "__main__":
    raise SystemExit(main())
