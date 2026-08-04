from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "eval-context-control-plane.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("eval_context_control_plane", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _source_report(*, status: str = "pass", evidence_scope: str = "deterministic-fixtures") -> dict:
    return {
        "schema_version": 2,
        "fixture_schema_version": 2,
        "status": status,
        "evidence_scope": evidence_scope,
        "fixture_count": 3,
        "limitations": ["Deterministic fixture limitation."],
        "cases": [
            {
                "id": "isolated-write-parallel-contract",
                "metrics": {
                    "preparation_loop_detected": False,
                    "parallel_write_conflict": False,
                    "loaded_skill_count": 2,
                    "loaded_layer3_reference_count": 0,
                    "required_progress_for_multi_agent": True,
                    "required_multi_agent_progress_satisfied": True,
                    "conditional_isolated_write_contract": True,
                    "shared_workspace_writes_serial": False,
                    "utility_workspace_diff_unchanged": False,
                },
            },
            {
                "id": "shared-workspace-serial-write",
                "fixture_group": "scheduling",
                "metrics": {
                    "preparation_loop_detected": False,
                    "parallel_write_conflict": False,
                    "loaded_skill_count": 2,
                    "loaded_layer3_reference_count": 0,
                    "required_progress_for_multi_agent": True,
                    "required_multi_agent_progress_satisfied": True,
                    "conditional_isolated_write_contract": False,
                    "shared_workspace_writes_serial": True,
                    "utility_workspace_diff_unchanged": False,
                },
            },
            {
                "id": "validation-task-no-edit",
                "fixture_group": "utility",
                "metrics": {
                    "preparation_loop_detected": False,
                    "parallel_write_conflict": False,
                    "loaded_skill_count": 0,
                    "loaded_layer3_reference_count": 0,
                    "required_progress_for_multi_agent": False,
                    "required_multi_agent_progress_satisfied": True,
                    "conditional_isolated_write_contract": False,
                    "shared_workspace_writes_serial": False,
                    "utility_workspace_diff_unchanged": True,
                },
            },
        ],
    }


def _rendered_report(*, status: str = "pass") -> dict:
    return {
        "schema_version": 2,
        "fixture_schema_version": 2,
        "status": status,
        "evidence_scope": "deterministic-rendered-artifacts",
        "tokenizer": "o200k_base",
        "fixture_count": 3,
        "build_profiles": ["recommended", "full", "dev"],
        "hosts": ["codex", "claude", "copilot"],
        "limitations": ["Deterministic rendered artifact limitation."],
        "cases": [
            {"id": "isolated-write-parallel-contract"},
            {"id": "shared-workspace-serial-write"},
            {"id": "validation-task-no-edit"},
        ],
        "aggregate": {"max_main": {"tokens": 1000}},
        "errors": [],
    }


class ContextControlPlaneEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def _invoke(
        self,
        source: str | None,
        rendered: str | None = None,
        control_prompt: str | None = None,
    ) -> tuple[int, str, dict | None, bool]:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source_path = root / "hookless-control-plane-eval.json"
            rendered_path = root / "rendered-context-budget.json"
            report_json = root / "context-control-plane-eval.json"
            report_md = root / "context-control-plane-eval.md"
            if source is not None:
                source_path.write_text(source, encoding="utf-8")
            if rendered is None:
                rendered = json.dumps(_rendered_report())
            rendered_path.write_text(rendered, encoding="utf-8")
            prompt_path = self.module.CONTROL_PROMPT
            if control_prompt is not None:
                prompt_path = root / "main-control-agent.md"
                prompt_path.write_text(control_prompt, encoding="utf-8")
            stderr = io.StringIO()
            with (
                mock.patch.object(self.module, "SOURCE_REPORT", source_path),
                mock.patch.object(self.module, "RENDERED_CONTEXT_REPORT", rendered_path),
                mock.patch.object(self.module, "REPORT_JSON", report_json),
                mock.patch.object(self.module, "REPORT_MD", report_md),
                mock.patch.object(self.module, "CONTROL_PROMPT", prompt_path),
                mock.patch.object(
                    subprocess,
                    "run",
                    side_effect=AssertionError("context evaluation must not launch another evaluator"),
                ),
                contextlib.redirect_stderr(stderr),
            ):
                result = self.module.main()
            report = json.loads(report_json.read_text(encoding="utf-8")) if report_json.exists() else None
            return result, stderr.getvalue(), report, report_md.exists()

    def test_consumes_existing_lightweight_report_without_subprocess(self) -> None:
        result, stderr, report, markdown_exists = self._invoke(json.dumps(_source_report()))

        self.assertEqual(0, result, stderr)
        self.assertEqual("pass", report["status"])
        self.assertEqual("deterministic-fixtures", report["evidence_scope"])
        self.assertTrue(markdown_exists)

    def test_missing_source_report_fails_without_writing_output(self) -> None:
        result, stderr, report, markdown_exists = self._invoke(None)

        self.assertEqual(1, result)
        self.assertIn("missing prerequisite report", stderr)
        self.assertIn("run scripts/eval-agent-lightweight.py first", stderr)
        self.assertIsNone(report)
        self.assertFalse(markdown_exists)

    def test_malformed_source_report_fails_without_writing_output(self) -> None:
        result, stderr, report, markdown_exists = self._invoke("not-json")

        self.assertEqual(1, result)
        self.assertIn("malformed prerequisite report", stderr)
        self.assertIn("invalid JSON", stderr)
        self.assertIsNone(report)
        self.assertFalse(markdown_exists)

    def test_non_passing_source_report_is_rejected(self) -> None:
        result, stderr, report, markdown_exists = self._invoke(
            json.dumps(_source_report(status="fail"))
        )

        self.assertEqual(1, result)
        self.assertIn("prerequisite report did not pass", stderr)
        self.assertIsNone(report)
        self.assertFalse(markdown_exists)

    def test_wrong_evidence_scope_is_rejected(self) -> None:
        result, stderr, report, markdown_exists = self._invoke(
            json.dumps(_source_report(evidence_scope="live-host"))
        )

        self.assertEqual(1, result)
        self.assertIn("wrong evidence_scope", stderr)
        self.assertIsNone(report)
        self.assertFalse(markdown_exists)

    def test_non_passing_rendered_context_report_is_rejected(self) -> None:
        result, stderr, report, markdown_exists = self._invoke(
            json.dumps(_source_report()),
            json.dumps(_rendered_report(status="fail")),
        )

        self.assertEqual(1, result)
        self.assertIn("rendered-context report did not pass", stderr)
        self.assertIsNone(report)
        self.assertFalse(markdown_exists)

    def test_stale_report_or_fixture_schema_is_rejected(self) -> None:
        stale_source = _source_report()
        stale_source["schema_version"] = 1
        result, stderr, report, markdown_exists = self._invoke(
            json.dumps(stale_source)
        )
        self.assertEqual(1, result)
        self.assertIn("schema_version 2", stderr)
        self.assertIsNone(report)
        self.assertFalse(markdown_exists)

        stale_rendered = _rendered_report()
        stale_rendered["fixture_schema_version"] = 1
        result, stderr, report, markdown_exists = self._invoke(
            json.dumps(_source_report()),
            json.dumps(stale_rendered),
        )
        self.assertEqual(1, result)
        self.assertIn("fixture_schema_version", stderr)
        self.assertIsNone(report)
        self.assertFalse(markdown_exists)

    def test_current_parallelism_projection_is_required_from_core_contract(self) -> None:
        original_prompt = self.module.CONTROL_PROMPT.read_text(encoding="utf-8")
        prompt = original_prompt.replace(
            "parallel read-only tasks",
            "concurrent read-only tasks",
            1,
        )
        self.assertNotEqual(original_prompt, prompt)

        result, stderr, report, markdown_exists = self._invoke(
            json.dumps(_source_report()),
            control_prompt=prompt,
        )

        self.assertEqual(1, result)
        expected_error = "control prompt does not declare current read-only parallelism"
        self.assertEqual(
            f"eval-context-control-plane: ERROR: {expected_error}\n",
            stderr,
        )
        self.assertEqual("fail", report["status"])
        self.assertEqual([expected_error], report["errors"])
        self.assertTrue(markdown_exists)

    def test_current_parallelism_projection_is_case_insensitive(self) -> None:
        original_prompt = self.module.CONTROL_PROMPT.read_text(encoding="utf-8")
        prompt = original_prompt.replace(
            "parallel read-only tasks",
            "PARALLEL READ-ONLY TASKS",
            1,
        )
        self.assertNotEqual(original_prompt, prompt)

        result, stderr, report, markdown_exists = self._invoke(
            json.dumps(_source_report()),
            control_prompt=prompt,
        )

        self.assertEqual(0, result, stderr)
        self.assertEqual("pass", report["status"])
        self.assertTrue(report["checks"]["current_read_only_parallelism_declared"])
        self.assertTrue(markdown_exists)


if __name__ == "__main__":
    unittest.main()
