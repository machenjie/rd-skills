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


def run_risk(event: dict, *, agent: str | None = None) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
        event["cwd"] = cwd
        env = os.environ.copy()
        env["XDG_CACHE_HOME"] = cache
        env.pop("CHANGEFORGE_HOOK_MODE", None)
        if agent is None:
            env.pop("CHANGEFORGE_AGENT", None)
        else:
            env["CHANGEFORGE_AGENT"] = agent
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

    def test_first_risk_surface_emits_route_preflight(self) -> None:
        event = {
            "runtime": "codex",
            "hookEventName": "PostToolUse",
            "toolName": "Edit",
            "toolInput": {"file_path": "src/auth/session_token.py"},
        }
        result = run_risk(event)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Route preflight", result.stdout)
        self.assertIn("change-forge-router", result.stdout)
        self.assertIn("changeforge_route", result.stdout)

    def test_route_preflight_not_repeated_in_same_turn(self) -> None:
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
        self.assertIn("Route preflight", first.stdout)
        self.assertIn("security", first.stdout)
        # The second risk surface in the same turn keeps the warning but drops the
        # one-time route-preflight nudge so the reminder is not repeated per edit.
        self.assertNotIn("Route preflight", second.stdout)
        self.assertIn("security", second.stdout)

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
        self.assertNotIn("Route preflight", result.stdout)
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
        self.assertNotIn("Route preflight", result.stdout)
        self.assertEqual(state["closure_risk_surfaces"], [])
        self.assertTrue(state["validation_command_seen"])
        self.assertEqual(records[-1]["closure_risk_surfaces"], [])
        self.assertTrue(records[-1]["validation_command_detected"])

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
                self.assertIn("ChangeForge Risk Surface Gate triggered", result.stdout)
                self.assertIn("Route preflight", result.stdout)


if __name__ == "__main__":
    unittest.main()
