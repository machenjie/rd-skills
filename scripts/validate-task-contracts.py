#!/usr/bin/env python3
"""Validate exact visible Task Contract v2, handoff, and ledger templates."""

from __future__ import annotations

import re
from pathlib import Path

from validation_utils import (
    COMPLETION_STATE_MODEL,
    CORE_CONTRACTS,
    EVIDENCE_LEDGER_MODEL,
    EXECUTION_LEVEL_MODEL,
    TASK_CONTRACT_MODEL,
    conditional_test_evidence_projection_text,
    execution_level_runtime_reference_errors,
    execution_level_router_errors,
    extract_section_body,
    fail_many,
    heading_entries,
    professional_review_risk_matrix_block,
    public_execution_template_spans,
    validate_core_contracts,
)


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_ROOT = ROOT / "src" / "control-skills" / "engineering-control-plane" / "references"
FORBIDDEN = (
    "runtime id",
    "runtime identity",
    "finding id",
    "dispatch cursor",
    "state ledger",
    "runtime projection",
    "capsule origin",
    "```json",
)
DIRECT_TASK_FORBIDDEN_DISCOVERY = (
    "owner / verification discovery allowed",
    "bounded ownership discovery",
    "may discover owner",
    "may discover ownership",
    "may discover verification",
)
FORBIDDEN_DIGEST_CLAIM_RE = re.compile(
    r"\b(?:self[- ]reported|self[- ]asserted|unbound|unverified)\s+"
    r"(?:identity\s+)?digest\b",
    re.IGNORECASE,
)
_FENCED_MARKDOWN_RE = re.compile(
    r"^```markdown\s*$\n(?P<body>.*?)^```\s*$",
    re.MULTILINE | re.DOTALL,
)
_LABELED_FIELD_RE = re.compile(r"^([A-Za-z][A-Za-z0-9 /-]*):(?:\s.*)?$")
_PUBLIC_EXECUTION_TEMPLATE_TERMS = (
    "Core public `execution-level/v1`",
    "[execution-level-contract.md](execution-level-contract.md)",
    "completed/read only",
    "active or resumed work, edit, validation, or review requires reissue",
)
_PUBLIC_EXECUTION_PREAMBLE_TEMPLATES = (
    "direct-task-template.md",
    "engineering-brief-template.md",
    "task-dag-template.md",
    "implementation-handoff-template.md",
    "review-handoff-template.md",
)
_PUBLIC_EXECUTION_PREAMBLE_PREFIXES = {
    "direct-task-template.md": (
        "# Direct Task Contract v2 Direct Task requires explicit behavior, local scope, "
        "owner, observable acceptance, non-production verification, placement, and "
        "rollback; work is low-risk, reversible, and clear of excluded boundaries or "
        "unresolved material impact. Otherwise route to Analyzed Work. Inspect within "
        "named owner, test, and consumer boundaries. If ownership or verification needs "
        "discovery, stop and route to Analyzed Work. Use `not applicable` for a field "
        "that has no Direct Task value."
    ),
    "engineering-brief-template.md": (
        "# Engineering Brief Return the First Executable Slice when current source "
        "evidence proves it safe, verifiable, reversible, and independent of the "
        "remaining unknowns. The slice is a complete Task Contract v2, not an informal "
        "checklist."
    ),
    "task-dag-template.md": (
        "# Task DAG Contract v2 Use only for at least two real tasks with an evidenced "
        "dependency, parallel benefit, cross-owner boundary, integration need, or "
        "migration/release order."
    ),
    "implementation-handoff-template.md": (
        "# Implementation Handoff Return this visible contract after the last material "
        "edit and its targeted validation. It records evidence, not implementer "
        "reasoning or self-review."
    ),
    "review-handoff-template.md": (
        "# Review Handoff The review-agent receives one bounded target and does not "
        "edit. Implementation review requires observable acceptance, the latest actual "
        "diff, the declared changed-path set, current validation results, and the "
        "Evidence Requirements."
    ),
}
_PUBLIC_EXECUTION_PREAMBLE = (
    "The public Execution Level lines use Core public `execution-level/v1`. The integrity "
    "fallback for missing, malformed, or duplicate public execution-level data is "
    "defined in [execution-level-contract.md](execution-level-contract.md). "
    "Legacy without v1 is completed/read only; active or resumed work, edit, "
    "validation, or review requires reissue."
)


def _public_execution_snapshot() -> dict[str, object]:
    return EXECUTION_LEVEL_MODEL["projection"]["public_task_extension"]


def _contract_surface(
    text: str,
    *,
    container: str,
    context: str,
    errors: list[str],
) -> str:
    if container == "document":
        return text
    matches = list(_FENCED_MARKDOWN_RE.finditer(text))
    if len(matches) != 1:
        errors.append(f"{context}: must contain exactly one fenced Markdown contract")
        return ""
    return matches[0].group("body")


def _ordered_labeled_fields(body: str) -> list[str]:
    fields: list[str] = []
    for line in body.splitlines():
        match = _LABELED_FIELD_RE.fullmatch(line.strip())
        if match:
            fields.append(match.group(1))
    return fields


def _status_literal() -> str:
    return " / ".join(COMPLETION_STATE_MODEL["statuses"])


def _assignment_status_literal() -> str:
    return TASK_CONTRACT_MODEL["assignment_initial_status"]


def _validate_status_heading(
    surface: str,
    *,
    context: str,
    expected: str,
    errors: list[str],
) -> None:
    body = extract_section_body(surface, "Status")
    if body != expected:
        errors.append(
            f"{context}: Status heading must contain exactly {expected!r}"
        )


def _validate_labeled_section(
    surface: str,
    section: str,
    expected: list[str],
    *,
    context: str,
    errors: list[str],
) -> None:
    body = extract_section_body(surface, section)
    if body is None:
        errors.append(f"{context}: missing labeled section {section!r}")
        return
    actual = _ordered_labeled_fields(body)
    if actual != expected:
        errors.append(
            f"{context}: {section} fields must be exactly ordered as {expected}, "
            f"found {actual}"
        )
    if "Status" in expected:
        status_lines = [
            line.strip()
            for line in body.splitlines()
            if line.strip().startswith("Status:")
        ]
        expected_line = f"Status: {_assignment_status_literal()}"
        if status_lines != [expected_line]:
            errors.append(
                f"{context}: {section} must contain exactly {expected_line!r}"
            )


def _validate_public_execution_rules(
    text: str,
    *,
    context: str,
    errors: list[str],
) -> None:
    normalized = " ".join(text.split())
    for term in _PUBLIC_EXECUTION_TEMPLATE_TERMS:
        if term not in normalized:
            errors.append(
                f"{context}: missing public execution-level/v1 rule {term!r}"
            )


def _validate_public_execution_template(
    text: str,
    *,
    surface: str,
    errors: list[str],
) -> None:
    _spans, block_errors = public_execution_template_spans(
        text,
        CORE_CONTRACTS,
        surface,
    )
    errors.extend(block_errors)


def _validate_template(
    name: str,
    text: str,
    schema: dict[str, object],
    errors: list[str],
) -> None:
    surface = _contract_surface(
        text,
        container=str(schema["container"]),
        context=name,
        errors=errors,
    )
    if not surface:
        return
    expected_headings = [tuple(item) for item in schema["headings"]]
    if name == "direct-task-template.md":
        expected_document_h1 = [(1, expected_headings[0][1])]
        actual_document_headings = [
            (level, title) for _line, level, title in heading_entries(text)
        ]
        if actual_document_headings != expected_document_h1:
            errors.append(
                f"{name}: document headings must be exactly "
                f"{expected_document_h1}, found {actual_document_headings}"
            )
    actual_headings = [
        (level, title) for _line_number, level, title in heading_entries(surface)
    ]
    allowed_heading_sequences = [expected_headings]
    optional_insertions = schema.get("optional_heading_insertions")
    if isinstance(optional_insertions, dict):
        with_optional = list(expected_headings)
        for field, insertion in optional_insertions.items():
            after = insertion["after"]
            positions = [
                index
                for index, (_level, title) in enumerate(with_optional)
                if title == after
            ]
            if len(positions) != 1:
                errors.append(
                    f"{name}: optional {field!r} insertion anchor {after!r} is ambiguous"
                )
                continue
            with_optional.insert(positions[0] + 1, (2, field))
        allowed_heading_sequences.append(with_optional)
    if actual_headings not in allowed_heading_sequences:
        errors.append(
            f"{name}: headings must exactly match the authoritative template schema; "
            f"expected one of {allowed_heading_sequences}, found {actual_headings}"
        )
    h1_titles = [title for level, title in actual_headings if level == 1]
    expected_h1_titles = [title for level, title in expected_headings if level == 1]
    if h1_titles != expected_h1_titles or len(h1_titles) != len(set(h1_titles)):
        errors.append(f"{name}: H1 headings must match the authoritative schema uniquely")
    if name == "direct-task-template.md":
        direct_titles = [title for _level, title in actual_headings]
        core_titles = [
            title for title in direct_titles if title in TASK_CONTRACT_MODEL["fields"]
        ]
        if len(core_titles) != len(set(core_titles)):
            errors.append(f"{name}: core headings, including Owner, must not repeat")
        expected_core = [
            field for field in TASK_CONTRACT_MODEL["fields"] if field in core_titles
        ]
        if core_titles != expected_core:
            errors.append(f"{name}: core headings must preserve canonical field order")
        for optional in TASK_CONTRACT_MODEL["optional_for_direct_task"]:
            if optional in direct_titles:
                optional_body = extract_section_body(surface, optional) or ""
                if not optional_body.strip():
                    errors.append(
                        f"{name}: optional {optional!r} must contain a meaningful dependency"
                    )

    labeled_sections = schema.get("labeled_sections")
    if isinstance(labeled_sections, dict):
        for section, expected in labeled_sections.items():
            _validate_labeled_section(
                surface,
                section,
                expected,
                context=name,
                errors=errors,
            )

    if name in {
        "direct-task-template.md",
        "engineering-brief-template.md",
        "task-dag-template.md",
        "implementation-handoff-template.md",
        "review-handoff-template.md",
    }:
        _validate_public_execution_rules(text, context=name, errors=errors)
        _validate_public_execution_template(text, surface=name, errors=errors)

    if name in {
        "direct-task-template.md",
        "engineering-brief-template.md",
        "task-dag-template.md",
        "implementation-handoff-template.md",
        "review-handoff-template.md",
    }:
        expected_status = (
            _assignment_status_literal()
            if name == "direct-task-template.md"
            else _status_literal()
        )
        _validate_status_heading(
            surface,
            context=name,
            expected=expected_status,
            errors=errors,
        )

    if "Evidence Ledger" in {title for _level, title in expected_headings}:
        ledger_header = "| " + " | ".join(EVIDENCE_LEDGER_MODEL["fields"]) + " |"
        if ledger_header not in surface:
            errors.append(f"{name}: Evidence Ledger fields do not match the core model")

    status_sections = schema.get("status_sections")
    if isinstance(status_sections, list):
        for status_contract in status_sections:
            parent = status_contract["parent"]
            parent_body = extract_section_body(surface, parent)
            status_body = (
                extract_section_body(parent_body, "Status")
                if parent_body is not None
                else None
            )
            actual = re.findall(
                r"`(in_progress|blocked|partial|completed)`",
                status_body or "",
            )
            if actual != status_contract["allowed"]:
                errors.append(
                    f"{name}: {parent} Status values must be exactly "
                    f"{status_contract['allowed']}, found {actual}"
                )


def validate_contracts(reference_root: Path = REFERENCE_ROOT) -> list[str]:
    """Return structural contract errors for one template directory."""

    errors = validate_core_contracts(CORE_CONTRACTS)
    template_schemas = TASK_CONTRACT_MODEL["template_schemas"]
    texts: dict[str, str] = {}
    for name, schema in template_schemas.items():
        path = reference_root / name
        if not path.is_file():
            errors.append(f"missing {name}")
            continue
        text = path.read_text(encoding="utf-8")
        texts[name] = text
        folded = text.casefold()
        for term in FORBIDDEN:
            if term in folded:
                errors.append(f"{name}: contains forbidden internal contract term {term!r}")
        if name == "direct-task-template.md":
            for term in DIRECT_TASK_FORBIDDEN_DISCOVERY:
                if term in folded:
                    errors.append(
                        f"{name}: Direct Task must not permit owner or verification "
                        f"discovery via {term!r}"
                    )
        if FORBIDDEN_DIGEST_CLAIM_RE.search(text):
            errors.append(
                f"{name}: contains a self-reported or unbound digest claim"
            )
        _validate_template(name, text, schema, errors)

    for name in _PUBLIC_EXECUTION_PREAMBLE_TEMPLATES:
        text = texts.get(name)
        if text is None:
            continue
        fence_start = text.find("```markdown")
        preamble = text if fence_start < 0 else text[:fence_start]
        expected = (
            f"{_PUBLIC_EXECUTION_PREAMBLE_PREFIXES[name]} "
            f"{_PUBLIC_EXECUTION_PREAMBLE}"
        )
        if " ".join(preamble.split()) != expected:
            errors.append(
                f"{name}: complete canonical-link-only preamble must exactly match "
                "its template introduction and execution-level-contract.md authority"
            )

    conditional_test_evidence = EVIDENCE_LEDGER_MODEL["conditional_test_evidence"]
    expected_conditional_projection = conditional_test_evidence_projection_text(
        conditional_test_evidence
    )
    conditional_targets = set(conditional_test_evidence["projection_targets"])
    legacy_conditional_claims = ("`test-approach`", "`red`", "`green`")
    for name, text in texts.items():
        normalized = " ".join(text.split())
        projection_count = normalized.count(expected_conditional_projection)
        if name in conditional_targets:
            if projection_count != 1:
                errors.append(
                    f"{name}: conditional test evidence projection must match the "
                    f"Core guidance exactly once, found {projection_count}"
                )
            legacy = [term for term in legacy_conditional_claims if term in text]
            if legacy:
                errors.append(
                    f"{name}: conditional test evidence projection contains unsupported "
                    "legacy Claim values: " + ", ".join(legacy)
                )
        elif projection_count:
            errors.append(
                f"{name}: conditional test evidence projection is not bound to this template"
            )

    professional_matrix = CORE_CONTRACTS["review_discipline_contract"][
        "professional_risk_matrix"
    ]
    expected_professional_matrix = professional_review_risk_matrix_block(
        professional_matrix
    )
    review_handoff = texts.get("review-handoff-template.md", "")
    matrix_projection_count = review_handoff.count(expected_professional_matrix)
    if matrix_projection_count != 1:
        errors.append(
            "review-handoff-template.md: professional review risk matrix projection "
            f"must match Core exactly once, found {matrix_projection_count}"
        )

    direct_schema = template_schemas["direct-task-template.md"]
    direct_titles = [item[1] for item in direct_schema["headings"]]
    for required in TASK_CONTRACT_MODEL["required_for_direct_task"]:
        if direct_titles.count(required) != 1:
            errors.append(f"direct-task-template.md: must contain one {required!r} field")
    for optional in TASK_CONTRACT_MODEL["optional_for_direct_task"]:
        if direct_titles.count(optional) > 1:
            errors.append(
                f"direct-task-template.md: optional field {optional!r} must not repeat"
            )

    brief_schema = template_schemas["engineering-brief-template.md"]
    brief_section = brief_schema["task_fields_section"]
    brief_fields = brief_schema["labeled_sections"][brief_section]
    extension_fields = _public_execution_snapshot()["ordered_labels"]
    required_dag = TASK_CONTRACT_MODEL["required_for_dag_task"]
    expected_extended = required_dag[:2] + extension_fields + required_dag[2:]
    if brief_fields[: len(expected_extended)] != expected_extended:
        errors.append("engineering-brief-template.md: executable slice is not Task Contract v2")

    dag_schema = template_schemas["task-dag-template.md"]
    for task_section in dag_schema["task_node_sections"]:
        fields = dag_schema["labeled_sections"][task_section]
        if fields[: len(expected_extended)] != expected_extended:
            errors.append(f"task-dag-template.md: {task_section} is not Task Contract v2")
    if dag_schema["labeled_sections"]["Parallel Group"] != TASK_CONTRACT_MODEL[
        "parallel_group_fields"
    ]:
        errors.append("task-dag-template.md: Parallel Group fields drifted from core model")

    dag_text = texts.get("task-dag-template.md", "")
    scheduling = TASK_CONTRACT_MODEL["scheduling_rules"]
    if scheduling["shared_or_unknown_writes"] == "serialize" and (
        "with a shared or unknown workspace, serialize writes." not in dag_text.casefold()
    ):
        errors.append(
            "task-dag-template.md: shared or unknown workspace writes must serialize"
        )
    for requirement in scheduling["parallel_write_requirements"]:
        if requirement not in dag_text.casefold():
            errors.append(
                f"task-dag-template.md: missing parallel write requirement {requirement!r}"
            )

    for rule in EVIDENCE_LEDGER_MODEL["freshness_rules"]:
        for name in rule["projection_targets"]:
            if name.startswith("prompt:"):
                continue
            folded = texts.get(name, "").casefold()
            missing = [
                term
                for term in rule["projection_terms"]
                if term.casefold() not in folded
            ]
            if missing:
                errors.append(
                    f"{name}: missing Evidence Ledger freshness rule {rule['id']!r}: "
                    + ", ".join(repr(term) for term in missing)
                )

    router = texts.get("professional-skill-router.md")
    if router is None:
        router_path = reference_root / "professional-skill-router.md"
        if not router_path.is_file():
            errors.append("missing professional-skill-router.md")
        else:
            router = router_path.read_text(encoding="utf-8")
    if router is not None:
        errors.extend(execution_level_router_errors(router))
    runtime_path = reference_root / "execution-level-contract.md"
    if not runtime_path.is_file():
        errors.append("missing execution-level-contract.md")
    else:
        errors.extend(
            execution_level_runtime_reference_errors(
                runtime_path.read_text(encoding="utf-8")
            )
        )
    for rule in EVIDENCE_LEDGER_MODEL["forbidden_storage"]:
        for name in rule["projection_targets"]:
            if name.startswith(("prompt:", "profile:", "control-skill:")):
                continue
            folded = texts.get(name, "").casefold()
            missing = [
                term
                for term in rule["projection_terms"]
                if term.casefold() not in folded
            ]
            if missing:
                errors.append(
                    f"{name}: missing forbidden storage rule {rule['id']!r}: "
                    + ", ".join(repr(term) for term in missing)
                )
    completion_proof = EVIDENCE_LEDGER_MODEL["completion_proof"]["implementation"]
    for projection in completion_proof["projections"]:
        name = projection["target"]
        if name.startswith(("prompt:", "profile:")):
            continue
        folded = texts.get(name, "").casefold()
        missing = [
            term
            for term in projection["terms"]
            if term.casefold() not in folded
        ]
        if missing:
            errors.append(
                f"{name}: missing independent review evidence proof: "
                + ", ".join(repr(term) for term in missing)
            )

    utility = texts.get("utility-capsule-template.md", "")
    for rule in TASK_CONTRACT_MODEL["utility_projection_rules"]:
        missing = [
            term
            for term in rule["projection_terms"]
            if term.casefold() not in utility.casefold()
        ]
        if missing:
            errors.append(
                f"utility-capsule-template.md: missing utility boundary {rule['id']!r}: "
                + ", ".join(repr(term) for term in missing)
            )

    schema_files = sorted(path.name for path in (ROOT / "schemas").glob("*.json"))
    if schema_files != ["marketplace-index.schema.json"]:
        errors.append(
            "schemas/: only marketplace-index.schema.json may remain, found "
            f"{schema_files}"
        )
    return errors


def main() -> int:
    errors = validate_contracts()
    if errors:
        return fail_many("validate-task-contracts", errors)
    print(
        "validate-task-contracts: exact Task Contract v2, visible Evidence Ledger, "
        "and four-state completion templates are valid."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
