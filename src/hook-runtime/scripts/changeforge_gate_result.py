#!/usr/bin/env python3
"""Unified gate result object for ChangeForge hook gates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


VALID_MODES = {"off", "monitor", "warn", "block"}
VALID_SEVERITIES = {"info", "warning", "error"}
VALID_CONFIDENCE = {"low", "medium", "high"}


@dataclass(frozen=True)
class GateResult:
    gate_name: str
    mode: str = "warn"
    severity: str = "warning"
    confidence: str = "medium"
    should_emit: bool = True
    should_block: bool = False
    message: str = ""
    facts: dict[str, Any] = field(default_factory=dict)
    residual_risk: str = ""

    @classmethod
    def from_policy(
        cls,
        gate_name: str,
        *,
        mode: str,
        confidence: str = "medium",
        severity: str = "warning",
        message: str = "",
        facts: dict[str, Any] | None = None,
        residual_risk: str = "",
    ) -> "GateResult":
        normalized_mode = mode if mode in VALID_MODES else "warn"
        normalized_confidence = confidence if confidence in VALID_CONFIDENCE else "medium"
        normalized_severity = severity if severity in VALID_SEVERITIES else "warning"
        should_emit = normalized_mode in {"warn", "block"}
        should_block = normalized_mode == "block" and normalized_confidence == "high"
        return cls(
            gate_name=str(gate_name or "").strip(),
            mode=normalized_mode,
            severity=normalized_severity,
            confidence=normalized_confidence,
            should_emit=should_emit,
            should_block=should_block,
            message=str(message or "").strip(),
            facts=facts if isinstance(facts, dict) else {},
            residual_risk=str(residual_risk or "").strip(),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "gate_name": self.gate_name,
            "mode": self.mode,
            "severity": self.severity,
            "confidence": self.confidence,
            "should_emit": self.should_emit,
            "should_block": self.should_block,
            "message": self.message,
            "facts": dict(self.facts),
            "residual_risk": self.residual_risk,
        }


__all__ = ["GateResult"]
