"""Reference graph construction for ChangeForge source files."""

from __future__ import annotations

from pathlib import Path
from typing import Any


CAPABILITY_ROOT = "src/foundation/capabilities"
SKILL_ROOT = "src/professional-skills"
DOMAIN_EXTENSION_ROOT = "src/domain-extensions"


def edge_key(edge: dict[str, str]) -> tuple[str, str, str]:
    return (edge["from"], edge["to"], edge["type"])


def dedupe_edges(edges: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    deduped: list[dict[str, str]] = []
    for edge in edges:
        key = edge_key(edge)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(edge)
    return deduped


def _existing_target(target: str, files_by_path: dict[str, dict[str, object]]) -> str | None:
    normalized = target.strip().lstrip("./")
    if normalized in files_by_path:
        return normalized
    if normalized.endswith("/"):
        normalized = normalized.rstrip("/")
    skill_target = f"{normalized}/SKILL.md"
    if skill_target in files_by_path:
        return skill_target
    return None


def _target_for_name(value: str, files_by_path: dict[str, dict[str, object]]) -> str | None:
    for root in (CAPABILITY_ROOT, SKILL_ROOT, DOMAIN_EXTENSION_ROOT):
        candidate = f"{root}/{value}/SKILL.md"
        if candidate in files_by_path:
            return candidate
    return None


def _edge_type_for_target(target: str, default: str = "doc_reference") -> str:
    if target.startswith("src/registry/"):
        return "routing_rule_reference"
    if target.startswith(CAPABILITY_ROOT) or target.startswith(SKILL_ROOT) or target.startswith(DOMAIN_EXTENSION_ROOT):
        return "skill_reference"
    if target.startswith("scripts/validate-") or target.startswith("scripts/eval-"):
        return "validator_reference"
    if target.startswith("tests/"):
        return "test_reference"
    if target.startswith("dist/"):
        return "generated_artifact"
    return default


def build_markdown_reference_edges(
    file_node: dict[str, object],
    files_by_path: dict[str, dict[str, object]],
) -> list[dict[str, str]]:
    source = str(file_node["path"])
    edges: list[dict[str, str]] = []
    for ref in file_node.get("references", []):
        if not isinstance(ref, dict):
            continue
        target = None
        if isinstance(ref.get("target"), str):
            target = _existing_target(str(ref["target"]), files_by_path)
        if target is None and isinstance(ref.get("value"), str):
            value = str(ref["value"])
            target = _existing_target(value, files_by_path) or _target_for_name(value, files_by_path)
        if target:
            edges.append({"from": source, "to": target, "type": _edge_type_for_target(target)})
    return edges


def build_registry_edges(
    file_node: dict[str, object],
    files_by_path: dict[str, dict[str, object]],
) -> list[dict[str, str]]:
    source = str(file_node["path"])
    edges: list[dict[str, str]] = []
    symbols = [symbol for symbol in file_node.get("symbols", []) if isinstance(symbol, dict)]
    for symbol in symbols:
        name = str(symbol.get("name") or "")
        path_value = symbol.get("path")
        target = None
        if isinstance(path_value, str):
            target = _existing_target(path_value, files_by_path)
        if target is None and name:
            target = _target_for_name(name, files_by_path)
        if target:
            edges.append({"from": source, "to": target, "type": "registry_entry"})

        for used_by in symbol.get("used_by", []) if isinstance(symbol.get("used_by"), list) else []:
            if isinstance(used_by, str):
                skill = _target_for_name(used_by, files_by_path)
                capability = _target_for_name(name, files_by_path)
                if skill and capability:
                    edges.append({"from": capability, "to": skill, "type": "capability_used_by"})

        for required in symbol.get("required_capabilities", []) if isinstance(symbol.get("required_capabilities"), list) else []:
            if isinstance(required, str):
                target_required = _target_for_name(required, files_by_path)
                if target_required:
                    edges.append({"from": source, "to": target_required, "type": "skill_selects_capability"})

    for ref in file_node.get("references", []):
        if not isinstance(ref, dict):
            continue
        value = ref.get("value")
        if not isinstance(value, str):
            continue
        target = _existing_target(value, files_by_path) or _target_for_name(value, files_by_path)
        if target:
            edge_type = "routing_rule_reference" if source.endswith("routing-rules.yaml") else _edge_type_for_target(target)
            edges.append({"from": source, "to": target, "type": edge_type})
    return edges


def build_reference_edges(
    file_node: dict[str, object],
    files_by_path: dict[str, dict[str, object]],
) -> list[dict[str, str]]:
    kind = str(file_node.get("kind") or "")
    if kind == "markdown":
        return build_markdown_reference_edges(file_node, files_by_path)
    if kind in {"yaml", "json"}:
        return build_registry_edges(file_node, files_by_path)
    return []
