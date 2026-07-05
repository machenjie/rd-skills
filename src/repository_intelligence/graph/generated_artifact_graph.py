"""Generated artifact relationship helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any


GENERATED_SOURCE_GROUPS: dict[str, list[str]] = {
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
    "docs/SCORECARD_DASHBOARD.md": [
        "scripts/render-scorecard-dashboard.py",
        "reports/professional-scorecard.json",
        "README.md",
    ],
}


def is_generated_artifact_path(path: str) -> bool:
    """Return True when a repository path is generated or build output."""
    normalized = path.strip().lstrip("./")
    return (
        normalized == "dist"
        or normalized.startswith("dist/")
        or normalized == "reports"
        or normalized.startswith("reports/")
        or normalized == "docs/SCORECARD_DASHBOARD.md"
    )


def generated_source_of_truth(
    path: str,
    files_by_path: dict[str, dict[str, Any]],
) -> list[str]:
    """Return known source-of-truth paths for a generated path."""
    normalized = path.strip().lstrip("./")
    source_group = _source_group_for_generated(normalized)
    if not source_group:
        return []
    sources = GENERATED_SOURCE_GROUPS[source_group]
    return [source for source in sources if _source_exists(source, files_by_path)]


def generated_edit_policy(path: str, files_by_path: dict[str, dict[str, Any]]) -> str:
    """Return the edit policy for a generated path."""
    if not is_generated_artifact_path(path):
        return "edit source"
    if generated_source_of_truth(path, files_by_path):
        return "edit source / do not edit generated"
    return "unknown requires inspection"


def generated_reason(path: str, files_by_path: dict[str, dict[str, Any]]) -> str:
    """Return a human-readable generated artifact reason."""
    if generated_source_of_truth(path, files_by_path):
        return "generated artifact; change source inputs and rebuild instead of treating output as source-of-truth"
    return "generated artifact source-of-truth is unknown; inspect build ownership before editing"


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
    for generated_path, sources in GENERATED_SOURCE_GROUPS.items():
        source_of_truth = [source for source in sources if _source_exists(source, files_by_path)]
        confidence = "medium" if source_of_truth else "low"
        payload.append(
            {
                "generated_path": generated_path,
                "source_path": source_of_truth[0] if source_of_truth else None,
                "source_of_truth": source_of_truth,
                "validation_candidates": _validation_for_generated(generated_path),
                "editable": False,
                "reason": generated_reason(generated_path, files_by_path),
                "edit_policy": "edit source / do not edit generated"
                if source_of_truth
                else "unknown requires inspection",
                "confidence": confidence,
                "freshness": "not_applicable",
                "extractor": "generated_artifact_graph",
                **({"unknown_reason": "generated_source_of_truth_unknown"} if not source_of_truth else {}),
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
    if path == "docs/SCORECARD_DASHBOARD.md":
        return [
            "python3 scripts/render-scorecard-dashboard.py --scorecard reports/professional-scorecard.json --out docs/SCORECARD_DASHBOARD.md --readme README.md --check",
            "python3 scripts/validate-productization-assets.py",
        ]
    return ["python3 scripts/build.py --profile recommended"]


def _source_group_for_generated(path: str) -> str | None:
    if path == "docs/SCORECARD_DASHBOARD.md":
        return "docs/SCORECARD_DASHBOARD.md"
    normalized = path if path.endswith("/") else f"{path}/" if path in {"dist", "reports"} else path
    for generated_path in ("dist/", "reports/"):
        if normalized == generated_path or normalized.startswith(generated_path):
            return generated_path
    return None


def _source_exists(source: str, files_by_path: dict[str, dict[str, object]]) -> bool:
    if source in files_by_path:
        return True
    source_path = Path(source)
    if source_path.suffix:
        return False
    prefix = f"{source.rstrip('/')}/"
    return any(path == source.rstrip("/") or path.startswith(prefix) for path in files_by_path)
