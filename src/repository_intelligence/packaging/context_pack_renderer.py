"""Render task context packs to Markdown."""

from __future__ import annotations

from typing import Any


def _pack_payload(context_pack: dict[str, Any]) -> dict[str, Any]:
    return context_pack.get("task_context_pack", context_pack)


def _lines_for_items(title: str, items: list[dict[str, object]], fields: list[str]) -> list[str]:
    lines = [f"## {title}"]
    if not items:
        return [*lines, "- None"]
    for item in items:
        parts = [f"{field}={item.get(field)}" for field in fields if item.get(field) is not None]
        lines.append(f"- {'; '.join(parts)}")
    return lines


def render_context_pack_markdown(context_pack: dict[str, Any]) -> str:
    """Render a bounded, human-readable context pack."""
    pack = _pack_payload(context_pack)
    lines = [
        f"# Task Context Pack",
        "",
        f"Task: {pack.get('task') or pack.get('task_goal', '')}",
        "",
        "## Freshness",
        f"- status: {(pack.get('freshness') or pack.get('freshness_markers', {})).get('status')}",
        f"- repo_hash: {(pack.get('freshness') or pack.get('freshness_markers', {})).get('repo_hash')}",
        f"- indexed_at: {(pack.get('freshness') or pack.get('freshness_markers', {})).get('indexed_at')}",
        f"- indexed_commit: {(pack.get('freshness') or pack.get('freshness_markers', {})).get('indexed_commit')}",
        "",
    ]
    sections = [
        ("Source Of Truth", pack.get("source_of_truth", []), ["path", "reason"]),
        ("Selected Files", pack.get("selected_files", pack.get("relevant_files", [])), ["path", "permitted_changes", "reason", "owner_module"]),
        ("Selected Symbols", pack.get("selected_symbols", pack.get("relevant_symbols", [])), ["name", "symbol", "path", "file", "kind", "line"]),
        ("Caller Callee Edges", pack.get("caller_callee_edges", []), ["from", "to", "type"]),
        ("Imports", pack.get("imports", []), ["path", "module", "names", "name", "kind"]),
        ("References", pack.get("references", []), ["path", "kind", "value", "target"]),
        ("Related Tests", pack.get("related_tests", pack.get("affected_tests", [])), ["path", "reason"]),
        ("Validation Candidates", pack.get("validation_candidates", []), ["command", "scope", "source", "proves"]),
        ("Generated Artifacts", pack.get("generated_artifacts", []), ["generated_path", "source_of_truth", "reason"]),
        ("Ownership", pack.get("ownership", []), ["path", "owner_surface", "owner_module", "public_private_boundary"]),
        ("Reuse Candidates", pack.get("reuse_candidates", []), ["path", "reason"]),
        ("Rejected Locations", pack.get("rejected_locations", []), ["path", "reason"]),
        ("Omitted Nodes", pack.get("omitted_nodes", []), ["path", "count", "reason"]),
        ("Residual Risk", pack.get("residual_risk", []), ["kind", "path", "detail"]),
        ("Excluded Context", pack.get("excluded_context", []), ["path", "reason"]),
    ]
    for title, items, fields in sections:
        lines.extend(_lines_for_items(title, items, fields))
        lines.append("")

    lines.append("## Anti Bloat Decision")
    anti_bloat = pack.get("anti_bloat_decision", {})
    if isinstance(anti_bloat, dict) and anti_bloat:
        for key, value in anti_bloat.items():
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- None")
    lines.append("")

    for title in ("local_conventions", "non_goals", "drift_triggers", "evidence_limits"):
        lines.append(f"## {title.replace('_', ' ').title()}")
        values = pack.get(title, [])
        if not values:
            lines.append("- None")
        else:
            for value in values:
                lines.append(f"- {value}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
