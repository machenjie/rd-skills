#!/usr/bin/env python3
"""Export a source-derived ChangeForge marketplace/discovery index."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from validation_utils import load_yaml_file, parse_frontmatter


ROOT = Path(__file__).resolve().parents[1]
PROFILES = ("recommended", "full", "dev")
ITEM_TYPES = {
    "professional_skill": "professional_skill",
    "foundation_capability": "foundation_capability",
    "domain_extension": "domain_extension",
}


class MarketplaceExportError(RuntimeError):
    """Raised when source data cannot produce a trustworthy marketplace index."""


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _frontmatter_summary(root: Path, source_path: str) -> str:
    skill_path = root / source_path / "SKILL.md"
    if not skill_path.exists():
        raise MarketplaceExportError(f"{skill_path.relative_to(root)} is missing")
    try:
        frontmatter, _, _ = parse_frontmatter(skill_path)
    except Exception as exc:
        raise MarketplaceExportError(f"{skill_path.relative_to(root)} frontmatter is invalid: {exc}") from exc
    description = frontmatter.get("description")
    summary = str(description).strip() if description is not None else ""
    if not summary:
        raise MarketplaceExportError(f"{skill_path.relative_to(root)} frontmatter missing description")
    return summary


def _runtime_path(profile: str, item_type: str, name: str) -> str | None:
    top_level = item_type == "professional_skill"
    if item_type == "domain_extension":
        top_level = profile in {"full", "dev"}
    if item_type == "foundation_capability":
        top_level = profile == "dev"
    if not top_level:
        return None
    return f"dist/universal/skills/{profile}/{name}"


def _profile_visibility(profile: str, item_type: str) -> dict[str, bool]:
    if item_type == "professional_skill":
        return {
            "top_level": True,
            "compiled_reference": False,
            "router_index": True,
            "authoring_visibility": True,
        }
    if item_type == "domain_extension":
        return {
            "top_level": profile in {"full", "dev"},
            "compiled_reference": False,
            "router_index": True,
            "authoring_visibility": profile == "dev",
        }
    return {
        "top_level": profile == "dev",
        "compiled_reference": True,
        "router_index": True,
        "authoring_visibility": profile == "dev",
    }


def _route_metadata(root: Path) -> dict[str, dict[str, set[str]]]:
    routing_path = root / "src" / "registry" / "routing-rules.yaml"
    routing = load_yaml_file(routing_path)
    metadata: dict[str, dict[str, set[str]]] = {}

    for rule in routing.get("risk_trigger_rules", []):
        trigger = str(rule.get("trigger", "")).strip()
        if not trigger:
            continue
        pairs = (
            ("required_skills", "professional_skill"),
            ("required_capabilities", "foundation_capability"),
            ("required_domain_extensions", "domain_extension"),
        )
        gates = {str(gate) for gate in _as_list(rule.get("required_quality_gates"))}
        for field, _item_type in pairs:
            for name in _as_list(rule.get(field)):
                key = str(name)
                entry = metadata.setdefault(key, {"triggers": set(), "required_quality_gates": set()})
                entry["triggers"].add(trigger)
                entry["required_quality_gates"].update(gates)

    return metadata


def _professional_items(root: Path, profile: str, route_metadata: dict[str, dict[str, set[str]]]) -> list[dict[str, Any]]:
    registry = load_yaml_file(root / "src" / "registry" / "skills.yaml")
    items: list[dict[str, Any]] = []
    for skill in registry.get("skills", []):
        name = skill["name"]
        source_path = skill["path"]
        route = route_metadata.get(name, {"triggers": set(), "required_quality_gates": set()})
        items.append(
            {
                "name": name,
                "type": ITEM_TYPES["professional_skill"],
                "profile_visibility": _profile_visibility(profile, "professional_skill"),
                "summary": _frontmatter_summary(root, source_path),
                "triggers": sorted(route["triggers"]),
                "risk_notes": [],
                "expected_outputs": ["Professional output contract defined in source SKILL.md."],
                "used_by": [],
                "required_quality_gates": sorted(route["required_quality_gates"]),
                "runtime_path": _runtime_path(profile, "professional_skill", name),
                "source_path": source_path,
            }
        )
    return items


def _capability_items(root: Path, profile: str, route_metadata: dict[str, dict[str, set[str]]]) -> list[dict[str, Any]]:
    registry = load_yaml_file(root / "src" / "registry" / "capabilities.yaml")
    items: list[dict[str, Any]] = []
    for capability in registry.get("capabilities", []):
        name = capability["name"]
        source_path = capability["path"]
        route = route_metadata.get(name, {"triggers": set(), "required_quality_gates": set()})
        triggers = {str(trigger) for trigger in _as_list(capability.get("triggers"))}
        triggers.update(route["triggers"])
        items.append(
            {
                "name": name,
                "type": ITEM_TYPES["foundation_capability"],
                "profile_visibility": _profile_visibility(profile, "foundation_capability"),
                "summary": _frontmatter_summary(root, source_path),
                "triggers": sorted(triggers),
                "risk_notes": [str(note) for note in _as_list(capability.get("risk_notes"))],
                "expected_outputs": [str(output) for output in _as_list(capability.get("expected_outputs"))],
                "used_by": [str(skill) for skill in _as_list(capability.get("used_by"))],
                "required_quality_gates": sorted(route["required_quality_gates"]),
                "runtime_path": _runtime_path(profile, "foundation_capability", name),
                "source_path": source_path,
            }
        )
    return items


def _domain_items(root: Path, profile: str, route_metadata: dict[str, dict[str, set[str]]]) -> list[dict[str, Any]]:
    registry = load_yaml_file(root / "src" / "registry" / "domain-extensions.yaml")
    items: list[dict[str, Any]] = []
    for extension in registry.get("domain_extensions", []):
        name = extension["name"]
        source_path = extension["path"]
        route = route_metadata.get(name, {"triggers": set(), "required_quality_gates": set()})
        items.append(
            {
                "name": name,
                "type": ITEM_TYPES["domain_extension"],
                "profile_visibility": _profile_visibility(profile, "domain_extension"),
                "summary": _frontmatter_summary(root, source_path),
                "triggers": sorted(route["triggers"]),
                "risk_notes": [],
                "expected_outputs": ["Domain-specific professional extension output contract defined in source SKILL.md."],
                "used_by": [],
                "required_quality_gates": sorted(route["required_quality_gates"]),
                "runtime_path": _runtime_path(profile, "domain_extension", name),
                "source_path": source_path,
            }
        )
    return items


def export_index(root: Path, profile: str) -> dict[str, Any]:
    """Build the marketplace index payload for one runtime profile."""
    if profile not in PROFILES:
        raise ValueError(f"unsupported profile: {profile}")
    route_metadata = _route_metadata(root)
    items = [
        *_professional_items(root, profile, route_metadata),
        *_capability_items(root, profile, route_metadata),
        *_domain_items(root, profile, route_metadata),
    ]
    return {
        "schema_version": 1,
        "profile": profile,
        "generated_by": "scripts/export-marketplace-index.py",
        "source_of_truth": [
            "src/registry/skills.yaml",
            "src/registry/capabilities.yaml",
            "src/registry/domain-extensions.yaml",
            "src/registry/routing-rules.yaml",
        ],
        "items": sorted(items, key=lambda item: (item["type"], item["name"])),
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for exporting the profile index."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=PROFILES, required=True)
    parser.add_argument("--out", required=True, help="JSON output path.")
    args = parser.parse_args(argv)

    try:
        payload = export_index(ROOT, args.profile)
    except MarketplaceExportError as exc:
        print(f"export-marketplace-index: ERROR: {exc}", file=sys.stderr)
        return 1
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {len(payload['items'])} marketplace index items to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
