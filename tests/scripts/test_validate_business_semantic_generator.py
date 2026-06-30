from __future__ import annotations

import importlib.util
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

SCRIPT_PATH = ROOT / "scripts" / "validate-business-semantic-generator.py"
GENERATOR_PATH = ROOT / "scripts" / "generate-business-semantic-actuals.py"
_SPEC = importlib.util.spec_from_file_location("validate_business_semantic_generator_under_test", SCRIPT_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT_PATH}")
VALIDATOR = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = VALIDATOR
_SPEC.loader.exec_module(VALIDATOR)


class ValidateBusinessSemanticGeneratorTests(unittest.TestCase):
    def test_current_generator_passes(self) -> None:
        self.assertEqual(VALIDATOR.validate_path(GENERATOR_PATH), [])

    def test_expected_skills_access_fails(self) -> None:
        source = GENERATOR_PATH.read_text(encoding="utf-8")
        candidate = source + '\n\ndef _bad_oracle_read(case):\n    return case.get("expected_skills")\n'
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp_s:
            candidate_path = Path(tmp_s) / "candidate-generator.py"
            candidate_path.write_text(candidate, encoding="utf-8")

            errors = VALIDATOR.validate_path(candidate_path)

        self.assertTrue(errors)
        self.assertTrue(any("expected_skills" in error for error in errors))

    def test_cli_path_argument_accepts_current_generator(self) -> None:
        buffer = io.StringIO()

        with contextlib.redirect_stdout(buffer):
            rc = VALIDATOR.main(["--path", str(GENERATOR_PATH)])

        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
