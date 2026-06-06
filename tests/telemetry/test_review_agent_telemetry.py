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
        "hook_name": "post_edit_structure_gate",
        "event_name": "PostToolUse",
        "session_id": "s1",
        "mode": "warn",
        "tool_name": "apply_patch",
        "changed_paths": [],
        "added_paths": [],
        "hook_findings": {},
        "suggested_skills": [],
        "suggested_capabilities": [],
        "suggested_gates": [],
        "suggested_domain_extensions": [],
        "risk_surfaces": [],
        "route_manifest_detected": False,
        "required_references_detected": False,
        "validation_evidence_detected": False,
        "residual_risk_detected": False,
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


class ReviewAgentTelemetryTests(unittest.TestCase):
    def _seed(self, root: Path, repo_hash: str, rows: list[str]) -> None:
        sessions = root / repo_hash / "sessions"
        sessions.mkdir(parents=True, exist_ok=True)
        (sessions / "2026-06-05.jsonl").write_text("\n".join(rows) + "\n", encoding="utf-8")

    def test_no_samples_found_returns_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = _run("--telemetry-root", str(Path(tmp) / "telemetry"))
            self.assertEqual(result.returncode, 0)
            self.assertIn("no samples found", result.stdout)

    def test_detects_missed_router_and_writes_suggestions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "telemetry"
            repo_hash = "repohashaaaaaaaaaaaaaaaa"
            self._seed(
                root,
                repo_hash,
                [
                    _record(changed_paths=["src/services/order_service.go"]),
                    _record(
                        hook_name="stop_closure_gate",
                        event_name="Stop",
                        changed_paths=["src/services/order_service.go"],
                    ),
                ],
            )
            result = _run("--telemetry-root", str(root))
            suggestions = list((root / repo_hash / "suggestions").glob("*-suggestions.yaml"))
            report = list((root / repo_hash / "reports").glob("*-agent-telemetry-review.md"))
            self.assertEqual(result.returncode, 0)
            self.assertTrue(suggestions)
            self.assertTrue(report)
            text = suggestions[0].read_text(encoding="utf-8")
            self.assertIn("generated_from_telemetry: true", text)
            self.assertIn("requires_human_review: true", text)
            self.assertIn("missed_router", text)

    def test_fail_on_high_severity_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "telemetry"
            self._seed(
                root,
                "repohashaaaaaaaaaaaaaaaa",
                [
                    _record(changed_paths=["src/x.go"]),
                    _record(hook_name="stop_closure_gate", event_name="Stop", changed_paths=["src/x.go"]),
                ],
            )
            result = _run("--telemetry-root", str(root), "--fail-on-high-severity")
            self.assertEqual(result.returncode, 1)

    def test_detects_missing_capability_even_with_manifest(self) -> None:
        # A manifest is present and closure evidence is complete, but the
        # manifest omits the go language capability and
        # implementation-structure-design, and there is no stage manifest.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "telemetry"
            repo_hash = "repohashaaaaaaaaaaaaaaaa"
            structure = {"structure_findings": ["src/services/order_service.go: new file"]}
            self._seed(
                root,
                repo_hash,
                [
                    _record(
                        changed_paths=["src/services/order_service.go"],
                        hook_findings=structure,
                    ),
                    _record(
                        hook_name="stop_closure_gate",
                        event_name="Stop",
                        changed_paths=[
                            "src/services/order_service.go",
                            "src/services/order_repo.go",
                        ],
                        route_manifest_detected=True,
                        required_references_detected=True,
                        validation_evidence_detected=True,
                        residual_risk_detected=True,
                        stage_manifest_detected=False,
                        manifest_selected_capabilities=["logging-error-handling"],
                        manifest_required_quality_gates=["test gate"],
                        hook_findings=structure,
                    ),
                ],
            )
            result = _run("--telemetry-root", str(root), "--format", "json")
            self.assertEqual(result.returncode, 0)
            report = list((root / repo_hash / "reports").glob("*-agent-telemetry-review.json"))
            self.assertTrue(report)
            text = report[0].read_text(encoding="utf-8")
            self.assertIn("missed_language_capability", text)
            self.assertIn("missed_implementation_structure", text)
            self.assertIn("missed_stage_manifest", text)
            # A route manifest was present, so this is not a missed-router case.
            self.assertNotIn('"type": "missed_router"', text)


if __name__ == "__main__":
    unittest.main()
