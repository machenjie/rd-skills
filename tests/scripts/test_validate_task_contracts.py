from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
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

import validation_utils as VALIDATION_UTILS  # noqa: E402
from fixture_capsule_contract import (  # noqa: E402
    FixtureCapsuleError,
    canonical_capsule_sha256,
    completion_claim_errors,
    completion_transition_errors,
    decode_public_task_extension,
    encode_public_task_extension,
    evidence_ledger_errors,
    execution_level_migration_errors,
    render_fixture_capsule_payload,
    trace_execution_level_migration_errors,
)
from validation_utils import (  # noqa: E402
    COMPLETION_STATE_MODEL,
    CORE_CONTRACTS,
    ExecutionLevelError,
    compute_execution_level,
    count_o200k_base_tokens,
    execution_level_integrity_fallback,
    execution_level_runtime_payload,
    execution_level_runtime_payload_bytes,
    execution_level_runtime_payload_sha256,
    execution_level_runtime_reference,
    execution_level_runtime_reference_errors,
    execution_scope_transition_errors,
    public_execution_template_block,
    validate_core_contracts,
    execution_level_router_block,
)


def _load_validator():
    spec = importlib.util.spec_from_file_location(
        "task_contract_validator_tests",
        SCRIPTS / "validate-task-contracts.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALIDATOR = _load_validator()
REFERENCE_ROOT = (
    ROOT / "src" / "control-skills" / "engineering-control-plane" / "references"
)
AGENT_LIGHT_CASES = ROOT / "evals" / "agent-light-trajectories" / "cases.yaml"
CONDITIONAL_TEST_EVIDENCE_TARGETS = (
    "direct-task-template.md",
    "engineering-brief-template.md",
    "task-dag-template.md",
    "implementation-handoff-template.md",
    "review-handoff-template.md",
)
CONDITIONAL_TEST_EVIDENCE_PROJECTION = (
    "Record one `test-approach-selected` Claim for each normal behavior batch with "
    "its Guard G approach, reason, oracle, evidence, and proof boundary. Record "
    "current `red-proof` and `green-proof` only when applicable, with current proof "
    "after the final material edit; they are evidence, not a separate stage. Never "
    "fabricate unavailable proof."
)


def _execution_evidence(
    *,
    matched_trigger: str | None = None,
    unknown_trigger: str | None = None,
    l2_status: str = "true",
) -> tuple[dict[str, dict[str, object]], dict[str, dict[str, object]]]:
    triggers = {
        row["id"]: {
            "status": (
                "matched"
                if row["id"] == matched_trigger
                else "unknown"
                if row["id"] == unknown_trigger
                else "not_matched"
            ),
            "evidence_kind": "analysis_handoff",
            "source_anchor": f"handoff:{row['id']}",
            "plausible_critical": row["id"] == unknown_trigger,
        }
        for row in CORE_CONTRACTS["execution_level_contract"]["trigger_registry"]
    }
    l2 = {
        row["id"]: {
            "status": l2_status,
            "evidence_kind": "analysis_handoff",
            "source_anchor": f"handoff:{row['id']}",
        }
        for row in CORE_CONTRACTS["execution_level_contract"]["l2_eligibility"]
    }
    return triggers, l2


def _first_fixture_step(contract_type: str) -> dict[str, object]:
    document = json.loads(AGENT_LIGHT_CASES.read_text(encoding="utf-8"))
    return next(
        step
        for case in document["cases"]
        for step in case["steps"]
        if step.get("fixture_capsule", {}).get("contract_type") == contract_type
    )


def _recompute_fixture_extension(extension: dict[str, object]) -> dict[str, object]:
    value = copy.deepcopy(extension)
    basis = value["level_basis"]
    assert isinstance(basis, dict)
    triggers = {
        row["id"]: {key: item for key, item in row.items() if key != "id"}
        for row in basis["trigger_evaluations"]
    }
    l2 = {
        row["id"]: {key: item for key, item in row.items() if key != "id"}
        for row in basis["l2_eligibility"]
    }
    result = compute_execution_level(
        requested=value["requested_level"],
        trigger_evaluations=triggers,
        l2_evaluations=l2,
        prior_historical_max_floor=value["prior_historical_max_floor"],
        prior_historical_max_effective=value["prior_historical_max_effective"],
    )
    value["computed_floor"] = result["computed_floor"]
    value["mandatory_floor"] = result["mandatory_floor"]
    value["automatic_level"] = result["automatic_level"]
    value["effective_level"] = result["effective_level"]
    value["level_basis"] = result["level_basis"]
    value["historical_max_floor"] = result["next_historical_floor"]
    value["historical_max_effective"] = result["next_historical_effective"]
    return value


class TaskContractTemplateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name) / "references"
        shutil.copytree(REFERENCE_ROOT, self.root)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _mutate(self, name: str, old: str, new: str, *, count: int = 1) -> list[str]:
        path = self.root / name
        text = path.read_text(encoding="utf-8")
        self.assertGreaterEqual(text.count(old), count, (name, old))
        path.write_text(text.replace(old, new, count), encoding="utf-8")
        errors = VALIDATOR.validate_contracts(self.root)
        self.assertTrue(errors, name)
        return errors

    def _mutate_normalized_term(self, name: str, term: str) -> list[str]:
        path = self.root / name
        text = path.read_text(encoding="utf-8")
        pattern = r"\s+".join(re.escape(part) for part in term.split())
        mutated, count = re.subn(
            pattern,
            "REMOVED_ANALYZED_WORK_AUTHORITY_TERM",
            text,
            count=1,
            flags=re.IGNORECASE,
        )
        self.assertEqual(1, count, (name, term))
        path.write_text(mutated, encoding="utf-8")
        errors = VALIDATOR.validate_contracts(self.root)
        self.assertTrue(errors, name)
        return errors

    def test_canonical_templates_pass(self) -> None:
        self.assertEqual([], VALIDATOR.validate_contracts(self.root))

    def test_analyzed_work_authority_is_projected_to_each_template(self) -> None:
        expected = {
            "engineering-brief-template.md": (
                "current Engineering Brief is the only operational analysis authority",
                "First Executable Slice is a complete Task Contract v2",
                "Specialist results are analysis input only",
            ),
            "direct-task-template.md": (
                "outside the Analyzed Work authority path",
            ),
            "task-dag-template.md": (
                "derived projection of the current Engineering Brief",
                "must not select or replace the First Executable Slice",
                "return to analysis",
            ),
            "implementation-handoff-template.md": (
                "derived projection of the current Engineering Brief",
                "return to analysis",
            ),
            "review-handoff-template.md": (
                "derived projection of the current Engineering Brief",
                "return to analysis",
            ),
        }
        for name, terms in expected.items():
            text = (self.root / name).read_text(encoding="utf-8")
            normalized = " ".join(text.casefold().split())
            for term in terms:
                with self.subTest(template=name, term=term):
                    self.assertIn(" ".join(term.casefold().split()), normalized)

    def test_each_template_authority_projection_has_a_negative_control(self) -> None:
        for name, terms in VALIDATOR.ANALYZED_WORK_TEMPLATE_TERMS.items():
            for term in terms:
                with self.subTest(template=name, term=term):
                    errors = self._mutate_normalized_term(name, term)
                    self.assertTrue(
                        any("analyzed-work authority" in error for error in errors),
                        errors,
                    )
                    self.tearDown()
                    self.setUp()

    def test_professional_authority_projections_reject_drift(self) -> None:
        for relative, terms in VALIDATOR.PROFESSIONAL_AUTHORITY_TERMS.items():
            for term in terms:
                with self.subTest(path=relative, term=term), tempfile.TemporaryDirectory() as raw:
                    professional_root = Path(raw) / "professional-skills"
                    shutil.copytree(
                        ROOT / "src" / "professional-skills" / "engineering-change-analysis",
                        professional_root / "engineering-change-analysis",
                    )
                    shutil.copytree(
                        ROOT / "src" / "professional-skills" / "task-dag-planner",
                        professional_root / "task-dag-planner",
                    )
                    path = professional_root / relative
                    text = path.read_text(encoding="utf-8")
                    pattern = r"\s+".join(re.escape(part) for part in term.split())
                    mutated, count = re.subn(
                        pattern,
                        "REMOVED_PROFESSIONAL_AUTHORITY_TERM",
                        text,
                        count=1,
                        flags=re.IGNORECASE,
                    )
                    self.assertEqual(1, count, (relative, term))
                    path.write_text(mutated, encoding="utf-8")
                    errors: list[str] = []
                    with mock.patch.object(
                        VALIDATOR,
                        "PROFESSIONAL_ROOT",
                        professional_root,
                    ):
                        VALIDATOR._validate_professional_authority_projections(errors)
                    self.assertTrue(
                        any("authority term" in error for error in errors),
                        errors,
                    )

    def test_conditional_test_evidence_projection_is_exact_once(self) -> None:
        contract = CORE_CONTRACTS["visible_evidence_contract"][
            "conditional_test_evidence"
        ]
        self.assertEqual(
            list(CONDITIONAL_TEST_EVIDENCE_TARGETS),
            contract["projection_targets"],
        )
        self.assertEqual(
            CONDITIONAL_TEST_EVIDENCE_PROJECTION,
            contract["projection_text"],
        )
        for name in CONDITIONAL_TEST_EVIDENCE_TARGETS:
            with self.subTest(template=name):
                normalized = " ".join(
                    (self.root / name).read_text(encoding="utf-8").split()
                )
                self.assertEqual(
                    1,
                    normalized.count(CONDITIONAL_TEST_EVIDENCE_PROJECTION),
                )

    def test_conditional_test_evidence_projection_rejects_removal(self) -> None:
        for name in CONDITIONAL_TEST_EVIDENCE_TARGETS:
            with self.subTest(template=name):
                path = self.root / name
                original = path.read_text(encoding="utf-8")
                normalized = " ".join(original.split())
                self.assertIn(CONDITIONAL_TEST_EVIDENCE_PROJECTION, normalized)
                mutated = original.replace(
                    "`test-approach-selected`",
                    "`removed-test-approach-selected`",
                    1,
                )
                path.write_text(mutated, encoding="utf-8")
                try:
                    errors = VALIDATOR.validate_contracts(self.root)
                    self.assertTrue(
                        any(
                            name in error
                            and "conditional test evidence projection" in error
                            for error in errors
                        ),
                        errors,
                    )
                finally:
                    path.write_text(original, encoding="utf-8")

    def test_implementation_handoff_rejects_conditional_test_evidence_omission(
        self,
    ) -> None:
        errors = self._mutate(
            "implementation-handoff-template.md",
            "`test-approach-selected`",
            "`omitted-test-approach-selected`",
        )
        self.assertTrue(
            any("conditional test evidence projection" in error for error in errors),
            errors,
        )

    def test_conditional_test_evidence_projection_rejects_weakening_and_duplicate(
        self,
    ) -> None:
        path = self.root / "direct-task-template.md"
        original = path.read_text(encoding="utf-8")
        weakened, weakening_count = re.subn(
            r"Never fabricate\s+unavailable proof",
            "Unavailable proof may be inferred",
            original,
            count=1,
        )
        self.assertEqual(1, weakening_count)
        for label, mutated in (
            ("weakening", weakened),
            (
                "duplicate",
                f"{original}\n{CONDITIONAL_TEST_EVIDENCE_PROJECTION}\n",
            ),
        ):
            with self.subTest(mutation=label):
                self.assertNotEqual(original, mutated)
                path.write_text(mutated, encoding="utf-8")
                errors = VALIDATOR.validate_contracts(self.root)
                self.assertTrue(
                    any(
                        "conditional test evidence projection" in error
                        for error in errors
                    ),
                    errors,
                )
        path.write_text(original, encoding="utf-8")

    def test_five_templates_resolve_integrity_fallback_without_duplicate_prose(self) -> None:
        names = (
            "direct-task-template.md",
            "engineering-brief-template.md",
            "task-dag-template.md",
            "implementation-handoff-template.md",
            "review-handoff-template.md",
        )
        duplicated_rule = (
            "Unknown or malformed content takes the complete integrity fallback with no "
            "partial computation: L4 floor retaining explicit known L5, edit blocked, "
            "only blocker or read-only diagnosis, and no implementation, validation, "
            "release, or Router."
        )
        duplicated = []
        for name in names:
            text = (self.root / name).read_text(encoding="utf-8")
            if duplicated_rule in " ".join(text.split()):
                duplicated.append(name)
        self.assertEqual(
            [],
            duplicated,
            f"duplicate multi-decision integrity fallback prose remains in {duplicated}",
        )
        for name in names:
            with self.subTest(template=name):
                text = (self.root / name).read_text(encoding="utf-8")
                self.assertIn(
                    "[execution-level-contract.md](execution-level-contract.md)",
                    text,
                )

        runtime = (self.root / "execution-level-contract.md").read_text(
            encoding="utf-8"
        )
        for term in (
            '"integrity_fallback"',
            '"inputs":["missing","malformed","duplicate"]',
            '"partial_computation":false',
            '"edit_status":"blocked"',
        ):
            with self.subTest(runtime_term=term):
                self.assertIn(term, runtime)

    def test_fallback_preamble_rejects_paraphrased_multi_outcome_restatement(self) -> None:
        restatement = (
            "Invalid execution data blocks editing and implementation while permitting "
            "only an integrity report or read-only diagnosis."
        )
        for name in (
            "direct-task-template.md",
            "engineering-brief-template.md",
            "task-dag-template.md",
            "implementation-handoff-template.md",
            "review-handoff-template.md",
        ):
            with self.subTest(template=name):
                path = self.root / name
                text = path.read_text(encoding="utf-8")
                path.write_text(
                    text.replace("Legacy without v1", f"{restatement}\nLegacy without v1", 1),
                    encoding="utf-8",
                )
                errors = VALIDATOR.validate_contracts(self.root)
                self.assertTrue(
                    any("canonical-link-only preamble" in error for error in errors),
                    errors,
                )
                self.tearDown()
                self.setUp()

    def test_fallback_preamble_rejects_reordered_multi_outcome_restatement(self) -> None:
        restatement = (
            "For malformed execution data, validation and release stop; diagnosis is "
            "the only route, partial computation stays off, and editing is blocked."
        )
        for name in (
            "direct-task-template.md",
            "engineering-brief-template.md",
            "task-dag-template.md",
            "implementation-handoff-template.md",
            "review-handoff-template.md",
        ):
            with self.subTest(template=name):
                path = self.root / name
                text = path.read_text(encoding="utf-8")
                path.write_text(
                    text.replace("Legacy without v1", f"{restatement}\nLegacy without v1", 1),
                    encoding="utf-8",
                )
                errors = VALIDATOR.validate_contracts(self.root)
                self.assertTrue(
                    any("canonical-link-only preamble" in error for error in errors),
                    errors,
                )
                self.tearDown()
                self.setUp()

    def test_fallback_preamble_rejects_before_marker_paraphrase(self) -> None:
        restatement = (
            "Invalid execution data blocks edits and implementation but still allows "
            "an integrity report or read-only diagnosis."
        )
        marker = "The public Execution Level lines"
        for name in VALIDATOR._PUBLIC_EXECUTION_PREAMBLE_TEMPLATES:
            with self.subTest(template=name):
                errors = self._mutate(
                    name,
                    marker,
                    f"{restatement}\n\n{marker}",
                )
                self.assertTrue(
                    any("complete canonical-link-only preamble" in error for error in errors),
                    errors,
                )
                self.tearDown()
                self.setUp()

    def test_fallback_preamble_rejects_before_marker_reordering(self) -> None:
        restatement = (
            "Diagnosis remains available after validation and release stop, editing is "
            "blocked, and partial computation is disabled for malformed execution data."
        )
        marker = "The public Execution Level lines"
        for name in VALIDATOR._PUBLIC_EXECUTION_PREAMBLE_TEMPLATES:
            with self.subTest(template=name):
                errors = self._mutate(
                    name,
                    marker,
                    f"{restatement}\n\n{marker}",
                )
                self.assertTrue(
                    any("complete canonical-link-only preamble" in error for error in errors),
                    errors,
                )
                self.tearDown()
                self.setUp()

    def test_retired_public_digest_language_is_rejected(self) -> None:
        implementation = self.root / "implementation-handoff-template.md"
        text = implementation.read_text(encoding="utf-8")
        self.assertNotIn("digest", text.casefold())
        self.assertEqual([], VALIDATOR.validate_contracts(self.root))
        implementation.write_text(
            text.replace(
                "Current task-agent evidence",
                "Self-reported digest evidence",
                1,
            ),
            encoding="utf-8",
        )
        errors = VALIDATOR.validate_contracts(self.root)
        self.assertTrue(
            any("self-reported or unbound digest" in error for error in errors),
            errors,
        )

    def test_direct_task_may_omit_optional_dependencies(self) -> None:
        text = (self.root / "direct-task-template.md").read_text(encoding="utf-8")
        self.assertNotIn("## Dependencies", text)
        self.assertEqual([], VALIDATOR.validate_contracts(self.root))

    def test_direct_task_forbids_owner_or_verification_discovery(self) -> None:
        path = self.root / "direct-task-template.md"
        text = path.read_text(encoding="utf-8")
        self.assertNotIn("Owner / Verification Discovery Allowed", text)
        self.assertNotIn("bounded ownership discovery", text)
        self.assertNotIn("Use only", text)
        self.assertNotIn("may inspect only", text)
        self.assertNotIn("must not discover", text)
        self.assertIn(
            "If ownership or\nverification needs discovery, stop and route to Analyzed Work",
            text,
        )
        path.write_text(
            text.replace(
                "If ownership or\nverification needs discovery, stop and route to Analyzed Work",
                "Task agents may discover ownership or verification before editing",
                1,
            ),
            encoding="utf-8",
        )
        errors = VALIDATOR.validate_contracts(self.root)
        self.assertTrue(
            any("must not permit owner or verification discovery" in error for error in errors),
            errors,
        )

    def test_direct_task_accepts_meaningful_dependencies_at_canonical_position(self) -> None:
        path = self.root / "direct-task-template.md"
        text = path.read_text(encoding="utf-8")
        path.write_text(
            text.replace(
                "## Non-goals\n\n## Expected Output",
                "## Non-goals\n\n## Dependencies\n\nNamed upstream task output.\n\n## Expected Output",
                1,
            ),
            encoding="utf-8",
        )
        self.assertEqual([], VALIDATOR.validate_contracts(self.root))

    def test_direct_task_rejects_empty_optional_dependencies(self) -> None:
        errors = self._mutate(
            "direct-task-template.md",
            "## Non-goals\n\n## Expected Output",
            "## Non-goals\n\n## Dependencies\n\n## Expected Output",
        )
        self.assertTrue(any("meaningful dependency" in error for error in errors), errors)

    def test_direct_task_rejects_optional_dependencies_out_of_order_or_repeated(self) -> None:
        errors = self._mutate(
            "direct-task-template.md",
            "## Acceptance\n",
            "## Dependencies\n\nNamed upstream task output.\n\n## Acceptance\n",
        )
        self.assertTrue(any("headings must exactly match" in error for error in errors), errors)
        self.tearDown()
        self.setUp()
        errors = self._mutate(
            "direct-task-template.md",
            "## Non-goals\n",
            "## Non-goals\n\n## Dependencies\n\n## Dependencies\n",
        )
        self.assertTrue(any("must not repeat" in error for error in errors), errors)

    def test_utility_status_values_are_model_gated(self) -> None:
        errors = self._mutate(
            "utility-capsule-template.md",
            "Exactly `blocked`, `partial`, or `completed`.",
            "Exactly `in_progress` or `completed`.",
        )
        self.assertTrue(any("Utility Return Status values" in error for error in errors), errors)

    def test_direct_task_rejects_missing_duplicate_and_wrong_order_owner(self) -> None:
        with self.subTest("missing"):
            self._mutate("direct-task-template.md", "## Owner\n", "")
        self.tearDown()
        self.setUp()
        with self.subTest("duplicate"):
            self._mutate(
                "direct-task-template.md",
                "## Owner\n",
                "## Owner\n\n## Owner\n",
            )
        self.tearDown()
        self.setUp()
        with self.subTest("wrong-order"):
            self._mutate(
                "direct-task-template.md",
                "## Goal\n\n## Owner\n",
                "## Owner\n\n## Goal\n",
            )

    def test_direct_task_rejects_h1_change_and_extension_heading_drift(self) -> None:
        with self.subTest("changed-h1"):
            errors = self._mutate(
                "direct-task-template.md",
                "# Direct Task Contract v2\n",
                "# Direct Task Contract\n",
            )
            self.assertTrue(any("document headings must be exactly" in error for error in errors))
        self.tearDown()
        self.setUp()
        with self.subTest("duplicate-h1"):
            errors = self._mutate(
                "direct-task-template.md",
                "# Direct Task Contract v2\n",
                "# Direct Task Contract v2\n\n# Direct Task Contract v2\n",
            )
            self.assertTrue(any("document headings must be exactly" in error for error in errors))
        self.tearDown()
        self.setUp()
        with self.subTest("swapped-extension"):
            path = self.root / "direct-task-template.md"
            text = path.read_text(encoding="utf-8")
            text = text.replace("## Inspection Boundary\n", "## __SWAP__\n", 1)
            text = text.replace(
                "## Inspection Stop Conditions\n",
                "## Inspection Boundary\n",
                1,
            )
            path.write_text(
                text.replace(
                    "## __SWAP__\n",
                    "## Inspection Stop Conditions\n",
                    1,
                ),
                encoding="utf-8",
            )
            errors = VALIDATOR.validate_contracts(self.root)
            self.assertTrue(any("headings must exactly match" in error for error in errors))
        self.tearDown()
        self.setUp()
        with self.subTest("duplicate-extension"):
            errors = self._mutate(
                "direct-task-template.md",
                "## Inspection Boundary\n",
                "## Inspection Boundary\n\n## Inspection Boundary\n",
            )
            self.assertTrue(any("headings must exactly match" in error for error in errors))

    def test_direct_task_rejects_missing_output_and_evidence_requirements(self) -> None:
        for heading in ("Expected Output", "Evidence Requirements"):
            with self.subTest(heading=heading):
                self._mutate("direct-task-template.md", f"## {heading}\n", "")
                self.tearDown()
                self.setUp()

    def test_dag_rejects_missing_dependencies(self) -> None:
        errors = self._mutate("task-dag-template.md", "Dependencies:\n", "Dependency:\n")
        self.assertTrue(any("Task A fields" in error for error in errors), errors)

    def test_parallel_group_rejects_missing_owners(self) -> None:
        for field in (
            "Integration Owner",
            "Merge Owner",
            "Conflict Resolution Owner",
        ):
            with self.subTest(field=field):
                marker = f"{field}:\n"
                block = (self.root / "task-dag-template.md").read_text(encoding="utf-8")
                parallel = block.split("## Parallel Group", 1)[1].split(
                    "## Integration Boundary", 1
                )[0]
                self.assertIn(marker, parallel)
                path = self.root / "task-dag-template.md"
                prefix, rest = block.split("## Parallel Group", 1)
                parallel_body, suffix = rest.split("## Integration Boundary", 1)
                path.write_text(
                    prefix
                    + "## Parallel Group"
                    + parallel_body.replace(marker, "", 1)
                    + "## Integration Boundary"
                    + suffix,
                    encoding="utf-8",
                )
                errors = VALIDATOR.validate_contracts(self.root)
                self.assertTrue(any("Parallel Group fields" in error for error in errors), errors)
                self.tearDown()
                self.setUp()

    def test_templates_reject_unknown_field_and_invalid_status(self) -> None:
        errors = self._mutate(
            "direct-task-template.md",
            "## Goal\n",
            "## Unknown Field\n\n## Goal\n",
        )
        self.assertTrue(any("headings must exactly match" in error for error in errors), errors)
        self.tearDown()
        self.setUp()
        errors = self._mutate(
            "direct-task-template.md",
            "## Status\n\nin_progress\n",
            "## Status\n\npartial\n",
        )
        self.assertTrue(any("Status heading" in error for error in errors), errors)

    def test_all_task_assignments_start_in_progress(self) -> None:
        mutations = (
            (
                "direct-task-template.md",
                "## Status\n\nin_progress\n",
                "## Status\n\nblocked\n",
            ),
            (
                "engineering-brief-template.md",
                "Status: in_progress",
                "Status: partial",
            ),
            (
                "task-dag-template.md",
                "Status: in_progress",
                "Status: completed",
            ),
        )
        for name, old, new in mutations:
            with self.subTest(template=name):
                errors = self._mutate(name, old, new)
                self.assertTrue(
                    any(
                        "Status heading" in error
                        or "must contain exactly 'Status: in_progress'" in error
                        for error in errors
                    ),
                    errors,
                )
                self.tearDown()
                self.setUp()

    def test_shared_or_unknown_workspace_writes_cannot_be_parallelized(self) -> None:
        errors = self._mutate(
            "task-dag-template.md",
            "With a shared or unknown workspace, serialize writes.",
            "With a shared or unknown workspace, parallelize writes.",
        )
        self.assertTrue(any("must serialize" in error for error in errors), errors)

    def test_handoff_requires_task_id_owner_and_ledger(self) -> None:
        for heading in ("Task ID", "Owner", "Evidence Ledger"):
            with self.subTest(heading=heading):
                errors = self._mutate(
                    "implementation-handoff-template.md",
                    f"## {heading}\n",
                    "",
                )
                self.assertTrue(any("headings must exactly match" in error for error in errors), errors)
                self.tearDown()
                self.setUp()

    def test_implementation_handoff_requires_each_forbidden_storage_projection(self) -> None:
        for rule in VALIDATOR.EVIDENCE_LEDGER_MODEL["forbidden_storage"]:
            term = rule["projection_terms"][0]
            with self.subTest(rule=rule["id"]):
                errors = self._mutate(
                    "implementation-handoff-template.md",
                    term,
                    "REMOVED_STORAGE_TERM",
                )
                self.assertTrue(
                    any(f"forbidden storage rule {rule['id']!r}" in error for error in errors),
                    errors,
                )
                self.tearDown()
                self.setUp()

    def test_execution_extension_is_additive_and_ordered_on_every_surface(self) -> None:
        fields = VALIDATOR._public_execution_snapshot()["ordered_labels"]
        direct = (self.root / "direct-task-template.md").read_text(encoding="utf-8")
        self.assertLess(direct.index("## Task ID"), direct.index("## Status"))
        self.assertLess(direct.index("## Status"), direct.index("## Execution Level"))
        for field in fields:
            self.assertEqual(
                1,
                len(re.findall(rf"^{re.escape(field)}:", direct, flags=re.MULTILINE)),
            )
        for name, section in (
            ("engineering-brief-template.md", "First Executable Slice"),
            ("task-dag-template.md", "Task A"),
        ):
            with self.subTest(template=name):
                text = (self.root / name).read_text(encoding="utf-8")
                extraction_errors: list[str] = []
                surface = VALIDATOR._contract_surface(
                    text,
                    container="fenced-markdown",
                    context=name,
                    errors=extraction_errors,
                )
                self.assertEqual([], extraction_errors)
                body = VALIDATOR.extract_section_body(surface, section)
                self.assertIsNotNone(body)
                assert body is not None
                expected = ["Task ID", "Status", *fields]
                self.assertEqual(
                    expected,
                    VALIDATOR._ordered_labeled_fields(body)[: len(expected)],
                )
        for name in (
            "implementation-handoff-template.md",
            "review-handoff-template.md",
        ):
            with self.subTest(template=name):
                text = (self.root / name).read_text(encoding="utf-8")
                self.assertLess(text.index("## Task ID"), text.index("## Execution Level"))
                self.assertLess(text.index("## Execution Level"), text.index("## Owner"))

        insertions = VALIDATOR.TASK_CONTRACT_MODEL["execution_level_extension"][
            "surface_insertions"
        ]
        for name, insertion in insertions.items():
            with self.subTest(exact_surface=name):
                text = (self.root / name).read_text(encoding="utf-8")
                expected_count = len(insertion.get("sections", [insertion]))
                block = public_execution_template_block(CORE_CONTRACTS, name)
                self.assertEqual(expected_count, text.count(block))

    def test_execution_extension_order_mutations_fail(self) -> None:
        mutations = (
            (
                "direct-task-template.md",
                "Level: requested=unspecified / L1 / L5; automatic=L2 / L3 / L4; default=L3; effective=L1 / L2 / L3 / L4 / L5; edit=allowed / blocked\nBasis:",
                "Basis:\nLevel: requested=unspecified / L1 / L5; automatic=L2 / L3 / L4; default=L3; effective=L1 / L2 / L3 / L4 / L5; edit=allowed / blocked",
            ),
            (
                "engineering-brief-template.md",
                "Level: requested=unspecified / L1 / L5; automatic=L2 / L3 / L4; default=L3; effective=L1 / L2 / L3 / L4 / L5; edit=allowed / blocked\nBasis:",
                "Basis:\nLevel: requested=unspecified / L1 / L5; automatic=L2 / L3 / L4; default=L3; effective=L1 / L2 / L3 / L4 / L5; edit=allowed / blocked",
            ),
            (
                "task-dag-template.md",
                "Level: requested=unspecified / L1 / L5; automatic=L2 / L3 / L4; default=L3; effective=L1 / L2 / L3 / L4 / L5; edit=allowed / blocked\nBasis:",
                "Basis:\nLevel: requested=unspecified / L1 / L5; automatic=L2 / L3 / L4; default=L3; effective=L1 / L2 / L3 / L4 / L5; edit=allowed / blocked",
            ),
        )
        for name, old, new in mutations:
            with self.subTest(template=name):
                errors = self._mutate(name, old, new)
                self.assertTrue(
                    any(
                        "managed public Execution Level" in error
                        or "Task Contract v2" in error
                        or "fields must be exactly ordered" in error
                        for error in errors
                    ),
                    errors,
                )
                self.tearDown()
                self.setUp()

    def test_public_execution_template_rules_and_subfields_are_gated(self) -> None:
        errors = self._mutate(
            "direct-task-template.md",
            "[execution-level-contract.md](execution-level-contract.md)",
            "missing execution-level fallback authority",
        )
        self.assertTrue(
            any("missing public execution-level/v1 rule" in error for error in errors),
            errors,
        )
        self.tearDown()
        self.setUp()
        errors = self._mutate(
            "implementation-handoff-template.md",
            "requested=unspecified / L1 / L5; automatic=L2 / L3 / L4",
            "automatic=L2 / L3 / L4; requested=unspecified / L1 / L5",
        )
        self.assertTrue(
            any("exact Core rendering" in error for error in errors),
            errors,
        )

    def test_every_public_execution_template_rejects_value_mutations(self) -> None:
        surfaces = VALIDATOR.TASK_CONTRACT_MODEL["execution_level_extension"][
            "surface_insertions"
        ]
        mutations = (
            (
                "default=L3",
                "default=L2",
            ),
            (
                "effective=L1 / L2 / L3 / L4 / L5",
                "effective=L1 / L5",
            ),
            (
                "when=effective L5 only",
                "when=all levels",
            ),
        )
        for name in surfaces:
            for old, new in mutations:
                with self.subTest(template=name, mutation=old):
                    errors = self._mutate(name, old, new)
                    self.assertTrue(
                        any("exact Core rendering" in error for error in errors),
                        errors,
                    )
                    self.tearDown()
                    self.setUp()

    def test_router_projection_is_exact_core_rendering(self) -> None:
        router = (self.root / "professional-skill-router.md").read_text(encoding="utf-8")
        self.assertTrue(router.endswith("\n"))
        self.assertEqual(62, len(router.splitlines()))
        self.assertEqual([], VALIDATOR.execution_level_router_errors(router))
        over_budget = (
            router.rstrip("\n")
            + "\n<!-- route-budget-negative-control -->\n"
        )
        self.assertEqual(63, len(over_budget.splitlines()))
        self.assertTrue(
            any(
                "at most 62 lines" in error
                for error in VALIDATOR.execution_level_router_errors(over_budget)
            )
        )
        payload_drift = router.replace("`effective_level`", "`computed_floor`", 1)
        self.assertTrue(
            any(
                "exact Core rendering" in error
                for error in VALIDATOR.execution_level_router_errors(payload_drift)
            )
        )
        begin = "<!-- BEGIN CHANGEFORGE CORE ROUTER PROJECTION: execution-level-router-projection -->"
        end = "<!-- END CHANGEFORGE CORE ROUTER PROJECTION: execution-level-router-projection -->"
        mutations = (
            router.replace(begin, "", 1),
            router.replace(begin, begin + "\n" + begin, 1),
            router.replace(begin, "__BEGIN__", 1).replace(end, begin, 1).replace("__BEGIN__", end, 1),
        )
        for mutation in mutations:
            with self.subTest():
                self.assertTrue(VALIDATOR.execution_level_router_errors(mutation))
        for forbidden in (
            "Execution Level Projection",
            "Closed Trigger Registry",
            *(
                row["id"]
                for row in CORE_CONTRACTS["execution_level_contract"]["trigger_registry"]
            ),
        ):
            self.assertNotIn(forbidden, router)


class CoreContractModelTests(unittest.TestCase):
    def test_analyzed_work_uses_the_engineering_brief_as_single_authority(self) -> None:
        contract = CORE_CONTRACTS["task_contract"]["analyzed_work_authority"]
        self.assertEqual("analyzed-work", contract["applies_to"])
        self.assertEqual("current-engineering-brief", contract["operational_authority"])
        self.assertEqual(
            [
                "Problem and Desired Behavior",
                "Acceptance and Non-goals",
                "Ownership and Invariants",
                "Placement and Reuse",
                "Contract / Data / Failure Impact",
                "Validation Strategy",
                "Risks and Rollback",
                "First Executable Slice",
                "Task Dependencies",
                "Integration Boundary",
                "Review Boundary",
                "Evidence Gaps and Proof Limits",
            ],
            contract["authoritative_sections"],
        )
        self.assertEqual(
            {
                "defined_by": "engineering-brief",
                "contract": "Task Contract v2",
                "required_fields_source": (
                    "task_contract.template_schemas.engineering-brief-template.md."
                    "labeled_sections.First Executable Slice"
                ),
                "dispatch": "verbatim",
                "main_reinterpretation": "forbidden",
                "main_generation": "forbidden",
                "dag_reselection": "forbidden",
            },
            contract["first_executable_slice"],
        )
        self.assertEqual(
            "incorporated-into-current-engineering-brief",
            contract["specialist_policy"]["effective_after"],
        )
        self.assertEqual("input-only", contract["specialist_policy"]["authority"])
        self.assertEqual(
            "return-to-analysis",
            contract["dag_planner_policy"]["insufficient_brief"],
        )
        self.assertEqual([], validate_core_contracts(CORE_CONTRACTS))

    def test_task_boundary_relations_and_same_pattern_authorization_are_closed(self) -> None:
        task = CORE_CONTRACTS["task_contract"]
        boundary = task["task_boundary"]
        self.assertEqual(["Goal", "Acceptance", "Non-goals"], boundary["fields"])
        self.assertEqual(
            "inspection-and-discovery-boundary",
            boundary["allowed_read_scope"],
        )
        self.assertEqual(
            "permission-ceiling-not-work-obligation",
            boundary["allowed_write_scope"],
        )
        self.assertFalse(boundary["discovery_grants_repair_authority"])
        self.assertFalse(boundary["repository_clean_required"])

        relations = task["finding_relations"]
        self.assertEqual(
            ["current-task", "scope-blocker", "adjacent"],
            relations["values"],
        )
        self.assertEqual(
            ["relation", "severity", "blocker"],
            relations["classification_order"],
        )
        self.assertEqual("orthogonal", relations["severity_relation"])
        self.assertEqual(["current-task"], relations["repair_input_relations"])
        self.assertFalse(
            relations["rules"]["adjacent"]["high_or_critical_scope_authority"]
        )

        scan = task["same_pattern_scan"]
        self.assertFalse(scan["discovery_grants_repair_authority"])
        self.assertEqual(
            "current-task-fix",
            scan["routes"]["affects_current_inside_authorized_scope"],
        )
        self.assertEqual(
            "scope-blocker-return-main",
            scan["routes"]["affects_current_outside_authorized_scope"],
        )
        self.assertEqual(
            "adjacent-record-do-not-edit",
            scan["routes"]["does_not_affect_current"],
        )

    def test_effective_level_review_policy_is_closed_and_task_scoped(self) -> None:
        review = CORE_CONTRACTS["review_discipline_contract"]
        policy = review["effective_level_policy"]
        self.assertEqual("execution_level_contract.effective_level", policy["source"])
        self.assertFalse(policy["creates_review_level"])
        self.assertEqual("review-agent", policy["final_review_profile"])
        self.assertEqual(
            ["latest actual diff", "every changed file"],
            policy["final_review_target"],
        )
        self.assertEqual(
            ["L1", "L2", "L3", "L4", "L5"],
            list(policy["levels"]),
        )
        self.assertEqual(1, policy["levels"]["L1"]["final_reviewers"])
        self.assertEqual(1, policy["levels"]["L2"]["final_reviewers"])
        self.assertEqual(1, policy["levels"]["L3"]["final_reviewers"])
        self.assertTrue(policy["levels"]["L3"]["risk_triggered_jit_lenses"])
        self.assertFalse(policy["levels"]["L4"]["default_preimplementation_review"])
        self.assertFalse(policy["levels"]["L4"]["default_secondary_reviewer"])
        self.assertTrue(policy["levels"]["L5"]["independent_preimplementation_review"])
        self.assertTrue(policy["levels"]["L5"]["exhaustive_final_review"])
        self.assertFalse(policy["levels"]["L5"]["full_ci_required"])
        self.assertFalse(policy["levels"]["L5"]["cross_model_review_required"])

        matrix = review["professional_risk_matrix"]
        self.assertEqual(
            [
                "Current Task Boundary",
                "latest actual diff",
                "current change reachable impact",
            ],
            matrix["evaluation_scope"],
        )
        self.assertFalse(matrix["repository_health_audit"])
        self.assertFalse(matrix["context_read_grants_repair_authority"])
        self.assertEqual(
            "task_contract.finding_relations",
            review["finding_policy_source"],
        )

    def test_external_read_is_analysis_only_jit_untrusted_and_fail_safe(self) -> None:
        contract = CORE_CONTRACTS["external_read_contract"]
        self.assertEqual("analysis-agent", contract["exclusive_role"])
        self.assertEqual("external-read", contract["tool"])
        self.assertEqual(
            [
                "native-enforced",
                "sandbox-enforced",
                "prompt-enforced",
                "unsupported",
            ],
            contract["capability_modes"],
        )
        self.assertFalse(contract["general_network_counts_as_supported"])
        self.assertEqual(
            ["WebSearch", "WebFetch", "ConnectorRead"],
            contract["ledger_projection"]["command_values"],
        )
        self.assertEqual(
            "visible_evidence_contract",
            contract["ledger_projection"]["schema_source"],
        )
        self.assertEqual(
            [
                "external-source",
                "analysis-agent-judgment",
                "normalized-claim",
                "evidence-ledger",
                "engineering-brief-decision",
            ],
            contract["trust_boundary"]["normalization_path"],
        )
        self.assertEqual(
            {
                "trigger": "critical-fact-missing-can-invalidate-current-slice",
                "execution_trigger": "unknown-critical-boundary",
                "edit_status": "blocked",
                "dispatch_implementation": False,
            },
            contract["missing_evidence"]["critical"],
        )
        self.assertEqual(
            "continue-when-existing-evidence-is-sufficient",
            contract["unsupported_behavior"],
        )
        self.assertIn("external-read", CORE_CONTRACTS["roles"]["analysis-agent"]["tools"])
        self.assertNotIn("external-read", CORE_CONTRACTS["roles"]["task-agent"]["tools"])
        self.assertNotIn("external-read", CORE_CONTRACTS["roles"]["review-agent"]["tools"])

    def test_authority_scope_review_and_external_read_mutations_fail_closed(self) -> None:
        mutations: list[tuple[str, dict[str, object]]] = []

        regenerated_slice = copy.deepcopy(CORE_CONTRACTS)
        regenerated_slice["task_contract"]["analyzed_work_authority"][
            "first_executable_slice"
        ]["main_generation"] = "allowed"
        mutations.append(("main-regenerates-slice", regenerated_slice))

        widened_relation = copy.deepcopy(CORE_CONTRACTS)
        widened_relation["task_contract"]["finding_relations"]["values"].append(
            "repository-health"
        )
        mutations.append(("finding-relation-widened", widened_relation))

        sibling_repair = copy.deepcopy(CORE_CONTRACTS)
        sibling_repair["task_contract"]["same_pattern_scan"]["routes"][
            "does_not_affect_current"
        ] = "repair"
        mutations.append(("adjacent-same-pattern-repair", sibling_repair))

        default_l4_prereview = copy.deepcopy(CORE_CONTRACTS)
        default_l4_prereview["review_discipline_contract"]["effective_level_policy"][
            "levels"
        ]["L4"]["default_preimplementation_review"] = True
        mutations.append(("default-l4-prereview", default_l4_prereview))

        broad_network = copy.deepcopy(CORE_CONTRACTS)
        broad_network["external_read_contract"]["general_network_counts_as_supported"] = True
        mutations.append(("general-network-supported", broad_network))

        task_external_read = copy.deepcopy(CORE_CONTRACTS)
        task_external_read["roles"]["task-agent"]["tools"].append("external-read")
        mutations.append(("task-agent-external-read", task_external_read))

        for label, mutation in mutations:
            with self.subTest(label=label):
                self.assertTrue(validate_core_contracts(mutation))

    def test_new_core_rules_preserve_existing_protocol_counts_and_versions(self) -> None:
        self.assertEqual(2, CORE_CONTRACTS["task_contract"]["schema_version"])
        self.assertEqual(
            ["in_progress", "blocked", "partial", "completed"],
            CORE_CONTRACTS["completion_state"]["statuses"],
        )
        self.assertEqual(
            ["current", "superseded", "invalid"],
            CORE_CONTRACTS["visible_evidence_contract"]["states"],
        )
        self.assertEqual(4, len(CORE_CONTRACTS["roles"]))
        self.assertEqual(
            ["L1", "L2", "L3", "L4", "L5"],
            [
                level["id"]
                for level in CORE_CONTRACTS["execution_level_contract"]["levels"]
            ],
        )

    def _route_decision_fixture(
        self,
    ) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
        level_basis = {
            "trigger_evaluations": [
                {
                    "id": "major-architecture-or-physical-safety",
                    "status": "matched",
                    "evidence_kind": "analysis_handoff",
                    "source_anchor": "task:route-contract:risk",
                    "plausible_critical": False,
                }
            ],
            "l2_eligibility": [],
            "obligations": ["high-risk pre-implementation evidence"],
            "unresolved": [],
            "edit_status": "allowed",
        }
        main_execution = {
            "producer": "main-control-agent",
            "task_id": "task-route-contract",
            "execution_level": "L4",
            "level_basis": level_basis,
        }
        authority = VALIDATION_UTILS.professional_routing_authority()
        envelope = {
            "path": "direct",
            "route_result": {
                "start_profile": "task-agent",
                "primary_skill": "repository-tooling-change-builder",
                "layer3_skills": ["implementation-structure-design"],
                "review_skill": "ai-code-review-refactor",
                "execution_level": "L4",
                "level_basis": copy.deepcopy(level_basis),
            },
            "selection_evidence": {
                "task_evidence": [
                    {
                        "id": "tool-owner",
                        "kind": "analysis_handoff",
                        "task_id": "task-route-contract",
                        "source_anchor": "task:route-contract:owner",
                    },
                    {
                        "id": "backend-rejected",
                        "kind": "analysis_handoff",
                        "task_id": "task-route-contract",
                        "source_anchor": "task:route-contract:non-goal",
                    },
                    {
                        "id": "review-required",
                        "kind": "task_contract",
                        "task_id": "task-route-contract",
                        "source_anchor": "task:route-contract:review-owner",
                    },
                    {
                        "id": "placement-open",
                        "kind": "analysis_handoff",
                        "task_id": "task-route-contract",
                        "source_anchor": "task:route-contract:placement",
                    },
                    {
                        "id": "build-graph-fixed",
                        "kind": "analysis_handoff",
                        "task_id": "task-route-contract",
                        "source_anchor": "task:route-contract:build-graph",
                    },
                ],
                "primary_candidates": [
                    {
                        "skill": "repository-tooling-change-builder",
                        "eligible": True,
                        "evidence_ids": ["tool-owner"],
                        "rejection_reasons": [],
                    },
                    {
                        "skill": "backend-change-builder",
                        "eligible": False,
                        "evidence_ids": ["backend-rejected"],
                        "rejection_reasons": ["backend product behavior is out of scope"],
                    },
                ],
                "review_candidates": [
                    {
                        "skill": "ai-code-review-refactor",
                        "eligible": True,
                        "evidence_ids": ["review-required"],
                        "rejection_reasons": [],
                    }
                ],
                "layer3_candidates": [
                    {
                        "skill": "implementation-structure-design",
                        "eligible": True,
                        "evidence_ids": ["placement-open"],
                        "rejection_reasons": [],
                    },
                    {
                        "skill": "build-tool-professional-usage",
                        "eligible": False,
                        "evidence_ids": ["build-graph-fixed"],
                        "rejection_reasons": ["build graph and generated authority are fixed"],
                    },
                ],
                "eligible_primary_count": 1,
            },
            "main_execution_provenance": copy.deepcopy(main_execution),
            "route_once": True,
        }
        selection = envelope["selection_evidence"]
        for skill in authority["primary_skills_by_profile"]["task-agent"]:
            if any(
                row["skill"] == skill
                for row in selection["primary_candidates"]
            ):
                continue
            selection["primary_candidates"].append(
                {
                    "skill": skill,
                    "eligible": False,
                    "evidence_ids": ["backend-rejected"],
                    "rejection_reasons": [
                        "not selected by the task route evidence"
                    ],
                }
            )
        for skill in authority["review_skills"]:
            if any(
                row["skill"] == skill
                for row in selection["review_candidates"]
            ):
                continue
            selection["review_candidates"].append(
                {
                    "skill": skill,
                    "eligible": False,
                    "evidence_ids": ["review-required"],
                    "rejection_reasons": [
                        "not selected by the review route evidence"
                    ],
                }
            )
        for skill in authority["layer3_candidates_by_primary"][
            "repository-tooling-change-builder"
        ]:
            if any(
                row["skill"] == skill
                for row in selection["layer3_candidates"]
            ):
                continue
            selection["layer3_candidates"].append(
                {
                    "skill": skill,
                    "eligible": False,
                    "evidence_ids": ["build-graph-fixed"],
                    "rejection_reasons": [
                        "not selected by the Layer 3 route evidence"
                    ],
                }
            )
        return envelope, main_execution, authority

    def _validate_route_decision(
        self,
        envelope: dict[str, object],
        main_execution: dict[str, object],
        authority: dict[str, object],
    ) -> list[str]:
        validator = getattr(VALIDATION_UTILS, "validate_route_decision", None)
        self.assertTrue(
            callable(validator),
            "validation_utils.validate_route_decision must own route fixture validation",
        )
        return validator(
            envelope,
            main_execution=main_execution,
            routing_authority=authority,
        )

    def test_route_decision_contract_owns_exact_result_and_envelope_fields(
        self,
    ) -> None:
        contract = CORE_CONTRACTS["route_decision_contract"]
        self.assertEqual(
            [
                "start_profile",
                "primary_skill",
                "layer3_skills",
                "review_skill",
                "execution_level",
                "level_basis",
            ],
            contract["route_result_fields"],
        )
        self.assertEqual(
            [
                "path",
                "route_result",
                "selection_evidence",
                "main_execution_provenance",
                "route_once",
            ],
            contract["envelope_fields"],
        )
        self.assertNotIn("path", contract["route_result_fields"])
        envelope, main_execution, authority = self._route_decision_fixture()
        self.assertEqual(
            set(contract["route_result_fields"]),
            set(envelope["route_result"]),
        )
        self.assertEqual([], self._validate_route_decision(
            envelope,
            main_execution,
            authority,
        ))
        mutated = copy.deepcopy(CORE_CONTRACTS)
        mutated["route_decision_contract"]["route_result_fields"].append("path")
        self.assertTrue(
            any(
                "route_decision_contract.route_result_fields" in error
                for error in validate_core_contracts(mutated)
            )
        )

    def test_route_decision_validator_never_computes_execution_level(self) -> None:
        envelope, main_execution, authority = self._route_decision_fixture()
        with mock.patch.object(
            VALIDATION_UTILS,
            "compute_execution_level",
            side_effect=AssertionError("Router must not compute execution level"),
        ):
            self.assertEqual(
                [],
                self._validate_route_decision(
                    envelope,
                    main_execution,
                    authority,
                ),
            )

    def test_professional_routing_authority_is_current_registry_projection(
        self,
    ) -> None:
        authority = VALIDATION_UTILS.professional_routing_authority()
        self.assertEqual(
            {
                "primary_skills_by_profile",
                "review_skills",
                "layer3_candidates_by_primary",
            },
            set(authority),
        )
        self.assertIn(
            "repository-tooling-change-builder",
            authority["primary_skills_by_profile"]["task-agent"],
        )
        self.assertIn(
            "engineering-change-analysis",
            authority["primary_skills_by_profile"]["analysis-agent"],
        )
        self.assertIn(
            "ai-code-review-refactor",
            authority["review_skills"],
        )

        envelope, main_execution, _canonical = self._route_decision_fixture()
        forged = copy.deepcopy(authority)
        forged["review_skills"].remove("ai-code-review-refactor")
        errors = self._validate_route_decision(
            envelope,
            main_execution,
            forged,
        )
        self.assertTrue(
            any("current Professional registry projection" in error for error in errors),
            errors,
        )

    def test_route_decision_rejects_level_basis_and_provenance_mismatch(
        self,
    ) -> None:
        envelope, main_execution, authority = self._route_decision_fixture()
        mutations: list[dict[str, object]] = []

        level_mismatch = copy.deepcopy(envelope)
        level_mismatch["route_result"]["execution_level"] = "L3"
        mutations.append(level_mismatch)

        basis_mismatch = copy.deepcopy(envelope)
        basis_mismatch["route_result"]["level_basis"]["edit_status"] = "blocked"
        mutations.append(basis_mismatch)

        provenance_mismatch = copy.deepcopy(envelope)
        provenance_mismatch["main_execution_provenance"]["producer"] = (
            "analysis-agent"
        )
        mutations.append(provenance_mismatch)

        for mutation in mutations:
            with self.subTest(mutation=mutation):
                errors = self._validate_route_decision(
                    mutation,
                    main_execution,
                    authority,
                )
                self.assertTrue(
                    any(
                        "main execution" in error.casefold()
                        or "provenance" in error.casefold()
                        for error in errors
                    ),
                    errors,
                )

    def test_route_decision_rejects_bool_int_level_basis_alias(self) -> None:
        envelope, main_execution, authority = self._route_decision_fixture()
        envelope["route_result"]["level_basis"]["trigger_evaluations"][0][
            "plausible_critical"
        ] = 0

        errors = self._validate_route_decision(
            envelope,
            main_execution,
            authority,
        )

        self.assertTrue(
            any(
                "route_result execution_level and level_basis must equal" in error
                for error in errors
            ),
            errors,
        )

    def test_route_decision_rejects_bool_int_main_provenance_alias(self) -> None:
        envelope, main_execution, authority = self._route_decision_fixture()
        envelope["main_execution_provenance"]["level_basis"][
            "trigger_evaluations"
        ][0]["plausible_critical"] = 0

        errors = self._validate_route_decision(
            envelope,
            main_execution,
            authority,
        )

        self.assertTrue(
            any(
                "main execution provenance must equal" in error
                for error in errors
            ),
            errors,
        )

    def test_route_decision_rejects_non_json_basis_without_exception(
        self,
    ) -> None:
        cycle: list[object] = []
        cycle.append(cycle)
        invalid_values = (
            ("nan", float("nan")),
            ("unsupported", object()),
            ("cyclic", cycle),
        )
        for label, invalid_value in invalid_values:
            with self.subTest(label=label):
                envelope, main_execution, authority = self._route_decision_fixture()
                for basis in (
                    main_execution["level_basis"],
                    envelope["route_result"]["level_basis"],
                    envelope["main_execution_provenance"]["level_basis"],
                ):
                    basis["trigger_evaluations"][0][
                        "plausible_critical"
                    ] = invalid_value

                errors = self._validate_route_decision(
                    envelope,
                    main_execution,
                    authority,
                )

                self.assertTrue(
                    any("canonical JSON" in error for error in errors),
                    errors,
                )

    def test_route_decision_rejects_tie_unknown_missing_basis_and_shape_drift(
        self,
    ) -> None:
        envelope, main_execution, authority = self._route_decision_fixture()
        mutations: list[tuple[str, dict[str, object]]] = []

        tie = copy.deepcopy(envelope)
        tie["selection_evidence"]["primary_candidates"][1]["eligible"] = True
        tie["selection_evidence"]["primary_candidates"][1][
            "rejection_reasons"
        ] = []
        tie["selection_evidence"]["eligible_primary_count"] = 2
        mutations.append(("eligible primary", tie))

        missing_basis = copy.deepcopy(envelope)
        missing_basis["selection_evidence"]["primary_candidates"][0][
            "evidence_ids"
        ] = []
        mutations.append(("evidence", missing_basis))

        cross_task_basis = copy.deepcopy(envelope)
        cross_task_basis["selection_evidence"]["task_evidence"][0][
            "task_id"
        ] = "different-task"
        mutations.append(("task-local evidence", cross_task_basis))

        unknown_primary = copy.deepcopy(envelope)
        unknown_primary["route_result"]["primary_skill"] = "unknown-builder"
        unknown_primary["selection_evidence"]["primary_candidates"][0][
            "skill"
        ] = "unknown-builder"
        mutations.append(("known professional", unknown_primary))

        unknown_review = copy.deepcopy(envelope)
        unknown_review["route_result"]["review_skill"] = "unknown-review"
        unknown_review["selection_evidence"]["review_candidates"][0][
            "skill"
        ] = "unknown-review"
        mutations.append(("known professional", unknown_review))

        unknown_layer3 = copy.deepcopy(envelope)
        unknown_layer3["route_result"]["layer3_skills"] = ["unknown-layer3"]
        unknown_layer3["selection_evidence"]["layer3_candidates"][0][
            "skill"
        ] = "unknown-layer3"
        mutations.append(("known candidate", unknown_layer3))

        duplicate_layer3 = copy.deepcopy(envelope)
        duplicate_layer3["route_result"]["layer3_skills"] *= 2
        mutations.append(("duplicate", duplicate_layer3))

        missing_result_field = copy.deepcopy(envelope)
        del missing_result_field["route_result"]["level_basis"]
        mutations.append(("fields must be exactly", missing_result_field))

        extra_result_field = copy.deepcopy(envelope)
        extra_result_field["route_result"]["path"] = "direct"
        mutations.append(("fields must be exactly", extra_result_field))

        incomplete_partition = copy.deepcopy(envelope)
        incomplete_partition["selection_evidence"][
            "primary_candidates"
        ].pop()
        mutations.append(("exact full current registry partition", incomplete_partition))

        for expected, mutation in mutations:
            with self.subTest(expected=expected):
                errors = self._validate_route_decision(
                    mutation,
                    main_execution,
                    authority,
                )
                self.assertTrue(
                    any(expected in error.casefold() for error in errors),
                    errors,
                )

    def test_route_decision_rejects_primary_review_role_swap_and_path_profile(
        self,
    ) -> None:
        envelope, main_execution, authority = self._route_decision_fixture()
        role_swap = copy.deepcopy(envelope)
        role_swap["route_result"]["primary_skill"] = "ai-code-review-refactor"
        role_swap["route_result"]["review_skill"] = (
            "repository-tooling-change-builder"
        )
        role_swap["route_result"]["layer3_skills"] = []
        role_swap["selection_evidence"]["primary_candidates"][0]["skill"] = (
            "ai-code-review-refactor"
        )
        role_swap["selection_evidence"]["review_candidates"][0]["skill"] = (
            "repository-tooling-change-builder"
        )
        role_swap["selection_evidence"]["layer3_candidates"] = []
        errors = self._validate_route_decision(
            role_swap,
            main_execution,
            authority,
        )
        self.assertTrue(
            any("primary authority" in error for error in errors),
            errors,
        )
        self.assertTrue(
            any("review authority" in error for error in errors),
            errors,
        )

        wrong_path_profile = copy.deepcopy(envelope)
        wrong_path_profile["route_result"]["start_profile"] = "analysis-agent"
        errors = self._validate_route_decision(
            wrong_path_profile,
            main_execution,
            authority,
        )
        self.assertTrue(
            any("path/start_profile" in error for error in errors),
            errors,
        )

    def test_route_decision_malformed_json_returns_errors_without_typeerror(
        self,
    ) -> None:
        envelope, main_execution, authority = self._route_decision_fixture()
        mutations: list[dict[str, object]] = []

        invalid_profile = copy.deepcopy(envelope)
        invalid_profile["route_result"]["start_profile"] = []
        mutations.append(invalid_profile)

        invalid_level = copy.deepcopy(envelope)
        invalid_level["route_result"]["execution_level"] = []
        mutations.append(invalid_level)

        invalid_primary_candidate = copy.deepcopy(envelope)
        invalid_primary_candidate["selection_evidence"]["primary_candidates"][0][
            "skill"
        ] = []
        mutations.append(invalid_primary_candidate)

        invalid_review_candidate = copy.deepcopy(envelope)
        invalid_review_candidate["selection_evidence"]["review_candidates"][0][
            "skill"
        ] = []
        mutations.append(invalid_review_candidate)

        invalid_layer3_candidate = copy.deepcopy(envelope)
        invalid_layer3_candidate["selection_evidence"]["layer3_candidates"][0][
            "skill"
        ] = []
        mutations.append(invalid_layer3_candidate)

        for mutation in mutations:
            with self.subTest(mutation=mutation):
                errors = self._validate_route_decision(
                    mutation,
                    main_execution,
                    authority,
                )
                self.assertTrue(errors)

    def test_route_once_is_derived_from_eligible_primary_count(self) -> None:
        envelope, main_execution, authority = self._route_decision_fixture()
        no_eligible = copy.deepcopy(envelope)
        no_eligible["selection_evidence"]["primary_candidates"][0][
            "eligible"
        ] = False
        no_eligible["selection_evidence"]["primary_candidates"][0][
            "rejection_reasons"
        ] = ["tool ownership is unresolved"]
        no_eligible["selection_evidence"]["eligible_primary_count"] = 0
        self.assertTrue(no_eligible["route_once"])
        errors = self._validate_route_decision(
            no_eligible,
            main_execution,
            authority,
        )
        self.assertTrue(
            any("route_once" in error and "eligible primary" in error for error in errors),
            errors,
        )

    def test_professional_review_risk_matrix_is_core_owned_and_level_uniform(
        self,
    ) -> None:
        expected_dimensions = [
            "correctness-invariants",
            "authority-security-privacy",
            "failure-recovery-concurrency",
            "performance-resources",
            "contracts-data-consumers",
            "tests-evidence",
            "maintainability-structure",
            "operations-documentation-release",
        ]
        matrix = CORE_CONTRACTS["review_discipline_contract"][
            "professional_risk_matrix"
        ]
        self.assertEqual(
            {
                "registry": "professional-skills.yaml",
                "field": "role_support",
                "contains": "review-agent",
            },
            matrix["registry_selector"],
        )
        self.assertEqual(expected_dimensions, matrix["dimensions"])
        self.assertEqual(
            {level: expected_dimensions for level in ("L1", "L2", "L3", "L4", "L5")},
            matrix["level_dimensions"],
        )
        self.assertEqual(
            ["verified", "finding", "not-applicable", "delegated", "blocked"],
            matrix["statuses"],
        )

    def test_review_discipline_contract_is_core_owned_and_level_uniform(self) -> None:
        expected_dimensions = [
            "actual-latest-diff",
            "every-changed-file",
            "observable-acceptance",
            "validation-freshness",
            "regression-mechanism",
            "negative-boundary-behavior",
            "ownership-placement",
            "unnecessary-scope",
            "unverified-scope",
            "residual-risk",
        ]
        contract = CORE_CONTRACTS["review_discipline_contract"]
        self.assertEqual("every implementation or repair review at L1-L5", contract["applies_to"])
        self.assertEqual(expected_dimensions, contract["base_dimensions"])
        self.assertEqual(
            {level: expected_dimensions for level in ("L1", "L2", "L3", "L4", "L5")},
            contract["level_base_dimensions"],
        )
        self.assertIn(
            contract["profile_capability_id"],
            CORE_CONTRACTS["profile_contract"]["role_capabilities"]["review-agent"]
            ["required_capability_ids"],
        )

    def test_adaptive_testing_contract_is_closed(self) -> None:
        contract = CORE_CONTRACTS["implementation_discipline_contract"]
        self.assertEqual(2, contract["schema_version"])
        adaptive = contract["adaptive_testing_contract"]
        self.assertEqual("guard-g-adaptive-testing", adaptive["guard_id"])
        self.assertEqual(
            [
                "test-first",
                "test-after",
                "existing-proof-only",
                "non-test-validation",
            ],
            adaptive["approaches"],
        )
        self.assertEqual(
            ["environment", "fixture", "import", "syntax", "unrelated"],
            adaptive["invalid_red_failure_classes"],
        )
        mutation = copy.deepcopy(CORE_CONTRACTS)
        mutation["implementation_discipline_contract"][
            "adaptive_testing_contract"
        ]["high_risk_downgrade"] = "allowed"
        self.assertTrue(
            any(
                "closed Core Guard G" in error
                for error in validate_core_contracts(mutation)
            )
        )

    def test_conditional_test_evidence_contract_is_closed(self) -> None:
        expected = {
            "schema_version": 1,
            "claim_values": [
                "test-approach-selected",
                "red-proof",
                "green-proof",
            ],
            "record_only_when_applicable": True,
            "separate_stage": False,
            "unavailable_proof_rule": "never-fabricate",
            "projection_targets": list(CONDITIONAL_TEST_EVIDENCE_TARGETS),
            "projection_text": CONDITIONAL_TEST_EVIDENCE_PROJECTION,
        }
        self.assertEqual(
            expected,
            CORE_CONTRACTS["visible_evidence_contract"][
                "conditional_test_evidence"
            ],
        )

        mutations: list[dict[str, object]] = []

        missing_semantic = copy.deepcopy(CORE_CONTRACTS)
        del missing_semantic["visible_evidence_contract"][
            "conditional_test_evidence"
        ]["record_only_when_applicable"]
        mutations.append(missing_semantic)

        weakened_projection = copy.deepcopy(CORE_CONTRACTS)
        weakened_projection["visible_evidence_contract"][
            "conditional_test_evidence"
        ]["projection_text"] = CONDITIONAL_TEST_EVIDENCE_PROJECTION.replace(
            "Never fabricate unavailable proof.",
            "Unavailable proof may be inferred.",
        )
        self.assertNotEqual(
            CONDITIONAL_TEST_EVIDENCE_PROJECTION,
            weakened_projection["visible_evidence_contract"][
                "conditional_test_evidence"
            ]["projection_text"],
        )
        mutations.append(weakened_projection)

        duplicate_target = copy.deepcopy(CORE_CONTRACTS)
        duplicate_target["visible_evidence_contract"][
            "conditional_test_evidence"
        ]["projection_targets"].append("implementation-handoff-template.md")
        mutations.append(duplicate_target)

        unsupported_required_claim = copy.deepcopy(CORE_CONTRACTS)
        unsupported_required_claim["visible_evidence_contract"][
            "conditional_test_evidence"
        ]["unavailable_proof_rule"] = "allow-placeholder-proof"
        mutations.append(unsupported_required_claim)

        unsupported_mandatory_field = copy.deepcopy(CORE_CONTRACTS)
        unsupported_mandatory_field["visible_evidence_contract"][
            "conditional_test_evidence"
        ]["mandatory_test_fields"] = ["coverage-proof"]
        mutations.append(unsupported_mandatory_field)

        for index, mutation in enumerate(mutations):
            with self.subTest(index=index):
                errors = validate_core_contracts(mutation)
                self.assertTrue(
                    any("conditional test evidence" in error.casefold() for error in errors),
                    errors,
                )

    def test_authoritative_model_passes(self) -> None:
        self.assertEqual([], validate_core_contracts(copy.deepcopy(CORE_CONTRACTS)))

    def test_execution_level_user_constants_are_locked(self) -> None:
        mutations: list[dict[str, object]] = []

        default_level = copy.deepcopy(CORE_CONTRACTS)
        default_level["execution_level_contract"]["default_level"] = "L2"
        mutations.append(default_level)

        automatic_default = copy.deepcopy(CORE_CONTRACTS)
        automatic_default["execution_level_contract"]["formula"][
            "automatic_default_level"
        ] = "L2"
        mutations.append(automatic_default)

        requested_values = copy.deepcopy(CORE_CONTRACTS)
        requested_values["execution_level_contract"]["requested_values"] = [
            "unspecified",
            "L1",
        ]
        mutations.append(requested_values)

        requested_base = copy.deepcopy(CORE_CONTRACTS)
        requested_base["execution_level_contract"]["formula"]["requested_base"][
            "L5"
        ] = "L4"
        mutations.append(requested_base)

        l5_review = copy.deepcopy(CORE_CONTRACTS)
        l5 = next(
            level
            for level in l5_review["execution_level_contract"]["levels"]
            if level["id"] == "L5"
        )
        l5["obligations"].remove("independent implementation review")
        mutations.append(l5_review)

        for model in mutations:
            with self.subTest():
                self.assertTrue(validate_core_contracts(model))

    def test_execution_formula_covers_l1_through_l5_and_historical_floors(self) -> None:
        triggers, l2 = _execution_evidence()
        table = (
            ("L1", None, "true", "L1", "L1", "L1", "L2", "L1"),
            ("unspecified", None, "true", "L1", "L1", "L1", "L2", "L2"),
            ("unspecified", None, "false", "L1", "L1", "L1", "L3", "L3"),
            ("unspecified", "multi-task-or-integration-ownership", "true", "L1", "L1", "L3", "L3", "L3"),
            ("unspecified", "authorization-security-privacy-secret", "true", "L1", "L1", "L4", "L4", "L4"),
            ("L5", None, "true", "L1", "L1", "L1", "L2", "L5"),
            ("L1", None, "true", "L4", "L4", "L1", "L2", "L4"),
        )
        for requested, trigger, l2_status, historical_floor, historical_effective, floor, automatic, effective in table:
            with self.subTest(requested=requested, trigger=trigger, l2=l2_status):
                triggers, l2 = _execution_evidence(
                    matched_trigger=trigger,
                    l2_status=l2_status,
                )
                result = compute_execution_level(
                    requested=requested,
                    trigger_evaluations=triggers,
                    l2_evaluations=l2,
                    prior_historical_max_floor=historical_floor,
                    prior_historical_max_effective=historical_effective,
                )
                self.assertEqual(floor, result["computed_floor"])
                self.assertEqual(automatic, result["automatic_level"])
                self.assertEqual(effective, result["effective_level"])
                self.assertEqual(
                    max((floor, historical_floor), key=lambda level: int(level[1:])),
                    result["mandatory_floor"],
                )
                self.assertEqual(result["mandatory_floor"], result["next_historical_floor"])
                self.assertEqual(effective, result["next_historical_effective"])

    def test_valid_l2_and_l3_do_not_inherit_integrity_fallback_l4(self) -> None:
        for l2_status, expected in (("true", "L2"), ("false", "L3")):
            with self.subTest(l2_status=l2_status):
                triggers, l2 = _execution_evidence(l2_status=l2_status)
                result = compute_execution_level(
                    requested="unspecified",
                    trigger_evaluations=triggers,
                    l2_evaluations=l2,
                    prior_historical_max_floor="L1",
                    prior_historical_max_effective="L1",
                )
                self.assertEqual(expected, result["effective_level"])
                self.assertNotEqual("L4", result["effective_level"])

    def test_every_closed_trigger_has_positive_negative_and_anchor_guards(self) -> None:
        registry = CORE_CONTRACTS["execution_level_contract"]["trigger_registry"]
        for index, row in enumerate(registry):
            for field in ("positive_predicate", "anti_trigger", "source_anchor"):
                with self.subTest(trigger=row["id"], field=field):
                    mutation = copy.deepcopy(CORE_CONTRACTS)
                    mutation["execution_level_contract"]["trigger_registry"][index][field] = ""
                    errors = validate_core_contracts(mutation)
                    self.assertTrue(any(field in error for error in errors), errors)

    def test_each_trigger_computes_its_declared_floor(self) -> None:
        for row in CORE_CONTRACTS["execution_level_contract"]["trigger_registry"]:
            with self.subTest(trigger=row["id"]):
                triggers, l2 = _execution_evidence(matched_trigger=row["id"])
                result = compute_execution_level(
                    requested="unspecified",
                    trigger_evaluations=triggers,
                    l2_evaluations=l2,
                )
                self.assertEqual(row["floor"], result["computed_floor"])
                triggers[row["id"]]["status"] = "not_matched"
                result = compute_execution_level(
                    requested="unspecified",
                    trigger_evaluations=triggers,
                    l2_evaluations=l2,
                )
                self.assertNotEqual(row["floor"], result["computed_floor"])
                triggers[row["id"]]["source_anchor"] = ""
                with self.assertRaisesRegex(ExecutionLevelError, "source anchor"):
                    compute_execution_level(
                        requested="unspecified",
                        trigger_evaluations=triggers,
                        l2_evaluations=l2,
                    )

    def test_l2_false_or_unknown_denies_l2(self) -> None:
        for row in CORE_CONTRACTS["execution_level_contract"]["l2_eligibility"]:
            for denied in ("false", "unknown"):
                with self.subTest(predicate=row["id"], status=denied):
                    triggers, l2 = _execution_evidence()
                    l2[row["id"]]["status"] = denied
                    result = compute_execution_level(
                        requested="unspecified",
                        trigger_evaluations=triggers,
                        l2_evaluations=l2,
                    )
                    self.assertEqual("L3", result["automatic_level"])
                    self.assertEqual("L3", result["effective_level"])
                    l2[row["id"]]["source_anchor"] = ""
                    with self.assertRaisesRegex(ExecutionLevelError, "source anchor"):
                        compute_execution_level(
                            requested="unspecified",
                            trigger_evaluations=triggers,
                            l2_evaluations=l2,
                        )

    def test_core_trigger_policy_mutation_projects_without_validator_sync(self) -> None:
        model = copy.deepcopy(CORE_CONTRACTS)
        execution = model["execution_level_contract"]
        changed = execution["trigger_registry"][0]
        changed["positive_predicate"] = "mutated policy evidence is present"
        self.assertEqual([], validate_core_contracts(model))
        original_hash = execution_level_runtime_payload_sha256()
        projection = execution_level_runtime_reference(model)
        self.assertIn('"positive_predicate":"mutated policy evidence is present"', projection)
        self.assertNotEqual(original_hash, execution_level_runtime_payload_sha256(model))
        router = execution_level_router_block(model)
        self.assertNotIn("mutated policy evidence is present", router)
        triggers = {
            row["id"]: {
                "status": "matched" if row["id"] == changed["id"] else "not_matched",
                "evidence_kind": "analysis_handoff",
                "source_anchor": f"handoff:{row['id']}",
                "plausible_critical": False,
            }
            for row in execution["trigger_registry"]
        }
        l2 = {
            row["id"]: {
                "status": "true",
                "evidence_kind": "analysis_handoff",
                "source_anchor": f"handoff:{row['id']}",
            }
            for row in execution["l2_eligibility"]
        }
        result = compute_execution_level(
            requested="unspecified",
            trigger_evaluations=triggers,
            l2_evaluations=l2,
            contract=execution,
        )
        self.assertEqual("L3", result["computed_floor"])

    def test_runtime_reference_is_canonical_closed_and_projection_independent(self) -> None:
        source = (REFERENCE_ROOT / "execution-level-contract.md").read_text(
            encoding="utf-8"
        )
        self.assertEqual(execution_level_runtime_reference(), source)
        self.assertEqual([], execution_level_runtime_reference_errors(source))
        payload = execution_level_runtime_payload()
        self.assertNotIn("projection", payload)
        self.assertEqual(
            hashlib.sha256(execution_level_runtime_payload_bytes()).hexdigest(),
            execution_level_runtime_payload_sha256(),
        )
        mutated = copy.deepcopy(CORE_CONTRACTS)
        projection = mutated["execution_level_contract"]["projection"]
        projection["prompt"]["id"] = "mutated-prompt-metadata"
        projection["router"]["path"] = "mutated/router.md"
        projection["runtime_reference"]["id"] = "mutated-runtime-metadata"
        self.assertEqual(
            execution_level_runtime_payload_bytes(),
            execution_level_runtime_payload_bytes(mutated),
        )

    def test_runtime_reference_rejects_structure_schema_ids_controls_and_unicode(self) -> None:
        source = execution_level_runtime_reference()
        payload_text = execution_level_runtime_payload_bytes().decode("utf-8")

        def replace_payload(value: str) -> str:
            return source.replace(payload_text, value, 1)

        extra = execution_level_runtime_payload()
        extra["extra"] = True
        duplicate = execution_level_runtime_payload()
        duplicate["trigger_registry"][1]["id"] = duplicate["trigger_registry"][0]["id"]
        controlled = execution_level_runtime_payload()
        controlled["default_level"] = "L3\u0001"
        mutations = (
            source.replace("<!-- BEGIN CHANGEFORGE CORE RUNTIME REFERENCE", "<!-- MISSING", 1),
            replace_payload("not-json"),
            replace_payload(json.dumps(extra, sort_keys=True, separators=(",", ":"))),
            replace_payload(json.dumps(duplicate, sort_keys=True, separators=(",", ":"))),
            replace_payload(json.dumps(controlled, sort_keys=True, separators=(",", ":"))),
        )
        for mutation in mutations:
            with self.subTest():
                self.assertTrue(execution_level_runtime_reference_errors(mutation))

        invalid_unicode = copy.deepcopy(CORE_CONTRACTS)
        invalid_unicode["execution_level_contract"]["trigger_registry"][0][
            "positive_predicate"
        ] = "invalid-\ud800"
        with self.assertRaisesRegex(ValueError, "Unicode surrogate"):
            execution_level_runtime_payload_bytes(invalid_unicode)
        extra_core = copy.deepcopy(CORE_CONTRACTS)
        extra_core["execution_level_contract"]["extra"] = True
        with self.assertRaisesRegex(ValueError, "schema is invalid"):
            execution_level_runtime_payload(extra_core)

    def test_integrity_fallback_is_fixed_monotonic_and_never_partial(self) -> None:
        cases = (
            ("unspecified", "L1", "L1", "L4", "L4"),
            ("L1", "L4", "L4", "L4", "L4"),
            ("L5", "L4", "L4", "L4", "L5"),
            ("unknown", "L5", "L5", "L5", "L5"),
        )
        for requested, prior_floor, prior_effective, floor, effective in cases:
            with self.subTest(requested=requested):
                result = execution_level_integrity_fallback(
                    requested=requested,
                    prior_historical_max_floor=prior_floor,
                    prior_historical_max_effective=prior_effective,
                )
                self.assertEqual(floor, result["computed_floor"])
                self.assertEqual(effective, result["effective_level"])
                self.assertEqual("blocked", result["edit_status"])
                self.assertFalse(result["partial_computation"])
                self.assertIn("dispatch-read-only-diagnosis", result["allowed_outcomes"])
                self.assertEqual(
                    ["implementation", "validation", "release", "router"],
                    result["forbidden_actions"],
                )

    def test_runtime_projection_schema_requires_effective_input_and_closed_metadata(self) -> None:
        for mutation in ("wrong-input", "extra-field"):
            with self.subTest(mutation=mutation):
                model = copy.deepcopy(CORE_CONTRACTS)
                router = model["execution_level_contract"]["projection"]["router"]
                if mutation == "wrong-input":
                    router["input_field"] = "computed_floor"
                else:
                    router["producer"] = "main"
                errors = validate_core_contracts(model)
                self.assertTrue(
                    any("projections must bind" in error for error in errors),
                    errors,
                )

    def test_critical_unknown_floors_l4_and_blocks_editing(self) -> None:
        trigger_id = "unknown-critical-boundary"
        triggers, l2 = _execution_evidence(unknown_trigger=trigger_id)
        result = compute_execution_level(
            requested="L1",
            trigger_evaluations=triggers,
            l2_evaluations=l2,
        )
        self.assertEqual("L4", result["computed_floor"])
        self.assertEqual("L4", result["effective_level"])
        self.assertEqual("blocked", result["edit_status"])
        self.assertIn(trigger_id, result["level_basis"]["unresolved"])

    def test_unknown_trigger_or_target_source_evidence_is_invalid(self) -> None:
        triggers, l2 = _execution_evidence()
        triggers["invented-trigger"] = triggers.pop(next(iter(triggers)))
        with self.assertRaisesRegex(ExecutionLevelError, "closed registry"):
            compute_execution_level(
                requested="unspecified",
                trigger_evaluations=triggers,
                l2_evaluations=l2,
            )
        triggers, l2 = _execution_evidence()
        triggers[next(iter(triggers))]["evidence_kind"] = "target_source"
        with self.assertRaisesRegex(ExecutionLevelError, "invalid evidence kind"):
            compute_execution_level(
                requested="unspecified",
                trigger_evaluations=triggers,
                l2_evaluations=l2,
            )

    def test_scope_lineage_rejects_same_task_relabel_and_lowering_bypasses(self) -> None:
        levels = {
            "previous_mandatory_floor": "L4",
            "previous_effective_level": "L4",
            "previous_historical_max_floor": "L4",
            "previous_historical_max_effective": "L4",
            "current_mandatory_floor": "L4",
            "current_effective_level": "L4",
            "current_historical_max_floor": "L4",
            "current_historical_max_effective": "L4",
        }
        cases = (
            {
                **levels,
                "previous_task_id": "task-a",
                "previous_scope_lineage": "root/a",
                "current_task_id": "task-a",
                "current_scope_lineage": "root/a/child",
                "scope_change": "same",
                "lowering_requested": False,
                "strict_narrowing_proof": False,
            },
            {
                **levels,
                "previous_task_id": "task-a",
                "previous_scope_lineage": "root/a",
                "current_task_id": "task-a",
                "current_scope_lineage": "root/a",
                "scope_change": "narrowed",
                "lowering_requested": True,
                "strict_narrowing_proof": True,
            },
            {
                **levels,
                "previous_task_id": "task-a",
                "previous_scope_lineage": "root/a",
                "current_task_id": "task-b",
                "current_scope_lineage": "root/other",
                "scope_change": "narrowed",
                "lowering_requested": True,
                "strict_narrowing_proof": True,
            },
            {
                **levels,
                "previous_task_id": "task-a",
                "previous_scope_lineage": "root/a",
                "current_task_id": "task-b",
                "current_scope_lineage": "root/a/child",
                "scope_change": "expanded",
                "lowering_requested": True,
                "strict_narrowing_proof": True,
            },
        )
        for case in cases:
            with self.subTest(case=case):
                self.assertTrue(execution_scope_transition_errors(**case))
        self.assertEqual(
            [],
            execution_scope_transition_errors(
                **levels,
                previous_task_id="task-a",
                previous_scope_lineage="root/a",
                current_task_id="task-b",
                current_scope_lineage="root/a/child",
                scope_change="narrowed",
                lowering_requested=True,
                strict_narrowing_proof=True,
            ),
        )
        fake_descent = {
            **levels,
            "current_mandatory_floor": "L1",
            "current_effective_level": "L1",
            "current_historical_max_floor": "L2",
            "current_historical_max_effective": "L2",
        }
        errors = execution_scope_transition_errors(
            **fake_descent,
            previous_task_id="task-a",
            previous_scope_lineage="root/a",
            current_task_id="task-a",
            current_scope_lineage="root/a",
            scope_change="same",
            lowering_requested=False,
            strict_narrowing_proof=False,
        )
        self.assertTrue(any("cannot lower" in error for error in errors), errors)

    def test_lightweight_evidence_ledger_requires_current_fresh_closure(self) -> None:
        fields = CORE_CONTRACTS["visible_evidence_contract"]["fields"]
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
        row = {
            "Claim": "validation-passed",
            "Owner": "task-agent",
            "Artifact": "targeted test result",
            "Command": "python3 -m unittest tests.test_target",
            "Result": "passed",
            "Freshness": 2,
            "Scope": "changed module",
            "Proof Limit": "targeted validation only",
            "State": "current",
        }
        self.assertEqual(list(row), fields)
        self.assertEqual(
            [],
            evidence_ledger_errors(
                [row],
                task_id="task-lightweight-ledger",
                owner="task-agent",
                required_claims=["validation-passed"],
                required_freshness_marker=2,
                latest_material_edit_marker=2,
                completion_status="completed",
            ),
        )

        stale = copy.deepcopy(row)
        stale["Freshness"] = 1
        stale_errors = evidence_ledger_errors(
            [stale],
            task_id="task-lightweight-ledger",
            owner="task-agent",
            required_claims=["validation-passed"],
            required_freshness_marker=2,
            latest_material_edit_marker=2,
            completion_status="completed",
        )
        self.assertTrue(any("stale current" in error for error in stale_errors), stale_errors)

        noncurrent = copy.deepcopy(row)
        noncurrent["State"] = "superseded"
        noncurrent_errors = evidence_ledger_errors(
            [noncurrent],
            task_id="task-lightweight-ledger",
            owner="task-agent",
            required_claims=["validation-passed"],
            required_freshness_marker=2,
            latest_material_edit_marker=2,
            completion_status="completed",
        )
        self.assertTrue(
            any("superseded or invalid" in error for error in noncurrent_errors),
            noncurrent_errors,
        )

        reintroduced = {"Evidence ID": "legacy", **row}
        legacy_errors = evidence_ledger_errors(
            [reintroduced],
            task_id="task-lightweight-ledger",
            owner="task-agent",
            required_claims=[],
            required_freshness_marker=0,
            latest_material_edit_marker=None,
            completion_status="in_progress",
        )
        self.assertTrue(any("exact ordered fields" in error for error in legacy_errors), legacy_errors)

    def test_public_task_extension_core_decision_schema_is_closed(self) -> None:
        public = CORE_CONTRACTS["execution_level_contract"]["projection"][
            "public_task_extension"
        ]
        self.assertEqual(
            {
                "version": "execution-level/v1",
                "ordered_labels": ["Level", "Basis", "L5 Evidence"],
                "line_fields": {
                    "Level": [
                        "requested",
                        "automatic",
                        "default",
                        "effective",
                        "edit",
                    ],
                    "Basis": ["source", "triggers", "l2", "unresolved"],
                    "L5 Evidence": ["when", "requires"],
                },
            },
            public,
        )
        for mutation in (
            ("label",),
            ("legacy",),
            ("version",),
        ):
            with self.subTest(mutation=mutation[0]):
                model = copy.deepcopy(CORE_CONTRACTS)
                candidate = model["execution_level_contract"]["projection"][
                    "public_task_extension"
                ]
                if mutation[0] == "label":
                    candidate["ordered_labels"].reverse()
                elif mutation[0] == "legacy":
                    candidate["ordered_labels"].append("Identity")
                    candidate["line_fields"]["Identity"] = ["digest", "path"]
                else:
                    candidate["version"] = "execution-level/v2"
                errors = validate_core_contracts(model)
                self.assertTrue(
                    any("public task extension" in error for error in errors), errors
                )

    def test_public_task_extension_projects_all_fixtures_within_lightweight_budget(self) -> None:
        document = json.loads(AGENT_LIGHT_CASES.read_text(encoding="utf-8"))
        encoded_count = 0
        forbidden = (
            "Projection:",
            "Claims:",
            "Gaps:",
            "Identity:",
            "History:",
            "digest",
            "manifest",
            "validation_path",
        )
        for case in (
            *document["cases"],
            *document["scheduling_cases"],
            *document["utility_cases"],
        ):
            for step in case["steps"]:
                extension = step.get("fixture_capsule", {}).get(
                    "execution_level_extension"
                )
                if extension is None:
                    continue
                encoded_count += 1
                encoded = encode_public_task_extension(extension)
                decoded = decode_public_task_extension(encoded)
                expected_labels = ["Level", "Basis"]
                if (
                    extension["effective_level"] == "L5"
                    or extension["requested_level"] == "L5"
                ):
                    expected_labels.append("L5 Evidence")
                self.assertEqual(
                    expected_labels,
                    [line.split(": ", 1)[0] for line in encoded.splitlines()],
                )
                for term in forbidden:
                    self.assertNotIn(term, encoded)
                self.assertNotIn("default=", encoded)
                if extension["requested_level"] == "unspecified":
                    self.assertNotIn("requested=", encoded.splitlines()[0])
                else:
                    self.assertIn(
                        f"requested={extension['requested_level']}",
                        encoded.splitlines()[0],
                    )
                self.assertEqual("execution-level/v1", decoded["version"])
                self.assertEqual(
                    extension["requested_level"], decoded["level"]["requested"]
                )
                self.assertEqual(
                    extension["automatic_level"], decoded["level"]["automatic"]
                )
                self.assertEqual(
                    extension["effective_level"], decoded["level"]["effective"]
                )
                self.assertEqual(
                    extension["level_basis"]["edit_status"],
                    decoded["level"]["edit"],
                )
                if decoded["basis"]["triggers"] or decoded["basis"]["l2"]:
                    self.assertIn("@", encoded.splitlines()[1])
                if "L5 Evidence" not in expected_labels:
                    self.assertNotIn("l5_evidence", decoded)
                self.assertLessEqual(
                    count_o200k_base_tokens(encoded),
                    180,
                    (case["id"], count_o200k_base_tokens(encoded)),
                )
        self.assertEqual(28, encoded_count)

    def test_explicit_l1_is_a_base_not_an_automatic_or_historical_override(self) -> None:
        document = json.loads(AGENT_LIGHT_CASES.read_text(encoding="utf-8"))
        dispatches = [
            step
            for case in document["cases"]
            for step in case["steps"]
            if isinstance(step.get("fixture_capsule", {}).get("execution_level_extension"), dict)
        ]

        eligible_step = next(
            step
            for step in dispatches
            if step["fixture_capsule"]["execution_level_extension"][
                "automatic_level"
            ]
            == "L2"
            and step["fixture_capsule"]["execution_level_extension"][
                "prior_historical_max_floor"
            ]
            == "L1"
            and step["fixture_capsule"]["execution_level_extension"][
                "prior_historical_max_effective"
            ]
            == "L1"
        )
        eligible = copy.deepcopy(
            eligible_step["fixture_capsule"]["execution_level_extension"]
        )
        eligible["requested_level"] = "L1"
        eligible["effective_level"] = "L2"
        encoded = encode_public_task_extension(eligible)
        decoded = decode_public_task_extension(encoded)
        self.assertEqual("L1", decoded["level"]["requested"])
        self.assertEqual("L2", decoded["level"]["effective"])

        eligible_migration_step = copy.deepcopy(eligible_step)
        eligible_migration_step["fixture_capsule"][
            "execution_level_extension"
        ] = eligible
        self.assertEqual(
            [],
            execution_level_migration_errors(
                eligible_migration_step["fixture_capsule"],
                lifecycle_status="in_progress",
                next_action="edit",
                step=eligible_migration_step,
            ),
        )

        automatic_l3_step = next(
            step
            for step in dispatches
            if step["fixture_capsule"]["execution_level_extension"][
                "automatic_level"
            ]
            == "L3"
        )
        security_case = next(
            case for case in document["cases"] if case["id"] == "security-ssrf-boundary"
        )
        security_step = next(
            step
            for step in security_case["steps"]
            if step.get("fixture_capsule", {}).get("contract_type") == "task"
        )

        for label, source_step, floor in (
            ("automatic-l3", automatic_l3_step, "L3"),
            ("security-l4", security_step, "L4"),
        ):
            with self.subTest(case=label):
                extension = copy.deepcopy(
                    source_step["fixture_capsule"]["execution_level_extension"]
                )
                extension["requested_level"] = "L1"
                extension["effective_level"] = "L1"
                with self.assertRaisesRegex(
                    FixtureCapsuleError,
                    "below its decision floor",
                ):
                    encode_public_task_extension(extension)

                migration_step = copy.deepcopy(source_step)
                migration_step["fixture_capsule"][
                    "execution_level_extension"
                ] = extension
                errors = execution_level_migration_errors(
                    migration_step["fixture_capsule"],
                    lifecycle_status="in_progress",
                    next_action="edit",
                    step=migration_step,
                )
                self.assertTrue(
                    any("below its decision floor" in error for error in errors),
                    errors,
                )

                extension["effective_level"] = floor
                valid_wire = encode_public_task_extension(extension)
                downgraded_wire = valid_wire.replace(
                    f"effective={floor}", "effective=L1", 1
                )
                self.assertNotEqual(valid_wire, downgraded_wire)
                fallback = decode_public_task_extension(downgraded_wire)
                self.assertEqual("blocked", fallback["integrity_status"])
                self.assertGreaterEqual(
                    {"L1": 1, "L2": 2, "L3": 3, "L4": 4, "L5": 5}[
                        fallback["effective_level"]
                    ],
                    4,
                )

        trusted_prior = copy.deepcopy(eligible)
        trusted_prior["prior_historical_max_floor"] = "L4"
        trusted_prior["prior_historical_max_effective"] = "L4"
        with self.assertRaisesRegex(
            FixtureCapsuleError,
            "below its decision floor",
        ):
            encode_public_task_extension(trusted_prior)

    def test_public_task_extension_does_not_require_or_emit_legacy_internal_fields(self) -> None:
        task = _first_fixture_step("task")
        full = copy.deepcopy(task["fixture_capsule"]["execution_level_extension"])
        encoded = encode_public_task_extension(full)
        minimal = {
            "requested_level": full["requested_level"],
            "automatic_level": full["automatic_level"],
            "effective_level": full["effective_level"],
            "level_basis": full["level_basis"],
        }
        self.assertEqual(encoded, encode_public_task_extension(minimal))

        changed_legacy = copy.deepcopy(full)
        changed_legacy["validation_claim_manifest"] = {"retired": True}
        changed_legacy["distinct_gap_manifest"] = {"retired": True}
        changed_legacy["validation_identity_manifest"] = {"retired": True}
        changed_legacy["prior_historical_max_floor"] = "L5"
        changed_legacy["prior_historical_max_effective"] = "L5"
        changed_legacy["historical_max_floor"] = "L5"
        changed_legacy["historical_max_effective"] = "L5"
        with self.assertRaisesRegex(
            FixtureCapsuleError,
            "below its decision floor",
        ):
            encode_public_task_extension(changed_legacy)

        changed_legacy["effective_level"] = "L5"
        historical_l5 = encode_public_task_extension(changed_legacy)
        self.assertEqual(
            "L5",
            decode_public_task_extension(historical_l5)["level"]["effective"],
        )
        for retired in (
            "Claims:",
            "Gaps:",
            "Identity:",
            "History:",
            "prior_historical",
            "historical_max",
            "manifest",
        ):
            with self.subTest(retired=retired):
                self.assertNotIn(retired, historical_l5)

    def test_public_task_extension_projects_nondefault_decisions(self) -> None:
        task = _first_fixture_step("task")
        base = copy.deepcopy(task["fixture_capsule"]["execution_level_extension"])

        unknown_critical = copy.deepcopy(base)
        trigger = unknown_critical["level_basis"]["trigger_evaluations"][-1]
        trigger["status"] = "unknown"
        trigger["plausible_critical"] = True
        unknown_critical = _recompute_fixture_extension(unknown_critical)
        encoded = encode_public_task_extension(unknown_critical)
        decoded = decode_public_task_extension(encoded)
        self.assertEqual(
            ["unknown-critical-boundary"], decoded["basis"]["triggers"]
        )
        self.assertEqual("L4", decoded["level"]["effective"])
        self.assertEqual("blocked", decoded["level"]["edit"])

        unknown_l2 = copy.deepcopy(base)
        unknown_l2["level_basis"]["l2_eligibility"][0]["status"] = "unknown"
        unknown_l2 = _recompute_fixture_extension(unknown_l2)
        decoded = decode_public_task_extension(
            encode_public_task_extension(unknown_l2)
        )
        self.assertEqual(["single-bounded-owner"], decoded["basis"]["l2"])
        self.assertEqual(
            ["single-bounded-owner"], decoded["basis"]["unresolved"]
        )
        self.assertEqual("L3", decoded["level"]["automatic"])

        explicit_l5 = copy.deepcopy(base)
        explicit_l5["requested_level"] = "L5"
        explicit_l5 = _recompute_fixture_extension(explicit_l5)
        decoded = decode_public_task_extension(
            encode_public_task_extension(explicit_l5)
        )
        self.assertEqual("L5", decoded["level"]["effective"])
        self.assertEqual(
            [
                "independent pre-implementation review",
                "strong safety and applicability proof",
                "declared-scope comprehensive negative and failure proof",
                "exhaustive final review",
            ],
            decoded["l5_evidence"]["requires"],
        )

    def test_public_task_extension_roundtrips_mixed_trigger_and_l2_basis(self) -> None:
        task = _first_fixture_step("task")
        base = copy.deepcopy(task["fixture_capsule"]["execution_level_extension"])

        noncritical_unknown = copy.deepcopy(base)
        unknown_trigger = noncritical_unknown["level_basis"]["trigger_evaluations"][1]
        unknown_trigger["status"] = "unknown"
        unknown_trigger["plausible_critical"] = False
        noncritical_unknown = _recompute_fixture_extension(noncritical_unknown)
        decoded = decode_public_task_extension(
            encode_public_task_extension(noncritical_unknown)
        )
        self.assertEqual([unknown_trigger["id"]], decoded["basis"]["triggers"])
        self.assertEqual([unknown_trigger["id"]], decoded["basis"]["unresolved"])
        self.assertEqual("L2", decoded["level"]["automatic"])
        self.assertEqual("allowed", decoded["level"]["edit"])

        mixed = copy.deepcopy(base)
        trigger_rows = mixed["level_basis"]["trigger_evaluations"]
        l2_rows = mixed["level_basis"]["l2_eligibility"]
        trigger_rows[0]["status"] = "matched"
        trigger_rows[1]["status"] = "unknown"
        trigger_rows[1]["plausible_critical"] = False
        l2_rows[0]["status"] = "false"
        l2_rows[1]["status"] = "unknown"
        mixed = _recompute_fixture_extension(mixed)
        encoded = encode_public_task_extension(mixed)
        self.assertTrue(encoded.splitlines()[1].startswith("Basis: t="))
        self.assertIn("; l=", encoded.splitlines()[1])
        self.assertIn("; u=", encoded.splitlines()[1])
        self.assertNotIn("triggers=", encoded)
        self.assertNotIn("unresolved=", encoded)
        decoded = decode_public_task_extension(encoded)
        expected_triggers = [trigger_rows[0]["id"], trigger_rows[1]["id"]]
        expected_l2 = [l2_rows[0]["id"], l2_rows[1]["id"]]
        expected_unresolved = [trigger_rows[1]["id"], l2_rows[1]["id"]]
        self.assertEqual(expected_triggers, decoded["basis"]["triggers"])
        self.assertEqual(expected_l2, decoded["basis"]["l2"])
        self.assertEqual(expected_unresolved, decoded["basis"]["unresolved"])
        self.assertEqual("L3", decoded["level"]["automatic"])
        self.assertEqual("allowed", decoded["level"]["edit"])
        self.assertNotIn(trigger_rows[2]["id"], decoded["basis"]["triggers"])
        self.assertIn(
            f"{trigger_rows[0]['evidence_kind']}:"
            f"{trigger_rows[0]['source_anchor']}",
            decoded["basis"]["source"],
        )

        evidence_alias = {
            "user_fact": "u",
            "analysis_handoff": "a",
        }[trigger_rows[0]["evidence_kind"]]
        trigger_bound = (
            f"{trigger_rows[0]['id']}@{evidence_alias}:"
            f"{trigger_rows[0]['source_anchor']}"
        )
        malformed = (
            encoded.replace(
                f'"{trigger_bound}"',
                f'"{trigger_bound}","{trigger_bound}"',
                1,
            ),
            encoded.replace(
                f"{trigger_rows[0]['id']}@",
                "unknown-schema-trigger@",
                1,
            ),
            encoded.replace(
                f"{evidence_alias}:{trigger_rows[0]['source_anchor']}",
                f"z:{trigger_rows[0]['source_anchor']}",
                1,
            ),
            encoded.replace(
                json.dumps(expected_unresolved, separators=(",", ":")),
                json.dumps(
                    ["unknown-schema-id", expected_unresolved[1]],
                    separators=(",", ":"),
                ),
                1,
            ),
        )
        for candidate in malformed:
            with self.subTest(candidate=candidate.splitlines()[1][:80]):
                fallback = decode_public_task_extension(candidate)
                self.assertEqual("blocked", fallback["integrity_status"])
                self.assertFalse(fallback["partial_computation"])

    def test_public_task_extension_malformed_input_retains_visible_l5(self) -> None:
        task = _first_fixture_step("task")
        base = copy.deepcopy(task["fixture_capsule"]["execution_level_extension"])

        explicit_l5 = copy.deepcopy(base)
        explicit_l5["requested_level"] = "L5"
        explicit_l5 = _recompute_fixture_extension(explicit_l5)

        historical_l5 = copy.deepcopy(base)
        historical_l5["prior_historical_max_floor"] = "L5"
        historical_l5["prior_historical_max_effective"] = "L5"
        historical_l5 = _recompute_fixture_extension(historical_l5)
        self.assertEqual("unspecified", historical_l5["requested_level"])
        self.assertEqual("L5", historical_l5["effective_level"])

        for extension in (explicit_l5, historical_l5):
            with self.subTest(requested=extension["requested_level"]):
                malformed = (
                    encode_public_task_extension(extension)
                    + "\nIdentity: digest=retired; path=retired"
                )
                fallback = decode_public_task_extension(malformed)
                self.assertEqual("blocked", fallback["integrity_status"])
                self.assertEqual("L5", fallback["effective_level"])
                self.assertFalse(fallback["partial_computation"])

        unsafe_level = (
            "Level: requested=L5; automatic=L2; effective=L5; "
            "effective=L5; edit=allowed\n"
            "Basis: triggers=[]; l2=[]; unresolved=[]"
        )
        fallback = decode_public_task_extension(unsafe_level)
        self.assertEqual("blocked", fallback["integrity_status"])
        self.assertEqual("L4", fallback["effective_level"])

    def test_public_task_extension_malformed_or_legacy_wire_fails_closed(self) -> None:
        task = _first_fixture_step("task")
        extension = copy.deepcopy(
            task["fixture_capsule"]["execution_level_extension"]
        )
        encoded = encode_public_task_extension(extension)
        lines = encoded.splitlines()
        malformed = (
            "not-a-public-extension",
            encoded.replace("automatic=L2", "automatic=L3", 1),
            "\n".join([lines[1], lines[0]]),
            encoded + "\nIdentity: digest=retired; path=retired",
            lines[0],
        )
        for candidate in malformed:
            with self.subTest(candidate=candidate[:40]):
                fallback = decode_public_task_extension(candidate)
                self.assertEqual("blocked", fallback["integrity_status"])
                self.assertFalse(fallback["partial_computation"])
                self.assertEqual(
                    ["implementation", "validation", "release", "router"],
                    fallback["forbidden_actions"],
                )

    def test_real_active_task_and_review_fixtures_are_migrated_at_exact_levels(self) -> None:
        document = json.loads(AGENT_LIGHT_CASES.read_text(encoding="utf-8"))
        counts = {"task": 0, "review": 0, "analysis": 0, "utility": 0}
        levels = {"L2": 0, "L3": 0, "L4": 0}
        for case in (
            *document["cases"],
            *document["scheduling_cases"],
            *document["utility_cases"],
        ):
            for step in case["steps"]:
                if step.get("action") != "dispatch":
                    continue
                payload = step["fixture_capsule"]
                contract_type = payload["contract_type"]
                counts[contract_type] += 1
                if contract_type not in {"task", "review"}:
                    self.assertNotIn("execution_level_extension", payload)
                    continue
                self.assertIn("execution_level_extension", payload)
                extension = payload["execution_level_extension"]
                levels[extension["effective_level"]] += 1
                rendered = render_fixture_capsule_payload(step, payload)
                self.assertEqual(
                    payload["canonical_sha256"],
                    hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
                )
                self.assertEqual(1, rendered.count("## Execution Level"))
                execution_body = VALIDATOR.extract_section_body(
                    rendered, "Execution Level"
                )
                self.assertIsNotNone(execution_body)
                assert execution_body is not None
                self.assertEqual(
                    encode_public_task_extension(extension),
                    execution_body,
                )
                self.assertNotIn("Requested Level:", execution_body)
                if contract_type == "task":
                    self.assertLess(
                        rendered.index("## Task ID"),
                        rendered.index("## Status"),
                    )
                    self.assertLess(
                        rendered.index("## Status"),
                        rendered.index("## Execution Level"),
                    )
                else:
                    self.assertLess(
                        rendered.index("## Task ID"),
                        rendered.index("## Execution Level"),
                    )
                self.assertLess(
                    rendered.index("## Execution Level"),
                    rendered.index("## Goal"),
                )
                for row in (
                    *extension["level_basis"]["trigger_evaluations"],
                    *extension["level_basis"]["l2_eligibility"],
                ):
                    self.assertTrue(
                        row["source_anchor"].startswith(f"fixture:{case['id']}:")
                    )
        self.assertEqual(
            {"task": 14, "review": 14, "analysis": 8, "utility": 2},
            counts,
        )
        self.assertEqual({"L2": 10, "L3": 7, "L4": 11}, levels)

    def test_extended_capsule_rejects_prose_or_fabricated_level_basis(self) -> None:
        task = _first_fixture_step("task")
        payload = task["fixture_capsule"]
        for mutation in ("prose", "fabricated"):
            with self.subTest(mutation=mutation):
                extended_payload = copy.deepcopy(payload)
                extension = extended_payload["execution_level_extension"]
                basis = extension["level_basis"]
                assert isinstance(basis, dict)
                if mutation == "prose":
                    basis["trigger_evaluations"] = ["all triggers checked"]
                else:
                    rows = basis["l2_eligibility"]
                    assert isinstance(rows, list)
                    rows[0]["status"] = "false"
                with self.assertRaisesRegex(
                    FixtureCapsuleError,
                    "cover the trigger registry|automatic_level is not canonical",
                ):
                    render_fixture_capsule_payload(task, extended_payload)

    def test_legacy_fixture_exemption_is_only_completed_read(self) -> None:
        task = _first_fixture_step("task")
        payload = copy.deepcopy(task["fixture_capsule"])
        payload.pop("execution_level_extension")
        for lifecycle, action in (
            ("in_progress", "read"),
            ("in_progress", "edit"),
            ("in_progress", "validation"),
            ("in_progress", "review"),
            ("completed", "edit"),
            ("completed", "validation"),
            ("completed", "review"),
        ):
            with self.subTest(lifecycle=lifecycle, action=action):
                self.assertTrue(
                    execution_level_migration_errors(
                        payload,
                        lifecycle_status=lifecycle,
                        next_action=action,
                    )
                )
        self.assertEqual(
            [],
            execution_level_migration_errors(
                payload,
                lifecycle_status="completed",
                next_action="read",
            ),
        )
        extended = copy.deepcopy(task["fixture_capsule"])
        self.assertEqual(
            [],
            execution_level_migration_errors(
                extended,
                lifecycle_status="in_progress",
                next_action="edit",
                step=task,
            ),
        )
        malformed_extensions: list[dict[str, object]] = []
        missing_value = copy.deepcopy(extended)
        missing_value["execution_level_extension"] = None
        malformed_extensions.append(missing_value)
        missing_decision = copy.deepcopy(extended)
        extension = missing_decision["execution_level_extension"]
        assert isinstance(extension, dict)
        del extension["automatic_level"]
        malformed_extensions.append(missing_decision)
        fabricated = copy.deepcopy(extended)
        extension = fabricated["execution_level_extension"]
        assert isinstance(extension, dict)
        basis = extension["level_basis"]
        assert isinstance(basis, dict)
        basis["trigger_evaluations"] = ["all true"]
        malformed_extensions.append(fabricated)
        reordered_basis = copy.deepcopy(extended)
        extension = reordered_basis["execution_level_extension"]
        assert isinstance(extension, dict)
        basis = extension["level_basis"]
        assert isinstance(basis, dict)
        trigger_rows = basis["trigger_evaluations"]
        assert isinstance(trigger_rows, list)
        basis["trigger_evaluations"] = list(reversed(trigger_rows))
        malformed_extensions.append(reordered_basis)
        for malformed in malformed_extensions:
            with self.subTest(keys=list(malformed)):
                errors = execution_level_migration_errors(
                    malformed,
                    lifecycle_status="in_progress",
                    next_action="edit",
                    step=task,
                )
                self.assertTrue(errors)
                self.assertTrue(any("extension is invalid" in error for error in errors), errors)

    def test_trace_migration_classifier_uses_material_action_not_incidental_read(self) -> None:
        task = _first_fixture_step("task")
        legacy_payload = copy.deepcopy(task["fixture_capsule"])
        legacy_payload.pop("execution_level_extension")
        action_expectations = {
            "repair": "edit",
            "validate": "validation",
            "finding": "review",
            "review": "review",
            "re-review": "review",
        }
        for trace_action, classified in action_expectations.items():
            with self.subTest(trace_action=trace_action):
                steps = [
                    {**task, "fixture_capsule": copy.deepcopy(legacy_payload)},
                    {"actor": "task-agent", "action": "read", "path": "owner.py"},
                    {"actor": "task-agent", "action": trace_action},
                ]
                errors = trace_execution_level_migration_errors(steps, 0)
                self.assertTrue(errors)
                self.assertIn(f"classified next action {classified}", errors[0])
        completed_read = [
            {**task, "fixture_capsule": copy.deepcopy(legacy_payload)},
            {"actor": "task-agent", "action": "read", "path": "owner.py"},
        ]
        self.assertEqual(
            [],
            trace_execution_level_migration_errors(
                completed_read,
                0,
                lifecycle_status="completed",
            ),
        )

    def test_trace_migration_classifier_scans_across_real_parallel_dispatch_batch(self) -> None:
        document = json.loads(AGENT_LIGHT_CASES.read_text(encoding="utf-8"))
        case = next(
            case
            for case in document["cases"]
            if case["id"] == "isolated-write-parallel-contract"
        )
        steps = case["steps"]
        parallel_dispatches = [
            index
            for index, step in enumerate(steps)
            if step.get("action") == "dispatch"
            and step.get("parallel_batch") == "batch-1"
        ]
        self.assertEqual([2, 3], parallel_dispatches)
        for index in parallel_dispatches:
            with self.subTest(index=index):
                self.assertEqual(
                    [], trace_execution_level_migration_errors(steps, index)
                )

        legacy_steps = copy.deepcopy(steps)
        legacy_index = parallel_dispatches[0]
        legacy_steps[legacy_index]["fixture_capsule"].pop(
            "execution_level_extension"
        )
        errors = trace_execution_level_migration_errors(
            legacy_steps,
            legacy_index,
        )
        self.assertTrue(errors)
        self.assertIn("classified next action edit", errors[0])

    def test_malformed_review_cost_authority_returns_errors_without_raising(self) -> None:
        malformed = copy.deepcopy(CORE_CONTRACTS)
        locked = malformed["final_goal_contract"][
            "professional_review_cost_fixtures"
        ]["locked_current_catalog"]
        locked["full_rereview_deduplicated_capsule_input_bytes_proxy"] = 0
        locked["named_isolated_case"]["fresh_target_count"] = "eight"
        errors = validate_core_contracts(malformed)
        self.assertTrue(any("byte proxy must be positive" in error for error in errors), errors)
        self.assertTrue(any("counts and bytes" in error for error in errors), errors)

    def test_review_cost_threshold_is_owned_by_core_and_bounds_current_lock(self) -> None:
        fixtures = CORE_CONTRACTS["final_goal_contract"][
            "professional_review_cost_fixtures"
        ]
        self.assertEqual(56, fixtures["thresholds"]["maximum_fresh_target_count"])
        self.assertEqual(189, fixtures["locked_current_catalog"]["case_count"])
        self.assertEqual([], validate_core_contracts(copy.deepcopy(CORE_CONTRACTS)))

        below_current_max = copy.deepcopy(CORE_CONTRACTS)
        below_current_max["final_goal_contract"][
            "professional_review_cost_fixtures"
        ]["thresholds"]["maximum_fresh_target_count"] = 53
        errors = validate_core_contracts(below_current_max)
        self.assertTrue(
            any(
                "fresh-target fixture arithmetic or threshold is stale" in error
                for error in errors
            ),
            errors,
        )

        boolean_threshold = copy.deepcopy(CORE_CONTRACTS)
        boolean_threshold["final_goal_contract"][
            "professional_review_cost_fixtures"
        ]["thresholds"]["maximum_fresh_target_count"] = True
        errors = validate_core_contracts(boolean_threshold)
        self.assertTrue(
            any("review cost threshold" in error for error in errors),
            errors,
        )

    def test_formal_round_cost_policy_is_closed_and_value_locked(self) -> None:
        mutations = []
        missing = copy.deepcopy(CORE_CONTRACTS)
        missing["final_goal_contract"]["professional_review_cost_fixtures"][
            "formal_round_policy"
        ].pop("full_fresh_source_material_coverage_ratio_ppm")
        mutations.append(missing)

        extra = copy.deepcopy(CORE_CONTRACTS)
        extra["final_goal_contract"]["professional_review_cost_fixtures"][
            "formal_round_policy"
        ]["unreviewed_override"] = 1
        mutations.append(extra)

        wrong = copy.deepcopy(CORE_CONTRACTS)
        wrong["final_goal_contract"]["professional_review_cost_fixtures"][
            "formal_round_policy"
        ][
            "maximum_reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm"
        ] = 50_001
        mutations.append(wrong)

        for model in mutations:
            with self.subTest(policy=model["final_goal_contract"]):
                errors = validate_core_contracts(model)
                self.assertTrue(
                    any("formal-round policy" in error for error in errors),
                    errors,
                )

    def test_profile_exact_rule_schema_rejects_missing_extra_and_wrong_bindings(
        self,
    ) -> None:
        def capability_rule(model, capability_id, rule_id):
            return next(
                rule
                for rule in model["profile_contract"]["capability_terms"][
                    capability_id
                ]
                if rule["rule_id"] == rule_id
            )

        missing = copy.deepcopy(CORE_CONTRACTS)
        capability_rule(missing, "task-normal-mode", "bounded-validation-retry").pop(
            "exact_rule"
        )

        extra = copy.deepcopy(CORE_CONTRACTS)
        extra_rule = capability_rule(
            extra,
            "task-normal-mode",
            "normal-primary-skill",
        )
        extra_rule["exact_rule"] = "- " + " ".join(extra_rule["required_terms"])

        wrong = copy.deepcopy(CORE_CONTRACTS)
        capability_rule(
            wrong,
            "review-target-modes",
            "implementation-review",
        ).pop("exact_rule")
        wrong_rule = capability_rule(
            wrong,
            "review-target-modes",
            "missing-diff",
        )
        wrong_rule["exact_rule"] = "- " + " ".join(wrong_rule["required_terms"])

        for label, mutation in (
            ("missing", missing),
            ("extra", extra),
            ("wrong", wrong),
        ):
            with self.subTest(label=label):
                errors = validate_core_contracts(mutation)
                self.assertTrue(
                    any("exact_rule bindings must be exactly" in error for error in errors),
                    errors,
                )

    def test_profile_rule_count_overrides_are_role_bounded(self) -> None:
        limits = CORE_CONTRACTS["profile_contract"]["instruction_rule_count"]
        self.assertEqual(
            {
                "minimum": 6,
                "maximum": 16,
                "maximum_by_role": {"task-agent": 38, "review-agent": 18},
            },
            limits,
        )

        unknown_role = copy.deepcopy(CORE_CONTRACTS)
        unknown_role["profile_contract"]["instruction_rule_count"][
            "maximum_by_role"
        ] = {"unknown-agent": 21}
        errors = validate_core_contracts(unknown_role)
        self.assertTrue(
            any("maximum_by_role contains unknown roles" in error for error in errors),
            errors,
        )

        below_default = copy.deepcopy(CORE_CONTRACTS)
        below_default["profile_contract"]["instruction_rule_count"][
            "maximum_by_role"
        ] = {"task-agent": 15}
        errors = validate_core_contracts(below_default)
        self.assertTrue(
            any("at least equal to the default maximum" in error for error in errors),
            errors,
        )

    def test_profile_exact_rule_schema_rejects_malformed_or_incomplete_bullets(
        self,
    ) -> None:
        malformed = copy.deepcopy(CORE_CONTRACTS)
        malformed_rule = next(
            rule
            for rule in malformed["implementation_discipline_contract"][
                "profile_projection"
            ]
            if rule["rule_id"] == "test-after-boundary"
        )
        malformed_rule["exact_rule"] += "\n- second bullet"

        incomplete = copy.deepcopy(CORE_CONTRACTS)
        incomplete_rule = next(
            rule
            for rule in incomplete["profile_contract"]["capability_terms"][
                "review-target-modes"
            ]
            if rule["rule_id"] == "implementation-review"
        )
        incomplete_rule["exact_rule"] = "- implementation or repair review"

        for label, mutation, marker in (
            ("malformed", malformed, "one non-empty canonical bullet"),
            ("incomplete", incomplete, "must contain every required term"),
        ):
            with self.subTest(label=label):
                errors = validate_core_contracts(mutation)
                self.assertTrue(any(marker in error for error in errors), errors)

    def test_profile_exact_rule_schema_rejects_present_invalid_values(self) -> None:
        for label, value in (
            ("null", None),
            ("wrong-type", 7),
            ("empty", ""),
            ("blank", "   "),
        ):
            with self.subTest(label=label):
                mutation = copy.deepcopy(CORE_CONTRACTS)
                rule = next(
                    item
                    for item in mutation["implementation_discipline_contract"][
                        "profile_projection"
                    ]
                    if item["rule_id"] == "non-test-validation-boundary"
                )
                rule["exact_rule"] = value
                errors = validate_core_contracts(mutation)
                self.assertTrue(
                    any(
                        "exact_rule must be one non-empty canonical bullet" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_model_rejects_principle_role_task_evidence_and_terminal_mutations(self) -> None:
        mutations = []

        duplicate_principle = copy.deepcopy(CORE_CONTRACTS)
        duplicate_principle["core_principles"][1]["id"] = duplicate_principle[
            "core_principles"
        ][0]["id"]
        mutations.append(duplicate_principle)

        role_capability = copy.deepcopy(CORE_CONTRACTS)
        role_capability["roles"]["analysis-agent"]["may_edit"] = True
        mutations.append(role_capability)

        missing_status = copy.deepcopy(CORE_CONTRACTS)
        missing_status["task_contract"]["fields"].remove("Status")
        mutations.append(missing_status)

        assignment_status = copy.deepcopy(CORE_CONTRACTS)
        assignment_status["task_contract"]["assignment_initial_status"] = "partial"
        mutations.append(assignment_status)

        evidence_state = copy.deepcopy(CORE_CONTRACTS)
        evidence_state["visible_evidence_contract"]["states"] = ["current", "done"]
        mutations.append(evidence_state)

        terminal_transition = copy.deepcopy(CORE_CONTRACTS)
        terminal_transition["completion_state"]["allowed_transitions"]["completed"] = [
            "in_progress"
        ]
        mutations.append(terminal_transition)

        missing_template_schema = copy.deepcopy(CORE_CONTRACTS)
        del missing_template_schema["task_contract"]["template_schemas"][
            "direct-task-template.md"
        ]
        mutations.append(missing_template_schema)

        relaxed_main_margin = copy.deepcopy(CORE_CONTRACTS)
        relaxed_main_margin["context_budget_contract"]["budget_classes"][
            "main"
        ]["minimum_release_margin_tokens"] = 79
        mutations.append(relaxed_main_margin)

        prompt_heading = copy.deepcopy(CORE_CONTRACTS)
        prompt_heading["prompt_contract"]["ordered_headings"][1][1] = "Main Control Agent"
        mutations.append(prompt_heading)

        profile_capability = copy.deepcopy(CORE_CONTRACTS)
        profile_capability["profile_contract"]["role_capabilities"]["task-agent"][
            "required_capability_ids"
        ].append("unknown-capability")
        mutations.append(profile_capability)

        control_reference_source = copy.deepcopy(CORE_CONTRACTS)
        control_reference_source["control_skill_contract"]["reference_path_source"] = (
            "duplicated.local.list"
        )
        mutations.append(control_reference_source)

        utility_status = copy.deepcopy(CORE_CONTRACTS)
        utility_status["task_contract"]["template_schemas"][
            "utility-capsule-template.md"
        ]["status_sections"][1]["allowed"] = ["completed"]
        mutations.append(utility_status)

        duplicate_heading = copy.deepcopy(CORE_CONTRACTS)
        duplicate_heading["task_contract"]["template_schemas"][
            "direct-task-template.md"
        ]["headings"].insert(5, [2, "Owner"])
        mutations.append(duplicate_heading)

        duplicate_h1 = copy.deepcopy(CORE_CONTRACTS)
        duplicate_h1["task_contract"]["template_schemas"][
            "engineering-brief-template.md"
        ]["headings"].insert(1, [1, "Engineering Brief"])
        mutations.append(duplicate_h1)

        wrong_core_order = copy.deepcopy(CORE_CONTRACTS)
        fields = wrong_core_order["task_contract"]["template_schemas"][
            "direct-task-template.md"
        ]["task_fields"]
        fields[3], fields[4] = fields[4], fields[3]
        mutations.append(wrong_core_order)

        unreachable_completed = copy.deepcopy(CORE_CONTRACTS)
        unreachable_completed["completion_state"]["allowed_transitions"][
            "partial"
        ] = ["in_progress", "blocked"]
        unreachable_completed["completion_state"]["allowed_transitions"][
            "blocked"
        ] = ["in_progress", "partial"]
        unreachable_completed["completion_state"]["allowed_transitions"][
            "in_progress"
        ] = ["blocked", "partial"]
        mutations.append(unreachable_completed)

        misbound_acceptance_check = copy.deepcopy(CORE_CONTRACTS)
        misbound_acceptance_check["principle_acceptance_contract"]["authorities"][
            0
        ]["pointer"] = "/missing-contract"
        mutations.append(misbound_acceptance_check)

        duplicate_freshness_id = copy.deepcopy(CORE_CONTRACTS)
        duplicate_freshness_id["visible_evidence_contract"]["freshness_rules"][1][
            "id"
        ] = duplicate_freshness_id["visible_evidence_contract"]["freshness_rules"][0][
            "id"
        ]
        mutations.append(duplicate_freshness_id)

        unknown_freshness_target = copy.deepcopy(CORE_CONTRACTS)
        unknown_freshness_target["visible_evidence_contract"]["freshness_rules"][0][
            "projection_targets"
        ].append("prompt:Unknown Section")
        mutations.append(unknown_freshness_target)

        duplicate_completed_rule = copy.deepcopy(CORE_CONTRACTS)
        duplicate_completed_rule["completion_state"]["completed_rules"][1]["id"] = (
            duplicate_completed_rule["completion_state"]["completed_rules"][0]["id"]
        )
        mutations.append(duplicate_completed_rule)

        malformed_forbidden_storage = copy.deepcopy(CORE_CONTRACTS)
        malformed_forbidden_storage["visible_evidence_contract"]["forbidden_storage"][
            0
        ]["projection_terms"] = []
        mutations.append(malformed_forbidden_storage)

        missing_completion_projection = copy.deepcopy(CORE_CONTRACTS)
        missing_completion_projection["completion_state"]["agent_projection"][
            "rules"
        ].pop()
        mutations.append(missing_completion_projection)

        for index, mutation in enumerate(mutations):
            with self.subTest(index=index):
                self.assertTrue(validate_core_contracts(mutation))

    def test_all_principles_reject_unknown_outcome_mappings(self) -> None:
        for index, principle in enumerate(CORE_CONTRACTS["core_principles"]):
            with self.subTest(principle=principle["id"]):
                mutation = copy.deepcopy(CORE_CONTRACTS)
                mutation["core_principles"][index]["required_outcomes"][
                    "authoring"
                ] = ["missing-outcome"]
                errors = validate_core_contracts(mutation)
                self.assertTrue(
                    any("unknown outcomes" in error for error in errors),
                    errors,
                )

    def test_acceptance_graph_rejects_deleted_misbound_and_recursive_producers(self) -> None:
        deleted = copy.deepcopy(CORE_CONTRACTS)
        deleted["principle_acceptance_contract"]["outcomes"].pop()

        misbound = copy.deepcopy(CORE_CONTRACTS)
        producer = next(
            item
            for item in misbound["principle_acceptance_contract"]["producers"]
            if item["id"] == "validate-control-plane-prompt"
        )
        producer["argv"] = ["python3", "scripts/eval-core-principles.py"]

        weak = copy.deepcopy(CORE_CONTRACTS)
        authority = next(
            item
            for item in weak["principle_acceptance_contract"]["authorities"]
            if item["id"] == "evidence-contract-authority"
        )
        authority["pointer"] = "/principle_acceptance_contract"

        for label, mutation in (
            ("deleted", deleted),
            ("misbound", misbound),
            ("weak", weak),
        ):
            with self.subTest(label=label):
                errors = validate_core_contracts(mutation)
                self.assertTrue(errors)
                self.assertTrue(
                    any(
                        marker in error
                        for error in errors
                        for marker in (
                            "unknown outcomes",
                            "recursively execute",
                            "self-containing",
                        )
                    ),
                    errors,
                )

    def test_final_goal_binds_context_and_structural_cost_outcomes(self) -> None:
        principle = next(
            item
            for item in CORE_CONTRACTS["core_principles"]
            if item["id"] == "final-goal"
        )
        self.assertTrue(
            {
                "final-goal-context-costs",
                "final-goal-structural-costs",
            }.issubset(principle["required_outcomes"]["authoring"])
        )

    def test_every_freshness_projection_target_is_required_and_consumed(self) -> None:
        for rule_index, rule in enumerate(
            CORE_CONTRACTS["visible_evidence_contract"]["freshness_rules"]
        ):
            for target in rule["projection_targets"]:
                with self.subTest(rule=rule["id"], target=target):
                    mutation = copy.deepcopy(CORE_CONTRACTS)
                    mutation["visible_evidence_contract"]["freshness_rules"][
                        rule_index
                    ]["projection_targets"].remove(target)
                    errors = validate_core_contracts(mutation)
                    self.assertTrue(
                        any("must be consumed exactly" in error for error in errors),
                        errors,
                    )

    def test_every_forbidden_storage_projection_target_is_required_and_consumed(self) -> None:
        for rule_index, rule in enumerate(
            CORE_CONTRACTS["visible_evidence_contract"]["forbidden_storage"]
        ):
            for target in rule["projection_targets"]:
                with self.subTest(rule=rule["id"], target=target):
                    mutation = copy.deepcopy(CORE_CONTRACTS)
                    mutation["visible_evidence_contract"]["forbidden_storage"][
                        rule_index
                    ]["projection_targets"].remove(target)
                    errors = validate_core_contracts(mutation)
                    self.assertTrue(
                        any("must be consumed exactly" in error for error in errors),
                        errors,
                    )

    def test_each_transition_graph_edge_requires_exact_agent_projection(self) -> None:
        transitions = CORE_CONTRACTS["completion_state"]["allowed_transitions"]
        for source, targets in transitions.items():
            for target in targets:
                with self.subTest(source=source, target=target):
                    mutation = copy.deepcopy(CORE_CONTRACTS)
                    mutation["completion_state"]["allowed_transitions"][source].remove(
                        target
                    )
                    errors = validate_core_contracts(mutation)
                    self.assertTrue(
                        any(
                            "projection must derive exactly" in error
                            for error in errors
                        ),
                        errors,
                    )

    def test_each_fail_closed_outcome_requires_exact_agent_projection(self) -> None:
        rules = CORE_CONTRACTS["completion_state"]["fail_closed_rules"]
        for rule_id, allowed_statuses in rules.items():
            for allowed_status in allowed_statuses:
                with self.subTest(rule=rule_id, status=allowed_status):
                    mutation = copy.deepcopy(CORE_CONTRACTS)
                    mutation["completion_state"]["fail_closed_rules"][rule_id].remove(
                        allowed_status
                    )
                    errors = validate_core_contracts(mutation)
                    self.assertTrue(
                        any(
                            "fail-closed-outcomes prompt projection must derive exactly"
                            in error
                            for error in errors
                        ),
                        errors,
                    )

    def test_independent_review_evidence_contract_is_closed(self) -> None:
        mutations = []

        missing_condition = copy.deepcopy(CORE_CONTRACTS)
        del missing_condition["visible_evidence_contract"]["completion_proof"][
            "implementation"
        ]["required_review_claims"]["blocking_findings"]["resolved"]
        mutations.append(missing_condition)

        wrong_owner = copy.deepcopy(CORE_CONTRACTS)
        wrong_owner["visible_evidence_contract"]["completion_proof"][
            "implementation"
        ]["independent_review_owner"] = "task-agent"
        mutations.append(wrong_owner)

        missing_owner_separation = copy.deepcopy(CORE_CONTRACTS)
        missing_owner_separation["visible_evidence_contract"]["completion_proof"][
            "implementation"
        ]["independent_owner_required"] = False
        mutations.append(missing_owner_separation)

        missing_projection = copy.deepcopy(CORE_CONTRACTS)
        missing_projection["visible_evidence_contract"]["completion_proof"][
            "implementation"
        ]["projections"][0]["terms"].remove("changed-scope-reviewed")
        mutations.append(missing_projection)

        wrong_validation_claim = copy.deepcopy(CORE_CONTRACTS)
        wrong_validation_claim["visible_evidence_contract"]["completion_proof"][
            "implementation"
        ]["validation_claim"] = "validation-complete"
        mutations.append(wrong_validation_claim)

        for mutation in mutations:
            with self.subTest():
                self.assertTrue(validate_core_contracts(mutation))

    def test_review_handoff_requires_exact_independent_review_claims(self) -> None:
        proof = CORE_CONTRACTS["visible_evidence_contract"]["completion_proof"][
            "implementation"
        ]
        projection = next(
            item
            for item in proof["projections"]
            if item["target"] == "review-handoff-template.md"
        )
        for term in projection["terms"]:
            with self.subTest(term=term):
                with tempfile.TemporaryDirectory() as raw:
                    root = Path(raw) / "references"
                    shutil.copytree(REFERENCE_ROOT, root)
                    path = root / "review-handoff-template.md"
                    text = path.read_text(encoding="utf-8")
                    mutated, count = re.subn(
                        re.escape(term),
                        "REMOVED_REVIEW_PROOF_TERM",
                        text,
                        count=1,
                        flags=re.IGNORECASE,
                    )
                    self.assertEqual(1, count)
                    path.write_text(
                        mutated,
                        encoding="utf-8",
                    )
                    errors = VALIDATOR.validate_contracts(root)
                    self.assertTrue(
                        any(
                            "independent review evidence proof" in error
                            for error in errors
                        ),
                        errors,
                    )

    def test_implementation_handoff_requires_exact_validation_claims(self) -> None:
        proof = CORE_CONTRACTS["visible_evidence_contract"]["completion_proof"][
            "implementation"
        ]
        projection = next(
            item
            for item in proof["projections"]
            if item["target"] == "implementation-handoff-template.md"
        )
        for term in projection["terms"]:
            with self.subTest(term=term):
                with tempfile.TemporaryDirectory() as raw:
                    root = Path(raw) / "references"
                    shutil.copytree(REFERENCE_ROOT, root)
                    path = root / "implementation-handoff-template.md"
                    text = path.read_text(encoding="utf-8")
                    mutated, count = re.subn(
                        re.escape(term),
                        "REMOVED_TASK_VALIDATION_PROOF_TERM",
                        text,
                        flags=re.IGNORECASE,
                    )
                    self.assertGreaterEqual(count, 1)
                    path.write_text(mutated, encoding="utf-8")
                    errors = VALIDATOR.validate_contracts(root)
                    self.assertTrue(
                        any(
                            "independent review evidence proof" in error
                            for error in errors
                        ),
                        errors,
                    )

    def test_direct_extension_insertion_metadata_is_exact(self) -> None:
        schema_path = (
            "task_contract",
            "template_schemas",
            "direct-task-template.md",
            "extension_heading_insertions",
        )
        missing = copy.deepcopy(CORE_CONTRACTS)
        target = missing
        for key in schema_path:
            target = target[key]
        del target["Inspection Boundary"]

        wrong_anchor = copy.deepcopy(CORE_CONTRACTS)
        target = wrong_anchor
        for key in schema_path:
            target = target[key]
        target["Professional Skill"]["after"] = "Review Owner"

        for mutation in (missing, wrong_anchor):
            with self.subTest():
                self.assertTrue(validate_core_contracts(mutation))


class CompletionReviewRequirementTests(unittest.TestCase):
    @staticmethod
    def _completed_claim() -> dict[str, object]:
        document = json.loads(AGENT_LIGHT_CASES.read_text(encoding="utf-8"))
        claim = copy.deepcopy(
            next(
                case["claim"]
                for case in document["completion_state_cases"]
                if case["id"] == "implementation-completed-with-current-evidence"
            )
        )
        claim["task_id"] = "task-single-file-bug-fix-1"
        claim["high_risk_review"] = "not-required"
        claim["evidence_ledger"] = [
            row
            for row in claim["evidence_ledger"]
            if row["Claim"] != "high-risk-review-passed"
        ]
        return claim

    @staticmethod
    def _authority() -> dict[str, object]:
        document = json.loads(AGENT_LIGHT_CASES.read_text(encoding="utf-8"))
        case = next(
            case for case in document["cases"] if case["id"] == "single-file-bug-fix"
        )
        task_dispatch = next(
            step
            for step in case["steps"]
            if step.get("action") == "dispatch"
            and step.get("profile") == "task-agent"
        )
        task_id = task_dispatch["fixture_capsule"]["task_id"]
        review_assignment = next(
            step
            for step in case["steps"]
            if step.get("action") == "dispatch"
            and step.get("profile") == "review-agent"
            and step.get("fixture_capsule", {}).get("task_id") == task_id
        )
        return {
            "task_dispatch": copy.deepcopy(task_dispatch),
            "review_assignment": copy.deepcopy(review_assignment),
        }

    @staticmethod
    def _refresh_task_digest(authority: dict[str, object]) -> str:
        dispatch = authority["task_dispatch"]
        payload = dispatch["fixture_capsule"]
        digest = canonical_capsule_sha256(dispatch, payload)
        payload["canonical_sha256"] = digest
        return digest

    @staticmethod
    def _recompute_execution(authority: dict[str, object]) -> None:
        extension = authority["task_dispatch"]["fixture_capsule"][
            "execution_level_extension"
        ]
        basis = extension["level_basis"]
        result = compute_execution_level(
            requested=extension["requested_level"],
            trigger_evaluations={
                row["id"]: {key: value for key, value in row.items() if key != "id"}
                for row in basis["trigger_evaluations"]
            },
            l2_evaluations={
                row["id"]: {key: value for key, value in row.items() if key != "id"}
                for row in basis["l2_eligibility"]
            },
            prior_historical_max_floor=extension["prior_historical_max_floor"],
            prior_historical_max_effective=extension[
                "prior_historical_max_effective"
            ],
        )
        extension["computed_floor"] = result["computed_floor"]
        extension["mandatory_floor"] = result["mandatory_floor"]
        extension["automatic_level"] = result["automatic_level"]
        extension["effective_level"] = result["effective_level"]
        extension["historical_max_floor"] = result["next_historical_floor"]
        extension["historical_max_effective"] = result[
            "next_historical_effective"
        ]
        basis.update(result["level_basis"])

    @classmethod
    def _bind(
        cls,
        claim: dict[str, object],
        authority: dict[str, object],
        *,
        digest: str | None = None,
        extra_binding: dict[str, object] | None = None,
    ) -> dict[str, object]:
        binding = {
            "capsule_canonical_sha256": (
                digest
                if digest is not None
                else authority["task_dispatch"]["fixture_capsule"][
                    "canonical_sha256"
                ]
            )
        }
        if extra_binding:
            binding.update(extra_binding)
        ledger = claim.pop("evidence_ledger")
        claim["review_requirement_binding"] = binding
        claim["evidence_ledger"] = ledger
        return claim

    def test_low_risk_not_required_is_bound_and_keeps_independent_review(self) -> None:
        authority = self._authority()
        claim = self._bind(self._completed_claim(), authority)
        self.assertEqual(
            [],
            completion_claim_errors(claim, review_authority=authority),
        )

        claim["evidence_ledger"] = [
            row
            for row in claim["evidence_ledger"]
            if row["Claim"] != "changed-scope-reviewed"
        ]
        errors = completion_claim_errors(claim, review_authority=authority)
        self.assertTrue(
            any("independent review evidence" in error for error in errors),
            errors,
        )

    def test_high_risk_level_history_or_critical_trigger_rejects_not_required(
        self,
    ) -> None:
        authorities = []
        for field, value in (
            ("effective_level", "L4"),
            ("effective_level", "L5"),
            ("historical_max_floor", "L4"),
            ("historical_max_effective", "L5"),
        ):
            authority = self._authority()
            extension = authority["task_dispatch"]["fixture_capsule"][
                "execution_level_extension"
            ]
            extension[field] = value
            self._refresh_task_digest(authority)
            authorities.append(authority)
        critical_trigger = next(
            row["id"]
            for row in CORE_CONTRACTS["execution_level_contract"]["trigger_registry"]
            if row["floor"] == "L4"
        )
        for status in ("matched", "unknown"):
            authority = self._authority()
            trigger = next(
                row
                for row in authority["task_dispatch"]["fixture_capsule"][
                    "execution_level_extension"
                ]["level_basis"]["trigger_evaluations"]
                if row["id"] == critical_trigger
            )
            trigger["status"] = status
            self._recompute_execution(authority)
            self._refresh_task_digest(authority)
            authorities.append(authority)
        specialized = self._authority()
        specialized["review_assignment"]["mode"] = "security-review"
        authorities.append(specialized)

        for authority in authorities:
            with self.subTest(authority=authority):
                errors = completion_claim_errors(
                    self._bind(self._completed_claim(), authority),
                    review_authority=authority,
                )
                self.assertTrue(
                    any("high-risk review is required" in error for error in errors),
                    errors,
                )

    def test_not_required_fails_closed_without_authority_or_matching_digest(
        self,
    ) -> None:
        authority = self._authority()
        missing_errors = completion_claim_errors(
            self._bind(self._completed_claim(), authority)
        )
        self.assertTrue(
            any("reissue" in error for error in missing_errors),
            missing_errors,
        )

        errors = completion_claim_errors(
            self._bind(self._completed_claim(), authority, digest="b" * 64),
            review_authority=authority,
        )
        self.assertTrue(any("does not match" in error for error in errors), errors)

    def test_synchronized_self_reported_risk_facts_cannot_override_authority(
        self,
    ) -> None:
        authority = self._authority()
        forged = copy.deepcopy(authority)
        forged["task_dispatch"]["fixture_capsule"][
            "goal"
        ] = "Forge a different bounded owner behavior without authority."
        forged_digest = self._refresh_task_digest(forged)
        extra_binding = {
            "effective_level": "L2",
            "trigger_evaluations": [
                {"id": row["id"], "status": "not_matched"}
                for row in CORE_CONTRACTS["execution_level_contract"][
                    "trigger_registry"
                ]
            ],
            "historical_max_floor": "L1",
            "historical_max_effective": "L2",
            "review_strategy": "independent-implementation-review",
        }
        errors = completion_claim_errors(
            self._bind(
                self._completed_claim(),
                authority,
                digest=forged_digest,
                extra_binding=extra_binding,
            ),
            review_authority=authority,
        )
        self.assertTrue(
            any(
                "digest-only" in error or "does not match" in error
                for error in errors
            ),
            errors,
        )


class CompletionTransitionTests(unittest.TestCase):
    def test_every_declared_transition_is_accepted(self) -> None:
        for source, targets in COMPLETION_STATE_MODEL["allowed_transitions"].items():
            for target in targets:
                with self.subTest(source=source, target=target):
                    self.assertEqual([], completion_transition_errors(source, target))

    def test_unknown_and_self_transitions_are_rejected(self) -> None:
        self.assertTrue(completion_transition_errors("unknown", "partial"))
        self.assertTrue(completion_transition_errors("partial", "unknown"))
        for status in COMPLETION_STATE_MODEL["statuses"]:
            with self.subTest(status=status):
                self.assertTrue(completion_transition_errors(status, status))

    def test_completed_is_terminal_for_same_task_id(self) -> None:
        self.assertTrue(completion_transition_errors("completed", "in_progress"))
        self.assertTrue(completion_transition_errors("completed", "blocked"))

    def test_new_work_after_completion_requires_new_task_id_and_initial_state(self) -> None:
        self.assertEqual(
            [],
            completion_transition_errors(
                "completed", "in_progress", same_task_id=False
            ),
        )
        self.assertTrue(
            completion_transition_errors("completed", "partial", same_task_id=False)
        )
        self.assertTrue(
            completion_transition_errors("blocked", "in_progress", same_task_id=False)
        )


if __name__ == "__main__":
    unittest.main()
