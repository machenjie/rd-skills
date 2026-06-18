"""Shared runtime governance facts for ChangeForge tooling."""

from .closure import ClosureContract, ClosureVerdict
from .events import EventKind, NormalizedEvent
from .evidence import EvidenceEntry, EvidenceLedger, EvidenceStrength, Freshness
from .gates import GateOutcome, GateResult
from .privacy import (
    cap_list,
    normalize_relative_path,
    redact_sensitive_value,
    sanitize_command_kind,
    validate_bounded_fact,
)
from .adapters import (
    AdapterCapabilities,
    AdapterEventResult,
    BaseRuntimeAdapter,
    ClaudeAdapter,
    CodexAdapter,
    CopilotAdapter,
    adapter_capabilities_for,
    coverage_matrix,
    format_coverage_matrix,
    strict_adapter_capabilities_for,
)

__all__ = [
    "ClosureContract",
    "ClosureVerdict",
    "AdapterCapabilities",
    "AdapterEventResult",
    "BaseRuntimeAdapter",
    "ClaudeAdapter",
    "CodexAdapter",
    "CopilotAdapter",
    "EventKind",
    "EvidenceEntry",
    "EvidenceLedger",
    "EvidenceStrength",
    "Freshness",
    "GateOutcome",
    "GateResult",
    "NormalizedEvent",
    "cap_list",
    "normalize_relative_path",
    "redact_sensitive_value",
    "sanitize_command_kind",
    "validate_bounded_fact",
    "adapter_capabilities_for",
    "coverage_matrix",
    "format_coverage_matrix",
    "strict_adapter_capabilities_for",
]
