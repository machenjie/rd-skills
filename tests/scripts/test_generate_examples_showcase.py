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
    spec = importlib.util.spec_from_file_location("generate_examples_showcase", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class GenerateExamplesShowcaseTests(unittest.TestCase):
    def test_repository_showcase_contains_required_sections(self) -> None:
        module = _load_module()
        rendered = module.render_showcase(ROOT)
        self.assertIn("# Scenario Showcase", rendered)
        self.assertIn("What ordinary agents usually miss", rendered)
        self.assertIn("What ChangeForge route forces", rendered)
        self.assertIn("does not create or require a demo repository", rendered)
        self.assertIn("../evals/routing/backend-auth-idor.yaml", rendered)

    def test_check_mode_catches_stale_output(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "SHOWCASE.md"
            out.write_text("stale\n", encoding="utf-8")
            self.assertEqual(module.main(["--check", "--out", str(out)]), 1)

    def test_check_mode_accepts_generated_output(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "SHOWCASE.md"
            self.assertEqual(module.main(["--out", str(out)]), 0)
            self.assertEqual(module.main(["--check", "--out", str(out)]), 0)


if __name__ == "__main__":
    unittest.main()
