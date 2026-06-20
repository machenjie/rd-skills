from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "eval-activation-precision.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    hook_runtime = str(ROOT / "src" / "hook-runtime" / "scripts")
    if hook_runtime not in sys.path:
        sys.path.insert(0, hook_runtime)
    spec = importlib.util.spec_from_file_location("eval_activation_precision", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class EvalActivationPrecisionTests(unittest.TestCase):
    def test_default_fixture_passes_with_required_metrics(self) -> None:
        module = _load_module()
        payload = module.evaluate_activation_precision(ROOT / "evals" / "activation")
        summary = payload["summary"]

        self.assertEqual(payload["status"], "pass")
        for metric in module.REQUIRED_METRICS:
            self.assertIn(metric, summary)
        self.assertEqual(summary["stage_accuracy"], 1.0)
        self.assertEqual(summary["skill_precision"], 1.0)
        self.assertEqual(summary["skill_recall"], 1.0)
        self.assertEqual(summary["capability_precision"], 1.0)
        self.assertEqual(summary["capability_recall"], 1.0)
        self.assertEqual(summary["reference_precision"], 1.0)
        self.assertEqual(summary["reference_recall"], 1.0)
        self.assertEqual(summary["language_fp_rate"], 0.0)
        self.assertEqual(summary["language_fn_rate"], 0.0)
        self.assertEqual(summary["risk_surface_fp_rate"], 0.0)
        self.assertEqual(summary["risk_surface_fn_rate"], 0.0)
        self.assertEqual(summary["overroute_rate"], 0.0)

    def test_overroute_mismatch_fails(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            fixture_dir = Path(tmp)
            (fixture_dir / "cases.yaml").write_text(
                "---\n"
                "cases:\n"
                "  - id: overroute-sentinel\n"
                "    event:\n"
                "      hook_event_name: UserPromptSubmit\n"
                "      prompt: Update src/components/ProfileCard.tsx disabled save button state.\n"
                "    expected:\n"
                "      stage: implementation-planning\n"
                "      product_surfaces: []\n"
                "      language_surfaces: []\n"
                "      risk_surfaces: []\n"
                "      selected_skills: []\n"
                "      selected_capabilities: []\n"
                "      required_references: []\n",
                encoding="utf-8",
            )
            payload = module.evaluate_activation_precision(fixture_dir)

        self.assertEqual(payload["status"], "fail")
        self.assertGreater(payload["summary"]["overroute_rate"], 0.0)
        self.assertTrue(any("extra" in error for error in payload["errors"]))

    def test_cli_writes_markdown_and_json(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            md_path = Path(tmp) / "activation.md"
            json_path = Path(tmp) / "activation.json"
            result = module.main(
                [
                    "--fixtures-dir",
                    str(ROOT / "evals" / "activation"),
                    "--out",
                    str(md_path),
                    "--json-out",
                    str(json_path),
                ]
            )

            self.assertEqual(result, 0)
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "pass")
            self.assertIn("# Activation Precision Evaluation", md_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
