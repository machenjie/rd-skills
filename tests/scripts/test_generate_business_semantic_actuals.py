from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

SCRIPT_PATH = ROOT / "scripts" / "generate-business-semantic-actuals.py"


class GenerateBusinessSemanticActualsTests(unittest.TestCase):
    def test_check_checked_in_actual_outputs_pass(self) -> None:
        rc, output = _run_generator(["--check"])

        self.assertEqual(rc, 0, output)

    def test_check_detects_stale_temp_actual_output(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp_s:
            tmp = Path(tmp_s)
            eval_dir = tmp / "evals" / "business-semantic"
            output_dir = tmp / "evals" / "business-semantic-outputs"
            shutil.copytree(ROOT / "evals" / "business-semantic", eval_dir)
            shutil.copytree(ROOT / "evals" / "business-semantic-outputs", output_dir)

            actual_path = sorted(output_dir.glob("*.actual.yaml"))[0]
            actual_path.write_text(
                actual_path.read_text(encoding="utf-8").replace(
                    'generation_mode: "deterministic"',
                    'generation_mode: "stale"',
                    1,
                ),
                encoding="utf-8",
            )

            rc, output = _run_generator(
                ["--check", "--eval-dir", str(eval_dir), "--output-dir", str(output_dir)]
            )

        self.assertNotEqual(rc, 0)
        self.assertIn("stale", output)


def _run_generator(argv: list[str]) -> tuple[int, str]:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *argv],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.returncode, completed.stdout + completed.stderr


if __name__ == "__main__":
    unittest.main()
