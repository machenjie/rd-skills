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

    def test_repository_intelligence_path_selects_graph_and_context_pack_validators(self) -> None:
        plan = resolve_validation_plan(["src/repository_intelligence/cache/repo_hash.py"])
        selected = commands(plan)
        self.assertIn(
            "python3 scripts/validate-repository-graph.py --graph /tmp/changeforge-repo-graph.json",
            selected,
        )
        self.assertIn(
            "python3 scripts/validate-context-pack.py --context-pack /tmp/changeforge-context-pack.json",
            selected,
        )

    def test_project_memory_trajectory_and_broker_paths_select_validators(self) -> None:
        cases = {
            "src/project_memory/privacy.py": "python3 scripts/validate-project-memory.py",
            "src/trajectory/trajectory_analyzer.py": "python3 scripts/validate-trajectory.py",
            "src/validation_broker/validation_result_parser.py": "python3 scripts/validate-validation-broker.py",
        }
        for path, expected in cases.items():
            with self.subTest(path=path):
                plan = resolve_validation_plan([path])
                self.assertIn(expected, commands(plan))

    def test_unknown_path_returns_conservative_recommendation(self) -> None:
        plan = resolve_validation_plan(["unknown/path.txt"])
        self.assertTrue(plan["conservative"])
        self.assertIn("python3 -m unittest discover -s tests", commands(plan))
        self.assertIn("unknown", plan["matched_categories"])


if __name__ == "__main__":
    unittest.main()
