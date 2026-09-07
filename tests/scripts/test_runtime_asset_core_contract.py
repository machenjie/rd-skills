from __future__ import annotations

import base64
import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
CORE_PATH = ROOT / "src" / "control-model" / "core-contracts.json"
VALIDATION_PATH = ROOT / "scripts" / "validation_utils.py"
PROFESSIONAL_REGISTRY = ROOT / "src" / "registry" / "professional-skills.yaml"
FOUNDATION_REGISTRY = ROOT / "src" / "registry" / "foundation-skills.yaml"
DOMAIN_REGISTRY = ROOT / "src" / "registry" / "domain-skills.yaml"
BRIEF_PATH = (
    ROOT
    / "src"
    / "control-skills"
    / "engineering-control-plane"
    / "references"
    / "engineering-brief-template.md"
)
UTILITY_PATH = BRIEF_PATH.with_name("utility-capsule-template.md")
ANALYSIS_SKILL_PATH = (
    ROOT / "src" / "professional-skills" / "engineering-change-analysis" / "SKILL.md"
)
PROFILES_PATH = ROOT / "src" / "agent-profiles" / "role-agents.json"
MAIN_PATH = ROOT / "src" / "control-prompts" / "main-control-agent.md"

SOURCE_VERSION = "0.1.0"
AUTHORITATIVE_SHA256 = (
    "2df3b721098fbb06ad2f1f8140c9a4d0"
    "f2c80e6bb46785faa0cb362c13a0de50"
)
BUILD_IDENTITY = base64.urlsafe_b64encode(
    bytes.fromhex(AUTHORITATIVE_SHA256)[:16]
).decode("ascii").rstrip("=")
PROFESSIONAL = "engineering-change-analysis"
RECEIPT_PROFESSIONAL = "repository-tooling-change-builder"
INLINE_CONTRACT = "changeforge.runtime-inline-identity/v2"
JIT_LINE = (
    "JIT: `references/runtime/selector.json`; "
    f"Runtime: `{SOURCE_VERSION}/{BUILD_IDENTITY}`."
)
LAYER3_MARKER = (
    f"<!-- Build: {BUILD_IDENTITY} -->"
)


def _load_validation():
    spec = importlib.util.spec_from_file_location(
        "runtime_asset_validation_utils", VALIDATION_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_build():
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location(
        "runtime_asset_build", ROOT / "scripts/build.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _semantic_sha256(value: dict, hash_field: str) -> str:
    semantics = {key: item for key, item in value.items() if key != hash_field}
    return hashlib.sha256(
        json.dumps(
            semantics,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _canonical_json(value: dict) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _selector_asset(**extra: object) -> bytes:
    return _canonical_json(
        {
            "build": BUILD_IDENTITY,
            "contract": "changeforge.test-selector/v1",
            "professional_skill": PROFESSIONAL,
            **extra,
        }
    )


class RuntimeAssetCoreContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.core = json.loads(CORE_PATH.read_text(encoding="utf-8"))
        cls.validation = _load_validation()
        cls.build = _load_build()

    @staticmethod
    def _reference_record(
        *, owner_skill: str, owner_layer: str, path: str
    ) -> dict[str, object]:
        return {
            "owner_skill": owner_skill,
            "owner_layer": owner_layer,
            "path": path,
            "type": "targeted",
            "load_when": "the bounded behavior needs this exact Reference",
            "do_not_load_when": "the bounded behavior does not need this Reference",
            "required_by": ["task-agent"],
            "required_output": ["boundary-decision"],
            "context_admissibility": None,
            "residency": "singleton",
        }

    def _valid_bundle(self):
        reference_records = [
            self._reference_record(
                owner_skill=PROFESSIONAL,
                owner_layer="professional",
                path="references/analysis-evidence.md",
            )
        ]
        reference_partition = {
            "authority_contract": "changeforge.layer3-selector-authority/v1",
            "build": BUILD_IDENTITY,
            "contract": "changeforge.layer3-selector-reference-records-partition/v1",
            "owner_skill": PROFESSIONAL,
            "professional_skill": PROFESSIONAL,
            "records_sha256": hashlib.sha256(
                json.dumps(
                    reference_records,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
                + b"\n"
            ).hexdigest(),
            "reference_records": reference_records,
        }
        assets = {
            "SKILL.md": (
                f"---\nname: {PROFESSIONAL}\n---\n\n# Professional\n\n{JIT_LINE}\n"
            ).encode(),
            "references/runtime/selector.json": _selector_asset(kind="envelope"),
            "references/runtime/selectors/complete.json": _selector_asset(
                kind="complete"
            ),
            "references/runtime/selectors/change-kind.json": _selector_asset(
                kind="decision-shard"
            ),
            "references/runtime/reference-records/engineering-change-analysis.json": (
                _canonical_json(reference_partition)
            ),
            "references/layer3/minimal-correct-implementation.md": (
                f"{LAYER3_MARKER}\n\n# minimal-correct-implementation\n"
            ).encode(),
            "references/analysis-evidence.md": b"# Targeted Reference\n",
        }
        manifest = {
            "contract": "changeforge.runtime-integrity-manifest/v1",
            "schema_version": 1,
            "runtime_version": SOURCE_VERSION,
            "build_identity": BUILD_IDENTITY,
            "professional_skill": PROFESSIONAL,
            "assets": [
                {
                    "path": path,
                    "kind": "delivery-asset",
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "size": len(payload),
                }
                for path, payload in sorted(assets.items())
            ],
            "integrity_manifest_sha256": "",
        }
        manifest["integrity_manifest_sha256"] = _semantic_sha256(
            manifest, "integrity_manifest_sha256"
        )
        manifest_bytes = _canonical_json(manifest)
        root_binding = {
            "professional_skill": PROFESSIONAL,
            "runtime_version": SOURCE_VERSION,
            "authoritative_build_inputs_sha256": AUTHORITATIVE_SHA256,
            "build_identity_algorithm": "sha256-prefix-128-base64url-nopad",
            "build_identity": BUILD_IDENTITY,
            "inline_identity_contract": INLINE_CONTRACT,
            "inline_identity_version": 2,
            "integrity_manifest_path": "references/runtime/integrity-manifest.json",
            "integrity_manifest_full_bytes_sha256": hashlib.sha256(
                manifest_bytes
            ).hexdigest(),
        }
        return manifest_bytes, assets, root_binding

    def _verify(self, *bundle):
        return self.validation.runtime_asset_bundle_metadata_errors(
            *bundle,
            expected_source_version=SOURCE_VERSION,
            expected_authoritative_build_inputs_sha256=AUTHORITATIVE_SHA256,
            expected_professional_skill=PROFESSIONAL,
        )

    def test_core_freezes_inline_identity_and_removes_sidecar(self) -> None:
        contract = self.core["runtime_asset_resolution_contract"]
        inline = contract["inline_identity"]

        self.assertNotIn("runtime_identity", contract)
        self.assertEqual(INLINE_CONTRACT, inline["contract"])
        self.assertEqual("root-source-version", inline["runtime_version_source"])
        self.assertEqual(
            "authoritative-build-inputs-sha256-prefix-128-base64url-nopad",
            inline["build_identity_derivation"],
        )
        self.assertEqual(128, inline["build_identity_bits"])
        self.assertEqual("base64url-nopad-22", inline["build_identity_format"])
        self.assertEqual("frontmatter-name", inline["professional_binding"])
        self.assertEqual(
            "JIT: `references/runtime/selector.json`; Runtime: `<V>/<B>`.",
            inline["professional_entrypoint_jit_line"],
        )
        self.assertEqual("build", inline["selector_build_field"])
        self.assertEqual(
            [
                "selector-envelope",
                "direct-selector",
                "complete-selector",
                "decision-shard",
                "reference-record-partition",
            ],
            inline["selector_assets"],
        )
        self.assertEqual("single-existing-load-no-reread", inline["selector_read"])
        self.assertEqual("build", inline["selection_receipt_build_field"])
        self.assertEqual(
            "canonical-semantic-domain-includes-build",
            inline["selection_receipt_hash_domain"],
        )
        self.assertEqual(
            "<!-- Build: <B> -->",
            inline["layer3_first_line"],
        )
        self.assertEqual("replace-existing-generated-marker", inline["layer3_marker_mode"])
        self.assertEqual(
            "host-root-plus-receipt-plus-fixed-path",
            inline["layer3_professional_binding"],
        )

        reference_path = contract["reference_record_path"]
        self.assertEqual("build-only", reference_path["projection_owner"])
        self.assertEqual("read-path-verbatim", reference_path["runtime_read"])
        self.assertEqual(
            "references/<file>.md",
            reference_path["professional_path"],
        )
        self.assertEqual(
            "references/layer3/<owner-skill>/references/<file>.md",
            reference_path["layer3_path"],
        )
        self.assertEqual(
            ["path"], reference_path["runtime_path_fields"]
        )
        self.assertEqual(
            "references/<file>.md",
            contract["fixed_paths"]["professional_reference_record_path_template"],
        )
        self.assertEqual(
            "references/layer3/<owner-skill>/references/<file>.md",
            contract["fixed_paths"]["layer3_reference_record_path_template"],
        )
        self.assertIn(
            "reference-record-path-verbatim",
            contract["runtime_inline_verification"]["checks"],
        )
        self.assertIn(
            "reference-record-path-shape-and-exact-target",
            contract["non_runtime_verifier"]["checks"],
        )
        for forbidden in (
            "basename-inference",
            "owner-plus-relative-concatenation",
            "source-runtime-dual-path",
            "search-fallback",
            "glob-fallback",
            "HOME-fallback",
            "parent-fallback",
            "sibling-fallback",
        ):
            self.assertIn(forbidden, reference_path["forbidden"])

        self.assertNotIn("identity_path", contract["fixed_paths"])
        self.assertNotIn(
            "references/runtime/identity.json",
            contract["integrity_manifest"]["excluded_metadata_paths"],
        )
        self.assertEqual(
            ["references/runtime/integrity-manifest.json"],
            contract["integrity_manifest"]["excluded_metadata_paths"],
        )
        self.assertNotIn(
            "identity_path", contract["root_manifest_binding"]["fields"]
        )
        self.assertNotIn(
            "identity_full_bytes_sha256",
            contract["root_manifest_binding"]["fields"],
        )

    def test_non_runtime_verifier_accepts_inline_bundle(self) -> None:
        self.assertEqual([], self._verify(*self._valid_bundle()))

    def test_non_runtime_verifier_rejects_unreadable_reference_record_path(self) -> None:
        manifest, assets, root = self._valid_bundle()
        mutated = copy.deepcopy(assets)
        partition_path = (
            "references/runtime/reference-records/engineering-change-analysis.json"
        )
        partition = json.loads(mutated[partition_path])
        partition["reference_records"][0]["path"] = "references/missing.md"
        partition["records_sha256"] = hashlib.sha256(
            json.dumps(
                partition["reference_records"],
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        ).hexdigest()
        mutated[partition_path] = _canonical_json(partition)
        rebound = json.loads(manifest)
        rebound["assets"] = [
            {
                "path": path,
                "kind": "delivery-asset",
                "sha256": hashlib.sha256(payload).hexdigest(),
                "size": len(payload),
            }
            for path, payload in sorted(mutated.items())
        ]
        rebound["integrity_manifest_sha256"] = _semantic_sha256(
            rebound,
            "integrity_manifest_sha256",
        )
        rebound_bytes = _canonical_json(rebound)
        rebound_root = copy.deepcopy(root)
        rebound_root["integrity_manifest_full_bytes_sha256"] = hashlib.sha256(
            rebound_bytes
        ).hexdigest()
        errors = self._verify(rebound_bytes, mutated, rebound_root)
        self.assertTrue(any("no exact delivery target" in error for error in errors), errors)

    def test_build_projects_exact_professional_and_layer3_reference_paths(self) -> None:
        professional = self._reference_record(
            owner_skill=PROFESSIONAL,
            owner_layer="professional",
            path="references/analysis-evidence.md",
        )
        layer3 = self._reference_record(
            owner_skill="minimal-correct-implementation",
            owner_layer="foundation",
            path="references/checklist.md",
        )
        self.assertEqual(
            "references/analysis-evidence.md",
            self.build._project_runtime_reference_record_path(
                professional,
                PROFESSIONAL,
            ),
        )
        self.assertEqual(
            "references/layer3/minimal-correct-implementation/references/checklist.md",
            self.build._project_runtime_reference_record_path(
                layer3,
                PROFESSIONAL,
            ),
        )

    def test_runtime_reference_target_reads_only_the_record_path_verbatim(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / PROFESSIONAL
            exact = root / "references/layer3/minimal-correct-implementation/references/checklist.md"
            exact.parent.mkdir(parents=True)
            exact.write_text("exact\n", encoding="utf-8")
            record = self._reference_record(
                owner_skill="minimal-correct-implementation",
                owner_layer="foundation",
                path="references/layer3/minimal-correct-implementation/references/checklist.md",
            )
            with mock.patch.object(
                Path,
                "expanduser",
                side_effect=AssertionError("Runtime must not inspect HOME"),
            ):
                self.assertEqual(
                    exact,
                    self.validation.runtime_reference_record_target(
                        root,
                        record,
                        expected_professional_skill=PROFESSIONAL,
                        context="valid Runtime record",
                    ),
                )

            inferred_only = root / "references/checklist.md"
            inferred_only.write_text("basename fallback\n", encoding="utf-8")
            missing = copy.deepcopy(record)
            missing["path"] = (
                "references/layer3/minimal-correct-implementation/"
                "references/missing.md"
            )
            with self.assertRaisesRegex(
                self.validation.ValidationProblem,
                "missing regular file",
            ):
                self.validation.runtime_reference_record_target(
                    root,
                    missing,
                    expected_professional_skill=PROFESSIONAL,
                    context="no basename fallback",
                )

    def test_runtime_reference_target_rejects_path_mutations_and_links(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / PROFESSIONAL
            valid = root / "references/analysis-evidence.md"
            valid.parent.mkdir(parents=True)
            valid.write_text("valid\n", encoding="utf-8")
            base = self._reference_record(
                owner_skill=PROFESSIONAL,
                owner_layer="professional",
                path="references/analysis-evidence.md",
            )
            for label, path in (
                ("absolute", "/tmp/analysis-evidence.md"),
                ("traversal", "references/../analysis-evidence.md"),
                ("dual", "references/analysis-evidence.md|src/reference.md"),
                ("glob", "references/*.md"),
                ("home", "~/references/analysis-evidence.md"),
                ("parent", "../references/analysis-evidence.md"),
                ("sibling", "references/../../sibling/analysis-evidence.md"),
                ("owner-relative", "minimal-correct-implementation/references/checklist.md"),
            ):
                mutant = copy.deepcopy(base)
                mutant["path"] = path
                with self.subTest(label=label), self.assertRaises(
                    self.validation.ValidationProblem
                ):
                    self.validation.runtime_reference_record_target(
                        root,
                        mutant,
                        expected_professional_skill=PROFESSIONAL,
                        context=label,
                    )

            directory = copy.deepcopy(base)
            directory["path"] = "references/not-a-file.md"
            (root / str(directory["path"])).mkdir()
            with self.assertRaisesRegex(
                self.validation.ValidationProblem,
                "missing regular file",
            ):
                self.validation.runtime_reference_record_target(
                    root,
                    directory,
                    expected_professional_skill=PROFESSIONAL,
                    context="directory",
                )

            outside = Path(raw) / "outside.md"
            outside.write_text("outside\n", encoding="utf-8")
            linked = copy.deepcopy(base)
            linked["path"] = "references/linked.md"
            (root / str(linked["path"])).symlink_to(outside)
            with self.assertRaisesRegex(
                self.validation.ValidationProblem,
                "symlink",
            ):
                self.validation.runtime_reference_record_target(
                    root,
                    linked,
                    expected_professional_skill=PROFESSIONAL,
                    context="symlink",
                )

    def test_non_runtime_verifier_rejects_missing_or_mismatched_inline_markers(self) -> None:
        manifest, assets, root = self._valid_bundle()
        mutations: list[tuple[bytes, dict[str, bytes], dict[str, object]]] = []

        def rebind(mutated_assets: dict[str, bytes]):
            rebound_manifest = json.loads(manifest)
            rebound_manifest["assets"] = [
                {
                    "path": path,
                    "kind": "delivery-asset",
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "size": len(payload),
                }
                for path, payload in sorted(mutated_assets.items())
            ]
            rebound_manifest["integrity_manifest_sha256"] = _semantic_sha256(
                rebound_manifest, "integrity_manifest_sha256"
            )
            rebound_bytes = _canonical_json(rebound_manifest)
            rebound_root = copy.deepcopy(root)
            rebound_root["integrity_manifest_full_bytes_sha256"] = hashlib.sha256(
                rebound_bytes
            ).hexdigest()
            return rebound_bytes, mutated_assets, rebound_root

        sidecar = copy.deepcopy(assets)
        sidecar["references/runtime/identity.json"] = b"{}\n"
        mutations.append(rebind(sidecar))

        missing_professional_marker = copy.deepcopy(assets)
        missing_professional_marker["SKILL.md"] = b"---\nname: engineering-change-analysis\n---\n"
        mutations.append(rebind(missing_professional_marker))

        wrong_selector_build = copy.deepcopy(assets)
        selector = json.loads(wrong_selector_build["references/runtime/selector.json"])
        selector["build"] = "_____________________w"
        wrong_selector_build["references/runtime/selector.json"] = _canonical_json(
            selector
        )
        mutations.append(rebind(wrong_selector_build))

        malformed_selector = copy.deepcopy(assets)
        malformed_selector["references/runtime/selectors/change-kind.json"] = b"{\n"
        mutations.append(rebind(malformed_selector))

        missing_layer3_marker = copy.deepcopy(assets)
        missing_layer3_marker[
            "references/layer3/minimal-correct-implementation.md"
        ] = b"# minimal-correct-implementation\n"
        mutations.append(rebind(missing_layer3_marker))

        stale_layer3_marker = copy.deepcopy(assets)
        stale_layer3_marker[
            "references/layer3/minimal-correct-implementation.md"
        ] = (
            f"<!-- Generated by scripts/build.py; Build: {BUILD_IDENTITY}. -->\n\n"
            "# minimal-correct-implementation\n"
        ).encode()
        mutations.append(rebind(stale_layer3_marker))

        wrong_prefix = copy.deepcopy(root)
        wrong_prefix["build_identity"] = "_____________________w"
        mutations.append((manifest, assets, wrong_prefix))

        for candidate in mutations:
            with self.subTest(candidate=candidate[1].keys()):
                self.assertTrue(self._verify(*candidate))

    def test_selection_receipt_build_identity_is_verified(self) -> None:
        authority = self.validation.layer3_selector_authority(
            self.validation.load_yaml_file(FOUNDATION_REGISTRY),
            self.validation.load_yaml_file(PROFESSIONAL_REGISTRY),
            self.validation.load_yaml_file(DOMAIN_REGISTRY),
            context="inline Runtime identity receipt test",
        )
        projection = self.validation.layer3_selector_runtime_projection(
            authority,
            professional_skill=RECEIPT_PROFESSIONAL,
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=[],
        )
        receipt = self.validation.layer3_selector_runtime_selection_receipt(
            projection,
            evidence_signals=[],
            build_identity=BUILD_IDENTITY,
        )
        self.assertEqual(BUILD_IDENTITY, receipt["build"])
        self.assertEqual(
            [],
            self.validation.layer3_selector_runtime_selection_receipt_errors(
                receipt,
                expected_owner="main-control-agent",
                expected_profile="task-agent",
                expected_professional=RECEIPT_PROFESSIONAL,
                expected_selection_kind="implementation-risk",
                expected_selected_layer3=[],
                expected_build_identity=BUILD_IDENTITY,
            ),
        )
        for invalid in (None, "0" * 32, "A" * 21 + "B", "A" * 21 + "="):
            mutant = copy.deepcopy(receipt)
            if invalid is None:
                del mutant["build"]
            else:
                mutant["build"] = invalid
            with self.subTest(build=invalid):
                self.assertTrue(
                    self.validation.layer3_selector_runtime_selection_receipt_errors(
                        mutant,
                        expected_owner="main-control-agent",
                        expected_profile="task-agent",
                        expected_professional=RECEIPT_PROFESSIONAL,
                        expected_selection_kind="implementation-risk",
                        expected_selected_layer3=[],
                        expected_build_identity=BUILD_IDENTITY,
                    )
                )

    def test_runtime_roles_use_existing_components_and_fail_closed(self) -> None:
        runtime = self.core["runtime_asset_resolution_contract"]
        self.assertEqual(
            [
                "professional-entrypoint",
                "logical-selection-receipt",
                "current-fixed-assets",
            ],
            runtime["runtime_inline_verification"]["inputs"],
        )
        self.assertEqual(
            ["integrity-manifest", "root-build-manifest"],
            runtime["runtime_roles"]["forbidden_reads"],
        )
        self.assertEqual([], runtime["runtime_roles"]["digest_operations"])
        self.assertEqual("fail-closed-no-utility-no-reroute", runtime["failure"])
        self.assertEqual(
            "professional-entrypoint-and-logical-selection-receipt-and-layer3-"
            "binding-required-selector-skipped",
            runtime["exact_set_bypass"],
        )

    def test_context_contract_counts_no_identity_component_or_selector_reload(self) -> None:
        projection = self.core["context_budget_contract"]["runtime_asset_projection"]
        self.assertEqual("inline-existing-component-bytes", projection["identity_accounting"])
        self.assertEqual(0, projection["identity_component_count_per_professional_assignment"])
        self.assertEqual(0, projection["integrity_manifest_runtime_load_count"])
        self.assertEqual(0, projection["selective_identity_field_read_count"])
        self.assertEqual(0, projection["identity_structural_selector_load_delta_max"])
        self.assertEqual(
            [
                "professional-entrypoint",
                "selector-or-reference-partition",
                "logical-selection-receipt",
                "targeted-reference-layer3-marker",
            ],
            projection["inline_accounted_components"],
        )
        for retired in (
            "candidate_b_max_identity_tokens",
            "candidate_b_maximizer",
            "candidate_a_review_delta",
            "candidate_b_task_delta",
            "candidate_b_review_delta",
        ):
            self.assertNotIn(retired, projection)
        self.assertEqual(
            "unproved-stop-on-context-route-coverage-or-binding-failure",
            projection["post_implementation_gate"],
        )
        self.assertEqual(32, projection["ordinary_delta_gate"]["absolute_token_max"])
        self.assertEqual(15_000, projection["ordinary_delta_gate"]["relative_ppm"])
        self.assertFalse(
            self.core["context_budget_contract"]["quality_cost_gate"][
                "candidate_total_not_greater_is_correctness_acceptance"
            ]
        )








if __name__ == "__main__":
    unittest.main()
