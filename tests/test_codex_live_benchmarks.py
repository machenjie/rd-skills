from __future__ import annotations

import importlib.util
import json
import subprocess
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


def _variant_payload(**overrides: object) -> dict[str, object]:
    usage = {
        "input_tokens": 10,
        "cached_input_tokens": 0,
        "output_tokens": 5,
        "reasoning_output_tokens": 0,
    }
    metrics = {
        "event_count": 1,
        "command_execution_count": 1,
        "file_change_count": 1,
        "plan_update_count": 0,
        "error_count": 0,
    }
    payload: dict[str, object] = {
        "run_count": 1,
        "case_count": 1,
        "result_count": 1,
        "artifact_status_counts": {"collected": 1},
        "grading_status_counts": {"passed": 1},
        "failure_categories": {"none": 1},
        "benchmark_eligible_result_count": 1,
        "benchmark_passed_result_count": 1,
        "pass_rate": 1.0,
        "pass_rate_ci_note": "descriptive only; small sample",
        "security_pass_rate": 1.0,
        "telemetry_only_result_count": 0,
        "not_collected_grading_count": 0,
        "contaminated_result_count": 0,
        "average_usage": usage,
        "median_usage": usage,
        "min_usage": usage,
        "max_usage": usage,
        "average_metrics": metrics,
        "median_metrics": metrics,
        "min_metrics": metrics,
        "max_metrics": metrics,
        "average_event_count": 1,
        "average_file_change_count": 1,
        "average_command_execution_count": 1,
        "delta_vs_baseline_clean": {},
    }
    payload.update(overrides)
    return payload


def _scope_detail(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "strong_claim_ready": False,
        "required_benchmark_mode": "ablation",
        "required_assertion_case_count": 5,
        "required_runs_per_variant": 3,
        "required_variants": ["baseline_clean", "skills_only_clean", "skills_with_hooks_clean"],
        "observed_benchmark_mode": "clean-paired",
        "observed_assertion_case_count": 1,
        "observed_variant_case_counts": {
            "baseline_clean": 1,
            "skills_only_clean": 0,
            "skills_with_hooks_clean": 1,
        },
        "observed_min_runs_per_required_variant": 0,
        "reason": "strict clean-paired evidence is smoke-scale until ablation covers the required cases and runs",
    }
    payload.update(overrides)
    return payload


def _strict_summary_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": 2,
        "generated_by": "scripts/generate-codex-live-summary.py",
        "status": "collected",
        "evidence_level": "local_codex_cli_live_benchmark",
        "evidence_scope": "smoke",
        "evidence_scope_detail": _scope_detail(),
        "benchmark_mode": "clean-paired",
        "codex_home_policy": "auth_borrowed_clean",
        "auth_policy": "borrow-current",
        "codex_environment_policy": "auth_borrowed_clean",
        "strict_benchmark_eligible": True,
        "publishable_for_strict_benchmark": True,
        "run_id": "local-test",
        "run_dir": "<run-dir>",
        "case_count": 1,
        "assertion_case_count": 1,
        "telemetry_only_case_count": 0,
        "result_count": 2,
        "benchmark_eligible_result_count": 2,
        "benchmark_passed_result_count": 2,
        "not_collected_grading_count": 0,
        "telemetry_only_result_count": 0,
        "contaminated_result_count": 0,
        "failure_categories": {"none": 2},
        "current_home_result_count": 0,
        "current_home_full_result_count": 0,
        "user_skills_visible": False,
        "user_config_loaded": False,
        "user_rules_loaded": False,
        "ignore_user_config": True,
        "ignore_rules": True,
        "plugins_disabled": True,
        "variants": {
            "baseline_clean": _variant_payload(),
            "skills_with_hooks_clean": _variant_payload(
                delta_vs_baseline_clean={
                    "pass_rate_delta": 0.0,
                    "security_pass_rate_delta": 0.0,
                }
            ),
        },
        "delta": {
            "skills_with_hooks_clean_vs_baseline_clean": {
                "pass_rate_delta": 0.0,
                "security_pass_rate_delta": 0.0,
            }
        },
        "cases": ["security/ssrf-url-allowlist"],
        "cases_summary": {
            "security/ssrf-url-allowlist": {
                "grading_mode": "assertion",
                "variants": {
                    "baseline_clean": {
                        "runs": 1,
                        "benchmark_eligible_result_count": 1,
                        "benchmark_passed_result_count": 1,
                        "pass_rate": 1.0,
                        "failure_categories": {"none": 1},
                    },
                    "skills_with_hooks_clean": {
                        "runs": 1,
                        "benchmark_eligible_result_count": 1,
                        "benchmark_passed_result_count": 1,
                        "pass_rate": 1.0,
                        "failure_categories": {"none": 1},
                    },
                },
            }
        },
        "telemetry": {"event_count": 2, "parse_error_count": 0},
        "limitations": ["strict local evidence"],
    }
    payload.update(overrides)
    return payload


def _environment_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "home": "<temp>",
        "codex_home": "<borrowed-current-auth>",
        "user_home_visible": False,
        "user_skills_visible": False,
        "user_config_loaded": False,
        "user_rules_loaded": False,
        "current_auth_borrowed": True,
        "ignore_user_config": True,
        "ignore_rules": True,
        "plugins_disabled": True,
        "auth_json_copied": False,
        "strict_benchmark_eligible": True,
    }
    payload.update(overrides)
    return payload


def _result_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": 2,
        "generated_by": "scripts/run-codex-live-benchmarks.py",
        "case_id": "security/ssrf-url-allowlist",
        "variant": "baseline_clean",
        "run_index": 1,
        "status": "collected",
        "artifact_status": "collected",
        "grading_status": "passed",
        "benchmark_mode": "clean-paired",
        "codex_home_mode": "isolated",
        "auth_policy": "borrow-current",
        "codex_environment_policy": "auth_borrowed_clean",
        "grading_mode": "assertion",
        "publishable_for_strict": True,
        "benchmark_eligible": True,
        "benchmark_passed": True,
        "failure_category": "none",
        "contamination": {"contaminated": False, "signals": [], "files": []},
        "environment": _environment_payload(),
        "codex_returncode": 0,
        "failure": None,
        "paths": {"final": "<run-dir>/final.md"},
        "grading": {"all_passed": True, "security_checks_passed": True},
        "metrics": {
            "event_count": 1,
            "command_execution_count": 1,
            "file_change_count": 1,
            "plan_update_count": 0,
            "error_count": 0,
            "usage": {
                "input_tokens": 10,
                "cached_input_tokens": 0,
                "output_tokens": 5,
                "reasoning_output_tokens": 0,
            },
            "parse_errors": [],
        },
        "limitations": ["local"],
    }
    payload.update(overrides)
    return payload


class CodexLiveBenchmarkTests(unittest.TestCase):
    def test_default_variants_for_clean_paired_ablation_and_smoke(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_defaults", "scripts/run-codex-live-benchmarks.py")
        self.assertEqual(
            runner.selected_variants(SimpleNamespace(benchmark_mode="clean-paired", variant=None)),
            ["baseline_clean", "skills_with_hooks_clean"],
        )
        self.assertEqual(
            runner.selected_variants(SimpleNamespace(benchmark_mode="ablation", variant=None)),
            ["baseline_clean", "skills_only_clean", "skills_with_hooks_clean"],
        )
        self.assertEqual(
            runner.selected_variants(SimpleNamespace(benchmark_mode="current-home-smoke", variant=None)),
            ["current_home_smoke"],
        )

    def test_default_auth_policy_is_borrow_current_for_strict_and_current_home_for_smoke(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_auth_defaults", "scripts/run-codex-live-benchmarks.py")
        self.assertEqual(runner.resolve_auth_policy(SimpleNamespace(benchmark_mode="clean-paired")), "borrow-current")
        self.assertEqual(runner.resolve_auth_policy(SimpleNamespace(benchmark_mode="ablation")), "borrow-current")
        self.assertEqual(
            runner.resolve_auth_policy(SimpleNamespace(benchmark_mode="current-home-smoke")),
            "current-home-full",
        )

    def test_borrow_current_uses_temp_home_and_redacted_current_auth(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_borrow_env", "scripts/run-codex-live-benchmarks.py")
        args = SimpleNamespace(auth_policy="borrow-current", benchmark_mode="clean-paired")
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            current_codex = Path(tmp) / "current-codex"
            current_codex.mkdir()
            (current_codex / "auth.json").write_text("{}", encoding="utf-8")
            with patch.dict("os.environ", {"HOME": "/Users/raw-home", "CODEX_HOME": str(current_codex)}, clear=True):
                env, metadata = runner.build_codex_environment(args, SimpleNamespace(id="x/y"), "baseline_clean", run_dir)
            borrowed_codex_home = Path(env["CODEX_HOME"])
            self.assertEqual(Path(env["HOME"]).name, "_home")
            self.assertNotEqual(borrowed_codex_home, current_codex)
            self.assertTrue(borrowed_codex_home.name.startswith("codex-live-borrowed-auth-"))
            self.assertTrue((borrowed_codex_home / "auth.json").is_symlink())
            self.assertFalse((borrowed_codex_home / "plugins").exists())
            runner._cleanup_borrowed_codex_home(env)
            self.assertFalse(borrowed_codex_home.exists())
        self.assertEqual(metadata["home"], "<temp>")
        self.assertEqual(metadata["codex_home"], "<borrowed-current-auth>")
        self.assertFalse(metadata["user_skills_visible"])
        self.assertFalse(metadata["user_config_loaded"])
        self.assertFalse(metadata["user_rules_loaded"])
        self.assertTrue(metadata["current_auth_borrowed"])
        self.assertTrue(metadata["ignore_user_config"])
        self.assertTrue(metadata["ignore_rules"])
        self.assertTrue(metadata["plugins_disabled"])

    def test_isolated_api_key_uses_temp_codex_home_and_redacts_secret_metadata(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_isolated_env", "scripts/run-codex-live-benchmarks.py")
        args = SimpleNamespace(auth_policy="isolated-api-key", benchmark_mode="clean-paired", codex_bin="codex", sandbox="workspace-write", model=None)
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            with patch.dict("os.environ", {"CODEX_API_KEY": "sk-raw-secret-value-12345"}, clear=True):
                env, metadata = runner.build_codex_environment(args, SimpleNamespace(id="x/y"), "baseline_clean", run_dir)
                command = runner.codex_command(args, run_dir / "final.md")
                command_metadata = runner._command_metadata(args, command, metadata)
        self.assertEqual(Path(env["HOME"]).name, "_home")
        self.assertEqual(Path(env["CODEX_HOME"]).name, "_codex-home")
        encoded = json.dumps(command_metadata) + json.dumps(metadata)
        self.assertNotIn("sk-raw-secret", encoded)
        self.assertEqual(command_metadata["env"]["CODEX_API_KEY"], "<redacted-if-present>")
        self.assertFalse(metadata["auth_json_copied"])

    def test_strict_codex_command_ignores_user_config_and_rules(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_command_flags", "scripts/run-codex-live-benchmarks.py")
        args = SimpleNamespace(
            auth_policy="borrow-current",
            benchmark_mode="clean-paired",
            codex_bin="codex",
            sandbox="workspace-write",
            model=None,
        )
        command = runner.codex_command(args, Path("/tmp/final.md"))
        self.assertIn("--ignore-user-config", command)
        self.assertIn("--ignore-rules", command)
        self.assertIn("--disable", command)
        self.assertIn("plugins", command)

    def test_current_home_full_is_only_valid_for_smoke_mode(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_current_mode", "scripts/run-codex-live-benchmarks.py")
        errors = runner.validate_mode_args(
            SimpleNamespace(
                benchmark_mode="clean-paired",
                auth_policy="current-home-full",
                codex_home_mode=None,
                publish_summary=False,
                publish_current_home_smoke=False,
            ),
            ["baseline_clean", "skills_with_hooks_clean"],
        )
        self.assertTrue(any("current-home-smoke" in error for error in errors))

    def test_current_home_full_requires_second_gate_for_live_runs(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_current_home_required", "scripts/run-codex-live-benchmarks.py")
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "current-home"
            with patch.dict("os.environ", {"CHANGEFORGE_ENABLE_CODEX_LIVE_BENCHMARK": "1"}):
                with patch.object(runner, "run_live") as run_live:
                    result = runner.main(
                        [
                            "--benchmark",
                            "security/ssrf-url-allowlist",
                            "--benchmark-mode",
                            "current-home-smoke",
                            "--auth-policy",
                            "current-home-full",
                            "--out",
                            str(out_dir),
                        ]
                    )
        self.assertEqual(result, 2)
        run_live.assert_not_called()

    def test_danger_full_access_still_requires_second_gate(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_danger_gate", "scripts/run-codex-live-benchmarks.py")
        result = runner.main(["--sandbox", "danger-full-access", "--dry-run"])
        self.assertEqual(result, 2)

    def test_live_execution_allowed_requires_env_or_cli_gate(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_allowed", "scripts/run-codex-live-benchmarks.py")
        args = SimpleNamespace(allow_live_codex=False)
        self.assertFalse(runner.live_execution_allowed(args, {}))
        self.assertTrue(runner.live_execution_allowed(args, {"CHANGEFORGE_ENABLE_CODEX_LIVE_BENCHMARK": "1"}))
        self.assertFalse(runner.live_execution_allowed(args, {"CHANGEFORGE_ENABLE_CODEX_LIVE_BENCHMARK": "true"}))
        self.assertTrue(runner.live_execution_allowed(SimpleNamespace(allow_live_codex=True), {}))

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
            manifest = json.loads((out_dir / "run-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(result, 0)
        subprocess_run.assert_not_called()
        self.assertEqual(manifest["auth_policy"], "borrow-current")
        self.assertEqual(manifest["codex_environment_policy"], "auth_borrowed_clean")
        self.assertEqual(manifest["variants"], ["baseline_clean", "skills_with_hooks_clean"])
        self.assertFalse(manifest["live_execution_effective"])

    def test_prompt_mapping_keeps_baseline_clean_free_of_changeforge(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_prompts", "scripts/run-codex-live-benchmarks.py")
        with tempfile.TemporaryDirectory() as tmp:
            task = Path(tmp) / "task.md"
            task.write_text("Implement the requested change.\n", encoding="utf-8")
            case = SimpleNamespace(task_prompt=task)
            baseline = runner._render_prompt(case, "baseline_clean")
            skills = runner._render_prompt(case, "skills_only_clean")
        self.assertNotIn("ChangeForge", baseline)
        self.assertNotIn("rd-skills", baseline)
        self.assertIn("ChangeForge", skills)

    def test_installer_variants_split_skills_only_and_hooks(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_install_flags", "scripts/run-codex-live-benchmarks.py")
        args = SimpleNamespace(profile="recommended")
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "candidate"
            candidate.mkdir()
            completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
            with patch.object(runner.subprocess, "run", return_value=completed) as subprocess_run:
                runner._install_changeforge(args, candidate, {}, set(), with_hooks=False)
            install_command = subprocess_run.call_args_list[-1].args[0]
            self.assertNotIn("--with-hooks", install_command)

            with patch.object(runner.subprocess, "run", return_value=completed) as subprocess_run:
                runner._install_changeforge(args, candidate, {}, {"recommended"}, with_hooks=True)
            install_command = subprocess_run.call_args_list[-1].args[0]
            self.assertIn("--with-hooks", install_command)

    def test_install_failure_writes_partial_result(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_install_partial", "scripts/run-codex-live-benchmarks.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            starter = root / "starter"
            starter.mkdir()
            (starter / "README.md").write_text("starter\n", encoding="utf-8")
            task = root / "task.md"
            task.write_text("Do the task.\n", encoding="utf-8")
            out_dir = root / "out"
            args = SimpleNamespace(
                profile="recommended",
                benchmark_mode="clean-paired",
                auth_policy="borrow-current",
                sandbox="workspace-write",
                model=None,
                codex_bin="codex",
                keep_workdirs=True,
            )
            case = SimpleNamespace(
                id="security/ssrf-url-allowlist",
                starter_repo=starter,
                task_prompt=task,
                grading_benchmark="security/ssrf-url-allowlist",
                grading_mode="assertion",
                publishable_for_strict=True,
            )
            with patch.object(runner, "build_codex_environment", return_value=({}, _environment_payload())):
                with patch.object(runner, "_install_changeforge", side_effect=RuntimeError("install failed")):
                    with patch.object(
                        runner,
                        "_grade",
                        return_value={
                            "all_passed": False,
                            "grading_status": "not_collected",
                            "security_checks_passed": False,
                        },
                    ):
                        result = runner._run_one_case(
                            args,
                            out_dir,
                            case,
                            "skills_with_hooks_clean",
                            1,
                            set(),
                        )
            result_path = (
                out_dir
                / "cases"
                / "security__ssrf-url-allowlist"
                / "skills_with_hooks_clean"
                / "run-01"
                / "result.json"
            )
            persisted = json.loads(result_path.read_text(encoding="utf-8"))
        self.assertEqual(result["artifact_status"], "partial")
        self.assertEqual(result["failure_stage"], "install_changeforge")
        self.assertFalse(result["benchmark_eligible"])
        self.assertFalse(result["benchmark_passed"])
        self.assertEqual(result["failure_category"], "install_failed")
        self.assertEqual(persisted["artifact_status"], "partial")
        self.assertEqual(persisted["failure_stage"], "install_changeforge")
        self.assertEqual(persisted["failure_category"], "install_failed")

    def test_generate_summary_failure_raises_for_publish(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_publish_failure", "scripts/run-codex-live-benchmarks.py")
        completed = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="publish failed")
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(runner.subprocess, "run", return_value=completed):
                with self.assertRaisesRegex(RuntimeError, "publish failed"):
                    runner._generate_summary(Path(tmp), publish=True, publish_current_home_smoke=False)

    def test_baseline_contamination_detector_finds_changeforge_route(self) -> None:
        helper = _load_script("codex_live_helper_contamination", "scripts/codex_live_benchmark_lib.py")
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "final.md").write_text("changeforge_route selected_skills", encoding="utf-8")
            result = helper.detect_baseline_contamination(run_dir)
        self.assertTrue(result["contaminated"])
        self.assertIn("changeforge_route", result["signals"])

    def test_baseline_contamination_detector_ignores_codegen_harness_env(self) -> None:
        helper = _load_script("codex_live_helper_harness_env", "scripts/codex_live_benchmark_lib.py")
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "diff.patch").write_text('ROOT="${CHANGEFORGE_CODEGEN_ROOT:-/tmp/root}"\n', encoding="utf-8")
            (run_dir / "final.md").write_text(
                "\n".join(
                    [
                        '`CHANGEFORGE_CODEGEN_CANDIDATE_DIR="$PWD" python3 test_helper.py` passed.',
                        "`CHANGEFORGE_CODEGEN_EVALUATE=1 bash ../test-suite/run.sh` could not run.",
                    ]
                ),
                encoding="utf-8",
            )
            result = helper.detect_baseline_contamination(run_dir)
        self.assertFalse(result["contaminated"])

    def test_report_redaction_handles_macos_temp_paths(self) -> None:
        helper = _load_script("codex_live_helper_report_redaction", "scripts/codex_live_benchmark_lib.py")
        text = "path=/private/var/folders/x/codex-live-borrowed-auth-abc/.tmp/plugin.json"
        self.assertNotIn("/private/var/", helper.redact_report_text(text))

    def test_publish_summary_rejects_current_home_full_and_contamination(self) -> None:
        summary_module = _load_script("generate_codex_live_summary_publish_rules", "scripts/generate-codex-live-summary.py")
        current_home = _strict_summary_payload(
            auth_policy="current-home-full",
            codex_environment_policy="current_home_full",
            current_home_full_result_count=1,
            strict_benchmark_eligible=False,
            user_skills_visible=True,
        )
        with self.assertRaisesRegex(ValueError, "current-home-full|auth_policy|strict_benchmark"):
            summary_module.publish_summary(current_home, "# current-home\n")
        contaminated = _strict_summary_payload(contaminated_result_count=1)
        with self.assertRaisesRegex(ValueError, "contaminated"):
            summary_module.publish_summary(contaminated, "# contaminated\n")

    def test_current_home_smoke_summary_is_not_strict_valid(self) -> None:
        validator = _load_script("validate_codex_live_reports_smoke", "scripts/validate-codex-live-benchmark-reports.py")
        payload = _strict_summary_payload(
            benchmark_mode="current-home-smoke",
            evidence_level="current_home_integration_smoke",
            codex_home_policy="current_home_smoke_only",
            auth_policy="current-home-full",
            codex_environment_policy="current_home_full",
            strict_benchmark_eligible=False,
            publishable_for_strict_benchmark=False,
            current_home_result_count=1,
            current_home_full_result_count=1,
            user_skills_visible=True,
            user_config_loaded=True,
            user_rules_loaded=True,
            ignore_user_config=False,
            ignore_rules=False,
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            errors = validator.validate_summary(path, publishable=True)
        self.assertTrue(any("strict summary" in error or "evidence_level" in error for error in errors))

    def test_validator_rejects_ablation_summary_without_required_deltas(self) -> None:
        validator = _load_script(
            "validate_codex_live_reports_ablation_delta",
            "scripts/validate-codex-live-benchmark-reports.py",
        )
        payload = _strict_summary_payload(
            benchmark_mode="ablation",
            result_count=3,
            benchmark_eligible_result_count=3,
            benchmark_passed_result_count=3,
            failure_categories={"none": 3},
            variants={
                "baseline_clean": _variant_payload(),
                "skills_only_clean": _variant_payload(),
                "skills_with_hooks_clean": _variant_payload(),
            },
            delta={
                "skills_only_clean_vs_baseline_clean": {"pass_rate_delta": 0.0},
                "skills_with_hooks_clean_vs_baseline_clean": {"pass_rate_delta": 0.0},
            },
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            errors = validator.validate_summary(path, publishable=True)
        self.assertTrue(any("delta.skills_with_hooks_clean_vs_skills_only_clean" in error for error in errors))

    def test_validator_rejects_invalid_failure_category_buckets(self) -> None:
        validator = _load_script(
            "validate_codex_live_reports_failure_category",
            "scripts/validate-codex-live-benchmark-reports.py",
        )
        payload = _strict_summary_payload(failure_categories={"mystery_failure": 1})
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            errors = validator.validate_summary(path, publishable=True)
        self.assertTrue(any("invalid failure category mystery_failure" in error for error in errors))

    def test_summary_counts_assertion_cases_only_for_pass_rate_and_groups_delta(self) -> None:
        summary_module = _load_script("generate_codex_live_summary_rates", "scripts/generate-codex-live-summary.py")
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "run-manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "generated_by": "scripts/run-codex-live-benchmarks.py",
                        "run_id": "local-test",
                        "status": "collected",
                        "benchmark_mode": "clean-paired",
                        "dry_run": False,
                        "live_execution_allowed": True,
                        "live_execution_effective": True,
                        "cases": ["security/ssrf-url-allowlist"],
                        "variants": ["baseline_clean", "skills_with_hooks_clean"],
                        "runs_per_variant": 1,
                        "sandbox": "workspace-write",
                        "auth_policy": "borrow-current",
                        "codex_environment_policy": "auth_borrowed_clean",
                        "limitations": ["local"],
                    }
                ),
                encoding="utf-8",
            )
            base = run_dir / "cases" / "security__ssrf-url-allowlist" / "baseline_clean" / "run-01"
            skill = run_dir / "cases" / "security__ssrf-url-allowlist" / "skills_with_hooks_clean" / "run-01"
            base.mkdir(parents=True)
            skill.mkdir(parents=True)
            (base / "result.json").write_text(
                json.dumps(
                    _result_payload(
                        case_id="devex/helper-reuse-search",
                        grading_status="telemetry_only",
                        grading_mode="telemetry_only",
                        publishable_for_strict=False,
                        benchmark_eligible=False,
                        benchmark_passed=False,
                    )
                ),
                encoding="utf-8",
            )
            (skill / "result.json").write_text(
                json.dumps(_result_payload(variant="skills_with_hooks_clean")),
                encoding="utf-8",
            )
            summary = summary_module.generate_summary(run_dir)
        self.assertEqual(summary["variants"]["baseline_clean"]["pass_rate"], "not_collected")
        self.assertEqual(summary["variants"]["skills_with_hooks_clean"]["pass_rate"], 1.0)
        self.assertEqual(summary["assertion_case_count"], 1)
        self.assertEqual(summary["telemetry_only_case_count"], 1)
        self.assertIn("skills_with_hooks_clean_vs_baseline_clean", summary["delta"])
        self.assertEqual(summary["evidence_scope"], "smoke")
        self.assertFalse(summary["evidence_scope_detail"]["strong_claim_ready"])
        self.assertTrue(any("smoke sample only" in item for item in summary["limitations"]))

    def test_summary_aggregates_ablation_runs_usage_cases_and_failure_categories(self) -> None:
        summary_module = _load_script("generate_codex_live_summary_ablation_stats", "scripts/generate-codex-live-summary.py")
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "run-manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "generated_by": "scripts/run-codex-live-benchmarks.py",
                        "run_id": "local-ablation",
                        "status": "collected",
                        "benchmark_mode": "ablation",
                        "dry_run": False,
                        "live_execution_allowed": True,
                        "live_execution_effective": True,
                        "cases": ["security/ssrf-url-allowlist"],
                        "variants": ["baseline_clean", "skills_only_clean", "skills_with_hooks_clean"],
                        "runs_per_variant": 3,
                        "sandbox": "workspace-write",
                        "auth_policy": "borrow-current",
                        "codex_environment_policy": "auth_borrowed_clean",
                        "limitations": ["local"],
                    }
                ),
                encoding="utf-8",
            )
            for variant, passed_runs in (
                ("baseline_clean", {3}),
                ("skills_only_clean", {1, 2, 3}),
                ("skills_with_hooks_clean", {1, 2, 3}),
            ):
                for run_index in range(1, 4):
                    result_dir = (
                        run_dir
                        / "cases"
                        / "security__ssrf-url-allowlist"
                        / variant
                        / f"run-{run_index:02d}"
                    )
                    result_dir.mkdir(parents=True)
                    passed = run_index in passed_runs
                    failure_category = "none" if passed else "test_suite_failed"
                    result = _result_payload(
                        variant=variant,
                        run_index=run_index,
                        grading_status="passed" if passed else "failed",
                        benchmark_passed=passed,
                        failure_category=failure_category,
                        grading={
                            "all_passed": passed,
                            "setup_passed": True,
                            "test_suite_passed": passed,
                            "security_checks_passed": True,
                        },
                    )
                    result["metrics"]["usage"]["input_tokens"] = run_index * 10
                    result["metrics"]["command_execution_count"] = run_index
                    (result_dir / "result.json").write_text(json.dumps(result), encoding="utf-8")
            summary = summary_module.generate_summary(run_dir)
        baseline = summary["variants"]["baseline_clean"]
        self.assertEqual(baseline["run_count"], 3)
        self.assertEqual(baseline["case_count"], 1)
        self.assertEqual(baseline["pass_rate"], 0.3333)
        self.assertEqual(baseline["failure_categories"], {"test_suite_failed": 2, "none": 1})
        self.assertEqual(baseline["average_usage"]["input_tokens"], 20.0)
        self.assertEqual(baseline["median_usage"]["input_tokens"], 20.0)
        self.assertEqual(baseline["min_usage"]["input_tokens"], 10)
        self.assertEqual(baseline["max_usage"]["input_tokens"], 30)
        self.assertIn("skills_only_clean_vs_baseline_clean", summary["delta"])
        self.assertIn("skills_with_hooks_clean_vs_skills_only_clean", summary["delta"])
        self.assertIn("skills_with_hooks_clean_vs_baseline_clean", summary["delta"])
        self.assertEqual(summary["evidence_scope"], "smoke")
        self.assertFalse(summary["evidence_scope_detail"]["strong_claim_ready"])
        self.assertEqual(
            summary["cases_summary"]["security/ssrf-url-allowlist"]["variants"]["baseline_clean"]["pass_rate"],
            0.3333,
        )

    def test_summary_marks_strong_scope_only_for_five_case_three_run_ablation(self) -> None:
        summary_module = _load_script(
            "generate_codex_live_summary_strong_scope",
            "scripts/generate-codex-live-summary.py",
        )
        cases = [
            "devex/helper-reuse-search",
            "structure/object-method-encapsulation-placement",
            "backend/service-method-vs-new-helper",
            "reliability/redis-cache-stampede-protection",
            "security/ssrf-url-allowlist",
        ]
        variants = ["baseline_clean", "skills_only_clean", "skills_with_hooks_clean"]
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "run-manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "generated_by": "scripts/run-codex-live-benchmarks.py",
                        "run_id": "local-ablation",
                        "status": "collected",
                        "benchmark_mode": "ablation",
                        "dry_run": False,
                        "live_execution_allowed": True,
                        "live_execution_effective": True,
                        "cases": cases,
                        "variants": variants,
                        "runs_per_variant": 3,
                        "sandbox": "workspace-write",
                        "auth_policy": "borrow-current",
                        "codex_environment_policy": "auth_borrowed_clean",
                        "limitations": ["local"],
                    }
                ),
                encoding="utf-8",
            )
            # This synthetic matrix exercises scope classification only; it is not live Codex evidence.
            for case_id in cases:
                for variant in variants:
                    for run_index in range(1, 4):
                        result_dir = (
                            run_dir
                            / "cases"
                            / case_id.replace("/", "__")
                            / variant
                            / f"run-{run_index:02d}"
                        )
                        result_dir.mkdir(parents=True)
                        (result_dir / "result.json").write_text(
                            json.dumps(
                                _result_payload(
                                    case_id=case_id,
                                    variant=variant,
                                    run_index=run_index,
                                )
                            ),
                            encoding="utf-8",
                        )
            summary = summary_module.generate_summary(run_dir)

        self.assertEqual(summary["evidence_scope"], "multi_case_ablation_3_run")
        self.assertTrue(summary["evidence_scope_detail"]["strong_claim_ready"])
        self.assertEqual(summary["evidence_scope_detail"]["observed_assertion_case_count"], 5)
        self.assertEqual(summary["evidence_scope_detail"]["observed_min_runs_per_required_variant"], 3)

    def test_failure_category_priority_is_stable(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_failure_category", "scripts/run-codex-live-benchmarks.py")
        self.assertEqual(
            runner._failure_category(
                artifact_status="partial",
                failure_stage="install_changeforge",
                codex_returncode=None,
                contamination={"contaminated": False},
                grading_status="not_collected",
                grading={},
                benchmark_passed=False,
            ),
            "install_failed",
        )
        self.assertEqual(
            runner._failure_category(
                artifact_status="failed",
                failure_stage=None,
                codex_returncode=1,
                contamination={"contaminated": False},
                grading_status="failed",
                grading={},
                benchmark_passed=False,
            ),
            "codex_exec_failed",
        )
        self.assertEqual(
            runner._failure_category(
                artifact_status="collected",
                failure_stage=None,
                codex_returncode=0,
                contamination={"contaminated": True},
                grading_status="failed",
                grading={"test_suite_passed": False},
                benchmark_passed=False,
            ),
            "contaminated",
        )
        self.assertEqual(
            runner._failure_category(
                artifact_status="collected",
                failure_stage=None,
                codex_returncode=0,
                contamination={"contaminated": False},
                grading_status="failed",
                grading={"setup_passed": True, "test_suite_passed": False},
                benchmark_passed=False,
            ),
            "test_suite_failed",
        )

    def test_validator_rejects_secret_patterns_and_absolute_paths_but_not_raw_events(self) -> None:
        validator = _load_script("validate_codex_live_reports_secret", "scripts/validate-codex-live-benchmark-reports.py")
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "run-manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "generated_by": "scripts/run-codex-live-benchmarks.py",
                        "run_id": "dry-run",
                        "status": "skipped_not_opted_in",
                        "benchmark_mode": "clean-paired",
                        "dry_run": True,
                        "live_execution_allowed": False,
                        "live_execution_effective": False,
                        "cases": ["devex/helper-reuse-search"],
                        "variants": ["baseline_clean", "skills_with_hooks_clean"],
                        "runs_per_variant": 1,
                        "sandbox": "workspace-write",
                        "auth_policy": "borrow-current",
                        "codex_environment_policy": "auth_borrowed_clean",
                        "limitations": ["dry-run"],
                    }
                ),
                encoding="utf-8",
            )
            leak_dir = run_dir / "cases" / "devex__helper-reuse-search" / "baseline_clean" / "run-01"
            leak_dir.mkdir(parents=True)
            (leak_dir / "events.jsonl").write_text('{"path": "/Users/raw/events-only"}\n', encoding="utf-8")
            (leak_dir / "events.redacted.jsonl").write_text('{"path": "/Users/raw/redacted"}\n', encoding="utf-8")
            fake_secret = "CODEX" + "_API" + "_KEY=" + "sk-" + "ThisShouldFail123"
            (leak_dir / "result.json").write_text(fake_secret, encoding="utf-8")
            (leak_dir / "final.md").write_text("/Users/raw/final", encoding="utf-8")
            errors = validator.validate_run_dir(run_dir)
        self.assertTrue(any("forbidden secret pattern" in error for error in errors))
        self.assertTrue(any("absolute path" in error for error in errors))
        self.assertTrue(any("events.redacted.jsonl" in error for error in errors))
        self.assertFalse(any("events-only" in error for error in errors))

    def test_generated_summary_and_result_do_not_store_host_paths_or_auth_json(self) -> None:
        summary_module = _load_script("generate_codex_live_summary_no_paths", "scripts/generate-codex-live-summary.py")
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "run-manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "generated_by": "scripts/run-codex-live-benchmarks.py",
                        "run_id": "local-test",
                        "status": "collected",
                        "benchmark_mode": "clean-paired",
                        "dry_run": False,
                        "live_execution_allowed": True,
                        "live_execution_effective": True,
                        "cases": ["security/ssrf-url-allowlist"],
                        "variants": ["baseline_clean", "skills_with_hooks_clean"],
                        "runs_per_variant": 1,
                        "sandbox": "workspace-write",
                        "auth_policy": "borrow-current",
                        "codex_environment_policy": "auth_borrowed_clean",
                        "limitations": ["local"],
                    }
                ),
                encoding="utf-8",
            )
            result_dir = run_dir / "cases" / "security__ssrf-url-allowlist" / "baseline_clean" / "run-01"
            result_dir.mkdir(parents=True)
            result = _result_payload()
            (result_dir / "result.json").write_text(json.dumps(result), encoding="utf-8")
            summary = summary_module.generate_summary(run_dir)
        encoded = json.dumps(summary) + json.dumps(result)
        self.assertNotIn("/Users/", encoded)
        self.assertNotIn("/home/", encoded)
        self.assertNotIn("C:/Users", encoded)
        self.assertNotIn("auth.json", encoded)

    def test_auth_json_is_not_copied_to_run_artifacts(self) -> None:
        runner = _load_script("run_codex_live_benchmarks_no_auth_copy", "scripts/run-codex-live-benchmarks.py")
        args = SimpleNamespace(auth_policy="borrow-current", benchmark_mode="clean-paired")
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            with patch.dict("os.environ", {"HOME": "/Users/raw-home", "CODEX_HOME": "/Users/raw-codex"}, clear=True):
                env, metadata = runner.build_codex_environment(args, SimpleNamespace(id="x/y"), "baseline_clean", run_dir)
            artifact_names = [path.name for path in run_dir.rglob("*")]
            runner._cleanup_borrowed_codex_home(env)
        self.assertFalse(metadata["auth_json_copied"])
        self.assertNotIn("auth.json", artifact_names)

    def test_parser_counts_usage_without_raw_command_or_message(self) -> None:
        parser = _load_script("parse_codex_jsonl_test", "scripts/parse-codex-jsonl.py")
        with tempfile.TemporaryDirectory() as tmp:
            events = Path(tmp) / "events.jsonl"
            events.write_text(
                "\n".join(
                    [
                        json.dumps({"type": "turn.started"}),
                        json.dumps({"type": "tool_call", "command": "echo SHOULD_NOT_LEAK", "usage": {"input_tokens": 10}}),
                        json.dumps({"type": "message", "role": "assistant", "message": "SHOULD_NOT_LEAK"}),
                        "{bad json",
                    ]
                ),
                encoding="utf-8",
            )
            metrics = parser.parse_events(events)
        self.assertEqual(metrics["event_count"], 3)
        self.assertEqual(metrics["command_execution_count"], 1)
        self.assertEqual(metrics["usage"]["input_tokens"], 10)
        self.assertNotIn("SHOULD_NOT_LEAK", json.dumps(metrics))
        self.assertEqual(len(metrics["parse_errors"]), 1)

    def test_parser_writes_bounded_redacted_events_without_raw_payloads(self) -> None:
        parser = _load_script("parse_codex_jsonl_redacted", "scripts/parse-codex-jsonl.py")
        with tempfile.TemporaryDirectory() as tmp:
            events = Path(tmp) / "events.jsonl"
            redacted = Path(tmp) / "events.redacted.jsonl"
            events.write_text(
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {
                            "type": "command_execution",
                            "status": "completed",
                            "command": "/bin/zsh -lc 'cat /Users/raw/secret.txt'",
                            "aggregated_output": "SHOULD_NOT_LEAK /Users/raw/project",
                            "usage": {"input_tokens": 10, "output_tokens": 5},
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            parser.write_redacted_events(events, redacted)
            text = redacted.read_text(encoding="utf-8")
        self.assertIn("command_execution", text)
        self.assertIn("input_tokens", text)
        self.assertNotIn("SHOULD_NOT_LEAK", text)
        self.assertNotIn("/Users/raw", text)

    def test_grader_marks_cases_without_assertions_not_collected_and_redacts_paths(self) -> None:
        grader = _load_script("grade_codex_live_redaction", "scripts/grade-codex-live-benchmarks.py")
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "candidate"
            out_dir = Path(tmp) / "grading"
            candidate.mkdir()
            result = grader.grade_candidate("devex/minimal-correct-implementation-ladder", candidate, out_dir)
            redacted = grader._redact_output(
                f"{candidate}/file.py {Path(tmp)}/other.py /private/var/folders/sample /tmp/sample",
                root=Path(tmp),
                candidate_dir=candidate,
            )
        self.assertEqual(result["grading_status"], "not_collected")
        self.assertEqual(result["candidate_dir"], "<candidate>")
        self.assertNotIn(str(candidate), redacted)
        self.assertNotIn(str(Path(tmp)), redacted)
        self.assertNotIn("/private/var/", redacted)
        self.assertNotIn("/tmp/", redacted)

    def test_case_registry_requires_assertions_for_publishable_cases(self) -> None:
        helper = _load_script("codex_live_helper_bad_registry", "scripts/codex_live_benchmark_lib.py")
        data = {
            "schema_version": 1,
            "kind": "changeforge.codex_live_benchmark_cases",
            "cases": [
                {
                    "id": "devex/minimal-correct-implementation-ladder",
                    "category": "devex",
                    "codegen_case": "minimal-correct-implementation-ladder",
                    "enabled": True,
                    "variants": ["baseline_clean"],
                    "task_prompt": "evals/codegen/devex/minimal-correct-implementation-ladder/prompt.md",
                    "starter_repo": "evals/codegen/devex/minimal-correct-implementation-ladder/starter-repo",
                    "grading_benchmark": "devex/minimal-correct-implementation-ladder",
                    "grading_mode": "assertion",
                    "publishable_for_strict": True,
                }
            ],
        }
        errors = helper.validate_case_registry(data, ROOT)
        self.assertTrue(any("requires real pytest assertion files" in error for error in errors))

    def test_case_registry_has_five_publishable_assertion_backed_cases(self) -> None:
        helper = _load_script("codex_live_helper_registry_coverage", "scripts/codex_live_benchmark_lib.py")
        cases = helper.load_case_registry()
        publishable = [
            case
            for case in cases
            if case.enabled and case.publishable_for_strict and case.grading_mode == "assertion"
        ]
        self.assertGreaterEqual(len(publishable), 5)
        self.assertIn(
            "reliability/redis-cache-stampede-protection",
            {case.id for case in publishable},
        )
        self.assertTrue(
            all(helper.case_assertion_files(case.category, case.codegen_case) for case in publishable)
        )
        telemetry_only = [case for case in cases if case.grading_mode == "telemetry_only"]
        self.assertTrue(telemetry_only)
        self.assertTrue(all(not case.publishable_for_strict for case in telemetry_only))

    def test_codegen_candidate_mode_executes_real_assertion_files(self) -> None:
        runner = _load_script("run_codegen_benchmark_assertions", "scripts/run-codegen-benchmarks.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            case_dir = root / "case"
            starter = case_dir / "starter-repo"
            test_suite = case_dir / "test-suite"
            security_checks = case_dir / "security-checks"
            tests_dir = test_suite / "tests"
            candidate = root / "candidate"
            for path in (starter, test_suite, security_checks, tests_dir, candidate):
                path.mkdir(parents=True, exist_ok=True)
            for script in (
                starter / "setup.sh",
                candidate / "setup.sh",
                test_suite / "run.sh",
                security_checks / "run.sh",
            ):
                script.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            (candidate / "sentinel.txt").write_text("ok", encoding="utf-8")
            (tests_dir / "test_candidate.py").write_text(
                "\n".join(
                    [
                        "import os",
                        "from pathlib import Path",
                        "candidate = Path(os.environ['CHANGEFORGE_CODEGEN_CANDIDATE_DIR'])",
                        "assert (candidate / 'sentinel.txt').read_text(encoding='utf-8') == 'ok'",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            self.assertEqual(runner._run_case("sample", "assertion-case", case_dir, candidate), [])
            (candidate / "sentinel.txt").write_text("bad", encoding="utf-8")
            errors = runner._run_case("sample", "assertion-case", case_dir, candidate)
        self.assertTrue(any("assertion" in error and "test_candidate.py" in error for error in errors))

    def test_scorecard_and_public_summary_accept_strict_auth_borrowed_summary(self) -> None:
        scorecard = _load_script("generate_professional_scorecard_codex_live", "scripts/generate-professional-scorecard.py")
        public = _load_script("generate_public_summary_codex_live", "scripts/generate-public-benchmark-summary.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "reports").mkdir()
            (root / "reports" / "codex-live-benchmark-summary.json").write_text(
                json.dumps(_strict_summary_payload()),
                encoding="utf-8",
            )
            status, detail = scorecard.codex_live_benchmark_status(root)
            item = public._codex_live_benchmark_item(root)
        self.assertEqual(status, "pass")
        self.assertIn("auth_borrowed_clean", detail)
        self.assertEqual(item.status, "pass")
        self.assertEqual(item.evidence_level, "local_codex_cli_live_benchmark")

    def test_public_summary_rejects_current_home_smoke_as_strict_file(self) -> None:
        public = _load_script("generate_public_summary_codex_live_smoke", "scripts/generate-public-benchmark-summary.py")
        payload = _strict_summary_payload(
            benchmark_mode="current-home-smoke",
            evidence_level="current_home_integration_smoke",
            auth_policy="current-home-full",
            codex_environment_policy="current_home_full",
            strict_benchmark_eligible=False,
            current_home_full_result_count=1,
            user_skills_visible=True,
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "reports").mkdir()
            (root / "reports" / "codex-live-benchmark-summary.json").write_text(json.dumps(payload), encoding="utf-8")
            item = public._codex_live_benchmark_item(root)
        self.assertEqual(item.status, "fail")
        self.assertIn("current-home-full", item.detail)

    def test_scorecard_and_public_summary_reject_ablation_missing_delta(self) -> None:
        scorecard = _load_script(
            "generate_professional_scorecard_codex_live_ablation_delta",
            "scripts/generate-professional-scorecard.py",
        )
        public = _load_script(
            "generate_public_summary_codex_live_ablation_delta",
            "scripts/generate-public-benchmark-summary.py",
        )
        payload = _strict_summary_payload(
            benchmark_mode="ablation",
            result_count=3,
            benchmark_eligible_result_count=3,
            benchmark_passed_result_count=3,
            failure_categories={"none": 3},
            variants={
                "baseline_clean": _variant_payload(),
                "skills_only_clean": _variant_payload(),
                "skills_with_hooks_clean": _variant_payload(),
            },
            delta={
                "skills_only_clean_vs_baseline_clean": {"pass_rate_delta": 0.0},
                "skills_with_hooks_clean_vs_baseline_clean": {"pass_rate_delta": 0.0},
            },
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "reports").mkdir()
            (root / "reports" / "codex-live-benchmark-summary.json").write_text(
                json.dumps(payload),
                encoding="utf-8",
            )
            status, detail = scorecard.codex_live_benchmark_status(root)
            item = public._codex_live_benchmark_item(root)
        self.assertEqual(status, "fail")
        self.assertIn("delta.skills_with_hooks_clean_vs_skills_only_clean", detail)
        self.assertEqual(item.status, "fail")
        self.assertIn("ablation delta skills_with_hooks_clean_vs_skills_only_clean", item.detail)


if __name__ == "__main__":
    unittest.main()
