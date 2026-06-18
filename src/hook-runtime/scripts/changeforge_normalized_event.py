#!/usr/bin/env python3
"""Normalized hook event object for ChangeForge executor adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from changeforge_common import (
    detect_runtime,
    event_name,
    extract_bash_command,
    extract_changed_paths,
    normalize_path,
    summarize_command_program,
    tool_name,
)


EVENT_NAME_MAP = {
    "sessionstart": "SessionStart",
    "userpromptsubmit": "UserPromptSubmit",
    "userpromptexpansion": "UserPromptSubmit",
    "pretooluse": "PreToolUse",
    "posttooluse": "PostToolUse",
    "posttoolbatch": "PostToolUse",
    "stop": "Stop",
    "subagentstart": "SubagentStart",
    "subagentstop": "SubagentStop",
    "permissionrequest": "PermissionRequest",
}


@dataclass(frozen=True)
class NormalizedEvent:
    runtime: str = "unknown"
    event_name: str = "unknown"
    stage: str = "unknown"
    tool_name: str = ""
    command_program: str = ""
    changed_paths: list[str] = field(default_factory=list)
    read_paths: list[str] = field(default_factory=list)
    searched_patterns: list[str] = field(default_factory=list)
    product_surfaces: list[str] = field(default_factory=list)
    language_surfaces: list[str] = field(default_factory=list)
    risk_surfaces: list[str] = field(default_factory=list)
    domain_extensions: list[str] = field(default_factory=list)
    prompt_signals: list[str] = field(default_factory=list)
    should_inject: bool = False

    @classmethod
    def from_event(
        cls,
        event: dict[str, Any],
        *,
        classification: dict[str, Any] | None = None,
        read_evidence: dict[str, list[str]] | None = None,
    ) -> "NormalizedEvent":
        event = event if isinstance(event, dict) else {}
        classification = classification if isinstance(classification, dict) else {}
        read_evidence = read_evidence if isinstance(read_evidence, dict) else {}
        raw_event_name = _canonical_event_name(event_name(event))
        stage = str(classification.get("stage") or "unknown").strip() or "unknown"
        command = extract_bash_command(event)
        command_program = str(
            classification.get("command_program") or summarize_command_program(command)
        ).strip()
        tool = str(classification.get("tool") or tool_name(event)).strip()
        paths = _string_list(classification.get("paths"))
        if not paths:
            paths = [normalize_path(path) for path in extract_changed_paths(event)]
        changed_paths = paths if stage in {"edit", "repair", "refactor", "release", "skill_authoring"} else []
        read_paths = _string_list(read_evidence.get("paths"))
        if stage in {"read", "review"} and not read_paths:
            read_paths = paths
        return cls(
            runtime=_normalized_runtime(detect_runtime(event)),
            event_name=raw_event_name,
            stage=stage,
            tool_name=tool,
            command_program=command_program,
            changed_paths=_unique(changed_paths),
            read_paths=_unique(read_paths),
            searched_patterns=_unique(_string_list(read_evidence.get("patterns"))),
            product_surfaces=_unique(_string_list(classification.get("product_surfaces") or classification.get("surfaces"))),
            language_surfaces=_unique(_string_list(classification.get("language_surfaces"))),
            risk_surfaces=_unique(_string_list(classification.get("risk_surfaces"))),
            domain_extensions=_unique(_string_list(classification.get("domain_extensions"))),
            prompt_signals=_unique(_string_list(classification.get("prompt_signals"))),
            should_inject=bool(classification.get("should_inject")),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "runtime": self.runtime,
            "event_name": self.event_name,
            "stage": self.stage,
            "tool_name": self.tool_name,
            "command_program": self.command_program,
            "changed_paths": list(self.changed_paths),
            "read_paths": list(self.read_paths),
            "searched_patterns": list(self.searched_patterns),
            "product_surfaces": list(self.product_surfaces),
            "language_surfaces": list(self.language_surfaces),
            "risk_surfaces": list(self.risk_surfaces),
            "domain_extensions": list(self.domain_extensions),
            "prompt_signals": list(self.prompt_signals),
            "should_inject": self.should_inject,
        }

    def to_classifier_dict(self) -> dict[str, object]:
        paths = self.changed_paths or self.read_paths
        return {
            "stage": self.stage,
            "surfaces": list(self.product_surfaces),
            "product_surfaces": list(self.product_surfaces),
            "language_surfaces": list(self.language_surfaces),
            "risk_surfaces": list(self.risk_surfaces),
            "domain_extensions": list(self.domain_extensions),
            "prompt_signals": list(self.prompt_signals),
            "paths": list(paths),
            "tool": self.tool_name,
            "command_program": self.command_program,
            "should_inject": self.should_inject,
        }


def _canonical_event_name(name: str) -> str:
    compact = "".join(ch for ch in str(name or "").strip().casefold() if ch.isalnum())
    return EVENT_NAME_MAP.get(compact, "unknown")


def _normalized_runtime(runtime: str) -> str:
    runtime = str(runtime or "").strip().casefold()
    return runtime if runtime in {"codex", "claude", "copilot", "generic"} else "unknown"


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        item = str(value).strip()[:300]
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


__all__ = ["NormalizedEvent"]
