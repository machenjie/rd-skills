"""Claude executor adapter."""

from __future__ import annotations

from .base import BaseRuntimeAdapter, adapter_capabilities_for


class ClaudeAdapter(BaseRuntimeAdapter):
    """Normalize Claude hook payloads into governance facts."""

    def __init__(self) -> None:
        super().__init__(adapter_capabilities_for("claude"))


__all__ = ["ClaudeAdapter"]
