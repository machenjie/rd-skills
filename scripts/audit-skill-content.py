#!/usr/bin/env python3
"""Audit rd-skills SKILL content for professionalism, redundancy, and split candidates.

This tool NEVER modifies SKILL.md files. Its default mode reads authored content
and writes only the two reports below. It walks the three
Layer 2/3 authoring roots, checks description metadata across all four Skill
layers, computes per-file content metrics, detects cross-file duplicated content,
scores each skill on four advisory dimensions, classifies a suggested action,
and writes two grouped reports:

- reports/skill-content-audit.md  (human-readable, grouped by kind)
- reports/skill-content-audit.json (machine-readable, full metric detail)

Finding a problem does not make the audit fail; it always exits 0 unless an
internal error occurs. Thresholds are centralized in THRESHOLDS below.
"""

from __future__ import annotations

import argparse
import ast
import builtins
import hashlib
import json
import math
import os
import re
import stat
import sys
import tempfile
import unicodedata
from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

import validation_utils as _validation_utils

from validation_utils import (
    AI_COMPLEX_SENTENCE_TARGET_WORDS,
    AI_SENTENCE_HARD_WORDS,
    AI_SENTENCE_TARGET_WORDS,
    CONTENT_BUDGET_CLASSIFICATIONS,
    EXPECTED_FOUNDATION_CAPABILITY_COUNT,
    FOUNDATION_CONTENT_BUDGETS,
    FOUNDATION_CONTENT_CLASSES,
    FOUNDATION_CONTENT_HARD_TOKENS,
    LAYER_ROOT_CONTENT_BUDGET_SCOPE,
    LAYER_ROOT_CONTENT_BUDGETS,
    MARKDOWN_ANY_LIST_ITEM_RE,
    REGISTRY_SCHEMA_VERSIONS,
    ValidationProblem,
    ai_readability_findings,
    count_o200k_base_tokens,
    classify_content_budget,
    foundation_decision_card,
    foundation_content_budget,
    foundation_content_class_errors,
    foundation_registry_field_errors,
    load_yaml_file,
    load_yaml_text,
    parse_frontmatter,
    parse_markdown_logical_list_items,
    read_text_preserve_newlines,
    report_output_paths,
    reference_contracts,
    REFERENCE_CONTRACT_TYPES,
    REFERENCE_CONTRACT_ROLES,
    REFERENCE_LINE_BUDGET_KIND,
    REFERENCE_OUTPUT_TYPES,
    reference_type_for_path,
    frontmatter_body_targeted_reference_projection_line_count,
    registry_targeted_reference_projection_line_count,
    strip_frontmatter_body_targeted_reference_projection,
    strip_registry_targeted_reference_projection,
)


ROOT = Path(__file__).resolve().parents[1]
CONTROL_SKILLS_DIR = ROOT / "src" / "control-skills"
PROFESSIONAL_SKILLS_DIR = ROOT / "src" / "professional-skills"
CAPABILITIES_DIR = ROOT / "src" / "foundation" / "capabilities"
DOMAIN_EXTENSIONS_DIR = ROOT / "src" / "domain-extensions"
CONTROL_REGISTRY = ROOT / "src" / "registry" / "control-skills.yaml"
PROFESSIONAL_REGISTRY = ROOT / "src" / "registry" / "professional-skills.yaml"
CAPABILITIES_REGISTRY = ROOT / "src" / "registry" / "foundation-skills.yaml"
DOMAIN_REGISTRY = ROOT / "src" / "registry" / "domain-skills.yaml"
REPORTS_DIR = ROOT / "reports"
MARKDOWN_REPORT = REPORTS_DIR / "skill-content-audit.md"
JSON_REPORT = REPORTS_DIR / "skill-content-audit.json"
SKILL_CONTENT_EXCEPTIONS_FILE = ROOT / "config" / "skill-content-exceptions.yaml"
SEMANTIC_DISPOSITION_APPLICATION_ERROR_ID = (
    "semantic-decision-application-invalid"
)

REFERENCE_SOURCES = (
    ("control", CONTROL_REGISTRY, "control_skills", CONTROL_SKILLS_DIR),
    ("professional", PROFESSIONAL_REGISTRY, "professional_skills", PROFESSIONAL_SKILLS_DIR),
    ("foundation", CAPABILITIES_REGISTRY, "foundation_skills", CAPABILITIES_DIR),
    ("domain", DOMAIN_REGISTRY, "domain_skills", DOMAIN_EXTENSIONS_DIR),
)
REFERENCE_LAYER_ORDER = {
    layer: index for index, (layer, _registry, _key, _root) in enumerate(REFERENCE_SOURCES)
}

# --- Centralized, configurable thresholds -----------------------------------
THRESHOLDS = {
    # Body length (lines) review target / hard gates per kind.
    "professional_review_lines": 80,
    "professional_heavy_lines": 120,
    "foundation_heavy_lines": 250,
    "domain_heavy_lines": 300,
    # Foundation root budgets are declared by Registry content_class. Targets
    # are advisory; class hard limits and the universal token limit are strict.
    "foundation_compact_target_words": FOUNDATION_CONTENT_BUDGETS["compact"]["target_words"],
    "foundation_compact_hard_words": FOUNDATION_CONTENT_BUDGETS["compact"]["hard_words"],
    "foundation_complex_target_words": FOUNDATION_CONTENT_BUDGETS["complex"]["target_words"],
    "foundation_complex_hard_words": FOUNDATION_CONTENT_BUDGETS["complex"]["hard_words"],
    # The universal hard cap remains independent from the provenance snapshot.
    "foundation_hard_tokens": FOUNDATION_CONTENT_HARD_TOKENS,
    "professional_target_words": LAYER_ROOT_CONTENT_BUDGETS["professional-skill"]["target_words"],
    "professional_hard_words": LAYER_ROOT_CONTENT_BUDGETS["professional-skill"]["hard_words"],
    "professional_target_tokens": LAYER_ROOT_CONTENT_BUDGETS["professional-skill"]["target_tokens"],
    "professional_hard_tokens": LAYER_ROOT_CONTENT_BUDGETS["professional-skill"]["hard_tokens"],
    "domain_target_words": LAYER_ROOT_CONTENT_BUDGETS["domain-extension"]["target_words"],
    "domain_hard_words": LAYER_ROOT_CONTENT_BUDGETS["domain-extension"]["hard_words"],
    "domain_target_tokens": LAYER_ROOT_CONTENT_BUDGETS["domain-extension"]["target_tokens"],
    "domain_hard_tokens": LAYER_ROOT_CONTENT_BUDGETS["domain-extension"]["hard_tokens"],
    "root_tutorial_density_min_words": 450,
    "foundation_rule_min": 3,
    "foundation_rule_max": 8,
    "foundation_rule_sentence_max": 2,
    "foundation_prose_line_words_max": 80,
    "foundation_tutorial_density_warn": 0.22,
    "foundation_decision_density_warn": 1.0,
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
    # Actionability / control-plane signal gates.
    "front_window_lines": 60,
    "weak_front_loaded_action": 60,
    "poor_front_loaded_action": 40,
    "control_boilerplate_density_high": 2.0,
    "generic_control_phrase_high": 2,
    "generic_control_phrase_classification_high": 6,
    "generic_control_phrase_density_count": 4,
    "control_boilerplate_repeated_phrase_high": 3,
}

FOUNDATION_DERIVATION_SNAPSHOT = {
    "date": "2026-08-21",
    "foundation_documents": 150,
    "compact_documents": 128,
    "complex_documents": 22,
    "sum_tokens": 65538,
    "min_tokens": 138,
    "p25_tokens": 276,
    "p50_tokens": 511,
    "p75_tokens": 553,
    "p90_tokens": 598,
    "p95_tokens": 628,
    "p99_tokens": 654,
    "distribution_max_tokens": 663,
    "mean_tokens": 436.92,
    "sum_words": 45983,
    "min_words": 94,
    "p25_words": 182,
    "p50_words": 357,
    "p75_words": 393,
    "p90_words": 419,
    "p95_words": 436,
    "p99_words": 454,
    "max_words": 475,
    "mean_words": 306.553,
    "median_token_word_ratio": 1.414,
    "p90_token_word_ratio": 1.552,
    "p95_token_word_ratio": 1.593,
    "max_token_word_ratio": 1.673,
    "mean_token_word_ratio": 1.435,
}


def _nearest_rank(values: list[int] | list[float], percentile: float) -> int | float:
    ordered = sorted(values)
    return ordered[math.ceil(percentile * len(ordered)) - 1]


def foundation_derivation_snapshot_from_documents(
    documents: list[dict],
) -> dict[str, object]:
    """Recompute the fixed Foundation provenance from validated body rows."""

    expected_count = FOUNDATION_DERIVATION_SNAPSHOT["foundation_documents"]
    if len(documents) != expected_count:
        raise ValidationProblem(
            f"expected {expected_count} Foundation body documents; found {len(documents)}"
        )
    document_ids: list[str] = []
    token_counts: list[int] = []
    word_counts: list[int] = []
    content_classes: list[str] = []
    for index, document in enumerate(documents):
        if not isinstance(document, dict):
            raise ValidationProblem(
                f"Foundation body document[{index}] must be a mapping"
            )
        document_id = document.get("document_id")
        if not isinstance(document_id, str) or not document_id.strip():
            raise ValidationProblem(
                f"Foundation body document[{index}].document_id must be non-blank"
            )
        document_ids.append(document_id)
        content_class = document.get("content_class")
        if content_class not in FOUNDATION_CONTENT_CLASSES:
            raise ValidationProblem(
                f"Foundation body document[{index}].content_class is invalid"
            )
        content_classes.append(str(content_class))
        for field, destination in (
            ("token_count", token_counts),
            ("word_count", word_counts),
        ):
            value = document.get(field)
            if type(value) is not int or value <= 0:
                raise ValidationProblem(
                    f"Foundation body document[{index}].{field} must be a positive integer"
                )
            destination.append(value)
    if len(document_ids) != len(set(document_ids)):
        raise ValidationProblem("Foundation body document_id values must be unique")

    token_word_ratios = [
        token_count / word_count
        for token_count, word_count in zip(
            token_counts,
            word_counts,
            strict=True,
        )
    ]
    return {
        "date": FOUNDATION_DERIVATION_SNAPSHOT["date"],
        "foundation_documents": len(documents),
        "compact_documents": content_classes.count("compact"),
        "complex_documents": content_classes.count("complex"),
        "sum_tokens": sum(token_counts),
        "min_tokens": min(token_counts),
        "p25_tokens": _nearest_rank(token_counts, 0.25),
        "p50_tokens": _nearest_rank(token_counts, 0.50),
        "p75_tokens": _nearest_rank(token_counts, 0.75),
        "p90_tokens": _nearest_rank(token_counts, 0.90),
        "p95_tokens": _nearest_rank(token_counts, 0.95),
        "p99_tokens": _nearest_rank(token_counts, 0.99),
        "distribution_max_tokens": max(token_counts),
        "mean_tokens": round(sum(token_counts) / len(token_counts), 3),
        "sum_words": sum(word_counts),
        "min_words": min(word_counts),
        "p25_words": _nearest_rank(word_counts, 0.25),
        "p50_words": _nearest_rank(word_counts, 0.50),
        "p75_words": _nearest_rank(word_counts, 0.75),
        "p90_words": _nearest_rank(word_counts, 0.90),
        "p95_words": _nearest_rank(word_counts, 0.95),
        "p99_words": _nearest_rank(word_counts, 0.99),
        "max_words": max(word_counts),
        "mean_words": round(sum(word_counts) / len(word_counts), 3),
        "median_token_word_ratio": round(
            _nearest_rank(token_word_ratios, 0.50), 3
        ),
        "p90_token_word_ratio": round(
            _nearest_rank(token_word_ratios, 0.90), 3
        ),
        "p95_token_word_ratio": round(
            _nearest_rank(token_word_ratios, 0.95), 3
        ),
        "max_token_word_ratio": round(max(token_word_ratios), 3),
        "mean_token_word_ratio": round(
            sum(token_word_ratios) / len(token_word_ratios), 3
        ),
    }

# Descriptions are discovery metadata and are therefore closer to always-loaded
# context than a targeted reference. The hard limit is enforced by
# validate-skill-content-size.py; the lower limit remains an authoring advisory.
DESCRIPTION_BUDGETS = {
    "control-skill": {"recommended": 220, "hard": 300},
    "professional-skill": {"recommended": 220, "hard": 300},
    "foundation-capability": {"recommended": 180, "hard": 260},
    "domain-extension": {"recommended": 180, "hard": 260},
}

DESCRIPTION_ROOTS = (
    ("control-skill", CONTROL_SKILLS_DIR),
    ("professional-skill", PROFESSIONAL_SKILLS_DIR),
    ("foundation-capability", CAPABILITIES_DIR),
    ("domain-extension", DOMAIN_EXTENSIONS_DIR),
)

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
# rd-skills descriptions conventionally open with a capability verb that states
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

FRONT_FIRST_MOVE_PATTERNS = (
    r"\bfirst moves?\b",
    r"\bfirst actions?\b",
    r"\bexecution checklist\b",
    r"\bbegin by\b",
    r"\bstart by\b",
    r"\bbefore (?:planning|implementation|editing|action)",
)
FRONT_STOP_CONDITION_PATTERNS = (
    r"\bstop conditions?\b",
    r"\bstop / escalation conditions?\b",
    r"\bblocking conditions?\b",
    r"\bdo not (?:continue|proceed|implement)\b",
    r"\breturn status needs_user_choice\b",
)
FRONT_RATIONALE_PATTERNS = (
    r"\brationalizations?\b",
    r"\banti-rationalization",
    r"\bcritical gotchas?\b",
    r"\bcritical details?\b",
    r"\bcritical risks?\b",
    r"\bhigh-value gotchas?\b",
)

FRONT_VERIFICATION_PATTERNS = (
    r"\bminimal verification\b",
    r"\bminimal validation\b",
    r"\bvalidation commands?\b",
    r"\brun .{0,80}\btests?\b",
    r"\bquality gate\b",
)
DOMAIN_ACTION_VERBS = frozenset({
    "audit", "authorize", "block", "build", "classify", "compare", "compile",
    "dedupe", "detect", "emit", "enforce", "inspect", "install", "map",
    "measure", "merge", "migrate", "move", "package", "parse", "preserve",
    "redact", "reject", "render", "repair", "route", "run", "sanitize",
    "scan", "score", "split", "test", "trace", "uninstall", "validate", "verify",
})
DOMAIN_ACTION_VERB_RE = re.compile(
    r"\b(" + "|".join(sorted(DOMAIN_ACTION_VERBS)) + r")(?:s|ed|ing)?\b",
    re.IGNORECASE,
)
CONTROL_BOILERPLATE_PATTERNS = (
    r"\bruntime prompt flow\b",
    r"\bruntime prompt execution protocol\b",
    r"\bruntime process phases?\b",
    r"\broute/stage manifests?\b",
    r"\bstage manifests?\b",
    r"\bhook telemetry\b",
    r"\bphase_status\b",
    r"\bprocess_facts\b",
    r"\b(?:private|hidden|runtime|persistent|persisted)\b"
    r"(?:\s*[,;:/-]?\s*(?:task-local|internal)\b)?"
    r"\s*[,;:/-]?\s+(?:evidence\s+)?ledgers?\b",
    r"\binternal protocol fields?\b",
    r"\binternal runtime protocol fields?\b",
    r"\bvalidation broker\b",
    r"\bartifact digests?\b",
    r"\bartifact_digest\b",
    r"\bmaintainer-only\b",
    r"\bbenchmark-only\b",
    r"\bphase_artifact\b",
    r"\bprocess_phase_ledger\b",
    r"\bruntime-observed\b",
)
GENERIC_CONTROL_PHRASE_PATTERNS = (
    r"\bdirect use still runs the runtime prompt flow\b",
    r"\bclarify requirements before action\b",
    r"\binspect relevant code/tests/config/docs before planning\b",
    r"\broute/stage manifests when routed\b",
    r"\bruntime process phases are observed evidence\b",
    r"\bnormal agents must not hand-author internal runtime protocol fields\b",
)

# These families describe generic control-plane choreography rather than domain
# decisions. Matches remain section-aware and deliberately narrow: one family
# is only evidence, while a complete prepare/execute/close arc is a high-
# confidence Professional finding.
CONTROL_SCAFFOLD_SECTION_PATTERNS = {
    "confirm-contract": (
        re.compile(
            r"^(?:(?:select|choose)\b.{0,100}\band\s+)?confirm\b.{0,180}"
            r"\b(?:acceptance|allowed scope|scope)\b.{0,100}\bstop conditions?\b",
            re.IGNORECASE,
        ),
        frozenset({"execution checklist", "inputs", "required inputs", "workflow"}),
    ),
    "inspect-owning-source": (
        re.compile(
            r"^inspect\b.{0,160}\b(?:current|owning)\s+source\b",
            re.IGNORECASE,
        ),
        frozenset({"execution checklist", "inputs", "required inputs", "workflow"}),
    ),
    "apply-skill-rules": (
        re.compile(
            r"^(?:apply\s+(?:only\s+)?(?:the\s+)?"
            r"(?:narrow|generic|skill(?:'s|-specific)?)\s+(?:rules?|guidance)\b"
            r"|implement\s+(?:only\s+)?(?:the\s+)?(?:smallest|accepted)\b)",
            re.IGNORECASE,
        ),
        frozenset({"execution checklist", "workflow"}),
    ),
    "post-edit-validation": (
        re.compile(
            r"\brun\b.{0,80}\bpost-edit validation\b",
            re.IGNORECASE,
        ),
        frozenset({"execution checklist", "quality gate", "workflow"}),
    ),
    "generic-handoff": (
        re.compile(
            r"^(?:return|state\s+source evidence)\b",
            re.IGNORECASE,
        ),
        frozenset({"execution checklist", "output contract", "output fragment", "workflow"}),
    ),
}
CONTROL_SCAFFOLD_HANDOFF_MARKER_RE = re.compile(
    r"\b(?:actual\s+diff|evidence|proof limits?|escalation|residual\s+risk|"
    r"next owner|handoff|findings|outcomes|validation)\b",
    re.IGNORECASE,
)
CONTROL_SCAFFOLD_HANDOFF_MIN_MARKERS = 3
CONTROL_SCAFFOLD_PROFILE_RE = re.compile(
    r"\b(main-control-agent|analysis-agent|task-agent|review-agent)\b",
    re.IGNORECASE,
)
CONTROL_SCAFFOLD_PROFILE_MODE_RE = re.compile(
    r"(?:\b(?:main-control-agent|analysis-agent|task-agent|review-agent)\b.{0,80}"
    r"\b(?:mode|profile)\b|\b(?:mode|profile)\b.{0,80}"
    r"\b(?:main-control-agent|analysis-agent|task-agent|review-agent)\b|"
    r"\b(?:main-control-agent|analysis-agent|task-agent|review-agent)\b.{0,60}"
    r"\bowns?\s+(?:this|the)\s+(?:generic\s+)?(?:step|workflow|task)\b)",
    re.IGNORECASE,
)
CONTROL_SCAFFOLD_PROFILE_SECTIONS = frozenset(
    {"execution checklist", "inputs", "required inputs", "role", "skill role", "workflow"}
)

# Exact lines are owned by Foundation authoring governance. Unlike the broader
# Professional families, one exact occurrence is already high confidence.
FOUNDATION_EXACT_CONTROL_SCAFFOLDS = {
    "current task contract": "foundation-inputs",
    "selected primary professional skill": "foundation-inputs",
    "task-local trigger evidence": "foundation-inputs",
    (
        "current task contract; selected primary professional skill; "
        "task-local trigger evidence"
    ): "foundation-inputs",
    (
        "confirm the concrete trigger and the primary professional skill"
    ): "confirm-contract",
    (
        "inspect only the current source, tests, contracts, and targeted references "
        "needed for this decision"
    ): "inspect-owning-source",
    (
        "apply the narrow rules without expanding task scope or taking over ownership"
    ): "apply-skill-rules",
    (
        "return the decision, evidence, proof limits, escalation, and residual risk"
    ): "foundation-return",
    "return the decision to the primary professional skill": "foundation-return",
    "return the result to the primary professional skill": "foundation-return",
    (
        "state source evidence, what the decision proves, what remains unverified, "
        "and the next owner"
    ): "foundation-return",
    (
        "return to the primary professional skill after this decision; do not load "
        "adjacent layer 3 skills speculatively"
    ): "foundation-return",
}
FOUNDATION_GENERIC_RETURN_RE = re.compile(
    r"\breturn\s+(?:the\s+(?:decision|result)|it|"
    r"(?:release|security|operational)\b.{0,100}\b(?:authority|decisions?))"
    r"\b.{0,100}\bto\b",
    re.IGNORECASE,
)
FOUNDATION_GENERIC_INPUT_RE = re.compile(
    r"\btask contract\b.{0,100}\bselected primary professional skill\b",
    re.IGNORECASE,
)
CONTROL_SCAFFOLD_PREPARE_FAMILIES = frozenset(
    {"confirm-contract", "inspect-owning-source"}
)
CONTROL_SCAFFOLD_EXECUTE_FAMILIES = frozenset(
    {"apply-skill-rules", "profile-mode"}
)
CONTROL_SCAFFOLD_CLOSE_FAMILIES = frozenset(
    {"post-edit-validation", "generic-handoff"}
)

HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$")
EMPTY_ATX_HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s*#*\s*$")
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
FENCE_OPENING_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<marker>`{3,}|~{3,})(?P<info>.*)$"
)
LIST_ITEM_RE = re.compile(r"^\s{0,3}(?:[-*+]|\d+[.)])\s+(.+?)\s*$")
LIST_MARKER_RE = re.compile(r"^([-*+]|\d+[.)])\s+")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\([^)]+\)")
TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?[\s:|-]*-[\s:|-]*\|?\s*$")
DECISION_HEADING_RE = re.compile(r"\b(?:gate|checklist|decision)\b", re.IGNORECASE)
DECISION_LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\S")
DECISION_SECTION_GENERIC_TOKENS = frozenset(
    {
        "additional",
        "and",
        "checklist",
        "checklists",
        "continued",
        "continuation",
        "decision",
        "decisions",
        "empty",
        "extra",
        "gate",
        "gates",
        "group",
        "groups",
        "item",
        "items",
        "misc",
        "miscellaneous",
        "more",
        "other",
        "others",
        "part",
        "parts",
        "phase",
        "phases",
        "placeholder",
        "quality",
        "section",
        "sections",
        "subsection",
        "subsections",
        "the",
    }
)
DECISION_SECTION_NUMBER_TOKENS = frozenset(
    {
        "one",
        "two",
        "three",
        "four",
        "five",
        "six",
        "seven",
        "eight",
        "nine",
        "ten",
        "first",
        "second",
        "third",
        "fourth",
        "fifth",
        "sixth",
        "seventh",
        "eighth",
        "ninth",
        "tenth",
    }
)
SEMANTIC_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9`*_])")
SEMANTIC_SENTENCE_ABBREVIATIONS = frozenset(
    {
        "e.g.",
        "i.e.",
        "etc.",
        "vs.",
        "mr.",
        "mrs.",
        "ms.",
        "dr.",
        "prof.",
        "fig.",
        "no.",
    }
)
SEMANTIC_EXAMPLE_HEADING_RE = re.compile(
    r"\b(?:example|examples|sample|samples|template|templates"
    r"|anti[- ]?patterns?|failure[- ]patterns?|rationalizations?)\b",
    re.IGNORECASE,
)
ABSOLUTE_SIGNAL_RE = re.compile(
    r"\b(?:must|mandatory|non[- ]negotiable|always|never|every|all)\b"
    r"|(?<![-/])\bonly\b",
    re.IGNORECASE,
)
ABSOLUTE_CONDITIONAL_RE = re.compile(
    r"\b(?:when|if|unless|under|candidate|candidates|baseline|baselines)\b"
    r"|\baccording\s+to\s+(?:the\s+)?policy\b"
    r"|\bcurrent[-\s]+evidence\b",
    re.IGNORECASE,
)
REFERENCE_SCOPE_ONLY_RE = re.compile(
    r"\b(?:(?:load|use|read)\s+(?:this\s+)?reference\b.*\bonly\b"
    r"|(?:load|use|read)\s+only\b)",
    re.IGNORECASE,
)
ABSOLUTE_QUESTION_RE = re.compile(
    r"^[\s*_`>'\"-]*(?:what|why|how|does|do|did|is|are|can|could|should|would|which)\b"
    r".*(?:\?|:)",
    re.IGNORECASE,
)
ABSOLUTE_ADDITIVE_ONLY_RE = re.compile(r"\bnot\s+only\b", re.IGNORECASE)
ABSOLUTE_SCOPED_ONLY_RE = re.compile(
    r"\bonly\s+(?:for|after|with|on|by|within|during|while|where|when|if"
    r"|unless|until|before|through|from|to|as|at|in)\b",
    re.IGNORECASE,
)
NEGATIVE_OR_PROOF_LIMIT_TABLE_HEADER_RE = re.compile(
    r"\b(?:does\s+not\s+prove|not\s+proven|(?:proof|evidence)\s+limits?"
    r"|reject(?:ed)?\s+(?:when|evidence)|invalid\s+evidence|anti[- ]?patterns?)\b",
    re.IGNORECASE,
)
ABSOLUTE_LITERAL_COMPOUND_RE = re.compile(
    r"\b(?:load-all|all-or-nothing|catch-all|always-on|must-handle|must-wait|never-existed)\b",
    re.IGNORECASE,
)
ABSOLUTE_TABLE_CONTEXT_HEADERS = frozenset(
    {
        "do not load when",
        "load when",
        "use when",
        "avoid when",
        "accept when",
        "reject or route when",
        "reject or downgrade when",
        "reject",
        "rejected shortcut",
        "common false proof",
        "false proof",
        "avoid",
        "do not accept",
        "do not substitute",
        "conflicts with",
        "limit",
        "required limit",
    }
)
ABSOLUTE_CLASSIFICATION_HEADERS = frozenset(
    {"location", "runtime fit", "condition", "allowed actions"}
)
ABSOLUTE_PROOF_VERB_RE = re.compile(r"\b(?:prove|proves|proved|cover|covers|covered|prescribe|prescribes|prescribed)\b", re.IGNORECASE)
ABSOLUTE_NEAR_NEGATION_RE = re.compile(r"\b(?:not|cannot|can't)\b", re.IGNORECASE)
ABSOLUTE_PROOF_CLAUSE_SPLIT_RE = re.compile(
    r"(?:[,;:.!?]+|\b(?:and|but|or|yet|so|however|whereas)\b"
    r"|(?:\s+(?:-{1,2}|[–—])\s+|[–—]))",
    re.IGNORECASE,
)
ABSOLUTE_AUTHORITY_CLAUSE_SPLIT_RE = re.compile(
    r"(?:[;:.!?]+|,\s*(?:and|but|or|yet|so)\b|\b(?:but|however|whereas)\b"
    r"|(?:\s+(?:-{1,2}|[–—])\s+|[–—]))",
    re.IGNORECASE,
)
ABSOLUTE_PROFILE_SUBJECT_RE = re.compile(
    r"\b(?:(?:main[- ]control|analysis|task|review)[- ]agent|this\s+profile|[a-z][a-z0-9_-]*\s+profile)\b",
    re.IGNORECASE,
)
ABSOLUTE_PROFILE_ACTION_RE = re.compile(
    r"\b(?:read|search|inspect|analy[sz]e|edit|write|modify|mutate|execute|run|use|using|dispatch|route|review|load|access)\b",
    re.IGNORECASE,
)
ABSOLUTE_BOUNDARY_AUTHORITY_RE = re.compile(
    r"\b(?:read[- ]only|non[- ]modifying|host[- ]permitted|mutate|fixtures?|reports?|external[- ]state|planned|not_run|not[- ]run)\b",
    re.IGNORECASE,
)
ABSOLUTE_BOUNDARY_ACTION_RE = re.compile(
    r"\b(?:read|search|inspect|refresh|regenerate|edit|write|modify|mutate|execute|run|use|load|access)\b",
    re.IGNORECASE,
)
ABSOLUTE_MAP_DESTINATION_COMPONENT_RE = re.compile(
    r"(?:(?:(?:a|an|the|fresh|current|explicit|named|generated|validation|review|manual|tool-output|local|inspected|not-run|not-verified)\s+){0,4}"
    r"(?:"
    r"(?:evidence|proof|artifacts?|reports?|commands?|sources?|references?)"
    r"(?:/(?:evidence|proof|artifacts?|reports?|commands?|sources?|references?))*"
    r"(?:\s+(?:path|output|result|artifact|report|source|diff|section))?"
    r"|owners?(?:\s+(?:approval|review))?"
    r"|residual(?:\s+[a-z][a-z0-9-]*){0,2}\s+risks?"
    r"))",
    re.IGNORECASE,
)
ABSOLUTE_MAP_DESTINATION_LIST_SPLIT_RE = re.compile(
    r"\s*(?:,\s*(?:(?:and|or)\s+)?|\s+(?:and|or)\s+)\s*",
    re.IGNORECASE,
)
ABSOLUTE_MAP_IN_SCOPE_OBJECT_RE = re.compile(
    r"\b(?:evidence|proof|claim|risk|report|artifact|reference|manifest|owner|validation|check)\b",
    re.IGNORECASE,
)
ABSOLUTE_CLASSIFICATION_GRAMMARS = {
    "location": re.compile(
        r"(?:build(?:/test)?|test|runtime|source|generated|workspace|repository|local|remote)(?:\s+(?:path|stage|only))*",
        re.IGNORECASE,
    ),
    "runtime fit": re.compile(
        r"(?:builder|runtime|build|test|client|server|worker|batch|request|startup|shutdown|host|target)(?:\s+(?:stage|runtime|process|job))?\s+only",
        re.IGNORECASE,
    ),
    "condition": re.compile(
        r"(?:never\s+existed(?:\s+or\s+unavailable)?|(?:always|never)\s+(?:available|unavailable|enabled|disabled|present|absent))",
        re.IGNORECASE,
    ),
    "allowed actions": re.compile(
        r"all\s+available\s+actions",
        re.IGNORECASE,
    ),
}
ABSOLUTE_MAP_REFERENCE_KINDS = frozenset(
    {"decision-checklist", "evidence-pattern", "mode-contract"}
)
SEMANTIC_ABSOLUTE_DOWNGRADE_REASONS = frozenset(
    {
        "same_sentence_conditional_language",
        "reference_loading_scope",
        "scoped_only_restriction",
        "preceding_conditional_language",
        "preceding_reference_loading_scope",
        "negative_or_proof_limit_table_context",
        "question_context",
        "not_only_idiom",
        "lexical_literal_or_compound",
        "exact_table_context_header",
        "clause_local_proof_limit",
        "explicit_profile_agent_authority",
        "boundary_record_authority",
        "map_every_evidence_closure",
        "short_classification_fragment",
    }
)
FIXED_MONEY_RE = re.compile(
    r"(?:[$€£¥]\s*\d[\d,]*(?:\.\d+)?(?:\s*[KMB])?"
    r"|\b\d[\d,]*(?:\.\d+)?\s*(?:USD|EUR|GBP|CNY|RMB|JPY)\b)",
    re.IGNORECASE,
)
FIXED_TIME_RE = re.compile(
    r"\b\d+(?:\.\d+)?(?:\s*|-)\s*(?:ms|milliseconds?|secs?|seconds?|mins?|minutes?"
    r"|hrs?|hours?|days?|weeks?|months?|years?)\b",
    re.IGNORECASE,
)
FIXED_PERCENT_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:%(?!\w)|percent(?:age)?\b)",
    re.IGNORECASE,
)
FIXED_POLICY_VALUE_RE = re.compile(
    r"(?:\b(?:cost|SLO|SLA|threshold|timeout|retention|TTL|budget|limit|ceiling|window)\b"
    r"\s*(?:(?:is|of|to|at|above|below|under|over)\s+|[:=<>]+\s*)?"
    r"\d+(?:[.,]\d+)*"
    r"|\d+(?:[.,]\d+)*\s*(?:(?:is|as)\s+|[:=<>]+\s*)?"
    r"\b(?:cost|SLO|SLA|threshold|timeout|retention|TTL|budget|limit|ceiling|window)\b)",
    re.IGNORECASE,
)
FIXED_MATURITY_COUNT_RE = re.compile(
    r"\b\d+(?:\.\d+)?\+\s*(?:years?|maintainers?|owners?|contributors?)\b",
    re.IGNORECASE,
)
FIXED_OPTION_COUNT_RE = re.compile(
    r"\b\d+\s*[-–—]\s*\d+\s+(?:candidates?|options?|alternatives?)\b",
    re.IGNORECASE,
)
FIXED_ORGANIZATION_WINDOW_RE = re.compile(
    r"\b(?:(?:current|next|this)\s+(?:sprint|quarter)|\d+\s+(?:sprints?|quarters?))\b",
    re.IGNORECASE,
)
FIXED_SCORE_THRESHOLD_RE = re.compile(
    r"\b(?:score|scorecard)\b[^.;\n]{0,40}?"
    r"\b(?:below|under|above|over|at\s+least|at\s+most)?\s*"
    r"\d+(?:\.\d+)?\s*/\s*10\b",
    re.IGNORECASE,
)
FIXED_EXCLUDED_PROSE_RE = re.compile(
    r"\b(?:example|examples|e\.g\.|candidate|candidates|baseline|baselines|benchmark|benchmarks)\b",
    re.IGNORECASE,
)
FIXED_INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
FIXED_THOUSANDS_NUMBER_RE = re.compile(
    r"\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b"
)
FIXED_THOUSANDS_COMMA_SENTINEL = "\ue000"
FIXED_CLAUSE_SPLIT_RE = re.compile(
    r"\s*(?:;|,|\b(?:and|but|while|whereas)\b)\s*",
    re.IGNORECASE,
)
FIXED_DATE_RE = re.compile(
    r"\b(?:19|20)\d{2}[-/]\d{1,2}[-/]\d{1,2}\b"
    r"|(?<![$€£¥])\b(?:19|20)\d{2}\b"
)
FIXED_STANDARD_VERSION_RE = re.compile(
    r"\b(?:RFC|ISO|IEC|IEEE|NIST(?:\s+SP)?|AIP|OWASP|SOC)"
    r"\s*[-:]?\s*[A-Za-z]*\d+(?:[.-]\d+)*\b"
    r"|\bHTTP\s*/\s*\d+(?:\.\d+)*\b"
    r"|\b(?:HTTP|TLS|SSL|ECMAScript|Java|Python|Node(?:\.js)?|C\+\+)\s*v?\d+(?:\.\d+)*\b"
    r"|\bversion\s+v?\d+(?:\.\d+)*\b"
    r"|\bp\d{2,3}\b",
    re.IGNORECASE,
)
FIXED_ALGEBRA_IDENTIFIER_RE = re.compile(
    r"\bN\s*\+\s*1\b|\bPID\s+\d+\b",
    re.IGNORECASE,
)
FIXED_HTTP_STATUS_RE = re.compile(
    r"(?<![$€£¥])\b[1-5]\d{2}\b"
    r"(?!\s*(?:ms|milliseconds?|secs?|seconds?|mins?|minutes?|hrs?|hours?"
    r"|days?|weeks?|months?|years?|%|percent|USD|EUR|GBP|CNY|RMB|JPY)\b)",
    re.IGNORECASE,
)
REFERENCE_PREFACE_RE = re.compile(
    r"^\s*(?:>\s*)?(?:[-*+]\s+)?(?:\*\*|__)?"
    r"(?:reference\s+type|load\s+when|do\s+not\s+load\s+when|required\s+by|required\s+output)"
    r"(?:(?:\*\*|__))?\s*:",
    re.IGNORECASE,
)
AUDIT_SCHEMA_VERSION = 10
AUDIT_GATE_STATUS_SCHEMA_VERSION = 1
AUDIT_GATES = ("authoring", "formal-release")
AI_READABILITY_SCHEMA_VERSION = 2
SURFACE_VALIDATION_SCHEMA_VERSION = 1
REFERENCE_CONTENT_SCHEMA_VERSION = 5
REFERENCE_CONTENT_SURFACES = ("control", "professional", "foundation", "domain")
SKILL_DETECTOR_SCHEMA_VERSION = 3
SKILL_DETECTOR_KIND = "changeforge.skill-content-detector"
SKILL_DETECTOR_REQUIRED_SKILL_FIELDS = (
    "actionability_applicable",
    "actionability_findings",
    "actionability_model",
    "actionable_repeated_phrase_count",
    "classification",
    "control_boilerplate_density",
    "control_scaffold_families",
    "control_scaffold_findings",
    "description_findings",
    "front_loaded_action_score",
    "generic_control_phrase_count",
    "governed_line_count",
    "high_confidence_control_scaffold",
    "kind",
    "line_count",
    "name",
    "projection_overhead_lines",
    "review_reasons",
    "review_state",
    "split_candidate_score",
)
SKILL_DETECTOR_FINDING_FIELDS = (
    "family",
    "section",
    "line",
    "text",
    "match",
)
REVIEW_STATE_PRIORITY = (
    "BLOCK",
    "TIGHTEN_BODY",
    "REVIEW_READABILITY",
    "REVIEW_CONTEXT",
    "KEEP_WITH_ADVISORY",
    "KEEP",
)
REVIEW_REASON_PRIORITY = (
    "classification_block",
    "ai_readability_hard_fail",
    "ai_readability_compound_bullet",
    "classification_tighten_body",
    "ai_readability_tighten",
    "ai_readability_review_as_complex",
    "classification_review_density",
    "professional_governed_lines_over_80",
    "professional_projection_pushes_physical_lines_over_80",
    "weak_front_loaded_action",
    "control_boilerplate_risk",
    "actionable_duplicate_content",
    "description_authoring_advisory",
    "split_candidate",
)
REVIEW_REASON_STATES = {
    "classification_block": "BLOCK",
    "ai_readability_hard_fail": "BLOCK",
    "ai_readability_compound_bullet": "BLOCK",
    "classification_tighten_body": "TIGHTEN_BODY",
    "ai_readability_tighten": "REVIEW_READABILITY",
    "ai_readability_review_as_complex": "REVIEW_READABILITY",
    "classification_review_density": "REVIEW_CONTEXT",
    "professional_governed_lines_over_80": "REVIEW_CONTEXT",
    "professional_projection_pushes_physical_lines_over_80": "REVIEW_CONTEXT",
    "weak_front_loaded_action": "KEEP_WITH_ADVISORY",
    "control_boilerplate_risk": "KEEP_WITH_ADVISORY",
    "actionable_duplicate_content": "KEEP_WITH_ADVISORY",
    "description_authoring_advisory": "KEEP_WITH_ADVISORY",
    "split_candidate": "KEEP_WITH_ADVISORY",
}
PREFACE_SOURCE_PRECEDENCE = ("local", "reference-index", "parent-root")
PREFACE_FIELDS = (
    "reference_type",
    "load_when",
    "do_not_load_when",
    "required_by",
    "required_output",
)
PREFACE_HEADING_ALIASES = {
    "reference_type": {"reference type"},
    "load_when": {"load when", "load trigger", "when to load", "use when"},
    "do_not_load_when": {
        "do not load",
        "do not load when",
        "when not to load",
        "skip when",
    },
    "required_by": {"required by", "required consumer", "required consumers"},
    "required_output": {"required output", "required outputs"},
}
GENERIC_PREFACE_TEXT_RE = re.compile(
    r"^(?:read|load|use)?\s*(?:this\s+)?(?:reference\s+)?"
    r"(?:only\s+)?(?:when|if)?\s*(?:its\s+)?subject\s+changes\s+"
    r"(?:the\s+)?current\s+decision[.!]?$"
    r"|^(?:when|if)\s+(?:needed|required|relevant|applicable)[.!]?$"
    r"|^as\s+needed[.!]?$",
    re.IGNORECASE,
)
MARKDOWN_LINK_TARGET_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
DUPLICATE_DECISION_HEADING_RE = re.compile(
    r"\b(?:decision|gate|checklist|rule|contract|permission|handoff|closure"
    r"|evidence|validation|output|proof|risk)\b",
    re.IGNORECASE,
)
TEMPLATE_SECTION_HEADING_RE = re.compile(
    r"\b(?:tool\s+permission|handoff|closure|evidence|output)\b",
    re.IGNORECASE,
)
YAML_FENCE_START_RE = re.compile(r"^\s*(```+|~~~+)\s*(?:yaml|yml)\s*$", re.IGNORECASE)
YAML_KEY_RE = re.compile(r"^(\s*)(?:-\s+)?([A-Za-z_][A-Za-z0-9_-]*)\s*:")
SCHEMA_FIELD_RE = re.compile(
    r"^\s*(?:[-*+]\s+|\d+[.)]\s+)(?:\*\*|`)?"
    r"([A-Za-z][A-Za-z0-9 _/-]{1,60})(?:\*\*|`)?\s*:",
)
EXACT_DUPLICATE_MIN_LINES = 3
EXACT_DUPLICATE_MIN_TOKENS = 36
TEMPLATE_YAML_MIN_FIELDS = 6
TEMPLATE_OUTPUT_MIN_FIELDS = 4
SEMANTIC_ADVISORY_SCHEMA_VERSION = 7
SEMANTIC_DISPOSITION_SCHEMA_VERSION = 2
SEMANTIC_DISPOSITION_FIELDS = (
    "candidate_id",
    "finding",
    "path",
    "fingerprint",
    "skill_owner",
    "priority",
    "disposition",
    "reason",
    "authority_or_condition",
    "decision_owner",
    "evidence",
    "mitigation",
    "review_after",
)
SEMANTIC_DISPOSITIONS = frozenset(
    {
        "rewrite",
        "valid-contextual-rule",
        "false-positive",
        "time-bounded-exception",
    }
)
SEMANTIC_RESOLVED_DISPOSITIONS = frozenset(
    {"valid-contextual-rule", "false-positive", "time-bounded-exception"}
)
SEMANTIC_PRIORITIES = frozenset({"P0", "P1", "P2"})
SEMANTIC_DEFAULT_PRIORITIES = {
    "unconditional_absolute_candidate": "P1",
    "fixed_number_candidate": "P1",
    "exact_normalized_duplicate_block": "P2",
    "templated_block_candidate": "P1",
}
SEMANTIC_EXCEPTION_GENERIC_VALUES = {
    "approved",
    "exception",
    "false positive",
    "known issue",
    "needed",
    "none",
    "n/a",
    "temporary",
    "tbd",
}
SEMANTIC_EXCEPTION_GENERIC_TOKENS = {
    "a",
    "accepted",
    "an",
    "approved",
    "by",
    "exception",
    "false",
    "for",
    "is",
    "issue",
    "known",
    "later",
    "maintainer",
    "needed",
    "needs",
    "now",
    "owner",
    "positive",
    "required",
    "risk",
    "team",
    "temporary",
    "temporarily",
    "the",
    "this",
    "waiver",
}
SEMANTIC_DISPOSITION_WILDCARD_RE = re.compile(r"[*?\[\]{}!]")
_USE_CONFIG_DISPOSITIONS = object()
SEMANTIC_FINDINGS = (
    "unconditional_absolute_candidate",
    "fixed_number_candidate",
    "exact_normalized_duplicate_block",
    "templated_block_candidate",
)
SEMANTIC_GROUP_FINDINGS = frozenset(
    {"exact_normalized_duplicate_block", "templated_block_candidate"}
)

# Root content has a different risk model from selectively loaded References.
# These families deliberately focus on policy/mechanism leakage and handbook
# density; Reference duplication/preface rules are not reused here.
ROOT_CONTENT_SCHEMA_VERSION = 9
ROOT_SEMANTIC_SCHEMA_VERSION = 6
ROOT_SEMANTIC_DISPOSITION_SCHEMA_VERSION = 7

def _effective_evaluation_date(evaluation_date: date | None = None) -> date:
    """Resolve one non-future date for a complete public invocation."""

    current_date = date.today()
    if evaluation_date is None:
        return current_date
    if type(evaluation_date) is not date or evaluation_date > current_date:
        raise ValueError("evaluation_date must be non-future")
    return evaluation_date


ROOT_SEMANTIC_FINDINGS = (
    "unconditional_mechanism_candidate",
    "fixed_duration_threshold_status_candidate",
    "fixed_vendor_tool_candidate",
    "mandatory_artifact_candidate",
    "tutorial_explanatory_density_candidate",
    "long_root_example_candidate",
    "context_free_organization_policy_candidate",
)
ROOT_SEMANTIC_DEFAULT_PRIORITIES = {
    "unconditional_mechanism_candidate": "P1",
    "fixed_duration_threshold_status_candidate": "P1",
    "fixed_vendor_tool_candidate": "P1",
    "mandatory_artifact_candidate": "P1",
    "tutorial_explanatory_density_candidate": "P1",
    "long_root_example_candidate": "P1",
    "context_free_organization_policy_candidate": "P0",
}
ROOT_SEMANTIC_DISPOSITION_KEY = "root_semantic_dispositions"
ROOT_SEMANTIC_DISPOSITION_FIELDS = (
    "candidate_id",
    "finding",
    "path",
    "document_part",
    "fingerprint",
    "skill_owner",
    "priority",
    "disposition",
    "reason",
    "authority_or_condition",
    "decision_owner",
    "evidence",
    "mitigation",
    "review_after",
)
ROOT_SEMANTIC_EVIDENCE_FIELDS = frozenset(
    {"occurrence_fingerprint", "context_fingerprint", "rationale"}
)

ROOT_CONTENT_SURFACES = (
    "control",
    "professional",
    "foundation",
    "domain",
    "description",
)
ROOT_LAYER_SURFACES = {
    "control-prompt": "control",
    "control-skill": "control",
    "professional-skill": "professional",
    "foundation-capability": "foundation",
    "domain-extension": "domain",
}
ROOT_AGENT_DOCUMENTS = (
    ("control-prompt", ROOT / "src/control-prompts/main-control-agent.md"),
)
AGENT_PROFILES_FILE = ROOT / "src" / "agent-profiles" / "role-agents.json"
ROOT_UNCONDITIONAL_RE = re.compile(
    r"\b(?:must|require|requires|required|mandatory|always|never|all|each|any|"
    r"every|exactly|non[- ]negotiable)\b",
    re.IGNORECASE,
)
ROOT_CONTEXT_AUTHORITY_RE = re.compile(
    r"\b(?:when|if|unless|where|for the current|from (?:the )?(?:current )?"
    r"(?:policy|contract|evidence|source)|according to|as required by|derived from|"
    r"risk[- ]based|task[- ]local|host[- ]provided|user[- ]owned)\b",
    re.IGNORECASE,
)
ROOT_DERIVED_VALUE_AUTHORITY_RE = re.compile(
    r"\b(?:derived from|according to|as required by|set by|defined by|calibrated from|"
    r"observed distribution|current (?:policy|SLO|SLA|contract|evidence|baseline)|"
    r"task[- ]specific|risk[- ]based)\b",
    re.IGNORECASE,
)
ROOT_MECHANISM_RE = re.compile(
    r"\b(?:workflow|process|phase|stage|step|sequence|loop|table|matrix|checklist|"
    r"template|artifact|document|report|ticket|approval|escalat(?:e|ion)|review|"
    r"reproduction|hypothes(?:is|es)|criteri(?:on|a)|evidence|proof|tests?|test plans?|"
    r"test suites?|benchmarks?|fixtures?|dashboards?|diagrams?|status code|command|"
    r"tool|vendor|retry|timeout|coverage|meeting|handoff|load|read|preload|reference|"
    r"catalog|index|directory)\b",
    re.IGNORECASE,
)
ROOT_STRONG_NORMATIVE_RE = re.compile(
    r"\b(?:must|require|requires|mandatory|always|never|"
    r"non[- ]negotiable)\b",
    re.IGNORECASE,
)
ROOT_IMPERATIVE_MECHANISM_RE = re.compile(
    r"^\s*(?:(?:\*\*|__)[^\n]+?(?:\*\*|__)\s*)?"
    r"(?:for\s+(?:all|each|any|every)\b[^,;:]{0,120},\s*)?"
    r"(?:apply|assign|bind|check|choose|classify|create|define|derive|document|"
    r"establish|give|identify|inspect|keep|load|map|maintain|measure|preload|"
    r"produce|prove|read|record|reject|report|review|select|show|test|tie|trace|"
    r"validate|verify|write)(?=\s|[,;:.]|$)",
    re.IGNORECASE,
)
ROOT_THRESHOLD_RE = re.compile(
    r"\b(?:at least|at most|more than|fewer than|less than|exactly|"
    r"no more than)\s+(?:one|two|three|four|five|six|seven|eight|nine|ten|\d+)\b"
    r"|\b(?:one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+or\s+more\b"
    r"|\b\d+(?:\.\d+)?\s*/\s*\d+(?:\.\d+)?\b",
    re.IGNORECASE,
)
ROOT_NUMBER_VALUE = (
    r"(?:\d+(?:\.\d+)?\+?|zero|one|two|three|four|five|six|seven|eight|nine|"
    r"ten|eleven|twelve|once|twice|thrice)"
)
ROOT_DURATION_RE = re.compile(
    rf"\b(?:the\s+)?first\s+(?:milliseconds?|seconds?|minutes?|hours?|days?|weeks?|"
    rf"months?|years?)\b|(?<!\w){ROOT_NUMBER_VALUE}(?:\s*[-–—]\s*{ROOT_NUMBER_VALUE})?"
    rf"\s*(?:ms|milliseconds?|secs?|seconds?|mins?|minutes?|hrs?|hours?|days?|weeks?|"
    rf"months?|years?)\b",
    re.IGNORECASE,
)
ROOT_COUNT_RE = re.compile(
    rf"(?<!\w){ROOT_NUMBER_VALUE}(?:\s+or\s+more)?(?!\w)"
    rf"(?:\s+[A-Za-z][A-Za-z-]*){{0,2}}\s+\b(?:times?|attempts?|retries|routes?|"
    rf"tasks?|functions?|reviews?|approvals?|tests?|hypotheses|steps?|phases?|"
    rf"failures?|passes|dimensions?)\b"
    rf"|\b(?:retry|retries|attempt|attempts|repeat|repeats)\b\s*[:=]?\s*"
    rf"(?<!\w){ROOT_NUMBER_VALUE}(?!\w)"
    rf"|\b(?:route|routed|repeat|repeated|retry|retried|attempt|attempted)\b"
    rf"[^.;:!?]{{0,24}}\b(?:once|twice|thrice)\b"
    rf"|\bone[- ]time\b[^.;:!?]{{0,24}}\b(?:routing|review|load|read|retry)\b"
    rf"|\b(?:assign|give|select|choose|route)\b[^.;:!?]{{0,36}}\bone\s+primary\s+"
    rf"(?:Professional\s+)?Skill\b",
    re.IGNORECASE,
)
ROOT_COUNT_IDENTIFIER_RE = re.compile(
    r"\b(?:Layer|EIP|ERC|BIP|CVE|RFC|ISO|SOC|NIST|P)\s*[-/]?\s*\d+(?:\.\d+)*\b",
    re.IGNORECASE,
)
ROOT_HTTP_STATUS_CONTEXT_RE = re.compile(
    r"\b(?:HTTP\s+)?[1-5]\d{2}\b.{0,36}\b(?:status|response|respond|return|code)\b"
    r"|\b(?:status|response|respond|return|code)\b.{0,36}\b(?:HTTP\s+)?[1-5]\d{2}\b",
    re.IGNORECASE,
)
ROOT_VENDOR_TOOL_LEXICON_SOURCE = (
    "Case-preserving product and command names observed in the four authored root "
    "layers as of 2026-07-14; generic capitalized assignments are also detected."
)
ROOT_VENDOR_TOOL_TERMS = (
    "AWS", "Azure", "GCP", "GitHub", "GitLab", "Jira", "Linear", "Confluence",
    "Datadog", "Prometheus", "Grafana", "Sentry", "Splunk", "Redis", "Kafka",
    "PostgreSQL", "MySQL", "MongoDB", "Terraform", "Kubernetes", "Docker",
    "pytest", "JUnit", "Maven", "Gradle", "npm", "yarn", "pnpm", "curl", "git",
)
ROOT_VENDOR_TOOL_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(item) for item in ROOT_VENDOR_TOOL_TERMS) + r")\b",
    re.IGNORECASE,
)
ROOT_GENERIC_VENDOR_ASSIGNMENT_RE = re.compile(
    r"\b(?:use|choose|select|standardize\s+on|install|run|execute|invoke)\s+"
    r"(?P<name>[A-Z][A-Za-z0-9.+-]{2,})\s+(?:for|as)\s+"
    r"(?:issue\s+tracking|ticketing|monitoring|observability|logging|builds?|tests?|"
    r"deployment|storage|database|messaging|queues?|caching|CI|CD)\b"
)
ROOT_PRESCRIPTIVE_TOOL_RE = re.compile(
    r"\b(?:must|require|requires|required|mandatory|always|never|use|using|run|execute|invoke|"
    r"install|select|choose|emit|return)\b",
    re.IGNORECASE,
)
ROOT_OWNED_VENDOR_SCOPE_RE = re.compile(
    r"(?:\buse\b[^.;:!?]{0,160}\bwhen\b|\bskip\b[^.;:!?]{0,160})",
    re.IGNORECASE,
)
ROOT_MANDATORY_ARTIFACT_SOURCE = (
    r"regression\s+tests?|test\s+plans?|test\s+suites?|tests?|benchmarks?|"
    r"fixtures?|dashboards?|diagrams?|tables?|matrices|checklists?|templates?|"
    r"artifacts?|documents?|reports?|tickets?|ADRs?|worksheets?|ledgers?|logs?|"
    r"records?|runbooks?|playbooks?|scorecards?"
)
ROOT_MANDATORY_ARTIFACT_RE = re.compile(
    rf"\b(?:{ROOT_MANDATORY_ARTIFACT_SOURCE})\b",
    re.IGNORECASE,
)
ROOT_ARTIFACT_DIRECTIVE_RE = re.compile(
    r"\b(?:add|create|write|maintain|record|require|requires|produce|"
    r"generate|submit|keep|archive|retain)\b",
    re.IGNORECASE,
)
ROOT_DATABASE_ARTIFACT_RE = re.compile(
    r"\b(?:database|relational|SQL|schema|warehouse|analytical|analytics|data)\s+table\b",
    re.IGNORECASE,
)
ROOT_ARTIFACT_OBJECT_BOUNDARY_RE = re.compile(
    r"[.;:!?]|\b(?:but|for|from|to|against|with|of|by|into|as|before|after|"
    r"when|if|unless|where|that)\b",
    re.IGNORECASE,
)
ROOT_ARTIFACT_PASSIVE_REQUIRED_RE = re.compile(
    rf"\b(?P<artifact>{ROOT_MANDATORY_ARTIFACT_SOURCE})\b"
    r"[^.;:!?]{0,40}\b(?:is|are)\s+(?:always\s+)?required\b",
    re.IGNORECASE,
)
ROOT_ARTIFACT_MUST_HAVE_RE = re.compile(
    rf"\b(?:must|always)\s+have\s+(?!no\b)[^.;:!?]*?"
    rf"\b(?P<artifact>{ROOT_MANDATORY_ARTIFACT_SOURCE})\b",
    re.IGNORECASE,
)
ROOT_ARTIFACT_ACCOMPANY_RE = re.compile(
    rf"\b(?P<artifact>{ROOT_MANDATORY_ARTIFACT_SOURCE})\b"
    r"[^.;:!?]{0,40}\b(?:must|always)\s+(?:accompany|go\s+with)\b",
    re.IGNORECASE,
)
ROOT_EXISTING_ARTIFACT_LIFECYCLE_RE = re.compile(
    r"\b(?:existing|affected|generated|immutable|promoted|registry)\s+artifacts?\b"
    r"|\bartifact[- ](?:identity|lifecycle|cleanup|provenance|lineage|promotion)\b",
    re.IGNORECASE,
)
ROOT_ORGANIZATION_ROLE_SOURCE = (
    r"team\s+lead|manager|director|VP|on[- ]call|incident\s+commander|CAB|"
    r"change\s+advisory\s+board"
)
ROOT_ORGANIZATION_ROLE_RE = re.compile(
    rf"\b(?:{ROOT_ORGANIZATION_ROLE_SOURCE})\b", re.IGNORECASE
)
ROOT_TECHNICAL_MANAGER_RE = re.compile(
    r"\b(?:package|dependency|connection|memory|window|process|resource|service|state|"
    r"cluster|transaction|session|job|task|file|cache|database|network)-manager\b",
    re.IGNORECASE,
)
ROOT_ORGANIZATION_AUTHORITY_RE = re.compile(
    rf"(?:\b(?:escalate|hand\s+off|route|submit|refer|send|notify)\b"
    rf"[^.;:!?]{{0,48}}\bto\s+(?:(?:the\s+)?(?:{ROOT_ORGANIZATION_ROLE_SOURCE})\b"
    rf"|whoever\s+is\s+on[- ]call\b)"
    rf"|\bnotify\b[^.;:!?]{{0,32}}\b(?:the\s+)?"
    rf"(?:{ROOT_ORGANIZATION_ROLE_SOURCE})\b"
    rf"|\b(?:require|requires|required|obtain|seek)\b[^.;:!?]{{0,24}}"
    rf"\b(?:approval|authorization|sign[- ]off)\b[^.;:!?]{{0,16}}"
    rf"\b(?:from|by)\s+(?:the\s+)?(?:{ROOT_ORGANIZATION_ROLE_SOURCE})\b"
    rf"|\bwithout\s+(?:the\s+)?(?:{ROOT_ORGANIZATION_ROLE_SOURCE})\s+"
    rf"(?:approval|authorization|sign[- ]off)\b"
    rf"|\b(?:{ROOT_ORGANIZATION_ROLE_SOURCE})\b\s+(?:must\s+)?"
    rf"(?:approve|authorize|decide|own|sign[- ]off)\b)",
    re.IGNORECASE,
)
ROOT_EXPLANATORY_MARKER_RE = re.compile(
    r"\b(?:is defined as|means that|in other words|for example|for instance|"
    r"the reason|this is because|why (?:this|the)|note that|remember that|"
    r"in general|typically|generally|fundamentally|these are|so that|because|"
    r"this is (?:a|an|the))\b",
    re.IGNORECASE,
)
ROOT_REFINEMENT_INTRO_RE = re.compile(
    r"\b(?:apply|use|follow)\s+(?:these|the following)\s+"
    r"(?:refinements?|examples?|definitions?)\b|\brefinements?\s*:",
    re.IGNORECASE,
)
ROOT_TEACHING_EXAMPLE_RE = re.compile(
    r"\b(?:for example|for instance|e\.g\.)\b|(?:→|(?<!-)\-\>)",
    re.IGNORECASE,
)
ROOT_TEACHING_DEFINITION_RE = re.compile(
    r"\b(?:is defined as|means that|means|refers to|in other words|that is)\b",
    re.IGNORECASE,
)
ROOT_TEACHING_CONTRAST_RE = re.compile(
    r"\b(?:instead of|rather than)\b", re.IGNORECASE
)
ROOT_DECISION_RULE_HEADING_RE = re.compile(
    r"^high[- ]value rules?$", re.IGNORECASE
)
ROOT_TUTORIAL_HEADINGS = frozenset({"introduction", "overview", "definitions"})
ROOT_TUTORIAL_HEADING_RE = re.compile(
    r"^(?:introduction|overview|definitions)(?:\s+(?:to|of|for)\b.+)?$",
    re.IGNORECASE,
)
ROOT_LONG_EXAMPLE_HEADING_RE = re.compile(
    r"\b(?:example|examples|sample|samples|walkthrough|worked case|template)\b",
    re.IGNORECASE,
)
ROOT_LONG_EXAMPLE_LINES = 12
ROOT_CLAUSE_SPLIT_RE = re.compile(
    r"(?:[;:]|\s+[–—]\s+|,\s*(?:and|but|or|yet|so)\b|"
    r"\b(?:but|however|whereas)\b|\band\b(?=\s+(?:always|never|all|each|any|every|"
    r"must|require|requires|required)\b))",
    re.IGNORECASE,
)
ROOT_PARENT_CONDITION_RE = re.compile(
    r"^\s*(?:(?:read|load|use)\b.+?\bonly\s+when\b|load\s+when\b|"
    r"skip\s+when\b)",
    re.IGNORECASE,
)
ROOT_COORDINATING_SEPARATOR_RE = re.compile(r"\b(?:and|or)\b", re.IGNORECASE)
ROOT_CONTEXT_INHERITANCE_BREAK_RE = re.compile(
    r"\b(?:regardless|unconditionally|independently)\b", re.IGNORECASE
)
ROOT_ROUTING_SELECTOR_HEADINGS = frozenset({"registry trigger", "do not use"})
ROOT_ROUTING_SELECTOR_SPAN_RE = re.compile(
    r"\b\d+\+\s+tasks?\b[^.;,]{0,48}\b(?:need|needs|require|requires)\b"
    r"[^.;,]{0,32}\b(?:analysis|coordination|plan|planning)\b"
    r"|\bone\s+(?:Direct\s+)?Task\b[^.;,]{0,48}\b(?:already\s+owns|owns)\b"
    r"|\bskip\s+one\s+(?:Direct\s+)?Task\b",
    re.IGNORECASE,
)
ROOT_FEASIBLE_SET_COMPARISON_RE = re.compile(
    r"\b(?:more\s+than\s+one|two\s+or\s+more|at\s+least\s+one)\b"
    r"[^.;:!?]{0,80}\b(?:candidate|option|alternative|runtime)s?\b"
    r"[^.;:!?]{0,80}\b(?:feasible|viable|comparable|differ|remain|reject)\b"
    r"|\b(?:candidate|option|alternative|runtime)s?\b[^.;:!?]{0,80}"
    r"\b(?:more\s+than\s+one|two\s+or\s+more|at\s+least\s+one)\b"
    r"|\bat\s+least\s+one\b[^.;:!?]{0,80}\balternative\b",
    re.IGNORECASE,
)
ROOT_ANTI_MANDATE_NUMBER_RE = re.compile(
    r"\bonly\s+one\s+(?:candidate|option|alternative)\b|"
    r"\b(?:candidate|option|alternative)\b[^.;:!?]{0,36}\bnot\s+(?:a\s+)?(?:mandate|required)\b",
    re.IGNORECASE,
)
ROOT_SYNTACTIC_SINGULAR_RE = re.compile(
    r"\b(?:for|within|per)\s+one\b|\bone\s+(?:isolated\s+)?(?:subagent|test|task|"
    r"use\s+case|interaction\s+state|boundary)\b[^.;:!?]{0,48}"
    r"\b(?:can|cannot|already|instead|return|prepare|contaminate|within)\b|"
    r"\bone\b[^.;:!?]{0,24}\bper\s+(?:ordinary\s+)?(?:task|review|boundary)\b",
    re.IGNORECASE,
)
ROOT_EXACT_TARGETED_LINK_RE = re.compile(
    r"^\s*(?:read|load|use)\s+\[[^\]]+\]\([^)]+\)\s+only\s+when\s+\S.+[.!]?\s*$",
    re.IGNORECASE,
)
ROOT_EXACT_NO_REFERENCE_RE = re.compile(
    r"^\s*No\s+separate\s+Reference\s+is\s+indexed[.!]?\s*$",
    re.IGNORECASE,
)
ROOT_QUOTED_OR_BACKTICK_RE = re.compile(
    r'"[^"\n]+"|\'[^\'\n]+\'|`[^`\n]+`'
)
ROOT_QUOTED_FAILURE_EXAMPLE_RE = re.compile(
    r"(?:\"[^\"\n]+\"|'[^'\n]+'|`[^`\n]+`)\s+"
    r"(?:is|are|would\s+be|represents?)\s+(?:an?\s+)?"
    r"(?:over[- ]prescriptive\s+|invalid\s+|forbidden\s+)?"
    r"(?:anti[- ]?pattern|failure(?:\s+example)?|bad\s+example)\b",
    re.IGNORECASE,
)
ROOT_NEGATED_REQUIREMENT_SPAN_RE = re.compile(
    r"\b(?:(?:do|does|did)\s+not|never)\s+requir(?:e|es|ed|ing)\b[^.;:!?]*"
    r"|\b(?:rather\s+than|instead\s+of|without)\s+requir(?:e|es|ed|ing)\b"
    r"[^.;:!?]*"
    r"|\bno\s+[^.;:!?]{0,80}\b(?:is|are)\s+required\b[^.;:!?]*"
    r"|\b[^.;:!?]{0,80}\b(?:is|are)\s+not\s+required\b[^.;:!?]*",
    re.IGNORECASE,
)
ROOT_ANTI_PATTERN_CONTRAST_SPAN_RE = re.compile(
    r"\b(?:rather\s+than|instead\s+of)\b[^.;:!?]*", re.IGNORECASE
)
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
    "foundation-capability": 2,
    "domain-extension": 2,
}

KIND_LABEL = {
    "professional-skill": "Professional Skills",
    "foundation-capability": "Foundation Skills",
    "domain-extension": "Domain Skills",
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
    content_class: str | None = None
    content_class_rationale: str | None = None
    content_target_words: int | None = None
    content_hard_words: int | None = None
    content_target_tokens: int | None = None
    content_hard_tokens: int | None = None
    content_budget_scope: str | None = None
    over_content_target_words: bool = False
    over_content_hard_words: bool = False
    over_content_target_tokens: bool = False
    over_content_hard_tokens: bool = False
    over_content_target: bool = False
    over_content_hard: bool = False
    line_count: int = 0
    governed_line_count: int = 0
    projection_overhead_lines: int = 0
    word_count: int = 0
    token_count: int = 0
    heading_count: int = 0
    table_count: int = 0
    largest_table_rows: int = 0
    code_block_count: int = 0
    bullet_count: int = 0
    reference_link_count: int = 0
    repeated_phrase_count: int = 0
    actionable_repeated_phrase_count: int = 0
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
    front_loaded_action_score: int = 100
    control_boilerplate_density: float = 0.0
    generic_control_phrase_count: int = 0
    control_scaffold_families: list[str] = field(default_factory=list)
    control_scaffold_findings: list[dict] = field(default_factory=list)
    high_confidence_control_scaffold: bool = False
    actionability_model: str = ""
    actionability_applicable: bool = False
    actionability_findings: list[str] = field(default_factory=list)
    high_value_rule_count: int = 0
    high_value_rule_sentence_max: int = 0
    high_value_rules_over_sentence_limit: int = 0
    high_value_rule_decision_count: int = 0
    high_value_rules_without_decision_semantics: int = 0
    max_prose_line_words: int = 0
    tutorial_explanatory_density: float = 0.0
    decision_density: float = 0.0
    professionalism_score: int = 100
    context_efficiency_score: int = 100
    routing_clarity_score: int = 100
    split_candidate_score: int = 0
    findings: list[str] = field(default_factory=list)
    classification: str = "KEEP"
    review_state: str = "KEEP"
    review_reasons: list[str] = field(default_factory=list)
    suggested_action: str = ""
    risk_of_change: str = "low"
    recommended_phase: str = "-"


@dataclass
class ReferenceMetrics:
    layer: str
    owner: str
    path: str
    kind: str
    exists: bool
    line_count: int | None = None
    token_count: int | None = None
    advisory_kind: str | None = None
    advisory_kind_source: str = "inferred"
    reference_type: str | None = None
    has_reference_type_preface: bool = False
    has_load_when_preface: bool = False
    has_do_not_load_when_preface: bool = False
    effective_preface: dict = field(default_factory=dict)
    h1_count: int = 0
    h1_status: str = "missing"
    h2_plus_headings: list[dict] = field(default_factory=list)
    empty_headings: list[dict] = field(default_factory=list)
    decision_headings: list[dict] = field(default_factory=list)
    decision_list_item_count: int = 0
    decision_table_item_count: int = 0
    decision_item_count: int = 0
    decision_sections: list[dict] = field(default_factory=list)
    max_decision_section_item_count: int = 0
    invalid_decision_section_headings: list[dict] = field(default_factory=list)


def _markdown_columns(value: str) -> int:
    """Return CommonMark-style columns for a leading prefix."""

    column = 0
    for character in value:
        if character == "\t":
            column += 4 - (column % 4)
        else:
            column += 1
    return column


def _leading_indent_columns(line: str) -> int:
    prefix = re.match(r"^[ \t]*", line)
    return _markdown_columns(prefix.group(0) if prefix else "")


def _list_item_indents(match: re.Match[str]) -> tuple[int, int]:
    marker_indent = _markdown_columns(match.group("indent"))
    content_indent = _markdown_columns(match.string[: match.start("text")])
    return marker_indent, content_indent


def _activate_list_item(
    active_items: list[tuple[int, int]], match: re.Match[str]
) -> tuple[int, int] | None:
    """Advance a CommonMark list-container stack for one candidate marker."""

    marker_indent, content_indent = _list_item_indents(match)
    while active_items and marker_indent < active_items[-1][1]:
        active_items.pop()
    if active_items:
        parent_content_indent = active_items[-1][1]
        if not parent_content_indent <= marker_indent <= parent_content_indent + 3:
            return None
    elif marker_indent > 3:
        return None
    item = (marker_indent, content_indent)
    active_items.append(item)
    return item


def _strip_fenced(lines: list[str]) -> list[tuple[int, str, bool]]:
    """Yield lines with container-aware fenced-code membership.

    CommonMark permits a fence indented relative to a list container, so a
    nested list fence can begin at four or more raw columns. Top-level fences
    retain the normal zero-to-three-column rule; deeper indentation is accepted
    only while an explicit list item owns that content indentation.
    """

    result: list[tuple[int, str, bool]] = []
    marker_character: str | None = None
    marker_length = 0
    fence_container_indent = 0
    active_list_items: list[tuple[int, int]] = []
    for index, line in enumerate(lines):
        if marker_character is not None:
            closing_match = re.fullmatch(
                rf"(?P<indent>[ \t]*){re.escape(marker_character)}"
                rf"{{{marker_length},}}[ \t]*",
                line,
            )
            closing = bool(
                closing_match
                and fence_container_indent
                <= _markdown_columns(closing_match.group("indent"))
                <= fence_container_indent + 3
            )
            result.append((index, line, True))
            if closing:
                marker_character = None
                marker_length = 0
                fence_container_indent = 0
            continue

        list_match = MARKDOWN_ANY_LIST_ITEM_RE.match(line)
        active_list_match = (
            _activate_list_item(active_list_items, list_match)
            if list_match
            else None
        )

        opening = FENCE_OPENING_RE.match(line)
        inline_list_opening = (
            FENCE_OPENING_RE.match(list_match.group("text"))
            if opening is None and list_match and active_list_match is not None
            else None
        )
        if inline_list_opening is not None:
            opening = inline_list_opening
        if opening:
            marker = opening.group("marker")
            info = opening.group("info")
            if inline_list_opening is not None:
                container_indent = active_list_match[1]
            else:
                opening_indent = _markdown_columns(opening.group("indent"))
                container_candidates = [
                    item_content_indent
                    for _item_marker_indent, item_content_indent in active_list_items
                    if item_content_indent <= opening_indent <= item_content_indent + 3
                ]
                container_indent = (
                    max(container_candidates)
                    if container_candidates
                    else (0 if opening_indent <= 3 else None)
                )
            # CommonMark forbids a backtick in the info string of a backtick
            # fence. Treat that line as prose rather than allowing it to hide
            # following metadata.
            if container_indent is not None and (
                marker[0] != "`" or "`" not in info
            ):
                marker_character = marker[0]
                marker_length = len(marker)
                fence_container_indent = container_indent
                result.append((index, line, True))
                continue
        result.append((index, line, False))

        if active_list_match is None and line.strip():
            line_indent = _leading_indent_columns(line)
            while active_list_items and line_indent < active_list_items[-1][1]:
                active_list_items.pop()
    return result


def _unfenced_text(lines: list[str]) -> str:
    return "\n".join(line for _index, line, in_fence in _strip_fenced(lines) if not in_fence)


def _pattern_count(patterns: tuple[str, ...], text: str) -> int:
    return sum(len(re.findall(pattern, text, flags=re.IGNORECASE)) for pattern in patterns)


def _front_window_text(body: str) -> str:
    return _unfenced_text(body.splitlines()[:THRESHOLDS["front_window_lines"]])


def _front_loaded_action_score(body: str) -> int:
    window = _front_window_text(body)
    score = 0
    if _pattern_count(FRONT_FIRST_MOVE_PATTERNS, window):
        score += 20
    if _pattern_count(FRONT_STOP_CONDITION_PATTERNS, window):
        score += 20
    if _pattern_count(FRONT_RATIONALE_PATTERNS, window):
        score += 20
    if _pattern_count(FRONT_VERIFICATION_PATTERNS, window):
        score += 20
    action_verbs = {
        match.group(1).casefold() for match in DOMAIN_ACTION_VERB_RE.finditer(window)
    }
    score += min(20, 4 * len(action_verbs))
    return max(0, min(100, score))


def _control_boilerplate_density(body: str) -> float:
    """Return weighted control-plane term hits per 100 words.

    The front window is weighted slightly more because governance boilerplate at
    the top of a skill crowds out the first actionable instructions.
    """
    front = _front_window_text(body)
    whole = _unfenced_text(body.splitlines())
    front_words = max(1, len(re.findall(r"\b[\w/-]+\b", front)))
    whole_words = max(1, len(re.findall(r"\b[\w/-]+\b", whole)))
    front_density = _pattern_count(CONTROL_BOILERPLATE_PATTERNS, front) / front_words
    whole_density = _pattern_count(CONTROL_BOILERPLATE_PATTERNS, whole) / whole_words
    return round(((front_density * 0.6) + (whole_density * 0.4)) * 100, 2)


def _generic_control_phrase_count(body: str) -> int:
    return _pattern_count(GENERIC_CONTROL_PHRASE_PATTERNS, _unfenced_text(body.splitlines()))


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


def _normalize_control_scaffold_line(value: str) -> str:
    """Normalize Markdown and Profile spelling without erasing semantics."""

    plain = LIST_MARKER_RE.sub("", value.strip())
    plain = re.sub(r"[`*_~]", "", plain)
    plain = re.sub(
        r"\bmain(?:-|\s+)control(?:-|\s+)agent\b",
        "main-control-agent",
        plain,
        flags=re.IGNORECASE,
    )
    plain = re.sub(
        r"\b(analysis|task|review)(?:-|\s+)agent\b",
        lambda match: f"{match.group(1).casefold()}-agent",
        plain,
        flags=re.IGNORECASE,
    )
    return re.sub(r"\s+", " ", plain).strip().rstrip(".").casefold()


def _control_scaffold_findings(
    kind: str,
    sections: list[Section],
) -> list[dict[str, object]]:
    """Return section-aware generic control scaffold evidence."""

    if kind not in {"professional-skill", "foundation-capability"}:
        return []
    findings: list[dict[str, object]] = []
    for section in sections:
        section_name = section.title.casefold()
        if section_name in {"targeted references", "reference loading policy"}:
            continue
        foundation_profile_sequence_offset: int | None = None
        if kind == "foundation-capability" and section_name == "execution checklist":
            section_roles: set[str] = set()
            first_role_offset: int | None = None
            for role_offset, role_line, role_in_fence in _strip_fenced(
                section.text.splitlines()
            ):
                if role_in_fence:
                    continue
                role_matches = list(
                    CONTROL_SCAFFOLD_PROFILE_RE.finditer(
                        _normalize_control_scaffold_line(role_line)
                    )
                )
                if role_matches and first_role_offset is None:
                    first_role_offset = role_offset
                section_roles.update(
                    match.group(1).casefold() for match in role_matches
                )
            if len(section_roles) >= 2:
                foundation_profile_sequence_offset = first_role_offset
        for offset, raw_line, in_fence in _strip_fenced(section.text.splitlines()):
            if in_fence or not raw_line.strip():
                continue
            normalized = _normalize_control_scaffold_line(raw_line)
            if not normalized:
                continue
            line_number = section.start + offset + 2
            exact_family = (
                FOUNDATION_EXACT_CONTROL_SCAFFOLDS.get(normalized)
                if kind == "foundation-capability"
                else None
            )
            if exact_family is not None:
                findings.append(
                    {
                        "family": exact_family,
                        "section": section.title,
                        "line": line_number,
                        "text": raw_line.strip(),
                        "match": "foundation-exact",
                    }
                )
                continue

            if (
                kind == "foundation-capability"
                and section_name == "skill role"
                and FOUNDATION_GENERIC_RETURN_RE.search(normalized)
            ):
                findings.append(
                    {
                        "family": "foundation-return",
                        "section": section.title,
                        "line": line_number,
                        "text": raw_line.strip(),
                        "match": "foundation-broad-governance",
                    }
                )
            if (
                kind == "foundation-capability"
                and section_name in {"inputs", "required inputs"}
                and FOUNDATION_GENERIC_INPUT_RE.search(normalized)
            ):
                findings.append(
                    {
                        "family": "foundation-inputs",
                        "section": section.title,
                        "line": line_number,
                        "text": raw_line.strip(),
                        "match": "foundation-governance",
                    }
                )

            for family, (pattern, allowed_sections) in CONTROL_SCAFFOLD_SECTION_PATTERNS.items():
                if section_name not in allowed_sections or not pattern.search(normalized):
                    continue
                if (
                    family == "generic-handoff"
                    and len(
                        {
                            match.group(0).casefold()
                            for match in CONTROL_SCAFFOLD_HANDOFF_MARKER_RE.finditer(
                                normalized
                            )
                        }
                    )
                    < CONTROL_SCAFFOLD_HANDOFF_MIN_MARKERS
                ):
                    continue
                findings.append(
                    {
                        "family": family,
                        "section": section.title,
                        "line": line_number,
                        "text": raw_line.strip(),
                        "match": "section-pattern",
                    }
                )
            profile_match = False
            profile_match_kind = "normalized-profile-pattern"
            if kind == "professional-skill":
                profile_match = bool(
                    section_name in CONTROL_SCAFFOLD_PROFILE_SECTIONS
                    and CONTROL_SCAFFOLD_PROFILE_MODE_RE.search(normalized)
                )
            elif section_name == "execution checklist":
                profile_match = offset == foundation_profile_sequence_offset
                profile_match_kind = "foundation-governance"
            if profile_match:
                findings.append(
                    {
                        "family": "profile-mode",
                        "section": section.title,
                        "line": line_number,
                        "text": raw_line.strip(),
                        "match": profile_match_kind,
                    }
                )
    return sorted(
        findings,
        key=lambda finding: (
            int(finding["line"]),
            str(finding["family"]),
            str(finding["text"]),
        ),
    )


def _high_confidence_control_scaffold(
    kind: str,
    findings: list[dict[str, object]],
) -> bool:
    """Require an exact Foundation line or a complete Professional flow arc."""

    if kind == "foundation-capability":
        if any(
            finding["match"] in {"foundation-exact", "foundation-governance"}
            for finding in findings
        ):
            return True
        families = {str(finding["family"]) for finding in findings}
        return bool(
            families & CONTROL_SCAFFOLD_PREPARE_FAMILIES
            and families & CONTROL_SCAFFOLD_EXECUTE_FAMILIES
            and families
            & (CONTROL_SCAFFOLD_CLOSE_FAMILIES | {"foundation-return"})
        )
    if kind != "professional-skill":
        return False
    families = {str(finding["family"]) for finding in findings}
    return bool(
        families & CONTROL_SCAFFOLD_PREPARE_FAMILIES
        and families & CONTROL_SCAFFOLD_EXECUTE_FAMILIES
        and families & CONTROL_SCAFFOLD_CLOSE_FAMILIES
    )


def _find_section(sections: list[Section], title: str) -> Section | None:
    wanted = title.casefold()
    for section in sections:
        if section.title.casefold() == wanted:
            return section
    return None


def _find_section_any(sections: list[Section], *titles: str) -> Section | None:
    for title in titles:
        section = _find_section(sections, title)
        if section is not None:
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
        is_pipe_row = len(_split_markdown_table_row(stripped)) >= 2
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

    This permits concise decision-bearing prose without treating every section as
    a checklist, while still detecting empty or generic stubs.
    """
    if section is None:
        return True
    content = section.text.strip()
    bullets = sum(1 for line in content.splitlines() if LIST_ITEM_RE.match(line))
    return len(content) < min_chars and bullets < min_bullets


def _load_foundation_content_contracts() -> dict[str, dict]:
    """Load the schema-v4 authoring classification that owns word budgets."""

    _require_safe_source_path(
        CAPABILITIES_REGISTRY,
        allowed_root=ROOT / "src" / "registry",
        source="registry",
        expect_directory=False,
    )
    data = load_yaml_file(CAPABILITIES_REGISTRY)
    if not isinstance(data, dict):
        raise ValidationProblem(
            f"{_repository_relative_path(CAPABILITIES_REGISTRY)}: must be a mapping"
        )
    if data.get("schema_version") != REGISTRY_SCHEMA_VERSIONS["foundation"]:
        raise ValidationProblem(
            f"{_repository_relative_path(CAPABILITIES_REGISTRY)}: schema_version "
            f"must equal {REGISTRY_SCHEMA_VERSIONS['foundation']}"
        )
    entries = data.get("foundation_skills")
    if not isinstance(entries, list) or len(entries) != EXPECTED_FOUNDATION_CAPABILITY_COUNT:
        raise ValidationProblem(
            f"{_repository_relative_path(CAPABILITIES_REGISTRY)}: foundation_skills "
            f"must contain {EXPECTED_FOUNDATION_CAPABILITY_COUNT} entries"
        )

    contracts: dict[str, dict] = {}
    errors: list[str] = []
    for index, entry in enumerate(entries):
        context = f"foundation-skills.yaml:foundation_skills[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{context}: must be a mapping")
            continue
        name = entry.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"{context}: name must be a non-empty string")
            continue
        errors.extend(foundation_registry_field_errors(entry, context))
        errors.extend(foundation_content_class_errors(entry, context))
        content_class = entry.get("content_class")
        if content_class not in FOUNDATION_CONTENT_CLASSES:
            continue
        if name in contracts:
            errors.append(f"{context}: duplicate name {name!r}")
            continue
        budget = foundation_content_budget(content_class)
        contracts[name] = {
            "content_class": content_class,
            "content_class_rationale": entry.get("content_class_rationale"),
            "target_words": budget["target_words"],
            "hard_words": budget["hard_words"],
        }
    if errors:
        raise ValidationProblem("; ".join(errors))
    if len(contracts) != EXPECTED_FOUNDATION_CAPABILITY_COUNT:
        raise ValidationProblem(
            "Foundation content_class contracts do not cover every registered Skill"
        )
    return contracts


def _load_used_by_counts() -> dict[str, int]:
    counts: dict[str, int] = {}
    _require_safe_source_path(
        CAPABILITIES_REGISTRY,
        allowed_root=ROOT / "src" / "registry",
        source="registry",
        expect_directory=False,
    )
    try:
        data = load_yaml_file(CAPABILITIES_REGISTRY)
    except ValidationProblem:
        return counts
    if not isinstance(data, dict):
        return counts
    for entry in data.get("foundation_skills", []) or []:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        used_by = entry.get("used_by")
        if isinstance(name, str) and isinstance(used_by, list):
            counts[name] = len([item for item in used_by if isinstance(item, str)])
    return counts


def _safe_skill_files_for_root(kind: str, root: Path) -> list[tuple[str, Path]]:
    _require_safe_source_path(
        root,
        allowed_root=ROOT,
        source="registry",
        expect_directory=True,
    )
    files: list[tuple[str, Path]] = []
    for skill_dir in sorted(root.iterdir()):
        if skill_dir.name.startswith((".", "_")):
            continue
        skill_dir_safe, skill_dir_errors = _safe_source_path(
            skill_dir,
            allowed_root=root,
            source="registry",
            expect_directory=True,
            target=_repository_relative_path(skill_dir),
        )
        if not skill_dir_safe:
            if skill_dir_errors and all(
                item.get("code") == "source-not-directory"
                for item in skill_dir_errors
            ):
                continue
            detail = "; ".join(
                f"{item['code']}: {item['message']}" for item in skill_dir_errors
            ) or "required Skill directory is missing"
            raise ValidationProblem(
                f"{_repository_relative_path(skill_dir)}: {detail}"
            )
        skill_file = skill_dir / "SKILL.md"
        safe, errors = _safe_source_path(
            skill_file,
            allowed_root=skill_dir,
            source="local",
            expect_directory=False,
            target=_repository_relative_path(skill_file),
        )
        if errors:
            detail = "; ".join(
                f"{item['code']}: {item['message']}" for item in errors
            )
            raise ValidationProblem(
                f"{_repository_relative_path(skill_file)}: {detail}"
            )
        if safe:
            files.append((kind, skill_file))
    return files


def _collect_files() -> list[tuple[str, Path]]:
    files: list[tuple[str, Path]] = []
    for kind, root in DESCRIPTION_ROOTS:
        if kind == "control-skill":
            continue
        files.extend(_safe_skill_files_for_root(kind, root))
    return files


def _collect_description_lengths_by_kind() -> dict[str, list[int]]:
    lengths = {kind: [] for kind in DESCRIPTION_BUDGETS}
    for kind, root in DESCRIPTION_ROOTS:
        for _kind, skill_file in _safe_skill_files_for_root(kind, root):
            try:
                metadata, _raw, _body = parse_frontmatter(skill_file)
            except ValidationProblem:
                metadata = {}
            description = metadata.get("description") if isinstance(metadata, dict) else None
            lengths[kind].append(len(description.strip()) if isinstance(description, str) else 0)
    return lengths


def _reference_kind(path: str) -> str:
    return reference_type_for_path(path)


def _explicit_preface(lines: list[str], label: str) -> tuple[bool, str | None]:
    pattern = re.compile(
        rf"^\s*(?:>\s*)?(?:[-*+]\s+)?(?:\*\*|__)?{re.escape(label)}"
        r"(?:(?:\*\*|__))?\s*:\s*(?:(?:\*\*|__))?\s*(.*?)\s*$",
        re.IGNORECASE,
    )
    for _index, line, in_fence in _strip_fenced(lines):
        if in_fence or HEADING_RE.match(line):
            continue
        match = pattern.match(line)
        if match:
            return True, match.group(1).strip() or None
    return False, None


def _normalized_reference_type(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = re.sub(r"[\s_]+", "-", value.strip().casefold())
    return normalized if normalized in REFERENCE_CONTRACT_TYPES else None


def _normalized_preface_text(value: str) -> str:
    value = MARKDOWN_LINK_RE.sub(" ", value)
    value = re.sub(r"[`*_]+", "", value)
    value = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(re.findall(r"[\w.-]+", value))


def _preface_text_is_usable(value: str | None) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    stripped = MARKDOWN_LINK_RE.sub("", value)
    stripped = re.sub(r"[`*_]+", "", stripped).strip()
    if GENERIC_PREFACE_TEXT_RE.match(stripped):
        return False
    return len(re.findall(r"[A-Za-z0-9]+", stripped)) >= 3


def _normalized_consumption_value(field: str, value: object) -> str | None:
    """Return one canonical JSON list for Registry-owned consumption fields."""

    if field not in {"required_by", "required_output"}:
        return None
    parsed: object = value
    if isinstance(value, str):
        stripped = value.strip()
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            parsed = [item.strip() for item in stripped.split(",") if item.strip()]
    if not isinstance(parsed, list) or not parsed:
        return None
    if any(not isinstance(item, str) or not item.strip() for item in parsed):
        return None
    values = [item.strip() for item in parsed]
    if len(values) != len(set(values)):
        return None
    vocabulary = (
        REFERENCE_CONTRACT_ROLES
        if field == "required_by"
        else REFERENCE_OUTPUT_TYPES
    )
    if not set(values) <= vocabulary:
        return None
    return json.dumps(values, ensure_ascii=True, separators=(",", ":"))


def _preface_evidence(
    *,
    source: str,
    path: str,
    line: int,
    value: str,
    accepted: bool = True,
    reason: str | None = None,
) -> dict:
    result = {
        "source": source,
        "path": path,
        "line": line,
        "value": value.strip(),
        "accepted": accepted,
    }
    if reason:
        result["reason"] = reason
    return result


def _canonical_preface_evidence(field: str, row: dict) -> dict:
    """Recompute one evidence row from its declaration, never its claims."""
    source = str(row.get("source", ""))
    path = str(row.get("path", ""))
    line = row.get("line")
    value = str(row.get("value", "")).strip()
    if field == "reference_type":
        normalized_type = _normalized_reference_type(value)
        return _preface_evidence(
            source=source,
            path=path,
            line=line,
            value=normalized_type or value,
            accepted=bool(normalized_type),
            reason=None if normalized_type else "unrecognized-reference-type",
        )
    if field in {"required_by", "required_output"}:
        normalized = _normalized_consumption_value(field, value)
        return _preface_evidence(
            source=source,
            path=path,
            line=line,
            value=normalized or value,
            accepted=bool(normalized),
            reason=None if normalized else f"invalid-{field.replace('_', '-')}",
        )
    accepted = _preface_text_is_usable(value)
    if source == "parent-root" and field == "do_not_load_when":
        stripped = MARKDOWN_LINK_RE.sub("", value)
        accepted = accepted and bool(
            re.search(
                r"\b(?:when|if|unless|otherwise|except|while|for)\b",
                stripped,
                re.IGNORECASE,
            )
        )
    return _preface_evidence(
        source=source,
        path=path,
        line=line,
        value=value,
        accepted=accepted,
        reason=None if accepted else "generic-or-empty-trigger",
    )


def _local_preface_evidence(markdown: str, path: str) -> dict[str, list[dict]]:
    lines = markdown.splitlines()
    result = {field: [] for field in PREFACE_FIELDS}
    labels = {
        "reference_type": "Reference type",
        "load_when": "Load when",
        "do_not_load_when": "Do not load when",
        "required_by": "Required by",
        "required_output": "Required output",
    }
    annotated = _strip_fenced(lines)
    for field, label in labels.items():
        pattern = re.compile(
            rf"^\s*(?:>\s*)?(?:[-*+]\s+)?(?:\*\*|__)?{re.escape(label)}"
            r"(?:(?:\*\*|__))?\s*:\s*(?:(?:\*\*|__))?\s*(.*?)\s*$",
            re.IGNORECASE,
        )
        for index, line, in_fence in annotated:
            if in_fence or HEADING_RE.match(line):
                continue
            match = pattern.match(line)
            if not match:
                continue
            value = match.group(1).strip()
            normalized_type = _normalized_reference_type(value) if field == "reference_type" else None
            normalized_consumption = _normalized_consumption_value(field, value)
            accepted = (
                bool(normalized_type)
                if field == "reference_type"
                else bool(normalized_consumption)
                if field in {"required_by", "required_output"}
                else _preface_text_is_usable(value)
            )
            reason = None
            if not accepted:
                reason = (
                    "unrecognized-reference-type"
                    if field == "reference_type"
                    else f"invalid-{field.replace('_', '-')}"
                    if field in {"required_by", "required_output"}
                    else "generic-or-empty-trigger"
                )
            result[field].append(
                _preface_evidence(
                    source="local",
                    path=path,
                    line=index + 1,
                    value=normalized_type or normalized_consumption or value,
                    accepted=accepted,
                    reason=reason,
                )
            )

    headings = _heading_records(markdown)
    for position, heading in enumerate(headings):
        title = _normalized_preface_text(heading["title"])
        field = next(
            (
                candidate
                for candidate, aliases in PREFACE_HEADING_ALIASES.items()
                if title in aliases
            ),
            None,
        )
        if field is None:
            continue
        end = len(lines)
        for later in headings[position + 1:]:
            if later["level"] <= heading["level"]:
                end = later["_index"]
                break
        value = next(
            (
                line.strip().lstrip(">-+* ").strip()
                for index, line, in_fence in annotated
                if heading["_index"] < index < end
                and not in_fence
                and line.strip()
                and not HEADING_RE.match(line)
            ),
            "",
        )
        normalized_type = _normalized_reference_type(value) if field == "reference_type" else None
        normalized_consumption = _normalized_consumption_value(field, value)
        accepted = (
            bool(normalized_type)
            if field == "reference_type"
            else bool(normalized_consumption)
            if field in {"required_by", "required_output"}
            else _preface_text_is_usable(value)
        )
        result[field].append(
            _preface_evidence(
                source="local",
                path=path,
                line=heading["line"],
                value=normalized_type or normalized_consumption or value,
                accepted=accepted,
                reason=(
                    None
                    if accepted
                    else (
                        "unrecognized-reference-type"
                        if field == "reference_type"
                        else f"invalid-{field.replace('_', '-')}"
                        if field in {"required_by", "required_output"}
                        else "generic-or-empty-trigger"
                    )
                ),
            )
        )
    return result


def _split_markdown_table_row(line: str) -> list[str]:
    """Split one Markdown table row without treating escaped/code pipes as columns."""

    text = line.strip()
    cells: list[str] = []
    current: list[str] = []
    code_delimiter = 0
    index = 0
    while index < len(text):
        char = text[index]
        if char == "\\" and index + 1 < len(text):
            following = text[index + 1]
            if following == "|":
                current.append("|")
                index += 2
                continue
            current.extend((char, following))
            index += 2
            continue
        if char == "`":
            end = index
            while end < len(text) and text[end] == "`":
                end += 1
            run_length = end - index
            if code_delimiter == 0:
                code_delimiter = run_length
            elif code_delimiter == run_length:
                code_delimiter = 0
            current.append(text[index:end])
            index = end
            continue
        if char == "|" and code_delimiter == 0:
            cells.append("".join(current).strip())
            current = []
            index += 1
            continue
        current.append(char)
        index += 1
    cells.append("".join(current).strip())
    if cells and not cells[0]:
        cells.pop(0)
    if cells and not cells[-1]:
        cells.pop()
    return cells


def _normalized_table_header(value: str) -> str:
    return _normalized_preface_text(value).replace("-", " ")


def _is_markdown_table_separator(cells: list[str], width: int) -> bool:
    return len(cells) == width and all(
        re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells
    )


def _resolved_owner_target(
    raw_target: str,
    *,
    source_path: Path,
    owner_root: Path,
    owner_relative: bool,
) -> tuple[str | None, str | None]:
    raw_target = raw_target.strip().split("#", 1)[0]
    if not raw_target or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", raw_target):
        return None, "non-local-reference-target"
    if Path(raw_target).is_absolute():
        return None, "absolute-reference-target"
    base = owner_root if owner_relative else source_path.parent
    target = (base / raw_target).resolve()
    owner_resolved = owner_root.resolve()
    try:
        target.relative_to(owner_resolved)
    except ValueError:
        return None, "cross-owner-reference-target"
    try:
        return target.relative_to(ROOT.resolve()).as_posix(), None
    except ValueError:
        return None, "reference-target-outside-repository"


def _reference_cell_target(
    cell: str,
    *,
    source_path: Path,
    owner_root: Path,
) -> tuple[str | None, str | None]:
    links = MARKDOWN_LINK_TARGET_RE.findall(cell)
    if len(links) > 1:
        return None, "ambiguous-reference-cell"
    if links:
        return _resolved_owner_target(
            links[0], source_path=source_path, owner_root=owner_root, owner_relative=False
        )
    raw = cell.strip().strip("`")
    return _resolved_owner_target(
        raw,
        source_path=source_path,
        owner_root=owner_root,
        owner_relative=raw.startswith(("references/", "examples/")),
    )


def _preface_contract_issue(
    *, code: str, source: str, path: str, line: int, message: str, target: str | None = None
) -> dict:
    issue = {"code": code, "source": source, "path": path, "line": line, "message": message}
    if target:
        issue["target"] = target
    return issue


def _repository_relative_path(path: Path) -> str:
    try:
        return path.absolute().relative_to(ROOT.absolute()).as_posix()
    except ValueError:
        return path.absolute().as_posix()


def _path_chain_uses_symlink(path: Path, boundary: Path) -> bool:
    """Check the lexical path chain without resolving away an ancestor link."""
    cursor = path.absolute()
    boundary = boundary.absolute()
    try:
        cursor.relative_to(boundary)
    except ValueError:
        return False
    while True:
        if cursor.is_symlink():
            return True
        if cursor == boundary:
            return False
        cursor = cursor.parent


def _safe_source_path(
    path: Path,
    *,
    allowed_root: Path,
    source: str,
    expect_directory: bool,
    target: str | None = None,
) -> tuple[bool, list[dict]]:
    """Validate lexical and real containment before any source read/traversal."""
    display = _repository_relative_path(path)
    root_absolute = ROOT.absolute()
    path_absolute = path.absolute()
    allowed_absolute = allowed_root.absolute()
    for candidate, label in (
        (allowed_absolute, "allowed source root"),
        (path_absolute, "source path"),
    ):
        try:
            candidate.relative_to(root_absolute)
        except ValueError:
            return False, [
                _preface_contract_issue(
                    code="source-path-outside-repository",
                    source=source,
                    path=display,
                    line=1,
                    target=target,
                    message=f"{label} is lexically outside the repository",
                )
            ]
    try:
        path_absolute.relative_to(allowed_absolute)
    except ValueError:
        return False, [
            _preface_contract_issue(
                code="source-path-outside-owner",
                source=source,
                path=display,
                line=1,
                target=target,
                message="source path is lexically outside its owner boundary",
            )
        ]
    if _path_chain_uses_symlink(allowed_root, ROOT) or _path_chain_uses_symlink(path, ROOT):
        return False, [
            _preface_contract_issue(
                code="source-symlink-chain",
                source=source,
                path=display,
                line=1,
                target=target,
                message="source path or an ancestor is a symlink",
            )
        ]
    try:
        root_resolved = ROOT.resolve(strict=True)
        allowed_resolved = allowed_root.resolve(strict=False)
        path_resolved = path.resolve(strict=False)
        allowed_resolved.relative_to(root_resolved)
        path_resolved.relative_to(root_resolved)
        path_resolved.relative_to(allowed_resolved)
    except (OSError, ValueError):
        return False, [
            _preface_contract_issue(
                code="source-realpath-outside-repository",
                source=source,
                path=display,
                line=1,
                target=target,
                message="source path or allowed root resolves outside the repository boundary",
            )
        ]
    if not path.exists():
        return False, []
    try:
        mode = path.lstat().st_mode
    except OSError:
        return False, [
            _preface_contract_issue(
                code="source-stat-failed",
                source=source,
                path=display,
                line=1,
                target=target,
                message="source path could not be inspected safely",
            )
        ]
    expected = stat.S_ISDIR(mode) if expect_directory else stat.S_ISREG(mode)
    if not expected:
        return False, [
            _preface_contract_issue(
                code=("source-not-directory" if expect_directory else "source-not-regular-file"),
                source=source,
                path=display,
                line=1,
                target=target,
                message=(
                    "source root is not a non-symlink directory"
                    if expect_directory
                    else "source document is not a non-symlink regular file"
                ),
            )
        ]
    try:
        resolved = path.resolve(strict=True)
        allowed_resolved = allowed_root.resolve(strict=True)
        resolved.relative_to(ROOT.resolve(strict=True))
        resolved.relative_to(allowed_resolved)
    except (OSError, ValueError):
        return False, [
            _preface_contract_issue(
                code="source-realpath-outside-owner",
                source=source,
                path=display,
                line=1,
                target=target,
                message="source realpath is outside its owner boundary",
            )
        ]
    return True, []


def _safe_markdown_text(
    path: Path,
    *,
    allowed_root: Path,
    source: str,
    target: str | None = None,
) -> tuple[str | None, list[dict]]:
    safe, errors = _safe_source_path(
        path,
        allowed_root=allowed_root,
        source=source,
        expect_directory=False,
        target=target,
    )
    if not safe:
        return None, errors
    try:
        return path.read_text(encoding="utf-8"), []
    except (OSError, UnicodeError):
        return None, [
            _preface_contract_issue(
                code="source-read-failed",
                source=source,
                path=_repository_relative_path(path),
                line=1,
                target=target,
                message="source document could not be read as UTF-8",
            )
        ]


def _require_safe_source_path(
    path: Path,
    *,
    allowed_root: Path,
    source: str,
    expect_directory: bool,
) -> None:
    safe, errors = _safe_source_path(
        path,
        allowed_root=allowed_root,
        source=source,
        expect_directory=expect_directory,
        target=_repository_relative_path(path),
    )
    if safe:
        return
    if errors:
        detail = "; ".join(
            f"{item['code']}: {item['message']}" for item in errors
        )
    else:
        detail = "required source path is missing"
    raise ValidationProblem(f"{_repository_relative_path(path)}: {detail}")


def _owner_index_preface_evidence(
    owner_root: Path,
    indexed_paths: set[str],
) -> tuple[dict[str, dict[str, list[dict]]], list[dict]]:
    result: dict[str, dict[str, list[dict]]] = defaultdict(
        lambda: {field: [] for field in PREFACE_FIELDS}
    )
    errors: list[dict] = []
    index_path = owner_root / "references" / "index.md"
    relative_index = _repository_relative_path(index_path)
    markdown, source_errors = _safe_markdown_text(
        index_path,
        allowed_root=owner_root / "references",
        source="reference-index",
        target=relative_index,
    )
    errors.extend(source_errors)
    if markdown is None:
        return {}, errors
    annotated = _strip_fenced(markdown.splitlines())
    table: list[tuple[int, str]] = []
    seen: dict[str, int] = {}

    def flush() -> None:
        nonlocal table
        if not table:
            table = []
            return
        header = _split_markdown_table_row(table[0][1])
        normalized = [_normalized_table_header(cell) for cell in header]
        if "reference" not in normalized:
            table = []
            return
        required = ("reference", "load when", "do not load when")
        if any(normalized.count(name) != 1 for name in required):
            errors.append(
                _preface_contract_issue(
                    code="malformed-index-header",
                    source="reference-index",
                    path=relative_index,
                    line=table[0][0],
                    message="reference metadata table requires unique Reference, Load When, and Do Not Load When columns",
                )
            )
            table = []
            return
        if len(table) < 2 or not _is_markdown_table_separator(
            _split_markdown_table_row(table[1][1]), len(header)
        ):
            errors.append(
                _preface_contract_issue(
                    code="malformed-index-separator",
                    source="reference-index",
                    path=relative_index,
                    line=table[1][0] if len(table) > 1 else table[0][0],
                    message="reference metadata table requires a complete Markdown separator row",
                )
            )
            table = []
            return
        columns = {name: normalized.index(name) for name in required}
        type_index = next(
            (normalized.index(name) for name in ("reference type", "type") if name in normalized),
            None,
        )
        for line_number, line in table[2:]:
            cells = _split_markdown_table_row(line)
            if len(cells) != len(header) or any(
                not cells[columns[name]].strip() for name in required
            ):
                errors.append(
                    _preface_contract_issue(
                        code="malformed-index-row",
                        source="reference-index",
                        path=relative_index,
                        line=line_number,
                        message="reference metadata row does not match its declared columns",
                    )
                )
                continue
            target, target_error = _reference_cell_target(
                cells[columns["reference"]], source_path=index_path, owner_root=owner_root
            )
            if target_error:
                errors.append(
                    _preface_contract_issue(
                        code=target_error,
                        source="reference-index",
                        path=relative_index,
                        line=line_number,
                        message="reference index target is ambiguous or outside its owner",
                    )
                )
                continue
            if target not in indexed_paths:
                # Example/output rows may share an index table but do not
                # establish Reference preface metadata.
                continue
            if target == relative_index:
                errors.append(
                    _preface_contract_issue(
                        code="index-self-inheritance",
                        source="reference-index",
                        path=relative_index,
                        line=line_number,
                        target=target,
                        message="an index cannot inherit metadata from a row it manages",
                    )
                )
                continue
            if target in seen:
                errors.append(
                    _preface_contract_issue(
                        code="duplicate-index-row",
                        source="reference-index",
                        path=relative_index,
                        line=line_number,
                        target=target,
                        message=f"duplicate metadata row; first declared at line {seen[target]}",
                    )
                )
            else:
                seen[target] = line_number
            for field, column_name in (("load_when", "load when"), ("do_not_load_when", "do not load when")):
                value = cells[columns[column_name]].strip()
                accepted = _preface_text_is_usable(value)
                result[target][field].append(
                    _preface_evidence(
                        source="reference-index",
                        path=relative_index,
                        line=line_number,
                        value=value,
                        accepted=accepted,
                        reason=None if accepted else "generic-or-empty-trigger",
                    )
                )
            if type_index is not None and type_index < len(cells):
                value = cells[type_index].strip()
                normalized_type = _normalized_reference_type(value)
                result[target]["reference_type"].append(
                    _preface_evidence(
                        source="reference-index",
                        path=relative_index,
                        line=line_number,
                        value=normalized_type or value,
                        accepted=bool(normalized_type),
                        reason=None if normalized_type else "unrecognized-reference-type",
                    )
                )
        table = []

    for index, line, in_fence in annotated:
        if not in_fence and line.lstrip().startswith("|"):
            table.append((index + 1, line))
        else:
            flush()
    flush()
    return dict(result), errors


def _owner_root_preface_evidence(
    owner_root: Path,
    indexed_paths: set[str],
) -> tuple[dict[str, dict[str, list[dict]]], list[dict]]:
    result: dict[str, dict[str, list[dict]]] = defaultdict(
        lambda: {field: [] for field in PREFACE_FIELDS}
    )
    errors: list[dict] = []
    skill_path = owner_root / "SKILL.md"
    relative_skill = _repository_relative_path(skill_path)
    markdown, source_errors = _safe_markdown_text(
        skill_path,
        allowed_root=owner_root,
        source="parent-root",
        target=relative_skill,
    )
    errors.extend(source_errors)
    if markdown is None:
        return {}, errors
    lines = markdown.splitlines()
    annotated = _strip_fenced(lines)
    sections = [
        index
        for index, line, in_fence in annotated
        if not in_fence
        and (match := HEADING_RE.match(line))
        and len(match.group(1)) == 2
        and _normalized_preface_text(match.group(2)) == "targeted references"
    ]
    if len(sections) > 1:
        errors.append(
            _preface_contract_issue(
                code="duplicate-targeted-reference-section",
                source="parent-root",
                path=relative_skill,
                line=sections[1] + 1,
                message="parent root has more than one Targeted References section",
            )
        )
    if not sections:
        return {}, errors
    start = sections[0] + 1
    end = len(lines)
    for index, line, in_fence in annotated[start:]:
        match = None if in_fence else HEADING_RE.match(line)
        if match and len(match.group(1)) <= 2:
            end = index
            break

    items: list[tuple[int, str]] = []
    current_line: int | None = None
    current: list[str] = []
    for index, line, in_fence in annotated:
        if index < start or index >= end or in_fence:
            continue
        if re.match(r"^\s*[-*+]\s+", line):
            if current_line is not None:
                items.append((current_line, " ".join(current)))
            current_line = index + 1
            current = [re.sub(r"^\s*[-*+]\s+", "", line).strip()]
        elif current_line is not None and line.strip() and not HEADING_RE.match(line):
            current.append(line.strip())
    if current_line is not None:
        items.append((current_line, " ".join(current)))

    seen: dict[str, int] = {}
    mode_targets: dict[str, tuple[int, str]] = {}
    group_mode_rules: list[tuple[int, str]] = []
    for line_number, item_text in items:
        links = MARKDOWN_LINK_TARGET_RE.findall(item_text)
        if not links:
            if re.search(r"\bnever\s+load\b.*\bmode\s+reference\b", item_text, re.IGNORECASE):
                group_mode_rules.append((line_number, item_text))
            continue
        if len(links) != 1:
            errors.append(
                _preface_contract_issue(
                    code="ambiguous-root-link",
                    source="parent-root",
                    path=relative_skill,
                    line=line_number,
                    message="a managed parent-root bullet must name exactly one Reference target",
                )
            )
            continue
        target, target_error = _resolved_owner_target(
            links[0],
            source_path=skill_path,
            owner_root=owner_root,
            owner_relative=False,
        )
        if target_error:
            errors.append(
                _preface_contract_issue(
                    code=target_error,
                    source="parent-root",
                    path=relative_skill,
                    line=line_number,
                    message="parent-root reference link is outside its owner",
                )
            )
            continue
        if target not in indexed_paths:
            # Exact example/output links are outside the managed Reference set.
            continue
        if target in seen:
            errors.append(
                _preface_contract_issue(
                    code="duplicate-root-link",
                    source="parent-root",
                    path=relative_skill,
                    line=line_number,
                    target=target,
                    message=f"duplicate exact target link; first declared at line {seen[target]}",
                )
            )
        else:
            seen[target] = line_number

        negative_match = re.search(
            r"\b(?:otherwise|unless)\b|\b(?:do\s+not|never)\s+load\b|\bskip\b",
            item_text,
            re.IGNORECASE,
        )
        positive_clause = (
            item_text[: negative_match.start()].rstrip(" ;,.")
            if negative_match
            else item_text
        )
        negative_clause = item_text[negative_match.start():].strip() if negative_match else ""
        if positive_clause:
            accepted = _preface_text_is_usable(positive_clause)
            result[target]["load_when"].append(
                _preface_evidence(
                    source="parent-root",
                    path=relative_skill,
                    line=line_number,
                    value=positive_clause,
                    accepted=accepted,
                    reason=None if accepted else "generic-or-empty-trigger",
                )
            )
        if negative_clause:
            stripped_negative = MARKDOWN_LINK_RE.sub("", negative_clause)
            has_condition = bool(
                re.search(
                    r"\b(?:when|if|unless|otherwise|except|while|for)\b",
                    stripped_negative,
                    re.IGNORECASE,
                )
            )
            accepted = has_condition and _preface_text_is_usable(negative_clause)
            result[target]["do_not_load_when"].append(
                _preface_evidence(
                    source="parent-root",
                    path=relative_skill,
                    line=line_number,
                    value=negative_clause,
                    accepted=accepted,
                    reason=None if accepted else "generic-or-empty-trigger",
                )
            )
        mode_match = re.match(r"^`([^`]+)`\s*:\s*load\s+only\b", item_text, re.IGNORECASE)
        if mode_match and Path(target).stem.casefold() == mode_match.group(1).strip().casefold():
            result[target]["reference_type"].append(
                _preface_evidence(
                    source="parent-root",
                    path=relative_skill,
                    line=line_number,
                    value="mode-contract",
                )
            )
            mode_targets[target] = (line_number, item_text)

    for rule_line, rule_text in group_mode_rules:
        for target in sorted(mode_targets):
            result[target]["do_not_load_when"].append(
                _preface_evidence(
                    source="parent-root",
                    path=relative_skill,
                    line=rule_line,
                    value=rule_text,
                )
            )
    return dict(result), errors


def _effective_preface(
    evidence_by_field: dict[str, list[dict]],
) -> dict:
    fields: dict[str, dict] = {}
    conflicts: list[dict] = []
    for field in PREFACE_FIELDS:
        evidence = sorted(
            list(evidence_by_field.get(field) or []),
            key=lambda item: (
                PREFACE_SOURCE_PRECEDENCE.index(item["source"]),
                item["path"],
                item["line"],
                item["value"],
            ),
        )
        accepted = [item for item in evidence if item.get("accepted")]
        selected = accepted[0] if accepted else None
        field_conflicts: list[dict] = []
        by_source: dict[str, list[dict]] = defaultdict(list)
        for item in evidence:
            by_source[item["source"]].append(item)
        for source in PREFACE_SOURCE_PRECEDENCE:
            source_items = by_source.get(source, [])
            if len(source_items) > 1:
                field_conflicts.append(
                    {
                        "field": field,
                        "code": "duplicate-source-evidence",
                        "message": f"multiple {source} declarations address the same field",
                        "evidence": source_items,
                    }
                )
        if selected and field in {"reference_type", "required_by", "required_output"}:
            selected_value = (
                _normalized_reference_type(selected["value"])
                if field == "reference_type"
                else _normalized_consumption_value(field, selected["value"])
            )
            for item in accepted[1:]:
                candidate_value = (
                    _normalized_reference_type(item["value"])
                    if field == "reference_type"
                    else _normalized_consumption_value(field, item["value"])
                )
                if candidate_value != selected_value:
                    field_conflicts.append(
                        {
                            "field": field,
                            "code": "inconsistent-source-evidence",
                            "message": "lower-priority evidence differs from the selected declaration",
                            "evidence": [selected, item],
                        }
                    )
        conflicts.extend(field_conflicts)
        has_invalid_declaration = any(
            not item.get("accepted")
            and item.get("source") in {"local", "reference-index"}
            for item in evidence
        )
        status = (
            "conflict"
            if field_conflicts
            else "resolved"
            if selected
            else "invalid"
            if has_invalid_declaration
            else "missing"
        )
        fields[field] = {
            "status": status,
            "value": selected["value"] if selected and status == "resolved" else None,
            "source": selected["source"] if selected and status == "resolved" else None,
            "evidence": evidence,
        }
    load = fields["load_when"]
    do_not_load = fields["do_not_load_when"]
    if (
        load["status"] == "resolved"
        and do_not_load["status"] == "resolved"
        and _normalized_preface_text(load["value"])
        == _normalized_preface_text(do_not_load["value"])
    ):
        conflict = {
            "field": "load_when/do_not_load_when",
            "code": "identical-opposite-evidence",
            "message": "the same condition is declared as both load and do-not-load evidence",
            "evidence": [load["evidence"][0], do_not_load["evidence"][0]],
        }
        conflicts.append(conflict)
        for field in (load, do_not_load):
            field["status"] = "conflict"
            field["value"] = None
            field["source"] = None
    return {**fields, "conflicts": conflicts}


def _heading_records(markdown: str) -> list[dict]:
    records: list[dict] = []
    for index, line, in_fence in _strip_fenced(markdown.splitlines()):
        if in_fence:
            continue
        match = HEADING_RE.match(line)
        if match:
            records.append(
                {
                    "level": len(match.group(1)),
                    "title": match.group(2).strip(),
                    "line": index + 1,
                    "_index": index,
                }
            )
    return records


def _table_item_indices(markdown: str) -> set[int]:
    result: set[int] = set()
    group: list[tuple[int, str]] = []

    def flush() -> None:
        if not group:
            return
        separator_positions = [
            position for position, (_index, line) in enumerate(group)
            if TABLE_SEPARATOR_RE.match(line.strip())
        ]
        start = separator_positions[0] + 1 if separator_positions else 1
        result.update(
            index
            for index, line in group[start:]
            if not TABLE_SEPARATOR_RE.match(line.strip())
        )
        group.clear()

    for index, line, in_fence in _strip_fenced(markdown.splitlines()):
        stripped = line.strip()
        if not in_fence and len(_split_markdown_table_row(stripped)) >= 2:
            group.append((index, line))
        else:
            flush()
    flush()
    return result


def _table_cell_headers(markdown: str) -> dict[tuple[int, int], str]:
    """Map data-cell positions to their table header without parsing Markdown broadly."""

    result: dict[tuple[int, int], str] = {}
    group: list[tuple[int, str]] = []

    def flush() -> None:
        if not group:
            return
        separator_positions = [
            position
            for position, (_index, line) in enumerate(group)
            if TABLE_SEPARATOR_RE.match(line.strip())
        ]
        if not separator_positions:
            group.clear()
            return
        separator = separator_positions[0]
        if separator == 0:
            group.clear()
            return
        headers = _split_markdown_table_row(group[separator - 1][1])
        for index, line in group[separator + 1 :]:
            if TABLE_SEPARATOR_RE.match(line.strip()):
                continue
            for cell_index, _cell in enumerate(_split_markdown_table_row(line)):
                if cell_index < len(headers):
                    result[(index, cell_index)] = headers[cell_index]
        group.clear()

    for index, line, in_fence in _strip_fenced(markdown.splitlines()):
        stripped = line.strip()
        if not in_fence and len(_split_markdown_table_row(stripped)) >= 2:
            group.append((index, line))
        else:
            flush()
    flush()
    return result


def _semantic_example_indices(
    markdown: str, *, include_negative_examples: bool = False
) -> set[int]:
    """Return lines governed by example, template, or negative-example headings."""

    lines = markdown.splitlines()
    headings = _heading_records(markdown)
    result: set[int] = set()
    for position, heading in enumerate(headings):
        if not SEMANTIC_EXAMPLE_HEADING_RE.search(heading["title"]):
            continue
        if include_negative_examples and re.search(
            r"\banti[- ]?patterns?\b", heading["title"], re.IGNORECASE
        ):
            continue
        end = len(lines)
        for later in headings[position + 1 :]:
            if later["level"] <= heading["level"]:
                end = later["_index"]
                break
        result.update(range(heading["_index"], end))
    return result


def _semantic_proof_limit_indices(markdown: str) -> set[int]:
    """Return lines governed by a proof/evidence-limit heading."""

    lines = markdown.splitlines()
    headings = _heading_records(markdown)
    result: set[int] = set()
    for position, heading in enumerate(headings):
        if not NEGATIVE_OR_PROOF_LIMIT_TABLE_HEADER_RE.search(heading["title"]):
            continue
        end = len(lines)
        for later in headings[position + 1 :]:
            if later["level"] <= heading["level"]:
                end = later["_index"]
                break
        result.update(range(heading["_index"], end))
    return result


def _semantic_normalize_sentence(sentence: str) -> str:
    normalized = unicodedata.normalize("NFKC", sentence).casefold()
    normalized = re.sub(r"[*_~]", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _semantic_fingerprint(finding: str, sentence: str) -> str:
    normalized = _semantic_normalize_sentence(sentence)
    return hashlib.sha256(f"{finding}\0{normalized}".encode("utf-8")).hexdigest()


def _semantic_candidate_id(finding: str, scope: str, fingerprint: str) -> str:
    expected_scope = "group" if finding in SEMANTIC_GROUP_FINDINGS else scope
    if finding not in SEMANTIC_FINDINGS:
        raise ValueError("semantic candidate finding is not declared")
    if finding in SEMANTIC_GROUP_FINDINGS:
        if scope != "group":
            raise ValueError("semantic group candidate scope must equal 'group'")
    elif not _is_canonical_semantic_path(scope):
        raise ValueError("semantic sentence candidate scope must be a canonical relative POSIX path")
    if not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
        raise ValueError("semantic candidate fingerprint must be lowercase sha256")
    payload = (
        "reference-semantic-candidate-v1\0"
        + finding
        + "\0"
        + expected_scope
        + "\0"
        + fingerprint
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _semantic_candidate_sort_key(item: object) -> tuple[str, str, str, str]:
    """Return the schema-v6 canonical order for semantic candidates."""

    if not isinstance(item, dict):
        return ("", "", "", "")
    return tuple(
        str(item.get(field, ""))
        for field in ("finding", "fingerprint", "path", "preview")
    )


def _semantic_evidence_fingerprint(occurrences: list[dict]) -> str:
    membership: list[tuple[str, str]] = []
    for occurrence in occurrences:
        path = occurrence.get("path")
        owner = occurrence.get("owner")
        if not _is_canonical_semantic_path(path):
            raise ValueError(
                "semantic evidence occurrence path must be a canonical relative POSIX path"
            )
        if not isinstance(owner, str) or not owner.strip():
            raise ValueError("semantic evidence occurrence owner must be non-blank")
        membership.append((path, owner))
    membership.sort()
    payload = "reference-semantic-evidence-v1\0" + "\0".join(
        f"{path}\0{owner}" for path, owner in membership
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _semantic_content_fingerprint(occurrences: list[dict]) -> str:
    content_membership: list[tuple[str, str, str]] = []
    for occurrence in occurrences:
        path = occurrence.get("path")
        owner = occurrence.get("owner")
        content_fingerprint = occurrence.get("content_fingerprint")
        if not _is_canonical_semantic_path(path):
            raise ValueError(
                "semantic content occurrence path must be a canonical relative POSIX path"
            )
        if not isinstance(owner, str) or not owner.strip():
            raise ValueError("semantic content occurrence owner must be non-blank")
        if not isinstance(content_fingerprint, str) or not re.fullmatch(
            r"[0-9a-f]{64}", content_fingerprint
        ):
            raise ValueError(
                "semantic content occurrence fingerprint must be lowercase sha256"
            )
        content_membership.append((path, owner, content_fingerprint))
    content_membership.sort()
    payload = "reference-semantic-content-v1\0" + "\0".join(
        f"{path}\0{owner}\0{content_fingerprint}"
        for path, owner, content_fingerprint in content_membership
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _semantic_occurrence_content_fingerprint(normalized_body: str) -> str:
    if not isinstance(normalized_body, str) or not normalized_body.strip():
        normalized_body = "<empty-content>"
    return hashlib.sha256(
        ("reference-semantic-occurrence-content-v1\0" + normalized_body).encode(
            "utf-8"
        )
    ).hexdigest()


def _is_canonical_semantic_path(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and value != "group"
        and "\0" not in value
        and "\\" not in value
        and not value.startswith("/")
        and re.match(r"^[A-Za-z]:/", value) is None
        and all(part not in {"", ".", ".."} for part in value.split("/"))
    )


def _semantic_sentence_slices(text: str) -> list[tuple[int, int, str]]:
    """Split logical Markdown text while retaining normalized character ranges."""

    result: list[tuple[int, int, str]] = []
    start = 0
    for separator in SEMANTIC_SENTENCE_SPLIT_RE.finditer(text):
        prefix = text[: separator.start()].casefold()
        if any(prefix.endswith(item) for item in SEMANTIC_SENTENCE_ABBREVIATIONS):
            continue
        # Do not split initials such as "A. Smith". The next true sentence
        # boundary remains available to the following iteration.
        if re.search(r"(?:^|\s)[a-z]\.$", prefix):
            continue
        end = separator.start()
        raw = text[start:end]
        left = len(raw) - len(raw.lstrip())
        right = len(raw.rstrip())
        if right > left:
            result.append((start + left, start + right, raw.strip()))
        start = separator.end()
    raw = text[start:]
    left = len(raw) - len(raw.lstrip())
    right = len(raw.rstrip())
    if right > left:
        result.append((start + left, start + right, raw.strip()))
    return result


def _semantic_logical_units(
    markdown: str, *, include_negative_examples: bool = False
) -> list[dict]:
    """Build paragraph, list-item, and table-cell units across physical wraps."""

    lines = markdown.splitlines()
    annotated = {index: in_fence for index, _line, in_fence in _strip_fenced(lines)}
    example_indices = _semantic_example_indices(
        markdown, include_negative_examples=include_negative_examples
    )
    proof_limit_indices = _semantic_proof_limit_indices(markdown)
    heading_indices = {item["_index"] for item in _heading_records(markdown)}
    table_items = _table_item_indices(markdown)
    table_headers = _table_cell_headers(markdown)
    heading_contexts = _heading_contexts(markdown)
    units: list[dict] = []
    current: dict | None = None

    def flush() -> None:
        nonlocal current
        if current and current["pieces"]:
            units.append(current)
        current = None

    def start_unit(kind: str, text: str, index: int, contexts: set[str] | None = None) -> None:
        nonlocal current
        current = {
            "kind": kind,
            "pieces": [(text, index + 1)],
            "contexts": {
                *(contexts or ()),
                f"unit-kind:{kind}",
                *(
                    f"heading:{_semantic_context_label(title)}"
                    for title in heading_contexts.get(index, [])
                ),
            },
        }
        if index in proof_limit_indices:
            current["contexts"].add("proof_limit_heading")

    for index, line in enumerate(lines):
        stripped = line.strip()
        if (
            not stripped
            or annotated.get(index, False)
            or index in example_indices
            or index in heading_indices
            or TABLE_SEPARATOR_RE.match(stripped)
        ):
            flush()
            continue

        if len(_split_markdown_table_row(stripped)) >= 2:
            flush()
            if index not in table_items:
                continue
            for cell_index, cell in enumerate(_split_markdown_table_row(stripped)):
                fragment = cell.strip()
                if not fragment:
                    continue
                contexts: set[str] = set()
                header = table_headers.get((index, cell_index), "")
                if header:
                    contexts.add(
                        f"table-header:{_semantic_context_label(header)}"
                    )
                if NEGATIVE_OR_PROOF_LIMIT_TABLE_HEADER_RE.search(header):
                    contexts.add("negative_or_proof_limit_table_cell")
                start_unit("table-cell", fragment, index, contexts)
                flush()
            continue

        list_match = LIST_ITEM_RE.match(line)
        if list_match:
            flush()
            start_unit("list-item", list_match.group(1).strip(), index)
            continue

        fragment = re.sub(r"^>\s*", "", stripped)
        if current is None:
            start_unit("paragraph", fragment, index)
        else:
            current["pieces"].append((fragment, index + 1))
            if index in proof_limit_indices:
                current["contexts"].add("proof_limit_heading")

    flush()
    return units


def _semantic_sentence_occurrences(
    document: dict, *, include_negative_examples: bool = False
) -> list[dict]:
    """Extract logical sentences with their physical source ranges and context."""

    occurrences: list[dict] = []

    for unit in _semantic_logical_units(
        str(document.get("governed_text", document["text"])),
        include_negative_examples=include_negative_examples,
    ):
        text = ""
        piece_ranges: list[tuple[int, int, int]] = []
        for piece, line in unit["pieces"]:
            normalized = re.sub(r"\s+", " ", piece).strip()
            if not normalized:
                continue
            if text:
                text += " "
            start = len(text)
            text += normalized
            piece_ranges.append((start, len(text), line))

        for start, end, sentence in _semantic_sentence_slices(text):
            if len(sentence) < 12:
                continue
            covered_lines = [
                line
                for piece_start, piece_end, line in piece_ranges
                if piece_end > start and piece_start < end
            ]
            if not covered_lines:
                continue
            contexts = set(unit["contexts"])
            preceding = text[:start].strip()
            if preceding and ABSOLUTE_CONDITIONAL_RE.search(preceding):
                contexts.add("preceding_conditional_language")
            if preceding and REFERENCE_SCOPE_ONLY_RE.search(preceding):
                contexts.add("preceding_reference_loading_scope")
            if preceding and NEGATIVE_OR_PROOF_LIMIT_TABLE_HEADER_RE.search(preceding):
                contexts.add("preceding_proof_limit_context")
            line_offset = int(document.get("line_offset", 0) or 0)
            line_range = {
                "start": min(covered_lines) + line_offset,
                "end": max(covered_lines) + line_offset,
            }
            occurrences.append(
                {
                    "path": str(document["path"]),
                    "layer": str(document["layer"]),
                    "owner": str(document["owner"]),
                    "line": line_range["start"],
                    "lines": line_range,
                    "sentence": sentence,
                    **({"semantic_contexts": sorted(contexts)} if contexts else {}),
                }
            )
    return occurrences


def _absolute_signals(sentence: str) -> list[str]:
    return sorted(
        {
            match.group(0).casefold().replace(" ", "-")
            for match in ABSOLUTE_SIGNAL_RE.finditer(sentence)
        }
    )


def _semantic_context_label(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = re.sub(r"[`*_~]", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip(" :")
    return normalized


def _semantic_context_value(contexts: set[str], prefix: str) -> str | None:
    values = sorted(
        item[len(prefix) :]
        for item in contexts
        if item.startswith(prefix) and item[len(prefix) :]
    )
    return values[0] if len(values) == 1 else None


def _absolute_literal_or_compound(sentence: str) -> bool:
    absolute_matches = list(ABSOLUTE_SIGNAL_RE.finditer(sentence))
    if not absolute_matches:
        return False
    covered_spans = [
        match.span() for match in FIXED_INLINE_CODE_RE.finditer(sentence)
    ] + [
        match.span() for match in ABSOLUTE_LITERAL_COMPOUND_RE.finditer(sentence)
    ]
    return all(
        any(start <= match.start() and match.end() <= end for start, end in covered_spans)
        for match in absolute_matches
    )


def _absolute_exact_table_context(contexts: set[str]) -> bool:
    return (
        "unit-kind:table-cell" in contexts
        and _semantic_context_value(contexts, "table-header:")
        in ABSOLUTE_TABLE_CONTEXT_HEADERS
    )


def _absolute_clause_ranges(
    sentence: str,
    splitter: re.Pattern[str] = ABSOLUTE_AUTHORITY_CLAUSE_SPLIT_RE,
) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    start = 0
    for boundary in splitter.finditer(sentence):
        if boundary.start() > start:
            ranges.append((start, boundary.start()))
        start = boundary.end()
    if start < len(sentence):
        ranges.append((start, len(sentence)))
    return ranges


def _absolute_clause_local_proof_limit(sentence: str) -> bool:
    matches = list(ABSOLUTE_SIGNAL_RE.finditer(sentence))
    if not matches:
        return False
    clause_ranges = _absolute_clause_ranges(
        sentence, ABSOLUTE_PROOF_CLAUSE_SPLIT_RE
    )
    for match in matches:
        clause_range = next(
            (
                (start, end)
                for start, end in clause_ranges
                if start <= match.start() and match.end() <= end
            ),
            None,
        )
        if clause_range is None:
            return False
        start, _end = clause_range
        prefix = sentence[start : match.start()]
        governors = list(ABSOLUTE_PROOF_VERB_RE.finditer(prefix))
        if not governors:
            return False
        governor = governors[-1]
        signal = match.group(0).casefold()
        if signal in {"must", "mandatory", "non-negotiable", "non negotiable", "always", "never"}:
            return False
        if signal != "only":
            governor_start = governor.start()
            governing_phrase = prefix[
                max(0, governor_start - 16) : governor.end()
            ]
            if not ABSOLUTE_NEAR_NEGATION_RE.search(governing_phrase):
                return False
    return True


def _absolute_permission_token(
    sentence: str,
    match: re.Match[str],
    clause_range: tuple[int, int],
    action_re: re.Pattern[str] = ABSOLUTE_PROFILE_ACTION_RE,
) -> bool:
    start, end = clause_range
    clause = sentence[start:end]
    relative_start = match.start() - start
    relative_end = match.end() - start
    signal = match.group(0).casefold()
    if signal == "only":
        return bool(action_re.search(clause))
    tail = clause[relative_end:]
    if signal == "never":
        return bool(action_re.search(tail))
    if signal == "must":
        return bool(
            re.match(r"\s+not\b", tail, re.IGNORECASE)
            and action_re.search(tail)
        )
    return False


def _absolute_profile_subject_for_clause(
    sentence: str,
    clause_range: tuple[int, int],
    preceding_ranges: list[tuple[int, int]],
) -> bool:
    start, end = clause_range
    clause = sentence[start:end]
    if ABSOLUTE_PROFILE_SUBJECT_RE.search(clause):
        return True
    if not re.match(
        r"\s*(?:it|they|this\s+profile|the\s+(?:agent|profile)|never|only|must\s+not)\b",
        clause,
        re.IGNORECASE,
    ):
        return False
    return any(
        ABSOLUTE_PROFILE_SUBJECT_RE.search(sentence[prior_start:prior_end])
        for prior_start, prior_end in preceding_ranges
    )


def _absolute_explicit_profile_authority(sentence: str) -> bool:
    matches = list(ABSOLUTE_SIGNAL_RE.finditer(sentence))
    if not matches:
        return False
    clause_ranges = _absolute_clause_ranges(sentence)
    for match in matches:
        position = next(
            (
                index
                for index, (start, end) in enumerate(clause_ranges)
                if start <= match.start() and match.end() <= end
            ),
            None,
        )
        if position is None:
            return False
        clause_range = clause_ranges[position]
        if not _absolute_profile_subject_for_clause(
            sentence, clause_range, clause_ranges[:position]
        ) or not _absolute_permission_token(sentence, match, clause_range):
            return False
    return True


def _absolute_boundary_record_authority(
    sentence: str, contexts: set[str]
) -> bool:
    if (
        "unit-kind:table-cell" not in contexts
        or _semantic_context_value(contexts, "table-header:") != "boundary record"
    ):
        return False
    matches = list(ABSOLUTE_SIGNAL_RE.finditer(sentence))
    clause_ranges = _absolute_clause_ranges(sentence)
    return bool(matches) and all(
        (
            clause_range := next(
                (
                    item
                    for item in clause_ranges
                    if item[0] <= match.start() and match.end() <= item[1]
                ),
                None,
            )
        )
        is not None
        and ABSOLUTE_BOUNDARY_AUTHORITY_RE.search(
            sentence[clause_range[0] : clause_range[1]]
        )
        and _absolute_permission_token(
            sentence, match, clause_range, ABSOLUTE_BOUNDARY_ACTION_RE
        )
        for match in matches
    )


def _absolute_map_every_evidence_closure(
    sentence: str, contexts: set[str]
) -> bool:
    reference_kind = _semantic_context_value(contexts, "reference-kind:")
    matches = list(ABSOLUTE_SIGNAL_RE.finditer(sentence))
    if (
        reference_kind not in ABSOLUTE_MAP_REFERENCE_KINDS
        or len(matches) != 1
        or matches[0].group(0).casefold() != "every"
        or re.match(r"^\s*Map\s+every\b", sentence, re.IGNORECASE) is None
    ):
        return False
    mapping = re.match(
        r"^\s*Map\s+every\b(?P<source>.+?)\bto\b(?P<destination>.+?)\s*[.!]?$",
        sentence,
        re.IGNORECASE,
    )
    if mapping is not None:
        destination = mapping.group("destination").strip().rstrip(".!?").strip()
        components = ABSOLUTE_MAP_DESTINATION_LIST_SPLIT_RE.split(destination)
        return bool(components) and all(
            component
            and ABSOLUTE_MAP_DESTINATION_COMPONENT_RE.fullmatch(component)
            for component in components
        )
    in_scope = re.match(
        r"^\s*Map\s+every\b(?P<source>.+?)\bin\s+scope\s*[.!]?$",
        sentence,
        re.IGNORECASE,
    )
    return bool(
        in_scope is not None
        and ABSOLUTE_MAP_IN_SCOPE_OBJECT_RE.search(in_scope.group("source"))
    )


def _absolute_short_classification_fragment(
    sentence: str, contexts: set[str]
) -> bool:
    header = _semantic_context_value(contexts, "table-header:")
    if (
        "unit-kind:table-cell" not in contexts
        or header not in ABSOLUTE_CLASSIFICATION_HEADERS
    ):
        return False
    normalized = sentence.strip().rstrip(".").strip()
    grammar = ABSOLUTE_CLASSIFICATION_GRAMMARS[header]
    return bool(grammar.fullmatch(normalized))


def _fixed_number_signals(sentence: str) -> list[str]:
    signals: set[str] = set()
    without_inline_code = FIXED_INLINE_CODE_RE.sub("", sentence)
    protected_thousands = FIXED_THOUSANDS_NUMBER_RE.sub(
        lambda match: match.group(0).replace(
            ",", FIXED_THOUSANDS_COMMA_SENTINEL
        ),
        without_inline_code,
    )
    for clause in FIXED_CLAUSE_SPLIT_RE.split(protected_thousands):
        clause = clause.replace(FIXED_THOUSANDS_COMMA_SENTINEL, ",")
        special_signals = {
            signal
            for signal, pattern in (
                ("maturity-count", FIXED_MATURITY_COUNT_RE),
                ("option-count", FIXED_OPTION_COUNT_RE),
                ("organization-window", FIXED_ORGANIZATION_WINDOW_RE),
                ("score-threshold", FIXED_SCORE_THRESHOLD_RE),
            )
            if pattern.search(clause)
        }
        if not clause.strip() or (
            FIXED_EXCLUDED_PROSE_RE.search(clause) and not special_signals
        ):
            continue
        signals.update(special_signals)
        masked = FIXED_DATE_RE.sub("", clause)
        masked = FIXED_STANDARD_VERSION_RE.sub("", masked)
        masked = FIXED_ALGEBRA_IDENTIFIER_RE.sub("", masked)
        masked = FIXED_HTTP_STATUS_RE.sub("", masked)
        if FIXED_MONEY_RE.search(masked):
            signals.add("money")
        if FIXED_TIME_RE.search(masked):
            signals.add("time")
        if FIXED_PERCENT_RE.search(masked):
            signals.add("percent")
        if FIXED_POLICY_VALUE_RE.search(masked):
            signals.add("cost-slo-threshold")
    return sorted(signals)


def _heading_contexts(markdown: str) -> dict[int, list[str]]:
    """Map physical lines to the active Markdown heading stack."""

    lines = markdown.splitlines()
    headings = {item["_index"]: item for item in _heading_records(markdown)}
    active: dict[int, str] = {}
    result: dict[int, list[str]] = {}
    for index in range(len(lines)):
        heading = headings.get(index)
        if heading:
            level = int(heading["level"])
            active = {key: value for key, value in active.items() if key < level}
            active[level] = str(heading["title"])
        result[index] = [active[key] for key in sorted(active) if key >= 2]
    return result


def _normalize_owner_text(text: str, owner: str, *, structural: bool) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    full_variants = {
        owner.casefold(),
        owner.replace("-", " ").casefold(),
        owner.replace("-", "_").casefold(),
    }
    for variant in sorted(full_variants, key=len, reverse=True):
        normalized = re.sub(
            rf"(?<![a-z0-9]){re.escape(variant)}(?![a-z0-9])",
            "<owner>",
            normalized,
        )
    if structural:
        for token in sorted(
            {part for part in re.split(r"[-_\s]+", owner.casefold()) if len(part) >= 3},
            key=len,
            reverse=True,
        ):
            normalized = re.sub(
                rf"(?<![a-z0-9]){re.escape(token)}(?![a-z0-9])",
                "<domain>",
                normalized,
            )
    return normalized


def _normalize_duplicate_line(line: str, owner: str) -> str:
    stripped = line.strip()
    list_match = LIST_ITEM_RE.match(line)
    if list_match:
        stripped = "- " + list_match.group(1).strip()
    stripped = re.sub(r"[*_~`]", "", stripped)
    stripped = re.sub(r"\s*\|\s*", " | ", stripped)
    stripped = re.sub(r"\s+", " ", stripped).strip()
    return _normalize_owner_text(stripped, owner, structural=False)


def _exact_block_occurrences(documents: list[dict]) -> list[dict]:
    occurrences: list[dict] = []
    for document in sorted(documents, key=lambda item: str(item["path"])):
        if document.get("kind") in {"index", "template"}:
            continue
        markdown = str(document["text"])
        lines = markdown.splitlines()
        fenced = {index: in_fence for index, _line, in_fence in _strip_fenced(lines)}
        examples = _semantic_example_indices(markdown)
        headings = {item["_index"] for item in _heading_records(markdown)}
        contexts = _heading_contexts(markdown)
        current: list[tuple[int, str]] = []

        def flush() -> None:
            if not current:
                return
            active_titles = contexts.get(current[0][0], [])
            decision_titles = [
                title for title in active_titles if DUPLICATE_DECISION_HEADING_RE.search(title)
            ]
            raw_lines = [line for _index, line in current]
            normalized_lines = [
                _normalize_duplicate_line(line, str(document["owner"]))
                for line in raw_lines
                if not TABLE_SEPARATOR_RE.match(line.strip())
            ]
            separator_positions = [
                position
                for position, line in enumerate(raw_lines)
                if TABLE_SEPARATOR_RE.match(line.strip())
            ]
            content_raw_lines = (
                raw_lines[separator_positions[0] + 1 :]
                if separator_positions
                else raw_lines
            )
            normalized_content_lines = [
                _normalize_duplicate_line(line, str(document["owner"]))
                for line in content_raw_lines
                if not TABLE_SEPARATOR_RE.match(line.strip())
            ]
            nontrivial = [
                line
                for line in normalized_lines
                if len(re.sub(r"[^a-z0-9]+", "", line)) >= 10
            ]
            link_only = all(
                len(re.sub(r"[^a-z0-9]+", "", MARKDOWN_LINK_RE.sub("", line))) < 8
                for line in raw_lines
            )
            if (
                decision_titles
                and len(nontrivial) >= EXACT_DUPLICATE_MIN_LINES
                and not link_only
            ):
                normalized_heading = _normalize_owner_text(
                    decision_titles[-1], str(document["owner"]), structural=False
                )
                normalized = "heading: " + normalized_heading + "\n" + "\n".join(
                    normalized_lines
                )
                tokens = count_o200k_base_tokens(normalized)
                if tokens >= EXACT_DUPLICATE_MIN_TOKENS:
                    occurrences.append(
                        {
                            "fingerprint": hashlib.sha256(
                                ("exact-normalized-block\0" + normalized).encode("utf-8")
                            ).hexdigest(),
                            "content_fingerprint": _semantic_occurrence_content_fingerprint(
                                "\n".join(normalized_content_lines)
                            ),
                            "path": str(document["path"]),
                            "layer": str(document["layer"]),
                            "owner": str(document["owner"]),
                            "lines": {
                                "start": current[0][0] + 1,
                                "end": current[-1][0] + 1,
                            },
                            "tokens": tokens,
                            "preview": re.sub(r"\s+", " ", " ".join(raw_lines))[:280],
                        }
                    )
            current.clear()

        for index, line in enumerate(lines):
            stripped = line.strip()
            if (
                not stripped
                or fenced.get(index, False)
                or index in examples
                or index in headings
                or REFERENCE_PREFACE_RE.match(line)
            ):
                flush()
                continue
            current.append((index, line))
        flush()
    return occurrences


def _group_duplicate_occurrences(
    finding: str,
    occurrences: list[dict],
    *,
    require_distinct_owners: bool,
) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for occurrence in occurrences:
        if not _is_canonical_semantic_path(occurrence.get("path")):
            raise ValueError(
                "semantic group occurrence path must be a canonical relative POSIX path"
            )
        grouped[str(occurrence["fingerprint"])].append(occurrence)
    candidates: list[dict] = []
    for fingerprint, rows in sorted(grouped.items()):
        rows = sorted(
            rows,
            key=lambda item: (
                item["path"],
                item["lines"]["start"],
                item["lines"]["end"],
            ),
        )
        paths = {item["path"] for item in rows}
        owners = {item["owner"] for item in rows}
        if len(paths) < 2 or (require_distinct_owners and len(owners) < 2):
            continue
        canonical = rows[0]
        occurrence_rows = [
            {
                key: item[key]
                for key in (
                    "fingerprint",
                    "content_fingerprint",
                    "path",
                    "layer",
                    "owner",
                    "lines",
                    "tokens",
                    "preview",
                )
            }
            for item in rows
        ]
        signals = sorted({str(item.get("shape_kind", "normalized-exact")) for item in rows})
        candidates.append(
            {
                "finding": finding,
                "fingerprint": fingerprint,
                "scope": "group",
                "candidate_id": _semantic_candidate_id(
                    finding, "group", fingerprint
                ),
                "path": "group",
                "layer": "group",
                "owner": "group",
                "skill_owner": "group",
                "tokens": int(canonical["tokens"]),
                "total_tokens": sum(int(item["tokens"]) for item in rows),
                "signals": signals,
                "preview": canonical["preview"],
                "detector_status": "candidate",
                "occurrence_count": len(rows),
                "distinct_path_count": len(paths),
                "owner_count": len(owners),
                "occurrences": occurrence_rows,
                "evidence_fingerprint": _semantic_evidence_fingerprint(
                    occurrence_rows
                ),
                "content_fingerprint": _semantic_content_fingerprint(
                    occurrence_rows
                ),
            }
        )
    return candidates


def _yaml_template_occurrences(document: dict) -> list[dict]:
    markdown = str(document["text"])
    lines = markdown.splitlines()
    contexts = _heading_contexts(markdown)
    examples = _semantic_example_indices(markdown)
    result: list[dict] = []
    index = 0
    while index < len(lines):
        match = YAML_FENCE_START_RE.match(lines[index])
        if not match or index in examples:
            index += 1
            continue
        marker = match.group(1)[0]
        end = index + 1
        while end < len(lines) and not lines[end].lstrip().startswith(marker * 3):
            end += 1
        stack: list[tuple[int, str]] = []
        paths: list[str] = []
        for line in lines[index + 1 : end]:
            key_match = YAML_KEY_RE.match(line)
            if not key_match:
                continue
            indent = len(key_match.group(1).replace("\t", "    "))
            key = _normalize_owner_text(
                key_match.group(2).replace("-", "_"),
                str(document["owner"]),
                structural=True,
            )
            while stack and stack[-1][0] >= indent:
                stack.pop()
            if not stack:
                key = "<root>"
            path = ".".join([item[1] for item in stack] + [key])
            paths.append(path)
            stack.append((indent, key))
        unique_paths = sorted(set(paths))
        if len(unique_paths) >= TEMPLATE_YAML_MIN_FIELDS:
            structure = "yaml-key-path-shape\n" + "\n".join(unique_paths)
            normalized_values: list[str] = []
            for body_line in lines[index + 1 : end]:
                key_match = YAML_KEY_RE.match(body_line)
                if key_match:
                    value = body_line[key_match.end() :].strip()
                    if value:
                        normalized_values.append(
                            _normalize_duplicate_line(
                                value, str(document["owner"])
                            )
                        )
                    continue
                stripped_body = body_line.strip()
                if stripped_body and not stripped_body.startswith("#"):
                    normalized_values.append(
                        _normalize_duplicate_line(
                            stripped_body, str(document["owner"])
                        )
                    )
            result.append(
                {
                    "fingerprint": hashlib.sha256(
                        ("templated-block\0" + structure).encode("utf-8")
                    ).hexdigest(),
                    "content_fingerprint": _semantic_occurrence_content_fingerprint(
                        "\n".join(normalized_values)
                    ),
                    "shape_kind": "yaml-key-path-shape",
                    "path": str(document["path"]),
                    "layer": str(document["layer"]),
                    "owner": str(document["owner"]),
                    "lines": {"start": index + 1, "end": min(end + 1, len(lines))},
                    "tokens": count_o200k_base_tokens(structure),
                    "field_count": len(unique_paths),
                    "preview": re.sub(
                        r"\s+", " ", " ".join(lines[index : min(end + 1, len(lines))])
                    )[:280],
                    "heading_context": contexts.get(index, []),
                }
            )
        index = end + 1
    return result


def _template_section_kind(titles: list[str]) -> str | None:
    joined = " ".join(titles).casefold()
    for kind, pattern in (
        ("tool-permission", r"tool\s+permission"),
        ("handoff", r"handoff"),
        ("closure", r"closure"),
        ("output", r"output"),
        ("evidence", r"evidence"),
    ):
        if re.search(pattern, joined):
            return kind
    return None


def _markdown_template_occurrences(document: dict) -> list[dict]:
    markdown = str(document["text"])
    lines = markdown.splitlines()
    fenced = {index: in_fence for index, _line, in_fence in _strip_fenced(lines)}
    examples = _semantic_example_indices(markdown)
    contexts = _heading_contexts(markdown)
    result: list[dict] = []

    group: list[tuple[int, str]] = []

    def flush_table() -> None:
        if not group:
            return
        separators = [
            position
            for position, (_index, line) in enumerate(group)
            if TABLE_SEPARATOR_RE.match(line.strip())
        ]
        if not separators or separators[0] == 0:
            group.clear()
            return
        separator = separators[0]
        header_index, header_line = group[separator - 1]
        kind = _template_section_kind(contexts.get(header_index, []))
        headers = _split_markdown_table_row(header_line)
        data_rows = group[separator + 1 :]
        minimum_columns = 2 if kind == "tool-permission" else 3
        if kind and len(headers) >= minimum_columns and len(data_rows) >= 2:
            normalized_headers = [
                _normalize_owner_text(cell, str(document["owner"]), structural=True)
                for cell in headers
            ]
            structure = f"markdown-table-schema:{kind}\n" + "\n".join(
                normalized_headers
            )
            normalized_rows = [
                " | ".join(
                    _normalize_duplicate_line(cell, str(document["owner"]))
                    for cell in _split_markdown_table_row(line)
                )
                for _index, line in data_rows
                if not TABLE_SEPARATOR_RE.match(line.strip())
            ]
            result.append(
                {
                    "fingerprint": hashlib.sha256(
                        ("templated-block\0" + structure).encode("utf-8")
                    ).hexdigest(),
                    "content_fingerprint": _semantic_occurrence_content_fingerprint(
                        "\n".join(normalized_rows)
                    ),
                    "shape_kind": "markdown-table-schema",
                    "path": str(document["path"]),
                    "layer": str(document["layer"]),
                    "owner": str(document["owner"]),
                    "lines": {"start": group[0][0] + 1, "end": group[-1][0] + 1},
                    "tokens": count_o200k_base_tokens(structure),
                    "field_count": len(headers),
                    "preview": re.sub(
                        r"\s+", " ", " ".join(line for _index, line in group)
                    )[:280],
                }
            )
        group.clear()

    for index, line in enumerate(lines):
        stripped = line.strip()
        if (
            not fenced.get(index, False)
            and index not in examples
            and len(_split_markdown_table_row(stripped)) >= 2
        ):
            group.append((index, line))
        else:
            flush_table()
    flush_table()

    fields: list[tuple[int, str]] = []

    def flush_fields() -> None:
        if len(fields) < TEMPLATE_OUTPUT_MIN_FIELDS:
            fields.clear()
            return
        kind = _template_section_kind(contexts.get(fields[0][0], []))
        if kind:
            normalized_fields = [
                _normalize_owner_text(field, str(document["owner"]), structural=True)
                for _index, field in fields
            ]
            structure = f"markdown-output-fields:{kind}\n" + "\n".join(
                normalized_fields
            )
            normalized_bodies = [
                _normalize_duplicate_line(
                    lines[index][SCHEMA_FIELD_RE.match(lines[index]).end() :],
                    str(document["owner"]),
                )
                for index, _field in fields
            ]
            result.append(
                {
                    "fingerprint": hashlib.sha256(
                        ("templated-block\0" + structure).encode("utf-8")
                    ).hexdigest(),
                    "content_fingerprint": _semantic_occurrence_content_fingerprint(
                        "\n".join(normalized_bodies)
                    ),
                    "shape_kind": "markdown-output-fields",
                    "path": str(document["path"]),
                    "layer": str(document["layer"]),
                    "owner": str(document["owner"]),
                    "lines": {"start": fields[0][0] + 1, "end": fields[-1][0] + 1},
                    "tokens": count_o200k_base_tokens(structure),
                    "field_count": len(fields),
                    "preview": ", ".join(field for _index, field in fields)[:280],
                }
            )
        fields.clear()

    for index, line in enumerate(lines):
        if fenced.get(index, False) or index in examples:
            flush_fields()
            continue
        match = SCHEMA_FIELD_RE.match(line)
        if match:
            fields.append((index, match.group(1).strip()))
        else:
            flush_fields()
    flush_fields()
    return result


def _duplicate_semantic_candidates(documents: list[dict]) -> list[dict]:
    exact_occurrences = _exact_block_occurrences(documents)
    exact_candidates = _group_duplicate_occurrences(
        "exact_normalized_duplicate_block",
        exact_occurrences,
        require_distinct_owners=False,
    )
    exact_spans = {
        (item["path"], item["lines"]["start"], item["lines"]["end"])
        for candidate in exact_candidates
        for item in candidate["occurrences"]
    }
    template_occurrences: list[dict] = []
    for document in documents:
        if document.get("kind") in {"index", "template"}:
            continue
        template_occurrences.extend(_yaml_template_occurrences(document))
        template_occurrences.extend(_markdown_template_occurrences(document))
    template_occurrences = [
        item
        for item in template_occurrences
        if (item["path"], item["lines"]["start"], item["lines"]["end"])
        not in exact_spans
    ]
    templated_candidates = _group_duplicate_occurrences(
        "templated_block_candidate",
        template_occurrences,
        require_distinct_owners=True,
    )
    return exact_candidates + templated_candidates


def _fold_sentence_semantic_candidates(rows: list[dict]) -> list[dict]:
    """Fold line-sensitive sentence hits into stable path-scoped candidates."""

    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in rows:
        if not _is_canonical_semantic_path(row.get("path")):
            raise ValueError(
                "semantic sentence occurrence path must be a canonical relative POSIX path"
            )
        grouped[(row["finding"], row["path"], row["fingerprint"])].append(row)
    candidates: list[dict] = []
    for (finding, path, fingerprint), occurrences in sorted(grouped.items()):
        occurrences = sorted(
            occurrences,
            key=lambda item: (
                item["lines"]["start"],
                item["lines"]["end"],
                item["preview"],
            ),
        )
        canonical = occurrences[0]
        occurrence_rows: list[dict] = []
        for occurrence in occurrences:
            row = {
                "path": occurrence["path"],
                "layer": occurrence["layer"],
                "owner": occurrence["owner"],
                "lines": dict(occurrence["lines"]),
                "tokens": int(occurrence["tokens"]),
                "signals": list(occurrence["signals"]),
                "preview": occurrence["preview"],
                "detector_status": occurrence["detector_status"],
            }
            if occurrence.get("downgrade_reason"):
                row["downgrade_reason"] = occurrence["downgrade_reason"]
            if occurrence.get("semantic_contexts"):
                row["semantic_contexts"] = list(occurrence["semantic_contexts"])
            occurrence_rows.append(row)
        detector_status = (
            "candidate"
            if any(row["detector_status"] == "candidate" for row in occurrence_rows)
            else "downgraded"
        )
        downgrade_reasons = sorted(
            {
                row["downgrade_reason"]
                for row in occurrence_rows
                if row.get("downgrade_reason")
            }
        )
        candidate = {
            "finding": finding,
            "fingerprint": fingerprint,
            "scope": path,
            "candidate_id": _semantic_candidate_id(finding, path, fingerprint),
            "path": path,
            "layer": canonical["layer"],
            "owner": canonical["owner"],
            "skill_owner": canonical["owner"],
            "tokens": int(canonical["tokens"]),
            "total_tokens": sum(row["tokens"] for row in occurrence_rows),
            "signals": sorted(
                {signal for row in occurrence_rows for signal in row["signals"]}
            ),
            "preview": canonical["preview"],
            "detector_status": detector_status,
            "occurrence_count": len(occurrence_rows),
            "occurrences": occurrence_rows,
            "evidence_fingerprint": None,
            "content_fingerprint": None,
        }
        if downgrade_reasons:
            candidate["downgrade_reasons"] = downgrade_reasons
        candidates.append(candidate)
    return candidates


def _load_reference_semantic_dispositions() -> tuple[dict, list[str]]:
    _require_safe_source_path(
        SKILL_CONTENT_EXCEPTIONS_FILE,
        allowed_root=ROOT / "config",
        source="registry",
        expect_directory=False,
    )
    source = _repository_relative_path(SKILL_CONTENT_EXCEPTIONS_FILE)
    try:
        data = load_yaml_file(SKILL_CONTENT_EXCEPTIONS_FILE)
    except ValidationProblem as exc:
        return {"schema_version": None, "entries": []}, [str(exc)]
    if not isinstance(data, dict):
        return {"schema_version": None, "entries": []}, [f"{source}: must be a mapping"]
    if "reference_semantic_exceptions" in data:
        return {"schema_version": None, "entries": []}, [
            f"{source}: legacy reference_semantic_exceptions is forbidden"
        ]
    if "reference_semantic_dispositions" not in data:
        return {"schema_version": None, "entries": []}, [
            f"{source}: missing reference_semantic_dispositions"
        ]
    contract = data.get("reference_semantic_dispositions")
    if not isinstance(contract, dict):
        return {"schema_version": None, "entries": []}, [
            f"{source}: reference_semantic_dispositions must be a mapping"
        ]
    errors: list[str] = []
    if set(contract) != {"schema_version", "entries"}:
        errors.append(
            f"{source}: reference_semantic_dispositions must contain exactly schema_version and entries"
        )
    schema_version = contract.get("schema_version")
    if schema_version != SEMANTIC_DISPOSITION_SCHEMA_VERSION:
        errors.append(
            f"{source}: reference_semantic_dispositions.schema_version must equal {SEMANTIC_DISPOSITION_SCHEMA_VERSION}"
        )
    entries = contract.get("entries")
    if not isinstance(entries, list):
        errors.append(
            f"{source}: reference_semantic_dispositions.entries must be a list"
        )
        entries = []
    return {"schema_version": schema_version, "entries": entries}, errors


def _validate_reference_semantic_dispositions(
    candidates: list[dict],
    entries: object,
    evaluation_date: date,
    *,
    require_applied: bool,
) -> tuple[list[dict], dict[int, int], list[str]]:
    """Validate exact semantic governance decisions against stable candidates."""

    if not isinstance(entries, list):
        return [], {}, ["reference_semantic_dispositions.entries must be a list"]
    normalized_entries: list[dict] = []
    matched_candidate_by_entry: dict[int, int] = {}
    errors: list[str] = []
    seen_ids: set[str] = set()
    candidate_by_id: dict[str, int] = {}
    for candidate_index, candidate in enumerate(candidates):
        finding = candidate.get("finding")
        fingerprint = candidate.get("fingerprint")
        path = candidate.get("path")
        expected_scope = "group" if finding in SEMANTIC_GROUP_FINDINGS else path
        candidate_id = candidate.get("candidate_id")
        if not isinstance(candidate_id, str) or not re.fullmatch(
            r"[0-9a-f]{64}", candidate_id
        ):
            errors.append(
                f"semantic candidate[{candidate_index}]: candidate_id must be lowercase sha256"
            )
            continue
        valid_scope = (
            expected_scope == "group"
            if finding in SEMANTIC_GROUP_FINDINGS
            else _is_canonical_semantic_path(expected_scope)
        )
        try:
            expected_candidate_id = _semantic_candidate_id(
                finding, expected_scope, fingerprint
            )
        except (TypeError, ValueError):
            expected_candidate_id = None
        if (
            finding not in SEMANTIC_FINDINGS
            or not isinstance(fingerprint, str)
            or not re.fullmatch(r"[0-9a-f]{64}", fingerprint)
            or not valid_scope
            or candidate.get("scope") != expected_scope
            or candidate_id != expected_candidate_id
        ):
            errors.append(
                f"semantic candidate[{candidate_index}]: stable identity fields do not match candidate_id"
            )
            continue
        occurrences = candidate.get("occurrences")
        try:
            expected_evidence = (
                _semantic_evidence_fingerprint(occurrences)
                if finding in SEMANTIC_GROUP_FINDINGS
                and isinstance(occurrences, list)
                else None
            )
        except ValueError as exc:
            errors.append(f"semantic candidate[{candidate_index}]: {exc}")
            continue
        if candidate.get("evidence_fingerprint") != expected_evidence:
            errors.append(
                f"semantic candidate[{candidate_index}]: evidence_fingerprint does not match current membership"
            )
            continue
        try:
            expected_content = (
                _semantic_content_fingerprint(occurrences)
                if finding in SEMANTIC_GROUP_FINDINGS
                and isinstance(occurrences, list)
                else None
            )
        except ValueError as exc:
            errors.append(f"semantic candidate[{candidate_index}]: {exc}")
            continue
        if candidate.get("content_fingerprint") != expected_content:
            errors.append(
                f"semantic candidate[{candidate_index}]: content_fingerprint does not match current normalized content"
            )
            continue
        if candidate_id in candidate_by_id:
            errors.append(
                f"semantic candidate[{candidate_index}]: duplicate candidate_id"
            )
            continue
        candidate_by_id[candidate_id] = candidate_index

    entry_candidate_ids = [
        item.get("candidate_id") if isinstance(item, dict) else None
        for item in entries
    ]
    if all(
        isinstance(candidate_id, str)
        and re.fullmatch(r"[0-9a-f]{64}", candidate_id)
        for candidate_id in entry_candidate_ids
    ) and entry_candidate_ids != sorted(entry_candidate_ids):
        errors.append(
            "reference_semantic_dispositions.entries must be sorted by candidate_id"
        )

    def generic_rationale(value: str) -> bool:
        normalized = re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()
        tokens = normalized.split()
        return (
            len(value) < 12
            or len(tokens) < 4
            or normalized in SEMANTIC_EXCEPTION_GENERIC_VALUES
            or not any(
                token not in SEMANTIC_EXCEPTION_GENERIC_TOKENS for token in tokens
            )
        )

    for index, raw_entry in enumerate(entries):
        context = f"reference_semantic_dispositions.entries[{index}]"
        if not isinstance(raw_entry, dict):
            errors.append(f"{context}: must be a mapping")
            continue
        unexpected = sorted(set(raw_entry) - set(SEMANTIC_DISPOSITION_FIELDS))
        missing = [
            field for field in SEMANTIC_DISPOSITION_FIELDS if field not in raw_entry
        ]
        if unexpected:
            errors.append(f"{context}: unknown field(s): {', '.join(unexpected)}")
        if missing:
            errors.append(f"{context}: missing field(s): {', '.join(missing)}")
            continue
        entry: dict[str, Any] = {}
        invalid = False
        string_fields = (
            "candidate_id",
            "finding",
            "path",
            "fingerprint",
            "skill_owner",
            "priority",
            "disposition",
            "reason",
            "authority_or_condition",
            "decision_owner",
            "mitigation",
        )
        for field in string_fields:
            value = raw_entry.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{context}: {field} must be a non-blank string")
                invalid = True
            else:
                entry[field] = value.strip()
        evidence = raw_entry.get("evidence")
        if not isinstance(evidence, dict) or set(evidence) != {
            "fingerprint",
            "content_fingerprint",
            "rationale",
        }:
            errors.append(
                f"{context}: evidence must contain exactly fingerprint, content_fingerprint, and rationale"
            )
            invalid = True
            normalized_evidence = {
                "fingerprint": None,
                "content_fingerprint": None,
                "rationale": "",
            }
        else:
            evidence_fingerprint = evidence.get("fingerprint")
            content_fingerprint = evidence.get("content_fingerprint")
            rationale = evidence.get("rationale")
            if evidence_fingerprint is not None and (
                not isinstance(evidence_fingerprint, str)
                or not re.fullmatch(r"[0-9a-f]{64}", evidence_fingerprint)
            ):
                errors.append(
                    f"{context}: evidence.fingerprint must be null or lowercase sha256"
                )
                invalid = True
            if content_fingerprint is not None and (
                not isinstance(content_fingerprint, str)
                or not re.fullmatch(r"[0-9a-f]{64}", content_fingerprint)
            ):
                errors.append(
                    f"{context}: evidence.content_fingerprint must be null or lowercase sha256"
                )
                invalid = True
            if not isinstance(rationale, str) or not rationale.strip():
                errors.append(
                    f"{context}: evidence.rationale must be a non-blank string"
                )
                invalid = True
                rationale = ""
            normalized_evidence = {
                "fingerprint": evidence_fingerprint,
                "content_fingerprint": content_fingerprint,
                "rationale": rationale.strip() if isinstance(rationale, str) else "",
            }
        entry["evidence"] = normalized_evidence
        review_after_raw = raw_entry.get("review_after")
        entry["review_after"] = review_after_raw
        if invalid:
            normalized_entries.append(entry)
            continue

        path = entry["path"]
        is_group_entry = entry["finding"] in SEMANTIC_GROUP_FINDINGS
        if (is_group_entry and path != "group") or (
            not is_group_entry and not _is_canonical_semantic_path(path)
        ):
            errors.append(f"{context}: path must be a canonical relative POSIX path")
        if SEMANTIC_DISPOSITION_WILDCARD_RE.search(entry["path"]):
            errors.append(f"{context}: path must not contain wildcard or glob syntax")
        if entry["finding"] not in SEMANTIC_FINDINGS:
            errors.append(f"{context}: finding is not a declared semantic family")
        for field in ("candidate_id", "fingerprint"):
            if not re.fullmatch(r"[0-9a-f]{64}", entry[field]):
                errors.append(f"{context}: {field} must be lowercase sha256")
        if entry["priority"] not in SEMANTIC_PRIORITIES:
            errors.append(f"{context}: priority must be P0, P1, or P2")
        if entry["disposition"] not in SEMANTIC_DISPOSITIONS:
            errors.append(
                f"{context}: disposition must be rewrite, valid-contextual-rule, false-positive, or time-bounded-exception"
            )
        for field in ("reason", "authority_or_condition", "mitigation"):
            if generic_rationale(entry[field]):
                errors.append(f"{context}: {field} is blank or generic")
        if len(entry["decision_owner"].split()) < 2 and not re.fullmatch(
            r"[a-z][a-z0-9]*(?:-[a-z0-9]+)+",
            entry["decision_owner"],
        ):
            errors.append(f"{context}: decision_owner must name an accountable owner")
        if generic_rationale(entry["evidence"]["rationale"]):
            errors.append(f"{context}: evidence.rationale is blank or generic")

        if entry["disposition"] == "time-bounded-exception":
            try:
                review_after = date.fromisoformat(review_after_raw)
                if review_after.isoformat() != review_after_raw:
                    raise ValueError
            except (TypeError, ValueError):
                errors.append(
                    f"{context}: time-bounded-exception review_after must be an ISO date"
                )
                review_after = None
            if review_after is not None and review_after <= evaluation_date:
                errors.append(
                    f"{context}: review_after must be strictly after {evaluation_date.isoformat()}"
                )
        elif review_after_raw is not None:
            errors.append(
                f"{context}: review_after must be null unless disposition is time-bounded-exception"
            )

        candidate_id = entry["candidate_id"]
        entry_scope = (
            "group" if entry["finding"] in SEMANTIC_GROUP_FINDINGS else entry["path"]
        )
        try:
            expected_entry_id = _semantic_candidate_id(
                entry["finding"], entry_scope, entry["fingerprint"]
            )
        except (TypeError, ValueError):
            expected_entry_id = None
        if candidate_id != expected_entry_id:
            errors.append(f"{context}: candidate_id does not match stable identity inputs")
        if candidate_id in seen_ids:
            errors.append(f"{context}: duplicate semantic disposition candidate_id")
        seen_ids.add(candidate_id)
        candidate_index = candidate_by_id.get(candidate_id)
        if candidate_index is None:
            metadata_matches = [
                candidate
                for candidate in candidates
                if candidate.get("finding") == entry["finding"]
                and candidate.get("path") == entry["path"]
                and candidate.get("fingerprint") == entry["fingerprint"]
            ]
            if metadata_matches:
                errors.append(f"{context}: candidate_id does not match candidate metadata")
            else:
                errors.append(f"{context}: stale semantic disposition entry")
        else:
            candidate = candidates[candidate_index]
            if candidate.get("detector_status") != "candidate":
                errors.append(f"{context}: disposition targets a detector-downgraded candidate")
            expected = {
                "finding": candidate.get("finding"),
                "path": candidate.get("path"),
                "fingerprint": candidate.get("fingerprint"),
                "skill_owner": candidate.get("skill_owner"),
            }
            for field, expected_value in expected.items():
                if entry[field] != expected_value:
                    errors.append(
                        f"{context}: {field} does not match current candidate"
                    )
            candidate_occurrences = candidate.get("occurrences")
            expected_evidence = (
                _semantic_evidence_fingerprint(candidate_occurrences)
                if candidate.get("finding") in SEMANTIC_GROUP_FINDINGS
                and isinstance(candidate_occurrences, list)
                else None
            )
            if entry["evidence"]["fingerprint"] != expected_evidence:
                errors.append(
                    f"{context}: evidence.fingerprint does not match current candidate membership"
                )
            expected_content = (
                _semantic_content_fingerprint(candidate_occurrences)
                if candidate.get("finding") in SEMANTIC_GROUP_FINDINGS
                and isinstance(candidate_occurrences, list)
                else None
            )
            if entry["evidence"]["content_fingerprint"] != expected_content:
                errors.append(
                    f"{context}: evidence.content_fingerprint does not match current candidate content"
                )
            matched_candidate_by_entry[index] = candidate_index
        normalized_entries.append(entry)

    if require_applied:
        common_errors, surface_errors = _reference_disposition_error_attribution(
            errors,
            entries,
            candidates,
        )
        blocked = _blocked_surfaces(
            REFERENCE_CONTENT_SURFACES,
            common_errors,
            surface_errors,
        )
        normalized_by_id = {
            str(item.get("candidate_id")): item
            for item in normalized_entries
            if isinstance(item, dict) and isinstance(item.get("candidate_id"), str)
        }
        applicable_matches = {
            entry_index: candidate_index
            for entry_index, candidate_index in matched_candidate_by_entry.items()
            if _reference_surfaces_for_candidate(candidates[candidate_index])
            and not (
                _reference_surfaces_for_candidate(candidates[candidate_index])
                & blocked
            )
        }
        matched_candidates = set(applicable_matches.values())
        for candidate_index, candidate in enumerate(candidates):
            if candidate_index in matched_candidates:
                entry = normalized_by_id.get(str(candidate.get("candidate_id", "")))
                if not isinstance(entry, dict):
                    errors.append(
                        f"semantic candidate[{candidate_index}]: applied disposition lacks canonical metadata"
                    )
                    continue
                expected_resolved = (
                    entry["disposition"] in SEMANTIC_RESOLVED_DISPOSITIONS
                )
                expected_status = (
                    f"resolved-{entry['disposition']}"
                    if expected_resolved
                    else "unresolved-rewrite"
                )
                if candidate.get("disposition_record") != entry:
                    errors.append(
                        f"semantic candidate[{candidate_index}]: applied semantic disposition metadata was mutated"
                    )
                if (
                    candidate.get("priority") != entry["priority"]
                    or candidate.get("disposition") != entry["disposition"]
                    or candidate.get("resolved") is not expected_resolved
                    or candidate.get("unresolved") is expected_resolved
                    or candidate.get("governance_status") != expected_status
                ):
                    errors.append(
                        f"semantic candidate[{candidate_index}]: applied semantic governance state was mutated"
                    )
                continue
            expected_priority = (
                None
                if candidate.get("detector_status") == "downgraded"
                else SEMANTIC_DEFAULT_PRIORITIES.get(str(candidate.get("finding")))
            )
            expected_status = (
                "detector-downgraded"
                if candidate.get("detector_status") == "downgraded"
                else "untriaged"
            )
            expected_unresolved = candidate.get("detector_status") != "downgraded"
            if (
                candidate.get("disposition") is not None
                or candidate.get("disposition_record") is not None
                or candidate.get("priority") != expected_priority
                or candidate.get("governance_status") != expected_status
                or candidate.get("resolved") is not False
                or candidate.get("unresolved") is not expected_unresolved
            ):
                errors.append(
                    f"semantic candidate[{candidate_index}]: blocked or unconfigured governance state was mutated"
                )
        matched_candidate_by_entry = applicable_matches
    return normalized_entries, matched_candidate_by_entry, errors


def _reference_semantic_candidates(documents: list[dict]) -> list[dict]:
    """Collect the pure, canonically ordered Reference detector projection."""
    for index, document in enumerate(documents):
        if not isinstance(document, dict) or not _is_canonical_semantic_path(
            document.get("path")
        ):
            raise ValueError(
                f"semantic document[{index}].path must be a canonical relative POSIX path"
            )
    sentence_rows: list[dict] = []
    for document in sorted(documents, key=lambda item: str(item["path"])):
        for occurrence in _semantic_sentence_occurrences(document):
            sentence = occurrence.pop("sentence")
            semantic_contexts = set(occurrence.get("semantic_contexts") or ())
            reference_kind = str(document.get("kind", "")).strip()
            if reference_kind:
                semantic_contexts.add(
                    f"reference-kind:{_semantic_context_label(reference_kind)}"
                )
            occurrence["semantic_contexts"] = sorted(semantic_contexts)
            absolute = _absolute_signals(sentence)
            if absolute:
                downgrade_reason = None
                contexts = set(occurrence["semantic_contexts"])
                if ABSOLUTE_CONDITIONAL_RE.search(sentence):
                    downgrade_reason = "same_sentence_conditional_language"
                elif REFERENCE_SCOPE_ONLY_RE.search(sentence):
                    downgrade_reason = "reference_loading_scope"
                elif ABSOLUTE_SCOPED_ONLY_RE.search(sentence):
                    downgrade_reason = "scoped_only_restriction"
                elif "preceding_conditional_language" in contexts:
                    downgrade_reason = "preceding_conditional_language"
                elif "preceding_reference_loading_scope" in contexts:
                    downgrade_reason = "preceding_reference_loading_scope"
                elif contexts & {
                    "negative_or_proof_limit_table_cell",
                    "proof_limit_heading",
                    "preceding_proof_limit_context",
                }:
                    downgrade_reason = "negative_or_proof_limit_table_context"
                elif ABSOLUTE_QUESTION_RE.search(sentence):
                    downgrade_reason = "question_context"
                elif ABSOLUTE_ADDITIVE_ONLY_RE.search(sentence):
                    downgrade_reason = "not_only_idiom"
                elif _absolute_literal_or_compound(sentence):
                    downgrade_reason = "lexical_literal_or_compound"
                elif _absolute_exact_table_context(contexts):
                    downgrade_reason = "exact_table_context_header"
                elif _absolute_clause_local_proof_limit(sentence):
                    downgrade_reason = "clause_local_proof_limit"
                elif _absolute_explicit_profile_authority(sentence):
                    downgrade_reason = "explicit_profile_agent_authority"
                elif _absolute_boundary_record_authority(sentence, contexts):
                    downgrade_reason = "boundary_record_authority"
                elif _absolute_map_every_evidence_closure(sentence, contexts):
                    downgrade_reason = "map_every_evidence_closure"
                elif _absolute_short_classification_fragment(sentence, contexts):
                    downgrade_reason = "short_classification_fragment"
                finding = "unconditional_absolute_candidate"
                sentence_rows.append(
                    {
                        "finding": finding,
                        "fingerprint": _semantic_fingerprint(finding, sentence),
                        **occurrence,
                        "tokens": count_o200k_base_tokens(sentence),
                        "signals": absolute,
                        "preview": sentence[:280],
                        "detector_status": (
                            "downgraded" if downgrade_reason else "candidate"
                        ),
                        **(
                            {"downgrade_reason": downgrade_reason}
                            if downgrade_reason
                            else {}
                        ),
                    }
                )

            fixed = _fixed_number_signals(sentence)
            if fixed:
                finding = "fixed_number_candidate"
                sentence_rows.append(
                    {
                        "finding": finding,
                        "fingerprint": _semantic_fingerprint(finding, sentence),
                        **{
                            key: value
                            for key, value in occurrence.items()
                            if key != "semantic_contexts"
                        },
                        "tokens": count_o200k_base_tokens(sentence),
                        "signals": fixed,
                        "preview": sentence[:280],
                        "detector_status": "candidate",
                    }
                )

    candidates = _fold_sentence_semantic_candidates(sentence_rows)
    candidates.extend(_duplicate_semantic_candidates(documents))

    candidates.sort(key=_semantic_candidate_sort_key)

    for candidate in candidates:
        candidate["disposition"] = None
        candidate["disposition_record"] = None
        if candidate.get("detector_status") == "downgraded":
            candidate["priority"] = None
            candidate["governance_status"] = "detector-downgraded"
            candidate["unresolved"] = False
            candidate["resolved"] = False
        else:
            candidate["priority"] = SEMANTIC_DEFAULT_PRIORITIES[
                candidate["finding"]
            ]
            candidate["governance_status"] = "untriaged"
            candidate["unresolved"] = True
            candidate["resolved"] = False

    return candidates


def _collect_reference_semantic_advisories(
    documents: list[dict],
    *,
    disposition_entries: object = _USE_CONFIG_DISPOSITIONS,
    evaluation_date: date | None = None,
) -> dict:
    """Collect stable semantic candidates and apply exact governance decisions."""

    candidates = _reference_semantic_candidates(documents)
    evaluated_on = (
        _effective_evaluation_date()
        if evaluation_date is None
        else evaluation_date
    )

    if disposition_entries is _USE_CONFIG_DISPOSITIONS:
        disposition_contract, disposition_errors = (
            _load_reference_semantic_dispositions()
        )
    elif isinstance(disposition_entries, list):
        disposition_contract = {
            "schema_version": SEMANTIC_DISPOSITION_SCHEMA_VERSION,
            "entries": disposition_entries,
        }
        disposition_errors = []
    elif isinstance(disposition_entries, dict):
        disposition_contract = disposition_entries
        disposition_errors = []
    else:
        disposition_contract = {"schema_version": None, "entries": []}
        disposition_errors = [
            "reference_semantic_dispositions must be a versioned mapping or entry list"
        ]
    if disposition_contract.get("schema_version") != SEMANTIC_DISPOSITION_SCHEMA_VERSION:
        disposition_errors.append(
            f"reference_semantic_dispositions.schema_version must equal {SEMANTIC_DISPOSITION_SCHEMA_VERSION}"
        )
    configured_entries = disposition_contract.get("entries")
    normalized_dispositions, disposition_matches, validation_errors = (
        _validate_reference_semantic_dispositions(
            candidates,
            configured_entries,
            evaluated_on,
            require_applied=False,
        )
    )
    disposition_errors.extend(validation_errors)
    for candidate_index, candidate in enumerate(candidates):
        if not _reference_surfaces_for_candidate(candidate):
            disposition_errors.append(
                f"semantic candidate[{candidate_index}]: cannot be attributed to a declared Reference surface"
            )
    disposition_common_errors, disposition_surface_errors = (
        _reference_disposition_error_attribution(
            disposition_errors,
            configured_entries,
            candidates,
        )
    )
    blocked_surfaces = _blocked_surfaces(
        REFERENCE_CONTENT_SURFACES,
        disposition_common_errors,
        disposition_surface_errors,
    )
    normalized_by_id = {
        str(item.get("candidate_id")): item
        for item in normalized_dispositions
        if isinstance(item, dict) and isinstance(item.get("candidate_id"), str)
    }
    applied_count = 0
    for _entry_index, candidate_index in sorted(disposition_matches.items()):
        candidate = candidates[candidate_index]
        candidate_surfaces = _reference_surfaces_for_candidate(candidate)
        entry = normalized_by_id.get(str(candidate.get("candidate_id", "")))
        if (
            not isinstance(entry, dict)
            or not candidate_surfaces
            or candidate_surfaces & blocked_surfaces
        ):
            continue
        entry = dict(entry)
        candidate["priority"] = entry["priority"]
        candidate["disposition"] = entry["disposition"]
        candidate["disposition_record"] = entry
        candidate["resolved"] = (
            entry["disposition"] in SEMANTIC_RESOLVED_DISPOSITIONS
        )
        candidate["unresolved"] = not candidate["resolved"]
        candidate["governance_status"] = (
            f"resolved-{entry['disposition']}"
            if candidate["resolved"]
            else "unresolved-rewrite"
        )
        applied_count += 1

    def disposition_counts(rows: list[dict]) -> dict[str, int]:
        return {
            "raw": len(rows),
            "detector_downgraded": sum(
                item["governance_status"] == "detector-downgraded" for item in rows
            ),
            "untriaged": sum(
                item["governance_status"] == "untriaged" for item in rows
            ),
            "rewrite": sum(item["disposition"] == "rewrite" for item in rows),
            "valid_contextual_rule": sum(
                item["disposition"] == "valid-contextual-rule" for item in rows
            ),
            "false_positive": sum(
                item["disposition"] == "false-positive" for item in rows
            ),
            "time_bounded_exception": sum(
                item["disposition"] == "time-bounded-exception" for item in rows
            ),
            "unresolved": sum(bool(item["unresolved"]) for item in rows),
            "resolved": sum(bool(item["resolved"]) for item in rows),
            "p0_unresolved": sum(
                item["unresolved"] and item["priority"] == "P0" for item in rows
            ),
            "p1_unresolved": sum(
                item["unresolved"] and item["priority"] == "P1" for item in rows
            ),
            "p2_unresolved": sum(
                item["unresolved"] and item["priority"] == "P2" for item in rows
            ),
        }

    by_finding: dict[str, dict[str, int]] = {}
    for finding in SEMANTIC_FINDINGS:
        rows = [item for item in candidates if item["finding"] == finding]
        by_finding[finding] = disposition_counts(rows)
    all_counts = disposition_counts(candidates)
    group_metrics = {
        finding: {
            "groups": len(
                [item for item in candidates if item["finding"] == finding]
            ),
            "occurrences": sum(
                int(item.get("occurrence_count", 0))
                for item in candidates
                if item["finding"] == finding
            ),
            "tokens": sum(
                int(item.get("total_tokens", 0))
                for item in candidates
                if item["finding"] == finding
            ),
        }
        for finding in (
            "exact_normalized_duplicate_block",
            "templated_block_candidate",
        )
    }
    return {
        "schema_version": SEMANTIC_ADVISORY_SCHEMA_VERSION,
        "detector_contract": _reference_semantic_detector_contract(),
        "finding_families": list(SEMANTIC_FINDINGS),
        "summary": {
            "raw_candidates": all_counts["raw"],
            "detector_downgraded_candidates": all_counts[
                "detector_downgraded"
            ],
            "untriaged_candidates": all_counts["untriaged"],
            "rewrite_candidates": all_counts["rewrite"],
            "valid_contextual_rule_candidates": all_counts[
                "valid_contextual_rule"
            ],
            "false_positive_candidates": all_counts["false_positive"],
            "time_bounded_exception_candidates": all_counts[
                "time_bounded_exception"
            ],
            "unresolved_candidates": all_counts["unresolved"],
            "resolved_candidates": all_counts["resolved"],
            "p0_unresolved_candidates": all_counts["p0_unresolved"],
            "p1_unresolved_candidates": all_counts["p1_unresolved"],
            "p2_unresolved_candidates": all_counts["p2_unresolved"],
            "by_finding": by_finding,
            "group_metrics": group_metrics,
            "strict_unresolved": {
                "fixed_number_candidates": by_finding[
                    "fixed_number_candidate"
                ]["unresolved"],
                "templated_block_groups": by_finding[
                    "templated_block_candidate"
                ]["unresolved"],
                "unconditional_absolute_p0_p1_candidates": (
                    by_finding["unconditional_absolute_candidate"][
                        "p0_unresolved"
                    ]
                    + by_finding["unconditional_absolute_candidate"][
                        "p1_unresolved"
                    ]
                ),
                "p2_rewrite_advisories": sum(
                    item["disposition"] == "rewrite"
                    and item["priority"] == "P2"
                    and item["finding"] not in SEMANTIC_GROUP_FINDINGS
                    and item["finding"] != "fixed_number_candidate"
                    for item in candidates
                ),
            },
        },
        "candidates": candidates,
        "disposition_contract": {
            "schema_version": SEMANTIC_DISPOSITION_SCHEMA_VERSION,
            "source": SKILL_CONTENT_EXCEPTIONS_FILE.relative_to(ROOT).as_posix(),
            "configured_count": (
                len(configured_entries) if isinstance(configured_entries, list) else 0
            ),
            "applied_count": applied_count,
            "entries": normalized_dispositions,
            "errors": disposition_errors,
            "common_errors": disposition_common_errors,
            "surface_errors": disposition_surface_errors,
            "group_scope": (
                "Group candidate IDs use the literal scope 'group'; evidence.fingerprint "
                "must match sorted path/owner membership and evidence.content_fingerprint "
                "must match the sorted path/owner/normalized-body multiset."
            ),
        },
        "limitations": [
            "Absolute-language detection is lexical over logical Markdown units; it does not decide whether an unconditional rule is correct.",
            "Fixed-number detection requires a syntactically associated money, time, percent, cost, SLO, maturity count, option count, organization window, score threshold, or policy value after deterministic example, code, date, status, protocol, identifier, standard-version, candidate, and baseline exclusions.",
            "Exact normalized duplicate blocks require at least three nontrivial decision-bearing lines, a 36-token floor, and two indexed Reference paths; whitespace, case, bullet markers, and the owning Skill name are the only semantic-preserving normalizations.",
            "Templated block candidates compare YAML key-path shapes or explicit Tool Permission, Handoff, Closure, Evidence, and Output schemas across at least two owners; they do not label semantically similar matrix contents as duplicates.",
            "Detector-downgraded conditional language remains visible but is outside semantic disposition gates.",
            "Semantic dispositions are exact candidate matches; malformed, duplicate, mismatched, stale, or expired entries fail the default validation contract.",
            "Strict mode requires zero unresolved fixed-number candidates, templated groups, and P0/P1 unconditional-absolute candidates; P2 rewrite candidates remain advisory.",
        ],
    }


def _root_semantic_candidate_id(
    finding: str,
    path: str,
    document_part: str,
    fingerprint: str,
) -> str:
    if finding not in ROOT_SEMANTIC_FINDINGS:
        raise ValueError("root semantic candidate finding is not declared")
    if not _is_canonical_semantic_path(path):
        raise ValueError("root semantic candidate path must be canonical")
    if document_part not in {"body", "description", "control-prompt"}:
        raise ValueError("root semantic document_part is not declared")
    if not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
        raise ValueError("root semantic fingerprint must be lowercase sha256")
    # Source lines are deliberately excluded: inserting unrelated lines does not
    # churn candidate IDs. Disposition evidence separately binds the exact
    # occurrence multiset and its section/local context.
    payload = (
        f"root-semantic-candidate-v2\0{finding}\0{path}\0{document_part}\0{fingerprint}"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _root_candidate_sort_key(item: object) -> tuple[str, str, str, str]:
    if not isinstance(item, dict):
        return ("", "", "", "")
    return tuple(
        str(item.get(field, ""))
        for field in ("finding", "path", "document_part", "fingerprint")
    )


def _root_occurrence_fingerprint(occurrences: list[dict]) -> str:
    membership = sorted(
        (
            str(item["path"]),
            str(item["owner"]),
            str(item["document_part"]),
        )
        for item in occurrences
    )
    payload = "root-semantic-occurrences-v1\0" + "\0".join(
        f"{path}\0{owner}\0{part}" for path, owner, part in membership
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _root_context_membership_fingerprint(occurrences: list[dict]) -> str:
    contexts = sorted(str(item["context_fingerprint"]) for item in occurrences)
    payload = "root-semantic-contexts-v1\0" + "\0".join(contexts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _root_local_context_fingerprint(
    document: dict,
    lines: dict[str, int],
    context_labels: list[str] | tuple[str, ...] | set[str] = (),
) -> str:
    body = str(document.get("governed_text", document["text"]))
    offset = int(document.get("line_offset", 0) or 0)
    local_index = max(0, int(lines["start"]) - offset - 1)
    containing = [
        section
        for section in parse_sections(body)
        if section.start <= local_index < section.start + section.line_count
    ]
    if containing:
        section = max(containing, key=lambda item: (item.level, item.start))
        section_material = f"{section.level}\0{section.title}\0{section.text}"
    else:
        section_material = body
    normalized_context = _semantic_normalize_sentence(section_material)
    labels = "\0".join(sorted(str(item) for item in context_labels))
    payload = (
        "root-semantic-local-context-v1\0"
        + str(document.get("document_part", "body"))
        + "\0"
        + labels
        + "\0"
        + normalized_context
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _root_candidate(
    finding: str,
    document: dict,
    text: str,
    lines: dict[str, int],
    signals: list[str],
    *,
    context_labels: list[str] | tuple[str, ...] | set[str] = (),
) -> dict:
    fingerprint = _semantic_fingerprint(finding, text)
    path = str(document["path"])
    document_part = str(document.get("document_part", "body"))
    occurrence = {
        "path": path,
        "layer": str(document["layer"]),
        "owner": str(document["owner"]),
        "document_part": document_part,
        "lines": dict(lines),
        "tokens": count_o200k_base_tokens(text),
        "signals": sorted(set(signals)),
        "preview": re.sub(r"\s+", " ", text).strip()[:280],
        "context_fingerprint": _root_local_context_fingerprint(
            document, lines, context_labels
        ),
    }
    return {
        "finding": finding,
        "fingerprint": fingerprint,
        "candidate_id": _root_semantic_candidate_id(
            finding, path, document_part, fingerprint
        ),
        "path": path,
        "document_part": document_part,
        "layer": str(document["layer"]),
        "owner": str(document["owner"]),
        "skill_owner": str(document["owner"]),
        "tokens": occurrence["tokens"],
        "total_tokens": occurrence["tokens"],
        "signals": occurrence["signals"],
        "preview": occurrence["preview"],
        "occurrence_count": 1,
        "occurrences": [occurrence],
        "priority": ROOT_SEMANTIC_DEFAULT_PRIORITIES[finding],
        "disposition": None,
        "disposition_record": None,
        "governance_status": "untriaged",
        "unresolved": True,
        "resolved": False,
    }


def _fold_root_candidates(rows: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str, str, str], list[dict]] = defaultdict(list)
    for row in rows:
        grouped[
            (
                row["finding"],
                row["path"],
                row["document_part"],
                row["fingerprint"],
            )
        ].append(row)
    result: list[dict] = []
    for _key, candidates in sorted(grouped.items()):
        canonical = candidates[0]
        occurrences = sorted(
            [item["occurrences"][0] for item in candidates],
            key=lambda item: (item["lines"]["start"], item["lines"]["end"]),
        )
        canonical["occurrences"] = occurrences
        canonical["occurrence_count"] = len(occurrences)
        canonical["total_tokens"] = sum(int(item["tokens"]) for item in occurrences)
        canonical["signals"] = sorted(
            {signal for item in occurrences for signal in item["signals"]}
        )
        canonical["occurrence_fingerprint"] = _root_occurrence_fingerprint(occurrences)
        canonical["context_fingerprint"] = _root_context_membership_fingerprint(
            occurrences
        )
        result.append(canonical)
    return sorted(result, key=_root_candidate_sort_key)


def _root_semantic_dispositions_from_data(
    data: object,
    *,
    source: str,
) -> tuple[dict, list[str]]:
    if not isinstance(data, dict):
        return {"schema_version": None, "entries": []}, [f"{source}: must be a mapping"]
    contract = data.get(ROOT_SEMANTIC_DISPOSITION_KEY)
    if not isinstance(contract, dict):
        return {"schema_version": None, "entries": []}, [
            f"{source}: missing {ROOT_SEMANTIC_DISPOSITION_KEY} mapping"
        ]
    errors: list[str] = []
    if set(contract) != {"schema_version", "entries"}:
        errors.append(
            f"{source}: {ROOT_SEMANTIC_DISPOSITION_KEY} must contain exactly "
            "schema_version and entries"
        )
    if contract.get("schema_version") != ROOT_SEMANTIC_DISPOSITION_SCHEMA_VERSION:
        errors.append(
            f"{source}: {ROOT_SEMANTIC_DISPOSITION_KEY}.schema_version must equal "
            f"{ROOT_SEMANTIC_DISPOSITION_SCHEMA_VERSION}"
        )
    entries = contract.get("entries")
    if not isinstance(entries, list):
        errors.append(f"{source}: {ROOT_SEMANTIC_DISPOSITION_KEY}.entries must be a list")
        entries = []
    return {
        "schema_version": contract.get("schema_version"),
        "entries": entries,
    }, errors


def _load_root_semantic_dispositions() -> tuple[dict, list[str]]:
    source = _repository_relative_path(SKILL_CONTENT_EXCEPTIONS_FILE)
    try:
        data = load_yaml_file(SKILL_CONTENT_EXCEPTIONS_FILE)
    except ValidationProblem as exc:
        return {"schema_version": None, "entries": []}, [str(exc)]
    return _root_semantic_dispositions_from_data(data, source=source)


def _root_rationale_is_generic(value: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()
    tokens = normalized.split()
    return (
        len(value) < 12
        or len(tokens) < 4
        or normalized in SEMANTIC_EXCEPTION_GENERIC_VALUES
        or not any(token not in SEMANTIC_EXCEPTION_GENERIC_TOKENS for token in tokens)
    )


def _validate_root_semantic_dispositions(
    candidates: list[dict],
    entries: object,
    evaluation_date: date,
    *,
    require_applied: bool,
) -> tuple[list[dict], dict[int, int], list[str]]:
    if not isinstance(entries, list):
        return [], {}, [f"{ROOT_SEMANTIC_DISPOSITION_KEY}.entries must be a list"]
    candidate_by_id = {item["candidate_id"]: index for index, item in enumerate(candidates)}
    normalized: list[dict] = []
    matches: dict[int, int] = {}
    errors: list[str] = []
    ids = [item.get("candidate_id") if isinstance(item, dict) else None for item in entries]
    if all(isinstance(item, str) for item in ids) and ids != sorted(ids):
        errors.append(f"{ROOT_SEMANTIC_DISPOSITION_KEY}.entries must be sorted by candidate_id")
    seen: set[str] = set()
    required = set(ROOT_SEMANTIC_DISPOSITION_FIELDS)
    for index, raw in enumerate(entries):
        label = f"{ROOT_SEMANTIC_DISPOSITION_KEY}.entries[{index}]"
        if not isinstance(raw, dict):
            errors.append(f"{label}: must be a mapping")
            continue
        if set(raw) != required:
            missing = sorted(required - set(raw))
            unknown = sorted(set(raw) - required)
            if missing:
                errors.append(f"{label}: missing field(s): {', '.join(missing)}")
            if unknown:
                errors.append(f"{label}: unknown field(s): {', '.join(unknown)}")
            continue
        entry = {key: raw[key] for key in ROOT_SEMANTIC_DISPOSITION_FIELDS}
        normalized.append(entry)
        for field in (
            "candidate_id", "finding", "path", "document_part", "fingerprint", "skill_owner",
            "priority", "disposition", "reason", "authority_or_condition",
            "decision_owner", "mitigation",
        ):
            if not isinstance(entry[field], str) or not entry[field].strip():
                errors.append(f"{label}: {field} must be a non-blank string")
        if not all(isinstance(entry[field], str) and entry[field].strip() for field in (
            "candidate_id", "finding", "path", "document_part", "fingerprint", "priority", "disposition"
        )):
            continue
        if entry["finding"] not in ROOT_SEMANTIC_FINDINGS:
            errors.append(f"{label}: finding is not a declared root semantic family")
            continue
        if not _is_canonical_semantic_path(entry["path"]):
            errors.append(f"{label}: path must be a canonical relative POSIX path")
        if entry["document_part"] not in {"body", "description", "control-prompt"}:
            errors.append(f"{label}: document_part is not declared")
        for field in ("candidate_id", "fingerprint"):
            if not re.fullmatch(r"[0-9a-f]{64}", entry[field]):
                errors.append(f"{label}: {field} must be lowercase sha256")
        if entry["priority"] != ROOT_SEMANTIC_DEFAULT_PRIORITIES[entry["finding"]]:
            errors.append(f"{label}: priority must match the current root finding family")
        if entry["disposition"] not in SEMANTIC_DISPOSITIONS:
            errors.append(f"{label}: invalid disposition")
        for field in ("reason", "authority_or_condition", "mitigation"):
            if isinstance(entry[field], str) and _root_rationale_is_generic(entry[field]):
                errors.append(f"{label}: {field} is blank or generic")
        if isinstance(entry["decision_owner"], str) and (
            len(entry["decision_owner"].split()) < 2
            and not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)+", entry["decision_owner"])
        ):
            errors.append(f"{label}: decision_owner must name an accountable owner")
        evidence = entry["evidence"]
        if not isinstance(evidence, dict) or set(evidence) != ROOT_SEMANTIC_EVIDENCE_FIELDS:
            errors.append(
                f"{label}: evidence must contain exactly occurrence_fingerprint, "
                "context_fingerprint, and rationale"
            )
        else:
            for field in ("occurrence_fingerprint", "context_fingerprint"):
                if not isinstance(evidence.get(field), str) or not re.fullmatch(
                    r"[0-9a-f]{64}", evidence[field]
                ):
                    errors.append(f"{label}: evidence.{field} must be lowercase sha256")
            rationale = evidence.get("rationale")
            if not isinstance(rationale, str) or _root_rationale_is_generic(rationale):
                errors.append(f"{label}: evidence.rationale is blank or generic")
        review_after = entry["review_after"]
        if entry["disposition"] == "time-bounded-exception":
            try:
                parsed = date.fromisoformat(review_after)
                if parsed.isoformat() != review_after or parsed <= evaluation_date:
                    raise ValueError
            except (TypeError, ValueError):
                errors.append(
                    f"{label}: time-bounded-exception review_after must be an ISO date after "
                    f"{evaluation_date.isoformat()}"
                )
        elif review_after is not None:
            errors.append(f"{label}: review_after must be null unless time-bounded-exception")
        try:
            expected_id = _root_semantic_candidate_id(
                entry["finding"], entry["path"], entry["document_part"],
                entry["fingerprint"]
            )
        except (TypeError, ValueError):
            expected_id = None
        if entry["candidate_id"] != expected_id:
            errors.append(f"{label}: candidate_id does not match stable identity inputs")
        if entry["candidate_id"] in seen:
            errors.append(f"{label}: duplicate candidate_id")
        seen.add(entry["candidate_id"])
        candidate_index = candidate_by_id.get(entry["candidate_id"])
        if candidate_index is None:
            errors.append(f"{label}: stale root semantic disposition entry")
            continue
        candidate = candidates[candidate_index]
        for field in (
            "finding", "path", "document_part", "fingerprint", "skill_owner"
        ):
            if entry[field] != candidate[field]:
                errors.append(f"{label}: {field} does not match current candidate")
        if isinstance(evidence, dict):
            for evidence_field, candidate_field in (
                ("occurrence_fingerprint", "occurrence_fingerprint"),
                ("context_fingerprint", "context_fingerprint"),
            ):
                if evidence.get(evidence_field) != candidate.get(candidate_field):
                    errors.append(
                        f"{label}: evidence.{evidence_field} does not match current candidate"
                    )
        matches[index] = candidate_index
    if require_applied:
        common_errors, surface_errors = _root_disposition_error_attribution(
            errors,
            entries,
            candidates,
        )
        blocked = _blocked_surfaces(
            ROOT_CONTENT_SURFACES,
            common_errors,
            surface_errors,
        )
        normalized_by_id = {
            str(item.get("candidate_id")): item
            for item in normalized
            if isinstance(item, dict) and isinstance(item.get("candidate_id"), str)
        }
        applicable_matches = {
            entry_index: candidate_index
            for entry_index, candidate_index in matches.items()
            if (
                (surface := _root_surface_for_document(candidates[candidate_index]))
                is not None
                and surface not in blocked
            )
        }
        matched_candidates = set(applicable_matches.values())
        for candidate_index, candidate in enumerate(candidates):
            if candidate_index in matched_candidates:
                entry = normalized_by_id.get(str(candidate.get("candidate_id", "")))
                if not isinstance(entry, dict):
                    errors.append(
                        f"root semantic candidate[{candidate_index}]: applied disposition lacks canonical metadata"
                    )
                    continue
                resolved = entry["disposition"] in SEMANTIC_RESOLVED_DISPOSITIONS
                status = (
                    f"resolved-{entry['disposition']}"
                    if resolved
                    else "unresolved-rewrite"
                )
                if (
                    candidate.get("disposition_record") != entry
                    or candidate.get("priority") != entry["priority"]
                    or candidate.get("disposition") != entry["disposition"]
                    or candidate.get("resolved") is not resolved
                    or candidate.get("unresolved") is resolved
                    or candidate.get("governance_status") != status
                ):
                    errors.append(
                        f"root semantic candidate[{candidate_index}]: applied root governance state was mutated"
                    )
                continue
            expected_priority = ROOT_SEMANTIC_DEFAULT_PRIORITIES.get(
                str(candidate.get("finding"))
            )
            if (
                candidate.get("disposition") is not None
                or candidate.get("disposition_record") is not None
                or candidate.get("priority") != expected_priority
                or candidate.get("governance_status") != "untriaged"
                or candidate.get("resolved") is not False
                or candidate.get("unresolved") is not True
            ):
                errors.append(
                    f"root semantic candidate[{candidate_index}]: blocked or unconfigured governance state was mutated"
                )
        matches = applicable_matches
    return normalized, matches, errors


def _root_skill_documents(
    foundation_contracts: dict[str, dict] | None = None,
) -> list[dict]:
    foundation_contracts = (
        foundation_contracts
        if foundation_contracts is not None
        else _load_foundation_content_contracts()
    )
    documents: list[dict] = []
    for kind, root in DESCRIPTION_ROOTS:
        for _kind, path in _safe_skill_files_for_root(kind, root):
            source_record = _validation_utils.collect_skill_root_source(
                path,
                root=ROOT,
            )
            raw_source = source_record["raw_source"]
            metadata, raw_frontmatter, body = parse_frontmatter(path)
            owner = str(metadata.get("name") or path.parent.name)
            relative_path = _repository_relative_path(path)
            body_document = {
                "path": relative_path,
                "layer": kind,
                "owner": owner,
                "kind": kind,
                "text": body,
                # Registry-authored JIT load/skip records remain part of the
                # source fingerprint and readability surface. Blank only the
                # exact canonical projection for authored-content budgets and
                # semantic-disposition detection.
                "governed_text": strip_frontmatter_body_targeted_reference_projection(
                    body,
                    raw_source,
                ),
                "line_offset": len(raw_frontmatter.splitlines()) + 2,
                "document_part": "body",
            }
            if kind == "foundation-capability":
                contract = foundation_contracts.get(owner)
                if contract is None:
                    raise ValidationProblem(
                        f"{relative_path}: missing Foundation content_class contract"
                    )
                body_document.update(contract)
            documents.append(body_document)
            description = metadata.get("description")
            if isinstance(description, str) and description.strip():
                description_index = next(
                    (
                        index
                        for index, line in enumerate(raw_frontmatter.splitlines())
                        if re.match(r"^description\s*:", line)
                    ),
                    0,
                )
                documents.append(
                    {
                        "path": relative_path,
                        "layer": kind,
                        "owner": owner,
                        "kind": kind,
                        "text": description.strip(),
                        # raw frontmatter starts on physical line 2. The semantic
                        # extractor adds one for its local first line.
                        "line_offset": description_index + 1,
                        "document_part": "description",
                    }
                )
    for kind, path in ROOT_AGENT_DOCUMENTS:
        _require_safe_source_path(
            path,
            allowed_root=path.parent,
            source="local",
            expect_directory=False,
        )
        documents.append(
            {
                "path": _repository_relative_path(path),
                "layer": kind,
                "owner": path.stem,
                "kind": kind,
                "text": path.read_text(encoding="utf-8"),
                "line_offset": 0,
                "document_part": "control-prompt",
            }
        )
    return sorted(
        documents,
        key=lambda item: (str(item["path"]), str(item["document_part"])),
    )


def _root_clause_texts(sentence: str) -> list[tuple[str, bool]]:
    clauses: list[tuple[str, str]] = []
    start = 0
    for separator in ROOT_CLAUSE_SPLIT_RE.finditer(sentence):
        value = sentence[start : separator.start()].strip(" ,;:–—")
        if value:
            clauses.append((value, separator.group(0)))
        start = separator.end()
    value = sentence[start:].strip(" ,;:–—")
    if value:
        clauses.append((value, ""))
    if not clauses:
        return [(sentence.strip(), False)]

    result: list[tuple[str, bool]] = []
    inherit_next = False
    for clause, following_separator in clauses:
        inherited = bool(
            inherit_next and not ROOT_CONTEXT_INHERITANCE_BREAK_RE.search(clause)
        )
        result.append((clause, inherited))
        local_parent = bool(ROOT_PARENT_CONDITION_RE.search(clause))
        # A real JIT directive may scope one coordinated child clause.  The
        # child cannot extend that scope again, and explicit independence
        # language terminates inheritance before it reaches the child.
        inherit_next = bool(
            local_parent
            and ROOT_COORDINATING_SEPARATOR_RE.search(following_separator)
            and not ROOT_CONTEXT_INHERITANCE_BREAK_RE.search(clause)
        )
    return result


def _root_mask_spans(value: str, patterns: tuple[re.Pattern[str], ...]) -> str:
    """Blank only protected spans while preserving all neighboring evidence."""

    masked = list(value)
    for pattern in patterns:
        for match in pattern.finditer(value):
            masked[match.start() : match.end()] = " " * (match.end() - match.start())
    return "".join(masked)


def _root_fixed_number_signals(
    clause: str,
    *,
    mask_routing_selectors: bool = False,
) -> list[str]:
    patterns = (
        ROOT_FEASIBLE_SET_COMPARISON_RE,
        ROOT_ANTI_MANDATE_NUMBER_RE,
        ROOT_SYNTACTIC_SINGULAR_RE,
        FIXED_INLINE_CODE_RE,
    )
    root_clause = _root_mask_spans(clause, patterns)
    if mask_routing_selectors:
        root_clause = _root_mask_spans(root_clause, (ROOT_ROUTING_SELECTOR_SPAN_RE,))
    root_clause = ROOT_COUNT_IDENTIFIER_RE.sub("", root_clause)
    signals = set(_fixed_number_signals(root_clause))
    if ROOT_THRESHOLD_RE.search(root_clause):
        signals.add("fixed-threshold")
    if ROOT_DURATION_RE.search(root_clause):
        signals.add("fixed-duration")
    if ROOT_COUNT_RE.search(root_clause):
        signals.add("fixed-count")
    if ROOT_HTTP_STATUS_CONTEXT_RE.search(root_clause):
        signals.add("fixed-http-status")
    return sorted(signals)


def _root_has_routing_selector_context(document: dict, contexts: set[str]) -> bool:
    headings = {
        item.removeprefix("heading:")
        for item in contexts
        if item.startswith("heading:")
    }
    return bool(
        headings & ROOT_ROUTING_SELECTOR_HEADINGS
        or document.get("document_part") == "description"
    )


def _root_vendor_tool_signals(clause: str) -> list[str]:
    signals = {
        match.group(0).casefold() for match in ROOT_VENDOR_TOOL_RE.finditer(clause)
    }
    signals.update(
        f"generic-assignment:{match.group('name').casefold()}"
        for match in ROOT_GENERIC_VENDOR_ASSIGNMENT_RE.finditer(clause)
    )
    return sorted(signals)


def _root_vendor_is_owned_description(
    document: dict, clause: str, signal: str
) -> bool:
    if document.get("document_part") != "description" or signal.startswith(
        "generic-assignment:"
    ):
        return False
    normalized_owner = re.sub(r"[^a-z0-9]+", " ", str(document["owner"]).casefold())
    normalized_signal = re.sub(r"[^a-z0-9]+", " ", signal.casefold()).strip()
    return bool(
        normalized_signal
        and normalized_signal in normalized_owner.split()
        and ROOT_OWNED_VENDOR_SCOPE_RE.search(clause)
        and not ROOT_UNCONDITIONAL_RE.search(clause)
    )


def _root_policy_clause(clause: str, *, anti_pattern_section: bool) -> str:
    """Mask explicit non-prescriptions without hiding neighboring rules."""

    patterns: tuple[re.Pattern[str], ...] = (
        ROOT_NEGATED_REQUIREMENT_SPAN_RE,
        ROOT_QUOTED_FAILURE_EXAMPLE_RE,
    )
    masked = _root_mask_spans(clause, patterns)
    if anti_pattern_section:
        # Quoted/backticked text in an Anti-Patterns section is example material;
        # prose outside those spans remains eligible for policy detection.
        masked = _root_mask_spans(
            masked,
            (ROOT_QUOTED_OR_BACKTICK_RE, ROOT_ANTI_PATTERN_CONTRAST_SPAN_RE),
        )
    return masked


def _root_has_normative_mechanism_force(clause: str) -> bool:
    if ROOT_STRONG_NORMATIVE_RE.search(clause):
        return True
    return bool(
        ROOT_UNCONDITIONAL_RE.search(clause)
        and ROOT_IMPERATIVE_MECHANISM_RE.search(clause)
    )


def _root_has_directive_force(clause: str, match: re.Match[str]) -> bool:
    verb = match.group(0).casefold()
    prefix = clause[: match.start()]
    if re.search(
        r"\b(?:(?:do|does|did)\s+not|never)\s*$", prefix, re.IGNORECASE
    ):
        return False
    if verb in {"require", "requires", "required"}:
        return True
    return bool(
        ROOT_UNCONDITIONAL_RE.search(prefix)
        or re.fullmatch(r"\s*(?:\*\*|__)?", prefix)
    )


def _root_mandatory_artifact_signals(clause: str) -> list[str]:
    signals: set[str] = set()
    for pattern in (
        ROOT_ARTIFACT_PASSIVE_REQUIRED_RE,
        ROOT_ARTIFACT_MUST_HAVE_RE,
        ROOT_ARTIFACT_ACCOMPANY_RE,
    ):
        signals.update(
            match.group("artifact").casefold() for match in pattern.finditer(clause)
        )
    for directive in ROOT_ARTIFACT_DIRECTIVE_RE.finditer(clause):
        if not _root_has_directive_force(clause, directive):
            continue
        tail = clause[directive.end() :]
        boundary = ROOT_ARTIFACT_OBJECT_BOUNDARY_RE.search(tail)
        direct_object = tail[: boundary.start()] if boundary else tail
        if re.match(r"\s*(?:,\s*)?(?:and\s+)?no\b", direct_object, re.IGNORECASE):
            continue
        if ROOT_EXISTING_ARTIFACT_LIFECYCLE_RE.search(direct_object):
            continue
        for artifact in ROOT_MANDATORY_ARTIFACT_RE.finditer(direct_object):
            value = artifact.group(0).casefold()
            remainder = direct_object[artifact.end() :]
            if remainder and not re.match(
                r"^\s*(?:[,/]|(?:and|or)\b|$)", remainder, re.IGNORECASE
            ):
                # `test control`, `fixture consumer`, and similar noun modifiers
                # describe a subject; they do not mandate the durable artifact.
                continue
            if value == "table" and ROOT_DATABASE_ARTIFACT_RE.search(
                direct_object
            ):
                continue
            signals.add(value)
    return sorted(signals)


def _root_organization_policy_signals(clause: str) -> list[str]:
    if ROOT_TECHNICAL_MANAGER_RE.search(clause) or not ROOT_ORGANIZATION_AUTHORITY_RE.search(
        clause
    ):
        return []
    return sorted(
        {match.group(0).casefold() for match in ROOT_ORGANIZATION_ROLE_RE.finditer(clause)}
    )


def _root_refinement_density(
    body: str, sections: list[Section]
) -> tuple[str, dict[str, int], list[str]] | None:
    """Return one file-level, source-auditable teaching/refinement block."""

    lines = body.splitlines()
    for section in sections:
        normalized_title = _semantic_context_label(section.title)
        if section.level < 2 or ROOT_DECISION_RULE_HEADING_RE.fullmatch(
            normalized_title
        ):
            continue
        section_lines = lines[
            section.start : min(len(lines), section.start + section.line_count)
        ]
        refinement_intros = sum(
            len(ROOT_REFINEMENT_INTRO_RE.findall(line)) for line in section_lines
        )
        list_items = sum(bool(LIST_ITEM_RE.match(line)) for line in section_lines)
        if refinement_intros and list_items >= 3:
            return (
                f"{section.title}\n{section.text}",
                {
                    "start": section.start + 1,
                    "end": section.start + section.line_count,
                },
                [
                    "root-refinement-density",
                    f"refinement-intros:{refinement_intros}",
                    f"refinement-items:{list_items}",
                ],
            )

    heading_contexts = _heading_contexts(body)
    marker_rows: list[tuple[int, str, set[str]]] = []
    marker_totals = {"example": 0, "definition": 0, "contrast": 0}
    for index, line, in_fence in _strip_fenced(lines):
        if in_fence or not line.strip() or HEADING_RE.match(line):
            continue
        if any(
            ROOT_DECISION_RULE_HEADING_RE.fullmatch(
                _semantic_context_label(title)
            )
            for title in heading_contexts.get(index, [])
        ):
            continue
        local_signals: set[str] = set()
        for name, pattern in (
            ("example", ROOT_TEACHING_EXAMPLE_RE),
            ("definition", ROOT_TEACHING_DEFINITION_RE),
            ("contrast", ROOT_TEACHING_CONTRAST_RE),
        ):
            count = len(pattern.findall(line))
            if count:
                local_signals.add(name)
                marker_totals[name] += count
        if local_signals:
            marker_rows.append((index, line.strip(), local_signals))
    if len(marker_rows) < 3 or sum(marker_totals.values()) < 3:
        return None
    selected_text = "\n".join(line for _index, line, _signals in marker_rows)
    return (
        selected_text,
        {"start": marker_rows[0][0] + 1, "end": marker_rows[-1][0] + 1},
        [
            "root-teaching-marker-density",
            *(f"{name}-markers:{count}" for name, count in marker_totals.items() if count),
            f"marker-lines:{len(marker_rows)}",
        ],
    )


def _root_sentence_candidates(document: dict) -> list[dict]:
    rows: list[dict] = []
    for occurrence in _semantic_sentence_occurrences(
        document, include_negative_examples=True
    ):
        sentence = occurrence.pop("sentence")
        contexts = set(occurrence.get("semantic_contexts") or ())
        heading = " ".join(
            item.removeprefix("heading:")
            for item in contexts
            if item.startswith("heading:")
        )
        reference_section = (
            "targeted references" in heading or "reference loading policy" in heading
        )
        anti_pattern_section = any(
            re.fullmatch(r"anti[- ]?patterns?", item.removeprefix("heading:"))
            for item in contexts
            if item.startswith("heading:")
        )
        lines = occurrence["lines"]
        for clause, inherited_context in _root_clause_texts(sentence):
            if reference_section and (
                ROOT_EXACT_TARGETED_LINK_RE.fullmatch(clause)
                or ROOT_EXACT_NO_REFERENCE_RE.fullmatch(clause)
            ):
                continue
            policy_clause = _root_policy_clause(
                clause, anti_pattern_section=anti_pattern_section
            )
            absolute = sorted(
                {
                    match.group(0).casefold()
                    for match in ROOT_UNCONDITIONAL_RE.finditer(policy_clause)
                }
            )
            contextual = bool(
                inherited_context or ROOT_CONTEXT_AUTHORITY_RE.search(policy_clause)
            )
            context_labels = sorted({*contexts, f"clause:{clause}"})
            if (
                absolute
                and ROOT_MECHANISM_RE.search(policy_clause)
                and _root_has_normative_mechanism_force(policy_clause)
                and not contextual
            ):
                rows.append(
                    _root_candidate(
                        "unconditional_mechanism_candidate", document, clause, lines,
                        [*absolute, "mechanism"], context_labels=context_labels,
                    )
                )
            fixed_signals = _root_fixed_number_signals(
                clause,
                mask_routing_selectors=_root_has_routing_selector_context(
                    document, contexts
                ),
            )
            if fixed_signals and not ROOT_DERIVED_VALUE_AUTHORITY_RE.search(clause):
                rows.append(
                    _root_candidate(
                        "fixed_duration_threshold_status_candidate", document, clause,
                        lines, fixed_signals, context_labels=context_labels,
                    )
                )
            vendors = [] if anti_pattern_section else [
                signal
                for signal in _root_vendor_tool_signals(clause)
                if not _root_vendor_is_owned_description(document, clause, signal)
            ]
            if (
                vendors
                and ROOT_PRESCRIPTIVE_TOOL_RE.search(clause)
                and not ROOT_DERIVED_VALUE_AUTHORITY_RE.search(clause)
            ):
                rows.append(
                    _root_candidate(
                        "fixed_vendor_tool_candidate", document, clause, lines, vendors,
                        context_labels=context_labels,
                    )
                )
            artifacts = _root_mandatory_artifact_signals(policy_clause)
            if artifacts and not contextual:
                rows.append(
                    _root_candidate(
                        "mandatory_artifact_candidate", document, clause, lines,
                        artifacts,
                        context_labels=context_labels,
                    )
                )
            organization = (
                []
                if anti_pattern_section
                else _root_organization_policy_signals(clause)
            )
            if organization and not ROOT_DERIVED_VALUE_AUTHORITY_RE.search(clause):
                rows.append(
                    _root_candidate(
                        "context_free_organization_policy_candidate", document, clause,
                        lines, organization, context_labels=context_labels,
                    )
                )
    return rows


def _root_document_candidates(document: dict) -> list[dict]:
    body = str(document.get("governed_text", document["text"]))
    offset = int(document.get("line_offset", 0) or 0)
    rows: list[dict] = []
    sections = parse_sections(body)
    tutorial_sections = [
        section
        for section in sections
        if section.level >= 2
        and ROOT_TUTORIAL_HEADING_RE.fullmatch(
            _semantic_context_label(section.title)
        )
    ]
    explanatory_lines = [
        line.strip()
        for _index, line, in_fence in _strip_fenced(body.splitlines())
        if not in_fence and ROOT_EXPLANATORY_MARKER_RE.search(line)
    ]
    refinement_density = _root_refinement_density(body, sections)
    words = len(body.split())
    if tutorial_sections:
        section = tutorial_sections[0]
        text = f"{section.title}\n{section.text}"
        rows.append(
            _root_candidate(
                "tutorial_explanatory_density_candidate", document, text,
                {"start": section.start + 1 + offset, "end": section.start + section.line_count + offset},
                ["tutorial-heading"],
            )
        )
    elif refinement_density is not None:
        text, local_lines, signals = refinement_density
        rows.append(
            _root_candidate(
                "tutorial_explanatory_density_candidate",
                document,
                text,
                {
                    "start": local_lines["start"] + offset,
                    "end": local_lines["end"] + offset,
                },
                signals,
                context_labels=["file-level-refinement-density"],
            )
        )
    elif (
        words
        > int(
            document.get(
                "target_words",
                THRESHOLDS["root_tutorial_density_min_words"],
            )
        )
        and len(explanatory_lines) >= 3
    ):
        text = "\n".join(explanatory_lines)
        rows.append(
            _root_candidate(
                "tutorial_explanatory_density_candidate", document, text,
                {"start": offset + 1, "end": offset + max(1, len(body.splitlines()))},
                ["explanatory-density", f"markers:{len(explanatory_lines)}"],
            )
        )
    for section in sections:
        if (
            ROOT_LONG_EXAMPLE_HEADING_RE.search(section.title)
            and section.line_count > ROOT_LONG_EXAMPLE_LINES
        ):
            rows.append(
                _root_candidate(
                    "long_root_example_candidate", document,
                    f"{section.title}\n{section.text}",
                    {"start": section.start + 1 + offset, "end": section.start + section.line_count + offset},
                    ["example-section", f"lines:{section.line_count}"],
                )
            )
    return rows


def _root_document_id(path: str, document_part: str) -> str:
    return f"{path}#{document_part}"


_ROOT_SKILL_DOCUMENTS_DETECTOR_SOURCE = _root_skill_documents
_ROOT_SENTENCE_CANDIDATES_DETECTOR_SOURCE = _root_sentence_candidates
_ROOT_DOCUMENT_CANDIDATES_DETECTOR_SOURCE = _root_document_candidates
_FOLD_ROOT_CANDIDATES_DETECTOR_SOURCE = _fold_root_candidates


_DETECTOR_REPOSITORY_SOURCE_PATHS = (
    "scripts/audit-skill-content.py",
    "scripts/validation_utils.py",
)
_DETECTOR_REPOSITORY_SOURCE_FILES = (
    ("audit-skill-content", Path(__file__).resolve()),
    ("validation_utils", (ROOT / "scripts" / "validation_utils.py").resolve()),
)
_DETECTOR_SOURCE_WALKER_CONTRACT = (
    "repository-source-reachable-symbol-walker-v1"
)
_DETECTOR_IMPLICIT_MODULE_NAMES = frozenset(
    {
        "__builtins__",
        "__cached__",
        "__file__",
        "__loader__",
        "__name__",
        "__package__",
        "__spec__",
    }
)


def _detector_repository_source_text(path: Path) -> str:
    """Read one explicitly declared detector source or fail closed."""

    if not path.is_file():
        raise ValidationProblem(f"detector source is missing: {path}")
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValidationProblem(f"detector source is unreadable: {path}: {exc}") from exc


class _DetectorDocstringStripper(ast.NodeTransformer):
    """Remove non-behavioral docstrings before canonical AST projection."""

    @staticmethod
    def _strip(node: ast.AST) -> ast.AST:
        body = getattr(node, "body", None)
        if (
            isinstance(body, list)
            and body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            del body[0]
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        self.generic_visit(node)
        return self._strip(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        self.generic_visit(node)
        return self._strip(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        self.generic_visit(node)
        return self._strip(node)


def _detector_ast_source(source: str, node: ast.AST) -> str:
    """Return portable normalized behavior AST without comments or docstrings."""

    del source
    normalized = _DetectorDocstringStripper().visit(deepcopy(node))
    if not isinstance(normalized, ast.AST):
        raise ValidationProblem("detector source node cannot be normalized")
    ast.fix_missing_locations(normalized)
    try:
        return ast.unparse(normalized)
    except (TypeError, ValueError, RecursionError) as exc:
        raise ValidationProblem("detector source node cannot be projected") from exc


def _detector_assignment_names(node: ast.AST) -> list[str]:
    targets: list[ast.AST] = []
    if isinstance(node, ast.Assign):
        targets.extend(node.targets)
    elif isinstance(node, ast.AnnAssign):
        targets.append(node.target)
    names: set[str] = set()
    for target in targets:
        names.update(
            child.id
            for child in ast.walk(target)
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store)
        )
    return sorted(names)


def _detector_compound_binding_names(node: ast.AST) -> list[str]:
    """Collect module bindings in one compound statement without child scopes."""

    names: set[str] = set()
    pending = list(ast.iter_child_nodes(node))
    while pending:
        child = pending.pop()
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(child.name)
            continue
        if isinstance(
            child,
            (ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp),
        ):
            continue
        if isinstance(child, ast.Import):
            names.update(alias.asname or alias.name.split(".")[0] for alias in child.names)
            continue
        if isinstance(child, ast.ImportFrom):
            names.update(alias.asname or alias.name for alias in child.names)
            continue
        if isinstance(child, ast.ExceptHandler) and isinstance(child.name, str):
            names.add(child.name)
        if isinstance(child, ast.MatchAs) and isinstance(child.name, str):
            names.add(child.name)
        if isinstance(child, ast.MatchStar) and isinstance(child.name, str):
            names.add(child.name)
        if isinstance(child, ast.MatchMapping) and isinstance(child.rest, str):
            names.add(child.rest)
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
            names.add(child.id)
        pending.extend(ast.iter_child_nodes(child))
    return sorted(names)


def _detector_source_catalog() -> dict[str, dict[str, object]]:
    catalog: dict[str, dict[str, object]] = {}
    seen_paths: dict[Path, str] = {}
    for namespace, path in _DETECTOR_REPOSITORY_SOURCE_FILES:
        resolved = path.resolve()
        if namespace in catalog:
            raise ValidationProblem(
                f"duplicate detector source namespace: {namespace}"
            )
        prior_namespace = seen_paths.get(resolved)
        if prior_namespace is not None:
            raise ValidationProblem(
                "duplicate detector source path: "
                f"{resolved} ({prior_namespace}, {namespace})"
            )
        seen_paths[resolved] = namespace
        source = _detector_repository_source_text(resolved)
        try:
            tree = ast.parse(source, filename=resolved.as_posix())
        except SyntaxError as exc:
            raise ValidationProblem(
                f"cannot parse detector source {resolved}: {exc.msg}"
            ) from exc
        symbols: dict[str, dict[str, object]] = {}
        imports: dict[str, dict[str, str | None]] = {}
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name in symbols:
                    raise ValidationProblem(
                        "duplicate detector source symbol: "
                        f"{namespace}.{node.name}"
                    )
                symbols[node.name] = {
                    "kind": "class" if isinstance(node, ast.ClassDef) else "function",
                    "node": node,
                    "source": _detector_ast_source(source, node),
                }
                continue
            assignment_names = _detector_assignment_names(node)
            if not assignment_names and not isinstance(node, (ast.Import, ast.ImportFrom)):
                assignment_names = _detector_compound_binding_names(node)
            for name in assignment_names:
                if name in symbols:
                    raise ValidationProblem(
                        "duplicate detector source symbol: "
                        f"{namespace}.{name}"
                    )
                symbols[name] = {
                    "kind": "binding",
                    "node": node,
                    "source": _detector_ast_source(source, node),
                }
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports[alias.asname or alias.name.split(".")[0]] = {
                        "module": alias.name,
                        "name": None,
                    }
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                for alias in node.names:
                    imports[alias.asname or alias.name] = {
                        "module": node.module,
                        "name": alias.name,
                    }
        catalog[namespace] = {
            "path": resolved,
            "symbols": symbols,
            "imports": imports,
        }
    return catalog


def _detector_root_selector(
    function: object,
    catalog: dict[str, dict[str, object]],
) -> tuple[str, str]:
    function_globals = getattr(function, "__globals__", None)
    function_name = getattr(function, "__name__", None)
    source_path = (
        function_globals.get("__file__")
        if isinstance(function_globals, dict)
        else None
    )
    if not isinstance(function_name, str) or not isinstance(source_path, str):
        raise ValidationProblem("detector root is not a repository source function")
    matches = [
        namespace
        for namespace, module in catalog.items()
        if module["path"] == Path(source_path).resolve()
    ]
    if len(matches) != 1:
        raise ValidationProblem(
            f"detector root source selector is not unique: {function_name}"
        )
    namespace = matches[0]
    symbols = catalog[namespace]["symbols"]
    assert isinstance(symbols, dict)
    symbol = symbols.get(function_name)
    if not isinstance(symbol, dict) or symbol.get("kind") != "function":
        raise ValidationProblem(
            "detector root function is missing from allowlisted source: "
            f"{namespace}.{function_name}"
        )
    return namespace, function_name


def _detector_target_names(node: ast.AST) -> set[str]:
    return {
        child.id
        for child in ast.walk(node)
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store)
    }


def _detector_argument_names(arguments: ast.arguments) -> set[str]:
    return {
        argument.arg
        for argument in (
            *arguments.posonlyargs,
            *arguments.args,
            *arguments.kwonlyargs,
            *(() if arguments.vararg is None else (arguments.vararg,)),
            *(() if arguments.kwarg is None else (arguments.kwarg,)),
        )
    }


class _DetectorScopeBindingCollector(ast.NodeVisitor):
    """Collect bindings owned by one lexical scope without entering children."""

    def __init__(self) -> None:
        self.local_names: set[str] = set()
        self.global_names: set[str] = set()
        self.nonlocal_names: set[str] = set()

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Store):
            self.local_names.add(node.id)

    def visit_Global(self, node: ast.Global) -> None:
        self.global_names.update(node.names)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        self.nonlocal_names.update(node.names)

    def visit_Import(self, node: ast.Import) -> None:
        self.local_names.update(
            alias.asname or alias.name.split(".")[0] for alias in node.names
        )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        self.local_names.update(alias.asname or alias.name for alias in node.names)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if isinstance(node.name, str):
            self.local_names.add(node.name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.local_names.add(node.name)
        self._visit_definition_expressions(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.local_names.add(node.name)
        self._visit_definition_expressions(node)

    def _visit_definition_expressions(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> None:
        for expression in (
            *node.decorator_list,
            *node.args.defaults,
            *(item for item in node.args.kw_defaults if item is not None),
        ):
            self.visit(expression)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.local_names.add(node.name)
        for expression in (*node.decorator_list, *node.bases):
            self.visit(expression)
        for keyword in node.keywords:
            self.visit(keyword.value)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        for expression in (
            *node.args.defaults,
            *(item for item in node.args.kw_defaults if item is not None),
        ):
            self.visit(expression)

    def visit_ListComp(self, node: ast.ListComp) -> None:
        self._visit_comprehension_bindings(node)

    def visit_SetComp(self, node: ast.SetComp) -> None:
        self._visit_comprehension_bindings(node)

    def visit_DictComp(self, node: ast.DictComp) -> None:
        self._visit_comprehension_bindings(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        self._visit_comprehension_bindings(node)

    def _visit_comprehension_bindings(
        self,
        node: ast.ListComp | ast.SetComp | ast.DictComp | ast.GeneratorExp,
    ) -> None:
        collector = _DetectorNamedExpressionBindingCollector()
        collector.visit(node)
        self.local_names.update(collector.names)


class _DetectorNamedExpressionBindingCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.names: set[str] = set()

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        self.names.update(_detector_target_names(node.target))
        self.visit(node.value)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        return


def _detector_scope_bindings(
    body: list[ast.stmt],
    arguments: ast.arguments | None = None,
) -> tuple[set[str], set[str], set[str]]:
    collector = _DetectorScopeBindingCollector()
    for statement in body:
        collector.visit(statement)
    local_names = set(collector.local_names)
    if arguments is not None:
        local_names.update(_detector_argument_names(arguments))
    local_names.difference_update(collector.global_names)
    local_names.difference_update(collector.nonlocal_names)
    return local_names, collector.global_names, collector.nonlocal_names


class _DetectorGlobalLoadCollector(ast.NodeVisitor):
    """Resolve source loads that reach the repository module namespace."""

    def __init__(
        self,
        *,
        scope_kind: str,
        local_names: set[str] | None = None,
        global_names: set[str] | None = None,
        nonlocal_names: set[str] | None = None,
        enclosing_function_locals: tuple[frozenset[str], ...] = (),
        loaded_names: set[str] | None = None,
    ) -> None:
        self.scope_kind = scope_kind
        self.local_names = local_names or set()
        self.global_names = global_names or set()
        self.nonlocal_names = nonlocal_names or set()
        self.enclosing_function_locals = enclosing_function_locals
        self.loaded_names = loaded_names if loaded_names is not None else set()

    def _child_enclosing_function_locals(self) -> tuple[frozenset[str], ...]:
        if self.scope_kind in {"function", "lambda", "comprehension"}:
            return (frozenset(self.local_names), *self.enclosing_function_locals)
        return self.enclosing_function_locals

    def _child(
        self,
        *,
        scope_kind: str,
        local_names: set[str],
        global_names: set[str] | None = None,
        nonlocal_names: set[str] | None = None,
    ) -> _DetectorGlobalLoadCollector:
        return _DetectorGlobalLoadCollector(
            scope_kind=scope_kind,
            local_names=local_names,
            global_names=global_names,
            nonlocal_names=nonlocal_names,
            enclosing_function_locals=self._child_enclosing_function_locals(),
            loaded_names=self.loaded_names,
        )

    def _resolves_to_module(self, name: str) -> bool:
        if self.scope_kind == "module" or name in self.global_names:
            return True
        if name in self.local_names or name in self.nonlocal_names:
            return False
        return not any(
            name in scope_names for scope_names in self.enclosing_function_locals
        )

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load) and self._resolves_to_module(node.id):
            self.loaded_names.add(node.id)

    def _visit_function_definition(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> None:
        for expression in (
            *node.decorator_list,
            *node.args.defaults,
            *(item for item in node.args.kw_defaults if item is not None),
        ):
            self.visit(expression)
        for argument in (
            *node.args.posonlyargs,
            *node.args.args,
            *node.args.kwonlyargs,
            *(() if node.args.vararg is None else (node.args.vararg,)),
            *(() if node.args.kwarg is None else (node.args.kwarg,)),
        ):
            if argument.annotation is not None:
                self.visit(argument.annotation)
        if node.returns is not None:
            self.visit(node.returns)
        for type_parameter in getattr(node, "type_params", ()):
            self.visit(type_parameter)
        local_names, global_names, nonlocal_names = _detector_scope_bindings(
            node.body, node.args
        )
        child = self._child(
            scope_kind="function",
            local_names=local_names,
            global_names=global_names,
            nonlocal_names=nonlocal_names,
        )
        for statement in node.body:
            child.visit(statement)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function_definition(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function_definition(node)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        for expression in (
            *node.args.defaults,
            *(item for item in node.args.kw_defaults if item is not None),
        ):
            self.visit(expression)
        collector = _DetectorScopeBindingCollector()
        collector.visit(node.body)
        local_names = _detector_argument_names(node.args) | collector.local_names
        local_names.difference_update(collector.global_names)
        local_names.difference_update(collector.nonlocal_names)
        self._child(
            scope_kind="lambda",
            local_names=local_names,
            global_names=collector.global_names,
            nonlocal_names=collector.nonlocal_names,
        ).visit(node.body)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for expression in (*node.decorator_list, *node.bases):
            self.visit(expression)
        for keyword in node.keywords:
            self.visit(keyword.value)
        for type_parameter in getattr(node, "type_params", ()):
            self.visit(type_parameter)
        local_names, global_names, nonlocal_names = _detector_scope_bindings(node.body)
        child = self._child(
            scope_kind="class",
            local_names=local_names,
            global_names=global_names,
            nonlocal_names=nonlocal_names,
        )
        for statement in node.body:
            child.visit(statement)

    def _visit_comprehension(
        self,
        node: ast.ListComp | ast.SetComp | ast.DictComp | ast.GeneratorExp,
        result_expressions: tuple[ast.expr, ...],
    ) -> None:
        if not node.generators:
            raise ValidationProblem("detector comprehension has no generator")
        self.visit(node.generators[0].iter)
        local_names = set().union(
            *(_detector_target_names(item.target) for item in node.generators)
        )
        child = self._child(scope_kind="comprehension", local_names=local_names)
        for index, generator in enumerate(node.generators):
            if index:
                child.visit(generator.iter)
            for condition in generator.ifs:
                child.visit(condition)
        for expression in result_expressions:
            child.visit(expression)

    def visit_ListComp(self, node: ast.ListComp) -> None:
        self._visit_comprehension(node, (node.elt,))

    def visit_SetComp(self, node: ast.SetComp) -> None:
        self._visit_comprehension(node, (node.elt,))

    def visit_DictComp(self, node: ast.DictComp) -> None:
        self._visit_comprehension(node, (node.key, node.value))

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        self._visit_comprehension(node, (node.elt,))


def _detector_loaded_names(node: ast.AST) -> list[str]:
    collector = _DetectorGlobalLoadCollector(scope_kind="module")
    collector.visit(node)
    return sorted(collector.loaded_names)


def _detector_selected_binding_projection(
    symbol_id: str,
    symbol: dict[str, object],
    fields: tuple[str, ...],
) -> dict[str, object]:
    """Extract selected literal dict fields from one reachable source binding."""

    node = symbol.get("node")
    value_node = (
        node.value
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        else None
    )
    if not isinstance(value_node, ast.Dict):
        raise ValidationProblem(
            f"selected detector binding is not a dict literal: {symbol_id}"
        )
    values: dict[str, object] = {}
    duplicates: set[str] = set()
    for key_node, item_node in zip(value_node.keys, value_node.values):
        try:
            key = ast.literal_eval(key_node) if key_node is not None else None
        except (TypeError, ValueError, SyntaxError):
            continue
        if key not in fields:
            continue
        if key in values:
            duplicates.add(str(key))
            continue
        try:
            values[str(key)] = ast.literal_eval(item_node)
        except (TypeError, ValueError, SyntaxError) as exc:
            raise ValidationProblem(
                f"selected detector binding is not literal: {symbol_id}.{key}"
            ) from exc
    if duplicates:
        raise ValidationProblem(
            f"selected detector binding fields are duplicated: {symbol_id}: "
            + ", ".join(sorted(duplicates))
        )
    missing = sorted(set(fields) - set(values))
    if missing:
        raise ValidationProblem(
            f"selected detector binding fields are missing: {symbol_id}: "
            + ", ".join(missing)
        )
    return {field: values[field] for field in fields}


def _detector_evaluated_binding_projection(
    symbol_id: str,
    value: object,
) -> object:
    """Project one explicitly selected already-evaluated module constant."""

    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return json.loads(encoded)
    except (TypeError, ValueError, RecursionError, json.JSONDecodeError) as exc:
        raise ValidationProblem(
            f"evaluated detector binding is not canonical JSON: {symbol_id}"
        ) from exc


def _detector_repository_payload(
    roots: tuple[object, ...],
    *,
    contract_version: str,
    selected_binding_fields: dict[str, tuple[str, ...]] | None = None,
    evaluated_binding_values: dict[str, object] | None = None,
) -> dict[str, object]:
    """Project the exact allowlisted repository-symbol closure for detector roots."""

    catalog = _detector_source_catalog()
    import_namespaces = {
        namespace: namespace
        for namespace in catalog
        if namespace != "audit-skill-content"
    }
    selected_binding_fields = selected_binding_fields or {}
    evaluated_binding_values = evaluated_binding_values or {}
    overlap = sorted(set(selected_binding_fields) & set(evaluated_binding_values))
    if overlap:
        raise ValidationProblem(
            "detector binding cannot be both selected and evaluated: "
            + ", ".join(overlap)
        )
    pending = [_detector_root_selector(function, catalog) for function in roots]
    root_ids = sorted(f"{namespace}.{name}" for namespace, name in pending)
    symbols_payload: dict[str, dict[str, object]] = {}
    bindings: dict[str, dict[str, str]] = {}
    selected_payload: dict[str, dict[str, object]] = {}
    evaluated_payload: dict[str, object] = {}
    selected_seen: set[str] = set()
    evaluated_seen: set[str] = set()
    while pending:
        namespace, symbol_name = pending.pop()
        symbol_id = f"{namespace}.{symbol_name}"
        if symbol_id in symbols_payload:
            continue
        if symbol_id in selected_binding_fields:
            selected_seen.add(symbol_id)
            module = catalog[namespace]
            symbols = module["symbols"]
            assert isinstance(symbols, dict)
            symbol = symbols.get(symbol_name)
            if not isinstance(symbol, dict):
                raise ValidationProblem(
                    f"reachable detector symbol is missing: {symbol_id}"
                )
            projection = _detector_selected_binding_projection(
                symbol_id,
                symbol,
                selected_binding_fields[symbol_id],
            )
            selected_payload[symbol_id] = projection
            symbols_payload[symbol_id] = {
                "kind": "selected-binding",
                "source": json.dumps(
                    projection,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            }
            continue
        if symbol_id in evaluated_binding_values:
            evaluated_seen.add(symbol_id)
            module = catalog[namespace]
            symbols = module["symbols"]
            assert isinstance(symbols, dict)
            symbol = symbols.get(symbol_name)
            if not isinstance(symbol, dict) or symbol.get("kind") != "binding":
                raise ValidationProblem(
                    f"evaluated detector binding is missing: {symbol_id}"
                )
            projection = _detector_evaluated_binding_projection(
                symbol_id,
                evaluated_binding_values[symbol_id],
            )
            evaluated_payload[symbol_id] = projection
            symbols_payload[symbol_id] = {
                "kind": "evaluated-binding",
                "value": projection,
            }
            continue
        module = catalog[namespace]
        symbols = module["symbols"]
        imports = module["imports"]
        assert isinstance(symbols, dict) and isinstance(imports, dict)
        symbol = symbols.get(symbol_name)
        if not isinstance(symbol, dict):
            raise ValidationProblem(
                f"reachable detector symbol is missing: {symbol_id}"
            )
        node = symbol.get("node")
        source = symbol.get("source")
        kind = symbol.get("kind")
        if (
            not isinstance(node, ast.AST)
            or not isinstance(source, str)
            or not isinstance(kind, str)
        ):
            raise ValidationProblem(
                f"reachable detector symbol is malformed: {symbol_id}"
            )
        symbols_payload[symbol_id] = {"kind": kind, "source": source}
        for loaded_name in _detector_loaded_names(node):
            binding_id = f"{symbol_id}:{loaded_name}"
            if loaded_name in symbols:
                target = f"{namespace}.{loaded_name}"
                bindings[binding_id] = {
                    "kind": (
                        "selected-binding"
                        if target in selected_binding_fields
                        else "evaluated-binding"
                        if target in evaluated_binding_values
                        else "repository-symbol"
                    ),
                    "target": target,
                }
                pending.append((namespace, loaded_name))
                continue
            imported = imports.get(loaded_name)
            if not isinstance(imported, dict):
                if hasattr(builtins, loaded_name):
                    bindings[binding_id] = {
                        "kind": "external-builtin",
                        "target": f"builtins.{loaded_name}",
                    }
                    continue
                if loaded_name in _DETECTOR_IMPLICIT_MODULE_NAMES:
                    bindings[binding_id] = {
                        "kind": "module-implicit",
                        "target": f"python.{loaded_name}",
                    }
                    continue
                raise ValidationProblem(
                    "unknown detector source symbol: "
                    f"{namespace}.{loaded_name} loaded by {symbol_id}"
                )
            imported_module = imported.get("module")
            imported_name = imported.get("name")
            target_namespace = (
                import_namespaces.get(imported_module)
                if isinstance(imported_module, str)
                else None
            )
            target_symbols = (
                catalog[target_namespace]["symbols"]
                if target_namespace is not None
                else None
            )
            if (
                isinstance(imported_name, str)
                and isinstance(target_symbols, dict)
                and imported_name in target_symbols
            ):
                target = f"{target_namespace}.{imported_name}"
                bindings[binding_id] = {
                    "kind": "repository-symbol",
                    "target": target,
                }
                pending.append((target_namespace, imported_name))
            else:
                target = str(imported_module)
                if isinstance(imported_name, str):
                    target = f"{target}.{imported_name}"
                bindings[binding_id] = {
                    "kind": "external-import",
                    "target": target,
                }
    unused_selected = sorted(set(selected_binding_fields) - selected_seen)
    if unused_selected:
        raise ValidationProblem(
            "selected detector binding is unreachable: " + ", ".join(unused_selected)
        )
    unused_evaluated = sorted(set(evaluated_binding_values) - evaluated_seen)
    if unused_evaluated:
        raise ValidationProblem(
            "evaluated detector binding is unreachable: "
            + ", ".join(unused_evaluated)
        )
    return {
        "contract_version": contract_version,
        "walker_contract": _DETECTOR_SOURCE_WALKER_CONTRACT,
        "roots": root_ids,
        "symbols": {
            key: symbols_payload[key] for key in sorted(symbols_payload)
        },
        "bindings": {key: bindings[key] for key in sorted(bindings)},
        "selected_bindings": {
            key: selected_payload[key] for key in sorted(selected_payload)
        },
        "evaluated_bindings": {
            key: evaluated_payload[key] for key in sorted(evaluated_payload)
        },
    }


def _explicit_detector_source_manifest(
    *,
    contract_version: str,
    contract_fields: dict[str, object] | None = None,
) -> dict[str, object]:
    """Bind a versioned contract to an explicit repository source manifest."""

    source_manifest = []
    for relative in _DETECTOR_REPOSITORY_SOURCE_PATHS:
        source = _detector_repository_source_text(ROOT / relative)
        source_manifest.append(
            {
                "path": relative,
                "sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
            }
        )
    payload: dict[str, object] = {
        "contract_version": contract_version,
        "source_manifest": source_manifest,
        "contract_fields": contract_fields or {},
    }
    payload["aggregate_source_digest"] = hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return payload


def _root_semantic_detector_payload() -> dict[str, object]:
    """Return the closed reachable-behavior projection for Root semantics."""

    return _detector_repository_payload(
        (
            _ROOT_SKILL_DOCUMENTS_DETECTOR_SOURCE,
            _ROOT_SENTENCE_CANDIDATES_DETECTOR_SOURCE,
            _ROOT_DOCUMENT_CANDIDATES_DETECTOR_SOURCE,
            _FOLD_ROOT_CANDIDATES_DETECTOR_SOURCE,
        ),
        contract_version="root-semantic-detector-contract-v1",
        selected_binding_fields={
            "audit-skill-content.THRESHOLDS": (
                "root_tutorial_density_min_words",
            )
        },
        evaluated_binding_values={
            "validation_utils.REFERENCE_CONTRACT_MODEL": (
                _validation_utils.REFERENCE_CONTRACT_MODEL
            ),
            "validation_utils.ROLE_CONTRACT_MODEL": (
                _validation_utils.ROLE_CONTRACT_MODEL
            ),
        },
    )


def _root_semantic_detector_fingerprint() -> str:
    """Return the canonical digest of reachable Root detector behavior."""

    return hashlib.sha256(
        json.dumps(
            _root_semantic_detector_payload(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _root_semantic_detector_contract() -> dict[str, str]:
    return {
        "contract_version": "root-semantic-detector-contract-v1",
        "algorithm": "sha256-canonical-json-v1",
        "value": _root_semantic_detector_fingerprint(),
    }


def _reference_semantic_detector_payload() -> dict[str, object]:
    """Return the closed reachable-behavior projection for Reference semantics."""

    return _detector_repository_payload(
        (_reference_semantic_candidates,),
        contract_version="reference-semantic-detector-contract-v1",
    )


def _reference_semantic_detector_fingerprint() -> str:
    return hashlib.sha256(
        json.dumps(
            _reference_semantic_detector_payload(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _reference_semantic_detector_contract() -> dict[str, str]:
    return {
        "contract_version": "reference-semantic-detector-contract-v1",
        "algorithm": "sha256-canonical-json-v1",
        "value": _reference_semantic_detector_fingerprint(),
    }

def _ordered_unique_strings(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _root_surface_for_document(value: object) -> str | None:
    if not isinstance(value, dict):
        return None
    if value.get("document_part") == "description":
        return "description"
    return ROOT_LAYER_SURFACES.get(str(value.get("layer", "")))


def _reference_surface_for_path(path: object) -> str | None:
    if not isinstance(path, str) or not path:
        return None
    prefixes = (
        ("src/control-skills/", "control"),
        ("src/professional-skills/", "professional"),
        ("src/foundation/capabilities/", "foundation"),
        ("src/domain-extensions/", "domain"),
    )
    for prefix, surface in prefixes:
        if path.startswith(prefix):
            return surface
    registry_paths = {
        _repository_relative_path(registry): layer
        for layer, registry, _key, _root in REFERENCE_SOURCES
    }
    return registry_paths.get(path)


def _reference_surfaces_for_candidate(candidate: object) -> set[str]:
    if not isinstance(candidate, dict):
        return set()
    layer = candidate.get("layer")
    if layer in REFERENCE_CONTENT_SURFACES:
        return {str(layer)}
    surfaces = {
        str(item.get("layer"))
        for item in candidate.get("occurrences") or []
        if isinstance(item, dict)
        and item.get("layer") in REFERENCE_CONTENT_SURFACES
    }
    if surfaces:
        return surfaces
    inferred = _reference_surface_for_path(candidate.get("path"))
    return {inferred} if inferred is not None else set()


def _root_surfaces_for_entry(
    entry: object,
    candidate_by_id: dict[str, dict],
) -> set[str]:
    if not isinstance(entry, dict):
        return set()
    candidate = candidate_by_id.get(str(entry.get("candidate_id", "")))
    surface = _root_surface_for_document(candidate)
    if surface is not None:
        return {surface}
    if entry.get("document_part") == "description":
        return {"description"}
    inferred = _reference_surface_for_path(entry.get("path"))
    if inferred is not None:
        return {inferred}
    if str(entry.get("path", "")).startswith("src/control-prompts/"):
        return {"control"}
    return set()


def _reference_surfaces_for_entry(
    entry: object,
    candidate_by_id: dict[str, dict],
) -> set[str]:
    if not isinstance(entry, dict):
        return set()
    candidate = candidate_by_id.get(str(entry.get("candidate_id", "")))
    surfaces = _reference_surfaces_for_candidate(candidate)
    if surfaces:
        return surfaces
    inferred = _reference_surface_for_path(entry.get("path"))
    return {inferred} if inferred is not None else set()


def _indexed_error_position(error: str, prefix: str) -> int | None:
    match = re.match(rf"^{re.escape(prefix)}\[(\d+)\]", error)
    return int(match.group(1)) if match else None


def _root_disposition_error_attribution(
    errors: list[str],
    entries: object,
    candidates: list[dict],
) -> tuple[list[str], dict[str, list[str]]]:
    by_surface = {surface: [] for surface in ROOT_CONTENT_SURFACES}
    common: list[str] = []
    raw_entries = entries if isinstance(entries, list) else []
    candidate_by_id = {
        str(item.get("candidate_id")): item
        for item in candidates
        if isinstance(item, dict) and isinstance(item.get("candidate_id"), str)
    }
    prefix = f"{ROOT_SEMANTIC_DISPOSITION_KEY}.entries"
    for error in errors:
        entry_index = _indexed_error_position(error, prefix)
        candidate_index = _indexed_error_position(error, "root semantic candidate")
        if entry_index is not None and entry_index < len(raw_entries):
            surfaces = _root_surfaces_for_entry(
                raw_entries[entry_index], candidate_by_id
            )
        elif candidate_index is not None and candidate_index < len(candidates):
            surface = _root_surface_for_document(candidates[candidate_index])
            surfaces = {surface} if surface is not None else set()
        else:
            surfaces = set()
        if not surfaces:
            common.append(error)
            continue
        for surface in sorted(surfaces):
            by_surface[surface].append(error)
    return _ordered_unique_strings(common), {
        surface: _ordered_unique_strings(by_surface[surface])
        for surface in ROOT_CONTENT_SURFACES
    }


def _reference_disposition_error_attribution(
    errors: list[str],
    entries: object,
    candidates: list[dict],
) -> tuple[list[str], dict[str, list[str]]]:
    by_surface = {surface: [] for surface in REFERENCE_CONTENT_SURFACES}
    common: list[str] = []
    raw_entries = entries if isinstance(entries, list) else []
    candidate_by_id = {
        str(item.get("candidate_id")): item
        for item in candidates
        if isinstance(item, dict) and isinstance(item.get("candidate_id"), str)
    }
    for error in errors:
        entry_index = _indexed_error_position(
            error, "reference_semantic_dispositions.entries"
        )
        candidate_index = _indexed_error_position(error, "semantic candidate")
        if entry_index is not None and entry_index < len(raw_entries):
            surfaces = _reference_surfaces_for_entry(
                raw_entries[entry_index], candidate_by_id
            )
        elif candidate_index is not None and candidate_index < len(candidates):
            surfaces = _reference_surfaces_for_candidate(candidates[candidate_index])
        else:
            surfaces = set()
        if not surfaces:
            common.append(error)
            continue
        for surface in sorted(surfaces):
            by_surface[surface].append(error)
    return _ordered_unique_strings(common), {
        surface: _ordered_unique_strings(by_surface[surface])
        for surface in REFERENCE_CONTENT_SURFACES
    }


def _blocked_surfaces(
    surfaces: tuple[str, ...],
    common_errors: list[str],
    surface_errors: dict[str, list[str]],
) -> set[str]:
    if common_errors:
        return set(surfaces)
    return {surface for surface in surfaces if surface_errors.get(surface)}


def _collect_root_semantic_advisories(
    documents: list[dict],
    *,
    disposition_entries: object = _USE_CONFIG_DISPOSITIONS,
    evaluation_date: date | None = None,
) -> dict:
    candidates = _fold_root_candidates(
        [
            candidate
            for document in documents
            for candidate in (
                _root_sentence_candidates(document) + _root_document_candidates(document)
            )
        ]
    )
    evaluated_on = (
        _effective_evaluation_date()
        if evaluation_date is None
        else evaluation_date
    )
    if disposition_entries is _USE_CONFIG_DISPOSITIONS:
        contract, contract_errors = _load_root_semantic_dispositions()
    elif isinstance(disposition_entries, list):
        contract = {
            "schema_version": ROOT_SEMANTIC_DISPOSITION_SCHEMA_VERSION,
            "entries": disposition_entries,
        }
        contract_errors = []
    elif isinstance(disposition_entries, dict):
        contract = disposition_entries
        contract_errors = []
    else:
        contract = {"schema_version": None, "entries": []}
        contract_errors = [f"{ROOT_SEMANTIC_DISPOSITION_KEY} must be a mapping or list"]
    if contract.get("schema_version") != ROOT_SEMANTIC_DISPOSITION_SCHEMA_VERSION:
        contract_errors.append(
            f"{ROOT_SEMANTIC_DISPOSITION_KEY}.schema_version must equal "
            f"{ROOT_SEMANTIC_DISPOSITION_SCHEMA_VERSION}"
        )
    entries = contract.get("entries")
    normalized, matches, errors = _validate_root_semantic_dispositions(
        candidates, entries, evaluated_on, require_applied=False
    )
    contract_errors.extend(errors)
    for candidate_index, candidate in enumerate(candidates):
        if _root_surface_for_document(candidate) is None:
            contract_errors.append(
                f"root semantic candidate[{candidate_index}]: cannot be attributed to a declared Root surface"
            )
    disposition_common_errors, disposition_surface_errors = (
        _root_disposition_error_attribution(contract_errors, entries, candidates)
    )
    blocked_surfaces = _blocked_surfaces(
        ROOT_CONTENT_SURFACES,
        disposition_common_errors,
        disposition_surface_errors,
    )
    normalized_by_id = {
        str(item.get("candidate_id")): item
        for item in normalized
        if isinstance(item, dict) and isinstance(item.get("candidate_id"), str)
    }
    applied = 0
    for _entry_index, candidate_index in sorted(matches.items()):
        candidate = candidates[candidate_index]
        surface = _root_surface_for_document(candidate)
        entry = normalized_by_id.get(str(candidate.get("candidate_id", "")))
        if (
            not isinstance(entry, dict)
            or surface is None
            or surface in blocked_surfaces
        ):
            continue
        entry = dict(entry)
        candidate["priority"] = entry["priority"]
        candidate["disposition"] = entry["disposition"]
        candidate["disposition_record"] = entry
        candidate["resolved"] = entry["disposition"] in SEMANTIC_RESOLVED_DISPOSITIONS
        candidate["unresolved"] = not candidate["resolved"]
        candidate["governance_status"] = (
            f"resolved-{entry['disposition']}"
            if candidate["resolved"] else "unresolved-rewrite"
        )
        applied += 1
    by_finding = {}
    for finding in ROOT_SEMANTIC_FINDINGS:
        rows = [item for item in candidates if item["finding"] == finding]
        by_finding[finding] = {
            "raw": len(rows),
            "untriaged": sum(item["governance_status"] == "untriaged" for item in rows),
            "rewrite": sum(item["disposition"] == "rewrite" for item in rows),
            "resolved": sum(bool(item["resolved"]) for item in rows),
            "unresolved": sum(bool(item["unresolved"]) for item in rows),
            "p0_unresolved": sum(item["unresolved"] and item["priority"] == "P0" for item in rows),
            "p1_unresolved": sum(item["unresolved"] and item["priority"] == "P1" for item in rows),
            "p2_unresolved": sum(item["unresolved"] and item["priority"] == "P2" for item in rows),
        }
    unresolved = sum(item["unresolved"] for item in candidates)
    p0_p1 = sum(
        item["unresolved"] and item["priority"] in {"P0", "P1"}
        for item in candidates
    )
    fixed = by_finding["fixed_duration_threshold_status_candidate"]["unresolved"]
    return {
        "schema_version": ROOT_SEMANTIC_SCHEMA_VERSION,
        "detector_contract": _root_semantic_detector_contract(),
        "finding_families": list(ROOT_SEMANTIC_FINDINGS),
        "summary": {
            "raw_candidates": len(candidates),
            "untriaged_candidates": sum(item["governance_status"] == "untriaged" for item in candidates),
            "rewrite_candidates": sum(item["disposition"] == "rewrite" for item in candidates),
            "resolved_candidates": sum(item["resolved"] for item in candidates),
            "unresolved_candidates": unresolved,
            "p0_unresolved_candidates": sum(item["unresolved"] and item["priority"] == "P0" for item in candidates),
            "p1_unresolved_candidates": sum(item["unresolved"] and item["priority"] == "P1" for item in candidates),
            "p2_unresolved_candidates": sum(item["unresolved"] and item["priority"] == "P2" for item in candidates),
            "by_finding": by_finding,
            "strict_unresolved": {
                "p0_p1_candidates": p0_p1,
                "fixed_number_candidates": fixed,
            },
        },
        "candidates": candidates,
        "disposition_contract": {
            "schema_version": ROOT_SEMANTIC_DISPOSITION_SCHEMA_VERSION,
            "source": SKILL_CONTENT_EXCEPTIONS_FILE.relative_to(ROOT).as_posix(),
            "configured_count": len(entries) if isinstance(entries, list) else 0,
            "applied_count": applied,
            "entries": normalized,
            "errors": contract_errors,
            "common_errors": disposition_common_errors,
            "surface_errors": disposition_surface_errors,
        },
        "limitations": [
            "Root detectors are high-precision lexical governance candidates, not expert judgments about whether a rule is correct.",
            "Authority and context downgrades are clause-local; novel valid contexts require an exact disposition rather than borrowing authority from another clause.",
            f"Vendor/tool lexicon source: {ROOT_VENDOR_TOOL_LEXICON_SOURCE}",
            "Tutorial density uses headings plus repeated explanatory markers and does not replace expert content review.",
            "Git history and the current fixed Semantic attestation provide the review audit trail.",
        ],
    }


def _root_surface_validation(
    documents: list[dict],
    advisories: dict,
    semantic: dict,
) -> dict:
    candidates = [
        item for item in semantic.get("candidates") or [] if isinstance(item, dict)
    ]
    contract = semantic.get("disposition_contract")
    contract = contract if isinstance(contract, dict) else {}
    entries = contract.get("entries")
    entries = entries if isinstance(entries, list) else []
    reported_errors = contract.get("errors")
    reported_errors = (
        [str(item) for item in reported_errors]
        if isinstance(reported_errors, list)
        else ["root semantic disposition errors must be a list"]
    )
    common_errors, disposition_errors = _root_disposition_error_attribution(
        reported_errors,
        entries,
        candidates,
    )
    for index, document in enumerate(documents):
        if _root_surface_for_document(document) is None:
            common_errors.append(
                f"root document[{index}] cannot be attributed to a declared Root surface"
            )
    for index, candidate in enumerate(candidates):
        if _root_surface_for_document(candidate) is None:
            common_errors.append(
                f"root semantic candidate[{index}] cannot be attributed to a declared Root surface"
            )
    candidate_by_id = {
        str(item.get("candidate_id")): item
        for item in candidates
        if isinstance(item.get("candidate_id"), str)
    }

    strict_advisory_gates = {
        "foundation": (
            ("Foundation root(s) over class hard word limit", "foundation_over_hard_words"),
            ("Foundation root(s) over 900 tokens", "foundation_over_hard_tokens"),
            ("Foundation High-Value Rules count outside 3-8", "foundation_rule_count_outside_target"),
            ("Foundation High-Value Rule(s) over two sentences", "foundation_rules_over_sentence_limit"),
            ("Foundation High-Value Rule(s) without decision semantics", "foundation_rules_without_decision_semantics"),
            ("Foundation root(s) below required decision density", "foundation_low_decision_density"),
        ),
        "professional": (
            ("Professional root(s) over 650 words", "professional_over_hard_words"),
            ("Professional root(s) over 1000 tokens", "professional_over_hard_tokens"),
        ),
        "domain": (
            ("Domain root(s) over 600 words", "domain_over_hard_words"),
            ("Domain root(s) over 900 tokens", "domain_over_hard_tokens"),
        ),
    }

    surfaces: dict[str, dict] = {}
    for surface in ROOT_CONTENT_SURFACES:
        surface_documents = [
            item for item in documents if _root_surface_for_document(item) == surface
        ]
        surface_candidates = [
            item for item in candidates if _root_surface_for_document(item) == surface
        ]
        p0_p1 = sum(
            bool(item.get("unresolved")) and item.get("priority") in {"P0", "P1"}
            for item in surface_candidates
        )
        fixed = sum(
            bool(item.get("unresolved"))
            and item.get("finding") == "fixed_duration_threshold_status_candidate"
            for item in surface_candidates
        )
        errors = list(disposition_errors[surface])
        if p0_p1:
            errors.append(f"root P0/P1 unresolved semantic candidate(s): {p0_p1}")
        if fixed:
            errors.append(f"root fixed-number unresolved semantic candidate(s): {fixed}")
        for label, key in strict_advisory_gates.get(surface, ()):
            count = len(advisories.get(key) or [])
            if count:
                errors.append(f"{label}: {count}")
        configured = sum(
            surface
            in _root_surfaces_for_entry(entry, candidate_by_id)
            for entry in entries
        )
        applied = sum(
            _root_surface_for_document(candidate) == surface
            and candidate.get("disposition_record") is not None
            for candidate in candidates
        )
        errors = _ordered_unique_strings(errors)
        surfaces[surface] = {
            "status": "pass" if not common_errors and not errors else "fail",
            "document_count": len(surface_documents),
            "semantic_candidate_count": len(surface_candidates),
            "semantic_unresolved_count": sum(
                bool(item.get("unresolved")) for item in surface_candidates
            ),
            "semantic_p0_p1_unresolved_count": p0_p1,
            "semantic_fixed_number_unresolved_count": fixed,
            "disposition_configured_count": configured,
            "disposition_applied_count": applied,
            "errors": errors,
        }
    return {
        "schema_version": SURFACE_VALIDATION_SCHEMA_VERSION,
        "common_errors": _ordered_unique_strings(common_errors),
        "surfaces": surfaces,
    }


def _collect_root_content(
    foundation_contracts: dict[str, dict] | None = None,
    *,
    evaluation_date: date | None = None,
) -> dict:
    effective_evaluation_date = (
        _effective_evaluation_date()
        if evaluation_date is None
        else evaluation_date
    )
    foundation_contracts = (
        foundation_contracts
        if foundation_contracts is not None
        else _load_foundation_content_contracts()
    )
    documents = _root_skill_documents(foundation_contracts)
    document_rows: list[dict] = []
    advisories = {
        "content_review_density": [],
        "content_tighten_body": [],
        "content_blockers": [],
        "foundation_over_target_words": [],
        "foundation_over_hard_words": [],
        "foundation_over_hard_tokens": [],
        "foundation_compact_over_target_words": [],
        "foundation_compact_over_hard_words": [],
        "foundation_complex_over_target_words": [],
        "foundation_complex_over_hard_words": [],
        "foundation_rule_count_outside_target": [],
        "foundation_rules_over_sentence_limit": [],
        "foundation_rules_without_decision_semantics": [],
        "foundation_long_prose_line": [],
        "foundation_tutorial_density": [],
        "foundation_low_decision_density": [],
        "professional_over_target_words": [],
        "professional_over_hard_words": [],
        "professional_over_target_tokens": [],
        "professional_over_hard_tokens": [],
        "domain_over_target_words": [],
        "domain_over_hard_words": [],
        "domain_over_target_tokens": [],
        "domain_over_hard_tokens": [],
    }
    for document in documents:
        body = str(document.get("governed_text", document["text"]))
        source_body = str(document["text"])
        row = {
            "path": document["path"],
            "document_part": document["document_part"],
            "document_id": f"{document['path']}#{document['document_part']}",
            "layer": document["layer"],
            "owner": document["owner"],
            "word_count": len(body.split()),
            "token_count": count_o200k_base_tokens(body),
            "line_count": len(body.splitlines()),
            "content_fingerprint": hashlib.sha256(
                source_body.encode("utf-8")
            ).hexdigest(),
        }
        is_budgeted_body = document["document_part"] == "body" and document[
            "layer"
        ] in {
            "professional-skill",
            "foundation-capability",
            "domain-extension",
        }
        if is_budgeted_body:
            layer = str(document["layer"])
            if layer == "foundation-capability":
                content_class = str(document["content_class"])
                target_words = int(document["target_words"])
                hard_words = int(document["hard_words"])
                target_tokens = None
                hard_tokens = THRESHOLDS["foundation_hard_tokens"]
            else:
                layer_budget = LAYER_ROOT_CONTENT_BUDGETS[layer]
                content_class = None
                target_words = int(layer_budget["target_words"])
                hard_words = int(layer_budget["hard_words"])
                target_tokens = int(layer_budget["target_tokens"])
                hard_tokens = int(layer_budget["hard_tokens"])
            classification = classify_content_budget(
                word_count=row["word_count"],
                token_count=row["token_count"],
                target_words=target_words,
                hard_words=hard_words,
                target_tokens=target_tokens,
                hard_tokens=hard_tokens,
            )
            over_target_words = row["word_count"] > target_words
            over_hard_words = row["word_count"] > hard_words
            over_target_tokens = (
                target_tokens is not None and row["token_count"] > target_tokens
            )
            over_hard_tokens = row["token_count"] > hard_tokens
            row.update(
                {
                    "content_class": content_class,
                    "content_class_rationale": (
                        document.get("content_class_rationale")
                        if content_class is not None
                        else None
                    ),
                    "content_budget_scope": LAYER_ROOT_CONTENT_BUDGET_SCOPE,
                    "content_target_words": target_words,
                    "content_hard_words": hard_words,
                    "content_target_tokens": target_tokens,
                    "content_hard_tokens": hard_tokens,
                    "over_content_target_words": over_target_words,
                    "over_content_hard_words": over_hard_words,
                    "over_content_target_tokens": over_target_tokens,
                    "over_content_hard_tokens": over_hard_tokens,
                    "over_content_target": (
                        over_target_words or over_target_tokens
                    ),
                    "over_content_hard": over_hard_words or over_hard_tokens,
                    "content_budget_classification": classification,
                }
            )
            classification_advisory = {
                "REVIEW_DENSITY": "content_review_density",
                "TIGHTEN_BODY": "content_tighten_body",
                "BLOCK": "content_blockers",
            }.get(classification)
            if classification_advisory is not None:
                advisories[classification_advisory].append(row["path"])

            layer_prefix = {
                "professional-skill": "professional",
                "foundation-capability": "foundation",
                "domain-extension": "domain",
            }[layer]
            for suffix, active in (
                ("over_target_words", over_target_words),
                ("over_hard_words", over_hard_words),
                ("over_target_tokens", over_target_tokens),
                ("over_hard_tokens", over_hard_tokens),
            ):
                key = f"{layer_prefix}_{suffix}"
                if active and key in advisories:
                    advisories[key].append(row["path"])

        if (
            document["layer"] == "foundation-capability"
            and document["document_part"] == "body"
        ):
            content_class = str(document["content_class"])
            facts = _foundation_content_facts(body, parse_sections(body))
            row.update(facts)
            if row["over_content_target_words"]:
                advisories[
                    f"foundation_{content_class}_over_target_words"
                ].append(row["path"])
            if row["over_content_hard_words"]:
                advisories[
                    f"foundation_{content_class}_over_hard_words"
                ].append(row["path"])
            if not THRESHOLDS["foundation_rule_min"] <= row["high_value_rule_count"] <= THRESHOLDS["foundation_rule_max"]:
                advisories["foundation_rule_count_outside_target"].append(row["path"])
            if row["high_value_rules_over_sentence_limit"]:
                advisories["foundation_rules_over_sentence_limit"].append(row["path"])
            if row["high_value_rules_without_decision_semantics"]:
                advisories["foundation_rules_without_decision_semantics"].append(
                    row["path"]
                )
            if row["max_prose_line_words"] > THRESHOLDS["foundation_prose_line_words_max"]:
                advisories["foundation_long_prose_line"].append(row["path"])
            if row["tutorial_explanatory_density"] >= THRESHOLDS["foundation_tutorial_density_warn"]:
                advisories["foundation_tutorial_density"].append(row["path"])
            if row["decision_density"] < THRESHOLDS["foundation_decision_density_warn"]:
                advisories["foundation_low_decision_density"].append(row["path"])
        document_rows.append(row)
    manifest = "\n".join(
        "\0".join(
            (
                str(row["path"]),
                str(row["document_part"]),
                str(row["content_fingerprint"]),
                str(row.get("content_class") or ""),
                str(row.get("content_class_rationale") or ""),
                str(row.get("content_target_words") or ""),
                str(row.get("content_hard_words") or ""),
                str(row.get("content_target_tokens") or ""),
                str(row.get("content_hard_tokens") or ""),
                str(row.get("content_budget_scope") or ""),
                str(row.get("content_budget_classification") or ""),
            )
        )
        for row in document_rows
    )
    semantic = _collect_root_semantic_advisories(
        documents,
        evaluation_date=effective_evaluation_date,
    )
    surface_validation = _root_surface_validation(document_rows, advisories, semantic)
    foundation_derivation_snapshot = dict(FOUNDATION_DERIVATION_SNAPSHOT)
    return {
        "schema_version": ROOT_CONTENT_SCHEMA_VERSION,
        "source_fingerprint": {
            "algorithm": "sha256",
            "value": hashlib.sha256(("root-content-v8\0" + manifest).encode("utf-8")).hexdigest(),
            "document_count": len(document_rows),
        },
        "summary": {
            "agent_facing_root_documents": len(document_rows),
            "agent_facing_root_files": len({row["path"] for row in document_rows}),
            "description_document_parts": sum(
                row["document_part"] == "description" for row in document_rows
            ),
            "control_prompts": sum(row["document_part"] == "control-prompt" for row in document_rows),
            "control_skills": sum(row["layer"] == "control-skill" and row["document_part"] == "body" for row in document_rows),
            "professional_skills": sum(row["layer"] == "professional-skill" and row["document_part"] == "body" for row in document_rows),
            "foundation_capabilities": sum(row["layer"] == "foundation-capability" and row["document_part"] == "body" for row in document_rows),
            "foundation_compact_capabilities": sum(
                row.get("content_class") == "compact" for row in document_rows
            ),
            "foundation_complex_capabilities": sum(
                row.get("content_class") == "complex" for row in document_rows
            ),
            "domain_extensions": sum(row["layer"] == "domain-extension" and row["document_part"] == "body" for row in document_rows),
            "content_keep": sum(
                row.get("content_budget_classification") == "KEEP"
                for row in document_rows
            ),
            "content_review_density": len(advisories["content_review_density"]),
            "content_tighten_body": len(advisories["content_tighten_body"]),
            "content_blockers": len(advisories["content_blockers"]),
            "foundation_over_target_words": len(advisories["foundation_over_target_words"]),
            "foundation_over_hard_words": len(advisories["foundation_over_hard_words"]),
            "foundation_over_hard_tokens": len(advisories["foundation_over_hard_tokens"]),
            "foundation_compact_over_target_words": len(
                advisories["foundation_compact_over_target_words"]
            ),
            "foundation_compact_over_hard_words": len(
                advisories["foundation_compact_over_hard_words"]
            ),
            "foundation_complex_over_target_words": len(
                advisories["foundation_complex_over_target_words"]
            ),
            "foundation_complex_over_hard_words": len(
                advisories["foundation_complex_over_hard_words"]
            ),
            "foundation_rule_count_outside_target": len(advisories["foundation_rule_count_outside_target"]),
            "foundation_rules_over_sentence_limit": len(advisories["foundation_rules_over_sentence_limit"]),
            "foundation_rules_without_decision_semantics": len(
                advisories["foundation_rules_without_decision_semantics"]
            ),
            "foundation_long_prose_line": len(advisories["foundation_long_prose_line"]),
            "foundation_tutorial_density": len(advisories["foundation_tutorial_density"]),
            "foundation_low_decision_density": len(advisories["foundation_low_decision_density"]),
            "professional_over_target_words": len(
                advisories["professional_over_target_words"]
            ),
            "professional_over_hard_words": len(
                advisories["professional_over_hard_words"]
            ),
            "professional_over_target_tokens": len(
                advisories["professional_over_target_tokens"]
            ),
            "professional_over_hard_tokens": len(
                advisories["professional_over_hard_tokens"]
            ),
            "domain_over_target_words": len(
                advisories["domain_over_target_words"]
            ),
            "domain_over_hard_words": len(
                advisories["domain_over_hard_words"]
            ),
            "domain_over_target_tokens": len(
                advisories["domain_over_target_tokens"]
            ),
            "domain_over_hard_tokens": len(
                advisories["domain_over_hard_tokens"]
            ),
            "semantic_raw_candidates": semantic["summary"]["raw_candidates"],
            "semantic_unresolved_candidates": semantic["summary"]["unresolved_candidates"],
            "semantic_p0_p1_unresolved": semantic["summary"]["strict_unresolved"]["p0_p1_candidates"],
            "semantic_fixed_number_unresolved": semantic["summary"]["strict_unresolved"]["fixed_number_candidates"],
            "semantic_disposition_configured": semantic["disposition_contract"]["configured_count"],
            "semantic_disposition_applied": semantic["disposition_contract"]["applied_count"],
            "semantic_disposition_errors": len(semantic["disposition_contract"]["errors"]),
        },
        "documents": document_rows,
        "advisories": advisories,
        "layer_root_budget_contract": {
            "schema_version": 1,
            "scope": LAYER_ROOT_CONTENT_BUDGET_SCOPE,
            "classifications": list(CONTENT_BUDGET_CLASSIFICATIONS),
            "target_enforcement": "expert-disposition-required",
            "hard_enforcement": "strict-no-exception",
            "tighten_threshold": "greater-than-90-percent-of-triggered-hard-limit",
            "layers": LAYER_ROOT_CONTENT_BUDGETS,
        },
        "foundation_budget_contract": {
            "schema_version": 1,
            "registry_schema_version": REGISTRY_SCHEMA_VERSIONS["foundation"],
            "content_classes": {
                "compact": {
                    **FOUNDATION_CONTENT_BUDGETS["compact"],
                    "rationale_required": False,
                },
                "complex": {
                    **FOUNDATION_CONTENT_BUDGETS["complex"],
                    "rationale_required": True,
                },
            },
            "hard_token_limit": THRESHOLDS["foundation_hard_tokens"],
            "content_budget_scope": LAYER_ROOT_CONTENT_BUDGET_SCOPE,
            "target_enforcement": "expert-disposition-required",
            "strict_basis": "class-hard-word-limit-and-universal-hard-token-limit",
            "class_counts": {
                content_class: sum(
                    row.get("content_class") == content_class
                    for row in document_rows
                )
                for content_class in sorted(FOUNDATION_CONTENT_CLASSES)
            },
            "derivation_snapshot": foundation_derivation_snapshot,
            "rule_contract": (
                "Count every High-Value Rules list item, including nested items; "
                "every rule needs substantive decision, condition, risk, evidence, "
                "or authority semantics."
            ),
        },
        "semantic_advisories": semantic,
        "surface_validation": surface_validation,
    }


def _canonical_decision_section_heading(title: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", title.casefold()))


def _generic_decision_section_heading(title: str) -> bool:
    tokens = _canonical_decision_section_heading(title).split()
    return not tokens or all(
        token.isdigit()
        or token in DECISION_SECTION_GENERIC_TOKENS
        or token in DECISION_SECTION_NUMBER_TOKENS
        for token in tokens
    )


def _markdown_structural_facts(markdown: str, inferred_kind: str) -> dict:
    lines = markdown.splitlines()
    headings = _heading_records(markdown)
    ranged_headings: list[dict] = []
    for position, heading in enumerate(headings):
        end = len(lines)
        for later in headings[position + 1:]:
            if later["level"] <= heading["level"]:
                end = later["_index"]
                break
        ranged_headings.append({**heading, "_end": end})
    h1_count = sum(item["level"] == 1 for item in headings)
    h1_status = "exactly-one" if h1_count == 1 else ("missing" if h1_count == 0 else "multiple")

    empty_headings: list[dict] = []
    for position, heading in enumerate(headings):
        end = headings[position + 1]["_index"] if position + 1 < len(headings) else len(lines)
        content = False
        for line in lines[heading["_index"] + 1:end]:
            if not line.strip() or FENCE_RE.match(line.strip()):
                continue
            content = True
            break
        if not content:
            empty_headings.append(
                {key: heading[key] for key in ("level", "title", "line")}
            )

    decision_headings = [
        {key: heading[key] for key in ("level", "title", "line")}
        for heading in headings
        if DECISION_HEADING_RE.search(heading["title"])
    ]
    decision_roots: list[dict] = []
    for heading in ranged_headings:
        if not DECISION_HEADING_RE.search(heading["title"]):
            continue
        if any(
            root["_index"] < heading["_index"] < root["_end"]
            and heading["level"] > root["level"]
            for root in decision_roots
        ):
            continue
        decision_roots.append(heading)

    decision_line_indices: set[int] = set()
    for root in decision_roots:
        decision_line_indices.update(range(root["_index"] + 1, root["_end"]))

    annotated = _strip_fenced(lines)
    decision_list_indices = {
        index
        for index, line, in_fence in annotated
        if index in decision_line_indices
        and not in_fence
        and DECISION_LIST_ITEM_RE.match(line)
    }
    decision_table_indices = _table_item_indices(markdown) & decision_line_indices

    empty_heading_lines = {item["line"] for item in empty_headings}
    invalid_decision_section_headings: list[dict] = []
    valid_sections_by_root: dict[int, list[dict]] = {}
    for root in decision_roots:
        valid_sections: list[dict] = []
        for heading in ranged_headings:
            if not (
                root["_index"] < heading["_index"] < root["_end"]
                and heading["level"] > root["level"]
            ):
                continue
            reason = None
            if heading["line"] in empty_heading_lines:
                reason = "empty-section"
            elif _generic_decision_section_heading(heading["title"]):
                reason = "generic-heading"
            if reason is not None:
                invalid_decision_section_headings.append(
                    {
                        "level": heading["level"],
                        "title": heading["title"],
                        "line": heading["line"],
                        "reason": reason,
                    }
                )
                continue
            valid_sections.append(heading)
        valid_sections_by_root[root["_index"]] = valid_sections

        for index, line, in_fence in annotated:
            if (
                root["_index"] < index < root["_end"]
                and not in_fence
                and (match := EMPTY_ATX_HEADING_RE.match(line)) is not None
                and len(match.group(1)) > root["level"]
            ):
                invalid_decision_section_headings.append(
                    {
                        "level": len(match.group(1)),
                        "title": "",
                        "line": index + 1,
                        "reason": "empty-heading",
                    }
                )

    section_rows: dict[tuple[str, str], dict] = {}
    section_order: list[tuple[str, str]] = []
    decision_item_indices = decision_list_indices | decision_table_indices
    for root in decision_roots:
        root_key = _canonical_decision_section_heading(root["title"])
        valid_sections = valid_sections_by_root[root["_index"]]
        for index in sorted(
            item_index
            for item_index in decision_item_indices
            if root["_index"] < item_index < root["_end"]
        ):
            containing_sections = [
                section
                for section in valid_sections
                if section["_index"] < index < section["_end"]
            ]
            if containing_sections:
                owner = max(
                    containing_sections,
                    key=lambda section: (section["level"], section["_index"]),
                )
                section_key = _canonical_decision_section_heading(owner["title"])
            else:
                owner = root
                section_key = f"root:{root_key}"
            key = (root_key, section_key)
            row = section_rows.get(key)
            if row is None:
                row = {
                    "heading": owner["title"],
                    "canonical_heading": section_key,
                    "level": owner["level"],
                    "line": owner["line"],
                    "heading_lines": [owner["line"]],
                    "list_item_count": 0,
                    "table_item_count": 0,
                    "decision_item_count": 0,
                }
                section_rows[key] = row
                section_order.append(key)
            elif owner["line"] not in row["heading_lines"]:
                row["heading_lines"].append(owner["line"])
            if index in decision_list_indices:
                row["list_item_count"] += 1
            if index in decision_table_indices:
                row["table_item_count"] += 1
            row["decision_item_count"] += 1

    decision_sections = [section_rows[key] for key in section_order]
    max_decision_section_item_count = max(
        (row["decision_item_count"] for row in decision_sections),
        default=0,
    )

    has_reference_type, reference_type_value = _explicit_preface(lines, "Reference type")
    has_load_when, _load_when_value = _explicit_preface(lines, "Load when")
    has_do_not_load_when, _do_not_load_value = _explicit_preface(lines, "Do not load when")
    declared_kind = _normalized_reference_type(reference_type_value)
    if has_reference_type:
        advisory_kind = declared_kind
        advisory_kind_source = "explicit" if declared_kind else "unrecognized-explicit"
    else:
        advisory_kind = inferred_kind
        advisory_kind_source = "inferred"

    return {
        "advisory_kind": advisory_kind,
        "advisory_kind_source": advisory_kind_source,
        "reference_type": reference_type_value,
        "has_reference_type_preface": has_reference_type,
        "has_load_when_preface": has_load_when,
        "has_do_not_load_when_preface": has_do_not_load_when,
        "h1_count": h1_count,
        "h1_status": h1_status,
        "h2_plus_headings": [
            {key: item[key] for key in ("level", "title", "line")}
            for item in headings if item["level"] >= 2
        ],
        "empty_headings": empty_headings,
        "decision_headings": decision_headings,
        "decision_list_item_count": len(decision_list_indices),
        "decision_table_item_count": len(decision_table_indices),
        "decision_item_count": len(decision_list_indices | decision_table_indices),
        "decision_sections": decision_sections,
        "max_decision_section_item_count": max_decision_section_item_count,
        "invalid_decision_section_headings": invalid_decision_section_headings,
    }


def _reference_sort_key(item: dict | ReferenceMetrics) -> tuple[int, str, str]:
    if isinstance(item, ReferenceMetrics):
        layer, owner, path = item.layer, item.owner, item.path
    else:
        layer, owner, path = str(item["layer"]), str(item["owner"]), str(item["path"])
    return (REFERENCE_LAYER_ORDER.get(layer, len(REFERENCE_LAYER_ORDER)), owner, path)


def _reference_budget_kind(item: ReferenceMetrics) -> str | None:
    """Map semantic Reference purpose to its independent size-budget class."""
    effective_type = item.effective_preface.get("reference_type", {})
    if (
        effective_type.get("status") == "resolved"
        and effective_type.get("value") in REFERENCE_LINE_BUDGET_KIND
    ):
        return REFERENCE_LINE_BUDGET_KIND[str(effective_type["value"])]
    return REFERENCE_LINE_BUDGET_KIND.get(str(item.advisory_kind), item.advisory_kind)


def _targeted_reference_line_limit(item: ReferenceMetrics) -> int:
    """Keep the router's closed route table within its reviewed local exception."""
    if item.path == (
        "src/control-skills/engineering-control-plane/references/"
        "professional-skill-router.md"
    ):
        return 62
    return 60


def _physical_references() -> tuple[list[dict], dict[str, str], list[dict]]:
    references: list[dict] = []
    markdown_by_path: dict[str, str] = {}
    errors: list[dict] = []
    for layer, _registry, _key, skills_root in REFERENCE_SOURCES:
        skills_root_safe, skills_root_errors = _safe_source_path(
            skills_root,
            allowed_root=ROOT,
            source="registry",
            expect_directory=True,
            target=_repository_relative_path(skills_root),
        )
        errors.extend(skills_root_errors)
        if not skills_root_safe:
            continue
        for owner_dir in sorted(skills_root.iterdir()):
            owner_safe, owner_errors = _safe_source_path(
                owner_dir,
                allowed_root=skills_root,
                source="registry",
                expect_directory=True,
            )
            if not owner_safe and owner_errors and all(
                item.get("code") == "source-not-directory"
                for item in owner_errors
            ):
                continue
            errors.extend(owner_errors)
            if not owner_safe:
                continue
            reference_root = owner_dir / "references"
            reference_safe, reference_errors = _safe_source_path(
                reference_root,
                allowed_root=owner_dir,
                source="local",
                expect_directory=True,
            )
            errors.extend(reference_errors)
            if not reference_safe:
                continue
            for path in sorted(reference_root.rglob("*.md")):
                relative = _repository_relative_path(path)
                text, source_errors = _safe_markdown_text(
                    path,
                    allowed_root=reference_root,
                    source="local",
                    target=relative,
                )
                errors.extend(source_errors)
                if text is None:
                    continue
                markdown_by_path[relative] = text
                references.append(
                    {
                        "layer": layer,
                        "owner": owner_dir.name,
                        "path": relative,
                        "kind": _reference_kind(relative),
                        "line_count": len(text.splitlines()),
                        "token_count": count_o200k_base_tokens(text),
                    }
                )
    return (
        sorted(references, key=_reference_sort_key),
        markdown_by_path,
        sorted(
            errors,
            key=lambda item: (
                str(item.get("path", "")),
                int(item.get("line", 0)),
                str(item.get("code", "")),
                str(item.get("target", "")),
            ),
        ),
    )


def _ai_readability_documents() -> list[dict]:
    """Return every source document governed by the shared readability gate."""

    documents: list[dict] = []
    for item in _root_skill_documents():
        part = str(item["document_part"])
        layer = str(item["layer"])
        surface = (
            "control-prompt"
            if part == "control-prompt"
            else f"{layer}-{part}"
        )
        path = str(item["path"])
        if part == "body":
            source_selector = {"kind": "yaml-body", "path": path}
        elif part == "description":
            source_selector = {
                "kind": "yaml-description",
                "path": path,
                "field": "description",
            }
        else:
            source_selector = {"kind": "whole-file", "path": path}
        documents.append(
            {
                "document_id": f"{path}#{part}",
                "path": path,
                "document_part": part,
                "surface": surface,
                "owner": str(item["owner"]),
                "text": str(item["text"]),
                "line_offset": (
                    0
                    if part == "description"
                    else int(item.get("line_offset", 0) or 0)
                ),
                "source_selector": source_selector,
                "check_bullets": part != "description",
            }
        )

    _require_safe_source_path(
        AGENT_PROFILES_FILE,
        allowed_root=AGENT_PROFILES_FILE.parent,
        source="local",
        expect_directory=False,
    )
    try:
        profile_data = json.loads(AGENT_PROFILES_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationProblem(
            f"{_repository_relative_path(AGENT_PROFILES_FILE)}: invalid JSON: {exc}"
        ) from exc
    profiles = profile_data.get("profiles") if isinstance(profile_data, dict) else None
    if not isinstance(profiles, list):
        raise ValidationProblem(
            f"{_repository_relative_path(AGENT_PROFILES_FILE)}: profiles must be a list"
        )
    profile_path = _repository_relative_path(AGENT_PROFILES_FILE)
    for index, profile in enumerate(profiles):
        if not isinstance(profile, dict):
            raise ValidationProblem(f"{profile_path}: profiles[{index}] must be a mapping")
        name = profile.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValidationProblem(f"{profile_path}: profiles[{index}].name must be non-blank")
        for part, check_bullets in (("description", False), ("instructions", True)):
            text = profile.get(part)
            if not isinstance(text, str) or not text.strip():
                raise ValidationProblem(
                    f"{profile_path}: {name}.{part} must be a non-blank string"
                )
            documents.append(
                {
                    "document_id": f"{profile_path}#{name}#{part}",
                    "path": profile_path,
                    "document_part": part,
                    "surface": f"agent-profile-{part}",
                    "owner": name,
                    "text": text,
                    "line_offset": 0,
                    "source_selector": {
                        "kind": "json-profile-field",
                        "path": profile_path,
                        "profile_name": name,
                        "field": part,
                    },
                    "check_bullets": check_bullets,
                }
            )

    physical, markdown_by_path, _physical_errors = _physical_references()
    for item in physical:
        path = str(item["path"])
        documents.append(
            {
                "document_id": f"{path}#reference",
                "path": path,
                "document_part": "reference",
                "surface": f"{item['layer']}-reference",
                "owner": str(item["owner"]),
                "text": markdown_by_path[path],
                "line_offset": 0,
                "source_selector": {"kind": "whole-file", "path": path},
                "check_bullets": True,
            }
        )

    documents.sort(key=lambda item: str(item["document_id"]))
    document_ids = [str(item["document_id"]) for item in documents]
    if len(document_ids) != len(set(document_ids)):
        raise ValidationProblem("AI-readability document IDs must be unique")
    return documents


def _collect_ai_readability(documents: list[dict] | None = None) -> dict:
    """Collect deterministic readability review bands and blocking findings."""

    source_documents = _ai_readability_documents() if documents is None else documents
    contract = {
        "schema_version": AI_READABILITY_SCHEMA_VERSION,
        "detector_contract": "ai-readability-v1",
        "ordinary_target_words": AI_SENTENCE_TARGET_WORDS,
        "complex_target_words": AI_COMPLEX_SENTENCE_TARGET_WORDS,
        "hard_max_words": AI_SENTENCE_HARD_WORDS,
        "bullet_decision_max": 1,
    }
    document_rows: list[dict] = []
    findings: list[dict] = []
    seen: set[str] = set()
    advisory_rank = {"review-as-complex": 1, "tighten": 2}
    for index, raw in enumerate(source_documents):
        if not isinstance(raw, dict):
            raise ValidationProblem(f"AI-readability document[{index}] must be a mapping")
        required = {
            "document_id",
            "path",
            "document_part",
            "surface",
            "owner",
            "text",
            "line_offset",
            "source_selector",
            "check_bullets",
        }
        if set(raw) != required:
            raise ValidationProblem(
                f"AI-readability document[{index}] must contain exactly {sorted(required)}"
            )
        document_id = raw["document_id"]
        text = raw["text"]
        check_bullets = raw["check_bullets"]
        line_offset = raw["line_offset"]
        source_selector = raw["source_selector"]
        if not isinstance(document_id, str) or not document_id.strip():
            raise ValidationProblem(
                f"AI-readability document[{index}].document_id must be non-blank"
            )
        if document_id in seen:
            raise ValidationProblem(f"duplicate AI-readability document_id: {document_id}")
        seen.add(document_id)
        if not isinstance(text, str):
            raise ValidationProblem(
                f"AI-readability document[{index}].text must be a string"
            )
        if not isinstance(check_bullets, bool):
            raise ValidationProblem(
                f"AI-readability document[{index}].check_bullets must be a boolean"
            )
        if type(line_offset) is not int or line_offset < 0:
            raise ValidationProblem(
                f"AI-readability document[{index}].line_offset must be a non-negative integer"
            )
        if not isinstance(source_selector, dict):
            raise ValidationProblem(
                f"AI-readability document[{index}].source_selector must be a mapping"
            )
        context_lines = text.splitlines()
        document_context = {
            "line_offset": line_offset,
            "line_count": len(context_lines),
            "text": text,
            "lines": [
                {"line": line_index, "text": line}
                for line_index, line in enumerate(context_lines, start=1)
            ],
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        }
        raw_findings = ai_readability_findings(
            text,
            document_id,
            check_bullets=check_bullets,
            # Source spans are always logical document-part coordinates.
            # line_offset remains separate inventory metadata only.
            line_offset=0,
        )
        band_counts = {"review-as-complex": 0, "tighten": 0, "hard-fail": 0}
        compound_count = 0
        for finding in raw_findings:
            sentence = str(finding["sentence"])
            source_span = finding.get("source_span")
            if not isinstance(source_span, dict):
                raise ValidationProblem(
                    f"AI-readability finding lacks source_span: {document_id}"
                )
            band = finding.get("band")
            if band in band_counts:
                band_counts[str(band)] += 1
            if finding["kind"] == "bullet-decisions":
                compound_count += 1
            sentence_fingerprint = hashlib.sha256(
                ("ai-readability-sentence-v1\0" + sentence).encode("utf-8")
            ).hexdigest()
            finding_id = hashlib.sha256(
                (
                    "ai-readability-finding-v2\0ai-readability-v1\0"
                    + document_id
                    + "\0"
                    + str(finding["kind"])
                    + "\0"
                    + str(band or "")
                    + "\0"
                    + str(finding.get("words") or "")
                    + "\0"
                    + sentence_fingerprint
                    + "\0"
                    + str(source_span.get("start_line"))
                    + "\0"
                    + str(source_span.get("end_line"))
                    + "\0"
                    + str(source_span.get("start_offset"))
                    + "\0"
                    + str(source_span.get("end_offset"))
                    + "\0"
                    + str(source_span.get("sha256"))
                ).encode("utf-8")
            ).hexdigest()
            findings.append(
                {
                    "finding_id": finding_id,
                    "document_id": document_id,
                    "kind": str(finding["kind"]),
                    "severity": str(finding["severity"]),
                    "line": int(finding["line"]),
                    "band": band,
                    "words": finding.get("words"),
                    "decisions": finding.get("decisions"),
                    "sentence": sentence,
                    "sentence_fingerprint": sentence_fingerprint,
                    "source_span": source_span,
                    "preview": re.sub(r"\s+", " ", sentence).strip()[:180],
                }
            )
        advisory_bands = [
            band for band in advisory_rank if band_counts[band] > 0
        ]
        highest_advisory_band = (
            max(advisory_bands, key=advisory_rank.__getitem__)
            if advisory_bands
            else None
        )
        document_rows.append(
            {
                "document_id": document_id,
                "path": str(raw["path"]),
                "document_part": str(raw["document_part"]),
                "surface": str(raw["surface"]),
                "owner": str(raw["owner"]),
                "source_selector": {
                    **source_selector,
                },
                "line_offset": line_offset,
                "check_bullets": check_bullets,
                "content_fingerprint": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "document_context": document_context,
                "highest_advisory_band": highest_advisory_band,
                "review_as_complex_count": band_counts["review-as-complex"],
                "tighten_count": band_counts["tighten"],
                "hard_fail_count": band_counts["hard-fail"],
                "compound_bullet_count": compound_count,
            }
        )
    document_rows.sort(key=lambda item: item["document_id"])
    findings.sort(
        key=lambda item: (
            item["document_id"],
            item["line"],
            item["kind"],
            str(item["band"] or ""),
            item["finding_id"],
            item["sentence_fingerprint"],
        )
    )
    finding_ids = [str(item["finding_id"]) for item in findings]
    if len(finding_ids) != len(set(finding_ids)):
        raise ValidationProblem("AI-readability finding IDs must be globally unique")

    surface_summary: dict[str, dict[str, int]] = {}
    for surface in sorted({str(item["surface"]) for item in document_rows}):
        rows = [item for item in document_rows if item["surface"] == surface]
        surface_summary[surface] = {
            "documents": len(rows),
            "advisory_documents": sum(
                item["highest_advisory_band"] is not None for item in rows
            ),
            "review_as_complex_sentences": sum(
                int(item["review_as_complex_count"]) for item in rows
            ),
            "tighten_sentences": sum(int(item["tighten_count"]) for item in rows),
            "hard_fail_sentences": sum(int(item["hard_fail_count"]) for item in rows),
            "compound_bullets": sum(
                int(item["compound_bullet_count"]) for item in rows
            ),
        }
    canonical = json.dumps(
        {
            "contract": contract,
            "documents": document_rows,
            "findings": findings,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    summary = {
        "documents": len(document_rows),
        "advisory_documents": sum(
            item["highest_advisory_band"] is not None for item in document_rows
        ),
        "review_as_complex_sentences": sum(
            int(item["review_as_complex_count"]) for item in document_rows
        ),
        "tighten_sentences": sum(
            int(item["tighten_count"]) for item in document_rows
        ),
        "hard_fail_sentences": sum(
            int(item["hard_fail_count"]) for item in document_rows
        ),
        "compound_bullets": sum(
            int(item["compound_bullet_count"]) for item in document_rows
        ),
    }
    summary["advisory_sentences"] = (
        summary["review_as_complex_sentences"] + summary["tighten_sentences"]
    )
    summary["blocker_findings"] = (
        summary["hard_fail_sentences"] + summary["compound_bullets"]
    )
    summary["hard_gate_ready"] = summary["blocker_findings"] == 0
    return {
        "schema_version": AI_READABILITY_SCHEMA_VERSION,
        "contract": contract,
        "source_fingerprint": {
            "algorithm": "sha256",
            "value": hashlib.sha256(canonical).hexdigest(),
            "document_count": len(document_rows),
        },
        "summary": summary,
        "by_surface": surface_summary,
        "documents": document_rows,
        "findings": findings,
        "limitations": [
            "Sentence bands are deterministic lexical evidence, not an expert judgment that every 25-40 word sentence is unclear.",
            "Compiled Layer 3 projections retain an independent exact hard gate; their source sentences are reviewed through the corresponding Root document disposition.",
        ],
    }


def _readability_by_owner(document_rows: list[dict]) -> dict[str, dict[str, int]]:
    """Aggregate the existing readability document evidence by Skill owner."""

    fields = (
        "review_as_complex_count",
        "tighten_count",
        "hard_fail_count",
        "compound_bullet_count",
    )
    result: dict[str, dict[str, int]] = {}
    for row in document_rows:
        owner = str(row["owner"])
        aggregate = result.setdefault(
            owner,
            {
                "documents": 0,
                **{field: 0 for field in fields},
            },
        )
        aggregate["documents"] += 1
        for field in fields:
            aggregate[field] += int(row[field])
    return {owner: result[owner] for owner in sorted(result)}


def _metric_field(metrics: SkillMetrics | dict, name: str):
    return metrics[name] if isinstance(metrics, dict) else getattr(metrics, name)


def _review_state_and_reasons(
    metrics: SkillMetrics | dict,
    owner_readability: dict[str, int] | None,
) -> tuple[str, list[str]]:
    """Derive the closed review axis while preserving every matched reason."""

    readability = owner_readability or {}
    classification = _metric_field(metrics, "classification")
    kind = _metric_field(metrics, "kind")
    physical_lines = int(_metric_field(metrics, "line_count"))
    governed_lines = int(_metric_field(metrics, "governed_line_count"))
    projection_lines = int(_metric_field(metrics, "projection_overhead_lines"))
    matched: set[str] = set()

    if classification == "BLOCK":
        matched.add("classification_block")
    if int(readability.get("hard_fail_count", 0)):
        matched.add("ai_readability_hard_fail")
    if int(readability.get("compound_bullet_count", 0)):
        matched.add("ai_readability_compound_bullet")
    if classification == "TIGHTEN_BODY":
        matched.add("classification_tighten_body")
    if int(readability.get("tighten_count", 0)):
        matched.add("ai_readability_tighten")
    if int(readability.get("review_as_complex_count", 0)):
        matched.add("ai_readability_review_as_complex")
    if classification == "REVIEW_DENSITY":
        matched.add("classification_review_density")
    if kind == "professional-skill" and governed_lines > 80:
        matched.add("professional_governed_lines_over_80")
    if (
        kind == "professional-skill"
        and governed_lines <= 80 < physical_lines
        and projection_lines > 0
    ):
        matched.add("professional_projection_pushes_physical_lines_over_80")
    if bool(_metric_field(metrics, "actionability_applicable")):
        matched.add("weak_front_loaded_action")
    if (
        bool(_metric_field(metrics, "high_confidence_control_scaffold"))
        or float(_metric_field(metrics, "control_boilerplate_density"))
        >= THRESHOLDS["control_boilerplate_density_high"]
        or int(_metric_field(metrics, "generic_control_phrase_count"))
        >= THRESHOLDS["generic_control_phrase_high"]
    ):
        matched.add("control_boilerplate_risk")
    if int(_metric_field(metrics, "actionable_repeated_phrase_count")):
        matched.add("actionable_duplicate_content")
    if _metric_field(metrics, "description_findings"):
        matched.add("description_authoring_advisory")
    if int(_metric_field(metrics, "split_candidate_score")) >= THRESHOLDS[
        "split_candidate_high"
    ]:
        matched.add("split_candidate")

    reasons = [reason for reason in REVIEW_REASON_PRIORITY if reason in matched]
    states = {REVIEW_REASON_STATES[reason] for reason in reasons}
    state = next(
        (candidate for candidate in REVIEW_STATE_PRIORITY if candidate in states),
        "KEEP",
    )
    return state, reasons


def _assign_review_state(
    metrics: SkillMetrics,
    readability_by_owner: dict[str, dict[str, int]],
) -> None:
    metrics.review_state, metrics.review_reasons = _review_state_and_reasons(
        metrics,
        readability_by_owner.get(metrics.name),
    )


def _registry_scalar(value: str) -> str:
    value = value.strip()
    if value.startswith('"'):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return value
        return parsed if isinstance(parsed, str) else value
    return value


def _registry_reference_contract_lines(
    registry_text: str,
    registry_path: str,
) -> tuple[dict[tuple[str, str, str], int], list[dict]]:
    """Map each structured Registry declaration to its physical YAML line."""

    result: dict[tuple[str, str, str], int] = {}
    errors: list[dict] = []
    owner: str | None = None
    reference_path: str | None = None
    in_reference_index = False
    for line_number, line in enumerate(registry_text.splitlines(), start=1):
        owner_match = re.match(r"^  - name:\s*(.+?)\s*$", line)
        if owner_match:
            owner = _registry_scalar(owner_match.group(1))
            reference_path = None
            in_reference_index = False
            continue
        if owner is None:
            continue
        if re.match(r"^    reference_index:\s*", line):
            in_reference_index = True
            reference_path = None
            continue
        if in_reference_index and re.match(r"^    \S", line):
            in_reference_index = False
            reference_path = None
        if not in_reference_index:
            continue
        path_match = re.match(r"^      - path:\s*(.+?)\s*$", line)
        if path_match:
            reference_path = _registry_scalar(path_match.group(1))
            continue
        field_match = re.match(
            r"^        (type|load_when|do_not_load_when|required_by|required_output):\s*(.+?)\s*$",
            line,
        )
        if not field_match or reference_path is None:
            continue
        field = field_match.group(1)
        key = (owner, reference_path, field)
        if key in result:
            errors.append(
                _preface_contract_issue(
                    code="duplicate-registry-field-line",
                    source="registry",
                    path=registry_path,
                    line=line_number,
                    target=reference_path,
                    message=f"duplicate {field} declaration for {owner}",
                )
            )
            continue
        result[key] = line_number
    return result, errors


def _indexed_references() -> tuple[list[dict], list[dict], dict[str, str]]:
    references: list[dict] = []
    errors: list[dict] = []
    registry_texts: dict[str, str] = {}
    registry_root = ROOT / "src" / "registry"
    for layer, registry, registry_key, skills_root in REFERENCE_SOURCES:
        skills_root_safe, skills_root_errors = _safe_source_path(
            skills_root,
            allowed_root=ROOT,
            source="registry",
            expect_directory=True,
            target=_repository_relative_path(skills_root),
        )
        errors.extend(skills_root_errors)
        if not skills_root_safe:
            continue
        registry_text, registry_errors = _safe_markdown_text(
            registry,
            allowed_root=registry_root,
            source="registry",
            target=_repository_relative_path(registry),
        )
        errors.extend(registry_errors)
        if registry_text is None:
            continue
        registry_texts[_repository_relative_path(registry)] = registry_text
        data = load_yaml_file(registry)
        entries = data.get(registry_key, []) if isinstance(data, dict) else []
        registry_relative = _repository_relative_path(registry)
        contract_line_map, contract_line_errors = _registry_reference_contract_lines(
            registry_text, registry_relative
        )
        errors.extend(contract_line_errors)
        for entry in entries or []:
            if not isinstance(entry, dict):
                continue
            owner = entry.get("name")
            owner_path = entry.get("path")
            reference_index = entry.get("reference_index")
            if not isinstance(owner, str) or not isinstance(owner_path, str):
                continue
            try:
                contracts = reference_contracts(
                    reference_index,
                    f"{_repository_relative_path(registry)}:{owner}.reference_index",
                    owner=owner,
                )
            except ValidationProblem as exc:
                errors.append(
                    _preface_contract_issue(
                        code="invalid-registry-reference-contract",
                        source="registry",
                        path=_repository_relative_path(registry),
                        line=1,
                        target=owner,
                        message=str(exc),
                    )
                )
                continue
            raw_owner_path = Path(owner_path)
            if raw_owner_path.is_absolute() or ".." in raw_owner_path.parts:
                errors.append(
                    _preface_contract_issue(
                        code="registry-owner-path-outside-skills-root",
                        source="registry",
                        path=_repository_relative_path(registry),
                        line=1,
                        target=owner_path,
                        message="registry owner path must be relative and remain inside its layer skills root",
                    )
                )
                continue
            owner_root = ROOT / raw_owner_path
            owner_safe, owner_errors = _safe_source_path(
                owner_root,
                allowed_root=skills_root,
                source="registry",
                expect_directory=True,
                target=owner_path,
            )
            errors.extend(owner_errors)
            if owner_errors:
                continue
            reference_root = owner_root / "references"
            for reference in contracts:
                reference_path = reference["path"]
                contract_lines = {
                    field: contract_line_map.get((owner, reference_path, field))
                    for field in (
                        "type",
                        "load_when",
                        "do_not_load_when",
                        "required_by",
                        "required_output",
                    )
                }
                missing_line_fields = [
                    field for field, line in contract_lines.items() if line is None
                ]
                if missing_line_fields:
                    errors.append(
                        _preface_contract_issue(
                            code="missing-registry-field-line",
                            source="registry",
                            path=registry_relative,
                            line=1,
                            target=reference_path,
                            message=(
                                f"{owner} structured Reference is missing physical YAML line(s): "
                                + ", ".join(missing_line_fields)
                            ),
                        )
                    )
                    continue
                raw_reference = Path(reference_path)
                if (
                    raw_reference.is_absolute()
                    or ".." in raw_reference.parts
                    or len(raw_reference.parts) < 2
                    or raw_reference.parts[0] != "references"
                ):
                    errors.append(
                        _preface_contract_issue(
                            code="registry-reference-path-outside-owner",
                            source="registry",
                            path=_repository_relative_path(registry),
                            line=1,
                            target=reference_path,
                            message="registry Reference path must remain inside the owner references directory",
                        )
                    )
                    continue
                target_path = owner_root / raw_reference
                _target_safe, target_errors = _safe_source_path(
                    target_path,
                    allowed_root=reference_root,
                    source="registry",
                    expect_directory=False,
                    target=reference_path,
                )
                errors.extend(target_errors)
                if target_errors:
                    continue
                relative = _repository_relative_path(target_path)
                references.append(
                    {
                        "layer": layer,
                        "owner": owner,
                        "owner_path": owner_path,
                        "path": relative,
                        "kind": _reference_kind(relative),
                        "reference_contract": dict(reference),
                        "registry_path": registry_relative,
                        "registry_lines": contract_lines,
                    }
                )
    return (
        sorted(references, key=_reference_sort_key),
        sorted(
            errors,
            key=lambda item: (
                str(item.get("path", "")),
                int(item.get("line", 0)),
                str(item.get("code", "")),
                str(item.get("target", "")),
            ),
        ),
        registry_texts,
    )


def _reference_source_fingerprint(
    indexed: list[dict],
    physical_markdown: dict[str, str],
    registry_texts: dict[str, str],
) -> tuple[dict, list[dict]]:
    """Hash the exact source set that can change effective Reference metadata."""
    documents: dict[str, dict[str, str]] = {}
    errors: list[dict] = []

    def record(path: Path, text: str | None) -> None:
        relative = _repository_relative_path(path)
        documents[relative] = (
            {
                "state": "present",
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            }
            if text is not None
            else {"state": "missing", "sha256": ""}
        )

    for _layer, registry, _registry_key, _skills_root in REFERENCE_SOURCES:
        record(registry, registry_texts.get(_repository_relative_path(registry)))

    owner_paths = sorted({str(item["owner_path"]) for item in indexed})
    for owner_path in owner_paths:
        owner_root = ROOT / owner_path
        for path, allowed_root, source in (
            (owner_root / "SKILL.md", owner_root, "parent-root"),
            (
                owner_root / "references" / "index.md",
                owner_root / "references",
                "reference-index",
            ),
        ):
            text, source_errors = _safe_markdown_text(
                path,
                allowed_root=allowed_root,
                source=source,
                target=_repository_relative_path(path),
            )
            errors.extend(source_errors)
            record(path, text)

    for item in indexed:
        path = str(item["path"])
        record(ROOT / path, physical_markdown.get(path))

    manifest = [
        {"path": path, **documents[path]}
        for path in sorted(documents)
    ]
    canonical = json.dumps(
        manifest,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return (
        {
            "algorithm": "sha256",
            "value": hashlib.sha256(canonical).hexdigest(),
            "document_count": len(manifest),
        },
        errors,
    )


def _reference_surfaces_for_record(value: object) -> set[str]:
    if not isinstance(value, dict):
        return set()
    layer = value.get("layer")
    if layer in REFERENCE_CONTENT_SURFACES:
        return {str(layer)}
    surfaces = {
        surface
        for surface in (
            _reference_surface_for_path(value.get("target")),
            _reference_surface_for_path(value.get("path")),
        )
        if surface is not None
    }
    return surfaces


def _reference_surface_validation(reference_content: dict) -> dict:
    references = [
        item
        for item in reference_content.get("references") or []
        if isinstance(item, dict)
    ]
    advisories = reference_content.get("advisories")
    advisories = advisories if isinstance(advisories, dict) else {}
    semantic = reference_content.get("semantic_advisories")
    semantic = semantic if isinstance(semantic, dict) else {}
    candidates = [
        item for item in semantic.get("candidates") or [] if isinstance(item, dict)
    ]
    contract = semantic.get("disposition_contract")
    contract = contract if isinstance(contract, dict) else {}
    entries = contract.get("entries")
    entries = entries if isinstance(entries, list) else []
    reported_errors = contract.get("errors")
    reported_errors = (
        [str(item) for item in reported_errors]
        if isinstance(reported_errors, list)
        else ["reference semantic disposition errors must be a list"]
    )
    common_errors, surface_errors = _reference_disposition_error_attribution(
        reported_errors,
        entries,
        candidates,
    )
    candidate_by_id = {
        str(item.get("candidate_id")): item
        for item in candidates
        if isinstance(item.get("candidate_id"), str)
    }

    def add_record_error(record: object, message: str) -> None:
        surfaces = _reference_surfaces_for_record(record)
        if not surfaces:
            common_errors.append(message)
            return
        for surface in sorted(surfaces):
            surface_errors[surface].append(message)

    for collection_name in ("references", "missing", "orphans", "template_assets"):
        for index, item in enumerate(reference_content.get(collection_name) or []):
            if not _reference_surfaces_for_record(item):
                common_errors.append(
                    f"reference_content.{collection_name}[{index}] cannot be attributed to a declared Reference surface"
                )
    for index, candidate in enumerate(candidates):
        if not _reference_surfaces_for_candidate(candidate):
            common_errors.append(
                f"semantic candidate[{index}] cannot be attributed to a declared Reference surface"
            )

    for item in reference_content.get("missing") or []:
        if isinstance(item, dict):
            add_record_error(item, f"missing indexed reference: {item.get('path')}")
    for item in reference_content.get("orphans") or []:
        if isinstance(item, dict):
            add_record_error(item, f"non-template orphan reference: {item.get('path')}")
    for item in references:
        if not item.get("exists"):
            continue
        if item.get("h1_status") == "missing":
            add_record_error(item, f"indexed reference missing H1: {item.get('path')}")
        effective = item.get("effective_preface")
        if not isinstance(effective, dict):
            add_record_error(
                item, f"invalid effective preface mapping: {item.get('path')}"
            )
            continue
        for field in PREFACE_FIELDS:
            value = effective.get(field)
            status = value.get("status") if isinstance(value, dict) else None
            if status == "missing":
                add_record_error(
                    item,
                    f"indexed reference missing effective {field}: {item.get('path')}",
                )
            elif status == "invalid" or status not in {"resolved", "missing", "conflict"}:
                add_record_error(
                    item,
                    f"indexed reference has invalid effective {field}: {item.get('path')}",
                )
    preface_contract = reference_content.get("preface_contract")
    preface_contract = preface_contract if isinstance(preface_contract, dict) else {}
    for item in preface_contract.get("errors") or []:
        if isinstance(item, dict):
            add_record_error(
                item,
                f"effective preface contract error {item.get('code')}: {item.get('path')}",
            )
        else:
            common_errors.append("effective preface contract error is not a mapping")
    for item in preface_contract.get("conflicts") or []:
        if isinstance(item, dict):
            add_record_error(
                item,
                f"effective preface conflict {item.get('code')}: {item.get('path')}",
            )
        else:
            common_errors.append("effective preface conflict is not a mapping")
    for key, label in (
        ("non_template_multiple_h1", "non-template reference with multiple H1"),
        ("non_template_empty_headings", "non-template reference with empty heading"),
        ("targeted_over_60_lines", "targeted reference over 60 lines"),
        ("mode_contract_over_80_lines", "mode-contract reference over 80 lines"),
        ("decision_items_over_15", "reference over 15 decision items"),
    ):
        for item in advisories.get(key) or []:
            if isinstance(item, dict):
                add_record_error(item, f"{label}: {item.get('path')}")
            else:
                common_errors.append(f"{key} advisory is not a mapping")

    surface_results: dict[str, dict] = {}
    for surface in REFERENCE_CONTENT_SURFACES:
        surface_references = [
            item for item in references if surface in _reference_surfaces_for_record(item)
        ]
        surface_candidates = [
            item
            for item in candidates
            if surface in _reference_surfaces_for_candidate(item)
        ]
        fixed = sum(
            bool(item.get("unresolved"))
            and item.get("finding") == "fixed_number_candidate"
            for item in surface_candidates
        )
        templated = sum(
            bool(item.get("unresolved"))
            and item.get("finding") == "templated_block_candidate"
            for item in surface_candidates
        )
        absolute_p0_p1 = sum(
            bool(item.get("unresolved"))
            and item.get("finding") == "unconditional_absolute_candidate"
            and item.get("priority") in {"P0", "P1"}
            for item in surface_candidates
        )
        if fixed:
            surface_errors[surface].append(
                f"unresolved fixed-number semantic candidate(s): {fixed}"
            )
        if templated:
            surface_errors[surface].append(
                f"unresolved templated-block semantic group(s): {templated}"
            )
        if absolute_p0_p1:
            surface_errors[surface].append(
                f"unresolved P0/P1 unconditional-absolute semantic candidate(s): {absolute_p0_p1}"
            )
        configured = sum(
            surface
            in _reference_surfaces_for_entry(entry, candidate_by_id)
            for entry in entries
        )
        applied = sum(
            surface in _reference_surfaces_for_candidate(candidate)
            and candidate.get("disposition_record") is not None
            for candidate in candidates
        )
        errors = _ordered_unique_strings(surface_errors[surface])
        surface_results[surface] = {
            "status": "pass" if not common_errors and not errors else "fail",
            "indexed_reference_count": len(surface_references),
            "existing_reference_count": sum(
                bool(item.get("exists")) for item in surface_references
            ),
            "semantic_candidate_count": len(surface_candidates),
            "semantic_unresolved_count": sum(
                bool(item.get("unresolved")) for item in surface_candidates
            ),
            "semantic_fixed_number_unresolved_count": fixed,
            "semantic_templated_group_unresolved_count": templated,
            "semantic_absolute_p0_p1_unresolved_count": absolute_p0_p1,
            "disposition_configured_count": configured,
            "disposition_applied_count": applied,
            "errors": errors,
        }
    return {
        "schema_version": SURFACE_VALIDATION_SCHEMA_VERSION,
        "common_errors": _ordered_unique_strings(common_errors),
        "surfaces": surface_results,
    }


def _collect_reference_content(
    *, evaluation_date: date | None = None
) -> dict:
    effective_evaluation_date = (
        _effective_evaluation_date()
        if evaluation_date is None
        else evaluation_date
    )
    physical, physical_markdown, physical_errors = _physical_references()
    indexed, indexed_errors, registry_texts = _indexed_references()
    physical_by_path = {item["path"]: item for item in physical}
    indexed_paths = {item["path"] for item in indexed}

    owner_preface_sources: dict[tuple[str, str, str], dict[str, dict[str, list[dict]]]] = {}
    preface_contract_errors: list[dict] = [*physical_errors, *indexed_errors]
    registry_claims: dict[str, list[dict]] = defaultdict(list)
    for item in indexed:
        registry_claims[str(item["path"])].append(item)
    for target, claims in sorted(registry_claims.items()):
        if len(claims) < 2:
            continue
        distinct_owners = {(item["layer"], item["owner"]) for item in claims}
        preface_contract_errors.append(
            _preface_contract_issue(
                code=(
                    "cross-owner-registry-target"
                    if len(distinct_owners) > 1
                    else "duplicate-registry-target"
                ),
                source="registry",
                path=target,
                line=1,
                target=target,
                message="canonical reference target is claimed more than once",
            )
        )
    owner_keys = sorted(
        {
            (str(item["layer"]), str(item["owner"]), str(item["owner_path"]))
            for item in indexed
        }
    )
    for layer, owner, owner_path in owner_keys:
        owner_root = ROOT / owner_path
        owner_indexed_paths = {
            str(item["path"])
            for item in indexed
            if item["layer"] == layer and item["owner"] == owner
        }
        root_evidence, root_errors = _owner_root_preface_evidence(
            owner_root, owner_indexed_paths
        )
        merged: dict[str, dict[str, list[dict]]] = defaultdict(
            lambda: {field: [] for field in PREFACE_FIELDS}
        )
        for source in (root_evidence,):
            for target, fields in source.items():
                for field in PREFACE_FIELDS:
                    merged[target][field].extend(fields.get(field, []))
        owner_preface_sources[(layer, owner, owner_path)] = dict(merged)
        preface_contract_errors.extend(root_errors)

    source_fingerprint, fingerprint_errors = _reference_source_fingerprint(
        indexed,
        physical_markdown,
        registry_texts,
    )
    preface_contract_errors.extend(fingerprint_errors)

    references: list[ReferenceMetrics] = []
    for item in indexed:
        physical_item = physical_by_path.get(item["path"])
        markdown = physical_markdown.get(item["path"], "")
        structural_facts = (
            _markdown_structural_facts(
                markdown,
                item["kind"],
            )
            if physical_item
            else {
                "advisory_kind": item["kind"],
                "advisory_kind_source": "inferred",
            }
        )
        evidence_by_field = _local_preface_evidence(markdown, item["path"])
        contract = item.get("reference_contract") or {}
        registry_path = str(item.get("registry_path") or "")
        for field in PREFACE_FIELDS:
            registry_field = "type" if field == "reference_type" else field
            value = contract.get(registry_field)
            if field in {"required_by", "required_output"}:
                value = _normalized_consumption_value(field, value)
            if isinstance(value, str) and value:
                evidence_by_field[field].append(
                    _preface_evidence(
                        source="reference-index",
                        path=registry_path,
                        line=int(item["registry_lines"][registry_field]),
                        value=value,
                    )
                )
        inherited = owner_preface_sources.get(
            (item["layer"], item["owner"], item["owner_path"]), {}
        ).get(item["path"], {})
        for field in PREFACE_FIELDS:
            evidence_by_field[field].extend(inherited.get(field, []))
        effective_preface = _effective_preface(evidence_by_field)
        references.append(
            ReferenceMetrics(
                layer=item["layer"],
                owner=item["owner"],
                path=item["path"],
                kind=item["kind"],
                exists=physical_item is not None,
                line_count=physical_item["line_count"] if physical_item else None,
                token_count=physical_item["token_count"] if physical_item else None,
                effective_preface=effective_preface,
                **structural_facts,
            )
        )

    preface_conflicts = sorted(
        [
            {
                "layer": item.layer,
                "owner": item.owner,
                "path": item.path,
                **conflict,
            }
            for item in references
            for conflict in item.effective_preface.get("conflicts", [])
        ],
        key=lambda item: (
            _reference_sort_key(item),
            str(item.get("field", "")),
            str(item.get("code", "")),
            json.dumps(item.get("evidence", []), sort_keys=True),
        ),
    )
    preface_contract_errors = sorted(
        {
            json.dumps(item, ensure_ascii=False, sort_keys=True): item
            for item in preface_contract_errors
        }.values(),
        key=lambda item: (
            str(item.get("path", "")),
            int(item.get("line", 0)),
            str(item.get("code", "")),
            str(item.get("target", "")),
        ),
    )

    missing = [asdict(item) for item in references if not item.exists]
    template_assets = [
        {**item, "indexed": item["path"] in indexed_paths}
        for item in physical
        if item["kind"] == "template"
    ]
    orphans = [
        item
        for item in physical
        if item["path"] not in indexed_paths and item["kind"] != "template"
    ]

    def finding_base(item: ReferenceMetrics) -> dict:
        return {
            "layer": item.layer,
            "owner": item.owner,
            "path": item.path,
            "advisory_kind": item.advisory_kind,
            "advisory_kind_source": item.advisory_kind_source,
            "budget_kind": _reference_budget_kind(item),
        }

    advisories = {
        "non_template_multiple_h1": [
            {**finding_base(item), "h1_count": item.h1_count}
            for item in references
            if item.exists
            and item.advisory_kind != "template"
            and item.h1_status == "multiple"
        ],
        "targeted_over_60_lines": [
            {
                **finding_base(item),
                "line_count": item.line_count,
                "limit": _targeted_reference_line_limit(item),
            }
            for item in references
            if item.exists
            and _reference_budget_kind(item) == "targeted"
            and (item.line_count or 0) > _targeted_reference_line_limit(item)
        ],
        "mode_contract_over_80_lines": [
            {**finding_base(item), "line_count": item.line_count, "limit": 80}
            for item in references
            if item.exists and _reference_budget_kind(item) == "mode-contract" and (item.line_count or 0) > 80
        ],
        "non_template_empty_headings": [
            {**finding_base(item), "empty_headings": item.empty_headings}
            for item in references
            if item.exists and item.advisory_kind != "template" and item.empty_headings
        ],
        "non_template_invalid_decision_section_headings": [
            {
                **finding_base(item),
                "invalid_headings": item.invalid_decision_section_headings,
            }
            for item in references
            if item.exists
            and item.advisory_kind != "template"
            and item.invalid_decision_section_headings
        ],
        "decision_items_over_15": [
            {
                **finding_base(item),
                "decision_item_count": item.decision_item_count,
                "max_decision_section_item_count": item.max_decision_section_item_count,
                "list_items": item.decision_list_item_count,
                "table_items": item.decision_table_item_count,
                "decision_headings": item.decision_headings,
                "decision_sections": item.decision_sections,
                "overflow_sections": [
                    section
                    for section in item.decision_sections
                    if section["decision_item_count"] > 15
                ],
                "limit": 15,
            }
            for item in references
            if item.exists and item.max_decision_section_item_count > 15
        ],
    }
    advisory_paths = {
        item["path"]
        for findings in advisories.values()
        for item in findings
    }
    semantic_advisories = _collect_reference_semantic_advisories(
        [
            {
                "layer": item.layer,
                "owner": item.owner,
                "path": item.path,
                "kind": item.advisory_kind or item.kind,
                "text": physical_markdown[item.path],
            }
            for item in references
            if item.exists and item.path in physical_markdown
        ],
        evaluation_date=effective_evaluation_date,
    )
    semantic_summary = semantic_advisories["summary"]

    by_layer: dict[str, dict] = {}
    for layer, _registry, _key, _root in REFERENCE_SOURCES:
        layer_indexed = [item for item in references if item.layer == layer]
        layer_physical = [item for item in physical if item["layer"] == layer]
        by_layer[layer] = {
            "indexed": len(layer_indexed),
            "existing_indexed": sum(item.exists for item in layer_indexed),
            "missing": sum(not item.exists for item in layer_indexed),
            "physical": len(layer_physical),
            "orphan": sum(item["layer"] == layer for item in orphans),
            "template_assets": sum(item["layer"] == layer for item in template_assets),
            "indexed_lines": sum(item.line_count or 0 for item in layer_indexed),
            "indexed_tokens": sum(item.token_count or 0 for item in layer_indexed),
            "structural_advisory_references": sum(
                item.path in advisory_paths for item in layer_indexed
            ),
        }

    by_kind: dict[str, dict] = {}
    for kind in sorted(REFERENCE_CONTRACT_TYPES):
        items = [
            item
            for item in references
            if item.effective_preface.get("reference_type", {}).get("value") == kind
        ]
        by_kind[kind] = {
            "indexed": len(items),
            "existing_indexed": sum(item.exists for item in items),
            "indexed_lines": sum(item.line_count or 0 for item in items),
            "indexed_tokens": sum(item.token_count or 0 for item in items),
            "structural_advisory_references": sum(
                item.path in advisory_paths for item in items
            ),
        }

    result = {
        "summary": {
            "indexed_reference_entries": len(references),
            "indexed_unique_paths": len(indexed_paths),
            "existing_indexed_references": sum(item.exists for item in references),
            "physical_markdown_references": len(physical),
            "missing_references": len(missing),
            "orphan_references": len(orphans),
            "template_assets": len(template_assets),
            "unindexed_template_assets": sum(not item["indexed"] for item in template_assets),
            "indexed_lines": sum(item.line_count or 0 for item in references),
            "indexed_tokens": sum(item.token_count or 0 for item in references),
            "exactly_one_h1": sum(item.h1_status == "exactly-one" for item in references if item.exists),
            "missing_h1": sum(item.h1_status == "missing" for item in references if item.exists),
            "multiple_h1": sum(item.h1_status == "multiple" for item in references if item.exists),
            "non_template_multiple_h1_references": len(
                advisories["non_template_multiple_h1"]
            ),
            "reference_type_prefaces": sum(item.has_reference_type_preface for item in references),
            "load_when_prefaces": sum(item.has_load_when_preface for item in references),
            "do_not_load_when_prefaces": sum(item.has_do_not_load_when_preface for item in references),
            "effective_reference_types": sum(
                item.effective_preface.get("reference_type", {}).get("status") == "resolved"
                for item in references
            ),
            "missing_effective_reference_types": sum(
                item.effective_preface.get("reference_type", {}).get("status") == "missing"
                for item in references if item.exists
            ),
            "effective_load_when": sum(
                item.effective_preface.get("load_when", {}).get("status") == "resolved"
                for item in references
            ),
            "missing_effective_load_when": sum(
                item.effective_preface.get("load_when", {}).get("status") == "missing"
                for item in references if item.exists
            ),
            "effective_do_not_load_when": sum(
                item.effective_preface.get("do_not_load_when", {}).get("status") == "resolved"
                for item in references
            ),
            "missing_effective_do_not_load_when": sum(
                item.effective_preface.get("do_not_load_when", {}).get("status") == "missing"
                for item in references if item.exists
            ),
            "effective_required_by": sum(
                item.effective_preface.get("required_by", {}).get("status") == "resolved"
                for item in references
            ),
            "missing_effective_required_by": sum(
                item.effective_preface.get("required_by", {}).get("status") == "missing"
                for item in references if item.exists
            ),
            "effective_required_output": sum(
                item.effective_preface.get("required_output", {}).get("status") == "resolved"
                for item in references
            ),
            "missing_effective_required_output": sum(
                item.effective_preface.get("required_output", {}).get("status") == "missing"
                for item in references if item.exists
            ),
            "effective_preface_conflicts": len(preface_conflicts),
            "effective_preface_contract_errors": len(preface_contract_errors),
            "effective_preface_invalid": sum(
                field.get("status") == "invalid"
                for item in references if item.exists
                for field in (
                    item.effective_preface.get("reference_type", {}),
                    item.effective_preface.get("load_when", {}),
                    item.effective_preface.get("do_not_load_when", {}),
                    item.effective_preface.get("required_by", {}),
                    item.effective_preface.get("required_output", {}),
                )
            ),
            "references_with_empty_headings": sum(bool(item.empty_headings) for item in references),
            "targeted_over_60_lines": len(advisories["targeted_over_60_lines"]),
            "mode_contract_over_80_lines": len(advisories["mode_contract_over_80_lines"]),
            "non_template_empty_heading_references": len(advisories["non_template_empty_headings"]),
            "non_template_invalid_decision_section_heading_references": len(
                advisories["non_template_invalid_decision_section_headings"]
            ),
            "decision_items_over_15": len(advisories["decision_items_over_15"]),
            "structural_advisory_references": len(advisory_paths),
            "semantic_raw_candidates": semantic_summary["raw_candidates"],
            "semantic_detector_downgraded_candidates": semantic_summary[
                "detector_downgraded_candidates"
            ],
            "semantic_untriaged_candidates": semantic_summary[
                "untriaged_candidates"
            ],
            "semantic_rewrite_candidates": semantic_summary["rewrite_candidates"],
            "semantic_resolved_candidates": semantic_summary[
                "resolved_candidates"
            ],
            "semantic_unresolved_candidates": semantic_summary[
                "unresolved_candidates"
            ],
            "semantic_fixed_number_unresolved": semantic_summary[
                "strict_unresolved"
            ]["fixed_number_candidates"],
            "semantic_templated_group_unresolved": semantic_summary[
                "strict_unresolved"
            ]["templated_block_groups"],
            "semantic_absolute_p0_p1_unresolved": semantic_summary[
                "strict_unresolved"
            ]["unconditional_absolute_p0_p1_candidates"],
            "semantic_p2_rewrite_advisories": semantic_summary[
                "strict_unresolved"
            ]["p2_rewrite_advisories"],
            "semantic_disposition_configured": semantic_advisories[
                "disposition_contract"
            ]["configured_count"],
            "semantic_disposition_applied": semantic_advisories[
                "disposition_contract"
            ]["applied_count"],
            "semantic_disposition_errors": len(
                semantic_advisories["disposition_contract"]["errors"]
            ),
        },
        "schema_version": REFERENCE_CONTENT_SCHEMA_VERSION,
        "preface_contract": {
            "schema_version": 3,
            "source_precedence": list(PREFACE_SOURCE_PRECEDENCE),
            "fields": list(PREFACE_FIELDS),
            "source_fingerprint": source_fingerprint,
            "errors": preface_contract_errors,
            "conflicts": preface_conflicts,
        },
        "distribution": {"by_layer": by_layer, "by_kind": by_kind},
        "references": [asdict(item) for item in references],
        "advisories": advisories,
        "semantic_advisories": semantic_advisories,
        "missing": missing,
        "orphans": orphans,
        "template_assets": template_assets,
        "limitations": [
            "Heading, preface, and decision-item facts are lexical, fence-aware structural evidence; they do not judge semantic quality.",
            *semantic_advisories["limitations"],
        ],
    }
    result["surface_validation"] = _reference_surface_validation(result)
    return result


def _semantic_application_audit_view(
    root_content: dict,
    reference_content: dict,
) -> dict:
    """Build the canonical in-memory evidence view used by the semantic panel."""

    return {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "thresholds": THRESHOLDS,
        "root_content": root_content,
        "reference_content": reference_content,
    }


def _collect_semantic_content_with_application(
    foundation_contracts: dict[str, dict] | None = None,
    *,
    evaluation_date: date | None = None,
) -> tuple[dict, dict, dict]:
    """Collect both semantic axes and validate one immutable majority binding."""

    from expert_panel_review import (
        PanelReviewError,
        SEMANTIC_DISPOSITION_APPLICATION_KIND,
        SEMANTIC_DISPOSITION_APPLICATION_SCHEMA_VERSION,
        validate_semantic_decision_application,
    )

    effective_evaluation_date = (
        _effective_evaluation_date()
        if evaluation_date is None
        else evaluation_date
    )
    root_content = _collect_root_content(
        foundation_contracts,
        evaluation_date=effective_evaluation_date,
    )
    reference_content = _collect_reference_content(
        evaluation_date=effective_evaluation_date,
    )
    try:
        application_report = validate_semantic_decision_application(
            _semantic_application_audit_view(root_content, reference_content),
        )
        application_report["error"] = None
    except (OSError, ValidationProblem, PanelReviewError) as exc:
        application_report = {
            "schema_version": SEMANTIC_DISPOSITION_APPLICATION_SCHEMA_VERSION,
            "kind": SEMANTIC_DISPOSITION_APPLICATION_KIND,
            "review_id": None,
            "decision_kind": (
                "changeforge.semantic-disposition-attestation"
            ),
            "decision": {
                "path": "evals/expert-panel/semantic-disposition.json",
                "sha256": None,
            },
            "status": "invalid",
            "target_count": 0,
            "applied_count": 0,
            "completed_rewrite_count": 0,
            "error": {
                "id": SEMANTIC_DISPOSITION_APPLICATION_ERROR_ID,
                "message": str(exc),
            },
        }
    return root_content, reference_content, application_report


def _description_findings(kind: str, description: str | None) -> list[str]:
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
    budget = DESCRIPTION_BUDGETS[kind]
    if len(text) > budget["hard"]:
        findings.append(
            f"description: hard budget exceeded ({len(text)} > {budget['hard']} chars)"
        )
    elif len(text) > budget["recommended"]:
        findings.append(
            "description: recommended budget exceeded "
            f"({len(text)} > {budget['recommended']} chars); keep only trigger, "
            "anti-trigger, and consumer-role guidance"
        )
    # "First Executable Slice" is the repository's canonical boundary term,
    # not sequencing prose. Remove it before scanning even when punctuation
    # follows the phrase (for example, ``Slice,`` or ``Slice.``).
    workflow_scan = re.sub(r"\bfirst executable slice\b", "", lowered)
    if any(marker in workflow_scan for marker in DESCRIPTION_WORKFLOW_MARKERS):
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


def _targeted_reference_lines(body: str) -> set[str]:
    """Return normalized lines in the selectively loaded reference policy."""
    sections = parse_sections(body)
    targeted = next(
        (
            section
            for section in sections
            if section.title.casefold() in {"targeted references", "reference loading policy"}
        ),
        None,
    )
    if targeted is None:
        return set()
    return {
        normalized
        for line in targeted.text.splitlines()
        if (normalized := _normalize_significant_line(line))
    }


def _actionable_significant_lines(body: str) -> set[str]:
    excluded = _targeted_reference_lines(body)
    return {
        line
        for line in _significant_lines(body)
        if line not in excluded
    }


def _markdown_list_items(markdown: str) -> list[str]:
    """Return every logical Markdown item; nesting never exempts a rule.

    Root content schema v4 already promises logical nested-item accounting.
    Blank lines end an item, and only explicitly content-indented continuation
    lines may extend it; unrelated prose cannot lend decision words to a rule.
    """

    unfenced = "\n".join(
        "" if in_fence else line
        for _index, line, in_fence in _strip_fenced(markdown.splitlines())
    )
    return parse_markdown_logical_list_items(unfenced)["items"]


def _sentence_count(value: str) -> int:
    slices = _semantic_sentence_slices(re.sub(r"\s+", " ", value).strip())
    return max(1, len(slices)) if value.strip() else 0


def _foundation_content_facts(body: str, sections: list[Section]) -> dict[str, int | float]:
    rules = _find_section(sections, "High-Value Rules")
    rule_items = _markdown_list_items(rules.text) if rules else []
    rule_sentence_counts = [_sentence_count(item) for item in rule_items]
    decision_card = foundation_decision_card(body)
    decision_metrics = decision_card["metrics"]
    decision_rule_count = int(
        decision_metrics["high_value_rule_decision_count"]
    )

    targeted_lines = _targeted_reference_lines(body)
    prose_lines: list[str] = []
    for _index, line, in_fence in _strip_fenced(body.splitlines()):
        stripped = line.strip()
        if (
            in_fence
            or not stripped
            or HEADING_RE.match(line)
            or TABLE_SEPARATOR_RE.match(stripped)
            or _normalize_significant_line(line) in targeted_lines
        ):
            continue
        prose_lines.append(LIST_MARKER_RE.sub("", stripped))

    explanatory = sum(bool(ROOT_EXPLANATORY_MARKER_RE.search(line)) for line in prose_lines)
    denominator = max(1, len(prose_lines))
    return {
        "high_value_rule_count": int(
            decision_metrics["high_value_rule_count"]
        ),
        "high_value_rule_sentence_max": max(rule_sentence_counts, default=0),
        "high_value_rules_over_sentence_limit": sum(
            count > THRESHOLDS["foundation_rule_sentence_max"]
            for count in rule_sentence_counts
        ),
        "high_value_rule_decision_count": decision_rule_count,
        "high_value_rules_without_decision_semantics": int(
            decision_metrics["high_value_rules_without_decision_semantics"]
        ),
        "max_prose_line_words": max(
            (len(re.findall(r"\b[\w/-]+\b", line)) for line in prose_lines),
            default=0,
        ),
        "tutorial_explanatory_density": round(explanatory / denominator, 3),
        "decision_density": float(decision_metrics["decision_density"]),
    }


def _base_metrics(
    kind: str,
    path: Path,
    body: str,
    used_by_counts: dict[str, int],
    foundation_contracts: dict[str, dict],
    *,
    raw_source: str,
    body_is_frontmatter_fragment: bool,
) -> SkillMetrics:
    lines = body.splitlines()
    sections = parse_sections(body)
    if body_is_frontmatter_fragment:
        governed_body = strip_frontmatter_body_targeted_reference_projection(
            body,
            raw_source,
        )
        projection_overhead_lines = (
            frontmatter_body_targeted_reference_projection_line_count(
                body,
                raw_source,
            )
        )
    else:
        governed_body = strip_registry_targeted_reference_projection(body)
        projection_overhead_lines = registry_targeted_reference_projection_line_count(
            body
        )
    governed_line_count = len(lines) - projection_overhead_lines
    if governed_line_count < 0:
        raise ValidationProblem(
            f"{_repository_relative_path(path)}: Registry projection line count "
            "exceeds physical body lines"
        )
    table_count, largest_table, oversized_tables = _count_tables(body)
    annotated = _strip_fenced(lines)

    bullet_count = sum(
        1 for _index, line, in_fence in annotated if not in_fence and LIST_ITEM_RE.match(line)
    )
    code_block_count = sum(
        1 for _index, line, in_fence in annotated if FENCE_RE.match(line.strip())
    ) // 2

    anti = _find_section(sections, "Anti-Patterns")
    if anti is None:
        anti = _find_section_contains(sections, "anti-example")
    benchmark = _find_section(sections, "Industry Benchmarks")
    critical = _find_section_any(sections, "Critical Details", "Critical Gotchas")
    output_contract = _find_section_any(
        sections,
        "Output Contract",
        "Output Fragment",
        "Domain Output Addendum",
    )
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

    foundation_facts = (
        _foundation_content_facts(
            governed_body, parse_sections(governed_body)
        )
        if kind == "foundation-capability"
        else {}
    )
    foundation_contract = (
        foundation_contracts.get(path.parent.name)
        if kind == "foundation-capability"
        else None
    )
    if kind == "foundation-capability" and foundation_contract is None:
        raise ValidationProblem(
            f"{_repository_relative_path(path)}: missing Foundation content_class contract"
        )
    word_count = len(governed_body.split())
    token_count = count_o200k_base_tokens(governed_body)
    layer_budget = LAYER_ROOT_CONTENT_BUDGETS.get(kind)
    content_target_words = (
        int(foundation_contract["target_words"])
        if foundation_contract is not None
        else int(layer_budget["target_words"])
        if layer_budget is not None
        else None
    )
    content_hard_words = (
        int(foundation_contract["hard_words"])
        if foundation_contract is not None
        else int(layer_budget["hard_words"])
        if layer_budget is not None
        else None
    )
    content_target_tokens = (
        int(layer_budget["target_tokens"])
        if layer_budget is not None
        else None
    )
    content_hard_tokens = (
        FOUNDATION_CONTENT_HARD_TOKENS
        if foundation_contract is not None
        else int(layer_budget["hard_tokens"])
        if layer_budget is not None
        else None
    )
    over_target_words = (
        content_target_words is not None and word_count > content_target_words
    )
    over_hard_words = (
        content_hard_words is not None and word_count > content_hard_words
    )
    over_target_tokens = (
        content_target_tokens is not None and token_count > content_target_tokens
    )
    over_hard_tokens = (
        content_hard_tokens is not None and token_count > content_hard_tokens
    )
    metrics = SkillMetrics(
        name=path.parent.name,
        path=str(path.relative_to(ROOT)).replace("\\", "/"),
        kind=kind,
        content_class=(
            str(foundation_contract["content_class"])
            if foundation_contract is not None
            else None
        ),
        content_class_rationale=(
            foundation_contract.get("content_class_rationale")
            if foundation_contract is not None
            else None
        ),
        content_target_words=content_target_words,
        content_hard_words=content_hard_words,
        content_target_tokens=content_target_tokens,
        content_hard_tokens=content_hard_tokens,
        content_budget_scope=(
            LAYER_ROOT_CONTENT_BUDGET_SCOPE
            if content_target_words is not None
            else None
        ),
        over_content_target_words=over_target_words,
        over_content_hard_words=over_hard_words,
        over_content_target_tokens=over_target_tokens,
        over_content_hard_tokens=over_hard_tokens,
        over_content_target=over_target_words or over_target_tokens,
        over_content_hard=over_hard_words or over_hard_tokens,
        line_count=len(lines),
        governed_line_count=governed_line_count,
        projection_overhead_lines=projection_overhead_lines,
        word_count=word_count,
        token_count=token_count,
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
        **foundation_facts,
    )
    return metrics


def _score(metrics: SkillMetrics, sections: list[Section], body: str) -> None:
    kind = metrics.kind
    titles = {s.title.casefold() for s in sections}
    metrics.front_loaded_action_score = _front_loaded_action_score(body)
    if kind == "foundation-capability":
        for field_name, value in _foundation_content_facts(body, sections).items():
            setattr(metrics, field_name, value)
        decision_card = foundation_decision_card(body)
        metrics.actionability_model = str(decision_card["model"])
        metrics.actionability_findings = list(decision_card["findings"])
        metrics.actionability_applicable = bool(decision_card["applicable"])
    else:
        metrics.actionability_model = {
            "professional-skill": "runtime-front-loaded-v1",
            "domain-extension": "domain-front-loaded-v1",
        }[kind]
        metrics.actionability_findings = []
        metrics.actionability_applicable = (
            metrics.front_loaded_action_score
            < THRESHOLDS["weak_front_loaded_action"]
        )
    metrics.control_boilerplate_density = _control_boilerplate_density(body)
    metrics.generic_control_phrase_count = _generic_control_phrase_count(body)
    metrics.control_scaffold_findings = _control_scaffold_findings(kind, sections)
    metrics.control_scaffold_families = sorted(
        {
            str(finding["family"])
            for finding in metrics.control_scaffold_findings
        }
    )
    metrics.high_confidence_control_scaffold = _high_confidence_control_scaffold(
        kind,
        metrics.control_scaffold_findings,
    )

    registry_trigger = _find_section(sections, "Registry Trigger")
    if kind == "foundation-capability":
        trigger_labels = {
            line.strip().strip("*_").strip().casefold()
            for line in registry_trigger.text.splitlines()
        } if registry_trigger else set()
        has_when = "use when" in trigger_labels
        has_do_not = "do not use when" in trigger_labels
    else:
        has_when = bool(
            titles
            & {
                "when to use",
                "load when",
                "trigger signals",
                "strong domain signals",
            }
        )
        has_do_not = bool(titles & {"do not use", "do not use when", "do not load when"})
    quality_gate = _find_section_any(sections, "Execution Checklist", "Quality Gate", "Domain Quality Gate")
    non_negotiable = _find_section_any(
        sections,
        "High-Value Rules",
        "Professional Decision Rules",
        "Non-Negotiable Rules",
        "Domain-Specific Non-Negotiable Rules",
    )
    do_not_section = registry_trigger if kind == "foundation-capability" else _find_section_any(
        sections, "Do Not Use", "Do Not Use When", "Do Not Load When"
    )
    risk_section = _find_section_any(
        sections, "Stop Conditions", "Stop / Escalation Conditions", "Risk Escalation"
    )

    # --- professionalism -----------------------------------------------------
    professionalism = 100
    if not has_when:
        professionalism -= 15
        metrics.findings.append("missing load/trigger boundary")
    if not has_do_not:
        professionalism -= 15
        metrics.findings.append("missing 'Do Not Use' boundary")
    if _section_weak(non_negotiable, min_chars=200, min_bullets=3):
        professionalism -= 10
        rule_name = "High-Value Rules" if kind == "foundation-capability" else "Professional Decision Rules"
        metrics.findings.append(f"{rule_name} is thin (short prose, few rules)")
    if quality_gate is None and kind != "foundation-capability":
        professionalism -= 25
        metrics.findings.append("missing Execution Checklist")
    elif quality_gate is not None and _section_weak(quality_gate, min_chars=200, min_bullets=3):
        professionalism -= 12
        metrics.findings.append("Execution Checklist is thin (few executable checks)")
    if kind != "foundation-capability" and not (
        "output contract" in titles
        or "output fragment" in titles
        or "domain output addendum" in titles
    ):
        professionalism -= 10
    if kind != "foundation-capability" and "stop / escalation conditions" not in titles:
        professionalism -= 8
    if titles & BANNED_BEGINNER_TITLES:
        professionalism -= 25
        metrics.findings.append("contains tutorial/beginner-style section")
    if metrics.high_confidence_control_scaffold:
        professionalism -= 10
        metrics.findings.append(
            "high-confidence generic control scaffold: "
            + ", ".join(metrics.control_scaffold_families)
        )
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
        efficiency = _score_layer_content_budget(metrics, efficiency)
    elif kind == "foundation-capability":
        if metrics.line_count > THRESHOLDS["foundation_heavy_lines"]:
            efficiency -= 25
            metrics.findings.append(
                f"body {metrics.line_count} lines exceeds heavy threshold "
                f"{THRESHOLDS['foundation_heavy_lines']}"
            )
        elif metrics.line_count > THRESHOLDS["foundation_heavy_lines"] - 50:
            efficiency -= 10
        efficiency = _score_layer_content_budget(metrics, efficiency)
        if not (
            THRESHOLDS["foundation_rule_min"]
            <= metrics.high_value_rule_count
            <= THRESHOLDS["foundation_rule_max"]
        ):
            efficiency -= 12
            metrics.findings.append(
                f"High-Value Rules has {metrics.high_value_rule_count} items; "
                f"target is {THRESHOLDS['foundation_rule_min']}-"
                f"{THRESHOLDS['foundation_rule_max']}"
            )
        if metrics.high_value_rules_over_sentence_limit:
            efficiency -= min(15, 3 * metrics.high_value_rules_over_sentence_limit)
            metrics.findings.append(
                f"{metrics.high_value_rules_over_sentence_limit} High-Value Rule(s) exceed "
                f"{THRESHOLDS['foundation_rule_sentence_max']} sentences"
            )
        if metrics.max_prose_line_words > THRESHOLDS["foundation_prose_line_words_max"]:
            efficiency -= 8
            metrics.findings.append(
                f"longest prose line is {metrics.max_prose_line_words} words; "
                "long lines must not bypass content budgets"
            )
        if (
            metrics.tutorial_explanatory_density
            >= THRESHOLDS["foundation_tutorial_density_warn"]
        ):
            efficiency -= 10
            metrics.findings.append(
                f"tutorial/explanatory density {metrics.tutorial_explanatory_density:.3f} "
                "is above the decision-card advisory threshold"
            )
        if metrics.decision_density < THRESHOLDS["foundation_decision_density_warn"]:
            efficiency -= 10
            metrics.findings.append(
                f"decision density {metrics.decision_density:.3f} is below the "
                "decision-card advisory threshold"
            )
    elif kind == "domain-extension":
        if metrics.line_count > THRESHOLDS["domain_heavy_lines"]:
            efficiency -= 25
            metrics.findings.append(
                f"body {metrics.line_count} lines exceeds heavy threshold "
                f"{THRESHOLDS['domain_heavy_lines']}"
            )
        elif metrics.line_count > THRESHOLDS["domain_heavy_lines"] - 60:
            efficiency -= 10
        efficiency = _score_layer_content_budget(metrics, efficiency)

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
    if metrics.actionable_repeated_phrase_count:
        efficiency -= min(20, 2 * metrics.actionable_repeated_phrase_count)
    if _is_professional_runtime_actionability_scope(kind) and _has_weak_front_loading(metrics):
        penalty = 8 if metrics.front_loaded_action_score < THRESHOLDS["poor_front_loaded_action"] else 4
        efficiency -= penalty
        metrics.findings.append(
            f"front-loaded action score {metrics.front_loaded_action_score}/100; "
            f"first {THRESHOLDS['front_window_lines']} lines need first moves, "
            "stop conditions, gotchas, verification, or domain actions"
        )
    if metrics.control_boilerplate_density >= THRESHOLDS["control_boilerplate_density_high"]:
        efficiency -= 6
        metrics.findings.append(
            f"control boilerplate density {metrics.control_boilerplate_density:.2f} "
            "per 100 words; move repeated governance protocol text out of the body"
        )
    if metrics.generic_control_phrase_count >= THRESHOLDS["generic_control_phrase_high"]:
        efficiency -= min(8, 2 * metrics.generic_control_phrase_count)
        metrics.findings.append(
            f"generic control phrase count {metrics.generic_control_phrase_count}; "
            "dedupe repeated runtime/governance phrasing"
        )
    if metrics.high_confidence_control_scaffold:
        efficiency -= 12
        metrics.findings.append(
            "control scaffold duplicates prepare/execute/close or exact Foundation "
            "governance; retain only the Skill-specific decision increment"
        )
    if metrics.benchmark_section_length > THRESHOLDS["movable_benchmark_lines"]:
        metrics.findings.append(
            f"Industry Benchmarks is {metrics.benchmark_section_length} lines (> "
            f"{THRESHOLDS['movable_benchmark_lines']}) — summarize and move the deep list to a reference"
        )
    if metrics.anti_example_section_length > THRESHOLDS["movable_anti_lines"]:
        if kind == "foundation-capability":
            metrics.findings.append(
                f"Anti-Patterns core is {metrics.anti_example_section_length} lines (> "
                f"{THRESHOLDS['movable_anti_lines']}) — tighten to decision-bearing "
                "failures without removing the required section"
            )
        else:
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
    elif kind != "foundation-capability" and _section_weak(do_not_section, min_chars=80, min_bullets=2):
        routing -= 12
        metrics.findings.append("Do Not Use When boundary is thin")
    if kind != "foundation-capability" and risk_section is None:
        routing -= 10
    if _is_professional_runtime_actionability_scope(kind) and _has_weak_front_loading(metrics):
        routing -= 8 if metrics.front_loaded_action_score < THRESHOLDS["poor_front_loaded_action"] else 4
    if (
        metrics.control_boilerplate_density >= THRESHOLDS["control_boilerplate_density_high"]
        or metrics.generic_control_phrase_count >= THRESHOLDS["generic_control_phrase_high"]
    ):
        routing -= 4
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


def _score_layer_content_budget(metrics: SkillMetrics, efficiency: int) -> int:
    if metrics.content_target_words is None or metrics.content_hard_words is None:
        raise ValidationProblem(f"{metrics.path}: missing governed-body content budget")

    if metrics.over_content_hard_words:
        efficiency -= 30
        metrics.findings.append(
            f"governed body {metrics.word_count} words exceeds hard limit "
            f"{metrics.content_hard_words}"
        )
    elif metrics.over_content_target_words:
        efficiency -= 8
        metrics.findings.append(
            f"governed body {metrics.word_count} words exceeds target "
            f"{metrics.content_target_words}"
        )

    if metrics.content_hard_tokens is not None:
        if metrics.over_content_hard_tokens:
            efficiency -= 30
            metrics.findings.append(
                f"governed body {metrics.token_count} tokens exceeds hard limit "
                f"{metrics.content_hard_tokens}"
            )
        elif metrics.over_content_target_tokens:
            efficiency -= 8
            metrics.findings.append(
                f"governed body {metrics.token_count} tokens exceeds target "
                f"{metrics.content_target_tokens}"
            )
    return efficiency


def _has_weak_front_loading(metrics: SkillMetrics) -> bool:
    return metrics.front_loaded_action_score < THRESHOLDS["weak_front_loaded_action"]


def _is_professional_runtime_actionability_scope(kind: str) -> bool:
    return kind == "professional-skill"


def _has_weak_professional_front_loading(metrics: SkillMetrics) -> bool:
    return _is_professional_runtime_actionability_scope(metrics.kind) and _has_weak_front_loading(metrics)


def _has_control_boilerplate_issue(metrics: SkillMetrics) -> bool:
    return (
        metrics.high_confidence_control_scaffold
        or metrics.control_boilerplate_density
        >= THRESHOLDS["control_boilerplate_density_high"]
        or metrics.generic_control_phrase_count >= THRESHOLDS["generic_control_phrase_high"]
    )


def _has_high_confidence_control_boilerplate(metrics: SkillMetrics) -> bool:
    high_phrase_count = (
        metrics.generic_control_phrase_count
        >= THRESHOLDS["generic_control_phrase_classification_high"]
    )
    dense_phrase_cluster = (
        metrics.generic_control_phrase_count
        >= THRESHOLDS["generic_control_phrase_density_count"]
        and metrics.control_boilerplate_density
        >= THRESHOLDS["control_boilerplate_density_high"]
    )
    duplicated_control_lines = (
        metrics.generic_control_phrase_count >= THRESHOLDS["generic_control_phrase_high"]
        and metrics.actionable_repeated_phrase_count
        >= THRESHOLDS["control_boilerplate_repeated_phrase_high"]
    )
    return (
        metrics.high_confidence_control_scaffold
        or high_phrase_count
        or dense_phrase_cluster
        or duplicated_control_lines
    )


def _classify(metrics: SkillMetrics) -> None:
    if metrics.professionalism_score < THRESHOLDS["low_professionalism"]:
        metrics.classification = "BLOCK"
        metrics.suggested_action = (
            "Resolve the hard budget or professionalism failure before release review."
        )
        metrics.risk_of_change = "high"
        metrics.recommended_phase = "P0"
        return

    if metrics.content_target_words is None or metrics.content_hard_words is None:
        raise ValidationProblem(f"{metrics.path}: missing governed-body content budget")
    metrics.classification = classify_content_budget(
        word_count=metrics.word_count,
        token_count=metrics.token_count,
        target_words=metrics.content_target_words,
        hard_words=metrics.content_hard_words,
        target_tokens=metrics.content_target_tokens,
        hard_tokens=metrics.content_hard_tokens,
    )
    if metrics.classification == "BLOCK":
        metrics.suggested_action = (
            "Resolve the hard budget failure before release review."
        )
        metrics.risk_of_change = "high"
        metrics.recommended_phase = "P0"
        return
    if _has_high_confidence_control_boilerplate(metrics):
        metrics.classification = "TIGHTEN_BODY"
        metrics.suggested_action = (
            "Remove the generic control scaffold while preserving Skill-specific "
            "decisions, failure modes, and verification guidance."
        )
        metrics.risk_of_change = "low"
        metrics.recommended_phase = "P1"
        return
    if metrics.classification == "TIGHTEN_BODY":
        metrics.classification = "TIGHTEN_BODY"
        metrics.suggested_action = (
            "Keep decision-critical guidance. Trim duplication or move low-frequency "
            "detail into an existing targeted Reference."
        )
        metrics.risk_of_change = "low"
        metrics.recommended_phase = "P1"
        return

    if metrics.classification == "REVIEW_DENSITY":
        metrics.suggested_action = (
            "Review density and retain the current body only with explicit expert disposition."
        )
        metrics.risk_of_change = "low"
        metrics.recommended_phase = "P1"
        return

    metrics.classification = "KEEP"
    metrics.suggested_action = "Within governed-body targets; no density action is required."
    metrics.risk_of_change = "low"
    metrics.recommended_phase = "-"


def _skill_detector_payload() -> dict[str, object]:
    """Return the explicit source manifest for Skill detector behavior."""

    return _explicit_detector_source_manifest(
        contract_version="skill-content-detector-v4",
        contract_fields={
            "required_skill_fields": list(SKILL_DETECTOR_REQUIRED_SKILL_FIELDS),
            "finding_fields": list(SKILL_DETECTOR_FINDING_FIELDS),
            "review_state_values": list(REVIEW_STATE_PRIORITY),
            "review_reason_values": list(REVIEW_REASON_PRIORITY),
        },
    )


def _skill_detector_fingerprint() -> str:
    """Return the aggregate digest of the explicit Skill detector sources."""

    return str(_skill_detector_payload()["aggregate_source_digest"])


def _skill_detector_contract() -> dict[str, object]:
    """Return the report contract that makes Skill detector freshness verifiable."""

    return {
        "schema_version": SKILL_DETECTOR_SCHEMA_VERSION,
        "kind": SKILL_DETECTOR_KIND,
        "required_skill_fields": list(SKILL_DETECTOR_REQUIRED_SKILL_FIELDS),
        "finding_fields": list(SKILL_DETECTOR_FINDING_FIELDS),
        "classification_values": list(CONTENT_BUDGET_CLASSIFICATIONS),
        "review_state_values": list(REVIEW_STATE_PRIORITY),
        "review_reason_values": list(REVIEW_REASON_PRIORITY),
        "detector_fingerprint": {
            "algorithm": "sha256",
            "value": _skill_detector_fingerprint(),
        },
        "detector_source_manifest": _skill_detector_payload(),
    }


def audit(evaluation_date: date | None = None) -> dict:
    effective_evaluation_date = _effective_evaluation_date(evaluation_date)
    foundation_contracts = _load_foundation_content_contracts()
    used_by_counts = _load_used_by_counts()
    files = _collect_files()

    parsed: list[tuple[SkillMetrics, list[Section], str]] = []
    raw_line_frequency: dict[str, set[str]] = defaultdict(set)
    actionable_line_frequency: dict[str, set[str]] = defaultdict(set)
    optimality_files: set[str] = set()

    for kind, path in files:
        raw_source = read_text_preserve_newlines(path)
        try:
            _metadata, _raw, body = parse_frontmatter(path)
            body_is_frontmatter_fragment = True
        except ValidationProblem:
            body = raw_source
            _metadata = {}
            body_is_frontmatter_fragment = False
        sections = parse_sections(body)
        metrics = _base_metrics(
            kind,
            path,
            body,
            used_by_counts,
            foundation_contracts,
            raw_source=raw_source,
            body_is_frontmatter_fragment=body_is_frontmatter_fragment,
        )
        description = _metadata.get("description") if isinstance(_metadata, dict) else None
        metrics.description_length = len((description or "").strip())
        metrics.description_findings = _description_findings(kind, description)
        metrics.findings.extend(metrics.description_findings)
        # Only a full inline block (> 20 lines) counts as shared duplication; a short
        # summary that points at a reference is the resolved state, not a defect.
        optimality_section = _find_section_contains(sections, "solution optimality")
        if optimality_section is not None and optimality_section.line_count > 20:
            optimality_files.add(metrics.path)
        for normalized in set(_significant_lines(body)):
            raw_line_frequency[normalized].add(metrics.path)
        for normalized in _actionable_significant_lines(body):
            actionable_line_frequency[normalized].add(metrics.path)
        parsed.append((metrics, sections, body))

    shared_optimality = len(optimality_files) >= THRESHOLDS["common_phrase_min_files"]
    raw_common_lines = {
        line: files
        for line, files in raw_line_frequency.items()
        if len(files) >= THRESHOLDS["common_phrase_min_files"]
    }
    actionable_common_lines = {
        line: files
        for line, files in actionable_line_frequency.items()
        if len(files) >= THRESHOLDS["common_phrase_min_files"]
    }

    for metrics, sections, body in parsed:
        raw_repeated = sum(
            1
            for normalized in set(_significant_lines(body))
            if len(raw_common_lines.get(normalized, ()))
            >= THRESHOLDS["common_phrase_min_files"]
        )
        actionable_repeated = sum(
            1
            for normalized in _actionable_significant_lines(body)
            if len(actionable_common_lines.get(normalized, ()))
            >= THRESHOLDS["common_phrase_min_files"]
        )
        metrics.repeated_phrase_count = raw_repeated
        metrics.actionable_repeated_phrase_count = actionable_repeated
        metrics.has_shared_optimality = (
            shared_optimality and metrics.path in optimality_files
        )
        _score(metrics, sections, body)
        _classify(metrics)

    all_metrics = [item[0] for item in parsed]
    ai_readability = _collect_ai_readability()
    readability_by_owner = _readability_by_owner(ai_readability["documents"])
    for metrics in all_metrics:
        _assign_review_state(metrics, readability_by_owner)
    root_content, reference_content, semantic_application = (
        _collect_semantic_content_with_application(
            foundation_contracts,
            evaluation_date=effective_evaluation_date,
        )
    )
    return {
        "metrics": all_metrics,
        "common_lines": raw_common_lines,
        "raw_common_lines": raw_common_lines,
        "actionable_common_lines": actionable_common_lines,
        "optimality_files": sorted(optimality_files),
        "shared_optimality": shared_optimality,
        "ai_readability": ai_readability,
        "root_content": root_content,
        "reference_content": reference_content,
        "semantic_disposition_application": semantic_application,
    }


def _summary(
    metrics: list[SkillMetrics],
    raw_common_line_count: int = 0,
    actionable_common_line_count: int = 0,
) -> dict:
    by_kind = defaultdict(list)
    for item in metrics:
        by_kind[item.kind].append(item)

    def heavy(kind: str, gate_key: str) -> int:
        return sum(
            1 for item in by_kind[kind] if item.line_count > THRESHOLDS[gate_key]
        )

    description_lengths_by_kind = _collect_description_lengths_by_kind()
    description_recommended_by_kind = {
        kind: sum(length > DESCRIPTION_BUDGETS[kind]["recommended"] for length in lengths)
        for kind, lengths in description_lengths_by_kind.items()
    }
    description_hard_by_kind = {
        kind: sum(length > DESCRIPTION_BUDGETS[kind]["hard"] for length in lengths)
        for kind, lengths in description_lengths_by_kind.items()
    }
    review_reason_counts = Counter(
        reason for item in metrics for reason in item.review_reasons
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
        "weak_professional_front_loaded_action": sum(
            1 for item in metrics if _has_weak_professional_front_loading(item)
        ),
        "weak_front_loaded_action_all_items": sum(
            1 for item in metrics if item.actionability_applicable
        ),
        "actionability_applicable_items": sum(
            1 for item in metrics if item.actionability_applicable
        ),
        "control_boilerplate_risks": sum(
            1 for item in metrics if _has_control_boilerplate_issue(item)
        ),
        "content_tighten_candidates": sum(
            item.classification == "TIGHTEN_BODY" for item in metrics
        ),
        "content_review_density_candidates": sum(
            item.classification == "REVIEW_DENSITY" for item in metrics
        ),
        "content_blockers": sum(
            item.classification == "BLOCK" for item in metrics
        ),
        "raw_common_line_count": raw_common_line_count,
        "actionable_common_line_count": actionable_common_line_count,
        "description_recommended_over_budget": sum(
            description_recommended_by_kind.values()
        ),
        "description_hard_over_budget": sum(description_hard_by_kind.values()),
        "description_checked_by_kind": {
            kind: len(lengths) for kind, lengths in description_lengths_by_kind.items()
        },
        "description_max_length_by_kind": {
            kind: max(lengths, default=0)
            for kind, lengths in description_lengths_by_kind.items()
        },
        "description_recommended_over_budget_by_kind": description_recommended_by_kind,
        "description_hard_over_budget_by_kind": description_hard_by_kind,
        "classifications": dict(Counter(item.classification for item in metrics)),
        "review_states": dict(Counter(item.review_state for item in metrics)),
        "review_reasons": {
            reason: review_reason_counts.get(reason, 0)
            for reason in REVIEW_REASON_PRIORITY
        },
    }


def _top(metrics: list[SkillMetrics], key, reverse: bool, limit: int = 10) -> list[SkillMetrics]:
    return sorted(metrics, key=key, reverse=reverse)[:limit]


def _sorted_common_lines(common_lines: dict[str, set[str]]) -> list[tuple[str, set[str]]]:
    return sorted(common_lines.items(), key=lambda item: (-len(item[1]), item[0]))


def _format_md(result: dict) -> str:
    metrics: list[SkillMetrics] = result["metrics"]
    summary = _summary(
        metrics,
        len(result["raw_common_lines"]),
        len(result["actionable_common_lines"]),
    )
    lines: list[str] = []
    a = lines.append

    a("# rd-skills Skill Content Audit")
    a("")
    a("> Generated by `scripts/audit-skill-content.py`. Read-only evidence.")
    a(
        "> Re-run after authoring changes. Heuristic scores remain advisory; "
        "the closed gate status below is deterministic."
    )
    a("")

    gate_status = result.get("gate_status")
    if isinstance(gate_status, dict):
        a("## Gate Status")
        a("")
        a(f"- Selected gate: `{gate_status['selected_gate']}`")
        a(
            "- Deterministic authoring: "
            f"`{gate_status['authoring']['status']}`"
        )
        a(
            "- Formal release: "
            f"`{gate_status['formal_release']['status']}`"
        )
        for limitation in gate_status["limitations"]:
            a(f"- Limitation: {limitation}")
        application = result.get("semantic_disposition_application")
        application_error = (
            application.get("error") if isinstance(application, dict) else None
        )
        if isinstance(application_error, dict):
            a(
                "- Semantic application: "
                f"`{application_error.get('id')}`: "
                f"{application_error.get('message')}"
            )
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
    a(
        f"| Weak professional front-loaded action (< {THRESHOLDS['weak_front_loaded_action']}) "
        f"| {summary['weak_professional_front_loaded_action']} |"
    )
    a(
        f"| Advisory all-items weak front-loaded action (< {THRESHOLDS['weak_front_loaded_action']}) "
        f"| {summary['weak_front_loaded_action_all_items']} |"
    )
    a(f"| Control boilerplate risks | {summary['control_boilerplate_risks']} |")
    a(f"| Density review candidates | {summary['content_review_density_candidates']} |")
    a(f"| Body-tightening candidates | {summary['content_tighten_candidates']} |")
    a(f"| Content blockers | {summary['content_blockers']} |")
    a(
        f"| Raw shared lines (≥ {THRESHOLDS['common_phrase_min_files']} files) "
        f"| {len(result['raw_common_lines'])} |"
    )
    a(
        "| Actionable shared lines after excluding Targeted References "
        f"| {len(result['actionable_common_lines'])} |"
    )
    a(
        "| Description recommended-budget overages "
        f"| {summary['description_recommended_over_budget']} |"
    )
    a(
        "| Description hard-budget overages "
        f"| {summary['description_hard_over_budget']} |"
    )
    a("")
    a("Content-budget classification distribution:")
    a("")
    a("| Classification | Count |")
    a("| --- | --- |")
    for category in (
        "KEEP",
        "REVIEW_DENSITY",
        "TIGHTEN_BODY",
        "BLOCK",
    ):
        a(f"| {category} | {summary['classifications'].get(category, 0)} |")
    a("")
    a("Review-state distribution:")
    a("")
    a("| Review state | Count |")
    a("| --- | ---: |")
    for state in REVIEW_STATE_PRIORITY:
        a(f"| {state} | {summary['review_states'].get(state, 0)} |")
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

    a("### 2.6 Actionability / Control Metrics")
    a("")
    a(
        "Fields: `front_loaded_action_score`, `control_boilerplate_density`, "
        "`generic_control_phrase_count`."
    )
    a("")
    a("| Skill | Kind | front_loaded_action_score | control_boilerplate_density | generic_control_phrase_count | Top finding |")
    a("| --- | --- | --- | --- | --- | --- |")
    actionability = _top(
        metrics,
        lambda m: (
            m.front_loaded_action_score,
            -m.control_boilerplate_density,
            -m.generic_control_phrase_count,
        ),
        reverse=False,
    )
    for item in actionability:
        finding = next(
            (
                f
                for f in item.findings
                if "front-loaded action" in f
                or "control boilerplate" in f
                or "generic control phrase" in f
            ),
            item.findings[0] if item.findings else "-",
        )
        a(
            f"| `{item.name}` | {item.kind} | {item.front_loaded_action_score} | "
            f"{item.control_boilerplate_density:.2f} | {item.generic_control_phrase_count} | "
            f"{finding} |"
        )
    a("")

    a("## 3. Per Skill Findings")
    a("")
    by_kind: dict[str, list[SkillMetrics]] = defaultdict(list)
    for item in metrics:
        by_kind[item.kind].append(item)

    for kind in ("professional-skill", "foundation-capability", "domain-extension"):
        group = sorted(
            by_kind[kind],
            key=lambda m: (REVIEW_STATE_PRIORITY.index(m.review_state), m.name),
        )
        a(f"### 3.{('professional-skill', 'foundation-capability', 'domain-extension').index(kind) + 1} {KIND_LABEL[kind]} ({len(group)})")
        a("")
        a(
            "| Skill | Class | Physical lines | Governed lines | Projection lines | Words | Tokens | Prof | Ctx | Route | Front | Ctrl density | "
            "Ctrl phrases | Split | Classification | Review state | Phase | Risk |"
        )
        a("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |")
        for item in group:
            a(
                f"| `{item.name}` | `{item.content_class or '-'}` | "
                f"{item.line_count} | {item.governed_line_count} | "
                f"{item.projection_overhead_lines} | {item.word_count} | {item.token_count} | "
                f"{item.professionalism_score} | {item.context_efficiency_score} | "
                f"{item.routing_clarity_score} | {item.front_loaded_action_score} | "
                f"{item.control_boilerplate_density:.2f} | {item.generic_control_phrase_count} | "
                f"{item.split_candidate_score} | "
                f"{item.classification} | {item.review_state} | "
                f"{item.recommended_phase} | {item.risk_of_change} |"
            )
        a("")
        flagged = [item for item in group if item.review_state != "KEEP"]
        if flagged:
            a(f"#### Detailed findings — {KIND_LABEL[kind]}")
            a("")
            for item in flagged:
                a(
                    f"- **`{item.name}`** (content={item.classification}; "
                    f"review={item.review_state}; phase={item.recommended_phase}; "
                    f"risk={item.risk_of_change})"
                )
                a(f"  - Path: `{item.path}`")
                a(
                    "  - Review reasons: "
                    + ", ".join(f"`{reason}`" for reason in item.review_reasons)
                )
                a(f"  - Content-budget action: {item.suggested_action}")
                if item.findings:
                    for finding in item.findings:
                        a(f"  - Finding: {finding}")
            a("")

    a("## 4. Review State and Classification Index")
    a("")
    a("Review states preserve every matched reason; expert dispositions do not lower them.")
    a("")
    for state in REVIEW_STATE_PRIORITY:
        members = sorted(item.name for item in metrics if item.review_state == state)
        a(
            f"- **{state}** ({len(members)}): "
            f"{', '.join(f'`{name}`' for name in members) if members else '_none_'}"
        )
    a("")
    a("Content-budget classifications:")
    a("")
    categories = [
        "KEEP",
        "REVIEW_DENSITY",
        "TIGHTEN_BODY",
        "BLOCK",
    ]
    for category in categories:
        members = sorted(
            item.name for item in metrics if item.classification == category
        )
        a(f"- **{category}** ({len(members)}): {', '.join(f'`{name}`' for name in members) if members else '_none_'}")
    a("")

    a("## 5. Shared / Duplicated Content (common-reference candidates)")
    a("")
    a(
        f"Actionable lines that appear in ≥ {THRESHOLDS['common_phrase_min_files']} "
        "skills after excluding Targeted References (top 25 by fan-out):"
    )
    a("")
    a("| Files | Excerpt |")
    a("| --- | --- |")
    common_sorted = _sorted_common_lines(result["actionable_common_lines"])[:25]
    for line, file_set in common_sorted:
        excerpt = line[:90].replace("|", "\\|")
        a(f"| {len(file_set)} | {excerpt} |")
    a("")
    a(
        "> Targeted Reference policies are reported in the raw count but excluded from "
        "actionable duplication and context scoring. Repeated execution or role scaffolding "
        "remains actionable."
    )
    a("")
    if result["shared_optimality"]:
        a(
            f"> The `Solution Optimality Self-Check` block appears in "
            f"{len(result['optimality_files'])} skills and is the primary common-reference candidate."
        )
        a("")

    readability = result.get("ai_readability")
    if isinstance(readability, dict):
        readability_summary = readability["summary"]
        readability_contract = readability["contract"]
        a("## 6. AI Readability")
        a("")
        a(
            "> Sentence targets are advisory through 40 words. Sentences above "
            "40 words and compound decision Bullets block authoring."
        )
        a("")
        a(
            "Contract: ordinary target "
            f"`<={readability_contract['ordinary_target_words']}` words; complex target "
            f"`<={readability_contract['complex_target_words']}` words; hard maximum "
            f"`<={readability_contract['hard_max_words']}` words; Bullet decisions "
            f"`<={readability_contract['bullet_decision_max']}`."
        )
        a("")
        a(
            "Fingerprint: "
            f"`{readability['source_fingerprint']['value']}` over "
            f"{readability['source_fingerprint']['document_count']} documents."
        )
        a("")
        a("| Metric | Value |")
        a("| --- | ---: |")
        for label, key in (
            ("Documents", "documents"),
            ("Advisory documents", "advisory_documents"),
            ("Review-as-complex sentences", "review_as_complex_sentences"),
            ("Tighten sentences", "tighten_sentences"),
            ("Hard-fail sentences", "hard_fail_sentences"),
            ("Compound Bullets", "compound_bullets"),
        ):
            a(f"| {label} | {readability_summary[key]} |")
        a("")
        a("### 6.1 Distribution By Surface")
        a("")
        a("| Surface | Documents | Advisory docs | Review | Tighten | Hard | Compound |")
        a("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
        for surface, row in readability["by_surface"].items():
            a(
                f"| `{surface}` | {row['documents']} | {row['advisory_documents']} | "
                f"{row['review_as_complex_sentences']} | {row['tighten_sentences']} | "
                f"{row['hard_fail_sentences']} | {row['compound_bullets']} |"
            )
        a("")
        a("### 6.2 Advisory Documents")
        a("")
        a("| Document | Surface | Highest band | Review | Tighten |")
        a("| --- | --- | --- | ---: | ---: |")
        for row in readability["documents"]:
            if row["highest_advisory_band"] is None:
                continue
            a(
                f"| `{row['document_id']}` | `{row['surface']}` | "
                f"`{row['highest_advisory_band']}` | "
                f"{row['review_as_complex_count']} | {row['tighten_count']} |"
            )
        a("")

    root_content = result.get("root_content")
    if isinstance(root_content, dict):
        root_summary = root_content["summary"]
        root_semantic = root_content["semantic_advisories"]
        a("## 7. Agent-Facing Root Content")
        a("")
        a(
            "> Fresh Control Prompt and Control/Professional/Foundation/Domain root "
            "governance. Root detectors are separate from Reference semantics."
        )
        a("")
        a("| Metric | Value |")
        a("| --- | ---: |")
        for label, key in (
            ("Agent-facing root documents", "agent_facing_root_documents"),
            ("Foundation compact capabilities", "foundation_compact_capabilities"),
            ("Foundation complex capabilities", "foundation_complex_capabilities"),
            ("Foundation over class target (advisory)", "foundation_over_target_words"),
            ("Foundation compact over 400-word target", "foundation_compact_over_target_words"),
            ("Foundation complex over 500-word target", "foundation_complex_over_target_words"),
            ("Foundation over class hard word limit", "foundation_over_hard_words"),
            ("Foundation compact over 500-word hard limit", "foundation_compact_over_hard_words"),
            ("Foundation complex over 600-word hard limit", "foundation_complex_over_hard_words"),
            ("Foundation over 900-token hard gate", "foundation_over_hard_tokens"),
            ("Foundation rule-count findings", "foundation_rule_count_outside_target"),
            ("Foundation rule sentence-limit findings", "foundation_rules_over_sentence_limit"),
            ("Foundation rules without decision semantics", "foundation_rules_without_decision_semantics"),
            ("Foundation long-line findings", "foundation_long_prose_line"),
            ("Foundation tutorial-density findings", "foundation_tutorial_density"),
            ("Foundation low decision-density findings", "foundation_low_decision_density"),
            ("Governed roots within target", "content_keep"),
            ("Governed roots requiring density review", "content_review_density"),
            ("Governed roots requiring body tightening", "content_tighten_body"),
            ("Governed root blockers", "content_blockers"),
            ("Professional over word target", "professional_over_target_words"),
            ("Professional over word hard gate", "professional_over_hard_words"),
            ("Professional over token target", "professional_over_target_tokens"),
            ("Professional over token hard gate", "professional_over_hard_tokens"),
            ("Domain over word target", "domain_over_target_words"),
            ("Domain over word hard gate", "domain_over_hard_words"),
            ("Domain over token target", "domain_over_target_tokens"),
            ("Domain over token hard gate", "domain_over_hard_tokens"),
            ("Root semantic candidates", "semantic_raw_candidates"),
            ("Root semantic unresolved", "semantic_unresolved_candidates"),
            ("Root P0/P1 unresolved", "semantic_p0_p1_unresolved"),
            ("Root fixed-number unresolved", "semantic_fixed_number_unresolved"),
            ("Root dispositions configured", "semantic_disposition_configured"),
            ("Root dispositions applied", "semantic_disposition_applied"),
            ("Root disposition errors", "semantic_disposition_errors"),
        ):
            a(f"| {label} | {root_summary[key]} |")
        a("")
        root_surfaces = root_content["surface_validation"]
        a("### Root Surface Validation")
        a("")
        a("| Surface | Status | Documents | Candidates | Unresolved | Configured | Applied | Errors |")
        a("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |")
        for surface in ROOT_CONTENT_SURFACES:
            row = root_surfaces["surfaces"][surface]
            a(
                f"| `{surface}` | `{row['status']}` | {row['document_count']} | "
                f"{row['semantic_candidate_count']} | {row['semantic_unresolved_count']} | "
                f"{row['disposition_configured_count']} | {row['disposition_applied_count']} | "
                f"{len(row['errors'])} |"
            )
        if root_surfaces["common_errors"]:
            a("")
            a("Common errors: " + "; ".join(root_surfaces["common_errors"]))
        a("")
        a("### 7.1 Root Semantic Candidates")
        a("")
        a("| Candidate ID | Finding | Priority | Status | Canonical occurrence | Preview |")
        a("| --- | --- | --- | --- | --- | --- |")
        for item in root_semantic["candidates"]:
            occurrence = item["occurrences"][0]
            line_label = f"L{occurrence['lines']['start']}"
            if occurrence["lines"]["end"] != occurrence["lines"]["start"]:
                line_label += f"-L{occurrence['lines']['end']}"
            preview = item["preview"].replace("|", "\\|")
            a(
                f"| `{item['candidate_id']}` | `{item['finding']}` | "
                f"{item['priority']} | {item['governance_status']} | "
                f"`{item['path']}#{item['document_part']}:{line_label}` | {preview} |"
            )
        if not root_semantic["candidates"]:
            a("| _none_ | | | | | |")
        a("")

    reference_content = result.get("reference_content")
    if isinstance(reference_content, dict):
        reference_summary = reference_content["summary"]
        distribution = reference_content["distribution"]
        semantic_advisories = reference_content["semantic_advisories"]
        semantic_summary = semantic_advisories["summary"]
        a("## 8. Reference Content")
        a("")
        a(
            "> Registry/physical parity, exact `o200k_base` size, and fence-aware "
            "Markdown structure inventory plus lexical semantic advisory candidates."
        )
        a("")
        a("| Metric | Value |")
        a("| --- | ---: |")
        for label, key in (
            ("Indexed reference entries", "indexed_reference_entries"),
            ("Indexed unique paths", "indexed_unique_paths"),
            ("Existing indexed references", "existing_indexed_references"),
            ("Physical Markdown references", "physical_markdown_references"),
            ("Missing references", "missing_references"),
            ("Orphan references", "orphan_references"),
            ("Template assets", "template_assets"),
            ("Unindexed template assets", "unindexed_template_assets"),
            ("Indexed lines", "indexed_lines"),
            ("Indexed tokens", "indexed_tokens"),
            ("Exactly one H1", "exactly_one_h1"),
            ("Missing H1", "missing_h1"),
            ("Multiple H1", "multiple_h1"),
            ("Non-template multiple-H1 references", "non_template_multiple_h1_references"),
            ("Explicit `Reference type:` prefaces", "reference_type_prefaces"),
            ("Explicit `Load when:` prefaces", "load_when_prefaces"),
            ("Explicit `Do not load when:` prefaces", "do_not_load_when_prefaces"),
            ("Effective reference types", "effective_reference_types"),
            ("Missing effective reference types", "missing_effective_reference_types"),
            ("Effective load conditions", "effective_load_when"),
            ("Missing effective load conditions", "missing_effective_load_when"),
            ("Effective do-not-load conditions", "effective_do_not_load_when"),
            ("Missing effective do-not-load conditions", "missing_effective_do_not_load_when"),
            ("Effective required consumers", "effective_required_by"),
            ("Missing effective required consumers", "missing_effective_required_by"),
            ("Effective required outputs", "effective_required_output"),
            ("Missing effective required outputs", "missing_effective_required_output"),
            ("Effective preface conflicts", "effective_preface_conflicts"),
            ("Effective preface contract errors", "effective_preface_contract_errors"),
            ("Invalid effective preface declarations", "effective_preface_invalid"),
            ("References with empty headings", "references_with_empty_headings"),
            ("Targeted references over 60 lines", "targeted_over_60_lines"),
            ("Mode contracts over 80 lines", "mode_contract_over_80_lines"),
            ("Non-template empty-heading references", "non_template_empty_heading_references"),
            ("References over 15 decision items", "decision_items_over_15"),
            ("References with structural advisories", "structural_advisory_references"),
            ("Semantic candidates (raw)", "semantic_raw_candidates"),
            ("Semantic candidates (detector-downgraded)", "semantic_detector_downgraded_candidates"),
            ("Semantic candidates (untriaged)", "semantic_untriaged_candidates"),
            ("Semantic candidates (rewrite)", "semantic_rewrite_candidates"),
            ("Semantic candidates (resolved)", "semantic_resolved_candidates"),
            ("Semantic candidates (unresolved)", "semantic_unresolved_candidates"),
            ("Semantic unresolved fixed-number", "semantic_fixed_number_unresolved"),
            ("Semantic unresolved templated groups", "semantic_templated_group_unresolved"),
            ("Semantic unresolved absolute P0/P1", "semantic_absolute_p0_p1_unresolved"),
            ("Semantic P2 rewrite advisories", "semantic_p2_rewrite_advisories"),
            ("Semantic dispositions configured", "semantic_disposition_configured"),
            ("Semantic dispositions applied", "semantic_disposition_applied"),
            ("Semantic disposition errors", "semantic_disposition_errors"),
        ):
            a(f"| {label} | {reference_summary[key]} |")
        a("")
        reference_surfaces = reference_content["surface_validation"]
        a("### Reference Surface Validation")
        a("")
        a("| Surface | Status | Indexed | Existing | Candidates | Unresolved | Configured | Applied | Errors |")
        a("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
        for surface in REFERENCE_CONTENT_SURFACES:
            row = reference_surfaces["surfaces"][surface]
            a(
                f"| `{surface}` | `{row['status']}` | {row['indexed_reference_count']} | "
                f"{row['existing_reference_count']} | {row['semantic_candidate_count']} | "
                f"{row['semantic_unresolved_count']} | {row['disposition_configured_count']} | "
                f"{row['disposition_applied_count']} | {len(row['errors'])} |"
            )
        if reference_surfaces["common_errors"]:
            a("")
            a("Common errors: " + "; ".join(reference_surfaces["common_errors"]))
        a("")
        a("### 8.1 Distribution By Layer")
        a("")
        a("| Layer | Indexed | Existing | Missing | Physical | Orphan | Templates | Lines | Tokens | Advisory refs |")
        a("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
        for layer, _registry, _key, _root in REFERENCE_SOURCES:
            row = distribution["by_layer"][layer]
            a(
                f"| {layer} | {row['indexed']} | {row['existing_indexed']} | "
                f"{row['missing']} | {row['physical']} | {row['orphan']} | "
                f"{row['template_assets']} | {row['indexed_lines']} | {row['indexed_tokens']} | "
                f"{row['structural_advisory_references']} |"
            )
        a("")
        a("### 8.2 Distribution By Inferred Kind")
        a("")
        a("| Inferred kind | Indexed | Existing | Lines | Tokens | Advisory refs |")
        a("| --- | ---: | ---: | ---: | ---: | ---: |")
        for kind in ("targeted", "mode-contract", "template", "index"):
            row = distribution["by_kind"][kind]
            a(
                f"| {kind} | {row['indexed']} | {row['existing_indexed']} | "
                f"{row['indexed_lines']} | {row['indexed_tokens']} | "
                f"{row['structural_advisory_references']} |"
            )
        a("")

        preface_contract = reference_content["preface_contract"]
        a("### 8.3 Effective Preface Contract")
        a("")
        a(
            f"Schema `{preface_contract['schema_version']}`; precedence: "
            + " > ".join(f"`{item}`" for item in preface_contract["source_precedence"])
            + "."
        )
        a("")
        if not preface_contract["errors"] and not preface_contract["conflicts"]:
            a("_No contract errors or conflicts._")
        else:
            for item in preface_contract["errors"]:
                a(
                    f"- ERROR `{item['code']}` at `{item['path']}:L{item['line']}` — "
                    f"{item['message']}"
                )
            for item in preface_contract["conflicts"]:
                a(
                    f"- CONFLICT `{item['code']}` for `{item['path']}` "
                    f"field `{item['field']}` — {item['message']}"
                )
        a("")

        a("### 8.4 Structural Advisories")
        a("")
        advisory_labels = (
            ("Non-template references with multiple H1 headings", "non_template_multiple_h1"),
            ("Targeted references over 60 lines", "targeted_over_60_lines"),
            ("Mode contracts over 80 lines", "mode_contract_over_80_lines"),
            ("Non-template references with empty headings", "non_template_empty_headings"),
            ("References over 15 Gate/Checklist/Decision items", "decision_items_over_15"),
        )
        for label, key in advisory_labels:
            findings = reference_content["advisories"][key]
            a(f"#### {label} ({len(findings)})")
            a("")
            if not findings:
                a("_none_")
            else:
                for item in findings:
                    if key == "non_template_multiple_h1":
                        detail = f"h1_count={item['h1_count']}; expected=1"
                    elif key in {"targeted_over_60_lines", "mode_contract_over_80_lines"}:
                        detail = f"lines={item['line_count']}; limit={item['limit']}"
                    elif key == "non_template_empty_headings":
                        headings = ", ".join(
                            f"L{heading['line']} H{heading['level']} {heading['title']}"
                            for heading in item["empty_headings"]
                        )
                        detail = f"empty={headings}"
                    else:
                        detail = (
                            f"items={item['decision_item_count']} "
                            f"(list={item['list_items']}, table={item['table_items']}); "
                            f"limit={item['limit']}"
                        )
                    a(
                        f"- `{item['path']}` — layer={item['layer']}; owner={item['owner']}; "
                        f"kind={item['advisory_kind']} ({item['advisory_kind_source']}); {detail}"
                    )
            a("")

        a("### 8.5 Semantic Advisories")
        a("")
        a(
            "> These rows are deterministic governance candidates. Strict mode blocks "
            "the unresolved families named by the schema-v6 contract."
        )
        a("")
        a("| Finding | Raw | Detector-down | Untriaged | Rewrite | Resolved | Unresolved | P0/P1/P2 unresolved |")
        a("| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |")
        for finding in SEMANTIC_FINDINGS:
            row = semantic_summary["by_finding"][finding]
            a(
                f"| `{finding}` | {row['raw']} | {row['detector_downgraded']} | "
                f"{row['untriaged']} | {row['rewrite']} | {row['resolved']} | "
                f"{row['unresolved']} | {row['p0_unresolved']}/"
                f"{row['p1_unresolved']}/{row['p2_unresolved']} |"
            )
        a("")
        a("| Duplicate family | Groups | Occurrences | Tokens |")
        a("| --- | ---: | ---: | ---: |")
        for finding, metrics in semantic_summary["group_metrics"].items():
            a(
                f"| `{finding}` | {metrics['groups']} | "
                f"{metrics['occurrences']} | {metrics['tokens']} |"
            )
        a("")
        disposition_contract = semantic_advisories["disposition_contract"]
        a(
            "Semantic disposition contract: "
            f"schema={disposition_contract['schema_version']}; "
            f"source=`{disposition_contract['source']}`; "
            f"configured={disposition_contract['configured_count']}; "
            f"applied={disposition_contract['applied_count']}; "
            f"errors={len(disposition_contract['errors'])}."
        )
        a("")
        a(f"> {disposition_contract['group_scope']}")
        a("")
        a("| Candidate ID | Finding | Priority | Status | Disposition | Canonical occurrence | Occurrences | Evidence fingerprint | Content fingerprint | Preview |")
        a("| --- | --- | --- | --- | --- | --- | ---: | --- | --- | --- |")
        for item in semantic_advisories["candidates"]:
            preview = item["preview"].replace("|", "\\|")
            canonical = min(
                item["occurrences"],
                key=lambda row: (
                    row["path"],
                    row["lines"]["start"],
                    row["lines"]["end"],
                ),
            )
            canonical_lines = f"L{canonical['lines']['start']}"
            if canonical["lines"]["end"] != canonical["lines"]["start"]:
                canonical_lines += f"-L{canonical['lines']['end']}"
            a(
                f"| `{item['candidate_id']}` | `{item['finding']}` | "
                f"{item['priority'] or '-'} | {item['governance_status']} | "
                f"{item['disposition'] or '-'} | "
                f"`{canonical['path']}:{canonical_lines}` | "
                f"{item.get('occurrence_count', 1)} | "
                f"`{item['evidence_fingerprint'] or '-'}` | "
                f"`{item['content_fingerprint'] or '-'}` | {preview} |"
            )
        if not semantic_advisories["candidates"]:
            a("| _none_ | | | | | | | | |")
        a("")
        a("Limitations:")
        a("")
        for item in semantic_advisories["limitations"]:
            a(f"- {item}")
        a("")

        for title, key in (
            ("Missing Indexed References", "missing"),
            ("Orphan Physical References", "orphans"),
            ("Template Assets", "template_assets"),
        ):
            a(f"### 8.{6 + ('missing', 'orphans', 'template_assets').index(key)} {title}")
            a("")
            items = reference_content[key]
            if not items:
                a("_none_")
            else:
                for item in items:
                    suffix = (
                        f"; indexed={str(item['indexed']).lower()}"
                        if key == "template_assets"
                        else ""
                    )
                    a(
                        f"- `{item['path']}` — layer={item['layer']}; owner={item['owner']}"
                        f"{suffix}"
                    )
            a("")

    return "\n".join(lines) + "\n"


def _reference_source_safety_errors(result: dict) -> list[dict]:
    reference_content = result.get("reference_content")
    if not isinstance(reference_content, dict):
        return []
    contract = reference_content.get("preface_contract")
    if not isinstance(contract, dict):
        return []
    errors = contract.get("errors")
    if not isinstance(errors, list):
        return []
    escape_codes = {
        "registry-owner-path-outside-skills-root",
        "registry-reference-path-outside-owner",
    }
    return [
        item
        for item in errors
        if isinstance(item, dict)
        and (
            str(item.get("code", "")).startswith("source-")
            or item.get("code") in escape_codes
        )
    ]


def _gate_blocker(blocker_id: str, message: str) -> dict[str, str]:
    return {"id": blocker_id, "message": message}


def _surface_gate_blockers(label: str, content: object) -> list[dict[str, str]]:
    if not isinstance(content, dict):
        return [
            _gate_blocker(
                f"{label}-surface-invalid",
                f"{label} must be a mapping with deterministic surface validation",
            )
        ]
    validation = content.get("surface_validation")
    if not isinstance(validation, dict):
        return [
            _gate_blocker(
                f"{label}-surface-invalid",
                f"{label}.surface_validation must be a mapping",
            )
        ]
    common_errors = validation.get("common_errors")
    surfaces = validation.get("surfaces")
    failing_surfaces = (
        sorted(
            name
            for name, row in surfaces.items()
            if not isinstance(row, dict)
            or row.get("status") != "pass"
            or row.get("errors") not in (None, [])
        )
        if isinstance(surfaces, dict)
        else ["<invalid>"]
    )
    if common_errors or failing_surfaces:
        return [
            _gate_blocker(
                f"{label}-surface-invalid",
                f"{label} deterministic surface validation failed; "
                f"common_errors={len(common_errors) if isinstance(common_errors, list) else 'invalid'}; "
                f"failing_surfaces={','.join(failing_surfaces) or 'none'}",
            )
        ]
    return []


def _audit_gate_status(
    result: dict,
    summary: dict,
    *,
    selected_gate: str,
) -> dict:
    authoring_blockers: list[dict[str, str]] = []
    if int(summary.get("content_blockers", 0)):
        authoring_blockers.append(
            _gate_blocker(
                "content-blockers-present",
                "deterministic content audit reports "
                f"{int(summary['content_blockers'])} blocker(s)",
            )
        )
    readability = result.get("ai_readability")
    readability_summary = (
        readability.get("summary") if isinstance(readability, dict) else None
    )
    if not isinstance(readability_summary, dict) or (
        readability_summary.get("hard_gate_ready") is not True
    ):
        authoring_blockers.append(
            _gate_blocker(
                "ai-readability-hard-gate-not-ready",
                "AI-readability deterministic hard gate is not ready",
            )
        )
    authoring_blockers.extend(
        _surface_gate_blockers("root-content", result.get("root_content"))
    )
    authoring_blockers.extend(
        _surface_gate_blockers(
            "reference-content",
            result.get("reference_content"),
        )
    )

    application = result.get("semantic_disposition_application")
    application_current = (
        isinstance(application, dict) and application.get("status") == "current"
    )
    formal_blockers: list[dict[str, str]] = []
    if authoring_blockers:
        formal_blockers.append(
            _gate_blocker(
                "authoring-gate-not-pass",
                "formal release requires the deterministic authoring gate to pass",
            )
        )
    if not application_current:
        application_error = (
            application.get("error") if isinstance(application, dict) else None
        )
        formal_blockers.append(
            _gate_blocker(
                (
                    str(application_error.get("id"))
                    if isinstance(application_error, dict)
                    and application_error.get("id")
                    else SEMANTIC_DISPOSITION_APPLICATION_ERROR_ID
                ),
                (
                    str(application_error.get("message"))
                    if isinstance(application_error, dict)
                    and application_error.get("message")
                    else "semantic decision application is invalid"
                ),
            )
        )

    limitations = [
        (
            "The authoring gate validates deterministic source content and does "
            "not attest semantic disposition application currentness."
        )
    ]
    if not application_current:
        stale = formal_blockers[-1]
        limitations.append(
            "Formal release remains blocked: "
            f"{stale['id']}: {stale['message']}"
        )
    return {
        "schema_version": AUDIT_GATE_STATUS_SCHEMA_VERSION,
        "selected_gate": selected_gate,
        "authoring": {
            "status": "fail" if authoring_blockers else "pass",
            "blockers": authoring_blockers,
        },
        "formal_release": {
            "status": "blocked" if formal_blockers else "pass",
            "blockers": formal_blockers,
        },
        "limitations": limitations,
    }


def _args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--gate",
        choices=AUDIT_GATES,
        required=True,
        help=(
            "Select deterministic authoring exit semantics or formal-release "
            "semantics that also require a current semantic application."
        ),
    )
    parser.add_argument(
        "--release-projection",
        action="store_true",
        help="Also emit the human-readable Markdown release projection.",
    )
    parser.add_argument("--reports-dir", type=Path, default=REPORTS_DIR)
    args = parser.parse_args(argv)
    return args


def main(argv: list[str] | None = None) -> int:
    args = _args([] if argv is None else argv)
    effective_evaluation_date = _effective_evaluation_date()
    try:
        result = audit(evaluation_date=effective_evaluation_date)
        source_safety_errors = _reference_source_safety_errors(result)
        if source_safety_errors:
            first = source_safety_errors[0]
            raise ValidationProblem(
                "Reference source safety contract failed: "
                f"{first.get('code')}: {first.get('path')}"
            )
        summary = _summary(
            result["metrics"],
            len(result["raw_common_lines"]),
            len(result["actionable_common_lines"]),
        )
    except ValidationProblem as exc:
        print(f"audit-skill-content: ERROR: {exc}")
        return 1
    json_report, markdown_report = report_output_paths(
        args.reports_dir, JSON_REPORT.name, MARKDOWN_REPORT.name
    )
    args.reports_dir.mkdir(parents=True, exist_ok=True)
    result["gate_status"] = _audit_gate_status(
        result,
        summary,
        selected_gate=args.gate,
    )

    json_payload = {
        "thresholds": THRESHOLDS,
        "description_budgets": DESCRIPTION_BUDGETS,
        "summary": summary,
        "schema_version": AUDIT_SCHEMA_VERSION,
        "skill_detector": _skill_detector_contract(),
        "skills": [asdict(item) for item in result["metrics"]],
        "raw_common_lines": {
            line: sorted(files) for line, files in result["raw_common_lines"].items()
        },
        "common_lines": {
            line: sorted(files) for line, files in result["raw_common_lines"].items()
        },
        "actionable_common_lines": {
            line: sorted(files)
            for line, files in result["actionable_common_lines"].items()
        },
        "optimality_files": result["optimality_files"],
        "ai_readability": result["ai_readability"],
        "root_content": result["root_content"],
        "reference_content": result["reference_content"],
        "semantic_disposition_application": result[
            "semantic_disposition_application"
        ],
        "gate_status": result["gate_status"],
    }
    json_report.write_text(
        json.dumps(json_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if args.release_projection:
        markdown_report.write_text(_format_md(result), encoding="utf-8")

    summary = json_payload["summary"]
    try:
        displayed_json_report = json_report.relative_to(ROOT)
        displayed_markdown_report = markdown_report.relative_to(ROOT)
    except ValueError:
        displayed_json_report = json_report
        displayed_markdown_report = markdown_report
    print(
        "audit-skill-content: wrote "
        f"{displayed_json_report}"
        + (
            f" and {displayed_markdown_report}"
            if args.release_projection
            else ""
        )
        + " "
        f"({summary['professional_skills']} professional, "
        f"{summary['foundation_capabilities']} foundation, "
        f"{summary['domain_extensions']} domain; "
        f"{summary['content_review_density_candidates']} density review, "
        f"{summary['content_tighten_candidates']} tighten, "
        f"{summary['content_blockers']} blocker(s); review states: "
        + ", ".join(
            f"{state}={summary['review_states'].get(state, 0)}"
            for state in REVIEW_STATE_PRIORITY
            if summary["review_states"].get(state, 0)
        )
        + ")."
        f" References: {json_payload['reference_content']['summary']['existing_indexed_references']} existing indexed, "
        f"{json_payload['reference_content']['summary']['missing_references']} missing, "
        f"{json_payload['reference_content']['summary']['orphan_references']} orphan, "
        f"{json_payload['reference_content']['summary']['template_assets']} template asset(s)."
    )
    gate_status = json_payload["gate_status"]
    for blocker in gate_status["authoring"]["blockers"]:
        print(
            "audit-skill-content: ERROR: "
            f"{blocker['id']}: {blocker['message']}",
            file=sys.stderr,
        )
    application = json_payload["semantic_disposition_application"]
    if application.get("status") != "current":
        error = application.get("error") or {}
        level = "ERROR" if args.gate == "formal-release" else "LIMITATION"
        print(
            f"audit-skill-content: {level}: "
            f"{error.get('id', SEMANTIC_DISPOSITION_APPLICATION_ERROR_ID)}: "
            f"{error.get('message', 'semantic decision application is invalid')}",
            file=sys.stderr,
        )
    selected_status = (
        gate_status["authoring"]["status"]
        if args.gate == "authoring"
        else gate_status["formal_release"]["status"]
    )
    return 0 if selected_status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
