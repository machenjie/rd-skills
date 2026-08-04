#!/usr/bin/env python3
"""Pure Professional Completeness binding, carry, and capsule helpers.

This module intentionally has no CLI and does not import ``expert_panel_review``.
The panel module owns artifact schemas and validation; this module owns only
canonical projections that future incremental review can reuse without creating
an import cycle or adding more stateful behavior to the panel module.
"""

from __future__ import annotations

import ast
import builtins
import copy
import functools
import hashlib
import inspect
import json
import operator
import re
import symtable
import typing
import types
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence


ACCEPTED_PROFESSIONAL_DISPOSITION = (
    "accepted-current-professional-completeness"
)
PROFESSIONAL_CARRY_CONTRACT = {
    "carry_unit": "whole-professional-package",
    "baseline_requirement": "exact-prior-target-snapshot",
    "review_contract_requirement": "exact-fingerprint-match",
    "dependency_depth": "one-hop-factual-material",
    "required_dependency_sources": [
        "packet-required-candidate",
        "reviewer-added-candidate-union-from-all-prior-target-ballots",
    ],
    "candidate_material_excludes": [
        "package_fingerprint",
        "routing_adjacency",
    ],
    "fresh_state_is_not_a_dependency": True,
    "accepted_prior_disposition": ACCEPTED_PROFESSIONAL_DISPOSITION,
}
PROFESSIONAL_CAPSULE_CONTRACT = {
    "projection": "final-assigned-fresh-target-review-capsule",
    "target_material": "complete-own-material-registry-expertise",
    "adjacency_metadata": "complete-full-ranking-and-required-selection",
    "candidate_material": "complete-material-without-candidate-ranking",
    "candidate_origins": ["packet-required", "reviewer-added"],
    "reviewer_added_source": "validated-immutable-candidate-request",
    "predecessor": "immutable-discovery-capsule",
    "material_storage": "top-level-skill-deduplicated-catalog",
    "closed_projection": True,
}
PROFESSIONAL_DISCOVERY_CAPSULE_CONTRACT = {
    "projection": "assigned-fresh-target-discovery-capsule",
    "target_material": "complete-own-material-registry-expertise",
    "required_candidate_material": "complete-material-without-candidate-ranking",
    "adjacency_metadata": "complete-full-ranking-and-required-selection",
    "candidate_boundary_catalog": "complete-lightweight-catalog",
    "candidate_request": "separate-immutable-artifact-required",
    "material_storage": "top-level-skill-deduplicated-catalog",
    "closed_projection": True,
}

_MATERIAL_RECORD_FIELDS = {"path", "sha256", "line_count", "content"}
_ADJACENCY_REVIEW_BINDING_FIELDS = {
    "algorithm",
    "declared_skills",
    "required_candidate_selection",
    "required_candidates",
    "required_candidates_fingerprint",
    "full_catalog_count",
    "full_catalog_ranking",
    "full_catalog_ranking_fingerprint",
}
_TARGET_BINDING_FIELDS = {
    "skill_id",
    "layer",
    "own_material",
    "own_material_fingerprint",
    "registry",
    "registry_fingerprint",
    "required_expertise_tags",
    "required_expertise_fingerprint",
    "adjacency",
    "adjacency_fingerprint",
    "candidate_material_fingerprint",
    "required_candidate_material_bindings",
    "review_binding_fingerprint",
}
_SNAPSHOT_TARGET_FIELDS = {
    "skill_id",
    "layer",
    "own_material_fingerprint",
    "registry_fingerprint",
    "required_expertise_fingerprint",
    "adjacency_fingerprint",
    "candidate_material_fingerprint",
    "required_candidate_material_bindings",
    "review_binding_fingerprint",
}
_DECISION_DEPENDENCY_FIELDS = {
    "skill_id",
    "final_disposition",
    "evidence_complete",
    "prior_target_vote_count",
    "required_candidate_ids",
    "reviewer_added_candidate_ids_union",
    "dependency_candidate_ids",
}
_CAPSULE_FIELDS = {
    "projection_contract",
    "assigned_fresh_target_ids",
    "material_catalog",
    "targets",
}
_CAPSULE_TARGET_FIELDS = {
    "skill_id",
    "source_review_binding_fingerprint",
    "adjacency",
    "candidate_material_manifest",
}
_CAPSULE_MANIFEST_FIELDS = {
    "skill_id",
    "review_origin",
    "discovery_reason",
    "material_fingerprint",
}
_DISCOVERY_CAPSULE_FIELDS = {
    "projection_contract",
    "assigned_fresh_target_ids",
    "material_catalog",
    "boundary_catalog",
    "targets",
}
_DISCOVERY_CAPSULE_TARGET_FIELDS = {
    "skill_id",
    "source_review_binding_fingerprint",
    "adjacency",
    "required_candidate_material_manifest",
}
_DISCOVERY_BOUNDARY_FIELDS = {
    "skill_id",
    "layer",
    "responsibility_contract",
    "required_expertise_tags",
    "material_fingerprint",
}
_REVIEWER_ADDED_REQUEST_FIELDS = {
    "skill_id",
    "discovery_reason",
    "ranking_evidence",
    "material_fingerprint",
}


class ProfessionalCarryForwardError(ValueError):
    """Raised when an internal carry or capsule projection is not canonical."""


def canonical_json_bytes(value: object) -> bytes:
    """Return deterministic UTF-8 JSON bytes without claiming artifact status."""

    try:
        rendered = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise ProfessionalCarryForwardError(
            "value is not canonical-JSON serializable"
        ) from exc
    return rendered.encode("utf-8")


def canonical_json_sha256(value: object) -> str:
    """Hash the canonical bytes used by every helper in this module."""

    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _is_sha256(value: object) -> bool:
    return bool(
        isinstance(value, str)
        and re.fullmatch(r"[0-9a-f]{64}", value)
    )


def _require_sha256(value: object, *, label: str) -> str:
    if not _is_sha256(value):
        raise ProfessionalCarryForwardError(
            f"{label} must be a lowercase SHA-256 digest"
        )
    return str(value)


def _require_skill_id(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProfessionalCarryForwardError(f"{label} must be non-empty")
    return value


def _sorted_unique_strings(value: object, *, label: str) -> list[str]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise ProfessionalCarryForwardError(f"{label} must be a string array")
    if value != sorted(set(value)):
        raise ProfessionalCarryForwardError(
            f"{label} must be sorted and unique"
        )
    return list(value)


def _is_canonical_repository_path(value: object) -> bool:
    return bool(
        isinstance(value, str)
        and value
        and "\\" not in value
        and not PurePosixPath(value).is_absolute()
        and PurePosixPath(value).as_posix() == value
        and all(part not in {"", ".", ".."} for part in value.split("/"))
    )


def _canonical_material_record(value: object, *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != _MATERIAL_RECORD_FIELDS:
        raise ProfessionalCarryForwardError(
            f"{label} must be one complete review-material record"
        )
    path = value.get("path")
    content = value.get("content")
    line_count = value.get("line_count")
    digest = _require_sha256(value.get("sha256"), label=f"{label}.sha256")
    if not _is_canonical_repository_path(path):
        raise ProfessionalCarryForwardError(
            f"{label}.path must be repository-relative"
        )
    if not isinstance(content, str):
        raise ProfessionalCarryForwardError(f"{label}.content must be text")
    if type(line_count) is not int or line_count != len(content.splitlines()):
        raise ProfessionalCarryForwardError(
            f"{label}.line_count must match content"
        )
    if hashlib.sha256(content.encode("utf-8")).hexdigest() != digest:
        raise ProfessionalCarryForwardError(
            f"{label}.sha256 must bind content"
        )
    return copy.deepcopy(value)


def professional_materials_by_skill(
    targets: Sequence[dict[str, Any]],
) -> dict[str, dict[str, dict[str, Any]]]:
    """Index target-owned root and Reference records for review validation.

    This intentionally preserves the legacy panel helper's projection: it does
    not copy or add fields, so existing ballot validation behavior and packet
    serialization remain unchanged.
    """

    return {
        target["skill_id"]: {
            target["root"]["path"]: target["root"],
            **{
                reference["path"]: reference
                for reference in target["indexed_references"]
            },
        }
        for target in targets
    }


def professional_own_material_binding(
    target: Mapping[str, Any],
) -> dict[str, Any]:
    """Project exactly the target's root and indexed Reference material."""

    return _canonical_own_material_binding(
        {
            "root": target.get("root"),
            "indexed_references": target.get("indexed_references"),
        },
        label=str(target.get("skill_id", "target")),
    )


def _canonical_own_material_binding(
    value: object, *, label: str
) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != {
        "root",
        "indexed_references",
    }:
        raise ProfessionalCarryForwardError(
            f"{label} own material fields are not canonical"
        )
    root = _canonical_material_record(value.get("root"), label=f"{label}.root")
    references_raw = value.get("indexed_references")
    if not isinstance(references_raw, list):
        raise ProfessionalCarryForwardError(
            "target.indexed_references must be an array"
        )
    references = [
        _canonical_material_record(
            reference,
            label=f"{label}.indexed_references[{index}]",
        )
        for index, reference in enumerate(references_raw)
    ]
    reference_paths = [item["path"] for item in references]
    if reference_paths != sorted(set(reference_paths)):
        raise ProfessionalCarryForwardError(
            "target indexed References must be path-sorted and unique"
        )
    if root["path"] in set(reference_paths):
        raise ProfessionalCarryForwardError(
            "target root path must not duplicate an indexed Reference path"
        )
    return {"root": root, "indexed_references": references}


def professional_registry_responsibility_binding(
    target: Mapping[str, Any],
) -> dict[str, Any]:
    """Project the Registry entry digest and embedded responsibility contract."""

    registry = target.get("registry")
    if not isinstance(registry, dict) or set(registry) != {
        "path",
        "entry_fingerprint",
        "responsibility_contract",
    }:
        raise ProfessionalCarryForwardError(
            "target.registry must contain the canonical Registry binding"
        )
    if not _is_canonical_repository_path(registry.get("path")):
        raise ProfessionalCarryForwardError(
            "target.registry.path must be non-empty"
        )
    _require_sha256(
        registry.get("entry_fingerprint"),
        label="target.registry.entry_fingerprint",
    )
    if not isinstance(registry.get("responsibility_contract"), dict):
        raise ProfessionalCarryForwardError(
            "target.registry.responsibility_contract must be an object"
        )
    return copy.deepcopy(registry)


def professional_required_expertise_binding(
    target: Mapping[str, Any],
) -> list[str]:
    """Project the exact closed expertise requirement for one target."""

    return _sorted_unique_strings(
        target.get("required_expertise_tags"),
        label="target.required_expertise_tags",
    )


def professional_adjacency_review_binding(
    target: Mapping[str, Any],
) -> dict[str, Any]:
    """Project target-visible ranking results and their stable selection contract.

    The packet's ``document_frequency_filter`` is a catalog-wide generation
    intermediate.  Binding its shared fingerprint here would make one local
    token change stale all 189 targets even when their own ranking and required
    candidates are unchanged.  The generated ranking/result still binds every
    review-visible consequence of that intermediate.
    """

    adjacency = target.get("routing_adjacency")
    if not isinstance(adjacency, dict):
        raise ProfessionalCarryForwardError(
            "target.routing_adjacency must be an object"
        )
    required = adjacency.get("required_candidates")
    ranking = adjacency.get("full_catalog_ranking")
    selection = adjacency.get("required_candidate_selection")
    if not isinstance(required, list) or not isinstance(ranking, list):
        raise ProfessionalCarryForwardError(
            "target adjacency must bind required candidates and full ranking"
        )
    if not isinstance(selection, dict):
        raise ProfessionalCarryForwardError(
            "target adjacency must bind its required-candidate selection contract"
        )
    required_ids = [
        _require_skill_id(item.get("skill_id"), label="required candidate skill_id")
        if isinstance(item, dict)
        else _raise_invalid_candidate("required candidate")
        for item in required
    ]
    ranking_ids = [
        _require_skill_id(item.get("skill_id"), label="ranking candidate skill_id")
        if isinstance(item, dict)
        else _raise_invalid_candidate("ranking candidate")
        for item in ranking
    ]
    if required_ids != sorted(set(required_ids)):
        raise ProfessionalCarryForwardError(
            "required adjacency candidates must be skill-sorted and unique"
        )
    if len(ranking_ids) != len(set(ranking_ids)):
        raise ProfessionalCarryForwardError(
            "full catalog ranking must contain unique Skill IDs"
        )
    if not set(required_ids) <= set(ranking_ids):
        raise ProfessionalCarryForwardError(
            "required adjacency candidates must be present in full ranking"
        )
    if adjacency.get("full_catalog_count") != len(ranking):
        raise ProfessionalCarryForwardError(
            "full catalog count must match embedded ranking"
        )
    if adjacency.get("full_catalog_ranking_fingerprint") != canonical_json_sha256(
        ranking
    ):
        raise ProfessionalCarryForwardError(
            "full catalog ranking fingerprint is stale"
        )
    if adjacency.get("required_candidates_fingerprint") != canonical_json_sha256(
        required
    ):
        raise ProfessionalCarryForwardError(
            "required candidate fingerprint is stale"
        )
    missing = sorted(_ADJACENCY_REVIEW_BINDING_FIELDS - set(adjacency))
    if missing:
        raise ProfessionalCarryForwardError(
            "target adjacency lacks review-visible fields: " + ", ".join(missing)
        )
    return {
        field: copy.deepcopy(adjacency[field])
        for field in sorted(_ADJACENCY_REVIEW_BINDING_FIELDS)
    }


def _raise_invalid_candidate(label: str) -> str:
    raise ProfessionalCarryForwardError(f"{label} must be an object")


def professional_candidate_material_binding(
    target: Mapping[str, Any],
) -> dict[str, Any]:
    """Project complete candidate material while deliberately excluding ranking.

    A candidate's adjacency/ranking is not review material for another target.
    Excluding it prevents a ranking-only change from recursively invalidating
    every target that reviewed this candidate.
    """

    skill_id = _require_skill_id(target.get("skill_id"), label="target.skill_id")
    layer = _require_skill_id(target.get("layer"), label=f"{skill_id}.layer")
    return {
        "skill_id": skill_id,
        "layer": layer,
        "own_material": professional_own_material_binding(target),
        "registry": professional_registry_responsibility_binding(target),
        "required_expertise_tags": professional_required_expertise_binding(target),
    }


def _canonical_target_index(
    targets: Sequence[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    if not isinstance(targets, Sequence) or isinstance(targets, (str, bytes)):
        raise ProfessionalCarryForwardError("targets must be an array")
    index: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for position, target in enumerate(targets):
        if not isinstance(target, dict):
            raise ProfessionalCarryForwardError(
                f"targets[{position}] must be an object"
            )
        skill_id = _require_skill_id(
            target.get("skill_id"), label=f"targets[{position}].skill_id"
        )
        if skill_id in index:
            raise ProfessionalCarryForwardError(
                f"duplicate target Skill ID: {skill_id}"
            )
        index[skill_id] = target
        order.append(skill_id)
    if order != sorted(order):
        raise ProfessionalCarryForwardError("targets must be skill-sorted")
    return index


def professional_review_bindings(
    targets: Sequence[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Build canonical per-target review and one-hop material bindings."""

    target_index = _canonical_target_index(targets)
    candidate_materials = {
        skill_id: professional_candidate_material_binding(target)
        for skill_id, target in target_index.items()
    }
    candidate_fingerprints = {
        skill_id: canonical_json_sha256(material)
        for skill_id, material in candidate_materials.items()
    }
    bindings: dict[str, dict[str, Any]] = {}
    for skill_id in sorted(target_index):
        target = target_index[skill_id]
        own_material = candidate_materials[skill_id]["own_material"]
        registry = candidate_materials[skill_id]["registry"]
        expertise = candidate_materials[skill_id]["required_expertise_tags"]
        adjacency = professional_adjacency_review_binding(target)
        required_ids = [
            candidate["skill_id"]
            for candidate in adjacency["required_candidates"]
        ]
        unknown = sorted(set(required_ids) - set(target_index))
        if unknown:
            raise ProfessionalCarryForwardError(
                f"{skill_id} requires unknown adjacency candidates: "
                + ", ".join(unknown)
            )
        required_material_bindings = [
            {
                "skill_id": candidate_id,
                "material_fingerprint": candidate_fingerprints[candidate_id],
            }
            for candidate_id in required_ids
        ]
        binding: dict[str, Any] = {
            "skill_id": skill_id,
            "layer": candidate_materials[skill_id]["layer"],
            "own_material": own_material,
            "own_material_fingerprint": canonical_json_sha256(own_material),
            "registry": registry,
            "registry_fingerprint": canonical_json_sha256(registry),
            "required_expertise_tags": expertise,
            "required_expertise_fingerprint": canonical_json_sha256(expertise),
            "adjacency": adjacency,
            "adjacency_fingerprint": canonical_json_sha256(adjacency),
            "candidate_material_fingerprint": candidate_fingerprints[skill_id],
            "required_candidate_material_bindings": (
                required_material_bindings
            ),
        }
        binding["review_binding_fingerprint"] = canonical_json_sha256(binding)
        bindings[skill_id] = binding
    _validate_binding_catalog(bindings)
    return bindings


def _validate_binding_catalog(
    bindings: Mapping[str, dict[str, Any]],
) -> None:
    if not isinstance(bindings, Mapping) or not bindings:
        raise ProfessionalCarryForwardError(
            "professional bindings must be a non-empty mapping"
        )
    if list(bindings) != sorted(bindings):
        raise ProfessionalCarryForwardError(
            "professional bindings must be Skill-sorted"
        )
    candidate_fingerprints: dict[str, str] = {}
    for key, binding in bindings.items():
        if not isinstance(binding, dict) or set(binding) != _TARGET_BINDING_FIELDS:
            raise ProfessionalCarryForwardError(
                f"binding {key} fields are not canonical"
            )
        if binding.get("skill_id") != key:
            raise ProfessionalCarryForwardError(
                f"binding key {key} does not match skill_id"
            )
        own = _canonical_own_material_binding(
            binding.get("own_material"), label=f"binding {key}"
        )
        registry = professional_registry_responsibility_binding(binding)
        expertise = professional_required_expertise_binding(binding)
        adjacency = professional_adjacency_review_binding(
            {"routing_adjacency": binding.get("adjacency")}
        )
        expected_parts = {
            "own_material_fingerprint": canonical_json_sha256(own),
            "registry_fingerprint": canonical_json_sha256(registry),
            "required_expertise_fingerprint": canonical_json_sha256(expertise),
            "adjacency_fingerprint": canonical_json_sha256(adjacency),
        }
        for field, expected in expected_parts.items():
            if binding.get(field) != expected:
                raise ProfessionalCarryForwardError(
                    f"binding {key}.{field} is stale"
                )
        candidate_projection = {
            "skill_id": key,
            "layer": binding["layer"],
            "own_material": own,
            "registry": registry,
            "required_expertise_tags": expertise,
        }
        candidate_fingerprint = canonical_json_sha256(candidate_projection)
        if binding.get("candidate_material_fingerprint") != candidate_fingerprint:
            raise ProfessionalCarryForwardError(
                f"binding {key}.candidate_material_fingerprint is stale"
            )
        candidate_fingerprints[key] = candidate_fingerprint
        without_fingerprint = dict(binding)
        review_fingerprint = without_fingerprint.pop("review_binding_fingerprint")
        if review_fingerprint != canonical_json_sha256(without_fingerprint):
            raise ProfessionalCarryForwardError(
                f"binding {key}.review_binding_fingerprint is stale"
            )
    for key, binding in bindings.items():
        required_ids = [
            row["skill_id"] for row in binding["adjacency"]["required_candidates"]
        ]
        ranking_ids = [
            row["skill_id"]
            for row in binding["adjacency"]["full_catalog_ranking"]
        ]
        expected_ranking_ids = set(bindings) - {key}
        if set(ranking_ids) != expected_ranking_ids:
            missing = sorted(expected_ranking_ids - set(ranking_ids))
            extra = sorted(set(ranking_ids) - expected_ranking_ids)
            raise ProfessionalCarryForwardError(
                f"binding {key} full ranking closed set is stale; "
                f"missing={missing}; extra={extra}"
            )
        material_bindings = binding.get("required_candidate_material_bindings")
        if not isinstance(material_bindings, list) or any(
            not isinstance(row, dict)
            or set(row) != {"skill_id", "material_fingerprint"}
            for row in material_bindings
        ):
            raise ProfessionalCarryForwardError(
                f"binding {key}.required_candidate_material_bindings is invalid"
            )
        material_ids = [row["skill_id"] for row in material_bindings]
        if material_ids != required_ids:
            raise ProfessionalCarryForwardError(
                f"binding {key} required candidate material set is stale"
            )
        for row in material_bindings:
            candidate_id = row["skill_id"]
            if candidate_id not in candidate_fingerprints:
                raise ProfessionalCarryForwardError(
                    f"binding {key} names unknown candidate {candidate_id}"
                )
            if row["material_fingerprint"] != candidate_fingerprints[candidate_id]:
                raise ProfessionalCarryForwardError(
                    f"binding {key} candidate material for {candidate_id} is stale"
                )


def professional_carry_snapshot(
    bindings: Mapping[str, dict[str, Any]],
    *,
    review_contract_fingerprint: str,
) -> dict[str, Any]:
    """Create the compact exact baseline consumed by the pure carry plan."""

    _validate_binding_catalog(bindings)
    contract = _require_sha256(
        review_contract_fingerprint,
        label="review_contract_fingerprint",
    )
    targets = {
        skill_id: {
            field: copy.deepcopy(binding[field])
            for field in sorted(_SNAPSHOT_TARGET_FIELDS)
        }
        for skill_id, binding in bindings.items()
    }
    return {
        "review_contract_fingerprint": contract,
        "targets": targets,
    }


def _required_candidate_ids(target: Mapping[str, Any]) -> list[str]:
    adjacency = target.get("routing_adjacency")
    required = adjacency.get("required_candidates") if isinstance(adjacency, dict) else None
    if not isinstance(required, list):
        raise ProfessionalCarryForwardError(
            "prior target lacks required adjacency candidates"
        )
    ids = [
        _require_skill_id(row.get("skill_id"), label="required candidate skill_id")
        if isinstance(row, dict)
        else _raise_invalid_candidate("required candidate")
        for row in required
    ]
    if ids != sorted(set(ids)):
        raise ProfessionalCarryForwardError(
            "prior required candidate IDs must be sorted and unique"
        )
    return ids


def professional_prior_decision_dependencies(
    *,
    prior_packet: Mapping[str, Any],
    prior_ballots: Sequence[Mapping[str, Any]],
    prior_decision: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    """Extract one-hop dependencies from previously validated panel artifacts.

    The reviewer-added set is recomputed as a union across all three target
    votes, including a candidate added only by a dissenting/minority ballot.  A
    decision's audit projection is cross-checked against that union.  Missing
    evidence is represented as ``evidence_complete=false`` so the carry planner
    fails the target fresh instead of treating an incomplete baseline as an
    exceptional control-flow error.
    """

    targets_raw = prior_packet.get("professional_targets")
    decisions_raw = prior_decision.get("professional_decisions")
    if not isinstance(targets_raw, list):
        raise ProfessionalCarryForwardError(
            "prior packet professional_targets must be an array"
        )
    if not isinstance(prior_ballots, Sequence) or isinstance(
        prior_ballots, (str, bytes)
    ):
        raise ProfessionalCarryForwardError("prior ballots must be an array")
    if not isinstance(decisions_raw, list):
        decisions_raw = []
    target_index = _canonical_target_index(targets_raw)
    full_ranking_ids = {
        skill_id: {
            row["skill_id"]
            for row in target["routing_adjacency"]["full_catalog_ranking"]
        }
        for skill_id, target in target_index.items()
    }
    required_by_target = {
        skill_id: _required_candidate_ids(target)
        for skill_id, target in target_index.items()
    }

    decision_index: dict[str, Mapping[str, Any]] = {}
    duplicate_decisions: set[str] = set()
    for row in decisions_raw:
        if not isinstance(row, Mapping):
            continue
        skill_id = row.get("skill_id")
        if not isinstance(skill_id, str):
            continue
        if skill_id in decision_index:
            duplicate_decisions.add(skill_id)
        decision_index[skill_id] = row
    unknown_decisions = sorted(set(decision_index) - set(target_index))
    if unknown_decisions:
        raise ProfessionalCarryForwardError(
            "prior decision names unknown targets: " + ", ".join(unknown_decisions)
        )

    packet_review_id = prior_packet.get("review_id")
    packet_sources = prior_packet.get("source_fingerprints")
    ballot_voters: dict[str, dict[str, Any]] = {}
    agent_owners: dict[str, str] = {}
    votes_by_target: dict[
        str, list[tuple[str, Mapping[str, Any], bool]]
    ] = {skill_id: [] for skill_id in target_index}
    for ballot_index, ballot in enumerate(prior_ballots):
        if not isinstance(ballot, Mapping):
            raise ProfessionalCarryForwardError(
                f"prior_ballots[{ballot_index}] must be an object"
            )
        voter = ballot.get("voter")
        if not isinstance(voter, Mapping):
            raise ProfessionalCarryForwardError(
                f"prior_ballots[{ballot_index}].voter must be an object"
            )
        voter_id = _require_skill_id(
            voter.get("voter_id"),
            label=f"prior_ballots[{ballot_index}].voter.voter_id",
        )
        agent_id = _require_skill_id(
            voter.get("agent_id"),
            label=f"prior_ballots[{ballot_index}].voter.agent_id",
        )
        if voter_id in ballot_voters:
            raise ProfessionalCarryForwardError(
                f"prior ballots duplicate voter_id {voter_id}"
            )
        if agent_id in agent_owners:
            raise ProfessionalCarryForwardError(
                f"prior ballots duplicate agent_id {agent_id}"
            )
        expertise_tags = voter.get("expertise_tags")
        if not isinstance(expertise_tags, list) or not all(
            isinstance(tag, str) and tag for tag in expertise_tags
        ):
            expertise_tags = []
        claims = voter.get("qualification_claims")
        claimed_tags = (
            [
                claim.get("expertise_tag")
                for claim in claims
                if isinstance(claim, Mapping)
            ]
            if isinstance(claims, list)
            else []
        )
        architecture = expertise_tags == ["skill-reference-architecture"]
        claims_complete = bool(
            isinstance(claims, list)
            and claims
            and all(
                isinstance(claim, Mapping)
                and isinstance(claim.get("qualification_basis"), str)
                and claim["qualification_basis"].strip()
                and isinstance(claim.get("proof_limit"), str)
                and claim["proof_limit"].strip()
                for claim in claims
            )
        )
        axis_complete = bool(
            architecture
            or "skill-reference-architecture" not in expertise_tags
        )
        qualification_complete = bool(
            expertise_tags
            and expertise_tags == sorted(set(expertise_tags))
            and claimed_tags == expertise_tags
            and claims_complete
            and axis_complete
            and voter.get("independent_review") is True
        )
        ballot_voters[voter_id] = {
            "agent_id": agent_id,
            "expertise_tags": expertise_tags,
            "voter_kind": "architecture" if architecture else "domain",
            "qualification_complete": qualification_complete,
        }
        agent_owners[agent_id] = voter_id
        ballot_current = bool(
            ballot.get("review_id") == packet_review_id
            and ballot.get("source_fingerprints") == packet_sources
        )
        votes = ballot.get("professional_votes")
        if not isinstance(votes, list):
            continue
        seen_in_ballot: set[str] = set()
        for vote in votes:
            if not isinstance(vote, Mapping):
                continue
            skill_id = vote.get("skill_id")
            if not isinstance(skill_id, str):
                continue
            if skill_id not in target_index:
                raise ProfessionalCarryForwardError(
                    f"prior ballot names unknown target {skill_id}"
                )
            if skill_id in seen_in_ballot:
                raise ProfessionalCarryForwardError(
                    f"prior ballot duplicates target {skill_id}"
                )
            seen_in_ballot.add(skill_id)
            votes_by_target[skill_id].append(
                (voter_id, vote, ballot_current)
            )

    decision_voters_raw = prior_decision.get("voters")
    decision_voters: dict[str, str] = {}
    decision_voters_complete = isinstance(decision_voters_raw, list)
    if isinstance(decision_voters_raw, list):
        for row in decision_voters_raw:
            if not isinstance(row, Mapping):
                decision_voters_complete = False
                continue
            voter_id = row.get("voter_id")
            agent_id = row.get("agent_id")
            if (
                not isinstance(voter_id, str)
                or not isinstance(agent_id, str)
                or voter_id in decision_voters
            ):
                decision_voters_complete = False
                continue
            decision_voters[voter_id] = agent_id
    decision_round_current = bool(
        prior_decision.get("review_id") == packet_review_id
        and prior_decision.get("source_fingerprints") == packet_sources
        and decision_voters_complete
        and decision_voters
        == {
            voter_id: metadata["agent_id"]
            for voter_id, metadata in ballot_voters.items()
        }
    )

    dependencies: dict[str, dict[str, Any]] = {}
    for skill_id in sorted(target_index):
        required_ids = required_by_target[skill_id]
        target_votes = votes_by_target[skill_id]
        reviewer_added_by_voter: dict[str, set[str]] = {}
        target_voter_ids = [voter_id for voter_id, _vote, _current in target_votes]
        votes_complete = bool(
            len(target_votes) == 3
            and len(target_voter_ids) == len(set(target_voter_ids))
            and all(current for _voter_id, _vote, current in target_votes)
        )
        domain_voters: list[str] = []
        architecture_voters: list[str] = []
        target_required_expertise = target_index[skill_id].get(
            "required_expertise_tags"
        )
        if not isinstance(target_required_expertise, list):
            target_required_expertise = []
            votes_complete = False
        for voter_id, vote, _current in target_votes:
            voter_metadata = ballot_voters[voter_id]
            if voter_metadata["voter_kind"] == "architecture":
                architecture_voters.append(voter_id)
            else:
                domain_voters.append(voter_id)
                if not set(target_required_expertise) <= set(
                    voter_metadata["expertise_tags"]
                ):
                    votes_complete = False
            if voter_metadata["qualification_complete"] is not True:
                votes_complete = False
            reviews = vote.get("examined_adjacent_candidates")
            if not isinstance(reviews, list):
                votes_complete = False
                continue
            reviewed_required: set[str] = set()
            added_for_voter: set[str] = set()
            reviewed_ids: set[str] = set()
            for review in reviews:
                if not isinstance(review, Mapping):
                    votes_complete = False
                    continue
                candidate_id = review.get("skill_id")
                origin = review.get("review_origin")
                if (
                    not isinstance(candidate_id, str)
                    or candidate_id not in full_ranking_ids[skill_id]
                    or candidate_id in reviewed_ids
                ):
                    votes_complete = False
                    continue
                reviewed_ids.add(candidate_id)
                if origin == "packet-required" and candidate_id in required_ids:
                    reviewed_required.add(candidate_id)
                elif origin == "reviewer-added" and candidate_id not in required_ids:
                    added_for_voter.add(candidate_id)
                else:
                    votes_complete = False
            if reviewed_required != set(required_ids):
                votes_complete = False
            if added_for_voter:
                reviewer_added_by_voter[voter_id] = added_for_voter
        if len(domain_voters) != 2 or len(architecture_voters) != 1:
            votes_complete = False

        reviewer_added = {
            candidate_id
            for candidates in reviewer_added_by_voter.values()
            for candidate_id in candidates
        }
        decision = decision_index.get(skill_id)
        final_disposition = (
            decision.get("final_disposition")
            if isinstance(decision, Mapping)
            else None
        )
        decision_added_by_voter: dict[str, set[str]] = {}
        decision_reviews = (
            decision.get("reviewer_added_adjacency_reviews")
            if isinstance(decision, Mapping)
            else None
        )
        decision_projection_complete = isinstance(decision_reviews, list)
        if isinstance(decision_reviews, list):
            for voter_review in decision_reviews:
                voter_id = (
                    voter_review.get("voter_id")
                    if isinstance(voter_review, Mapping)
                    else None
                )
                candidates = (
                    voter_review.get("candidates")
                    if isinstance(voter_review, Mapping)
                    else None
                )
                if (
                    not isinstance(voter_id, str)
                    or voter_id not in target_voter_ids
                    or voter_id in decision_added_by_voter
                    or not isinstance(candidates, list)
                ):
                    decision_projection_complete = False
                    continue
                ids = {
                    candidate.get("skill_id")
                    for candidate in candidates
                    if isinstance(candidate, Mapping)
                    and isinstance(candidate.get("skill_id"), str)
                }
                if len(ids) != len(candidates):
                    decision_projection_complete = False
                if any(
                    not isinstance(candidate, Mapping)
                    or candidate.get("review_origin") != "reviewer-added"
                    for candidate in candidates
                ):
                    decision_projection_complete = False
                decision_added_by_voter[voter_id] = ids
        qualification_coverage = (
            decision.get("qualification_coverage")
            if isinstance(decision, Mapping)
            else None
        )
        expected_qualification_coverage = {
            "required_expertise_tags": target_required_expertise,
            "domain_voters": sorted(domain_voters),
            "architecture_voter": (
                architecture_voters[0]
                if len(architecture_voters) == 1
                else None
            ),
        }
        package_fingerprint_current = target_index[skill_id].get(
            "package_fingerprint"
        )
        package_fingerprint_prior = (
            decision.get("package_fingerprint")
            if isinstance(decision, Mapping)
            else None
        )
        evidence_complete = bool(
            votes_complete
            and decision_round_current
            and decision is not None
            and skill_id not in duplicate_decisions
            and isinstance(final_disposition, str)
            and package_fingerprint_current == package_fingerprint_prior
            and qualification_coverage == expected_qualification_coverage
            and decision_projection_complete
            and reviewer_added_by_voter == decision_added_by_voter
        )
        dependency_ids = sorted(set(required_ids) | reviewer_added)
        dependencies[skill_id] = {
            "skill_id": skill_id,
            "final_disposition": final_disposition,
            "evidence_complete": evidence_complete,
            "prior_target_vote_count": len(target_votes),
            "required_candidate_ids": required_ids,
            "reviewer_added_candidate_ids_union": sorted(reviewer_added),
            "dependency_candidate_ids": dependency_ids,
        }
    return dependencies


def _snapshot_targets(
    prior_snapshot: object,
) -> tuple[str | None, dict[str, dict[str, Any]] | None]:
    if prior_snapshot is None:
        return None, None
    if not isinstance(prior_snapshot, Mapping) or set(prior_snapshot) != {
        "review_contract_fingerprint",
        "targets",
    }:
        raise ProfessionalCarryForwardError(
            "prior snapshot fields are not canonical"
        )
    contract = _require_sha256(
        prior_snapshot.get("review_contract_fingerprint"),
        label="prior_snapshot.review_contract_fingerprint",
    )
    targets = prior_snapshot.get("targets")
    if not isinstance(targets, dict):
        raise ProfessionalCarryForwardError(
            "prior_snapshot.targets must be an object"
        )
    if list(targets) != sorted(targets):
        raise ProfessionalCarryForwardError(
            "prior_snapshot.targets must be Skill-sorted"
        )
    for skill_id, target in targets.items():
        if not isinstance(target, dict) or set(target) != _SNAPSHOT_TARGET_FIELDS:
            raise ProfessionalCarryForwardError(
                f"prior snapshot target {skill_id} fields are not canonical"
            )
        if target.get("skill_id") != skill_id:
            raise ProfessionalCarryForwardError(
                f"prior snapshot target key {skill_id} is stale"
            )
    return contract, targets


def _decision_dependencies(
    value: Mapping[str, dict[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ProfessionalCarryForwardError(
            "prior decision dependencies must be an object"
        )
    dependencies: dict[str, dict[str, Any]] = {}
    for skill_id in sorted(value):
        dependency = value[skill_id]
        if not isinstance(dependency, dict) or set(dependency) != _DECISION_DEPENDENCY_FIELDS:
            raise ProfessionalCarryForwardError(
                f"prior decision dependency {skill_id} fields are not canonical"
            )
        if dependency.get("skill_id") != skill_id:
            raise ProfessionalCarryForwardError(
                f"prior decision dependency key {skill_id} is stale"
            )
        for field in (
            "required_candidate_ids",
            "reviewer_added_candidate_ids_union",
            "dependency_candidate_ids",
        ):
            _sorted_unique_strings(
                dependency.get(field), label=f"{skill_id}.{field}"
            )
        expected_union = sorted(
            set(dependency["required_candidate_ids"])
            | set(dependency["reviewer_added_candidate_ids_union"])
        )
        if dependency["dependency_candidate_ids"] != expected_union:
            raise ProfessionalCarryForwardError(
                f"prior decision dependency {skill_id} union is stale"
            )
        dependencies[skill_id] = dependency
    return dependencies


def plan_exact_professional_carry_forward(
    *,
    current_bindings: Mapping[str, dict[str, Any]],
    prior_snapshot: Mapping[str, Any] | None,
    prior_decision_dependencies: Mapping[str, dict[str, Any]] | None,
    review_contract_fingerprint: str,
) -> dict[str, Any]:
    """Partition whole packages into deterministic fresh and carry sets.

    The plan compares factual bindings only.  It never reads or propagates the
    fresh/carry status of another target, so A material changing can invalidate
    B when B reviewed A, but cannot invalidate C merely because C reviewed B.
    """

    _validate_binding_catalog(current_bindings)
    current_contract = _require_sha256(
        review_contract_fingerprint,
        label="review_contract_fingerprint",
    )
    prior_contract, prior_targets = _snapshot_targets(prior_snapshot)
    dependencies = _decision_dependencies(prior_decision_dependencies)
    reasons_by_target: dict[str, list[str]] = {}

    global_reason: str | None = None
    if prior_targets is None:
        global_reason = "no-prior-baseline"
    elif prior_contract != current_contract:
        global_reason = "review-contract-changed"

    for skill_id, binding in current_bindings.items():
        reasons: set[str] = set()
        if global_reason is not None:
            reasons.add(global_reason)
        else:
            prior = prior_targets.get(skill_id) if prior_targets else None
            dependency = dependencies.get(skill_id)
            if prior is None:
                reasons.add("target-not-in-prior-snapshot")
            if dependency is None or dependency.get("evidence_complete") is not True:
                reasons.add("prior-evidence-missing")
            if (
                dependency is not None
                and dependency.get("final_disposition")
                != ACCEPTED_PROFESSIONAL_DISPOSITION
            ):
                reasons.add("prior-final-not-accepted")
            if prior is not None:
                comparisons = (
                    (
                        "layer",
                        "target-placement-changed",
                    ),
                    (
                        "own_material_fingerprint",
                        "own-material-changed",
                    ),
                    (
                        "registry_fingerprint",
                        "registry-responsibility-changed",
                    ),
                    (
                        "required_expertise_fingerprint",
                        "required-expertise-changed",
                    ),
                    (
                        "adjacency_fingerprint",
                        "adjacency-review-binding-changed",
                    ),
                )
                for field, reason in comparisons:
                    if prior.get(field) != binding.get(field):
                        reasons.add(reason)

                prior_required = {
                    row["skill_id"]: row["material_fingerprint"]
                    for row in prior["required_candidate_material_bindings"]
                }
                current_required = {
                    row["skill_id"]: row["material_fingerprint"]
                    for row in binding["required_candidate_material_bindings"]
                }
                if set(prior_required) == set(current_required) and any(
                    prior_required[candidate_id]
                    != current_required[candidate_id]
                    for candidate_id in current_required
                ):
                    reasons.add("required-candidate-material-changed")

                if dependency is not None:
                    for candidate_id in dependency[
                        "reviewer_added_candidate_ids_union"
                    ]:
                        prior_candidate = (
                            prior_targets.get(candidate_id)
                            if prior_targets is not None
                            else None
                        )
                        current_candidate = current_bindings.get(candidate_id)
                        if (
                            prior_candidate is None
                            or current_candidate is None
                            or prior_candidate.get(
                                "candidate_material_fingerprint"
                            )
                            != current_candidate.get(
                                "candidate_material_fingerprint"
                            )
                        ):
                            reasons.add(
                                "reviewer-added-candidate-material-changed"
                            )
                            break
        reasons_by_target[skill_id] = sorted(reasons)

    fresh = sorted(
        skill_id for skill_id, reasons in reasons_by_target.items() if reasons
    )
    carry = sorted(set(current_bindings) - set(fresh))
    return {
        "review_contract_fingerprint": current_contract,
        "fresh_target_ids": fresh,
        "carry_target_ids": carry,
        "reasons_by_target": reasons_by_target,
    }


def _candidate_projection_from_binding(
    binding: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "skill_id": binding["skill_id"],
        "layer": binding["layer"],
        "own_material": copy.deepcopy(binding["own_material"]),
        "registry": copy.deepcopy(binding["registry"]),
        "required_expertise_tags": copy.deepcopy(
            binding["required_expertise_tags"]
        ),
        "material_fingerprint": binding["candidate_material_fingerprint"],
    }


def _candidate_boundary_projection_from_binding(
    binding: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "skill_id": binding["skill_id"],
        "layer": binding["layer"],
        "responsibility_contract": copy.deepcopy(
            binding["registry"]["responsibility_contract"]
        ),
        "required_expertise_tags": copy.deepcopy(
            binding["required_expertise_tags"]
        ),
        "material_fingerprint": binding["candidate_material_fingerprint"],
    }


def _normalize_assigned_targets(
    *,
    bindings: Mapping[str, dict[str, Any]],
    assigned_fresh_target_ids: Sequence[str],
) -> list[str]:
    _validate_binding_catalog(bindings)
    if not isinstance(assigned_fresh_target_ids, Sequence) or isinstance(
        assigned_fresh_target_ids, (str, bytes)
    ):
        raise ProfessionalCarryForwardError(
            "assigned fresh targets must be an array"
        )
    assigned = list(assigned_fresh_target_ids)
    if not assigned:
        raise ProfessionalCarryForwardError(
            "assigned fresh targets must be non-empty"
        )
    if not all(isinstance(item, str) and item for item in assigned):
        raise ProfessionalCarryForwardError(
            "assigned fresh targets must contain Skill IDs"
        )
    if len(assigned) != len(set(assigned)):
        raise ProfessionalCarryForwardError(
            "assigned fresh targets must not contain duplicates"
        )
    assigned = sorted(assigned)
    unknown = sorted(set(assigned) - set(bindings))
    if unknown:
        raise ProfessionalCarryForwardError(
            "assigned fresh targets are unknown: " + ", ".join(unknown)
        )
    return assigned


def _project_professional_discovery_capsule(
    *,
    bindings: Mapping[str, dict[str, Any]],
    assigned: Sequence[str],
) -> dict[str, Any]:
    targets: list[dict[str, Any]] = []
    material_ids: set[str] = set(assigned)
    for skill_id in assigned:
        binding = bindings[skill_id]
        required_ids = [
            row["skill_id"]
            for row in binding["adjacency"]["required_candidates"]
        ]
        material_ids.update(required_ids)
        targets.append(
            {
                "skill_id": skill_id,
                "source_review_binding_fingerprint": binding[
                    "review_binding_fingerprint"
                ],
                "adjacency": copy.deepcopy(binding["adjacency"]),
                "required_candidate_material_manifest": [
                    {
                        "skill_id": candidate_id,
                        "material_fingerprint": bindings[candidate_id][
                            "candidate_material_fingerprint"
                        ],
                    }
                    for candidate_id in required_ids
                ],
            }
        )
    return {
        "projection_contract": copy.deepcopy(
            PROFESSIONAL_DISCOVERY_CAPSULE_CONTRACT
        ),
        "assigned_fresh_target_ids": list(assigned),
        "material_catalog": [
            _candidate_projection_from_binding(bindings[skill_id])
            for skill_id in sorted(material_ids)
        ],
        "boundary_catalog": [
            _candidate_boundary_projection_from_binding(bindings[skill_id])
            for skill_id in sorted(bindings)
        ],
        "targets": targets,
    }


def project_professional_discovery_capsule(
    *,
    bindings: Mapping[str, dict[str, Any]],
    assigned_fresh_target_ids: Sequence[str],
) -> dict[str, Any]:
    """Project the immutable first-stage discovery input for one reviewer."""

    assigned = _normalize_assigned_targets(
        bindings=bindings,
        assigned_fresh_target_ids=assigned_fresh_target_ids,
    )
    capsule = _project_professional_discovery_capsule(
        bindings=bindings,
        assigned=assigned,
    )
    validate_professional_discovery_capsule(
        capsule,
        bindings=bindings,
        assigned_fresh_target_ids=assigned,
    )
    return capsule


def validate_professional_discovery_capsule(
    capsule: object,
    *,
    bindings: Mapping[str, dict[str, Any]],
    assigned_fresh_target_ids: Sequence[str],
) -> dict[str, Any]:
    """Reject incomplete, expanded, or stale discovery projections."""

    assigned = _normalize_assigned_targets(
        bindings=bindings,
        assigned_fresh_target_ids=assigned_fresh_target_ids,
    )
    if not isinstance(capsule, dict) or set(capsule) != _DISCOVERY_CAPSULE_FIELDS:
        raise ProfessionalCarryForwardError(
            "discovery capsule fields are not closed"
        )
    if (
        capsule.get("projection_contract")
        != PROFESSIONAL_DISCOVERY_CAPSULE_CONTRACT
    ):
        raise ProfessionalCarryForwardError(
            "discovery capsule projection contract is stale"
        )
    expected = _project_professional_discovery_capsule(
        bindings=bindings,
        assigned=assigned,
    )
    if capsule.get("assigned_fresh_target_ids") != assigned:
        raise ProfessionalCarryForwardError(
            "discovery capsule assigned target set is stale"
        )
    targets = _closed_ids(
        capsule.get("targets"),
        field="skill_id",
        label="discovery capsule.targets",
        expected=set(assigned),
    )
    for skill_id, target in targets.items():
        if set(target) != _DISCOVERY_CAPSULE_TARGET_FIELDS:
            raise ProfessionalCarryForwardError(
                f"discovery capsule target {skill_id} fields are not closed"
            )
    boundary = _closed_ids(
        capsule.get("boundary_catalog"),
        field="skill_id",
        label="discovery capsule.boundary_catalog",
        expected=set(bindings),
    )
    for skill_id, row in boundary.items():
        if set(row) != _DISCOVERY_BOUNDARY_FIELDS:
            raise ProfessionalCarryForwardError(
                f"discovery boundary {skill_id} fields are not closed"
            )
    expected_material_ids = {
        row["skill_id"] for row in expected["material_catalog"]
    }
    _closed_ids(
        capsule.get("material_catalog"),
        field="skill_id",
        label="discovery capsule.material_catalog",
        expected=expected_material_ids,
    )
    if capsule != expected:
        raise ProfessionalCarryForwardError(
            "discovery capsule is extra, missing, duplicate, or stale"
        )
    return capsule


def _normalize_capsule_inputs(
    *,
    bindings: Mapping[str, dict[str, Any]],
    assigned_fresh_target_ids: Sequence[str],
    reviewer_added_requests_by_target: (
        Mapping[str, Sequence[Mapping[str, Any]]] | None
    ),
) -> tuple[list[str], dict[str, list[dict[str, Any]]]]:
    assigned = _normalize_assigned_targets(
        bindings=bindings,
        assigned_fresh_target_ids=assigned_fresh_target_ids,
    )
    raw_added = reviewer_added_requests_by_target or {}
    if not isinstance(raw_added, Mapping):
        raise ProfessionalCarryForwardError(
            "reviewer-added requests must be an object"
        )
    extra_targets = sorted(set(raw_added) - set(assigned))
    if extra_targets:
        raise ProfessionalCarryForwardError(
            "reviewer-added candidates contain extra target assignments: "
            + ", ".join(extra_targets)
        )
    normalized: dict[str, list[dict[str, Any]]] = {}
    for skill_id in assigned:
        values = raw_added.get(skill_id, [])
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
            raise ProfessionalCarryForwardError(
                f"reviewer-added requests for {skill_id} must be an array"
            )
        added: list[dict[str, Any]] = []
        for index, raw in enumerate(values):
            if not isinstance(raw, Mapping) or set(raw) != _REVIEWER_ADDED_REQUEST_FIELDS:
                raise ProfessionalCarryForwardError(
                    f"reviewer-added request {skill_id}[{index}] fields are not closed"
                )
            candidate_id = _require_skill_id(
                raw.get("skill_id"),
                label=f"reviewer-added request {skill_id}[{index}].skill_id",
            )
            reason = raw.get("discovery_reason")
            if not isinstance(reason, str) or not reason.strip():
                raise ProfessionalCarryForwardError(
                    f"reviewer-added request {skill_id}[{index}].discovery_reason must be non-empty"
                )
            added.append(copy.deepcopy(dict(raw)))
        added_ids = [row["skill_id"] for row in added]
        if len(added_ids) != len(set(added_ids)):
            raise ProfessionalCarryForwardError(
                f"reviewer-added requests for {skill_id} contain duplicates"
            )
        added.sort(key=lambda row: row["skill_id"])
        binding = bindings[skill_id]
        ranking = {
            row["skill_id"]: row
            for row in binding["adjacency"]["full_catalog_ranking"]
        }
        required_ids = {
            row["skill_id"]
            for row in binding["adjacency"]["required_candidates"]
        }
        outside = sorted(set(added_ids) - set(ranking))
        if outside:
            raise ProfessionalCarryForwardError(
                f"reviewer-added requests for {skill_id} are absent from full ranking: "
                + ", ".join(outside)
            )
        already_required = sorted(set(added_ids) & required_ids)
        if already_required:
            raise ProfessionalCarryForwardError(
                f"reviewer-added requests for {skill_id} are already packet-required: "
                + ", ".join(already_required)
            )
        for request in added:
            candidate_id = request["skill_id"]
            if request["ranking_evidence"] != ranking[candidate_id]:
                raise ProfessionalCarryForwardError(
                    f"reviewer-added request {skill_id}->{candidate_id} ranking evidence is stale"
                )
            if request["material_fingerprint"] != bindings[candidate_id][
                "candidate_material_fingerprint"
            ]:
                raise ProfessionalCarryForwardError(
                    f"reviewer-added request {skill_id}->{candidate_id} material fingerprint is stale"
                )
        normalized[skill_id] = added
    return assigned, normalized


def _project_professional_review_capsule(
    *,
    bindings: Mapping[str, dict[str, Any]],
    assigned: Sequence[str],
    reviewer_added: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, Any]:
    targets: list[dict[str, Any]] = []
    material_ids: set[str] = set(assigned)
    for skill_id in assigned:
        binding = bindings[skill_id]
        required_ids = [
            row["skill_id"]
            for row in binding["adjacency"]["required_candidates"]
        ]
        added_by_id = {
            row["skill_id"]: row for row in reviewer_added[skill_id]
        }
        added_ids = sorted(added_by_id)
        origin_by_id = {
            **{candidate_id: "packet-required" for candidate_id in required_ids},
            **{candidate_id: "reviewer-added" for candidate_id in added_ids},
        }
        candidate_ids = sorted(origin_by_id)
        material_ids.update(candidate_ids)
        manifest = [
            {
                "skill_id": candidate_id,
                "review_origin": origin_by_id[candidate_id],
                "discovery_reason": (
                    added_by_id[candidate_id]["discovery_reason"]
                    if candidate_id in added_by_id
                    else None
                ),
                "material_fingerprint": bindings[candidate_id][
                    "candidate_material_fingerprint"
                ],
            }
            for candidate_id in candidate_ids
        ]
        targets.append(
            {
                "skill_id": skill_id,
                "source_review_binding_fingerprint": binding[
                    "review_binding_fingerprint"
                ],
                "adjacency": copy.deepcopy(binding["adjacency"]),
                "candidate_material_manifest": manifest,
            }
        )
    return {
        "projection_contract": copy.deepcopy(PROFESSIONAL_CAPSULE_CONTRACT),
        "assigned_fresh_target_ids": list(assigned),
        "material_catalog": [
            _candidate_projection_from_binding(bindings[skill_id])
            for skill_id in sorted(material_ids)
        ],
        "targets": targets,
    }


def project_professional_review_capsule(
    *,
    bindings: Mapping[str, dict[str, Any]],
    assigned_fresh_target_ids: Sequence[str],
    reviewer_added_requests_by_target: (
        Mapping[str, Sequence[Mapping[str, Any]]] | None
    ) = None,
) -> dict[str, Any]:
    """Project one exact final capsule from validated request rows."""

    assigned, reviewer_added = _normalize_capsule_inputs(
        bindings=bindings,
        assigned_fresh_target_ids=assigned_fresh_target_ids,
        reviewer_added_requests_by_target=reviewer_added_requests_by_target,
    )
    capsule = _project_professional_review_capsule(
        bindings=bindings,
        assigned=assigned,
        reviewer_added=reviewer_added,
    )
    validate_professional_review_capsule(
        capsule,
        bindings=bindings,
        assigned_fresh_target_ids=assigned,
        reviewer_added_requests_by_target=reviewer_added,
    )
    return capsule


def _closed_ids(
    rows: object,
    *,
    field: str,
    label: str,
    expected: set[str],
) -> dict[str, Mapping[str, Any]]:
    if not isinstance(rows, list):
        raise ProfessionalCarryForwardError(f"{label} must be an array")
    index: dict[str, Mapping[str, Any]] = {}
    duplicates: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            raise ProfessionalCarryForwardError(f"{label} entries must be objects")
        item_id = row.get(field)
        if not isinstance(item_id, str) or not item_id:
            raise ProfessionalCarryForwardError(
                f"{label}.{field} must be a Skill ID"
            )
        if item_id in index:
            duplicates.add(item_id)
        index[item_id] = row
    if duplicates:
        raise ProfessionalCarryForwardError(
            f"{label} contains duplicate IDs: " + ", ".join(sorted(duplicates))
        )
    missing = sorted(expected - set(index))
    extra = sorted(set(index) - expected)
    if missing or extra:
        raise ProfessionalCarryForwardError(
            f"{label} closed set mismatch; missing={missing}; extra={extra}"
        )
    return index


def validate_professional_review_capsule(
    capsule: object,
    *,
    bindings: Mapping[str, dict[str, Any]],
    assigned_fresh_target_ids: Sequence[str],
    reviewer_added_requests_by_target: (
        Mapping[str, Sequence[Mapping[str, Any]]] | None
    ) = None,
) -> dict[str, Any]:
    """Reject extra, missing, duplicate, or stale capsule projections."""

    assigned, reviewer_added = _normalize_capsule_inputs(
        bindings=bindings,
        assigned_fresh_target_ids=assigned_fresh_target_ids,
        reviewer_added_requests_by_target=reviewer_added_requests_by_target,
    )
    if not isinstance(capsule, dict) or set(capsule) != _CAPSULE_FIELDS:
        raise ProfessionalCarryForwardError("capsule fields are not closed")
    if capsule.get("projection_contract") != PROFESSIONAL_CAPSULE_CONTRACT:
        raise ProfessionalCarryForwardError("capsule projection contract is stale")
    assigned_in_capsule = capsule.get("assigned_fresh_target_ids")
    if not isinstance(assigned_in_capsule, list):
        raise ProfessionalCarryForwardError(
            "capsule assigned_fresh_target_ids must be an array"
        )
    if len(assigned_in_capsule) != len(set(assigned_in_capsule)):
        raise ProfessionalCarryForwardError(
            "capsule assigned_fresh_target_ids contains duplicates"
        )
    if assigned_in_capsule != assigned:
        missing = sorted(set(assigned) - set(assigned_in_capsule))
        extra = sorted(set(assigned_in_capsule) - set(assigned))
        raise ProfessionalCarryForwardError(
            "capsule assigned target set is stale; "
            f"missing={missing}; extra={extra}"
        )
    target_index = _closed_ids(
        capsule.get("targets"),
        field="skill_id",
        label="capsule.targets",
        expected=set(assigned),
    )
    expected_capsule = _project_professional_review_capsule(
        bindings=bindings,
        assigned=assigned,
        reviewer_added=reviewer_added,
    )
    expected_target_index = {
        row["skill_id"]: row for row in expected_capsule["targets"]
    }
    expected_catalog_ids = {
        row["skill_id"] for row in expected_capsule["material_catalog"]
    }
    material_index = _closed_ids(
        capsule.get("material_catalog"),
        field="skill_id",
        label="capsule.material_catalog",
        expected=expected_catalog_ids,
    )
    if [row["skill_id"] for row in capsule["material_catalog"]] != sorted(
        expected_catalog_ids
    ):
        raise ProfessionalCarryForwardError(
            "capsule material_catalog must be Skill-sorted"
        )
    if [row["skill_id"] for row in capsule["targets"]] != assigned:
        raise ProfessionalCarryForwardError(
            "capsule targets must be Skill-sorted"
        )
    for skill_id in assigned:
        target = target_index[skill_id]
        expected_target = expected_target_index[skill_id]
        if set(target) != _CAPSULE_TARGET_FIELDS:
            raise ProfessionalCarryForwardError(
                f"capsule target {skill_id} fields are not closed"
            )
        expected_candidate_ids = {
            row["skill_id"]
            for row in expected_target["candidate_material_manifest"]
        }
        manifest_index = _closed_ids(
            target.get("candidate_material_manifest"),
            field="skill_id",
            label=f"capsule target {skill_id} candidate manifest",
            expected=expected_candidate_ids,
        )
        for candidate_id, manifest in manifest_index.items():
            if set(manifest) != _CAPSULE_MANIFEST_FIELDS:
                raise ProfessionalCarryForwardError(
                    f"capsule target {skill_id} candidate manifest fields are not closed"
                )
            if (
                material_index[candidate_id].get("material_fingerprint")
                != manifest.get("material_fingerprint")
            ):
                raise ProfessionalCarryForwardError(
                    f"capsule target {skill_id} candidate {candidate_id} manifest is stale"
                )
        if target != expected_target:
            raise ProfessionalCarryForwardError(
                f"capsule target {skill_id} projection is stale"
            )
    if capsule["material_catalog"] != expected_capsule["material_catalog"]:
        raise ProfessionalCarryForwardError(
            "capsule material_catalog projection is stale"
        )
    return capsule


def professional_review_capsule_cost_proxy(capsule: object) -> dict[str, Any]:
    """Return deterministic size proxies; never claim latency or real token cost."""

    payload = canonical_json_bytes(capsule)
    result: dict[str, Any] = {
        "canonical_json_bytes_proxy": len(payload),
        "o200k_base_tokens_proxy": None,
        "o200k_tokenizer_available": False,
    }
    try:
        import tiktoken  # type: ignore[import-not-found]

        encoding = tiktoken.get_encoding("o200k_base")
    except (ImportError, KeyError, OSError, ValueError):
        return result
    result["o200k_base_tokens_proxy"] = len(
        encoding.encode(payload.decode("utf-8"))
    )
    result["o200k_tokenizer_available"] = True
    return result


class _ContractValueProjector:
    """Project value identity with deterministic graph-local node IDs."""

    def __init__(self, *, repository_root: Path) -> None:
        self.repository_root = repository_root.resolve()
        self._seen: dict[int, tuple[object, str]] = {}
        self._nodes: dict[str, dict[str, object]] = {}

    def nodes(self) -> dict[str, dict[str, object]]:
        return {key: self._nodes[key] for key in sorted(self._nodes)}

    def envelope(self, root: object) -> dict[str, object]:
        return {"root": root, "nodes": self.nodes()}

    def identity_reference(
        self,
        value: object,
        *,
        kind: str,
        identity: str,
    ) -> dict[str, str]:
        """Bind alias topology without serializing a process-local address."""

        return self._reference(
            value,
            kind=kind,
            build=lambda: {"identity": identity},
        )

    def _reference(
        self,
        value: object,
        *,
        kind: str,
        build: Any,
    ) -> dict[str, str]:
        object_id = id(value)
        existing = self._seen.get(object_id)
        if existing is not None:
            existing_value, node_id = existing
            if existing_value is not value:
                raise ProfessionalCarryForwardError(
                    "contract value identity table is inconsistent"
                )
            return {"kind": "value-ref", "node_id": node_id}
        node_id = f"value-{len(self._nodes) + 1:06d}"
        self._seen[object_id] = (value, node_id)
        self._nodes[node_id] = {"kind": kind}
        self._nodes[node_id].update(build())
        return {"kind": "value-ref", "node_id": node_id}

    def _path_value(self, value: Path) -> str:
        try:
            return value.resolve().relative_to(self.repository_root).as_posix()
        except ValueError:
            return value.as_posix()

    def _unordered_value_key(
        self,
        value: object,
        *,
        allow_opaque_object: bool,
        value_label: str,
    ) -> bytes:
        ordering_projector = _ContractValueProjector(
            repository_root=self.repository_root
        )
        projected = ordering_projector.project(
            value,
            allow_opaque_object=allow_opaque_object,
            value_label=value_label,
        )
        return canonical_json_bytes(ordering_projector.envelope(projected))

    def project(
        self,
        value: object,
        *,
        allow_opaque_object: bool,
        value_label: str,
    ) -> object:
        if value is Ellipsis:
            return {"kind": "ellipsis"}
        if value is None:
            return {"kind": "none"}
        if type(value) is bool:
            return {"kind": "boolean", "value": value}
        if type(value) is int:
            return {"kind": "integer", "value": str(value)}
        if type(value) is float:
            return {"kind": "float", "hex": value.hex()}
        if type(value) is str:
            return {"kind": "string", "value": value}
        if type(value) is bytes:
            return {
                "kind": "bytes",
                "sha256": hashlib.sha256(value).hexdigest(),
            }
        if type(value) is re.Pattern:
            return self._reference(
                value,
                kind="regular-expression",
                build=lambda: {
                    "pattern": value.pattern,
                    "flags": int(value.flags),
                },
            )
        if isinstance(value, Path) and type(value).__module__ == "pathlib":
            return self._reference(
                value,
                kind="path",
                build=lambda: {"value": self._path_value(value)},
            )
        if type(value) is dict:
            return self._reference(
                value,
                kind="mapping",
                build=lambda: {
                    "entries": [
                        {
                            "key": self.project(
                                key,
                                allow_opaque_object=allow_opaque_object,
                                value_label=value_label,
                            ),
                            "value": self.project(
                                item,
                                allow_opaque_object=allow_opaque_object,
                                value_label=value_label,
                            ),
                        }
                        for key, item in value.items()
                    ]
                },
            )
        if type(value) in {list, tuple}:
            return self._reference(
                value,
                kind="list" if type(value) is list else "tuple",
                build=lambda: {
                    "items": [
                        self.project(
                            item,
                            allow_opaque_object=allow_opaque_object,
                            value_label=value_label,
                        )
                        for item in value
                    ]
                },
            )
        if type(value) in {set, frozenset}:
            keyed_items = [
                (
                    self._unordered_value_key(
                        item,
                        allow_opaque_object=allow_opaque_object,
                        value_label=value_label,
                    ),
                    item,
                )
                for item in value
            ]
            keyed_items.sort(key=lambda row: row[0])
            if any(
                left[0] == right[0]
                for left, right in zip(keyed_items, keyed_items[1:])
            ):
                raise ProfessionalCarryForwardError(
                    "unordered contract values lack a stable identity order"
                )
            return self._reference(
                value,
                kind="set" if type(value) is set else "frozenset",
                build=lambda: {
                    "items": [
                        self.project(
                            item,
                            allow_opaque_object=allow_opaque_object,
                            value_label=value_label,
                        )
                        for _key, item in keyed_items
                    ]
                },
            )
        if inspect.iscode(value):
            raise ProfessionalCarryForwardError(
                "code objects are not a cross-version contract value"
            )
        if allow_opaque_object and type(value) is object:
            return self._reference(
                value,
                kind="opaque-object",
                build=lambda: {"nominal_type": "builtins.object"},
            )
        raise ProfessionalCarryForwardError(
            f"{value_label} value cannot be represented safely: "
            f"{type(value).__module__}.{type(value).__qualname__}"
        )


def _contract_value(
    value: object,
    *,
    repository_root: Path,
    projector: _ContractValueProjector | None = None,
) -> object:
    active = projector or _ContractValueProjector(
        repository_root=repository_root
    )
    projected = active.project(
        value,
        allow_opaque_object=False,
        value_label="explicit contract",
    )
    return projected if projector is not None else active.envelope(projected)


def _callable_source_path(function: object) -> Path | None:
    unwrapped = inspect.unwrap(function) if callable(function) else function
    code = getattr(unwrapped, "__code__", None)
    filename = getattr(code, "co_filename", None)
    if isinstance(filename, str) and filename.startswith("<") and filename.endswith(
        ">"
    ):
        return None
    if not isinstance(filename, str):
        try:
            filename = inspect.getsourcefile(unwrapped)
        except (OSError, TypeError):
            filename = None
    if not isinstance(filename, str) and callable(unwrapped):
        try:
            filename = inspect.getsourcefile(type(unwrapped))
        except (OSError, TypeError):
            filename = None
    if not isinstance(filename, str):
        return None
    return Path(filename).resolve()


def _callable_identity(function: object, *, repository_root: Path) -> str:
    unwrapped = inspect.unwrap(function) if callable(function) else function
    source_path = _callable_source_path(function)
    qualname = getattr(unwrapped, "__qualname__", None) or getattr(
        unwrapped, "__name__", None
    )
    if source_path is not None:
        try:
            namespace = source_path.relative_to(repository_root.resolve()).as_posix()
        except ValueError:
            namespace = source_path.name
    else:
        namespace = getattr(unwrapped, "__module__", None) or (
            f"{type(unwrapped).__module__}.{type(unwrapped).__qualname__}"
        )
    return f"{namespace}:{qualname or type(unwrapped).__qualname__}"


_PYTHON_SOURCE_AST_CONTRACT = "python-source-ast-v2"
_AST_IGNORED_FIELDS = frozenset({"type_comment"})
_SYMTABLE_IGNORED_TYPES = frozenset(
    {
        "annotation",
        "type alias",
        "type parameter",
        "type parameters",
        "type variable",
    }
)
_AstNodeKey = tuple[str, str | None, int | None]
_SymbolTableKey = tuple[str, str, int]
_RepositoryModuleSource = tuple[
    str,
    ast.Module,
    symtable.SymbolTable,
    dict[_AstNodeKey, list[ast.AST]],
    dict[_SymbolTableKey, list[symtable.SymbolTable]],
]


_PROCESS_LOCAL_IDENTITY_POLICY = "process-local-identity-v2"
_DYNAMIC_CODE_PRIMITIVE_BOUNDARY = (
    "scripts/professional_completeness_carry_forward.py:"
    "_dynamic_code_primitive_name"
)
_PACKET_STATE_CLASS_IDENTITY = (
    "scripts/expert_panel_review.py:_professional_v3_packet_state_boundary."
    "<locals>._ProfessionalV3CanonicalPacketState"
)
_PACKET_STATE_ISSUER_IDENTITY = (
    "scripts/expert_panel_review.py:_professional_v3_packet_state_boundary."
    "<locals>.canonical_packet_state"
)
_OPAQUE_IDENTITY_CLOSURE_BOUNDARIES = frozenset(
    {
        _PACKET_STATE_CLASS_IDENTITY,
        _PACKET_STATE_ISSUER_IDENTITY,
    }
)
_PROCESS_LOCAL_IDENTITY_BOUNDARIES = frozenset(
    {
        # Deterministic graph construction uses process identity only as an
        # unexported lookup key.  Serialized references use graph-local IDs.
        "scripts/professional_completeness_carry_forward.py:_ContractValueProjector",
        "scripts/professional_completeness_carry_forward.py:_contains_identity_ambiguous_scalar",
        _DYNAMIC_CODE_PRIMITIVE_BOUNDARY,
        "scripts/professional_completeness_carry_forward.py:_repository_module_member_chains",
        # These implementation helpers compare inspected runtime objects while
        # constructing the closed contract graph; the values are never emitted
        # as process-local IDs.
        "scripts/professional_completeness_carry_forward.py:_callable_contract",
        "scripts/professional_completeness_carry_forward.py:_identity_observation_names",
        "scripts/professional_completeness_carry_forward.py:_process_identity_primitive_name",
        "scripts/professional_completeness_carry_forward.py:code_aware_contract_fingerprint",
        # The schema-3 packet handle deliberately uses an unforgeable seal and
        # object identity.  Its full source AST and captured seal topology are
        # still part of the review contract.
        *_OPAQUE_IDENTITY_CLOSURE_BOUNDARIES,
    }
)


def _process_identity_primitive_name(value: object) -> str | None:
    if value is builtins.id:
        return "builtins.id"
    if value is operator.is_:
        return "operator.is_"
    if value is operator.is_not:
        return "operator.is_not"
    return None


def _dynamic_code_primitive_name(value: object) -> str | None:
    if value is builtins.eval:
        return "builtins.eval"
    if value is builtins.exec:
        return "builtins.exec"
    if value is builtins.compile:
        return "builtins.compile"
    if value is builtins.__import__:
        return "builtins.__import__"
    return None


def _canonical_ast_scalar(value: object) -> object:
    if value is Ellipsis:
        return {"kind": "ellipsis"}
    if isinstance(value, bytes):
        return {"kind": "bytes", "hex": value.hex()}
    if isinstance(value, complex):
        return {
            "kind": "complex",
            "real_hex": value.real.hex(),
            "imag_hex": value.imag.hex(),
        }
    if isinstance(value, float):
        return {"kind": "float", "hex": value.hex()}
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    raise ProfessionalCarryForwardError(
        "Python AST contains an unsupported scalar value: "
        f"{type(value).__module__}.{type(value).__qualname__}"
    )


def _canonical_ast_value(value: object) -> object:
    """Project source syntax without positions, comments, or empty new fields."""

    if isinstance(value, ast.AST):
        fields: dict[str, object] = {}
        for field in value._fields:
            if field in _AST_IGNORED_FIELDS:
                continue
            field_value = getattr(value, field)
            if isinstance(field_value, list) and not field_value:
                continue
            if isinstance(value, ast.Constant) and field == "kind":
                continue
            fields[field] = _canonical_ast_value(field_value)
        return {
            "node": type(value).__name__,
            "fields": fields,
        }
    if isinstance(value, list):
        return [_canonical_ast_value(item) for item in value]
    if isinstance(value, tuple):
        return [_canonical_ast_value(item) for item in value]
    return _canonical_ast_scalar(value)


def _ast_definition_start(node: ast.AST) -> int | None:
    line = getattr(node, "lineno", None)
    decorator_lines = [
        decorator.lineno
        for decorator in getattr(node, "decorator_list", ())
        if isinstance(getattr(decorator, "lineno", None), int)
    ]
    if isinstance(line, int) and decorator_lines:
        return min(line, *decorator_lines)
    return line if isinstance(line, int) else None


def _repository_module_source(
    source_path: Path,
    *,
    cache: dict[Path, _RepositoryModuleSource],
) -> _RepositoryModuleSource:
    if source_path in cache:
        return cache[source_path]
    try:
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=source_path.as_posix())
        table = symtable.symtable(source, source_path.as_posix(), "exec")
    except (OSError, SyntaxError, UnicodeError, ValueError) as exc:
        raise ProfessionalCarryForwardError(
            f"repository module source cannot be parsed: {source_path}"
        ) from exc
    node_index: dict[_AstNodeKey, list[ast.AST]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            key = ("class", node.name, _ast_definition_start(node))
        elif isinstance(node, ast.Lambda):
            key = ("lambda", "<lambda>", _ast_definition_start(node))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            key = ("function", node.name, _ast_definition_start(node))
        else:
            continue
        node_index.setdefault(key, []).append(node)
    table_index: dict[_SymbolTableKey, list[symtable.SymbolTable]] = {}
    pending = list(table.get_children())
    while pending:
        child = pending.pop()
        key = (str(child.get_type()), child.get_name(), child.get_lineno())
        table_index.setdefault(key, []).append(child)
        pending.extend(child.get_children())
    cache[source_path] = (source, tree, table, node_index, table_index)
    return cache[source_path]


def _repository_callable_source_ast(
    function: object,
    *,
    repository_root: Path,
    source_cache: dict[Path, _RepositoryModuleSource] | None = None,
) -> tuple[ast.AST, str, dict[str, object], symtable.SymbolTable]:
    unwrapped = inspect.unwrap(function) if callable(function) else function
    source_path = _callable_source_path(function)
    root_path = repository_root.resolve()
    if (
        not (inspect.isfunction(unwrapped) or inspect.isclass(unwrapped))
        or source_path is None
        or not (source_path == root_path or root_path in source_path.parents)
    ):
        raise ProfessionalCarryForwardError(
            "contract callable is not a repository Python function or class"
        )
    source, _tree, _module_table, node_index, table_index = _repository_module_source(
        source_path, cache=source_cache if source_cache is not None else {}
    )
    function_name = getattr(unwrapped, "__name__", None)
    code = getattr(unwrapped, "__code__", None)
    if inspect.iscode(code):
        expected_start = code.co_firstlineno
    else:
        try:
            _source_lines, expected_start = inspect.getsourcelines(unwrapped)
        except (OSError, TypeError) as exc:
            raise ProfessionalCarryForwardError(
                "repository callable source is unavailable: "
                + _callable_identity(function, repository_root=root_path)
            ) from exc
    node_type = (
        "class"
        if inspect.isclass(unwrapped)
        else "lambda" if function_name == "<lambda>" else "function"
    )
    matches = node_index.get((node_type, function_name, expected_start), [])
    if len(matches) != 1:
        raise ProfessionalCarryForwardError(
            "repository callable source does not uniquely match its identity: "
            + _callable_identity(function, repository_root=root_path)
        )
    target = matches[0]
    expected_type = "class" if inspect.isclass(unwrapped) else "function"
    expected_table_name = "lambda" if function_name == "<lambda>" else function_name
    table_matches = table_index.get(
        (expected_type, str(expected_table_name), int(target.lineno)), []
    )
    if len(table_matches) != 1:
        raise ProfessionalCarryForwardError(
            "repository callable symbol table does not uniquely match its source"
        )
    selector = {
        "path": source_path.relative_to(root_path).as_posix(),
        "node": type(target).__name__,
        "name": function_name,
        "qualname": getattr(unwrapped, "__qualname__", function_name),
        "definition_start_line": expected_start,
        "definition_line": getattr(target, "lineno", None),
    }
    return target, source, selector, table_matches[0]


def _definition_time_expressions(target: ast.AST) -> list[ast.AST]:
    expressions: list[ast.AST] = []
    if isinstance(target, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
        expressions.extend(getattr(target, "decorator_list", ()))
        arguments = target.args
        expressions.extend(arguments.defaults)
        expressions.extend(
            value for value in arguments.kw_defaults if value is not None
        )
        annotated_args = [*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs]
        if arguments.vararg is not None:
            annotated_args.append(arguments.vararg)
        if arguments.kwarg is not None:
            annotated_args.append(arguments.kwarg)
        expressions.extend(
            argument.annotation
            for argument in annotated_args
            if argument.annotation is not None
        )
        returns = getattr(target, "returns", None)
        if returns is not None:
            expressions.append(returns)
    elif isinstance(target, ast.ClassDef):
        expressions.extend(target.decorator_list)
        expressions.extend(target.bases)
        expressions.extend(keyword.value for keyword in target.keywords)
    for type_parameter in getattr(target, "type_params", ()):
        for field in ("bound", "default_value"):
            value = getattr(type_parameter, field, None)
            if isinstance(value, ast.AST):
                expressions.append(value)
    return expressions


def _symbol_table_global_names(table: symtable.SymbolTable) -> set[str]:
    names: set[str] = set()
    pending = [table]
    while pending:
        current = pending.pop()
        for symbol in current.get_symbols():
            if (
                symbol.is_referenced()
                and symbol.is_global()
                and not symbol.is_local()
            ):
                names.add(symbol.get_name())
        pending.extend(
            child
            for child in current.get_children()
            if str(child.get_type()) not in _SYMTABLE_IGNORED_TYPES
        )
    return names


def _expression_global_names(
    expression: ast.AST, *, source: str, source_path: Path
) -> set[str]:
    del source
    try:
        segment = ast.unparse(expression)
    except (TypeError, ValueError) as exc:
        raise ProfessionalCarryForwardError(
            "definition-time expression source is unavailable"
        ) from exc
    if not segment.strip():
        raise ProfessionalCarryForwardError(
            "definition-time expression source is unavailable"
        )
    try:
        table = symtable.symtable(segment, source_path.as_posix(), "eval")
    except (SyntaxError, ValueError) as exc:
        raise ProfessionalCarryForwardError(
            "definition-time expression symbol table cannot be built"
        ) from exc
    return _symbol_table_global_names(table)


def _referenced_global_names(
    *,
    function: object,
    source: str,
    source_path: Path,
    target: ast.AST,
    callable_table: symtable.SymbolTable,
) -> set[str]:
    del function
    names = _symbol_table_global_names(callable_table)
    for expression in _definition_time_expressions(target):
        names.update(
            _expression_global_names(
                expression, source=source, source_path=source_path
            )
        )
    return names


def _strict_contract_value(
    value: object,
    *,
    repository_root: Path,
    allow_opaque_object: bool = False,
    projector: _ContractValueProjector | None = None,
) -> object:
    active = projector or _ContractValueProjector(
        repository_root=repository_root
    )
    projected = active.project(
        value,
        allow_opaque_object=allow_opaque_object,
        value_label="stateful contract",
    )
    return projected if projector is not None else active.envelope(projected)


def _external_callable_contract(
    function: object,
    *,
    repository_root: Path,
    projector: _ContractValueProjector | None = None,
) -> dict[str, object]:
    """Bind an external callable by public identity, never interpreter source."""

    unwrapped = inspect.unwrap(function) if callable(function) else function
    module = getattr(unwrapped, "__module__", None) or (
        f"{type(unwrapped).__module__}.{type(unwrapped).__qualname__}"
    )
    qualname = getattr(unwrapped, "__qualname__", None) or getattr(
        unwrapped, "__name__", None
    ) or type(unwrapped).__qualname__
    if module == "typing":
        callable_kind = "typing-public-symbol"
    elif inspect.isclass(unwrapped):
        callable_kind = "class"
    elif inspect.isbuiltin(unwrapped):
        callable_kind = "builtin"
    elif inspect.ismethoddescriptor(unwrapped):
        callable_kind = "method-descriptor"
    else:
        callable_kind = "function"
    contract: dict[str, object] = {
        "identity": f"{module}:{qualname}",
        "kind": callable_kind,
    }
    bound_self = getattr(function, "__self__", None)
    if bound_self is not None and not isinstance(bound_self, types.ModuleType):
        contract["bound_self"] = _strict_contract_value(
            bound_self,
            repository_root=repository_root,
            projector=projector,
        )
    safe = bool(
        inspect.isfunction(unwrapped)
        or inspect.isbuiltin(unwrapped)
        or inspect.isclass(unwrapped)
        or inspect.ismethoddescriptor(unwrapped)
        or module == "typing"
    )
    if not safe:
        raise ProfessionalCarryForwardError(
            "stateful external callable requires an explicit contract: "
            f"{module}:{qualname}; runtime_type="
            f"{type(function).__module__}.{type(function).__qualname__}"
        )
    return contract


def _callable_runtime_functions(function: object) -> list[tuple[str, object]]:
    unwrapped = inspect.unwrap(function) if callable(function) else function
    if inspect.isfunction(unwrapped):
        return [("callable", unwrapped)]
    if not inspect.isclass(unwrapped):
        return []
    values: list[tuple[str, object]] = []
    for name, member in sorted(vars(unwrapped).items()):
        if isinstance(member, (staticmethod, classmethod)):
            values.append((name, member.__func__))
        elif isinstance(member, property):
            values.extend(
                (f"{name}.{part}", candidate)
                for part, candidate in (
                    ("get", member.fget),
                    ("set", member.fset),
                    ("delete", member.fdel),
                )
                if candidate is not None
            )
        elif inspect.isfunction(member):
            values.append((name, member))
    return values


def _callable_closure_values(function: object) -> dict[str, object]:
    values: dict[str, object] = {}

    def add_function(label: str, candidate: object) -> None:
        try:
            nonlocals = inspect.getclosurevars(candidate).nonlocals
        except TypeError as exc:
            raise ProfessionalCarryForwardError(
                f"closure values are unavailable for {label}"
            ) from exc
        for name, value in sorted(nonlocals.items()):
            values[f"{label}:{name}"] = value

    for label, candidate in _callable_runtime_functions(function):
        add_function(label, candidate)
    return values


def _attribute_chains(target: ast.AST) -> set[tuple[str, ...]]:
    chains: set[tuple[str, ...]] = set()
    for node in ast.walk(target):
        if not isinstance(node, ast.Attribute):
            continue
        parts = [node.attr]
        value = node.value
        while isinstance(value, ast.Attribute):
            parts.append(value.attr)
            value = value.value
        if isinstance(value, ast.Name):
            chains.add((value.id, *reversed(parts)))
    return chains


def _repository_module_member_chains(
    target: ast.AST,
    *,
    repository_modules: Mapping[str, types.ModuleType],
    resolved_names: Mapping[str, object],
) -> set[tuple[str, ...]]:
    """Allow only closed member selection from repository module globals."""

    if not repository_modules:
        return set()
    parents: dict[int, ast.AST] = {}
    for parent in ast.walk(target):
        for child in ast.iter_child_nodes(parent):
            parents[id(child)] = parent
    allowed_dynamic_names: set[int] = set()
    selections: set[tuple[str, ...]] = set()
    for call in (node for node in ast.walk(target) if isinstance(node, ast.Call)):
        if not (
            isinstance(call.func, ast.Name)
            and call.func.id == "getattr"
            and resolved_names.get("getattr") is builtins.getattr
            and len(call.args) >= 2
            and isinstance(call.args[0], ast.Name)
            and call.args[0].id in repository_modules
        ):
            continue
        module_name = call.args[0].id
        member_node = call.args[1]
        if not (
            isinstance(member_node, ast.Constant)
            and type(member_node.value) is str
            and member_node.value
            and not member_node.value.startswith("__")
        ):
            raise ProfessionalCarryForwardError(
                "repository module getattr requires a constant public member: "
                + module_name
            )
        parent = parents.get(id(call))
        if isinstance(parent, ast.Attribute) and parent.value is call:
            raise ProfessionalCarryForwardError(
                "repository module getattr result cannot start an unbound "
                "attribute chain: "
                + module_name
                + "."
                + member_node.value
            )
        allowed_dynamic_names.add(id(call.args[0]))
        selections.add((module_name, member_node.value))

    for node in (item for item in ast.walk(target) if isinstance(item, ast.Name)):
        if node.id not in repository_modules:
            continue
        parent = parents.get(id(node))
        if isinstance(parent, ast.Attribute) and parent.value is node:
            outermost: ast.AST = parent
            while True:
                candidate = parents.get(id(outermost))
                if not (
                    isinstance(candidate, ast.Attribute)
                    and candidate.value is outermost
                ):
                    break
                outermost = candidate
            parts: list[str] = []
            selected: ast.AST = outermost
            while isinstance(selected, ast.Attribute):
                parts.append(selected.attr)
                selected = selected.value
            if not isinstance(selected, ast.Name) or selected.id != node.id:
                raise ProfessionalCarryForwardError(
                    "repository module attribute chain is not canonical"
                )
            if any(part.startswith("__") for part in parts):
                raise ProfessionalCarryForwardError(
                    "repository module metadata member is unsupported: "
                    + node.id
                )
            selections.add((node.id, *reversed(parts)))
            continue
        if id(node) in allowed_dynamic_names:
            continue
        raise ProfessionalCarryForwardError(
            "repository module has unsupported dynamic or bare use: " + node.id
        )
    return selections


def _contains_identity_ambiguous_scalar(
    value: object, *, seen: set[int] | None = None
) -> bool:
    if value is None or value is Ellipsis or type(value) is bool:
        return False
    if type(value) in {str, int, float, bytes}:
        return True
    if type(value) is re.Pattern:
        return False
    if isinstance(value, Path) and type(value).__module__ == "pathlib":
        return False
    if callable(value) or isinstance(value, types.ModuleType):
        return False
    if type(value) is object:
        return False
    active_seen = seen if seen is not None else set()
    object_id = id(value)
    if object_id in active_seen:
        return False
    active_seen.add(object_id)
    if type(value) is dict:
        return any(
            _contains_identity_ambiguous_scalar(item, seen=active_seen)
            for row in value.items()
            for item in row
        )
    if type(value) in {list, tuple, set, frozenset}:
        return any(
            _contains_identity_ambiguous_scalar(item, seen=active_seen)
            for item in value
        )
    try:
        state = vars(value)
    except TypeError:
        return True
    return _contains_identity_ambiguous_scalar(state, seen=active_seen)


def _identity_observation_names(
    target: ast.AST,
    *,
    callable_identity: str,
    resolved_names: Mapping[str, object],
) -> None:
    """Reject process-local identity semantics outside exact boundaries.

    Scalar identity depends on interpreter interning and allocation.  A direct
    check in a caller is not enough: a reachable helper can observe the same
    values through parameters.  Therefore every reachable callable is checked
    independently and any unproved non-singleton comparison fails closed.
    """

    allow_process_identity = (
        callable_identity in _PROCESS_LOCAL_IDENTITY_BOUNDARIES
    )
    allow_dynamic_code = (
        callable_identity == _DYNAMIC_CODE_PRIMITIVE_BOUNDARY
    )
    local_imports = [
        node
        for node in ast.walk(target)
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    if local_imports:
        raise ProfessionalCarryForwardError(
            "callable-local imports are unsupported for " + callable_identity
        )

    def names_in(node: ast.AST) -> set[str]:
        return {
            candidate.id
            for candidate in ast.walk(node)
            if isinstance(candidate, ast.Name)
            and candidate.id in resolved_names
        }

    def singleton_operand(node: ast.AST) -> bool:
        if isinstance(node, ast.Constant):
            return (
                node.value is None
                or node.value is Ellipsis
                or type(node.value) is bool
            )
        if not isinstance(node, ast.Name) or node.id not in resolved_names:
            return False
        value = resolved_names[node.id]
        return (
            value is None
            or value is Ellipsis
            or type(value) is bool
        )

    def static_value(node: ast.AST) -> tuple[bool, object | None]:
        if isinstance(node, ast.Name) and node.id in resolved_names:
            return True, resolved_names[node.id]
        if isinstance(node, ast.Call):
            available, target = static_value(node.func)
            if not (
                available
                and target is builtins.getattr
                and len(node.args) == 2
                and not node.keywords
                and isinstance(node.args[1], ast.Constant)
                and type(node.args[1].value) is str
                and node.args[1].value
                and not node.args[1].value.startswith("__")
            ):
                return False, None
            base_available, base = static_value(node.args[0])
            if not base_available:
                return False, None
            try:
                return True, inspect.getattr_static(base, node.args[1].value)
            except AttributeError:
                return False, None
        if not isinstance(node, ast.Attribute) or node.attr.startswith("__"):
            return False, None
        available, base = static_value(node.value)
        if not available:
            return False, None
        try:
            return True, inspect.getattr_static(base, node.attr)
        except AttributeError:
            return False, None

    def type_call(node: ast.AST) -> bool:
        return (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "type"
            and resolved_names.get("type") is builtins.type
            and len(node.args) == 1
            and not node.keywords
        )

    def exact_type_check(left: ast.AST, right: ast.AST) -> bool:
        if type_call(left):
            available, expected_type = static_value(right)
        elif type_call(right):
            available, expected_type = static_value(left)
        else:
            return False
        return available and inspect.isclass(expected_type)

    def reject_comparison(left: ast.AST, right: ast.AST) -> None:
        scalar_names = sorted(
            name
            for name in names_in(left) | names_in(right)
            if _contains_identity_ambiguous_scalar(resolved_names[name])
        )
        if scalar_names:
            raise ProfessionalCarryForwardError(
                "identity comparison observes scalar contract state for "
                + callable_identity
                + ": "
                + ",".join(scalar_names)
            )
        raise ProfessionalCarryForwardError(
            "unsupported non-singleton identity comparison for "
            + callable_identity
        )

    def validate_pair(left: ast.AST, right: ast.AST) -> None:
        if allow_process_identity:
            return
        if singleton_operand(left) or singleton_operand(right):
            return
        if exact_type_check(left, right):
            return
        reject_comparison(left, right)

    parents: dict[int, ast.AST] = {}
    for parent in ast.walk(target):
        for child in ast.iter_child_nodes(parent):
            parents[id(child)] = parent

    for node in ast.walk(target):
        available, value = static_value(node)
        if not available:
            continue
        primitive_name = _process_identity_primitive_name(value)
        if primitive_name is not None and not allow_process_identity:
            if primitive_name == "builtins.id":
                raise ProfessionalCarryForwardError(
                    "process-local id() observes contract state for "
                    + callable_identity
                )
            raise ProfessionalCarryForwardError(
                "process-local identity primitive is unsupported for "
                + callable_identity
                + ": "
                + primitive_name
            )
        dynamic_name = _dynamic_code_primitive_name(value)
        if dynamic_name is not None and not allow_dynamic_code:
            raise ProfessionalCarryForwardError(
                "dynamic code or import primitive is unsupported for "
                + callable_identity
                + ": "
                + dynamic_name
            )

    if not allow_process_identity:
        for node in (
            candidate
            for candidate in ast.walk(target)
            if isinstance(candidate, ast.Name)
            and (
                resolved_names.get(candidate.id) is builtins
                or resolved_names.get(candidate.id) is operator
            )
        ):
            parent = parents.get(id(node))
            if (
                isinstance(parent, ast.Attribute)
                and parent.value is node
                and not parent.attr.startswith("__")
            ):
                continue
            if (
                isinstance(parent, ast.Call)
                and len(parent.args) >= 2
                and parent.args[0] is node
            ):
                target_available, target_value = static_value(parent.func)
                if (
                    target_available
                    and target_value is builtins.getattr
                    and isinstance(parent.args[1], ast.Constant)
                    and type(parent.args[1].value) is str
                    and parent.args[1].value
                    and not parent.args[1].value.startswith("__")
                ):
                    continue
            raise ProfessionalCarryForwardError(
                "identity-sensitive module has unsupported dynamic or bare use for "
                + callable_identity
                + ": "
                + node.id
            )

    opaque_names = {
        name for name, value in resolved_names.items() if type(value) is object
    }
    if opaque_names:
        for node in (
            candidate
            for candidate in ast.walk(target)
            if isinstance(candidate, ast.Name)
            and candidate.id in opaque_names
        ):
            parent = parents.get(id(node))
            allowed = False
            if callable_identity == _PACKET_STATE_CLASS_IDENTITY:
                allowed = (
                    isinstance(parent, ast.Compare)
                    and len(parent.ops) == 1
                    and isinstance(parent.ops[0], (ast.Is, ast.IsNot))
                    and parent.comparators == [node]
                    and isinstance(parent.left, ast.Attribute)
                    and isinstance(parent.left.value, ast.Name)
                    and parent.left.value.id == "self"
                    and parent.left.attr == "__seal"
                )
            elif (
                callable_identity == _PACKET_STATE_ISSUER_IDENTITY
                and isinstance(parent, ast.Dict)
            ):
                allowed = any(
                    value is node
                    and isinstance(key, ast.Constant)
                    and key.value == "seal"
                    for key, value in zip(parent.keys, parent.values, strict=True)
                )
            if not allowed:
                raise ProfessionalCarryForwardError(
                    "opaque identity closure has unsupported use for "
                    + callable_identity
                    + ": "
                    + node.id
                )

    for comparison in (
        node for node in ast.walk(target) if isinstance(node, ast.Compare)
    ):
        operands = [comparison.left, *comparison.comparators]
        for index, comparison_operator in enumerate(comparison.ops):
            if not isinstance(comparison_operator, (ast.Is, ast.IsNot)):
                continue
            left = operands[index]
            right = operands[index + 1]
            validate_pair(left, right)

    for call in (node for node in ast.walk(target) if isinstance(node, ast.Call)):
        target_available, call_target = static_value(call.func)
        primitive_name = (
            _process_identity_primitive_name(call_target)
            if target_available
            else None
        )
        if primitive_name == "builtins.id":
            if not allow_process_identity:
                raise ProfessionalCarryForwardError(
                    "process-local id() observes contract state for "
                    + callable_identity
                )
        elif primitive_name in {"operator.is_", "operator.is_not"}:
            if len(call.args) != 2 or call.keywords:
                raise ProfessionalCarryForwardError(
                    primitive_name
                    + " call shape is unsupported for "
                    + callable_identity
                )
            validate_pair(call.args[0], call.args[1])


def _is_functools_cache_wrapper(value: object) -> bool:
    cache_parameters = getattr(value, "cache_parameters", None)
    if type(value).__module__ != "functools" or not callable(cache_parameters):
        return False
    try:
        parameters = cache_parameters()
    except (TypeError, ValueError):
        return False
    return isinstance(parameters, Mapping) and set(parameters) == {
        "maxsize",
        "typed",
    }


def _callable_contract(
    function: object,
    *,
    repository_root: Path,
    source_cache: dict[Path, _RepositoryModuleSource],
) -> dict[str, Any]:
    unwrapped = inspect.unwrap(function) if callable(function) else function
    target, _, selector, _ = _repository_callable_source_ast(
        function,
        repository_root=repository_root,
        source_cache=source_cache,
    )
    wrapper_contract: dict[str, Any] | None = None
    if unwrapped is not function:
        if not _is_functools_cache_wrapper(function):
            raise ProfessionalCarryForwardError(
                "repository callable wrapper has unsupported runtime state: "
                + _callable_identity(function, repository_root=repository_root)
            )
        cache_parameters = getattr(function, "cache_parameters", None)
        wrapper_contract = {
            "kind": "functools-cache-wrapper",
            "cache_parameters": (
                _contract_value(
                    cache_parameters(), repository_root=repository_root
                )
                if callable(cache_parameters)
                else None
            ),
        }
    behavior: dict[str, Any] = {
        "representation": _PYTHON_SOURCE_AST_CONTRACT,
        "source_selector": {
            "path": selector["path"],
            "node": selector["node"],
            "qualname": selector["qualname"],
        },
        "ast": _canonical_ast_value(target),
    }
    return {
        "identity": _callable_identity(
            function, repository_root=repository_root
        ),
        "behavior": behavior,
        "wrapper": wrapper_contract,
    }


def code_aware_contract_fingerprint(
    *,
    contract_name: str,
    root_callables: Iterable[object],
    constants: Mapping[str, object],
    repository_root: Path,
    opaque_repository_callables: Iterable[object] = (),
) -> str:
    """Fingerprint only the reachable repository callable/constant contract.

    Unlike hashing a whole script, unrelated edits cannot stale the review
    contract.  Unlike a manual version string, a relevant callable,
    definition-time dependency, lexical global, runtime default, or closure
    state change necessarily changes the digest or fails closed.
    """

    if not isinstance(contract_name, str) or not contract_name.strip():
        raise ProfessionalCarryForwardError("contract_name must be non-empty")
    roots = list(root_callables)
    opaque_callables = list(opaque_repository_callables)
    if not roots or not all(callable(item) for item in roots):
        raise ProfessionalCarryForwardError(
            "root_callables must contain callable values"
        )
    root_path = repository_root.resolve()
    value_projector = _ContractValueProjector(repository_root=root_path)
    source_cache: dict[Path, _RepositoryModuleSource] = {}
    root_identities = [
        _callable_identity(item, repository_root=root_path) for item in roots
    ]
    if len(root_identities) != len(set(root_identities)):
        raise ProfessionalCarryForwardError(
            "root_callables contain a duplicate repository identity"
        )
    for root in roots:
        _repository_callable_source_ast(
            root, repository_root=root_path, source_cache=source_cache
        )
    pending = list(roots)
    opaque_identities = {
        _callable_identity(item, repository_root=root_path)
        for item in opaque_callables
    }
    for opaque in opaque_callables:
        _repository_callable_source_ast(
            opaque, repository_root=root_path, source_cache=source_cache
        )
    functions: dict[str, dict[str, Any]] = {}
    function_objects: dict[str, object] = {}
    repository_callable_objects: dict[str, object] = {}
    bindings: dict[str, dict[str, Any]] = {}
    referenced_constants: dict[str, object] = {}

    def register_repository_callable(value: object) -> str:
        identity = _callable_identity(value, repository_root=root_path)
        existing = repository_callable_objects.get(identity)
        if existing is not None and existing is not value:
            raise ProfessionalCarryForwardError(
                "repository callable identity collision: " + identity
            )
        repository_callable_objects[identity] = value
        return identity

    for root in roots:
        register_repository_callable(root)
    for opaque in opaque_callables:
        register_repository_callable(opaque)

    def repository_path(value: object) -> Path | None:
        path = _callable_source_path(value)
        if path is not None and (path == root_path or root_path in path.parents):
            return path
        return None

    def bind_value(
        binding_key: str,
        value: object,
        *,
        allow_opaque_object: bool = False,
        allow_process_identity: bool = False,
    ) -> None:
        primitive_name = _process_identity_primitive_name(value)
        if primitive_name is not None and not allow_process_identity:
            if primitive_name == "builtins.id":
                raise ProfessionalCarryForwardError(
                    "process-local id() observes contract state for "
                    + binding_key
                )
            raise ProfessionalCarryForwardError(
                "process-local identity primitive is unsupported for "
                + binding_key
                + ": "
                + primitive_name
            )
        dynamic_name = _dynamic_code_primitive_name(value)
        if (
            dynamic_name is not None
            and not binding_key.startswith(
                _DYNAMIC_CODE_PRIMITIVE_BOUNDARY + ":"
            )
        ):
            raise ProfessionalCarryForwardError(
                "dynamic code or import primitive is unsupported for "
                + binding_key
                + ": "
                + dynamic_name
            )
        if isinstance(value, types.ModuleType):
            module_file = getattr(value, "__file__", None)
            module_path = (
                Path(module_file).resolve()
                if isinstance(module_file, str)
                else None
            )
            if module_path is not None and (
                module_path == root_path or root_path in module_path.parents
            ):
                module_identity = module_path.relative_to(root_path).as_posix()
                bindings[binding_key] = {
                    "kind": "repository-module",
                    "path": module_identity,
                    "identity_ref": value_projector.identity_reference(
                        value,
                        kind="repository-module-identity",
                        identity=module_identity,
                    ),
                }
            else:
                module_identity = getattr(
                    value, "__name__", type(value).__qualname__
                )
                bindings[binding_key] = {
                    "kind": "external-module",
                    "identity": module_identity,
                    "identity_ref": value_projector.identity_reference(
                        value,
                        kind="external-module-identity",
                        identity=module_identity,
                    ),
                }
            return
        if isinstance(value, types.UnionType):
            bindings[binding_key] = {"kind": "union-type"}
            for index, argument in enumerate(value.__args__):
                bind_value(
                    f"{binding_key}:argument:{index}",
                    argument,
                    allow_process_identity=allow_process_identity,
                )
            return
        if isinstance(value, types.GenericAlias):
            bindings[binding_key] = {
                "kind": "generic-alias",
                "identity_ref": value_projector.identity_reference(
                    value,
                    kind="generic-alias-identity",
                    identity="types.GenericAlias",
                ),
            }
            bind_value(
                f"{binding_key}:origin",
                value.__origin__,
                allow_process_identity=allow_process_identity,
            )
            for index, argument in enumerate(value.__args__):
                bind_value(
                    f"{binding_key}:argument:{index}",
                    argument,
                    allow_process_identity=allow_process_identity,
                )
            return
        typing_origin = typing.get_origin(value)
        if typing_origin is not None:
            bindings[binding_key] = {
                "kind": "typing-parameterized",
                "identity_ref": value_projector.identity_reference(
                    value,
                    kind="typing-parameterized-identity",
                    identity=(
                        f"{type(value).__module__}.{type(value).__qualname__}"
                    ),
                ),
            }
            bind_value(
                f"{binding_key}:origin",
                typing_origin,
                allow_process_identity=allow_process_identity,
            )
            for index, argument in enumerate(typing.get_args(value)):
                bind_value(
                    f"{binding_key}:argument:{index}",
                    argument,
                    allow_process_identity=allow_process_identity,
                )
            return
        if isinstance(value, functools.partial):
            bindings[binding_key] = {
                "kind": "partial-callable",
                "identity_ref": value_projector.identity_reference(
                    value,
                    kind="partial-callable-identity",
                    identity="functools.partial",
                ),
            }
            bind_value(
                f"{binding_key}:function",
                value.func,
                allow_process_identity=allow_process_identity,
            )
            for index, argument in enumerate(value.args):
                bind_value(
                    f"{binding_key}:argument:{index}",
                    argument,
                    allow_process_identity=allow_process_identity,
                )
            for name, argument in sorted((value.keywords or {}).items()):
                bind_value(
                    f"{binding_key}:keyword:{name}",
                    argument,
                    allow_process_identity=allow_process_identity,
                )
            return
        if inspect.ismethod(value) and value.__self__ is not None:
            method_identity = _callable_identity(
                value.__func__, repository_root=root_path
            )
            bindings[binding_key] = {
                "kind": "bound-method",
                "identity_ref": value_projector.identity_reference(
                    value,
                    kind="bound-method-identity",
                    identity=method_identity,
                ),
            }
            bind_value(
                f"{binding_key}:function",
                value.__func__,
                allow_process_identity=allow_process_identity,
            )
            bind_value(
                f"{binding_key}:self",
                value.__self__,
                allow_process_identity=allow_process_identity,
            )
            return
        value_unwrapped = inspect.unwrap(value) if callable(value) else value
        value_path = repository_path(value)
        if callable(value) and value_path is not None:
            if not (
                inspect.isfunction(value_unwrapped)
                or inspect.isclass(value_unwrapped)
            ):
                raise ProfessionalCarryForwardError(
                    "stateful repository callable requires an explicit contract: "
                    + _callable_identity(value, repository_root=root_path)
                )
            target_identity = register_repository_callable(value)
            if target_identity in opaque_identities:
                bindings[binding_key] = {
                    "kind": "opaque-repository-boundary",
                    "target": target_identity,
                    "identity_ref": value_projector.identity_reference(
                        value,
                        kind="repository-callable-identity",
                        identity=target_identity,
                    ),
                }
            else:
                bindings[binding_key] = {
                    "kind": "repository-callable",
                    "target": target_identity,
                    "identity_ref": value_projector.identity_reference(
                        value,
                        kind="repository-callable-identity",
                        identity=target_identity,
                    ),
                }
                pending.append(value)
            return
        if callable(value):
            try:
                external_contract = _external_callable_contract(
                    value,
                    repository_root=root_path,
                    projector=value_projector,
                )
            except ProfessionalCarryForwardError as exc:
                raise ProfessionalCarryForwardError(
                    f"{binding_key}: {exc}"
                ) from exc
            bindings[binding_key] = {
                "kind": "external-callable",
                "contract": external_contract,
                "identity_ref": value_projector.identity_reference(
                    value,
                    kind="external-callable-identity",
                    identity=(
                        str(external_contract["identity"])
                        + ":"
                        + str(external_contract["kind"])
                    ),
                ),
            }
            return
        value_type = type(value)
        type_path = repository_path(value_type)
        if type_path is not None:
            target_identity = _callable_identity(
                value_type, repository_root=root_path
            )
            try:
                state = vars(value)
            except TypeError as exc:
                raise ProfessionalCarryForwardError(
                    "repository instance state is unavailable: " + target_identity
                ) from exc
            bindings[binding_key] = {
                "kind": "repository-instance",
                "target": target_identity,
                "state": _strict_contract_value(
                    state,
                    repository_root=root_path,
                    allow_opaque_object=allow_opaque_object,
                    projector=value_projector,
                ),
            }
            pending.append(value_type)
            return
        referenced_constants[binding_key] = _strict_contract_value(
            value,
            repository_root=root_path,
            allow_opaque_object=allow_opaque_object,
            projector=value_projector,
        )

    while pending:
        function = pending.pop()
        unwrapped = inspect.unwrap(function)
        identity = _callable_identity(function, repository_root=root_path)
        contract = _callable_contract(
            function, repository_root=root_path, source_cache=source_cache
        )
        if identity in functions:
            if (
                functions[identity] != contract
                or function_objects[identity] is not function
            ):
                raise ProfessionalCarryForwardError(
                    "repository callable identity collision: " + identity
                )
            continue
        functions[identity] = contract
        function_objects[identity] = function
        allow_process_identity = (
            identity in _PROCESS_LOCAL_IDENTITY_BOUNDARIES
        )
        namespace = getattr(unwrapped, "__globals__", None)
        if not isinstance(namespace, dict) and inspect.isclass(unwrapped):
            module = inspect.getmodule(unwrapped)
            namespace = vars(module) if module is not None else None
        if not isinstance(namespace, dict):
            continue
        target_ast, source, _, callable_table = _repository_callable_source_ast(
            function,
            repository_root=root_path,
            source_cache=source_cache,
        )
        source_path = _callable_source_path(function)
        if source_path is None:
            raise ProfessionalCarryForwardError(
                "repository callable source path is unavailable"
            )
        if inspect.isclass(unwrapped):
            direct_free_names = sorted(
                symbol.get_name()
                for symbol in callable_table.get_symbols()
                if symbol.is_free() and symbol.is_referenced()
            )
            if direct_free_names:
                raise ProfessionalCarryForwardError(
                    "repository class body captures unsupported runtime state: "
                    + identity
                    + "; free_names="
                    + ",".join(direct_free_names)
                )
        for callable_label, runtime_function in _callable_runtime_functions(
            function
        ):
            runtime_unwrapped = inspect.unwrap(runtime_function)
            if (
                runtime_unwrapped is not runtime_function
                and not _is_functools_cache_wrapper(runtime_function)
            ):
                raise ProfessionalCarryForwardError(
                    "repository callable wrapper has unsupported runtime state: "
                    + identity
                    + "; member="
                    + callable_label
                )
            defaults = getattr(runtime_function, "__defaults__", None) or ()
            for index, default in enumerate(defaults):
                bind_value(
                    f"{identity}:runtime:{callable_label}:default:{index}",
                    default,
                    allow_process_identity=allow_process_identity,
                )
            kwdefaults = (
                getattr(runtime_function, "__kwdefaults__", None) or {}
            )
            for name, default in sorted(kwdefaults.items()):
                bind_value(
                    f"{identity}:runtime:{callable_label}:kwdefault:{name}",
                    default,
                    allow_process_identity=allow_process_identity,
                )
        dependency_names = _referenced_global_names(
            function=function,
            source=source,
            source_path=source_path,
            target=target_ast,
            callable_table=callable_table,
        )
        closure_values = _callable_closure_values(function)
        direct_closure_values = {
            key.removeprefix("callable:"): value
            for key, value in closure_values.items()
            if key.startswith("callable:")
        }
        resolved_names: dict[str, object] = {}
        for dependency_name in sorted(dependency_names):
            if dependency_name in {
                "__cached__",
                "__file__",
                "__loader__",
                "__name__",
                "__package__",
                "__spec__",
            }:
                bindings[f"{identity}:global:{dependency_name}"] = {
                    "kind": "repository-module-metadata",
                    "field": dependency_name,
                    "path": source_path.relative_to(root_path).as_posix(),
                }
                continue
            if dependency_name in direct_closure_values:
                dependency = direct_closure_values[dependency_name]
            elif dependency_name in namespace:
                dependency = namespace[dependency_name]
            elif dependency_name in vars(builtins):
                dependency = vars(builtins)[dependency_name]
            else:
                raise ProfessionalCarryForwardError(
                    f"referenced global {dependency_name!r} is unresolved for {identity}"
                )
            resolved_names[dependency_name] = dependency
            bind_value(
                f"{identity}:global:{dependency_name}",
                dependency,
                allow_process_identity=allow_process_identity,
            )
        for closure_name, closure_value in sorted(closure_values.items()):
            closure_variable_name = closure_name.rsplit(":", 1)[-1]
            if (
                closure_variable_name in resolved_names
                and resolved_names[closure_variable_name] is not closure_value
            ):
                raise ProfessionalCarryForwardError(
                    "closure dependency name resolves to multiple values: "
                    + closure_variable_name
                )
            resolved_names.setdefault(closure_variable_name, closure_value)
            bind_value(
                f"{identity}:closure:{closure_name}",
                closure_value,
                allow_opaque_object=(
                    identity in _OPAQUE_IDENTITY_CLOSURE_BOUNDARIES
                    and closure_variable_name == "seal"
                    and type(closure_value) is object
                ),
                allow_process_identity=allow_process_identity,
            )
        _identity_observation_names(
            target_ast,
            callable_identity=identity,
            resolved_names=resolved_names,
        )
        repository_modules: dict[str, types.ModuleType] = {}
        for name, value in resolved_names.items():
            if not isinstance(value, types.ModuleType):
                continue
            module_file = getattr(value, "__file__", None)
            module_path = (
                Path(module_file).resolve()
                if isinstance(module_file, str)
                else None
            )
            if module_path is not None and (
                module_path == root_path or root_path in module_path.parents
            ):
                repository_modules[name] = value
        module_chains = _repository_module_member_chains(
            target_ast,
            repository_modules=repository_modules,
            resolved_names=resolved_names,
        )
        for chain in sorted(module_chains):
            base_name = chain[0]
            base = repository_modules[base_name]
            selected: object = base
            try:
                for attribute in chain[1:]:
                    selected = getattr(selected, attribute)
            except AttributeError as exc:
                raise ProfessionalCarryForwardError(
                    "repository module attribute is unresolved: " + ".".join(chain)
                ) from exc
            if isinstance(selected, types.ModuleType):
                raise ProfessionalCarryForwardError(
                    "repository module member resolves to an unbound module: "
                    + ".".join(chain)
                )
            bind_value(
                f"{identity}:attribute:{'.'.join(chain)}",
                selected,
                allow_process_identity=allow_process_identity,
            )
    explicit_constants = _contract_value(
        constants,
        repository_root=root_path,
        projector=value_projector,
    )
    payload = {
        "contract": contract_name,
        "callable_representation": _PYTHON_SOURCE_AST_CONTRACT,
        "identity_observation_policy": {
            "version": _PROCESS_LOCAL_IDENTITY_POLICY,
            "exact_boundaries": sorted(_PROCESS_LOCAL_IDENTITY_BOUNDARIES),
            "opaque_closure_boundaries": sorted(
                _OPAQUE_IDENTITY_CLOSURE_BOUNDARIES
            ),
            "opaque_closure_name": "seal",
            "opaque_usage": "exact-packet-seal-v1",
        },
        "root_callables": sorted(
            root_identities
        ),
        "functions": {key: functions[key] for key in sorted(functions)},
        "bindings": {key: bindings[key] for key in sorted(bindings)},
        "referenced_constants": {
            key: referenced_constants[key]
            for key in sorted(referenced_constants)
        },
        "explicit_constants": explicit_constants,
        "value_nodes": value_projector.nodes(),
        "opaque_repository_callables": sorted(opaque_identities),
    }
    return canonical_json_sha256(payload)
