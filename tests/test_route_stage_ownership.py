from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from validation_utils import load_yaml_file


ROUTER = ROOT / "src" / "professional-skills" / "change-forge-router" / "SKILL.md"


def _text(relative: str | Path) -> str:
    path = ROOT / relative if isinstance(relative, str) else relative
    return path.read_text(encoding="utf-8")


class RouteStageOwnershipTests(unittest.TestCase):
    def test_router_lists_process_and_logging_skills(self) -> None:
        text = _text(ROUTER)
        self.assertIn("development-process-orchestrator", text)
        self.assertIn("PDD/DDD/SDD/TDD process orchestration", text)
        self.assertIn("logging-design-gate", text)
        self.assertIn("structured logging", text)

    def test_router_contains_logging_trigger_terms(self) -> None:
        text = _text(ROUTER).casefold()
        for term in (
            "log",
            "logger",
            "logging",
            "audit log",
            "diagnostic log",
            "security log",
            "access log",
            "structured logging",
            "redaction",
            "trace_id",
            "span_id",
            "request_id",
            "correlation_id",
            "fallback log",
            "retry log",
            "degradation log",
            "error log",
            "raw request body",
            "raw query",
            "authorization header",
            "cookie",
            "token",
            "pii",
        ):
            self.assertIn(term, text)

    def test_stage_owner_skills_declare_process_ownership(self) -> None:
        ownership = {
            "change-intake-compiler": "Own the PDD slice",
            "domain-impact-modeler": "Own the DDD slice",
            "architecture-impact-reviewer": "Own the SDD slice",
            "quality-test-gate": "Own the TDD slice",
            "ai-code-review-refactor": "Own cross-stage review",
            "logging-design-gate": "Own the SDD/TDD logging slice",
        }
        for skill, phrase in ownership.items():
            with self.subTest(skill=skill):
                self.assertIn(phrase, _text(f"src/professional-skills/{skill}/SKILL.md"))

    def test_stage_model_declares_process_and_logging_route_manifest_patterns(self) -> None:
        stage_model = load_yaml_file(ROOT / "src" / "registry" / "stage-model.yaml")
        ownership = stage_model["process_stage_ownership"]
        self.assertEqual(ownership["pdd"]["owner_skill"], "change-intake-compiler")
        self.assertEqual(ownership["ddd"]["owner_skill"], "domain-impact-modeler")
        self.assertEqual(ownership["sdd"]["owner_skill"], "architecture-impact-reviewer")
        self.assertEqual(ownership["sdd_logging_decision"]["owner_skill"], "logging-design-gate")
        self.assertEqual(ownership["tdd"]["owner_skill"], "quality-test-gate")
        self.assertEqual(ownership["cross_stage_review"]["owner_skill"], "ai-code-review-refactor")

        patterns = stage_model["route_manifest_patterns"]
        code_change = patterns["non_documentation_code_change"]
        for skill in (
            "development-process-orchestrator",
            "change-intake-compiler",
            "domain-impact-modeler",
            "architecture-impact-reviewer",
            "quality-test-gate",
        ):
            self.assertIn(skill, code_change["selected_skills"])
        for gate in (
            "pdd_acceptance_to_tdd_tests",
            "ddd_invariants_to_tdd_tests",
            "sdd_public_api_to_tdd_tests",
            "sdd_failure_modes_to_tdd_tests",
        ):
            self.assertIn(gate, code_change["required_quality_gates"])

        logging_change = patterns["logging_change"]
        self.assertIn("logging-design-gate", logging_change["selected_skills"])
        self.assertIn("logging-error-handling", logging_change["selected_capabilities"])
        for gate in (
            "logging_decision_has_type_level_fields_redaction",
            "logging_or_security_tests_present",
            "forbidden_secret_fields_absent",
        ):
            self.assertIn(gate, logging_change["required_quality_gates"])


if __name__ == "__main__":
    unittest.main()
