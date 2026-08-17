#!/usr/bin/env python3
"""Gate Hookless authoring and formal content-release contracts.

The pre-Hookless professionalism baseline is intentionally reported as
incomparable.  This validator fails current structural/captured-evidence errors,
but it never converts that into host performance, real-host accuracy, or an
installed-experience claim.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import re
import secrets
import stat
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import date
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from types import ModuleType
from typing import Any

from capability_coverage import fixture_ids, validate_capability_coverage
from validation_utils import (
    AFFECTED_CONTEXT_ENV,
    EXPERT_PANEL_RELEASE_MANIFEST_ARTIFACTS,
    EXPERT_PANEL_RELEASE_MANIFEST_SCHEMA_VERSION,
    PROFESSIONAL_COVERAGE_STATES,
    PROFESSIONAL_REVIEW_COST_FIELDS,
    PROFESSIONAL_REVIEW_COST_LIMITATIONS,
    PROFESSIONAL_REVIEW_COST_TEXT_FIELDS,
    PROFESSIONAL_REVIEW_FORMAL_ROUND_POLICY_FIELDS,
    PROFESSIONAL_REVIEW_FIXTURE_LIMITATIONS,
    ValidationProblem,
    load_yaml_file,
    parse_affected_professionalism_context,
    validate_core_contracts,
    validate_expert_panel_release_manifest,
)
import expert_panel_review as expert_panel


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_VALIDATOR = ROOT / "scripts" / "validate-reference-content.py"
ROOT_VALIDATOR = ROOT / "scripts" / "validate-root-content.py"
CONTENT_AUDITOR = ROOT / "scripts" / "audit-skill-content.py"
COVERAGE_EVALUATOR = ROOT / "scripts" / "eval-skill-professionalism.py"
BENCHMARK_EVALUATOR = ROOT / "scripts" / "eval-professional-benchmarks.py"
CAPABILITY_MATRIX = ROOT / "evals" / "capability-coverage" / "matrix.yaml"
DEFAULT_RELEASE_REVIEW_CONFIG = ROOT / "config" / "professionalism-release-review.yaml"
CORE_CONTRACTS = ROOT / "src" / "control-model" / "core-contracts.json"
AUTHORING_GATE_PASS = "current-contract-pass"
AUTHORING_GATE_FAIL = "current-contract-fail"
RELEASE_GATE_PASS = "release-ready"
RELEASE_GATE_FAIL = "release-not-ready"
EXPERT_PANEL_RELEASE_MANIFEST_BLOCKER_CATEGORY = (
    "expert-panel-release-manifest-release-gate"
)
PROFESSIONALISM_REPORT_SCHEMA_VERSION = 4
FORMAL_HEAD_COMMIT_ENV = "CHANGEFORGE_FORMAL_HEAD_COMMIT"
FORMAL_EVIDENCE_ROOT = ".rd-skills/formal-release"

REFERENCE_DEFAULT_COUNT_FIELDS = (
    "missing_indexed_references",
    "non_template_orphan_references",
    "missing_h1_references",
    "non_template_multiple_h1_references",
    "non_template_empty_heading_references",
    "effective_preface_contract_errors",
    "effective_preface_conflicts",
    "effective_preface_invalid_declarations",
)
REFERENCE_STRICT_COUNT_FIELDS = (
    "missing_effective_reference_types",
    "missing_effective_load_when",
    "missing_effective_do_not_load_when",
    "missing_effective_required_by",
    "missing_effective_required_output",
    "targeted_over_60_lines",
    "mode_contract_over_80_lines",
    "decision_items_over_15",
    "fixed_number_unresolved_candidates",
    "templated_block_unresolved_groups",
    "unconditional_absolute_p0_p1_unresolved_candidates",
)
REFERENCE_STRUCTURAL_STRICT_COUNT_FIELDS = (
    *REFERENCE_DEFAULT_COUNT_FIELDS,
    "missing_effective_reference_types",
    "missing_effective_load_when",
    "missing_effective_do_not_load_when",
    "missing_effective_required_by",
    "missing_effective_required_output",
    "targeted_over_60_lines",
    "mode_contract_over_80_lines",
    "decision_items_over_15",
)
ROOT_STRUCTURAL_STRICT_COUNT_FIELDS = (
    "foundation_over_hard_words",
    "foundation_over_hard_tokens",
    "professional_over_hard_words",
    "professional_over_hard_tokens",
    "domain_over_hard_words",
    "domain_over_hard_tokens",
    "foundation_rule_count_outside_target",
    "foundation_rules_over_sentence_limit",
    "foundation_rules_without_decision_semantics",
    "foundation_low_decision_density",
)
ROOT_SEMANTIC_STRICT_COUNT_FIELDS = (
    "semantic_p0_p1_unresolved_candidates",
    "semantic_fixed_number_unresolved_candidates",
)
EXPERT_ATTESTATION_FIELDS = {
    "schema_version",
    "scope",
    "complete",
    "source_fingerprints",
    "attested_by",
    "attested_on",
    "evidence",
    "limitations",
    "content_dispositions",
    "readability_dispositions",
}
EXPERT_SOURCE_FINGERPRINT_FIELDS = {
    "reference_content",
    "root_content",
    "ai_readability",
}
EXPERT_EVIDENCE_FIELDS = {"path", "sha256"}
EXPERT_CONTENT_DISPOSITION_FIELDS = {
    "path",
    "classification",
    "disposition",
    "rationale",
}
EXPERT_CONTENT_DISPOSITIONS = {
    "accepted-current-density",
    "tracked-tightening",
}
EXPERT_READABILITY_DISPOSITION_FIELDS = {
    "document_id",
    "highest_band",
    "disposition",
    "rationale",
}
EXPERT_READABILITY_DISPOSITIONS = {
    "accepted-current-readability",
    "tracked-tightening",
}
EXPERT_PANEL_ATTESTATION_FIELDS = {
    "schema_version",
    "scope",
    "decision_method",
    "source_fingerprints",
    "panel_record",
    "limitations",
}
EXPERT_PANEL_RECORD_FIELDS = {"path", "sha256"}
DUAL_PANEL_CONFIG_FIELDS = {
    "schema_version",
    "review_owner",
    "reviewed_at",
    "decisions",
    "readability_review_attestation",
    "professional_completeness_review_attestation",
}
READABILITY_CONFIG_ATTESTATION_FIELDS = {
    "schema_version",
    "panel_kind",
    "scope",
    "decision_method",
    "limitations",
}
PROFESSIONAL_CONFIG_ATTESTATION_FIELDS = {
    "schema_version",
    "panel_kind",
    "scope",
    "decision_method",
    "limitations",
}
READABILITY_SOURCE_FINGERPRINT_FIELDS = set(
    expert_panel.panel_contracts.READABILITY_SOURCE_FINGERPRINT_KEYS
)
LEGACY_READABILITY_SOURCE_FINGERPRINT_FIELDS = set(
    expert_panel.panel_contracts.READABILITY_LEGACY_SOURCE_FINGERPRINT_KEYS
)
GENERATED_EXPERT_EVIDENCE_PATHS = {
    "docs/MARKETPLACE_CATALOG.md",
    "docs/SHOWCASE.md",
}


def validate_capability_coverage_matrix(
    matrix_path: Path = CAPABILITY_MATRIX,
    *,
    root: Path = ROOT,
) -> list[str]:
    """Validate complete inventory, dispositions, and current evidence."""

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
            evidence_ids=evidence_catalog,
        ),
    ]


@dataclass
class Finding:
    category: str
    target: str
    message: str
    severity: str = "error"


@dataclass
class Result:
    schema_version: int = field(
        default=PROFESSIONALISM_REPORT_SCHEMA_VERSION,
        init=False,
    )
    mode: str
    status: str
    authoring_gate: str
    release_gate: str
    strict: bool
    baseline_comparison: str
    evidence_scope: str
    content_audit_summary: dict[str, Any] = field(default_factory=dict)
    ai_readability_summary: dict[str, Any] = field(default_factory=dict)
    reference_content_summary: dict[str, Any] = field(default_factory=dict)
    root_content_summary: dict[str, Any] = field(default_factory=dict)
    content_readiness: dict[str, Any] = field(default_factory=dict)
    coverage_gate_summary: dict[str, Any] = field(default_factory=dict)
    expert_panel_release_manifest: dict[str, Any] = field(default_factory=dict)
    professional_review_cost_fixtures: dict[str, Any] = field(
        default_factory=dict
    )
    blockers: list[Finding] = field(default_factory=list)
    release_blockers: list[Finding] = field(default_factory=list)
    advisories: list[Finding] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    limitations: list[str] = field(default_factory=list)


def _affected_package_ids() -> list[str]:
    evaluator = _load_coverage_evaluator()
    return sorted(
        str(entry.get("name", ""))
        for kind, entry in evaluator._load_entries()
        if kind != "control"
    )


def _canonical_package_list(
    value: object,
    *,
    label: str,
    known_package_ids: set[str],
) -> list[str]:
    if (
        not isinstance(value, list)
        or any(not isinstance(item, str) or not item for item in value)
        or value != sorted(set(value))
    ):
        raise ValueError(f"{label} must be a sorted unique package list")
    unknown = sorted(set(value) - known_package_ids)
    if unknown:
        raise ValueError(f"{label} names unknown packages: {unknown}")
    return value


def _affected_reports(
    directory: Path,
    context: dict[str, Any],
    known_package_ids: list[str],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    names = {
        "skill": "skill-professionalism-eval.json",
        "depth": "skill-professionalism-depth.json",
        "coverage": "professional-coverage-matrix.json",
    }
    reports: dict[str, dict[str, Any]] = {}
    for key, name in names.items():
        path = directory / name
        if not path.is_file():
            raise ValueError(f"required affected report missing: {path}")
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError(f"required affected report is not a mapping: {path}")
        reports[key] = value

    execution_scope = reports["skill"].get("execution_scope")
    expected_scope_fields = {
        "mode",
        "direct_package_ids",
        "fresh_package_ids",
        "carried_package_ids",
        "unevaluated_package_ids",
        "baseline_stale_no_carry",
        "baseline_decision",
        "reasons_by_package",
        "reason_chains",
        "control_skill_checked",
    }
    if (
        not isinstance(execution_scope, dict)
        or set(execution_scope) != expected_scope_fields
        or execution_scope.get("mode") != "affected"
    ):
        raise ValueError("affected execution_scope is not canonical")
    for key, report in reports.items():
        if report.get("execution_scope") != execution_scope:
            raise ValueError(
                f"{names[key]} execution_scope does not match affected evidence"
            )

    known = set(known_package_ids)
    direct = _canonical_package_list(
        execution_scope.get("direct_package_ids"),
        label="affected direct_package_ids",
        known_package_ids=known,
    )
    fresh = _canonical_package_list(
        execution_scope.get("fresh_package_ids"),
        label="affected fresh_package_ids",
        known_package_ids=known,
    )
    carried = _canonical_package_list(
        execution_scope.get("carried_package_ids"),
        label="affected carried_package_ids",
        known_package_ids=known,
    )
    unevaluated = _canonical_package_list(
        execution_scope.get("unevaluated_package_ids"),
        label="affected unevaluated_package_ids",
        known_package_ids=known,
    )
    baseline_stale_no_carry = execution_scope.get("baseline_stale_no_carry")
    if not isinstance(baseline_stale_no_carry, bool):
        raise ValueError("affected baseline_stale_no_carry must be boolean")
    if any(
        left & right
        for left, right in (
            (set(fresh), set(carried)),
            (set(fresh), set(unevaluated)),
            (set(carried), set(unevaluated)),
        )
    ) or set(fresh) | set(carried) | set(unevaluated) != known:
        raise ValueError("affected package sets must partition the inventory")
    if not set(direct).issubset(fresh):
        raise ValueError("affected direct packages must be fresh")
    professionalism = context["professionalism"]
    if direct != professionalism["direct_package_ids"]:
        raise ValueError("affected direct packages do not match canonical context")
    if execution_scope.get("reason_chains") != professionalism["reason_chains"]:
        raise ValueError("affected reason chains do not match canonical context")
    if execution_scope.get("control_skill_checked") is not False:
        raise ValueError("affected execution cannot claim Control Skill coverage")

    reasons = execution_scope.get("reasons_by_package")
    if not isinstance(reasons, dict) or set(reasons) != known:
        raise ValueError("affected reasons_by_package must cover the inventory")
    for package_id in known_package_ids:
        package_reasons = reasons.get(package_id)
        if (
            not isinstance(package_reasons, list)
            or any(not isinstance(item, str) or not item for item in package_reasons)
        ):
            raise ValueError(
                f"affected reasons for {package_id!r} must be non-blank strings"
            )
        if package_id in fresh and not package_reasons:
            raise ValueError(f"affected fresh package {package_id!r} lacks a reason")
        if package_id in set(carried) | set(unevaluated) and package_reasons:
            raise ValueError(
                f"affected non-evaluated package {package_id!r} has a fresh reason"
            )

    affected_scope = professionalism["scope"]
    baseline_decision = execution_scope.get("baseline_decision")
    if affected_scope == "full":
        if (
            direct
            or fresh != known_package_ids
            or carried
            or unevaluated
            or baseline_stale_no_carry
            or baseline_decision is not None
        ):
            raise ValueError("affected full scope must freshly evaluate every package")
        if reasons != {
            package_id: ["impact-scope-full"] for package_id in known_package_ids
        }:
            raise ValueError("affected full scope reasons are not canonical")
    elif affected_scope == "packages":
        if not direct:
            raise ValueError("affected package scope requires direct packages")
        if not isinstance(baseline_decision, str) or not baseline_decision:
            raise ValueError("affected package scope lacks its carry baseline")
        if baseline_stale_no_carry:
            if carried:
                raise ValueError(
                    "stale affected baseline cannot authorize carried packages"
                )
        elif unevaluated:
            raise ValueError(
                "validated affected carry scope cannot leave packages unevaluated"
            )
        candidate = Path(baseline_decision)
        if (
            candidate.is_absolute()
            or ".." in candidate.parts
            or candidate.as_posix() != baseline_decision
            or candidate.suffix != ".json"
        ):
            raise ValueError("affected carry baseline path is not canonical")
    else:
        raise ValueError("affected regression cannot run with professionalism scope none")

    expected_schemas = {"skill": 2, "depth": 2, "coverage": 3}
    for key, expected_schema in expected_schemas.items():
        report = reports[key]
        if report.get("schema_version") != expected_schema:
            raise ValueError(
                f"{names[key]} schema_version must equal {expected_schema}"
            )
        if report.get("errors") != []:
            raise ValueError(f"{names[key]} contains affected validation errors")
    for key in ("skill", "depth"):
        rows = reports[key].get("results")
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise ValueError(f"{names[key]} results must be a list of mappings")
        if [row.get("name") for row in rows] != fresh:
            raise ValueError(f"{names[key]} results do not equal the fresh package closure")
        if any(row.get("status") != "pass" or row.get("errors", []) for row in rows):
            raise ValueError(f"{names[key]} contains a failing fresh package")
    skill = reports["skill"]
    if (
        skill.get("architecture") != "hookless-control-plane"
        or skill.get("skills_checked") != len(fresh)
        or skill.get("error_count") != 0
    ):
        raise ValueError("skill-professionalism-eval.json summary is inconsistent")
    coverage = reports["coverage"]
    if (
        coverage.get("architecture") != "hookless-control-plane"
        or coverage.get("evaluation_kind")
        != "affected-static-authoring-evidence"
        or coverage.get("rows") != []
        or coverage.get("gate_summary")
        != {
            "required_skill_count": 0,
            "pass_count": 0,
            "fail_count": 0,
            "not_required_count": len(fresh),
        }
    ):
        raise ValueError("professional-coverage-matrix.json is not affected-only")
    return reports, execution_scope


def _write_affected_result(
    directory: Path,
    *,
    args: argparse.Namespace,
    context: dict[str, Any],
    execution_scope: dict[str, Any],
) -> None:
    payload = {
        "schema_version": PROFESSIONALISM_REPORT_SCHEMA_VERSION,
        "mode": "affected",
        "status": "affected-current-contract-pass",
        "authoring_gate": "affected-current-contract-pass",
        "release_gate": "not-evaluated",
        "strict": bool(args.strict),
        "baseline_comparison": "not-evaluated",
        "evidence_scope": "affected-partial-json",
        "affected_context": context,
        "execution_scope": execution_scope,
        "expert_panel_release_manifest": {
            "schema_version": EXPERT_PANEL_RELEASE_MANIFEST_SCHEMA_VERSION,
            "status": "not-evaluated",
            "head_commit": None,
            "artifacts": [],
            "verification_toolchain": None,
        },
        "blockers": [],
        "release_blockers": [],
        "advisories": [],
        "summary": {
            "direct_package_count": len(execution_scope["direct_package_ids"]),
            "fresh_package_count": len(execution_scope["fresh_package_ids"]),
            "carried_package_count": len(execution_scope["carried_package_ids"]),
            "unevaluated_package_count": len(
                execution_scope["unevaluated_package_ids"]
            ),
            "blocker_count": 0,
        },
        "limitations": [
            "Affected evidence is isolated JSON-only authoring evidence and is not full regression authority.",
            "Affected evidence does not establish formal release, expert-review currentness, or Markdown freshness.",
        ]
        + (
            [
                "The stale baseline authorizes no carry; unevaluated packages remain outside this PR-only evidence."
            ]
            if execution_scope["baseline_stale_no_carry"]
            else []
        ),
    }
    (directory / "professionalism-regression-report.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _affected_main(
    args: argparse.Namespace,
    context: dict[str, Any],
    known_package_ids: list[str],
) -> int:
    if args.release_projection or args.update_baseline or args.require_expert_content_review:
        raise ValidationProblem(
            "affected professionalism evidence cannot project release or lifecycle artifacts"
        )
    _reports_by_kind, execution_scope = _affected_reports(
        args.reports_dir,
        context,
        known_package_ids,
    )
    _write_affected_result(
        args.reports_dir,
        args=args,
        context=context,
        execution_scope=execution_scope,
    )
    print(
        "validate-professionalism-regression: "
        "authoring_gate=affected-current-contract-pass; "
        "release_gate=not-evaluated; evidence=affected-partial-json"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _args(sys.argv[1:] if argv is None else argv)
    args.reports_dir.mkdir(parents=True, exist_ok=True)
    output_directory = args.output_dir or args.reports_dir
    formal_head_commit = (
        os.environ.get(FORMAL_HEAD_COMMIT_ENV)
        if args.release_projection
        else None
    )
    if formal_head_commit is not None:
        expected_output_directory = (
            ROOT
            / FORMAL_EVIDENCE_ROOT
            / formal_head_commit
            / "reports"
        ).absolute()
        if output_directory.absolute() != expected_output_directory:
            print(
                "validate-professionalism-regression: ERROR: formal output "
                "directory is not bound to the captured Core HEAD",
                file=sys.stderr,
            )
            return 1
    else:
        output_directory.mkdir(parents=True, exist_ok=True)
    raw_affected_context = os.environ.get(AFFECTED_CONTEXT_ENV)
    if raw_affected_context is not None:
        try:
            known_package_ids = _affected_package_ids()
            context = parse_affected_professionalism_context(
                raw_affected_context,
                known_package_ids=known_package_ids,
            )
            assert context is not None
            return _affected_main(args, context, known_package_ids)
        except (OSError, json.JSONDecodeError, ValidationProblem, ValueError) as exc:
            print(
                f"validate-professionalism-regression: ERROR: {exc}",
                file=sys.stderr,
            )
            return 1
    formal_manifest = bool(
        args.release_projection or args.require_expert_content_review
    )
    try:
        expert_panel_storage_statuses = _validate_current_expert_panel_storage(
            formal=formal_manifest
        )
    except (OSError, json.JSONDecodeError, ValidationProblem, ValueError) as exc:
        print(f"validate-professionalism-regression: ERROR: {exc}", file=sys.stderr)
        return 1
    try:
        reports = _reports(args.reports_dir)
        _validate_fresh_benchmark_report(reports["benchmarks"])
        content_audit_summary = _content_audit_summary(reports["content"])
        ai_readability_summary = _ai_readability_summary(reports["content"])
        reference_content_summary = _reference_content_summary(reports["content"])
        root_content_summary = _root_content_summary(reports["content"])
        expert_reviews = _expert_reviews(
            args.release_review_config,
            reference_fingerprint=reference_content_summary["source_fingerprint"],
            root_fingerprint=root_content_summary["source_fingerprint"],
            ai_readability_fingerprint=ai_readability_summary[
                "source_fingerprint"
            ],
            content_skills=reports["content"].get("skills"),
            readability_content=reports["content"].get("ai_readability"),
            content_audit=reports["content"],
            storage_statuses=expert_panel_storage_statuses,
            formal=formal_manifest,
        )
        content_readiness = _content_readiness(
            reference_content_summary,
            root_content_summary,
            expert_reviews,
        )
        coverage_gate_summary = _coverage_gate_summary(
            reports["coverage"],
            args.release_review_config,
        )
        professional_review_cost_fixtures = (
            _professional_review_cost_fixtures()
        )
        expert_panel_release_manifest = _expert_panel_release_manifest(
            formal=formal_manifest,
            storage_statuses=expert_panel_storage_statuses,
        )
    except (OSError, json.JSONDecodeError, ValidationProblem, ValueError) as exc:
        print(f"validate-professionalism-regression: ERROR: {exc}", file=sys.stderr)
        return 1

    baseline_comparison = _baseline_state(args.baseline)
    blockers: list[Finding] = []
    advisories: list[Finding] = []
    for key, report in reports.items():
        for message in _strings(report.get("errors")):
            blockers.append(Finding("current-report-error", key, message))
    reference_blockers, reference_advisories = _reference_content_findings(
        reference_content_summary
    )
    blockers.extend(reference_blockers)
    root_blockers, root_advisories = _root_content_findings(root_content_summary)
    blockers.extend(root_blockers)
    readability_blockers, readability_advisories = _readability_gate_findings(
        ai_readability_summary
    )
    blockers.extend(readability_blockers)
    blockers.extend(_coverage_gate_findings(coverage_gate_summary))
    skill_report = reports["skill"]
    skill_results = [row for row in skill_report.get("results", []) if isinstance(row, dict)]
    professional = [row for row in skill_results if row.get("kind") == "professional"]
    if len(professional) != 26:
        blockers.append(
            Finding(
                "professional-skill-count",
                "skill-professionalism-eval.json",
                f"expected 26 registered Professional Skills, found {len(professional)}",
            )
        )
    for row in professional:
        if row.get("status") == "fail" or row.get("missing_sections"):
            blockers.append(
                Finding(
                    "professional-skill-contract",
                    str(row.get("name", "<unknown>")),
                    "required AI execution or registry contract is incomplete",
                )
            )
    for warning in _strings(skill_report.get("warnings")):
        advisories.append(Finding("authoring-advisory", "skill-professionalism-eval.json", warning, "warning"))

    content_followups = {
        key: value
        for key, value in content_audit_summary.items()
        if key
        in {
            "content_review_density_candidates",
            "content_tighten_candidates",
            "weak_front_loaded_skills",
            "description_recommended_over_budget_count",
            "actionable_duplicate_line_count",
        }
        and value
    }
    if content_followups:
        details = ", ".join(
            f"{key}={value}" for key, value in sorted(content_followups.items())
        )
        advisories.append(
            Finding(
                "content-efficiency-advisory",
                "skill-content-audit.json",
                details,
                "warning",
            )
        )
    review_state_followups = {
        state: count
        for state, count in content_audit_summary["review_states"].items()
        if state != "KEEP" and count
    }
    if review_state_followups:
        details = ", ".join(
            f"{state}={count}"
            for state, count in review_state_followups.items()
        )
        advisories.append(
            Finding(
                "skill-review-state-advisory",
                "skill-content-audit.json",
                details,
                "warning",
            )
        )
    advisories.extend(reference_advisories)
    advisories.extend(root_advisories)
    advisories.extend(readability_advisories)

    benchmark = reports["benchmarks"]
    comparison_passes = sum(
        row.get("comparison_status") in {"pass", "expected-fail-detected"}
        for row in benchmark.get("results", [])
        if isinstance(row, dict)
    )
    if comparison_passes != int(benchmark.get("cases_checked", 0)):
        blockers.append(
            Finding(
                "benchmark-comparison",
                "professional-benchmarks-report.json",
                "not every captured benchmark comparison passed or detected its expected adversarial failure",
            )
        )
    promoted = reports["samples"]
    if int(promoted.get("promoted_checked", 0)) < 2:
        blockers.append(
            Finding(
                "promoted-sample-count",
                "professional-agent-samples-report.json",
                "at least two human-reviewed promoted captures are required",
            )
        )

    if baseline_comparison != "not-numerically-comparable":
        advisories.append(
            Finding(
                "historical-baseline",
                _rel(args.baseline),
                "baseline is unavailable or malformed; no historical comparison claim is made",
                "info",
            )
        )

    authoring_gate = AUTHORING_GATE_PASS if not blockers else AUTHORING_GATE_FAIL
    release_gate, release_blockers = _release_gate(
        authoring_gate,
        blockers,
        expert_reviews,
        root_content_summary,
        content_audit_summary,
        expert_panel_release_manifest=expert_panel_release_manifest,
    )
    application = content_audit_summary.get(
        "semantic_disposition_application",
        {"status": "current", "error": None},
    )
    application_limitations: list[str] = []
    if application["status"] != "current":
        application_error = application["error"]
        application_limitations.append(
            "Formal release remains blocked: "
            f"{application_error['id']}: {application_error['message']}"
        )
    result = Result(
        mode="strict" if args.strict else "default",
        status=authoring_gate,
        authoring_gate=authoring_gate,
        release_gate=release_gate,
        strict=args.strict,
        baseline_comparison=baseline_comparison,
        evidence_scope="deterministic-fixtures",
        content_audit_summary=content_audit_summary,
        ai_readability_summary=ai_readability_summary,
        reference_content_summary=reference_content_summary,
        root_content_summary=root_content_summary,
        content_readiness=content_readiness,
        coverage_gate_summary=coverage_gate_summary,
        expert_panel_release_manifest=expert_panel_release_manifest,
        professional_review_cost_fixtures=(
            professional_review_cost_fixtures
        ),
        blockers=blockers,
        release_blockers=release_blockers,
        advisories=advisories,
        summary={
            "skills_checked": int(skill_report.get("skills_checked", 0)),
            "professional_skills_checked": len(professional),
            "benchmark_cases_checked": int(benchmark.get("cases_checked", 0)),
            "benchmark_comparisons_passed": comparison_passes,
            "promoted_samples_checked": int(promoted.get("promoted_checked", 0)),
            "coverage_required_skills": coverage_gate_summary["required_skill_count"],
            "coverage_gate_passes": coverage_gate_summary["pass_count"],
            "coverage_gate_failures": coverage_gate_summary["fail_count"],
            "blocker_count": len(blockers),
            "release_blocker_count": len(release_blockers),
            "advisory_count": len(advisories),
        },
        limitations=[
            "Authoring reports are static source checks.",
            "Benchmark comparisons and promoted-agent reports use checked-in deterministic fixtures.",
            "The removed-architecture baseline is not numerically comparable.",
            "Deterministic fixtures do not prove wall-clock performance, real-host accuracy, or the installed user experience.",
            "reference_content_summary.strict_ready is Reference-only and preserves the reference-strict-v4 contract; it does not attest Root content or expert review.",
            "Root strict readiness is recomputed from fresh agent-facing Root source and blocks the authoring gate when its strict structural or semantic contract fails.",
            "AI-readability uses one three-reviewer full-coverage panel; Professional Completeness uses a separate per-Skill qualified reviewer pool with domain-critical fail-closed decisions. Neither axis can substitute for the other, and pending or stale evidence does not redefine the authoring gate.",
            "Coverage gates are recomputed from deterministic routing, captured benchmark, and captured pressure fixtures; they do not prove live-agent behavior.",
            *application_limitations,
        ],
    )
    if args.update_baseline:
        _write_snapshot(args.baseline, result, reports)
        result.mode = "baseline-snapshot-updated"
        result.baseline_comparison = "not-numerically-comparable"
    _write(
        output_directory,
        result,
        release_projection=args.release_projection,
        trusted_root=(ROOT if formal_head_commit is not None else None),
    )
    print(
        "validate-professionalism-regression: "
        f"authoring_gate={result.authoring_gate}; release_gate={result.release_gate}; "
        f"strict={args.strict}; blockers={len(blockers)}; "
        f"release_blockers={len(release_blockers)}; "
        f"reference_strict_ready={str(reference_content_summary['strict_ready']).lower()}; "
        f"root_strict_ready={str(root_content_summary['strict_ready']).lower()}; "
        "content_structural_strict_ready="
        f"{str(content_readiness['aggregate']['structural_strict_ready']).lower()}; "
        "content_semantic_triage_complete="
        f"{str(content_readiness['aggregate']['semantic_triage_complete']).lower()}; "
        "readability_review_current="
        f"{str(content_readiness['aggregate']['readability_review_current']).lower()}; "
        "professional_completeness_review_current="
        f"{str(content_readiness['aggregate']['professional_completeness_review_current']).lower()}; "
        f"coverage_gate_failures={coverage_gate_summary['fail_count']}; "
        f"baseline={result.baseline_comparison}; evidence={result.evidence_scope}"
    )
    for finding in blockers:
        print(
            f"validate-professionalism-regression: ERROR: {finding.target}: {finding.message}",
            file=sys.stderr,
        )
    if args.require_expert_content_review:
        for finding in release_blockers:
            if finding not in blockers:
                print(
                    "validate-professionalism-regression: ERROR: "
                    f"{finding.target}: {finding.message}",
                    file=sys.stderr,
                )
    exit_blocked = bool(blockers) or (
        args.require_expert_content_review and bool(release_blockers)
    )
    return 0 if args.report_only or not exit_blocked else 1


def _args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=ROOT / "config/professionalism-baseline.yaml")
    parser.add_argument("--reports-dir", type=Path, default=ROOT / "reports")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--routing-dir", type=Path, default=ROOT / "evals/routing")
    parser.add_argument("--content-exceptions", type=Path)
    parser.add_argument(
        "--release-review-config",
        type=Path,
        default=DEFAULT_RELEASE_REVIEW_CONFIG,
    )
    parser.add_argument("--update-baseline", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--report-only", action="store_true")
    parser.add_argument("--release-projection", action="store_true")
    parser.add_argument(
        "--require-expert-content-review",
        action="store_true",
        help=(
            "With --strict, fail unless both independent expert review axes and "
            "the current Semantic disposition application are current; "
            "incompatible with --report-only."
        ),
    )
    args = parser.parse_args(argv)
    if args.require_expert_content_review and not args.strict:
        parser.error("--require-expert-content-review requires --strict")
    if args.require_expert_content_review and args.report_only:
        parser.error(
            "--require-expert-content-review cannot be combined with --report-only"
        )
    if args.output_dir is not None and not args.release_projection:
        parser.error("--output-dir requires --release-projection")
    return args


def _reports(directory: Path) -> dict[str, dict[str, Any]]:
    names = {
        "skill": "skill-professionalism-eval.json",
        "depth": "skill-professionalism-depth.json",
        "coverage": "professional-coverage-matrix.json",
        "benchmarks": "professional-benchmarks-report.json",
        "samples": "professional-agent-samples-report.json",
        "content": "skill-content-audit.json",
    }
    result: dict[str, dict[str, Any]] = {}
    for key, name in names.items():
        path = directory / name
        if not path.is_file():
            raise ValueError(f"required report missing: {path}")
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError(f"required report is not a mapping: {path}")
        if value.get("architecture") not in {None, "hookless-control-plane"} and key in {"skill", "benchmarks", "samples"}:
            raise ValueError(f"required report is not Hookless v2 evidence: {path}")
        if key in {"skill", "depth", "coverage"}:
            execution_scope = value.get("execution_scope")
            if (
                not isinstance(execution_scope, dict)
                or execution_scope.get("mode") != "full"
            ):
                raise ValueError(
                    f"{name} must contain full professionalism evidence; "
                    "affected partial evidence is isolated from full regression"
                )
        result[key] = value
    samples = result["samples"]
    expected_sample_contract = {
        "strict": True,
        "promoted_only": True,
        "candidates_only": False,
    }
    for field, expected in expected_sample_contract.items():
        if samples.get(field) is not expected:
            raise ValueError(
                "professional-agent-samples-report.json must be generated with "
                f"--promoted-only --strict: expected {field}={expected!r}"
            )
    return result


def _baseline_state(path: Path) -> str:
    if not path.is_file():
        return "missing"
    try:
        text = path.read_text(encoding="utf-8")
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = load_yaml_file(path)
    except (OSError, ValidationProblem):
        return "malformed"
    if isinstance(data, dict) and data.get("hookless_schema_version") == 2:
        return "not-numerically-comparable"
    return "legacy-incomparable"


def _content_audit_summary(report: dict[str, Any]) -> dict[str, Any]:
    auditor = _load_content_auditor()
    expected_schema = auditor.AUDIT_SCHEMA_VERSION
    if report.get("schema_version") != expected_schema:
        raise ValueError(
            "skill-content-audit.json: schema_version must equal "
            f"{expected_schema}"
        )
    gate_status = report.get("gate_status")
    if (
        not isinstance(gate_status, dict)
        or gate_status.get("schema_version") != 1
        or gate_status.get("selected_gate") not in {"authoring", "formal-release"}
    ):
        raise ValueError(
            "skill-content-audit.json: gate_status must be a current closed gate report"
        )
    authoring_status = gate_status.get("authoring")
    formal_status = gate_status.get("formal_release")
    if (
        not isinstance(authoring_status, dict)
        or authoring_status.get("status") not in {"pass", "fail"}
        or not isinstance(authoring_status.get("blockers"), list)
        or not isinstance(formal_status, dict)
        or formal_status.get("status") not in {"pass", "blocked"}
        or not isinstance(formal_status.get("blockers"), list)
        or not isinstance(gate_status.get("limitations"), list)
    ):
        raise ValueError(
            "skill-content-audit.json: gate_status has invalid status or blocker fields"
        )
    application = report.get("semantic_disposition_application")
    if (
        not isinstance(application, dict)
        or application.get("status") not in {"current", "invalid"}
    ):
        raise ValueError(
            "skill-content-audit.json: semantic disposition application status is invalid"
        )
    application_error = application.get("error")
    if application["status"] == "current":
        if application_error is not None:
            raise ValueError(
                "skill-content-audit.json: current semantic disposition "
                "application cannot carry an error"
            )
        normalized_application_error = None
    else:
        if (
            not isinstance(application_error, dict)
            or not isinstance(application_error.get("id"), str)
            or not application_error["id"]
            or not isinstance(application_error.get("message"), str)
            or not application_error["message"]
        ):
            raise ValueError(
                "skill-content-audit.json: invalid semantic disposition "
                "application must preserve its exact error"
            )
        if formal_status["status"] != "blocked":
            raise ValueError(
                "skill-content-audit.json: stale semantic disposition "
                "application must block the formal audit gate"
            )
        normalized_application_error = {
            "id": application_error["id"],
            "message": application_error["message"],
        }
    _validate_skill_detector_contract(report)
    summary = report.get("summary")
    if not isinstance(summary, dict):
        raise ValueError("skill-content-audit.json: summary must be a mapping")
    actionable = report.get("actionable_common_lines")
    if not isinstance(actionable, dict):
        raise ValueError(
            "skill-content-audit.json: actionable_common_lines must be a mapping"
        )
    classifications = summary.get("classifications")
    if not isinstance(classifications, dict):
        classifications = {}
    skills = report["skills"]
    review_states = summary.get("review_states")
    expected_review_states = {
        state: sum(row["review_state"] == state for row in skills)
        for state in auditor.REVIEW_STATE_PRIORITY
        if any(row["review_state"] == state for row in skills)
    }
    if review_states != expected_review_states:
        raise ValueError(
            "skill-content-audit.json: summary.review_states does not match skills"
        )
    review_reasons = summary.get("review_reasons")
    expected_review_reasons = {
        reason: sum(reason in row["review_reasons"] for row in skills)
        for reason in auditor.REVIEW_REASON_PRIORITY
    }
    if review_reasons != expected_review_reasons:
        raise ValueError(
            "skill-content-audit.json: summary.review_reasons does not match skills"
        )
    detector = report.get("skill_detector")
    detector_fingerprint = (
        detector.get("detector_fingerprint", {}).get("value")
        if isinstance(detector, dict)
        and isinstance(detector.get("detector_fingerprint"), dict)
        else None
    )
    if not isinstance(detector_fingerprint, str) or not _is_sha256(
        detector_fingerprint
    ):
        raise ValueError(
            "skill-content-audit.json: Skill-detector fingerprint is invalid"
        )
    return {
        "skill_detector_fingerprint": detector_fingerprint,
        "audit_gate_status": {
            "selected_gate": gate_status["selected_gate"],
            "authoring": authoring_status["status"],
            "formal_release": formal_status["status"],
        },
        "semantic_disposition_application": {
            "status": application["status"],
            "error": normalized_application_error,
        },
        "content_review_density_candidates": int(
            summary.get(
                "content_review_density_candidates",
                classifications.get("REVIEW_DENSITY", 0),
            )
        ),
        "content_tighten_candidates": int(
            summary.get(
                "content_tighten_candidates",
                classifications.get("TIGHTEN_BODY", 0),
            )
        ),
        "content_blockers": int(
            summary.get("content_blockers", classifications.get("BLOCK", 0))
        ),
        "weak_front_loaded_skills": int(
            review_reasons.get("weak_front_loaded_action", 0)
        ),
        "description_recommended_over_budget_count": int(
            summary.get("description_recommended_over_budget", 0)
        ),
        "description_hard_over_budget_count": int(
            summary.get("description_hard_over_budget", 0)
        ),
        "actionable_duplicate_line_count": len(actionable),
        "review_states": dict(review_states),
        "review_reasons": dict(review_reasons),
    }


@lru_cache(maxsize=1)
def _load_content_auditor() -> ModuleType:
    module_name = "professionalism_regression_content_auditor"
    spec = importlib.util.spec_from_file_location(module_name, CONTENT_AUDITOR)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load {CONTENT_AUDITOR}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _validate_skill_detector_contract(report: dict[str, Any]) -> None:
    """Reject stale Skill classifications or irreproducible review states."""

    auditor = _load_content_auditor()
    expected = auditor._skill_detector_contract()
    if report.get("skill_detector") != expected:
        raise ValueError(
            "skill-content-audit.json: skill_detector is missing or stale; "
            "rerun audit-skill-content.py"
        )
    skills = report.get("skills")
    if not isinstance(skills, list):
        raise ValueError("skill-content-audit.json: skills must be a list")
    required_fields = set(expected["required_skill_fields"])
    finding_fields = set(expected["finding_fields"])
    classifications = set(expected["classification_values"])
    review_states = set(expected["review_state_values"])
    review_reason_order = list(expected["review_reason_values"])
    review_reasons = set(review_reason_order)
    readability = report.get("ai_readability")
    documents = readability.get("documents") if isinstance(readability, dict) else None
    if not isinstance(documents, list):
        raise ValueError(
            "skill-content-audit.json: ai_readability.documents is required to "
            "recompute Skill review states"
        )
    try:
        readability_by_owner = auditor._readability_by_owner(documents)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "skill-content-audit.json: ai_readability.documents cannot be "
            "aggregated by owner"
        ) from exc
    for index, row in enumerate(skills):
        context = f"skill-content-audit.json: skills[{index}]"
        if not isinstance(row, dict):
            raise ValueError(f"{context} must be a mapping")
        missing = sorted(required_fields - set(row))
        if missing:
            raise ValueError(
                f"{context} is missing required detector field(s) {missing}"
            )
        classification = row["classification"]
        if not isinstance(classification, str) or classification not in classifications:
            raise ValueError(f"{context}.classification is not recognized")
        kind = row["kind"]
        if not isinstance(kind, str) or not kind:
            raise ValueError(f"{context}.kind must be a non-empty string")
        name = row["name"]
        if not isinstance(name, str) or not name:
            raise ValueError(f"{context}.name must be a non-empty string")
        line_fields = (
            "line_count",
            "governed_line_count",
            "projection_overhead_lines",
        )
        if any(type(row[field]) is not int or row[field] < 0 for field in line_fields):
            raise ValueError(f"{context} line metrics must be non-negative integers")
        if row["line_count"] != (
            row["governed_line_count"] + row["projection_overhead_lines"]
        ):
            raise ValueError(
                f"{context} physical lines must equal governed lines plus "
                "projection overhead"
            )
        for field in (
            "front_loaded_action_score",
            "generic_control_phrase_count",
            "actionable_repeated_phrase_count",
            "split_candidate_score",
        ):
            if type(row[field]) is not int or row[field] < 0:
                raise ValueError(f"{context}.{field} must be a non-negative integer")
        if (
            not isinstance(row["control_boilerplate_density"], (int, float))
            or isinstance(row["control_boilerplate_density"], bool)
            or row["control_boilerplate_density"] < 0
        ):
            raise ValueError(
                f"{context}.control_boilerplate_density must be non-negative"
            )
        if not isinstance(row["description_findings"], list):
            raise ValueError(f"{context}.description_findings must be a list")
        families = row["control_scaffold_families"]
        if (
            not isinstance(families, list)
            or any(not isinstance(item, str) or not item for item in families)
            or families != sorted(set(families))
        ):
            raise ValueError(
                f"{context}.control_scaffold_families must be a sorted unique string list"
            )
        findings = row["control_scaffold_findings"]
        if not isinstance(findings, list):
            raise ValueError(f"{context}.control_scaffold_findings must be a list")
        for finding_index, finding in enumerate(findings):
            finding_context = (
                f"{context}.control_scaffold_findings[{finding_index}]"
            )
            if not isinstance(finding, dict) or set(finding) != finding_fields:
                raise ValueError(
                    f"{finding_context} must contain exactly {sorted(finding_fields)}"
                )
            if (
                any(
                    not isinstance(finding[field], str) or not finding[field]
                    for field in ("family", "section", "text", "match")
                )
                or type(finding["line"]) is not int
                or finding["line"] < 1
            ):
                raise ValueError(f"{finding_context} has invalid field types")
        expected_families = sorted({finding["family"] for finding in findings})
        if families != expected_families:
            raise ValueError(
                f"{context}.control_scaffold_families does not match findings"
            )
        high_confidence = row["high_confidence_control_scaffold"]
        if type(high_confidence) is not bool:
            raise ValueError(
                f"{context}.high_confidence_control_scaffold must be a boolean"
            )
        if high_confidence != auditor._high_confidence_control_scaffold(
            kind,
            findings,
        ):
            raise ValueError(
                f"{context}.high_confidence_control_scaffold does not match findings"
            )
        review_state = row["review_state"]
        if not isinstance(review_state, str) or review_state not in review_states:
            raise ValueError(f"{context}.review_state is not recognized")
        reasons = row["review_reasons"]
        if (
            not isinstance(reasons, list)
            or any(not isinstance(reason, str) or reason not in review_reasons for reason in reasons)
            or reasons
            != [reason for reason in review_reason_order if reason in set(reasons)]
        ):
            raise ValueError(
                f"{context}.review_reasons must be a closed, ordered, unique list"
            )
        expected_state, expected_reasons = auditor._review_state_and_reasons(
            row,
            readability_by_owner.get(name),
        )
        if review_state != expected_state or reasons != expected_reasons:
            raise ValueError(
                f"{context} review state/reasons do not match current evidence"
            )


def _ai_readability_summary(
    report: dict[str, Any],
    *,
    fresh_ai_readability: dict[str, Any] | None = None,
) -> dict[str, Any]:
    readability = report.get("ai_readability")
    if not isinstance(readability, dict):
        raise ValueError(
            "skill-content-audit.json: ai_readability must be a current mapping"
        )
    expected_fields = {
        "schema_version",
        "contract",
        "source_fingerprint",
        "summary",
        "by_surface",
        "documents",
        "findings",
        "limitations",
    }
    if set(readability) != expected_fields or readability.get("schema_version") != 2:
        raise ValueError(
            "skill-content-audit.json: ai_readability must match current schema 2"
        )
    for key in ("contract", "source_fingerprint", "summary", "by_surface"):
        if not isinstance(readability.get(key), dict):
            raise ValueError(
                f"skill-content-audit.json: ai_readability.{key} must be a mapping"
            )
    for key in ("documents", "findings", "limitations"):
        if not isinstance(readability.get(key), list):
            raise ValueError(
                f"skill-content-audit.json: ai_readability.{key} must be a list"
            )
    fingerprint = readability["source_fingerprint"]
    if (
        set(fingerprint) != {"algorithm", "value", "document_count"}
        or fingerprint.get("algorithm") != "sha256"
        or not isinstance(fingerprint.get("value"), str)
        or not _is_sha256(fingerprint["value"])
        or type(fingerprint.get("document_count")) is not int
        or fingerprint["document_count"] < 0
    ):
        raise ValueError(
            "skill-content-audit.json: ai_readability.source_fingerprint is malformed"
        )
    fresh = (
        _load_content_auditor()._collect_ai_readability()
        if fresh_ai_readability is None
        else fresh_ai_readability
    )
    if readability.get("source_fingerprint") != fresh.get("source_fingerprint"):
        raise ValueError(
            "skill-content-audit.json: stale AI-readability source fingerprint; "
            "rerun audit-skill-content.py"
        )
    if readability != fresh:
        raise ValueError(
            "skill-content-audit.json: tracked AI-readability content does not "
            "match fresh canonical source; rerun audit-skill-content.py"
        )
    summary = readability["summary"]
    count_fields = (
        "documents",
        "advisory_documents",
        "review_as_complex_sentences",
        "tighten_sentences",
        "hard_fail_sentences",
        "compound_bullets",
        "advisory_sentences",
        "blocker_findings",
    )
    counts: dict[str, int] = {}
    for field_name in count_fields:
        value = summary.get(field_name)
        if type(value) is not int or value < 0:
            raise ValueError(
                f"skill-content-audit.json: ai_readability.summary.{field_name} "
                "must be a non-negative integer"
            )
        counts[field_name] = value
    hard_gate_ready = summary.get("hard_gate_ready")
    if type(hard_gate_ready) is not bool:
        raise ValueError(
            "skill-content-audit.json: ai_readability.summary.hard_gate_ready "
            "must be a boolean"
        )
    if counts["documents"] != fingerprint["document_count"]:
        raise ValueError(
            "skill-content-audit.json: AI-readability document count does not "
            "match its fingerprint"
        )
    if counts["advisory_sentences"] != (
        counts["review_as_complex_sentences"] + counts["tighten_sentences"]
    ):
        raise ValueError(
            "skill-content-audit.json: AI-readability advisory count is inconsistent"
        )
    if counts["blocker_findings"] != (
        counts["hard_fail_sentences"] + counts["compound_bullets"]
    ) or hard_gate_ready != (counts["blocker_findings"] == 0):
        raise ValueError(
            "skill-content-audit.json: AI-readability hard gate is inconsistent"
        )
    return {
        "source": "skill-content-audit.json#ai_readability",
        "readiness_scope": "agent-facing-ai-readability",
        "schema_version": readability["schema_version"],
        "source_fingerprint": fingerprint["value"],
        "source_fingerprint_document_count": fingerprint["document_count"],
        "contract": dict(readability["contract"]),
        **counts,
        "hard_gate_ready": hard_gate_ready,
        "by_surface": dict(readability["by_surface"]),
    }


@lru_cache(maxsize=1)
def _load_reference_validator() -> ModuleType:
    module_name = "professionalism_regression_reference_validator"
    spec = importlib.util.spec_from_file_location(module_name, REFERENCE_VALIDATOR)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load {REFERENCE_VALIDATOR}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def _load_root_validator() -> ModuleType:
    module_name = "professionalism_regression_root_validator"
    spec = importlib.util.spec_from_file_location(module_name, ROOT_VALIDATOR)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load {ROOT_VALIDATOR}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def _load_coverage_evaluator() -> ModuleType:
    module_name = "professionalism_regression_coverage_evaluator"
    spec = importlib.util.spec_from_file_location(module_name, COVERAGE_EVALUATOR)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load {COVERAGE_EVALUATOR}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def _load_benchmark_evaluator() -> ModuleType:
    module_name = "professionalism_regression_benchmark_evaluator"
    spec = importlib.util.spec_from_file_location(module_name, BENCHMARK_EVALUATOR)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load {BENCHMARK_EVALUATOR}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _validate_fresh_benchmark_report(report: dict[str, Any]) -> None:
    fresh = _load_benchmark_evaluator().evaluate_benchmarks()
    if report != fresh:
        raise ValueError(
            "professional-benchmarks-report.json is stale or non-canonical; "
            "rerun scripts/eval-professional-benchmarks.py"
        )


def _coverage_gate_summary(
    report: dict[str, Any],
    release_review_config: Path,
) -> dict[str, Any]:
    capability_errors = validate_capability_coverage_matrix()
    if capability_errors:
        raise ValueError("\n".join(capability_errors))
    if report.get("schema_version") != 3:
        raise ValueError("professional-coverage-matrix.json: schema_version must equal 3")
    rows = report.get("rows")
    if not isinstance(rows, list):
        raise ValueError("professional-coverage-matrix.json: rows must be a list")
    expected_row_fields = {
        "name",
        "layer",
        "role_support",
        "trigger_contract",
        "anti_trigger_contract",
        "layer3_candidates",
        "authoring_status",
        "evidence_case_ids",
        "evidence_counts",
        "coverage_states",
        "required_states",
        "unmet_required_states",
        "coverage_gate_status",
    }
    evidence_fields = {
        "positive_route",
        "negative_route",
        "behavior",
        "pressure",
        "release_critical",
        "adversarial_negative_control",
    }
    names: list[str] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != expected_row_fields:
            raise ValueError(
                f"professional-coverage-matrix.json: rows[{index}] fields do not match schema 3"
            )
        if "status" in row:
            raise ValueError(
                "professional-coverage-matrix.json: ambiguous row status is forbidden"
            )
        name = row.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError(
                f"professional-coverage-matrix.json: rows[{index}].name is invalid"
            )
        names.append(name)
        if row.get("authoring_status") not in {"pass", "needs-review", "fail"}:
            raise ValueError(
                f"professional-coverage-matrix.json: {name} has invalid authoring_status"
            )
        evidence = row.get("evidence_case_ids")
        counts = row.get("evidence_counts")
        states = row.get("coverage_states")
        if not isinstance(evidence, dict) or set(evidence) != evidence_fields:
            raise ValueError(
                f"professional-coverage-matrix.json: {name} evidence_case_ids is invalid"
            )
        if not isinstance(counts, dict) or set(counts) != evidence_fields:
            raise ValueError(
                f"professional-coverage-matrix.json: {name} evidence_counts is invalid"
            )
        if not isinstance(states, dict) or set(states) != set(PROFESSIONAL_COVERAGE_STATES):
            raise ValueError(
                f"professional-coverage-matrix.json: {name} coverage_states is invalid"
            )
        for field in evidence_fields:
            case_ids = evidence[field]
            if not isinstance(case_ids, list) or not all(
                isinstance(item, str) and item for item in case_ids
            ):
                raise ValueError(
                    f"professional-coverage-matrix.json: {name}.{field} evidence is invalid"
                )
            if len(case_ids) != len(set(case_ids)) or case_ids != sorted(case_ids):
                raise ValueError(
                    f"professional-coverage-matrix.json: {name}.{field} evidence must be sorted and unique"
                )
            if type(counts[field]) is not int or counts[field] != len(case_ids):
                raise ValueError(
                    f"professional-coverage-matrix.json: {name}.{field} count is inconsistent"
                )
        expected_states = {
            "registered": True,
            "route_covered": bool(evidence["positive_route"]),
            "negative_route_covered": bool(evidence["negative_route"]),
            "behavior_covered": bool(evidence["behavior"]),
            "pressure_covered": bool(evidence["pressure"]),
            "release_critical_covered": bool(evidence["release_critical"]),
        }
        if states != expected_states:
            raise ValueError(
                f"professional-coverage-matrix.json: {name} coverage_states are inconsistent"
            )
        required = row.get("required_states")
        unmet = row.get("unmet_required_states")
        if not isinstance(required, list) or not all(
            item in PROFESSIONAL_COVERAGE_STATES for item in required
        ):
            raise ValueError(
                f"professional-coverage-matrix.json: {name} required_states is invalid"
            )
        if len(required) != len(set(required)):
            raise ValueError(
                f"professional-coverage-matrix.json: {name} repeats required states"
            )
        expected_unmet = [state for state in required if not states[state]]
        if unmet != expected_unmet:
            raise ValueError(
                f"professional-coverage-matrix.json: {name} unmet_required_states is inconsistent"
            )
        expected_gate = (
            "not-required"
            if not required
            else ("pass" if not expected_unmet else "fail")
        )
        if row.get("coverage_gate_status") != expected_gate:
            raise ValueError(
                f"professional-coverage-matrix.json: {name} coverage_gate_status is inconsistent"
            )
    if len(names) != len(set(names)):
        raise ValueError("professional-coverage-matrix.json: row names must be unique")

    try:
        fresh = _load_coverage_evaluator().build_coverage_matrix(
            release_review_config
        )
    except ValidationProblem as exc:
        raise ValueError(str(exc)) from exc
    if report != fresh:
        raise ValueError(
            "professional-coverage-matrix.json: stale or non-canonical coverage evidence; "
            "rerun eval-skill-professionalism.py"
        )
    summary = report.get("gate_summary")
    if not isinstance(summary, dict):
        raise ValueError(
            "professional-coverage-matrix.json: gate_summary must be a mapping"
        )
    failing = sorted(
        row["name"] for row in rows if row["coverage_gate_status"] == "fail"
    )
    return {
        "source": "professional-coverage-matrix.json",
        "policy": report.get("coverage_policy"),
        "required_skill_count": sum(bool(row["required_states"]) for row in rows),
        "pass_count": sum(row["coverage_gate_status"] == "pass" for row in rows),
        "fail_count": len(failing),
        "not_required_count": sum(
            row["coverage_gate_status"] == "not-required" for row in rows
        ),
        "failing_skills": failing,
        "status": "pass" if not failing else "fail",
    }


def _coverage_gate_findings(summary: dict[str, Any]) -> list[Finding]:
    return [
        Finding(
            "professional-coverage-gate",
            name,
            "required deterministic coverage states are incomplete",
        )
        for name in _strings(summary.get("failing_skills"))
    ]


def _reference_content_summary(
    report: dict[str, Any],
    *,
    fresh_reference_content: dict[str, Any] | None = None,
) -> dict[str, Any]:
    reference_content = report.get("reference_content")
    if not isinstance(reference_content, dict):
        raise ValueError(
            "skill-content-audit.json: reference_content must be a current mapping"
        )
    for key in ("summary", "advisories"):
        if not isinstance(reference_content.get(key), dict):
            raise ValueError(
                f"skill-content-audit.json: reference_content.{key} must be a mapping"
            )
    for key in ("references", "missing", "orphans", "template_assets"):
        if not isinstance(reference_content.get(key), list):
            raise ValueError(
                f"skill-content-audit.json: reference_content.{key} must be a list"
            )

    validator = _load_reference_validator()
    preface_counts, preface_errors = validator._effective_preface_contract(
        reference_content
    )
    if preface_errors:
        raise ValueError(
            "skill-content-audit.json: invalid effective preface contract: "
            + "; ".join(preface_errors)
        )
    fresh = (
        validator._fresh_reference_content()
        if fresh_reference_content is None
        else fresh_reference_content
    )
    fresh_counts, fresh_errors = validator._effective_preface_contract(fresh)
    if fresh_errors:
        raise ValueError(
            "fresh Reference source has an invalid effective preface contract: "
            + "; ".join(fresh_errors)
        )
    reported_fingerprint = reference_content["preface_contract"].get(
        "source_fingerprint"
    )
    fresh_fingerprint = fresh["preface_contract"].get("source_fingerprint")
    if reported_fingerprint != fresh_fingerprint:
        raise ValueError(
            "skill-content-audit.json: stale Reference source fingerprint; "
            "rerun audit-skill-content.py"
        )
    if reference_content != fresh:
        raise ValueError(
            "skill-content-audit.json: tracked Reference content does not match "
            "fresh canonical source; rerun audit-skill-content.py"
        )
    _semantic_counts, semantic_errors = validator._semantic_contract(reference_content)
    if semantic_errors:
        raise ValueError(
            "skill-content-audit.json: invalid semantic advisory contract: "
            + "; ".join(semantic_errors)
        )
    counts, _default_errors = validator._evaluate(reference_content, strict=False)
    _strict_counts, strict_errors = validator._evaluate(reference_content, strict=True)
    structural_counts = {
        "missing_indexed_references": counts["missing"],
        "non_template_orphan_references": counts["non_template_orphan"],
        "missing_h1_references": counts["missing_h1"],
        "non_template_multiple_h1_references": counts["non_template_multiple_h1"],
        "non_template_empty_heading_references": counts["non_template_empty_heading"],
        "effective_preface_contract_errors": counts["effective_preface_contract_errors"],
        "effective_preface_conflicts": counts["effective_preface_conflicts"],
        "effective_preface_invalid_declarations": counts["effective_preface_invalid"],
        "missing_effective_reference_types": counts["missing_effective_reference_type"],
        "missing_effective_load_when": counts["missing_effective_load_when"],
        "missing_effective_do_not_load_when": counts[
            "missing_effective_do_not_load_when"
        ],
        "missing_effective_required_by": counts[
            "missing_effective_required_by"
        ],
        "missing_effective_required_output": counts[
            "missing_effective_required_output"
        ],
        "targeted_over_60_lines": counts["targeted_over_60"],
        "mode_contract_over_80_lines": counts["mode_contract_over_80"],
        "decision_items_over_15": counts["decision_items_over_15"],
    }
    structural_strict_ready = not any(
        int(structural_counts[key]) for key in REFERENCE_STRUCTURAL_STRICT_COUNT_FIELDS
    )
    semantic_accounted = counts["semantic_raw_candidates"] == sum(
        (
            counts["semantic_detector_downgraded_candidates"],
            counts["semantic_untriaged_candidates"],
            counts["semantic_rewrite_candidates"],
            counts["semantic_resolved_candidates"],
        )
    )
    semantic_triage_complete = (
        semantic_accounted
        and counts["semantic_untriaged_candidates"] == 0
        and counts["semantic_disposition_errors"] == 0
        and counts["semantic_disposition_configured"]
        == counts["semantic_disposition_applied"]
    )
    return {
        "source": "skill-content-audit.json#reference_content",
        "readiness_scope": "reference-content",
        "targeted_line_limit": validator.TARGETED_LINE_LIMIT,
        "mode_contract_line_limit": validator.MODE_CONTRACT_LINE_LIMIT,
        "decision_item_limit": validator.DECISION_ITEM_LIMIT,
        "effective_preface_schema_version": validator.PREFACE_CONTRACT_SCHEMA_VERSION,
        "strict_ready_basis": "reference-strict-v4",
        "source_fingerprint": reported_fingerprint["value"],
        "source_fingerprint_document_count": reported_fingerprint["document_count"],
        "indexed_references": counts["indexed"],
        "existing_indexed_references": counts["existing"],
        "physical_markdown_references": counts["physical"],
        "missing_indexed_references": counts["missing"],
        "non_template_orphan_references": counts["non_template_orphan"],
        "missing_h1_references": counts["missing_h1"],
        "non_template_multiple_h1_references": counts["non_template_multiple_h1"],
        "non_template_empty_heading_references": counts["non_template_empty_heading"],
        "template_assets": counts["template_assets"],
        "template_multiple_h1_references": counts["template_multiple_h1"],
        "unindexed_template_assets": counts["unindexed_template_assets"],
        "missing_reference_type_prefaces": counts["missing_reference_type"],
        "missing_load_when_prefaces": counts["missing_load_when"],
        "missing_do_not_load_when_prefaces": counts["missing_do_not_load_when"],
        "effective_reference_types": preface_counts["effective_reference_types"],
        "effective_load_when": preface_counts["effective_load_when"],
        "effective_do_not_load_when": preface_counts["effective_do_not_load_when"],
        "effective_required_by": preface_counts["effective_required_by"],
        "effective_required_output": preface_counts["effective_required_output"],
        "missing_effective_reference_types": counts[
            "missing_effective_reference_type"
        ],
        "missing_effective_load_when": counts["missing_effective_load_when"],
        "missing_effective_do_not_load_when": counts[
            "missing_effective_do_not_load_when"
        ],
        "missing_effective_required_by": counts[
            "missing_effective_required_by"
        ],
        "missing_effective_required_output": counts[
            "missing_effective_required_output"
        ],
        "effective_preface_contract_errors": counts[
            "effective_preface_contract_errors"
        ],
        "effective_preface_conflicts": counts["effective_preface_conflicts"],
        "effective_preface_invalid_declarations": counts[
            "effective_preface_invalid"
        ],
        "targeted_over_60_lines": counts["targeted_over_60"],
        "mode_contract_over_80_lines": counts["mode_contract_over_80"],
        "decision_items_over_15": counts["decision_items_over_15"],
        "semantic_schema_version": validator.SEMANTIC_SCHEMA_VERSION,
        "semantic_finding_families": list(validator.SEMANTIC_FINDINGS),
        "semantic_raw_candidates": counts["semantic_raw_candidates"],
        "semantic_detector_downgraded_candidates": counts[
            "semantic_detector_downgraded_candidates"
        ],
        "semantic_untriaged_candidates": counts["semantic_untriaged_candidates"],
        "semantic_rewrite_candidates": counts["semantic_rewrite_candidates"],
        "semantic_resolved_candidates": counts["semantic_resolved_candidates"],
        "semantic_unresolved_candidates": counts["semantic_unresolved_candidates"],
        "unconditional_absolute_p0_p1_unresolved_candidates": counts[
            "unconditional_absolute_p0_p1_unresolved_candidates"
        ],
        "fixed_number_unresolved_candidates": counts[
            "fixed_number_unresolved_candidates"
        ],
        "exact_normalized_duplicate_unresolved_groups": counts[
            "exact_normalized_duplicate_unresolved_groups"
        ],
        "templated_block_unresolved_groups": counts[
            "templated_block_unresolved_groups"
        ],
        "p2_rewrite_advisory_candidates": counts[
            "p2_rewrite_advisory_candidates"
        ],
        "exact_duplicate_occurrences": counts["exact_duplicate_occurrences"],
        "exact_duplicate_tokens": counts["exact_duplicate_tokens"],
        "templated_block_occurrences": counts["templated_block_occurrences"],
        "templated_block_tokens": counts["templated_block_tokens"],
        "semantic_disposition_configured": counts["semantic_disposition_configured"],
        "semantic_disposition_applied": counts["semantic_disposition_applied"],
        "semantic_disposition_errors": counts["semantic_disposition_errors"],
        "structural_strict_ready": structural_strict_ready,
        "semantic_triage_complete": semantic_triage_complete,
        "strict_ready": not strict_errors,
    }


def _root_content_summary(
    report: dict[str, Any],
    *,
    fresh_root_content: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root_content = report.get("root_content")
    if not isinstance(root_content, dict):
        raise ValueError("skill-content-audit.json: root_content must be a current mapping")
    for key in (
        "documents",
        "advisories",
        "summary",
        "semantic_advisories",
        "source_fingerprint",
    ):
        expected_type = list if key == "documents" else dict
        if not isinstance(root_content.get(key), expected_type):
            raise ValueError(
                f"skill-content-audit.json: root_content.{key} must be a "
                f"{'list' if expected_type is list else 'mapping'}"
            )

    validator = _load_root_validator()
    fresh = (
        validator._fresh_root_content()
        if fresh_root_content is None
        else fresh_root_content
    )
    if not isinstance(fresh, dict):
        raise ValueError("fresh Root source must be a mapping")
    reported_fingerprint = root_content.get("source_fingerprint")
    fresh_fingerprint = fresh.get("source_fingerprint")
    if (
        not isinstance(reported_fingerprint, dict)
        or set(reported_fingerprint) != {"algorithm", "document_count", "value"}
        or reported_fingerprint.get("algorithm") != "sha256"
        or not isinstance(reported_fingerprint.get("value"), str)
        or len(reported_fingerprint["value"]) != 64
        or type(reported_fingerprint.get("document_count")) is not int
        or reported_fingerprint["document_count"] < 0
    ):
        raise ValueError(
            "skill-content-audit.json: root_content.source_fingerprint is malformed"
        )
    if reported_fingerprint != fresh_fingerprint:
        raise ValueError(
            "skill-content-audit.json: stale Root source fingerprint; "
            "rerun audit-skill-content.py"
        )
    if root_content != fresh:
        raise ValueError(
            "skill-content-audit.json: tracked Root content does not match "
            "fresh canonical source; rerun audit-skill-content.py"
        )

    counts, default_errors = validator._evaluate(root_content, strict=False)
    if default_errors:
        raise ValueError(
            "skill-content-audit.json: invalid Root content contract: "
            + "; ".join(default_errors)
        )
    _strict_counts, strict_errors = validator._evaluate(root_content, strict=True)
    semantic = root_content["semantic_advisories"]
    semantic_summary = semantic.get("summary")
    if not isinstance(semantic_summary, dict):
        raise ValueError(
            "skill-content-audit.json: root_content.semantic_advisories.summary "
            "must be a mapping"
        )
    disposition_contract = semantic.get("disposition_contract")
    if not isinstance(disposition_contract, dict):
        raise ValueError(
            "skill-content-audit.json: root_content semantic disposition contract "
            "must be a mapping"
        )
    structural_strict_ready = not any(
        int(counts.get(key, 0)) for key in ROOT_STRUCTURAL_STRICT_COUNT_FIELDS
    )
    semantic_raw = int(semantic_summary.get("raw_candidates", 0))
    semantic_untriaged = int(semantic_summary.get("untriaged_candidates", 0))
    semantic_rewrite = int(semantic_summary.get("rewrite_candidates", 0))
    semantic_resolved = int(semantic_summary.get("resolved_candidates", 0))
    semantic_triage_complete = (
        semantic_raw == semantic_untriaged + semantic_rewrite + semantic_resolved
        and semantic_untriaged == 0
        and counts["disposition_errors"] == 0
        and counts["dispositions_configured"] == counts["dispositions_applied"]
    )
    return {
        "source": "skill-content-audit.json#root_content",
        "readiness_scope": "agent-facing-root-content",
        "strict_ready_basis": "root-strict-v5",
        "source_fingerprint": reported_fingerprint["value"],
        "source_fingerprint_document_count": reported_fingerprint["document_count"],
        "agent_facing_root_documents": counts["documents"],
        "foundation_compact_capabilities": counts[
            "foundation_compact_capabilities"
        ],
        "foundation_complex_capabilities": counts[
            "foundation_complex_capabilities"
        ],
        "foundation_over_target_words": counts["foundation_over_target_words"],
        "foundation_compact_over_target_words": counts[
            "foundation_compact_over_target_words"
        ],
        "foundation_complex_over_target_words": counts[
            "foundation_complex_over_target_words"
        ],
        "foundation_over_hard_words": counts["foundation_over_hard_words"],
        "foundation_compact_over_hard_words": counts[
            "foundation_compact_over_hard_words"
        ],
        "foundation_complex_over_hard_words": counts[
            "foundation_complex_over_hard_words"
        ],
        "foundation_over_hard_tokens": counts["foundation_over_hard_tokens"],
        "foundation_rule_count_outside_target": counts[
            "foundation_rule_count_outside_target"
        ],
        "foundation_rules_over_sentence_limit": counts[
            "foundation_rules_over_sentence_limit"
        ],
        "foundation_rules_without_decision_semantics": counts[
            "foundation_rules_without_decision_semantics"
        ],
        "foundation_long_prose_line": counts["foundation_long_prose_line"],
        "foundation_tutorial_density": counts["foundation_tutorial_density"],
        "foundation_low_decision_density": counts[
            "foundation_low_decision_density"
        ],
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
        "semantic_schema_version": semantic.get("schema_version"),
        "semantic_finding_families": list(semantic.get("finding_families") or []),
        "semantic_raw_candidates": semantic_raw,
        "semantic_untriaged_candidates": semantic_untriaged,
        "semantic_rewrite_candidates": semantic_rewrite,
        "semantic_resolved_candidates": semantic_resolved,
        "semantic_unresolved_candidates": counts["semantic_unresolved"],
        "semantic_p0_p1_unresolved_candidates": counts[
            "semantic_p0_p1_unresolved"
        ],
        "semantic_fixed_number_unresolved_candidates": counts[
            "semantic_fixed_number_unresolved"
        ],
        "semantic_disposition_configured": counts["dispositions_configured"],
        "semantic_disposition_applied": counts["dispositions_applied"],
        "semantic_disposition_errors": counts["disposition_errors"],
        "structural_strict_ready": structural_strict_ready,
        "semantic_triage_complete": semantic_triage_complete,
        "strict_ready": not strict_errors,
    }


def _required_content_disposition_rows(
    content_skills: object,
) -> tuple[list[dict[str, str]], int]:
    if content_skills is None:
        return [], 0
    if not isinstance(content_skills, list):
        raise ValueError("skill-content-audit.json: skills must be a list")
    required: list[dict[str, str]] = []
    blocker_count = 0
    for index, row in enumerate(content_skills):
        if not isinstance(row, dict):
            raise ValueError(
                f"skill-content-audit.json: skills[{index}] must be a mapping"
            )
        classification = row.get("classification")
        if classification == "BLOCK":
            blocker_count += 1
        if classification not in {"REVIEW_DENSITY", "TIGHTEN_BODY"}:
            continue
        path = row.get("path")
        if not isinstance(path, str) or not path.strip():
            raise ValueError(
                f"skill-content-audit.json: skills[{index}].path must be non-blank"
            )
        required.append({"path": path, "classification": classification})
    required.sort(key=lambda item: item["path"])
    paths = [item["path"] for item in required]
    if len(paths) != len(set(paths)):
        raise ValueError(
            "skill-content-audit.json: disposition-required Skill paths must be unique"
        )
    return required, blocker_count


def _required_readability_disposition_rows(
    readability_content: object,
) -> tuple[list[dict[str, str]], int]:
    if readability_content is None:
        return [], 0
    if not isinstance(readability_content, dict):
        raise ValueError("skill-content-audit.json: ai_readability must be a mapping")
    documents = readability_content.get("documents")
    summary = readability_content.get("summary")
    if not isinstance(documents, list) or not isinstance(summary, dict):
        raise ValueError(
            "skill-content-audit.json: ai_readability documents and summary are required"
        )
    required: list[dict[str, str]] = []
    for index, row in enumerate(documents):
        if not isinstance(row, dict):
            raise ValueError(
                f"skill-content-audit.json: ai_readability.documents[{index}] "
                "must be a mapping"
            )
        document_id = row.get("document_id")
        highest_band = row.get("highest_advisory_band")
        if not isinstance(document_id, str) or not document_id.strip():
            raise ValueError(
                f"skill-content-audit.json: ai_readability.documents[{index}] "
                "needs a non-blank document_id"
            )
        if highest_band not in {None, "review-as-complex", "tighten"}:
            raise ValueError(
                f"skill-content-audit.json: ai_readability.documents[{index}] "
                "has an invalid highest advisory band"
            )
        if highest_band is not None:
            required.append(
                {"document_id": document_id, "highest_band": highest_band}
            )
    required.sort(key=lambda item: item["document_id"])
    document_ids = [item["document_id"] for item in required]
    if len(document_ids) != len(set(document_ids)):
        raise ValueError(
            "skill-content-audit.json: advisory readability document IDs must be unique"
        )
    advisory_count = summary.get("advisory_documents")
    if type(advisory_count) is not int or advisory_count != len(required):
        raise ValueError(
            "skill-content-audit.json: advisory readability document count is inconsistent"
        )
    blocker_count = summary.get("blocker_findings")
    if type(blocker_count) is not int or blocker_count < 0:
        raise ValueError(
            "skill-content-audit.json: readability blocker count must be non-negative"
        )
    return required, blocker_count


def _required_actionability_disposition_rows(
    content_skills: object,
) -> list[dict[str, Any]]:
    """Return every audit Skill that requires an actionability disposition."""

    if content_skills is None:
        return []
    if not isinstance(content_skills, list):
        raise ValueError("skill-content-audit.json: skills must be a list")
    required: list[dict[str, Any]] = []
    for index, row in enumerate(content_skills):
        if not isinstance(row, dict):
            raise ValueError(
                f"skill-content-audit.json: skills[{index}] must be a mapping"
            )
        review_reasons = row.get("review_reasons")
        if review_reasons is None:
            continue
        if not isinstance(review_reasons, list):
            raise ValueError(
                f"skill-content-audit.json: skills[{index}].review_reasons must be a list"
            )
        actionability_model = row.get("actionability_model")
        actionability_applicable = row.get("actionability_applicable")
        if not isinstance(actionability_model, str) or not actionability_model:
            raise ValueError(
                f"skill-content-audit.json: skills[{index}].actionability_model "
                "must be non-blank"
            )
        if type(actionability_applicable) is not bool:
            raise ValueError(
                f"skill-content-audit.json: skills[{index}].actionability_applicable "
                "must be boolean"
            )
        if (
            ("weak_front_loaded_action" in review_reasons)
            != actionability_applicable
        ):
            raise ValueError(
                f"skill-content-audit.json: skills[{index}] actionability "
                "applicability disagrees with review reason"
            )
        if not actionability_applicable:
            continue
        path = row.get("path")
        skill_id = row.get("name")
        score = row.get("front_loaded_action_score")
        if not isinstance(path, str) or not path.strip():
            raise ValueError(
                f"skill-content-audit.json: skills[{index}].path must be non-blank"
            )
        if not isinstance(skill_id, str) or not skill_id.strip():
            raise ValueError(
                f"skill-content-audit.json: skills[{index}].name must be non-blank"
            )
        if type(score) is not int or score < 0:
            raise ValueError(
                "skill-content-audit.json: "
                f"skills[{index}].front_loaded_action_score must be non-negative"
            )
        required.append(
            {
                "target_id": expert_panel._actionability_target_id(path),
                "skill_id": skill_id,
                "path": path,
                "front_loaded_action_score": score,
            }
        )
    required.sort(key=lambda item: item["target_id"])
    target_ids = [item["target_id"] for item in required]
    if len(target_ids) != len(set(target_ids)):
        raise ValueError(
            "skill-content-audit.json: actionability target IDs must be unique"
        )
    return required


def _readability_packet_actionability_projection(
    content_audit: dict[str, Any],
) -> dict[str, Any]:
    """Return only target-local actionability authority for Readability packets."""

    if not isinstance(content_audit, dict):
        raise ValueError("skill-content-audit.json must be a mapping")
    required = _required_actionability_disposition_rows(
        content_audit.get("skills")
    )
    target_count = len(required)
    summary = content_audit.get("summary")
    review_reasons = summary.get("review_reasons") if isinstance(
        summary, dict
    ) else None
    reason_count = review_reasons.get(
        "weak_front_loaded_action", 0
    ) if isinstance(review_reasons, dict) else None
    applicable_count = summary.get(
        "actionability_applicable_items"
    ) if isinstance(summary, dict) else None
    all_items_count = summary.get(
        "weak_front_loaded_action_all_items"
    ) if isinstance(summary, dict) else None
    if any(
        type(value) is not int or value != target_count
        for value in (reason_count, applicable_count, all_items_count)
    ):
        raise ValueError(
            "skill-content-audit.json: actionability summary does not match "
            "the required disposition rows"
        )
    return {
        "weak_front_loaded_skills": target_count,
        "required_targets": required,
    }


def _expert_panel_content_review(
    path: Path,
    *,
    config_bytes: bytes,
    config_fingerprint: str,
    outer_schema: int,
    attestation: dict[str, Any],
    reference_fingerprint: str,
    root_fingerprint: str,
    ai_readability_fingerprint: str | None,
    content_skills: object,
    readability_content: object,
    required_dispositions: list[dict[str, str]],
    required_readability_dispositions: list[dict[str, str]],
    content_blocker_count: int,
    readability_blocker_count: int,
    evaluation_date: date | None,
    content_audit: object = None,
) -> dict[str, Any]:
    """Validate schema 5 three-expert majority evidence and release binding."""

    source = f"{_rel(path)}#expert_content_review_attestation"
    if outer_schema != 5 or attestation.get("schema_version") != 5:
        raise ValueError(
            f"{_rel(path)}: expert panel review requires matching schema 5"
        )
    if set(attestation) != EXPERT_PANEL_ATTESTATION_FIELDS:
        raise ValueError(
            f"{_rel(path)}: expert panel attestation fields must exactly match schema 5"
        )
    if attestation.get("scope") != "agent-facing-content":
        raise ValueError(
            f"{_rel(path)}: expert panel scope must equal 'agent-facing-content'"
        )
    if attestation.get("decision_method") != expert_panel.DECISION_METHOD:
        raise ValueError(
            f"{_rel(path)}: expert panel decision_method must equal "
            f"{expert_panel.DECISION_METHOD}"
        )
    if content_blocker_count:
        raise ValueError(
            f"{_rel(path)}: expert panel cannot override "
            f"{content_blocker_count} content blocker(s)"
        )
    if readability_blocker_count:
        raise ValueError(
            f"{_rel(path)}: expert panel cannot override "
            f"{readability_blocker_count} readability blocker(s)"
        )
    if not isinstance(ai_readability_fingerprint, str) or not _is_sha256(
        ai_readability_fingerprint
    ):
        raise ValueError(f"{_rel(path)}: current AI-readability fingerprint is required")
    fingerprints = attestation.get("source_fingerprints")
    expected_fingerprints = {
        "reference_content": reference_fingerprint,
        "root_content": root_fingerprint,
        "ai_readability": ai_readability_fingerprint,
    }
    if fingerprints != expected_fingerprints:
        raise ValueError(f"{_rel(path)}: stale expert panel source fingerprints")

    limitations = attestation.get("limitations")
    if not isinstance(limitations, list) or not limitations or not all(
        isinstance(item, str) and item.strip() for item in limitations
    ):
        raise ValueError(
            f"{_rel(path)}: expert panel limitations must be a non-empty string list"
        )
    record_ref = attestation.get("panel_record")
    if not isinstance(record_ref, dict) or set(record_ref) != EXPERT_PANEL_RECORD_FIELDS:
        raise ValueError(f"{_rel(path)}: expert panel_record must contain path and sha256")
    record_value = record_ref.get("path")
    record_sha256 = record_ref.get("sha256")
    if not isinstance(record_value, str) or not record_value.strip():
        raise ValueError(f"{_rel(path)}: expert panel_record.path must be non-blank")
    if not isinstance(record_sha256, str) or not _is_sha256(record_sha256):
        raise ValueError(f"{_rel(path)}: expert panel_record.sha256 must be lowercase sha256")
    relative_record = Path(record_value)
    if (
        relative_record.is_absolute()
        or relative_record.as_posix() != record_value
        or ".." in relative_record.parts
    ):
        raise ValueError(
            f"{_rel(path)}: expert panel_record.path must be canonical repository-relative"
        )
    record_path = (ROOT / relative_record).resolve()
    try:
        record_path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"{_rel(path)}: expert panel_record escapes repository") from exc
    if not record_path.is_file():
        raise ValueError(f"{_rel(path)}: expert panel_record is missing")
    current_record_sha256 = hashlib.sha256(record_path.read_bytes()).hexdigest()
    if current_record_sha256 != record_sha256:
        raise ValueError(f"{_rel(path)}: expert panel_record sha256 is stale")
    try:
        record_value_data = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{_rel(path)}: expert panel_record is not valid JSON") from exc
    if not isinstance(record_value_data, dict):
        raise ValueError(f"{_rel(path)}: expert panel_record must be a JSON object")
    try:
        record = expert_panel.validate_decision_record(
            record_value_data,
            record_path=record_path,
        )
    except expert_panel.PanelReviewError as exc:
        raise ValueError(f"{_rel(path)}: invalid expert panel_record: {exc}") from exc
    if record.get("source_fingerprints") != expected_fingerprints:
        raise ValueError(f"{_rel(path)}: expert panel decision fingerprints are stale")
    if not isinstance(content_skills, list) or not isinstance(readability_content, dict):
        raise ValueError(f"{_rel(path)}: current panel target sources are required")
    packet_ref = record.get("packet")
    if not isinstance(packet_ref, dict):
        raise ValueError(f"{_rel(path)}: expert panel packet reference is invalid")
    packet_path = ROOT / str(packet_ref.get("path"))
    try:
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{_rel(path)}: expert panel packet is unreadable") from exc
    if not isinstance(packet, dict):
        raise ValueError(f"{_rel(path)}: expert panel packet must be a JSON object")
    if packet.get("schema_version") == expert_panel.SCHEMA_VERSION:
        try:
            expert_panel.validate_packet(
                packet,
                validation_mode=expert_panel.VALIDATION_MODE_HISTORICAL,
            )
        except expert_panel.PanelReviewError as exc:
            raise ValueError(
                f"{_rel(path)}: legacy expert panel packet is invalid: {exc}"
            ) from exc
        legacy_content_targets = {
            (row.get("path"), row.get("classification"))
            for row in packet.get("content_targets", [])
            if isinstance(row, dict)
        }
        expected_legacy_content_targets = {
            (row["path"], row["classification"])
            for row in required_dispositions
        }
        legacy_readability_targets = {
            (row.get("document_id"), row.get("highest_band"))
            for row in packet.get("readability_targets", [])
            if isinstance(row, dict)
        }
        expected_legacy_readability_targets = {
            (row["document_id"], row["highest_band"])
            for row in required_readability_dispositions
        }
        if (
            packet.get("review_id") != record["review_id"]
            or packet.get("source_fingerprints") != expected_fingerprints
            or legacy_content_targets != expected_legacy_content_targets
            or legacy_readability_targets
            != expected_legacy_readability_targets
        ):
            raise ValueError(
                f"{_rel(path)}: legacy expert panel packet is stale against "
                "current source authority"
            )
    else:
        if (
            not isinstance(content_audit, dict)
            or content_audit.get("skills") != content_skills
            or content_audit.get("ai_readability") != readability_content
        ):
            raise ValueError(
                f"{_rel(path)}: current schema-2 packet requires its complete "
                "bound content audit"
            )
        root_content = content_audit.get("root_content")
        reference_content = content_audit.get("reference_content")
        reference_preface = (
            reference_content.get("preface_contract")
            if isinstance(reference_content, dict)
            else None
        )
        root_source = (
            root_content.get("source_fingerprint")
            if isinstance(root_content, dict)
            else None
        )
        reference_source = (
            reference_preface.get("source_fingerprint")
            if isinstance(reference_preface, dict)
            else None
        )
        root_document_count = (
            root_source.get("document_count")
            if isinstance(root_source, dict)
            else None
        )
        reference_document_count = (
            reference_source.get("document_count")
            if isinstance(reference_source, dict)
            else None
        )
        try:
            expected_packet = expert_panel.prepare_packet(
                audit=content_audit,
                review_id=record["review_id"],
                created_on=packet["created_on"],
            )
        except expert_panel.PanelReviewError as exc:
            raise ValueError(
                f"{_rel(path)}: cannot recompute expert panel packet: {exc}"
            ) from exc
        if packet != expected_packet:
            raise ValueError(
                f"{_rel(path)}: expert panel packet is not current canonical input"
            )

    expected_content = {
        item["path"]: item["classification"] for item in required_dispositions
    }
    normalized_dispositions: list[dict[str, str]] = []
    actual_content: dict[str, str] = {}
    for index, item in enumerate(record.get("content_decisions", [])):
        if not isinstance(item, dict):
            raise ValueError(f"{_rel(path)}: panel content decision {index} is invalid")
        decision_path = item.get("path")
        classification = item.get("classification")
        disposition = item.get("winning_disposition")
        if disposition not in EXPERT_CONTENT_DISPOSITIONS:
            raise ValueError(f"{_rel(path)}: panel content disposition is invalid")
        if not isinstance(decision_path, str) or decision_path in actual_content:
            raise ValueError(f"{_rel(path)}: panel content decision identity is invalid")
        actual_content[decision_path] = classification
        rationales = item.get("winning_rationales")
        if not isinstance(rationales, list) or len(rationales) < 2:
            raise ValueError(f"{_rel(path)}: panel content majority rationale is incomplete")
        normalized_dispositions.append(
            {
                "path": decision_path,
                "classification": classification,
                "disposition": disposition,
                "rationale": "Majority decision: " + " ".join(
                    str(row.get("rationale")) for row in rationales
                ),
            }
        )
    if actual_content != expected_content:
        raise ValueError(f"{_rel(path)}: panel content decisions do not match current audit")

    expected_readability = {
        item["document_id"]: item["highest_band"]
        for item in required_readability_dispositions
    }
    normalized_readability_dispositions: list[dict[str, str]] = []
    actual_readability: dict[str, str] = {}
    for index, item in enumerate(record.get("readability_decisions", [])):
        if not isinstance(item, dict):
            raise ValueError(
                f"{_rel(path)}: panel readability decision {index} is invalid"
            )
        document_id = item.get("document_id")
        highest_band = item.get("highest_band")
        disposition = item.get("winning_disposition")
        if disposition not in EXPERT_READABILITY_DISPOSITIONS:
            raise ValueError(f"{_rel(path)}: panel readability disposition is invalid")
        if not isinstance(document_id, str) or document_id in actual_readability:
            raise ValueError(
                f"{_rel(path)}: panel readability decision identity is invalid"
            )
        actual_readability[document_id] = highest_band
        rationales = item.get("winning_rationales")
        if not isinstance(rationales, list) or len(rationales) < 2:
            raise ValueError(
                f"{_rel(path)}: panel readability majority rationale is incomplete"
            )
        normalized_readability_dispositions.append(
            {
                "document_id": document_id,
                "highest_band": highest_band,
                "disposition": disposition,
                "rationale": "Majority decision: " + " ".join(
                    str(row.get("rationale")) for row in rationales
                ),
            }
        )
    if actual_readability != expected_readability:
        raise ValueError(
            f"{_rel(path)}: panel readability decisions do not match current audit"
        )

    evidence = [{"path": record_value, "sha256": record_sha256}]
    evidence.append(
        {"path": record["packet"]["path"], "sha256": record["packet"]["sha256"]}
    )
    for voter in record["voters"]:
        ballot_path = (record_path.parent / voter["ballot_path"]).relative_to(ROOT)
        evidence.append(
            {
                "path": ballot_path.as_posix(),
                "sha256": voter["ballot_sha256"],
            }
        )
    evidence.sort(key=lambda item: item["path"])
    storage_error: str | None = None
    try:
        _require_default_release_review_config(path, current_bytes=config_bytes)
        for item in evidence:
            _validate_expert_evidence(item)
    except ValueError as exc:
        storage_error = str(exc)
    complete = storage_error is None
    status = "panel-majority-current" if complete else "panel-majority-pending-checkin"
    attested_on = _validated_iso_date(
        record.get("decided_on"),
        label=f"{_rel(path)}: expert panel decided_on",
        evaluation_date=evaluation_date,
    )
    normalized_limitations = list(limitations)
    if storage_error is not None:
        normalized_limitations.append(
            "Panel decision is complete but formal release binding is pending: "
            + storage_error
        )
    return {
        "scope": "agent-facing-content",
        "expert_content_review_complete": complete,
        "panel_decision_complete": True,
        "storage_current": complete,
        "decision_method": expert_panel.DECISION_METHOD,
        "panel_review_id": record["review_id"],
        "panel_size": len(record["voters"]),
        "attestation_status": status,
        "attestation_source": source,
        "attestation_schema_version": 5,
        "attestation_config_fingerprint": config_fingerprint,
        "source_fingerprints": dict(fingerprints),
        "attested_by": f"expert-panel:{record['review_id']}",
        "attested_on": attested_on,
        "evidence": evidence,
        "content_dispositions": normalized_dispositions,
        "readability_dispositions": normalized_readability_dispositions,
        "required_content_disposition_count": len(required_dispositions),
        "applied_content_disposition_count": len(normalized_dispositions),
        "content_blocker_count": content_blocker_count,
        "required_readability_disposition_count": len(
            required_readability_dispositions
        ),
        "applied_readability_disposition_count": len(
            normalized_readability_dispositions
        ),
        "readability_blocker_count": readability_blocker_count,
        "limitations": normalized_limitations,
    }


def _expert_content_review(
    path: Path,
    *,
    reference_fingerprint: str,
    root_fingerprint: str,
    ai_readability_fingerprint: str | None = None,
    content_skills: object = None,
    readability_content: object = None,
    evaluation_date: date | None = None,
    content_audit: object = None,
) -> dict[str, Any]:
    source = f"{_rel(path)}#expert_content_review_attestation"
    try:
        config_bytes = path.read_bytes()
        data = load_yaml_file(path)
    except (OSError, ValidationProblem) as exc:
        raise ValueError(str(exc)) from exc
    config_fingerprint = hashlib.sha256(config_bytes).hexdigest()
    if not isinstance(data, dict):
        raise ValueError(f"{_rel(path)}: release review config must be a mapping")
    schema_version = data.get("schema_version")
    expected_common = {"schema_version", "review_owner", "reviewed_at", "decisions"}
    expected = (
        expected_common
        if schema_version == 1
        else expected_common | {"expert_content_review_attestation"}
    )
    if schema_version not in {1, 2, 3, 4, 5}:
        raise ValueError(
            f"{_rel(path)}: schema_version must equal 1, 2, 3, 4, or 5"
        )
    if set(data) != expected:
        raise ValueError(
            f"{_rel(path)}: schema {schema_version} fields must exactly match "
            + ", ".join(sorted(expected))
        )
    review_owner = data.get("review_owner")
    if not isinstance(review_owner, str) or not review_owner.strip():
        raise ValueError(f"{_rel(path)}: review_owner must be a non-blank string")
    _validated_iso_date(
        data.get("reviewed_at"),
        label=f"{_rel(path)}: reviewed_at",
        evaluation_date=evaluation_date,
    )
    if not isinstance(data.get("decisions"), list):
        raise ValueError(f"{_rel(path)}: decisions must be a list")
    if schema_version == 1:
        return {
            "scope": "agent-facing-content",
            "expert_content_review_complete": False,
            "panel_decision_complete": False,
            "storage_current": False,
            "decision_method": "legacy-maintainer-attestation",
            "panel_review_id": None,
            "panel_size": 0,
            "attestation_status": "legacy-schema-default-false",
            "attestation_source": source,
            "attestation_schema_version": None,
            "attestation_config_fingerprint": config_fingerprint,
            "source_fingerprints": {
                "reference_content": None,
                "root_content": None,
                "ai_readability": None,
            },
            "attested_by": None,
            "attested_on": None,
            "evidence": [],
            "content_dispositions": [],
            "readability_dispositions": [],
            "required_content_disposition_count": 0,
            "applied_content_disposition_count": 0,
            "content_blocker_count": 0,
            "required_readability_disposition_count": 0,
            "applied_readability_disposition_count": 0,
            "readability_blocker_count": 0,
            "limitations": [
                "Release review schema 1 carries no expert content attestation."
            ],
        }

    required_dispositions, content_blocker_count = (
        _required_content_disposition_rows(content_skills)
    )
    required_readability_dispositions, readability_blocker_count = (
        _required_readability_disposition_rows(readability_content)
    )
    attestation = data.get("expert_content_review_attestation")
    if not isinstance(attestation, dict):
        raise ValueError(
            f"{_rel(path)}: expert_content_review_attestation must be a mapping"
        )
    attestation_schema = attestation.get("schema_version")
    if attestation_schema == 5:
        return _expert_panel_content_review(
            path,
            config_bytes=config_bytes,
            config_fingerprint=config_fingerprint,
            outer_schema=schema_version,
            attestation=attestation,
            reference_fingerprint=reference_fingerprint,
            root_fingerprint=root_fingerprint,
            ai_readability_fingerprint=ai_readability_fingerprint,
            content_skills=content_skills,
            readability_content=readability_content,
            required_dispositions=required_dispositions,
            required_readability_dispositions=required_readability_dispositions,
            content_blocker_count=content_blocker_count,
            readability_blocker_count=readability_blocker_count,
            evaluation_date=evaluation_date,
            content_audit=content_audit,
        )
    expected_attestation_fields = {
        2: EXPERT_ATTESTATION_FIELDS
        - {"content_dispositions", "readability_dispositions"},
        3: EXPERT_ATTESTATION_FIELDS - {"readability_dispositions"},
        4: EXPERT_ATTESTATION_FIELDS,
    }.get(attestation_schema, set())
    if set(attestation) != expected_attestation_fields:
        raise ValueError(
            f"{_rel(path)}: expert_content_review_attestation fields must exactly "
            f"match schema {attestation_schema}"
        )
    if attestation_schema not in {2, 3, 4} or attestation_schema != schema_version:
        raise ValueError(
            f"{_rel(path)}: expert_content_review_attestation.schema_version "
            "must equal outer schema_version and be 2, 3, 4, or 5"
        )
    if attestation.get("scope") != "agent-facing-content":
        raise ValueError(
            f"{_rel(path)}: expert content review scope must equal "
            "'agent-facing-content'"
        )
    complete = attestation.get("complete")
    if type(complete) is not bool:
        raise ValueError(
            f"{_rel(path)}: expert_content_review_attestation.complete must be a boolean"
        )
    fingerprints = attestation.get("source_fingerprints")
    expected_fingerprint_fields = (
        EXPERT_SOURCE_FINGERPRINT_FIELDS
        if attestation_schema == 4
        else EXPERT_SOURCE_FINGERPRINT_FIELDS - {"ai_readability"}
    )
    if not isinstance(fingerprints, dict) or set(fingerprints) != expected_fingerprint_fields:
        raise ValueError(
            f"{_rel(path)}: expert source_fingerprints must contain exactly "
            + ", ".join(sorted(expected_fingerprint_fields))
        )
    evidence = attestation.get("evidence")
    if not isinstance(evidence, list):
        raise ValueError(
            f"{_rel(path)}: expert content review evidence must be a list of "
            "path and sha256 mappings"
        )
    normalized_evidence: list[dict[str, str]] = []
    evidence_paths: list[str] = []
    for index, item in enumerate(evidence):
        label = f"{_rel(path)}: expert content review evidence[{index}]"
        if not isinstance(item, dict) or set(item) != EXPERT_EVIDENCE_FIELDS:
            raise ValueError(f"{label} must contain exactly path and sha256")
        evidence_path = item.get("path")
        evidence_sha256 = item.get("sha256")
        if not isinstance(evidence_path, str) or not evidence_path.strip():
            raise ValueError(f"{label}.path must be a non-blank string")
        if not isinstance(evidence_sha256, str) or not _is_sha256(evidence_sha256):
            raise ValueError(f"{label}.sha256 must be lowercase sha256")
        evidence_paths.append(evidence_path)
        normalized_evidence.append(
            {"path": evidence_path, "sha256": evidence_sha256}
        )
    if evidence_paths != sorted(evidence_paths) or len(evidence_paths) != len(
        set(evidence_paths)
    ):
        raise ValueError(
            f"{_rel(path)}: expert content review evidence paths must be sorted "
            "and unique"
        )
    raw_dispositions = (
        attestation.get("content_dispositions", [])
        if attestation_schema in {3, 4}
        else []
    )
    if not isinstance(raw_dispositions, list):
        raise ValueError(
            f"{_rel(path)}: expert content_dispositions must be a list"
        )
    normalized_dispositions: list[dict[str, str]] = []
    for index, item in enumerate(raw_dispositions):
        label = f"{_rel(path)}: expert content_dispositions[{index}]"
        if not isinstance(item, dict) or set(item) != EXPERT_CONTENT_DISPOSITION_FIELDS:
            raise ValueError(
                f"{label} must contain exactly path, classification, disposition, and rationale"
            )
        disposition_path = item.get("path")
        classification = item.get("classification")
        disposition = item.get("disposition")
        rationale = item.get("rationale")
        if not isinstance(disposition_path, str) or not disposition_path.strip():
            raise ValueError(f"{label}.path must be a non-blank string")
        if classification not in {"REVIEW_DENSITY", "TIGHTEN_BODY"}:
            raise ValueError(f"{label}.classification is invalid")
        if disposition not in EXPERT_CONTENT_DISPOSITIONS:
            raise ValueError(f"{label}.disposition is invalid")
        if not isinstance(rationale, str) or len(rationale.split()) < 8:
            raise ValueError(
                f"{label}.rationale must state a concrete expert decision"
            )
        normalized_dispositions.append(
            {
                "path": disposition_path,
                "classification": classification,
                "disposition": disposition,
                "rationale": rationale,
            }
        )
    disposition_paths = [item["path"] for item in normalized_dispositions]
    if disposition_paths != sorted(disposition_paths) or len(disposition_paths) != len(
        set(disposition_paths)
    ):
        raise ValueError(
            f"{_rel(path)}: expert content disposition paths must be sorted and unique"
        )
    raw_readability_dispositions = (
        attestation.get("readability_dispositions", [])
        if attestation_schema == 4
        else []
    )
    if not isinstance(raw_readability_dispositions, list):
        raise ValueError(
            f"{_rel(path)}: expert readability_dispositions must be a list"
        )
    normalized_readability_dispositions: list[dict[str, str]] = []
    for index, item in enumerate(raw_readability_dispositions):
        label = f"{_rel(path)}: expert readability_dispositions[{index}]"
        if (
            not isinstance(item, dict)
            or set(item) != EXPERT_READABILITY_DISPOSITION_FIELDS
        ):
            raise ValueError(
                f"{label} must contain exactly document_id, highest_band, "
                "disposition, and rationale"
            )
        document_id = item.get("document_id")
        highest_band = item.get("highest_band")
        disposition = item.get("disposition")
        rationale = item.get("rationale")
        if not isinstance(document_id, str) or not document_id.strip():
            raise ValueError(f"{label}.document_id must be a non-blank string")
        if highest_band not in {"review-as-complex", "tighten"}:
            raise ValueError(f"{label}.highest_band is invalid")
        if disposition not in EXPERT_READABILITY_DISPOSITIONS:
            raise ValueError(f"{label}.disposition is invalid")
        if not isinstance(rationale, str) or len(rationale.split()) < 8:
            raise ValueError(
                f"{label}.rationale must state a concrete expert decision"
            )
        normalized_readability_dispositions.append(
            {
                "document_id": document_id,
                "highest_band": highest_band,
                "disposition": disposition,
                "rationale": rationale,
            }
        )
    readability_document_ids = [
        item["document_id"] for item in normalized_readability_dispositions
    ]
    if readability_document_ids != sorted(readability_document_ids) or len(
        readability_document_ids
    ) != len(set(readability_document_ids)):
        raise ValueError(
            f"{_rel(path)}: expert readability disposition document IDs must be "
            "sorted and unique"
        )
    limitations = attestation.get("limitations")
    if not isinstance(limitations, list) or not limitations or not all(
        isinstance(item, str) and item.strip() for item in limitations
    ):
        raise ValueError(
            f"{_rel(path)}: expert content review limitations must be a non-empty "
            "list of non-blank strings"
        )
    attested_by = attestation.get("attested_by")
    attested_on = attestation.get("attested_on")
    if not complete:
        if fingerprints != {
            field_name: None for field_name in expected_fingerprint_fields
        }:
            raise ValueError(
                f"{_rel(path)}: incomplete expert review must use null source fingerprints"
            )
        if attested_by is not None or attested_on is not None or evidence:
            raise ValueError(
                f"{_rel(path)}: incomplete expert review cannot carry attester, date, or evidence"
            )
        if normalized_dispositions:
            raise ValueError(
                f"{_rel(path)}: incomplete expert review cannot carry content dispositions"
            )
        if normalized_readability_dispositions:
            raise ValueError(
                f"{_rel(path)}: incomplete expert review cannot carry readability dispositions"
            )
        status = "explicitly-incomplete"
    else:
        if attestation_schema != 4:
            raise ValueError(
                f"{_rel(path)}: complete expert review requires schema 4 "
                "AI-readability evidence"
            )
        if content_blocker_count:
            raise ValueError(
                f"{_rel(path)}: complete expert review cannot override "
                f"{content_blocker_count} content blocker(s)"
            )
        if readability_blocker_count:
            raise ValueError(
                f"{_rel(path)}: complete expert review cannot override "
                f"{readability_blocker_count} readability blocker(s)"
            )
        if not isinstance(ai_readability_fingerprint, str) or not _is_sha256(
            ai_readability_fingerprint
        ):
            raise ValueError(
                f"{_rel(path)}: current AI-readability fingerprint is required"
            )
        _require_default_release_review_config(path, current_bytes=config_bytes)
        expected_fingerprints = {
            "reference_content": reference_fingerprint,
            "root_content": root_fingerprint,
            "ai_readability": ai_readability_fingerprint,
        }
        if fingerprints != expected_fingerprints:
            raise ValueError(
                f"{_rel(path)}: stale expert content review source fingerprints"
            )
        if not isinstance(attested_by, str) or not attested_by.strip():
            raise ValueError(
                f"{_rel(path)}: complete expert review requires a non-blank maintainer identity"
            )
        _validated_iso_date(
            attested_on,
            label=f"{_rel(path)}: expert content review attested_on",
            evaluation_date=evaluation_date,
        )
        if not normalized_evidence:
            raise ValueError(
                f"{_rel(path)}: complete expert review requires checked-in evidence"
            )
        for item in normalized_evidence:
            _validate_expert_evidence(item)
        expected_by_path = {
            item["path"]: item["classification"] for item in required_dispositions
        }
        actual_by_path = {
            item["path"]: item["classification"]
            for item in normalized_dispositions
        }
        if actual_by_path != expected_by_path:
            missing = sorted(set(expected_by_path) - set(actual_by_path))
            extra = sorted(set(actual_by_path) - set(expected_by_path))
            stale = sorted(
                path_value
                for path_value in set(expected_by_path) & set(actual_by_path)
                if expected_by_path[path_value] != actual_by_path[path_value]
            )
            raise ValueError(
                f"{_rel(path)}: expert content dispositions do not match current "
                f"audit; missing={missing}, extra={extra}, stale={stale}"
            )
        expected_readability_by_document = {
            item["document_id"]: item["highest_band"]
            for item in required_readability_dispositions
        }
        actual_readability_by_document = {
            item["document_id"]: item["highest_band"]
            for item in normalized_readability_dispositions
        }
        if actual_readability_by_document != expected_readability_by_document:
            missing = sorted(
                set(expected_readability_by_document)
                - set(actual_readability_by_document)
            )
            extra = sorted(
                set(actual_readability_by_document)
                - set(expected_readability_by_document)
            )
            stale = sorted(
                document_id
                for document_id in set(expected_readability_by_document)
                & set(actual_readability_by_document)
                if expected_readability_by_document[document_id]
                != actual_readability_by_document[document_id]
            )
            raise ValueError(
                f"{_rel(path)}: expert readability dispositions do not match "
                f"current audit; missing={missing}, extra={extra}, stale={stale}"
            )
        status = "attested-current"
    return {
        "scope": "agent-facing-content",
        "expert_content_review_complete": complete,
        "panel_decision_complete": False,
        "storage_current": complete,
        "decision_method": "legacy-maintainer-attestation",
        "panel_review_id": None,
        "panel_size": 0,
        "attestation_status": status,
        "attestation_source": source,
        "attestation_schema_version": attestation_schema,
        "attestation_config_fingerprint": config_fingerprint,
        "source_fingerprints": dict(fingerprints),
        "attested_by": attested_by,
        "attested_on": attested_on,
        "evidence": normalized_evidence,
        "content_dispositions": normalized_dispositions,
        "readability_dispositions": normalized_readability_dispositions,
        "required_content_disposition_count": len(required_dispositions),
        "applied_content_disposition_count": len(normalized_dispositions),
        "content_blocker_count": content_blocker_count,
        "required_readability_disposition_count": len(
            required_readability_dispositions
        ),
        "applied_readability_disposition_count": len(
            normalized_readability_dispositions
        ),
        "readability_blocker_count": readability_blocker_count,
        "limitations": list(limitations),
    }


def _validated_readability_config(
    path: Path,
    attestation: object,
) -> tuple[dict[str, Any], list[str]]:
    field_name = "readability_review_attestation"
    if (
        not isinstance(attestation, dict)
        or set(attestation) != READABILITY_CONFIG_ATTESTATION_FIELDS
    ):
        raise ValueError(
            f"{_rel(path)}: {field_name} fields must exactly match the "
            "selector-free schema 5 contract"
        )
    if attestation.get("schema_version") != 5:
        raise ValueError(f"{_rel(path)}: {field_name}.schema_version must equal 5")
    if attestation.get("panel_kind") != expert_panel.READABILITY_PANEL_KIND:
        raise ValueError(
            f"{_rel(path)}: {field_name}.panel_kind must equal "
            f"{expert_panel.READABILITY_PANEL_KIND!r}"
        )
    if attestation.get("scope") != "ai-readability-and-density":
        raise ValueError(
            f"{_rel(path)}: {field_name}.scope must equal "
            "'ai-readability-and-density'"
        )
    if attestation.get("decision_method") != expert_panel.DECISION_METHOD:
        raise ValueError(
            f"{_rel(path)}: {field_name}.decision_method is invalid"
        )
    limitations = attestation.get("limitations")
    if not isinstance(limitations, list) or not limitations or not all(
        isinstance(item, str) and item.strip() for item in limitations
    ):
        raise ValueError(
            f"{_rel(path)}: {field_name}.limitations must be a non-empty string list"
        )
    return attestation, list(limitations)


def _validated_professional_config(
    path: Path,
    attestation: object,
) -> tuple[dict[str, Any], list[str]]:
    field_name = "professional_completeness_review_attestation"
    if (
        not isinstance(attestation, dict)
        or set(attestation) != PROFESSIONAL_CONFIG_ATTESTATION_FIELDS
    ):
        raise ValueError(
            f"{_rel(path)}: {field_name} fields must exactly match the "
            "selector-free schema 5 contract"
        )
    if attestation.get("schema_version") != 5:
        raise ValueError(f"{_rel(path)}: {field_name}.schema_version must equal 5")
    if (
        attestation.get("panel_kind")
        != expert_panel.PROFESSIONAL_COMPLETENESS_PANEL_KIND
    ):
        raise ValueError(
            f"{_rel(path)}: {field_name}.panel_kind must equal "
            f"{expert_panel.PROFESSIONAL_COMPLETENESS_PANEL_KIND!r}"
        )
    if attestation.get("scope") != "professional-skill-packages":
        raise ValueError(
            f"{_rel(path)}: {field_name}.scope must equal "
            "'professional-skill-packages'"
        )
    if (
        attestation.get("decision_method")
        != expert_panel.PROFESSIONAL_COMPLETENESS_INCREMENTAL_DECISION_METHOD
    ):
        raise ValueError(
            f"{_rel(path)}: {field_name}.decision_method is invalid"
        )
    limitations = attestation.get("limitations")
    if not isinstance(limitations, list) or not limitations or not all(
        isinstance(item, str) and item.strip() for item in limitations
    ):
        raise ValueError(
            f"{_rel(path)}: {field_name}.limitations must be a non-empty string list"
        )
    return attestation, list(limitations)



def _dual_storage_status(
    path: Path,
    *,
    config_bytes: bytes,
    evidence: list[dict[str, str]],
) -> tuple[bool, str | None]:
    try:
        _require_default_release_review_config(path, current_bytes=config_bytes)
        for item in evidence:
            _validate_expert_evidence(item)
    except ValueError as exc:
        return False, str(exc)
    return True, None


def _missing_axis_result(
    *,
    path: Path,
    field_name: str,
    panel_kind: str,
    scope: str,
    config_fingerprint: str,
    current_source_fingerprints: dict[str, str],
    current_review_contract_fingerprint: str | None = None,
    limitations: list[str],
    required_target_count: int | None = None,
    required_density_count: int | None = None,
    required_readability_count: int | None = None,
    required_actionability_count: int | None = None,
    blocker_count: int = 0,
) -> dict[str, Any]:
    common: dict[str, Any] = {
        "scope": scope,
        "panel_kind": panel_kind,
        "decision_complete": False,
        "storage_current": False,
        "source_current": False,
        "accepted_for_formal": False,
        "decision_method": (
            expert_panel.PROFESSIONAL_COMPLETENESS_DECISION_METHOD
            if panel_kind
            == expert_panel.PROFESSIONAL_COMPLETENESS_PANEL_KIND
            else expert_panel.DECISION_METHOD
        ),
        "panel_review_id": None,
        "panel_size": 0,
        "attestation_status": "missing-evidence",
        "attestation_source": f"{_rel(path)}#{field_name}",
        "attestation_schema_version": 5,
        "attestation_config_fingerprint": config_fingerprint,
        "source_fingerprints": {
            key: None for key in current_source_fingerprints
        },
        "current_source_fingerprints": dict(current_source_fingerprints),
        "attested_by": None,
        "attested_on": None,
        "evidence": [],
        "limitations": list(limitations),
    }
    if panel_kind == expert_panel.READABILITY_PANEL_KIND:
        common.update(
            {
                "density_dispositions": [],
                "readability_dispositions": [],
                "actionability_dispositions": [],
                "panel_artifact_schema_version": None,
                "required_density_disposition_count": required_density_count,
                "applied_density_disposition_count": 0,
                "required_readability_disposition_count": required_readability_count,
                "applied_readability_disposition_count": 0,
                "required_actionability_disposition_count": required_actionability_count,
                "applied_actionability_disposition_count": 0,
                "accepted_current_actionability_count": None,
                "detector_false_positive_count": None,
                "rewrite_required_count": None,
                "tracked_tightening_count": None,
                "blocker_count": blocker_count,
            }
        )
    else:
        common.update(
            {
                "reviewer_pool_size": 0,
                "professional_dispositions": [],
                "panel_artifact_schema_version": None,
                "evidence_contract_satisfied": False,
                "qualification_summary": None,
                "evidence_summary": None,
                "review_contract_fingerprint": None,
                "current_review_contract_fingerprint": (
                    current_review_contract_fingerprint
                ),
                "review_contract_current": False,
                "review_plan_fingerprint": None,
                "current_review_plan_fingerprint": None,
                "review_plan_current": False,
                "review_binding_current": False,
                "provenance_current": False,
                "round_lifecycle_current": False,
                "round_lifecycle": {
                    "status": "no-schema3-current-decision",
                    "round_count": 0,
                    "chain_depth": 0,
                    "head_decision": None,
                    "current_decision_is_head": False,
                    "errors": [],
                    "limitations": [
                        PROFESSIONAL_REVIEW_COST_LIMITATIONS[2]
                    ],
                },
                "review_cost_current": False,
                "review_cost": None,
                "required_target_count": required_target_count,
                "fresh_target_count": 0,
                "carried_forward_target_count": 0,
                "applied_target_count": 0,
                "accepted_current_count": None,
                "correction_count": None,
                "unresolved_professional_disagreement_count": None,
            }
        )
    return common


def _fixed_axis_noncurrent_result(
    result: dict[str, Any],
    *,
    storage_status: str,
    formal: bool,
) -> dict[str, Any] | None:
    if storage_status == "current":
        return None
    if storage_status not in {"missing", "stale", "pending", "invalid"}:
        raise ValueError(
            f"fixed Expert Panel storage status is invalid: {storage_status}"
        )
    if formal:
        raise ValueError(
            f"formal fixed Expert Panel attestation is {storage_status}"
        )
    updated = copy.deepcopy(result)
    updated["attestation_status"] = {
        "missing": "missing-evidence",
        "stale": "panel-majority-stale",
        "pending": "panel-majority-pending-checkin",
        "invalid": "invalid-evidence",
    }[storage_status]
    updated["storage_current"] = False
    updated["source_current"] = False
    updated["accepted_for_formal"] = False
    updated["limitations"] = [
        *updated["limitations"],
        "Fixed Expert Panel attestation storage is " + storage_status + ".",
    ]
    return updated


def _readability_review_axis(
    path: Path,
    *,
    config_bytes: bytes,
    config_fingerprint: str,
    attestation: object,
    content_skills: object,
    readability_content: object,
    content_audit: object,
    evaluation_date: date | None,
    storage_status: str = "current",
    formal: bool = False,
) -> dict[str, Any]:
    field_name = "readability_review_attestation"
    _value, limitations = _validated_readability_config(
        path, attestation
    )
    required_density, content_blockers = _required_content_disposition_rows(
        content_skills
    )
    required_readability, readability_blockers = (
        _required_readability_disposition_rows(readability_content)
    )
    required_actionability = _required_actionability_disposition_rows(
        content_skills
    )
    blocker_count = content_blockers + readability_blockers
    if not isinstance(content_audit, dict):
        raise ValueError(
            "fixed readability attestation requires the current content audit"
        )
    try:
        current_packet = expert_panel.prepare_packet(
            audit=content_audit,
            review_id="current-readability-bindings",
            created_on="2000-01-01",
        )
        current_bindings = expert_panel._readability_target_authorities(
            current_packet
        )
    except expert_panel.PanelReviewError as exc:
        raise ValueError(
            "fixed readability attestation current bindings are invalid"
        ) from exc
    current_source_fingerprints = current_packet["source_fingerprints"]
    expected_review_contract_fingerprint = (
        expert_panel._canonical_json_sha256(current_packet["panel_contract"])
    )
    skeleton = _missing_axis_result(
        path=path,
        field_name=field_name,
        panel_kind=expert_panel.READABILITY_PANEL_KIND,
        scope="ai-readability-and-density",
        config_fingerprint=config_fingerprint,
        current_source_fingerprints=current_source_fingerprints,
        limitations=limitations,
        required_density_count=len(required_density),
        required_readability_count=len(required_readability),
        required_actionability_count=len(required_actionability),
        blocker_count=blocker_count,
    )
    softened = _fixed_axis_noncurrent_result(
        skeleton,
        storage_status=storage_status,
        formal=formal,
    )
    if softened is not None:
        return softened
    fixed = _apply_fixed_readability_attestation(
        skeleton,
        required_density=required_density,
        required_readability=required_readability,
        required_actionability=required_actionability,
        expected_review_contract_fingerprint=(
            expected_review_contract_fingerprint
        ),
        expected_readability_current_bindings=current_bindings,
        require_equivalent=False,
    )
    fixed["limitations"] = list(limitations)
    return fixed


def _read_professional_artifact_reference(
    reference: object,
    *,
    label: str,
) -> tuple[Path, dict[str, Any]]:
    if (
        not isinstance(reference, dict)
        or not isinstance(reference.get("path"), str)
        or not isinstance(reference.get("sha256"), str)
        or not _is_sha256(reference["sha256"])
    ):
        raise ValueError(f"{label} reference is malformed")
    relative = Path(reference["path"])
    if (
        relative.is_absolute()
        or relative.as_posix() != reference["path"]
        or ".." in relative.parts
    ):
        raise ValueError(f"{label} path is not canonical repository-relative")
    candidate = (ROOT / relative).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} escapes the repository") from exc
    if not candidate.is_file():
        raise ValueError(f"{label} is missing: {reference['path']}")
    payload = candidate.read_bytes()
    if hashlib.sha256(payload).hexdigest() != reference["sha256"]:
        raise ValueError(f"{label} sha256 is stale: {reference['path']}")
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is not canonical UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return candidate, value


def _deduplicated_professional_evidence(
    evidence: list[dict[str, str]],
) -> list[dict[str, str]]:
    by_path: dict[str, str] = {}
    for item in evidence:
        path = item["path"]
        sha256 = item["sha256"]
        prior = by_path.get(path)
        if prior is not None and prior != sha256:
            raise ValueError(
                "professional-completeness evidence reuses one path with "
                f"conflicting sha256: {path}"
            )
        by_path[path] = sha256
    return [
        {"path": path, "sha256": by_path[path]}
        for path in sorted(by_path)
    ]


def _professional_schema3_capsule_chain_evidence(
    capsule_reference: dict[str, Any],
    *,
    label: str,
) -> list[dict[str, str]]:
    """Return final, request, and discovery refs after closing the chain."""

    _capsule_path, capsule = _read_professional_artifact_reference(
        capsule_reference, label=f"{label} final capsule"
    )
    if capsule.get("kind") != (
        expert_panel.PROFESSIONAL_COMPLETENESS_CAPSULE_KIND
    ):
        raise ValueError(f"{label} final capsule kind is invalid")
    request_ref = capsule.get("candidate_request")
    discovery_ref = capsule.get("discovery_capsule")
    if not isinstance(request_ref, dict) or not isinstance(discovery_ref, dict):
        raise ValueError(
            f"{label} uses a pre-finalization schema-3 capsule shape; no formal "
            "schema-3 legacy migration is supported, so regenerate a full-fresh "
            "round with discovery, candidate-request, and final capsule artifacts"
        )
    _request_path, request = _read_professional_artifact_reference(
        request_ref, label=f"{label} candidate request"
    )
    if request.get("kind") != (
        expert_panel.PROFESSIONAL_COMPLETENESS_CANDIDATE_REQUEST_KIND
    ) or request.get("discovery_capsule") != discovery_ref:
        raise ValueError(f"{label} candidate request predecessor is stale")
    _discovery_path, discovery = _read_professional_artifact_reference(
        discovery_ref, label=f"{label} discovery capsule"
    )
    if discovery.get("kind") != (
        expert_panel.PROFESSIONAL_COMPLETENESS_DISCOVERY_CAPSULE_KIND
    ):
        raise ValueError(f"{label} discovery capsule kind is invalid")
    voter_id = capsule.get("voter_id")
    if (
        request.get("voter_id") != voter_id
        or discovery.get("voter_id") != voter_id
    ):
        raise ValueError(f"{label} capsule chain crosses voter identities")
    return [
        {
            "path": capsule_reference["path"],
            "sha256": capsule_reference["sha256"],
        },
        {"path": request_ref["path"], "sha256": request_ref["sha256"]},
        {
            "path": discovery_ref["path"],
            "sha256": discovery_ref["sha256"],
        },
    ]


def _professional_schema3_storage_evidence(
    record: dict[str, Any],
    *,
    evidence: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Flatten current and direct-fresh-origin evidence without recursive surplus."""

    flattened = list(evidence)
    for row in record["professional_decisions"]:
        provenance = row["provenance"]
        if provenance["mode"] == "fresh":
            continue
        origin_ref = provenance["origin_decision"]
        flattened.append(
            {"path": origin_ref["path"], "sha256": origin_ref["sha256"]}
        )
        _origin_path, origin = _read_professional_artifact_reference(
            origin_ref,
            label=f"schema-3 direct fresh origin for {row['skill_id']}",
        )
        packet_ref = origin.get("packet")
        if not isinstance(packet_ref, dict):
            raise ValueError(
                f"schema-3 direct fresh origin packet is missing: {row['skill_id']}"
            )
        flattened.append(
            {"path": packet_ref["path"], "sha256": packet_ref["sha256"]}
        )
        matches = [
            origin_row
            for origin_row in origin.get("professional_decisions", [])
            if isinstance(origin_row, dict)
            and origin_row.get("skill_id") == row["skill_id"]
        ]
        if len(matches) != 1:
            raise ValueError(
                f"schema-3 direct fresh origin target is missing: {row['skill_id']}"
            )
        origin_provenance = matches[0].get("provenance")
        if (
            not isinstance(origin_provenance, dict)
            or origin_provenance.get("mode") != "fresh"
            or origin_provenance.get("origin_depth") != 0
            or not isinstance(origin_provenance.get("evidence"), list)
            or len(origin_provenance["evidence"]) != expert_panel.PANEL_SIZE
        ):
            raise ValueError(
                f"schema-3 carry origin is not direct fresh evidence: {row['skill_id']}"
            )
        for origin_evidence in origin_provenance["evidence"]:
            ballot = origin_evidence["ballot"]
            flattened.append(
                {"path": ballot["path"], "sha256": ballot["sha256"]}
            )
            flattened.extend(
                _professional_schema3_capsule_chain_evidence(
                    origin_evidence["capsule"],
                    label=(
                        "schema-3 direct origin voter "
                        f"{origin_evidence['voter_id']} for {row['skill_id']}"
                    ),
                )
            )
    return _deduplicated_professional_evidence(flattened)


def _professional_schema3_round_topology(
    *,
    round_paths: set[str],
    baseline_by_child: dict[str, str | None],
    current_relative: str,
    initial_errors: list[str] | None = None,
) -> dict[str, Any]:
    """Derive the single-chain lifecycle without trusting a selected head."""

    errors = list(initial_errors or [])
    child_count = {path: 0 for path in round_paths}
    for child, baseline in baseline_by_child.items():
        if child not in round_paths:
            errors.append(
                "schema-3 Professional topology names an unknown child: " + child
            )
            continue
        if baseline is None:
            continue
        if baseline not in round_paths:
            errors.append(
                "schema-3 Professional round chain has a missing predecessor: "
                f"{child} -> {baseline}"
            )
            continue
        child_count[baseline] += 1
        if child_count[baseline] > 1:
            errors.append(
                "schema-3 Professional round chain forks at " + baseline
            )
    cycle_nodes: set[str] = set()
    globally_seen: set[str] = set()
    for start in sorted(round_paths):
        local_order: list[str] = []
        local_index: dict[str, int] = {}
        cursor: str | None = start
        while cursor in round_paths and cursor not in globally_seen:
            if cursor in local_index:
                cycle_nodes.update(local_order[local_index[cursor] :])
                break
            local_index[cursor] = len(local_order)
            local_order.append(cursor)
            cursor = baseline_by_child.get(cursor)
        globally_seen.update(local_order)
    if cycle_nodes:
        errors.append(
            "schema-3 Professional round chain contains a cycle: "
            + ", ".join(sorted(cycle_nodes))
        )
    heads = sorted(path for path, count in child_count.items() if count == 0)
    if len(heads) != 1:
        errors.append(
            "schema-3 Professional rounds must have exactly one current head"
        )
    chain: list[str] = []
    cursor = heads[0] if len(heads) == 1 else None
    while cursor in round_paths and cursor not in chain:
        chain.append(cursor)
        cursor = baseline_by_child.get(cursor)
    if set(chain) != round_paths:
        errors.append(
            "schema-3 Professional round tree contains an orphan or skipped round"
        )
    normalized_errors = sorted(set(errors))
    selected = not normalized_errors and current_relative == heads[0]
    return {
        "status": (
            "schema3-head-current"
            if selected
            else (
                "schema3-round-lifecycle-invalid"
                if normalized_errors
                else "schema3-head-not-selected"
            )
        ),
        "chain_depth": len(chain),
        "head_decision": heads[0] if len(heads) == 1 else None,
        "current_decision_is_head": selected,
        "errors": normalized_errors,
    }


def _professional_schema3_round_lifecycle(
    current_record_path: Path,
) -> dict[str, Any]:
    """Require every checked-in schema-3 Professional round to form one chain."""

    decisions: dict[str, tuple[Path, dict[str, Any], dict[str, Any]]] = {}
    lifecycle_evidence: list[dict[str, str]] = []
    current_contract = (
        expert_panel._professional_evidence_review_contract_fingerprint()
    )
    rounds_root = ROOT / "evals" / "expert-panel"
    if rounds_root.is_dir():
        for candidate in sorted(rounds_root.glob("*/panel/decision.json")):
            try:
                value = json.loads(candidate.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ValueError(
                    f"schema-3 Professional round is unreadable: {_rel(candidate)}"
                ) from exc
            if not isinstance(value, dict) or value.get("kind") != (
                expert_panel.PROFESSIONAL_COMPLETENESS_DECISION_KIND
            ):
                continue
            if value.get("schema_version") != (
                expert_panel.PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
            ):
                continue
            relative = candidate.relative_to(ROOT).as_posix()
            try:
                contract = expert_panel._professional_v3_decision_envelope(
                    value
                )
                expected_decision_path = (
                    f"evals/expert-panel/{value['review_id']}/panel/decision.json"
                )
                expected_packet_path = (
                    f"evals/expert-panel/{value['review_id']}/packet.json"
                )
                if (
                    relative != expected_decision_path
                    or value["packet"]["path"] != expected_packet_path
                ):
                    raise expert_panel.PanelReviewError(
                        "historical schema-3 artifact path does not match review_id"
                    )
                packet_path, packet = _read_professional_artifact_reference(
                    value["packet"],
                    label=f"schema-3 round packet {relative}",
                )
                if (
                    set(packet) != expert_panel.PROFESSIONAL_V3_PACKET_FIELDS
                    or packet.get("schema_version")
                    != expert_panel.PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
                    or packet.get("kind")
                    != expert_panel.PROFESSIONAL_COMPLETENESS_PACKET_KIND
                    or packet.get("review_id") != value.get("review_id")
                    or packet.get("review_contract_fingerprint") != contract
                    or value.get("source_fingerprints")
                    != packet.get("source_fingerprints")
                ):
                    raise expert_panel.PanelReviewError(
                        "historical schema-3 decision/packet envelope is stale"
                    )
                expert_panel._validate_professional_v3_review_plan_shape(
                    packet.get("review_plan"),
                    target_ids=sorted(
                        target["skill_id"]
                        for target in packet.get("professional_targets", [])
                    ),
                    review_contract_fingerprint=contract,
                )
                if contract == current_contract:
                    expert_panel.validate_decision_record(
                        value,
                        record_path=candidate,
                        validation_root=ROOT,
                    )
            except (KeyError, TypeError, expert_panel.PanelReviewError) as exc:
                raise ValueError(
                    f"invalid schema-3 Professional round {relative}: {exc}"
                ) from exc
            decision_sha256 = hashlib.sha256(candidate.read_bytes()).hexdigest()
            lifecycle_evidence.extend(
                [
                    {"path": relative, "sha256": decision_sha256},
                    {
                        "path": value["packet"]["path"],
                        "sha256": value["packet"]["sha256"],
                    },
                ]
            )
            for voter in value.get("voters", []):
                if not isinstance(voter, dict):
                    raise ValueError(
                        f"schema-3 round voter is invalid: {relative}"
                    )
                ballot = voter.get("ballot")
                capsule = voter.get("capsule")
                if not isinstance(ballot, dict) or not isinstance(capsule, dict):
                    raise ValueError(
                        f"schema-3 round voter evidence is incomplete: {relative}"
                    )
                lifecycle_evidence.append(
                    {"path": ballot["path"], "sha256": ballot["sha256"]}
                )
                lifecycle_evidence.extend(
                    _professional_schema3_capsule_chain_evidence(
                        capsule,
                        label=(
                            f"schema-3 round {value['review_id']} voter "
                            f"{voter.get('voter_id')}"
                        ),
                    )
                )
            decisions[relative] = (candidate, value, packet)
    if not decisions:
        return {
            "status": "no-schema3-rounds",
            "round_count": 0,
            "chain_depth": 0,
            "head_decision": None,
            "current_decision_is_head": False,
            "errors": [],
            "limitations": [PROFESSIONAL_REVIEW_COST_LIMITATIONS[2]],
            "_storage_evidence": [],
        }
    baseline_by_child: dict[str, str | None] = {}
    topology_errors: list[str] = []
    for relative, (_decision_path, decision, packet) in decisions.items():
        baseline = packet["review_plan"]["baseline"]
        baseline_path = None if baseline is None else baseline["decision"]["path"]
        if baseline_path is not None:
            if baseline_path in decisions:
                baseline_decision = decisions[baseline_path][1]
                if (
                    baseline["decision"]["sha256"]
                    != hashlib.sha256(
                        decisions[baseline_path][0].read_bytes()
                    ).hexdigest()
                    or baseline["packet"] != baseline_decision["packet"]
                ):
                    topology_errors.append(
                        "schema-3 Professional round predecessor binding is stale: "
                        f"{relative} -> {baseline_path}"
                    )
        baseline_by_child[relative] = baseline_path
    current_relative = current_record_path.resolve().relative_to(
        ROOT.resolve()
    ).as_posix()
    topology = _professional_schema3_round_topology(
        round_paths=set(decisions),
        baseline_by_child=baseline_by_child,
        current_relative=current_relative,
        initial_errors=topology_errors,
    )
    return {
        "status": topology["status"],
        "round_count": len(decisions),
        "chain_depth": topology["chain_depth"],
        "head_decision": topology["head_decision"],
        "current_decision_is_head": topology[
            "current_decision_is_head"
        ],
        "errors": topology["errors"],
        "limitations": [PROFESSIONAL_REVIEW_COST_LIMITATIONS[2]],
        "_storage_evidence": _deduplicated_professional_evidence(
            lifecycle_evidence
        ),
    }


def _professional_schema3_current_state(
    record: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, bool | str]]:
    packet_path, packet = _read_professional_artifact_reference(
        record["packet"], label="schema-3 current packet"
    )
    baseline = packet["review_plan"]["baseline"]
    baseline_path = (
        None
        if baseline is None
        else (ROOT / baseline["decision"]["path"]).resolve()
    )
    try:
        expected = expert_panel.prepare_professional_completeness_packet_v3(
            review_id=record["review_id"],
            created_on=packet["created_on"],
            baseline_decision_path=baseline_path,
            root=ROOT,
            validation_root=ROOT,
        )
    except expert_panel.PanelReviewError as exc:
        raise ValueError(
            f"cannot rebuild canonical schema-3 Professional plan: {exc}"
        ) from exc
    actual_bindings = {
        target["skill_id"]: target["review_binding"]
        for target in packet["professional_targets"]
    }
    current_bindings = {
        target["skill_id"]: target["review_binding"]
        for target in expected["professional_targets"]
    }
    fresh = {
        row["skill_id"] for row in expected["review_plan"]["fresh_targets"]
    }
    carried = {
        row["skill_id"] for row in expected["review_plan"]["carried_targets"]
    }
    provenance_current = all(
        (
            row["provenance"]["mode"] == "fresh"
            and row["skill_id"] in fresh
        )
        or (
            row["provenance"]["mode"] == "carried-forward"
            and row["skill_id"] in carried
        )
        for row in record["professional_decisions"]
    )
    return packet, expected, {
        "review_contract_current": (
            packet["review_contract_fingerprint"]
            == expected["review_contract_fingerprint"]
            == record["review_contract_fingerprint"]
        ),
        "review_plan_current": packet["review_plan"] == expected["review_plan"],
        "review_binding_current": actual_bindings == current_bindings,
        "provenance_current": provenance_current,
    }


def _professional_review_formal_round_policy() -> tuple[dict[str, int], str]:
    try:
        contracts = json.loads(CORE_CONTRACTS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            "cannot load Professional review formal-round policy authority"
        ) from exc
    contract_errors = validate_core_contracts(contracts)
    if contract_errors:
        raise ValueError(
            "Professional review formal-round policy authority is invalid: "
            + "; ".join(contract_errors)
        )
    try:
        policy = contracts["final_goal_contract"][
            "professional_review_cost_fixtures"
        ]["formal_round_policy"]
    except (KeyError, TypeError) as exc:
        raise ValueError(
            "Professional review formal-round policy authority is missing"
        ) from exc
    if (
        not isinstance(policy, dict)
        or set(policy) != PROFESSIONAL_REVIEW_FORMAL_ROUND_POLICY_FIELDS
        or any(
            type(policy.get(field)) is not int or policy[field] < 0
            for field in PROFESSIONAL_REVIEW_FORMAL_ROUND_POLICY_FIELDS
            - {"schema_version"}
        )
        or policy.get("schema_version") != 1
    ):
        raise ValueError(
            "Professional review formal-round policy authority is malformed"
        )
    normalized = dict(policy)
    fingerprint = hashlib.sha256(
        expert_panel.professional_carry.canonical_json_bytes(normalized)
    ).hexdigest()
    return normalized, fingerprint


def _professional_review_cost_add_blocks(
    blocks: object,
    *,
    sizes: dict[str, int],
    occurrences: dict[str, int],
    label: str,
) -> None:
    if not isinstance(blocks, list):
        raise ValueError(f"{label} must be an array")
    seen: set[str] = set()
    for index, block in enumerate(blocks):
        if (
            not isinstance(block, dict)
            or set(block) != {"sha256", "canonical_json_bytes_proxy"}
        ):
            raise ValueError(f"{label}[{index}] fields are invalid")
        digest = block["sha256"]
        size = block["canonical_json_bytes_proxy"]
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(char not in "0123456789abcdef" for char in digest)
            or type(size) is not int
            or size <= 0
            or digest in seen
        ):
            raise ValueError(f"{label}[{index}] value is invalid")
        seen.add(digest)
        prior_size = sizes.get(digest)
        if prior_size is not None and prior_size != size:
            raise ValueError(
                "schema-3 review cost input block sizes conflict"
            )
        sizes[digest] = size
        occurrences[digest] = occurrences.get(digest, 0) + 1


def _professional_review_source_material_blocks(
    *projections: dict[str, Any],
) -> list[dict[str, Any]]:
    blocks_by_digest: dict[str, dict[str, Any]] = {}
    for projection_index, projection in enumerate(projections):
        material = projection.get("material_catalog")
        if not isinstance(material, list):
            raise ValueError(
                "schema-3 review cost source projection lacks material catalog: "
                f"{projection_index}"
            )
        for row_index, row in enumerate(material):
            if not isinstance(row, dict):
                raise ValueError(
                    "schema-3 review cost source material row is invalid: "
                    f"{projection_index}[{row_index}]"
                )
            block = expert_panel._professional_v3_input_block(
                {"block_kind": "source-material", "value": row}
            )
            existing = blocks_by_digest.get(block["sha256"])
            if existing is not None and existing != block:
                raise ValueError(
                    "schema-3 review cost source-material digest conflicts"
                )
            blocks_by_digest[block["sha256"]] = block
    return [
        blocks_by_digest[digest] for digest in sorted(blocks_by_digest)
    ]


def _professional_review_charged_bytes(
    *, sizes: dict[str, int], occurrences: dict[str, int]
) -> int:
    if set(sizes) != set(occurrences):
        raise ValueError("schema-3 review cost block accounting is incomplete")
    return sum(
        sizes[digest] * min(count, expert_panel.PANEL_SIZE)
        for digest, count in occurrences.items()
    )


def _professional_schema3_review_cost(
    record: dict[str, Any],
    *,
    packet: dict[str, Any],
) -> dict[str, Any]:
    artifact_targets = packet.get("professional_targets")
    if not isinstance(artifact_targets, list) or not artifact_targets:
        raise ValueError(
            "schema-3 review cost artifact packet targets are invalid"
        )
    artifact_target_count = len(artifact_targets)
    rows = record["professional_decisions"]
    fresh_rows = [row for row in rows if row["provenance"]["mode"] == "fresh"]
    carried_rows = [
        row for row in rows if row["provenance"]["mode"] == "carried-forward"
    ]
    fresh_count = len(fresh_rows)
    carried_count = len(carried_rows)
    if fresh_count + carried_count != artifact_target_count:
        raise ValueError(
            "schema-3 review cost target partition does not match artifact packet"
        )
    capsule_refs: dict[
        tuple[str, str], tuple[dict[str, Any], list[dict[str, Any]]]
    ] = {}
    for voter in record["voters"]:
        reference = voter["capsule"]
        key = (reference["path"], reference["sha256"])
        blocks = voter.get("capsule_input_blocks_proxy")
        if not isinstance(blocks, list):
            raise ValueError("schema-3 review cost lacks capsule input blocks")
        prior = capsule_refs.get(key)
        value = (reference, blocks)
        if prior is not None and prior != value:
            raise ValueError(
                "schema-3 review cost capsule evidence conflicts across voters"
            )
        capsule_refs[key] = value
    block_occurrences: dict[str, int] = {}
    block_sizes: dict[str, int] = {}
    required_block_occurrences: dict[str, int] = {}
    required_block_sizes: dict[str, int] = {}
    source_block_occurrences: dict[str, int] = {}
    source_block_sizes: dict[str, int] = {}
    required_source_block_occurrences: dict[str, int] = {}
    required_source_block_sizes: dict[str, int] = {}
    bindings = expert_panel.professional_carry.professional_review_bindings(
        artifact_targets
    )
    fresh_ids = {row["skill_id"] for row in fresh_rows}
    required_candidate_ids_by_target: dict[str, tuple[str, ...]] = {}
    reviewer_added_ids_by_target: dict[str, set[str]] = {
        skill_id: set() for skill_id in fresh_ids
    }
    reviewer_added_request_count = 0
    for reference, stored_blocks in capsule_refs.values():
        _capsule_path, capsule = _read_professional_artifact_reference(
            reference, label="schema-3 current review capsule"
        )
        _request_path, request = _read_professional_artifact_reference(
            capsule["candidate_request"],
            label="schema-3 current candidate request",
        )
        _discovery_path, discovery = _read_professional_artifact_reference(
            capsule["discovery_capsule"],
            label="schema-3 current discovery capsule",
        )
        recomputed_blocks = (
            expert_panel._professional_v3_effective_capsule_input_blocks(
                discovery_capsule=discovery,
                candidate_request=request,
                capsule=capsule,
            )
        )
        if stored_blocks != recomputed_blocks:
            raise ValueError(
                "schema-3 review cost capsule input blocks are stale"
            )
        _professional_review_cost_add_blocks(
            recomputed_blocks,
            sizes=block_sizes,
            occurrences=block_occurrences,
            label="schema-3 actual input blocks",
        )
        discovery_projection = discovery["discovery_projection"]
        final_projection = capsule["review_projection"]
        assigned_ids = request["assigned_fresh_target_ids"]
        if assigned_ids != discovery_projection["assigned_fresh_target_ids"]:
            raise ValueError(
                "schema-3 review cost assignment differs across capsule chain"
            )
        empty_requests = {skill_id: [] for skill_id in assigned_ids}
        required_final_projection = (
            expert_panel._professional_v3_capsule_projection_from_packet(
                packet=packet,
                assigned_skill_ids=assigned_ids,
                reviewer_added_requests_by_target=empty_requests,
                bindings=bindings,
            )
        )
        required_blocks = expert_panel._professional_v3_effective_input_blocks(
            review_contract_fingerprint=packet[
                "review_contract_fingerprint"
            ],
            discovery_projection=discovery_projection,
            assigned_skill_ids=assigned_ids,
            reviewer_added_requests=[],
            final_projection=required_final_projection,
        )
        _professional_review_cost_add_blocks(
            required_blocks,
            sizes=required_block_sizes,
            occurrences=required_block_occurrences,
            label="schema-3 required-only input blocks",
        )
        _professional_review_cost_add_blocks(
            _professional_review_source_material_blocks(
                discovery_projection, final_projection
            ),
            sizes=source_block_sizes,
            occurrences=source_block_occurrences,
            label="schema-3 actual source-material blocks",
        )
        _professional_review_cost_add_blocks(
            _professional_review_source_material_blocks(
                discovery_projection, required_final_projection
            ),
            sizes=required_source_block_sizes,
            occurrences=required_source_block_occurrences,
            label="schema-3 required-only source-material blocks",
        )
        discovery_targets = {
            row["skill_id"]: row
            for row in discovery_projection["targets"]
        }
        if set(discovery_targets) != set(assigned_ids):
            raise ValueError(
                "schema-3 review cost discovery targets differ from assignment"
            )
        for skill_id in assigned_ids:
            required_ids = tuple(
                row["skill_id"]
                for row in discovery_targets[skill_id]["adjacency"][
                    "required_candidates"
                ]
            )
            prior_required = required_candidate_ids_by_target.get(skill_id)
            if prior_required is not None and prior_required != required_ids:
                raise ValueError(
                    "schema-3 review cost required candidate set differs across voters: "
                    + skill_id
                )
            required_candidate_ids_by_target[skill_id] = required_ids
        requests = request["reviewer_added_requests"]
        reviewer_added_request_count += len(requests)
        for added in requests:
            target_id = added["target_skill_id"]
            candidate_id = added["skill_id"]
            if target_id not in reviewer_added_ids_by_target:
                raise ValueError(
                    "schema-3 reviewer-added request names a non-fresh target"
                )
            reviewer_added_ids_by_target[target_id].add(candidate_id)
    capsule_bytes = _professional_review_charged_bytes(
        sizes=block_sizes, occurrences=block_occurrences
    )
    required_only_bytes = _professional_review_charged_bytes(
        sizes=required_block_sizes,
        occurrences=required_block_occurrences,
    )
    source_material_bytes = _professional_review_charged_bytes(
        sizes=source_block_sizes,
        occurrences=source_block_occurrences,
    )
    required_source_material_bytes = _professional_review_charged_bytes(
        sizes=required_source_block_sizes,
        occurrences=required_source_block_occurrences,
    )
    full_rereview_bytes = expert_panel.PANEL_SIZE * sum(
        block["canonical_json_bytes_proxy"]
        for block in expert_panel._professional_v3_full_rereview_input_blocks(
            packet
        )
    )
    all_skill_ids = sorted(bindings)
    full_discovery_projection = (
        expert_panel._professional_v3_discovery_projection_from_packet(
            packet=packet,
            assigned_skill_ids=all_skill_ids,
            bindings=bindings,
        )
    )
    full_final_projection = (
        expert_panel._professional_v3_capsule_projection_from_packet(
            packet=packet,
            assigned_skill_ids=all_skill_ids,
            reviewer_added_requests_by_target=None,
            bindings=bindings,
        )
    )
    full_source_blocks = _professional_review_source_material_blocks(
        full_discovery_projection, full_final_projection
    )
    full_source_material_bytes = expert_panel.PANEL_SIZE * sum(
        block["canonical_json_bytes_proxy"] for block in full_source_blocks
    )
    if full_rereview_bytes <= 0 or full_source_material_bytes <= 0:
        raise ValueError("schema-3 review cost full denominator is invalid")
    ratio = (
        capsule_bytes * 1_000_000 // full_rereview_bytes
    )
    required_only_ratio = (
        required_only_bytes * 1_000_000 // full_rereview_bytes
    )
    source_material_coverage_ratio = (
        source_material_bytes * 1_000_000
        // full_source_material_bytes
    )
    if (
        source_material_bytes < required_source_material_bytes
        or source_material_bytes > full_source_material_bytes
        or required_only_bytes < required_source_material_bytes
        or capsule_bytes < source_material_bytes
    ):
        raise ValueError(
            "schema-3 review cost source-material decomposition is invalid"
        )
    actual_metadata_bytes = capsule_bytes - source_material_bytes
    required_metadata_bytes = (
        required_only_bytes - required_source_material_bytes
    )
    if actual_metadata_bytes < required_metadata_bytes:
        raise ValueError(
            "schema-3 reviewer-added relationship/evidence metadata overhead is negative"
        )
    reviewer_added_source_material_bytes = (
        source_material_bytes - required_source_material_bytes
    )
    reviewer_added_metadata_overhead_bytes = (
        actual_metadata_bytes - required_metadata_bytes
    )
    reviewer_added_metadata_overhead_ratio = (
        reviewer_added_metadata_overhead_bytes * 1_000_000
        // required_metadata_bytes
        if required_metadata_bytes
        else 0
    )
    if set(required_candidate_ids_by_target) != fresh_ids:
        raise ValueError(
            "schema-3 review cost required candidate coverage is incomplete"
        )
    maximum_reviewer_added_union_ratio = 0
    for skill_id in sorted(fresh_ids):
        required_count = len(required_candidate_ids_by_target[skill_id])
        added_count = len(reviewer_added_ids_by_target[skill_id])
        if required_count <= 0:
            raise ValueError(
                "schema-3 review cost target lacks a required candidate budget: "
                + skill_id
            )
        maximum_reviewer_added_union_ratio = max(
            maximum_reviewer_added_union_ratio,
            added_count * 1_000_000 // required_count,
        )
    reviewer_added_unique_relationship_count = sum(
        len(values) for values in reviewer_added_ids_by_target.values()
    )
    formal_policy, formal_policy_fingerprint = (
        _professional_review_formal_round_policy()
    )
    maximum_origin_depth = max(
        (row["provenance"]["origin_depth"] for row in rows), default=0
    )
    core_cost = record["summary"]["review_cost"]
    expected_core_cost = {
        "fresh_vote_count": expert_panel.PANEL_SIZE * fresh_count,
        "avoided_vote_count": expert_panel.PANEL_SIZE * carried_count,
        "fresh_criterion_result_count": 30 * fresh_count,
        "carried_criterion_result_count": 30 * carried_count,
        "effective_criterion_result_count": 30 * artifact_target_count,
        "avoided_criterion_result_count": 30 * carried_count,
        "canonical_capsule_input_bytes_proxy": capsule_bytes,
        "full_rereview_deduplicated_capsule_input_bytes_proxy": (
            full_rereview_bytes
        ),
        "input_ratio_ppm": ratio,
        "maximum_origin_depth": maximum_origin_depth,
    }
    if core_cost != expected_core_cost:
        raise ValueError("schema-3 core review_cost does not match raw evidence")
    plan = packet["review_plan"]
    split_policy_valid = True
    if fresh_count == 0:
        policy_status = "all-carry-zero-input"
        split_policy_valid = all(
            value == 0
            for value in (
                capsule_bytes,
                required_only_bytes,
                source_material_bytes,
                required_source_material_bytes,
                reviewer_added_source_material_bytes,
                reviewer_added_metadata_overhead_bytes,
                reviewer_added_request_count,
                reviewer_added_unique_relationship_count,
                maximum_reviewer_added_union_ratio,
                ratio,
                required_only_ratio,
                source_material_coverage_ratio,
                reviewer_added_metadata_overhead_ratio,
            )
        )
    elif fresh_count == artifact_target_count:
        reasons = {
            reason
            for row in plan["fresh_targets"]
            for reason in row["reason_codes"]
        }
        if plan["baseline"] is None:
            policy_status = "bootstrap-full-review"
        elif "review-contract-changed" in reasons:
            policy_status = "contract-change-full-review"
        elif "lineage-depth-limit" in reasons:
            policy_status = "lineage-checkpoint-full-review"
        else:
            policy_status = "full-fresh-review"
        split_policy_valid = bool(
            required_only_bytes == full_rereview_bytes
            and required_only_ratio == 1_000_000
            and required_source_material_bytes
            == full_source_material_bytes
            and source_material_coverage_ratio
            == formal_policy[
                "full_fresh_source_material_coverage_ratio_ppm"
            ]
        )
    else:
        policy_status = "incremental-reduced-input"
        split_policy_valid = bool(
            0 < required_only_bytes < full_rereview_bytes
            and 0 < required_only_ratio < 1_000_000
            and 0 < required_source_material_bytes
            <= source_material_bytes
            <= full_source_material_bytes
        )
    if not split_policy_valid:
        policy_status = "required-source-coverage-invalid"
    elif (
        maximum_reviewer_added_union_ratio
        > formal_policy[
            "maximum_reviewer_added_unique_union_to_required_ratio_ppm"
        ]
    ):
        policy_status = "reviewer-added-relationship-budget-exceeded"
    elif (
        reviewer_added_metadata_overhead_bytes * 1_000_000
        > formal_policy[
            "maximum_reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm"
        ]
        * required_metadata_bytes
    ):
        policy_status = "reviewer-added-metadata-overhead-exceeded"
    if (
        maximum_origin_depth > 1
        or plan["plan_lineage_depth"]
        > expert_panel.PROFESSIONAL_COMPLETENESS_MAX_PLAN_LINEAGE_DEPTH
    ):
        raise ValueError("schema-3 review cost lineage bounds are stale")
    return {
        "fresh_vote_count": expert_panel.PANEL_SIZE * fresh_count,
        "carried_forward_vote_count": expert_panel.PANEL_SIZE * carried_count,
        "effective_vote_count": (
            expert_panel.PANEL_SIZE * artifact_target_count
        ),
        "fresh_criterion_result_count": 30 * fresh_count,
        "carried_forward_criterion_result_count": 30 * carried_count,
        "effective_criterion_result_count": 30 * artifact_target_count,
        "canonical_capsule_input_bytes_proxy": capsule_bytes,
        "full_rereview_deduplicated_capsule_input_bytes_proxy": (
            full_rereview_bytes
        ),
        "input_ratio_ppm": ratio,
        "required_only_capsule_input_bytes_proxy": required_only_bytes,
        "required_only_input_ratio_ppm": required_only_ratio,
        "required_only_source_material_input_bytes_proxy": (
            required_source_material_bytes
        ),
        "source_material_input_bytes_proxy": source_material_bytes,
        "full_rereview_source_material_input_bytes_proxy": (
            full_source_material_bytes
        ),
        "source_material_coverage_ratio_ppm": (
            source_material_coverage_ratio
        ),
        "reviewer_added_source_material_input_bytes_proxy": (
            reviewer_added_source_material_bytes
        ),
        "reviewer_added_relationship_evidence_metadata_overhead_bytes_proxy": (
            reviewer_added_metadata_overhead_bytes
        ),
        "reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm": (
            reviewer_added_metadata_overhead_ratio
        ),
        "reviewer_added_request_count": reviewer_added_request_count,
        "reviewer_added_unique_relationship_count": (
            reviewer_added_unique_relationship_count
        ),
        "maximum_reviewer_added_unique_union_to_required_ratio_ppm": (
            maximum_reviewer_added_union_ratio
        ),
        "formal_round_policy_fingerprint": formal_policy_fingerprint,
        "maximum_origin_depth": maximum_origin_depth,
        "plan_lineage_depth": plan["plan_lineage_depth"],
        "policy_status": policy_status,
        "limitations": list(PROFESSIONAL_REVIEW_COST_LIMITATIONS),
    }


def _professional_review_cost_policy_satisfied(
    review_cost: object,
    *,
    fresh_target_count: int,
    carried_forward_target_count: int,
) -> bool:
    if (
        not isinstance(review_cost, dict)
        or set(review_cost) != PROFESSIONAL_REVIEW_COST_FIELDS
        or review_cost.get("limitations")
        != PROFESSIONAL_REVIEW_COST_LIMITATIONS
    ):
        return False
    integer_fields = (
        PROFESSIONAL_REVIEW_COST_FIELDS - PROFESSIONAL_REVIEW_COST_TEXT_FIELDS
    )
    if (
        fresh_target_count + carried_forward_target_count
        != expert_panel.PROFESSIONAL_PACKAGE_COUNT
        or any(
            type(review_cost.get(field)) is not int
            or review_cost[field] < 0
            for field in integer_fields
        )
    ):
        return False
    try:
        formal_policy, formal_policy_fingerprint = (
            _professional_review_formal_round_policy()
        )
    except ValueError:
        return False
    fingerprint = review_cost.get("formal_round_policy_fingerprint")
    if (
        not isinstance(fingerprint, str)
        or len(fingerprint) != 64
        or any(char not in "0123456789abcdef" for char in fingerprint)
        or fingerprint != formal_policy_fingerprint
    ):
        return False
    actual = review_cost["canonical_capsule_input_bytes_proxy"]
    denominator = review_cost[
        "full_rereview_deduplicated_capsule_input_bytes_proxy"
    ]
    required = review_cost["required_only_capsule_input_bytes_proxy"]
    actual_source = review_cost["source_material_input_bytes_proxy"]
    required_source = review_cost[
        "required_only_source_material_input_bytes_proxy"
    ]
    full_source = review_cost[
        "full_rereview_source_material_input_bytes_proxy"
    ]
    if (
        denominator <= 0
        or full_source <= 0
        or required > actual
        or required_source > actual_source
        or actual_source > full_source
        or actual < actual_source
        or required < required_source
    ):
        return False
    actual_metadata = actual - actual_source
    required_metadata = required - required_source
    if actual_metadata < required_metadata:
        return False
    metadata_overhead = actual_metadata - required_metadata
    expected_metadata_overhead_ratio = (
        metadata_overhead * 1_000_000 // required_metadata
        if required_metadata
        else 0
    )
    if (
        review_cost["input_ratio_ppm"]
        != actual * 1_000_000 // denominator
        or review_cost["required_only_input_ratio_ppm"]
        != required * 1_000_000 // denominator
        or review_cost["source_material_coverage_ratio_ppm"]
        != actual_source * 1_000_000 // full_source
        or review_cost[
            "reviewer_added_source_material_input_bytes_proxy"
        ]
        != actual_source - required_source
        or review_cost[
            "reviewer_added_relationship_evidence_metadata_overhead_bytes_proxy"
        ]
        != metadata_overhead
        or review_cost[
            "reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm"
        ]
        != expected_metadata_overhead_ratio
        or metadata_overhead * 1_000_000
        > formal_policy[
            "maximum_reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm"
        ]
        * required_metadata
        or review_cost[
            "maximum_reviewer_added_unique_union_to_required_ratio_ppm"
        ]
        > formal_policy[
            "maximum_reviewer_added_unique_union_to_required_ratio_ppm"
        ]
        or review_cost["reviewer_added_unique_relationship_count"]
        > review_cost["reviewer_added_request_count"]
        or review_cost["reviewer_added_request_count"]
        > expert_panel.PANEL_SIZE
        * review_cost["reviewer_added_unique_relationship_count"]
        or review_cost["fresh_vote_count"]
        != expert_panel.PANEL_SIZE * fresh_target_count
        or review_cost["carried_forward_vote_count"]
        != expert_panel.PANEL_SIZE * carried_forward_target_count
        or review_cost["effective_vote_count"] != 567
        or review_cost["fresh_criterion_result_count"]
        != 30 * fresh_target_count
        or review_cost["carried_forward_criterion_result_count"]
        != 30 * carried_forward_target_count
        or review_cost["effective_criterion_result_count"] != 5670
        or review_cost["maximum_origin_depth"] > 1
        or review_cost["plan_lineage_depth"]
        > expert_panel.PROFESSIONAL_COMPLETENESS_MAX_PLAN_LINEAGE_DEPTH
    ):
        return False
    status = review_cost.get("policy_status")
    if fresh_target_count == 0:
        return bool(
            all(
                review_cost[field] == 0
                for field in {
                    "canonical_capsule_input_bytes_proxy",
                    "required_only_capsule_input_bytes_proxy",
                    "required_only_source_material_input_bytes_proxy",
                    "source_material_input_bytes_proxy",
                    "source_material_coverage_ratio_ppm",
                    "reviewer_added_source_material_input_bytes_proxy",
                    "reviewer_added_relationship_evidence_metadata_overhead_bytes_proxy",
                    "reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm",
                    "reviewer_added_request_count",
                    "reviewer_added_unique_relationship_count",
                    "maximum_reviewer_added_unique_union_to_required_ratio_ppm",
                    "input_ratio_ppm",
                    "required_only_input_ratio_ppm",
                }
            )
            and status == "all-carry-zero-input"
        )
    if fresh_target_count < expert_panel.PROFESSIONAL_PACKAGE_COUNT:
        return bool(
            0 < required < denominator
            and 0 < required_source <= actual_source <= full_source
            and 0 < review_cost["required_only_input_ratio_ppm"] < 1_000_000
            and required_metadata > 0
            and status == "incremental-reduced-input"
        )
    return bool(
        required == denominator
        and review_cost["required_only_input_ratio_ppm"] == 1_000_000
        and required_source == full_source
        and review_cost["source_material_coverage_ratio_ppm"]
        == formal_policy[
            "full_fresh_source_material_coverage_ratio_ppm"
        ]
        and required_metadata > 0
        and status
        in {
            "bootstrap-full-review",
            "contract-change-full-review",
            "lineage-checkpoint-full-review",
            "full-fresh-review",
        }
    )


def _professional_completeness_v2_evidence_ready(
    *,
    schema_version: object,
    qualification: object,
    evidence: object,
    required_adjacency_candidate_count: object,
) -> bool:
    """Require the schema-2 qualification and source-bound evidence contract."""

    if schema_version != expert_panel.PROFESSIONAL_COMPLETENESS_SCHEMA_VERSION:
        return False
    qualification_fields = {
        "covered_target_count",
        "required_domain_experts_per_target",
        "required_architecture_experts_per_target",
        "per_target_panel_size",
        "reviewer_pool_size",
        "domain_reviewer_count",
        "architecture_reviewer_count",
    }
    if not isinstance(qualification, dict) or set(qualification) != qualification_fields:
        return False
    reviewer_pool_size = qualification.get("reviewer_pool_size")
    domain_reviewer_count = qualification.get("domain_reviewer_count")
    architecture_reviewer_count = qualification.get("architecture_reviewer_count")
    if (
        qualification.get("covered_target_count")
        != expert_panel.PROFESSIONAL_PACKAGE_COUNT
        or qualification.get("required_domain_experts_per_target") != 2
        or qualification.get("required_architecture_experts_per_target") != 1
        or qualification.get("per_target_panel_size") != expert_panel.PANEL_SIZE
        or type(reviewer_pool_size) is not int
        or reviewer_pool_size < expert_panel.PANEL_SIZE
        or type(domain_reviewer_count) is not int
        or domain_reviewer_count < 2
        or type(architecture_reviewer_count) is not int
        or architecture_reviewer_count < 1
        or domain_reviewer_count + architecture_reviewer_count
        != reviewer_pool_size
    ):
        return False
    expected_evidence_fields = {
        "required_adjacency_candidate_count",
        "criterion_result_count",
        "criterion_anchor_binding_count",
        "criterion_assertion_count",
        "evidence_anchor_count",
        "examined_failure_mode_count",
        "examined_omission_candidate_count",
        "examined_adjacency_count",
        "examined_required_adjacency_count",
        "reviewer_added_adjacency_count",
        "proof_limit_count",
        "qualification_claim_count",
    }
    if not isinstance(evidence, dict) or set(evidence) != expected_evidence_fields:
        return False
    if not all(type(evidence.get(field)) is int for field in expected_evidence_fields):
        return False
    reviewed_votes = expert_panel.PROFESSIONAL_PACKAGE_COUNT * expert_panel.PANEL_SIZE
    criterion_results = reviewed_votes * len(
        expert_panel.PROFESSIONAL_COMPLETENESS_CRITERIA
    )
    if (
        type(required_adjacency_candidate_count) is not int
        or required_adjacency_candidate_count < 0
    ):
        return False
    required_adjacency_reviews = (
        expert_panel.PANEL_SIZE * required_adjacency_candidate_count
    )
    return bool(
        evidence["criterion_result_count"] == criterion_results
        and evidence["required_adjacency_candidate_count"]
        == required_adjacency_candidate_count
        and evidence["criterion_assertion_count"] >= criterion_results
        and evidence["criterion_anchor_binding_count"]
        >= evidence["criterion_assertion_count"]
        and evidence["evidence_anchor_count"] >= reviewed_votes * 2
        and evidence["examined_failure_mode_count"] >= reviewed_votes * 2
        and evidence["examined_omission_candidate_count"] >= reviewed_votes * 2
        and evidence["examined_required_adjacency_count"]
        == required_adjacency_reviews
        and evidence["reviewer_added_adjacency_count"] >= 0
        and evidence["examined_adjacency_count"]
        == evidence["examined_required_adjacency_count"]
        + evidence["reviewer_added_adjacency_count"]
        and evidence["proof_limit_count"] >= reviewed_votes
        and evidence["qualification_claim_count"] >= reviewer_pool_size
    )


def _professional_completeness_v3_evidence_ready(
    *,
    qualification: object,
    evidence: object,
) -> bool:
    qualification_fields = {
        "covered_target_count",
        "required_domain_experts_per_target",
        "required_architecture_experts_per_target",
        "per_target_panel_size",
        "fresh_reviewer_pool_size",
        "effective_domain_vote_count",
        "effective_architecture_vote_count",
    }
    if (
        not isinstance(qualification, dict)
        or set(qualification) != qualification_fields
    ):
        return False
    if (
        qualification["covered_target_count"]
        != expert_panel.PROFESSIONAL_PACKAGE_COUNT
        or qualification["required_domain_experts_per_target"] != 2
        or qualification["required_architecture_experts_per_target"] != 1
        or qualification["per_target_panel_size"] != expert_panel.PANEL_SIZE
        or type(qualification["fresh_reviewer_pool_size"]) is not int
        or qualification["fresh_reviewer_pool_size"] < 0
        or qualification["effective_domain_vote_count"] != 378
        or qualification["effective_architecture_vote_count"] != 189
    ):
        return False
    expected_evidence_fields = set(
        expert_panel.PROFESSIONAL_V3_EVIDENCE_METRIC_FIELDS
    )
    if (
        not isinstance(evidence, dict)
        or set(evidence) != expected_evidence_fields
        or any(type(value) is not int or value < 0 for value in evidence.values())
    ):
        return False
    return bool(
        evidence["target_vote_count"] == 567
        and evidence["criterion_result_count"] == 5670
        and evidence["criterion_assertion_count"] >= 5670
        and evidence["criterion_anchor_binding_count"]
        >= evidence["criterion_assertion_count"]
        and evidence["evidence_anchor_count"] >= 1134
        and evidence["examined_failure_mode_count"] >= 1134
        and evidence["examined_omission_candidate_count"] >= 1134
        and evidence["examined_required_adjacency_count"]
        == 3 * evidence["required_adjacency_candidate_count"]
        and evidence["examined_adjacency_count"]
        == evidence["examined_required_adjacency_count"]
        + evidence["reviewer_added_adjacency_count"]
        and evidence["proof_limit_count"] >= 567
        and evidence["qualification_claim_count"] >= 567
    )


def _professional_completeness_review_axis(
    path: Path,
    *,
    config_bytes: bytes,
    config_fingerprint: str,
    attestation: object,
    current_packet: dict[str, Any],
    evaluation_date: date | None,
    storage_status: str = "current",
    formal: bool = False,
) -> dict[str, Any]:
    field_name = "professional_completeness_review_attestation"
    _value, limitations = _validated_professional_config(path, attestation)
    current_source_fingerprints: dict[str, str] = {}
    required_target_count = len(current_packet["professional_targets"])
    skeleton = _missing_axis_result(
        path=path,
        field_name=field_name,
        panel_kind=expert_panel.PROFESSIONAL_COMPLETENESS_PANEL_KIND,
        scope="professional-skill-packages",
        config_fingerprint=config_fingerprint,
        current_source_fingerprints=current_source_fingerprints,
        current_review_contract_fingerprint=(
            expert_panel._professional_evidence_review_contract_fingerprint()
        ),
        limitations=limitations,
        required_target_count=required_target_count,
    )
    softened = _fixed_axis_noncurrent_result(
        skeleton,
        storage_status=storage_status,
        formal=formal,
    )
    if softened is not None:
        return softened
    try:
        fixed = _apply_fixed_professional_attestation(
            skeleton,
            current_packet=current_packet,
            require_equivalent=False,
        )
    except ValueError as exc:
        if formal:
            raise
        message = str(exc)
        if "missing" in message:
            failure_status = "missing"
        elif "stale" in message or "not current" in message:
            failure_status = "stale"
        else:
            failure_status = "invalid"
        result = _fixed_axis_noncurrent_result(
            skeleton,
            storage_status=failure_status,
            formal=False,
        )
        assert result is not None
        return result
    fixed["limitations"] = [
        *limitations,
        PROFESSIONAL_REVIEW_COST_LIMITATIONS[2],
    ]
    return fixed


def _load_fixed_compact_attestation(
    panel_kind: str,
    *,
    expected_source_fingerprints: dict[str, str] | None = None,
    expected_review_contract_fingerprint: str | None = None,
    expected_readability_current_bindings: dict[
        str, dict[str, dict[str, Any]]
    ] | None = None,
    expected_professional_current_bindings: dict[str, dict[str, Any]] | None = None,
    expected_attestation_sha256: str | None = None,
) -> tuple[dict[str, Any], dict[str, str]] | None:
    relative = expert_panel.panel_attestation.ATTESTATION_PATHS[panel_kind]
    candidate = ROOT / relative
    try:
        bound = expert_panel.reviewer_manifest.read_bound_regular_file(
            candidate,
            max_bytes=expert_panel.panel_attestation.MAX_ATTESTATION_BYTES,
            label=f"fixed {panel_kind} attestation",
        )
    except expert_panel.reviewer_manifest.ManifestError as exc:
        if not candidate.exists() and not candidate.is_symlink():
            return None
        raise ValueError(f"invalid fixed {panel_kind} attestation: {exc}") from exc
    if (
        expected_attestation_sha256 is not None
        and bound.sha256 != expected_attestation_sha256
    ):
        raise ValueError(f"fixed {panel_kind} attestation selector is stale")
    try:
        value = expert_panel.panel_attestation.parse_attestation_bytes(
            bound.raw,
            expected_path=relative,
            expected_source_fingerprints=expected_source_fingerprints,
            expected_review_contract_fingerprint=(
                expected_review_contract_fingerprint
            ),
            expected_readability_current_bindings=(
                expected_readability_current_bindings
            ),
            expected_professional_current_bindings=(
                expected_professional_current_bindings
            ),
        )
    except expert_panel.panel_attestation.AttestationError as exc:
        raise ValueError(f"invalid fixed {panel_kind} attestation: {exc}") from exc
    evidence = {"path": relative, "sha256": bound.sha256}
    _validate_expert_evidence(evidence)
    return value, evidence


def _winning_vote_rationales(
    row: dict[str, Any], *, professional: bool = False
) -> list[dict[str, Any]]:
    winner = row["result"]["winning_disposition"]
    values = []
    for vote in (
        row["votes"]
        if professional
        else row["votes"]
    ):
        disposition = vote["decision"] if professional else vote["disposition"]
        if disposition != winner:
            continue
        voter_id = vote["reviewer"] if professional else vote["voter_id"]
        values.append(
            {
                "voter_id": voter_id,
                "reason_code": vote["reason_code"],
                "rationale": vote["rationale"],
            }
        )
    return values


def _validate_fixed_readability_coverage(
    value: dict[str, Any],
    *,
    required_density: list[dict[str, Any]],
    required_readability: list[dict[str, Any]],
    required_actionability: list[dict[str, Any]],
    expected_review_contract_fingerprint: str,
) -> None:
    if value.get("review_contract_fingerprint") != (
        expected_review_contract_fingerprint
    ):
        raise ValueError("fixed readability attestation review contract is stale")
    actual_by_category = {
        category: [
            row for row in value.get("findings", [])
            if isinstance(row, dict) and row.get("category") == category
        ]
        for category in ("content", "readability", "actionability")
    }
    if sum(len(rows) for rows in actual_by_category.values()) != len(
        value.get("findings", [])
    ):
        raise ValueError("fixed readability attestation category is invalid")
    comparisons = (
        (
            "content",
            [(row["path"],) for row in required_density],
            [
                (row.get("target_id"),)
                for row in actual_by_category["content"]
            ],
        ),
        (
            "readability",
            [(row["document_id"],) for row in required_readability],
            [
                (row.get("target_id"),)
                for row in actual_by_category["readability"]
            ],
        ),
        (
            "actionability",
            [(row["target_id"],) for row in required_actionability],
            [
                (row.get("target_id"),)
                for row in actual_by_category["actionability"]
            ],
        ),
    )
    for category, expected, actual in comparisons:
        if actual != sorted(set(actual)) or actual != sorted(expected):
            raise ValueError(
                f"fixed readability attestation {category} coverage is stale"
            )


def _apply_fixed_readability_attestation(
    legacy: dict[str, Any],
    *,
    required_density: list[dict[str, Any]],
    required_readability: list[dict[str, Any]],
    required_actionability: list[dict[str, Any]],
    expected_review_contract_fingerprint: str,
    expected_readability_current_bindings: dict[
        str, dict[str, dict[str, Any]]
    ],
    require_equivalent: bool = True,
) -> dict[str, Any]:
    loaded = _load_fixed_compact_attestation(
        expert_panel.READABILITY_PANEL_KIND,
        expected_source_fingerprints=legacy["current_source_fingerprints"],
        expected_review_contract_fingerprint=(
            expected_review_contract_fingerprint
        ),
        expected_readability_current_bindings=(
            expected_readability_current_bindings
        ),
    )
    if loaded is None:
        raise ValueError("selected fixed readability attestation is missing")
    value, evidence = loaded
    _validate_fixed_readability_coverage(
        value,
        required_density=required_density,
        required_readability=required_readability,
        required_actionability=required_actionability,
        expected_review_contract_fingerprint=(
            expected_review_contract_fingerprint
        ),
    )
    actionability_targets = {
        row["target_id"]: row
        for row in required_actionability
    }
    density_targets = {row["path"]: row for row in required_density}
    readability_targets = {
        row["document_id"]: row for row in required_readability
    }
    if (
        len(actionability_targets) != len(required_actionability)
        or len(density_targets) != len(required_density)
        or len(readability_targets) != len(required_readability)
    ):
        raise ValueError("fixed readability current target identities are duplicated")
    current_actionability = expected_readability_current_bindings.get(
        "actionability"
    )
    if (
        not isinstance(current_actionability, dict)
        or set(current_actionability) != set(actionability_targets)
    ):
        raise ValueError(
            "fixed readability actionability authority coverage is stale"
        )
    density = []
    readability = []
    actionability = []
    for row in value["findings"]:
        if row["category"] == "content":
            target = density_targets[row["target_id"]]
            rationales = _winning_vote_rationales(row)
            density.append(
                {
                    "path": row["target_id"],
                    "classification": target["classification"],
                    "disposition": row["result"]["winning_disposition"],
                    "rationale": "Majority decision: "
                    + " ".join(item["rationale"] for item in rationales),
                }
            )
        elif row["category"] == "readability":
            target = readability_targets[row["target_id"]]
            winning_voters = set(row["result"]["supporting_voters"])
            rationales = [
                vote["rationale"]
                for finding in row["finding_reviews"]
                for vote in finding["votes"]
                if vote["voter_id"] in winning_voters
            ]
            readability.append(
                {
                    "document_id": row["target_id"],
                    "highest_band": target["highest_band"],
                    "disposition": row["result"]["winning_disposition"],
                    "rationale": "Majority decision: " + " ".join(rationales),
                }
            )
        else:
            target = actionability_targets.get(row["target_id"])
            authority = current_actionability.get(row["target_id"])
            current_target = (
                authority.get("target") if isinstance(authority, dict) else None
            )
            if (
                target is None
                or not isinstance(current_target, dict)
                or authority.get("category") != "actionability"
                or authority.get("target_id") != row["target_id"]
                or any(
                    current_target.get(field) != target[field]
                    for field in (
                        "target_id",
                        "skill_id",
                        "path",
                        "front_loaded_action_score",
                    )
                )
            ):
                raise ValueError(
                    "fixed readability attestation actionability target is stale"
                )
            window = current_target.get("front_window")
            if not isinstance(window, dict) or not isinstance(
                window.get("lines"), list
            ):
                raise ValueError(
                    "fixed readability actionability authority window is invalid"
                )
            current_evidence = [
                {
                    "line": evidence_row["line"],
                    "source_line": evidence_row["text"],
                    "claim": evidence_row["text"],
                }
                for evidence_row in window["lines"]
                if isinstance(evidence_row, dict)
                and type(evidence_row.get("line")) is int
                and isinstance(evidence_row.get("text"), str)
                and evidence_row["text"].strip()
                and expert_panel._actionability_window_line_is_substantive(
                    window, evidence_row["line"]
                )
            ]
            if not current_evidence:
                raise ValueError(
                    "fixed readability actionability authority has no substantive evidence"
                )
            rationales = _winning_vote_rationales(row)
            actionability.append(
                {
                    "target_id": row["target_id"],
                    "skill_id": target["skill_id"],
                    "path": target["path"],
                    "front_loaded_action_score": target[
                        "front_loaded_action_score"
                    ],
                    "disposition": row["result"]["winning_disposition"],
                    "reason_codes": sorted(
                        {item["reason_code"] for item in rationales}
                    ),
                    "rationale": "Majority decision: "
                    + " ".join(item["rationale"] for item in rationales),
                    "evidence": current_evidence,
                }
            )
    projection = {
        "density_dispositions": density,
        "readability_dispositions": readability,
        "actionability_dispositions": actionability,
    }
    for key, rows in projection.items():
        if require_equivalent and rows != legacy[key]:
            raise ValueError(
                f"fixed readability attestation is not field-equivalent for {key}"
            )
    updated = copy.deepcopy(legacy)
    tracked = sum(
        row["disposition"] == "tracked-tightening"
        for row in (*density, *readability)
    )
    accepted_actionability = sum(
        row["disposition"] == "accepted-current-actionability"
        for row in actionability
    )
    false_positives = sum(
        row["disposition"] == "detector-false-positive"
        for row in actionability
    )
    rewrites = sum(
        row["disposition"] == "rewrite-required"
        for row in actionability
    )
    updated.update(
        {
            "decision_complete": True,
            "storage_current": True,
            "source_current": True,
            "panel_review_id": value["review_id"],
            "panel_size": expert_panel.PANEL_SIZE,
            "attestation_source": evidence["path"],
            "attestation_schema_version": 5,
            "source_fingerprints": value["source_fingerprints"],
            "attested_by": f"expert-panel:{value['review_id']}",
            "attested_on": value["decided_on"],
            "evidence": [evidence],
            "panel_artifact_schema_version": (
                expert_panel.READABILITY_SCHEMA_VERSION
            ),
            **projection,
            "applied_density_disposition_count": len(density),
            "applied_readability_disposition_count": len(readability),
            "applied_actionability_disposition_count": len(actionability),
            "accepted_current_actionability_count": accepted_actionability,
            "detector_false_positive_count": false_positives,
            "rewrite_required_count": rewrites,
            "tracked_tightening_count": tracked,
        }
    )
    updated["accepted_for_formal"] = bool(
        value["verdict"] == "accepted-current-readability"
        and updated["blocker_count"] == 0
        and updated["tracked_tightening_count"] == 0
        and updated["detector_false_positive_count"] == 0
        and updated["rewrite_required_count"] == 0
    )
    updated["attestation_status"] = (
        "panel-majority-current"
        if updated["accepted_for_formal"]
        else legacy["attestation_status"]
    )
    return updated


def _apply_fixed_professional_attestation(
    legacy: dict[str, Any], *, current_packet: dict[str, Any],
    require_equivalent: bool = True,
) -> dict[str, Any]:
    fixed_path = (
        ROOT
        / expert_panel.panel_attestation.PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH
    )
    authenticated_bound = expert_panel.reviewer_manifest.read_bound_regular_file(
        fixed_path,
        max_bytes=expert_panel.panel_attestation.MAX_ATTESTATION_BYTES,
        label="fixed Professional attestation authority",
    )
    authenticated_value = (
        expert_panel.panel_attestation.parse_attestation_storage_selector_bytes(
            authenticated_bound.raw
        )
    )
    authenticated_claims = (
        expert_panel._professional_authenticated_claims_from_findings(
            authenticated_value["findings"]
        )
    )
    current_authority = expert_panel._professional_attestation_current_bindings(
        current_packet,
        authenticated_claims=authenticated_claims,
    )
    loaded = _load_fixed_compact_attestation(
        expert_panel.PROFESSIONAL_COMPLETENESS_PANEL_KIND,
        expected_review_contract_fingerprint=current_packet[
            "review_contract_fingerprint"
        ],
        expected_professional_current_bindings=current_authority,
    )
    if loaded is None:
        raise ValueError("selected fixed Professional attestation is missing")
    value, evidence = loaded
    try:
        expert_panel.validate_professional_attestation_current(
            value,
            current_packet=current_packet,
            authenticated_claims=authenticated_claims,
        )
    except expert_panel.PanelReviewError as exc:
        raise ValueError(
            f"fixed Professional attestation is not current: {exc}"
        ) from exc
    dispositions = []
    for row in value["findings"]:
        rationales = _winning_vote_rationales(row, professional=True)
        dispositions.append(
            {
                "skill_id": row["skill_id"],
                "package_material_binding": row[
                    "package_material_binding"
                ],
                "review_unit_binding": row["review_unit_binding"],
                "disposition": row["result"]["final_disposition"],
                "majority_disposition": row["result"][
                    "winning_disposition"
                ],
                "domain_critical_defects": row["result"][
                    "domain_critical_defects"
                ],
                "ordinary_criterion_disposition": row["result"][
                    "ordinary_criterion_disposition"
                ],
                "ordinary_criterion_defects": row["result"][
                    "ordinary_criterion_defects"
                ],
                "reason_codes": sorted(
                    {item["reason_code"] for item in rationales}
                ),
                "rationales": rationales,
                "review_dependencies": row["result"]["review_dependencies"],
                "evidence_metrics": row["result"]["evidence_metrics"],
                "provenance": copy.deepcopy(row["provenance"]),
                "target_decision_fingerprint": row["provenance"]["origin"][
                    "origin_verdict_digest"
                ],
            }
        )
    legacy_projection = [
        {
            key: row[key]
            for key in (
                "skill_id",
                "package_material_binding",
                "review_unit_binding",
                "disposition",
                "majority_disposition",
                "domain_critical_defects",
                "ordinary_criterion_disposition",
                "ordinary_criterion_defects",
                "review_dependencies",
                "evidence_metrics",
            )
        }
        for row in legacy["professional_dispositions"]
    ]
    fixed_projection = [
        {key: row[key] for key in legacy_projection[0]}
        for row in dispositions
    ] if legacy_projection else []
    if require_equivalent and fixed_projection != legacy_projection:
        raise ValueError(
            "fixed Professional attestation is not field-equivalent to configured legacy evidence"
        )
    partition = value["summary"]["partition"]
    qualification = value["summary"]["qualification"]
    review_cost = value["summary"]["review_cost"]
    evidence_summary = value["summary"]["evidence"]["effective"]
    accepted = sum(
        row["disposition"] == "accepted-current-professional-completeness"
        for row in dispositions
    )
    corrections = sum(
        row["disposition"] == "requires-professional-correction"
        for row in dispositions
    )
    unresolved = sum(
        row["disposition"] == expert_panel.PROFESSIONAL_UNRESOLVED_DISPOSITION
        for row in dispositions
    )
    qualification_summary = {
        "covered_target_count": qualification["effective_covered_target_count"],
        "required_domain_experts_per_target": 2,
        "required_architecture_experts_per_target": 1,
        "per_target_panel_size": expert_panel.PANEL_SIZE,
        "fresh_reviewer_pool_size": qualification["fresh_reviewer_pool_size"],
        "effective_domain_vote_count": 2 * len(dispositions),
        "effective_architecture_vote_count": len(dispositions),
    }
    evidence_current = _professional_completeness_v3_evidence_ready(
        qualification=qualification_summary,
        evidence=evidence_summary,
    )
    review_cost_current = _professional_review_cost_policy_satisfied(
        review_cost,
        fresh_target_count=partition["fresh_target_count"],
        carried_forward_target_count=partition["carried_target_count"],
    )
    accepted_for_formal = bool(
        value["verdict"] == "accepted-current-professional-completeness"
        and len(dispositions) == expert_panel.PROFESSIONAL_PACKAGE_COUNT
        and corrections == 0
        and unresolved == 0
        and evidence_current
        and review_cost_current
    )
    updated = copy.deepcopy(legacy)
    updated.update(
        {
            "decision_complete": True,
            "storage_current": True,
            "source_current": True,
            "accepted_for_formal": accepted_for_formal,
            "decision_method": (
                expert_panel.PROFESSIONAL_COMPLETENESS_INCREMENTAL_DECISION_METHOD
            ),
            "panel_review_id": value["review_id"],
            "panel_size": expert_panel.PANEL_SIZE,
            "reviewer_pool_size": len(value["reviewers"]),
            "attestation_status": (
                "panel-majority-current"
                if accepted_for_formal
                else "panel-majority-incomplete-coverage"
            ),
            "attestation_source": evidence["path"],
            "attestation_schema_version": 5,
            "source_fingerprints": {},
            "attested_by": f"expert-panel:{value['review_id']}",
            "attested_on": value["decided_on"],
            "evidence": [evidence],
            "panel_artifact_schema_version": (
                expert_panel.PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
            ),
            "evidence_contract_satisfied": evidence_current,
            "qualification_summary": qualification_summary,
            "evidence_summary": evidence_summary,
            "professional_dispositions": dispositions,
            "review_contract_fingerprint": value[
                "review_contract_fingerprint"
            ],
            "current_review_contract_fingerprint": current_packet[
                "review_contract_fingerprint"
            ],
            "review_contract_current": True,
            "review_plan_fingerprint": None,
            "current_review_plan_fingerprint": None,
            "review_plan_current": True,
            "review_binding_current": True,
            "provenance_current": True,
            "round_lifecycle_current": True,
            "round_lifecycle": {
                "status": "fixed-attestation-current",
                "round_count": 1,
                "chain_depth": review_cost["plan_lineage_depth"],
                "head_decision": None,
                "current_decision_is_head": True,
                "errors": [],
                "limitations": [PROFESSIONAL_REVIEW_COST_LIMITATIONS[2]],
            },
            "review_cost_current": review_cost_current,
            "review_cost": review_cost,
            "fresh_target_count": partition["fresh_target_count"],
            "carried_forward_target_count": partition["carried_target_count"],
            "applied_target_count": len(dispositions),
            "accepted_current_count": accepted,
            "correction_count": corrections,
            "unresolved_professional_disagreement_count": unresolved,
        }
    )
    return updated


def _dual_expert_reviews_from_data(
    path: Path,
    *,
    data: dict[str, Any],
    config_bytes: bytes,
    reference_fingerprint: str,
    root_fingerprint: str,
    ai_readability_fingerprint: str,
    content_skills: object,
    readability_content: object,
    current_completeness_packet: dict[str, Any],
    evaluation_date: date | None,
    content_audit: object = None,
    skill_detector_fingerprint: str | None = None,
    storage_statuses: dict[str, str] | None = None,
    formal: bool = False,
) -> dict[str, Any]:
    if data.get("schema_version") != 5 or set(data) != DUAL_PANEL_CONFIG_FIELDS:
        raise ValueError(
            f"{_rel(path)}: dual expert review config must match schema 5"
        )
    if not isinstance(data.get("review_owner"), str) or not data["review_owner"].strip():
        raise ValueError(f"{_rel(path)}: review_owner must be a non-blank string")
    _validated_iso_date(
        data.get("reviewed_at"),
        label=f"{_rel(path)}: reviewed_at",
        evaluation_date=evaluation_date,
    )
    if not isinstance(data.get("decisions"), list):
        raise ValueError(f"{_rel(path)}: decisions must be a list")
    config_fingerprint = hashlib.sha256(config_bytes).hexdigest()
    readability = _readability_review_axis(
        path,
        config_bytes=config_bytes,
        config_fingerprint=config_fingerprint,
        attestation=data["readability_review_attestation"],
        content_skills=content_skills,
        readability_content=readability_content,
        content_audit=content_audit,
        evaluation_date=evaluation_date,
        storage_status=(storage_statuses or {}).get(
            expert_panel.READABILITY_PANEL_KIND,
            "current",
        ),
        formal=formal,
    )
    completeness = _professional_completeness_review_axis(
        path,
        config_bytes=config_bytes,
        config_fingerprint=config_fingerprint,
        attestation=data["professional_completeness_review_attestation"],
        current_packet=current_completeness_packet,
        evaluation_date=evaluation_date,
        storage_status=(storage_statuses or {}).get(
            expert_panel.PROFESSIONAL_COMPLETENESS_PANEL_KIND,
            "current",
        ),
        formal=formal,
    )
    return {
        "deprecated_legacy_attestation": False,
        "readability": readability,
        "professional_completeness": completeness,
        # Compatibility projection only.  Formal predicates must never consume it.
        "deprecated_expert_content_review_complete": False,
    }


def _normalized_expert_reviews(
    legacy_review: dict[str, Any],
) -> dict[str, Any]:
    """Expose the legacy attestation as a non-authoritative readability axis.

    This is a migration adapter only.  The old combined attestation never
    satisfies either new formal axis, even when its historical storage binding
    is current.
    """

    content_dispositions = list(legacy_review.get("content_dispositions", []))
    readability_dispositions = list(
        legacy_review.get("readability_dispositions", [])
    )
    tracked_tightening_count = sum(
        item.get("disposition") == "tracked-tightening"
        for item in (*content_dispositions, *readability_dispositions)
        if isinstance(item, dict)
    )
    current_fingerprints = dict(legacy_review.get("source_fingerprints", {}))
    readability = {
        "scope": "ai-readability-and-density",
        "panel_kind": expert_panel.READABILITY_PANEL_KIND,
        "decision_complete": legacy_review.get("panel_decision_complete") is True,
        "storage_current": legacy_review.get("storage_current") is True,
        "source_current": legacy_review.get("expert_content_review_complete") is True,
        "accepted_for_formal": False,
        "decision_method": legacy_review.get("decision_method"),
        "panel_review_id": legacy_review.get("panel_review_id"),
        "panel_artifact_schema_version": None,
        "panel_size": legacy_review.get("panel_size", 0),
        "attestation_status": "deprecated-combined-attestation",
        "attestation_source": legacy_review.get("attestation_source"),
        "attestation_schema_version": legacy_review.get(
            "attestation_schema_version"
        ),
        "attestation_config_fingerprint": legacy_review.get(
            "attestation_config_fingerprint"
        ),
        "source_fingerprints": current_fingerprints,
        "current_source_fingerprints": current_fingerprints,
        "attested_by": legacy_review.get("attested_by"),
        "attested_on": legacy_review.get("attested_on"),
        "evidence": list(legacy_review.get("evidence", [])),
        "density_dispositions": content_dispositions,
        "readability_dispositions": readability_dispositions,
        "actionability_dispositions": [],
        "required_density_disposition_count": legacy_review.get(
            "required_content_disposition_count", 0
        ),
        "applied_density_disposition_count": legacy_review.get(
            "applied_content_disposition_count", 0
        ),
        "required_readability_disposition_count": legacy_review.get(
            "required_readability_disposition_count", 0
        ),
        "applied_readability_disposition_count": legacy_review.get(
            "applied_readability_disposition_count", 0
        ),
        "required_actionability_disposition_count": None,
        "applied_actionability_disposition_count": 0,
        "accepted_current_actionability_count": None,
        "detector_false_positive_count": None,
        "rewrite_required_count": None,
        "tracked_tightening_count": tracked_tightening_count,
        "blocker_count": (
            int(legacy_review.get("content_blocker_count", 0))
            + int(legacy_review.get("readability_blocker_count", 0))
        ),
        "limitations": [
            *list(legacy_review.get("limitations", [])),
            "Deprecated combined expert attestation is historical evidence only; "
            "it cannot satisfy the independent readability formal gate.",
        ],
    }
    professional_completeness = {
        "scope": "professional-skill-packages",
        "panel_kind": expert_panel.PROFESSIONAL_COMPLETENESS_PANEL_KIND,
        "decision_complete": False,
        "storage_current": False,
        "source_current": False,
        "accepted_for_formal": False,
        "decision_method": expert_panel.PROFESSIONAL_COMPLETENESS_DECISION_METHOD,
        "panel_review_id": None,
        "panel_size": 0,
        "reviewer_pool_size": 0,
        "attestation_status": "missing-evidence",
        "attestation_source": None,
        "attestation_schema_version": 5,
        "attestation_config_fingerprint": legacy_review.get(
            "attestation_config_fingerprint"
        ),
        "source_fingerprints": {"professional_packages": None},
        "current_source_fingerprints": {"professional_packages": None},
        "attested_by": None,
        "attested_on": None,
        "evidence": [],
        "panel_artifact_schema_version": None,
        "evidence_contract_satisfied": False,
        "qualification_summary": None,
        "evidence_summary": None,
        "review_contract_fingerprint": None,
        "current_review_contract_fingerprint": None,
        "review_contract_current": False,
        "review_plan_fingerprint": None,
        "current_review_plan_fingerprint": None,
        "review_plan_current": False,
        "review_binding_current": False,
        "provenance_current": False,
        "round_lifecycle_current": False,
        "round_lifecycle": {
            "status": "no-schema3-current-decision",
            "round_count": 0,
            "chain_depth": 0,
            "head_decision": None,
            "current_decision_is_head": False,
            "errors": [],
            "limitations": [PROFESSIONAL_REVIEW_COST_LIMITATIONS[2]],
        },
        "review_cost_current": False,
        "review_cost": None,
        "professional_dispositions": [],
        "required_target_count": expert_panel.PROFESSIONAL_PACKAGE_COUNT,
        "fresh_target_count": 0,
        "carried_forward_target_count": 0,
        "applied_target_count": 0,
        "accepted_current_count": None,
        "correction_count": None,
        "unresolved_professional_disagreement_count": None,
        "limitations": [
            "No independent professional-completeness panel evidence is configured."
        ],
    }
    return {
        "deprecated_legacy_attestation": True,
        "readability": readability,
        "professional_completeness": professional_completeness,
        # Compatibility projection only.  Formal predicates must never consume it.
        "deprecated_expert_content_review_complete": False,
    }


@lru_cache(maxsize=1)
def _current_professional_completeness_packet() -> dict[str, Any]:
    return expert_panel.prepare_professional_completeness_packet_v3(
        review_id="current-professional-completeness-contract",
        created_on="2000-01-01",
        root=ROOT,
        validation_root=ROOT,
    )


_ProfessionalReviewCostBlock = tuple[str, int]


@dataclass(frozen=True)
class _ProfessionalReviewCostBlockIndex:
    """Packet-bound, recursively immutable canonical cost blocks."""

    review_contract_fingerprint: str
    assigned_skill_ids: tuple[str, ...]
    base_blocks_by_digest: Mapping[str, int]
    material_blocks_by_skill_id: Mapping[str, _ProfessionalReviewCostBlock]
    material_skill_ids_by_target: Mapping[str, tuple[str, ...]]
    discovery_target_blocks_by_skill_id: Mapping[
        str, _ProfessionalReviewCostBlock
    ]
    final_target_blocks_by_skill_id: Mapping[
        str, _ProfessionalReviewCostBlock
    ]
    request_closure_blocks_by_skill_id: Mapping[
        str, _ProfessionalReviewCostBlock
    ]
    reviewer_added_request_blocks_by_target: Mapping[
        str, tuple[_ProfessionalReviewCostBlock, ...]
    ]


def _professional_review_cost_block(value: dict[str, Any]) -> (
    _ProfessionalReviewCostBlock
):
    block = expert_panel._professional_v3_input_block(value)
    return block["sha256"], block["canonical_json_bytes_proxy"]


def _professional_review_cost_row_index(
    rows: object,
    *,
    label: str,
) -> dict[str, dict[str, Any]]:
    if not isinstance(rows, list):
        raise ValueError(f"{label} must be an array")
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"{label} entries must be objects")
        skill_id = row.get("skill_id")
        if not isinstance(skill_id, str) or not skill_id:
            raise ValueError(f"{label} entries must name a Skill")
        if skill_id in result:
            raise ValueError(f"{label} entries must be Skill-unique")
        result[skill_id] = row
    return result


def _professional_review_cost_block_index(
    *,
    review_contract_fingerprint: str,
    discovery_projection: dict[str, Any],
    reviewer_added_requests: list[dict[str, Any]],
    final_projection: dict[str, Any],
) -> _ProfessionalReviewCostBlockIndex:
    """Index the effective-input-block semantics without per-case projection."""

    assigned_raw = discovery_projection.get("assigned_fresh_target_ids")
    final_assigned = final_projection.get("assigned_fresh_target_ids")
    if (
        not isinstance(assigned_raw, list)
        or not assigned_raw
        or assigned_raw != sorted(set(assigned_raw))
        or final_assigned != assigned_raw
    ):
        raise ValueError(
            "professional review cost projections require one identical canonical assignment"
        )
    assigned = tuple(assigned_raw)
    discovery_targets = _professional_review_cost_row_index(
        discovery_projection.get("targets"),
        label="professional review discovery targets",
    )
    final_targets = _professional_review_cost_row_index(
        final_projection.get("targets"),
        label="professional review final targets",
    )
    if set(discovery_targets) != set(assigned) or set(final_targets) != set(
        assigned
    ):
        raise ValueError(
            "professional review cost target projections do not match the assignment"
        )

    discovery_material = _professional_review_cost_row_index(
        discovery_projection.get("material_catalog"),
        label="professional review discovery material catalog",
    )
    final_material = _professional_review_cost_row_index(
        final_projection.get("material_catalog"),
        label="professional review final material catalog",
    )
    material_rows = dict(discovery_material)
    for skill_id, row in final_material.items():
        existing = material_rows.get(skill_id)
        if existing is not None and existing != row:
            raise ValueError(
                "professional review cost material differs across review stages"
            )
        material_rows[skill_id] = row
    boundary_rows = _professional_review_cost_row_index(
        discovery_projection.get("boundary_catalog"),
        label="professional review discovery boundary catalog",
    )

    canonical_sizes: dict[str, int] = {}

    def register(block: _ProfessionalReviewCostBlock) -> None:
        digest, size = block
        existing = canonical_sizes.get(digest)
        if existing is not None and existing != size:
            raise ValueError(
                "professional review cost input block digest has conflicting canonical size"
            )
        canonical_sizes[digest] = size

    review_binding = _professional_review_cost_block(
        {
            "block_kind": "review-binding",
            "review_contract_fingerprint": review_contract_fingerprint,
        }
    )
    register(review_binding)
    base_blocks_by_digest = {review_binding[0]: review_binding[1]}
    for row in boundary_rows.values():
        block = _professional_review_cost_block(
            {"block_kind": "candidate-boundary", "value": row}
        )
        register(block)
        base_blocks_by_digest[block[0]] = block[1]

    material_blocks: dict[str, _ProfessionalReviewCostBlock] = {}
    for skill_id, row in material_rows.items():
        block = _professional_review_cost_block(
            {"block_kind": "source-material", "value": row}
        )
        register(block)
        material_blocks[skill_id] = block

    discovery_target_blocks: dict[str, _ProfessionalReviewCostBlock] = {}
    final_target_blocks: dict[str, _ProfessionalReviewCostBlock] = {}
    request_closure_blocks: dict[str, _ProfessionalReviewCostBlock] = {}
    material_skill_ids_by_target: dict[str, tuple[str, ...]] = {}
    for skill_id in assigned:
        discovery_row = discovery_targets[skill_id]
        final_row = final_targets[skill_id]
        discovery_block = _professional_review_cost_block(
            {"block_kind": "discovery-target", "value": discovery_row}
        )
        final_block = _professional_review_cost_block(
            {"block_kind": "final-review-target", "value": final_row}
        )
        closure_block = _professional_review_cost_block(
            {
                "block_kind": "candidate-request-closure",
                "target_skill_id": skill_id,
            }
        )
        for block in (discovery_block, final_block, closure_block):
            register(block)
        discovery_target_blocks[skill_id] = discovery_block
        final_target_blocks[skill_id] = final_block
        request_closure_blocks[skill_id] = closure_block

        discovery_manifest = discovery_row.get(
            "required_candidate_material_manifest"
        )
        final_manifest = final_row.get("candidate_material_manifest")
        if not isinstance(discovery_manifest, list) or not isinstance(
            final_manifest, list
        ):
            raise ValueError(
                "professional review cost target material manifests are invalid"
            )
        material_ids = {skill_id}
        for manifest in (discovery_manifest, final_manifest):
            for item in manifest:
                candidate_id = (
                    item.get("skill_id") if isinstance(item, dict) else None
                )
                if not isinstance(candidate_id, str) or not candidate_id:
                    raise ValueError(
                        "professional review cost target material manifest is invalid"
                    )
                material_ids.add(candidate_id)
        unknown_material = sorted(material_ids - set(material_blocks))
        if unknown_material:
            raise ValueError(
                "professional review cost target material is absent from the canonical catalog"
            )
        material_skill_ids_by_target[skill_id] = tuple(sorted(material_ids))

    request_blocks_by_target: dict[
        str, list[_ProfessionalReviewCostBlock]
    ] = {skill_id: [] for skill_id in assigned}
    for row in reviewer_added_requests:
        if not isinstance(row, dict):
            raise ValueError(
                "professional review cost reviewer-added requests must be objects"
            )
        target_id = row.get("target_skill_id")
        if target_id not in request_blocks_by_target:
            raise ValueError(
                "professional review cost reviewer-added request names an unassigned target"
            )
        block = _professional_review_cost_block(
            {"block_kind": "reviewer-added-request", "value": row}
        )
        register(block)
        request_blocks_by_target[target_id].append(block)

    return _ProfessionalReviewCostBlockIndex(
        review_contract_fingerprint=review_contract_fingerprint,
        assigned_skill_ids=assigned,
        base_blocks_by_digest=MappingProxyType(
            dict(sorted(base_blocks_by_digest.items()))
        ),
        material_blocks_by_skill_id=MappingProxyType(
            dict(sorted(material_blocks.items()))
        ),
        material_skill_ids_by_target=MappingProxyType(
            dict(sorted(material_skill_ids_by_target.items()))
        ),
        discovery_target_blocks_by_skill_id=MappingProxyType(
            dict(sorted(discovery_target_blocks.items()))
        ),
        final_target_blocks_by_skill_id=MappingProxyType(
            dict(sorted(final_target_blocks.items()))
        ),
        request_closure_blocks_by_skill_id=MappingProxyType(
            dict(sorted(request_closure_blocks.items()))
        ),
        reviewer_added_request_blocks_by_target=MappingProxyType(
            {
                skill_id: tuple(sorted(blocks))
                for skill_id, blocks in sorted(
                    request_blocks_by_target.items()
                )
            }
        ),
    )


def _professional_review_cost_case_input_blocks(
    index: _ProfessionalReviewCostBlockIndex,
    *,
    fresh_skill_ids: Sequence[str],
) -> list[dict[str, Any]]:
    """Select one assignment's exact digest union from the canonical index."""

    fresh = sorted(fresh_skill_ids)
    if not fresh or fresh != sorted(set(fresh)):
        raise ValueError(
            "professional review cost case requires unique fresh target IDs"
        )
    unknown = sorted(set(fresh) - set(index.assigned_skill_ids))
    if unknown:
        raise ValueError(
            "professional review cost case names unknown fresh targets: "
            + ", ".join(unknown)
        )
    selected = dict(index.base_blocks_by_digest)

    def select(block: _ProfessionalReviewCostBlock) -> None:
        digest, size = block
        existing = selected.get(digest)
        if existing is not None and existing != size:
            raise ValueError(
                "professional review cost selected block digest has conflicting canonical size"
            )
        selected[digest] = size

    for skill_id in fresh:
        for material_id in index.material_skill_ids_by_target[skill_id]:
            select(index.material_blocks_by_skill_id[material_id])
        select(index.discovery_target_blocks_by_skill_id[skill_id])
        select(index.final_target_blocks_by_skill_id[skill_id])
        select(index.request_closure_blocks_by_skill_id[skill_id])
        for block in index.reviewer_added_request_blocks_by_target[skill_id]:
            select(block)
    return [
        {"sha256": digest, "canonical_json_bytes_proxy": selected[digest]}
        for digest in sorted(selected)
    ]


def _professional_review_cost_case_bytes(
    index: _ProfessionalReviewCostBlockIndex,
    *,
    fresh_skill_ids: Sequence[str],
    semantic_vote_multiplicity: int = expert_panel.PANEL_SIZE,
) -> int:
    """Apply the schema-3 maximum-three semantic vote multiplicity."""

    if (
        type(semantic_vote_multiplicity) is not int
        or semantic_vote_multiplicity < 1
        or semantic_vote_multiplicity > expert_panel.PANEL_SIZE
    ):
        raise ValueError(
            "professional review cost semantic vote multiplicity must be between one and three"
        )
    blocks = _professional_review_cost_case_input_blocks(
        index,
        fresh_skill_ids=fresh_skill_ids,
    )
    return semantic_vote_multiplicity * sum(
        row["canonical_json_bytes_proxy"] for row in blocks
    )


def _calculate_professional_review_cost_fixtures() -> dict[str, Any]:
    """Calculate deterministic exact-carry sensitivity before lock comparison."""

    packet = _current_professional_completeness_packet()
    state = expert_panel._professional_v3_packet_state(
        packet,
        validation_root=ROOT,
        artifact_path=None,
        validate_baseline=False,
    )
    bindings = state["bindings"]
    target_ids = sorted(bindings)
    if len(target_ids) != expert_panel.PROFESSIONAL_PACKAGE_COUNT:
        raise ValueError("professional review cost fixture requires 189 targets")
    reverse_dependencies = {skill_id: {skill_id} for skill_id in target_ids}
    for target_id, binding in bindings.items():
        for candidate_id in binding["dependency_material_bindings"]:
            reverse_dependencies[candidate_id].add(target_id)

    full_discovery_projection = (
        expert_panel._professional_v3_discovery_projection_from_packet(
            packet=packet,
            assigned_skill_ids=target_ids,
            bindings=bindings,
        )
    )
    full_final_projection = (
        expert_panel._professional_v3_capsule_projection_from_packet(
            packet=packet,
            assigned_skill_ids=target_ids,
            reviewer_added_requests_by_target=None,
            bindings=bindings,
        )
    )
    block_index = _professional_review_cost_block_index(
        review_contract_fingerprint=packet[
            "review_contract_fingerprint"
        ],
        discovery_projection=full_discovery_projection,
        reviewer_added_requests=[],
        final_projection=full_final_projection,
    )
    full_round_bytes = _professional_review_cost_case_bytes(
        block_index,
        fresh_skill_ids=target_ids,
    )
    cases: list[dict[str, Any]] = []
    for changed_skill_id in target_ids:
        fresh_ids = sorted(reverse_dependencies[changed_skill_id])
        local_round_bytes = _professional_review_cost_case_bytes(
            block_index,
            fresh_skill_ids=fresh_ids,
        )
        cases.append(
            {
                "skill_id": changed_skill_id,
                "fresh_target_count": len(fresh_ids),
                "carried_forward_target_count": len(target_ids)
                - len(fresh_ids),
                "canonical_capsule_input_bytes_proxy": local_round_bytes,
                "input_ratio_ppm": (
                    local_round_bytes * 1_000_000 // full_round_bytes
                ),
            }
        )
    fresh_counts = sorted(row["fresh_target_count"] for row in cases)
    ratios = sorted(row["input_ratio_ppm"] for row in cases)
    p95_index = (95 * len(cases) + 99) // 100 - 1
    named = next(
        row for row in cases if row["skill_id"] == "acceptance-criteria-builder"
    )
    sensitivity = {
        "case_count": len(cases),
        "full_rereview_deduplicated_capsule_input_bytes_proxy": (
            full_round_bytes
        ),
        "fresh_target_count": {
            "min": fresh_counts[0],
            "sum": sum(fresh_counts),
            "mean_milli": sum(fresh_counts) * 1000 // len(fresh_counts),
            "p95": fresh_counts[p95_index],
            "max": fresh_counts[-1],
        },
        "input_ratio_ppm": {
            "min": ratios[0],
            "sum": sum(ratios),
            "mean": sum(ratios) // len(ratios),
            "p95": ratios[p95_index],
            "max": ratios[-1],
        },
        "named_isolated_case": dict(named),
    }
    dependency_fixture: dict[str, dict[str, Any]] = {}
    for skill_id, binding in bindings.items():
        required_ids = sorted(binding["dependency_material_bindings"])
        dependency_fixture[skill_id] = {
            "skill_id": skill_id,
            "final_disposition": (
                "accepted-current-professional-completeness"
            ),
            "evidence_complete": True,
            "prior_target_vote_count": 3,
            "required_candidate_ids": required_ids,
            "reviewer_added_candidate_ids_union": [],
            "dependency_candidate_ids": required_ids,
        }
    adjacency_target = "acceptance-criteria-builder"
    prior_snapshot = copy.deepcopy(state["snapshot"])
    prior_snapshot["targets"][adjacency_target][
        "review_unit_binding"
    ] = hashlib.sha256(
        b"representative-prior-routing-adjacency"
    ).hexdigest()
    adjacency_plan = (
        expert_panel.professional_carry.plan_exact_professional_carry_forward(
            current_bindings=bindings,
            prior_snapshot=prior_snapshot,
            prior_decision_dependencies=dependency_fixture,
            review_contract_fingerprint=packet[
                "review_contract_fingerprint"
            ],
        )
    )
    if (
        adjacency_plan["fresh_target_ids"] != [adjacency_target]
        or adjacency_plan["reasons_by_target"][adjacency_target]
        != ["review-unit-binding-changed"]
        or len(adjacency_plan["carry_target_ids"]) != 188
    ):
        raise ValueError(
            "representative routing-adjacency mutation carry plan is stale"
        )
    representative_adjacency = {
        "skill_id": adjacency_target,
        "fresh_target_ids": list(adjacency_plan["fresh_target_ids"]),
        "carried_forward_target_count": len(
            adjacency_plan["carry_target_ids"]
        ),
        "reason_codes": list(
            adjacency_plan["reasons_by_target"][adjacency_target]
        ),
        "cost_threshold_applied": False,
    }
    try:
        contracts = json.loads(CORE_CONTRACTS.read_text(encoding="utf-8"))
        fixture_contract = contracts["final_goal_contract"][
            "professional_review_cost_fixtures"
        ]
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(
            "final_goal_contract lacks Professional review cost fixture authority"
        ) from exc
    thresholds = fixture_contract["thresholds"]
    if (
        sensitivity["fresh_target_count"]["max"]
        > thresholds["maximum_fresh_target_count"]
        or sensitivity["fresh_target_count"]["sum"]
        > thresholds["maximum_mean_fresh_target_count"]
        * sensitivity["case_count"]
        or sensitivity["input_ratio_ppm"]["max"]
        > thresholds["maximum_input_ratio_ppm"]
        or sensitivity["input_ratio_ppm"]["sum"]
        > thresholds["maximum_mean_input_ratio_ppm"]
        * sensitivity["case_count"]
    ):
        status = "formal-non-current"
    else:
        status = "pass"
    return {
        "schema_version": 1,
        "status": status,
        "unchanged": {
            "fresh_target_count": 0,
            "carried_forward_target_count": 189,
            "input_ratio_ppm": 0,
        },
        "routing_neutral_isolated_material_binding_sensitivity": sensitivity,
        "representative_routing_adjacency_mutation": representative_adjacency,
        "review_contract_change": {
            "fresh_target_count": 189,
            "carried_forward_target_count": 0,
            "input_ratio_ppm": 1_000_000,
        },
        "thresholds": dict(thresholds),
        "limitations": list(PROFESSIONAL_REVIEW_FIXTURE_LIMITATIONS),
    }


def _professional_review_cost_fixtures() -> dict[str, Any]:
    """Recompute current measured review cost and enforce invariant ceilings."""

    result = _calculate_professional_review_cost_fixtures()
    try:
        contracts = json.loads(CORE_CONTRACTS.read_text(encoding="utf-8"))
        contract_errors = validate_core_contracts(contracts)
        if contract_errors:
            raise ValueError("; ".join(contract_errors))
        authority = contracts["final_goal_contract"][
            "professional_review_cost_fixtures"
        ]
        thresholds = authority["thresholds"]
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(
            "final_goal_contract lacks Professional review cost fixture authority"
        ) from exc
    result = copy.deepcopy(result)
    sensitivity = result.get(
        "routing_neutral_isolated_material_binding_sensitivity"
    )
    if not isinstance(sensitivity, dict):
        result["status"] = "formal-non-current"
        return result
    for legacy_digest_field in (
        "professional_packages_fingerprint",
        "catalog_fingerprint",
        "material_catalog_fingerprint",
        "full_projection_fingerprint",
        "review_contract_fingerprint",
        "cases_fingerprint",
    ):
        sensitivity.pop(legacy_digest_field, None)
    expected_fields = {
        "case_count",
        "full_rereview_deduplicated_capsule_input_bytes_proxy",
        "fresh_target_count",
        "input_ratio_ppm",
        "named_isolated_case",
    }
    current = set(sensitivity) == expected_fields
    case_count = sensitivity.get("case_count")
    full_bytes = sensitivity.get(
        "full_rereview_deduplicated_capsule_input_bytes_proxy"
    )
    fresh = sensitivity.get("fresh_target_count")
    ratio = sensitivity.get("input_ratio_ppm")
    named = sensitivity.get("named_isolated_case")
    current = bool(
        current
        and type(case_count) is int
        and case_count == expert_panel.PROFESSIONAL_PACKAGE_COUNT
        and type(full_bytes) is int
        and full_bytes > 0
        and isinstance(fresh, dict)
        and set(fresh) == {"min", "sum", "mean_milli", "p95", "max"}
        and all(type(value) is int and value >= 0 for value in fresh.values())
        and fresh["mean_milli"] == fresh["sum"] * 1000 // case_count
        and fresh["min"] <= fresh["p95"] <= fresh["max"]
        and fresh["max"] <= thresholds["maximum_fresh_target_count"]
        and fresh["sum"]
        <= thresholds["maximum_mean_fresh_target_count"] * case_count
        and isinstance(ratio, dict)
        and set(ratio) == {"min", "sum", "mean", "p95", "max"}
        and all(type(value) is int and value >= 0 for value in ratio.values())
        and ratio["mean"] == ratio["sum"] // case_count
        and ratio["min"] <= ratio["p95"] <= ratio["max"]
        and ratio["max"] <= thresholds["maximum_input_ratio_ppm"]
        and ratio["sum"]
        <= thresholds["maximum_mean_input_ratio_ppm"] * case_count
        and isinstance(named, dict)
        and set(named)
        == {
            "skill_id",
            "fresh_target_count",
            "carried_forward_target_count",
            "canonical_capsule_input_bytes_proxy",
            "input_ratio_ppm",
        }
        and named["skill_id"] == "acceptance-criteria-builder"
        and all(
            type(named[field]) is int and named[field] >= 0
            for field in (
                "fresh_target_count",
                "carried_forward_target_count",
                "canonical_capsule_input_bytes_proxy",
                "input_ratio_ppm",
            )
        )
        and named["fresh_target_count"] + named["carried_forward_target_count"]
        == case_count
        and named["canonical_capsule_input_bytes_proxy"] > 0
        and named["input_ratio_ppm"]
        == named["canonical_capsule_input_bytes_proxy"] * 1_000_000 // full_bytes
        and result.get("thresholds") == thresholds
    )
    result["status"] = "pass" if current else "formal-non-current"
    return result


def _expert_reviews(
    path: Path,
    *,
    reference_fingerprint: str,
    root_fingerprint: str,
    ai_readability_fingerprint: str | None = None,
    content_skills: object = None,
    readability_content: object = None,
    content_audit: object = None,
    evaluation_date: date | None = None,
    storage_statuses: dict[str, str] | None = None,
    formal: bool = False,
) -> dict[str, Any]:
    """Parse independent schema-5 axes or normalize a legacy attestation."""

    try:
        config_bytes = path.read_bytes()
        data = load_yaml_file(path)
    except (OSError, ValidationProblem) as exc:
        raise ValueError(str(exc)) from exc
    if not isinstance(data, dict):
        raise ValueError(f"{_rel(path)}: release review config must be a mapping")
    if set(data) == DUAL_PANEL_CONFIG_FIELDS:
        if not isinstance(content_audit, dict):
            raise ValueError(
                f"{_rel(path)}: current content audit is required"
            )
        current_completeness_packet = (
            _current_professional_completeness_packet()
        )
        return _dual_expert_reviews_from_data(
            path,
            data=data,
            config_bytes=config_bytes,
            reference_fingerprint=reference_fingerprint,
            root_fingerprint=root_fingerprint,
            ai_readability_fingerprint=ai_readability_fingerprint,
            content_skills=content_skills,
            readability_content=readability_content,
            current_completeness_packet=current_completeness_packet,
            evaluation_date=evaluation_date,
            content_audit=content_audit,
            storage_statuses=storage_statuses,
            formal=formal,
        )

    legacy_review = _expert_content_review(
        path,
        reference_fingerprint=reference_fingerprint,
        root_fingerprint=root_fingerprint,
        ai_readability_fingerprint=ai_readability_fingerprint,
        content_skills=content_skills,
        readability_content=readability_content,
        evaluation_date=evaluation_date,
        content_audit=content_audit,
    )
    return _normalized_expert_reviews(legacy_review)


def _validated_iso_date(
    value: object,
    *,
    label: str,
    evaluation_date: date | None,
) -> str:
    try:
        parsed = date.fromisoformat(value)  # type: ignore[arg-type]
        if parsed.isoformat() != value or parsed > (evaluation_date or date.today()):
            raise ValueError
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a non-future ISO date") from exc
    return parsed.isoformat()


def _is_sha256(value: str) -> bool:
    return bool(len(value) == 64 and all(char in "0123456789abcdef" for char in value))


def _repository_relative_path(path: Path, *, label: str) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"{label} escapes the repository") from exc


def _git_path_is_tracked(value: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", value],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError as exc:
        raise ValueError("cannot verify checked-in expert content review evidence") from exc
    return result.returncode == 0


def _git_head_blob(value: str, *, commit: str = "HEAD") -> bytes:
    try:
        result = subprocess.run(
            ["git", "show", f"{commit}:{value}"],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError as exc:
        raise ValueError("cannot read expert content review evidence from HEAD") from exc
    if result.returncode != 0:
        raise ValueError(
            f"expert content review evidence has no readable HEAD blob: {value}"
        )
    return result.stdout


def _git_path_is_clean(value: str) -> bool:
    try:
        result = subprocess.run(
            [
                "git",
                "status",
                "--porcelain=v1",
                "--untracked-files=no",
                "--",
                value,
            ],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError as exc:
        raise ValueError("cannot verify expert content review evidence cleanliness") from exc
    if result.returncode != 0:
        raise ValueError(
            f"cannot verify expert content review evidence cleanliness: {value}"
        )
    return not result.stdout.strip()


def _git_tracked_expert_panel_paths() -> list[str]:
    """Return the exact tracked Expert Panel inventory from the current index."""

    try:
        result = subprocess.run(
            ["git", "ls-files", "-z", "--", "evals/expert-panel"],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError as exc:
        raise ValueError("cannot resolve tracked Expert Panel inventory") from exc
    if result.returncode != 0:
        raise ValueError("cannot resolve tracked Expert Panel inventory")
    raw_paths = result.stdout.split(b"\0")
    if raw_paths and raw_paths[-1] == b"":
        raw_paths.pop()
    paths: list[str] = []
    for raw in raw_paths:
        try:
            value = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(
                "tracked Expert Panel inventory paths must be UTF-8"
            ) from exc
        relative = Path(value)
        if (
            relative.is_absolute()
            or relative.as_posix() != value
            or ".." in relative.parts
            or not value.startswith("evals/expert-panel/")
        ):
            raise ValueError(
                f"tracked Expert Panel inventory path is not canonical: {value}"
            )
        paths.append(value)
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate tracked Expert Panel inventory path")
    return sorted(paths)


def _expert_panel_currentness_drift(exc: Exception) -> bool:
    """Classify only external authority drift as non-structural staleness."""

    message = str(exc)
    if isinstance(
        exc,
        expert_panel.panel_attestation.AttestationCurrentnessError,
    ):
        return message in {
            "Readability detector contract binding is stale",
            "Readability target manifest binding is stale",
        }
    if isinstance(exc, expert_panel.PanelReviewError):
        return message in {
            "semantic attestation selector must match exactly one current authority",
            "Professional attestation exact current binding is stale",
            "Professional attestation target coverage is stale",
            "Professional baseline attestation selector is stale",
            "readability attestation exact current coverage or contract is stale",
            "semantic attestation exact current candidate coverage is stale",
            "semantic attestation application entries are stale",
            "semantic fixed missing target lacks a rewrite majority",
            "semantic fixed attestation omits a current candidate",
            "semantic fixed rewrite target remains current",
            "semantic fixed attestation disposition mismatch",
        }
    if isinstance(exc, expert_panel.panel_attestation.AttestationError):
        return (
            message
            in {
                "attestation source fingerprints are stale",
                "attestation review contract fingerprint is stale",
                "professional package fingerprints are stale",
                "readability source or review binding coverage is stale",
                "semantic candidate authority is incomplete",
                "Semantic candidate binding is stale",
                "semantic candidate fingerprints are stale",
                "semantic candidate fingerprint coverage is stale",
                "Professional current binding coverage is incomplete",
            }
            or message.startswith("Professional current binding for ")
            or message.startswith("Professional dependency binding for ")
        )
    return False


def _validate_current_expert_panel_storage(*, formal: bool) -> dict[str, str]:
    """Validate fixed storage and report per-axis currentness."""

    tracked_paths = _git_tracked_expert_panel_paths()
    if len(tracked_paths) != len(set(tracked_paths)):
        raise ValueError("duplicate tracked Expert Panel inventory path")
    allowed_by_axis = expert_panel.panel_attestation.ATTESTATION_PATHS
    allowed_paths = set(allowed_by_axis.values())
    unexpected = sorted(set(tracked_paths) - allowed_paths)
    if unexpected:
        raise ValueError(
            "unexpected tracked Expert Panel storage paths: "
            + ", ".join(unexpected)
        )
    tracked = set(tracked_paths)
    statuses: dict[str, str] = {}
    for panel_kind, relative in sorted(allowed_by_axis.items()):
        candidate = ROOT / relative
        if not os.path.lexists(candidate):
            statuses[panel_kind] = "missing"
            continue
        label = f"fixed Expert Panel attestation {relative}"
        bound = expert_panel.reviewer_manifest.read_bound_regular_file(
            candidate,
            max_bytes=expert_panel.panel_attestation.MAX_ATTESTATION_BYTES,
            label=label,
        )
        header = (
            expert_panel.panel_attestation.parse_attestation_storage_selector_bytes(
                bound.raw
            )
        )
        review_id = header.get("review_id")
        decided_on = header.get("decided_on")
        if not isinstance(review_id, str) or not isinstance(decided_on, str):
            raise ValueError(
                f"{relative}: attestation review_id and decided_on are required"
            )
        actual_panel_kind = (
            expert_panel.panel_attestation.attestation_axis_for_path(relative)
        )
        if actual_panel_kind != panel_kind:
            raise ValueError(
                f"current Expert Panel attestation path is invalid: {relative}"
            )
        storage_schema = header.get("schema_version")
        if storage_schema != expert_panel.panel_attestation.ATTESTATION_SCHEMA_VERSION:
            if storage_schema != 1:
                raise ValueError(
                    f"{relative}: unsupported compact storage schema_version"
                )
            expected_kind = {
                expert_panel.READABILITY_PANEL_KIND: (
                    expert_panel.panel_attestation.READABILITY_ATTESTATION_KIND
                ),
                expert_panel.SEMANTIC_DISPOSITION_PANEL_KIND: (
                    expert_panel.panel_attestation.SEMANTIC_DISPOSITION_ATTESTATION_KIND
                ),
                expert_panel.PROFESSIONAL_COMPLETENESS_PANEL_KIND: (
                    expert_panel.panel_attestation.PROFESSIONAL_COMPLETENESS_ATTESTATION_KIND
                ),
            }[panel_kind]
            if (
                header.get("axis") != panel_kind
                or header.get("kind") != expected_kind
                or not isinstance(header.get("findings"), list)
                or not isinstance(header.get("summary"), dict)
                or not isinstance(header.get("review_contract_fingerprint"), str)
                or re.fullmatch(
                    r"[0-9a-f]{64}", header["review_contract_fingerprint"]
                )
                is None
            ):
                raise ValueError(
                    f"{relative}: historical compact storage envelope is malformed"
                )
            try:
                historical_head_equal = _git_head_blob(relative) == bound.raw
            except ValueError:
                historical_head_equal = False
            if relative not in tracked or not historical_head_equal:
                raise ValueError(
                    f"{relative}: historical compact storage must be tracked and HEAD-equal"
                )
            if (
                expert_panel.reviewer_manifest.recheck_bound_file(
                    bound, label=label
                )
                != bound.raw
            ):
                raise ValueError(
                    f"historical Expert Panel attestation changed during validation: {relative}"
                )
            statuses[panel_kind] = "stale"
            continue
        current = True
        try:
            fixed_path, validation, _validate_current = (
                expert_panel._current_attestation_validation(
                    panel_kind,
                    review_id=review_id,
                    decided_on=decided_on,
                    attestation_selector=header,
                )
            )
            if fixed_path != relative:
                raise ValueError(
                    "current Expert Panel attestation kind does not match path: "
                    + relative
                )
            value = expert_panel.panel_attestation.parse_attestation_bytes(
                bound.raw,
                expected_path=relative,
                **validation,
            )
        except (
            expert_panel.PanelReviewError,
            expert_panel.panel_attestation.AttestationError,
        ) as exc:
            if not _expert_panel_currentness_drift(exc):
                raise
            try:
                trusted_head_bytes = (
                    relative in tracked
                    and _git_head_blob(relative) == bound.raw
                    and _git_path_is_clean(relative)
                )
            except ValueError:
                trusted_head_bytes = False
            if not trusted_head_bytes:
                raise
            current = False
        if (
            expert_panel.reviewer_manifest.recheck_bound_file(
                bound, label=label
            )
            != bound.raw
        ):
            raise ValueError(
                f"current Expert Panel attestation changed during validation: {relative}"
            )
        if not current:
            statuses[panel_kind] = "stale"
            continue
        if relative not in tracked:
            statuses[panel_kind] = "pending"
            continue
        try:
            head_current = _git_head_blob(relative) == bound.raw
        except ValueError:
            head_current = False
        statuses[panel_kind] = (
            "current"
            if head_current and _git_path_is_clean(relative)
            else "pending"
        )
    noncurrent = [
        f"{panel_kind}={statuses[panel_kind]}"
        for panel_kind in sorted(statuses)
        if statuses[panel_kind] != "current"
    ]
    if formal and noncurrent:
        raise ValueError(
            "formal Expert Panel storage requires current attestations: "
            + ", ".join(noncurrent)
        )
    return statuses


def _derive_expert_panel_release_manifest(
    *,
    formal: bool,
    storage_statuses: dict[str, str],
    current_head_commit: str | None,
    manifest_head_commit: str | None,
    artifact_observations: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """Derive the downstream release identity without affecting panel inputs."""

    expected_axes = {axis for axis, _path, _verdict in (
        EXPERT_PANEL_RELEASE_MANIFEST_ARTIFACTS
    )}
    if set(storage_statuses) != expected_axes:
        raise ValueError(
            "Expert Panel release manifest storage axes must be exact"
        )
    invalid_statuses = sorted(
        set(storage_statuses.values()) - {"current", "missing", "stale", "pending"}
    )
    if invalid_statuses:
        raise ValueError(
            "Expert Panel release manifest storage status is invalid: "
            + ", ".join(invalid_statuses)
        )
    if not formal:
        status = "not-evaluated"
        for candidate in ("missing", "stale", "pending"):
            if candidate in storage_statuses.values():
                status = candidate
                break
        return {
            "schema_version": EXPERT_PANEL_RELEASE_MANIFEST_SCHEMA_VERSION,
            "status": status,
            "head_commit": None,
            "artifacts": [],
            "verification_toolchain": None,
        }

    if set(storage_statuses.values()) != {"current"}:
        raise ValueError(
            "formal Expert Panel release manifest requires all axes current"
        )
    if (
        not isinstance(current_head_commit, str)
        or len(current_head_commit) not in {40, 64}
        or any(char not in "0123456789abcdef" for char in current_head_commit)
        or manifest_head_commit != current_head_commit
    ):
        raise ValueError(
            "formal Expert Panel release manifest HEAD is not the current commit"
        )
    if not isinstance(artifact_observations, list):
        raise ValueError(
            "formal Expert Panel release manifest artifacts are missing"
        )
    expected = list(EXPERT_PANEL_RELEASE_MANIFEST_ARTIFACTS)
    if len(artifact_observations) != len(expected):
        raise ValueError(
            "formal Expert Panel release manifest requires exactly three artifacts"
        )

    artifacts: list[dict[str, Any]] = []
    head_byte_equal_count = 0
    clean_artifact_count = 0
    accepted_artifact_count = 0
    for observed, (axis, path, accepted_verdict) in zip(
        artifact_observations,
        expected,
        strict=True,
    ):
        expected_fields = {
            "axis",
            "path",
            "external_sha256",
            "size_bytes",
            "review_id",
            "verdict",
            "head_byte_equal",
            "clean",
        }
        if not isinstance(observed, dict) or set(observed) != expected_fields:
            raise ValueError(
                "formal Expert Panel release manifest artifact fields are invalid"
            )
        if observed["axis"] != axis or observed["path"] != path:
            raise ValueError(
                "formal Expert Panel release manifest axis/path is not canonical"
            )
        digest = observed["external_sha256"]
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(char not in "0123456789abcdef" for char in digest)
        ):
            raise ValueError(
                "formal Expert Panel release manifest external sha256 is invalid"
            )
        if (
            type(observed["size_bytes"]) is not int
            or observed["size_bytes"] <= 0
            or not isinstance(observed["review_id"], str)
            or not observed["review_id"]
        ):
            raise ValueError(
                "formal Expert Panel release manifest artifact identity is invalid"
            )
        if observed["verdict"] == accepted_verdict:
            accepted_artifact_count += 1
        else:
            raise ValueError(
                "formal Expert Panel release manifest contains an adverse verdict"
            )
        if observed["head_byte_equal"] is True:
            head_byte_equal_count += 1
        else:
            raise ValueError(
                "formal Expert Panel release manifest artifact differs from HEAD"
            )
        if observed["clean"] is True:
            clean_artifact_count += 1
        else:
            raise ValueError(
                "formal Expert Panel release manifest artifact has dirty Git state"
            )
        artifacts.append(
            {
                field: observed[field]
                for field in (
                    "axis",
                    "path",
                    "external_sha256",
                    "size_bytes",
                    "review_id",
                    "verdict",
                )
            }
        )
    return {
        "schema_version": EXPERT_PANEL_RELEASE_MANIFEST_SCHEMA_VERSION,
        "status": "current",
        "head_commit": manifest_head_commit,
        "artifacts": artifacts,
        "verification_toolchain": {
            "head_commit_matches_current": True,
            "artifact_count": len(artifacts),
            "accepted_artifact_count": accepted_artifact_count,
            "head_byte_equal_count": head_byte_equal_count,
            "clean_artifact_count": clean_artifact_count,
        },
    }


def _git_head_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            text=True,
        )
    except OSError as exc:
        raise ValueError("cannot resolve current HEAD for release manifest") from exc
    value = result.stdout.strip()
    if (
        result.returncode != 0
        or len(value) not in {40, 64}
        or any(char not in "0123456789abcdef" for char in value)
    ):
        raise ValueError("cannot resolve current HEAD for release manifest")
    return value


def _expert_panel_release_manifest(
    *, formal: bool, storage_statuses: dict[str, str]
) -> dict[str, Any]:
    if not formal:
        return _derive_expert_panel_release_manifest(
            formal=False,
            storage_statuses=storage_statuses,
            current_head_commit=None,
            manifest_head_commit=None,
            artifact_observations=None,
        )

    captured_head_commit = os.environ.get(FORMAL_HEAD_COMMIT_ENV)
    if captured_head_commit is None:
        captured_head_commit = _git_head_commit()
    if (
        len(captured_head_commit) not in {40, 64}
        or any(
            character not in "0123456789abcdef"
            for character in captured_head_commit
        )
        or _git_head_commit() != captured_head_commit
    ):
        raise ValueError(
            "formal Expert Panel release manifest HEAD is not the current commit "
            "or captured Core HEAD"
        )
    head_commit = captured_head_commit
    observations: list[dict[str, Any]] = []
    for axis, relative, _accepted_verdict in (
        EXPERT_PANEL_RELEASE_MANIFEST_ARTIFACTS
    ):
        candidate = ROOT / relative
        label = f"fixed Expert Panel release artifact {relative}"
        bound = expert_panel.reviewer_manifest.read_bound_regular_file(
            candidate,
            max_bytes=expert_panel.panel_attestation.MAX_ATTESTATION_BYTES,
            label=label,
        )
        value = (
            expert_panel.panel_attestation.parse_attestation_storage_selector_bytes(
                bound.raw
            )
        )
        if (
            expert_panel.reviewer_manifest.recheck_bound_file(bound, label=label)
            != bound.raw
        ):
            raise ValueError(
                f"fixed Expert Panel release artifact changed during validation: {relative}"
            )
        observations.append(
            {
                "axis": value.get("axis", axis),
                "path": relative,
                "external_sha256": hashlib.sha256(bound.raw).hexdigest(),
                "size_bytes": len(bound.raw),
                "review_id": value.get("review_id"),
                "verdict": value.get("verdict"),
                "head_byte_equal": (
                    _git_head_blob(relative, commit=head_commit) == bound.raw
                ),
                "clean": _git_path_is_clean(relative),
            }
        )
    return _derive_expert_panel_release_manifest(
        formal=True,
        storage_statuses=storage_statuses,
        current_head_commit=_git_head_commit(),
        manifest_head_commit=head_commit,
        artifact_observations=observations,
    )


def _require_default_release_review_config(
    path: Path, *, current_bytes: bytes
) -> None:
    if path.resolve() != DEFAULT_RELEASE_REVIEW_CONFIG.resolve():
        raise ValueError(
            "complete expert content review requires the default "
            "config/professionalism-release-review.yaml"
        )
    relative = _repository_relative_path(
        path, label="expert content review release config"
    )
    if not _git_path_is_tracked(relative):
        raise ValueError(
            "complete expert content review requires a Git-tracked default "
            "release-review config"
        )
    if _git_head_blob(relative) != current_bytes:
        raise ValueError(
            "complete expert content review default release-review config "
            "differs from its HEAD blob"
        )
    if not _git_path_is_clean(relative):
        raise ValueError(
            "complete expert content review default release-review config has "
            "dirty Git state"
        )


def _validate_expert_evidence(item: dict[str, str]) -> None:
    value = item["path"]
    relative = Path(value)
    if relative.is_absolute() or relative.as_posix() != value or ".." in relative.parts:
        raise ValueError(
            "expert content review evidence paths must be canonical repository-relative paths"
        )
    if value.startswith(("reports/", "dist/")) or value in GENERATED_EXPERT_EVIDENCE_PATHS:
        raise ValueError(
            f"expert content review evidence cannot use generated artifact: {value}"
        )
    candidate = (ROOT / relative).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError(
            f"expert content review evidence escapes the repository: {value}"
        ) from exc
    if not candidate.is_file():
        raise ValueError(f"expert content review evidence is missing: {value}")
    if not _git_path_is_tracked(value):
        raise ValueError(
            f"expert content review evidence is not checked in: {value}"
        )
    current = candidate.read_bytes()
    current_sha256 = hashlib.sha256(current).hexdigest()
    if item["sha256"] != current_sha256:
        raise ValueError(
            f"expert content review evidence sha256 is stale: {value}"
        )
    if _git_head_blob(value) != current:
        raise ValueError(
            f"expert content review evidence differs from its HEAD blob: {value}"
        )
    if not _git_path_is_clean(value):
        raise ValueError(
            f"expert content review evidence has dirty Git state: {value}"
        )


def _content_readiness(
    reference_summary: dict[str, Any],
    root_summary: dict[str, Any],
    expert_reviews: dict[str, Any],
) -> dict[str, Any]:
    reference = {
        "scope": "reference-content",
        "source_fingerprint": reference_summary["source_fingerprint"],
        "strict_ready_basis": reference_summary["strict_ready_basis"],
        "structural_strict_ready": reference_summary["structural_strict_ready"],
        "semantic_triage_complete": reference_summary["semantic_triage_complete"],
        "strict_ready": reference_summary["strict_ready"],
    }
    root = {
        "scope": "agent-facing-root-content",
        "source_fingerprint": root_summary["source_fingerprint"],
        "strict_ready_basis": root_summary["strict_ready_basis"],
        "structural_strict_ready": root_summary["structural_strict_ready"],
        "semantic_triage_complete": root_summary["semantic_triage_complete"],
        "strict_ready": root_summary["strict_ready"],
    }
    readability = expert_reviews["readability"]
    professional_completeness = expert_reviews["professional_completeness"]
    expert = {
        "readability": readability,
        "professional_completeness": professional_completeness,
        "deprecated_expert_content_review_complete": expert_reviews.get(
            "deprecated_expert_content_review_complete", False
        ),
    }
    aggregate = {
        "structural_strict_ready": (
            reference["structural_strict_ready"] and root["structural_strict_ready"]
        ),
        "semantic_triage_complete": (
            reference["semantic_triage_complete"] and root["semantic_triage_complete"]
        ),
        "readability_review_current": (
            _readability_review_formal_ready(readability)
        ),
        "professional_completeness_review_current": (
            _professional_completeness_review_formal_ready(
                professional_completeness
            )
        ),
    }
    return {
        "schema_version": 10,
        "reference": reference,
        "root": root,
        "expert": expert,
        "aggregate": aggregate,
    }


def _readability_review_formal_ready(review: object) -> bool:
    if not isinstance(review, dict):
        return False
    return bool(
        review.get("panel_kind") == expert_panel.READABILITY_PANEL_KIND
        and review.get("scope") == "ai-readability-and-density"
        and review.get("decision_complete") is True
        and review.get("storage_current") is True
        and review.get("source_current") is True
        and review.get("accepted_for_formal") is True
        and review.get("decision_method") == expert_panel.DECISION_METHOD
        and review.get("panel_size") == expert_panel.PANEL_SIZE
        and review.get("attestation_schema_version") == 5
        and review.get("attestation_status") == "panel-majority-current"
        and review.get("panel_artifact_schema_version")
        == expert_panel.READABILITY_SCHEMA_VERSION
        and review.get("tracked_tightening_count") == 0
        and review.get("detector_false_positive_count") == 0
        and review.get("rewrite_required_count") == 0
        and review.get("blocker_count") == 0
        and review.get("required_density_disposition_count")
        == review.get("applied_density_disposition_count")
        and review.get("required_readability_disposition_count")
        == review.get("applied_readability_disposition_count")
        and review.get("required_actionability_disposition_count")
        == review.get("applied_actionability_disposition_count")
    )


def _professional_completeness_review_formal_ready(review: object) -> bool:
    if not isinstance(review, dict):
        return False
    return bool(
        review.get("panel_kind")
        == expert_panel.PROFESSIONAL_COMPLETENESS_PANEL_KIND
        and review.get("scope") == "professional-skill-packages"
        and review.get("decision_complete") is True
        and review.get("storage_current") is True
        and review.get("source_current") is True
        and review.get("accepted_for_formal") is True
        and review.get("decision_method")
        == expert_panel.PROFESSIONAL_COMPLETENESS_INCREMENTAL_DECISION_METHOD
        and review.get("panel_size") == expert_panel.PANEL_SIZE
        and type(review.get("reviewer_pool_size")) is int
        and review.get("reviewer_pool_size") >= 0
        and (
            (
                review.get("fresh_target_count") == 0
                and review.get("reviewer_pool_size") == 0
            )
            or (
                type(review.get("fresh_target_count")) is int
                and review.get("fresh_target_count") > 0
                and review.get("reviewer_pool_size")
                >= expert_panel.PANEL_SIZE
            )
        )
        and review.get("attestation_schema_version") == 5
        and review.get("attestation_status") == "panel-majority-current"
        and review.get("panel_artifact_schema_version")
        == expert_panel.PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
        and review.get("evidence_contract_satisfied") is True
        and _professional_completeness_v3_evidence_ready(
            qualification=review.get("qualification_summary"),
            evidence=review.get("evidence_summary"),
        )
        and review.get("qualification_summary", {}).get(
            "fresh_reviewer_pool_size"
        )
        == review.get("reviewer_pool_size")
        and review.get("review_contract_current") is True
        and review.get("review_plan_current") is True
        and review.get("review_binding_current") is True
        and review.get("provenance_current") is True
        and review.get("round_lifecycle_current") is True
        and review.get("review_cost_current") is True
        and isinstance(review.get("review_cost"), dict)
        and review.get("required_target_count")
        == expert_panel.PROFESSIONAL_PACKAGE_COUNT
        and type(review.get("fresh_target_count")) is int
        and type(review.get("carried_forward_target_count")) is int
        and review.get("fresh_target_count")
        + review.get("carried_forward_target_count")
        == expert_panel.PROFESSIONAL_PACKAGE_COUNT
        and _professional_review_cost_policy_satisfied(
            review.get("review_cost"),
            fresh_target_count=review.get("fresh_target_count"),
            carried_forward_target_count=review.get(
                "carried_forward_target_count"
            ),
        )
        and review.get("applied_target_count")
        == expert_panel.PROFESSIONAL_PACKAGE_COUNT
        and review.get("accepted_current_count")
        == expert_panel.PROFESSIONAL_PACKAGE_COUNT
        and review.get("correction_count") == 0
        and review.get("unresolved_professional_disagreement_count") == 0
    )


def _release_gate(
    authoring_gate: str,
    authoring_blockers: list[Finding],
    expert_reviews: dict[str, Any],
    root_summary: dict[str, Any] | None = None,
    content_audit_summary: dict[str, Any] | None = None,
    *,
    expert_panel_release_manifest: dict[str, Any],
) -> tuple[str, list[Finding]]:
    release_blockers = list(authoring_blockers)
    manifest_errors = validate_expert_panel_release_manifest(
        expert_panel_release_manifest,
        require_current=True,
    )
    if manifest_errors:
        release_blockers.append(
            Finding(
                EXPERT_PANEL_RELEASE_MANIFEST_BLOCKER_CATEGORY,
                "professionalism-regression-report.json"
                "#expert_panel_release_manifest",
                "; ".join(manifest_errors),
            )
        )
    audit_summary = content_audit_summary or {}
    application = audit_summary.get("semantic_disposition_application")
    audit_gate = audit_summary.get("audit_gate_status")
    if isinstance(application, dict) and application.get("status") != "current":
        error = application.get("error")
        error_id = (
            str(error.get("id"))
            if isinstance(error, dict) and error.get("id")
            else "semantic-decision-application-invalid"
        )
        error_message = (
            str(error.get("message"))
            if isinstance(error, dict) and error.get("message")
            else "semantic disposition application is invalid"
        )
        release_blockers.append(
            Finding(
                "semantic-disposition-application-release-gate",
                "skill-content-audit.json#semantic_disposition_application",
                f"{error_id}: {error_message}",
            )
        )
    elif (
        isinstance(audit_gate, dict)
        and audit_gate.get("formal_release") != "pass"
    ):
        release_blockers.append(
            Finding(
                "content-audit-formal-release-gate",
                "skill-content-audit.json#gate_status.formal_release",
                "formal content-audit gate is not pass",
            )
        )
    readability = expert_reviews.get("readability", {})
    professional_completeness = expert_reviews.get(
        "professional_completeness", {}
    )
    if not _readability_review_formal_ready(readability):
        status = str(readability.get("attestation_status", "unknown"))
        tracked = readability.get("tracked_tightening_count")
        false_positives = readability.get("detector_false_positive_count")
        rewrites = readability.get("rewrite_required_count")
        release_blockers.append(
            Finding(
                "readability-review-release-gate",
                str(
                    readability.get(
                        "attestation_source",
                        "config/professionalism-release-review.yaml"
                        "#readability_review_attestation",
                    )
                ),
                "formal release requires a checked-in three-expert majority "
                "readability and actionability review over current Root, "
                "Reference, AI-readability, and Skill-detector fingerprints "
                "with no tracked tightening, unresolved detector false "
                "positives, or rewrite-required decisions; "
                f"status={status}; tracked_tightening_count={tracked}; "
                f"detector_false_positive_count={false_positives}; "
                f"rewrite_required_count={rewrites}",
            )
        )
    if not _professional_completeness_review_formal_ready(
        professional_completeness
    ):
        status = str(
            professional_completeness.get("attestation_status", "unknown")
        )
        corrections = professional_completeness.get("correction_count")
        unresolved = professional_completeness.get(
            "unresolved_professional_disagreement_count"
        )
        coverage = professional_completeness.get("applied_target_count")
        evidence_contract = professional_completeness.get(
            "evidence_contract_satisfied"
        )
        release_blockers.append(
            Finding(
                "professional-completeness-review-release-gate",
                str(
                    professional_completeness.get(
                        "attestation_source",
                        "config/professionalism-release-review.yaml"
                        "#professional_completeness_review_attestation",
                    )
                ),
                "formal release requires a checked-in schema-3 Professional "
                "Completeness round with exact package carry-forward, current "
                "review contract, plan, bindings, provenance, chain head, and "
                "review-cost evidence; every fresh Skill needs two qualified "
                "domain reviewers and one architecture reviewer, and all 189 "
                "effective packages need source evidence, no required corrections, "
                "and no unresolved domain-critical disagreement; "
                f"status={status}; applied_target_count={coverage}; "
                f"evidence_contract_satisfied={evidence_contract}; "
                f"correction_count={corrections}; "
                f"unresolved_professional_disagreement_count={unresolved}",
            )
        )
    release_ready = (
        authoring_gate == AUTHORING_GATE_PASS and not release_blockers
    )
    return (
        RELEASE_GATE_PASS if release_ready else RELEASE_GATE_FAIL,
        release_blockers,
    )


def _reference_content_findings(
    summary: dict[str, Any],
) -> tuple[list[Finding], list[Finding]]:
    blockers = [
        Finding(
            "reference-content-structural-gate",
            "skill-content-audit.json#reference_content",
            f"{key}={int(summary.get(key, 0))}",
        )
        for key in REFERENCE_DEFAULT_COUNT_FIELDS
        if int(summary.get(key, 0))
    ]
    strict_counts = {
        key: int(summary.get(key, 0)) for key in REFERENCE_STRICT_COUNT_FIELDS
    }
    advisories: list[Finding] = []
    if any(strict_counts.values()):
        details = ", ".join(f"{key}={value}" for key, value in strict_counts.items())
        blockers.append(
            Finding(
                "reference-content-strict-gate",
                "skill-content-audit.json#reference_content",
                f"strict_ready=false; {details}",
            )
        )
    if not summary.get("semantic_triage_complete"):
        blockers.append(
            Finding(
                "reference-semantic-triage-gate",
                "skill-content-audit.json#reference_content.semantic_advisories",
                (
                    "semantic_triage_complete=false; "
                    f"untriaged={int(summary.get('semantic_untriaged_candidates', 0))}; "
                    "dispositions="
                    f"{int(summary.get('semantic_disposition_applied', 0))}/"
                    f"{int(summary.get('semantic_disposition_configured', 0))}; "
                    f"errors={int(summary.get('semantic_disposition_errors', 0))}"
                ),
            )
        )
    exact_unresolved = int(
        summary.get("exact_normalized_duplicate_unresolved_groups", 0)
    )
    p2_rewrite = int(summary.get("p2_rewrite_advisory_candidates", 0))
    if exact_unresolved or p2_rewrite:
        advisories.append(
            Finding(
                "reference-semantic-content-advisory",
                "skill-content-audit.json#reference_content.semantic_advisories",
                (
                    f"exact_duplicate_groups={exact_unresolved}; "
                    f"p2_rewrite={p2_rewrite}; "
                    "these two semantic classes remain non-blocking"
                ),
                "warning",
            )
        )
    return blockers, advisories


def _root_content_findings(
    summary: dict[str, Any],
) -> tuple[list[Finding], list[Finding]]:
    strict_counts = {
        key: int(summary.get(key, 0))
        for key in ROOT_STRUCTURAL_STRICT_COUNT_FIELDS
        + ROOT_SEMANTIC_STRICT_COUNT_FIELDS
    }
    blockers: list[Finding] = []
    if any(strict_counts.values()) or not summary.get("strict_ready"):
        details = ", ".join(f"{key}={value}" for key, value in strict_counts.items())
        blockers.append(
            Finding(
                "root-content-strict-gate",
                "skill-content-audit.json#root_content",
                f"strict_ready=false; {details}",
            )
        )
    if not summary.get("semantic_triage_complete"):
        blockers.append(
            Finding(
                "root-semantic-triage-gate",
                "skill-content-audit.json#root_content.semantic_advisories",
                (
                    "semantic_triage_complete=false; "
                    f"untriaged={int(summary.get('semantic_untriaged_candidates', 0))}; "
                    "dispositions="
                    f"{int(summary.get('semantic_disposition_applied', 0))}/"
                    f"{int(summary.get('semantic_disposition_configured', 0))}; "
                    f"errors={int(summary.get('semantic_disposition_errors', 0))}"
                ),
            )
        )
    advisories: list[Finding] = []
    tightening_counts = {
        key: int(summary.get(key, 0))
        for key in (
            "foundation_over_target_words",
            "professional_over_target_words",
            "professional_over_target_tokens",
            "domain_over_target_words",
            "domain_over_target_tokens",
            "content_review_density",
            "content_tighten_body",
            "foundation_long_prose_line",
            "foundation_tutorial_density",
        )
        if int(summary.get(key, 0))
    }
    if tightening_counts:
        advisories.append(
            Finding(
                "root-content-efficiency-advisory",
                "skill-content-audit.json#root_content",
                ", ".join(
                    f"{key}={value}" for key, value in tightening_counts.items()
                ),
                "warning",
            )
        )
    return blockers, advisories


def _readability_gate_findings(
    summary: dict[str, Any],
) -> tuple[list[Finding], list[Finding]]:
    hard = int(summary.get("hard_fail_sentences", 0))
    compound = int(summary.get("compound_bullets", 0))
    blockers: list[Finding] = []
    if hard or compound or summary.get("hard_gate_ready") is not True:
        blockers.append(
            Finding(
                "ai-readability-hard-gate",
                "skill-content-audit.json#ai_readability",
                f"hard_gate_ready=false; hard_fail_sentences={hard}; "
                f"compound_bullets={compound}",
            )
        )
    review = int(summary.get("review_as_complex_sentences", 0))
    tighten = int(summary.get("tighten_sentences", 0))
    advisories: list[Finding] = []
    if review or tighten:
        advisories.append(
            Finding(
                "ai-readability-advisory",
                "skill-content-audit.json#ai_readability",
                "advisory_documents="
                f"{int(summary.get('advisory_documents', 0))}; "
                f"review_as_complex_sentences={review}; tighten_sentences={tighten}",
                "warning",
            )
        )
    return blockers, advisories


def _write_snapshot(path: Path, result: Result, reports: dict[str, dict[str, Any]]) -> None:
    snapshot = {
        "hookless_schema_version": 2,
        "authoring_gate": result.authoring_gate,
        "release_gate": result.release_gate,
        "evidence_scope": result.evidence_scope,
        "content_audit_summary": result.content_audit_summary,
        "ai_readability_summary": result.ai_readability_summary,
        "reference_content_summary": result.reference_content_summary,
        "root_content_summary": result.root_content_summary,
        "content_readiness": result.content_readiness,
        "coverage_gate_summary": result.coverage_gate_summary,
        "professional_review_cost_fixtures": (
            result.professional_review_cost_fixtures
        ),
        "limitations": result.limitations,
        "professional_skill_names": sorted(
            row.get("name")
            for row in reports["skill"].get("results", [])
            if isinstance(row, dict) and row.get("kind") == "professional"
        ),
        "benchmark_case_count": reports["benchmarks"].get("cases_checked", 0),
        "promoted_sample_count": reports["samples"].get("promoted_checked", 0),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    # JSON is valid YAML and keeps the snapshot deterministic without a writer dependency.
    path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _safe_directory_fd(
    trusted_root: Path,
    directory: Path,
    *,
    create: bool,
) -> int:
    root = trusted_root.absolute()
    try:
        relative = directory.absolute().relative_to(root)
    except ValueError as exc:
        raise ValueError("formal evidence directory escapes its trusted root") from exc
    if not relative.parts or any(
        part in {"", ".", ".."} or "/" in part for part in relative.parts
    ):
        raise ValueError("formal evidence directory is not contained")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(root, flags)
        for part in relative.parts:
            try:
                next_descriptor = os.open(part, flags, dir_fd=descriptor)
            except FileNotFoundError:
                if not create:
                    raise
                try:
                    os.mkdir(part, mode=0o755, dir_fd=descriptor)
                    os.fsync(descriptor)
                except FileExistsError:
                    pass
                next_descriptor = os.open(part, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except OSError as exc:
        if descriptor is not None:
            os.close(descriptor)
        raise ValueError(
            "formal evidence must use a safe directory without symlinks"
        ) from exc


def _atomic_write(
    path: Path,
    content: str,
    *,
    trusted_root: Path | None = None,
) -> None:
    if trusted_root is None:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
        return

    directory_fd = _safe_directory_fd(trusted_root, path.parent, create=True)
    name = path.name
    temporary_name: str | None = None
    file_fd: int | None = None
    try:
        try:
            current = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            current = None
        if current is not None and (
            not stat.S_ISREG(current.st_mode) or current.st_nlink != 1
        ):
            raise ValueError(
                "formal evidence destination must be a single-link regular file"
            )
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        flags |= getattr(os, "O_NOFOLLOW", 0)
        flags |= getattr(os, "O_CLOEXEC", 0)
        for _attempt in range(16):
            candidate = f".{name}.{secrets.token_hex(12)}.tmp"
            try:
                file_fd = os.open(
                    candidate, flags, 0o644, dir_fd=directory_fd
                )
                temporary_name = candidate
                break
            except FileExistsError:
                continue
        if file_fd is None or temporary_name is None:
            raise ValueError("formal evidence temporary file could not be reserved")
        opened = os.fstat(file_fd)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
            raise ValueError(
                "formal evidence temporary must be a single-link regular file"
            )
        raw = content.encode("utf-8")
        offset = 0
        while offset < len(raw):
            written = os.write(file_fd, raw[offset:])
            if written <= 0:  # pragma: no cover - os.write raises.
                raise OSError("short formal evidence write")
            offset += written
        os.fsync(file_fd)
        temporary_identity = (opened.st_dev, opened.st_ino)
        os.close(file_fd)
        file_fd = None
        os.replace(
            temporary_name,
            name,
            src_dir_fd=directory_fd,
            dst_dir_fd=directory_fd,
        )
        temporary_name = None
        stored = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        if (
            not stat.S_ISREG(stored.st_mode)
            or stored.st_nlink != 1
            or (stored.st_dev, stored.st_ino) != temporary_identity
        ):
            raise ValueError("formal evidence publish identity changed")
        os.fsync(directory_fd)
    except OSError as exc:
        raise ValueError("formal evidence safe atomic publish failed") from exc
    finally:
        if file_fd is not None:
            os.close(file_fd)
        if temporary_name is not None:
            try:
                current = os.stat(
                    temporary_name,
                    dir_fd=directory_fd,
                    follow_symlinks=False,
                )
                if stat.S_ISREG(current.st_mode):
                    os.unlink(temporary_name, dir_fd=directory_fd)
            except OSError:
                pass
        os.close(directory_fd)


def _write(
    directory: Path,
    result: Result,
    *,
    release_projection: bool = False,
    trusted_root: Path | None = None,
) -> None:
    payload = asdict(result)
    _atomic_write(
        directory / "professionalism-regression-report.json",
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        trusted_root=trusted_root,
    )
    if not release_projection:
        return
    lines = [
        "# Hookless Professionalism Gates",
        "",
        f"- Authoring gate: **{result.authoring_gate}**",
        f"- Formal release gate: **{result.release_gate}**",
        f"- Mode: `{result.mode}`",
        f"- Historical baseline: `{result.baseline_comparison}`",
        f"- Evidence scope: `{result.evidence_scope}`",
        "- Professional coverage gate: "
        f"`{result.coverage_gate_summary.get('status', 'unknown')}` "
        f"(required={result.coverage_gate_summary.get('required_skill_count', 0)}; "
        f"pass={result.coverage_gate_summary.get('pass_count', 0)}; "
        f"fail={result.coverage_gate_summary.get('fail_count', 0)})",
        "- Reference structural strict readiness: "
        f"`{str(result.reference_content_summary['structural_strict_ready']).lower()}`",
        "- Reference semantic triage complete: "
        f"`{str(result.reference_content_summary['semantic_triage_complete']).lower()}`",
        "- Reference strict gate: "
        f"`{str(result.reference_content_summary['strict_ready']).lower()}` "
        f"(basis={result.reference_content_summary.get('strict_ready_basis')}; "
        "legacy compatibility; Reference-only; CI requires `--strict`)",
        "- Root structural strict readiness: "
        f"`{str(result.root_content_summary['structural_strict_ready']).lower()}`",
        "- Root semantic triage complete: "
        f"`{str(result.root_content_summary['semantic_triage_complete']).lower()}`",
        "- Root strict gate: "
        f"`{str(result.root_content_summary['strict_ready']).lower()}` "
        f"(basis={result.root_content_summary.get('strict_ready_basis')}; "
        "fresh agent-facing Root source)",
        "- AI readability gate: "
        f"`{str(result.ai_readability_summary.get('hard_gate_ready')).lower()}` "
        f"(documents={result.ai_readability_summary.get('documents', 0)}; "
        f"advisory-documents={result.ai_readability_summary.get('advisory_documents', 0)}; "
        f"review={result.ai_readability_summary.get('review_as_complex_sentences', 0)}; "
        f"tighten={result.ai_readability_summary.get('tighten_sentences', 0)}; "
        f"hard={result.ai_readability_summary.get('hard_fail_sentences', 0)}; "
        f"compound={result.ai_readability_summary.get('compound_bullets', 0)}; "
        f"fingerprint={result.ai_readability_summary.get('source_fingerprint')})",
        "- Skill review states: "
        + ", ".join(
            f"{state}={count}"
            for state, count in result.content_audit_summary["review_states"].items()
        )
        + "; classification remains the independent governed-body budget axis",
        "- Foundation content classes: "
        f"compact={result.root_content_summary.get('foundation_compact_capabilities', 0)} "
        "(target<=400; hard<=500; "
        f"over-target={result.root_content_summary.get('foundation_compact_over_target_words', 0)}; "
        f"over-hard={result.root_content_summary.get('foundation_compact_over_hard_words', 0)}); "
        f"complex={result.root_content_summary.get('foundation_complex_capabilities', 0)} "
        "(target<=500; hard<=600; "
        f"over-target={result.root_content_summary.get('foundation_complex_over_target_words', 0)}; "
        f"over-hard={result.root_content_summary.get('foundation_complex_over_hard_words', 0)}); "
        "universal-hard-tokens<=900 "
        f"(over-hard={result.root_content_summary.get('foundation_over_hard_tokens', 0)}); "
        "target overages require readability disposition",
        "- Professional root budget: target<=550w/850t; hard<=650w/1000t; "
        f"word-target={result.root_content_summary.get('professional_over_target_words', 0)}; "
        f"token-target={result.root_content_summary.get('professional_over_target_tokens', 0)}; "
        f"word-hard={result.root_content_summary.get('professional_over_hard_words', 0)}; "
        f"token-hard={result.root_content_summary.get('professional_over_hard_tokens', 0)}",
        "- Domain root budget: target<=500w/800t; hard<=600w/900t; "
        f"word-target={result.root_content_summary.get('domain_over_target_words', 0)}; "
        f"token-target={result.root_content_summary.get('domain_over_target_tokens', 0)}; "
        f"word-hard={result.root_content_summary.get('domain_over_hard_words', 0)}; "
        f"token-hard={result.root_content_summary.get('domain_over_hard_tokens', 0)}",
        "- Readability expert review current: "
        f"`{str(result.content_readiness['aggregate']['readability_review_current']).lower()}` "
        f"(status={result.content_readiness['expert']['readability']['attestation_status']}; "
        "artifact-schema="
        f"{result.content_readiness['expert']['readability']['panel_artifact_schema_version']}; "
        "tracked-tightening="
        f"{result.content_readiness['expert']['readability']['tracked_tightening_count']}; "
        "actionability="
        f"{result.content_readiness['expert']['readability']['applied_actionability_disposition_count']}/"
        f"{result.content_readiness['expert']['readability']['required_actionability_disposition_count']}; "
        "rewrite-required="
        f"{result.content_readiness['expert']['readability']['rewrite_required_count']}; "
        "storage-current="
        f"{str(result.content_readiness['expert']['readability']['storage_current']).lower()})",
        "- Professional-completeness expert review current: "
        f"`{str(result.content_readiness['aggregate']['professional_completeness_review_current']).lower()}` "
        f"(status={result.content_readiness['expert']['professional_completeness']['attestation_status']}; "
        "artifact-schema="
        f"{result.content_readiness['expert']['professional_completeness']['panel_artifact_schema_version']}; "
        "evidence-contract="
        f"{str(result.content_readiness['expert']['professional_completeness']['evidence_contract_satisfied']).lower()}; "
        "coverage="
        f"{result.content_readiness['expert']['professional_completeness']['applied_target_count']}/"
        f"{result.content_readiness['expert']['professional_completeness']['required_target_count']}; "
        "corrections="
        f"{result.content_readiness['expert']['professional_completeness']['correction_count']}; "
        "storage-current="
        f"{str(result.content_readiness['expert']['professional_completeness']['storage_current']).lower()})",
        "- Aggregate content readiness: "
        "structural="
        f"`{str(result.content_readiness['aggregate']['structural_strict_ready']).lower()}`; "
        "semantic-triage="
        f"`{str(result.content_readiness['aggregate']['semantic_triage_complete']).lower()}`; "
        "readability-review="
        f"`{str(result.content_readiness['aggregate']['readability_review_current']).lower()}`; "
        "professional-completeness-review="
        f"`{str(result.content_readiness['aggregate']['professional_completeness_review_current']).lower()}`",
        "- Reference preface coverage: "
        f"local={result.reference_content_summary.get('missing_reference_type_prefaces', 0)}/"
        f"{result.reference_content_summary.get('missing_load_when_prefaces', 0)}/"
        f"{result.reference_content_summary.get('missing_do_not_load_when_prefaces', 0)} missing; "
        f"effective={result.reference_content_summary.get('missing_effective_reference_types', 0)}/"
        f"{result.reference_content_summary.get('missing_effective_load_when', 0)}/"
        f"{result.reference_content_summary.get('missing_effective_do_not_load_when', 0)} missing",
        "- Reference targets: "
        f"targeted <= {result.reference_content_summary.get('targeted_line_limit')}; "
        f"mode-contract <= {result.reference_content_summary.get('mode_contract_line_limit')}; "
        f"decision items <= {result.reference_content_summary.get('decision_item_limit')}",
        "- Reference semantic governance: "
        f"unresolved={result.reference_content_summary.get('semantic_unresolved_candidates', 0)}; "
        "unconditional_absolute_p0_p1="
        f"{result.reference_content_summary.get('unconditional_absolute_p0_p1_unresolved_candidates', 0)}; "
        f"fixed_number={result.reference_content_summary.get('fixed_number_unresolved_candidates', 0)}; "
        f"exact_duplicate_groups={result.reference_content_summary.get('exact_normalized_duplicate_unresolved_groups', 0)}; "
        f"templated_groups={result.reference_content_summary.get('templated_block_unresolved_groups', 0)}; "
        f"p2_rewrite_advisory={result.reference_content_summary.get('p2_rewrite_advisory_candidates', 0)}; "
        "duplicate_occurrences="
        f"{int(result.reference_content_summary.get('exact_duplicate_occurrences', 0)) + int(result.reference_content_summary.get('templated_block_occurrences', 0))}; "
        "duplicate_tokens="
        f"{int(result.reference_content_summary.get('exact_duplicate_tokens', 0)) + int(result.reference_content_summary.get('templated_block_tokens', 0))} "
        "dispositions="
        f"{result.reference_content_summary.get('semantic_disposition_applied', 0)}/"
        f"{result.reference_content_summary.get('semantic_disposition_configured', 0)}",
        "- Root semantic governance: "
        f"unresolved={result.root_content_summary.get('semantic_unresolved_candidates', 0)}; "
        f"p0_p1={result.root_content_summary.get('semantic_p0_p1_unresolved_candidates', 0)}; "
        "fixed_number="
        f"{result.root_content_summary.get('semantic_fixed_number_unresolved_candidates', 0)}; "
        "dispositions="
        f"{result.root_content_summary.get('semantic_disposition_applied', 0)}/"
        f"{result.root_content_summary.get('semantic_disposition_configured', 0)}",
        "",
        "> Passing the authoring gate proves current deterministic source and captured-fixture contracts only; formal release additionally requires the release gate to be `release-ready`.",
        "",
        "## Evidence limits",
        "",
    ] + [f"- {item}" for item in result.limitations]
    if result.blockers:
        lines.extend(["", "## Authoring Blockers", ""] + [f"- `{item.target}`: {item.message}" for item in result.blockers])
    if result.release_blockers:
        lines.extend(["", "## Release Blockers", ""] + [f"- `{item.target}`: {item.message}" for item in result.release_blockers])
    if result.advisories:
        lines.extend(["", "## Advisories", ""] + [f"- `{item.target}`: {item.message}" for item in result.advisories])
    markdown = "\n".join(lines) + "\n"
    _atomic_write(
        directory / "professionalism-regression-report.md",
        markdown,
        trusted_root=trusted_root,
    )


def _strings(value: Any) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
