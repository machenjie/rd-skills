#!/usr/bin/env python3
"""Classify hook events into ChangeForge action stages and risk surfaces."""

from __future__ import annotations

import re
from typing import Any

from changeforge_common import (
    compact_name,
    event_name,
    extract_bash_command,
    extract_changed_paths,
    normalize_path,
    tool_name,
)


READ_TOOLS = {
    "read",
    "grep",
    "glob",
    "ls",
    "list",
    "view",
    "open",
    "search",
    "fetch",
    "cat",
    "sed",
    "rg",
}
EDIT_TOOLS = {"edit", "write", "multiedit", "applypatch", "apply_patch"}
TEST_COMMAND_RE = re.compile(
    r"\b(pytest|unittest|go\s+test|cargo\s+test|npm\s+test|pnpm\s+test|"
    r"yarn\s+test|validate[-_\w./]*|eval-routing|build\.py)\b",
    re.IGNORECASE,
)
REVIEW_RE = re.compile(r"\b(review|inspect|audit|pr\s+diff|code\s+review|审查|评审)\b", re.I)
REPAIR_RE = re.compile(r"\b(fix|repair|address|resolve|remediate|修复|解决)\b", re.I)
RELEASE_RE = re.compile(r"\b(release|deploy|install|build|package|rollback|发布|部署)\b", re.I)
SCHEMA_RE = re.compile(r"\b(schema|dto|api|contract|openapi|graphql|proto|migration)\b", re.I)
SECURITY_RE = re.compile(r"\b(auth|permission|secret|token|password|credential|security)\b", re.I)


def classify_event(event: dict) -> dict[str, Any]:
    """Return stage, surfaces, and compact prompt signals for an event."""
    tool = compact_name(tool_name(event))
    hook = compact_name(event_name(event))
    command = extract_bash_command(event)
    paths = [normalize_path(path) for path in extract_changed_paths(event)]
    text = _transient_text(event, limit=1200)

    stage = _stage_from_event(tool, hook, command, text)
    surfaces = _surfaces(paths, command, text)
    prompt_signals = _prompt_signals(text)
    if stage == "read" and "context_read" not in surfaces:
        surfaces.append("context_read")
    if stage == "review" and "review" not in surfaces:
        surfaces.append("review")
    if stage == "test" and "test" not in surfaces:
        surfaces.append("test")
    return {
        "stage": stage,
        "surfaces": surfaces,
        "prompt_signals": prompt_signals,
        "paths": paths,
        "tool": tool,
        "command_program": command.strip().split()[0] if command.strip() else "",
    }


def is_read_tool(event: dict) -> bool:
    tool = compact_name(tool_name(event))
    if tool in READ_TOOLS:
        return True
    command = extract_bash_command(event).strip()
    return bool(command) and command.split()[0] in {"cat", "sed", "rg", "grep", "find", "ls"}


def extract_read_evidence(event: dict) -> dict[str, list[str]]:
    paths: list[str] = []
    patterns: list[str] = []

    def visit(value: Any, key: str = "") -> None:
        if isinstance(value, dict):
            for child_key, child_value in value.items():
                visit(child_value, str(child_key))
            return
        if isinstance(value, list):
            for item in value:
                visit(item, key)
            return
        if not isinstance(value, str):
            return
        lowered_key = key.casefold()
        if lowered_key in {"path", "filepath", "file", "glob", "pattern", "query"}:
            candidate = value.strip()
            if "/" in candidate or "." in candidate:
                paths.append(normalize_path(candidate))
            elif len(candidate) <= 120:
                patterns.append(candidate)

    visit(event)
    command = extract_bash_command(event)
    if command:
        parts = command.split()
        for part in parts[1:6]:
            if "/" in part or "." in part:
                paths.append(normalize_path(part.strip("'\"")))
    return {"paths": _unique(paths), "patterns": _unique(patterns)}


def _stage_from_event(tool: str, hook: str, command: str, text: str) -> str:
    if hook == "permissionrequest":
        return "permission"
    if "subagent" in hook:
        return "subagent"
    if "compact" in hook:
        return "compaction"
    if tool in EDIT_TOOLS:
        return "edit"
    if tool in READ_TOOLS:
        return "read"
    if command and TEST_COMMAND_RE.search(command):
        return "test"
    if REVIEW_RE.search(text):
        return "review"
    if REPAIR_RE.search(text):
        return "repair"
    if RELEASE_RE.search(text):
        return "release"
    if hook == "userpromptsubmit":
        return "planning"
    return "implementation"


def _surfaces(paths: list[str], command: str, text: str) -> list[str]:
    values: list[str] = []
    joined = "\n".join(paths) + "\n" + command + "\n" + text
    for path in paths:
        if path.startswith("src/hook-runtime/"):
            values.append("hook_runtime")
        if path.startswith("src/professional-skills/"):
            values.append("skill_authoring")
        if path.startswith("src/foundation/capabilities/"):
            values.append("capability_authoring")
        if path.startswith("scripts/") or path.startswith("installers/"):
            values.append("build_install_validation")
        if path.startswith("docs/") or path in {"AGENTS.md", "CLAUDE.md", "CONTRIBUTING.md"}:
            values.append("documentation")
    if SCHEMA_RE.search(joined):
        values.append("data_api_contract")
    if SECURITY_RE.search(joined):
        values.append("security")
    if re.search(r"\b(kubectl|helm|terraform|deploy|rollback|install)\b", joined, re.I):
        values.append("delivery")
    return _unique(values) or ["general_engineering"]


def _prompt_signals(text: str) -> list[str]:
    signals: list[str] = []
    for name, pattern in (
        ("review_intent", REVIEW_RE),
        ("repair_intent", REPAIR_RE),
        ("release_intent", RELEASE_RE),
        ("schema_or_api", SCHEMA_RE),
        ("security_or_permission", SECURITY_RE),
    ):
        if pattern.search(text):
            signals.append(name)
    return signals


def _transient_text(event: dict, *, limit: int) -> str:
    pieces: list[str] = []
    for key in (
        "prompt",
        "message",
        "userPrompt",
        "user_prompt",
        "instructions",
        "tool_input",
        "toolInput",
        "input",
    ):
        value = event.get(key)
        if isinstance(value, str):
            pieces.append(value[:limit])
        elif isinstance(value, dict):
            pieces.append(" ".join(str(v)[:200] for v in value.values() if isinstance(v, str)))
    return "\n".join(pieces)[:limit]


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        item = value.strip()[:200]
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out

