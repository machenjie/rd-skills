"""Executor adapter protocol implementations for runtime governance."""

from .base import (
    AdapterCapabilities,
    AdapterEventResult,
    BaseRuntimeAdapter,
    adapter_capabilities_for,
    coverage_matrix,
    docs_capability_matrix_from_text,
    format_docs_capability_matrix,
    format_coverage_matrix,
    runtime_adapter_for,
    strict_adapter_capabilities_for,
)
from .claude import ClaudeAdapter
from .cline import ClineAdapter
from .codex import CodexAdapter
from .copilot import CopilotAdapter
from .openhands import OpenHandsAdapter
from .roo import RooAdapter

__all__ = [
    "AdapterCapabilities",
    "AdapterEventResult",
    "BaseRuntimeAdapter",
    "ClaudeAdapter",
    "ClineAdapter",
    "CodexAdapter",
    "CopilotAdapter",
    "OpenHandsAdapter",
    "RooAdapter",
    "adapter_capabilities_for",
    "coverage_matrix",
    "docs_capability_matrix_from_text",
    "format_docs_capability_matrix",
    "format_coverage_matrix",
    "runtime_adapter_for",
    "strict_adapter_capabilities_for",
]
