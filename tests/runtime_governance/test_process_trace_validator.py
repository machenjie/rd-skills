from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from process_governance.process_trace_validator import validate_phase_artifact  # noqa: E402


COMMAND = "python3 -m unittest tests/test_runtime.py"


class RuntimeProcessTraceValidatorTests(unittest.TestCase):
    def test_rejects_generic_pdd(self) -> None:
        errors = validate_phase_artifact(
            "pdd",
            {
                "problem": "Improve candidate behavior.",
                "user_or_system_impact": ["candidate passes"],
                "acceptance_criteria": [
                    "requested benchmark behavior is observable through public API or documented setup/test contract"
                ],
                "constraints": ["preserve setup"],
                "non_goals": ["none"],
                "risk_surfaces": ["quality"],
                "validation_signal": [COMMAND],
            },
        )

        self.assertTrue(any("generic" in error for error in errors))

    def test_rejects_sdd_safe_assumption_on_high_risk_surface(self) -> None:
        errors = validate_phase_artifact(
            "sdd",
            {
                "modules": ["auth migration module"],
                "public_api": ["new public API for auth migration"],
                "data_flow": ["request to migration"],
                "error_contract": ["permission denial"],
                "failure_modes": ["schema rollback failure"],
                "logging_decision": {"needed": False, "rationale": "tests cover behavior"},
                "design_decision_points": [
                    {
                        "id": "auth-migration-api",
                        "decision": "Assume auth migration public API placement",
                        "trigger": "Choice changes auth, schema, and migration behavior.",
                        "blocking": False,
                        "user_choice_status": "assumed_with_rationale",
                        "safe_default_if_user_unavailable": "Use existing auth API path.",
                        "resolution_evidence": "local reversible conventional existing pattern acceptance-neutral",
                        "residual_risk": "Low.",
                    }
                ],
                "assumption_policy": "block_when_wrong_answer_changes_contract_architecture_data_security_acceptance_or_user_visible_behavior",
            },
        )

        self.assertTrue(any("high-risk" in error for error in errors))

    def test_rejects_tdd_boolean_only_traceability(self) -> None:
        errors = validate_phase_artifact(
            "tdd",
            {
                "acceptance_to_tests": True,
                "invariant_to_tests_or_code": True,
                "public_api_to_tests": True,
                "failure_mode_tests": True,
                "validation_commands": [COMMAND],
            },
        )

        self.assertTrue(any("not a boolean" in error or "not a mapping" in error for error in errors))

    def test_accepts_complete_source_backed_phase_artifacts(self) -> None:
        pdd = {
            "problem": "Prevent unsafe URL fetches.",
            "user_or_system_impact": ["metadata services are protected"],
            "acceptance_criteria": ["metadata URL is denied before fetch"],
            "constraints": ["preserve public URL validation entrypoint"],
            "non_goals": ["new HTTP client"],
            "risk_surfaces": ["security"],
            "validation_signal": [COMMAND],
        }
        ddd = {
            "domain_terms": ["URL candidate", "network boundary"],
            "invariants": ["unsafe URL is never fetched"],
            "ownership_decision": ["URL policy owns deny decision"],
            "side_effect_boundaries": ["fetch happens only after allowlist"],
        }
        sdd = {
            "modules": ["URL validation module"],
            "public_api": ["existing URL validation public entrypoint"],
            "data_flow": ["raw URL to validation to optional fetch"],
            "error_contract": ["stable unsafe-url error category"],
            "failure_modes": ["metadata URL denial"],
            "logging_decision": {"needed": False, "rationale": "public validation tests cover denial"},
            "design_decision_points": [],
            "no_design_choice_rationale": "Prompt source and repository convention require the existing URL validation boundary.",
            "assumption_policy": "block_when_wrong_answer_changes_contract_architecture_data_security_acceptance_or_user_visible_behavior",
        }
        tdd = {
            "acceptance_to_tests": {"metadata URL is denied before fetch": [COMMAND]},
            "invariant_to_tests_or_code": {"unsafe URL is never fetched": [COMMAND]},
            "public_api_to_tests": {"existing URL validation public entrypoint": [COMMAND]},
            "failure_mode_tests": [{"failure_mode": "metadata URL denial", "tests": [COMMAND]}],
            "validation_commands": [COMMAND],
        }

        self.assertEqual(validate_phase_artifact("pdd", pdd), [])
        self.assertEqual(validate_phase_artifact("ddd", ddd), [])
        self.assertEqual(validate_phase_artifact("sdd", sdd), [])
        self.assertEqual(validate_phase_artifact("tdd", tdd), [])


if __name__ == "__main__":
    unittest.main()
