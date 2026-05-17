#!/usr/bin/env python3
"""Validate authored professional skills."""

from __future__ import annotations

from pathlib import Path

from validation_utils import (
    EXPECTED_DOMAIN_EXTENSION_COUNT,
    EXPECTED_FOUNDATION_CAPABILITY_COUNT,
    EXPECTED_PROFESSIONAL_SKILL_COUNT,
    EXPECTED_PROFILE_TOP_LEVEL_COUNTS,
    ValidationProblem,
    fail_many,
    parse_frontmatter,
    relpath,
    validate_allowed_tools_warning,
    validate_description_length,
    validate_name,
    validate_no_beginner_sections,
    validate_no_personal_references,
    validate_expected_count,
    validate_required_frontmatter,
    validate_required_sections,
    visible_child_dirs,
)


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "src" / "professional-skills"
CAPABILITIES_DIR = ROOT / "src" / "foundation" / "capabilities"
DOMAIN_EXTENSIONS_DIR = ROOT / "src" / "domain-extensions"
BANNED_PATHS = (
    ROOT / "src" / "toolbox",
    ROOT / "registry" / "toolbox.yaml",
    ROOT / "src" / "registry" / "toolbox.yaml",
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
    "When To Use",
    "Do Not Use When",
    "Non-Negotiable Rules",
    "Industry Benchmarks",
    "Technical Selection Criteria",
    "Risk Escalation Rules",
    "Critical Details",
    "Failure Modes",
    "Output Contract",
    "Quality Gate",
    "Handoff",
    "Completion Criteria",
)


def main() -> int:
    errors: list[str] = []

    for path in BANNED_PATHS:
        if path.exists():
            errors.append(f"banned personal asset mapping path exists: {relpath(ROOT, path)}")

    if not SKILLS_DIR.exists():
        errors.append("missing src/professional-skills")
        return fail_many("validate-skills", errors)

    skill_dirs = visible_child_dirs(SKILLS_DIR)
    capability_dirs = visible_child_dirs(CAPABILITIES_DIR, excluded_prefixes=(".", "_"))
    domain_extension_dirs = visible_child_dirs(DOMAIN_EXTENSIONS_DIR)
    profile_counts = {
        "recommended": len(skill_dirs),
        "full": len(skill_dirs) + len(domain_extension_dirs),
        "dev": len(skill_dirs) + len(capability_dirs) + len(domain_extension_dirs),
    }

    validate_expected_count(
        errors,
        "professional skill(s)",
        len(skill_dirs),
        EXPECTED_PROFESSIONAL_SKILL_COUNT,
        relpath(ROOT, SKILLS_DIR),
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

    for child in sorted(SKILLS_DIR.iterdir()):
        if child.name.startswith(".") and child.name != ".gitkeep":
            errors.append(f"invalid hidden skill path: {relpath(ROOT, child)}")
        if child.is_file() and child.name != ".gitkeep":
            errors.append(f"unexpected file in professional skills root: {relpath(ROOT, child)}")

    if not skill_dirs:
        if errors:
            return fail_many("validate-skills", errors)
        print("validate-skills: no professional skills found; nothing to validate yet.")
        return 0

    names: dict[str, Path] = {}
    for skill_dir in skill_dirs:
        context = relpath(ROOT, skill_dir)
        skill_file = skill_dir / "SKILL.md"
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
            if name != skill_dir.name:
                errors.append(f"{file_context}: frontmatter 'name' must match directory name")
            if name in names:
                errors.append(
                    f"{file_context}: duplicate skill name also declared in {relpath(ROOT, names[name])}"
                )
            else:
                names[name] = skill_file

        validate_description_length(metadata.get("description"), 120, 700, file_context, errors)

        if metadata.get("changeforge_kind") != "professional-skill":
            errors.append(
                f"{file_context}: frontmatter 'changeforge_kind' must be professional-skill"
            )

        validate_required_sections(body, REQUIRED_SECTIONS, file_context, errors)
        validate_no_beginner_sections(body, file_context, errors)
        validate_no_personal_references(raw_frontmatter + "\n" + body, file_context, errors)
        validate_allowed_tools_warning(metadata, raw_frontmatter, body, file_context, errors)

    if errors:
        return fail_many("validate-skills", errors)

    print(f"validate-skills: validated {len(skill_dirs)} professional skill(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
