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

# A versioned simulated installation input, not a discovered real Host path.
# Evaluators map this root to their actual built Professional root when reading.
FIXTURE_HOST_SKILLS_ROOT = Path("/rd-skills-fixture/skills")


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


def validate_and_render_fixture_capsule(
    step: dict[str, Any], *, professional_root: Path | None = None,
) -> str:
    """Check the real role/expertise boundary and render only needed instructions."""
    role = step.get("profile")
    primary = step.get("primary_skill")
    authority = professional_routing_authority()
    if primary not in authority["primary_skills_by_profile"].get(role, []):
        raise FixtureCapsuleError("Primary Professional is not authorized for this Profile")
    layer3 = step.get("layer3_skills", [])
    if not isinstance(layer3, list) or len(set(layer3)) != len(layer3):
        raise FixtureCapsuleError("Layer 3 selection must contain an ordered list of unique Skills")
    if any(name not in authority["layer3_candidates_by_primary"][primary] for name in layer3):
        raise FixtureCapsuleError("Layer 3 selection is not authorized for the Primary Professional")
    rows = _source_rows()
    if any(role not in rows[name]["role_support"] for name in layer3):
        raise FixtureCapsuleError("Layer 3 selection is not authorized for this Profile")
    root = Path(__file__).resolve().parents[1]
    for field in ("professional_references", "layer3_references"):
        values = step.get(field)
        if values is not None and (not isinstance(values, list)
                or not all(isinstance(value, str) for value in values)
                or len(values) != len(set(values))):
            raise FixtureCapsuleError(f"{field} must be unresolved or an ordered unique list")
    for path in step.get("professional_references") or []:
        entry = next((item for item in rows[primary].get("reference_index", []) if item["path"] == path), None)
        if not entry or role not in entry["required_by"] or not (root / rows[primary]["path"] / path).is_file():
            raise FixtureCapsuleError("Professional Reference must be current and authorized for this Profile")
    goal = step.get("goal")
    if not isinstance(goal, str) or not goal.strip():
        raise FixtureCapsuleError("assignment needs a concrete goal")
    # A caller can supply its actual Host root. The evaluator default is a fixed
    # simulated installation, independent of temporary checkout locations.
    host_root = professional_root if professional_root is not None else FIXTURE_HOST_SKILLS_ROOT / primary
    if (not isinstance(host_root, Path) or not host_root.is_absolute()
            or ".." in host_root.parts or host_root.name != primary):
        raise FixtureCapsuleError("Host Professional root must be an absolute path for the assigned Primary")
    lines = [goal, "", f"Primary Professional Skill: {host_root / 'SKILL.md'}"]
    if step.get("constraints"):
        lines.extend(["", "Constraints:", *[f"- {item}" for item in step["constraints"]]])
    if step.get("write_scope"):
        lines.extend(["", "Write scope:", *[f"- {item}" for item in step["write_scope"]]])
    if step.get("validation"):
        lines.extend(["", f"Validation: {step['validation']}"])
    if step.get("brief"):
        lines.extend(["", step["brief"]])
    lines.extend(["", "Layer 3 exact:" + ("" if layer3 else " []")])
    lines.extend(f"- {host_root / 'references/layer3' / (name + '.md')}" for name in layer3)
    lines.extend(["", "## Reference Delivery"])
    for path in step.get("professional_references") or []:
        lines.append(f"- {host_root / path}")
    for path in step.get("layer3_references") or []:
        runtime_layer3_reference_path(path)
        if PurePosixPath(path).parts[2] not in layer3:
            raise FixtureCapsuleError("nested Reference owner was not selected")
        owner = PurePosixPath(path).parts[2]
        local = "references/" + PurePosixPath(path).name
        entry = next((item for item in rows[owner].get("reference_index", []) if item["path"] == local), None)
        if not entry or role not in entry["required_by"] or not (root / rows[owner]["path"] / local).is_file():
            raise FixtureCapsuleError("nested Reference must be current and authorized for this Profile")
        lines.append(f"- {host_root / path}")
    unresolved_owners = ([primary] if step.get("professional_references") is None else [])
    if step.get("layer3_references") is None:
        unresolved_owners.extend(layer3)
    if unresolved_owners:
        lines.append("References unresolved for: " + ", ".join(unresolved_owners) + ". Exact Layer 3 skips only Layer 3 selection.")
        lines.append("Read these owner partitions directly for Reference loading rules:")
        lines.extend(f"- {host_root / 'references/runtime/reference-records' / (owner + '.json')}" for owner in unresolved_owners)
        lines.append("Match required_by, load_when, do_not_load_when and required_output; honor any context_admissibility relationships. Read each needed record.path verbatim under the Primary Professional Host root after safe relative-path validation. No catalog preload or inferred roots.")
    else:
        lines.append("References exact: " + ("as listed above" if step.get("professional_references") or step.get("layer3_references") else "[]") + "; skip Reference selection.")
    return "\n".join(lines).rstrip() + "\n"
