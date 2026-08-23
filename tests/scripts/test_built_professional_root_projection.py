from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build as BUILD
import validation_utils as VALIDATION


PROFESSIONAL = VALIDATION.load_yaml_file(
    ROOT / "src/registry/professional-skills.yaml"
)
FOUNDATION = VALIDATION.load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
DOMAIN = VALIDATION.load_yaml_file(ROOT / "src/registry/domain-skills.yaml")


class BuiltProfessionalRootProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.authority = VALIDATION.layer3_selector_authority(
            FOUNDATION,
            PROFESSIONAL,
            DOMAIN,
            context="built Professional root projection",
        )
        cls.rows = {
            row["name"]: row for row in PROFESSIONAL["professional_skills"]
        }

    def test_role_filtered_reference_rows_derive_from_registry_authority(self) -> None:
        projections = VALIDATION.layer3_selector_control_projections(self.authority)
        layer3_rows = {
            row["name"]: ("foundation", row)
            for row in FOUNDATION["foundation_skills"]
        }
        layer3_rows.update(
            {
                row["name"]: ("domain", row)
                for row in DOMAIN["domain_skills"]
            }
        )
        for professional, row in self.rows.items():
            with self.subTest(professional=professional):
                source = [
                    contract
                    for contract in VALIDATION.reference_contracts(
                        row["reference_index"],
                        f"{professional}.reference_index",
                        owner=professional,
                    )
                    if contract["type"] != "index"
                ]
                document = projections[f"{professional}.json"]
                for surface in document["selection_surfaces"]:
                    profile = surface["profile"]
                    authorized = self.authority["runtime_professionals"][
                        professional
                    ]["candidates_by_role"][profile]
                    expected = [
                        (professional, "professional", contract)
                        for contract in source
                        if profile in contract["required_by"]
                    ]
                    for owner in authorized:
                        layer, owner_row = layer3_rows[owner]
                        expected.extend(
                            (owner, layer, contract)
                            for contract in VALIDATION.reference_contracts(
                                owner_row["reference_index"],
                                f"{owner}.reference_index",
                                owner=owner,
                            )
                            if contract["type"] != "index"
                            and profile in contract["required_by"]
                        )
                    self.assertTrue(surface["reference_selector_loaded"])
                    self.assertIsNone(surface["exact_references"])
                    self.assertEqual(
                        [
                            (owner, contract["path"])
                            for owner, _layer, contract in expected
                        ],
                        [
                            (record["owner_skill"], record["path"])
                            for record in surface["reference_records"]
                        ],
                    )
                    for (owner, layer, expected_row), actual in zip(
                        expected, surface["reference_records"], strict=True
                    ):
                        self.assertEqual(owner, actual["owner_skill"])
                        self.assertEqual(layer, actual["owner_layer"])
                        for field in (
                            "path",
                            "type",
                            "load_when",
                            "do_not_load_when",
                            "required_by",
                            "required_output",
                        ):
                            self.assertEqual(expected_row[field], actual[field])
                        expected_residency = (
                            "must-co-trigger-component"
                            if isinstance(actual["context_admissibility"], dict)
                            and actual["context_admissibility"][
                                "must_co_trigger_with"
                            ]
                            else "singleton"
                        )
                        self.assertEqual(expected_residency, actual["residency"])
                        self.assertNotEqual([], actual["required_output"])
                        self.assertNotEqual("index", actual["type"])

    def test_exact_reference_skips_reference_selector_and_fails_closed(self) -> None:
        exact_path = "references/generator-and-plugin-contracts.md"
        fixed = VALIDATION.layer3_selector_runtime_projection(
            self.authority,
            professional_skill="repository-tooling-change-builder",
            profile="task-agent",
            selection_owner="engineering-brief",
            exact_layer3=[],
            exact_references=[exact_path],
        )
        self.assertFalse(fixed["selector_loaded"])
        self.assertFalse(fixed["reference_selector_loaded"])
        self.assertEqual([exact_path], fixed["exact_references"])
        self.assertEqual([], fixed["reference_records"])
        for invalid in (
            ["references/invented.md"],
            [exact_path, exact_path],
        ):
            with self.subTest(invalid=invalid), self.assertRaises(
                VALIDATION.ValidationProblem
            ):
                VALIDATION.layer3_selector_runtime_projection(
                    self.authority,
                    professional_skill="repository-tooling-change-builder",
                    profile="task-agent",
                    selection_owner="engineering-brief",
                    exact_layer3=[],
                    exact_references=invalid,
                )

    def test_built_roots_are_compact_across_all_profiles_and_source_is_complete(self) -> None:
        items = BUILD._load_items("professional", list(self.rows.values()))
        with tempfile.TemporaryDirectory() as temporary:
            for item in items:
                source_root = (item.path / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn("## Targeted References", source_root)
                prefixes = []
                for profile in BUILD.PROFILES:
                    with self.subTest(professional=item.name, profile=profile):
                        root = Path(temporary) / profile / item.name
                        BUILD._copy_skill_tree(item.path, root)
                        BUILD._write_compact_professional_projection(root, item)
                        BUILD._append_layer3_entrypoint(root, profile)
                        rendered = (root / "SKILL.md").read_text(encoding="utf-8")
                        self.assertNotIn("## Targeted References", rendered)
                        self.assertIn("## JIT Reference Delivery", rendered)
                        self.assertIn(
                            f"references/selectors/{item.name}.json",
                            rendered,
                        )
                        for heading in BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS:
                            self.assertIn(f"## {heading}", rendered)
                        expected_delivery = {
                            "recommended": "No Foundation or Domain Layer 3 items are assigned to this Skill.",
                            "full": "Domain items are top-level Skills; no Foundation items are compiled for this Skill.",
                            "dev": "Foundation and Domain items are top-level Skills; no Layer 3 references are compiled.",
                        }[profile]
                        self.assertEqual(
                            expected_delivery,
                            rendered.split("## Layer 3 Delivery\n\n", 1)[1].strip(),
                        )
                        self.assertNotIn("Never preload Layer 3", rendered)
                        self.assertNotIn("Layer 3 index or catalog", rendered)
                        prefixes.append(rendered.split("## Layer 3 Delivery", 1)[0])
                self.assertEqual(1, len(set(prefixes)))
                self.assertEqual(
                    source_root,
                    (item.path / "SKILL.md").read_text(encoding="utf-8"),
                )

    def test_all_built_layer3_roots_are_compact_and_sources_remain_complete(self) -> None:
        registries = BUILD._load_registries()
        items = [
            *BUILD._load_items("foundation", registries["foundation"]),
            *BUILD._load_items("domain", registries["domain"]),
        ]
        with tempfile.TemporaryDirectory() as temporary:
            for item in items:
                source_path = item.path / "SKILL.md"
                source_root = source_path.read_text(encoding="utf-8")
                self.assertIn("## Targeted References", source_root)
                for profile in BUILD.PROFILES:
                    with self.subTest(skill=item.name, profile=profile):
                        root = Path(temporary) / profile / item.name
                        root.mkdir(parents=True)
                        (root / "SKILL.md").write_text(
                            source_root, encoding="utf-8"
                        )
                        BUILD._write_compact_layer3_root_projection(root, item)
                        rendered = (root / "SKILL.md").read_text(encoding="utf-8")
                        self.assertNotIn("## Targeted References", rendered)
                        self.assertIn("## JIT Reference Delivery", rendered)
                        self.assertIn("Current-Professional JIT", rendered)
                self.assertEqual(source_root, source_path.read_text(encoding="utf-8"))

    def test_compiled_layer3_projection_uses_same_jit_reference_delivery(self) -> None:
        registries = BUILD._load_registries()
        items = [
            *[
                item
                for item in BUILD._load_items(
                    "foundation", registries["foundation"]
                )
                if item.registry.get("delivery_scope") == "product"
            ],
            *BUILD._load_items("domain", registries["domain"]),
        ]
        for item in items:
            with self.subTest(skill=item.name):
                rendered = BUILD._render_layer3_reference(item)
                self.assertNotIn("## Targeted References", rendered)
                self.assertIn("## JIT Reference Delivery", rendered)
                self.assertIn("Current-Professional JIT", rendered)
                for contract in VALIDATION.reference_contracts(
                    item.registry["reference_index"],
                    f"{item.name}.reference_index",
                    owner=item.name,
                ):
                    if contract["type"] != "index":
                        self.assertTrue((item.path / contract["path"]).is_file())

    def test_built_named_reference_receipt_and_inventory_are_complete(self) -> None:
        expected_counts = {"recommended": 27, "full": 40, "dev": 190}
        named = "references/generator-and-plugin-contracts.md"
        registries = BUILD._load_registries()
        items = {
            layer: BUILD._load_items(layer, rows)
            for layer, rows in registries.items()
        }
        for profile, expected_count in expected_counts.items():
            self.assertEqual(
                expected_count, len(BUILD._top_level_items(profile, items))
            )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            professional = root / "repository-tooling-change-builder"
            item = next(
                row
                for row in items["professional"]
                if row.name == "repository-tooling-change-builder"
            )
            BUILD._copy_skill_tree(item.path, professional)
            BUILD._write_compact_professional_projection(professional, item)
            control = root / "engineering-control-plane"
            control.mkdir()
            BUILD._write_control_layer3_selector_projections(control)
            selector = json.loads(
                (
                    control
                    / "references/selectors/repository-tooling-change-builder.json"
                ).read_text(encoding="utf-8")
            )
            surface = next(
                row
                for row in selector["selection_surfaces"]
                if row["profile"] == "task-agent"
                and row["selection_owner"] == "main-control-agent"
            )
            record = next(
                row for row in surface["reference_records"] if row["path"] == named
            )
            self.assertIn("boundary-decision", record["required_output"])
            self.assertTrue((professional / named).is_file())
            self.assertFalse(
                any(row["type"] == "index" for row in surface["reference_records"])
            )
        self.assertEqual(
            189,
            len(BUILD._top_level_items("dev", items)) - 1,
        )


if __name__ == "__main__":
    unittest.main()
