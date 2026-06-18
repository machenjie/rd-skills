from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from validation_broker.command_registry import command_kind, matching_categories, registry_commands


class CommandRegistryTests(unittest.TestCase):
    def test_hook_runtime_path_matches_registry_category(self) -> None:
        self.assertEqual(
            matching_categories(["src/hook-runtime/scripts/changeforge_common.py"]),
            ["hook_runtime"],
        )

    def test_runtime_governance_paths_match_registry_categories(self) -> None:
        cases = {
            "src/repository_intelligence/cache/repo_hash.py": "repository_intelligence",
            "scripts/index-repository.py": "repository_intelligence",
            "scripts/build-context-pack.py": "repository_intelligence",
            "scripts/validate-repository-graph.py": "repository_intelligence",
            "scripts/validate-context-pack.py": "repository_intelligence",
            "src/project_memory/privacy.py": "project_memory",
            "scripts/review-project-memory.py": "project_memory",
            "scripts/promote-memory-candidate.py": "project_memory",
            "scripts/validate-project-memory.py": "project_memory",
            "src/trajectory/trajectory_analyzer.py": "trajectory",
            "scripts/inspect-trajectory.py": "trajectory",
            "scripts/validate-trajectory.py": "trajectory",
            "src/validation_broker/validation_result_parser.py": "validation_broker",
            "scripts/resolve-validation.py": "validation_broker",
            "scripts/validate-validation-broker.py": "validation_broker",
            "scripts/validate-hooks.py": "hook_runtime",
            "scripts/review-agent-telemetry.py": "telemetry",
            "tests/telemetry/test_review_agent_telemetry.py": "telemetry",
            "evals/routing/cases.yaml": "evals",
            "reports/professional-scorecard.json": "generated_artifacts",
            "installers/install.py": "installer_build_profile",
            "scripts/build.py": "installer_build_profile",
            "src/unowned/new_module.py": "source",
            "tests/unknown/test_sample.py": "tests",
        }
        for path, category in cases.items():
            with self.subTest(path=path):
                self.assertIn(category, matching_categories([path]))

    def test_known_command_kind_is_narrow(self) -> None:
        self.assertEqual(command_kind("python3 scripts/validate-hooks.py"), "narrow")
        self.assertEqual(command_kind("python3 scripts/validate-validation-broker.py"), "narrow")

    def test_registry_is_deterministic(self) -> None:
        first = [command.command for command in registry_commands()]
        second = [command.command for command in registry_commands()]
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
