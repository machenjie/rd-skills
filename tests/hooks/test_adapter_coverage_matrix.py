from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class AdapterCoverageMatrixTests(unittest.TestCase):
    def test_validate_hooks_outputs_runtime_coverage_matrix(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/validate-hooks.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("runtime coverage matrix:", result.stdout)
        self.assertIn("copilot", result.stdout)
        self.assertIn("pre_tool_advisory_context", result.stdout)

    def test_doctor_outputs_runtime_coverage_matrix(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "installers/doctor.py",
                "--agent",
                "codex",
                "--scope",
                "user",
                "--profile",
                "recommended",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertIn("doctor: runtime coverage matrix", result.stdout)
        self.assertIn("runtime coverage matrix:", result.stdout)


if __name__ == "__main__":
    unittest.main()
