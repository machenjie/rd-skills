from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


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
            VALIDATOR._validate_profile(
                profile_root, errors, enforce_source_mapping=False
            )
            self.assertEqual([], errors)

    def test_rejects_rendered_professional_body_over_hard_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile_root = self._write_profile(Path(temporary), 121)
            errors: list[str] = []
            VALIDATOR._validate_profile(
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
                VALIDATOR._validate_profile(
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
            VALIDATOR._validate_profile(profile_root, errors)
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
            VALIDATOR._validate_profile(profile_root, errors)
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
            "- Stop when the owner is unknown.\n\n"
            "## JIT Reference Delivery\n\n"
            "Current-Professional JIT. Exact skips it; never select/reroute/preload\n"
            "index/catalog.\n"
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
            selector = (
                root
                / "engineering-control-plane/references/selectors/sample-professional.json"
            )
            selector.parent.mkdir(parents=True)
            selector.write_text(
                json.dumps(
                    {
                        "contract": "changeforge.layer3-selector-control/v1",
                        "professional_skill": "sample-professional",
                        "selection_surfaces": [
                            {
                                "reference_records": [
                                    {
                                        "owner_skill": "sample-foundation",
                                        "path": "references/checklist.md",
                                        "required_output": ["checklist-result"],
                                        "type": "decision-checklist",
                                    }
                                ]
                            }
                        ],
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


if __name__ == "__main__":
    unittest.main()
