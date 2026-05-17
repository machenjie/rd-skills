#!/usr/bin/env python3
"""Validate ChangeForge registries and cross-references."""

from __future__ import annotations

from pathlib import Path

from validation_utils import (
    EXPECTED_DOMAIN_EXTENSION_COUNT,
    EXPECTED_FOUNDATION_CAPABILITY_COUNT,
    EXPECTED_PROFESSIONAL_SKILL_COUNT,
    EXPECTED_PROFILE_TOP_LEVEL_COUNTS,
    ValidationProblem,
    collect_reference_values,
    entry_path,
    entry_ref,
    fail_many,
    load_yaml_file,
    parse_frontmatter,
    path_is_within,
    registry_items,
    relpath,
    validate_expected_count,
    validate_no_personal_references,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_DIR = ROOT / "src" / "registry"
PROFESSIONAL_SKILLS_DIR = ROOT / "src" / "professional-skills"
CAPABILITIES_DIR = ROOT / "src" / "foundation" / "capabilities"
DOMAIN_EXTENSIONS_DIR = ROOT / "src" / "domain-extensions"
REQUIRED_REGISTRIES = (
    "skills.yaml",
    "capabilities.yaml",
    "domain-extensions.yaml",
    "routing-rules.yaml",
)
BANNED_REGISTRIES = (
    ROOT / "registry" / "toolbox.yaml",
    REGISTRY_DIR / "toolbox.yaml",
)
REFERENCE_KEYS = {
    "skill",
    "skills",
    "skill_name",
    "skill_names",
    "capability",
    "capabilities",
    "capability_id",
    "capability_ids",
    "changeforge_capability_id",
    "domain_extension",
    "domain_extensions",
    "domain_extension_id",
    "domain_extension_ids",
    "target",
    "targets",
    "route_to",
    "routes_to",
    "uses",
    "used_by",
    "requires",
    "required_capabilities",
    "fallback",
    "fallbacks",
    "handoff",
    "handoffs",
    "handoff_to",
    "handoff_targets",
}
HANDOFF_KEYS = {
    "handoff",
    "handoffs",
    "handoff_to",
    "handoff_targets",
    "escalate_to",
    "escalates_to",
}


def _load_skill_names() -> set[str]:
    names: set[str] = set()
    if not PROFESSIONAL_SKILLS_DIR.exists():
        return names

    for skill_dir in PROFESSIONAL_SKILLS_DIR.iterdir():
        if not skill_dir.is_dir() or skill_dir.name.startswith("."):
            continue
        names.add(skill_dir.name)
        skill_file = skill_dir / "SKILL.md"
        if skill_file.is_file():
            try:
                metadata, _raw_frontmatter, _body = parse_frontmatter(skill_file)
            except ValidationProblem:
                continue
            name = metadata.get("name")
            if isinstance(name, str):
                names.add(name)
    return names


def _load_capability_refs() -> set[str]:
    refs: set[str] = set()
    if not CAPABILITIES_DIR.exists():
        return refs

    for capability_dir in CAPABILITIES_DIR.iterdir():
        if not capability_dir.is_dir() or capability_dir.name.startswith((".", "_")):
            continue
        refs.add(capability_dir.name)
        skill_file = capability_dir / "SKILL.md"
        if skill_file.is_file():
            try:
                metadata, _raw_frontmatter, _body = parse_frontmatter(skill_file)
            except ValidationProblem:
                continue
            for key in ("name", "changeforge_capability_id"):
                value = metadata.get(key)
                if isinstance(value, str):
                    refs.add(value)
    return refs


def _load_domain_extension_names() -> set[str]:
    names: set[str] = set()
    if not DOMAIN_EXTENSIONS_DIR.exists():
        return names

    for extension_dir in DOMAIN_EXTENSIONS_DIR.iterdir():
        if not extension_dir.is_dir() or extension_dir.name.startswith("."):
            continue
        names.add(extension_dir.name)
        skill_file = extension_dir / "SKILL.md"
        if skill_file.is_file():
            try:
                metadata, _raw_frontmatter, _body = parse_frontmatter(skill_file)
            except ValidationProblem:
                continue
            name = metadata.get("name")
            if isinstance(name, str):
                names.add(name)
    return names


def _entry_path_exists(path_value: str, expected_root: Path) -> bool:
    candidate = (ROOT / path_value).resolve()
    return path_is_within(expected_root, candidate) and candidate.exists()


def _validate_registry_entry_reference(
    entry: object,
    keys: tuple[str, ...],
    existing_refs: set[str],
    expected_root: Path,
    registry_name: str,
    index: int,
    errors: list[str],
) -> None:
    path_value = entry_path(entry)
    if not path_value:
        errors.append(f"{registry_name}[{index}]: missing source path")
        return
    if not _entry_path_exists(path_value, expected_root):
        errors.append(f"{registry_name}[{index}]: path does not exist: {path_value}")
        return

    ref = entry_ref(entry, keys)
    if ref is None:
        errors.append(f"{registry_name}[{index}]: missing reference name/id/path")
        return
    if ref not in existing_refs:
        errors.append(f"{registry_name}[{index}]: references missing item '{ref}'")


def _validate_capability_status(entry: object, index: int, errors: list[str]) -> None:
    if not isinstance(entry, dict):
        return
    if entry.get("status") != "implemented":
        errors.append(
            "capabilities.yaml:capabilities"
            f"[{index}]: status must be implemented"
        )


def _validate_capability_used_by_references(
    entry: object,
    index: int,
    all_refs: set[str],
    errors: list[str],
) -> None:
    context = f"capabilities.yaml:capabilities[{index}]"
    if not isinstance(entry, dict):
        return
    used_by = entry.get("used_by")
    if not isinstance(used_by, list):
        errors.append(f"{context}: field 'used_by' must be a list")
        return
    for target in used_by:
        if not isinstance(target, str) or not target.strip():
            errors.append(f"{context}: used_by entries must be non-empty strings")
            continue
        if target not in all_refs:
            errors.append(f"{context}: used_by references missing item '{target}'")


def _validate_optional_status(
    entry: object,
    registry_name: str,
    index: int,
    errors: list[str],
) -> None:
    if not isinstance(entry, dict) or "status" not in entry:
        return
    if entry.get("status") != "implemented":
        errors.append(f"{registry_name}[{index}]: status must be implemented when present")


def main() -> int:
    errors: list[str] = []

    if not REGISTRY_DIR.exists():
        errors.append("missing src/registry")
        return fail_many("validate-registry", errors)

    for path in BANNED_REGISTRIES:
        if path.exists():
            errors.append(f"banned personal asset mapping registry exists: {relpath(ROOT, path)}")

    toolbox_dir = ROOT / "src" / "toolbox"
    if toolbox_dir.exists():
        errors.append(f"banned personal asset mapping path exists: {relpath(ROOT, toolbox_dir)}")

    missing = [name for name in REQUIRED_REGISTRIES if not (REGISTRY_DIR / name).is_file()]
    if missing:
        errors.append(f"missing registry file(s): {', '.join(missing)}")
        return fail_many("validate-registry", errors)

    registry_data: dict[str, object] = {}
    for name in REQUIRED_REGISTRIES:
        path = REGISTRY_DIR / name
        text = path.read_text(encoding="utf-8")
        validate_no_personal_references(text, relpath(ROOT, path), errors)
        try:
            registry_data[name] = load_yaml_file(path)
        except ValidationProblem as exc:
            errors.append(str(exc))
            registry_data[name] = {}

    skill_names = _load_skill_names()
    capability_refs = _load_capability_refs()
    domain_extension_names = _load_domain_extension_names()
    all_refs = skill_names | capability_refs | domain_extension_names

    skill_entries = registry_items(
        registry_data["skills.yaml"],
        "skills",
        REGISTRY_DIR / "skills.yaml",
        errors,
    )
    validate_expected_count(
        errors,
        "professional skill registry entrie(s)",
        len(skill_entries),
        EXPECTED_PROFESSIONAL_SKILL_COUNT,
        "skills.yaml:skills",
    )
    for index, entry in enumerate(skill_entries):
        _validate_optional_status(entry, "skills.yaml:skills", index, errors)
        _validate_registry_entry_reference(
            entry,
            ("name", "skill", "skill_name", "id"),
            skill_names,
            PROFESSIONAL_SKILLS_DIR,
            "skills.yaml:skills",
            index,
            errors,
        )

    capability_entries = registry_items(
        registry_data["capabilities.yaml"],
        "capabilities",
        REGISTRY_DIR / "capabilities.yaml",
        errors,
    )
    validate_expected_count(
        errors,
        "capability registry entrie(s)",
        len(capability_entries),
        EXPECTED_FOUNDATION_CAPABILITY_COUNT,
        "capabilities.yaml:capabilities",
    )
    for index, entry in enumerate(capability_entries):
        _validate_capability_status(entry, index, errors)
        _validate_registry_entry_reference(
            entry,
            ("changeforge_capability_id", "capability_id", "id", "name", "capability"),
            capability_refs,
            CAPABILITIES_DIR,
            "capabilities.yaml:capabilities",
            index,
            errors,
        )
        _validate_capability_used_by_references(entry, index, all_refs, errors)

    domain_extension_entries = registry_items(
        registry_data["domain-extensions.yaml"],
        "domain_extensions",
        REGISTRY_DIR / "domain-extensions.yaml",
        errors,
    )
    validate_expected_count(
        errors,
        "domain extension registry entrie(s)",
        len(domain_extension_entries),
        EXPECTED_DOMAIN_EXTENSION_COUNT,
        "domain-extensions.yaml:domain_extensions",
    )
    for index, entry in enumerate(domain_extension_entries):
        _validate_optional_status(
            entry,
            "domain-extensions.yaml:domain_extensions",
            index,
            errors,
        )
        _validate_registry_entry_reference(
            entry,
            ("name", "domain_extension", "domain_extension_id", "id"),
            domain_extension_names,
            DOMAIN_EXTENSIONS_DIR,
            "domain-extensions.yaml:domain_extensions",
            index,
            errors,
        )

    profile_counts = {
        "recommended": len(skill_entries),
        "full": len(skill_entries) + len(domain_extension_entries),
        "dev": len(skill_entries) + len(capability_entries) + len(domain_extension_entries),
    }
    for profile, expected_count in EXPECTED_PROFILE_TOP_LEVEL_COUNTS.items():
        validate_expected_count(
            errors,
            f"{profile} profile top-level skill(s)",
            profile_counts[profile],
            expected_count,
            "registry profile counts",
        )

    routing_entries = registry_items(
        registry_data["routing-rules.yaml"],
        "routing_rules",
        REGISTRY_DIR / "routing-rules.yaml",
        errors,
    )
    for index, entry in enumerate(routing_entries):
        for ref in collect_reference_values(entry, REFERENCE_KEYS):
            first_part = ref.strip("/").split("/", 1)[0]
            if ref not in all_refs and first_part not in all_refs:
                errors.append(
                    f"routing-rules.yaml:routing_rules[{index}]: broken reference '{ref}'"
                )

    for registry_name, data in registry_data.items():
        for ref in collect_reference_values(data, HANDOFF_KEYS):
            first_part = ref.strip("/").split("/", 1)[0]
            if ref not in all_refs and first_part not in all_refs:
                errors.append(f"{registry_name}: broken handoff reference '{ref}'")

    if errors:
        return fail_many("validate-registry", errors)

    print("validate-registry: registry references are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
