#!/usr/bin/env python3
"""Explicit runtime capability model for ChangeForge hook adapters."""

from __future__ import annotations

from dataclasses import dataclass, field


SUPPORTED_RUNTIMES = ("codex", "claude", "copilot", "generic")
COPILOT_UNSUPPORTED_ADVISORY_EVENTS = ("UserPromptSubmit", "PreToolUse", "SubagentStop")

EVENT_SUPPORT_FIELDS = {
    "SessionStart": "supports_session_start",
    "UserPromptSubmit": "supports_user_prompt_submit",
    "UserPromptExpansion": "supports_user_prompt_submit",
    "PreToolUse": "supports_pre_tool_use",
    "PostToolUse": "supports_post_tool_use",
    "PostToolBatch": "supports_post_tool_use",
    "Stop": "supports_stop",
    "SubagentStart": "supports_subagent_start",
    "SubagentStop": "supports_subagent_stop",
    "PermissionRequest": "supports_permission_decision",
}

CONTEXT_EVENTS_BY_RUNTIME = {
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
class AdapterCapabilities:
    runtime: str
    supports_session_start: bool
    supports_user_prompt_submit: bool
    supports_pre_tool_use: bool
    supports_post_tool_use: bool
    supports_stop: bool
    supports_subagent_start: bool
    supports_subagent_stop: bool
    supports_permission_decision: bool
    supports_blocking: bool
    supports_context_injection: bool
    supports_tool_result_inspection: bool
    default_failure_mode: str = "fail_open"
    unsupported_events: tuple[str, ...] = field(default_factory=tuple)

    def supports_event(self, event_name: str) -> bool:
        field_name = EVENT_SUPPORT_FIELDS.get(str(event_name or "").strip())
        if not field_name:
            return False
        return bool(getattr(self, field_name, False))

    def supports_context_event(self, event_name: str) -> bool:
        if not self.supports_context_injection:
            return False
        return str(event_name or "").strip() in CONTEXT_EVENTS_BY_RUNTIME.get(self.runtime, set())

    def to_dict(self) -> dict[str, object]:
        return {
            "runtime": self.runtime,
            "supports_session_start": self.supports_session_start,
            "supports_user_prompt_submit": self.supports_user_prompt_submit,
            "supports_pre_tool_use": self.supports_pre_tool_use,
            "supports_post_tool_use": self.supports_post_tool_use,
            "supports_stop": self.supports_stop,
            "supports_subagent_start": self.supports_subagent_start,
            "supports_subagent_stop": self.supports_subagent_stop,
            "supports_permission_decision": self.supports_permission_decision,
            "supports_blocking": self.supports_blocking,
            "supports_context_injection": self.supports_context_injection,
            "supports_tool_result_inspection": self.supports_tool_result_inspection,
            "default_failure_mode": self.default_failure_mode,
            "unsupported_events": list(self.unsupported_events),
        }


CAPABILITIES_BY_RUNTIME = {
    "codex": AdapterCapabilities(
        runtime="codex",
        supports_session_start=True,
        supports_user_prompt_submit=True,
        supports_pre_tool_use=True,
        supports_post_tool_use=True,
        supports_stop=True,
        supports_subagent_start=True,
        supports_subagent_stop=True,
        supports_permission_decision=True,
        supports_blocking=True,
        supports_context_injection=True,
        supports_tool_result_inspection=True,
    ),
    "claude": AdapterCapabilities(
        runtime="claude",
        supports_session_start=True,
        supports_user_prompt_submit=True,
        supports_pre_tool_use=True,
        supports_post_tool_use=True,
        supports_stop=True,
        supports_subagent_start=True,
        supports_subagent_stop=True,
        supports_permission_decision=True,
        supports_blocking=True,
        supports_context_injection=True,
        supports_tool_result_inspection=True,
    ),
    "copilot": AdapterCapabilities(
        runtime="copilot",
        supports_session_start=True,
        supports_user_prompt_submit=False,
        supports_pre_tool_use=False,
        supports_post_tool_use=True,
        supports_stop=True,
        supports_subagent_start=True,
        supports_subagent_stop=False,
        supports_permission_decision=False,
        supports_blocking=True,
        supports_context_injection=True,
        supports_tool_result_inspection=True,
        unsupported_events=COPILOT_UNSUPPORTED_ADVISORY_EVENTS,
    ),
    "generic": AdapterCapabilities(
        runtime="generic",
        supports_session_start=True,
        supports_user_prompt_submit=True,
        supports_pre_tool_use=True,
        supports_post_tool_use=True,
        supports_stop=True,
        supports_subagent_start=False,
        supports_subagent_stop=False,
        supports_permission_decision=True,
        supports_blocking=False,
        supports_context_injection=True,
        supports_tool_result_inspection=False,
    ),
}


def adapter_capabilities_for(runtime: str) -> AdapterCapabilities:
    name = str(runtime or "").strip().casefold()
    return CAPABILITIES_BY_RUNTIME.get(name, CAPABILITIES_BY_RUNTIME["generic"])


def unsupported_events_for(runtime: str) -> tuple[str, ...]:
    return adapter_capabilities_for(runtime).unsupported_events


__all__ = [
    "AdapterCapabilities",
    "CAPABILITIES_BY_RUNTIME",
    "CONTEXT_EVENTS_BY_RUNTIME",
    "COPILOT_UNSUPPORTED_ADVISORY_EVENTS",
    "SUPPORTED_RUNTIMES",
    "adapter_capabilities_for",
    "unsupported_events_for",
]
