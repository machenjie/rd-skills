from __future__ import annotations

import importlib.util
import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "eval-rendered-context-budget.py"
TEST_TIMEOUT_CLASS = "source-validation"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(
        "eval_rendered_context_budget_tests",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


EVAL = _load_module()
SOURCE_ROOT = ROOT
FOCUS_BASELINE_REF = "3e3c54aa108ea23287ad2b752a4b36c73486643f"
FOCUS_BASELINE_SHA256 = (
    "85e4090f5f3f59be900af0e0ec288d68bb448c3c7a7ad69bd87bec887b4a6b2a"
)


def _load_built_link_validator():
    path = ROOT / "scripts/validate-built-skill-reference-links.py"
    spec = importlib.util.spec_from_file_location(
        "eval_rendered_built_link_validator_tests", path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BUILT_LINK_VALIDATOR = _load_built_link_validator()

import build as BUILD  # noqa: E402
import validation_utils as VALIDATION  # noqa: E402

from fixture_capsule_contract import (
    FixtureCapsuleError,
    runtime_layer3_reference_path,
    validate_and_render_fixture_capsule,
)


def _build_runtime_subject(subject: Path) -> None:
    for relative in ("src", "scripts", "evals", "reports", "tests"):
        shutil.copytree(
            SOURCE_ROOT / relative,
            subject / relative,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )
    shutil.copy2(SOURCE_ROOT / "pyproject.toml", subject / "pyproject.toml")

    build_source_root = BUILD.ROOT

    def rebased(path: Path) -> Path:
        return subject / path.relative_to(build_source_root)

    with mock.patch.multiple(
        BUILD,
        ROOT=subject,
        SRC_DIR=rebased(BUILD.SRC_DIR),
        REGISTRY_DIR=rebased(BUILD.REGISTRY_DIR),
        DIST_DIR=subject / "dist",
        UNIVERSAL_SKILLS_ROOT=rebased(BUILD.UNIVERSAL_SKILLS_ROOT),
        OPENAI_ZIP_DIR=rebased(BUILD.OPENAI_ZIP_DIR),
        PROFILE_SOURCE=rebased(BUILD.PROFILE_SOURCE),
        HOST_ENFORCEMENT_SOURCE=rebased(BUILD.HOST_ENFORCEMENT_SOURCE),
        CONTROL_PROMPT_SOURCE=rebased(BUILD.CONTROL_PROMPT_SOURCE),
        CORE_CONTRACTS_PATH=rebased(BUILD.CORE_CONTRACTS_PATH),
        LAYER_SOURCE_ROOTS={
            layer: rebased(path)
            for layer, path in BUILD.LAYER_SOURCE_ROOTS.items()
        },
        AGENT_SKILL_ROOTS=tuple(rebased(path) for path in BUILD.AGENT_SKILL_ROOTS),
        AGENT_PROFILE_OUTPUTS=tuple(
            (platform, rebased(path))
            for platform, path in BUILD.AGENT_PROFILE_OUTPUTS
        ),
    ):
        result = BUILD.build_profile(BUILD.RUNTIME_PROFILE)
    if result["top_level_count"] != 26 or result["agent_profile_count"] != 4:
        raise AssertionError(f"temporary Runtime build is incomplete: {result}")


def _focus_baseline_document() -> dict[str, object]:
    result = subprocess.run(
        [
            "git",
            "show",
            f"{FOCUS_BASELINE_REF}:evals/agent-light-trajectories/cases.yaml",
        ],
        cwd=SOURCE_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    document = json.loads(result.stdout)
    cases = document["task_focus_cases"]
    canonical = json.dumps(
        cases,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    if hashlib.sha256(canonical.encode("utf-8")).hexdigest() != FOCUS_BASELINE_SHA256:
        raise AssertionError("branch-independent task-focus baseline is stale")
    return {"task_focus_cases": cases}


def setUpModule() -> None:
    global ROOT
    runtime = tempfile.TemporaryDirectory(
        prefix=".rendered-context-subject-",
    )
    subject = Path(runtime.name).resolve()
    if subject.resolve().is_relative_to(SOURCE_ROOT.resolve()):
        runtime.cleanup()
        raise AssertionError("temporary Runtime subject must be outside the repository")
    evaluation_context = None
    try:
        _build_runtime_subject(subject)
        lightweight = subprocess.run(
            [
                sys.executable,
                "scripts/eval-agent-lightweight.py",
                "--reports-dir",
                str(subject / "reports"),
            ],
            cwd=subject,
            text=True,
            capture_output=True,
            check=False,
        )
        if lightweight.returncode != 0:
            raise AssertionError(
                "temporary lightweight prerequisite failed:\n"
                f"stdout:\n{lightweight.stdout}\n"
                f"stderr:\n{lightweight.stderr}"
            )
        evaluation_context = EVAL._subject_configuration(
            subject,
            subject / "evals/agent-light-trajectories/cases.yaml",
            subject / "reports/hookless-control-plane-eval.json",
        )
        evaluation_context.__enter__()
        ROOT = subject
    except BaseException:
        if evaluation_context is not None:
            evaluation_context.__exit__(*sys.exc_info())
        runtime.cleanup()
        raise

    def cleanup() -> None:
        global ROOT
        ROOT = SOURCE_ROOT
        evaluation_context.__exit__(None, None, None)
        runtime.cleanup()

    unittest.addModuleCleanup(cleanup)


AUTHORITATIVE_DAG_INPUTS = [
    "Accepted, artifact-reviewed authoritative Task DAG and downstream "
    "Task Capsule",
    "Current source, tests, routed Professional Skill, and named Layer 3 "
    "guidance",
]
AUTHORITATIVE_DAG_EVIDENCE_BY_CASE = {
    "isolated-write-parallel-contract": (
        "Accepted, artifact-reviewed authoritative Task DAG selects three "
        "downstream integration tasks and final review."
    ),
    "shared-workspace-serial-write": (
        "Accepted, artifact-reviewed authoritative Task DAG selects two "
        "serialized downstream tasks and final review."
    ),
}
AUTHORITATIVE_DAG_NODES = {
    ("isolated-write-parallel-contract", 2): (
        "implementation-task",
        "Accepted authoritative Task DAG node and engineering-artifact-review "
        "pass.",
    ),
    ("isolated-write-parallel-contract", 3): (
        "implementation-task",
        "Accepted authoritative Task DAG node and engineering-artifact-review "
        "pass.",
    ),
    ("isolated-write-parallel-contract", 20): (
        "integration-task",
        "Completed authoritative Task DAG predecessor outputs and their "
        "current evidence.",
    ),
    ("shared-workspace-serial-write", 2): (
        "implementation-task",
        "Accepted authoritative Task DAG node and engineering-artifact-review "
        "pass.",
    ),
    ("shared-workspace-serial-write", 12): (
        "implementation-task",
        "Accepted authoritative Task DAG dependency plus completed predecessor "
        "output and current evidence.",
    ),
}

_DOMINANCE_MEMBER_KINDS = (
    "professional",
    "layer3",
    "active_reference",
)


def _dominance_membership_sha256(members: list[str]) -> str:
    return hashlib.sha256(
        json.dumps(
            members,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _dominance_member_maxima(
    records: object,
    *,
    member_kind: str,
    placement: str,
) -> dict[str, int]:
    if not isinstance(records, list):
        raise ValueError(f"{placement} {member_kind} records are invalid")
    maxima: dict[str, int] = {}
    ordered_members: list[str] = []
    expected_fields = (
        {
            "member",
            "maximum_tokens",
            "canonical_reduction_key_sha256",
            "render_signature_sha256",
        }
        if placement == "frontier"
        else {"member", "maximum_tokens"}
    )
    for record in records:
        if not isinstance(record, dict) or set(record) != expected_fields:
            raise ValueError(f"{placement} {member_kind} witness schema is invalid")
        member = record.get("member")
        maximum_tokens = record.get("maximum_tokens")
        if not isinstance(member, str) or not member:
            raise ValueError(f"{placement} {member_kind} member is invalid")
        if (
            not isinstance(maximum_tokens, int)
            or isinstance(maximum_tokens, bool)
            or maximum_tokens < 0
        ):
            raise ValueError(f"{placement} {member_kind} maximum is invalid")
        if member in maxima:
            raise ValueError(f"{placement} {member_kind} duplicate member")
        if placement == "frontier" and any(
            re.fullmatch(r"[0-9a-f]{64}", str(record[field])) is None
            for field in (
                "canonical_reduction_key_sha256",
                "render_signature_sha256",
            )
        ):
            raise ValueError(f"{placement} {member_kind} witness hash is invalid")
        ordered_members.append(member)
        maxima[member] = maximum_tokens
    if ordered_members != sorted(ordered_members):
        raise ValueError(f"{placement} {member_kind} members are not sorted")
    return maxima


def _reconstruct_budget_dominance_relation(row: object) -> dict[str, object]:
    if not isinstance(row, dict):
        raise ValueError("dominance budget row is invalid")
    soft_target = row.get("soft_target")
    if not isinstance(soft_target, int) or isinstance(soft_target, bool):
        raise ValueError("dominance soft target is invalid")
    frontier_counts = row.get("frontier_counts")
    outside_counts = row.get("outside_counts")
    frontier_witnesses = row.get("frontier_witnesses")
    outside = row.get("outside")
    for name, value in (
        ("frontier_counts", frontier_counts),
        ("outside_counts", outside_counts),
        ("frontier_witnesses", frontier_witnesses),
        ("outside", outside),
    ):
        if not isinstance(value, dict) or set(value) != set(_DOMINANCE_MEMBER_KINDS):
            raise ValueError(f"dominance {name} member set is invalid")

    frontier: dict[str, list[str]] = {}
    safe_complement: dict[str, list[str]] = {}
    universe: dict[str, list[str]] = {}
    maxima: dict[str, dict[str, int]] = {}
    for member_kind in _DOMINANCE_MEMBER_KINDS:
        frontier_maxima = _dominance_member_maxima(
            frontier_witnesses[member_kind],
            member_kind=member_kind,
            placement="frontier",
        )
        outside_maxima = _dominance_member_maxima(
            outside[member_kind],
            member_kind=member_kind,
            placement="outside",
        )
        if frontier_counts[member_kind] != len(frontier_maxima):
            raise ValueError(f"frontier {member_kind} count mismatch")
        if outside_counts[member_kind] != len(outside_maxima):
            raise ValueError(f"outside {member_kind} count mismatch")
        overlap = set(frontier_maxima) & set(outside_maxima)
        if overlap:
            raise ValueError(f"{member_kind} duplicate member across placements")
        if any(value <= soft_target for value in frontier_maxima.values()):
            raise ValueError(f"frontier {member_kind} member is on the wrong side")
        if any(value > soft_target for value in outside_maxima.values()):
            raise ValueError(f"outside {member_kind} member is on the wrong side")
        combined = {**frontier_maxima, **outside_maxima}
        frontier[member_kind] = sorted(frontier_maxima)
        safe_complement[member_kind] = sorted(outside_maxima)
        universe[member_kind] = sorted(combined)
        maxima[member_kind] = combined
    return {
        "soft_target": soft_target,
        "frontier": frontier,
        "safe_complement": safe_complement,
        "universe": universe,
        "maxima": maxima,
    }


def _reconstruct_global_dominance_relation(
    task_relation: object,
    review_relation: object,
    projected: object,
) -> dict[str, object]:
    if not isinstance(task_relation, dict) or not isinstance(review_relation, dict):
        raise ValueError("budget dominance relation is invalid")
    if not isinstance(projected, dict):
        raise ValueError("global dominance projection is invalid")
    expected_projection_fields = {
        "frontier_counts",
        "frontier",
        "safe_complement_counts",
        "safe_complement",
    }
    if set(projected) != expected_projection_fields:
        raise ValueError("global dominance projection schema is invalid")
    for field in expected_projection_fields:
        value = projected[field]
        if not isinstance(value, dict) or set(value) != set(_DOMINANCE_MEMBER_KINDS):
            raise ValueError(f"global {field} member set is invalid")

    reconstructed_frontier: dict[str, list[str]] = {}
    reconstructed_complement: dict[str, list[str]] = {}
    reconstructed_universe: dict[str, list[str]] = {}
    projected_digests: dict[str, str] = {}
    reconstructed_digests: dict[str, str] = {}
    for member_kind in _DOMINANCE_MEMBER_KINDS:
        universe = sorted(
            set(task_relation["universe"][member_kind])
            | set(review_relation["universe"][member_kind])
        )
        frontier = sorted(
            set(task_relation["frontier"][member_kind])
            | set(review_relation["frontier"][member_kind])
        )
        complement = sorted(set(universe) - set(frontier))
        projected_frontier = projected["frontier"][member_kind]
        projected_complement = projected["safe_complement"][member_kind]
        if not isinstance(projected_frontier, list) or not isinstance(
            projected_complement, list
        ):
            raise ValueError(f"global {member_kind} lists are invalid")
        if projected_frontier != sorted(projected_frontier) or projected_complement != sorted(
            projected_complement
        ):
            raise ValueError(f"global {member_kind} lists are not sorted")
        if len(projected_frontier) != len(set(projected_frontier)) or len(
            projected_complement
        ) != len(set(projected_complement)):
            raise ValueError(f"global {member_kind} list contains duplicate member")
        if projected["frontier_counts"][member_kind] != len(projected_frontier):
            raise ValueError(f"global frontier {member_kind} count mismatch")
        if projected["safe_complement_counts"][member_kind] != len(
            projected_complement
        ):
            raise ValueError(f"global complement {member_kind} count mismatch")
        if set(projected_frontier) & set(projected_complement):
            raise ValueError(f"global {member_kind} overlap")
        if set(projected_frontier) | set(projected_complement) != set(universe):
            raise ValueError(f"global {member_kind} is nonexhaustive")
        reconstructed_frontier[member_kind] = frontier
        reconstructed_complement[member_kind] = complement
        reconstructed_universe[member_kind] = universe
        for placement, expected, actual in (
            ("frontier", frontier, projected_frontier),
            ("safe_complement", complement, projected_complement),
        ):
            key = f"{placement}_{member_kind}"
            reconstructed_digests[key] = _dominance_membership_sha256(expected)
            projected_digests[key] = _dominance_membership_sha256(actual)
    if projected_digests != reconstructed_digests:
        raise ValueError("global membership digest/list mismatch")
    return {
        "frontier": reconstructed_frontier,
        "safe_complement": reconstructed_complement,
        "universe": reconstructed_universe,
        "membership_sha256": reconstructed_digests,
    }


class RenderedContextBudgetTests(unittest.TestCase):
    def _assert_canonical_runtime_receipt(self, receipt: dict[str, object]) -> None:
        manifest = json.loads(
            (
                ROOT
                / "dist/universal/skills/recommended/"
                / ".changeforge-build-manifest.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            EVAL.runtime_asset_build_identity(
                manifest["authoritative_build_inputs"]["sha256"]
            ),
            receipt["build"],
        )
        self.assertEqual([], EVAL.layer3_selector_runtime_selection_receipt_errors(
            receipt, expected_owner=receipt["selection_owner"], expected_profile=receipt["profile"],
            expected_professional=receipt["professional_skill"], expected_selection_kind=receipt["selection_kind"],
            expected_selected_layer3=receipt["selected_layer3"], expected_build_identity=receipt["build"],
        ))

    def _assert_semantic_budget_witness(
        self,
        components: list[dict[str, object]],
        *,
        budget_class: str,
        expected_components: list[tuple[str, str]],
    ) -> dict[str, object]:
        self.assertEqual(
            expected_components,
            [(str(item["kind"]), str(item["path"])) for item in components],
        )
        self.assertTrue(all(str(item["_text"]).strip() for item in components))
        measurement = EVAL._measure_context(
            components,
            budget_class=budget_class,
        )
        self.assertEqual(
            sum(int(item["tokens"]) for item in components),
            measurement["sum_component_tokens"],
        )
        self.assertEqual(
            EVAL.count_o200k_base_tokens(
                "\n\n".join(str(item["_text"]).rstrip() for item in components)
            ),
            measurement["total_tokens"],
        )
        limits = EVAL.CONTEXT_BUDGET_LIMITS[budget_class]
        self.assertEqual(limits["soft_target"], measurement["soft_target"])
        self.assertEqual(limits["hard_ceiling"], measurement["hard_ceiling"])
        self.assertTrue(measurement["within_hard_ceiling"])
        self.assertLessEqual(measurement["total_tokens"], limits["hard_ceiling"])
        return measurement

    @staticmethod
    def _native_dispatch_probe() -> tuple[dict[str, object], dict[str, object]]:
        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        case = copy.deepcopy(
            next(item for item in document["cases"] if item["id"] == "single-module-feature")
        )
        runtime_manifest = json.loads(
            (
                ROOT
                / "dist/universal/skills"
                / EVAL.RUNTIME_NAME
                / ".changeforge-build-manifest.json"
            ).read_text(encoding="utf-8")
        )
        return case, runtime_manifest

    @staticmethod
    def _copy_native_dispatch_subject(
        target: Path, primary: str, step: dict[str, object]
    ) -> None:
        for host, relative in {
            "codex": "dist/codex/project/.codex/agents/main-control-agent.toml",
            "claude": "dist/claude/project/.claude/agents/main-control-agent.md",
            "copilot": "dist/copilot/project/.github/agents/main-control-agent.agent.md",
        }.items():
            del host
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, destination)
        common = (
            "engineering-control-plane/SKILL.md",
            "engineering-control-plane/references/professional-skill-router.md",
        )
        for relative in common:
            destination = target / "dist/universal/skills/recommended" / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(
                ROOT / "dist/universal/skills/recommended" / relative,
                destination,
            )
        router_source = (
            "src/control-skills/engineering-control-plane/references/"
            "professional-skill-router.md"
        )
        router_destination = target / router_source
        router_destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / router_source, router_destination)
        runtime_source = (
            ROOT
            / "dist/universal/skills/recommended"
            / primary
            / "references/runtime"
        )
        runtime_destination = (
            target
            / "dist/universal/skills/recommended"
            / primary
            / "references/runtime"
        )
        shutil.copytree(runtime_source, runtime_destination, dirs_exist_ok=True)
        professional_source = (
            ROOT / "dist/universal/skills/recommended" / primary / "SKILL.md"
        )
        professional_destination = (
            target / "dist/universal/skills/recommended" / primary / "SKILL.md"
        )
        professional_destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(professional_source, professional_destination)
        relative = (
            f"dist/universal/skills/{EVAL.RUNTIME_NAME}/"
            ".changeforge-build-manifest.json"
        )
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
        for name in (
            "professional-skills.yaml",
            "foundation-skills.yaml",
            "domain-skills.yaml",
            "release-routing-scenarios.yaml",
        ):
            relative = f"src/registry/{name}"
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, destination)
        fixture_relative = "evals/agent-light-trajectories/cases.yaml"
        fixture_destination = target / fixture_relative
        fixture_destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / fixture_relative, fixture_destination)
        reference_paths = [
            str(path) for path in step.get("professional_references", [])
        ]
        reference_paths.extend(
            str(record_path) for record_path in step.get("layer3_references", [])
        )
        for record_path in reference_paths:
            binding, _owner, _source_path = EVAL._runtime_reference_native_binding(
                ROOT,
                primary,
                record_path,
            )
            source = ROOT / binding["physical_path"]
            destination = target / binding["physical_path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

    @staticmethod
    def _write_legacy_native_selector(
        target: Path,
        primary: str,
        release_scenario: dict[str, object],
    ) -> Path:
        runtime_root = (
            target
            / "dist/universal/skills/recommended"
            / primary
            / "references/runtime"
        )
        selector = json.loads((runtime_root / "selector.json").read_text(encoding="utf-8"))
        selector.pop("build")
        for decision in selector["decisions"]:
            decision["provenance"]["release_scenario"] = copy.deepcopy(
                release_scenario
            )
        legacy_path = (
            target
            / "dist/universal/skills/recommended/engineering-control-plane/"
            "references/selectors"
            / f"{primary}.json"
        )
        legacy_path.parent.mkdir(parents=True, exist_ok=True)
        legacy_path.write_text(
            json.dumps(
                selector,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        for binding in [*selector["decisions"], selector["complete"]]:
            source = runtime_root / binding["path"]
            destination = legacy_path.parent / binding["path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        return legacy_path























    _admissible_report_cache: dict[str, object] | None = None

    @classmethod
    def _admissible_report(cls) -> dict[str, object]:
        if cls._admissible_report_cache is None:
            cls._admissible_report_cache = EVAL.evaluate()[
                "admissible_context_compositions"
            ]
        return cls._admissible_report_cache




    def test_route_obligation_pressure_is_named_and_fails_closed(self) -> None:
        obligations = {
            "primary_professional_skill": "quality-test-gate",
            "implementation_layer3": ["regression-testing"],
            "domain": ["bigdata-product-extension"],
            "required_review_skills": ["ai-code-review-refactor"],
        }
        budget = EVAL.CONTEXT_BUDGET_LIMITS["task"]["hard_ceiling"]
        components = [
            EVAL._component(
                "route-obligations",
                "decision-eval/route-obligations.json",
                json.dumps(obligations, sort_keys=True),
            ),
            EVAL._component(
                "pressure",
                "decision-eval/token-pressure.txt",
                "overflow-pressure-evidence " * (budget * 2),
            ),
        ]
        result = EVAL.evaluate_route_obligation_context(
            components,
            required_route_obligations=obligations,
            budget_class="task",
        )
        self.assertEqual("context-token-budget-overflow", result["failure_id"])
        self.assertEqual("fail-closed", result["outcome"])
        self.assertFalse(result["continue_allowed"])
        self.assertTrue(result["route_obligations_preserved"])

        dropped = copy.deepcopy(obligations)
        dropped["implementation_layer3"] = []
        mismatch = EVAL.evaluate_route_obligation_context(
            [
                EVAL._component(
                    "route-obligations",
                    "decision-eval/route-obligations.json",
                    json.dumps(dropped, sort_keys=True),
                )
            ],
            required_route_obligations=obligations,
            budget_class="task",
        )
        self.assertEqual("context-route-obligation-mismatch", mismatch["failure_id"])
        self.assertEqual("fail-closed", mismatch["outcome"])
        self.assertFalse(mismatch["continue_allowed"])

    def test_budget_taxonomy_and_limits_come_only_from_core(self) -> None:
        contract = EVAL.CONTEXT_BUDGET_MODEL
        self.assertEqual(3, contract["schema_version"])
        self.assertEqual(
            {
                "authoring",
                "resident_runtime",
                "dispatch_composition",
                "runtime_dynamic_context",
            },
            set(contract["context_taxonomy"]),
        )
        self.assertEqual(
            [
                "main_prompt",
                "control_skill",
                "professional_skill",
                "foundation",
                "domain",
            ],
            contract["context_taxonomy"]["authoring"]["classes"],
        )
        dynamic = contract["context_taxonomy"]["runtime_dynamic_context"]
        self.assertTrue(dynamic["observation_only"])
        self.assertTrue(dynamic["host_compaction_out_of_scope"])
        self.assertEqual(
            {
                key: (
                    value["soft_target"],
                    value["hard_ceiling"],
                    value["calibration_status"],
                )
                for key, value in contract["budget_classes"].items()
            },
            {
                key: (
                    value["soft_target"],
                    value["hard_ceiling"],
                    value["calibration_status"],
                )
                for key, value in EVAL.CONTEXT_BUDGET_LIMITS.items()
            },
        )
        for source in contract["budget_classes"].values():
            self.assertEqual("provisional-migration-value", source["calibration_status"])
            self.assertNotIn("capacity_ceiling", source)
            self.assertNotIn("minimum_headroom_ratio", source)
            self.assertNotIn("minimum_release_margin_tokens", source)
        self.assertEqual(
            EVAL.CONTEXT_BUDGET_MODEL["duplicate_rule_token_ratio_max"],
            EVAL.DUPLICATE_TOKEN_RATIO_MAX,
        )

        measurement = EVAL._measure_context(
            [EVAL._component("synthetic", "synthetic.md", "bounded context")],
            budget_class="main",
        )
        measurement.update({"host": "test", "runtime": "test"})
        maximum = EVAL._maximum_summary(measurement, include_dispatch=False)
        assert maximum is not None
        self.assertEqual(
            contract["budget_classes"]["main"]["soft_target"],
            maximum["soft_target"],
        )
        self.assertEqual(
            contract["budget_classes"]["main"]["hard_ceiling"],
            maximum["hard_ceiling"],
        )
        self.assertEqual(
            maximum["soft_target"] - maximum["tokens"],
            maximum["soft_margin_tokens"],
        )
        self.assertEqual(
            maximum["hard_ceiling"] - maximum["tokens"],
            maximum["hard_margin_tokens"],
        )

    def test_budget_contract_rejects_incomplete_or_reversed_limits(self) -> None:
        mutations = []
        missing = copy.deepcopy(EVAL.CONTEXT_BUDGET_MODEL)
        del missing["budget_classes"]["main"]["soft_target"]
        mutations.append(missing)
        wrong_type = copy.deepcopy(EVAL.CONTEXT_BUDGET_MODEL)
        wrong_type["budget_classes"]["main"]["hard_ceiling"] = True
        mutations.append(wrong_type)
        reversed_limits = copy.deepcopy(EVAL.CONTEXT_BUDGET_MODEL)
        reversed_limits["budget_classes"]["main"]["soft_target"] = (
            reversed_limits["budget_classes"]["main"]["hard_ceiling"]
        )
        mutations.append(reversed_limits)

        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    EVAL.derived_context_budget_limits(mutation)

    def test_soft_overage_is_advisory_and_hard_overage_fails_conformance(self) -> None:
        limits = EVAL.CONTEXT_BUDGET_LIMITS["task"]
        for tokens, expected in (
            (limits["soft_target"], (True, True, None)),
            (limits["soft_target"] + 1, (False, True, "growth-advisory")),
            (limits["hard_ceiling"] + 1, (False, False, "hard-ceiling-exceeded")),
        ):
            with self.subTest(tokens=tokens), mock.patch.object(
                EVAL, "count_o200k_base_tokens", return_value=tokens
            ):
                measurement = EVAL._measure_context(
                    [EVAL._component("synthetic", "synthetic.md", "context")],
                    budget_class="task",
                )
            self.assertEqual(expected[0], measurement["within_soft_target"])
            self.assertEqual(expected[1], measurement["within_hard_ceiling"])
            self.assertEqual(expected[2], measurement["budget_signal"])

    def test_calibration_distribution_is_nearest_rank_and_budget_independent(self) -> None:
        contract = EVAL.CONTEXT_BUDGET_MODEL
        mutated = copy.deepcopy(contract)
        mutated["budget_classes"]["task"]["soft_target"] = 1
        mutated["budget_classes"]["task"]["hard_ceiling"] = 2
        values = [10, 20, 30, 40, 50]
        self.assertEqual(
            {
                "count": 5,
                "p50": 30,
                "p90": 50,
                "p95": 50,
                "p99": 50,
                "max": 50,
            },
            EVAL._token_distribution(values),
        )
        self.assertEqual(
            EVAL._calibration_selection_identity(values, contract),
            EVAL._calibration_selection_identity(values, mutated),
        )
        args = EVAL._args(["--mode", "calibration", "--reports-dir", "/tmp/reports"])
        self.assertEqual("calibration", args.mode)

    def test_selection_identity_binds_candidates_not_distribution_summaries(self) -> None:
        admissible_values = [10, 20, 30, 40, 50, 60]

        def admissible(mapping_digest: str) -> dict[str, object]:
            return {
                "dominance_frontier": {
                    "mapping_digest": mapping_digest,
                    "mapping_row_count": len(admissible_values)
                    * len(EVAL.ADMISSIBLE_BUDGET_CLASSES),
                    "budget_classes": {
                        budget_class: {
                            "token_distribution": EVAL._token_distribution(
                                admissible_values
                            )
                        }
                        for budget_class in EVAL.ADMISSIBLE_BUDGET_CLASSES
                    },
                },
                "max_by_budget_class": {
                    budget_class: {"tokens": max(admissible_values)}
                    for budget_class in EVAL.ADMISSIBLE_BUDGET_CLASSES
                },
            }

        def report(
            *,
            mapping_digest: str,
            main_tokens: list[int],
        ) -> dict[str, object]:
            def component(kind: str, path: str, tokens: int) -> dict[str, object]:
                return {
                    "kind": kind,
                    "path": path,
                    "sha256": hashlib.sha256(path.encode("utf-8")).hexdigest(),
                    "tokens": tokens,
                }

            return EVAL._budget_governance_report(
                mode="calibration",
                main_contexts=[
                    {
                        "budget_class": "main",
                        "host": f"host-{index}",
                        "runtime": "recommended",
                        "components": [
                            component("rendered_main_profile", f"main-{index}", tokens)
                        ],
                        "total_tokens": tokens,
                    }
                    for index, tokens in enumerate(main_tokens)
                ],
                dispatch_measurements=[
                    {
                        "budget_class": "utility",
                        "host": "codex",
                        "runtime": "recommended",
                        "step": index,
                        "role": "task-agent",
                        "mode": "utility",
                        "primary_skill": None,
                        "layer3_skills": [],
                        "layer3_references": [],
                        "professional_references": [],
                        "canonical_capsule_sha256": f"capsule-{index}",
                        "components": [
                            component("dispatch_assignment", f"utility-{index}", tokens)
                        ],
                        "total_tokens": tokens,
                    }
                    for index, tokens in enumerate(main_tokens)
                ],
                admissible_context_compositions=admissible(mapping_digest),
            )

        baseline_tokens = [1, 2, 3, 4, 5, 6]
        changed_internal_tokens = [0, 1, 3, 4, 5, 6]
        self.assertEqual(
            EVAL._token_distribution(baseline_tokens),
            EVAL._token_distribution(changed_internal_tokens),
        )
        baseline = report(mapping_digest="a" * 64, main_tokens=baseline_tokens)
        changed_members = report(
            mapping_digest="b" * 64,
            main_tokens=baseline_tokens,
        )
        changed_internal_rows = report(
            mapping_digest="a" * 64,
            main_tokens=changed_internal_tokens,
        )
        baseline_identity = baseline["selection_contract"][
            "selection_identity_sha256"
        ]
        self.assertNotEqual(
            baseline_identity,
            changed_members["selection_contract"]["selection_identity_sha256"],
        )
        self.assertNotEqual(
            baseline_identity,
            changed_internal_rows["selection_contract"][
                "selection_identity_sha256"
            ],
        )

    def test_calibration_keeps_above_hard_candidates_without_changing_selection(self) -> None:
        tokens_by_class = {
            budget_class: 1 for budget_class in EVAL.CONTEXT_BUDGET_LIMITS
        }
        tokens_by_class["task"] = (
            EVAL.CONTEXT_BUDGET_LIMITS["task"]["hard_ceiling"] + 1
        )
        admissible = {
            "dominance_frontier": {
                "mapping_digest": "0" * 64,
                "mapping_row_count": len(EVAL.ADMISSIBLE_BUDGET_CLASSES),
                "budget_classes": {
                    budget_class: {
                        "token_distribution": EVAL._token_distribution(
                            [tokens_by_class[budget_class]]
                        )
                    }
                    for budget_class in EVAL.ADMISSIBLE_BUDGET_CLASSES
                }
            },
            "max_by_budget_class": {
                budget_class: {"tokens": tokens_by_class[budget_class]}
                for budget_class in EVAL.ADMISSIBLE_BUDGET_CLASSES
            },
        }
        kwargs = {
            "main_contexts": [
                {
                    "budget_class": "main",
                    "host": "codex",
                    "runtime": "recommended",
                    "components": [
                        {
                            "kind": "rendered_main_profile",
                            "path": "main",
                            "sha256": "1" * 64,
                            "tokens": tokens_by_class["main"],
                        }
                    ],
                    "total_tokens": tokens_by_class["main"],
                }
            ],
            "dispatch_measurements": [
                {
                    "budget_class": "utility",
                    "host": "codex",
                    "runtime": "recommended",
                    "step": 1,
                    "role": "task-agent",
                    "mode": "utility",
                    "primary_skill": None,
                    "layer3_skills": [],
                    "layer3_references": [],
                    "professional_references": [],
                    "canonical_capsule_sha256": "2" * 64,
                    "components": [
                        {
                            "kind": "dispatch_assignment",
                            "path": "utility",
                            "sha256": "3" * 64,
                            "tokens": tokens_by_class["utility"],
                        }
                    ],
                    "total_tokens": tokens_by_class["utility"],
                }
            ],
            "admissible_context_compositions": admissible,
        }

        calibration = EVAL._budget_governance_report(mode="calibration", **kwargs)
        conformance = EVAL._budget_governance_report(mode="conformance", **kwargs)

        self.assertEqual(
            tokens_by_class["task"], calibration["distributions"]["task"]["max"]
        )
        self.assertEqual([], calibration["conformance_failures"])
        self.assertEqual(1, len(calibration["hard_ceiling_overages"]))
        self.assertEqual(
            calibration["selection_contract"]["selection_count"],
            conformance["selection_contract"]["selection_count"],
        )
        self.assertEqual(
            calibration["selection_contract"]["selection_identity_sha256"],
            conformance["selection_contract"]["selection_identity_sha256"],
        )
        self.assertEqual(
            calibration["hard_ceiling_overages"],
            conformance["conformance_failures"],
        )




    def test_layer3_runtime_reference_record_path_safety(self) -> None:
        self.assertEqual(
            "references/layer3/transaction-consistency/references/evidence-patterns.md",
            runtime_layer3_reference_path(
                "references/layer3/transaction-consistency/references/evidence-patterns.md"
            ),
        )
        invalid = (
            "/references/layer3/transaction-consistency/references/evidence-patterns.md",
            "references\\layer3\\transaction-consistency\\references\\evidence-patterns.md",
            "../references/layer3/transaction-consistency/references/evidence-patterns.md",
            "references/layer3/transaction-consistency/./evidence-patterns.md",
            "references/layer3/transaction-consistency/references/index.md",
            "references/layer3/transaction-consistency/references/catalog.md",
            "references/layer3/transaction-consistency/references/evidence-patterns.md?raw=1",
            "references/layer3/transaction-consistency/references/evidence-patterns.md#section",
            "references/layer3/transaction-consistency/references/*.md",
            "references/layer3/transaction-consistency/references/nested/evidence-patterns.md",
            "transaction-consistency/references/evidence-patterns.md",
        )
        for record_path in invalid:
            with self.subTest(record_path=record_path):
                with self.assertRaises(FixtureCapsuleError):
                    runtime_layer3_reference_path(record_path)

    def test_duplicate_blocks_count_only_extra_cross_component_copy(self) -> None:
        repeated = (
            "Never preload Layer 3 guidance or open a generated index before the "
            "capsule names the exact task-relevant item."
        )
        components = [
            EVAL._component("one", "one.md", repeated),
            EVAL._component("two", "two.md", repeated),
            EVAL._component("three", "three.md", "A distinct short statement."),
        ]

        result = EVAL._duplicate_block_metrics(components)

        self.assertEqual(EVAL.count_o200k_base_tokens(repeated.casefold()), result["duplicate_rule_tokens"])
        self.assertEqual(1, len(result["duplicate_blocks"]))
        self.assertEqual(1, result["duplicate_blocks"][0]["extra_copy_count"])
        self.assertEqual(2, result["duplicate_blocks"][0]["occurrence_count"])
        self.assertEqual(2, len(result["duplicate_blocks"][0]["sources"]))

    def test_duplicate_blocks_count_extra_copy_inside_one_component(self) -> None:
        repeated = (
            "Never preload Layer 3 guidance or open a generated index before the "
            "capsule names the exact task-relevant item."
        )
        component = EVAL._component(
            "one",
            "one.md",
            f"{repeated}\n\n{repeated}\n",
        )

        result = EVAL._duplicate_block_metrics([component])

        self.assertEqual(
            EVAL.count_o200k_base_tokens(repeated.casefold()),
            result["duplicate_rule_tokens"],
        )
        self.assertEqual(2, result["duplicate_blocks"][0]["occurrence_count"])
        self.assertEqual(
            [{"component": "one:one.md", "occurrences": 2}],
            result["duplicate_blocks"][0]["sources"],
        )

    def test_duplicate_rule_p0_data_migration_witness_has_zero_layer3_control_copy(self) -> None:
        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        case = next(
            case
            for _group, case in EVAL._fixture_cases(document)
            if case["id"] == "data-migration"
        )
        dispatch_index, dispatch = next(
            (index, step)
            for index, step in enumerate(case["steps"])
            if step.get("action") == "dispatch"
        )
        self.assertEqual(
            ["data-migration-design", "transaction-consistency", "release-rollback"],
            dispatch["layer3_skills"],
        )
        self.assertEqual("task-agent", dispatch["profile"])
        self.assertEqual("data-middleware-change-builder", dispatch["primary_skill"])
        capsule = EVAL._component(
            "dispatch_assignment",
            f"fixture:data-migration:step:{dispatch_index}:canonical-capsule",
            EVAL.validate_and_render_fixture_capsule(dispatch),
        )
        foundation_items = {
            item.name: item
            for item in BUILD._load_items(
                "foundation", BUILD._load_registries()["foundation"]
            )
        }
        components = [
            EVAL._file_component(
                "worker_profile",
                ROOT / "dist/codex/project/.codex/agents/task-agent.toml",
            ),
            EVAL._file_component(
                "primary_skill",
                ROOT
                / "dist/universal/skills/recommended/"
                "data-middleware-change-builder/SKILL.md",
            ),
            *[
                EVAL._component(
                    "layer3",
                    f"source-projection:{name}",
                    BUILD._render_layer3_reference(
                        foundation_items[name],
                        EVAL.runtime_asset_build_identity(
                            json.loads(
                                (
                                    ROOT
                                    / "dist/universal/skills/recommended/"
                                    / ".changeforge-build-manifest.json"
                                ).read_text(encoding="utf-8")
                            )["authoritative_build_inputs"]["sha256"]
                        ),
                    ),
                )
                for name in dispatch["layer3_skills"]
            ],
            capsule,
        ]
        measurement = EVAL._measure_context(
            components,
            budget_class="task",
        )
        self.assertLessEqual(
            measurement["total_tokens"],
            EVAL.CONTEXT_BUDGET_LIMITS["task"]["hard_ceiling"],
        )
        self.assertEqual(0, measurement["duplicate_rule_tokens"])
        self.assertEqual(0.0, measurement["duplicate_rule_token_ratio"])
        self.assertEqual([], measurement["duplicate_blocks"])
        affected_family_ratios = []
        for name in (
            "data-migration-design",
            "release-rollback",
            "version-compatibility",
            "permission-boundary-modeling",
        ):
            family_components = [
                *components[:2],
                EVAL._component(
                    "layer3",
                    f"source-projection:{name}",
                    BUILD._render_layer3_reference(
                        foundation_items[name],
                        EVAL.runtime_asset_build_identity(
                            json.loads(
                                (
                                    ROOT
                                    / "dist/universal/skills/recommended/"
                                    / ".changeforge-build-manifest.json"
                                ).read_text(encoding="utf-8")
                            )["authoritative_build_inputs"]["sha256"]
                        ),
                    ),
                ),
                capsule,
            ]
            affected_family_ratios.append(
                EVAL._measure_context(
                    family_components,
                    budget_class="task",
                )["duplicate_rule_token_ratio"]
            )
        self.assertLess(max(affected_family_ratios), 0.01)












    @staticmethod
    def _ab_subject(total_tokens: int) -> dict[str, object]:
        fixed_component_tokens = {
            "always_loaded": 20,
            "dispatch_instructions": 10,
            "professional": 15,
            "layer3": 10,
            "selector": 5,
            "reference_partition": 0,
            "targeted_reference": 10,
        }
        transfer_tokens = total_tokens - sum(fixed_component_tokens.values())
        synthetic_transfer_components = {
            "task_capsule": transfer_tokens // 2,
            "implementation_handoff": transfer_tokens - transfer_tokens // 2,
        }
        component_tokens = {
            **fixed_component_tokens,
            "cross_agent_transfer": sum(synthetic_transfer_components.values()),
        }
        subject = {
            "identity": {
                "measurement_source": "isolated-built-subject",
                "evaluator_sha256": "1" * 64,
                "lightweight_evaluator_sha256": "8" * 64,
                "native_fixture_sha256": "2" * 64,
                "native_schema": {
                    "fixture_schema_version": 2,
                    "trajectory_case_count": 1,
                    "task_focus_case_count": 1,
                    "capsule_contracts": [],
                },
                "native_validator_sha256": "7" * 64,
                "canonical_corpus_digest": "9" * 64,
                "tokenizer": "o200k_base",
                "source_commit": "3" * 40,
                "authoritative_build_inputs": {"sha256": "4" * 64},
                "runtime_manifest": {
                    "runtime": EVAL.RUNTIME_NAME,
                    "sha256": "5" * 64,
                    "authoritative_build_inputs": {"sha256": "4" * 64},
                },
            },
            "cases": [
                {
                    "id": "measured-case",
                    "route_obligations": {
                        "professional": ["repository-tooling-change-builder"],
                        "layer3": ["targeted-validation-selection"],
                        "domain": [],
                        "review": ["quality-test-gate"],
                    },
                    "component_tokens": component_tokens,
                    "structural": {
                        "selector_load_count": 1,
                        "reference_partition_load_count": 0,
                        "envelope_count": 1,
                        "reference_load_count": 1,
                        "reference_tokens": 10,
                        "handoff_count": 1,
                        "handoff_tokens": component_tokens["cross_agent_transfer"],
                        "same_assignment_duplicate_read_count": 0,
                        "end_to_end_context_occurrence_count": 4,
                    },
                    "total_task_tokens": sum(component_tokens.values()),
                    "native_sources": {
                        "selection_authority_bundles": [
                            {
                                "schema": "combined-router/v1",
                                "effective_ordered_layer3": [
                                    "targeted-validation-selection"
                                ],
                            }
                        ]
                    },
                }
            ],
        }
        logical = subject["cases"][0]
        subject["cases"] = []
        for host in EVAL.FOCUS_PROFILE_HOSTS:
            row = copy.deepcopy(logical)
            row["id"] = f"measured-case::{host}"
            row["logical_case_id"] = "measured-case"
            row["host"] = host
            row["native_sources"]["selection_authority_bundles"][0]["host"] = host
            row["native_sources"]["components"] = []
            row["native_sources"]["selection_asset_component_tokens"] = {
                "always_loaded": 0,
                "selector": 0,
                "reference_partition": 0,
            }
            subject["cases"].append(row)
        subject["identity"].update(
            {
                "logical_case_count": 1,
                "host_pair_count": len(EVAL.FOCUS_PROFILE_HOSTS),
                "host_order": list(EVAL.FOCUS_PROFILE_HOSTS),
            }
        )
        return subject

    @staticmethod
    def _focus_row(case: dict[str, object], subject: str = "candidate") -> dict[str, object]:
        case_id = str(case["id"])
        return {
            "canonical_id": case_id,
            f"{subject}_native_id": case_id,
            f"{subject}_native_sha256": hashlib.sha256(
                json.dumps(
                    case,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest(),
            "state": "raw-route-equal",
            "semantic_obligation": EVAL._focus_semantic_obligation(case),
            "route_obligations": {
                "professional": [],
                "layer3": [],
                "domain": [],
                "review": [],
                "references": [],
                "not_applicable_basis": "task-focus case contains no Task dispatch",
            },
        }

    @staticmethod
    def _focus_case(scenario: str) -> dict[str, object]:
        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        return copy.deepcopy(
            next(
                case
                for case in document["task_focus_cases"]
                if case["scenario"] == scenario
            )
        )

    @staticmethod
    def _copy_focus_subject(target: Path) -> None:
        copied = (
            "src/control-model/core-contracts.json",
            "src/agent-profiles/role-agents.json",
            "src/control-skills/engineering-control-plane/references/implementation-handoff-template.md",
        )
        for relative in copied:
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((ROOT / relative).read_bytes())
        host_templates = {
            "codex": "dist/codex/project/.codex/agents/{role}.toml",
            "claude": "dist/claude/project/.claude/agents/{role}.md",
            "copilot": "dist/copilot/project/.github/agents/{role}.agent.md",
        }
        for role in (
            "main-control-agent",
            "analysis-agent",
            "task-agent",
            "review-agent",
        ):
            for host in EVAL.FOCUS_PROFILE_HOSTS:
                relative = host_templates[host].format(role=role)
                destination = target / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes((ROOT / relative).read_bytes())
        relative = (
            f"dist/universal/skills/{EVAL.RUNTIME_NAME}/"
            ".changeforge-build-manifest.json"
        )
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT / relative).read_bytes())








    @staticmethod
    def _quality_evidence(
        verdict: str,
        *,
        evidence_class: str = "live_agent",
        live_status: str = "collected",
        kind: str = "blind-old-new-agent-behavior",
    ) -> dict[str, object]:
        return {
            "evaluation_kind": kind,
            "evidence_class": evidence_class,
            "live_evidence_status": live_status,
            "verdict": verdict,
            "old": {"cost_metrics": {"tokens": 100, "turns": 2, "elapsed_ms": 50}},
            "new": {"cost_metrics": {"tokens": 75, "turns": 2, "elapsed_ms": 40}},
        }







    @staticmethod
    def _host_complete_ab_subject(total_tokens: int) -> dict[str, object]:
        return RenderedContextBudgetTests._ab_subject(total_tokens)

































    def test_layer3_resolution_follows_runtime_manifest(self) -> None:
        self.assertNotEqual(
            (SOURCE_ROOT / "dist").resolve(),
            (ROOT / "dist").resolve(),
        )
        self.assertEqual(
            (ROOT / "dist/universal/skills").resolve(),
            EVAL.DIST_SKILLS.resolve(),
        )
        errors: list[str] = []
        runtime_manifest = EVAL._load_runtime_manifest(errors)
        self.assertEqual([], errors)
        assert runtime_manifest is not None
        manifests = {EVAL.RUNTIME_NAME: runtime_manifest}

        def selector_reference_id(
            profile: str,
            primary: str,
            owner: str,
            decision_problem: str,
        ) -> str:
            partition = json.loads(
                (
                    EVAL.DIST_SKILLS
                    / profile
                    / primary
                    / "references/runtime/reference-records"
                    / f"{owner}.json"
                ).read_text(encoding="utf-8")
            )
            records = {
                json.dumps(record, sort_keys=True, separators=(",", ":"))
                for record in partition["reference_records"]
                if record.get("owner_skill") == owner
                and (record.get("context_admissibility") or {}).get(
                    "decision_problem"
                )
                == decision_problem
            }
            self.assertEqual(1, len(records))
            record = json.loads(records.pop())
            return str(record["path"])

        self.assertEqual(
            EVAL.COMPILED_LAYER3_FORMAT,
            runtime_manifest["compiled_layer3_format"],
        )
        recommended = EVAL._layer3_path(
            "recommended",
            "engineering-change-analysis",
            "failure-diagnosis",
            manifests["recommended"],
        )
        self.assertIn("references/layer3", recommended.as_posix())

        payment_references = {
            profile: selector_reference_id(
                profile,
                "engineering-change-analysis",
                "payment-trading-extension",
                "financial-role-and-state-authority",
            )
            for profile in (EVAL.RUNTIME_NAME,)
        }

        rows = (
            ("recommended", "engineering-change-analysis", "test-strategy", "references/layer3/test-strategy/references/checklist.md"),
            ("recommended", "engineering-change-analysis", "payment-trading-extension", payment_references["recommended"]),
            ("recommended", "high-risk-design-review", "module-boundary-design", "references/layer3/module-boundary-design/references/benchmarks-and-enforcement.md"),
            ("recommended", "security-privacy-gate", "web-security", "references/layer3/web-security/references/checklist.md"),
            ("recommended", "security-privacy-gate", "ai-product-extension", "references/layer3/ai-product-extension/references/checklist.md"),
            ("recommended", "backend-change-builder", "ai-product-extension", "references/layer3/ai-product-extension/references/checklist.md"),
            ("recommended", "frontend-change-builder", "ai-product-extension", "references/layer3/ai-product-extension/references/checklist.md"),
            ("recommended", "data-middleware-change-builder", "ai-product-extension", "references/layer3/ai-product-extension/references/checklist.md"),
            ("recommended", "integration-change-builder", "ai-product-extension", "references/layer3/ai-product-extension/references/checklist.md"),
            ("recommended", "installed-client-change-builder", "ai-product-extension", "references/layer3/ai-product-extension/references/checklist.md"),
            ("recommended", "ai-code-review-refactor", "ai-product-extension", "references/layer3/ai-product-extension/references/checklist.md"),
            ("recommended", "delivery-release-gate", "release-rollback", "references/layer3/release-rollback/references/benchmarks-and-patterns.md"),
            ("recommended", "delivery-release-gate", "release-rollback", "references/layer3/release-rollback/references/evidence-patterns.md"),
        )
        for profile, primary, owner, record_path in rows:
            with self.subTest(profile=profile, owner=owner):
                record, resolved = EVAL._runtime_reference_record_and_target(
                    EVAL.DIST_SKILLS / profile / primary,
                    primary,
                    record_path,
                )
                self.assertEqual(record_path, record["path"])
                self.assertEqual(
                    EVAL.DIST_SKILLS / profile / primary / record_path,
                    resolved,
                )
                self.assertTrue(resolved.is_file())

        foundation_id = "references/layer3/transaction-consistency/references/evidence-patterns.md"
        _record, recommended_nested = EVAL._runtime_reference_record_and_target(
            EVAL.DIST_SKILLS / "recommended" / "data-middleware-change-builder",
            "data-middleware-change-builder",
            foundation_id,
        )
        self.assertIn("references/layer3/transaction-consistency", recommended_nested.as_posix())

        domain_ids = {
            profile: selector_reference_id(
                profile,
                "data-middleware-change-builder",
                "bigdata-product-extension",
                "consumer-and-schema-contracts",
            )
            for profile in (EVAL.RUNTIME_NAME,)
        }
        _record, recommended_domain = EVAL._runtime_reference_record_and_target(
            EVAL.DIST_SKILLS / "recommended" / "data-middleware-change-builder",
            "data-middleware-change-builder",
            domain_ids["recommended"],
        )
        self.assertIn("references/layer3/bigdata-product-extension", recommended_domain.as_posix())
        self.assertTrue(recommended_domain.is_file())

    def test_task_context_loads_two_foundation_references_without_an_index(self) -> None:
        report = EVAL.evaluate()
        catalog = {item["id"]: item for item in report["component_catalog"]}
        foundation = EVAL.load_yaml_file(
            ROOT / "src/registry/foundation-skills.yaml"
        )
        foundation_names = {
            row["name"] for row in foundation["foundation_skills"]
        }
        case = next(
            item for item in report["cases"] if item["id"] == "release-rollback"
        )
        measurements = [
            item
            for item in case["measurements"]
            if item["role"] == "task-agent"
            and item["loaded_layer3_reference_count"] == 2
        ]
        self.assertEqual(3, len(measurements))
        for measurement in measurements:
            with self.subTest(
                host=measurement["host"],
                runtime_name=measurement["runtime"],
            ):
                logical_ids = measurement["loaded_layer3_reference_logical_ids"]
                self.assertEqual(2, len(logical_ids))
                self.assertTrue(
                    all(
                        Path(logical_id).parts[2] in foundation_names
                        for logical_id in logical_ids
                    )
                )
                nested = [
                    catalog[component_id]
                    for component_id in measurement["component_ids"]
                    if catalog[component_id]["kind"] == "layer3_reference"
                ]
                self.assertEqual(2, len(nested))
                self.assertEqual(2, len({item["path"] for item in nested}))
                self.assertTrue(
                    all(
                        not item["path"].endswith(("/index.md", "/catalog.md"))
                        for item in nested
                    )
                )

    def test_domain_root_and_checklist_use_runtime_compiled_delivery(self) -> None:
        report = EVAL.evaluate()
        catalog = {item["id"]: item for item in report["component_catalog"]}
        case = next(
            item
            for item in report["cases"]
            if item["id"] == "source-backed-payment-retry-proof"
        )
        measurements = [
            item
            for item in case["measurements"]
            if item["runtime"] == EVAL.RUNTIME_NAME
        ]
        self.assertEqual(len(EVAL.HOST_PROFILE_ROOTS), len(measurements))
        for measurement in measurements:
            with self.subTest(
                host=measurement["host"],
                runtime_name=measurement["runtime"],
            ):
                selected = [
                    catalog[component_id]
                    for component_id in measurement["component_ids"]
                ]
                domain_roots = [
                    item
                    for item in selected
                    if item["kind"] == "layer3"
                    and "payment-trading-extension" in item["path"]
                ]
                domain_checklists = [
                    item
                    for item in selected
                    if item["kind"] == "layer3_reference"
                    and item["path"].endswith(
                        "/payment-trading-extension/references/duplicate-financial-effect-control.md"
                    )
                ]
                self.assertEqual(1, len(domain_roots))
                self.assertEqual(1, len(domain_checklists))
                self.assertFalse(
                    any(item["path"].endswith("/index.md") for item in selected)
                )
                self.assertIn("/references/layer3/", domain_roots[0]["path"])
                self.assertIn(
                    "/references/layer3/", domain_checklists[0]["path"]
                )
                self.assertTrue(measurement["within_duplicate_budget"])

    def test_context_manifest_loader_requires_ai_consumption_format(self) -> None:
        self.assertEqual("recommended", EVAL.RUNTIME_NAME)
        self.assertFalse(hasattr(EVAL, "BUILD_PROFILES"))
        with tempfile.TemporaryDirectory() as raw:
            dist = Path(raw)
            profile_root = dist / "recommended"
            profile_root.mkdir(parents=True)
            manifest_path = profile_root / ".changeforge-build-manifest.json"
            for value in (None, "authoring-root-v1"):
                with self.subTest(value=value):
                    manifest = {"profile": "recommended"}
                    if value is not None:
                        manifest["compiled_layer3_format"] = value
                    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                    with mock.patch.object(EVAL, "DIST_SKILLS", dist):
                        errors: list[str] = []
                        runtime_manifest = EVAL._load_runtime_manifest(errors)
                    self.assertIsNone(runtime_manifest)
                    self.assertTrue(
                        any("compiled_layer3_format must equal" in error for error in errors),
                        errors,
                    )
        manifest = json.loads(
            (
                EVAL.DIST_SKILLS
                / EVAL.RUNTIME_NAME
                / ".changeforge-build-manifest.json"
            ).read_text(encoding="utf-8")
        )
        manifest["top_level_skills"].append(manifest["foundation_skills"][0])
        with tempfile.TemporaryDirectory() as raw:
            dist = Path(raw)
            runtime_root = dist / EVAL.RUNTIME_NAME
            runtime_root.mkdir(parents=True)
            (runtime_root / ".changeforge-build-manifest.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            with mock.patch.object(EVAL, "DIST_SKILLS", dist):
                errors = []
                runtime_manifest = EVAL._load_runtime_manifest(errors)
        self.assertIsNone(runtime_manifest)
        self.assertTrue(any("no Foundation or Domain" in error for error in errors))

    def test_layer3_skill_resolution_requires_exactly_one_delivery_path(self) -> None:
        base = {
            "compiled_layer3_references": {"primary": []},
            "top_level_skills": [],
        }
        with self.assertRaisesRegex(ValueError, "exactly one compiled or top-level"):
            EVAL._layer3_path("test", "primary", "owner", copy.deepcopy(base))

        dual = copy.deepcopy(base)
        dual["compiled_layer3_references"]["primary"] = ["owner"]
        dual["top_level_skills"] = ["owner"]
        with self.assertRaisesRegex(ValueError, "exactly one compiled or top-level"):
            EVAL._layer3_path("test", "primary", "owner", dual)

    def test_runtime_reference_resolution_uses_record_path_without_fallback(self) -> None:
        self.assertFalse(hasattr(EVAL, "_layer3_reference_path"))
        self.assertFalse(hasattr(EVAL, "_professional_reference_path"))
        record_path = "references/layer3/owner/references/checklist.md"
        with tempfile.TemporaryDirectory() as raw:
            professional_root = Path(raw) / "primary"
            partition_root = professional_root / "references/runtime/reference-records"
            partition_root.mkdir(parents=True)
            fallback = professional_root / "references/checklist.md"
            fallback.parent.mkdir(parents=True, exist_ok=True)
            fallback.write_text("must not be used\n", encoding="utf-8")
            record = {
                "context_admissibility": {
                    "decision_problem": "test",
                    "load_when": "test",
                    "do_not_load_when": "not test",
                    "required_output": "proof",
                },
                "do_not_load_when": "not test",
                "load_when": "test",
                "owner_layer": "foundation",
                "owner_skill": "owner",
                "path": record_path,
                "required_by": ["primary"],
                "required_output": "proof",
                "residency": "targeted",
                "type": "checklist",
            }
            (partition_root / "owner.json").write_text(
                json.dumps(
                    {
                        "professional_skill": "primary",
                        "owner_skill": "owner",
                        "reference_records": [record],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "missing regular file"):
                EVAL._runtime_reference_record_and_target(
                    professional_root,
                    "primary",
                    record_path,
                )

    def test_fixture_capsule_renderer_is_not_built(self) -> None:
        self.assertEqual(
            [],
            list((ROOT / "dist").rglob("fixture_capsule_contract.py")),
        )

    def test_admissible_composition_inventory_is_source_derived(self) -> None:
        composition = self._admissible_report()
        authority = EVAL._selector_authority()
        projections = EVAL.layer3_selector_control_projections(authority)

        self.assertEqual(
            "changeforge.admissible-context-composition-eval/v1",
            composition["contract"],
        )
        self.assertFalse(composition["parallel_catalog"])
        self.assertEqual(
            authority["inventory"],
            composition["selector_authority_inventory"],
        )
        self.assertEqual(len(projections), composition["inventory"]["professional_count"])
        self.assertEqual(
            sum(len(item["selection_surfaces"]) for item in projections.values()),
            composition["inventory"]["owner_surface_count"],
        )
        self.assertGreater(
            composition["inventory"]["legal_selection_equivalence_class_count"],
            composition["inventory"]["owner_surface_count"],
        )
        self.assertGreater(composition["inventory"]["positive_selector_case_count"], 0)
        self.assertEqual(
            composition["inventory"]["positive_selector_case_count"],
            composition["inventory"]["nearest_negative_case_count"],
        )
        self.assertGreater(composition["inventory"]["professional_reference_count"], 0)
        self.assertGreater(
            composition["inventory"]["professional_reference_conflict_count"],
            0,
        )
        self.assertGreater(composition["inventory"]["nested_reference_count"], 0)
        self.assertGreater(
            composition["inventory"]["legal_nested_reference_combination_count"],
            composition["inventory"]["nested_reference_count"],
        )
        self.assertGreater(composition["inventory"]["dominated_reference_subset_count"], 0)
        self.assertEqual(
            composition["inventory"]["candidate_composition_count"],
            composition["inventory"]["coverage_mapping_count"],
        )
        self.assertLess(
            composition["inventory"]["canonical_representative_count"],
            composition["inventory"]["coverage_mapping_count"],
        )
        self.assertLessEqual(
            composition["inventory"]["exact_measurement_count"],
            composition["inventory"]["canonical_representative_count"],
        )
        self.assertEqual(
            {
                "src/registry/professional-skills.yaml",
                "src/registry/foundation-skills.yaml",
                "src/registry/domain-skills.yaml",
            },
            set(composition["source_scope"]["registries"]),
        )

    def test_admissible_compositions_cover_required_owner_and_layer_shapes(self) -> None:
        composition = self._admissible_report()

        self.assertEqual(
            {
                "analysis_foundation_domain",
                "analyzed_task_three_layer3",
                "review_domain_foundation",
                "nested_targeted_references",
                "direct_main_owner",
                "initial_analysis_main_owner",
                "analyzed_brief_owner",
            },
            {
                key
                for key, covered in composition["required_coverage"].items()
                if covered
            },
        )
        self.assertEqual(
            {"0", "1", "2", "3"},
            {
                cardinality
                for cardinality, count in composition["inventory"][
                    "layer3_cardinality_counts"
                ].items()
                if count
            },
        )
        obligations = composition["obligation_preservation"]
        self.assertTrue(obligations["professional_preserved"])
        self.assertTrue(obligations["domain_authorization_preserved"])
        self.assertTrue(obligations["review_selection_independent"])
        self.assertTrue(obligations["receipts_replayed"])
        self.assertTrue(obligations["route_once_input_only"])
        self.assertTrue(obligations["staged_reference_obligations_preserved"])
        self.assertEqual(0, obligations["routing_classification_calls"])
        inventory = composition["inventory"]
        self.assertGreater(inventory["stage_measurement_count"], 0)
        self.assertGreater(inventory["valid_carried_predecessor_count"], 0)
        self.assertEqual(0, inventory["carrier_failure_count"])
        self.assertEqual(0, inventory["dropped_reference_obligation_count"])
        self.assertEqual(0, inventory["required_output_receipt_failure_count"])
        self.assertGreater(inventory["required_output_receipt_count"], 0)
        self.assertGreaterEqual(inventory["maximum_selected_reference_count"], 4)

    def test_admissible_compositions_fail_closed_without_truncation(self) -> None:
        forbidden = self._admissible_report()["forbidden_combinations"]

        self.assertEqual(3, forbidden["maximum_layer3"])
        self.assertGreater(forbidden["over_max_rejection_count"], 0)
        self.assertGreater(forbidden["unauthorized_exact_rejection_count"], 0)
        self.assertGreater(forbidden["duplicate_exact_rejection_count"], 0)
        self.assertEqual(0, forbidden["silent_truncation_count"])
        self.assertEqual(0, forbidden["nearest_negative_leak_count"])
        self.assertEqual(0, forbidden["reference_conflict_leak_count"])
        self.assertEqual(0, forbidden["index_or_catalog_load_count"])
        inventory = self._admissible_report()["inventory"]
        self.assertEqual(1, inventory["maximum_loaded_reference_count"])
        self.assertEqual(0, inventory["four_plus_reference_measurement_count"])
        self.assertGreaterEqual(inventory["maximum_selected_reference_count"], 4)
        self.assertEqual(0, inventory["path_excluded_composition_count"])
        self.assertEqual(
            "admissible-context-layer3-overflow",
            forbidden["overflow_failure_id"],
        )

    def test_admissible_composition_worst_cases_report_current_frontier(self) -> None:
        composition = self._admissible_report()
        targets = {
            budget_class: EVAL.CONTEXT_BUDGET_LIMITS[budget_class]["soft_target"]
            for budget_class in EVAL.ADMISSIBLE_BUDGET_CLASSES
        }

        for budget_class, target in targets.items():
            with self.subTest(budget_class=budget_class):
                maximum = composition["max_by_budget_class"][budget_class]
                self.assertEqual(
                    maximum["tokens"] <= target,
                    maximum["within_soft_target"],
                )
                self.assertEqual([], composition["errors"])
                self.assertTrue(maximum["route_obligations_preserved"])
                self.assertLessEqual(
                    len(maximum["stage_loaded_references"]), 1
                )
                self.assertFalse(
                    any(
                        path.endswith(("/index.md", "/catalog.md"))
                        for path in maximum["loaded_paths"]
                    )
                )

    def test_dominance_relation_oracle_rejects_counterfactuals(self) -> None:
        member_kinds = ("professional", "layer3", "active_reference")

        def witness(member: str, maximum_tokens: int) -> dict[str, object]:
            return {
                "member": member,
                "maximum_tokens": maximum_tokens,
                "canonical_reduction_key_sha256": "a" * 64,
                "render_signature_sha256": "b" * 64,
            }

        row = {
            "soft_target": 100,
            "frontier_counts": {kind: 2 for kind in member_kinds},
            "outside_counts": {kind: 2 for kind in member_kinds},
            "frontier_witnesses": {
                kind: [witness(f"{kind}-frontier-a", 101), witness(f"{kind}-frontier-b", 102)]
                for kind in member_kinds
            },
            "outside": {
                kind: [
                    {"member": f"{kind}-safe-a", "maximum_tokens": 99},
                    {"member": f"{kind}-safe-b", "maximum_tokens": 100},
                ]
                for kind in member_kinds
            },
        }
        relation = _reconstruct_budget_dominance_relation(row)
        projection = {
            "frontier_counts": {
                kind: len(relation["frontier"][kind]) for kind in member_kinds
            },
            "frontier": copy.deepcopy(relation["frontier"]),
            "safe_complement_counts": {
                kind: len(relation["safe_complement"][kind])
                for kind in member_kinds
            },
            "safe_complement": copy.deepcopy(relation["safe_complement"]),
        }
        _reconstruct_global_dominance_relation(relation, relation, projection)

        mutations: list[tuple[str, object, str]] = []
        deleted = copy.deepcopy(row)
        deleted["frontier_witnesses"]["professional"].pop()
        mutations.append(("delete", deleted, "count"))
        duplicate = copy.deepcopy(row)
        duplicate["outside"]["layer3"].append(
            copy.deepcopy(duplicate["outside"]["layer3"][0])
        )
        mutations.append(("duplicate", duplicate, "duplicate"))
        boundary = copy.deepcopy(row)
        boundary["frontier_witnesses"]["active_reference"][0]["maximum_tokens"] = 100
        mutations.append(("equal-target-frontier", boundary, "wrong side"))
        over_target = copy.deepcopy(row)
        over_target["outside"]["active_reference"][0]["maximum_tokens"] = 101
        mutations.append(("over-target-complement", over_target, "wrong side"))
        bad_witness = copy.deepcopy(row)
        bad_witness["frontier_witnesses"]["professional"][0][
            "canonical_reduction_key_sha256"
        ] = "invalid"
        mutations.append(("witness", bad_witness, "witness"))
        bad_count = copy.deepcopy(row)
        bad_count["outside_counts"]["professional"] = 3
        mutations.append(("count", bad_count, "count"))
        bad_member = copy.deepcopy(row)
        bad_member["outside"]["professional"][0]["member"] = ""
        mutations.append(("member", bad_member, "member"))
        for name, mutated, error in mutations:
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, error):
                _reconstruct_budget_dominance_relation(mutated)

        overlap = copy.deepcopy(projection)
        overlap["safe_complement"]["professional"].append(
            overlap["frontier"]["professional"][0]
        )
        overlap["safe_complement"]["professional"].sort()
        overlap["safe_complement_counts"]["professional"] += 1
        with self.assertRaisesRegex(ValueError, "overlap"):
            _reconstruct_global_dominance_relation(relation, relation, overlap)

        nonexhaustive = copy.deepcopy(projection)
        nonexhaustive["safe_complement"]["professional"].pop()
        nonexhaustive["safe_complement_counts"]["professional"] -= 1
        with self.assertRaisesRegex(ValueError, "nonexhaustive"):
            _reconstruct_global_dominance_relation(
                relation, relation, nonexhaustive
            )

        unsorted = copy.deepcopy(projection)
        unsorted["frontier"]["layer3"].reverse()
        with self.assertRaisesRegex(ValueError, "sorted"):
            _reconstruct_global_dominance_relation(relation, relation, unsorted)

        digest_mismatch = copy.deepcopy(projection)
        for placement_a, placement_b in (
            ("frontier", "safe_complement"),
        ):
            first = digest_mismatch[placement_a]["active_reference"].pop(0)
            second = digest_mismatch[placement_b]["active_reference"].pop(0)
            digest_mismatch[placement_a]["active_reference"].append(second)
            digest_mismatch[placement_b]["active_reference"].append(first)
            digest_mismatch[placement_a]["active_reference"].sort()
            digest_mismatch[placement_b]["active_reference"].sort()
        with self.assertRaisesRegex(ValueError, "digest/list mismatch"):
            _reconstruct_global_dominance_relation(
                relation, relation, digest_mismatch
            )

    def test_dominance_relation_test_is_not_an_authoritative_build_input(self) -> None:
        relative = Path("tests/scripts/test_eval_rendered_context_budget.py")
        workspace_before = (ROOT / relative).read_bytes()
        source_snapshot = VALIDATION.authoritative_build_input_snapshot(ROOT)
        with tempfile.TemporaryDirectory() as raw:
            subject = Path(raw) / "subject"
            for include_root in source_snapshot["include_roots"]:
                shutil.copytree(ROOT / include_root, subject / include_root)
            for include_file in source_snapshot["include_files"]:
                destination = subject / include_file
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / include_file, destination)
            target = subject / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(workspace_before)
            before = VALIDATION.authoritative_build_input_snapshot(subject)
            target.write_bytes(workspace_before + b"\n# temporary dominance oracle mutation\n")
            after = VALIDATION.authoritative_build_input_snapshot(subject)
            included = subject / source_snapshot["include_files"][0]
            included.write_bytes(included.read_bytes() + b"\n")
            included_after = VALIDATION.authoritative_build_input_snapshot(subject)

        identity_fields = (
            "schema_version",
            "kind",
            "algorithm",
            "record_format",
            "include_roots",
            "include_files",
            "exclusions",
            "file_count",
            "sha256",
        )
        self.assertEqual(
            {field: before[field] for field in identity_fields},
            {field: after[field] for field in identity_fields},
        )
        self.assertEqual(source_snapshot["sha256"], before["sha256"])
        self.assertEqual(
            VALIDATION.runtime_asset_build_identity(before["sha256"]),
            VALIDATION.runtime_asset_build_identity(after["sha256"]),
        )
        self.assertNotEqual(after["sha256"], included_after["sha256"])
        self.assertNotEqual(
            VALIDATION.runtime_asset_build_identity(after["sha256"]),
            VALIDATION.runtime_asset_build_identity(included_after["sha256"]),
        )
        relative_text = relative.as_posix()
        self.assertNotIn(relative_text, before["include_files"])
        self.assertFalse(
            any(
                relative_text == root or relative_text.startswith(f"{root}/")
                for root in before["include_roots"]
            )
        )
        self.assertEqual(workspace_before, (ROOT / relative).read_bytes())

    def test_global_dominance_frontier_is_complete_and_source_derived(self) -> None:
        composition = self._admissible_report()
        frontier = composition["dominance_frontier"]

        for budget_class, row in frontier["budget_classes"].items():
            self.assertGreater(row["candidate_count"], 0)
            self.assertGreater(row["exact_render_signature_count"], 0)
            self.assertLessEqual(
                row["exact_render_signature_count"], row["candidate_count"]
            )
            self.assertGreaterEqual(row["over_target_candidate_count"], 0)
            self.assertLessEqual(
                row["over_target_candidate_count"], row["candidate_count"]
            )

        budget_relations = {
            budget_class: _reconstruct_budget_dominance_relation(row)
            for budget_class, row in frontier["budget_classes"].items()
        }
        task_relation = budget_relations["task"]
        review_relation = budget_relations["review"]
        global_union = frontier["global_task_review_union"]
        reconstructed_global = _reconstruct_global_dominance_relation(
            task_relation,
            review_relation,
            global_union,
        )
        self.assertEqual(
            {
                member_kind: len(reconstructed_global["frontier"][member_kind])
                for member_kind in _DOMINANCE_MEMBER_KINDS
            },
            global_union["frontier_counts"],
        )
        self.assertEqual(
            {
                member_kind: len(
                    reconstructed_global["safe_complement"][member_kind]
                )
                for member_kind in _DOMINANCE_MEMBER_KINDS
            },
            global_union["safe_complement_counts"],
        )
        actual_membership_sha256 = {
            f"{placement}_{member_kind}": _dominance_membership_sha256(
                global_union[placement][member_kind]
            )
            for placement in ("frontier", "safe_complement")
            for member_kind in _DOMINANCE_MEMBER_KINDS
        }
        self.assertEqual(
            reconstructed_global["membership_sha256"],
            actual_membership_sha256,
        )
        runtime_manifest_path = (
            "dist/universal/skills/recommended/.changeforge-build-manifest.json"
        )
        control_projection_authority = EVAL._selector_authority()
        expected_control_projections = EVAL.layer3_selector_control_projections(
            control_projection_authority
        )
        expected_source_fingerprints = {
            "runtime_manifest": {
                "runtime": EVAL.RUNTIME_NAME,
                "path": runtime_manifest_path,
                "sha256": hashlib.sha256(
                    (ROOT / runtime_manifest_path).read_bytes()
                ).hexdigest(),
            },
            "capsule_source": {
                "path": EVAL.FIXTURES.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(EVAL.FIXTURES.read_bytes()).hexdigest(),
            },
            "control_projection_sha256": EVAL._sha256_text(
                EVAL._canonical_json_text(expected_control_projections)
            ),
            "registries": {
                path.relative_to(ROOT).as_posix(): hashlib.sha256(
                    path.read_bytes()
                ).hexdigest()
                for path in (
                    EVAL.DOMAIN_REGISTRY,
                    EVAL.FOUNDATION_REGISTRY,
                    EVAL.PROFESSIONAL_REGISTRY,
                )
            },
        }
        actual_source_fingerprints = dict(frontier["source_fingerprints"])
        selector_authority_sha256 = actual_source_fingerprints.pop(
            "selector_authority_sha256"
        )
        render_component_inventory = actual_source_fingerprints.pop(
            "render_component_inventory"
        )
        self.assertEqual(expected_source_fingerprints, actual_source_fingerprints)
        self.assertRegex(selector_authority_sha256, r"\A[0-9a-f]{64}\Z")
        self.assertGreater(render_component_inventory["count"], 0)
        self.assertRegex(
            render_component_inventory["mapping_sha256"],
            r"\A[0-9a-f]{64}\Z",
        )
        self.assertEqual(
            composition["inventory"]["canonical_representative_count"],
            frontier["mapping_row_count"],
        )
        self.assertRegex(frontier["mapping_digest"], r"\A[0-9a-f]{64}\Z")
        self.assertEqual(
            {
                "canonical_representatives_exhausted": True,
                "index_or_catalog_preload": False,
                "numeric_cap": None,
                "task_matcher": False,
                "truncation": False,
            },
            frontier["completeness"],
        )
        consumer_boundary = frontier["consumer_boundary"]
        self.assertTrue(consumer_boundary["projection_only"])
        self.assertEqual([], consumer_boundary["runtime_consumers"])
        self.assertEqual([], consumer_boundary["build_consumers"])
        checked_paths = (
            "scripts/build.py",
            "scripts/validation_utils.py",
            "src/control-prompts/main-control-agent.md",
            "src/control-skills/engineering-control-plane/references/"
            "professional-skill-router.md",
        )
        self.assertEqual(
            {
                path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
                for path in checked_paths
            },
            consumer_boundary["checked_path_fingerprints"],
        )
        for budget_class, row in frontier["budget_classes"].items():
            relation = budget_relations[budget_class]
            self.assertEqual(
                {
                    member_kind: len(relation["frontier"][member_kind])
                    for member_kind in _DOMINANCE_MEMBER_KINDS
                },
                row["frontier_counts"],
            )
            self.assertEqual(
                {
                    member_kind: len(relation["safe_complement"][member_kind])
                    for member_kind in _DOMINANCE_MEMBER_KINDS
                },
                row["outside_counts"],
            )
            maximum_tokens = max(
                [
                    item["maximum_tokens"]
                    for item in row["outside"]["active_reference"]
                ]
                + [
                    item["maximum_tokens"]
                    for item in row["frontier_witnesses"]["active_reference"]
                ]
            )
            self.assertEqual(row["token_distribution"]["max"], maximum_tokens)
            self.assertLessEqual(
                maximum_tokens,
                EVAL.CONTEXT_BUDGET_LIMITS[budget_class]["hard_ceiling"],
            )
        for row in frontier["budget_classes"].values():
            for member_kind, witnesses in row["frontier_witnesses"].items():
                self.assertEqual(row["frontier_counts"][member_kind], len(witnesses))
                self.assertTrue(
                    all(witness["maximum_tokens"] > row["soft_target"] for witness in witnesses)
                )
                self.assertTrue(
                    all(
                        re.fullmatch(r"[0-9a-f]{64}", witness["canonical_reduction_key_sha256"])
                        for witness in witnesses
                    )
                )

    def test_current_frontier_preserves_obligations_and_hard_limits(self) -> None:
        composition = self._admissible_report()
        targets = {
            budget_class: EVAL.CONTEXT_BUDGET_LIMITS[budget_class]["soft_target"]
            for budget_class in EVAL.ADMISSIBLE_BUDGET_CLASSES
        }
        maxima = composition["max_by_budget_class"]
        self.assertEqual(set(targets), set(maxima))
        self.assertEqual(
            [],
            composition["errors"],
        )
        self.assertEqual(0, composition["inventory"]["dropped_reference_obligation_count"])
        self.assertEqual(0, composition["inventory"]["required_output_receipt_failure_count"])
        for budget_class, target in targets.items():
            with self.subTest(budget_class=budget_class):
                maximum = maxima[budget_class]
                distribution = composition["dominance_frontier"]["budget_classes"][
                    budget_class
                ]["token_distribution"]
                self.assertEqual(distribution["max"], maximum["tokens"])
                self.assertEqual(
                    maximum["tokens"] <= target,
                    maximum["within_soft_target"],
                )
                self.assertEqual(
                    maximum["tokens"]
                    <= EVAL.CONTEXT_BUDGET_LIMITS[budget_class]["hard_ceiling"],
                    maximum["within_hard_ceiling"],
                )
                self.assertTrue(maximum["within_hard_ceiling"])
                self.assertTrue(maximum["route_obligations_preserved"])

    def test_c1d_data_middleware_benchmark_witness_under_direct_target(self) -> None:
        authority = EVAL._selector_authority()
        projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="data-middleware-change-builder",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        selection_classes, _inventory, errors = (
            EVAL._admissible_selector_equivalence_classes(authority, projection)
        )
        self.assertEqual([], errors)
        expected_layer3 = [
            "data-migration-design",
            "release-rollback",
            "permission-boundary-modeling",
        ]
        selected_class = next(
            item
            for item in selection_classes
            if item["selected_layer3"] == expected_layer3
        )
        receipt = selected_class["receipt"]
        self.assertEqual(
            [],
            EVAL.layer3_selector_runtime_selection_receipt_errors(
                receipt,
                expected_owner="main-control-agent",
                expected_profile="task-agent",
                expected_professional="data-middleware-change-builder",
                expected_selection_kind="implementation-risk",
                expected_selected_layer3=expected_layer3,
                expected_build_identity=receipt["build"],
            ),
        )
        self._assert_canonical_runtime_receipt(receipt)

        selected_owners = {"data-middleware-change-builder", *expected_layer3}
        selected_references = [
            (record["owner_skill"], record["path"])
            for record in projection["reference_records"]
            if record["owner_skill"] in selected_owners
        ]
        self.assertEqual(12, len(selected_references))
        context_authority = EVAL.reference_context_admissibility_authority(
            EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY),
            EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY),
            EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY),
            context="C1D named witness",
        )
        staged = EVAL.reference_context_staged_plan(
            context_authority,
            references=selected_references,
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        self.assertTrue(staged["reachable"])
        self.assertEqual(staged["selected_union"], staged["loaded_union"])
        self.assertEqual(12, len(staged["selected_union"]))
        benchmark = [
            "data-migration-design",
            "references/benchmarks-and-patterns.md",
        ]
        benchmark_stage = next(
            stage
            for stage in staged["stages"]
            if stage["loaded_references"] == [benchmark]
        )
        self.assertEqual(1, len(benchmark_stage["loaded_references"]))

        def source_professional_component() -> dict[str, object]:
            path = ROOT / "src/professional-skills/data-middleware-change-builder/SKILL.md"
            _metadata, raw_frontmatter, body = EVAL.parse_frontmatter(path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS:
                values = sections.get(heading, [])
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines("data-middleware-change-builder"))
            output.extend([
                "",
                "## Layer 3 Delivery",
                "",
                "Expanded Layer 3 roots exist only in this temporary stress projection.",
                "",
            ])
            return EVAL._component(
                "primary_skill",
                path.relative_to(ROOT).as_posix(),
                "\n".join(output),
            )

        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        capsule = EVAL._capsule_envelopes(EVAL._fixture_cases(document))["task"]
        with tempfile.TemporaryDirectory() as raw:
            temporary_root = Path(raw)
            projection_errors: list[str] = []
            proof = BUILT_LINK_VALIDATOR._validate_complete_layer3_projection_at(
                temporary_root, projection_errors
            )
            self.assertEqual([], projection_errors)
            self.assertEqual(163, proof["projected_count"])
            projection_root = temporary_root / "expanded-layer3-validation"
            components = [
                EVAL._file_component(
                    "worker_profile",
                    ROOT / "dist/copilot/project/.github/agents/task-agent.agent.md",
                ),
                source_professional_component(),
                *[
                    EVAL._file_component(
                        "layer3", projection_root / layer3 / "SKILL.md"
                    )
                    for layer3 in expected_layer3
                ],
                EVAL._file_component(
                    "layer3_reference",
                    projection_root
                    / "data-migration-design/references/benchmarks-and-patterns.md",
                ),
                capsule,
            ]
            measurement = EVAL._measure_context(
                components,
                budget_class="task",
            )
            self.assertEqual(
                sum(item["tokens"] for item in components),
                measurement["sum_component_tokens"],
            )
            self.assertTrue(measurement["within_hard_ceiling"])

    def test_frontend_named_direct_evidence_stays_singleton_and_under_target(self) -> None:
        authority = EVAL._selector_authority()
        projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="frontend-change-builder",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        classes, _inventory, errors = EVAL._admissible_selector_equivalence_classes(
            authority, projection
        )
        self.assertEqual([], errors)
        expected_layer3 = [
            "interaction-state-modeling",
            "accessibility-inclusive-design",
            "web-platform-professional-usage",
        ]
        selected = next(
            item for item in classes if item["selected_layer3"] == expected_layer3
        )
        self._assert_canonical_runtime_receipt(selected["receipt"])

        evidence_references = [
            (record["owner_skill"], record["path"])
            for record in projection["reference_records"]
            if record.get("type") == "evidence-pattern"
            and record["owner_skill"]
            in {"frontend-change-builder", *expected_layer3}
        ]
        self.assertEqual(7, len(evidence_references))
        context_authority = EVAL.reference_context_admissibility_authority(
            EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY),
            EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY),
            EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY),
            context="frontend named Direct evidence",
        )
        owner_roots = {
            "frontend-change-builder": ROOT
            / "src/professional-skills/frontend-change-builder",
            **{
                owner: ROOT / "src/foundation/capabilities" / owner
                for owner in expected_layer3
            },
        }
        for reference in evidence_references:
            with self.subTest(reference=reference):
                staged = EVAL.reference_context_staged_plan(
                    context_authority,
                    references=[reference],
                    path="direct",
                    profile="task-agent",
                    selection_owner="main-control-agent",
                    available_carrier_fields=[],
                    receipt_replayed=True,
                    brief_current=False,
                    review_fresh=True,
                )
                self.assertTrue(staged["reachable"])
                self.assertEqual([list(reference)], staged["selected_union"])
                self.assertEqual([list(reference)], staged["loaded_union"])
                self.assertEqual(1, len(staged["stages"]))
                self.assertEqual(
                    [list(reference)], staged["stages"][0]["loaded_references"]
                )
                self.assertEqual(
                    [list(reference)], staged["stages"][0]["loaded_references"]
                )
                self.assertTrue(
                    staged["stages"][0]["required_output_receipts"], reference
                )

    def test_review_architecture_named_evidence_stays_singleton_and_under_target(self) -> None:
        authority = EVAL._selector_authority()
        projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="architecture-impact-reviewer",
            profile="review-agent",
            selection_owner="engineering-brief",
            exact_layer3=None,
        )
        classes, _inventory, errors = EVAL._admissible_selector_equivalence_classes(
            authority, projection
        )
        self.assertEqual([], errors)
        expected_layer3 = [
            "module-boundary-design",
            "implementation-structure-design",
            "technology-stack-selection",
        ]
        selected = next(
            item for item in classes if item["selected_layer3"] == expected_layer3
        )
        self._assert_canonical_runtime_receipt(selected["receipt"])

        selected_owners = {"architecture-impact-reviewer", *expected_layer3}
        selected_references = [
            (record["owner_skill"], record["path"])
            for record in projection["reference_records"]
            if record["owner_skill"] in selected_owners
        ]
        self.assertEqual(13, len(selected_references))
        context_authority = EVAL.reference_context_admissibility_authority(
            EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY),
            EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY),
            EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY),
            context="Review architecture named evidence",
        )
        staged = EVAL.reference_context_staged_plan(
            context_authority,
            references=selected_references,
            path="analyzed",
            profile="review-agent",
            selection_owner="engineering-brief",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=True,
            review_fresh=True,
        )
        self.assertTrue(staged["reachable"])
        self.assertEqual(
            sorted(staged["selected_union"]), sorted(staged["loaded_union"])
        )
        self.assertEqual(13, len(staged["selected_union"]))
        self.assertTrue(
            all(len(stage["loaded_references"]) == 1 for stage in staged["stages"])
        )

        owner_roots = {
            "architecture-impact-reviewer": ROOT
            / "src/professional-skills/architecture-impact-reviewer",
            **{
                owner: ROOT / "src/foundation/capabilities" / owner
                for owner in expected_layer3
            },
        }
        active_tokens = {
            (owner, path): EVAL.count_o200k_base_tokens(
                (owner_roots[owner] / path).read_text(encoding="utf-8")
            )
            for owner, path in selected_references
        }
        self.assertEqual(
            ("implementation-structure-design", "references/reuse-and-placement.md"),
            max(active_tokens, key=active_tokens.get),
        )
        maximum = self._admissible_report()["max_by_budget_class"]["review"]
        self.assertIsNotNone(maximum)
        self.assertTrue(maximum["within_hard_ceiling"])
        self.assertTrue(maximum["route_obligations_preserved"])


    def test_c1f_repository_tooling_named_direct_witness_is_bounded(self) -> None:
        authority = EVAL._selector_authority()
        projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="repository-tooling-change-builder",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        classes, _inventory, errors = EVAL._admissible_selector_equivalence_classes(
            authority, projection
        )
        self.assertEqual([], errors)
        expected_layer3 = [
            "design-pattern-selection",
            "build-tool-professional-usage",
            "targeted-validation-selection",
        ]
        selected = next(
            item for item in classes if item["selected_layer3"] == expected_layer3
        )
        self._assert_canonical_runtime_receipt(selected["receipt"])

        selected_owners = {"repository-tooling-change-builder", *expected_layer3}
        selected_references = [
            (record["owner_skill"], record["path"])
            for record in projection["reference_records"]
            if record["owner_skill"] in selected_owners
        ]
        self.assertEqual(
            [
                ("repository-tooling-change-builder", "references/generator-and-plugin-contracts.md"),
                ("repository-tooling-change-builder", "references/harness-validity-contracts.md"),
                ("repository-tooling-change-builder", "references/repository-automation-contracts.md"),
                ("build-tool-professional-usage", "references/benchmarks-and-patterns.md"),
                ("build-tool-professional-usage", "references/checklist.md"),
                ("build-tool-professional-usage", "references/evidence-patterns.md"),
                ("design-pattern-selection", "references/pattern-evidence-record.md"),
                ("targeted-validation-selection", "references/repository-command-entry-evidence.md"),
            ],
            selected_references,
        )
        context_authority = EVAL.reference_context_admissibility_authority(
            EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY),
            EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY),
            EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY),
            context="C1F repository-tooling named Direct witness",
        )
        staged = EVAL.reference_context_staged_plan(
            context_authority,
            references=selected_references,
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        self.assertTrue(staged["reachable"])
        expected_selected_union = [list(reference) for reference in selected_references]
        expected_loaded_union = [list(reference) for reference in sorted(selected_references)]
        self.assertEqual(expected_selected_union, staged["selected_union"])
        self.assertEqual(expected_loaded_union, staged["loaded_union"])
        self.assertEqual(
            {tuple(reference) for reference in expected_selected_union},
            {tuple(reference) for reference in expected_loaded_union},
        )
        self.assertEqual(8, len(staged["selected_union"]))
        self.assertEqual(8, len(staged["loaded_union"]))
        self.assertEqual(8, len(staged["stages"]))
        self.assertEqual(8, len(staged["required_output_receipts"]))
        self.assertEqual(
            expected_loaded_union,
            [stage["loaded_references"][0] for stage in staged["stages"]],
        )
        self.assertTrue(
            all(
                len(stage["loaded_references"]) == 1
                and stage["carried_predecessors"] == []
                for stage in staged["stages"]
            )
        )
        self.assertNotEqual(expected_selected_union, expected_selected_union[:-1])
        self.assertNotEqual(expected_loaded_union, expected_loaded_union[:-1])
        active_reference = [
            "repository-tooling-change-builder",
            "references/generator-and-plugin-contracts.md",
        ]
        active_stage = next(
            stage for stage in staged["stages"]
            if stage["loaded_references"] == [active_reference]
        )
        self.assertEqual(4, active_stage["stage"])
        self.assertEqual([], active_stage["carried_predecessors"])
        self.assertEqual(
            [{
                "reference": active_reference,
                "required_outputs": ["boundary-decision", "selected-approach", "proof-limit"],
            }],
            active_stage["required_output_receipts"],
        )

        def compact_source_component(
            kind: str,
            path: Path,
            headings: tuple[str, ...],
            selector: str | None,
        ) -> dict[str, object]:
            _metadata, raw_frontmatter, body = EVAL.parse_frontmatter(path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            output.append("")
            return EVAL._component(kind, path.relative_to(ROOT).as_posix(), "\n".join(output))

        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        capsule = EVAL._capsule_envelopes(EVAL._fixture_cases(document))["task"]
        components = [
            EVAL._file_component(
                "worker_profile",
                ROOT / "dist/copilot/project/.github/agents/task-agent.agent.md",
            ),
            compact_source_component(
                "primary_skill",
                ROOT / "src/professional-skills/repository-tooling-change-builder/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                "repository-tooling-change-builder",
            ),
            *[
                compact_source_component(
                    "layer3",
                    ROOT / "src/foundation/capabilities" / owner / "SKILL.md",
                    BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                    None,
                )
                for owner in expected_layer3
            ],
            EVAL._file_component(
                "layer3_reference",
                ROOT / "src/professional-skills/repository-tooling-change-builder/references/generator-and-plugin-contracts.md",
            ),
            capsule,
        ]
        self._assert_semantic_budget_witness(
            components,
            budget_class="task",
            expected_components=[
                (
                    "worker_profile",
                    "dist/copilot/project/.github/agents/task-agent.agent.md",
                ),
                (
                    "primary_skill",
                    "src/professional-skills/repository-tooling-change-builder/"
                    "SKILL.md",
                ),
                *[
                    (
                        "layer3",
                        f"src/foundation/capabilities/{owner}/SKILL.md",
                    )
                    for owner in expected_layer3
                ],
                (
                    "layer3_reference",
                    "src/professional-skills/repository-tooling-change-builder/"
                    "references/generator-and-plugin-contracts.md",
                ),
                ("dispatch_assignment", capsule["path"]),
            ],
        )

    def test_c1f_reliability_named_review_witness_is_bounded(self) -> None:
        authority = EVAL._selector_authority()
        projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="reliability-observability-gate",
            profile="review-agent",
            selection_owner="engineering-brief",
            exact_layer3=None,
        )
        classes, _inventory, errors = EVAL._admissible_selector_equivalence_classes(
            authority, projection
        )
        self.assertEqual([], errors)
        expected_layer3 = [
            "degradation-circuit-breaking",
            "observability",
            "backup-recovery",
        ]
        selected = next(
            item for item in classes if item["selected_layer3"] == expected_layer3
        )
        self._assert_canonical_runtime_receipt(selected["receipt"])

        selected_owners = {"reliability-observability-gate", *expected_layer3}
        selected_references = [
            (record["owner_skill"], record["path"])
            for record in projection["reference_records"]
            if record["owner_skill"] in selected_owners
        ]
        expected_selected_references = [
            ("reliability-observability-gate", "references/checklist.md"),
            ("reliability-observability-gate", "references/evidence-patterns.md"),
            ("reliability-observability-gate", "references/reliability-output-and-gates.md"),
            ("reliability-observability-gate", "references/solution-optimality.md"),
            ("degradation-circuit-breaking", "references/benchmarks-and-patterns.md"),
            ("degradation-circuit-breaking", "references/checklist.md"),
            ("degradation-circuit-breaking", "references/evidence-patterns.md"),
            ("observability", "references/benchmarks-and-patterns.md"),
            ("observability", "references/checklist.md"),
            ("observability", "references/evidence-patterns.md"),
            ("backup-recovery", "references/benchmarks-and-patterns.md"),
            ("backup-recovery", "references/checklist.md"),
            ("backup-recovery", "references/evidence-patterns.md"),
        ]
        self.assertEqual(expected_selected_references, selected_references)
        self.assertEqual(13, len(selected_references))
        context_authority = EVAL.reference_context_admissibility_authority(
            EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY),
            EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY),
            EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY),
            context="C1F reliability named Review witness",
        )
        staged = EVAL.reference_context_staged_plan(
            context_authority,
            references=selected_references,
            path="analyzed",
            profile="review-agent",
            selection_owner="engineering-brief",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=True,
            review_fresh=True,
        )
        self.assertTrue(staged["reachable"])
        expected_selected_union = [list(reference) for reference in selected_references]
        expected_loaded_union = [list(reference) for reference in sorted(selected_references)]
        self.assertEqual(expected_selected_union, staged["selected_union"])
        self.assertEqual(expected_loaded_union, staged["loaded_union"])
        self.assertEqual(
            {tuple(reference) for reference in expected_selected_union},
            {tuple(reference) for reference in expected_loaded_union},
        )
        self.assertEqual(13, len(staged["selected_union"]))
        self.assertEqual(13, len(staged["loaded_union"]))
        self.assertEqual(13, len(staged["stages"]))
        self.assertEqual(13, len(staged["required_output_receipts"]))
        self.assertEqual(
            expected_loaded_union,
            [stage["loaded_references"][0] for stage in staged["stages"]],
        )
        self.assertTrue(
            all(
                len(stage["loaded_references"]) == 1
                and stage["carried_predecessors"] == []
                for stage in staged["stages"]
            )
        )
        self.assertNotEqual(expected_selected_union, expected_selected_union[:-1])
        self.assertNotEqual(expected_loaded_union, expected_loaded_union[:-1])
        active_reference = [
            "reliability-observability-gate",
            "references/reliability-output-and-gates.md",
        ]
        active_stage = next(
            stage for stage in staged["stages"]
            if stage["loaded_references"] == [active_reference]
        )
        self.assertEqual(11, active_stage["stage"])
        self.assertEqual([], active_stage["carried_predecessors"])
        self.assertEqual(
            [{
                "reference": active_reference,
                "required_outputs": ["gate-decision", "residual-risk"],
            }],
            active_stage["required_output_receipts"],
        )

        def compact_source_component(
            kind: str,
            path: Path,
            headings: tuple[str, ...],
            selector: str | None,
        ) -> dict[str, object]:
            _metadata, raw_frontmatter, body = EVAL.parse_frontmatter(path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            output.append("")
            return EVAL._component(kind, path.relative_to(ROOT).as_posix(), "\n".join(output))

        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        capsule = EVAL._capsule_envelopes(EVAL._fixture_cases(document))["review"]
        components = [
            EVAL._file_component(
                "review_profile",
                ROOT / "dist/copilot/project/.github/agents/review-agent.agent.md",
            ),
            compact_source_component(
                "primary_skill",
                ROOT / "src/professional-skills/reliability-observability-gate/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                "reliability-observability-gate",
            ),
            *[
                compact_source_component(
                    "layer3",
                    ROOT / "src/foundation/capabilities" / owner / "SKILL.md",
                    BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                    None,
                )
                for owner in expected_layer3
            ],
            EVAL._file_component(
                "layer3_reference",
                ROOT / "src/professional-skills/reliability-observability-gate/references/reliability-output-and-gates.md",
            ),
            capsule,
        ]
        measurement = EVAL._measure_context(
            components,
            budget_class="review",
        )
        self.assertEqual(
            sum(item["tokens"] for item in components),
            measurement["sum_component_tokens"],
        )
        self.assertTrue(measurement["within_hard_ceiling"])

    def test_c1g_delivery_release_named_task_and_review_witnesses_are_bounded(self) -> None:
        authority = EVAL._selector_authority()
        expected_layer3 = [
            "release-rollback",
            "version-compatibility",
            "configuration-runtime-policy",
        ]
        expected_selected_references = [
            ("delivery-release-gate", "references/checklist.md"),
            ("delivery-release-gate", "references/delivery-output-and-gates.md"),
            ("delivery-release-gate", "references/release-evidence-patterns.md"),
            ("release-rollback", "references/benchmarks-and-patterns.md"),
            ("release-rollback", "references/checklist.md"),
            ("release-rollback", "references/evidence-patterns.md"),
            ("version-compatibility", "references/checklist.md"),
            ("version-compatibility", "references/compatibility-benchmarks.md"),
            ("version-compatibility", "references/evidence-patterns.md"),
            ("configuration-runtime-policy", "references/benchmarks-and-patterns.md"),
            ("configuration-runtime-policy", "references/checklist.md"),
            ("configuration-runtime-policy", "references/evidence-patterns.md"),
        ]
        expected_loaded_union = [
            list(reference) for reference in sorted(expected_selected_references)
        ]
        context_authority = EVAL.reference_context_admissibility_authority(
            EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY),
            EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY),
            EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY),
            context="C1G delivery-release named Task and Review witnesses",
        )

        def compact_source_component(
            kind: str,
            path: Path,
            headings: tuple[str, ...],
            selector: str | None,
        ) -> dict[str, object]:
            _metadata, raw_frontmatter, body = EVAL.parse_frontmatter(path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            output.append("")
            return EVAL._component(
                kind,
                path.relative_to(ROOT).as_posix(),
                "\n".join(output),
            )

        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        capsules = EVAL._capsule_envelopes(EVAL._fixture_cases(document))
        cases = (
            {
                "budget_class": "task",
                "profile": "task-agent",
                "selection_owner": "main-control-agent",
                "path": "direct",
                "brief_current": False,
                "receipt": "ff2e40b9dac8df918ee255de792fe38e76b797daa2053634bfbb982f98a3448a",
                "profile_path": ROOT / "dist/copilot/project/.github/agents/task-agent.agent.md",
                "profile_kind": "worker_profile",
                "capsule": capsules["task"],
            },
            {
                "budget_class": "review",
                "profile": "review-agent",
                "selection_owner": "engineering-brief",
                "path": "analyzed",
                "brief_current": True,
                "receipt": "a315f22c298373562a6f6d6120b954f95dbef726a57b7bc9b13572b0d9ff3a58",
                "profile_path": ROOT / "dist/copilot/project/.github/agents/review-agent.agent.md",
                "profile_kind": "review_profile",
                "capsule": capsules["review"],
            },
        )
        for case in cases:
            with self.subTest(profile=case["profile"]):
                projection = EVAL.layer3_selector_runtime_projection(
                    authority,
                    professional_skill="delivery-release-gate",
                    profile=case["profile"],
                    selection_owner=case["selection_owner"],
                    exact_layer3=None,
                )
                classes, _inventory, errors = (
                    EVAL._admissible_selector_equivalence_classes(
                        authority, projection
                    )
                )
                self.assertEqual([], errors)
                selected = next(
                    item
                    for item in classes
                    if item["selected_layer3"] == expected_layer3
                )
                self._assert_canonical_runtime_receipt(selected["receipt"])
                self.assertTrue(
                    set(expected_layer3).isdisjoint(projection["domain_authorization"])
                )
                selected_owners = {"delivery-release-gate", *expected_layer3}
                selected_references = [
                    (record["owner_skill"], record["path"])
                    for record in projection["reference_records"]
                    if record["owner_skill"] in selected_owners
                ]
                self.assertEqual(expected_selected_references, selected_references)
                staged = EVAL.reference_context_staged_plan(
                    context_authority,
                    references=selected_references,
                    path=case["path"],
                    profile=case["profile"],
                    selection_owner=case["selection_owner"],
                    available_carrier_fields=[],
                    receipt_replayed=True,
                    brief_current=case["brief_current"],
                    review_fresh=True,
                )
                expected_selected_union = [
                    list(reference) for reference in selected_references
                ]
                self.assertTrue(staged["reachable"])
                self.assertEqual(expected_selected_union, staged["selected_union"])
                self.assertEqual(expected_loaded_union, staged["loaded_union"])
                self.assertEqual(
                    {tuple(reference) for reference in expected_selected_union},
                    {tuple(reference) for reference in expected_loaded_union},
                )
                self.assertEqual(12, len(staged["selected_union"]))
                self.assertEqual(12, len(staged["loaded_union"]))
                self.assertEqual(12, len(staged["stages"]))
                self.assertEqual(12, len(staged["required_output_receipts"]))
                self.assertEqual(
                    expected_loaded_union,
                    [stage["loaded_references"][0] for stage in staged["stages"]],
                )
                self.assertTrue(
                    all(
                        len(stage["loaded_references"]) == 1
                        and stage["carried_predecessors"] == []
                        for stage in staged["stages"]
                    )
                )
                self.assertNotEqual(expected_selected_union, expected_selected_union[:-1])
                self.assertNotEqual(expected_loaded_union, expected_loaded_union[:-1])
                active_reference = [
                    "version-compatibility",
                    "references/compatibility-benchmarks.md",
                ]
                active_stage = next(
                    stage
                    for stage in staged["stages"]
                    if stage["loaded_references"] == [active_reference]
                )
                self.assertEqual(10, active_stage["stage"])
                self.assertEqual([], active_stage["carried_predecessors"])
                self.assertEqual(
                    [{
                        "reference": active_reference,
                        "required_outputs": ["option-comparison", "selected-approach"],
                    }],
                    active_stage["required_output_receipts"],
                )
                components = [
                    EVAL._file_component(
                        case["profile_kind"], case["profile_path"]
                    ),
                    compact_source_component(
                        "primary_skill",
                        ROOT / "src/professional-skills/delivery-release-gate/SKILL.md",
                        BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                        "delivery-release-gate",
                    ),
                    *[
                        compact_source_component(
                            "layer3",
                            ROOT / "src/foundation/capabilities" / owner / "SKILL.md",
                            BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                            None,
                        )
                        for owner in expected_layer3
                    ],
                    EVAL._file_component(
                        "layer3_reference",
                        ROOT / "src/foundation/capabilities/version-compatibility/references/compatibility-benchmarks.md",
                    ),
                    case["capsule"],
                ]
                self._assert_semantic_budget_witness(
                    components,
                    budget_class=case["budget_class"],
                    expected_components=[
                        (
                            case["profile_kind"],
                            case["profile_path"].relative_to(ROOT).as_posix(),
                        ),
                        (
                            "primary_skill",
                            "src/professional-skills/delivery-release-gate/SKILL.md",
                        ),
                        *[
                            (
                                "layer3",
                                f"src/foundation/capabilities/{owner}/SKILL.md",
                            )
                            for owner in expected_layer3
                        ],
                        (
                            "layer3_reference",
                            "src/foundation/capabilities/version-compatibility/"
                            "references/compatibility-benchmarks.md",
                        ),
                        ("dispatch_assignment", case["capsule"]["path"]),
                    ],
                )

    def test_c1h_logging_named_task_and_review_witnesses_are_bounded(self) -> None:
        authority = EVAL._selector_authority()
        expected_layer3 = [
            "audit-evidence-integrity",
            "secret-configuration-security",
            "logging-error-handling",
        ]
        expected_selected_references = [
            ("logging-design-gate", "references/checklist.md"),
            ("logging-design-gate", "references/logging-output-and-gates.md"),
            ("logging-design-gate", "references/logging-selection-criteria.md"),
            ("logging-error-handling", "references/benchmarks-and-patterns.md"),
            ("logging-error-handling", "references/checklist.md"),
            ("logging-error-handling", "references/evidence-patterns.md"),
            ("secret-configuration-security", "references/benchmarks-and-patterns.md"),
            ("secret-configuration-security", "references/checklist.md"),
            ("secret-configuration-security", "references/evidence-patterns.md"),
            ("audit-evidence-integrity", "references/completeness-identity-and-time.md"),
            ("audit-evidence-integrity", "references/tamper-evidence-storage-and-access.md"),
            ("audit-evidence-integrity", "references/retention-export-and-chain-of-custody.md"),
        ]
        expected_loaded_union = [
            list(reference) for reference in sorted(expected_selected_references)
        ]
        context_authority = EVAL.reference_context_admissibility_authority(
            EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY),
            EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY),
            EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY),
            context="C1H logging named Task and Review witnesses",
        )

        def compact_source_component(
            kind: str,
            path: Path,
            headings: tuple[str, ...],
            selector: str | None,
        ) -> dict[str, object]:
            _metadata, raw_frontmatter, body = EVAL.parse_frontmatter(path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            output.append("")
            return EVAL._component(
                kind,
                path.relative_to(ROOT).as_posix(),
                "\n".join(output),
            )

        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        capsules = EVAL._capsule_envelopes(EVAL._fixture_cases(document))
        cases = (
            {
                "budget_class": "task",
                "profile": "task-agent",
                "selection_owner": "main-control-agent",
                "path": "direct",
                "brief_current": False,
                "receipt": "847e3e393a0b788fde7fff1b6e1197b77f9c93645557ab028a12c251a05e2ed3",
                "profile_path": ROOT / "dist/copilot/project/.github/agents/task-agent.agent.md",
                "profile_kind": "worker_profile",
                "capsule": capsules["task"],
            },
            {
                "budget_class": "review",
                "profile": "review-agent",
                "selection_owner": "engineering-brief",
                "path": "analyzed",
                "brief_current": True,
                "receipt": "68c159e1558c75166882b4559ece25fb3c5b0828f27b4df1dbc8b17f93eba78a",
                "profile_path": ROOT / "dist/copilot/project/.github/agents/review-agent.agent.md",
                "profile_kind": "review_profile",
                "capsule": capsules["review"],
            },
        )
        for case in cases:
            with self.subTest(profile=case["profile"]):
                projection = EVAL.layer3_selector_runtime_projection(
                    authority,
                    professional_skill="logging-design-gate",
                    profile=case["profile"],
                    selection_owner=case["selection_owner"],
                    exact_layer3=None,
                )
                classes, _inventory, errors = (
                    EVAL._admissible_selector_equivalence_classes(
                        authority, projection
                    )
                )
                self.assertEqual([], errors)
                selected = next(
                    item
                    for item in classes
                    if item["selected_layer3"] == expected_layer3
                )
                self._assert_canonical_runtime_receipt(selected["receipt"])
                self.assertTrue(
                    set(expected_layer3).isdisjoint(projection["domain_authorization"])
                )
                self.assertEqual([], projection["domain_authorization"])
                selected_owners = {"logging-design-gate", *expected_layer3}
                selected_references = [
                    (record["owner_skill"], record["path"])
                    for record in projection["reference_records"]
                    if record["owner_skill"] in selected_owners
                ]
                self.assertEqual(expected_selected_references, selected_references)
                reference_components = [
                    EVAL._file_component(
                        "layer3_reference",
                        (
                            ROOT
                            / (
                                "src/professional-skills"
                                if owner == "logging-design-gate"
                                else "src/foundation/capabilities"
                            )
                            / owner
                            / path
                        ),
                    )
                    for owner, path in selected_references
                ]
                self.assertEqual(12, len(reference_components))
                self.assertTrue(all(item["_text"].strip() for item in reference_components))
                staged = EVAL.reference_context_staged_plan(
                    context_authority,
                    references=selected_references,
                    path=case["path"],
                    profile=case["profile"],
                    selection_owner=case["selection_owner"],
                    available_carrier_fields=[],
                    receipt_replayed=True,
                    brief_current=case["brief_current"],
                    review_fresh=True,
                )
                expected_selected_union = [
                    list(reference) for reference in selected_references
                ]
                self.assertTrue(staged["reachable"])
                self.assertEqual(expected_selected_union, staged["selected_union"])
                self.assertEqual(expected_loaded_union, staged["loaded_union"])
                self.assertEqual(
                    {tuple(reference) for reference in expected_selected_union},
                    {tuple(reference) for reference in expected_loaded_union},
                )
                self.assertEqual(12, len(staged["selected_union"]))
                self.assertEqual(12, len(staged["loaded_union"]))
                self.assertEqual(12, len(staged["stages"]))
                self.assertEqual(12, len(staged["required_output_receipts"]))
                self.assertEqual(
                    expected_loaded_union,
                    [stage["loaded_references"][0] for stage in staged["stages"]],
                )
                self.assertTrue(
                    all(
                        len(stage["loaded_references"]) == 1
                        and stage["carried_predecessors"] == []
                        for stage in staged["stages"]
                    )
                )
                self.assertNotEqual(expected_selected_union, expected_selected_union[:-1])
                self.assertNotEqual(expected_loaded_union, expected_loaded_union[:-1])
                active_reference = [
                    "logging-error-handling",
                    "references/benchmarks-and-patterns.md",
                ]
                active_stage = next(
                    stage
                    for stage in staged["stages"]
                    if stage["loaded_references"] == [active_reference]
                )
                self.assertEqual(6, active_stage["stage"])
                self.assertEqual([], active_stage["carried_predecessors"])
                self.assertEqual(
                    [{
                        "reference": active_reference,
                        "required_outputs": ["option-comparison", "selected-approach"],
                    }],
                    active_stage["required_output_receipts"],
                )
                components = [
                    EVAL._file_component(
                        case["profile_kind"], case["profile_path"]
                    ),
                    compact_source_component(
                        "primary_skill",
                        ROOT / "src/professional-skills/logging-design-gate/SKILL.md",
                        BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                        "logging-design-gate",
                    ),
                    *[
                        compact_source_component(
                            "layer3",
                            ROOT / "src/foundation/capabilities" / owner / "SKILL.md",
                            BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                            None,
                        )
                        for owner in expected_layer3
                    ],
                    EVAL._file_component(
                        "layer3_reference",
                        ROOT / "src/foundation/capabilities/logging-error-handling/references/benchmarks-and-patterns.md",
                    ),
                    case["capsule"],
                ]
                self._assert_semantic_budget_witness(
                    components,
                    budget_class=case["budget_class"],
                    expected_components=[
                        (
                            case["profile_kind"],
                            case["profile_path"].relative_to(ROOT).as_posix(),
                        ),
                        (
                            "primary_skill",
                            "src/professional-skills/logging-design-gate/SKILL.md",
                        ),
                        *[
                            (
                                "layer3",
                                f"src/foundation/capabilities/{owner}/SKILL.md",
                            )
                            for owner in expected_layer3
                        ],
                        (
                            "layer3_reference",
                            "src/foundation/capabilities/logging-error-handling/"
                            "references/benchmarks-and-patterns.md",
                        ),
                        ("dispatch_assignment", case["capsule"]["path"]),
                    ],
                )

    def test_c1i_quality_task_and_review_projection_witnesses_are_bounded(self) -> None:
        authority = EVAL._selector_authority()
        professional = EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY)
        foundation = EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY)
        domain = EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY)
        domain_names = {row["name"] for row in domain["domain_skills"]}
        context_authority = EVAL.reference_context_admissibility_authority(
            professional,
            foundation,
            domain,
            context="C1I named Task and Review projections",
        )

        def compact_source_component(
            kind: str,
            path: Path,
            headings: tuple[str, ...],
            selector: str | None,
        ) -> dict[str, object]:
            _metadata, raw_frontmatter, body = EVAL.parse_frontmatter(path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            output.append("")
            return EVAL._component(
                kind,
                path.relative_to(ROOT).as_posix(),
                "\n".join(output),
            )

        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        capsules = EVAL._capsule_envelopes(EVAL._fixture_cases(document))

        task_layer3 = [
            "test-data-management",
            "targeted-validation-selection",
            "test-strategy",
        ]
        task_projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="quality-test-gate",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        task_classes, _task_inventory, task_errors = (
            EVAL._admissible_selector_equivalence_classes(
                authority, task_projection
            )
        )
        self.assertEqual([], task_errors)
        task_selected = next(
            item
            for item in task_classes
            if item["selected_layer3"] == task_layer3
        )
        self._assert_canonical_runtime_receipt(task_selected["receipt"])
        self.assertTrue(
            set(task_layer3).isdisjoint(task_projection["domain_authorization"])
        )
        task_owners = {"quality-test-gate", *task_layer3}
        expected_task_selected_references = [
            ("quality-test-gate", "references/checklist.md"),
            ("quality-test-gate", "references/test-output-and-gates.md"),
            ("quality-test-gate", "references/test-structure-boundaries.md"),
            ("test-strategy", "references/benchmarks-and-patterns.md"),
            ("test-strategy", "references/checklist.md"),
            ("test-strategy", "references/evidence-patterns.md"),
            ("test-data-management", "references/benchmarks-and-patterns.md"),
            ("test-data-management", "references/checklist.md"),
            ("test-data-management", "references/evidence-patterns.md"),
            (
                "targeted-validation-selection",
                "references/repository-command-entry-evidence.md",
            ),
        ]
        task_selected_references = [
            (record["owner_skill"], record["path"])
            for record in task_projection["reference_records"]
            if record["owner_skill"] in task_owners
        ]
        self.assertEqual(
            expected_task_selected_references,
            task_selected_references,
        )
        self.assertEqual(
            set(),
            {owner for owner, _path in task_selected_references} & domain_names,
        )
        task_staged = EVAL.reference_context_staged_plan(
            context_authority,
            references=task_selected_references,
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        expected_task_selected_union = [
            list(reference) for reference in expected_task_selected_references
        ]
        expected_task_loaded_union = [
            list(reference) for reference in sorted(task_selected_references)
        ]
        expected_task_stage_outputs = [
            (["quality-test-gate", "references/checklist.md"], ["checklist-result", "validation-plan"]),
            (["quality-test-gate", "references/test-output-and-gates.md"], ["gate-decision", "residual-risk"]),
            (["quality-test-gate", "references/test-structure-boundaries.md"], ["validation-plan", "proof-limit"]),
            (["targeted-validation-selection", "references/repository-command-entry-evidence.md"], ["evidence-record", "proof-limit", "residual-risk"]),
            (["test-data-management", "references/benchmarks-and-patterns.md"], ["option-comparison", "selected-approach"]),
            (["test-data-management", "references/checklist.md"], ["checklist-result", "residual-risk"]),
            (["test-data-management", "references/evidence-patterns.md"], ["evidence-record", "proof-limit", "residual-risk"]),
            (["test-strategy", "references/benchmarks-and-patterns.md"], ["option-comparison", "selected-approach"]),
            (["test-strategy", "references/checklist.md"], ["checklist-result", "residual-risk"]),
            (["test-strategy", "references/evidence-patterns.md"], ["evidence-record", "proof-limit", "residual-risk"]),
        ]
        self.assertTrue(task_staged["reachable"])
        self.assertEqual(
            expected_task_selected_union, task_staged["selected_union"]
        )
        self.assertEqual(
            expected_task_loaded_union, task_staged["loaded_union"]
        )
        self.assertEqual(10, len(task_staged["stages"]))
        self.assertEqual(10, len(task_staged["required_output_receipts"]))
        self.assertEqual([], task_staged["carried_predecessors"])
        for stage, (reference, required_outputs) in zip(
            task_staged["stages"],
            expected_task_stage_outputs,
            strict=True,
        ):
            self.assertEqual([reference], stage["loaded_references"])
            self.assertEqual([], stage["carried_predecessors"])
            self.assertEqual(
                [{"reference": reference, "required_outputs": required_outputs}],
                stage["required_output_receipts"],
            )
        task_reference_components = [
            EVAL._file_component(
                "layer3_reference",
                ROOT
                / (
                    "src/professional-skills"
                    if owner == "quality-test-gate"
                    else "src/foundation/capabilities"
                )
                / owner
                / path,
            )
            for owner, path in task_selected_references
        ]
        self.assertEqual(10, len(task_reference_components))
        self.assertTrue(all(item["_text"].strip() for item in task_reference_components))
        task_active_reference = [
            "quality-test-gate",
            "references/test-output-and-gates.md",
        ]
        task_active_stage = next(
            stage
            for stage in task_staged["stages"]
            if stage["loaded_references"] == [task_active_reference]
        )
        self.assertEqual(1, task_active_stage["stage"])
        self.assertEqual([], task_active_stage["carried_predecessors"])
        self.assertEqual(
            [{
                "reference": task_active_reference,
                "required_outputs": ["gate-decision", "residual-risk"],
            }],
            task_active_stage["required_output_receipts"],
        )
        task_components = [
            EVAL._file_component(
                "worker_profile",
                ROOT / "dist/copilot/project/.github/agents/task-agent.agent.md",
            ),
            compact_source_component(
                "primary_skill",
                ROOT / "src/professional-skills/quality-test-gate/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                "quality-test-gate",
            ),
            *[
                compact_source_component(
                    "layer3",
                    ROOT / "src/foundation/capabilities" / owner / "SKILL.md",
                    BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                    None,
                )
                for owner in task_layer3
            ],
            EVAL._file_component(
                "layer3_reference",
                ROOT
                / "src/professional-skills/quality-test-gate/references/test-output-and-gates.md",
            ),
            capsules["task"],
        ]
        self._assert_semantic_budget_witness(
            task_components,
            budget_class="task",
            expected_components=[
                (
                    "worker_profile",
                    "dist/copilot/project/.github/agents/task-agent.agent.md",
                ),
                (
                    "primary_skill",
                    "src/professional-skills/quality-test-gate/SKILL.md",
                ),
                *[
                    (
                        "layer3",
                        f"src/foundation/capabilities/{owner}/SKILL.md",
                    )
                    for owner in task_layer3
                ],
                (
                    "layer3_reference",
                    "src/professional-skills/quality-test-gate/"
                    "references/test-output-and-gates.md",
                ),
                ("dispatch_assignment", capsules["task"]["path"]),
            ],
        )
        review_layer3 = [
            "domain-object-identification",
            "implementation-structure-design",
            "refactoring",
        ]
        review_projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="ai-code-review-refactor",
            profile="review-agent",
            selection_owner="engineering-brief",
            exact_layer3=None,
        )
        review_classes, _review_inventory, review_errors = (
            EVAL._admissible_selector_equivalence_classes(
                authority, review_projection
            )
        )
        self.assertEqual([], review_errors)
        review_selected = next(
            item
            for item in review_classes
            if item["selected_layer3"] == review_layer3
        )
        self._assert_canonical_runtime_receipt(review_selected["receipt"])
        self.assertTrue(
            set(review_layer3).isdisjoint(
                review_projection["domain_authorization"]
            )
        )
        review_owners = {"ai-code-review-refactor", *review_layer3}
        expected_review_selected_references = [
            ("ai-code-review-refactor", "references/ai-review-pattern-catalog.md"),
            ("ai-code-review-refactor", "references/review-output-and-gates.md"),
            ("ai-code-review-refactor", "references/solution-optimality.md"),
            ("domain-object-identification", "references/benchmarks-and-patterns.md"),
            ("domain-object-identification", "references/checklist.md"),
            ("domain-object-identification", "references/evidence-patterns.md"),
            ("implementation-structure-design", "references/object-module-decomposition.md"),
            ("implementation-structure-design", "references/reuse-and-placement.md"),
            ("implementation-structure-design", "references/evidence-patterns.md"),
            ("refactoring", "references/behavior-preservation-evidence.md"),
            ("refactoring", "references/checklist.md"),
            ("refactoring", "references/split-merge-cleanup-patterns.md"),
        ]
        review_selected_references = [
            (record["owner_skill"], record["path"])
            for record in review_projection["reference_records"]
            if record["owner_skill"] in review_owners
            and not (
                record["owner_skill"] == "ai-code-review-refactor"
                and record["path"] == "references/checklist.md"
            )
        ]
        self.assertEqual(
            expected_review_selected_references,
            review_selected_references,
        )
        self.assertEqual(
            set(),
            {owner for owner, _path in review_selected_references} & domain_names,
        )
        review_declarations = context_authority["owners"][
            "ai-code-review-refactor"
        ]["declarations"]
        self.assertEqual(
            [
                "references/ai-review-pattern-catalog.md",
                "references/review-output-and-gates.md",
            ],
            review_declarations["references/checklist.md"]["conflicts_with"],
        )
        self.assertNotIn(
            ("ai-code-review-refactor", "references/checklist.md"),
            review_selected_references,
        )
        expected_review_loaded_union = [
            list(reference) for reference in sorted(review_selected_references)
        ]
        review_records = {
            (record["owner_skill"], record["path"]): record
            for record in review_projection["reference_records"]
            if (record["owner_skill"], record["path"])
            in set(review_selected_references)
        }
        expected_review_stage_outputs = [
            (["ai-code-review-refactor", "references/ai-review-pattern-catalog.md"], ["option-comparison", "selected-approach"]),
            (["ai-code-review-refactor", "references/review-output-and-gates.md"], ["gate-decision", "residual-risk"]),
            (["ai-code-review-refactor", "references/solution-optimality.md"], ["selected-approach", "residual-risk"]),
            (["domain-object-identification", "references/benchmarks-and-patterns.md"], ["option-comparison", "selected-approach"]),
            (["domain-object-identification", "references/checklist.md"], ["checklist-result", "residual-risk"]),
            (["domain-object-identification", "references/evidence-patterns.md"], ["evidence-record", "proof-limit", "residual-risk"]),
            (["implementation-structure-design", "references/evidence-patterns.md"], ["evidence-record", "validation-plan", "proof-limit", "residual-risk"]),
            (["implementation-structure-design", "references/object-module-decomposition.md"], ["decision-record", "validation-plan", "proof-limit", "residual-risk"]),
            (["implementation-structure-design", "references/reuse-and-placement.md"], ["selected-approach", "validation-plan", "proof-limit", "residual-risk"]),
            (["refactoring", "references/behavior-preservation-evidence.md"], ["evidence-record", "proof-limit", "residual-risk"]),
            (["refactoring", "references/checklist.md"], ["checklist-result", "residual-risk"]),
            (["refactoring", "references/split-merge-cleanup-patterns.md"], ["option-comparison", "selected-approach"]),
        ]
        actual_review_stages = []
        for stage, reference in enumerate(expected_review_loaded_union):
            record = review_records[tuple(reference)]
            self.assertEqual("singleton", record["residency"])
            actual_review_stages.append(
                (
                    stage,
                    reference,
                    record["required_output"],
                    [],
                )
            )
        self.assertEqual(
            [
                (stage, reference, outputs, [])
                for stage, (reference, outputs) in enumerate(
                    expected_review_stage_outputs
                )
            ],
            actual_review_stages,
        )
        self.assertEqual(12, len(review_selected_references))
        self.assertEqual(12, len(expected_review_loaded_union))
        self.assertEqual(
            {tuple(reference) for reference in review_selected_references},
            {tuple(reference) for reference in expected_review_loaded_union},
        )
        self.assertNotEqual(
            review_selected_references, review_selected_references[:-1]
        )
        self.assertNotEqual(
            expected_review_loaded_union, expected_review_loaded_union[:-1]
        )
        review_active_reference = [
            "refactoring",
            "references/split-merge-cleanup-patterns.md",
        ]
        review_active_stage = next(
            item
            for item in actual_review_stages
            if item[1] == review_active_reference
        )
        self.assertEqual(
            (11, review_active_reference, ["option-comparison", "selected-approach"], []),
            review_active_stage,
        )
        review_components = [
            EVAL._file_component(
                "review_profile",
                ROOT / "dist/copilot/project/.github/agents/review-agent.agent.md",
            ),
            EVAL._file_component(
                "primary_skill",
                ROOT
                / "dist/copilot/project/.github/skills/recommended/ai-code-review-refactor/SKILL.md",
            ),
            *[
                compact_source_component(
                    "layer3",
                    ROOT / "src/foundation/capabilities" / owner / "SKILL.md",
                    BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                    None,
                )
                for owner in review_layer3
            ],
            EVAL._file_component(
                "layer3_reference",
                ROOT
                / "src/foundation/capabilities/refactoring/references/split-merge-cleanup-patterns.md",
            ),
            capsules["review"],
        ]
        self._assert_semantic_budget_witness(
            review_components,
            budget_class="review",
            expected_components=[
                (
                    "review_profile",
                    "dist/copilot/project/.github/agents/review-agent.agent.md",
                ),
                (
                    "primary_skill",
                    "dist/copilot/project/.github/skills/recommended/"
                    "ai-code-review-refactor/SKILL.md",
                ),
                *[
                    (
                        "layer3",
                        f"src/foundation/capabilities/{owner}/SKILL.md",
                    )
                    for owner in review_layer3
                ],
                (
                    "layer3_reference",
                    "src/foundation/capabilities/refactoring/"
                    "references/split-merge-cleanup-patterns.md",
                ),
                ("dispatch_assignment", capsules["review"]["path"]),
            ],
        )

    def test_c1j_data_middleware_named_task_witness_is_bounded(self) -> None:
        authority = EVAL._selector_authority()
        professional = EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY)
        foundation = EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY)
        domain = EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY)
        domain_names = {row["name"] for row in domain["domain_skills"]}
        expected_layer3 = [
            "concurrency-control",
            "transaction-consistency",
            "distributed-workflow-consistency",
        ]
        projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="data-middleware-change-builder",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        classes, _inventory, errors = (
            EVAL._admissible_selector_equivalence_classes(authority, projection)
        )
        self.assertEqual([], errors)
        selected = next(
            item for item in classes
            if item["selected_layer3"] == expected_layer3
        )
        self._assert_canonical_runtime_receipt(selected["receipt"])
        self.assertTrue(
            set(expected_layer3).isdisjoint(projection["domain_authorization"])
        )

        selected_owners = {"data-middleware-change-builder", *expected_layer3}
        expected_selected_references = [
            ("data-middleware-change-builder", "references/checklist.md"),
            ("data-middleware-change-builder", "references/evidence-patterns.md"),
            ("data-middleware-change-builder", "references/recovery-patterns.md"),
            ("transaction-consistency", "references/benchmarks-and-patterns.md"),
            ("transaction-consistency", "references/checklist.md"),
            ("transaction-consistency", "references/evidence-patterns.md"),
            ("concurrency-control", "references/benchmarks-and-patterns.md"),
            ("concurrency-control", "references/checklist.md"),
            ("concurrency-control", "references/evidence-patterns.md"),
            ("distributed-workflow-consistency", "references/identity-state-and-unknown-outcomes.md"),
            ("distributed-workflow-consistency", "references/compensation-convergence-and-reconciliation.md"),
            ("distributed-workflow-consistency", "references/stuck-manual-repair-and-versioning.md"),
        ]
        selected_references = [
            (record["owner_skill"], record["path"])
            for record in projection["reference_records"]
            if record["owner_skill"] in selected_owners
        ]
        self.assertEqual(expected_selected_references, selected_references)
        self.assertEqual(
            set(),
            {owner for owner, _path in selected_references} & domain_names,
        )

        context_authority = EVAL.reference_context_admissibility_authority(
            professional,
            foundation,
            domain,
            context="C1J data-middleware named Task witness",
        )
        staged = EVAL.reference_context_staged_plan(
            context_authority,
            references=selected_references,
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        expected_selected_union = [
            list(reference) for reference in expected_selected_references
        ]
        expected_loaded_union = [
            list(reference) for reference in sorted(expected_selected_references)
        ]
        expected_stage_outputs = [
            (["concurrency-control", "references/benchmarks-and-patterns.md"], ["option-comparison", "selected-approach"]),
            (["concurrency-control", "references/checklist.md"], ["checklist-result", "residual-risk"]),
            (["concurrency-control", "references/evidence-patterns.md"], ["evidence-record", "proof-limit", "residual-risk"]),
            (["data-middleware-change-builder", "references/checklist.md"], ["checklist-result", "residual-risk"]),
            (["data-middleware-change-builder", "references/evidence-patterns.md"], ["evidence-record", "proof-limit", "residual-risk"]),
            (["data-middleware-change-builder", "references/recovery-patterns.md"], ["option-comparison", "selected-approach"]),
            (["distributed-workflow-consistency", "references/compensation-convergence-and-reconciliation.md"], ["failure-decision", "selected-approach", "residual-risk"]),
            (["distributed-workflow-consistency", "references/identity-state-and-unknown-outcomes.md"], ["boundary-decision", "failure-decision", "proof-limit"]),
            (["distributed-workflow-consistency", "references/stuck-manual-repair-and-versioning.md"], ["failure-decision", "validation-plan", "proof-limit"]),
            (["transaction-consistency", "references/benchmarks-and-patterns.md"], ["option-comparison", "selected-approach"]),
            (["transaction-consistency", "references/checklist.md"], ["checklist-result", "residual-risk"]),
            (["transaction-consistency", "references/evidence-patterns.md"], ["evidence-record", "proof-limit", "residual-risk"]),
        ]
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected_selected_union, staged["selected_union"])
        self.assertEqual(expected_loaded_union, staged["loaded_union"])
        self.assertEqual(12, len(staged["selected_union"]))
        self.assertEqual(12, len(staged["loaded_union"]))
        self.assertEqual(12, len(staged["stages"]))
        self.assertEqual(12, len(staged["required_output_receipts"]))
        self.assertEqual([], staged["carried_predecessors"])
        for stage, (reference, required_outputs) in zip(
            staged["stages"], expected_stage_outputs, strict=True
        ):
            self.assertEqual([reference], stage["loaded_references"])
            self.assertEqual([], stage["carried_predecessors"])
            self.assertEqual(
                [{"reference": reference, "required_outputs": required_outputs}],
                stage["required_output_receipts"],
            )
        self.assertEqual(
            {tuple(reference) for reference in expected_selected_union},
            {tuple(reference) for reference in expected_loaded_union},
        )
        self.assertNotEqual(expected_selected_union, expected_selected_union[:-1])
        self.assertNotEqual(expected_loaded_union, expected_loaded_union[:-1])

        owner_roots = {
            "data-middleware-change-builder": ROOT / "src/professional-skills/data-middleware-change-builder",
            **{
                owner: ROOT / "src/foundation/capabilities" / owner
                for owner in expected_layer3
            },
        }
        reference_components = [
            EVAL._file_component(
                "layer3_reference", owner_roots[owner] / path
            )
            for owner, path in selected_references
        ]
        self.assertEqual(12, len(reference_components))
        self.assertTrue(all(item["_text"].strip() for item in reference_components))

        active_reference = [
            "transaction-consistency",
            "references/evidence-patterns.md",
        ]
        active_stage = next(
            stage for stage in staged["stages"]
            if stage["loaded_references"] == [active_reference]
        )
        self.assertEqual(11, active_stage["stage"])
        self.assertEqual([], active_stage["carried_predecessors"])
        self.assertEqual(
            [{
                "reference": active_reference,
                "required_outputs": ["evidence-record", "proof-limit", "residual-risk"],
            }],
            active_stage["required_output_receipts"],
        )

        def compact_source_component(
            kind: str,
            path: Path,
            headings: tuple[str, ...],
            selector: str | None,
        ) -> dict[str, object]:
            _metadata, raw_frontmatter, body = EVAL.parse_frontmatter(path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            output.append("")
            return EVAL._component(
                kind,
                path.relative_to(ROOT).as_posix(),
                "\n".join(output),
            )

        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        capsule = EVAL._capsule_envelopes(EVAL._fixture_cases(document))["task"]
        worst_reference = (
            ROOT
            / "src/foundation/capabilities/transaction-consistency/references/benchmarks-and-patterns.md"
        )
        components = [
            EVAL._file_component(
                "worker_profile",
                ROOT / "dist/copilot/project/.github/agents/task-agent.agent.md",
            ),
            compact_source_component(
                "primary_skill",
                ROOT / "src/professional-skills/data-middleware-change-builder/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                "data-middleware-change-builder",
            ),
            *[
                compact_source_component(
                    "layer3",
                    ROOT / "src/foundation/capabilities" / owner / "SKILL.md",
                    BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                    None,
                )
                for owner in expected_layer3
            ],
            EVAL._file_component("layer3_reference", worst_reference),
            capsule,
        ]
        self._assert_semantic_budget_witness(
            components,
            budget_class="task",
            expected_components=[
                (
                    "worker_profile",
                    "dist/copilot/project/.github/agents/task-agent.agent.md",
                ),
                (
                    "primary_skill",
                    "src/professional-skills/data-middleware-change-builder/SKILL.md",
                ),
                *[
                    (
                        "layer3",
                        f"src/foundation/capabilities/{owner}/SKILL.md",
                    )
                    for owner in expected_layer3
                ],
                (
                    "layer3_reference",
                    "src/foundation/capabilities/transaction-consistency/"
                    "references/benchmarks-and-patterns.md",
                ),
                ("dispatch_assignment", capsule["path"]),
            ],
        )

    def test_c1l_data_api_named_task_witness_is_bounded(self) -> None:
        authority = EVAL._selector_authority()
        projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="data-api-contract-changer",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        classes, _inventory, errors = EVAL._admissible_selector_equivalence_classes(
            authority, projection
        )
        self.assertEqual([], errors)
        expected_layer3 = [
            "model-boundary-mapping",
            "sdk-library-contract-design",
            "api-contract-design",
        ]
        selected = next(
            item for item in classes if item["selected_layer3"] == expected_layer3
        )
        self._assert_canonical_runtime_receipt(selected["receipt"])
        self.assertEqual(
            (["accepted-brief", "input-shape-change"], "implementation-risk", "professional-risk"),
            (
                selected["receipt"]["evidence_signals"],
                selected["receipt"]["selection_kind"],
                selected["receipt"]["selection_basis"],
            ),
        )
        selected_owners = {"data-api-contract-changer", *expected_layer3}
        selected_references = [
            (record["owner_skill"], record["path"])
            for record in projection["reference_records"]
            if record["owner_skill"] in selected_owners
        ]
        expected_selected_union = [
            ["data-api-contract-changer", "references/checklist.md"],
            ["data-api-contract-changer", "references/evidence-patterns.md"],
            ["data-api-contract-changer", "references/solution-optimality.md"],
            ["api-contract-design", "references/api-style-and-semantics.md"],
            ["api-contract-design", "references/checklist.md"],
            ["api-contract-design", "references/evidence-patterns.md"],
            ["model-boundary-mapping", "references/benchmarks-and-patterns.md"],
            ["model-boundary-mapping", "references/checklist.md"],
            ["model-boundary-mapping", "references/evidence-patterns.md"],
            ["sdk-library-contract-design", "references/benchmarks-and-patterns.md"],
            ["sdk-library-contract-design", "references/checklist.md"],
            ["sdk-library-contract-design", "references/evidence-patterns.md"],
        ]
        self.assertEqual(
            [tuple(reference) for reference in expected_selected_union],
            selected_references,
        )
        context_authority = EVAL.reference_context_admissibility_authority(
            EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY),
            EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY),
            EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY),
            context="C1L data-api named Task witness",
        )
        staged = EVAL.reference_context_staged_plan(
            context_authority,
            references=selected_references,
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        expected_loaded_union = [list(reference) for reference in sorted(selected_references)]
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected_selected_union, staged["selected_union"])
        self.assertEqual(expected_loaded_union, staged["loaded_union"])
        self.assertEqual(
            {tuple(reference) for reference in expected_selected_union},
            {tuple(reference) for reference in expected_loaded_union},
        )
        self.assertEqual(
            [12, 12, 12, 12],
            [
                len(staged["selected_union"]),
                len(staged["loaded_union"]),
                len(staged["stages"]),
                len(staged["required_output_receipts"]),
            ],
        )
        self.assertEqual(
            expected_loaded_union,
            [stage["loaded_references"][0] for stage in staged["stages"]],
        )
        self.assertTrue(
            all(
                len(stage["loaded_references"]) == 1
                and stage["carried_predecessors"] == []
                for stage in staged["stages"]
            )
        )
        self.assertEqual(
            staged["required_output_receipts"],
            [stage["required_output_receipts"][0] for stage in staged["stages"]],
        )
        active_reference = [
            "sdk-library-contract-design",
            "references/benchmarks-and-patterns.md",
        ]
        active_stage = staged["stages"][9]
        self.assertEqual([active_reference], active_stage["loaded_references"])
        self.assertEqual([], active_stage["carried_predecessors"])
        self.assertEqual(
            [{
                "reference": active_reference,
                "required_outputs": ["option-comparison", "selected-approach"],
            }],
            active_stage["required_output_receipts"],
        )
        self.assertNotEqual(expected_selected_union, expected_selected_union[:-1])
        self.assertNotEqual(expected_loaded_union, expected_loaded_union[:-1])

        def compact_source_component(
            kind: str,
            path: Path,
            headings: tuple[str, ...],
            selector: str | None,
        ) -> dict[str, object]:
            _metadata, raw_frontmatter, body = EVAL.parse_frontmatter(path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            output.append("")
            return EVAL._component(
                kind,
                path.relative_to(ROOT).as_posix(),
                "\n".join(output),
            )

        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        capsule = EVAL._capsule_envelopes(EVAL._fixture_cases(document))["task"]
        components = [
            EVAL._file_component(
                "worker_profile",
                ROOT / "dist/copilot/project/.github/agents/task-agent.agent.md",
            ),
            compact_source_component(
                "primary_skill",
                ROOT / "src/professional-skills/data-api-contract-changer/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                "data-api-contract-changer",
            ),
            *[
                compact_source_component(
                    "layer3",
                    ROOT / "src/foundation/capabilities" / owner / "SKILL.md",
                    BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                    None,
                )
                for owner in expected_layer3
            ],
            EVAL._file_component(
                "layer3_reference",
                ROOT / "src/foundation/capabilities/sdk-library-contract-design/references/benchmarks-and-patterns.md",
            ),
            capsule,
        ]
        self._assert_semantic_budget_witness(
            components,
            budget_class="task",
            expected_components=[
                (
                    "worker_profile",
                    "dist/copilot/project/.github/agents/task-agent.agent.md",
                ),
                (
                    "primary_skill",
                    "src/professional-skills/data-api-contract-changer/SKILL.md",
                ),
                *[
                    (
                        "layer3",
                        f"src/foundation/capabilities/{owner}/SKILL.md",
                    )
                    for owner in expected_layer3
                ],
                (
                    "layer3_reference",
                    "src/foundation/capabilities/sdk-library-contract-design/"
                    "references/benchmarks-and-patterns.md",
                ),
                ("dispatch_assignment", capsule["path"]),
            ],
        )
        self.assertNotEqual(components, components[:-1])


    def test_c1m_security_cloud_tenant_named_task_witness_is_bounded(self) -> None:
        authority = EVAL._selector_authority()
        projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="security-privacy-gate",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        classes, _inventory, errors = EVAL._admissible_selector_equivalence_classes(
            authority, projection
        )
        self.assertEqual([], errors)
        expected_layer3 = [
            "cloud-platform-extension",
            "permission-boundary-modeling",
            "tenant-isolation",
        ]
        selected = next(
            item for item in classes if item["selected_layer3"] == expected_layer3
        )
        self._assert_canonical_runtime_receipt(selected["receipt"])
        self.assertEqual(
            (
                [
                    "cloud control plane",
                    "account authority",
                    "changed-surface",
                    "tenant-isolation",
                ],
                "implementation-risk",
                "professional-risk",
            ),
            (
                selected["receipt"]["evidence_signals"],
                selected["receipt"]["selection_kind"],
                selected["receipt"]["selection_basis"],
            ),
        )
        domain_registry = EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY)
        domain_names = {row["name"] for row in domain_registry["domain_skills"]}
        self.assertEqual(
            ["cloud-platform-extension"],
            [owner for owner in expected_layer3 if owner in domain_names],
        )
        negative_receipt = EVAL.layer3_selector_runtime_selection_receipt(
            projection,
            evidence_signals=[
                "cloud control plane",
                "account authority",
                "changed-surface",
            ],
            build_identity=selected["receipt"]["build"],
        )
        self.assertEqual(
            ["cloud-platform-extension"],
            negative_receipt["selected_layer3"],
        )
        self.assertNotEqual(
            selected["receipt"]["selected_layer3"],
            negative_receipt["selected_layer3"],
        )

        selected_owners = {"security-privacy-gate", *expected_layer3}
        selected_references = [
            (record["owner_skill"], record["path"])
            for record in projection["reference_records"]
            if record["owner_skill"] in selected_owners
        ]
        expected_selected_input = [
            ["security-privacy-gate", "references/checklist.md"],
            ["security-privacy-gate", "references/evidence-patterns.md"],
            ["security-privacy-gate", "references/security-output-and-gates.md"],
            ["permission-boundary-modeling", "references/benchmarks-and-patterns.md"],
            ["permission-boundary-modeling", "references/checklist.md"],
            ["permission-boundary-modeling", "references/evidence-patterns.md"],
            ["cloud-platform-extension", "references/resource-control-and-data-plane-boundaries.md"],
            ["cloud-platform-extension", "references/iam-workload-identity-and-network-contracts.md"],
            ["cloud-platform-extension", "references/region-failure-domain-consistency-and-quota-contracts.md"],
            ["cloud-platform-extension", "references/encryption-kms-and-cost-contracts.md"],
            ["cloud-platform-extension", "references/provider-api-and-managed-service-authority.md"],
            ["tenant-isolation", "references/data-storage-cache-and-search-isolation.md"],
            ["tenant-isolation", "references/async-queue-and-execution-context-isolation.md"],
            ["tenant-isolation", "references/operations-telemetry-and-lifecycle-isolation.md"],
        ]
        self.assertEqual(
            [tuple(reference) for reference in expected_selected_input],
            selected_references,
        )
        context_authority = EVAL.reference_context_admissibility_authority(
            EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY),
            EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY),
            domain_registry,
            context="C1M security cloud tenant named Task witness",
        )
        staged = EVAL.reference_context_staged_plan(
            context_authority,
            references=selected_references,
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        expected_loaded_union = [list(reference) for reference in sorted(selected_references)]
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected_selected_input, staged["selected_union"])
        self.assertEqual(expected_loaded_union, staged["loaded_union"])
        self.assertEqual(
            {tuple(reference) for reference in expected_selected_input},
            {tuple(reference) for reference in expected_loaded_union},
        )
        self.assertEqual(
            [14, 14, 14, 14],
            [
                len(staged["selected_union"]),
                len(staged["loaded_union"]),
                len(staged["stages"]),
                len(staged["required_output_receipts"]),
            ],
        )
        self.assertEqual(
            expected_loaded_union,
            [stage["loaded_references"][0] for stage in staged["stages"]],
        )
        self.assertTrue(
            all(
                len(stage["loaded_references"]) == 1
                and stage["carried_predecessors"] == []
                for stage in staged["stages"]
            )
        )
        self.assertEqual([], staged["carried_predecessors"])
        expected_outputs = {
            ("cloud-platform-extension", "references/encryption-kms-and-cost-contracts.md"): ["boundary-decision", "failure-decision", "residual-risk"],
            ("cloud-platform-extension", "references/iam-workload-identity-and-network-contracts.md"): ["boundary-decision", "failure-decision", "validation-plan"],
            ("cloud-platform-extension", "references/provider-api-and-managed-service-authority.md"): ["decision-record", "proof-limit", "validation-plan"],
            ("cloud-platform-extension", "references/region-failure-domain-consistency-and-quota-contracts.md"): ["decision-record", "proof-limit", "validation-plan"],
            ("cloud-platform-extension", "references/resource-control-and-data-plane-boundaries.md"): ["boundary-decision", "decision-record", "proof-limit"],
            ("permission-boundary-modeling", "references/benchmarks-and-patterns.md"): ["option-comparison", "selected-approach"],
            ("permission-boundary-modeling", "references/checklist.md"): ["checklist-result", "residual-risk"],
            ("permission-boundary-modeling", "references/evidence-patterns.md"): ["evidence-record", "proof-limit", "residual-risk"],
            ("security-privacy-gate", "references/checklist.md"): ["checklist-result", "residual-risk"],
            ("security-privacy-gate", "references/evidence-patterns.md"): ["evidence-record", "proof-limit", "residual-risk"],
            ("security-privacy-gate", "references/security-output-and-gates.md"): ["gate-decision", "residual-risk"],
            ("tenant-isolation", "references/async-queue-and-execution-context-isolation.md"): ["boundary-decision", "validation-plan", "proof-limit"],
            ("tenant-isolation", "references/data-storage-cache-and-search-isolation.md"): ["boundary-decision", "validation-plan", "residual-risk"],
            ("tenant-isolation", "references/operations-telemetry-and-lifecycle-isolation.md"): ["boundary-decision", "validation-plan", "residual-risk"],
        }
        expected_output_receipts = [
            {
                "reference": reference,
                "required_outputs": expected_outputs[tuple(reference)],
            }
            for reference in expected_loaded_union
        ]
        self.assertEqual(expected_output_receipts, staged["required_output_receipts"])
        self.assertEqual(
            expected_output_receipts,
            [stage["required_output_receipts"][0] for stage in staged["stages"]],
        )
        active_reference = [
            "permission-boundary-modeling",
            "references/evidence-patterns.md",
        ]
        active_stage = staged["stages"][7]
        self.assertEqual([active_reference], active_stage["loaded_references"])
        self.assertEqual([], active_stage["carried_predecessors"])
        self.assertEqual(
            [{
                "reference": active_reference,
                "required_outputs": ["evidence-record", "proof-limit", "residual-risk"],
            }],
            active_stage["required_output_receipts"],
        )
        self.assertNotEqual(expected_selected_input, expected_selected_input[:-1])
        self.assertNotEqual(expected_loaded_union, expected_loaded_union[:-1])

        def compact_source_component(
            kind: str,
            path: Path,
            headings: tuple[str, ...],
            selector: str | None,
        ) -> dict[str, object]:
            _metadata, raw_frontmatter, body = EVAL.parse_frontmatter(path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            if selector is not None:
                output.extend([
                    "",
                    "## Layer 3 Delivery",
                    "",
                    "Expanded Layer 3 roots exist only in this temporary stress projection.",
                ])
            output.append("")
            return EVAL._component(
                kind,
                path.relative_to(ROOT).as_posix(),
                "\n".join(output),
            )

        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        capsule = EVAL._capsule_envelopes(EVAL._fixture_cases(document))["task"]
        components = [
            EVAL._file_component(
                "worker_profile",
                ROOT / "dist/copilot/project/.github/agents/task-agent.agent.md",
            ),
            compact_source_component(
                "primary_skill",
                ROOT / "src/professional-skills/security-privacy-gate/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                "security-privacy-gate",
            ),
            compact_source_component(
                "layer3",
                ROOT / "src/domain-extensions/cloud-platform-extension/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                None,
            ),
            *[
                compact_source_component(
                    "layer3",
                    ROOT / "src/foundation/capabilities" / owner / "SKILL.md",
                    BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                    None,
                )
                for owner in expected_layer3[1:]
            ],
            EVAL._file_component(
                "layer3_reference",
                ROOT / "src/foundation/capabilities/permission-boundary-modeling/references/evidence-patterns.md",
            ),
            capsule,
        ]
        self._assert_semantic_budget_witness(
            components,
            budget_class="task",
            expected_components=[
                (
                    "worker_profile",
                    "dist/copilot/project/.github/agents/task-agent.agent.md",
                ),
                (
                    "primary_skill",
                    "src/professional-skills/security-privacy-gate/SKILL.md",
                ),
                (
                    "layer3",
                    "src/domain-extensions/cloud-platform-extension/SKILL.md",
                ),
                *[
                    (
                        "layer3",
                        f"src/foundation/capabilities/{owner}/SKILL.md",
                    )
                    for owner in expected_layer3[1:]
                ],
                (
                    "layer3_reference",
                    "src/foundation/capabilities/permission-boundary-modeling/"
                    "references/evidence-patterns.md",
                ),
                ("dispatch_assignment", capsule["path"]),
            ],
        )
        self.assertNotEqual(components, components[:-1])

    def test_c1n_quality_client_named_task_witness_is_bounded(self) -> None:
        authority = EVAL._selector_authority()
        projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="quality-test-gate",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        classes, _inventory, errors = EVAL._admissible_selector_equivalence_classes(
            authority, projection
        )
        self.assertEqual([], errors)
        expected_layer3 = [
            "test-data-management",
            "client-application-testing",
            "test-strategy",
        ]
        selected = next(
            item for item in classes if item["selected_layer3"] == expected_layer3
        )
        self._assert_canonical_runtime_receipt(selected["receipt"])
        self.assertEqual(
            (
                [
                    "explicit-test-data-decision",
                    "changed installed-client behavior needs lifecycle os integration installation device configuration or accessibility proof",
                    "analysis-action",
                ],
                "implementation-risk",
                "professional-risk",
            ),
            (
                selected["receipt"]["evidence_signals"],
                selected["receipt"]["selection_kind"],
                selected["receipt"]["selection_basis"],
            ),
        )
        domain_registry = EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY)
        domain_names = {row["name"] for row in domain_registry["domain_skills"]}
        self.assertEqual([], [owner for owner in expected_layer3 if owner in domain_names])
        negative_receipt = EVAL.layer3_selector_runtime_selection_receipt(
            projection,
            evidence_signals=["explicit-test-data-decision", "analysis-action"],
            build_identity=selected["receipt"]["build"],
        )
        self.assertNotIn("client-application-testing", negative_receipt["selected_layer3"])
        self.assertNotEqual(
            selected["receipt"]["selected_layer3"],
            negative_receipt["selected_layer3"],
        )

        expected_union = [
            ["client-application-testing", "references/client-test-matrix.md"],
            ["quality-test-gate", "references/checklist.md"],
            ["quality-test-gate", "references/test-output-and-gates.md"],
            ["quality-test-gate", "references/test-structure-boundaries.md"],
            ["test-data-management", "references/benchmarks-and-patterns.md"],
            ["test-data-management", "references/checklist.md"],
            ["test-data-management", "references/evidence-patterns.md"],
            ["test-strategy", "references/benchmarks-and-patterns.md"],
            ["test-strategy", "references/checklist.md"],
            ["test-strategy", "references/evidence-patterns.md"],
        ]
        projection_references = [
            [record["owner_skill"], record["path"]]
            for record in projection["reference_records"]
            if record["owner_skill"] in {"quality-test-gate", *expected_layer3}
        ]
        self.assertEqual(
            {tuple(reference) for reference in expected_union},
            {tuple(reference) for reference in projection_references},
        )
        self.assertEqual(10, len(projection_references))
        context_authority = EVAL.reference_context_admissibility_authority(
            EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY),
            EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY),
            domain_registry,
            context="C1N quality client named Task witness",
        )
        staged = EVAL.reference_context_staged_plan(
            context_authority,
            references=[tuple(reference) for reference in expected_union],
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected_union, staged["selected_union"])
        self.assertEqual(expected_union, staged["loaded_union"])
        self.assertEqual(
            [10, 10, 10, 10],
            [
                len(staged["selected_union"]),
                len(staged["loaded_union"]),
                len(staged["stages"]),
                len(staged["required_output_receipts"]),
            ],
        )
        self.assertEqual(
            expected_union,
            [stage["loaded_references"][0] for stage in staged["stages"]],
        )
        self.assertTrue(
            all(
                len(stage["loaded_references"]) == 1
                and stage["carried_predecessors"] == []
                for stage in staged["stages"]
            )
        )
        self.assertEqual([], staged["carried_predecessors"])
        expected_outputs = {
            ("client-application-testing", "references/client-test-matrix.md"): ["validation-plan", "residual-risk"],
            ("quality-test-gate", "references/checklist.md"): ["checklist-result", "validation-plan"],
            ("quality-test-gate", "references/test-output-and-gates.md"): ["gate-decision", "residual-risk"],
            ("quality-test-gate", "references/test-structure-boundaries.md"): ["validation-plan", "proof-limit"],
            ("test-data-management", "references/benchmarks-and-patterns.md"): ["option-comparison", "selected-approach"],
            ("test-data-management", "references/checklist.md"): ["checklist-result", "residual-risk"],
            ("test-data-management", "references/evidence-patterns.md"): ["evidence-record", "proof-limit", "residual-risk"],
            ("test-strategy", "references/benchmarks-and-patterns.md"): ["option-comparison", "selected-approach"],
            ("test-strategy", "references/checklist.md"): ["checklist-result", "residual-risk"],
            ("test-strategy", "references/evidence-patterns.md"): ["evidence-record", "proof-limit", "residual-risk"],
        }
        expected_receipts = [
            {"reference": reference, "required_outputs": expected_outputs[tuple(reference)]}
            for reference in expected_union
        ]
        self.assertEqual(expected_receipts, staged["required_output_receipts"])
        self.assertEqual(
            expected_receipts,
            [stage["required_output_receipts"][0] for stage in staged["stages"]],
        )
        self.assertEqual(expected_union[0:1], staged["stages"][0]["loaded_references"])
        self.assertEqual(expected_receipts[0:1], staged["stages"][0]["required_output_receipts"])
        self.assertNotEqual(expected_union, expected_union[:-1])

        def source_component(
            kind: str,
            path: Path,
            headings: tuple[str, ...],
            selector: str | None,
            *,
            layer3_delivery: bool = False,
        ) -> dict[str, object]:
            _metadata, raw_frontmatter, body = EVAL.parse_frontmatter(path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            if layer3_delivery:
                output.extend([
                    "",
                    "## Layer 3 Delivery",
                    "",
                    "Expanded Layer 3 roots exist only in this temporary stress projection.",
                ])
            output.append("")
            return EVAL._component(kind, path.relative_to(ROOT).as_posix(), "\n".join(output))

        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        capsule = EVAL._capsule_envelopes(EVAL._fixture_cases(document))["task"]
        components = [
            EVAL._file_component(
                "worker_profile",
                ROOT / "dist/copilot/project/.github/agents/task-agent.agent.md",
            ),
            source_component(
                "primary_skill",
                ROOT / "src/professional-skills/quality-test-gate/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                "quality-test-gate",
                layer3_delivery=True,
            ),
            source_component(
                "layer3",
                ROOT / "src/foundation/capabilities/test-data-management/SKILL.md",
                BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                None,
            ),
            source_component(
                "layer3",
                ROOT / "src/foundation/capabilities/client-application-testing/SKILL.md",
                BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                None,
            ),
            source_component(
                "layer3",
                ROOT / "src/foundation/capabilities/test-strategy/SKILL.md",
                BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                None,
            ),
            EVAL._file_component(
                "layer3_reference",
                ROOT / "src/foundation/capabilities/client-application-testing/references/client-test-matrix.md",
            ),
            capsule,
        ]
        self._assert_semantic_budget_witness(
            components,
            budget_class="task",
            expected_components=[
                (
                    "worker_profile",
                    "dist/copilot/project/.github/agents/task-agent.agent.md",
                ),
                (
                    "primary_skill",
                    "src/professional-skills/quality-test-gate/SKILL.md",
                ),
                *[
                    (
                        "layer3",
                        f"src/foundation/capabilities/{owner}/SKILL.md",
                    )
                    for owner in expected_layer3
                ],
                (
                    "layer3_reference",
                    "src/foundation/capabilities/client-application-testing/"
                    "references/client-test-matrix.md",
                ),
                ("dispatch_assignment", capsule["path"]),
            ],
        )
        self.assertNotEqual(components, components[:-1])


    def test_c1o_platform_infrastructure_named_task_witness_is_bounded(self) -> None:
        authority = EVAL._selector_authority()
        projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="platform-infrastructure-change-builder",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        classes, _inventory, errors = EVAL._admissible_selector_equivalence_classes(
            authority, projection
        )
        self.assertEqual([], errors)
        expected_layer3 = [
            "cloud-platform-extension",
            "configuration-runtime-policy",
            "powershell-professional-usage",
        ]
        selected = next(
            item for item in classes if item["selected_layer3"] == expected_layer3
        )
        self._assert_canonical_runtime_receipt(selected["receipt"])
        self.assertEqual(
            (
                [
                    "cloud control plane",
                    "account authority",
                    "changed-surface",
                    "configuration runtime policy typed config default validation fail fast hot reload feature flag owner expiry cleanup kill switch stale flag mode kind switch tenant user experiment rollout rollback config observability",
                    "powershell pipeline binding errors native exit arguments encoding remoting credentials providers modules or administrative idempotency",
                ],
                "implementation-risk",
                "professional-risk",
            ),
            (
                selected["receipt"]["evidence_signals"],
                selected["receipt"]["selection_kind"],
                selected["receipt"]["selection_basis"],
            ),
        )
        domain_registry = EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY)
        domain_names = {row["name"] for row in domain_registry["domain_skills"]}
        self.assertEqual(
            ["cloud-platform-extension"],
            [owner for owner in expected_layer3 if owner in domain_names],
        )
        negative_receipt = EVAL.layer3_selector_runtime_selection_receipt(
            projection,
            evidence_signals=[
                "cloud control plane",
                "account authority",
                "changed-surface",
                "configuration runtime policy typed config default validation fail fast hot reload feature flag owner expiry cleanup kill switch stale flag mode kind switch tenant user experiment rollout rollback config observability",
            ],
            build_identity=selected["receipt"]["build"],
        )
        self.assertNotIn(
            "powershell-professional-usage",
            negative_receipt["selected_layer3"],
        )
        self.assertNotEqual(
            selected["receipt"]["selected_layer3"],
            negative_receipt["selected_layer3"],
        )

        expected_selected_input = [
            ["platform-infrastructure-change-builder", "references/iac-source-contracts.md"],
            ["platform-infrastructure-change-builder", "references/kubernetes-source-contracts.md"],
            ["powershell-professional-usage", "references/pipeline-error-and-native-contracts.md"],
            ["powershell-professional-usage", "references/remoting-provider-and-administration-contracts.md"],
            ["cloud-platform-extension", "references/resource-control-and-data-plane-boundaries.md"],
            ["cloud-platform-extension", "references/iam-workload-identity-and-network-contracts.md"],
            ["cloud-platform-extension", "references/region-failure-domain-consistency-and-quota-contracts.md"],
            ["cloud-platform-extension", "references/encryption-kms-and-cost-contracts.md"],
            ["cloud-platform-extension", "references/provider-api-and-managed-service-authority.md"],
            ["configuration-runtime-policy", "references/benchmarks-and-patterns.md"],
            ["configuration-runtime-policy", "references/checklist.md"],
            ["configuration-runtime-policy", "references/evidence-patterns.md"],
        ]
        selected_references = [
            [record["owner_skill"], record["path"]]
            for record in projection["reference_records"]
            if record["owner_skill"]
            in {"platform-infrastructure-change-builder", *expected_layer3}
        ]
        self.assertEqual(expected_selected_input, selected_references)
        context_authority = EVAL.reference_context_admissibility_authority(
            EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY),
            EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY),
            domain_registry,
            context="C1O platform infrastructure named Task witness",
        )
        staged = EVAL.reference_context_staged_plan(
            context_authority,
            references=[tuple(reference) for reference in selected_references],
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        expected_loaded_union = [
            ["cloud-platform-extension", "references/encryption-kms-and-cost-contracts.md"],
            ["cloud-platform-extension", "references/iam-workload-identity-and-network-contracts.md"],
            ["cloud-platform-extension", "references/provider-api-and-managed-service-authority.md"],
            ["cloud-platform-extension", "references/region-failure-domain-consistency-and-quota-contracts.md"],
            ["cloud-platform-extension", "references/resource-control-and-data-plane-boundaries.md"],
            ["configuration-runtime-policy", "references/benchmarks-and-patterns.md"],
            ["configuration-runtime-policy", "references/checklist.md"],
            ["configuration-runtime-policy", "references/evidence-patterns.md"],
            ["platform-infrastructure-change-builder", "references/iac-source-contracts.md"],
            ["platform-infrastructure-change-builder", "references/kubernetes-source-contracts.md"],
            ["powershell-professional-usage", "references/pipeline-error-and-native-contracts.md"],
            ["powershell-professional-usage", "references/remoting-provider-and-administration-contracts.md"],
        ]
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected_selected_input, staged["selected_union"])
        self.assertEqual(expected_loaded_union, staged["loaded_union"])
        self.assertEqual(
            {tuple(reference) for reference in expected_selected_input},
            {tuple(reference) for reference in expected_loaded_union},
        )
        self.assertEqual(
            [12, 12, 12, 12],
            [
                len(staged["selected_union"]),
                len(staged["loaded_union"]),
                len(staged["stages"]),
                len(staged["required_output_receipts"]),
            ],
        )
        self.assertEqual(
            expected_loaded_union,
            [stage["loaded_references"][0] for stage in staged["stages"]],
        )
        self.assertTrue(
            all(
                len(stage["loaded_references"]) == 1
                and stage["carried_predecessors"] == []
                for stage in staged["stages"]
            )
        )
        self.assertEqual([], staged["carried_predecessors"])
        expected_outputs = {
            ("cloud-platform-extension", "references/encryption-kms-and-cost-contracts.md"): ["boundary-decision", "failure-decision", "residual-risk"],
            ("cloud-platform-extension", "references/iam-workload-identity-and-network-contracts.md"): ["boundary-decision", "failure-decision", "validation-plan"],
            ("cloud-platform-extension", "references/provider-api-and-managed-service-authority.md"): ["decision-record", "proof-limit", "validation-plan"],
            ("cloud-platform-extension", "references/region-failure-domain-consistency-and-quota-contracts.md"): ["decision-record", "proof-limit", "validation-plan"],
            ("cloud-platform-extension", "references/resource-control-and-data-plane-boundaries.md"): ["boundary-decision", "decision-record", "proof-limit"],
            ("configuration-runtime-policy", "references/benchmarks-and-patterns.md"): ["option-comparison", "selected-approach"],
            ("configuration-runtime-policy", "references/checklist.md"): ["checklist-result", "residual-risk"],
            ("configuration-runtime-policy", "references/evidence-patterns.md"): ["evidence-record", "proof-limit", "residual-risk"],
            ("platform-infrastructure-change-builder", "references/iac-source-contracts.md"): ["proof-limit", "selected-approach", "validation-plan"],
            ("platform-infrastructure-change-builder", "references/kubernetes-source-contracts.md"): ["proof-limit", "selected-approach", "validation-plan"],
            ("powershell-professional-usage", "references/pipeline-error-and-native-contracts.md"): ["decision-record", "residual-risk"],
            ("powershell-professional-usage", "references/remoting-provider-and-administration-contracts.md"): ["selected-approach", "proof-limit", "residual-risk"],
        }
        expected_receipts = [
            {
                "reference": reference,
                "required_outputs": expected_outputs[tuple(reference)],
            }
            for reference in expected_loaded_union
        ]
        self.assertEqual(expected_receipts, staged["required_output_receipts"])
        self.assertEqual(
            expected_receipts,
            [stage["required_output_receipts"][0] for stage in staged["stages"]],
        )
        active_reference = [
            "powershell-professional-usage",
            "references/remoting-provider-and-administration-contracts.md",
        ]
        active_stage = staged["stages"][11]
        self.assertEqual([active_reference], active_stage["loaded_references"])
        self.assertEqual([], active_stage["carried_predecessors"])
        self.assertEqual(
            [{
                "reference": active_reference,
                "required_outputs": ["selected-approach", "proof-limit", "residual-risk"],
            }],
            active_stage["required_output_receipts"],
        )
        self.assertNotEqual(expected_selected_input, expected_selected_input[:-1])
        self.assertNotEqual(expected_loaded_union, expected_loaded_union[:-1])

        def source_component(
            kind: str,
            path: Path,
            headings: tuple[str, ...],
            selector: str | None,
            *,
            layer3_delivery: bool = False,
        ) -> dict[str, object]:
            _metadata, raw_frontmatter, body = EVAL.parse_frontmatter(path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            if layer3_delivery:
                output.extend([
                    "",
                    "## Layer 3 Delivery",
                    "",
                    "Expanded Layer 3 roots exist only in this temporary stress projection.",
                ])
            output.append("")
            return EVAL._component(
                kind,
                path.relative_to(ROOT).as_posix(),
                "\n".join(output),
            )

        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        capsule = EVAL._capsule_envelopes(EVAL._fixture_cases(document))["task"]
        components = [
            EVAL._file_component(
                "worker_profile",
                ROOT / "dist/copilot/project/.github/agents/task-agent.agent.md",
            ),
            source_component(
                "primary_skill",
                ROOT / "src/professional-skills/platform-infrastructure-change-builder/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                "platform-infrastructure-change-builder",
                layer3_delivery=True,
            ),
            source_component(
                "layer3",
                ROOT / "src/domain-extensions/cloud-platform-extension/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                None,
            ),
            source_component(
                "layer3",
                ROOT / "src/foundation/capabilities/configuration-runtime-policy/SKILL.md",
                BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                None,
            ),
            source_component(
                "layer3",
                ROOT / "src/foundation/capabilities/powershell-professional-usage/SKILL.md",
                BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                None,
            ),
            EVAL._file_component(
                "layer3_reference",
                ROOT / "src/foundation/capabilities/powershell-professional-usage/references/remoting-provider-and-administration-contracts.md",
            ),
            capsule,
        ]
        self._assert_semantic_budget_witness(
            components,
            budget_class="task",
            expected_components=[
                (
                    "worker_profile",
                    "dist/copilot/project/.github/agents/task-agent.agent.md",
                ),
                (
                    "primary_skill",
                    "src/professional-skills/platform-infrastructure-change-builder/"
                    "SKILL.md",
                ),
                (
                    "layer3",
                    "src/domain-extensions/cloud-platform-extension/SKILL.md",
                ),
                (
                    "layer3",
                    "src/foundation/capabilities/configuration-runtime-policy/"
                    "SKILL.md",
                ),
                (
                    "layer3",
                    "src/foundation/capabilities/powershell-professional-usage/"
                    "SKILL.md",
                ),
                (
                    "layer3_reference",
                    "src/foundation/capabilities/powershell-professional-usage/"
                    "references/remoting-provider-and-administration-contracts.md",
                ),
                ("dispatch_assignment", capsule["path"]),
            ],
        )
        self.assertNotEqual(components, components[:-1])

    def test_fg_c1p_platform_iac_safety_named_task_witness_is_bounded(self) -> None:
        authority = EVAL._selector_authority()
        projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="platform-infrastructure-change-builder",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        classes, _inventory, errors = EVAL._admissible_selector_equivalence_classes(
            authority, projection
        )
        self.assertEqual([], errors)
        expected_layer3 = [
            "cloud-platform-extension",
            "configuration-runtime-policy",
            "infrastructure-as-code-safety",
        ]
        selected = next(
            item for item in classes if item["selected_layer3"] == expected_layer3
        )
        expected_signals = [
            "cloud control plane",
            "account authority",
            "changed-surface",
            "configuration runtime policy typed config default validation fail fast hot reload feature flag owner expiry cleanup kill switch stale flag mode kind switch tenant user experiment rollout rollback config observability",
            "desired-state infrastructure source with state identity drift destruction or recovery",
        ]
        self._assert_canonical_runtime_receipt(selected["receipt"])
        self.assertEqual(
            (
                expected_signals,
                "implementation-risk",
                "professional-risk",
            ),
            (
                selected["receipt"]["evidence_signals"],
                selected["receipt"]["selection_kind"],
                selected["receipt"]["selection_basis"],
            ),
        )
        domain_registry = EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY)
        domain_names = {row["name"] for row in domain_registry["domain_skills"]}
        self.assertEqual(
            ["cloud-platform-extension"],
            [owner for owner in expected_layer3 if owner in domain_names],
        )
        negative_receipt = EVAL.layer3_selector_runtime_selection_receipt(
            projection,
            evidence_signals=expected_signals[:-1],
            build_identity=selected["receipt"]["build"],
        )
        self.assertNotIn(
            "infrastructure-as-code-safety",
            negative_receipt["selected_layer3"],
        )
        self.assertNotEqual(
            selected["receipt"]["selected_layer3"],
            negative_receipt["selected_layer3"],
        )

        expected_selected_input = [
            ["platform-infrastructure-change-builder", "references/iac-source-contracts.md"],
            ["platform-infrastructure-change-builder", "references/kubernetes-source-contracts.md"],
            ["infrastructure-as-code-safety", "references/state-plan-and-drift-contracts.md"],
            ["infrastructure-as-code-safety", "references/identity-destruction-and-recovery-contracts.md"],
            ["cloud-platform-extension", "references/resource-control-and-data-plane-boundaries.md"],
            ["cloud-platform-extension", "references/iam-workload-identity-and-network-contracts.md"],
            ["cloud-platform-extension", "references/region-failure-domain-consistency-and-quota-contracts.md"],
            ["cloud-platform-extension", "references/encryption-kms-and-cost-contracts.md"],
            ["cloud-platform-extension", "references/provider-api-and-managed-service-authority.md"],
            ["configuration-runtime-policy", "references/benchmarks-and-patterns.md"],
            ["configuration-runtime-policy", "references/checklist.md"],
            ["configuration-runtime-policy", "references/evidence-patterns.md"],
        ]
        selected_references = [
            [record["owner_skill"], record["path"]]
            for record in projection["reference_records"]
            if record["owner_skill"]
            in {"platform-infrastructure-change-builder", *expected_layer3}
        ]
        self.assertEqual(expected_selected_input, selected_references)
        context_authority = EVAL.reference_context_admissibility_authority(
            EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY),
            EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY),
            domain_registry,
            context="C1P platform IaC safety named Task witness",
        )
        staged = EVAL.reference_context_staged_plan(
            context_authority,
            references=[tuple(reference) for reference in selected_references],
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        expected_loaded_union = [
            ["cloud-platform-extension", "references/encryption-kms-and-cost-contracts.md"],
            ["cloud-platform-extension", "references/iam-workload-identity-and-network-contracts.md"],
            ["cloud-platform-extension", "references/provider-api-and-managed-service-authority.md"],
            ["cloud-platform-extension", "references/region-failure-domain-consistency-and-quota-contracts.md"],
            ["cloud-platform-extension", "references/resource-control-and-data-plane-boundaries.md"],
            ["configuration-runtime-policy", "references/benchmarks-and-patterns.md"],
            ["configuration-runtime-policy", "references/checklist.md"],
            ["configuration-runtime-policy", "references/evidence-patterns.md"],
            ["infrastructure-as-code-safety", "references/identity-destruction-and-recovery-contracts.md"],
            ["infrastructure-as-code-safety", "references/state-plan-and-drift-contracts.md"],
            ["platform-infrastructure-change-builder", "references/iac-source-contracts.md"],
            ["platform-infrastructure-change-builder", "references/kubernetes-source-contracts.md"],
        ]
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected_selected_input, staged["selected_union"])
        self.assertEqual(expected_loaded_union, staged["loaded_union"])
        self.assertEqual(
            {tuple(reference) for reference in expected_selected_input},
            {tuple(reference) for reference in expected_loaded_union},
        )
        self.assertEqual(
            [12, 12, 12, 12],
            [
                len(staged["selected_union"]),
                len(staged["loaded_union"]),
                len(staged["stages"]),
                len(staged["required_output_receipts"]),
            ],
        )
        self.assertEqual(
            expected_loaded_union,
            [stage["loaded_references"][0] for stage in staged["stages"]],
        )
        self.assertTrue(
            all(
                len(stage["loaded_references"]) == 1
                and stage["carried_predecessors"] == []
                for stage in staged["stages"]
            )
        )
        self.assertEqual([], staged["carried_predecessors"])
        expected_outputs = {
            ("cloud-platform-extension", "references/encryption-kms-and-cost-contracts.md"): ["boundary-decision", "failure-decision", "residual-risk"],
            ("cloud-platform-extension", "references/iam-workload-identity-and-network-contracts.md"): ["boundary-decision", "failure-decision", "validation-plan"],
            ("cloud-platform-extension", "references/provider-api-and-managed-service-authority.md"): ["decision-record", "proof-limit", "validation-plan"],
            ("cloud-platform-extension", "references/region-failure-domain-consistency-and-quota-contracts.md"): ["decision-record", "proof-limit", "validation-plan"],
            ("cloud-platform-extension", "references/resource-control-and-data-plane-boundaries.md"): ["boundary-decision", "decision-record", "proof-limit"],
            ("configuration-runtime-policy", "references/benchmarks-and-patterns.md"): ["option-comparison", "selected-approach"],
            ("configuration-runtime-policy", "references/checklist.md"): ["checklist-result", "residual-risk"],
            ("configuration-runtime-policy", "references/evidence-patterns.md"): ["evidence-record", "proof-limit", "residual-risk"],
            ("infrastructure-as-code-safety", "references/identity-destruction-and-recovery-contracts.md"): ["decision-record", "proof-limit", "residual-risk"],
            ("infrastructure-as-code-safety", "references/state-plan-and-drift-contracts.md"): ["decision-record", "proof-limit", "residual-risk"],
            ("platform-infrastructure-change-builder", "references/iac-source-contracts.md"): ["proof-limit", "selected-approach", "validation-plan"],
            ("platform-infrastructure-change-builder", "references/kubernetes-source-contracts.md"): ["proof-limit", "selected-approach", "validation-plan"],
        }
        expected_receipts = [
            {
                "reference": reference,
                "required_outputs": expected_outputs[tuple(reference)],
            }
            for reference in expected_loaded_union
        ]
        self.assertEqual(expected_receipts, staged["required_output_receipts"])
        self.assertEqual(
            expected_receipts,
            [stage["required_output_receipts"][0] for stage in staged["stages"]],
        )
        active_reference = [
            "infrastructure-as-code-safety",
            "references/identity-destruction-and-recovery-contracts.md",
        ]
        active_stage = staged["stages"][8]
        self.assertEqual([active_reference], active_stage["loaded_references"])
        self.assertEqual([], active_stage["carried_predecessors"])
        self.assertEqual(
            [{
                "reference": active_reference,
                "required_outputs": ["decision-record", "proof-limit", "residual-risk"],
            }],
            active_stage["required_output_receipts"],
        )
        self.assertNotEqual(expected_selected_input, expected_selected_input[:-1])
        self.assertNotEqual(expected_loaded_union, expected_loaded_union[:-1])

        def source_component(
            kind: str,
            path: Path,
            headings: tuple[str, ...],
            selector: str | None,
            *,
            layer3_delivery: bool = False,
        ) -> dict[str, object]:
            _metadata, raw_frontmatter, body = EVAL.parse_frontmatter(path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            if layer3_delivery:
                output.extend([
                    "",
                    "## Layer 3 Delivery",
                    "",
                    "Expanded Layer 3 roots exist only in this temporary stress projection.",
                ])
            output.append("")
            return EVAL._component(
                kind,
                path.relative_to(ROOT).as_posix(),
                "\n".join(output),
            )

        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        capsule = EVAL._capsule_envelopes(EVAL._fixture_cases(document))["task"]
        components = [
            EVAL._file_component(
                "worker_profile",
                ROOT / "dist/copilot/project/.github/agents/task-agent.agent.md",
            ),
            source_component(
                "primary_skill",
                ROOT / "src/professional-skills/platform-infrastructure-change-builder/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                "platform-infrastructure-change-builder",
                layer3_delivery=True,
            ),
            source_component(
                "layer3",
                ROOT / "src/domain-extensions/cloud-platform-extension/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                None,
            ),
            source_component(
                "layer3",
                ROOT / "src/foundation/capabilities/configuration-runtime-policy/SKILL.md",
                BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                None,
            ),
            source_component(
                "layer3",
                ROOT / "src/foundation/capabilities/infrastructure-as-code-safety/SKILL.md",
                BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                None,
            ),
            EVAL._file_component(
                "layer3_reference",
                ROOT / "src/foundation/capabilities/infrastructure-as-code-safety/references/identity-destruction-and-recovery-contracts.md",
            ),
            capsule,
        ]
        self._assert_semantic_budget_witness(
            components,
            budget_class="task",
            expected_components=[
                (
                    "worker_profile",
                    "dist/copilot/project/.github/agents/task-agent.agent.md",
                ),
                (
                    "primary_skill",
                    "src/professional-skills/platform-infrastructure-change-builder/"
                    "SKILL.md",
                ),
                (
                    "layer3",
                    "src/domain-extensions/cloud-platform-extension/SKILL.md",
                ),
                (
                    "layer3",
                    "src/foundation/capabilities/configuration-runtime-policy/"
                    "SKILL.md",
                ),
                (
                    "layer3",
                    "src/foundation/capabilities/infrastructure-as-code-safety/"
                    "SKILL.md",
                ),
                (
                    "layer3_reference",
                    "src/foundation/capabilities/infrastructure-as-code-safety/"
                    "references/identity-destruction-and-recovery-contracts.md",
                ),
                ("dispatch_assignment", capsule["path"]),
            ],
        )
        negative = copy.deepcopy(components)
        negative[5]["tokens"] += (
            EVAL.CONTEXT_BUDGET_LIMITS["task"]["soft_target"]
            + 1
            - EVAL._component_upper_bound(negative)
        )
        self.assertEqual(
            EVAL.CONTEXT_BUDGET_LIMITS["task"]["soft_target"] + 1,
            EVAL._component_upper_bound(negative),
        )
        self.assertNotEqual(components, components[:-1])

    def test_fg_c1q_data_middleware_named_task_witness_is_bounded(self) -> None:
        authority = EVAL._selector_authority()
        projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="data-middleware-change-builder",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        classes, _inventory, errors = EVAL._admissible_selector_equivalence_classes(
            authority, projection
        )
        self.assertEqual([], errors)
        expected_layer3 = [
            "data-migration-design",
            "transaction-consistency",
            "distributed-workflow-consistency",
        ]
        selected = next(
            item for item in classes if item["selected_layer3"] == expected_layer3
        )
        expected_signals = ["database-migration", "distributed-effect-change"]
        self._assert_canonical_runtime_receipt(selected["receipt"])
        self.assertEqual(
            (
                expected_signals,
                "implementation-risk",
                "professional-risk",
            ),
            (
                selected["receipt"]["evidence_signals"],
                selected["receipt"]["selection_kind"],
                selected["receipt"]["selection_basis"],
            ),
        )
        domain_names = {
            row["name"]
            for row in EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY)["domain_skills"]
        }
        self.assertEqual([], [name for name in expected_layer3 if name in domain_names])
        negative_receipt = EVAL.layer3_selector_runtime_selection_receipt(
            projection,
            evidence_signals=expected_signals[:-1],
            build_identity=selected["receipt"]["build"],
        )
        self.assertNotIn("distributed-workflow-consistency", negative_receipt["selected_layer3"])
        self.assertNotEqual(selected["receipt"]["selected_layer3"], negative_receipt["selected_layer3"])

        expected_selected = [
            ["data-middleware-change-builder", "references/checklist.md"],
            ["data-middleware-change-builder", "references/evidence-patterns.md"],
            ["data-middleware-change-builder", "references/recovery-patterns.md"],
            ["data-migration-design", "references/benchmarks-and-patterns.md"],
            ["data-migration-design", "references/checklist.md"],
            ["data-migration-design", "references/evidence-patterns.md"],
            ["transaction-consistency", "references/benchmarks-and-patterns.md"],
            ["transaction-consistency", "references/checklist.md"],
            ["transaction-consistency", "references/evidence-patterns.md"],
            ["distributed-workflow-consistency", "references/identity-state-and-unknown-outcomes.md"],
            ["distributed-workflow-consistency", "references/compensation-convergence-and-reconciliation.md"],
            ["distributed-workflow-consistency", "references/stuck-manual-repair-and-versioning.md"],
        ]
        selected_references = [
            [record["owner_skill"], record["path"]]
            for record in projection["reference_records"]
            if record["owner_skill"] in {"data-middleware-change-builder", *expected_layer3}
        ]
        self.assertEqual(expected_selected, selected_references)
        context_authority = EVAL.reference_context_admissibility_authority(
            EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY),
            EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY),
            EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY),
            context="C1Q data middleware named Task witness",
        )
        staged = EVAL.reference_context_staged_plan(
            context_authority,
            references=[tuple(reference) for reference in selected_references],
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        expected_loaded = [
            ["data-middleware-change-builder", "references/checklist.md"],
            ["data-middleware-change-builder", "references/evidence-patterns.md"],
            ["data-middleware-change-builder", "references/recovery-patterns.md"],
            ["data-migration-design", "references/benchmarks-and-patterns.md"],
            ["data-migration-design", "references/checklist.md"],
            ["data-migration-design", "references/evidence-patterns.md"],
            ["distributed-workflow-consistency", "references/compensation-convergence-and-reconciliation.md"],
            ["distributed-workflow-consistency", "references/identity-state-and-unknown-outcomes.md"],
            ["distributed-workflow-consistency", "references/stuck-manual-repair-and-versioning.md"],
            ["transaction-consistency", "references/benchmarks-and-patterns.md"],
            ["transaction-consistency", "references/checklist.md"],
            ["transaction-consistency", "references/evidence-patterns.md"],
        ]
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected_selected, staged["selected_union"])
        self.assertEqual(expected_loaded, staged["loaded_union"])
        self.assertEqual({tuple(x) for x in expected_selected}, {tuple(x) for x in expected_loaded})
        self.assertEqual([12, 12, 12, 12], [len(staged[key]) for key in ("selected_union", "loaded_union", "stages", "required_output_receipts")])
        self.assertEqual(expected_loaded, [stage["loaded_references"][0] for stage in staged["stages"]])
        self.assertTrue(all(len(stage["loaded_references"]) == 1 and stage["carried_predecessors"] == [] for stage in staged["stages"]))
        self.assertEqual([], staged["carried_predecessors"])
        outputs = {
            ("data-middleware-change-builder", "references/checklist.md"): ["checklist-result", "residual-risk"],
            ("data-middleware-change-builder", "references/evidence-patterns.md"): ["evidence-record", "proof-limit", "residual-risk"],
            ("data-middleware-change-builder", "references/recovery-patterns.md"): ["option-comparison", "selected-approach"],
            ("data-migration-design", "references/benchmarks-and-patterns.md"): ["option-comparison", "selected-approach"],
            ("data-migration-design", "references/checklist.md"): ["checklist-result", "residual-risk"],
            ("data-migration-design", "references/evidence-patterns.md"): ["evidence-record", "proof-limit", "residual-risk"],
            ("distributed-workflow-consistency", "references/compensation-convergence-and-reconciliation.md"): ["failure-decision", "selected-approach", "residual-risk"],
            ("distributed-workflow-consistency", "references/identity-state-and-unknown-outcomes.md"): ["boundary-decision", "failure-decision", "proof-limit"],
            ("distributed-workflow-consistency", "references/stuck-manual-repair-and-versioning.md"): ["failure-decision", "validation-plan", "proof-limit"],
            ("transaction-consistency", "references/benchmarks-and-patterns.md"): ["option-comparison", "selected-approach"],
            ("transaction-consistency", "references/checklist.md"): ["checklist-result", "residual-risk"],
            ("transaction-consistency", "references/evidence-patterns.md"): ["evidence-record", "proof-limit", "residual-risk"],
        }
        receipts = [{"reference": reference, "required_outputs": outputs[tuple(reference)]} for reference in expected_loaded]
        self.assertEqual(receipts, staged["required_output_receipts"])
        self.assertEqual(receipts, [stage["required_output_receipts"][0] for stage in staged["stages"]])
        active = ["data-migration-design", "references/evidence-patterns.md"]
        self.assertEqual(
            ([active], [], [{"reference": active, "required_outputs": ["evidence-record", "proof-limit", "residual-risk"]}]),
            (staged["stages"][5]["loaded_references"], staged["stages"][5]["carried_predecessors"], staged["stages"][5]["required_output_receipts"]),
        )
        self.assertNotEqual(expected_selected, expected_selected[:-1])
        self.assertNotEqual(expected_loaded, expected_loaded[:-1])

        def source_component(kind: str, path: Path, headings: tuple[str, ...], selector: str | None, *, layer3_delivery: bool = False) -> dict[str, object]:
            _metadata, raw_frontmatter, body = EVAL.parse_frontmatter(path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            if layer3_delivery:
                output.extend(["", "## Layer 3 Delivery", "", "Expanded Layer 3 roots exist only in this temporary stress projection."])
            output.append("")
            return EVAL._component(kind, path.relative_to(ROOT).as_posix(), "\n".join(output))

        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        capsule = EVAL._capsule_envelopes(EVAL._fixture_cases(document))["task"]
        components = [
            EVAL._file_component("worker_profile", ROOT / "dist/copilot/project/.github/agents/task-agent.agent.md"),
            source_component("primary_skill", ROOT / "src/professional-skills/data-middleware-change-builder/SKILL.md", BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS, "data-middleware-change-builder", layer3_delivery=True),
            source_component("layer3", ROOT / "src/foundation/capabilities/data-migration-design/SKILL.md", BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS, None),
            source_component("layer3", ROOT / "src/foundation/capabilities/transaction-consistency/SKILL.md", BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS, None),
            source_component("layer3", ROOT / "src/foundation/capabilities/distributed-workflow-consistency/SKILL.md", BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS, None),
            EVAL._file_component("layer3_reference", ROOT / "src/foundation/capabilities/data-migration-design/references/evidence-patterns.md"),
            capsule,
        ]
        self._assert_semantic_budget_witness(
            components,
            budget_class="task",
            expected_components=[
                (
                    "worker_profile",
                    "dist/copilot/project/.github/agents/task-agent.agent.md",
                ),
                (
                    "primary_skill",
                    "src/professional-skills/data-middleware-change-builder/SKILL.md",
                ),
                *[
                    (
                        "layer3",
                        f"src/foundation/capabilities/{owner}/SKILL.md",
                    )
                    for owner in expected_layer3
                ],
                (
                    "layer3_reference",
                    "src/foundation/capabilities/data-migration-design/"
                    "references/evidence-patterns.md",
                ),
                ("dispatch_assignment", capsule["path"]),
            ],
        )
        negative = copy.deepcopy(components)
        negative[5]["tokens"] += (
            EVAL.CONTEXT_BUDGET_LIMITS["task"]["soft_target"]
            + 1
            - EVAL._component_upper_bound(negative)
        )
        self.assertEqual(
            EVAL.CONTEXT_BUDGET_LIMITS["task"]["soft_target"] + 1,
            EVAL._component_upper_bound(negative),
        )
        self.assertNotEqual(components, components[:-1])

    def test_fg_c1r_delivery_release_iot_named_task_witness_is_bounded(self) -> None:
        authority = EVAL._selector_authority()
        projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="delivery-release-gate",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        classes, _inventory, errors = EVAL._admissible_selector_equivalence_classes(
            authority, projection
        )
        self.assertEqual([], errors)
        expected_layer3 = [
            "iot-embedded-extension",
            "release-rollback",
            "version-compatibility",
        ]
        selected = next(
            item for item in classes if item["selected_layer3"] == expected_layer3
        )
        expected_signals = [
            "device",
            "recovery",
            "changed-surface",
            "production-apply-or-rollout",
        ]
        self._assert_canonical_runtime_receipt(selected["receipt"])
        self.assertEqual(
            (
                expected_signals,
                "implementation-risk",
                "professional-risk",
            ),
            (
                selected["receipt"]["evidence_signals"],
                selected["receipt"]["selection_kind"],
                selected["receipt"]["selection_basis"],
            ),
        )
        domain_names = {
            row["name"]
            for row in EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY)["domain_skills"]
        }
        self.assertEqual(
            ["iot-embedded-extension"],
            [name for name in expected_layer3 if name in domain_names],
        )
        negative_receipt = EVAL.layer3_selector_runtime_selection_receipt(
            projection,
            evidence_signals=expected_signals[1:],
            build_identity=selected["receipt"]["build"],
        )
        self.assertNotIn(
            "iot-embedded-extension", negative_receipt["selected_layer3"]
        )
        self.assertNotEqual(
            selected["receipt"]["selected_layer3"],
            negative_receipt["selected_layer3"],
        )

        expected_selected = [
            ["delivery-release-gate", "references/checklist.md"],
            ["delivery-release-gate", "references/delivery-output-and-gates.md"],
            ["delivery-release-gate", "references/release-evidence-patterns.md"],
            ["release-rollback", "references/benchmarks-and-patterns.md"],
            ["release-rollback", "references/checklist.md"],
            ["release-rollback", "references/evidence-patterns.md"],
            ["version-compatibility", "references/checklist.md"],
            ["version-compatibility", "references/compatibility-benchmarks.md"],
            ["version-compatibility", "references/evidence-patterns.md"],
            ["iot-embedded-extension", "references/checklist.md"],
        ]
        selected_references = [
            [record["owner_skill"], record["path"]]
            for record in projection["reference_records"]
            if record["owner_skill"]
            in {"delivery-release-gate", *expected_layer3}
        ]
        self.assertEqual(expected_selected, selected_references)
        context_authority = EVAL.reference_context_admissibility_authority(
            EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY),
            EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY),
            EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY),
            context="C1R delivery release IoT named Task witness",
        )
        staged = EVAL.reference_context_staged_plan(
            context_authority,
            references=[tuple(reference) for reference in selected_references],
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        expected_loaded = [
            ["delivery-release-gate", "references/checklist.md"],
            ["delivery-release-gate", "references/delivery-output-and-gates.md"],
            ["delivery-release-gate", "references/release-evidence-patterns.md"],
            ["iot-embedded-extension", "references/checklist.md"],
            ["release-rollback", "references/benchmarks-and-patterns.md"],
            ["release-rollback", "references/checklist.md"],
            ["release-rollback", "references/evidence-patterns.md"],
            ["version-compatibility", "references/checklist.md"],
            ["version-compatibility", "references/compatibility-benchmarks.md"],
            ["version-compatibility", "references/evidence-patterns.md"],
        ]
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected_selected, staged["selected_union"])
        self.assertEqual(expected_loaded, staged["loaded_union"])
        self.assertEqual(
            {tuple(reference) for reference in expected_selected},
            {tuple(reference) for reference in expected_loaded},
        )
        self.assertEqual(
            [10, 10, 10, 10],
            [
                len(staged["selected_union"]),
                len(staged["loaded_union"]),
                len(staged["stages"]),
                len(staged["required_output_receipts"]),
            ],
        )
        self.assertEqual(
            expected_loaded,
            [stage["loaded_references"][0] for stage in staged["stages"]],
        )
        self.assertTrue(
            all(
                len(stage["loaded_references"]) == 1
                and stage["carried_predecessors"] == []
                for stage in staged["stages"]
            )
        )
        self.assertEqual([], staged["carried_predecessors"])
        outputs = {
            ("delivery-release-gate", "references/checklist.md"): ["checklist-result", "residual-risk"],
            ("delivery-release-gate", "references/delivery-output-and-gates.md"): ["gate-decision", "residual-risk"],
            ("delivery-release-gate", "references/release-evidence-patterns.md"): ["evidence-record", "proof-limit", "residual-risk"],
            ("iot-embedded-extension", "references/checklist.md"): ["checklist-result", "residual-risk"],
            ("release-rollback", "references/benchmarks-and-patterns.md"): ["option-comparison", "selected-approach"],
            ("release-rollback", "references/checklist.md"): ["checklist-result", "residual-risk"],
            ("release-rollback", "references/evidence-patterns.md"): ["evidence-record", "proof-limit", "residual-risk"],
            ("version-compatibility", "references/checklist.md"): ["checklist-result", "residual-risk"],
            ("version-compatibility", "references/compatibility-benchmarks.md"): ["option-comparison", "selected-approach"],
            ("version-compatibility", "references/evidence-patterns.md"): ["evidence-record", "proof-limit", "residual-risk"],
        }
        receipts = [
            {"reference": reference, "required_outputs": outputs[tuple(reference)]}
            for reference in expected_loaded
        ]
        self.assertEqual(receipts, staged["required_output_receipts"])
        self.assertEqual(
            receipts,
            [stage["required_output_receipts"][0] for stage in staged["stages"]],
        )
        active = ["iot-embedded-extension", "references/checklist.md"]
        self.assertEqual(
            (
                [active],
                [],
                [{
                    "reference": active,
                    "required_outputs": ["checklist-result", "residual-risk"],
                }],
            ),
            (
                staged["stages"][3]["loaded_references"],
                staged["stages"][3]["carried_predecessors"],
                staged["stages"][3]["required_output_receipts"],
            ),
        )
        self.assertNotEqual(expected_selected, expected_selected[:-1])
        self.assertNotEqual(expected_loaded, expected_loaded[:-1])

        owner_roots = {
            "delivery-release-gate": ROOT / "src/professional-skills/delivery-release-gate",
            "iot-embedded-extension": ROOT / "src/domain-extensions/iot-embedded-extension",
            "release-rollback": ROOT / "src/foundation/capabilities/release-rollback",
            "version-compatibility": ROOT / "src/foundation/capabilities/version-compatibility",
        }
        reference_components = [
            EVAL._file_component(
                "layer3_reference", owner_roots[owner] / relative_path
            )
            for owner, relative_path in [tuple(reference) for reference in expected_selected]
        ]
        self.assertEqual(10, len(reference_components))
        self.assertTrue(all(item["_text"].strip() for item in reference_components))

        def source_component(
            kind: str,
            path: Path,
            headings: tuple[str, ...],
            selector: str | None,
            *,
            layer3_delivery: bool = False,
        ) -> dict[str, object]:
            _metadata, raw_frontmatter, body = EVAL.parse_frontmatter(path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            if layer3_delivery:
                output.extend([
                    "",
                    "## Layer 3 Delivery",
                    "",
                    "Expanded Layer 3 roots exist only in this temporary stress projection.",
                ])
            output.append("")
            return EVAL._component(
                kind, path.relative_to(ROOT).as_posix(), "\n".join(output)
            )

        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        capsule = EVAL._capsule_envelopes(EVAL._fixture_cases(document))["task"]
        components = [
            EVAL._file_component(
                "worker_profile",
                ROOT / "dist/copilot/project/.github/agents/task-agent.agent.md",
            ),
            source_component(
                "primary_skill",
                ROOT / "src/professional-skills/delivery-release-gate/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                "delivery-release-gate",
                layer3_delivery=True,
            ),
            source_component(
                "layer3",
                ROOT / "src/domain-extensions/iot-embedded-extension/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                None,
            ),
            source_component(
                "layer3",
                ROOT / "src/foundation/capabilities/release-rollback/SKILL.md",
                BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                None,
            ),
            source_component(
                "layer3",
                ROOT / "src/foundation/capabilities/version-compatibility/SKILL.md",
                BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                None,
            ),
            EVAL._file_component(
                "layer3_reference",
                ROOT / "src/domain-extensions/iot-embedded-extension/references/checklist.md",
            ),
            capsule,
        ]
        self._assert_semantic_budget_witness(
            components,
            budget_class="task",
            expected_components=[
                (
                    "worker_profile",
                    "dist/copilot/project/.github/agents/task-agent.agent.md",
                ),
                (
                    "primary_skill",
                    "src/professional-skills/delivery-release-gate/SKILL.md",
                ),
                (
                    "layer3",
                    "src/domain-extensions/iot-embedded-extension/SKILL.md",
                ),
                (
                    "layer3",
                    "src/foundation/capabilities/release-rollback/SKILL.md",
                ),
                (
                    "layer3",
                    "src/foundation/capabilities/version-compatibility/SKILL.md",
                ),
                (
                    "layer3_reference",
                    "src/domain-extensions/iot-embedded-extension/"
                    "references/checklist.md",
                ),
                ("dispatch_assignment", capsule["path"]),
            ],
        )
        negative = copy.deepcopy(components)
        negative[5]["tokens"] += (
            EVAL.CONTEXT_BUDGET_LIMITS["task"]["soft_target"]
            + 1
            - EVAL._component_upper_bound(negative)
        )
        self.assertEqual(
            EVAL.CONTEXT_BUDGET_LIMITS["task"]["soft_target"] + 1,
            EVAL._component_upper_bound(negative),
        )
        self.assertNotEqual(components, components[:-1])

    def test_fg_c1s_security_web_named_task_witness_is_bounded(self) -> None:
        authority = EVAL._selector_authority()
        projection = EVAL.layer3_selector_runtime_projection(
            authority,
            professional_skill="security-privacy-gate",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        classes, _inventory, errors = EVAL._admissible_selector_equivalence_classes(
            authority, projection
        )
        self.assertEqual([], errors)
        expected_layer3 = [
            "cloud-platform-extension",
            "threat-modeling",
            "web-security",
        ]
        selected = next(
            item for item in classes if item["selected_layer3"] == expected_layer3
        )
        expected_signals = [
            "cloud control plane",
            "account authority",
            "changed-surface",
            "ssrf",
        ]
        self._assert_canonical_runtime_receipt(selected["receipt"])
        self.assertEqual(
            (
                expected_signals,
                "implementation-risk",
                "professional-risk",
            ),
            (
                selected["receipt"]["evidence_signals"],
                selected["receipt"]["selection_kind"],
                selected["receipt"]["selection_basis"],
            ),
        )
        domain_names = {
            row["name"]
            for row in EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY)["domain_skills"]
        }
        self.assertEqual(
            ["cloud-platform-extension"],
            [name for name in expected_layer3 if name in domain_names],
        )
        negative_receipt = EVAL.layer3_selector_runtime_selection_receipt(
            projection,
            evidence_signals=expected_signals[:-1],
            build_identity=selected["receipt"]["build"],
        )
        self.assertEqual(
            ["cloud-platform-extension"], negative_receipt["selected_layer3"]
        )
        self.assertNotEqual(
            selected["receipt"]["selected_layer3"],
            negative_receipt["selected_layer3"],
        )

        expected_selected = [
            ["security-privacy-gate", "references/checklist.md"],
            ["security-privacy-gate", "references/evidence-patterns.md"],
            ["security-privacy-gate", "references/security-output-and-gates.md"],
            ["threat-modeling", "references/benchmarks-and-patterns.md"],
            ["threat-modeling", "references/checklist.md"],
            ["threat-modeling", "references/evidence-patterns.md"],
            ["web-security", "references/benchmarks-and-patterns.md"],
            ["web-security", "references/checklist.md"],
            ["web-security", "references/evidence-patterns.md"],
            ["cloud-platform-extension", "references/resource-control-and-data-plane-boundaries.md"],
            ["cloud-platform-extension", "references/iam-workload-identity-and-network-contracts.md"],
            ["cloud-platform-extension", "references/region-failure-domain-consistency-and-quota-contracts.md"],
            ["cloud-platform-extension", "references/encryption-kms-and-cost-contracts.md"],
            ["cloud-platform-extension", "references/provider-api-and-managed-service-authority.md"],
        ]
        selected_references = [
            [record["owner_skill"], record["path"]]
            for record in projection["reference_records"]
            if record["owner_skill"]
            in {"security-privacy-gate", *expected_layer3}
        ]
        self.assertEqual(expected_selected, selected_references)
        context_authority = EVAL.reference_context_admissibility_authority(
            EVAL.load_yaml_file(EVAL.PROFESSIONAL_REGISTRY),
            EVAL.load_yaml_file(EVAL.FOUNDATION_REGISTRY),
            EVAL.load_yaml_file(EVAL.DOMAIN_REGISTRY),
            context="C1S security web named Task witness",
        )
        staged = EVAL.reference_context_staged_plan(
            context_authority,
            references=[tuple(reference) for reference in selected_references],
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        expected_loaded = [
            ["cloud-platform-extension", "references/encryption-kms-and-cost-contracts.md"],
            ["cloud-platform-extension", "references/iam-workload-identity-and-network-contracts.md"],
            ["cloud-platform-extension", "references/provider-api-and-managed-service-authority.md"],
            ["cloud-platform-extension", "references/region-failure-domain-consistency-and-quota-contracts.md"],
            ["cloud-platform-extension", "references/resource-control-and-data-plane-boundaries.md"],
            ["security-privacy-gate", "references/checklist.md"],
            ["security-privacy-gate", "references/evidence-patterns.md"],
            ["security-privacy-gate", "references/security-output-and-gates.md"],
            ["threat-modeling", "references/benchmarks-and-patterns.md"],
            ["threat-modeling", "references/checklist.md"],
            ["threat-modeling", "references/evidence-patterns.md"],
            ["web-security", "references/benchmarks-and-patterns.md"],
            ["web-security", "references/checklist.md"],
            ["web-security", "references/evidence-patterns.md"],
        ]
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected_selected, staged["selected_union"])
        self.assertEqual(expected_loaded, staged["loaded_union"])
        self.assertEqual(
            {tuple(item) for item in expected_selected},
            {tuple(item) for item in expected_loaded},
        )
        self.assertEqual(
            [14, 14, 14, 14],
            [
                len(staged["selected_union"]),
                len(staged["loaded_union"]),
                len(staged["stages"]),
                len(staged["required_output_receipts"]),
            ],
        )
        self.assertEqual(
            expected_loaded,
            [stage["loaded_references"][0] for stage in staged["stages"]],
        )
        self.assertTrue(
            all(
                len(stage["loaded_references"]) == 1
                and stage["carried_predecessors"] == []
                for stage in staged["stages"]
            )
        )
        self.assertEqual([], staged["carried_predecessors"])
        outputs = {
            ("cloud-platform-extension", "references/encryption-kms-and-cost-contracts.md"): ["boundary-decision", "failure-decision", "residual-risk"],
            ("cloud-platform-extension", "references/iam-workload-identity-and-network-contracts.md"): ["boundary-decision", "failure-decision", "validation-plan"],
            ("cloud-platform-extension", "references/provider-api-and-managed-service-authority.md"): ["decision-record", "proof-limit", "validation-plan"],
            ("cloud-platform-extension", "references/region-failure-domain-consistency-and-quota-contracts.md"): ["decision-record", "proof-limit", "validation-plan"],
            ("cloud-platform-extension", "references/resource-control-and-data-plane-boundaries.md"): ["boundary-decision", "decision-record", "proof-limit"],
            ("security-privacy-gate", "references/checklist.md"): ["checklist-result", "residual-risk"],
            ("security-privacy-gate", "references/evidence-patterns.md"): ["evidence-record", "proof-limit", "residual-risk"],
            ("security-privacy-gate", "references/security-output-and-gates.md"): ["gate-decision", "residual-risk"],
            ("threat-modeling", "references/benchmarks-and-patterns.md"): ["option-comparison", "selected-approach"],
            ("threat-modeling", "references/checklist.md"): ["checklist-result", "validation-plan"],
            ("threat-modeling", "references/evidence-patterns.md"): ["evidence-record", "proof-limit", "residual-risk"],
            ("web-security", "references/benchmarks-and-patterns.md"): ["option-comparison", "selected-approach"],
            ("web-security", "references/checklist.md"): ["checklist-result", "residual-risk"],
            ("web-security", "references/evidence-patterns.md"): ["evidence-record", "proof-limit", "residual-risk"],
        }
        receipts = [
            {"reference": reference, "required_outputs": outputs[tuple(reference)]}
            for reference in expected_loaded
        ]
        self.assertEqual(receipts, staged["required_output_receipts"])
        self.assertEqual(
            receipts,
            [stage["required_output_receipts"][0] for stage in staged["stages"]],
        )
        active = ["web-security", "references/benchmarks-and-patterns.md"]
        self.assertEqual(
            (
                [active],
                [],
                [{
                    "reference": active,
                    "required_outputs": ["option-comparison", "selected-approach"],
                }],
            ),
            (
                staged["stages"][11]["loaded_references"],
                staged["stages"][11]["carried_predecessors"],
                staged["stages"][11]["required_output_receipts"],
            ),
        )
        self.assertNotEqual(expected_selected, expected_selected[:-1])
        self.assertNotEqual(expected_loaded, expected_loaded[:-1])

        def source_component(
            kind: str,
            path: Path,
            headings: tuple[str, ...],
            selector: str | None,
            *,
            layer3_delivery: bool = False,
        ) -> dict[str, object]:
            _metadata, raw_frontmatter, body = EVAL.parse_frontmatter(path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            if layer3_delivery:
                output.extend([
                    "",
                    "## Layer 3 Delivery",
                    "",
                    "Expanded Layer 3 roots exist only in this temporary stress projection.",
                ])
            output.append("")
            return EVAL._component(
                kind, path.relative_to(ROOT).as_posix(), "\n".join(output)
            )

        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        capsule = EVAL._capsule_envelopes(EVAL._fixture_cases(document))["task"]
        components = [
            EVAL._file_component(
                "worker_profile",
                ROOT / "dist/copilot/project/.github/agents/task-agent.agent.md",
            ),
            source_component(
                "primary_skill",
                ROOT / "src/professional-skills/security-privacy-gate/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                "security-privacy-gate",
                layer3_delivery=True,
            ),
            source_component(
                "layer3",
                ROOT / "src/domain-extensions/cloud-platform-extension/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                None,
            ),
            source_component(
                "layer3",
                ROOT / "src/foundation/capabilities/threat-modeling/SKILL.md",
                BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                None,
            ),
            source_component(
                "layer3",
                ROOT / "src/foundation/capabilities/web-security/SKILL.md",
                BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                None,
            ),
            EVAL._file_component(
                "layer3_reference",
                ROOT / "src/foundation/capabilities/web-security/references/benchmarks-and-patterns.md",
            ),
            capsule,
        ]
        self._assert_semantic_budget_witness(
            components,
            budget_class="task",
            expected_components=[
                (
                    "worker_profile",
                    "dist/copilot/project/.github/agents/task-agent.agent.md",
                ),
                (
                    "primary_skill",
                    "src/professional-skills/security-privacy-gate/SKILL.md",
                ),
                (
                    "layer3",
                    "src/domain-extensions/cloud-platform-extension/SKILL.md",
                ),
                (
                    "layer3",
                    "src/foundation/capabilities/threat-modeling/SKILL.md",
                ),
                (
                    "layer3",
                    "src/foundation/capabilities/web-security/SKILL.md",
                ),
                (
                    "layer3_reference",
                    "src/foundation/capabilities/web-security/"
                    "references/benchmarks-and-patterns.md",
                ),
                ("dispatch_assignment", capsule["path"]),
            ],
        )
        negative = copy.deepcopy(components)
        negative[5]["tokens"] += (
            EVAL.CONTEXT_BUDGET_LIMITS["task"]["soft_target"]
            + 1
            - EVAL._component_upper_bound(negative)
        )
        self.assertEqual(
            EVAL.CONTEXT_BUDGET_LIMITS["task"]["soft_target"] + 1,
            EVAL._component_upper_bound(negative),
        )
        self.assertNotEqual(components, components[:-1])


if __name__ == "__main__":
    unittest.main()
