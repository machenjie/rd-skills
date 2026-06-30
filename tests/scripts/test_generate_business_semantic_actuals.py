from __future__ import annotations

import contextlib
import importlib.util
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

SCRIPT_PATH = ROOT / "scripts" / "generate-business-semantic-actuals.py"
_SPEC = importlib.util.spec_from_file_location("generate_business_semantic_actuals_under_test", SCRIPT_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT_PATH}")
GENERATOR = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = GENERATOR
_SPEC.loader.exec_module(GENERATOR)


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

            actual_path = next(sorted(output_dir.glob("*.actual.yaml")))
            actual_path.write_text(
                actual_path.read_text(encoding="utf-8").replace(
                    "generation_mode: deterministic",
                    "generation_mode: stale",
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
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
        rc = GENERATOR.main(argv)
    return rc, buffer.getvalue()


if __name__ == "__main__":
    unittest.main()
