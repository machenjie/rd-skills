from __future__ import annotations

import ast
import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import validation_utils as VALIDATION
from validation_utils import (
    REGISTRY_SCHEMA_VERSIONS,
    foundation_ownership_errors,
    foundation_registry_field_errors,
    load_yaml_file,
    professional_review_skill_ids,
)


FOUNDATION_REGISTRY = ROOT / "src" / "registry" / "foundation-skills.yaml"
PROFESSIONAL_REGISTRY = ROOT / "src" / "registry" / "professional-skills.yaml"
ACTIVATION_FIELDS = frozenset(
    {
        "contract",
        "id",
        "mode",
        "path",
        "profile",
        "primary_skill",
        "review_skill",
        "semantic_atoms",
        "matcher_evidence",
        "negative_families",
    }
)
REVIEW_SELECTOR_INPUT = {
    "registry_selector": {
        "registry": "professional-skills.yaml",
        "field": "role_support",
        "contains": "review-agent",
    }
}
COMMON_NEGATIVE_FAMILIES = (
    "lexical-near-miss",
    "explicit-anti-or-adjacent",
    "alternate-professional-owner",
)
ACTIVATION_COMBINATIONS = {
    "explicit-analyzed": {
        "path": "analyzed",
        "profile": "analysis-agent",
        "negative": "analysis-authority-invalid",
    },
    "accepted-brief-review": {
        "path": "direct",
        "profile": "review-agent",
        "negative": "artifact-authority-invalid",
    },
}


def _activation(
    foundation: dict[str, object],
    *,
    primary_skill: str,
    review_skill: str,
    mode: str = "explicit-analyzed",
) -> dict[str, object]:
    combination = ACTIVATION_COMBINATIONS[mode]
    name = str(foundation["name"])
    return {
        "contract": "foundation-activation/v1",
        "id": f"foundation-activation-{name}",
        "mode": mode,
        "path": combination["path"],
        "profile": combination["profile"],
        "primary_skill": primary_skill,
        "review_skill": review_skill,
        "semantic_atoms": [
            "current-source",
            "decision-boundary",
        ],
        "matcher_evidence": [
            "accepted-evidence",
            "owner-resolved",
        ],
        "negative_families": [
            *COMMON_NEGATIVE_FAMILIES,
            combination["negative"],
        ],
    }


def _with_activation(
    foundation: dict[str, object],
    activation: dict[str, object],
) -> dict[str, object]:
    row = copy.deepcopy(foundation)
    row["activation"] = copy.deepcopy(activation)
    return row


def _replace_foundation_rows(
    foundations: list[dict[str, object]],
    replacements: list[dict[str, object]],
) -> list[dict[str, object]]:
    by_name = {
        str(replacement["name"]): copy.deepcopy(replacement)
        for replacement in replacements
    }
    return [
        by_name.get(str(row["name"]), copy.deepcopy(row))
        for row in foundations
    ]


def _replace_professional_rows(
    professionals: list[dict[str, object]],
    replacements: list[dict[str, object]],
) -> list[dict[str, object]]:
    by_name = {
        str(replacement["name"]): copy.deepcopy(replacement)
        for replacement in replacements
    }
    return [
        by_name.get(str(row["name"]), copy.deepcopy(row))
        for row in professionals
    ]


class FoundationActivationAuthorityRedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.foundation_registry = load_yaml_file(FOUNDATION_REGISTRY)
        cls.professional_registry = load_yaml_file(PROFESSIONAL_REGISTRY)
        cls.foundations = cls.foundation_registry["foundation_skills"]
        cls.professionals = cls.professional_registry["professional_skills"]
        cls.professional_by_name = {
            row["name"]: row
            for row in cls.professionals
        }

        analysis_rows: list[tuple[str, str]] = []
        review_rows: list[tuple[str, str]] = []
        for foundation in cls.foundations:
            owners = foundation.get("used_by")
            if (
                foundation.get("delivery_scope") != "product"
                or not isinstance(owners, list)
                or len(owners) != 1
                or owners[0] not in cls.professional_by_name
            ):
                continue
            owner = cls.professional_by_name[owners[0]]
            if (
                foundation["name"] not in owner.get("layer3_candidates", [])
                or owner.get("task_routable") is not True
            ):
                continue
            if (
                "analysis-agent" in foundation.get("role_support", [])
                and "analysis-agent" in owner.get("role_support", [])
                and len(owner.get("role_support", [])) > 1
            ):
                analysis_rows.append((foundation["name"], owner["name"]))
            if (
                "review-agent" in foundation.get("role_support", [])
                and owner.get("role_support") == ["review-agent"]
            ):
                review_rows.append((foundation["name"], owner["name"]))

        analysis_rows.sort()
        review_rows.sort()
        cls.analysis_foundation = next(
            row
            for row in cls.foundations
            if row["name"] == analysis_rows[0][0]
        )
        cls.analysis_primary = analysis_rows[0][1]
        cls.review_foundation = next(
            row
            for row in cls.foundations
            if row["name"] == review_rows[0][0]
        )
        cls.review_primary = review_rows[0][1]

        review_ids = professional_review_skill_ids(
            cls.professionals,
            REVIEW_SELECTOR_INPUT,
        )
        cls.routable_review = sorted(
            name
            for name in review_ids
            if cls.professional_by_name[name].get("task_routable") is True
        )[0]
        cls.nonroutable_review = sorted(
            name
            for name in review_ids
            if cls.professional_by_name[name].get("task_routable") is False
        )[0]
        cls.nonreview_professional = sorted(
            row["name"]
            for row in cls.professionals
            if row.get("task_routable") is True
            and "review-agent" not in row.get("role_support", [])
        )[0]

    def _analysis_row(self) -> dict[str, object]:
        return _with_activation(
            self.analysis_foundation,
            _activation(
                self.analysis_foundation,
                primary_skill=self.analysis_primary,
                review_skill=self.routable_review,
            ),
        )

    def _review_row(self) -> dict[str, object]:
        return _with_activation(
            self.review_foundation,
            _activation(
                self.review_foundation,
                primary_skill=self.review_primary,
                review_skill=self.routable_review,
                mode="accepted-brief-review",
            ),
        )

    def _field_errors(
        self,
        row: dict[str, object],
    ) -> list[str]:
        return foundation_registry_field_errors(
            row,
            f"foundation-skills.yaml:{row['name']}",
        )

    def _ownership_errors(
        self,
        rows: list[dict[str, object]],
        professionals: list[dict[str, object]] | None = None,
    ) -> list[str]:
        return foundation_ownership_errors(
            rows,
            (
                self.professionals
                if professionals is None
                else professionals
            ),
        )

    def _complete_errors(
        self,
        row: dict[str, object],
        *,
        professionals: list[dict[str, object]] | None = None,
    ) -> list[str]:
        rows = _replace_foundation_rows(self.foundations, [row])
        return [
            *self._field_errors(row),
            *self._ownership_errors(rows, professionals),
        ]

    def _assert_contract_marker(
        self,
        errors: list[str],
        marker: str,
        label: str,
    ) -> None:
        folded = " ".join(errors).casefold()
        self.assertIn(
            marker.casefold(),
            folded,
            f"[foundation-activation-{label}] expected marker={marker!r}; "
            f"actual={errors}",
        )

    def test_schema_v8_accepts_one_complete_source_derived_activation(
        self,
    ) -> None:
        row = self._analysis_row()
        with self.subTest(contract="foundation-schema-v8"):
            self.assertEqual(
                8,
                REGISTRY_SCHEMA_VERSIONS["foundation"],
                "[foundation-activation-schema-v8] validation authority must "
                "recognize Foundation schema v8",
            )
            self.assertEqual(8, self.foundation_registry["schema_version"])
        with self.subTest(contract="complete-synthetic-activation"):
            self.assertEqual(
                ACTIVATION_FIELDS,
                set(row["activation"]),
            )
            self.assertEqual(
                [],
                self._complete_errors(row),
                "[foundation-activation-complete] a complete source-derived "
                "activation must pass the registry validation surfaces",
            )
            target = str(row["name"])
            self.assertEqual(1, str(row["activation"]).count(target))

    def test_activation_fields_are_closed_missing_and_unknown(self) -> None:
        base = self._analysis_row()
        for field in sorted(ACTIVATION_FIELDS):
            with self.subTest(missing=field):
                row = copy.deepcopy(base)
                del row["activation"][field]
                self._assert_contract_marker(
                    self._field_errors(row),
                    f"activation.{field}",
                    f"missing-field-{field}",
                )
        with self.subTest(unknown="extra"):
            row = copy.deepcopy(base)
            row["activation"]["extra"] = "forbidden"
            self._assert_contract_marker(
                self._field_errors(row),
                "activation.extra",
                "unknown-field-extra",
            )
        with self.subTest(unknown="mixed-key-types"):
            row = copy.deepcopy(base)
            row["activation"]["extra"] = "forbidden"
            row["activation"][7] = "forbidden"
            errors = self._field_errors(row)
            self.assertEqual(
                1,
                sum("activation.extra" in error for error in errors),
                errors,
            )
            self.assertEqual(
                1,
                sum("activation[7]" in error for error in errors),
                errors,
            )

    def test_contract_and_activation_id_are_exact_grammatical_and_row_bound(
        self,
    ) -> None:
        base = self._analysis_row()
        mutations = {
            "contract": ("contract", "foundation-activation/v2"),
            "id-prefix": ("id", f"activation-{base['name']}"),
            "id-uppercase": ("id", "foundation-activation-Uppercase"),
            "id-underscore": ("id", "foundation-activation-bad_value"),
            "id-row-mismatch": (
                "id",
                f"foundation-activation-{self.review_foundation['name']}",
            ),
        }
        for label, (field, value) in mutations.items():
            with self.subTest(case=label):
                row = copy.deepcopy(base)
                row["activation"][field] = value
                self._assert_contract_marker(
                    self._field_errors(row),
                    f"activation.{field}",
                    f"identity-{label}",
                )

    def test_mode_path_profile_matrix_is_closed(self) -> None:
        analysis = self._analysis_row()
        review = self._review_row()
        mutations = (
            ("unknown-mode", analysis, "mode", "automatic"),
            ("analysis-path", analysis, "path", "direct"),
            ("analysis-profile", analysis, "profile", "review-agent"),
            ("review-path", review, "path", "analyzed"),
            ("review-profile", review, "profile", "analysis-agent"),
        )
        for label, base, field, value in mutations:
            with self.subTest(case=label):
                row = copy.deepcopy(base)
                row["activation"][field] = value
                self._assert_contract_marker(
                    self._field_errors(row),
                    f"activation.{field}",
                    f"mode-matrix-{label}",
                )

    def test_primary_owner_is_unique_reciprocal_routable_and_profile_capable(
        self,
    ) -> None:
        base = self._analysis_row()
        primary = copy.deepcopy(
            self.professional_by_name[self.analysis_primary]
        )
        profile = str(base["activation"]["profile"])

        with self.subTest(case="unknown"):
            row = copy.deepcopy(base)
            row["activation"]["primary_skill"] = (
                "unknown-professional-owner"
            )
            self.assertEqual(base["used_by"], row["used_by"])
            self._assert_contract_marker(
                self._complete_errors(row),
                "activation.primary_skill",
                "primary-unknown",
            )

        with self.subTest(case="nonreciprocal"):
            row = copy.deepcopy(base)
            row["used_by"] = []
            professionals = copy.deepcopy(self.professionals)
            copied_primary = next(
                item
                for item in professionals
                if item["name"] == self.analysis_primary
            )
            self.assertEqual(
                {
                    key: value
                    for key, value in base.items()
                    if key != "used_by"
                },
                {
                    key: value
                    for key, value in row.items()
                    if key != "used_by"
                },
            )
            self.assertNotIn(self.analysis_primary, row["used_by"])
            self.assertIn(
                row["name"],
                copied_primary["layer3_candidates"],
            )
            self.assertIs(copied_primary["task_routable"], True)
            self.assertIn(profile, copied_primary["role_support"])
            rows = _replace_foundation_rows(self.foundations, [row])
            self.assertEqual(len(self.foundations), len(rows))
            self._assert_contract_marker(
                self._ownership_errors(rows, professionals),
                "activation.primary_skill",
                "primary-nonreciprocal",
            )

        with self.subTest(case="not-routable"):
            invalid_primary = copy.deepcopy(primary)
            invalid_primary["task_routable"] = False
            professionals = _replace_professional_rows(
                self.professionals,
                [invalid_primary],
            )
            self.assertEqual(
                {
                    key: value
                    for key, value in primary.items()
                    if key != "task_routable"
                },
                {
                    key: value
                    for key, value in invalid_primary.items()
                    if key != "task_routable"
                },
            )
            self.assertEqual(
                [self.analysis_primary],
                base["used_by"],
            )
            self.assertIn(
                base["name"],
                invalid_primary["layer3_candidates"],
            )
            self.assertIn(profile, invalid_primary["role_support"])
            self._assert_contract_marker(
                self._complete_errors(base, professionals=professionals),
                "activation.primary_skill",
                "primary-not-routable",
            )

        with self.subTest(case="primary-wrong-profile"):
            invalid_primary = copy.deepcopy(primary)
            invalid_primary["role_support"] = [
                role
                for role in invalid_primary["role_support"]
                if role != profile
            ]
            professionals = _replace_professional_rows(
                self.professionals,
                [invalid_primary],
            )
            self.assertEqual(
                {
                    key: value
                    for key, value in primary.items()
                    if key != "role_support"
                },
                {
                    key: value
                    for key, value in invalid_primary.items()
                    if key != "role_support"
                },
            )
            self.assertIs(invalid_primary["task_routable"], True)
            self.assertIn(
                base["name"],
                invalid_primary["layer3_candidates"],
            )
            self.assertIn(self.analysis_primary, base["used_by"])
            self.assertNotIn(profile, invalid_primary["role_support"])
            self.assertTrue(invalid_primary["role_support"])
            self._assert_contract_marker(
                self._complete_errors(base, professionals=professionals),
                "activation.primary_skill",
                "primary-wrong-profile",
            )

        with self.subTest(case="foundation-wrong-profile"):
            row = copy.deepcopy(base)
            row["role_support"] = [
                role
                for role in row["role_support"]
                if role != profile
            ]
            self.assertEqual(
                {
                    key: value
                    for key, value in base.items()
                    if key != "role_support"
                },
                {
                    key: value
                    for key, value in row.items()
                    if key != "role_support"
                },
            )
            self.assertNotIn(profile, row["role_support"])
            self.assertTrue(row["role_support"])
            self.assertIn(self.analysis_primary, row["used_by"])
            self.assertIn(
                row["name"],
                primary["layer3_candidates"],
            )
            self.assertIs(primary["task_routable"], True)
            self.assertIn(profile, primary["role_support"])
            rows = _replace_foundation_rows(self.foundations, [row])
            self.assertEqual(len(self.foundations), len(rows))
            self._assert_contract_marker(
                [
                    *self._field_errors(row),
                    *self._ownership_errors(rows),
                ],
                "activation.primary_skill",
                "foundation-wrong-profile",
            )

        duplicate = copy.deepcopy(self.professional_by_name[self.analysis_primary])
        professionals = [*copy.deepcopy(self.professionals), duplicate]
        self._assert_contract_marker(
            self._complete_errors(base, professionals=professionals),
            "activation.primary_skill",
            "primary-duplicate",
        )

    def test_review_is_unique_routable_review_capable_and_not_an_owner(
        self,
    ) -> None:
        base = self._analysis_row()
        self.assertNotIn(
            self.routable_review,
            base["used_by"],
            "the valid review selection must demonstrate that review_skill "
            "does not need Foundation ownership",
        )
        with self.subTest(case="valid-not-used-by"):
            self.assertEqual(
                [],
                self._complete_errors(base),
                "[foundation-activation-review-not-owner] review_skill may be "
                "outside Foundation.used_by",
            )

        with self.subTest(case="unknown"):
            row = copy.deepcopy(base)
            row["activation"]["review_skill"] = "unknown-review-skill"
            self.assertEqual(base["used_by"], row["used_by"])
            self._assert_contract_marker(
                self._complete_errors(row),
                "activation.review_skill",
                "review-unknown",
            )

        with self.subTest(case="not-review-capable"):
            invalid_review = self.professional_by_name[
                self.nonreview_professional
            ]
            self.assertIs(invalid_review["task_routable"], True)
            self.assertNotIn(
                "review-agent",
                invalid_review["role_support"],
            )
            row = copy.deepcopy(base)
            row["activation"]["review_skill"] = (
                self.nonreview_professional
            )
            self.assertEqual(base["used_by"], row["used_by"])
            self._assert_contract_marker(
                self._complete_errors(row),
                "activation.review_skill",
                "review-not-review-capable",
            )

        duplicate = copy.deepcopy(self.professional_by_name[self.routable_review])
        professionals = [*copy.deepcopy(self.professionals), duplicate]
        self._assert_contract_marker(
            self._complete_errors(base, professionals=professionals),
            "activation.review_skill",
            "review-duplicate",
        )

    def test_accepted_brief_review_allows_review_only_routable_primary(
        self,
    ) -> None:
        row = self._review_row()
        primary = self.professional_by_name[self.review_primary]
        self.assertEqual(["review-agent"], primary["role_support"])
        self.assertIs(primary["task_routable"], True)
        self.assertEqual(
            [],
            self._complete_errors(row),
            "[foundation-activation-accepted-brief-review] a reciprocal "
            "review-only task-routable primary is valid",
        )

    def test_negative_families_are_exact_unique_and_mode_specific(self) -> None:
        for label, base in (
            ("analysis", self._analysis_row()),
            ("review", self._review_row()),
        ):
            with self.subTest(case=f"{label}-order-insensitive"):
                row = copy.deepcopy(base)
                row["activation"]["negative_families"] = list(
                    reversed(row["activation"]["negative_families"])
                )
                self.assertEqual([], self._complete_errors(row))

        analysis = self._analysis_row()
        review = self._review_row()
        mutations = {
            "duplicate": (
                analysis,
                [
                    *analysis["activation"]["negative_families"],
                    "lexical-near-miss",
                ],
            ),
            "missing": (
                analysis,
                analysis["activation"]["negative_families"][:-1],
            ),
            "unknown": (
                analysis,
                [
                    *COMMON_NEGATIVE_FAMILIES,
                    "unknown-negative-family",
                ],
            ),
            "analysis-wrong-n4": (
                analysis,
                [
                    *COMMON_NEGATIVE_FAMILIES,
                    "artifact-authority-invalid",
                ],
            ),
            "review-wrong-n4": (
                review,
                [
                    *COMMON_NEGATIVE_FAMILIES,
                    "analysis-authority-invalid",
                ],
            ),
        }
        for label, (base, families) in mutations.items():
            with self.subTest(case=label):
                row = copy.deepcopy(base)
                row["activation"]["negative_families"] = families
                self._assert_contract_marker(
                    self._field_errors(row),
                    "activation.negative_families",
                    f"negative-{label}",
                )

    def test_atoms_and_matcher_evidence_are_distinct_closed_atom_sets(
        self,
    ) -> None:
        base = self._analysis_row()
        for field in ("semantic_atoms", "matcher_evidence"):
            with self.subTest(case=f"{field}-order-insensitive"):
                row = copy.deepcopy(base)
                row["activation"][field] = list(
                    reversed(row["activation"][field])
                )
                self.assertEqual([], self._complete_errors(row))

        target = str(base["name"])
        mutations = {
            "semantic-empty": ("semantic_atoms", []),
            "matcher-empty": ("matcher_evidence", []),
            "semantic-duplicate": (
                "semantic_atoms",
                ["current-source", "current-source"],
            ),
            "matcher-duplicate": (
                "matcher_evidence",
                ["accepted-evidence", "accepted-evidence"],
            ),
            "uppercase": ("semantic_atoms", ["Current-source"]),
            "underscore": ("semantic_atoms", ["current_source"]),
            "slash": ("matcher_evidence", ["accepted/evidence"]),
            "whitespace": ("matcher_evidence", ["accepted evidence"]),
            "semantic-target": ("semantic_atoms", [target]),
            "matcher-target": ("matcher_evidence", [target]),
            "contiguous-target": (
                "semantic_atoms",
                [f"prefix-{target}-suffix"],
            ),
        }
        for label, (field, value) in mutations.items():
            with self.subTest(case=label):
                row = copy.deepcopy(base)
                row["activation"][field] = value
                self._assert_contract_marker(
                    self._field_errors(row),
                    f"activation.{field}",
                    f"atom-{label}",
                )

        with self.subTest(case="semantic-matcher-intersection"):
            row = copy.deepcopy(base)
            row["activation"]["matcher_evidence"][0] = row["activation"][
                "semantic_atoms"
            ][0]
            self._assert_contract_marker(
                self._field_errors(row),
                "activation.matcher_evidence",
                "atom-intersection",
            )

    def test_activation_absence_remains_valid_and_unclassified(self) -> None:
        professionals_by_name: dict[str, list[dict[str, object]]] = {}
        for professional in self.professionals:
            professionals_by_name.setdefault(
                str(professional["name"]),
                [],
            ).append(professional)

        candidates: list[
            tuple[dict[str, object], dict[str, object]]
        ] = []
        for foundation in self.foundations:
            owners = foundation.get("used_by")
            if (
                "activation" in foundation
                or foundation.get("delivery_scope") != "product"
                or not isinstance(owners, list)
                or len(owners) != 1
            ):
                continue
            owner_matches = professionals_by_name.get(
                str(owners[0]),
                [],
            )
            if len(owner_matches) != 1:
                continue
            owner = owner_matches[0]
            foundation_roles = {
                role
                for role in foundation.get("role_support", [])
                if isinstance(role, str)
            }
            owner_roles = {
                role
                for role in owner.get("role_support", [])
                if isinstance(role, str)
            }
            if (
                foundation["name"] not in owner.get(
                    "layer3_candidates",
                    [],
                )
                or owner.get("task_routable") is not True
                or not foundation_roles & owner_roles
            ):
                continue
            candidates.append((foundation, owner))

        self.assertTrue(candidates)
        selected, owner = sorted(
            candidates,
            key=lambda candidate: str(candidate[0]["name"]),
        )[0]
        owners = selected["used_by"]
        self.assertNotIn("activation", selected)
        self.assertEqual("product", selected["delivery_scope"])
        self.assertIsInstance(owners, list)
        self.assertEqual(1, len(owners))
        self.assertEqual(
            1,
            len(professionals_by_name[str(owners[0])]),
        )
        self.assertIn(
            selected["name"],
            owner["layer3_candidates"],
        )
        self.assertIs(owner["task_routable"], True)
        self.assertTrue(
            set(selected["role_support"]) & set(owner["role_support"])
        )

        row = copy.deepcopy(selected)
        self.assertIsNone(row.get("activation"))
        self.assertEqual([], self._field_errors(row))
        replaced = _replace_foundation_rows(self.foundations, [row])
        self.assertEqual(len(self.foundations), len(replaced))
        self.assertEqual(
            1,
            sum(item["name"] == row["name"] for item in replaced),
        )
        self.assertEqual([], self._ownership_errors(replaced))

    def test_synthetic_row_replaces_copied_owner_row_without_duplication(
        self,
    ) -> None:
        row = self._analysis_row()
        replaced = _replace_foundation_rows(self.foundations, [row])
        self.assertEqual(len(self.foundations), len(replaced))
        self.assertEqual(
            1,
            sum(item["name"] == row["name"] for item in replaced),
        )
        replaced_row = next(
            item
            for item in replaced
            if item["name"] == row["name"]
        )
        self.assertEqual(row["used_by"], replaced_row["used_by"])
        self.assertEqual([], self._ownership_errors(replaced))

    def test_test_module_uses_only_static_registry_validation_surfaces(
        self,
    ) -> None:
        path = Path(__file__)
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        validation_imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module == "validation_utils"
            for alias in node.names
        }
        self.assertEqual(
            {
                "REGISTRY_SCHEMA_VERSIONS",
                "foundation_ownership_errors",
                "foundation_registry_field_errors",
                "load_yaml_file",
                "professional_review_skill_ids",
            },
            validation_imports,
        )
        forbidden_surfaces = (
            "deterministic_route_" + "oracle",
            "_admission_case_" + "contract",
            "runtime_state_" + "engine",
        )
        for surface in forbidden_surfaces:
            with self.subTest(surface=surface):
                self.assertNotIn(surface, source)
        literal_exact_target_tables = [
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.List, ast.Tuple))
            and len(node.elts) == 11 + 11
        ]
        self.assertEqual([], literal_exact_target_tables)

    def test_source_derived_nonroutable_review_is_rejected(self) -> None:
        review_ids = professional_review_skill_ids(
            self.professionals,
            REVIEW_SELECTOR_INPUT,
        )
        self.assertIn(self.nonroutable_review, review_ids)
        self.assertIs(
            self.professional_by_name[self.nonroutable_review][
                "task_routable"
            ],
            False,
        )
        self.assertIn(
            "review-agent",
            self.professional_by_name[self.nonroutable_review][
                "role_support"
            ],
        )
        row = self._analysis_row()
        row["activation"]["review_skill"] = self.nonroutable_review
        self._assert_contract_marker(
            self._complete_errors(row),
            "activation.review_skill",
            "review-not-routable",
        )

    def test_runtime_matcher_reports_all_indexed_nested_field_errors(
        self,
    ) -> None:
        violations: list[str] = []
        authority = getattr(
            VALIDATION,
            "foundation_runtime_matcher_authority",
            None,
        )
        target = next(
            row
            for row in self.foundations
            if row["name"] == "test-strategy"
        )
        runtime_matcher = target["activation"].get("runtime_matcher")
        if not callable(authority):
            violations.append(
                "foundation_runtime_matcher_authority is missing or not callable"
            )
        if not isinstance(runtime_matcher, dict):
            violations.append(
                "canonical test-strategy runtime_matcher is missing"
            )

        if callable(authority) and isinstance(runtime_matcher, dict):
            malformed = copy.deepcopy(self.foundation_registry)
            malformed_target = next(
                row
                for row in malformed["foundation_skills"]
                if row["name"] == "test-strategy"
            )
            malformed_matcher = malformed_target["activation"][
                "runtime_matcher"
            ]
            malformed_matcher["contract"] = (
                "foundation-semantic-matcher/v2"
            )
            malformed_matcher["predicates"][0]["polarity"] = "optional"
            malformed_matcher["predicates"][0]["term_groups"][0][0] = (
                " Several "
            )

            with self.assertRaises(
                VALIDATION.ValidationProblem
            ) as captured:
                authority(malformed)
            diagnostic = str(captured.exception)
            required_paths = (
                "activation.runtime_matcher.contract",
                "activation.runtime_matcher.predicates[0].polarity",
                (
                    "activation.runtime_matcher.predicates[0]."
                    "term_groups[0][0]"
                ),
            )
            missing_paths = [
                path
                for path in required_paths
                if path not in diagnostic
            ]
            if missing_paths:
                violations.append(
                    "aggregate ValidationProblem omitted indexed paths "
                    f"{missing_paths!r}; found {diagnostic!r}"
                )

            for field, value in (
                ("polarity", []),
                ("action", {}),
            ):
                unhashable = copy.deepcopy(self.foundation_registry)
                unhashable_target = next(
                    row
                    for row in unhashable["foundation_skills"]
                    if row["name"] == "test-strategy"
                )
                unhashable_target["activation"]["runtime_matcher"][
                    "predicates"
                ][0][field] = value
                required_path = (
                    "activation.runtime_matcher.predicates[0]."
                    f"{field}"
                )
                try:
                    authority(unhashable)
                except VALIDATION.ValidationProblem as exc:
                    diagnostic = str(exc)
                    if required_path not in diagnostic:
                        violations.append(
                            f"unhashable {field} omitted indexed path "
                            f"{required_path!r}; found {diagnostic!r}"
                        )
                except Exception as exc:
                    violations.append(
                        f"unhashable {field} expected ValidationProblem, "
                        f"found {type(exc).__name__}: {exc}"
                    )
                else:
                    violations.append(
                        f"unhashable {field} was accepted"
                    )

        self.assertEqual([], violations)

    def test_runtime_matcher_mapping_order_fails_closed_for_both_levels(
        self,
    ) -> None:
        violations: list[str] = []
        authority = getattr(
            VALIDATION,
            "foundation_runtime_matcher_authority",
            None,
        )
        target = next(
            row
            for row in self.foundations
            if row["name"] == "test-strategy"
        )
        runtime_matcher = target["activation"].get("runtime_matcher")
        if not callable(authority):
            violations.append(
                "foundation_runtime_matcher_authority is missing or not callable"
            )
        if not isinstance(runtime_matcher, dict):
            violations.append(
                "canonical test-strategy runtime_matcher is missing"
            )

        if callable(authority) and isinstance(runtime_matcher, dict):
            top_level = copy.deepcopy(self.foundation_registry)
            top_target = next(
                row
                for row in top_level["foundation_skills"]
                if row["name"] == "test-strategy"
            )
            original_top = top_target["activation"]["runtime_matcher"]
            reordered_top = {
                key: original_top[key]
                for key in reversed(tuple(original_top))
            }
            if (
                reordered_top != original_top
                or tuple(reordered_top) == tuple(original_top)
            ):
                violations.append(
                    "top runtime_matcher fixture changed values or kept order"
                )
            top_target["activation"]["runtime_matcher"] = reordered_top

            predicate_level = copy.deepcopy(self.foundation_registry)
            predicate_target = next(
                row
                for row in predicate_level["foundation_skills"]
                if row["name"] == "test-strategy"
            )
            predicate = predicate_target["activation"]["runtime_matcher"][
                "predicates"
            ][0]
            reordered_predicate = {
                key: predicate[key]
                for key in reversed(tuple(predicate))
            }
            if (
                reordered_predicate != predicate
                or tuple(reordered_predicate) == tuple(predicate)
            ):
                violations.append(
                    "predicate fixture changed values or kept order"
                )
            predicate_target["activation"]["runtime_matcher"][
                "predicates"
            ][0] = reordered_predicate

            order_cases = (
                (
                    "top-runtime-matcher-order",
                    top_level,
                    "activation.runtime_matcher",
                ),
                (
                    "predicate-order",
                    predicate_level,
                    "activation.runtime_matcher.predicates[0]",
                ),
            )
            for label, data, required_path in order_cases:
                try:
                    authority(data)
                except VALIDATION.ValidationProblem as exc:
                    diagnostic = str(exc)
                    missing_fragments = [
                        fragment
                        for fragment in (required_path, "order")
                        if fragment not in diagnostic
                    ]
                    if missing_fragments:
                        violations.append(
                            f"{label}: missing diagnostic fragments "
                            f"{missing_fragments!r}; found {diagnostic!r}"
                        )
                except Exception as exc:
                    violations.append(
                        f"{label}: expected ValidationProblem, found "
                        f"{type(exc).__name__}: {exc}"
                    )
                else:
                    violations.append(
                        f"{label}: pure key reorder was accepted"
                    )

        self.assertEqual([], violations)


if __name__ == "__main__":
    unittest.main()
