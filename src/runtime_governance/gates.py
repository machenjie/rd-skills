"""Gate result primitives for runtime governance."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping

from .events import EventKind, NormalizedEvent
from .privacy import cap_list, redact_sensitive_value
from .serialization import json_dumps, json_loads, to_json_dict


class GateOutcome(str, Enum):
    PASS = "pass"
    WARN = "warn"
    BLOCK = "block"
    FAIL_OPEN = "fail_open"
    DEGRADED = "degraded"


@dataclass
class GateResult:
    gate_name: str
    outcome: str
    severity: str = "info"
    reason: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    residual_risk: list[str] = field(default_factory=list)

    @classmethod
    def pass_result(cls, gate_name: str, *, evidence_refs: Iterable[object] = ()) -> "GateResult":
        return cls(
            gate_name=redact_sensitive_value(gate_name),
            outcome=GateOutcome.PASS.value,
            severity="info",
            evidence_refs=cap_list(evidence_refs),
        )

    @classmethod
    def warn(
        cls,
        gate_name: str,
        reason: str,
        *,
        evidence_refs: Iterable[object] = (),
        residual_risk: Iterable[object] = (),
    ) -> "GateResult":
        return cls(
            gate_name=redact_sensitive_value(gate_name),
            outcome=GateOutcome.WARN.value,
            severity="warning",
            reason=redact_sensitive_value(reason),
            evidence_refs=cap_list(evidence_refs),
            residual_risk=cap_list(residual_risk),
        )

    @classmethod
    def fail_open(
        cls,
        gate_name: str,
        reason: str,
        *,
        evidence_refs: Iterable[object] = (),
        residual_risk: Iterable[object] = (),
    ) -> "GateResult":
        return cls(
            gate_name=redact_sensitive_value(gate_name),
            outcome=GateOutcome.FAIL_OPEN.value,
            severity="warning",
            reason=redact_sensitive_value(reason),
            evidence_refs=cap_list(evidence_refs),
            residual_risk=cap_list(["advisory gate failed open", *list(residual_risk)]),
        )

    @classmethod
    def degraded(
        cls,
        gate_name: str,
        reason: str,
        *,
        evidence_refs: Iterable[object] = (),
        residual_risk: Iterable[object] = (),
    ) -> "GateResult":
        return cls(
            gate_name=redact_sensitive_value(gate_name),
            outcome=GateOutcome.DEGRADED.value,
            severity="warning",
            reason=redact_sensitive_value(reason),
            evidence_refs=cap_list(evidence_refs),
            residual_risk=cap_list(residual_risk),
        )

    @classmethod
    def block(
        cls,
        gate_name: str,
        reason: str,
        *,
        explicit: bool,
        high_confidence: bool,
        evidence_refs: Iterable[object] = (),
        residual_risk: Iterable[object] = (),
    ) -> "GateResult":
        if not explicit or not high_confidence:
            return cls.warn(
                gate_name,
                "block requested without explicit high-confidence gate configuration",
                evidence_refs=evidence_refs,
                residual_risk=residual_risk,
            )
        return cls(
            gate_name=redact_sensitive_value(gate_name),
            outcome=GateOutcome.BLOCK.value,
            severity="error",
            reason=redact_sensitive_value(reason),
            evidence_refs=cap_list(evidence_refs),
            residual_risk=cap_list(residual_risk),
        )

    @classmethod
    def from_event_support(
        cls,
        gate_name: str,
        event: NormalizedEvent,
        *,
        supported_events: Iterable[str],
    ) -> "GateResult":
        supported = {str(item) for item in supported_events}
        if event.event_kind not in supported or event.event_kind == EventKind.UNKNOWN.value:
            return cls.degraded(
                gate_name,
                f"unsupported runtime event: {event.event_kind}",
                evidence_refs=[event.event_id],
                residual_risk=["runtime adapter did not provide full event support"],
            )
        return cls.pass_result(gate_name, evidence_refs=[event.event_id])

    def to_json_dict(self) -> dict[str, Any]:
        return to_json_dict(self)

    def to_json(self) -> str:
        return json_dumps(self)

    @classmethod
    def from_json_dict(cls, data: Mapping[str, Any]) -> "GateResult":
        return cls(
            gate_name=redact_sensitive_value(data.get("gate_name")),
            outcome=_outcome(data.get("outcome")),
            severity=redact_sensitive_value(data.get("severity")) or "info",
            reason=redact_sensitive_value(data.get("reason")),
            evidence_refs=cap_list(data.get("evidence_refs") or []),
            residual_risk=cap_list(data.get("residual_risk") or []),
        )

    @classmethod
    def from_json(cls, text: str) -> "GateResult":
        return cls.from_json_dict(json_loads(text))


def _outcome(value: object) -> str:
    text = str(value or "").strip()
    allowed = {item.value for item in GateOutcome}
    return text if text in allowed else GateOutcome.DEGRADED.value
