#!/usr/bin/env python3
"""Validate fresh agent-facing root content and strict semantic governance."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from datetime import date
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT_SCRIPT = ROOT / "scripts/audit-skill-content.py"


@lru_cache(maxsize=1)
def _load_auditor() -> ModuleType:
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    name = "validate_root_content_auditor"
    spec = importlib.util.spec_from_file_location(name, AUDIT_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {AUDIT_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _fresh_root_content(
    *, evaluation_date: date | None = None
) -> dict[str, Any]:
    auditor = _load_auditor()
    if evaluation_date is None:
        return auditor._collect_root_content()
    return auditor._collect_root_content(evaluation_date=evaluation_date)


def _surface_validation_contract(root_content: dict[str, Any]) -> list[str]:
    auditor = _load_auditor()
    reported = root_content.get("surface_validation")
    if not isinstance(reported, dict):
        return ["root_content.surface_validation must be a mapping"]
    errors: list[str] = []
    if set(reported) != {"schema_version", "common_errors", "surfaces"}:
        errors.append(
            "root_content.surface_validation must contain exactly schema_version, common_errors, and surfaces"
        )
    if reported.get("schema_version") != auditor.SURFACE_VALIDATION_SCHEMA_VERSION:
        errors.append(
            "root_content.surface_validation.schema_version must equal "
            f"{auditor.SURFACE_VALIDATION_SCHEMA_VERSION}"
        )
    common_errors = reported.get("common_errors")
    if (
        not isinstance(common_errors, list)
        or any(not isinstance(item, str) or not item for item in common_errors)
        or common_errors != list(dict.fromkeys(common_errors))
    ):
        errors.append(
            "root_content.surface_validation.common_errors must be an ordered unique string list"
        )
    surfaces = reported.get("surfaces")
    if not isinstance(surfaces, dict) or set(surfaces) != set(
        auditor.ROOT_CONTENT_SURFACES
    ):
        errors.append(
            "root_content.surface_validation.surfaces must exactly match the declared Root surfaces"
        )
        surfaces = {}
    expected_fields = {
        "status",
        "document_count",
        "semantic_candidate_count",
        "semantic_unresolved_count",
        "semantic_p0_p1_unresolved_count",
        "semantic_fixed_number_unresolved_count",
        "disposition_configured_count",
        "disposition_applied_count",
        "errors",
    }
    for surface in auditor.ROOT_CONTENT_SURFACES:
        row = surfaces.get(surface)
        context = f"root_content.surface_validation.surfaces.{surface}"
        if not isinstance(row, dict) or set(row) != expected_fields:
            errors.append(f"{context} fields do not match the closed schema")
            continue
        if row.get("status") not in {"pass", "fail"}:
            errors.append(f"{context}.status must be pass or fail")
        for field in expected_fields - {"status", "errors"}:
            value = row.get(field)
            if type(value) is not int or value < 0:
                errors.append(f"{context}.{field} must be a non-negative integer")
        row_errors = row.get("errors")
        if (
            not isinstance(row_errors, list)
            or any(not isinstance(item, str) or not item for item in row_errors)
            or row_errors != list(dict.fromkeys(row_errors))
        ):
            errors.append(f"{context}.errors must be an ordered unique string list")
    documents = root_content.get("documents")
    advisories = root_content.get("advisories")
    semantic = root_content.get("semantic_advisories")
    if isinstance(documents, list) and isinstance(advisories, dict) and isinstance(semantic, dict):
        expected = auditor._root_surface_validation(documents, advisories, semantic)
        if reported != expected:
            errors.append(
                "root_content.surface_validation does not match canonical source attribution"
            )
    return errors


def _evaluate(
    root_content: dict[str, Any],
    *,
    strict: bool,
    evaluation_date: date | None = None,
) -> tuple[dict[str, int], list[str]]:
    auditor = _load_auditor()
    effective_evaluation_date = (
        auditor._effective_evaluation_date()
        if evaluation_date is None
        else evaluation_date
    )
    errors: list[str] = []
    if root_content.get("schema_version") != auditor.ROOT_CONTENT_SCHEMA_VERSION:
        errors.append(
            f"root_content.schema_version must equal {auditor.ROOT_CONTENT_SCHEMA_VERSION}"
        )
    documents = root_content.get("documents")
    advisories = root_content.get("advisories")
    summary = root_content.get("summary")
    semantic = root_content.get("semantic_advisories")
    if not isinstance(documents, list):
        documents = []
        errors.append("root_content.documents must be a list")
    if not isinstance(advisories, dict):
        advisories = {}
        errors.append("root_content.advisories must be a mapping")
    if not isinstance(summary, dict):
        summary = {}
        errors.append("root_content.summary must be a mapping")
    if not isinstance(semantic, dict):
        semantic = {}
        errors.append("root_content.semantic_advisories must be a mapping")
    errors.extend(_surface_validation_contract(root_content))

    budgeted_documents = [
        item
        for item in documents
        if isinstance(item, dict)
        and item.get("layer") in {
            "professional-skill",
            "foundation-capability",
            "domain-extension",
        }
        and item.get("document_part") == "body"
    ]
    foundation_documents = [
        item
        for item in budgeted_documents
        if item.get("layer") == "foundation-capability"
    ]
    for index, document in enumerate(budgeted_documents):
        layer = str(document.get("layer"))
        label = f"{layer} root document[{index}]"
        content_class = document.get("content_class")
        if layer == "foundation-capability":
            try:
                budget = auditor.foundation_content_budget(content_class)
            except auditor.ValidationProblem as exc:
                errors.append(f"{label}: {exc}")
                continue
            target_tokens = None
            hard_tokens = auditor.FOUNDATION_CONTENT_HARD_TOKENS
            rationale = document.get("content_class_rationale")
            class_entry = {"content_class": content_class}
            if rationale is not None:
                class_entry["content_class_rationale"] = rationale
            errors.extend(
                auditor.foundation_content_class_errors(class_entry, label)
            )
        else:
            budget = auditor.LAYER_ROOT_CONTENT_BUDGETS[layer]
            target_tokens = budget["target_tokens"]
            hard_tokens = budget["hard_tokens"]
            if content_class is not None:
                errors.append(f"{label}: content_class must be null")

        if document.get("content_budget_scope") != auditor.LAYER_ROOT_CONTENT_BUDGET_SCOPE:
            errors.append(f"{label}: content_budget_scope does not match policy")
        for field, expected in (
            ("content_target_words", budget["target_words"]),
            ("content_hard_words", budget["hard_words"]),
            ("content_target_tokens", target_tokens),
            ("content_hard_tokens", hard_tokens),
        ):
            if document.get(field) != expected:
                errors.append(f"{label}: {field} does not match layer budget")
        word_count = document.get("word_count")
        token_count = document.get("token_count")
        if type(word_count) is not int or type(token_count) is not int:
            errors.append(f"{label}: word_count and token_count must be integers")
            continue
        expected_flags = {
            "over_content_target_words": word_count > budget["target_words"],
            "over_content_hard_words": word_count > budget["hard_words"],
            "over_content_target_tokens": (
                target_tokens is not None and token_count > target_tokens
            ),
            "over_content_hard_tokens": token_count > hard_tokens,
        }
        expected_flags["over_content_target"] = (
            expected_flags["over_content_target_words"]
            or expected_flags["over_content_target_tokens"]
        )
        expected_flags["over_content_hard"] = (
            expected_flags["over_content_hard_words"]
            or expected_flags["over_content_hard_tokens"]
        )
        for field, expected in expected_flags.items():
            if document.get(field) is not expected:
                errors.append(f"{label}: {field} does not match governed counts")
        expected_classification = auditor.classify_content_budget(
            word_count=word_count,
            token_count=token_count,
            target_words=budget["target_words"],
            hard_words=budget["hard_words"],
            target_tokens=target_tokens,
            hard_tokens=hard_tokens,
        )
        if document.get("content_budget_classification") != expected_classification:
            errors.append(
                f"{label}: content_budget_classification does not match governed counts"
            )

    candidates = semantic.get("candidates")
    if not isinstance(candidates, list):
        candidates = []
        errors.append("root semantic candidates must be a list")
    if candidates != sorted(candidates, key=auditor._root_candidate_sort_key):
        errors.append("root semantic candidates must be canonically sorted")
    if semantic.get("schema_version") != auditor.ROOT_SEMANTIC_SCHEMA_VERSION:
        errors.append(
            "root semantic schema_version must equal "
            f"{auditor.ROOT_SEMANTIC_SCHEMA_VERSION}"
        )
    if semantic.get("finding_families") != list(auditor.ROOT_SEMANTIC_FINDINGS):
        errors.append("root semantic finding_families must match the closed root family list")
    seen: set[str] = set()
    for index, candidate in enumerate(candidates):
        label = f"root semantic candidate[{index}]"
        if not isinstance(candidate, dict):
            errors.append(f"{label} must be a mapping")
            continue
        finding = candidate.get("finding")
        path = candidate.get("path")
        if finding not in auditor.ROOT_SEMANTIC_FINDINGS:
            errors.append(f"{label}.finding is not declared")
            continue
        try:
            source_selector = auditor._validate_root_semantic_source_selector(
                candidate.get("source_selector")
            )
            expected_id = auditor._root_semantic_candidate_id(source_selector)
        except (TypeError, ValueError):
            expected_id = None
            errors.append(f"{label}.source_selector is invalid")
        candidate_id = candidate.get("candidate_id")
        if candidate_id != expected_id:
            errors.append(f"{label}.candidate_id does not match stable identity inputs")
        elif candidate_id in seen:
            errors.append(f"{label}.candidate_id must be unique")
        else:
            seen.add(candidate_id)
        if candidate.get("priority") not in auditor.SEMANTIC_PRIORITIES:
            errors.append(f"{label}.priority is invalid")
        occurrences = candidate.get("occurrences")
        if not isinstance(occurrences, list) or not occurrences:
            errors.append(f"{label}.occurrences must be a non-empty list")
        elif candidate.get("occurrence_count") != len(occurrences):
            errors.append(f"{label}.occurrence_count must match occurrences")
        else:
            try:
                expected_occurrence = auditor._root_occurrence_fingerprint(occurrences)
                expected_context = auditor._root_context_membership_fingerprint(occurrences)
            except (KeyError, TypeError, ValueError):
                expected_occurrence = expected_context = None
            if candidate.get("occurrence_fingerprint") != expected_occurrence:
                errors.append(f"{label}.occurrence_fingerprint does not match occurrences")
            if candidate.get("context_fingerprint") != expected_context:
                errors.append(f"{label}.context_fingerprint does not match occurrences")
        disposition = candidate.get("disposition")
        needs_confirmation = candidate.get("governance_status") == "needs-confirmation"
        expected_resolved = disposition in auditor.SEMANTIC_RESOLVED_DISPOSITIONS
        expected_unresolved = needs_confirmation or not expected_resolved
        expected_status = (
            f"resolved-{disposition}"
            if expected_resolved
            else (
                "unresolved-rewrite"
                if disposition == "rewrite"
                else ("needs-confirmation" if needs_confirmation else "untriaged")
            )
        )
        if (
            candidate.get("resolved") is not expected_resolved
            or candidate.get("unresolved") is not expected_unresolved
            or candidate.get("governance_status") != expected_status
        ):
            errors.append(f"{label} governance state is inconsistent")

    contract = semantic.get("disposition_contract")
    if not isinstance(contract, dict):
        contract = {}
        errors.append("root semantic disposition_contract must be a mapping")
    elif set(contract) != {
        "schema_version",
        "source",
        "configured_count",
        "applied_count",
        "entries",
        "errors",
        "common_errors",
        "surface_errors",
    }:
        errors.append("root semantic disposition_contract fields do not match the closed schema")
    entries = contract.get("entries")
    if not isinstance(entries, list):
        entries = []
        errors.append("root semantic disposition entries must be a list")
    reported_contract_errors = contract.get("errors")
    if not isinstance(reported_contract_errors, list):
        reported_contract_errors = []
        errors.append("root semantic disposition errors must be a list")
    elif reported_contract_errors:
        errors.extend(
            f"root semantic disposition contract: {item}"
            for item in reported_contract_errors
        )
    normalized, _raw_matches, disposition_errors = (
        auditor._validate_root_semantic_dispositions(
            candidates,
            entries,
            effective_evaluation_date,
            require_applied=False,
        )
    )
    if reported_contract_errors != disposition_errors:
        errors.append(
            "root semantic disposition contract errors do not match canonical validation"
        )
    expected_common_errors, expected_surface_errors = (
        auditor._root_disposition_error_attribution(
            disposition_errors,
            entries,
            candidates,
        )
    )
    if contract.get("common_errors") != expected_common_errors:
        errors.append(
            "root semantic disposition common_errors do not match attributable errors"
        )
    if contract.get("surface_errors") != expected_surface_errors:
        errors.append(
            "root semantic disposition surface_errors do not match attributable errors"
        )
    _applied_normalized, matches, applied_errors = (
        auditor._validate_root_semantic_dispositions(
            candidates,
            entries,
            effective_evaluation_date,
            require_applied=True,
        )
    )
    if applied_errors != disposition_errors:
        errors.append(
            "root semantic applied disposition state does not match surface fail-closed validation"
        )
    if normalized != entries:
        errors.append("root semantic disposition entries are not canonical")
    if contract.get("configured_count") != len(entries):
        errors.append("root semantic configured_count does not match entries")
    if contract.get("applied_count") != len(matches):
        errors.append("root semantic applied_count does not match exact matches")

    unresolved = sum(bool(item.get("unresolved")) for item in candidates if isinstance(item, dict))
    p0_p1 = sum(
        bool(item.get("unresolved")) and item.get("priority") in {"P0", "P1"}
        for item in candidates if isinstance(item, dict)
    )
    fixed = sum(
        bool(item.get("unresolved"))
        and item.get("finding") == "fixed_duration_threshold_status_candidate"
        for item in candidates if isinstance(item, dict)
    )
    counts = {
        "documents": len(documents),
        "semantic_raw": len(candidates),
        "semantic_needs_confirmation": sum(
            item.get("governance_status") == "needs-confirmation"
            for item in candidates
            if isinstance(item, dict)
        ),
        "semantic_unresolved": unresolved,
        "semantic_p0_p1_unresolved": p0_p1,
        "semantic_fixed_number_unresolved": fixed,
        "foundation_over_target_words": len(advisories.get("foundation_over_target_words") or []),
        "foundation_over_hard_words": len(advisories.get("foundation_over_hard_words") or []),
        "foundation_over_hard_tokens": len(advisories.get("foundation_over_hard_tokens") or []),
        "foundation_compact_capabilities": sum(
            item.get("content_class") == "compact" for item in foundation_documents
        ),
        "foundation_complex_capabilities": sum(
            item.get("content_class") == "complex" for item in foundation_documents
        ),
        "foundation_compact_over_target_words": len(
            advisories.get("foundation_compact_over_target_words") or []
        ),
        "foundation_compact_over_hard_words": len(
            advisories.get("foundation_compact_over_hard_words") or []
        ),
        "foundation_complex_over_target_words": len(
            advisories.get("foundation_complex_over_target_words") or []
        ),
        "foundation_complex_over_hard_words": len(
            advisories.get("foundation_complex_over_hard_words") or []
        ),
        "foundation_rule_count_outside_target": len(advisories.get("foundation_rule_count_outside_target") or []),
        "foundation_rules_over_sentence_limit": len(advisories.get("foundation_rules_over_sentence_limit") or []),
        "foundation_rules_without_decision_semantics": len(advisories.get("foundation_rules_without_decision_semantics") or []),
        "foundation_long_prose_line": len(advisories.get("foundation_long_prose_line") or []),
        "foundation_tutorial_density": len(advisories.get("foundation_tutorial_density") or []),
        "foundation_low_decision_density": len(advisories.get("foundation_low_decision_density") or []),
        "content_keep": sum(
            item.get("content_budget_classification") == "KEEP"
            for item in budgeted_documents
        ),
        "content_review_density": len(
            advisories.get("content_review_density") or []
        ),
        "content_tighten_body": len(
            advisories.get("content_tighten_body") or []
        ),
        "content_blockers": len(advisories.get("content_blockers") or []),
        "professional_over_target_words": len(
            advisories.get("professional_over_target_words") or []
        ),
        "professional_over_hard_words": len(
            advisories.get("professional_over_hard_words") or []
        ),
        "professional_over_target_tokens": len(
            advisories.get("professional_over_target_tokens") or []
        ),
        "professional_over_hard_tokens": len(
            advisories.get("professional_over_hard_tokens") or []
        ),
        "domain_over_target_words": len(
            advisories.get("domain_over_target_words") or []
        ),
        "domain_over_hard_words": len(
            advisories.get("domain_over_hard_words") or []
        ),
        "domain_over_target_tokens": len(
            advisories.get("domain_over_target_tokens") or []
        ),
        "domain_over_hard_tokens": len(
            advisories.get("domain_over_hard_tokens") or []
        ),
        "dispositions_configured": len(entries),
        "dispositions_applied": len(matches),
        "disposition_errors": len(reported_contract_errors),
    }
    expected_summary = {
        "agent_facing_root_documents": counts["documents"],
        "foundation_over_target_words": counts["foundation_over_target_words"],
        "foundation_over_hard_words": counts["foundation_over_hard_words"],
        "foundation_over_hard_tokens": counts["foundation_over_hard_tokens"],
        "foundation_compact_capabilities": counts["foundation_compact_capabilities"],
        "foundation_complex_capabilities": counts["foundation_complex_capabilities"],
        "foundation_compact_over_target_words": counts[
            "foundation_compact_over_target_words"
        ],
        "foundation_compact_over_hard_words": counts[
            "foundation_compact_over_hard_words"
        ],
        "foundation_complex_over_target_words": counts[
            "foundation_complex_over_target_words"
        ],
        "foundation_complex_over_hard_words": counts[
            "foundation_complex_over_hard_words"
        ],
        "foundation_rule_count_outside_target": counts["foundation_rule_count_outside_target"],
        "foundation_rules_over_sentence_limit": counts["foundation_rules_over_sentence_limit"],
        "foundation_rules_without_decision_semantics": counts["foundation_rules_without_decision_semantics"],
        "foundation_long_prose_line": counts["foundation_long_prose_line"],
        "foundation_tutorial_density": counts["foundation_tutorial_density"],
        "foundation_low_decision_density": counts["foundation_low_decision_density"],
        "content_keep": counts["content_keep"],
        "content_review_density": counts["content_review_density"],
        "content_tighten_body": counts["content_tighten_body"],
        "content_blockers": counts["content_blockers"],
        "professional_over_target_words": counts["professional_over_target_words"],
        "professional_over_hard_words": counts["professional_over_hard_words"],
        "professional_over_target_tokens": counts["professional_over_target_tokens"],
        "professional_over_hard_tokens": counts["professional_over_hard_tokens"],
        "domain_over_target_words": counts["domain_over_target_words"],
        "domain_over_hard_words": counts["domain_over_hard_words"],
        "domain_over_target_tokens": counts["domain_over_target_tokens"],
        "domain_over_hard_tokens": counts["domain_over_hard_tokens"],
        "semantic_raw_candidates": counts["semantic_raw"],
        "semantic_needs_confirmation_candidates": counts[
            "semantic_needs_confirmation"
        ],
        "semantic_unresolved_candidates": counts["semantic_unresolved"],
        "semantic_p0_p1_unresolved": counts["semantic_p0_p1_unresolved"],
        "semantic_fixed_number_unresolved": counts["semantic_fixed_number_unresolved"],
        "semantic_disposition_configured": counts["dispositions_configured"],
        "semantic_disposition_applied": counts["dispositions_applied"],
        "semantic_disposition_errors": counts["disposition_errors"],
    }
    for field, expected in expected_summary.items():
        if summary.get(field) != expected:
            errors.append(f"root_content.summary.{field} does not match canonical content")

    layer_budget = root_content.get("layer_root_budget_contract")
    expected_layer_budget = {
        "schema_version": 1,
        "scope": auditor.LAYER_ROOT_CONTENT_BUDGET_SCOPE,
        "classifications": list(auditor.CONTENT_BUDGET_CLASSIFICATIONS),
        "target_enforcement": "expert-disposition-required",
        "hard_enforcement": "strict-no-exception",
        "tighten_threshold": "greater-than-90-percent-of-triggered-hard-limit",
        "layers": auditor.LAYER_ROOT_CONTENT_BUDGETS,
    }
    if layer_budget != expected_layer_budget:
        errors.append(
            "root_content.layer_root_budget_contract does not match canonical policy"
        )

    budget = root_content.get("foundation_budget_contract")
    if not isinstance(budget, dict):
        errors.append("root_content.foundation_budget_contract must be a mapping")
    else:
        expected_budget = {
            "schema_version": 1,
            "registry_schema_version": auditor.REGISTRY_SCHEMA_VERSIONS["foundation"],
            "content_classes": {
                "compact": {
                    **auditor.FOUNDATION_CONTENT_BUDGETS["compact"],
                    "rationale_required": False,
                },
                "complex": {
                    **auditor.FOUNDATION_CONTENT_BUDGETS["complex"],
                    "rationale_required": True,
                },
            },
            "hard_token_limit": auditor.FOUNDATION_CONTENT_HARD_TOKENS,
            "content_budget_scope": auditor.LAYER_ROOT_CONTENT_BUDGET_SCOPE,
            "target_enforcement": "expert-disposition-required",
            "strict_basis": "class-hard-word-limit-and-universal-hard-token-limit",
            "class_counts": {
                "compact": counts["foundation_compact_capabilities"],
                "complex": counts["foundation_complex_capabilities"],
            },
            "rule_contract": auditor.FOUNDATION_RULE_CONTRACT,
        }
        if set(budget) != set(expected_budget):
            errors.append(
                "root_content.foundation_budget_contract does not match canonical policy"
            )
        for field, expected in expected_budget.items():
            if budget.get(field) != expected:
                errors.append(
                    f"Foundation budget contract field {field} does not match canonical policy"
                )

    if strict:
        for label, key in (
            ("root P0/P1 unresolved semantic candidate(s)", "semantic_p0_p1_unresolved"),
            ("root fixed-number unresolved semantic candidate(s)", "semantic_fixed_number_unresolved"),
            ("Foundation root(s) over class hard word limit", "foundation_over_hard_words"),
            ("Foundation root(s) over 900 tokens", "foundation_over_hard_tokens"),
            ("Professional root(s) over 650 words", "professional_over_hard_words"),
            ("Professional root(s) over 1000 tokens", "professional_over_hard_tokens"),
            ("Domain root(s) over 600 words", "domain_over_hard_words"),
            ("Domain root(s) over 900 tokens", "domain_over_hard_tokens"),
            ("Foundation High-Value Rules count outside 3-8", "foundation_rule_count_outside_target"),
            ("Foundation High-Value Rule(s) over two sentences", "foundation_rules_over_sentence_limit"),
            ("Foundation High-Value Rule(s) without decision semantics", "foundation_rules_without_decision_semantics"),
            ("Foundation root(s) below required decision density", "foundation_low_decision_density"),
        ):
            if counts[key]:
                errors.append(f"{label}: {counts[key]}")
    return counts, errors


def _format_counts(counts: dict[str, int], *, strict: bool) -> list[str]:
    return [
        f"validate-root-content: mode={'strict' if strict else 'default'}; evidence=fresh-source",
        (
            "validate-root-content: inventory "
            f"documents={counts['documents']} semantic_raw={counts['semantic_raw']} "
            f"needs_confirmation={counts['semantic_needs_confirmation']} "
            f"unresolved={counts['semantic_unresolved']} "
            f"p0_p1_unresolved={counts['semantic_p0_p1_unresolved']} "
            f"fixed_number_unresolved={counts['semantic_fixed_number_unresolved']}"
        ),
        (
            "validate-root-content: foundation-budget "
            f"compact={counts['foundation_compact_capabilities']} "
            f"complex={counts['foundation_complex_capabilities']} "
            f"over_class_target={counts['foundation_over_target_words']} "
            f"compact_over_400={counts['foundation_compact_over_target_words']} "
            f"complex_over_500={counts['foundation_complex_over_target_words']} "
            f"over_class_hard={counts['foundation_over_hard_words']} "
            f"compact_over_500_hard={counts['foundation_compact_over_hard_words']} "
            f"complex_over_600_hard={counts['foundation_complex_over_hard_words']} "
            f"over_900_tokens={counts['foundation_over_hard_tokens']} "
            f"rule_count={counts['foundation_rule_count_outside_target']} "
            f"rule_sentences={counts['foundation_rules_over_sentence_limit']} "
            f"rule_decision_semantics={counts['foundation_rules_without_decision_semantics']} "
            f"long_line={counts['foundation_long_prose_line']} "
            f"tutorial_density={counts['foundation_tutorial_density']} "
            f"low_decision_density={counts['foundation_low_decision_density']}"
        ),
        (
            "validate-root-content: layer-root-budget "
            f"keep={counts['content_keep']} "
            f"review_density={counts['content_review_density']} "
            f"tighten_body={counts['content_tighten_body']} "
            f"block={counts['content_blockers']} "
            f"professional_word_target={counts['professional_over_target_words']} "
            f"professional_word_hard={counts['professional_over_hard_words']} "
            f"professional_token_target={counts['professional_over_target_tokens']} "
            f"professional_token_hard={counts['professional_over_hard_tokens']} "
            f"domain_word_target={counts['domain_over_target_words']} "
            f"domain_word_hard={counts['domain_over_hard_words']} "
            f"domain_token_target={counts['domain_over_target_tokens']} "
            f"domain_token_hard={counts['domain_over_hard_tokens']}"
        ),
        (
            "validate-root-content: dispositions "
            f"configured={counts['dispositions_configured']} "
            f"applied={counts['dispositions_applied']} "
            f"errors={counts['disposition_errors']}"
        ),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    try:
        effective_evaluation_date = _load_auditor()._effective_evaluation_date()
        root_content = _fresh_root_content(
            evaluation_date=effective_evaluation_date
        )
        counts, errors = _evaluate(
            root_content,
            strict=args.strict,
            evaluation_date=effective_evaluation_date,
        )
    except Exception as exc:  # ValidationProblem is loaded with the auditor.
        print(f"validate-root-content: ERROR: {exc}", file=sys.stderr)
        return 1
    for line in _format_counts(counts, strict=args.strict):
        print(line)
    if errors:
        for error in errors:
            print(f"validate-root-content: ERROR: {error}", file=sys.stderr)
        return 1
    print("validate-root-content: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
