from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate-professionalism-regression.py"
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("validate_professionalism_regression", SCRIPT)
assert SPEC and SPEC.loader
REGRESSION = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = REGRESSION
SPEC.loader.exec_module(REGRESSION)


RELEASE_REVIEW_WARNING = {
    "target": "src/foundation/capabilities/engineering-stage-professionalism/SKILL.md",
    "path": "src/foundation/capabilities/engineering-stage-professionalism/SKILL.md",
    "message": "Evidence Contract weak: evidence_contract_strength score 2/5 needs review",
    "warning_type": "weak_evidence_contract_strength",
    "type": "weak_evidence_contract_strength",
    "scope": "enhanced-foundation-capability",
    "release_relevance": "release-review-required",
}


def _base_skill_eval(
    warnings: list[str] | None = None,
    total: int = 50,
    status: str = "acceptable",
    extra_items: list[dict] | None = None,
) -> dict:
    items = [
        {
            "name": "backend-change-builder",
            "path": "src/professional-skills/backend-change-builder/SKILL.md",
            "kind": "professional-skill",
            "total": total,
            "status": status,
            "warnings": warnings or [],
            "likely_missing_sections": [],
        },
        {
            "name": "agent-execution-discipline",
            "path": "src/foundation/capabilities/agent-execution-discipline/SKILL.md",
            "kind": "foundation-capability",
            "total": 40,
            "status": "acceptable",
            "warnings": [],
            "likely_missing_sections": [],
        },
        *(extra_items or []),
    ]
    return {
        "generated_at": "2026-01-01T00:00:00+00:00",
        "skills_checked": len(items),
        "warning_count": sum(len(item.get("warnings") or []) for item in items),
        "average_score": 45.0,
        "duplicate_template_warnings": [],
        "items": items,
    }


def _coverage_row(
    *,
    mode_matrix: str = "yes",
    proactive_triggers: str = "yes",
    evidence_contract: str = "yes",
    reference_loading_hint: str = "yes",
) -> dict:
    return {
        "name": "backend-change-builder",
        "path": "src/professional-skills/backend-change-builder/SKILL.md",
        "kind": "professional-skill",
        "score": 50,
        "status": "acceptable",
        "mode_matrix": mode_matrix,
        "proactive_triggers": proactive_triggers,
        "evidence_contract": evidence_contract,
        "output_contract": "yes",
        "failure_modes": "yes",
        "quality_gate": "yes",
        "reference_loading_hint": reference_loading_hint,
        "routing_coverage": "yes (1)",
        "benchmark_coverage": "yes (1)",
        "anti_bloat_status": "ok",
        "warnings": [],
    }


def _foundation_coverage_row(
    name: str = "agent-execution-discipline",
    path: str = "src/foundation/capabilities/agent-execution-discipline/SKILL.md",
    warnings: list[str] | None = None,
) -> dict:
    return {
        "name": name,
        "path": path,
        "kind": "foundation-capability",
        "score": 40,
        "status": "acceptable",
        "mode_matrix": "n/a",
        "proactive_triggers": "n/a",
        "evidence_contract": "yes",
        "output_contract": "yes",
        "failure_modes": "yes",
        "quality_gate": "yes",
        "reference_loading_hint": "yes",
        "routing_coverage": "yes (1)",
        "benchmark_coverage": "yes (1)",
        "anti_bloat_status": "ok",
        "warnings": warnings or [],
    }


def _base_coverage(*, extra_rows: list[dict] | None = None, **overrides: str) -> dict:
    foundation = {
        "name": "agent-execution-discipline",
        "path": "src/foundation/capabilities/agent-execution-discipline/SKILL.md",
        "kind": "foundation-capability",
        "score": 40,
        "status": "acceptable",
        "mode_matrix": "n/a",
        "proactive_triggers": "n/a",
        "evidence_contract": "yes",
        "output_contract": "yes",
        "failure_modes": "yes",
        "quality_gate": "yes",
        "reference_loading_hint": "yes",
        "routing_coverage": "yes (1)",
        "benchmark_coverage": "yes (1)",
        "anti_bloat_status": "ok",
        "warnings": [],
    }
    rows = [_coverage_row(**overrides), foundation, *(extra_rows or [])]
    return {
        "generated_at": "2026-01-01T00:00:00+00:00",
        "rows_checked": len(rows),
        "rows": rows,
    }


def _base_benchmarks(
    *,
    baseline_hits: int = 1,
    delta_score: int = 6,
    quality_status: str = "pass",
    errors: list[str] | None = None,
) -> dict:
    hits = ["claim completion without evidence"] if baseline_hits else []
    return {
        "generated_at": "2026-01-01T00:00:00+00:00",
        "mode": "auto",
        "cases_checked": 1,
        "comparison_cases_checked": 1,
        "actual_output_comparison": "test fixture",
        "errors": [],
        "results": [
            {
                "path": "evals/professional-benchmarks/backend/sample",
                "case_id": "evals/professional-benchmarks/backend/sample",
                "expected_stage": "bug-fix",
                "expected_skills": ["backend-change-builder"],
                "expected_capabilities": ["agent-execution-discipline"],
                "schema_status": "pass",
                "comparison_status": "pass",
                "benchmark_quality_status": quality_status,
                "baseline_defect_hits": hits,
                "with_skill_obligation_coverage": [
                    "selected stage",
                    "selected professional skill",
                    "selected capabilities",
                    "expected hidden risks",
                    "expected evidence",
                    "expected output obligations",
                    "residual risk",
                    "next gate",
                    "validation command or not-verified disclosure",
                ],
                "delta_score": delta_score,
                "remaining_gaps": [],
                "professional_delta_summary": {
                    "delta_score": delta_score,
                    "remaining_gaps": [],
                },
                "errors": errors or [],
            }
        ],
    }


def _depth_dimensions(domain_judgment_depth: int = 13) -> dict:
    return {
        "professional_responsibility_clarity": 8,
        "domain_judgment_depth": domain_judgment_depth,
        "decision_criteria_completeness": 10,
        "failure_mode_specificity": 10,
        "evidence_contract_completeness": 10,
        "output_contract_actionability": 9,
        "boundary_and_ownership_precision": 8,
        "tradeoff_priority_quality": 6,
        "anti_pattern_quality": 6,
        "validation_semantics": 5,
        "residual_risk_handling": 3,
    }


def _depth_item(
    *,
    name: str,
    path: str,
    kind: str,
    score: int = 90,
    status: str = "release-grade",
    warnings: list[dict] | None = None,
    domain_judgment_depth: int = 13,
    judgment_axis_source: str | None = None,
) -> dict:
    return {
        "name": name,
        "path": path,
        "kind": kind,
        "professionalism_score": score,
        "status": status,
        "dimensions": _depth_dimensions(domain_judgment_depth),
        "judgment_axes": [
            "owned decision boundary",
            "evidence requirement",
            "failure prevented",
            "validation proof limit",
        ],
        "judgment_axis_source": judgment_axis_source or f"items.{name}",
        "warnings": warnings or [],
        "recommended_fixes": [],
    }


def _base_depth(
    *,
    backend_score: int = 90,
    backend_status: str = "release-grade",
    backend_warnings: list[dict] | None = None,
    backend_domain_judgment_depth: int = 13,
    foundation_score: int = 90,
    foundation_status: str = "release-grade",
    foundation_warnings: list[dict] | None = None,
    extra_items: list[dict] | None = None,
) -> dict:
    items = [
        _depth_item(
            name="backend-change-builder",
            path="src/professional-skills/backend-change-builder/SKILL.md",
            kind="professional-skill",
            score=backend_score,
            status=backend_status,
            warnings=backend_warnings,
            domain_judgment_depth=backend_domain_judgment_depth,
        ),
        _depth_item(
            name="agent-execution-discipline",
            path="src/foundation/capabilities/agent-execution-discipline/SKILL.md",
            kind="foundation-capability",
            score=foundation_score,
            status=foundation_status,
            warnings=foundation_warnings,
        ),
        *(extra_items or []),
    ]
    return {
        "generated_at": "2026-01-01T00:00:00+00:00",
        "items_checked": len(items),
        "warning_count": sum(len(item.get("warnings") or []) for item in items),
        "average_professionalism_score": round(
            sum(int(item.get("professionalism_score") or 0) for item in items) / len(items),
            2,
        ),
        "score_model": (
            "100-point professional-depth rubric from "
            "docs/skill_professionalism_standard/SKILL_PROFESSIONALISM_DIMENSION_RUBRIC.md"
        ),
        "score_model_path": "docs/skill_professionalism_standard/SKILL_PROFESSIONALISM_DIMENSION_RUBRIC.md",
        "judgment_axis_registry": "docs/skill_professionalism_standard/professionalism-axes.yaml",
        "metadata_warnings": [],
        "items": items,
    }


def _write_reports(
    reports_dir: Path,
    *,
    skill_eval: dict | None = None,
    coverage: dict | None = None,
    benchmarks: dict | None = None,
    depth: dict | None = None,
    content_audit: dict | None = None,
) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "skill-professionalism-eval.json").write_text(
        json.dumps(skill_eval or _base_skill_eval()),
        encoding="utf-8",
    )
    (reports_dir / "professional-coverage-matrix.json").write_text(
        json.dumps(coverage or _base_coverage()),
        encoding="utf-8",
    )
    (reports_dir / "professional-benchmarks-report.json").write_text(
        json.dumps(benchmarks or _base_benchmarks()),
        encoding="utf-8",
    )
    (reports_dir / "skill-professionalism-depth.json").write_text(
        json.dumps(depth or _base_depth()),
        encoding="utf-8",
    )
    if content_audit is not None:
        (reports_dir / "skill-content-audit.json").write_text(
            json.dumps(content_audit),
            encoding="utf-8",
        )


def _write_routing_case(routing_dir: Path, *, forbidden: bool = True) -> None:
    routing_dir.mkdir(parents=True, exist_ok=True)
    forbidden_block = (
        "forbidden:\n"
        "  skills:\n"
        "    - frontend-change-builder\n"
        "  capabilities:\n"
        "    - cache-design\n"
        "  domain_extensions:\n"
        "    - web3-product-extension\n"
        "  quality_gates:\n"
        "    - delivery gate\n"
        if forbidden
        else "forbidden: {}\n"
    )
    (routing_dir / "backend-risk.yaml").write_text(
        (
            "---\n"
            "id: backend-risk\n"
            "description: Backend risk fixture.\n"
            "prompt: Fix a backend issue.\n"
            "expected:\n"
            "  complexity: L3\n"
            "  risk_level: high\n"
            "  skills:\n"
            "    - backend-change-builder\n"
            "  capabilities:\n"
            "    - agent-execution-discipline\n"
            "  domain_extensions: []\n"
            "  quality_gates:\n"
            "    - implementation gate\n"
            f"{forbidden_block}"
        ),
        encoding="utf-8",
    )


def _run(
    reports_dir: Path,
    baseline: Path,
    routing_dir: Path,
    *extra: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--reports-dir",
            str(reports_dir),
            "--baseline",
            str(baseline),
            "--routing-dir",
            str(routing_dir),
            "--release-review-config",
            str(baseline.parent / "professionalism-release-review.yaml"),
            *extra,
        ],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=False,
    )


def _release_review_config(
    path: Path,
    *,
    decision: str = "accepted_for_current_release",
    target: str = "src/foundation/capabilities/engineering-stage-professionalism/SKILL.md",
    warning_message: str = "Evidence Contract weak: evidence_contract_strength score 2/5 needs review",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        (
            "schema_version: 1\n"
            "review_owner: changeforge-maintainers\n"
            "reviewed_at: \"2026-06-10\"\n"
            "decisions:\n"
            f"  - target: {target}\n"
            "    warning_type: weak_evidence_contract_strength\n"
            f"    warning_message: \"{warning_message}\"\n"
            "    scope: enhanced-foundation-capability\n"
            "    release_relevance: release-review-required\n"
            f"    decision: {decision}\n"
            "    reason: \"Reviewed for test release.\"\n"
            "    follow_up_phase: \"P2 enhanced-foundation-hardening\"\n"
            "    review_after: \"2026-07-15\"\n"
        ),
        encoding="utf-8",
    )


def _release_review_result(config: Path, warnings: list[dict]) -> dict:
    return REGRESSION._release_review_reconciliation({"warnings": warnings}, config)


class ValidateProfessionalismRegressionTests(unittest.TestCase):
    def _seed_baseline(self, tmp: Path) -> tuple[Path, Path, Path]:
        reports_dir = tmp / "reports"
        routing_dir = tmp / "routing"
        baseline = tmp / "config" / "professionalism-baseline.yaml"
        _write_reports(reports_dir)
        _write_routing_case(routing_dir, forbidden=True)
        result = _run(reports_dir, baseline, routing_dir, "--update-baseline")
        self.assertEqual(result.returncode, 0, result.stderr)
        return reports_dir, routing_dir, baseline

    def test_score_regression_over_threshold_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            reports_dir, routing_dir, baseline = self._seed_baseline(Path(raw))
            _write_reports(reports_dir, skill_eval=_base_skill_eval(total=48))
            result = _run(reports_dir, baseline, routing_dir)
            self.assertEqual(result.returncode, 1)
            report = json.loads((reports_dir / "professionalism-regression-report.json").read_text())
            self.assertTrue(any(item["category"] == "score-regression" for item in report["blockers"]))

    def test_missing_depth_report_is_required_input_error(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            reports_dir = tmp / "reports"
            routing_dir = tmp / "routing"
            baseline = tmp / "config" / "professionalism-baseline.yaml"
            _write_reports(reports_dir)
            (reports_dir / "skill-professionalism-depth.json").unlink()
            _write_routing_case(routing_dir, forbidden=True)
            result = _run(reports_dir, baseline, routing_dir, "--update-baseline")
            self.assertEqual(result.returncode, 1)
            self.assertIn("skill-professionalism-depth.json", result.stderr)

    def test_baseline_snapshot_records_professional_depth_source_report(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            reports_dir, _routing_dir, baseline = self._seed_baseline(Path(raw))
            updated = baseline.read_text(encoding="utf-8")
            self.assertIn("skill_professionalism_depth: reports/skill-professionalism-depth.json", updated)
            self.assertIn("professional_depth:", updated)
            self.assertIn("judgment_axis_registry: docs/skill_professionalism_standard/professionalism-axes.yaml", updated)
            readiness = json.loads((reports_dir / "professionalism-release-readiness.json").read_text())
            self.assertIn("professionalism_depth_summary", readiness)

    def test_professional_depth_score_regression_fails_independently(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            reports_dir, routing_dir, baseline = self._seed_baseline(Path(raw))
            _write_reports(reports_dir, depth=_base_depth(backend_score=88))
            result = _run(reports_dir, baseline, routing_dir)
            self.assertEqual(result.returncode, 1)
            report = json.loads((reports_dir / "professionalism-regression-report.json").read_text())
            self.assertTrue(
                any(item["category"] == "professional-depth-score-regression" for item in report["blockers"])
            )

    def test_professional_depth_core_dimension_regression_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            reports_dir, routing_dir, baseline = self._seed_baseline(Path(raw))
            _write_reports(reports_dir, depth=_base_depth(backend_domain_judgment_depth=11))
            result = _run(reports_dir, baseline, routing_dir)
            self.assertEqual(result.returncode, 1)
            report = json.loads((reports_dir / "professionalism-regression-report.json").read_text())
            self.assertTrue(
                any(item["category"] == "professional-depth-core-dimension-regression" for item in report["blockers"])
            )

    def test_strict_requires_item_specific_axes_for_key_foundation_capability(self) -> None:
        key_foundation = _depth_item(
            name="cache-design",
            path="src/foundation/capabilities/cache-design/SKILL.md",
            kind="foundation-capability",
            judgment_axis_source="default_axes.foundation-capability",
        )
        with tempfile.TemporaryDirectory() as raw:
            reports_dir, routing_dir, baseline = self._seed_baseline(Path(raw))
            _write_reports(reports_dir, depth=_base_depth(extra_items=[key_foundation]))
            result = _run(reports_dir, baseline, routing_dir, "--strict")
            self.assertEqual(result.returncode, 1)
            report = json.loads((reports_dir / "professionalism-regression-report.json").read_text())
            self.assertTrue(
                any(
                    item["category"] == "professional-depth-item-specific-axes-required"
                    for item in report["blockers"]
                )
            )

    def test_strict_allows_default_axes_for_non_key_foundation_capability(self) -> None:
        non_key_foundation = _depth_item(
            name="api-contract-design",
            path="src/foundation/capabilities/api-contract-design/SKILL.md",
            kind="foundation-capability",
            judgment_axis_source="default_axes.foundation-capability",
        )
        with tempfile.TemporaryDirectory() as raw:
            reports_dir, routing_dir, baseline = self._seed_baseline(Path(raw))
            _write_reports(reports_dir, depth=_base_depth(extra_items=[non_key_foundation]))
            result = _run(reports_dir, baseline, routing_dir, "--strict")
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_key_foundation_axis_policy_matches_depth_scope(self) -> None:
        self.assertIn("minimal-correct-implementation", REGRESSION.KEY_FOUNDATION_CAPABILITIES)
        self.assertIn("senior-programming-judgment-core", REGRESSION.KEY_FOUNDATION_CAPABILITIES)
        self.assertIn("senior-programming-judgment-core", REGRESSION.ENHANCED_FOUNDATION_CAPABILITIES)

    def test_update_baseline_reports_judgment_axis_source_changes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            reports_dir, routing_dir, baseline = self._seed_baseline(Path(raw))
            depth = _base_depth()
            depth["items"][0]["judgment_axis_source"] = "skills.backend-change-builder"
            _write_reports(reports_dir, depth=depth)
            result = _run(reports_dir, baseline, routing_dir, "--update-baseline")
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((reports_dir / "professionalism-regression-report.json").read_text())
            self.assertTrue(
                any(
                    item["target"] == "professional_depth.backend-change-builder.judgment_axis_source"
                    for item in report["baseline_changes"]
                )
            )

    def test_depth_review_required_warning_blocks_release_readiness_without_decision(self) -> None:
        depth_warning = {
            "type": "professionalism_score_below_release_threshold",
            "severity": "review-required",
            "message": "agent-execution-discipline professionalism_score 84/100 is below 85",
            "dimension": "professionalism_score",
        }
        depth = _base_depth(
            foundation_score=84,
            foundation_status="needs-review",
            foundation_warnings=[depth_warning],
        )
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            reports_dir = tmp / "reports"
            routing_dir = tmp / "routing"
            baseline = tmp / "config" / "professionalism-baseline.yaml"
            _write_reports(reports_dir, depth=depth)
            _write_routing_case(routing_dir, forbidden=True)
            self.assertEqual(_run(reports_dir, baseline, routing_dir, "--update-baseline").returncode, 0)
            _write_reports(reports_dir, depth=depth)
            result = _run(reports_dir, baseline, routing_dir)
            self.assertEqual(result.returncode, 0, result.stderr)
            readiness = json.loads((reports_dir / "professionalism-release-readiness.json").read_text())
            self.assertEqual(readiness["release_ready"], "blocked")
            self.assertEqual(readiness["professional_depth_review_required_warnings"], 1)
            self.assertEqual(readiness["release_review_required_warnings"], 1)
            self.assertEqual(readiness["release_review_decision"], "missing")
            self.assertEqual(readiness["warning_reconciliation"]["tracked_release_warnings"], 0)
            self.assertEqual(
                readiness["professional_depth_warning_reconciliation"]["tracked_release_warnings"],
                1,
            )
            self.assertEqual(readiness["latest_results_available"]["professional_depth_warnings"], 1)
            self.assertEqual(readiness["latest_results_available"]["professional_depth_needs_review_items"], 1)
            markdown = (reports_dir / "professionalism-release-readiness.md").read_text(encoding="utf-8")
            self.assertIn("## Professional Depth Summary", markdown)
            self.assertIn("## Professional Depth Warning Reconciliation", markdown)
            self.assertIn("Professional-depth", markdown)

    def test_release_readiness_surfaces_tighten_body_followup(self) -> None:
        content_audit = {
            "summary": {
                "classifications": {
                    "KEEP_AS_IS": 148,
                    "TIGHTEN_BODY": 17,
                },
                "heavy_professional": 0,
                "heavy_foundation": 0,
                "heavy_domain": 0,
                "split_candidates": 0,
                "low_professionalism": 0,
            },
            "common_lines": [f"duplicated line {index}" for index in range(52)],
        }
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            reports_dir = tmp / "reports"
            routing_dir = tmp / "routing"
            baseline = tmp / "config" / "professionalism-baseline.yaml"
            _write_reports(reports_dir, content_audit=content_audit)
            _write_routing_case(routing_dir, forbidden=True)
            result = _run(reports_dir, baseline, routing_dir, "--update-baseline")
            self.assertEqual(result.returncode, 0, result.stderr)
            readiness = json.loads((reports_dir / "professionalism-release-readiness.json").read_text())
            self.assertEqual(readiness["content_bloat_status"]["tighten_body"], 17)
            self.assertEqual(readiness["content_bloat_status"]["shared_duplicated_lines"], 52)
            row = next(item for item in readiness["checklist"] if item["item"] == "content efficiency follow-up")
            self.assertEqual(row["status"], "needs-review")
            self.assertFalse(row["blocking"])
            self.assertIn("TIGHTEN_BODY=17", row["notes"])
            markdown = (reports_dir / "professionalism-release-readiness.md").read_text(encoding="utf-8")
            self.assertIn("content efficiency follow-up", markdown)

    def test_release_readiness_counts_content_bloat_from_current_audit_shape(self) -> None:
        content_audit = {
            "summary": {
                "classifications": {
                    "KEEP_AS_IS": 165,
                },
                "heavy_professional": 0,
                "heavy_foundation": 0,
                "heavy_domain": 0,
                "split_candidates": 0,
                "low_professionalism": 0,
            },
            "common_lines": {
                f"duplicated line {index}": ["skill-a", "skill-b"]
                for index in range(44)
            },
        }
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            reports_dir = tmp / "reports"
            routing_dir = tmp / "routing"
            baseline = tmp / "config" / "professionalism-baseline.yaml"
            _write_reports(reports_dir, content_audit=content_audit)
            _write_routing_case(routing_dir, forbidden=True)
            result = _run(reports_dir, baseline, routing_dir, "--update-baseline")
            self.assertEqual(result.returncode, 0, result.stderr)
            readiness = json.loads((reports_dir / "professionalism-release-readiness.json").read_text())
            self.assertEqual(readiness["content_bloat_status"]["tighten_body"], 0)
            self.assertEqual(readiness["content_bloat_status"]["keep_as_is"], 165)
            self.assertEqual(readiness["content_bloat_status"]["shared_duplicated_lines"], 44)
            markdown = (reports_dir / "professionalism-release-readiness.md").read_text(encoding="utf-8")
            self.assertIn("- shared_duplicated_lines: 44", markdown)
            self.assertIn("- tighten_body: 0", markdown)

    def test_release_readiness_aggregates_content_classifications_when_summary_missing(self) -> None:
        content_audit = {
            "summary": {
                "heavy_professional": 0,
                "heavy_foundation": 0,
                "heavy_domain": 0,
                "split_candidates": 0,
                "low_professionalism": 0,
            },
            "skills": [
                {"name": "skill-a", "classification": "KEEP_AS_IS"},
                {"name": "skill-b", "classification": "KEEP_AS_IS"},
                {"name": "skill-c", "classification": "TIGHTEN_BODY"},
            ],
            "common_lines": {},
        }
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            reports_dir = tmp / "reports"
            routing_dir = tmp / "routing"
            baseline = tmp / "config" / "professionalism-baseline.yaml"
            _write_reports(reports_dir, content_audit=content_audit)
            _write_routing_case(routing_dir, forbidden=True)
            result = _run(reports_dir, baseline, routing_dir, "--update-baseline")
            self.assertEqual(result.returncode, 0, result.stderr)
            readiness = json.loads((reports_dir / "professionalism-release-readiness.json").read_text())
            self.assertEqual(readiness["content_bloat_status"]["tighten_body"], 1)
            self.assertEqual(readiness["content_bloat_status"]["keep_as_is"], 2)
            row = next(item for item in readiness["checklist"] if item["item"] == "content efficiency follow-up")
            self.assertEqual(row["status"], "needs-review")
            self.assertIn("TIGHTEN_BODY=1", row["notes"])

    def test_release_readiness_keeps_content_efficiency_not_run_without_classification_evidence(self) -> None:
        content_audit = {
            "summary": {
                "heavy_professional": 0,
                "heavy_foundation": 0,
                "heavy_domain": 0,
                "split_candidates": 0,
                "low_professionalism": 0,
            },
            "common_lines": {},
        }
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            reports_dir = tmp / "reports"
            routing_dir = tmp / "routing"
            baseline = tmp / "config" / "professionalism-baseline.yaml"
            _write_reports(reports_dir, content_audit=content_audit)
            _write_routing_case(routing_dir, forbidden=True)
            result = _run(reports_dir, baseline, routing_dir, "--update-baseline")
            self.assertEqual(result.returncode, 0, result.stderr)
            readiness = json.loads((reports_dir / "professionalism-release-readiness.json").read_text())
            self.assertEqual(readiness["content_bloat_status"]["tighten_body"], "unknown")
            row = next(item for item in readiness["checklist"] if item["item"] == "content efficiency follow-up")
            self.assertEqual(row["status"], "not-run")

    def test_known_warning_in_baseline_does_not_fail(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            reports_dir = tmp / "reports"
            routing_dir = tmp / "routing"
            baseline = tmp / "config" / "professionalism-baseline.yaml"
            _write_reports(reports_dir, skill_eval=_base_skill_eval(warnings=["known warning"]))
            _write_routing_case(routing_dir, forbidden=True)
            self.assertEqual(_run(reports_dir, baseline, routing_dir, "--update-baseline").returncode, 0)
            _write_reports(reports_dir, skill_eval=_base_skill_eval(warnings=["known warning"]))
            result = _run(reports_dir, baseline, routing_dir)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((reports_dir / "professionalism-regression-report.json").read_text())
            self.assertEqual(report["summary"]["known_warnings"], 1)

    def test_release_readiness_discloses_non_key_skill_eval_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            reports_dir = tmp / "reports"
            routing_dir = tmp / "routing"
            baseline = tmp / "config" / "professionalism-baseline.yaml"
            accepted_warning = "long Markdown table in SKILL.md body (16 rows); consider moving deep table to references"
            non_key_warning = "long Markdown table in SKILL.md body (16 rows); consider moving deep table to references"
            skill_eval = _base_skill_eval(
                warnings=[],
                extra_items=[
                    {
                        "name": "code-review",
                        "path": "src/foundation/capabilities/code-review/SKILL.md",
                        "kind": "foundation-capability",
                        "total": 48,
                        "status": "acceptable",
                        "warnings": [accepted_warning],
                        "likely_missing_sections": [],
                    },
                    {
                        "name": "api-contract-design",
                        "path": "src/foundation/capabilities/api-contract-design/SKILL.md",
                        "kind": "foundation-capability",
                        "total": 48,
                        "status": "acceptable",
                        "warnings": [non_key_warning],
                        "likely_missing_sections": [],
                    }
                ],
            )
            coverage = _base_coverage(
                extra_rows=[
                    _foundation_coverage_row(
                        "code-review",
                        "src/foundation/capabilities/code-review/SKILL.md",
                    )
                ]
            )
            _write_reports(reports_dir, skill_eval=skill_eval, coverage=coverage)
            _write_routing_case(routing_dir, forbidden=True)
            self.assertEqual(_run(reports_dir, baseline, routing_dir, "--update-baseline").returncode, 0)
            _write_reports(reports_dir, skill_eval=skill_eval, coverage=coverage)
            result = _run(reports_dir, baseline, routing_dir)
            self.assertEqual(result.returncode, 0, result.stderr)
            readiness = json.loads((reports_dir / "professionalism-release-readiness.json").read_text())
            reconciliation = readiness["warning_reconciliation"]
            self.assertEqual(readiness["release_blocking_professionalism_warnings"], 0)
            self.assertEqual(reconciliation["total_skill_professionalism_warnings"], 2)
            self.assertEqual(reconciliation["tracked_release_warnings"], 1)
            self.assertEqual(reconciliation["accepted_known_warnings"], 1)
            self.assertEqual(reconciliation["release_blocking_warnings"], 0)
            self.assertEqual(reconciliation["non_key_foundation_advisory_warnings"], 1)
            api_warning = next(
                item for item in reconciliation["warnings"]
                if item["target"] == "src/foundation/capabilities/api-contract-design/SKILL.md"
            )
            self.assertEqual(api_warning["message"], non_key_warning)
            self.assertEqual(api_warning["release_relevance"], "advisory-only")
            accepted = next(
                item for item in reconciliation["warnings"]
                if item["target"] == "src/foundation/capabilities/code-review/SKILL.md"
            )
            self.assertEqual(accepted["release_relevance"], "accepted-known-warning")
            markdown = (reports_dir / "professionalism-release-readiness.md").read_text(encoding="utf-8")
            self.assertIn("## Skill Professionalism Warning Reconciliation", markdown)
            self.assertIn("non_key_foundation_advisory_warnings: 1", markdown)
            self.assertIn("accepted-known-warning", markdown)
            self.assertIn("## Release Review Decisions", markdown)
            self.assertEqual(readiness["release_review_decision"], "accepted")
            self.assertEqual(readiness["release_review_required_warnings"], 0)
            self.assertEqual(readiness["release_review_decisions"]["missing"], 0)

    def test_release_review_required_warning_without_decision_blocks_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            result = _release_review_result(Path(raw) / "missing.yaml", [RELEASE_REVIEW_WARNING])
            self.assertEqual(result["decision"], "missing")
            self.assertEqual(result["summary"]["missing"], 1)
            self.assertTrue(
                any(item["category"] == "release-review-decision-missing" for item in result["blockers"])
            )

    def test_release_review_accepted_decision_allows_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            config = Path(raw) / "release-review.yaml"
            _release_review_config(config)
            result = _release_review_result(config, [RELEASE_REVIEW_WARNING])
            self.assertEqual(result["decision"], "accepted")
            self.assertEqual(result["summary"]["accepted_for_current_release"], 1)
            self.assertEqual(result["blockers"], [])

    def test_release_review_blocks_release_decision_blocks_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            config = Path(raw) / "release-review.yaml"
            _release_review_config(config, decision="blocks_release")
            result = _release_review_result(config, [RELEASE_REVIEW_WARNING])
            self.assertEqual(result["decision"], "blocked")
            self.assertEqual(result["summary"]["blocks_release"], 1)
            self.assertTrue(
                any(item["category"] == "release-review-decision-blocks-release" for item in result["blockers"])
            )

    def test_release_review_stale_decision_blocks_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            config = Path(raw) / "release-review.yaml"
            _release_review_config(
                config,
                target="src/foundation/capabilities/skill-authoring-expert/SKILL.md",
            )
            result = _release_review_result(config, [RELEASE_REVIEW_WARNING])
            self.assertNotEqual(result["decision"], "accepted")
            self.assertEqual(result["summary"]["stale"], 1)
            self.assertTrue(
                any(item["category"] == "release-review-decision-stale" for item in result["blockers"])
            )

    def test_advisory_warning_does_not_need_release_review_decision(self) -> None:
        advisory = {
            **RELEASE_REVIEW_WARNING,
            "release_relevance": "advisory-only",
            "scope": "non-key-foundation-capability",
        }
        with tempfile.TemporaryDirectory() as raw:
            result = _release_review_result(Path(raw) / "missing.yaml", [advisory])
            self.assertEqual(result["decision"], "accepted")
            self.assertEqual(result["release_review_required_warnings"], 0)
            self.assertEqual(result["blockers"], [])

    def test_new_warning_over_budget_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            reports_dir, routing_dir, baseline = self._seed_baseline(Path(raw))
            _write_reports(reports_dir, skill_eval=_base_skill_eval(warnings=["new warning"]))
            result = _run(reports_dir, baseline, routing_dir)
            self.assertEqual(result.returncode, 1)
            report = json.loads((reports_dir / "professionalism-regression-report.json").read_text())
            self.assertTrue(any(item["category"] == "new-warning-budget" for item in report["blockers"]))

    def test_new_missing_mode_matrix_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            reports_dir, routing_dir, baseline = self._seed_baseline(Path(raw))
            _write_reports(reports_dir, coverage=_base_coverage(mode_matrix="no"))
            result = _run(reports_dir, baseline, routing_dir)
            self.assertEqual(result.returncode, 1)
            report = json.loads((reports_dir / "professionalism-regression-report.json").read_text())
            self.assertTrue(any(item["category"] == "missing-mode-matrix" for item in report["blockers"]))

    def test_new_reference_without_loading_hint_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            reports_dir, routing_dir, baseline = self._seed_baseline(Path(raw))
            _write_reports(reports_dir, coverage=_base_coverage(reference_loading_hint="no"))
            result = _run(reports_dir, baseline, routing_dir)
            self.assertEqual(result.returncode, 1)
            report = json.loads((reports_dir / "professionalism-regression-report.json").read_text())
            self.assertTrue(any(item["category"] == "reference-loading-hint-regression" for item in report["blockers"]))

    def test_new_empty_benchmark_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            reports_dir, routing_dir, baseline = self._seed_baseline(Path(raw))
            _write_reports(reports_dir, benchmarks=_base_benchmarks(baseline_hits=0))
            result = _run(reports_dir, baseline, routing_dir)
            self.assertEqual(result.returncode, 1)
            report = json.loads((reports_dir / "professionalism-regression-report.json").read_text())
            self.assertTrue(any(item["category"] == "empty-benchmark-regression" for item in report["blockers"]))

    def test_routing_case_without_forbidden_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            reports_dir, routing_dir, baseline = self._seed_baseline(Path(raw))
            _write_routing_case(routing_dir, forbidden=False)
            result = _run(reports_dir, baseline, routing_dir)
            self.assertEqual(result.returncode, 1)
            report = json.loads((reports_dir / "professionalism-regression-report.json").read_text())
            self.assertTrue(any(item["category"] == "routing-forbidden-regression" for item in report["blockers"]))

    def test_report_only_writes_report_without_failing(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            reports_dir, routing_dir, baseline = self._seed_baseline(Path(raw))
            _write_reports(reports_dir, skill_eval=_base_skill_eval(total=48))
            result = _run(reports_dir, baseline, routing_dir, "--report-only")
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((reports_dir / "professionalism-regression-report.json").read_text())
            self.assertEqual(report["status"], "report-only")
            self.assertTrue(report["blockers"])

    def test_update_baseline_writes_changes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            reports_dir, routing_dir, baseline = self._seed_baseline(Path(raw))
            _write_reports(reports_dir, benchmarks=_base_benchmarks(delta_score=8))
            result = _run(reports_dir, baseline, routing_dir, "--update-baseline")
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((reports_dir / "professionalism-regression-report.json").read_text())
            self.assertTrue(report["baseline_changes"])
            updated = baseline.read_text(encoding="utf-8")
            self.assertIn("delta_score: 8", updated)

    def test_schema_or_io_error_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            reports_dir = tmp / "reports"
            routing_dir = tmp / "routing"
            baseline = tmp / "config" / "professionalism-baseline.yaml"
            reports_dir.mkdir()
            result = _run(reports_dir, baseline, routing_dir)
            self.assertEqual(result.returncode, 1)
            self.assertIn("missing required report", result.stderr)


if __name__ == "__main__":
    unittest.main()
