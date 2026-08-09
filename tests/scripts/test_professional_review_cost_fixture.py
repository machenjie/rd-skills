from __future__ import annotations

import copy
import functools
import importlib.util
import json
import sys
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest import mock

from . import test_professional_completeness_carry_forward as fixtures


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _load_regression_module():
    path = SCRIPTS / "validate-professionalism-regression.py"
    spec = importlib.util.spec_from_file_location(
        "professional_review_cost_fixture_tests",
        path,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


REGRESSION = _load_regression_module()
PANEL = REGRESSION.expert_panel
CARRY = PANEL.professional_carry


def _reviewer_added_request(
    bindings: dict[str, dict],
    *,
    target_id: str,
    candidate_id: str,
) -> dict:
    ranking = next(
        row
        for row in bindings[target_id]["adjacency"]["full_catalog_ranking"]
        if row["skill_id"] == candidate_id
    )
    return {
        "skill_id": candidate_id,
        "discovery_reason": (
            "The discovery boundary exposes a distinct overlapping responsibility."
        ),
        "ranking_evidence": copy.deepcopy(ranking),
        "material_fingerprint": bindings[candidate_id][
            "candidate_material_fingerprint"
        ],
    }


@functools.lru_cache(maxsize=1)
def _current_catalog_cost_state() -> dict:
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
        source_fingerprints=packet["source_fingerprints"],
        review_contract_fingerprint=packet["review_contract_fingerprint"],
        discovery_projection=discovery,
        reviewer_added_requests=[],
        final_projection=final,
    )
    reverse_dependencies = {skill_id: {skill_id} for skill_id in target_ids}
    for target_id, binding in bindings.items():
        for candidate in binding["required_candidate_material_bindings"]:
            reverse_dependencies[candidate["skill_id"]].add(target_id)
    return {
        "packet": packet,
        "bindings": bindings,
        "target_ids": target_ids,
        "index": index,
        "reverse_dependencies": reverse_dependencies,
    }


@functools.lru_cache(maxsize=1)
def _synthetic_catalog_cost_state() -> dict:
    targets = fixtures._catalog()
    bindings = CARRY.professional_review_bindings(targets)
    target_ids = sorted(bindings)
    request = _reviewer_added_request(
        bindings,
        target_id="a",
        candidate_id="b",
    )
    requests_by_target = {"a": [request]}
    request_rows = [{"target_skill_id": "a", **request}]
    discovery = CARRY.project_professional_discovery_capsule(
        bindings=bindings,
        assigned_fresh_target_ids=target_ids,
    )
    final = CARRY.project_professional_review_capsule(
        bindings=bindings,
        assigned_fresh_target_ids=target_ids,
        reviewer_added_requests_by_target=requests_by_target,
    )
    packet = {
        "source_fingerprints": {
            "professional_packages": "1" * 64,
            "professional_review_bindings": "2" * 64,
            "professional_review_contract": "3" * 64,
        },
        "review_contract_fingerprint": "4" * 64,
    }
    index = REGRESSION._professional_review_cost_block_index(
        source_fingerprints=packet["source_fingerprints"],
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


class ProfessionalReviewCostFixtureTests(unittest.TestCase):
    def test_shared_fixture_uses_current_unittest_package(self) -> None:
        expected_module = (
            f"{__package__}.test_professional_completeness_carry_forward"
        )
        self.assertEqual(expected_module, fixtures.__name__)
        self.assertIs(fixtures, sys.modules[expected_module])
        self.assertIs(fixtures.PANEL, sys.modules[fixtures.PANEL.__name__])

    def _assert_exact_legacy_equivalence(
        self,
        *,
        packet: dict,
        bindings: dict[str, dict],
        index,
        fresh_ids: list[str],
        reviewer_added_requests_by_target: dict[str, list[dict]] | None = None,
    ) -> None:
        discovery = PANEL._professional_v3_discovery_projection_from_packet(
            packet=packet,
            assigned_skill_ids=fresh_ids,
            bindings=bindings,
        )
        final = PANEL._professional_v3_capsule_projection_from_packet(
            packet=packet,
            assigned_skill_ids=fresh_ids,
            reviewer_added_requests_by_target=(
                reviewer_added_requests_by_target
            ),
            bindings=bindings,
        )
        request_rows = [
            {"target_skill_id": target_id, **request}
            for target_id in sorted(reviewer_added_requests_by_target or {})
            for request in (reviewer_added_requests_by_target or {})[target_id]
        ]
        legacy = PANEL._professional_v3_effective_input_blocks(
            source_fingerprints=packet["source_fingerprints"],
            review_contract_fingerprint=packet[
                "review_contract_fingerprint"
            ],
            discovery_projection=discovery,
            assigned_skill_ids=fresh_ids,
            reviewer_added_requests=request_rows,
            final_projection=final,
        )
        optimized = REGRESSION._professional_review_cost_case_input_blocks(
            index,
            fresh_skill_ids=fresh_ids,
        )
        self.assertEqual(legacy, optimized)
        self.assertEqual(
            CARRY.canonical_json_bytes(legacy),
            CARRY.canonical_json_bytes(optimized),
        )
        expected_bytes = PANEL.PANEL_SIZE * sum(
            row["canonical_json_bytes_proxy"] for row in legacy
        )
        self.assertEqual(
            expected_bytes,
            REGRESSION._professional_review_cost_case_bytes(
                index,
                fresh_skill_ids=fresh_ids,
            ),
        )

    def test_synthetic_index_matches_duplicate_overlap_and_cross_stage(self) -> None:
        synthetic = _synthetic_catalog_cost_state()
        packet = synthetic["packet"]
        bindings = synthetic["bindings"]
        index = synthetic["index"]
        requests_by_target = synthetic["requests_by_target"]

        # a->b exists only in the final stage; a+b also makes b both a target
        # and a candidate. b+c overlap through their required candidate sets.
        for fresh_ids, additions in (
            (["a"], requests_by_target),
            (["a", "b"], requests_by_target),
            (["b", "c"], None),
        ):
            with self.subTest(fresh_ids=fresh_ids):
                self._assert_exact_legacy_equivalence(
                    packet=packet,
                    bindings=bindings,
                    index=index,
                    fresh_ids=fresh_ids,
                    reviewer_added_requests_by_target=additions,
                )

        with self.assertRaises(TypeError):
            index.base_blocks_by_digest["f" * 64] = 1
        with self.assertRaises(FrozenInstanceError):
            index.assigned_skill_ids = ("a",)
        self.assertEqual(
            PANEL.PANEL_SIZE,
            REGRESSION._professional_review_cost_case_bytes(
                index,
                fresh_skill_ids=["a"],
            )
            // sum(
                row["canonical_json_bytes_proxy"]
                for row in REGRESSION._professional_review_cost_case_input_blocks(
                    index,
                    fresh_skill_ids=["a"],
                )
            ),
        )

    def test_invalid_case_selection_and_vote_multiplicity_fail_closed(self) -> None:
        index = _synthetic_catalog_cost_state()["index"]
        invalid_assignments = (
            ([], "requires unique fresh target IDs"),
            (["a", "a"], "requires unique fresh target IDs"),
            (["unknown-skill"], "names unknown fresh targets"),
        )
        for fresh_ids, message in invalid_assignments:
            with self.subTest(fresh_ids=fresh_ids):
                with self.assertRaisesRegex(ValueError, message):
                    REGRESSION._professional_review_cost_case_input_blocks(
                        index,
                        fresh_skill_ids=fresh_ids,
                    )

        for multiplicity in (False, 0, 4):
            with self.subTest(semantic_vote_multiplicity=multiplicity):
                with self.assertRaisesRegex(
                    ValueError,
                    "semantic vote multiplicity must be between one and three",
                ):
                    REGRESSION._professional_review_cost_case_bytes(
                        index,
                        fresh_skill_ids=["a"],
                        semantic_vote_multiplicity=multiplicity,
                    )

        fixture = REGRESSION._calculate_professional_review_cost_fixtures()
        self.assertEqual(
            {
                "fresh_target_count": 0,
                "carried_forward_target_count": 189,
                "input_ratio_ppm": 0,
            },
            fixture["unchanged"],
        )

    def test_current_catalog_policy_and_lock_are_current_and_fail_closed_on_drift(
        self,
    ) -> None:
        contracts = json.loads(
            REGRESSION.CORE_CONTRACTS.read_text(encoding="utf-8")
        )
        authority = contracts["final_goal_contract"][
            "professional_review_cost_fixtures"
        ]
        thresholds = authority["thresholds"]
        locked = authority["locked_current_catalog"]

        current = REGRESSION._calculate_professional_review_cost_fixtures()
        sensitivity = current[
            "routing_neutral_isolated_material_binding_sensitivity"
        ]
        self.assertEqual(1, current["schema_version"])
        self.assertEqual("pass", current["status"])
        self.assertEqual(189, sensitivity["case_count"])
        self.assertEqual(56, sensitivity["fresh_target_count"]["max"])
        self.assertEqual(348342, sensitivity["input_ratio_ppm"]["max"])
        self.assertEqual(
            {
                "maximum_fresh_target_count": 56,
                "maximum_mean_fresh_target_count": 25,
                "maximum_input_ratio_ppm": 450000,
                "maximum_mean_input_ratio_ppm": 220000,
            },
            current["thresholds"],
        )
        self.assertLessEqual(
            sensitivity["fresh_target_count"]["max"],
            thresholds["maximum_fresh_target_count"],
        )
        self.assertLessEqual(
            sensitivity["fresh_target_count"]["sum"],
            thresholds["maximum_mean_fresh_target_count"]
            * sensitivity["case_count"],
        )
        self.assertLessEqual(
            sensitivity["input_ratio_ppm"]["max"],
            thresholds["maximum_input_ratio_ppm"],
        )
        self.assertLessEqual(
            sensitivity["input_ratio_ppm"]["sum"],
            thresholds["maximum_mean_input_ratio_ppm"]
            * sensitivity["case_count"],
        )
        self.assertEqual(locked, sensitivity)

        with mock.patch.object(
            REGRESSION,
            "_calculate_professional_review_cost_fixtures",
            return_value=copy.deepcopy(current),
        ):
            projected = REGRESSION._professional_review_cost_fixtures()
        self.assertEqual("pass", projected["status"])
        self.assertEqual(
            sensitivity,
            projected[
                "routing_neutral_isolated_material_binding_sensitivity"
            ],
        )

        with mock.patch.object(
            REGRESSION,
            "_calculate_professional_review_cost_fixtures",
            return_value=copy.deepcopy(current),
        ):
            self.assertEqual(
                "pass",
                REGRESSION._professional_review_cost_fixtures()["status"],
            )

        lock_drift = copy.deepcopy(current)
        lock_drift[
            "routing_neutral_isolated_material_binding_sensitivity"
        ]["cases_fingerprint"] = "0" * 64
        with mock.patch.object(
            REGRESSION,
            "_calculate_professional_review_cost_fixtures",
            return_value=lock_drift,
        ):
            self.assertEqual(
                "formal-non-current",
                REGRESSION._professional_review_cost_fixtures()["status"],
            )

        threshold_drift = copy.deepcopy(current)
        threshold_drift["status"] = "formal-non-current"
        with mock.patch.object(
            REGRESSION,
            "_calculate_professional_review_cost_fixtures",
            return_value=threshold_drift,
        ):
            self.assertEqual(
                "formal-non-current",
                REGRESSION._professional_review_cost_fixtures()["status"],
            )

        malformed_core = mock.Mock()
        malformed_core.read_text.return_value = "{}"
        with (
            mock.patch.object(
                REGRESSION,
                "_calculate_professional_review_cost_fixtures",
                return_value=current,
            ),
            mock.patch.object(
                REGRESSION,
                "CORE_CONTRACTS",
                malformed_core,
            ),
        ):
            with self.assertRaisesRegex(
                ValueError,
                "lacks Professional review cost fixture authority",
            ):
                REGRESSION._professional_review_cost_fixtures()

    def test_current_catalog_min_named_max_and_full_match_legacy(self) -> None:
        current = _current_catalog_cost_state()
        reverse = current["reverse_dependencies"]
        minimum = min(reverse, key=lambda skill_id: (len(reverse[skill_id]), skill_id))
        maximum = max(reverse, key=lambda skill_id: (len(reverse[skill_id]), skill_id))
        cases = {
            "minimum": sorted(reverse[minimum]),
            "named": sorted(reverse["acceptance-criteria-builder"]),
            "maximum": sorted(reverse[maximum]),
            "full": current["target_ids"],
        }
        for label, fresh_ids in cases.items():
            with self.subTest(case=label, fresh_target_count=len(fresh_ids)):
                self._assert_exact_legacy_equivalence(
                    packet=current["packet"],
                    bindings=current["bindings"],
                    index=current["index"],
                    fresh_ids=fresh_ids,
                )


if __name__ == "__main__":
    unittest.main()
