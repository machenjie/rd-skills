from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


def run_risk(
    event: dict,
    *,
    agent: str | None = None,
    env_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
        event["cwd"] = cwd
        env = os.environ.copy()
        env["XDG_CACHE_HOME"] = cache
        env.pop("CHANGEFORGE_HOOK_MODE", None)
        if agent is None:
            env.pop("CHANGEFORGE_AGENT", None)
        else:
            env["CHANGEFORGE_AGENT"] = agent
        if env_overrides:
            env.update(env_overrides)
        return subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "changeforge_risk_surface_gate.py")],
            input=json.dumps(event),
            text=True,
            capture_output=True,
            cwd=cwd,
            env=env,
            check=False,
        )


def read_records(cache: Path) -> list[dict]:
    records: list[dict] = []
    for file_path in cache.glob("changeforge/telemetry/*/sessions/*.jsonl"):
        for line in file_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
    return records


def run_risk_with_state(event: dict) -> tuple[subprocess.CompletedProcess[str], dict, list[dict]]:
    with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
        cwd = Path(cwd_s)
        cache = Path(cache_s)
        event = dict(event)
        event["cwd"] = str(cwd)
        env = os.environ.copy()
        env["XDG_CACHE_HOME"] = str(cache)
        env.pop("CHANGEFORGE_HOOK_MODE", None)
        env.pop("CHANGEFORGE_AGENT", None)
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "changeforge_risk_surface_gate.py")],
            input=json.dumps(event),
            text=True,
            capture_output=True,
            cwd=str(cwd),
            env=env,
            check=False,
        )
        state_files = list(cache.glob("changeforge/hooks/*/current-turn.json"))
        state = json.loads(state_files[0].read_text(encoding="utf-8")) if state_files else {}
        records = read_records(cache)
        return result, state, records


class RiskSurfaceGateTests(unittest.TestCase):
    def test_auth_path_triggers_security_gate(self) -> None:
        event = {
            "runtime": "codex",
            "hookEventName": "PostToolUse",
            "toolName": "Edit",
            "toolInput": {"file_path": "src/auth/session_token.py"},
        }
        result = run_risk(event)
        self.assertEqual(result.returncode, 0)
        self.assertIn("security", result.stdout)
        self.assertIn("security gate", result.stdout)

    def test_claude_auth_path_outputs_additional_context(self) -> None:
        event = {
            "runtime": "claude",
            "hook_event_name": "PostToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "src/auth/session_token.py"},
        }
        result = run_risk(event, agent="claude")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PostToolUse")
        self.assertIn("security gate", payload["hookSpecificOutput"]["additionalContext"])

    def test_migration_sql_schema_triggers_data_api_gate(self) -> None:
        event = {
            "runtime": "codex",
            "hookEventName": "PostToolUse",
            "toolName": "Edit",
            "toolInput": {"file_path": "db/migrations/001_create_schema.sql"},
        }
        result = run_risk(event)
        self.assertEqual(result.returncode, 0)
        self.assertIn("data-api", result.stdout)
        self.assertIn("API/data gate", result.stdout)

    def test_kubectl_apply_triggers_delivery_and_reliability(self) -> None:
        event = json.loads((FIXTURE_DIR / "codex_post_tool_use_bash_kubectl.json").read_text())
        result = run_risk(event)
        self.assertEqual(result.returncode, 0)
        self.assertIn("kubernetes", result.stdout)
        self.assertIn("delivery gate", result.stdout)
        self.assertIn("reliability gate", result.stdout)

    def test_helm_upgrade_triggers_helm_delivery_security(self) -> None:
        event = {
            "runtime": "codex",
            "hookEventName": "PostToolUse",
            "toolName": "Bash",
            "toolInput": {"command": "helm upgrade app ./deploy/helm -f deploy/helm/values.yaml"},
        }
        result = run_risk(event)
        self.assertEqual(result.returncode, 0)
        self.assertIn("helm", result.stdout)
        self.assertIn("delivery gate", result.stdout)
        self.assertIn("security gate", result.stdout)

    def test_spark_backfill_triggers_bigdata_domain_extension(self) -> None:
        event = {
            "runtime": "codex",
            "hookEventName": "PostToolUse",
            "toolName": "Edit",
            "toolInput": {"file_path": "jobs/spark/backfill_partitions.py"},
        }
        result = run_risk(event)
        self.assertEqual(result.returncode, 0)
        self.assertIn("spark-bigdata", result.stdout)
        self.assertIn("bigdata-product-extension", result.stdout)
        self.assertIn("reliability gate", result.stdout)

    def test_first_risk_surface_emits_expert_note_without_internal_protocol(self) -> None:
        event = {
            "runtime": "codex",
            "hookEventName": "PostToolUse",
            "toolName": "Edit",
            "toolInput": {"file_path": "src/auth/session_token.py"},
        }
        result = run_risk(event)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Engineering expert note", result.stdout)
        self.assertIn("task type and risk level", result.stdout)
        self.assertIn("owner skill or professional concerns", result.stdout)
        self.assertIn("source files and tests", result.stdout)
        self.assertIn("validation plan and residual risk", result.stdout)
        for forbidden in (
            "Route preflight",
            "changeforge_route",
            "selected_skills",
            "selected_capabilities",
            "required_references",
            "required_quality_gates",
            "closure evidence",
        ):
            self.assertNotIn(forbidden, result.stdout)

    def test_expert_note_not_repeated_in_same_turn(self) -> None:
        event = {
            "runtime": "codex",
            "hookEventName": "PostToolUse",
            "toolName": "Edit",
            "toolInput": {"file_path": "src/auth/session_token.py"},
        }
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
            env = os.environ.copy()
            env["XDG_CACHE_HOME"] = cache
            env.pop("CHANGEFORGE_HOOK_MODE", None)
            env.pop("CHANGEFORGE_AGENT", None)
            event["cwd"] = cwd

            def _run() -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [sys.executable, str(SCRIPT_DIR / "changeforge_risk_surface_gate.py")],
                    input=json.dumps(event),
                    text=True,
                    capture_output=True,
                    cwd=cwd,
                    env=env,
                    check=False,
                )

            first = _run()
            second = _run()
        self.assertIn("Engineering expert note", first.stdout)
        self.assertIn("security", first.stdout)
        # The second risk surface in the same turn keeps the warning but drops the
        # one-time expert nudge so the reminder is not repeated per edit.
        self.assertNotIn("Engineering expert note", second.stdout)
        self.assertIn("security", second.stdout)

    def test_global_block_mode_does_not_block_ordinary_risk_surface(self) -> None:
        event = {
            "runtime": "codex",
            "hookEventName": "PostToolUse",
            "toolName": "Edit",
            "toolInput": {"file_path": "src/auth/session_token.py"},
        }
        result = run_risk(event, env_overrides={"CHANGEFORGE_HOOK_MODE": "block"})
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertIn("hookSpecificOutput", payload)
        self.assertNotEqual(payload.get("decision"), "block")
        self.assertIn("security", payload["hookSpecificOutput"]["additionalContext"])

    def test_strict_global_block_mode_can_block_risk_surface(self) -> None:
        event = {
            "runtime": "codex",
            "hookEventName": "PostToolUse",
            "toolName": "Edit",
            "toolInput": {"file_path": "src/auth/session_token.py"},
        }
        result = run_risk(
            event,
            env_overrides={
                "CHANGEFORGE_HOOK_MODE": "block",
                "CHANGEFORGE_STRICT_BLOCKING": "1",
            },
        )
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload.get("decision"), "block")
        self.assertIn("security", payload.get("reason", ""))

    def test_read_only_command_surface_does_not_pollute_closure_state(self) -> None:
        event = {
            "runtime": "codex",
            "hookEventName": "PostToolUse",
            "toolName": "Bash",
            "toolInput": {
                "command": "sed -n '1,80p' src/hook-runtime/schemas/hook-state.v1.schema.json"
            },
        }
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd = Path(cwd_s)
            cache = Path(cache_s)
            env = os.environ.copy()
            env["XDG_CACHE_HOME"] = str(cache)
            env.pop("CHANGEFORGE_HOOK_MODE", None)
            env.pop("CHANGEFORGE_AGENT", None)
            event["cwd"] = str(cwd)
            result = subprocess.run(
                [sys.executable, str(SCRIPT_DIR / "changeforge_risk_surface_gate.py")],
                input=json.dumps(event),
                text=True,
                capture_output=True,
                cwd=str(cwd),
                env=env,
                check=False,
            )
            state_files = list(cache.glob("changeforge/hooks/*/current-turn.json"))
            self.assertEqual(len(state_files), 1)
            state = json.loads(state_files[0].read_text(encoding="utf-8"))
            records = read_records(cache)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertNotIn("Engineering expert note", result.stdout)
        self.assertEqual(state["risk_surfaces"], [])
        self.assertEqual(state["closure_risk_surfaces"], [])
        self.assertEqual(state["command_risk_surfaces"], ["data-api"])
        self.assertEqual(records[-1]["risk_surfaces"], [])
        self.assertEqual(records[-1]["suggested_skills"], [])
        self.assertEqual(records[-1]["command_risk_surfaces"], ["data-api"])
        self.assertEqual(records[-1]["closure_risk_surfaces"], [])

    def test_validation_command_surface_does_not_pollute_closure_state(self) -> None:
        event = {
            "runtime": "codex",
            "hookEventName": "PostToolUse",
            "toolName": "Bash",
            "toolInput": {"command": "python3 scripts/validate-schema.py"},
        }
        with tempfile.TemporaryDirectory() as cwd_s, tempfile.TemporaryDirectory() as cache_s:
            cwd = Path(cwd_s)
            cache = Path(cache_s)
            env = os.environ.copy()
            env["XDG_CACHE_HOME"] = str(cache)
            env.pop("CHANGEFORGE_HOOK_MODE", None)
            env.pop("CHANGEFORGE_AGENT", None)
            event["cwd"] = str(cwd)
            result = subprocess.run(
                [sys.executable, str(SCRIPT_DIR / "changeforge_risk_surface_gate.py")],
                input=json.dumps(event),
                text=True,
                capture_output=True,
                cwd=str(cwd),
                env=env,
                check=False,
            )
            state_files = list(cache.glob("changeforge/hooks/*/current-turn.json"))
            self.assertEqual(len(state_files), 1)
            state = json.loads(state_files[0].read_text(encoding="utf-8"))
            records = read_records(cache)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertNotIn("Engineering expert note", result.stdout)
        self.assertEqual(state["closure_risk_surfaces"], [])
        self.assertTrue(state["validation_command_seen"])
        self.assertEqual(records[-1]["closure_risk_surfaces"], [])
        self.assertTrue(records[-1]["validation_command_detected"])

    def test_destructive_commands_record_tool_permission_sandbox(self) -> None:
        commands = {
            "rm -rf tmp/generated": "tmp/generated",
            "git clean -fd": "-fd",
        }
        for command, sensitive_arg in commands.items():
            with self.subTest(command=command):
                event = {
                    "runtime": "codex",
                    "hookEventName": "PostToolUse",
                    "toolName": "Bash",
                    "toolInput": {"command": command},
                }
                result, state, records = run_risk_with_state(event)
                self.assertEqual(result.returncode, 0)
                self.assertIn("tool-permission-sandbox", result.stdout)
                self.assertNotIn(sensitive_arg, result.stdout)
                self.assertTrue(state["tool_permission_sandbox_seen"])
                self.assertIn("tool-permission-sandbox", state["closure_risk_surfaces"])
                self.assertIn("agent-tool-permission-sandbox", state["suggested_capabilities"])
                self.assertTrue(records[-1]["tool_permission_sandbox_seen"])
                self.assertIn("agent-tool-permission-sandbox", records[-1]["suggested_capabilities"])

    def test_script_name_markers_record_high_risk_tool_permission_sandbox(self) -> None:
        # Regression: command markers inside script paths must not depend on spaces.
        commands = [
            "python scripts/migrate_schema.py",
            "python scripts/run_migration.py",
            "python scripts/backfill_orders.py",
            "python scripts/deploy_app.py",
            "python scripts/apply_migration.py",
        ]
        for command in commands:
            with self.subTest(command=command):
                event = {
                    "runtime": "codex",
                    "hookEventName": "PostToolUse",
                    "toolName": "Bash",
                    "toolInput": {"command": command},
                }
                result, state, records = run_risk_with_state(event)
                self.assertEqual(result.returncode, 0)
                self.assertIn("tool-permission-sandbox", result.stdout)
                self.assertIn("delivery gate", result.stdout)
                self.assertIn("reliability gate", result.stdout)
                self.assertIn("rollback note", result.stdout)
                self.assertIn("tool-permission-sandbox", state["closure_risk_surfaces"])
                self.assertIn("agent-tool-permission-sandbox", state["suggested_capabilities"])
                self.assertIn("delivery-release-gate", state["suggested_skills"])
                self.assertIn("reliability-observability-gate", state["suggested_skills"])
                self.assertIn("delivery gate", state["suggested_gates"])
                self.assertIn("reliability gate", state["suggested_gates"])
                self.assertIn(
                    "agent-tool-permission-sandbox",
                    records[-1]["suggested_capabilities"],
                )
                self.assertIn("delivery gate", records[-1]["suggested_gates"])
                self.assertIn("reliability gate", records[-1]["suggested_gates"])

    def test_marker_substrings_do_not_escalate_tool_permission_sandbox(self) -> None:
        # Boundary guard: words containing marker text are still ordinary local writes.
        commands = [
            "python scripts/application_report.py",
            "python scripts/tokenizer.py",
        ]
        for command in commands:
            with self.subTest(command=command):
                event = {
                    "runtime": "codex",
                    "hookEventName": "PostToolUse",
                    "toolName": "Bash",
                    "toolInput": {"command": command},
                }
                result, state, records = run_risk_with_state(event)
                self.assertEqual(result.returncode, 0)
                self.assertIn("tool-permission-sandbox", result.stdout)
                self.assertIn("agent-tool-permission-sandbox", state["suggested_capabilities"])
                self.assertNotIn("delivery gate", state["suggested_gates"])
                self.assertNotIn("reliability gate", state["suggested_gates"])
                self.assertNotIn("delivery gate", records[-1]["suggested_gates"])
                self.assertNotIn("reliability gate", records[-1]["suggested_gates"])

    def test_read_only_and_validation_commands_do_not_record_tool_permission(self) -> None:
        commands = [
            "pytest tests/hook_runtime/test_risk_surface_gate.py",
            "rg data-api src",
            "cat README.md",
            "git diff README.md",
        ]
        for command in commands:
            with self.subTest(command=command):
                event = {
                    "runtime": "codex",
                    "hookEventName": "PostToolUse",
                    "toolName": "Bash",
                    "toolInput": {"command": command},
                }
                result, state, records = run_risk_with_state(event)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertFalse(state["tool_permission_sandbox_seen"])
                self.assertNotIn("agent-tool-permission-sandbox", state["suggested_capabilities"])
                self.assertFalse(records[-1]["tool_permission_sandbox_seen"])
                self.assertNotIn("agent-tool-permission-sandbox", records[-1]["suggested_capabilities"])

    def test_read_only_wrappers_and_pipelines_do_not_emit_warning(self) -> None:
        commands = [
            'bash -lc "rg data-api src"',
            'sh -c "sed -n 1,80p src/auth/session.py"',
            'zsh -c "git grep data-api"',
            'bash -lc "rg data-api src || true"',
            "rg data-api src || true",
            "rg data-api src || :",
            "rg data-api src | head",
            "jq .schema config.json",
            "awk /schema/ README.md",
            "bat src/auth/session.py",
            "fd migration db",
        ]
        for command in commands:
            with self.subTest(command=command):
                event = {
                    "runtime": "codex",
                    "hookEventName": "PostToolUse",
                    "toolName": "Bash",
                    "toolInput": {"command": command},
                }
                result = run_risk(event)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")

    def test_read_only_git_commands_do_not_emit_warning(self) -> None:
        commands = [
            "git diff src/auth/session.py",
            "git show HEAD:db/schema.sql",
            "git status --short src/auth/session.py",
            "git log -- db/migrations",
            "git ls-files db/migrations",
            "git rev-parse HEAD",
            "git cat-file -p HEAD:db/schema.sql",
        ]
        for command in commands:
            with self.subTest(command=command):
                event = {
                    "runtime": "codex",
                    "hookEventName": "PostToolUse",
                    "toolName": "Bash",
                    "toolInput": {"command": command},
                }
                result = run_risk(event)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")

    def test_gmgn_bounded_remote_kubectl_logs_are_readonly_diagnostic(self) -> None:
        command = (
            "ssh HKBUILD 'cd crypto && kubectl logs --selector "
            "app.kubernetes.io/instance=crypto-one --since=2h --tail=2000 "
            "--all-containers=true | grep -F \"gmgn_token_intel_skipped\" | "
            "tail -80 || true'"
        )
        event = {
            "runtime": "codex",
            "hookEventName": "PostToolUse",
            "toolName": "Bash",
            "toolInput": {"command": command},
        }
        result, state, records = run_risk_with_state(event)
        self.assertEqual(result.returncode, 0)
        self.assertIn("production-readonly-diagnostic", result.stdout)
        self.assertNotIn("delivery gate", result.stdout)
        self.assertNotIn("gmgn_token_intel_skipped", result.stdout)
        self.assertEqual(
            state["command_risks"],
            ["production_readonly_diagnostic:ssh:kubectl:logs:bounded"],
        )
        self.assertEqual(state["closure_risk_surfaces"], [])
        self.assertEqual(records[-1]["command_risk"], "production_readonly_diagnostic")
        self.assertNotIn("gmgn_token_intel_skipped", json.dumps(records[-1]))

    def test_gmgn_env_metadata_probe_is_allowed(self) -> None:
        command = (
            "ssh HKBUILD 'cd crypto && if [ -f .env ]; then echo "
            "env_file=present; else echo env_file=missing; fi'"
        )
        event = {
            "runtime": "codex",
            "hookEventName": "PostToolUse",
            "toolName": "Bash",
            "toolInput": {"command": command},
        }
        result, state, records = run_risk_with_state(event)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(state["command_risks"], ["secret_metadata_read:ssh:env_file:metadata"])
        self.assertEqual(state["closure_risk_surfaces"], [])
        self.assertEqual(records[-1]["command_risk"], "secret_metadata_read")

    def test_gmgn_env_value_read_is_high_risk_and_redacted(self) -> None:
        event = {
            "runtime": "codex",
            "hookEventName": "PostToolUse",
            "toolName": "Bash",
            "toolInput": {"command": "ssh HKBUILD 'cd crypto && cat .env'"},
        }
        result, state, records = run_risk_with_state(event)
        self.assertEqual(result.returncode, 0)
        self.assertIn("secret-sensitive-output", result.stdout)
        self.assertIn("security gate", result.stdout)
        self.assertNotIn("cat .env", result.stdout)
        self.assertEqual(state["command_risks"], ["secret_sensitive_output:ssh:env_file:value_read"])
        self.assertIn("secret-sensitive-output", state["closure_risk_surfaces"])
        self.assertEqual(records[-1]["command_risk"], "secret_sensitive_output")
        self.assertNotIn("cat .env", json.dumps(records[-1]))

    def test_bounded_kubectl_logs_and_apply_have_distinct_risk_classes(self) -> None:
        cases = {
            "kubectl logs --since=2h --tail=2000": "production_readonly_diagnostic:kubectl:logs:bounded",
            "kubectl apply -f deployment.yaml": "external_write_release:kubectl:apply:external_write",
        }
        for command, expected in cases.items():
            with self.subTest(command=command):
                event = {
                    "runtime": "codex",
                    "hookEventName": "PostToolUse",
                    "toolName": "Bash",
                    "toolInput": {"command": command},
                }
                result, state, records = run_risk_with_state(event)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(state["command_risks"], [expected])
                self.assertEqual(records[-1]["command_risk"], expected.split(":", 1)[0])
        self.assertIn("external-write-release", result.stdout)

    def test_mutating_commands_remain_closure_relevant(self) -> None:
        commands = [
            "python scripts/migrate_schema.py",
            "kubectl apply -f deploy/kubernetes/rbac.yaml",
            "helm upgrade app ./deploy/helm -f deploy/helm/values.yaml",
            "go generate ./internal/auth",
            "git checkout -- src/auth/session.py",
            "git reset HEAD src/auth/session.py",
            "git clean -fd db/migrations",
            'bash -lc "kubectl apply -f deploy/kubernetes/rbac.yaml"',
        ]
        for command in commands:
            with self.subTest(command=command):
                event = {
                    "runtime": "codex",
                    "hookEventName": "PostToolUse",
                    "toolName": "Bash",
                    "toolInput": {"command": command},
                }
                result = run_risk(event)
                self.assertEqual(result.returncode, 0)
                self.assertIn("Design risk note", result.stdout)
                self.assertIn("Engineering expert note", result.stdout)


if __name__ == "__main__":
    unittest.main()
