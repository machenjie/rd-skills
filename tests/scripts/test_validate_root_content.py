from __future__ import annotations

import importlib
import importlib.util
import hashlib
import sys
import unittest
from copy import deepcopy
from datetime import date
from pathlib import Path
from unittest import mock


FULL_TEST_RESOURCE_CLASS = "heavy-tokenizer"


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/validate-root-content.py"


def _load_module():
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location("validate_root_content_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ValidateRootContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()
        cls.auditor = cls.module._load_auditor()
        cls.validation_utils = importlib.import_module("validation_utils")

    def _unfenced_logical_list_items(self, markdown: str) -> dict[str, list[str]]:
        unfenced = "\n".join(
            "" if in_fence else line
            for _index, line, in_fence in self.auditor._strip_fenced(
                markdown.splitlines()
            )
        )
        return self.validation_utils.parse_markdown_logical_list_items(unfenced)

    def test_fresh_root_collection_is_source_only(self) -> None:
        content = {"source": "fresh-root"}
        auditor = mock.Mock()
        auditor._collect_root_content.return_value = content
        auditor._collect_semantic_content_with_application.side_effect = AssertionError(
            "authoring Root validation consumed formal application state"
        )

        with mock.patch.object(self.module, "_load_auditor", return_value=auditor):
            self.assertIs(content, self.module._fresh_root_content())

        auditor._collect_root_content.assert_called_once_with()
        auditor._collect_semantic_content_with_application.assert_not_called()

    def test_foundation_budget_contract_excludes_derivation_snapshot(self) -> None:
        document = self._document(
            "# Capability\n\n## High-Value Rules\n\n"
            "- Verify the bounded input against the owned invariant.\n"
            "- Reject values above the declared hard limit.\n"
            "- Preserve current evidence for the observed result.\n"
        )
        with (
            mock.patch.object(
                self.auditor, "_root_skill_documents", return_value=[document]
            ),
            mock.patch.object(
                self.auditor, "count_o200k_base_tokens", return_value=100
            ),
            mock.patch.object(
                self.auditor,
                "_load_root_semantic_dispositions",
                return_value=self._empty_disposition_contract([document]),
            ),
        ):
            content = self.auditor._collect_root_content(
                evaluation_date=date(2026, 8, 2)
            )

        self.assertNotIn(
            "derivation_snapshot", content["foundation_budget_contract"]
        )
        stale = deepcopy(content)
        stale["foundation_budget_contract"]["derivation_snapshot"] = {
            "sum_tokens": 100
        }
        _counts, errors = self.module._evaluate(
            stale,
            strict=False,
            evaluation_date=date(2026, 8, 2),
        )
        self.assertIn(
            "root_content.foundation_budget_contract does not match canonical policy",
            errors,
        )

    def _document(
        self,
        text: str,
        *,
        part: str = "body",
        path: str = "src/foundation/capabilities/example/SKILL.md",
    ) -> dict:
        return {
            "path": path,
            "layer": "foundation-capability",
            "owner": "example",
            "kind": "foundation-capability",
            "text": text,
            "line_offset": 4 if part == "body" else 2,
            "document_part": part,
            **(
                {
                    "content_class": "compact",
                    "content_class_rationale": None,
                    "target_words": 400,
                    "hard_words": 500,
                }
                if part == "body"
                else {}
            ),
        }

    def _semantic(self, document: dict) -> dict:
        return self.auditor._collect_root_semantic_advisories(
            [document], disposition_entries=[], evaluation_date=date(2026, 7, 14)
        )

    def _empty_disposition_contract(
        self, documents: list[dict]
    ) -> tuple[dict, list[str]]:
        return (
            {
                "schema_version": self.auditor.ROOT_SEMANTIC_DISPOSITION_SCHEMA_VERSION,
                "entries": [],
            },
            [],
        )

    def _findings(
        self,
        text: str,
        *,
        part: str = "body",
        path: str = "src/foundation/capabilities/example/SKILL.md",
    ) -> set[str]:
        return {
            item["finding"]
            for item in self._semantic(
                self._document(text, part=part, path=path)
            )["candidates"]
        }

    def _entry(self, candidate: dict, *, disposition: str = "valid-contextual-rule") -> dict:
        entry = {
            "candidate_id": candidate["candidate_id"],
            "finding": candidate["finding"],
            "path": candidate["path"],
            "document_part": candidate["document_part"],
            "source_selector": deepcopy(candidate["source_selector"]),
            "skill_owner": candidate["skill_owner"],
            "priority": candidate["priority"],
            "disposition": disposition,
            "reason": "The bounded repository contract makes this exact rule decision-relevant.",
            "authority_or_condition": "A current repository policy explicitly owns this bounded condition.",
            "decision_owner": "changeforge-maintainers",
            "evidence": {
                "occurrence_fingerprint": candidate["occurrence_fingerprint"],
                "context_fingerprint": candidate["context_fingerprint"],
                "rationale": "The exact occurrence membership and local section context were inspected.",
            },
            "mitigation": "Rewrite the rule when its owning repository policy or local context changes.",
            "review_after": "2026-08-01" if disposition == "time-bounded-exception" else None,
        }
        contracts = importlib.import_module("expert_panel_contracts")
        entry["record_fingerprint"] = contracts.semantic_disposition_record_fingerprint(
            "root", entry
        )
        return entry

    def test_review_positive_detector_table(self) -> None:
        cases = (
            ("All changes require review.", "unconditional_mechanism_candidate"),
            ("Each non-trivial function requires unit tests.", "unconditional_mechanism_candidate"),
            ("Any deployment requires approval.", "unconditional_mechanism_candidate"),
            ("Retry 3 times.", "fixed_duration_threshold_status_candidate"),
            ("Timeout is one hour.", "fixed_duration_threshold_status_candidate"),
            ("Escalate in the first hour.", "fixed_duration_threshold_status_candidate"),
            ("Require 80% coverage.", "fixed_duration_threshold_status_candidate"),
            ("Return HTTP 409 for conflicts.", "fixed_duration_threshold_status_candidate"),
            ("Use Linear for issue tracking.", "fixed_vendor_tool_candidate"),
            ("Always preload every Reference.", "unconditional_mechanism_candidate"),
            ("Create a DAG for two or more real tasks.", "fixed_duration_threshold_status_candidate"),
            ("Use a 60–90 second heartbeat.", "fixed_duration_threshold_status_candidate"),
            ("Stop after the same failed route twice.", "fixed_duration_threshold_status_candidate"),
        )
        for sentence, expected in cases:
            with self.subTest(sentence=sentence):
                result = self._semantic(
                    self._document(f"# Capability\n\n## High-Value Rules\n\n- {sentence}\n")
                )
                self.assertIn(expected, {item["finding"] for item in result["candidates"]})

    def test_anti_pattern_normative_and_failure_example_table(self) -> None:
        positives = (
            (
                "A no-docs outcome must identify the affected audience and durable artifact.",
                "unconditional_mechanism_candidate",
            ),
            (
                "Every change requires an ADR.",
                "mandatory_artifact_candidate",
            ),
        )
        for sentence, expected in positives:
            with self.subTest(sentence=sentence, expected=expected):
                self.assertIn(
                    expected,
                    self._findings(
                        f"# Capability\n\n## Anti-Patterns\n\n- {sentence}\n"
                    ),
                )

        negatives = (
            '"Every change requires an ADR" is an over-prescriptive anti-pattern.',
            "`Every change requires an ADR` is an over-prescriptive anti-pattern.",
            "Do not require an ADR for an unrelated change.",
            "Select current proof rather than requiring a standard report.",
        )
        forbidden = {
            "unconditional_mechanism_candidate",
            "mandatory_artifact_candidate",
        }
        for sentence in negatives:
            with self.subTest(sentence=sentence, expected="no-policy-candidate"):
                self.assertTrue(
                    forbidden.isdisjoint(
                        self._findings(
                            f"# Capability\n\n## Anti-Patterns\n\n- {sentence}\n"
                        )
                    )
                )

    def test_decision_and_proof_mechanism_table(self) -> None:
        positives = (
            "Each criterion must have an explicit unacceptable result.",
            "Evidence must be reproducible by an independent reviewer.",
            "Every benchmark requires proof tied to the affected behavior.",
            "Map each material invariant to a test.",
        )
        for sentence in positives:
            with self.subTest(sentence=sentence, expected="candidate"):
                self.assertIn(
                    "unconditional_mechanism_candidate",
                    self._findings(f"# Capability\n\n## Rules\n\n- {sentence}\n"),
                )

        negatives = (
            "Each criterion maps to an observable outcome.",
            "The evidence describes the observed result.",
            "Benchmarks compare feasible candidates from current measurements.",
            "The regression test covers the prior failure.",
        )
        for sentence in negatives:
            with self.subTest(sentence=sentence, expected="no-candidate"):
                self.assertNotIn(
                    "unconditional_mechanism_candidate",
                    self._findings(f"# Capability\n\n## Rules\n\n- {sentence}\n"),
                )

    def test_durable_artifact_lexicon_table(self) -> None:
        positives = (
            "Create a test for the accepted behavior.",
            "Write a regression test for the causal failure.",
            "A test plan is required for the release.",
            "Every change requires a test suite.",
            "Produce a benchmark for the selected boundary.",
            "Maintain a fixture for the compatibility case.",
            "A dashboard is required for the rollout.",
            "Create a diagram for the cross-boundary flow.",
        )
        for sentence in positives:
            with self.subTest(sentence=sentence, expected="candidate"):
                self.assertIn(
                    "mandatory_artifact_candidate",
                    self._findings(f"# Capability\n\n## Rules\n\n- {sentence}\n"),
                )

        negatives = (
            "Inspect the existing regression test when it covers the affected behavior.",
            "The existing test suite covers the current contract.",
            "Do not require a dashboard for an unrelated change.",
            "Choose evidence rather than requiring a standard fixture.",
        )
        for sentence in negatives:
            with self.subTest(sentence=sentence, expected="no-candidate"):
                self.assertNotIn(
                    "mandatory_artifact_candidate",
                    self._findings(f"# Capability\n\n## Rules\n\n- {sentence}\n"),
                )

    def test_file_level_refinement_density_table(self) -> None:
        positives = (
            """# Capability

## Anti-Patterns

For example, compare a stale result with current proof.
For instance, distinguish an observed failure from an inferred cause.
A waiver is defined as a bounded exception with an owner.
""",
            """# Capability

## Notes

A contract is defined as an owned observable boundary.
A proof means evidence another reviewer can reproduce.
In other words, a claim without current evidence remains open.
""",
            """# Capability

## Anti-Patterns

Refresh stale facts instead of adding surrounding prose.
Name the evidence limit rather than inventing a passing result.
Use the owned boundary instead of a generic organization policy.
""",
        )
        for text in positives:
            with self.subTest(first_marker=text.splitlines()[4]):
                self.assertIn(
                    "tutorial_explanatory_density_candidate", self._findings(text)
                )

        negatives = (
            """# Capability

## High-Value Rules

- Refresh stale facts instead of adding surrounding prose.
- Name the evidence limit rather than inventing a passing result.
- Use the owned boundary instead of a generic organization policy.
""",
            """# Capability

## Anti-Patterns

- For example, reject one stale proof claim.
""",
            """# Capability

## Anti-Patterns

- Missing evidence hides the decision boundary.
- Stale proof can preserve a repaired failure.
- Generic process can replace task-local judgment.
""",
        )
        for text in negatives:
            with self.subTest(first_line=text.splitlines()[0]):
                self.assertNotIn(
                    "tutorial_explanatory_density_candidate", self._findings(text)
                )

    def test_acceptance_has_no_refinement_candidate(self) -> None:
        path = "src/foundation/capabilities/acceptance-standard-definition/SKILL.md"
        document = next(
            item
            for item in self.auditor._root_skill_documents()
            if item["path"] == path and item["document_part"] == "body"
        )
        result = self.auditor._collect_root_semantic_advisories(
            [document], disposition_entries=[], evaluation_date=date(2026, 7, 14)
        )
        candidates = [
            item
            for item in result["candidates"]
            if item["finding"] == "tutorial_explanatory_density_candidate"
        ]
        self.assertEqual([], candidates)

    def test_tutorial_heading_requires_exact_normalized_h2_or_deeper_title(self) -> None:
        positives = (
            "Introduction",
            "Overview",
            "Definitions",
            "  **Overview**:  ",
            "Introduction to Failure Diagnosis",
            "Overview of Recovery Evidence",
            "Definitions for Contract Terms",
        )
        for title in positives:
            with self.subTest(title=title, expected="candidate"):
                self.assertIn(
                    "tutorial_explanatory_density_candidate",
                    self._findings(
                        f"# Capability\n\n## {title}\n\nThis section explains the background.\n"
                    ),
                )

        negatives = (
            "# acceptance-standard-definition\n\n## Rules\n\n- Choose from current evidence.\n",
            "# Overview\n\nThis root title names the Skill.\n",
            "# Capability\n\n## Decision Overview\n\nThis is a decision card.\n",
            "# Capability\n\n## Definition Boundaries\n\nThis is a boundary card.\n",
        )
        for text in negatives:
            with self.subTest(text=text.splitlines()[0], expected="no-candidate"):
                self.assertNotIn(
                    "tutorial_explanatory_density_candidate", self._findings(text)
                )

    def test_mandatory_artifact_requires_direct_prescriptive_object(self) -> None:
        positives = (
            "Create an ADR for the accepted decision.",
            "Every diagnosis must produce a hypothesis table.",
            "Maintain a runbook for the owned recovery path.",
            "All releases require a scorecard.",
            "Write a compatibility report for the changed contract.",
            "An ADR is required for every decision.",
            "Every release must have a scorecard.",
            "A scorecard must accompany every release.",
            "Always create, archive, and retain an ADR.",
            "Create a current source-backed cross-boundary consumer compatibility "
            "and release evidence report.",
        )
        for sentence in positives:
            with self.subTest(sentence=sentence, expected="candidate"):
                self.assertIn(
                    "mandatory_artifact_candidate",
                    self._findings(f"# Capability\n\n## Rules\n\n- {sentence}\n"),
                )

        negatives = (
            "Document every changed command against current source.",
            "Report all remaining proof gaps.",
            "Classify each invariant as item/document-local or partition-local.",
            "Create a database table for account state.",
            "Review every artifact before release.",
            "Tie each claim to source, log, artifact, or test evidence.",
            "Existing artifact-lifecycle decisions must close together.",
            "Record and explain any unplanned path.",
            "Do not require an unrelated full unit template.",
            "Reproducibility risk requires immutable artifact identity.",
            "**Create a recoverable evidence trail.** Record pre-mutation identity and intended ref changes.",
            "Never create a report.",
            "Create no report.",
        )
        for sentence in negatives:
            with self.subTest(sentence=sentence, expected="no-candidate"):
                self.assertNotIn(
                    "mandatory_artifact_candidate",
                    self._findings(f"# Capability\n\n## Rules\n\n- {sentence}\n"),
                )

    def test_jit_parent_condition_reaches_coordinated_child_clause(self) -> None:
        conditional = (
            "Read [checklist.md](references/checklist.md) only when risk changes, "
            "and always read every affected rule.",
            "Load when current policy selects the checklist, and always read every "
            "affected rule.",
            "Skip when no decision remains, and never preload the catalog.",
        )
        for sentence in conditional:
            with self.subTest(sentence=sentence):
                self.assertNotIn(
                    "unconditional_mechanism_candidate",
                    self._findings(
                        f"# Capability\n\n## Targeted References\n\n- {sentence}\n"
                    ),
                )

        self.assertIn(
            "unconditional_mechanism_candidate",
            self._findings(
                "# Capability\n\n## Targeted References\n\n"
                "- Always preload every Reference.\n"
            ),
        )

        adversarial = (
            "Load when current policy selects the checklist, and always read every "
            "affected rule, and always preload every Reference regardless of risk.",
            "Describe the label 'load when', and always preload every Reference.",
            "Describe the label `load when`, and always preload every Reference.",
            "Load when current policy selects the checklist, and always read every "
            "affected rule unconditionally.",
            "Load when current policy selects the checklist, and independently "
            "always preload every Reference.",
        )
        for sentence in adversarial:
            with self.subTest(sentence=sentence, expected="candidate"):
                self.assertIn(
                    "unconditional_mechanism_candidate",
                    self._findings(
                        f"# Capability\n\n## Targeted References\n\n- {sentence}\n"
                    ),
                )

    def test_registry_projection_is_metadata_for_root_budget_and_semantics(self) -> None:
        body = """# Capability

## High-Value Rules

- Verify the affected boundary against current source before accepting proof.
- Compare feasible options when the current contract leaves a real choice.
- Preserve the owned invariant so failure cannot create forbidden state.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | every change requires a checklist | no review decision remains | analysis-agent | checklist-result |
"""
        plain = self._document(body)
        self.assertIn(
            "unconditional_mechanism_candidate",
            {
                item["finding"]
                for item in self._semantic(plain)["candidates"]
            },
        )

        governed = deepcopy(plain)
        governed["governed_text"] = (
            self.auditor.strip_registry_targeted_reference_projection(body)
        )
        self.assertEqual([], self._semantic(governed)["candidates"])
        self.assertEqual(
            len(body.splitlines()), len(governed["governed_text"].splitlines())
        )

        with (
            mock.patch.object(
                self.auditor, "_root_skill_documents", return_value=[governed]
            ),
            mock.patch.object(
                self.auditor,
                "_load_root_semantic_dispositions",
                return_value=self._empty_disposition_contract([governed]),
            ),
        ):
            content = self.auditor._collect_root_content()
        row = content["documents"][0]
        self.assertEqual(len(governed["governed_text"].split()), row["word_count"])
        self.assertEqual(
            hashlib.sha256(body.encode("utf-8")).hexdigest(),
            row["content_fingerprint"],
        )

        noncanonical = body.replace(
            "| [checklist](references/checklist.md) | decision-checklist | "
            "every change requires a checklist | no review decision remains | "
            "analysis-agent | checklist-result |",
            "- Always preload every Reference.",
        )
        self.assertEqual(
            noncanonical,
            self.auditor.strip_registry_targeted_reference_projection(noncanonical),
        )
        self.assertIn(
            "unconditional_mechanism_candidate",
            self._findings(noncanonical),
        )

        for path in (
            "references/../checklist.md",
            "references//checklist.md",
            "references/./checklist.md",
        ):
            with self.subTest(path=path):
                invalid_path = body.replace(
                    "references/checklist.md",
                    path,
                )
                self.assertEqual(
                    invalid_path,
                    self.auditor.strip_registry_targeted_reference_projection(
                        invalid_path
                    ),
                )

    def test_fixed_number_excludes_only_proven_non_policy_shapes(self) -> None:
        negative_documents = (
            "# Capability\n\n## Registry Trigger\n\n- HTTP 502 503 504 retry amplification\n",
            "# Capability\n\n## Do Not Use\n\n- one Direct Task already owns the change\n",
            "# Capability\n\n## Rules\n\n- Prepare a handoff for one isolated subagent.\n",
            "# Capability\n\n## Rules\n\n- One test cannot contaminate another.\n",
            "# Capability\n\n## Rules\n\n- More than one runtime remains feasible.\n",
            "# Capability\n\n## Rules\n\n- Two or more feasible options remain comparable.\n",
            "# Capability\n\n## Rules\n\n- A DLQ is only one candidate among several.\n",
        )
        for text in negative_documents:
            with self.subTest(text=text.splitlines()[-1], expected="no-candidate"):
                self.assertNotIn(
                    "fixed_duration_threshold_status_candidate", self._findings(text)
                )
        self.assertNotIn(
            "fixed_duration_threshold_status_candidate",
            self._findings(
                "`analysis-agent`: use when 2+ tasks need planning; skip one Direct Task.",
                part="description",
            ),
        )

        positives = (
            "Retry 3 times.",
            "Timeout is one hour.",
            "Escalate in the first hour.",
            "Require 80% coverage.",
            "Return HTTP 409 for conflicts.",
            "Create a DAG for two or more real tasks.",
            "Assign each task one primary Professional Skill.",
            "Retry 3 times because more than one runtime remains feasible.",
            "One test cannot contaminate another while retrying 3 times.",
            "At least one alternative remains while retries are set to 3 attempts.",
        )
        for sentence in positives:
            with self.subTest(sentence=sentence, expected="candidate"):
                self.assertIn(
                    "fixed_duration_threshold_status_candidate",
                    self._findings(f"# Capability\n\n## Rules\n\n- {sentence}\n"),
                )

        metadata_positives = (
            "`task-agent`: use when deployment fails, retry 3 times before escalation.",
            "`task-agent`: use when a worker has retried 3 times.",
        )
        for description in metadata_positives:
            with self.subTest(description=description, expected="candidate"):
                self.assertIn(
                    "fixed_duration_threshold_status_candidate",
                    self._findings(description, part="description"),
                )

        self.assertIn(
            "fixed_duration_threshold_status_candidate",
            self._findings(
                "# Capability\n\n## Anti-patterns\n\n"
                "- Always retry 3 times for every failure.\n"
            ),
        )
        self.assertIn(
            "fixed_duration_threshold_status_candidate",
            self._findings(
                "# Capability\n\n## Registry Trigger\n\n"
                "- Retry 3 times after deployment failure.\n"
            ),
        )

    def test_organization_policy_requires_prescribed_authority_target(self) -> None:
        positives = (
            "Always escalate to the manager.",
            "Require approval from the incident commander.",
            "The CAB must approve the release.",
            "Do not proceed without manager approval.",
            "Send the release to the CAB for approval.",
            "Notify the incident commander about the release.",
            "Escalate the incident to whoever is on-call.",
        )
        for sentence in positives:
            with self.subTest(sentence=sentence, expected="candidate"):
                self.assertIn(
                    "context_free_organization_policy_candidate",
                    self._findings(f"# Capability\n\n## Rules\n\n- {sentence}\n"),
                )

        negatives = (
            "Use the package-manager lockfile selected by the repository.",
            "The connection manager owns retry state.",
            "The manager can review the incident if asked.",
            "Finish the work in the current sprint.",
            "Attend the standup when the team requests it.",
            "Notify the connection-manager about retry state.",
            "Send the release to the CAB according to the current policy.",
        )
        for sentence in negatives:
            with self.subTest(sentence=sentence, expected="no-candidate"):
                self.assertNotIn(
                    "context_free_organization_policy_candidate",
                    self._findings(f"# Capability\n\n## Rules\n\n- {sentence}\n"),
                )

    def test_vendor_specific_description_may_name_its_owned_domain(self) -> None:
        specialized = self._document(
            "`task-agent`: use when a Kubernetes workload changes.",
            part="description",
            path="src/foundation/capabilities/kubernetes-gateway/SKILL.md",
        )
        specialized["owner"] = "kubernetes-gateway"
        self.assertNotIn(
            "fixed_vendor_tool_candidate",
            {item["finding"] for item in self._semantic(specialized)["candidates"]},
        )

        universal = self._document(
            "Always use Kubernetes for every deployment.",
            part="description",
            path="src/foundation/capabilities/kubernetes-gateway/SKILL.md",
        )
        universal["owner"] = "kubernetes-gateway"
        self.assertIn(
            "fixed_vendor_tool_candidate",
            {item["finding"] for item in self._semantic(universal)["candidates"]},
        )

        generic_descriptions = (
            "Use Linear for issue tracking.",
            "Use Kubernetes for every deployment.",
        )
        for description in generic_descriptions:
            with self.subTest(description=description):
                self.assertIn(
                    "fixed_vendor_tool_candidate",
                    self._findings(description, part="description"),
                )

    def test_adjacent_legal_rules_and_clause_local_authority(self) -> None:
        legal = (
            "When the current contract requires review, review each affected boundary.",
            "Use three retries as required by the current SLO.",
            "Return the status defined by the current API contract.",
            "Use the issue tracker selected by the current policy.",
        )
        for sentence in legal:
            with self.subTest(sentence=sentence):
                self.assertEqual(
                    [],
                    self._semantic(
                        self._document(f"# Capability\n\n## Rules\n\n- {sentence}\n")
                    )["candidates"],
                )

        compound = self._semantic(
            self._document(
                "# Capability\n\n## Rules\n\n"
                "- According to the current policy, use Jira for issue tracking; "
                "always use Linear for issue tracking.\n"
            )
        )
        self.assertEqual(1, len(compound["candidates"]))
        self.assertIn("Linear", compound["candidates"][0]["preview"])

    def test_all_seven_root_families_are_reachable(self) -> None:
        examples = "\n".join(f"line {index}" for index in range(14))
        documents = [
            self._document(
                "# Capability\n\n## Overview\n\nThis is a tutorial overview because the reader needs background.\n"
                "\n## Examples\n\n" + examples
            ),
            self._document(
                "# Capability\n\n## Rules\n\n"
                "- Every diagnosis must produce a hypothesis table.\n"
                "- Always escalate to the manager in the first hour.\n"
                "- Use Linear for issue tracking.\n"
            ),
        ]
        result = self.auditor._collect_root_semantic_advisories(
            documents, disposition_entries=[], evaluation_date=date(2026, 7, 14)
        )
        self.assertEqual(
            set(self.auditor.ROOT_SEMANTIC_FINDINGS),
            {item["finding"] for item in result["candidates"]},
        )

    def test_reference_section_scans_universal_rule_but_ignores_exact_jit_link(self) -> None:
        document = self._document(
            "# Capability\n\n## Targeted References\n\n"
            "- Read [checklist.md](references/checklist.md) only when several decisions remain open.\n"
            "- Always preload every Reference.\n"
        )
        candidates = self._semantic(document)["candidates"]
        self.assertEqual(1, len(candidates))
        self.assertIn("preload", candidates[0]["preview"])

    def test_candidate_id_is_line_stable_but_evidence_binds_occurrence_and_context(self) -> None:
        base = self._document(
            "# Capability\n\n## Rules\n\n- Every diagnosis must produce a hypothesis table.\n"
        )
        first = self._semantic(base)["candidates"][0]
        entry = self._entry(first)

        shifted = self._document(
            "\n\n# Capability\n\n## Rules\n\n- Every diagnosis must produce a hypothesis table.\n"
        )
        shifted_candidate = self._semantic(shifted)["candidates"][0]
        self.assertEqual(first["candidate_id"], shifted_candidate["candidate_id"])
        governed = self.auditor._collect_root_semantic_advisories(
            [shifted], disposition_entries=[entry], evaluation_date=date(2026, 7, 14)
        )
        self.assertEqual([], governed["disposition_contract"]["errors"])

        evidence_variants = (
            self._document(
                "# Capability\n\n## Rules\n\n"
                "- Every diagnosis must produce a hypothesis table.\n"
                "- Every diagnosis must produce a hypothesis table.\n"
            ),
            self._document(
                "# Capability\n\n## Rules\n\n- Inspect current risk first.\n"
                "- Every diagnosis must produce a hypothesis table.\n"
            ),
        )
        for variant in evidence_variants:
            with self.subTest(text=variant["text"][:60]):
                candidate = self._semantic(variant)["candidates"][0]
                self.assertEqual(first["candidate_id"], candidate["candidate_id"])
                governed = self.auditor._collect_root_semantic_advisories(
                    [variant], disposition_entries=[entry], evaluation_date=date(2026, 7, 14)
                )
                self.assertEqual([], governed["disposition_contract"]["errors"])
                self.assertEqual(
                    "needs-confirmation",
                    governed["candidates"][0]["governance_status"],
                )
                self.assertIsNone(governed["candidates"][0]["disposition_record"])

        moved_section = self._document(
            "# Capability\n\n## Required Process\n\n"
            "- Every diagnosis must produce a hypothesis table.\n"
        )
        moved_candidate = self._semantic(moved_section)["candidates"][0]
        self.assertNotEqual(first["candidate_id"], moved_candidate["candidate_id"])

    def test_disposition_contract_rejects_malformed_expired_and_unsorted_entries(self) -> None:
        document = self._document(
            "# Capability\n\n## Rules\n\n"
            "- Every diagnosis must produce a hypothesis table.\n"
            "- Use Linear for issue tracking.\n"
        )
        candidates = self._semantic(document)["candidates"]
        entries = sorted((self._entry(item) for item in candidates), key=lambda item: item["candidate_id"])

        malformed = deepcopy(entries[0])
        malformed.pop("document_part")
        _, _, errors = self.auditor._validate_root_semantic_dispositions(
            candidates, [malformed], date(2026, 7, 14), require_applied=False
        )
        self.assertTrue(any("missing field" in item for item in errors), errors)

        expired = self._entry(candidates[0], disposition="time-bounded-exception")
        expired["review_after"] = "2026-07-14"
        expired["record_fingerprint"] = importlib.import_module(
            "expert_panel_contracts"
        ).semantic_disposition_record_fingerprint("root", expired)
        _, _, errors = self.auditor._validate_root_semantic_dispositions(
            candidates, [expired], date(2026, 7, 13), require_applied=False
        )
        self.assertEqual([], errors)
        _, _, errors = self.auditor._validate_root_semantic_dispositions(
            candidates, [expired], date(2026, 7, 14), require_applied=False
        )
        self.assertTrue(any("after 2026-07-14" in item for item in errors), errors)

        _, _, errors = self.auditor._validate_root_semantic_dispositions(
            candidates, list(reversed(entries)), date(2026, 7, 14), require_applied=False
        )
        self.assertTrue(any("sorted by candidate_id" in item for item in errors), errors)

    def test_disposition_projection_rejects_volatile_evaluated_on(self) -> None:
        evaluation_date = date(2026, 8, 9)
        content = self.auditor._collect_root_content(
            evaluation_date=evaluation_date
        )
        contract = content["semantic_advisories"]["disposition_contract"]
        self.assertNotIn("evaluated_on", contract)

        malformed = deepcopy(content)
        malformed["semantic_advisories"]["disposition_contract"][
            "evaluated_on"
        ] = evaluation_date.isoformat()
        _counts, errors = self.module._evaluate(
            malformed,
            strict=False,
            evaluation_date=evaluation_date,
        )
        self.assertTrue(
            any("disposition_contract fields do not match" in item for item in errors),
            errors,
        )

    def test_disposition_contract_rejects_duplicate_entry(self) -> None:
        document = self._document(
            "# Capability\n\n## High-Value Rules\n\n"
            "- Every diagnosis must produce a hypothesis table.\n"
        )
        candidate = self._semantic(document)["candidates"][0]
        entry = self._entry(candidate)
        governed = self.auditor._collect_root_semantic_advisories(
            [document],
            disposition_entries=[entry, deepcopy(entry)],
            evaluation_date=date(2026, 7, 14),
        )
        contract = governed["disposition_contract"]
        self.assertEqual(2, contract["configured_count"])
        self.assertEqual(0, contract["applied_count"])
        self.assertTrue(
            any("duplicate candidate_id" in item for item in contract["errors"]),
            contract["errors"],
        )
        governed_candidate = governed["candidates"][0]
        self.assertEqual("needs-confirmation", governed_candidate["governance_status"])
        self.assertIsNone(governed_candidate["disposition_record"])

    def test_control_needs_confirmation_blocks_only_control_surface(self) -> None:
        documents = [
            {
                "path": "src/control-prompts/main-control-agent.md",
                "layer": "control-prompt",
                "owner": "main-control-agent",
                "kind": "control-prompt",
                "text": "# Control\n\n## Rules\n\n- Use Linear for issue tracking.\n",
                "line_offset": 0,
                "document_part": "control-prompt",
            },
            {
                "path": "src/professional-skills/example/SKILL.md",
                "layer": "professional-skill",
                "owner": "example",
                "kind": "professional-skill",
                "text": "# Professional Rule\n\n## Rules\n\n- Use Linear for issue tracking.\n",
                "line_offset": 4,
                "document_part": "body",
            },
        ]
        initial = self.auditor._collect_root_semantic_advisories(
            documents,
            disposition_entries=[],
            evaluation_date=date(2026, 7, 14),
        )
        candidates = {item["layer"]: item for item in initial["candidates"]}
        control_entry = self._entry(candidates["control-prompt"])
        control_entry["evidence"]["context_fingerprint"] = "0" * 64
        control_entry["record_fingerprint"] = importlib.import_module(
            "expert_panel_contracts"
        ).semantic_disposition_record_fingerprint("root", control_entry)
        professional_entry = self._entry(candidates["professional-skill"])
        governed = self.auditor._collect_root_semantic_advisories(
            documents,
            disposition_entries=sorted(
                [control_entry, professional_entry],
                key=lambda item: item["candidate_id"],
            ),
            evaluation_date=date(2026, 7, 14),
        )
        contract = governed["disposition_contract"]
        self.assertEqual([], contract["common_errors"])
        self.assertEqual([], contract["surface_errors"]["control"])
        self.assertEqual([], contract["surface_errors"]["professional"])
        governed_by_layer = {item["layer"]: item for item in governed["candidates"]}
        self.assertIsNone(governed_by_layer["control-prompt"]["disposition"])
        self.assertEqual(
            "needs-confirmation",
            governed_by_layer["control-prompt"]["governance_status"],
        )
        self.assertEqual(
            "valid-contextual-rule",
            governed_by_layer["professional-skill"]["disposition"],
        )
        surfaces = self.auditor._root_surface_validation(
            documents,
            {},
            governed,
        )["surfaces"]
        self.assertEqual("fail", surfaces["control"]["status"])
        self.assertTrue(surfaces["control"]["semantic_p0_p1_unresolved_count"])
        self.assertEqual("pass", surfaces["professional"]["status"])

    def test_candidate_error_is_attributed_to_its_root_surface(self) -> None:
        candidate = {
            "candidate_id": "a" * 64,
            "layer": "professional-skill",
            "document_part": "body",
        }
        message = "root semantic candidate[0]: applied root governance state was mutated"
        common, surfaces = self.auditor._root_disposition_error_attribution(
            [message],
            [],
            [candidate],
        )
        self.assertEqual([], common)
        self.assertEqual([message], surfaces["professional"])
        self.assertEqual([], surfaces["control"])
        self.assertEqual([], surfaces["foundation"])
        self.assertEqual([], surfaces["domain"])
        self.assertEqual([], surfaces["description"])

    def test_root_surface_validation_tampering_fails_closed(self) -> None:
        documents = self.auditor._root_skill_documents()
        with mock.patch.object(
            self.auditor,
            "_load_root_semantic_dispositions",
            return_value=self._empty_disposition_contract(documents),
        ):
            content = self.auditor._collect_root_content()
        surface = content["surface_validation"]["surfaces"]["professional"]
        surface["status"] = "fail" if surface["status"] == "pass" else "pass"
        _counts, errors = self.module._evaluate(content, strict=False)
        self.assertTrue(
            any("does not match canonical source attribution" in item for item in errors),
            errors,
        )

    def test_all_rule_levels_enter_sentence_and_decision_density_contract(self) -> None:
        body = """# Capability

## High-Value Rules

- Verify the affected boundary against current source and reject stale evidence.
  - Nested explanation one.
  - Nested explanation two.
- Compare feasible options when the current contract leaves a real choice.
- Preserve the owned invariant so failure cannot produce forbidden state.
"""
        facts = self.auditor._foundation_content_facts(body, self.auditor.parse_sections(body))
        self.assertEqual(5, facts["high_value_rule_count"])
        self.assertEqual(3, facts["high_value_rule_decision_count"])
        self.assertEqual(2, facts["high_value_rules_without_decision_semantics"])
        self.assertEqual(0.6, facts["decision_density"])
        self.assertEqual(
            2,
            self.auditor._sentence_count(
                "Use evidence, e.g. Current logs and traces. Reject stale claims."
            ),
        )

        generic = """# Capability

## High-Value Rules

- Explain the concept.
- Add details.
- Be helpful.
"""
        facts = self.auditor._foundation_content_facts(
            generic, self.auditor.parse_sections(generic)
        )
        self.assertEqual(3, facts["high_value_rule_count"])
        self.assertEqual(0, facts["high_value_rule_decision_count"])
        self.assertEqual(3, facts["high_value_rules_without_decision_semantics"])

        parsed = self._unfenced_logical_list_items(
            """- Verify the affected boundary when current evidence changes
  and reject stale proof before changing the decision.
  - Inspect the nested failure boundary against current source
    before accepting the claimed recovery.
```text
- This fenced marker is not a rule.
```
- Preserve the owned invariant when the failure remains possible.
"""
        )
        logical = parsed["items"]
        self.assertEqual(3, len(logical))
        self.assertEqual([], parsed["non_list_content"])
        self.assertIn("reject stale proof", logical[0])
        self.assertIn("accepting the claimed recovery", logical[1])
        self.assertTrue(all("fenced marker" not in item for item in logical))

    def test_foundation_decision_detector_rejects_plain_format_summary_and_transfer(
        self,
    ) -> None:
        ordinary_prose = (
            "Pair the heading color and spacing in the published style guide.",
            "Assess the paragraph wording against editorial standards for general readers.",
            "Trace the file names from configuration into the compact transfer table.",
            "Summarize the available material in a concise neutral paragraph.",
        )
        for rule in ordinary_prose:
            with self.subTest(rule=rule):
                card = self.validation_utils.foundation_decision_card(
                    f"## High-Value Rules\n\n- {rule}\n"
                )
                self.assertEqual(1, card["metrics"]["high_value_rule_count"])
                self.assertEqual(
                    0, card["metrics"]["high_value_rule_decision_count"]
                )
                self.assertEqual(
                    1,
                    card["metrics"][
                        "high_value_rules_without_decision_semantics"
                    ],
                )

    def test_nested_rules_cannot_bypass_rule_count_strict_gate(self) -> None:
        nested = "\n".join(
            "  - Inspect the nested failure boundary when current evidence changes."
            for _ in range(20)
        )
        body = (
            "# Capability\n\n## High-Value Rules\n\n"
            "- Verify the affected boundary against current source and reject stale evidence.\n"
            f"{nested}\n"
            "- Compare feasible options when the current contract leaves a real choice.\n"
            "- Preserve the owned invariant so failure cannot produce forbidden state.\n"
        )
        facts = self.auditor._foundation_content_facts(
            body, self.auditor.parse_sections(body)
        )
        self.assertEqual(23, facts["high_value_rule_count"])
        self.assertEqual(23, facts["high_value_rule_decision_count"])
        document = self._document(body)
        with (
            mock.patch.object(
                self.auditor, "_root_skill_documents", return_value=[document]
            ),
            mock.patch.object(
                self.auditor,
                "_load_root_semantic_dispositions",
                return_value=self._empty_disposition_contract([document]),
            ),
        ):
            content = self.auditor._collect_root_content()
        self.assertEqual(self.auditor.ROOT_CONTENT_SCHEMA_VERSION, content["schema_version"])
        counts, errors = self.module._evaluate(content, strict=True)
        self.assertEqual(1, counts["foundation_rule_count_outside_target"])
        self.assertTrue(any("outside 3-8" in item for item in errors), errors)

    def test_blank_separated_prose_cannot_lend_decision_semantics(self) -> None:
        # Root schema v5 preserves logical list-item accounting. This
        # protects that contract from unrelated prose being treated as a lazy
        # continuation merely because it follows a bullet.
        body = """# Capability

## High-Value Rules

- Explain the concept.

When current evidence changes, verify the affected boundary before proceeding.
- Add details.

When the source contract changes, reject stale proof before deciding.
- Be helpful.

When failure remains possible, preserve the owned invariant before release.
"""
        facts = self.auditor._foundation_content_facts(
            body, self.auditor.parse_sections(body)
        )
        self.assertEqual(3, facts["high_value_rule_count"])
        self.assertEqual(0, facts["high_value_rule_decision_count"])
        self.assertEqual(3, facts["high_value_rules_without_decision_semantics"])
        self.assertEqual(0.0, facts["decision_density"])

        document = self._document(body)
        with (
            mock.patch.object(
                self.auditor, "_root_skill_documents", return_value=[document]
            ),
            mock.patch.object(
                self.auditor,
                "_load_root_semantic_dispositions",
                return_value=self._empty_disposition_contract([document]),
            ),
            mock.patch.object(
                self.auditor, "count_o200k_base_tokens", return_value=100
            ),
        ):
            content = self.auditor._collect_root_content()
        counts, errors = self.module._evaluate(content, strict=True)
        self.assertEqual(1, counts["foundation_rules_without_decision_semantics"])
        self.assertEqual(1, counts["foundation_low_decision_density"])
        self.assertTrue(any("without decision semantics" in item for item in errors), errors)

    def test_nested_list_fences_at_container_indents_are_not_rules(self) -> None:
        body = """# Capability

## High-Value Rules

- Verify the outer boundary against current evidence and reject stale proof.
  - Inspect the nested boundary when current source changes materially.
    ```text
    - This marker is code, not a High-Value Rule.
    ```
    - Preserve the deepest invariant so failure cannot create forbidden state.
      ~~~text
      - This deeper marker is also code.
      ~~~
  - ```text
    - This inline-list fence marker is also code.
    ```
- Compare feasible options when the current contract leaves a real choice.
"""
        section = self.auditor._find_section(
            self.auditor.parse_sections(body), "High-Value Rules"
        )
        self.assertIsNotNone(section)
        parsed = self._unfenced_logical_list_items(section.text)
        logical = parsed["items"]
        self.assertEqual(4, len(logical))
        self.assertEqual([], parsed["non_list_content"])
        self.assertTrue(all("marker is" not in item for item in logical))

        annotated = self.auditor._strip_fenced(section.text.splitlines())
        fenced = [line.strip() for _index, line, in_fence in annotated if in_fence]
        self.assertIn("```text", fenced)
        self.assertIn("~~~text", fenced)
        self.assertIn("- This marker is code, not a High-Value Rule.", fenced)
        self.assertIn("- This deeper marker is also code.", fenced)
        self.assertIn("- ```text", fenced)
        self.assertIn("- This inline-list fence marker is also code.", fenced)

        raw = self.validation_utils.parse_markdown_logical_list_items(section.text)
        self.assertEqual(8, len(raw["items"]))
        self.assertEqual(["```", "~~~", "```"], raw["non_list_content"])

        facts = self.auditor._foundation_content_facts(
            body, self.auditor.parse_sections(body)
        )
        self.assertEqual(8, facts["high_value_rule_count"])
        self.assertEqual(4, facts["high_value_rule_decision_count"])
        self.assertEqual(4, facts["high_value_rules_without_decision_semantics"])

    def test_description_is_independent_agent_facing_part(self) -> None:
        documents = self.auditor._root_skill_documents()
        descriptions = {
            item["path"]: item
            for item in documents
            if item["document_part"] == "description"
        }
        control = descriptions["src/control-skills/engineering-control-plane/SKILL.md"]
        self.assertEqual("description", control["document_part"])
        self.assertEqual([], self._semantic(control)["candidates"])
        yaml_description = self._document("Retry 3 times.", part="description")
        self.assertIn(
            "fixed_duration_threshold_status_candidate",
            {
                item["finding"]
                for item in self._semantic(yaml_description)["candidates"]
            },
        )

    def test_default_reports_and_strict_gates_semantic_token_and_decision_debt(self) -> None:
        document = self._document(
            "# Capability\n\n## High-Value Rules\n\n"
            "- Every diagnosis must produce a hypothesis table.\n"
            "- Explain the concept.\n"
            "- Add details.\n"
        )
        with (
            mock.patch.object(
                self.auditor, "_root_skill_documents", return_value=[document]
            ),
            mock.patch.object(
                self.auditor,
                "_load_root_semantic_dispositions",
                return_value=self._empty_disposition_contract([document]),
            ),
        ):
            content = self.auditor._collect_root_content()
        _counts, default_errors = self.module._evaluate(content, strict=False)
        counts, strict_errors = self.module._evaluate(content, strict=True)
        self.assertEqual([], default_errors)
        self.assertGreater(counts["semantic_p0_p1_unresolved"], 0)
        self.assertGreater(counts["foundation_rules_without_decision_semantics"], 0)
        self.assertTrue(any("root P0/P1 unresolved" in item for item in strict_errors))
        self.assertTrue(any("without decision semantics" in item for item in strict_errors))

    def test_foundation_word_and_token_limits_are_independent_strict_gates(self) -> None:
        compact = self._document(
            "# Capability\n\n## High-Value Rules\n\n"
            "- Verify the affected boundary against current source and reject stale evidence.\n"
            "- Compare feasible options when the current contract leaves a real choice.\n"
            "- Preserve the owned invariant so failure cannot produce forbidden state.\n"
        )
        with (
            mock.patch.object(self.auditor, "_root_skill_documents", return_value=[compact]),
            mock.patch.object(self.auditor, "count_o200k_base_tokens", return_value=901),
            mock.patch.object(
                self.auditor,
                "_load_root_semantic_dispositions",
                return_value=self._empty_disposition_contract([compact]),
            ),
        ):
            content = self.auditor._collect_root_content()
        counts, errors = self.module._evaluate(content, strict=True)
        self.assertEqual(1, counts["foundation_over_hard_tokens"])
        self.assertEqual(0, counts["foundation_over_hard_words"])
        self.assertTrue(any("over 900 tokens" in item for item in errors), errors)

        def with_word_count(total: int, content_class: str) -> dict:
            result = deepcopy(compact)
            if content_class == "complex":
                result.update(
                    {
                        "content_class": "complex",
                        "content_class_rationale": (
                            "This fixture couples failure classification, boundary "
                            "translation, recovery meaning, and proof because they "
                            "form one test contract."
                        ),
                        "target_words": 500,
                        "hard_words": 600,
                    }
                )
            padding = total - len(result["text"].split())
            self.assertGreaterEqual(padding, 0)
            result["text"] += "\n" + " ".join("detail" for _ in range(padding))
            self.assertEqual(total, len(result["text"].split()))
            return result

        for content_class, target, hard in (
            ("compact", 400, 500),
            ("complex", 500, 600),
        ):
            target_document = with_word_count(target + 1, content_class)
            with (
                self.subTest(content_class=content_class, boundary="target"),
                mock.patch.object(
                    self.auditor,
                    "_root_skill_documents",
                    return_value=[target_document],
                ),
                mock.patch.object(
                    self.auditor, "count_o200k_base_tokens", return_value=800
                ),
                mock.patch.object(
                    self.auditor,
                    "_load_root_semantic_dispositions",
                    return_value=self._empty_disposition_contract(
                        [target_document]
                    ),
                ),
            ):
                content = self.auditor._collect_root_content()
            counts, errors = self.module._evaluate(content, strict=True)
            self.assertEqual(1, counts["foundation_over_target_words"])
            self.assertEqual(
                1, counts[f"foundation_{content_class}_over_target_words"]
            )
            self.assertEqual(0, counts["foundation_over_hard_words"])
            self.assertFalse(
                any("over class hard word limit" in item for item in errors), errors
            )

            for total, expected_count in ((hard, 0), (hard + 1, 1)):
                hard_document = with_word_count(total, content_class)
                with (
                    self.subTest(
                        content_class=content_class,
                        boundary="hard",
                        total=total,
                    ),
                    mock.patch.object(
                        self.auditor,
                        "_root_skill_documents",
                        return_value=[hard_document],
                    ),
                    mock.patch.object(
                        self.auditor, "count_o200k_base_tokens", return_value=800
                    ),
                    mock.patch.object(
                        self.auditor,
                        "_load_root_semantic_dispositions",
                        return_value=self._empty_disposition_contract(
                            [hard_document]
                        ),
                    ),
                ):
                    content = self.auditor._collect_root_content()
                counts, errors = self.module._evaluate(content, strict=True)
                self.assertEqual(expected_count, counts["foundation_over_hard_words"])
                self.assertEqual(
                    expected_count,
                    counts[f"foundation_{content_class}_over_hard_words"],
                )
                self.assertEqual(
                    bool(expected_count),
                    any("over class hard word limit" in item for item in errors),
                    errors,
                )


if __name__ == "__main__":
    unittest.main()
