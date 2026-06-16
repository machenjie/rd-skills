#!/usr/bin/env python3
"""Warn or block high-risk permission and destructive tool events."""

from __future__ import annotations

import re

from changeforge_common import (
    cwd_from_event,
    detect_runtime,
    event_name,
    extract_bash_command,
    hook_mode,
    is_permission_request,
    merge_state,
    read_event,
    repo_root,
    session_id_from_event,
    tool_name,
    write_telemetry_event,
)
from changeforge_runtime_adapters import adapter_for


DESTRUCTIVE_RE = re.compile(
    r"\b(rm\s+-rf|git\s+reset\s+--hard|git\s+clean\s+-fd|git\s+push\s+--force|"
    r"kubectl\s+delete|helm\s+(uninstall|upgrade|install)|terraform\s+(apply|destroy)|"
    r"redis-cli\s+flush(all|db)|kafka-topics.*--delete)\b",
    re.IGNORECASE,
)
SENSITIVE_RE = re.compile(
    r"\b(env|printenv|cat\s+.*(\.env|id_rsa|credentials|token)|chmod\s+-R|chown\s+-R)\b",
    re.IGNORECASE,
)


def main() -> int:
    event = read_event()
    if not event or not is_permission_request(event):
        return 0
    runtime = detect_runtime(event)
    mode = hook_mode()
    if mode == "off":
        return 0
    command = extract_bash_command(event)
    decision, reason = _decision(command)
    repo = repo_root(cwd_from_event(event))
    merge_state(
        repo,
        runtime,
        permission_decisions=[f"{decision}:{_program(command)}"],
        risk_surfaces=_surfaces(command),
        turn_stage="permission",
        permission_gate_seen=True,
        suggested_skills=["security-privacy-gate", "delivery-release-gate"],
        suggested_gates=["security-privacy-gate", "delivery-release-gate"],
    )
    write_telemetry_event(
        repo,
        runtime=runtime,
        hook_name="permission_policy_gate",
        event_name=event_name(event),
        mode=mode,
        session_id=session_id_from_event(event),
        cwd=cwd_from_event(event),
        tool_name=tool_name(event),
        command_program=_program(command),
        risk_surfaces=_surfaces(command),
        permission_gate_seen=True,
        turn_stage="permission",
    )
    adapter = adapter_for(runtime)
    if decision == "block" and mode == "block":
        adapter.emit_permission_decision("block", reason)
    elif mode != "monitor":
        adapter.emit_warning(event_name(event) or "PermissionRequest", reason)
    return 0


def _decision(command: str) -> tuple[str, str]:
    if not command:
        return (
            "allow",
            "ChangeForge Permission Policy Gate: no command payload detected; continue with normal runtime review.",
        )
    if DESTRUCTIVE_RE.search(command):
        return (
            "block",
            "ChangeForge Permission Policy Gate: destructive or release-sensitive command requires explicit rollback, owner, and validation evidence before approval.",
        )
    if SENSITIVE_RE.search(command):
        return (
            "warn",
            "ChangeForge Permission Policy Gate: sensitive filesystem or credential-adjacent command; do not expose secrets and state validation/rollback evidence.",
        )
    return ("allow", "ChangeForge Permission Policy Gate: no high-risk permission pattern detected.")


def _surfaces(command: str) -> list[str]:
    surfaces: list[str] = []
    lowered = command.casefold()
    if any(token in lowered for token in ("kubectl", "helm", "terraform")):
        surfaces.append("delivery")
    if any(token in lowered for token in ("env", "credential", "token", "secret", "chmod", "chown")):
        surfaces.append("security")
    return surfaces or ["permission"]


def _program(command: str) -> str:
    return command.strip().split()[0][:40] if command.strip() else ""


if __name__ == "__main__":
    raise SystemExit(main())
