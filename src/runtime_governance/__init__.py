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
    ClineAdapter,
    CodexAdapter,
    CopilotAdapter,
    OpenHandsAdapter,
    RooAdapter,
    adapter_capabilities_for,
    coverage_matrix,
    docs_capability_matrix_from_text,
    format_docs_capability_matrix,
    format_coverage_matrix,
    runtime_adapter_for,
    strict_adapter_capabilities_for,
)

__all__ = [
    "ClosureContract",
    "ClosureVerdict",
    "AdapterCapabilities",
    "AdapterEventResult",
    "BaseRuntimeAdapter",
    "ClaudeAdapter",
    "ClineAdapter",
    "CodexAdapter",
    "CopilotAdapter",
    "OpenHandsAdapter",
    "RooAdapter",
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
    "docs_capability_matrix_from_text",
    "format_docs_capability_matrix",
    "format_coverage_matrix",
    "runtime_adapter_for",
    "strict_adapter_capabilities_for",
]
