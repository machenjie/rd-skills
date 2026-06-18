"""YAML and JSON registry reference extraction."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from repository_intelligence.graph.file_classifier import normalize_repo_path


PATH_KEYS = {
    "path",
    "paths",
    "file",
    "files",
    "script",
    "scripts",
    "template",
    "templates",
    "validator",
    "validators",
    "doc",
    "docs",
    "reference",
    "references",
}

NAME_KEYS = {
    "name",
    "capability",
    "capabilities",
    "required_capabilities",
    "required_gates",
    "skills",
    "used_by",
    "domain_extensions",
    "route_to",
    "skill",
}


def _load_validation_utils(repo_root: str | Path | None = None) -> Any | None:
    candidates: list[Path] = []
    if repo_root is not None:
        candidates.append(Path(repo_root).resolve() / "scripts")
    candidates.append(Path(__file__).resolve().parents[3] / "scripts")
    for candidate in candidates:
        if candidate.exists() and str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))
    try:
        import validation_utils  # type: ignore
    except Exception:
        return None
    return validation_utils


def load_structured_file(path: str | Path, repo_root: str | Path | None = None) -> dict[str, Any]:
    file_path = Path(path)
    if file_path.suffix.lower() == ".json":
        return json.loads(file_path.read_text(encoding="utf-8"))
    validation_utils = _load_validation_utils(repo_root)
    if validation_utils is None:
        raise RuntimeError("validation_utils is required to parse YAML without PyYAML")
    return validation_utils.load_yaml_file(file_path)


def _as_items(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return [value]


def _walk_references(value: Any, key_path: tuple[str, ...] = ()) -> list[dict[str, object]]:
    references: list[dict[str, object]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            key_lower = key_text.lower()
            if key_lower in PATH_KEYS:
                for item in _as_items(child):
                    if isinstance(item, str):
                        references.append(
                            {
                                "kind": "path",
                                "key": key_text,
                                "value": item,
                                "path": ".".join((*key_path, key_text)),
                            }
                        )
            elif key_lower in NAME_KEYS:
                for item in _as_items(child):
                    if isinstance(item, str):
                        references.append(
                            {
                                "kind": "name",
                                "key": key_text,
                                "value": item,
                                "path": ".".join((*key_path, key_text)),
                            }
                        )
            references.extend(_walk_references(child, (*key_path, key_text)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            references.extend(_walk_references(child, (*key_path, str(index))))
    return references


def _registry_entries(data: dict[str, Any]) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for collection_name in ("capabilities", "skills", "domain_extensions", "routes", "rules"):
        collection = data.get(collection_name)
        if not isinstance(collection, list):
            continue
        for item in collection:
            if not isinstance(item, dict):
                continue
            name = item.get("name") or item.get("id") or item.get("route_to")
            if not isinstance(name, str):
                continue
            entries.append(
                {
                    "name": name,
                    "kind": "registry_entry",
                    "collection": collection_name,
                    "path": item.get("path"),
                    "used_by": item.get("used_by", []),
                    "required_capabilities": item.get("required_capabilities", []),
                    "required_gates": item.get("required_gates", []),
                    "route_to": item.get("route_to"),
                }
            )
    return entries


def extract_structured_data(data: dict[str, Any]) -> dict[str, list[dict[str, object]]]:
    return {
        "symbols": _registry_entries(data),
        "references": _walk_references(data),
    }


def extract_structured_file(path: str | Path, repo_root: str | Path | None = None) -> dict[str, object]:
    file_path = Path(path)
    data = load_structured_file(file_path, repo_root)
    extracted = extract_structured_data(data)
    extracted["path"] = normalize_repo_path(file_path, repo_root)
    extracted["frontmatter"] = {
        "schema_version": data.get("schema_version"),
        "kind": data.get("kind"),
        "description": data.get("description"),
    }
    return extracted
