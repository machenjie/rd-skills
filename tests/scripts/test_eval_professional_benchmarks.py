from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "eval-professional-benchmarks.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("eval_professional_benchmarks", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class EvalProfessionalBenchmarksTests(unittest.TestCase):
    def test_valid_case_schema_passes_registry_checks(self) -> None:
        module = _load_module()
        registry = {
            "skills": {"backend-change-builder"},
            "capabilities": {"agent-execution-discipline", "regression-testing"},
        }
        with tempfile.TemporaryDirectory() as tmp:
            case_dir = Path(tmp) / "backend" / "case"
            case_dir.mkdir(parents=True)
            (case_dir / "prompt.md").write_text(
                "Fix a backend bug and require same-pattern scan plus regression evidence.",
                encoding="utf-8",
            )
            (case_dir / "expected.yaml").write_text(
                "\n".join(
                    [
                        "expected_stage: bug-fix",
                        "expected_professional_skill: backend-change-builder",
                        "expected_capabilities:",
                        "  - agent-execution-discipline",
                        "  - regression-testing",
                        "expected_hidden_risks:",
                        "  - local fix without same-pattern scan",
                        "  - unverified authorization regression",
                        "expected_evidence:",
                        "  - regression validation evidence",
                        "  - same-pattern scan output",
                        "forbidden_behaviors:",
                        "  - claim completion without command output",
                        "  - patch only one endpoint without sibling scan",
                        "expected_output_obligations:",
                        "  - validation evidence for backend regression and residual risk",
                        "  - inspected backend boundaries",
                        "  - next gate named",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            result = module._evaluate_case(case_dir, registry, {"bug-fix"}, "schema-only")
            self.assertEqual(result.errors, [])
            self.assertEqual(result.schema_status, "pass")
            self.assertEqual(result.comparison_status, "schema-only")

    def test_missing_forbidden_behaviors_is_error(self) -> None:
        module = _load_module()
        registry = {"skills": {"backend-change-builder"}, "capabilities": {"regression-testing"}}
        with tempfile.TemporaryDirectory() as tmp:
            case_dir = Path(tmp) / "backend" / "case"
            case_dir.mkdir(parents=True)
            (case_dir / "prompt.md").write_text(
                "Fix a backend bug with enough concrete detail to require regression validation.",
                encoding="utf-8",
            )
            (case_dir / "expected.yaml").write_text(
                "\n".join(
                    [
                        "expected_stage: bug-fix",
                        "expected_professional_skill: backend-change-builder",
                        "expected_capabilities:",
                        "  - regression-testing",
                        "expected_hidden_risks:",
                        "  - tenant authorization regression gap",
                        "  - missing denied-path backend coverage",
                        "expected_evidence:",
                        "  - validation evidence",
                        "  - regression command output",
                        "forbidden_behaviors: []",
                        "expected_output_obligations:",
                        "  - validation evidence for backend regression",
                        "  - residual tenant authorization risk",
                        "  - next quality-test gate",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            result = module._evaluate_case(case_dir, registry, {"bug-fix"}, "auto")
            self.assertTrue(any("forbidden_behaviors" in error for error in result.errors))
            self.assertEqual(result.schema_status, "fail")
            self.assertTrue(result.missing_expected_items)

    def test_comparison_scores_with_skill_output_higher_than_baseline(self) -> None:
        module = _load_module()
        registry = {
            "skills": {"backend-change-builder"},
            "capabilities": {"agent-execution-discipline", "regression-testing"},
        }
        with tempfile.TemporaryDirectory() as tmp:
            case_dir = Path(tmp) / "backend" / "case"
            case_dir.mkdir(parents=True)
            (case_dir / "prompt.md").write_text(
                "Fix a backend bug and require same-pattern scan plus regression evidence.",
                encoding="utf-8",
            )
            (case_dir / "expected.yaml").write_text(
                "\n".join(
                    [
                        "expected_stage: bug-fix",
                        "expected_professional_skill: backend-change-builder",
                        "expected_capabilities:",
                        "  - agent-execution-discipline",
                        "  - regression-testing",
                        "expected_hidden_risks:",
                        "  - local fix without same-pattern scan",
                        "  - unverified authorization regression",
                        "expected_evidence:",
                        "  - regression validation evidence",
                        "  - same-pattern scan output",
                        "forbidden_behaviors:",
                        "  - claim completion without command output",
                        "  - patch only one endpoint without sibling scan",
                        "expected_output_obligations:",
                        "  - validation evidence for backend regression and residual risk",
                        "  - inspected backend boundaries",
                        "  - next gate named",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (case_dir / "baseline_output.md").write_text(
                "I patched only one endpoint without sibling scan and claim completion without command output.",
                encoding="utf-8",
            )
            (case_dir / "with_skill_output.md").write_text(
                "\n".join(
                    [
                        "Selected stage: bug-fix.",
                        "Selected professional skill: backend-change-builder.",
                        "Selected capabilities: agent-execution-discipline, regression-testing.",
                        "Hidden risks: local fix without same-pattern scan.",
                        "Hidden risks: unverified authorization regression.",
                        "Evidence: regression validation evidence; same-pattern scan output.",
                        "Output obligations: validation evidence for backend regression and residual risk; inspected backend boundaries; next gate named.",
                        "Validation command: python3 -m pytest tests/test_backend.py.",
                        "Residual risk: concurrency path not verified.",
                        "Next gate: quality-test-gate.",
                    ]
                ),
                encoding="utf-8",
            )
            result = module._evaluate_case(case_dir, registry, {"bug-fix"}, "auto")
            self.assertEqual(result.errors, [])
            self.assertIsNotNone(result.comparison)
            self.assertEqual(result.comparison.mode, "comparison")
            self.assertGreater(result.comparison.with_skill_score, result.comparison.baseline_score)
            self.assertEqual(result.comparison_status, "pass")
            self.assertEqual(result.forbidden_behavior_hits, [])
            self.assertGreater(result.professional_delta_summary.delta_score, 0)
            self.assertIn("selected stage", result.professional_delta_summary.with_skill_present)
            self.assertTrue(result.professional_delta_summary.baseline_missing)
            self.assertTrue(result.baseline_defect_hits)
            self.assertEqual(result.benchmark_quality_status, "pass")

    def test_schema_only_mode_skips_case_without_output_pair(self) -> None:
        module = _load_module()
        registry = {"skills": {"backend-change-builder"}, "capabilities": {"regression-testing"}}
        with tempfile.TemporaryDirectory() as tmp:
            case_dir = Path(tmp) / "backend" / "case"
            case_dir.mkdir(parents=True)
            (case_dir / "prompt.md").write_text(
                "Fix a backend bug with enough concrete detail to require regression validation.",
                encoding="utf-8",
            )
            (case_dir / "expected.yaml").write_text(
                "\n".join(
                    [
                        "expected_stage: bug-fix",
                        "expected_professional_skill: backend-change-builder",
                        "expected_capabilities:",
                        "  - regression-testing",
                        "expected_hidden_risks:",
                        "  - tenant authorization regression gap",
                        "  - missing denied-path backend coverage",
                        "expected_evidence:",
                        "  - validation evidence",
                        "  - regression command output",
                        "forbidden_behaviors:",
                        "  - claim completion without evidence",
                        "  - patch only one endpoint without sibling scan",
                        "expected_output_obligations:",
                        "  - validation evidence for backend regression",
                        "  - residual tenant authorization risk",
                        "  - next quality-test gate",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            result = module._evaluate_case(case_dir, registry, {"bug-fix"}, "schema-only")
            self.assertEqual(result.errors, [])
            self.assertIsNotNone(result.comparison)
            self.assertEqual(result.comparison.mode, "schema-only")
            self.assertEqual(result.comparison_status, "schema-only")

    def test_auto_mode_requires_output_pair(self) -> None:
        module = _load_module()
        registry = {"skills": {"backend-change-builder"}, "capabilities": {"regression-testing"}}
        with tempfile.TemporaryDirectory() as tmp:
            case_dir = Path(tmp) / "backend" / "case"
            case_dir.mkdir(parents=True)
            (case_dir / "prompt.md").write_text(
                "Fix a backend bug with enough concrete detail to require regression validation.",
                encoding="utf-8",
            )
            (case_dir / "expected.yaml").write_text(
                "\n".join(
                    [
                        "expected_stage: bug-fix",
                        "expected_professional_skill: backend-change-builder",
                        "expected_capabilities:",
                        "  - regression-testing",
                        "expected_hidden_risks:",
                        "  - tenant authorization regression gap",
                        "  - missing denied-path backend coverage",
                        "expected_evidence:",
                        "  - validation evidence",
                        "  - regression command output",
                        "forbidden_behaviors:",
                        "  - claim completion without evidence",
                        "  - patch only one endpoint without sibling scan",
                        "expected_output_obligations:",
                        "  - validation evidence for backend regression",
                        "  - residual tenant authorization risk",
                        "  - next quality-test gate",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            result = module._evaluate_case(case_dir, registry, {"bug-fix"}, "auto")
            self.assertTrue(any("missing baseline_output.md" in error for error in result.errors))
            self.assertEqual(result.comparison_status, "fail")
            self.assertEqual(result.benchmark_quality_status, "fail")

    def test_vague_expected_items_are_rejected(self) -> None:
        module = _load_module()
        registry = {"skills": {"backend-change-builder"}, "capabilities": {"regression-testing"}}
        with tempfile.TemporaryDirectory() as tmp:
            case_dir = Path(tmp) / "backend" / "case"
            case_dir.mkdir(parents=True)
            (case_dir / "prompt.md").write_text(
                "Fix a backend bug with enough concrete detail to require regression validation.",
                encoding="utf-8",
            )
            (case_dir / "expected.yaml").write_text(
                "\n".join(
                    [
                        "expected_stage: bug-fix",
                        "expected_professional_skill: backend-change-builder",
                        "expected_capabilities:",
                        "  - regression-testing",
                        "expected_hidden_risks:",
                        "  - check security",
                        "  - add tests",
                        "expected_evidence:",
                        "  - run tests",
                        "  - do validation",
                        "forbidden_behaviors:",
                        "  - use best practices",
                        "  - handle errors",
                        "expected_output_obligations:",
                        "  - ensure quality",
                        "  - validation evidence",
                        "  - residual risk",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            result = module._evaluate_case(case_dir, registry, {"bug-fix"}, "auto")
        self.assertTrue(any("vague content" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
