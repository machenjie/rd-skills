#!/usr/bin/env python3
"""Validate the thin hookless engineering control Skill."""

from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath

from validation_utils import (
    CONTROL_SKILL_CONTRACT_MODEL,
    EVIDENCE_LEDGER_MODEL,
    REFERENCE_CONTRACT_MODEL,
    ValidationProblem,
    count_nonblank_lines,
    count_o200k_base_tokens,
    execution_level_runtime_reference_errors,
    extract_section_body,
    fail_many,
    heading_entries,
    parse_frontmatter,
    read_text_preserve_newlines,
    shared_normalized_non_heading_lines,
    strip_frontmatter_body_targeted_reference_projection,
    validate_ai_markdown_format,
    validate_ai_readability,
)


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / CONTROL_SKILL_CONTRACT_MODEL["path"]
PROMPT = ROOT / CONTROL_SKILL_CONTRACT_MODEL["prompt_path"]
HOST_ENFORCEMENT_SOURCE = ROOT / "src/agent-profiles/host-enforcement.json"
CONTROL_SKILL_MAX_NONBLANK_LINES = 35
CONTROL_SKILL_MAX_O200K_BASE_TOKENS = 500
DECISION_RULES_MAX_NONBLANK_LINES = 6
DECISION_RULES_MAX_O200K_BASE_TOKENS = 90
MAX_COPIED_LINES = 0
REFERENCES = tuple(
    PurePosixPath(path).name
    for path in REFERENCE_CONTRACT_MODEL["control_required_by"]
)
try:
    _HOST_ENFORCEMENT = json.loads(HOST_ENFORCEMENT_SOURCE.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError):
    _HOST_ENFORCEMENT = {}
FORBIDDEN_HOST_MODE_BRANCH_LITERALS = (
    "native-enforced",
    "sandbox-enforced",
    "prompt-enforced",
    "unsupported",
)
LEGACY_HOST_MODE_FIELDS = ("diff_inspection", "validation_execution")
FORBIDDEN_OBSOLETE_MECHANISMS = (
    "task context compiler",
    "runtime dispatch bridge",
    "dispatch cursor",
    "private evidence ledger",
    "runtime evidence ledger",
    "hidden evidence ledger",
    "runtime identity",
    "runtime digest",
    "finding id",
    "phase fsm",
    ".changeforge-packs",
)
COPIED_LINE_ALLOWANCES = (
    "[professional-skill-router.md](references/professional-skill-router.md)",
    "[implementation-handoff-template.md](references/implementation-handoff-template.md)",
)
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)\s]+)\)")
MARKDOWN_FORMATTING_RE = re.compile(r"[`*_~]")
LIST_RULE_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\S", re.MULTILINE)


def _fold(text: str) -> str:
    return " ".join(text.casefold().split())


def _validate_heading_structure(body: str, errors: list[str]) -> None:
    context = str(SKILL.relative_to(ROOT))
    entries = heading_entries(body)
    actual_headings = [(level, title) for _line, level, title in entries]
    expected_headings = [
        (level, title)
        for level, title in CONTROL_SKILL_CONTRACT_MODEL["ordered_headings"]
    ]
    if actual_headings != expected_headings:
        errors.append(
            f"{context}: headings must exactly match the authoritative order "
            f"{expected_headings!r}; found {actual_headings!r}"
        )


def _validate_concepts(body: str, errors: list[str]) -> None:
    for concept in CONTROL_SKILL_CONTRACT_MODEL["concepts"]:
        label = concept["id"]
        section = concept["section"]
        terms = concept["required_terms"]
        surface = extract_section_body(body, section)
        if surface is None:
            errors.append(f"cannot validate {label}: missing section '{section}'")
            continue
        folded = _fold(surface)
        missing = [term for term in terms if term.casefold() not in folded]
        if missing:
            errors.append(
                f"missing {label} concept terms: "
                + ", ".join(repr(term) for term in missing)
            )
    forbidden_rules = {
        rule["id"]: rule for rule in EVIDENCE_LEDGER_MODEL["forbidden_storage"]
    }
    for section, rule_ids in CONTROL_SKILL_CONTRACT_MODEL[
        "forbidden_storage_projection_ids_by_section"
    ].items():
        surface = extract_section_body(body, section)
        folded = _fold(surface or "")
        for rule_id in rule_ids:
            missing = [
                term
                for term in forbidden_rules[rule_id]["projection_terms"]
                if term.casefold() not in folded
            ]
            if missing:
                errors.append(
                    f"control-skill:{section} is missing forbidden storage rule "
                    f"{rule_id!r}: "
                    + ", ".join(repr(term) for term in missing)
                )


def _validate_references(body: str, errors: list[str]) -> None:
    section = extract_section_body(body, "Targeted References")
    if section is None:
        return
    links = MARKDOWN_LINK_RE.findall(section)
    all_body_links = MARKDOWN_LINK_RE.findall(body)
    expected = [f"references/{name}" for name in REFERENCES]
    actual = set(links)
    if links != expected:
        missing = sorted(set(expected) - actual)
        unexpected = sorted(actual - set(expected))
        details: list[str] = []
        if missing:
            details.append(f"missing {', '.join(missing)}")
        if unexpected:
            details.append(f"unexpected {', '.join(unexpected)}")
        if len(links) != len(actual):
            details.append("duplicate links")
        if not details:
            details.append("wrong order")
        errors.append(
            "Targeted References must link exactly the runtime contract, router, and six templates"
            + (f": {'; '.join(details)}" if details else "")
        )
    if links != all_body_links:
        errors.append("all control Skill links must appear in Targeted References")
    reference_root = SKILL.parent / "references"
    for name in REFERENCES:
        if not (reference_root / name).is_file():
            errors.append(f"missing control reference {name}")
    runtime_reference = reference_root / "execution-level-contract.md"
    if runtime_reference.is_file():
        errors.extend(
            execution_level_runtime_reference_errors(
                runtime_reference.read_text(encoding="utf-8")
            )
        )


def _validate_thin_decision_rules(body: str, errors: list[str]) -> None:
    section = extract_section_body(body, "Decision Rules")
    if section is None:
        return
    nonblank_lines = count_nonblank_lines(section)
    token_count = count_o200k_base_tokens(section)
    paragraphs = [item for item in re.split(r"\n\s*\n", section.strip()) if item.strip()]
    if len(paragraphs) != 1 or LIST_RULE_RE.search(section):
        errors.append(
            "Decision Rules must remain one concise prose delegation; "
            "control rule lists belong only in the authoritative prompt"
        )
    if nonblank_lines > DECISION_RULES_MAX_NONBLANK_LINES:
        errors.append(
            f"Decision Rules has {nonblank_lines} nonblank lines; "
            f"maximum is {DECISION_RULES_MAX_NONBLANK_LINES}"
        )
    if token_count > DECISION_RULES_MAX_O200K_BASE_TOKENS:
        errors.append(
            f"Decision Rules has {token_count} o200k_base tokens; "
            f"maximum is {DECISION_RULES_MAX_O200K_BASE_TOKENS}"
        )


def _validate_context_budget(
    body: str,
    raw_source: str,
    errors: list[str],
) -> tuple[int, int]:
    governed_body = strip_frontmatter_body_targeted_reference_projection(
        body,
        raw_source,
    )
    line_count = count_nonblank_lines(governed_body)
    token_count = count_o200k_base_tokens(governed_body)
    if line_count > CONTROL_SKILL_MAX_NONBLANK_LINES:
        errors.append(
            f"control Skill body has {line_count} nonblank lines; "
            f"maximum is {CONTROL_SKILL_MAX_NONBLANK_LINES}"
        )
    if token_count > CONTROL_SKILL_MAX_O200K_BASE_TOKENS:
        errors.append(
            f"control Skill body has {token_count} o200k_base tokens; "
            f"maximum is {CONTROL_SKILL_MAX_O200K_BASE_TOKENS}"
        )
    return line_count, token_count


def _validate_no_prompt_copy(body: str, errors: list[str]) -> None:
    if not PROMPT.is_file():
        errors.append("missing src/control-prompts/main-control-agent.md")
        return
    prompt = PROMPT.read_text(encoding="utf-8")
    copied = shared_normalized_non_heading_lines(
        prompt,
        body,
        minimum_length=50,
        allowed_lines=COPIED_LINE_ALLOWANCES,
    )
    if len(copied) > MAX_COPIED_LINES:
        preview = " | ".join(copied[:3])
        errors.append(
            f"control Skill copies {len(copied)} long prompt lines; "
            f"maximum is {MAX_COPIED_LINES}: {preview}"
        )


def _validate_no_host_mode_branches(body: str, errors: list[str]) -> None:
    normalized = MARKDOWN_FORMATTING_RE.sub("", body.casefold())
    for literal in FORBIDDEN_HOST_MODE_BRANCH_LITERALS:
        pattern = rf"(?<![a-z0-9_-]){re.escape(literal)}(?![a-z0-9_-])"
        if re.search(pattern, normalized):
            errors.append(
                f"control Skill must defer host branch value {literal!r} "
                "to the host projection adapter"
            )


def _validate_host_enforcement_status_owner(errors: list[str]) -> None:
    if (
        _HOST_ENFORCEMENT.get("schema_version") != 5
        or tuple(_HOST_ENFORCEMENT.get("status_values") or ())
        != FORBIDDEN_HOST_MODE_BRANCH_LITERALS
    ):
        errors.append(
            "host-enforcement schema v5 status_values must match the non-empty "
            "control Skill host-branch exclusion enum"
        )


def main() -> int:
    errors: list[str] = []
    _validate_host_enforcement_status_owner(errors)
    if not SKILL.is_file():
        errors.append("missing engineering-control-plane/SKILL.md")
        return fail_many("validate-control-skills", errors)
    raw_source = read_text_preserve_newlines(SKILL)
    try:
        metadata, _raw, body = parse_frontmatter(SKILL)
    except ValidationProblem as exc:
        errors.append(str(exc).replace(str(ROOT) + "/", ""))
        return fail_many("validate-control-skills", errors)

    if set(metadata) != {"name", "description"}:
        errors.append("control Skill frontmatter must contain only name and description")
    if metadata.get("name") != "engineering-control-plane":
        errors.append("control Skill name must be engineering-control-plane")
    if not isinstance(metadata.get("description"), str) or not metadata["description"].strip():
        errors.append("control Skill description must be non-empty text")
    else:
        validate_ai_readability(
            metadata["description"],
            "src/control-skills/engineering-control-plane/SKILL.md#description",
            errors,
            check_bullets=False,
        )

    _validate_heading_structure(body, errors)
    validate_ai_markdown_format(
        body,
        "src/control-skills/engineering-control-plane/SKILL.md",
        errors,
    )
    _validate_concepts(body, errors)
    _validate_thin_decision_rules(body, errors)
    _validate_no_host_mode_branches(body, errors)
    folded = _fold(body)
    for field in LEGACY_HOST_MODE_FIELDS:
        if field in folded:
            errors.append(f"control Skill contains legacy host field {field!r}")
    for term in FORBIDDEN_OBSOLETE_MECHANISMS:
        if term in folded:
            errors.append(f"control Skill exposes obsolete mechanism {term!r}")
    _validate_references(body, errors)
    line_count, token_count = _validate_context_budget(
        body,
        raw_source,
        errors,
    )
    _validate_no_prompt_copy(body, errors)

    if errors:
        return fail_many("validate-control-skills", errors)
    print(
        "validate-control-skills: thin delegation, headings, references, boundaries, copy, "
        f"and body budgets are valid ({line_count} nonblank lines, "
        f"{token_count} o200k_base tokens)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
