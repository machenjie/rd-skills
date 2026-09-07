from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validation_utils as VALIDATION


def _load_context_eval():
    path = ROOT / "scripts" / "eval-rendered-context-budget.py"
    spec = importlib.util.spec_from_file_location("eval_rendered_context_budget", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CONTEXT_EVAL = _load_context_eval()
PROFESSIONAL_PATH = ROOT / "src" / "registry" / "professional-skills.yaml"
FOUNDATION_PATH = ROOT / "src" / "registry" / "foundation-skills.yaml"
DOMAIN_PATH = ROOT / "src" / "registry" / "domain-skills.yaml"


class ContextAdmissibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.professional = VALIDATION.load_yaml_file(PROFESSIONAL_PATH)
        cls.foundation = VALIDATION.load_yaml_file(FOUNDATION_PATH)
        cls.domain = VALIDATION.load_yaml_file(DOMAIN_PATH)

    def _authority(self, professional=None, foundation=None):
        projector = getattr(
            VALIDATION,
            "reference_context_admissibility_authority",
            None,
        )
        self.assertTrue(
            callable(projector),
            "source-owned Reference context admissibility authority is absent",
        )
        return projector(
            self.professional if professional is None else professional,
            self.foundation if foundation is None else foundation,
            self.domain,
            context="focused context admissibility",
        )

    @staticmethod
    def _row(document, key, name):
        return next(row for row in document[key] if row["name"] == name)

    def test_selected_expertise_is_reachable_without_a_process_floor(self) -> None:
        authority = self._authority()
        decisions = VALIDATION.reference_context_admissibility_decisions

        proactive = decisions(
            authority,
            references=[
                (
                    "backend-change-builder",
                    "references/proactive-triggers.md",
                )
            ],
            path="direct",
        )
        self.assertTrue(proactive["reachable"])
        self.assertEqual([], proactive["conflicts"])

        for path in (
            "references/backend-output-and-gates.md",
            "references/professional-modes.md",
        ):
            with self.subTest(path=path):
                local = decisions(
                    authority,
                    references=[("backend-change-builder", path)],
                    path="direct",
                )
                self.assertTrue(local["reachable"])

        for owner, path in (
            (
                "backend-change-builder",
                "references/solution-optimality.md",
            ),
            (
                "domain-object-identification",
                "references/benchmarks-and-patterns.md",
            ),
            (
                "filesystem-process-safety",
                "references/child-process-invocation-and-completion.md",
            ),
            (
                "filesystem-process-safety",
                "references/atomic-filesystem-commit-and-containment.md",
            ),
        ):
            with self.subTest(owner=owner, path=path):
                unknown = decisions(
                    authority,
                    references=[(owner, path)],
                    path="direct",
                )
                self.assertTrue(unknown["reachable"])

    def test_missing_declaration_is_conservatively_reachable(self) -> None:
        authority = self._authority()
        decision = VALIDATION.reference_context_admissibility_decisions(
            authority,
            references=[
                ("backend-change-builder", "references/checklist.md")
            ],
            path="direct",
        )
        self.assertTrue(decision["reachable"])
        self.assertEqual([], decision["declarations"])
        self.assertEqual(
            [("backend-change-builder", "references/checklist.md")],
            decision["undeclared_references"],
        )

    def test_invalid_declarations_fail_closed(self) -> None:
        cases = []

        invented_problem = copy.deepcopy(self.professional)
        backend = next(
            row
            for row in invented_problem["professional_skills"]
            if row["name"] == "backend-change-builder"
        )
        self.assertIn("context_admissibility", backend)
        backend["context_admissibility"]["references"][
            "references/proactive-triggers.md"
        ]["decision_problem"] = "invented-problem"
        cases.append(invented_problem)

        invented_conflict = copy.deepcopy(self.professional)
        backend = next(
            row
            for row in invented_conflict["professional_skills"]
            if row["name"] == "backend-change-builder"
        )
        backend["context_admissibility"]["references"][
            "references/proactive-triggers.md"
        ]["conflicts_with"] = ["references/invented.md"]
        cases.append(invented_conflict)

        invented_path = copy.deepcopy(self.professional)
        backend = next(
            row
            for row in invented_path["professional_skills"]
            if row["name"] == "backend-change-builder"
        )
        backend["context_admissibility"]["references"][
            "references/invented.md"
        ] = backend["context_admissibility"]["references"].pop(
            "references/proactive-triggers.md"
        )
        cases.append(invented_path)

        for document in cases:
            with self.subTest():
                with self.assertRaises(VALIDATION.ValidationProblem):
                    self._authority(professional=document)

    def test_uncapped_selected_union_measures_four_or_more_independent_files(self) -> None:
        report = CONTEXT_EVAL.evaluate()["admissible_context_compositions"]
        self.assertGreaterEqual(
            report["inventory"]["maximum_selected_reference_count"],
            4,
        )
        self.assertEqual(
            1, report["inventory"]["maximum_loaded_reference_count"]
        )
        self.assertGreater(
            report["inventory"]["required_output_receipt_count"], 0
        )
        self.assertEqual(
            0, report["inventory"]["required_output_receipt_failure_count"]
        )
        self.assertEqual(0, report["inventory"]["dropped_reference_obligation_count"])
        self.assertEqual([], report["errors"])
        self.assertTrue(
            all(
                maximum is not None
                for maximum in report["max_by_budget_class"].values()
            )
        )

    def test_v3_authority_projects_named_problems_sequences_and_co_triggers(self) -> None:
        authority = self._authority()
        self.assertEqual(
            "changeforge.reference-context-admissibility/v3",
            authority["contract"],
        )
        display = authority["owners"]["linux-desktop-platform-extension"][
            "declarations"
        ]["references/display-session-and-toolkit-contracts.md"]
        self.assertEqual(
            "display-session-and-toolkit-contracts",
            display["decision_problem"],
        )
        self.assertEqual(
            [],
            display["sequenced_after"],
        )
        display_evidence = authority["owners"][
            "linux-desktop-platform-extension"
        ]["declarations"][
            "references/display-session-and-toolkit-contracts-"
            "implementation-and-review-evidence.md"
        ]
        self.assertEqual(1, len(display_evidence["sequenced_after"]))
        self.assertEqual(
            "linux-desktop-platform-extension/references/"
            "display-session-and-toolkit-contracts.md",
            display_evidence["sequenced_after"][0]["reference"],
        )
        lifecycle = authority["owners"]["android-platform-extension"][
            "declarations"
        ]["references/lifecycle-task-and-state-contracts.md"]
        self.assertEqual([], lifecycle["sequenced_after"])
        self.assertEqual([], lifecycle["must_co_trigger_with"])

        for owner, routing_path in (
            (
                "linux-desktop-platform-extension",
                "references/server-and-system-boundaries.md",
            ),
            (
                "windows-platform-extension",
                "references/service-background-and-notification-contracts.md",
            ),
        ):
            declarations = authority["owners"][owner]["declarations"]
            self.assertEqual([], declarations[routing_path]["sequenced_after"])
            self.assertEqual([], declarations[routing_path]["must_co_trigger_with"])
            self.assertEqual(
                7,
                sum(bool(rule["sequenced_after"]) for rule in declarations.values()),
            )
            self.assertTrue(
                all(not rule["must_co_trigger_with"] for rule in declarations.values())
            )

    def test_v3_schema_rejects_cycle_output_carrier_role_and_nonreciprocity(self) -> None:
        self.assertEqual(
            "changeforge.reference-context-admissibility/v3",
            self._authority()["contract"],
        )
        cases = []

        cycle = copy.deepcopy(self.domain)
        linux = self._row(cycle, "domain_skills", "linux-desktop-platform-extension")
        declarations = linux["context_admissibility"]["references"]
        display_path = (
            "references/display-session-and-toolkit-contracts-"
            "implementation-and-review-evidence.md"
        )
        server_path = (
            "references/server-and-system-boundaries-"
            "implementation-and-review-evidence.md"
        )
        for successor, predecessor in (
            (display_path, server_path),
            (server_path, display_path),
        ):
            declarations[successor]["sequenced_after"].append({
                "reference": f"linux-desktop-platform-extension/{predecessor}",
                "required_output": "evidence-record",
                "carried_by": copy.deepcopy(
                    declarations[successor]["sequenced_after"][0]["carried_by"]
                ),
            })
        # Either edge alone must satisfy the role, output, and carrier contract.
        for path in (display_path, server_path):
            acyclic = copy.deepcopy(cycle)
            self._row(acyclic, "domain_skills", "linux-desktop-platform-extension")[
                "context_admissibility"
            ]["references"][path]["sequenced_after"].pop()
            VALIDATION.reference_context_admissibility_authority(
                self.professional,
                self.foundation,
                acyclic,
                context="valid one-way evidence sequence",
            )
        cases.append(("Reference sequencing graph is cyclic", cycle))

        unknown_output = copy.deepcopy(self.domain)
        linux = self._row(
            unknown_output, "domain_skills", "linux-desktop-platform-extension"
        )
        linux["context_admissibility"]["references"][
            "references/display-session-and-toolkit-contracts-"
            "implementation-and-review-evidence.md"
        ]["sequenced_after"][0]["required_output"] = "invented-output"
        cases.append(("is not produced by the predecessor", unknown_output))

        stale_field = copy.deepcopy(self.domain)
        linux = self._row(
            stale_field, "domain_skills", "linux-desktop-platform-extension"
        )
        linux["context_admissibility"]["references"][
            "references/display-session-and-toolkit-contracts-"
            "implementation-and-review-evidence.md"
        ]["sequenced_after"][0]["carried_by"]["task-agent"][
            "engineering-brief"
        ][-1] = "engineering-brief.layer3"
        cases.append(("fields are stale, incomplete", stale_field))

        empty_fields = copy.deepcopy(self.domain)
        linux = self._row(
            empty_fields, "domain_skills", "linux-desktop-platform-extension"
        )
        linux["context_admissibility"]["references"][
            "references/display-session-and-toolkit-contracts-"
            "implementation-and-review-evidence.md"
        ]["sequenced_after"][0]["carried_by"]["task-agent"][
            "engineering-brief"
        ] = []
        cases.append(("fields are stale, incomplete", empty_fields))

        missing_profile = copy.deepcopy(self.domain)
        linux = self._row(
            missing_profile, "domain_skills", "linux-desktop-platform-extension"
        )
        linux["context_admissibility"]["references"][
            "references/display-session-and-toolkit-contracts-"
            "implementation-and-review-evidence.md"
        ]["sequenced_after"][0]["carried_by"].pop("task-agent")
        cases.append(("analyzed Task and Review surfaces", missing_profile))

        nonreciprocal = copy.deepcopy(self.domain)
        linux = self._row(
            nonreciprocal, "domain_skills", "linux-desktop-platform-extension"
        )
        linux["context_admissibility"]["references"][
            "references/display-session-and-toolkit-contracts.md"
        ]["must_co_trigger_with"] = [
            "linux-desktop-platform-extension/references/"
            "server-and-system-boundaries.md"
        ]
        cases.append(("must be reciprocal", nonreciprocal))

        for message, domain in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(VALIDATION.ValidationProblem, message):
                    VALIDATION.reference_context_admissibility_authority(
                        self.professional,
                        self.foundation,
                        domain,
                        context="invalid v3 context admissibility",
                    )

    def test_desktop_companions_carry_only_their_own_active_decision(self) -> None:
        authority = self._authority()
        for domain, service in (
            ("linux-desktop-platform-extension", "server-and-system-boundaries"),
            ("windows-platform-extension", "service-background-and-notification-contracts"),
        ):
            declarations = authority["owners"][domain]["declarations"]
            suffix = "-implementation-and-review-evidence.md"
            companions = [path for path in declarations if path.endswith(suffix)]
            self.assertEqual(7, len(companions))
            for companion in companions:
                decision = companion.removesuffix(suffix) + ".md"
                for profile in ("task-agent", "review-agent"):
                    with self.subTest(domain=domain, companion=companion, profile=profile):
                        plan = VALIDATION.reference_context_staged_plan(
                            authority,
                            references=[(domain, companion)],
                            path="analyzed",
                            profile=profile,
                            selection_owner="engineering-brief",
                            available_carrier_fields=authority["carrier_fields"][profile]["engineering-brief"],
                            receipt_replayed=True,
                            brief_current=True,
                            review_fresh=True,
                        )
                        self.assertTrue(plan["reachable"])
                        self.assertEqual([[domain, companion]], plan["loaded_union"])
                        self.assertEqual([[domain, decision]], plan["carried_predecessors"])
                        if decision != f"references/{service}.md":
                            self.assertNotIn([domain, f"references/{service}.md"], plan["carried_predecessors"])

    def test_staged_plan_requires_current_carrier_and_preserves_selected_union(self) -> None:
        authority = self._authority()
        planner = getattr(VALIDATION, "reference_context_staged_plan", None)
        self.assertTrue(callable(planner), "staged Reference planner is absent")
        selected = [
            (
                "linux-desktop-platform-extension",
                "references/server-and-system-boundaries.md",
            ),
            (
                "linux-desktop-platform-extension",
                "references/display-session-and-toolkit-contracts.md",
            ),
            (
                "linux-desktop-platform-extension",
                "references/display-session-and-toolkit-contracts-"
                "implementation-and-review-evidence.md",
            ),
        ]
        stale = planner(
            authority,
            references=selected,
            path="analyzed",
            profile="task-agent",
            selection_owner="engineering-brief",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=True,
            review_fresh=True,
        )
        self.assertFalse(stale["reachable"])
        self.assertEqual("context-reference-carrier-stale", stale["failure_id"])

        current = planner(
            authority,
            references=selected,
            path="analyzed",
            profile="task-agent",
            selection_owner="engineering-brief",
            available_carrier_fields=authority["carrier_fields"]["task-agent"][
                "engineering-brief"
            ],
            receipt_replayed=True,
            brief_current=True,
            review_fresh=True,
        )
        self.assertTrue(current["reachable"])
        self.assertEqual(3, len(current["stages"]))
        self.assertEqual(
            set(selected), {tuple(item) for item in current["selected_union"]}
        )
        self.assertEqual(
            set(selected), {tuple(item) for item in current["loaded_union"]}
        )
        self.assertEqual(
            set(selected),
            {
                tuple(receipt["reference"])
                for receipt in current["required_output_receipts"]
            },
        )
        external_only = planner(
            authority,
            references=[selected[-1]],
            path="analyzed",
            profile="task-agent",
            selection_owner="engineering-brief",
            available_carrier_fields=authority["carrier_fields"]["task-agent"]
            ["engineering-brief"],
            receipt_replayed=True,
            brief_current=True,
            review_fresh=True,
        )
        self.assertTrue(external_only["reachable"])
        self.assertEqual([list(selected[-1])], external_only["loaded_union"])
        self.assertEqual(
            {selected[1]},
            {tuple(item) for item in external_only["carried_predecessors"]},
        )
        current_fields = authority["carrier_fields"]["task-agent"][
            "engineering-brief"
        ]
        for evidence_delta in (
            {"receipt_replayed": False},
            {"brief_current": False},
        ):
            arguments = {
                "receipt_replayed": True,
                "brief_current": True,
                "review_fresh": True,
                **evidence_delta,
            }
            with self.subTest(evidence_delta=evidence_delta):
                invalid = planner(
                    authority,
                    references=selected,
                    path="analyzed",
                    profile="task-agent",
                    selection_owner="engineering-brief",
                    available_carrier_fields=current_fields,
                    **arguments,
                )
                self.assertFalse(invalid["reachable"])
                self.assertEqual(
                    "context-reference-carrier-stale",
                    invalid["failure_id"],
                )

        stale_review = planner(
            authority,
            references=selected,
            path="analyzed",
            profile="review-agent",
            selection_owner="engineering-brief",
            available_carrier_fields=authority["carrier_fields"]["review-agent"][
                "engineering-brief"
            ],
            receipt_replayed=True,
            brief_current=True,
            review_fresh=False,
        )
        self.assertFalse(stale_review["reachable"])
        self.assertEqual(
            "context-reference-carrier-stale",
            stale_review["failure_id"],
        )

    def test_four_plus_references_stage_without_drop_and_missing_relations_stay_independent(self) -> None:
        authority = self._authority()
        planner = getattr(VALIDATION, "reference_context_staged_plan", None)
        self.assertTrue(callable(planner), "staged Reference planner is absent")
        selected = [
            (
                "linux-desktop-platform-extension",
                "references/server-and-system-boundaries.md",
            )
        ]
        for stem in (
            "display-session-and-toolkit-contracts",
            "dbus-portal-and-session-integration-contracts",
            "packaging-installation-and-update-contracts",
        ):
            selected.extend(
                [
                    (
                        "linux-desktop-platform-extension",
                        f"references/{stem}.md",
                    ),
                    (
                        "linux-desktop-platform-extension",
                        f"references/{stem}-implementation-and-review-evidence.md",
                    ),
                ]
            )
        result = planner(
            authority,
            references=selected,
            path="analyzed",
            profile="task-agent",
            selection_owner="engineering-brief",
            available_carrier_fields=authority["carrier_fields"]["task-agent"][
                "engineering-brief"
            ],
            receipt_replayed=True,
            brief_current=True,
            review_fresh=True,
        )
        self.assertTrue(result["reachable"])
        self.assertEqual(
            set(selected), {tuple(item) for item in result["selected_union"]}
        )
        self.assertGreaterEqual(len(result["stages"]), 2)
        self.assertTrue(
            all(len(stage["loaded_references"]) == 1 for stage in result["stages"])
        )

        missing = planner(
            authority,
            references=[
                ("backend-change-builder", "references/checklist.md"),
                ("domain-object-identification", "references/checklist.md"),
            ],
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=False,
        )
        self.assertTrue(missing["reachable"])
        self.assertEqual(2, len(missing["stages"]))
        self.assertTrue(
            all(len(stage["loaded_references"]) == 1 for stage in missing["stages"])
        )

    def test_v3_only_reciprocal_must_components_authorize_same_stage(self) -> None:
        professional = copy.deepcopy(self.professional)
        backend = self._row(
            professional, "professional_skills", "backend-change-builder"
        )
        declarations = backend["context_admissibility"]["references"]
        left = "references/backend-output-and-gates.md"
        right = "references/professional-modes.md"
        declarations[left]["must_co_trigger_with"] = [
            f"backend-change-builder/{right}"
        ]
        declarations[right]["must_co_trigger_with"] = [
            f"backend-change-builder/{left}"
        ]
        authority = self._authority(professional=professional)
        planner = VALIDATION.reference_context_staged_plan
        selected = [
            ("backend-change-builder", left),
            ("backend-change-builder", right),
        ]
        current = planner(
            authority,
            references=selected,
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=False,
            requested_same_stage=[selected],
        )
        self.assertTrue(current["reachable"])
        self.assertEqual(1, len(current["stages"]))
        self.assertEqual(
            set(selected),
            {tuple(item) for item in current["stages"][0]["loaded_references"]},
        )

        missing = planner(
            authority,
            references=[selected[0]],
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=False,
        )
        self.assertFalse(missing["reachable"])
        self.assertEqual("required-co-trigger-missing", missing["failure_id"])

    def test_v3_rejects_unauthorized_same_stage_and_old_all_ref_residency(self) -> None:
        source = (ROOT / "scripts" / "eval-rendered-context-budget.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("Registry References co-trigger by default", source)
        authority = self._authority()
        selected = [
            ("backend-change-builder", "references/backend-output-and-gates.md"),
            ("backend-change-builder", "references/professional-modes.md"),
        ]
        result = VALIDATION.reference_context_staged_plan(
            authority,
            references=selected,
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=False,
            requested_same_stage=[selected],
        )
        self.assertFalse(result["reachable"])
        self.assertEqual(
            "context-reference-simultaneity-unauthorized", result["failure_id"]
        )

    def test_v3_conflict_rejects_union_but_nearest_negative_stays_independent(self) -> None:
        authority = self._authority()
        planner = VALIDATION.reference_context_staged_plan
        common = {
            "authority": authority,
            "path": "analyzed",
            "profile": "review-agent",
            "selection_owner": "engineering-brief",
            "available_carrier_fields": authority["carrier_fields"][
                "review-agent"
            ]["engineering-brief"],
            "receipt_replayed": True,
            "brief_current": True,
            "review_fresh": True,
        }
        conflict = planner(
            references=[
                (
                    "ai-code-review-refactor",
                    "references/ai-review-pattern-catalog.md",
                ),
                ("ai-code-review-refactor", "references/checklist.md"),
            ],
            **common,
        )
        self.assertFalse(conflict["reachable"])
        self.assertEqual("context-reference-conflict", conflict["failure_id"])

        nearest_negative = planner(
            references=[
                (
                    "ai-code-review-refactor",
                    "references/ai-review-pattern-catalog.md",
                ),
                (
                    "ai-code-review-refactor",
                    "references/solution-optimality.md",
                ),
            ],
            **common,
        )
        self.assertTrue(nearest_negative["reachable"])
        self.assertEqual(2, len(nearest_negative["stages"]))
        self.assertTrue(
            all(
                len(stage["loaded_references"]) == 1
                for stage in nearest_negative["stages"]
            )
        )

    def test_platform_routing_knowledge_does_not_force_analysis(self) -> None:
        authority = self._authority()
        for owner, path in (
            (
                "linux-desktop-platform-extension",
                "references/server-and-system-boundaries.md",
            ),
            (
                "windows-platform-extension",
                "references/service-background-and-notification-contracts.md",
            ),
        ):
            with self.subTest(owner=owner):
                decision = VALIDATION.reference_context_admissibility_decisions(
                    authority,
                    references=[(owner, path)],
                    path="direct",
                )
                self.assertTrue(decision["reachable"])
        mixed = VALIDATION.reference_context_admissibility_decisions(
            authority,
            references=[
                (
                    "android-platform-extension",
                    "references/lifecycle-task-and-state-contracts.md",
                )
            ],
            path="direct",
        )
        self.assertTrue(mixed["reachable"])

    def test_platform_decisions_and_evidence_are_role_sequenced(self) -> None:
        def decision(
            output,
            *,
            predecessor=None,
            evidence_output=None,
        ):
            outputs = output if isinstance(output, list) else [output]
            return (outputs, evidence_output or outputs[-1], predecessor)

        expected = {
            "android-platform-extension": {
                "lifecycle-task-and-state-contracts": decision("decision-record"),
                "components-permissions-and-background-contracts": decision("boundary-decision"),
                "storage-and-keystore-contracts": decision("decision-record"),
                "compatibility-packaging-and-performance-contracts": decision("decision-record"),
                "jetpack-compose-contracts": decision("selected-approach"),
                "accessibility-representation-input-and-scaling": decision("decision-record"),
                "special-form-factor-boundaries": decision("boundary-decision"),
            },
            "ios-ipados-platform-extension": {
                "lifecycle-scenes-and-background-contracts": decision("decision-record"),
                "entry-capabilities-and-entitlements-contracts": decision("boundary-decision"),
                "data-keychain-and-extension-contracts": decision("decision-record"),
                "ui-form-factor-and-accessibility-contracts": decision("selected-approach"),
                "compatibility-signing-and-distribution-contracts": decision("decision-record"),
                "special-platform-boundaries": decision("boundary-decision"),
            },
            "linux-desktop-platform-extension": {
                "display-session-and-toolkit-contracts": decision("boundary-decision"),
                "dbus-portal-and-session-integration-contracts": decision("decision-record"),
                "desktop-entry-mime-and-keyring-contracts": decision("boundary-decision"),
                "packaging-installation-and-update-contracts": decision("selected-approach"),
                "desktop-environment-input-and-localization-contracts": decision("decision-record"),
                "accessibility-platform-deltas": decision("decision-record"),
                "server-and-system-boundaries": decision(["routing-decision", "boundary-decision"], evidence_output="boundary-decision"),
            },
            "macos-platform-extension": {
                "framework-lifecycle-window-and-document-contracts": decision("selected-approach"),
                "file-sandbox-and-entitlement-contracts": decision("boundary-decision"),
                "keychain-xpc-and-helper-contracts": decision("decision-record"),
                "signing-notarization-and-distribution-contracts": decision("decision-record"),
                "architecture-and-update-contracts": decision("boundary-decision"),
                "accessibility-platform-deltas": decision("decision-record"),
            },
            "windows-platform-extension": {
                "framework-lifecycle-and-activation-contracts": decision("selected-approach"),
                "identity-packaging-and-installation-contracts": decision("boundary-decision"),
                "os-integration-and-registration-contracts": decision("decision-record"),
                "security-ipc-and-loading-contracts": decision("boundary-decision"),
                "architecture-signing-and-distribution-contracts": decision("decision-record"),
                "dpi-and-accessibility-deltas": decision("decision-record"),
                "service-background-and-notification-contracts": decision(["routing-decision", "failure-decision"], evidence_output="failure-decision"),
            },
        }
        authority = self._authority()
        for owner, decisions in expected.items():
            registry_row = self._row(self.domain, "domain_skills", owner)
            contracts = {
                contract["path"]: contract
                for contract in VALIDATION.reference_contracts(
                    registry_row["reference_index"],
                    f"focused {owner} reference index",
                    owner=owner,
                )
            }
            declarations = authority["owners"][owner]["declarations"]
            source_root = ROOT / registry_row["path"]
            for stem, (
                decision_outputs,
                evidence_output,
                predecessor,
            ) in decisions.items():
                decision_path = f"references/{stem}.md"
                evidence_path = (
                    f"references/{stem}-implementation-and-review-evidence.md"
                )
                with self.subTest(owner=owner, stem=stem):
                    self.assertTrue((source_root / evidence_path).is_file())
                    self.assertEqual(
                        ["analysis-agent"], contracts[decision_path]["required_by"]
                    )
                    self.assertEqual(
                        decision_outputs, contracts[decision_path]["required_output"]
                    )
                    self.assertEqual(
                        ["task-agent", "review-agent"],
                        contracts[evidence_path]["required_by"],
                    )
                    self.assertEqual(stem, declarations[decision_path]["decision_problem"])
                    evidence_rule = declarations[evidence_path]
                    self.assertEqual([], evidence_rule["conflicts_with"])
                    self.assertEqual([], evidence_rule["must_co_trigger_with"])
                    expected_sequence = [
                        {
                            "reference": f"{owner}/{decision_path}",
                            "required_output": evidence_output,
                            "carried_by": authority["carrier_fields"],
                        }
                    ]
                    if predecessor is not None:
                        predecessor_stem, predecessor_output = predecessor
                        expected_sequence.append(
                            {
                                "reference": (
                                    f"{owner}/references/{predecessor_stem}.md"
                                ),
                                "required_output": predecessor_output,
                                "carried_by": authority["carrier_fields"],
                            }
                        )
                    self.assertEqual(expected_sequence, evidence_rule["sequenced_after"])

    def test_cross_role_carrier_rejects_reverse_or_stale_delivery(self) -> None:
        owner = "ios-ipados-platform-extension"
        decision_path = "references/lifecycle-scenes-and-background-contracts.md"
        evidence_path = (
            "references/lifecycle-scenes-and-background-contracts-"
            "implementation-and-review-evidence.md"
        )

        def row(document):
            return self._row(document, "domain_skills", owner)

        def sequence(document):
            return row(document)["context_admissibility"]["references"][
                evidence_path
            ]["sequenced_after"][0]

        cases = []

        wrong_owner = copy.deepcopy(self.domain)
        carried = sequence(wrong_owner)["carried_by"]["task-agent"]
        carried["main-control-agent"] = carried.pop("engineering-brief")
        cases.append(("engineering-brief selection owner", wrong_owner))

        wrong_profile = copy.deepcopy(self.domain)
        carried = sequence(wrong_profile)["carried_by"]
        carried["analysis-agent"] = carried.pop("task-agent")
        cases.append(("analyzed Task and Review surfaces", wrong_profile))

        missing_brief = copy.deepcopy(self.domain)
        sequence(missing_brief)["carried_by"]["task-agent"][
            "engineering-brief"
        ].remove("engineering-brief.Key Decisions")
        cases.append(("stale, incomplete", missing_brief))

        stale_receipt = copy.deepcopy(self.domain)
        sequence(stale_receipt)["carried_by"]["task-agent"][
            "engineering-brief"
        ][0] = "selector-receipt.invented"
        cases.append(("stale, incomplete", stale_receipt))

        reverse_review_to_task = copy.deepcopy(self.domain)
        decision_contract = next(
            contract
            for contract in row(reverse_review_to_task)["reference_index"]
            if contract["path"] == decision_path
        )
        decision_contract["required_by"] = ["review-agent"]
        cases.append(("forward role flow", reverse_review_to_task))

        task_to_analysis = copy.deepcopy(self.domain)
        evidence_contract = next(
            contract
            for contract in row(task_to_analysis)["reference_index"]
            if contract["path"] == evidence_path
        )
        evidence_contract["required_by"] = ["analysis-agent"]
        cases.append(("forward role flow", task_to_analysis))

        for message, document in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(VALIDATION.ValidationProblem, message):
                    VALIDATION.reference_context_admissibility_authority(
                        self.professional,
                        self.foundation,
                        document,
                        context="invalid cross-role carrier",
                    )

    def test_platform_family_pairs_remain_simultaneously_reachable(self) -> None:
        authority = self._authority()
        envelopes = {
            "ios-lifecycle-entry-data": [
                (
                    "ios-ipados-platform-extension",
                    "references/lifecycle-scenes-and-background-contracts.md",
                ),
                (
                    "ios-ipados-platform-extension",
                    "references/entry-capabilities-and-entitlements-contracts.md",
                ),
                (
                    "ios-ipados-platform-extension",
                    "references/data-keychain-and-extension-contracts.md",
                ),
            ],
            "macos-file-helper-signing": [
                (
                    "macos-platform-extension",
                    "references/file-sandbox-and-entitlement-contracts.md",
                ),
                (
                    "macos-platform-extension",
                    "references/keychain-xpc-and-helper-contracts.md",
                ),
                (
                    "macos-platform-extension",
                    "references/signing-notarization-and-distribution-contracts.md",
                ),
            ],
            "shared-client-lifecycle": [
                (
                    "android-platform-extension",
                    "references/lifecycle-task-and-state-contracts.md",
                ),
                (
                    "ios-ipados-platform-extension",
                    "references/lifecycle-scenes-and-background-contracts.md",
                ),
                (
                    "macos-platform-extension",
                    "references/framework-lifecycle-window-and-document-contracts.md",
                ),
            ],
        }
        for name, references in envelopes.items():
            with self.subTest(name=name):
                decision = VALIDATION.reference_context_admissibility_decisions(
                    authority,
                    references=references,
                    path="analyzed",
                )
                self.assertTrue(decision["reachable"])
                self.assertEqual([], decision["conflicts"])
                self.assertEqual(len(references), len(decision["declarations"]))
                for owner, path in references:
                    rule = authority["owners"][owner]["declarations"][path]
                    self.assertEqual([], rule["must_co_trigger_with"])

    def test_c1_framework_and_language_references_stage_independently(self) -> None:
        authority = self._authority()
        framework_paths = [
            f"references/{stem}-framework-contracts.md"
            for stem in (
                "flutter",
                "react-native",
                "electron",
                "tauri",
                "qt",
                "dotnet-maui",
                "kotlin-multiplatform",
            )
        ]
        selected = [
            ("installed-client-change-builder", path)
            for path in framework_paths
        ]
        language_paths = {
            "csharp-dotnet-professional-usage": (
                "references/async-resource-and-iterator-contracts.md",
                "references/runtime-deployment-and-interop-contracts.md",
            ),
            "kotlin-professional-usage": (
                "references/coroutine-flow-state-contracts.md",
                "references/type-interop-and-dsl-contracts.md",
            ),
            "swift-professional-usage": (
                "references/value-memory-and-type-contracts.md",
                "references/concurrency-interop-and-ui-contracts.md",
            ),
        }
        selected.extend(
            (owner, path)
            for owner, paths in language_paths.items()
            for path in paths
        )
        plan = VALIDATION.reference_context_staged_plan(
            authority,
            references=selected,
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=False,
        )
        self.assertTrue(plan["reachable"])
        self.assertEqual(set(selected), {tuple(item) for item in plan["selected_union"]})
        self.assertEqual(set(selected), {tuple(item) for item in plan["loaded_union"]})
        self.assertEqual(len(selected), len(plan["stages"]))
        self.assertTrue(all(len(stage["loaded_references"]) == 1 for stage in plan["stages"]))
        self.assertEqual(len(selected), len(plan["required_output_receipts"]))

        missing = copy.deepcopy(self.professional)
        installed = self._row(missing, "professional_skills", "installed-client-change-builder")
        installed["context_admissibility"]["references"].pop(framework_paths[0])
        indexed = {row["path"] for row in installed["reference_index"]}
        declared = set(installed["context_admissibility"]["references"])
        self.assertEqual({framework_paths[0]}, indexed - declared)
        self.assertNotEqual(indexed, declared)

        accidental = copy.deepcopy(self.professional)
        installed = self._row(accidental, "professional_skills", "installed-client-change-builder")
        installed["context_admissibility"]["references"][framework_paths[0]]["must_co_trigger_with"] = [
            f"installed-client-change-builder/{framework_paths[1]}"
        ]
        with self.assertRaises(VALIDATION.ValidationProblem):
            self._authority(professional=accidental)


if __name__ == "__main__":
    unittest.main()
