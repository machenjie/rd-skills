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


def _record(**fields: object) -> str:
    base = {
        "schema_version": "1",
        "timestamp_utc": "2026-06-05T10:00:00+00:00",
        "repo_hash": "repohashaaaaaaaaaaaaaaaa",
        "cwd_hash": "cwd",
        "runtime": "codex",
        "hook_name": "stop_closure_gate",
        "event_name": "Stop",
        "session_id": "s1",
        "mode": "warn",
        "tool_name": "",
        "changed_paths": ["src/app.py"],
        "added_paths": [],
        "hook_findings": {},
        "suggested_skills": [],
        "suggested_capabilities": [],
        "suggested_gates": [],
        "suggested_domain_extensions": [],
        "risk_surfaces": [],
        "changed_path_risk_surfaces": [],
        "command_risk_surfaces": [],
        "closure_risk_surfaces": [],
        "route_manifest_detected": True,
        "required_references_detected": True,
        "validation_command_detected": True,
        "validation_evidence_detected": False,
        "validation_broker_negative_evidence": [],
        "residual_risk_detected": True,
    }
    base.update(fields)
    return json.dumps(base)


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("XDG_CACHE_HOME", None)
    return subprocess.run(
        [sys.executable, str(REVIEW_SCRIPT), *args],
        text=True,
        capture_output=True,
        cwd=str(ROOT),
        env=env,
        check=False,
    )


class MemoryCandidateGenerationTests(unittest.TestCase):
    def _seed(self, root: Path, repo_hash: str, rows: list[str]) -> None:
        sessions = root / repo_hash / "sessions"
        sessions.mkdir(parents=True, exist_ok=True)
        (sessions / "2026-06-05.jsonl").write_text("\n".join(rows) + "\n", encoding="utf-8")

    def test_stale_validation_and_hook_candidates_emit_memory_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "telemetry"
            repo_hash = "repohashaaaaaaaaaaaaaaaa"
            self._seed(
                root,
                repo_hash,
                [
                    _record(
                        validation_broker_negative_evidence=["stale_validation"],
                        hook_findings={"structure_findings": ["tests/fixture.py: generated fixture path"]},
                    ),
                ],
            )
            result = _run("--telemetry-root", str(root), "--format", "json")
            self.assertEqual(result.returncode, 0, result.stderr)
            report_path = next((root / repo_hash / "reports").glob("*-agent-telemetry-review.json"))
            report = json.loads(report_path.read_text(encoding="utf-8"))
        candidate_types = {item["type"] for item in report["memory_candidates"]}
        self.assertIn("validation_pattern", candidate_types)
        self.assertTrue(all(item["requires_human_review"] for item in report["memory_candidates"]))
        self.assertEqual(report["summary"]["memory_candidate_suggestions"], len(report["memory_candidates"]))

    def test_repeated_failed_path_emits_repeat_failure_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "telemetry"
            repo_hash = "repohashaaaaaaaaaaaaaaaa"
            self._seed(
                root,
                repo_hash,
                [
                    _record(session_id="s1", validation_result_outcome="fail"),
                    _record(session_id="s2", validation_result_outcome="fail"),
                ],
            )
            result = _run("--telemetry-root", str(root), "--format", "json")
            self.assertEqual(result.returncode, 0, result.stderr)
            report_path = next((root / repo_hash / "reports").glob("*-agent-telemetry-review.json"))
            report = json.loads(report_path.read_text(encoding="utf-8"))
        repeat = [item for item in report["memory_candidates"] if item["type"] == "repeat_failure"]
        self.assertEqual(repeat[0]["bounded_paths"], ["src/app.py"])
        self.assertEqual(repeat[0]["promotion_target"], "memory")


if __name__ == "__main__":
    unittest.main()
