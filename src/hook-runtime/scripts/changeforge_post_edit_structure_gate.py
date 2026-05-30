#!/usr/bin/env python3
"""Warn when post-edit paths should trigger ChangeForge structure discipline."""

from __future__ import annotations

import sys
from pathlib import Path

from changeforge_common import (
    compact_name,
    cwd_from_event,
    detect_runtime,
    emit_block,
    emit_warning,
    extract_changed_paths,
    hook_mode,
    is_post_tool_use,
    merge_state,
    normalize_path,
    read_event,
    repo_root,
    tool_name,
)


EDIT_TOOLS = {"edit", "write", "multiedit", "applypatch"}
STRUCTURE_PATH_HINTS = [
    "/service/",
    "/services/",
    "/repository/",
    "/repositories/",
    "/adapter/",
    "/adapters/",
    "/client/",
    "/clients/",
    "/helper/",
    "/helpers/",
    "/utils/",
    "/common/",
    "/shared/",
    "/domain/",
    "/model/",
    "/models/",
]
DEPENDENCY_FILES = [
    "package.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "go.mod",
    "go.sum",
    "pyproject.toml",
    "requirements.txt",
    "Cargo.toml",
    "Cargo.lock",
    "pom.xml",
    "build.gradle",
]
STRUCTURAL_ROLE_HINTS = {
    "service",
    "services",
    "repository",
    "repositories",
    "adapter",
    "adapters",
    "client",
    "clients",
    "helper",
    "helpers",
    "parser",
    "parsers",
    "mapper",
    "mappers",
    "validator",
    "validators",
}
PUBLIC_INTERFACE_HINTS = {
    "api",
    "apis",
    "contract",
    "contracts",
    "interface",
    "interfaces",
    "sdk",
    "client",
    "clients",
    "adapter",
    "adapters",
}


def main() -> int:
    event = read_event()
    if not event:
        return 0
    runtime = detect_runtime(event)
    if runtime == "unknown":
        return 0
    mode = hook_mode()
    if mode == "off":
        return 0
    if not is_post_tool_use(event):
        return 0
    tool = compact_name(tool_name(event))
    if tool not in EDIT_TOOLS:
        return 0

    try:
        repo = repo_root(cwd_from_event(event))
        paths = extract_changed_paths(event)
        if not paths:
            return 0
        findings = _structure_findings(event, paths, tool)
        merge_state(
            repo,
            runtime,
            changed_paths=paths,
            structure_findings=findings,
            suggested_skills=_suggested_skills(findings),
            suggested_capabilities=["implementation-structure-design"] if findings else [],
            suggested_gates=["code-review"] if findings else [],
        )
        if not findings or mode == "monitor":
            return 0
        message = _warning_message(findings)
        if mode == "block":
            emit_block(runtime, message)
            return 2
        emit_warning(runtime, message)
        return 0
    except Exception as exc:
        emit_warning(runtime, f"ChangeForge Hook Runtime warning: structure gate failed open: {exc}")
        return 0


def _structure_findings(event: dict, paths: list[str], tool: str) -> list[str]:
    added_paths = _added_paths(event)
    findings: list[str] = []
    for raw_path in paths:
        path = normalize_path(raw_path)
        normalized = f"/{path.casefold()}"
        name = Path(path).name
        parts = {part.casefold() for part in Path(path).parts}

        reasons: list[str] = []
        if path in added_paths or tool == "write":
            reasons.append("new file")
        if name in DEPENDENCY_FILES:
            reasons.append("dependency or lockfile")
        if any(hint in normalized for hint in STRUCTURE_PATH_HINTS):
            reasons.append("shared or structural path")
        if (path in added_paths or tool == "write") and parts.intersection(STRUCTURAL_ROLE_HINTS):
            reasons.append("new service/repository/adapter/client/helper/parser/mapper/validator")
        if parts.intersection(PUBLIC_INTERFACE_HINTS):
            reasons.append("public interface, SDK, client, or adapter surface")

        if reasons:
            findings.append(f"{path}: {', '.join(_unique(reasons))}")
    return _unique(findings)


def _added_paths(event: dict) -> set[str]:
    paths: set[str] = set()

    def visit(value: object) -> None:
        if isinstance(value, dict):
            for child in value.values():
                visit(child)
            return
        if isinstance(value, list):
            for child in value:
                visit(child)
            return
        if isinstance(value, str) and "*** Begin Patch" in value:
            for line in value.splitlines():
                stripped = line.strip()
                prefix = "*** Add File:"
                if stripped.startswith(prefix):
                    paths.add(normalize_path(stripped[len(prefix) :].strip()))

    visit(event)
    return paths


def _suggested_skills(findings: list[str]) -> list[str]:
    if not findings:
        return []
    return ["change-forge-router", "ai-code-review-refactor"]


def _warning_message(findings: list[str]) -> str:
    detected = "\n".join(f"- {finding}" for finding in findings)
    return f"""ChangeForge Structure Gate triggered.

Detected structural paths:
{detected}

This change appears to add or modify structural code. Before continuing, preserve:
- reuse vs new rationale
- placement rationale
- module ownership and dependency direction
- public/private API decision
- same-pattern scan
- tests near the changed behavior

Expected ChangeForge route:
- implementation-structure-design
- code-review
- ai-code-review-refactor when AI-generated implementation is material"""


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
