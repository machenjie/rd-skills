"""Classify repository files for graph extraction."""

from __future__ import annotations

from pathlib import Path


EXCLUDED_DIRS = {
    ".git",
    "dist",
    "__pycache__",
    ".cache",
    "node_modules",
    ".venv",
}

INDEXED_SUFFIXES = {
    ".py",
    ".md",
    ".sh",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".go",
    ".rs",
    ".java",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
}


def normalize_repo_path(path: str | Path, repo_root: str | Path | None = None) -> str:
    """Return a stable POSIX path relative to the repository root."""
    raw = Path(path)
    if repo_root is not None:
        root = Path(repo_root).resolve()
        try:
            raw = raw.resolve().relative_to(root)
        except (OSError, ValueError):
            pass
    return raw.as_posix().lstrip("./")


def is_excluded(path: str | Path) -> bool:
    """Return True when any path segment is excluded from source indexing."""
    parts = Path(path).parts
    return any(part in EXCLUDED_DIRS for part in parts)


def should_index(path: str | Path) -> bool:
    """Return True when a file should be included in the source graph."""
    candidate = Path(path)
    if is_excluded(candidate):
        return False
    if candidate.name == "SKILL.md":
        return True
    return candidate.suffix.lower() in INDEXED_SUFFIXES


def classify_kind(path: str | Path) -> str:
    """Classify a file by deterministic syntax extractor kind."""
    candidate = Path(path)
    suffix = candidate.suffix.lower()
    if suffix == ".py":
        return "python"
    if candidate.name == "SKILL.md" or suffix == ".md":
        return "markdown"
    if suffix in {".yaml", ".yml"}:
        return "yaml"
    if suffix == ".json":
        return "json"
    if suffix == ".sh":
        return "shell"
    if suffix in {".js", ".jsx", ".ts", ".tsx"}:
        return "javascript"
    if suffix == ".go":
        return "go"
    if suffix == ".rs":
        return "rust"
    if suffix == ".java":
        return "java"
    if suffix == ".toml":
        return "toml"
    return "unknown"


def classify_role(path: str | Path) -> str:
    """Classify the ChangeForge repository role for a relative path."""
    rel = normalize_repo_path(path)
    parts = rel.split("/")
    name = parts[-1] if parts else rel

    if parts and parts[0] == "dist":
        return "generated_artifact"
    if rel.startswith("src/hook-runtime/"):
        return "hook_runtime"
    if rel.startswith("src/registry/"):
        return "registry"
    if rel.startswith("src/foundation/capabilities/"):
        return "capability"
    if rel.startswith("src/professional-skills/"):
        return "skill"
    if rel.startswith("src/domain-extensions/"):
        return "domain_extension"
    if rel.startswith("tests/"):
        return "test"
    if rel.startswith("evals/"):
        return "eval"
    if rel.startswith("docs/") or name in {"README.md", "CHANGELOG.md", "AGENTS.md"}:
        return "docs"
    if rel.startswith("scripts/validate-") or rel.startswith("scripts/eval-"):
        return "validator"
    if rel.startswith("scripts/"):
        return "script"
    if rel.startswith("reports/"):
        return "generated_artifact"
    return "unknown"
