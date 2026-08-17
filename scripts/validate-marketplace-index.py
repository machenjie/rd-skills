#!/usr/bin/env python3
"""Validate hookless rd-skills marketplace/discovery indexes."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from validation_utils import (
    EXPECTED_CONTROL_SKILL_COUNT,
    EXPECTED_DOMAIN_EXTENSION_COUNT,
    EXPECTED_FOUNDATION_CAPABILITY_COUNT,
    EXPECTED_PROFILE_DELIVERY_MODE_COUNTS,
    EXPECTED_PROFILE_TOP_LEVEL_COUNTS,
    EXPECTED_PROFESSIONAL_SKILL_COUNT,
    FOUNDATION_DELIVERY_SCOPES,
    MARKETPLACE_SCHEMA_VERSION,
    NAME_RE,
    role_contract_map_errors,
)


ROOT = Path(__file__).resolve().parents[1]
PROFILES = ("recommended", "full", "dev")
ITEM_TYPES = {
    "control_skill",
    "professional_skill",
    "foundation_skill",
    "domain_skill",
}
TOP_LEVEL_KEYS = {
    "schema_version",
    "profile",
    "generated_by",
    "source_of_truth",
    "items",
}
ITEM_KEYS = {
    "name",
    "type",
    "delivery_scope",
    "task_routable",
    "profile_delivery",
    "summary",
    "role_support",
    "trigger_signals",
    "anti_trigger_signals",
    "required_inputs",
    "required_inputs_by_role",
    "output_contract_by_role",
    "output_contract",
    "escalation_signals",
    "reference_index",
    "related_layer3_skills",
    "used_by",
    "group",
    "source_path",
}
DELIVERY_KEYS = {"mode", "top_level", "targeted_reference", "routing_index"}
DELIVERY_MODES = {"top_level_skill", "targeted_reference", "routing_index_only"}
STRING_LIST_FIELDS = (
    "role_support",
    "trigger_signals",
    "anti_trigger_signals",
    "required_inputs",
    "output_contract",
    "escalation_signals",
    "reference_index",
    "related_layer3_skills",
    "used_by",
)
NON_EMPTY_STRING_LIST_FIELDS = (
    "role_support",
    "trigger_signals",
    "anti_trigger_signals",
    "required_inputs",
    "output_contract",
    "escalation_signals",
)
EXPECTED_SOURCES = [
    "src/registry/control-skills.yaml",
    "src/registry/professional-skills.yaml",
    "src/registry/foundation-skills.yaml",
    "src/registry/domain-skills.yaml",
]
EXPECTED_ITEM_COUNTS = {
    "control_skill": EXPECTED_CONTROL_SKILL_COUNT,
    "professional_skill": EXPECTED_PROFESSIONAL_SKILL_COUNT,
    "foundation_skill": EXPECTED_FOUNDATION_CAPABILITY_COUNT,
    "domain_skill": EXPECTED_DOMAIN_EXTENSION_COUNT,
}
EXPECTED_TOTAL_ITEM_COUNT = sum(EXPECTED_ITEM_COUNTS.values())
ALLOWED_ROLES = {
    "main-control-agent",
    "analysis-agent",
    "task-agent",
    "review-agent",
}


def _load_exporter():
    spec = importlib.util.spec_from_file_location(
        "export_marketplace_index",
        ROOT / "scripts" / "export-marketplace-index.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load marketplace exporter")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _string_list_errors(
    item: dict[str, Any],
    field: str,
    label: str,
) -> list[str]:
    value = item.get(field)
    if not isinstance(value, list):
        return [f"{label}.{field} must be a list"]
    errors: list[str] = []
    if field in NON_EMPTY_STRING_LIST_FIELDS and not value:
        errors.append(f"{label}.{field} must not be empty")
    if not all(isinstance(entry, str) and entry.strip() for entry in value):
        errors.append(f"{label}.{field} must contain only non-empty strings")
    if len(value) != len(set(value)):
        errors.append(f"{label}.{field} must not contain duplicates")
    return errors


def _delivery_errors(item: dict[str, Any], label: str) -> list[str]:
    delivery = item.get("profile_delivery")
    if not isinstance(delivery, dict):
        return [f"{label}.profile_delivery must be an object"]
    errors: list[str] = []
    if set(delivery) != DELIVERY_KEYS:
        errors.append(
            f"{label}.profile_delivery keys must be exactly {sorted(DELIVERY_KEYS)}"
        )
    mode = delivery.get("mode")
    if mode not in DELIVERY_MODES:
        errors.append(
            f"{label}.profile_delivery.mode must be one of {sorted(DELIVERY_MODES)}"
        )
    for field in ("top_level", "targeted_reference", "routing_index"):
        if not isinstance(delivery.get(field), bool):
            errors.append(f"{label}.profile_delivery.{field} must be boolean")
    expected_flags = {
        "top_level_skill": (True, False),
        "targeted_reference": (False, True),
        "routing_index_only": (False, False),
    }
    if mode in expected_flags:
        expected_top, expected_reference = expected_flags[mode]
        if delivery.get("top_level") is not expected_top:
            errors.append(f"{label}: delivery mode and top_level disagree")
        if delivery.get("targeted_reference") is not expected_reference:
            errors.append(f"{label}: delivery mode and targeted_reference disagree")
    if delivery.get("routing_index") is not True:
        errors.append(f"{label}: every item must remain discoverable in the routing index")
    return errors


def _required_inputs_by_role_errors(
    item: dict[str, Any], label: str
) -> list[str]:
    value = item.get("required_inputs_by_role")
    if not isinstance(value, dict):
        return [f"{label}.required_inputs_by_role must be an object"]
    errors: list[str] = []
    roles = item.get("role_support")
    supported = set(roles) if isinstance(roles, list) else set()
    if value and item.get("type") != "professional_skill":
        errors.append(
            f"{label}.required_inputs_by_role is only valid for a Professional Skill"
        )
    if item.get("type") == "professional_skill" and len(supported) > 1:
        if set(value) != supported:
            errors.append(
                f"{label}.required_inputs_by_role keys must exactly match role_support"
            )
    elif value:
        errors.append(
            f"{label}.required_inputs_by_role must be empty for a single-role Skill"
        )
    for role, inputs in value.items():
        if role not in ALLOWED_ROLES:
            errors.append(
                f"{label}.required_inputs_by_role contains unsupported role {role!r}"
            )
        if not isinstance(inputs, list) or not inputs:
            errors.append(
                f"{label}.required_inputs_by_role.{role} must be a non-empty list"
            )
        elif not all(isinstance(value, str) and value.strip() for value in inputs):
            errors.append(
                f"{label}.required_inputs_by_role.{role} must contain non-empty strings"
            )
    return errors


def _role_map_errors(item: dict[str, Any], field: str, label: str) -> list[str]:
    if item.get("type") != "professional_skill":
        return [] if item.get(field) == {} else [f"{label}.{field} must be empty outside Professional Skills"]
    roles = item.get("role_support")
    role_list = roles if isinstance(roles, list) else []
    return role_contract_map_errors(item.get(field), role_list, f"{label}.{field}")


def _expected_delivery_mode(
    profile: str,
    item: dict[str, Any],
    targeted_layer3: set[str],
) -> str:
    item_type = item.get("type")
    name = str(item.get("name") or "")
    top_level = (
        item_type in {"control_skill", "professional_skill"}
        or (item_type == "domain_skill" and profile in {"full", "dev"})
        or (item_type == "foundation_skill" and profile == "dev")
    )
    if top_level:
        return "top_level_skill"
    if name in targeted_layer3:
        return "targeted_reference"
    return "routing_index_only"


def _item_count_errors(items: list[Any]) -> list[str]:
    errors: list[str] = []
    if len(items) != EXPECTED_TOTAL_ITEM_COUNT:
        errors.append(
            f"items must contain {EXPECTED_TOTAL_ITEM_COUNT} total item(s), found {len(items)}"
        )
    counts = Counter(
        item.get("type") for item in items if isinstance(item, dict)
    )
    for item_type, expected in EXPECTED_ITEM_COUNTS.items():
        actual = counts.get(item_type, 0)
        if actual != expected:
            errors.append(
                f"items must contain {expected} {item_type} item(s), found {actual}"
            )
    return errors


def _relationship_errors(items: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    items_by_name = {str(item.get("name")): item for item in items}
    professional_names = {
        name
        for name, item in items_by_name.items()
        if item.get("type") == "professional_skill"
    }
    layer3 = {
        str(item.get("name"))
        for item in items
        if item.get("type") in {"foundation_skill", "domain_skill"}
    }
    actual_foundation_owners: dict[str, set[str]] = {
        name: set()
        for name, item in items_by_name.items()
        if item.get("type") == "foundation_skill"
    }
    for item in items:
        name = str(item.get("name"))
        candidates = item.get("related_layer3_skills")
        for candidate in candidates if isinstance(candidates, list) else []:
            if candidate not in layer3:
                errors.append(f"{name}: unknown related Layer 3 Skill {candidate!r}")
                continue
            target = items_by_name[candidate]
            if target.get("type") == "foundation_skill":
                if item.get("type") == "professional_skill":
                    actual_foundation_owners[candidate].add(name)
                if target.get("delivery_scope") != "product":
                    errors.append(
                        f"{name}: non-product Foundation Skill {candidate!r} "
                        "cannot be a related Layer 3 Skill"
                    )
        owners = item.get("used_by")
        for owner in owners if isinstance(owners, list) else []:
            if owner not in professional_names:
                errors.append(f"{name}: unknown Professional owner {owner!r}")
    for name, actual_owners in actual_foundation_owners.items():
        item = items_by_name[name]
        declared = item.get("used_by")
        declared_owners = set(declared) if isinstance(declared, list) else set()
        if declared_owners != actual_owners:
            errors.append(
                f"{name}: used_by must exactly match related_layer3_skills; "
                f"declared={sorted(declared_owners)}, actual={sorted(actual_owners)}"
            )
        if item.get("delivery_scope") == "product" and not actual_owners:
            errors.append(f"{name}: product Foundation Skill must have an owner")
        if item.get("delivery_scope") == "product":
            foundation_roles = {
                role
                for role in item.get("role_support", [])
                if isinstance(role, str)
            }
            for owner in sorted(actual_owners):
                professional = items_by_name[owner]
                if professional.get("task_routable") is not True:
                    errors.append(
                        f"{name}: product owner {owner!r} must be task_routable"
                    )
                professional_roles = {
                    role
                    for role in professional.get("role_support", [])
                    if isinstance(role, str)
                }
                if not foundation_roles & professional_roles:
                    errors.append(
                        f"{name}: product owner {owner!r} has no role_support "
                        "intersection"
                    )
    return errors


def validate_payload(
    root: Path,
    payload: dict[str, Any],
    profile: str,
    *,
    enforce_counts: bool = True,
) -> list[str]:
    """Return schema, relationship, and profile-delivery errors."""

    errors: list[str] = []
    if set(payload) != TOP_LEVEL_KEYS:
        errors.append(f"top-level keys must be exactly {sorted(TOP_LEVEL_KEYS)}")
    if payload.get("schema_version") != MARKETPLACE_SCHEMA_VERSION:
        errors.append(
            f"schema_version must be {MARKETPLACE_SCHEMA_VERSION}"
        )
    if payload.get("profile") != profile:
        errors.append(f"profile must be {profile}")
    if not isinstance(payload.get("generated_by"), str):
        errors.append("generated_by must be a string")
    if payload.get("source_of_truth") != EXPECTED_SOURCES:
        errors.append("source_of_truth must list exactly the four hookless Skill registries")

    items = payload.get("items")
    if not isinstance(items, list):
        return [*errors, "items must be a list"]
    dict_items = [item for item in items if isinstance(item, dict)]
    if enforce_counts:
        errors.extend(_item_count_errors(items))

    names: set[str] = set()
    candidates = {
        candidate
        for item in dict_items
        for candidate in (
            item.get("related_layer3_skills")
            if isinstance(item.get("related_layer3_skills"), list)
            else []
        )
        if isinstance(candidate, str)
    }
    deliverable_layer3 = {
        str(item.get("name"))
        for item in dict_items
        if item.get("type") == "domain_skill"
        or (
            item.get("type") == "foundation_skill"
            and item.get("delivery_scope") == "product"
        )
    }
    targeted_layer3 = candidates & deliverable_layer3

    for index, item in enumerate(items):
        label = f"items[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        if set(item) != ITEM_KEYS:
            errors.append(f"{label} keys must be exactly {sorted(ITEM_KEYS)}")
        name = item.get("name")
        if not isinstance(name, str) or not NAME_RE.fullmatch(name):
            errors.append(f"{label}.name invalid name: {name!r}")
        elif name in names:
            errors.append(f"{label}.name is duplicated: {name}")
        else:
            names.add(name)
        if item.get("type") not in ITEM_TYPES:
            errors.append(f"{label}.type must be one of {sorted(ITEM_TYPES)}")
        if not isinstance(item.get("summary"), str) or not item.get("summary", "").strip():
            errors.append(f"{label}.summary must be a non-empty string")
        for field in STRING_LIST_FIELDS:
            errors.extend(_string_list_errors(item, field, label))
        errors.extend(_required_inputs_by_role_errors(item, label))
        errors.extend(_role_map_errors(item, "output_contract_by_role", label))
        roles = item.get("role_support")
        if isinstance(roles, list) and not set(roles).issubset(ALLOWED_ROLES):
            errors.append(f"{label}.role_support contains a non-static Agent Profile")
        group = item.get("group")
        if group is not None and (not isinstance(group, str) or not group.strip()):
            errors.append(f"{label}.group must be a non-empty string or null")
        item_type = item.get("type")
        delivery_scope = item.get("delivery_scope")
        task_routable = item.get("task_routable")
        if item_type == "foundation_skill":
            if delivery_scope not in FOUNDATION_DELIVERY_SCOPES:
                errors.append(
                    f"{label}.delivery_scope must be one of "
                    f"{sorted(FOUNDATION_DELIVERY_SCOPES)}"
                )
        elif delivery_scope is not None:
            errors.append(
                f"{label}.delivery_scope is only valid for a Foundation Skill"
            )
        if item_type == "professional_skill":
            if not isinstance(task_routable, bool):
                errors.append(
                    f"{label}.task_routable must be boolean for a Professional Skill"
                )
        elif task_routable is not None:
            errors.append(
                f"{label}.task_routable is only valid for a Professional Skill"
            )
        if item_type == "foundation_skill" and group is None:
            errors.append(f"{label}.group is required for a Foundation Skill")
        if item_type != "foundation_skill" and group is not None:
            errors.append(f"{label}.group is only valid for a Foundation Skill")
        if item_type != "professional_skill" and item.get("related_layer3_skills"):
            errors.append(
                f"{label}.related_layer3_skills is only valid for a Professional Skill"
            )
        if item_type != "foundation_skill" and item.get("used_by"):
            errors.append(f"{label}.used_by is only valid for a Foundation Skill")
        source_path = item.get("source_path")
        if not isinstance(source_path, str):
            errors.append(f"{label}.source_path must be a string")
        elif not (root / source_path / "SKILL.md").is_file():
            errors.append(f"{label}.source_path is not a standard Skill: {source_path}")
        else:
            source_root = (root / source_path).resolve()
            references = item.get("reference_index")
            for reference in references if isinstance(references, list) else []:
                target = (source_root / reference).resolve()
                if source_root not in target.parents or not target.is_file():
                    errors.append(
                        f"{label}.reference_index target is missing or escapes its Skill: "
                        f"{reference}"
                    )
        errors.extend(_delivery_errors(item, label))
        delivery = item.get("profile_delivery")
        if isinstance(delivery, dict):
            expected_mode = _expected_delivery_mode(profile, item, targeted_layer3)
            if delivery.get("mode") != expected_mode:
                errors.append(
                    f"{label}: expected {expected_mode} delivery in {profile}, "
                    f"found {delivery.get('mode')!r}"
                )

    errors.extend(_relationship_errors(dict_items))
    if enforce_counts:
        top_level_count = sum(
            item.get("profile_delivery", {}).get("top_level") is True
            for item in dict_items
            if isinstance(item.get("profile_delivery"), dict)
        )
        expected = EXPECTED_PROFILE_TOP_LEVEL_COUNTS[profile]
        if top_level_count != expected:
            errors.append(
                f"{profile} must expose {expected} top-level standard Skill(s), "
                f"found {top_level_count}"
            )
        mode_counts = Counter(
            item.get("profile_delivery", {}).get("mode")
            for item in dict_items
            if isinstance(item.get("profile_delivery"), dict)
        )
        for mode, expected_count in EXPECTED_PROFILE_DELIVERY_MODE_COUNTS[
            profile
        ].items():
            actual_count = mode_counts.get(mode, 0)
            if actual_count != expected_count:
                errors.append(
                    f"{profile} must expose {expected_count} item(s) with "
                    f"delivery mode {mode}, found {actual_count}"
                )
    return errors


def validate_profile(root: Path, profile: str) -> list[str]:
    exporter = _load_exporter()
    return validate_payload(root, exporter.export_index(root, profile), profile)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=PROFILES, required=True)
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args(argv)

    errors = validate_profile(Path(args.root), args.profile)
    if errors:
        for error in errors:
            print(f"validate-marketplace-index: ERROR: {error}", file=sys.stderr)
        return 1
    print(f"validate-marketplace-index: validated {args.profile} marketplace index")
    return 0


if __name__ == "__main__":
    sys.exit(main())
