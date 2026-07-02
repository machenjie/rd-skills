#!/usr/bin/env python3
"""Warn or block high-risk permission and destructive tool events."""

from __future__ import annotations

import re
import sys

from changeforge_common import (
    compact_name,
    cwd_from_event,
    detect_runtime,
    event_name,
    extract_bash_command,
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
from changeforge_executor_adapter_core import (
    snapshot_from_event_state,
    state_update_from_snapshot,
)
from changeforge_hook_policy import gate_mode, run_gate_with_policy
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
NETWORK_RE = re.compile(r"\b(curl|wget|ssh|scp|rsync|gh\s+api)\b", re.IGNORECASE)
MIGRATION_RE = re.compile(r"\b(alembic|prisma\s+migrate|sequelize\s+db:migrate)\b", re.IGNORECASE)
READ_ONLY_RE = re.compile(
    r"^\s*(ls|pwd|find|rg|grep|sed|awk|cat|head|tail|git\s+(status|diff|show|log)|python3?\s+-m\s+unittest|pytest|npm\s+test|pnpm\s+test)\b",
    re.IGNORECASE,
)
PROD_SIGNAL_RE = re.compile(r"(\bprod(uction)?\b|--namespace\s+prod\b|-n\s+prod\b)", re.IGNORECASE)
ROLLBACK_EVIDENCE_RE = re.compile(r"(\brollback\b|--atomic\b|--dry-run\b|helm\s+diff)", re.IGNORECASE)
PRETOOL_BASH_TOOLS = {"bash", "runterminalcommand", "runinterminal"}


def main() -> int:
    return run_gate_with_policy(
        "permission_policy",
        _main,
        fail_closed=_fail_closed,
        fail_open=_fail_open,
    )


def _fail_closed(exc: Exception) -> None:
    runtime = detect_runtime({})
    adapter_for(runtime).emit_permission_decision(
        "block",
        f"ChangeForge Permission Policy gate failed closed: {exc}",
    )


def _fail_open(exc: Exception) -> None:
    print(
        f"ChangeForge Hook Runtime warning: permission policy gate failed open: {exc}",
        file=sys.stderr,
    )


def _main() -> int:
    event = read_event()
    if not event:
        return 0
    runtime = detect_runtime(event)
    mode = gate_mode("permission_policy")
    if mode == "off":
        return 0
    permission_event = is_permission_request(event)
    pretool_bash_event = is_pre_tool_use(event) and compact_name(tool_name(event)) in PRETOOL_BASH_TOOLS
    if not permission_event and not pretool_bash_event:
        return 0
    command = extract_bash_command(event)
    decision, reason = _decision(command)
    risk_class = _command_risk_class(command)
    recorded_decision = "block" if pretool_bash_event and decision == "block" and mode == "block" else ("warn" if pretool_bash_event else decision)
    repo = repo_root(cwd_from_event(event))
    program = summarize_command_program(command) or "unknown"
    snapshot = snapshot_from_event_state(
        event,
        {},
        classification={
            "stage": "permission",
            "tool": tool_name(event),
            "command_program": program,
            "risk_surfaces": _surfaces(command),
        },
        gate_name="permission_policy",
        gate_mode=mode,
        gate_facts={"command_risk": risk_class, "permission_decision": recorded_decision},
    )
    snapshot_update = state_update_from_snapshot(snapshot)
    snapshot_update["command_risks"] = [f"{risk_class}:{program}"]
    snapshot_update["permission_decisions"] = [f"{recorded_decision}:{program}"]
    merge_state(
        repo,
        runtime,
        **snapshot_update,
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
        normalized_events=snapshot_update["normalized_events"],
        command_program=program,
        command_risk=risk_class,
        permission_decision=recorded_decision,
        risk_surfaces=_surfaces(command),
        permission_gate_seen=True,
        turn_stage="permission",
    )
    if pretool_bash_event and decision == "allow":
        return 0
    adapter = adapter_for(runtime)
    if (permission_event or pretool_bash_event) and decision == "block" and mode == "block":
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


def _command_risk_class(command: str) -> str:
    if not command:
        return "safe"
    if DESTRUCTIVE_RE.search(command):
        if MIGRATION_RE.search(command):
            return "migration"
        if any(token in command.casefold() for token in ("kubectl", "helm", "terraform", "docker compose")):
            return "release"
        return "destructive"
    if HELM_INSTALL_UPGRADE_RE.search(command):
        return "release"
    if MIGRATION_RE.search(command):
        return "migration"
    if DEPENDENCY_MUTATION_RE.search(command):
        return "dependency"
    if NETWORK_RE.search(command):
        return "network"
    if READ_ONLY_RE.search(command):
        return "safe"
    if command.strip():
        return "mutation"
    return "unknown"


if __name__ == "__main__":
    raise SystemExit(main())
