from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROMOTE_SCRIPT = ROOT / "scripts" / "promote-telemetry-suggestion.py"

SUGGESTIONS = """generated_from_telemetry: true
requires_human_review: true
suggestions:
  - id: missed-router-abc123-0
    type: missed_router
    severity: high
    evidence: 1 changed path but no manifest
    affected_session: s1
    suggested_action: Require change-forge-router
    promotion_target: evals/agent-behavior/samples
    requires_human_review: true
  - id: missed-language-capability-abc123-3
    type: missed_language_capability
    severity: medium
    evidence: go files changed
    affected_session: s1
    suggested_action: Select go-professional-usage
    promotion_target: evals/routing
    requires_human_review: true
  - id: bad-target-abc123-9
    type: missed_router
    severity: high
    evidence: malformed target
    affected_session: s1
    suggested_action: do not write to rules
    promotion_target: src/registry/routing-rules.yaml
    requires_human_review: true
"""


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PROMOTE_SCRIPT), *args],
        text=True,
        capture_output=True,
        cwd=str(ROOT),
        env=os.environ.copy(),
        check=False,
    )


class PromoteSuggestionTests(unittest.TestCase):
    def _write_suggestions(self, tmp: Path) -> Path:
        path = tmp / "suggestions.yaml"
        path.write_text(SUGGESTIONS, encoding="utf-8")
        return path

    def test_dry_run_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_s:
            tmp = Path(tmp_s)
            suggestions = self._write_suggestions(tmp)
            result = _run(
                "--id",
                "missed-router-abc123-0",
                "--suggestions",
                str(suggestions),
                "--repo-root",
                str(tmp),
            )
            written = list(tmp.rglob("telemetry-*.yaml"))
            self.assertEqual(result.returncode, 0)
            self.assertIn("DRY RUN", result.stdout)
            self.assertEqual(written, [])

    def test_write_generates_candidate_with_headers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_s:
            tmp = Path(tmp_s)
            suggestions = self._write_suggestions(tmp)
            result = _run(
                "--id",
                "missed-language-capability-abc123-3",
                "--suggestions",
                str(suggestions),
                "--repo-root",
                str(tmp),
                "--write",
            )
            generated = tmp / "evals" / "routing" / "telemetry-missed-language-capability-abc123-3.yaml"
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(generated.is_file())
            text = generated.read_text(encoding="utf-8")
            self.assertIn("generated_from_telemetry: true", text)
            self.assertIn("requires_human_review: true", text)
            self.assertIn("source_suggestion_id: missed-language-capability-abc123-3", text)

    def test_refuses_forbidden_promotion_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_s:
            tmp = Path(tmp_s)
            suggestions = self._write_suggestions(tmp)
            result = _run(
                "--id",
                "bad-target-abc123-9",
                "--suggestions",
                str(suggestions),
                "--repo-root",
                str(tmp),
                "--write",
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("unsupported promotion_target", result.stderr)

    def test_unknown_id_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_s:
            tmp = Path(tmp_s)
            suggestions = self._write_suggestions(tmp)
            result = _run("--id", "does-not-exist", "--suggestions", str(suggestions))
            self.assertEqual(result.returncode, 1)
            self.assertIn("not found", result.stderr)


if __name__ == "__main__":
    unittest.main()
