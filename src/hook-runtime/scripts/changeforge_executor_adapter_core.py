#!/usr/bin/env python3
"""Unified Executor Adapter Core helpers for ChangeForge hook runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from changeforge_adapter_capabilities import AdapterCapabilities, adapter_capabilities_for
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

    def to_dict(self) -> dict[str, object]:
        return {
            "adapter_capabilities": self.capabilities.to_dict(),
            "normalized_event": self.normalized_event.to_dict(),
            "lifecycle_state": self.lifecycle_state.to_dict(),
            "evidence_ledger": self.evidence_ledger.to_dict(),
        }


def snapshot_from_event_state(
    event: dict[str, Any],
    state: dict | None = None,
    *,
    classification: dict[str, Any] | None = None,
    read_evidence: dict[str, list[str]] | None = None,
) -> ExecutorAdapterSnapshot:
    normalized = NormalizedEvent.from_event(
        event,
        classification=classification,
        read_evidence=read_evidence,
    )
    lifecycle = LifecycleState.from_state(state)
    return ExecutorAdapterSnapshot(
        capabilities=adapter_capabilities_for(normalized.runtime),
        normalized_event=normalized,
        lifecycle_state=lifecycle,
        evidence_ledger=EvidenceLedger.from_state(state, normalized_event=normalized),
    )


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


__all__ = [
    "ClosureContract",
    "ExecutorAdapterSnapshot",
    "EvidenceLedger",
    "GateResult",
    "LifecycleState",
    "NormalizedEvent",
    "adapter_capabilities_for",
    "gate_result",
    "snapshot_from_event_state",
]
