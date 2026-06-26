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
from changeforge_normalized_event import NormalizedEvent
from changeforge_runtime_route_resolver import (
    detect_conditional_capabilities,
    detect_domain_extensions,
    detect_language_surfaces,
    detect_product_surfaces,
    detect_risk_surfaces,
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
REVIEW_ZH_ARTIFACT_RE = re.compile(r"(检查|查看).*(修改|改动|提交|修复|diff|PR|文件)", re.I)
REPAIR_EN_RE = re.compile(r"\b(fix|repair|address|resolve|remediate)\b", re.I)
REPAIR_ZH_RE = re.compile(r"(修复|解决|修复已经提交|已修复提交|再审查)")
REPAIR_FOLLOWUP_RE = re.compile(r"(修复已经提交|已修复提交|再审查|latest fix|fix is submitted)", re.I)
QUESTION_INTENT_RE = re.compile(
    r"\b(explain|what(?:'s| is| are)?|how(?: to| do| does| can| should)?|why|"
    r"difference between|compare|overview|describe|tell me about)\b"
    r"|为什么|是什么|什么是|解释|区别|介绍|怎么|如何|怎样|干嘛|做什么|概念",
    re.I,
)
EXPLICIT_EXECUTION_RE = re.compile(
    r"\b(review|inspect|audit|fix|repair|address|resolve|remediate|test|"
    r"validate|verify|read|open|look at|implement|modify|update|refactor|debug)"
    r"\s+(?:this|that|these|those|latest|current|the)\b",
    re.I,
)
EXPLICIT_EXECUTION_ZH_RE = re.compile(
    r"(?:请|帮我|帮忙|麻烦|需要|给我)?\s*"
    r"(审查|评审|复查|仔细审查|详细审查|检查|查看|修复|解决|测试|验证|跑一下|"
    r"阅读|分析|修改|改动|实现|添加|新增|优化|调整|完善|重构|调试)"
    r".{0,12}(这个|这次|上面|上述|最新|文件|提交|修复|修改|改动|仓库|项目|PR|diff)",
    re.I,
)
ARTIFACT_SIGNAL_RE = re.compile(
    r"\b(file|files|repo|repository|commit|diff|patch|pr|pull request|"
    r"changed files?|latest commit)\b"
    r"|(?:^|[\s\"'`])[\w./-]+\."
    r"(?:py|ts|tsx|js|jsx|go|rs|java|kt|rb|php|cs|cpp|c|h|hpp|md|yaml|yml|json|toml|sh)\b"
    r"|最新提交|这次修改|这次改动|最新改动|上面的修复|上述修复|这个修复|"
    r"这个文件|这个仓库|这个项目|文件|提交|仓库|项目|PR|diff",
    re.I,
)
RELEASE_RE = re.compile(r"\b(release|deploy|deployment|install|build|package|rollback)\b|发布|部署", re.I)
READ_INTENT_RE = re.compile(r"\b(read|grep|search|find|open|look at|inspect file)\b", re.I)
READ_ZH_RE = re.compile(r"(阅读|查看|分析|理解|看看|检查代码)")
EDIT_INTENT_RE = re.compile(r"\b(add|change|modify|update|implement|write|create)\b", re.I)
EDIT_ZH_RE = re.compile(r"(修改|改动|实现|添加|新增|优化|调整|完善)")
TEST_INTENT_RE = re.compile(r"\b(tests?|validate|verify|regression|coverage)\b", re.I)
TEST_ZH_RE = re.compile(r"(测试|验证|跑一下|检查是否通过)")
DEBUG_RE = re.compile(r"\b(debug|diagnose|root cause|reproduce|triage)\b", re.I)
REFACTOR_RE = re.compile(r"\b(refactor|cleanup|split|merge|rename|move)\b", re.I)
REFACTOR_ZH_RE = re.compile(r"(重构|拆分|合并|移动|重命名|抽取)")
SKILL_AUTHORING_RE = re.compile(
    r"\b(SKILL\.md|skill author(?:ing)?|foundation capability|capability reference|routing rule|"
    r"ChangeForge registry|skill registry|capability registry|routing-rules\.ya?ml|"
    r"stage-model\.ya?ml|hook runtime)\b"
    r"|src/(?:professional-skills|foundation/capabilities|domain-extensions|registry|hook-runtime)/",
    re.I,
)
NO_INJECTION_STAGES = {"question", "unknown", "no_engineering_action", "compaction"}


def classify_event(event: dict) -> dict[str, Any]:
    """Return stage, surfaces, and compact prompt signals for an event."""
    return normalize_event(event).to_classifier_dict()


def normalize_event(event: dict) -> NormalizedEvent:
    """Return the normalized event object while preserving classifier semantics."""
    classification = _classify_event_dict(event)
    read_evidence = (
        extract_read_evidence(event)
        if is_read_tool(event) or classification.get("stage") == "read"
        else {}
    )
    return NormalizedEvent.from_event(
        event,
        classification=classification,
        read_evidence=read_evidence,
    )


def _classify_event_dict(event: dict) -> dict[str, Any]:
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
            "product_surfaces": [],
            "language_surfaces": [],
            "risk_surfaces": [],
            "domain_extensions": [],
            "prompt_signals": _prompt_signals(text),
            "paths": paths,
            "tool": tool,
            "command_program": summarize_command_program(command),
            "should_inject": False,
        }
    surfaces = _surfaces(paths, command, text)
    language_surfaces = detect_language_surfaces(paths, command, text)
    risk_surfaces = detect_risk_surfaces(paths, command, text)
    domain_extensions = detect_domain_extensions(paths, command, text)
    conditional_capabilities = detect_conditional_capabilities(paths, command, text)
    prompt_signals = _prompt_signals(text)
    return {
        "stage": stage,
        "surfaces": surfaces,
        "product_surfaces": surfaces,
        "language_surfaces": language_surfaces,
        "risk_surfaces": risk_surfaces,
        "domain_extensions": domain_extensions,
        "conditional_capabilities": conditional_capabilities,
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
    if hook == "userpromptsubmit" and _educational_question(text):
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
    if SKILL_AUTHORING_RE.search(combined):
        return "skill_authoring"
    if _edit_intent(text):
        return "edit"
    if RELEASE_RE.search(combined):
        return "release"
    if hook == "userpromptsubmit":
        return "question"
    if hook in {"sessionstart", "userpromptexpansion"}:
        return "no_engineering_action"
    return "unknown"


def _surfaces(paths: list[str], command: str, text: str) -> list[str]:
    return detect_product_surfaces(paths, command, text)


def _prompt_signals(text: str) -> list[str]:
    if _educational_question(text):
        return []
    signals: list[str] = []
    for name, pattern in (
        ("release_intent", RELEASE_RE),
    ):
        if pattern.search(text):
            signals.append(name)
    lowered = text.casefold()
    for signal, terms in (
        ("context budget", ("context budget", "reference bloat", "skipped references")),
        ("jit retrieval", ("jit retrieval", "just in time retrieval")),
        ("tool output boundary", ("tool output boundary", "output truncation")),
        ("compaction snapshot", ("compaction snapshot", "compaction contract")),
        ("source of truth", ("source of truth", "source-of-truth")),
        ("generated artifact", ("generated artifact", "generated source")),
        ("broad system audit", ("broad system audit", "system-wide audit")),
    ):
        if any(term in lowered for term in terms):
            signals.append(signal)
    risk_surfaces = detect_risk_surfaces([], "", text)
    if "data-api" in risk_surfaces:
        signals.append("schema_or_api")
    if "security" in risk_surfaces:
        signals.append("security_or_permission")
    if _review_intent(text):
        signals.append("review_intent")
    if _repair_intent(text):
        signals.append("repair_intent")
    if REPAIR_FOLLOWUP_RE.search(text):
        signals.append("repair_followup")
    return _unique(signals)


def _review_intent(text: str) -> bool:
    return bool(
        REVIEW_EN_RE.search(text)
        or REVIEW_ZH_RE.search(text)
        or REVIEW_ZH_ARTIFACT_RE.search(text)
    )


def _repair_intent(text: str) -> bool:
    return bool(REPAIR_EN_RE.search(text) or REPAIR_ZH_RE.search(text))


def _question_intent(text: str) -> bool:
    return bool(QUESTION_INTENT_RE.search(text))


def _educational_question(text: str) -> bool:
    return bool(_question_intent(text) and not _explicit_execution_request(text))


def _explicit_execution_request(text: str) -> bool:
    if EXPLICIT_EXECUTION_RE.search(text) or EXPLICIT_EXECUTION_ZH_RE.search(text):
        return True
    return bool(ARTIFACT_SIGNAL_RE.search(text) and _engineering_action_intent(text))


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
