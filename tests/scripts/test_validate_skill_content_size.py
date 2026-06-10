from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate-skill-content-size.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("validate_skill_content_size", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ValidateSkillContentSizeTests(unittest.TestCase):
    def test_empty_exceptions_file_is_valid(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            path = Path(raw) / "exceptions.yaml"
            path.write_text("exceptions: []\n", encoding="utf-8")
            module.EXCEPTIONS_FILE = path
            errors: list[str] = []
            loaded = module.load_exceptions(errors)
        self.assertEqual(errors, [])
        self.assertEqual(loaded, {})

    def test_exception_requires_specific_metadata_and_reference_rationale(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            path = Path(raw) / "exceptions.yaml"
            path.write_text(
                "\n".join(
                    [
                        "exceptions:",
                        "  - path: README.md",
                        "    allow:",
                        "      - body_lines",
                        "    reason: professionalism enhancement",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            module.EXCEPTIONS_FILE = path
            errors: list[str] = []
            module.load_exceptions(errors)
        self.assertTrue(any("generic reason" in error for error in errors))
        self.assertTrue(any("owner" in error for error in errors))
        self.assertTrue(any("review_after" in error for error in errors))
        self.assertTrue(any("mitigation" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
