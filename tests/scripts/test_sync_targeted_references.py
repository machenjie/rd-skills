from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"


def _load_module():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(
        "sync_targeted_references_tests",
        SCRIPTS / "sync-targeted-references.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SYNC = _load_module()


class SyncTargetedReferencesTests(unittest.TestCase):
    def _fixture(self, root: Path) -> Path:
        registry_root = root / "src" / "registry"
        registry_root.mkdir(parents=True)
        (registry_root / "control-skills.yaml").write_text(
            "schema_version: 3\ncontrol_skills: []\n", encoding="utf-8"
        )
        (registry_root / "professional-skills.yaml").write_text(
            "schema_version: 4\nprofessional_skills: []\n", encoding="utf-8"
        )
        domain_names = [
            f"fixture-domain-extension-{index:02d}"
            for index in range(13)
        ]
        domain_rows = "".join(
            f"  - name: {name}\n"
            "    routing_mode: modifier-only\n"
            "    used_by: [fixture-professional-owner]\n"
            "    role_support: [analysis-agent]\n"
            f"    path: src/domain-extensions/{name}\n"
            "    reference_index: []\n"
            for name in domain_names
        )
        (registry_root / "domain-skills.yaml").write_text(
            "schema_version: 6\n"
            "domain_skills:\n"
            f"{domain_rows}",
            encoding="utf-8",
        )
        (registry_root / "foundation-skills.yaml").write_text(
            "schema_version: 8\n"
            "foundation_skills:\n"
            "  - name: cache-design\n"
            "    path: src/foundation/capabilities/cache-design\n"
            "    required_expertise_tags: [foundation-data-middleware]\n"
            "    reference_index:\n"
            "      - path: references/checklist.md\n"
            "        type: decision-checklist\n"
            "        load_when: cache invalidation changes require failure coverage\n"
            "        do_not_load_when: no cache behavior or ownership changes\n"
            "        required_by: [task-agent]\n"
            "        required_output: [checklist-result]\n",
            encoding="utf-8",
        )
        skill = root / "src" / "foundation" / "capabilities" / "cache-design" / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text(
            "---\nname: cache-design\ndescription: Fixture.\n---\n\n"
            "# Cache Design\n\n## Targeted References\n\n"
            "- [checklist.md](references/checklist.md)\n",
            encoding="utf-8",
        )
        for domain_name in domain_names:
            domain_skill = (
                root
                / "src"
                / "domain-extensions"
                / domain_name
                / "SKILL.md"
            )
            domain_skill.parent.mkdir(parents=True)
            domain_skill.write_text(
                f"---\nname: {domain_name}\ndescription: Fixture.\n---\n\n"
                f"# {domain_name}\n\n## Targeted References\n\n"
                "- No task-local Reference is indexed for this Skill.\n",
                encoding="utf-8",
            )
        return skill

    def test_check_write_and_second_check_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            skill = self._fixture(root)

            drift, errors, checked = SYNC.synchronize(root=root, write=False)
            self.assertEqual([], errors)
            self.assertEqual(14, checked)
            self.assertEqual(
                ["src/foundation/capabilities/cache-design/SKILL.md"], drift
            )

            written, errors, checked = SYNC.synchronize(root=root, write=True)
            self.assertEqual([], errors)
            self.assertEqual(14, checked)
            self.assertEqual(drift, written)
            self.assertIn(
                "| Path | Type | Load when | Do not load when | Required by | Required output |\n"
                "|---|---|---|---|---|---|\n"
                "| [checklist](references/checklist.md) | decision-checklist | "
                "cache invalidation changes require failure coverage | "
                "no cache behavior or ownership changes | task-agent | checklist-result |",
                skill.read_text(encoding="utf-8"),
            )
            self.assertTrue(
                skill.read_text(encoding="utf-8").endswith(
                    "task-agent | checklist-result |\n"
                )
            )

            drift, errors, checked = SYNC.synchronize(root=root, write=False)
            self.assertEqual(([], [], 14), (drift, errors, checked))

    def test_invalid_domain_registry_never_partially_writes_any_skill(self) -> None:
        mutations = {
            "schema-v5": ("schema_version: 6", "schema_version: 5"),
            "unknown-routing-mode": (
                "routing_mode: modifier-only",
                "routing_mode: sometimes",
            ),
        }
        for label, (current, invalid) in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                self._fixture(root)
                registry = root / "src/registry/domain-skills.yaml"
                registry.write_text(
                    registry.read_text(encoding="utf-8").replace(
                        current,
                        invalid,
                        1,
                    ),
                    encoding="utf-8",
                )
                before = {
                    path.relative_to(root).as_posix(): path.read_bytes()
                    for path in sorted((root / "src").rglob("SKILL.md"))
                }

                drift, errors, checked = SYNC.synchronize(
                    root=root,
                    write=True,
                )

                after = {
                    path.relative_to(root).as_posix(): path.read_bytes()
                    for path in sorted((root / "src").rglob("SKILL.md"))
                }
                self.assertEqual([], drift)
                self.assertEqual(0, checked)
                self.assertTrue(errors)
                self.assertEqual(before, after)

    def test_missing_or_duplicate_section_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            skill = self._fixture(root)
            for body in (
                "# Cache Design\n",
                "# Cache Design\n\n## Targeted References\n\n- One.\n\n"
                "## Targeted References\n\n- Two.\n",
            ):
                with self.subTest(body=body):
                    skill.write_text(body, encoding="utf-8")
                    drift, errors, checked = SYNC.synchronize(
                        root=root, write=False
                    )
                    self.assertEqual([], drift)
                    self.assertEqual(0, checked)
                    self.assertTrue(
                        any(
                            "expected exactly one Targeted References section"
                            in error
                            for error in errors
                        ),
                        errors,
                    )

    def test_unsafe_registry_path_fails_before_sync_write(self) -> None:
        for path in (
            "references/bad path.md",
            "references/bad[name].md",
            "references/bad(name).md",
            r"references/bad\name.md",
            "references/bad|name.md",
        ):
            with self.subTest(path=path), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                skill = self._fixture(root)
                before = skill.read_text(encoding="utf-8")
                registry_path = root / "src/registry/foundation-skills.yaml"
                registry_path.write_text(
                    registry_path.read_text(encoding="utf-8").replace(
                        "references/checklist.md", path
                    ),
                    encoding="utf-8",
                )

                drift, errors, checked = SYNC.synchronize(root=root, write=True)

                self.assertEqual([], drift)
                self.assertEqual(0, checked)
                self.assertTrue(
                    any("Markdown-link-safe slugs" in error for error in errors),
                    errors,
                )
                self.assertEqual(before, skill.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
