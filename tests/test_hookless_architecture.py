from __future__ import annotations

import importlib.util
import json
import re
import sys
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validation_utils import (  # noqa: E402
    CORE_CONTRACTS,
    heading_entries,
    load_yaml_file,
)


OPAQUE_DIGEST_RE = re.compile(
    r"(?<![0-9A-Fa-f])[0-9a-f]{64}(?![0-9A-Fa-f])"
    r"|sha256-b64u:(?:[A-Za-z0-9_-]{43}|<43-character-base64url-SHA-256>)"
    r"|<43-character-base64url-SHA-256>"
)


def _load_validator(module_name: str, file_name: str):
    spec = importlib.util.spec_from_file_location(module_name, ROOT / "scripts" / file_name)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CONTROL_PROMPT_VALIDATOR = _load_validator(
    "hookless_control_prompt_validator",
    "validate-control-plane-prompt.py",
)
CONTROL_SKILL_VALIDATOR = _load_validator(
    "hookless_control_skill_validator",
    "validate-control-skills.py",
)


class HooklessArchitectureTests(unittest.TestCase):
    def test_runtime_validators_do_not_offer_retired_profile_selection(self) -> None:
        for path in (
            ROOT / "scripts/validate-installation.py",
            ROOT / "scripts/validate-built-skill-reference-links.py",
        ):
            source = path.read_text(encoding="utf-8")
            self.assertNotRegex(
                source,
                r'(?m)^PROFILES = \("recommended", "full", "dev"\)$',
            )
            self.assertNotIn('add_argument("--profile"', source)

    def test_source_boundary_contains_only_authoring_assets(self) -> None:
        expected = {
            "agent-profiles",
            "control-model",
            "control-prompts",
            "control-skills",
            "domain-extensions",
            "foundation",
            "professional-skills",
            "registry",
        }
        actual = {path.name for path in (ROOT / "src").iterdir() if path.is_dir()}
        self.assertEqual(expected, actual)

    def test_obsolete_runtime_paths_are_absent(self) -> None:
        forbidden = (
            "src/hook-runtime",
            "src/runtime_governance",
            "src/process_governance",
            "src/project_memory",
            "src/repository_intelligence",
            "src/validation_broker",
            "src/trajectory",
            "src/executor_backends",
        )
        self.assertFalse([path for path in forbidden if (ROOT / path).exists()])
        self.assertEqual([ROOT / "schemas" / "marketplace-index.schema.json"], list((ROOT / "schemas").glob("*.json")))

    def test_four_profiles_have_exact_tool_boundaries(self) -> None:
        data = json.loads((ROOT / "src/agent-profiles/role-agents.json").read_text())
        profiles = {item["name"]: item for item in data["profiles"]}
        self.assertEqual(
            {name: role["tools"] for name, role in CORE_CONTRACTS["roles"].items()},
            {name: item["tools"] for name, item in profiles.items()},
        )
        self.assertEqual(
            {name: role["sandbox"] for name, role in CORE_CONTRACTS["roles"].items()},
            {name: item["sandbox"] for name, item in profiles.items()},
        )




    def test_control_skill_rejects_any_seventh_link(self) -> None:
        links = "\n".join(
            f"- [{name}](references/{name})"
            for name in CONTROL_SKILL_VALIDATOR.REFERENCES
        )
        body = (
            "# Engineering Control Plane\n\n## Targeted References\n\n"
            f"{links}\n- [unexpected](https://example.com)\n"
        )
        errors: list[str] = []
        CONTROL_SKILL_VALIDATOR._validate_references(body, errors)
        self.assertTrue(
            any(
                "must link exactly the runtime contract, router, and six templates" in error
                for error in errors
            ),
            errors,
        )

    def test_control_skill_rejects_raw_host_branch_value_mutations(self) -> None:
        self.assertEqual(
            tuple(CONTROL_SKILL_VALIDATOR._HOST_ENFORCEMENT["status_values"]),
            CONTROL_SKILL_VALIDATOR.FORBIDDEN_HOST_MODE_BRANCH_LITERALS,
        )
        self.assertTrue(CONTROL_SKILL_VALIDATOR.FORBIDDEN_HOST_MODE_BRANCH_LITERALS)
        source = CONTROL_SKILL_VALIDATOR.SKILL.read_text(encoding="utf-8")
        for literal in CONTROL_SKILL_VALIDATOR.FORBIDDEN_HOST_MODE_BRANCH_LITERALS:
            with self.subTest(literal=literal):
                errors: list[str] = []
                mutated = f"{source}\n- forbidden host branch: {literal}\n"
                CONTROL_SKILL_VALIDATOR._validate_no_host_mode_branches(
                    mutated,
                    errors,
                )
                self.assertTrue(
                    any(literal in error for error in errors),
                    errors,
                )

    def test_control_skill_host_branch_gate_is_markdown_independent(self) -> None:
        for rendered in ("native-enforced", "`native-enforced`"):
            errors: list[str] = []
            CONTROL_SKILL_VALIDATOR._validate_no_host_mode_branches(
                f"tool_allowlist={rendered}",
                errors,
            )
            self.assertTrue(errors, rendered)


    def test_four_registries_have_required_ai_contract_fields(self) -> None:
        specs = {
            "control-skills.yaml": ("control_skills", 1),
            "professional-skills.yaml": ("professional_skills", 25),
            "foundation-skills.yaml": ("foundation_skills", 150),
            "domain-skills.yaml": ("domain_skills", 13),
        }
        fields = {
            "name",
            "path",
            "role_support",
            "trigger_signals",
            "anti_trigger_signals",
            "required_inputs",
            "output_contract",
            "escalation_signals",
            "reference_index",
        }
        for file_name, (key, count) in specs.items():
            data = load_yaml_file(ROOT / "src/registry" / file_name)
            expected_schema = {
                "control-skills.yaml": 3,
                "professional-skills.yaml": 5,
                "foundation-skills.yaml": 8,
                "domain-skills.yaml": 6,
            }[file_name]
            self.assertEqual(expected_schema, data["schema_version"])
            items = data[key]
            self.assertEqual(count, len(items), file_name)
            for item in items:
                self.assertTrue(fields.issubset(item), f"{file_name}:{item.get('name')}")
                if file_name == "domain-skills.yaml":
                    self.assertIn("boundary_signals", item)
                if file_name != "control-skills.yaml":
                    self.assertIn("required_expertise_tags", item)
                    self.assertEqual(
                        sorted(set(item["required_expertise_tags"])),
                        item["required_expertise_tags"],
                    )
                self.assertTrue((ROOT / item["path"] / "SKILL.md").is_file())
                self.assertFalse(any(name.startswith("runtime_") for name in item))
                if file_name == "professional-skills.yaml" and len(item["role_support"]) > 1:
                    self.assertEqual(
                        set(item["required_inputs_by_role"]),
                        set(item["role_support"]),
                    )
                    self.assertEqual(
                        set(item["output_contract_by_role"]),
                        set(item["role_support"]),
                    )
            if file_name == "foundation-skills.yaml":
                self.assertEqual(
                    Counter(item["delivery_scope"] for item in items),
                    {"product": 141, "authoring-only": 1, "dev-only": 8},
                )
                self.assertEqual(
                    Counter(item["content_class"] for item in items),
                    {"compact": 128, "complex": 22},
                )
                self.assertTrue(
                    all(
                        ("content_class_rationale" in item)
                        == (item["content_class"] == "complex")
                        for item in items
                    )
                )

    def test_security_anti_triggers_exactly_match_the_root_boundary(self) -> None:
        registry = load_yaml_file(
            ROOT / "src/registry/professional-skills.yaml"
        )["professional_skills"]
        security = next(
            item for item in registry if item["name"] == "security-privacy-gate"
        )
        root = (
            ROOT / "src/professional-skills/security-privacy-gate/SKILL.md"
        ).read_text(encoding="utf-8")
        do_not_use = root.split("\n## Do Not Use\n", 1)[1].split("\n## ", 1)[0]
        root_anti_triggers = [
            line.removeprefix("- ")
            for line in do_not_use.splitlines()
            if line.startswith("- ")
        ]
        narrow_refactor_boundary = (
            "internal refactor with evidence that security controls and "
            "credential, session, and privacy lifecycle behavior are unchanged"
        )

        self.assertEqual(security["anti_trigger_signals"], root_anti_triggers)
        self.assertIn(narrow_refactor_boundary, root_anti_triggers)
        self.assertNotIn(
            "internal refactor with evidence that credential and session "
            "lifecycle behavior is unchanged",
            root_anti_triggers,
        )
        self.assertNotIn(
            "credential or session lifecycle with no new trust boundary",
            root_anti_triggers,
        )
        self.assertIn(
            "credential or session lifecycle behavior change",
            security["trigger_signals"],
        )
        self.assertIn(
            "- credential or session lifecycle behavior change",
            root.split("\n## When To Use\n", 1)[1].split("\n## ", 1)[0],
        )


if __name__ == "__main__":
    unittest.main()
