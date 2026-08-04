#!/usr/bin/env python3
"""Synchronize Registry-owned Targeted References into source Skill roots."""

from __future__ import annotations

import argparse
from pathlib import Path

from validation_utils import (
    ValidationProblem,
    domain_registry_contract_errors,
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


def synchronize(
    *, root: Path = ROOT, write: bool = False
) -> tuple[list[str], list[str], int]:
    """Return drift, errors, and checked count; write only when explicitly asked."""

    errors: list[str] = []
    source_root = (root / "src").resolve()
    loaded: list[tuple[str, str, list[object]]] = []
    for filename, key in REGISTRIES:
        registry_path = root / "src" / "registry" / filename
        try:
            registry = load_yaml_file(registry_path)
        except ValidationProblem as exc:
            errors.append(str(exc))
            continue
        if filename == "domain-skills.yaml":
            errors.extend(domain_registry_contract_errors(registry, filename))
        entries = registry.get(key) if isinstance(registry, dict) else None
        if not isinstance(entries, list):
            errors.append(f"{filename}:{key} must be a list")
            continue
        loaded.append((filename, key, entries))
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                errors.append(f"{filename}:{key}[{index}] must be a mapping")
                continue
            name = entry.get("name")
            path_value = entry.get("path")
            if not isinstance(name, str) or not isinstance(path_value, str):
                errors.append(f"{filename}:{key}[{index}] needs name and path")
    if errors:
        return [], errors, 0

    staged: list[tuple[str, Path, str, str]] = []
    for filename, key, entries in loaded:
        for index, entry in enumerate(entries):
            assert isinstance(entry, dict)
            name = entry.get("name")
            path_value = entry.get("path")
            assert isinstance(name, str)
            assert isinstance(path_value, str)
            skill_file = (root / path_value / "SKILL.md").resolve()
            context = f"{filename}:{name}"
            if not path_is_within(source_root, skill_file):
                errors.append(f"{context}: Skill path escapes src/")
                continue
            try:
                source = skill_file.read_text(encoding="utf-8")
                contracts = reference_contracts(
                    entry.get("reference_index"),
                    f"{context}.reference_index",
                    owner=name,
                )
                rendered = render_targeted_reference_section(
                    source, contracts, name
                )
            except (OSError, ValidationProblem) as exc:
                errors.append(f"{context}: {exc}")
                continue
            relative = skill_file.relative_to(root.resolve()).as_posix()
            staged.append((relative, skill_file, source, rendered))
    if errors:
        return [], errors, 0

    drift = [
        relative
        for relative, _skill_file, source, rendered in staged
        if rendered != source
    ]
    if write:
        for _relative, skill_file, source, rendered in staged:
            if rendered != source:
                skill_file.write_text(rendered, encoding="utf-8")
    checked = len(staged)
    return drift, errors, checked


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="rewrite drifting source sections; default mode only checks",
    )
    args = parser.parse_args(argv)
    drift, errors, checked = synchronize(write=args.write)
    if errors:
        return fail_many("sync-targeted-references", errors)
    if drift and not args.write:
        preview = ", ".join(drift[:10])
        suffix = " ..." if len(drift) > 10 else ""
        return fail_many(
            "sync-targeted-references",
            [
                f"{len(drift)} source Targeted References section(s) drift: "
                f"{preview}{suffix}; run with --write"
            ],
        )
    action = "updated" if args.write else "checked"
    print(
        f"sync-targeted-references: {action} {checked} source Skill root(s); "
        f"changed={len(drift)}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
