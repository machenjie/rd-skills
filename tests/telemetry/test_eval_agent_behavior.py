from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVAL_SCRIPT = ROOT / "scripts" / "eval-agent-behavior.py"

PASSING_SAMPLE = """id: sample-pass
description: passing sample
prompt: do a backend auth fix
validation_evidence: true
residual_risk: true
expected:
  selected_skills:
    - backend-change-builder
  forbidden_skills:
    - frontend-change-builder
  selected_capabilities:
    - authentication-authorization
  required_references:
    - references/routing-rules.md
  required_quality_gates:
    - security gate
manifest:
  schema_version: 1
  selected_skills:
    - backend-change-builder
    - security-privacy-gate
  selected_capabilities:
    - authentication-authorization
  selected_domain_extensions: []
  required_references:
    - references/routing-rules.md
    - references/skill-registry.md
    - references/capability-index.md
    - references/domain-extension-index.md
  required_quality_gates:
    - security gate
  skipped_quality_gates:
    - delivery gate => no deployment change
"""

FORBIDDEN_SAMPLE = """id: sample-forbidden
description: forbidden skill present
prompt: do something
validation_evidence: true
residual_risk: true
expected:
  selected_skills:
    - backend-change-builder
  forbidden_skills:
    - frontend-change-builder
  selected_capabilities: []
  required_references: []
  required_quality_gates: []
manifest:
  schema_version: 1
  selected_skills:
    - backend-change-builder
    - frontend-change-builder
  selected_capabilities: []
  selected_domain_extensions: []
  required_references: []
  required_quality_gates: []
  skipped_quality_gates: []
"""


def _run(samples_dir: Path, output_dir: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    return subprocess.run(
        [
            sys.executable,
            str(EVAL_SCRIPT),
            "--samples-dir",
            str(samples_dir),
            "--output-dir",
            str(output_dir),
            "--format",
            "json",
        ],
        text=True,
        capture_output=True,
        cwd=str(ROOT),
        env=env,
        check=False,
    )


class EvalAgentBehaviorTests(unittest.TestCase):
    def test_no_samples_found_returns_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            samples = Path(tmp) / "samples"
            samples.mkdir()
            result = _run(samples, Path(tmp) / "out")
        self.assertEqual(result.returncode, 0)
        self.assertIn("no samples found", result.stdout)

    def test_passing_sample_scores_high(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            samples = Path(tmp) / "samples"
            samples.mkdir()
            (samples / "pass.yaml").write_text(PASSING_SAMPLE, encoding="utf-8")
            result = _run(samples, Path(tmp) / "out")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("route_recall=1.00", result.stdout)
        self.assertIn("gate_closure=1.00", result.stdout)

    def test_forbidden_skill_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            samples = Path(tmp) / "samples"
            samples.mkdir()
            (samples / "forbidden.yaml").write_text(FORBIDDEN_SAMPLE, encoding="utf-8")
            result = _run(samples, Path(tmp) / "out")
        self.assertEqual(result.returncode, 1)
        self.assertIn("forbidden", result.stderr)

    def test_committed_samples_pass(self) -> None:
        # The repository's own samples must remain valid for the standard
        # validation workflow.
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(EVAL_SCRIPT), "--output-dir", str(tmp)],
                text=True,
                capture_output=True,
                cwd=str(ROOT),
                env=os.environ.copy(),
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
