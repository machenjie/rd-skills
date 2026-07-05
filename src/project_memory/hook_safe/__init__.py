"""Hook-safe Project Memory adapter surface."""

from __future__ import annotations

from .adapter import (
    closure_advice,
    memory_enabled,
    memory_policy_status,
    pre_edit_advice,
    sanitize_event,
    write_event,
)

__all__ = [
    "closure_advice",
    "memory_enabled",
    "memory_policy_status",
    "pre_edit_advice",
    "sanitize_event",
    "write_event",
]
