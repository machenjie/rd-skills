"""Domain-owned Professional Completeness fixtures shared by panel tests."""

from __future__ import annotations

import copy
import functools
import hashlib
import json
import tempfile
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

from .expert_panel_source_test_support import PANEL, ROOT, write_json

SKILL_IDS = ("a", "b", "c", "d")

def _sha(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()

def _material(skill_id: str, part: str, content: str) -> dict:
    return {
        "path": f"src/{skill_id}/{part}.md",
        "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "line_count": len(content.splitlines()),
        "content": content,
    }

def _catalog(
    *,
    roots: dict[str, str] | None = None,
    references: dict[str, str] | None = None,
    registry_markers: dict[str, str] | None = None,
    expertise: dict[str, list[str]] | None = None,
    layers: dict[str, str] | None = None,
    required: dict[str, list[str]] | None = None,
    rankings: dict[str, list[str]] | None = None,
    document_filter_marker: str = "baseline-filter",
) -> list[dict]:
    roots = roots or {}
    references = references or {}
    registry_markers = registry_markers or {}
    expertise = expertise or {}
    layers = layers or {}
    required = required or {"b": ["d"], "c": ["a"]}
    rankings = rankings or {}
    targets = []
    for skill_id in SKILL_IDS:
        root_content = roots.get(
            skill_id, f"# {skill_id}\n\nReview {skill_id} root behavior.\n"
        )
        reference_content = references.get(
            skill_id,
            f"# {skill_id} Reference\n\nVerify {skill_id} failure evidence.\n",
        )
        ranking_ids = rankings.get(
            skill_id, sorted(set(SKILL_IDS) - {skill_id})
        )
        ranking = [
            {
                "skill_id": candidate_id,
                "rank": rank,
                "total_score": 0,
                "signals": {},
            }
            for rank, candidate_id in enumerate(ranking_ids, start=1)
        ]
        ranking_by_id = {row["skill_id"]: row for row in ranking}
        required_ids = sorted(required.get(skill_id, []))
        required_candidates = [
            {
                **ranking_by_id[candidate_id],
                "declared": False,
                "selection_reasons": ["fixture-required"],
            }
            for candidate_id in required_ids
        ]
        responsibility = {
            "marker": registry_markers.get(skill_id, "baseline-registry"),
            "trigger_signals": [f"trigger {skill_id}"],
            "output_contract": [f"output {skill_id}"],
        }
        registry_row = {
            "name": skill_id,
            "responsibility_contract": responsibility,
        }
        adjacency = {
            "algorithm": "fixture-ranking-v1",
            "document_frequency_filter": {
                "catalog_wide_intermediate": document_filter_marker
            },
            "declared_skills": [],
            "required_candidate_selection": {
                "version": "fixture-selection-v1"
            },
            "required_candidates": required_candidates,
            "required_candidates_fingerprint": _sha(required_candidates),
            "full_catalog_count": len(ranking),
            "full_catalog_ranking": ranking,
            "full_catalog_ranking_fingerprint": _sha(ranking),
        }
        target = {
            "skill_id": skill_id,
            "layer": layers.get(skill_id, "foundation"),
            "required_expertise_tags": expertise.get(skill_id, ["domain"]),
            "root": _material(skill_id, "SKILL", root_content),
            "indexed_references": [
                _material(skill_id, "reference", reference_content)
            ],
            "registry": {
                "path": "src/registry.yaml",
                "entry_fingerprint": _sha(registry_row),
                "responsibility_contract": responsibility,
            },
            "routing_adjacency": adjacency,
        }
        target["package_fingerprint"] = _sha(target)
        targets.append(target)
    return targets

def _live_packet() -> dict:
    return PANEL.prepare_professional_completeness_packet(
        review_id="carry-baseline",
        created_on="2026-07-17",
    )

def _legacy_schema1_packet() -> dict:
    current = _live_packet()
    targets = []
    for current_target in current["professional_targets"]:
        responsibility = copy.deepcopy(
            current_target["registry"]["responsibility_contract"]
        )
        adjacent_skills = copy.deepcopy(
            current_target["routing_adjacency"]["declared_skills"]
        )
        routing_basis = {
            "skill_id": current_target["skill_id"],
            "layer": current_target["layer"],
            "role_support": responsibility["role_support"],
            "trigger_signals": responsibility["trigger_signals"],
            "anti_trigger_signals": responsibility["anti_trigger_signals"],
            "output_contract": responsibility["output_contract"],
            "adjacent_skills": adjacent_skills,
        }
        target = {
            "skill_id": current_target["skill_id"],
            "layer": current_target["layer"],
            "root": {
                "path": current_target["root"]["path"],
                "sha256": current_target["root"]["sha256"],
            },
            "indexed_references": [
                {"path": row["path"], "sha256": row["sha256"]}
                for row in current_target["indexed_references"]
            ],
            "registry": {
                "path": current_target["registry"]["path"],
                "entry_fingerprint": _sha(current_target["registry"]),
                "responsibility_contract": responsibility,
            },
            "routing_adjacency": {
                "skills": adjacent_skills,
                "fingerprint": _sha(routing_basis),
            },
        }
        target["package_fingerprint"] = _sha(target)
        targets.append(target)
    return {
        "schema_version": PANEL.SCHEMA_VERSION,
        "kind": PANEL.PROFESSIONAL_COMPLETENESS_PACKET_KIND,
        "review_id": "legacy-carry-baseline",
        "created_on": "2026-07-17",
        "source_fingerprints": {"professional_packages": _sha(targets)},
        "panel_contract": {
            "decision_method": PANEL.DECISION_METHOD,
            "required_voters": PANEL.PANEL_SIZE,
            "abstentions_allowed": False,
            "minimum_winning_votes": 2,
            "independent_ballots": True,
            "required_target_count": PANEL.PROFESSIONAL_PACKAGE_COUNT,
            "criteria_required_per_target": sorted(
                PANEL.PROFESSIONAL_COMPLETENESS_CRITERIA
            ),
        },
        "rubric": {
            "accept": "Accept the complete legacy package.",
            "correct": "Correct any legacy professional defect.",
            "criteria": dict(
                sorted(PANEL.PROFESSIONAL_COMPLETENESS_CRITERIA.items())
            ),
            "reason_codes": {
                decision: sorted(PANEL.PROFESSIONAL_REASON_CODES[decision])
                for decision in sorted(
                    PANEL.PROFESSIONAL_COMPLETENESS_DECISIONS
                )
            },
        },
        "professional_targets": targets,
        "limitations": ["Legacy static fixture."],
    }

@functools.lru_cache(maxsize=1)
def _bootstrap_packet_cached() -> dict:
    return PANEL.prepare_professional_completeness_packet_v3(
        review_id="schema3-unit-bootstrap",
        created_on="2026-07-17",
    )

def _bootstrap_packet() -> dict:
    return copy.deepcopy(_bootstrap_packet_cached())


def _normalize_historical_reviewer_added_promotions(
    value: dict, *, bindings: dict[str, dict]
) -> None:
    """Reclassify authenticated reviewer-added candidates now required."""

    findings = value.get("findings")
    if not isinstance(findings, list):
        raise AssertionError("Professional fixture findings are missing")
    findings_by_id = {
        row.get("skill_id"): row
        for row in findings
        if isinstance(row, dict) and isinstance(row.get("skill_id"), str)
    }
    if len(findings_by_id) != len(findings):
        raise AssertionError("Professional fixture findings are not unique")

    catalog = value.get("dependency_material_catalog")
    if not isinstance(catalog, dict):
        raise AssertionError(
            "Professional fixture dependency material catalog is missing"
        )
    if set(findings_by_id) != set(bindings):
        raise AssertionError(
            "Professional fixture finding and binding coverage differs"
        )
    for skill_id, row in sorted(findings_by_id.items()):
        binding = bindings[skill_id]
        if not isinstance(binding, dict):
            raise AssertionError(
                f"Professional fixture binding is invalid: {skill_id}"
            )
        current_required_ids = binding["adjacency"][
            "required_candidate_ids"
        ]
        if current_required_ids != sorted(set(current_required_ids)):
            raise AssertionError(
                f"Professional fixture required candidates are not canonical: {skill_id}"
            )
        current_required = set(current_required_ids)

        review_dependencies = row["result"]["review_dependencies"]
        historical_added_ids = review_dependencies[
            "reviewer_added_candidate_ids_union"
        ]
        if historical_added_ids != sorted(set(historical_added_ids)):
            raise AssertionError(
                f"Professional fixture reviewer-added union is not canonical: {skill_id}"
            )
        historical_added = set(historical_added_ids)
        promoted_ids = historical_added & current_required

        observed_added: set[str] = set()
        remaining_by_vote: list[list[str]] = []
        for vote in row["votes"]:
            adjacency = vote["examined_adjacent_candidates"]
            added_ids = adjacency["reviewer_added_candidate_ids"]
            if added_ids != sorted(set(added_ids)):
                raise AssertionError(
                    f"Professional fixture reviewer-added vote is not canonical: {skill_id}"
                )
            observed_added.update(added_ids)
            remaining = sorted(set(added_ids) - promoted_ids)
            adjacency["reviewer_added_candidate_ids"] = remaining
            adjacency["required_count"] = len(current_required_ids)
            adjacency["count"] = len(current_required_ids) + len(remaining)
            remaining_by_vote.append(remaining)
        if observed_added != historical_added:
            raise AssertionError(
                f"Professional fixture reviewer-added union is inconsistent: {skill_id}"
            )

        remaining_union = sorted(
            {
                candidate_id
                for added_ids in remaining_by_vote
                for candidate_id in added_ids
            }
        )
        expected_remaining = sorted(historical_added - promoted_ids)
        if remaining_union != expected_remaining:
            raise AssertionError(
                f"Professional fixture reviewer-added union is inconsistent: {skill_id}"
            )
        historical_unknown = sorted(historical_added - set(bindings))
        if historical_unknown:
            raise AssertionError(
                f"Professional fixture reviewer-added candidates are unknown: {skill_id}"
            )
        dependency_ids = sorted(current_required | set(remaining_union))
        unknown_dependencies = sorted(set(dependency_ids) - set(bindings))
        if unknown_dependencies:
            raise AssertionError(
                f"Professional fixture promotion dependencies are unknown: {skill_id}"
            )
        missing_material = sorted(
            candidate_id
            for candidate_id in historical_added
            if not isinstance(catalog.get(candidate_id), str)
            or len(catalog[candidate_id]) != 64
            or any(
                character not in "0123456789abcdef"
                for character in catalog[candidate_id]
            )
        )
        if missing_material:
            raise AssertionError(
                f"Professional fixture reviewer-added material is missing or stale: {skill_id}"
            )

        review_dependencies["required_candidate_ids"] = copy.deepcopy(
            current_required_ids
        )
        review_dependencies[
            "reviewer_added_candidate_ids_union"
        ] = remaining_union
        review_dependencies["dependency_candidate_ids"] = dependency_ids
        row["dependency_ids"] = dependency_ids
        for candidate_id in dependency_ids:
            catalog[candidate_id] = bindings[candidate_id][
                "package_material_binding"
            ]

        metrics = row["result"]["evidence_metrics"]
        metrics["required_adjacency_candidate_count"] = len(
            current_required_ids
        )
        metrics["examined_adjacency_count"] = sum(
            vote["examined_adjacent_candidates"]["count"]
            for vote in row["votes"]
        )
        metrics["examined_required_adjacency_count"] = sum(
            vote["examined_adjacent_candidates"]["required_count"]
            for vote in row["votes"]
        )
        metrics["reviewer_added_adjacency_count"] = sum(
            len(vote["examined_adjacent_candidates"][
                "reviewer_added_candidate_ids"
            ])
            for vote in row["votes"]
        )
    value["dependency_material_catalog"] = dict(sorted(catalog.items()))


def _current_compact_professional_fixture_bytes(
    targets: list[dict], *, review_contract_fingerprint: str
) -> bytes:
    """Rebind historical judgments as schema-2 test data, never authority."""

    bindings, _snapshot = PANEL._professional_v3_binding_state(
        targets,
        review_contract_fingerprint=review_contract_fingerprint,
    )
    raw = (
        PANEL.ROOT
        / PANEL.panel_attestation.PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH
    ).read_bytes()
    preliminary = (
        PANEL.panel_attestation.parse_attestation_storage_selector_bytes(raw)
    )
    _normalize_historical_reviewer_added_promotions(
        preliminary, bindings=bindings
    )
    claims = PANEL._professional_authenticated_claims_from_findings(
        preliminary["findings"]
    )
    authorities = PANEL._professional_attestation_bindings_from_state(
        current_bindings=bindings,
        authenticated_claims=claims,
    )
    residual_overlaps = {
        skill_id: sorted(
            set(authority["required_candidate_ids"])
            & set(authority["reviewer_added_candidate_ids_union"])
        )
        for skill_id, authority in authorities.items()
        if set(authority["required_candidate_ids"])
        & set(authority["reviewer_added_candidate_ids_union"])
    }
    if residual_overlaps:
        raise AssertionError(
            "Professional fixture retains reviewer-added/required overlap"
        )
    normalized_storage = copy.deepcopy(preliminary)
    PANEL.panel_attestation._encode_professional_storage_in_place(
        normalized_storage
    )
    normalized_raw = (
        PANEL.panel_attestation._json_body(normalized_storage) + b"\n"
    )
    value, _eligible_ids = (
        PANEL.panel_attestation.parse_professional_baseline_bytes(
            normalized_raw,
            expected_path=(
                PANEL.panel_attestation.PROFESSIONAL_COMPLETENESS_ATTESTATION_PATH
            ),
            expected_professional_current_bindings=authorities,
        )
    )
    value["review_contract_fingerprint"] = review_contract_fingerprint
    for row in value["findings"]:
        authority = authorities[row["skill_id"]]
        required_candidate_count = len(authority["required_candidate_ids"])
        for vote in row["votes"]:
            adjacency = vote["examined_adjacent_candidates"]
            adjacency["required_count"] = required_candidate_count
            adjacency["count"] = required_candidate_count + len(
                adjacency["reviewer_added_candidate_ids"]
            )
        row["package_material_binding"] = authority[
            "package_material_binding"
        ]
        row["review_unit_binding"] = authority["review_unit_binding"]
        row["required_expertise_tags"] = authority[
            "required_expertise_tags"
        ]
        dependencies = {
            **authority["required_candidate_material_bindings"],
            **authority["reviewer_added_candidate_material_bindings"],
        }
        row["dependency_ids"] = sorted(dependencies)
        value["dependency_material_catalog"].update(dependencies)
        row["result"]["qualification_coverage"][
            "required_expertise_tags"
        ] = authority["required_expertise_tags"]
        row["result"]["review_dependencies"][
            "required_candidate_ids"
        ] = authority["required_candidate_ids"]
        row["result"]["review_dependencies"][
            "reviewer_added_candidate_ids_union"
        ] = authority["reviewer_added_candidate_ids_union"]
        metrics = row["result"]["evidence_metrics"]
        metrics["required_adjacency_candidate_count"] = (
            required_candidate_count
        )
        metrics["examined_adjacency_count"] = sum(
            vote["examined_adjacent_candidates"]["count"]
            for vote in row["votes"]
        )
        metrics["examined_required_adjacency_count"] = sum(
            vote["examined_adjacent_candidates"]["required_count"]
            for vote in row["votes"]
        )
    value["dependency_material_catalog"] = dict(
        sorted(value["dependency_material_catalog"].items())
    )
    claims = PANEL._professional_authenticated_claims_from_findings(
        value["findings"]
    )
    authorities = PANEL._professional_attestation_bindings_from_state(
        current_bindings=bindings,
        authenticated_claims=claims,
    )
    value = PANEL.panel_attestation.finalize_attestation(
        value,
        expected_professional_current_bindings=authorities,
    )
    return PANEL.panel_attestation.canonical_attestation_bytes(
        value,
        expected_professional_current_bindings=authorities,
    )


def _materialize_empty_capsule_chain(
    *,
    validation_root: Path,
    packet: dict,
    packet_sha256: str,
    state: object,
    voter_id: str,
    skill_ids: list[str],
) -> tuple[dict, Path, dict, Path, dict, Path]:
    round_root = validation_root / packet["review_id"]
    if validation_root.resolve() == PANEL.ROOT.resolve():
        round_root = (
            validation_root
            / ".rd-skills"
            / "expert-panel"
            / packet["review_id"]
        )
    discovery = PANEL.prepare_professional_discovery_capsule_v3(
        packet=packet,
        packet_sha256=packet_sha256,
        voter_id=voter_id,
        assigned_skill_ids=skill_ids,
        created_on="2026-07-17",
        validation_root=validation_root,
        validate_packet_plan=False,
        packet_state=state,
    )
    discovery_path = round_root / "discovery-capsules" / f"{voter_id}.json"
    discovery_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(discovery_path, discovery)
    request = PANEL.prepare_professional_candidate_request_v3(
        packet=packet,
        packet_sha256=packet_sha256,
        discovery_capsule_path=discovery_path,
        voter_id=voter_id,
        reviewer_added_requests_by_target=None,
        created_on="2026-07-17",
        validation_root=validation_root,
        validate_packet_plan=False,
        packet_state=state,
    )
    request_path = round_root / "candidate-requests" / f"{voter_id}.json"
    request_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(request_path, request)
    capsule = PANEL.prepare_professional_review_capsule_v3(
        packet=packet,
        packet_sha256=packet_sha256,
        discovery_capsule_path=discovery_path,
        candidate_request_path=request_path,
        voter_id=voter_id,
        created_on="2026-07-17",
        validation_root=validation_root,
        validate_packet_plan=False,
        packet_state=state,
    )
    capsule_path = round_root / "capsules" / f"{voter_id}.json"
    capsule_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(capsule_path, capsule)
    return discovery, discovery_path, request, request_path, capsule, capsule_path

def _anchor_phrase(
    anchor_id: str,
    *,
    vote: dict,
    materials_by_skill: dict,
) -> tuple[str, str]:
    anchors = {row["anchor_id"]: row for row in vote["evidence_anchors"]}
    sequences = PANEL._professional_v3_anchor_token_sequences(
        anchor_id,
        anchors_by_id=anchors,
        materials_by_skill=materials_by_skill,
    )
    phrase = next(sequence[:2] for sequence in sequences if len(sequence) >= 2)
    return phrase[0], phrase[1]

def _ground_schema3_vote(vote: dict, materials_by_skill: dict) -> None:
    """Make the generic schema-2 fixture satisfy the stricter schema-3 contract."""

    anchors_by_id = {
        anchor["anchor_id"]: anchor for anchor in vote["evidence_anchors"]
    }
    for anchor in vote["evidence_anchors"]:
        if any(
            len(sequence) >= 2
            for sequence in PANEL._professional_v3_anchor_token_sequences(
                anchor["anchor_id"],
                anchors_by_id=anchors_by_id,
                materials_by_skill=materials_by_skill,
            )
        ):
            continue
        line_count = len(
            materials_by_skill[anchor["skill_id"]][anchor["path"]][
                "content"
            ].splitlines()
        )
        candidates = (
            (max(1, anchor["start_line"] - 1), anchor["end_line"]),
            (anchor["start_line"], min(line_count, anchor["end_line"] + 1)),
        )
        for start_line, end_line in candidates:
            anchor["start_line"] = start_line
            anchor["end_line"] = end_line
            if any(
                len(sequence) >= 2
                for sequence in PANEL._professional_v3_anchor_token_sequences(
                    anchor["anchor_id"],
                    anchors_by_id=anchors_by_id,
                    materials_by_skill=materials_by_skill,
                )
            ):
                break
        else:
            raise AssertionError(
                f"test fixture anchor lacks a contiguous grounding phrase: {anchor['anchor_id']}"
            )

    for criterion, result in vote["criteria"].items():
        for assertion_index, assertion in enumerate(result["evidence_assertions"]):
            phrases = [
                _anchor_phrase(
                    anchor_id,
                    vote=vote,
                    materials_by_skill=materials_by_skill,
                )
                for anchor_id in assertion["evidence_anchor_ids"]
            ]
            exact = " and ".join(" ".join(phrase) for phrase in phrases)
            assertion["claim"] = (
                f"{exact} supports numbered finding {assertion_index} for "
                f"{criterion} under inspection."
            )
            assertion["source_excerpt_sha256"] = (
                PANEL._professional_assertion_excerpt_sha256(
                    assertion["evidence_anchor_ids"],
                    anchors_by_id=anchors_by_id,
                    materials_by_skill=materials_by_skill,
                )
            )
    for collection, item_name in (
        ("examined_failure_modes", "failure_mode"),
        ("examined_omission_candidates", "omission_candidate"),
    ):
        for index, item in enumerate(vote[collection]):
            phrases = [
                _anchor_phrase(
                    anchor_id,
                    vote=vote,
                    materials_by_skill=materials_by_skill,
                )
                for anchor_id in item["evidence_anchor_ids"]
            ]
            exact = " and ".join(" ".join(phrase) for phrase in phrases)
            item["rationale"] = (
                f"{exact} grounds this {item_name.replace('_', ' ')} outcome "
                f"through examined path {index}."
            )
    for index, candidate in enumerate(vote["examined_adjacent_candidates"]):
        target_phrase = _anchor_phrase(
            candidate["target_anchor_ids"][0],
            vote=vote,
            materials_by_skill=materials_by_skill,
        )
        candidate_phrase = _anchor_phrase(
            candidate["candidate_anchor_ids"][0],
            vote=vote,
            materials_by_skill=materials_by_skill,
        )
        candidate["rationale"] = (
            f"{' '.join(target_phrase)} defines the target boundary while "
            f"{' '.join(candidate_phrase)} defines the candidate boundary in "
            f"adjacency comparison {index}."
        )

@contextmanager
def _synthetic_schema1_professional_decision():
    packet = copy.deepcopy(_legacy_schema1_packet())
    packet["review_id"] = "schema-one-professional-fixture"
    with tempfile.TemporaryDirectory(dir=ROOT) as raw:
        root = Path(raw)
        packet_path = root / "packet.json"
        write_json(packet_path, packet)
        digest = hashlib.sha256(packet_path.read_bytes()).hexdigest()
        ballots = []
        for voter in range(1, 4):
            ballot = PANEL.prepare_professional_completeness_ballot_template(
                packet=packet,
                packet_sha256=digest,
                voter_id=f"schema-one-professional-voter-{voter}",
                agent_id=f"schema-one-professional-agent-{voter}",
                role=f"schema-one-professional-role-{voter}",
                expertise=["Professional completeness review."],
                expertise_tags=None,
                skill_ids=None,
                created_on="2026-08-10",
            )
            for vote in ballot["professional_votes"]:
                vote.update(
                    decision="accepted-current-professional-completeness",
                    reason_code="all-professional-criteria-satisfied",
                    rationale=(
                        "The synthetic package satisfies every bounded criterion."
                    ),
                )
                vote["criteria"] = {
                    criterion: "satisfied"
                    for criterion in sorted(PANEL.PROFESSIONAL_COMPLETENESS_CRITERIA)
                }
            ballot_path = root / f"schema-one-voter-{voter}.json"
            write_json(ballot_path, ballot)
            ballots.append((ballot_path, ballot))
        decision = PANEL.aggregate_ballots(
            packet=packet,
            packet_path=packet_path,
            ballot_values=ballots,
            decided_on="2026-08-10",
        )
        decision_path = root / "decision.json"
        write_json(decision_path, decision)
        yield packet, packet_path, ballots, decision, decision_path

@contextmanager
def _synthetic_schema3_professional_decision(
    *, mutate_registered_selection: bool = False
):
    """Materialize one minimal 189-package decision without checked-in history."""

    content = "\n".join(
        [
            "# Synthetic Professional Boundary",
            "Authority boundaries reject ambiguous ownership transitions.",
            "Input contracts require explicit source authority evidence.",
            "Output contracts identify deterministic verification signals.",
            "Failure handling preserves actionable rejection context.",
            "Omission review examines material responsibility gaps.",
            "Boundary review covers invalid state transitions safely.",
            "Verification methods distinguish behavior from harness health.",
            "Reference coverage records high risk decisions explicitly.",
            "Adjacent ownership analysis prevents hidden routing overlap.",
            "Professional correctness excludes unsupported operational claims.",
            "Proof limits bound static evidence conclusions carefully.",
        ]
    )
    responsibility = {
        "role_support": ["task-agent"],
        "trigger_signals": ["synthetic professional review"],
        "anti_trigger_signals": ["unbounded synthetic work"],
        "required_inputs": ["bounded synthetic authority"],
        "output_contract": ["validated synthetic decision"],
        "escalation_signals": ["synthetic authority mismatch"],
        "layer3_candidates": [],
        "used_by": [],
        "boundary_signals": ["synthetic fixture boundary"],
        "group": "engineering",
        "content_class": "professional",
        "delivery_scope": "test-only",
        "task_routable": True,
    }
    target_specs = sorted(
        (f"synthetic-professional-{index:03d}", "professional")
        for index in range(26)
    ) + sorted(
        (f"synthetic-foundation-{index:03d}", "foundation")
        for index in range(150)
    ) + sorted(
        (f"synthetic-domain-{index:03d}", "domain")
        for index in range(13)
    )
    target_specs.sort()
    targets = []
    for skill_id, layer in target_specs:
        material = {
            "path": f"{skill_id}/SKILL.md",
            "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "line_count": len(content.splitlines()),
            "content": content,
        }
        targets.append(
            {
                "skill_id": skill_id,
                "layer": layer,
                "required_expertise_tags": ["foundation-quality-testing"],
                "root": material,
                "indexed_references": [],
                "registry": {
                    "path": "synthetic-registry.yaml",
                    "entry_fingerprint": hashlib.sha256(
                        skill_id.encode("utf-8")
                    ).hexdigest(),
                    "responsibility_contract": copy.deepcopy(
                        responsibility
                    ),
                },
            }
        )
    with (
        mock.patch.object(
            PANEL, "PROFESSIONAL_ADJACENCY_TOP_K", 0
        ),
        mock.patch.object(
            PANEL, "PROFESSIONAL_ADJACENCY_PER_SIGNAL_TOP_K", 0
        ),
        tempfile.TemporaryDirectory() as raw,
    ):
        bases, document_filter = (
            PANEL._professional_catalog_adjacency_features(
                targets,
                include_historical_alias=True,
            )
        )
        for target in targets:
            ranking = PANEL._professional_catalog_ranking(
                target["skill_id"], bases=bases
            )
            required_candidates = (
                PANEL._professional_required_adjacency_candidates(
                    ranking,
                    registry_declared_skills=[],
                    source_declared_skills=[],
                )
            )
            target["routing_adjacency"] = {
                "algorithm": PANEL.PROFESSIONAL_ADJACENCY_ALGORITHM,
                "document_frequency_filter": document_filter,
                "declared_skills": [],
                "registry_declared_skills": [],
                "source_declared_skills": [],
                "required_candidate_selection": (
                    PANEL._professional_adjacency_selection_contract(
                        target_count=PANEL.PROFESSIONAL_PACKAGE_COUNT
                    )
                ),
                "required_candidates": required_candidates,
                "required_candidates_fingerprint": (
                    PANEL._canonical_json_sha256(required_candidates)
                ),
                "full_catalog_count": len(ranking),
                "full_catalog_ranking": ranking,
                "full_catalog_ranking_fingerprint": (
                    PANEL._canonical_json_sha256(ranking)
                ),
            }
        review_contract = (
            PANEL._professional_evidence_review_contract_fingerprint()
        )
        bindings, snapshot = PANEL._professional_v3_binding_state(
            targets, review_contract_fingerprint=review_contract
        )
        packet = {
            "schema_version": (
                PANEL.PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
            ),
            "kind": PANEL.PROFESSIONAL_COMPLETENESS_PACKET_KIND,
            "review_id": "synthetic-professional-history-r1",
            "created_on": "2026-07-17",
            "review_contract_fingerprint": review_contract,
            "panel_contract": PANEL._professional_v3_panel_contract(
                target_count=PANEL.PROFESSIONAL_PACKAGE_COUNT
            ),
            "rubric": PANEL._professional_v3_rubric(),
            "professional_targets": [
                {
                    **copy.deepcopy(target),
                    "review_binding": copy.deepcopy(
                        snapshot["targets"][target["skill_id"]]
                    ),
                }
                for target in targets
            ],
            "review_plan": PANEL._professional_v3_review_plan(
                current_bindings=bindings,
                review_contract_fingerprint=review_contract,
                baseline_state=None,
            ),
            "limitations": PANEL._professional_v3_packet_limitations(),
        }
        validation_mode = (
            PANEL.VALIDATION_MODE_HISTORICAL
            if mutate_registered_selection
            else PANEL.VALIDATION_MODE_CURRENT
        )
        if mutate_registered_selection:
            selections = [
                packet["panel_contract"]["adjacency_contract"][
                    "required_candidate_selection"
                ]
            ]
            selections.extend(
                target["routing_adjacency"]["required_candidate_selection"]
                for target in packet["professional_targets"]
            )
            for selection in selections:
                selection["overall_top_k"] += 1
                selection["per_signal_top_k"] += 1
            for target in packet["professional_targets"]:
                adjacency = target["routing_adjacency"]
                selection = adjacency["required_candidate_selection"]
                required_candidates = (
                    PANEL._professional_required_adjacency_candidates(
                        adjacency["full_catalog_ranking"],
                        registry_declared_skills=adjacency[
                            "registry_declared_skills"
                        ],
                        source_declared_skills=adjacency[
                            "source_declared_skills"
                        ],
                        overall_top_k=selection["overall_top_k"],
                        per_signal_top_k=selection["per_signal_top_k"],
                    )
                )
                adjacency["required_candidates"] = required_candidates
                adjacency["required_candidates_fingerprint"] = (
                    PANEL._canonical_json_sha256(required_candidates)
                )
            base_targets = PANEL._professional_v3_base_targets(
                packet["professional_targets"]
            )
            bindings, snapshot = PANEL._professional_v3_binding_state(
                base_targets,
                review_contract_fingerprint=review_contract,
            )
            for target in packet["professional_targets"]:
                target["review_binding"] = copy.deepcopy(
                    snapshot["targets"][target["skill_id"]]
                )
            packet["review_plan"] = PANEL._professional_v3_review_plan(
                current_bindings=bindings,
                review_contract_fingerprint=review_contract,
                baseline_state=None,
            )
        state = PANEL._professional_v3_packet_state(
            packet,
            validation_root=ROOT,
            artifact_path=None,
            validate_baseline=False,
            validation_mode=validation_mode,
        )
        if mutate_registered_selection:
            yield {
                "validation_root": ROOT,
                "packet": packet,
                "state": state,
            }
            return
        skill_ids = sorted(state["bindings"])
        projected = PANEL._professional_v2_projection_from_v3(
            packet, validation_mode=validation_mode
        )
        validation_root = Path(raw)
        round_root = validation_root / packet["review_id"]
        packet_path = round_root / "packet.json"
        packet_path.parent.mkdir(parents=True)
        write_json(packet_path, packet)
        packet_sha256 = hashlib.sha256(packet_path.read_bytes()).hexdigest()
        ballots = []
        for voter in range(1, 4):
            voter_id = f"professional-expert-{voter}"
            (
                _discovery,
                _discovery_path,
                _request,
                _request_path,
                capsule,
                capsule_path,
            ) = _materialize_empty_capsule_chain(
                validation_root=validation_root,
                packet=packet,
                packet_sha256=packet_sha256,
                state=state,
                voter_id=voter_id,
                skill_ids=skill_ids,
            )
            capsule_ref = PANEL._artifact_reference(
                capsule_path,
                validation_root=validation_root,
                kind=PANEL.PROFESSIONAL_COMPLETENESS_CAPSULE_KIND,
                axis=PANEL.PROFESSIONAL_COMPLETENESS_ARTIFACT_AXIS,
                review_id=packet["review_id"],
            )
            ballot = _professional_ballot(
                projected,
                packet_sha256,
                voter=voter,
                skill_ids=skill_ids,
            )
            ballot["schema_version"] = (
                PANEL.PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
            )
            ballot.pop("source_fingerprints")
            ballot["review_contract_fingerprint"] = packet[
                "review_contract_fingerprint"
            ]
            ballot["capsule"] = capsule_ref
            scoped_materials = (
                PANEL._professional_v3_target_scoped_capsule_materials(capsule)
            )
            for vote in ballot["professional_votes"]:
                _ground_schema3_vote(
                    vote,
                    scoped_materials[vote["skill_id"]],
                )
            ballot_path = round_root / "panel" / f"{voter_id}.json"
            ballot_path.parent.mkdir(parents=True, exist_ok=True)
            write_json(ballot_path, ballot)
            ballots.append((ballot_path, ballot))

        decision = PANEL.aggregate_ballots(
            packet=packet,
            packet_path=packet_path,
            ballot_values=ballots,
            decided_on="2026-07-17",
            validation_root=validation_root,
            validation_mode=validation_mode,
        )
        decision_path = round_root / "panel" / "decision.json"
        write_json(decision_path, decision)
        PANEL.validate_decision_record(
            decision,
            record_path=decision_path,
            validation_root=validation_root,
            validation_mode=validation_mode,
        )
        yield {
            "validation_root": validation_root,
            "packet": packet,
            "packet_path": packet_path,
            "ballots": ballots,
            "decision": decision,
            "decision_path": decision_path,
        }

@functools.lru_cache(maxsize=1)
def _professional_packet_cached() -> dict:
    return PANEL.prepare_professional_completeness_packet(
        review_id="professional-review-1",
        created_on="2026-07-16",
    )

def _professional_packet() -> dict:
    return copy.deepcopy(_professional_packet_cached())

def _fixture_evidence_lines(material: dict, count: int) -> list[tuple[int, list[str]]]:
    rows = []
    for line_number, line in enumerate(material["content"].splitlines(), start=1):
        tokens = sorted(PANEL._evidence_tokens(line))
        if (
            PANEL._is_substantive_markdown_line(material["content"], line_number)
            and len(tokens) >= 2
        ):
            rows.append((line_number, tokens))
        if len(rows) == count:
            return rows
    raise AssertionError(f"fixture material lacks {count} substantive evidence lines")

def _fixture_anchor(
    *, skill_id: str, material: dict, anchor_id: str, line_number: int
) -> dict:
    return {
        "anchor_id": anchor_id,
        "skill_id": skill_id,
        "path": material["path"],
        "start_line": line_number,
        "end_line": line_number,
    }

def _fixture_anchor_tokens(
    anchor: dict, materials_by_skill: dict[str, dict[str, dict]]
) -> list[str]:
    material = materials_by_skill[anchor["skill_id"]][anchor["path"]]
    line = material["content"].splitlines()[anchor["start_line"] - 1]
    return sorted(PANEL._evidence_tokens(line))

def _professional_ballot(
    packet: dict,
    packet_sha256: str,
    *,
    voter: int,
    correction_skill: str | None = None,
    correction_criterion: str = "professional-correctness",
    skill_ids: list[str] | None = None,
    reviewer_kind: str | None = None,
) -> dict:
    votes = []
    materials_by_skill = PANEL._professional_materials_by_skill(packet)
    targets_by_id = {
        target["skill_id"]: target for target in packet["professional_targets"]
    }
    selected_skill_ids = (
        {target["skill_id"] for target in packet["professional_targets"]}
        if skill_ids is None
        else set(skill_ids)
    )
    for target in packet["professional_targets"]:
        if target["skill_id"] not in selected_skill_ids:
            continue
        correction = target["skill_id"] == correction_skill
        criterion_names = sorted(PANEL.PROFESSIONAL_COMPLETENESS_CRITERIA)
        root_lines = iter(_fixture_evidence_lines(target["root"], len(criterion_names)))
        anchors = []
        criterion_anchor_ids = {}
        for criterion_index, criterion in enumerate(criterion_names):
            material = target["root"]
            line_number, _tokens = next(root_lines)
            if (
                criterion == "reference-high-risk-coverage"
                and target["indexed_references"]
            ):
                material = target["indexed_references"][0]
                line_number, _tokens = _fixture_evidence_lines(material, 1)[0]
            anchor_id = f"criterion-{criterion_index:02d}"
            anchors.append(
                _fixture_anchor(
                    skill_id=target["skill_id"],
                    material=material,
                    anchor_id=anchor_id,
                    line_number=line_number,
                )
            )
            criterion_anchor_ids[criterion] = anchor_id

        adjacency_target_anchor_id = criterion_anchor_ids[
            "adjacent-overlap-or-gap"
        ]
        for candidate_index, candidate in enumerate(
            target["routing_adjacency"]["required_candidates"]
        ):
            candidate_target = targets_by_id[candidate["skill_id"]]
            candidate_line, _tokens = _fixture_evidence_lines(
                candidate_target["root"], 1
            )[0]
            anchors.append(
                _fixture_anchor(
                    skill_id=candidate["skill_id"],
                    material=candidate_target["root"],
                    anchor_id=f"candidate-{candidate_index:03d}",
                    line_number=candidate_line,
                )
            )
        anchors.sort(key=lambda row: row["anchor_id"])
        anchors_by_id = {anchor["anchor_id"]: anchor for anchor in anchors}

        criteria = {}
        for criterion_index, criterion in enumerate(criterion_names):
            anchor_id = criterion_anchor_ids[criterion]
            tokens = _fixture_anchor_tokens(
                anchors_by_id[anchor_id], materials_by_skill
            )
            assertion = {
                "claim": (
                    f"Criterion {criterion_index} binds {tokens[0]} and {tokens[1]} "
                    "to one bounded professional decision."
                ),
                "evidence_anchor_ids": [anchor_id],
                "source_excerpt_sha256": (
                    PANEL._professional_assertion_excerpt_sha256(
                        [anchor_id],
                        anchors_by_id=anchors_by_id,
                        materials_by_skill=materials_by_skill,
                    )
                ),
            }
            criteria[criterion] = {
                "status": "satisfied",
                "evidence_assertions": [assertion],
            }
        if correction:
            criteria[correction_criterion]["status"] = "defect-found"

        def examined_items(
            *, item_field: str, anchor_names: list[str], kind: str
        ) -> list[dict]:
            items = []
            for item_index, anchor_id in enumerate(anchor_names, start=1):
                tokens = _fixture_anchor_tokens(
                    anchors_by_id[anchor_id], materials_by_skill
                )
                items.append(
                    {
                        item_field: (
                            f"{item_index:02d}-{kind}-{tokens[0]}-{tokens[1]}"
                        ),
                        "outcome": "covered",
                        "evidence_anchor_ids": [anchor_id],
                        "rationale": (
                            f"The {tokens[0]} and {tokens[1]} rules bound this "
                            f"examined {kind} decision path."
                        ),
                    }
                )
            return sorted(items, key=lambda item: item[item_field])

        failure_modes = examined_items(
            item_field="failure_mode",
            anchor_names=[
                criterion_anchor_ids["failure-modes"],
                criterion_anchor_ids["boundary-conditions"],
            ],
            kind="failure-mode",
        )
        omission_candidates = examined_items(
            item_field="omission_candidate",
            anchor_names=[
                criterion_anchor_ids["material-omissions"],
                criterion_anchor_ids["verification-methods"],
            ],
            kind="omission-candidate",
        )
        if correction and correction_criterion == "failure-modes":
            failure_modes[0]["outcome"] = "defect-found"
        if correction and correction_criterion == "material-omissions":
            omission_candidates[0]["outcome"] = "defect-found"

        adjacency_reviews = []
        target_tokens = _fixture_anchor_tokens(
            anchors_by_id[adjacency_target_anchor_id], materials_by_skill
        )
        for candidate_index, candidate in enumerate(
            target["routing_adjacency"]["required_candidates"]
        ):
            candidate_anchor_id = f"candidate-{candidate_index:03d}"
            candidate_tokens = _fixture_anchor_tokens(
                anchors_by_id[candidate_anchor_id], materials_by_skill
            )
            adjacency_reviews.append(
                {
                    "skill_id": candidate["skill_id"],
                    "review_origin": "packet-required",
                    "discovery_reason": None,
                    "disposition": (
                        "adjacent-no-gap"
                        if candidate["declared"]
                        else "not-adjacent"
                    ),
                    "target_anchor_ids": [adjacency_target_anchor_id],
                    "candidate_anchor_ids": [candidate_anchor_id],
                    "rationale": (
                        f"The {target_tokens[0]} target boundary and "
                        f"{candidate_tokens[0]} candidate boundary were compared "
                        "for hidden responsibility gaps."
                    ),
                }
            )
        if correction and correction_criterion == "adjacent-overlap-or-gap":
            adjacency_reviews[0]["disposition"] = "gap-or-overlap-defect"
        votes.append(
            {
                "skill_id": target["skill_id"],
                "decision": (
                    "requires-professional-correction"
                    if correction
                    else "accepted-current-professional-completeness"
                ),
                "reason_code": (
                    {
                        "professional-correctness": "professional-correctness-defect",
                        "erroneous-rules": "erroneous-professional-rule",
                        "material-omissions": "material-professional-omission",
                        "failure-modes": "failure-mode-gap",
                        "boundary-conditions": "boundary-condition-gap",
                        "verification-methods": "verification-method-gap",
                        "adjacent-overlap-or-gap": "adjacent-responsibility-gap",
                        "generic-knowledge-pollution": "generic-knowledge-pollution",
                        "reference-high-risk-coverage": "reference-high-risk-coverage-gap",
                        "output-verifiability": "output-verification-gap",
                    }[correction_criterion]
                    if correction
                    else "all-professional-criteria-satisfied"
                ),
                "evidence_anchors": anchors,
                "criteria": criteria,
                "examined_failure_modes": failure_modes,
                "examined_omission_candidates": omission_candidates,
                "examined_adjacent_candidates": adjacency_reviews,
                "proof_limits": [
                    "Static source review cannot prove production runtime behavior."
                ],
                "rationale": (
                    "This package contains a professional correctness defect requiring correction."
                    if correction
                    else "Every required professional completeness criterion is satisfied for this package."
                ),
            }
        )
    effective_reviewer_kind = reviewer_kind or (
        "domain" if voter < 3 else "architecture"
    )
    expertise_tags = (
        sorted(
            {
                tag
                for target in packet["professional_targets"]
                if target["skill_id"] in selected_skill_ids
                for tag in target["required_expertise_tags"]
            }
        )
        if effective_reviewer_kind == "domain"
        else [PANEL.PROFESSIONAL_ARCHITECTURE_EXPERTISE_TAG]
    )
    return {
        "schema_version": PANEL.PROFESSIONAL_COMPLETENESS_SCHEMA_VERSION,
        "kind": PANEL.PROFESSIONAL_COMPLETENESS_BALLOT_KIND,
        "review_id": packet["review_id"],
        "created_on": "2026-07-16",
        "packet_sha256": packet_sha256,
        **(
            {"source_fingerprints": copy.deepcopy(packet["source_fingerprints"])}
            if packet["schema_version"]
            != PANEL.PROFESSIONAL_COMPLETENESS_INCREMENTAL_SCHEMA_VERSION
            else {}
        ),
        "voter": {
            "voter_id": f"professional-expert-{voter}",
            "agent_id": f"professional-agent-{voter}",
            "role": f"senior-professional-role-{voter}",
            "expertise": ["professional completeness review"],
            "expertise_tags": expertise_tags,
            "qualification_claims": [
                {
                    "expertise_tag": tag,
                    "qualification_basis": (
                        f"Reviewer declares bounded prior work in {tag} "
                        "professional decision reviews."
                    ),
                    "proof_limit": (
                        f"This static {tag} declaration cannot verify external "
                        "identity credentials or experience."
                    ),
                }
                for tag in expertise_tags
            ],
            "independent_review": True,
        },
        "professional_votes": votes,
        "limitations": ["Static professional fixture vote."],
    }
