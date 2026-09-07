from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validation_utils as VALIDATION  # noqa: E402


def load_script(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PACKAGE = load_script("build_input_freshness_package", "scripts/package.py")
INSTALLATION = load_script(
    "build_input_freshness_installation",
    "scripts/validate-installation.py",
)


class BuildInputFreshnessTests(unittest.TestCase):
    def _repository(self, root: Path) -> None:
        (root / "src/registry").mkdir(parents=True)
        (root / "src/registry/sample.yaml").write_text(
            "schema_version: 1\n",
            encoding="utf-8",
        )
        (root / "scripts").mkdir()
        for producer in VALIDATION.CORE_CONTRACTS[
            "principle_acceptance_contract"
        ]["producers"]:
            producer_path = root / producer["argv"][1]
            producer_path.parent.mkdir(parents=True, exist_ok=True)
            producer_path.write_text("# canonical producer\n", encoding="utf-8")
        (root / "scripts/build.py").write_text("# build\n", encoding="utf-8")
        (root / "scripts/validation_utils.py").write_text(
            "# validation\n",
            encoding="utf-8",
        )
        (root / "pyproject.toml").write_text(
            '[project]\nversion = "1.0.0"\n',
            encoding="utf-8",
        )

    def _snapshot(self, root: Path) -> dict[str, object]:
        return VALIDATION.authoritative_build_input_snapshot(root)

    def test_modification_untracked_addition_and_deletion_make_snapshot_stale(self) -> None:
        mutations = (
            lambda root: (root / "src/registry/sample.yaml").write_text(
                "schema_version: 2\n",
                encoding="utf-8",
            ),
            lambda root: (root / "src/untracked.md").write_text(
                "new authoritative input\n",
                encoding="utf-8",
            ),
            lambda root: (root / "src/registry/sample.yaml").unlink(),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                with tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    self._repository(root)
                    recorded = self._snapshot(root)
                    mutate(root)
                    errors = VALIDATION.authoritative_build_input_snapshot_errors(
                        recorded,
                        root,
                    )
                    self.assertTrue(
                        any("stale" in error for error in errors),
                        errors,
                    )

    def test_required_producer_deletion_makes_old_snapshot_stale(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root)
            recorded = self._snapshot(root)
            (root / "scripts/validate-skills.py").unlink()

            errors = VALIDATION.authoritative_build_input_snapshot_errors(
                recorded,
                root,
            )

            self.assertTrue(any("stale" in error for error in errors), errors)

    def test_semantic_marker_change_remains_a_build_provenance_change(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root)
            source = root / "src/marker.md"
            source.write_text(
                "<!-- rd-semantic-id:v2 finding=unconditional_absolute_candidate "
                "rule=sample/rule occurrence=first -->\n"
                "- Retain current evidence.\n",
                encoding="utf-8",
            )
            recorded = self._snapshot(root)
            source.write_text(
                "<!-- rd-semantic-id:v2 finding=unconditional_absolute_candidate "
                "rule=sample/rule occurrence=second -->\n"
                "- Retain current evidence.\n",
                encoding="utf-8",
            )

            self.assertTrue(
                any(
                    "stale" in error
                    for error in VALIDATION.authoritative_build_input_snapshot_errors(
                        recorded, root
                    )
                )
            )

    def test_irrelevant_generated_outputs_and_caches_are_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root)
            recorded = self._snapshot(root)
            for relative in (
                "dist/generated.txt",
                "reports/result.json",
                "docs/SHOWCASE.md",
                "evals/pressure/outputs/result.json",
                "src/__pycache__/cache.pyc",
                "src/.pytest_cache/state",
                "src/.DS_Store",
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("irrelevant\n", encoding="utf-8")
            self.assertEqual(
                [],
                VALIDATION.authoritative_build_input_snapshot_errors(recorded, root),
            )

    def test_git_unavailable_is_explicit_and_audit_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root)
            with mock.patch.object(
                VALIDATION.subprocess,
                "run",
                side_effect=FileNotFoundError,
            ):
                recorded = self._snapshot(root)
            self.assertEqual(
                {"head": None, "state": "unavailable"},
                recorded["git"],
            )

            prior_commit = deepcopy(recorded)
            prior_commit["git"] = {"head": "a" * 40, "state": "dirty"}
            self.assertEqual(
                [],
                VALIDATION.authoritative_build_input_snapshot_errors(
                    prior_commit,
                    root,
                ),
            )

    def test_package_rejects_a_stale_manifest_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            self._repository(root)
            source = root / "dist/universal/skills/recommended"
            names = {
                layer: [entry["name"] for entry in VALIDATION.load_yaml_file(
                    ROOT / "src/registry" / filename
                )[key]]
                for layer, filename, key in (
                    ("control", "control-skills.yaml", "control_skills"),
                    ("professional", "professional-skills.yaml", "professional_skills"),
                    ("foundation", "foundation-skills.yaml", "foundation_skills"),
                    ("domain", "domain-skills.yaml", "domain_skills"),
                )
            }
            for name in [*names["control"], *names["professional"]]:
                skill = source / name
                skill.mkdir(parents=True)
                (skill / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")
            manifest_path = source / ".changeforge-build-manifest.json"
            manifest = {
                "profile": "recommended",
                "authoritative_build_inputs": self._snapshot(root),
                "top_level_skills": [*names["control"], *names["professional"]],
                "control_skills": names["control"],
                "professional_skills": names["professional"],
                "foundation_skills": names["foundation"],
                "domain_skills": names["domain"],
                "compiled_layer3_references": {
                    name: [] for name in names["professional"]
                },
                "foundation_mode": "targeted-product-references",
                "domain_mode": "targeted-references",
                "agent_profiles": [
                    "main-control-agent",
                    "analysis-agent",
                    "task-agent",
                    "review-agent",
                ],
            }
            manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
            (root / "src/registry/sample.yaml").write_text(
                "schema_version: 2\n",
                encoding="utf-8",
            )
            zip_root = root / "dist/openai-api/zips"

            with mock.patch.multiple(
                PACKAGE,
                ROOT=root,
                BUILT_SKILLS_ROOT=source.parent,
                ZIP_DIR=zip_root,
            ), mock.patch.object(
                PACKAGE,
                "_authoritative_runtime_inventory",
                return_value={
                    **names,
                    "top_level": [*names["control"], *names["professional"]],
                    "compiled": manifest["compiled_layer3_references"],
                },
            ):
                with self.assertRaisesRegex(PACKAGE.PackageError, "stale"):
                    PACKAGE.package_profile()
            self.assertFalse(zip_root.exists())

    def test_installation_reports_a_stale_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root)
            manifest_path = root / ".changeforge-build-manifest.json"
            manifest = {"authoritative_build_inputs": self._snapshot(root)}
            (root / "scripts/build.py").write_text(
                "# changed build logic\n",
                encoding="utf-8",
            )

            errors = INSTALLATION._build_input_freshness_errors(
                manifest,
                manifest_path,
                repository_root=root,
            )
            self.assertTrue(any("stale" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
