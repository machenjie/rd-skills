from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validation_utils as validation
from fixture_capsule_contract import render_direct_discovery_extension
from validation_utils import (
    CORE_CONTRACTS,
    direct_bounded_discovery_outcome,
    evidence_resolution_authority,
    load_yaml_file,
    resolve_evidence_gap,
    validate_core_contracts,
)


def _load_script(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


EVAL_ROUTING = _load_script("evidence_direct_eval_routing", "eval-routing.py")
EVAL_PRESSURE = _load_script(
    "evidence_direct_eval_pressure", "eval-pressure-behavior.py"
)
AUDIT_SKILL_CONTENT = _load_script(
    "evidence_direct_audit_skill_content", "audit-skill-content.py"
)
PROMPT = ROOT / "src" / "control-prompts" / "main-control-agent.md"
DIRECT_TEMPLATE = (
    ROOT
    / "src"
    / "control-skills"
    / "engineering-control-plane"
    / "references"
    / "direct-task-template.md"
)
PROFILES = ROOT / "src" / "agent-profiles" / "role-agents.json"
LOCAL_DISCOVERY = (
    ROOT / "evals" / "pressure" / "hookless" / "direct-bounded-local-discovery.yaml"
)
RISK_ESCALATION = (
    ROOT / "evals" / "pressure" / "hookless" / "direct-discovery-risk-escalation.yaml"
)
INTAKE_SKILL = (
    ROOT / "src" / "professional-skills" / "change-intake-compiler" / "SKILL.md"
)


class EvidenceDirectAuthorityTests(unittest.TestCase):
    def test_intake_semantics_project_to_exact_gap_classes_without_second_owner(
        self,
    ) -> None:
        authority = evidence_resolution_authority(CORE_CONTRACTS)
        self.assertEqual("change-intake-compiler", authority["semantics_owner"])
        self.assertTrue(authority["projection_only"])
        collected = validation.collect_skill_root_source(INTAKE_SKILL)
        self.assertEqual(
            collected["source_fingerprint"],
            authority["source_binding"]["source_fingerprint"],
        )
        self.assertEqual(
            validation.evidence_resolution_source_declaration(INTAKE_SKILL)[
                "gap_classes"
            ],
            authority["gap_classes"],
        )
        choice = next(
            row for row in authority["gap_classes"] if row["id"] == "user-owned-choice"
        )
        self.assertEqual(
            ["semantic-choice", "execution-level-choice"], choice["subtypes"]
        )

    def test_audit_root_collector_and_evidence_binding_share_one_source_reader(
        self,
    ) -> None:
        original = validation.collect_skill_root_source
        observed: list[str] = []

        def recording_collector(path: Path, *, root: Path = ROOT) -> dict[str, str]:
            observed.append(path.as_posix())
            return original(path, root=root)

        with mock.patch.object(
            AUDIT_SKILL_CONTENT._validation_utils,
            "collect_skill_root_source",
            side_effect=recording_collector,
        ):
            documents = AUDIT_SKILL_CONTENT._root_skill_documents()
        self.assertIn(INTAKE_SKILL.as_posix(), observed)
        intake = next(
            row
            for row in documents
            if row["path"]
            == "src/professional-skills/change-intake-compiler/SKILL.md"
            and row["document_part"] == "body"
        )
        self.assertIn("source-discoverable fact", intake["text"])

    def test_source_fact_uses_direct_only_when_semantic_route_and_risk_are_stable(
        self,
    ) -> None:
        local = resolve_evidence_gap(
            "repo-resolvable-fact", route_affecting_surfaces=[]
        )
        self.assertEqual("direct", local["path"])
        self.assertEqual("direct-bounded-discovery", local["resolution"])
        self.assertEqual(0, local["question_count"])

        for surface in evidence_resolution_authority(CORE_CONTRACTS)[
            "route_affecting_surfaces"
        ]:
            with self.subTest(surface=surface):
                material = resolve_evidence_gap(
                    "repo-resolvable-fact",
                    route_affecting_surfaces=[surface],
                )
                self.assertEqual("analyzed", material["path"])
                self.assertEqual("analysis", material["resolution"])
                self.assertEqual(0, material["question_count"])

    def test_user_choice_asks_once_and_only_execution_choice_is_projection_only(
        self,
    ) -> None:
        semantic = resolve_evidence_gap(
            "user-owned-choice", choice_kind="semantic-choice"
        )
        self.assertIsNone(semantic["path"])
        self.assertEqual("ask", semantic["action_authority"])
        self.assertEqual(1, semantic["question_count"])
        self.assertEqual("protected-brief-semantics", semantic["invalidation"])

        level = resolve_evidence_gap(
            "user-owned-choice", choice_kind="execution-level-choice"
        )
        self.assertEqual(1, level["question_count"])
        self.assertEqual("execution-level-projection-only", level["invalidation"])
        self.assertFalse(level["semantic_route_change"])

    def test_material_unknown_never_enters_direct(self) -> None:
        decision = resolve_evidence_gap("route-or-material-unknown")
        self.assertEqual("analyzed", decision["path"])
        self.assertEqual("block", decision["action_authority"])
        self.assertEqual("analysis-or-fail-closed", decision["resolution"])

    def test_direct_discovery_has_only_three_outcomes_and_worker_never_reroutes(
        self,
    ) -> None:
        confirmed = direct_bounded_discovery_outcome(
            "boundary-confirmed", risk_change="simpler"
        )
        self.assertTrue(confirmed["may_edit"])
        self.assertEqual("confirm-and-continue", confirmed["worker_action"])
        self.assertEqual("preserve-current", confirmed["level_action"])
        self.assertEqual("current-route-only", confirmed["route_authority"])

        invalidated = direct_bounded_discovery_outcome(
            "route-or-risk-invalidated", risk_change="higher"
        )
        self.assertFalse(invalidated["may_edit"])
        self.assertEqual("return-main-for-analysis", invalidated["worker_action"])
        self.assertEqual("recompute", invalidated["level_action"])
        self.assertEqual("worker-reroute-forbidden", invalidated["route_authority"])

        choice = direct_bounded_discovery_outcome("user-choice-discovered")
        self.assertFalse(choice["may_edit"])
        self.assertEqual("return-main-for-one-question", choice["worker_action"])
        self.assertEqual(1, choice["question_count"])

    def test_direct_template_and_capsule_projection_name_exact_boundaries(self) -> None:
        text = " ".join(DIRECT_TEMPLATE.read_text(encoding="utf-8").split())
        for term in (
            "exact owning symbol/file",
            "relevant existing test",
            "minimum local consumer",
            "local reuse candidate",
            "local validation command",
            "already-known owner boundary",
            "repo-wide discovery",
            "Worker rerouting",
            "confirm and continue",
            "stop before editing and return to Main",
        ):
            with self.subTest(term=term):
                self.assertIn(term, text)

        rendered = render_direct_discovery_extension(
            {
                "inspection_boundary": ["named owner", "targeted test", "consumer"],
                "inspection_stop_conditions": ["route invalidated", "user choice"],
            }
        )
        self.assertIn("## Inspection Boundary", rendered)
        self.assertIn("## Inspection Stop Conditions", rendered)

    def test_unknown_boundary_requires_analysis_but_bounded_confirmation_is_allowed(
        self,
    ) -> None:
        prompt = " ".join(PROMPT.read_text(encoding="utf-8").split())
        template = " ".join(DIRECT_TEMPLATE.read_text(encoding="utf-8").split())
        profiles = {
            row["name"]: " ".join(row["instructions"].split())
            for row in json.loads(PROFILES.read_text(encoding="utf-8"))["profiles"]
        }
        combined = " ".join((prompt, template, profiles["task-agent"]))
        for obsolete in (
            "without ownership/verification discovery",
            "If ownership or verification needs discovery",
        ):
            with self.subTest(obsolete=obsolete):
                self.assertNotIn(obsolete, combined)
        for required in (
            "unknown owner/module/system/verification boundary",
            "already-known stable owner/test/consumer boundary",
            "bounded confirmation",
        ):
            with self.subTest(required=required):
                self.assertIn(required, combined)

        escaped = json.loads(json.dumps(CORE_CONTRACTS))
        escaped["task_contract"]["direct_bounded_discovery"]["outcomes"][
            "route-or-risk-invalidated"
        ] = "continue-editing-after-boundary-escape"
        self.assertTrue(
            any(
                "Direct bounded discovery" in error
                for error in validate_core_contracts(escaped)
            )
        )

    def test_prompt_profiles_and_brief_authority_forbid_worker_reinterpretation(
        self,
    ) -> None:
        prompt = PROMPT.read_text(encoding="utf-8")
        for term in (
            "repo-resolvable-fact",
            "user-owned-choice",
            "route-or-material-unknown",
            "semantic-choice",
            "execution-level-choice",
            "Direct bounded discovery",
            "Worker never reroutes",
        ):
            self.assertIn(term, prompt)
        profiles = {
            row["name"]: row["instructions"]
            for row in json.loads(PROFILES.read_text(encoding="utf-8"))["profiles"]
        }
        self.assertIn("Evidence Resolution", profiles["main-control-agent"])
        self.assertIn("Brief decision authority", profiles["analysis-agent"])
        self.assertIn("bounded discovery", profiles["task-agent"])
        self.assertIn("must not reroute", profiles["review-agent"])
        ownership = CORE_CONTRACTS["task_contract"]["analyzed_work_authority"][
            "decision_ownership"
        ]
        self.assertEqual("forbidden", ownership["main_reinterpretation"])
        self.assertEqual("forbidden", ownership["worker_route_change"])

    def test_core_rejects_source_binding_drift_and_repo_wide_discovery(self) -> None:
        for field, mutation in (
            ("source_path", "src/professional-skills/missing/SKILL.md"),
            ("source_anchor", "not present in the owning Skill"),
            ("source_fingerprint", "0" * 64),
        ):
            with self.subTest(field=field):
                drift = json.loads(json.dumps(CORE_CONTRACTS))
                authority = drift["task_contract"]["evidence_resolution"]
                if field == "source_anchor":
                    authority["gap_classes"][0][field] = mutation
                elif field == "source_fingerprint":
                    authority["source_binding"][field] = mutation
                else:
                    authority[field] = mutation
                self.assertTrue(
                    any(
                        "Evidence Resolution" in error
                        for error in validate_core_contracts(drift)
                    )
                )

        discovery = json.loads(json.dumps(CORE_CONTRACTS))
        discovery["task_contract"]["direct_bounded_discovery"][
            "prohibited"
        ].remove("repo-wide-discovery")
        self.assertTrue(
            any("Direct bounded discovery" in error for error in validate_core_contracts(discovery))
        )
        self.assertEqual(
            ["direct", "analyzed"],
            CORE_CONTRACTS["route_decision_contract"]["path_values"],
        )

    def test_pressure_fixtures_prove_direct_confirmation_and_risk_return(self) -> None:
        local = load_yaml_file(LOCAL_DISCOVERY)
        escalation = load_yaml_file(RISK_ESCALATION)
        self.assertEqual("task-agent", local["expected"]["profile"])
        self.assertIn(
            "confirmed bounded owner test consumer reuse placement and validation evidence before editing",
            local["expected"]["behaviors"],
        )
        self.assertIn(
            "returned to Main before editing without selecting a new Skill Domain or Layer3",
            escalation["expected"]["behaviors"],
        )
        report = EVAL_PRESSURE.evaluate_pressure_cases()
        self.assertEqual([], report["errors"])

    def test_erpar_00_evidence_and_discovery_mutants_remain_green(self) -> None:
        report = EVAL_ROUTING.evaluate_decision_cases()
        by_id = {row["id"]: row for row in report["results"]}
        for mutant in (
            "source-fact-to-ask-user",
            "user-choice-to-source-inference",
            "route-material-unknown-to-direct",
            "direct-discovery-escape-then-edit",
        ):
            with self.subTest(mutant=mutant):
                self.assertTrue(by_id[mutant]["passed"])


if __name__ == "__main__":
    unittest.main()
