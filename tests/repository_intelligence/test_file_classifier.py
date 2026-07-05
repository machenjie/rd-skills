from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from repository_intelligence.graph.file_classifier import classify_kind, classify_role, should_index


class FileClassifierTests(unittest.TestCase):
    def test_classifies_roles_and_kinds(self) -> None:
        self.assertEqual(classify_kind("src/hook-runtime/scripts/router.py"), "python")
        self.assertEqual(classify_role("src/hook-runtime/scripts/router.py"), "hook_runtime")
        self.assertEqual(classify_role("src/foundation/capabilities/repository-context-map/SKILL.md"), "capability")
        self.assertEqual(classify_role("src/professional-skills/change-impact-analyzer/SKILL.md"), "skill")
        self.assertEqual(classify_role("src/registry/capabilities.yaml"), "registry")
        self.assertEqual(classify_role("tests/repository_intelligence/test_file_classifier.py"), "test")

    def test_excludes_generated_and_environment_directories(self) -> None:
        self.assertFalse(should_index("dist/change-impact-analyzer/SKILL.md"))
        self.assertFalse(should_index(".git/config"))
        self.assertFalse(should_index("node_modules/pkg/index.js"))
        self.assertFalse(should_index(".venv/lib/site.py"))
        self.assertTrue(should_index("src/registry/capabilities.yaml"))


if __name__ == "__main__":
    unittest.main()
