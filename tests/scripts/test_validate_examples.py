from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate-examples.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("validate_examples", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ValidateExamplesTests(unittest.TestCase):
    def test_repository_examples_validate(self) -> None:
        module = _load_module()
        self.assertEqual(module.validate_examples(ROOT), [])

    def test_unknown_capability_is_reported(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src" / "registry").mkdir(parents=True)
            (root / "src" / "registry" / "skills.yaml").write_text(
                "skills:\n  - name: backend-change-builder\n    path: src/professional-skills/backend-change-builder\n",
                encoding="utf-8",
            )
            (root / "src" / "registry" / "domain-extensions.yaml").write_text(
                "domain_extensions: []\n",
                encoding="utf-8",
            )
            (root / "src" / "registry" / "capabilities.yaml").write_text(
                "capabilities:\n  - name: regression-testing\n    path: src/foundation/capabilities/regression-testing\n",
                encoding="utf-8",
            )
            scenario = root / "examples" / "01-sample"
            scenario.mkdir(parents=True)
            (root / "examples" / "README.md").write_text("# Examples\n", encoding="utf-8")
            (scenario / "prompt.md").write_text("Change a backend permission path.\n", encoding="utf-8")
            (scenario / "expected-route.md").write_text(
                "```yaml\n"
                "selected_skills:\n"
                "  - backend-change-builder\n"
                "selected_capabilities:\n"
                "  - invented-capability\n"
                "required_quality_gates:\n"
                "  - test gate\n"
                "```\n",
                encoding="utf-8",
            )
            (scenario / "expected-evidence.md").write_text(
                "read before plan\nTDD\nvalidation evidence\nindependent review\nresidual risk\nhandoff\n",
                encoding="utf-8",
            )
            errors = module.validate_examples(root)
        self.assertTrue(any("unknown capability" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
