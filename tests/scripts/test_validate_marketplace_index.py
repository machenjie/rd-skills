from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate-marketplace-index.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("validate_marketplace_index", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _item(**overrides):
    item = {
        "name": "regression-testing",
        "type": "foundation_capability",
        "profile_visibility": {
            "top_level": True,
            "compiled_reference": True,
            "router_index": True,
            "authoring_visibility": True,
        },
        "summary": "Regression testing capability.",
        "triggers": ["regression"],
        "risk_notes": ["Regression risk."],
        "expected_outputs": ["Regression proof."],
        "used_by": ["quality-test-gate"],
        "required_quality_gates": ["test gate"],
        "runtime_path": "dist/universal/skills/dev/regression-testing",
        "source_path": "src/foundation/capabilities/regression-testing",
    }
    item.update(overrides)
    return item


def _payload(profile: str, item: dict[str, object]):
    return {
        "schema_version": 1,
        "profile": profile,
        "generated_by": "scripts/export-marketplace-index.py",
        "source_of_truth": ["src/registry/capabilities.yaml"],
        "items": [item],
    }


class ValidateMarketplaceIndexTests(unittest.TestCase):
    def test_valid_dev_foundation_runtime_path_passes(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "dist" / "universal" / "skills" / "dev" / "regression-testing").mkdir(parents=True)
            (root / "src" / "foundation" / "capabilities" / "regression-testing").mkdir(parents=True)
            errors = module.validate_payload(
                root,
                _payload("dev", _item()),
                "dev",
                enforce_counts=False,
            )
        self.assertEqual(errors, [])

    def test_extra_top_level_key_fails(self) -> None:
        module = _load_module()
        payload = _payload("dev", _item())
        payload["unexpected"] = True
        errors = module.validate_payload(
            Path("/tmp"),
            payload,
            "dev",
            enforce_counts=False,
        )
        self.assertTrue(any("top-level keys" in error for error in errors))

    def test_recommended_foundation_top_level_fails(self) -> None:
        module = _load_module()
        item = _item(runtime_path=None)
        errors = module.validate_payload(
            Path("/tmp"),
            _payload("recommended", item),
            "recommended",
            enforce_counts=False,
        )
        self.assertTrue(any("foundation capability must not be top-level" in error for error in errors))

    def test_missing_runtime_path_target_fails(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            errors = module.validate_payload(
                root,
                _payload("dev", _item()),
                "dev",
                enforce_counts=False,
            )
        self.assertTrue(any("runtime_path does not exist" in error for error in errors))

    def test_invalid_name_fails(self) -> None:
        module = _load_module()
        errors = module.validate_payload(
            Path("/tmp"),
            _payload("dev", _item(name="RegressionTesting")),
            "dev",
            enforce_counts=False,
        )
        self.assertTrue(any("invalid name" in error for error in errors))

    def test_item_count_mismatch_fails(self) -> None:
        module = _load_module()
        errors = module._item_count_errors([_item()])
        joined = "\n".join(errors)
        self.assertIn("153 total", joined)
        self.assertIn("19 professional_skill", joined)
        self.assertIn("127 foundation_capability", joined)
        self.assertIn("7 domain_extension", joined)


if __name__ == "__main__":
    unittest.main()
