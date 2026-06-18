"""Codex executor adapter."""

from __future__ import annotations

from .base import BaseRuntimeAdapter, adapter_capabilities_for


class CodexAdapter(BaseRuntimeAdapter):
    """Normalize Codex hook payloads into governance facts."""

    def __init__(self) -> None:
        super().__init__(adapter_capabilities_for("codex"))


__all__ = ["CodexAdapter"]
