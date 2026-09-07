"""Render evaluator assignments for exact context measurement; no runtime protocol.

The consumer measures the text actually handed to a selected Profile. No digest,
readiness record, or mandatory Brief/Review is needed to render an assignment.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Any

from validation_utils import load_yaml_file, professional_routing_authority


class FixtureCapsuleError(ValueError):
    pass


@lru_cache(maxsize=1)
def _source_rows():
    root = Path(__file__).resolve().parents[1]
    return {row["name"]: row for filename, key in (
        ("professional-skills.yaml", "professional_skills"),
        ("foundation-skills.yaml", "foundation_skills"),
        ("domain-skills.yaml", "domain_skills"),
    ) for row in load_yaml_file(root / "src/registry" / filename)[key]}


def runtime_layer3_reference_path(value: object, label: str = "layer3_reference") -> str:
    if not isinstance(value, str) or not re.fullmatch(
        r"references/layer3/[a-z0-9-]+/references/[a-z0-9-]+\.md", value
    ) or PurePosixPath(value).name in {"index.md", "catalog.md"}:
        raise FixtureCapsuleError(f"{label} must name one exact nested Layer 3 Reference")
    return value


def validate_and_render_fixture_capsule(step: dict[str, Any]) -> str:
    """Check the real role/expertise boundary and render only needed instructions."""
    role = step.get("profile")
    primary = step.get("primary_skill")
    authority = professional_routing_authority()
    if primary not in authority["primary_skills_by_profile"].get(role, []):
        raise FixtureCapsuleError("Primary Professional is not authorized for this Profile")
    layer3 = step.get("layer3_skills", [])
    if not isinstance(layer3, list) or len(layer3) > 3 or len(set(layer3)) != len(layer3):
        raise FixtureCapsuleError("Layer 3 selection must contain zero to three unique Skills")
    if any(name not in authority["layer3_candidates_by_primary"][primary] for name in layer3):
        raise FixtureCapsuleError("Layer 3 selection is not authorized for the Primary Professional")
    rows = _source_rows()
    if any(role not in rows[name]["role_support"] for name in layer3):
        raise FixtureCapsuleError("Layer 3 selection is not authorized for this Profile")
    root = Path(__file__).resolve().parents[1]
    for path in step.get("professional_references", []):
        entry = next((item for item in rows[primary].get("reference_index", []) if item["path"] == path), None)
        if not entry or role not in entry["required_by"] or not (root / rows[primary]["path"] / path).is_file():
            raise FixtureCapsuleError("Professional Reference must be current and authorized for this Profile")
    goal = step.get("goal")
    if not isinstance(goal, str) or not goal.strip():
        raise FixtureCapsuleError("assignment needs a concrete goal")
    lines = [goal, "", f"Primary Professional: {primary}"]
    if step.get("constraints"):
        lines.extend(["", "Constraints:", *[f"- {item}" for item in step["constraints"]]])
    if step.get("write_scope"):
        lines.extend(["", "Write scope:", *[f"- {item}" for item in step["write_scope"]]])
    if step.get("validation"):
        lines.extend(["", f"Validation: {step['validation']}"])
    if step.get("brief"):
        lines.extend(["", step["brief"]])
    lines.extend(["", "## Layer 3 Delivery"])
    lines.extend(f"- {name}" for name in layer3)
    for path in step.get("layer3_references", []):
        runtime_layer3_reference_path(path)
        if PurePosixPath(path).parts[2] not in layer3:
            raise FixtureCapsuleError("nested Reference owner was not selected")
        owner = PurePosixPath(path).parts[2]
        local = "references/" + PurePosixPath(path).name
        entry = next((item for item in rows[owner].get("reference_index", []) if item["path"] == local), None)
        if not entry or role not in entry["required_by"] or not (root / rows[owner]["path"] / local).is_file():
            raise FixtureCapsuleError("nested Reference must be current and authorized for this Profile")
        lines.append(f"- {path}")
    return "\n".join(lines).rstrip() + "\n"
