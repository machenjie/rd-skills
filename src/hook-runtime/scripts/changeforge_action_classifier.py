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
    is_compaction_event,
    normalize_path,
    summarize_command_program,
    tool_name,
)


READ_TOOLS = {
    "read",
    "readfile",
    "grep",
    "glob",
    "ls",
    "list",
    "listdirectory",
    "view",
    "open",
    "search",
    "searchcode",
    "fetch",
    "fetchfile",
    "fetchprpatch",
    "cat",
    "sed",
    "rg",
    "getprdiff",
    "mcpfilesystemreadfile",
    "mcpfilesystemlistdirectory",
    "mcpgithubgetfilecontents",
    "mcpgithubpullrequestread",
    "mcpgithubsearchcode",
}
EDIT_TOOLS = {"edit", "write", "multiedit", "applypatch", "apply_patch"}
TEST_COMMAND_RE = re.compile(
    r"\b(pytest|unittest|go\s+test|cargo\s+test|npm\s+test|pnpm\s+test|"
    r"yarn\s+test|validate[-_\w./]*|eval-routing|build\.py)\b",
    re.IGNORECASE,
)
REVIEW_EN_RE = re.compile(
    r"\b(review|inspect|audit|pr\s+diff|code\s+review|latest commit)\b",
    re.I,
)
REVIEW_ZH_RE = re.compile(r"(审查|评审|复查|仔细审查|详细审查|最新提交|修复已经提交)")
REPAIR_EN_RE = re.compile(r"\b(fix|repair|address|resolve|remediate)\b", re.I)
REPAIR_ZH_RE = re.compile(r"(修复|解决|修复已经提交|已修复提交|再审查)")
REPAIR_FOLLOWUP_RE = re.compile(r"(修复已经提交|已修复提交|再审查|latest fix|fix is submitted)", re.I)
QUESTION_INTENT_RE = re.compile(
    r"\b(explain|what(?:'s| is| are)?|how(?: to| do| does| can| should)?|why|"
    r"difference between|compare|overview|describe|tell me about)\b"
    r"|为什么|是什么|什么是|解释|区别|介绍|怎么|如何|怎样|干嘛|做什么|概念",
    re.I,
)
RELEASE_RE = re.compile(r"\b(release|deploy|deployment|install|build|package|rollback)\b|发布|部署", re.I)
READ_INTENT_RE = re.compile(r"\b(read|grep|search|find|open|look at|inspect file)\b", re.I)
READ_ZH_RE = re.compile(r"(阅读|查看|分析|理解|看看|检查代码)")
EDIT_INTENT_RE = re.compile(r"\b(add|change|modify|update|implement|write|create)\b", re.I)
EDIT_ZH_RE = re.compile(r"(修改|改动|实现|添加|新增|优化|调整|完善)")
TEST_INTENT_RE = re.compile(r"\b(test|validate|verify|regression|coverage)\b", re.I)
TEST_ZH_RE = re.compile(r"(测试|验证|跑一下|检查是否通过)")
DEBUG_RE = re.compile(r"\b(debug|diagnose|root cause|reproduce|triage)\b", re.I)
REFACTOR_RE = re.compile(r"\b(refactor|cleanup|split|merge|rename|move)\b", re.I)
REFACTOR_ZH_RE = re.compile(r"(重构|拆分|合并|移动|重命名|抽取)")
SKILL_AUTHORING_RE = re.compile(
    r"\b(SKILL\.md|skill author|capability|registry|routing rule|hook runtime)\b",
    re.I,
)
SCHEMA_RE = re.compile(r"\b(schema|dto|api|contract|openapi|graphql|proto|migration)\b", re.I)
SECURITY_RE = re.compile(r"\b(auth|permission|secret|token|password|credential|security)\b", re.I)
DELIVERY_SURFACE_RE = re.compile(
    r"\b(kubectl|helm|terraform|release|deploy|deployment|rollback|install|build|package)\b|发布|部署",
    re.I,
)
NO_INJECTION_STAGES = {"question", "unknown", "no_engineering_action", "compaction"}


def classify_event(event: dict) -> dict[str, Any]:
    """Return stage, surfaces, and compact prompt signals for an event."""
    tool = compact_name(tool_name(event))
    hook = compact_name(event_name(event))
    command = extract_bash_command(event)
    paths = [normalize_path(path) for path in extract_changed_paths(event)]
    text = _transient_text(event, limit=1200)

    stage = _stage_from_event(event, tool, hook, command, text, paths)
    if stage in {"question", "unknown", "no_engineering_action"}:
        return {
            "stage": stage,
            "surfaces": [],
            "prompt_signals": _prompt_signals(text),
            "paths": paths,
            "tool": tool,
            "command_program": summarize_command_program(command),
            "should_inject": False,
        }
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
        "command_program": summarize_command_program(command),
        "should_inject": stage not in NO_INJECTION_STAGES,
    }


def is_read_tool(event: dict) -> bool:
    if any(tool in READ_TOOLS for tool in _tool_names(event)):
        return True
    command = extract_bash_command(event).strip()
    return bool(command) and summarize_command_program(command) in {
        "cat",
        "sed",
        "rg",
        "grep",
        "find",
        "ls",
    }


def is_review_diff_tool(event: dict) -> bool:
    if any(
        tool in {"fetchprpatch", "getprdiff", "mcpgithubpullrequestread"}
        for tool in _tool_names(event)
    ):
        return True
    evidence = "\n".join(_string_values(event, limit=40)).casefold()
    return any(token in evidence for token in ("pr diff", "pull request", ".patch", ".diff"))


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


def _stage_from_event(
    event: dict,
    tool: str,
    hook: str,
    command: str,
    text: str,
    paths: list[str],
) -> str:
    if hook == "permissionrequest":
        return "permission"
    if "subagent" in hook:
        return "subagent"
    if is_compaction_event(event):
        return "compaction"
    if tool in EDIT_TOOLS:
        return "edit"
    if tool in READ_TOOLS:
        return "read"
    if command and TEST_COMMAND_RE.search(command):
        return "test"
    combined = "\n".join([command, text, *paths])
    if hook == "userpromptsubmit" and _question_intent(text) and not _engineering_action_intent(text):
        return "question"
    if _test_intent(text):
        return "test"
    if REPAIR_FOLLOWUP_RE.search(text):
        return "repair"
    if _review_intent(text):
        return "review"
    if _repair_intent(text):
        return "repair"
    if _refactor_intent(text):
        return "refactor"
    if DEBUG_RE.search(text):
        return "repair"
    if _read_intent(text):
        return "read"
    if _edit_intent(text):
        return "edit"
    if RELEASE_RE.search(combined):
        return "release"
    if SKILL_AUTHORING_RE.search(combined):
        return "skill_authoring"
    if hook == "userpromptsubmit":
        return "question"
    if hook in {"sessionstart", "userpromptexpansion"}:
        return "no_engineering_action"
    return "unknown"


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
    if SKILL_AUTHORING_RE.search(joined):
        values.append("skill_authoring")
    if DELIVERY_SURFACE_RE.search(joined):
        values.append("delivery")
    return _unique(values) or ["general_engineering"]


def _prompt_signals(text: str) -> list[str]:
    signals: list[str] = []
    for name, pattern in (
        ("release_intent", RELEASE_RE),
        ("schema_or_api", SCHEMA_RE),
        ("security_or_permission", SECURITY_RE),
    ):
        if pattern.search(text):
            signals.append(name)
    if _review_intent(text):
        signals.append("review_intent")
    if _repair_intent(text):
        signals.append("repair_intent")
    if REPAIR_FOLLOWUP_RE.search(text):
        signals.append("repair_followup")
    return _unique(signals)


def _review_intent(text: str) -> bool:
    return bool(REVIEW_EN_RE.search(text) or REVIEW_ZH_RE.search(text))


def _repair_intent(text: str) -> bool:
    return bool(REPAIR_EN_RE.search(text) or REPAIR_ZH_RE.search(text))


def _question_intent(text: str) -> bool:
    return bool(QUESTION_INTENT_RE.search(text))


def _engineering_action_intent(text: str) -> bool:
    return any(
        (
            _review_intent(text),
            _repair_intent(text),
            _read_intent(text),
            _edit_intent(text),
            _test_intent(text),
            _refactor_intent(text),
            bool(DEBUG_RE.search(text)),
        )
    )


def _read_intent(text: str) -> bool:
    return bool(READ_INTENT_RE.search(text) or READ_ZH_RE.search(text))


def _edit_intent(text: str) -> bool:
    return bool(EDIT_INTENT_RE.search(text) or EDIT_ZH_RE.search(text))


def _test_intent(text: str) -> bool:
    return bool(TEST_INTENT_RE.search(text) or TEST_ZH_RE.search(text))


def _refactor_intent(text: str) -> bool:
    return bool(REFACTOR_RE.search(text) or REFACTOR_ZH_RE.search(text))


def _tool_names(event: dict) -> list[str]:
    names: list[str] = []

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
        if key in {"tool_name", "toolName", "name"}:
            names.append(compact_name(value))

    primary = compact_name(tool_name(event))
    if primary:
        names.append(primary)
    visit(event)
    return _unique(names)


def _string_values(value: Any, *, limit: int) -> list[str]:
    values: list[str] = []

    def visit(child: Any) -> None:
        if len(values) >= limit:
            return
        if isinstance(child, dict):
            for item in child.values():
                visit(item)
            return
        if isinstance(child, list):
            for item in child:
                visit(item)
            return
        if isinstance(child, str):
            values.append(child[:200])

    visit(value)
    return values


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
