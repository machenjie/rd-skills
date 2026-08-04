from __future__ import annotations

import ast
import json
import sys
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from deterministic_route_oracle import route_with_trace  # noqa: E402
from validation_utils import compute_execution_level, load_yaml_file  # noqa: E402


FOUNDATION_REGISTRY = ROOT / "src" / "registry" / "foundation-skills.yaml"
DOMAIN_REGISTRY = ROOT / "src" / "registry" / "domain-skills.yaml"
CORE_CONTRACTS = ROOT / "src" / "control-model" / "core-contracts.json"
ROUTE_ORACLE = ROOT / "scripts" / "deterministic_route_oracle.py"
ACTIVATION_ID = "foundation-activation-test-strategy"
TASK_ID = "T4B-ACT-V3-ANALYZED-MATCHER-RED-01"
LEGACY_EXACT_PHRASE = "explicit test strategy decision"

PROMPTS = {
    "positive": (
        "Analyze which proof portfolio should cover several material failure "
        "mechanisms. Select the test levels, observable failure oracles, and "
        "justified omissions because no single command has been fixed."
    ),
    "n1": (
        "Summarize the existing proof portfolio and fixed failure-oracle mapping "
        "without selecting test levels or omissions."
    ),
    "n2": (
        "One test level and command are already fixed; only implement the "
        "accepted tests."
    ),
    "n3": (
        "Define observable acceptance for normal, invalid, boundary, and "
        "forbidden outcomes."
    ),
    "n4": "Implement regression tests proving the changed behavior.",
}


def _main_execution(
    case: str,
    execution_contract: dict[str, Any],
) -> dict[str, Any]:
    case_task_id = f"{TASK_ID}:{case}"
    trigger_evaluations = {
        row["id"]: {
            "status": "not_matched",
            "evidence_kind": "analysis_handoff",
            "source_anchor": f"handoff:{case_task_id}:trigger:{row['id']}",
            "plausible_critical": False,
        }
        for row in execution_contract["trigger_registry"]
    }
    shared_contract_id = "no-shared-contract-or-external-consumer"
    l2_evaluations = {
        row["id"]: {
            "status": "false" if row["id"] == shared_contract_id else "true",
            "evidence_kind": "analysis_handoff",
            "source_anchor": f"handoff:{case_task_id}:l2:{row['id']}",
        }
        for row in execution_contract["l2_eligibility"]
    }
    if shared_contract_id not in l2_evaluations:
        raise AssertionError(
            f"Core contract lacks required L2 predicate {shared_contract_id!r}"
        )
    computed = compute_execution_level(
        requested="unspecified",
        trigger_evaluations=trigger_evaluations,
        l2_evaluations=l2_evaluations,
        contract=execution_contract,
    )
    if (
        computed["effective_level"] != "L3"
        or computed["level_basis"]["unresolved"]
        or computed["level_basis"]["edit_status"] != "allowed"
    ):
        raise AssertionError("Core contract did not derive the required editable L3")
    return {
        "producer": "main-control-agent",
        "task_id": case_task_id,
        "execution_level": computed["effective_level"],
        "level_basis": computed["level_basis"],
    }


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _collect_string_values(value: object) -> set[str]:
    collected: set[str] = set()

    def visit(item: object) -> None:
        if isinstance(item, str):
            collected.add(item)
        elif isinstance(item, dict):
            for child in item.values():
                visit(child)
        elif isinstance(item, (list, tuple, set, frozenset)):
            for child in item:
                visit(child)

    visit(value)
    return collected


def _final_result(observed: dict[str, Any]) -> dict[str, Any]:
    return observed["route_decision"]["route_result"]


class FoundationActivationAnalyzedMatcherRedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        foundation_rows = load_yaml_file(FOUNDATION_REGISTRY)["foundation_skills"]
        authority_rows = [
            row
            for row in foundation_rows
            if row.get("activation", {}).get("id") == ACTIVATION_ID
        ]
        if len(authority_rows) != 1:
            raise AssertionError(
                f"expected exactly one activation authority for {ACTIVATION_ID}"
            )
        cls.authority_row = authority_rows[0]
        cls.activation = cls.authority_row["activation"]
        cls.target_name = cls.authority_row["name"]
        cls.semantic_atoms = tuple(cls.activation["semantic_atoms"])
        cls.matcher_evidence = tuple(cls.activation["matcher_evidence"])

        domain_rows = load_yaml_file(DOMAIN_REGISTRY)["domain_skills"]
        cls.domain_names = frozenset(row["name"] for row in domain_rows)
        if not cls.domain_names:
            raise AssertionError("Domain registry must provide the negative guard set")

        core_contracts = json.loads(CORE_CONTRACTS.read_text(encoding="utf-8"))
        cls.execution_contract = core_contracts["execution_level_contract"]
        cls.main_executions = {
            case: _main_execution(case, cls.execution_contract)
            for case in PROMPTS
        }
        cls.observations = {
            case: route_with_trace(
                prompt,
                main_execution=cls.main_executions[case],
            )
            for case, prompt in PROMPTS.items()
        }

    def _assert_target_and_domains_absent(self, case: str) -> None:
        observed = self.observations[case]
        raw_values = _collect_string_values(
            observed["winner_trace"]["raw_candidates"]
        )
        final_values = _collect_string_values(
            _final_result(observed)["layer3_skills"]
        )
        self.assertEqual(
            {
                "target_in_raw": False,
                "target_in_final": False,
                "raw_domain_intersection": set(),
                "final_domain_intersection": set(),
            },
            {
                "target_in_raw": self.target_name in raw_values,
                "target_in_final": self.target_name in final_values,
                "raw_domain_intersection": raw_values & self.domain_names,
                "final_domain_intersection": final_values & self.domain_names,
            },
            msg=f"{case} must suppress the target and every registry-derived Domain",
        )

    def test_semantic_positive_registry_route(self) -> None:
        observed = self.observations["positive"]
        route_decision = observed["route_decision"]
        result = _final_result(observed)
        winner = observed["winner_trace"]
        expected_evidence = [
            *self.matcher_evidence,
            f"foundation-selector:{ACTIVATION_ID}",
        ]
        raw_candidates = winner["raw_candidates"]
        candidate = raw_candidates[0] if len(raw_candidates) == 1 else {}
        selected_candidate = winner.get("selected_candidate", {})
        raw_values = _collect_string_values(raw_candidates)
        final_values = _collect_string_values(result["layer3_skills"])
        self.assertEqual(
            {
                "raw_candidate_count": 1,
                "candidate_id": self.activation["id"],
                "path": self.activation["path"],
                "profile": self.activation["profile"],
                "primary_skill": self.activation["primary_skill"],
                "review_skill": self.activation["review_skill"],
                "layer3_skills": [self.target_name],
                "candidate_match_evidence": expected_evidence,
                "candidate_semantic_atoms": list(self.semantic_atoms),
                "selected_candidate_id": self.activation["id"],
                "winner_rule_id": self.activation["id"],
                "winner_match_evidence": expected_evidence,
                "winner_semantic_atoms": list(self.semantic_atoms),
                "final_path": self.activation["path"],
                "final_profile": self.activation["profile"],
                "final_primary_skill": self.activation["primary_skill"],
                "final_review_skill": self.activation["review_skill"],
                "final_layer3_skills": [self.target_name],
                "execution_level": "L3",
                "route_once": True,
                "trace_route_once": "proven",
                "raw_domain_intersection": set(),
                "final_domain_intersection": set(),
            },
            {
                "raw_candidate_count": len(raw_candidates),
                "candidate_id": candidate.get("candidate_id"),
                "path": candidate.get("path"),
                "profile": candidate.get("profile"),
                "primary_skill": candidate.get("primary_skill"),
                "review_skill": candidate.get("review_skill"),
                "layer3_skills": candidate.get("layer3_skills"),
                "candidate_match_evidence": candidate.get("evidence"),
                "candidate_semantic_atoms": candidate.get("semantic_atoms"),
                "selected_candidate_id": selected_candidate.get("candidate_id"),
                "winner_rule_id": winner.get("rule_id"),
                "winner_match_evidence": winner.get("match_evidence"),
                "winner_semantic_atoms": winner.get("semantic_atoms"),
                "final_path": route_decision["path"],
                "final_profile": result["start_profile"],
                "final_primary_skill": result["primary_skill"],
                "final_review_skill": result["review_skill"],
                "final_layer3_skills": result["layer3_skills"],
                "execution_level": result["execution_level"],
                "route_once": route_decision["route_once"],
                "trace_route_once": winner["route_once"],
                "raw_domain_intersection": raw_values & self.domain_names,
                "final_domain_intersection": final_values & self.domain_names,
            },
            msg=(
                "the sole semantic route must be owned and evidenced only by its "
                "registry activation; "
                f"atoms={self.semantic_atoms!r}, evidence={self.matcher_evidence!r}"
            ),
        )

    def test_legacy_keyword_only_source_and_candidate_guard(self) -> None:
        oracle_source = ROUTE_ORACLE.read_text(encoding="utf-8")
        oracle_tree = ast.parse(oracle_source)
        string_literals = {
            node.value
            for node in ast.walk(oracle_tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }
        violations: list[str] = []
        obsolete_authorities = {
            LEGACY_EXACT_PHRASE: "legacy exact phrase",
            "explicit-test-strategy-analysis": "obsolete candidate/rule identity",
            "explicit-test-strategy-decision": "obsolete target evidence identity",
        }
        for authority, label in obsolete_authorities.items():
            if authority in string_literals:
                violations.append(label)

        hardcoded_activation_values = {
            self.target_name,
            *self.semantic_atoms,
        }
        matcher_evidence_set = set(self.matcher_evidence)
        for node in ast.walk(oracle_tree):
            if isinstance(node, (ast.List, ast.Tuple, ast.Set, ast.Dict)):
                container_literals = {
                    child.value
                    for child in ast.walk(node)
                    if isinstance(child, ast.Constant)
                    and isinstance(child.value, str)
                }
                if matcher_evidence_set <= container_literals:
                    violations.append(
                        "hardcoded full matcher-evidence container"
                    )
            if isinstance(node, ast.If):
                branch_literals = {
                    child.value
                    for statement in node.body
                    for child in ast.walk(statement)
                    if isinstance(child, ast.Constant)
                    and isinstance(child.value, str)
                }
                if matcher_evidence_set <= branch_literals:
                    violations.append(
                        "hardcoded full matcher-evidence branch authority"
                    )
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name):
                called_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                called_name = node.func.attr
            else:
                continue
            if "candidate" not in called_name.lower():
                continue
            call_literals = {
                child.value
                for child in ast.walk(node)
                if isinstance(child, ast.Constant)
                and isinstance(child.value, str)
            }
            leaked = sorted(call_literals & hardcoded_activation_values)
            if leaked:
                violations.append(
                    f"hardcoded activation authority in {called_name}: {leaked!r}"
                )

        self.assertEqual(
            [],
            sorted(set(violations)),
            msg=(
                "the oracle must remove legacy and hardcoded target-specific "
                "authority in favor of registry-generic activation access"
            ),
        )

    def test_n1_n2_suppress_target_and_domain_activation(self) -> None:
        for case in ("n1", "n2"):
            with self.subTest(case=case):
                self._assert_target_and_domains_absent(case)

    def test_n3_n4_preserve_adjacent_authorities(self) -> None:
        for case in ("n3", "n4"):
            with self.subTest(case=case):
                self._assert_target_and_domains_absent(case)

        n3_decision = self.observations["n3"]["route_decision"]
        n3_result = _final_result(self.observations["n3"])
        self.assertEqual(
            {
                "path": "analyzed",
                "profile": "analysis-agent",
                "primary_skill": "acceptance-criteria-builder",
            },
            {
                "path": n3_decision["path"],
                "profile": n3_result["start_profile"],
                "primary_skill": n3_result["primary_skill"],
            },
        )

        n4_decision = self.observations["n4"]["route_decision"]
        n4_result = _final_result(self.observations["n4"])
        self.assertEqual(
            {
                "path": "direct",
                "profile": "task-agent",
                "primary_skill": "quality-test-gate",
                "layer3_skills": ["regression-testing"],
            },
            {
                "path": n4_decision["path"],
                "profile": n4_result["start_profile"],
                "primary_skill": n4_result["primary_skill"],
                "layer3_skills": n4_result["layer3_skills"],
            },
        )

    def test_public_surface_and_routing_invariants(self) -> None:
        module_source = Path(__file__).read_text(encoding="utf-8")
        module_tree = ast.parse(module_source)
        surface_violations: list[str] = []
        oracle_imports = [
            (alias.name, alias.asname)
            for node in module_tree.body
            if isinstance(node, ast.ImportFrom)
            and node.module == "deterministic_route_oracle"
            for alias in node.names
        ]
        if oracle_imports != [("route_with_trace", None)]:
            surface_violations.append(
                f"non-canonical oracle imports: {oracle_imports!r}"
            )
        if any(
            isinstance(node, ast.Import)
            and any(
                alias.name == "deterministic_route_oracle"
                for alias in node.names
            )
            for node in module_tree.body
        ):
            surface_violations.append("module or alternate oracle import")
        route_calls = [
            node
            for node in ast.walk(module_tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "route_with_trace"
        ]
        if len(route_calls) != 1:
            surface_violations.append(
                f"expected one canonical route call site, found {len(route_calls)}"
            )
        module_helpers = {
            node.name
            for node in module_tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        forbidden_helper_terms = (
            "match",
            "classif",
            "select",
            "candidate",
            "routing",
        )
        local_authorities = sorted(
            name
            for name in module_helpers
            if any(term in name.lower() for term in forbidden_helper_terms)
        )
        if local_authorities:
            surface_violations.append(
                f"local matcher/classifier/selector authority: {local_authorities!r}"
            )
        imported_names = {
            alias.name
            for node in ast.walk(module_tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        if any("mock" in name.lower() or "monkeypatch" in name.lower() for name in imported_names):
            surface_violations.append("mock or monkeypatch import")
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
        if patch_calls:
            surface_violations.append("patch or monkeypatch call")
        self.assertEqual([], surface_violations)

        positive_lower = PROMPTS["positive"].lower()
        self.assertNotIn(ACTIVATION_ID.lower(), positive_lower)
        self.assertNotIn(self.target_name.lower(), positive_lower)
        self.assertNotIn(LEGACY_EXACT_PHRASE, positive_lower)
        for trigger_signal in self.authority_row.get("trigger_signals", []):
            self.assertNotIn(trigger_signal.lower(), positive_lower)
        self.assertTrue(self.semantic_atoms)
        self.assertTrue(self.matcher_evidence)
        self.assertEqual({"positive", "n1", "n2", "n3", "n4"}, set(PROMPTS))
        self.assertEqual(5, len(self.observations))

        domain_rows = load_yaml_file(DOMAIN_REGISTRY)["domain_skills"]
        self.assertEqual(
            frozenset(row["name"] for row in domain_rows),
            self.domain_names,
        )
        source_string_literals = {
            node.value
            for node in ast.walk(module_tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }
        self.assertFalse(source_string_literals & self.domain_names)

        for case, observed in self.observations.items():
            with self.subTest(case=case):
                decision = observed["route_decision"]
                result = _final_result(observed)
                selection = decision["selection_evidence"]
                self.assertEqual("L3", self.main_executions[case]["execution_level"])
                self.assertEqual(
                    self.main_executions[case]["execution_level"],
                    result["execution_level"],
                )
                self.assertEqual(
                    _canonical_bytes(self.main_executions[case]["level_basis"]),
                    _canonical_bytes(result["level_basis"]),
                )
                self.assertEqual(
                    _canonical_bytes(self.main_executions[case]),
                    _canonical_bytes(decision["main_execution_provenance"]),
                )
                self.assertIs(decision["route_once"], True)
                self.assertEqual("proven", observed["winner_trace"]["route_once"])
                self.assertLessEqual(len(result["layer3_skills"]), 3)
                self.assertIsInstance(result["primary_skill"], str)
                self.assertTrue(result["primary_skill"])
                self.assertIsInstance(result["review_skill"], str)
                self.assertTrue(result["review_skill"])
                self.assertEqual(1, selection["eligible_primary_count"])
                self.assertEqual(
                    1,
                    sum(
                        candidate["eligible"]
                        for candidate in selection["primary_candidates"]
                    ),
                )
                self.assertEqual(
                    1,
                    sum(
                        candidate["eligible"]
                        for candidate in selection["review_candidates"]
                    ),
                )


if __name__ == "__main__":
    unittest.main()
