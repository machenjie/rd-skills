from __future__ import annotations

import copy
import json
import linecache
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from . import expert_panel_source_test_support as source_support
from . import professional_completeness_test_support as professional_support

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import expert_panel_contracts as CONTRACTS
import professional_completeness_carry_forward as CARRY






PANEL = source_support.PANEL
_sha = professional_support._sha
_material = professional_support._material
_catalog = professional_support._catalog
_live_packet = professional_support._live_packet
_legacy_schema1_packet = professional_support._legacy_schema1_packet
SKILL_IDS = ("a", "b", "c", "d")
CONTRACT_FINGERPRINT = "a" * 64




def _load_contract_fixture(path: Path, module_name: str, source: str):
    path.write_text(source, encoding="utf-8")
    linecache.clearcache()
    module = types.ModuleType(module_name)
    module.__file__ = path.as_posix()
    sys.modules[module_name] = module
    exec(compile(source, path.as_posix(), "exec"), module.__dict__)
    return module






def _prior_artifacts(
    targets: list[dict],
    *,
    final_dispositions: dict[str, str] | None = None,
) -> tuple[dict, list[dict], dict]:
    final_dispositions = final_dispositions or {}
    source_fingerprints = {"professional_packages": _sha(targets)}
    packet = {
        "review_id": "prior-review",
        "source_fingerprints": source_fingerprints,
        "professional_targets": copy.deepcopy(targets),
    }
    voters = [
        ("domain-one", "agent-domain-one", ["domain"]),
        ("domain-two", "agent-domain-two", ["domain"]),
        (
            "architecture-one",
            "agent-architecture-one",
            ["skill-reference-architecture"],
        ),
    ]
    ballots = []
    for voter_index, (voter_id, agent_id, tags) in enumerate(voters):
        votes = []
        for target in targets:
            reviews = [
                {
                    "skill_id": candidate["skill_id"],
                    "review_origin": "packet-required",
                }
                for candidate in target["routing_adjacency"][
                    "required_candidates"
                ]
            ]
            # Only one of three ballots adds b while reviewing a.  The union
            # must retain this minority/dissent dependency.
            if voter_index == 0 and target["skill_id"] == "a":
                reviews.append(
                    {"skill_id": "b", "review_origin": "reviewer-added"}
                )
            reviews.sort(key=lambda row: row["skill_id"])
            votes.append(
                {
                    "skill_id": target["skill_id"],
                    "examined_adjacent_candidates": reviews,
                }
            )
        ballots.append(
            {
                "review_id": packet["review_id"],
                "source_fingerprints": source_fingerprints,
                "voter": {
                    "voter_id": voter_id,
                    "agent_id": agent_id,
                    "expertise_tags": tags,
                    "qualification_claims": [
                        {
                            "expertise_tag": tag,
                            "qualification_basis": "fixture qualification",
                            "proof_limit": "fixture proof limit",
                        }
                        for tag in tags
                    ],
                    "independent_review": True,
                },
                "professional_votes": votes,
            }
        )
    decisions = []
    for target in targets:
        reviewer_added = []
        if target["skill_id"] == "a":
            reviewer_added = [
                {
                    "voter_id": "domain-one",
                    "candidates": [
                        {
                            "skill_id": "b",
                            "review_origin": "reviewer-added",
                        }
                    ],
                }
            ]
        decisions.append(
            {
                "skill_id": target["skill_id"],
                "package_fingerprint": target["package_fingerprint"],
                "qualification_coverage": {
                    "required_expertise_tags": target[
                        "required_expertise_tags"
                    ],
                    "domain_voters": ["domain-one", "domain-two"],
                    "architecture_voter": "architecture-one",
                },
                "reviewer_added_adjacency_reviews": reviewer_added,
                "final_disposition": final_dispositions.get(
                    target["skill_id"],
                    CARRY.ACCEPTED_PROFESSIONAL_DISPOSITION,
                ),
            }
        )
    decision = {
        "review_id": packet["review_id"],
        "source_fingerprints": source_fingerprints,
        "voters": [
            {"voter_id": voter_id, "agent_id": agent_id}
            for voter_id, agent_id, _tags in voters
        ],
        "professional_decisions": decisions,
    }
    return packet, ballots, decision






def _historical_schema1_packet() -> dict:
    packet = copy.deepcopy(_legacy_schema1_packet())
    remaining = copy.deepcopy(PANEL.PROFESSIONAL_LEGACY_LAYER_COUNTS)
    targets = []
    for target in packet["professional_targets"]:
        layer = target["layer"]
        if remaining[layer] > 0:
            targets.append(target)
            remaining[layer] -= 1
    if remaining != {"professional": 0, "foundation": 0, "domain": 0}:
        raise AssertionError(f"legacy fixture inventory is incomplete: {remaining}")
    packet["review_id"] = "synthetic-legacy-schema-one"
    packet["professional_targets"] = sorted(
        targets, key=lambda target: target["skill_id"]
    )
    selected_ids = {
        target["skill_id"] for target in packet["professional_targets"]
    }
    for target in packet["professional_targets"]:
        adjacency = target["routing_adjacency"]
        adjacency["skills"] = [
            skill_id
            for skill_id in adjacency["skills"]
            if skill_id in selected_ids
        ]
        responsibility = target["registry"]["responsibility_contract"]
        adjacency["fingerprint"] = _sha(
            {
                "skill_id": target["skill_id"],
                "layer": target["layer"],
                "role_support": responsibility["role_support"],
                "trigger_signals": responsibility["trigger_signals"],
                "anti_trigger_signals": responsibility["anti_trigger_signals"],
                "output_contract": responsibility["output_contract"],
                "adjacent_skills": adjacency["skills"],
            }
        )
        without_fingerprint = dict(target)
        without_fingerprint.pop("package_fingerprint")
        target["package_fingerprint"] = _sha(without_fingerprint)
    packet["source_fingerprints"]["professional_packages"] = _sha(
        packet["professional_targets"]
    )
    packet["panel_contract"]["required_target_count"] = len(targets)
    return packet


def _historical_schema3_adapter_fixture(*, cap50: bool) -> tuple[dict, dict, dict]:
    packet = professional_support._bootstrap_packet()
    if cap50:
        review_id = PANEL.PROFESSIONAL_HISTORICAL_CAP50_REVIEW_ID
        review_contract = (
            PANEL.PROFESSIONAL_HISTORICAL_CAP50_REVIEW_CONTRACT_FINGERPRINT
        )
        packet_sha = PANEL.PROFESSIONAL_HISTORICAL_CAP50_PACKET_SHA256
        target_count = PANEL.PROFESSIONAL_HISTORICAL_CAP50_TARGET_COUNT
        include_derivation = False
        maximum = (
            PANEL.PROFESSIONAL_HISTORICAL_ADJACENCY_MAX_REQUIRED_CANDIDATES_PER_TARGET
        )
        remaining = copy.deepcopy(PANEL.PROFESSIONAL_LEGACY_LAYER_COUNTS)
        targets = []
        for target in packet["professional_targets"]:
            layer = target["layer"]
            if remaining[layer] > 0:
                targets.append(target)
                remaining[layer] -= 1
    else:
        review_id = PANEL.PROFESSIONAL_HISTORICAL_V1_REVIEW_ID
        review_contract = PANEL.PROFESSIONAL_HISTORICAL_V1_REVIEW_CONTRACT_FINGERPRINT
        packet_sha = PANEL.PROFESSIONAL_HISTORICAL_V1_PACKET_SHA256
        target_count = PANEL.PROFESSIONAL_PACKAGE_COUNT
        include_derivation = True
        maximum = 52
        targets = packet["professional_targets"]
    if len(targets) != target_count:
        raise AssertionError("historical adapter fixture target count is stale")
    historical_selection = PANEL._professional_adjacency_selection_contract_v1(
        target_count=target_count,
        include_derivation=include_derivation,
        maximum_required_candidates_per_target=maximum,
    )
    packet["review_id"] = review_id
    packet["review_contract_fingerprint"] = review_contract
    packet["professional_targets"] = copy.deepcopy(targets)
    packet["panel_contract"] = PANEL._professional_v3_panel_contract(
        target_count=target_count,
        include_selection_derivation=include_derivation,
    )
    packet["panel_contract"]["adjacency_contract"][
        "required_candidate_selection"
    ] = copy.deepcopy(historical_selection)
    for target in packet["professional_targets"]:
        target["routing_adjacency"]["required_candidate_selection"] = copy.deepcopy(
            historical_selection
        )
    packet_ref = {
        "path": f"evals/expert-panel/{review_id}/packet.json",
        "sha256": packet_sha,
        "kind": PANEL.PROFESSIONAL_COMPLETENESS_PACKET_KIND,
        "axis": PANEL.PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
        "review_id": review_id,
    }
    decision = {
        "review_id": review_id,
        "review_contract_fingerprint": review_contract,
    }
    return decision, packet_ref, packet


class ProfessionalCarryForwardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.targets = _catalog()
        self.bindings = CARRY.professional_review_bindings(self.targets)
        self.snapshot = CARRY.professional_carry_snapshot(
            self.bindings,
            review_contract_fingerprint=CONTRACT_FINGERPRINT,
        )
        packet, ballots, decision = _prior_artifacts(self.targets)
        self.dependencies = CARRY.professional_prior_decision_dependencies(
            prior_packet=packet,
            prior_ballots=ballots,
            prior_decision=decision,
        )

    def _plan(self, current_targets: list[dict], **overrides) -> dict:
        arguments = {
            "current_bindings": CARRY.professional_review_bindings(
                current_targets
            ),
            "prior_snapshot": self.snapshot,
            "prior_decision_dependencies": self.dependencies,
            "review_contract_fingerprint": CONTRACT_FINGERPRINT,
        }
        arguments.update(overrides)
        return CARRY.plan_exact_professional_carry_forward(**arguments)

    def _request(self, target_id: str, candidate_id: str) -> dict:
        target = next(
            row for row in self.targets if row["skill_id"] == target_id
        )
        ranking = next(
            (
                row
                for row in target["routing_adjacency"][
                    "full_catalog_ranking"
                ]
                if row["skill_id"] == candidate_id
            ),
            {
                "skill_id": candidate_id,
                "rank": 999,
                "total_score": 0,
                "signals": {},
            },
        )
        fingerprint = self.bindings.get(candidate_id, {}).get(
            "content_fingerprint", "f" * 64
        )
        return {
            "skill_id": candidate_id,
            "discovery_reason": "The boundary summary exposes a distinct overlapping responsibility.",
            "ranking_evidence": copy.deepcopy(ranking),
            "material_fingerprint": fingerprint,
        }

    def test_unchanged_exact_baseline_carries_every_package(self) -> None:
        plan = self._plan(self.targets)
        self.assertEqual([], plan["fresh_target_ids"])
        self.assertEqual(list(SKILL_IDS), plan["carry_target_ids"])
        for target in self.targets:
            binding = self.bindings[target["skill_id"]]
            self.assertEqual(
                CARRY.canonical_json_sha256(
                    CARRY.professional_candidate_material_binding(target)
                ),
                binding["content_fingerprint"],
            )
            self.assertEqual(
                CARRY.canonical_json_sha256(
                    CARRY.professional_candidate_currentness_projection(
                        target
                    )
                ),
                binding["package_material_binding"],
            )

    def test_no_baseline_and_contract_change_make_every_target_fresh(self) -> None:
        without_baseline = self._plan(
            self.targets,
            prior_snapshot=None,
            prior_decision_dependencies=None,
        )
        contract_changed = self._plan(
            self.targets,
            review_contract_fingerprint="b" * 64,
        )
        self.assertEqual(list(SKILL_IDS), without_baseline["fresh_target_ids"])
        self.assertEqual(list(SKILL_IDS), contract_changed["fresh_target_ids"])
        self.assertEqual(
            ["no-prior-baseline"], without_baseline["reasons_by_target"]["a"]
        )
        self.assertEqual(
            ["review-contract-changed"],
            contract_changed["reasons_by_target"]["a"],
        )

    def test_semantic_contract_projection_is_the_only_contract_staleness_input(
        self,
    ) -> None:
        current_contract = (
            CONTRACTS.professional_review_contract_fingerprint()
        )
        current_snapshot = CARRY.professional_carry_snapshot(
            self.bindings,
            review_contract_fingerprint=current_contract,
        )
        unchanged = CARRY.plan_exact_professional_carry_forward(
            current_bindings=self.bindings,
            prior_snapshot=current_snapshot,
            prior_decision_dependencies=self.dependencies,
            review_contract_fingerprint=current_contract,
        )

        changed_projection = (
            CONTRACTS.professional_schema3_contract_projection()
        )
        changed_projection["evidence"]["semantic_grounding"][
            "uniform_template_guard"
        ]["minimum_uniform_share_percent"] -= 1
        changed_contract = (
            CONTRACTS.professional_review_contract_fingerprint(
                changed_projection
            )
        )
        changed = CARRY.plan_exact_professional_carry_forward(
            current_bindings=self.bindings,
            prior_snapshot=current_snapshot,
            prior_decision_dependencies=self.dependencies,
            review_contract_fingerprint=changed_contract,
        )

        self.assertEqual([], unchanged["fresh_target_ids"])
        self.assertEqual(list(SKILL_IDS), unchanged["carry_target_ids"])
        self.assertNotEqual(current_contract, changed_contract)
        self.assertEqual(list(SKILL_IDS), changed["fresh_target_ids"])
        self.assertEqual(
            ["review-contract-changed"],
            changed["reasons_by_target"]["a"],
        )

    def test_currentness_contract_mutation_forces_all_fresh(self) -> None:
        current_contract = CONTRACTS.professional_review_contract_fingerprint()
        current_snapshot = CARRY.professional_carry_snapshot(
            self.bindings,
            review_contract_fingerprint=current_contract,
        )
        changed_projection = CONTRACTS.professional_schema3_contract_projection()
        changed_projection["binding_contracts"]["currentness_projection"][
            "version"
        ] = "professional-conservative-material-projection-other"
        changed_contract = CONTRACTS.professional_review_contract_fingerprint(
            changed_projection
        )
        plan = CARRY.plan_exact_professional_carry_forward(
            current_bindings=self.bindings,
            prior_snapshot=current_snapshot,
            prior_decision_dependencies=self.dependencies,
            review_contract_fingerprint=changed_contract,
        )
        self.assertNotEqual(current_contract, changed_contract)
        self.assertEqual(list(SKILL_IDS), plan["fresh_target_ids"])
        self.assertEqual(
            ["review-contract-changed"], plan["reasons_by_target"]["a"]
        )

    def test_presentation_only_markdown_changes_carry_with_new_raw_sha(self) -> None:
        cases = (
            _catalog(
                roots={
                    "d": (
                        "# d\r\n\r\nReview d\r\n"
                        "root behavior.\r\n"
                    )
                }
            ),
            _catalog(
                roots={
                    "d": (
                        "# d\n\n"
                        "<!-- BEGIN CHANGEFORGE CORE DOCS PROJECTION: d -->\n"
                        "Review d root behavior.\n"
                        "<!-- END CHANGEFORGE CORE DOCS PROJECTION: d -->\n"
                    )
                }
            ),
            _catalog(roots={"d": "# d\n\n**Review** d root behavior.\n"}),
            _catalog(roots={"d": "# d\n\nReview   d root behavior.\n"}),
            _catalog(roots={"d": "# d\n    \nReview d root behavior.\n"}),
            _catalog(roots={"d": "# d\n\t\nReview d root behavior.\n"}),
            _catalog(
                roots={
                    "d": (
                        "# d\n\n"
                        "<!-- rd-semantic-id:v2 finding=fixed_number_candidate "
                        "rule=d/rule occurrence=d-one -->\n"
                        "Review d root behavior.\n"
                    )
                }
            ),
        )
        baseline_content = self.bindings["d"]["content_fingerprint"]
        for targets in cases:
            with self.subTest(content=targets[3]["root"]["content"]):
                current = CARRY.professional_review_bindings(targets)
                self.assertNotEqual(
                    baseline_content, current["d"]["content_fingerprint"]
                )
                self.assertEqual(
                    self.bindings["d"]["package_material_binding"],
                    current["d"]["package_material_binding"],
                )
                plan = self._plan(targets)
                self.assertEqual([], plan["fresh_target_ids"])
                self.assertEqual(list(SKILL_IDS), plan["carry_target_ids"])

    def test_unicode_nfc_carries_but_compatibility_and_case_do_not(self) -> None:
        composed = _catalog(
            roots={"d": "# d\n\nReview café behavior.\n"}
        )
        decomposed = _catalog(
            roots={"d": "# d\n\nReview cafe\u0301 behavior.\n"}
        )
        fullwidth = _catalog(
            roots={"d": "# d\n\nReview Ａ behavior.\n"}
        )
        compatibility = _catalog(
            roots={"d": "# d\n\nReview A behavior.\n"}
        )
        composed_bindings = CARRY.professional_review_bindings(composed)
        decomposed_bindings = CARRY.professional_review_bindings(decomposed)
        fullwidth_bindings = CARRY.professional_review_bindings(fullwidth)
        compatibility_bindings = CARRY.professional_review_bindings(
            compatibility
        )
        self.assertNotEqual(
            composed_bindings["d"]["content_fingerprint"],
            decomposed_bindings["d"]["content_fingerprint"],
        )
        self.assertEqual(
            composed_bindings["d"]["package_material_binding"],
            decomposed_bindings["d"]["package_material_binding"],
        )
        packet, ballots, decision = _prior_artifacts(composed)
        nfc_plan = CARRY.plan_exact_professional_carry_forward(
            current_bindings=decomposed_bindings,
            prior_snapshot=CARRY.professional_carry_snapshot(
                composed_bindings,
                review_contract_fingerprint=CONTRACT_FINGERPRINT,
            ),
            prior_decision_dependencies=(
                CARRY.professional_prior_decision_dependencies(
                    prior_packet=packet,
                    prior_ballots=ballots,
                    prior_decision=decision,
                )
            ),
            review_contract_fingerprint=CONTRACT_FINGERPRINT,
        )
        self.assertEqual([], nfc_plan["fresh_target_ids"])
        self.assertEqual(list(SKILL_IDS), nfc_plan["carry_target_ids"])
        self.assertNotEqual(
            fullwidth_bindings["d"]["package_material_binding"],
            compatibility_bindings["d"]["package_material_binding"],
        )

    def test_frontmatter_and_unordered_marker_presentation_changes_carry(
        self,
    ) -> None:
        baseline = _catalog(
            roots={
                "d": (
                    "---\n"
                    "name: d\n"
                    'description: "Review d behavior."\n'
                    "---\n\n"
                    "# d\n\n"
                    "- Review d root behavior.\n"
                    "  - Verify d failure evidence.\n"
                )
            }
        )
        presentation = _catalog(
            roots={
                "d": (
                    "---\n"
                    'description: "Review d behavior."\n'
                    "name: d\n"
                    "---\n\n"
                    "# d\n\n"
                    "* **Review** d root\n"
                    "  behavior.\n"
                    "  + Verify d failure evidence.\n"
                )
            }
        )
        baseline_bindings = CARRY.professional_review_bindings(baseline)
        current_bindings = CARRY.professional_review_bindings(presentation)
        self.assertNotEqual(
            baseline_bindings["d"]["content_fingerprint"],
            current_bindings["d"]["content_fingerprint"],
        )
        self.assertEqual(
            baseline_bindings["d"]["package_material_binding"],
            current_bindings["d"]["package_material_binding"],
        )
        plan = CARRY.plan_exact_professional_carry_forward(
            current_bindings=current_bindings,
            prior_snapshot=CARRY.professional_carry_snapshot(
                baseline_bindings,
                review_contract_fingerprint=CONTRACT_FINGERPRINT,
            ),
            prior_decision_dependencies=self.dependencies,
            review_contract_fingerprint=CONTRACT_FINGERPRINT,
        )
        self.assertEqual([], plan["fresh_target_ids"])
        self.assertEqual(list(SKILL_IDS), plan["carry_target_ids"])

    def test_parser_authenticated_presentation_families_carry(self) -> None:
        cases = (
            (
                "blockquote-soft-wrap",
                "# d\n\n> Review d root behavior.\n",
                "# d\n\n> **Review** d root\n> behavior.\n",
            ),
            (
                "heading-decoration",
                "# d\n\n## Review input\n",
                "# d\n\nReview input\n------------\n",
            ),
            (
                "fence-decoration",
                "# d\n\n```text\nReview input\n```\n",
                "# d\n\n~~~text\nReview input\n~~~\n",
            ),
            (
                "thematic-decoration",
                "# d\n\n***\n",
                "# d\n\n_ _ _\n",
            ),
            (
                "intraword-strong-decoration",
                "# d\n\nfoobarbaz\n",
                "# d\n\nfoo**bar**baz\n",
            ),
        )
        for label, baseline_text, changed_text in cases:
            baseline_projection = (
                CARRY.professional_markdown_currentness_projection(
                    baseline_text
                )
            )
            changed_projection = (
                CARRY.professional_markdown_currentness_projection(
                    changed_text
                )
            )
            baseline = _catalog(roots={"d": baseline_text})
            changed = _catalog(roots={"d": changed_text})
            baseline_bindings = CARRY.professional_review_bindings(baseline)
            changed_bindings = CARRY.professional_review_bindings(changed)
            packet, ballots, decision = _prior_artifacts(baseline)
            dependencies = CARRY.professional_prior_decision_dependencies(
                prior_packet=packet,
                prior_ballots=ballots,
                prior_decision=decision,
            )
            plan = CARRY.plan_exact_professional_carry_forward(
                current_bindings=changed_bindings,
                prior_snapshot=CARRY.professional_carry_snapshot(
                    baseline_bindings,
                    review_contract_fingerprint=CONTRACT_FINGERPRINT,
                ),
                prior_decision_dependencies=dependencies,
                review_contract_fingerprint=CONTRACT_FINGERPRINT,
            )
            with self.subTest(label=label):
                self.assertEqual(baseline_projection, changed_projection)
                self.assertNotEqual(
                    baseline_bindings["d"]["content_fingerprint"],
                    changed_bindings["d"]["content_fingerprint"],
                )
                self.assertEqual(
                    baseline_bindings["d"]["package_material_binding"],
                    changed_bindings["d"]["package_material_binding"],
                )
                self.assertEqual([], plan["fresh_target_ids"])
                self.assertEqual(list(SKILL_IDS), plan["carry_target_ids"])

    def test_markdown_collision_matrix_is_material_and_scoped(self) -> None:
        cases = (
            (
                "intraword-double-underscore",
                "# d\n\nReview foo__bar__baz.\n",
                "# d\n\nReview foobarbaz.\n",
            ),
            (
                "escaped-emphasis-closer",
                "# d\n\nReview **A\\**\n",
                "# d\n\nReview A\\\n",
            ),
            (
                "html-horizontal-whitespace",
                "# d\n\n<pre>Review  input</pre>\n",
                "# d\n\n<pre>Review input</pre>\n",
            ),
            (
                "fenced-block-under-list",
                "# d\n\n- Review\n  ```text\n  input\n  ```\n",
                "# d\n\n- Review ```text input ```\n",
            ),
            (
                "indented-code-under-list",
                "# d\n\n- Review\n\n      input\n",
                "# d\n\n- Review input\n",
            ),
            (
                "blockquote-under-list",
                "# d\n\n- Review\n  > input\n",
                "# d\n\n- Review > input\n",
            ),
            (
                "table-under-list",
                (
                    "# d\n\n"
                    "- Review\n"
                    "  | A | B |\n"
                    "  | --- | --- |\n"
                ),
                "# d\n\n- Review | A | B | | --- | --- |\n",
            ),
            (
                "unwrapped-gfm-table",
                "# d\n\nA | B\n--- | ---\n",
                "# d\n\nA | B --- | ---\n",
            ),
            (
                "setext-heading",
                "# d\n\nTitle\n===\n",
                "# d\n\nTitle ===\n",
            ),
            (
                "ambiguous-lazy-list-continuation",
                "# d\n\n- Review\nVerify output\n",
                "# d\n\n- Review\n\nVerify output\n",
            ),
            (
                "ambiguous-lazy-list-after-closed-wrap",
                "# d\n\n- Review\n  input\nVerify output\n",
                "# d\n\n- Review\n  input\n\nVerify output\n",
            ),
            (
                "nested-atx-heading-under-list",
                "# d\n\n- Item\n  # Rule\n",
                "# d\n\n- Item # Rule\n",
            ),
            (
                "nested-thematic-break-under-list",
                "# d\n\n- Item\n  ***\n",
                "# d\n\n- Item ***\n",
            ),
            (
                "spaced-star-thematic-break",
                "# d\n\n* * *\n",
                "# d\n\n- * *\n",
            ),
            (
                "spaced-dash-thematic-break",
                "# d\n\n- - -\n",
                "# d\n\n* - -\n",
            ),
            (
                "spaced-underscore-thematic-break",
                "# d\n\n_ _ _\n",
                "# d\n\nReview _ _ _\n",
            ),
            (
                "indented-frontmatter-delimiters",
                (
                    "    ---\n"
                    "name: d\n"
                    'description: "Review d behavior."\n'
                    "    ---\n\n"
                    "# d\n\nReview d root behavior.\n"
                ),
                (
                    "---\n"
                    "name: d\n"
                    'description: "Review d behavior."\n'
                    "---\n\n"
                    "# d\n\nReview d root behavior.\n"
                ),
            ),
            (
                "authenticated-marker-inside-fence",
                (
                    "# d\n\n```text\n"
                    "<!-- BEGIN CHANGEFORGE CORE DOCS PROJECTION: d -->\n"
                    "```\n"
                ),
                "# d\n\n```text\n```\n",
            ),
            (
                "indented-authenticated-marker",
                (
                    "# d\n\n"
                    "    <!-- BEGIN CHANGEFORGE CORE DOCS PROJECTION: d -->\n"
                ),
                (
                    "# d\n\n"
                    "<!-- BEGIN CHANGEFORGE CORE DOCS PROJECTION: d -->\n"
                ),
            ),
            (
                "indented-heading-candidate",
                "# d\n\n    # Rule\n",
                "# d\n\n# Rule\n",
            ),
            (
                "indented-fully-wrapped-table",
                "# d\n\n    | A | B |\n    | --- | --- |\n",
                "# d\n\n| A | B |\n| --- | --- |\n",
            ),
            (
                "ordered-list-block-ownership",
                "# d\n\nReview input\n2. Verify output\n",
                "# d\n\nReview input\n\n2. Verify output\n",
            ),
            (
                "pipe-row-block-ownership",
                "# d\n\nReview input\n| Verify output |\n",
                "# d\n\nReview input\n\n| Verify output |\n",
            ),
            (
                "gfm-table-block-ownership",
                (
                    "# d\n\nReview input\n"
                    "A | B\n"
                    "--- | ---\n"
                ),
                (
                    "# d\n\nReview input\n\n"
                    "A | B\n"
                    "--- | ---\n"
                ),
            ),
            (
                "autolink-block-ownership",
                "# d\n\nReview input\n<https://example.com>\n",
                "# d\n\nReview input\n\n<https://example.com>\n",
            ),
            (
                "list-marker-padding-ownership",
                "# d\n\n- item\n",
                "# d\n\n-     item\n",
            ),
        )
        for label, baseline_text, changed_text in cases:
            baseline_projection = (
                CARRY.professional_markdown_currentness_projection(
                    baseline_text
                )
            )
            changed_projection = (
                CARRY.professional_markdown_currentness_projection(
                    changed_text
                )
            )
            baseline = _catalog(roots={"d": baseline_text})
            changed = _catalog(roots={"d": changed_text})
            baseline_bindings = CARRY.professional_review_bindings(baseline)
            changed_bindings = CARRY.professional_review_bindings(changed)
            snapshot = CARRY.professional_carry_snapshot(
                baseline_bindings,
                review_contract_fingerprint=CONTRACT_FINGERPRINT,
            )
            packet, ballots, decision = _prior_artifacts(baseline)
            dependencies = CARRY.professional_prior_decision_dependencies(
                prior_packet=packet,
                prior_ballots=ballots,
                prior_decision=decision,
            )
            plan = CARRY.plan_exact_professional_carry_forward(
                current_bindings=changed_bindings,
                prior_snapshot=snapshot,
                prior_decision_dependencies=dependencies,
                review_contract_fingerprint=CONTRACT_FINGERPRINT,
            )
            with self.subTest(label=label):
                self.assertNotEqual(
                    baseline_projection,
                    changed_projection,
                )
                self.assertNotEqual(
                    baseline_bindings["d"]["package_material_binding"],
                    changed_bindings["d"]["package_material_binding"],
                )
                self.assertEqual(["b", "d"], plan["fresh_target_ids"])
                self.assertIn(
                    "target-material-changed",
                    plan["reasons_by_target"]["d"],
                )
                self.assertIn(
                    "required-candidate-material-changed",
                    plan["reasons_by_target"]["b"],
                )
                self.assertEqual([], plan["reasons_by_target"]["a"])
                self.assertEqual([], plan["reasons_by_target"]["c"])

    def test_opaque_markdown_preserves_whitespace_and_final_newline(self) -> None:
        cases = (
            (
                "horizontal-whitespace",
                "# d\n\n<pre>Review  input</pre>\n",
                "# d\n\n<pre>Review input</pre>\n",
            ),
            (
                "blank-whitespace",
                "# d\n\n<pre>Review input\n \nVerify output</pre>\n",
                "# d\n\n<pre>Review input\n\nVerify output</pre>\n",
            ),
            (
                "final-newline",
                "# d\n\n<pre>Review input</pre>\n",
                "# d\n\n<pre>Review input</pre>",
            ),
        )
        for label, baseline_text, changed_text in cases:
            with self.subTest(label=label):
                self.assertNotEqual(
                    CARRY.professional_markdown_currentness_projection(
                        baseline_text
                    ),
                    CARRY.professional_markdown_currentness_projection(
                        changed_text
                    ),
                )

    def test_markdown_hard_break_is_not_normalized_as_soft_wrapping(self) -> None:
        hard_break = "# d\n\nReview input.  \nVerify output.\n"
        one_paragraph = "# d\n\nReview input. Verify output.\n"
        hard_projection = (
            CARRY.professional_markdown_currentness_projection(hard_break)
        )
        self.assertNotEqual("opaque-document", hard_projection[0]["type"])
        self.assertNotEqual(
            hard_projection,
            CARRY.professional_markdown_currentness_projection(one_paragraph),
        )

    def test_unsupported_parser_families_make_the_whole_body_opaque(self) -> None:
        cases = (
            "# d\n\n1. Review input\n",
            "# d\n\n| A | B |\n| --- | --- |\n",
            "# d\n\n<pre>Review input</pre>\n",
            "# d\n\n[Review][rule]\n\n[rule]: /input\n",
        )
        for content in cases:
            with self.subTest(content=content):
                projection = (
                    CARRY.professional_markdown_currentness_projection(content)
                )
                self.assertEqual("opaque-document", projection[0]["type"])
                self.assertEqual(content, projection[0]["value"])

    def test_commonmark_emphasis_is_presentation_but_unmatched_is_material(
        self,
    ) -> None:
        for decorated, plain in (
            ("# d\n\n**Review _input_**\n", "# d\n\nReview input\n"),
            ("# d\n\nfoo**bar**baz\n", "# d\n\nfoobarbaz\n"),
        ):
            with self.subTest(decorated=decorated):
                self.assertEqual(
                    CARRY.professional_markdown_currentness_projection(decorated),
                    CARRY.professional_markdown_currentness_projection(plain),
                )
        self.assertNotEqual(
            CARRY.professional_markdown_currentness_projection(
                "# d\n\n**Review input\n"
            ),
            CARRY.professional_markdown_currentness_projection(
                "# d\n\nReview input\n"
            ),
        )

    def test_possible_prose_semantic_changes_are_fresh_not_inferred(self) -> None:
        cases = {
            "spelling": "# d\n\nReveiw d root behavior.\n",
            "synonym": "# d\n\nInspect d root behavior.\n",
            "compression": "# d\n\nReview d behavior.\n",
            "action": "# d\n\nDelete d root behavior.\n",
            "object": "# d\n\nReview d root contract.\n",
            "direction": "# d\n\nReview input from d root behavior.\n",
            "condition": "# d\n\nReview d root behavior unless valid.\n",
            "constraint": "# d\n\nMay review d root behavior.\n",
            "case": "# d\n\nreview d root behavior.\n",
            "punctuation": "# d\n\nReview d root behavior!\n",
            "unauthenticated-comment": (
                "# d\n\n<!-- ordinary prose note -->\n"
                "Review d root behavior.\n"
            ),
        }
        for label, content in cases.items():
            targets = _catalog(roots={"d": content})
            with self.subTest(label=label):
                plan = self._plan(targets)
                self.assertEqual(["b", "d"], plan["fresh_target_ids"])
                self.assertIn(
                    "target-material-changed",
                    plan["reasons_by_target"]["d"],
                )
                self.assertIn(
                    "required-candidate-material-changed",
                    plan["reasons_by_target"]["b"],
                )
                self.assertEqual([], plan["reasons_by_target"]["a"])
                self.assertEqual([], plan["reasons_by_target"]["c"])

    def test_order_nesting_code_link_table_and_opaque_changes_are_fresh(
        self,
    ) -> None:
        cases = (
            (
                "heading-level",
                "# d\n\nReview input.\n",
                "## d\n\nReview input.\n",
            ),
            (
                "paragraph-list-type",
                "# d\n\nReview input.\n",
                "# d\n\n- Review input.\n",
            ),
            (
                "ordered-step",
                (
                    "# d\n\n"
                    "1. Review input.\n"
                    "2. Verify output.\n"
                ),
                (
                    "# d\n\n"
                    "1. Verify output.\n"
                    "2. Review input.\n"
                ),
            ),
            (
                "nested-owner",
                (
                    "# d\n\n"
                    "- Review input.\n"
                    "  - Verify output.\n"
                ),
                (
                    "# d\n\n"
                    "- Review input.\n"
                    "- Verify output.\n"
                ),
            ),
            (
                "fenced-code",
                "# d\n\n" + "\x60\x60\x60text\nreview input\n\x60\x60\x60\n",
                "# d\n\n" + "\x60\x60\x60text\nreview output\n\x60\x60\x60\n",
            ),
            (
                "inline-code",
                "# d\n\nReview \x60input\x60 exactly.\n",
                "# d\n\nReview \x60output\x60 exactly.\n",
            ),
            (
                "link-destination",
                "# d\n\nReview [input](references/input.md).\n",
                "# d\n\nReview [input](references/output.md).\n",
            ),
            (
                "link-title",
                '# d\n\nReview [input](references/input.md "input").\n',
                '# d\n\nReview [input](references/input.md "output").\n',
            ),
            (
                "image-source",
                "# d\n\nReview ![input](images/input.png).\n",
                "# d\n\nReview ![input](images/output.png).\n",
            ),
            (
                "commonmark-autolink",
                "# d\n\nReview <https://example.com/input>.\n",
                "# d\n\nReview <https://example.com/output>.\n",
            ),
            (
                "link-leading-boundary-whitespace",
                "# d\n\nReview [input](references/input.md).\n",
                "# d\n\nReview[input](references/input.md).\n",
            ),
            (
                "link-trailing-boundary-whitespace",
                "# d\n\n[Review](references/input.md) input.\n",
                "# d\n\n[Review](references/input.md)input.\n",
            ),
            (
                "inline-code-boundary-whitespace",
                "# d\n\nReview `input`.\n",
                "# d\n\nReview`input`.\n",
            ),
            (
                "image-boundary-whitespace",
                "# d\n\nUse ![safe](images/input.png) input.\n",
                "# d\n\nUse![safe](images/input.png) input.\n",
            ),
            (
                "link-label-boundary-whitespace",
                "# d\n\nReview [ input ](references/input.md).\n",
                "# d\n\nReview [input](references/input.md).\n",
            ),
            (
                "autolink-boundary-whitespace",
                "# d\n\nReview <https://example.com>.\n",
                "# d\n\nReview<https://example.com>.\n",
            ),
            (
                "table-cell",
                (
                    "# d\n\n"
                    "| Action | Object |\n"
                    "| --- | --- |\n"
                    "| Review | input |\n"
                ),
                (
                    "# d\n\n"
                    "| Action | Object |\n"
                    "| --- | --- |\n"
                    "| Review | output |\n"
                ),
            ),
            (
                "opaque-block",
                "# d\n\n> Review input conservatively.\n",
                "# d\n\n> Delete input conservatively.\n",
            ),
        )
        for label, baseline_text, changed_text in cases:
            baseline = _catalog(roots={"d": baseline_text})
            changed = _catalog(roots={"d": changed_text})
            baseline_bindings = CARRY.professional_review_bindings(baseline)
            snapshot = CARRY.professional_carry_snapshot(
                baseline_bindings,
                review_contract_fingerprint=CONTRACT_FINGERPRINT,
            )
            packet, ballots, decision = _prior_artifacts(baseline)
            dependencies = CARRY.professional_prior_decision_dependencies(
                prior_packet=packet,
                prior_ballots=ballots,
                prior_decision=decision,
            )
            with self.subTest(label=label):
                plan = CARRY.plan_exact_professional_carry_forward(
                    current_bindings=CARRY.professional_review_bindings(changed),
                    prior_snapshot=snapshot,
                    prior_decision_dependencies=dependencies,
                    review_contract_fingerprint=CONTRACT_FINGERPRINT,
                )
                self.assertEqual(["b", "d"], plan["fresh_target_ids"])

    def test_complete_structured_authority_changes_are_fresh(self) -> None:
        cases = {
            "responsibility": _catalog(
                responsibility_overrides={
                    "d": {"role_support": ["analysis-agent"]}
                }
            ),
            "trigger": _catalog(
                responsibility_overrides={
                    "d": {"trigger_signals": ["changed trigger"]}
                }
            ),
            "anti-trigger": _catalog(
                responsibility_overrides={
                    "d": {"anti_trigger_signals": ["changed anti-trigger"]}
                }
            ),
            "required-input": _catalog(
                responsibility_overrides={
                    "d": {"required_inputs": ["changed input"]}
                }
            ),
            "required-output": _catalog(
                responsibility_overrides={
                    "d": {"output_contract": ["changed output"]}
                }
            ),
            "constraint": _catalog(
                responsibility_overrides={
                    "d": {"escalation_signals": ["changed constraint"]}
                }
            ),
            "routing-boundary": _catalog(
                responsibility_overrides={
                    "d": {"boundary_signals": ["changed boundary"]}
                }
            ),
            "layer3": _catalog(
                responsibility_overrides={
                    "d": {"layer3_candidates": ["a"]}
                }
            ),
            "used-by": _catalog(
                responsibility_overrides={"d": {"used_by": ["a"]}}
            ),
            "task-routable": _catalog(
                responsibility_overrides={"d": {"task_routable": False}}
            ),
            "required-expertise": _catalog(
                expertise={"d": ["domain", "security"]}
            ),
            "registry-extra-authority": _catalog(
                registry_authority_overrides={
                    "d": {"routing_mode": "direct"}
                }
            ),
        }
        for label, targets in cases.items():
            with self.subTest(label=label):
                plan = self._plan(targets)
                self.assertEqual(["b", "d"], plan["fresh_target_ids"])
                self.assertIn(
                    "target-material-changed",
                    plan["reasons_by_target"]["d"],
                )

    def test_reference_loading_authority_changes_are_fresh(self) -> None:
        base = copy.deepcopy(self.targets[3]["reference_authority"][0])
        changes = {
            "identity": ("path", "renamed-reference.md"),
            "type": ("type", "decision-checklist"),
            "load-when": (
                "load_when",
                "Reviewing d recovery evidence for this bounded task",
            ),
            "do-not-load-when": (
                "do_not_load_when",
                "The d recovery boundary is already fully evidenced",
            ),
            "required-by": ("required_by", ["analysis-agent"]),
            "required-output": (
                "required_output",
                ["checklist-result", "residual-risk"],
            ),
        }
        for label, (field, value) in changes.items():
            reference = copy.deepcopy(base)
            reference[field] = value
            targets = _catalog(
                reference_authority_overrides={"d": [reference]}
            )
            if field == "path":
                targets[3]["indexed_references"][0]["path"] = (
                    "src/d/renamed-reference.md"
                )
            with self.subTest(label=label):
                plan = self._plan(targets)
                self.assertEqual(["b", "d"], plan["fresh_target_ids"])
                self.assertIn(
                    "target-material-changed",
                    plan["reasons_by_target"]["d"],
                )

    def test_raw_material_integrity_mismatch_fails_closed(self) -> None:
        cases = []
        stale_content = _catalog()
        stale_content[3]["root"]["content"] += "changed"
        cases.append(stale_content)
        stale_digest = _catalog()
        stale_digest[3]["root"]["sha256"] = "0" * 64
        cases.append(stale_digest)
        stale_line_count = _catalog()
        stale_line_count[3]["root"]["line_count"] += 1
        cases.append(stale_line_count)
        for targets in cases:
            with self.subTest(record=targets[3]["root"]), self.assertRaises(
                CARRY.ProfessionalCarryForwardError
            ):
                CARRY.professional_review_bindings(targets)

    def test_missing_or_drifting_structured_authority_fails_closed(self) -> None:
        missing_registry = _catalog()
        missing_registry[0].pop("registry_authority")
        missing_reference = _catalog()
        missing_reference[0].pop("reference_authority")
        mismatched_reference = _catalog()
        mismatched_reference[0]["registry_authority"]["reference_index"][0][
            "load_when"
        ] = "A different authenticated loading condition"
        drifting_compatibility = _catalog()
        drifting_compatibility[0]["registry"]["responsibility_contract"][
            "output_contract"
        ] = ["drifted compatibility output"]
        duplicate_reference = _catalog()
        duplicate_reference[0]["reference_authority"].append(
            copy.deepcopy(duplicate_reference[0]["reference_authority"][0])
        )
        duplicate_reference[0]["registry_authority"]["reference_index"] = (
            copy.deepcopy(duplicate_reference[0]["reference_authority"])
        )
        for targets in (
            missing_registry,
            missing_reference,
            mismatched_reference,
            drifting_compatibility,
            duplicate_reference,
        ):
            with self.subTest(target=targets[0]), self.assertRaises(
                CARRY.ProfessionalCarryForwardError
            ):
                CARRY.professional_review_bindings(targets)

    def test_currentness_contract_has_no_natural_language_inference_authority(
        self,
    ) -> None:
        serialized = json.dumps(
            CONTRACTS.PROFESSIONAL_CURRENTNESS_PROJECTION_CONTRACT,
            sort_keys=True,
        )
        for forbidden in (
            "lexical:",
            "synonym",
            "stemming",
            "part-of-speech",
            "predicate-owner",
            "modal-passive",
            "gerund",
            "infinitive",
        ):
            self.assertNotIn(forbidden, serialized)
        self.assertEqual(
            "unsupported-or-ambiguous-markdown-is-opaque-and-change-is-fresh",
            CONTRACTS.PROFESSIONAL_CURRENTNESS_PROJECTION_CONTRACT[
                "unsupported_markdown"
            ],
        )
        self.assertEqual(
            "professional-commonmark-material-projection-v4",
            CONTRACTS.PROFESSIONAL_CURRENTNESS_PROJECTION_VERSION,
        )
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('"markdown-it-py==4.2.0"', pyproject)
        self.assertIn('"mdurl==0.1.2"', pyproject)

    def test_markdown_parser_distribution_mismatch_fails_closed(self) -> None:
        actual = {
            "markdown-it-py": "4.2.0",
            "mdurl": "0.1.2",
        }
        for distribution in actual:
            changed = dict(actual)
            changed[distribution] = "unexpected"
            with self.subTest(distribution=distribution), mock.patch.object(
                CARRY.importlib_metadata,
                "version",
                side_effect=lambda name, versions=changed: versions[name],
            ), self.assertRaisesRegex(
                CARRY.ProfessionalCarryForwardError,
                rf"{distribution}=={actual[distribution]}",
            ):
                CARRY.professional_markdown_currentness_projection(
                    "# d\n\nReview input.\n"
                )
        with mock.patch.object(
            CARRY.importlib_metadata,
            "version",
            side_effect=CARRY.importlib_metadata.PackageNotFoundError(
                "markdown-it-py"
            ),
        ), self.assertRaisesRegex(
            CARRY.ProfessionalCarryForwardError,
            "markdown-it-py==4.2.0",
        ):
            CARRY.professional_markdown_currentness_projection(
                "# d\n\nReview input.\n"
            )

    def test_markdown_parser_options_and_rules_match_the_contract(self) -> None:
        parser = CARRY._verified_professional_markdown_parser()
        parser_contract = (
            CONTRACTS.PROFESSIONAL_CURRENTNESS_PROJECTION_CONTRACT["parser"]
        )
        self.assertEqual(
            parser_contract["active_rules"], parser.get_active_rules()
        )
        for option, expected in parser_contract["options"].items():
            self.assertEqual(expected, parser.options[option])

    def test_unknown_parser_token_attrs_and_metadata_fall_back_to_opaque(
        self,
    ) -> None:
        content = "# d\n\nReview input.\n"
        tokens, environment = CARRY._parse_professional_markdown(content)
        mutations = (
            ("unknown-token", 0, "type", "plugin_block"),
            ("unexpected-attrs", 0, "attrs", {"plugin": "value"}),
            ("unexpected-meta", 0, "meta", {"plugin": "value"}),
            ("unexpected-nesting", 0, "nesting", 0),
        )
        for label, index, field, value in mutations:
            changed_tokens = copy.deepcopy(tokens)
            setattr(changed_tokens[index], field, value)
            with self.subTest(label=label), mock.patch.object(
                CARRY,
                "_parse_professional_markdown",
                return_value=(changed_tokens, copy.deepcopy(environment)),
            ):
                projection = (
                    CARRY.professional_markdown_currentness_projection(content)
                )
                self.assertEqual(
                    [{"type": "opaque-document", "value": content}],
                    projection,
                )

    def test_currentness_binding_rejects_forged_and_unknown_authority(self) -> None:
        missing = _catalog()
        missing[0]["registry"]["responsibility_contract"].pop(
            "output_contract"
        )
        malformed = _catalog()
        malformed[0]["registry"]["responsibility_contract"][
            "required_inputs"
        ] = "not-a-list"
        noncanonical = _catalog()
        noncanonical[0]["required_expertise_tags"] = ["z", "a"]
        unknown_dependency = _catalog(
            required={"a": ["unknown"]},
            rankings={"a": ["b", "c", "d", "unknown"]},
        )
        for targets in (
            missing,
            malformed,
            noncanonical,
            unknown_dependency,
        ):
            with self.subTest(target=targets[0]), self.assertRaises(
                CARRY.ProfessionalCarryForwardError
            ):
                CARRY.professional_review_bindings(targets)

        forged = copy.deepcopy(self.bindings)
        forged["a"]["package_material_binding"] = "0" * 64
        with self.assertRaisesRegex(
            CARRY.ProfessionalCarryForwardError,
            "package_material_binding is stale",
        ):
            CARRY.professional_carry_snapshot(
                forged,
                review_contract_fingerprint=CONTRACT_FINGERPRINT,
            )

    def test_unselected_ranking_churn_does_not_reopen_target(self) -> None:
        rank_plan = self._plan(
            _catalog(rankings={"d": ["c", "b", "a"]})
        )

        self.assertEqual([], rank_plan["fresh_target_ids"])
        self.assertEqual(list(SKILL_IDS), rank_plan["carry_target_ids"])
        self.assertEqual([], rank_plan["reasons_by_target"]["d"])

    def test_required_list_change_reopens_only_target(self) -> None:
        required_plan = self._plan(
            _catalog(required={"b": ["d"], "c": ["a"], "d": ["a"]})
        )

        self.assertEqual(["d"], required_plan["fresh_target_ids"])
        self.assertEqual(
            ["adjacency-review-binding-changed"],
            required_plan["reasons_by_target"]["d"],
        )
        self.assertEqual([], required_plan["reasons_by_target"]["b"])

    def test_target_binding_contains_only_local_selection_authority(self) -> None:
        binding = self.bindings["b"]

        self.assertEqual(
            {
                "required_candidate_ids",
                "selection_contract_version",
            },
            set(binding["adjacency"]),
        )
        self.assertEqual(["d"], binding["adjacency"]["required_candidate_ids"])
        self.assertEqual(
            "fixture-selection-v1",
            binding["adjacency"]["selection_contract_version"],
        )
        serialized = CARRY.canonical_json_bytes(
            CARRY.professional_carry_snapshot(
                self.bindings,
                review_contract_fingerprint=CONTRACT_FINGERPRINT,
            )["targets"]["b"]
        )
        snapshot_target = CARRY.professional_carry_snapshot(
            self.bindings,
            review_contract_fingerprint=CONTRACT_FINGERPRINT,
        )["targets"]["b"]
        self.assertNotIn("content_fingerprint", snapshot_target)
        for forbidden in (
            b"content_fingerprint",
            b"own_material",
            b"required_candidates_fingerprint",
            b"full_catalog_ranking",
            b"full_catalog_ranking_fingerprint",
        ):
            self.assertNotIn(forbidden, serialized)

    def test_catalog_intermediate_filter_change_does_not_stale_all_targets(self) -> None:
        changed = CARRY.professional_review_bindings(
            _catalog(document_filter_marker="changed-global-intermediate")
        )
        self.assertEqual(self.bindings, changed)
        plan = CARRY.plan_exact_professional_carry_forward(
            current_bindings=changed,
            prior_snapshot=self.snapshot,
            prior_decision_dependencies=self.dependencies,
            review_contract_fingerprint=CONTRACT_FINGERPRINT,
        )
        self.assertEqual([], plan["fresh_target_ids"])

    def test_minority_reviewer_added_dependency_is_union_and_one_hop(self) -> None:
        self.assertEqual(
            ["b"],
            self.dependencies["a"][
                "reviewer_added_candidate_ids_union"
            ],
        )
        # b changes. a is fresh because one prior ballot added b; c reviews a,
        # but a's fresh status is not recursively propagated to c.
        plan = self._plan(
            _catalog(
                roots={
                    "b": (
                        "# b\n\n## Professional Decision Rules\n\n"
                        "- Do not validate outputs before release.\n"
                    )
                }
            )
        )
        self.assertEqual(["a", "b"], plan["fresh_target_ids"])
        self.assertIn(
            "reviewer-added-candidate-material-changed",
            plan["reasons_by_target"]["a"],
        )
        self.assertEqual([], plan["reasons_by_target"]["c"])

    def test_duplicate_ballot_identity_cannot_form_complete_evidence(self) -> None:
        packet, ballots, decision = _prior_artifacts(self.targets)
        with self.assertRaisesRegex(
            CARRY.ProfessionalCarryForwardError, "duplicate voter_id"
        ):
            CARRY.professional_prior_decision_dependencies(
                prior_packet=packet,
                prior_ballots=[ballots[0], ballots[0], ballots[0]],
                prior_decision=decision,
            )

    def test_missing_evidence_and_nonaccepted_prior_are_never_carried(self) -> None:
        missing = copy.deepcopy(self.dependencies)
        missing["a"]["evidence_complete"] = False
        missing_plan = self._plan(
            self.targets, prior_decision_dependencies=missing
        )
        self.assertEqual(["a"], missing_plan["fresh_target_ids"])
        for disposition in (
            "requires-professional-correction",
            "unresolved-professional-disagreement",
        ):
            with self.subTest(disposition=disposition):
                nonaccepted = copy.deepcopy(self.dependencies)
                nonaccepted["a"]["final_disposition"] = disposition
                plan = self._plan(
                    self.targets,
                    prior_decision_dependencies=nonaccepted,
                )
                self.assertEqual(["a"], plan["fresh_target_ids"])
                self.assertIn(
                    "prior-final-not-accepted",
                    plan["reasons_by_target"]["a"],
                )

    def test_partition_and_reason_order_are_deterministic(self) -> None:
        targets = _catalog(
            roots={"b": "# b\n\nChanged deterministic evidence.\n"}
        )
        first = self._plan(targets)
        second = self._plan(copy.deepcopy(targets))
        self.assertEqual(first, second)
        self.assertEqual(
            CARRY.canonical_json_bytes(first),
            CARRY.canonical_json_bytes(second),
        )

    def test_capsule_exact_projection_and_reviewer_added_material(self) -> None:
        request = self._request("a", "b")
        capsule = CARRY.project_professional_review_capsule(
            bindings=self.bindings,
            review_targets=self.targets,
            assigned_fresh_target_ids=["a"],
            reviewer_added_requests_by_target={"a": [request]},
        )
        validated = CARRY.validate_professional_review_capsule(
            capsule,
            bindings=self.bindings,
            review_targets=self.targets,
            assigned_fresh_target_ids=["a"],
            reviewer_added_requests_by_target={"a": [request]},
        )
        self.assertIs(capsule, validated)
        target = capsule["targets"][0]
        self.assertEqual(
            ["b"],
            [row["skill_id"] for row in target["candidate_material_manifest"]],
        )
        self.assertEqual(
            ["a", "b"],
            [row["skill_id"] for row in capsule["material_catalog"]],
        )
        self.assertNotIn("adjacency", capsule["material_catalog"][1])
        self.assertNotIn("material", target)
        self.assertNotIn("candidate_materials", target)
        self.assertIn("full_catalog_ranking", target["adjacency"])
        self.assertEqual(
            request["discovery_reason"],
            target["candidate_material_manifest"][0]["discovery_reason"],
        )

    def test_discovery_capsule_has_required_material_and_complete_boundary_catalog(self) -> None:
        discovery = CARRY.project_professional_discovery_capsule(
            bindings=self.bindings,
            review_targets=self.targets,
            assigned_fresh_target_ids=["b"],
        )
        self.assertIs(
            discovery,
            CARRY.validate_professional_discovery_capsule(
                discovery,
                bindings=self.bindings,
                review_targets=self.targets,
                assigned_fresh_target_ids=["b"],
            ),
        )
        self.assertEqual(
            list(SKILL_IDS),
            [row["skill_id"] for row in discovery["boundary_catalog"]],
        )
        self.assertEqual(
            ["b", "d"],
            [row["skill_id"] for row in discovery["material_catalog"]],
        )

    def test_capsule_rejects_extra_missing_duplicate_and_stale_projection(self) -> None:
        expected_arguments = {
            "bindings": self.bindings,
            "review_targets": self.targets,
            "assigned_fresh_target_ids": ["a"],
            "reviewer_added_requests_by_target": {
                "a": [self._request("a", "b")]
            },
        }
        capsule = CARRY.project_professional_review_capsule(**expected_arguments)
        mutations = []
        missing_target = copy.deepcopy(capsule)
        missing_target["targets"] = []
        mutations.append(missing_target)
        duplicate_target = copy.deepcopy(capsule)
        duplicate_target["targets"].append(copy.deepcopy(duplicate_target["targets"][0]))
        mutations.append(duplicate_target)
        missing_catalog_material = copy.deepcopy(capsule)
        missing_catalog_material["material_catalog"] = [
            row
            for row in missing_catalog_material["material_catalog"]
            if row["skill_id"] != "b"
        ]
        mutations.append(missing_catalog_material)
        duplicate_catalog_material = copy.deepcopy(capsule)
        duplicate_catalog_material["material_catalog"].append(
            copy.deepcopy(duplicate_catalog_material["material_catalog"][0])
        )
        mutations.append(duplicate_catalog_material)
        duplicate_candidate = copy.deepcopy(capsule)
        duplicate_candidate["targets"][0]["candidate_material_manifest"].append(
            copy.deepcopy(
                duplicate_candidate["targets"][0]["candidate_material_manifest"][0]
            )
        )
        mutations.append(duplicate_candidate)
        stale = copy.deepcopy(capsule)
        stale["material_catalog"][0]["own_material"]["root"][
            "content"
        ] += "stale"
        mutations.append(stale)
        extra_top_level_field = copy.deepcopy(capsule)
        extra_top_level_field["unexpected"] = True
        mutations.append(extra_top_level_field)
        extra_target_field = copy.deepcopy(capsule)
        extra_target_field["targets"][0]["unexpected"] = True
        mutations.append(extra_target_field)
        extra_nested_field = copy.deepcopy(capsule)
        extra_nested_field["targets"][0]["candidate_material_manifest"][0][
            "unexpected"
        ] = True
        mutations.append(extra_nested_field)
        extra = copy.deepcopy(capsule)
        extra_material = CARRY.project_professional_review_capsule(
            bindings=self.bindings,
            review_targets=self.targets,
            assigned_fresh_target_ids=["d"],
        )["material_catalog"][0]
        extra["material_catalog"].append(extra_material)
        mutations.append(extra)
        for index, value in enumerate(mutations):
            with self.subTest(index=index), self.assertRaises(
                CARRY.ProfessionalCarryForwardError
            ):
                CARRY.validate_professional_review_capsule(
                    value, **expected_arguments
                )

    def test_raw_source_change_still_invalidates_capsule_integrity(self) -> None:
        capsule = CARRY.project_professional_review_capsule(
            bindings=self.bindings,
            review_targets=self.targets,
            assigned_fresh_target_ids=["b"],
        )
        changed_targets = _catalog(
            roots={"d": "# d\n\n**Review** d root behavior.\n"}
        )
        changed_bindings = CARRY.professional_review_bindings(
            changed_targets
        )
        plan = self._plan(changed_targets)
        self.assertEqual([], plan["fresh_target_ids"])
        with self.assertRaisesRegex(
            CARRY.ProfessionalCarryForwardError,
            "projection is stale|material_catalog projection is stale",
        ):
            CARRY.validate_professional_review_capsule(
                capsule,
                bindings=changed_bindings,
                review_targets=changed_targets,
                assigned_fresh_target_ids=["b"],
            )

        forged_targets = copy.deepcopy(changed_targets)
        forged_targets[3]["root"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(
            CARRY.ProfessionalCarryForwardError, "sha256 must bind content"
        ):
            CARRY.professional_review_bindings(forged_targets)

    def test_capsule_reviewer_added_ids_must_be_unique_ranked_and_not_required(self) -> None:
        for added in ([self._request("a", "a")], [self._request("a", "b")] * 2):
            with self.subTest(added=added), self.assertRaises(
                CARRY.ProfessionalCarryForwardError
            ):
                CARRY.project_professional_review_capsule(
                    bindings=self.bindings,
                    review_targets=self.targets,
                    assigned_fresh_target_ids=["a"],
                    reviewer_added_requests_by_target={"a": added},
                )
        with self.assertRaisesRegex(
            CARRY.ProfessionalCarryForwardError, "already packet-required"
        ):
            CARRY.project_professional_review_capsule(
                bindings=self.bindings,
                review_targets=self.targets,
                assigned_fresh_target_ids=["b"],
                reviewer_added_requests_by_target={
                    "b": [self._request("b", "d")]
                },
            )

    def test_material_paths_must_be_canonical_repository_relative(self) -> None:
        for path in ("../escape.md", "a/../b.md", "a\\b.md", "/abs.md"):
            targets = copy.deepcopy(self.targets)
            targets[0]["root"]["path"] = path
            with self.subTest(path=path), self.assertRaises(
                CARRY.ProfessionalCarryForwardError
            ):
                CARRY.professional_review_bindings(targets)

    def test_capsule_cost_proxy_uses_canonical_unicode_bytes(self) -> None:
        left = {"z": "技能", "a": {"b": 1}}
        right = {"a": {"b": 1}, "z": "技能"}
        self.assertEqual(
            CARRY.canonical_json_bytes(left), CARRY.canonical_json_bytes(right)
        )
        left_cost = CARRY.professional_review_capsule_cost_proxy(left)
        right_cost = CARRY.professional_review_capsule_cost_proxy(right)
        self.assertEqual(left_cost, right_cost)
        self.assertEqual(
            len(CARRY.canonical_json_bytes(left)),
            left_cost["canonical_json_bytes_proxy"],
        )
        self.assertTrue(all("proxy" in key or "available" in key for key in left_cost))


class ProfessionalReviewContractFingerprintTests(unittest.TestCase):
    def tearDown(self) -> None:
        PANEL._professional_evidence_review_contract_fingerprint.cache_clear()

    def test_review_contract_uses_canonical_semantic_projection(self) -> None:
        projection = CONTRACTS.professional_schema3_contract_projection()
        self.assertEqual(
            "professional-completeness-schema3-review-carry-v3",
            projection["contract_version"],
        )
        self.assertEqual(3, projection["artifact_contract"]["schema_version"])
        self.assertEqual(3, projection["panel"]["exact_votes_per_target"])
        self.assertEqual(
            CONTRACTS.canonical_json_sha256(projection),
            PANEL._professional_evidence_review_contract_fingerprint(),
        )

        encoded = CONTRACTS.canonical_json_bytes(projection)
        for forbidden in (
            b"scripts/",
            b"source_paths",
            b"created_on",
            b"review_id",
            b"selector",
            b'"report_path"',
            b"package_fingerprint",
            b"required-candidate-material-fingerprints",
            b"full-catalog-ranking-fingerprint",
        ):
            self.assertNotIn(forbidden, encoded)

    def test_legacy_source_manifest_is_diagnostic_only(self) -> None:
        manifest = PANEL._professional_evidence_review_contract_manifest()
        self.assertEqual(
            "professional-evidence-review-and-carry-v3",
            manifest["contract_version"],
        )
        self.assertRegex(manifest["aggregate_source_digest"], r"^[0-9a-f]{64}$")
        self.assertEqual(
            [
                "scripts/audit-skill-content.py",
                "scripts/expert_panel_attestation.py",
                "scripts/expert_panel_review.py",
                "scripts/professional_completeness_carry_forward.py",
                "scripts/validation_utils.py",
            ],
            [row["path"] for row in manifest["source_manifest"]],
        )
        payload = {
            key: value
            for key, value in manifest.items()
            if key != "aggregate_source_digest"
        }
        self.assertEqual(
            CARRY.canonical_json_sha256(payload),
            manifest["aggregate_source_digest"],
        )
        self.assertNotEqual(
            manifest["aggregate_source_digest"],
            PANEL._professional_evidence_review_contract_fingerprint(),
        )

    def test_non_contract_source_bytes_do_not_change_semantic_digest(self) -> None:
        semantic_before = (
            CONTRACTS.professional_review_contract_fingerprint()
        )
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "source.py"
            source.write_text("VALUE = 1\n", encoding="utf-8")
            first = CARRY.versioned_explicit_source_manifest(
                contract_version="fixture-v1",
                source_paths=("source.py",),
                repository_root=root,
            )
            source.write_text("VALUE = 2\n", encoding="utf-8")
            source_changed = CARRY.versioned_explicit_source_manifest(
                contract_version="fixture-v1",
                source_paths=("source.py",),
                repository_root=root,
            )
        semantic_after = CONTRACTS.professional_review_contract_fingerprint()
        self.assertNotEqual(
            first["aggregate_source_digest"],
            source_changed["aggregate_source_digest"],
        )
        self.assertEqual(semantic_before, semantic_after)

    def test_contract_version_and_semantic_projection_change_digest(self) -> None:
        projection = CONTRACTS.professional_schema3_contract_projection()
        original = CONTRACTS.professional_review_contract_fingerprint(
            projection
        )
        changed_version = copy.deepcopy(projection)
        changed_version["contract_version"] = "fixture-v2"
        changed_rule = copy.deepcopy(projection)
        changed_rule["panel"]["minimum_winning_votes"] = 3

        self.assertNotEqual(
            original,
            CONTRACTS.professional_review_contract_fingerprint(
                changed_version
            ),
        )
        self.assertNotEqual(
            original,
            CONTRACTS.professional_review_contract_fingerprint(changed_rule),
        )


class ProfessionalPacketCompatibilityTests(unittest.TestCase):
    def test_schema1_inventory_count_is_a_strict_closed_integer_set(self) -> None:
        historical = _historical_schema1_packet()
        current = copy.deepcopy(_legacy_schema1_packet())
        PANEL._validate_professional_completeness_packet_v1(historical)
        PANEL._validate_professional_completeness_packet_v1(current)
        self.assertEqual(
            {"professional": 22, "foundation": 133, "domain": 7},
            PANEL.PROFESSIONAL_LEGACY_LAYER_COUNTS,
        )
        self.assertEqual(
            {"professional": 25, "foundation": 150, "domain": 13},
            PANEL.PROFESSIONAL_CURRENT_LAYER_COUNTS,
        )
        self.assertTrue(
            all(
                type(value) is int
                for counts in (
                    PANEL.PROFESSIONAL_LEGACY_LAYER_COUNTS,
                    PANEL.PROFESSIONAL_CURRENT_LAYER_COUNTS,
                )
                for value in counts.values()
            )
        )
        invalid_layer_cases = (
            (
                historical,
                "PROFESSIONAL_LEGACY_LAYER_COUNTS",
                "professional",
                22.0,
            ),
            (
                historical,
                "PROFESSIONAL_LEGACY_LAYER_COUNTS",
                "domain",
                True,
            ),
            (
                current,
                "PROFESSIONAL_CURRENT_LAYER_COUNTS",
                "professional",
                24.0,
            ),
            (
                current,
                "PROFESSIONAL_CURRENT_LAYER_COUNTS",
                "domain",
                False,
            ),
        )
        for source, constant_name, layer, invalid_count in invalid_layer_cases:
            with self.subTest(
                constant_name=constant_name,
                layer=layer,
                invalid_count=invalid_count,
            ):
                expected_counts = copy.deepcopy(
                    getattr(PANEL, constant_name)
                )
                expected_counts[layer] = invalid_count
                with mock.patch.object(
                    PANEL,
                    constant_name,
                    expected_counts,
                ), self.assertRaisesRegex(
                    PANEL.PanelReviewError,
                    "target layers",
                ):
                    PANEL._validate_professional_completeness_packet_v1(
                        copy.deepcopy(source)
                    )

        invalid_cases = (
            (current, 187),
            (current, 189),
            (historical, 162.0),
            (current, 188.0),
            (current, True),
            (current, False),
            (current, "188"),
            (current, None),
        )
        for source, required_target_count in invalid_cases:
            with self.subTest(required_target_count=required_target_count):
                packet = copy.deepcopy(source)
                packet["panel_contract"][
                    "required_target_count"
                ] = required_target_count
                with self.assertRaisesRegex(
                    PANEL.PanelReviewError,
                    "panel_contract is invalid",
                ):
                    PANEL._validate_professional_completeness_packet_v1(
                        packet
                    )

    def test_schema2_packet_shape_and_canonical_bytes_remain_unchanged(self) -> None:
        packet = copy.deepcopy(_live_packet())
        before = CARRY.canonical_json_bytes(packet)
        bindings = PANEL._professional_review_bindings(
            packet["professional_targets"]
        )
        after = CARRY.canonical_json_bytes(packet)
        self.assertEqual(188, len(bindings))
        self.assertEqual(before, after)
        self.assertEqual(
            after,
            CARRY.canonical_json_bytes(json.loads(after)),
        )
        self.assertEqual(
            {
                "created_on",
                "kind",
                "limitations",
                "panel_contract",
                "professional_targets",
                "review_id",
                "rubric",
                "schema_version",
                "source_fingerprints",
            },
            set(packet),
        )
        self.assertEqual(
            {
                "indexed_references",
                "layer",
                "package_fingerprint",
                "registry",
                "required_expertise_tags",
                "root",
                "routing_adjacency",
                "skill_id",
            },
            set(packet["professional_targets"][0]),
        )

    def test_schema2_unregistered_selector_is_rejected_in_every_mode(self) -> None:
        packet = copy.deepcopy(_live_packet())
        selector = packet["panel_contract"]["adjacency_contract"][
            "required_candidate_selection"
        ]
        selector["version"] = "unregistered-selection-mutation"
        for target in packet["professional_targets"]:
            target["routing_adjacency"]["required_candidate_selection"] = (
                copy.deepcopy(selector)
            )
            without_fingerprint = copy.deepcopy(target)
            without_fingerprint.pop("package_fingerprint")
            target["package_fingerprint"] = _sha(without_fingerprint)
        packet["source_fingerprints"]["professional_packages"] = _sha(
            packet["professional_targets"]
        )

        for validation_mode in (
            PANEL.VALIDATION_MODE_CURRENT,
            PANEL.VALIDATION_MODE_HISTORICAL,
        ):
            with self.subTest(validation_mode=validation_mode), self.assertRaisesRegex(
                PANEL.PanelReviewError,
                "panel_contract",
            ):
                PANEL._validate_professional_completeness_packet_v2(
                    packet,
                    validation_mode=validation_mode,
                )

    def test_historical_cap50_adapter_is_exact_and_hash_preserving(self) -> None:
        decision, packet_ref, packet = _historical_schema3_adapter_fixture(
            cap50=True
        )
        adapted = PANEL._professional_v3_historical_cap50_packet(
            decision,
            packet_ref,
            packet,
        )
        self.assertEqual(_sha(packet), _sha(adapted))
        self.assertEqual(
            PANEL._professional_v3_panel_contract(
                target_count=162,
                include_selection_derivation=False,
            ),
            adapted["panel_contract"],
        )

        mutations = (
            (
                "packet-sha",
                lambda record, packet_ref, value: packet_ref.update(
                    {"sha256": "0" * 64}
                ),
            ),
            (
                "review-id",
                lambda record, packet_ref, value: record.update(
                    {"review_id": "professional-completeness-panel-other"}
                ),
            ),
            (
                "review-contract",
                lambda record, packet_ref, value: record.update(
                    {"review_contract_fingerprint": "0" * 64}
                ),
            ),
            (
                "target-count",
                lambda record, packet_ref, value: value[
                    "professional_targets"
                ].pop(),
            ),
            (
                "panel-cap",
                lambda record, packet_ref, value: value["panel_contract"][
                    "adjacency_contract"
                ]["required_candidate_selection"].update(
                    {"maximum_required_candidates_per_target": 49}
                ),
            ),
            (
                "target-cap",
                lambda record, packet_ref, value: value[
                    "professional_targets"
                ][0]["routing_adjacency"][
                    "required_candidate_selection"
                ].update({"maximum_required_candidates_per_target": 49}),
            ),
        )
        for label, mutate in mutations:
            record_value = copy.deepcopy(decision)
            mutated_packet_ref = copy.deepcopy(packet_ref)
            packet_value = copy.deepcopy(packet)
            mutate(record_value, mutated_packet_ref, packet_value)
            with self.subTest(label=label), self.assertRaises(
                PANEL.PanelReviewError
            ):
                PANEL._professional_v3_historical_cap50_packet(
                    record_value,
                    mutated_packet_ref,
                    packet_value,
                )
        with mock.patch.object(
            PANEL,
            "PROFESSIONAL_ADJACENCY_MAX_REQUIRED_CANDIDATES_PER_TARGET",
            53,
        ), self.assertRaises(PANEL.PanelReviewError):
            PANEL._professional_v3_historical_cap50_packet(
                decision,
                packet_ref,
                packet,
            )

    def test_historical_r14_v1_adapter_is_exact_and_hash_preserving(self) -> None:
        decision, packet_ref, packet = _historical_schema3_adapter_fixture(
            cap50=False
        )
        adapted = PANEL._professional_v3_historical_v1_packet(
            decision,
            packet_ref,
            packet,
        )
        self.assertEqual(_sha(packet), _sha(adapted))
        self.assertEqual(
            PANEL._professional_v3_panel_contract(target_count=188),
            adapted["panel_contract"],
        )
        self.assertEqual(
            "declared_skills",
            next(
                key
                for key in adapted["professional_targets"][0][
                    "routing_adjacency"
                ]
                if key == "declared_skills"
            ),
        )

        mutations = (
            (
                "packet-sha",
                lambda record, packet_ref, value: packet_ref.update(
                    {"sha256": "0" * 64}
                ),
            ),
            (
                "review-id",
                lambda record, packet_ref, value: record.update(
                    {"review_id": "professional-completeness-panel-other"}
                ),
            ),
            (
                "review-contract",
                lambda record, packet_ref, value: record.update(
                    {"review_contract_fingerprint": "0" * 64}
                ),
            ),
            (
                "target-count",
                lambda record, packet_ref, value: value[
                    "professional_targets"
                ].pop(),
            ),
            (
                "selector-version",
                lambda record, packet_ref, value: value["panel_contract"][
                    "adjacency_contract"
                ]["required_candidate_selection"].update(
                    {"version": "layered-required-candidates-other"}
                ),
            ),
        )
        for label, mutate in mutations:
            record_value = copy.deepcopy(decision)
            mutated_packet_ref = copy.deepcopy(packet_ref)
            packet_value = copy.deepcopy(packet)
            mutate(record_value, mutated_packet_ref, packet_value)
            with self.subTest(label=label), self.assertRaises(
                PANEL.PanelReviewError
            ):
                PANEL._professional_v3_historical_v1_packet(
                    record_value,
                    mutated_packet_ref,
                    packet_value,
                )

    def test_historical_schema3_decision_remains_auditable_for_carry(self) -> None:
        with professional_support._synthetic_schema3_professional_decision() as fixture:
            decision = fixture["decision"]
            validation_root = fixture["validation_root"]
            with mock.patch.object(
                PANEL,
                "_professional_evidence_review_contract_fingerprint",
                return_value="0" * 64,
            ), mock.patch.object(
                PANEL, "PROFESSIONAL_ADJACENCY_TOP_K", 0
            ), mock.patch.object(
                PANEL, "PROFESSIONAL_ADJACENCY_PER_SIGNAL_TOP_K", 0
            ):
                self.assertEqual(
                    decision,
                    PANEL.validate_decision_record(
                        decision,
                        record_path=fixture["decision_path"],
                        validation_root=validation_root,
                        validation_mode="historical",
                    ),
                )

            dependencies = CARRY.professional_prior_decision_dependencies(
                prior_packet=fixture["packet"],
                prior_ballots=[ballot for _path, ballot in fixture["ballots"]],
                prior_decision=decision,
            )
            self.assertEqual(PANEL.PROFESSIONAL_PACKAGE_COUNT, len(dependencies))
            self.assertTrue(
                all(row["evidence_complete"] for row in dependencies.values())
            )

    def test_schema1_legacy_packet_bytes_and_validator_remain_compatible(self) -> None:
        packet = copy.deepcopy(_legacy_schema1_packet())
        before = CARRY.canonical_json_bytes(packet)
        PANEL._validate_professional_completeness_packet(packet)
        template = PANEL.prepare_professional_completeness_ballot_template(
            packet=packet,
            packet_sha256="b" * 64,
            voter_id="legacy-reviewer",
            agent_id="legacy-agent",
            role="legacy-professional-reviewer",
            expertise=["legacy completeness"],
            expertise_tags=None,
            skill_ids=None,
            created_on="2026-07-17",
        )
        PANEL.validate_ballot_template(
            packet,
            template,
            packet_sha256="b" * 64,
        )
        self.assertEqual(before, CARRY.canonical_json_bytes(packet))
        self.assertEqual(
            before,
            CARRY.canonical_json_bytes(json.loads(before)),
        )


if __name__ == "__main__":
    unittest.main()
