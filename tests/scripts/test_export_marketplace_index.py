from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "export-marketplace-index.py"
REQUIRED_ITEM_FIELDS = {
    "name",
    "type",
    "delivery_scope",
    "task_routable",
    "profile_delivery",
    "summary",
    "role_support",
    "trigger_signals",
    "anti_trigger_signals",
    "required_inputs",
    "required_inputs_by_role",
    "output_contract",
    "output_contract_by_role",
    "escalation_signals",
    "reference_index",
    "related_layer3_skills",
    "used_by",
    "group",
    "source_path",
}


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("export_marketplace_index", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _by_name(payload: dict, name: str) -> dict:
    return next(item for item in payload["items"] if item["name"] == name)


class ExportMarketplaceIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()
        cls.payload = cls.module.export_index(ROOT)

    def test_v3_index_is_derived_from_exactly_four_registries(self) -> None:
        expected_sources = [
            "src/registry/control-skills.yaml",
            "src/registry/professional-skills.yaml",
            "src/registry/foundation-skills.yaml",
            "src/registry/domain-skills.yaml",
        ]
        self.assertEqual(self.payload["schema_version"], 3)
        self.assertEqual(self.payload["profile"], "recommended")
        self.assertEqual(self.payload["source_of_truth"], expected_sources)

    def test_index_shape_and_layer_counts(self) -> None:
        payload = self.payload
        self.assertEqual(len(payload["items"]), 189)
        self.assertEqual(
            Counter(item["type"] for item in payload["items"]),
            {
                "control_skill": 1,
                "professional_skill": 25,
                "foundation_skill": 150,
                "domain_skill": 13,
            },
        )
        for item in payload["items"]:
            self.assertEqual(set(item), REQUIRED_ITEM_FIELDS)

    def test_runtime_delivery_is_one_fixed_projection(self) -> None:
        top_level = sum(
            item["profile_delivery"]["top_level"]
            for item in self.payload["items"]
        )
        modes = Counter(
            item["profile_delivery"]["mode"]
            for item in self.payload["items"]
        )
        self.assertEqual(top_level, 26)
        self.assertEqual(
            modes,
            {
                "top_level_skill": 26,
                "targeted_reference": 154,
                "routing_index_only": 9,
            },
        )

    def test_only_control_and_professional_skills_are_top_level(self) -> None:
        top_level = [
            item
            for item in self.payload["items"]
            if item["profile_delivery"]["top_level"]
        ]
        self.assertEqual(
            Counter(item["type"] for item in top_level),
            {"control_skill": 1, "professional_skill": 25},
        )
        self.assertTrue(
            all(
                isinstance(item["task_routable"], bool)
                for item in top_level
                if item["type"] == "professional_skill"
            )
        )

    def test_task_routable_is_null_outside_professional_skills(self) -> None:
        self.assertTrue(
            all(
                item["task_routable"] is None
                for item in self.payload["items"]
                if item["type"] != "professional_skill"
            )
        )

    def test_multi_role_professional_inputs_are_exported_by_role(self) -> None:
        recommended = self.payload
        security = _by_name(recommended, "security-privacy-gate")
        self.assertEqual(
            set(security["required_inputs_by_role"]),
            {"analysis-agent", "task-agent", "review-agent"},
        )
        unified = _by_name(recommended, "engineering-change-analysis")
        self.assertEqual(unified["required_inputs_by_role"], {})
        self.assertEqual(
            set(security["output_contract_by_role"]),
            {"analysis-agent", "task-agent", "review-agent"},
        )
        self.assertEqual(unified["output_contract_by_role"], {})

    def test_layer3_delivery_is_task_targeted(self) -> None:
        recommended = self.payload
        self.assertEqual(
            _by_name(recommended, "transaction-consistency")["profile_delivery"]["mode"],
            "targeted_reference",
        )
        self.assertEqual(
            _by_name(recommended, "payment-trading-extension")["profile_delivery"]["mode"],
            "targeted_reference",
        )
        self.assertEqual(
            _by_name(recommended, "skill-authoring-expert")["profile_delivery"]["mode"],
            "routing_index_only",
        )

    def test_foundation_delivery_scopes_are_explicit(self) -> None:
        foundations = [
            item
            for item in self.payload["items"]
            if item["type"] == "foundation_skill"
        ]
        self.assertEqual(
            Counter(item["delivery_scope"] for item in foundations),
            {"product": 141, "authoring-only": 1, "internal-only": 8},
        )
        self.assertEqual(
            _by_name(self.payload, "skill-authoring-expert")[
                "delivery_scope"
            ],
            "authoring-only",
        )
        self.assertTrue(
            all(
                item["delivery_scope"] is None
                for item in self.payload["items"]
                if item["type"] != "foundation_skill"
            )
        )

    def test_used_by_preserves_all_layer3_selector_ownership(self) -> None:
        entries = self.module._load_registry_entries(ROOT)
        foundation_used_by = {
            entry["name"]: entry["used_by"]
            for entry in entries["foundation_skill"]
        }
        domain_used_by = {
            entry["name"]: entry["used_by"]
            for entry in entries["domain_skill"]
        }
        self.assertEqual(len(domain_used_by), 13)
        self.assertTrue(all(domain_used_by.values()))
        self.assertEqual(sum(map(len, domain_used_by.values())), 47)

        foundations = [
            item
            for item in self.payload["items"]
            if item["type"] == "foundation_skill"
        ]
        non_layer3 = [
            item
            for item in self.payload["items"]
            if item["type"] not in {"foundation_skill", "domain_skill"}
        ]
        domains = [
            item
            for item in self.payload["items"]
            if item["type"] == "domain_skill"
        ]
        self.assertEqual(len(foundations), 150)
        self.assertEqual(sum(bool(item["used_by"]) for item in foundations), 141)
        self.assertEqual(sum(not item["used_by"] for item in foundations), 9)
        self.assertTrue(all(item["used_by"] == [] for item in non_layer3))
        self.assertTrue(
            all(
                item["used_by"] == foundation_used_by[item["name"]]
                for item in foundations
            )
        )
        self.assertTrue(
            all(item["used_by"] == domain_used_by[item["name"]] for item in domains)
        )

    def test_invalid_domain_used_by_is_rejected_before_projection(self) -> None:
        entry = self.module._load_registry_entries(ROOT)["domain_skill"][0]
        targeted_layer3 = self.module._targeted_layer3_names(
            self.module._load_registry_entries(ROOT),
        )
        for invalid_used_by in ("engineering-change-analysis", [""]):
            invalid_entry = dict(entry)
            invalid_entry["used_by"] = invalid_used_by
            with self.subTest(used_by=invalid_used_by):
                with self.assertRaises(self.module.MarketplaceExportError):
                    self.module._item(
                        ROOT,
                        "domain_skill",
                        invalid_entry,
                        targeted_layer3,
                    )

    def test_exported_shape_has_no_obsolete_delivery_fields(self) -> None:
        serialized = json.dumps(self.payload, sort_keys=True)
        for marker in (
            "runtime_path",
            ".changeforge-packs",
            "specialist_packs",
            "review_packs",
            "compiled_reference",
            "dev-only",
        ):
            self.assertNotIn(marker, serialized)

    def test_obsolete_profile_argument_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit) as caught:
                self.module.main(
                    ["--profile", "full", "--out", str(Path(tmp) / "index.json")]
                )
        self.assertEqual(caught.exception.code, 2)

    def test_temp_exports_are_byte_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first.json"
            second = Path(tmp) / "second.json"
            self.assertEqual(self.module.main(["--out", str(first)]), 0)
            self.assertEqual(self.module.main(["--out", str(second)]), 0)
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_frontmatter_missing_skill_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(self.module.MarketplaceExportError):
                self.module._frontmatter_summary(
                    Path(tmp),
                    "src/professional-skills/missing",
                )

    def test_frontmatter_missing_description_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "src" / "professional-skills" / "sample"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: sample\n---\n# Sample\n",
                encoding="utf-8",
            )
            with self.assertRaises(self.module.MarketplaceExportError):
                self.module._frontmatter_summary(
                    root,
                    "src/professional-skills/sample",
                )


if __name__ == "__main__":
    unittest.main()
