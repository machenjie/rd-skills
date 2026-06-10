from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "eval-professional-agent-samples.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("eval_professional_agent_samples", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _valid_sample(status: str = "candidate") -> str:
    return (
        "id: backend-idor-professional-sample\n"
        "description: Backend IDOR fix sample.\n"
        "prompt: Fix an invoice IDOR without claiming unverified completion.\n"
        "expected:\n"
        "  selected_skills:\n"
        "    - backend-change-builder\n"
        "    - security-privacy-gate\n"
        "  selected_capabilities:\n"
        "    - permission-boundary-modeling\n"
        "    - regression-testing\n"
        "  required_references:\n"
        "    - references/routing-rules.md\n"
        "  required_quality_gates:\n"
        "    - security gate\n"
        "    - test gate\n"
        "  required_professional_obligations:\n"
        "    - same-pattern scan\n"
        "    - denied-case regression\n"
        "  forbidden_behaviors:\n"
        "    - claim completion without evidence\n"
        "actual:\n"
        "  route_manifest:\n"
        "    selected_skills:\n"
        "      - backend-change-builder\n"
        "      - security-privacy-gate\n"
        "    selected_capabilities:\n"
        "      - permission-boundary-modeling\n"
        "      - regression-testing\n"
        "    required_references:\n"
        "      - references/routing-rules.md\n"
        "    required_quality_gates:\n"
        "      - security gate\n"
        "      - test gate\n"
        "  validation_evidence: denied-case regression command and same-pattern scan output\n"
        "  residual_risk: historic access logs were not audited\n"
        "  inspected_boundaries: controller, service, repository, permission policy\n"
        "  next_gate: security gate for audit review\n"
        "review:\n"
        "  human_review_required: true\n"
        f"  promotion_status: {status}\n"
        "  notes: Candidate fixture.\n"
    )


class EvalProfessionalAgentSamplesTests(unittest.TestCase):
    def test_valid_sample_passes_rule_checks(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.yaml"
            path.write_text(_valid_sample(), encoding="utf-8")
            data = module.load_yaml_file(path)
            result = module._evaluate_sample(path, data)
            self.assertTrue(result.ok, module._result_findings(result))
            self.assertEqual(result.promotion_status, "candidate")

    def test_raw_output_sample_passes_rule_checks(self) -> None:
        module = _load_module()
        sample = (
            "id: raw-output-sample\n"
            "description: Raw output sample.\n"
            "prompt: Fix a backend IDOR with evidence.\n"
            "expected:\n"
            "  selected_skills:\n"
            "    - backend-change-builder\n"
            "  selected_capabilities:\n"
            "    - regression-testing\n"
            "  required_references:\n"
            "    - references/routing-rules.md\n"
            "  required_quality_gates:\n"
            "    - test gate\n"
            "  required_professional_obligations:\n"
            "    - denied-case regression\n"
            "  forbidden_behaviors:\n"
            "    - completion claim without evidence\n"
            "actual:\n"
            "  raw_output: |\n"
            "    ```yaml\n"
            "    changeforge_route:\n"
            "      selected_skills:\n"
            "        - backend-change-builder\n"
            "      selected_capabilities:\n"
            "        - regression-testing\n"
            "      required_references:\n"
            "        - references/routing-rules.md\n"
            "      required_quality_gates:\n"
            "        - test gate\n"
            "    ```\n"
            "    Boundaries inspected: controller and repository.\n"
            "    Validation evidence: denied-case regression command output.\n"
            "    Residual risk: historic access logs not audited.\n"
            "    Next gate: test gate.\n"
            "review:\n"
            "  human_review_required: true\n"
            "  promotion_status: candidate\n"
            "  notes: Raw sample.\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.yaml"
            path.write_text(sample, encoding="utf-8")
            data = module.load_yaml_file(path)
            result = module._evaluate_sample(path, data)
            self.assertTrue(result.ok, module._result_findings(result))

    def test_forbidden_behavior_is_warning_and_strict_failure(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            samples_dir = tmp_path / "samples" / "backend"
            reports_dir = tmp_path / "reports"
            samples_dir.mkdir(parents=True)
            (samples_dir / "case.yaml").write_text(
                _valid_sample().replace(
                    "historic access logs were not audited",
                    "claim completion without evidence",
                ),
                encoding="utf-8",
            )
            default_code = module.main(
                ["--samples-dir", str(tmp_path / "samples"), "--reports-dir", str(reports_dir)]
            )
            strict_code = module.main(
                [
                    "--samples-dir",
                    str(tmp_path / "samples"),
                    "--reports-dir",
                    str(reports_dir),
                    "--strict",
                ]
            )
            self.assertEqual(default_code, 0)
            self.assertEqual(strict_code, 1)
            report = json.loads((reports_dir / "professional-agent-samples-report.json").read_text())
            self.assertEqual(report["warnings"], 1)
            self.assertTrue(report["results"][0]["forbidden_behavior_hits"])

    def test_forbidden_behavior_requires_exact_normalized_phrase(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.yaml"
            path.write_text(
                _valid_sample().replace(
                    "claim completion without evidence",
                    "skip replay path",
                ).replace(
                    "historic access logs were not audited",
                    "replay path inspected",
                ),
                encoding="utf-8",
            )
            data = module.load_yaml_file(path)
            result = module._evaluate_sample(path, data)
            self.assertEqual(result.forbidden_behavior_hits, [])

    def test_candidate_filter_excludes_promoted_samples(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            samples_dir = tmp_path / "samples" / "backend"
            reports_dir = tmp_path / "reports"
            samples_dir.mkdir(parents=True)
            (samples_dir / "candidate.yaml").write_text(_valid_sample("candidate"), encoding="utf-8")
            (samples_dir / "promoted.yaml").write_text(_valid_sample("promoted"), encoding="utf-8")
            code = module.main(
                [
                    "--samples-dir",
                    str(tmp_path / "samples"),
                    "--reports-dir",
                    str(reports_dir),
                    "--candidates-only",
                ]
            )
            self.assertEqual(code, 0)
            report = json.loads((reports_dir / "professional-agent-samples-report.json").read_text())
            self.assertEqual(report["samples_checked"], 1)
            self.assertEqual(report["results"][0]["promotion_status"], "candidate")


if __name__ == "__main__":
    unittest.main()
