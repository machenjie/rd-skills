from __future__ import annotations

import contextlib
import hashlib
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


def _integration_evidence_summary() -> dict:
    summary = {
        "schema_version": 1,
        "utility_fixture_count": 2,
        "evidence_continuation_fixture_count": 8,
        "route_frozen": True,
        "logical_request_max": 1,
        "host_attempt_max": 2,
        "observation_max": 1,
        "copilot_trace_sha256": "a" * 64,
        "live_host": False,
    }
    summary["canonical_sha256"] = hashlib.sha256(
        json.dumps(
            summary,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return summary


def _rendered_report(*, status: str = "pass") -> dict:
    return {
        "schema_version": 2,
        "fixture_schema_version": 2,
        "status": status,
        "evidence_scope": "deterministic-rendered-artifacts",
        "tokenizer": "o200k_base",
        "fixture_count": 3,
        "runtime": "recommended",
        "hosts": ["codex", "claude", "copilot"],
        "limitations": ["Deterministic rendered artifact limitation."],
        "cases": [
            {"id": "isolated-write-parallel-contract"},
            {"id": "shared-workspace-serial-write"},
            {"id": "validation-task-no-edit", "fixture_group": "utility"},
        ],
        "aggregate": {"max_main": {"tokens": 1000}},
        "transferred_context": {
            "source_scope": {
                "trajectory_fixture": "evals/agent-light-trajectories/cases.yaml",
                "lightweight_long_task_selector": (
                    "reports/hookless-control-plane-eval.json"
                    "#/cases/*/metrics/required_progress_for_multi_agent"
                ),
            },
            "semantic_baseline": {
                "source": "reports/hookless-control-plane-eval.json#/orchestration_fixtures",
                "retained_semantic_equality": True,
            },
            "measurement_kind": "candidate-subject-only",
            "gross_tokens": 10,
            "non_compressible_tokens": 10,
            "compressible_tokens": 0,
            "compressible_ratio": 0.0,
            "measured_case_count": 2,
            "long_task_selector_join_count": 2,
            "long_task_rows": [
                {
                    "id": "isolated-write-parallel-contract",
                    "required_progress_for_multi_agent": True,
                    "gross_tokens": 10,
                    "non_compressible_tokens": 10,
                    "compressible_tokens": 0,
                    "compressible_ratio": 0.0,
                },
                {
                    "id": "shared-workspace-serial-write",
                    "required_progress_for_multi_agent": True,
                    "gross_tokens": 10,
                    "non_compressible_tokens": 10,
                    "compressible_tokens": 0,
                    "compressible_ratio": 0.0,
                },
            ],
            "proof_limits": ["Deterministic transfer projection only."],
        },
        "integration_evidence_summary": _integration_evidence_summary(),
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
        *,
        write_rendered: bool = True,
        dependencies: list[str] | None = None,
    ) -> tuple[int, str, dict | None, bool]:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source_path = root / "hookless-control-plane-eval.json"
            rendered_path = root / "rendered-context-budget.json"
            report_json = root / "context-control-plane-eval.json"
            report_md = root / "context-control-plane-eval.md"
            core_contracts = root / "core-contracts.json"
            if source is not None:
                source_path.write_text(source, encoding="utf-8")
            if rendered is None:
                rendered = json.dumps(_rendered_report())
            if write_rendered:
                rendered_path.write_text(rendered, encoding="utf-8")
            core_contracts.write_text(
                json.dumps(
                    {
                        "principle_acceptance_contract": {
                            "producers": [
                                {
                                    "id": "eval-context-control",
                                    "depends_on": dependencies
                                    if dependencies is not None
                                    else ["eval-agent-lightweight", "eval-rendered-context"],
                                }
                            ]
                        }
                    }
                ),
                encoding="utf-8",
            )
            stderr = io.StringIO()
            with (
                mock.patch.object(self.module, "SOURCE_REPORT", source_path),
                mock.patch.object(self.module, "RENDERED_CONTEXT_REPORT", rendered_path),
                mock.patch.object(self.module, "REPORT_JSON", report_json),
                mock.patch.object(self.module, "REPORT_MD", report_md),
                mock.patch.object(self.module, "CORE_CONTRACTS", core_contracts),
                mock.patch.object(
                    subprocess,
                    "run",
                    side_effect=AssertionError("context evaluation must not launch another evaluator"),
                ),
                contextlib.redirect_stderr(stderr),
            ):
                result = self.module.main([])
            report = json.loads(report_json.read_text(encoding="utf-8")) if report_json.exists() else None
            return result, stderr.getvalue(), report, report_md.exists()

    def test_consumes_existing_lightweight_report_without_subprocess(self) -> None:
        result, stderr, report, markdown_exists = self._invoke(json.dumps(_source_report()))

        self.assertEqual(0, result, stderr)
        self.assertEqual("pass", report["status"])
        self.assertEqual("deterministic-fixtures", report["evidence_scope"])
        self.assertEqual(
            "candidate-subject-only",
            report["transferred_context_summary"]["measurement_kind"],
        )
        self.assertNotIn("context_compaction_decision", report)
        self.assertEqual("pass", report["status"])
        self.assertFalse(markdown_exists)

    def test_copies_candidate_producer_summary_without_recomputing(self) -> None:
        rendered = _rendered_report()
        transfer = rendered["transferred_context"]
        producer_semantic = {
            **transfer["semantic_baseline"],
            "producer_owned_marker": "copied-not-recomputed",
        }
        transfer["semantic_baseline"] = producer_semantic

        result, stderr, report, markdown_exists = self._invoke(
            json.dumps(_source_report()),
            json.dumps(rendered),
        )

        self.assertEqual(0, result, stderr)
        self.assertEqual(
            producer_semantic,
            report["transferred_context_summary"]["semantic_baseline"],
        )
        self.assertNotIn("realized_reduction_ratio", report["transferred_context_summary"])
        self.assertFalse(markdown_exists)

    def test_consumes_integration_evidence_summary_and_digest_without_reducing_trace(self) -> None:
        rendered = _rendered_report()
        producer_summary = rendered["integration_evidence_summary"]
        result, stderr, report, _markdown_exists = self._invoke(
            json.dumps(_source_report()),
            json.dumps(rendered),
        )
        self.assertEqual(0, result, stderr)
        self.assertEqual(producer_summary, report["integration_evidence_summary"])

        rendered["integration_evidence_summary"]["observation_max"] = 2
        result, stderr, report, _markdown_exists = self._invoke(
            json.dumps(_source_report()),
            json.dumps(rendered),
        )
        self.assertEqual(1, result)
        self.assertIn("summary digest mismatch", stderr)
        self.assertIsNone(report)

    def test_rendered_context_rejects_unproven_long_task_join(self) -> None:
        rendered = _rendered_report()
        rendered["transferred_context"]["long_task_rows"] = []

        result, stderr, report, markdown_exists = self._invoke(
            json.dumps(_source_report()),
            json.dumps(rendered),
        )

        self.assertEqual(1, result)
        self.assertIn("long-task rows do not match", stderr)
        self.assertIsNone(report)
        self.assertFalse(markdown_exists)

    def test_missing_source_report_fails_without_writing_output(self) -> None:
        result, stderr, report, markdown_exists = self._invoke(None)

        self.assertEqual(1, result)
        self.assertIn("missing prerequisite report", stderr)
        self.assertIn("run scripts/eval-agent-lightweight.py first", stderr)
        self.assertIsNone(report)
        self.assertFalse(markdown_exists)

    def test_missing_rendered_report_fails_without_writing_output(self) -> None:
        result, stderr, report, markdown_exists = self._invoke(
            json.dumps(_source_report()),
            write_rendered=False,
        )

        self.assertEqual(1, result)
        self.assertIn("missing rendered-context report", stderr)
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

    def test_malformed_rendered_context_report_is_rejected(self) -> None:
        result, stderr, report, markdown_exists = self._invoke(
            json.dumps(_source_report()),
            "not-json",
        )

        self.assertEqual(1, result)
        self.assertIn("malformed rendered-context report", stderr)
        self.assertIsNone(report)
        self.assertFalse(markdown_exists)

    def test_fabricated_realized_reduction_is_rejected(self) -> None:
        rendered = _rendered_report()
        rendered["transferred_context"]["realized_reduction_ratio"] = 0.5

        result, stderr, report, markdown_exists = self._invoke(
            json.dumps(_source_report()),
            json.dumps(rendered),
        )

        self.assertEqual(1, result)
        self.assertIn("must not claim a realized reduction", stderr)
        self.assertIsNone(report)
        self.assertFalse(markdown_exists)

    def test_declared_producer_dependency_is_required(self) -> None:
        result, stderr, report, markdown_exists = self._invoke(
            json.dumps(_source_report()),
            dependencies=["eval-rendered-context"],
        )

        self.assertEqual(1, result)
        self.assertIn("Core eval-context-control dependency", stderr)
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

if __name__ == "__main__":
    unittest.main()
