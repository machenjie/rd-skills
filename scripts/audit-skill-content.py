#!/usr/bin/env python3
"""Audit ChangeForge SKILL content for professionalism, redundancy, and split candidates.

This tool is read-only. It NEVER modifies SKILL.md files. It walks the three
authoring roots, computes per-file content metrics, detects cross-file duplicated
content, scores each skill on four advisory dimensions, classifies a suggested
action, and writes two grouped reports:

- reports/skill-content-audit.md  (human-readable, grouped by kind)
- reports/skill-content-audit.json (machine-readable, full metric detail)

Finding a problem does not make the audit fail; it always exits 0 unless an
internal error occurs. Thresholds are centralized in THRESHOLDS below.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path

from validation_utils import (
    ValidationProblem,
    load_yaml_file,
    parse_frontmatter,
)


ROOT = Path(__file__).resolve().parents[1]
PROFESSIONAL_SKILLS_DIR = ROOT / "src" / "professional-skills"
CAPABILITIES_DIR = ROOT / "src" / "foundation" / "capabilities"
DOMAIN_EXTENSIONS_DIR = ROOT / "src" / "domain-extensions"
CAPABILITIES_REGISTRY = ROOT / "src" / "registry" / "capabilities.yaml"
REPORTS_DIR = ROOT / "reports"
MARKDOWN_REPORT = REPORTS_DIR / "skill-content-audit.md"
JSON_REPORT = REPORTS_DIR / "skill-content-audit.json"

# --- Centralized, configurable thresholds -----------------------------------
THRESHOLDS = {
    # Body length (lines) review / heavy gates per kind.
    "professional_review_lines": 250,
    "professional_heavy_lines": 350,
    "foundation_heavy_lines": 250,
    "domain_heavy_lines": 300,
    # Section / table size gates.
    "section_split_lines": 80,
    "table_move_rows": 20,
    # Movable-theme gates: a body block this large is worth summarizing + relocating.
    "movable_benchmark_lines": 40,
    "movable_anti_lines": 14,
    "movable_optimality_lines": 35,
    # Cross-file duplication.
    "common_phrase_min_files": 3,
    "significant_line_min_chars": 40,
    # Score gates used for classification.
    "low_professionalism": 70,
    "split_candidate_high": 60,
    # used_by fan-out that, combined with heavy body, is a concern.
    "used_by_fanout": 4,
    # Frontmatter description risk gate. validate-skills enforces 120-700 chars;
    # the audit flags descriptions that drift long enough to read like a body
    # summary rather than a trigger condition.
    "description_long_chars": 360,
}

# A description should say WHEN to use the skill, not summarize the whole workflow.
DESCRIPTION_WORKFLOW_MARKERS = (
    " then ",
    " first ",
    " next, ",
    " step ",
    " step-by-step",
    " follow these",
    " and then ",
    "1.",
    "2.",
)
DESCRIPTION_CATCHALL_MARKERS = (
    "everything",
    "anything",
    "any change",
    "all changes",
    "all code",
    "every change",
    "general-purpose",
    "general purpose",
    "catch-all",
)
# Trigger framing or a scope noun shows the description names a situation it
# applies to, not a bare process. A scoping preposition (for/of/across/into/...)
# counts as trigger framing. Absence of all of these is the missing-trigger
# signal, which is a high-precision guard against vague descriptions.
DESCRIPTION_TRIGGER_MARKERS = (
    "use when",
    "use for",
    " when ",
    " for ",
    " before ",
    " during ",
    " after ",
    " of ",
    " into ",
    " across ",
    " on ",
    " in ",
    " to ",
    " with ",
)
DESCRIPTION_SCOPE_NOUNS = (
    "change",
    "code",
    "product",
    "api",
    "schema",
    "data",
    "skill",
    "review",
    "test",
    "release",
    "migration",
    "security",
    "frontend",
    "backend",
    "deployment",
    "request",
)
# ChangeForge descriptions conventionally open with a capability verb that states
# what the skill does ("Designs ...", "Reviews ..."). A capability-verb opening
# is itself trigger framing, so the missing-trigger check stays a high-precision
# guard for genuinely vague descriptions.
DESCRIPTION_CAPABILITY_VERBS = frozenset({
    "designs", "defines", "reviews", "requires", "adds", "models", "guides",
    "selects", "analyzes", "verifies", "produces", "identifies", "evaluates",
    "decomposes", "structures", "separates", "prevents", "plans", "packages",
    "implements", "extracts", "ensures", "enforces", "diagnoses", "describes",
    "converts", "classifies", "builds", "breaks", "applies", "maps", "detects",
    "manages", "maintains", "provides", "coordinates", "generates", "validates",
    "creates", "optimizes", "reduces", "routes", "handles", "orchestrates",
})

HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$")
FENCE_RE = re.compile(r"^(```+|~~~+)")
LIST_ITEM_RE = re.compile(r"^\s{0,3}(?:[-*+]|\d+[.)])\s+(.+?)\s*$")
LIST_MARKER_RE = re.compile(r"^([-*+]|\d+[.)])\s+")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\([^)]+\)")
TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?[\s:|-]*-[\s:|-]*\|?\s*$")
SPECIFICITY_RE = re.compile(
    r"\b(?:\d+%?|P\d{2}|RFC\s?\d+|OWASP|ISO\s?\d+|SOC\s?2|O\(|SLO|SLA|p9\d)\b",
    re.IGNORECASE,
)

BANNED_BEGINNER_TITLES = {
    "basic usage",
    "installation tutorial",
    "hello world",
    "introduction",
    "getting started",
    "quick start",
    "beginner guide",
    "syntax",
    "framework setup",
}

KIND_BASE_LEVEL = {
    "professional-skill": 2,
    "foundation-capability": 1,
    "domain-extension": 2,
}

KIND_LABEL = {
    "professional-skill": "Professional Skills",
    "foundation-capability": "Foundation Capabilities",
    "domain-extension": "Domain Extensions",
}


@dataclass
class Section:
    level: int
    title: str
    start: int
    line_count: int
    text: str


@dataclass
class SkillMetrics:
    name: str
    path: str
    kind: str
    line_count: int = 0
    word_count: int = 0
    heading_count: int = 0
    table_count: int = 0
    largest_table_rows: int = 0
    code_block_count: int = 0
    bullet_count: int = 0
    reference_link_count: int = 0
    repeated_phrase_count: int = 0
    anti_example_section_length: int = 0
    benchmark_section_length: int = 0
    critical_details_length: int = 0
    output_contract_length: int = 0
    optimality_section_length: int = 0
    largest_section_title: str = ""
    largest_section_lines: int = 0
    oversized_sections: list[dict] = field(default_factory=list)
    oversized_tables: list[int] = field(default_factory=list)
    used_by_count: int = 0
    description_length: int = 0
    description_findings: list[str] = field(default_factory=list)
    has_shared_optimality: bool = False
    professionalism_score: int = 100
    context_efficiency_score: int = 100
    routing_clarity_score: int = 100
    split_candidate_score: int = 0
    findings: list[str] = field(default_factory=list)
    classification: str = "KEEP_AS_IS"
    suggested_action: str = ""
    risk_of_change: str = "low"
    recommended_phase: str = "-"


def _strip_fenced(lines: list[str]) -> list[tuple[int, str, bool]]:
    """Yield (index, line, in_fence) where in_fence marks fenced-code content."""
    result: list[tuple[int, str, bool]] = []
    in_fence = False
    marker: str | None = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        fence_match = FENCE_RE.match(stripped)
        if fence_match:
            token = fence_match.group(1)[:3]
            if not in_fence:
                in_fence = True
                marker = token
                result.append((index, line, True))
                continue
            if marker and token.startswith(marker):
                in_fence = False
                marker = None
            result.append((index, line, True))
            continue
        result.append((index, line, in_fence))
    return result


def parse_sections(body: str) -> list[Section]:
    lines = body.splitlines()
    annotated = _strip_fenced(lines)
    headings: list[tuple[int, int, str]] = []
    for index, line, in_fence in annotated:
        if in_fence:
            continue
        match = HEADING_RE.match(line)
        if match:
            headings.append((index, len(match.group(1)), match.group(2).strip()))

    sections: list[Section] = []
    for position, (index, level, title) in enumerate(headings):
        end = len(lines)
        for later in headings[position + 1:]:
            if later[1] <= level:
                end = later[0]
                break
        body_lines = lines[index + 1: end]
        sections.append(
            Section(
                level=level,
                title=title,
                start=index,
                line_count=end - index,
                text="\n".join(body_lines).strip(),
            )
        )
    return sections


def _find_section(sections: list[Section], title: str) -> Section | None:
    wanted = title.casefold()
    for section in sections:
        if section.title.casefold() == wanted:
            return section
    return None


def _find_section_contains(sections: list[Section], needle: str) -> Section | None:
    needle = needle.casefold()
    for section in sections:
        if needle in section.title.casefold():
            return section
    return None


def _count_tables(body: str) -> tuple[int, int, list[int]]:
    """Return (table_count, largest_table_rows, oversized_table_row_counts)."""
    lines = body.splitlines()
    annotated = _strip_fenced(lines)
    table_count = 0
    largest = 0
    oversized: list[int] = []
    rows = 0
    in_table = False
    for _index, line, in_fence in annotated:
        if in_fence:
            continue
        stripped = line.strip()
        is_pipe_row = stripped.startswith("|") and stripped.count("|") >= 2
        if is_pipe_row:
            if not in_table:
                in_table = True
                rows = 0
                table_count += 1
            if not TABLE_SEPARATOR_RE.match(stripped):
                rows += 1
        else:
            if in_table:
                largest = max(largest, rows)
                if rows > THRESHOLDS["table_move_rows"]:
                    oversized.append(rows)
                in_table = False
    if in_table:
        largest = max(largest, rows)
        if rows > THRESHOLDS["table_move_rows"]:
            oversized.append(rows)
    return table_count, largest, oversized


def _normalize_significant_line(line: str) -> str | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if HEADING_RE.match(line):
        return None
    if stripped.startswith("|") or TABLE_SEPARATOR_RE.match(stripped):
        return None
    if re.fullmatch(r"[-=_*\s>`]+", stripped):
        return None
    normalized = LIST_MARKER_RE.sub("", stripped)
    normalized = re.sub(r"\s+", " ", normalized).casefold()
    if len(normalized) < THRESHOLDS["significant_line_min_chars"]:
        return None
    return normalized


def _significant_lines(body: str) -> list[str]:
    lines = body.splitlines()
    annotated = _strip_fenced(lines)
    result: list[str] = []
    for _index, line, in_fence in annotated:
        if in_fence:
            continue
        normalized = _normalize_significant_line(line)
        if normalized:
            result.append(normalized)
    return result


def _section_bullet_count(section: Section | None) -> int:
    if section is None:
        return 0
    return sum(1 for line in section.text.splitlines() if LIST_ITEM_RE.match(line))


def _section_weak(section: Section | None, min_chars: int, min_bullets: int) -> bool:
    """A section is weak only when it is both short prose AND under-enumerated.

    Foundation capabilities legitimately use prose paragraphs (not bullets) for
    'Do Not Use When'; this avoids penalizing that authored style.
    """
    if section is None:
        return True
    content = section.text.strip()
    bullets = sum(1 for line in content.splitlines() if LIST_ITEM_RE.match(line))
    return len(content) < min_chars and bullets < min_bullets


def _load_used_by_counts() -> dict[str, int]:
    counts: dict[str, int] = {}
    if not CAPABILITIES_REGISTRY.is_file():
        return counts
    try:
        data = load_yaml_file(CAPABILITIES_REGISTRY)
    except ValidationProblem:
        return counts
    if not isinstance(data, dict):
        return counts
    for entry in data.get("capabilities", []) or []:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        used_by = entry.get("used_by")
        if isinstance(name, str) and isinstance(used_by, list):
            counts[name] = len([item for item in used_by if isinstance(item, str)])
    return counts


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


def _description_findings(description: str | None) -> list[str]:
    """Risk findings for a frontmatter description.

    A description states WHEN to use a skill, not the whole workflow. Returns the
    advisory findings: too long, workflow-summary, catch-all, or missing trigger.
    """
    findings: list[str] = []
    text = (description or "").strip()
    if not text:
        findings.append("description: missing")
        return findings
    lowered = " " + text.casefold() + " "
    if len(text) > THRESHOLDS["description_long_chars"]:
        findings.append(
            f"description: long ({len(text)} chars); keep it to trigger conditions, not a body summary"
        )
    if any(marker in lowered for marker in DESCRIPTION_WORKFLOW_MARKERS):
        findings.append("description: reads like a workflow summary; move the workflow to the body")
    if any(marker in lowered for marker in DESCRIPTION_CATCHALL_MARKERS):
        findings.append("description: broad/catch-all wording risks over-routing; scope the trigger")
    first_word_match = re.match(r"\s*([A-Za-z]+)", text)
    starts_with_capability_verb = bool(
        first_word_match and first_word_match.group(1).casefold() in DESCRIPTION_CAPABILITY_VERBS
    )
    has_trigger = starts_with_capability_verb or any(
        marker in lowered for marker in DESCRIPTION_TRIGGER_MARKERS
    )
    has_scope = any(noun in lowered for noun in DESCRIPTION_SCOPE_NOUNS)
    if not has_trigger and not has_scope:
        findings.append("description: states no trigger condition or scope (when/for/use, or a scope noun)")
    return findings


def _base_metrics(kind: str, path: Path, body: str, used_by_counts: dict[str, int]) -> SkillMetrics:
    lines = body.splitlines()
    sections = parse_sections(body)
    table_count, largest_table, oversized_tables = _count_tables(body)
    annotated = _strip_fenced(lines)

    bullet_count = sum(
        1 for _index, line, in_fence in annotated if not in_fence and LIST_ITEM_RE.match(line)
    )
    code_block_count = sum(
        1 for _index, line, in_fence in annotated if FENCE_RE.match(line.strip())
    ) // 2

    anti = _find_section_contains(sections, "anti-example")
    benchmark = _find_section(sections, "Industry Benchmarks")
    critical = _find_section(sections, "Critical Details")
    output_contract = _find_section(sections, "Output Contract")
    optimality = _find_section_contains(sections, "solution optimality")

    base_level = KIND_BASE_LEVEL[kind]
    # Only the authored top-level sections count; the document H1 title (present in
    # professional skills) is not a content section and must not masquerade as one.
    top_sections = [s for s in sections if s.level == base_level]
    oversized_sections = [
        {"title": s.title, "lines": s.line_count}
        for s in top_sections
        if s.line_count > THRESHOLDS["section_split_lines"]
    ]
    largest_section = max(top_sections, key=lambda s: s.line_count, default=None)

    metrics = SkillMetrics(
        name=path.parent.name,
        path=str(path.relative_to(ROOT)).replace("\\", "/"),
        kind=kind,
        line_count=len(lines),
        word_count=len(body.split()),
        heading_count=len(sections),
        table_count=table_count,
        largest_table_rows=largest_table,
        code_block_count=code_block_count,
        bullet_count=bullet_count,
        reference_link_count=len(MARKDOWN_LINK_RE.findall(body)),
        anti_example_section_length=anti.line_count if anti else 0,
        benchmark_section_length=benchmark.line_count if benchmark else 0,
        critical_details_length=critical.line_count if critical else 0,
        output_contract_length=output_contract.line_count if output_contract else 0,
        optimality_section_length=optimality.line_count if optimality else 0,
        largest_section_title=largest_section.title if largest_section else "",
        largest_section_lines=largest_section.line_count if largest_section else 0,
        oversized_sections=oversized_sections,
        oversized_tables=oversized_tables,
        used_by_count=used_by_counts.get(path.parent.name, 0),
    )
    return metrics


def _score(metrics: SkillMetrics, sections: list[Section], body: str) -> None:
    kind = metrics.kind
    titles = {s.title.casefold() for s in sections}

    has_when = "when to use" in titles or "trigger signals" in titles
    has_do_not = "do not use when" in titles
    quality_gate = _find_section(sections, "Quality Gate")
    non_negotiable = _find_section(sections, "Non-Negotiable Rules")
    do_not_section = _find_section(sections, "Do Not Use When")
    risk_section = _find_section_contains(sections, "risk")

    # --- professionalism -----------------------------------------------------
    professionalism = 100
    if not has_when:
        professionalism -= 15
        metrics.findings.append("missing 'When To Use'/'Trigger Signals' boundary")
    if not has_do_not:
        professionalism -= 15
        metrics.findings.append("missing 'Do Not Use When' boundary")
    if _section_weak(non_negotiable, min_chars=200, min_bullets=3):
        professionalism -= 10
        metrics.findings.append("Non-Negotiable Rules is thin (short prose, few rules)")
    if quality_gate is None:
        professionalism -= 25
        metrics.findings.append("missing Quality Gate")
    elif _section_weak(quality_gate, min_chars=200, min_bullets=3):
        professionalism -= 12
        metrics.findings.append("Quality Gate is thin (few verifiable checks)")
    if "output contract" not in titles:
        professionalism -= 10
    if "completion criteria" not in titles:
        professionalism -= 8
    if titles & BANNED_BEGINNER_TITLES:
        professionalism -= 25
        metrics.findings.append("contains tutorial/beginner-style section")
    if len(SPECIFICITY_RE.findall(body)) < 5:
        professionalism -= 10
        metrics.findings.append("few concrete/measurable standards (specificity proxy low)")
    metrics.professionalism_score = max(0, min(100, professionalism))

    # --- context efficiency --------------------------------------------------
    efficiency = 100
    if kind == "professional-skill":
        if metrics.line_count > THRESHOLDS["professional_heavy_lines"]:
            efficiency -= 30
            metrics.findings.append(
                f"body {metrics.line_count} lines exceeds heavy threshold "
                f"{THRESHOLDS['professional_heavy_lines']}"
            )
        elif metrics.line_count > THRESHOLDS["professional_review_lines"]:
            efficiency -= 15
            metrics.findings.append(
                f"body {metrics.line_count} lines exceeds review threshold "
                f"{THRESHOLDS['professional_review_lines']}"
            )
    elif kind == "foundation-capability":
        if metrics.line_count > THRESHOLDS["foundation_heavy_lines"]:
            efficiency -= 25
            metrics.findings.append(
                f"body {metrics.line_count} lines exceeds heavy threshold "
                f"{THRESHOLDS['foundation_heavy_lines']}"
            )
        elif metrics.line_count > THRESHOLDS["foundation_heavy_lines"] - 50:
            efficiency -= 10
    elif kind == "domain-extension":
        if metrics.line_count > THRESHOLDS["domain_heavy_lines"]:
            efficiency -= 25
            metrics.findings.append(
                f"body {metrics.line_count} lines exceeds heavy threshold "
                f"{THRESHOLDS['domain_heavy_lines']}"
            )
        elif metrics.line_count > THRESHOLDS["domain_heavy_lines"] - 60:
            efficiency -= 10

    if metrics.has_shared_optimality:
        efficiency -= 12
        metrics.findings.append("carries shared 'Solution Optimality Self-Check' boilerplate")
    section_penalty = min(32, 8 * len(metrics.oversized_sections))
    if section_penalty:
        efficiency -= section_penalty
        for entry in metrics.oversized_sections:
            metrics.findings.append(
                f"section '{entry['title']}' is {entry['lines']} lines (> "
                f"{THRESHOLDS['section_split_lines']}) — reference candidate"
            )
    table_penalty = min(15, 5 * len(metrics.oversized_tables))
    if table_penalty:
        efficiency -= table_penalty
        for rows in metrics.oversized_tables:
            metrics.findings.append(
                f"table with {rows} rows (> {THRESHOLDS['table_move_rows']}) — move-to-reference candidate"
            )
    if metrics.repeated_phrase_count:
        efficiency -= min(20, 2 * metrics.repeated_phrase_count)
    if metrics.benchmark_section_length > THRESHOLDS["movable_benchmark_lines"]:
        metrics.findings.append(
            f"Industry Benchmarks is {metrics.benchmark_section_length} lines (> "
            f"{THRESHOLDS['movable_benchmark_lines']}) — summarize and move the deep list to a reference"
        )
    if metrics.anti_example_section_length > THRESHOLDS["movable_anti_lines"]:
        metrics.findings.append(
            f"Anti-Examples block is {metrics.anti_example_section_length} lines (> "
            f"{THRESHOLDS['movable_anti_lines']}) — move-to-reference candidate"
        )
    if metrics.optimality_section_length > THRESHOLDS["movable_optimality_lines"]:
        metrics.findings.append(
            f"Solution Optimality block is {metrics.optimality_section_length} lines (> "
            f"{THRESHOLDS['movable_optimality_lines']}) — move-to-reference candidate"
        )
    metrics.context_efficiency_score = max(0, min(100, efficiency))

    # --- routing clarity -----------------------------------------------------
    routing = 100
    if not has_when:
        routing -= 30
    if not has_do_not:
        routing -= 30
    elif _section_weak(do_not_section, min_chars=80, min_bullets=2):
        routing -= 12
        metrics.findings.append("Do Not Use When boundary is thin")
    if risk_section is None:
        routing -= 10
    metrics.routing_clarity_score = max(0, min(100, routing))

    # --- split candidate -----------------------------------------------------
    split = 0
    heavy_line_gate = {
        "professional-skill": THRESHOLDS["professional_heavy_lines"],
        "foundation-capability": THRESHOLDS["foundation_heavy_lines"],
        "domain-extension": THRESHOLDS["domain_heavy_lines"],
    }[kind]
    if metrics.line_count > heavy_line_gate:
        split += 35
    elif kind == "professional-skill" and metrics.line_count > THRESHOLDS["professional_review_lines"]:
        split += 18
    split += min(42, 14 * len(metrics.oversized_sections))
    split += min(16, 8 * len(metrics.oversized_tables))
    max_section = max((s["lines"] for s in metrics.oversized_sections), default=0)
    if max_section > 250:
        split += 22
    elif max_section > 150:
        split += 12
    heavy_themes = sum(
        1
        for value in (
            metrics.anti_example_section_length > 12,
            metrics.benchmark_section_length > 25,
            metrics.optimality_section_length > 35,
            metrics.critical_details_length > 60,
        )
        if value
    )
    if heavy_themes >= 2:
        split += 12
    metrics.split_candidate_score = max(0, min(100, split))


def _classify(metrics: SkillMetrics) -> None:
    kind = metrics.kind
    big_anti = metrics.anti_example_section_length > THRESHOLDS["movable_anti_lines"]
    big_benchmark = metrics.benchmark_section_length > THRESHOLDS["movable_benchmark_lines"]
    big_optimality = metrics.optimality_section_length > THRESHOLDS["movable_optimality_lines"]
    has_oversized_section = len(metrics.oversized_sections) >= 1
    movable = big_anti or big_benchmark or big_optimality or has_oversized_section

    if metrics.professionalism_score < THRESHOLDS["low_professionalism"]:
        metrics.classification = "REWRITE_FOR_PROFESSIONALISM"
        metrics.suggested_action = (
            "Tighten boundaries, concrete standards, and a verifiable quality gate before any move."
        )
        metrics.risk_of_change = "medium"
        metrics.recommended_phase = "P0"
        return

    if kind == "professional-skill":
        over_review = metrics.line_count > THRESHOLDS["professional_review_lines"]
        if metrics.has_shared_optimality and (big_optimality or big_benchmark or big_anti):
            metrics.classification = "MOVE_SECTIONS_TO_REFERENCES"
            metrics.suggested_action = (
                "Move the shared Solution Optimality Self-Check plus oversized anti-example/benchmark "
                "blocks into references/*.md; keep a 3-5 item summary and a Reference Loading pointer."
            )
            metrics.risk_of_change = "low"
            metrics.recommended_phase = "P1"
            return
        if metrics.has_shared_optimality and not movable:
            metrics.classification = "MERGE_DUPLICATE_CONTENT"
            metrics.suggested_action = (
                "Replace the duplicated Solution Optimality boilerplate with a short summary plus "
                "a `solution-optimality-evaluation` capability-reference pointer."
            )
            metrics.risk_of_change = "low"
            metrics.recommended_phase = "P1"
            return
        if movable:
            metrics.classification = "MOVE_SECTIONS_TO_REFERENCES"
            metrics.suggested_action = (
                "Move oversized sections/tables into references/*.md; keep a concise body summary."
            )
            metrics.risk_of_change = "low"
            metrics.recommended_phase = "P2"
            return
        if over_review:
            metrics.classification = "TIGHTEN_BODY"
            metrics.suggested_action = "Trim restating prose; keep the decision-critical lines only."
            metrics.risk_of_change = "low"
            metrics.recommended_phase = "P2"
            return
        metrics.classification = "KEEP_AS_IS"
        metrics.suggested_action = "Within size and professionalism budget; no action required."
        metrics.recommended_phase = "-"
        return

    if kind == "foundation-capability":
        # Capabilities are compiled into professional-skill references already; the
        # levers are tightening the body or splitting into focused capabilities, not
        # adding a nested reference layer.
        over_heavy = metrics.line_count > THRESHOLDS["foundation_heavy_lines"]
        huge_section = any(s["lines"] > 150 for s in metrics.oversized_sections)
        if over_heavy and (len(metrics.oversized_sections) >= 2 or huge_section):
            metrics.classification = "SPLIT_CAPABILITY"
            metrics.suggested_action = (
                "Plan-only: evaluate splitting into focused sub-capabilities (registry + used_by "
                "update) or relocating a deep appendix; verify dev-profile top-level count impact."
            )
            metrics.risk_of_change = "high"
            metrics.recommended_phase = "P3"
            return
        if over_heavy:
            metrics.classification = "TIGHTEN_BODY"
            metrics.suggested_action = (
                "Trim the heaviest section to decision-critical lines; this capability is already a "
                "selectively-loaded reference, so brevity directly reduces compiled-reference weight."
            )
            metrics.risk_of_change = "low"
            metrics.recommended_phase = "P2"
            return
        metrics.classification = "KEEP_AS_IS"
        metrics.suggested_action = "Compact decision aid within budget; no action required."
        metrics.recommended_phase = "-"
        return

    # domain-extension
    over_heavy = metrics.line_count > THRESHOLDS["domain_heavy_lines"]
    if movable or over_heavy:
        metrics.classification = "MOVE_SECTIONS_TO_REFERENCES"
        metrics.suggested_action = (
            "Move the deep benchmark/anti-example/governance appendix into references/*.md; keep the "
            "trigger signals, domain risk model, and quality gate in the body."
        )
        metrics.risk_of_change = "low"
        metrics.recommended_phase = "P2"
        return
    metrics.classification = "KEEP_AS_IS"
    metrics.suggested_action = "Within size and professionalism budget; no action required."
    metrics.recommended_phase = "-"


def audit() -> dict:
    used_by_counts = _load_used_by_counts()
    files = _collect_files()

    parsed: list[tuple[SkillMetrics, list[Section], str]] = []
    line_frequency: dict[str, set[str]] = defaultdict(set)
    optimality_files: set[str] = set()

    for kind, path in files:
        try:
            _metadata, _raw, body = parse_frontmatter(path)
        except ValidationProblem:
            body = path.read_text(encoding="utf-8")
            _metadata = {}
        sections = parse_sections(body)
        metrics = _base_metrics(kind, path, body, used_by_counts)
        description = _metadata.get("description") if isinstance(_metadata, dict) else None
        metrics.description_length = len((description or "").strip())
        metrics.description_findings = _description_findings(description)
        metrics.findings.extend(metrics.description_findings)
        # Only a full inline block (> 20 lines) counts as shared duplication; a short
        # summary that points at a reference is the resolved state, not a defect.
        optimality_section = _find_section_contains(sections, "solution optimality")
        if optimality_section is not None and optimality_section.line_count > 20:
            optimality_files.add(metrics.path)
        for normalized in set(_significant_lines(body)):
            line_frequency[normalized].add(metrics.path)
        parsed.append((metrics, sections, body))

    shared_optimality = len(optimality_files) >= THRESHOLDS["common_phrase_min_files"]
    common_lines = {
        line: files
        for line, files in line_frequency.items()
        if len(files) >= THRESHOLDS["common_phrase_min_files"]
    }

    for metrics, sections, body in parsed:
        repeated = sum(
            1
            for normalized in set(_significant_lines(body))
            if len(common_lines.get(normalized, ())) >= THRESHOLDS["common_phrase_min_files"]
        )
        metrics.repeated_phrase_count = repeated
        metrics.has_shared_optimality = (
            shared_optimality and metrics.path in optimality_files
        )
        _score(metrics, sections, body)
        _classify(metrics)

    all_metrics = [item[0] for item in parsed]
    return {
        "metrics": all_metrics,
        "common_lines": common_lines,
        "optimality_files": sorted(optimality_files),
        "shared_optimality": shared_optimality,
    }


def _summary(metrics: list[SkillMetrics]) -> dict:
    by_kind = defaultdict(list)
    for item in metrics:
        by_kind[item.kind].append(item)

    def heavy(kind: str, gate_key: str) -> int:
        return sum(
            1 for item in by_kind[kind] if item.line_count > THRESHOLDS[gate_key]
        )

    return {
        "professional_skills": len(by_kind["professional-skill"]),
        "foundation_capabilities": len(by_kind["foundation-capability"]),
        "domain_extensions": len(by_kind["domain-extension"]),
        "heavy_professional": heavy("professional-skill", "professional_heavy_lines"),
        "heavy_foundation": heavy("foundation-capability", "foundation_heavy_lines"),
        "heavy_domain": heavy("domain-extension", "domain_heavy_lines"),
        "split_candidates": sum(
            1 for item in metrics if item.split_candidate_score >= THRESHOLDS["split_candidate_high"]
        ),
        "low_professionalism": sum(
            1 for item in metrics if item.professionalism_score < THRESHOLDS["low_professionalism"]
        ),
        "move_to_reference": sum(
            1 for item in metrics if item.classification == "MOVE_SECTIONS_TO_REFERENCES"
        ),
        "classifications": dict(Counter(item.classification for item in metrics)),
    }


def _top(metrics: list[SkillMetrics], key, reverse: bool, limit: int = 10) -> list[SkillMetrics]:
    return sorted(metrics, key=key, reverse=reverse)[:limit]


def _format_md(result: dict) -> str:
    metrics: list[SkillMetrics] = result["metrics"]
    summary = _summary(metrics)
    lines: list[str] = []
    a = lines.append

    a("# ChangeForge Skill Content Audit")
    a("")
    a("> Generated by `scripts/audit-skill-content.py`. Read-only, advisory.")
    a("> Re-run after authoring changes. Scores are heuristic and do not gate the build.")
    a("")

    a("## 1. Executive Summary")
    a("")
    a("| Metric | Value |")
    a("| --- | --- |")
    a(f"| Total professional skills | {summary['professional_skills']} |")
    a(f"| Total foundation capabilities | {summary['foundation_capabilities']} |")
    a(f"| Total domain extensions | {summary['domain_extensions']} |")
    a(
        f"| Heavy professional skills (> {THRESHOLDS['professional_heavy_lines']} lines) "
        f"| {summary['heavy_professional']} |"
    )
    a(
        f"| Heavy foundation capabilities (> {THRESHOLDS['foundation_heavy_lines']} lines) "
        f"| {summary['heavy_foundation']} |"
    )
    a(
        f"| Heavy domain extensions (> {THRESHOLDS['domain_heavy_lines']} lines) "
        f"| {summary['heavy_domain']} |"
    )
    a(f"| Split candidates (score ≥ {THRESHOLDS['split_candidate_high']}) | {summary['split_candidates']} |")
    a(f"| Low-professionalism candidates (< {THRESHOLDS['low_professionalism']}) | {summary['low_professionalism']} |")
    a(f"| Move-to-reference candidates | {summary['move_to_reference']} |")
    a(f"| Shared duplicated lines (≥ {THRESHOLDS['common_phrase_min_files']} files) | {len(result['common_lines'])} |")
    a("")
    a("Suggested-action distribution:")
    a("")
    a("| Classification | Count |")
    a("| --- | --- |")
    for category in (
        "KEEP_AS_IS",
        "TIGHTEN_BODY",
        "MOVE_SECTIONS_TO_REFERENCES",
        "MERGE_DUPLICATE_CONTENT",
        "SPLIT_CAPABILITY",
        "REWRITE_FOR_PROFESSIONALISM",
        "DEFER",
    ):
        a(f"| {category} | {summary['classifications'].get(category, 0)} |")
    a("")

    a("## 2. Top Problems")
    a("")
    a("### 2.1 Worst Context Waste (lowest context efficiency)")
    a("")
    a("| Skill | Kind | Lines | Efficiency | Top finding |")
    a("| --- | --- | --- | --- | --- |")
    for item in _top(metrics, lambda m: (m.context_efficiency_score, -m.line_count), reverse=False):
        finding = item.findings[0] if item.findings else "-"
        a(f"| `{item.name}` | {item.kind} | {item.line_count} | {item.context_efficiency_score} | {finding} |")
    a("")

    a("### 2.2 Lowest Professionalism")
    a("")
    a("| Skill | Kind | Professionalism | Top finding |")
    a("| --- | --- | --- | --- |")
    for item in _top(metrics, lambda m: (m.professionalism_score, m.line_count), reverse=False):
        finding = next((f for f in item.findings if "boundary" in f or "Quality" in f or "specificity" in f), item.findings[0] if item.findings else "-")
        a(f"| `{item.name}` | {item.kind} | {item.professionalism_score} | {finding} |")
    a("")

    a("### 2.3 Weakest Routing Boundaries")
    a("")
    a("| Skill | Kind | Routing clarity | Top finding |")
    a("| --- | --- | --- | --- |")
    for item in _top(metrics, lambda m: (m.routing_clarity_score, m.line_count), reverse=False):
        finding = next((f for f in item.findings if "Do Not" in f or "boundary" in f), "-")
        a(f"| `{item.name}` | {item.kind} | {item.routing_clarity_score} | {finding} |")
    a("")

    a("### 2.4 Strongest Split Candidates")
    a("")
    a("| Skill | Kind | Lines | Split score | Oversized sections |")
    a("| --- | --- | --- | --- | --- |")
    for item in _top(metrics, lambda m: (m.split_candidate_score, m.line_count), reverse=True):
        sections = ", ".join(f"{s['title']} ({s['lines']})" for s in item.oversized_sections) or "-"
        a(f"| `{item.name}` | {item.kind} | {item.line_count} | {item.split_candidate_score} | {sections} |")
    a("")

    a("### 2.5 Description Risk (frontmatter triggers)")
    a("")
    description_risk = [m for m in metrics if m.description_findings]
    if not description_risk:
        a("No frontmatter description risks detected.")
        a("")
    else:
        a("| Skill | Kind | Description chars | Description finding |")
        a("| --- | --- | --- | --- |")
        for item in sorted(description_risk, key=lambda m: m.description_length, reverse=True):
            finding = "; ".join(f.replace("description: ", "") for f in item.description_findings)
            a(f"| `{item.name}` | {item.kind} | {item.description_length} | {finding} |")
        a("")

    a("## 3. Per Skill Findings")
    a("")
    by_kind: dict[str, list[SkillMetrics]] = defaultdict(list)
    for item in metrics:
        by_kind[item.kind].append(item)

    for kind in ("professional-skill", "foundation-capability", "domain-extension"):
        group = sorted(by_kind[kind], key=lambda m: (m.classification != "KEEP_AS_IS", -m.line_count))
        a(f"### 3.{('professional-skill', 'foundation-capability', 'domain-extension').index(kind) + 1} {KIND_LABEL[kind]} ({len(group)})")
        a("")
        a("| Skill | Lines | Words | Prof | Ctx | Route | Split | Classification | Phase | Risk |")
        a("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
        for item in group:
            a(
                f"| `{item.name}` | {item.line_count} | {item.word_count} | "
                f"{item.professionalism_score} | {item.context_efficiency_score} | "
                f"{item.routing_clarity_score} | {item.split_candidate_score} | "
                f"{item.classification} | {item.recommended_phase} | {item.risk_of_change} |"
            )
        a("")
        flagged = [item for item in group if item.classification != "KEEP_AS_IS"]
        if flagged:
            a(f"#### Detailed findings — {KIND_LABEL[kind]}")
            a("")
            for item in flagged:
                a(f"- **`{item.name}`** ({item.classification}, {item.recommended_phase}, risk: {item.risk_of_change})")
                a(f"  - Path: `{item.path}`")
                a(f"  - Suggested action: {item.suggested_action}")
                if item.findings:
                    for finding in item.findings:
                        a(f"  - Finding: {finding}")
            a("")

    a("## 4. Classification Index")
    a("")
    categories = [
        "KEEP_AS_IS",
        "TIGHTEN_BODY",
        "MOVE_SECTIONS_TO_REFERENCES",
        "SPLIT_CAPABILITY",
        "MERGE_DUPLICATE_CONTENT",
        "REWRITE_FOR_PROFESSIONALISM",
        "DEFER",
    ]
    for category in categories:
        members = sorted(
            item.name for item in metrics if item.classification == category
        )
        a(f"- **{category}** ({len(members)}): {', '.join(f'`{name}`' for name in members) if members else '_none_'}")
    a("")

    a("## 5. Shared / Duplicated Content (common-reference candidates)")
    a("")
    a(f"Lines that appear in ≥ {THRESHOLDS['common_phrase_min_files']} skills (top 25 by fan-out):")
    a("")
    a("| Files | Excerpt |")
    a("| --- | --- |")
    common_sorted = sorted(result["common_lines"].items(), key=lambda kv: len(kv[1]), reverse=True)[:25]
    for line, file_set in common_sorted:
        excerpt = line[:90].replace("|", "\\|")
        a(f"| {len(file_set)} | {excerpt} |")
    a("")
    a(
        "> Note: the `Reference Loading Policy` L1-L5 lines and the capability-path examples are "
        "intentionally uniform across all professional skills and are **required** by "
        "`validate-skills.py`. They are a deliberate shared contract, not a dedup defect, and are "
        "excluded from merge recommendations."
    )
    a("")
    if result["shared_optimality"]:
        a(
            f"> The `Solution Optimality Self-Check` block appears in "
            f"{len(result['optimality_files'])} skills and is the primary common-reference candidate."
        )
        a("")

    return "\n".join(lines) + "\n"


def main() -> int:
    result = audit()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    json_payload = {
        "thresholds": THRESHOLDS,
        "summary": _summary(result["metrics"]),
        "skills": [asdict(item) for item in result["metrics"]],
        "common_lines": {
            line: sorted(files) for line, files in result["common_lines"].items()
        },
        "optimality_files": result["optimality_files"],
    }
    JSON_REPORT.write_text(
        json.dumps(json_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    MARKDOWN_REPORT.write_text(_format_md(result), encoding="utf-8")

    summary = json_payload["summary"]
    print(
        "audit-skill-content: wrote "
        f"{MARKDOWN_REPORT.relative_to(ROOT)} and {JSON_REPORT.relative_to(ROOT)} "
        f"({summary['professional_skills']} professional, "
        f"{summary['foundation_capabilities']} foundation, "
        f"{summary['domain_extensions']} domain; "
        f"{summary['move_to_reference']} move-to-reference, "
        f"{summary['split_candidates']} split candidate(s), "
        f"{summary['low_professionalism']} low-professionalism)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
