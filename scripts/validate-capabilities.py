#!/usr/bin/env python3
"""Validate focused Foundation Layer 3 Skills."""

from __future__ import annotations

from pathlib import Path

from capability_coverage import fixture_ids, validate_capability_coverage
from validation_utils import (
    EXPECTED_FOUNDATION_CAPABILITY_COUNT,
    ValidationProblem,
    ai_markdown_list_sentence_counts,
    ai_readability_findings,
    empty_markdown_headings,
    fail_many,
    foundation_decision_card,
    heading_entries,
    load_yaml_file,
    parse_frontmatter,
    reference_paths,
    validate_ai_readability,
    validate_ai_markdown_format,
    validate_required_sections,
)


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / "src" / "foundation" / "capabilities"
REGISTRY = ROOT / "src" / "registry" / "foundation-skills.yaml"
CAPABILITY_MATRIX = ROOT / "evals" / "capability-coverage" / "matrix.yaml"
REQUIRED_SECTIONS = (
    "Registry Trigger",
    "Skill Role",
    "High-Value Rules",
    "Anti-Patterns",
    "Targeted References",
)
OPTIONAL_SECTIONS = (
    "Inputs",
    "Execution Checklist",
    "Stop Conditions",
    "Output Contract",
    "Standards",
)
SECTION_ORDER = (
    "Registry Trigger",
    "Skill Role",
    "Inputs",
    "High-Value Rules",
    "Anti-Patterns",
    "Execution Checklist",
    "Stop Conditions",
    "Output Contract",
    "Standards",
    "Targeted References",
)
FORBIDDEN_GENERIC_SCAFFOLD_LINES = frozenset(
    {
        "- current task contract",
        "- selected primary Professional Skill",
        "- task-local trigger evidence",
        "- current task contract; selected primary Professional Skill; task-local trigger evidence",
        "1. Confirm the concrete trigger and the primary Professional Skill.",
        "2. Inspect only the current source, tests, contracts, and targeted references needed for this decision.",
        "3. Apply the narrow rules without expanding task scope or taking over ownership.",
        "4. Return the decision, evidence, proof limits, escalation, and residual risk.",
        "- State source evidence, what the decision proves, what remains unverified, and the next owner.",
        "- Return to the primary Professional Skill after this decision; do not load adjacent Layer 3 Skills speculatively.",
        "- Read [checklist.md](references/checklist.md) only when its subject changes the current decision.",
        "- Read [evidence-patterns.md](references/evidence-patterns.md) only when its subject changes the current decision.",
        "Support `analysis-agent`, `task-agent`, and `review-agent` as a focused Layer 3",
        "Support an `analysis-agent`, `task-agent`, or `review-agent` as a focused Layer 3",
    }
)
FORBIDDEN = (
    "task context compiler", "runtime dispatch bridge", "private evidence ledger",
    "runtime evidence ledger", "hidden evidence ledger",
    "runtime identity", "runtime digest", "hidden pack", ".changeforge-packs",
    "phase artifact", "process phase ledger", "finding id", "pretooluse", "posttooluse",
)


def validate_capability_coverage_matrix(
    matrix_path: Path = CAPABILITY_MATRIX,
    *,
    root: Path = ROOT,
    foundation_registry: object | None = None,
) -> list[str]:
    """Validate matrix Layer 3 IDs and Professional ownership."""

    registry_root = root / "src" / "registry"
    professional_path = registry_root / "professional-skills.yaml"
    foundation_path = registry_root / "foundation-skills.yaml"
    domain_path = registry_root / "domain-skills.yaml"
    professional_registry = (
        load_yaml_file(professional_path) if professional_path.is_file() else None
    )
    if foundation_registry is None and foundation_path.is_file():
        foundation_registry = load_yaml_file(foundation_path)
    domain_registry = (
        load_yaml_file(domain_path) if domain_path.is_file() else None
    )
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
            foundation_registry=foundation_registry,
            domain_registry=domain_registry,
            evidence_ids=evidence_catalog,
        ),
    ]


def _section(body: str, heading: str) -> str:
    marker = f"## {heading}"
    start = body.find(marker)
    if start < 0:
        return ""
    content_start = start + len(marker)
    end = body.find("\n## ", content_start)
    return body[content_start:] if end < 0 else body[content_start:end]


def _output_contract_items(section: str) -> tuple[list[str], list[str]]:
    """Return normalized top-level bullets from a root Output Contract."""

    items: list[str] = []
    errors: list[str] = []
    current: list[str] | None = None
    for raw_line in section.splitlines():
        if raw_line.startswith("- "):
            if current is not None:
                items.append(" ".join(current))
            value = " ".join(raw_line[2:].split())
            current = [value] if value else []
            if not value:
                errors.append("contains an empty bullet")
            continue
        if not raw_line.strip():
            continue
        if current is not None and raw_line[:1].isspace():
            current.append(" ".join(raw_line.split()))
            continue
        errors.append(f"contains non-bullet content {raw_line.strip()!r}")
    if current is not None:
        items.append(" ".join(current))
    if not items:
        errors.append("must contain at least one top-level bullet")
    return items, errors


def _registry_trigger_errors(section: str) -> list[str]:
    """Return errors for the canonical Foundation trigger boundaries."""

    labels = {
        line.strip().strip("*_").strip().casefold()
        for line in section.splitlines()
    }
    errors: list[str] = []
    if "use when" not in labels:
        errors.append("Registry Trigger must contain a 'Use when' boundary")
    if "do not use when" not in labels:
        errors.append("Registry Trigger must contain a 'Do not use when' boundary")
    return errors


def _decision_card_errors(body: str) -> list[str]:
    result = foundation_decision_card(body)
    findings = set(result["findings"])
    metrics = result["metrics"]
    errors: list[str] = []
    if "trigger-boundaries-not-front-loaded" in findings:
        errors.append(
            "Registry Trigger Use/Do not use boundaries must precede High-Value Rules"
        )
    if "high-value-rules-not-early" in findings:
        errors.append(
            "High-Value Rules must begin within the first 60 lines"
        )
    if "decision-rule-count-outside-3-8" in findings:
        errors.append("High-Value Rules must contain 3-8 decision rules")
    if "decision-density-low" in findings:
        errors.append(
            "High-Value Rules decision density must equal 1.0; found "
            f"{float(metrics['decision_density']):.3f}"
        )
    if "non-list-content" in findings:
        errors.append(
            "High-Value Rules must contain only list items and "
            "content-indented continuations"
        )
    if "stop-conditions-missing-or-late" in findings:
        errors.append(
            "Stop Conditions must be present after High-Value Rules and before "
            "applicable Output Contract and Targeted References"
        )
    return errors


def main() -> int:
    errors: list[str] = []
    try:
        data = load_yaml_file(REGISTRY)
    except ValidationProblem as exc:
        errors.append(str(exc))
        return fail_many("validate-capabilities", errors)
    entries = data.get("foundation_skills") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        errors.append("foundation-skills.yaml:foundation_skills must be a list")
        return fail_many("validate-capabilities", errors)
    if len(entries) != EXPECTED_FOUNDATION_CAPABILITY_COUNT:
        errors.append(f"expected {EXPECTED_FOUNDATION_CAPABILITY_COUNT} Foundation Skills, found {len(entries)}")
    registered: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        name, path_value = entry.get("name"), entry.get("path")
        if not isinstance(name, str) or not isinstance(path_value, str):
            continue
        registered.add(name)
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
        description = metadata.get("description")
        if not isinstance(description, str) or len(description.strip()) < 60:
            errors.append(f"{context}: description must contain trigger and boundary guidance")
        elif isinstance(description, str):
            validate_ai_readability(
                description,
                f"{context}#description",
                errors,
                check_bullets=False,
            )
        validate_required_sections(
            body,
            REQUIRED_SECTIONS,
            context,
            errors,
            require_order=True,
        )
        for line_number, _level, title in empty_markdown_headings(body):
            errors.append(f"{context}: empty heading '{title}' at line {line_number}")
        validate_ai_markdown_format(
            body,
            context,
            errors,
            check_bullets=False,
        )
        for error in _decision_card_errors(body):
            errors.append(f"{context}: {error}")
        for rule in ai_markdown_list_sentence_counts(
            _section(body, "High-Value Rules")
        ):
            sentence_count = int(rule["sentences"])
            if sentence_count <= 2:
                continue
            errors.append(
                f"{context}: Foundation High-Value Rule exceeds the two-sentence "
                f"limit; found {sentence_count} sentences"
            )
        for finding in ai_readability_findings(body, context):
            if finding.get("band") != "tighten":
                continue
            errors.append(
                f"{context}:{finding['line']}: Foundation root sentence requires "
                f"tightening; {finding['words']} words exceeds the 32-word root limit"
            )
        h2_titles = [
            title for _line, level, title in heading_entries(body) if level == 2
        ]
        all_heading_titles = [title for _line, _level, title in heading_entries(body)]
        for title in REQUIRED_SECTIONS:
            if title in all_heading_titles and title not in h2_titles:
                errors.append(
                    f"{context}: required Foundation section '{title}' must be level 2"
                )
        allowed_sections = set(REQUIRED_SECTIONS) | set(OPTIONAL_SECTIONS)
        unexpected = [title for title in h2_titles if title not in allowed_sections]
        if unexpected:
            errors.append(
                f"{context}: unsupported Foundation section(s): {', '.join(unexpected)}"
            )
        positions = [SECTION_ORDER.index(title) for title in h2_titles if title in allowed_sections]
        if positions != sorted(positions):
            errors.append(f"{context}: Foundation sections are out of order")
        duplicate_optional = sorted(
            title for title in OPTIONAL_SECTIONS if h2_titles.count(title) > 1
        )
        if duplicate_optional:
            errors.append(
                f"{context}: duplicate optional Foundation section(s): "
                + ", ".join(duplicate_optional)
            )
        for line in body.splitlines():
            if line.strip() in FORBIDDEN_GENERIC_SCAFFOLD_LINES:
                errors.append(
                    f"{context}: contains forbidden generic scaffold line {line.strip()!r}"
                )
        if len(body.splitlines()) > 120:
            errors.append(f"{context}: root Layer 3 Skill exceeds 120 lines")
        folded = body.casefold()
        for term in FORBIDDEN:
            if term in folded:
                errors.append(f"{context}: contains obsolete mechanism {term!r}")
        trigger_section = _section(body, "Registry Trigger")
        for error in _registry_trigger_errors(trigger_section):
            errors.append(f"{context}: {error}")
        output_section = _section(body, "Output Contract")
        if output_section:
            root_outputs, output_errors = _output_contract_items(output_section)
            for error in output_errors:
                errors.append(f"{context}: Output Contract {error}")
            registry_outputs = entry.get("output_contract")
            normalized_registry_outputs = (
                [" ".join(value.split()) for value in registry_outputs]
                if isinstance(registry_outputs, list)
                and all(isinstance(value, str) for value in registry_outputs)
                else []
            )
            if len(root_outputs) != len(set(root_outputs)):
                errors.append(f"{context}: Output Contract contains duplicate bullets")
            if len(normalized_registry_outputs) != len(set(normalized_registry_outputs)):
                errors.append(f"{context}: registry output_contract contains duplicate values")
            if set(root_outputs) != set(normalized_registry_outputs):
                missing = sorted(set(root_outputs) - set(normalized_registry_outputs))
                extra = sorted(set(normalized_registry_outputs) - set(root_outputs))
                errors.append(
                    f"{context}: Output Contract bullet-set must exactly match registry "
                    f"output_contract; missing={missing!r}; extra={extra!r}"
                )
        reference_section = _section(body, "Targeted References")
        for reference in reference_paths(
            entry.get("reference_index"), f"{context}.reference_index", owner=name
        ):
            if not (skill_file.parent / str(reference)).is_file():
                errors.append(f"{context}: missing targeted reference {reference}")
            if str(reference) not in reference_section:
                errors.append(f"{context}: Targeted References must link {reference}")
    actual = {
        path.name for path in SKILLS_ROOT.iterdir()
        if path.is_dir() and not path.name.startswith((".", "_"))
    }
    if actual != registered:
        errors.append(f"Foundation Skill directory/registry mismatch: {sorted(actual ^ registered)}")
    errors.extend(validate_capability_coverage_matrix())
    if errors:
        return fail_many("validate-capabilities", errors)
    print(f"validate-capabilities: validated {len(registered)} focused Foundation Skill(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
