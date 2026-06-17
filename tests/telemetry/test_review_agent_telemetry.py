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
        "changed_path_risk_surfaces": [],
        "command_risk_surfaces": [],
        "closure_risk_surfaces": [],
        "route_manifest_detected": False,
        "required_references_detected": False,
        "validation_command_detected": False,
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

    def _json_report(self, root: Path, repo_hash: str) -> dict:
        report = list((root / repo_hash / "reports").glob("*-agent-telemetry-review.json"))
        self.assertTrue(report)
        return json.loads(report[0].read_text(encoding="utf-8"))

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

    def test_detects_unverified_completion_claim(self) -> None:
        # Completion language at stop with an engineering surface but no validation
        # evidence must surface unverified_completion_claim.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "telemetry"
            repo_hash = "repohashaaaaaaaaaaaaaaaa"
            self._seed(
                root,
                repo_hash,
                [
                    _record(changed_paths=["src/pricing.py"]),
                    _record(
                        hook_name="stop_closure_gate",
                        event_name="Stop",
                        changed_paths=["src/pricing.py"],
                        route_manifest_detected=True,
                        completion_language_detected=True,
                        validation_evidence_detected=False,
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
            self.assertIn("unverified_completion_claim", text)
            report_text = report[0].read_text(encoding="utf-8")
            self.assertIn("- unverified completion claims: 1", report_text)
            self.assertIn("- pressure candidate suggestions:", report_text)

    def test_completion_claim_with_validation_is_not_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "telemetry"
            repo_hash = "repohashaaaaaaaaaaaaaaaa"
            self._seed(
                root,
                repo_hash,
                [
                    _record(changed_paths=["src/pricing.py"]),
                    _record(
                        hook_name="stop_closure_gate",
                        event_name="Stop",
                        changed_paths=["src/pricing.py"],
                        route_manifest_detected=True,
                        completion_language_detected=True,
                        validation_evidence_detected=True,
                        residual_risk_detected=True,
                    ),
                ],
            )
            result = _run("--telemetry-root", str(root))
            suggestions = list((root / repo_hash / "suggestions").glob("*-suggestions.yaml"))
            text = suggestions[0].read_text(encoding="utf-8") if suggestions else ""
            self.assertNotIn("unverified_completion_claim", text)

    def test_reports_route_manifest_adoption_rate(self) -> None:
        # One code+stop session emits a manifest, one does not: adoption is 1/2.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "telemetry"
            repo_hash = "repohashaaaaaaaaaaaaaaaa"
            self._seed(
                root,
                repo_hash,
                [
                    _record(session_id="s1", changed_paths=["src/a.py"]),
                    _record(
                        session_id="s1",
                        hook_name="stop_closure_gate",
                        event_name="Stop",
                        changed_paths=["src/a.py"],
                        route_manifest_detected=True,
                        validation_evidence_detected=True,
                        residual_risk_detected=True,
                    ),
                    _record(session_id="s2", changed_paths=["src/b.py"]),
                    _record(
                        session_id="s2",
                        hook_name="stop_closure_gate",
                        event_name="Stop",
                        changed_paths=["src/b.py"],
                        route_manifest_detected=False,
                    ),
                ],
            )
            json_result = _run("--telemetry-root", str(root), "--format", "json")
            self.assertEqual(json_result.returncode, 0)
            report = list((root / repo_hash / "reports").glob("*-agent-telemetry-review.json"))
            self.assertTrue(report)
            summary = json.loads(report[0].read_text(encoding="utf-8"))["summary"]
            self.assertEqual(summary["code_change_closures"], 2)
            self.assertEqual(summary["engineering_surface_closures"], 2)
            self.assertEqual(summary["route_manifest_closures"], 1)
            self.assertEqual(summary["route_manifest_adoption"], 0.5)

            md_result = _run("--telemetry-root", str(root))
            self.assertEqual(md_result.returncode, 0)
            md_report = list((root / repo_hash / "reports").glob("*-agent-telemetry-review.md"))
            self.assertTrue(md_report)
            self.assertIn(
                "- route manifest adoption: 1/2 (50%)",
                md_report[0].read_text(encoding="utf-8"),
            )

    def test_no_manifest_capability_misses_marked_cascading(self) -> None:
        # A no-manifest code session raises missed_router as the actionable root
        # cause; its capability/structure misses are downstream cascades of it.
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
                        changed_paths=["src/services/order_service.go"],
                        risk_surfaces=["cache"],
                        route_manifest_detected=False,
                        hook_findings=structure,
                    ),
                ],
            )
            result = _run("--telemetry-root", str(root), "--format", "json")
            self.assertEqual(result.returncode, 0)
            report = list((root / repo_hash / "reports").glob("*-agent-telemetry-review.json"))
            self.assertTrue(report)
            data = json.loads(report[0].read_text(encoding="utf-8"))
            by_type = {s["type"]: s for s in data["suggestions"]}
            self.assertIn("missed_router", by_type)
            self.assertFalse(by_type["missed_router"]["cascading"])
            for cascading_type in (
                "missed_language_capability",
                "missed_middleware_capability",
                "missed_implementation_structure",
            ):
                self.assertIn(cascading_type, by_type)
                self.assertTrue(by_type[cascading_type]["cascading"], cascading_type)
                self.assertEqual(
                    by_type[cascading_type]["cascading_from"], "missed_router"
                )
            self.assertGreaterEqual(data["summary"]["cascading_suggestions"], 3)
            self.assertGreaterEqual(data["summary"]["primary_suggestions"], 1)

    def test_manifest_present_capability_miss_stays_primary(self) -> None:
        # When a manifest is present but omits a capability, the miss is a real,
        # independently actionable gap and must not be marked cascading.
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
                        route_manifest_detected=True,
                        required_references_detected=True,
                        validation_evidence_detected=True,
                        residual_risk_detected=True,
                        manifest_selected_capabilities=["logging-error-handling"],
                    ),
                ],
            )
            result = _run("--telemetry-root", str(root), "--format", "json")
            self.assertEqual(result.returncode, 0)
            report = list((root / repo_hash / "reports").glob("*-agent-telemetry-review.json"))
            data = json.loads(report[0].read_text(encoding="utf-8"))
            by_type = {s["type"]: s for s in data["suggestions"]}
            self.assertIn("missed_language_capability", by_type)
            self.assertFalse(by_type["missed_language_capability"]["cascading"])

    def test_read_only_command_risk_surface_not_treated_as_code_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "telemetry"
            repo_hash = "repohashaaaaaaaaaaaaaaaa"
            self._seed(
                root,
                repo_hash,
                [
                    _record(
                        hook_name="risk_surface_gate",
                        tool_name="Bash",
                        command_program="sed",
                        risk_surfaces=["data-api"],
                    ),
                    _record(
                        hook_name="stop_closure_gate",
                        event_name="Stop",
                        risk_surfaces=["data-api"],
                        route_manifest_detected=False,
                    ),
                ],
            )
            result = _run("--telemetry-root", str(root), "--format", "json")
            self.assertEqual(result.returncode, 0)
            report = list((root / repo_hash / "reports").glob("*-agent-telemetry-review.json"))
            data = json.loads(report[0].read_text(encoding="utf-8"))
            self.assertEqual(data["summary"]["code_change_closures"], 0)
            self.assertEqual(data["summary"]["engineering_surface_closures"], 0)
            self.assertEqual(data["summary"]["read_only_risk_surface_closures"], 1)
            self.assertNotIn("missed_router", data["summary"]["issue_counts"])

    def test_legacy_jq_command_risk_surface_not_treated_as_code_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "telemetry"
            repo_hash = "repohashaaaaaaaaaaaaaaaa"
            self._seed(
                root,
                repo_hash,
                [
                    _record(
                        hook_name="risk_surface_gate",
                        tool_name="Bash",
                        command_program="jq",
                        risk_surfaces=["data-api"],
                    ),
                    _record(
                        hook_name="stop_closure_gate",
                        event_name="Stop",
                        risk_surfaces=["data-api"],
                        route_manifest_detected=False,
                    ),
                ],
            )
            result = _run("--telemetry-root", str(root), "--format", "json")
            self.assertEqual(result.returncode, 0)
            data = self._json_report(root, repo_hash)
            self.assertEqual(data["summary"]["engineering_surface_closures"], 0)
            self.assertEqual(data["summary"]["read_only_risk_surface_closures"], 1)
            self.assertNotIn("missed_router", data["summary"]["issue_counts"])

    def test_validation_command_without_outcome_is_distinct_from_no_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "telemetry"
            repo_hash = "repohashaaaaaaaaaaaaaaaa"
            self._seed(
                root,
                repo_hash,
                [
                    _record(
                        changed_paths=["src/pricing.py"],
                        hook_name="risk_surface_gate",
                        validation_command_detected=True,
                    ),
                    _record(
                        hook_name="stop_closure_gate",
                        event_name="Stop",
                        changed_paths=["src/pricing.py"],
                        validation_evidence_detected=False,
                    ),
                ],
            )
            result = _run("--telemetry-root", str(root), "--format", "json")
            self.assertEqual(result.returncode, 0)
            report = list((root / repo_hash / "reports").glob("*-agent-telemetry-review.json"))
            data = json.loads(report[0].read_text(encoding="utf-8"))
            by_type = {s["type"]: s for s in data["suggestions"]}
            self.assertIn("validation_command_without_outcome", by_type)
            self.assertNotIn("missed_validation_evidence", by_type)
            self.assertEqual(data["summary"]["validation_command_without_outcome"], 1)
            self.assertIn("weighted_issue_scores", data["summary"])
            self.assertGreater(
                data["summary"]["weighted_issue_scores"]["validation_command_without_outcome"],
                0,
            )

    def test_mixed_legacy_and_split_telemetry_keeps_legacy_closure_risk(self) -> None:
        # A legacy mutating command risk must survive a later split-format
        # read-only command record in the same review window.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "telemetry"
            repo_hash = "repohashaaaaaaaaaaaaaaaa"
            self._seed(
                root,
                repo_hash,
                [
                    _record(
                        hook_name="risk_surface_gate",
                        tool_name="Bash",
                        command_program="python",
                        risk_surfaces=["cache"],
                    ),
                    _record(
                        hook_name="risk_surface_gate",
                        tool_name="Bash",
                        command_program="sed",
                        command_risk_surfaces=["data-api"],
                        closure_risk_surfaces=[],
                    ),
                    _record(
                        hook_name="stop_closure_gate",
                        event_name="Stop",
                        route_manifest_detected=False,
                    ),
                ],
            )
            result = _run("--telemetry-root", str(root), "--format", "json")
            self.assertEqual(result.returncode, 0)
            data = self._json_report(root, repo_hash)
            self.assertEqual(data["summary"]["engineering_surface_closures"], 1)
            self.assertEqual(data["summary"]["risk_surface_closures"], 1)
            self.assertIn("missed_router", data["summary"]["issue_counts"])
            self.assertEqual(data["summary"]["read_only_risk_surface_closures"], 0)

    def test_recency_default_half_life_weights_two_day_old_issue_at_half(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "telemetry"
            repo_hash = "repohashaaaaaaaaaaaaaaaa"
            self._seed(
                root,
                repo_hash,
                [
                    _record(
                        session_id="old",
                        timestamp_utc="2026-06-03T10:00:00+00:00",
                        hook_name="stop_closure_gate",
                        event_name="Stop",
                        changed_paths=["README"],
                    ),
                    _record(
                        session_id="new",
                        timestamp_utc="2026-06-05T10:00:00+00:00",
                        hook_name="stop_closure_gate",
                        event_name="Stop",
                        changed_paths=["README"],
                    ),
                ],
            )
            result = _run("--telemetry-root", str(root), "--format", "json")
            self.assertEqual(result.returncode, 0)
            data = self._json_report(root, repo_hash)
            routers = {
                suggestion["affected_session"]: suggestion
                for suggestion in data["suggestions"]
                if suggestion["type"] == "missed_router"
            }
            self.assertEqual(routers["old"]["recency_weight"], 0.5)
            self.assertEqual(routers["old"]["priority_score"], 1.5)
            self.assertEqual(routers["new"]["recency_weight"], 1.0)
            self.assertEqual(routers["new"]["priority_score"], 3.0)
            self.assertEqual(data["summary"]["weighted_issue_scores"]["missed_router"], 4.5)

    def test_recency_half_life_zero_disables_decay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "telemetry"
            repo_hash = "repohashaaaaaaaaaaaaaaaa"
            self._seed(
                root,
                repo_hash,
                [
                    _record(
                        session_id="old",
                        timestamp_utc="2026-06-01T10:00:00+00:00",
                        hook_name="stop_closure_gate",
                        event_name="Stop",
                        changed_paths=["README"],
                    ),
                    _record(
                        session_id="new",
                        timestamp_utc="2026-06-05T10:00:00+00:00",
                        hook_name="stop_closure_gate",
                        event_name="Stop",
                        changed_paths=["README"],
                    ),
                ],
            )
            result = _run(
                "--telemetry-root",
                str(root),
                "--format",
                "json",
                "--recency-half-life-days",
                "0",
            )
            self.assertEqual(result.returncode, 0)
            data = self._json_report(root, repo_hash)
            routers = [
                suggestion
                for suggestion in data["suggestions"]
                if suggestion["type"] == "missed_router"
            ]
            self.assertEqual([suggestion["recency_weight"] for suggestion in routers], [1.0, 1.0])
            self.assertEqual(data["summary"]["weighted_issue_scores"]["missed_router"], 6.0)

    def test_recent_24h_boundary_is_inclusive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "telemetry"
            repo_hash = "repohashaaaaaaaaaaaaaaaa"
            self._seed(
                root,
                repo_hash,
                [
                    _record(
                        session_id="just_old",
                        timestamp_utc="2026-06-04T09:59:59+00:00",
                        hook_name="stop_closure_gate",
                        event_name="Stop",
                        changed_paths=["README"],
                    ),
                    _record(
                        session_id="boundary",
                        timestamp_utc="2026-06-04T10:00:00+00:00",
                        hook_name="stop_closure_gate",
                        event_name="Stop",
                        changed_paths=["README"],
                    ),
                    _record(
                        session_id="latest",
                        timestamp_utc="2026-06-05T10:00:00+00:00",
                        hook_name="stop_closure_gate",
                        event_name="Stop",
                        changed_paths=["README"],
                    ),
                ],
            )
            result = _run("--telemetry-root", str(root), "--format", "json")
            self.assertEqual(result.returncode, 0)
            data = self._json_report(root, repo_hash)
            routers = {
                suggestion["affected_session"]: suggestion
                for suggestion in data["suggestions"]
                if suggestion["type"] == "missed_router"
            }
            self.assertFalse(routers["just_old"]["recent_24h"])
            self.assertTrue(routers["boundary"]["recent_24h"])
            self.assertTrue(routers["latest"]["recent_24h"])
            self.assertEqual(data["summary"]["recent_24h_issue_counts"]["missed_router"], 2)

    def test_recency_weighted_markdown_order_is_stable_for_equal_scores(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "telemetry"
            repo_hash = "repohashaaaaaaaaaaaaaaaa"
            self._seed(
                root,
                repo_hash,
                [
                    _record(
                        hook_name="stop_closure_gate",
                        event_name="Stop",
                        changed_paths=["README"],
                    ),
                ],
            )
            result = _run("--telemetry-root", str(root))
            self.assertEqual(result.returncode, 0)
            report = list((root / repo_hash / "reports").glob("*-agent-telemetry-review.md"))
            self.assertTrue(report)
            text = report[0].read_text(encoding="utf-8")
            self.assertLess(
                text.index("- missed_router: priority 3"),
                text.index("- missed_validation_evidence: priority 3"),
            )


if __name__ == "__main__":
    unittest.main()
