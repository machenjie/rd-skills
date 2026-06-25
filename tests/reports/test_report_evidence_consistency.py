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

    def test_current_canonical_summary_satisfies_consistency_rules(self) -> None:
        summary = REPORT_VALIDATOR.read_json(SUMMARY_PATH)
        errors = REPORT_VALIDATOR._report_evidence_consistency_errors(SUMMARY_PATH, summary)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
