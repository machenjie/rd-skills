from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
EVAL_SCRIPT = ROOT / "scripts" / "eval-routing.py"
SCRIPTS_DIR = ROOT / "scripts"


def _load_eval_routing() -> ModuleType:
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    spec = importlib.util.spec_from_file_location("eval_routing", EVAL_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not import eval-routing.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EVAL_ROUTING = _load_eval_routing()


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
    schema_version: 1
    current_stage: bug-fix
    next_stage: testing
    product_surface: backend-product
    language_surface: none
    selected_skills:
      - backend-change-builder
      - security-privacy-gate
      - quality-test-gate
    selected_capabilities:
      - authentication-authorization
      - logging-error-handling
      - regression-testing
    selected_domain_extensions: []
    context_budget_mode: staged-plan
    context_budget_rationale: L3 security bug fix needs staged evidence while the active stage stays bug-fix
    required_evidence:
      - minimal diff
      - same-pattern scan record
      - deleted or rejected complexity
      - regression test
      - blast-radius note
    required_quality_gates:
      - requirement gate
      - impact gate
      - implementation gate
      - security gate
      - test gate
      - documentation gate
    skipped_capabilities:
      - capability: release-rollback
        reason: no release sequencing required for this route
    handoff_target: testing
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


def _validate_case_data(case_data: dict[str, object]) -> list[str]:
    skills, capabilities, extensions = EVAL_ROUTING._load_registry_names()
    allowed_triggers, allowed_gates, allowed_stages = (
        EVAL_ROUTING._load_routing_allow_lists()
    )
    errors: list[str] = []
    EVAL_ROUTING._validate_case(
        ROOT / "evals" / "routing" / f"{case_data['id']}.yaml",
        case_data,
        set(),
        skills,
        capabilities,
        extensions,
        allowed_triggers,
        allowed_gates,
        allowed_stages,
        errors,
    )
    return errors


def _minimal_l2_case() -> dict[str, object]:
    return {
        "id": "test-stage-required",
        "description": "Synthetic L2 routing case.",
        "prompt": "Add a backend behavior change.",
        "expected": {
            "complexity": "L2",
            "risk_triggers": [],
            "skills": ["backend-change-builder"],
            "capabilities": ["implementation-structure-design"],
            "domain_extensions": [],
            "quality_gates": ["implementation gate"],
        },
    }


class EvalRoutingCandidateTests(unittest.TestCase):
    def test_valid_candidate_with_stage_and_references_passes(self) -> None:
        result = _run_candidate(VALID_BACKEND_AUTH_IDOR)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1 router output(s) matched", result.stdout)

    def test_missing_stage_route_fails_for_l2_plus_candidate(self) -> None:
        candidate = VALID_BACKEND_AUTH_IDOR.replace(
            "  stage_route_manifest:\n"
            "    schema_version: 1\n"
            "    current_stage: bug-fix\n"
            "    next_stage: testing\n"
            "    product_surface: backend-product\n"
            "    language_surface: none\n"
            "    selected_skills:\n"
            "      - backend-change-builder\n"
            "      - security-privacy-gate\n"
            "      - quality-test-gate\n"
            "    selected_capabilities:\n"
            "      - authentication-authorization\n"
            "      - logging-error-handling\n"
            "      - regression-testing\n"
            "    selected_domain_extensions: []\n"
            "    context_budget_mode: staged-plan\n"
            "    context_budget_rationale: L3 security bug fix needs staged evidence while the active stage stays bug-fix\n"
            "    required_evidence:\n"
            "      - minimal diff\n"
            "      - same-pattern scan record\n"
            "      - deleted or rejected complexity\n"
            "      - regression test\n"
            "      - blast-radius note\n"
            "    required_quality_gates:\n"
            "      - requirement gate\n"
            "      - impact gate\n"
            "      - implementation gate\n"
            "      - security gate\n"
            "      - test gate\n"
            "      - documentation gate\n"
            "    skipped_capabilities:\n"
            "      - capability: release-rollback\n"
            "        reason: no release sequencing required for this route\n"
            "    handoff_target: testing\n",
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

    def test_unknown_candidate_stage_fails(self) -> None:
        candidate = VALID_BACKEND_AUTH_IDOR.replace(
            "current_stage: bug-fix",
            "current_stage: not-a-stage",
        )
        result = _run_candidate(candidate)
        self.assertEqual(result.returncode, 1)
        self.assertIn("current_stage must be one of", result.stderr)

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

    def test_l2_plus_golden_requires_expected_stage(self) -> None:
        case_data = _minimal_l2_case()
        errors = _validate_case_data(case_data)
        self.assertIn(
            "evals/routing/test-stage-required.yaml: expected.expected_stage "
            "is required for L2 cases unless expected.stage_route_required is false",
            errors,
        )

    def test_unknown_golden_expected_stage_fails(self) -> None:
        case_data = _minimal_l2_case()
        expected = case_data["expected"]
        assert isinstance(expected, dict)
        expected["expected_stage"] = "not-a-stage"
        expected["expected_context_budget_mode"] = "single-stage"
        errors = _validate_case_data(case_data)
        self.assertTrue(
            any("expected.expected_stage must be one of" in error for error in errors),
            errors,
        )

    def test_stage_route_skip_reason_allows_missing_expected_stage(self) -> None:
        case_data = _minimal_l2_case()
        expected = case_data["expected"]
        assert isinstance(expected, dict)
        expected["stage_route_required"] = False
        expected["stage_route_skip_reason"] = "single trivial edit has no stage route"
        errors = _validate_case_data(case_data)
        self.assertNotIn(
            "expected.expected_stage is required",
            "\n".join(errors),
        )

    def test_domain_extension_can_own_selected_capability(self) -> None:
        metadata = EVAL_ROUTING._load_capability_metadata()
        actual_sets = {
            "skills": ["frontend-change-builder"],
            "capabilities": ["python-professional-usage"],
            "domain_extensions": ["ai-product-extension"],
        }
        errors: list[str] = []
        EVAL_ROUTING._enforce_actual_capability_references(
            "candidate.yaml",
            actual_sets,
            {"references/capabilities/92-python-professional-usage.md"},
            metadata,
            errors,
        )
        self.assertEqual(errors, [])

    def test_unowned_selected_capability_still_fails(self) -> None:
        metadata = EVAL_ROUTING._load_capability_metadata()
        actual_sets = {
            "skills": ["frontend-change-builder"],
            "capabilities": ["python-professional-usage"],
            "domain_extensions": ["web3-product-extension"],
        }
        errors: list[str] = []
        EVAL_ROUTING._enforce_actual_capability_references(
            "candidate.yaml",
            actual_sets,
            {"references/capabilities/92-python-professional-usage.md"},
            metadata,
            errors,
        )
        self.assertIn(
            "candidate.yaml: selected capability 'python-professional-usage' "
            "does not map to any actual selected skill or domain extension through used_by",
            errors,
        )


if __name__ == "__main__":
    unittest.main()
