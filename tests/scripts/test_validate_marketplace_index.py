from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate-marketplace-index.py"
SOURCES = [
    "src/registry/control-skills.yaml",
    "src/registry/professional-skills.yaml",
    "src/registry/foundation-skills.yaml",
    "src/registry/domain-skills.yaml",
]


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("validate_marketplace_index", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _item(**overrides):
    item = {
        "name": "regression-testing",
        "type": "foundation_skill",
        "delivery_scope": "dev-only",
        "task_routable": None,
        "profile_delivery": {
            "mode": "top_level_skill",
            "top_level": True,
            "targeted_reference": False,
            "routing_index": True,
        },
        "summary": "Regression testing Skill.",
        "role_support": ["task-agent", "review-agent"],
        "trigger_signals": ["regression risk"],
        "anti_trigger_signals": ["no behavior changed"],
        "required_inputs": ["acceptance", "changed paths"],
        "required_inputs_by_role": {},
        "output_contract": ["fresh regression result"],
        "output_contract_by_role": {},
        "escalation_signals": ["critical coverage gap"],
        "reference_index": [],
        "related_layer3_skills": [],
        "used_by": [],
        "group": "testing-quality",
        "source_path": "src/foundation/capabilities/regression-testing",
    }
    item.update(overrides)
    return item


def _payload(profile: str, item: dict[str, object]):
    return {
        "schema_version": 3,
        "profile": profile,
        "generated_by": "scripts/export-marketplace-index.py",
        "source_of_truth": SOURCES,
        "items": [item],
    }


def _write_skill(root: Path, relative: str) -> None:
    target = root / relative
    target.mkdir(parents=True)
    (target / "SKILL.md").write_text(
        "---\nname: regression-testing\ndescription: Regression testing.\n---\n",
        encoding="utf-8",
    )


class ValidateMarketplaceIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_valid_dev_foundation_skill_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_skill(root, "src/foundation/capabilities/regression-testing")
            errors = self.module.validate_payload(
                root,
                _payload("dev", _item()),
                "dev",
                enforce_counts=False,
            )
        self.assertEqual(errors, [])

    def test_all_exported_profiles_pass(self) -> None:
        for profile in ("recommended", "full", "dev"):
            with self.subTest(profile=profile):
                self.assertEqual(self.module.validate_profile(ROOT, profile), [])

    def test_extra_top_level_key_fails(self) -> None:
        payload = _payload("dev", _item())
        payload["unexpected"] = True
        errors = self.module.validate_payload(
            Path("/tmp"),
            payload,
            "dev",
            enforce_counts=False,
        )
        self.assertTrue(any("top-level keys" in error for error in errors))

    def test_v2_payload_is_rejected(self) -> None:
        payload = _payload("dev", _item())
        payload["schema_version"] = 2
        errors = self.module.validate_payload(
            Path("/tmp"), payload, "dev", enforce_counts=False
        )
        self.assertTrue(any("schema_version must be 3" in error for error in errors))

    def test_recommended_foundation_cannot_claim_top_level_delivery(self) -> None:
        errors = self.module.validate_payload(
            Path("/tmp"),
            _payload("recommended", _item()),
            "recommended",
            enforce_counts=False,
        )
        self.assertTrue(any("expected routing_index_only" in error for error in errors))

    def test_recommended_professional_must_be_top_level(self) -> None:
        item = _item(
            name="backend-change-builder",
            type="professional_skill",
            delivery_scope=None,
            task_routable=True,
            profile_delivery={
                "mode": "routing_index_only",
                "top_level": False,
                "targeted_reference": False,
                "routing_index": True,
            },
            related_layer3_skills=[],
            used_by=[],
            group=None,
            source_path="src/professional-skills/backend-change-builder",
        )
        errors = self.module.validate_payload(
            ROOT,
            _payload("recommended", item),
            "recommended",
            enforce_counts=False,
        )
        self.assertTrue(any("expected top_level_skill" in error for error in errors))

    def test_missing_standard_skill_root_fails(self) -> None:
        errors = self.module.validate_payload(
            Path("/tmp"),
            _payload("dev", _item()),
            "dev",
            enforce_counts=False,
        )
        self.assertTrue(any("is not a standard Skill" in error for error in errors))

    def test_invalid_name_fails(self) -> None:
        errors = self.module.validate_payload(
            Path("/tmp"),
            _payload("dev", _item(name="RegressionTesting")),
            "dev",
            enforce_counts=False,
        )
        self.assertTrue(any("invalid name" in error for error in errors))

    def test_obsolete_field_is_rejected(self) -> None:
        item = _item()
        item["runtime_path"] = "obsolete"
        errors = self.module.validate_payload(
            Path("/tmp"),
            _payload("dev", item),
            "dev",
            enforce_counts=False,
        )
        self.assertTrue(any("keys must be exactly" in error for error in errors))

    def test_missing_task_routable_field_is_rejected(self) -> None:
        item = _item()
        item.pop("task_routable")
        errors = self.module.validate_payload(
            Path("/tmp"),
            _payload("dev", item),
            "dev",
            enforce_counts=False,
        )
        self.assertTrue(any("keys must be exactly" in error for error in errors))

    def test_foundation_delivery_scope_is_required(self) -> None:
        errors = self.module.validate_payload(
            Path("/tmp"),
            _payload("dev", _item(delivery_scope=None)),
            "dev",
            enforce_counts=False,
        )
        self.assertTrue(any("delivery_scope must be one of" in error for error in errors))

    def test_non_foundation_delivery_scope_is_rejected(self) -> None:
        item = _item(
            name="backend-change-builder",
            type="professional_skill",
            delivery_scope="product",
            task_routable=True,
            group=None,
            source_path="src/professional-skills/backend-change-builder",
        )
        errors = self.module.validate_payload(
            ROOT,
            _payload("recommended", item),
            "recommended",
            enforce_counts=False,
        )
        self.assertTrue(any("only valid for a Foundation Skill" in error for error in errors))

    def test_non_foundation_used_by_is_rejected_for_every_layer(self) -> None:
        cases = (
            (
                "control_skill",
                _item(
                    name="engineering-control-plane",
                    type="control_skill",
                    delivery_scope=None,
                    task_routable=None,
                    group=None,
                    source_path="src/control-skills/engineering-control-plane",
                ),
            ),
            (
                "professional_skill",
                _item(
                    name="backend-change-builder",
                    type="professional_skill",
                    delivery_scope=None,
                    task_routable=True,
                    group=None,
                    source_path="src/professional-skills/backend-change-builder",
                ),
            ),
            (
                "domain_skill",
                _item(
                    name="web3-product-extension",
                    type="domain_skill",
                    delivery_scope=None,
                    task_routable=None,
                    group=None,
                    source_path="src/domain-extensions/web3-product-extension",
                ),
            ),
        )
        for item_type, item in cases:
            item["used_by"] = ["backend-change-builder"]
            errors = self.module.validate_payload(
                ROOT,
                _payload("recommended", item),
                "recommended",
                enforce_counts=False,
            )
            with self.subTest(item_type=item_type):
                self.assertTrue(
                    any(
                        ".used_by is only valid for a Foundation Skill" in error
                        for error in errors
                    )
                )

    def test_professional_task_routable_is_explicit(self) -> None:
        item = _item(
            name="backend-change-builder",
            type="professional_skill",
            delivery_scope=None,
            task_routable=None,
            group=None,
            source_path="src/professional-skills/backend-change-builder",
        )
        errors = self.module.validate_payload(
            ROOT,
            _payload("recommended", item),
            "recommended",
            enforce_counts=False,
        )
        self.assertTrue(any("task_routable must be boolean" in error for error in errors))

    def test_malformed_list_is_reported_without_crashing(self) -> None:
        errors = self.module.validate_payload(
            Path("/tmp"),
            _payload("dev", _item(related_layer3_skills=None)),
            "dev",
            enforce_counts=False,
        )
        self.assertTrue(any("related_layer3_skills must be a list" in error for error in errors))

    def test_multi_role_professional_requires_exact_role_input_map(self) -> None:
        item = _item(
            name="security-privacy-gate",
            type="professional_skill",
            delivery_scope=None,
            task_routable=True,
            role_support=["analysis-agent", "review-agent"],
            required_inputs_by_role={"review-agent": ["actual diff"]},
            group=None,
            source_path="src/professional-skills/security-privacy-gate",
        )
        errors = self.module.validate_payload(
            ROOT,
            _payload("recommended", item),
            "recommended",
            enforce_counts=False,
        )
        self.assertTrue(
            any("keys must exactly match role_support" in error for error in errors)
        )

    def test_product_owner_must_be_task_routable(self) -> None:
        exporter = self.module._load_exporter()
        payload = exporter.export_index(ROOT, "recommended")
        owner = next(
            item
            for item in payload["items"]
            if item["name"] == "quality-test-gate"
        )
        owner["task_routable"] = False
        errors = self.module.validate_payload(ROOT, payload, "recommended")
        self.assertTrue(any("must be task_routable" in error for error in errors))

    def test_product_owner_requires_role_support_intersection(self) -> None:
        exporter = self.module._load_exporter()
        payload = copy.deepcopy(exporter.export_index(ROOT, "recommended"))
        high_risk = next(
            item
            for item in payload["items"]
            if item["name"] == "high-risk-design-review"
        )
        tradeoff = next(
            item
            for item in payload["items"]
            if item["name"] == "architecture-tradeoff-analysis"
        )
        high_risk["related_layer3_skills"].append(
            "architecture-tradeoff-analysis"
        )
        tradeoff["used_by"].append("high-risk-design-review")
        errors = self.module.validate_payload(ROOT, payload, "recommended")
        self.assertTrue(
            any("has no role_support intersection" in error for error in errors)
        )

    def test_reference_must_exist_inside_skill_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_skill(root, "src/foundation/capabilities/regression-testing")
            errors = self.module.validate_payload(
                root,
                _payload("dev", _item(reference_index=["../outside.md"])),
                "dev",
                enforce_counts=False,
            )
        self.assertTrue(any("missing or escapes" in error for error in errors))

    def test_item_count_mismatch_names_all_four_layers(self) -> None:
        errors = self.module._item_count_errors([_item()])
        joined = "\n".join(errors)
        self.assertIn("190 total", joined)
        self.assertIn("1 control_skill", joined)
        self.assertIn("26 professional_skill", joined)
        self.assertIn("150 foundation_skill", joined)
        self.assertIn("13 domain_skill", joined)

    def test_committed_schema_declares_v3_shape(self) -> None:
        schema = json.loads(
            (ROOT / "schemas" / "marketplace-index.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(schema["properties"]["schema_version"]["const"], 3)
        self.assertEqual(schema["title"], "rd-skills Marketplace Index v3")
        item = schema["$defs"]["item"]
        self.assertIn("profile_delivery", item["required"])
        self.assertIn("required_inputs_by_role", item["required"])
        self.assertIn("delivery_scope", item["required"])
        self.assertIn("task_routable", item["required"])
        self.assertNotIn("runtime_path", item["properties"])
        self.assertEqual(
            set(item["properties"]["type"]["enum"]),
            {
                "control_skill",
                "professional_skill",
                "foundation_skill",
                "domain_skill",
            },
        )


if __name__ == "__main__":
    unittest.main()
