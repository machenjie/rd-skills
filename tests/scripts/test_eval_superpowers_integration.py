from __future__ import annotations

import importlib.util
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "eval-superpowers-integration.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("eval_superpowers_integration", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class EvalSuperpowersIntegrationTests(unittest.TestCase):
    def test_repository_fixtures_pass(self) -> None:
        module = _load_module()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(module.main([]), 0)

    def test_missing_required_contract_text_fails(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            fixture_dir = Path(tmp) / "evals"
            fixture_dir.mkdir()
            target = Path(tmp) / "target.md"
            target.write_text("visible contract\n", encoding="utf-8")
            (fixture_dir / "case.yaml").write_text(
                "id: missing-term\n"
                "required_contracts:\n"
                f"  - path: {target}\n"
                "    must_contain:\n"
                "      - absent requirement\n",
                encoding="utf-8",
            )
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(module.main(["--fixture-dir", str(fixture_dir)]), 1)

    def test_visible_plan_case_failure_is_reported(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            fixture_dir = Path(tmp) / "evals"
            fixture_dir.mkdir()
            target = Path(tmp) / "target.md"
            target.write_text("visible contract\n", encoding="utf-8")
            (fixture_dir / "case.yaml").write_text(
                "id: plan-status-mismatch\n"
                "required_contracts:\n"
                f"  - path: {target}\n"
                "    must_contain:\n"
                "      - visible contract\n"
                "visible_plan_cases:\n"
                "  - name: generic-plan\n"
                "    input: |\n"
                "      # Implementation Plan\n"
                "      ## Task 1: Add proper error handling\n"
                "    expected_status: pass\n",
                encoding="utf-8",
            )
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(module.main(["--fixture-dir", str(fixture_dir)]), 1)

    def test_routing_case_failure_is_reported(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            fixture_dir = Path(tmp) / "evals"
            fixture_dir.mkdir()
            target = Path(tmp) / "target.md"
            target.write_text("visible contract\n", encoding="utf-8")
            candidate = Path(tmp) / "superpowers-complex-engineering-flow.actual.yaml"
            candidate.write_text(
                "case_id: superpowers-complex-engineering-flow\n"
                "actual:\n"
                "  complexity: L3\n"
                "  risk_level: medium\n"
                "  skills:\n"
                "    - frontend-change-builder\n"
                "  capabilities: []\n"
                "  domain_extensions: []\n"
                "  quality_gates: []\n",
                encoding="utf-8",
            )
            (fixture_dir / "case.yaml").write_text(
                "id: routing-mismatch\n"
                "required_contracts:\n"
                f"  - path: {target}\n"
                "    must_contain:\n"
                "      - visible contract\n"
                "routing_cases:\n"
                "  - case_id: superpowers-complex-engineering-flow\n"
                f"    candidate_output: {candidate}\n",
                encoding="utf-8",
            )
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(module.main(["--fixture-dir", str(fixture_dir)]), 1)


if __name__ == "__main__":
    unittest.main()
