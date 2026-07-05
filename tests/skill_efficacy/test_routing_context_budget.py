from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "eval-routing.py"
SCRIPTS_DIR = ROOT / "scripts"


def _load_eval_routing() -> ModuleType:
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    spec = importlib.util.spec_from_file_location("eval_routing_budget", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not import eval-routing.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EVAL_ROUTING = _load_eval_routing()


class RoutingContextBudgetTests(unittest.TestCase):
    def test_budget_metrics_are_deterministic_proxy(self) -> None:
        budget = EVAL_ROUTING.context_budget_for_route(
            mode="minimal",
            selected_skills=["change-forge-router", "quality-test-gate"],
            selected_capabilities=["skill-efficacy-benchmark"],
            required_references=[
                "src/foundation/capabilities/skill-efficacy-benchmark/SKILL.md",
            ],
            skipped_references=[{"reference": "unused", "reason": "not needed"}],
            rationale="bounded fixture route",
        )

        self.assertEqual(budget["mode"], "minimal")
        self.assertEqual(budget["selected_skill_count"], 2)
        self.assertEqual(budget["selected_capability_count"], 1)
        self.assertEqual(budget["selected_reference_count"], 1)
        self.assertEqual(budget["skipped_reference_count"], 1)
        self.assertIsInstance(budget["estimated_token_cost"], int)
        self.assertIn("proxy", budget["estimate_method"])
        self.assertFalse(budget["over_budget"])

    def test_low_confidence_reference_bloat_marks_over_budget(self) -> None:
        references = [f"references/capabilities/{index}-example.md" for index in range(6)]
        budget = EVAL_ROUTING.context_budget_for_route(
            mode="minimal",
            selected_skills=["change-forge-router"],
            selected_capabilities=["skill-efficacy-benchmark"],
            required_references=references,
            rationale="too many references",
        )
        self.assertTrue(budget["over_budget"])

    def test_full_budget_mode_is_valid(self) -> None:
        budget = EVAL_ROUTING.context_budget_for_route(
            mode="full",
            selected_skills=[],
            selected_capabilities=[],
            required_references=[],
            rationale="full release review",
        )
        self.assertEqual(budget["mode"], "full")

    def test_stage_context_budget_requires_proxy_method(self) -> None:
        errors = EVAL_ROUTING._stage_context_budget_errors(
            "actual.yaml",
            {
                "context_budget_mode": "single-stage",
                "context_budget": {
                    "mode": "single-stage",
                    "selected_skill_count": 1,
                    "selected_capability_count": 1,
                    "selected_reference_count": 1,
                    "skipped_reference_count": 0,
                    "estimated_token_cost": 10,
                    "estimate_method": "real tokenizer",
                    "over_budget": False,
                    "rationale": "bounded route",
                },
            },
        )
        self.assertTrue(any("proxy" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
