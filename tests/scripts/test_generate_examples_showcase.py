from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "generate-examples-showcase.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(
        "generate_examples_showcase", SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class GenerateExamplesShowcaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_multiline_evidence_bullet_preserves_continuation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "expected-evidence.md"
            path.write_text(
                "# Expected Evidence\n\n"
                "- handoff: include `actual diff`, validation,\n"
                "  unverified scope, residual risk, and next step.\n"
                "- review: use `quality-test-gate`.\n",
                encoding="utf-8",
            )

            self.assertEqual(
                (
                    "handoff: include `actual diff`, validation, unverified scope, "
                    "residual risk, and next step.",
                    "review: use `quality-test-gate`.",
                ),
                self.module._evidence(path),
            )

    def test_rendered_showcase_uses_nested_markdown_evidence(self) -> None:
        rendered = self.module.render_showcase(ROOT)

        self.assertIn("- Evidence obligations:\n  - read before plan:", rendered)
        self.assertIn(
            "compatibility note, unverified scope, residual risk, and next step.",
            rendered,
        )
        self.assertIn(
            "rollback result, validation output, unverified scope, residual risk, "
            "and owner decision if a breaking change remains.",
            rendered,
        )
        self.assertNotIn("- Evidence obligations: `", rendered)

    def test_check_mode_catches_stale_and_accepts_generated_output(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            out = Path(raw) / "SHOWCASE.md"
            out.write_text("stale\n", encoding="utf-8")
            self.assertEqual(self.module.main(["--out", str(out), "--check"]), 1)
            self.assertEqual(self.module.main(["--out", str(out)]), 0)
            self.assertEqual(self.module.main(["--out", str(out), "--check"]), 0)


if __name__ == "__main__":
    unittest.main()
