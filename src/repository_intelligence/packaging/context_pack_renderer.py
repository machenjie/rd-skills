"""Render task context packs to Markdown."""

from __future__ import annotations

from typing import Any


def _pack_payload(context_pack: dict[str, Any]) -> dict[str, Any]:
    return context_pack.get("task_context_pack", context_pack)


def _lines_for_items(
    title: str,
    items: list[dict[str, object]],
    fields: list[str],
    *,
    max_items: int | None = None,
) -> list[str]:
    lines = [f"## {title}"]
    if not items:
        return [*lines, "- None"]
    visible_items = items[:max_items] if max_items is not None else items
    for item in visible_items:
        parts = [f"{field}={item.get(field)}" for field in fields if item.get(field) is not None]
        lines.append(f"- {'; '.join(parts)}")
    if max_items is not None and len(items) > max_items:
        lines.append(f"- additional_omitted_count={len(items) - max_items}")
    return lines


def _context_control_lines(pack: dict[str, Any]) -> list[str]:
    control = pack.get("context_control")
    if not isinstance(control, dict):
        return ["## Context Control", "- None"]
    fields = (
        "budget_mode",
        "budget_profile",
        "context_budget_tokens",
        "selected_file_count",
        "omitted_file_count",
        "selected_symbol_count",
        "selected_graph_node_count",
        "skipped_graph_node_count",
        "signal_density_rationale",
    )
    lines = ["## Context Control"]
    for field in fields:
        if field in control:
            lines.append(f"- {field}: {control.get(field)}")
    return lines


def _jit_plan_lines(pack: dict[str, Any]) -> list[str]:
    plan = pack.get("jit_retrieval_plan")
    lines = ["## JIT Retrieval Plan"]
    if not isinstance(plan, dict):
        return [*lines, "- None"]
    for title, fields in (
        ("Discovery", ["command", "purpose", "expected_output_policy"]),
        ("Targeted Reads", ["path", "line_hint", "read_policy", "source_truth_status", "reason"]),
        ("Deferred Reads", ["path", "reason"]),
        ("Forbidden Reads", ["path", "reason"]),
    ):
        key = title.lower().replace(" ", "_")
        lines.extend(_lines_for_items(title, plan.get(key, []), fields, max_items=12))
    return lines


def _artifact_policy_lines(pack: dict[str, Any]) -> list[str]:
    policy = pack.get("artifact_policy")
    lines = ["## Artifact Policy"]
    if not isinstance(policy, dict):
        return [*lines, "- None"]
    for key in ("large_outputs", "full_graph_dump", "full_test_log_dump"):
        lines.append(f"- {key}: {policy.get(key)}")
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
    for section_lines in (_context_control_lines(pack), _jit_plan_lines(pack), _artifact_policy_lines(pack)):
        lines.extend(section_lines)
        lines.append("")
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
        ("Residual Risk", pack.get("residual_risk", []), ["kind", "path", "detail"]),
        ("Excluded Context", pack.get("excluded_context", []), ["path", "reason"]),
    ]
    for title, items, fields in sections:
        lines.extend(_lines_for_items(title, items, fields))
        lines.append("")

    omitted_nodes = pack.get("omitted_nodes", [])
    lines.append("## Omitted Nodes")
    if not omitted_nodes:
        lines.append("- None")
    else:
        lines.append(f"- total_count: {len(omitted_nodes)}")
        lines.extend(_lines_for_items("Omitted Node Examples", omitted_nodes, ["path", "count", "reason"], max_items=8)[1:])
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
