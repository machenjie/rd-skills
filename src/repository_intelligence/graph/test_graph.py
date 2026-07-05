"""Heuristic test-to-source graph edges."""

from __future__ import annotations

from pathlib import Path


def _source_names(path: str) -> set[str]:
    stem = Path(path).stem
    names = {stem}
    if stem.startswith("test_"):
        names.add(stem.removeprefix("test_"))
    if stem.endswith("_test"):
        names.add(stem.removesuffix("_test"))
    return names


def build_test_edges(files_by_path: dict[str, dict[str, object]]) -> list[dict[str, str]]:
    edges: list[dict[str, str]] = []
    tests = [path for path, node in files_by_path.items() if node.get("role") == "test"]
    sources = [path for path, node in files_by_path.items() if node.get("role") != "test"]
    for test_path in tests:
        names = _source_names(test_path)
        for source_path in sources:
            if Path(source_path).stem in names:
                edges.append({"from": test_path, "to": source_path, "type": "test_reference"})
    return edges
