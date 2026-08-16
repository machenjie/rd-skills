#!/usr/bin/env python3
"""Export a source-derived hookless rd-skills Skill discovery index."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from validation_utils import (
    FOUNDATION_DELIVERY_SCOPES,
    MARKETPLACE_SCHEMA_VERSION,
    REGISTRY_SCHEMA_VERSIONS,
    ValidationProblem,
    load_yaml_file,
    parse_frontmatter,
    reference_paths,
    role_contract_map_errors,
)


ROOT = Path(__file__).resolve().parents[1]
PROFILES = ("recommended", "full", "dev")
REGISTRIES = (
    ("control_skill", "control-skills.yaml", "control_skills"),
    ("professional_skill", "professional-skills.yaml", "professional_skills"),
    ("foundation_skill", "foundation-skills.yaml", "foundation_skills"),
    ("domain_skill", "domain-skills.yaml", "domain_skills"),
)
REGISTRY_SCHEMA_BY_ITEM_TYPE = {
    "control_skill": REGISTRY_SCHEMA_VERSIONS["control"],
    "professional_skill": REGISTRY_SCHEMA_VERSIONS["professional"],
    "foundation_skill": REGISTRY_SCHEMA_VERSIONS["foundation"],
    "domain_skill": REGISTRY_SCHEMA_VERSIONS["domain"],
}
CONTRACT_FIELDS = (
    "role_support",
    "trigger_signals",
    "anti_trigger_signals",
    "required_inputs",
    "output_contract",
    "escalation_signals",
    "reference_index",
)


class MarketplaceExportError(RuntimeError):
    """Raised when source data cannot produce a trustworthy discovery index."""


def _string_list(value: Any, *, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise MarketplaceExportError(f"{label} must be a non-empty list")
    result: list[str] = []
    for item in value:
        text = str(item).strip()
        if not text:
            raise MarketplaceExportError(f"{label} must contain non-empty strings")
        result.append(text)
    return result


def _optional_string_list(value: Any, *, label: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise MarketplaceExportError(f"{label} must be a list")
    result: list[str] = []
    for item in value:
        text = str(item).strip()
        if not text:
            raise MarketplaceExportError(f"{label} must contain non-empty strings")
        result.append(text)
    return result


def _reference_path_list(value: Any, *, label: str, owner: str) -> list[str]:
    """Project Registry JIT contracts to stable marketplace discovery paths."""

    try:
        return reference_paths(value, label, owner=owner)
    except ValidationProblem as exc:
        raise MarketplaceExportError(str(exc)) from exc


def _required_inputs_by_role(value: Any, *, label: str) -> dict[str, list[str]]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise MarketplaceExportError(f"{label} must be a mapping")
    result: dict[str, list[str]] = {}
    for role, inputs in value.items():
        role_name = str(role).strip()
        if not role_name:
            raise MarketplaceExportError(f"{label} must use non-empty role names")
        result[role_name] = _string_list(
            inputs, label=f"{label}.{role_name}"
        )
    return result


def _validated_role_map(
    entry: dict[str, Any], field: str, roles: list[str], *, label: str
) -> dict[str, list[str]]:
    value = entry.get(field)
    errors = role_contract_map_errors(value, roles, label)
    if errors:
        raise MarketplaceExportError("; ".join(errors))
    return _required_inputs_by_role(value, label=label)


def _frontmatter_summary(root: Path, source_path: str) -> str:
    skill_path = root / source_path / "SKILL.md"
    if not skill_path.is_file():
        raise MarketplaceExportError(f"{skill_path.relative_to(root)} is missing")
    try:
        frontmatter, _, _ = parse_frontmatter(skill_path)
    except Exception as exc:
        raise MarketplaceExportError(
            f"{skill_path.relative_to(root)} frontmatter is invalid: {exc}"
        ) from exc
    summary = str(frontmatter.get("description") or "").strip()
    if not summary:
        raise MarketplaceExportError(
            f"{skill_path.relative_to(root)} frontmatter missing description"
        )
    return summary


def _load_registry_entries(
    root: Path,
) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for item_type, filename, key in REGISTRIES:
        path = root / "src" / "registry" / filename
        registry = load_yaml_file(path)
        expected_schema_version = REGISTRY_SCHEMA_BY_ITEM_TYPE[item_type]
        if registry.get("schema_version") != expected_schema_version:
            raise MarketplaceExportError(
                f"src/registry/{filename} must use schema_version "
                f"{expected_schema_version}"
            )
        entries = registry.get(key)
        if not isinstance(entries, list):
            raise MarketplaceExportError(f"src/registry/{filename}:{key} must be a list")
        normalized: list[dict[str, Any]] = []
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                raise MarketplaceExportError(
                    f"src/registry/{filename}:{key}[{index}] must be a mapping"
                )
            normalized.append(entry)
        result[item_type] = normalized
    return result


def _targeted_layer3_names(
    profile: str,
    entries: dict[str, list[dict[str, Any]]],
) -> set[str]:
    """Mirror build-time Layer 3 selection without creating a delivery engine."""

    candidates = {
        name
        for skill in entries["professional_skill"]
        for name in _optional_string_list(
            skill.get("layer3_candidates"),
            label=f"professional skill {skill.get('name')}.layer3_candidates",
        )
    }
    product_foundation_names = {
        str(entry.get("name"))
        for entry in entries["foundation_skill"]
        if entry.get("delivery_scope") == "product"
    }
    domain_names = {
        str(entry.get("name")) for entry in entries["domain_skill"]
    }
    return candidates & (product_foundation_names | domain_names)


def _delivery(
    profile: str,
    item_type: str,
    name: str,
    targeted_layer3: set[str],
) -> dict[str, Any]:
    top_level = (
        item_type in {"control_skill", "professional_skill"}
        or (item_type == "domain_skill" and profile in {"full", "dev"})
        or (item_type == "foundation_skill" and profile == "dev")
    )
    targeted_reference = not top_level and name in targeted_layer3
    if top_level:
        mode = "top_level_skill"
    elif targeted_reference:
        mode = "targeted_reference"
    else:
        mode = "routing_index_only"
    return {
        "mode": mode,
        "top_level": top_level,
        "targeted_reference": targeted_reference,
        "routing_index": True,
    }


def _item(
    root: Path,
    profile: str,
    item_type: str,
    entry: dict[str, Any],
    targeted_layer3: set[str],
) -> dict[str, Any]:
    name = str(entry.get("name") or "").strip()
    source_path = str(entry.get("path") or "").strip()
    if not name or not source_path:
        raise MarketplaceExportError(f"{item_type} entry must define name and path")
    contract = {
        field: (
            _reference_path_list(
                entry.get(field), label=f"{name}.{field}", owner=name
            )
            if field == "reference_index"
            else _string_list(entry.get(field), label=f"{name}.{field}")
        )
        for field in CONTRACT_FIELDS
    }
    roles = contract["role_support"]
    delivery_scope = entry.get("delivery_scope")
    task_routable = entry.get("task_routable")
    if item_type == "foundation_skill":
        if delivery_scope not in FOUNDATION_DELIVERY_SCOPES:
            raise MarketplaceExportError(
                f"{name}.delivery_scope must be one of "
                f"{sorted(FOUNDATION_DELIVERY_SCOPES)}"
            )
    elif delivery_scope is not None:
        raise MarketplaceExportError(
            f"{name}.delivery_scope is only valid for a Foundation Skill"
        )
    if item_type == "professional_skill":
        if not isinstance(task_routable, bool):
            raise MarketplaceExportError(
                f"{name}.task_routable must be boolean for a Professional Skill"
            )
    elif task_routable is not None:
        raise MarketplaceExportError(
            f"{name}.task_routable is only valid for a Professional Skill"
        )
    raw_used_by = _optional_string_list(
        entry.get("used_by"),
        label=f"{name}.used_by",
    )
    used_by = raw_used_by if item_type == "foundation_skill" else []
    return {
        "name": name,
        "type": item_type,
        "delivery_scope": delivery_scope,
        "task_routable": task_routable,
        "profile_delivery": _delivery(
            profile,
            item_type,
            name,
            targeted_layer3,
        ),
        "summary": _frontmatter_summary(root, source_path),
        **contract,
        "required_inputs_by_role": (
            _validated_role_map(
                entry,
                "required_inputs_by_role",
                roles,
                label=f"{name}.required_inputs_by_role",
            )
            if item_type == "professional_skill"
            else {}
        ),
        "output_contract_by_role": (
            _validated_role_map(
                entry,
                "output_contract_by_role",
                roles,
                label=f"{name}.output_contract_by_role",
            )
            if item_type == "professional_skill"
            else {}
        ),
        "related_layer3_skills": _optional_string_list(
            entry.get("layer3_candidates"),
            label=f"{name}.layer3_candidates",
        ),
        "used_by": used_by,
        "group": str(entry.get("group") or "").strip() or None,
        "source_path": source_path,
    }


def export_index(root: Path, profile: str) -> dict[str, Any]:
    """Build one profile's standard-Skill marketplace payload."""

    if profile not in PROFILES:
        raise ValueError(f"unsupported profile: {profile}")
    entries = _load_registry_entries(root)
    targeted_layer3 = _targeted_layer3_names(profile, entries)
    items = [
        _item(root, profile, item_type, entry, targeted_layer3)
        for item_type, _filename, _key in REGISTRIES
        for entry in entries[item_type]
    ]
    return {
        "schema_version": MARKETPLACE_SCHEMA_VERSION,
        "profile": profile,
        "generated_by": "scripts/export-marketplace-index.py",
        "source_of_truth": [
            "src/registry/control-skills.yaml",
            "src/registry/professional-skills.yaml",
            "src/registry/foundation-skills.yaml",
            "src/registry/domain-skills.yaml",
        ],
        "items": sorted(items, key=lambda item: (item["type"], item["name"])),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=PROFILES, required=True)
    parser.add_argument("--out", required=True, help="JSON output path")
    args = parser.parse_args(argv)

    try:
        payload = export_index(ROOT, args.profile)
    except MarketplaceExportError as exc:
        print(f"export-marketplace-index: ERROR: {exc}", file=sys.stderr)
        return 1
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(payload['items'])} marketplace index items to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
