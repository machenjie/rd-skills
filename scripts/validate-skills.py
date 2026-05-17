#!/usr/bin/env python3
"""Validate authored professional skills."""

from __future__ import annotations

from pathlib import Path

from validation_utils import (
    ValidationProblem,
    fail_many,
    parse_frontmatter,
    relpath,
    validate_allowed_tools_warning,
    validate_description_length,
    validate_name,
    validate_no_beginner_sections,
    validate_no_personal_references,
    validate_required_frontmatter,
    validate_required_sections,
)


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "src" / "professional-skills"
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

    skill_dirs = sorted(
        path for path in SKILLS_DIR.iterdir() if path.is_dir() and path.name != ".gitkeep"
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
