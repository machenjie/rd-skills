#!/usr/bin/env python3
"""Shared validation helpers for ChangeForge authoring contracts."""

from __future__ import annotations

import re
import sys
import json
from pathlib import Path
from typing import Any, Iterable

try:  # PyYAML is optional; the fallback covers the repository registries.
    import yaml as _yaml
except Exception:  # pragma: no cover - depends on local environment
    _yaml = None


NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_DELIMITER = "---"
EXPECTED_PROFESSIONAL_SKILL_COUNT = 21
EXPECTED_FOUNDATION_CAPABILITY_COUNT = 136
EXPECTED_DOMAIN_EXTENSION_COUNT = 7
EXPECTED_PROFILE_TOP_LEVEL_COUNTS = {
    "recommended": EXPECTED_PROFESSIONAL_SKILL_COUNT,
    "full": EXPECTED_PROFESSIONAL_SKILL_COUNT + EXPECTED_DOMAIN_EXTENSION_COUNT,
    "dev": (
        EXPECTED_PROFESSIONAL_SKILL_COUNT
        + EXPECTED_FOUNDATION_CAPABILITY_COUNT
        + EXPECTED_DOMAIN_EXTENSION_COUNT
    ),
}

BANNED_BEGINNER_SECTIONS = (
    "Basic Usage",
    "Installation Tutorial",
    "Hello World",
    "Introduction",
    "What is",
    "Getting Started",
    "Quick Start",
    "Beginner Guide",
    "Syntax",
    "Framework Setup",
)

PERSONAL_ASSET_REFERENCES = (
    "folder.md",
    "personal notes",
    "local knowledge base",
    "toolbox",
    "user's asset library",
    "users asset library",
    "private documents",
)

class ValidationProblem(Exception):
    """Raised for malformed inputs that cannot be validated further."""


def relpath(root: Path, path: Path) -> str:
    return str(path.relative_to(root))


def fail_many(label: str, errors: Iterable[str]) -> int:
    items = list(errors)
    if not items:
        return 0
    for message in items:
        print(f"{label}: ERROR: {message}", file=sys.stderr)
    return 1


def visible_child_dirs(
    root: Path,
    *,
    excluded_prefixes: tuple[str, ...] = (".",),
    excluded_names: tuple[str, ...] = (),
) -> list[Path]:
    if not root.is_dir():
        return []
    return [
        path
        for path in sorted(root.iterdir())
        if path.is_dir()
        and not path.name.startswith(excluded_prefixes)
        and path.name not in excluded_names
    ]


def validate_expected_count(
    errors: list[str],
    label: str,
    actual: int,
    expected: int,
    context: str,
) -> None:
    if actual != expected:
        errors.append(f"{context}: expected {expected} {label}, found {actual}")


def _parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if value == "":
        return ""
    if value in {"[]", "[ ]"}:
        return []
    if value in {"{}", "{ }"}:
        return {}
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if value.lower() in {"null", "~"}:
        return None
    if value.startswith('"') and value.endswith('"'):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(part) for part in inner.split(",")]
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value


def _is_yaml_list_marker(content: str) -> bool:
    return content == "-" or content.startswith("- ")


def _is_block_scalar(value: str) -> bool:
    """A YAML block scalar indicator; only the indicator is retained."""
    return value[:1] in {"|", ">"}


def _yaml_significant_lines(text: str) -> list[tuple[int, str]]:
    """Return (indent, stripped-content) for each structural YAML line.

    Blank lines, comments, and frontmatter delimiters are dropped so the
    recursive parser sees only structural lines.
    """
    lines: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or stripped == FRONTMATTER_DELIMITER:
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        lines.append((indent, stripped))
    return lines


def _simple_yaml_load(text: str) -> dict[str, Any]:
    """Parse the indentation-based YAML subset used by ChangeForge assets.

    Supports nested mappings, lists of scalars, lists of mappings (whose items
    may carry nested mapping values), and simple block scalars to any depth.
    PyYAML is still preferred when available; this keeps the validation,
    routing, and telemetry tooling free of a hard YAML dependency.
    """
    value, _ = _parse_yaml_block(_yaml_significant_lines(text), 0, 0)
    return value if isinstance(value, dict) else {}


def _parse_yaml_block(
    lines: list[tuple[int, str]], start: int, indent: int
) -> tuple[Any, int]:
    if start >= len(lines):
        return {}, start
    if _is_yaml_list_marker(lines[start][1]):
        return _parse_yaml_list(lines, start, indent)
    return _parse_yaml_map(lines, start, indent)


def _parse_yaml_map(
    lines: list[tuple[int, str]], start: int, indent: int
) -> tuple[dict[str, Any], int]:
    result: dict[str, Any] = {}
    index = start
    while index < len(lines):
        line_indent, content = lines[index]
        if line_indent < indent or _is_yaml_list_marker(content):
            break
        if line_indent > indent or ":" not in content:
            index += 1
            continue
        key, raw_value = content.split(":", 1)
        key = key.strip()
        value = raw_value.strip()
        if value:
            index += 1
            if _is_block_scalar(value):
                block_entries: list[tuple[int, str]] = []
                while index < len(lines) and lines[index][0] > indent:
                    block_entries.append(lines[index])
                    index += 1
                min_indent = min((line_indent for line_indent, _ in block_entries), default=indent + 2)
                result[key] = "\n".join(
                    (" " * max(0, line_indent - min_indent)) + content
                    for line_indent, content in block_entries
                )
            else:
                result[key] = _parse_scalar(value)
            continue
        index += 1
        if index < len(lines) and lines[index][0] > indent:
            child, index = _parse_yaml_block(lines, index, lines[index][0])
            result[key] = child
        else:
            # Match the historical fallback: an empty root key is an empty
            # mapping, an empty nested key is an empty (scalar child) list.
            result[key] = {} if indent == 0 else []
    return result, index


def _parse_yaml_list(
    lines: list[tuple[int, str]], start: int, indent: int
) -> tuple[list[Any], int]:
    items: list[Any] = []
    index = start
    while index < len(lines):
        line_indent, content = lines[index]
        if line_indent != indent or not _is_yaml_list_marker(content):
            break
        remainder = content[1:].strip()
        index += 1
        child_lines: list[tuple[int, str]] = []
        while index < len(lines) and lines[index][0] > indent:
            child_lines.append(lines[index])
            index += 1
        if not remainder:
            if child_lines:
                value, _ = _parse_yaml_block(child_lines, 0, child_lines[0][0])
                items.append(value)
            else:
                items.append(None)
        elif ":" in remainder and remainder[:1] not in {"'", '"', "[", "{"}:
            # A mapping item: the inline key shares the dash line, so re-anchor
            # it (and any continuation keys) one block level deeper.
            synthesized = [(indent + 2, remainder), *child_lines]
            value, _ = _parse_yaml_block(synthesized, 0, indent + 2)
            items.append(value)
        else:
            items.append(_parse_scalar(remainder))
    return items, index


def load_yaml_text(text: str, path: Path) -> Any:
    if _yaml is not None:
        try:
            loaded = _yaml.safe_load(text)
        except Exception as exc:  # pragma: no cover - parser-specific
            raise ValidationProblem(f"invalid YAML in {path}: {exc}") from exc
        return {} if loaded is None else loaded

    return _simple_yaml_load(text)


def load_yaml_file(path: Path) -> Any:
    return load_yaml_text(path.read_text(encoding="utf-8"), path)


def parse_frontmatter(path: Path) -> tuple[dict[str, Any], str, str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_DELIMITER:
        raise ValidationProblem(f"{path} is missing YAML frontmatter")

    end_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == FRONTMATTER_DELIMITER:
            end_index = index
            break

    if end_index is None:
        raise ValidationProblem(f"{path} has unterminated YAML frontmatter")

    raw_frontmatter = "\n".join(lines[1:end_index])
    body = "\n".join(lines[end_index + 1 :])
    loaded = load_yaml_text(raw_frontmatter, path)
    if not isinstance(loaded, dict):
        raise ValidationProblem(f"{path} frontmatter must be a mapping")

    return loaded, raw_frontmatter, body


def heading_titles(markdown: str) -> list[str]:
    titles: list[str] = []
    for line in markdown.splitlines():
        match = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        if match:
            titles.append(match.group(1).strip())
    return titles


def has_section(markdown: str, section: str) -> bool:
    wanted = section.casefold()
    return any(title.casefold() == wanted for title in heading_titles(markdown))


def extract_section_body(markdown: str, section: str) -> str | None:
    """Return the body for a markdown heading with the exact title.

    The section ends at the next heading of the same or higher level. Fenced
    code blocks are ignored for heading detection so example output templates
    do not masquerade as authored sections.
    """

    wanted = section.casefold()
    lines = markdown.splitlines()
    capture_level: int | None = None
    captured: list[str] = []
    in_fence = False
    fence_marker: str | None = None

    for line in lines:
        stripped = line.strip()
        fence_match = re.match(r"^(```+|~~~+)", stripped)
        if fence_match:
            marker = fence_match.group(1)
            if not in_fence:
                in_fence = True
                fence_marker = marker[:3]
            elif fence_marker and marker.startswith(fence_marker):
                in_fence = False
                fence_marker = None

            if capture_level is not None:
                captured.append(line)
            continue

        heading_match = (
            None
            if in_fence
            else re.match(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$", line)
        )
        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            if capture_level is not None and level <= capture_level:
                break
            if title.casefold() == wanted:
                capture_level = level
                captured = []
            elif capture_level is not None:
                captured.append(line)
            continue

        if capture_level is not None:
            captured.append(line)

    if capture_level is None:
        return None
    return "\n".join(captured).strip()


def validate_required_sections(
    body: str,
    required_sections: Iterable[str],
    context: str,
    errors: list[str],
) -> None:
    titles = {title.casefold() for title in heading_titles(body)}
    for section in required_sections:
        if section.casefold() not in titles:
            errors.append(f"{context}: missing required section '{section}'")


def validate_no_beginner_sections(body: str, context: str, errors: list[str]) -> None:
    for title in heading_titles(body):
        folded = title.casefold()
        for banned in BANNED_BEGINNER_SECTIONS:
            banned_folded = banned.casefold()
            if folded == banned_folded or (
                banned_folded == "what is" and folded.startswith("what is ")
            ):
                errors.append(f"{context}: banned beginner section '{title}'")


def validate_no_personal_references(text: str, context: str, errors: list[str]) -> None:
    folded = text.casefold()
    for phrase in PERSONAL_ASSET_REFERENCES:
        if phrase.casefold() in folded:
            errors.append(f"{context}: banned personal/private reference '{phrase}'")


def validate_required_frontmatter(
    metadata: dict[str, Any],
    required_keys: Iterable[str],
    context: str,
    errors: list[str],
) -> None:
    for key in required_keys:
        value = metadata.get(key)
        if value is None or value == "":
            errors.append(f"{context}: missing required frontmatter '{key}'")


def validate_name(value: Any, context: str, errors: list[str], field: str = "name") -> None:
    if not isinstance(value, str) or not NAME_RE.fullmatch(value):
        errors.append(f"{context}: frontmatter '{field}' must be lowercase hyphen-separated")


def validate_description_length(
    value: Any,
    minimum: int,
    maximum: int,
    context: str,
    errors: list[str],
) -> None:
    if not isinstance(value, str):
        errors.append(f"{context}: frontmatter 'description' must be text")
        return

    length = len(value.strip())
    if length < minimum or length > maximum:
        errors.append(
            f"{context}: frontmatter 'description' must be {minimum}-{maximum} characters"
        )


def metadata_value_contains_tool(value: Any, tool_names: Iterable[str]) -> bool:
    folded = " ".join(_flatten_string_values(value)).casefold()
    return any(re.search(rf"\b{re.escape(tool.casefold())}\b", folded) for tool in tool_names)


def _flatten_string_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        values: list[str] = []
        for key, item in value.items():
            values.extend(_flatten_string_values(key))
            values.extend(_flatten_string_values(item))
        return values
    if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray)):
        values = []
        for item in value:
            values.extend(_flatten_string_values(item))
        return values
    return [str(value)]


def validate_allowed_tools_warning(
    metadata: dict[str, Any],
    raw_frontmatter: str,
    body: str,
    context: str,
    errors: list[str],
) -> None:
    allowed_tool_values = [
        value
        for key, value in metadata.items()
        if key.casefold().replace("_", "-") == "allowed-tools"
    ]
    raw_allowed_tools = re.findall(
        r"(?im)^allowed[-_ ]tools\s*:\s*(.+)$",
        raw_frontmatter,
    )
    requires_warning = any(
        metadata_value_contains_tool(value, ("shell", "bash"))
        for value in allowed_tool_values + raw_allowed_tools
    )
    if requires_warning and not has_section(body, "Trusted Tooling Warning"):
        errors.append(
            f"{context}: allowed-tools may not include shell/bash without "
            "a 'Trusted Tooling Warning' section"
        )


def registry_items(data: Any, key: str, path: Path, errors: list[str]) -> list[Any]:
    if not isinstance(data, dict):
        errors.append(f"{path}: registry must be a mapping")
        return []

    value = data.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list):
        errors.append(f"{path}: '{key}' must be a list")
        return []
    return value


def entry_ref(entry: Any, keys: Iterable[str]) -> str | None:
    if isinstance(entry, str):
        return entry
    if not isinstance(entry, dict):
        return None

    for key in keys:
        value = entry.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def entry_path(entry: Any) -> str | None:
    if not isinstance(entry, dict):
        return None
    value = entry.get("path")
    return value if isinstance(value, str) and value else None


def collect_reference_values(obj: Any, reference_keys: set[str]) -> list[str]:
    refs: list[str] = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            normalized_key = str(key).casefold().replace("-", "_")
            if normalized_key in reference_keys:
                refs.extend(_reference_strings(value))
            else:
                refs.extend(collect_reference_values(value, reference_keys))
    elif isinstance(obj, list):
        for item in obj:
            refs.extend(collect_reference_values(item, reference_keys))

    return refs


def _reference_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        refs: list[str] = []
        for item in value:
            refs.extend(_reference_strings(item))
        return refs
    if isinstance(value, dict):
        for key in (
            "name",
            "id",
            "skill",
            "skill_name",
            "capability_id",
            "changeforge_capability_id",
            "domain_extension",
            "domain_extension_id",
            "path",
        ):
            item = value.get(key)
            if isinstance(item, str) and item:
                return [item]
    return []


def path_is_within(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def first_path_part(path_value: str) -> str:
    return path_value.strip("/").split("/", 1)[0]
