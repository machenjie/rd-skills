#!/usr/bin/env python3
"""Audit professional-coverage of the stage-aware architecture.

Report-only by default. This tool is read-only and NEVER modifies skills. It
checks that every engineering stage, product surface, and language surface has an
owner, that bodies are not over-long, that professional rules and the stage matrix
are not duplicated across files, that language-deep content has not leaked into the
router or the stage launcher, that triggers are not catch-all, and that output
contracts are verifiable.

It writes two reports:

- reports/professionalism-coverage.md  (human-readable)
- reports/professionalism-coverage.json (machine-readable)

It does not access the network and does not call any model. It exits 0 even when
findings exist, so it can run in an authoring workflow without blocking the build.
Pass --strict to exit non-zero when any finding is present.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from validation_utils import (
    ValidationProblem,
    load_yaml_file,
    parse_frontmatter,
)


ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
STAGE_MODEL_DOC = DOCS_DIR / "ENGINEERING_STAGE_MODEL.md"
PROFESSIONAL_SKILLS_DIR = ROOT / "src" / "professional-skills"
CAPABILITIES_DIR = ROOT / "src" / "foundation" / "capabilities"
DOMAIN_EXTENSIONS_DIR = ROOT / "src" / "domain-extensions"
REGISTRY_DIR = ROOT / "src" / "registry"
CAPABILITIES_REGISTRY = REGISTRY_DIR / "capabilities.yaml"
ROUTER_SKILL = PROFESSIONAL_SKILLS_DIR / "change-forge-router" / "SKILL.md"
STAGE_LAUNCHER = CAPABILITIES_DIR / "engineering-stage-professionalism" / "SKILL.md"
REPORTS_DIR = ROOT / "reports"
MARKDOWN_REPORT = REPORTS_DIR / "professionalism-coverage.md"
JSON_REPORT = REPORTS_DIR / "professionalism-coverage.json"

REQUIRED_STAGES = (
    "requirement-intake",
    "architecture-design",
    "implementation-planning",
    "coding",
    "debugging-diagnosis",
    "bug-fix",
    "code-review",
    "refactoring",
    "testing",
    "release-delivery",
    "documentation-handoff",
    "skill-authoring",
)
LANGUAGE_CAPABILITIES = (
    "go-professional-usage",
    "java-jvm-professional-usage",
    "typescript-professional-usage",
    "python-professional-usage",
    "rust-professional-usage",
    "cpp-professional-usage",
    "shell-cli-professional-usage",
    "sql-professional-usage",
)

# Body-size advisory thresholds (lines, excluding frontmatter).
BODY_LINE_LIMITS = {
    "professional-skill": 350,
    "foundation-capability": 250,
    "domain-extension": 300,
}
# A single trigger string longer than this many words reads as a catch-all.
TRIGGER_WORD_LIMIT = 45
# Distinctive marker of the canonical full stage matrix.
FULL_MATRIX_MARKER = "do not launch by default"
# Markers that signal a per-language deep checklist copied where only a
# reference belongs.
LANGUAGE_DEEP_MARKERS = (
    "goroutine",
    "borrow checker",
    "errgroup",
    "raii",
    "monkeypatch",
    "context.todo",
    "strings.builder",
)
LANGUAGE_DEEP_MARKER_LIMIT = 2
BACKTICK_RE = re.compile(r"`([^`\n]+)`")
TABLE_ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")


@dataclass
class Finding:
    check: str
    severity: str
    target: str
    message: str


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    stages_checked: int = 0
    product_surfaces_checked: int = 0
    language_surfaces_checked: int = 0
    bodies_checked: int = 0

    def add(self, check: str, severity: str, target: str, message: str) -> None:
        self.findings.append(Finding(check, severity, target, message))


def _registry_capability_names() -> set[str]:
    try:
        data = load_yaml_file(CAPABILITIES_REGISTRY)
    except ValidationProblem:
        return set()
    entries = data.get("capabilities") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        return set()
    return {
        entry["name"]
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("name"), str)
    }


def _registry_capability_triggers() -> dict[str, list[str]]:
    try:
        data = load_yaml_file(CAPABILITIES_REGISTRY)
    except ValidationProblem:
        return {}
    entries = data.get("capabilities") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        return {}
    result: dict[str, list[str]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        triggers = entry.get("triggers")
        if isinstance(name, str) and isinstance(triggers, list):
            result[name] = [t for t in triggers if isinstance(t, str)]
    return result


def _skill_names() -> set[str]:
    names: set[str] = set()
    for root in (PROFESSIONAL_SKILLS_DIR, DOMAIN_EXTENSIONS_DIR):
        if root.is_dir():
            names.update(p.name for p in root.glob("*/") if (p / "SKILL.md").is_file())
    return names


def _all_owner_names() -> set[str]:
    return _registry_capability_names() | _skill_names()


def _iter_skill_files() -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []
    roots = {
        PROFESSIONAL_SKILLS_DIR: "professional-skill",
        CAPABILITIES_DIR: "foundation-capability",
        DOMAIN_EXTENSIONS_DIR: "domain-extension",
    }
    for root, kind in roots.items():
        if not root.is_dir():
            continue
        for skill_file in sorted(root.glob("*/SKILL.md")):
            files.append((skill_file, kind))
    return files


def _stage_model_text() -> str:
    if not STAGE_MODEL_DOC.is_file():
        return ""
    return STAGE_MODEL_DOC.read_text(encoding="utf-8")


def _stage_launch_owners(text: str) -> dict[str, list[str]]:
    """Map each '### <stage>' block to the capabilities on its '- Launch:' line."""
    owners: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        heading = re.match(r"^###\s+(.+?)\s*$", line)
        if heading:
            current = heading.group(1).strip()
            continue
        if current and line.strip().lower().startswith("- launch:"):
            owners[current] = BACKTICK_RE.findall(line)
            current = None
    return owners


def _table_column_values(text: str, header_marker: str, column_index: int) -> list[str]:
    """Return backtick values from a given column of the table under a header."""
    lines = text.splitlines()
    values: list[str] = []
    in_section = False
    for line in lines:
        if header_marker.casefold() in line.casefold() and line.startswith("##"):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if not in_section:
            continue
        row = TABLE_ROW_RE.match(line)
        if not row:
            continue
        cells = [c.strip() for c in row.group(1).split("|")]
        if len(cells) <= column_index:
            continue
        cell = cells[column_index]
        if set(cell) <= {"-", ":", " "}:
            continue
        found = BACKTICK_RE.findall(cell)
        values.extend(found)
    return values


def _check_stage_owners(report: Report, owner_names: set[str]) -> None:
    text = _stage_model_text()
    launch_owners = _stage_launch_owners(text)
    for stage in REQUIRED_STAGES:
        report.stages_checked += 1
        owners = launch_owners.get(stage)
        if not owners:
            report.add(
                "stage-owner", "high", stage,
                "stage has no '- Launch:' owner capabilities in ENGINEERING_STAGE_MODEL.md",
            )
            continue
        for owner in owners:
            if owner not in owner_names:
                report.add(
                    "stage-owner", "medium", stage,
                    f"launch owner '{owner}' is not a registered capability or skill",
                )


def _check_product_surface_owners(report: Report, owner_names: set[str]) -> None:
    text = _stage_model_text()
    skills = _table_column_values(text, "Product Surface Selector", 1)
    for skill in skills:
        report.product_surfaces_checked += 1
        if skill not in owner_names:
            report.add(
                "product-surface-owner", "medium", skill,
                "product surface owner skill is not a registered skill or capability",
            )


def _check_language_surface_owners(report: Report, owner_names: set[str]) -> None:
    text = _stage_model_text()
    caps = _table_column_values(text, "Language Surface Selector", 1)
    declared = set(caps)
    for cap in caps:
        report.language_surfaces_checked += 1
        if cap not in owner_names:
            report.add(
                "language-surface-owner", "medium", cap,
                "language surface owner capability is not registered",
            )
    for expected in LANGUAGE_CAPABILITIES:
        if expected not in declared:
            report.add(
                "language-surface-owner", "high", expected,
                "language capability is missing from the Language Surface Selector",
            )


def _check_professional_skill_stage_declaration(report: Report) -> None:
    text = _stage_model_text().casefold()
    if not PROFESSIONAL_SKILLS_DIR.is_dir():
        return
    for skill_dir in sorted(PROFESSIONAL_SKILLS_DIR.glob("*/")):
        name = skill_dir.name
        if name == "change-forge-router":
            continue
        if name.casefold() not in text:
            report.add(
                "skill-stage-declaration", "low", name,
                "professional skill is not referenced in the stage model "
                "(stage matrix or product surface selector)",
            )


def _check_body_sizes_and_contracts(report: Report) -> None:
    for skill_file, kind in _iter_skill_files():
        try:
            _metadata, _raw, body = parse_frontmatter(skill_file)
        except ValidationProblem:
            continue
        report.bodies_checked += 1
        rel = str(skill_file.relative_to(ROOT))
        line_count = len(body.splitlines())
        limit = BODY_LINE_LIMITS.get(kind, 300)
        if line_count > limit:
            report.add(
                "body-size", "low", rel,
                f"body is {line_count} lines (advisory limit {limit} for {kind})",
            )
        # Output-contract verifiability: professional skills and the stage
        # launcher must carry a structured Output Contract.
        if kind == "professional-skill" or skill_file == STAGE_LAUNCHER:
            folded = body.casefold()
            if "output contract" not in folded:
                report.add(
                    "output-contract", "high", rel,
                    "missing an Output Contract section",
                )
            elif not re.search(r"(?m)^[-*]\s+\*?\*?[A-Za-z].+:", body) and "```" not in body:
                report.add(
                    "output-contract", "medium", rel,
                    "Output Contract has no structured fields or fenced template",
                )


def _check_trigger_breadth(report: Report) -> None:
    for name, triggers in _registry_capability_triggers().items():
        for trigger in triggers:
            words = len(trigger.split())
            if words > TRIGGER_WORD_LIMIT:
                report.add(
                    "trigger-breadth", "low", name,
                    f"a single trigger string is {words} words "
                    f"(>{TRIGGER_WORD_LIMIT}); consider splitting to avoid over-routing",
                )


def _check_matrix_duplication(report: Report) -> None:
    offenders: list[str] = []
    for skill_file, _kind in _iter_skill_files():
        text = skill_file.read_text(encoding="utf-8").casefold()
        if FULL_MATRIX_MARKER in text:
            offenders.append(str(skill_file.relative_to(ROOT)))
    if len(offenders) > 1:
        for rel in offenders:
            report.add(
                "matrix-duplication", "high", rel,
                "full stage matrix marker appears in a skill body; the matrix must "
                "live only in docs/ENGINEERING_STAGE_MODEL.md",
            )


def _check_language_deep_leak(report: Report) -> None:
    for path in (ROUTER_SKILL, STAGE_LAUNCHER):
        if not path.is_file():
            continue
        try:
            _metadata, _raw, body = parse_frontmatter(path)
        except ValidationProblem:
            continue
        folded = body.casefold()
        hits = [m for m in LANGUAGE_DEEP_MARKERS if m in folded]
        if len(hits) > LANGUAGE_DEEP_MARKER_LIMIT:
            report.add(
                "language-deep-leak", "high", str(path.relative_to(ROOT)),
                f"language-deep checklist content appears here ({', '.join(hits)}); "
                "reference the language capability instead",
            )


def _check_cross_file_rule_duplication(report: Report) -> None:
    """Flag long, distinctive lines repeated verbatim across many skill bodies."""
    line_sources: dict[str, set[str]] = {}
    for skill_file, _kind in _iter_skill_files():
        try:
            _metadata, _raw, body = parse_frontmatter(skill_file)
        except ValidationProblem:
            continue
        rel = str(skill_file.relative_to(ROOT))
        seen: set[str] = set()
        for raw_line in body.splitlines():
            line = raw_line.strip().strip("-*").strip()
            if len(line) < 60 or line.startswith("#") or line.startswith("|"):
                continue
            key = line.casefold()
            if key in seen:
                continue
            seen.add(key)
            line_sources.setdefault(key, set()).add(rel)
    for key, sources in line_sources.items():
        if len(sources) >= 4:
            report.add(
                "rule-duplication", "low", "; ".join(sorted(sources)[:4]),
                f"a professional rule line is duplicated across {len(sources)} bodies; "
                "consider a shared capability reference",
            )


def _write_reports(report: Report, strict: bool) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    by_check: dict[str, list[Finding]] = {}
    for finding in report.findings:
        by_check.setdefault(finding.check, []).append(finding)

    lines = ["# Professionalism Coverage Report", ""]
    lines.append(
        f"- Mode: {'strict' if strict else 'report-only'}",
    )
    lines.append(f"- Stages checked: {report.stages_checked}")
    lines.append(f"- Product surfaces checked: {report.product_surfaces_checked}")
    lines.append(f"- Language surfaces checked: {report.language_surfaces_checked}")
    lines.append(f"- Skill bodies checked: {report.bodies_checked}")
    lines.append(f"- Total findings: {len(report.findings)}")
    lines.append("")
    if not report.findings:
        lines.append("No professionalism-coverage findings.")
    else:
        for check in sorted(by_check):
            lines.append(f"## {check}")
            lines.append("")
            for finding in by_check[check]:
                lines.append(
                    f"- [{finding.severity}] `{finding.target}` — {finding.message}"
                )
            lines.append("")
    MARKDOWN_REPORT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    payload = {
        "mode": "strict" if strict else "report-only",
        "summary": {
            "stages_checked": report.stages_checked,
            "product_surfaces_checked": report.product_surfaces_checked,
            "language_surfaces_checked": report.language_surfaces_checked,
            "bodies_checked": report.bodies_checked,
            "total_findings": len(report.findings),
        },
        "findings": [asdict(f) for f in report.findings],
    }
    JSON_REPORT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit professional coverage of the stage-aware architecture."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when any finding is present (default: report-only, exit 0).",
    )
    args = parser.parse_args()

    report = Report()
    owner_names = _all_owner_names()

    _check_stage_owners(report, owner_names)
    _check_product_surface_owners(report, owner_names)
    _check_language_surface_owners(report, owner_names)
    _check_professional_skill_stage_declaration(report)
    _check_body_sizes_and_contracts(report)
    _check_trigger_breadth(report)
    _check_matrix_duplication(report)
    _check_language_deep_leak(report)
    _check_cross_file_rule_duplication(report)

    _write_reports(report, args.strict)

    print(
        "audit-professionalism-coverage: "
        f"{len(report.findings)} finding(s) across "
        f"{report.stages_checked} stage(s), {report.product_surfaces_checked} product "
        f"surface(s), {report.language_surfaces_checked} language surface(s), and "
        f"{report.bodies_checked} body(s). "
        f"Reports written to {MARKDOWN_REPORT.relative_to(ROOT)} and "
        f"{JSON_REPORT.relative_to(ROOT)}."
    )

    if args.strict and report.findings:
        print(
            "audit-professionalism-coverage: ERROR: strict mode and findings present.",
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
