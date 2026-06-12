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


if __name__ == "__main__":
    unittest.main()
