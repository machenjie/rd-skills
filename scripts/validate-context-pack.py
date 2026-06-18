#!/usr/bin/env python3
"""Validate ChangeForge TaskContextPack JSON documents."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"sk_live_[A-Za-z0-9]+"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(password|token|secret|api[_-]?key)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{8,}"),
]


def _payload(document: dict[str, Any]) -> dict[str, Any]:
    if "task_context_pack" not in document or not isinstance(document["task_context_pack"], dict):
        raise ValueError("missing task_context_pack object")
    return document["task_context_pack"]


def _has_secret_like(value: Any) -> bool:
    text = json.dumps(value, sort_keys=True)
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def _is_user_absolute_path(path: str) -> bool:
    return path.startswith(("/Users/", "/home/")) or re.match(r"^[A-Za-z]:\\\\Users\\\\", path) is not None


def _path_values(items: list[Any], key: str = "path") -> set[str]:
    values: set[str] = set()
    for item in items:
        if isinstance(item, dict) and isinstance(item.get(key), str):
            values.add(item[key])
    return values


def validate_context_pack(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    try:
        pack = _payload(document)
    except ValueError as exc:
        return [str(exc)]

    schema_version = pack.get("schema_version")
    if schema_version not in {1, 2}:
        errors.append("task_context_pack.schema_version must be 1 or 2")
    if not pack.get("task_goal") and not pack.get("task"):
        errors.append("task_context_pack.task_goal or task must be present")

    freshness = pack.get("freshness") if schema_version == 2 else pack.get("freshness_markers")
    if not isinstance(freshness, dict):
        freshness = pack.get("freshness_markers")
    if not isinstance(freshness, dict):
        errors.append("task_context_pack.freshness or freshness_markers must be present")
        freshness = {}
    if not freshness.get("repo_hash"):
        errors.append("freshness_markers.repo_hash must be present")
    elif _is_user_absolute_path(str(freshness.get("repo_hash"))):
        errors.append("freshness_markers.repo_hash must not contain an absolute path")
    if not freshness.get("indexed_at"):
        errors.append("freshness_markers.indexed_at must be present")

    source_paths = _path_values(pack.get("source_of_truth", []))
    evidence_text = "\n".join(str(item) for item in pack.get("evidence_limits", []))
    for path in pack.get("changed_paths", []):
        if not isinstance(path, str):
            errors.append("changed_paths entries must be strings")
            continue
        if _is_user_absolute_path(path):
            errors.append(f"changed path must be repository-relative: {path}")
        if path.startswith("dist/"):
            if path not in evidence_text:
                errors.append(f"generated changed path needs evidence limit: {path}")
        elif path not in source_paths and path not in evidence_text:
            errors.append(f"changed path needs source_of_truth or evidence_limits explanation: {path}")

    validations = pack.get("validation_candidates")
    if not isinstance(validations, list) or not validations:
        errors.append("validation_candidates must include at least one command or unknown explanation")
    else:
        for index, item in enumerate(validations):
            if not isinstance(item, dict) or not item.get("command") or not item.get("proves"):
                errors.append(f"validation_candidates[{index}] must include command and proves")
            if schema_version == 2 and isinstance(item, dict) and not item.get("scope"):
                errors.append(f"validation_candidates[{index}] must include scope for schema_version=2")

    for collection_name in (
        "source_of_truth",
        "relevant_files",
        "selected_files",
        "affected_tests",
        "related_tests",
        "excluded_context",
        "reuse_candidates",
        "rejected_locations",
        "omitted_nodes",
    ):
        collection = pack.get(collection_name, [])
        if not isinstance(collection, list):
            errors.append(f"{collection_name} must be a list")
            continue
        for item in collection:
            if isinstance(item, dict) and isinstance(item.get("path"), str) and _is_user_absolute_path(item["path"]):
                errors.append(f"{collection_name}.path must be repository-relative: {item['path']}")

    if any(
        isinstance(item, dict) and str(item.get("path", "")).startswith("dist/")
        for item in pack.get("source_of_truth", [])
    ):
        errors.append("dist must not appear as source_of_truth")
    if schema_version == 2:
        for field in (
            "graph_source",
            "selected_files",
            "selected_symbols",
            "caller_callee_edges",
            "imports",
            "references",
            "related_tests",
            "generated_artifacts",
            "ownership",
            "reuse_candidates",
            "rejected_locations",
            "anti_bloat_decision",
            "omitted_nodes",
            "residual_risk",
        ):
            if field not in pack:
                errors.append(f"task_context_pack.{field} is required for schema_version=2")
        if not isinstance(pack.get("anti_bloat_decision"), dict):
            errors.append("anti_bloat_decision must be an object for schema_version=2")
        for index, item in enumerate(pack.get("ownership", []) if isinstance(pack.get("ownership"), list) else []):
            if not isinstance(item, dict):
                errors.append(f"ownership[{index}] must be an object")
                continue
            for field in ("path", "owner_surface", "owner_module", "public_private_boundary"):
                if not item.get(field):
                    errors.append(f"ownership[{index}].{field} is required")
    if _has_secret_like(document):
        errors.append("context pack contains secret-like content")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context-pack", required=True, help="TaskContextPack JSON path.")
    args = parser.parse_args(argv)
    document = json.loads(Path(args.context_pack).read_text(encoding="utf-8"))
    errors = validate_context_pack(document)
    if errors:
        for error in errors:
            print(f"validate-context-pack: ERROR: {error}")
        return 1
    pack = document["task_context_pack"]
    print(
        "validate-context-pack: validated "
        f"{len(pack.get('relevant_files', []))} relevant files and "
        f"{len(pack.get('validation_candidates', []))} validation candidates"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
