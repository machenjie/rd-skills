"""Build import edges from extracted Python imports."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable


def _candidate_files(base: Path) -> Iterable[Path]:
    yield base.with_suffix(".py")
    yield base / "__init__.py"


def resolve_import(
    import_ref: dict[str, object],
    current_path: str,
    repo_root: str | Path,
) -> str | None:
    """Resolve a Python import to a repository-relative file when local."""
    root = Path(repo_root).resolve()
    current = root / current_path
    module = str(import_ref.get("module") or "")
    level = int(import_ref.get("level") or 0)
    module_parts = [part for part in module.split(".") if part]

    bases: list[Path] = []
    if level > 0:
        base = current.parent
        for _ in range(level - 1):
            base = base.parent
        bases.append(base.joinpath(*module_parts))
    else:
        for prefix in (root, root / "src", root / "scripts", current.parent):
            bases.append(prefix.joinpath(*module_parts))

    for base in bases:
        for candidate in _candidate_files(base):
            if candidate.exists() and candidate.is_file():
                try:
                    return candidate.relative_to(root).as_posix()
                except ValueError:
                    return None
    return None


def build_import_edges(
    file_node: dict[str, object],
    repo_root: str | Path,
) -> list[dict[str, str]]:
    source = str(file_node["path"])
    edges: list[dict[str, str]] = []
    for import_ref in file_node.get("imports", []):
        if not isinstance(import_ref, dict):
            continue
        target = resolve_import(import_ref, source, repo_root)
        if target:
            edges.append({"from": source, "to": target, "type": "import"})
    return edges
