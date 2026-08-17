#!/usr/bin/env python3
"""Validate the authoritative main-control-agent prompt contract."""

from __future__ import annotations

import re
from pathlib import Path

from validation_utils import (
    _completion_rule_text,
    CORE_CONTRACTS,
    COMPLETION_STATE_MODEL,
    EVIDENCE_LEDGER_MODEL,
    PROMPT_CONTRACT_MODEL,
    REFERENCE_CONTRACT_MODEL,
    REVIEW_DISCIPLINE_MODEL,
    TASK_CONTRACT_MODEL,
    ValidationProblem,
    completion_fail_closed_projection_terms,
    completion_fail_closed_surface_errors,
    completion_transition_projection_terms,
    completion_transition_surface_errors,
    count_nonblank_lines,
    count_o200k_base_tokens,
    execution_level_runtime_reference_errors,
    extract_section_body,
    fail_many,
    heading_entries,
    parse_frontmatter,
    prompt_projection_block,
    prompt_projection_errors,
    shared_normalized_non_heading_lines,
    validate_ai_readability,
)


ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT / PROMPT_CONTRACT_MODEL["path"]
CONTROL_SKILL = (
    ROOT / "src" / "control-skills" / "engineering-control-plane" / "SKILL.md"
)
REFERENCE_ROOT = CONTROL_SKILL.parent / "references"
PROMPT_MAX_NONBLANK_LINES = 120
PROMPT_MAX_O200K_BASE_TOKENS = 1700
MAX_COPIED_LINES = 2
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
MODE_BRANCH_RE = re.compile(r"^- `([^`]+)`:\s*(.*)$")
FENCED_MARKDOWN_RE = re.compile(
    r"^```markdown\s*$\n(?P<body>.*?)^```\s*$",
    re.MULTILINE | re.DOTALL,
)
PROMPT_TEMPLATE_BINDINGS = (
    ("direct-task-template.md", ("main-control-agent",)),
    ("implementation-handoff-template.md", ("task-agent",)),
)
ANALYZED_WORK_PROMPT_TERMS = {
    "Analyzed Work": (
        "current Engineering Brief: sole analysis authority",
        "First Executable Slice: Task Contract v2",
        "dispatch verbatim",
        "never reinterpret",
        "Specialists: Brief only",
        "DAGs/handoffs cannot redefine it",
        "blocked -> main-control-agent -> analysis-agent -> updated Engineering Brief",
        "redispatch affected tasks",
        "Direct Task/non-implementation paths remain unchanged",
    ),
    "Scheduling and Context": (
        "requested task > DAG > blockers > adjacent",
        "adjacent never preempts task/DAG",
    ),
}


def _fold(text: str) -> str:
    return " ".join(text.casefold().split())


def _validate_heading_structure(text: str, errors: list[str]) -> None:
    context = str(PROMPT.relative_to(ROOT))
    entries = heading_entries(text)
    actual_headings = [(level, title) for _line, level, title in entries]
    expected_headings = [
        (level, title) for level, title in PROMPT_CONTRACT_MODEL["ordered_headings"]
    ]
    if actual_headings != expected_headings:
        errors.append(
            f"{context}: headings must exactly match the authoritative order "
            f"{expected_headings!r}; found {actual_headings!r}"
        )
    expected_h1_titles = [
        title
        for level, title in PROMPT_CONTRACT_MODEL["ordered_headings"]
        if level == 1
    ]
    h1_titles = [title for _line, level, title in entries if level == 1]
    if h1_titles != expected_h1_titles:
        errors.append(
            f"{context}: H1 headings must exactly match {expected_h1_titles!r}"
        )
    expected_first = (
        f"# {expected_h1_titles[0]}" if len(expected_h1_titles) == 1 else ""
    )
    first_nonblank = next((line.strip() for line in text.splitlines() if line.strip()), "")
    if first_nonblank != expected_first:
        errors.append(
            f"{context}: must start with {expected_first!r} and no frontmatter"
        )


def _validate_template_bindings(
    reference_root: Path,
    errors: list[str],
) -> None:
    """Bind Prompt template references to their authoritative physical schemas."""

    registered_paths = REFERENCE_CONTRACT_MODEL["control_required_by"]
    for name, expected_roles in PROMPT_TEMPLATE_BINDINGS:
        relative = f"references/{name}"
        if relative not in registered_paths:
            errors.append(
                f"{name}: missing from the authoritative control Reference contract"
            )
        elif registered_paths[relative] != list(expected_roles):
            errors.append(
                f"{name}: required_by roles drifted from the Prompt template binding"
            )
        schema = TASK_CONTRACT_MODEL["template_schemas"].get(name)
        if not isinstance(schema, dict):
            errors.append(f"{name}: missing authoritative template schema")
            continue
        path = reference_root / name
        if not path.is_file():
            errors.append(f"missing Prompt-authoritative template {name}")
            continue
        text = path.read_text(encoding="utf-8")
        container = schema.get("container")
        if container == "document":
            surface = text
        elif container == "fenced-markdown":
            matches = list(FENCED_MARKDOWN_RE.finditer(text))
            if len(matches) != 1:
                errors.append(
                    f"{name}: must contain exactly one fenced Markdown contract"
                )
                continue
            surface = matches[0].group("body")
        else:
            errors.append(f"{name}: unsupported authoritative template container")
            continue

        expected = [tuple(item) for item in schema.get("headings", [])]
        allowed = [expected]
        optional_insertions = schema.get("optional_heading_insertions")
        if isinstance(optional_insertions, dict):
            with_optional = list(expected)
            for field, insertion in optional_insertions.items():
                anchor = insertion.get("after") if isinstance(insertion, dict) else None
                positions = [
                    index
                    for index, (_level, title) in enumerate(with_optional)
                    if title == anchor
                ]
                if len(positions) != 1:
                    errors.append(
                        f"{name}: optional field {field!r} has no unique schema anchor"
                    )
                    continue
                with_optional.insert(positions[0] + 1, (2, field))
            allowed.append(with_optional)
        actual = [
            (level, title)
            for _line_number, level, title in heading_entries(surface)
        ]
        if actual not in allowed:
            errors.append(
                f"{name}: physical template fields drifted from the authoritative schema"
            )

        if name == "direct-task-template.md":
            expected_fields = TASK_CONTRACT_MODEL["required_for_direct_task"]
            if schema.get("task_fields") != expected_fields:
                errors.append(
                    "direct-task-template.md: schema fields drifted from Task Contract v2"
                )
        if name == "implementation-handoff-template.md":
            ledger_header = (
                "| " + " | ".join(EVIDENCE_LEDGER_MODEL["fields"]) + " |"
            )
            if surface.count(ledger_header) != 1:
                errors.append(
                    "implementation-handoff-template.md: Evidence Ledger fields "
                    "drifted from the authoritative schema"
                )


def _validate_concepts(text: str, errors: list[str]) -> None:
    for concept in PROMPT_CONTRACT_MODEL["concepts"]:
        label = concept["id"]
        section = concept["section"]
        terms = concept["required_terms"]
        surface = text if section is None else extract_section_body(text, section)
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

    direct = extract_section_body(text, PROMPT_CONTRACT_MODEL["task_contract_section"]) or ""
    for field in TASK_CONTRACT_MODEL["optional_for_direct_task"]:
        insertion = TASK_CONTRACT_MODEL["template_schemas"]["direct-task-template.md"][
            "optional_heading_insertions"
        ][field]
        expected = f"optional {field} after {insertion['after']}"
        if expected.casefold() not in direct.casefold():
            errors.append(
                f"Direct Task Routing must project optional {field!r} at its canonical position"
            )
    initial_status = TASK_CONTRACT_MODEL["assignment_initial_status"]
    initial_marker = f"`Status: {initial_status}`"
    scheduling = extract_section_body(text, "Scheduling and Context") or ""
    if direct.count(initial_marker) != 1:
        errors.append(
            "Direct Task Routing must declare the assignment initial Status exactly once"
        )
    if scheduling.count(initial_marker) != 1:
        errors.append(
            "Scheduling and Context must declare the DAG assignment initial Status exactly once"
        )
    if text.count(initial_marker) != 2:
        errors.append(
            "assignment initial Status must appear only in Direct and DAG routing"
        )
    closure = extract_section_body(text, PROMPT_CONTRACT_MODEL["completion_section"]) or ""
    for status in COMPLETION_STATE_MODEL["statuses"]:
        if status not in closure:
            errors.append(f"Closure is missing core completion state {status!r}")
    agent_projection = COMPLETION_STATE_MODEL["agent_projection"]
    if agent_projection["prompt_section"] != PROMPT_CONTRACT_MODEL["completion_section"]:
        errors.append("completion projection section disagrees with prompt contract")
    folded_closure = _fold(closure)
    for rule in agent_projection["rules"]:
        if rule["id"] == "same-task-transitions":
            projection_terms = completion_transition_projection_terms(
                COMPLETION_STATE_MODEL
            )
        elif rule["id"] == "fail-closed-outcomes":
            projection_terms = completion_fail_closed_projection_terms(
                COMPLETION_STATE_MODEL
            )
        else:
            projection_terms = rule["projection_terms"]
        missing = [
            term
            for term in projection_terms
            if term.casefold() not in folded_closure
        ]
        if missing:
            errors.append(
                f"Closure is missing completion projection {rule['id']!r}: "
                + ", ".join(repr(term) for term in missing)
            )
    for rule in COMPLETION_STATE_MODEL["completed_rules"]:
        rendered = _completion_rule_text(rule)
        if rendered.casefold() not in folded_closure:
            errors.append(
                f"Closure is missing completed rule {rule['id']!r}: {rendered!r}"
            )
    errors.extend(
        completion_transition_surface_errors(
            closure,
            COMPLETION_STATE_MODEL,
            "Closure",
        )
    )
    errors.extend(
        completion_fail_closed_surface_errors(
            closure,
            COMPLETION_STATE_MODEL,
            "Closure",
        )
    )
    for rule in EVIDENCE_LEDGER_MODEL["freshness_rules"]:
        for target in rule["projection_targets"]:
            if not target.startswith("prompt:"):
                continue
            section = target.removeprefix("prompt:")
            surface = extract_section_body(text, section)
            folded_surface = _fold(surface or "")
            missing = [
                term
                for term in rule["projection_terms"]
                if term.casefold() not in folded_surface
            ]
            if missing:
                errors.append(
                    f"{target} is missing Evidence Ledger freshness rule "
                    f"{rule['id']!r}: "
                    + ", ".join(repr(term) for term in missing)
                )
    for rule in EVIDENCE_LEDGER_MODEL["forbidden_storage"]:
        for target in rule["projection_targets"]:
            if not target.startswith("prompt:"):
                continue
            section = target.removeprefix("prompt:")
            surface = extract_section_body(text, section)
            folded_surface = _fold(surface or "")
            missing = [
                term
                for term in rule["projection_terms"]
                if term.casefold() not in folded_surface
            ]
            if missing:
                errors.append(
                    f"{target} is missing forbidden storage rule {rule['id']!r}: "
                    + ", ".join(repr(term) for term in missing)
                )
    completion_proof = EVIDENCE_LEDGER_MODEL["completion_proof"]["implementation"]
    for projection in completion_proof["projections"]:
        proof_target = projection["target"]
        if not proof_target.startswith("prompt:"):
            continue
        proof_section = proof_target.removeprefix("prompt:")
        proof_surface = extract_section_body(text, proof_section) or ""
        missing = [
            term
            for term in projection["terms"]
            if term.casefold() not in _fold(proof_surface)
        ]
        if missing:
            errors.append(
                f"{proof_target} is missing independent review evidence proof: "
                + ", ".join(repr(term) for term in missing)
            )


def _validate_analyzed_work_authority(text: str, errors: list[str]) -> None:
    authority = TASK_CONTRACT_MODEL["analyzed_work_authority"]
    if authority["operational_authority"] != "current-engineering-brief":
        errors.append(
            "Core analyzed-work authority must remain the current Engineering Brief"
        )
    for section, terms in ANALYZED_WORK_PROMPT_TERMS.items():
        surface = extract_section_body(text, section)
        if surface is None:
            errors.append(
                f"cannot validate analyzed-work authority: missing section {section!r}"
            )
            continue
        folded = _fold(surface)
        for term in terms:
            if term.casefold() not in folded:
                errors.append(
                    f"{section}: missing analyzed-work authority term {term!r}"
                )


def _validate_capability_branches(text: str, errors: list[str]) -> None:
    section = extract_section_body(text, PROMPT_CONTRACT_MODEL["capability_section"])
    if section is None:
        errors.append("cannot validate capability branches: missing Direct Task Routing")
        return

    regions: dict[str, str] = {}
    branch_contracts = REVIEW_DISCIPLINE_MODEL["generic_capability_contract"][
        "prompt_branches"
    ]
    for branch_contract in branch_contracts:
        field = branch_contract["field"]
        next_field = branch_contract["next_field"]
        marker = f"`{field}`"
        if section.count(marker) != 1:
            errors.append(
                f"Direct Task Routing must name capability field {field!r} exactly once"
            )
            continue
        start = section.index(marker) + len(marker)
        if next_field is None:
            regions[field] = section[start:]
            continue
        next_marker = f"`{next_field}`"
        if section.count(next_marker) != 1:
            continue
        end = section.index(next_marker)
        if end <= start:
            errors.append(f"capability field {field!r} must precede {next_field!r}")
            continue
        regions[field] = section[start:end]

    for branch_contract in branch_contracts:
        field = branch_contract["field"]
        expected_branches = branch_contract["branches"]
        region = regions.get(field)
        if region is None:
            continue
        order: list[str] = []
        bodies: dict[str, str] = {}
        current: str | None = None
        for line in region.splitlines():
            match = MODE_BRANCH_RE.match(line)
            if match:
                current = match.group(1)
                order.append(current)
                bodies[current] = match.group(2)
            elif current is not None and line.startswith("  "):
                bodies[current] += " " + line.strip()
            else:
                current = None

        expected_order = [branch["value"] for branch in expected_branches]
        if order != expected_order:
            errors.append(
                f"{field} branches must be exactly {', '.join(expected_order)} in order; "
                f"found {', '.join(order) or 'none'}"
            )
        for branch in expected_branches:
            mode = branch["value"]
            terms = branch["required_terms"]
            folded = _fold(bodies.get(mode, ""))
            missing = [term for term in terms if term.casefold() not in folded]
            if missing:
                errors.append(
                    f"{field}={mode} branch missing action terms: "
                    + ", ".join(repr(term) for term in missing)
                )


def _validate_context_budget(text: str, errors: list[str]) -> tuple[int, int]:
    line_count = count_nonblank_lines(text)
    token_count = count_o200k_base_tokens(text)
    if line_count > PROMPT_MAX_NONBLANK_LINES:
        errors.append(
            f"control prompt has {line_count} nonblank lines; "
            f"maximum is {PROMPT_MAX_NONBLANK_LINES}"
        )
    if token_count > PROMPT_MAX_O200K_BASE_TOKENS:
        errors.append(
            f"control prompt has {token_count} o200k_base tokens; "
            f"maximum is {PROMPT_MAX_O200K_BASE_TOKENS}"
        )
    return line_count, token_count


def _validate_no_prompt_copy(text: str, errors: list[str]) -> None:
    if not CONTROL_SKILL.is_file():
        errors.append("missing engineering-control-plane/SKILL.md for copy comparison")
        return
    try:
        _metadata, _raw, body = parse_frontmatter(CONTROL_SKILL)
    except ValidationProblem as exc:
        errors.append(str(exc).replace(str(ROOT) + "/", ""))
        return
    copied = shared_normalized_non_heading_lines(
        text,
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


def main() -> int:
    errors: list[str] = []
    if not PROMPT.is_file():
        errors.append("missing src/control-prompts/main-control-agent.md")
        return fail_many("validate-control-plane-prompt", errors)

    raw = PROMPT.read_bytes()
    text = raw.decode("utf-8")
    errors.extend(
        f"{PROMPT.relative_to(ROOT)}: {error}"
        for error in prompt_projection_errors(
            text,
            CORE_CONTRACTS,
            document_bytes=raw,
        )
    )
    validate_ai_readability(
        text,
        str(PROMPT.relative_to(ROOT)),
        errors,
    )
    _validate_heading_structure(text, errors)
    _validate_template_bindings(REFERENCE_ROOT, errors)
    runtime_reference = REFERENCE_ROOT / "execution-level-contract.md"
    if not runtime_reference.is_file():
        errors.append("missing Prompt execution-level runtime Reference")
    else:
        errors.extend(
            execution_level_runtime_reference_errors(
                runtime_reference.read_text(encoding="utf-8")
            )
        )
    _validate_concepts(text, errors)
    _validate_analyzed_work_authority(text, errors)
    _validate_capability_branches(text, errors)
    folded = _fold(text)
    for field in LEGACY_HOST_MODE_FIELDS:
        if field in folded:
            errors.append(f"control prompt contains legacy host field {field!r}")
    for term in FORBIDDEN_OBSOLETE_MECHANISMS:
        if term in folded:
            errors.append(f"control prompt contains obsolete mechanism {term!r}")
    line_count, token_count = _validate_context_budget(text, errors)
    _validate_no_prompt_copy(text, errors)

    if errors:
        return fail_many("validate-control-plane-prompt", errors)
    print(
        "validate-control-plane-prompt: heading, invariant, copy, and context "
        f"budgets are valid ({line_count} nonblank lines, {token_count} o200k_base tokens)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
