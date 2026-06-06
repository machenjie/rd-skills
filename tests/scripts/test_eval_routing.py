from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVAL_SCRIPT = ROOT / "scripts" / "eval-routing.py"


VALID_BACKEND_AUTH_IDOR = """case_id: backend-auth-idor
actual:
  complexity: L3
  risk_level: high
  skills:
    - change-intake-compiler
    - change-impact-analyzer
    - backend-change-builder
    - security-privacy-gate
    - quality-test-gate
    - change-documentation-gate
  capabilities:
    - implementation-structure-design
    - permission-boundary-modeling
    - authentication-authorization
    - web-security
    - input-validation
    - regression-testing
    - logging-error-handling
  domain_extensions: []
  quality_gates:
    - requirement gate
    - impact gate
    - implementation gate
    - security gate
    - test gate
    - documentation gate
  required_references:
    - references/routing-rules.md
    - references/skill-registry.md
    - references/capability-index.md
    - references/domain-extension-index.md
    - references/capabilities/101-implementation-structure-design.md
    - references/capabilities/16-permission-boundary-modeling.md
    - references/capabilities/41-authentication-authorization.md
    - references/capabilities/44-logging-error-handling.md
    - references/capabilities/53-input-validation.md
    - references/capabilities/54-web-security.md
    - references/capabilities/64-regression-testing.md
  stage_route_manifest:
    current_stage: bug-fix
    context_budget_mode: staged-plan
    skipped_capabilities:
      - capability: release-rollback
        reason: no release sequencing required for this route
"""


def _run_candidate(candidate_text: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmp:
        candidate = Path(tmp) / "backend-auth-idor.actual.yaml"
        candidate.write_text(candidate_text, encoding="utf-8")
        return subprocess.run(
            [
                sys.executable,
                str(EVAL_SCRIPT),
                "--candidate-output",
                str(candidate),
            ],
            text=True,
            capture_output=True,
            cwd=str(ROOT),
            check=False,
        )


class EvalRoutingCandidateTests(unittest.TestCase):
    def test_valid_candidate_with_stage_and_references_passes(self) -> None:
        result = _run_candidate(VALID_BACKEND_AUTH_IDOR)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1 router output(s) matched", result.stdout)

    def test_missing_stage_route_fails_for_l2_plus_candidate(self) -> None:
        candidate = VALID_BACKEND_AUTH_IDOR.replace(
            "  stage_route_manifest:\n"
            "    current_stage: bug-fix\n"
            "    context_budget_mode: staged-plan\n"
            "    skipped_capabilities:\n"
            "      - capability: release-rollback\n"
            "        reason: no release sequencing required for this route\n",
            "",
        )
        result = _run_candidate(candidate)
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing changeforge_stage_route", result.stderr)

    def test_wrong_stage_fails_when_golden_declares_expected_stage(self) -> None:
        candidate = VALID_BACKEND_AUTH_IDOR.replace(
            "current_stage: bug-fix",
            "current_stage: code-review",
        )
        result = _run_candidate(candidate)
        self.assertEqual(result.returncode, 1)
        self.assertIn("current_stage must be 'bug-fix'", result.stderr)

    def test_missing_selected_capability_reference_fails(self) -> None:
        candidate = VALID_BACKEND_AUTH_IDOR.replace(
            "    - references/capabilities/53-input-validation.md\n",
            "",
        )
        result = _run_candidate(candidate)
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "missing selected capability reference "
            "'references/capabilities/53-input-validation.md'",
            result.stderr,
        )


if __name__ == "__main__":
    unittest.main()
