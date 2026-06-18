from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "generate-marketplace-catalog.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("generate_marketplace_catalog", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class GenerateMarketplaceCatalogTests(unittest.TestCase):
    def test_catalog_is_derived_from_exported_indexes(self) -> None:
        module = _load_module()
        payload = module.generate_catalog(ROOT, "recommended")
        self.assertEqual(len(payload["indexes"]["recommended"]["items"]), 148)
        self.assertEqual(len(payload["items"]), 148)
        self.assertIn("change-forge-router", payload["items"])
        self.assertIn("implementation-structure-design", payload["items"])

    def test_rendered_catalog_has_required_sections_and_boundary(self) -> None:
        module = _load_module()
        rendered = module.render_catalog(module.generate_catalog(ROOT, "recommended"))
        for section in (
            "## Profile Summary",
            "## Professional Skills",
            "## Foundation Capabilities By Group",
            "## Domain Extensions",
            "## Browse By Quality Gate",
            "## Browse By Risk Trigger",
            "## Browse By Profile Exposure",
        ):
            self.assertIn(section, rendered)
        self.assertIn("Official Codex and Claude marketplace publishing is intentionally not implemented", rendered)

    def test_check_mode_catches_stale_output(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "MARKETPLACE_CATALOG.md"
            out.write_text("stale\n", encoding="utf-8")
            self.assertEqual(module.main(["--profile", "recommended", "--check", "--out", str(out)]), 1)

    def test_check_mode_accepts_generated_output(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "MARKETPLACE_CATALOG.md"
            self.assertEqual(module.main(["--profile", "recommended", "--out", str(out)]), 0)
            self.assertEqual(module.main(["--profile", "recommended", "--check", "--out", str(out)]), 0)


if __name__ == "__main__":
    unittest.main()
