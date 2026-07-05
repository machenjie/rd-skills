from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REVIEW_SCRIPT = ROOT / "scripts" / "review-agent-telemetry.py"


def record(**fields: object) -> str:
    base = {
        "schema_version": "1",
        "timestamp_utc": "2026-06-05T10:00:00+00:00",
        "repo_hash": "repohashbbbbbbbbbbbbbbbb",
        "cwd_hash": "cwd",
        "runtime": "codex",
        "hook_name": "stop_closure_gate",
        "event_name": "Stop",
        "session_id": "s1",
        "mode": "warn",
        "tool_name": "",
        "changed_paths": ["src/validation_broker/validation_policy.py"],
        "added_paths": [],
        "hook_findings": {},
        "suggested_skills": [],
        "suggested_capabilities": [],
        "suggested_gates": [],
        "suggested_domain_extensions": [],
        "risk_surfaces": [],
        "changed_path_risk_surfaces": [],
        "command_risk_surfaces": [],
        "closure_risk_surfaces": ["validation-broker"],
        "route_manifest_detected": True,
        "required_references_detected": True,
        "validation_command_detected": False,
        "validation_evidence_detected": False,
        "residual_risk_detected": True,
    }
    base.update(fields)
    return json.dumps(base)


def run_review(root: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("XDG_CACHE_HOME", None)
    return subprocess.run(
        [sys.executable, str(REVIEW_SCRIPT), "--telemetry-root", str(root), "--format", "json"],
        text=True,
        capture_output=True,
        cwd=str(ROOT),
        env=env,
        check=False,
    )


class ValidationBrokerTelemetryFactTests(unittest.TestCase):
    def seed(self, root: Path, rows: list[str]) -> None:
        sessions = root / "repohashbbbbbbbbbbbbbbbb" / "sessions"
        sessions.mkdir(parents=True, exist_ok=True)
        (sessions / "2026-06-05.jsonl").write_text("\n".join(rows) + "\n", encoding="utf-8")

    def report_payload(self, root: Path) -> dict:
        reports = list((root / "repohashbbbbbbbbbbbbbbbb" / "reports").glob("*.json"))
        self.assertTrue(reports)
        return json.loads(reports[0].read_text(encoding="utf-8"))

    def test_old_telemetry_sample_without_broker_fields_still_reads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.seed(
                root,
                [
                    record(
                        validation_command_detected=True,
                        validation_evidence_detected=True,
                        validation_result_outcome="pass",
                        residual_risk_detected=True,
                    )
                ],
            )
            result = run_review(root)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(self.report_payload(root)["summary"]["stale_validation_reused"], 0)

    def test_broker_command_without_outcome_is_not_validation_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.seed(
                root,
                [
                    record(
                        validation_broker_closure_outcome="needs_validation",
                        validation_broker_negative_evidence=[
                            "validation_command_without_outcome"
                        ],
                        validation_broker_command_ledger=[
                            {
                                "command_kind": "narrow",
                                "command_display_safe": "python3 scripts/validate-validation-broker.py",
                                "scope": "narrow",
                                "outcome": "not_verified",
                                "finished_at_or_order": "4",
                                "covered_paths": ["src/validation_broker/**"],
                                "covered_risk_surfaces": ["validation-broker"],
                                "evidence_strength": "weak",
                            }
                        ],
                    )
                ],
            )
            result = run_review(root)
            payload = self.report_payload(root)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(payload["summary"]["validation_command_without_outcome"], 1)
            self.assertIn(
                "validation_command_without_outcome",
                payload["summary"]["issue_counts"],
            )

    def test_broker_stale_validation_fact_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.seed(
                root,
                [
                    record(
                        validation_broker_closure_outcome="blocked",
                        validation_broker_negative_evidence=["stale_validation"],
                        validation_broker_command_ledger=[
                            {
                                "command_kind": "narrow",
                                "command_display_safe": "python3 scripts/validate-validation-broker.py",
                                "scope": "narrow",
                                "outcome": "stale",
                                "finished_at_or_order": "4",
                                "covered_paths": ["src/validation_broker/**"],
                                "covered_risk_surfaces": ["validation-broker"],
                                "evidence_strength": "negative",
                            }
                        ],
                    )
                ],
            )
            result = run_review(root)
            payload = self.report_payload(root)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(payload["summary"]["stale_validation_reused"], 1)
            self.assertIn("stale_validation_reused", payload["summary"]["issue_counts"])

    def test_adapter_degraded_closure_facts_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.seed(
                root,
                [
                    record(
                        runtime="copilot",
                        adapter_name="copilot",
                        validation_broker_closure_outcome="ready",
                        validation_broker_command_ledger=[
                            {
                                "command_kind": "narrow",
                                "command_display_safe": "python3 scripts/validate-hooks.py",
                                "scope": "narrow",
                                "outcome": "passed",
                                "finished_at_or_order": "7",
                                "covered_paths": ["src/hook-runtime/**"],
                                "covered_risk_surfaces": ["hook-runtime"],
                                "evidence_strength": "strong",
                            }
                        ],
                        adapter_unsupported_checks=["pre_tool_advisory_context"],
                        adapter_degraded_capabilities=[
                            "copilot_pre_tool_advisory_context_unsupported"
                        ],
                        closure_contract_verdict="degraded_ready",
                        closure_contract_residual_risk=[
                            "unsupported runtime checks remain"
                        ],
                    )
                ],
            )
            result = run_review(root)
            payload = self.report_payload(root)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(payload["summary"]["degraded_runtime_adapter_closures"], 1)
            self.assertIn(
                "degraded_runtime_adapter_closure",
                payload["summary"]["issue_counts"],
            )


if __name__ == "__main__":
    unittest.main()
