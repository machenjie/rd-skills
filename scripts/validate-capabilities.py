#!/usr/bin/env python3
"""Validate authored foundation capabilities."""

from __future__ import annotations

import re
from pathlib import Path

from validation_utils import (
    EXPECTED_DOMAIN_EXTENSION_COUNT,
    EXPECTED_FOUNDATION_CAPABILITY_COUNT,
    EXPECTED_PROFESSIONAL_SKILL_COUNT,
    EXPECTED_PROFILE_TOP_LEVEL_COUNTS,
    NAME_RE,
    ValidationProblem,
    entry_path,
    entry_ref,
    fail_many,
    load_yaml_file,
    parse_frontmatter,
    registry_items,
    relpath,
    validate_description_length,
    validate_no_beginner_sections,
    validate_no_personal_references,
    validate_expected_count,
    validate_name,
    validate_required_frontmatter,
    validate_required_sections,
    visible_child_dirs,
)


ROOT = Path(__file__).resolve().parents[1]
PROFESSIONAL_SKILLS_DIR = ROOT / "src" / "professional-skills"
CAPABILITIES_DIR = ROOT / "src" / "foundation" / "capabilities"
CAPABILITIES_REGISTRY = ROOT / "src" / "registry" / "capabilities.yaml"
CAPABILITY_TEMPLATE_DIR = CAPABILITIES_DIR / "_template"
DOMAIN_EXTENSIONS_DIR = ROOT / "src" / "domain-extensions"
ALLOWED_CAPABILITIES_ROOT_FILES = {".gitkeep", "README.md"}
BANNED_MAPPING_PATHS = (
    ROOT / "registry" / "toolbox.yaml",
    ROOT / "src" / "registry" / "toolbox.yaml",
    ROOT / "src" / "toolbox",
)
REGISTRY_REQUIRED_FIELDS = (
    "id",
    "name",
    "group",
    "path",
    "status",
    "used_by",
    "triggers",
    "risk_notes",
    "expected_outputs",
)
REGISTRY_LIST_FIELDS = ("used_by", "triggers", "risk_notes", "expected_outputs")
REGISTRY_STATUSES = {"implemented"}
REQUIRED_FRONTMATTER = (
    "name",
    "description",
    "license",
    "changeforge_kind",
    "changeforge_capability_id",
    "changeforge_version",
)
REQUIRED_SECTIONS = (
    "Mission",
    "When To Use",
    "Do Not Use When",
    "Non-Negotiable Rules",
    "Industry Benchmarks",
    "Selection Rules",
    "Risk Escalation Rules",
    "Critical Details",
    "Failure Modes",
    "Output Contract",
    "Quality Gate",
    "Used By",
    "Handoff",
    "Completion Criteria",
)
ANTI_FRAGMENTATION_KEYWORDS = (
    "anti-fragmentation",
    "file granularity",
    "micro-file sprawl",
    "one-function file",
    "tiny helper file",
    "navigation cost",
    "keep in existing file",
    "small file merge",
    "merge restraint",
    "reckless file merge",
    "lost small-file boundary",
    "split merge decision",
)
CAPABILITY_KEYWORD_REQUIREMENTS = {
    "implementation-structure-design": ANTI_FRAGMENTATION_KEYWORDS,
    "code-clarity-maintainability": ANTI_FRAGMENTATION_KEYWORDS,
}


def _is_nonempty_string_list(value: object) -> bool:
    return isinstance(value, list) and all(
        isinstance(item, str) and item.strip() for item in value
    )


def _normalize_capability_id(value: object) -> str | None:
    if isinstance(value, str) and re.fullmatch(r"\d+", value):
        number = int(value)
        if 1 <= number <= EXPECTED_FOUNDATION_CAPABILITY_COUNT:
            return f"{number:02d}" if number < 100 else str(number)
    if isinstance(value, int) and 1 <= value <= EXPECTED_FOUNDATION_CAPABILITY_COUNT:
        return f"{value:02d}" if value < 100 else str(value)
    return None


def _validate_registry_format(registry_data: object, errors: list[str]) -> list[object]:
    entries = registry_items(
        registry_data,
        "capabilities",
        CAPABILITIES_REGISTRY,
        errors,
    )
    seen_ids: dict[str, int] = {}
    seen_names: dict[str, int] = {}
    seen_paths: dict[str, int] = {}

    for index, entry in enumerate(entries):
        context = f"capabilities.yaml:capabilities[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{context}: entry must be a mapping")
            continue

        for field in REGISTRY_REQUIRED_FIELDS:
            if field not in entry:
                errors.append(f"{context}: missing required field '{field}'")

        capability_id = entry.get("id")
        if _normalize_capability_id(capability_id) != capability_id:
            errors.append(f"{context}: field 'id' must be a valid capability id string")
        elif capability_id in seen_ids:
            errors.append(
                f"{context}: duplicate id '{capability_id}' first used at "
                f"capabilities.yaml:capabilities[{seen_ids[capability_id]}]"
            )
        else:
            seen_ids[capability_id] = index

        name = entry.get("name")
        if not isinstance(name, str) or not NAME_RE.fullmatch(name):
            errors.append(f"{context}: field 'name' must be lowercase hyphen-separated text")
            name = None
        elif name in seen_names:
            errors.append(
                f"{context}: duplicate name '{name}' first used at "
                f"capabilities.yaml:capabilities[{seen_names[name]}]"
            )
        else:
            seen_names[name] = index

        group = entry.get("group")
        if not isinstance(group, str) or not NAME_RE.fullmatch(group):
            errors.append(f"{context}: field 'group' must be lowercase hyphen-separated text")

        path = entry.get("path")
        expected_path = f"src/foundation/capabilities/{name}" if name else None
        if not isinstance(path, str) or not path:
            errors.append(f"{context}: field 'path' must be a non-empty string")
        elif path.startswith("src/toolbox") or "toolbox.yaml" in path:
            errors.append(f"{context}: path must not reference banned mapping content")
        elif expected_path and path != expected_path:
            errors.append(f"{context}: field 'path' must be {expected_path}")
        elif path in seen_paths:
            errors.append(
                f"{context}: duplicate path '{path}' first used at "
                f"capabilities.yaml:capabilities[{seen_paths[path]}]"
            )
        else:
            seen_paths[path] = index

        status = entry.get("status")
        if not isinstance(status, str) or status.casefold() not in REGISTRY_STATUSES:
            errors.append(
                f"{context}: field 'status' must be one of "
                f"{', '.join(sorted(REGISTRY_STATUSES))}"
            )

        for field in REGISTRY_LIST_FIELDS:
            if not _is_nonempty_string_list(entry.get(field)):
                errors.append(f"{context}: field '{field}' must be a non-empty list of strings")

    return entries


def _validate_capability_template(errors: list[str]) -> None:
    required_files = (
        CAPABILITY_TEMPLATE_DIR / "SKILL.md",
        CAPABILITY_TEMPLATE_DIR / "references" / "checklist.md",
        CAPABILITY_TEMPLATE_DIR / "examples" / "example-output.md",
    )
    for path in required_files:
        if not path.is_file():
            errors.append(f"missing capability template file: {relpath(ROOT, path)}")

    skill_file = CAPABILITY_TEMPLATE_DIR / "SKILL.md"
    if not skill_file.is_file():
        return

    file_context = relpath(ROOT, skill_file)
    try:
        metadata, raw_frontmatter, body = parse_frontmatter(skill_file)
    except ValidationProblem as exc:
        errors.append(str(exc).replace(str(ROOT) + "/", ""))
        return

    validate_required_frontmatter(metadata, REQUIRED_FRONTMATTER, file_context, errors)
    validate_name(metadata.get("name"), file_context, errors)
    if metadata.get("changeforge_kind") != "foundation-capability":
        errors.append(
            f"{file_context}: frontmatter 'changeforge_kind' must be foundation-capability"
        )
    validate_required_sections(body, REQUIRED_SECTIONS, file_context, errors)
    validate_no_beginner_sections(body, file_context, errors)
    validate_no_personal_references(raw_frontmatter + "\n" + body, file_context, errors)


def _validate_targeted_content_keywords(
    name: str | None,
    body: str,
    context: str,
    errors: list[str],
) -> None:
    if name not in CAPABILITY_KEYWORD_REQUIREMENTS:
        return
    folded = body.casefold()
    missing = [
        keyword
        for keyword in CAPABILITY_KEYWORD_REQUIREMENTS[name]
        if keyword.casefold() not in folded
    ]
    if missing:
        errors.append(
            f"{context}: missing required anti-fragmentation keyword(s): "
            + ", ".join(missing)
        )


def main() -> int:
    errors: list[str] = []

    if not CAPABILITIES_DIR.exists():
        errors.append("missing src/foundation/capabilities")
        return fail_many("validate-capabilities", errors)

    if not CAPABILITIES_REGISTRY.is_file():
        errors.append("missing src/registry/capabilities.yaml")
        return fail_many("validate-capabilities", errors)

    for path in BANNED_MAPPING_PATHS:
        if path.exists():
            errors.append(f"banned mapping path exists: {relpath(ROOT, path)}")

    registry_text = CAPABILITIES_REGISTRY.read_text(encoding="utf-8")
    validate_no_personal_references(
        registry_text,
        relpath(ROOT, CAPABILITIES_REGISTRY),
        errors,
    )
    try:
        registry_data = load_yaml_file(CAPABILITIES_REGISTRY)
    except ValidationProblem as exc:
        errors.append(str(exc))
        registry_data = {}

    registered_entries = _validate_registry_format(registry_data, errors)
    validate_expected_count(
        errors,
        "capability registry entrie(s)",
        len(registered_entries),
        EXPECTED_FOUNDATION_CAPABILITY_COUNT,
        relpath(ROOT, CAPABILITIES_REGISTRY),
    )

    _validate_capability_template(errors)

    capability_dirs = visible_child_dirs(CAPABILITIES_DIR, excluded_prefixes=(".", "_"))
    professional_dirs = visible_child_dirs(PROFESSIONAL_SKILLS_DIR)
    domain_extension_dirs = visible_child_dirs(DOMAIN_EXTENSIONS_DIR)
    profile_counts = {
        "recommended": len(professional_dirs),
        "full": len(professional_dirs) + len(domain_extension_dirs),
        "dev": len(professional_dirs) + len(capability_dirs) + len(domain_extension_dirs),
    }

    validate_expected_count(
        errors,
        "professional skill(s)",
        len(professional_dirs),
        EXPECTED_PROFESSIONAL_SKILL_COUNT,
        relpath(ROOT, PROFESSIONAL_SKILLS_DIR),
    )
    validate_expected_count(
        errors,
        "foundation capability(s)",
        len(capability_dirs),
        EXPECTED_FOUNDATION_CAPABILITY_COUNT,
        relpath(ROOT, CAPABILITIES_DIR),
    )
    validate_expected_count(
        errors,
        "domain extension(s)",
        len(domain_extension_dirs),
        EXPECTED_DOMAIN_EXTENSION_COUNT,
        relpath(ROOT, DOMAIN_EXTENSIONS_DIR),
    )
    for profile, expected_count in EXPECTED_PROFILE_TOP_LEVEL_COUNTS.items():
        validate_expected_count(
            errors,
            f"{profile} profile top-level skill(s)",
            profile_counts[profile],
            expected_count,
            "source profile counts",
        )

    for child in sorted(CAPABILITIES_DIR.iterdir()):
        if child.name.startswith(".") and child.name != ".gitkeep":
            errors.append(f"invalid hidden capability path: {relpath(ROOT, child)}")
        if child.is_dir() and child.name.startswith("_") and child.name != "_template":
            errors.append(f"invalid template capability path: {relpath(ROOT, child)}")
        if child.is_file() and child.name not in ALLOWED_CAPABILITIES_ROOT_FILES:
            errors.append(f"unexpected file in capabilities root: {relpath(ROOT, child)}")

    if not capability_dirs:
        if errors:
            return fail_many("validate-capabilities", errors)
        print(
            "validate-capabilities: validated "
            f"{len(registered_entries)} capability registry entries and template."
        )
        return 0

    registered_refs = {
        ref
        for entry in registered_entries
        for ref in (
            entry_ref(
                entry,
                (
                    "changeforge_capability_id",
                    "capability_id",
                    "id",
                    "name",
                    "capability",
                ),
            ),
        )
        if ref
    }
    registered_paths = {
        str((ROOT / path).resolve())
        for entry in registered_entries
        for path in (entry_path(entry),)
        if path
    }

    capability_ids: dict[str, Path] = {}
    capability_names: dict[str, Path] = {}
    implemented_capabilities: list[tuple[str, str | None, str | None, str]] = []

    for capability_dir in capability_dirs:
        context = relpath(ROOT, capability_dir)
        skill_file = capability_dir / "SKILL.md"
        if not skill_file.is_file():
            errors.append(f"{context}: missing SKILL.md")
            continue

        file_context = relpath(ROOT, skill_file)
        try:
            metadata, raw_frontmatter, body = parse_frontmatter(skill_file)
        except ValidationProblem as exc:
            errors.append(str(exc).replace(str(ROOT) + "/", ""))
            continue

        validate_required_frontmatter(metadata, REQUIRED_FRONTMATTER, file_context, errors)

        if metadata.get("changeforge_kind") != "foundation-capability":
            errors.append(
                f"{file_context}: frontmatter 'changeforge_kind' must be foundation-capability"
            )

        capability_id = metadata.get("changeforge_capability_id")
        normalized_capability_id = _normalize_capability_id(capability_id)
        if normalized_capability_id is None:
            errors.append(
                f"{file_context}: frontmatter 'changeforge_capability_id' must be a "
                "valid capability id"
            )
        elif normalized_capability_id in capability_ids:
            errors.append(
                f"{file_context}: duplicate capability id also declared in "
                f"{relpath(ROOT, capability_ids[normalized_capability_id])}"
            )
        else:
            capability_ids[normalized_capability_id] = skill_file

        name = metadata.get("name")
        validate_name(name, file_context, errors)
        if isinstance(name, str):
            if name != capability_dir.name:
                errors.append(f"{file_context}: frontmatter 'name' must match directory name")
            if name in capability_names:
                errors.append(
                    f"{file_context}: duplicate capability name also declared in "
                    f"{relpath(ROOT, capability_names[name])}"
                )
            else:
                capability_names[name] = skill_file

        validate_description_length(metadata.get("description"), 120, 700, file_context, errors)

        implemented_capabilities.append(
            (
                file_context,
                normalized_capability_id,
                name if isinstance(name, str) else None,
                str(capability_dir.resolve()),
            )
        )

        validate_required_sections(body, REQUIRED_SECTIONS, file_context, errors)
        validate_no_beginner_sections(body, file_context, errors)
        validate_no_personal_references(raw_frontmatter + "\n" + body, file_context, errors)
        _validate_targeted_content_keywords(
            name if isinstance(name, str) else None,
            body,
            file_context,
            errors,
        )

    for context, capability_id, name, capability_path in implemented_capabilities:
        refs = {ref for ref in (capability_id, name) if ref}
        if not refs.intersection(registered_refs) and capability_path not in registered_paths:
            errors.append(f"{context}: implemented capability is missing from capabilities.yaml")

    solution_capability = next(
        (
            item
            for item in implemented_capabilities
            if item[2] == "solution-optimality-evaluation"
        ),
        None,
    )
    if solution_capability is None:
        errors.append("solution-optimality-evaluation: capability 82 source is missing")
    elif solution_capability[1] != "82":
        errors.append(
            f"{solution_capability[0]}: solution-optimality-evaluation must use "
            "changeforge_capability_id 82"
        )

    if errors:
        return fail_many("validate-capabilities", errors)

    print(f"validate-capabilities: validated {len(capability_dirs)} foundation capability(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
