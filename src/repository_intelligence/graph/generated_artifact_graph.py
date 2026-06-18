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


def build_generated_artifact_payload(files_by_path: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    """Return source-to-generated artifact relationships without indexing dist."""
    payload: list[dict[str, object]] = []
    source_groups = {
        "dist/": [
            "src/professional-skills",
            "src/foundation/capabilities",
            "src/domain-extensions",
            "src/hook-runtime",
            "scripts/build.py",
        ],
        "reports/": [
            "scripts/eval-routing.py",
            "scripts/eval-skill-professionalism.py",
            "scripts/eval-professional-benchmarks.py",
            "scripts/render-scorecard-dashboard.py",
        ],
    }
    for generated_path, sources in source_groups.items():
        payload.append(
            {
                "generated_path": generated_path,
                "source_of_truth": [source for source in sources if source in files_by_path or not source.endswith(".py")],
                "validation_candidates": _validation_for_generated(generated_path),
                "editable": False,
                "reason": "generated artifact; change source inputs and rebuild instead of treating output as source-of-truth",
            }
        )
    return payload


def _validation_for_generated(path: str) -> list[str]:
    if path == "dist/":
        return [
            "python3 scripts/build.py --profile recommended",
            "python3 scripts/validate-runtime-reference-links.py",
            "python3 scripts/validate-installation.py",
        ]
    if path == "reports/":
        return [
            "python3 scripts/eval-routing.py",
            "python3 scripts/eval-skill-professionalism.py",
        ]
    return ["python3 scripts/build.py --profile recommended"]
