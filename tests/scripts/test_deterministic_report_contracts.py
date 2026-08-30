from __future__ import annotations

import ast
import importlib.util
import hashlib
import io
import json
import sys
import tempfile
import unittest
from contextlib import contextmanager
from datetime import date
from functools import lru_cache
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
TEST_TIMEOUT_CLASS = "source-validation"
TRACKED_REPORT_PRODUCERS = (
    "scripts/audit-skill-content.py",
    "scripts/eval-skill-professionalism.py",
    "scripts/eval-professional-benchmarks.py",
    "scripts/validate-professional-routing-coverage.py",
    "scripts/eval-professional-agent-samples.py",
    "scripts/validate-professionalism-regression.py",
    "scripts/validate-installation.py",
)
TRACKED_JSON_REPORTS = (
    "reports/skill-content-audit.json",
    "reports/skill-professionalism-eval.json",
    "reports/skill-professionalism-depth.json",
    "reports/professional-coverage-matrix.json",
    "reports/professional-benchmarks-report.json",
    "reports/professional-benchmarks-eval.json",
    "reports/professional-routing-coverage.json",
    "reports/professional-agent-samples-report.json",
    "reports/professionalism-regression-report.json",
    "reports/installation-validation.json",
)
HOOKLESS_FORBIDDEN_PRODUCER_SCRIPTS = frozenset(
    {
        "scripts/build.py",
        "scripts/validate-src-invariants.py",
        "scripts/eval-routing.py",
        "scripts/eval-agent-lightweight.py",
        "scripts/eval-rendered-context-budget.py",
        "scripts/eval-context-control-plane.py",
        "scripts/eval-skill-professionalism.py",
    }
)
SUBPROCESS_LAUNCH_FUNCTIONS = frozenset(
    {"call", "check_call", "check_output", "Popen", "run"}
)


def _static_ast_text(
    node: ast.AST,
    bindings: dict[str, str],
) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return bindings.get(node.id)
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Div)):
        left = _static_ast_text(node.left, bindings)
        right = _static_ast_text(node.right, bindings)
        if left is None or right is None:
            return None
        return left + right if isinstance(node.op, ast.Add) else f"{left}/{right}"
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"Path", "PurePath", "PurePosixPath", "str"}
        and len(node.args) == 1
    ):
        return _static_ast_text(node.args[0], bindings)
    if isinstance(node, (ast.List, ast.Tuple)):
        values = [_static_ast_text(item, bindings) for item in node.elts]
        if any(value is None for value in values):
            return None
        return "\0".join(value for value in values if value is not None)
    return None


def hookless_independence_errors(relative: str, source: str) -> list[str]:
    tree = ast.parse(source)
    errors: list[str] = []
    subprocess_modules = {"subprocess"}
    subprocess_functions: set[str] = set()
    bindings: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("tests.") or alias.name == "tests":
                    errors.append(f"{relative}: imports test module {alias.name}")
                if alias.name == "subprocess":
                    subprocess_modules.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom):
            if (
                node.level > 0
                or (node.module or "").startswith("tests.")
                or node.module == "tests"
            ):
                errors.append(f"{relative}: imports test module {node.module}")
            if node.module == "subprocess":
                subprocess_functions.update(
                    alias.asname or alias.name
                    for alias in node.names
                    if alias.name in SUBPROCESS_LAUNCH_FUNCTIONS
                )
    for statement in tree.body:
        if not isinstance(statement, (ast.Assign, ast.AnnAssign)):
            continue
        value = _static_ast_text(statement.value, bindings)
        if value is None:
            continue
        targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
        for target in targets:
            if isinstance(target, ast.Name):
                bindings[target.id] = value
    for node in ast.walk(tree):
        static_text = _static_ast_text(node, bindings)
        if static_text is not None and "core-principles-outcomes" in static_text:
            errors.append(f"{relative}: reads the global Core report")
        if not isinstance(node, ast.Call):
            continue
        subprocess_launch = (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in subprocess_modules
            and node.func.attr in SUBPROCESS_LAUNCH_FUNCTIONS
        ) or (
            isinstance(node.func, ast.Name)
            and node.func.id in subprocess_functions
        )
        if not subprocess_launch:
            continue
        rendered = ast.unparse(node)
        static_arguments = [
            value
            for argument in (
                *node.args,
                *(keyword.value for keyword in node.keywords),
            )
            if (value := _static_ast_text(argument, bindings)) is not None
        ]
        replayed = sorted(
            script
            for script in HOOKLESS_FORBIDDEN_PRODUCER_SCRIPTS
            if script in rendered
            or any(script in argument for argument in static_arguments)
        )
        if replayed:
            errors.append(
                f"{relative}: replays Core producer(s): {', '.join(replayed)}"
            )
    return errors


@lru_cache(maxsize=1)
def _load_regression_module(module_name: str | None = None):
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    path = ROOT / "scripts/validate-professionalism-regression.py"
    module_name = module_name or f"{__name__}.deterministic_regression_contract"
    existing = sys.modules.get(module_name)
    if existing is not None:
        existing_path = getattr(existing, "__file__", None)
        if not isinstance(existing_path, str) or (
            Path(existing_path).resolve() != path.resolve()
        ):
            raise RuntimeError(f"{module_name} is bound to a different source path")
        return existing
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def _load_productization_module():
    path = ROOT / "scripts/validate-productization-assets.py"
    module_name = f"{__name__}.productization_report_consumer"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def _reference_detector_contract_fixture() -> dict[str, str]:
    return dict(
        _load_regression_module()
        ._load_content_auditor()
        ._reference_semantic_detector_contract()
    )


def _semantic_advisories(candidates=None) -> dict:
    candidates = list(candidates or [])
    families = (
        "unconditional_absolute_candidate",
        "fixed_number_candidate",
        "exact_normalized_duplicate_block",
        "templated_block_candidate",
    )
    by_finding = {}
    for finding in families:
        rows = [item for item in candidates if item["finding"] == finding]
        by_finding[finding] = {
            "raw": len(rows),
            "detector_downgraded": sum(
                item["governance_status"] == "detector-downgraded" for item in rows
            ),
            "untriaged": sum(item["governance_status"] == "untriaged" for item in rows),
            "rewrite": sum(item.get("disposition") == "rewrite" for item in rows),
            "valid_contextual_rule": sum(item.get("disposition") == "valid-contextual-rule" for item in rows),
            "false_positive": sum(item.get("disposition") == "false-positive" for item in rows),
            "time_bounded_exception": sum(item.get("disposition") == "time-bounded-exception" for item in rows),
            "unresolved": sum(bool(item["unresolved"]) for item in rows),
            "resolved": sum(bool(item["resolved"]) for item in rows),
            "p0_unresolved": sum(item["unresolved"] and item["priority"] == "P0" for item in rows),
            "p1_unresolved": sum(item["unresolved"] and item["priority"] == "P1" for item in rows),
            "p2_unresolved": sum(item["unresolved"] and item["priority"] == "P2" for item in rows),
        }
    totals = {
        field: sum(by_finding[finding][field] for finding in families)
        for field in next(iter(by_finding.values()))
    }
    entries = [item["disposition_record"] for item in candidates if item.get("disposition_record")]
    return {
        "schema_version": 7,
        "detector_contract": dict(_reference_detector_contract_fixture()),
        "finding_families": list(families),
        "summary": {
            "raw_candidates": totals["raw"],
            "detector_downgraded_candidates": totals["detector_downgraded"],
            "untriaged_candidates": totals["untriaged"],
            "rewrite_candidates": totals["rewrite"],
            "valid_contextual_rule_candidates": totals["valid_contextual_rule"],
            "false_positive_candidates": totals["false_positive"],
            "time_bounded_exception_candidates": totals["time_bounded_exception"],
            "unresolved_candidates": totals["unresolved"],
            "resolved_candidates": totals["resolved"],
            "p0_unresolved_candidates": totals["p0_unresolved"],
            "p1_unresolved_candidates": totals["p1_unresolved"],
            "p2_unresolved_candidates": totals["p2_unresolved"],
            "by_finding": by_finding,
            "group_metrics": {
                finding: {
                    "groups": len(
                        [item for item in candidates if item["finding"] == finding]
                    ),
                    "occurrences": sum(
                        item.get("occurrence_count", 0)
                        for item in candidates
                        if item["finding"] == finding
                    ),
                    "tokens": sum(
                        item.get("total_tokens", 0)
                        for item in candidates
                        if item["finding"] == finding
                    ),
                }
                for finding in (
                    "exact_normalized_duplicate_block",
                    "templated_block_candidate",
                )
            },
            "strict_unresolved": {
                "fixed_number_candidates": by_finding["fixed_number_candidate"]["unresolved"],
                "templated_block_groups": by_finding["templated_block_candidate"]["unresolved"],
                "unconditional_absolute_p0_p1_candidates": (
                    by_finding["unconditional_absolute_candidate"]["p0_unresolved"]
                    + by_finding["unconditional_absolute_candidate"]["p1_unresolved"]
                ),
                "p2_rewrite_advisories": sum(
                    item.get("disposition") == "rewrite"
                    and item.get("priority") == "P2"
                    and item["finding"] not in {
                        "fixed_number_candidate",
                        "exact_normalized_duplicate_block",
                        "templated_block_candidate",
                    }
                    for item in candidates
                ),
            },
        },
        "candidates": candidates,
        "disposition_contract": {
            "schema_version": 2,
            "source": "config/skill-content-exceptions.yaml",
            "configured_count": len(entries),
            "applied_count": len(entries),
            "entries": entries,
            "errors": [],
            "common_errors": [],
            "surface_errors": {
                "control": [],
                "professional": [],
                "foundation": [],
                "domain": [],
            },
            "group_scope": "Group candidate IDs use the literal scope 'group'.",
        },
        "limitations": ["Synthetic semantic contract fixture."],
    }


def _effective_preface(path: str, *, resolved: bool) -> dict:
    fields = {}
    values = {
        "reference_type": "targeted",
        "load_when": "Concrete load condition.",
        "do_not_load_when": "Concrete do-not-load condition.",
        "required_by": '["analysis-agent"]',
        "required_output": '["decision-record"]',
    }
    for field, value in values.items():
        fields[field] = {
            "status": "resolved" if resolved else "missing",
            "value": value if resolved else None,
            "source": "local" if resolved else None,
            "evidence": (
                [
                    {
                        "source": "local",
                        "path": path,
                        "line": 3,
                        "value": value,
                        "accepted": True,
                    }
                ]
                if resolved
                else []
            ),
        }
    return {**fields, "conflicts": []}


def _reference_content_fixture() -> dict:
    result = {
        "schema_version": 5,
        "preface_contract": {
            "schema_version": 3,
            "source_precedence": ["local", "reference-index", "parent-root"],
            "fields": [
                "reference_type",
                "load_when",
                "do_not_load_when",
                "required_by",
                "required_output",
            ],
            "source_fingerprint": {
                "algorithm": "sha256",
                "value": "a" * 64,
                "document_count": 1,
            },
            "errors": [],
            "conflicts": [],
        },
        "summary": {
            "physical_markdown_references": 5,
            "effective_reference_types": 2,
            "missing_effective_reference_types": 1,
            "effective_load_when": 2,
            "missing_effective_load_when": 1,
            "effective_do_not_load_when": 2,
            "missing_effective_do_not_load_when": 1,
            "effective_required_by": 2,
            "missing_effective_required_by": 1,
            "effective_required_output": 2,
            "missing_effective_required_output": 1,
            "effective_preface_conflicts": 0,
            "effective_preface_contract_errors": 0,
            "effective_preface_invalid": 0,
        },
        "references": [
            {
                "layer": "foundation",
                "owner": "owner",
                "path": "missing.md",
                "exists": False,
                "kind": "targeted",
                "h1_status": None,
                "has_reference_type_preface": False,
                "has_load_when_preface": False,
                "has_do_not_load_when_preface": False,
                "effective_preface": _effective_preface("missing.md", resolved=False),
            },
            {
                "layer": "foundation",
                "owner": "owner",
                "path": "missing-h1.md",
                "exists": True,
                "kind": "targeted",
                "h1_status": "missing",
                "has_reference_type_preface": False,
                "has_load_when_preface": False,
                "has_do_not_load_when_preface": False,
                "effective_preface": _effective_preface("missing-h1.md", resolved=False),
            },
            {
                "layer": "foundation",
                "owner": "owner",
                "path": "multiple.md",
                "exists": True,
                "kind": "targeted",
                "h1_status": "multiple",
                "has_reference_type_preface": True,
                "has_load_when_preface": True,
                "has_do_not_load_when_preface": True,
                "effective_preface": _effective_preface("multiple.md", resolved=True),
            },
            {
                "layer": "control",
                "owner": "owner",
                "path": "template.md",
                "exists": True,
                "kind": "template",
                "h1_status": "multiple",
                "has_reference_type_preface": True,
                "has_load_when_preface": True,
                "has_do_not_load_when_preface": True,
                "effective_preface": _effective_preface("template.md", resolved=True),
            },
        ],
        "missing": [{"path": "missing.md"}],
        "orphans": [{"path": "orphan.md"}],
        "template_assets": [
            {"path": "template.md", "indexed": True},
            {"path": "unindexed-template.md", "indexed": False},
        ],
        "advisories": {
            "non_template_multiple_h1": [{"path": "multiple.md"}],
            "non_template_empty_headings": [{"path": "multiple.md"}],
            "targeted_over_60_lines": [{"path": "multiple.md", "line_count": 61}],
            "mode_contract_over_80_lines": [{"path": "mode.md", "line_count": 81}],
            "decision_items_over_15": [
                {"path": "decisions.md", "decision_item_count": 16}
            ],
        },
        "semantic_advisories": _semantic_advisories(),
    }
    auditor = _load_regression_module()._load_content_auditor()
    result["surface_validation"] = auditor._reference_surface_validation(result)
    return result


@lru_cache(maxsize=1)
def _canonical_root_content_fixture() -> str:
    validator = _load_regression_module()._load_root_validator()
    auditor = validator._load_auditor()
    fresh = validator._fresh_root_content()
    semantic = fresh["semantic_advisories"]
    entries = []
    for candidate in semantic["candidates"]:
        entry = {
            "candidate_id": candidate["candidate_id"],
            "finding": candidate["finding"],
            "path": candidate["path"],
            "document_part": candidate["document_part"],
            "fingerprint": candidate["fingerprint"],
            "skill_owner": candidate["skill_owner"],
            "priority": auditor.ROOT_SEMANTIC_DEFAULT_PRIORITIES[
                candidate["finding"]
            ],
            "disposition": "valid-contextual-rule",
            "reason": "Synthetic current evidence preserves this bounded governance decision.",
            "authority_or_condition": "The fixture contract owns this explicit contextual boundary.",
            "decision_owner": "changeforge-test-maintainers",
            "evidence": {
                "occurrence_fingerprint": candidate["occurrence_fingerprint"],
                "context_fingerprint": candidate["context_fingerprint"],
                "rationale": "The synthetic fixture binds the exact current candidate evidence.",
            },
            "mitigation": "Rebuild the synthetic fixture after source or detector changes.",
            "review_after": None,
        }
        entries.append(entry)
        candidate.update(
            {
                "priority": entry["priority"],
                "disposition": entry["disposition"],
                "disposition_record": entry,
                "resolved": True,
                "unresolved": False,
                "governance_status": "resolved-valid-contextual-rule",
            }
        )
    entries.sort(key=lambda item: item["candidate_id"])
    by_finding = {}
    for finding in auditor.ROOT_SEMANTIC_FINDINGS:
        rows = [item for item in semantic["candidates"] if item["finding"] == finding]
        by_finding[finding] = {
            "raw": len(rows),
            "untriaged": 0,
            "rewrite": 0,
            "resolved": len(rows),
            "unresolved": 0,
            "p0_unresolved": 0,
            "p1_unresolved": 0,
            "p2_unresolved": 0,
        }
    semantic["summary"] = {
        "raw_candidates": len(entries),
        "untriaged_candidates": 0,
        "rewrite_candidates": 0,
        "resolved_candidates": len(entries),
        "unresolved_candidates": 0,
        "p0_unresolved_candidates": 0,
        "p1_unresolved_candidates": 0,
        "p2_unresolved_candidates": 0,
        "by_finding": by_finding,
        "strict_unresolved": {
            "p0_p1_candidates": 0,
            "fixed_number_candidates": 0,
        },
    }
    semantic["disposition_contract"].update(
        {
            "configured_count": len(entries),
            "applied_count": len(entries),
            "entries": entries,
            "errors": [],
            "common_errors": [],
            "surface_errors": {
                surface: [] for surface in auditor.ROOT_CONTENT_SURFACES
            },
        }
    )
    summary = fresh["summary"]
    summary.update(
        {
            "semantic_raw_candidates": len(entries),
            "semantic_unresolved_candidates": 0,
            "semantic_p0_p1_unresolved": 0,
            "semantic_fixed_number_unresolved": 0,
            "semantic_disposition_configured": len(entries),
            "semantic_disposition_applied": len(entries),
            "semantic_disposition_errors": 0,
        }
    )
    fresh["surface_validation"] = auditor._root_surface_validation(
        fresh["documents"], fresh["advisories"], semantic
    )
    return json.dumps(fresh, sort_keys=True)


def _root_content_fixture() -> dict:
    return json.loads(_canonical_root_content_fixture())


def _reference_disposition(candidate: dict, value: str) -> dict:
    return {
        "candidate_id": candidate["candidate_id"],
        "finding": candidate["finding"],
        "path": candidate["path"],
        "fingerprint": candidate["fingerprint"],
        "skill_owner": candidate["skill_owner"],
        "priority": candidate["priority"],
        "disposition": value,
        "reason": "Current source evidence supports this explicit governance decision.",
        "authority_or_condition": "Repository governance owns the bounded condition.",
        "decision_owner": "changeforge-maintainers",
        "evidence": {
            "fingerprint": candidate["evidence_fingerprint"],
            "content_fingerprint": candidate["content_fingerprint"],
            "rationale": "Current candidate identity and source membership were inspected.",
        },
        "mitigation": "Re-evaluate the rule when its source contract changes.",
        "review_after": None,
    }


def _release_review_config(
    *,
    complete: bool,
    reference_fingerprint: str | None = None,
    root_fingerprint: str | None = None,
    ai_readability_fingerprint: str | None = None,
    evidence: list[dict[str, str]] | None = None,
    content_dispositions: list[dict[str, str]] | None = None,
    readability_dispositions: list[dict[str, str]] | None = None,
) -> dict:
    return {
        "schema_version": 4,
        "review_owner": "changeforge-maintainers",
        "reviewed_at": "2026-07-14",
        "decisions": [],
        "expert_content_review_attestation": {
            "schema_version": 4,
            "scope": "agent-facing-content",
            "complete": complete,
            "source_fingerprints": {
                "reference_content": reference_fingerprint,
                "root_content": root_fingerprint,
                "ai_readability": ai_readability_fingerprint,
            },
            "attested_by": "changeforge-maintainers" if complete else None,
            "attested_on": "2026-07-14" if complete else None,
            "evidence": list(evidence or []),
            "content_dispositions": list(content_dispositions or []),
            "readability_dispositions": list(readability_dispositions or []),
            "limitations": [
                "Static expert review does not prove real-host behavior or installed experience."
            ],
        },
    }


def _expert_evidence(path: str = "LICENSE") -> dict[str, str]:
    return {
        "path": path,
        "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
    }


def _incomplete_expert_review_fixture() -> dict:
    return {
        "readability": {
            "scope": "ai-readability-and-density",
            "panel_kind": "readability",
            "decision_complete": False,
            "storage_current": False,
            "source_current": False,
            "accepted_for_formal": False,
            "decision_method": "three-independent-experts-majority",
            "panel_review_id": None,
            "panel_size": 0,
            "attestation_status": "missing-evidence",
            "attestation_source": "fixture#readability_review_attestation",
            "attestation_schema_version": 5,
            "panel_artifact_schema_version": None,
            "attestation_config_fingerprint": "0" * 64,
            "source_fingerprints": {
                "reference_content": None,
                "root_content": None,
                "ai_readability": None,
                "skill_detector": None,
            },
            "current_source_fingerprints": {
                "reference_content": "a" * 64,
                "root_content": "b" * 64,
                "ai_readability": "c" * 64,
                "skill_detector": "e" * 64,
            },
            "attested_by": None,
            "attested_on": None,
            "evidence": [],
            "density_dispositions": [],
            "readability_dispositions": [],
            "actionability_dispositions": [],
            "required_density_disposition_count": 0,
            "applied_density_disposition_count": 0,
            "required_readability_disposition_count": 0,
            "applied_readability_disposition_count": 0,
            "required_actionability_disposition_count": 0,
            "applied_actionability_disposition_count": 0,
            "accepted_current_actionability_count": None,
            "detector_false_positive_count": None,
            "rewrite_required_count": None,
            "tracked_tightening_count": None,
            "blocker_count": 0,
            "limitations": ["No readability panel evidence is present."],
        },
        "professional_completeness": {
            "scope": "professional-skill-packages",
            "panel_kind": "professional-completeness",
            "decision_complete": False,
            "storage_current": False,
            "source_current": False,
            "accepted_for_formal": False,
            "decision_method": "exact-package-carry-forward-qualified-reviewer-pool-domain-critical-fail-closed",
            "panel_review_id": None,
            "panel_size": 0,
            "reviewer_pool_size": 0,
            "attestation_status": "missing-evidence",
            "attestation_source": "fixture#professional_completeness_review_attestation",
            "attestation_schema_version": 5,
            "panel_artifact_schema_version": None,
            "attestation_config_fingerprint": "0" * 64,
            "source_fingerprints": {"professional_packages": None},
            "current_source_fingerprints": {"professional_packages": "d" * 64},
            "attested_by": None,
            "attested_on": None,
            "evidence": [],
            "evidence_contract_satisfied": False,
            "qualification_summary": None,
            "evidence_summary": None,
            "professional_dispositions": [],
            "required_target_count": 189,
            "applied_target_count": 0,
            "accepted_current_count": None,
            "correction_count": None,
            "unresolved_professional_disagreement_count": None,
            "limitations": ["No professional-completeness panel evidence is present."],
        },
        "deprecated_expert_content_review_complete": False,
    }


def _formal_professional_dispositions_fixture(
    *, panel_review_id: str
) -> list[dict]:
    rows = []
    for index in range(189):
        skill_id = f"fixture-skill-{index:03d}"
        target_digest = hashlib.sha256(
            f"fixture-decision:{skill_id}".encode("utf-8")
        ).hexdigest()
        required_candidate_id = f"fixture-dependency-{index:03d}"
        rows.append(
            {
                "skill_id": skill_id,
                "package_material_binding": hashlib.sha256(
                    f"fixture-package:{skill_id}".encode("utf-8")
                ).hexdigest(),
                "review_unit_binding": hashlib.sha256(
                    f"fixture-review-unit:{skill_id}".encode("utf-8")
                ).hexdigest(),
                "disposition": "accepted-current-professional-completeness",
                "majority_disposition": (
                    "accepted-current-professional-completeness"
                ),
                "domain_critical_defects": [],
                "ordinary_criterion_disposition": (
                    "accepted-current-professional-completeness"
                ),
                "ordinary_criterion_defects": [],
                "reason_codes": ["fixture-panel-majority-accepted"],
                "rationales": [
                    {
                        "voter_id": f"fixture-voter-{voter}",
                        "reason_code": "fixture-panel-majority-accepted",
                        "rationale": (
                            "The bounded fixture supplies canonical accepted "
                            "evidence for the manifest-only authoring oracle."
                        ),
                    }
                    for voter in ("architecture", "domain-a", "domain-b")
                ],
                "review_dependencies": {
                    "skill_id": skill_id,
                    "final_disposition": (
                        "accepted-current-professional-completeness"
                    ),
                    "evidence_complete": True,
                    "prior_target_vote_count": 3,
                    "required_candidate_ids": [required_candidate_id],
                    "reviewer_added_candidate_ids_union": [],
                    "dependency_candidate_ids": [required_candidate_id],
                },
                "evidence_metrics": {
                    "target_vote_count": 3,
                    "required_adjacency_candidate_count": 1,
                    "criterion_result_count": 30,
                    "criterion_anchor_binding_count": 30,
                    "criterion_assertion_count": 30,
                    "evidence_anchor_count": 6,
                    "examined_failure_mode_count": 6,
                    "examined_omission_candidate_count": 6,
                    "examined_adjacency_count": 3,
                    "examined_required_adjacency_count": 3,
                    "reviewer_added_adjacency_count": 0,
                    "proof_limit_count": 3,
                    "qualification_claim_count": 3,
                },
                "provenance": {
                    "mode": "fresh",
                    "origin": {
                        "origin_review_id": panel_review_id,
                        "origin_commit": "a" * 40,
                        "origin_verdict_digest": target_digest,
                    },
                },
                "target_decision_fingerprint": target_digest,
            }
        )
    return rows


def _formal_expert_reviews_fixture() -> dict:
    regression = _load_regression_module()
    _policy, policy_fingerprint = (
        regression._professional_review_formal_round_policy()
    )
    panel_review_id = "fixture-professional-current"
    professional_dispositions = _formal_professional_dispositions_fixture(
        panel_review_id=panel_review_id
    )
    evidence_summary = {
        field: sum(
            row["evidence_metrics"][field]
            for row in professional_dispositions
        )
        for field in professional_dispositions[0]["evidence_metrics"]
    }
    return {
        "readability": {
            "scope": "ai-readability-and-density",
            "panel_kind": "readability",
            "decision_complete": True,
            "storage_current": True,
            "source_current": True,
            "accepted_for_formal": True,
            "decision_method": "three-independent-experts-majority",
            "panel_size": 3,
            "attestation_schema_version": 5,
            "panel_artifact_schema_version": 2,
            "attestation_status": "panel-majority-current",
            "attestation_source": "config/review.yaml#readability",
            "tracked_tightening_count": 0,
            "detector_false_positive_count": 0,
            "rewrite_required_count": 0,
            "blocker_count": 0,
            "required_density_disposition_count": 0,
            "applied_density_disposition_count": 0,
            "required_readability_disposition_count": 0,
            "applied_readability_disposition_count": 0,
            "required_actionability_disposition_count": 0,
            "applied_actionability_disposition_count": 0,
        },
        "professional_completeness": {
            "scope": "professional-skill-packages",
            "panel_kind": "professional-completeness",
            "decision_complete": True,
            "storage_current": True,
            "source_current": True,
            "accepted_for_formal": True,
            "decision_method": "exact-package-carry-forward-qualified-reviewer-pool-domain-critical-fail-closed",
            "panel_review_id": panel_review_id,
            "panel_size": 3,
            "reviewer_pool_size": 3,
            "panel_artifact_schema_version": 3,
            "attestation_schema_version": 5,
            "attestation_status": "panel-majority-current",
            "attestation_source": "config/review.yaml#professional-completeness",
            "attestation_config_fingerprint": "c" * 64,
            "source_fingerprints": {},
            "current_source_fingerprints": {},
            "attested_by": f"expert-panel:{panel_review_id}",
            "attested_on": "2026-08-14",
            "evidence": [
                {
                    "path": "evals/expert-panel/professional-completeness.json",
                    "sha256": "d" * 64,
                }
            ],
            "required_target_count": 189,
            "fresh_target_count": 189,
            "carried_forward_target_count": 0,
            "applied_target_count": 189,
            "accepted_current_count": 189,
            "correction_count": 0,
            "unresolved_professional_disagreement_count": 0,
            "evidence_contract_satisfied": True,
            "qualification_summary": {
                "covered_target_count": 189,
                "required_domain_experts_per_target": 2,
                "required_architecture_experts_per_target": 1,
                "per_target_panel_size": 3,
                "fresh_reviewer_pool_size": 3,
                "effective_domain_vote_count": 378,
                "effective_architecture_vote_count": 189,
            },
            "evidence_summary": evidence_summary,
            "review_contract_fingerprint": "e" * 64,
            "current_review_contract_fingerprint": "e" * 64,
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
                "chain_depth": 0,
                "head_decision": None,
                "current_decision_is_head": True,
                "errors": [],
                "limitations": [
                    regression.PROFESSIONAL_REVIEW_COST_LIMITATIONS[2]
                ],
            },
            "review_cost_current": True,
            "review_cost": {
                "fresh_vote_count": 567,
                "carried_forward_vote_count": 0,
                "effective_vote_count": 567,
                "fresh_criterion_result_count": 5670,
                "carried_forward_criterion_result_count": 0,
                "effective_criterion_result_count": 5670,
                "canonical_capsule_input_bytes_proxy": 303,
                "full_rereview_deduplicated_capsule_input_bytes_proxy": 300,
                "input_ratio_ppm": 1_010_000,
                "required_only_capsule_input_bytes_proxy": 300,
                "required_only_input_ratio_ppm": 1_000_000,
                "required_only_source_material_input_bytes_proxy": 100,
                "source_material_input_bytes_proxy": 100,
                "full_rereview_source_material_input_bytes_proxy": 100,
                "source_material_coverage_ratio_ppm": 1_000_000,
                "reviewer_added_source_material_input_bytes_proxy": 0,
                "reviewer_added_relationship_evidence_metadata_overhead_bytes_proxy": 3,
                "reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm": 15_000,
                "reviewer_added_request_count": 3,
                "reviewer_added_unique_relationship_count": 1,
                "maximum_reviewer_added_unique_union_to_required_ratio_ppm": 200_000,
                "formal_round_policy_fingerprint": policy_fingerprint,
                "maximum_origin_depth": 0,
                "plan_lineage_depth": 0,
                "policy_status": "bootstrap-full-review",
                "limitations": list(
                    regression.PROFESSIONAL_REVIEW_COST_LIMITATIONS
                ),
            },
            "professional_dispositions": professional_dispositions,
            "limitations": [
                "The fixture proves only deterministic static report behavior."
            ],
        },
        "deprecated_expert_content_review_complete": False,
    }


def _formal_release_manifest_fixture() -> dict:
    regression = _load_regression_module()
    head_commit = "1" * 40
    observations = [
        {
            "axis": axis,
            "path": path,
            "external_sha256": format(index + 1, "x") * 64,
            "size_bytes": 100 + index,
            "review_id": f"fixture-{axis}",
            "verdict": verdict,
            "head_byte_equal": True,
            "clean": True,
        }
        for index, (axis, path, verdict) in enumerate(
            regression.EXPERT_PANEL_RELEASE_MANIFEST_ARTIFACTS
        )
    ]
    return regression._derive_expert_panel_release_manifest(
        formal=True,
        storage_statuses={
            axis: "current"
            for axis, _path, _verdict in (
                regression.EXPERT_PANEL_RELEASE_MANIFEST_ARTIFACTS
            )
        },
        current_head_commit=head_commit,
        manifest_head_commit=head_commit,
        artifact_observations=observations,
    )


@contextmanager
def _mock_attestation_storage(regression):
    """Keep non-storage attestation tests independent from Git worktree state."""

    with mock.patch.object(
        regression, "_require_default_release_review_config"
    ), mock.patch.object(regression, "_validate_expert_evidence"):
        yield


def _write_release_review_config(path: Path, config: dict) -> None:
    attestation = config["expert_content_review_attestation"]
    fingerprints = attestation["source_fingerprints"]
    evidence = attestation["evidence"]
    content_dispositions = attestation["content_dispositions"]
    readability_dispositions = attestation["readability_dispositions"]
    evidence_lines = (
        [
            "  evidence:",
            *[
                line
                for item in evidence
                for line in (
                    f'    - path: "{item["path"]}"',
                    f'      sha256: "{item["sha256"]}"',
                )
            ],
        ]
        if evidence
        else ["  evidence: []"]
    )
    disposition_lines = (
        [
            "  content_dispositions:",
            *[
                line
                for item in content_dispositions
                for line in (
                    f'    - path: "{item["path"]}"',
                    f'      classification: "{item["classification"]}"',
                    f'      disposition: "{item["disposition"]}"',
                    f'      rationale: "{item["rationale"]}"',
                )
            ],
        ]
        if content_dispositions
        else ["  content_dispositions: []"]
    )
    readability_disposition_lines = (
        [
            "  readability_dispositions:",
            *[
                line
                for item in readability_dispositions
                for line in (
                    f'    - document_id: "{item["document_id"]}"',
                    f'      highest_band: "{item["highest_band"]}"',
                    f'      disposition: "{item["disposition"]}"',
                    f'      rationale: "{item["rationale"]}"',
                )
            ],
        ]
        if readability_dispositions
        else ["  readability_dispositions: []"]
    )
    lines = [
        f"schema_version: {config['schema_version']}",
        f"review_owner: {config['review_owner']}",
        f'reviewed_at: "{config["reviewed_at"]}"',
        "decisions: []",
        "expert_content_review_attestation:",
        f"  schema_version: {attestation['schema_version']}",
        f"  scope: {attestation['scope']}",
        f"  complete: {'true' if attestation['complete'] else 'false'}",
        "  source_fingerprints:",
        "    reference_content: "
        + (
            f'"{fingerprints["reference_content"]}"'
            if fingerprints["reference_content"] is not None
            else "null"
        ),
        "    root_content: "
        + (
            f'"{fingerprints["root_content"]}"'
            if fingerprints["root_content"] is not None
            else "null"
        ),
        "    ai_readability: "
        + (
            f'"{fingerprints["ai_readability"]}"'
            if fingerprints["ai_readability"] is not None
            else "null"
        ),
        "  attested_by: "
        + (
            f'"{attestation["attested_by"]}"'
            if attestation["attested_by"] is not None
            else "null"
        ),
        "  attested_on: "
        + (
            f'"{attestation["attested_on"]}"'
            if attestation["attested_on"] is not None
            else "null"
        ),
        *evidence_lines,
        *disposition_lines,
        *readability_disposition_lines,
        "  limitations:",
        *[f'    - "{item}"' for item in attestation["limitations"]],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class DeterministicReportContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.regression = _load_regression_module()

    def _content_audit_report(self, *, summary: dict | None = None) -> dict:
        auditor = self.regression._load_content_auditor()
        readability = auditor._collect_ai_readability(
            [
                {
                    "document_id": "src/example/SKILL.md#body",
                    "path": "src/example/SKILL.md",
                    "document_part": "body",
                    "surface": "professional-skill-body",
                    "owner": "example",
                    "line_offset": 0,
                    "source_selector": {
                        "kind": "whole-file",
                        "path": "src/example/SKILL.md",
                    },
                    "text": "Inspect the bounded source.",
                    "check_bullets": True,
                }
            ]
        )
        base_summary = {
            "classifications": {"KEEP": 1},
            "review_states": {"KEEP": 1},
            "review_reasons": {
                reason: 0 for reason in auditor.REVIEW_REASON_PRIORITY
            },
            "weak_professional_front_loaded_action": 0,
            "description_recommended_over_budget": 0,
            "description_hard_over_budget": 0,
        }
        if summary:
            base_summary.update(summary)
        return {
            "schema_version": auditor.AUDIT_SCHEMA_VERSION,
            "skill_detector": auditor._skill_detector_contract(),
            "skills": [
                {
                    "actionability_applicable": False,
                    "actionability_findings": [],
                    "actionability_model": "runtime-front-loaded-v1",
                    "actionable_repeated_phrase_count": 0,
                    "classification": "KEEP",
                    "control_boilerplate_density": 0.0,
                    "control_scaffold_families": [],
                    "control_scaffold_findings": [],
                    "description_findings": [],
                    "front_loaded_action_score": 100,
                    "generic_control_phrase_count": 0,
                    "governed_line_count": 10,
                    "high_confidence_control_scaffold": False,
                    "kind": "professional-skill",
                    "line_count": 10,
                    "name": "example",
                    "projection_overhead_lines": 0,
                    "review_reasons": [],
                    "review_state": "KEEP",
                    "split_candidate_score": 0,
                }
            ],
            "summary": base_summary,
            "actionable_common_lines": {},
            "ai_readability": readability,
            "semantic_disposition_application": {
                "schema_version": 1,
                "kind": "changeforge.semantic-disposition-application",
                "status": "current",
            },
            "gate_status": {
                "schema_version": 1,
                "selected_gate": "authoring",
                "authoring": {"status": "pass", "blockers": []},
                "formal_release": {"status": "pass", "blockers": []},
                "limitations": [
                    "The authoring gate does not attest formal application currentness."
                ],
            },
        }

    def test_tracked_report_producers_do_not_use_wall_clock_fields(self) -> None:
        for relative in TRACKED_REPORT_PRODUCERS:
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("generated_at", text, relative)
            self.assertNotIn("datetime.now", text, relative)

    def test_tracked_reports_do_not_contain_wall_clock_fields(self) -> None:
        for relative in TRACKED_JSON_REPORTS:
            text = (ROOT / relative).read_text(encoding="utf-8")
            report = json.loads(text)
            self.assertNotIn("generated_at", report, relative)
            self.assertNotIn('"evaluated_on"', text, relative)
        self.assertNotIn(
            "evaluated_on=",
            (ROOT / "reports/skill-content-audit.md").read_text(encoding="utf-8"),
        )

    def test_expert_release_requirement_has_strict_non_report_only_cli_contract(self) -> None:
        with mock.patch.object(sys, "stderr", new=io.StringIO()):
            with self.assertRaises(SystemExit) as missing_strict:
                self.regression._args(["--require-expert-content-review"])
            with self.assertRaises(SystemExit) as report_only:
                self.regression._args(
                    [
                        "--strict",
                        "--report-only",
                        "--require-expert-content-review",
                    ]
                )
        self.assertEqual(2, missing_strict.exception.code)
        self.assertEqual(2, report_only.exception.code)

    def test_reference_validator_follows_audit_in_required_command_contracts(self) -> None:
        for relative in (
            "docs/SKILL_CONTENT_GOVERNANCE.md",
            "docs/VALIDATION.md",
        ):
            lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
            audit_lines = [
                index
                for index, line in enumerate(lines)
                if "python3 scripts/audit-skill-content.py" in line
            ]
            validator_lines = [
                index
                for index, line in enumerate(lines)
                if "python3 scripts/validate-reference-content.py" in line
                and "--strict" in line
            ]
            root_validator_lines = [
                index
                for index, line in enumerate(lines)
                if "python3 scripts/validate-root-content.py" in line
                and "--strict" in line
            ]
            self.assertTrue(audit_lines, relative)
            self.assertTrue(validator_lines, relative)
            self.assertTrue(root_validator_lines, relative)
            self.assertTrue(
                any(audit + 1 == validator for audit in audit_lines for validator in validator_lines),
                relative,
            )
            self.assertTrue(
                any(
                    reference + 1 == root_validator
                    for reference in validator_lines
                    for root_validator in root_validator_lines
                ),
                relative,
            )
        pull_request_template = (
            ROOT / ".github/pull_request_template.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "Development Affected selected the expected producer/test closure",
            pull_request_template,
        )
        self.assertIn("docs/VALIDATION.md", pull_request_template)
        self.assertNotIn(
            "python3 scripts/validate-reference-content.py",
            pull_request_template,
        )
        for relative in ("AGENTS.md",):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(
                "python3 scripts/eval-core-principles.py --gate authoring",
                text,
                relative,
            )
            self.assertNotIn("python3 scripts/audit-skill-content.py", text, relative)
            self.assertNotIn(
                "python3 scripts/validate-reference-content.py", text, relative
            )

    def test_mandatory_quickstart_commands_match_agents_and_validation(self) -> None:
        commands = (
            "python3 scripts/quickstart.py --agent codex --scope user --dry-run",
            "python3 scripts/quickstart.py --agent claude --scope project --target /tmp/changeforge-quickstart-claude --dry-run",
            "python3 scripts/quickstart.py --agent copilot --scope project --target /tmp/changeforge-quickstart-copilot --dry-run",
            "python3 scripts/quickstart.py --agent openai-api --dry-run",
        )
        for relative in ("AGENTS.md", "docs/VALIDATION.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            for command in commands:
                self.assertEqual(1, text.count(command), (relative, command))

    def test_retired_workflows_leave_local_formal_core_as_the_only_gate(self) -> None:
        for relative in (
            ".github/workflows/ci.yml",
            ".github/workflows/formal-release.yml",
        ):
            self.assertFalse((ROOT / relative).exists(), relative)

        formal_command = (
            "python3 scripts/eval-core-principles.py --gate formal-release"
        )
        for relative in ("AGENTS.md", "docs/VALIDATION.md", "docs/RELEASE.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertEqual(1, text.count(formal_command), relative)

        evaluator = (ROOT / "scripts/eval-core-principles.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('choices=("authoring", "formal-release", "affected")', evaluator)
        self.assertIn('args.gate == "formal-release"', evaluator)

    def test_hookless_modules_own_their_checks_without_core_report_or_replay(
        self,
    ) -> None:
        modules = {
            "tests/test_hookless_build_install.py",
            "tests/test_hookless_architecture.py",
            "tests/test_hookless_evaluations.py",
        }
        for relative in modules:
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertEqual(
                [],
                hookless_independence_errors(relative, source),
                relative,
            )

        build_source = (
            ROOT / "tests/test_hookless_build_install.py"
        ).read_text(encoding="utf-8")
        self.assertIn("authoritative_build_input_snapshot_errors", build_source)

    def test_hookless_independence_guard_rejects_common_bypasses(self) -> None:
        guard = globals().get("hookless_independence_errors")
        self.assertTrue(callable(guard), "hookless independence guard is missing")
        bypasses = {
            "ordinary-test-import": (
                "import tests.scripts.test_eval_core_principles\n"
            ),
            "relative-test-import": (
                "from .scripts.test_eval_core_principles import "
                "assert_core_producer_outcomes_passed\n"
            ),
            "split-core-report-path": (
                "from pathlib import Path\n"
                "REPORT = Path('reports') / "
                "('core-principles-' + 'outcomes.json')\n"
            ),
            "alternate-subprocess-launch": (
                "import subprocess\n"
                "subprocess.check_call(["
                "'python3', 'scripts/eval-routing.py'])\n"
            ),
            "bound-subprocess-target": (
                "import subprocess\n"
                "ROUTER = 'scripts/' + 'eval-routing.py'\n"
                "subprocess.check_call(['python3', ROUTER])\n"
            ),
            "path-composed-subprocess-target": (
                "from pathlib import Path\n"
                "import subprocess\n"
                "subprocess.Popen(["
                "'python3', str(Path('scripts') / 'eval-routing.py')])\n"
            ),
        }
        for label, source in bypasses.items():
            with self.subTest(bypass=label):
                self.assertTrue(guard(label, source), label)

    def test_validation_gate_paths_exclude_individual_producer_commands(self) -> None:
        text = (ROOT / "docs/VALIDATION.md").read_text(encoding="utf-8")
        gate_marker = "## Gate Paths"
        diagnostic_marker = "## Diagnostic Appendix"
        self.assertEqual(1, text.count(gate_marker))
        self.assertEqual(1, text.count(diagnostic_marker))
        before_gate, gate_and_after = text.split(gate_marker, 1)
        gate_section, after_gate = gate_and_after.split("\n## ", 1)
        before_diagnostics, diagnostics = text.split(diagnostic_marker, 1)
        self.assertTrue(before_gate.strip())
        self.assertTrue(after_gate.strip())
        gate_lines = gate_section.splitlines()
        diagnostic_lines = diagnostics.splitlines()
        self.assertEqual(
            1,
            text.count("python3 scripts/eval-core-principles.py --gate authoring"),
        )
        self.assertEqual(
            1,
            text.count(
                "python3 scripts/eval-core-principles.py --gate formal-release"
            ),
        )
        self.assertNotIn("Run every section", text)
        formal_professionalism_command = (
            "python3 scripts/validate-professionalism-regression.py --strict "
            "--require-expert-content-review"
        )
        report_only_command = (
            "python3 scripts/validate-professionalism-regression.py --strict "
            "--report-only"
        )
        self.assertEqual(0, text.count(formal_professionalism_command))
        self.assertNotIn(formal_professionalism_command, gate_lines)
        self.assertNotIn(formal_professionalism_command, diagnostic_lines)
        self.assertEqual(1, text.count(report_only_command))
        self.assertEqual(1, diagnostic_lines.count(report_only_command))
        self.assertNotIn(report_only_command, gate_lines)
        contract = json.loads(
            (ROOT / "src/control-model/core-contracts.json").read_text(
                encoding="utf-8"
            )
        )
        producers = contract["principle_acceptance_contract"]["producers"]
        self.assertEqual(31, len(producers))
        before_lines = before_diagnostics.splitlines()
        for producer in producers:
            command = " ".join(producer["argv"])
            documented_command = command
            if producer["id"] == "eval-rendered-context":
                documented_command = f"{command} --mode conformance"
                calibration_lines = [
                    line
                    for line in before_diagnostics.splitlines()
                    if line.startswith(
                        f"{command} --mode calibration --reports-dir "
                    )
                ]
                self.assertEqual(1, len(calibration_lines), command)
                self.assertEqual(
                    1,
                    before_lines.count(documented_command),
                    documented_command,
                )
            else:
                self.assertNotIn(documented_command, before_lines, command)
            self.assertEqual(
                1,
                diagnostic_lines.count(documented_command),
                documented_command,
            )

    def test_regression_requires_prebuilt_strict_promoted_sample_report(self) -> None:
        names = {
            "skill-professionalism-eval.json": {
                "architecture": "hookless-control-plane",
                "execution_scope": {"mode": "full"},
            },
            "skill-professionalism-depth.json": {
                "execution_scope": {"mode": "full"},
            },
            "professional-coverage-matrix.json": {
                "execution_scope": {"mode": "full"},
            },
            "professional-benchmarks-report.json": {
                "architecture": "hookless-control-plane"
            },
            "professional-agent-samples-report.json": {
                "architecture": "hookless-control-plane",
                "strict": True,
                "promoted_only": True,
                "candidates_only": False,
            },
            "skill-content-audit.json": {
                **self._content_audit_report(),
                "reference_content": _reference_content_fixture(),
            },
        }
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            for name, report in names.items():
                (directory / name).write_text(json.dumps(report), encoding="utf-8")
            self.regression._reports(directory)

            sample_path = directory / "professional-agent-samples-report.json"
            sample = json.loads(sample_path.read_text(encoding="utf-8"))
            sample["promoted_only"] = False
            sample_path.write_text(json.dumps(sample), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "--promoted-only --strict"):
                self.regression._reports(directory)

    def test_content_audit_summary_is_aggregate_and_non_blocking(self) -> None:
        report = self._content_audit_report(
            summary={
                "classifications": {
                    "REVIEW_DENSITY": 2,
                    "TIGHTEN_BODY": 3,
                    "BLOCK": 1,
                },
                "weak_professional_front_loaded_action": 2,
                "description_recommended_over_budget": 4,
                "description_hard_over_budget": 0,
            },
        )
        report["actionable_common_lines"] = {
            "shared decision rule": ["a", "b", "c"]
        }
        summary = self.regression._content_audit_summary(report)
        self.assertEqual(
            summary,
            {
                "skill_detector_fingerprint": report["skill_detector"][
                    "detector_fingerprint"
                ]["value"],
                "audit_gate_status": {
                    "selected_gate": "authoring",
                    "authoring": "pass",
                    "formal_release": "pass",
                },
                "semantic_disposition_application": {
                    "status": "current",
                    "error": None,
                },
                "content_review_density_candidates": 2,
                "content_tighten_candidates": 3,
                "content_blockers": 1,
                "weak_front_loaded_skills": 0,
                "description_recommended_over_budget_count": 4,
                "description_hard_over_budget_count": 0,
                "actionable_duplicate_line_count": 1,
                "review_states": {"KEEP": 1},
                "review_reasons": {
                    reason: 0
                    for reason in self.regression._load_content_auditor().REVIEW_REASON_PRIORITY
                },
            },
        )

    def test_content_audit_rejects_stale_skill_detector_contract(self) -> None:
        valid = self._content_audit_report()
        self.regression._content_audit_summary(valid)

        missing = json.loads(json.dumps(valid))
        missing.pop("skill_detector")
        with self.assertRaisesRegex(ValueError, "skill_detector is missing or stale"):
            self.regression._content_audit_summary(missing)

        stale = json.loads(json.dumps(valid))
        stale["skill_detector"]["detector_fingerprint"]["value"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "skill_detector is missing or stale"):
            self.regression._content_audit_summary(stale)

        incomplete = json.loads(json.dumps(valid))
        incomplete["skills"][0].pop("control_scaffold_findings")
        with self.assertRaisesRegex(ValueError, "missing required detector field"):
            self.regression._content_audit_summary(incomplete)

        malformed = json.loads(json.dumps(valid))
        malformed["skills"][0]["classification"] = []
        with self.assertRaisesRegex(ValueError, "classification is not recognized"):
            self.regression._content_audit_summary(malformed)

    def test_content_audit_recomputes_review_state_from_owner_evidence(self) -> None:
        valid = self._content_audit_report()

        stale_state = json.loads(json.dumps(valid))
        stale_state["skills"][0]["review_state"] = "KEEP_WITH_ADVISORY"
        stale_state["summary"]["review_states"] = {"KEEP_WITH_ADVISORY": 1}
        with self.assertRaisesRegex(ValueError, "do not match current evidence"):
            self.regression._content_audit_summary(stale_state)

        stale_reasons = json.loads(json.dumps(valid))
        stale_reasons["skills"][0]["review_reasons"] = [
            "weak_front_loaded_action"
        ]
        stale_reasons["skills"][0]["review_state"] = "KEEP_WITH_ADVISORY"
        stale_reasons["summary"]["review_states"] = {"KEEP_WITH_ADVISORY": 1}
        stale_reasons["summary"]["review_reasons"][
            "weak_front_loaded_action"
        ] = 1
        with self.assertRaisesRegex(ValueError, "do not match current evidence"):
            self.regression._content_audit_summary(stale_reasons)

    def test_content_audit_rejects_incoherent_line_metrics(self) -> None:
        malformed = self._content_audit_report()
        malformed["skills"][0]["projection_overhead_lines"] = 1

        with self.assertRaisesRegex(ValueError, "physical lines must equal"):
            self.regression._content_audit_summary(malformed)

    def test_content_audit_rejects_legacy_schema_eight_shape(self) -> None:
        legacy = self._content_audit_report()
        legacy["schema_version"] = 8

        with self.assertRaisesRegex(ValueError, "schema_version must equal 10"):
            self.regression._content_audit_summary(legacy)

    def test_ai_readability_summary_is_fresh_and_advisory_visible(self) -> None:
        auditor = self.regression._load_content_auditor()
        document = {
            "document_id": "src/example/SKILL.md#body",
            "path": "src/example/SKILL.md",
            "document_part": "body",
            "surface": "professional-skill-body",
            "owner": "example",
            "line_offset": 0,
            "source_selector": {
                "kind": "whole-file",
                "path": "src/example/SKILL.md",
            },
            "text": " ".join(f"word{index}" for index in range(25)) + ".",
            "check_bullets": True,
        }
        fresh = auditor._collect_ai_readability([document])
        tracked_document = fresh["documents"][0]
        self.assertEqual(0, tracked_document["line_offset"])
        self.assertEqual(
            document["source_selector"], tracked_document["source_selector"]
        )
        self.assertEqual(
            {
                "line_offset",
                "line_count",
                "text",
                "lines",
                "sha256",
            },
            set(tracked_document["document_context"]),
        )
        self.assertEqual(
            tracked_document["content_fingerprint"],
            tracked_document["document_context"]["sha256"],
        )
        summary = self.regression._ai_readability_summary(
            {"ai_readability": fresh},
            fresh_ai_readability=fresh,
        )
        self.assertEqual(1, summary["documents"])
        self.assertEqual(1, summary["advisory_documents"])
        self.assertEqual(1, summary["review_as_complex_sentences"])
        self.assertEqual(0, summary["tighten_sentences"])
        self.assertTrue(summary["hard_gate_ready"])
        blockers, advisories = self.regression._readability_gate_findings(summary)
        self.assertEqual([], blockers)
        self.assertEqual(1, len(advisories))
        self.assertIn("review_as_complex_sentences=1", advisories[0].message)

        stale = json.loads(json.dumps(fresh))
        stale["source_fingerprint"]["value"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "stale AI-readability"):
            self.regression._ai_readability_summary(
                {"ai_readability": stale},
                fresh_ai_readability=fresh,
            )

        legacy = json.loads(json.dumps(fresh))
        legacy["schema_version"] = 1
        with self.assertRaisesRegex(ValueError, "current schema 2"):
            self.regression._ai_readability_summary(
                {"ai_readability": legacy},
                fresh_ai_readability=legacy,
            )

    def test_ai_readability_hard_and_compound_findings_block(self) -> None:
        summary = {
            "hard_gate_ready": False,
            "hard_fail_sentences": 2,
            "compound_bullets": 1,
            "review_as_complex_sentences": 0,
            "tighten_sentences": 0,
            "advisory_documents": 0,
        }
        blockers, advisories = self.regression._readability_gate_findings(summary)
        self.assertEqual([], advisories)
        self.assertEqual(1, len(blockers))
        self.assertIn("hard_fail_sentences=2", blockers[0].message)
        self.assertIn("compound_bullets=1", blockers[0].message)

    def test_reference_content_summary_promotes_strict_counts_to_blockers(self) -> None:
        fixture = _reference_content_fixture()
        summary = self.regression._reference_content_summary(
            {"reference_content": fixture},
            fresh_reference_content=fixture,
        )
        self.assertEqual(
            [
                "source",
                "readiness_scope",
                "targeted_line_limit",
                "mode_contract_line_limit",
                "decision_item_limit",
                "effective_preface_schema_version",
                "strict_ready_basis",
                "source_fingerprint",
                "source_fingerprint_document_count",
                "indexed_references",
                "existing_indexed_references",
                "physical_markdown_references",
                "missing_indexed_references",
                "non_template_orphan_references",
                "missing_h1_references",
                "non_template_multiple_h1_references",
                "non_template_empty_heading_references",
                "template_assets",
                "template_multiple_h1_references",
                "unindexed_template_assets",
                "missing_reference_type_prefaces",
                "missing_load_when_prefaces",
                "missing_do_not_load_when_prefaces",
                "effective_reference_types",
                "effective_load_when",
                "effective_do_not_load_when",
                "effective_required_by",
                "effective_required_output",
                "missing_effective_reference_types",
                "missing_effective_load_when",
                "missing_effective_do_not_load_when",
                "missing_effective_required_by",
                "missing_effective_required_output",
                "effective_preface_contract_errors",
                "effective_preface_conflicts",
                "effective_preface_invalid_declarations",
                "targeted_over_60_lines",
                "mode_contract_over_80_lines",
                "decision_items_over_15",
                "semantic_schema_version",
                "semantic_finding_families",
                "semantic_raw_candidates",
                "semantic_detector_downgraded_candidates",
                "semantic_untriaged_candidates",
                "semantic_rewrite_candidates",
                "semantic_resolved_candidates",
                "semantic_unresolved_candidates",
                "unconditional_absolute_p0_p1_unresolved_candidates",
                "fixed_number_unresolved_candidates",
                "exact_normalized_duplicate_unresolved_groups",
                "templated_block_unresolved_groups",
                "p2_rewrite_advisory_candidates",
                "exact_duplicate_occurrences",
                "exact_duplicate_tokens",
                "templated_block_occurrences",
                "templated_block_tokens",
                "semantic_disposition_configured",
                "semantic_disposition_applied",
                "semantic_disposition_errors",
                "structural_strict_ready",
                "semantic_triage_complete",
                "strict_ready",
            ],
            list(summary),
        )
        self.assertEqual(60, summary["targeted_line_limit"])
        self.assertEqual(80, summary["mode_contract_line_limit"])
        self.assertEqual(15, summary["decision_item_limit"])
        self.assertEqual(3, summary["effective_preface_schema_version"])
        self.assertEqual("reference-strict-v4", summary["strict_ready_basis"])
        self.assertEqual("a" * 64, summary["source_fingerprint"])
        self.assertEqual(1, summary["source_fingerprint_document_count"])
        self.assertEqual(1, summary["template_multiple_h1_references"])
        self.assertEqual(1, summary["unindexed_template_assets"])
        self.assertFalse(summary["structural_strict_ready"])
        self.assertTrue(summary["semantic_triage_complete"])
        self.assertFalse(summary["strict_ready"])
        self.assertEqual(7, summary["semantic_schema_version"])
        self.assertEqual(
            [
                "unconditional_absolute_candidate",
                "fixed_number_candidate",
                "exact_normalized_duplicate_block",
                "templated_block_candidate",
            ],
            summary["semantic_finding_families"],
        )
        self.assertEqual(0, summary["semantic_unresolved_candidates"])

        blockers, advisories = self.regression._reference_content_findings(summary)
        self.assertEqual(
            [
                "missing_indexed_references=1",
                "non_template_orphan_references=1",
                "missing_h1_references=1",
                "non_template_multiple_h1_references=1",
                "non_template_empty_heading_references=1",
                "strict_ready=false; missing_effective_reference_types=1, "
                "missing_effective_load_when=1, missing_effective_do_not_load_when=1, "
                "missing_effective_required_by=1, "
                "missing_effective_required_output=1, "
                "targeted_over_60_lines=1, mode_contract_over_80_lines=1, "
                "decision_items_over_15=1, fixed_number_unresolved_candidates=0, "
                "templated_block_unresolved_groups=0, "
                "unconditional_absolute_p0_p1_unresolved_candidates=0"
            ],
            [item.message for item in blockers],
        )
        self.assertEqual([], advisories)

    def test_semantic_strict_candidates_add_readiness_blocker(self) -> None:
        fixture = _reference_content_fixture()
        auditor = self.regression._load_reference_validator()._load_auditor()
        fixture["semantic_advisories"] = auditor._collect_reference_semantic_advisories(
            [{
                "path": "rule.md",
                "layer": "foundation",
                "owner": "rule-owner",
                "kind": "targeted",
                "text": "# Rule\n\n- Every external mutation must retain an owner.\n- Complete recovery within 30 minutes.\n",
            }],
            disposition_entries=[],
        )
        summary = self.regression._reference_content_summary(
            {"reference_content": fixture},
            fresh_reference_content=fixture,
        )
        blockers, advisories = self.regression._reference_content_findings(summary)
        self.assertEqual(7, len(blockers))
        strict_blocker = next(
            item for item in blockers if item.category == "reference-content-strict-gate"
        )
        self.assertIn("fixed_number_unresolved_candidates=1", strict_blocker.message)
        self.assertIn(
            "unconditional_absolute_p0_p1_unresolved_candidates=1",
            strict_blocker.message,
        )
        self.assertFalse(summary["semantic_triage_complete"])
        self.assertTrue(
            any(item.category == "reference-semantic-triage-gate" for item in blockers)
        )
        self.assertEqual([], advisories)

    def test_rewrite_is_triaged_but_does_not_satisfy_reference_strict_gate(self) -> None:
        fixture = _reference_content_fixture()
        auditor = self.regression._load_reference_validator()._load_auditor()
        documents = [
            {
                "path": "rule.md",
                "layer": "foundation",
                "owner": "rule-owner",
                "kind": "targeted",
                "text": "# Rule\n\n- Complete recovery within 30 minutes.\n",
            }
        ]
        initial = auditor._collect_reference_semantic_advisories(
            documents, disposition_entries=[]
        )
        candidate = next(
            item
            for item in initial["candidates"]
            if item["finding"] == "fixed_number_candidate"
        )
        fixture["semantic_advisories"] = auditor._collect_reference_semantic_advisories(
            documents,
            disposition_entries=[_reference_disposition(candidate, "rewrite")],
        )
        summary = self.regression._reference_content_summary(
            {"reference_content": fixture}, fresh_reference_content=fixture
        )
        self.assertTrue(summary["semantic_triage_complete"])
        self.assertEqual(1, summary["semantic_rewrite_candidates"])
        self.assertFalse(summary["strict_ready"])

    def test_reference_content_summary_requires_current_audit_schema(self) -> None:
        with self.assertRaisesRegex(ValueError, "reference_content must be a current mapping"):
            self.regression._reference_content_summary({})

        fixture = _reference_content_fixture()
        fixture.pop("preface_contract")
        with self.assertRaisesRegex(ValueError, "invalid effective preface contract"):
            self.regression._reference_content_summary(
                {"reference_content": fixture}
            )

        fixture = _reference_content_fixture()
        fixture["references"][1].pop("effective_preface")
        with self.assertRaisesRegex(ValueError, "invalid effective preface contract"):
            self.regression._reference_content_summary(
                {"reference_content": fixture}
            )

        fixture = _reference_content_fixture()
        fixture.pop("semantic_advisories")
        with self.assertRaisesRegex(ValueError, "invalid semantic advisory contract"):
            self.regression._reference_content_summary(
                {"reference_content": fixture},
                fresh_reference_content=fixture,
            )

        fixture = _reference_content_fixture()
        fixture["semantic_advisories"]["summary"]["raw_candidates"] = 1
        with self.assertRaisesRegex(ValueError, "does not match candidates"):
            self.regression._reference_content_summary(
                {"reference_content": fixture},
                fresh_reference_content=fixture,
            )

    def test_reference_content_summary_rejects_stale_source_fingerprint(self) -> None:
        report = _reference_content_fixture()
        fresh = json.loads(json.dumps(report))
        fresh["preface_contract"]["source_fingerprint"]["value"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "stale Reference source fingerprint"):
            self.regression._reference_content_summary(
                {"reference_content": report},
                fresh_reference_content=fresh,
            )

    def test_reference_content_summary_rejects_hidden_fresh_contract_error(self) -> None:
        report = _reference_content_fixture()
        fresh = json.loads(json.dumps(report))
        fresh["preface_contract"]["errors"] = [
            {
                "code": "duplicate-index-row",
                "source": "reference-index",
                "path": "src/skills/owner/references/index.md",
                "line": 7,
                "message": "duplicate metadata row",
            }
        ]
        fresh["summary"]["effective_preface_contract_errors"] = 1
        with self.assertRaisesRegex(
            ValueError, "tracked Reference content does not match fresh canonical source"
        ):
            self.regression._reference_content_summary(
                {"reference_content": report},
                fresh_reference_content=fresh,
            )

    def test_root_content_summary_is_fresh_scoped_and_strict(self) -> None:
        fixture = _root_content_fixture()
        summary = self.regression._root_content_summary(
            {"root_content": fixture},
            fresh_root_content=fixture,
        )
        self.assertEqual(
            [
                "source",
                "readiness_scope",
                "strict_ready_basis",
                "source_fingerprint",
                "source_fingerprint_document_count",
                "agent_facing_root_documents",
                "foundation_compact_capabilities",
                "foundation_complex_capabilities",
                "foundation_over_target_words",
                "foundation_compact_over_target_words",
                "foundation_complex_over_target_words",
                "foundation_over_hard_words",
                "foundation_compact_over_hard_words",
                "foundation_complex_over_hard_words",
                "foundation_over_hard_tokens",
                "foundation_rule_count_outside_target",
                "foundation_rules_over_sentence_limit",
                "foundation_rules_without_decision_semantics",
                "foundation_long_prose_line",
                "foundation_tutorial_density",
                "foundation_low_decision_density",
                "content_keep",
                "content_review_density",
                "content_tighten_body",
                "content_blockers",
                "professional_over_target_words",
                "professional_over_hard_words",
                "professional_over_target_tokens",
                "professional_over_hard_tokens",
                "domain_over_target_words",
                "domain_over_hard_words",
                "domain_over_target_tokens",
                "domain_over_hard_tokens",
                "semantic_schema_version",
                "semantic_finding_families",
                "semantic_raw_candidates",
                "semantic_untriaged_candidates",
                "semantic_rewrite_candidates",
                "semantic_resolved_candidates",
                "semantic_unresolved_candidates",
                "semantic_p0_p1_unresolved_candidates",
                "semantic_fixed_number_unresolved_candidates",
                "semantic_disposition_configured",
                "semantic_disposition_applied",
                "semantic_disposition_errors",
                "structural_strict_ready",
                "semantic_triage_complete",
                "strict_ready",
            ],
            list(summary),
        )
        self.assertEqual("root-strict-v5", summary["strict_ready_basis"])
        self.assertTrue(summary["structural_strict_ready"])
        self.assertTrue(summary["semantic_triage_complete"])
        self.assertTrue(summary["strict_ready"])

    def test_root_strict_failure_is_a_regression_blocker(self) -> None:
        fixture = _root_content_fixture()
        path = "src/foundation/capabilities/example/SKILL.md"
        fixture["advisories"]["foundation_over_hard_words"].append(path)
        fixture["advisories"]["foundation_compact_over_hard_words"].append(path)
        fixture["summary"]["foundation_over_hard_words"] += 1
        fixture["summary"]["foundation_compact_over_hard_words"] += 1
        auditor = self.regression._load_content_auditor()
        fixture["surface_validation"] = auditor._root_surface_validation(
            fixture["documents"],
            fixture["advisories"],
            fixture["semantic_advisories"],
        )
        summary = self.regression._root_content_summary(
            {"root_content": fixture},
            fresh_root_content=fixture,
        )
        self.assertFalse(summary["structural_strict_ready"])
        self.assertFalse(summary["strict_ready"])
        blockers, _advisories = self.regression._root_content_findings(summary)
        self.assertTrue(
            any(item.category == "root-content-strict-gate" for item in blockers)
        )

    def test_root_content_summary_rejects_stale_source_fingerprint(self) -> None:
        report = _root_content_fixture()
        fresh = json.loads(json.dumps(report))
        fresh["source_fingerprint"]["value"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "stale Root source fingerprint"):
            self.regression._root_content_summary(
                {"root_content": report},
                fresh_root_content=fresh,
            )

    def test_root_content_summary_rejects_payload_tamper_with_same_fingerprint(self) -> None:
        report = _root_content_fixture()
        fresh = json.loads(json.dumps(report))
        fresh["advisories"]["foundation_over_target_words"].append(
            "src/foundation/capabilities/tampered/SKILL.md"
        )
        self.assertEqual(
            report["source_fingerprint"], fresh["source_fingerprint"]
        )

        with self.assertRaisesRegex(
            ValueError, "tracked Root content does not match fresh canonical source"
        ):
            self.regression._root_content_summary(
                {"root_content": report},
                fresh_root_content=fresh,
            )

    def test_root_semantic_triage_failure_is_a_regression_blocker(self) -> None:
        fixture = _root_content_fixture()
        summary = self.regression._root_content_summary(
            {"root_content": fixture}, fresh_root_content=fixture
        )
        summary["semantic_triage_complete"] = False
        summary["strict_ready"] = False
        summary["semantic_untriaged_candidates"] = 1
        summary["semantic_p0_p1_unresolved_candidates"] = 1
        blockers, _advisories = self.regression._root_content_findings(summary)
        self.assertEqual(
            {"root-content-strict-gate", "root-semantic-triage-gate"},
            {item.category for item in blockers},
        )

    def test_root_strict_blocker_enters_release_authoring_gate(self) -> None:
        reports = self.regression._reports(ROOT / "reports")
        content_audit_summary = self.regression._content_audit_summary(
            self._content_audit_report()
        )
        reference_fixture = _reference_content_fixture()
        reference_summary = self.regression._reference_content_summary(
            {"reference_content": reference_fixture},
            fresh_reference_content=reference_fixture,
        )
        root_fixture = _root_content_fixture()
        root_summary = self.regression._root_content_summary(
            {"root_content": root_fixture}, fresh_root_content=root_fixture
        )
        root_summary["foundation_over_hard_words"] = 1
        root_summary["structural_strict_ready"] = False
        root_summary["strict_ready"] = False
        ai_readability_summary = {
            "source": "synthetic#ai_readability",
            "readiness_scope": "agent-facing-ai-readability",
            "schema_version": 2,
            "source_fingerprint": "c" * 64,
            "source_fingerprint_document_count": 0,
            "contract": {},
            "documents": 0,
            "advisory_documents": 0,
            "review_as_complex_sentences": 0,
            "tighten_sentences": 0,
            "hard_fail_sentences": 0,
            "compound_bullets": 0,
            "advisory_sentences": 0,
            "blocker_findings": 0,
            "hard_gate_ready": True,
            "by_surface": {},
        }
        expert_review = _incomplete_expert_review_fixture()
        locked_cost_fixture = json.loads(
            (ROOT / "reports/professionalism-regression-report.json").read_text(
                encoding="utf-8"
            )
        )["professional_review_cost_fixtures"]
        with tempfile.TemporaryDirectory() as raw, mock.patch.object(
            self.regression, "_reports", return_value=reports
        ), mock.patch.object(
            self.regression,
            "_content_audit_summary",
            return_value=content_audit_summary,
        ), mock.patch.object(
            self.regression,
            "_reference_content_summary",
            return_value=reference_summary,
        ), mock.patch.object(
            self.regression,
            "_ai_readability_summary",
            return_value=ai_readability_summary,
        ), mock.patch.object(
            self.regression,
            "_professional_review_cost_fixtures",
            return_value=locked_cost_fixture,
        ), mock.patch.object(
            self.regression, "_root_content_summary", return_value=root_summary
        ), mock.patch.object(
            self.regression,
            "_expert_reviews",
            return_value=expert_review,
        ):
            returncode = self.regression.main(
                ["--reports-dir", raw, "--strict", "--report-only"]
            )
            self.assertEqual(0, returncode)
            readiness = json.loads(
                (Path(raw) / "professionalism-regression-report.json").read_text(
                    encoding="utf-8"
                )
            )
        self.assertEqual("current-contract-fail", readiness["authoring_gate"])
        self.assertTrue(
            any(
                item["category"] == "root-content-strict-gate"
                for item in readiness["blockers"]
            )
        )

    def test_expert_review_defaults_false_and_requires_current_triple_fingerprints(self) -> None:
        root_fixture = _root_content_fixture()
        root_summary = self.regression._root_content_summary(
            {"root_content": root_fixture}, fresh_root_content=root_fixture
        )
        reference_fixture = _reference_content_fixture()
        reference_summary = self.regression._reference_content_summary(
            {"reference_content": reference_fixture},
            fresh_reference_content=reference_fixture,
        )
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "release-review.json"
            path.write_text(
                "schema_version: 1\n"
                "review_owner: changeforge-maintainers\n"
                'reviewed_at: "2026-07-14"\n'
                "decisions: []\n",
                encoding="utf-8",
            )
            legacy = self.regression._expert_content_review(
                path,
                reference_fingerprint=reference_summary["source_fingerprint"],
                root_fingerprint=root_summary["source_fingerprint"],
                evaluation_date=date(2026, 7, 14),
            )
            self.assertFalse(legacy["expert_content_review_complete"])
            self.assertEqual("legacy-schema-default-false", legacy["attestation_status"])

            _write_release_review_config(
                path, _release_review_config(complete=False)
            )
            explicit = self.regression._expert_content_review(
                path,
                reference_fingerprint=reference_summary["source_fingerprint"],
                root_fingerprint=root_summary["source_fingerprint"],
                evaluation_date=date(2026, 7, 14),
            )
            self.assertFalse(explicit["expert_content_review_complete"])
            self.assertEqual("explicitly-incomplete", explicit["attestation_status"])

            current_config = _release_review_config(
                complete=True,
                reference_fingerprint=reference_summary["source_fingerprint"],
                root_fingerprint=root_summary["source_fingerprint"],
                ai_readability_fingerprint="c" * 64,
                evidence=[_expert_evidence()],
            )
            _write_release_review_config(path, current_config)
            with _mock_attestation_storage(self.regression):
                current = self.regression._expert_content_review(
                    path,
                    reference_fingerprint=reference_summary["source_fingerprint"],
                    root_fingerprint=root_summary["source_fingerprint"],
                    ai_readability_fingerprint="c" * 64,
                    evaluation_date=date(2026, 7, 14),
                )
            self.assertTrue(current["expert_content_review_complete"])
            self.assertEqual("attested-current", current["attestation_status"])
            self.assertRegex(current["attestation_config_fingerprint"], r"^[0-9a-f]{64}$")

            current_config["expert_content_review_attestation"]["source_fingerprints"][
                "root_content"
            ] = "c" * 64
            _write_release_review_config(path, current_config)
            with _mock_attestation_storage(
                self.regression
            ), self.assertRaisesRegex(ValueError, "stale expert content review"):
                self.regression._expert_content_review(
                    path,
                    reference_fingerprint=reference_summary["source_fingerprint"],
                    root_fingerprint=root_summary["source_fingerprint"],
                    ai_readability_fingerprint="c" * 64,
                    evaluation_date=date(2026, 7, 14),
                )

            current_config["expert_content_review_attestation"]["source_fingerprints"][
                "root_content"
            ] = root_summary["source_fingerprint"]
            current_config["expert_content_review_attestation"]["source_fingerprints"][
                "ai_readability"
            ] = "d" * 64
            _write_release_review_config(path, current_config)
            with _mock_attestation_storage(
                self.regression
            ), self.assertRaisesRegex(ValueError, "stale expert content review"):
                self.regression._expert_content_review(
                    path,
                    reference_fingerprint=reference_summary["source_fingerprint"],
                    root_fingerprint=root_summary["source_fingerprint"],
                    ai_readability_fingerprint="c" * 64,
                    evaluation_date=date(2026, 7, 14),
                )

    def test_complete_expert_review_disposes_every_current_density_overage(self) -> None:
        skills = [
            {"path": "a/SKILL.md", "classification": "REVIEW_DENSITY"},
            {"path": "b/SKILL.md", "classification": "TIGHTEN_BODY"},
        ]
        dispositions = [
            {
                "path": "a/SKILL.md",
                "classification": "REVIEW_DENSITY",
                "disposition": "accepted-current-density",
                "rationale": "Current shared invariants justify retaining this bounded decision density today.",
            },
            {
                "path": "b/SKILL.md",
                "classification": "TIGHTEN_BODY",
                "disposition": "tracked-tightening",
                "rationale": "Existing references own the low frequency detail scheduled for tightening.",
            },
        ]
        config = _release_review_config(
            complete=True,
            reference_fingerprint="a" * 64,
            root_fingerprint="b" * 64,
            ai_readability_fingerprint="c" * 64,
            evidence=[_expert_evidence()],
            content_dispositions=dispositions,
        )
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "release-review.yaml"
            _write_release_review_config(path, config)
            with _mock_attestation_storage(self.regression):
                result = self.regression._expert_content_review(
                    path,
                    reference_fingerprint="a" * 64,
                    root_fingerprint="b" * 64,
                    ai_readability_fingerprint="c" * 64,
                    content_skills=skills,
                    evaluation_date=date(2026, 7, 14),
                )
            self.assertEqual(2, result["required_content_disposition_count"])
            self.assertEqual(2, result["applied_content_disposition_count"])

            config["expert_content_review_attestation"]["content_dispositions"] = dispositions[:1]
            _write_release_review_config(path, config)
            with _mock_attestation_storage(
                self.regression
            ), self.assertRaisesRegex(ValueError, "do not match current audit"):
                self.regression._expert_content_review(
                    path,
                    reference_fingerprint="a" * 64,
                    root_fingerprint="b" * 64,
                    ai_readability_fingerprint="c" * 64,
                    content_skills=skills,
                    evaluation_date=date(2026, 7, 14),
                )

            _write_release_review_config(path, config)
            with _mock_attestation_storage(
                self.regression
            ), self.assertRaisesRegex(ValueError, "cannot override 1 content blocker"):
                self.regression._expert_content_review(
                    path,
                    reference_fingerprint="a" * 64,
                    root_fingerprint="b" * 64,
                    ai_readability_fingerprint="c" * 64,
                    content_skills=[{"path": "c/SKILL.md", "classification": "BLOCK"}],
                    evaluation_date=date(2026, 7, 14),
                )

    def test_complete_expert_review_requires_schema_four(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "release-review.json"
            path.write_text(
                "schema_version: 3\n"
                "review_owner: changeforge-maintainers\n"
                'reviewed_at: "2026-07-14"\n'
                "decisions: []\n"
                "expert_content_review_attestation:\n"
                "  schema_version: 3\n"
                "  scope: agent-facing-content\n"
                "  complete: true\n"
                "  source_fingerprints:\n"
                f'    reference_content: "{"a" * 64}"\n'
                f'    root_content: "{"b" * 64}"\n'
                "  attested_by: changeforge-maintainers\n"
                '  attested_on: "2026-07-14"\n'
                "  evidence: []\n"
                "  content_dispositions: []\n"
                "  limitations:\n"
                "    - Static evidence does not prove real-host behavior.\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ValueError, "complete expert review requires schema 4"
            ):
                self.regression._expert_content_review(
                    path,
                    reference_fingerprint="a" * 64,
                    root_fingerprint="b" * 64,
                    ai_readability_fingerprint="c" * 64,
                    evaluation_date=date(2026, 7, 14),
                )

    def test_complete_expert_review_disposes_every_readability_advisory(self) -> None:
        readability = {
            "summary": {"advisory_documents": 2, "blocker_findings": 0},
            "documents": [
                {
                    "document_id": "a#body",
                    "highest_advisory_band": "review-as-complex",
                },
                {
                    "document_id": "b#description",
                    "highest_advisory_band": "tighten",
                },
            ],
        }
        dispositions = [
            {
                "document_id": "a#body",
                "highest_band": "review-as-complex",
                "disposition": "accepted-current-readability",
                "rationale": "Expert review accepts this bounded complex sentence for current use.",
            },
            {
                "document_id": "b#description",
                "highest_band": "tighten",
                "disposition": "tracked-tightening",
                "rationale": "Expert review tracks this document for a specific tightening pass.",
            },
        ]
        config = _release_review_config(
            complete=True,
            reference_fingerprint="a" * 64,
            root_fingerprint="b" * 64,
            ai_readability_fingerprint="c" * 64,
            evidence=[_expert_evidence()],
            readability_dispositions=dispositions,
        )
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "release-review.yaml"
            _write_release_review_config(path, config)
            with _mock_attestation_storage(self.regression):
                result = self.regression._expert_content_review(
                    path,
                    reference_fingerprint="a" * 64,
                    root_fingerprint="b" * 64,
                    ai_readability_fingerprint="c" * 64,
                    readability_content=readability,
                    evaluation_date=date(2026, 7, 14),
                )
            self.assertEqual(2, result["required_readability_disposition_count"])
            self.assertEqual(2, result["applied_readability_disposition_count"])

            for value, expected in (
                (dispositions[:1], "missing=\\['b#description'\\]"),
                (
                    dispositions
                    + [
                        {
                            "document_id": "c#body",
                            "highest_band": "tighten",
                            "disposition": "tracked-tightening",
                            "rationale": "Expert review tracks this extra document pending source reconciliation.",
                        }
                    ],
                    "extra=\\['c#body'\\]",
                ),
                (
                    [
                        dispositions[0],
                        {**dispositions[1], "highest_band": "review-as-complex"},
                    ],
                    "stale=\\['b#description'\\]",
                ),
            ):
                with self.subTest(expected=expected):
                    config["expert_content_review_attestation"][
                        "readability_dispositions"
                    ] = value
                    _write_release_review_config(path, config)
                    with _mock_attestation_storage(
                        self.regression
                    ), self.assertRaisesRegex(ValueError, expected):
                        self.regression._expert_content_review(
                            path,
                            reference_fingerprint="a" * 64,
                            root_fingerprint="b" * 64,
                            ai_readability_fingerprint="c" * 64,
                            readability_content=readability,
                            evaluation_date=date(2026, 7, 14),
                        )

    def test_complete_expert_review_cannot_override_readability_blocker(self) -> None:
        config = _release_review_config(
            complete=True,
            reference_fingerprint="a" * 64,
            root_fingerprint="b" * 64,
            ai_readability_fingerprint="c" * 64,
            evidence=[_expert_evidence()],
        )
        readability = {
            "summary": {"advisory_documents": 0, "blocker_findings": 1},
            "documents": [],
        }
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "release-review.yaml"
            _write_release_review_config(path, config)
            with self.assertRaisesRegex(
                ValueError, "cannot override 1 readability blocker"
            ):
                self.regression._expert_content_review(
                    path,
                    reference_fingerprint="a" * 64,
                    root_fingerprint="b" * 64,
                    ai_readability_fingerprint="c" * 64,
                    readability_content=readability,
                    evaluation_date=date(2026, 7, 14),
                )

    def test_ordinary_authoring_does_not_claim_formal_release_without_manifest(self) -> None:
        reports = {
            "skill": {
                "errors": [],
                "warnings": [],
                "results": [
                    {
                        "name": f"fixture-professional-{index:02d}",
                        "kind": "professional",
                        "status": "pass",
                        "missing_sections": [],
                    }
                    for index in range(26)
                ],
            },
            "depth": {"errors": []},
            "coverage": {"errors": []},
            "benchmarks": {
                "errors": [],
                "cases_checked": 1,
                "results": [{"comparison_status": "pass"}],
            },
            "samples": {"errors": [], "promoted_checked": 2},
            "content": {"errors": [], "skills": [], "ai_readability": {}},
        }
        content_audit = self._content_audit_report()
        content_summary = self.regression._content_audit_summary(content_audit)
        ai_readability_summary = {
            "source": "synthetic#ai_readability",
            "readiness_scope": "agent-facing-ai-readability",
            "schema_version": 2,
            "source_fingerprint": "c" * 64,
            "source_fingerprint_document_count": 0,
            "contract": {},
            "documents": 0,
            "advisory_documents": 0,
            "review_as_complex_sentences": 0,
            "tighten_sentences": 0,
            "hard_fail_sentences": 0,
            "compound_bullets": 0,
            "advisory_sentences": 0,
            "blocker_findings": 0,
            "hard_gate_ready": True,
            "by_surface": {},
        }
        reference_summary = {
            "source_fingerprint": "a" * 64,
            "strict_ready_basis": "reference-strict-v4",
            "structural_strict_ready": True,
            "semantic_triage_complete": True,
            "strict_ready": True,
        }
        root_summary = {
            "source_fingerprint": "b" * 64,
            "strict_ready_basis": "root-strict-v5",
            "structural_strict_ready": True,
            "semantic_triage_complete": True,
            "strict_ready": True,
        }
        coverage_summary = {
            "status": "pass",
            "required_skill_count": 26,
            "pass_count": 26,
            "fail_count": 0,
            "not_required_count": 0,
            "failing_skills": [],
        }
        cost_fixture = {"status": "pass"}
        not_evaluated_manifest = {
            "schema_version": 1,
            "status": "not-evaluated",
            "head_commit": None,
            "artifacts": [],
            "verification_toolchain": None,
        }
        original_read_text = Path.read_text
        forbidden_reads = []

        def guarded_read_text(path: Path, *args, **kwargs) -> str:
            candidate = path.resolve()
            if candidate.is_relative_to((ROOT / "reports").resolve()) or (
                candidate.is_relative_to(
                    (ROOT / "evals/expert-panel").resolve()
                )
            ):
                forbidden_reads.append(candidate)
                raise AssertionError(
                    f"manifest-only oracle read generated evidence: {candidate}"
                )
            return original_read_text(path, *args, **kwargs)

        with tempfile.TemporaryDirectory() as raw, mock.patch.object(
            Path, "read_text", new=guarded_read_text
        ), mock.patch.object(
            self.regression,
            "_validate_current_expert_panel_storage",
            return_value={
                "readability": "current",
                "semantic-disposition": "current",
                "professional-completeness": "current",
            },
        ), mock.patch.object(
            self.regression, "_reports", return_value=reports
        ), mock.patch.object(
            self.regression, "_validate_fresh_benchmark_report"
        ), mock.patch.object(
            self.regression,
            "_content_audit_summary",
            return_value=content_summary,
        ), mock.patch.object(
            self.regression,
            "_ai_readability_summary",
            return_value=ai_readability_summary,
        ), mock.patch.object(
            self.regression,
            "_reference_content_summary",
            return_value=reference_summary,
        ), mock.patch.object(
            self.regression,
            "_root_content_summary",
            return_value=root_summary,
        ), mock.patch.object(
            self.regression,
            "_expert_reviews",
            return_value=_formal_expert_reviews_fixture(),
        ), mock.patch.object(
            self.regression,
            "_coverage_gate_summary",
            return_value=coverage_summary,
        ), mock.patch.object(
            self.regression,
            "_professional_review_cost_fixtures",
            return_value=cost_fixture,
        ), mock.patch.object(
            self.regression,
            "_expert_panel_release_manifest",
            return_value=not_evaluated_manifest,
        ), mock.patch.object(
            self.regression,
            "_baseline_state",
            return_value="not-numerically-comparable",
        ):
            returncode = self.regression.main(
                ["--reports-dir", raw, "--strict"]
            )
            report = json.loads(
                (Path(raw) / "professionalism-regression-report.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual([], forbidden_reads)
        self.assertEqual(0, returncode)
        self.assertEqual("current-contract-pass", report["authoring_gate"])
        self.assertEqual(
            "not-evaluated",
            report["expert_panel_release_manifest"]["status"],
        )
        self.assertIsNone(
            report["expert_panel_release_manifest"]["head_commit"]
        )
        self.assertEqual("release-not-ready", report["release_gate"])
        self.assertEqual(
            ["expert-panel-release-manifest-release-gate"],
            [item["category"] for item in report["release_blockers"]],
        )
        self.assertEqual(1, report["summary"]["release_blocker_count"])
        self.assertEqual(
            [],
            _load_productization_module()._release_gate_errors(
                "reports/professionalism-regression-report.json",
                report,
            ),
        )

    def test_release_requirement_changes_exit_only_and_preserves_report_payload(self) -> None:
        reports = self.regression._reports(ROOT / "reports")
        tracked = json.loads(
            (ROOT / "reports/professionalism-regression-report.json").read_text(
                encoding="utf-8"
            )
        )
        tracked_content_summary = self.regression._content_audit_summary(
            self._content_audit_report()
        )
        release_root = _root_content_fixture()
        release_root_summary = self.regression._root_content_summary(
            {"root_content": release_root},
            fresh_root_content=release_root,
        )
        expert_review = _incomplete_expert_review_fixture()
        with tempfile.TemporaryDirectory() as raw, mock.patch.object(
            self.regression, "_reports", return_value=reports
        ), mock.patch.object(
            self.regression,
            "_content_audit_summary",
            return_value=tracked_content_summary,
        ), mock.patch.object(
            self.regression,
            "_ai_readability_summary",
            return_value=tracked["ai_readability_summary"],
        ), mock.patch.object(
            self.regression,
            "_reference_content_summary",
            return_value=tracked["reference_content_summary"],
        ), mock.patch.object(
            self.regression,
            "_root_content_summary",
            return_value=release_root_summary,
        ), mock.patch.object(
            self.regression,
            "_expert_reviews",
            return_value=expert_review,
        ), mock.patch.object(
            self.regression,
            "_coverage_gate_summary",
            return_value=tracked["coverage_gate_summary"],
        ), mock.patch.object(
            self.regression,
            "_professional_review_cost_fixtures",
            return_value=tracked["professional_review_cost_fixtures"],
        ), mock.patch.object(
            self.regression,
            "_validate_current_expert_panel_storage",
            return_value={
                "readability": "current",
                "semantic-disposition": "current",
                "professional-completeness": "current",
            },
        ):
            directory = Path(raw)
            ordinary_directory = directory / "ordinary"
            formal_directory = directory / "formal"
            ordinary = self.regression.main(
                ["--reports-dir", str(ordinary_directory), "--strict"]
            )
            ordinary_report = json.loads(
                (ordinary_directory / "professionalism-regression-report.json")
                .read_text(encoding="utf-8")
            )
            ordinary_before = {
                path.name: path.read_bytes()
                for path in sorted(ordinary_directory.iterdir())
            }
            formal_arguments = [
                "--reports-dir",
                str(ordinary_directory),
                "--output-dir",
                str(formal_directory),
                "--strict",
                "--release-projection",
            ]
            projected = self.regression.main(formal_arguments)
            first = {
                path.name: path.read_bytes()
                for path in sorted(formal_directory.iterdir())
            }
            with mock.patch.object(sys, "stderr", new=io.StringIO()):
                release = self.regression.main(
                    formal_arguments + ["--require-expert-content-review"]
                )
            second = {
                path.name: path.read_bytes()
                for path in sorted(formal_directory.iterdir())
            }
            readiness = json.loads(
                (formal_directory / "professionalism-regression-report.json")
                .read_text(encoding="utf-8")
            )
            ordinary_after = {
                path.name: path.read_bytes()
                for path in sorted(ordinary_directory.iterdir())
            }

        self.assertEqual(0, ordinary)
        self.assertEqual(0, projected)
        self.assertEqual(1, release)
        self.assertEqual(first, second)
        self.assertEqual(ordinary_before, ordinary_after)
        self.assertEqual(
            "not-evaluated",
            ordinary_report["expert_panel_release_manifest"]["status"],
        )
        self.assertIsNone(
            ordinary_report["expert_panel_release_manifest"]["head_commit"]
        )
        self.assertEqual(
            "current", readiness["expert_panel_release_manifest"]["status"]
        )
        self.assertEqual("current-contract-pass", readiness["authoring_gate"])
        self.assertEqual("release-not-ready", readiness["release_gate"])
        self.assertEqual(
            [
                "readability-review-release-gate",
                "professional-completeness-review-release-gate",
            ],
            [item["category"] for item in readiness["release_blockers"]],
        )

    def test_d_stale_application_is_release_only_and_exactly_reported(self) -> None:
        tracked = json.loads(
            (ROOT / "reports/professionalism-regression-report.json").read_text(
                encoding="utf-8"
            )
        )
        reports = self.regression._reports(ROOT / "reports")
        content = self._content_audit_report()
        stale_error = {
            "id": "semantic-decision-application-invalid",
            "message": "semantic disposition packet is stale against the current audit",
        }
        content["semantic_disposition_application"] = {
            "schema_version": 1,
            "kind": "changeforge.semantic-disposition-application",
            "status": "invalid",
            "error": stale_error,
        }
        content["gate_status"]["formal_release"] = {
            "status": "blocked",
            "blockers": [dict(stale_error)],
        }
        reports["content"] = content
        content_summary = self.regression._content_audit_summary(content)
        expert_reviews = _formal_expert_reviews_fixture()
        release_root = _root_content_fixture()
        release_root_summary = self.regression._root_content_summary(
            {"root_content": release_root},
            fresh_root_content=release_root,
        )

        with tempfile.TemporaryDirectory() as raw, mock.patch.object(
            self.regression, "_reports", return_value=reports
        ), mock.patch.object(
            self.regression,
            "_content_audit_summary",
            return_value=content_summary,
        ), mock.patch.object(
            self.regression,
            "_ai_readability_summary",
            return_value=tracked["ai_readability_summary"],
        ), mock.patch.object(
            self.regression,
            "_reference_content_summary",
            return_value=tracked["reference_content_summary"],
        ), mock.patch.object(
            self.regression,
            "_root_content_summary",
            return_value=release_root_summary,
        ), mock.patch.object(
            self.regression,
            "_expert_reviews",
            return_value=expert_reviews,
        ), mock.patch.object(
            self.regression,
            "_coverage_gate_summary",
            return_value=tracked["coverage_gate_summary"],
        ), mock.patch.object(
            self.regression,
            "_professional_review_cost_fixtures",
            return_value=tracked["professional_review_cost_fixtures"],
        ), mock.patch.object(
            self.regression,
            "_validate_current_expert_panel_storage",
            return_value={
                "readability": "current",
                "semantic-disposition": "current",
                "professional-completeness": "current",
            },
        ):
            directory = Path(raw)
            ordinary_directory = directory / "ordinary"
            formal_directory = directory / "formal"
            report_only = self.regression.main(
                [
                    "--reports-dir",
                    str(ordinary_directory),
                    "--strict",
                    "--report-only",
                ]
            )
            ordinary_report = json.loads(
                (ordinary_directory / "professionalism-regression-report.json")
                .read_text(encoding="utf-8")
            )
            ordinary_before = {
                path.name: path.read_bytes()
                for path in sorted(ordinary_directory.iterdir())
            }
            formal_arguments = [
                "--reports-dir",
                str(ordinary_directory),
                "--output-dir",
                str(formal_directory),
                "--strict",
                "--release-projection",
            ]
            projected = self.regression.main(formal_arguments)
            first = {
                path.name: path.read_bytes()
                for path in sorted(formal_directory.iterdir())
            }
            with mock.patch.object(sys, "stderr", new=io.StringIO()):
                formal = self.regression.main(
                    formal_arguments + ["--require-expert-content-review"]
                )
            second = {
                path.name: path.read_bytes()
                for path in sorted(formal_directory.iterdir())
            }
            readiness = json.loads(
                (formal_directory / "professionalism-regression-report.json")
                .read_text(encoding="utf-8")
            )
            ordinary_after = {
                path.name: path.read_bytes()
                for path in sorted(ordinary_directory.iterdir())
            }

        exact_error = f"{stale_error['id']}: {stale_error['message']}"
        self.assertEqual(0, report_only)
        self.assertEqual(0, projected)
        self.assertEqual(1, formal)
        self.assertEqual(first, second)
        self.assertEqual(ordinary_before, ordinary_after)
        self.assertEqual(
            "not-evaluated",
            ordinary_report["expert_panel_release_manifest"]["status"],
        )
        self.assertIsNone(
            ordinary_report["expert_panel_release_manifest"]["head_commit"]
        )
        self.assertEqual(
            "current", readiness["expert_panel_release_manifest"]["status"]
        )
        self.assertEqual("current-contract-pass", readiness["authoring_gate"])
        self.assertEqual([], readiness["blockers"])
        self.assertEqual("release-not-ready", readiness["release_gate"])
        self.assertEqual(
            ["semantic-disposition-application-release-gate"],
            [item["category"] for item in readiness["release_blockers"]],
        )
        self.assertEqual(
            exact_error,
            readiness["release_blockers"][0]["message"],
        )
        self.assertIn(
            f"Formal release remains blocked: {exact_error}",
            readiness["limitations"],
        )

        current_summary = self.regression._content_audit_summary(
            self._content_audit_report()
        )
        gate, blockers = self.regression._release_gate(
            "current-contract-pass",
            [],
            expert_reviews,
            release_root_summary,
            current_summary,
            expert_panel_release_manifest=_formal_release_manifest_fixture(),
        )
        self.assertEqual("release-ready", gate)
        self.assertEqual([], blockers)

    def test_release_gate_requires_authoring_and_both_expert_axes(self) -> None:
        current = _formal_expert_reviews_fixture()
        manifest = _formal_release_manifest_fixture()
        recorded = {}
        gate, blockers = self.regression._release_gate(
            "current-contract-pass",
            [],
            current,
            recorded,
            expert_panel_release_manifest=manifest,
        )
        self.assertEqual("release-ready", gate)
        self.assertEqual([], blockers)

        noncurrent_manifests = {
            "stale": self.regression._derive_expert_panel_release_manifest(
                formal=False,
                storage_statuses={
                    "readability": "stale",
                    "semantic-disposition": "current",
                    "professional-completeness": "current",
                },
                current_head_commit=None,
                manifest_head_commit=None,
                artifact_observations=None,
            ),
            "malformed": {"status": "current"},
        }
        for label, noncurrent_manifest in noncurrent_manifests.items():
            with self.subTest(manifest=label):
                gate, blockers = self.regression._release_gate(
                    "current-contract-pass",
                    [],
                    current,
                    recorded,
                    expert_panel_release_manifest=noncurrent_manifest,
                )
                self.assertEqual("release-not-ready", gate)
                self.assertEqual(
                    ["expert-panel-release-manifest-release-gate"],
                    [item.category for item in blockers],
                )

        legacy_maintainer = json.loads(json.dumps(current))
        legacy_maintainer["readability"].update(
            {
                "decision_complete": False,
                "storage_current": True,
                "source_current": False,
                "accepted_for_formal": False,
                "decision_method": "legacy-maintainer-attestation",
                "panel_size": 0,
                "attestation_schema_version": 4,
                "attestation_status": "deprecated-combined-attestation",
            }
        )
        gate, blockers = self.regression._release_gate(
            "current-contract-pass",
            [],
            legacy_maintainer,
            recorded,
            expert_panel_release_manifest=manifest,
        )
        self.assertEqual("release-not-ready", gate)
        self.assertEqual(
            ["readability-review-release-gate"],
            [item.category for item in blockers],
        )

        authoring_blocker = self.regression.Finding(
            "fixture", "fixture", "authoring failed"
        )
        gate, blockers = self.regression._release_gate(
            "current-contract-fail",
            [authoring_blocker],
            current,
            recorded,
            expert_panel_release_manifest=manifest,
        )
        self.assertEqual("release-not-ready", gate)
        self.assertEqual([authoring_blocker], blockers)

    def test_complete_expert_review_rejects_missing_or_generated_evidence(self) -> None:
        root_fixture = _root_content_fixture()
        root_summary = self.regression._root_content_summary(
            {"root_content": root_fixture}, fresh_root_content=root_fixture
        )
        reference_fixture = _reference_content_fixture()
        reference_summary = self.regression._reference_content_summary(
            {"reference_content": reference_fixture},
            fresh_reference_content=reference_fixture,
        )
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "release-review.json"
            for evidence, expected in (
                ([], "requires checked-in evidence"),
                (
                    [_expert_evidence("reports/professionalism-regression-report.json")],
                    "generated artifact",
                ),
            ):
                with self.subTest(evidence=evidence):
                    _write_release_review_config(
                        path,
                        _release_review_config(
                            complete=True,
                            reference_fingerprint=reference_summary[
                                "source_fingerprint"
                            ],
                            root_fingerprint=root_summary["source_fingerprint"],
                            ai_readability_fingerprint="c" * 64,
                            evidence=evidence,
                        ),
                    )
                    with mock.patch.object(
                        self.regression, "_require_default_release_review_config"
                    ), self.assertRaisesRegex(ValueError, expected):
                        self.regression._expert_content_review(
                            path,
                            reference_fingerprint=reference_summary[
                                "source_fingerprint"
                            ],
                            root_fingerprint=root_summary["source_fingerprint"],
                            ai_readability_fingerprint="c" * 64,
                            evaluation_date=date(2026, 7, 14),
                        )
            _write_release_review_config(
                path,
                _release_review_config(
                    complete=True,
                    reference_fingerprint=reference_summary["source_fingerprint"],
                    root_fingerprint=root_summary["source_fingerprint"],
                    ai_readability_fingerprint="c" * 64,
                    evidence=[_expert_evidence()],
                ),
            )
            with mock.patch.object(
                self.regression, "_require_default_release_review_config"
            ), mock.patch.object(
                self.regression, "_git_path_is_tracked", return_value=False
            ), self.assertRaisesRegex(ValueError, "is not checked in"):
                self.regression._expert_content_review(
                    path,
                    reference_fingerprint=reference_summary["source_fingerprint"],
                    root_fingerprint=root_summary["source_fingerprint"],
                    ai_readability_fingerprint="c" * 64,
                    evaluation_date=date(2026, 7, 14),
                )

    def test_complete_expert_review_requires_default_config_and_clean_hashed_evidence(self) -> None:
        root_fixture = _root_content_fixture()
        root_summary = self.regression._root_content_summary(
            {"root_content": root_fixture}, fresh_root_content=root_fixture
        )
        reference_fixture = _reference_content_fixture()
        reference_summary = self.regression._reference_content_summary(
            {"reference_content": reference_fixture},
            fresh_reference_content=reference_fixture,
        )
        config = _release_review_config(
            complete=True,
            reference_fingerprint=reference_summary["source_fingerprint"],
            root_fingerprint=root_summary["source_fingerprint"],
            ai_readability_fingerprint="c" * 64,
            evidence=[_expert_evidence()],
        )
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "release-review.yaml"
            _write_release_review_config(path, config)

            with self.assertRaisesRegex(ValueError, "requires the default"):
                self.regression._expert_content_review(
                    path,
                    reference_fingerprint=reference_summary["source_fingerprint"],
                    root_fingerprint=root_summary["source_fingerprint"],
                    ai_readability_fingerprint="c" * 64,
                    evaluation_date=date(2026, 7, 14),
                )

            config["expert_content_review_attestation"]["evidence"][0][
                "sha256"
            ] = "0" * 64
            _write_release_review_config(path, config)
            with mock.patch.object(
                self.regression, "_require_default_release_review_config"
            ), self.assertRaisesRegex(ValueError, "sha256 is stale"):
                self.regression._expert_content_review(
                    path,
                    reference_fingerprint=reference_summary["source_fingerprint"],
                    root_fingerprint=root_summary["source_fingerprint"],
                    ai_readability_fingerprint="c" * 64,
                    evaluation_date=date(2026, 7, 14),
                )

            config["expert_content_review_attestation"]["evidence"] = [
                _expert_evidence()
            ]
            _write_release_review_config(path, config)
            with mock.patch.object(
                self.regression, "_require_default_release_review_config"
            ), mock.patch.object(
                self.regression, "_git_path_is_tracked", return_value=True
            ), mock.patch.object(
                self.regression, "_git_head_blob", return_value=b"different HEAD bytes"
            ), self.assertRaisesRegex(ValueError, "differs from its HEAD blob"):
                self.regression._expert_content_review(
                    path,
                    reference_fingerprint=reference_summary["source_fingerprint"],
                    root_fingerprint=root_summary["source_fingerprint"],
                    ai_readability_fingerprint="c" * 64,
                    evaluation_date=date(2026, 7, 14),
                )

            with mock.patch.object(
                self.regression, "_require_default_release_review_config"
            ), mock.patch.object(
                self.regression, "_git_path_is_tracked", return_value=True
            ), mock.patch.object(
                self.regression,
                "_git_head_blob",
                return_value=(ROOT / "LICENSE").read_bytes(),
            ), mock.patch.object(
                self.regression, "_git_path_is_clean", return_value=False
            ), self.assertRaisesRegex(ValueError, "dirty Git state"):
                self.regression._expert_content_review(
                    path,
                    reference_fingerprint=reference_summary["source_fingerprint"],
                    root_fingerprint=root_summary["source_fingerprint"],
                    ai_readability_fingerprint="c" * 64,
                    evaluation_date=date(2026, 7, 14),
                )

    def test_complete_expert_review_requires_clean_head_config_bytes(self) -> None:
        path = self.regression.DEFAULT_RELEASE_REVIEW_CONFIG
        current = path.read_bytes()
        with mock.patch.object(
            self.regression, "_git_path_is_tracked", return_value=True
        ), mock.patch.object(
            self.regression, "_git_head_blob", return_value=b"different HEAD bytes"
        ), self.assertRaisesRegex(ValueError, "config differs from its HEAD blob"):
            self.regression._require_default_release_review_config(
                path, current_bytes=current
            )

        with mock.patch.object(
            self.regression, "_git_path_is_tracked", return_value=True
        ), mock.patch.object(
            self.regression, "_git_head_blob", return_value=current
        ), mock.patch.object(
            self.regression, "_git_path_is_clean", return_value=False
        ), self.assertRaisesRegex(ValueError, "config has dirty Git state"):
            self.regression._require_default_release_review_config(
                path, current_bytes=current
            )

        with mock.patch.object(
            self.regression, "_git_path_is_tracked", return_value=True
        ), mock.patch.object(
            self.regression, "_git_head_blob", return_value=current
        ), mock.patch.object(
            self.regression, "_git_path_is_clean", return_value=True
        ):
            self.regression._require_default_release_review_config(
                path, current_bytes=current
            )

    def test_expert_review_attestation_rejects_unknown_fields_and_future_date(self) -> None:
        root_fixture = _root_content_fixture()
        root_summary = self.regression._root_content_summary(
            {"root_content": root_fixture}, fresh_root_content=root_fixture
        )
        reference_fixture = _reference_content_fixture()
        reference_summary = self.regression._reference_content_summary(
            {"reference_content": reference_fixture},
            fresh_reference_content=reference_fixture,
        )
        config = _release_review_config(
            complete=True,
            reference_fingerprint=reference_summary["source_fingerprint"],
            root_fingerprint=root_summary["source_fingerprint"],
            ai_readability_fingerprint="c" * 64,
            evidence=[_expert_evidence()],
        )
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "release-review.yaml"
            _write_release_review_config(path, config)
            path.write_text(
                path.read_text(encoding="utf-8") + "  unknown_field: true\n",
                encoding="utf-8",
            )
            with _mock_attestation_storage(
                self.regression
            ), self.assertRaisesRegex(ValueError, "fields must exactly"):
                self.regression._expert_content_review(
                    path,
                    reference_fingerprint=reference_summary["source_fingerprint"],
                    root_fingerprint=root_summary["source_fingerprint"],
                    ai_readability_fingerprint="c" * 64,
                    evaluation_date=date(2026, 7, 14),
                )

            config["expert_content_review_attestation"]["attested_on"] = "2026-07-15"
            _write_release_review_config(path, config)
            with _mock_attestation_storage(
                self.regression
            ), self.assertRaisesRegex(ValueError, "non-future ISO date"):
                self.regression._expert_content_review(
                    path,
                    reference_fingerprint=reference_summary["source_fingerprint"],
                    root_fingerprint=root_summary["source_fingerprint"],
                    ai_readability_fingerprint="c" * 64,
                    evaluation_date=date(2026, 7, 14),
                )

    def test_release_report_schema_is_additive_and_deterministic(self) -> None:
        fixture = _reference_content_fixture()
        reference_summary = self.regression._reference_content_summary(
            {"reference_content": fixture},
            fresh_reference_content=fixture,
        )
        root_fixture = _root_content_fixture()
        root_summary = self.regression._root_content_summary(
            {"root_content": root_fixture}, fresh_root_content=root_fixture
        )
        expert_review = _incomplete_expert_review_fixture()
        content_readiness = self.regression._content_readiness(
            reference_summary, root_summary, expert_review
        )
        blockers, advisories = self.regression._reference_content_findings(
            reference_summary
        )
        result = self.regression.Result(
            mode="strict",
            status="current-contract-fail",
            authoring_gate="current-contract-fail",
            release_gate="release-not-ready",
            strict=True,
            baseline_comparison="not-numerically-comparable",
            evidence_scope="deterministic-fixtures",
            content_audit_summary={
                "description_recommended_over_budget_count": 119,
                "review_states": {"KEEP": 1},
                "review_reasons": {},
            },
            reference_content_summary=reference_summary,
            root_content_summary=root_summary,
            content_readiness=content_readiness,
            coverage_gate_summary={
                "status": "pass",
                "required_skill_count": 11,
                "pass_count": 11,
                "fail_count": 0,
                "not_required_count": 159,
                "failing_skills": [],
            },
            blockers=blockers,
            release_blockers=blockers
            + [
                self.regression.Finding(
                    "readability-review-release-gate",
                    "config/professionalism-release-review.yaml"
                    "#readability_review_attestation",
                    "formal release requires current readability review",
                ),
                self.regression.Finding(
                    "professional-completeness-review-release-gate",
                    "config/professionalism-release-review.yaml"
                    "#professional_completeness_review_attestation",
                    "formal release requires current professional completeness review",
                ),
            ],
            advisories=advisories,
            summary={"blocker_count": len(blockers), "advisory_count": 1},
            limitations=["Static evidence only."],
        )
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            self.regression._write(directory, result)
            self.assertEqual(
                ["professionalism-regression-report.json"],
                sorted(path.name for path in directory.iterdir()),
            )
            first = {
                path.name: path.read_bytes() for path in sorted(directory.iterdir())
            }
            self.regression._write(directory, result)
            second = {
                path.name: path.read_bytes() for path in sorted(directory.iterdir())
            }
            self.assertEqual(first, second)

            regression = json.loads(
                (directory / "professionalism-regression-report.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertIs(type(result.schema_version), int)
            self.assertEqual(
                self.regression.PROFESSIONALISM_REPORT_SCHEMA_VERSION,
                result.schema_version,
            )
            self.assertIs(type(regression["schema_version"]), int)
            self.assertEqual(result.schema_version, regression["schema_version"])
            self.assertEqual(
                [
                    "schema_version",
                    "mode",
                    "status",
                    "authoring_gate",
                    "release_gate",
                    "strict",
                    "baseline_comparison",
                    "evidence_scope",
                    "content_audit_summary",
                    "ai_readability_summary",
                    "reference_content_summary",
                    "root_content_summary",
                    "content_readiness",
                    "coverage_gate_summary",
                    "expert_panel_release_manifest",
                    "professional_review_cost_fixtures",
                    "blockers",
                    "release_blockers",
                    "advisories",
                    "summary",
                    "limitations",
                ],
                list(regression),
            )
            self.assertFalse(regression["reference_content_summary"]["strict_ready"])
            self.assertTrue(regression["root_content_summary"]["strict_ready"])
            self.assertEqual(10, regression["content_readiness"]["schema_version"])
            self.assertFalse(
                regression["content_readiness"]["aggregate"][
                    "readability_review_current"
                ]
            )
            self.assertFalse(
                regression["content_readiness"]["aggregate"][
                    "professional_completeness_review_current"
                ]
            )
            self.regression._write(directory, result, release_projection=True)
            markdown = (
                directory / "professionalism-regression-report.md"
            ).read_text(encoding="utf-8")
            self.assertIn("Reference strict gate: `false`", markdown)
            self.assertIn("Root strict gate: `true`", markdown)
            self.assertIn(
                "Foundation content classes: "
                f"compact={root_summary['foundation_compact_capabilities']}",
                markdown,
            )
            self.assertIn(
                f"complex={root_summary['foundation_complex_capabilities']} "
                "(target<=500; hard<=600",
                markdown,
            )
            self.assertIn("target overages require readability disposition", markdown)
            self.assertIn("Readability expert review current: `false`", markdown)
            self.assertIn(
                "Professional-completeness expert review current: `false`",
                markdown,
            )
            self.assertIn("Professional coverage gate: `pass`", markdown)
            self.assertIn("Formal release gate: **release-not-ready**", markdown)
            self.assertIn("## Release Blockers", markdown)
            self.assertNotIn("not a CI release gate", markdown)

    def test_coverage_matrix_is_fresh_and_policy_gated(self) -> None:
        report = json.loads(
            (ROOT / "reports/professional-coverage-matrix.json").read_text(
                encoding="utf-8"
            )
        )
        summary = self.regression._coverage_gate_summary(
            report,
            ROOT / "config/professionalism-release-review.yaml",
        )
        self.assertEqual("pass", summary["status"])
        self.assertEqual(10, summary["required_skill_count"])
        self.assertEqual(0, summary["fail_count"])

        stale = json.loads(json.dumps(report))
        stale["coverage_policy"]["fingerprint"]["value"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "stale or non-canonical"):
            self.regression._coverage_gate_summary(
                stale,
                ROOT / "config/professionalism-release-review.yaml",
            )

    def test_benchmark_report_is_fresh(self) -> None:
        report = json.loads(
            (ROOT / "reports/professional-benchmarks-report.json").read_text(
                encoding="utf-8"
            )
        )
        self.regression._validate_fresh_benchmark_report(report)

        stale = json.loads(json.dumps(report))
        stale["results"][0]["with_skill_score"] += 1
        with self.assertRaisesRegex(ValueError, "stale or non-canonical"):
            self.regression._validate_fresh_benchmark_report(stale)

    def test_coverage_failure_is_a_release_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            policy = Path(raw) / "release-review.yaml"
            policy.write_text(
                "decisions:\n"
                "  - id: release-critical-professional-coverage\n"
                "    kind: professional-coverage-gate\n"
                "    schema_version: 1\n"
                "    requirements:\n"
                "      reliability-observability-gate:\n"
                "        - registered\n"
                "        - pressure_covered\n",
                encoding="utf-8",
            )
            report = self.regression._load_coverage_evaluator().build_coverage_matrix(
                policy
            )
            summary = self.regression._coverage_gate_summary(report, policy)
        self.assertEqual("fail", summary["status"])
        findings = self.regression._coverage_gate_findings(summary)
        self.assertEqual(1, len(findings))
        self.assertEqual("professional-coverage-gate", findings[0].category)
        self.assertEqual("reliability-observability-gate", findings[0].target)

    def test_hookless_snapshot_is_not_reported_as_numeric_comparison(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "baseline.json"
            path.write_text(
                json.dumps({"hookless_schema_version": 2}), encoding="utf-8"
            )
            self.assertEqual(
                self.regression._baseline_state(path),
                "not-numerically-comparable",
            )


if __name__ == "__main__":
    unittest.main()
