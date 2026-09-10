"""Mutation-safe review-cost fixtures shared by Professional panel tests."""

from __future__ import annotations

import copy
import functools

from .expert_panel_source_test_support import CARRY, PANEL, REGRESSION, ROOT
from .professional_completeness_test_support import _catalog

def _reviewer_added_request(
    bindings: dict[str, dict],
    *,
    targets: list[dict],
    target_id: str,
    candidate_id: str,
) -> dict:
    target = next(row for row in targets if row["skill_id"] == target_id)
    ranking = next(
        row
        for row in target["routing_adjacency"]["full_catalog_ranking"]
        if row["skill_id"] == candidate_id
    )
    return {
        "skill_id": candidate_id,
        "discovery_reason": (
            "The discovery boundary exposes a distinct overlapping responsibility."
        ),
        "ranking_evidence": copy.deepcopy(ranking),
        "material_fingerprint": bindings[candidate_id][
            "content_fingerprint"
        ],
    }

def _current_catalog_cost_state_cached() -> dict:
    packet = REGRESSION._current_professional_completeness_packet()
    state = PANEL._professional_v3_packet_state(
        packet,
        validation_root=ROOT,
        artifact_path=None,
        validate_baseline=False,
    )
    bindings = state["bindings"]
    target_ids = sorted(bindings)
    discovery = PANEL._professional_v3_discovery_projection_from_packet(
        packet=packet,
        assigned_skill_ids=target_ids,
        bindings=bindings,
    )
    final = PANEL._professional_v3_capsule_projection_from_packet(
        packet=packet,
        assigned_skill_ids=target_ids,
        reviewer_added_requests_by_target=None,
        bindings=bindings,
    )
    index = REGRESSION._professional_review_cost_block_index(
        review_contract_fingerprint=packet["review_contract_fingerprint"],
        discovery_projection=discovery,
        reviewer_added_requests=[],
        final_projection=final,
    )
    reverse_dependencies = {skill_id: {skill_id} for skill_id in target_ids}
    for target_id, binding in bindings.items():
        for candidate_id in binding["dependency_material_bindings"]:
            reverse_dependencies[candidate_id].add(target_id)
    return {
        "packet": packet,
        "bindings": bindings,
        "target_ids": target_ids,
        "index": index,
        "reverse_dependencies": reverse_dependencies,
    }

def _synthetic_catalog_cost_state_cached() -> dict:
    targets = _catalog()
    bindings = CARRY.professional_review_bindings(targets)
    target_ids = sorted(bindings)
    request = _reviewer_added_request(
        bindings,
        targets=targets,
        target_id="a",
        candidate_id="b",
    )
    requests_by_target = {"a": [request]}
    request_rows = [{"target_skill_id": "a", **request}]
    discovery = CARRY.project_professional_discovery_capsule(
        bindings=bindings,
        review_targets=targets,
        assigned_fresh_target_ids=target_ids,
    )
    final = CARRY.project_professional_review_capsule(
        bindings=bindings,
        review_targets=targets,
        assigned_fresh_target_ids=target_ids,
        reviewer_added_requests_by_target=requests_by_target,
    )
    packet = {
        "review_contract_fingerprint": "4" * 64,
        "professional_targets": targets,
    }
    index = REGRESSION._professional_review_cost_block_index(
        review_contract_fingerprint=packet["review_contract_fingerprint"],
        discovery_projection=discovery,
        reviewer_added_requests=request_rows,
        final_projection=final,
    )
    return {
        "packet": packet,
        "bindings": bindings,
        "index": index,
        "requests_by_target": requests_by_target,
    }

@functools.lru_cache(maxsize=1)
def _current_catalog_cost_state_cache() -> dict:
    return _current_catalog_cost_state_cached()


def _current_catalog_cost_state() -> dict:
    cached = _current_catalog_cost_state_cache()
    return {
        key: value if key == "index" else copy.deepcopy(value)
        for key, value in cached.items()
    }


@functools.lru_cache(maxsize=1)
def _synthetic_catalog_cost_state_cache() -> dict:
    return _synthetic_catalog_cost_state_cached()


def _synthetic_catalog_cost_state() -> dict:
    cached = _synthetic_catalog_cost_state_cache()
    return {
        key: value if key == "index" else copy.deepcopy(value)
        for key, value in cached.items()
    }
