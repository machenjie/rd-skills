from __future__ import annotations

import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
RUNNER_PATH = SCRIPTS / "run-ci-tests.py"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _load_runner():
    spec = importlib.util.spec_from_file_location("run_ci_tests", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CiTestRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = _load_runner()
        cls.core = json.loads(
            (ROOT / "src/control-model/core-contracts.json").read_text(
                encoding="utf-8"
            )
        )

    def test_selection_is_the_unsharded_shared_resolver_result(self) -> None:
        resolved = {
            "schema_version": 1,
            "kind": "changeforge.impact_selection",
            "base_sha": "a" * 40,
            "head_sha": "b" * 40,
            "status": "resolved",
            "reason": "affected-targets",
            "changed_paths": [],
            "selected_producer_ids": ["validate-task-contracts"],
            "selected_test_modules": [
                "tests/scripts/test_validation_utils.py",
                "tests/scripts/test_run_ci_tests.py",
                "tests/scripts/test_impact_graph.py",
            ],
            "selected_test_modules_by_layer": {
                "unit": ["tests/scripts/test_validation_utils.py"],
                "integration": [],
                "contract": [
                    "tests/scripts/test_impact_graph.py",
                    "tests/scripts/test_run_ci_tests.py",
                ],
                "governance": [],
                "release": [],
            },
            "producer_explanations": [],
        }
        with mock.patch.object(self.runner, "select", return_value=resolved) as select:
            result = self.runner._selection(
                ROOT, self.core, resolved["base_sha"], resolved["head_sha"]
            )
        select.assert_called_once_with(
            ROOT, self.core, resolved["base_sha"], resolved["head_sha"]
        )
        self.assertEqual(resolved, result)
        self.assertNotIn("shards", result)

    def test_runner_projects_resolver_flat_targets_without_layer_policy(self) -> None:
        source = RUNNER_PATH.read_text(encoding="utf-8")
        self.assertNotIn("always_layers", source)
        self.assertNotIn("direct_only_layers", source)
        self.assertNotIn("forbidden_layers", source)

    def test_unittest_exec_is_direct_and_preserves_selected_argv(self) -> None:
        modules = ["tests/scripts/test_run_ci_tests.py"]
        with mock.patch.object(self.runner.os, "chdir") as chdir, mock.patch.object(
            self.runner.os, "execv"
        ) as execv:
            self.runner._exec_unittest(ROOT, modules)
        chdir.assert_called_once_with(ROOT)
        execv.assert_called_once_with(
            sys.executable,
            [sys.executable, "-m", "unittest", *modules],
        )

    def test_empty_no_impact_selection_exits_zero_with_explicit_signal(self) -> None:
        selection = {
            "reason": "known-no-impact",
            "selected_test_modules": [],
        }
        with mock.patch.object(self.runner, "load_core", return_value=self.core), mock.patch.object(
            self.runner, "_selection", return_value=selection
        ), mock.patch.object(self.runner, "_exec_unittest") as execute, mock.patch.object(
            sys, "stdout", io.StringIO()
        ) as stdout:
            exit_code = self.runner.main(
                ["run", "--base", "a" * 40, "--head", "b" * 40]
            )
        self.assertEqual(0, exit_code)
        execute.assert_not_called()
        payload = json.loads(stdout.getvalue())
        self.assertEqual("known-no-impact", payload["reason"])
        self.assertEqual([], payload["test_modules"])

    def test_deleted_test_is_classified_but_never_executed(self) -> None:
        selection = {
            "reason": "affected-targets",
            "selected_test_modules": [],
        }
        with mock.patch.object(self.runner, "load_core", return_value=self.core), mock.patch.object(
            self.runner, "_selection", return_value=selection
        ), mock.patch.object(self.runner, "_exec_unittest") as execute:
            exit_code = self.runner.main(
                ["run", "--base", "a" * 40, "--head", "b" * 40]
            )
        self.assertEqual(0, exit_code)
        execute.assert_not_called()

    def test_renamed_test_executes_only_the_new_path(self) -> None:
        new_path = "tests/scripts/test_new.py"
        selection = {
            "reason": "affected-targets",
            "selected_test_modules": [new_path],
        }
        with mock.patch.object(self.runner, "load_core", return_value=self.core), mock.patch.object(
            self.runner, "_selection", return_value=selection
        ), mock.patch.object(self.runner, "_exec_unittest") as execute:
            self.assertEqual(
                0,
                self.runner.main(
                    [
                        "run",
                        "--base",
                        "a" * 40,
                        "--head",
                        "b" * 40,
                    ]
                ),
            )
        execute.assert_called_once_with(ROOT, [new_path])

    def test_resolver_failure_is_nonzero_and_machine_readable(self) -> None:
        failure = self.runner.ImpactGraphError(
            "unmatched-path", "path has no Core classification"
        )
        with mock.patch.object(self.runner, "load_core", return_value=self.core), mock.patch.object(
            self.runner, "_selection", side_effect=failure
        ), mock.patch.object(sys, "stderr", io.StringIO()) as stderr:
            exit_code = self.runner.main(
                ["explain", "--base", "a" * 40, "--head", "b" * 40]
            )
        self.assertEqual(2, exit_code)
        diagnostic = json.loads(stderr.getvalue().split(": ", 1)[1])
        self.assertEqual("unmatched-path", diagnostic["reason"])

    def test_runner_contains_no_path_mapping_or_full_fallback(self) -> None:
        source = RUNNER_PATH.read_text(encoding="utf-8")
        self.assertIn("from impact_graph import", source)
        self.assertNotIn("ci_validation_contract", source)
        self.assertNotIn("fnmatch", source)
        self.assertNotIn("fallback", source.casefold())
        self.assertNotIn("subprocess", source)
        self.assertNotIn("shard", source.casefold())


if __name__ == "__main__":
    unittest.main()
