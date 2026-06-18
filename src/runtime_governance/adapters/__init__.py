"""Executor adapter protocol implementations for runtime governance."""

from .base import (
    AdapterCapabilities,
    AdapterEventResult,
    BaseRuntimeAdapter,
    adapter_capabilities_for,
    coverage_matrix,
    format_coverage_matrix,
    strict_adapter_capabilities_for,
)
from .claude import ClaudeAdapter
from .codex import CodexAdapter
from .copilot import CopilotAdapter

__all__ = [
    "AdapterCapabilities",
    "AdapterEventResult",
    "BaseRuntimeAdapter",
    "ClaudeAdapter",
    "CodexAdapter",
    "CopilotAdapter",
    "adapter_capabilities_for",
    "coverage_matrix",
    "format_coverage_matrix",
    "strict_adapter_capabilities_for",
]
