from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_build_module():
    spec = importlib.util.spec_from_file_location(
        "hookless_build_safety_tests",
        ROOT / "scripts/build.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BUILD = load_build_module()

import validation_utils as VALIDATION  # noqa: E402

from validation_utils import (  # noqa: E402
    AUTHORITATIVE_BUILD_INPUT_FILES,
    CONTEXT_BUDGET_MODEL,
    _foundation_activation_field_errors,
    count_o200k_base_tokens,
    derived_context_budget_limits,
)


class BuildSafetyTests(unittest.TestCase):
    @staticmethod
    def _current_handoff(kind: str) -> dict[str, object]:
        artifact: object = (
            "diff --git a/owner.py b/owner.py\n"
            "--- a/owner.py\n"
            "+++ b/owner.py\n"
            "@@ -1 +1 @@\n-old\n+new\n"
        )
        if kind == "reviewer-accessible-native-reference":
            artifact = {
                "reference": "native-change://codex/current-worktree",
                "generation": 7,
                "reviewer": "review-agent",
                "changed_paths": ["owner.py"],
                "readable": True,
            }
        return {
            "latest_changed_paths": ["owner.py"],
            "exact_change_evidence": {
                "kind": kind,
                "artifact": artifact,
                "generation": 7,
            },
            "reviewer_artifact_accessibility": {
                "reviewer": "review-agent",
                "generation": 7,
                "changed_paths": ["owner.py"],
                "readable": True,
            },
            "validation_after_latest_material_edit": {
                "evidence_id": "focused-projection-test",
                "result": "passed",
                "generation": 7,
            },
            "fixed_review_scope": ["owner.py"],
        }

    def test_review_readiness_has_one_deterministic_owner(self) -> None:
        self.assertTrue(
            VALIDATION.review_input_ready(
                self._current_handoff("exact-change-content")
            )
        )
        for obsolete in (
            "_normalized_declared_capability_ceiling",
            "_normalized_decision_capabilities",
            "_main_capability_projection",
            "_render_decision_capability_facts",
        ):
            self.assertFalse(hasattr(BUILD, obsolete), obsolete)

    def test_runtime_strips_source_only_semantic_identity_markers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = root / "sample" / "SKILL.md"
            reference = root / "sample" / "references" / "rule.md"
            reference.parent.mkdir(parents=True)
            skill.write_text(
                "# Sample\n\n<!-- rd-semantic-id:v2 "
                "finding=unconditional_mechanism_candidate "
                "rule=sample/rule occurrence=root -->\n"
                "- Every operation retains an owner.\n",
                encoding="utf-8",
            )
            reference.write_text(
                "# Rule\n\n<!-- rd-semantic-id:v2 "
                "finding=unconditional_absolute_candidate "
                "rule=sample/evidence occurrence=reference -->\n"
                "- Record current evidence.\n",
                encoding="utf-8",
            )

            BUILD._strip_runtime_semantic_markers(root / "sample")

            self.assertNotIn("rd-semantic-id:", skill.read_text(encoding="utf-8"))
            self.assertNotIn(
                "rd-semantic-id:", reference.read_text(encoding="utf-8")
            )

    def test_runtime_rejects_malformed_semantic_identity_marker_leakage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = root / "SKILL.md"
            skill.write_text(
                "# Sample\n\n<!-- rd-semantic-id:v2 "
                "finding=unconditional_mechanism_candidate "
                "rule=bad--rule occurrence=root -->\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(BUILD.BuildError, "malformed semantic identity"):
                BUILD._strip_runtime_semantic_markers(root)

    def test_semantic_marker_inventory_preflight_accepts_valid_sources(self) -> None:
        class SnapshotReached(RuntimeError):
            pass

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            self._copy_source(root)
            sentinel = root / "dist/sentinel.bin"
            sentinel.parent.mkdir(parents=True)
            sentinel.write_bytes(b"unchanged")

            with self._layout(root):
                registries = BUILD._load_registries()
                BUILD._preflight_registry_entries(registries)
                BUILD._preflight_semantic_marker_inventory(registries)
                with mock.patch.object(
                    BUILD,
                    "authoritative_build_input_snapshot",
                    side_effect=SnapshotReached,
                ) as snapshot:
                    with self.assertRaises(SnapshotReached):
                        BUILD.build_profile("recommended")

            snapshot.assert_called_once_with(root)
            self.assertEqual(b"unchanged", sentinel.read_bytes())

    def _assert_marker_preflight_failure_preserves_outputs(
        self, mutate, message: str
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            self._copy_source(root)
            mutate(root)
            sentinel = root / "dist/sentinel.bin"
            sentinel.parent.mkdir(parents=True)
            sentinel.write_bytes(b"unchanged")

            with self._layout(root), mock.patch.object(
                BUILD, "authoritative_build_input_snapshot"
            ) as snapshot, self.assertRaisesRegex(BUILD.BuildError, message):
                BUILD.build_profile("recommended")

            snapshot.assert_not_called()
            self.assertEqual(b"unchanged", sentinel.read_bytes())

    def test_semantic_marker_wrong_owner_and_orphan_fail_before_mutation(self) -> None:
        relative = Path(
            "src/professional-skills/engineering-change-analysis/SKILL.md"
        )

        def wrong_owner(root: Path) -> None:
            path = root / relative
            source = path.read_text(encoding="utf-8")
            path.write_text(
                source.replace(
                    "rule=engineering-change-analysis/mode-boundary",
                    "rule=wrong-owner/mode-boundary",
                    1,
                ),
                encoding="utf-8",
            )

        def orphan(root: Path) -> None:
            path = root / relative
            path.write_text(
                path.read_text(encoding="utf-8").rstrip()
                + "\n<!-- rd-semantic-id:v2 "
                "finding=unconditional_mechanism_candidate "
                "rule=engineering-change-analysis/orphan occurrence=r4-orphan -->\n",
                encoding="utf-8",
            )

        self._assert_marker_preflight_failure_preserves_outputs(
            wrong_owner, "owner prefix"
        )
        self._assert_marker_preflight_failure_preserves_outputs(orphan, "orphan")

    def test_semantic_marker_rule_and_occurrence_collisions_fail_before_mutation(
        self,
    ) -> None:
        relative = Path(
            "src/professional-skills/engineering-change-analysis/SKILL.md"
        )

        def append_marker(root: Path, *, rule: str, occurrence: str) -> None:
            path = root / relative
            path.write_text(
                path.read_text(encoding="utf-8").rstrip()
                + "\n\n<!-- rd-semantic-id:v2 "
                "finding=unconditional_mechanism_candidate "
                f"rule={rule} occurrence={occurrence} -->\n"
                "- Retain the bounded source decision.\n",
                encoding="utf-8",
            )

        self._assert_marker_preflight_failure_preserves_outputs(
            lambda root: append_marker(
                root,
                rule="engineering-change-analysis/mode-boundary",
                occurrence="r4-second",
            ),
            "rule-id collision",
        )
        self._assert_marker_preflight_failure_preserves_outputs(
            lambda root: append_marker(
                root,
                rule="engineering-change-analysis/r4-second",
                occurrence="eca-mode-boundary",
            ),
            "duplicate.*occurrence",
        )

    def test_build_marker_preflight_does_not_consume_audit_or_reports(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            self._copy_source(root)
            observed: list[Path] = []
            original = Path.read_bytes

            def tracked(path: Path) -> bytes:
                observed.append(path)
                return original(path)

            with self._layout(root), mock.patch.object(
                Path, "read_bytes", tracked
            ), mock.patch.object(
                BUILD,
                "validate_semantic_identity_marker_inventory",
                wraps=VALIDATION.validate_semantic_identity_marker_inventory,
            ) as validator:
                registries = BUILD._load_registries()
                BUILD._preflight_registry_entries(registries)
                BUILD._preflight_semantic_marker_inventory(registries)

            self.assertTrue(observed)
            self.assertTrue(
                all(path.is_relative_to(root / "src") for path in observed)
            )
            expected: dict[str, tuple[str, str]] = {
                "src/control-prompts/main-control-agent.md": (
                    "main-control-agent",
                    "root",
                )
            }
            for entries in registries.values():
                for entry in entries:
                    skill_root = root / entry["path"]
                    expected[(skill_root / "SKILL.md").relative_to(root).as_posix()] = (
                        entry["name"],
                        "root",
                    )
                    references = skill_root / "references"
                    if references.is_dir():
                        for path in references.rglob("*.md"):
                            expected[path.relative_to(root).as_posix()] = (
                                entry["name"],
                                "reference",
                            )
            records = validator.call_args.args[0]
            actual = {
                record["path"]: (record["owner"], record["axis"])
                for record in records
            }
            self.assertEqual(expected, actual)
            self.assertNotIn("audit-skill-content", BUILD.__dict__)

    def test_review_ready_fails_closed_for_self_reported_native_handoff(self) -> None:
        handoff = self._current_handoff("reviewer-accessible-native-reference")
        self.assertFalse(VALIDATION.review_input_ready(handoff))
        handoff["exact_change_evidence"]["artifact"]["reference"] = (
            "native-change://codex/nonexistent-worktree"
        )
        self.assertFalse(VALIDATION.review_input_ready(handoff))

    def test_review_ready_requires_current_complete_supplied_handoff(self) -> None:
        handoff = self._current_handoff("exact-change-content")
        self.assertTrue(VALIDATION.review_input_ready(handoff))

    def test_review_ready_fails_closed_for_incomplete_or_mismatched_handoff(self) -> None:
        valid = self._current_handoff("exact-before-after")
        mutations = []
        for field in (
            "latest_changed_paths",
            "exact_change_evidence",
            "reviewer_artifact_accessibility",
            "validation_after_latest_material_edit",
            "fixed_review_scope",
        ):
            changed = copy.deepcopy(valid)
            changed.pop(field)
            mutations.append(changed)
        stale = copy.deepcopy(valid)
        stale["validation_after_latest_material_edit"]["generation"] = 6
        mutations.append(stale)
        wrong_scope = copy.deepcopy(valid)
        wrong_scope["fixed_review_scope"] = ["different.py"]
        mutations.append(wrong_scope)
        unreadable = copy.deepcopy(valid)
        unreadable["reviewer_artifact_accessibility"]["readable"] = False
        mutations.append(unreadable)
        for index, handoff in enumerate(mutations):
            with self.subTest(index=index):
                self.assertFalse(VALIDATION.review_input_ready(handoff))

    def test_review_readiness_is_independent_of_l5_confirmation_states(self) -> None:
        core = copy.deepcopy(BUILD.CORE_CONTRACTS)
        core["execution_level_contract"]["l5_confirmation"]["states"].remove(
            "not-required"
        )
        self.assertTrue(
            VALIDATION.review_input_ready(
                self._current_handoff("exact-change-content"),
                core=core,
            )
        )

    @staticmethod
    def _windows_translating_write_text(
        path: Path,
        data: str,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> int:
        """Emulate Windows text-mode newline translation on any host."""

        del newline
        with path.open(
            mode="w",
            encoding=encoding,
            errors=errors,
            newline="\r\n",
        ) as handle:
            return handle.write(data)

    def _copy_source(self, root: Path) -> None:
        shutil.copytree(ROOT / "src", root / "src")
        (root / "scripts").mkdir()
        for relative in AUTHORITATIVE_BUILD_INPUT_FILES:
            source = ROOT / relative
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

    @contextmanager
    def _layout(self, root: Path, *, dist: Path | None = None):
        src = root / "src"
        dist_root = dist or root / "dist"
        agent_skill_roots = (
            dist_root / "codex/project/.agents/skills",
            dist_root / "codex/user/.agents/skills",
            dist_root / "codex/admin/skills",
            dist_root / "claude/project/.claude/skills",
            dist_root / "claude/user/.claude/skills",
            dist_root / "copilot/project/.github/skills",
            dist_root / "copilot/user/.copilot/skills",
            dist_root / "cline/project/.cline/skills",
            dist_root / "cline/user/.cline/skills",
        )
        profile_outputs = (
            ("codex", dist_root / "codex/project/.codex/agents"),
            ("codex", dist_root / "codex/user/.codex/agents"),
            ("codex", dist_root / "codex/admin/agents"),
            ("claude", dist_root / "claude/project/.claude/agents"),
            ("claude", dist_root / "claude/user/.claude/agents"),
            ("copilot", dist_root / "copilot/project/.github/agents"),
            ("copilot", dist_root / "copilot/user/.copilot/agents"),
        )
        with mock.patch.multiple(
            BUILD,
            ROOT=root,
            SRC_DIR=src,
            REGISTRY_DIR=src / "registry",
            DIST_DIR=dist_root,
            UNIVERSAL_SKILLS_ROOT=dist_root / "universal/skills",
            OPENAI_ZIP_DIR=dist_root / "openai-api/zips",
            PROFILE_SOURCE=src / "agent-profiles/role-agents.json",
            HOST_ENFORCEMENT_SOURCE=src / "agent-profiles/host-enforcement.json",
            CONTROL_PROMPT_SOURCE=src / "control-prompts/main-control-agent.md",
            CORE_CONTRACTS_PATH=src / "control-model/core-contracts.json",
            LAYER_SOURCE_ROOTS={
                "control": src / "control-skills",
                "professional": src / "professional-skills",
                "foundation": src / "foundation/capabilities",
                "domain": src / "domain-extensions",
            },
            AGENT_SKILL_ROOTS=agent_skill_roots,
            AGENT_PROFILE_OUTPUTS=profile_outputs,
        ):
            yield dist_root

    def _assert_registry_failure_preserves_dist(
        self,
        old: str,
        new: str,
        registry: str = "control-skills.yaml",
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            self._copy_source(root)
            registry_path = root / "src/registry" / registry
            text = registry_path.read_text(encoding="utf-8")
            self.assertIn(old, text)
            registry_path.write_text(text.replace(old, new, 1), encoding="utf-8")
            dist = root / "dist"
            dist.mkdir()
            sentinel = dist / "sentinel.txt"
            sentinel.write_text("unchanged\n", encoding="utf-8")

            with self._layout(root):
                with self.assertRaises(BUILD.BuildError):
                    BUILD.build_profile("recommended")
            self.assertEqual("unchanged\n", sentinel.read_text(encoding="utf-8"))

    def test_compact_runtime_roots_omit_routing_and_keep_source_authority(self) -> None:
        professional_source = """---
name: sample-professional
description: synthetic
---

# sample-professional

## Role

Support `task-agent` at the bounded owner.

## When To Use

- authoring positive trigger

## Do Not Use

- authoring anti-trigger

## Required Inputs

- accepted task input

## Professional Decision Rules

- Preserve the accepted owner and decision.

## Stop / Escalation Conditions

- Stop when authority is unknown.

## Output Contract

- bounded result and proof limit

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [sample](references/sample.md) | targeted | a named decision is open | no named decision is open | task-agent | proof-limit |
"""
        foundation_source = """---
name: sample-foundation
description: synthetic
---

# sample-foundation

## Registry Trigger

**Use when**

- authoring positive trigger

**Do not use when**

- authoring anti-trigger

## Skill Role

Own one bounded decision.

## Inputs

- accepted task input

## High-Value Rules

- Preserve the accepted decision.
- Prove the negative path.
- Record the proof limit.

## Anti-Patterns

- Local success substituted for boundary evidence.

## Stop Conditions

- Stop when authority is unknown.

## Output Contract

- bounded result and proof limit

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [sample](references/sample.md) | targeted | a named decision is open | no named decision is open | task-agent | proof-limit |
"""

        def headings(text: str) -> list[str]:
            return [
                line.removeprefix("## ").strip()
                for line in text.splitlines()
                if line.startswith("## ")
            ]

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            professional = root / "sample-professional"
            professional.mkdir()
            professional_file = professional / "SKILL.md"
            professional_file.write_text(professional_source, encoding="utf-8")
            professional_item = BUILD.SkillItem(
                name="sample-professional",
                path=professional,
                layer="professional",
                description="synthetic",
                metadata={},
                body=professional_source,
                registry={"reference_index": []},
            )
            BUILD._write_compact_professional_projection(professional, professional_item)
            rendered_professional = professional_file.read_text(encoding="utf-8")
            self.assertEqual(
                [*BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS, "JIT Reference Delivery"],
                headings(rendered_professional),
            )
            for omitted in ("When To Use", "Do Not Use", "Required Inputs"):
                self.assertIn(f"## {omitted}", professional_source)
                self.assertNotIn(f"## {omitted}", rendered_professional)

            foundation = root / "sample-foundation"
            foundation.mkdir()
            foundation_file = foundation / "SKILL.md"
            foundation_file.write_text(foundation_source, encoding="utf-8")
            foundation_item = BUILD.SkillItem(
                name="sample-foundation",
                path=foundation,
                layer="foundation",
                description="synthetic",
                metadata={},
                body=foundation_source,
                registry={"reference_index": []},
            )
            BUILD._write_compact_layer3_root_projection(foundation, foundation_item)
            rendered_foundation = foundation_file.read_text(encoding="utf-8")
            self.assertEqual(
                list(BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS),
                headings(rendered_foundation),
            )
            for forbidden in (
                "## JIT Reference Delivery",
                "Current-Professional JIT",
                "engineering-control-plane/references/selectors/",
                "never select/reroute/preload",
                "index/catalog",
            ):
                self.assertNotIn(forbidden, rendered_foundation)
            for source_only in ("Registry Trigger", "Inputs", "Output Contract"):
                self.assertIn(f"## {source_only}", foundation_source)
                self.assertNotIn(f"## {source_only}", rendered_foundation)

            professional_file.write_text(
                professional_source.replace(
                    "## Output Contract\n\n- bounded result and proof limit\n\n",
                    "",
                    1,
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                BUILD.BuildError,
                "exactly one non-empty 'Output Contract'",
            ):
                BUILD._write_compact_professional_projection(professional, professional_item)

    def test_single_runtime_build_has_canonical_manifest_in_isolated_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            self._copy_source(root)

            with self._layout(root) as dist:
                result = BUILD.build_profile("recommended")
                manifest_path = (
                    dist
                    / "universal/skills/recommended"
                    / BUILD.BUILD_MANIFEST_NAME
                )
                manifest = BUILD.json.loads(
                    manifest_path.read_text(encoding="utf-8")
                )
                self.assertEqual("recommended", result["profile"])
                self.assertEqual(26, result["top_level_count"])
                self.assertEqual("recommended", manifest["profile"])
                self.assertEqual(
                    "changeforge.authoritative_build_inputs",
                    manifest["authoritative_build_inputs"]["kind"],
                )
                self.assertEqual(26, len(manifest["top_level_skills"]))
                self.assertEqual(1, len(manifest["control_skills"]))
                self.assertEqual(25, len(manifest["professional_skills"]))
                self.assertEqual(150, len(manifest["foundation_skills"]))
                self.assertEqual(13, len(manifest["domain_skills"]))
                self.assertEqual("targeted-product-references", manifest["foundation_mode"])
                self.assertEqual("targeted-references", manifest["domain_mode"])
                self.assertEqual(4, len(manifest["agent_profiles"]))

    def test_retired_profiles_are_rejected_before_managed_output_mutation(self) -> None:
        for retired in ("full", "dev"):
            with self.subTest(profile=retired), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / "repo"
                self._copy_source(root)
                sentinel = root / "dist/sentinel.bin"
                sentinel.parent.mkdir(parents=True)
                sentinel.write_bytes(b"unchanged")

                with self._layout(root), self.assertRaisesRegex(
                    BUILD.BuildError,
                    f"unsupported profile: {retired}",
                ):
                    BUILD.build_profile(retired)

                self.assertEqual(b"unchanged", sentinel.read_bytes())

    def test_build_cli_rejects_profile_selection_before_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            self._copy_source(root)
            sentinel = root / "dist/sentinel.bin"
            sentinel.parent.mkdir(parents=True)
            sentinel.write_bytes(b"unchanged")

            with self._layout(root), mock.patch.object(
                sys,
                "argv",
                ["build.py", "--profile", "full"],
            ), self.assertRaises(SystemExit):
                BUILD.main()

            self.assertEqual(b"unchanged", sentinel.read_bytes())

    def test_build_removes_only_preflighted_retired_profile_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            self._copy_source(root)

            with self._layout(root) as dist:
                managed_roots = (
                    dist / "universal/skills",
                    *BUILD.AGENT_SKILL_ROOTS,
                    dist / "openai-api/zips",
                )
                sentinels: list[Path] = []
                for managed_root in managed_roots:
                    for retired in ("full", "dev"):
                        residue = managed_root / retired / "managed.bin"
                        residue.parent.mkdir(parents=True, exist_ok=True)
                        residue.write_bytes(retired.encode("ascii"))
                    sentinel = managed_root / "user-sentinel.bin"
                    sentinel.write_bytes(b"preserve")
                    sentinels.append(sentinel)

                BUILD.build_profile("recommended")

                for managed_root in managed_roots:
                    self.assertFalse((managed_root / "full").exists())
                    self.assertFalse((managed_root / "dev").exists())
                for sentinel in sentinels:
                    self.assertEqual(b"preserve", sentinel.read_bytes())

    def test_invalid_retired_profile_root_fails_before_any_cleanup_or_reset(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            self._copy_source(root)

            with self._layout(root) as dist:
                first_residue = dist / "universal/skills/full/managed.bin"
                first_residue.parent.mkdir(parents=True)
                first_residue.write_bytes(b"preserve")
                invalid = BUILD.AGENT_SKILL_ROOTS[-1] / "dev"
                invalid.parent.mkdir(parents=True)
                invalid.write_bytes(b"not-a-directory")
                current = dist / "universal/skills/recommended/prior.bin"
                current.parent.mkdir(parents=True)
                current.write_bytes(b"current")

                with self.assertRaisesRegex(
                    BUILD.BuildError,
                    "retired profile output.*regular directory",
                ):
                    BUILD.build_profile("recommended")

                self.assertEqual(b"preserve", first_residue.read_bytes())
                self.assertEqual(b"not-a-directory", invalid.read_bytes())
                self.assertEqual(b"current", current.read_bytes())

    def test_build_removes_exact_pre_hookless_dist_and_zip_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            self._copy_source(root)

            with self._layout(root) as dist:
                hook_roots = (
                    dist / "codex/project/.codex",
                    dist / "codex/user/.codex",
                    dist / "claude/project/.claude",
                    dist / "claude/user/.claude",
                    dist / "copilot/project/.github",
                    dist / "copilot/user/.copilot",
                )
                legacy_directories = [
                    *(hook_root / "hooks" for hook_root in hook_roots),
                    dist / "universal/bootstrap",
                    dist / "copilot/project/.github/copilot/agents",
                    dist
                    / "universal/skills/recommended/.changeforge-packs",
                    dist
                    / "universal/skills/recommended/.changeforge-control",
                ]
                for directory in legacy_directories:
                    directory.mkdir(parents=True, exist_ok=True)
                    (directory / "legacy.bin").write_bytes(b"legacy")

                legacy_file_names = (
                    ".changeforge-hook-manifest.json",
                    "hooks.json",
                    "settings.changeforge-hooks.fragment.json",
                    "changeforge-route-preflight.md",
                    "changeforge-professional-contract.md",
                )
                legacy_files = []
                for hook_root in hook_roots:
                    hook_root.mkdir(parents=True, exist_ok=True)
                    for name in legacy_file_names:
                        path = hook_root / name
                        path.write_bytes(b"legacy")
                        legacy_files.append(path)

                legacy_root_zip = dist / "openai-api/zips/legacy-skill.zip"
                legacy_root_zip.parent.mkdir(parents=True, exist_ok=True)
                legacy_root_zip.write_bytes(b"legacy zip")

                sentinels = (
                    dist / "codex/project/.codex/user-owned.txt",
                    dist / "unrelated/hooks/user-owned.txt",
                    dist / "openai-api/zips/vendor/user-owned.zip",
                )
                for sentinel in sentinels:
                    sentinel.parent.mkdir(parents=True, exist_ok=True)
                    sentinel.write_bytes(b"preserve")

                BUILD.build_profile("recommended")

                self.assertTrue(all(not path.exists() for path in legacy_directories))
                self.assertTrue(all(not path.exists() for path in legacy_files))
                self.assertFalse(legacy_root_zip.exists())
                for sentinel in sentinels:
                    self.assertEqual(b"preserve", sentinel.read_bytes())
                runtime = dist / "universal/skills/recommended"
                self.assertEqual(
                    26,
                    len(
                        [
                            path
                            for path in runtime.iterdir()
                            if path.is_dir() and (path / "SKILL.md").is_file()
                        ]
                    ),
                )

    def test_legacy_cleanup_ambiguity_fails_before_any_mutation(self) -> None:
        scenarios = {
            "directory-is-file": Path("universal/bootstrap"),
            "file-is-directory": Path("codex/project/.codex/hooks.json"),
            "root-zip-is-directory": Path("openai-api/zips/legacy.zip"),
        }
        for scenario, relative in scenarios.items():
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / "repo"
                self._copy_source(root)

                with self._layout(root) as dist:
                    invalid = dist / relative
                    invalid.parent.mkdir(parents=True, exist_ok=True)
                    if scenario == "directory-is-file":
                        invalid.write_bytes(b"ambiguous")
                    else:
                        invalid.mkdir()
                    earlier = dist / "codex/project/.codex/hooks/legacy.bin"
                    earlier.parent.mkdir(parents=True, exist_ok=True)
                    earlier.write_bytes(b"preserve")
                    current = dist / "universal/skills/recommended/prior.bin"
                    current.parent.mkdir(parents=True, exist_ok=True)
                    current.write_bytes(b"current")

                    with self.assertRaises(BUILD.BuildError):
                        BUILD.build_profile("recommended")

                    self.assertEqual(b"preserve", earlier.read_bytes())
                    self.assertEqual(b"current", current.read_bytes())

    def test_legacy_cleanup_symlink_fails_before_any_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            self._copy_source(root)

            with self._layout(root) as dist:
                outside = root / "outside"
                outside.mkdir()
                legacy = dist / "codex/project/.codex/hooks"
                legacy.parent.mkdir(parents=True)
                legacy.symlink_to(outside, target_is_directory=True)
                current = dist / "universal/skills/recommended/prior.bin"
                current.parent.mkdir(parents=True)
                current.write_bytes(b"current")

                with self.assertRaises(BUILD.BuildError):
                    BUILD.build_profile("recommended")

                self.assertTrue(legacy.is_symlink())
                self.assertEqual(b"current", current.read_bytes())

    def test_agent_profiles_remain_lf_canonical_with_windows_text_translation(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            self._copy_source(root)

            with (
                self._layout(root) as dist,
                mock.patch.object(
                    Path,
                    "write_text",
                    self._windows_translating_write_text,
                ),
            ):
                profiles = BUILD._load_agent_profiles()
                enforcement = BUILD._load_host_enforcement()
                by_name = {profile["name"]: profile for profile in profiles}
                renderers = {
                    "codex": BUILD._render_codex_profile,
                    "claude": BUILD._render_claude_profile,
                    "copilot": BUILD._render_copilot_profile,
                }
                suffixes = {
                    "codex": ".toml",
                    "claude": ".md",
                    "copilot": ".agent.md",
                }
                expected_digests = BUILD._agent_profile_digests(
                    profiles,
                    enforcement,
                )
                manifest_roots = (
                    dist / "universal/skills",
                    *BUILD.AGENT_SKILL_ROOTS,
                )
                BUILD.build_profile("recommended")
                observed_files = 0
                for platform, profile_root in BUILD.AGENT_PROFILE_OUTPUTS:
                    for role, profile in by_name.items():
                        raw = (
                            profile_root
                            / f"{role}{suffixes[platform]}"
                        ).read_bytes()
                        expected = renderers[platform](
                            profile,
                            enforcement,
                        ).encode("utf-8")
                        self.assertEqual(expected, raw)
                        self.assertNotIn(b"\r", raw)
                        self.assertEqual(
                            expected_digests[platform][role],
                            hashlib.sha256(raw).hexdigest(),
                        )
                        observed_files += 1
                self.assertEqual(28, observed_files)

                for skills_root in manifest_roots:
                    manifest = BUILD.json.loads(
                        (
                            skills_root
                            / "recommended"
                            / BUILD.BUILD_MANIFEST_NAME
                        ).read_bytes()
                    )
                    self.assertEqual(
                        expected_digests,
                        manifest["agent_profile_sha256"],
                    )

    def test_agent_profile_cr_fails_preflight_before_managed_output_mutation(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            self._copy_source(root)
            dist = root / "dist"
            sentinel = (
                dist / "universal/skills/recommended/prior-output.txt"
            )
            sentinel.parent.mkdir(parents=True)
            prior_output = b"prior-output\n"
            sentinel.write_bytes(prior_output)
            original_renderer = BUILD._render_codex_profile

            def render_with_cr(
                profile: dict[str, object],
                enforcement: dict[str, object],
            ) -> str:
                return original_renderer(profile, enforcement).replace("\n", "\r\n")

            with (
                self._layout(root),
                mock.patch.object(
                    BUILD,
                    "_render_codex_profile",
                    side_effect=render_with_cr,
                ),
                self.assertRaisesRegex(
                    BUILD.BuildError,
                    "rendered Profile must use canonical LF bytes",
                ),
            ):
                BUILD.build_profile("recommended")

            self.assertTrue(sentinel.is_file())
            self.assertEqual(prior_output, sentinel.read_bytes())

    def test_malicious_skill_name_and_noncanonical_path_fail_before_reset(self) -> None:
        self._assert_registry_failure_preserves_dist(
            "name: engineering-control-plane",
            "name: ../escape",
        )
        self._assert_registry_failure_preserves_dist(
            "path: src/control-skills/engineering-control-plane",
            "path: src/control-skills/../control-skills/engineering-control-plane",
        )

    def test_foundation_schema_scope_and_ownership_fail_before_reset(self) -> None:
        self._assert_registry_failure_preserves_dist(
            "schema_version: 8",
            "schema_version: 5",
            "foundation-skills.yaml",
        )
        self._assert_registry_failure_preserves_dist(
            "delivery_scope: product",
            "delivery_scope: normal",
            "foundation-skills.yaml",
        )
        self._assert_registry_failure_preserves_dist(
            "content_class: compact",
            "content_class: broad",
            "foundation-skills.yaml",
        )
        self._assert_registry_failure_preserves_dist(
            "content_class: complex",
            "content_class: compact",
            "foundation-skills.yaml",
        )
        self._assert_registry_failure_preserves_dist(
            'used_by: ["change-intake-compiler"]',
            'used_by: ["change-intake-compiler", "engineering-change-analysis"]',
            "foundation-skills.yaml",
        )

    def test_non_product_foundation_candidate_fails_before_reset(self) -> None:
        self._assert_registry_failure_preserves_dist(
            'layer3_candidates: ["task-dag-decomposition", "release-rollback"]',
            'layer3_candidates: ["task-dag-decomposition", "release-rollback", "skill-authoring-expert"]',
            "professional-skills.yaml",
        )

    def test_multi_role_output_contract_is_required_before_build(self) -> None:
        entry = {
            "role_support": ["analysis-agent", "task-agent"],
            "required_inputs_by_role": {
                "analysis-agent": ["accepted brief"],
                "task-agent": ["accepted capsule"],
            },
        }
        with self.assertRaisesRegex(BUILD.BuildError, "output_contract_by_role"):
            BUILD._validate_role_contract_maps(entry, "professional[0]")

    def test_source_tree_symlink_fails_before_reset(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            self._copy_source(root)
            outside = root / "outside.md"
            outside.write_text("outside\n", encoding="utf-8")
            link = root / "src/control-skills/engineering-control-plane/references/escape.md"
            link.symlink_to(outside)
            dist = root / "dist"
            dist.mkdir()
            sentinel = dist / "sentinel.txt"
            sentinel.write_text("unchanged\n", encoding="utf-8")

            with self._layout(root):
                with self.assertRaises(BUILD.BuildError):
                    BUILD.build_profile("recommended")
            self.assertEqual("unchanged\n", sentinel.read_text(encoding="utf-8"))

    def test_managed_dist_ancestor_symlink_fails_before_reset(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            self._copy_source(root)
            dist = root / "dist"
            dist.mkdir()
            sentinel = dist / "sentinel.txt"
            sentinel.write_text("unchanged\n", encoding="utf-8")
            outside = root / "outside"
            outside.mkdir()
            (outside / "sentinel.txt").write_text("outside\n", encoding="utf-8")
            (dist / "universal").symlink_to(outside, target_is_directory=True)

            with self._layout(root):
                with self.assertRaises(BUILD.BuildError):
                    BUILD.build_profile("recommended")
            self.assertEqual("unchanged\n", sentinel.read_text(encoding="utf-8"))
            self.assertEqual("outside\n", (outside / "sentinel.txt").read_text(encoding="utf-8"))

    def test_source_output_overlap_fails_before_reset(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            self._copy_source(root)
            overlapping = root / "src/professional-skills"
            sentinel = overlapping / "sentinel.txt"
            sentinel.write_text("unchanged\n", encoding="utf-8")

            with self._layout(root, dist=overlapping):
                with self.assertRaises(BUILD.BuildError):
                    BUILD.build_profile("recommended")
            self.assertEqual("unchanged\n", sentinel.read_text(encoding="utf-8"))

    def test_cross_layer_duplicate_name_fails_before_reset(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            self._copy_source(root)
            duplicate = "transaction-consistency"
            shutil.copytree(
                root / "src/foundation/capabilities" / duplicate,
                root / "src/domain-extensions" / duplicate,
            )
            registry = root / "src/registry/domain-skills.yaml"
            text = registry.read_text(encoding="utf-8")
            text = text.replace("name: ai-product-extension", f"name: {duplicate}", 1)
            text = text.replace(
                "path: src/domain-extensions/ai-product-extension",
                f"path: src/domain-extensions/{duplicate}",
                1,
            )
            registry.write_text(text, encoding="utf-8")
            dist = root / "dist"
            dist.mkdir()
            sentinel = dist / "sentinel.txt"
            sentinel.write_text("unchanged\n", encoding="utf-8")

            with self._layout(root):
                with self.assertRaises(BUILD.BuildError):
                    BUILD.build_profile("recommended")
            self.assertEqual("unchanged\n", sentinel.read_text(encoding="utf-8"))

    def test_main_profile_embeds_prompt_once_and_preserves_fallback(self) -> None:
        profiles = {
            profile["name"]: profile for profile in BUILD._load_agent_profiles()
        }
        main = profiles["main-control-agent"]
        for platform, renderer in (
            ("codex", BUILD._render_codex_profile),
            ("claude", BUILD._render_claude_profile),
            ("copilot", BUILD._render_copilot_profile),
        ):
            rendered = renderer(main)
            self.assertEqual(1, rendered.count("# Main Control Agent"))
            BUILD._validate_rendered_prompt_embedding(
                platform,
                "main-control-agent",
                rendered,
            )
            self.assertIn(
                "Never reload references/main-control-agent.md.",
                rendered,
            )
            worker = renderer(profiles["analysis-agent"])
            BUILD._validate_rendered_prompt_embedding(
                platform,
                "analysis-agent",
                worker,
            )
            self.assertNotIn("# Main Control Agent", worker)
        control = " ".join(
            (
                ROOT
                / "src/control-skills/engineering-control-plane/SKILL.md"
            ).read_text(encoding="utf-8").split()
        )
        self.assertIn("host without an Agent Profile", control)
        self.assertIn("references/main-control-agent.md", control)

    def test_all_source_rendered_main_contexts_meet_core_hard_ceiling(self) -> None:
        profiles = {
            profile["name"]: profile for profile in BUILD._load_agent_profiles()
        }
        enforcement = BUILD._load_host_enforcement()
        item = next(
            entry
            for entry in BUILD._load_items(
                "control", BUILD._load_registries()["control"]
            )
            if entry.name == "engineering-control-plane"
        )
        with tempfile.TemporaryDirectory() as raw:
            destination = Path(raw) / item.name
            shutil.copytree(item.path, destination)
            BUILD._write_compact_control_projection(destination, item)
            control_text = (destination / "SKILL.md").read_text(encoding="utf-8")

        gate = derived_context_budget_limits(CONTEXT_BUDGET_MODEL)["main"][
            "hard_ceiling"
        ]
        observed: dict[str, int] = {}
        for host, renderer in (
            ("codex", BUILD._render_codex_profile),
            ("claude", BUILD._render_claude_profile),
            ("copilot", BUILD._render_copilot_profile),
        ):
            rendered = renderer(profiles["main-control-agent"], enforcement)
            key = f"{host}:recommended"
            observed[key] = count_o200k_base_tokens(
                rendered.rstrip() + "\n\n" + control_text.rstrip()
            )

        self.assertEqual(3, len(observed))
        self.assertLessEqual(max(observed.values()), gate, observed)

    def test_build_preflight_rejects_stale_prompt_before_dist_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            self._copy_source(root)
            prompt = root / "src/control-prompts/main-control-agent.md"
            original = prompt.read_text(encoding="utf-8")
            mutated = original.replace(
                "Trust exact build/install validation.",
                "Trust stale build/install validation.",
                1,
            )
            self.assertNotEqual(original, mutated)
            prompt.write_text(mutated, encoding="utf-8")
            dist = root / "dist"
            dist.mkdir()
            sentinel = dist / "sentinel.txt"
            sentinel.write_text("unchanged\n", encoding="utf-8")

            with self._layout(root), self.assertRaisesRegex(
                BUILD.BuildError,
                "authoritative control prompt projection is stale",
            ):
                BUILD.build_profile("recommended")

            self.assertEqual("unchanged\n", sentinel.read_text(encoding="utf-8"))

    def test_build_preflight_rejects_post_build_unreachable_template(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            self._copy_source(root)
            registry_path = root / "src/registry/control-skills.yaml"
            registry = registry_path.read_text(encoding="utf-8")
            start = registry.index(
                '      - path: "references/direct-task-template.md"'
            )
            end = registry.index("      - path:", start + 1)
            registry_path.write_text(
                registry[:start] + registry[end:],
                encoding="utf-8",
            )
            dist = root / "dist"
            dist.mkdir()
            sentinel = dist / "sentinel.txt"
            sentinel.write_text("unchanged\n", encoding="utf-8")

            with self._layout(root), self.assertRaisesRegex(
                BUILD.BuildError,
                "unreachable after build",
            ):
                BUILD.build_profile("recommended")

            self.assertEqual("unchanged\n", sentinel.read_text(encoding="utf-8"))

    def test_compact_control_projection_preserves_registry_v2_rows(self) -> None:
        item = next(
            entry
            for entry in BUILD._load_items(
                "control", BUILD._load_registries()["control"]
            )
            if entry.name == "engineering-control-plane"
        )
        contracts = BUILD._item_reference_contracts(
            item.registry,
            item.name,
            item.name,
        )
        with tempfile.TemporaryDirectory() as raw:
            destination = Path(raw) / item.name
            shutil.copytree(item.path, destination)
            BUILD._write_compact_control_projection(destination, item)
            text = (destination / "SKILL.md").read_text(encoding="utf-8")
            BUILD._write_compact_control_projection(destination, item)
            repeated = (destination / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("Reference Contract v2; Prompt owns rules.", text)
        self.assertEqual(text, repeated)
        self.assertLessEqual(count_o200k_base_tokens(text), 400)
        for contract in contracts:
            with self.subTest(path=contract["path"]):
                row = next(
                    line
                    for line in text.splitlines()
                    if f"]({contract['path']})" in line
                )
                self.assertEqual(
                    [
                        f"[{Path(contract['path']).stem.removesuffix('-template').split('-')[-1]}]({contract['path']})",
                        contract["type"],
                        contract["load_when"],
                        contract["do_not_load_when"],
                        ", ".join(contract["required_by"]),
                        ", ".join(contract["required_output"]),
                    ],
                    row.strip("|").split("|"),
                )

    def test_host_enforcement_drives_safe_review_projection(self) -> None:
        matrix = BUILD._load_host_enforcement()
        profiles = {
            profile["name"]: profile for profile in BUILD._load_agent_profiles()
        }
        self.assertEqual(
            "prompt-enforced",
            matrix["hosts"]["codex"]["roles"]["main-control-agent"]["tool_allowlist"],
        )
        self.assertEqual(5, matrix["schema_version"])
        self.assertNotIn("mode_values", matrix)
        for host in matrix["hosts"].values():
            self.assertNotIn("native_diff_safeguards", host)
            self.assertNotIn("diff_input_mode", host)
            self.assertNotIn("validation_mode", host)
        renderer_hosts = {
            BUILD._render_codex_profile: "codex",
            BUILD._render_claude_profile: "claude",
            BUILD._render_copilot_profile: "copilot",
        }
        for renderer, host in renderer_hosts.items():
            rendered = renderer(profiles["main-control-agent"], matrix)
            self.assertNotIn("Current capability facts:", rendered)
            self.assertNotIn("Current external-read mode:", rendered)
        claude = BUILD._render_claude_profile(profiles["review-agent"], matrix)
        copilot = BUILD._render_copilot_profile(profiles["review-agent"], matrix)
        self.assertNotIn("Current capability facts:", claude)
        self.assertNotIn("Current capability facts:", copilot)
        self.assertIn("tools: Skill, Read, Grep, Glob", claude)
        self.assertNotIn("Bash", claude.split("---", 2)[1])
        self.assertIn('tools: ["read","search"]', copilot)
        self.assertNotIn('"execute"', copilot.split("---", 2)[1])

    def test_main_profile_has_no_runtime_capability_projection(self) -> None:
        matrix = BUILD._load_host_enforcement()
        profiles = {
            profile["name"]: profile for profile in BUILD._load_agent_profiles()
        }
        for host in ("codex", "claude", "copilot"):
            with self.subTest(host=host):
                rendered = {
                    "codex": BUILD._render_codex_profile,
                    "claude": BUILD._render_claude_profile,
                    "copilot": BUILD._render_copilot_profile,
                }[host](profiles["main-control-agent"], matrix)
                self.assertNotIn("Current capability facts:", rendered)
                self.assertNotIn("CAPABILITY_MISMATCH", rendered)

    def test_copilot_analysis_projects_only_bounded_web_read_tools(self) -> None:
        matrix = BUILD._load_host_enforcement()
        profiles = {
            profile["name"]: profile for profile in BUILD._load_agent_profiles()
        }
        analysis = matrix["hosts"]["copilot"]["roles"]["analysis-agent"]

        self.assertEqual(["read", "search", "web"], analysis["rendered_tools"])
        self.assertEqual("prompt-enforced", analysis["external_source_read"])
        rendered = BUILD._render_copilot_profile(
            profiles["analysis-agent"],
            matrix,
        )
        frontmatter = rendered.split("---", 2)[1]
        compact_tools_line = 'tools: ["read","search","web"]'
        self.assertIn(compact_tools_line, frontmatter)
        self.assertEqual(9, count_o200k_base_tokens(compact_tools_line))
        expected_tools_lines = {
            "main-control-agent": 'tools: ["agent"]',
            "analysis-agent": compact_tools_line,
            "task-agent": 'tools: ["read","search","edit","execute"]',
            "review-agent": 'tools: ["read","search"]',
        }
        for role, expected_line in expected_tools_lines.items():
            with self.subTest(role=role):
                role_frontmatter = BUILD._render_copilot_profile(
                    profiles[role], matrix
                ).split("---", 2)[1]
                tools_line = next(
                    line
                    for line in role_frontmatter.splitlines()
                    if line.startswith("tools: ")
                )
                self.assertEqual(expected_line, tools_line)
        for forbidden in ("edit", "execute", "agent", "*", "mcp"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(f'"{forbidden}"', frontmatter)

        for role in ("main-control-agent", "task-agent", "review-agent"):
            with self.subTest(role=role):
                self.assertNotIn(
                    "web",
                    matrix["hosts"]["copilot"]["roles"][role]["rendered_tools"],
                )

    def test_host_enforcement_rejects_stale_schema_and_invalid_enforcement(self) -> None:
        mutations = (
            ('"schema_version": 5', '"schema_version": 4', "schema_version 5"),
            (
                '"profile_delivery": "native-enforced"',
                '"profile_delivery": "stale-mode"',
                "invalid profile_delivery enforcement",
            ),
            (
                '"tool_allowlist": "prompt-enforced"',
                '"tool_allowlist": "stale-mode"',
                "invalid tool_allowlist enforcement status",
            ),
            (
                '"rendered_tools": ["read", "search", "web"]',
                '"rendered_tools": ["read", "search", "web", "execute"]',
                "copilot-vscode: analysis tools do not match the surface ceiling",
            ),
        )
        for old, new, error in mutations:
            with self.subTest(error=error), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / "repo"
                self._copy_source(root)
                matrix_path = root / "src/agent-profiles/host-enforcement.json"
                text = matrix_path.read_text(encoding="utf-8")
                self.assertIn(old, text)
                matrix_path.write_text(text.replace(old, new, 1), encoding="utf-8")
                with self._layout(root), self.assertRaisesRegex(BUILD.BuildError, error):
                    BUILD._load_host_enforcement()

    def test_layer3_entrypoint_describes_only_the_current_build(self) -> None:
        expected = (
            (
                False,
                "No Foundation or Domain Layer 3 items are assigned to this Skill.",
            ),
            (
                True,
                "Foundation and Domain items are compiled at `references/layer3/<name>.md`.",
            ),
        )
        with tempfile.TemporaryDirectory() as temporary:
            skill_root = Path(temporary) / "professional"
            skill_root.mkdir()
            for compiled, expected_body in expected:
                with self.subTest(compiled=compiled):
                    (skill_root / "SKILL.md").write_text("# Professional\n", encoding="utf-8")
                    layer3_root = skill_root / "references/layer3"
                    if layer3_root.exists():
                        shutil.rmtree(layer3_root)
                    if compiled:
                        layer3_root.mkdir(parents=True)
                        (layer3_root / "index.md").write_text(
                            "# Layer 3 Reference Index\n",
                            encoding="utf-8",
                        )
                    BUILD._append_layer3_entrypoint(skill_root)
                    text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
                    self.assertEqual(1, text.count("## Layer 3 Delivery"))
                    self.assertEqual(
                        expected_body,
                        text.split("## Layer 3 Delivery\n\n", 1)[1].strip(),
                    )
                    self.assertNotIn(BUILD.GENERATED_MARKER, text)
                    self.assertNotIn("Never preload Layer 3", text)
                    self.assertNotIn("index or catalog", text)
                    self.assertNotIn("## Compiled Layer 3 References", text)

    def test_foundation_layer3_projection_keeps_exact_runtime_sections(self) -> None:
        body = """# sample-foundation

## Registry Trigger

Use this only for authoring-route selection and ignore [omitted](references/omitted.md).

## Skill Role

Own the first coupled boundary sentence. Preserve the second sentence too.

Preserve this second paragraph because the complete role defines the decision boundary.

## Inputs

- authoring-only input

## High-Value Rules

- Keep one decision-bearing rule.

## Anti-Patterns

- Do not collapse distinct states.

## Execution Checklist

1. Authoring-only workflow.

## Stop Conditions

- Stop when the invariant owner is unknown.

## Output Contract

- Authoring-only output.

## Targeted References

- stale authoring prose
"""
        item = BUILD.SkillItem(
            name="sample-foundation",
            path=ROOT / "src/foundation/capabilities/sample-foundation",
            layer="foundation",
            description="synthetic",
            metadata={},
            body=body,
            registry={
                "activation": {
                    "contract": "foundation-activation/v1",
                    "id": "foundation-activation-sample-foundation",
                    "mode": "explicit-analyzed",
                    "path": "analyzed",
                    "profile": "analysis-agent",
                    "primary_skill": "sample-primary",
                    "review_skill": "sample-review",
                    "semantic_atoms": [
                        "activation-registry-non-render-sentinel"
                    ],
                    "matcher_evidence": ["source-bound"],
                    "negative_families": [
                        "lexical-near-miss",
                        "explicit-anti-or-adjacent",
                        "alternate-professional-owner",
                        "analysis-authority-invalid",
                    ],
                    "runtime_matcher": {
                        "contract": "foundation-semantic-matcher/v1",
                        "rollout": "enabled",
                        "action": "analysis-only",
                        "combine": "all",
                        "predicates": [
                            {
                                "atom": (
                                    "activation-registry-non-render-sentinel"
                                ),
                                "operator": "all-term-groups",
                                "scope": "bounded-clause",
                                "polarity": "present",
                                "action": "none",
                                "term_groups": [
                                    ["runtime matcher metadata sentinel"],
                                ],
                            }
                        ],
                    },
                },
                "reference_index": [
                    {
                        "path": "references/checklist.md",
                        "type": "decision-checklist",
                        "load_when": "boundary evidence remains unresolved",
                        "do_not_load_when": "the root proves the bounded decision",
                        "required_by": ["task-agent"],
                        "required_output": ["checklist-result"],
                    }
                ]
            },
        )

        rendered = BUILD._render_layer3_reference(item)
        h1, sections = BUILD._markdown_heading_sections(rendered)
        self.assertEqual(["sample-foundation"], h1)
        self.assertEqual(
            [
                "Decision Boundary",
                "High-Value Rules",
                "Anti-Patterns",
                "Stop Conditions",
            ],
            list(sections),
        )
        self.assertEqual(
            "Own the first coupled boundary sentence. Preserve the second sentence too.\n\n"
            "Preserve this second paragraph because the complete role defines the decision boundary.",
            sections["Decision Boundary"][0],
        )
        for heading in BUILD.LAYER3_PROJECTION_FORBIDDEN_HEADINGS:
            self.assertNotIn(f"## {heading}", rendered)
        self.assertNotIn("stale authoring prose", rendered)
        self.assertNotIn("references/omitted.md", rendered)
        self.assertNotIn("foundation-activation/v1", rendered)
        self.assertNotIn(
            "foundation-activation-sample-foundation",
            rendered,
        )
        self.assertNotIn(
            "activation-registry-non-render-sentinel",
            rendered,
        )
        self.assertNotIn("foundation-semantic-matcher/v1", rendered)
        self.assertNotIn("runtime matcher metadata sentinel", rendered)
        self.assertNotIn("## Targeted References", rendered)
        for forbidden in (
            "## JIT Reference Delivery",
            "Current-Professional JIT",
            "engineering-control-plane/references/selectors/",
            "never select/reroute/preload",
            "index/catalog",
        ):
            self.assertNotIn(forbidden, rendered)

    def test_occurrence_activation_metadata_is_not_rendered(self) -> None:
        body = """# sample-occurrence-activation

## Skill Role

Own the occurrence-render-body-sentinel boundary.

## High-Value Rules

- Preserve the public projection.

## Anti-Patterns

- Do not render authoring-only registry metadata.

## Stop Conditions

- Stop when metadata changes rendered bytes.

## Targeted References

- stale authoring prose
"""
        reference_index = [
            {
                "path": "references/occurrence-checklist.md",
                "type": "decision-checklist",
                "load_when": "occurrence-reference-load-sentinel",
                "do_not_load_when": "occurrence-reference-skip-sentinel",
                "required_by": ["task-agent"],
                "required_output": ["checklist-result"],
            }
        ]
        item_without = BUILD.SkillItem(
            name="sample-occurrence-activation",
            path=(
                ROOT
                / "src/foundation/capabilities/sample-occurrence-activation"
            ),
            layer="foundation",
            description="synthetic",
            metadata={},
            body=body,
            registry={"reference_index": reference_index},
        )
        activation = {
            "contract": "foundation-activation/v1",
            "id": "foundation-activation-sample-occurrence-activation",
            "mode": "explicit-analyzed",
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "domain-impact-modeler",
            "review_skill": "architecture-impact-reviewer",
            "semantic_atoms": ["business-rule-occurrence"],
            "matcher_evidence": [
                "analysis-action",
                "governed-business-object",
                "owner-qualified-domain-language",
            ],
            "negative_families": [
                "lexical-near-miss",
                "explicit-anti-or-adjacent",
                "alternate-professional-owner",
                "analysis-authority-invalid",
            ],
            "runtime_matcher": {
                "contract": "foundation-occurrence-matcher/v1",
                "rollout": "enabled",
                "action": "analysis-only",
                "combine": "any",
                "relations": [
                    {
                        "atom": "business-rule-occurrence",
                        "operator": "governed-object-occurrence",
                        "scope": "bounded-clause",
                        "actions": ["analyze", "analyse", "extract"],
                        "objects": [
                            "business invariant",
                            "business invariants",
                            "domain invariant",
                            "domain invariants",
                            "business policy",
                            "business policies",
                            "domain policy",
                            "domain policies",
                            "business calculation",
                            "business calculations",
                            "domain calculation",
                            "domain calculations",
                            "business constraint",
                            "business constraints",
                            "domain constraint",
                            "domain constraints",
                            "business rule",
                            "business rules",
                            "domain rule",
                            "domain rules",
                            "business decision authority",
                            "domain decision authority",
                        ],
                        "owner_relation": {
                            "mode": "intrinsic-qualified-object",
                            "qualifiers": ["business", "domain"],
                        },
                        "non_owner_modifiers": [
                            "accepted",
                            "current",
                            "existing",
                            "material",
                        ],
                    }
                ],
            },
        }
        self.assertEqual(
            [],
            _foundation_activation_field_errors(
                {
                    "name": item_without.name,
                    "activation": activation,
                },
                "synthetic occurrence activation",
            ),
        )
        item_with = replace(
            item_without,
            registry={
                "activation": activation,
                "reference_index": reference_index,
            },
        )

        rendered_without = BUILD._render_layer3_reference(item_without)
        rendered_with = BUILD._render_layer3_reference(item_with)

        self.assertEqual(
            rendered_without.encode("utf-8"),
            rendered_with.encode("utf-8"),
        )
        for forbidden in (
            "foundation-activation/v1",
            "foundation-occurrence-matcher/v1",
            "business-rule-occurrence",
            "governed-object-occurrence",
            "objects",
            "business decision authority",
            "qualifiers",
            "business",
            "non_owner_modifiers",
            "material",
        ):
            self.assertNotIn(forbidden, rendered_with)
        self.assertIn("occurrence-render-body-sentinel", rendered_with)
        self.assertNotIn("## Targeted References", rendered_with)
        self.assertNotIn("## JIT Reference Delivery", rendered_with)
        self.assertNotIn("Current-Professional JIT", rendered_with)

    def test_domain_layer3_projection_uses_domain_decision_sections(self) -> None:
        body = """# sample-domain

## Role

Own the complete domain boundary. Keep this second sentence.

## When To Use

- authoring trigger

## Do Not Use

- authoring anti-trigger

## Required Inputs

- authoring input

## Professional Decision Rules

- Apply the domain invariant.

## High-Value Gotchas

- A domain-specific failure.

## Execution Checklist

1. Authoring workflow.

## Stop / Escalation Conditions

- Stop when domain authority is unknown.

## Output Contract

- Authoring output.

## Targeted References

- stale
"""
        item = BUILD.SkillItem(
            name="sample-domain",
            path=ROOT / "src/domain-extensions/sample-domain",
            layer="domain",
            description="synthetic",
            metadata={},
            body=body,
            registry={"reference_index": []},
        )

        rendered = BUILD._render_layer3_reference(item)
        _h1, sections = BUILD._markdown_heading_sections(rendered)
        self.assertEqual(
            [
                "Decision Boundary",
                "Professional Decision Rules",
                "High-Value Gotchas",
                "Stop / Escalation Conditions",
            ],
            list(sections),
        )
        self.assertEqual(
            "Own the complete domain boundary. Keep this second sentence.",
            sections["Decision Boundary"][0],
        )
        self.assertNotIn("No task-local Reference is indexed", rendered)
        for heading in BUILD.LAYER3_PROJECTION_FORBIDDEN_HEADINGS:
            self.assertNotIn(f"## {heading}", rendered)

    def test_four_foundation_replacement_rules_are_exact_and_decision_bearing(self) -> None:
        expected = {
            "data-migration-design": (
                "Block destructive cleanup until readers retire and reconciliation, "
                "recovery, and ownership are proven.",
            ),
            "release-rollback": (
                "Choose rollback only while old code reads current durable, provider, "
                "and retained state.",
            ),
            "version-compatibility": (
                "Select a bridge from each failing producer-consumer or data direction "
                "using current evidence.",
            ),
            "permission-boundary-modeling": (
                "Enforce permissions before collection outputs.",
                "Define explicit behavior for mixed tenant bulk actions.",
            ),
        }
        generic = (
            "Load the named benchmark, checklist, or evidence Reference according to "
            "the open output."
        )
        source_occurrences = 0
        registries = BUILD._load_registries()
        foundation_items = {
            item.name: item
            for item in BUILD._load_items("foundation", registries["foundation"])
        }
        for skill_name, required_rules in expected.items():
            with self.subTest(skill=skill_name):
                path = foundation_items[skill_name].path / "SKILL.md"
                source = path.read_text(encoding="utf-8")
                source_occurrences += source.count(generic)
                _h1, sections = BUILD._markdown_heading_sections(source)
                rules = [
                    line.removeprefix("- ")
                    for line in sections["High-Value Rules"][0].splitlines()
                    if line.startswith("- ")
                ]
                self.assertEqual(list(required_rules), rules[-len(required_rules):])
                self.assertEqual([], VALIDATION.foundation_content_class_errors(
                    foundation_items[skill_name].registry,
                    f"foundation_skills.{skill_name}",
                ))
        self.assertEqual(0, source_occurrences)

    def test_layer3_projection_fails_closed_on_missing_or_duplicate_sections(self) -> None:
        body = """# sample-foundation

## Skill Role

First role.

## Skill Role

Second role.

## High-Value Rules

- Rule.

## Anti-Patterns

- Failure.

## Stop Conditions

- Stop.

## Targeted References

- None.
"""
        item = BUILD.SkillItem(
            name="sample-foundation",
            path=ROOT / "src/foundation/capabilities/sample-foundation",
            layer="foundation",
            description="synthetic",
            metadata={},
            body=body,
            registry={"reference_index": []},
        )
        with self.assertRaisesRegex(BUILD.BuildError, "exactly one non-empty 'Skill Role'"):
            BUILD._render_layer3_reference(item)

    def test_rendered_professional_body_over_budget_fails_before_reset(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            self._copy_source(root)
            skill_file = (
                root
                / "src/professional-skills/engineering-change-analysis/SKILL.md"
            )
            registry = BUILD.load_yaml_file(
                root / "src/registry/professional-skills.yaml"
            )
            entry = next(
                item
                for item in registry["professional_skills"]
                if item["name"] == "engineering-change-analysis"
            )
            rendered_source = BUILD._render_targeted_reference_section(
                skill_file.read_text(encoding="utf-8"),
                BUILD._item_reference_contracts(
                    entry, "engineering-change-analysis", "engineering-change-analysis"
                ),
                "engineering-change-analysis",
            )
            skill_file.write_text(rendered_source, encoding="utf-8")
            _metadata, raw_frontmatter, body = BUILD.parse_frontmatter(skill_file)
            body_lines = body.splitlines()
            kernel_index = body_lines.index("## Professional Decision Rules") + 1
            padding = [
                f"Rendered-budget fixture line {index}"
                for index in range(121)
            ]
            body_lines[kernel_index:kernel_index] = padding
            skill_file.write_text(
                "---\n"
                + raw_frontmatter
                + "\n---\n"
                + "\n".join(body_lines)
                + "\n",
                encoding="utf-8",
            )

            dist = root / "dist"
            dist.mkdir()
            sentinel = dist / "sentinel.txt"
            sentinel.write_text("unchanged\n", encoding="utf-8")

            with self._layout(root), self.assertRaisesRegex(
                BUILD.BuildError,
                r"rendered Professional SKILL\.md body has \d+ lines; maximum is 120",
            ):
                BUILD.build_profile("recommended")
            self.assertEqual("unchanged\n", sentinel.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
