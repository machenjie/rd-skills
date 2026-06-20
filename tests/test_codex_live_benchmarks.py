from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _load_script(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CodexLiveBenchmarkTests(unittest.TestCase):
    def test_live_execution_allowed_requires_env_or_cli_gate(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_allowed", "scripts/run-codex-live-benchmarks.py")
        args = SimpleNamespace(allow_live_codex=False)
        self.assertFalse(runner.live_execution_allowed(args, {}))
        self.assertTrue(runner.live_execution_allowed(args, {"CHANGEFORGE_ENABLE_CODEX_LIVE_BENCHMARK": "1"}))
        self.assertFalse(runner.live_execution_allowed(args, {"CHANGEFORGE_ENABLE_CODEX_LIVE_BENCHMARK": "true"}))
        self.assertTrue(runner.live_execution_allowed(SimpleNamespace(allow_live_codex=True), {}))

    def test_dry_run_has_priority_and_does_not_spawn_codex(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_dry_run", "scripts/run-codex-live-benchmarks.py")
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "dry-run"
            with patch.dict("os.environ", {"CHANGEFORGE_ENABLE_CODEX_LIVE_BENCHMARK": "1"}):
                with patch.object(runner.subprocess, "run") as subprocess_run:
                    result = runner.main(
                        [
                            "--benchmark",
                            "devex/helper-reuse-search",
                            "--dry-run",
                            "--out",
                            str(out_dir),
                        ]
                    )
            self.assertEqual(result, 0)
            subprocess_run.assert_not_called()
            manifest = json.loads((out_dir / "run-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "skipped_not_opted_in")
            self.assertEqual(manifest["codex_invocations"], [])
            self.assertFalse(manifest["live_execution_effective"])

    def test_unauthorized_codex_exec_raises_before_subprocess(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_unauthorized", "scripts/run-codex-live-benchmarks.py")
        args = SimpleNamespace(allow_live_codex=False, dry_run=False, timeout_seconds=1)
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            with patch.object(runner.subprocess, "run") as subprocess_run:
                with self.assertRaisesRegex(RuntimeError, runner.REFUSAL_MESSAGE):
                    runner.run_codex_exec(
                        ["codex", "exec", "--json", "-"],
                        prompt="task",
                        cwd=tmp_path,
                        events_path=tmp_path / "events.jsonl",
                        stderr_path=tmp_path / "stderr.log",
                        args=args,
                        env={},
                    )
            subprocess_run.assert_not_called()

    def test_danger_full_access_has_independent_gate(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_danger", "scripts/run-codex-live-benchmarks.py")
        args = SimpleNamespace(allow_danger_full_access=False)
        self.assertFalse(runner.danger_full_access_allowed(args, {}))
        self.assertTrue(runner.danger_full_access_allowed(args, {"CHANGEFORGE_ALLOW_DANGER_FULL_ACCESS": "1"}))
        self.assertTrue(runner.danger_full_access_allowed(SimpleNamespace(allow_danger_full_access=True), {}))

    def test_current_codex_home_has_independent_gate(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_current_home_gate", "scripts/run-codex-live-benchmarks.py")
        args = SimpleNamespace(allow_current_codex_home=False)
        self.assertFalse(runner.current_codex_home_allowed(args, {}))
        self.assertTrue(runner.current_codex_home_allowed(args, {"CHANGEFORGE_ALLOW_CURRENT_CODEX_HOME": "1"}))
        self.assertFalse(runner.current_codex_home_allowed(args, {"CHANGEFORGE_ALLOW_CURRENT_CODEX_HOME": "true"}))
        self.assertTrue(runner.current_codex_home_allowed(SimpleNamespace(allow_current_codex_home=True), {}))

    def test_current_codex_home_mode_requires_second_gate_for_live_runs(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_current_home_required", "scripts/run-codex-live-benchmarks.py")
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "current-home"
            with patch.dict("os.environ", {"CHANGEFORGE_ENABLE_CODEX_LIVE_BENCHMARK": "1"}):
                with patch.object(runner, "run_live") as run_live:
                    result = runner.main(
                        [
                            "--benchmark",
                            "devex/helper-reuse-search",
                            "--codex-home-mode",
                            "current",
                            "--out",
                            str(out_dir),
                        ]
                    )
        self.assertEqual(result, 2)
        run_live.assert_not_called()

    def test_isolated_codex_home_is_absolute(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_home", "scripts/run-codex-live-benchmarks.py")
        case = SimpleNamespace(id="devex/helper-reuse-search")
        with tempfile.TemporaryDirectory() as tmp:
            env = runner._isolated_env(Path(tmp).resolve(), case, "baseline", 1)
        self.assertTrue(Path(env["HOME"]).is_absolute())
        self.assertTrue(Path(env["CODEX_HOME"]).is_absolute())

    def test_current_codex_home_mode_preserves_env_but_redacts_metadata(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_current_home_metadata", "scripts/run-codex-live-benchmarks.py")
        args = SimpleNamespace(codex_home_mode="current")
        case = SimpleNamespace(id="devex/helper-reuse-search")
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(
                "os.environ",
                {
                    "HOME": "/tmp/raw-user-home",
                    "CODEX_HOME": "/tmp/raw-codex-home",
                    "CODEX_API_KEY": "sk-raw-codex-secret",
                    "OPENAI_API_KEY": "sk-raw-openai-secret",
                },
                clear=True,
            ):
                env, metadata = runner._codex_env(args, Path(tmp).resolve(), case, "baseline", 1)

        self.assertEqual(env["HOME"], "/tmp/raw-user-home")
        self.assertEqual(env["CODEX_HOME"], "/tmp/raw-codex-home")
        encoded = json.dumps(metadata)
        self.assertNotIn("/tmp/raw-user-home", encoded)
        self.assertNotIn("/tmp/raw-codex-home", encoded)
        self.assertNotIn("sk-raw", encoded)
        self.assertEqual(metadata["HOME"], "<inherited-redacted>")
        self.assertEqual(metadata["CODEX_HOME"], "<inherited-redacted>")
        self.assertEqual(metadata["CODEX_API_KEY"], "<inherited-redacted>")
        self.assertEqual(metadata["OPENAI_API_KEY"], "<inherited-redacted>")

    def test_parser_counts_usage_without_raw_command_or_message(self) -> None:
        parser = _load_script("parse_codex_jsonl_test", "scripts/parse-codex-jsonl.py")
        with tempfile.TemporaryDirectory() as tmp:
            events = Path(tmp) / "events.jsonl"
            events.write_text(
                "\n".join(
                    [
                        json.dumps({"type": "turn.started"}),
                        json.dumps(
                            {
                                "type": "tool_call",
                                "command": "echo SHOULD_NOT_LEAK",
                                "usage": {
                                    "input_tokens": 10,
                                    "cached_input_tokens": 2,
                                    "output_tokens": 4,
                                    "reasoning_output_tokens": 1,
                                },
                            }
                        ),
                        json.dumps({"type": "message", "role": "assistant", "message": "SHOULD_NOT_LEAK"}),
                        "{bad json",
                    ]
                ),
                encoding="utf-8",
            )
            metrics = parser.parse_events(events)
        self.assertEqual(metrics["event_count"], 3)
        self.assertEqual(metrics["turn_started"], 1)
        self.assertEqual(metrics["command_execution_count"], 1)
        self.assertEqual(metrics["usage"]["input_tokens"], 10)
        encoded = json.dumps(metrics)
        self.assertNotIn("SHOULD_NOT_LEAK", encoded)
        self.assertEqual(len(metrics["parse_errors"]), 1)

    def test_validator_rejects_secret_patterns(self) -> None:
        validator = _load_script("validate_codex_live_reports_secret", "scripts/validate-codex-live-benchmark-reports.py")
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "run-manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "generated_by": "scripts/run-codex-live-benchmarks.py",
                        "run_id": "dry-run",
                        "status": "skipped_not_opted_in",
                        "dry_run": True,
                        "live_execution_allowed": False,
                        "live_execution_effective": False,
                        "cases": ["devex/helper-reuse-search"],
                        "variants": ["baseline"],
                        "runs_per_variant": 1,
                        "sandbox": "workspace-write",
                        "limitations": ["dry-run"],
                    }
                ),
                encoding="utf-8",
            )
            fake_secret = "CODEX" + "_API" + "_KEY=" + "sk-" + "ThisShouldFail123"
            leak_dir = run_dir / "cases" / "devex__helper-reuse-search" / "baseline" / "run-01"
            leak_dir.mkdir(parents=True)
            (leak_dir / "leak.txt").write_text(fake_secret, encoding="utf-8")
            errors = validator.validate_run_dir(run_dir)
        self.assertTrue(any("forbidden secret pattern" in error for error in errors))

    def test_skipped_summary_cannot_be_published(self) -> None:
        summary_module = _load_script("generate_codex_live_summary_publish", "scripts/generate-codex-live-summary.py")
        payload = {
            "schema_version": 1,
            "generated_by": "scripts/generate-codex-live-summary.py",
            "status": "skipped_not_opted_in",
            "evidence_level": "local_codex_cli_live_benchmark",
            "run_id": "dry-run",
            "case_count": 0,
            "variant_count": 0,
            "pass_rate": "not_collected",
            "security_pass_rate": "not_collected",
            "average_usage": {},
            "limitations": ["dry-run"],
        }
        with self.assertRaisesRegex(ValueError, "cannot be published"):
            summary_module.publish_summary(payload, "# skipped\n")

    def test_grader_marks_cases_without_assertions_not_collected(self) -> None:
        grader = _load_script("grade_codex_live_no_assertions", "scripts/grade-codex-live-benchmarks.py")
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "candidate"
            out_dir = Path(tmp) / "grading"
            candidate.mkdir()
            result = grader.grade_candidate("devex/helper-reuse-search", candidate, out_dir)
            self.assertTrue((out_dir / "grading-result.json").is_file())
        self.assertEqual(result["grading_status"], "not_collected")
        self.assertFalse(result["all_passed"])

    def test_bad_registry_fails_validation(self) -> None:
        helper = _load_script("codex_live_helper_bad_registry", "scripts/codex_live_benchmark_lib.py")
        data = {
            "schema_version": 1,
            "kind": "changeforge.codex_live_benchmark_cases",
            "cases": [
                {
                    "id": "devex/not-real",
                    "category": "devex",
                    "codegen_case": "not-real",
                    "enabled": True,
                    "variants": ["baseline"],
                    "task_prompt": "evals/codegen/devex/not-real/prompt.md",
                    "starter_repo": "evals/codegen/devex/not-real/starter-repo",
                    "grading_benchmark": "devex/not-real",
                }
            ],
        }
        errors = helper.validate_case_registry(data, ROOT)
        self.assertTrue(any("not in codegen benchmark manifest" in error for error in errors))

    def test_published_summary_fields_feed_scorecard_and_public_summary(self) -> None:
        scorecard = _load_script("generate_professional_scorecard_codex_live", "scripts/generate-professional-scorecard.py")
        public = _load_script("generate_public_summary_codex_live", "scripts/generate-public-benchmark-summary.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "reports").mkdir()
            (root / "reports" / "codex-live-benchmark-summary.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "generated_by": "scripts/generate-codex-live-summary.py",
                        "status": "collected",
                        "evidence_level": "local_codex_cli_live_benchmark",
                        "run_id": "local-test",
                        "case_count": 1,
                        "variant_count": 2,
                        "pass_rate": 1.0,
                        "security_pass_rate": 1.0,
                        "average_usage": {"input_tokens": 10},
                        "limitations": ["local smoke"],
                    }
                ),
                encoding="utf-8",
            )
            status, detail = scorecard.codex_live_benchmark_status(root)
            item = public._codex_live_benchmark_item(root)
        self.assertEqual(status, "pass")
        self.assertIn("local-test", detail)
        self.assertEqual(item.status, "pass")
        self.assertEqual(item.evidence_level, "local_codex_cli_live_benchmark")


if __name__ == "__main__":
    unittest.main()
