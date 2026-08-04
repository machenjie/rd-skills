"""Small TOML fallback for validation scripts on Python versions before 3.11."""

from __future__ import annotations

import re
from typing import Any


class TOMLDecodeError(ValueError):
    """Raised when the fallback parser cannot read the provided TOML."""


def loads(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    current = root
    logical_lines = _logical_lines(text)
    for line in logical_lines:
        stripped = _strip_comment(line).strip()
        if not stripped:
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            table_name = stripped[1:-1].strip()
            if not table_name:
                raise TOMLDecodeError("empty table name")
            current = _table(root, table_name)
            continue
        if "=" not in stripped:
            raise TOMLDecodeError(f"invalid TOML line: {stripped}")
        key, raw_value = stripped.split("=", 1)
        key = key.strip()
        if not key:
            raise TOMLDecodeError("empty key")
        target, final_key = _key_target(current, key)
        target[final_key] = _parse_value(raw_value.strip())
    return root


def _logical_lines(text: str) -> list[str]:
    lines: list[str] = []
    pending: list[str] = []
    bracket_balance = 0
    for raw in text.splitlines():
        stripped = raw.strip()
        if pending:
            pending.append(stripped)
            bracket_balance += _bracket_delta(stripped)
            if bracket_balance <= 0:
                lines.append(" ".join(pending))
                pending = []
            continue
        if not stripped or stripped.startswith("#"):
            lines.append(raw)
            continue
        bracket_balance = _bracket_delta(stripped)
        if bracket_balance > 0 and "=" in stripped:
            pending = [stripped]
            continue
        lines.append(raw)
    if pending:
        raise TOMLDecodeError("unterminated array")
    return lines


def _bracket_delta(value: str) -> int:
    delta = 0
    in_string = False
    escaped = False
    for char in value:
        if escaped:
            escaped = False
            continue
        if char == "\\" and in_string:
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "[":
            delta += 1
        elif char == "]":
            delta -= 1
    return delta


def _strip_comment(value: str) -> str:
    in_string = False
    escaped = False
    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if char == "\\" and in_string:
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if char == "#" and not in_string:
            return value[:index]
    return value


def _table(root: dict[str, Any], dotted_name: str) -> dict[str, Any]:
    current = root
    for part in dotted_name.split("."):
        key = part.strip()
        if not key:
            raise TOMLDecodeError(f"invalid table name: {dotted_name}")
        child = current.setdefault(key, {})
        if not isinstance(child, dict):
            raise TOMLDecodeError(f"table conflicts with scalar: {dotted_name}")
        current = child
    return current


def _key_target(current: dict[str, Any], key: str) -> tuple[dict[str, Any], str]:
    parts = [part.strip() for part in key.split(".")]
    if any(not part for part in parts):
        raise TOMLDecodeError(f"invalid key: {key}")
    target = current
    for part in parts[:-1]:
        child = target.setdefault(part, {})
        if not isinstance(child, dict):
            raise TOMLDecodeError(f"key conflicts with scalar: {key}")
        target = child
    return target, parts[-1]


def _parse_value(raw: str) -> Any:
    value = raw.strip().rstrip(",").strip()
    if value.startswith('"') and value.endswith('"'):
        return bytes(value[1:-1], "utf-8").decode("unicode_escape")
    if value in {"true", "false"}:
        return value == "true"
    if value.startswith("{") and value.endswith("}"):
        return _parse_inline_table(value[1:-1])
    if value.startswith("[") and value.endswith("]"):
        return [_parse_value(part) for part in _split_top_level(value[1:-1]) if part.strip()]
    if re.fullmatch(r"[+-]?\d+", value):
        return int(value)
    if value:
        return value
    raise TOMLDecodeError("empty value")


def _parse_inline_table(raw: str) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for item in _split_top_level(raw):
        if not item.strip():
            continue
        if "=" not in item:
            raise TOMLDecodeError(f"invalid inline table item: {item}")
        key, value = item.split("=", 1)
        target, final_key = _key_target(parsed, key.strip())
        target[final_key] = _parse_value(value.strip())
    return parsed


def _split_top_level(raw: str) -> list[str]:
    items: list[str] = []
    start = 0
    brace_depth = 0
    bracket_depth = 0
    in_string = False
    escaped = False
    for index, char in enumerate(raw):
        if escaped:
            escaped = False
            continue
        if char == "\\" and in_string:
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            brace_depth += 1
        elif char == "}":
            brace_depth -= 1
        elif char == "[":
            bracket_depth += 1
        elif char == "]":
            bracket_depth -= 1
        elif char == "," and brace_depth == 0 and bracket_depth == 0:
            items.append(raw[start:index])
            start = index + 1
    items.append(raw[start:])
    return items
