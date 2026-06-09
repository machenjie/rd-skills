from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCTOR_SCRIPT = ROOT / "installers" / "doctor.py"


class DoctorTelemetryTests(unittest.TestCase):
    def test_telemetry_summary_includes_unverified_completion_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_s:
            tmp = Path(tmp_s)
            report = tmp / "report.json"
            report.write_text(
                json.dumps(
                    {
                        "summary": {
                            "sessions": 2,
                            "missed_router": 0,
                            "missed_reference": 0,
                            "missed_gate": 0,
                            "validation_evidence_missing": 1,
                            "unverified_completion_claims": 1,
                            "incomplete_required_references": 1,
                            "residual_risk_missing": 0,
                            "pressure_candidate_suggestions": 2,
                            "high_severity_suggestions": 1,
                        }
                    }
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(DOCTOR_SCRIPT),
                    "--agent",
                    "codex",
                    "--scope",
                    "project",
                    "--target",
                    str(tmp),
                    "--telemetry-report",
                    str(report),
                ],
                text=True,
                capture_output=True,
                cwd=str(ROOT),
                env=os.environ.copy(),
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("unverified completion claims: 1", result.stdout)
        self.assertIn("incomplete required references: 1", result.stdout)
        self.assertIn("pressure candidate suggestions: 2", result.stdout)


if __name__ == "__main__":
    unittest.main()
