#!/usr/bin/env python3
"""Parse Codex CLI JSONL into bounded live benchmark metrics."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from codex_live_benchmark_lib import write_json


USAGE_KEYS = {
    "input_tokens": "input_tokens",
    "cached_input_tokens": "cached_input_tokens",
    "output_tokens": "output_tokens",
    "reasoning_output_tokens": "reasoning_output_tokens",
    "reasoning_tokens": "reasoning_output_tokens",
}
SAFE_LABEL_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,80}$")


def parse_events(path: Path, *, max_parse_errors: int = 50) -> dict[str, Any]:
    """Return bounded counts from a Codex JSONL event file.

    The parser deliberately omits raw command text and message bodies. It keeps
    only event categories, counters, parse-error locations, and usage totals.
    """
    metrics: dict[str, Any] = {
        "event_count": 0,
        "turn_started": 0,
        "turn_completed": 0,
        "turn_failed": 0,
        "command_execution_count": 0,
        "file_change_count": 0,
        "plan_update_count": 0,
        "agent_message_count": 0,
        "error_count": 0,
        "usage": {
            "input_tokens": 0,
            "cached_input_tokens": 0,
            "output_tokens": 0,
            "reasoning_output_tokens": 0,
        },
        "event_types": {},
        "parse_errors": [],
    }
    if not path.exists():
        metrics["parse_errors"].append({"line": 0, "error": "events file missing"})
        return metrics

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            if len(metrics["parse_errors"]) < max_parse_errors:
                metrics["parse_errors"].append({"line": line_number, "error": exc.msg})
            continue
        metrics["event_count"] += 1
        _count_event(event, metrics)
        _sum_usage(event, metrics["usage"])
    return metrics


def write_redacted_events(path: Path, out_path: Path, *, max_parse_errors: int = 50) -> None:
    """Write a bounded event JSONL stream without raw commands, paths, or messages."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows = _redacted_event_rows(path, max_parse_errors=max_parse_errors)
    out_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _redacted_event_rows(path: Path, *, max_parse_errors: int = 50) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return [{"line": 0, "event_type": "parse_error", "error": "events file missing"}]

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            if len([row for row in rows if row.get("event_type") == "parse_error"]) < max_parse_errors:
                rows.append({"line": line_number, "event_type": "parse_error", "error": exc.msg})
            continue
        rows.append(_redacted_event_row(event, line_number))
    return rows


def _redacted_event_row(event: Any, line_number: int) -> dict[str, Any]:
    searchable = _safe_search_text(event)
    usage = {
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "output_tokens": 0,
        "reasoning_output_tokens": 0,
    }
    _sum_usage(event, usage)
    row: dict[str, Any] = {
        "line": line_number,
        "event_type": _safe_label(_event_name(event) or "unknown"),
    }
    for key in ("status", "role"):
        value = _first_safe_string(event, key)
        if value:
            row[key] = value
    tags: list[str] = []
    if "turn.started" in searchable or "turn_started" in searchable:
        tags.append("turn_started")
    if "turn.completed" in searchable or "turn_completed" in searchable:
        tags.append("turn_completed")
    if "turn.failed" in searchable or "turn_failed" in searchable:
        tags.append("turn_failed")
    if "exec" in searchable or "command" in searchable or "tool_call" in searchable:
        tags.append("command_execution")
    if "apply_patch" in searchable or "file_change" in searchable or "patch" in searchable:
        tags.append("file_change")
    if "update_plan" in searchable or "plan_update" in searchable:
        tags.append("plan_update")
    if "assistant" in searchable or "agent_message" in searchable:
        tags.append("agent_message")
    if "error" in searchable or "failed" in searchable:
        tags.append("error")
    if tags:
        row["tags"] = sorted(dict.fromkeys(tags))
    compact_usage = {key: value for key, value in usage.items() if value}
    if compact_usage:
        row["usage"] = compact_usage
    return row


def _event_name(event: Any) -> str:
    if not isinstance(event, dict):
        return ""
    for key in ("type", "event", "kind", "name"):
        value = event.get(key)
        if isinstance(value, str):
            return value.lower()
    return ""


def _safe_label(value: str) -> str:
    return value if SAFE_LABEL_RE.fullmatch(value) else "<redacted>"


def _first_safe_string(value: Any, target_key: str) -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == target_key and isinstance(child, str):
                return _safe_label(child.lower())
            if not isinstance(child, str):
                nested = _first_safe_string(child, target_key)
                if nested:
                    return nested
    elif isinstance(value, list):
        for child in value:
            if not isinstance(child, str):
                nested = _first_safe_string(child, target_key)
                if nested:
                    return nested
    return None


def _count_event(event: Any, metrics: dict[str, Any]) -> None:
    name = _event_name(event)
    if name:
        metrics["event_types"][name] = metrics["event_types"].get(name, 0) + 1
    searchable = _safe_search_text(event)
    if "turn.started" in searchable or "turn_started" in searchable:
        metrics["turn_started"] += 1
    if "turn.completed" in searchable or "turn_completed" in searchable:
        metrics["turn_completed"] += 1
    if "turn.failed" in searchable or "turn_failed" in searchable:
        metrics["turn_failed"] += 1
    if "exec" in searchable or "command" in searchable or "tool_call" in searchable:
        metrics["command_execution_count"] += 1
    if "apply_patch" in searchable or "file_change" in searchable or "patch" in searchable:
        metrics["file_change_count"] += 1
    if "update_plan" in searchable or "plan_update" in searchable:
        metrics["plan_update_count"] += 1
    if "assistant" in searchable or "agent_message" in searchable:
        metrics["agent_message_count"] += 1
    if "error" in searchable or "failed" in searchable:
        metrics["error_count"] += 1


def _safe_search_text(value: Any) -> str:
    """Return only keys and low-risk event names, not raw text payloads."""
    parts: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            parts.append(str(key).lower())
            if key in {"type", "event", "kind", "name", "role", "status"} and isinstance(child, str):
                parts.append(_safe_label(child.lower()))
            elif not isinstance(child, str):
                parts.append(_safe_search_text(child))
    elif isinstance(value, list):
        for child in value:
            if not isinstance(child, str):
                parts.append(_safe_search_text(child))
    return " ".join(parts)


def _sum_usage(value: Any, usage: dict[str, int]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            mapped = USAGE_KEYS.get(str(key))
            if mapped and isinstance(child, int):
                usage[mapped] += child
            else:
                _sum_usage(child, usage)
    elif isinstance(value, list):
        for child in value:
            _sum_usage(child, usage)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--redacted-out", type=Path)
    args = parser.parse_args(argv)

    metrics = parse_events(args.events)
    if args.out:
        write_json(args.out, metrics)
    else:
        print(json.dumps(metrics, indent=2, sort_keys=True))
    if args.redacted_out:
        write_redacted_events(args.events, args.redacted_out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
