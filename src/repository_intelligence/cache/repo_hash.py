"""Stable repository hash calculation for indexed source content."""

from __future__ import annotations

import hashlib
from pathlib import Path

from repository_intelligence.graph.file_classifier import should_index


def iter_indexed_files(repo_root: str | Path) -> list[Path]:
    """Return indexed source files in deterministic relative-path order."""
    root = Path(repo_root).resolve()
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if should_index(relative):
            files.append(relative)
    return sorted(files, key=lambda item: item.as_posix())


def stable_repo_hash(repo_root: str | Path) -> str:
    """Hash indexed file paths and bytes without recording absolute paths."""
    root = Path(repo_root).resolve()
    digest = hashlib.sha256()
    for relative in iter_indexed_files(root):
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update((root / relative).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()

