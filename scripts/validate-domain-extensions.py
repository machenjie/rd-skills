#!/usr/bin/env python3
"""Validate authored domain extensions."""

from __future__ import annotations

from pathlib import Path

from validation_utils import (
    EXPECTED_DOMAIN_EXTENSION_COUNT,
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
    validate_expected_count,
    validate_name,
    validate_no_beginner_sections,
    validate_no_personal_references,
    validate_required_frontmatter,
    validate_required_sections,
    visible_child_dirs,
)


ROOT = Path(__file__).resolve().parents[1]
DOMAIN_EXTENSIONS_DIR = ROOT / "src" / "domain-extensions"
DOMAIN_EXTENSIONS_REGISTRY = ROOT / "src" / "registry" / "domain-extensions.yaml"
BANNED_MAPPING_PATHS = (
    ROOT / "registry" / "toolbox.yaml",
    ROOT / "src" / "registry" / "toolbox.yaml",
    ROOT / "src" / "toolbox",
)
REQUIRED_FRONTMATTER = (
    "name",
    "description",
    "license",
    "changeforge_kind",
    "changeforge_version",
)
REQUIRED_SECTIONS = (
    "Mission",
    "Trigger Signals",
    "Do Not Use When",
    "Non-Negotiable Rules",
    "Industry Benchmarks",
    "Domain Risk Model",
    "Linked Foundation Capabilities",
    "Linked Professional Skills",
    "Critical Details",
    "Failure Modes",
    "Output Contract",
    "Quality Gate",
    "Handoff",
    "Completion Criteria",
)


def _validate_registry_format(registry_data: object, errors: list[str]) -> list[object]:
    entries = registry_items(
        registry_data,
        "domain_extensions",
        DOMAIN_EXTENSIONS_REGISTRY,
        errors,
    )
    seen_names: dict[str, int] = {}
    seen_paths: dict[str, int] = {}

    for index, entry in enumerate(entries):
        context = f"domain-extensions.yaml:domain_extensions[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{context}: entry must be a mapping")
            continue

        name = entry.get("name")
        if not isinstance(name, str) or not NAME_RE.fullmatch(name):
            errors.append(f"{context}: field 'name' must be lowercase hyphen-separated text")
            name = None
        elif name in seen_names:
            errors.append(
                f"{context}: duplicate name '{name}' first used at "
                f"domain-extensions.yaml:domain_extensions[{seen_names[name]}]"
            )
        else:
            seen_names[name] = index

        path = entry.get("path")
        expected_path = f"src/domain-extensions/{name}" if name else None
        if not isinstance(path, str) or not path:
            errors.append(f"{context}: field 'path' must be a non-empty string")
        elif path.startswith("src/toolbox") or "toolbox.yaml" in path:
            errors.append(f"{context}: path must not reference banned mapping content")
        elif expected_path and path != expected_path:
            errors.append(f"{context}: field 'path' must be {expected_path}")
        elif path in seen_paths:
            errors.append(
                f"{context}: duplicate path '{path}' first used at "
                f"domain-extensions.yaml:domain_extensions[{seen_paths[path]}]"
            )
        else:
            seen_paths[path] = index

        status = entry.get("status")
        if status is not None and status != "implemented":
            errors.append(f"{context}: field 'status' must be implemented when present")

    return entries


def main() -> int:
    errors: list[str] = []

    for path in BANNED_MAPPING_PATHS:
        if path.exists():
            errors.append(f"banned personal asset mapping path exists: {relpath(ROOT, path)}")

    if not DOMAIN_EXTENSIONS_DIR.exists():
        errors.append("missing src/domain-extensions")
        return fail_many("validate-domain-extensions", errors)

    if not DOMAIN_EXTENSIONS_REGISTRY.is_file():
        errors.append("missing src/registry/domain-extensions.yaml")
        return fail_many("validate-domain-extensions", errors)

    registry_text = DOMAIN_EXTENSIONS_REGISTRY.read_text(encoding="utf-8")
    validate_no_personal_references(
        registry_text,
        relpath(ROOT, DOMAIN_EXTENSIONS_REGISTRY),
        errors,
    )
    try:
        registry_data = load_yaml_file(DOMAIN_EXTENSIONS_REGISTRY)
    except ValidationProblem as exc:
        errors.append(str(exc))
        registry_data = {}

    registered_entries = _validate_registry_format(registry_data, errors)
    validate_expected_count(
        errors,
        "domain extension registry entrie(s)",
        len(registered_entries),
        EXPECTED_DOMAIN_EXTENSION_COUNT,
        relpath(ROOT, DOMAIN_EXTENSIONS_REGISTRY),
    )

    extension_dirs = visible_child_dirs(DOMAIN_EXTENSIONS_DIR)
    validate_expected_count(
        errors,
        "domain extension(s)",
        len(extension_dirs),
        EXPECTED_DOMAIN_EXTENSION_COUNT,
        relpath(ROOT, DOMAIN_EXTENSIONS_DIR),
    )

    for child in sorted(DOMAIN_EXTENSIONS_DIR.iterdir()):
        if child.name.startswith(".") and child.name != ".gitkeep":
            errors.append(f"invalid hidden domain extension path: {relpath(ROOT, child)}")
        if child.is_file() and child.name != ".gitkeep":
            errors.append(f"unexpected file in domain extensions root: {relpath(ROOT, child)}")

    registered_refs = {
        ref
        for entry in registered_entries
        for ref in (entry_ref(entry, ("name", "domain_extension", "domain_extension_id", "id")),)
        if ref
    }
    registered_paths = {
        str((ROOT / path).resolve())
        for entry in registered_entries
        for path in (entry_path(entry),)
        if path
    }

    names: dict[str, Path] = {}
    implemented_extensions: list[tuple[str, str | None, str]] = []

    for extension_dir in extension_dirs:
        context = relpath(ROOT, extension_dir)
        skill_file = extension_dir / "SKILL.md"
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

        name = metadata.get("name")
        validate_name(name, file_context, errors)
        if isinstance(name, str):
            if name != extension_dir.name:
                errors.append(f"{file_context}: frontmatter 'name' must match directory name")
            if name in names:
                errors.append(
                    f"{file_context}: duplicate domain extension name also declared in "
                    f"{relpath(ROOT, names[name])}"
                )
            else:
                names[name] = skill_file

        validate_description_length(metadata.get("description"), 120, 700, file_context, errors)

        if metadata.get("changeforge_kind") != "domain-extension":
            errors.append(
                f"{file_context}: frontmatter 'changeforge_kind' must be domain-extension"
            )

        validate_required_sections(body, REQUIRED_SECTIONS, file_context, errors)
        validate_no_beginner_sections(body, file_context, errors)
        validate_no_personal_references(raw_frontmatter + "\n" + body, file_context, errors)

        implemented_extensions.append(
            (
                file_context,
                name if isinstance(name, str) else None,
                str(extension_dir.resolve()),
            )
        )

    for context, name, extension_path in implemented_extensions:
        if name not in registered_refs and extension_path not in registered_paths:
            errors.append(f"{context}: implemented domain extension is missing from domain-extensions.yaml")

    if errors:
        return fail_many("validate-domain-extensions", errors)

    print(f"validate-domain-extensions: validated {len(extension_dirs)} domain extension(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
