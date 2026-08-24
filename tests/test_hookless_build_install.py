from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from validation_utils import (  # noqa: E402
    authoritative_build_input_snapshot_errors,
    count_o200k_base_tokens,
)


def load_script(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


BUILD = load_script("hookless_build_install_build", "scripts/build.py")


def assert_build_profile_artifact_semantics(
    test_case: unittest.TestCase,
    root: Path,
    profile: str,
    expected_skill_count: int,
) -> dict:
    test_case.assertTrue(root.is_dir(), f"build profile root is missing: {profile}")
    skills = [
        path
        for path in root.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    ]
    test_case.assertEqual(expected_skill_count, len(skills), profile)
    manifest_path = root / ".changeforge-build-manifest.json"
    test_case.assertTrue(
        manifest_path.is_file(), f"build manifest is missing: {profile}"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    test_case.assertIsInstance(manifest, dict, profile)
    build_input_errors = authoritative_build_input_snapshot_errors(
        manifest.get("authoritative_build_inputs"),
        ROOT,
    )
    test_case.assertEqual(
        [],
        build_input_errors,
        f"{profile}: {'; '.join(build_input_errors)}",
    )
    test_case.assertEqual("hookless-control-plane-v1", manifest["architecture"])
    test_case.assertEqual(
        "ai-consumption-v1", manifest["compiled_layer3_format"]
    )
    test_case.assertEqual(
        Counter(manifest["foundation_delivery_scopes"].values()),
        {"product": 141, "authoring-only": 1, "dev-only": 8},
    )
    expected_compiled_foundation = 0 if profile == "dev" else 141
    test_case.assertEqual(
        expected_compiled_foundation,
        len(manifest["compiled_foundation_skills"]),
    )
    return manifest


class BuildArtifactConsumerContractTests(unittest.TestCase):
    def test_profile_artifact_consumer_rejects_real_manifest_file_and_count_mutations(
        self,
    ) -> None:
        consumer = globals().get("assert_build_profile_artifact_semantics")
        self.assertTrue(callable(consumer), "build artifact consumer is missing")
        source_manifest = json.loads(
            (
                ROOT
                / "dist/universal/skills/recommended/.changeforge-build-manifest.json"
            ).read_text(encoding="utf-8")
        )

        def fixture(directory: Path) -> Path:
            root = directory / "recommended"
            root.mkdir()
            for index in range(27):
                skill = root / f"skill-{index:02d}"
                skill.mkdir()
                (skill / "SKILL.md").write_text("# fixture\n", encoding="utf-8")
            (root / ".changeforge-build-manifest.json").write_text(
                json.dumps(source_manifest), encoding="utf-8"
            )
            return root

        with tempfile.TemporaryDirectory() as raw:
            root = fixture(Path(raw))
            manifest_path = root / ".changeforge-build-manifest.json"
            self.assertEqual(
                "hookless-control-plane-v1",
                consumer(self, root, "recommended", 27)["architecture"],
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["architecture"] = "mutated"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(AssertionError):
                consumer(self, root, "recommended", 27)

        with tempfile.TemporaryDirectory() as raw:
            root = fixture(Path(raw))
            manifest_path = root / ".changeforge-build-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["authoritative_build_inputs"]["sha256"] = "0" * 64
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(
                AssertionError, "authoritative build inputs are stale"
            ):
                consumer(self, root, "recommended", 27)

        with tempfile.TemporaryDirectory() as raw:
            root = fixture(Path(raw))
            (root / ".changeforge-build-manifest.json").unlink()
            with self.assertRaisesRegex(AssertionError, "build manifest is missing"):
                consumer(self, root, "recommended", 27)

        with tempfile.TemporaryDirectory() as raw:
            root = fixture(Path(raw))
            (root / "skill-00/SKILL.md").unlink()
            with self.assertRaises(AssertionError):
                consumer(self, root, "recommended", 27)


class HooklessBuildInstallTests(unittest.TestCase):
    def test_profile_counts_and_standard_skill_roots(self) -> None:
        expected = {"recommended": 27, "full": 40, "dev": 190}
        for profile, count in expected.items():
            root = ROOT / "dist/universal/skills" / profile
            manifest = assert_build_profile_artifact_semantics(
                self, root, profile, count
            )
            self.assertEqual(
                "prompt-enforced",
                manifest["agent_profile_enforcement"]["codex"]["roles"]
                ["main-control-agent"]["tool_allowlist"],
            )
            self.assertEqual(
                "src/agent-profiles/host-enforcement.json",
                manifest["agent_profile_enforcement_source"]["path"],
            )
            self.assertEqual(
                    4,
                    manifest["agent_profile_enforcement_source"]["schema_version"],
            )
            self.assertEqual(
                {
                    "path": "src/control-model/core-contracts.json",
                    "schema_version": 1,
                    "kind": "changeforge.core_contracts",
                    "sha256": hashlib.sha256(
                        (ROOT / "src/control-model/core-contracts.json").read_bytes()
                    ).hexdigest(),
                },
                manifest["core_model"],
            )
            enforcement_source = json.loads(
                (ROOT / "src/agent-profiles/host-enforcement.json").read_text()
            )
            self.assertEqual(
                enforcement_source["hosts"],
                manifest["agent_profile_enforcement"],
            )
            for host, expected in enforcement_source["hosts"].items():
                enforcement = manifest["agent_profile_enforcement"][host]
                self.assertEqual(expected, enforcement)
                self.assertNotIn("diff_inspection", enforcement)
                self.assertNotIn("validation_execution", enforcement)
            for obsolete in ("runtime_engine", "hidden_role_packs", "executable_interception"):
                self.assertNotIn(obsolete, manifest)

    def test_recommended_exposes_control_and_all_professional_skills(self) -> None:
        root = ROOT / "dist/universal/skills/recommended"
        names = {path.name for path in root.iterdir() if (path / "SKILL.md").is_file()}
        self.assertIn("engineering-control-plane", names)
        self.assertEqual(26, len(names - {"engineering-control-plane"}))
        self.assertTrue((root / "backend-change-builder/references/layer3/transaction-consistency.md").is_file())

    def test_execution_level_runtime_reference_reaches_profiles_fallback_and_zip_exactly(self) -> None:
        source = (
            ROOT
            / "src/control-skills/engineering-control-plane/references/execution-level-contract.md"
        ).read_bytes()
        skill_roots = (
            ROOT / "dist/universal/skills/recommended",
            ROOT / "dist/codex/project/.agents/skills/recommended",
            ROOT / "dist/claude/project/.claude/skills/recommended",
            ROOT / "dist/copilot/project/.github/skills/recommended",
        )
        for root in skill_roots:
            with self.subTest(root=root):
                control = root / "engineering-control-plane/references"
                self.assertEqual(source, (control / "execution-level-contract.md").read_bytes())
                self.assertIn(
                    "references/execution-level-contract.md",
                    (control / "main-control-agent.md").read_text(encoding="utf-8"),
                )
        profile_paths = (
            ROOT / "dist/codex/project/.codex/agents/main-control-agent.toml",
            ROOT / "dist/claude/project/.claude/agents/main-control-agent.md",
            ROOT / "dist/copilot/project/.github/agents/main-control-agent.agent.md",
        )
        for profile in profile_paths:
            self.assertIn(
                "references/execution-level-contract.md",
                profile.read_text(encoding="utf-8"),
            )
        for profile in ("recommended", "full", "dev"):
            with self.subTest(openai_archive_profile=profile):
                zip_path = (
                    ROOT
                    / f"dist/openai-api/zips/{profile}/engineering-control-plane.zip"
                )
                with zipfile.ZipFile(zip_path) as archive:
                    self.assertEqual(
                        source,
                        archive.read(
                            "engineering-control-plane/references/execution-level-contract.md"
                        ),
                    )
                    fallback = archive.read(
                        "engineering-control-plane/references/main-control-agent.md"
                    ).decode("utf-8")
                    self.assertIn("references/execution-level-contract.md", fallback)

    def test_build_copy_gate_rejects_runtime_reference_drift(self) -> None:
        build = load_script("runtime_reference_build_gate", "scripts/build.py")
        with tempfile.TemporaryDirectory() as raw:
            destination = Path(raw) / "engineering-control-plane"
            shutil.copytree(
                ROOT / "src/control-skills/engineering-control-plane",
                destination,
            )
            runtime = destination / "references/execution-level-contract.md"
            runtime.write_text(
                runtime.read_text(encoding="utf-8").replace(
                    '"default_level":"L3"',
                    '"default_level":"L2"',
                    1,
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                build.BuildError,
                "not an exact source copy",
            ):
                build._copy_control_prompt(destination)

    def test_compiled_layer3_is_selectively_reachable_from_professional_root(self) -> None:
        for profile in ("recommended", "full", "dev"):
            root = ROOT / "dist/universal/skills" / profile
            manifest = json.loads((root / ".changeforge-build-manifest.json").read_text())
            for skill_name, candidates in manifest["compiled_layer3_references"].items():
                skill_root = root / skill_name
                skill_text = (skill_root / "SKILL.md").read_text()
                self.assertEqual(1, skill_text.count("## Layer 3 Delivery"))
                self.assertNotIn("## Compiled Layer 3 References", skill_text)
                if profile == "recommended":
                    expected_delivery = (
                        "Foundation and Domain items are compiled at "
                        "`references/layer3/<name>.md`."
                        if candidates
                        else "No Foundation or Domain Layer 3 items are assigned to this Skill."
                    )
                elif profile == "full":
                    expected_delivery = (
                        "Foundation items are compiled at `references/layer3/<name>.md`; "
                        "Domain items are top-level Skills."
                        if candidates
                        else "Domain items are top-level Skills; no Foundation items are compiled for this Skill."
                    )
                else:
                    expected_delivery = (
                        "Foundation and Domain items are top-level Skills; "
                        "no Layer 3 references are compiled."
                    )
                self.assertEqual(
                    expected_delivery,
                    skill_text.split("## Layer 3 Delivery\n\n", 1)[1].strip(),
                )
                self.assertNotIn("Never preload Layer 3", skill_text)
                self.assertNotIn("Layer 3 index or catalog", skill_text)
                if not candidates:
                    self.assertFalse((skill_root / "references/layer3").exists())
                    self.assertNotIn("(references/layer3/index.md)", skill_text)
                    continue
                self.assertNotIn("(references/layer3/index.md)", skill_text)
                index_text = (skill_root / "references/layer3/index.md").read_text()
                for candidate in candidates:
                    self.assertIn(f"- [{candidate}]({candidate}.md)", index_text)
                    self.assertTrue((skill_root / f"references/layer3/{candidate}.md").is_file())
                self.assertNotIn("- Trigger:", index_text)
                self.assertNotIn("- Do not load:", index_text)
                self.assertLessEqual(len(index_text.encode("utf-8")), 4096)
                self.assertIn("`references/layer3/<name>.md`", skill_text)

        recommended_manifest = json.loads(
            (ROOT / "dist/universal/skills/recommended/.changeforge-build-manifest.json").read_text()
        )
        full_manifest = json.loads(
            (ROOT / "dist/universal/skills/full/.changeforge-build-manifest.json").read_text()
        )
        self.assertFalse(
            set(recommended_manifest["top_level_skills"])
            & set(recommended_manifest["foundation_skills"] + recommended_manifest["domain_skills"])
        )
        self.assertFalse(
            set(full_manifest["top_level_skills"])
            & set(full_manifest["foundation_skills"])
        )
        domain = set(full_manifest["domain_skills"])
        self.assertTrue(domain <= set(full_manifest["top_level_skills"]))
        self.assertFalse(
            domain
            & {
                candidate
                for candidates in full_manifest["compiled_layer3_references"].values()
                for candidate in candidates
            }
        )
        self.assertIn(
            "payment-trading-extension",
            {
                candidate
                for candidates in recommended_manifest["compiled_layer3_references"].values()
                for candidate in candidates
            },
        )
        non_product = {
            name
            for name, scope in recommended_manifest[
                "foundation_delivery_scopes"
            ].items()
            if scope != "product"
        }
        self.assertEqual(9, len(non_product))
        for manifest in (recommended_manifest, full_manifest):
            compiled = {
                candidate
                for candidates in manifest["compiled_layer3_references"].values()
                for candidate in candidates
            }
            self.assertFalse(non_product & compiled)
        dev_manifest = json.loads(
            (ROOT / "dist/universal/skills/dev/.changeforge-build-manifest.json").read_text()
        )
        self.assertTrue(
            set(dev_manifest["foundation_skills"] + dev_manifest["domain_skills"])
            <= set(dev_manifest["top_level_skills"])
        )
        self.assertTrue(
            all(not candidates for candidates in dev_manifest["compiled_layer3_references"].values())
        )

    def test_compiled_projection_and_top_level_authoring_boundaries(self) -> None:
        expected_foundation = [
            "Decision Boundary",
            "High-Value Rules",
            "Anti-Patterns",
            "Stop Conditions",
            "JIT Reference Delivery",
        ]
        expected_domain = [
            "Decision Boundary",
            "Professional Decision Rules",
            "High-Value Gotchas",
            "Stop / Escalation Conditions",
            "JIT Reference Delivery",
        ]
        forbidden = {
            "Registry Trigger",
            "Inputs",
            "Required Inputs",
            "Output Contract",
            "Execution Checklist",
            "When To Use",
            "Do Not Use",
        }

        compiled_paths = {
            "recommended-foundation": (
                ROOT
                / "dist/universal/skills/recommended/backend-change-builder"
                / "references/layer3/transaction-consistency.md",
                expected_foundation,
            ),
            "full-foundation": (
                ROOT
                / "dist/universal/skills/full/backend-change-builder"
                / "references/layer3/transaction-consistency.md",
                expected_foundation,
            ),
            "recommended-domain": (
                ROOT
                / "dist/universal/skills/recommended/data-middleware-change-builder"
                / "references/layer3/bigdata-product-extension.md",
                expected_domain,
            ),
        }
        for label, (path, expected) in compiled_paths.items():
            with self.subTest(label=label):
                text = path.read_text(encoding="utf-8")
                headings = [
                    line.removeprefix("## ").strip()
                    for line in text.splitlines()
                    if line.startswith("## ")
                ]
                self.assertEqual(expected, headings)
                self.assertFalse(forbidden & set(headings))

        nested = compiled_paths["recommended-foundation"][0]
        self.assertTrue(
            (
                nested.parent
                / "transaction-consistency/references/evidence-patterns.md"
            ).is_file()
        )
        selector = json.loads(
            (
                ROOT
                / "dist/universal/skills/recommended/engineering-control-plane"
                / "references/selectors/backend-change-builder.json"
            ).read_text(encoding="utf-8")
        )
        partition = json.loads(
            (
                ROOT
                / "dist/universal/skills/recommended/engineering-control-plane"
                / "references/reference-records/backend-change-builder"
                / "transaction-consistency.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            "changeforge.layer3-selector-normalized-control/v1",
            selector["contract"],
        )
        self.assertNotIn("reference_records", selector)
        self.assertTrue(
            any(
                record.get("owner_skill") == "transaction-consistency"
                and record.get("path") == "references/evidence-patterns.md"
                and record.get("required_output")
                for record in partition["reference_records"]
            )
        )

        full_domain = (
            ROOT / "dist/universal/skills/full/bigdata-product-extension/SKILL.md"
        ).read_text(encoding="utf-8")
        dev_foundation_without_inputs = (
            ROOT
            / "dist/universal/skills/dev/transaction-consistency/SKILL.md"
        ).read_text(encoding="utf-8")
        dev_foundation_with_inputs = (
            ROOT
            / "dist/universal/skills/dev/targeted-validation-selection/SKILL.md"
        ).read_text(encoding="utf-8")
        dev_domain = (
            ROOT
            / "dist/universal/skills/dev/bigdata-product-extension/SKILL.md"
        ).read_text(encoding="utf-8")
        expected_domain_headings = [
            "Role",
            "Professional Decision Rules",
            "Stop / Escalation Conditions",
            "Output Contract",
            "JIT Reference Delivery",
        ]
        expected_foundation_without_inputs = [
            "Skill Role",
            "High-Value Rules",
            "Anti-Patterns",
            "Stop Conditions",
            "JIT Reference Delivery",
        ]
        expected_foundation_with_inputs = expected_foundation_without_inputs

        def h2_headings(text: str) -> list[str]:
            return [
                line.removeprefix("## ").strip()
                for line in text.splitlines()
                if line.startswith("## ")
            ]

        for text in (full_domain, dev_domain):
            self.assertEqual(expected_domain_headings, h2_headings(text))
            self.assertNotIn("## Targeted References", text)
        self.assertEqual(
            expected_foundation_without_inputs,
            h2_headings(dev_foundation_without_inputs),
        )
        self.assertEqual(
            expected_foundation_with_inputs,
            h2_headings(dev_foundation_with_inputs),
        )
        for text in (dev_foundation_without_inputs, dev_foundation_with_inputs):
            self.assertNotIn("## Targeted References", text)

        source_domain = (
            ROOT / "src/domain-extensions/bigdata-product-extension/SKILL.md"
        ).read_text(encoding="utf-8")
        for heading in ("When To Use", "Do Not Use", "Required Inputs"):
            self.assertIn(f"## {heading}", source_domain)
            self.assertNotIn(f"## {heading}", full_domain)
            self.assertNotIn(f"## {heading}", dev_domain)
        source_foundation_without_inputs = (
            ROOT / "src/foundation/capabilities/transaction-consistency/SKILL.md"
        ).read_text(encoding="utf-8")
        source_foundation_with_inputs = (
            ROOT
            / "src/foundation/capabilities/targeted-validation-selection/SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("## Registry Trigger", source_foundation_without_inputs)
        self.assertNotIn("## Registry Trigger", dev_foundation_without_inputs)
        self.assertNotIn("## Inputs", source_foundation_without_inputs)
        self.assertNotIn("## Inputs", dev_foundation_without_inputs)
        self.assertIn("## Inputs", source_foundation_with_inputs)
        self.assertNotIn("## Inputs", dev_foundation_with_inputs)
        for source, built in (
            (source_foundation_without_inputs, dev_foundation_without_inputs),
            (source_foundation_with_inputs, dev_foundation_with_inputs),
        ):
            self.assertIn("## Output Contract", source)
            self.assertNotIn("## Output Contract", built)

        def without_section(text: str, heading: str) -> str:
            marker = f"\n## {heading}\n"
            self.assertIn(marker, text)
            prefix, remainder = text.split(marker, 1)
            next_heading = remainder.find("\n## ")
            if next_heading < 0:
                return prefix.rstrip() + "\n"
            return prefix + remainder[next_heading:]

        with tempfile.TemporaryDirectory() as raw:
            fixture_root = Path(raw) / "transaction-consistency"
            fixture_root.mkdir()
            fixture_file = fixture_root / "SKILL.md"
            item = BUILD.SkillItem(
                name="transaction-consistency",
                path=fixture_root,
                layer="foundation",
                description="synthetic",
                metadata={},
                body=source_foundation_without_inputs,
                registry={"reference_index": []},
            )
            for required_heading in (
                "Skill Role",
                "High-Value Rules",
                "Anti-Patterns",
                "Stop Conditions",
                "Output Contract",
                "Targeted References",
            ):
                fixture_file.write_text(
                    without_section(
                        source_foundation_without_inputs,
                        required_heading,
                    ),
                    encoding="utf-8",
                )
                expected_error = (
                    "complete source Targeted References authority"
                    if required_heading == "Targeted References"
                    else f"one non-empty {required_heading!r} section"
                )
                with self.subTest(required_heading=required_heading):
                    with self.assertRaisesRegex(BUILD.BuildError, expected_error):
                        BUILD._write_compact_layer3_root_projection(
                            fixture_root,
                            item,
                        )

    def test_source_profiles_use_compact_role_and_generated_delivery_rules(self) -> None:
        data = json.loads((ROOT / "src/agent-profiles/role-agents.json").read_text())
        core = json.loads((ROOT / "src/control-model/core-contracts.json").read_text())
        roles = core["roles"]
        profile_contract = core["profile_contract"]
        limits = core["profile_contract"]["instruction_rule_count"]
        profiles = {item["name"]: item for item in data["profiles"]}
        self.assertEqual(set(roles), set(profiles))

        capability_groups = dict(profile_contract["capability_terms"])
        for contract_name in (
            "implementation_discipline_contract",
            "review_discipline_contract",
        ):
            contract = core[contract_name]
            capability_groups[contract["profile_capability_id"]] = contract[
                "profile_projection"
            ]

        def matching_rules(rules: list[str], rule: dict[str, object]) -> list[str]:
            required_terms = rule.get(
                "required_terms",
                rule.get("projection_terms"),
            )
            self.assertIsInstance(required_terms, list)
            return [
                bullet
                for bullet in rules
                if all(
                    term.casefold() in bullet.casefold()
                    for term in required_terms
                )
            ]

        forbidden_storage = {
            rule["id"]: rule
            for rule in core["visible_evidence_contract"]["forbidden_storage"]
        }
        built_profile_roots = {
            "codex": (ROOT / "dist/codex/project/.codex/agents", ".toml"),
            "claude": (ROOT / "dist/claude/project/.claude/agents", ".md"),
            "copilot": (
                ROOT / "dist/copilot/project/.github/agents",
                ".agent.md",
            ),
        }
        for name, profile in profiles.items():
            role = roles[name]
            expected_fields = set(profile_contract["profile_fields"]) | set(
                profile_contract["optional_fields_by_role"][name]
            )
            self.assertEqual(expected_fields, set(profile))
            self.assertEqual(role["sandbox"], profile["sandbox"])
            self.assertEqual(role["tools"], profile["tools"])
            tools = set(profile["tools"])
            self.assertEqual("dispatch" in tools, role["may_dispatch"])
            self.assertEqual({"edit", "execute"} <= tools, role["may_edit"])
            self.assertEqual("execute-read-only" in tools, role["may_review"])

            rules = profile["instructions"].splitlines()
            maximum = limits["maximum_by_role"].get(name, limits["maximum"])
            self.assertGreaterEqual(len(rules), limits["minimum"])
            self.assertLessEqual(len(rules), maximum)
            self.assertTrue(all(rule.startswith("- ") for rule in rules))
            for forbidden in profile_contract["forbidden_instruction_terms"]:
                self.assertNotIn(forbidden, profile["instructions"])

            role_capability = profile_contract["role_capabilities"][name]
            if name in {"task-agent", "review-agent"}:
                role_terms = {
                    "task-agent": (
                        ("Task Capsule", "Professional Skill", "Layer 3 Delivery"),
                        ("bound effective Level", "never calculate or recompute"),
                        ("final edit", "fresh validation", "exact change capture"),
                        ("latest changed paths", "exact change evidence", "fixed review scope"),
                        ("daemon", "database", "runtime task state engine", "hidden protocol record"),
                    ),
                    "review-agent": (
                        ("assigned Review Skill", "Layer 3 Delivery"),
                        ("bound effective Level", "review depth", "never calculate or recompute"),
                        ("delivered current", "every changed file", "missing evidence block"),
                        ("fresh validation", "latest actual diff", "fresh re-review"),
                        ("assigned Review Handoff", "reviewed/unreviewed scope", "residual risk"),
                    ),
                }[name]
                for terms in role_terms:
                    self.assertEqual(
                        1,
                        sum(all(term in rule for term in terms) for rule in rules),
                        terms,
                    )
                limit = 440 if name == "task-agent" else 568
                self.assertLessEqual(count_o200k_base_tokens(profile["instructions"]), limit)
            else:
                for capability_id in role_capability["required_capability_ids"]:
                    for rule in capability_groups[capability_id]:
                        matches = matching_rules(rules, rule)
                        self.assertEqual(1, len(matches), rule["rule_id"])
                        if "exact_rule" in rule:
                            self.assertEqual(rule["exact_rule"], matches[0], rule["rule_id"])

                handoff_id = role_capability["handoff_contract"]
                for rule in profile_contract["handoff_contracts"][handoff_id]:
                    matches = matching_rules(rules, rule)
                    self.assertEqual(1, len(matches), rule["rule_id"])
                    if "exact_rule" in rule:
                        self.assertEqual(rule["exact_rule"], matches[0], rule["rule_id"])

                for rule_id in role_capability["forbidden_storage_projection_ids"]:
                    matches = matching_rules(rules, forbidden_storage[rule_id])
                    self.assertEqual(1, len(matches), rule_id)

            for host, (root, suffix) in built_profile_roots.items():
                built_lines = (
                    (root / f"{name}{suffix}")
                    .read_text(encoding="utf-8")
                    .splitlines()
                )
                for rule in rules:
                    self.assertIn(rule, built_lines, (host, name, rule))

        self.assertEqual(
            core["prompt_contract"]["path"],
            profiles["main-control-agent"]["prompt"],
        )
        external = core["external_read_contract"]
        self.assertEqual("analysis-agent", external["exclusive_role"])
        self.assertEqual("external-source-read", external["operation"])
        for name, profile in profiles.items():
            self.assertEqual(
                name == external["exclusive_role"],
                external["operation"] in profile["tools"],
            )
        for name in ("task-agent", "review-agent"):
            self.assertNotIn(external["operation"], profiles[name]["tools"])

    def test_no_built_runtime_or_hidden_delivery(self) -> None:
        forbidden_names = {".changeforge-packs", ".changeforge-control", "hooks", "runtime_governance"}
        residue = [path for path in (ROOT / "dist").rglob("*") if path.name in forbidden_names]
        self.assertFalse(residue)
        self.assertFalse(list((ROOT / "dist").rglob("changeforge_*.py")))
        self.assertFalse(list((ROOT / "dist").rglob("hooks.json")))

    def test_platform_profiles_are_generated_for_supported_hosts(self) -> None:
        roots = {
            "codex": ROOT / "dist/codex/project/.codex/agents",
            "claude": ROOT / "dist/claude/project/.claude/agents",
            "copilot": ROOT / "dist/copilot/project/.github/agents",
        }
        expected_suffixes = {
            "codex": ".toml",
            "claude": ".md",
            "copilot": ".agent.md",
        }
        for root in roots.values():
            self.assertEqual(4, len([path for path in root.iterdir() if path.is_file()]))
        for host, root in roots.items():
            suffix = expected_suffixes[host]
            main = (root / f"main-control-agent{suffix}").read_text()
            capabilities = BUILD._normalized_decision_capabilities(
                BUILD._load_host_enforcement()["hosts"][host]
            )
            self.assertIn(
                BUILD._render_decision_capability_facts(capabilities),
                main,
            )
            self.assertNotIn("Current host modes:", main)
            self.assertNotIn("diff_input_mode=", main)
            self.assertNotIn("validation_mode=", main)
            for name in ("analysis-agent", "task-agent", "review-agent"):
                worker = (root / f"{name}{suffix}").read_text()
                self.assertNotIn("Current capability facts:", worker)
        for path in (ROOT / "dist/codex/project/.codex/agents").glob("*.toml"):
            self.assertNotIn("permission_enforcement", path.read_text())
        copilot = ROOT / "dist/copilot/project/.github/agents"
        for name in ("analysis-agent", "task-agent", "review-agent"):
            self.assertNotIn("disable-model-invocation: true", (copilot / f"{name}.agent.md").read_text())
        self.assertEqual(4, len(list(copilot.glob("*.agent.md"))))
        copilot_analysis = (copilot / "analysis-agent.agent.md").read_text()
        copilot_analysis_frontmatter = copilot_analysis.split("---", 2)[1]
        self.assertIn(
            'tools: ["read","search","web"]',
            copilot_analysis_frontmatter,
        )
        self.assertIn(
            "Current external-read mode: external_source_read=prompt-enforced.",
            copilot_analysis,
        )
        for forbidden in ("edit", "execute", "agent", "*", "mcp"):
            with self.subTest(copilot_analysis_forbidden=forbidden):
                self.assertNotIn(f'"{forbidden}"', copilot_analysis_frontmatter)
        self.assertEqual(
            (copilot / "analysis-agent.agent.md").read_bytes(),
            (
                ROOT
                / "dist/copilot/user/.copilot/agents/analysis-agent.agent.md"
            ).read_bytes(),
        )
        for path in (ROOT / "dist/claude/project/.claude/agents").glob("*.md"):
            self.assertIn("Skill", path.read_text().splitlines()[3])
        self.assertFalse((ROOT / "dist/copilot/project/.github/copilot/agents").exists())

    def test_quickstart_plan_has_no_obsolete_flags(self) -> None:
        quickstart = load_script("hookless_quickstart", "scripts/quickstart.py")
        args = argparse.Namespace(
            agent="codex",
            scope="project",
            target=Path("/tmp/project"),
            profile="auto",
            dry_run=True,
            no_doctor=False,
        )
        plan = quickstart.build_plan(args)
        command_text = " ".join(" ".join(command) for command in plan.commands)
        self.assertEqual("recommended", plan.selected_profile)
        self.assertEqual(27, plan.expected_skill_count)
        for token in ("--with-hooks", "--without-hooks", "--hook-profile", "activation-level"):
            self.assertNotIn(token, command_text)

        for agent in ("cline", "openai-api"):
            host_args = argparse.Namespace(
                agent=agent,
                scope="project" if agent == "cline" else None,
                target=Path("/tmp/project") if agent == "cline" else None,
                profile="auto",
                dry_run=True,
                no_doctor=False,
            )
            self.assertEqual((), quickstart.build_plan(host_args).agent_profiles)

    def test_real_project_install_doctor_and_uninstall(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw) / "project"
            install = subprocess.run(
                [sys.executable, "installers/install.py", "--agent", "codex", "--scope", "project", "--profile", "recommended", "--target", str(target)],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(0, install.returncode, install.stderr or install.stdout)
            manifest = json.loads(
                (target / ".agents/skills/.changeforge-install-manifest.json").read_text()
            )
            self.assertEqual(
                "ai-consumption-v1",
                manifest["compiled_layer3_format"],
            )
            self.assertEqual(
                "prompt-enforced",
                manifest["installed_agent_profile_enforcement"]["roles"]
                ["main-control-agent"]["tool_allowlist"],
            )
            self.assertEqual(
                {
                    "path": "src/control-model/core-contracts.json",
                    "schema_version": 1,
                    "kind": "changeforge.core_contracts",
                    "sha256": hashlib.sha256(
                        (ROOT / "src/control-model/core-contracts.json").read_bytes()
                    ).hexdigest(),
                },
                manifest["core_model"],
            )
            doctor = subprocess.run(
                [sys.executable, "installers/doctor.py", "--agent", "codex", "--scope", "project", "--profile", "recommended", "--target", str(target)],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(0, doctor.returncode, doctor.stderr or doctor.stdout)
            self.assertIn("tool_allowlist=prompt-enforced", doctor.stdout)
            self.assertIn("diff_input_mode=native", doctor.stdout)
            self.assertIn("validation_mode=native-read-only", doctor.stdout)
            self.assertIn("utility_no_edit=prompt-enforced", doctor.stdout)
            uninstall = subprocess.run(
                [sys.executable, "installers/uninstall.py", "--agent", "codex", "--scope", "project", "--target", str(target)],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(0, uninstall.returncode, uninstall.stderr or uninstall.stdout)
            self.assertFalse((target / ".agents/skills/.changeforge-install-manifest.json").exists())

    def test_doctor_rejects_tampered_installed_core_model_digest(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw) / "project"
            install = subprocess.run(
                [
                    sys.executable,
                    "installers/install.py",
                    "--agent",
                    "codex",
                    "--scope",
                    "project",
                    "--profile",
                    "recommended",
                    "--target",
                    str(target),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, install.returncode, install.stderr or install.stdout)
            manifest_path = (
                target / ".agents/skills/.changeforge-install-manifest.json"
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["core_model"]["sha256"] = "0" * 64
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            doctor = subprocess.run(
                [
                    sys.executable,
                    "installers/doctor.py",
                    "--agent",
                    "codex",
                    "--scope",
                    "project",
                    "--profile",
                    "recommended",
                    "--target",
                    str(target),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(0, doctor.returncode, doctor.stderr or doctor.stdout)
            self.assertIn(
                "installed core model digest does not match the validated build",
                doctor.stdout,
            )

    def test_doctor_rejects_tampered_profile_projection_for_every_host(self) -> None:
        mutations = {
            "codex": (
                Path(".codex/agents/main-control-agent.toml"),
                'sandbox_mode = "read-only"',
                'sandbox_mode = "workspace-write"',
                "sandbox_mode is not the declared default",
            ),
            "claude": (
                Path(".claude/agents/review-agent.md"),
                "tools: Skill, Read, Grep, Glob",
                "tools: Skill, Read, Grep, Glob, Bash",
                "Claude tools differ from the declared default",
            ),
            "copilot": (
                Path(".github/agents/review-agent.agent.md"),
                'tools: ["read","search"]',
                'tools: ["read","search","execute"]',
                "Copilot tools differ from the declared default",
            ),
        }
        for agent, (relative, before, after, projection_error) in mutations.items():
            with self.subTest(agent=agent), tempfile.TemporaryDirectory() as raw:
                target = Path(raw) / "project"
                install = subprocess.run(
                    [
                        sys.executable,
                        "installers/install.py",
                        "--agent",
                        agent,
                        "--scope",
                        "project",
                        "--profile",
                        "recommended",
                        "--target",
                        str(target),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(0, install.returncode, install.stderr or install.stdout)
                profile_path = target / relative
                original = profile_path.read_text(encoding="utf-8")
                self.assertIn(before, original)
                profile_path.write_text(original.replace(before, after, 1), encoding="utf-8")

                doctor = subprocess.run(
                    [
                        sys.executable,
                        "installers/doctor.py",
                        "--agent",
                        agent,
                        "--scope",
                        "project",
                        "--profile",
                        "recommended",
                        "--target",
                        str(target),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertNotEqual(0, doctor.returncode, doctor.stderr or doctor.stdout)
                self.assertIn(
                    "installed Agent Profile file digests do not match the install manifest",
                    doctor.stdout,
                )
                self.assertIn(projection_error, doctor.stdout)

    def test_doctor_rejects_profile_and_synchronously_forged_install_manifest(self) -> None:
        layouts = {
            "codex": (
                Path(".codex/agents/main-control-agent.toml"),
                Path(".agents/skills/.changeforge-install-manifest.json"),
                "\n# forged but valid TOML\n",
            ),
            "claude": (
                Path(".claude/agents/main-control-agent.md"),
                Path(".claude/skills/.changeforge-install-manifest.json"),
                "\n<!-- forged but valid Markdown -->\n",
            ),
            "copilot": (
                Path(".github/agents/main-control-agent.agent.md"),
                Path(".github/skills/.changeforge-install-manifest.json"),
                "\n<!-- forged but valid Markdown -->\n",
            ),
        }
        for agent, (profile_relative, manifest_relative, suffix) in layouts.items():
            with self.subTest(agent=agent), tempfile.TemporaryDirectory() as raw:
                target = Path(raw) / "project"
                install = subprocess.run(
                    [
                        sys.executable,
                        "installers/install.py",
                        "--agent",
                        agent,
                        "--scope",
                        "project",
                        "--profile",
                        "recommended",
                        "--target",
                        str(target),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(0, install.returncode, install.stderr or install.stdout)
                profile_path = target / profile_relative
                profile_path.write_text(
                    profile_path.read_text(encoding="utf-8") + suffix,
                    encoding="utf-8",
                )
                manifest_path = target / manifest_relative
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["installed_agent_profile_sha256"]["main-control-agent"] = (
                    hashlib.sha256(profile_path.read_bytes()).hexdigest()
                )
                manifest_path.write_text(
                    json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                doctor = subprocess.run(
                    [
                        sys.executable,
                        "installers/doctor.py",
                        "--agent",
                        agent,
                        "--scope",
                        "project",
                        "--profile",
                        "recommended",
                        "--target",
                        str(target),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertNotEqual(0, doctor.returncode, doctor.stderr or doctor.stdout)
                self.assertIn(
                    "install manifest Agent Profile digests do not match the validated build",
                    doctor.stdout,
                )
                self.assertIn(
                    "installed Agent Profile files do not match the validated build",
                    doctor.stdout,
                )

    def test_doctor_rejects_legacy_host_mode_marker_for_every_host(self) -> None:
        layouts = {
            "codex": Path(".codex/agents/main-control-agent.toml"),
            "claude": Path(".claude/agents/main-control-agent.md"),
            "copilot": Path(".github/agents/main-control-agent.agent.md"),
        }
        legacy = (
            "Current host modes: diff_input_mode=native; "
            "validation_mode=native-read-only; utility_no_edit=prompt-enforced."
        )
        for agent, relative in layouts.items():
            with self.subTest(agent=agent), tempfile.TemporaryDirectory() as raw:
                target = Path(raw) / "project"
                install = subprocess.run(
                    [
                        sys.executable,
                        "installers/install.py",
                        "--agent",
                        agent,
                        "--scope",
                        "project",
                        "--profile",
                        "recommended",
                        "--target",
                        str(target),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(0, install.returncode, install.stderr or install.stdout)
                profile = target / relative
                profile.write_text(
                    profile.read_text(encoding="utf-8") + f"\n# {legacy}\n",
                    encoding="utf-8",
                )

                doctor = subprocess.run(
                    [
                        sys.executable,
                        "installers/doctor.py",
                        "--agent",
                        agent,
                        "--scope",
                        "project",
                        "--profile",
                        "recommended",
                        "--target",
                        str(target),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertNotEqual(0, doctor.returncode, doctor.stderr or doctor.stdout)
                self.assertIn("legacy host mode projection is forbidden", doctor.stdout)

    def test_doctor_ignores_unrelated_user_profile(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw) / "project"
            install = subprocess.run(
                [sys.executable, "installers/install.py", "--agent", "codex", "--scope", "project", "--profile", "recommended", "--target", str(target)],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(0, install.returncode, install.stderr or install.stdout)
            (target / ".codex/agents/user-owned.toml").write_text(
                'name = "user-owned"\n', encoding="utf-8"
            )
            doctor = subprocess.run(
                [sys.executable, "installers/doctor.py", "--agent", "codex", "--scope", "project", "--profile", "recommended", "--target", str(target)],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(0, doctor.returncode, doctor.stderr or doctor.stdout)


if __name__ == "__main__":
    unittest.main()
