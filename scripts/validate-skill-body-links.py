#!/usr/bin/env python3
"""Validate local links in all four authored Skill layers."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

from validation_utils import (
    ValidationProblem,
    fail_many,
    load_yaml_file,
    path_is_within,
    reference_contracts,
    render_targeted_reference_section,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRIES = (
    ("control-skills.yaml", "control_skills"),
    ("professional-skills.yaml", "professional_skills"),
    ("foundation-skills.yaml", "foundation_skills"),
    ("domain-skills.yaml", "domain_skills"),
)
LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")


def main() -> int:
    errors: list[str] = []
    skills: list[tuple[Path, str, list[dict[str, str]]]] = []
    for file_name, key in REGISTRIES:
        path = ROOT / "src" / "registry" / file_name
        try:
            data = load_yaml_file(path)
        except ValidationProblem as exc:
            errors.append(str(exc))
            continue
        entries = data.get(key) if isinstance(data, dict) else None
        if not isinstance(entries, list):
            errors.append(f"{file_name}:{key} must be a list")
            continue
        for entry in entries:
            if (
                not isinstance(entry, dict)
                or not isinstance(entry.get("name"), str)
                or not isinstance(entry.get("path"), str)
            ):
                continue
            name = entry["name"]
            try:
                contracts = reference_contracts(
                    entry.get("reference_index"),
                    f"{file_name}:{name}.reference_index",
                    owner=name,
                )
            except ValidationProblem as exc:
                errors.append(str(exc))
                continue
            skills.append(((ROOT / entry["path"]).resolve(), name, contracts))
    checked = 0
    for skill_root, name, contracts in skills:
        skill_file = skill_root / "SKILL.md"
        try:
            source = skill_file.read_text(encoding="utf-8")
            canonical = render_targeted_reference_section(
                source, contracts, name
            )
        except (OSError, ValidationProblem) as exc:
            errors.append(f"{name}: cannot validate Targeted References: {exc}")
        else:
            if canonical != source:
                errors.append(
                    f"{skill_file.relative_to(ROOT)}: Targeted References must "
                    "exactly match the Registry projection; run "
                    "scripts/sync-targeted-references.py --write"
                )
        for markdown in sorted(skill_root.rglob("*.md")):
            checked += 1
            text = markdown.read_text(encoding="utf-8")
            for raw_target in LINK_RE.findall(text):
                target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
                if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                    continue
                path_text = unquote(target.split("#", 1)[0])
                if not path_text:
                    continue
                candidate = (markdown.parent / path_text).resolve()
                if not path_is_within(skill_root, candidate):
                    errors.append(f"{markdown.relative_to(ROOT)}: local link escapes Skill root: {target}")
                elif not candidate.exists():
                    errors.append(f"{markdown.relative_to(ROOT)}: missing local link target: {target}")
    if errors:
        return fail_many("validate-skill-body-links", errors)
    print(f"validate-skill-body-links: validated local links in {checked} authored Markdown file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
