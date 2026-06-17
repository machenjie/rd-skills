#!/usr/bin/env python3
"""Validate generated ChangeForge marketplace/discovery index payloads."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Any

from validation_utils import NAME_RE


ROOT = Path(__file__).resolve().parents[1]
PROFILES = ("recommended", "full", "dev")
ITEM_TYPES = {"professional_skill", "foundation_capability", "domain_extension"}
TOP_LEVEL_KEYS = {"schema_version", "profile", "generated_by", "source_of_truth", "items"}
ITEM_KEYS = {
    "name",
    "type",
    "profile_visibility",
    "summary",
    "triggers",
    "risk_notes",
    "expected_outputs",
    "used_by",
    "required_quality_gates",
    "runtime_path",
    "source_path",
}
VISIBILITY_KEYS = {"top_level", "compiled_reference", "router_index", "authoring_visibility"}
STRING_LIST_FIELDS = (
    "triggers",
    "risk_notes",
    "expected_outputs",
    "used_by",
    "required_quality_gates",
)


def _load_exporter():
    spec = importlib.util.spec_from_file_location(
        "export_marketplace_index",
        ROOT / "scripts" / "export-marketplace-index.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load marketplace exporter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _string_list_errors(item: dict[str, Any], field: str, label: str) -> list[str]:
    value = item.get(field)
    if not isinstance(value, list):
        return [f"{label}.{field} must be a list"]
    if not all(isinstance(entry, str) for entry in value):
        return [f"{label}.{field} must contain only strings"]
    return []


def _validate_visibility(item: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    visibility = item.get("profile_visibility")
    if not isinstance(visibility, dict):
        return [f"{label}.profile_visibility must be an object"]
    if set(visibility) != VISIBILITY_KEYS:
        errors.append(f"{label}.profile_visibility keys must be exactly {sorted(VISIBILITY_KEYS)}")
    for key in VISIBILITY_KEYS:
        if not isinstance(visibility.get(key), bool):
            errors.append(f"{label}.profile_visibility.{key} must be boolean")
    return errors


def _validate_profile_policy(
    profile: str,
    item_type: str,
    visibility: dict[str, Any],
    runtime_path: object,
    label: str,
) -> list[str]:
    errors: list[str] = []
    top_level = visibility.get("top_level")
    if item_type == "foundation_capability":
        if profile in {"recommended", "full"} and (top_level or runtime_path is not None):
            errors.append(f"{label}: foundation capability must not be top-level in {profile}")
        if profile == "dev" and (not top_level or runtime_path is None):
            errors.append(f"{label}: foundation capability must be top-level in dev")
    return errors


def validate_payload(root: Path, payload: dict[str, Any], profile: str) -> list[str]:
    """Return schema/profile/runtime-path errors for a marketplace payload."""
    errors: list[str] = []
    if set(payload) != TOP_LEVEL_KEYS:
        errors.append(f"top-level keys must be exactly {sorted(TOP_LEVEL_KEYS)}")
    if payload.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if payload.get("profile") != profile:
        errors.append(f"profile must be {profile}")
    if not isinstance(payload.get("generated_by"), str):
        errors.append("generated_by must be a string")
    source_of_truth = payload.get("source_of_truth")
    if not isinstance(source_of_truth, list) or not source_of_truth or not all(
        isinstance(entry, str) for entry in source_of_truth
    ):
        errors.append("source_of_truth must be a non-empty list of strings")
    items = payload.get("items")
    if not isinstance(items, list):
        errors.append("items must be a list")
        return errors

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
        item_type = item.get("type")
        if item_type not in ITEM_TYPES:
            errors.append(f"{label}.type must be one of {sorted(ITEM_TYPES)}")
        summary = item.get("summary")
        if not isinstance(summary, str):
            errors.append(f"{label}.summary must be a string")
        for field in STRING_LIST_FIELDS:
            errors.extend(_string_list_errors(item, field, label))
        errors.extend(_validate_visibility(item, label))
        visibility = item.get("profile_visibility") if isinstance(item.get("profile_visibility"), dict) else {}
        runtime_path = item.get("runtime_path")
        if runtime_path is not None:
            if not isinstance(runtime_path, str):
                errors.append(f"{label}.runtime_path must be a string or null")
            elif not (root / runtime_path).exists():
                errors.append(f"{label}.runtime_path does not exist: {runtime_path}")
        source_path = item.get("source_path")
        if not isinstance(source_path, str):
            errors.append(f"{label}.source_path must be a string")
        elif not (root / source_path).exists():
            errors.append(f"{label}.source_path does not exist: {source_path}")
        if isinstance(item_type, str):
            errors.extend(_validate_profile_policy(profile, item_type, visibility, runtime_path, label))
    return errors


def validate_profile(root: Path, profile: str) -> list[str]:
    """Export and validate one runtime profile marketplace index."""
    exporter = _load_exporter()
    payload = exporter.export_index(root, profile)
    return validate_payload(root, payload, profile)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for marketplace index validation."""
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
