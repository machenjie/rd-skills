#!/usr/bin/env python3
"""Compatibility export for the canonical runtime adapter capabilities."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from runtime_governance.adapters.base import (
        AdapterCapabilities,
        CAPABILITIES_BY_RUNTIME,
        CANONICAL_EVENTS,
        CONTEXT_EVENTS_BY_RUNTIME,
        COPILOT_UNSUPPORTED_ADVISORY_EVENTS,
        EVENT_SUPPORT_FIELDS,
        PLACEHOLDER_CAPABILITIES_BY_RUNTIME,
        PLACEHOLDER_RUNTIMES,
        SUPPORTED_RUNTIMES,
        adapter_capabilities_for,
        coverage_matrix,
        format_coverage_matrix,
        strict_adapter_capabilities_for,
        unsupported_events_for,
    )
except ModuleNotFoundError:
    _src_root = Path(__file__).resolve().parents[2]
    if str(_src_root) not in sys.path:
        sys.path.insert(0, str(_src_root))
    _runtime_package = sys.modules.get("runtime_governance")
    _runtime_source_path = str(_src_root / "runtime_governance")
    if _runtime_package is not None and hasattr(_runtime_package, "__path__"):
        _package_paths = list(getattr(_runtime_package, "__path__", []))
        if _runtime_source_path not in _package_paths:
            _runtime_package.__path__.append(_runtime_source_path)
    from runtime_governance.adapters.base import (  # type: ignore[no-redef]
        AdapterCapabilities,
        CAPABILITIES_BY_RUNTIME,
        CANONICAL_EVENTS,
        CONTEXT_EVENTS_BY_RUNTIME,
        COPILOT_UNSUPPORTED_ADVISORY_EVENTS,
        EVENT_SUPPORT_FIELDS,
        PLACEHOLDER_CAPABILITIES_BY_RUNTIME,
        PLACEHOLDER_RUNTIMES,
        SUPPORTED_RUNTIMES,
        adapter_capabilities_for,
        coverage_matrix,
        format_coverage_matrix,
        strict_adapter_capabilities_for,
        unsupported_events_for,
    )


__all__ = [
    "AdapterCapabilities",
    "CAPABILITIES_BY_RUNTIME",
    "CANONICAL_EVENTS",
    "CONTEXT_EVENTS_BY_RUNTIME",
    "COPILOT_UNSUPPORTED_ADVISORY_EVENTS",
    "EVENT_SUPPORT_FIELDS",
    "PLACEHOLDER_CAPABILITIES_BY_RUNTIME",
    "PLACEHOLDER_RUNTIMES",
    "SUPPORTED_RUNTIMES",
    "adapter_capabilities_for",
    "coverage_matrix",
    "format_coverage_matrix",
    "strict_adapter_capabilities_for",
    "unsupported_events_for",
]
