from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate-codex-live-benchmark-reports.py"
SCRIPTS_DIR = ROOT / "scripts"


def _load_report_validator() -> ModuleType:
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    spec = importlib.util.spec_from_file_location("validate_codex_live_reports", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not import validate-codex-live-benchmark-reports.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REPORT_VALIDATOR = _load_report_validator()
SUMMARY_PATH = ROOT / "reports" / "codex-live-benchmark-summary.json"


def _base_summary() -> dict[str, object]:
    return {
        "evidence_level": "local_codex_cli_live_benchmark",
        "effect_verdict": "neutral",
        "effect_status": "neutral",
        "run_id": "unit-test-run",
        "generated_by": "scripts/generate-codex-live-summary.py",
        "actual_run_cases": ["case-a"],
        "coverage_summary": {
            "manifest_case_count": 10,
            "registered_live_case_count": 4,
            "actual_run_case_count": 2,
            "registered_case_coverage_rate": 0.4,
            "actual_run_case_coverage_rate": 0.2,
            "registered_but_not_run_cases": ["case-b"],
        },
        "capability_coverage_summary": {
            "status": "partial",
            "items": [],
        },
        "quality_improvement_summary": {
            "large_quality_improvement_claim": False,
            "efficiency_improvement_claim": False,
        },
    }


def _coverage_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "case_count": 2,
        "assertion_case_count": 2,
        "telemetry_only_case_count": 0,
        "publishable_assertion_case_count": 2,
        "unregistered_case_count": 0,
        "manifest_category_count": 3,
        "manifest_case_count": 10,
        "registered_live_case_count": 4,
        "registered_assertion_case_count": 4,
        "registered_telemetry_only_case_count": 0,
        "registered_publishable_assertion_case_count": 4,
        "registered_category_count": 3,
        "actual_run_case_count": 2,
        "actual_run_assertion_case_count": 2,
        "actual_run_publishable_assertion_case_count": 2,
        "actual_run_category_count": 2,
        "registered_case_coverage_rate": 0.4,
        "registered_publishable_case_coverage_rate": 0.4,
        "actual_run_case_coverage_rate": 0.2,
        "tiers": {"core": 2, "level1": 0, "experimental": 0},
        "tiers_registered": {"core": 2, "level1": 2, "experimental": 0},
        "tiers_run": {"core": 2, "level1": 0, "experimental": 0},
        "categories": {"security": 1, "backend": 1},
        "coverage_dimensions": {"security": 1, "backend": 1},
        "categories_registered": {"security": 1, "backend": 1, "frontend": 1, "integration": 1},
        "publishable_categories_registered": {"security": 1, "backend": 1, "frontend": 1, "integration": 1},
        "coverage_dimensions_registered": {"security": 1, "backend": 1, "frontend": 1, "integration": 1},
        "categories_run": {"security": 1, "backend": 1},
        "coverage_dimensions_run": {"security": 1, "backend": 1},
        "manifest_categories": ["security", "backend", "frontend"],
        "registered_but_not_run_cases": ["frontend/case", "integration/case"],
        "missing_manifest_categories": [],
    }
    payload.update(overrides)
    return payload


class ReportEvidenceConsistencyTests(unittest.TestCase):
    def test_registered_coverage_must_not_mirror_actual_rate_when_counts_differ(self) -> None:
        summary = _base_summary()
        summary["coverage_summary"]["registered_case_coverage_rate"] = 0.2
        errors = REPORT_VALIDATOR._report_evidence_consistency_errors(SUMMARY_PATH, summary)
        self.assertTrue(any("must not mirror" in error for error in errors), errors)

    def test_dry_run_cannot_claim_live_evidence(self) -> None:
        summary = _base_summary()
        summary["dry_run"] = True
        errors = REPORT_VALIDATOR._report_evidence_consistency_errors(SUMMARY_PATH, summary)
        self.assertTrue(any("dry-run" in error for error in errors), errors)

    def test_capability_pass_cannot_mask_failed_item(self) -> None:
        summary = _base_summary()
        summary["capability_coverage_summary"] = {
            "status": "pass",
            "items": [{"id": "core-case", "status": "fail"}],
        }
        errors = REPORT_VALIDATOR._report_evidence_consistency_errors(SUMMARY_PATH, summary)
        self.assertTrue(any("cannot be pass" in error for error in errors), errors)

    def test_improvement_claim_requires_actual_run_evidence(self) -> None:
        summary = _base_summary()
        summary["quality_improvement_summary"] = {
            "large_quality_improvement_claim": True,
            "efficiency_improvement_claim": False,
        }
        summary["actual_run_cases"] = []
        errors = REPORT_VALIDATOR._report_evidence_consistency_errors(SUMMARY_PATH, summary)
        self.assertTrue(any("actual_run_cases" in error for error in errors), errors)

    def test_coverage_summary_requires_registered_but_not_run_count_consistency(self) -> None:
        coverage = _coverage_payload(registered_but_not_run_cases=["frontend/case"])
        errors = REPORT_VALIDATOR._coverage_summary_errors(coverage)
        self.assertTrue(any("registered_but_not_run_cases count" in error for error in errors), errors)

    def test_coverage_summary_requires_missing_publishable_list_when_not_all_ran(self) -> None:
        coverage = _coverage_payload(registered_but_not_run_cases=[])
        errors = REPORT_VALIDATOR._coverage_summary_errors(coverage)
        self.assertTrue(any("must list missing publishable assertion cases" in error for error in errors), errors)

    def test_coverage_summary_rejects_publishable_actual_count_above_registered(self) -> None:
        coverage = _coverage_payload(
            actual_run_case_count=5,
            actual_run_publishable_assertion_case_count=5,
            registered_but_not_run_cases=[],
        )
        errors = REPORT_VALIDATOR._coverage_summary_errors(coverage)
        self.assertTrue(any("cannot exceed registered_publishable" in error for error in errors), errors)

    def test_current_canonical_summary_satisfies_consistency_rules(self) -> None:
        summary = REPORT_VALIDATOR.read_json(SUMMARY_PATH)
        errors = REPORT_VALIDATOR._report_evidence_consistency_errors(SUMMARY_PATH, summary)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
