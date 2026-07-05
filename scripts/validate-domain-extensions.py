#!/usr/bin/env python3
"""Validate authored domain extensions."""

from __future__ import annotations

import re
from pathlib import Path

from validation_utils import (
    EXPECTED_DOMAIN_EXTENSION_COUNT,
    NAME_RE,
    ValidationProblem,
    count_markdown_list_items,
    entry_path,
    entry_ref,
    extract_section_body,
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
    validate_skill_text_quality,
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
    "Domain Scope",
    "Strong Domain Signals",
    "Weak Signals That Are Not Enough",
    "Do Not Use When",
    "Required Professional Owner Skill",
    "Domain-Specific Non-Negotiable Rules",
    "Domain Risk Escalation",
    "Domain Reference Loading Policy",
    "Domain Output Addendum",
    "Domain Quality Gate",
    "Return / Escalate",
    "Completion Criteria",
)


def _validate_description_prefix(description: object, context: str, errors: list[str]) -> None:
    if not isinstance(description, str):
        return
    if not description.startswith("Use this domain extension when "):
        errors.append(
            f"{context}: frontmatter 'description' must start with "
            "'Use this domain extension when '"
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


def _professional_skill_names() -> set[str]:
    return {path.name for path in visible_child_dirs(ROOT / "src" / "professional-skills")}


def _validate_domain_section_semantics(
    body: str,
    context: str,
    extension_dir: Path,
    professional_names: set[str],
    errors: list[str],
) -> None:
    """Validate domain routing semantics that section headings alone cannot prove."""
    validate_skill_text_quality(body, context, errors)

    strong = extract_section_body(body, "Strong Domain Signals") or ""
    if count_markdown_list_items(strong) < 5:
        errors.append(f"{context}: Strong Domain Signals must contain at least five concrete signals")

    weak = extract_section_body(body, "Weak Signals That Are Not Enough") or ""
    folded_weak = weak.casefold()
    if "only because" not in folded_weak or "unless" not in folded_weak:
        errors.append(
            f"{context}: Weak Signals That Are Not Enough must reject keyword-only "
            "matches and state the domain-behavior condition"
        )

    owners = extract_section_body(body, "Required Professional Owner Skill") or ""
    referenced_owners = set(
        item.strip("` ")
        for item in re.findall(r"^\s*[-*]\s+`?([a-z0-9]+(?:-[a-z0-9]+)*)`?", owners, re.M)
    )
    if not referenced_owners.intersection(professional_names):
        errors.append(
            f"{context}: Required Professional Owner Skill must list at least one "
            "registered professional skill"
        )

    policy = extract_section_body(body, "Domain Reference Loading Policy") or ""
    folded_policy = policy.casefold()
    for phrase in (
        "do not load all domain references",
        "primary professional owner",
        "strong domain signal",
        "keyword-only",
    ):
        if phrase not in folded_policy:
            errors.append(f"{context}: Domain Reference Loading Policy must mention '{phrase}'")

    references_dir = extension_dir / "references"
    if references_dir.is_dir():
        for reference_path in sorted(references_dir.glob("*.md")):
            reference_name = reference_path.name
            if reference_name not in policy:
                errors.append(
                    f"{context}: Domain Reference Loading Policy must index "
                    f"references/{reference_name}"
                )


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
    professional_names = _professional_skill_names()

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

        description = metadata.get("description")
        validate_description_length(description, 120, 700, file_context, errors)
        _validate_description_prefix(description, file_context, errors)

        if metadata.get("changeforge_kind") != "domain-extension":
            errors.append(
                f"{file_context}: frontmatter 'changeforge_kind' must be domain-extension"
            )

        validate_required_sections(
            body,
            REQUIRED_SECTIONS,
            file_context,
            errors,
            require_order=True,
        )
        _validate_domain_section_semantics(
            body,
            file_context,
            extension_dir,
            professional_names,
            errors,
        )
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
