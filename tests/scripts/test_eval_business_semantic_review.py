from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

SCRIPT_PATH = ROOT / "scripts" / "eval-business-semantic-review.py"
_SPEC = importlib.util.spec_from_file_location("eval_business_semantic_review_under_test", SCRIPT_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT_PATH}")
REVIEW = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = REVIEW
_SPEC.loader.exec_module(REVIEW)


class BusinessSemanticReviewEvalTests(unittest.TestCase):
    def test_expected_review_finding_missing_fails(self) -> None:
        case = _case("hidden-rule-in-sql")
        actual = _actual("hidden-rule-in-sql", findings=[])

        rc, output = self._run_eval(case, actual)

        self.assertNotEqual(rc, 0)
        self.assertIn("missing expected review finding", output)

    def test_forbidden_behavior_not_avoided_fails(self) -> None:
        case = _case("review-forbidden")
        actual = _actual(
            "review-forbidden",
            findings=[_finding(category="hidden_sql_rule")],
            forbidden_behavior_avoided=[],
        )

        rc, output = self._run_eval(case, actual)

        self.assertNotEqual(rc, 0)
        self.assertIn("forbidden behavior not avoided", output)

    def _run_eval(self, case_yaml: str, actual_yaml: str | None) -> tuple[int, str]:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp_s:
            tmp = Path(tmp_s)
            eval_dir = tmp / "evals" / "business-semantic"
            output_dir = tmp / "evals" / "business-semantic-outputs"
            eval_dir.mkdir(parents=True)
            output_dir.mkdir(parents=True)
            case_id = _case_id(case_yaml)
            (eval_dir / f"{case_id}.yaml").write_text(case_yaml, encoding="utf-8")
            if actual_yaml is not None:
                (output_dir / f"{case_id}.actual.yaml").write_text(actual_yaml, encoding="utf-8")
            old_eval_dir = REVIEW.EVAL_DIR
            old_output_dir = REVIEW.OUTPUT_DIR
            REVIEW.EVAL_DIR = eval_dir
            REVIEW.OUTPUT_DIR = output_dir
            buffer = io.StringIO()
            try:
                with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
                    rc = REVIEW.main()
            finally:
                REVIEW.EVAL_DIR = old_eval_dir
                REVIEW.OUTPUT_DIR = old_output_dir
        return rc, buffer.getvalue()


def _case(case_id: str) -> str:
    return f"""case_id: {case_id}
expected_review_findings:
  - finding_id: BSP-HIDDEN-SQL-RULE
    category: hidden_sql_rule
    impacted_claim: renewal status filter
    required_fix: catalog rule and add changed-path validation
forbidden_behavior:
  - approve SQL condition without rule catalog
"""


def _actual(case_id: str, *, findings: list[str], forbidden_behavior_avoided: list[str] | None = None) -> str:
    avoided = forbidden_behavior_avoided if forbidden_behavior_avoided is not None else ["approve SQL condition without rule catalog"]
    finding_text = "\n".join(findings)
    return f"""actual_route:
  stage: code-review
  business_semantic_pack_required: true
actual_review:
  findings:
{finding_text}
  forbidden_behavior_avoided: {avoided}
  residual_risk: []
"""


def _finding(category: str = "hidden_sql_rule") -> str:
    return f"""    - finding_id: BSP-HIDDEN-SQL-RULE
      severity: high
      category: {category}
      impacted_claim: renewal status filter
      evidence: [fixture]
      required_fix: catalog rule and add changed-path validation
      validation_required: changed-path validation
"""


def _case_id(case_yaml: str) -> str:
    return next(line.split(":", 1)[1].strip() for line in case_yaml.splitlines() if line.startswith("case_id:"))


if __name__ == "__main__":
    unittest.main()
