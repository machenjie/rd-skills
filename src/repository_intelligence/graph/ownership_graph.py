"""Ownership-style graph helpers for repository-intelligence payloads."""

from __future__ import annotations

from pathlib import Path


DUMPING_GROUND_SEGMENTS = {"common", "commons", "shared", "utils", "util", "helpers", "helper"}


def owner_for_path(path: str) -> dict[str, object]:
    """Return conservative ownership metadata for an rd-skills repository path."""
    parts = path.split("/")
    role = _owner_surface(path)
    owner_module = _owner_module(path)
    return {
        "path": path,
        "owner_surface": role,
        "owner_module": owner_module,
        "owner_object_or_function": _owner_object(path),
        "public_private_boundary": _public_private_boundary(path),
        "sibling_conventions": [],
        "rejected_dumping_ground_candidates": _dumping_ground_rejections(path),
        "package_or_module_root": "/".join(parts[:3]) if len(parts) >= 3 else (parts[0] if parts else ""),
    }


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


def build_ownership_payload(files_by_path: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    """Return per-file ownership facts used by context packs and validators."""
    siblings_by_dir: dict[str, list[str]] = {}
    for path in files_by_path:
        siblings_by_dir.setdefault(str(Path(path).parent), []).append(path)

    payload: list[dict[str, object]] = []
    for path in sorted(files_by_path):
        item = owner_for_path(path)
        sibling_names = [
            Path(sibling).name
            for sibling in sorted(siblings_by_dir.get(str(Path(path).parent), []))
            if sibling != path
        ][:8]
        item["sibling_conventions"] = sibling_names
        payload.append(item)
    return payload


def build_module_boundaries(files_by_path: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    """Summarize module boundaries from file ownership facts."""
    boundaries: dict[str, dict[str, object]] = {}
    ownership = build_ownership_payload(files_by_path)
    for item in ownership:
        module = str(item["owner_module"])
        boundary = boundaries.setdefault(
            module,
            {
                "owner_module": module,
                "owner_surface": item["owner_surface"],
                "root_paths": set(),
                "public_paths": [],
                "private_paths": [],
                "test_paths": [],
                "generated_paths": [],
                "rejected_dumping_ground_candidates": [],
            },
        )
        path = str(item["path"])
        root = str(item.get("package_or_module_root") or path.split("/", 1)[0])
        boundary["root_paths"].add(root)  # type: ignore[union-attr]
        if path.startswith("tests/"):
            boundary["test_paths"].append(path)  # type: ignore[union-attr]
        elif str(item.get("owner_surface")) == "generated_artifact":
            boundary["generated_paths"].append(path)  # type: ignore[union-attr]
        elif item.get("public_private_boundary") == "public_contract":
            boundary["public_paths"].append(path)  # type: ignore[union-attr]
        else:
            boundary["private_paths"].append(path)  # type: ignore[union-attr]
        boundary["rejected_dumping_ground_candidates"].extend(  # type: ignore[union-attr]
            item.get("rejected_dumping_ground_candidates", [])
            if isinstance(item.get("rejected_dumping_ground_candidates"), list)
            else []
        )

    result: list[dict[str, object]] = []
    for boundary in boundaries.values():
        result.append(
            {
                **boundary,
                "root_paths": sorted(boundary["root_paths"]),  # type: ignore[index]
                "public_paths": list(boundary["public_paths"])[:24],  # type: ignore[index]
                "private_paths": list(boundary["private_paths"])[:24],  # type: ignore[index]
                "test_paths": list(boundary["test_paths"])[:24],  # type: ignore[index]
                "generated_paths": list(boundary["generated_paths"])[:24],  # type: ignore[index]
                "rejected_dumping_ground_candidates": list(
                    boundary["rejected_dumping_ground_candidates"]  # type: ignore[index]
                )[:24],
            }
        )
    return sorted(result, key=lambda item: str(item["owner_module"]))


def _owner_surface(path: str) -> str:
    if path.startswith("src/foundation/capabilities/"):
        return "capability"
    if path.startswith("src/professional-skills/"):
        return "professional_skill"
    if path.startswith("src/domain-extensions/"):
        return "domain_extension"
    if path.startswith("src/hook-runtime/"):
        return "hook_runtime"
    if path.startswith("src/repository_intelligence/"):
        return "repository_intelligence"
    if path.startswith("src/validation_broker/"):
        return "validation_broker"
    if path.startswith("src/runtime_governance/"):
        return "runtime_governance"
    if path.startswith("src/trajectory/"):
        return "trajectory"
    if path.startswith("src/project_memory/"):
        return "project_memory"
    if path.startswith("src/registry/"):
        return "registry"
    if path.startswith("tests/"):
        return "test"
    if path.startswith("docs/") or path in {"README.md", "AGENTS.md"}:
        return "docs"
    if path.startswith("evals/") or path.startswith("scripts/eval-"):
        return "evals"
    if path.startswith("reports/") or path.startswith("dist/"):
        return "generated_artifact"
    if path.startswith("installers/") or path.startswith("profiles/") or path == "scripts/build.py":
        return "installer_build_profile"
    if path.startswith("scripts/"):
        return "script"
    if path.startswith("src/"):
        return "source"
    return "unknown"


def _owner_module(path: str) -> str:
    parts = path.split("/")
    if path.startswith("src/foundation/capabilities/") and len(parts) >= 4:
        return f"capability:{parts[3]}"
    if path.startswith("src/professional-skills/") and len(parts) >= 3:
        return f"skill:{parts[2]}"
    if path.startswith("src/domain-extensions/") and len(parts) >= 3:
        return f"domain_extension:{parts[2]}"
    if path.startswith("tests/") and len(parts) >= 2:
        return f"tests:{parts[1]}"
    surface = _owner_surface(path)
    if surface != "unknown":
        return surface
    return "unknown"


def _owner_object(path: str) -> str:
    name = Path(path).name
    if name == "SKILL.md":
        parts = path.split("/")
        return parts[-2] if len(parts) >= 2 else name
    return Path(path).stem


def _public_private_boundary(path: str) -> str:
    name = Path(path).name
    if name == "SKILL.md" or path.startswith("src/registry/") or path.startswith("scripts/"):
        return "public_contract"
    if name.startswith("_") or "/_" in path:
        return "private_internal"
    if path.startswith("tests/"):
        return "test_contract"
    return "module_internal"


def _dumping_ground_rejections(path: str) -> list[dict[str, str]]:
    parts = {part.casefold() for part in Path(path).parts}
    if not parts & DUMPING_GROUND_SEGMENTS:
        return []
    return [
        {
            "path": path,
            "reason": "shared/common/utils/helpers locations are rejected unless the code is pure technical utility with a named owner",
        }
    ]
