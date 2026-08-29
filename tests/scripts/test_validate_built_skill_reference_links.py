from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/validate-built-skill-reference-links.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(
        "validate_built_skill_reference_links_tests",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALIDATOR = _load_module()


class RenderedProfessionalBodyBudgetTests(unittest.TestCase):
    def _write_profile(self, root: Path, body_line_count: int) -> Path:
        profile_root = root / "recommended"
        skill_root = profile_root / "sample-professional"
        skill_root.mkdir(parents=True)
        fixed_lines = [
            "# Sample Professional",
            "## JIT Reference Delivery",
            "",
            "JIT: `engineering-control-plane/references/selectors/"
            "sample-professional.json`. Exact skips it; never select/reroute/preload",
            "index/catalog.",
            "## Layer 3 Delivery",
            "",
            "No Foundation or Domain Layer 3 items are assigned to this Skill.",
        ]
        self.assertGreaterEqual(body_line_count, len(fixed_lines))
        body = [
            fixed_lines[0],
            *("Bounded rendered fixture" for _ in range(body_line_count - len(fixed_lines))),
            *fixed_lines[1:],
        ]
        self.assertEqual(body_line_count, len(body))
        (skill_root / "SKILL.md").write_text(
            "---\n"
            "name: sample-professional\n"
            "description: Synthetic rendered Professional Skill.\n"
            "---\n"
            + "\n".join(body)
            + "\n",
            encoding="utf-8",
        )
        manifest = {
            "profile": "recommended",
            "top_level_skills": ["sample-professional"],
            "professional_skills": ["sample-professional"],
            "foundation_skills": [],
            "foundation_delivery_scopes": {},
            "compiled_foundation_skills": [],
            "domain_skills": [],
            "compiled_layer3_format": VALIDATOR.COMPILED_LAYER3_FORMAT,
            "compiled_layer3_references": {"sample-professional": []},
        }
        (profile_root / VALIDATOR.BUILD_MANIFEST_NAME).write_text(
            json.dumps(manifest),
            encoding="utf-8",
        )
        return profile_root

    def test_accepts_rendered_professional_body_at_hard_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile_root = self._write_profile(Path(temporary), 120)
            errors: list[str] = []
            VALIDATOR._validate_runtime(
                profile_root, errors, enforce_source_mapping=False
            )
            self.assertEqual([], errors)

    def test_rejects_rendered_professional_body_over_hard_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile_root = self._write_profile(Path(temporary), 121)
            errors: list[str] = []
            VALIDATOR._validate_runtime(
                profile_root, errors, enforce_source_mapping=False
            )
            self.assertTrue(
                any(
                    "rendered Professional SKILL.md body has 121 lines; maximum is 120"
                    in error
                    for error in errors
                ),
                errors,
            )

    def test_rejects_missing_or_duplicate_professional_jit_anchor(self) -> None:
        for mutation in ("missing", "duplicate"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                profile_root = self._write_profile(Path(temporary), 120)
                skill = profile_root / "sample-professional/SKILL.md"
                text = skill.read_text(encoding="utf-8")
                block = (
                    "## JIT Reference Delivery\n\n"
                    "JIT: `engineering-control-plane/references/selectors/"
                    "sample-professional.json`. Exact skips it; never select/reroute/preload\n"
                    "index/catalog.\n"
                )
                self.assertEqual(1, text.count(block))
                skill.write_text(
                    text.replace(block, "", 1)
                    if mutation == "missing"
                    else text.replace(block, block + "\n" + block, 1),
                    encoding="utf-8",
                )
                errors: list[str] = []
                VALIDATOR._validate_runtime(
                    profile_root, errors, enforce_source_mapping=False
                )
                self.assertTrue(
                    any(
                        "exactly one Professional JIT Reference Delivery and selector path"
                        in error
                        for error in errors
                    ),
                    errors,
                )

    def test_rejects_missing_or_unknown_compiled_layer3_format(self) -> None:
        for value in (None, "authoring-root-v1"):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as temporary:
                profile_root = self._write_profile(Path(temporary), 120)
                manifest_path = profile_root / VALIDATOR.BUILD_MANIFEST_NAME
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                if value is None:
                    manifest.pop("compiled_layer3_format")
                else:
                    manifest["compiled_layer3_format"] = value
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                errors: list[str] = []
                VALIDATOR._validate_runtime(
                    profile_root, errors, enforce_source_mapping=False
                )
                self.assertTrue(
                    any("compiled_layer3_format must equal" in error for error in errors),
                    errors,
                )

    def test_rejects_compiled_authoring_heading_in_projection(self) -> None:
        built = ROOT / "dist/universal/skills/recommended"
        self.assertTrue(built.is_dir(), "run the recommended build before this test")
        with tempfile.TemporaryDirectory() as temporary:
            profile_root = Path(temporary) / "recommended"
            shutil.copytree(built, profile_root)
            projection = (
                profile_root
                / "backend-change-builder/references/layer3/transaction-consistency.md"
            )
            text = projection.read_text(encoding="utf-8")
            self.assertIn("## Decision Boundary", text)
            projection.write_text(
                text.replace("## Decision Boundary", "## Skill Role", 1),
                encoding="utf-8",
            )
            errors: list[str] = []
            VALIDATOR._validate_runtime(profile_root, errors)
        self.assertTrue(
            any("compiled projection headings" in error for error in errors),
            errors,
        )

    def test_synchronized_manifest_index_and_files_cannot_reassign_owner(self) -> None:
        built = ROOT / "dist/universal/skills/recommended"
        self.assertTrue(built.is_dir(), "run the recommended build before this test")
        with tempfile.TemporaryDirectory() as temporary:
            profile_root = Path(temporary) / "recommended"
            shutil.copytree(built, profile_root)
            manifest_path = profile_root / VALIDATOR.BUILD_MANIFEST_NAME
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            candidate = "user-role-identification"
            source_owner = "change-intake-compiler"
            wrong_owner = "engineering-change-analysis"
            manifest["compiled_layer3_references"][source_owner].remove(candidate)
            manifest["compiled_layer3_references"][wrong_owner].append(candidate)
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            source_layer3 = profile_root / source_owner / "references/layer3"
            wrong_layer3 = profile_root / wrong_owner / "references/layer3"
            source_link = f"- [{candidate}]({candidate}.md)\n"
            source_index = source_layer3 / "index.md"
            source_text = source_index.read_text(encoding="utf-8")
            self.assertIn(source_link, source_text)
            source_index.write_text(
                source_text.replace(source_link, "", 1), encoding="utf-8"
            )
            with (wrong_layer3 / "index.md").open("a", encoding="utf-8") as handle:
                handle.write(source_link)
            shutil.move(source_layer3 / f"{candidate}.md", wrong_layer3)
            shutil.move(source_layer3 / candidate, wrong_layer3)

            errors: list[str] = []
            VALIDATOR._validate_runtime(profile_root, errors)
        candidate_mapping_errors = [
            error
            for error in errors
            if "does not match source Registry" in error and candidate in error
        ]
        self.assertEqual(2, len(candidate_mapping_errors), errors)


class CompiledLayer3ReadabilityTests(unittest.TestCase):
    @staticmethod
    def _projection(decision: str) -> str:
        return (
            "# sample-foundation\n\n"
            "## Decision Boundary\n\n"
            f"{decision}\n\n"
            "## High-Value Rules\n\n"
            "- Keep the changed invariant explicit.\n\n"
            "## Anti-Patterns\n\n"
            "- Reject evidence that predates the final edit.\n\n"
            "## Stop Conditions\n\n"
            "- Stop when the owner is unknown.\n"
        )

    def test_rejects_41_word_sentence_in_compiled_projection(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "sample-foundation.md"
            path.write_text(
                self._projection(" ".join(["word"] * 41) + "."),
                encoding="utf-8",
            )
            errors: list[str] = []
            VALIDATOR._validate_compiled_layer3_projection(
                path, "sample-foundation", "foundation", errors
            )
            self.assertTrue(
                any("sentence has 41 words; hard maximum is 40" in error for error in errors),
                errors,
            )

    def test_accepts_canonical_load_skip_projection(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            path = (
                root
                / "sample-professional/references/layer3/sample-foundation.md"
            )
            path.parent.mkdir(parents=True)
            path.write_text(
                self._projection("Keep the changed ownership boundary explicit."),
                encoding="utf-8",
            )
            physical = path.parent / "sample-foundation/references/checklist.md"
            physical.parent.mkdir(parents=True)
            physical.write_text("# Sample Checklist\n", encoding="utf-8")
            partition = (
                root
                / "engineering-control-plane/references/reference-records/"
                "sample-professional/sample-foundation.json"
            )
            partition.parent.mkdir(parents=True)
            records = [
                {
                    "owner_skill": "sample-foundation",
                    "owner_layer": "foundation",
                    "path": "references/checklist.md",
                    "type": "decision-checklist",
                    "load_when": "A checklist decision is required.",
                    "do_not_load_when": "No checklist decision is required.",
                    "required_by": ["task-agent"],
                    "required_output": ["checklist-result"],
                    "context_admissibility": None,
                    "residency": "singleton",
                }
            ]
            partition_document = {
                "contract": "changeforge.layer3-selector-reference-records-partition/v1",
                "authority_contract": "changeforge.layer3-selector-authority/v1",
                "professional_skill": "sample-professional",
                "owner_skill": "sample-foundation",
                "records_sha256": hashlib.sha256(
                    (json.dumps(records, sort_keys=True, separators=(",", ":")) + "\n").encode()
                ).hexdigest(),
                "reference_records": records,
            }
            partition_bytes = (
                json.dumps(
                    partition_document,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            ).encode()
            partition.write_bytes(partition_bytes)
            professional_partition = partition.parent / "sample-professional.json"
            empty_records: list[dict[str, object]] = []
            professional_partition.write_text(
                json.dumps(
                    {
                        "contract": "changeforge.layer3-selector-reference-records-partition/v1",
                        "authority_contract": "changeforge.layer3-selector-authority/v1",
                        "professional_skill": "sample-professional",
                        "owner_skill": "sample-professional",
                        "records_sha256": hashlib.sha256(b"[]\n").hexdigest(),
                        "reference_records": empty_records,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n",
                encoding="utf-8",
            )
            selector = (
                root
                / "engineering-control-plane/references/selectors/sample-professional.json"
            )
            selector.parent.mkdir(parents=True)
            selector.write_text(
                json.dumps(
                    {
                        "contract": "changeforge.layer3-selector-normalized-control/v1",
                        "authority_contract": "changeforge.layer3-selector-authority/v1",
                        "professional_skill": "sample-professional",
                        "maximum_layer3": 3,
                        "exact_layer3_bypass": True,
                        "profile_authority": [
                            {
                                "profile": "task-agent",
                                "selection_basis": "professional-risk",
                                "authorized_layer3": ["sample-foundation"],
                                "domain_authorization": [],
                                "selectors": [],
                            }
                        ],
                        "owner_surfaces": [
                            {
                                "profile": "task-agent",
                                "selection_owner": "main-control-agent",
                            }
                        ],
                        "reference_records_partition": {
                            "contract": "changeforge.layer3-selector-reference-records-partition/v1",
                            "path_template": (
                                "../reference-records/sample-professional/"
                                "{owner_skill}.json"
                            ),
                        },
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n",
                encoding="utf-8",
            )
            errors: list[str] = []
            VALIDATOR._validate_compiled_layer3_projection(
                path, "sample-foundation", "foundation", errors
            )
            self.assertEqual([], errors)

    def test_rejects_layer3_jit_and_control_policy(self) -> None:
        forbidden = (
            "## JIT Reference Delivery",
            "Current-Professional JIT",
            "engineering-control-plane/references/selectors/sample.json",
            "never select/reroute/preload",
            "index/catalog",
        )
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            for value in forbidden:
                with self.subTest(value=value):
                    path = root / "sample-foundation.md"
                    path.write_text(
                        self._projection(
                            "Keep the changed ownership boundary explicit."
                        )
                        + f"\n{value}\n",
                        encoding="utf-8",
                    )
                    errors: list[str] = []
                    VALIDATOR._validate_compiled_layer3_projection(
                        path, "sample-foundation", "foundation", errors
                    )
                    self.assertTrue(
                        any("Layer 3 JIT/control policy is forbidden" in error for error in errors),
                        errors,
                    )


class CompleteLayer3TemporaryProjectionTests(unittest.TestCase):
    @staticmethod
    def _tree_digest(root: Path) -> str:
        digest = hashlib.sha256()
        if not root.exists():
            return digest.hexdigest()
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(root).as_posix().encode("utf-8")
            digest.update(relative)
            digest.update(b"\0")
            if path.is_file():
                digest.update(path.read_bytes())
            digest.update(b"\0")
        return digest.hexdigest()

    def test_projects_all_layer3_sources_once_in_cleaned_temporary_storage(self) -> None:
        self.assertTrue(
            hasattr(VALIDATOR, "_validate_complete_layer3_temporary_projection"),
            "the dev-independent 163-item temporary projection proof is missing",
        )
        dist_before = self._tree_digest(ROOT / "dist")
        created_roots: list[Path] = []
        real_temporary_directory = tempfile.TemporaryDirectory

        def tracked_temporary_directory(*args, **kwargs):
            context = real_temporary_directory(*args, **kwargs)
            created_roots.append(Path(context.name))
            return context

        errors: list[str] = []
        with mock.patch.object(
            VALIDATOR.tempfile,
            "TemporaryDirectory",
            side_effect=tracked_temporary_directory,
        ):
            result = VALIDATOR._validate_complete_layer3_temporary_projection(errors)

        self.assertEqual([], errors)
        self.assertEqual(163, result["projected_count"])
        self.assertEqual(150, result["foundation_count"])
        self.assertEqual(13, result["domain_count"])
        self.assertEqual(154, result["runtime_jit_count"])
        self.assertEqual(9, result["non_runtime_count"])
        self.assertEqual(163, len(result["projected_names"]))
        self.assertEqual(163, len(set(result["projected_names"])))
        self.assertTrue(created_roots)
        self.assertTrue(all(not path.exists() for path in created_roots))
        self.assertEqual(dist_before, self._tree_digest(ROOT / "dist"))

    def test_rejects_repository_or_runtime_output_as_projection_root(self) -> None:
        forbidden = ROOT / "dist/complete-layer3-validation-forbidden"
        self.assertFalse(forbidden.exists())
        errors: list[str] = []
        result = VALIDATOR._validate_complete_layer3_projection_at(
            forbidden, errors
        )
        self.assertEqual(0, result["projected_count"])
        self.assertTrue(
            any(
                "must remain outside the repository and Runtime outputs" in error
                for error in errors
            ),
            errors,
        )
        self.assertFalse(forbidden.exists())

    def test_rejects_registry_source_disagreement_and_duplicate(self) -> None:
        registries = VALIDATOR.canonical_build._load_registries()
        items = {
            layer: VALIDATOR.canonical_build._load_items(layer, entries)
            for layer, entries in registries.items()
        }
        incomplete = dict(items)
        incomplete["foundation"] = items["foundation"][:-1]
        disagreement_errors: list[str] = []
        VALIDATOR._validate_layer3_registry_source_inventory(
            incomplete, disagreement_errors
        )
        self.assertTrue(
            any("Registry/source inventory disagrees" in error for error in disagreement_errors),
            disagreement_errors,
        )

        duplicate_registries = copy.deepcopy(registries)
        duplicate_registries["foundation"].append(
            copy.deepcopy(duplicate_registries["foundation"][0])
        )
        duplicate_errors: list[str] = []
        with mock.patch.object(
            VALIDATOR.canonical_build,
            "_load_registries",
            return_value=duplicate_registries,
        ):
            VALIDATOR._validate_complete_layer3_temporary_projection(
                duplicate_errors
            )
        self.assertTrue(
            any("duplicate foundation Skill" in error for error in duplicate_errors),
            duplicate_errors,
        )

    def test_rejects_missing_or_malformed_compact_projection(self) -> None:
        original = VALIDATOR.canonical_build._write_compact_layer3_root_projection

        for mutation in ("missing", "malformed-heading"):
            with self.subTest(mutation=mutation):
                def mutate(destination, item):
                    original(destination, item)
                    if item.name != "transaction-consistency":
                        return
                    skill_file = destination / "SKILL.md"
                    if mutation == "missing":
                        skill_file.unlink()
                    else:
                        text = skill_file.read_text(encoding="utf-8")
                        skill_file.write_text(
                            text.replace(
                                "## Skill Role",
                                "## Invalid Projection Heading",
                                1,
                            ),
                            encoding="utf-8",
                        )

                errors: list[str] = []
                with mock.patch.object(
                    VALIDATOR.canonical_build,
                    "_write_compact_layer3_root_projection",
                    side_effect=mutate,
                ):
                    VALIDATOR._validate_complete_layer3_temporary_projection(errors)
                expected = (
                    "is missing root SKILL.md"
                    if mutation == "missing"
                    else "compact foundation projection headings"
                )
                self.assertTrue(
                    any(expected in error for error in errors),
                    errors,
                )

    def test_rejects_missing_nested_reference_and_link(self) -> None:
        original = VALIDATOR.canonical_build._copy_skill_tree

        def inject_broken_nested_link(source, destination):
            original(source, destination)
            if destination.name != "targeted-validation-selection":
                return
            reference = (
                destination
                / "references/repository-command-entry-evidence.md"
            )
            with reference.open("a", encoding="utf-8") as handle:
                handle.write("\n[missing nested asset](../assets/missing-proof.txt)\n")

        errors: list[str] = []
        with mock.patch.object(
            VALIDATOR.canonical_build,
            "_copy_skill_tree",
            side_effect=inject_broken_nested_link,
        ):
            VALIDATOR._validate_complete_layer3_temporary_projection(errors)
        self.assertTrue(
            any("copied nested references files do not match" in error for error in errors),
            errors,
        )
        self.assertTrue(
            any("missing local temporary Layer 3 reference" in error for error in errors),
            errors,
        )

    def test_rejects_selector_ownership_mismatch(self) -> None:
        original = VALIDATOR._load_complete_selector_projection

        def remove_authorized_candidate(selector_path, errors):
            selector = original(selector_path, errors)
            if selector is None or selector_path.name != "backend-change-builder.json":
                return selector
            selector = copy.deepcopy(selector)
            for row in selector["profile_authority"]:
                row["authorized_layer3"] = [
                    candidate
                    for candidate in row["authorized_layer3"]
                    if candidate != "transaction-consistency"
                ]
                row["authorized_layer3"].append("skill-authoring-expert")
            return selector

        errors: list[str] = []
        with mock.patch.object(
            VALIDATOR,
            "_load_complete_selector_projection",
            side_effect=remove_authorized_candidate,
        ):
            VALIDATOR._validate_complete_layer3_temporary_projection(errors)
        self.assertTrue(
            any("selector ownership does not match" in error for error in errors),
            errors,
        )
        self.assertTrue(
            any(
                "non-Runtime Foundation Skills entered selector authorization"
                in error
                for error in errors
            ),
            errors,
        )

    def test_rejects_symlink_escape_in_temporary_projection(self) -> None:
        original = VALIDATOR.canonical_build._copy_skill_tree

        def inject_symlink(source, destination):
            original(source, destination)
            if destination.name == "targeted-validation-selection":
                (destination / "references/escape.md").symlink_to(
                    destination.parent / "outside-projection.md"
                )

        errors: list[str] = []
        with mock.patch.object(
            VALIDATOR.canonical_build,
            "_copy_skill_tree",
            side_effect=inject_symlink,
        ):
            VALIDATOR._validate_complete_layer3_temporary_projection(errors)
        self.assertTrue(
            any("must not be a symlink" in error for error in errors),
            errors,
        )


if __name__ == "__main__":
    unittest.main()
