#!/usr/bin/env python3
"""Runtime output adapters for ChangeForge professional injection hooks."""

from __future__ import annotations

import json
from dataclasses import dataclass

from changeforge_adapter_capabilities import (
    AdapterCapabilities,
    CONTEXT_EVENTS_BY_RUNTIME,
    adapter_capabilities_for,
)
from changeforge_common import emit_session_context, emit_stop_reminder, emit_warning
from changeforge_gate_result import GateResult


CONTEXT_EVENTS = CONTEXT_EVENTS_BY_RUNTIME


@dataclass(frozen=True)
class RuntimeAdapter:
    """Small compatibility shim around each runtime output protocol."""

    runtime: str
    capabilities: AdapterCapabilities | None = None

    def _capabilities(self) -> AdapterCapabilities:
        return self.capabilities or adapter_capabilities_for(self.runtime)

    def supports_context_event(self, event_name: str) -> bool:
        return self._capabilities().supports_context_event(event_name)

    def supports_permission_event(self) -> bool:
        return self._capabilities().supports_permission_decision

    def supports_stop_block(self) -> bool:
        capabilities = self._capabilities()
        return capabilities.supports_stop and capabilities.supports_blocking

    def gate_result(
        self,
        gate_name: str,
        *,
        mode: str,
        confidence: str = "medium",
        severity: str = "warning",
        message: str = "",
        facts: dict | None = None,
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

    def emit_gate_result(self, event_name: str, result: GateResult) -> None:
        if not result.should_emit or not result.message:
            return
        if result.should_block:
            self.emit_permission_decision("block", result.message)
            return
        self.emit_context(event_name, result.message)

    def emit_context(self, event_name: str, text: str) -> None:
        if not self.supports_context_event(event_name):
            return
        if self.runtime == "generic":
            print(text.strip())
            return
        if event_name in {"PreToolUse", "PostToolUse"}:
            emit_warning(self.runtime, event_name, text)
            return
        emit_session_context(self.runtime, text, event_name)

    def emit_warning(self, event_name: str, text: str) -> None:
        if self.runtime == "generic":
            print(text.strip())
            return
        emit_warning(self.runtime, event_name, text)

    def emit_stop(self, text: str, *, continue_turn: bool) -> None:
        if self.runtime == "generic":
            print(text.strip())
            return
        emit_stop_reminder(self.runtime, text, continue_turn=continue_turn)

    def emit_permission_decision(self, decision: str, reason: str) -> None:
        if self.runtime == "generic":
            print(f"{decision}: {reason.strip()}")
            return
        print(json.dumps({"decision": decision, "reason": reason.strip()}, sort_keys=True))


def adapter_for(runtime: str) -> RuntimeAdapter:
    """Return a conservative adapter; unknown runtimes use plain text."""
    capabilities = adapter_capabilities_for(runtime)
    return RuntimeAdapter(capabilities.runtime, capabilities)
