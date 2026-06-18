"""Generated artifact relationship helpers."""

from __future__ import annotations


def build_generated_artifact_edges(files_by_path: dict[str, dict[str, object]]) -> list[dict[str, str]]:
    """Represent generated outputs without indexing dist content."""
    edges: list[dict[str, str]] = []
    if "scripts/build.py" in files_by_path:
        for source in (
            "src/professional-skills",
            "src/foundation/capabilities",
            "src/domain-extensions",
            "src/hook-runtime",
        ):
            edges.append({"from": source, "to": "dist/", "type": "generated_artifact"})
        edges.append({"from": "scripts/build.py", "to": "dist/", "type": "generated_artifact"})

    if "scripts/validate-hooks.py" in files_by_path:
        for path in files_by_path:
            if path.startswith("src/hook-runtime/templates/") or path.startswith("src/hook-runtime/scripts/"):
                edges.append({"from": path, "to": "scripts/validate-hooks.py", "type": "hook_template_reference"})
    return edges
