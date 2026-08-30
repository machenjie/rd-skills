from __future__ import annotations

import copy
import functools
import json
import sys
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest import mock

from . import expert_panel_source_test_support as source_support
from . import professional_review_cost_test_support as cost_support


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))




REGRESSION = source_support.REGRESSION
PANEL = source_support.PANEL
CARRY = source_support.CARRY
_current_catalog_cost_state = cost_support._current_catalog_cost_state
_synthetic_catalog_cost_state = cost_support._synthetic_catalog_cost_state








class ProfessionalReviewCostFixtureTests(unittest.TestCase):
    def test_current_cost_fixture_uses_closed_schema3_authority(self) -> None:
        packet = REGRESSION._current_professional_completeness_packet()
        self.assertNotIn("source_fingerprints", packet)

        fixture = REGRESSION._calculate_professional_review_cost_fixtures()
        self.assertEqual(
            188,
            fixture["review_contract_change"]["fresh_target_count"],
        )

        legacy_shaped = copy.deepcopy(packet)
        legacy_shaped["source_fingerprints"] = {
            "professional_packages": "0" * 64,
        }
        with self.assertRaisesRegex(
            PANEL.PanelReviewError,
            "professional completeness packet fields do not match schema 3",
        ):
            PANEL._professional_v3_packet_state(
                legacy_shaped,
                validation_root=ROOT,
                artifact_path=None,
                validate_baseline=False,
            )

    def test_shared_fixture_uses_current_unittest_package(self) -> None:
        isolated_name = f"{__name__}.isolated_expert_panel_review"
        self.assertIs(PANEL, source_support.load_panel())
        self.assertIs(PANEL, sys.modules[PANEL.__name__])
        with source_support.isolated_source_module(
            "scripts/expert_panel_review.py", isolated_name
        ) as isolated:
            self.assertIsNot(PANEL, isolated)
            self.assertIs(isolated, sys.modules[isolated_name])
        self.assertNotIn(isolated_name, sys.modules)

    def _assert_exact_projection_equivalence(
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
        projected = PANEL._professional_v3_effective_input_blocks(
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
        self.assertEqual(projected, optimized)
        self.assertEqual(
            CARRY.canonical_json_bytes(projected),
            CARRY.canonical_json_bytes(optimized),
        )
        expected_bytes = PANEL.PANEL_SIZE * sum(
            row["canonical_json_bytes_proxy"] for row in projected
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
                self._assert_exact_projection_equivalence(
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
                "carried_forward_target_count": 188,
                "input_ratio_ppm": 0,
            },
            fixture["unchanged"],
        )

    def test_current_catalog_policy_uses_measured_invariants_and_ceilings(
        self,
    ) -> None:
        contracts = json.loads(
            REGRESSION.CORE_CONTRACTS.read_text(encoding="utf-8")
        )
        authority = contracts["final_goal_contract"][
            "professional_review_cost_fixtures"
        ]
        self.assertEqual({"thresholds", "formal_round_policy"}, set(authority))
        thresholds = authority["thresholds"]

        current = REGRESSION._professional_review_cost_fixtures()
        sensitivity = current[
            "routing_neutral_isolated_material_binding_sensitivity"
        ]
        self.assertEqual(1, current["schema_version"])
        self.assertEqual("pass", current["status"])
        self.assertEqual(
            {
                "case_count",
                "full_rereview_deduplicated_capsule_input_bytes_proxy",
                "fresh_target_count",
                "input_ratio_ppm",
                "named_isolated_case",
            },
            set(sensitivity),
        )
        self.assertEqual(188, sensitivity["case_count"])
        self.assertEqual(188, REGRESSION.expert_panel.PROFESSIONAL_PACKAGE_COUNT)
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
            self.assertRaisesRegex(
                ValueError,
                "lacks Professional review cost fixture authority",
            ),
        ):
            REGRESSION._professional_review_cost_fixtures()

    def test_digest_only_drift_is_not_cost_currentness(self) -> None:
        measured = REGRESSION._calculate_professional_review_cost_fixtures()
        sensitivity = measured[
            "routing_neutral_isolated_material_binding_sensitivity"
        ]
        digest_fields = {
            "professional_packages_fingerprint",
            "catalog_fingerprint",
            "material_catalog_fingerprint",
            "full_projection_fingerprint",
            "review_contract_fingerprint",
            "cases_fingerprint",
        }
        for field in digest_fields:
            if field in sensitivity:
                sensitivity[field] = "0" * 64
        with mock.patch.object(
            REGRESSION,
            "_calculate_professional_review_cost_fixtures",
            return_value=measured,
        ):
            projected = REGRESSION._professional_review_cost_fixtures()
        self.assertEqual("pass", projected["status"])
        self.assertTrue(
            digest_fields.isdisjoint(
                projected[
                    "routing_neutral_isolated_material_binding_sensitivity"
                ]
            )
        )

    def test_count_and_threshold_tamper_remain_non_current(self) -> None:
        measured = REGRESSION._calculate_professional_review_cost_fixtures()
        thresholds = json.loads(
            REGRESSION.CORE_CONTRACTS.read_text(encoding="utf-8")
        )["final_goal_contract"]["professional_review_cost_fixtures"][
            "thresholds"
        ]
        mutations = {
            "case-count": lambda sensitivity: sensitivity.update(
                {"case_count": 189}
            ),
            "fresh-max": lambda sensitivity: sensitivity[
                "fresh_target_count"
            ].update(
                {
                    "max": (
                        thresholds["maximum_fresh_target_count"] + 1
                    )
                }
            ),
            "ratio-max": lambda sensitivity: sensitivity[
                "input_ratio_ppm"
            ].update(
                {"max": thresholds["maximum_input_ratio_ppm"] + 1}
            ),
        }
        for label, mutate in mutations.items():
            candidate = copy.deepcopy(measured)
            mutate(
                candidate[
                    "routing_neutral_isolated_material_binding_sensitivity"
                ]
            )
            candidate["status"] = "pass"
            with mock.patch.object(
                REGRESSION,
                "_calculate_professional_review_cost_fixtures",
                return_value=candidate,
            ):
                with self.subTest(label=label):
                    self.assertEqual(
                        "formal-non-current",
                        REGRESSION._professional_review_cost_fixtures()[
                            "status"
                        ],
                    )

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
                self._assert_exact_projection_equivalence(
                    packet=current["packet"],
                    bindings=current["bindings"],
                    index=current["index"],
                    fresh_ids=fresh_ids,
                )


if __name__ == "__main__":
    unittest.main()
