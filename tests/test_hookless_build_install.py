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

from tests.scripts.test_eval_core_principles import (
    assert_core_producer_outcomes_passed,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_script(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


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
            (root / ".changeforge-build-manifest.json").unlink()
            with self.assertRaisesRegex(AssertionError, "build manifest is missing"):
                consumer(self, root, "recommended", 27)

        with tempfile.TemporaryDirectory() as raw:
            root = fixture(Path(raw))
            (root / "skill-00/SKILL.md").unlink()
            with self.assertRaises(AssertionError):
                consumer(self, root, "recommended", 27)


class HooklessBuildInstallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        assert_core_producer_outcomes_passed(
            ROOT,
            "build-recommended",
            "build-full",
            "build-dev",
        )

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
                3,
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
                self.assertEqual(
                    (
                        expected["diff_input_mode"],
                        expected["validation_mode"],
                        expected["utility_no_edit"],
                    ),
                    (
                        enforcement["diff_input_mode"],
                        enforcement["validation_mode"],
                        enforcement["utility_no_edit"],
                    ),
                )
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
                self.assertIn("Never preload Layer 3", skill_text)
                if not candidates:
                    self.assertFalse((skill_root / "references/layer3").exists())
                    self.assertNotIn("(references/layer3/index.md)", skill_text)
                    continue
                self.assertIn("(references/layer3/index.md)", skill_text, (profile, skill_name))
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
            "Targeted References",
        ]
        expected_domain = [
            "Decision Boundary",
            "Professional Decision Rules",
            "High-Value Gotchas",
            "Stop / Escalation Conditions",
            "Targeted References",
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
        nested_text = nested.read_text(encoding="utf-8")
        self.assertIn(
            "transaction-consistency/references/evidence-patterns.md",
            nested_text,
        )
        self.assertTrue(
            (
                nested.parent
                / "transaction-consistency/references/evidence-patterns.md"
            ).is_file()
        )

        full_domain = (
            ROOT
            / "dist/universal/skills/full/bigdata-product-extension/SKILL.md"
        ).read_text(encoding="utf-8")
        dev_foundation = (
            ROOT
            / "dist/universal/skills/dev/transaction-consistency/SKILL.md"
        ).read_text(encoding="utf-8")
        dev_domain = (
            ROOT
            / "dist/universal/skills/dev/bigdata-product-extension/SKILL.md"
        ).read_text(encoding="utf-8")
        for text in (full_domain, dev_domain):
            for heading in (
                "Role",
                "When To Use",
                "Do Not Use",
                "Required Inputs",
                "Execution Checklist",
                "Output Contract",
            ):
                self.assertIn(f"## {heading}", text)
            self.assertNotIn("## Decision Boundary", text)
        for heading in (
            "Registry Trigger",
            "Skill Role",
            "Execution Checklist",
            "Output Contract",
        ):
            self.assertIn(f"## {heading}", dev_foundation)
        self.assertNotIn("## Decision Boundary", dev_foundation)

    def test_source_profiles_use_compact_role_and_generated_delivery_rules(self) -> None:
        data = json.loads((ROOT / "src/agent-profiles/role-agents.json").read_text())
        core = json.loads((ROOT / "src/control-model/core-contracts.json").read_text())
        limits = core["profile_contract"]["instruction_rule_count"]
        expected_counts = {
            "main-control-agent": 6,
            "analysis-agent": 16,
            "task-agent": 38,
            "review-agent": 18,
        }
        profiles = {item["name"]: item for item in data["profiles"]}
        self.assertEqual(set(expected_counts), set(profiles))
        for name, profile in profiles.items():
            rules = profile["instructions"].splitlines()
            maximum = limits["maximum_by_role"].get(name, limits["maximum"])
            self.assertGreaterEqual(len(rules), limits["minimum"])
            self.assertLessEqual(len(rules), maximum)
            self.assertEqual(expected_counts[name], len(rules))
            self.assertTrue(all(rule.startswith("- ") for rule in rules))
            for obsolete in ("In a recommended build", "In a full build", "In a dev build"):
                self.assertNotIn(obsolete, profile["instructions"])
        for name in ("analysis-agent", "task-agent", "review-agent"):
            instructions = profiles[name]["instructions"]
            self.assertIn("generated `## Layer 3 Delivery` section", instructions)
            self.assertIn("Never preload Layer 3", instructions)
            self.assertIn("Layer 3 index or catalog", instructions)
        review = profiles["review-agent"]["instructions"]
        self.assertIn("actual diff or an accessible host-native diff reference", review)
        self.assertIn("inspect the diff and every changed file", review)
        self.assertIn("pre-implementation design", review)
        self.assertIn("no implementation diff is required", review)
        self.assertIn("assigned Review Handoff", review)
        task = profiles["task-agent"]["instructions"]
        task_casefold = task.casefold()
        task_rules = task.splitlines()
        capability_rules = core["profile_contract"]["capability_terms"]
        projected_rules = [
            rule
            for group in (
                "layer3-jit-delivery",
                "task-normal-mode",
                "task-utility-mode",
                "task-scope-boundary",
            )
            for rule in capability_rules[group]
        ]
        projected_rules.extend(
            core["implementation_discipline_contract"]["profile_projection"]
        )
        canonical_task_rules = []
        for rule in projected_rules:
            matches = [
                line
                for line in task_rules
                if all(
                    term.casefold() in line.casefold()
                    for term in rule["required_terms"]
                )
            ]
            self.assertEqual(1, len(matches), rule["rule_id"])
            if "exact_rule" in rule:
                self.assertEqual(rule["exact_rule"], matches[0], rule["rule_id"])
            canonical_task_rules.append(matches[0])

        built_task_profiles = {
            "codex": ROOT / "dist/codex/project/.codex/agents/task-agent.toml",
            "claude": ROOT / "dist/claude/project/.claude/agents/task-agent.md",
            "copilot": (
                ROOT
                / "dist/copilot/project/.github/agents/task-agent.agent.md"
            ),
        }
        for host, path in built_task_profiles.items():
            built_lines = path.read_text(encoding="utf-8").splitlines()
            for rule in task_rules:
                self.assertIn(rule, built_lines, (host, rule))
            for rule in canonical_task_rules:
                self.assertIn(rule, built_lines, (host, rule))
        self.assertIn("return only bounded utility evidence", task_casefold)
        analysis = profiles["analysis-agent"]["instructions"]
        for phrase in (
            "no-repo direct-answer",
            "fully determined by user-supplied facts",
            "Control prompt files are ineligible and require source-backed analysis.",
            "do not load a named Skill, inspect repository or source evidence, or produce an Engineering Brief or First Executable Slice",
            "only user-supplied facts",
            "answer, assumptions, limits, and four-state Status",
            "Remain read-only",
            "one bounded scope in one pass",
            "minimum safe slice handoff",
        ):
            self.assertIn(phrase, analysis)

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
        expected_modes = {
            "codex": ("native", "native-read-only", "prompt-enforced", ".toml"),
            "claude": ("supplied-artifact", "task-no-edit", "prompt-enforced", ".md"),
            "copilot": ("supplied-artifact", "task-no-edit", "prompt-enforced", ".agent.md"),
        }
        for root in roots.values():
            self.assertEqual(4, len([path for path in root.iterdir() if path.is_file()]))
        for host, root in roots.items():
            diff_mode, validation_mode, utility_no_edit, suffix = expected_modes[host]
            main = (root / f"main-control-agent{suffix}").read_text()
            self.assertIn(
                f"Current host modes: diff_input_mode={diff_mode}; validation_mode={validation_mode}; utility_no_edit={utility_no_edit}.",
                main,
            )
            for name in ("analysis-agent", "task-agent", "review-agent"):
                worker = (root / f"{name}{suffix}").read_text()
                self.assertNotIn("Current host modes:", worker)
        for path in (ROOT / "dist/codex/project/.codex/agents").glob("*.toml"):
            self.assertNotIn("permission_enforcement", path.read_text())
        copilot = ROOT / "dist/copilot/project/.github/agents"
        for name in ("analysis-agent", "task-agent", "review-agent"):
            self.assertNotIn("disable-model-invocation: true", (copilot / f"{name}.agent.md").read_text())
        self.assertEqual(4, len(list(copilot.glob("*.agent.md"))))
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
                'tools: ["read", "search"]',
                'tools: ["read", "search", "execute"]',
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
