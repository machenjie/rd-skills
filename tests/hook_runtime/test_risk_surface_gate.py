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


def run_risk(event: dict) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as cache:
        event["cwd"] = cwd
        env = os.environ.copy()
        env["XDG_CACHE_HOME"] = cache
        env.pop("CHANGEFORGE_HOOK_MODE", None)
        env.pop("CHANGEFORGE_AGENT", None)
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


if __name__ == "__main__":
    unittest.main()
