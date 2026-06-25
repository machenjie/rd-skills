"""Offline reviewer for Project Memory Governance events."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from project_memory.gates.fragile_file_gate import fragile_file_counts
from project_memory.gates.repeat_failure_gate import FAILURE_OUTCOMES
from project_memory.store.append_log import ensure_memory_root, iter_memory_events
from project_memory.store.projection import build_memory_summary


def review_repository_memory(root: Path) -> dict[str, Any]:
    """Generate a projection and human-review-only candidate suggestions."""
    events = list(iter_memory_events(root))
    summary = build_memory_summary(events)
    suggestions = build_suggestions(events)
    ensure_memory_root(root)
    stem = _timestamp_slug(summary["project_memory_summary"]["generated_at"])
    projection_path = root / "projections" / f"{stem}-project-memory-summary.json"
    projection_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    suggestions_path: Path | None = None
    if suggestions:
        suggestions_doc = {
            "generated_from_project_memory": True,
            "requires_human_review": True,
            "suggestions": suggestions,
        }
        suggestions_path = root / "suggestions" / f"{stem}-memory-suggestions.yaml"
        suggestions_path.write_text(dump_yaml(suggestions_doc), encoding="utf-8")
    return {
        "events": len(events),
        "projection_path": str(projection_path),
        "suggestions_path": str(suggestions_path) if suggestions_path else "",
        "suggestions": suggestions,
        "summary": summary["project_memory_summary"],
    }


def build_suggestions(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build candidate-only suggestions; never mutate skills or routing."""
    suggestions: list[dict[str, Any]] = []
    suggestions.extend(_repeat_failure_suggestions(events))
    suggestions.extend(_fragile_file_suggestions(events))
    return suggestions[:50]


def dump_yaml(data: Any, indent: int = 0) -> str:
    """Emit a small deterministic YAML subset used by memory promotion."""
    lines: list[str] = []
    _emit_yaml(data, indent, lines)
    return "\n".join(lines) + "\n"


def _repeat_failure_suggestions(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: Counter[tuple[str, str, str, str]] = Counter()
    group_events: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    for event in events:
        if event.get("outcome") not in FAILURE_OUTCOMES:
            continue
        for path in event.get("paths") or [""]:
            key = (
                str(event.get("repo_hash", "")),
                str(event.get("task_fingerprint", "")),
                str(path),
                str(event.get("owner_skill", "")),
            )
            grouped[key] += 1
            group_events.setdefault(key, []).append(event)
    result: list[dict[str, Any]] = []
    for key, count in sorted(grouped.items()):
        if count < 2:
            continue
        repo_hash, task, path, owner = key
        evidence_events = group_events.get(key, [])
        suggestion_id = f"memory-repeat-failure-{_short(repo_hash, task, path, owner)}"
        result.append(
            {
                "id": suggestion_id,
                "type": "repeat_failure",
                "promotion_type": "failure_pattern",
                "severity": "high",
                "evidence": f"{count} failed or blocked attempts for {path}",
                "failure_evidence": f"{count} failed or blocked attempts for {path}",
                "validation_evidence": _event_refs(evidence_events),
                "affected_repo_hash": repo_hash,
                "task_fingerprint": task,
                "source_evidence": _first_source_evidence(evidence_events),
                "residual_risk": ["memory-derived candidate requires current source validation"],
                "promotion_target": "tests/project_memory/fixtures",
                "suggested_action": "Add a memory gate fixture for same-path repeat failure handling.",
                "requires_human_review": True,
            }
        )
    return result


def _fragile_file_suggestions(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for path, count in sorted(fragile_file_counts(events).items()):
        if count < 2:
            continue
        evidence_events = [
            event for event in events if path in [str(item) for item in event.get("paths") or []]
        ]
        result.append(
            {
                "id": f"memory-fragile-file-{_short(path)}",
                "type": "fragile_file",
                "promotion_type": "fragile_file",
                "severity": "medium",
                "evidence": f"{count} fragile signals for {path}",
                "failure_evidence": f"{count} fragile signals for {path}",
                "validation_evidence": _event_refs(evidence_events),
                "source_evidence": _first_source_evidence(evidence_events),
                "residual_risk": ["memory-derived candidate requires current source validation"],
                "promotion_target": "tests/project_memory/fixtures",
                "suggested_action": "Add a fragile-file gate fixture before changing this path again.",
                "requires_human_review": True,
            }
        )
    return result


def _timestamp_slug(value: str) -> str:
    return value.replace(":", "").replace("-", "").replace("+", "").replace("Z", "z")


def _short(*parts: str) -> str:
    import hashlib

    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:12]


def _first_source_evidence(events: list[dict[str, Any]]) -> dict[str, Any]:
    for event in events:
        evidence = event.get("source_evidence")
        if isinstance(evidence, dict):
            return dict(evidence)
    return {}


def _event_refs(events: list[dict[str, Any]]) -> list[str]:
    refs: list[str] = []
    for event in events:
        refs.extend(str(ref) for ref in event.get("evidence_refs") or [] if str(ref).strip())
    return sorted(set(refs))[:10]


def _emit_yaml(value: Any, indent: int, lines: list[str]) -> None:
    pad = " " * indent
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, (dict, list)) and item:
                lines.append(f"{pad}{key}:")
                _emit_yaml(item, indent + 2, lines)
            elif isinstance(item, dict):
                lines.append(f"{pad}{key}: {{}}")
            elif isinstance(item, list):
                lines.append(f"{pad}{key}: []")
            else:
                lines.append(f"{pad}{key}: {_scalar(item)}")
        return
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                first = True
                for key, child in item.items():
                    prefix = f"{pad}- " if first else f"{pad}  "
                    if isinstance(child, (dict, list)) and child:
                        lines.append(f"{prefix}{key}:")
                        _emit_yaml(child, indent + 4, lines)
                    else:
                        lines.append(f"{prefix}{key}: {_scalar(child)}")
                    first = False
            else:
                lines.append(f"{pad}- {_scalar(item)}")


def _scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    text = str(value)
    if not text or any(char in text for char in (":", "#", "\n", '"')) or text.strip() != text:
        return '"' + text.replace("\n", " ").replace('"', "'") + '"'
    return text
