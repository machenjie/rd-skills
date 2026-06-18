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
            "src/project_memory/privacy.py": "project_memory",
            "src/trajectory/trajectory_analyzer.py": "trajectory",
            "src/validation_broker/validation_result_parser.py": "validation_broker",
        }
        for path, category in cases.items():
            with self.subTest(path=path):
                self.assertEqual(matching_categories([path]), [category])

    def test_known_command_kind_is_narrow(self) -> None:
        self.assertEqual(command_kind("python3 scripts/validate-hooks.py"), "narrow")
        self.assertEqual(command_kind("python3 scripts/validate-validation-broker.py"), "narrow")

    def test_registry_is_deterministic(self) -> None:
        first = [command.command for command in registry_commands()]
        second = [command.command for command in registry_commands()]
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
