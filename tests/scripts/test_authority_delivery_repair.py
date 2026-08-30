from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build as BUILD
import deterministic_route_oracle as ORACLE
from fixture_capsule_contract import decode_public_task_extension
from validation_utils import (
    CORE_CONTRACTS,
    load_yaml_file,
    validate_core_contracts,
    validate_main_execution,
)


ROUTING_FIXTURES = (
    ROOT / "evals" / "routing" / "cases.yaml",
    ROOT / "evals" / "routing" / "capability-coverage-cases.yaml",
    ROOT / "evals" / "capability-coverage" / "admission-cases.yaml",
)
BRIEF = (
    ROOT
    / "src"
    / "control-skills"
    / "engineering-control-plane"
    / "references"
    / "engineering-brief-template.md"
)


def _direct_cases(path: Path) -> list[dict[str, object]]:
    document = load_yaml_file(path)
    cases = document["cases"]
    assert isinstance(cases, list)
    return [
        case
        for case in cases
        if isinstance(case, dict)
        and isinstance(case.get("main_execution"), dict)
        and "execution_level" in case["main_execution"]
    ]


class AuthorityDeliveryRepairTests(unittest.TestCase):
    def test_all_active_frozen_route_inputs_are_v2(self) -> None:
        expected_basis = set(
            CORE_CONTRACTS["execution_level_contract"]["level_basis_fields"]
        )
        observed = 0
        invalid: list[str] = []
        for path in ROUTING_FIXTURES:
            for case in _direct_cases(path):
                observed += 1
                main = case["main_execution"]
                if validate_main_execution(main) or set(main["level_basis"]) != expected_basis:
                    invalid.append(f"{path.name}:{case['id']}")
        self.assertGreater(observed, 0)
        self.assertEqual([], invalid)

    def test_canonical_active_route_rejects_v1_before_routing(self) -> None:
        direct = _direct_cases(ROOT / "evals" / "routing" / "cases.yaml")[0]
        legacy = copy.deepcopy(direct["main_execution"])
        basis = legacy["level_basis"]
        for field in (
            "l1_eligibility",
            "l5_assurance_eligibility",
            "l5_confirmation",
        ):
            basis.pop(field, None)
        errors = validate_main_execution(legacy)
        self.assertTrue(errors)
        self.assertTrue(
            any("execution-level/v1" in error and "reissue" in error for error in errors),
            errors,
        )
        with self.assertRaisesRegex(ORACLE.RoutingIntegrityError, "v1.*reissue"):
            ORACLE.route(str(direct["prompt"]), main_execution=legacy)

        legacy_wire = "\n".join(
            (
                "Level: automatic=L2; effective=L2; edit=allowed",
                "Basis: t=[]; l=[]; u=[]",
            )
        )
        self.assertEqual(
            "execution-level/v1",
            decode_public_task_extension(legacy_wire)["version"],
        )

    def test_evidence_adapter_is_owned_by_the_core_model(self) -> None:
        authority = CORE_CONTRACTS["task_contract"]["evidence_resolution"]
        self.assertEqual("core-control-model", authority["authority_owner"])
        self.assertEqual(
            "control.evidence-resolution-decision-adapter/v1",
            authority["adapter_contract"],
        )
        self.assertEqual(
            {
                "discoverable-fact",
                "reversible-assumption",
                "unsafe-or-non-reversible-assumption",
                "user-owned-decision",
            },
            set(authority["professional_input_semantics"]),
        )
        self.assertEqual(
            ["reversible-assumption"], authority["non_gap_semantics"]
        )

    def test_duplicate_semantic_and_repo_fact_direct_route_fail_closed(self) -> None:
        invented = copy.deepcopy(CORE_CONTRACTS)
        gap_classes = invented["task_contract"]["evidence_resolution"][
            "gap_classes"
        ]
        gap_classes[0]["input_semantic"] = gap_classes[1]["input_semantic"]
        errors = validate_core_contracts(invented)
        self.assertTrue(
            any("input semantics must remain unique" in error for error in errors),
            errors,
        )

        unsafe_route = copy.deepcopy(CORE_CONTRACTS)
        unsafe_route["task_contract"]["evidence_resolution"]["decision_rules"][
            "repo-resolvable-fact"
        ]["route_affecting"] = "direct"
        errors = validate_core_contracts(unsafe_route)
        self.assertTrue(
            any("route-affecting facts must fail closed" in error for error in errors),
            errors,
        )

    def test_brief_names_exact_owner_reachable_jit_projection(self) -> None:
        contract = CORE_CONTRACTS["layer3_selector_contract"]
        expected = (
            "engineering-control-plane/references/selectors/"
            "<professional-skill>.json"
        )
        self.assertEqual(expected, contract.get("delivery_path_template"))
        brief = " ".join(BRIEF.read_text(encoding="utf-8").split())
        self.assertIn(expected, brief)
        self.assertIn("exact authorized Layer 3", brief)
        self.assertIn("skip the selector file", brief)
        self.assertIn("one current-Professional projection", brief)

    def test_built_analysis_brief_loads_one_projection_and_exact_route_skips(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            dist = Path(temporary) / "dist"
            universal = dist / "universal" / "skills"
            agent_skill_roots = tuple(
                dist / relative
                for relative in (
                    "codex/project/.agents/skills",
                    "codex/user/.agents/skills",
                    "codex/admin/skills",
                    "claude/project/.claude/skills",
                    "claude/user/.claude/skills",
                    "copilot/project/.github/skills",
                    "copilot/user/.copilot/skills",
                    "cline/project/.cline/skills",
                    "cline/user/.cline/skills",
                )
            )
            profile_outputs = tuple(
                (host, dist / relative)
                for host, relative in (
                    ("codex", "codex/project/.codex/agents"),
                    ("codex", "codex/user/.codex/agents"),
                    ("codex", "codex/admin/agents"),
                    ("claude", "claude/project/.claude/agents"),
                    ("claude", "claude/user/.claude/agents"),
                    ("copilot", "copilot/project/.github/agents"),
                    ("copilot", "copilot/user/.copilot/agents"),
                )
            )
            with mock.patch.multiple(
                BUILD,
                DIST_DIR=dist,
                UNIVERSAL_SKILLS_ROOT=universal,
                OPENAI_ZIP_DIR=dist / "openai-api" / "zips",
                AGENT_SKILL_ROOTS=agent_skill_roots,
                AGENT_PROFILE_OUTPUTS=profile_outputs,
            ):
                BUILD.build_profile("recommended")

            skills = universal / "recommended"
            control = skills / "engineering-control-plane"
            built_brief = (
                control / "references" / "engineering-brief-template.md"
            ).read_text(encoding="utf-8")
            expected_relative = Path(
                "engineering-control-plane/references/selectors/"
                "data-api-contract-changer.json"
            )
            self.assertIn(
                "engineering-control-plane/references/selectors/"
                "<professional-skill>.json",
                built_brief,
            )

            loaded: list[str] = []

            def load_current_professional() -> dict[str, object]:
                loaded.append(expected_relative.as_posix())
                return json.loads(
                    (skills / expected_relative).read_text(encoding="utf-8")
                )

            def consume_for_brief(
                exact_layer3: list[str] | None,
            ) -> dict[str, object]:
                if exact_layer3 is not None:
                    return {
                        "selector_loaded": False,
                        "exact_layer3": list(exact_layer3),
                    }
                projection = load_current_professional()
                return {
                    "selector_loaded": True,
                    "projection": projection,
                }

            consumed = consume_for_brief(None)
            projection = consumed["projection"]
            surfaces = [
                row
                for row in projection["owner_surfaces"]
                if row["selection_owner"] == "engineering-brief"
            ]
            self.assertEqual(
                {"task-agent"},
                {row["profile"] for row in surfaces},
            )
            self.assertEqual([expected_relative.as_posix()], loaded)
            self.assertFalse(
                (control / "references" / "selectors" / "index.json").exists()
            )

            fixed = consume_for_brief(["api-contract-design"])
            self.assertFalse(fixed["selector_loaded"])
            self.assertEqual([expected_relative.as_posix()], loaded)


if __name__ == "__main__":
    unittest.main()
