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
    load_yaml_file,
    professional_review_risk_matrix_block,
    public_execution_template_spans,
    validate_core_contracts,
)


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_ROOT = ROOT / "src" / "control-skills" / "engineering-control-plane" / "references"
PROFESSIONAL_ROOT = ROOT / "src" / "professional-skills"
PROFESSIONAL_REGISTRY = ROOT / "src" / "registry" / "professional-skills.yaml"
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
_RAW_FINDING_FIELD_LABEL_OVERRIDES = {
    "finding_identity": "Finding Identity",
    "task_id": "Task ID",
    "review_round_id": "Review Round ID",
    "relation": "Finding Relation",
    "protected_decision_boundary": "Protected Decision Boundary",
    "required_covering_rereview": "Required covering re-review",
    "proof_limit": "Proof Limit",
}
_PUBLIC_EXECUTION_TEMPLATE_TERMS = (
    "Core public `execution-level/v2`",
    "[execution-level-contract.md](execution-level-contract.md)",
    "completed/read only",
    "active or resumed work, edit, validation, or review requires reissue",
)


def _raw_finding_field_label(field: str) -> str:
    return _RAW_FINDING_FIELD_LABEL_OVERRIDES.get(
        field,
        field.replace("_", " ").capitalize(),
    )


def _validate_review_finding_projection(text: str, errors: list[str]) -> None:
    start_marker = (
        "For each implementation or repair finding, state fields in this order:\n\n"
    )
    end_marker = "\n\nRe-review findings require both classification fields"
    _prefix, separator, remainder = text.partition(start_marker)
    if not separator:
        errors.append(
            "review-handoff-template.md: missing implementation finding field projection"
        )
        return
    field_block, separator, _suffix = remainder.partition(end_marker)
    if not separator:
        errors.append(
            "review-handoff-template.md: implementation finding field projection "
            "has no canonical boundary"
        )
        return
    labels = [
        match.group(1)
        for line in field_block.splitlines()
        if (match := _LABELED_FIELD_RE.fullmatch(line)) is not None
    ]
    compiler = CORE_CONTRACTS["review_discipline_contract"][
        "review_boundary_contract"
    ]["finding_compiler"]
    for field in compiler["raw_required_fields"]:
        label = _raw_finding_field_label(field)
        count = labels.count(label)
        if count != 1:
            errors.append(
                "review-handoff-template.md: implementation finding projection must "
                f"contain Core field {label!r} exactly once, found {count}"
            )
_PUBLIC_EXECUTION_PREAMBLE_TEMPLATES = (
    "direct-task-template.md",
    "engineering-brief-template.md",
    "task-dag-template.md",
    "implementation-handoff-template.md",
)
_PUBLIC_EXECUTION_PREAMBLE_PREFIXES = {
    "direct-task-template.md": (
        "# Direct Task Contract v2 Direct Task requires explicit behavior, local scope, "
        "owner, observable acceptance, non-production verification, placement, and "
        "rollback; work is low-risk, reversible, and clear of excluded boundaries or "
        "unresolved material impact. Otherwise route to Analyzed Work. Direct Task is "
        "outside the Analyzed Work authority path. It keeps this template's existing "
        "field authority and does not create or derive authority from an Engineering "
        "Brief. An unknown owner/module/system/verification boundary routes to Analyzed "
        "Work. Inside an already-known stable owner/test/consumer boundary, bounded "
        "confirmation may inspect only the named checks below. Use `not applicable` for "
        "a field that has no Direct Task value."
    ),
    "engineering-brief-template.md": (
        "# Engineering Brief For Analyzed Work, the current Engineering Brief is the "
        "only operational analysis authority. Its authoritative sections are Problem "
        "and Desired Behavior; Acceptance and Non-goals; Ownership and Invariants; "
        "Placement and Reuse; Contract / Data / Failure Impact; Validation Strategy; "
        "Risks and Rollback; First Executable Slice; Task Dependencies; Integration "
        "Boundary; Review Boundary; and Evidence Gaps and Proof Limits. User requests, "
        "change sources, source and tests, external evidence, and Specialist results "
        "are analysis input only. Write source-proven placement directly into the "
        "Brief. Use a corresponding Specialist for a real structural choice, then "
        "incorporate its result into the current Brief before it can affect "
        "implementation. A Specialist never becomes a parallel authority. Task DAGs, "
        "Task Contracts, Implementation Handoffs, and Review Handoffs are derived "
        "artifacts and must not redefine Acceptance, Non-goals, Owner, Invariants, "
        "Placement, contract semantics, Rollback, or the First Executable Slice. The "
        "First Executable Slice is a complete Task Contract v2, not an informal "
        "checklist. Main dispatches it verbatim and never regenerates or reinterprets "
        "it; the DAG planner never reselects it. The Analysis assignment and "
        "Engineering Brief itself have no Execution Level, apply no default L3, "
        "write no historical effective level, and do not participate in historical "
        "maxima. Compute the executable Task Level only after this Brief has "
        "identified the First Executable Slice, using the analysis handoff as "
        "evidence. The Level fields below belong only to that executable Slice. "
        "Return the First Executable Slice "
        "when current evidence proves it safe, verifiable, reversible, and independent "
        "of remaining unknowns. If the Brief is insufficient, a downstream artifact "
        "conflicts with it, or a protected decision must change, mark the task blocked "
        "and return through Main to analysis for an updated Brief and redispatch of "
        "affected tasks. Complete one initial Analysis by closing observable Acceptance, "
        "Owner/Placement/Invariant, Acceptance-proving Validation, executable task "
        "dependencies, professional Skill boundaries, minimum sufficient Review "
        "Boundaries, and critical gaps blocking the First Executable Slice. Task "
        "completion or switch, ordinary implementation discovery, and an unreached "
        "Review Boundary do not re-trigger Analysis. The first Analysis event is always "
        "`initial`. Desired behavior and observable Acceptance are target authority; "
        "observed behavior is failure evidence only and cannot be copied into Acceptance. "
        "A Delta is legal only after this complete initial Brief is accepted and current "
        "evidence names the protected decision it invalidates. Before dispatch, close "
        "every authoritative Brief section and every non-blocked First Executable Slice "
        "field, then preserve the Slice's Professional Skill and Layer 3 selections "
        "verbatim. When this Brief must select Layer 3 "
        "for an analyzed downstream Task or Review, load exactly one current-Professional "
        "projection from `engineering-control-plane/references/selectors/"
        "<professional-skill>.json`. Load it only after the Professional and downstream "
        "profile are fixed, and do not load any sibling projection, index, or catalog. "
        "If the exact authorized Layer 3 set is already fixed, skip the selector file and "
        "retain that authorized set. Write the resulting exact set into the Brief; "
        "downstream Task and Review agents do not reroute. Main continues to own Direct "
        "and initial-Analysis selection. Delta Analysis is permitted only "
        "when evidence invalidates Acceptance/Non-goals, Owner/Placement/Invariant, "
        "contract/data semantics, dependency/rollback, material risk, or a scope blocker. "
        "Reuse Core `delta_analysis`; do not change its invalidation triggers or "
        "transitive scope. After Delta Analysis, the complete updated Engineering Brief "
        "remains the only operational analysis authority. Then emit only this decision "
        "projection: ```text Delta Impact: invalidated=[...]; affected={ brief:[...], "
        "tasks:[...], dependencies:[...], skills:[...], reviews:[...] }; "
        "unlisted=preserved ``` Each list is the exact proved affected set; `[]` means "
        "proved no impact, while unknown requires a Proof Limit rather than `[]`. Preserve Skill assignments unless professional "
        "domain, work type, or a material-risk trigger changes. If transitive impact is "
        "not closed, record a Proof Limit and return blocked. Main consumes Delta Impact "
        "without reinterpreting affected scope. Use full re-analysis only when foundational "
        "goals or system assumptions are invalidated. Delta Impact never replaces, "
        "summarizes, or weakens the Brief."
    ),
    "task-dag-template.md": (
        "# Task DAG Contract v2 Use only for at least two real tasks with an evidenced "
        "dependency, parallel benefit, cross-owner boundary, integration need, or "
        "migration/release order. For Analyzed Work, this DAG is a derived projection "
        "of the current Engineering Brief. It may split Brief work, project Task "
        "Contracts, dependencies, parallel safety, critical path, and integration, "
        "merge, and conflict ownership. It must not select or replace the First "
        "Executable Slice or modify Acceptance, Non-goals, Owner, Invariants, "
        "Placement, contract semantics, or Rollback. The First Executable Slice below "
        "names the Brief-selected Task ID; its matching task node is a verbatim "
        "projection, and Main dispatches the Brief slice itself. If the Brief is "
        "insufficient or any projection conflicts with it, mark the DAG blocked and "
        "return to analysis through Main for an updated Brief and redispatch. Each Task "
        "is one complete semantic change with one Primary Professional Skill. Keep "
        "co-effective changes for one Acceptance together when they naturally validate "
        "together. Split materially different professional domains into separate Tasks. "
        "File, function, code layer, test, or edit step differences do not define Tasks. "
        "Define minimum sufficient Review Boundaries. Related work is combined by "
        "default. Concrete risk justifies an intermediate boundary. Combined review "
        "preserves Primary Skills, required Review Skills, Specialists, and "
        "professional-risk obligations. Review-side Layer 3 is selected independently "
        "from review risk and is not copied from Task implementation Layer 3."
    ),
    "implementation-handoff-template.md": (
        "# Implementation Handoff Return this visible contract after the last material "
        "edit and its targeted validation. It records evidence, not implementer "
        "reasoning or self-review. The normal sequence is one Task's final edit, fresh "
        "validation, exact change capture, this same Implementation Handoff, and Main's "
        "readiness gate. Do not use a second Task or normal recovery/export Task to "
        "complete that sequence. For Analyzed Work, this handoff is a derived "
        "projection of the current Engineering Brief and its verbatim-dispatched First "
        "Executable Slice. Result and evidence may report execution but must not "
        "redefine Acceptance, Non-goals, Owner, Invariants, Placement, contract "
        "semantics, Rollback, or the Slice. If the assignment conflicts with the "
        "current Brief or needs one of those decisions to change, mark it blocked and "
        "return to analysis through Main. This cross-Agent artifact is an Execution "
        "Delta, not a second Task Contract. Transmit only Task ID and Status; Changed "
        "Files; the actual diff or accessible diff reference; Commands; a structured "
        "Validation Result; Freshness; relevant current Evidence; Review Input Ready; "
        "Unverified Scope; and Residual Risk. Resolve Goal, Acceptance, Owner, Non-goals, and other "
        "existing Authority at its source instead of copying them here. Keep raw "
        "command logs as JIT-readable artifacts and include them only when a downstream "
        "consumer explicitly requires them."
    ),
}
_PUBLIC_EXECUTION_PREAMBLE = (
    "The public Execution Level lines use Core public `execution-level/v2`. The integrity "
    "fallback for missing, malformed, or duplicate public execution-level data is "
    "defined in [execution-level-contract.md](execution-level-contract.md). "
    "Legacy v1 is completed/read only; active or resumed work, edit, "
    "validation, or review requires reissue."
)

ANALYZED_WORK_TEMPLATE_TERMS = {
    "engineering-brief-template.md": (
        "current Engineering Brief is the only operational analysis authority",
        "Specialist results are analysis input only",
        "First Executable Slice is a complete Task Contract v2",
        "Main dispatches it verbatim",
        "DAG planner never reselects it",
        "return through Main to analysis",
        "one initial Analysis",
        "Delta Impact never replaces, summarizes, or weakens the Brief",
        "Preserve Skill assignments",
    ),
    "direct-task-template.md": (
        "outside the Analyzed Work authority path",
        "does not create or derive authority from an Engineering Brief",
    ),
    "task-dag-template.md": (
        "derived projection of the current Engineering Brief",
        "must not select or replace the First Executable Slice",
        "matching task node is a verbatim projection",
        "return to analysis through Main",
        "one complete semantic change with one Primary Professional Skill",
        "minimum sufficient Review Boundaries",
    ),
    "implementation-handoff-template.md": (
        "derived projection of the current Engineering Brief",
        "must not redefine Acceptance, Non-goals, Owner, Invariants, Placement",
        "return to analysis through Main",
    ),
    "review-handoff-template.md": (
        "derived projection of the current Engineering Brief",
        "findings cannot redefine",
        "return to analysis through Main",
    ),
}

PROFESSIONAL_AUTHORITY_TERMS = {
    "engineering-change-analysis/SKILL.md": (
        "This root owns mode choice",
        "the mode contract owns output",
        "Keep Professional, Layer3, and mode fixed; never reroute",
        "read-only scope",
    ),
    "engineering-change-analysis/references/implementation-preparation.md": (
        "current Engineering Brief is the only operational analysis authority",
        "Specialist analysis are inputs",
        "complete Task Contract v2",
        "Task DAGs, Task Contracts, Implementation Handoffs, and Review Handoffs are derived artifacts",
        "planner does not reselect the First Executable Slice",
        "updated Brief and redispatch",
    ),
    "engineering-change-analysis/examples/example-output.md": (
        "## First Executable Slice",
        "Task ID: example-api-validation-001",
        "## Evidence Gaps and Proof Limits",
    ),
    "task-dag-planner/SKILL.md": (
        "Brief retains sole operational analysis authority",
        "preserve its First Executable Slice verbatim",
        "Never select the First Executable Slice",
        "Never replace the First Executable Slice",
        "Never reinterpret the First Executable Slice",
        "derived artifacts, not a parallel analysis authority",
        "updated Brief and redispatch of affected tasks",
    ),
}

FORBIDDEN_PROFESSIONAL_AUTHORITY_TERMS = (
    "Non-Authoritative Slice Hypothesis",
    "non-authoritative and non-dispatchable",
    "independently selects the First Executable Slice",
    "Select the First Executable Slice independently",
    "sole final authoritative Task DAG",
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
                f"{context}: missing public execution-level/v2 rule {term!r}"
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


def _normalized(text: str) -> str:
    return " ".join(text.casefold().split())


def _validate_analyzed_work_authority_templates(
    texts: dict[str, str], errors: list[str]
) -> None:
    authority = TASK_CONTRACT_MODEL["analyzed_work_authority"]
    for name, terms in ANALYZED_WORK_TEMPLATE_TERMS.items():
        normalized = _normalized(texts.get(name, ""))
        for term in terms:
            if _normalized(term) not in normalized:
                errors.append(
                    f"{name}: missing analyzed-work authority projection {term!r}"
                )

    brief = texts.get("engineering-brief-template.md", "")
    fence_start = brief.find("```markdown")
    brief_preamble = _normalized(brief if fence_start < 0 else brief[:fence_start])
    for section in authority["authoritative_sections"]:
        if _normalized(section) not in brief_preamble:
            errors.append(
                "engineering-brief-template.md: authoritative section list is "
                f"missing {section!r}"
            )
    for decision in authority["protected_decisions"]:
        if _normalized(decision) not in brief_preamble:
            errors.append(
                "engineering-brief-template.md: protected decision list is "
                f"missing {decision!r}"
            )

def _validate_professional_authority_projections(errors: list[str]) -> None:
    for relative, terms in PROFESSIONAL_AUTHORITY_TERMS.items():
        path = PROFESSIONAL_ROOT / relative
        if not path.is_file():
            errors.append(f"missing analyzed-work projection source {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        normalized = _normalized(text)
        for term in terms:
            if _normalized(term) not in normalized:
                errors.append(
                    f"{relative}: missing analyzed-work authority term {term!r}"
                )
        for term in FORBIDDEN_PROFESSIONAL_AUTHORITY_TERMS:
            if _normalized(term) in normalized:
                errors.append(
                    f"{relative}: contains conflicting analyzed-work authority "
                    f"term {term!r}"
                )

    try:
        registry = load_yaml_file(PROFESSIONAL_REGISTRY)
    except OSError as exc:
        errors.append(f"professional-skills.yaml: {exc}")
        return
    entries = registry.get("professional_skills") if isinstance(registry, dict) else None
    if not isinstance(entries, list):
        errors.append("professional-skills.yaml: professional_skills must be a list")
        return
    by_name = {
        entry.get("name"): entry
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("name"), str)
    }
    analysis_entry = by_name.get("engineering-change-analysis")
    planner_entry = by_name.get("task-dag-planner")
    if not isinstance(analysis_entry, dict) or analysis_entry.get("role_support") != [
        "analysis-agent"
    ]:
        errors.append(
            "professional-skills.yaml: engineering-change-analysis must remain "
            "analysis-agent-only"
        )
    if not isinstance(planner_entry, dict):
        errors.append("professional-skills.yaml: missing task-dag-planner")
    else:
        required_inputs = planner_entry.get("required_inputs")
        if not isinstance(required_inputs, list) or "accepted Engineering Brief" not in required_inputs:
            errors.append(
                "professional-skills.yaml: task-dag-planner must require the "
                "accepted Engineering Brief"
            )
        output_contract = planner_entry.get("output_contract")
        if not isinstance(output_contract, list) or any(
            "authoritative" in str(item).casefold() for item in output_contract
        ):
            errors.append(
                "professional-skills.yaml: task-dag-planner output must remain a "
                "derived projection, not an authority"
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
            present = (
                re.search(r"\bfinding id\b", folded) is not None
                if term == "finding id"
                else term in folded
            )
            if present:
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

    _validate_analyzed_work_authority_templates(texts, errors)
    _validate_professional_authority_projections(errors)

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
    _validate_review_finding_projection(review_handoff, errors)

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
