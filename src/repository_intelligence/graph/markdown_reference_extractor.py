"""Markdown frontmatter, heading, and reference extraction."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from repository_intelligence.graph.file_classifier import normalize_repo_path


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
CODE_RE = re.compile(r"`([^`\n]+)`")


def _simple_frontmatter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    end_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break
    if end_index is None:
        return {}, text

    frontmatter: dict[str, object] = {}
    for line in lines[1:end_index]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            frontmatter[key.strip()] = [
                item.strip().strip("\"'")
                for item in value[1:-1].split(",")
                if item.strip()
            ]
        else:
            frontmatter[key.strip()] = value.strip("\"'")
    return frontmatter, "\n".join(lines[end_index + 1 :])


def _target_from_link(raw_target: str, source_path: str) -> str | None:
    target = raw_target.split("#", 1)[0].strip()
    if not target:
        return None
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
        return None
    if target.startswith("#"):
        return None
    path = Path(source_path).parent / target
    return path.as_posix().lstrip("./")


def _looks_like_reference(value: str) -> bool:
    if "/" in value:
        return True
    if value.endswith((".py", ".md", ".yaml", ".yml", ".json", ".sh")):
        return True
    return bool(re.fullmatch(r"[a-z][a-z0-9]+(?:-[a-z0-9]+)+", value))


def extract_markdown_source(source: str, source_path: str = "") -> dict[str, Any]:
    frontmatter, body = _simple_frontmatter(source)
    headings: list[dict[str, object]] = []
    references: list[dict[str, object]] = []
    body_start_line = source[: len(source) - len(body)].count("\n")
    heading_stack: list[dict[str, object]] = []

    for offset, line in enumerate(body.splitlines(), start=1):
        line_number = body_start_line + offset
        heading_match = HEADING_RE.match(line)
        if heading_match:
            level = len(heading_match.group(1))
            while heading_stack and int(heading_stack[-1]["level"]) >= level:
                heading_stack.pop()
            parent = str(heading_stack[-1]["name"]) if heading_stack else None
            heading = {
                "name": heading_match.group(2).strip(),
                "kind": "heading",
                "path": source_path,
                "line": line_number,
                "level": level,
                "line_start": line_number,
                "line_end": line_number,
                "visibility": "public",
                "owner_object": frontmatter.get("name"),
                "parent_symbol": parent,
                "language": "markdown",
                "confidence": "high",
            }
            headings.append(
                heading
            )
            heading_stack.append(heading)

        for match in LINK_RE.finditer(line):
            raw_target = match.group(2).strip()
            references.append(
                {
                    "kind": "link",
                    "value": raw_target,
                    "target": _target_from_link(raw_target, source_path),
                    "line": line_number,
                }
            )

        for match in CODE_RE.finditer(line):
            value = match.group(1).strip()
            if _looks_like_reference(value):
                references.append({"kind": "code", "value": value, "line": line_number})

    return {
        "frontmatter": frontmatter,
        "headings": headings,
        "references": references,
    }


def extract_markdown_file(path: str | Path, repo_root: str | Path | None = None) -> dict[str, Any]:
    file_path = Path(path)
    source_path = normalize_repo_path(file_path, repo_root)
    source = file_path.read_text(encoding="utf-8", errors="replace")
    extracted = extract_markdown_source(source, source_path)
    extracted["path"] = source_path
    return extracted
