#!/usr/bin/env python3
"""Warn when a SKILL.md exceeds the skill-content governance budget.

Warning-only by default (exit 0) so it never blocks the build. Pass --strict to
exit non-zero on any unexcepted finding. Parsing logic and thresholds are reused
from scripts/audit-skill-content.py so there is a single source of truth.
Deliberate overages are recorded in config/skill-content-exceptions.yaml.

Checks:
  body_lines      body length over the per-kind heavy gate (all kinds)
  section_lines   a top-level section over the section gate (always-loaded bodies)
  table_rows      a table over the row gate (always-loaded bodies)
  duplicate_block an inline 'Solution Optimality Self-Check' still carrying the full
                  shared block instead of a summary (professional skills)
  repeated_phrase too many significant lines shared with >= 3 other skills, excluding
                  the required Reference Loading Policy contract (professional skills)

Foundation capabilities are themselves selectively-loaded references, so section and
table size are not gated for them; only their overall body length is.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from collections import defaultdict
from pathlib import Path

from validation_utils import (
    ValidationProblem,
    fail_many,
    load_yaml_file,
    parse_frontmatter,
    relpath,
)


ROOT = Path(__file__).resolve().parents[1]
PROFESSIONAL_SKILLS_DIR = ROOT / "src" / "professional-skills"
CAPABILITIES_DIR = ROOT / "src" / "foundation" / "capabilities"
DOMAIN_EXTENSIONS_DIR = ROOT / "src" / "domain-extensions"
EXCEPTIONS_FILE = ROOT / "config" / "skill-content-exceptions.yaml"

REPEATED_PHRASE_WARN = 6
ALWAYS_LOADED = {"professional-skill", "domain-extension"}
VALID_ALLOW = {
    "body_lines",
    "section_lines",
    "table_rows",
    "duplicate_block",
    "repeated_phrase",
}
REQUIRED_EXCEPTION_FIELDS = ("owner", "review_after", "mitigation")
GENERIC_EXCEPTION_REASONS = {
    "professionalism enhancement",
    "professional enhancement",
    "needed for professionalism",
    "too long",
    "known issue",
}
REFERENCE_IMMOVABLE_MARKERS = (
    "cannot move to reference",
    "cannot be moved to reference",
    "must stay in skill.md",
    "must stay in the body",
    "always-loaded decision",
    "body-only",
)


def _load_audit_module():
    spec = importlib.util.spec_from_file_location(
        "audit_skill_content", ROOT / "scripts" / "audit-skill-content.py"
    )
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise RuntimeError("could not load audit-skill-content.py")
    module = importlib.util.module_from_spec(spec)
    # Register before exec so dataclasses can resolve the module's namespace.
    sys.modules["audit_skill_content"] = module
    spec.loader.exec_module(module)
    return module


audit = _load_audit_module()
THRESHOLDS = audit.THRESHOLDS
BODY_GATES = {
    "professional-skill": THRESHOLDS["professional_heavy_lines"],
    "foundation-capability": THRESHOLDS["foundation_heavy_lines"],
    "domain-extension": THRESHOLDS["domain_heavy_lines"],
}
KIND_BASE_LEVEL = audit.KIND_BASE_LEVEL


def _collect_files() -> list[tuple[str, Path]]:
    files: list[tuple[str, Path]] = []
    for kind, root in (
        ("professional-skill", PROFESSIONAL_SKILLS_DIR),
        ("foundation-capability", CAPABILITIES_DIR),
        ("domain-extension", DOMAIN_EXTENSIONS_DIR),
    ):
        if not root.is_dir():
            continue
        for skill_dir in sorted(root.iterdir()):
            if not skill_dir.is_dir() or skill_dir.name.startswith((".", "_")):
                continue
            skill_file = skill_dir / "SKILL.md"
            if skill_file.is_file():
                files.append((kind, skill_file))
    return files


def load_exceptions(errors: list[str]) -> dict[str, set[str]]:
    if not EXCEPTIONS_FILE.is_file():
        return {}
    try:
        data = load_yaml_file(EXCEPTIONS_FILE)
    except ValidationProblem as exc:
        errors.append(str(exc))
        return {}
    if not isinstance(data, dict):
        errors.append(f"{relpath(ROOT, EXCEPTIONS_FILE)}: must be a mapping")
        return {}

    result: dict[str, set[str]] = {}
    for index, entry in enumerate(data.get("exceptions", []) or []):
        context = f"{relpath(ROOT, EXCEPTIONS_FILE)}:exceptions[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{context}: must be a mapping")
            continue
        path = entry.get("path")
        allow = entry.get("allow")
        reason = entry.get("reason")
        if not isinstance(path, str) or not path.strip():
            errors.append(f"{context}: missing string field 'path'")
            continue
        if not isinstance(reason, str) or not reason.strip():
            errors.append(f"{context}: exception for '{path}' must record a 'reason'")
        elif reason.strip().casefold() in GENERIC_EXCEPTION_REASONS:
            errors.append(
                f"{context}: exception for '{path}' has a generic reason; "
                "state the concrete decision-critical content being retained"
            )
        elif not any(marker in reason.casefold() for marker in REFERENCE_IMMOVABLE_MARKERS):
            errors.append(
                f"{context}: exception for '{path}' must explain why the overage "
                "cannot move to references"
            )
        for field_name in REQUIRED_EXCEPTION_FIELDS:
            value = entry.get(field_name)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{context}: exception for '{path}' must record '{field_name}'")
        allow_set: set[str] = set()
        if not isinstance(allow, list) or not allow:
            errors.append(f"{context}: 'allow' must be a non-empty list")
        else:
            for token in allow:
                if token not in VALID_ALLOW:
                    errors.append(f"{context}: unknown allow token '{token}'")
                else:
                    allow_set.add(token)
        normalized = path.strip().replace("\\", "/")
        if not (ROOT / normalized).is_file():
            errors.append(f"{context}: path does not exist: {normalized}")
        result[normalized] = allow_set
    return result


def _body_of(path: Path) -> str:
    try:
        _metadata, _raw, body = parse_frontmatter(path)
    except ValidationProblem:
        return path.read_text(encoding="utf-8")
    return body


def _significant_excluding_reference_policy(body: str) -> set[str]:
    sections = audit.parse_sections(body)
    policy = next(
        (s for s in sections if s.title.casefold() == "reference loading policy"),
        None,
    )
    excluded: set[str] = set()
    if policy is not None:
        for line in policy.text.splitlines():
            normalized = audit._normalize_significant_line(line)
            if normalized:
                excluded.add(normalized)
    return {
        line for line in audit._significant_lines(body) if line not in excluded
    }


def check() -> tuple[list[tuple[str, str, str]], list[str]]:
    """Return (findings, exception_errors). Each finding is (path, check, message)."""
    errors: list[str] = []
    exceptions = load_exceptions(errors)
    files = _collect_files()

    # Cross-file repeated-phrase frequency, excluding the required policy contract.
    significant_by_file: dict[str, set[str]] = {}
    frequency: dict[str, int] = defaultdict(int)
    for _kind, path in files:
        rel = relpath(ROOT, path).replace("\\", "/")
        lines = _significant_excluding_reference_policy(_body_of(path))
        significant_by_file[rel] = lines
        for line in lines:
            frequency[line] += 1

    findings: list[tuple[str, str, str]] = []
    for kind, path in files:
        rel = relpath(ROOT, path).replace("\\", "/")
        allowed = exceptions.get(rel, set())
        body = _body_of(path)
        line_count = len(body.splitlines())
        sections = audit.parse_sections(body)

        if line_count > BODY_GATES[kind] and "body_lines" not in allowed:
            findings.append(
                (rel, "body_lines", f"body is {line_count} lines (> {BODY_GATES[kind]} for {kind})")
            )

        if kind in ALWAYS_LOADED:
            base_level = KIND_BASE_LEVEL[kind]
            for section in sections:
                if (
                    section.level == base_level
                    and section.line_count > THRESHOLDS["section_split_lines"]
                    and "section_lines" not in allowed
                ):
                    findings.append(
                        (
                            rel,
                            "section_lines",
                            f"section '{section.title}' is {section.line_count} lines "
                            f"(> {THRESHOLDS['section_split_lines']})",
                        )
                    )
            _count, _largest, oversized_tables = audit._count_tables(body)
            for rows in oversized_tables:
                if "table_rows" not in allowed:
                    findings.append(
                        (rel, "table_rows", f"table has {rows} rows (> {THRESHOLDS['table_move_rows']})")
                    )

        if kind == "professional-skill":
            optimality = next(
                (s for s in sections if "solution optimality" in s.title.casefold()),
                None,
            )
            if (
                optimality is not None
                and optimality.line_count > 20
                and "duplicate_block" not in allowed
            ):
                findings.append(
                    (
                        rel,
                        "duplicate_block",
                        f"inline 'Solution Optimality Self-Check' is {optimality.line_count} lines; "
                        "reduce to a summary and move the method into references/",
                    )
                )

            shared = sum(
                1
                for line in significant_by_file[rel]
                if frequency[line] >= THRESHOLDS["common_phrase_min_files"]
            )
            if shared > REPEATED_PHRASE_WARN and "repeated_phrase" not in allowed:
                findings.append(
                    (
                        rel,
                        "repeated_phrase",
                        f"{shared} significant lines are shared with >= "
                        f"{THRESHOLDS['common_phrase_min_files']} skills (excluding the policy contract)",
                    )
                )

    return findings, errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Warn when SKILL.md content exceeds governance budget."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when any unexcepted finding is present.",
    )
    args = parser.parse_args()

    findings, errors = check()
    if errors:
        # Malformed exceptions config is always a hard error.
        return fail_many("validate-skill-content-size", errors)

    if not findings:
        print("validate-skill-content-size: all SKILL.md bodies within governance budget.")
        return 0

    grouped: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for path, check_type, message in findings:
        grouped[path].append((check_type, message))

    label = "ERROR" if args.strict else "WARN"
    for path in sorted(grouped):
        for check_type, message in grouped[path]:
            print(f"validate-skill-content-size: {label}: {path}: [{check_type}] {message}")

    print(
        f"validate-skill-content-size: {len(findings)} finding(s) across {len(grouped)} file(s). "
        "Record deliberate overages in config/skill-content-exceptions.yaml."
    )
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
