#!/usr/bin/env python3
"""Unified Executor Adapter Core helpers for ChangeForge hook runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from changeforge_adapter_capabilities import AdapterCapabilities, runtime_adapter_for
from changeforge_closure_contract import ClosureContract
from changeforge_evidence_ledger import EvidenceLedger
from changeforge_gate_result import GateResult
from changeforge_lifecycle_state import LifecycleState
from changeforge_normalized_event import NormalizedEvent


@dataclass(frozen=True)
class ExecutorAdapterSnapshot:
    capabilities: AdapterCapabilities
    normalized_event: NormalizedEvent
    lifecycle_state: LifecycleState
    evidence_ledger: EvidenceLedger
    gate_result: GateResult
    closure_contract: ClosureContract | None = None

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "adapter_capabilities": self.capabilities.to_dict(),
            "normalized_event": self.normalized_event.to_dict(),
            "lifecycle_state": self.lifecycle_state.to_dict(),
            "evidence_ledger": self.evidence_ledger.to_dict(),
            "gate_result": self.gate_result.to_dict(),
        }
        if self.closure_contract is not None:
            data["closure_contract"] = self.closure_contract.to_dict()
        return data


def snapshot_from_event_state(
    event: dict[str, Any],
    state: dict | None = None,
    *,
    classification: dict[str, Any] | None = None,
    read_evidence: dict[str, list[str]] | None = None,
    gate_name: str = "executor_adapter",
    gate_mode: str = "monitor",
    gate_facts: dict[str, Any] | None = None,
    closure_contract: ClosureContract | None = None,
) -> ExecutorAdapterSnapshot:
    normalized = NormalizedEvent.from_event(
        event,
        classification=classification,
        read_evidence=read_evidence,
    )
    lifecycle = LifecycleState.from_state(state)
    capabilities = runtime_adapter_for(normalized.runtime).capabilities
    degraded = _degraded_capabilities(capabilities, normalized)
    facts = dict(gate_facts or {})
    if degraded:
        facts.setdefault("degraded_capabilities", degraded)
    return ExecutorAdapterSnapshot(
        capabilities=capabilities,
        normalized_event=normalized,
        lifecycle_state=lifecycle,
        evidence_ledger=EvidenceLedger.from_state(state, normalized_event=normalized),
        gate_result=gate_result(
            gate_name,
            mode=gate_mode,
            confidence="medium",
            severity="warning" if degraded else "info",
            facts=facts,
            residual_risk="; ".join(degraded),
        ),
        closure_contract=closure_contract,
    )


def state_update_from_snapshot(snapshot: ExecutorAdapterSnapshot) -> dict[str, Any]:
    """Return bounded reducer fields derived from one adapter snapshot."""
    event = snapshot.normalized_event
    capabilities = snapshot.capabilities
    degraded = _degraded_capabilities(capabilities, event)
    runtime_adapter = {
        "adapter": capabilities.runtime,
        "supported_checks": list(capabilities.supported_checks),
        "unsupported_checks": list(capabilities.unsupported_checks),
        "degraded_capabilities": degraded,
    }
    validation_results = _validation_results(event)
    return {
        "runtime_adapter": runtime_adapter,
        "normalized_events": [_event_summary(event)],
        "changed_paths": list(event.changed_paths),
        "deleted_paths": list(event.deleted_paths),
        "generated_paths": list(event.generated_paths),
        "read_paths": list(event.read_paths),
        "searched_patterns": list(event.searched_patterns),
        "external_file_changes": _external_file_changes(event),
        "config_changes": _config_changes(event),
        "validation_results": validation_results,
        "command_risks": _command_risks(event),
        "permission_decisions": _permission_decisions(event),
        "rollback_points": _rollback_points(event),
        "validation_command_seen": bool(event.validation_candidate) or None,
        "validation_freshness_seen": any("current" in item for item in validation_results)
        or None,
    }


def gate_result(
    gate_name: str,
    *,
    mode: str,
    confidence: str = "medium",
    severity: str = "warning",
    message: str = "",
    facts: dict[str, Any] | None = None,
    residual_risk: str = "",
) -> GateResult:
    return GateResult.from_policy(
        gate_name,
        mode=mode,
        confidence=confidence,
        severity=severity,
        message=message,
        facts=facts,
        residual_risk=residual_risk,
    )


def _degraded_capabilities(
    capabilities: AdapterCapabilities, event: NormalizedEvent
) -> list[str]:
    values = [str(item) for item in getattr(event, "capability_degradation", [])]
    values.extend(
        f"{capabilities.runtime}:{check}:unsupported"
        for check in getattr(capabilities, "unsupported_checks", ())
    )
    return _unique(values)


def _event_summary(event: NormalizedEvent) -> str:
    parts = [
        f"event={event.event_name or 'unknown'}",
        f"stage={event.stage or 'unknown'}",
    ]
    if event.tool_category or event.tool_name:
        parts.append(f"tool={event.tool_category or event.tool_name}")
    if event.command_risk:
        parts.append(f"risk={event.command_risk}")
    path_count = len(event.bounded_paths or event.changed_paths or event.read_paths)
    if path_count:
        parts.append(f"paths={path_count}")
    return ";".join(parts)


def _validation_results(event: NormalizedEvent) -> list[str]:
    if not event.validation_candidate and not event.validation_outcome:
        return []
    outcome = event.validation_outcome or "unknown"
    freshness = event.validation_freshness or "unknown"
    program = event.command_program or "unknown"
    return [f"{outcome}:{freshness}:{program}"]


def _command_risks(event: NormalizedEvent) -> list[str]:
    if not event.command_risk:
        return []
    program = event.command_program or event.tool_category or event.tool_name or "unknown"
    return [f"{event.command_risk}:{program}"]


def _permission_decisions(event: NormalizedEvent) -> list[str]:
    if not event.permission_decision:
        return []
    program = event.command_program or event.tool_category or event.tool_name or "unknown"
    return [f"{event.permission_decision}:{program}"]


def _rollback_points(event: NormalizedEvent) -> list[str]:
    values: list[str] = []
    if event.checkpoint_id:
        values.append(f"checkpoint:{event.checkpoint_id}")
    if event.rollback_available:
        values.append("rollback_available:true")
    return values


def _external_file_changes(event: NormalizedEvent) -> list[str]:
    return list(event.bounded_paths) if event.event_name == "FileChanged" else []


def _config_changes(event: NormalizedEvent) -> list[str]:
    return list(event.bounded_paths) if event.event_name == "ConfigChanged" else []


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value).strip()[:300]
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


__all__ = [
    "AdapterCapabilities",
    "ClosureContract",
    "ExecutorAdapterSnapshot",
    "EvidenceLedger",
    "GateResult",
    "LifecycleState",
    "NormalizedEvent",
    "gate_result",
    "snapshot_from_event_state",
    "state_update_from_snapshot",
]
