from __future__ import annotations

import importlib.util
import copy
import hashlib
import json
import re
import shutil
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
FOCUS_BASELINE_SHA256 = (
    "5111857d64e4da46d781559ceea1896980648c6d6b13858425c7d16e768a2322"
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
    canonical_capsule_sha256,
    parse_layer3_reference_id,
    validate_and_render_fixture_capsule,
)


def _build_runtime_subject(subject: Path) -> None:
    for relative in ("src", "scripts", "evals", "reports"):
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
    current = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
    cases = [
        copy.deepcopy(case)
        for case in current["task_focus_cases"]
        if case["id"] not in EVAL.FOCUS_CURRENT_ONLY_MAP
    ]
    for case in cases:
        if case["id"] == "focus-capability-equivalent-adapter-metadata":
            for adapter in case["inputs"]["adapters"]:
                capabilities = adapter["capabilities"]
                capabilities["exact-change-evidence-export"] = capabilities.pop(
                    "change-evidence-export"
                )
                capabilities.pop("native-change-read")
                capabilities.pop("supplied-change-delivery")
                capabilities["exact-change-evidence-read"] = "supported"
                capabilities[
                    "reviewer-accessible-change-reference"
                ] = capabilities.pop("reviewer-change-consume")
        elif case.get("scenario") == "review-readiness":
            inputs = case["inputs"]
            inputs.pop("change_evidence_artifact", None)
            inputs["exact-change-evidence-export"] = inputs.pop(
                "change-evidence-export"
            )
            inputs.pop("native-change-read")
            inputs.pop("supplied-change-delivery")
            inputs["exact-change-evidence-read"] = (
                "unsupported"
                if inputs["handoff_kind"] == "legacy-incomplete"
                else "supported"
            )
            inputs["reviewer-accessible-change-reference"] = inputs.pop(
                "reviewer-change-consume"
            )
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


class RenderedContextBudgetTests(unittest.TestCase):
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
        BUILD._write_control_layer3_selector_projections(
            target
            / "dist/universal/skills/recommended/engineering-control-plane"
        )
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
        reference_pairs = [
            (primary, str(path))
            for path in step.get("professional_references", [])
        ]
        reference_pairs.extend(
            tuple(str(logical_id).split("/", 1))
            for logical_id in step.get("layer3_references", [])
        )
        for owner, relative_path in reference_pairs:
            binding = EVAL._reference_native_binding(ROOT, owner, relative_path)
            source = ROOT / binding["physical_path"]
            destination = target / binding["physical_path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

    def test_native_dispatch_selection_assets_are_complete_and_host_ordered(self) -> None:
        case, runtime_manifest = self._native_dispatch_probe()
        step_index, step = next(
            (index, item)
            for index, item in enumerate(case["steps"])
            if item.get("action") == "dispatch" and item.get("primary_skill")
        )
        with tempfile.TemporaryDirectory() as raw:
            subject = Path(raw)
            self._copy_native_dispatch_subject(
                subject, str(step["primary_skill"]), step
            )
            measured = EVAL._native_dispatch_selection_assets(
                str(case["id"]), step_index, step, subject, runtime_manifest
            )
        self.assertEqual(["codex", "claude", "copilot"], measured["host_order"])
        self.assertEqual(
            [
                (host, kind)
                for host in ("codex", "claude", "copilot")
                for kind in (
                    "main-profile",
                    "control-owner",
                    "global-professional-router",
                    "professional-selector-envelope",
                    "professional-selector-complete",
                )
            ],
            [(row["host"], row["kind"]) for row in measured["components"]],
        )

    def test_native_dispatch_selection_assets_bind_runtime_and_input(self) -> None:
        case, runtime_manifest = self._native_dispatch_probe()
        step_index, step = next(
            (index, item)
            for index, item in enumerate(case["steps"])
            if item.get("action") == "dispatch" and item.get("primary_skill")
        )
        measured = EVAL._native_dispatch_selection_assets(
            str(case["id"]), step_index, step, ROOT, runtime_manifest
        )
        self.assertEqual(
            EVAL.RUNTIME_NAME, measured["runtime_manifest_binding"]["runtime"]
        )
        self.assertTrue(measured["authoritative_build_inputs"]["sha256"])
        self.assertEqual(
            measured["authoritative_build_inputs"],
            measured["runtime_manifest_binding"]["authoritative_build_inputs"],
        )

    def test_native_dispatch_keeps_one_envelope_and_counts_asset_occurrences(self) -> None:
        case, runtime_manifest = self._native_dispatch_probe()
        lightweight = EVAL._load_current_lightweight_module(
            ROOT / "scripts/eval-agent-lightweight.py"
        )
        measured = EVAL._native_trajectory_case_cost(
            case,
            ROOT,
            runtime_manifest,
            lightweight,
            native_schema=EVAL._native_contract_identity(
                json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
            ),
            host="codex",
        )
        kinds = [row["kind"] for row in measured["native_sources"]["components"]]
        dispatch_count = sum(
            step.get("action") == "dispatch" for step in case["steps"]
        )
        self.assertEqual(dispatch_count, kinds.count("native-selector-envelope"))
        self.assertEqual(
            3,
            measured["structural"]["selector_load_count"],
        )
        self.assertEqual(
            dispatch_count,
            measured["structural"]["envelope_count"],
        )

    def test_s3c_native_trajectory_cost_is_complete_and_exclusive_per_host(self) -> None:
        case, manifests = self._native_dispatch_probe()
        lightweight = EVAL._load_current_lightweight_module(
            ROOT / "scripts/eval-agent-lightweight.py"
        )
        native_schema = EVAL._native_contract_identity(
            json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        )
        measured_rows = []
        for host in EVAL.FOCUS_PROFILE_HOSTS:
            measured = EVAL._native_trajectory_case_cost(
                case,
                ROOT,
                manifests,
                lightweight,
                native_schema=native_schema,
                host=host,
            )
            measured_rows.append(measured)
            sources = measured["native_sources"]["components"]
            envelopes = [
                row for row in sources if row["kind"] == "native-selector-envelope"
            ]
            selector_rows = [row for row in sources if row["bucket"] == "selector"]
            worker = next(row for row in sources if row["kind"] == "worker-profile")
            with self.subTest(host=host):
                self.assertEqual(f"{case['id']}::{host}", measured["id"])
                self.assertEqual(host, measured["host"])
                self.assertTrue(all(row["host"] == host for row in sources))
                self.assertIn(f"dist/{host}/", worker["physical_path"])
                self.assertTrue(
                    all(
                        row["kind"]
                        in {
                            "global-professional-router",
                            "professional-selector",
                            "professional-selector-envelope",
                            "professional-selector-decision",
                            "professional-selector-complete",
                        }
                        for row in selector_rows
                    )
                )
                self.assertTrue(
                    all(row["bucket"] == "cross_agent_transfer" for row in envelopes)
                )
                self.assertEqual(
                    sum(row["tokens"] for row in envelopes)
                    + sum(
                        row["tokens"]
                        for row in measured["native_sources"]["handoffs"]
                    ),
                    measured["component_tokens"]["cross_agent_transfer"],
                )
                self.assertEqual(
                    measured["total_task_tokens"],
                    sum(measured["component_tokens"].values()),
                )
        errors = []
        matrix = EVAL._host_complete_case_matrix(
            "candidate",
            measured_rows,
            {
                "logical_case_count": 1,
                "host_pair_count": 3,
                "host_order": list(EVAL.FOCUS_PROFILE_HOSTS),
            },
            errors,
        )
        self.assertEqual([], errors)
        self.assertEqual(3, matrix["host_pair_count"])

    def test_native_dispatch_assets_are_separate_complete_occurrence_rows(self) -> None:
        case, manifests = self._native_dispatch_probe()
        step_index, step = next(
            (index, item)
            for index, item in enumerate(case["steps"])
            if item.get("action") == "dispatch" and item.get("primary_skill")
        )
        measured = EVAL._native_dispatch_selection_assets(
            str(case["id"]), step_index, step, ROOT, manifests
        )
        self.assertEqual(15, len(measured["components"]))
        self.assertTrue(
            all(
                row["load_count"] == 1
                and row["content_scope"] == "complete-native-bytes"
                and row["tokens"] > 0
                for row in measured["components"]
            )
        )
        self.assertEqual(9, measured["selector_load_count"])

    def test_native_dispatch_selection_assets_fail_on_missing_authority(self) -> None:
        case, manifests = self._native_dispatch_probe()
        step_index, step = next(
            (index, item)
            for index, item in enumerate(case["steps"])
            if item.get("action") == "dispatch" and item.get("primary_skill")
        )
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._copy_native_dispatch_subject(root, str(step["primary_skill"]), step)
            selector = root / (
                "dist/universal/skills/recommended/engineering-control-plane/"
                f"references/selectors/{step['primary_skill']}.json"
            )
            selector.unlink()
            with self.assertRaisesRegex(ValueError, "professional-selector"):
                EVAL._native_dispatch_selection_assets(
                    str(case["id"]),
                    step_index,
                    step,
                    root,
                    manifests,
                )

    def test_native_dispatch_selection_assets_fail_on_host_profile_omission(self) -> None:
        case, manifests = self._native_dispatch_probe()
        step_index, step = next(
            (index, item)
            for index, item in enumerate(case["steps"])
            if item.get("action") == "dispatch" and item.get("primary_skill")
        )
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._copy_native_dispatch_subject(root, str(step["primary_skill"]), step)
            (root / "dist/claude/project/.claude/agents/main-control-agent.md").unlink()
            with self.assertRaisesRegex(ValueError, "claude.*main-profile"):
                EVAL._native_dispatch_selection_assets(
                    str(case["id"]),
                    step_index,
                    step,
                    root,
                    manifests,
                )

    def test_native_dispatch_selection_bundle_is_schema_aware(self) -> None:
        case, manifests = self._native_dispatch_probe()
        step_index, step = next(
            (index, item)
            for index, item in enumerate(case["steps"])
            if item.get("action") == "dispatch" and item.get("primary_skill")
        )
        measured = EVAL._native_dispatch_selection_assets(
            str(case["id"]), step_index, step, ROOT, manifests
        )
        self.assertEqual("split-professional-selector/v1", measured["schema"])
        self.assertEqual(
            [
                "global-professional-router",
                "professional-selector-complete",
                "professional-selector-envelope",
            ],
            measured["physical_selector_kinds"],
        )
        self.assertEqual(9, measured["selector_load_count"])
        self.assertEqual("complete", measured["selector_resolution"])
        self.assertEqual(
            "engineering-change-analysis/complete.json",
            measured["professional_selector_decision_path"],
        )
        self.assertEqual(step["layer3_skills"], measured["effective_ordered_layer3"])
        self.assertEqual([], measured["handoff_augmentation"]["layer3_skills"])

    def test_s3d_diagnosis_loads_only_envelope_and_exact_decision_partition(self) -> None:
        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        case = copy.deepcopy(
            next(item for item in document["cases"] if item["id"] == "diagnosis-only")
        )
        runtime_manifest = json.loads(
            (
                ROOT
                / "dist/universal/skills"
                / EVAL.RUNTIME_NAME
                / ".changeforge-build-manifest.json"
            ).read_text(encoding="utf-8")
        )
        step_index, step = next(
            (index, item)
            for index, item in enumerate(case["steps"])
            if item.get("action") == "dispatch" and item.get("primary_skill")
        )
        with tempfile.TemporaryDirectory() as raw:
            subject = Path(raw)
            self._copy_native_dispatch_subject(
                subject, str(step["primary_skill"]), step
            )
            measured = EVAL._native_dispatch_selection_assets(
                str(case["id"]), step_index, step, subject, runtime_manifest
            )
            for host in EVAL.FOCUS_PROFILE_HOSTS:
                selector_rows = [
                    row
                    for row in measured["components"]
                    if row["host"] == host
                    and row["kind"]
                    in {
                        "professional-selector-envelope",
                        "professional-selector-decision",
                    }
                ]
                with self.subTest(host=host):
                    self.assertEqual(
                        [
                            "professional-selector-envelope",
                            "professional-selector-decision",
                        ],
                        [row["kind"] for row in selector_rows],
                    )
                    self.assertFalse(
                        any(
                            row["kind"] == "professional-selector-complete"
                            for row in measured["components"]
                            if row["host"] == host
                        )
                    )
            self.assertEqual("exact", measured["selector_resolution"])
            self.assertEqual(
                "engineering-change-analysis/failure-diagnosis-analysis.json",
                measured["professional_selector_decision_path"],
            )
            self.assertEqual(
                ["failure-diagnosis"], measured["effective_ordered_layer3"]
            )
            resolution = measured["professional_selector_resolution"]
            self.assertEqual(
                {
                    "route_source",
                    "trigger",
                    "start_profile",
                    "primary_professional_skill",
                    "review_skill",
                    "selection_owner",
                },
                set(resolution["runtime_key"]),
            )
            self.assertNotIn("selected_layer3", resolution["runtime_key"])
            self.assertNotIn("scenario_id", resolution["runtime_key"])
            self.assertNotIn("light_case_id", resolution["runtime_key"])
            self.assertEqual(
                ["failure-diagnosis"], resolution["selected_layer3"]
            )
            receipt = measured["professional_selector_receipt"]
            self.assertEqual([], receipt["evidence_signals"])
            self.assertEqual(["exact-layer3-authority"], receipt["selector_ids"])
            self.assertEqual(["failure-diagnosis"], receipt["selected_layer3"])

        lightweight = EVAL._load_current_lightweight_module(
            ROOT / "scripts/eval-agent-lightweight.py"
        )
        trajectory = EVAL._native_trajectory_case_cost(
            case,
            ROOT,
            runtime_manifest,
            lightweight,
            native_schema=EVAL._native_contract_identity(document),
            host="codex",
        )
        bundle = trajectory["native_sources"]["selection_authority_bundles"][0]
        resolution = bundle["professional_selector_resolution"]
        self.assertEqual("exact", resolution["selection_kind"])
        self.assertEqual(
            "failure-diagnosis-analysis", resolution["decision_id"]
        )
        self.assertEqual(
            {
                "route_source",
                "trigger",
                "start_profile",
                "primary_professional_skill",
                "review_skill",
                "selection_owner",
            },
            set(resolution["runtime_key"]),
        )
        self.assertEqual(
            {"router", "release_scenario", "selector_registry"},
            set(resolution["source_authorities"]),
        )
        report_receipt = bundle["professional_selector_receipt"]
        self.assertEqual([], report_receipt["evidence_signals"])
        self.assertEqual(
            ["exact-layer3-authority"], report_receipt["selector_ids"]
        )
        self.assertEqual(
            ["failure-diagnosis"], report_receipt["selected_layer3"]
        )
        self.assertTrue(bundle["professional_selector_pointer"])
        self.assertTrue(bundle["native_envelope"]["sha256"])
        self.assertEqual(
            EVAL.RUNTIME_NAME, bundle["runtime_manifest_binding"]["runtime"]
        )

    def test_s3d_all_current_engineering_analysis_dispatches_resolve_once_per_host(self) -> None:
        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        dispatches = [
            (str(case["id"]), index, step)
            for case in document["cases"]
            for index, step in enumerate(case.get("steps", []))
            if step.get("action") == "dispatch"
            and step.get("primary_skill") == "engineering-change-analysis"
        ]
        self.assertEqual(8, len(dispatches))
        runtime_manifest = json.loads(
            (
                ROOT
                / "dist/universal/skills"
                / EVAL.RUNTIME_NAME
                / ".changeforge-build-manifest.json"
            ).read_text(encoding="utf-8")
        )
        observed: list[tuple[str, str, str]] = []
        with tempfile.TemporaryDirectory() as raw:
            subject = Path(raw)
            for case_id, step_index, step in dispatches:
                self._copy_native_dispatch_subject(
                    subject, str(step["primary_skill"]), step
                )
                measured = EVAL._native_dispatch_selection_assets(
                    case_id, step_index, step, subject, runtime_manifest
                )
                expected_resolution = (
                    "exact" if case_id == "diagnosis-only" else "complete"
                )
                self.assertEqual(expected_resolution, measured["selector_resolution"])
                for host in EVAL.FOCUS_PROFILE_HOSTS:
                    host_rows = [
                        row
                        for row in measured["components"]
                        if row["host"] == host
                        and row["kind"]
                        in {
                            "professional-selector-envelope",
                            "professional-selector-decision",
                            "professional-selector-complete",
                        }
                    ]
                    self.assertEqual(2, len(host_rows))
                    observed.append((case_id, host, expected_resolution))
        self.assertEqual(24, len(observed))
        self.assertEqual(
            3,
            sum(resolution == "exact" for _case, _host, resolution in observed),
        )
        self.assertEqual(
            21,
            sum(resolution == "complete" for _case, _host, resolution in observed),
        )

    def test_s3b_trajectory_reference_pair_binds_exact_or_fails_closed(self) -> None:
        case, _manifests = self._native_dispatch_probe()
        step = next(
            item
            for item in case["steps"]
            if item.get("action") == "dispatch" and item.get("primary_skill")
        )
        exact, bindings = EVAL._trajectory_exact_reference_selection(step, ROOT)
        self.assertEqual(step["professional_references"], exact)
        self.assertEqual(
            [(step["primary_skill"], path) for path in exact],
            [(row["owner_skill"], row["path"]) for row in bindings],
        )
        for missing in ("professional_references", "layer3_references"):
            unresolved = copy.deepcopy(step)
            unresolved.pop(missing)
            self.assertEqual(
                (None, []),
                EVAL._trajectory_exact_reference_selection(unresolved, ROOT),
            )
        invalid = copy.deepcopy(step)
        invalid["professional_references"] = ["references/invented.md"]
        with self.assertRaisesRegex(ValueError, "native registry binding"):
            EVAL._trajectory_exact_reference_selection(invalid, ROOT)

    def test_s3b_comparison_retains_physical_selection_rows_and_reconciles(self) -> None:
        baseline = self._ab_subject(100)
        candidate = self._ab_subject(100)
        for subject in (baseline, candidate):
            subject["cases"][0]["native_sources"]["components"] = [
                {
                    "host": "codex",
                    "kind": "global-professional-router",
                    "bucket": "selector",
                    "physical_path": "router.md",
                    "sha256": "a" * 64,
                    "tokens": 5,
                    "load_count": 1,
                    "assignment_key": "case/main/router",
                }
            ]
            subject["cases"][0]["native_sources"][
                "selection_asset_component_tokens"
            ] = {"always_loaded": 0, "selector": 5, "reference_partition": 0}
        compared = EVAL._compare_end_to_end_subjects(baseline, candidate)
        row = next(item for item in compared["cases"] if item["host"] == "codex")
        self.assertEqual(
            baseline["cases"][0]["native_sources"]["components"],
            row["selection_asset_rows"]["baseline"],
        )
        self.assertEqual(0, row["selection_asset_reconciliation"]["baseline"])
        broken = copy.deepcopy(candidate)
        broken["cases"][0]["native_sources"]["components"][0]["tokens"] = 4
        failed = EVAL._compare_end_to_end_subjects(baseline, broken)
        self.assertEqual("fail", failed["status"])
        self.assertTrue(
            any("selection asset rows do not reconcile" in error for error in failed["errors"]),
            failed["errors"],
        )

    def test_normalized_native_bundle_expands_authority_and_binds_partitions(self) -> None:
        authority = VALIDATION.layer3_selector_authority(
            VALIDATION.load_yaml_file(ROOT / "src/registry/foundation-skills.yaml"),
            VALIDATION.load_yaml_file(ROOT / "src/registry/professional-skills.yaml"),
            VALIDATION.load_yaml_file(ROOT / "src/registry/domain-skills.yaml"),
            context="normalized evaluator bundle",
        )
        selectors, partitions = (
            VALIDATION.layer3_selector_normalized_control_projections(authority)
        )
        filename = "backend-change-builder.json"
        base = selectors[filename]
        selected_layer3 = ["transaction-consistency"]
        selected_partitions = {
            owner: partitions[f"backend-change-builder/{owner}.json"]
            for owner in ["backend-change-builder", *selected_layer3]
        }
        measured = EVAL._selection_authority_bundle(
            schema="split-professional-selector/v1",
            router_rows=[
                {
                    "pointer": "#L1",
                    "profile": "task-agent",
                    "professional_skill": "backend-change-builder",
                    "layer3_skills": [],
                    "review_skill": "ai-code-review-refactor",
                }
            ],
            step={
                "profile": "task-agent",
                "primary_skill": "backend-change-builder",
                "layer3_skills": ["transaction-consistency"],
            },
            selector=base,
            reference_partitions=selected_partitions,
            exact_references=None,
            envelope_pointer="fixture:normalized:selector",
            envelope_sha256="a" * 64,
        )
        self.assertEqual(
            ["backend-change-builder", *selected_layer3],
            measured["reference_partitions_loaded"],
        )
        self.assertEqual(
            [
                "../reference-records/backend-change-builder/"
                "backend-change-builder.json",
                "../reference-records/backend-change-builder/"
                "transaction-consistency.json",
            ],
            measured["reference_partition_pointers"],
        )
        self.assertEqual(
            ["transaction-consistency"], measured["effective_ordered_layer3"]
        )

    def test_native_partitions_are_loaded_once_per_host_only_when_unresolved(self) -> None:
        case, manifests = self._native_dispatch_probe()
        step_index, step = next(
            (index, item)
            for index, item in enumerate(case["steps"])
            if item.get("action") == "dispatch" and item.get("primary_skill")
        )
        authority = VALIDATION.layer3_selector_authority(
            VALIDATION.load_yaml_file(ROOT / "src/registry/foundation-skills.yaml"),
            VALIDATION.load_yaml_file(ROOT / "src/registry/professional-skills.yaml"),
            VALIDATION.load_yaml_file(ROOT / "src/registry/domain-skills.yaml"),
            context="native partition cost",
        )
        selectors, partitions = (
            VALIDATION.layer3_selector_normalized_control_projections(authority)
        )
        filename = f"{step['primary_skill']}.json"
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._copy_native_dispatch_subject(root, str(step["primary_skill"]), step)
            control = root / (
                "dist/universal/skills/recommended/engineering-control-plane/references"
            )
            selector_path = control / "selectors" / filename
            selector_path.write_text(
                json.dumps(selectors[filename], sort_keys=True, separators=(",", ":"))
                + "\n",
                encoding="utf-8",
            )
            owners = [str(step["primary_skill"]), *step["layer3_skills"]]
            partition_paths = []
            for owner in owners:
                partition_path = (
                    control / "reference-records" / str(step["primary_skill"])
                    / f"{owner}.json"
                )
                partition_path.parent.mkdir(parents=True, exist_ok=True)
                partition_path.write_text(
                    json.dumps(
                        partitions[f"{step['primary_skill']}/{owner}.json"],
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                    + "\n",
                    encoding="utf-8",
                )
                partition_paths.append(partition_path)
            unresolved_step = copy.deepcopy(step)
            unresolved_step.pop("professional_references")
            unresolved_step.pop("layer3_references")
            unresolved = EVAL._native_dispatch_selection_assets(
                str(case["id"]), step_index, unresolved_step, root, manifests
            )
            self.assertEqual(3 * len(owners), unresolved["reference_partition_load_count"])
            self.assertEqual(
                3 * len(owners),
                sum(
                    row["load_count"]
                    for row in unresolved["components"]
                    if row["kind"] == "reference-records-partition"
                ),
            )
            self.assertGreater(unresolved["component_tokens"]["reference_partition"], 0)

            exact = copy.deepcopy(step)
            exact["professional_references"] = []
            exact["layer3_references"] = []
            skipped = EVAL._native_dispatch_selection_assets(
                str(case["id"]), step_index, exact, root, manifests
            )
            self.assertEqual(0, skipped["reference_partition_load_count"])
            self.assertEqual([], skipped["reference_partitions_loaded"])
            self.assertFalse(
                any(
                    row["kind"] == "reference-records-partition"
                    for row in skipped["components"]
                )
            )

            partition_paths[-1].unlink()
            with self.assertRaisesRegex(ValueError, "Reference partition"):
                EVAL._native_dispatch_selection_assets(
                    str(case["id"]), step_index, unresolved_step, root, manifests
                )

    def test_native_combined_router_uses_declared_base_and_zero_token_handoff_augmentation(self) -> None:
        case, manifests = self._native_dispatch_probe()
        step_index, step = next(
            (index, item)
            for index, item in enumerate(case["steps"])
            if item.get("action") == "dispatch" and item.get("profile") == "task-agent"
        )
        step = copy.deepcopy(step)
        step["primary_skill"] = "data-api-contract-changer"
        step["layer3_skills"] = [
            "api-contract-design",
            "dto-schema-design",
            "version-compatibility",
        ]
        step["professional_references"] = []
        step["layer3_references"] = []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._copy_native_dispatch_subject(root, str(step["primary_skill"]), step)
            router = root / (
                "dist/universal/skills/recommended/engineering-control-plane/"
                "references/professional-skill-router.md"
            )
            router.write_text(
                "# Professional Skill Router\n\n"
                "| Task signal | Start profile | Primary Professional Skill | Optional Layer 3 Skills | Review Skill |\n"
                "| --- | --- | --- | --- | --- |\n"
                "| analyzed public API or data-contract implementation (`implementation-preparation`) | analysis-agent | engineering-change-analysis | api-contract-design, version-compatibility | architecture-impact-reviewer |\n"
                "| analyzed release scenario | analysis-agent | engineering-change-analysis | release-rollback, version-compatibility | delivery-release-gate |\n",
                encoding="utf-8",
            )
            fixture_path = root / "evals/agent-light-trajectories/cases.yaml"
            fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
            native_case = next(
                item for item in fixture["cases"] if item["id"] == "api-contract-change"
            )
            native_case["steps"][step_index] = step
            fixture_path.write_text(
                json.dumps(fixture, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (root / (
                "dist/universal/skills/recommended/engineering-control-plane/"
                "references/selectors/data-api-contract-changer.json"
            )).unlink()
            measured = EVAL._native_dispatch_selection_assets(
                "api-contract-change", step_index, step, root, manifests
            )
        self.assertEqual("combined-router/v1", measured["schema"])
        self.assertEqual(
            ["api-contract-design", "version-compatibility"],
            measured["router_declared_layer3"],
        )
        self.assertEqual(
            ["dto-schema-design"],
            measured["handoff_augmentation"]["layer3_skills"],
        )
        self.assertEqual(
            "analyzed public API or data-contract implementation (`implementation-preparation`)",
            measured["router_trigger"],
        )
        self.assertEqual("analysis-agent", measured["router_profile"])
        self.assertEqual(
            "engineering-change-analysis", measured["router_primary_skill"]
        )
        self.assertEqual(
            "architecture-impact-reviewer", measured["router_review_skill"]
        )
        self.assertEqual(1, len(measured["router_pointers"]))
        self.assertEqual(
            "src/registry/release-routing-scenarios.yaml",
            measured["handoff_augmentation"]["authority_path"],
        )
        self.assertEqual(
            hashlib.sha256(
                (ROOT / "src/registry/release-routing-scenarios.yaml").read_bytes()
            ).hexdigest(),
            measured["handoff_augmentation"]["sha256"],
        )
        self.assertEqual(0, measured["handoff_augmentation"]["tokens_added"])
        self.assertEqual(3, measured["selector_load_count"])

    def test_native_combined_router_rejects_ambiguous_release_scenario(self) -> None:
        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        case = copy.deepcopy(
            next(item for item in document["cases"] if item["id"] == "api-contract-change")
        )
        step_index, step = next(
            (index, item)
            for index, item in enumerate(case["steps"])
            if item.get("action") == "dispatch" and item.get("profile") == "task-agent"
        )
        _probe, manifests = self._native_dispatch_probe()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._copy_native_dispatch_subject(root, str(step["primary_skill"]), step)
            scenario_path = root / "src/registry/release-routing-scenarios.yaml"
            scenario_text = scenario_path.read_text(encoding="utf-8")
            scenario_path.write_text(
                scenario_text.replace(
                    "light_case_id: single-module-feature",
                    "light_case_id: api-contract-change",
                    1,
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "scenario authority is ambiguous"):
                EVAL._native_combined_dispatch_binding(
                    str(case["id"]),
                    step_index,
                    step,
                    root,
                    {"rows": []},
                )

    def test_native_selection_bundle_rejects_authority_disagreement_and_duplicate_occurrence(self) -> None:
        with self.assertRaisesRegex(ValueError, "augmentation authority"):
            EVAL._selection_authority_bundle(
                schema="combined-router/v1",
                router_rows=[{
                    "pointer": "#L5",
                    "signal": "accepted API task",
                    "profile": "task-agent",
                    "professional_skill": "data-api-contract-changer",
                    "layer3_skills": [],
                    "review_skill": "architecture-impact-reviewer",
                }],
                step={
                    "profile": "task-agent",
                    "primary_skill": "data-api-contract-changer",
                    "layer3_skills": ["version-compatibility"],
                    "router_trigger": "accepted API task",
                    "review_skill": "architecture-impact-reviewer",
                    "handoff_augmentation_authority": {
                        "path": "src/registry/release-routing-scenarios.yaml",
                        "sha256": "a" * 64,
                        "pointer": "#/scenarios/0/tasks/0",
                        "layer3_skills": [],
                    },
                },
                selector=None,
                envelope_pointer="fixture:case:step:1:selector",
                envelope_sha256="a" * 64,
            )
        duplicate = {
            "host": "codex",
            "kind": "global-professional-router",
            "physical_path": "same.md",
            "sha256": "b" * 64,
            "load_count": 1,
        }
        with self.assertRaisesRegex(ValueError, "duplicate selection asset"):
            EVAL._validate_selection_asset_occurrences([duplicate, dict(duplicate)])

    def test_combined_router_binding_rejects_nearby_but_unbound_authority(self) -> None:
        correct = {
            "pointer": "#/scenarios/0/router",
            "signal": "accepted API task",
            "profile": "task-agent",
            "professional_skill": "data-api-contract-changer",
            "layer3_skills": ["api-contract-design", "dto-schema-design"],
            "review_skill": "architecture-impact-reviewer",
        }
        unrelated = {
            "pointer": "#/scenarios/1/router",
            "signal": "analyzed release scenario",
            "profile": "analysis-agent",
            "professional_skill": "engineering-change-analysis",
            "layer3_skills": ["release-rollback", "version-compatibility"],
            "review_skill": "delivery-release-gate",
        }
        step = {
            "profile": "task-agent",
            "primary_skill": "data-api-contract-changer",
            "layer3_skills": [
                "api-contract-design",
                "dto-schema-design",
                "version-compatibility",
            ],
            "router_trigger": "accepted API task",
            "review_skill": "architecture-impact-reviewer",
            "handoff_augmentation_authority": {
                "path": "src/registry/release-routing-scenarios.yaml",
                "sha256": "a" * 64,
                "pointer": "#/scenarios/0/tasks/0",
                "layer3_skills": ["version-compatibility"],
            },
        }
        complete = {
            **correct,
            "layer3_skills": [
                "api-contract-design",
                "dto-schema-design",
                "version-compatibility",
            ],
        }
        mutations = {
            "wrong trigger": [{**complete, "signal": "different trigger"}],
            "wrong Professional": [
                {**complete, "professional_skill": "backend-change-builder"}
            ],
            "wrong Profile": [{**complete, "profile": "analysis-agent"}],
            "wrong Review": [
                {**complete, "review_skill": "ai-code-review-refactor"}
            ],
            "ambiguous scenario": [complete, {**complete, "pointer": "#L99"}],
        }
        for label, router_rows in mutations.items():
            with self.subTest(label=label), self.assertRaises(ValueError):
                EVAL._selection_authority_bundle(
                    schema="combined-router/v1",
                    router_rows=router_rows,
                    step=step,
                    selector=None,
                    envelope_pointer="fixture:api-contract-change:step:6:selector",
                    envelope_sha256="b" * 64,
                )

        missing_augmentation = copy.deepcopy(step)
        missing_augmentation.pop("handoff_augmentation_authority")
        with self.assertRaisesRegex(ValueError, "augmentation authority"):
            EVAL._selection_authority_bundle(
                schema="combined-router/v1",
                router_rows=[correct, unrelated],
                step=missing_augmentation,
                selector=None,
                envelope_pointer="fixture:api-contract-change:step:6:selector",
                envelope_sha256="b" * 64,
            )

    def test_release_projection_rejects_stale_json_or_markdown_binding(self) -> None:
        comparison = {
            "status": "pass",
            "aggregate": {"baseline": 10, "candidate": 9, "delta": -1},
            "cases": [
                {
                    "id": "case-a",
                    "selection_authority_bundles": {
                        "baseline": [{"schema": "combined-router/v1"}],
                        "candidate": [
                            {"schema": "changeforge.layer3-selector-normalized-control/v1"}
                        ],
                    },
                    "structural": {
                        "selector_load_count": {"baseline": 1, "candidate": 1},
                        "reference_partition_load_count": {
                            "baseline": 0,
                            "candidate": 1,
                        },
                        "reference_load_count": {"baseline": 1, "candidate": 1},
                    },
                }
            ],
            "subjects": {"baseline": {}, "candidate": {}},
            "host_matrix": {
                "logical_case_count": 1,
                "host_pair_count": 1,
                "host_order": ["codex"],
                "component_tokens": {},
                "hosts": {},
                "reconciliation": {
                    "baseline": 0,
                    "candidate": 0,
                    "host_pair_count": 0,
                },
            },
        }
        binding = EVAL._end_to_end_projection_binding(comparison)
        self.assertEqual(
            {
                "bundle_count": 1,
                "bundle_digest": hashlib.sha256(
                    EVAL._canonical_json_text(
                        [{"schema": "combined-router/v1"}]
                    ).encode("utf-8")
                ).hexdigest(),
                "schemas": {"combined-router/v1": 1},
                "selector_load_count": 1,
                "reference_partition_load_count": 0,
                "reference_load_count": 1,
            },
            binding["selection_authority_summary"]["baseline"],
        )
        self.assertIn(
            "Selection authority candidate: bundles **1**; schemas "
            "**changeforge.layer3-selector-normalized-control/v1=1**; "
            "selector/partition/reference loads **1 / 1 / 1**.",
            EVAL._render_end_to_end_projection_markdown(comparison),
        )
        self.assertEqual(
            [],
            EVAL._end_to_end_projection_binding_errors(
                comparison,
                EVAL._render_end_to_end_projection_markdown(comparison),
                binding,
            ),
        )
        self.assertTrue(
            EVAL._end_to_end_projection_binding_errors(
                comparison,
                "# stale\n",
                binding,
            )
        )

    _admissible_report_cache: dict[str, object] | None = None

    @classmethod
    def _admissible_report(cls) -> dict[str, object]:
        if cls._admissible_report_cache is None:
            cls._admissible_report_cache = EVAL.evaluate()[
                "admissible_context_compositions"
            ]
        return cls._admissible_report_cache

    def test_phase3_profile_and_analysis_mode_owners_are_isolated(self) -> None:
        profiles = json.loads(
            (ROOT / "src/agent-profiles/role-agents.json").read_text(
                encoding="utf-8"
            )
        )["profiles"]
        instructions = {item["name"]: item["instructions"] for item in profiles}
        role_obligations = {
            "main-control-agent": ("Dispatch only/no target-code access",),
            "analysis-agent": (
                "minimum complete direct read/search current source",
                "Remain read-only",
            ),
            "task-agent": (
                "Before editing inspect the owner/tests/minimum consumer",
                "fresh validation",
            ),
            "review-agent": (
                "Actual diff authoritative",
                "Never edit",
            ),
        }
        for role, obligations in role_obligations.items():
            with self.subTest(role=role):
                for obligation in obligations:
                    self.assertIn(obligation, instructions[role])

        task_rules = instructions["task-agent"].splitlines()
        core = json.loads(
            (ROOT / "src/control-model/core-contracts.json").read_text(
                encoding="utf-8"
            )
        )
        discipline = core["implementation_discipline_contract"]
        self.assertIn(
            discipline["profile_capability_id"],
            core["profile_contract"]["role_capabilities"]["task-agent"][
                "required_capability_ids"
            ],
        )
        resident_projection_ids = set()
        for projection in discipline["profile_projection"]:
            rule = projection["exact_rule"]
            occurrences = task_rules.count(rule)
            if occurrences:
                resident_projection_ids.add(projection["rule_id"])
            with self.subTest(task_rule=projection["rule_id"]):
                self.assertLessEqual(occurrences, 1)
        self.assertEqual({"test-first-required"}, resident_projection_ids)

        analysis_root = (
            ROOT / "src/professional-skills/engineering-change-analysis/SKILL.md"
        ).read_text(encoding="utf-8")
        implementation = (
            ROOT
            / "src/professional-skills/engineering-change-analysis/references/implementation-preparation.md"
        ).read_text(encoding="utf-8")
        control_template = (
            ROOT
            / "src/control-skills/engineering-control-plane/references/engineering-brief-template.md"
        ).read_text(encoding="utf-8")
        for control_only_term in (
            "Task Contract v2",
            "Delta Impact:",
        ):
            with self.subTest(control_only_term=control_only_term):
                self.assertNotIn(control_only_term, analysis_root)
                self.assertNotIn(control_only_term, implementation)
                self.assertIn(control_only_term, control_template)

        self.assertNotIn("## First Executable Slice", analysis_root)
        self.assertIn("`## First Executable Slice`", implementation)

    def test_review_profile_keeps_evidence_localization_and_depth_on_all_hosts(
        self,
    ) -> None:
        profiles = json.loads(
            (ROOT / "src/agent-profiles/role-agents.json").read_text(
                encoding="utf-8"
            )
        )["profiles"]
        review = next(
            item["instructions"]
            for item in profiles
            if item["name"] == "review-agent"
        )
        obligations = (
            "Depth only Level-added, never removed.",
            "Evidence Closure:",
            "independently direct read/search current source→minimum complete proof",
            "counts/Top-K/files/summaries/digests/paths/output/opaque refs are selectors only",
            "Actual diff authoritative; every changed file required; missing blocks",
            "older review cannot cover later edits.",
            "Never edit, repair, dispatch or inherit implementer reasoning",
            "Re-review Classification=",
        )
        for obligation in obligations:
            self.assertEqual(1, review.count(obligation))
        profile = next(
            item for item in profiles if item["name"] == "review-agent"
        )
        enforcement = json.loads(
            (ROOT / "src/agent-profiles/host-enforcement.json").read_text(
                encoding="utf-8"
            )
        )
        for renderer in (
            BUILD._render_codex_profile,
            BUILD._render_claude_profile,
            BUILD._render_copilot_profile,
        ):
            with self.subTest(renderer=renderer.__name__):
                rendered = renderer(profile, enforcement)
                for obligation in obligations:
                    self.assertEqual(1, rendered.count(obligation))

    def test_transfer_compaction_round_trips_every_valid_boundary(self) -> None:
        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        for _group, case in EVAL._fixture_cases(document):
            for boundary, projection, source in EVAL._case_transfer_projection_rows(
                case
            ):
                with self.subTest(case=case["id"], boundary=boundary):
                    compact = EVAL._compact_transfer_projection(
                        boundary, projection, source
                    )
                    self.assertEqual(
                        projection,
                        EVAL._expand_transfer_projection(boundary, compact),
                    )
                    self.assertLess(
                        EVAL.count_o200k_base_tokens(
                            EVAL._canonical_json_text(compact)
                        ),
                        EVAL.count_o200k_base_tokens(
                            EVAL._canonical_json_text(projection)
                        ),
                    )

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
                            component("dispatch_capsule", f"utility-{index}", tokens)
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
                            "kind": "dispatch_capsule",
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

    def test_all_fixture_dispatches_declare_rendered_context(self) -> None:
        document = EVAL.json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        cases = EVAL._fixture_cases(document)
        dispatches = [
            (case["id"], index, step, case["steps"])
            for _group, case in cases
            for index, step in enumerate(case["steps"])
            if step.get("action") == "dispatch"
        ]
        self.assertEqual(16, len(cases))
        self.assertEqual(40, len(dispatches))
        for case_id, index, step, steps in dispatches:
            with self.subTest(case=case_id, step=index):
                self.assertNotIn("dispatch_capsule", step)
                if "utility_capsule" in step:
                    self.assertNotIn("layer3_references", step)
                else:
                    self.assertIsInstance(step.get("layer3_references"), list)
                self.assertEqual(
                    [],
                    EVAL._dispatch_metadata_errors(
                        case_id, index, step, steps
                    ),
                )

    def test_utility_assignment_requires_current_canonical_baseline_state(self) -> None:
        document = EVAL.json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        original = copy.deepcopy(document["utility_cases"][0]["steps"][1])
        ledger = original["utility_capsule"]["evidence_ledger"]
        self.assertEqual("workspace baseline captured", ledger[0]["Claim"])
        self.assertEqual("current", ledger[0]["State"])
        self.assertNotIn("Evidence State", ledger[0])
        self.assertIn("# Utility Assignment", validate_and_render_fixture_capsule(original))

        mutations = []
        for state in ("superseded", "invalid"):
            step = copy.deepcopy(original)
            step["utility_capsule"]["evidence_ledger"][0]["State"] = state
            mutations.append((state, step))
        missing = copy.deepcopy(original)
        missing["utility_capsule"]["evidence_ledger"] = []
        mutations.append(("missing", missing))

        for label, step in mutations:
            with self.subTest(state=label):
                with self.assertRaisesRegex(
                    FixtureCapsuleError,
                    "missing current claims.*workspace baseline captured",
                ):
                    step["fixture_capsule"][
                        "canonical_sha256"
                    ] = canonical_capsule_sha256(
                        step,
                        step["fixture_capsule"],
                    )
                    validate_and_render_fixture_capsule(step)

    def test_nested_reference_selection_changes_capsule_hash(self) -> None:
        document = EVAL.json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        migration = next(case for case in document["cases"] if case["id"] == "data-migration")
        selected = copy.deepcopy(migration["steps"][6])
        without_nested = copy.deepcopy(selected)
        without_nested["layer3_references"] = []
        selected_text = validate_and_render_fixture_capsule(
            selected,
            accepted_analysis_task_id="task-data-migration-1",
        )
        without_hash = canonical_capsule_sha256(
            without_nested,
            without_nested["fixture_capsule"],
            accepted_analysis_task_id="task-data-migration-1",
        )
        self.assertIn(
            "transaction-consistency/references/evidence-patterns.md",
            selected_text,
        )
        self.assertNotEqual(
            selected["fixture_capsule"]["canonical_sha256"], without_hash
        )

    def test_layer3_reference_logical_id_path_safety(self) -> None:
        self.assertEqual(
            ("transaction-consistency", "references/evidence-patterns.md"),
            parse_layer3_reference_id(
                "transaction-consistency/references/evidence-patterns.md"
            ),
        )
        invalid = (
            "/transaction-consistency/references/evidence-patterns.md",
            "transaction-consistency\\references\\evidence-patterns.md",
            "../transaction-consistency/references/evidence-patterns.md",
            "transaction-consistency/./evidence-patterns.md",
            "transaction-consistency/references/index.md",
            "transaction-consistency/references/catalog.md",
            "transaction-consistency/references/evidence-patterns.md?raw=1",
            "transaction-consistency/references/evidence-patterns.md#section",
            "transaction-consistency/references/*.md",
            "transaction-consistency/references/nested/evidence-patterns.md",
        )
        for logical_id in invalid:
            with self.subTest(logical_id=logical_id):
                with self.assertRaises(FixtureCapsuleError):
                    parse_layer3_reference_id(logical_id)

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
        self.assertEqual("analyzed", case["kind"])
        self.assertEqual("analysis-agent", dispatch["profile"])
        self.assertEqual("engineering-change-analysis", dispatch["primary_skill"])
        review_dispatch = next(
            step
            for step in case["steps"]
            if step.get("action") == "dispatch"
            and step.get("profile") == "review-agent"
        )
        self.assertEqual("delivery-release-gate", review_dispatch["primary_skill"])
        self.assertEqual([], review_dispatch["layer3_skills"])
        capsule = EVAL._component(
            "dispatch_capsule",
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
                ROOT / "dist/codex/project/.codex/agents/analysis-agent.toml",
            ),
            EVAL._file_component(
                "primary_skill",
                ROOT
                / "dist/universal/skills/recommended/"
                "engineering-change-analysis/SKILL.md",
            ),
            EVAL._file_component(
                "mode_reference",
                ROOT
                / "src/professional-skills/engineering-change-analysis/"
                "references/implementation-preparation.md",
            ),
            *[
                EVAL._component(
                    "layer3",
                    f"source-projection:{name}",
                    BUILD._render_layer3_reference(foundation_items[name]),
                )
                for name in dispatch["layer3_skills"]
            ],
            capsule,
        ]
        measurement = EVAL._measure_context(
            components,
            budget_class="analysis",
        )
        self.assertLessEqual(
            measurement["total_tokens"],
            EVAL.CONTEXT_BUDGET_LIMITS["analysis"]["hard_ceiling"],
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
                *components[:3],
                EVAL._component(
                    "layer3",
                    f"source-projection:{name}",
                    BUILD._render_layer3_reference(foundation_items[name]),
                ),
                capsule,
            ]
            affected_family_ratios.append(
                EVAL._measure_context(
                    family_components,
                    budget_class="analysis",
                )["duplicate_rule_token_ratio"]
            )
        self.assertLess(max(affected_family_ratios), 0.01)

    def test_transferred_context_categories_are_source_bound_and_exclusive(self) -> None:
        report = EVAL.evaluate()
        transfer = report["transferred_context"]
        expected_categories = {
            "authority",
            "skill_reference",
            "task_capsule",
            "implementation_handoff",
            "evidence_ledger",
            "diff",
            "validation",
            "review_handoff",
            "repair_context",
            "duplicate_context",
            "superseded_evidence",
        }
        self.assertEqual(expected_categories, set(transfer["categories"]))
        exclusive = transfer["accounting"]["exclusive_categories"]
        self.assertEqual(
            transfer["gross_tokens"],
            sum(transfer["categories"][item]["gross_tokens"] for item in exclusive),
        )
        self.assertEqual(
            transfer["gross_tokens"],
            transfer["non_compressible_tokens"] + transfer["compressible_tokens"],
        )
        for category, measurement in transfer["categories"].items():
            with self.subTest(category=category):
                self.assertTrue(measurement["source_selectors"])
                if measurement["accounting_role"] == "exclusive-denominator":
                    self.assertEqual(
                        measurement["gross_tokens"],
                        measurement["non_compressible_tokens"]
                        + measurement["compressible_tokens"],
                    )

    def test_long_tasks_join_lightweight_required_progress_metric(self) -> None:
        report = EVAL.evaluate()
        lightweight = json.loads(EVAL.LIGHTWEIGHT_REPORT.read_text(encoding="utf-8"))
        expected = {
            item["id"]
            for item in lightweight["cases"]
            if item["metrics"]["required_progress_for_multi_agent"]
        }
        rows = report["transferred_context"]["long_task_rows"]

        self.assertEqual(expected, {item["id"] for item in rows})
        self.assertTrue(rows)
        self.assertTrue(
            all(item["required_progress_for_multi_agent"] is True for item in rows)
        )
        self.assertEqual(
            "candidate-subject-only",
            report["transferred_context"]["measurement_kind"],
        )
        self.assertTrue(
            all("realized_reduction_ratio" not in item for item in rows)
        )

    def test_candidate_transfer_is_measured_without_a_fabricated_baseline(self) -> None:
        transfer = EVAL.evaluate()["transferred_context"]

        self.assertEqual("candidate-subject-only", transfer["measurement_kind"])
        self.assertGreater(transfer["gross_tokens"], 0)
        repair = transfer["categories"]["repair_context"]
        self.assertTrue(repair["source_selectors"])
        self.assertEqual(
            repair["gross_tokens"],
            repair["non_compressible_tokens"] + repair["compressible_tokens"],
        )
        self.assertEqual(0, transfer["categories"]["superseded_evidence"]["gross_tokens"])
        self.assertTrue(transfer["semantic_baseline"]["retained_semantic_equality"])

        isolated = next(
            row
            for row in transfer["long_task_rows"]
            if row["id"] == "isolated-write-parallel-contract"
        )
        task_rows = {
            item["task_id"]: item["projection"]
            for item in isolated["boundary_rows"]
            if item["boundary"] == "task_to_implementation"
        }
        first = "task-isolated-write-parallel-contract-1"
        second = "task-isolated-write-parallel-contract-2"
        self.assertEqual(["module-a/service.py"], task_rows[first]["changed_files"])
        self.assertEqual(["module-b/view.tsx"], task_rows[second]["changed_files"])
        self.assertEqual(
            "isolated-module-tests", task_rows[first]["validation_result"]["evidence_id"]
        )
        self.assertEqual(
            "isolated-module-tests", task_rows[second]["validation_result"]["evidence_id"]
        )

        repair_case = next(
            row
            for row in transfer["long_task_rows"]
            if row["id"] == "repair-and-rereview"
        )
        repair = next(
            item["projection"]
            for item in repair_case["boundary_rows"]
            if item["boundary"] == "review_to_repair"
        )
        self.assertEqual(
            ["initial-service-review-A", "initial-service-review-B"],
            [item["claim"] for item in repair["blocking_findings"]],
        )
        self.assertEqual(
            ["current-task", "current-task"],
            [item["relation"] for item in repair["blocking_findings"]],
        )
        self.assertTrue(
            all(
                set(item) == {"claim", "relation"}
                for item in repair["blocking_findings"]
            )
        )
        self.assertTrue(
            all("outcome" not in item for item in repair["blocking_findings"])
        )
        self.assertEqual(["service.py", "tests/test_service.py"], repair["affected_scope"])
        self.assertEqual(
            {"initial-targeted-test", "previous-diff-review"},
            {item["claim"] for item in repair["invalidated_evidence"]},
        )
        self.assertEqual(
            ["owner-placement-inspection"],
            [item["claim"] for item in repair["reusable_evidence"]],
        )

    def test_boundary_projections_reject_lossy_or_expansive_transfer(self) -> None:
        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        case = next(
            item for item in document["cases"] if item["id"] == "repair-and-rereview"
        )
        projections = EVAL._case_transfer_projections(case)

        for boundary, projection in projections.items():
            for field in EVAL.TRANSFER_PROJECTION_FIELDS[boundary]:
                with self.subTest(boundary=boundary, missing=field):
                    mutated = copy.deepcopy(projection)
                    mutated.pop(field)
                    self.assertTrue(EVAL._transfer_projection_errors(boundary, mutated))

        review = copy.deepcopy(projections["implementation_to_review"])
        review["latest_diff"] = {"changed_files": ["service.py"]}
        self.assertTrue(EVAL._transfer_projection_errors("implementation_to_review", review))

        review = copy.deepcopy(projections["implementation_to_review"])
        review["current_evidence"].append({"claim": "old", "state": "superseded"})
        self.assertTrue(EVAL._transfer_projection_errors("implementation_to_review", review))

        execution = copy.deepcopy(projections["task_to_implementation"])
        execution["validation_result"]["stdout"] = "full command log"
        self.assertTrue(EVAL._transfer_projection_errors("task_to_implementation", execution))

        repair = projections["review_to_repair"]
        self.assertTrue(repair["invalidated_evidence"])
        self.assertFalse(
            {
                item["claim"] for item in repair["invalidated_evidence"]
            }
            & {item["claim"] for item in repair["reusable_evidence"]}
        )
        for relation in ("adjacent", "scope-blocker"):
            with self.subTest(repair_relation=relation):
                invalid = copy.deepcopy(repair)
                invalid["blocking_findings"][0]["relation"] = relation
                self.assertTrue(
                    any(
                        "only material current-task findings" in error
                        for error in EVAL._transfer_projection_errors(
                            "review_to_repair", invalid
                        )
                    )
                )

    def test_consecutive_task_dispatches_use_canonical_task_identity(self) -> None:
        def dispatch(task_id: str) -> dict[str, object]:
            return {
                "action": "dispatch",
                "profile": "task-agent",
                "fixture_capsule": {
                    "contract_type": "task",
                    "task_id": task_id,
                    "status": "in_progress",
                    "acceptance": [f"complete {task_id}"],
                    "verification": ["shared-check"],
                    "review_owner": "review-agent",
                },
            }

        case = {
            "id": "consecutive-task-identity",
            "steps": [
                dispatch("task-A"),
                dispatch("task-B"),
                {"action": "edit", "task_id": "task-A", "path": "a.py"},
                {
                    "action": "adaptive-test-evidence",
                    "task_id": "task-A",
                    "evidence_id": "evidence-A",
                    "freshness": 1,
                    "oracle": "A oracle",
                },
                {"action": "edit", "task_id": "task-B", "path": "b.py"},
                {
                    "action": "adaptive-test-evidence",
                    "task_id": "task-B",
                    "evidence_id": "evidence-B",
                    "freshness": 1,
                    "oracle": "B oracle",
                },
                {
                    "action": "validate",
                    "task_ids": ["task-A", "task-B"],
                    "command": "shared-check",
                    "outcome": "passed",
                    "evidence_id": "shared-validation",
                },
            ],
        }

        rows = {
            projection["task_id"]: projection
            for boundary, projection, _source in EVAL._case_transfer_projection_rows(case)
            if boundary == "task_to_implementation"
        }

        self.assertEqual({"task-A", "task-B"}, set(rows))
        self.assertEqual(["a.py"], rows["task-A"]["changed_files"])
        self.assertEqual(["b.py"], rows["task-B"]["changed_files"])
        self.assertEqual(
            ["evidence-A", "shared-validation"],
            [item["claim"] for item in rows["task-A"]["current_evidence"]],
        )
        self.assertEqual(
            ["evidence-B", "shared-validation"],
            [item["claim"] for item in rows["task-B"]["current_evidence"]],
        )
        self.assertEqual(
            "shared-validation", rows["task-A"]["validation_result"]["evidence_id"]
        )
        self.assertEqual(
            "shared-validation", rows["task-B"]["validation_result"]["evidence_id"]
        )

    def test_repair_projection_uses_complete_current_blocker_window(self) -> None:
        affected = ["a.py", "a_test.py", "b.py"]
        case = {
            "id": "multi-blocker-repair",
            "steps": [
                {
                    "action": "finding",
                    "path": "historical.py",
                    "evidence_id": "historical",
                    "relation": "current-task",
                    "material": True,
                },
                {
                    "action": "review-discipline",
                    "task_id": "original-task",
                    "verdict": "findings",
                    "diff": {
                        "kind": "actual-diff",
                        "artifact": "original.diff",
                        "generation": 1,
                        "changed_files": ["a.py", "b.py"],
                    },
                    "validation": {
                        "evidence_id": "original-validation",
                        "result": "passed",
                        "generation": 1,
                    },
                },
                {
                    "action": "finding",
                    "task_id": "original-task",
                    "review_round_id": "R-original-1",
                    "path": "a.py",
                    "dependent_scope": ["a_test.py"],
                    "evidence_id": "blocker-A",
                    "relation": "current-task",
                    "material": True,
                    "acceptance_impact": "acceptance",
                    "required_validation": ["repair-check"],
                    "required_covering_rereview": {
                        "covered_task_ids": ["original-task"],
                        "same_or_stronger": True,
                    },
                },
                {
                    "action": "finding",
                    "task_id": "original-task",
                    "review_round_id": "R-original-1",
                    "path": "b.py",
                    "evidence_id": "blocker-B",
                    "relation": "current-task",
                    "material": True,
                    "acceptance_impact": "correctness",
                    "required_validation": ["repair-check"],
                    "required_covering_rereview": {
                        "covered_task_ids": ["original-task"],
                        "same_or_stronger": True,
                    },
                },
                {
                    "action": "finding",
                    "path": "noise.py",
                    "evidence_id": "non-material",
                    "relation": "current-task",
                    "material": False,
                    "task_id": "original-task",
                    "review_round_id": "R-original-1",
                },
                {
                    "action": "finding",
                    "path": "resolved.py",
                    "evidence_id": "resolved",
                    "relation": "adjacent",
                    "material": False,
                    "task_id": "original-task",
                    "review_round_id": "R-original-1",
                },
                {
                    "actor": "review-agent",
                    "action": "review",
                    "task_id": "original-task",
                    "review_round_id": "R-original-1",
                    "required_changed_scope_complete": True,
                    "base_dimensions_complete": True,
                    "professional_risk_dimensions_complete": True,
                    "finding_ids": [
                        "blocker-A",
                        "blocker-B",
                        "non-material",
                        "resolved",
                    ],
                },
                {
                    "action": "dispatch",
                    "profile": "task-agent",
                    "fixture_capsule": {
                        "contract_type": "task",
                        "task_id": "original-task",
                        "status": "in_progress",
                        "acceptance": ["resolve current blockers"],
                        "verification": ["repair-check"],
                        "review_owner": "review-agent",
                    },
                },
                {"action": "repair", "task_id": "original-task", "path": "a.py"},
                {
                    "action": "validate",
                    "task_id": "original-task",
                    "command": "repair-check",
                    "outcome": "passed",
                    "evidence_id": "repair-validation",
                },
            ],
        }

        repair = next(
            projection
            for boundary, projection, _source in EVAL._case_transfer_projection_rows(case)
            if boundary == "review_to_repair"
        )

        self.assertEqual(
            ["blocker-A", "blocker-B"],
            [item["claim"] for item in repair["blocking_findings"]],
        )
        self.assertEqual(
            ["current-task", "current-task"],
            [item["relation"] for item in repair["blocking_findings"]],
        )
        self.assertTrue(
            all(
                set(item) == {"claim", "relation"}
                for item in repair["blocking_findings"]
            )
        )
        self.assertTrue(
            all("outcome" not in item for item in repair["blocking_findings"])
        )
        self.assertEqual(affected, repair["affected_scope"])
        self.assertEqual(
            {"original-validation", "previous-diff-review"},
            {item["claim"] for item in repair["invalidated_evidence"]},
        )
        self.assertTrue(
            all(item["scope"] == affected for item in repair["invalidated_evidence"])
        )
        self.assertEqual(
            ["owner-placement-inspection"],
            [item["claim"] for item in repair["reusable_evidence"]],
        )

    def test_review_convergence_projection_preserves_per_finding_obligations(self) -> None:
        obligations = {
            "blocker-A": {
                "finding_id": "blocker-A",
                "relation": "current-task",
                "affected_scope": ["a.py", "a_test.py"],
                "acceptance_or_risk_impact": "acceptance",
                "required_validation": ["targeted-A"],
                "required_covering_rereview": {
                    "covered_task_ids": ["task-A"],
                    "same_or_stronger": True,
                },
            },
            "blocker-B": {
                "finding_id": "blocker-B",
                "relation": "current-task",
                "affected_scope": ["b.py"],
                "acceptance_or_risk_impact": "correctness",
                "required_validation": ["targeted-B"],
                "required_covering_rereview": {
                    "covered_task_ids": ["task-A"],
                    "same_or_stronger": True,
                },
            },
        }
        case = {
            "id": "review-convergence-transfer",
            "steps": [
                {
                    "action": "review-discipline",
                    "task_id": "task-A",
                    "verdict": "findings",
                    "diff": {"kind": "actual-diff", "artifact": "a.diff"},
                    "validation": {"evidence_id": "validation-A"},
                },
                *[
                    {
                        "action": "finding",
                        "task_id": "task-A",
                        "review_round_id": "R-A-1",
                        "path": obligation["affected_scope"][0],
                        "dependent_scope": obligation["affected_scope"][1:],
                        "evidence_id": finding_id,
                        "relation": "current-task",
                        "material": True,
                        "acceptance_impact": obligation[
                            "acceptance_or_risk_impact"
                        ],
                        "required_validation": obligation["required_validation"],
                        "required_covering_rereview": obligation[
                            "required_covering_rereview"
                        ],
                    }
                    for finding_id, obligation in obligations.items()
                ],
                {
                    "actor": "review-agent",
                    "action": "review",
                    "task_id": "task-A",
                    "review_round_id": "R-A-1",
                    "required_changed_scope_complete": True,
                    "base_dimensions_complete": True,
                    "professional_risk_dimensions_complete": True,
                    "finding_ids": ["blocker-A", "blocker-B"],
                },
                {
                    "action": "dispatch",
                    "profile": "task-agent",
                    "fixture_capsule": {
                        "contract_type": "task",
                        "task_id": "task-A",
                        "status": "in_progress",
                        "acceptance": ["resolve A and B"],
                        "verification": ["targeted-A", "targeted-B"],
                        "review_owner": "review-agent",
                    },
                },
            ],
        }

        repair = next(
            projection
            for boundary, projection, _source in EVAL._case_transfer_projection_rows(case)
            if boundary == "review_to_repair"
        )

        self.assertEqual(
            list(obligations.values()), repair["finding_obligations"]
        )
        self.assertEqual(["R-A-1", "task-A"], repair["repair_batch_key"])

        for mutation, batch_key in (
            ("empty-round", ["", "task-A"]),
            ("empty-task", ["R-A-1", ""]),
        ):
            with self.subTest(malformed_batch_key=mutation):
                probe = copy.deepcopy(repair)
                probe["repair_batch_key"] = batch_key
                self.assertTrue(
                    any(
                        "repair_batch_key must bind" in error
                        for error in EVAL._transfer_projection_errors(
                            "review_to_repair", probe
                        )
                    )
                )

        delimiter_case = copy.deepcopy(case)
        for step in delimiter_case["steps"]:
            if step.get("task_id") == "task-A":
                step["task_id"] = "task:A"
            if step.get("review_round_id") == "R-A-1":
                step["review_round_id"] = "R:A:1"
            covering = step.get("required_covering_rereview")
            if isinstance(covering, dict):
                covering["covered_task_ids"] = ["task:A"]
        delimiter_case["steps"][-1]["fixture_capsule"]["task_id"] = "task:A"
        delimiter_repair = next(
            projection
            for boundary, projection, _source in EVAL._case_transfer_projection_rows(
                delimiter_case
            )
            if boundary == "review_to_repair"
        )
        self.assertEqual(
            ["R:A:1", "task:A"], delimiter_repair["repair_batch_key"]
        )
        self.assertTrue(
            all(
                item["required_covering_rereview"]["covered_task_ids"]
                == ["task:A"]
                for item in delimiter_repair["finding_obligations"]
            )
        )

        malformed_findings = {
            "missing-impact": lambda finding: finding.pop("acceptance_impact"),
            "empty-impact": lambda finding: finding.update(acceptance_impact=""),
            "empty-path": lambda finding: finding.update(path=""),
            "non-string-dependent-scope": lambda finding: finding.update(
                dependent_scope=[7]
            ),
            "scalar-dependent-scope": lambda finding: finding.update(
                dependent_scope="scope"
            ),
            "missing-validation": lambda finding: finding.pop("required_validation"),
            "empty-validation": lambda finding: finding.update(required_validation=[]),
            "invalid-validation-member": lambda finding: finding.update(
                required_validation=[7]
            ),
            "missing-covering-rereview": lambda finding: finding.pop(
                "required_covering_rereview"
            ),
            "malformed-covering-rereview": lambda finding: finding.update(
                required_covering_rereview=[]
            ),
            "missing-covering-task": lambda finding: finding.update(
                required_covering_rereview={"same_or_stronger": True}
            ),
            "wrong-covering-task": lambda finding: finding.update(
                required_covering_rereview={
                    "covered_task_ids": ["task-B"],
                    "same_or_stronger": True,
                }
            ),
            "non-covering-rereview": lambda finding: finding.update(
                required_covering_rereview={
                    "covered_task_ids": ["task-A"],
                    "same_or_stronger": False,
                }
            ),
        }
        for mutation, mutate in malformed_findings.items():
            with self.subTest(malformed_finding=mutation):
                probe = copy.deepcopy(case)
                finding = next(
                    step
                    for step in probe["steps"]
                    if step.get("evidence_id") == "blocker-A"
                )
                mutate(finding)
                with self.assertRaisesRegex(
                    ValueError, "per-finding obligations|dependent_scope"
                ):
                    list(EVAL._case_transfer_projection_rows(probe))

        malformed_obligations = {
            "empty-impact": lambda item: item.update(
                acceptance_or_risk_impact=""
            ),
            "empty-scope-member": lambda item: item.update(
                affected_scope=[""]
            ),
            "non-string-scope-member": lambda item: item.update(
                affected_scope=[7]
            ),
            "empty-validation-member": lambda item: item.update(
                required_validation=[""]
            ),
            "non-string-validation-member": lambda item: item.update(
                required_validation=[7]
            ),
            "missing-covering-task": lambda item: item.update(
                required_covering_rereview={"same_or_stronger": True}
            ),
            "wrong-covering-task": lambda item: item.update(
                required_covering_rereview={
                    "covered_task_ids": ["task-B"],
                    "same_or_stronger": True,
                }
            ),
        }
        for mutation, mutate in malformed_obligations.items():
            with self.subTest(malformed_projection=mutation):
                probe = copy.deepcopy(repair)
                mutate(probe["finding_obligations"][0])
                self.assertTrue(
                    any(
                        "each Finding must preserve" in error
                        for error in EVAL._transfer_projection_errors(
                            "review_to_repair", probe
                        )
                    )
                )

        for mutation, expected in (
            ("unclosed-boundary", None),
            ("missing-review-round", None),
            ("changed-task-id", None),
            ("cross-task-finding", ["blocker-A"]),
        ):
            with self.subTest(mutation=mutation):
                probe = copy.deepcopy(case)
                if mutation == "unclosed-boundary":
                    probe["steps"] = [
                        step for step in probe["steps"]
                        if step.get("action") != "review"
                    ]
                elif mutation == "missing-review-round":
                    for step in probe["steps"]:
                        if step.get("action") in {"finding", "review"}:
                            step.pop("review_round_id", None)
                elif mutation == "changed-task-id":
                    probe["steps"][-1]["fixture_capsule"]["task_id"] = "task-B"
                else:
                    probe["steps"][2]["task_id"] = "task-B"
                    probe["steps"][2]["required_covering_rereview"][
                        "covered_task_ids"
                    ] = ["task-B"]
                window = EVAL._current_blocking_review_window(
                    probe["steps"], len(probe["steps"]) - 1
                )
                if expected is None:
                    self.assertIsNone(window)
                else:
                    self.assertEqual(
                        expected,
                        [item["evidence_id"] for item in window[1]],
                    )

    def test_rereview_findings_create_a_second_repair_transfer_occurrence(self) -> None:
        def finding(finding_id: str, round_id: str) -> dict[str, object]:
            return {
                "action": "finding",
                "task_id": "task-A",
                "review_round_id": round_id,
                "path": "a.py",
                "dependent_scope": [],
                "evidence_id": finding_id,
                "relation": "current-task",
                "material": True,
                "acceptance_impact": "correctness",
                "required_validation": ["targeted-A"],
                "required_covering_rereview": {
                    "covered_task_ids": ["task-A"],
                    "same_or_stronger": True,
                },
            }

        def closing(action: str, finding_id: str, round_id: str) -> dict[str, object]:
            result = {
                "actor": "review-agent",
                "action": action,
                "task_id": "task-A",
                "review_round_id": round_id,
                "finding_ids": [finding_id],
            }
            if action == "review":
                result.update(
                    required_changed_scope_complete=True,
                    base_dimensions_complete=True,
                    professional_risk_dimensions_complete=True,
                )
            else:
                result.update(
                    rereview_checks=[
                        "inherited-finding-resolution",
                        "repair-diff-correctness",
                        "repair-regression",
                        "repair-affected-scope-and-transitive-dependents",
                        "frozen-acceptance-invariant-contract-and-professional-risk-boundary",
                    ],
                    rereview_scope_expanded=False,
                    frozen_boundary_status="preserved",
                    frozen_professional_risk_boundary_status="preserved",
                )
            return result

        def repair_dispatch() -> dict[str, object]:
            return {
                "action": "dispatch",
                "profile": "task-agent",
                "fixture_capsule": {
                    "contract_type": "task",
                    "task_id": "task-A",
                    "status": "in_progress",
                    "acceptance": ["resolve current finding"],
                    "verification": ["targeted-A"],
                    "review_owner": "review-agent",
                },
            }

        case = {
            "id": "rereview-second-repair-transfer",
            "steps": [
                {
                    "action": "review-discipline",
                    "task_id": "task-A",
                    "verdict": "findings",
                    "diff": {"kind": "actual-diff", "artifact": "r1.diff"},
                    "validation": {"evidence_id": "validation-r1"},
                },
                finding("finding-r1", "R-A-1"),
                closing("review", "finding-r1", "R-A-1"),
                repair_dispatch(),
                {"action": "repair", "task_id": "task-A", "path": "a.py"},
                {
                    "action": "validate",
                    "task_id": "task-A",
                    "command": "targeted-A",
                    "outcome": "passed",
                    "evidence_id": "validation-r2",
                },
                {
                    "action": "review-discipline",
                    "task_id": "task-A",
                    "verdict": "findings",
                    "diff": {"kind": "actual-diff", "artifact": "r2.diff"},
                    "validation": {"evidence_id": "validation-r2"},
                },
                finding("finding-r2", "R-A-2"),
                closing("re-review", "finding-r2", "R-A-2"),
                repair_dispatch(),
            ],
        }

        rows = [
            projection
            for boundary, projection, _source in EVAL._case_transfer_projection_rows(
                case
            )
            if boundary == "review_to_repair"
        ]

        self.assertEqual(2, len(rows))
        self.assertEqual(
            [["R-A-1", "task-A"], ["R-A-2", "task-A"]],
            [row["repair_batch_key"] for row in rows],
        )
        self.assertEqual(
            [["finding-r1"], ["finding-r2"]],
            [
                [item["finding_id"] for item in row["finding_obligations"]]
                for row in rows
            ],
        )

        malformed_rereview_completion = {
            "missing-focus": lambda event: event.pop("rereview_checks"),
            "malformed-focus": lambda event: event.update(rereview_checks="all"),
            "reordered-focus": lambda event: event.update(
                rereview_checks=list(reversed(event["rereview_checks"]))
            ),
            "expanded-scope": lambda event: event.update(
                rereview_scope_expanded=True
            ),
            "missing-frozen-boundary": lambda event: event.pop(
                "frozen_boundary_status"
            ),
            "invalid-frozen-boundary": lambda event: event.update(
                frozen_boundary_status="unknown"
            ),
            "invalid-professional-risk-boundary": lambda event: event.update(
                frozen_professional_risk_boundary_status="invalidated"
            ),
        }
        for mutation, mutate in malformed_rereview_completion.items():
            with self.subTest(malformed_rereview_completion=mutation):
                probe = copy.deepcopy(case)
                rereview = next(
                    step
                    for step in probe["steps"]
                    if step.get("action") == "re-review"
                )
                mutate(rereview)
                repair_rows = [
                    projection
                    for boundary, projection, _source in EVAL._case_transfer_projection_rows(
                        probe
                    )
                    if boundary == "review_to_repair"
                ]
                self.assertEqual(
                    [["R-A-1", "task-A"]],
                    [row["repair_batch_key"] for row in repair_rows],
                )

    def test_repair_task_projections_are_bound_to_their_own_generation(self) -> None:
        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        case = next(
            item for item in document["cases"] if item["id"] == "repair-and-rereview"
        )

        projection_rows = EVAL._case_transfer_projection_rows(case)
        rows = [
            projection
            for boundary, projection, _source in projection_rows
            if boundary == "task_to_implementation"
        ]
        repair_rows = [
            projection
            for boundary, projection, _source in projection_rows
            if boundary == "review_to_repair"
        ]

        self.assertEqual([1, 2, 3], [row["freshness"] for row in rows])
        self.assertEqual(
            [
                "initial-targeted-test",
                "repair-targeted-test",
                "second-repair-targeted-test",
            ],
            [row["validation_result"]["evidence_id"] for row in rows],
        )
        self.assertEqual(
            [
                ["targeted-test"],
                ["targeted-test"],
                ["targeted-test"],
            ],
            [row["commands"] for row in rows],
        )
        self.assertEqual(
            [
                {
                    "task-repair-and-rereview-1-green",
                    "initial-targeted-test",
                },
                {
                    "task-repair-and-rereview-1-repair-green",
                    "repair-targeted-test",
                },
                {
                    "task-repair-and-rereview-1-second-repair-red",
                    "task-repair-and-rereview-1-second-repair-green",
                    "second-repair-targeted-test",
                },
            ],
            [
                {item["claim"] for item in row["current_evidence"]}
                for row in rows
            ],
        )
        self.assertEqual(
            [
                ["review-repair-and-rereview-1", "task-repair-and-rereview-1"],
                ["review-repair-and-rereview-2", "task-repair-and-rereview-1"],
            ],
            [row["repair_batch_key"] for row in repair_rows],
        )

    def test_adjacent_and_scope_blocker_findings_never_create_repair_projection(
        self,
    ) -> None:
        for relation in ("adjacent", "scope-blocker"):
            with self.subTest(relation=relation):
                case = {
                    "id": f"reject-{relation}-repair-projection",
                    "steps": [
                        {
                            "action": "review-discipline",
                            "task_id": "task-A",
                            "verdict": "findings",
                        },
                        {
                            "action": "finding",
                            "path": "a.py",
                            "evidence_id": f"{relation}-finding",
                            "relation": relation,
                            "material": True,
                        },
                        {
                            "action": "dispatch",
                            "profile": "task-agent",
                            "fixture_capsule": {
                                "contract_type": "task",
                                "task_id": "repair-task",
                            },
                        },
                    ],
                }
                self.assertIsNone(
                    EVAL._current_blocking_review_window(case["steps"], 2)
                )

    def test_evaluator_source_contains_no_registered_token_baseline(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("long_task_baseline_gross_tokens", source)
        self.assertNotIn("category_baseline_gross_tokens", source)
        self.assertNotIn('"baseline_gross_tokens": 47_302', source)

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

    def test_focus_cost_binds_only_the_core_derived_subject_actor_profile(self) -> None:
        expected = {
            "finding": "review-agent",
            "same-pattern": "task-agent",
            "repair": "task-agent",
            "review-level": "review-agent",
            "analysis-level": "main-control-agent",
            "review-readiness": "main-control-agent",
            "task-execution": "task-agent",
            "cost": "task-agent",
        }
        for scenario, role in expected.items():
            case = self._focus_case(scenario)
            measured = EVAL._focus_case_cost(
                self._focus_row(case), case, ROOT, subject="candidate", host="codex"
            )
            profile_tokens = next(
                item["tokens"]
                for item in measured["actor_profile_binding"]["generated_profiles"]
                if item["host"] == "codex"
            )
            with self.subTest(scenario=scenario):
                self.assertEqual(role, measured["actor_profile_binding"]["actor"])
                self.assertEqual(role, measured["actor_profile_binding"]["profile"])
                self.assertEqual(
                    profile_tokens, measured["component_tokens"]["always_loaded"]
                )
                self.assertEqual(
                    0, measured["component_tokens"]["dispatch_instructions"]
                )
                self.assertEqual(
                    profile_tokens, measured["total_task_tokens"]
                )
                self.assertEqual(
                    list(EVAL.FOCUS_PROFILE_HOSTS),
                    measured["actor_profile_binding"]["host_order"],
                )
                self.assertEqual(
                    list(EVAL.FOCUS_PROFILE_HOSTS),
                    [
                        item["host"]
                        for item in measured["actor_profile_binding"][
                            "generated_profiles"
                        ]
                    ],
                )
                self.assertEqual(
                    "oracle-only-not-loaded",
                    measured["native_sources"]["fixture_case"]["content_scope"],
                )
                self.assertEqual(
                    "authority-only-not-loaded",
                    measured["native_sources"]["core"]["content_scope"],
                )
        capability = self._focus_case("task-execution")
        measured = EVAL._focus_case_cost(
            self._focus_row(capability), capability, ROOT, subject="candidate", host="codex"
        )
        self.assertEqual("task-agent", measured["actor_profile_binding"]["profile"])

    def test_focus_cost_core_growth_does_not_change_loaded_tokens(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._copy_focus_subject(root)
            case = self._focus_case("finding")
            before = EVAL._focus_case_cost(
                self._focus_row(case), case, root, subject="candidate", host="codex"
            )
            core_path = root / "src/control-model/core-contracts.json"
            core = json.loads(core_path.read_text(encoding="utf-8"))
            core["s2d_unloaded_authority_probe"] = "full Core growth is not loaded"
            core_path.write_text(
                json.dumps(core, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            after = EVAL._focus_case_cost(
                self._focus_row(case), case, root, subject="candidate", host="codex"
            )
        self.assertNotEqual(
            before["native_sources"]["core"]["sha256"],
            after["native_sources"]["core"]["sha256"],
        )
        self.assertEqual(before["component_tokens"], after["component_tokens"])
        self.assertEqual(before["total_task_tokens"], after["total_task_tokens"])

    def test_focus_cost_profile_mutation_is_scoped_to_its_bound_consumer(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._copy_focus_subject(root)
            finding = self._focus_case("finding")
            cost = self._focus_case("cost")
            finding_before = EVAL._focus_case_cost(
                self._focus_row(finding), finding, root, subject="candidate", host="codex"
            )
            cost_before = EVAL._focus_case_cost(
                self._focus_row(cost), cost, root, subject="candidate", host="codex"
            )
            profile_path = root / "dist/codex/project/.codex/agents/task-agent.toml"
            profile_path.write_text(
                profile_path.read_text(encoding="utf-8")
                + "\nS2D scoped profile token probe.\n",
                encoding="utf-8",
            )
            profile_sha256 = hashlib.sha256(profile_path.read_bytes()).hexdigest()
            manifest_path = root / (
                "dist/universal/skills/"
                f"{EVAL.RUNTIME_NAME}/.changeforge-build-manifest.json"
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["agent_profile_sha256"]["codex"]["task-agent"] = (
                profile_sha256
            )
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            finding_after = EVAL._focus_case_cost(
                self._focus_row(finding), finding, root, subject="candidate", host="codex"
            )
            cost_after = EVAL._focus_case_cost(
                self._focus_row(cost), cost, root, subject="candidate", host="codex"
            )
        self.assertEqual(
            finding_before["total_task_tokens"], finding_after["total_task_tokens"]
        )
        self.assertGreater(
            cost_after["total_task_tokens"], cost_before["total_task_tokens"]
        )

    def test_focus_cost_binding_fails_closed_on_unknown_disagreement_missing_and_stale(self) -> None:
        mutations = (
            "unknown",
            "disagreement",
            "missing-profile",
            "symlink-profile",
            "missing-manifest-host",
            "stale-manifest",
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                self._copy_focus_subject(root)
                case = self._focus_case("finding")
                if mutation == "unknown":
                    case["scenario"] = "unknown-focus-scenario"
                elif mutation == "disagreement":
                    core_path = root / "src/control-model/core-contracts.json"
                    core = json.loads(core_path.read_text(encoding="utf-8"))
                    core["review_discipline_contract"]["effective_level_policy"][
                        "finding_merge_owner"
                    ] = "task-agent"
                    core_path.write_text(
                        json.dumps(core, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )
                elif mutation == "missing-profile":
                    (
                        root
                        / "dist/codex/project/.codex/agents/review-agent.toml"
                    ).unlink()
                elif mutation == "symlink-profile":
                    profile_path = (
                        root
                        / "dist/codex/project/.codex/agents/review-agent.toml"
                    )
                    profile_path.unlink()
                    profile_path.symlink_to(
                        ROOT
                        / "dist/codex/project/.codex/agents/review-agent.toml"
                    )
                else:
                    manifest_path = root / (
                        "dist/universal/skills/recommended/"
                        ".changeforge-build-manifest.json"
                    )
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    if mutation == "missing-manifest-host":
                        manifest["agent_profile_sha256"]["copilot"].pop(
                            "review-agent"
                        )
                    else:
                        manifest["agent_profile_sha256"]["codex"][
                            "review-agent"
                        ] = "0" * 64
                    manifest_path.write_text(
                        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )
                with self.assertRaises(ValueError):
                    EVAL._focus_case_cost(
                        self._focus_row(case), case, root, subject="candidate", host="codex"
                    )

    def test_end_to_end_ab_cost_observation_does_not_authorize_or_reject_quality(self) -> None:
        equal = EVAL._compare_end_to_end_subjects(
            self._ab_subject(100), self._ab_subject(100)
        )
        self.assertEqual("pass", equal["status"])
        self.assertEqual(0, equal["aggregate"]["delta"])
        below_legacy_ratio = EVAL._compare_end_to_end_subjects(
            self._ab_subject(100), self._ab_subject(99)
        )
        self.assertEqual("pass", below_legacy_ratio["status"])
        one_over = EVAL._compare_end_to_end_subjects(
            self._ab_subject(100), self._ab_subject(101)
        )
        self.assertEqual("pass", one_over["status"])
        self.assertEqual("candidate-higher-cost", one_over["cost_observation"]["status"])
        self.assertEqual([], one_over["errors"])

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

    def test_quality_first_gate_rejects_quality_regression_despite_lower_cost(self) -> None:
        cost = EVAL._compare_end_to_end_subjects(
            self._ab_subject(100), self._ab_subject(75)
        )
        gate = EVAL._quality_first_cost_gate(
            behavior_evidence=self._quality_evidence("regression"),
            codegen_evidence=self._quality_evidence(
                "no_effect", kind="blind-old-new-codegen-quality"
            ),
            cost_comparison=cost,
        )
        self.assertEqual("fail", gate["status"])
        self.assertEqual("regression", gate["verdict"])
        self.assertTrue(gate["candidate_rejected"])
        self.assertFalse(gate["cost_frontier"]["eligible"])

    def test_quality_first_gate_selects_equal_quality_lower_cost_frontier(self) -> None:
        cost = EVAL._compare_end_to_end_subjects(
            self._ab_subject(100), self._ab_subject(75)
        )
        gate = EVAL._quality_first_cost_gate(
            behavior_evidence=self._quality_evidence("no_effect"),
            codegen_evidence=self._quality_evidence(
                "no_effect", kind="blind-old-new-codegen-quality"
            ),
            cost_comparison=cost,
        )
        self.assertEqual("pass", gate["status"])
        self.assertEqual("no_effect", gate["verdict"])
        self.assertTrue(gate["quality_preserved"])
        self.assertEqual("selected-lower-cost", gate["cost_frontier"]["status"])
        self.assertTrue(gate["cost_frontier"]["eligible"])
        self.assertEqual(0, gate["cost_frontier"]["metrics"]["turns"]["delta"])
        self.assertEqual(-10, gate["cost_frontier"]["metrics"]["elapsed_ms"]["delta"])

    def test_quality_first_gate_preserves_hardening_only_verdict(self) -> None:
        gate = EVAL._quality_first_cost_gate(
            behavior_evidence=self._quality_evidence("hardening_only"),
            codegen_evidence=self._quality_evidence(
                "no_effect", kind="blind-old-new-codegen-quality"
            ),
            cost_comparison=EVAL._compare_end_to_end_subjects(
                self._ab_subject(100), self._ab_subject(100)
            ),
        )
        self.assertEqual("hardening_only", gate["verdict"])
        self.assertTrue(gate["quality_preserved"])
        self.assertEqual("selected-lower-cost", gate["cost_frontier"]["status"])

    def test_quality_first_gate_reports_insufficient_structural_evidence(self) -> None:
        structural = self._quality_evidence(
            "not_enough_evidence",
            evidence_class="structural_only",
            live_status="not_collected",
        )
        gate = EVAL._quality_first_cost_gate(
            behavior_evidence=structural,
            codegen_evidence={
                **structural,
                "evaluation_kind": "captured-fixture-comparison",
            },
            cost_comparison=EVAL._compare_end_to_end_subjects(
                self._ab_subject(100), self._ab_subject(75)
            ),
        )
        self.assertEqual("pass", gate["status"])
        self.assertEqual("not_enough_evidence", gate["verdict"])
        self.assertEqual("structural-only", gate["claim_boundary"])
        self.assertFalse(gate["quality_preserved"])
        self.assertFalse(gate["cost_frontier"]["eligible"])
        self.assertEqual("not_collected", gate["live_evidence"]["behavior"])
        self.assertEqual("not_collected", gate["live_evidence"]["codegen"])
        self.assertEqual("not_collected", gate["live_evidence"]["elapsed_ms"])

    def test_quality_consumer_uses_detached_validated_behavior_authority(self) -> None:
        self.assertEqual(
            VALIDATION.behavior_eval_authority(VALIDATION.CORE_CONTRACTS),
            EVAL.BEHAVIOR_EVAL_MODEL,
        )
        malformed = copy.deepcopy(EVAL.BEHAVIOR_EVAL_MODEL)
        malformed["verdicts"].remove("regression")
        with mock.patch.object(EVAL, "BEHAVIOR_EVAL_MODEL", malformed):
            with self.assertRaisesRegex(ValueError, "Behavior Eval authority"):
                EVAL._quality_first_cost_gate(
                    behavior_evidence=self._quality_evidence("regression"),
                    codegen_evidence=self._quality_evidence(
                        "no_effect", kind="blind-old-new-codegen-quality"
                    ),
                    cost_comparison=EVAL._compare_end_to_end_subjects(
                        self._ab_subject(100), self._ab_subject(75)
                    ),
                )

    def test_candidate_changed_paths_reject_tracked_symlinks_before_read_or_execute(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            target = root / "safe.txt"
            target.write_text("safe", encoding="utf-8")
            paths = (
                "scripts/eval-agent-behavior.py",
                "src/control-model/core-contracts.json",
                "evals/agent-behavior/comparison-fixtures/structural.yaml",
                "src/agent-profiles/role-agents.json",
            )
            for relative in paths:
                link = root / relative
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(target)
                with self.subTest(relative=relative):
                    with self.assertRaisesRegex(ValueError, "symlink|regular|contain"):
                        EVAL._validate_candidate_changed_paths(root, {relative})
                link.unlink()

    @staticmethod
    def _host_complete_ab_subject(total_tokens: int) -> dict[str, object]:
        return RenderedContextBudgetTests._ab_subject(total_tokens)

    def test_s3c_comparison_rejects_hybrid_or_incomplete_host_matrix(self) -> None:
        baseline = self._host_complete_ab_subject(100)
        candidate = self._host_complete_ab_subject(100)
        self.assertEqual(
            "pass", EVAL._compare_end_to_end_subjects(baseline, candidate)["status"]
        )

        for mutation in ("hybrid", "missing-host", "cross-host"):
            before = copy.deepcopy(baseline)
            broken = copy.deepcopy(candidate)
            if mutation == "hybrid":
                before["cases"] = before["cases"][:1]
                broken["cases"] = broken["cases"][:1]
            elif mutation == "missing-host":
                before["cases"] = before["cases"][:-1]
                broken["cases"] = broken["cases"][:-1]
            else:
                broken["cases"][0]["host"] = "claude"
            with self.subTest(mutation=mutation):
                report = EVAL._compare_end_to_end_subjects(before, broken)
                self.assertEqual("fail", report["status"])
                self.assertTrue(
                    any("host" in error for error in report["errors"]),
                    report["errors"],
                )

    def test_s3c_comparison_rejects_selector_envelope_component_overlap(self) -> None:
        baseline = self._host_complete_ab_subject(100)
        candidate = self._host_complete_ab_subject(100)
        for subject in (baseline, candidate):
            case = subject["cases"][0]
            case["native_sources"]["components"].append(
                {
                    "host": "codex",
                    "kind": "native-selector-envelope",
                    "bucket": "selector",
                    "physical_path": "fixture:measured-case:step:1:selector",
                    "sha256": "a" * 64,
                    "tokens": 5,
                    "load_count": 1,
                    "content_scope": "complete-native-dispatch-partition",
                }
            )
        report = EVAL._compare_end_to_end_subjects(baseline, candidate)
        self.assertEqual("fail", report["status"])
        self.assertTrue(
            any("overlap" in error for error in report["errors"]), report["errors"]
        )

    def test_s3c_comparison_requires_each_host_to_conserve_cost_and_authority(self) -> None:
        baseline = self._host_complete_ab_subject(100)
        candidate = self._host_complete_ab_subject(99)
        candidate["cases"][0]["component_tokens"]["cross_agent_transfer"] += 2
        candidate["cases"][0]["total_task_tokens"] += 2
        report = EVAL._compare_end_to_end_subjects(baseline, candidate)
        self.assertEqual("pass", report["status"])
        self.assertLess(report["aggregate"]["candidate"], report["aggregate"]["baseline"])
        self.assertEqual("mixed-cost-deltas", report["cost_observation"]["status"])

        crossed = self._host_complete_ab_subject(100)
        crossed["cases"][0]["native_sources"]["selection_authority_bundles"][0][
            "host"
        ] = "copilot"
        report = EVAL._compare_end_to_end_subjects(baseline, crossed)
        self.assertEqual("fail", report["status"])
        self.assertTrue(
            any("cross-host" in error for error in report["errors"]), report["errors"]
        )

    def test_ordinary_raw_route_case_cannot_hide_one_token_regression_in_host_totals(self) -> None:
        baseline = self._host_complete_ab_subject(100)
        candidate = self._host_complete_ab_subject(100)
        for subject in (baseline, candidate):
            original = subject["cases"]
            duplicate = []
            for row in original:
                row["mapping_state"] = "raw-route-equal"
                row["raw_route_obligations"] = copy.deepcopy(
                    row["route_obligations"]
                )
                second = copy.deepcopy(row)
                second["id"] = f"second::{row['host']}"
                second["logical_case_id"] = "second"
                duplicate.append(second)
            subject["cases"].extend(duplicate)
            subject["identity"]["logical_case_count"] = 2
            subject["identity"]["host_pair_count"] = 6

        for row in candidate["cases"]:
            delta = 1 if row["logical_case_id"] == "measured-case" else -2
            row["component_tokens"]["cross_agent_transfer"] += delta
            row["structural"]["handoff_tokens"] += delta
            row["total_task_tokens"] += delta
        report = EVAL._compare_end_to_end_subjects(baseline, candidate)
        self.assertEqual("pass", report["status"])
        self.assertLess(report["aggregate"]["candidate"], report["aggregate"]["baseline"])
        self.assertTrue(
            all(
                host["total_task_tokens"]["candidate"]
                < host["total_task_tokens"]["baseline"]
                for host in report["host_matrix"]["hosts"].values()
            )
        )
        self.assertEqual(3, len(report["ordinary_route_regressions"]))
        self.assertTrue(
            all(row["total_task_tokens"]["delta"] == 1 for row in report["ordinary_route_regressions"])
        )
        markdown = EVAL._render_end_to_end_projection_markdown(report)
        self.assertIn("Ordinary raw-route-equal gate regressions/digest: **3**", markdown)
        self.assertIn("**1 token(s)**", markdown)

    def test_end_to_end_ab_gate_uses_measured_subjects_and_conservation(self) -> None:
        conserved = EVAL._compare_end_to_end_subjects(
            self._ab_subject(100), self._ab_subject(100)
        )
        self.assertEqual("pass", conserved["status"])
        self.assertEqual(0.0, conserved["aggregate"]["reduction_ratio"])
        row = conserved["cases"][0]
        self.assertEqual(
            {"baseline": 100, "candidate": 100, "delta": 0},
            row["total_task_tokens"],
        )
        self.assertEqual(
            {"baseline": 30, "candidate": 30, "delta": 0},
            row["component_tokens"]["cross_agent_transfer"],
        )
        self.assertEqual(
            "combined-router/v1",
            row["selection_authority_bundles"]["baseline"][0]["schema"],
        )

        lost_bundle = self._ab_subject(100)
        lost_bundle["cases"][0]["native_sources"].pop(
            "selection_authority_bundles"
        )
        lost = EVAL._compare_end_to_end_subjects(
            lost_bundle, self._ab_subject(100)
        )
        self.assertEqual("fail", lost["status"])
        self.assertTrue(
            any("loses measured selection authority bundles" in error for error in lost["errors"]),
            lost["errors"],
        )

        one_over = EVAL._compare_end_to_end_subjects(
            self._ab_subject(100), self._ab_subject(101)
        )
        self.assertEqual("pass", one_over["status"])
        self.assertEqual("candidate-higher-cost", one_over["cost_observation"]["status"])

    def test_end_to_end_ab_actor_profiles_require_all_hosts_without_min_selection(self) -> None:
        def add_binding(subject: dict[str, object]) -> None:
            rows = [
                {
                    "host": host,
                    "path": f"dist/{host}/profile",
                    "sha256": str(index + 1) * 64,
                    "tokens": tokens,
                    "content_scope": "complete-subject-native-profile",
                }
                for index, (host, tokens) in enumerate(
                    zip(EVAL.FOCUS_PROFILE_HOSTS, (5, 7, 8))
                )
            ]
            for case in subject["cases"]:
                host = case["host"]
                selected = next(item for item in rows if item["host"] == host)
                case["total_task_tokens"] += (
                    selected["tokens"] - case["component_tokens"]["always_loaded"]
                )
                case["component_tokens"]["always_loaded"] = selected["tokens"]
                case["actor_profile_binding"] = {
                    "actor": "task-agent",
                    "profile": "task-agent",
                    "scenario": "cost",
                    "core_authority": {"path": "core", "sha256": "a" * 64},
                    "profile_authority": {"path": "profiles", "sha256": "b" * 64},
                    "host_order": list(EVAL.FOCUS_PROFILE_HOSTS),
                    "measured_host": host,
                    "generated_profiles": rows,
                    "runtime_binding": {
                        "runtime": EVAL.RUNTIME_NAME,
                        "hosts": {
                            row_host: {
                                "manifest_sha256": "c" * 64,
                                "profile_sha256": rows[index]["sha256"],
                            }
                            for index, row_host in enumerate(EVAL.FOCUS_PROFILE_HOSTS)
                        },
                    }
                }

        baseline = self._ab_subject(100)
        candidate = self._ab_subject(100)
        add_binding(baseline)
        add_binding(candidate)
        report = EVAL._compare_end_to_end_subjects(baseline, candidate)
        self.assertEqual("pass", report["status"])
        self.assertEqual(
            ["claude"],
            [row["host"] for row in report["cases"][0]["actor_profile_differences"]],
        )

        incomplete = copy.deepcopy(candidate)
        incomplete["cases"][0]["actor_profile_binding"]["host_order"] = [
            "codex"
        ]
        report = EVAL._compare_end_to_end_subjects(baseline, incomplete)
        self.assertEqual("fail", report["status"])
        self.assertTrue(any("host order" in error for error in report["errors"]))

        selected_minimum = copy.deepcopy(candidate)
        selected_minimum["cases"][0]["component_tokens"]["always_loaded"] = 1
        selected_minimum["cases"][0]["total_task_tokens"] -= 4
        report = EVAL._compare_end_to_end_subjects(baseline, selected_minimum)
        self.assertEqual("fail", report["status"])
        self.assertTrue(
            any("not fully accounted" in error for error in report["errors"]),
            report["errors"],
        )

    def test_end_to_end_ab_gate_accepts_only_closed_integration_scope(self) -> None:
        expected = frozenset(
            {
                "scripts/build.py",
                "scripts/eval-agent-lightweight.py",
                "scripts/eval-rendered-context-budget.py",
                "scripts/validate-agent-profiles.py",
                "scripts/validate-control-plane-prompt.py",
                "scripts/validate-control-skills.py",
                "scripts/validate-skill-routing.py",
                "scripts/validate-task-contracts.py",
                "scripts/validation_utils.py",
                "src/agent-profiles/role-agents.json",
                "src/control-prompts/main-control-agent.md",
                "src/control-skills/engineering-control-plane/references/implementation-handoff-template.md",
                "src/control-skills/engineering-control-plane/references/professional-skill-router.md",
                "src/control-skills/engineering-control-plane/references/review-handoff-template.md",
                "evals/agent-light-trajectories/cases.yaml",
                "reports/hookless-control-plane-eval.json",
                "reports/rendered-context-budget.json",
                "reports/rendered-context-budget.md",
                "tests/scripts/test_authority_delivery_repair.py",
                "tests/scripts/test_build_safety.py",
                "tests/scripts/test_eval_agent_lightweight_layer3_references.py",
                "tests/scripts/test_eval_agent_lightweight_utility.py",
                "tests/scripts/test_eval_rendered_context_budget.py",
                "tests/scripts/test_foundation_selector_authority.py",
                "tests/scripts/test_rds_005_public_projection.py",
                "tests/scripts/test_rds_006_agent_execution_discipline.py",
                "tests/scripts/test_rds_006_task_handoff_context.py",
                "tests/scripts/test_selector_jit_domain_parity.py",
                "tests/scripts/test_skill_routing_roles.py",
                "tests/scripts/test_validate_agent_profiles.py",
                "tests/scripts/test_validate_control_plane_prompt.py",
                "tests/scripts/test_validate_control_skills.py",
                "tests/scripts/test_validate_docs_consistency.py",
                "tests/scripts/test_validate_task_contracts.py",
                "tests/test_hookless_build_install.py",
                "scripts/validate-built-skill-reference-links.py",
                "tests/scripts/test_built_professional_root_projection.py",
                "tests/scripts/test_validate_built_skill_reference_links.py",
                "tests/scripts/test_context_content_relocation.py",
            }
        )
        expected |= EVAL.AB_P4_INTEGRATION_WRITE_PATHS
        self.assertIn(
            "src/control-model/core-contracts.json", EVAL.AB_ALLOWED_WRITE_PATHS
        )
        self.assertNotIn(
            "src/registry/professional-skills.yaml", EVAL.AB_ALLOWED_WRITE_PATHS
        )
        self.assertLessEqual(
            {
                "scripts/validate-task-contracts.py",
                "src/control-skills/engineering-control-plane/references/review-handoff-template.md",
                "tests/scripts/test_validate_task_contracts.py",
            },
            EVAL.AB_ALLOWED_WRITE_PATHS,
            "Core/Review Handoff A/B patches require their shared contract consumer",
        )
        self.assertEqual(expected, EVAL.AB_ALLOWED_WRITE_PATHS)

    def test_end_to_end_ab_gate_rejects_fabricated_or_reduced_coverage(self) -> None:
        fabricated = self._ab_subject(100)
        fabricated["identity"].pop("measurement_source")
        report = EVAL._compare_end_to_end_subjects(
            fabricated, self._ab_subject(75)
        )
        self.assertEqual("fail", report["status"])
        self.assertTrue(any("measured subject" in error for error in report["errors"]))

        for field in ("professional", "layer3", "domain", "review"):
            with self.subTest(route_field=field):
                baseline = self._ab_subject(100)
                candidate = self._ab_subject(75)
                baseline["cases"][0]["route_obligations"][field] = [field]
                report = EVAL._compare_end_to_end_subjects(baseline, candidate)
                self.assertEqual("fail", report["status"])
                self.assertTrue(
                    any("route obligations" in error for error in report["errors"])
                )

        reduced = self._ab_subject(75)
        reduced["cases"][0]["structural"]["reference_load_count"] = 0
        report = EVAL._compare_end_to_end_subjects(self._ab_subject(100), reduced)
        self.assertEqual("fail", report["status"])
        self.assertTrue(any("coverage" in error for error in report["errors"]))

    def test_end_to_end_ab_gate_rejects_absent_components_and_fabricated_totals(self) -> None:
        missing = self._ab_subject(100)
        missing["cases"][0]["component_tokens"].pop("targeted_reference")
        report = EVAL._compare_end_to_end_subjects(missing, self._ab_subject(75))
        self.assertEqual("fail", report["status"])
        self.assertTrue(any("complete component" in error for error in report["errors"]))

        fabricated = self._ab_subject(100)
        fabricated["cases"][0]["total_task_tokens"] += 1
        report = EVAL._compare_end_to_end_subjects(fabricated, self._ab_subject(75))
        self.assertEqual("fail", report["status"])
        self.assertTrue(any("component sum" in error for error in report["errors"]))

    def test_subject_case_cost_changes_when_measured_source_component_changes(self) -> None:
        case = {
            "id": "source-sensitive",
            "measurements": [
                {
                    "host": "codex",
                    "runtime": "recommended",
                    "total_tokens": 40,
                    "components": [
                        {"kind": "worker_profile", "tokens": 10},
                        {"kind": "primary_skill", "tokens": 20},
                        {"kind": "dispatch_capsule", "tokens": 10},
                    ],
                }
            ],
        }
        transfer = {
            "gross_tokens": 5,
            "boundary_rows": [],
            "categories": {
                name: {"gross_tokens": 0, "occurrence_count": 0}
                for name in EVAL.TRANSFER_CATEGORY_ORDER
            },
        }
        metrics = {
            "selector_load_count": 1,
            "reference_load_count": 0,
            "same_assignment_duplicate_read_count": 0,
        }
        measured = EVAL._subject_case_cost(case, transfer, metrics, {})
        changed = copy.deepcopy(case)
        changed["measurements"][0]["components"][1]["tokens"] += 7
        changed["measurements"][0]["total_tokens"] += 7
        remeasured = EVAL._subject_case_cost(changed, transfer, metrics, {})
        self.assertEqual(7, remeasured["total_task_tokens"] - measured["total_task_tokens"])
        self.assertEqual(
            7,
            remeasured["component_tokens"]["professional"]
            - measured["component_tokens"]["professional"],
        )

    def test_manifest_input_mismatch_fails_before_subject_comparison(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            dist = Path(raw)
            expected = {"sha256": "a" * 64, "file_count": 1}
            root = dist / EVAL.RUNTIME_NAME
            root.mkdir(parents=True)
            (root / ".changeforge-build-manifest.json").write_text(
                json.dumps(
                    {
                        "profile": EVAL.RUNTIME_NAME,
                        "compiled_layer3_format": EVAL.COMPILED_LAYER3_FORMAT,
                        "authoritative_build_inputs": {
                            "sha256": "b" * 64,
                            "file_count": 1,
                        },
                    }
                ),
                encoding="utf-8",
            )
            identity, errors = EVAL._manifest_input_identity(dist, expected)
        self.assertEqual({}, identity)
        self.assertEqual(1, len(errors))
        self.assertTrue(all("authoritative input mismatch" in error for error in errors))

    def test_native_validator_binding_cannot_bypass_candidate_validity(self) -> None:
        report = {
            "status": "pass",
            "fixture_schema_version": 2,
            "evidence_scope": "deterministic-fixtures",
            "errors": [],
        }
        EVAL._require_native_validator_report(
            report, subject="baseline", expected_fixture_schema=2
        )
        EVAL._require_native_validator_report(
            report, subject="candidate", expected_fixture_schema=2
        )
        for mutation in ("failed", "errors", "schema", "scope"):
            with self.subTest(mutation=mutation):
                changed = copy.deepcopy(report)
                if mutation == "failed":
                    changed["status"] = "fail"
                elif mutation == "errors":
                    changed["errors"] = ["invalid native trajectory"]
                elif mutation == "schema":
                    changed["fixture_schema_version"] = None
                else:
                    changed["evidence_scope"] = "candidate-substitution"
                with self.assertRaises(ValueError):
                    EVAL._require_native_validator_report(
                        changed, subject="candidate", expected_fixture_schema=2
                    )

    def test_native_dispatch_partition_is_complete_and_unambiguous(self) -> None:
        step = {
            "actor": "main-control-agent",
            "action": "dispatch",
            "profile": "task-agent",
            "mode": "normal",
            "primary_skill": "repository-tooling-change-builder",
            "layer3_skills": ["targeted-validation-selection"],
            "professional_references": [],
            "layer3_references": [],
            "fixture_capsule": {"contract_version": "native-v1", "goal": "measure"},
        }
        selector, instructions = EVAL._native_dispatch_partition(step)
        self.assertNotIn("fixture_capsule", selector)
        self.assertEqual({"fixture_capsule": step["fixture_capsule"]}, instructions)
        self.assertEqual(
            set(step), set(selector) | {"fixture_capsule"}
        )
        combined = copy.deepcopy(step)
        combined["utility_capsule"] = {"contract_version": "native-v1"}
        selector, instructions = EVAL._native_dispatch_partition(combined)
        self.assertEqual(
            {"fixture_capsule", "utility_capsule"}, set(instructions)
        )
        self.assertEqual(
            set(combined), set(selector) | {"fixture_capsule", "utility_capsule"}
        )

        for mutation in ("missing-profile", "missing-capsule", "malformed-capsule"):
            with self.subTest(mutation=mutation):
                changed = copy.deepcopy(step)
                if mutation == "missing-profile":
                    changed.pop("profile")
                elif mutation == "missing-capsule":
                    changed.pop("fixture_capsule")
                else:
                    changed["utility_capsule"] = "not-a-native-capsule"
                with self.assertRaises(ValueError):
                    EVAL._native_dispatch_partition(changed)

    def test_native_contract_identity_records_unversioned_utility_capsule(self) -> None:
        document = {
            "schema_version": 2,
            "cases": [],
            "scheduling_cases": [],
            "utility_cases": [
                {
                    "id": "native-utility",
                    "steps": [
                        {
                            "action": "dispatch",
                            "profile": "task-agent",
                            "fixture_capsule": {
                                "contract_version": "changeforge.fixture-capsule.v2",
                                "contract_type": "utility",
                            },
                            "utility_capsule": {"mode": "validation-only/no-edit"},
                        }
                    ],
                }
            ],
            "task_focus_cases": [],
        }
        identity = EVAL._native_contract_identity(document)
        utility = next(
            row
            for row in identity["capsule_contracts"]
            if row["capsule_field"] == "utility_capsule"
        )
        self.assertIsNone(utility["contract_version"])
        self.assertEqual("unversioned-native-auxiliary", utility["version_state"])

    def test_native_transfer_measurement_uses_complete_handoff_bytes(self) -> None:
        document = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        source_case = next(
            case for case in document["cases"] if case["id"] == "single-module-feature"
        )
        handoff = copy.deepcopy(
            next(
                step
                for step in source_case["steps"]
                if step.get("action") == "implementation-handoff"
            )
        )
        case = {"id": "native-transfer", "steps": [handoff]}
        lightweight_module = EVAL._load_current_lightweight_module(
            ROOT / "scripts/eval-agent-lightweight.py"
        )
        measured = EVAL._native_transfer_measurement(case, lightweight_module)
        expected = EVAL.count_o200k_base_tokens(EVAL._canonical_json_text(handoff))
        self.assertEqual(expected, measured["gross_tokens"])
        self.assertEqual(expected, measured["handoff_tokens"])
        changed = copy.deepcopy(case)
        changed["steps"][0]["exact_change_evidence"]["artifact"] = (
            "diff --git a/module-a/service.py b/module-a/service.py\n"
            "--- a/module-a/service.py\n"
            "+++ b/module-a/service.py\n"
            "@@ -1 +1 @@\n-old\n+changed\n"
        )
        changed_measurement = EVAL._native_transfer_measurement(
            changed, lightweight_module
        )
        self.assertNotEqual(
            measured["handoff_rows"][0]["sha256"],
            changed_measurement["handoff_rows"][0]["sha256"],
        )
        with self.assertRaises(ValueError):
            EVAL._native_transfer_measurement(
                {"id": "native-transfer", "steps": [{"actor": "task-agent"}]},
                lightweight_module,
            )

    def test_canonical_focus_mapping_closes_all_current_cases(self) -> None:
        current = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        baseline = _focus_baseline_document()
        mapping = EVAL._canonical_focus_mapping(current, baseline)
        self.assertEqual([], mapping["errors"])
        self.assertEqual("pass", mapping["status"])
        self.assertEqual(59, len(mapping["rows"]))
        self.assertEqual(
            {
                "raw-route-equal",
                "source-derived-semantic-equivalent",
                "protected-semantic-extension",
            },
            {row["state"] for row in mapping["rows"]},
        )
        mapped = {
            row["canonical_id"]: row["baseline_native_id"]
            for row in mapping["rows"]
            if row["canonical_id"] != row["baseline_native_id"]
        }
        self.assertEqual(EVAL.FOCUS_CURRENT_ONLY_MAP, mapped)
        protected = {
            row["canonical_id"]: row["protected_projection"]
            for row in mapping["rows"]
            if row["state"] == "protected-semantic-extension"
        }
        self.assertEqual(
            {
                "l4-risk-depth-not-frequency",
                "engineering-choice-not-user-choice",
            },
            set(protected),
        )
        self.assertEqual(EVAL.FOCUS_PROTECTED_SEMANTIC_EXTENSIONS, protected)
        for projection in protected.values():
            self.assertEqual(
                projection["candidate_actor"], projection["baseline_actor"]
            )

    def test_canonical_focus_mapping_fails_closed_on_mapping_defects(self) -> None:
        current = {
            "task_focus_cases": [
                {
                    "id": "current",
                    "scenario": "review-readiness",
                    "decision": {"review_dispatches": 0},
                    "expected_valid": True,
                    "expected_error": None,
                }
            ]
        }
        baseline = {"task_focus_cases": []}
        for overrides, expected in (
            ({}, "unmapped"),
            ({"current": ["one", "two"]}, "ambiguous"),
            ({"current": "missing"}, "missing-native-binding"),
        ):
            with self.subTest(expected=expected):
                report = EVAL._canonical_focus_mapping(
                    current, baseline, overrides=overrides
                )
                self.assertTrue(any(expected in error for error in report["errors"]))
                self.assertEqual("fail", report["status"])

        baseline["task_focus_cases"] = [
            {
                "id": "native",
                "scenario": "review-readiness",
                "decision": {"review_dispatches": 1},
                "expected_valid": True,
                "expected_error": None,
            }
        ]
        report = EVAL._canonical_focus_mapping(
            current, baseline, overrides={"current": "native"}
        )
        self.assertTrue(any("semantic-mismatch" in error for error in report["errors"]))

    def test_protected_focus_extensions_fail_closed_on_binding_drift(self) -> None:
        current = json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        baseline = _focus_baseline_document()
        target = "l4-risk-depth-not-frequency"
        mutations = []

        missing = copy.deepcopy(EVAL.FOCUS_PROTECTED_SEMANTIC_EXTENSIONS)
        missing.pop(target)
        mutations.append((missing, current, "protected-projection-missing"))

        for field, expected in (
            ("candidate_native_sha256", "stale-candidate-native-hash"),
            ("baseline_native_sha256", "stale-baseline-native-hash"),
            ("candidate_semantic_sha256", "stale-candidate-semantic-hash"),
        ):
            protection = copy.deepcopy(EVAL.FOCUS_PROTECTED_SEMANTIC_EXTENSIONS)
            protection[target][field] = "0" * 64
            mutations.append((protection, current, expected))

        actor_mismatch = copy.deepcopy(EVAL.FOCUS_PROTECTED_SEMANTIC_EXTENSIONS)
        actor_mismatch[target]["baseline_actor"] = "main-control-agent"
        mutations.append((actor_mismatch, current, "protected-actor-mismatch"))

        semantic_drift = copy.deepcopy(current)
        drift_case = next(
            case
            for case in semantic_drift["task_focus_cases"]
            if case["id"] == target
        )
        drift_case["decision"]["professional_gates"] = 2
        drift_protection = copy.deepcopy(EVAL.FOCUS_PROTECTED_SEMANTIC_EXTENSIONS)
        drift_text = json.dumps(
            drift_case,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        drift_protection[target]["candidate_native_sha256"] = __import__(
            "hashlib"
        ).sha256(drift_text.encode("utf-8")).hexdigest()
        mutations.append(
            (drift_protection, semantic_drift, "stale-candidate-semantic-hash")
        )

        for protection, candidate, expected in mutations:
            with self.subTest(expected=expected):
                report = EVAL._canonical_focus_mapping(
                    candidate,
                    baseline,
                    protected_extensions=protection,
                )
                self.assertEqual("fail", report["status"])
                self.assertTrue(
                    any(expected in error for error in report["errors"]),
                    report["errors"],
                )

    def test_canonical_trajectory_mapping_preserves_routes_and_exposes_native_split(self) -> None:
        baseline_case = {
            "id": "payment-case",
            "steps": [
                {
                    "action": "dispatch",
                    "profile": "task-agent",
                    "primary_skill": "repository-tooling-change-builder",
                    "layer3_skills": ["payment-trading-extension"],
                    "professional_references": [],
                    "layer3_references": [
                        "payment-trading-extension/references/checklist.md"
                    ],
                    "fixture_capsule": {"contract_version": "native-v1"},
                }
            ],
        }
        candidate_case = copy.deepcopy(baseline_case)
        candidate_case["steps"][0]["layer3_references"] = [
            "payment-trading-extension/references/duplicate-financial-effect-control.md"
        ]
        candidate_document = {
            "cases": [candidate_case],
            "scheduling_cases": [],
            "utility_cases": [],
        }
        baseline_document = {
            "cases": [baseline_case],
            "scheduling_cases": [],
            "utility_cases": [],
        }
        report = EVAL._canonical_trajectory_mapping(
            candidate_document,
            baseline_document,
            candidate_root=ROOT,
            baseline_root=ROOT,
        )
        self.assertEqual([], report["errors"])
        self.assertEqual("source-derived-semantic-equivalent", report["rows"][0]["state"])
        self.assertFalse(report["rows"][0]["raw_physical_route_equal"])

        baseline_case["id"] = "api-contract-change"
        candidate_case["id"] = "api-contract-change"
        baseline_case["steps"][0]["primary_skill"] = "architecture-impact-reviewer"
        candidate_case["steps"][0]["primary_skill"] = "architecture-impact-reviewer"
        baseline_case["steps"][0]["layer3_references"] = []
        candidate_case["steps"][0]["layer3_references"] = []
        baseline_case["steps"][0]["professional_references"] = [
            "references/architecture-output-and-gates.md"
        ]
        candidate_case["steps"][0]["professional_references"] = [
            "references/consumer-and-data-impact.md"
        ]
        baseline_document["cases"] = [baseline_case]
        candidate_document["cases"] = [candidate_case]
        report = EVAL._canonical_trajectory_mapping(
            candidate_document,
            baseline_document,
            candidate_root=ROOT,
            baseline_root=ROOT,
        )
        self.assertEqual([], report["errors"])
        self.assertEqual("source-derived-semantic-equivalent", report["rows"][0]["state"])

        candidate_case["steps"][0]["primary_skill"] = "quality-test-gate"
        report = EVAL._canonical_trajectory_mapping(
            candidate_document,
            baseline_document,
            candidate_root=ROOT,
            baseline_root=ROOT,
        )
        self.assertTrue(any("obligation-mismatch" in error for error in report["errors"]))

    def test_subject_comparison_rejects_hidden_native_reference_differences(self) -> None:
        baseline = self._ab_subject(100)
        candidate = self._ab_subject(75)
        binding = {
            "semantic_obligation": "payment-duplicate-financial-effect-control",
            "physical_path": "src/domain/references/checklist.md",
            "reference_type": "decision-checklist",
            "required_outputs": ["checklist-result", "residual-risk"],
            "registry_sha256": "a" * 64,
            "source_sha256": "b" * 64,
            "tokens": 10,
            "content_scope": "complete-native-bytes",
        }
        baseline["cases"][0]["native_reference_bindings"] = [binding]
        candidate["cases"][0]["native_reference_bindings"] = [
            {
                **binding,
                "physical_path": "src/domain/references/split.md",
                "reference_type": "targeted",
                "required_outputs": ["selected-approach", "residual-risk"],
                "source_sha256": "c" * 64,
                "tokens": 8,
            }
        ]
        report = EVAL._compare_end_to_end_subjects(baseline, candidate)
        self.assertEqual("pass", report["status"])
        differences = next(
            row["native_reference_differences"]
            for row in report["cases"]
            if row["host"] == "codex"
        )
        self.assertEqual(1, len(differences))
        self.assertEqual("source-derived-semantic-equivalent", differences[0]["state"])

        candidate["cases"][0]["native_reference_bindings"][0].pop("physical_path")
        report = EVAL._compare_end_to_end_subjects(baseline, candidate)
        self.assertEqual("fail", report["status"])
        self.assertTrue(any("hidden physical" in error for error in report["errors"]))

        repeated = {
            **binding,
            "physical_path": "src/domain/references/repeated.md",
        }
        baseline["cases"][0]["native_reference_bindings"] = [binding, repeated]
        candidate = self._ab_subject(75)
        candidate["cases"][0]["native_reference_bindings"] = [binding, repeated]
        report = EVAL._compare_end_to_end_subjects(baseline, candidate)
        self.assertEqual("pass", report["status"])
        self.assertEqual(
            [0, 1],
            [
                row["occurrence"]
                for row in next(
                    item["native_reference_differences"]
                    for item in report["cases"]
                    if item["host"] == "codex"
                )
            ],
        )

        candidate["cases"][0]["native_reference_bindings"] = [binding]
        report = EVAL._compare_end_to_end_subjects(baseline, candidate)
        self.assertEqual("fail", report["status"])
        self.assertTrue(
            any("occurrence cardinality" in error for error in report["errors"])
        )

    def test_lightweight_join_requires_current_retained_semantic_equality(self) -> None:
        report = json.loads(EVAL.LIGHTWEIGHT_REPORT.read_text(encoding="utf-8"))
        expected_case_ids = {item["id"] for item in report["cases"]}
        positive = next(
            item for item in report["orchestration_fixtures"] if item["expected_valid"]
        )
        mutations = {}
        missing = copy.deepcopy(report)
        next(
            item
            for item in missing["orchestration_fixtures"]
            if item["id"] == positive["id"]
        ).pop("retained_semantic_equality")
        mutations["missing"] = missing
        unequal = copy.deepcopy(report)
        next(
            item
            for item in unequal["orchestration_fixtures"]
            if item["id"] == positive["id"]
        )["retained_semantic_equality"] = False
        mutations["unequal"] = unequal

        for label, mutation in mutations.items():
            with self.subTest(mutation=label):
                with self.assertRaisesRegex(ValueError, "retained semantic equality"):
                    EVAL._long_task_ids_from_lightweight(mutation, expected_case_ids)

    def test_lightweight_join_rejects_missing_required_progress_metric(self) -> None:
        source = {
            "schema_version": 2,
            "fixture_schema_version": 2,
            "status": "pass",
            "evidence_scope": "deterministic-fixtures",
            "fixture_count": 1,
            "cases": [{"id": "one", "metrics": {}}],
        }
        with self.assertRaisesRegex(ValueError, "required_progress_for_multi_agent"):
            EVAL._long_task_ids_from_lightweight(source, {"one"})

    def test_fixture_capsule_mutations_fail_closed(self) -> None:
        document = EVAL.json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        original = copy.deepcopy(document["cases"][0]["steps"][1])
        mutations = []

        free_text = copy.deepcopy(original)
        free_text["dispatch_capsule"] = "x"
        mutations.append(free_text)

        placeholder = copy.deepcopy(original)
        placeholder["fixture_capsule"]["goal"] = "x"
        mutations.append(placeholder)

        drift = copy.deepcopy(original)
        drift["fixture_capsule"]["goal"] += "."
        mutations.append(drift)

        missing = copy.deepcopy(original)
        missing["fixture_capsule"].pop("verification")
        mutations.append(missing)

        wrong_version = copy.deepcopy(original)
        wrong_version["fixture_capsule"]["contract_version"] += "x"
        mutations.append(wrong_version)

        for index, step in enumerate(mutations):
            with self.subTest(mutation=index):
                errors = EVAL._dispatch_metadata_errors("mutated", 1, step)
                self.assertTrue(errors)
                self.assertTrue(any("invalid fixture Capsule" in item for item in errors))

    def test_analysis_modes_require_their_exact_templates(self) -> None:
        document = EVAL.json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        case = next(
            item
            for item in document["cases"]
            if item["id"] == "source-backed-payment-retry-proof"
        )
        original = case["steps"][1]

        mismatch = copy.deepcopy(original)
        mismatch["fixture_capsule"]["template"] = "engineering-brief"
        with self.assertRaisesRegex(
            FixtureCapsuleError,
            "requires template 'source-backed-answer'",
        ):
            validate_and_render_fixture_capsule(mismatch)

        unknown = copy.deepcopy(original)
        unknown["mode"] = "unknown-analysis-mode"
        with self.assertRaisesRegex(
            FixtureCapsuleError,
            "unsupported mode 'unknown-analysis-mode'",
        ):
            validate_and_render_fixture_capsule(unknown)

    def test_payment_retry_fixture_rebinds_to_the_exact_split_reference(self) -> None:
        document = EVAL.json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        case = next(
            item
            for item in document["cases"]
            if item["id"] == "source-backed-payment-retry-proof"
        )
        self.assertIn("selected References", case["prompt"])
        self.assertNotIn("indexed checklists", case["prompt"])
        step = case["steps"][1]
        expected = [
            "test-strategy/references/checklist.md",
            "payment-trading-extension/references/duplicate-financial-effect-control.md",
        ]
        self.assertEqual(expected, step["layer3_references"])
        capsule = step["fixture_capsule"]
        self.assertEqual(
            [
                "src/foundation/capabilities/test-strategy/references/checklist.md",
                "src/domain-extensions/payment-trading-extension/references/duplicate-financial-effect-control.md",
            ],
            capsule["scope"],
        )
        self.assertEqual(
            "21a62db2a192bec9c753b38b857260b112290ffab7b3351ed302fefcf01bb08b",
            capsule["canonical_sha256"],
        )
        rendered = validate_and_render_fixture_capsule(step)
        self.assertEqual(236, EVAL.count_o200k_base_tokens(rendered))
        selected = json.dumps(case, sort_keys=True)
        self.assertNotIn("financial-role-and-state-authority", selected)
        self.assertNotIn("provider-venue-event-authentication", selected)
        self.assertEqual(
            "src/domain-extensions/payment-trading-extension/references/duplicate-financial-effect-control.md",
            case["steps"][4]["path"],
        )

    def test_semantic_placeholders_fail_with_synchronized_hash(self) -> None:
        document = EVAL.json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        original = copy.deepcopy(document["cases"][0]["steps"][1])
        original_text = validate_and_render_fixture_capsule(original)
        mutations = (
            ("goal", 0, "x" * 20),
            ("allowed_write_scope", 0, "xxx"),
            ("expected_output", 0, "x" * 10),
            ("verification", 0, "TBD..."),
            ("stop_conditions", 0, "placeholder_1"),
            ("acceptance", 0, "repeat " * 20),
            ("goal", 0, "ｘ" * 20),
        )

        for field, item, replacement in mutations:
            with self.subTest(field=field, replacement=replacement):
                step = copy.deepcopy(original)
                replacement = " ".join(replacement.split())
                previous = step["fixture_capsule"][field]
                if isinstance(previous, list):
                    previous_text = previous[item]
                    previous[item] = replacement
                else:
                    previous_text = previous
                    step["fixture_capsule"][field] = replacement
                forged_render = original_text.replace(previous_text, replacement, 1)
                self.assertNotEqual(original_text, forged_render)
                step["fixture_capsule"]["canonical_sha256"] = hashlib.sha256(
                    forged_render.encode("utf-8")
                ).hexdigest()

                errors = EVAL._dispatch_metadata_errors("mutated", 1, step)

                self.assertTrue(errors)
                self.assertTrue(
                    any("invalid fixture Capsule" in item for item in errors),
                    errors,
                )

    def test_typed_capsule_fields_accept_short_technical_values(self) -> None:
        document = EVAL.json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        task = copy.deepcopy(document["cases"][0]["steps"][1])
        task["mode"] = "go"
        task["primary_skill"] = "todo-service"
        task["fixture_capsule"]["goal"] = "Review AA mapping and BB contract evidence."
        task["fixture_capsule"]["allowed_read_scope"] = [
            "./x",
            "./go",
            "a.py",
            "Makefile",
            "README",
            "module-a/**",
            "src/{api,web}/**/*.ts",
            "c++/x.cc",
        ]
        task["fixture_capsule"]["allowed_write_scope"] = list(
            task["fixture_capsule"]["allowed_read_scope"]
        )
        task["fixture_capsule"]["inputs"] = [
            "HTTP_2",
            "HEAD~1",
            "R",
            "rg",
            "v1",
            "AA",
            "owner.py",
            "Run targeted checks",
        ]
        task["fixture_capsule"]["canonical_sha256"] = canonical_capsule_sha256(
            task,
            task["fixture_capsule"],
        )
        self.assertTrue(validate_and_render_fixture_capsule(task))

        utility = copy.deepcopy(document["utility_cases"][1]["steps"][1])
        utility["utility_capsule"]["inputs"] = {
            "validation_targets": ["HTTP_2", "a.py", "src/**"],
        }
        utility["utility_capsule"]["commands_allowed"].extend(
            ["pytest", "go test ./...", "rg TODO", "./scripts/check.sh"]
        )
        utility["fixture_capsule"]["canonical_sha256"] = canonical_capsule_sha256(
            utility,
            utility["fixture_capsule"],
        )
        self.assertTrue(validate_and_render_fixture_capsule(utility))

    def test_utility_semantics_reject_synchronized_schema_forgery(self) -> None:
        document = EVAL.json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        original = copy.deepcopy(document["utility_cases"][0]["steps"][1])
        original_text = validate_and_render_fixture_capsule(original)
        mutations = []

        mode = copy.deepcopy(original)
        mode["mode"] = "unknown/no-edit"
        mode["utility_capsule"]["mode"] = "unknown/no-edit"
        mutations.append(
            (mode, original_text.replace("diff-export/no-edit", "unknown/no-edit", 1))
        )

        enforcement = copy.deepcopy(original)
        enforcement["utility_capsule"]["no_edit_enforcement"] = "host-enforced"
        mutations.append(
            (
                enforcement,
                original_text.replace(
                    "## No-edit Enforcement\n\nsupported\n\n",
                    "## No-edit Enforcement\n\nhost-enforced\n\n",
                    1,
                ),
            )
        )

        root = copy.deepcopy(original)
        root["utility_capsule"]["allowed_scope"]["workspace_root"] = "whole repository"
        mutations.append(
            (
                root,
                original_text.replace(
                    "Workspace Root: .",
                    "Workspace Root: whole repository",
                    1,
                ),
            )
        )

        inputs = copy.deepcopy(original)
        inputs["utility_capsule"]["inputs"] = {"anything": "some plausible value"}
        old_inputs = (
            '## Inputs\n\n- artifact_delivery: "supplied-content"\n'
            '- base: "HEAD~1"\n- head: "HEAD"\n'
        )
        new_inputs = '## Inputs\n\n- anything: "some plausible value"\n'
        mutations.append((inputs, original_text.replace(old_inputs, new_inputs, 1)))

        change_set = copy.deepcopy(original)
        change_set["utility_capsule"]["workspace_baseline"]["change_set"] = [
            "anything at all"
        ]
        mutations.append(
            (
                change_set,
                original_text.replace(
                    "Change Set:\n- tracked:none\n- staged:none\n- untracked:none",
                    "Change Set:\n- anything at all",
                    1,
                ),
            )
        )

        chained = copy.deepcopy(original)
        previous = chained["utility_capsule"]["commands_allowed"][-1]
        replacement = "git status && rm -rf ."
        chained["utility_capsule"]["commands_allowed"][-1] = replacement
        mutations.append((chained, original_text.replace(previous, replacement, 1)))

        for index, (step, forged_render) in enumerate(mutations):
            with self.subTest(mutation=index):
                self.assertNotEqual(original_text, forged_render)
                step["fixture_capsule"]["canonical_sha256"] = hashlib.sha256(
                    forged_render.encode("utf-8")
                ).hexdigest()

                errors = EVAL._dispatch_metadata_errors("mutated-utility", 1, step)

                self.assertTrue(errors)
                self.assertTrue(
                    any("invalid fixture Capsule" in item for item in errors),
                    errors,
                )

    def test_main_measurement_does_not_add_control_prompt_component(self) -> None:
        report = EVAL.evaluate()

        self.assertEqual(16, report["fixture_count"])
        self.assertEqual(
            report["dispatch_count"] * len(EVAL.HOST_PROFILE_ROOTS),
            report["measurement_count"],
        )
        catalog = {item["id"]: item for item in report["component_catalog"]}
        for measurement in report["main_contexts"]:
            kinds = [catalog[item]["kind"] for item in measurement["component_ids"]]
            self.assertEqual(["rendered_main_profile", "control_skill"], kinds)
            self.assertIn("not added", measurement["control_prompt_accounting"])
        for case in report["cases"]:
            for measurement in case["measurements"]:
                capsule = next(
                    catalog[item]
                    for item in measurement["component_ids"]
                    if catalog[item]["kind"] == "dispatch_capsule"
                )
                self.assertEqual(
                    measurement["canonical_capsule_sha256"],
                    capsule["sha256"],
                )
                self.assertEqual(
                    measurement["canonical_capsule_tokens"],
                    capsule["tokens"],
                )
                self.assertGreater(measurement["canonical_capsule_tokens"], 0)

        self.assertEqual(8, report["aggregate"]["loaded_layer3_reference_count"])
        self.assertEqual(
            8 * len(EVAL.HOST_PROFILE_ROOTS),
            report["aggregate"]["measured_layer3_reference_component_count"],
        )
        self.assertEqual(
            [
                "ai-product-extension/references/checklist.md",
                "module-boundary-design/references/benchmarks-and-enforcement.md",
                "payment-trading-extension/references/duplicate-financial-effect-control.md",
                "release-rollback/references/benchmarks-and-patterns.md",
                "release-rollback/references/evidence-patterns.md",
                "test-strategy/references/checklist.md",
                "transaction-consistency/references/evidence-patterns.md",
                "web-security/references/checklist.md",
            ],
            report["aggregate"]["loaded_layer3_reference_logical_ids"],
        )
        migration = next(item for item in report["cases"] if item["id"] == "data-migration")
        measured = [
            item
            for item in migration["measurements"]
            if item["loaded_layer3_reference_count"] == 1
        ]
        self.assertEqual(len(EVAL.HOST_PROFILE_ROOTS), len(measured))
        for item in measured:
            nested = [
                catalog[component_id]
                for component_id in item["component_ids"]
                if catalog[component_id]["kind"] == "layer3_reference"
            ]
            self.assertEqual(1, len(nested))
            self.assertNotIn("/index.md", nested[0]["path"])

        expected_by_case = {
            "source-backed-payment-retry-proof": {
                "payment-trading-extension/references/duplicate-financial-effect-control.md",
                "test-strategy/references/checklist.md",
            },
            "module-boundary-benchmark-review": {
                "module-boundary-design/references/benchmarks-and-enforcement.md",
            },
            "security-ssrf-boundary": {
                "web-security/references/checklist.md",
            },
            "shared-workspace-serial-write": {
                "ai-product-extension/references/checklist.md",
            },
            "release-rollback": {
                "release-rollback/references/benchmarks-and-patterns.md",
                "release-rollback/references/evidence-patterns.md",
            },
        }
        for case_id, expected_ids in expected_by_case.items():
            fixture = next(item for item in report["cases"] if item["id"] == case_id)
            selected = [
                measurement
                for measurement in fixture["measurements"]
                if measurement["loaded_layer3_reference_count"]
            ]
            self.assertEqual(len(EVAL.HOST_PROFILE_ROOTS), len(selected))
            for measurement in selected:
                with self.subTest(case=case_id, host=measurement["host"], runtime=measurement["runtime"]):
                    self.assertEqual(
                        expected_ids,
                        set(measurement["loaded_layer3_reference_logical_ids"]),
                    )

        source_backed = next(
            item
            for item in report["cases"]
            if item["id"] == "source-backed-payment-retry-proof"
        )
        for measurement in source_backed["measurements"]:
            mode_references = [
                catalog[component_id]
                for component_id in measurement["component_ids"]
                if catalog[component_id]["kind"] == "mode_reference"
            ]
            self.assertEqual(1, len(mode_references))
            self.assertTrue(
                mode_references[0]["path"].endswith(
                    "/engineering-change-analysis/references/source-backed-answer.md"
                )
            )

        reliability = next(
            item
            for item in report["cases"]
            if item["id"] == "cache-stampede-reliability"
        )
        evidence_measurements = [
            measurement
            for measurement in reliability["measurements"]
            if measurement["professional_references"]
            == ["references/evidence-patterns.md"]
        ]
        self.assertEqual(
            len(EVAL.HOST_PROFILE_ROOTS), len(evidence_measurements)
        )
        for measurement in evidence_measurements:
            targeted = [
                catalog[component_id]
                for component_id in measurement["component_ids"]
                if catalog[component_id]["kind"] == "targeted_reference"
            ]
            self.assertEqual(1, len(targeted))
            self.assertTrue(
                targeted[0]["path"].endswith(
                    "/reliability-observability-gate/references/evidence-patterns.md"
                )
            )

    def test_authoritative_dag_direct_task_nodes_use_analyzed_task_budget(
        self,
    ) -> None:
        document = EVAL.json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        fixture_cases = {
            str(case["id"]): case
            for key in ("cases", "scheduling_cases")
            for case in document[key]
        }
        expected_measurement_coordinates = {
            (host, EVAL.RUNTIME_NAME)
            for host in EVAL.HOST_PROFILE_ROOTS
        }

        for (case_id, step_index), (
            template,
            dependency,
        ) in AUTHORITATIVE_DAG_NODES.items():
            with self.subTest(case=case_id, step=step_index, contract="fixture"):
                case = fixture_cases[case_id]
                step = case["steps"][step_index]
                capsule = step["fixture_capsule"]
                self.assertEqual("direct", case["kind"])
                self.assertEqual("task-agent", step["profile"])
                self.assertNotIn("utility_capsule", step)
                self.assertEqual("task", capsule["contract_type"])
                self.assertEqual(template, capsule["template"])
                self.assertEqual(AUTHORITATIVE_DAG_INPUTS, capsule["inputs"])
                self.assertEqual([dependency], capsule["dependencies"])
                self.assertIn(
                    AUTHORITATIVE_DAG_EVIDENCE_BY_CASE[case_id],
                    [
                        item.get("evidence")
                        for item in case["steps"]
                        if isinstance(item, dict)
                        and item.get("action") == "progress"
                    ],
                )
                self.assertFalse(
                    any(
                        isinstance(item, dict)
                        and item.get("action") == "dispatch"
                        and item.get("profile") == "analysis-agent"
                        for item in case["steps"]
                    )
                )

        report = EVAL.evaluate()
        measurements_by_case = {
            str(case["id"]): case["measurements"]
            for case in report["cases"]
        }
        selected = [
            measurement
            for case_id, step_index in AUTHORITATIVE_DAG_NODES
            for measurement in measurements_by_case[case_id]
            if measurement["step"] == step_index
        ]
        self.assertEqual(5 * 3, len(selected))
        for case_id, step_index in AUTHORITATIVE_DAG_NODES:
            node_measurements = [
                measurement
                for measurement in measurements_by_case[case_id]
                if measurement["step"] == step_index
            ]
            self.assertEqual(3, len(node_measurements))
            self.assertEqual(
                expected_measurement_coordinates,
                {
                    (
                        measurement["host"],
                        measurement["runtime"],
                    )
                    for measurement in node_measurements
                },
            )
            for measurement in node_measurements:
                with self.subTest(
                    case=case_id,
                    step=step_index,
                    host=measurement["host"],
                    runtime_name=measurement["runtime"],
                ):
                    self.assertEqual(
                        "analyzed_task",
                        measurement["budget_class"],
                    )

    def test_authoritative_dag_analyzed_task_budget_predicate_is_closed(
        self,
    ) -> None:
        document = EVAL.json.loads(EVAL.FIXTURES.read_text(encoding="utf-8"))
        release_cases = {
            str(case["id"]): case for case in document["cases"]
        }
        positive_case = release_cases["isolated-write-parallel-contract"]
        base_step = copy.deepcopy(positive_case["steps"][2])
        analysis_step = copy.deepcopy(
            next(
                step
                for case in document["cases"]
                if case["kind"] == "analyzed"
                for step in case["steps"]
                if step.get("action") == "dispatch"
                and step.get("profile") == "analysis-agent"
            )
        )
        analyzed_task_step = copy.deepcopy(
            next(
                step
                for case in document["cases"]
                if case["kind"] == "analyzed"
                for step in case["steps"]
                if step.get("action") == "dispatch"
                and step.get("profile") == "task-agent"
            )
        )
        utility_step = copy.deepcopy(
            next(
                step
                for case in document["utility_cases"]
                for step in case["steps"]
                if step.get("action") == "dispatch"
                and step.get("profile") == "task-agent"
            )
        )
        direct_task_step = copy.deepcopy(
            next(
                step
                for case in document["cases"]
                for step in case["steps"]
                if step.get("action") == "dispatch"
                and step.get("profile") == "task-agent"
                and step.get("fixture_capsule", {}).get("template")
                == "direct-task"
            )
        )
        repair_task_step = copy.deepcopy(
            next(
                step
                for case in document["cases"]
                for step in case["steps"]
                if step.get("action") == "dispatch"
                and step.get("profile") == "task-agent"
                and step.get("fixture_capsule", {}).get("template")
                == "repair-task"
            )
        )

        progress = {
            "actor": "main-control-agent",
            "action": "progress",
            "checkpoint_type": "start/path",
            "evidence": AUTHORITATIVE_DAG_EVIDENCE_BY_CASE[
                "isolated-write-parallel-contract"
            ],
            "evidence_anchor": "fixture:budget-classification:path",
        }
        alternate_progress = {
            "actor": "main-control-agent",
            "action": "progress",
            "checkpoint_type": "start/path",
            "evidence": AUTHORITATIVE_DAG_EVIDENCE_BY_CASE[
                "shared-workspace-serial-write"
            ],
            "evidence_anchor": (
                "fixture:budget-classification:alternate-path"
            ),
        }

        def authoritative_fields(step: dict[str, object]) -> None:
            capsule = step["fixture_capsule"]
            assert isinstance(capsule, dict)
            capsule["contract_type"] = "task"
            capsule["inputs"] = list(AUTHORITATIVE_DAG_INPUTS)
            capsule["dependencies"] = [
                AUTHORITATIVE_DAG_NODES[
                    ("isolated-write-parallel-contract", 2)
                ][1]
            ]

        authoritative_fields(direct_task_step)
        authoritative_fields(repair_task_step)

        cases: list[tuple[str, dict[str, object], str]] = []

        def add_case(
            label: str,
            step: dict[str, object],
            *,
            expected: str = "task",
            kind: str = "direct",
            evidence: dict[str, object] | None = progress,
            preceding_dispatch: dict[str, object] | None = None,
            prefix_steps: list[dict[str, object]] | None = None,
        ) -> None:
            steps = copy.deepcopy(prefix_steps or [])
            if evidence is not None:
                steps.append(copy.deepcopy(evidence))
            if preceding_dispatch is not None:
                steps.append(copy.deepcopy(preceding_dispatch))
            steps.append(step)
            cases.append(
                (
                    label,
                    {
                        "id": f"budget-classification-{label}",
                        "kind": kind,
                        "steps": steps,
                    },
                    expected,
                )
            )

        add_case("direct-task-template", direct_task_step)
        add_case("repair-task-template", repair_task_step)

        def mutated_base() -> dict[str, object]:
            return copy.deepcopy(base_step)

        missing_inputs = mutated_base()
        missing_inputs["fixture_capsule"].pop("inputs")
        add_case("missing-inputs", missing_inputs)

        missing_input_item = mutated_base()
        missing_input_item["fixture_capsule"]["inputs"] = [
            AUTHORITATIVE_DAG_INPUTS[0]
        ]
        add_case("missing-input-item", missing_input_item)

        near_input = mutated_base()
        near_input["fixture_capsule"]["inputs"][0] += "."
        add_case("near-match-input", near_input)

        reversed_inputs = mutated_base()
        reversed_inputs["fixture_capsule"]["inputs"].reverse()
        add_case("reordered-inputs", reversed_inputs)

        extra_input = mutated_base()
        extra_input["fixture_capsule"]["inputs"].append(
            "Additional non-authoritative context."
        )
        add_case("extra-input", extra_input)

        missing_dependencies = mutated_base()
        missing_dependencies["fixture_capsule"].pop("dependencies")
        add_case("missing-dependencies", missing_dependencies)

        empty_dependencies = mutated_base()
        empty_dependencies["fixture_capsule"]["dependencies"] = []
        add_case("empty-dependencies", empty_dependencies)

        near_dependency = mutated_base()
        near_dependency["fixture_capsule"]["dependencies"][0] += "."
        add_case("near-match-dependency", near_dependency)

        multiple_dependencies = mutated_base()
        multiple_dependencies["fixture_capsule"]["dependencies"].append(
            "Another predecessor."
        )
        add_case("multiple-dependencies", multiple_dependencies)

        wrong_template_dependency = mutated_base()
        wrong_template_dependency["fixture_capsule"]["dependencies"] = [
            AUTHORITATIVE_DAG_NODES[
                ("isolated-write-parallel-contract", 20)
            ][1]
        ]
        add_case("wrong-template-dependency", wrong_template_dependency)

        missing_template = mutated_base()
        missing_template["fixture_capsule"].pop("template")
        add_case("missing-template", missing_template)

        near_template = mutated_base()
        near_template["fixture_capsule"]["template"] = "implementation-task-v2"
        add_case("near-match-template", near_template)

        missing_task_contract = mutated_base()
        missing_task_contract["fixture_capsule"].pop("contract_type")
        add_case("missing-task-contract", missing_task_contract)

        near_task_contract = mutated_base()
        near_task_contract["fixture_capsule"]["contract_type"] = "tasks"
        add_case("near-match-task-contract", near_task_contract)

        add_case("missing-evidence", mutated_base(), evidence=None)

        prepended_evidence = copy.deepcopy(progress)
        prepended_evidence["evidence"] = (
            "X"
            + AUTHORITATIVE_DAG_EVIDENCE_BY_CASE[
                "isolated-write-parallel-contract"
            ]
        )
        add_case(
            "near-match-evidence-prepend",
            mutated_base(),
            evidence=prepended_evidence,
        )

        appended_evidence = copy.deepcopy(progress)
        appended_evidence["evidence"] = (
            AUTHORITATIVE_DAG_EVIDENCE_BY_CASE[
                "isolated-write-parallel-contract"
            ]
            + "X"
        )
        add_case(
            "near-match-evidence-append",
            mutated_base(),
            evidence=appended_evidence,
        )

        add_case(
            "near-match-case-kind",
            mutated_base(),
            kind="direct-task",
        )
        add_case(
            "analysis-dispatch-present",
            mutated_base(),
            preceding_dispatch=analysis_step,
        )

        synthetic_dependencies = (
            (
                "synthetic-authority-node",
                "implementation-task",
                AUTHORITATIVE_DAG_NODES[
                    ("isolated-write-parallel-contract", 2)
                ][1],
                progress,
                3,
            ),
            (
                "synthetic-authority-predecessor",
                "implementation-task",
                AUTHORITATIVE_DAG_NODES[
                    ("shared-workspace-serial-write", 12)
                ][1],
                alternate_progress,
                5,
            ),
            (
                "synthetic-authority-integration",
                "integration-task",
                AUTHORITATIVE_DAG_NODES[
                    ("isolated-write-parallel-contract", 20)
                ][1],
                progress,
                8,
            ),
        )
        real_case_ids = {
            str(case["id"])
            for key in ("cases", "scheduling_cases", "utility_cases")
            for case in document[key]
        }
        synthetic_target_steps: dict[str, int] = {}
        for (
            label,
            template,
            dependency,
            evidence,
            filler_count,
        ) in synthetic_dependencies:
            synthetic_step = mutated_base()
            synthetic_step["fixture_capsule"]["template"] = template
            synthetic_step["fixture_capsule"]["dependencies"] = [dependency]
            if template == "integration-task":
                synthetic_step["mode"] = "integration"
            if label == "synthetic-authority-node":
                synthetic_step["primary_skill"] = "backend-change-builder"
                synthetic_step["professional_references"] = [
                    "references/checklist.md"
                ]
                synthetic_step["layer3_skills"] = []
                synthetic_step["layer3_references"] = []
                self.assertEqual(
                    "backend-change-builder",
                    synthetic_step["primary_skill"],
                )
                self.assertEqual(
                    ["references/checklist.md"],
                    synthetic_step["professional_references"],
                )
                self.assertEqual([], synthetic_step["layer3_skills"])
                self.assertEqual([], synthetic_step["layer3_references"])
                self.assertEqual("task-agent", synthetic_step["profile"])
                self.assertNotIn("utility_capsule", synthetic_step)
                self.assertEqual(
                    "task",
                    synthetic_step["fixture_capsule"]["contract_type"],
                )
                self.assertEqual(
                    AUTHORITATIVE_DAG_INPUTS,
                    synthetic_step["fixture_capsule"]["inputs"],
                )
                self.assertEqual(
                    "implementation-task",
                    synthetic_step["fixture_capsule"]["template"],
                )
                self.assertEqual(
                    [dependency],
                    synthetic_step["fixture_capsule"]["dependencies"],
                )
                self.assertEqual(
                    AUTHORITATIVE_DAG_EVIDENCE_BY_CASE[
                        "isolated-write-parallel-contract"
                    ],
                    evidence["evidence"],
                )
            prefix_steps = [
                {
                    "actor": "task-agent",
                    "action": "read",
                    "path": f"synthetic/input-{index}.txt",
                }
                for index in range(filler_count)
            ]
            add_case(
                label,
                synthetic_step,
                expected="analyzed_task",
                evidence=evidence,
                prefix_steps=prefix_steps,
            )
            synthetic_case_id = f"budget-classification-{label}"
            self.assertNotIn(synthetic_case_id, real_case_ids)
            synthetic_target_steps[synthetic_case_id] = filler_count + 1
        self.assertEqual(
            {
                "budget-classification-synthetic-authority-node": 4,
                "budget-classification-synthetic-authority-predecessor": 6,
                "budget-classification-synthetic-authority-integration": 9,
            },
            synthetic_target_steps,
        )

        add_case(
            "analyzed-case-unchanged",
            analyzed_task_step,
            expected="analyzed_task",
            kind="analyzed",
            evidence=None,
        )
        add_case(
            "utility-unchanged",
            utility_step,
            expected="utility",
            kind="utility",
            evidence=None,
        )

        fixture_cases = [
            ("utility" if expected == "utility" else "release", case)
            for _label, case, expected in cases
        ]
        with (
            mock.patch.object(
                EVAL,
                "_fixture_cases",
                return_value=fixture_cases,
            ),
            mock.patch.object(
                EVAL,
                "_dispatch_metadata_errors",
                return_value=[],
            ),
            mock.patch.object(
                EVAL,
                "trace_execution_level_migration_errors",
                return_value=[],
            ),
            mock.patch.object(
                EVAL,
                "_layer3_reference_registry_errors",
                return_value=[],
            ),
            mock.patch.object(
                EVAL,
                "validate_and_render_fixture_capsule",
                return_value="# Classification capsule",
            ),
            mock.patch.object(
                EVAL,
                "_load_lightweight_prerequisite",
                return_value=(
                    {str(cases[0][1]["id"])},
                    {"retained_semantic_equality": True},
                ),
            ),
        ):
            report = EVAL.evaluate()

        results = {
            str(case["id"]): case["measurements"]
            for case in report["cases"]
        }
        expected_coordinates = {
            (host, EVAL.RUNTIME_NAME)
            for host in EVAL.HOST_PROFILE_ROOTS
        }
        for label, case, expected in cases:
            case_id = str(case["id"])
            target_step = len(case["steps"]) - 1
            measurements = [
                measurement
                for measurement in results[case_id]
                if measurement["step"] == target_step
            ]
            with self.subTest(case=label, contract="measurement-count"):
                self.assertEqual(3, len(measurements))
                self.assertEqual(
                    expected_coordinates,
                    {
                        (
                            measurement["host"],
                            measurement["runtime"],
                        )
                        for measurement in measurements
                    },
                )
            for measurement in measurements:
                with self.subTest(
                    case=label,
                    host=measurement["host"],
                    runtime_name=measurement["runtime"],
                ):
                    self.assertEqual(expected, measurement["budget_class"])

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
                    / "engineering-control-plane/references/reference-records"
                    / primary
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
            return f"{owner}/{record['path']}"

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
            ).split("/", 1)[1]
            for profile in (EVAL.RUNTIME_NAME,)
        }

        rows = (
            ("recommended", "engineering-change-analysis", "test-strategy", "references/checklist.md", "compiled"),
            ("recommended", "engineering-change-analysis", "payment-trading-extension", payment_references["recommended"], "compiled"),
            ("recommended", "high-risk-design-review", "module-boundary-design", "references/benchmarks-and-enforcement.md", "compiled"),
            ("recommended", "security-privacy-gate", "web-security", "references/checklist.md", "compiled"),
            ("recommended", "security-privacy-gate", "ai-product-extension", "references/checklist.md", "compiled"),
            ("recommended", "backend-change-builder", "ai-product-extension", "references/checklist.md", "compiled"),
            ("recommended", "frontend-change-builder", "ai-product-extension", "references/checklist.md", "compiled"),
            ("recommended", "data-middleware-change-builder", "ai-product-extension", "references/checklist.md", "compiled"),
            ("recommended", "integration-change-builder", "ai-product-extension", "references/checklist.md", "compiled"),
            ("recommended", "installed-client-change-builder", "ai-product-extension", "references/checklist.md", "compiled"),
            ("recommended", "ai-code-review-refactor", "ai-product-extension", "references/checklist.md", "compiled"),
            ("recommended", "delivery-release-gate", "release-rollback", "references/benchmarks-and-patterns.md", "compiled"),
            ("recommended", "delivery-release-gate", "release-rollback", "references/evidence-patterns.md", "compiled"),
        )
        for profile, primary, owner, relative, delivery in rows:
            with self.subTest(profile=profile, owner=owner):
                logical_id = f"{owner}/{relative}"
                resolved = EVAL._layer3_reference_path(
                    profile,
                    primary,
                    logical_id,
                    manifests[profile],
                )
                compiled_path = (
                    EVAL.DIST_SKILLS
                    / profile
                    / primary
                    / "references"
                    / "layer3"
                    / owner
                    / relative
                )
                top_level_path = EVAL.DIST_SKILLS / profile / owner / relative
                expected = compiled_path if delivery == "compiled" else top_level_path
                alternate = top_level_path if delivery == "compiled" else compiled_path
                self.assertEqual(expected, resolved)
                self.assertTrue(resolved.is_file())
                self.assertFalse(alternate.exists())

        foundation_id = "transaction-consistency/references/evidence-patterns.md"
        recommended_nested = EVAL._layer3_reference_path(
            "recommended",
            "data-middleware-change-builder",
            foundation_id,
            manifests["recommended"],
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
        recommended_domain = EVAL._layer3_reference_path(
            "recommended",
            "data-middleware-change-builder",
            domain_ids["recommended"],
            manifests["recommended"],
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
                        parse_layer3_reference_id(logical_id)[0]
                        in foundation_names
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

    def test_layer3_reference_resolution_requires_exactly_one_delivery_path(self) -> None:
        logical_id = "owner/references/checklist.md"
        base = {
            "compiled_layer3_references": {"primary": []},
            "top_level_skills": [],
        }
        with self.assertRaisesRegex(ValueError, "exactly one compiled or top-level"):
            EVAL._layer3_reference_path(
                "test",
                "primary",
                logical_id,
                copy.deepcopy(base),
            )

        dual = copy.deepcopy(base)
        dual["compiled_layer3_references"]["primary"] = ["owner"]
        dual["top_level_skills"] = ["owner"]
        with self.assertRaisesRegex(ValueError, "exactly one compiled or top-level"):
            EVAL._layer3_reference_path("test", "primary", logical_id, dual)

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
                "direct_false_worst_excluded",
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
        self.assertGreater(inventory["path_excluded_composition_count"], 0)
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

    def test_global_dominance_frontier_is_complete_and_source_derived(self) -> None:
        composition = self._admissible_report()
        frontier = composition["dominance_frontier"]

        self.assertEqual(
            {
                "analysis": {
                    "candidate_count": 112_828,
                    "exact_render_signature_count": 46_158,
                    "over_target_candidate_count": 0,
                },
                "task": {
                    "candidate_count": 19_281,
                    "exact_render_signature_count": 19_281,
                    "over_target_candidate_count": 112,
                },
                "analyzed_task": {
                    "candidate_count": 66_150,
                    "exact_render_signature_count": 66_150,
                    "over_target_candidate_count": 0,
                },
                "review": {
                    "candidate_count": 38_007,
                    "exact_render_signature_count": 16_640,
                    "over_target_candidate_count": 0,
                },
            },
            {
                budget_class: {
                    key: row[key]
                    for key in (
                        "candidate_count",
                        "exact_render_signature_count",
                        "over_target_candidate_count",
                    )
                }
                for budget_class, row in frontier["budget_classes"].items()
            },
        )
        global_union = frontier["global_task_review_union"]
        self.assertEqual(
            {"professional": 5, "layer3": 28, "active_reference": 6},
            global_union["frontier_counts"],
        )
        self.assertEqual(
            {"professional": 11, "layer3": 40, "active_reference": 260},
            global_union["safe_complement_counts"],
        )
        self.assertEqual(
            [
                "change-documentation-gate",
                "installed-client-change-builder",
                "integration-change-builder",
                "repository-tooling-change-builder",
                "security-privacy-gate",
            ],
            global_union["frontier"]["professional"],
        )
        self.assertEqual(
            [
                "ai-product-extension",
                "android-platform-extension",
                "build-tool-professional-usage",
                "client-application-testing",
                "client-lifecycle-state-restoration",
                "configuration-runtime-policy",
                "consumer-impact-analysis",
                "contract-testing",
                "cross-platform-client-extension",
                "csharp-dotnet-professional-usage",
                "dependency-vulnerability-scanning",
                "design-pattern-selection",
                "documentation-generation",
                "failure-contract-design",
                "idempotency-retry-design",
                "ios-ipados-platform-extension",
                "kotlin-professional-usage",
                "linux-desktop-platform-extension",
                "macos-platform-extension",
                "minimal-correct-implementation",
                "offline-sync-conflict-resolution",
                "privacy-data-lifecycle",
                "state-management-design",
                "swift-professional-usage",
                "targeted-validation-selection",
                "threat-modeling",
                "web-security",
                "windows-platform-extension",
            ],
            global_union["frontier"]["layer3"],
        )
        self.assertEqual(
            [
                "ai-product-extension/references/checklist.md",
                "client-lifecycle-state-restoration/references/restoration-boundaries.md",
                "dependency-vulnerability-scanning/references/evidence-patterns.md",
                "documentation-generation/references/benchmarks-and-patterns.md",
                "kotlin-professional-usage/references/coroutine-flow-state-contracts.md",
                "kotlin-professional-usage/references/type-interop-and-dsl-contracts.md",
            ],
            global_union["frontier"]["active_reference"],
        )
        self.assertEqual(
            [
                "ai-code-review-refactor",
                "architecture-impact-reviewer",
                "data-api-contract-changer",
                "data-middleware-change-builder",
                "delivery-release-gate",
                "engineering-artifact-review",
                "high-risk-design-review",
                "logging-design-gate",
                "platform-infrastructure-change-builder",
                "quality-test-gate",
                "reliability-observability-gate",
            ],
            global_union["safe_complement"]["professional"],
        )
        expected_membership_sha256 = {
            "frontier_professional": "05ea3553f9f11039c7cc955109c3e8c2cde1287d54e019cf040fa94ce139d114",
            "frontier_layer3": "29532ec3aefd2dc81ba3e725e4814e5405fdfaac7ae337986e0dd18cbf4511a3",
            "frontier_active_reference": "7b755df04debe3ace3c012e6b23ec6a89308a95711a1b7a7480fc3b67d166b39",
            "safe_complement_professional": "08263e9035ab66f4b588c2baba8a88dcea7460dea6e3eae93c0e819f2bf99a92",
            "safe_complement_layer3": "4d7deb92ce7c91731298b01c7cad4717912b4beefe91bb7f97c955f5dd9cb209",
            "safe_complement_active_reference": "fa6031c51a27a2f80d92f099eeff34529c65529d6dc3f0a7ccb28cb64751d18e",
        }
        actual_membership_sha256 = {
            f"{placement}_{member_kind}": EVAL._sha256_text(
                EVAL._canonical_json_text(global_union[placement][member_kind])
            )
            for placement in ("frontier", "safe_complement")
            for member_kind in ("professional", "layer3", "active_reference")
        }
        self.assertEqual(expected_membership_sha256, actual_membership_sha256)
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
        direct = frontier["budget_classes"]["task"]
        review = frontier["budget_classes"]["review"]
        self.assertEqual(
            {"professional": 5, "layer3": 28, "active_reference": 6},
            direct["frontier_counts"],
        )
        self.assertEqual(
            {"professional": 0, "layer3": 0, "active_reference": 0},
            review["frontier_counts"],
        )
        for budget_class, row in (("task", direct), ("review", review)):
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

    def test_current_frontier_preserves_obligations_with_one_known_overflow(self) -> None:
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
            ),
        )
        self.assertEqual(
            "a4e5bbb9d94f00b18ab3a7dc8532bf671a6a69e2908fc5cccbaf7fdd92757f6e",
            receipt["receipt_sha256"],
        )

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
        self.assertEqual(
            "fixture:repair-and-rereview:step:22:canonical-capsule",
            capsule["path"],
        )
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
        self.assertEqual(
            "77007dd093f4b9cd5e46dd953ba7982c1709ba32392e33091323bd01c7cc9484",
            selected["receipt"]["receipt_sha256"],
        )

        evidence_references = [
            (record["owner_skill"], record["path"])
            for record in projection["reference_records"]
            if (record.get("context_admissibility") or {}).get("gap_class")
            == "repo-resolvable-fact"
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
        self.assertEqual(
            "ee2fbb10ab636724db615fb026229648289a1f821c2b78e23733f3f857d55900",
            selected["receipt"]["receipt_sha256"],
        )

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
        self.assertEqual(
            "9675e14cd6ed0e30fd85e02bf5ca9353d7e901d034632d15e1653ca976bc1056",
            selected["receipt"]["receipt_sha256"],
        )

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
                ("dispatch_capsule", capsule["path"]),
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
        self.assertEqual(
            "141c7fccec4e72d06d444554f3451465a7612a8128a176840bd80c51ed23b18a",
            selected["receipt"]["receipt_sha256"],
        )

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
                self.assertEqual(case["receipt"], selected["receipt"]["receipt_sha256"])
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
                        ("dispatch_capsule", case["capsule"]["path"]),
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
                self.assertEqual(case["receipt"], selected["receipt"]["receipt_sha256"])
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
                        ("dispatch_capsule", case["capsule"]["path"]),
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
        self.assertEqual(
            "0c9aa8b856780e9aecfa385003bc7f2b87167ed326e3863b570c79af4a7848a9",
            task_selected["receipt"]["receipt_sha256"],
        )
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
                ("dispatch_capsule", capsules["task"]["path"]),
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
        self.assertEqual(
            "ccdcc0383fe8a0956f5b801f66c9fb4173aa00336eed4ee10c252825ea2a3098",
            review_selected["receipt"]["receipt_sha256"],
        )
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
                ("dispatch_capsule", capsules["review"]["path"]),
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
        self.assertEqual(
            "23f0408560643c339c33bf05806fc6ab7e1c8929b892a2a2de28686f5b4fdd55",
            selected["receipt"]["receipt_sha256"],
        )
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
                ("dispatch_capsule", capsule["path"]),
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
        self.assertEqual(
            (
                "b6f4ecd27fed13f1d570970b4a316d3a0c7c6128add25328b983318eafbe4f5b",
                ["accepted-brief", "input-shape-change"],
                "implementation-risk",
                "professional-risk",
            ),
            (
                selected["receipt"]["receipt_sha256"],
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
                ("dispatch_capsule", capsule["path"]),
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
        self.assertEqual(
            (
                "ff438335ba459e33cfccf8dd2a9a3903ad3094ebef55562d5467d3e855e6d3b8",
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
                selected["receipt"]["receipt_sha256"],
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
        )
        self.assertEqual(
            ["cloud-platform-extension"],
            negative_receipt["selected_layer3"],
        )
        self.assertNotEqual(
            selected["receipt"]["receipt_sha256"],
            negative_receipt["receipt_sha256"],
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
                ("dispatch_capsule", capsule["path"]),
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
        self.assertEqual(
            (
                "561a404c9f71b49fc1c15e727f8fe21e426622ed9224df71d0d21056513da9b4",
                [
                    "explicit-test-data-decision",
                    "changed installed-client behavior needs lifecycle os integration installation device configuration or accessibility proof",
                    "analysis-action",
                ],
                "implementation-risk",
                "professional-risk",
            ),
            (
                selected["receipt"]["receipt_sha256"],
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
        )
        self.assertNotIn("client-application-testing", negative_receipt["selected_layer3"])
        self.assertNotEqual(
            selected["receipt"]["receipt_sha256"],
            negative_receipt["receipt_sha256"],
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
                ("dispatch_capsule", capsule["path"]),
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
        self.assertEqual(
            (
                "274ab034c0a7efd4d2986963b7774d8ac909c445b89f5c19e0e306a97fdfcdd4",
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
                selected["receipt"]["receipt_sha256"],
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
        )
        self.assertNotIn(
            "powershell-professional-usage",
            negative_receipt["selected_layer3"],
        )
        self.assertNotEqual(
            selected["receipt"]["receipt_sha256"],
            negative_receipt["receipt_sha256"],
        )

        for path, expected_sha256 in {
            "src/professional-skills/platform-infrastructure-change-builder/SKILL.md": "2543b9cc91b1efa0696905015b5b6a6d11126798e14c386ad95591b12c1ab1da",
            "src/professional-skills/platform-infrastructure-change-builder/references/iac-source-contracts.md": "a0265060cbbe58e1ac9771511848498335614965a9110aa2af55298773168570",
            "src/foundation/capabilities/powershell-professional-usage/references/pipeline-error-and-native-contracts.md": "ab30d62d5e947340effe9918dd49546f2e69c47806b049c4f125673260833c8e",
            "src/foundation/capabilities/powershell-professional-usage/references/remoting-provider-and-administration-contracts.md": "97ce7438c774d56a64d46fd241c3d6876b97929b8294f43897818185ba812cd4",
        }.items():
            with self.subTest(source_hash=path):
                self.assertEqual(
                    expected_sha256,
                    hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
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
                ("dispatch_capsule", capsule["path"]),
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
        self.assertEqual(
            (
                "434c91b6b2caf2b3b78ff6ffbfd86491a1d834746060092e516142467fcb6953",
                expected_signals,
                "implementation-risk",
                "professional-risk",
            ),
            (
                selected["receipt"]["receipt_sha256"],
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
        )
        self.assertNotIn(
            "infrastructure-as-code-safety",
            negative_receipt["selected_layer3"],
        )
        self.assertNotEqual(
            selected["receipt"]["receipt_sha256"],
            negative_receipt["receipt_sha256"],
        )

        protected_sources = {
            "src/professional-skills/platform-infrastructure-change-builder/SKILL.md": "2543b9cc91b1efa0696905015b5b6a6d11126798e14c386ad95591b12c1ab1da",
            "src/domain-extensions/cloud-platform-extension/SKILL.md": "6c300ff1c468f83c7b75c54997c67539710e6f8e236fc655d4ecda5e806a4224",
            "src/foundation/capabilities/configuration-runtime-policy/SKILL.md": "a0c6c4b122e76426256bc5deac35b741b32a406255992ac4c958ff10cfb2f9c6",
            "src/foundation/capabilities/infrastructure-as-code-safety/SKILL.md": "30c8a48b94f411059bb8e17e1670d1b5ca79db1c27b06394d5818f14de10c21c",
            "src/foundation/capabilities/infrastructure-as-code-safety/references/identity-destruction-and-recovery-contracts.md": "8cf0a2d5b85a83cd517a937059b28b243c2718e7da90dad405fd33a474e44b1f",
            "src/foundation/capabilities/infrastructure-as-code-safety/references/state-plan-and-drift-contracts.md": "d1d0bbf5306aaa75e25a9ed6a08d0d7c5b0066b75dd091cb276b63da58892bc6",
        }
        for path, expected_sha256 in protected_sources.items():
            self.assertEqual(
                expected_sha256,
                hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
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
                ("dispatch_capsule", capsule["path"]),
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
        self.assertEqual(
            (
                "6267555050601288125c263945346b3abdd3f22a54cb2a6337e3de44053e1298",
                expected_signals,
                "implementation-risk",
                "professional-risk",
            ),
            (
                selected["receipt"]["receipt_sha256"],
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
            projection, evidence_signals=expected_signals[:-1]
        )
        self.assertNotIn("distributed-workflow-consistency", negative_receipt["selected_layer3"])
        self.assertNotEqual(selected["receipt"]["receipt_sha256"], negative_receipt["receipt_sha256"])

        protected = {
            "src/professional-skills/data-middleware-change-builder/SKILL.md": "51af820aededb532f57198975c6290b76e6c65b20e9c0ae2817171a9980c5db1",
            "src/foundation/capabilities/data-migration-design/SKILL.md": "1c2d3921cfe7f848e03f32fb0031f49b0d5ff55d8e0f65a4bee4c6549cdc1649",
            "src/foundation/capabilities/transaction-consistency/SKILL.md": "076dff13a9468d13713ec106f5a96586f44635855f9600998209d197a8fb5308",
            "src/foundation/capabilities/distributed-workflow-consistency/SKILL.md": "df3a7d24a62d3aabc74405abeb7ce98376da7a049c3ec8b36c43c25694a98b2e",
            "src/foundation/capabilities/data-migration-design/references/evidence-patterns.md": "b868feeb34a6b3e3399403c1b96608a6baa46f8768945768c02ff1a517f3ea65",
        }
        for path, expected_sha256 in protected.items():
            self.assertEqual(expected_sha256, hashlib.sha256((ROOT / path).read_bytes()).hexdigest())

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
                ("dispatch_capsule", capsule["path"]),
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
        self.assertEqual(
            (
                "0a93ab092e22e6ce4b18a629db71817e23222ed5d89397c5be7434e10a85047a",
                expected_signals,
                "implementation-risk",
                "professional-risk",
            ),
            (
                selected["receipt"]["receipt_sha256"],
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
            projection, evidence_signals=expected_signals[1:]
        )
        self.assertNotIn(
            "iot-embedded-extension", negative_receipt["selected_layer3"]
        )
        self.assertNotEqual(
            selected["receipt"]["receipt_sha256"],
            negative_receipt["receipt_sha256"],
        )

        protected = {
            "src/professional-skills/delivery-release-gate/SKILL.md": "aaf5c2ea8078a3c794725303f2ce7c3372dd96569a4a0d5dc88bc82024fa1fda",
            "src/domain-extensions/iot-embedded-extension/SKILL.md": "6d7eca5af1dac2721ccfa51a33aa21deba46a818593e8186cb6eadd2350a9269",
            "src/foundation/capabilities/release-rollback/SKILL.md": "05bc0fa788fd635c9ce8948f64c7eb25846a083c1b6d33876ba95f4464ac0830",
            "src/foundation/capabilities/version-compatibility/SKILL.md": "8579ded9475e7b7faf3a740d4526e770be0270113be18090cc9496f3d5190f9f",
            "src/domain-extensions/iot-embedded-extension/references/checklist.md": "951aef0ee02152fee0ff4478463b9bd80b96034a0a37c886dd19496ecbe6f64f",
        }
        for path, expected_sha256 in protected.items():
            self.assertEqual(
                expected_sha256,
                hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
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
                ("dispatch_capsule", capsule["path"]),
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
        self.assertEqual(
            (
                "336dfef51f64a686fc616f4fc48cac5451ebd55fe61dee5e402d4e98ca5a90e4",
                expected_signals,
                "implementation-risk",
                "professional-risk",
            ),
            (
                selected["receipt"]["receipt_sha256"],
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
            projection, evidence_signals=expected_signals[:-1]
        )
        self.assertEqual(
            ["cloud-platform-extension"], negative_receipt["selected_layer3"]
        )
        self.assertNotEqual(
            selected["receipt"]["receipt_sha256"],
            negative_receipt["receipt_sha256"],
        )

        protected = {
            "src/professional-skills/security-privacy-gate/SKILL.md": "f11d7bdde385a27584a4b22e07cd389adc4c59d8933597433238c4ecc5ba7ae5",
            "src/domain-extensions/cloud-platform-extension/SKILL.md": "6c300ff1c468f83c7b75c54997c67539710e6f8e236fc655d4ecda5e806a4224",
            "src/foundation/capabilities/threat-modeling/SKILL.md": "90d1b45cc6cab690eb2861c3ec896cc742466223468a41aafd8b84674db7271d",
            "src/foundation/capabilities/web-security/SKILL.md": "4d9a6d9e61de16b63b62b4c5e19ff8857cc96f5661b32f4540aaa7f07960a191",
            "src/foundation/capabilities/web-security/references/benchmarks-and-patterns.md": "ba0d3b7172e4fce659dfce92653dfcbd628295d4714ab0b6b81a38e6bd2ab763",
        }
        for path, expected_sha256 in protected.items():
            self.assertEqual(
                expected_sha256, hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
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
                ("dispatch_capsule", capsule["path"]),
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
