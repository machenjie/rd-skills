"""Repository freshness metadata for graph and context-pack outputs."""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

from repository_intelligence.cache.repo_hash import (
    iter_source_files,
    stable_artifact_hash,
    stable_repo_hash,
)


def indexed_at_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def indexed_commit(repo_root: str | Path) -> str | None:
    """Return HEAD commit when git metadata is available."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(Path(repo_root).resolve()),
            text=True,
            capture_output=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    commit = result.stdout.strip()
    return commit or None


def fallback_mtime(repo_root: str | Path) -> float | None:
    """Return newest indexed source mtime when git commit metadata is absent."""
    root = Path(repo_root).resolve()
    mtimes = [(root / relative).stat().st_mtime for relative in iter_source_files(root)]
    return max(mtimes) if mtimes else None


def freshness_metadata(repo_root: str | Path) -> dict[str, object]:
    commit = indexed_commit(repo_root)
    metadata: dict[str, object] = {
        "repo_hash": stable_repo_hash(repo_root),
        "artifact_hash": stable_artifact_hash(repo_root),
        "indexed_at": indexed_at_now(),
        "indexed_commit": commit,
    }
    if commit is None:
        metadata["fallback_mtime"] = fallback_mtime(repo_root)
    return metadata
