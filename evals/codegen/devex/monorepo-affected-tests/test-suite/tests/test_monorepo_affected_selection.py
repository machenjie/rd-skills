from __future__ import annotations

import importlib
import os
import sys
import unittest
from pathlib import Path


ROOT = Path(os.environ.get("CHANGEFORGE_CODEGEN_CANDIDATE_DIR", Path.cwd()))


def module(name: str):
    sys.path.insert(0, str(ROOT))
    for loaded in list(sys.modules):
        if loaded == "affected_tests" or loaded.startswith("affected_tests."):
            del sys.modules[loaded]
    return importlib.import_module(name)


class MonorepoAffectedSelectionAssertions(unittest.TestCase):
    def test_graph_slice_selects_transitive_dependents(self) -> None:
        affected_packages = module("affected_tests.graph_selection").affected_packages
        graph = {"shared": {"api"}, "api": {"web"}}
        self.assertEqual(affected_packages({"shared"}, graph), {"shared", "api", "web"})

    def test_cache_slice_covers_every_input_and_uses_safe_fallback(self) -> None:
        policy = module("affected_tests.cache_policy")
        key = policy.cache_key("graph-v1", "tool-v2", "lock-a", "generated-b")
        self.assertTrue(all(signal in key for signal in ("graph-v1", "tool-v2", "lock-a", "generated-b")))
        self.assertEqual(policy.fallback_for_unknown_path("unknown/file.txt"), "full-suite")

    def test_integration_consumes_graph_and_cache_slices_together(self) -> None:
        select_tests = module("affected_tests.selector").select_tests
        result = select_tests(
            {"shared"},
            {"shared": {"api"}, "api": {"web"}},
            graph_version="graph-v1",
            tool_version="tool-v2",
            lockfile_digest="lock-a",
            generated_digest="generated-b",
        )
        self.assertEqual(result["selected"], ["api", "shared", "web"])
        self.assertIn("transitive", str(result["reason"]).casefold())
        self.assertTrue(
            all(signal in str(result["cache_key"]) for signal in ("graph-v1", "tool-v2", "lock-a", "generated-b"))
        )

    def test_integration_unknown_path_forces_full_suite_with_explanation(self) -> None:
        select_tests = module("affected_tests.selector").select_tests
        result = select_tests(
            {"shared"},
            {"shared": {"api"}},
            graph_version="graph-v1",
            tool_version="tool-v2",
            lockfile_digest="lock-a",
            generated_digest="generated-b",
            unknown_paths={"tools/unmapped.file"},
        )
        self.assertEqual(result["selected"], ["full-suite"])
        self.assertIn("unknown", str(result["reason"]).casefold())


if __name__ == "__main__":
    unittest.main()
