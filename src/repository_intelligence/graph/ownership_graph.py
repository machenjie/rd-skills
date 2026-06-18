"""Ownership-style graph helpers for registry owned source files."""

from __future__ import annotations


def build_ownership_edges(files_by_path: dict[str, dict[str, object]]) -> list[dict[str, str]]:
    """Connect SKILL.md files to their nearest registry owner when known.

    rd-skills currently expresses ownership through registries, so this module
    is intentionally conservative and only adds explicit source-to-registry
    backlinks for common skill/capability roots.
    """
    edges: list[dict[str, str]] = []
    registry_for_prefix = {
        "src/foundation/capabilities/": "src/registry/capabilities.yaml",
        "src/professional-skills/": "src/registry/skills.yaml",
        "src/domain-extensions/": "src/registry/domain-extensions.yaml",
    }
    for path in files_by_path:
        if not path.endswith("/SKILL.md"):
            continue
        for prefix, registry in registry_for_prefix.items():
            if path.startswith(prefix) and registry in files_by_path:
                edges.append({"from": path, "to": registry, "type": "registry_entry"})
    return edges
