from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate-professionalism-regression.py"


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


def _write_reports(
    reports_dir: Path,
    *,
    skill_eval: dict | None = None,
    coverage: dict | None = None,
    benchmarks: dict | None = None,
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
            *extra,
        ],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=False,
    )


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
