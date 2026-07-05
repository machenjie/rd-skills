from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "eval-executor-adapters.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    for module_name in list(sys.modules):
        if module_name == "runtime_governance" or module_name.startswith("runtime_governance."):
            del sys.modules[module_name]
    spec = importlib.util.spec_from_file_location("eval_executor_adapters", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class EvalExecutorAdaptersTests(unittest.TestCase):
    def test_suite_passes_with_required_pressure_coverage(self) -> None:
        module = _load_module()
        payload = module.evaluate_suite(ROOT / "evals" / "executor-adapter")
        summary = payload["summary"]

        self.assertEqual(payload["status"], "pass")
        self.assertGreaterEqual(summary["case_count"], 15)
        self.assertEqual(summary["failed"], 0)
        self.assertEqual(summary["live_pass_rate"]["status"], "not_collected")
        self.assertEqual(summary["token_overhead"]["status"], "not_collected")
        self.assertEqual(summary["turn_overhead"]["status"], "not_collected")
        self.assertTrue(module.REQUIRED_COVERAGE_TARGETS.issubset(set(summary["coverage_targets"])))
        self.assertTrue(module.REQUIRED_PRESSURE_CASES.issubset(set(summary["pressure_cases"])))

    def test_report_payload_does_not_include_raw_fixture_input(self) -> None:
        module = _load_module()
        payload = module.evaluate_suite(ROOT / "evals" / "executor-adapter")
        serialized = json.dumps(payload, sort_keys=True)

        self.assertNotIn("input_payload", serialized)
        self.assertNotIn("SYNTHETIC_TOKEN_SHOULD_BE_IGNORED", serialized)
        self.assertNotIn("deploy.py --token", serialized)
        self.assertNotIn("/Users/", serialized)

    def test_telemetry_sample_is_bounded_and_sanitized(self) -> None:
        module = _load_module()
        payload = module.evaluate_suite(ROOT / "evals" / "executor-adapter")
        sample = module.telemetry_sample_from_eval(payload)
        serialized = json.dumps(sample, sort_keys=True)

        self.assertEqual(sample["source"], "deterministic-fixture-bounded-facts")
        self.assertEqual(sample["sample_kind"], "runtime_telemetry_fixture_sample")
        self.assertEqual(sample["evidence_level"], "runtime telemetry fixture sample")
        self.assertEqual(sample["event_count"], payload["summary"]["case_count"])
        self.assertEqual(sample["token_overhead"]["status"], "not_collected")
        self.assertEqual(sample["turn_overhead"]["status"], "not_collected")
        self.assertNotIn("input_payload", serialized)
        self.assertNotIn("SYNTHETIC_TOKEN_SHOULD_BE_IGNORED", serialized)
        self.assertNotIn("deploy.py --token", serialized)
        self.assertNotIn("/Users/", serialized)

    def test_cli_writes_reports_without_raw_input_payload(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            md_out = tmp_path / "executor-adapter-eval.md"
            json_out = tmp_path / "executor-adapter-eval.json"
            telemetry_out = tmp_path / "runtime-telemetry-sample.json"

            result = module.main(
                [
                    "--fixtures-dir",
                    str(ROOT / "evals" / "executor-adapter"),
                    "--out",
                    str(md_out),
                    "--json-out",
                    str(json_out),
                    "--telemetry-out",
                    str(telemetry_out),
                ]
            )

            self.assertEqual(result, 0)
            report_text = json_out.read_text(encoding="utf-8")
            telemetry_text = telemetry_out.read_text(encoding="utf-8")
            self.assertIn("# Executor Adapter Evaluation", md_out.read_text(encoding="utf-8"))
            self.assertNotIn("input_payload", report_text)
            self.assertNotIn("SYNTHETIC_TOKEN_SHOULD_BE_IGNORED", report_text)
            self.assertNotIn("SYNTHETIC_TOKEN_SHOULD_BE_IGNORED", telemetry_text)


if __name__ == "__main__":
    unittest.main()
