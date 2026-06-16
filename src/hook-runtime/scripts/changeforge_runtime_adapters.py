#!/usr/bin/env python3
"""Runtime output adapters for ChangeForge professional injection hooks."""

from __future__ import annotations

import json
from dataclasses import dataclass

from changeforge_common import emit_session_context, emit_stop_reminder, emit_warning


CONTEXT_EVENTS = {
    "codex": {
        "SessionStart",
        "UserPromptSubmit",
        "PreToolUse",
        "PostToolUse",
        "SubagentStart",
        "SubagentStop",
        "UserPromptExpansion",
        "PostToolBatch",
    },
    "claude": {
        "SessionStart",
        "UserPromptSubmit",
        "PreToolUse",
        "PostToolUse",
        "SubagentStart",
        "SubagentStop",
        "UserPromptExpansion",
        "PostToolBatch",
    },
    "copilot": {"SessionStart", "PostToolUse", "SubagentStart", "Notification"},
    "generic": {"SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse"},
}


@dataclass(frozen=True)
class RuntimeAdapter:
    """Small compatibility shim around each runtime output protocol."""

    runtime: str

    def supports_context_event(self, event_name: str) -> bool:
        return event_name in CONTEXT_EVENTS.get(self.runtime, set())

    def supports_permission_event(self) -> bool:
        return self.runtime in {"codex", "claude", "generic"}

    def supports_stop_block(self) -> bool:
        return self.runtime in {"codex", "claude", "copilot"}

    def emit_context(self, event_name: str, text: str) -> None:
        if not self.supports_context_event(event_name):
            return
        if self.runtime == "generic":
            print(text.strip())
            return
        if event_name in {"PreToolUse", "PostToolUse"}:
            emit_warning(self.runtime, event_name, text)
            return
        emit_session_context(self.runtime, text, event_name)

    def emit_warning(self, event_name: str, text: str) -> None:
        if self.runtime == "generic":
            print(text.strip())
            return
        emit_warning(self.runtime, event_name, text)

    def emit_stop(self, text: str, *, continue_turn: bool) -> None:
        if self.runtime == "generic":
            print(text.strip())
            return
        emit_stop_reminder(self.runtime, text, continue_turn=continue_turn)

    def emit_permission_decision(self, decision: str, reason: str) -> None:
        if self.runtime == "generic":
            print(f"{decision}: {reason.strip()}")
            return
        print(json.dumps({"decision": decision, "reason": reason.strip()}, sort_keys=True))


def adapter_for(runtime: str) -> RuntimeAdapter:
    """Return a conservative adapter; unknown runtimes use plain text."""
    return RuntimeAdapter(runtime if runtime in CONTEXT_EVENTS else "generic")

