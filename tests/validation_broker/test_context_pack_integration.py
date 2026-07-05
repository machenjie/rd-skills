from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from validation_broker.command_resolver import resolve_validation_plan


def commands(plan: dict[str, object]) -> list[dict[str, object]]:
    return [item for item in plan.get("recommended_commands", []) or [] if isinstance(item, dict)]


class ContextPackIntegrationTests(unittest.TestCase):
    def test_context_pack_candidate_preserves_scope_and_coverage(self) -> None:
        repo_context = {
            "task_context_pack": {
                "changed_paths": ["unknown/file.bin"],
                "validation_candidates": [
                    {
                        "command": "python3 scripts/custom-check.py",
                        "proves": "custom context-pack validator",
                        "scope": "narrow",
                        "category": "context_pack",
                        "covered_paths": ["unknown/file.bin"],
                        "covered_risk_surfaces": ["context-pack"],
                    }
                ],
            }
        }
        plan = resolve_validation_plan(["unknown/file.bin"], repo_context=repo_context)

        selected = commands(plan)
        custom = next(item for item in selected if item["command"] == "python3 scripts/custom-check.py")
        self.assertEqual(custom["level"], "narrow")
        self.assertEqual(custom["covered_path_patterns"], ["unknown/file.bin"])
        self.assertIn("unknown/file.bin", plan["unknown_paths"])

    def test_repository_context_wrapper_is_accepted(self) -> None:
        repo_context = {
            "repository_context": {
                "validation_candidates": [
                    {
                        "command": "python3 scripts/wrapped-check.py",
                        "proves": "wrapped preflight candidate",
                        "scope": "module",
                    }
                ],
                "changed_paths": ["src/repository_intelligence/graph/repo_indexer.py"],
            }
        }
        plan = resolve_validation_plan(
            ["src/repository_intelligence/graph/repo_indexer.py"],
            repo_context=repo_context,
        )

        self.assertIn("python3 scripts/wrapped-check.py", {item["command"] for item in commands(plan)})


if __name__ == "__main__":
    unittest.main()
