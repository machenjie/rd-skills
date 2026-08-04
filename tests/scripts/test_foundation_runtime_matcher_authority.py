from __future__ import annotations

import ast
import copy
import inspect
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build as BUILD  # noqa: E402
import validation_utils as VALIDATION  # noqa: E402


FOUNDATION_REGISTRY = ROOT / "src" / "registry" / "foundation-skills.yaml"
TASK_ID = "T4B-ACT-V3-RUNTIME-MATCHER-AUTHORITY-RED-01"
TARGET_NAME = "test-strategy"
AUTHORITY_NAME = "foundation_runtime_matcher_authority"
AUTHORITY_CONTEXT = "foundation-skills.yaml"
_OMITTED = object()

ACTIVATION_FIELDS = (
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
)
MATCHER_FIELDS = (
    "contract",
    "rollout",
    "action",
    "combine",
    "predicates",
)
PREDICATE_FIELDS = (
    "atom",
    "operator",
    "scope",
    "polarity",
    "action",
    "term_groups",
)
PROJECTION_FIELDS = (
    "name",
    "activation_id",
    "path",
    "profile",
    "primary_skill",
    "review_skill",
    "semantic_atoms",
    "matcher_evidence",
    "runtime_matcher",
)
REPAIR177_TARGETS = (
    "business-rule-extraction",
    "state-machine-modeling",
)
REPAIR177_ACTIVATION_IDS = (
    "foundation-activation-business-rule-extraction",
    "foundation-activation-state-machine-modeling",
)
REPAIR177_MATCHER_FIELDS = (
    "contract",
    "rollout",
    "action",
    "combine",
    "relations",
)
REPAIR177_RELATION_FIELDS = (
    "atom",
    "operator",
    "scope",
    "actions",
    "objects",
    "owner_relation",
    "non_owner_modifiers",
)
REPAIR177_OWNER_RELATION_FIELDS = ("mode", "qualifiers")
REPAIR177_BUSINESS_OBJECTS = [
    "business invariant",
    "business invariants",
    "domain invariant",
    "domain invariants",
    "business policy",
    "business policies",
    "domain policy",
    "domain policies",
    "business calculation",
    "business calculations",
    "domain calculation",
    "domain calculations",
    "business constraint",
    "business constraints",
    "domain constraint",
    "domain constraints",
    "business rule",
    "business rules",
    "domain rule",
    "domain rules",
    "business decision authority",
    "domain decision authority",
]
REPAIR177_STATE_OBJECTS = [
    "state machine",
    "state machines",
    "lifecycle state",
    "lifecycle states",
    "lifecycle transition",
    "lifecycle transitions",
    "allowed transition",
    "allowed transitions",
    "allowed lifecycle transition",
    "allowed lifecycle transitions",
    "forbidden transition",
    "forbidden transitions",
    "forbidden lifecycle transition",
    "forbidden lifecycle transitions",
    "state guard",
    "state guards",
    "transition guard",
    "transition guards",
    "terminal state",
    "terminal states",
]
REPAIR177_RELATION_EXPECTATIONS = {
    "business-rule-extraction": {
        "atom": "business-rule-occurrence",
        "actions": ["analyze", "analyse", "extract"],
        "objects": REPAIR177_BUSINESS_OBJECTS,
        "owner_relation": {
            "mode": "intrinsic-qualified-object",
            "qualifiers": ["business", "domain"],
        },
        "non_owner_modifiers": [
            "accepted",
            "current",
            "existing",
            "material",
        ],
    },
    "state-machine-modeling": {
        "atom": "state-machine-occurrence",
        "actions": ["analyze", "analyse", "model"],
        "objects": REPAIR177_STATE_OBJECTS,
        "owner_relation": {
            "mode": "immediate-qualified-subject",
            "qualifiers": ["business", "domain"],
        },
        "non_owner_modifiers": [
            "accepted",
            "current",
            "existing",
            "material",
            "proposed",
            "target",
        ],
    },
}

CANONICAL_RUNTIME_MATCHER = {
    "contract": "foundation-semantic-matcher/v1",
    "rollout": "enabled",
    "action": "analysis-only",
    "combine": "all",
    "predicates": [
        {
            "atom": "multiple-material-failure-mechanisms",
            "operator": "all-term-groups",
            "scope": "bounded-clause",
            "polarity": "present",
            "action": "none",
            "term_groups": [
                ["several", "multiple"],
                ["material"],
                ["failure", "failures"],
                ["mechanism", "mechanisms"],
            ],
        },
        {
            "atom": "test-level-oracle-omission-selection",
            "operator": "all-term-groups",
            "scope": "bounded-clause",
            "polarity": "present",
            "action": "selection",
            "term_groups": [
                ["test level", "test levels"],
                ["observable failure oracle", "observable failure oracles"],
                ["omission", "omissions"],
            ],
        },
        {
            "atom": "single-fixed-command-absent",
            "operator": "all-term-groups",
            "scope": "bounded-clause",
            "polarity": "absent",
            "action": "none",
            "term_groups": [
                ["single command"],
            ],
        },
    ],
}


class FoundationRuntimeMatcherAuthorityRedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.canonical_data = VALIDATION.load_yaml_file(FOUNDATION_REGISTRY)
        cls.foundation_rows = cls.canonical_data["foundation_skills"]
        cls.target_row = next(
            row
            for row in cls.foundation_rows
            if row["name"] == TARGET_NAME
        )
        cls.target_activation = cls.target_row["activation"]
        cls.activation_rows = [
            row
            for row in cls.foundation_rows
            if isinstance(row.get("activation"), dict)
        ]

    def _v8_data(
        self,
        target_metadata: object = _OMITTED,
    ) -> dict[str, Any]:
        data = copy.deepcopy(self.canonical_data)
        data["schema_version"] = 8
        for row in data["foundation_skills"]:
            activation = row.get("activation")
            if isinstance(activation, dict):
                activation.pop("runtime_matcher", None)
        if target_metadata is not _OMITTED:
            target = next(
                row
                for row in data["foundation_skills"]
                if row["name"] == TARGET_NAME
            )
            target["activation"]["runtime_matcher"] = copy.deepcopy(
                target_metadata
            )
        return data

    def _invoke_authority(
        self,
        data: object,
    ) -> tuple[object, str | None]:
        authority = getattr(VALIDATION, AUTHORITY_NAME, None)
        if not callable(authority):
            return None, f"{AUTHORITY_NAME} is missing or not callable"
        try:
            return authority(data), None
        except Exception as exc:
            return None, f"{type(exc).__name__}: {exc}"

    @staticmethod
    def _expected_projection(row: dict[str, Any]) -> dict[str, Any]:
        activation = row["activation"]
        return {
            "name": row["name"],
            "activation_id": activation["id"],
            "path": activation["path"],
            "profile": activation["profile"],
            "primary_skill": activation["primary_skill"],
            "review_skill": activation["review_skill"],
            "semantic_atoms": copy.deepcopy(activation["semantic_atoms"]),
            "matcher_evidence": copy.deepcopy(activation["matcher_evidence"]),
            "runtime_matcher": copy.deepcopy(activation["runtime_matcher"]),
        }

    def test_schema_v8_closed11_runtime_matcher_is_optional(self) -> None:
        violations: list[str] = []
        existing_fields = set(self.target_activation) - {"runtime_matcher"}
        if existing_fields != set(ACTIVATION_FIELDS):
            violations.append(
                "the ten existing activation fields changed: "
                f"{sorted(existing_fields)!r}"
            )

        authority = getattr(VALIDATION, AUTHORITY_NAME, None)
        if not callable(authority):
            violations.append(f"{AUTHORITY_NAME} is missing or not callable")
        else:
            absent_data = self._v8_data()
            absent_projection, absent_error = self._invoke_authority(absent_data)
            if absent_error is not None:
                violations.append(
                    f"schema-v8 row without runtime_matcher failed: {absent_error}"
                )
            elif absent_projection != []:
                violations.append(
                    "schema-v8 rows without runtime_matcher must be deferred: "
                    f"{absent_projection!r}"
                )

            schema_v7_data = copy.deepcopy(absent_data)
            schema_v7_data["schema_version"] = 7
            _value, diagnostic = self._invoke_authority(schema_v7_data)
            if diagnostic is None or "schema_version" not in diagnostic:
                violations.append(
                    "schema-v7 authority input did not fail with a "
                    "schema_version diagnostic"
                )

            for field in ACTIVATION_FIELDS:
                malformed = copy.deepcopy(absent_data)
                target = next(
                    row
                    for row in malformed["foundation_skills"]
                    if row["name"] == TARGET_NAME
                )
                del target["activation"][field]
                _value, diagnostic = self._invoke_authority(malformed)
                required_path = f"activation.{field}"
                if (
                    diagnostic is None
                    or required_path not in diagnostic
                    or "required" not in diagnostic
                ):
                    violations.append(
                        f"missing {field!r} lacked required field diagnostic: "
                        f"{diagnostic!r}"
                    )

            unknown = copy.deepcopy(absent_data)
            target = next(
                row
                for row in unknown["foundation_skills"]
                if row["name"] == TARGET_NAME
            )
            target["activation"]["unexpected"] = "forbidden"
            _value, diagnostic = self._invoke_authority(unknown)
            if (
                diagnostic is None
                or "activation.unexpected" not in diagnostic
                or "unknown" not in diagnostic
            ):
                violations.append(
                    "unknown eleventh-plus activation field did not fail "
                    f"closed: {diagnostic!r}"
                )

        self.assertEqual([], violations)

    def test_canonical_authority_has_three_enabled_rows_and_twenty_one_deferred(
        self,
    ) -> None:
        violations: list[str] = []
        authority = getattr(VALIDATION, AUTHORITY_NAME, None)
        if not callable(authority):
            violations.append(f"{AUTHORITY_NAME} is missing or not callable")
        else:
            signature = inspect.signature(authority)
            parameters = list(signature.parameters.values())
            if (
                [parameter.name for parameter in parameters]
                != ["data", "context"]
                or len(parameters) != 2
                or parameters[1].default != AUTHORITY_CONTEXT
            ):
                violations.append(f"public API signature is not exact: {signature}")

            if self.canonical_data.get("schema_version") != 8:
                violations.append(
                    "canonical Foundation registry schema_version is not 8"
                )
            enabled_rows = [
                row
                for row in self.activation_rows
                if isinstance(
                    row["activation"].get("runtime_matcher"),
                    dict,
                )
                and row["activation"]["runtime_matcher"].get("rollout")
                == "enabled"
            ]
            if [row["name"] for row in enabled_rows] != [
                *REPAIR177_TARGETS,
                TARGET_NAME,
            ]:
                violations.append(
                    "canonical enabled activation rows are not the accepted "
                    "three registry-owned matchers: "
                    f"{[row['name'] for row in enabled_rows]!r}"
                )
            if len(self.activation_rows) != 24:
                violations.append(
                    f"expected 24 activation rows, found {len(self.activation_rows)}"
                )

            projection, diagnostic = self._invoke_authority(
                self.canonical_data
            )
            expected_projection = [
                self._expected_projection(row)
                for row in self.canonical_data["foundation_skills"]
                if isinstance(row.get("activation"), dict)
                and "runtime_matcher" in row["activation"]
            ]
            if diagnostic is not None:
                violations.append(f"canonical authority failed: {diagnostic}")
            elif projection != expected_projection:
                violations.append(
                    "canonical nine-field authority projection mismatch: "
                    f"{projection!r}"
                )
            elif (
                len(projection) != 3
                or any(
                    set(row) != set(PROJECTION_FIELDS)
                    for row in projection
                )
                or len(self.activation_rows) - len(projection) != 21
            ):
                violations.append(
                    "canonical projection did not prove exactly three enabled "
                    "and twenty-one deferred rows"
                )

            second_data = copy.deepcopy(self.canonical_data)
            second_row = next(
                row
                for row in second_data["foundation_skills"]
                if isinstance(row.get("activation"), dict)
                and row["name"] != TARGET_NAME
                and row["activation"]["mode"] == "explicit-analyzed"
                and "runtime_matcher" not in row["activation"]
            )
            second_runtime_metadata = {
                "contract": "foundation-semantic-matcher/v1",
                "rollout": "enabled",
                "action": "analysis-only",
                "combine": "all",
                "predicates": [
                    {
                        "atom": atom,
                        "operator": "all-term-groups",
                        "scope": "bounded-clause",
                        "polarity": "present",
                        "action": "none",
                        "term_groups": [
                            [f"synthetic term {index}"],
                        ],
                    }
                    for index, atom in enumerate(
                        second_row["activation"]["semantic_atoms"],
                        start=1,
                    )
                ],
            }
            second_row["activation"]["runtime_matcher"] = (
                second_runtime_metadata
            )
            second_projection, diagnostic = self._invoke_authority(second_data)
            expected_second_projection = [
                self._expected_projection(row)
                for row in second_data["foundation_skills"]
                if isinstance(row.get("activation"), dict)
                and "runtime_matcher" in row["activation"]
            ]
            if diagnostic is not None:
                violations.append(
                    f"valid second enabled row was rejected: {diagnostic}"
                )
            elif second_projection != expected_second_projection:
                violations.append(
                    "two enabled rows were not projected in registry order: "
                    f"{second_projection!r}"
                )
            elif any(
                set(row) != set(PROJECTION_FIELDS)
                for row in second_projection
            ):
                violations.append("second projection widened the public fields")

        self.assertEqual([], violations)

    def test_predicates_bind_every_semantic_atom_to_closed_generic_primitives(
        self,
    ) -> None:
        violations: list[str] = []
        actual = self.target_activation.get("runtime_matcher")
        if actual != CANONICAL_RUNTIME_MATCHER:
            violations.append(
                "canonical test-strategy runtime_matcher does not equal the "
                "frozen registry authority"
            )

        if isinstance(actual, dict):
            if tuple(actual) != MATCHER_FIELDS:
                violations.append(
                    f"runtime_matcher fields are not closed and ordered: {tuple(actual)!r}"
                )
            if actual.get("contract") != "foundation-semantic-matcher/v1":
                violations.append("runtime_matcher.contract is not exact")
            if actual.get("rollout") != "enabled":
                violations.append("runtime_matcher.rollout is not enabled")
            if actual.get("action") != "analysis-only":
                violations.append("runtime_matcher.action is not analysis-only")
            if actual.get("combine") != "all":
                violations.append("runtime_matcher.combine is not all")
            predicates = actual.get("predicates")
            if not isinstance(predicates, list):
                violations.append("runtime_matcher.predicates is not a list")
            else:
                atoms = [
                    predicate.get("atom")
                    for predicate in predicates
                    if isinstance(predicate, dict)
                ]
                if atoms != self.target_activation["semantic_atoms"]:
                    violations.append(
                        f"predicate atom order is not exact: {atoms!r}"
                    )
                for index, predicate in enumerate(predicates):
                    if not isinstance(predicate, dict):
                        violations.append(
                            f"predicates[{index}] is not a mapping"
                        )
                        continue
                    if tuple(predicate) != PREDICATE_FIELDS:
                        violations.append(
                            f"predicates[{index}] fields are not closed and "
                            f"ordered: {tuple(predicate)!r}"
                        )
                    if predicate.get("operator") != "all-term-groups":
                        violations.append(
                            f"predicates[{index}].operator is not closed"
                        )
                    if predicate.get("scope") != "bounded-clause":
                        violations.append(
                            f"predicates[{index}].scope is not closed"
                        )
                    if predicate.get("polarity") not in {"present", "absent"}:
                        violations.append(
                            f"predicates[{index}].polarity is not closed"
                        )
                    if predicate.get("action") not in {"none", "selection"}:
                        violations.append(
                            f"predicates[{index}].action is not closed"
                        )
                    term_groups = predicate.get("term_groups")
                    if not isinstance(term_groups, list):
                        violations.append(
                            f"predicates[{index}].term_groups is not a list"
                        )
                        continue
                    normalized_groups: list[tuple[str, ...]] = []
                    for group_index, group in enumerate(term_groups):
                        if not isinstance(group, list):
                            violations.append(
                                f"predicates[{index}].term_groups"
                                f"[{group_index}] is not a list"
                            )
                            continue
                        normalized_terms: list[str] = []
                        for term in group:
                            if not isinstance(term, str):
                                violations.append(
                                    f"predicates[{index}].term_groups"
                                    f"[{group_index}] contains a non-string"
                                )
                                continue
                            normalized = " ".join(term.casefold().split())
                            if (
                                term != normalized
                                or not term
                                or any(
                                    not character.isalnum()
                                    and character != " "
                                    for character in term
                                )
                            ):
                                violations.append(
                                    f"predicates[{index}].term_groups"
                                    f"[{group_index}] term is not normalized"
                                )
                            normalized_terms.append(normalized)
                        if len(normalized_terms) != len(set(normalized_terms)):
                            violations.append(
                                f"predicates[{index}].term_groups"
                                f"[{group_index}] contains duplicate terms"
                            )
                        normalized_groups.append(tuple(normalized_terms))
                    if len(normalized_groups) != len(set(normalized_groups)):
                        violations.append(
                            f"predicates[{index}].term_groups contains "
                            "duplicate normalized groups"
                        )

        module_tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
        helper_names = {
            member.name
            for node in module_tree.body
            if isinstance(node, ast.ClassDef)
            for member in node.body
            if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not member.name.startswith("test_")
        }
        forbidden_terms = (
            "match",
            "interpret",
            "classif",
            "route",
            "evaluate",
            "normalize",
        )
        local_authorities = sorted(
            name
            for name in helper_names
            if any(term in name.lower() for term in forbidden_terms)
        )
        if local_authorities:
            violations.append(
                f"local matcher/interpreter authority exists: {local_authorities!r}"
            )

        self.assertEqual([], violations)

    def test_malformed_runtime_matcher_contracts_fail_closed(self) -> None:
        cases: list[tuple[str, object, tuple[str, ...]]] = []

        cases.append(
            (
                "non-mapping-matcher",
                "not-a-mapping",
                ("activation.runtime_matcher", "mapping"),
            )
        )
        for field in MATCHER_FIELDS:
            value = copy.deepcopy(CANONICAL_RUNTIME_MATCHER)
            del value[field]
            cases.append(
                (
                    f"missing-matcher-{field}",
                    value,
                    (f"activation.runtime_matcher.{field}", "required"),
                )
            )
        value = copy.deepcopy(CANONICAL_RUNTIME_MATCHER)
        value["unexpected"] = "forbidden"
        cases.append(
            (
                "unknown-matcher-field",
                value,
                ("activation.runtime_matcher.unexpected", "unknown"),
            )
        )
        for field, invalid in (
            ("contract", "foundation-semantic-matcher/v2"),
            ("rollout", "disabled"),
            ("action", "implementation"),
            ("combine", "any"),
        ):
            value = copy.deepcopy(CANONICAL_RUNTIME_MATCHER)
            value[field] = invalid
            cases.append(
                (
                    f"invalid-matcher-{field}",
                    value,
                    (f"activation.runtime_matcher.{field}",),
                )
            )

        value = copy.deepcopy(CANONICAL_RUNTIME_MATCHER)
        value["predicates"] = []
        cases.append(
            (
                "empty-predicates",
                value,
                ("activation.runtime_matcher.predicates", "non-empty"),
            )
        )
        value = copy.deepcopy(CANONICAL_RUNTIME_MATCHER)
        value["predicates"] = {}
        cases.append(
            (
                "non-list-predicates",
                value,
                ("activation.runtime_matcher.predicates", "list"),
            )
        )
        value = copy.deepcopy(CANONICAL_RUNTIME_MATCHER)
        value["predicates"][0] = "not-a-mapping"
        cases.append(
            (
                "non-mapping-predicate",
                value,
                ("activation.runtime_matcher.predicates[0]", "mapping"),
            )
        )
        for field in PREDICATE_FIELDS:
            value = copy.deepcopy(CANONICAL_RUNTIME_MATCHER)
            del value["predicates"][0][field]
            cases.append(
                (
                    f"missing-predicate-{field}",
                    value,
                    (
                        "activation.runtime_matcher.predicates[0]."
                        f"{field}",
                        "required",
                    ),
                )
            )
        value = copy.deepcopy(CANONICAL_RUNTIME_MATCHER)
        value["predicates"][0]["unexpected"] = "forbidden"
        cases.append(
            (
                "unknown-predicate-field",
                value,
                (
                    "activation.runtime_matcher.predicates[0].unexpected",
                    "unknown",
                ),
            )
        )

        value = copy.deepcopy(CANONICAL_RUNTIME_MATCHER)
        value["predicates"][1]["atom"] = value["predicates"][0]["atom"]
        cases.append(
            (
                "duplicate-atom-binding",
                value,
                (
                    "activation.runtime_matcher.predicates[1].atom",
                    "duplicate",
                ),
            )
        )
        value = copy.deepcopy(CANONICAL_RUNTIME_MATCHER)
        extra = copy.deepcopy(value["predicates"][-1])
        extra["atom"] = "extra-semantic-atom"
        value["predicates"].append(extra)
        cases.append(
            (
                "extra-atom-binding",
                value,
                ("activation.runtime_matcher.predicates[3].atom",),
            )
        )
        value = copy.deepcopy(CANONICAL_RUNTIME_MATCHER)
        value["predicates"].pop()
        cases.append(
            (
                "missing-atom-binding",
                value,
                (
                    "activation.runtime_matcher.predicates",
                    "single-fixed-command-absent",
                ),
            )
        )
        value = copy.deepcopy(CANONICAL_RUNTIME_MATCHER)
        value["predicates"][0], value["predicates"][1] = (
            value["predicates"][1],
            value["predicates"][0],
        )
        cases.append(
            (
                "out-of-order-atom-binding",
                value,
                ("activation.runtime_matcher.predicates[0].atom",),
            )
        )

        for field, invalid in (
            ("operator", "any-term-group"),
            ("scope", "whole-prompt"),
            ("polarity", "optional"),
            ("action", "implementation"),
        ):
            value = copy.deepcopy(CANONICAL_RUNTIME_MATCHER)
            value["predicates"][0][field] = invalid
            cases.append(
                (
                    f"invalid-predicate-{field}",
                    value,
                    (
                        "activation.runtime_matcher.predicates[0]."
                        f"{field}",
                    ),
                )
            )

        value = copy.deepcopy(CANONICAL_RUNTIME_MATCHER)
        value["predicates"][0]["term_groups"] = []
        cases.append(
            (
                "empty-term-groups",
                value,
                (
                    "activation.runtime_matcher.predicates[0].term_groups",
                    "non-empty",
                ),
            )
        )
        value = copy.deepcopy(CANONICAL_RUNTIME_MATCHER)
        value["predicates"][0]["term_groups"] = {}
        cases.append(
            (
                "non-list-term-groups",
                value,
                (
                    "activation.runtime_matcher.predicates[0].term_groups",
                    "list",
                ),
            )
        )
        value = copy.deepcopy(CANONICAL_RUNTIME_MATCHER)
        value["predicates"][0]["term_groups"][0] = []
        cases.append(
            (
                "empty-inner-group",
                value,
                (
                    "activation.runtime_matcher.predicates[0].term_groups[0]",
                    "non-empty",
                ),
            )
        )
        value = copy.deepcopy(CANONICAL_RUNTIME_MATCHER)
        value["predicates"][0]["term_groups"][0] = "several"
        cases.append(
            (
                "non-list-inner-group",
                value,
                (
                    "activation.runtime_matcher.predicates[0].term_groups[0]",
                    "list",
                ),
            )
        )
        value = copy.deepcopy(CANONICAL_RUNTIME_MATCHER)
        value["predicates"][0]["term_groups"][0][0] = 7
        cases.append(
            (
                "non-string-term",
                value,
                (
                    "activation.runtime_matcher.predicates[0]."
                    "term_groups[0][0]",
                    "string",
                ),
            )
        )
        value = copy.deepcopy(CANONICAL_RUNTIME_MATCHER)
        value["predicates"][0]["term_groups"][0][0] = " Several "
        cases.append(
            (
                "non-normalized-term",
                value,
                (
                    "activation.runtime_matcher.predicates[0]."
                    "term_groups[0][0]",
                    "normalized",
                ),
            )
        )
        value = copy.deepcopy(CANONICAL_RUNTIME_MATCHER)
        value["predicates"][0]["term_groups"][0][1] = "several"
        cases.append(
            (
                "duplicate-term",
                value,
                (
                    "activation.runtime_matcher.predicates[0]."
                    "term_groups[0][1]",
                    "duplicate",
                ),
            )
        )
        value = copy.deepcopy(CANONICAL_RUNTIME_MATCHER)
        value["predicates"][0]["term_groups"][1] = copy.deepcopy(
            value["predicates"][0]["term_groups"][0]
        )
        cases.append(
            (
                "duplicate-normalized-group",
                value,
                (
                    "activation.runtime_matcher.predicates[0].term_groups[1]",
                    "duplicate",
                ),
            )
        )

        violations: list[str] = []
        authority = getattr(VALIDATION, AUTHORITY_NAME, None)
        if not callable(authority):
            violations.append(f"{AUTHORITY_NAME} is missing or not callable")
        else:
            for label, malformed_matcher, required_fragments in cases:
                data = self._v8_data(malformed_matcher)
                _value, diagnostic = self._invoke_authority(data)
                if diagnostic is None:
                    violations.append(f"{label}: malformed input was accepted")
                    continue
                missing_fragments = [
                    fragment
                    for fragment in required_fragments
                    if fragment not in diagnostic
                ]
                if missing_fragments:
                    violations.append(
                        f"{label}: missing diagnostics {missing_fragments!r}; "
                        f"found {diagnostic!r}"
                    )

        self.assertEqual([], violations)

    def test_runtime_matcher_metadata_is_authoring_only(self) -> None:
        body = """# sample-runtime-authority

## Skill Role

Own one synthetic decision boundary.

## High-Value Rules

- Preserve the public build projection.

## Anti-Patterns

- Do not render authoring-only registry metadata.

## Stop Conditions

- Stop when metadata changes rendered behavior.

## Targeted References

- None.
"""
        activation = copy.deepcopy(self.target_activation)
        activation.pop("runtime_matcher", None)
        registry_without = {
            "activation": activation,
            "reference_index": [],
        }
        item_without = BUILD.SkillItem(
            name="sample-runtime-authority",
            path=(
                ROOT
                / "src"
                / "foundation"
                / "capabilities"
                / "sample-runtime-authority"
            ),
            layer="foundation",
            description="synthetic",
            metadata={},
            body=body,
            registry=registry_without,
        )

        sentinel_runtime_metadata = {
            "contract": "foundation-semantic-matcher/v1",
            "rollout": "runtime-matcher-rollout-sentinel",
            "action": "runtime-matcher-action-sentinel",
            "combine": "runtime-matcher-combine-sentinel",
            "predicates": [
                {
                    "atom": "runtime-matcher-atom-sentinel",
                    "operator": "runtime-matcher-operator-sentinel",
                    "scope": "runtime-matcher-scope-sentinel",
                    "polarity": "runtime-matcher-polarity-sentinel",
                    "action": "runtime-matcher-predicate-action-sentinel",
                    "term_groups": [
                        ["runtime matcher term sentinel"],
                    ],
                }
            ],
        }
        registry_with = copy.deepcopy(registry_without)
        registry_with["activation"]["runtime_matcher"] = (
            sentinel_runtime_metadata
        )
        item_with = replace(item_without, registry=registry_with)

        rendered_without = BUILD._render_layer3_reference(item_without)
        rendered_with = BUILD._render_layer3_reference(item_with)
        self.assertEqual(
            rendered_without.encode("utf-8"),
            rendered_with.encode("utf-8"),
        )
        for forbidden in (
            "runtime_matcher",
            "foundation-activation/v1",
            "foundation-semantic-matcher/v1",
            "runtime-matcher-rollout-sentinel",
            "runtime-matcher-action-sentinel",
            "runtime-matcher-combine-sentinel",
            "runtime-matcher-atom-sentinel",
            "runtime-matcher-operator-sentinel",
            "runtime-matcher-scope-sentinel",
            "runtime-matcher-polarity-sentinel",
            "runtime-matcher-predicate-action-sentinel",
            "runtime matcher term sentinel",
        ):
            self.assertNotIn(forbidden, rendered_with)

        module_tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
        imported_modules = {
            alias.name
            for node in ast.walk(module_tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertFalse(
            any(
                "deterministic_route_oracle" in name
                or "mock" in name
                or "monkeypatch" in name
                for name in imported_modules
            )
        )
        patch_calls = [
            node
            for node in ast.walk(module_tree)
            if isinstance(node, ast.Call)
            and (
                isinstance(node.func, ast.Name)
                and node.func.id in {"patch", "monkeypatch"}
                or isinstance(node.func, ast.Attribute)
                and node.func.attr in {"patch", "monkeypatch"}
            )
        ]
        self.assertEqual([], patch_calls)


class Repair177FoundationOccurrenceAuthorityRedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = VALIDATION.load_yaml_file(FOUNDATION_REGISTRY)
        cls.rows = cls.data["foundation_skills"]
        cls.rows_by_name = {
            row["name"]: row
            for row in cls.rows
            if isinstance(row, dict)
            and isinstance(row.get("name"), str)
        }

    def _authority(self, data: object) -> tuple[object, str | None]:
        authority = getattr(VALIDATION, AUTHORITY_NAME, None)
        if not callable(authority):
            return None, f"{AUTHORITY_NAME} is missing or not callable"
        try:
            return authority(data), None
        except Exception as exc:
            return None, f"{type(exc).__name__}: {exc}"

    def test_repair177_registry_adds_two_ordered_activation_rows(self) -> None:
        violations: list[str] = []
        missing = [
            name
            for name in REPAIR177_TARGETS
            if name not in self.rows_by_name
            or not isinstance(
                self.rows_by_name[name].get("activation"),
                dict,
            )
        ]
        if missing:
            violations.append(
                f"missing registry activation rows: {missing!r}"
            )

        activation_rows = [
            row
            for row in self.rows
            if isinstance(row.get("activation"), dict)
        ]
        if len(activation_rows) != 24:
            violations.append(
                "Repair177 must add exactly two activation rows to the "
                f"unchanged legacy 22; found {len(activation_rows)}"
            )
        activation_ids = [
            row["activation"].get("id")
            for row in activation_rows
        ]
        for activation_id in REPAIR177_ACTIVATION_IDS:
            if activation_ids.count(activation_id) != 1:
                violations.append(
                    f"{activation_id!r} must occur exactly once"
                )

        projections, diagnostic = self._authority(self.data)
        if diagnostic is not None:
            violations.append(f"canonical authority failed: {diagnostic}")
        elif isinstance(projections, list):
            projected_targets = [
                projection
                for projection in projections
                if projection.get("name") in REPAIR177_TARGETS
            ]
            if [
                projection.get("name")
                for projection in projected_targets
            ] != list(REPAIR177_TARGETS):
                violations.append(
                    "Repair177 projections are not in Foundation registry "
                    f"order: {projected_targets!r}"
                )

            legacy_names = [
                projection.get("name")
                for projection in projections
                if projection.get("name") not in REPAIR177_TARGETS
            ]
            if legacy_names != [TARGET_NAME]:
                violations.append(
                    "the pre-Repair177 enabled matcher projection changed: "
                    f"{legacy_names!r}"
                )

        self.assertEqual([], violations)

    def test_repair177_occurrence_authority_projection_is_canonical(self) -> None:
        violations: list[str] = []
        projections, diagnostic = self._authority(self.data)
        if diagnostic is not None:
            violations.append(f"canonical authority failed: {diagnostic}")
            projections = []
        projection_by_name = {
            projection.get("name"): projection
            for projection in projections
            if isinstance(projection, dict)
        }

        for name, activation_id in zip(
            REPAIR177_TARGETS,
            REPAIR177_ACTIVATION_IDS,
            strict=True,
        ):
            row = self.rows_by_name.get(name)
            if not isinstance(row, dict):
                violations.append(f"{name}: registry row is absent")
                continue
            activation = row.get("activation")
            if not isinstance(activation, dict):
                violations.append(f"{name}: activation is absent")
                continue

            if set(activation) != {
                *ACTIVATION_FIELDS,
                "runtime_matcher",
            }:
                violations.append(
                    f"{name}: activation fields are not the closed schema-v8 "
                    f"set: {sorted(activation)!r}"
                )
            expected_route = {
                "contract": "foundation-activation/v1",
                "id": activation_id,
                "mode": "explicit-analyzed",
                "path": "analyzed",
                "profile": "analysis-agent",
                "primary_skill": "domain-impact-modeler",
                "review_skill": "architecture-impact-reviewer",
            }
            actual_route = {
                field: activation.get(field)
                for field in expected_route
            }
            if actual_route != expected_route:
                violations.append(
                    f"{name}: activation route mismatch {actual_route!r}"
                )

            matcher = activation.get("runtime_matcher")
            if not isinstance(matcher, dict):
                violations.append(f"{name}: runtime_matcher is absent")
                continue
            if tuple(matcher) != REPAIR177_MATCHER_FIELDS:
                violations.append(
                    f"{name}: matcher fields are not closed and ordered"
                )
            for field, expected in (
                ("contract", "foundation-occurrence-matcher/v1"),
                ("rollout", "enabled"),
                ("action", "analysis-only"),
                ("combine", "any"),
            ):
                if matcher.get(field) != expected:
                    violations.append(
                        f"{name}: matcher.{field} != {expected!r}"
                    )
            relations = matcher.get("relations")
            if not isinstance(relations, list) or len(relations) != 1:
                violations.append(
                    f"{name}: matcher.relations must contain exactly one row"
                )
                continue
            relation = relations[0]
            if not isinstance(relation, dict):
                violations.append(f"{name}: relation is not a mapping")
                continue
            if tuple(relation) != REPAIR177_RELATION_FIELDS:
                violations.append(
                    f"{name}: relation fields are not closed and ordered"
                )
            expected_relation = REPAIR177_RELATION_EXPECTATIONS[name]
            expected = {
                "atom": expected_relation["atom"],
                "operator": "governed-object-occurrence",
                "scope": "bounded-clause",
                "actions": expected_relation["actions"],
                "objects": expected_relation["objects"],
                "owner_relation": expected_relation["owner_relation"],
                "non_owner_modifiers": expected_relation[
                    "non_owner_modifiers"
                ],
            }
            if relation != expected:
                violations.append(
                    f"{name}: canonical relation mismatch {relation!r}"
                )
            if tuple(relation.get("owner_relation", {})) != (
                REPAIR177_OWNER_RELATION_FIELDS
            ):
                violations.append(
                    f"{name}: owner_relation fields are not closed and ordered"
                )
            if activation.get("semantic_atoms") != [
                expected_relation["atom"]
            ]:
                violations.append(
                    f"{name}: relation atom is not the sole semantic atom"
                )

            projection = projection_by_name.get(name)
            if not isinstance(projection, dict):
                violations.append(f"{name}: authority projection is absent")
                continue
            expected_projection = {
                "name": name,
                "activation_id": activation["id"],
                "path": activation["path"],
                "profile": activation["profile"],
                "primary_skill": activation["primary_skill"],
                "review_skill": activation["review_skill"],
                "semantic_atoms": activation["semantic_atoms"],
                "matcher_evidence": activation["matcher_evidence"],
                "runtime_matcher": activation["runtime_matcher"],
            }
            if projection != expected_projection:
                violations.append(
                    f"{name}: authority projection lost registry binding"
                )

        if not violations:
            business_projection = projection_by_name[
                "business-rule-extraction"
            ]
            state_projection = projection_by_name["state-machine-modeling"]
            business_projection["runtime_matcher"]["relations"][0][
                "non_owner_modifiers"
            ].append("projection-mutation")
            business_projection["semantic_atoms"].append(
                "projection-mutation"
            )
            business_projection["matcher_evidence"].append(
                "projection-mutation"
            )
            self.assertNotIn(
                "projection-mutation",
                self.rows_by_name["business-rule-extraction"]["activation"][
                    "runtime_matcher"
                ]["relations"][0]["non_owner_modifiers"],
            )
            self.assertNotIn(
                "projection-mutation",
                self.rows_by_name["business-rule-extraction"]["activation"][
                    "semantic_atoms"
                ],
            )
            self.assertNotIn(
                "projection-mutation",
                self.rows_by_name["business-rule-extraction"]["activation"][
                    "matcher_evidence"
                ],
            )
            self.assertEqual(
                ["accepted", "current", "existing", "material"],
                self.rows_by_name["business-rule-extraction"]["activation"][
                    "runtime_matcher"
                ]["relations"][0]["non_owner_modifiers"],
            )
            self.assertEqual(
                [
                    "accepted",
                    "current",
                    "existing",
                    "material",
                    "proposed",
                    "target",
                ],
                state_projection["runtime_matcher"]["relations"][0][
                    "non_owner_modifiers"
                ],
                "authority must preserve B4 and S6 independently",
            )

        self.assertEqual([], violations)


if __name__ == "__main__":
    unittest.main()
