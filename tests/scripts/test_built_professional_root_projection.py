from __future__ import annotations

import copy
import hashlib
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

    def test_normalized_selector_expands_to_every_canonical_owner_surface(self) -> None:
        normalizer = getattr(
            VALIDATION, "layer3_selector_normalized_control_projections", None
        )
        expander = getattr(
            VALIDATION, "layer3_selector_expand_runtime_projection", None
        )
        self.assertTrue(callable(normalizer))
        self.assertTrue(callable(expander))
        selectors, partitions = normalizer(self.authority)
        canonical = VALIDATION.layer3_selector_control_projections(self.authority)
        self.assertEqual(
            set(canonical),
            {path for path in selectors if "/" not in path},
        )
        for filename, document in canonical.items():
            professional = document["professional_skill"]
            base = selectors.get(f"{professional}/complete.json", selectors[filename])
            professional = base["professional_skill"]
            self.assertEqual(
                {"profile", "selection_owner"},
                set(base["owner_surfaces"][0]),
            )
            self.assertEqual(
                len({row["profile"] for row in base["owner_surfaces"]}),
                len(base["profile_authority"]),
            )
            for expected in document["selection_surfaces"]:
                selections = [[], *[[item] for item in expected["authorized_layer3"]]]
                for selected_layer3 in selections:
                    with self.subTest(
                        professional=base["professional_skill"],
                        profile=expected["profile"],
                        owner=expected["selection_owner"],
                        selected_layer3=selected_layer3,
                    ):
                        selected_partitions = {
                            owner: partitions[f"{professional}/{owner}.json"]
                            for owner in [professional, *selected_layer3]
                        }
                        actual = expander(
                            base,
                            selected_partitions,
                            profile=expected["profile"],
                            selection_owner=expected["selection_owner"],
                            exact_layer3=None,
                            selected_layer3=selected_layer3,
                            exact_references=None,
                        )
                        selected_owners = {professional, *selected_layer3}
                        projected_expected = copy.deepcopy(expected)
                        projected_expected["reference_records"] = [
                            record
                            for record in expected["reference_records"]
                            if record["owner_skill"] in selected_owners
                        ]
                        self.assertEqual(projected_expected, actual)
                        signals: list[str] = []
                        self.assertEqual(
                            VALIDATION.layer3_selector_runtime_selection_receipt(
                                expected, evidence_signals=signals
                            ),
                            VALIDATION.layer3_selector_runtime_selection_receipt(
                                actual, evidence_signals=signals
                            ),
                        )

    def test_s3d_diagnosis_decision_partition_is_lossless_and_bounded(self) -> None:
        selectors, partitions = (
            VALIDATION.layer3_selector_normalized_control_projections(self.authority)
        )
        professional = "engineering-change-analysis"
        envelope = selectors[f"{professional}.json"]
        complete = selectors[f"{professional}/complete.json"]
        shard = selectors[
            f"{professional}/failure-diagnosis-analysis.json"
        ]
        self.assertEqual(
            "changeforge.layer3-selector-decision-envelope/v1",
            envelope["contract"],
        )
        self.assertEqual(
            "changeforge.layer3-selector-normalized-control/v1",
            complete["contract"],
        )
        self.assertEqual(
            "changeforge.layer3-selector-decision-partition/v1",
            shard["contract"],
        )
        decision_binding = envelope["decisions"][0]
        runtime_key = decision_binding["runtime_key"]
        self.assertEqual(
            {
                "route_source",
                "trigger",
                "start_profile",
                "primary_professional_skill",
                "review_skill",
                "selection_owner",
            },
            set(runtime_key),
        )
        self.assertEqual(
            {"path", "sha256", "pointer"}, set(runtime_key["route_source"])
        )
        self.assertEqual(
            {
                "decision_id",
                "scenario_id",
                "light_case_id",
                "release_scenario",
                "selector_registry",
            },
            set(decision_binding["provenance"]),
        )
        self.assertNotIn("selected_layer3", runtime_key)
        self.assertNotIn("scenario_id", runtime_key)
        self.assertNotIn("light_case_id", runtime_key)
        self.assertEqual(
            {
                f"{professional}.json",
                f"{professional}/complete.json",
                f"{professional}/failure-diagnosis-analysis.json",
            },
            {
                path
                for path in selectors
                if path == f"{professional}.json"
                or path.startswith(f"{professional}/")
            },
        )
        self.assertLessEqual(
            VALIDATION.count_o200k_base_tokens(
                VALIDATION._canonical_selector_document_bytes(envelope).decode()
            )
            + VALIDATION.count_o200k_base_tokens(
                VALIDATION._canonical_selector_document_bytes(shard).decode()
            ),
            1_530,
        )

        decision = VALIDATION.layer3_selector_resolve_control_projection(
            envelope,
            {
                "engineering-change-analysis/failure-diagnosis-analysis.json": shard,
            },
            runtime_key=runtime_key,
        )
        self.assertEqual("exact", decision["selection_kind"])
        self.assertEqual(
            "engineering-change-analysis/failure-diagnosis-analysis.json",
            decision["path"],
        )
        selected_partitions = {
            owner: partitions[f"{professional}/{owner}.json"]
            for owner in [professional, "failure-diagnosis"]
        }
        full_projection = VALIDATION.layer3_selector_expand_runtime_projection(
            complete,
            selected_partitions,
            profile="analysis-agent",
            selection_owner="main-control-agent",
            exact_layer3=decision["selected_layer3"],
            exact_references=None,
        )
        shard_projection = VALIDATION.layer3_selector_expand_runtime_projection(
            decision["projection"],
            selected_partitions,
            profile="analysis-agent",
            selection_owner="main-control-agent",
            exact_layer3=decision["selected_layer3"],
            exact_references=None,
        )
        for field in (
            "authority_contract",
            "professional_skill",
            "profile",
            "selection_owner",
            "selection_basis",
            "authorized_layer3",
            "domain_authorization",
            "reference_records",
        ):
            self.assertEqual(full_projection[field], shard_projection[field])
        full_receipt = VALIDATION.layer3_selector_runtime_selection_receipt(
            full_projection, evidence_signals=[]
        )
        shard_receipt = VALIDATION.layer3_selector_runtime_selection_receipt(
            shard_projection, evidence_signals=[]
        )
        self.assertFalse(shard_projection["selector_loaded"])
        self.assertEqual(["exact-layer3-authority"], full_receipt["selector_ids"])
        self.assertEqual([], full_receipt["evidence_signals"])
        self.assertEqual(["failure-diagnosis"], full_receipt["selected_layer3"])
        self.assertEqual(full_receipt, shard_receipt)

    def test_s3d_decision_partition_fails_closed_or_uses_complete_fallback(self) -> None:
        selectors, _partitions = (
            VALIDATION.layer3_selector_normalized_control_projections(self.authority)
        )
        professional = "engineering-change-analysis"
        envelope = selectors[f"{professional}.json"]
        shard_path = "engineering-change-analysis/failure-diagnosis-analysis.json"
        complete_path = "engineering-change-analysis/complete.json"
        shard = selectors[shard_path]
        complete = selectors[complete_path]
        diagnosis_key = copy.deepcopy(envelope["decisions"][0]["runtime_key"])
        fallback_key = copy.deepcopy(diagnosis_key)
        fallback_key["route_source"]["pointer"] = "| unrelated route |"
        fallback = VALIDATION.layer3_selector_resolve_control_projection(
            envelope,
            {complete_path: complete},
            runtime_key=fallback_key,
        )
        self.assertEqual("complete", fallback["selection_kind"])
        self.assertTrue(fallback["projection"]["profile_authority"])

        exact_documents = {shard_path: shard}
        for field, value in (
            ("start_profile", "task-agent"),
            ("selection_owner", "engineering-brief"),
            ("review_skill", "ai-code-review-refactor"),
            ("primary_professional_skill", "backend-change-builder"),
        ):
            wrong = copy.deepcopy(diagnosis_key)
            wrong[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(
                VALIDATION.ValidationProblem, "tuple|identity"
            ):
                VALIDATION.layer3_selector_resolve_control_projection(
                    envelope, exact_documents, runtime_key=wrong
                )

        provenance_only = copy.deepcopy(envelope)
        provenance_only["decisions"][0]["provenance"]["scenario_id"] = (
            "renamed-provenance"
        )
        provenance_only["decisions"][0]["provenance"]["light_case_id"] = (
            "renamed-light-case"
        )
        self.assertEqual(
            "exact",
            VALIDATION.layer3_selector_resolve_control_projection(
                provenance_only, exact_documents, runtime_key=diagnosis_key
            )["selection_kind"],
        )

        stale = copy.deepcopy(exact_documents)
        stale[shard_path]["selected_layer3"] = []
        ambiguous_envelope = copy.deepcopy(envelope)
        ambiguous_envelope["decisions"].append(
            copy.deepcopy(ambiguous_envelope["decisions"][0])
        )
        for candidate_envelope, candidate_documents, pattern in (
            (envelope, {}, "missing"),
            (envelope, stale, "stale"),
            (ambiguous_envelope, exact_documents, "duplicate|ambiguous"),
        ):
            with self.subTest(pattern=pattern), self.assertRaisesRegex(
                VALIDATION.ValidationProblem, pattern
            ):
                VALIDATION.layer3_selector_resolve_control_projection(
                    candidate_envelope,
                    candidate_documents,
                    runtime_key=diagnosis_key,
                )

    def test_s3b_reference_partitions_are_owner_scoped_and_tri_state(self) -> None:
        selectors, partitions = (
            VALIDATION.layer3_selector_normalized_control_projections(self.authority)
        )
        professional = "repository-tooling-change-builder"
        base = selectors[f"{professional}.json"]
        self.assertEqual(
            f"../reference-records/{professional}/{{owner_skill}}.json",
            base["reference_records_partition"]["path_template"],
        )
        self.assertNotIn("reference_records_companion", base)
        self.assertNotIn(f"{professional}.json", partitions)
        selected_layer3 = [
            "build-tool-professional-usage",
            "targeted-validation-selection",
        ]
        selected_partitions = {
            owner: partitions[f"{professional}/{owner}.json"]
            for owner in [professional, *selected_layer3]
        }
        unresolved = VALIDATION.layer3_selector_expand_runtime_projection(
            base,
            selected_partitions,
            profile="task-agent",
            selection_owner="engineering-brief",
            exact_layer3=None,
            selected_layer3=selected_layer3,
            exact_references=None,
        )
        self.assertEqual(
            {professional, *selected_layer3},
            {row["owner_skill"] for row in unresolved["reference_records"]},
        )
        self.assertLessEqual(len(selected_partitions), 4)

        exact_path = "references/generator-and-plugin-contracts.md"
        exact = VALIDATION.layer3_selector_expand_runtime_projection(
            base,
            None,
            profile="task-agent",
            selection_owner="engineering-brief",
            exact_layer3=[],
            selected_layer3=[],
            exact_references=[exact_path],
            exact_reference_bindings=[
                {"owner_skill": professional, "path": exact_path}
            ],
        )
        self.assertFalse(exact["reference_selector_loaded"])
        self.assertEqual([exact_path], exact["exact_references"])
        self.assertEqual([], exact["reference_records"])

        with self.assertRaisesRegex(VALIDATION.ValidationProblem, "partition"):
            VALIDATION.layer3_selector_expand_runtime_projection(
                base,
                {professional: selected_partitions[professional]},
                profile="task-agent",
                selection_owner="engineering-brief",
                exact_layer3=None,
                selected_layer3=selected_layer3,
                exact_references=None,
            )

    def test_reference_partitions_are_unique_complete_and_not_a_catalog(self) -> None:
        normalizer = getattr(
            VALIDATION, "layer3_selector_normalized_control_projections", None
        )
        self.assertTrue(callable(normalizer))
        selectors, partitions = normalizer(self.authority)
        forbidden = {"body", "content", "index", "catalog", "markdown"}
        for partition_name, partition in partitions.items():
            with self.subTest(partition=partition_name):
                professional = partition["professional_skill"]
                base = selectors.get(
                    f"{professional}/complete.json",
                    selectors[f"{professional}.json"],
                )
                self.assertEqual(
                    "changeforge.layer3-selector-reference-records-partition/v1",
                    partition["contract"],
                )
                identities = [
                    (row["owner_skill"], row["path"])
                    for row in partition["reference_records"]
                ]
                self.assertEqual(len(identities), len(set(identities)))
                self.assertTrue(
                    all(
                        row["type"] != "index"
                        and not (set(row) & forbidden)
                        and row["required_output"]
                        and row["owner_skill"] == partition["owner_skill"]
                        for row in partition["reference_records"]
                    )
                )
                self.assertEqual(
                    f"../reference-records/{professional}/{{owner_skill}}.json",
                    base["reference_records_partition"]["path_template"],
                )

    def test_expander_exact_reference_skip_and_invalid_bundles_fail_closed(self) -> None:
        normalizer = getattr(
            VALIDATION, "layer3_selector_normalized_control_projections", None
        )
        expander = getattr(
            VALIDATION, "layer3_selector_expand_runtime_projection", None
        )
        self.assertTrue(callable(normalizer))
        self.assertTrue(callable(expander))
        selectors, partitions = normalizer(self.authority)
        filename = "repository-tooling-change-builder.json"
        base = selectors[filename]
        skipped = expander(
            base,
            None,
            profile="task-agent",
            selection_owner="engineering-brief",
            exact_layer3=[],
            selected_layer3=[],
            exact_references=[],
        )
        self.assertFalse(skipped["selector_loaded"])
        self.assertFalse(skipped["reference_selector_loaded"])
        self.assertEqual([], skipped["exact_references"])
        self.assertEqual([], skipped["reference_records"])

        professional = base["professional_skill"]
        selected_partitions = {
            professional: copy.deepcopy(
                partitions[f"{professional}/{professional}.json"]
            )
        }
        duplicate = copy.deepcopy(selected_partitions)
        duplicate[professional]["reference_records"].append(
            copy.deepcopy(duplicate[professional]["reference_records"][0])
        )
        duplicate[professional]["records_sha256"] = hashlib.sha256(
            VALIDATION._canonical_selector_document_bytes(
                duplicate[professional]["reference_records"]
            )
        ).hexdigest()
        with self.assertRaisesRegex(VALIDATION.ValidationProblem, "duplicate"):
            expander(
                base,
                duplicate,
                profile="task-agent",
                selection_owner="main-control-agent",
                exact_layer3=None,
                selected_layer3=[],
                exact_references=None,
            )

        leaked = copy.deepcopy(selected_partitions)
        leaked[professional]["reference_records"][0]["owner_skill"] = "invented-owner"
        leaked[professional]["records_sha256"] = hashlib.sha256(
            VALIDATION._canonical_selector_document_bytes(
                leaked[professional]["reference_records"]
            )
        ).hexdigest()
        with self.assertRaisesRegex(
            VALIDATION.ValidationProblem, "owner"
        ):
            expander(
                base,
                leaked,
                profile="task-agent",
                selection_owner="main-control-agent",
                exact_layer3=None,
                selected_layer3=[],
                exact_references=None,
            )

        stale = copy.deepcopy(selected_partitions)
        stale[professional]["reference_records"][0]["load_when"] += " stale"
        with self.assertRaisesRegex(VALIDATION.ValidationProblem, "stale"):
            expander(
                base,
                stale,
                profile="task-agent",
                selection_owner="main-control-agent",
                exact_layer3=None,
                selected_layer3=[],
                exact_references=None,
            )

        with self.assertRaisesRegex(VALIDATION.ValidationProblem, "partition"):
            expander(
                base,
                None,
                profile="task-agent",
                selection_owner="main-control-agent",
                exact_layer3=None,
                selected_layer3=[],
                exact_references=None,
            )

        over_three = copy.deepcopy(base)
        profile = next(
            row
            for row in over_three["profile_authority"]
            if row["profile"] == "task-agent"
        )
        with self.assertRaisesRegex(VALIDATION.ValidationProblem, "0..3"):
            expander(
                over_three,
                None,
                profile="task-agent",
                selection_owner="main-control-agent",
                exact_layer3=profile["authorized_layer3"][:4],
                selected_layer3=profile["authorized_layer3"][:4],
                exact_references=[],
            )

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
                        self.assertEqual(
                            1, rendered.count("## JIT Reference Delivery")
                        )
                        self.assertEqual(
                            1,
                            rendered.count(
                                "engineering-control-plane/references/selectors/"
                                f"{item.name}.json"
                            ),
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
                        for forbidden in (
                            "## JIT Reference Delivery",
                            "Current-Professional JIT",
                            "engineering-control-plane/references/selectors/",
                            "never select/reroute/preload",
                            "index/catalog",
                        ):
                            self.assertNotIn(forbidden, rendered)
                self.assertEqual(source_root, source_path.read_text(encoding="utf-8"))

    def test_compiled_layer3_projection_has_no_jit_control_and_keeps_references(self) -> None:
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
                for forbidden in (
                    "## JIT Reference Delivery",
                    "Current-Professional JIT",
                    "engineering-control-plane/references/selectors/",
                    "never select/reroute/preload",
                    "index/catalog",
                ):
                    self.assertNotIn(forbidden, rendered)
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
            selector_root = control / "references/selectors"
            self.assertEqual(
                {
                    "engineering-change-analysis.json",
                    "engineering-change-analysis/complete.json",
                    "engineering-change-analysis/failure-diagnosis-analysis.json",
                },
                {
                    path.relative_to(selector_root).as_posix()
                    for path in selector_root.rglob("*.json")
                    if path.name == "engineering-change-analysis.json"
                    or path.parent.name == "engineering-change-analysis"
                },
            )
            selector = json.loads(
                (
                    control
                    / "references/selectors/repository-tooling-change-builder.json"
                ).read_text(encoding="utf-8")
            )
            partition_path = (
                control
                / "references/reference-records/repository-tooling-change-builder"
                / "repository-tooling-change-builder.json"
            )
            partition = json.loads(partition_path.read_text(encoding="utf-8"))
            self.assertEqual(
                "changeforge.layer3-selector-normalized-control/v1",
                selector["contract"],
            )
            self.assertNotIn("selection_surfaces", selector)
            self.assertNotIn("reference_records", selector)
            surface = VALIDATION.layer3_selector_expand_runtime_projection(
                selector,
                {"repository-tooling-change-builder": partition},
                profile="task-agent",
                selection_owner="main-control-agent",
                exact_layer3=None,
                selected_layer3=[],
                exact_references=None,
            )
            record = next(
                row for row in surface["reference_records"] if row["path"] == named
            )
            self.assertIn("boundary-decision", record["required_output"])
            self.assertTrue((professional / named).is_file())
            self.assertFalse(
                any(row["type"] == "index" for row in partition["reference_records"])
            )
        self.assertEqual(
            189,
            len(BUILD._top_level_items("dev", items)) - 1,
        )


if __name__ == "__main__":
    unittest.main()
