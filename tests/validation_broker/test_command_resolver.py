from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from validation_broker.command_resolver import resolve_validation_plan


def commands(plan: dict[str, object], field: str = "recommended_commands") -> list[str]:
    return [
        str(item.get("command"))
        for item in plan.get(field, []) or []
        if isinstance(item, dict)
    ]


class CommandResolverTests(unittest.TestCase):
    def test_hook_runtime_path_selects_hook_validators(self) -> None:
        plan = resolve_validation_plan(["src/hook-runtime/scripts/changeforge_common.py"])
        self.assertIn("python3 scripts/validate-hooks.py", commands(plan))
        self.assertIn("python3 -m unittest discover -s tests/hook_runtime", commands(plan))

    def test_registry_path_selects_registry_validators(self) -> None:
        plan = resolve_validation_plan(["src/registry/routing-rules.yaml"])
        self.assertIn("python3 scripts/validate-registry.py", commands(plan))
        self.assertIn("python3 scripts/eval-routing.py", commands(plan))

    def test_capability_path_selects_capability_validators(self) -> None:
        plan = resolve_validation_plan(["src/foundation/capabilities/test-strategy/SKILL.md"])
        self.assertIn("python3 scripts/validate-capabilities.py", commands(plan))
        self.assertIn(
            "python3 scripts/eval-skill-professionalism.py --coverage-matrix",
            commands(plan),
        )

    def test_unknown_path_returns_conservative_recommendation(self) -> None:
        plan = resolve_validation_plan(["unknown/path.txt"])
        self.assertTrue(plan["conservative"])
        self.assertIn("python3 -m unittest discover -s tests", commands(plan))
        self.assertIn("unknown", plan["matched_categories"])


if __name__ == "__main__":
    unittest.main()
