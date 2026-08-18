from __future__ import annotations

import hashlib
import importlib.util
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

from validation_utils import (  # noqa: E402
    AUTHORITATIVE_BUILD_INPUT_FILES,
    CONTEXT_BUDGET_MODEL,
    _foundation_activation_field_errors,
    count_o200k_base_tokens,
    derived_context_budget_limits,
)


class BuildSafetyTests(unittest.TestCase):
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

    def test_all_profiles_build_with_canonical_manifest_in_isolated_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            self._copy_source(root)
            expected_counts = {"recommended": 27, "full": 40, "dev": 190}

            with self._layout(root) as dist:
                for profile in BUILD.PROFILES:
                    with self.subTest(profile=profile):
                        result = BUILD.build_profile(profile)
                        manifest_path = (
                            dist
                            / "universal/skills"
                            / profile
                            / BUILD.BUILD_MANIFEST_NAME
                        )
                        manifest = BUILD.json.loads(
                            manifest_path.read_text(encoding="utf-8")
                        )
                        self.assertEqual(profile, result["profile"])
                        self.assertEqual(expected_counts[profile], result["top_level_count"])
                        self.assertEqual(profile, manifest["profile"])
                        self.assertEqual(
                            "changeforge.authoritative_build_inputs",
                            manifest["authoritative_build_inputs"]["kind"],
                        )
                        self.assertEqual(
                            expected_counts[profile], len(manifest["top_level_skills"])
                        )
                        self.assertEqual(4, len(manifest["agent_profiles"]))

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
                for build_profile in BUILD.PROFILES:
                    with self.subTest(build_profile=build_profile):
                        BUILD.build_profile(build_profile)
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
                                    / build_profile
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
            "layer3_candidates: []",
            'layer3_candidates: ["skill-authoring-expert"]',
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
                    BUILD.build_profile("dev")
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

    def test_all_source_rendered_main_contexts_meet_evolution_target(self) -> None:
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
            "evolution_target"
        ]
        observed: dict[str, int] = {}
        for host, renderer in (
            ("codex", BUILD._render_codex_profile),
            ("claude", BUILD._render_claude_profile),
            ("copilot", BUILD._render_copilot_profile),
        ):
            rendered = renderer(profiles["main-control-agent"], enforcement)
            for build_profile in BUILD.PROFILES:
                key = f"{host}:{build_profile}"
                observed[key] = count_o200k_base_tokens(
                    rendered.rstrip() + "\n\n" + control_text.rstrip()
                )

        self.assertEqual(9, len(observed))
        self.assertLessEqual(max(observed.values()), gate, observed)

    def test_build_preflight_rejects_stale_prompt_before_dist_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            self._copy_source(root)
            prompt = root / "src/control-prompts/main-control-agent.md"
            original = prompt.read_text(encoding="utf-8")
            mutated = original.replace(
                "State: current, superseded, invalid",
                "State: stale, superseded, invalid",
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

        self.assertIn("Reference Contract v2; Prompt owns rules.", text)
        encoded = text.encode("utf-8")
        self.assertEqual(
            "f67957d0f282d0ee3b91eb0fce7045c205cbaccfa558e84c33d51dacd4406c3d",
            hashlib.sha256(encoded).hexdigest(),
        )
        self.assertEqual(1546, len(encoded))
        self.assertEqual(18, sum(bool(line.strip()) for line in text.splitlines()))
        self.assertEqual(342, count_o200k_base_tokens(text))
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
        self.assertEqual(4, matrix["schema_version"])
        self.assertEqual(
            {
                "diff_input_mode": ["native", "supplied-artifact", "unsupported"],
                "validation_mode": ["native-read-only", "task-no-edit", "unsupported"],
            },
            matrix["mode_values"],
        )
        self.assertEqual(
            ["--no-pager", "--no-ext-diff", "--no-textconv"],
            matrix["hosts"]["codex"]["native_diff_safeguards"],
        )
        for host in ("claude", "copilot", "cline", "openai-api"):
            self.assertEqual([], matrix["hosts"][host]["native_diff_safeguards"])
        self.assertEqual(
            {capability: "supported" for capability in BUILD.DECISION_CAPABILITY_FIELDS},
            BUILD._normalized_decision_capabilities(matrix["hosts"]["codex"]),
        )
        unknown_adapter = dict(matrix["hosts"]["codex"])
        unknown_adapter.update(
            {
                "profile_delivery": "unknown-native-id",
                "diff_input_mode": "unknown-native-id",
                "validation_mode": "unknown-native-id",
                "utility_no_edit": "unknown-native-id",
            }
        )
        self.assertEqual(
            {capability: "unsupported" for capability in BUILD.DECISION_CAPABILITY_FIELDS},
            BUILD._normalized_decision_capabilities(unknown_adapter),
        )
        renderer_hosts = {
            BUILD._render_codex_profile: "codex",
            BUILD._render_claude_profile: "claude",
            BUILD._render_copilot_profile: "copilot",
        }
        for renderer, host in renderer_hosts.items():
            host_contract = matrix["hosts"][host]
            capability_facts = BUILD._normalized_decision_capabilities(host_contract)
            rendered = renderer(profiles["main-control-agent"], matrix)
            self.assertIn(
                BUILD._render_decision_capability_facts(capability_facts),
                rendered,
            )
            self.assertEqual(1, rendered.count("Current capability facts:"))
        claude = BUILD._render_claude_profile(profiles["review-agent"], matrix)
        copilot = BUILD._render_copilot_profile(profiles["review-agent"], matrix)
        self.assertNotIn("Current capability facts:", claude)
        self.assertNotIn("Current capability facts:", copilot)
        self.assertIn("tools: Skill, Read, Grep, Glob", claude)
        self.assertNotIn("Bash", claude.split("---", 2)[1])
        self.assertIn('tools: ["read", "search"]', copilot)
        self.assertNotIn('"execute"', copilot.split("---", 2)[1])

    def test_host_enforcement_rejects_stale_schema_and_unknown_modes(self) -> None:
        mutations = (
            ('"schema_version": 4', '"schema_version": 3', "schema_version 4"),
            (
                '"diff_input_mode": "supplied-artifact"',
                '"diff_input_mode": "stale-mode"',
                "invalid diff_input_mode",
            ),
            (
                '"native_diff_safeguards": ["--no-pager", "--no-ext-diff", "--no-textconv"]',
                '"native_diff_safeguards": ["--no-pager", "--no-ext-diff"]',
                "native diff safeguards",
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
        expected = {
            "recommended": "compiles assigned Foundation and Domain guidance",
            "full": "delivers Domain guidance as",
            "dev": "delivers assigned Foundation and Domain guidance as top-level",
        }
        with tempfile.TemporaryDirectory() as temporary:
            skill_root = Path(temporary) / "professional"
            skill_root.mkdir()
            for profile, phrase in expected.items():
                with self.subTest(profile=profile):
                    (skill_root / "SKILL.md").write_text("# Professional\n", encoding="utf-8")
                    BUILD._append_layer3_entrypoint(skill_root, profile)
                    text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
                    self.assertEqual(1, text.count("## Layer 3 Delivery"))
                    self.assertIn(phrase, text)
                    self.assertIn("Never preload Layer 3", text)
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
                "Targeted References",
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
        self.assertIn(
            "| [checklist](sample-foundation/references/checklist.md) | "
            "decision-checklist | boundary evidence remains unresolved | "
            "the root proves the bounded decision | task-agent | checklist-result |",
            rendered,
        )

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
        self.assertIn(
            "| [occurrence]"
            "(sample-occurrence-activation/references/occurrence-checklist.md) | "
            "decision-checklist | occurrence-reference-load-sentinel | "
            "occurrence-reference-skip-sentinel | task-agent | "
            "checklist-result |",
            rendered_with,
        )

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
                "Targeted References",
            ],
            list(sections),
        )
        self.assertEqual(
            "Own the complete domain boundary. Keep this second sentence.",
            sections["Decision Boundary"][0],
        )
        self.assertIn("No task-local Reference is indexed", rendered)
        for heading in BUILD.LAYER3_PROJECTION_FORBIDDEN_HEADINGS:
            self.assertNotIn(f"## {heading}", rendered)

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
        for profile in BUILD.PROFILES:
            with self.subTest(profile=profile), tempfile.TemporaryDirectory() as temporary:
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
                self.assertLessEqual(len(body_lines), 115)
                targeted_index = body_lines.index("## Targeted References")
                padding = [
                    f"Rendered-budget fixture line {index}"
                    for index in range(115 - len(body_lines))
                ]
                body_lines[targeted_index:targeted_index] = padding
                self.assertEqual(115, len(body_lines))
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
                    BUILD.build_profile(profile)
                self.assertEqual("unchanged\n", sentinel.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
