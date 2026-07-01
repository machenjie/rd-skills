from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "export-marketplace-index.py"
REQUIRED_ITEM_FIELDS = {
    "name",
    "type",
    "profile_visibility",
    "summary",
    "triggers",
    "risk_notes",
    "expected_outputs",
    "used_by",
    "required_quality_gates",
    "runtime_path",
    "source_path",
}


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("export_marketplace_index", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ExportMarketplaceIndexTests(unittest.TestCase):
    def test_profile_visibility_preserves_top_level_policy(self) -> None:
        module = _load_module()
        recommended = module.export_index(ROOT, "recommended")
        full = module.export_index(ROOT, "full")
        dev = module.export_index(ROOT, "dev")

        recommended_caps = [item for item in recommended["items"] if item["type"] == "foundation_capability"]
        full_caps = [item for item in full["items"] if item["type"] == "foundation_capability"]
        dev_caps = [item for item in dev["items"] if item["type"] == "foundation_capability"]
        self.assertEqual(sum(item["profile_visibility"]["top_level"] for item in recommended_caps), 0)
        self.assertEqual(sum(item["profile_visibility"]["top_level"] for item in full_caps), 0)
        self.assertEqual(sum(item["profile_visibility"]["top_level"] for item in dev_caps), 136)

    def test_index_shape_contains_required_fields(self) -> None:
        module = _load_module()
        payload = module.export_index(ROOT, "recommended")
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["profile"], "recommended")
        self.assertEqual(len(payload["items"]), 164)
        for item in payload["items"]:
            self.assertEqual(set(item), REQUIRED_ITEM_FIELDS)

    def test_full_profile_exposes_domain_extensions_top_level(self) -> None:
        module = _load_module()
        payload = module.export_index(ROOT, "full")
        extensions = [item for item in payload["items"] if item["type"] == "domain_extension"]
        self.assertEqual(len(extensions), 7)
        self.assertTrue(all(item["profile_visibility"]["top_level"] for item in extensions))

    def test_frontmatter_missing_skill_raises(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(module.MarketplaceExportError):
                module._frontmatter_summary(Path(tmp), "src/professional-skills/missing")

    def test_frontmatter_missing_description_raises(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "src" / "professional-skills" / "sample"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: sample\nlicense: MIT\n---\n# Sample\n",
                encoding="utf-8",
            )
            with self.assertRaises(module.MarketplaceExportError):
                module._frontmatter_summary(root, "src/professional-skills/sample")

    def test_frontmatter_parse_error_raises(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "src" / "professional-skills" / "sample"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("---\nname: sample\n", encoding="utf-8")
            with self.assertRaises(module.MarketplaceExportError):
                module._frontmatter_summary(root, "src/professional-skills/sample")


if __name__ == "__main__":
    unittest.main()
