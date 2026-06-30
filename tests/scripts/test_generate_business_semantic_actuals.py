from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

SCRIPT_PATH = ROOT / "scripts" / "generate-business-semantic-actuals.py"
REVIEW_PATH = ROOT / "scripts" / "eval-business-semantic-review.py"
_GENERATOR_SPEC = importlib.util.spec_from_file_location("generate_business_semantic_actuals_under_test", SCRIPT_PATH)
if _GENERATOR_SPEC is None or _GENERATOR_SPEC.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT_PATH}")
GENERATOR = importlib.util.module_from_spec(_GENERATOR_SPEC)
sys.modules[_GENERATOR_SPEC.name] = GENERATOR
_GENERATOR_SPEC.loader.exec_module(GENERATOR)
_REVIEW_SPEC = importlib.util.spec_from_file_location("eval_business_semantic_review_for_generator_test", REVIEW_PATH)
if _REVIEW_SPEC is None or _REVIEW_SPEC.loader is None:
    raise RuntimeError(f"cannot load {REVIEW_PATH}")
REVIEW = importlib.util.module_from_spec(_REVIEW_SPEC)
sys.modules[_REVIEW_SPEC.name] = REVIEW
_REVIEW_SPEC.loader.exec_module(REVIEW)


class GenerateBusinessSemanticActualsTests(unittest.TestCase):
    def test_check_checked_in_actual_outputs_pass(self) -> None:
        rc, output = _run_generator(["--check"])

        self.assertEqual(rc, 0, output)

    def test_check_detects_stale_temp_actual_output(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp_s:
            tmp = Path(tmp_s)
            eval_dir = tmp / "evals" / "business-semantic"
            output_dir = tmp / "evals" / "business-semantic-outputs"
            shutil.copytree(ROOT / "evals" / "business-semantic", eval_dir)
            shutil.copytree(ROOT / "evals" / "business-semantic-outputs", output_dir)

            actual_path = sorted(output_dir.glob("*.actual.yaml"))[0]
            actual_path.write_text(
                actual_path.read_text(encoding="utf-8").replace(
                    'generation_mode: "deterministic"',
                    'generation_mode: "stale"',
                    1,
                ),
                encoding="utf-8",
            )

            rc, output = _run_generator(
                ["--check", "--eval-dir", str(eval_dir), "--output-dir", str(output_dir)]
            )

        self.assertNotEqual(rc, 0)
        self.assertIn("stale", output)

    def test_fake_expected_oracle_fields_do_not_enter_actual(self) -> None:
        case = _oracle_pollution_case()

        actual = GENERATOR.build_actual(Path("oracle-skill-pollution.yaml"), case)
        actual_text = json.dumps(actual, sort_keys=True)

        for forbidden in (
            "fake-oracle-skill",
            "fake-oracle-capability",
            "fake oracle gate",
            "fake_section",
            "fake evidence not in source",
            "fake fix",
        ):
            self.assertNotIn(forbidden, actual_text)

    def test_fake_expected_evidence_does_not_enter_actual_review(self) -> None:
        case = _oracle_pollution_case()
        case["expected_review_findings"][0]["expected_evidence"] = ["not in source"]

        actual = GENERATOR.build_actual(Path("oracle-evidence-pollution.yaml"), case)
        actual_text = json.dumps(actual["actual_review"], sort_keys=True)

        self.assertNotIn("not in source", actual_text)

    def test_review_eval_fails_when_expected_evidence_is_not_in_generated_actual(self) -> None:
        case_yaml = _missing_evidence_case_yaml()
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp_s:
            tmp = Path(tmp_s)
            eval_dir = tmp / "evals" / "business-semantic"
            output_dir = tmp / "evals" / "business-semantic-outputs"
            eval_dir.mkdir(parents=True)
            output_dir.mkdir(parents=True)
            (eval_dir / "missing-oracle-evidence.yaml").write_text(case_yaml, encoding="utf-8")
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
                generator_rc = GENERATOR.main(["--eval-dir", str(eval_dir), "--output-dir", str(output_dir)])
            self.assertEqual(generator_rc, 0, buffer.getvalue())

            old_eval_dir = REVIEW.EVAL_DIR
            old_output_dir = REVIEW.OUTPUT_DIR
            REVIEW.EVAL_DIR = eval_dir
            REVIEW.OUTPUT_DIR = output_dir
            try:
                buffer = io.StringIO()
                with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
                    review_rc = REVIEW.main()
            finally:
                REVIEW.EVAL_DIR = old_eval_dir
                REVIEW.OUTPUT_DIR = old_output_dir

        self.assertNotEqual(review_rc, 0)
        self.assertIn("missing expected evidence", buffer.getvalue())


def _run_generator(argv: list[str]) -> tuple[int, str]:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *argv],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.returncode, completed.stdout + completed.stderr


def _oracle_pollution_case() -> dict[str, object]:
    return {
        "case_id": "oracle-skill-pollution",
        "prompt": "Change renewal SQL rule.",
        "routing_triggers": ["business rule hidden in SQL/controller/UI/test"],
        "source_context": {
            "files": [
                {
                    "path": "billing/sql/renewal.sql",
                    "language": "sql",
                    "content": "SELECT * FROM subscriptions WHERE status != 'expired';\n",
                }
            ]
        },
        "input_route_hint": {
            "stage": "implementation-planning",
            "business_semantic_pack_required": True,
            "business_semantic_scope": "hidden-sql-rule",
        },
        "expected_route": {
            "stage": "implementation-planning",
            "business_semantic_pack_required": True,
            "business_semantic_scope": "hidden-sql-rule",
        },
        "expected_skills": ["fake-oracle-skill"],
        "expected_capabilities": ["fake-oracle-capability"],
        "expected_quality_gates": ["fake oracle gate"],
        "expected_bsp_sections": ["fake_section"],
        "expected_review_findings": [
            {
                "finding_id": "FAKE",
                "category": "fake_category",
                "impacted_claim": "fake",
                "expected_evidence": ["fake evidence not in source"],
                "required_fix": "fake fix",
            }
        ],
        "forbidden_behavior": [],
    }


def _missing_evidence_case_yaml() -> str:
    return """case_id: missing-oracle-evidence
prompt: Change renewal SQL rule.
routing_triggers:
  - business rule hidden in SQL/controller/UI/test
source_context:
  files:
    - path: billing/sql/renewal.sql
      language: sql
      content: |
        SELECT * FROM subscriptions WHERE status != 'expired';
input_route_hint:
  stage: implementation-planning
  business_semantic_pack_required: true
  business_semantic_scope: hidden-sql-rule
expected_route:
  stage: implementation-planning
  business_semantic_pack_required: true
  business_semantic_scope: hidden-sql-rule
expected_skills: [domain-impact-modeler]
expected_capabilities: [business-semantic-control-plane, business-rule-extraction]
expected_quality_gates: [domain gate]
expected_bsp_sections: [business_rules, data_and_signal_semantics]
expected_review_findings:
  - finding_id: BSP-HIDDEN-SQL-RULE
    category: hidden_sql_rule
    impacted_claim: subscription renewal eligibility status filter
    expected_evidence:
      - not in source
    required_fix: SQL condition is a hidden business rule and needs rule_id, owner, authoritative enforcement layer, golden case, changed-path validation.
forbidden_behavior: [approve SQL condition without rule catalog]
scoring: [evidence_detection]
"""


if __name__ == "__main__":
    unittest.main()
