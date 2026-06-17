from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate-productization-assets.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("validate_productization_assets", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ValidateProductizationAssetsTests(unittest.TestCase):
    def test_repository_productization_assets_validate(self) -> None:
        module = _load_module()
        self.assertEqual(module.validate_productization_assets(ROOT), [])


if __name__ == "__main__":
    unittest.main()
