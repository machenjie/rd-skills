#!/usr/bin/env python3
"""Validate AI-executable Professional Skills."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path
from types import ModuleType
from typing import Iterable

from capability_coverage import fixture_ids, validate_capability_coverage
from validation_utils import (
    EXPECTED_PROFESSIONAL_SKILL_COUNT,
    PROFESSIONAL_BUILT_KERNEL_HEADINGS,
    ValidationProblem,
    _ai_markdown_units,
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
CONTENT_AUDIT_SCRIPT = ROOT / "scripts" / "audit-skill-content.py"
SKILL_REGISTRIES = (
    (ROOT / "src" / "registry" / "control-skills.yaml", "control_skills"),
    (REGISTRY, "professional_skills"),
    (ROOT / "src" / "registry" / "foundation-skills.yaml", "foundation_skills"),
    (ROOT / "src" / "registry" / "domain-skills.yaml", "domain_skills"),
)
AUTHORING_DETAIL_SECTIONS = ("High-Value Gotchas", "Execution Checklist")
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
PROFESSIONAL_INDEPENDENCE_REPORT_FLAG = "--professional-independence-report"
_CONTENT_AUDIT_MODULE: ModuleType | None = None

_INDEPENDENCE_RAW_LINE_PATTERNS = (
    (
        "branded-control-schema",
        re.compile(
            r"(?:\brd-skills\b|\bCHANGEFORGE\b|\bchangeforge[.][a-z0-9_.-]+\b|"
            r"\bcontrol[- ]plane\s+(?:adapter|gap|handoff|projection|route|schema)\b|"
            r"\bexecution-level-(?:choice|projection)\b)",
            re.IGNORECASE,
        ),
    ),
)
_INDEPENDENCE_UNIT_PATTERNS = (
    (
        "versioned-internal-contract",
        re.compile(
            r"\b(?:Task(?:\s+DAG)?|Reference|Review)\s+Contract\s+v[0-9]+\b",
            re.IGNORECASE,
        ),
    ),
    (
        "internal-execution-path",
        re.compile(r"\bDirect Task\b"),
    ),
    (
        "internal-execution-path",
        re.compile(r"\bno-repo direct-answer\b", re.IGNORECASE),
    ),
    (
        "internal-execution-path",
        re.compile(
            r"(?:"
            r"\b(?:load\w*|preload\w*|select\w*|reference\w*)\b[^.!?;]{0,96}"
            r"\bsource-owned registry\b|"
            r"\bsource-owned registry\b[^.!?;]{0,96}"
            r"\b(?:load\w*|preload\w*|select\w*|reference\w*)\b"
            r")",
            re.IGNORECASE,
        ),
    ),
    (
        "internal-routing-object",
        re.compile(
            r"\b(?:Primary\s+Professional\s+Skill|Effective\s+Level|"
            r"Review\s+Round\s+ID|Review\s+Skills?|Layer\s*3(?:\s+Skills?)?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "execution-level-protocol",
        re.compile(
            r"(?:"
            r"\bL[1-5](?:\s*(?:-|/|to)\s*L[1-5]|\+)?\b.{0,48}"
            r"\b(?:check|closure|gate|implementation|load|mode|proof|read|reference|"
            r"result|review|task|work)\b|"
            r"\b(?:bounded|compact|full|implementation|mode|proof|read|reference|"
            r"result|review|task|work)\b.{0,48}"
            r"\bL[1-5](?:\s*(?:-|/|to)\s*L[1-5]|\+)?\b|"
            r"\|\s*L[1-5](?:\s*(?:-|/|to)\s*L[1-5]|\+)?\s*\|"
            r")",
            re.IGNORECASE,
        ),
    ),
    (
        "control-role-dependency",
        re.compile(
            r"(?:"
            r"\b(?:Main|Core)\b.{0,80}\b(?:analyzed|authority|decides?|discipline|"
            r"dispatch|guard|handoff|owns?|projection|relation|rerout\w*|rout\w*|"
            r"selects?)\b|"
            r"\b(?:[Ee]scalate|[Hh]andoff|[Rr]eroute|[Rr]eturn|[Rr]oute)\w*\b.{0,80}"
            r"\b(?:through|to)\s+(?:Main|Core)\b"
            r")"
        ),
    ),
)
_SIBLING_ROUTE_RELATION_RE = re.compile(
    r"(?:"
    r"\b(?:defer\w*|escalat\w*|forward\w*|hand[- ]?off|rerout\w*|rout\w*|"
    r"send\w*)\b.{0,120}\b(?:through|to|via)\b|"
    r"\b(?:go|goes)\s+to\b|"
    r"\b(?:deferred|escalated|forwarded|handed[- ]off|rerouted|routed|sent)\b"
    r".{0,120}\bby\b"
    r")",
    re.IGNORECASE,
)
_SIBLING_OWNER_AFTER_RE = re.compile(
    r"^[\s`*_]*(?:owns?\b|(?:is|remains|serves\s+as)\s+(?:the\s+|an?\s+)?"
    r"(?:[a-z][a-z -]{0,40}\s+)?owner\b)",
    re.IGNORECASE,
)
_SIBLING_OWNER_BEFORE_RE = re.compile(
    r"(?:\bowner\s*(?:is|:|=)|\bowned\s+by)\s*$",
    re.IGNORECASE,
)


def _load_content_audit_module() -> ModuleType:
    """Load the repository's single Skill-content collector without running it."""

    global _CONTENT_AUDIT_MODULE
    if _CONTENT_AUDIT_MODULE is not None:
        return _CONTENT_AUDIT_MODULE
    module_name = "_rd_skills_audit_skill_content"
    spec = importlib.util.spec_from_file_location(module_name, CONTENT_AUDIT_SCRIPT)
    if spec is None or spec.loader is None:
        raise ValidationProblem(f"cannot load Skill-content collector {CONTENT_AUDIT_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    _CONTENT_AUDIT_MODULE = module
    return module


def _professional_independence_documents() -> list[dict[str, object]]:
    """Collect governed Professional content through the audit owner."""

    audit = _load_content_audit_module()
    return [dict(document) for document in audit._professional_skill_documents()]


def _registered_skill_names() -> set[str]:
    """Return registered Skill identities used only to recognize sibling routes."""

    names: set[str] = set()
    for path, key in SKILL_REGISTRIES:
        data = load_yaml_file(path)
        entries = data.get(key) if isinstance(data, dict) else None
        if not isinstance(entries, list):
            raise ValidationProblem(f"{path.relative_to(ROOT)}:{key} must be a list")
        names.update(
            str(entry["name"])
            for entry in entries
            if isinstance(entry, dict)
            and isinstance(entry.get("name"), str)
            and str(entry["name"]).strip()
        )
    return names


def _normalized_excerpt(line: str, *, limit: int = 240) -> str:
    excerpt = " ".join(line.split())
    if len(excerpt) <= limit:
        return excerpt
    return excerpt[: limit - 1].rstrip() + "…"


def professional_independence_findings(
    documents: Iterable[dict[str, object]],
    *,
    registered_skill_names: Iterable[str],
) -> list[dict[str, object]]:
    """Return deterministic contextual rd-skills self-coupling findings.

    Generic engineering concepts remain valid. A finding requires an explicit
    branded/versioned protocol, a control routing object, an execution-level
    usage context, a Main/Core authority relation, or a routing action naming a
    different registered Skill.
    """

    skill_names = tuple(sorted({str(name) for name in registered_skill_names}))
    findings: list[dict[str, object]] = []
    seen: set[tuple[str, str, int, str]] = set()

    def add(path: str, category: str, line_number: int, line: str) -> None:
        excerpt = _normalized_excerpt(line)
        key = (path, category, line_number, excerpt)
        if not excerpt or key in seen:
            return
        seen.add(key)
        findings.append(
            {
                "path": path,
                "category": category,
                "line": line_number,
                "excerpt": excerpt,
            }
        )

    for document in documents:
        path = str(document.get("path", ""))
        owner = str(document.get("owner", ""))
        governed_text = document.get("governed_text")
        text = governed_text if isinstance(governed_text, str) else document.get("text")
        if not path or not isinstance(text, str):
            continue
        line_offset = document.get("line_offset", 0)
        if type(line_offset) is not int:
            line_offset = 0
        for local_line, line in enumerate(text.splitlines(), start=1):
            absolute_line = line_offset + local_line
            for category, pattern in _INDEPENDENCE_RAW_LINE_PATTERNS:
                if pattern.search(line):
                    add(path, category, absolute_line, line)
            # Canonical Registry projections have already been blanked from
            # governed_text. Any remaining Markdown table row is authored
            # content and is one bounded semantic unit in its own right.
            if line.lstrip().startswith("|"):
                for category, pattern in _INDEPENDENCE_UNIT_PATTERNS:
                    if pattern.search(line):
                        add(path, category, absolute_line, line)

        for unit in _ai_markdown_units(text):
            unit_text = str(unit["text"])
            absolute_line = line_offset + int(unit["line"])
            for category, pattern in _INDEPENDENCE_UNIT_PATTERNS:
                if pattern.search(unit_text):
                    add(path, category, absolute_line, unit_text)

            folded_unit = unit_text.casefold()
            relation = _SIBLING_ROUTE_RELATION_RE.search(unit_text)
            sibling_route = False
            sibling_owner = False
            for name in skill_names:
                if name == owner:
                    continue
                target = re.search(
                    rf"(?<![a-z0-9-]){re.escape(name.casefold())}(?![a-z0-9-])",
                    folded_unit,
                )
                if target:
                    if relation and "|" not in relation.group(0):
                        if (
                            target.start() >= relation.end()
                            and "|"
                            not in unit_text[relation.end() : target.start()]
                        ):
                            sibling_route = True
                    owner_before = unit_text[
                        max(0, target.start() - 80) : target.start()
                    ]
                    owner_after = unit_text[target.end() : target.end() + 96]
                    if (
                        _SIBLING_OWNER_BEFORE_RE.search(owner_before)
                        or _SIBLING_OWNER_AFTER_RE.search(owner_after)
                    ):
                        sibling_owner = True
            if sibling_route:
                add(path, "sibling-skill-route", absolute_line, unit_text)
            if sibling_owner:
                add(path, "sibling-skill-owner", absolute_line, unit_text)

    return sorted(
        findings,
        key=lambda finding: (
            str(finding["path"]),
            int(finding["line"]),
            str(finding["category"]),
            str(finding["excerpt"]),
        ),
    )


def professional_independence_report(
    documents: Iterable[dict[str, object]],
    *,
    registered_skill_names: Iterable[str],
) -> dict[str, object]:
    """Build the report-only Professional independence inventory."""

    document_rows = list(documents)
    findings = professional_independence_findings(
        document_rows,
        registered_skill_names=registered_skill_names,
    )
    counts = Counter(str(finding["category"]) for finding in findings)
    return {
        "schema_version": 1,
        "mode": "report-only",
        "collector": "scripts/audit-skill-content.py",
        "scope": (
            "authored governed Professional content (Professional roots excluding "
            "the canonical Registry-generated Targeted References projection only "
            "after exact current Registry/package/root equality is proved, physical "
            "References, and examples)"
        ),
        "document_count": len(document_rows),
        "finding_count": len(findings),
        "category_counts": dict(sorted(counts.items())),
        "findings": findings,
        "proof_limits": [
            "Zero findings covers authored governed Professional content in this "
            "scope, not every source byte.",
            "The canonical Registry-generated Targeted References projection is "
            "adapter metadata logically excluded from authored domain knowledge "
            "only when current Registry names, package paths, root membership, "
            "frontmatter names, Reference contracts, and rendered source bytes are "
            "exactly equal; it may select only optional Reference and depth and "
            "cannot change owner, invariant, failure, acceptance, domain verdict, "
            "or proof obligation.",
            "Contextual static detection does not prove that every control dependency is absent.",
            "Non-Markdown and other non-root/non-Reference/non-example assets are outside the audit collector's governed scope.",
        ],
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


def _validate_professional_section_contract(
    body: str,
    context: str,
    errors: list[str],
) -> None:
    detail_presence = {
        title: bool(re.search(rf"^## {re.escape(title)}\s*$", body, re.MULTILINE))
        for title in AUTHORING_DETAIL_SECTIONS
    }
    if len(set(detail_presence.values())) != 1:
        errors.append(
            f"{context}: 'High-Value Gotchas' and 'Execution Checklist' "
            "must appear together"
        )
    required_sections = [*PROFESSIONAL_BUILT_KERNEL_HEADINGS]
    if all(detail_presence.values()):
        insertion = required_sections.index("Stop / Escalation Conditions")
        required_sections[insertion:insertion] = AUTHORING_DETAIL_SECTIONS
    required_sections.append("Targeted References")
    validate_required_sections(
        body,
        required_sections,
        context,
        errors,
        require_order=True,
    )


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
    has_execution = bool(
        re.search(r"^## Execution Checklist\s*$", body, re.MULTILINE)
    )
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
            if has_execution and mode_marker not in execution:
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


def _args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        PROFESSIONAL_INDEPENDENCE_REPORT_FLAG,
        action="store_true",
        help=(
            "Print a deterministic advisory inventory of contextual rd-skills "
            "self-coupling in Professional content without changing validation status."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _args(sys.argv[1:] if argv is None else argv)
    if args.professional_independence_report:
        try:
            report = professional_independence_report(
                _professional_independence_documents(),
                registered_skill_names=_registered_skill_names(),
            )
        except (OSError, ValidationProblem, ValueError) as exc:
            print(f"validate-skills: ERROR: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
        return 0

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
    try:
        independence_findings = professional_independence_findings(
            _professional_independence_documents(),
            registered_skill_names=_registered_skill_names(),
        )
    except (OSError, ValidationProblem, ValueError) as exc:
        errors.append(f"Professional independence validation failed: {exc}")
    else:
        errors.extend(
            f"{finding['path']}:{finding['line']}: confirmed Professional "
            f"independence finding [{finding['category']}]: {finding['excerpt']}"
            for finding in independence_findings
        )
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
        _validate_professional_section_contract(body, context, errors)
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
