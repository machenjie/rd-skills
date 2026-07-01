from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"


def _load_script(name: str, filename: str) -> ModuleType:
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not import {filename}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SCORECARD = _load_script("generate_professional_scorecard", "generate-professional-scorecard.py")
PUBLIC_SUMMARY = _load_script("generate_public_benchmark_summary", "generate-public-benchmark-summary.py")
CONTEXT_EVAL = _load_script("eval_context_control_plane", "eval-context-control-plane.py")
REPORT_CONSISTENCY = _load_script("validate_report_consistency", "validate-report-consistency.py")


def _context_report(status: str = "partial", overhead_status: str = "partial") -> dict[str, object]:
    structural_status = "pass" if status in {"pass", "partial"} else "fail"
    return {
        "schema_version": 1,
        "status": status,
        "fixture_status": structural_status,
        "overhead_status": overhead_status,
        "release_status": "partial" if status == "partial" else status,
        "summary": {"failed": 0 if structural_status == "pass" else 1},
        "context_control_overhead": {
            "status": overhead_status,
            "structural_fixture_status": structural_status,
            "overhead_status": overhead_status,
            "input_token_overhead_pct": 234.06,
            "output_token_overhead_pct": 45.63,
            "turn_overhead": None,
            "command_delta": 22.61,
            "pass_rate_delta": 0.0,
            "live_pass_rate": {"status": "collected", "pass_rate_delta": 0.0},
            "token_overhead": {"status": "collected", "input_pct": 234.06, "output_pct": 45.63},
            "turn_overhead_detail": {"status": "not_collected", "turn_overhead": None},
            "runtime_telemetry": {
                "status": "existing_report",
                "source": "reports/codex-live-benchmark-summary.json",
                "live_codex_executed": False,
                "command_delta": 22.61,
            },
            "quality_improvement_claim_allowed": False,
            "overhead_policy_verdict": (
                "partial: structural fixtures pass and live overhead is collected, but high token overhead remains "
                "an ungoverned P2 risk; do not claim Context Control Plane quality or cost improvement"
            ),
            "evidence_boundary": "Evidence separates structural fixture pass, live pass-rate, live runtime telemetry, token overhead, and turn overhead.",
        },
    }


class ContextControlOverheadReportingTests(unittest.TestCase):
    def test_public_summary_includes_context_control_row_when_report_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports = root / "reports"
            reports.mkdir()
            (reports / "context-control-plane-eval.json").write_text(
                json.dumps(_context_report()),
                encoding="utf-8",
            )
            status, detail = SCORECARD.context_control_overhead_status(root)
            self.assertEqual(status, "partial")
            scorecard_path = reports / "professional-scorecard.json"
            scorecard_path.write_text(
                json.dumps(
                    {
                        "status_summary": {"partial": 1},
                        "evidence_levels": {},
                        "dimensions": [
                            {
                                "name": "context_control_overhead",
                                "status": status,
                                "source": "reports/context-control-plane-eval.json",
                                "detail": detail,
                                "verification_command": "python3 scripts/eval-context-control-plane.py",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            payload = PUBLIC_SUMMARY.generate_summary(root, scorecard_path=scorecard_path)
            row = next(item for item in payload["items"] if item["name"] == "context_control_overhead")

        self.assertEqual(row["status"], "partial")
        self.assertIn("input_token_overhead_pct", row["detail"])
        detail = json.loads(row["detail"])
        self.assertEqual(detail["structural_fixture_status"], "pass")
        self.assertEqual(detail["fixture_status"], "pass")
        self.assertEqual(detail["overhead_status"], "partial")
        self.assertEqual(detail["release_status"], "partial")
        self.assertFalse(detail["quality_improvement_claim_allowed"])
        self.assertEqual(detail["live_pass_rate"]["status"], "collected")
        self.assertEqual(detail["token_overhead"]["status"], "collected")
        self.assertEqual(detail["turn_overhead_detail"]["status"], "not_collected")
        self.assertEqual(detail["runtime_telemetry"]["status"], "existing_report")

    def test_high_overhead_neutral_pass_rate_does_not_become_success_wording(self) -> None:
        summary = {
            "cost_summary": {
                "cost_adjusted_delta": {
                    "skills_with_hooks_clean_vs_baseline_clean": {
                        "average_input_token_overhead_pct": 2.3406,
                        "average_output_token_overhead_pct": 0.4563,
                        "average_command_execution_delta": 22.61,
                        "pass_rate_delta": 0.0,
                    }
                }
            },
            "quality_improvement_summary": {
                "large_quality_improvement_claim": False,
                "efficiency_improvement_claim": False,
            },
            "effect_status": "neutral",
            "effect_verdict": "neutral",
        }
        overhead = CONTEXT_EVAL._context_control_overhead(
            fixtures_pass=True,
            raw_leak_count=0,
            live_summary=summary,
        )
        self.assertEqual(overhead["status"], "partial")
        self.assertNotEqual(overhead["status"], "pass")
        self.assertEqual(overhead["structural_fixture_status"], "pass")
        self.assertEqual(overhead["overhead_status"], "partial")
        self.assertFalse(overhead["quality_improvement_claim_allowed"])
        self.assertEqual(overhead["live_pass_rate"], {"status": "collected", "pass_rate_delta": 0.0})
        self.assertEqual(overhead["token_overhead"]["status"], "collected")
        self.assertEqual(overhead["turn_overhead_detail"]["status"], "not_collected")
        self.assertEqual(overhead["runtime_telemetry"]["status"], "existing_report")

        markdown = PUBLIC_SUMMARY.render_markdown(
            {
                "repository": {"name": "test/repo", "version": "0", "source_commit": "test"},
                "status_counts": {"pass": 0, "partial": 1, "fail": 0, "unknown": 0, "not_collected": 0},
                "evidence_levels": {},
                "items": [
                    {
                        "name": "context_control_overhead",
                        "status": "partial",
                        "evidence_level": "structural fixture",
                        "source": "reports/context-control-plane-eval.json",
                        "detail": json.dumps(overhead, sort_keys=True),
                        "command": "python3 scripts/eval-context-control-plane.py",
                    }
                ],
                "known_unknowns": [],
                "refresh_commands": [],
            }
        )
        self.assertIn("High overhead without pass-rate improvement is not success.", markdown)
        self.assertIn("Live benchmark commands remain opt-in.", markdown)
        self.assertIn("- structural_fixture_status: `pass`", markdown)
        self.assertIn("- overhead_status: `partial`", markdown)
        self.assertIn("Structural fixture pass is not live quality improvement", markdown)
        self.assertIn('"live_codex_executed": false', markdown)

    def test_high_overhead_positive_pass_rate_without_p2_governance_stays_partial(self) -> None:
        summary = {
            "cost_summary": {
                "cost_is_telemetry_only": True,
                "telemetry_only_note": "No efficiency improvement claim is made.",
                "cost_adjusted_delta": {
                    "skills_with_hooks_clean_vs_baseline_clean": {
                        "average_input_token_overhead_pct": 2.2879,
                        "average_output_token_overhead_pct": 0.3556,
                        "average_command_execution_delta": 19.91,
                        "pass_rate_delta": 0.0417,
                    }
                },
            },
            "quality_improvement_summary": {
                "large_quality_improvement_claim": False,
                "efficiency_improvement_claim": False,
            },
            "effect_status": "improved",
            "effect_verdict": "positive",
        }

        overhead = CONTEXT_EVAL._context_control_overhead(
            fixtures_pass=True,
            raw_leak_count=0,
            live_summary=summary,
        )

        self.assertEqual(overhead["status"], "partial")
        self.assertEqual(overhead["overhead_status"], "partial")
        self.assertEqual(overhead["input_token_overhead_pct"], 228.79)
        self.assertEqual(overhead["output_token_overhead_pct"], 35.56)
        self.assertEqual(overhead["command_delta"], 19.91)
        self.assertEqual(overhead["pass_rate_delta"], 0.0417)
        self.assertFalse(overhead["quality_improvement_claim_allowed"])
        self.assertEqual(overhead["runtime_telemetry"]["status"], "existing_report")
        self.assertFalse(overhead["runtime_telemetry"]["live_codex_executed"])
        self.assertIn("ungoverned P2 risk", overhead["overhead_policy_verdict"])
        self.assertIn("do not claim Context Control Plane quality or cost improvement", overhead["overhead_policy_verdict"])

    def test_context_control_eval_partial_overhead_keeps_top_level_partial(self) -> None:
        self.assertEqual(
            CONTEXT_EVAL._overall_status(fixtures_pass=True, overhead_status="partial"),
            "partial",
        )
        self.assertEqual(
            CONTEXT_EVAL._overall_status(fixtures_pass=True, overhead_status="not_collected"),
            "partial",
        )
        self.assertEqual(
            CONTEXT_EVAL._overall_status(fixtures_pass=True, overhead_status="pass"),
            "pass",
        )
        self.assertEqual(
            CONTEXT_EVAL._overall_status(fixtures_pass=False, overhead_status="pass"),
            "fail",
        )

    def test_professional_scorecard_markdown_renders_context_control_evidence_split(self) -> None:
        markdown = SCORECARD.render_markdown(
            {
                "status_summary": {"pass": 0, "partial": 1, "fail": 0, "unknown": 0, "not_collected": 0},
                "evidence_levels": {},
                "dimensions": [
                    {
                        "name": "context_control_overhead",
                        "status": "partial",
                        "source": "reports/context-control-plane-eval.json",
                        "verification_command": "python3 scripts/eval-context-control-plane.py",
                        "fix_hint": "repair overhead",
                        "detail": json.dumps(_context_report()["context_control_overhead"], sort_keys=True),
                    }
                ],
                "profile_counts": {},
            }
        )

        self.assertIn("## Context Control Overhead", markdown)
        self.assertIn("- structural_fixture_status: `pass`", markdown)
        self.assertIn("- overhead_status: `partial`", markdown)
        self.assertIn("- live_pass_rate: `", markdown)
        self.assertIn("- token_overhead: `", markdown)
        self.assertIn("- turn_overhead_detail: `", markdown)
        self.assertIn("- runtime_telemetry: `", markdown)

    def test_missing_overhead_is_not_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            status, _detail = SCORECARD.context_control_overhead_status(Path(tmp))
        self.assertEqual(status, "not_collected")

        overhead = CONTEXT_EVAL._context_control_overhead(
            fixtures_pass=True,
            raw_leak_count=0,
            live_summary=None,
        )
        self.assertEqual(overhead["status"], "partial")
        self.assertEqual(overhead["structural_fixture_status"], "pass")
        self.assertEqual(overhead["token_overhead"]["status"], "not_collected")
        self.assertEqual(overhead["turn_overhead_detail"]["status"], "not_collected")

    def test_forbidden_raw_key_variants_are_detected_without_token_metric_false_positive(self) -> None:
        record = {
            "context_budget_tokens": 1200,
            "input_token_overhead_pct": 234.06,
            "safe": {"raw_output_excerpt": "must not be retained"},
            "nested": [{"stdout_text": "must not be retained"}],
        }
        errors = CONTEXT_EVAL._forbidden_key_errors(record, "fixture")

        self.assertTrue(any("raw_output_excerpt" in error for error in errors), errors)
        self.assertTrue(any("stdout_text" in error for error in errors), errors)
        self.assertFalse(any("context_budget_tokens" in error for error in errors), errors)
        self.assertFalse(any("input_token_overhead_pct" in error for error in errors), errors)

    def test_context_control_eval_failure_blocks_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports = root / "reports"
            reports.mkdir()
            report_path = reports / "context-control-plane-eval.json"
            report_path.write_text(json.dumps(_context_report(status="fail", overhead_status="pass")), encoding="utf-8")

            status, _detail = SCORECARD.context_control_overhead_status(root)
            errors = REPORT_CONSISTENCY.context_control_report_consistency_errors(
                context_report_path=report_path,
            )

        self.assertEqual(status, "fail")
        self.assertTrue(any("blocks pass" in error for error in errors), errors)

    def test_context_control_eval_pass_with_partial_overhead_blocks_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports = root / "reports"
            reports.mkdir()
            report_path = reports / "context-control-plane-eval.json"
            report_path.write_text(json.dumps(_context_report(status="pass", overhead_status="partial")), encoding="utf-8")

            status, _detail = SCORECARD.context_control_overhead_status(root)
            errors = REPORT_CONSISTENCY.context_control_report_consistency_errors(
                context_report_path=report_path,
            )

        self.assertEqual(status, "fail")
        self.assertTrue(any("blocks pass" in error for error in errors), errors)

    def test_context_control_eval_pass_with_high_positive_overhead_blocks_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports = root / "reports"
            reports.mkdir()
            report_path = reports / "context-control-plane-eval.json"
            report = _context_report(status="pass", overhead_status="pass")
            report["release_status"] = "pass"
            report["context_control_overhead"]["status"] = "pass"
            report["context_control_overhead"]["overhead_status"] = "pass"
            report["context_control_overhead"]["pass_rate_delta"] = 0.0417
            report["context_control_overhead"]["live_pass_rate"] = {"status": "collected", "pass_rate_delta": 0.0417}
            report["context_control_overhead"]["quality_improvement_claim_allowed"] = True
            report["context_control_overhead"]["overhead_policy_verdict"] = "pass: within policy threshold"
            report_path.write_text(json.dumps(report), encoding="utf-8")

            status, detail_json = SCORECARD.context_control_overhead_status(root)
            errors = REPORT_CONSISTENCY.context_control_report_consistency_errors(
                context_report_path=report_path,
            )

        detail = json.loads(detail_json)
        self.assertEqual(status, "fail")
        self.assertEqual(detail["invalid_status"], "pass_with_high_token_overhead_without_p2_governance")
        self.assertTrue(any("failure blocks pass" in error for error in errors), errors)

    def test_context_control_eval_partial_with_partial_overhead_is_partial(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports = root / "reports"
            reports.mkdir()
            report_path = reports / "context-control-plane-eval.json"
            report = _context_report(status="partial", overhead_status="partial")
            report["summary"] = {"failed": 0}
            report["context_control_overhead"]["structural_fixture_status"] = "pass"
            report_path.write_text(json.dumps(report), encoding="utf-8")

            status, _detail = SCORECARD.context_control_overhead_status(root)
            errors = REPORT_CONSISTENCY.context_control_report_consistency_errors(
                context_report_path=report_path,
            )

        self.assertEqual(status, "partial")
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
