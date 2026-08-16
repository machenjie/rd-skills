from __future__ import annotations

import copy
import importlib.util
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_control_plane_prompt_test_target",
        SCRIPTS / "validate-control-plane-prompt.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load validate-control-plane-prompt.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALIDATOR = _load_validator()


class ControlPromptProjectionTests(unittest.TestCase):
    def _remove_term(self, text: str, term: str) -> str:
        mutated, count = re.subn(
            re.escape(term),
            "REMOVED_CANONICAL_TERM",
            text,
            flags=re.IGNORECASE,
        )
        self.assertGreater(count, 0, term)
        return mutated

    def test_managed_blocks_and_document_digest_match_exactly(self) -> None:
        raw = VALIDATOR.PROMPT.read_bytes()
        text = raw.decode("utf-8")

        self.assertEqual(
            [],
            VALIDATOR.prompt_projection_errors(
                text,
                VALIDATOR.CORE_CONTRACTS,
                document_bytes=raw,
            ),
        )

    def test_prompt_has_no_readability_findings(self) -> None:
        text = VALIDATOR.PROMPT.read_text(encoding="utf-8")
        errors: list[str] = []

        findings = VALIDATOR.validate_ai_readability(text, "prompt", errors)

        self.assertEqual([], errors)
        self.assertEqual([], findings)

    def test_prompt_source_stays_within_context_budget(self) -> None:
        text = VALIDATOR.PROMPT.read_text(encoding="utf-8")

        self.assertLessEqual(
            VALIDATOR.count_o200k_base_tokens(text),
            min(1415, VALIDATOR.PROMPT_MAX_O200K_BASE_TOKENS),
        )

    def test_main_business_execution_and_permission_gates_are_projected(
        self,
    ) -> None:
        text = VALIDATOR.PROMPT.read_text(encoding="utf-8")
        authorization = VALIDATOR.extract_section_body(text, "Authorization") or ""
        expected_by_concept = {
            "dispatch-only-boundary": ("execute business commands",),
            "bounded-delegation-authorization": (
                "permission required",
                "scope expansion",
                "destructive/production action",
                "elevation",
                "irreversible/material data change",
                "unsupported choice",
            ),
        }
        concepts = {
            item["id"]: item
            for item in VALIDATOR.PROMPT_CONTRACT_MODEL["concepts"]
        }

        self.assertIn("execute business commands", text.casefold())
        for term in expected_by_concept["bounded-delegation-authorization"]:
            with self.subTest(surface_term=term):
                self.assertIn(term.casefold(), authorization.casefold())
        for concept_id, terms in expected_by_concept.items():
            with self.subTest(concept_id=concept_id):
                self.assertTrue(
                    set(terms).issubset(concepts[concept_id]["required_terms"]),
                    concepts[concept_id],
                )

    def test_main_business_execution_and_permission_gate_mutations_fail(
        self,
    ) -> None:
        text = VALIDATOR.PROMPT.read_text(encoding="utf-8")
        mutations = {
            "dispatch-only-boundary": ("execute business commands",),
            "bounded-delegation-authorization": (
                "permission required",
                "scope expansion",
                "destructive/production action",
                "elevation",
                "irreversible/material data change",
                "unsupported choice",
            ),
        }

        for concept_id, terms in mutations.items():
            for term in terms:
                with self.subTest(concept_id=concept_id, term=term):
                    errors: list[str] = []
                    VALIDATOR._validate_concepts(
                        self._remove_term(text, term),
                        errors,
                    )
                    self.assertTrue(
                        any(concept_id in error for error in errors),
                        errors,
                    )

    def test_analyzed_work_authority_and_scheduling_priority_are_projected(self) -> None:
        text = VALIDATOR.PROMPT.read_text(encoding="utf-8")
        analyzed = VALIDATOR.extract_section_body(text, "Analyzed Work") or ""
        scheduling = VALIDATOR.extract_section_body(text, "Scheduling and Context") or ""

        for term in (
            "current Engineering Brief is the only operational analysis authority",
            "dispatch its First Executable Slice verbatim",
            "never regenerate or reinterpret",
            "blocked -> main-control-agent -> analysis-agent -> updated Engineering Brief",
            "redispatch affected tasks",
        ):
            with self.subTest(term=term):
                self.assertIn(term.casefold(), analyzed.casefold())
        self.assertIn(
            "current requested task > declared DAG work > current-task blockers > adjacent follow-up",
            scheduling,
        )
        self.assertIn("Adjacent findings never preempt", scheduling)

    def test_each_analyzed_work_authority_term_has_a_negative_control(self) -> None:
        text = VALIDATOR.PROMPT.read_text(encoding="utf-8")
        for section, terms in VALIDATOR.ANALYZED_WORK_PROMPT_TERMS.items():
            for term in terms:
                with self.subTest(section=section, term=term):
                    errors: list[str] = []
                    VALIDATOR._validate_analyzed_work_authority(
                        self._remove_term(text, term),
                        errors,
                    )
                    self.assertTrue(
                        any("analyzed-work authority term" in error for error in errors),
                        errors,
                    )

    def test_managed_block_and_digest_mutations_fail(self) -> None:
        text = VALIDATOR.PROMPT.read_text(encoding="utf-8")
        mutation = text.replace("State: current", "State: stale", 1)
        self.assertNotEqual(text, mutation)

        errors = VALIDATOR.prompt_projection_errors(
            mutation,
            VALIDATOR.CORE_CONTRACTS,
        )

        self.assertTrue(any("exact Core Model rendering" in error for error in errors))
        self.assertTrue(any("whole-document SHA-256" in error for error in errors))

    def test_duplicate_managed_marker_fails(self) -> None:
        text = VALIDATOR.PROMPT.read_text(encoding="utf-8")
        marker = (
            "<!-- review-evidence-contract:B -->"
        )
        mutation = text.replace(marker, marker + "\n" + marker, 1)

        errors = VALIDATOR.prompt_projection_errors(
            mutation,
            VALIDATOR.CORE_CONTRACTS,
        )

        self.assertTrue(any("markers must each appear exactly once" in error for error in errors))

    def test_renderer_uses_template_authority_without_copying_evidence_fields(self) -> None:
        model = copy.deepcopy(VALIDATOR.CORE_CONTRACTS)
        fields = model["visible_evidence_contract"]["fields"]
        self.assertEqual(
            [
                "Claim",
                "Owner",
                "Artifact",
                "Command",
                "Result",
                "Freshness",
                "Scope",
                "Proof Limit",
                "State",
            ],
            fields,
        )
        fields[fields.index("State")] = "Evidence Phase"
        model["visible_evidence_contract"]["states"] = [
            "fresh",
            "replaced",
            "rejected",
        ]
        projections = {
            item["id"]: VALIDATOR.prompt_projection_block(model, item)
            for item in model["prompt_contract"]["managed_projections"]
        }

        self.assertNotIn("Evidence Phase", projections["review-evidence-contract"])
        self.assertIn("schema authority", projections["review-evidence-contract"])
        self.assertIn(
            "State: fresh, replaced, rejected",
            projections["review-evidence-contract"],
        )
        self.assertNotIn("Assignment initial", projections["closure-contract"])

    def test_missing_prompt_authoritative_template_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            reference_root = Path(raw) / "references"
            shutil.copytree(VALIDATOR.REFERENCE_ROOT, reference_root)
            (reference_root / "direct-task-template.md").unlink()
            errors: list[str] = []

            VALIDATOR._validate_template_bindings(reference_root, errors)

            self.assertTrue(
                any("missing Prompt-authoritative template" in error for error in errors),
                errors,
            )

    def test_prompt_authoritative_template_field_drift_fails_closed(self) -> None:
        mutations = (
            ("direct-task-template.md", "## Goal", "## Objective"),
            (
                "implementation-handoff-template.md",
                "| Claim | Owner | Artifact | Command | Result | Freshness | Scope | Proof Limit | State |",
                "| Evidence Key | Owner | Artifact | Command | Result | Freshness | Scope | Proof Limit | State |",
            ),
        )
        for name, old, new in mutations:
            with self.subTest(template=name), tempfile.TemporaryDirectory() as raw:
                reference_root = Path(raw) / "references"
                shutil.copytree(VALIDATOR.REFERENCE_ROOT, reference_root)
                path = reference_root / name
                text = path.read_text(encoding="utf-8")
                self.assertIn(old, text)
                path.write_text(text.replace(old, new, 1), encoding="utf-8")
                errors: list[str] = []

                VALIDATOR._validate_template_bindings(reference_root, errors)

                self.assertTrue(
                    any("drifted from the authoritative schema" in error for error in errors),
                    errors,
                )

    def test_prompt_authoritative_template_required_by_role_drift_fails_closed(
        self,
    ) -> None:
        mutations = (
            ("direct-task-template.md", ["analysis-agent"]),
            ("implementation-handoff-template.md", ["review-agent"]),
        )
        for name, wrong_roles in mutations:
            with self.subTest(template=name):
                model = copy.deepcopy(VALIDATOR.REFERENCE_CONTRACT_MODEL)
                model["control_required_by"][f"references/{name}"] = wrong_roles
                errors: list[str] = []

                with mock.patch.object(
                    VALIDATOR,
                    "REFERENCE_CONTRACT_MODEL",
                    model,
                ):
                    VALIDATOR._validate_template_bindings(
                        VALIDATOR.REFERENCE_ROOT,
                        errors,
                    )

                self.assertTrue(
                    any(
                        f"{name}: required_by roles drifted" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_prompt_authoritative_template_extra_required_by_role_fails_closed(
        self,
    ) -> None:
        mutations = (
            ("direct-task-template.md", "analysis-agent"),
            ("implementation-handoff-template.md", "review-agent"),
        )
        for name, extra_role in mutations:
            with self.subTest(template=name):
                model = copy.deepcopy(VALIDATOR.REFERENCE_CONTRACT_MODEL)
                model["control_required_by"][f"references/{name}"].append(
                    extra_role
                )
                errors: list[str] = []

                with mock.patch.object(
                    VALIDATOR,
                    "REFERENCE_CONTRACT_MODEL",
                    model,
                ):
                    VALIDATOR._validate_template_bindings(
                        VALIDATOR.REFERENCE_ROOT,
                        errors,
                    )

                self.assertTrue(
                    any(
                        f"{name}: required_by roles drifted" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_prompt_authoritative_template_missing_required_by_entry_fails_closed(
        self,
    ) -> None:
        for name, _expected_roles in VALIDATOR.PROMPT_TEMPLATE_BINDINGS:
            with self.subTest(template=name):
                model = copy.deepcopy(VALIDATOR.REFERENCE_CONTRACT_MODEL)
                del model["control_required_by"][f"references/{name}"]
                errors: list[str] = []

                with mock.patch.object(
                    VALIDATOR,
                    "REFERENCE_CONTRACT_MODEL",
                    model,
                ):
                    VALIDATOR._validate_template_bindings(
                        VALIDATOR.REFERENCE_ROOT,
                        errors,
                    )

                self.assertTrue(
                    any(
                        f"{name}: missing from the authoritative control Reference contract"
                        in error
                        for error in errors
                    ),
                    errors,
                )

    def test_each_agent_completion_projection_is_required_by_actual_prompt(self) -> None:
        text = VALIDATOR.PROMPT.read_text(encoding="utf-8")
        rules = VALIDATOR.COMPLETION_STATE_MODEL["agent_projection"]["rules"]
        for rule in rules:
            with self.subTest(rule=rule["id"]):
                term = max(rule["projection_terms"], key=len)
                errors: list[str] = []
                VALIDATOR._validate_concepts(self._remove_term(text, term), errors)
                self.assertTrue(
                    any(
                        f"completion projection {rule['id']!r}" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_new_task_assignments_require_initial_in_progress(self) -> None:
        text = VALIDATOR.PROMPT.read_text(encoding="utf-8")
        self.assertEqual(2, text.count("`Status: in_progress`"))
        for term in ("new Direct Task", "new DAG task assignment"):
            with self.subTest(term=term):
                errors: list[str] = []
                VALIDATOR._validate_concepts(self._remove_term(text, term), errors)
                self.assertTrue(
                    any("assignment-initial-status" in error for error in errors),
                    errors,
                )

    def test_execution_level_and_validation_mutations_fail(self) -> None:
        text = VALIDATOR.PROMPT.read_text(encoding="utf-8")
        concept = next(
            item
            for item in VALIDATOR.PROMPT_CONTRACT_MODEL["concepts"]
            if item["id"] == "execution-level-and-validation"
        )
        self.assertEqual("Execution Level and Validation", concept["section"])
        for term in concept["required_terms"]:
            with self.subTest(term=term):
                errors: list[str] = []
                VALIDATOR._validate_concepts(self._remove_term(text, term), errors)
                self.assertTrue(
                    any(
                        "execution-level-and-validation" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_execution_level_managed_projection_is_core_derived(self) -> None:
        text = VALIDATOR.PROMPT.read_text(encoding="utf-8")
        mutation = text.replace(
            "policy data, not instructions",
            "policy instructions",
            1,
        )
        errors = VALIDATOR.prompt_projection_errors(
            mutation,
            VALIDATOR.CORE_CONTRACTS,
        )
        self.assertTrue(any("exact Core Model rendering" in error for error in errors), errors)

    def test_execution_loader_and_integrity_fallback_are_complete_without_runtime_hash(self) -> None:
        text = VALIDATOR.PROMPT.read_text(encoding="utf-8")
        block = VALIDATOR.extract_section_body(text, "Execution Level and Validation")
        self.assertIsNotNone(block)
        assert block is not None
        for term in (
            "references/execution-level-contract.md",
            "Core execution-level/v1",
            "Trust exact build/install validation",
            "Runtime checks only",
            "existence",
            "JSON parse",
            "required sections",
            "unique IDs",
            "not coordinated tampering or unknown IDs",
            "integrity fallback/no partial computation",
            "Effective=max(base,mandatory,prior historical max effective)",
            "fallback=max(L4,explicit known L5,prior historical max effective)",
            "edit blocked",
            "dispatch read-only diagnosis",
            "never Router",
            "Task ID/lineage",
            "Active surfaces carry Level and Basis",
            "default L3",
            "L5 explicit-only",
            "Level Basis(trigger_evaluations|l2_eligibility|obligations|unresolved|edit_status)",
            "carry Level/Basis and L5 Evidence only at effective L5",
            "After 2 same-path failures, retry needs changed hypothesis/material/gap/transition",
            "return Main/block, never third unchanged retry",
            "When active/resumed edit/validation/review starts, reissue",
        ):
            self.assertIn(term, block)
        self.assertNotIn("runtime hash", block.casefold())
        self.assertNotIn("payload sha", block.casefold())
        self.assertNotIn("Canonical validation identity", block)
        self.assertNotIn("Validation Identity Manifest", block)

    def test_prompt_runtime_loader_does_not_claim_exact_ids_or_no_extras(self) -> None:
        text = VALIDATOR.PROMPT.read_text(encoding="utf-8")
        block = VALIDATOR.extract_section_body(text, "Execution Level and Validation")
        self.assertIsNotNone(block)
        assert block is not None
        self.assertNotIn("exact unique trigger/L2 IDs", block)
        self.assertNotIn("no extras", block)

    def test_runtime_reference_missing_or_drifted_is_rejected_by_prompt_validator(self) -> None:
        runtime = VALIDATOR.REFERENCE_ROOT / "execution-level-contract.md"
        text = runtime.read_text(encoding="utf-8")
        self.assertEqual([], VALIDATOR.execution_level_runtime_reference_errors(text))
        self.assertTrue(
            VALIDATOR.execution_level_runtime_reference_errors(
                text.replace('"default_level":"L3"', '"default_level":"L2"', 1)
            )
        )

    def test_answer_routing_diagnosis_and_preimplementation_review_exceptions_are_core_bound(
        self,
    ) -> None:
        text = VALIDATOR.PROMPT.read_text(encoding="utf-8")
        concept_ids = {
            "source-free-answer-boundary",
            "source-backed-answer-diagnosis-boundary",
            "preimplementation-artifact-review",
        }
        concepts = [
            item
            for item in VALIDATOR.PROMPT_CONTRACT_MODEL["concepts"]
            if item["id"] in concept_ids
        ]
        self.assertEqual(concept_ids, {item["id"] for item in concepts})
        for concept in concepts:
            for term in concept["required_terms"]:
                with self.subTest(concept=concept["id"], term=term):
                    errors: list[str] = []
                    VALIDATOR._validate_concepts(self._remove_term(text, term), errors)
                    self.assertTrue(
                        any(concept["id"] in error for error in errors),
                        errors,
                    )

    def test_each_completed_rule_is_required_by_actual_prompt(self) -> None:
        text = VALIDATOR.PROMPT.read_text(encoding="utf-8")
        for rule in VALIDATOR.COMPLETION_STATE_MODEL["completed_rules"]:
            with self.subTest(rule=rule["id"]):
                term = VALIDATOR._completion_rule_text(rule)
                errors: list[str] = []
                VALIDATOR._validate_concepts(self._remove_term(text, term), errors)
                self.assertTrue(
                    any(f"completed rule {rule['id']!r}" in error for error in errors),
                    errors,
                )

    def test_each_prompt_freshness_projection_is_required(self) -> None:
        text = VALIDATOR.PROMPT.read_text(encoding="utf-8")
        for rule in VALIDATOR.EVIDENCE_LEDGER_MODEL["freshness_rules"]:
            if not any(target.startswith("prompt:") for target in rule["projection_targets"]):
                continue
            with self.subTest(rule=rule["id"]):
                term = max(rule["projection_terms"], key=len)
                errors: list[str] = []
                VALIDATOR._validate_concepts(self._remove_term(text, term), errors)
                self.assertTrue(
                    any(f"freshness rule {rule['id']!r}" in error for error in errors),
                    errors,
                )

    def test_each_same_task_transition_edge_is_required(self) -> None:
        text = VALIDATOR.PROMPT.read_text(encoding="utf-8")
        transitions = VALIDATOR.COMPLETION_STATE_MODEL["allowed_transitions"]
        for source, targets in transitions.items():
            for target in targets:
                with self.subTest(source=source, target=target):
                    old = f"{source} -> {' | '.join(targets)}"
                    remaining = [item for item in targets if item != target]
                    new = f"{source} -> {' | '.join(remaining)}"
                    self.assertEqual(1, text.count(old))
                    errors: list[str] = []
                    VALIDATOR._validate_concepts(text.replace(old, new, 1), errors)
                    self.assertTrue(
                        any("transition matrix must be exactly" in error for error in errors),
                        errors,
                    )

    def test_same_task_transition_addition_and_change_are_rejected(self) -> None:
        text = VALIDATOR.PROMPT.read_text(encoding="utf-8")
        group = "in_progress -> blocked | partial | completed"
        mutations = (
            group + " | in_progress",
            "in_progress -> in_progress | partial | completed",
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                errors: list[str] = []
                VALIDATOR._validate_concepts(text.replace(group, mutation, 1), errors)
                self.assertTrue(
                    any("transition matrix must be exactly" in error for error in errors),
                    errors,
                )

    def test_each_fail_closed_outcome_is_exact(self) -> None:
        text = VALIDATOR.PROMPT.read_text(encoding="utf-8")
        rules = VALIDATOR.COMPLETION_STATE_MODEL["fail_closed_rules"]
        for rule_id, targets in rules.items():
            canonical = f"{rule_id} -> {' | '.join(targets)}"
            self.assertEqual(1, text.count(canonical))
            mutations = (
                canonical.replace(targets[0], "completed", 1),
                canonical + " | completed",
            )
            for mutation in mutations:
                with self.subTest(rule=rule_id, mutation=mutation):
                    errors: list[str] = []
                    VALIDATOR._validate_concepts(
                        text.replace(canonical, mutation, 1), errors
                    )
                    self.assertTrue(
                        any("fail-closed outcome" in error for error in errors),
                        errors,
                    )

    def test_each_prompt_forbidden_storage_projection_is_required(self) -> None:
        text = VALIDATOR.PROMPT.read_text(encoding="utf-8")
        for rule in VALIDATOR.EVIDENCE_LEDGER_MODEL["forbidden_storage"]:
            with self.subTest(rule=rule["id"]):
                term = rule["projection_terms"][0]
                errors: list[str] = []
                VALIDATOR._validate_concepts(self._remove_term(text, term), errors)
                self.assertTrue(
                    any(f"forbidden storage rule {rule['id']!r}" in error for error in errors),
                    errors,
                )

    def test_each_independent_review_evidence_term_is_required(self) -> None:
        text = VALIDATOR.PROMPT.read_text(encoding="utf-8")
        proof = VALIDATOR.EVIDENCE_LEDGER_MODEL["completion_proof"][
            "implementation"
        ]
        projection = next(
            item
            for item in proof["projections"]
            if item["target"].startswith("prompt:")
        )
        for term in projection["terms"]:
            with self.subTest(term=term):
                errors: list[str] = []
                VALIDATOR._validate_concepts(self._remove_term(text, term), errors)
                self.assertTrue(
                    any("independent review evidence proof" in error for error in errors),
                    errors,
                )


class ControlPromptHeadingTests(unittest.TestCase):
    def test_heading_swap_duplicate_and_h1_change_are_rejected(self) -> None:
        text = VALIDATOR.PROMPT.read_text(encoding="utf-8")
        mutations = (
            text.replace(
                "## Authorization\n",
                "## __SWAP__\n",
                1,
            ).replace(
                "## Choose Exactly One Path\n",
                "## Authorization\n",
                1,
            ).replace("## __SWAP__\n", "## Choose Exactly One Path\n", 1),
            text.replace("## Authorization\n", "## Authorization\n\n## Authorization\n", 1),
            text.replace("# Main Control Agent\n", "# Main Control Plane\n", 1),
        )
        for mutation in mutations:
            with self.subTest():
                errors: list[str] = []
                VALIDATOR._validate_heading_structure(mutation, errors)
                self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
