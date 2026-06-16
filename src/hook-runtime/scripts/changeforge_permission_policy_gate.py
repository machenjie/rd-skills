#!/usr/bin/env python3
"""Warn or block high-risk permission and destructive tool events."""

from __future__ import annotations

import re

from changeforge_common import (
    compact_name,
    cwd_from_event,
    detect_runtime,
    event_name,
    extract_bash_command,
    hook_mode,
    is_permission_request,
    is_pre_tool_use,
    merge_state,
    read_event,
    repo_root,
    session_id_from_event,
    summarize_command_program,
    tool_name,
    write_telemetry_event,
)
from changeforge_runtime_adapters import adapter_for


DESTRUCTIVE_RE = re.compile(
    r"\b(rm\s+-rf|git\s+reset\s+--hard|git\s+clean\s+-fd|git\s+push\s+--force|"
    r"kubectl\s+(delete|apply|patch)|helm\s+(uninstall|rollback)|"
    r"terraform\s+(apply|destroy)|alembic\s+(upgrade|downgrade)|"
    r"prisma\s+migrate|docker\s+compose\s+down|redis-cli\s+flush(all|db)|"
    r"kafka-topics.*--delete)\b",
    re.IGNORECASE,
)
SENSITIVE_RE = re.compile(
    r"\b(env|printenv|cat\s+.*(\.env|id_rsa|credentials|token)|chmod\s+-R|chown\s+-R)\b",
    re.IGNORECASE,
)
HELM_INSTALL_UPGRADE_RE = re.compile(r"\bhelm\s+(install|upgrade)\b", re.IGNORECASE)
DEPENDENCY_MUTATION_RE = re.compile(
    r"\b(npm\s+(install|uninstall|update)|pnpm\s+(add|remove|update|install)|"
    r"yarn\s+(add|remove|upgrade|install)|pip\s+(install|uninstall))\b",
    re.IGNORECASE,
)
PROD_SIGNAL_RE = re.compile(r"(\bprod(uction)?\b|--namespace\s+prod\b|-n\s+prod\b)", re.IGNORECASE)
ROLLBACK_EVIDENCE_RE = re.compile(r"(\brollback\b|--atomic\b|--dry-run\b|helm\s+diff)", re.IGNORECASE)
PRETOOL_BASH_TOOLS = {"bash", "runterminalcommand", "runinterminal"}


def main() -> int:
    event = read_event()
    if not event:
        return 0
    runtime = detect_runtime(event)
    mode = hook_mode()
    if mode == "off":
        return 0
    permission_event = is_permission_request(event)
    pretool_bash_event = is_pre_tool_use(event) and compact_name(tool_name(event)) in PRETOOL_BASH_TOOLS
    if not permission_event and not pretool_bash_event:
        return 0
    command = extract_bash_command(event)
    decision, reason = _decision(command)
    if pretool_bash_event and decision == "allow":
        return 0
    recorded_decision = "warn" if pretool_bash_event else decision
    repo = repo_root(cwd_from_event(event))
    merge_state(
        repo,
        runtime,
        permission_decisions=[f"{recorded_decision}:{summarize_command_program(command)}"],
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
        command_program=summarize_command_program(command),
        risk_surfaces=_surfaces(command),
        permission_gate_seen=True,
        turn_stage="permission",
    )
    adapter = adapter_for(runtime)
    if permission_event and decision == "block" and mode == "block":
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
    if HELM_INSTALL_UPGRADE_RE.search(command):
        if PROD_SIGNAL_RE.search(command) and not ROLLBACK_EVIDENCE_RE.search(command):
            return (
                "block",
                "ChangeForge Permission Policy Gate: production Helm install/upgrade requires rendered diff, rollback scope, owner, and validation evidence before approval.",
            )
        return (
            "warn",
            "ChangeForge Permission Policy Gate: Helm install/upgrade is release-sensitive; include mode, namespace, rendered diff, rollback scope, and validation evidence.",
        )
    if DEPENDENCY_MUTATION_RE.search(command):
        return (
            "warn",
            "ChangeForge Permission Policy Gate: dependency mutation requires dependency review, validation evidence, and rollback or lockfile rationale.",
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
    if any(token in lowered for token in ("kubectl", "helm", "terraform", "docker compose")):
        surfaces.append("delivery")
    if any(token in lowered for token in ("alembic", "prisma migrate")):
        surfaces.append("data_api_contract")
    if DEPENDENCY_MUTATION_RE.search(command):
        surfaces.append("dependency")
    if any(token in lowered for token in ("env", "credential", "token", "secret", "chmod", "chown")):
        surfaces.append("security")
    return surfaces or ["permission"]


if __name__ == "__main__":
    raise SystemExit(main())
