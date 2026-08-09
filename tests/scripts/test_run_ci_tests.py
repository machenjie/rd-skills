from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
RUNNER_PATH = SCRIPTS / "run-ci-tests.py"
CORE_PATH = ROOT / "src" / "control-model" / "core-contracts.json"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
FORMAL_WORKFLOW = ROOT / ".github" / "workflows" / "formal-release.yml"
CURRENT_PR_BASE = "d41e9bf7ec6e1dcd9279bba0611c082fc1beea3c"
FORMAL_WORKFLOW_SHA256 = (
    "0400f6b73eee4872ea81834132ee77f511cfe97453cfe784da30ddeaf2bd1f32"
)
CURRENT_PR_CHANGED_TEST_PATHS = {
    "evals/codegen/devex/bugfix-same-pattern-scan/test-suite/tests/"
    "test_bugfix_same_pattern_scan.py",
    "tests/scripts/test_audit_skill_content.py",
    "tests/scripts/test_build_safety.py",
    "tests/scripts/test_eval_agent_lightweight_utility.py",
    "tests/scripts/test_eval_core_principles.py",
    "tests/scripts/test_expert_panel_actionability.py",
    "tests/scripts/test_professional_completeness_carry_forward.py",
    "tests/scripts/test_professional_review_cost_fixture.py",
    "tests/scripts/test_professionalism_expert_panel.py",
    "tests/scripts/test_rds_006_task_dag_decomposition.py",
    "tests/scripts/test_root_disposition_lifecycle.py",
    "tests/scripts/test_validate_agent_profiles.py",
    "tests/scripts/test_validate_control_plane_prompt.py",
    "tests/scripts/test_validate_docs_consistency.py",
    "tests/scripts/test_validate_productization_assets.py",
    "tests/scripts/test_validate_root_content.py",
    "tests/scripts/test_validate_task_contracts.py",
    "tests/test_hookless_build_install.py",
}

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from validation_utils import CORE_CONTRACTS, validate_core_contracts  # noqa: E402


def _load_runner():
    if not RUNNER_PATH.is_file():
        raise AssertionError("missing bounded CI test selector runner")
    spec = importlib.util.spec_from_file_location("run_ci_tests", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CiSelectionCoreContractTests(unittest.TestCase):
    def test_core_contract_declares_single_ci_selection_authority(self) -> None:
        self.assertTrue(
            "ci_validation_contract" in CORE_CONTRACTS,
            "missing ci_validation_contract",
        )
        contract = CORE_CONTRACTS["ci_validation_contract"]
        self.assertEqual(1, contract["schema_version"])
        self.assertEqual("scripts/run-ci-tests.py", contract["runner"])
        self.assertEqual(2, contract["shard_count"])
        authorities = CORE_CONTRACTS["principle_acceptance_contract"]["authorities"]
        matches = [
            row
            for row in authorities
            if row["pointer"] == "/ci_validation_contract"
        ]
        self.assertEqual(1, len(matches))
        self.assertEqual("ci-validation-authority", matches[0]["id"])
        self.assertEqual([], validate_core_contracts(copy.deepcopy(CORE_CONTRACTS)))

    def test_ci_mapping_schema_and_references_fail_closed(self) -> None:
        base = copy.deepcopy(CORE_CONTRACTS)
        contract = base["ci_validation_contract"]
        mutations: list[tuple[str, dict, str]] = []

        missing_contract = copy.deepcopy(base)
        del missing_contract["ci_validation_contract"]
        mutations.append(("missing-contract", missing_contract, "ci_validation_contract"))

        malformed = copy.deepcopy(base)
        malformed["ci_validation_contract"]["mappings"][0]["extra"] = True
        mutations.append(("malformed-mapping", malformed, "fields must be exactly"))

        duplicate = copy.deepcopy(base)
        duplicate["ci_validation_contract"]["mappings"].append(
            copy.deepcopy(contract["mappings"][0])
        )
        mutations.append(("duplicate-mapping", duplicate, "mapping ids must be unique"))

        unknown_producer = copy.deepcopy(base)
        unknown_producer["ci_validation_contract"]["mappings"][0][
            "producer_ids"
        ] = ["unknown-producer"]
        mutations.append(
            ("unknown-producer", unknown_producer, "unknown producer id")
        )

        missing_test = copy.deepcopy(base)
        missing_test["ci_validation_contract"]["mappings"][0]["test_modules"] = [
            "tests/scripts/test_missing_ci_owner.py"
        ]
        mutations.append(("missing-test", missing_test, "test module does not exist"))

        traversal = copy.deepcopy(base)
        traversal["ci_validation_contract"]["mappings"][0]["test_modules"] = [
            "tests/../outside/test_escape.py"
        ]
        mutations.append(("traversal", traversal, "safe tests/ test module"))

        non_test = copy.deepcopy(base)
        non_test["ci_validation_contract"]["mappings"][0]["test_modules"] = [
            "docs/VALIDATION.md"
        ]
        mutations.append(("non-test", non_test, "safe tests/ test module"))

        duplicate_test = copy.deepcopy(base)
        existing_test = duplicate_test["ci_validation_contract"]["mappings"][0][
            "test_modules"
        ][0]
        duplicate_test["ci_validation_contract"]["mappings"][0][
            "test_modules"
        ] = [existing_test, existing_test]
        mutations.append(
            ("duplicate-test", duplicate_test, "test_modules must be unique strings")
        )

        for label, mutation, expected in mutations:
            with self.subTest(label=label):
                errors = validate_core_contracts(mutation)
                self.assertTrue(any(expected in error for error in errors), errors)


class CiTestSelectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = _load_runner()
        cls.core = json.loads(CORE_PATH.read_text(encoding="utf-8"))

    def test_changed_test_self_selects_and_shared_source_unions_tests(self) -> None:
        result = self.runner._selection_from_entries(
            ROOT,
            self.core,
            [
                ("M", "tests/scripts/test_run_ci_tests.py"),
                ("M", "scripts/validation_utils.py"),
            ],
            base_sha="a" * 40,
            head_sha="b" * 40,
        )
        self.assertFalse(result["fallback"])
        selected = set(result["selected_test_modules"])
        self.assertIn("tests/scripts/test_run_ci_tests.py", selected)
        self.assertIn("tests/scripts/test_validation_utils.py", selected)
        self.assertIn("tests/scripts/test_validate_task_contracts.py", selected)
        decisions = {row["path"]: row for row in result["changed_paths"]}
        shared = decisions["scripts/validation_utils.py"]
        self.assertIn("validate-task-contracts", shared["producer_ids"])
        self.assertIn("tests/scripts/test_validation_utils.py", shared["test_modules"])
        self.assertTrue(shared["rationale"])

    def test_required_owner_mappings_select_specific_regression_modules(self) -> None:
        cases = {
            "scripts/validation_utils.py": {
                "tests/scripts/test_validation_utils.py"
            },
            "scripts/eval-agent-lightweight.py": {
                "tests/scripts/test_eval_agent_lightweight_layer3_references.py"
            },
            "src/control-skills/engineering-control-plane/SKILL.md": {
                "tests/scripts/test_validate_control_skills.py",
                "tests/test_hookless_architecture.py",
            },
            "src/control-prompts/main-control-agent.md": {
                "tests/test_hookless_architecture.py"
            },
        }
        for path, expected in cases.items():
            with self.subTest(path=path):
                result = self.runner._selection_from_entries(
                    ROOT,
                    self.core,
                    [("M", path)],
                    base_sha="a" * 40,
                    head_sha="b" * 40,
                )
                self.assertFalse(result["fallback"], result)
                self.assertTrue(
                    expected.issubset(set(result["selected_test_modules"])), result
                )

    def test_unmatched_deleted_and_empty_selection_fall_back_full(self) -> None:
        cases = (
            ([('M', 'unknown/path with spaces.txt')], "unmatched-path"),
            ([('D', 'README.md')], "deleted-path"),
            ([('M', 'reports/core-principles-outcomes.json')], "empty-selection"),
            ([], "empty-diff"),
        )
        for entries, reason in cases:
            with self.subTest(reason=reason):
                result = self.runner._selection_from_entries(
                    ROOT,
                    self.core,
                    entries,
                    base_sha="a" * 40,
                    head_sha="b" * 40,
                )
                self.assertTrue(result["fallback"], result)
                self.assertEqual(reason, result["fallback_reason"])
                self.assertEqual(
                    self.runner._discover_full_suite_modules(ROOT, self.core),
                    result["selected_test_modules"],
                )

    def test_missing_invalid_zero_and_nonexistent_revisions_fall_back_full(self) -> None:
        head = "b" * 40
        base = "a" * 40
        for candidate_base, candidate_head, reason in (
            (None, head, "missing-revision"),
            (base, None, "missing-revision"),
            ("not-a-sha", head, "invalid-revision"),
            (base, "not-a-sha", "invalid-revision"),
            ("0" * 40, head, "zero-revision"),
            (base, "0" * 40, "zero-revision"),
        ):
            with self.subTest(reason=reason):
                result = self.runner.select(
                    ROOT, self.core, candidate_base, candidate_head
                )
                self.assertTrue(result["fallback"])
                self.assertEqual(reason, result["fallback_reason"])

        completed = subprocess.CompletedProcess(
            ["git", "cat-file"], 1, stdout=b"", stderr=b"missing"
        )
        with mock.patch.object(self.runner, "_run_git", return_value=completed):
            result = self.runner.select(ROOT, self.core, base, head)
        self.assertTrue(result["fallback"])
        self.assertEqual("nonexistent-revision", result["fallback_reason"])

        existing = subprocess.CompletedProcess(
            ["git", "cat-file"], 0, stdout=b"", stderr=b""
        )
        with mock.patch.object(
            self.runner, "_run_git", side_effect=[existing, completed]
        ):
            result = self.runner.select(ROOT, self.core, base, head)
        self.assertTrue(result["fallback"])
        self.assertEqual("nonexistent-revision", result["fallback_reason"])

    def test_nul_paths_are_preserved_and_git_never_uses_a_shell(self) -> None:
        payload = b"M\0odd path\nwith newline.txt\0"
        self.assertEqual(
            [("M", "odd path\nwith newline.txt")],
            self.runner._parse_name_status_z(payload),
        )
        completed = subprocess.CompletedProcess(
            ["git", "status"], 0, stdout=b"", stderr=b""
        )
        with mock.patch.object(
            self.runner.subprocess, "run", return_value=completed
        ) as run:
            self.runner._run_git(ROOT, ["status", "--short"])
        args, kwargs = run.call_args
        self.assertEqual(["git", "status", "--short"], args[0])
        self.assertEqual(ROOT, kwargs["cwd"])
        self.assertFalse(kwargs.get("shell", False))
        self.assertFalse(kwargs["check"])

    def test_shards_are_stable_disjoint_complete_and_reject_duplicates(self) -> None:
        modules = [
            "tests/scripts/test_validation_utils.py",
            "tests/test_hookless_architecture.py",
            "tests/scripts/test_run_ci_tests.py",
            "tests/scripts/test_validate_control_skills.py",
        ]
        first = self.runner._stable_shards(modules, 2)
        second = self.runner._stable_shards(list(reversed(modules)), 2)
        self.assertEqual(first, second)
        self.assertEqual(set(), set(first[0]) & set(first[1]))
        self.assertEqual(set(modules), set(first[0]) | set(first[1]))
        self.assertEqual(sum(len(shard) for shard in first), len(modules))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.runner._stable_shards(modules + [modules[0]], 2)

    def test_unittest_exec_is_direct_and_replaces_runner_for_exit_passthrough(self) -> None:
        modules = ["tests/scripts/test_run_ci_tests.py"]
        with mock.patch.object(self.runner.os, "chdir") as chdir, mock.patch.object(
            self.runner.os, "execv"
        ) as execv:
            self.runner._exec_unittest(ROOT, self.core, modules)
        chdir.assert_called_once_with(ROOT)
        executable, argv = execv.call_args.args
        self.assertEqual(sys.executable, executable)
        self.assertEqual(
            [sys.executable, "-m", "unittest", *modules],
            argv,
        )

    def test_empty_full_discovery_is_a_harness_failure(self) -> None:
        with self.assertRaisesRegex(self.runner.SelectionError, "empty"):
            self.runner._discover_modules(Path("/definitely/missing"), "tests", "test*.py")

    def test_current_pr_selects_all_changed_tests_without_fallback(self) -> None:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        ).stdout.strip()
        result = self.runner.select(ROOT, self.core, CURRENT_PR_BASE, head)
        self.assertFalse(result["fallback"], result)
        decisions = {row["path"]: row for row in result["changed_paths"]}
        self.assertEqual(
            set(), CURRENT_PR_CHANGED_TEST_PATHS - set(decisions), decisions
        )
        for path in CURRENT_PR_CHANGED_TEST_PATHS:
            with self.subTest(path=path):
                self.assertTrue(decisions[path]["selected"], decisions[path])
        full_modules = set(self.runner._discover_full_suite_modules(ROOT, self.core))
        self.assertLess(set(result["selected_test_modules"]), full_modules)
        shard_union = set().union(*map(set, result["shards"]))
        self.assertEqual(set(result["selected_test_modules"]), shard_union)


class CiWorkflowProjectionTests(unittest.TestCase):
    def test_ci_projects_canonical_gates_and_two_affected_test_shards(self) -> None:
        text = CI_WORKFLOW.read_text(encoding="utf-8")
        for command in (
            "python3 scripts/eval-core-principles.py --gate authoring",
            "python3 scripts/validate-examples.py",
            "python3 scripts/generate-examples-showcase.py --out docs/SHOWCASE.md --check",
            "python3 scripts/generate-marketplace-catalog.py --profile recommended --out docs/MARKETPLACE_CATALOG.md --check",
            "python3 scripts/validate-marketplace-index.py --profile recommended",
            "python3 scripts/validate-marketplace-index.py --profile full",
            "python3 scripts/validate-marketplace-index.py --profile dev",
            "python3 scripts/validate-productization-assets.py",
            "python3 scripts/validate-open-source-readiness.py --require-pass",
            "python3 scripts/validate-codegen-benchmarks.py",
            "python3 scripts/run-codegen-benchmarks.py --limit 3",
            "python3 scripts/quickstart.py --agent codex --scope user --dry-run",
            "python3 scripts/quickstart.py --agent claude --scope project --target /tmp/changeforge-quickstart-claude --dry-run",
            "python3 scripts/quickstart.py --agent copilot --scope project --target /tmp/changeforge-quickstart-copilot --dry-run",
            "python3 scripts/quickstart.py --agent openai-api --dry-run",
        ):
            with self.subTest(command=command):
                self.assertEqual(1, text.count(command))
        self.assertFalse(
            "python3 -m unittest discover -s tests" in text,
            "CI still runs unconditional full unittest discovery",
        )
        self.assertEqual(2, text.count("fetch-depth: 0"))
        self.assertTrue("shard: [0, 1]" in text, "missing two-shard matrix")
        self.assertTrue(
            "github.event.pull_request.base.sha" in text,
            "missing pull-request base revision",
        )
        self.assertTrue("github.event.before" in text, "missing push base revision")
        self.assertTrue("github.sha" in text, "missing checked-out head revision")
        self.assertTrue(
            "python3 scripts/run-ci-tests.py run" in text,
            "missing affected-test runner command",
        )
        self.assertEqual(2, text.count("git diff --exit-code"))

    def test_formal_release_workflow_is_unchanged(self) -> None:
        self.assertEqual(
            FORMAL_WORKFLOW_SHA256,
            hashlib.sha256(FORMAL_WORKFLOW.read_bytes()).hexdigest(),
        )

    def test_runner_has_no_second_mapping_manifest(self) -> None:
        self.assertTrue(RUNNER_PATH.is_file(), "missing bounded CI test selector runner")
        source = RUNNER_PATH.read_text(encoding="utf-8")
        self.assertIn("src/control-model/core-contracts.json", source)
        self.assertNotIn("yaml", source.casefold())
        self.assertNotIn("shell=True", source)


if __name__ == "__main__":
    unittest.main()
