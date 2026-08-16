from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import argparse
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from . import expert_panel_source_test_support as source_support


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import expert_panel_attestation as ATTESTATION

PANEL = source_support.PANEL


SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
CRITERIA = (
    "adjacent-overlap-or-gap",
    "boundary-conditions",
    "erroneous-rules",
    "failure-modes",
    "generic-knowledge-pollution",
    "material-omissions",
    "output-verifiability",
    "professional-correctness",
    "reference-high-risk-coverage",
    "verification-methods",
)
CRITICAL_CRITERIA = {
    "boundary-conditions",
    "erroneous-rules",
    "failure-modes",
    "material-omissions",
    "professional-correctness",
    "verification-methods",
}
ORDINARY_CRITERIA = set(CRITERIA) - CRITICAL_CRITERIA
FORMAL_ROUND_POLICY = {
    "schema_version": 1,
    "full_fresh_source_material_coverage_ratio_ppm": 1_000_000,
    "maximum_reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm": 50_000,
    "maximum_reviewer_added_unique_union_to_required_ratio_ppm": 1_000_000,
}


def _sha(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


FORMAL_ROUND_POLICY_FINGERPRINT = _sha(FORMAL_ROUND_POLICY)


def _basic_reviewers() -> list[dict]:
    return [
        {
            "voter_id": f"reviewer-{index}",
            "agent_id": f"agent-{index}",
            "role": f"senior-role-{index}",
            "expertise": ["content-review"],
            "independent_review": True,
        }
        for index in range(1, 4)
    ]


def _qualification(tag: str) -> dict:
    return {
        "expertise_tag": tag,
        "qualification_basis": (
            "Current fixture qualification evidence is explicitly declared."
        ),
        "proof_limit": "Static declarations do not prove reviewer identity.",
    }


def _professional_reviewers() -> list[dict]:
    # Duplicate roles are intentional: Professional requires unique voter and
    # agent identities, not artificial role-string uniqueness.
    return [
        {
            "voter_id": "architecture-reviewer",
            "agent_id": "agent-architecture",
            "role": "senior-reviewer",
            "expertise": ["reference architecture"],
            "expertise_tags": ["skill-reference-architecture"],
            "qualification_claims": [
                _qualification("skill-reference-architecture")
            ],
            "independent_review": True,
        },
        {
            "voter_id": "domain-reviewer-one",
            "agent_id": "agent-domain-one",
            "role": "senior-reviewer",
            "expertise": ["repository tooling"],
            "expertise_tags": ["repository-tooling"],
            "qualification_claims": [_qualification("repository-tooling")],
            "independent_review": True,
        },
        {
            "voter_id": "domain-reviewer-two",
            "agent_id": "agent-domain-two",
            "role": "senior-reviewer",
            "expertise": ["repository tooling"],
            "expertise_tags": ["repository-tooling"],
            "qualification_claims": [_qualification("repository-tooling")],
            "independent_review": True,
        },
    ]


def _common(*, axis: str, kind: str, fingerprints: dict, reviewers: list) -> dict:
    return {
        "schema_version": ATTESTATION.ATTESTATION_SCHEMA_VERSION,
        "kind": kind,
        "axis": axis,
        "review_id": f"{axis}-review-2026-08-10-r1",
        "decided_on": "2026-08-10",
        "source_fingerprints": fingerprints,
        "review_contract_fingerprint": SHA_A,
        "reviewers": reviewers,
        "findings": [],
        "summary": {},
        "verdict": "",
        "rationale": ["Static evidence is bounded to current declared sources."],
    }


def _simple_vote(voter_id: str, disposition: str, reason_code: str) -> dict:
    return {
        "voter_id": voter_id,
        "disposition": disposition,
        "reason_code": reason_code,
        "rationale": "This reviewer independently supports the bounded disposition.",
    }


def readability_fixture() -> dict:
    value, bindings = _compact_readability_value()
    return ATTESTATION.finalize_attestation(
        value, expected_readability_current_bindings=bindings
    )


def _compact_readability_targets() -> dict[str, dict]:
    sentence = "One bounded sentence provides current readability evidence."
    sentence_fingerprint = hashlib.sha256(
        ("ai-readability-sentence-v1\0" + sentence).encode("utf-8")
    ).hexdigest()
    return {
        "content": {
            "path": "src/foundation/example/SKILL.md",
            "classification": "REVIEW_DENSITY",
            "content_fingerprint": _sha("content-source"),
            "document_context": {"text": "Regenerable source context."},
        },
        "readability": {
            "document_id": "document-one",
            "path": "src/foundation/example/SKILL.md",
            "highest_band": "review-as-complex",
            "content_fingerprint": _sha("readability-source"),
            "findings": [
                {
                    "finding_id": _sha("finding-one"),
                    "sentence": sentence,
                    "sentence_fingerprint": sentence_fingerprint,
                    "source_span": {"start_offset": 0, "end_offset": len(sentence)},
                }
            ],
        },
        "actionability": {
            "target_id": "action-one",
            "skill_id": "example",
            "path": "src/foundation/example/SKILL.md",
            "front_loaded_action_score": 1,
            "content_fingerprint": _sha("actionability-source"),
            "front_window": {
                "start_line": 1,
                "end_line": 1,
                "line_count": 1,
                "lines": [{"line": 1, "text": "Define one bounded action."}],
                "sha256": hashlib.sha256(
                    b"Define one bounded action."
                ).hexdigest(),
            },
        },
    }


def _compact_readability_bindings() -> dict[str, dict[str, dict]]:
    targets = _compact_readability_targets()
    return {
        category: {
            ATTESTATION.readability_target_authority(
                category=category, target=target
            )["target_id"]: ATTESTATION.readability_target_authority(
                category=category, target=target
            )
        }
        for category, target in targets.items()
    }


def _compact_readability_value() -> tuple[dict, dict[str, dict[str, dict]]]:
    reviewers = _basic_reviewers()
    voter_ids = [row["voter_id"] for row in reviewers]
    bindings = _compact_readability_bindings()
    value = _common(
        axis=ATTESTATION.READABILITY_AXIS,
        kind=ATTESTATION.READABILITY_ATTESTATION_KIND,
        fingerprints={
            "readability_target_manifest": (
                ATTESTATION.readability_target_manifest_fingerprint(bindings)
            ),
            "readability_detector_contract": SHA_B,
            "actionability_detector_contract": SHA_C,
        },
        reviewers=reviewers,
    )
    value["review_artifacts"] = {
        "decision": {"sha256": _sha("readability-decision")},
        "packet": {"sha256": _sha("readability-packet")},
        "ballots": [
            {
                "voter_id": voter_id,
                "sha256": _sha(f"readability-ballot-{voter_id}"),
            }
            for voter_id in voter_ids
        ],
    }
    content = bindings["content"]["src/foundation/example/SKILL.md"]
    document = bindings["readability"]["document-one"]
    action = bindings["actionability"]["action-one"]
    nested = document["findings"][_sha("finding-one")]
    value["findings"] = [
        {
            "category": "content",
            "target_id": content["target_id"],
            "source_fingerprint": content["source_fingerprint"],
            "review_binding_fingerprint": content[
                "review_binding_fingerprint"
            ],
            "votes": [
                _simple_vote(
                    voter_id,
                    "accepted-current-density",
                    "bounded-density-preserves-professional-coverage",
                )
                for voter_id in voter_ids
            ],
            "result": {},
        },
        {
            "category": "readability",
            "target_id": document["target_id"],
            "source_fingerprint": document["source_fingerprint"],
            "review_binding_fingerprint": document[
                "review_binding_fingerprint"
            ],
            "finding_reviews": [
                {
                    "finding_id": nested["finding_id"],
                    "source_fingerprint": nested["source_fingerprint"],
                    "review_binding_fingerprint": nested[
                        "review_binding_fingerprint"
                    ],
                    "votes": [
                        _simple_vote(
                            voter_id,
                            "accepted-current-readability",
                            "bounded-enumeration-improves-precision",
                        )
                        for voter_id in voter_ids
                    ],
                    "result": {},
                }
            ],
            "result": {},
        },
        {
            "category": "actionability",
            "target_id": action["target_id"],
            "source_fingerprint": action["source_fingerprint"],
            "review_binding_fingerprint": action[
                "review_binding_fingerprint"
            ],
            "votes": [
                _simple_vote(
                    voter_id,
                    "accepted-current-actionability",
                    "explicit-domain-actions-are-front-loaded",
                )
                for voter_id in voter_ids
            ],
            "result": {},
        },
    ]
    return value, bindings


def _readability_decision_adapter_fixture() -> tuple[dict, dict]:
    path = "src/foundation/example/SKILL.md"
    document_id = f"{path}#body"
    first_sentence = "First bounded sentence provides current readability evidence."

    def span(text: str, sentence: str, start_offset: int) -> dict:
        end_offset = start_offset + len(sentence)
        return {
            "start_offset": start_offset,
            "end_offset": end_offset,
            "start_line": 1,
            "end_line": 1,
            "start_column": start_offset + 1,
            "end_column": end_offset + 1,
            "lines": [{"line": 1, "text": text}],
            "sha256": hashlib.sha256(sentence.encode("utf-8")).hexdigest(),
        }

    selected: tuple[str, str, list[dict]] | None = None
    for candidate in range(1024):
        second_sentence = (
            "Second bounded readability evidence uses deterministic candidate "
            f"{candidate}."
        )
        text = first_sentence + " " * (100 - len(first_sentence)) + second_sentence
        raw_findings = []
        for sentence, start_offset in ((first_sentence, 0), (second_sentence, 100)):
            sentence_fingerprint = hashlib.sha256(
                ("ai-readability-sentence-v1\0" + sentence).encode("utf-8")
            ).hexdigest()
            source_span = span(text, sentence, start_offset)
            finding_id = PANEL._readability_finding_id(
                document_id=document_id,
                kind="compound-sentence",
                band="review-as-complex",
                words=len(sentence.split()),
                sentence_fingerprint=sentence_fingerprint,
                source_span=source_span,
            )
            raw_findings.append(
                {
                    "finding_id": finding_id,
                    "line": 1,
                    "band": "review-as-complex",
                    "words": len(sentence.split()),
                    "kind": "compound-sentence",
                    "sentence": sentence,
                    "sentence_fingerprint": sentence_fingerprint,
                    "source_span": source_span,
                }
            )
        if raw_findings[0]["finding_id"] > raw_findings[1]["finding_id"]:
            selected = text, second_sentence, raw_findings
            break
    if selected is None:
        raise AssertionError("fixture search did not invert finding ID order")
    text, _second_sentence, findings = selected
    context = {
        "line_count": 1,
        "text": text,
        "lines": [{"line": 1, "text": text}],
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }
    content_target = {
        "path": path,
        "classification": "REVIEW_DENSITY",
        "review_state": "REVIEW_CONTEXT",
        "review_reasons": ["classification_review_density"],
        "document_id": document_id,
        "owner": "example",
        "document_part": "body",
        "source_selector": {"kind": "yaml-body", "path": path},
        "content_fingerprint": context["sha256"],
        "document_context": copy.deepcopy(context),
    }
    readability_target = {
        "document_id": document_id,
        "path": path,
        "surface": "root-skill-body",
        "document_part": "body",
        "owner": "example",
        "source_selector": {"kind": "yaml-body", "path": path},
        "content_fingerprint": context["sha256"],
        "document_context": copy.deepcopy(context),
        "highest_band": "review-as-complex",
        "findings": findings,
    }
    packet = {
        "schema_version": PANEL.READABILITY_SCHEMA_VERSION,
        "kind": PANEL.PACKET_KIND,
        "review_id": "compact-readability",
        "created_on": "2026-08-10",
        "source_fingerprints": {
            "readability_target_manifest": SHA_A,
            "readability_detector_contract": SHA_B,
            "actionability_detector_contract": SHA_C,
        },
        "panel_contract": {
            "decision_method": PANEL.DECISION_METHOD,
            "required_voters": PANEL.PANEL_SIZE,
            "abstentions_allowed": False,
            "minimum_winning_votes": 2,
            "independent_ballots": True,
            "required_actionability_target_count": 0,
            "actionability_score_threshold": 60,
            "actionability_front_window_lines": 60,
            "allowed_actionability_dispositions": sorted(
                PANEL.ACTIONABILITY_DECISIONS
            ),
            "readability_document_decision_method": (
                "finding-grounded-document-majority-v1"
            ),
            "readability_reviewer_derivation": "any-nested-tightening",
            "content_source_binding_contract": (
                PANEL.CONTENT_SOURCE_BINDING_CONTRACT
            ),
            "readability_currentness_contract": (
                PANEL.panel_contracts.readability_currentness_contract_projection()
            ),
        },
        "rubric": {
            "accept": "Accept the current bounded readability evidence.",
            "tighten": "Tighten evidence that contains independent instructions.",
            "reason_codes": {
                decision: sorted(reason_codes)
                for decision, reason_codes in sorted(
                    PANEL.READABILITY_V2_REASON_CODES.items()
                )
            },
        },
        "content_targets": [content_target],
        "readability_targets": [readability_target],
        "actionability_targets": [],
        "limitations": ["Static fixture evidence is not production behavior."],
    }
    packet["source_fingerprints"]["readability_target_manifest"] = (
        ATTESTATION.readability_target_manifest_fingerprint(
            PANEL._readability_target_authorities(packet)
        )
    )
    return packet, {
        "expected_finding_ids": sorted(
            finding["finding_id"] for finding in findings
        ),
        "source_order_finding_ids": [
            finding["finding_id"] for finding in findings
        ],
        "source_offsets": [
            finding["source_span"]["start_offset"] for finding in findings
        ],
    }


def _semantic_candidates() -> dict[str, dict]:
    root_candidate = ATTESTATION.semantic_candidate_review_evidence(
        axis="root",
        candidate={
        "candidate_id": _sha("root-candidate-one"),
        "finding": "One contextual semantic rule requires disposition.",
        "path": "src/foundation/example/SKILL.md",
        "owner": "example",
        "skill_owner": "example",
        "fingerprint": _sha("root-candidate-finding"),
        "document_part": "body",
        "occurrence_fingerprint": _sha("root-occurrence"),
        "context_fingerprint": _sha("root-context"),
        "priority": "P1",
        "occurrences": [
            {
                "path": "src/foundation/example/SKILL.md",
                "lines": {"start": 1, "end": 1},
                "preview": "One contextual semantic rule requires disposition.",
                "context_fingerprint": _sha("root-context"),
            }
        ],
        "governance_status": "pending",
        "resolved": False,
        },
    )
    reference_candidate = ATTESTATION.semantic_candidate_review_evidence(
        axis="reference",
        candidate={
            "candidate_id": _sha("reference-candidate-one"),
            "finding": "One repeated Reference rule requires disposition.",
            "path": "group",
            "owner": "shared-reference",
            "skill_owner": "example",
            "fingerprint": _sha("reference-candidate-finding"),
            "evidence_fingerprint": _sha("reference-evidence"),
            "content_fingerprint": _sha("reference-content"),
            "priority": "P2",
            "occurrences": [
                {
                    "path": "src/professional/example/references/one.md",
                    "owner": "example",
                    "lines": {"start": 1, "end": 1},
                    "preview": "One repeated Reference rule.",
                },
                {
                    "path": "src/professional/other/references/two.md",
                    "owner": "other",
                    "lines": {"start": 2, "end": 2},
                    "preview": "One repeated Reference rule.",
                },
            ],
            "disposition": "rewrite",
            "unresolved": True,
        },
    )
    return {"reference": reference_candidate, "root": root_candidate}


def _semantic_expected_bindings(
    candidates: dict[str, dict] | None = None,
) -> dict[str, dict]:
    candidates = _semantic_candidates() if candidates is None else candidates
    return {
        f"{axis}:{candidate['candidate_id']}": (
            ATTESTATION.semantic_candidate_authority(
                axis=axis, candidate=candidate
            )
        )
        for axis, candidate in candidates.items()
    }


def semantic_fixture() -> dict:
    reviewers = _basic_reviewers()
    value = _common(
        axis=ATTESTATION.SEMANTIC_DISPOSITION_AXIS,
        kind=ATTESTATION.SEMANTIC_DISPOSITION_ATTESTATION_KIND,
        fingerprints={key: _sha(key) for key in (
            "reference_candidate_manifest",
            "reference_detector_contract",
            "root_candidate_manifest",
            "root_detector_contract",
        )},
        reviewers=reviewers,
    )
    candidates = _semantic_candidates()
    expected_bindings = _semantic_expected_bindings(candidates)
    votes = [
        {
            "voter_id": reviewer["voter_id"],
            "disposition": "valid-contextual-rule",
            "rationale": "The rule is valid within this declared context.",
            "authority_or_condition": "The source owner retains authority.",
            "decision_owner": "source-owner",
            "mitigation": "Retain the bounded contextual explanation.",
            "review_after": None,
        }
        for reviewer in reviewers
    ]
    value["findings"] = [
        {
            "target_id": f"reference:{candidates['reference']['candidate_id']}",
            "axis": "reference",
            "candidate_binding_fingerprint": expected_bindings[
                f"reference:{candidates['reference']['candidate_id']}"
            ]["candidate_binding_fingerprint"],
            "votes": copy.deepcopy(votes),
            "result": {},
        },
        {
            "target_id": f"root:{candidates['root']['candidate_id']}",
            "axis": "root",
            "candidate_binding_fingerprint": expected_bindings[
                f"root:{candidates['root']['candidate_id']}"
            ]["candidate_binding_fingerprint"],
            "votes": copy.deepcopy(votes),
            "result": {},
        },
    ]
    return ATTESTATION.finalize_attestation(
        value,
        expected_semantic_current_bindings=expected_bindings,
    )


def _anchor(
    *, anchor_id: str, skill_id: str, path: str, excerpt: str
) -> dict:
    return {
        "anchor_id": anchor_id,
        "skill_id": skill_id,
        "path": path,
        "start_line": 1,
        "end_line": 1,
        "excerpt": excerpt,
        "excerpt_sha256": hashlib.sha256(excerpt.encode("utf-8")).hexdigest(),
    }


def _assertion_sha(anchors: list[dict], anchor_ids: list[str]) -> str:
    by_id = {row["anchor_id"]: row for row in anchors}
    projection = [
        {
            "anchor_id": anchor_id,
            "skill_id": by_id[anchor_id]["skill_id"],
            "path": by_id[anchor_id]["path"],
            "start_line": by_id[anchor_id]["start_line"],
            "end_line": by_id[anchor_id]["end_line"],
            "excerpt": by_id[anchor_id]["excerpt"],
        }
        for anchor_id in anchor_ids
    ]
    return _sha(projection)


def _professional_vote(skill_id: str, reviewer: dict) -> dict:
    own_one = f"{skill_id}-a"
    own_two = f"{skill_id}-b"
    adjacent = f"{skill_id}-c"
    anchors = [
        _anchor(
            anchor_id=own_one,
            skill_id=skill_id,
            path=f"src/foundation/{skill_id}/SKILL.md",
            excerpt="Bounded tooling evidence supports this current decision.",
        ),
        _anchor(
            anchor_id=own_two,
            skill_id=skill_id,
            path=f"src/foundation/{skill_id}/SKILL.md",
            excerpt="Failure recovery evidence remains explicit and verifiable.",
        ),
        _anchor(
            anchor_id=adjacent,
            skill_id="adjacent-skill",
            path="src/foundation/adjacent-skill/SKILL.md",
            excerpt="Adjacent responsibility stays outside the selected boundary.",
        ),
    ]
    criteria = {}
    for index, criterion in enumerate(CRITERIA):
        anchor_ids = [own_one if index % 2 == 0 else own_two]
        criteria[criterion] = {
            "status": "satisfied",
            "evidence_assertions": [
                {
                    "claim": f"Current {criterion} evidence is explicit and bounded.",
                    "evidence_anchor_ids": anchor_ids,
                    "source_excerpt_sha256": _assertion_sha(anchors, anchor_ids),
                }
            ],
        }
    return {
        "reviewer": copy.deepcopy(reviewer),
        "decision": "accepted-current-professional-completeness",
        "reason_code": "all-professional-criteria-satisfied",
        "evidence_anchors": anchors,
        "criteria": criteria,
        "examined_failure_modes": [
            {
                "failure_mode": "A stale binding could authorize invalid evidence.",
                "outcome": "not-applicable",
                "evidence_anchor_ids": [own_one],
                "rationale": "The current binding rejects stale evidence before use.",
            }
        ],
        "examined_omission_candidates": [
            {
                "omission_candidate": "Recovery proof could be omitted from the contract.",
                "outcome": "not-applicable",
                "evidence_anchor_ids": [own_two],
                "rationale": "Recovery evidence is explicit in the bounded source.",
            }
        ],
        "examined_adjacent_candidates": [
            {
                "skill_id": "adjacent-skill",
                "review_origin": "packet-required",
                "discovery_reason": None,
                "disposition": "not-adjacent",
                "target_anchor_ids": [own_one],
                "candidate_anchor_ids": [adjacent],
                "rationale": "Target and adjacent evidence prove separate responsibilities.",
            }
        ],
        "proof_limits": [
            "Static evidence does not prove production reviewer behavior."
        ],
        "rationale": "All complete evidence classes support the accepted disposition.",
    }


def _origin(skill_id: str, *, review_id: str) -> dict:
    return {
        "review_id": review_id,
        "decided_on": (
            "2026-08-10" if "2026-08-10" in review_id else "2026-08-09"
        ),
        "origin_depth": 0,
        "review_contract_fingerprint": SHA_A,
        "package_fingerprint": SHA_B,
        "review_binding_fingerprint": SHA_C,
        "required_expertise_tags": ["repository-tooling"],
        "required_candidate_ids": ["adjacent-skill"],
        "dependency_material_fingerprints": {"adjacent-skill": SHA_A},
        "votes": [
            _professional_vote(skill_id, reviewer)
            for reviewer in _professional_reviewers()
        ],
        "origin_fingerprint": "",
    }


def _professional_finding(skill_id: str, *, mode: str) -> dict:
    current_review_id = "professional-completeness-review-2026-08-10-r1"
    origin = _origin(
        skill_id,
        review_id=(
            current_review_id
            if mode == "fresh"
            else "professional-completeness-review-2026-08-09-r0"
        ),
    )
    return {
        "skill_id": skill_id,
        "package_fingerprint": SHA_B,
        "review_binding_fingerprint": SHA_C,
        "required_expertise_tags": ["repository-tooling"],
        "required_candidate_ids": ["adjacent-skill"],
        "dependency_material_fingerprints": {"adjacent-skill": SHA_A},
        "provenance": {"mode": mode, "origin": origin},
        "result": {},
        "rationale": "The normalized origin completely proves this target decision.",
    }


def _compact_professional_vote_fixture(skill_id: str, reviewer: dict) -> dict:
    full = _professional_vote(skill_id, reviewer)
    failure_rows = full["examined_failure_modes"]
    omission_rows = full["examined_omission_candidates"]
    adjacency_rows = full["examined_adjacent_candidates"]
    proof_limits = full["proof_limits"]
    compact = {
        "reviewer": full["reviewer"]["voter_id"],
        "decision": full["decision"],
        "reason_code": full["reason_code"],
        "review_evidence_fingerprint": _sha(full),
        "criteria": {
            "ordinary": {
                criterion: full["criteria"][criterion]["status"]
                for criterion in sorted(ORDINARY_CRITERIA)
            }
            ,
            "domain_critical_defects": (
                []
                if full["reviewer"]["expertise_tags"]
                == ["skill-reference-architecture"]
                else sorted(
                    criterion
                    for criterion in CRITICAL_CRITERIA
                    if full["criteria"][criterion]["status"] == "defect-found"
                )
            ),
        },
        "examined_failure_modes": {
            "count": len(failure_rows),
            "defect_count": sum(
                row["outcome"] == "defect-found" for row in failure_rows
            ),
        },
        "examined_omission_candidates": {
            "count": len(omission_rows),
            "defect_count": sum(
                row["outcome"] == "defect-found" for row in omission_rows
            ),
        },
        "examined_adjacent_candidates": {
            "count": len(adjacency_rows),
            "required_count": sum(
                row["review_origin"] == "packet-required"
                for row in adjacency_rows
            ),
            "reviewer_added_candidate_ids": sorted(
                row["skill_id"]
                for row in adjacency_rows
                if row["review_origin"] == "reviewer-added"
            ),
            "defect_count": sum(
                row["disposition"] == "gap-or-overlap-defect"
                for row in adjacency_rows
            ),
        },
        "proof_limits": {
            "count": len(proof_limits),
            "bounded": copy.deepcopy(proof_limits[:2]),
        },
        "rationale": full["rationale"],
    }
    return compact


def _compact_professional_finding_fixture(
    skill_id: str, *, mode: str, origin_review_id: str
) -> dict:
    return {
        "skill_id": skill_id,
        "package_material_binding": SHA_B,
        "review_unit_binding": SHA_C,
        "dependency_ids": ["adjacent-skill"],
        "required_expertise_tags": ["repository-tooling"],
        "provenance": {
            "mode": mode,
            "origin": {
                "origin_review_id": origin_review_id,
                "origin_commit": "d" * 40,
                "origin_verdict_digest": SHA_C,
            },
        },
        "votes": [
            _compact_professional_vote_fixture(skill_id, reviewer)
            for reviewer in _professional_reviewers()
        ],
        "result": {},
    }


def _compact_professional_authority(skill_id: str) -> dict[str, dict]:
    finding = _compact_professional_finding_fixture(
        skill_id,
        mode="fresh",
        origin_review_id="professional-completeness-review-2026-08-10-r1",
    )
    return {
        skill_id: {
            "package_material_binding": SHA_B,
            "review_unit_binding": SHA_C,
            "required_expertise_tags": ["repository-tooling"],
            "selection_contract_version": "fixture-selection-v1",
            "required_candidate_ids": ["adjacent-skill"],
            "required_candidate_material_bindings": {
                "adjacent-skill": SHA_A
            },
            "reviewer_added_candidate_ids_union": [],
            "reviewer_added_candidate_material_bindings": {},
            "vote_authorities": {
                vote["reviewer"]: copy.deepcopy(vote)
                for vote in finding["votes"]
            },
            "reviewer_partition": {
                "domain_voters": ["domain-reviewer-one", "domain-reviewer-two"],
                "architecture_voter": "architecture-reviewer",
            },
            "evidence_metrics": _professional_evidence_metrics(),
            "origin": copy.deepcopy(finding["provenance"]["origin"]),
        }
    }


def _professional_authority(value: dict) -> dict[str, dict]:
    return {
        row["skill_id"]: {
            "package_material_binding": row["package_material_binding"],
            "review_unit_binding": row["review_unit_binding"],
            "required_expertise_tags": copy.deepcopy(
                row["required_expertise_tags"]
            ),
            "selection_contract_version": "fixture-selection-v1",
            "required_candidate_ids": copy.deepcopy(
                ["adjacent-skill"]
            ),
            "required_candidate_material_bindings": {
                candidate_id: value["dependency_material_catalog"][candidate_id]
                for candidate_id in ["adjacent-skill"]
            },
            "reviewer_added_candidate_ids_union": sorted(
                {
                    candidate_id
                    for vote in row["votes"]
                    for candidate_id in vote[
                        "examined_adjacent_candidates"
                    ]["reviewer_added_candidate_ids"]
                }
            ),
            "reviewer_added_candidate_material_bindings": {
                candidate_id: value["dependency_material_catalog"][candidate_id]
                for candidate_id in sorted(
                    {
                        candidate_id
                        for vote in row["votes"]
                        for candidate_id in vote[
                            "examined_adjacent_candidates"
                        ]["reviewer_added_candidate_ids"]
                    }
                )
            },
            "vote_authorities": {
                vote["reviewer"]: copy.deepcopy(vote)
                for vote in row["votes"]
            },
            "reviewer_partition": {
                "domain_voters": ["domain-reviewer-one", "domain-reviewer-two"],
                "architecture_voter": "architecture-reviewer",
            },
            "evidence_metrics": _professional_evidence_metrics(),
            "origin": copy.deepcopy(row["provenance"]["origin"]),
        }
        for row in value["findings"]
    }


def _professional_claims(value: dict) -> dict[str, dict]:
    return {
        row["skill_id"]: {
            "vote_authorities": {
                vote["reviewer"]: copy.deepcopy(vote)
                for vote in row["votes"]
            },
            "reviewer_partition": {
                "domain_voters": ["domain-reviewer-one", "domain-reviewer-two"],
                "architecture_voter": "architecture-reviewer",
            },
            "evidence_metrics": _professional_evidence_metrics(),
            "reviewer_added_candidate_ids_union": sorted(
                {
                    candidate_id
                    for vote in row["votes"]
                    for candidate_id in vote[
                        "examined_adjacent_candidates"
                    ]["reviewer_added_candidate_ids"]
                }
            ),
            "origin": copy.deepcopy(row["provenance"]["origin"]),
        }
        for row in value["findings"]
    }


def _professional_evidence_metrics() -> dict[str, int]:
    return {
        "target_vote_count": 3,
        "required_adjacency_candidate_count": 1,
        "criterion_result_count": 30,
        "criterion_anchor_binding_count": 30,
        "criterion_assertion_count": 30,
        "evidence_anchor_count": 9,
        "examined_failure_mode_count": 3,
        "examined_omission_candidate_count": 3,
        "examined_adjacency_count": 3,
        "examined_required_adjacency_count": 3,
        "reviewer_added_adjacency_count": 0,
        "proof_limit_count": 3,
        "qualification_claim_count": 3,
    }


def _review_cost_input(mode: str) -> dict:
    if mode == "all-carry":
        return {
            "canonical_capsule_input_bytes_proxy": 0,
            "full_rereview_deduplicated_capsule_input_bytes_proxy": 1_000_200,
            "required_only_capsule_input_bytes_proxy": 0,
            "required_only_source_material_input_bytes_proxy": 0,
            "source_material_input_bytes_proxy": 0,
            "full_rereview_source_material_input_bytes_proxy": 200,
            "reviewer_added_request_count": 0,
            "reviewer_added_unique_relationship_count": 0,
            "maximum_reviewer_added_unique_union_to_required_ratio_ppm": 0,
            "formal_round_policy_fingerprint": FORMAL_ROUND_POLICY_FINGERPRINT,
            "plan_lineage_depth": 1,
            "policy_status": "all-carry-zero-input",
        }
    if mode == "full-fresh":
        return {
            "canonical_capsule_input_bytes_proxy": 1_050_200,
            "full_rereview_deduplicated_capsule_input_bytes_proxy": 1_000_200,
            "required_only_capsule_input_bytes_proxy": 1_000_200,
            "required_only_source_material_input_bytes_proxy": 200,
            "source_material_input_bytes_proxy": 200,
            "full_rereview_source_material_input_bytes_proxy": 200,
            "reviewer_added_request_count": 3,
            "reviewer_added_unique_relationship_count": 1,
            "maximum_reviewer_added_unique_union_to_required_ratio_ppm": 500_000,
            "formal_round_policy_fingerprint": FORMAL_ROUND_POLICY_FINGERPRINT,
            "plan_lineage_depth": 0,
            "policy_status": "bootstrap-full-review",
        }
    if mode != "incremental":
        raise AssertionError(f"unknown review-cost fixture mode: {mode}")
    return {
        "canonical_capsule_input_bytes_proxy": 1_050_200,
        "full_rereview_deduplicated_capsule_input_bytes_proxy": 2_000_400,
        "required_only_capsule_input_bytes_proxy": 1_000_200,
        "required_only_source_material_input_bytes_proxy": 200,
        "source_material_input_bytes_proxy": 200,
        "full_rereview_source_material_input_bytes_proxy": 400,
        "reviewer_added_request_count": 3,
        "reviewer_added_unique_relationship_count": 1,
        "maximum_reviewer_added_unique_union_to_required_ratio_ppm": 1_000_000,
        "formal_round_policy_fingerprint": FORMAL_ROUND_POLICY_FINGERPRINT,
        "plan_lineage_depth": 8,
        "policy_status": "incremental-reduced-input",
    }


class ProfessionalClosedFieldMigrationContractTests(unittest.TestCase):
    def test_current_professional_compact_shape_has_one_authority_vocabulary(
        self,
    ) -> None:
        value = professional_fixture(review_mode="full-fresh")
        expected_top = {
            "schema_version",
            "kind",
            "axis",
            "review_id",
            "decided_on",
            "review_contract_fingerprint",
            "reviewers",
            "dependency_material_catalog",
            "findings",
            "review_cost_input",
            "summary",
            "verdict",
            "rationale",
        }
        expected_finding = {
            "skill_id",
            "package_material_binding",
            "review_unit_binding",
            "dependency_ids",
            "required_expertise_tags",
            "votes",
            "result",
            "provenance",
        }

        self.assertEqual(expected_top, set(value))
        self.assertTrue(value["dependency_material_catalog"])
        for row in value["findings"]:
            self.assertEqual(expected_finding, set(row))
            self.assertEqual(
                {
                    "mode",
                    "origin",
                },
                set(row["provenance"]),
            )
            self.assertEqual(
                {
                    "origin_review_id",
                    "origin_commit",
                    "origin_verdict_digest",
                },
                set(row["provenance"]["origin"]),
            )

    def test_current_professional_rejects_all_legacy_authority_aliases(
        self,
    ) -> None:
        value = professional_fixture(review_mode="full-fresh")
        authority = _professional_authority(value)
        for field, replacement in (
            ("source_fingerprints", {}),
            ("package_fingerprint", SHA_A),
            ("review_binding_fingerprint", SHA_B),
            ("source_fingerprint", SHA_C),
        ):
            changed = copy.deepcopy(value)
            if field == "source_fingerprints":
                changed[field] = replacement
            else:
                changed["findings"][0][field] = replacement
            with self.subTest(field=field), self.assertRaises(
                ATTESTATION.AttestationError
            ):
                ATTESTATION.validate_attestation(
                    changed,
                    expected_professional_current_bindings=authority,
                )


def professional_fixture(
    *, all_carry: bool = False, review_mode: str = "incremental"
) -> dict:
    if all_carry:
        review_mode = "all-carry"
    value = _common(
        axis=ATTESTATION.PROFESSIONAL_COMPLETENESS_AXIS,
        kind=ATTESTATION.PROFESSIONAL_COMPLETENESS_ATTESTATION_KIND,
        fingerprints={
            "professional_packages": SHA_A,
            "professional_review_bindings": SHA_B,
            "professional_review_contract": SHA_A,
        },
        reviewers=[] if review_mode == "all-carry" else _professional_reviewers(),
    )
    value.pop("source_fingerprints")
    value["review_contract_fingerprint"] = (
        PANEL._professional_evidence_review_contract_fingerprint()
    )
    value["dependency_material_catalog"] = {
        "adjacent-skill": SHA_A,
    }
    value["review_id"] = "professional-completeness-review-2026-08-10-r1"
    if review_mode == "all-carry":
        value["findings"] = [
            _compact_professional_finding_fixture(
                "carried-skill",
                mode="carried",
                origin_review_id="professional-completeness-origin-r1",
            )
        ]
    elif review_mode == "full-fresh":
        value["findings"] = [
            _compact_professional_finding_fixture(
                skill_id,
                mode="fresh",
                origin_review_id=value["review_id"],
            )
            for skill_id in ("fresh-skill-one", "fresh-skill-two")
        ]
    else:
        value["findings"] = [
            _compact_professional_finding_fixture(
                "carried-skill",
                mode="carried",
                origin_review_id="professional-completeness-origin-r1",
            ),
            _compact_professional_finding_fixture(
                "fresh-skill",
                mode="fresh",
                origin_review_id=value["review_id"],
            ),
        ]
    value["review_cost_input"] = _review_cost_input(review_mode)
    return ATTESTATION.finalize_attestation(
        value, expected_professional_current_bindings=_professional_authority(value)
    )


def _carry_material(skill_id: str, content: str) -> dict:
    return {
        "path": f"src/foundation/{skill_id}/SKILL.md",
        "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "line_count": len(content.splitlines()),
        "content": content,
    }


def _carry_targets(*, changed_skill_id: str | None = None) -> list[dict]:
    skill_ids = ("adjacent-skill", "carried-skill", "unaffected-skill")
    targets = []
    for skill_id in skill_ids:
        content = f"# {skill_id}\n\nBounded current package evidence.\n"
        if skill_id == changed_skill_id:
            content += "Changed current package evidence.\n"
        ranking = [
            {
                "skill_id": candidate_id,
                "rank": index,
                "total_score": 0,
                "signals": {},
            }
            for index, candidate_id in enumerate(
                (value for value in skill_ids if value != skill_id), start=1
            )
        ]
        required_id = (
            "unaffected-skill"
            if skill_id == "adjacent-skill"
            else "adjacent-skill"
        )
        required = [
            {
                **next(
                    row for row in ranking
                    if row["skill_id"] == required_id
                ),
                "declared": False,
                "selection_reasons": ["fixture-required"],
            }
        ]
        responsibility = {"marker": skill_id}
        adjacency = {
            "algorithm": "fixture-v1",
            "document_frequency_filter": {},
            "declared_skills": [],
            "required_candidate_selection": {"version": "fixture-v1"},
            "required_candidates": required,
            "required_candidates_fingerprint": _sha(required),
            "full_catalog_count": len(ranking),
            "full_catalog_ranking": ranking,
            "full_catalog_ranking_fingerprint": _sha(ranking),
        }
        target = {
            "skill_id": skill_id,
            "layer": "foundation",
            "required_expertise_tags": ["repository-tooling"],
            "root": _carry_material(skill_id, content),
            "indexed_references": [],
            "registry": {
                "path": "src/registry.yaml",
                "entry_fingerprint": _sha(responsibility),
                "responsibility_contract": responsibility,
            },
            "routing_adjacency": adjacency,
        }
        targets.append(target)
    return targets


def _all_carry_attestation_for_targets(targets: list[dict]) -> dict:
    bindings = PANEL.professional_carry.professional_review_bindings(targets)
    value = professional_fixture(all_carry=True)
    value["findings"] = [
        _compact_professional_finding_fixture(
            skill_id,
            mode="carried",
            origin_review_id="professional-completeness-origin-r1",
        )
        for skill_id in sorted(bindings)
    ]
    for row in value["findings"]:
        binding = bindings[row["skill_id"]]
        required_ids = [
            item
            for item in binding["adjacency"]["required_candidate_ids"]
        ]
        dependencies = {
            candidate_id: bindings[candidate_id][
                "package_material_binding"
            ]
            for candidate_id in required_ids
        }
        row.update(
            {
                "package_material_binding": binding[
                    "package_material_binding"
                ],
                "review_unit_binding": binding["review_unit_binding"],
                "required_expertise_tags": binding[
                    "required_expertise_tags"
                ],
                "dependency_ids": sorted(dependencies),
            }
        )
    value["dependency_material_catalog"] = dict(
        sorted(
            {
                candidate_id: bindings[candidate_id][
                    "package_material_binding"
                ]
                for row in value["findings"]
                for candidate_id in row["dependency_ids"]
            }.items()
        )
    )
    value["review_cost_input"] = _review_cost_input("all-carry")
    return ATTESTATION.finalize_attestation(
        value,
        expected_professional_current_bindings=(
            PANEL.professional_carry.professional_current_authority(
                bindings,
                authenticated_claims=_professional_claims(value),
            )
        ),
    )


def _current_professional_attestation_fixture() -> tuple[dict, dict]:
    targets = _carry_targets()
    for target in targets:
        target["required_expertise_tags"] = [
            "foundation-repository-intelligence"
        ]
    value = _all_carry_attestation_for_targets(targets)
    bindings = PANEL.professional_carry.professional_review_bindings(targets)
    snapshot = PANEL.professional_carry.professional_carry_snapshot(
        bindings,
        review_contract_fingerprint=value["review_contract_fingerprint"],
    )
    packet = {
        "review_id": "professional-completeness-review-2026-08-10-r2",
        "created_on": "2026-08-10",
        "professional_targets": [
            {
                **copy.deepcopy(target),
                "review_binding": copy.deepcopy(
                    snapshot["targets"][target["skill_id"]]
                ),
            }
            for target in targets
        ],
    }
    return value, packet


class ExpertPanelAttestationRepairTests(unittest.TestCase):
    def test_current_compact_storage_schema_is_v2(self) -> None:
        self.assertEqual(2, ATTESTATION.ATTESTATION_SCHEMA_VERSION)
        self.assertEqual(
            "25b596b788197ac59ce85d09d701eb3fd004b5418589b119857c856838184f49",
            PANEL.panel_contracts.professional_review_contract_fingerprint(),
        )
        self.assertEqual(
            "readability-target-authority-currentness-v2",
            PANEL.panel_contracts.READABILITY_CURRENTNESS_CONTRACT_VERSION,
        )
        self.assertEqual(
            "readability-complete-target-authority-manifest-v2",
            PANEL.panel_contracts.READABILITY_TARGET_MANIFEST_CONTRACT_ID,
        )
        self.assertEqual(
            "readability-review-unit-binding-v3",
            PANEL.panel_contracts.READABILITY_REVIEW_UNIT_BINDING_CONTRACT_ID,
        )

    def test_professional_storage_codec_interns_all_repeated_strings_and_round_trips(
        self,
    ) -> None:
        value = professional_fixture(review_mode="full-fresh")
        authority = _professional_authority(value)
        payload = ATTESTATION.canonical_attestation_bytes(
            value,
            expected_professional_current_bindings=authority,
        )
        physical = json.loads(payload)
        self.assertEqual(
            "professional-string-catalog-v1",
            physical["storage_encoding"],
        )
        catalog = physical["string_catalog"]
        self.assertEqual(sorted(set(catalog)), catalog)
        for field in (
            "schema_version",
            "kind",
            "axis",
            "review_id",
            "decided_on",
            "review_contract_fingerprint",
        ):
            self.assertEqual(value[field], physical[field])

        selector = ATTESTATION.parse_attestation_storage_selector_bytes(
            payload
        )
        routing = {
            "schema_version",
            "kind",
            "axis",
            "review_id",
            "decided_on",
            "review_contract_fingerprint",
        }
        counts: dict[str, int] = {}

        def count_strings(item: object) -> None:
            if isinstance(item, dict):
                for key, child in item.items():
                    if item is selector and key in routing:
                        continue
                    count_strings(child)
            elif isinstance(item, list):
                for child in item:
                    count_strings(child)
            elif isinstance(item, str):
                counts[item] = counts.get(item, 0) + 1

        count_strings(selector)
        self.assertEqual(
            sorted(text for text, count in counts.items() if count >= 2),
            catalog,
        )

        raw_literals: list[str] = []

        def collect_raw_literals(item: object) -> None:
            if isinstance(item, dict):
                for key, child in item.items():
                    if item is physical and key in routing | {
                        "storage_encoding",
                        "string_catalog",
                    }:
                        continue
                    collect_raw_literals(child)
            elif isinstance(item, list):
                for child in item:
                    collect_raw_literals(child)
            elif isinstance(item, str):
                raw_literals.append(item)

        collect_raw_literals(physical)
        self.assertEqual(set(), set(catalog) & set(raw_literals))
        self.assertEqual(
            value,
            ATTESTATION.parse_attestation_bytes(
                payload,
                expected_professional_current_bindings=authority,
            ),
        )

        bare = json.dumps(
            selector,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8") + b"\n"
        with self.assertRaises(ATTESTATION.AttestationError):
            ATTESTATION.parse_attestation_bytes(
                bare,
                expected_professional_current_bindings=authority,
            )

    def test_professional_storage_codec_rejects_noncanonical_catalogs_and_refs(
        self,
    ) -> None:
        value = professional_fixture(review_mode="full-fresh")
        authority = _professional_authority(value)
        payload = ATTESTATION.canonical_attestation_bytes(
            value,
            expected_professional_current_bindings=authority,
        )
        physical = json.loads(payload)
        catalog = physical["string_catalog"]
        self.assertGreater(len(catalog), 1)

        def encoded(changed: dict) -> bytes:
            return json.dumps(
                changed,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8") + b"\n"

        def replace_first_ref(item: object, replacement) -> bool:
            if isinstance(item, dict):
                for key, child in item.items():
                    if isinstance(child, int) and not isinstance(child, bool) and child < 0:
                        item[key] = replacement(child)
                        return True
                    if replace_first_ref(child, replacement):
                        return True
            elif isinstance(item, list):
                for index, child in enumerate(item):
                    if isinstance(child, int) and not isinstance(child, bool) and child < 0:
                        item[index] = replacement(child)
                        return True
                    if replace_first_ref(child, replacement):
                        return True
            return False

        mutations: list[tuple[str, dict]] = []
        for field in ("storage_encoding", "string_catalog"):
            changed = copy.deepcopy(physical)
            changed.pop(field)
            mutations.append((f"missing-{field}", changed))
        changed = copy.deepcopy(physical)
        changed["unexpected_storage_field"] = True
        mutations.append(("extra-field", changed))
        changed = copy.deepcopy(physical)
        changed["storage_encoding"] = "professional-string-catalog-v0"
        mutations.append(("wrong-encoding", changed))
        changed = copy.deepcopy(physical)
        changed["string_catalog"].append(changed["string_catalog"][-1])
        mutations.append(("duplicate-catalog-entry", changed))
        changed = copy.deepcopy(physical)
        changed["string_catalog"].append("zzzz-unused-storage-catalog-entry")
        mutations.append(("unused-catalog-entry", changed))
        changed = copy.deepcopy(physical)
        changed["string_catalog"] = sorted(
            [*changed["string_catalog"], "e\u0301"]
        )
        mutations.append(("noncanonical-unicode-catalog-entry", changed))
        changed = copy.deepcopy(physical)
        old_catalog = changed["string_catalog"]
        changed["string_catalog"] = list(reversed(old_catalog))
        ref_count = len(old_catalog)

        def reverse_ref(reference: int) -> int:
            return -(ref_count - (-reference - 1))

        def rewrite_all_refs(item: object) -> None:
            if isinstance(item, dict):
                for key, child in item.items():
                    if isinstance(child, int) and not isinstance(child, bool) and child < 0:
                        item[key] = reverse_ref(child)
                    else:
                        rewrite_all_refs(child)
            elif isinstance(item, list):
                for index, child in enumerate(item):
                    if isinstance(child, int) and not isinstance(child, bool) and child < 0:
                        item[index] = reverse_ref(child)
                    else:
                        rewrite_all_refs(child)

        rewrite_all_refs(changed)
        mutations.append(("reordered-catalog-with-rewritten-refs", changed))
        changed = copy.deepcopy(physical)
        self.assertTrue(
            replace_first_ref(
                changed,
                lambda reference: catalog[-reference - 1],
            )
        )
        mutations.append(("eligible-literal-not-interned", changed))
        changed = copy.deepcopy(physical)
        self.assertTrue(
            replace_first_ref(changed, lambda _reference: -(len(catalog) + 1))
        )
        mutations.append(("out-of-range-reference", changed))
        for numeric in (-1, True):
            changed = copy.deepcopy(physical)
            changed["review_cost_input"]["plan_lineage_depth"] = numeric
            mutations.append((f"invalid-numeric-{numeric!r}", changed))

        for label, changed in mutations:
            with self.subTest(label=label), self.assertRaises(
                ATTESTATION.AttestationError
            ):
                ATTESTATION.parse_attestation_bytes(
                    encoded(changed),
                    expected_professional_current_bindings=authority,
                )
        for label, raw in (
            ("bom", b"\xef\xbb\xbf" + payload),
            (
                "noncanonical-json",
                json.dumps(physical, ensure_ascii=False, indent=2).encode(
                    "utf-8"
                )
                + b"\n",
            ),
            (
                "duplicate-physical-key",
                payload.replace(
                    b'"storage_encoding":',
                    b'"storage_encoding":"duplicate",'
                    b'"storage_encoding":',
                    1,
                ),
            ),
            (
                "recursive-json",
                b'{"axis":"professional-completeness",'
                b'"schema_version":2,"value":'
                + b"[" * 2_000
                + b"0"
                + b"]" * 2_000
                + b"}\n",
            ),
        ):
            with self.subTest(label=label), self.assertRaises(
                ATTESTATION.AttestationError
            ):
                ATTESTATION.parse_attestation_bytes(
                    raw,
                    expected_professional_current_bindings=authority,
                )

    def test_professional_codec_does_not_change_readability_or_semantic_bytes(
        self,
    ) -> None:
        readability = ATTESTATION.canonical_attestation_bytes(
            readability_fixture(),
            expected_readability_current_bindings=(
                _compact_readability_bindings()
            ),
        )
        semantic = ATTESTATION.canonical_attestation_bytes(
            semantic_fixture(),
            expected_semantic_current_bindings=_semantic_expected_bindings(),
        )
        self.assertEqual(
            "90510de8c48742a87d584923e351acb3241b9346cea9240c12bab19c6ebaf627",
            hashlib.sha256(readability).hexdigest(),
        )
        self.assertEqual(
            "8de2dceab394c8b970bfb1ff6d558e354a6bee75e4a4218208fd2d611af1e664",
            hashlib.sha256(semantic).hexdigest(),
        )

    @staticmethod
    def _readability_coverage() -> tuple[list[dict], list[dict], list[dict]]:
        return (
            [
                {
                    "path": "src/foundation/example/SKILL.md",
                    "classification": "REVIEW_DENSITY",
                }
            ],
            [
                {
                    "document_id": "document-one",
                    "highest_band": "review-as-complex",
                }
            ],
            [
                {
                    "target_id": "action-one",
                    "skill_id": "example",
                    "path": "src/foundation/example/SKILL.md",
                    "front_loaded_action_score": 1,
                }
            ],
        )

    @staticmethod
    def _adapt_readability_fixture() -> tuple[dict, dict]:
        packet, metadata = _readability_decision_adapter_fixture()
        with tempfile.TemporaryDirectory(dir=ROOT) as raw:
            root = Path(raw)
            packet_path = root / "packet.json"
            packet_path.write_text(
                json.dumps(packet, indent=2) + "\n", encoding="utf-8"
            )
            packet_sha256 = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            ballot_values = []
            with mock.patch.object(
                PANEL,
                "_current_readability_target_projection",
                return_value=(
                    packet["source_fingerprints"],
                    packet["content_targets"],
                    packet["readability_targets"],
                    packet["actionability_targets"],
                ),
            ):
                PANEL.validate_packet(packet)
                for index, voter in enumerate(_basic_reviewers(), start=1):
                    ballot = PANEL.prepare_readability_ballot_template(
                        packet=packet,
                        packet_sha256=packet_sha256,
                        voter_id=voter["voter_id"],
                        agent_id=voter["agent_id"],
                        role=voter["role"],
                        expertise=voter["expertise"],
                        created_on=packet["created_on"],
                    )
                    for vote in ballot["content_votes"]:
                        vote.update(
                            decision="accepted-current-density",
                            reason_code=(
                                "bounded-density-preserves-professional-coverage"
                            ),
                            rationale=(
                                "The current density preserves one bounded "
                                "professional decision model."
                            ),
                        )
                    for document in ballot["readability_votes"]:
                        for finding in document["finding_reviews"]:
                            finding.update(
                                decision="accepted-current-readability",
                                reason_code=(
                                    "bounded-enumeration-improves-precision"
                                ),
                                rationale=(
                                    "The sentence preserves one bounded and "
                                    "indivisible readability decision."
                                ),
                            )
                    self_order = [
                        row["finding_id"]
                        for row in ballot["readability_votes"][0][
                            "finding_reviews"
                        ]
                    ]
                    if self_order != metadata["source_order_finding_ids"]:
                        raise AssertionError("ballot did not preserve packet order")
                    ballot_path = root / f"{index}-{voter['voter_id']}.json"
                    ballot_path.write_text(
                        json.dumps(ballot, indent=2) + "\n", encoding="utf-8"
                    )
                    PANEL.validate_ballot(
                        packet,
                        ballot,
                        packet_sha256=packet_sha256,
                    )
                    ballot_values.append((ballot_path, ballot))
                record = PANEL.aggregate_ballots(
                    packet=packet,
                    packet_path=packet_path,
                    ballot_values=ballot_values,
                    decided_on=packet["created_on"],
                )
                decision_path = root / "decision.json"
                decision_path.write_text(
                    json.dumps(record, indent=2) + "\n", encoding="utf-8"
                )
                PANEL.validate_decision_record(
                    record,
                    record_path=decision_path,
                )
                with mock.patch.object(PANEL, "prepare_packet", return_value=packet):
                    compact = PANEL._readability_attestation_from_decision(
                        record,
                        decision_path=decision_path,
                        audit={},
                    )
        return compact, metadata

    def test_compact_readability_requires_complete_current_binding_authority(
        self,
    ) -> None:
        value, bindings = _compact_readability_value()
        with self.assertRaises(ATTESTATION.AttestationError):
            ATTESTATION.finalize_attestation(value)
        finalized = ATTESTATION.finalize_attestation(
            value, expected_readability_current_bindings=bindings
        )
        payload = ATTESTATION.canonical_attestation_bytes(
            finalized, expected_readability_current_bindings=bindings
        )
        self.assertEqual(
            finalized,
            ATTESTATION.parse_attestation_bytes(
                payload,
                expected_source_fingerprints=finalized["source_fingerprints"],
                expected_readability_current_bindings=bindings,
            ),
        )
        self.assertLess(len(payload), 12_000)
        self.assertEqual(
            {
                "category",
                "target_id",
                "source_fingerprint",
                "review_binding_fingerprint",
                "votes",
                "result",
            },
            set(finalized["findings"][0]),
        )
        self.assertEqual(
            {
                "category",
                "target_id",
                "source_fingerprint",
                "review_binding_fingerprint",
                "finding_reviews",
                "result",
            },
            set(finalized["findings"][1]),
        )
        self.assertEqual(
            {
                "finding_id",
                "source_fingerprint",
                "review_binding_fingerprint",
                "votes",
                "result",
            },
            set(finalized["findings"][1]["finding_reviews"][0]),
        )
        forbidden = {
            "sentence", "line", "source_line", "claim", "path", "span",
            "source_span", "candidate", "document_context",
            "document_part", "source_selector", "front_window",
        }

        def keys(item: object) -> set[str]:
            if isinstance(item, dict):
                return set(item) | {
                    nested
                    for child in item.values()
                    for nested in keys(child)
                }
            if isinstance(item, list):
                return {nested for child in item for nested in keys(child)}
            return set()

        self.assertEqual(set(), forbidden & keys(finalized))

        mutations = []
        for field in ("source_fingerprint", "review_binding_fingerprint"):
            changed = copy.deepcopy(finalized)
            changed["findings"][0][field] = SHA_A
            mutations.append(changed)
        coordinated = copy.deepcopy(finalized)
        coordinated["findings"][0]["source_fingerprint"] = SHA_A
        coordinated["findings"][0]["review_binding_fingerprint"] = SHA_B
        mutations.append(coordinated)
        for changed in mutations:
            with self.assertRaises(ATTESTATION.AttestationError):
                ATTESTATION.validate_attestation(
                    changed, expected_readability_current_bindings=bindings
                )

        partial = copy.deepcopy(bindings)
        partial["actionability"].clear()
        extra = copy.deepcopy(bindings)
        extra["content"]["extra"] = copy.deepcopy(
            next(iter(extra["content"].values()))
        )
        for expected in (partial, extra):
            with self.assertRaises(ATTESTATION.AttestationError):
                ATTESTATION.validate_attestation(
                    finalized,
                    expected_readability_current_bindings=expected,
                )

    def test_readability_source_shape_is_exact3_current_exact4_legacy(self) -> None:
        current = readability_fixture()
        bindings = _compact_readability_bindings()
        self.assertEqual(
            "current",
            ATTESTATION.readability_source_fingerprint_shape(
                current["source_fingerprints"]
            ),
        )

        legacy = copy.deepcopy(current)
        legacy["source_fingerprints"] = {
            "ai_readability": SHA_A,
            "reference_content": SHA_B,
            "root_content": SHA_C,
            "skill_detector": _sha("legacy-skill-detector"),
        }
        self.assertEqual(
            "legacy",
            ATTESTATION.readability_source_fingerprint_shape(
                legacy["source_fingerprints"]
            ),
        )
        with self.assertRaisesRegex(ATTESTATION.AttestationError, "stale"):
            ATTESTATION.validate_attestation(
                legacy,
                expected_readability_current_bindings=bindings,
            )
        legacy_payload = (
            json.dumps(
                legacy,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        )
        with self.assertRaisesRegex(
            ATTESTATION.AttestationError,
            "stale|binding|compact storage schema_version",
        ):
            ATTESTATION.parse_attestation_bytes(
                legacy_payload,
                expected_source_fingerprints=legacy["source_fingerprints"],
                expected_readability_current_bindings=bindings,
            )
        with self.assertRaisesRegex(
            ATTESTATION.AttestationError,
            "stale",
        ):
            ATTESTATION.validate_attestation(
                legacy,
                expected_source_fingerprints=current["source_fingerprints"],
                expected_readability_current_bindings=bindings,
            )
        with self.assertRaisesRegex(
            ATTESTATION.AttestationError,
            "stale",
        ):
            ATTESTATION.canonical_attestation_bytes(
                legacy,
                expected_readability_current_bindings=bindings,
            )

        malformed = copy.deepcopy(legacy)
        malformed["source_fingerprints"].pop("skill_detector")
        with self.assertRaisesRegex(
            ATTESTATION.AttestationError,
            "source fingerprint fields are not closed",
        ):
            ATTESTATION.validate_attestation(
                malformed,
                expected_readability_current_bindings=bindings,
            )

    def test_readability_review_bindings_exclude_report_state_but_bind_exact_evidence(
        self,
    ) -> None:
        targets = _compact_readability_targets()
        content = ATTESTATION.readability_target_authority(
            category="content", target=targets["content"]
        )
        administrative = copy.deepcopy(targets["content"])
        administrative["review_state"] = "REPORT_ONLY"
        administrative["review_reasons"] = ["report-only"]
        self.assertEqual(
            content["review_binding_fingerprint"],
            ATTESTATION.readability_target_authority(
                category="content", target=administrative
            )["review_binding_fingerprint"],
        )

        readability = ATTESTATION.readability_target_authority(
            category="readability", target=targets["readability"]
        )
        finding_id = _sha("finding-one")
        for field, mutate in (
            (
                "sentence",
                lambda finding: finding.__setitem__(
                    "sentence", finding["sentence"] + " changed"
                ),
            ),
            (
                "sentence-fingerprint",
                lambda finding: finding.__setitem__(
                    "sentence_fingerprint", SHA_A
                ),
            ),
            (
                "source-span",
                lambda finding: finding["source_span"].__setitem__(
                    "end_offset", finding["source_span"]["end_offset"] - 1
                ),
            ),
        ):
            changed = copy.deepcopy(targets["readability"])
            mutate(changed["findings"][0])
            authority = ATTESTATION.readability_target_authority(
                category="readability", target=changed
            )
            with self.subTest(field=field):
                self.assertNotEqual(
                    readability["review_binding_fingerprint"],
                    authority["review_binding_fingerprint"],
                )
                self.assertNotEqual(
                    readability["findings"][finding_id][
                        "review_binding_fingerprint"
                    ],
                    authority["findings"][finding_id][
                        "review_binding_fingerprint"
                    ],
                )

    def test_readability_decision_adapter_persists_only_compact_review_facts(
        self,
    ) -> None:
        compact, metadata = self._adapt_readability_fixture()
        serialized = json.dumps(compact, sort_keys=True)
        for forbidden in (
            '"sentence"', '"line"', '"source_line"', '"claim"',
            '"path"', '"source_span"', '"document_context"',
            '"front_window"',
        ):
            self.assertNotIn(forbidden, serialized)
        self.assertEqual("accepted-current-readability", compact["verdict"])
        self.assertEqual(
            ["content", "readability"],
            [row["category"] for row in compact["findings"]],
        )
        self.assertEqual(3, len(compact["findings"][0]["votes"]))
        finding_ids = [
            row["finding_id"]
            for row in compact["findings"][1]["finding_reviews"]
        ]
        self.assertEqual([0, 100], metadata["source_offsets"])
        self.assertEqual(2, len(metadata["source_order_finding_ids"]))
        self.assertGreater(
            metadata["source_order_finding_ids"][0],
            metadata["source_order_finding_ids"][1],
        )
        self.assertEqual(metadata["expected_finding_ids"], finding_ids)
        self.assertEqual(
            list(reversed(metadata["source_order_finding_ids"])),
            finding_ids,
        )
        self.assertTrue(
            all(
                len(row["votes"]) == 3
                for row in compact["findings"][1]["finding_reviews"]
            )
        )

    def test_readability_decision_adapter_is_ballot_permutation_deterministic(
        self,
    ) -> None:
        first, first_metadata = self._adapt_readability_fixture()
        second, second_metadata = self._adapt_readability_fixture()
        self.assertEqual(first_metadata, second_metadata)
        first["review_artifacts"]["decision"]["sha256"] = "artifact-local"
        second["review_artifacts"]["decision"]["sha256"] = "artifact-local"
        self.assertEqual(first, second)

    def test_compact_readability_rejects_duplicate_finding_ids(self) -> None:
        value, bindings = _compact_readability_value()
        value["findings"][1]["finding_reviews"].append(
            copy.deepcopy(value["findings"][1]["finding_reviews"][0])
        )
        with self.assertRaisesRegex(
            ATTESTATION.AttestationError,
            "readability finding IDs are not canonical",
        ):
            ATTESTATION.finalize_attestation(
                value,
                expected_readability_current_bindings=bindings,
            )

    def test_compact_readability_review_units_reject_identity_substitution(
        self,
    ) -> None:
        value, bindings = _compact_readability_value()
        second_target = copy.deepcopy(_compact_readability_targets()["content"])
        second_target["path"] = "src/foundation/other/SKILL.md"
        second_target["content_fingerprint"] = _sha("other-content-source")
        second_authority = ATTESTATION.readability_target_authority(
            category="content", target=second_target
        )
        bindings["content"][second_authority["target_id"]] = second_authority
        value["source_fingerprints"]["readability_target_manifest"] = (
            ATTESTATION.readability_target_manifest_fingerprint(bindings)
        )
        value["findings"].append(
            {
                "category": "content",
                "target_id": second_authority["target_id"],
                "source_fingerprint": second_authority["source_fingerprint"],
                "review_binding_fingerprint": second_authority[
                    "review_binding_fingerprint"
                ],
                "votes": [
                    _simple_vote(
                        reviewer["voter_id"],
                        "tracked-tightening",
                        "multiple-independent-actions",
                    )
                    for reviewer in value["reviewers"]
                ],
                "result": {},
            }
        )
        value["findings"].sort(
            key=lambda row: (
                ("content", "readability", "actionability").index(
                    row["category"]
                ),
                row["target_id"],
            )
        )
        finalized = ATTESTATION.finalize_attestation(
            value,
            expected_readability_current_bindings=bindings,
        )
        compact = json.loads(
            ATTESTATION.canonical_attestation_bytes(
                finalized,
                expected_readability_current_bindings=bindings,
            )
        )
        content_rows = [
            row for row in compact["findings"] if row["category"] == "content"
        ]
        self.assertNotEqual(
            content_rows[0]["votes"][0]["disposition"],
            content_rows[1]["votes"][0]["disposition"],
        )
        content_rows[0]["target_id"], content_rows[1]["target_id"] = (
            content_rows[1]["target_id"],
            content_rows[0]["target_id"],
        )
        compact["findings"].sort(
            key=lambda row: (
                ("content", "readability", "actionability").index(
                    row["category"]
                ),
                row["target_id"],
            )
        )
        tampered = (
            json.dumps(
                compact,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        )
        with self.assertRaisesRegex(
            ATTESTATION.AttestationError,
            "review unit binding",
        ):
            ATTESTATION.parse_attestation_bytes(
                tampered,
                expected_source_fingerprints=finalized[
                    "source_fingerprints"
                ],
                expected_readability_current_bindings=bindings,
            )

    def test_compact_readability_findings_reject_identity_substitution(
        self,
    ) -> None:
        value, bindings = _compact_readability_value()
        target = copy.deepcopy(_compact_readability_targets()["readability"])
        second_sentence = "Another bounded sentence has a different decision."
        second_finding = {
            "finding_id": _sha("finding-two"),
            "sentence": second_sentence,
            "sentence_fingerprint": hashlib.sha256(
                ("ai-readability-sentence-v1\0" + second_sentence).encode(
                    "utf-8"
                )
            ).hexdigest(),
            "source_span": {
                "start_offset": 100,
                "end_offset": 100 + len(second_sentence),
            },
        }
        target["findings"].append(second_finding)
        authority = ATTESTATION.readability_target_authority(
            category="readability", target=target
        )
        bindings["readability"] = {authority["target_id"]: authority}
        value["source_fingerprints"]["readability_target_manifest"] = (
            ATTESTATION.readability_target_manifest_fingerprint(bindings)
        )
        document = value["findings"][1]
        document["source_fingerprint"] = authority["source_fingerprint"]
        document["review_binding_fingerprint"] = authority[
            "review_binding_fingerprint"
        ]
        document["finding_reviews"][0]["source_fingerprint"] = authority[
            "findings"
        ][_sha("finding-one")]["source_fingerprint"]
        document["finding_reviews"][0][
            "review_binding_fingerprint"
        ] = authority["findings"][_sha("finding-one")][
            "review_binding_fingerprint"
        ]
        document["finding_reviews"].append(
            {
                "finding_id": second_finding["finding_id"],
                "source_fingerprint": authority["findings"][
                    second_finding["finding_id"]
                ]["source_fingerprint"],
                "review_binding_fingerprint": authority["findings"][
                    second_finding["finding_id"]
                ]["review_binding_fingerprint"],
                "votes": [
                    _simple_vote(
                        reviewer["voter_id"],
                        "tracked-tightening",
                        "multiple-independent-actions",
                    )
                    for reviewer in value["reviewers"]
                ],
                "result": {},
            }
        )
        document["finding_reviews"].sort(key=lambda row: row["finding_id"])
        finalized = ATTESTATION.finalize_attestation(
            value,
            expected_readability_current_bindings=bindings,
        )
        compact = json.loads(
            ATTESTATION.canonical_attestation_bytes(
                finalized,
                expected_readability_current_bindings=bindings,
            )
        )
        findings = next(
            row["finding_reviews"]
            for row in compact["findings"]
            if row["category"] == "readability"
        )
        self.assertNotEqual(
            findings[0]["votes"][0]["disposition"],
            findings[1]["votes"][0]["disposition"],
        )
        findings[0]["finding_id"], findings[1]["finding_id"] = (
            findings[1]["finding_id"],
            findings[0]["finding_id"],
        )
        findings.sort(key=lambda row: row["finding_id"])
        tampered = (
            json.dumps(
                compact,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        )
        with self.assertRaisesRegex(
            ATTESTATION.AttestationError,
            "review unit binding",
        ):
            ATTESTATION.parse_attestation_bytes(
                tampered,
                expected_source_fingerprints=finalized[
                    "source_fingerprints"
                ],
                expected_readability_current_bindings=bindings,
            )

    def test_compact_readability_unknown_ids_and_unit_binding_tamper_fail_closed(
        self,
    ) -> None:
        value, bindings = _compact_readability_value()
        finalized = ATTESTATION.finalize_attestation(
            value,
            expected_readability_current_bindings=bindings,
        )
        payload = ATTESTATION.canonical_attestation_bytes(
            finalized,
            expected_readability_current_bindings=bindings,
        )
        compact = json.loads(payload)
        cases = []
        unknown_target = copy.deepcopy(compact)
        unknown_target["findings"][0]["target_id"] = "unknown-target"
        cases.append(("unknown-target", unknown_target))
        unknown_finding = copy.deepcopy(compact)
        unknown_finding["findings"][1]["finding_reviews"][0][
            "finding_id"
        ] = "0" * 64
        cases.append(("unknown-finding", unknown_finding))
        missing_binding = copy.deepcopy(compact)
        missing_binding["findings"][0].pop("review_unit_binding", None)
        cases.append(("missing-binding", missing_binding))
        tampered_binding = copy.deepcopy(compact)
        tampered_binding["findings"][0]["review_unit_binding"] = "0" * 64
        cases.append(("tampered-binding", tampered_binding))
        for label, changed in cases:
            tampered = (
                json.dumps(
                    changed,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
                + b"\n"
            )
            with self.subTest(label=label), self.assertRaises(
                ATTESTATION.AttestationError
            ):
                ATTESTATION.parse_attestation_bytes(
                    tampered,
                    expected_source_fingerprints=finalized[
                        "source_fingerprints"
                    ],
                    expected_readability_current_bindings=bindings,
                )

    def test_fixed_readability_requires_exact_current_coverage_and_contract(
        self,
    ) -> None:
        regression = PANEL._load_professional_regression_validator()
        density, readability, actionability = self._readability_coverage()
        value = readability_fixture()
        regression._validate_fixed_readability_coverage(
            value,
            required_density=density,
            required_readability=readability,
            required_actionability=actionability,
            expected_review_contract_fingerprint=SHA_A,
        )
        mutations = []
        empty = copy.deepcopy(value)
        empty["findings"] = []
        mutations.append(empty)
        for category in ("content", "readability", "actionability"):
            missing = copy.deepcopy(value)
            missing["findings"] = [
                row for row in missing["findings"]
                if row["category"] != category
            ]
            mutations.append(missing)
        extra = copy.deepcopy(value)
        extra_row = copy.deepcopy(extra["findings"][0])
        extra_row["target_id"] = "src/foundation/extra/SKILL.md"
        extra["findings"].append(extra_row)
        mutations.append(extra)
        duplicate = copy.deepcopy(value)
        duplicate["findings"].append(copy.deepcopy(duplicate["findings"][0]))
        mutations.append(duplicate)
        stale = copy.deepcopy(value)
        stale["review_contract_fingerprint"] = SHA_B
        mutations.append(stale)
        for mutation in mutations:
            with self.subTest(mutation=len(mutation["findings"])), self.assertRaises(
                ValueError
            ):
                regression._validate_fixed_readability_coverage(
                    mutation,
                    required_density=density,
                    required_readability=readability,
                    required_actionability=actionability,
                    expected_review_contract_fingerprint=SHA_A,
                )

    def test_regression_loader_requires_complete_readability_current_map(self) -> None:
        regression = PANEL._load_professional_regression_validator()
        value = readability_fixture()
        bindings = _compact_readability_bindings()
        raw = ATTESTATION.canonical_attestation_bytes(
            value, expected_readability_current_bindings=bindings
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixed = root / ATTESTATION.READABILITY_ATTESTATION_PATH
            fixed.parent.mkdir(parents=True)
            fixed.write_bytes(raw)
            kwargs = {
                "expected_source_fingerprints": value["source_fingerprints"],
                "expected_review_contract_fingerprint": value[
                    "review_contract_fingerprint"
                ],
            }
            with mock.patch.object(regression, "ROOT", root), mock.patch.object(
                regression, "_validate_expert_evidence"
            ):
                loaded = regression._load_fixed_compact_attestation(
                    ATTESTATION.READABILITY_AXIS,
                    expected_readability_current_bindings=bindings,
                    **kwargs,
                )
                self.assertEqual(value, loaded[0])
                with self.assertRaises(ValueError):
                    regression._load_fixed_compact_attestation(
                        ATTESTATION.READABILITY_AXIS,
                        **kwargs,
                    )
                partial = copy.deepcopy(bindings)
                partial["actionability"].clear()
                with self.assertRaises(ValueError):
                    regression._load_fixed_compact_attestation(
                        ATTESTATION.READABILITY_AXIS,
                        expected_readability_current_bindings=partial,
                        **kwargs,
                    )
                fixed.unlink()
                self.assertIsNone(
                    regression._load_fixed_compact_attestation(
                        ATTESTATION.READABILITY_AXIS,
                        expected_readability_current_bindings=bindings,
                        **kwargs,
                    )
                )
                target = root / "unsafe-readability-target.json"
                target.write_bytes(raw)
                fixed.symlink_to(target)
                with self.assertRaisesRegex(ValueError, "symbolic links"):
                    regression._load_fixed_compact_attestation(
                        ATTESTATION.READABILITY_AXIS,
                        expected_readability_current_bindings=bindings,
                        **kwargs,
                    )

    def test_compact_professional_retains_only_decisions_and_exact_origin(self) -> None:
        review_id = "professional-completeness-review-2026-08-10-r1"
        value = _common(
            axis=ATTESTATION.PROFESSIONAL_COMPLETENESS_AXIS,
            kind=ATTESTATION.PROFESSIONAL_COMPLETENESS_ATTESTATION_KIND,
            fingerprints={
                "professional_packages": SHA_A,
                "professional_review_bindings": SHA_B,
                "professional_review_contract": SHA_A,
            },
            reviewers=_professional_reviewers(),
        )
        value.pop("source_fingerprints")
        value["review_contract_fingerprint"] = (
            PANEL._professional_evidence_review_contract_fingerprint()
        )
        value["dependency_material_catalog"] = {
            "adjacent-skill": SHA_A,
        }
        value["review_id"] = review_id
        value["findings"] = [
            _compact_professional_finding_fixture(
                "fresh-skill", mode="fresh", origin_review_id=review_id
            )
        ]
        value["review_cost_input"] = _review_cost_input("full-fresh")
        authority = _compact_professional_authority("fresh-skill")
        finalized = ATTESTATION.finalize_attestation(
            value,
            expected_professional_current_bindings=authority,
        )
        finding = finalized["findings"][0]
        self.assertEqual(
            {
                "origin_review_id",
                "origin_commit",
                "origin_verdict_digest",
            },
            set(finding["provenance"]["origin"]),
        )
        forbidden = {
            "anchor_id", "anchors", "evidence_anchors", "excerpt", "path",
            "start_line", "end_line", "source_line", "source_span",
            "source_phrase", "evidence_anchor_ids", "packet", "capsule",
            "ballot", "origin_decision", "origin_attestation",
        }

        def keys(item: object) -> set[str]:
            if isinstance(item, dict):
                return set(item) | {
                    nested
                    for value in item.values()
                    for nested in keys(value)
                }
            if isinstance(item, list):
                return {nested for value in item for nested in keys(value)}
            return set()

        self.assertFalse(keys(finalized) & forbidden)
        self.assertEqual(
            finalized,
            ATTESTATION.parse_attestation_bytes(
                ATTESTATION.canonical_attestation_bytes(
                    finalized,
                    expected_professional_current_bindings=authority,
                ),
                expected_professional_current_bindings=authority,
            ),
        )

    def test_professional_current_authority_plumbing_rejects_partial_map(self) -> None:
        value = professional_fixture()
        authority = _professional_authority(value)
        self.assertEqual(
            value,
            ATTESTATION.validate_attestation(
                value, expected_professional_current_bindings=authority
            ),
        )
        encoded = ATTESTATION.canonical_attestation_bytes(
            value, expected_professional_current_bindings=authority
        )
        for operation in (
            lambda: ATTESTATION.validate_attestation(value),
            lambda: ATTESTATION.finalize_attestation(value),
            lambda: ATTESTATION.canonical_attestation_bytes(value),
            lambda: ATTESTATION.parse_attestation_bytes(encoded),
        ):
            with self.subTest(operation=operation):
                with self.assertRaisesRegex(
                    ATTESTATION.AttestationError,
                    "current bindings",
                ):
                    operation()
        partial = copy.deepcopy(authority)
        partial.pop(next(iter(partial)))
        with self.assertRaisesRegex(
            ATTESTATION.AttestationError, "coverage is incomplete"
        ):
            ATTESTATION.validate_attestation(
                value, expected_professional_current_bindings=partial
            )
        extra = copy.deepcopy(authority)
        extra["unexpected-skill"] = copy.deepcopy(next(iter(authority.values())))
        with self.assertRaisesRegex(
            ATTESTATION.AttestationError, "coverage is incomplete"
        ):
            ATTESTATION.validate_attestation(
                value, expected_professional_current_bindings=extra
            )

    def test_professional_authority_is_target_local_and_dependency_closed(self) -> None:
        value = professional_fixture()
        authority = _professional_authority(value)
        skill_id = value["findings"][0]["skill_id"]
        target = authority[skill_id]

        self.assertNotIn("candidate_material_fingerprints", target)
        self.assertEqual(
            {"adjacent-skill": SHA_A},
            target["required_candidate_material_bindings"],
        )
        self.assertEqual([], target["reviewer_added_candidate_ids_union"])
        self.assertEqual(
            {}, target["reviewer_added_candidate_material_bindings"]
        )
        self.assertEqual("fixture-selection-v1", target["selection_contract_version"])

        mutations = []
        missing = copy.deepcopy(authority)
        missing[skill_id]["required_candidate_material_bindings"].clear()
        mutations.append(missing)
        for field in (
            "required_candidate_material_bindings",
            "reviewer_added_candidate_material_bindings",
        ):
            extra = copy.deepcopy(authority)
            extra[skill_id][field]["unexpected-skill"] = SHA_A
            mutations.append(extra)
        partial_added = copy.deepcopy(authority)
        partial_added[skill_id]["reviewer_added_candidate_ids_union"] = [
            "reviewer-added-skill"
        ]
        mutations.append(partial_added)
        tampered = copy.deepcopy(authority)
        tampered[skill_id]["required_candidate_material_bindings"][
            "adjacent-skill"
        ] = SHA_B
        mutations.append(tampered)

        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(
                ATTESTATION.AttestationError
            ):
                ATTESTATION.validate_attestation(
                    value,
                    expected_professional_current_bindings=mutation,
                )

    def test_professional_compact_text_bounds_and_old_schema_fail_closed(self) -> None:
        value = professional_fixture(review_mode="full-fresh")
        old_schema = copy.deepcopy(value)
        old_schema["findings"][0]["votes"][0]["reviewer"] = copy.deepcopy(
            _professional_reviewers()[0]
        )
        with self.assertRaises(ATTESTATION.AttestationError):
            ATTESTATION.validate_attestation(
                old_schema,
                expected_professional_current_bindings=(
                    _professional_authority(value)
                ),
            )

        for mutation in (
            lambda vote: vote["proof_limits"].__setitem__(
                "bounded", ["one", "two", "three"]
            ),
            lambda vote: vote["proof_limits"].__setitem__(
                "bounded", ["x" * 257]
            ),
            lambda vote: vote.__setitem__("rationale", "x" * 513),
        ):
            changed = copy.deepcopy(value)
            mutation(changed["findings"][0]["votes"][0])
            authority = _professional_authority(changed)
            with self.assertRaises(ATTESTATION.AttestationError):
                ATTESTATION.finalize_attestation(
                    changed,
                    expected_professional_current_bindings=authority,
                )

        boundary = copy.deepcopy(value)
        vote = boundary["findings"][0]["votes"][0]
        vote["proof_limits"] = {
            "count": 2,
            "digest": SHA_A,
            "bounded": ["a" * 256, "b" * 256],
        }
        vote["rationale"] = "r" * 512
        authority = _professional_authority(boundary)
        authority[boundary["findings"][0]["skill_id"]]["evidence_metrics"][
            "proof_limit_count"
        ] = 4
        boundary["findings"][0]["result"] = {}
        boundary["summary"] = {}
        boundary["verdict"] = ""
        ATTESTATION.finalize_attestation(
            boundary,
            expected_professional_current_bindings=authority,
        )

    def test_professional_authenticated_vote_claims_reject_coordinated_rewrite(
        self,
    ) -> None:
        value = professional_fixture(review_mode="full-fresh")
        authority = _professional_authority(value)

        mutations = (
            lambda vote: vote["criteria"]["ordinary"].__setitem__(
                "generic-knowledge-pollution", "defect-found"
            ),
            lambda vote: vote.__setitem__(
                "rationale", "Coordinated rewritten rationale."
            ),
            lambda vote: vote["proof_limits"]["bounded"].__setitem__(
                0, "Coordinated rewritten proof limit."
            ),
        )
        for mutation in mutations:
            changed = copy.deepcopy(value)
            vote = changed["findings"][0]["votes"][0]
            mutation(vote)
            changed["findings"][0]["result"] = {}
            changed["summary"] = {}
            changed["verdict"] = ""
            with self.subTest(mutation=mutation):
                with self.assertRaises(ATTESTATION.AttestationError):
                    ATTESTATION.finalize_attestation(
                        changed,
                        expected_professional_current_bindings=authority,
                    )

    def test_professional_defect_reason_code_uses_closed_authority(self) -> None:
        value = professional_fixture(review_mode="full-fresh")
        vote = value["findings"][0]["votes"][0]
        vote["criteria"]["ordinary"]["generic-knowledge-pollution"] = (
            "defect-found"
        )
        vote["decision"] = "requires-professional-correction"
        vote["reason_code"] = "invented-correction-reason"
        value["findings"][0]["result"] = {}
        value["summary"] = {}
        value["verdict"] = ""
        authority = _professional_authority(value)
        with self.assertRaisesRegex(
            ATTESTATION.AttestationError, "reason_code"
        ):
            ATTESTATION.finalize_attestation(
                value,
                expected_professional_current_bindings=authority,
            )
    def test_fixed_readability_rehydrates_current_actionability_evidence(self) -> None:
        regression = PANEL._load_professional_regression_validator()
        density, readability, actionability = self._readability_coverage()
        value = readability_fixture()
        bindings = _compact_readability_bindings()
        legacy = regression._missing_axis_result(
            path=ROOT / "config/professionalism-release-review.yaml",
            field_name="readability_review_attestation",
            panel_kind=ATTESTATION.READABILITY_AXIS,
            scope="ai-readability-and-density",
            config_fingerprint=SHA_A,
            current_source_fingerprints={},
            limitations=["Static evidence does not prove runtime behavior."],
            required_density_count=1,
            required_readability_count=1,
            required_actionability_count=1,
        )
        with mock.patch.object(
            regression,
            "_load_fixed_compact_attestation",
            return_value=(
                value,
                {"path": ATTESTATION.READABILITY_ATTESTATION_PATH, "sha256": SHA_A},
            ),
        ):
            applied = regression._apply_fixed_readability_attestation(
                legacy,
                required_density=density,
                required_readability=readability,
                required_actionability=actionability,
                expected_review_contract_fingerprint=SHA_A,
                expected_readability_current_bindings=bindings,
                require_equivalent=False,
            )
        evidence = applied["actionability_dispositions"][0]["evidence"]
        self.assertEqual(
            [{
                "line": 1,
                "source_line": "Define one bounded action.",
                "claim": "Define one bounded action.",
            }],
            evidence,
        )
        compact_json = json.dumps(value, sort_keys=True)
        self.assertNotIn('"evidence"', compact_json)
        self.assertNotIn('"source_line"', compact_json)
        self.assertTrue(applied["decision_complete"])
        self.assertEqual(5, applied["attestation_schema_version"])
        self.assertEqual(2, applied["panel_artifact_schema_version"])

        module_name = "test_productization_evidence_owner"
        spec = importlib.util.spec_from_file_location(
            module_name, SCRIPTS / "validate-productization-assets.py"
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        productization = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(productization)
        errors = productization._readability_axis_errors("fixture.json", applied)
        self.assertFalse(
            [error for error in errors if "actionability_dispositions" in error],
            errors,
        )
        with mock.patch.object(
            regression,
            "_load_fixed_compact_attestation",
            return_value=(
                value,
                {"path": ATTESTATION.READABILITY_ATTESTATION_PATH, "sha256": SHA_A},
            ),
        ):
            with self.assertRaises(ValueError):
                regression._apply_fixed_readability_attestation(
                    legacy,
                    required_density=density,
                    required_readability=readability,
                    required_actionability=actionability + actionability,
                    expected_review_contract_fingerprint=SHA_A,
                    expected_readability_current_bindings=bindings,
                    require_equivalent=False,
                )
            mismatched = copy.deepcopy(bindings)
            mismatched["actionability"]["action-one"]["target"]["skill_id"] = (
                "different-skill"
            )
            with self.assertRaisesRegex(ValueError, "target is stale"):
                regression._apply_fixed_readability_attestation(
                    legacy,
                    required_density=density,
                    required_readability=readability,
                    required_actionability=actionability,
                    expected_review_contract_fingerprint=SHA_A,
                    expected_readability_current_bindings=mismatched,
                    require_equivalent=False,
                )

    def test_fixed_professional_preserves_report_and_panel_schema_versions(
        self,
    ) -> None:
        regression = PANEL._load_professional_regression_validator()
        value, packet = _current_professional_attestation_fixture()
        packet["review_contract_fingerprint"] = value[
            "review_contract_fingerprint"
        ]
        legacy = regression._missing_axis_result(
            path=ROOT / "config/professionalism-release-review.yaml",
            field_name="professional_completeness_review_attestation",
            panel_kind=ATTESTATION.PROFESSIONAL_COMPLETENESS_AXIS,
            scope="professional-skill-packages",
            config_fingerprint=SHA_A,
            current_source_fingerprints={},
            limitations=["Static evidence does not prove runtime behavior."],
            required_target_count=PANEL.PROFESSIONAL_PACKAGE_COUNT,
        )
        with mock.patch.object(
            regression.expert_panel.reviewer_manifest,
            "read_bound_regular_file",
            return_value=mock.Mock(raw=b"{}"),
        ), mock.patch.object(
            regression.expert_panel.panel_attestation,
            "parse_attestation_storage_selector_bytes",
            return_value=value,
        ), mock.patch.object(
            regression.expert_panel,
            "_professional_attestation_bindings_from_state",
            return_value={},
        ), mock.patch.object(
            regression,
            "_load_fixed_compact_attestation",
            return_value=(
                value,
                {
                    "path": ATTESTATION.PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH,
                    "sha256": SHA_A,
                },
            ),
        ), mock.patch.object(
            regression.expert_panel,
            "validate_professional_attestation_current",
        ):
            applied = regression._apply_fixed_professional_attestation(
                legacy,
                current_packet=packet,
                require_equivalent=False,
            )

        self.assertTrue(applied["decision_complete"])
        self.assertEqual(5, applied["attestation_schema_version"])
        self.assertEqual(3, applied["panel_artifact_schema_version"])

    def test_professional_current_rejects_binding_and_conclusion_rewrites(
        self,
    ) -> None:
        value, packet = _current_professional_attestation_fixture()
        PANEL.validate_professional_attestation_current(
            value,
            current_packet=packet,
            authenticated_claims=_professional_claims(value),
        )

        binding_rewrite = copy.deepcopy(value)
        binding_rewrite["findings"][0]["review_binding_fingerprint"] = SHA_B
        with self.assertRaises(PANEL.PanelReviewError):
            PANEL.validate_professional_attestation_current(
                binding_rewrite,
                current_packet=packet,
                authenticated_claims=_professional_claims(value),
            )

        invented = copy.deepcopy(value)
        invented["findings"][0]["votes"][0]["criteria"]["ordinary"][
            "generic-knowledge-pollution"
        ] = "defect-found"
        with self.assertRaises(PANEL.PanelReviewError):
            PANEL.validate_professional_attestation_current(
                invented,
                current_packet=packet,
                authenticated_claims=_professional_claims(value),
            )

    def test_professional_current_ignores_unselected_ranking_churn(self) -> None:
        value, packet = _current_professional_attestation_fixture()
        changed = copy.deepcopy(packet)
        target = next(
            row
            for row in changed["professional_targets"]
            if row["skill_id"] == "carried-skill"
        )
        ranking = target["routing_adjacency"]["full_catalog_ranking"]
        unselected = next(
            row for row in ranking if row["skill_id"] == "unaffected-skill"
        )
        unselected["total_score"] += 1
        target["routing_adjacency"]["full_catalog_ranking_fingerprint"] = _sha(
            ranking
        )

        PANEL.validate_professional_attestation_current(
            value,
            current_packet=changed,
            authenticated_claims=_professional_claims(value),
        )

    def test_explicit_fixed_semantic_application_dispatches_current_complete_evidence(
        self,
    ) -> None:
        compact = semantic_fixture()
        candidates = _semantic_candidates()
        candidates["reference"]["detector_status"] = "candidate"
        candidates["reference"]["owner"] = candidates["reference"][
            "skill_owner"
        ]
        expected_bindings = _semantic_expected_bindings(candidates)
        detector_contracts = {
            "root": source_support.AUDIT._root_semantic_detector_contract(),
            "reference": (
                source_support.AUDIT._reference_semantic_detector_contract()
            ),
        }
        for finding in compact["findings"]:
            authority = expected_bindings[finding["target_id"]]
            finding["candidate_binding_fingerprint"] = authority[
                "candidate_binding_fingerprint"
            ]

        def semantic(candidate: dict, axis: str) -> dict:
            detector_contract = copy.deepcopy(detector_contracts[axis])
            winner = next(
                row["result"]["winning_disposition"]
                for row in compact["findings"]
                if row["axis"] == axis
            )
            entry = {
                key: copy.deepcopy(candidate[key])
                for key in (
                    "candidate_id",
                    "finding",
                    "path",
                    "fingerprint",
                    "skill_owner",
                )
            }
            entry["disposition"] = winner
            if axis == "root":
                entry.update(
                    {
                        "document_part": candidate["document_part"],
                        "priority": candidate["priority"],
                        "evidence": {
                            "occurrence_fingerprint": candidate[
                                "occurrence_fingerprint"
                            ],
                            "context_fingerprint": candidate[
                                "context_fingerprint"
                            ],
                        },
                    }
                )
            else:
                entry["evidence"] = {
                    "fingerprint": candidate["evidence_fingerprint"],
                    "content_fingerprint": candidate["content_fingerprint"],
                }
            return {
                "schema_version": 6,
                "finding_families": [],
                "limitations": [],
                "detector_contract": detector_contract,
                "candidates": [copy.deepcopy(candidate)],
                "disposition_contract": {"entries": [entry]},
            }

        audit = {
            "schema_version": 9,
            "thresholds": {},
            "root_content": {
                "source_fingerprint": SHA_B,
                "semantic_advisories": semantic(candidates["root"], "root"),
            },
            "reference_content": {
                "preface_contract": {"source_fingerprint": SHA_C},
                "semantic_advisories": semantic(
                    candidates["reference"], "reference"
                ),
            },
        }
        review_audit = copy.deepcopy(audit)
        for key in ("root_content", "reference_content"):
            review_audit[key]["semantic_advisories"][
                "disposition_contract"
            ]["entries"] = []
        packet = PANEL.prepare_semantic_disposition_packet(
            audit=review_audit,
            review_id=compact["review_id"],
            created_on=compact["decided_on"],
        )
        compact["source_fingerprints"] = packet["source_fingerprints"]
        compact["review_contract_fingerprint"] = _sha(packet["panel_contract"])
        packet_bindings = PANEL._semantic_candidate_authorities(packet)
        compact = ATTESTATION.finalize_attestation(
            compact,
            expected_semantic_current_bindings=packet_bindings,
        )
        encoded = ATTESTATION.canonical_attestation_bytes(
            compact,
            expected_path=ATTESTATION.SEMANTIC_DISPOSITION_ATTESTATION_PATH,
            expected_semantic_current_bindings=packet_bindings,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixed = root / ATTESTATION.SEMANTIC_DISPOSITION_ATTESTATION_PATH
            fixed.parent.mkdir(parents=True)
            fixed.write_bytes(encoded)
            with mock.patch.object(PANEL, "ROOT", root):
                result = PANEL.validate_semantic_decision_application(audit)
                self.assertEqual("current", result["status"])
                self.assertEqual(2, result["target_count"])
                self.assertEqual(2, result["applied_count"])

                rewrite = copy.deepcopy(compact)
                rewrite_row = next(
                    row for row in rewrite["findings"] if row["axis"] == "root"
                )
                for vote in rewrite_row["votes"]:
                    vote["disposition"] = "rewrite"
                rewrite = ATTESTATION.finalize_attestation(
                    rewrite,
                    expected_semantic_current_bindings=packet_bindings,
                )
                rewrite_bytes = ATTESTATION.canonical_attestation_bytes(
                    rewrite,
                    expected_path=(
                        ATTESTATION.SEMANTIC_DISPOSITION_ATTESTATION_PATH
                    ),
                    expected_semantic_current_bindings=packet_bindings,
                )
                applied_rewrite_audit = copy.deepcopy(audit)
                root_semantic = applied_rewrite_audit["root_content"][
                    "semantic_advisories"
                ]
                root_semantic["candidates"] = []
                root_semantic["disposition_contract"]["entries"] = []
                fixed.write_bytes(rewrite_bytes)
                rewrite_result = PANEL.validate_semantic_decision_application(
                    applied_rewrite_audit
                )
                self.assertEqual("current", rewrite_result["status"])
                self.assertEqual(1, rewrite_result["applied_count"])
                self.assertEqual(
                    1, rewrite_result["completed_rewrite_count"]
                )

                fixed.write_bytes(encoded)
                with self.assertRaises(PANEL.PanelReviewError):
                    PANEL.validate_semantic_decision_application(
                        applied_rewrite_audit
                    )

                one_sided = copy.deepcopy(applied_rewrite_audit)
                one_sided["root_content"]["semantic_advisories"][
                    "disposition_contract"
                ]["entries"] = copy.deepcopy(
                    audit["root_content"]["semantic_advisories"][
                        "disposition_contract"
                    ]["entries"]
                )
                fixed.write_bytes(rewrite_bytes)
                with self.assertRaises(PANEL.PanelReviewError):
                    PANEL.validate_semantic_decision_application(one_sided)

                tampered_rewrite = copy.deepcopy(rewrite)
                rewrite_target = next(
                    row
                    for row in tampered_rewrite["findings"]
                    if row["axis"] == "root"
                )
                rewrite_target["candidate_binding_fingerprint"] = SHA_A
                tampered_rewrite_bytes = (
                    json.dumps(
                        tampered_rewrite,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                    + b"\n"
                )
                fixed.write_bytes(tampered_rewrite_bytes)
                with self.assertRaises(PANEL.PanelReviewError):
                    PANEL.validate_semantic_decision_application(
                        applied_rewrite_audit
                    )

                for axis, section, field in (
                    ("root", "root_content", "fingerprint"),
                    (
                        "reference",
                        "reference_content",
                        "content_fingerprint",
                    ),
                ):
                    stale = copy.deepcopy(audit)
                    stale[section]["semantic_advisories"]["candidates"][0][
                        field
                    ] = "0" * 64
                    with self.subTest(axis=axis), self.assertRaisesRegex(
                        PANEL.PanelReviewError,
                        "stale|invalid|match exactly one current authority",
                    ):
                        PANEL.validate_semantic_decision_application(stale)

                incomplete = copy.deepcopy(compact)
                incomplete["findings"].pop()
                incomplete_contract = PANEL._semantic_panel_contract(
                    reference_target_count=sum(
                        row["axis"] == "reference"
                        for row in incomplete["findings"]
                    ),
                    root_target_count=sum(
                        row["axis"] == "root"
                        for row in incomplete["findings"]
                    ),
                )
                incomplete["review_contract_fingerprint"] = _sha(
                    incomplete_contract
                )
                incomplete_bindings = {
                    row["target_id"]: packet_bindings[row["target_id"]]
                    for row in incomplete["findings"]
                }
                incomplete = ATTESTATION.finalize_attestation(
                    incomplete,
                    expected_semantic_current_bindings=incomplete_bindings,
                )
                incomplete_bytes = ATTESTATION.canonical_attestation_bytes(
                    incomplete,
                    expected_path=(
                        ATTESTATION.SEMANTIC_DISPOSITION_ATTESTATION_PATH
                    ),
                    expected_semantic_current_bindings=incomplete_bindings,
                )
                fixed.write_bytes(incomplete_bytes)
                with self.assertRaisesRegex(
                    PANEL.PanelReviewError,
                    "omits a current candidate",
                ):
                    PANEL.validate_semantic_decision_application(audit)

                tampered = copy.deepcopy(compact)
                tampered["findings"][0]["result"][
                    "winning_disposition"
                ] = "rewrite"
                tampered_bytes = (
                    json.dumps(
                        tampered,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                    + b"\n"
                )
                fixed.write_bytes(tampered_bytes)
                with self.assertRaises(PANEL.PanelReviewError):
                    PANEL.validate_semantic_decision_application(audit)

    def test_professional_review_cost_contract_covers_three_partition_modes(self) -> None:
        cases = (
            (professional_fixture(review_mode="full-fresh"), 2, 0, "bootstrap-full-review"),
            (professional_fixture(), 1, 1, "incremental-reduced-input"),
            (professional_fixture(all_carry=True), 0, 1, "all-carry-zero-input"),
        )
        for value, fresh, carried, status in cases:
            cost = value["summary"]["review_cost"]
            with self.subTest(status=status):
                self.assertEqual(
                    ATTESTATION.PROFESSIONAL_REVIEW_COST_FIELDS, set(cost)
                )
                self.assertEqual(3 * fresh, cost["fresh_vote_count"])
                self.assertEqual(
                    3 * carried, cost["carried_forward_vote_count"]
                )
                self.assertEqual(3 * (fresh + carried), cost["effective_vote_count"])
                self.assertEqual(
                    30 * fresh, cost["fresh_criterion_result_count"]
                )
                self.assertEqual(
                    30 * carried, cost["carried_forward_criterion_result_count"]
                )
                self.assertEqual(
                    30 * (fresh + carried),
                    cost["effective_criterion_result_count"],
                )
                self.assertEqual(status, cost["policy_status"])
                self.assertEqual(
                    ATTESTATION.PROFESSIONAL_REVIEW_COST_LIMITATIONS,
                    cost["limitations"],
                )
        carry_cost = cases[-1][0]["summary"]["review_cost"]
        for field in (
            "canonical_capsule_input_bytes_proxy",
            "required_only_capsule_input_bytes_proxy",
            "required_only_source_material_input_bytes_proxy",
            "source_material_input_bytes_proxy",
            "reviewer_added_source_material_input_bytes_proxy",
            "reviewer_added_relationship_evidence_metadata_overhead_bytes_proxy",
            "reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm",
            "reviewer_added_request_count",
            "reviewer_added_unique_relationship_count",
            "maximum_reviewer_added_unique_union_to_required_ratio_ppm",
            "input_ratio_ppm",
            "required_only_input_ratio_ppm",
            "source_material_coverage_ratio_ppm",
        ):
            self.assertEqual(0, carry_cost[field])

    def test_professional_all_carry_preserves_projection_origin_commit(
        self,
    ) -> None:
        value = professional_fixture(all_carry=True)
        origin = copy.deepcopy(
            value["findings"][0]["provenance"]["origin"]
        )
        authority = _professional_authority(value)
        raw = ATTESTATION.canonical_attestation_bytes(
            value,
            expected_professional_current_bindings=authority,
        )
        parsed = ATTESTATION.parse_attestation_bytes(
            raw,
            expected_professional_current_bindings=authority,
        )
        self.assertEqual(
            origin,
            parsed["findings"][0]["provenance"]["origin"],
        )

    def test_professional_review_cost_policy_matches_core_and_exact_ratios(self) -> None:
        contracts = json.loads(
            (ROOT / "src/control-model/core-contracts.json").read_text(
                encoding="utf-8"
            )
        )
        policy = contracts["final_goal_contract"][
            "professional_review_cost_fixtures"
        ]["formal_round_policy"]
        self.assertEqual(
            policy, ATTESTATION.PROFESSIONAL_REVIEW_FORMAL_ROUND_POLICY
        )
        self.assertEqual(
            _sha(policy), ATTESTATION.PROFESSIONAL_REVIEW_FORMAL_ROUND_POLICY_FINGERPRINT
        )
        cost = professional_fixture()["summary"]["review_cost"]
        self.assertEqual(
            cost["canonical_capsule_input_bytes_proxy"] * 1_000_000
            // cost["full_rereview_deduplicated_capsule_input_bytes_proxy"],
            cost["input_ratio_ppm"],
        )
        self.assertEqual(
            50_000,
            cost[
                "reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm"
            ],
        )
        self.assertEqual(8, cost["plan_lineage_depth"])

    def test_professional_review_cost_closed_and_policy_mutations_fail(self) -> None:
        mutations = []
        missing = professional_fixture()
        missing["review_cost_input"].pop("source_material_input_bytes_proxy")
        mutations.append(missing)
        extra = professional_fixture()
        extra["review_cost_input"]["extra"] = 0
        mutations.append(extra)
        stale_policy = professional_fixture()
        stale_policy["review_cost_input"]["formal_round_policy_fingerprint"] = SHA_A
        mutations.append(stale_policy)
        bad_lineage = professional_fixture()
        bad_lineage["review_cost_input"]["plan_lineage_depth"] = 9
        mutations.append(bad_lineage)
        bad_status = professional_fixture()
        bad_status["review_cost_input"]["policy_status"] = "all-carry-zero-input"
        mutations.append(bad_status)
        bad_decomposition = professional_fixture()
        bad_decomposition["review_cost_input"][
            "source_material_input_bytes_proxy"
        ] = 199
        mutations.append(bad_decomposition)
        overhead_over_boundary = professional_fixture()
        overhead_over_boundary["review_cost_input"][
            "canonical_capsule_input_bytes_proxy"
        ] += 1
        mutations.append(overhead_over_boundary)
        union_over_boundary = professional_fixture()
        union_over_boundary["review_cost_input"][
            "maximum_reviewer_added_unique_union_to_required_ratio_ppm"
        ] = 1_000_001
        mutations.append(union_over_boundary)
        stale_result = professional_fixture()
        stale_result["summary"]["review_cost"]["input_ratio_ppm"] += 1
        mutations.append(stale_result)
        for value in mutations:
            with self.assertRaises(ATTESTATION.AttestationError):
                ATTESTATION.validate_attestation(value)

        other_axis = readability_fixture()
        other_axis["review_cost_input"] = _review_cost_input("full-fresh")
        with self.assertRaises(ATTESTATION.AttestationError):
            ATTESTATION.validate_attestation(other_axis)

    def test_semantic_uses_authoritative_root_and_reference_evidence_projection(self) -> None:
        value = semantic_fixture()
        for row in value["findings"]:
            self.assertEqual(
                {
                    "target_id",
                    "axis",
                    "candidate_binding_fingerprint",
                    "votes",
                    "result",
                },
                set(row),
            )
        encoded = json.dumps(value, sort_keys=True)
        for forbidden in ("candidate", "occurrences", "preview"):
            self.assertNotIn(f'"{forbidden}"', encoded)

        reduced = semantic_fixture()
        reduced["findings"][0]["candidate_binding_fingerprint"] = SHA_A
        with self.assertRaises(ATTESTATION.AttestationError):
            ATTESTATION.validate_attestation(
                reduced,
                expected_semantic_current_bindings=_semantic_expected_bindings(),
            )

    def test_semantic_every_validation_surface_requires_exact_current_authority(
        self,
    ) -> None:
        value = semantic_fixture()
        authorities = _semantic_expected_bindings()
        encoded = ATTESTATION.canonical_attestation_bytes(
            value,
            expected_semantic_current_bindings=authorities,
        )
        for operation in (
            lambda: ATTESTATION.validate_attestation(value),
            lambda: ATTESTATION.finalize_attestation(value),
            lambda: ATTESTATION.canonical_attestation_bytes(value),
            lambda: ATTESTATION.parse_attestation_bytes(encoded),
        ):
            with self.subTest(operation=operation):
                with self.assertRaises(ATTESTATION.AttestationError):
                    operation()

        partial = copy.deepcopy(authorities)
        partial.pop(next(iter(partial)))
        extra = copy.deepcopy(authorities)
        extra[f"root:{SHA_A}"] = copy.deepcopy(next(iter(authorities.values())))
        for expected in (partial, extra):
            with self.assertRaises(ATTESTATION.AttestationError):
                ATTESTATION.validate_attestation(
                    value,
                    expected_semantic_current_bindings=expected,
                )

        tampered_authority = copy.deepcopy(authorities)
        root_id = next(key for key in tampered_authority if key.startswith("root:"))
        tampered_authority[root_id]["candidate"]["context_fingerprint"] = SHA_C
        with self.assertRaises(ATTESTATION.AttestationError):
            ATTESTATION.validate_attestation(
                value,
                expected_semantic_current_bindings=tampered_authority,
            )

        changed_candidates = _semantic_candidates()
        changed_candidates["root"]["context_fingerprint"] = SHA_C
        coordinated = _semantic_expected_bindings(changed_candidates)
        with self.assertRaises(ATTESTATION.AttestationError):
            ATTESTATION.validate_attestation(
                value,
                expected_semantic_current_bindings=coordinated,
            )

    def test_semantic_source_shape_accepts_only_current_or_exact_legacy_contracts(
        self,
    ) -> None:
        current = semantic_fixture()
        authorities = _semantic_expected_bindings()
        self.assertEqual(
            "current",
            ATTESTATION.semantic_source_fingerprint_shape(
                current["source_fingerprints"]
            ),
        )
        ATTESTATION.validate_attestation(
            current,
            expected_semantic_current_bindings=authorities,
        )

        legacy = copy.deepcopy(current)
        legacy["source_fingerprints"] = {
            key: _sha(key)
            for key in (
                "audit",
                "reference_candidates",
                "reference_detector",
                "reference_groups",
                "reference_source",
                "root_candidates",
                "root_context",
                "root_detector",
                "root_source",
            )
        }
        self.assertEqual(
            "legacy",
            ATTESTATION.semantic_source_fingerprint_shape(
                legacy["source_fingerprints"]
            ),
        )
        with self.assertRaisesRegex(ATTESTATION.AttestationError, "stale"):
            ATTESTATION.validate_attestation(
                legacy,
                expected_semantic_current_bindings=authorities,
            )

        malformed = copy.deepcopy(legacy)
        malformed["source_fingerprints"].pop("audit")
        with self.assertRaisesRegex(
            ATTESTATION.AttestationError,
            "source fingerprint fields are not closed",
        ):
            ATTESTATION.validate_attestation(
                malformed,
                expected_semantic_current_bindings=authorities,
            )

    def test_semantic_adapter_compacts_noncanonical_source_preview(self) -> None:
        reviewers = _basic_reviewers()
        candidate_id = _sha("semantic-compact-root-candidate")
        candidate = {
            "candidate_id": candidate_id,
            "finding": "One current Root candidate.",
            "path": "src/foundation/example/SKILL.md",
            "owner": "example",
            "skill_owner": "example",
            "fingerprint": _sha("semantic-compact-root-finding"),
            "document_part": "body",
            "occurrence_fingerprint": _sha("semantic-compact-root-occurrence"),
            "context_fingerprint": _sha("semantic-compact-root-context"),
            "priority": "P1",
            "occurrences": [
                {
                    "path": "src/foundation/example/SKILL.md",
                    "lines": {"start": 7, "end": 7},
                    "preview": "Source-owned preview keeps trailing whitespace. ",
                    "context_fingerprint": _sha("semantic-compact-root-context"),
                }
            ],
        }
        evidence = ATTESTATION.semantic_candidate_review_evidence(
            axis="root", candidate=candidate
        )
        candidate_binding_fingerprint = ATTESTATION.semantic_candidate_fingerprints(
            axis="root", candidate=candidate
        )["candidate_binding_fingerprint"]
        votes = [
            {
                "voter_id": reviewer["voter_id"],
                "disposition": "valid-contextual-rule",
                "rationale": "The current Root rule is contextually valid.",
                "authority_or_condition": "The packet-bound source owns the rule.",
                "decision_owner": "source-owner",
                "mitigation": "Re-review when the current binding changes.",
                "review_after": None,
            }
            for reviewer in reviewers
        ]
        target_id = f"root:{candidate_id}"
        packet = {
            "panel_contract": {},
            "semantic_targets": [
                {
                    "target_id": target_id,
                    "axis": "root",
                    "candidate": candidate,
                    "candidate_binding_fingerprint": candidate_binding_fingerprint,
                }
            ],
        }
        record = {
            "review_id": "semantic-compact-review",
            "decided_on": "2026-08-10",
            "source_fingerprints": {
                key: _sha(key)
                for key in (
                    "reference_candidate_manifest",
                    "reference_detector_contract",
                    "root_candidate_manifest",
                    "root_detector_contract",
                )
            },
            "voters": reviewers,
            "semantic_decisions": [
                {
                    "target_id": target_id,
                    "axis": "root",
                    "candidate_binding_fingerprint": candidate_binding_fingerprint,
                    "ballot_rationales": votes,
                }
            ],
        }
        with mock.patch.object(
            PANEL, "validate_decision_record", return_value=record
        ), mock.patch.object(
            PANEL, "_decision_packet_and_ballots", return_value=(Path("packet.json"), packet, [])
        ), mock.patch.object(
            PANEL, "validate_semantic_packet_current", return_value=packet
        ):
            compact = PANEL._semantic_attestation_from_decision(
                record,
                decision_path=Path("decision.json"),
                audit={},
            )

        finding = compact["findings"][0]
        self.assertEqual(
            {
                "target_id",
                "axis",
                "candidate_binding_fingerprint",
                "votes",
                "result",
            },
            set(finding),
        )
        self.assertEqual(
            candidate_binding_fingerprint,
            finding["candidate_binding_fingerprint"],
        )
        serialized = json.dumps(compact, ensure_ascii=False)
        for forbidden in ("candidate", "occurrences", "preview"):
            self.assertNotIn(f'"{forbidden}"', serialized)
        self.assertNotIn("Source-owned preview", serialized)
        self.assertNotIn("src/foundation/example/SKILL.md", serialized)

    def test_semantic_same_id_current_binding_drift_fails_for_both_axes(self) -> None:
        value = semantic_fixture()
        for axis, field in (
            ("root", "context_fingerprint"),
            ("reference", "content_fingerprint"),
        ):
            current_candidates = _semantic_candidates()
            current_candidates[axis][field] = SHA_C
            changed_current = _semantic_expected_bindings(current_candidates)
            with self.subTest(axis=axis):
                with self.assertRaises(ATTESTATION.AttestationError):
                    ATTESTATION.validate_attestation(
                        value,
                        expected_semantic_current_bindings=changed_current,
                    )

    def test_carried_package_binding_cannot_drift_or_move_together(self) -> None:
        value = professional_fixture(all_carry=True)
        origin = value["findings"][0]["provenance"]["origin"]
        origin["package_fingerprint"] = SHA_C
        origin["origin_fingerprint"] = ATTESTATION.professional_origin_fingerprint(
            origin
        )
        with self.assertRaises(ATTESTATION.AttestationError):
            ATTESTATION.validate_attestation(value)

        moved_together = professional_fixture(all_carry=True)
        row = moved_together["findings"][0]
        row["package_fingerprint"] = SHA_C
        row["provenance"]["origin"]["package_fingerprint"] = SHA_C
        row["provenance"]["origin"]["origin_fingerprint"] = (
            ATTESTATION.professional_origin_fingerprint(row["provenance"]["origin"])
        )
        with self.assertRaises(ATTESTATION.AttestationError):
            ATTESTATION.validate_attestation(
                moved_together,
                expected_professional_current_bindings=(
                    _professional_authority(value)
                ),
            )

    def test_all_axes_roundtrip_with_derived_votes_and_summaries(self) -> None:
        fixtures = {
            ATTESTATION.READABILITY_ATTESTATION_PATH: readability_fixture(),
            ATTESTATION.PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH:
                professional_fixture(),
            ATTESTATION.SEMANTIC_DISPOSITION_ATTESTATION_PATH: semantic_fixture(),
        }
        for path, value in fixtures.items():
            with self.subTest(path=path):
                validation = (
                    {
                        "expected_semantic_current_bindings": (
                            _semantic_expected_bindings()
                        )
                    }
                    if value["axis"] == ATTESTATION.SEMANTIC_DISPOSITION_AXIS
                    else (
                        {
                            "expected_source_fingerprints": value[
                                "source_fingerprints"
                            ],
                            "expected_readability_current_bindings": (
                                _compact_readability_bindings()
                            )
                        }
                        if value["axis"] == ATTESTATION.READABILITY_AXIS
                        else {
                            "expected_professional_current_bindings": (
                                _professional_authority(value)
                            )
                        }
                    )
                )
                first = ATTESTATION.canonical_attestation_bytes(
                    value, expected_path=path, **validation
                )
                parsed = ATTESTATION.parse_attestation_bytes(
                    first, expected_path=path, **validation
                )
                self.assertEqual(value, parsed)
                self.assertEqual(
                    first,
                    ATTESTATION.canonical_attestation_bytes(
                        parsed, **validation
                    ),
                )

    def test_readability_and_semantic_require_three_independent_raw_votes(self) -> None:
        readability = readability_fixture()
        self.assertEqual(
            {
                "accepted-current-actionability": 1,
                "detector-false-positive": 0,
                "rewrite-required": 0,
            },
            readability["summary"]["actionability"],
        )
        semantic = semantic_fixture()
        self.assertEqual(
            3, len(semantic["findings"][0]["votes"])
        )
        for value, votes in (
            (readability, readability["findings"][0]["votes"]),
            (semantic, semantic["findings"][0]["votes"]),
        ):
            votes.pop()
            with self.assertRaises(ATTESTATION.AttestationError):
                ATTESTATION.validate_attestation(
                    value,
                    **(
                        {
                            "expected_semantic_current_bindings": (
                                _semantic_expected_bindings()
                            )
                        }
                        if value["axis"]
                        == ATTESTATION.SEMANTIC_DISPOSITION_AXIS
                        else {
                            "expected_readability_current_bindings": (
                                _compact_readability_bindings()
                            )
                        }
                    ),
                )

    def test_professional_preserves_evidence_classes_and_derives_formal_summary(self) -> None:
        value = professional_fixture()
        target = value["findings"][0]
        vote = target["votes"][0]
        self.assertEqual(
            {
                "criteria",
                "decision",
                "examined_adjacent_candidates",
                "examined_failure_modes",
                "examined_omission_candidates",
                "proof_limits",
                "rationale",
                "reason_code",
                "reviewer",
                "review_evidence_fingerprint",
            },
            set(vote),
        )
        self.assertEqual(2, value["summary"]["partition"]["effective_target_count"])
        self.assertEqual(30, target["result"]["evidence_metrics"]["criterion_result_count"])
        self.assertEqual(
            "accepted-current-professional-completeness",
            target["result"]["final_disposition"],
        )
        self.assertEqual(3, value["summary"]["review_cost"]["fresh_vote_count"])
        self.assertEqual(
            3, value["summary"]["review_cost"]["carried_forward_vote_count"]
        )

    def test_all_carry_has_zero_fresh_reviewers_and_duplicate_roles_are_allowed(self) -> None:
        all_carry = professional_fixture(all_carry=True)
        self.assertEqual([], all_carry["reviewers"])
        self.assertEqual(0, all_carry["summary"]["qualification"]["fresh_reviewer_pool_size"])
        self.assertEqual(
            3,
            all_carry["summary"]["review_cost"][
                "carried_forward_vote_count"
            ],
        )
        mixed = professional_fixture()
        self.assertEqual(
            1, len({reviewer["role"] for reviewer in mixed["reviewers"]})
        )
        ATTESTATION.validate_attestation(
            mixed,
            expected_professional_current_bindings=(
                _professional_authority(mixed)
            ),
        )

    def test_professional_compact_authority_rejects_tampered_vote_surface(self) -> None:
        mutations = (
            ("reviewer", lambda vote: vote.__setitem__("reviewer", "forged-reviewer")),
            ("review fingerprint", lambda vote: vote.__setitem__("review_evidence_fingerprint", SHA_A)),
            ("ordinary criterion", lambda vote: vote["criteria"]["ordinary"].__setitem__("generic-knowledge-pollution", "defect-found")),
            ("critical set", lambda vote: vote["criteria"]["domain_critical_defects"].append("professional-correctness")),
            ("failure count", lambda vote: vote["examined_failure_modes"].__setitem__("count", 2)),
            ("adjacency count", lambda vote: vote["examined_adjacent_candidates"].__setitem__("count", 2)),
            (
                "reviewer-added IDs",
                lambda vote: vote["examined_adjacent_candidates"][
                    "reviewer_added_candidate_ids"
                ].append("forged-candidate"),
            ),
            ("rationale", lambda vote: vote.__setitem__("rationale", "Changed compact rationale.")),
        )
        for label, mutate in mutations:
            value = professional_fixture()
            authority = _professional_authority(value)
            vote = value["findings"][0]["votes"][0]
            mutate(vote)
            with self.subTest(label=label):
                with self.assertRaises(ATTESTATION.AttestationError):
                    ATTESTATION.validate_attestation(
                        value,
                        expected_professional_current_bindings=authority,
                    )

    def test_compact_origin_projects_authoritative_reviewer_added_ids(
        self,
    ) -> None:
        value = professional_fixture()
        finding = value["findings"][0]
        vote = finding["votes"][0]
        adjacency = vote["examined_adjacent_candidates"]
        adjacency["count"] += 1
        adjacency["reviewer_added_candidate_ids"] = ["reviewer-added-skill"]
        finding["dependency_ids"].append("reviewer-added-skill")
        value["dependency_material_catalog"]["reviewer-added-skill"] = SHA_C
        authority = _professional_authority(value)
        metrics = authority[finding["skill_id"]]["evidence_metrics"]
        metrics["examined_adjacency_count"] += 1
        metrics["reviewer_added_adjacency_count"] += 1
        finalized = ATTESTATION.finalize_attestation(
            value,
            expected_professional_current_bindings=authority,
        )

        changed_dependency = copy.deepcopy(authority)
        changed_dependency[finding["skill_id"]][
            "reviewer_added_candidate_material_bindings"
        ]["reviewer-added-skill"] = SHA_A
        with self.assertRaises(ATTESTATION.AttestationError):
            ATTESTATION.validate_attestation(
                finalized,
                expected_professional_current_bindings=changed_dependency,
            )

        projected = PANEL._professional_attestation_origin_row(
            finalized["findings"][0]
        )

        self.assertEqual(
            [
                {
                    "voter_id": vote["reviewer"],
                    "candidates": [
                        {
                            "skill_id": "reviewer-added-skill",
                            "review_origin": "reviewer-added",
                        }
                    ],
                }
            ],
            projected["reviewer_added_adjacency_reviews"],
        )

    def test_every_stored_digest_is_recomputed_or_currentness_compared(self) -> None:
        cases: list[tuple[dict, dict]] = []
        readability = readability_fixture()
        readability["findings"][1]["finding_reviews"][0]["source_fingerprint"] = SHA_A
        cases.append(
            (readability, {"expected_readability_current_bindings": _compact_readability_bindings()})
        )
        semantic = semantic_fixture()
        semantic["findings"][0]["candidate_binding_fingerprint"] = SHA_A
        cases.append(
            (semantic, {"expected_semantic_current_bindings": _semantic_expected_bindings()})
        )
        for mutation in (
            lambda value: value["findings"][0]["votes"][0].__setitem__(
                "review_evidence_fingerprint", SHA_A
            ),
            lambda value: value["findings"][0].__setitem__(
                "review_unit_binding", SHA_A
            ),
            lambda value: value["dependency_material_catalog"].__setitem__(
                "adjacent-skill", SHA_B
            ),
            lambda value: value["findings"][0]["provenance"]["origin"].__setitem__(
                "origin_verdict_digest", SHA_A
            ),
        ):
            professional = professional_fixture()
            authority = _professional_authority(professional)
            mutation(professional)
            cases.append(
                (
                    professional,
                    {"expected_professional_current_bindings": authority},
                )
            )
        for value, validation in cases:
            with self.assertRaises(ATTESTATION.AttestationError):
                ATTESTATION.validate_attestation(value, **validation)

        value = professional_fixture()
        authority = _professional_authority(value)
        with self.assertRaises(ATTESTATION.AttestationError):
            ATTESTATION.validate_attestation(
                value,
                expected_source_fingerprints={"professional_packages": SHA_C},
                expected_professional_current_bindings=authority,
            )
        with self.assertRaises(ATTESTATION.AttestationError):
            ATTESTATION.validate_attestation(
                value,
                expected_review_contract_fingerprint=SHA_B,
                expected_professional_current_bindings=authority,
            )

    def test_professional_identity_qualification_and_carry_mutations_fail(self) -> None:
        values: list[tuple[dict, dict]] = []
        duplicate_voter = professional_fixture()
        authority = _professional_authority(duplicate_voter)
        votes = duplicate_voter["findings"][0]["votes"]
        votes[1]["reviewer"] = votes[0]["reviewer"]
        values.append((duplicate_voter, authority))
        duplicate_agent = professional_fixture()
        authority = _professional_authority(duplicate_agent)
        duplicate_agent["reviewers"][1]["agent_id"] = duplicate_agent["reviewers"][0]["agent_id"]
        values.append((duplicate_agent, authority))
        stale_binding = professional_fixture()
        authority = _professional_authority(stale_binding)
        stale_binding["findings"][0]["review_binding_fingerprint"] = SHA_A
        values.append((stale_binding, authority))
        stale_origin = professional_fixture()
        authority = _professional_authority(stale_origin)
        stale_origin["findings"][0]["provenance"]["origin"]["origin_commit"] = "e" * 40
        values.append((stale_origin, authority))
        fresh_pool_on_all_carry = professional_fixture(all_carry=True)
        authority = _professional_authority(fresh_pool_on_all_carry)
        fresh_pool_on_all_carry["reviewers"] = _professional_reviewers()
        values.append((fresh_pool_on_all_carry, authority))
        for value, authority in values:
            with self.assertRaises(ATTESTATION.AttestationError):
                ATTESTATION.validate_attestation(
                    value,
                    expected_professional_current_bindings=authority,
                )

    def test_representative_189_package_full_fresh_fixture_fits(self) -> None:
        value = professional_fixture(review_mode="full-fresh")
        template = value["findings"][1]
        value["findings"] = [
            _compact_professional_finding_fixture(
                f"skill-{index:03d}",
                mode="fresh",
                origin_review_id=value["review_id"],
            )
            for index in range(189)
        ]
        value["review_cost_input"] = _review_cost_input("full-fresh")
        authority = _professional_authority(value)
        value = ATTESTATION.finalize_attestation(
            value, expected_professional_current_bindings=authority
        )
        encoded = ATTESTATION.canonical_attestation_bytes(
            value, expected_professional_current_bindings=authority
        )
        self.assertEqual(189, value["summary"]["partition"]["effective_target_count"])
        self.assertLessEqual(len(encoded), 1_006_846)
        self.assertGreater(len(encoded), 0)
        self.assertIsNotNone(template)

    def test_exact_four_mib_limit_noncanonical_and_read_only_failure(self) -> None:
        value = readability_fixture()
        validation = {
            "expected_source_fingerprints": value["source_fingerprints"],
            "expected_readability_current_bindings": (
                _compact_readability_bindings()
            )
        }
        encoded = ATTESTATION.canonical_attestation_bytes(value, **validation)
        value["rationale"][0] += "x" * (
            ATTESTATION.MAX_ATTESTATION_BYTES - len(encoded)
        )
        exact = ATTESTATION.canonical_attestation_bytes(value, **validation)
        self.assertEqual(ATTESTATION.MAX_ATTESTATION_BYTES, len(exact))
        self.assertEqual(
            value, ATTESTATION.parse_attestation_bytes(exact, **validation)
        )
        value["rationale"][0] += "x"
        before = copy.deepcopy(value)
        with tempfile.TemporaryDirectory() as directory:
            sentinel = Path(directory) / "sentinel"
            sentinel.write_text("unchanged", encoding="utf-8")
            with self.assertRaises(ATTESTATION.AttestationError):
                ATTESTATION.canonical_attestation_bytes(value, **validation)
            self.assertEqual("unchanged", sentinel.read_text(encoding="utf-8"))
        self.assertEqual(before, value)

    def test_fixed_paths_closed_fields_and_forbidden_external_evidence_paths(self) -> None:
        self.assertEqual(
            {
                "readability": "evals/expert-panel/readability.json",
                "professional-completeness": "evals/expert-panel/professional-completeness.json",
                "semantic-disposition": "evals/expert-panel/semantic-disposition.json",
            },
            ATTESTATION.ATTESTATION_PATHS,
        )
        for reference in (
            ".rd-skills/expert-panel/run/evidence.json",
            "packet.json",
            "ballots/reviewer.json",
            "capsules/reviewer.json",
            "predecessor decision evidence",
            "evals/expert-panel/old/panel/decision.json",
        ):
            value = semantic_fixture()
            value["findings"][0]["votes"][0]["rationale"] = reference
            with self.assertRaises(ATTESTATION.AttestationError):
                ATTESTATION.validate_attestation(
                    value,
                    expected_semantic_current_bindings=(
                        _semantic_expected_bindings()
                    ),
                )
        extra = readability_fixture()
        extra["findings"][0]["extra"] = True
        with self.assertRaises(ATTESTATION.AttestationError):
            ATTESTATION.validate_attestation(extra)

    def test_current_compact_attestation_metadata_stays_within_bound(self) -> None:
        fixtures = (
            (
                readability_fixture(),
                {
                    "expected_readability_current_bindings": (
                        _compact_readability_bindings()
                    )
                },
            ),
            (
                professional_fixture(),
                {
                    "expected_professional_current_bindings": (
                        _professional_authority(professional_fixture())
                    )
                },
            ),
            (
                semantic_fixture(),
                {
                    "expected_semantic_current_bindings": (
                        _semantic_expected_bindings()
                    )
                },
            ),
        )
        for value, authority in fixtures:
            encoded = ATTESTATION.canonical_attestation_bytes(value, **authority)
            self.assertGreater(len(value["findings"]), 0)
            self.assertLessEqual(len(encoded), ATTESTATION.MAX_ATTESTATION_BYTES)


class ExpertPanelAttestationPromotionTests(unittest.TestCase):
    def _git(self, root: Path, *arguments: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(root), *arguments],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def _repo(self, directory: str) -> tuple[Path, dict]:
        root = Path(directory)
        self._git(root, "init", "-q")
        self._git(root, "config", "user.email", "test@example.invalid")
        self._git(root, "config", "user.name", "Test")
        (root / ".gitignore").write_text(".rd-skills/\n", encoding="utf-8")
        fixed_parent = root / "evals" / "expert-panel"
        fixed_parent.mkdir(parents=True)
        (fixed_parent / ".gitkeep").write_text("", encoding="utf-8")
        self._git(root, "add", ".gitignore", "evals/expert-panel/.gitkeep")
        self._git(root, "commit", "-qm", "fixture")
        value = readability_fixture()
        source = (
            root
            / ATTESTATION.EPHEMERAL_RUN_ROOT
            / value["review_id"]
            / "attestation.json"
        )
        source.parent.mkdir(parents=True)
        source.write_bytes(
            ATTESTATION.canonical_attestation_bytes(
                value,
                expected_readability_current_bindings=(
                    _compact_readability_bindings()
                ),
            )
        )
        return root, value

    @staticmethod
    def _validation(value: dict) -> tuple[str, dict, object]:
        return ATTESTATION.READABILITY_ATTESTATION_PATH, {
            "expected_source_fingerprints": value["source_fingerprints"],
            "expected_review_contract_fingerprint": value[
                "review_contract_fingerprint"
            ],
            "expected_readability_current_bindings": (
                _compact_readability_bindings()
            ),
        }, lambda _value: None

    @staticmethod
    def _args(value: dict, expected: str = "absent") -> argparse.Namespace:
        return argparse.Namespace(
            panel_kind=ATTESTATION.READABILITY_AXIS,
            review_id=value["review_id"],
            source=(
                f"{ATTESTATION.EPHEMERAL_RUN_ROOT}/"
                f"{value['review_id']}/attestation.json"
            ),
            expected_existing_sha256=expected,
        )

    @staticmethod
    def _readability_packet(value: dict) -> dict:
        targets = _compact_readability_targets()
        return {
            "source_fingerprints": value["source_fingerprints"],
            "panel_contract": {"fixture": "strict-current-readability"},
            "content_targets": [targets["content"]],
            "readability_targets": [targets["readability"]],
            "actionability_targets": [targets["actionability"]],
        }

    def test_fixed_professional_currentness_ignores_same_review_runtime_decision(
        self,
    ) -> None:
        value = professional_fixture()
        projection_head = "b" * 40
        for row in value["findings"]:
            row["provenance"]["origin"]["origin_commit"] = projection_head
        authority = _professional_authority(value)
        with mock.patch.object(
            PANEL,
            "_ephemeral_review_path",
            side_effect=AssertionError(
                "fixed currentness must not inspect runtime decisions"
            ),
        ), mock.patch.object(
            PANEL,
            "_git_output",
            side_effect=AssertionError(
                "fixed currentness must not require origin_commit to equal promotion HEAD"
            ),
        ), mock.patch.object(
            PANEL, "_professional_package_targets", return_value=[]
        ), mock.patch.object(
            PANEL,
            "_professional_v3_binding_state",
            return_value=({}, {"targets": {}}),
        ), mock.patch.object(
            PANEL,
            "_professional_evidence_review_contract_fingerprint",
            return_value=value["review_contract_fingerprint"],
        ), mock.patch.object(
            PANEL,
            "_professional_attestation_bindings_from_state",
            return_value=authority,
        ), mock.patch.object(
            PANEL,
            "_professional_authenticated_claims_from_findings",
            wraps=PANEL._professional_authenticated_claims_from_findings,
        ) as authenticate:
            relative, validation, _validate_current = (
                PANEL._current_attestation_validation(
                    PANEL.PROFESSIONAL_COMPLETENESS_PANEL_KIND,
                    review_id=value["review_id"],
                    decided_on=value["decided_on"],
                    attestation_selector=value,
                )
            )

        self.assertEqual(
            ATTESTATION.PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH,
            relative,
        )
        self.assertEqual(
            authority,
            validation["expected_professional_current_bindings"],
        )
        self.assertEqual(
            {projection_head},
            {
                row["provenance"]["origin"]["origin_commit"]
                for row in value["findings"]
            },
        )
        authenticate.assert_called_once_with(value["findings"])

    def test_professional_currentness_builds_catalog_bindings_and_registries_once(
        self,
    ) -> None:
        value = professional_fixture()
        authority = _professional_authority(value)
        registry_reads: list[str] = []
        original_load_yaml = PANEL.load_yaml_file

        def counted_load_yaml(path: Path) -> dict:
            registry_reads.append(path.as_posix())
            return original_load_yaml(path)

        with mock.patch.object(
            PANEL,
            "_professional_package_targets",
            wraps=PANEL._professional_package_targets,
        ) as catalog, mock.patch.object(
            PANEL.professional_carry,
            "professional_review_bindings",
            wraps=PANEL.professional_carry.professional_review_bindings,
        ) as bindings, mock.patch.object(
            PANEL,
            "_professional_catalog_rankings",
            wraps=PANEL._professional_catalog_rankings,
        ) as rankings, mock.patch.object(
            PANEL,
            "load_yaml_file",
            side_effect=counted_load_yaml,
        ), mock.patch.object(
            PANEL,
            "_professional_evidence_review_contract_fingerprint",
            return_value=value["review_contract_fingerprint"],
        ), mock.patch.object(
            PANEL,
            "_professional_attestation_bindings_from_state",
            return_value=authority,
        ):
            PANEL._current_attestation_validation(
                PANEL.PROFESSIONAL_COMPLETENESS_PANEL_KIND,
                review_id=value["review_id"],
                decided_on=value["decided_on"],
                attestation_selector=value,
            )

        self.assertEqual(1, catalog.call_count)
        self.assertEqual(1, bindings.call_count)
        self.assertEqual(1, rankings.call_count)
        expected_registries = {
            (ROOT / relative).as_posix()
            for _layer, relative, _collection in PANEL.REGISTRY_SOURCES
        }
        self.assertEqual(expected_registries, set(registry_reads))
        self.assertTrue(
            all(registry_reads.count(path) == 1 for path in expected_registries)
        )

    def test_professional_promotion_authority_must_match_source_projection(
        self,
    ) -> None:
        value = professional_fixture()
        authority = _professional_authority(value)
        raw = ATTESTATION.canonical_attestation_bytes(
            value,
            expected_professional_current_bindings=authority,
        )
        selector = ATTESTATION.parse_attestation_storage_selector_bytes(raw)
        decision_path = Path(
            ".rd-skills/expert-panel/"
            f"{value['review_id']}/panel/decision.json"
        )
        decision = {"review_id": value["review_id"]}
        claims = PANEL._professional_authenticated_claims_from_findings(
            value["findings"]
        )
        common = (
            mock.patch.object(
                PANEL, "_bound_json_object", return_value=(mock.sentinel.bound, decision)
            ),
            mock.patch.object(PANEL, "_professional_package_targets", return_value=[]),
            mock.patch.object(
                PANEL,
                "_professional_v3_binding_state",
                return_value=({}, {"targets": {}}),
            ),
            mock.patch.object(
                PANEL,
                "_professional_evidence_review_contract_fingerprint",
                return_value=value["review_contract_fingerprint"],
            ),
            mock.patch.object(
                PANEL,
                "_professional_attestation_bindings_from_state",
                return_value=authority,
            ),
        )
        with common[0], common[1], common[2], common[3], common[4], mock.patch.object(
            PANEL,
            "_professional_attestation_projection_from_decision",
            return_value=(copy.deepcopy(value), claims),
        ):
            relative, validation, _validate_current = (
                PANEL._current_attestation_validation(
                    PANEL.PROFESSIONAL_COMPLETENESS_PANEL_KIND,
                    review_id=value["review_id"],
                    decided_on=value["decided_on"],
                    attestation_selector=selector,
                    promotion_decision_path=decision_path,
                    promotion_source_bytes=raw,
                )
            )
        self.assertEqual(
            ATTESTATION.PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH,
            relative,
        )
        self.assertEqual(
            authority,
            validation["expected_professional_current_bindings"],
        )

        mismatched = copy.deepcopy(value)
        mismatched["rationale"] = ["A different projected attestation."]
        common = (
            mock.patch.object(
                PANEL, "_bound_json_object", return_value=(mock.sentinel.bound, decision)
            ),
            mock.patch.object(PANEL, "_professional_package_targets", return_value=[]),
            mock.patch.object(
                PANEL,
                "_professional_v3_binding_state",
                return_value=({}, {"targets": {}}),
            ),
            mock.patch.object(
                PANEL,
                "_professional_evidence_review_contract_fingerprint",
                return_value=value["review_contract_fingerprint"],
            ),
            mock.patch.object(
                PANEL,
                "_professional_attestation_bindings_from_state",
                return_value=authority,
            ),
        )
        with common[0], common[1], common[2], common[3], common[4], mock.patch.object(
            PANEL,
            "_professional_attestation_projection_from_decision",
            return_value=(mismatched, claims),
        ), self.assertRaisesRegex(PANEL.PanelReviewError, "does not match"):
            PANEL._current_attestation_validation(
                PANEL.PROFESSIONAL_COMPLETENESS_PANEL_KIND,
                review_id=value["review_id"],
                decided_on=value["decided_on"],
                attestation_selector=selector,
                promotion_decision_path=decision_path,
                promotion_source_bytes=raw,
            )

    def test_professional_promotion_binds_canonical_source_bytes_to_decision(
        self,
    ) -> None:
        value = professional_fixture(review_mode="full-fresh")
        projection_head = "b" * 40
        for row in value["findings"]:
            row["provenance"]["origin"]["origin_commit"] = projection_head
        authority = _professional_authority(value)
        raw = ATTESTATION.canonical_attestation_bytes(
            value,
            expected_professional_current_bindings=authority,
        )
        selector = ATTESTATION.parse_attestation_storage_selector_bytes(raw)
        decision_path = Path(
            ".rd-skills/expert-panel/"
            f"{value['review_id']}/panel/decision.json"
        )
        decision = {"review_id": value["review_id"]}
        claims = PANEL._professional_authenticated_claims_from_findings(
            value["findings"]
        )

        def patches():
            return (
                mock.patch.object(
                    PANEL,
                    "_bound_json_object",
                    return_value=(mock.sentinel.bound, decision),
                ),
                mock.patch.object(
                    PANEL, "_professional_package_targets", return_value=[]
                ),
                mock.patch.object(
                    PANEL,
                    "_professional_v3_binding_state",
                    return_value=({}, {"targets": {}}),
                ),
                mock.patch.object(
                    PANEL,
                    "_professional_evidence_review_contract_fingerprint",
                    return_value=value["review_contract_fingerprint"],
                ),
                mock.patch.object(
                    PANEL,
                    "_professional_attestation_bindings_from_state",
                    return_value=authority,
                ),
                mock.patch.object(
                    PANEL,
                    "_professional_attestation_projection_from_decision",
                    return_value=(copy.deepcopy(value), claims),
                ),
            )

        contexts = patches()
        with contexts[0], contexts[1], contexts[2], contexts[3], contexts[4], contexts[5]:
            PANEL._current_attestation_validation(
                PANEL.PROFESSIONAL_COMPLETENESS_PANEL_KIND,
                review_id=value["review_id"],
                decided_on=value["decided_on"],
                attestation_selector=selector,
                promotion_decision_path=decision_path,
                promotion_source_bytes=raw,
            )

        old_head = copy.deepcopy(value)
        for row in old_head["findings"]:
            row["provenance"]["origin"]["origin_commit"] = "a" * 40
        rebound = copy.deepcopy(old_head)
        for row in rebound["findings"]:
            row["provenance"]["origin"]["origin_commit"] = projection_head
        self.assertEqual(
            value,
            rebound,
            "projection commit must not alter conclusions, votes, or material bindings",
        )
        old_head_raw = ATTESTATION.canonical_attestation_bytes(
            old_head,
            expected_professional_current_bindings=(
                _professional_authority(old_head)
            ),
        )
        old_head_selector = (
            ATTESTATION.parse_attestation_storage_selector_bytes(old_head_raw)
        )
        contexts = patches()
        with contexts[0], contexts[1], contexts[2], contexts[3], contexts[4], contexts[5], self.assertRaisesRegex(
            PANEL.PanelReviewError,
            "does not match its decision projection",
        ):
            PANEL._current_attestation_validation(
                PANEL.PROFESSIONAL_COMPLETENESS_PANEL_KIND,
                review_id=value["review_id"],
                decided_on=value["decided_on"],
                attestation_selector=old_head_selector,
                promotion_decision_path=decision_path,
                promotion_source_bytes=old_head_raw,
            )

        different = copy.deepcopy(value)
        different["rationale"] = ["A different canonical source projection."]
        different_raw = ATTESTATION.canonical_attestation_bytes(
            different,
            expected_professional_current_bindings=authority,
        )
        different_selector = (
            ATTESTATION.parse_attestation_storage_selector_bytes(different_raw)
        )
        contexts = patches()
        with contexts[0], contexts[1], contexts[2], contexts[3], contexts[4], contexts[5], self.assertRaisesRegex(
            PANEL.PanelReviewError,
            "does not match its decision projection",
        ):
            PANEL._current_attestation_validation(
                PANEL.PROFESSIONAL_COMPLETENESS_PANEL_KIND,
                review_id=value["review_id"],
                decided_on=value["decided_on"],
                attestation_selector=different_selector,
                promotion_decision_path=decision_path,
                promotion_source_bytes=different_raw,
            )

    def test_readability_promotion_rejects_rebound_conclusion_substitution(
        self,
    ) -> None:
        value = readability_fixture()
        packet = self._readability_packet(value)
        value["review_contract_fingerprint"] = PANEL._canonical_json_sha256(
            packet["panel_contract"]
        )
        bindings = PANEL._readability_target_authorities(packet)
        value = ATTESTATION.finalize_attestation(
            value,
            expected_readability_current_bindings=bindings,
        )
        compact = json.loads(
            ATTESTATION.canonical_attestation_bytes(
                value,
                expected_source_fingerprints=packet["source_fingerprints"],
                expected_review_contract_fingerprint=value[
                    "review_contract_fingerprint"
                ],
                expected_readability_current_bindings=bindings,
            )
        )
        tampered = copy.deepcopy(compact)
        row = next(
            finding
            for finding in tampered["findings"]
            if finding["category"] == "content"
        )
        row["votes"] = [
            _simple_vote(
                reviewer["voter_id"],
                "tracked-tightening",
                "multiple-independent-actions",
            )
            for reviewer in value["reviewers"]
        ]
        row["review_unit_binding"] = (
            ATTESTATION.readability_review_unit_binding(
                category="content",
                target_id=row["target_id"],
                authority=bindings["content"][row["target_id"]],
            )
        )
        tampered["verdict"] = "requires-readability-correction"
        tampered_raw = (
            json.dumps(
                tampered,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        )
        parsed = ATTESTATION.parse_attestation_bytes(
            tampered_raw,
            expected_source_fingerprints=packet["source_fingerprints"],
            expected_review_contract_fingerprint=value[
                "review_contract_fingerprint"
            ],
            expected_readability_current_bindings=bindings,
        )
        self.assertEqual("requires-readability-correction", parsed["verdict"])

        decision_path = PANEL._ephemeral_review_path(
            value["review_id"], "panel", "decision.json"
        )
        with mock.patch.object(
            PANEL, "_json_object", return_value={}
        ), mock.patch.object(
            PANEL,
            "_bound_json_object",
            return_value=(
                mock.sentinel.bound,
                {"review_id": value["review_id"]},
            ),
        ), mock.patch.object(
            PANEL,
            "_readability_attestation_from_decision",
            return_value=value,
        ), mock.patch.object(
            PANEL, "prepare_packet", return_value=packet
        ), self.assertRaisesRegex(
            PANEL.PanelReviewError,
            "does not match its decision projection",
        ):
            PANEL._current_attestation_validation(
                PANEL.READABILITY_PANEL_KIND,
                review_id=value["review_id"],
                decided_on=value["decided_on"],
                attestation_selector=tampered,
                promotion_decision_path=decision_path,
            )

    def test_promotion_rejects_empty_current_readability_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, value = self._repo(directory)
            packet = self._readability_packet(value)
            value["review_contract_fingerprint"] = _sha(
                packet["panel_contract"]
            )
            value["findings"] = []
            source = (
                root
                / ATTESTATION.EPHEMERAL_RUN_ROOT
                / value["review_id"]
                / "attestation.json"
            )
            source.write_bytes(
                json.dumps(
                    value,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
                + b"\n"
            )
            with mock.patch.object(PANEL, "ROOT", root), mock.patch.object(
                PANEL, "_json_object", return_value={}
            ), mock.patch.object(PANEL, "prepare_packet", return_value=packet):
                with self.assertRaises(
                    (PANEL.PanelReviewError, ATTESTATION.AttestationError)
                ):
                    PANEL._promote_attestation(self._args(value))
            self.assertFalse(
                (root / ATTESTATION.READABILITY_ATTESTATION_PATH).exists()
            )

    def test_semantic_promotion_requires_current_authority_and_rejects_tampering(
        self,
    ) -> None:
        for mutation in (
            "missing-authority",
            "tampered-candidate-binding-fingerprint",
        ):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root, _readability = self._repo(directory)
                value = semantic_fixture()
                authorities = _semantic_expected_bindings()
                source = (
                    root
                    / ATTESTATION.EPHEMERAL_RUN_ROOT
                    / value["review_id"]
                    / "attestation.json"
                )
                source.parent.mkdir(parents=True, exist_ok=True)
                if mutation.startswith("tampered-"):
                    changed = copy.deepcopy(value)
                    changed["findings"][0][
                        "candidate_binding_fingerprint"
                    ] = SHA_A
                    source.write_bytes(
                        json.dumps(
                            changed,
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        ).encode("utf-8")
                        + b"\n"
                    )
                else:
                    source.write_bytes(
                        ATTESTATION.canonical_attestation_bytes(
                            value,
                            expected_semantic_current_bindings=authorities,
                        )
                    )
                validation = {
                    "expected_source_fingerprints": value[
                        "source_fingerprints"
                    ],
                    "expected_review_contract_fingerprint": value[
                        "review_contract_fingerprint"
                    ],
                }
                if mutation != "missing-authority":
                    validation["expected_semantic_current_bindings"] = authorities
                args = argparse.Namespace(
                    panel_kind=ATTESTATION.SEMANTIC_DISPOSITION_AXIS,
                    review_id=value["review_id"],
                    source=(
                        f"{ATTESTATION.EPHEMERAL_RUN_ROOT}/"
                        f"{value['review_id']}/attestation.json"
                    ),
                    expected_existing_sha256="absent",
                )
                with mock.patch.object(PANEL, "ROOT", root), mock.patch.object(
                    PANEL,
                    "_current_attestation_validation",
                    return_value=(
                        ATTESTATION.SEMANTIC_DISPOSITION_ATTESTATION_PATH,
                        validation,
                        lambda _value: None,
                    ),
                ), self.assertRaises(
                    (PANEL.PanelReviewError, ATTESTATION.AttestationError)
                ):
                    PANEL._promote_attestation(args)
                self.assertFalse(
                    (
                        root
                        / ATTESTATION.SEMANTIC_DISPOSITION_ATTESTATION_PATH
                    ).exists()
                )

    def test_promotion_replays_strict_validator_on_every_atomic_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, value = self._repo(directory)
            calls = 0
            parse_attestation = ATTESTATION.parse_attestation_bytes

            def strict(raw: bytes, **validation) -> dict:
                nonlocal calls
                calls += 1
                if calls == 4:
                    raise ATTESTATION.AttestationError(
                        "injected final strict-current rejection"
                    )
                return parse_attestation(raw, **validation)

            relative, parse_validation, _unused = self._validation(value)
            with mock.patch.object(PANEL, "ROOT", root), mock.patch.object(
                PANEL,
                "_current_attestation_validation",
                return_value=(relative, parse_validation, lambda _value: None),
            ), mock.patch.object(
                ATTESTATION,
                "parse_attestation_bytes",
                side_effect=strict,
            ), self.assertRaises(PANEL.PanelReviewError):
                PANEL._promote_attestation(self._args(value))
            self.assertEqual(4, calls)
            self.assertFalse(
                (root / ATTESTATION.READABILITY_ATTESTATION_PATH).exists()
            )
            self.assertEqual(
                [],
                list(
                    (
                        root
                        / ATTESTATION.READABILITY_ATTESTATION_PATH
                    ).parent.glob(".*.tmp")
                ),
            )

    def test_professional_promotion_validates_current_authority_once_per_pass(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, value = self._repo(directory)
            source = (
                root
                / ATTESTATION.EPHEMERAL_RUN_ROOT
                / value["review_id"]
                / "attestation.json"
            )
            source.write_bytes(
                json.dumps(
                    {
                        "schema_version": 2,
                        "review_id": value["review_id"],
                        "decided_on": value["decided_on"],
                        "axis": ATTESTATION.PROFESSIONAL_COMPLETENESS_AXIS,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
                + b"\n"
            )
            authority = {
                "fixture-skill": {"fixture": "current-authority"}
            }
            validation = {
                "expected_professional_current_bindings": authority,
            }

            def duplicate_post_parse(parsed):
                ATTESTATION.validate_attestation(parsed, **validation)

            def parse_attestation(_raw, *, expected_path, **actual_validation):
                self.assertEqual(
                    ATTESTATION.PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH,
                    expected_path,
                )
                self.assertEqual(validation, actual_validation)
                return ATTESTATION.validate_attestation(
                    {"parsed": True}, **actual_validation
                )

            args = argparse.Namespace(
                panel_kind=ATTESTATION.PROFESSIONAL_COMPLETENESS_AXIS,
                review_id=value["review_id"],
                source=(
                    f"{ATTESTATION.EPHEMERAL_RUN_ROOT}/"
                    f"{value['review_id']}/attestation.json"
                ),
                expected_existing_sha256="absent",
            )
            with mock.patch.object(PANEL, "ROOT", root), mock.patch.object(
                PANEL,
                "_current_attestation_validation",
                return_value=(
                    ATTESTATION.PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH,
                    validation,
                    duplicate_post_parse,
                ),
            ), mock.patch.object(
                ATTESTATION,
                "parse_attestation_storage_selector_bytes",
                return_value={
                    "schema_version": 2,
                    "review_id": value["review_id"],
                    "decided_on": value["decided_on"],
                    "axis": ATTESTATION.PROFESSIONAL_COMPLETENESS_AXIS,
                },
            ) as selector, mock.patch.object(
                ATTESTATION,
                "parse_attestation_bytes",
                side_effect=parse_attestation,
            ) as parse, mock.patch.object(
                ATTESTATION,
                "validate_attestation",
                return_value={"parsed": True},
            ) as validate:
                destination = PANEL._promote_attestation(args)

        self.assertEqual(
            ATTESTATION.PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH,
            destination.relative_to(root).as_posix(),
        )
        self.assertEqual(1, selector.call_count)
        self.assertEqual(4, parse.call_count)
        self.assertEqual(parse.call_count, validate.call_count)

    def test_professional_promotion_rejects_rehashed_currentness_rewrites(
        self,
    ) -> None:
        for mutation in ("binding", "vote-digest"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root, _readability = self._repo(directory)
                value = professional_fixture(review_mode="full-fresh")
                authority = _professional_authority(value)
                if mutation == "binding":
                    row = value["findings"][0]
                    row["review_unit_binding"] = SHA_A
                else:
                    value["findings"][0]["votes"][0][
                        "review_evidence_fingerprint"
                    ] = SHA_A
                source = (
                    root
                    / ATTESTATION.EPHEMERAL_RUN_ROOT
                    / value["review_id"]
                    / "attestation.json"
                )
                source.parent.mkdir(parents=True, exist_ok=True)
                source.write_bytes(
                    json.dumps(
                        value,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                    + b"\n"
                )
                args = argparse.Namespace(
                    panel_kind=ATTESTATION.PROFESSIONAL_COMPLETENESS_AXIS,
                    review_id=value["review_id"],
                    source=(
                        f"{ATTESTATION.EPHEMERAL_RUN_ROOT}/"
                        f"{value['review_id']}/attestation.json"
                    ),
                    expected_existing_sha256="absent",
                )
                validation = {
                    "expected_review_contract_fingerprint": value[
                        "review_contract_fingerprint"
                    ],
                    "expected_professional_current_bindings": authority,
                }
                with mock.patch.object(PANEL, "ROOT", root), mock.patch.object(
                    PANEL,
                    "_current_attestation_validation",
                    return_value=(
                        ATTESTATION.PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH,
                        validation,
                        lambda _value: None,
                    ),
                ):
                    with self.assertRaises(PANEL.PanelReviewError):
                        PANEL._promote_attestation(args)
                self.assertFalse(
                    (
                        root
                        / ATTESTATION.PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH
                    ).exists()
                )

    def test_baseline_loader_rejects_old_professional_vote_schema(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            value, packet = _current_professional_attestation_fixture()
            targets = []
            for target in packet["professional_targets"]:
                base = copy.deepcopy(target)
                base.pop("review_binding")
                targets.append(base)
            bindings = PANEL.professional_carry.professional_review_bindings(
                targets
            )
            snapshot = PANEL.professional_carry.professional_carry_snapshot(
                bindings, review_contract_fingerprint=SHA_A
            )
            value["findings"][0]["votes"][0]["reviewer"] = copy.deepcopy(
                _professional_reviewers()[0]
            )
            fixed = root / ATTESTATION.PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH
            fixed.parent.mkdir(parents=True)
            fixed.write_bytes(
                json.dumps(
                    value,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
                + b"\n"
            )
            with mock.patch.object(PANEL, "ROOT", root), self.assertRaises(
                PANEL.PanelReviewError
            ):
                PANEL._load_professional_attestation_baseline(
                    fixed,
                    current_bindings=bindings,
                    current_snapshot=snapshot,
                    review_contract_fingerprint=SHA_A,
                    expected_attestation_sha256=hashlib.sha256(
                        fixed.read_bytes()
                    ).hexdigest(),
                )

    def test_atomic_creation_and_cas_failure_preserve_destination(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, value = self._repo(directory)
            with mock.patch.object(PANEL, "ROOT", root), mock.patch.object(
                PANEL,
                "_current_attestation_validation",
                return_value=self._validation(value),
            ):
                destination = PANEL._promote_attestation(self._args(value))
                original = destination.read_bytes()
                self.assertEqual(
                    ATTESTATION.canonical_attestation_bytes(
                        value,
                        expected_readability_current_bindings=(
                            _compact_readability_bindings()
                        ),
                    ),
                    original,
                )
                with self.assertRaises(PANEL.PanelReviewError):
                    PANEL._promote_attestation(self._args(value))
                self.assertEqual(original, destination.read_bytes())
                self.assertEqual([], list(destination.parent.glob(".*.tmp")))

    def test_dirty_tree_and_symlink_source_fail_without_destination(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, value = self._repo(directory)
            dirty = root / "dirty.txt"
            dirty.write_text("dirty", encoding="utf-8")
            with mock.patch.object(PANEL, "ROOT", root), mock.patch.object(
                PANEL,
                "_current_attestation_validation",
                return_value=self._validation(value),
            ):
                with self.assertRaises(PANEL.PanelReviewError):
                    PANEL._promote_attestation(self._args(value))
                self.assertFalse(
                    (root / ATTESTATION.READABILITY_ATTESTATION_PATH).exists()
                )
            dirty.unlink()
            source = (
                root
                / ATTESTATION.EPHEMERAL_RUN_ROOT
                / value["review_id"]
                / "attestation.json"
            )
            real = source.with_name("real.json")
            source.rename(real)
            source.symlink_to(real.name)
            with mock.patch.object(PANEL, "ROOT", root), self.assertRaises(
                PANEL.PanelReviewError
            ):
                PANEL._promote_attestation(self._args(value))

    def test_atomic_rollback_preserves_existing_bytes_and_mode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            destination = root / "destination.json"
            source.write_bytes(b'{"new":true}\n')
            destination.write_bytes(b'{"old":true}\n')
            destination.chmod(0o660)
            bound_source = PANEL.reviewer_manifest.read_bound_regular_file(
                source, max_bytes=1024, label="source"
            )
            bound_existing = PANEL.reviewer_manifest.read_bound_regular_file(
                destination, max_bytes=1024, label="destination"
            )
            calls = 0

            def fail_after_replace(_raw: bytes) -> None:
                nonlocal calls
                calls += 1
                if calls == 3:
                    raise RuntimeError("injected post-replace failure")

            with self.assertRaises(RuntimeError):
                PANEL.reviewer_manifest.promote_bound_file_atomically(
                    bound_source,
                    destination,
                    bound_existing=bound_existing,
                    max_bytes=1024,
                    validate_final=fail_after_replace,
                )
            self.assertEqual(b'{"old":true}\n', destination.read_bytes())
            self.assertEqual(0o660, stat.S_IMODE(destination.stat().st_mode))
            self.assertEqual([], list(root.glob(".*.tmp")))

    def test_atomic_rollback_does_not_clobber_concurrent_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            destination = root / "destination.json"
            replacement = root / "replacement.json"
            source.write_bytes(b'{"new":true}\n')
            destination.write_bytes(b'{"old":true}\n')
            replacement.write_bytes(b'{"unrelated":true}\n')
            replacement.chmod(0o644)
            bound_source = PANEL.reviewer_manifest.read_bound_regular_file(
                source, max_bytes=1024, label="source"
            )
            bound_existing = PANEL.reviewer_manifest.read_bound_regular_file(
                destination, max_bytes=1024, label="destination"
            )
            calls = 0

            def swap_after_replace(_raw: bytes) -> None:
                nonlocal calls
                calls += 1
                if calls == 3:
                    os.replace(replacement, destination)
                    raise RuntimeError("injected concurrent replacement")

            with self.assertRaises(PANEL.reviewer_manifest.ManifestError):
                PANEL.reviewer_manifest.promote_bound_file_atomically(
                    bound_source,
                    destination,
                    bound_existing=bound_existing,
                    max_bytes=1024,
                    validate_final=swap_after_replace,
                )
            self.assertEqual(
                b'{"unrelated":true}\n', destination.read_bytes()
            )
            self.assertEqual(0o644, stat.S_IMODE(destination.stat().st_mode))
            self.assertEqual([], list(root.glob(".*.tmp")))

    def test_atomic_pre_replace_and_bound_identity_swaps_preserve_destination(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            destination = root / "destination.json"
            source.write_bytes(b'{"new":true}\n')
            destination.write_bytes(b'{"old":true}\n')
            bound_source = PANEL.reviewer_manifest.read_bound_regular_file(
                source, max_bytes=1024, label="source"
            )
            bound_existing = PANEL.reviewer_manifest.read_bound_regular_file(
                destination, max_bytes=1024, label="destination"
            )

            calls = 0

            def fail_before_replace(_raw: bytes) -> None:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise RuntimeError("injected pre-replace failure")

            with self.assertRaises(RuntimeError):
                PANEL.reviewer_manifest.promote_bound_file_atomically(
                    bound_source,
                    destination,
                    bound_existing=bound_existing,
                    max_bytes=1024,
                    validate_final=fail_before_replace,
                )
            self.assertEqual(b'{"old":true}\n', destination.read_bytes())
            source_swap = root / "source-swap.json"
            source_swap.write_bytes(b'{"swapped":true}\n')
            os.replace(source_swap, source)
            with self.assertRaises(PANEL.reviewer_manifest.ManifestError):
                PANEL.reviewer_manifest.promote_bound_file_atomically(
                    bound_source,
                    destination,
                    bound_existing=bound_existing,
                    max_bytes=1024,
                    validate_final=lambda _raw: None,
                )
            self.assertEqual(b'{"old":true}\n', destination.read_bytes())
            destination_swap = root / "destination-swap.json"
            destination_swap.write_bytes(b'{"other":true}\n')
            os.replace(destination_swap, destination)
            with self.assertRaises(PANEL.reviewer_manifest.ManifestError):
                PANEL.reviewer_manifest.promote_bound_file_atomically(
                    PANEL.reviewer_manifest.read_bound_regular_file(
                        source, max_bytes=1024, label="source"
                    ),
                    destination,
                    bound_existing=bound_existing,
                    max_bytes=1024,
                    validate_final=lambda _raw: None,
                )
            self.assertEqual(b'{"other":true}\n', destination.read_bytes())
            self.assertEqual([], list(root.glob(".*.tmp")))

    def test_fixed_professional_baseline_plans_without_predecessor_paths(self) -> None:
        value, packet = _current_professional_attestation_fixture()
        contract = value["review_contract_fingerprint"]
        targets = []
        for target in packet["professional_targets"]:
            base = copy.deepcopy(target)
            base.pop("review_binding")
            targets.append(base)
        bindings = PANEL.professional_carry.professional_review_bindings(targets)
        snapshot = PANEL.professional_carry.professional_carry_snapshot(
            bindings, review_contract_fingerprint=contract
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixed = root / ATTESTATION.PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH
            fixed.parent.mkdir(parents=True)
            fixed.write_bytes(
                ATTESTATION.canonical_attestation_bytes(
                    value,
                    expected_professional_current_bindings=(
                        PANEL._professional_attestation_current_bindings(
                            packet,
                            authenticated_claims=_professional_claims(value),
                        )
                    ),
                )
            )
            for target in targets:
                path = root / target["root"]["path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(target["root"]["content"], encoding="utf-8")
            with mock.patch.object(PANEL, "ROOT", root):
                state = PANEL._load_professional_attestation_baseline(
                    fixed,
                    current_bindings=bindings,
                    current_snapshot=snapshot,
                    review_contract_fingerprint=contract,
                    expected_attestation_sha256=hashlib.sha256(
                        fixed.read_bytes()
                    ).hexdigest(),
                )
            carry_plan = {
                "fresh_target_ids": [],
                "carry_target_ids": sorted(bindings),
                "reasons_by_target": {skill_id: [] for skill_id in bindings},
            }
            with mock.patch.object(
                PANEL.professional_carry,
                "plan_exact_professional_carry_forward",
                return_value=carry_plan,
            ):
                plan = PANEL._professional_v3_review_plan(
                    current_bindings=bindings,
                    review_contract_fingerprint=contract,
                    baseline_state=state,
                )
            self.assertEqual(
                {"attestation"}, set(plan["baseline"])
            )
            self.assertEqual([], plan["fresh_targets"])
            self.assertTrue(plan["carried_targets"])
            self.assertTrue(
                all(
                    set(row)
                    == {
                        "skill_id",
                        "review_unit_binding",
                        "origin_attestation",
                        "origin_verdict_digest",
                    }
                    for row in plan["carried_targets"]
                )
            )

    def test_fixed_professional_baseline_reopens_only_changed_package(self) -> None:
        value, packet = _current_professional_attestation_fixture()
        contract = value["review_contract_fingerprint"]
        current_targets = []
        for target in packet["professional_targets"]:
            base = copy.deepcopy(target)
            base.pop("review_binding")
            current_targets.append(base)
        changed = next(
            target for target in current_targets
            if target["skill_id"] == "carried-skill"
        )
        changed["root"]["content"] += "Changed current package evidence.\n"
        changed["root"]["sha256"] = hashlib.sha256(
            changed["root"]["content"].encode("utf-8")
        ).hexdigest()
        changed["root"]["line_count"] = len(
            changed["root"]["content"].splitlines()
        )
        current_bindings = (
            PANEL.professional_carry.professional_review_bindings(
                current_targets
            )
        )
        current_snapshot = PANEL.professional_carry.professional_carry_snapshot(
            current_bindings,
            review_contract_fingerprint=contract,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixed = root / ATTESTATION.PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH
            fixed.parent.mkdir(parents=True)
            fixed.write_bytes(
                ATTESTATION.canonical_attestation_bytes(
                    value,
                    expected_professional_current_bindings=(
                        PANEL._professional_attestation_current_bindings(
                            packet,
                            authenticated_claims=_professional_claims(value),
                        )
                    ),
                )
            )
            for target in current_targets:
                path = root / target["root"]["path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(target["root"]["content"], encoding="utf-8")
            with mock.patch.object(PANEL, "ROOT", root):
                state = PANEL._load_professional_attestation_baseline(
                    fixed,
                    current_bindings=current_bindings,
                    current_snapshot=current_snapshot,
                    review_contract_fingerprint=contract,
                    expected_attestation_sha256=hashlib.sha256(
                        fixed.read_bytes()
                    ).hexdigest(),
                )
        plan = PANEL.professional_carry.plan_exact_professional_carry_forward(
            current_bindings=current_bindings,
            prior_snapshot=state["snapshot"],
            prior_decision_dependencies=state["dependencies"],
            review_contract_fingerprint=contract,
        )
        self.assertEqual(["carried-skill"], plan["fresh_target_ids"])
        self.assertEqual(
            ["adjacent-skill", "unaffected-skill"],
            plan["carry_target_ids"],
        )
        self.assertTrue(
            all(
                "predecessor" not in json.dumps(origin)
                for origin in state["origins"].values()
            )
        )

    def test_fixed_professional_baseline_reopens_changed_required_candidate_closure(
        self,
    ) -> None:
        value, packet = _current_professional_attestation_fixture()
        contract = value["review_contract_fingerprint"]
        current_targets = []
        for target in packet["professional_targets"]:
            base = copy.deepcopy(target)
            base.pop("review_binding")
            current_targets.append(base)
        changed = next(
            target
            for target in current_targets
            if target["skill_id"] == "unaffected-skill"
        )
        changed["root"]["content"] += "Changed required candidate evidence.\n"
        changed["root"]["sha256"] = hashlib.sha256(
            changed["root"]["content"].encode("utf-8")
        ).hexdigest()
        changed["root"]["line_count"] = len(
            changed["root"]["content"].splitlines()
        )
        current_bindings = (
            PANEL.professional_carry.professional_review_bindings(
                current_targets
            )
        )
        current_snapshot = PANEL.professional_carry.professional_carry_snapshot(
            current_bindings,
            review_contract_fingerprint=contract,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixed = root / ATTESTATION.PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH
            fixed.parent.mkdir(parents=True)
            fixed.write_bytes(
                ATTESTATION.canonical_attestation_bytes(
                    value,
                    expected_professional_current_bindings=(
                        PANEL._professional_attestation_current_bindings(
                            packet,
                            authenticated_claims=_professional_claims(value),
                        )
                    ),
                )
            )
            for target in current_targets:
                path = root / target["root"]["path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(target["root"]["content"], encoding="utf-8")
            with mock.patch.object(PANEL, "ROOT", root):
                state = PANEL._load_professional_attestation_baseline(
                    fixed,
                    current_bindings=current_bindings,
                    current_snapshot=current_snapshot,
                    review_contract_fingerprint=contract,
                    expected_attestation_sha256=hashlib.sha256(
                        fixed.read_bytes()
                    ).hexdigest(),
                )
        plan = PANEL.professional_carry.plan_exact_professional_carry_forward(
            current_bindings=current_bindings,
            prior_snapshot=state["snapshot"],
            prior_decision_dependencies=state["dependencies"],
            review_contract_fingerprint=contract,
        )
        self.assertEqual(
            ["adjacent-skill", "unaffected-skill"],
            plan["fresh_target_ids"],
        )
        self.assertEqual(["carried-skill"], plan["carry_target_ids"])
        self.assertTrue(
            all(
                "predecessor" not in json.dumps(origin)
                for origin in state["origins"].values()
            )
        )


if __name__ == "__main__":
    unittest.main()
