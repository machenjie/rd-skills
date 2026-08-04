#!/usr/bin/env python3
"""Validate AI-executable Professional Skills."""

from __future__ import annotations

import re
from pathlib import Path

from capability_coverage import fixture_ids, validate_capability_coverage
from validation_utils import (
    EXPECTED_PROFESSIONAL_SKILL_COUNT,
    ValidationProblem,
    empty_markdown_headings,
    fail_many,
    load_yaml_file,
    parse_frontmatter,
    reference_paths,
    validate_ai_readability,
    validate_ai_markdown_format,
    validate_required_sections,
)


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / "src" / "professional-skills"
REGISTRY = ROOT / "src" / "registry" / "professional-skills.yaml"
CAPABILITY_MATRIX = ROOT / "evals" / "capability-coverage" / "matrix.yaml"
REQUIRED_SECTIONS = (
    "Role",
    "When To Use",
    "Do Not Use",
    "Required Inputs",
    "Professional Decision Rules",
    "High-Value Gotchas",
    "Execution Checklist",
    "Stop / Escalation Conditions",
    "Output Contract",
    "Targeted References",
)
FORBIDDEN = (
    "task context compiler",
    "runtime dispatch bridge",
    "private evidence ledger",
    "runtime evidence ledger",
    "hidden evidence ledger",
    "runtime identity",
    "runtime digest",
    "hidden pack",
    ".changeforge-packs",
    "phase fsm",
    "finding id",
)
STATIC_ROLES = ("main-control-agent", "analysis-agent", "task-agent", "review-agent")
MODE_NAMES = {
    "analysis-agent": "Analysis",
    "task-agent": "Task",
    "review-agent": "Review",
}
GENERIC_TRIGGER_PHRASE = "implementing, reviewing, planning, or validating"
MAX_ROOT_SKILL_LINES = 120
GENERIC_PERMISSION_PATTERNS = {
    "analysis-profile-permission": re.compile(r"\bread/search-only\b", re.IGNORECASE),
    "task-profile-close": re.compile(
        r"\b(?:post-edit validation|do not claim final independent review)\b",
        re.IGNORECASE,
    ),
    "review-profile-permission": re.compile(
        r"\b(?:read-only|non-modifying|never edit)\b",
        re.IGNORECASE,
    ),
}


def validate_capability_coverage_matrix(
    matrix_path: Path = CAPABILITY_MATRIX,
    *,
    root: Path = ROOT,
    professional_registry: object | None = None,
) -> list[str]:
    """Validate the matrix's Professional owner and Profile projection."""

    registry_path = root / "src" / "registry" / "professional-skills.yaml"
    if professional_registry is None and registry_path.is_file():
        professional_registry = load_yaml_file(registry_path)
    evidence_documents = [
        (path.relative_to(root).as_posix(), load_yaml_file(path))
        for path in (
            root / "evals" / "capability-coverage" / "admission-cases.yaml",
            root / "evals" / "routing" / "capability-coverage-cases.yaml",
        )
        if path.is_file()
    ]
    evidence_catalog, evidence_errors = fixture_ids(*evidence_documents)
    return [
        *evidence_errors,
        *validate_capability_coverage(
            matrix_path,
            root=root,
            professional_registry=professional_registry,
            evidence_ids=evidence_catalog,
        ),
    ]


def _section(body: str, title: str) -> str:
    match = re.search(
        rf"^## {re.escape(title)}\s*$\n(.*?)(?=^## |\Z)",
        body,
        flags=re.MULTILINE | re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def _role_labeled_line(section: str, mode: str, role: str) -> str | None:
    match = re.search(
        rf"^- \*\*{re.escape(mode)} mode \(`{re.escape(role)}`\):\*\*\s*(.+)$",
        section,
        flags=re.MULTILINE,
    )
    return match.group(1).strip() if match else None


def _generic_permission_scaffold_findings(body: str) -> list[str]:
    """Reject duplicated Profile permissions while allowing professional mode rules."""

    role_section = _section(body, "Role")
    execution = _section(body, "Execution Checklist")
    findings: list[str] = []
    if (
        GENERIC_PERMISSION_PATTERNS["analysis-profile-permission"].search(role_section)
        and GENERIC_PERMISSION_PATTERNS["analysis-profile-permission"].search(execution)
    ):
        findings.append("analysis-profile-permission")
    task_role = "do not claim final independent review" in role_section.casefold()
    task_close = "post-edit validation" in execution.casefold()
    if task_role and task_close:
        findings.append("task-profile-close")
    review_role = GENERIC_PERMISSION_PATTERNS["review-profile-permission"].search(
        role_section
    )
    review_execution_hits = {
        match.group(0).casefold()
        for match in GENERIC_PERMISSION_PATTERNS["review-profile-permission"].finditer(
            execution
        )
    }
    if review_role and len(review_execution_hits) >= 2:
        findings.append("review-profile-permission")
    return findings


def _validate_role_contract(
    entry: dict[str, object],
    metadata: dict[str, object],
    body: str,
    context: str,
    errors: list[str],
) -> None:
    roles = tuple(str(role) for role in entry.get("role_support") or [])
    role_set = set(roles)
    description = str(metadata.get("description") or "")
    folded_description = description.casefold()
    role_section = _section(body, "Role")
    when_to_use = _section(body, "When To Use")
    do_not_use = _section(body, "Do Not Use")
    required_inputs = _section(body, "Required Inputs")
    execution = _section(body, "Execution Checklist")
    output = _section(body, "Output Contract")

    if GENERIC_TRIGGER_PHRASE in folded_description:
        errors.append(f"{context}: description uses the obsolete all-role trigger phrase")
    for role in STATIC_ROLES:
        token = f"`{role}`"
        if role in role_set:
            if token not in description:
                errors.append(f"{context}: description must name supported profile {role}")
            if token not in role_section:
                errors.append(f"{context}: Role must name supported profile {role}")
        else:
            if token in description:
                errors.append(f"{context}: description names unsupported profile {role}")
            if token in role_section:
                errors.append(f"{context}: Role names unsupported profile {role}")

    for signal in entry.get("trigger_signals") or []:
        if str(signal).casefold() not in when_to_use.casefold():
            errors.append(f"{context}: When To Use must include registry trigger {signal!r}")
    for signal in entry.get("anti_trigger_signals") or []:
        if str(signal).casefold() not in do_not_use.casefold():
            errors.append(f"{context}: Do Not Use must include registry anti-trigger {signal!r}")

    if len(roles) > 1:
        for value in entry.get("required_inputs") or []:
            if str(value).casefold() not in required_inputs.casefold():
                errors.append(
                    f"{context}: Required Inputs must include common registry input {value!r}"
                )
        by_role = entry.get("required_inputs_by_role")
        if not isinstance(by_role, dict):
            errors.append(f"{context}: multi-role Skill requires required_inputs_by_role")
            by_role = {}
        for role in roles:
            mode = MODE_NAMES.get(role)
            if mode is None:
                continue
            role_marker = f"**{mode} mode (`{role}`):**"
            mode_marker = f"**{mode} mode:**"
            if role_marker not in role_section:
                errors.append(f"{context}: Role must define {role_marker}")
            if mode_marker not in execution:
                errors.append(f"{context}: Execution Checklist must define {mode_marker}")
            if role_marker not in output:
                errors.append(f"{context}: Output Contract must define {role_marker}")
            required_marker = f"**{mode} mode (`{role}`):**"
            if required_marker not in required_inputs:
                errors.append(
                    f"{context}: Required Inputs must define {required_marker}"
                )
            required_line = _role_labeled_line(required_inputs, mode, role) or ""
            for value in by_role.get(role, []):
                if str(value).casefold() not in required_line.casefold():
                    errors.append(
                        f"{context}: Required Inputs {role} block must include registry input {value!r}"
                    )
            outputs_by_role = entry.get("output_contract_by_role")
            if not isinstance(outputs_by_role, dict):
                errors.append(f"{context}: multi-role Skill requires output_contract_by_role")
                outputs_by_role = {}
            output_line = _role_labeled_line(output, mode, role) or ""
            for value in outputs_by_role.get(role, []):
                if str(value).casefold() not in output_line.casefold():
                    errors.append(
                        f"{context}: Output Contract {role} block must include registry output {value!r}"
                    )
        for value in entry.get("output_contract") or []:
            if str(value).casefold() not in output.casefold():
                errors.append(
                    f"{context}: Output Contract must include common registry union {value!r}"
                )
    for finding in _generic_permission_scaffold_findings(body):
        errors.append(
            f"{context}: generic Profile permission scaffold {finding!r} belongs in "
            "the Agent Profile, not the Professional Skill"
        )


def main() -> int:
    errors: list[str] = []
    try:
        data = load_yaml_file(REGISTRY)
    except ValidationProblem as exc:
        errors.append(str(exc))
        return fail_many("validate-skills", errors)
    entries = data.get("professional_skills") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        errors.append("professional-skills.yaml:professional_skills must be a list")
        return fail_many("validate-skills", errors)
    if len(entries) != EXPECTED_PROFESSIONAL_SKILL_COUNT:
        errors.append(f"expected {EXPECTED_PROFESSIONAL_SKILL_COUNT} Professional Skills, found {len(entries)}")
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        path_value = entry.get("path")
        if not isinstance(name, str) or not isinstance(path_value, str):
            continue
        skill_file = ROOT / path_value / "SKILL.md"
        context = str(skill_file.relative_to(ROOT))
        if not skill_file.is_file():
            errors.append(f"{context}: missing")
            continue
        try:
            metadata, _raw, body = parse_frontmatter(skill_file)
        except ValidationProblem as exc:
            errors.append(str(exc).replace(str(ROOT) + "/", ""))
            continue
        if set(metadata) != {"name", "description"}:
            errors.append(f"{context}: frontmatter must contain only name and description")
        if metadata.get("name") != name or skill_file.parent.name != name:
            errors.append(f"{context}: name must match registry and directory")
        if name in seen:
            errors.append(f"{context}: duplicate name")
        seen.add(name)
        description = metadata.get("description")
        if not isinstance(description, str) or len(description.strip()) < 60:
            errors.append(f"{context}: description must contain concrete trigger guidance")
        elif isinstance(description, str):
            validate_ai_readability(
                description,
                f"{context}#description",
                errors,
                check_bullets=False,
            )
        _validate_role_contract(entry, metadata, body, context, errors)
        validate_required_sections(body, REQUIRED_SECTIONS, context, errors, require_order=True)
        for line_number, _level, title in empty_markdown_headings(body):
            errors.append(f"{context}: empty heading '{title}' at line {line_number}")
        validate_ai_markdown_format(body, context, errors)
        line_count = len(body.splitlines())
        if line_count > MAX_ROOT_SKILL_LINES:
            errors.append(
                f"{context}: root Skill is too long for AI execution "
                f"({line_count} lines > {MAX_ROOT_SKILL_LINES})"
            )
        folded = body.casefold()
        for term in FORBIDDEN:
            if term in folded:
                errors.append(f"{context}: contains obsolete mechanism {term!r}")
        for reference in reference_paths(
            entry.get("reference_index"), f"{context}.reference_index", owner=name
        ):
            if not (skill_file.parent / str(reference)).is_file():
                errors.append(f"{context}: missing targeted reference {reference}")
        if entry.get("task_routable") is False and "not a task owner" not in folded and "do not select this skill" not in folded:
            errors.append(f"{context}: compatibility Skill must reject task routing")
    actual = {path.name for path in SKILLS_ROOT.iterdir() if path.is_dir() and not path.name.startswith(".")}
    if actual != seen:
        errors.append(f"Professional Skill directory/registry mismatch: {sorted(actual ^ seen)}")
    errors.extend(validate_capability_coverage_matrix())
    if errors:
        return fail_many("validate-skills", errors)
    print(f"validate-skills: validated {len(seen)} AI-executable Professional Skill(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
