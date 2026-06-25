"""Classify ChangeForge skill behavior changes for validation closure."""

from __future__ import annotations

from fnmatch import fnmatch
from typing import Iterable


SKILL_BEHAVIOR_CHANGE_PATTERNS: tuple[tuple[str, str], ...] = (
    ("skill", "src/professional-skills/**"),
    ("capability", "src/foundation/capabilities/**"),
    ("skill", "src/domain-extensions/**"),
    ("router", "src/registry/**"),
    ("hook", "src/hook-runtime/**"),
    ("adapter", "src/runtime_governance/**"),
    ("validation", "src/validation_broker/**"),
    ("memory", "src/project_memory/**"),
    ("graph", "src/repository_intelligence/**"),
    ("trajectory", "src/trajectory/**"),
    ("validation", "evals/**"),
    ("validation", "scripts/eval-*.py"),
    ("validation", "scripts/validate-skill-efficacy-benchmarks.py"),
)

DOCS_ONLY_PATTERNS: tuple[str, ...] = (
    "README.md",
    "docs/**",
    "reports/**",
)

SURFACE_PRIORITY: tuple[str, ...] = (
    "router",
    "skill",
    "capability",
    "hook",
    "adapter",
    "validation",
    "graph",
    "memory",
    "trajectory",
)


def classify_skill_behavior_change(changed_paths: Iterable[str]) -> dict[str, object]:
    """Return a serializable skill-efficacy benchmark requirement summary."""
    paths = _clean_paths(changed_paths)
    matches: list[dict[str, str]] = []
    matched_surfaces: list[str] = []
    for path in paths:
        for surface, pattern in SKILL_BEHAVIOR_CHANGE_PATTERNS:
            if not fnmatch(path, pattern):
                continue
            matches.append({"path": path, "surface": surface, "pattern": pattern})
            if surface not in matched_surfaces:
                matched_surfaces.append(surface)

    docs_only = bool(paths) and not matches and all(_is_docs_only(path) for path in paths)
    requires = bool(matches)
    if requires:
        changed_surface = _primary_surface(matched_surfaces)
        reason = (
            "skill, routing, hook, memory, graph, validation, trajectory, or "
            "adapter behavior changed; skill efficacy benchmark evidence is required"
        )
    elif docs_only:
        changed_surface = "docs-only"
        reason = "changed paths are documentation or generated reports with no behavior surface"
    else:
        changed_surface = "unknown"
        reason = "no registered skill behavior change path matched"

    return {
        "schema_version": 1,
        "paths": paths,
        "path_matches": matches,
        "matched_surfaces": matched_surfaces,
        "changed_surface": changed_surface,
        "requires_skill_efficacy_benchmark": requires,
        "docs_only": docs_only,
        "reason": reason,
    }


def _clean_paths(paths: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    if isinstance(paths, str):
        paths = (paths,)
    for path in paths or ():
        text = str(path).replace("\\", "/").strip().lstrip("./")
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _is_docs_only(path: str) -> bool:
    return any(fnmatch(path, pattern) for pattern in DOCS_ONLY_PATTERNS)


def _primary_surface(surfaces: list[str]) -> str:
    for surface in SURFACE_PRIORITY:
        if surface in surfaces:
            return surface
    return surfaces[0] if surfaces else "unknown"
