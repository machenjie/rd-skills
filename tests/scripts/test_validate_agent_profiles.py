from __future__ import annotations

import copy
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build as BUILDER
from validation_utils import count_o200k_base_tokens


def _load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_agent_profiles_test_target",
        SCRIPTS / "validate-agent-profiles.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load validate-agent-profiles.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALIDATOR = _load_validator()
INVALID_JSON_OBJECT_PAYLOADS = (
    ("null", "null", "JSON top level must be an object"),
    ("array", "[]", "JSON top level must be an object"),
    ("string", '"value"', "JSON top level must be an object"),
    ("boolean", "true", "JSON top level must be an object"),
    ("number", "42", "JSON top level must be an object"),
    ("bad-json", "{not-json", "invalid JSON"),
)


class AgentProfileReadabilityTests(unittest.TestCase):
    def _mutated_source_result(
        self,
        role: str,
        old: str,
        new: str,
    ) -> tuple[int, str]:
        source = json.loads(VALIDATOR.SOURCE.read_text(encoding="utf-8"))
        profile = next(item for item in source["profiles"] if item["name"] == role)
        self.assertIn(old, profile["instructions"])
        profile["instructions"] = profile["instructions"].replace(old, new, 1)
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "role-agents.json"
            path.write_text(json.dumps(source), encoding="utf-8")
            output = io.StringIO()
            with (
                mock.patch.object(VALIDATOR, "SOURCE", path),
                redirect_stdout(output),
                redirect_stderr(output),
            ):
                result = VALIDATOR.main(["--source-only"])
        return result, output.getvalue()

    def _mutated_built_result(
        self,
        platform: str,
        role: str,
        old: str,
        new: str,
    ) -> tuple[int, str]:
        source = json.loads(VALIDATOR.SOURCE.read_text(encoding="utf-8"))
        enforcement = json.loads(
            VALIDATOR.ENFORCEMENT_SOURCE.read_text(encoding="utf-8")
        )
        renderer = {
            "codex": BUILDER._render_codex_profile,
            "claude": BUILDER._render_claude_profile,
            "copilot": BUILDER._render_copilot_profile,
        }[platform]
        extension = {
            "codex": ".toml",
            "claude": ".md",
            "copilot": ".agent.md",
        }[platform]
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "agents"
            root.mkdir()
            for profile in source["profiles"]:
                rendered = renderer(profile, enforcement)
                if profile["name"] == role:
                    self.assertEqual(1, rendered.count(old))
                    rendered = rendered.replace(old, new, 1)
                (root / f"{profile['name']}{extension}").write_text(
                    rendered,
                    encoding="utf-8",
                )
            output = io.StringIO()
            with (
                mock.patch.object(
                    VALIDATOR,
                    "OUTPUTS",
                    ((platform, root, extension),),
                ),
                mock.patch.object(VALIDATOR, "BUILT_MANIFESTS", ()),
                redirect_stdout(output),
                redirect_stderr(output),
            ):
                result = VALIDATOR.main([])
        return result, output.getvalue()

    def _mutated_enforcement_result(self, mutate) -> tuple[int, str]:
        enforcement = json.loads(
            VALIDATOR.ENFORCEMENT_SOURCE.read_text(encoding="utf-8")
        )
        mutate(enforcement)
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "host-enforcement.json"
            path.write_text(json.dumps(enforcement), encoding="utf-8")
            output = io.StringIO()
            with (
                mock.patch.object(VALIDATOR, "ENFORCEMENT_SOURCE", path),
                redirect_stdout(output),
                redirect_stderr(output),
            ):
                result = VALIDATOR.main(["--source-only"])
        return result, output.getvalue()

    def test_source_descriptions_pass_readability_gate(self) -> None:
        source = json.loads(VALIDATOR.SOURCE.read_text(encoding="utf-8"))
        errors: list[str] = []
        for profile in source["profiles"]:
            VALIDATOR._validate_profile_description(
                profile,
                profile["name"],
                errors,
            )
        self.assertEqual([], errors)

    def test_main_wrapper_budget_and_obligations_are_exact(self) -> None:
        source = json.loads(VALIDATOR.SOURCE.read_text(encoding="utf-8"))
        main = next(
            item for item in source["profiles"]
            if item["name"] == "main-control-agent"
        )
        expected = (
            "- Prompt authoritative.\n"
            "- Load engineering-control-plane only.\n"
            "- Never reload references/main-control-agent.md.\n"
            "- Dispatch only/no target-code access.\n"
            "- No worker: business acceptance/placement, Brief/DAG authoring, implementation review.\n"
            "- Capability facts authoritative; host/tool/command identifiers absent/unrecognized=unsupported.\n"
            "- Forward reviewer-accessible exact evidence."
        )

        self.assertEqual(expected, main["instructions"])
        self.assertEqual(70, count_o200k_base_tokens(main["instructions"]))

    def test_review_evidence_capabilities_are_four_independent_dimensions(self) -> None:
        enforcement = json.loads(
            VALIDATOR.ENFORCEMENT_SOURCE.read_text(encoding="utf-8")
        )
        expected = {
            "codex": {
                "native-change-read": "supported",
                "change-evidence-export": "supported",
                "supplied-change-delivery": "unsupported",
                "reviewer-change-consume": "supported",
            },
            "claude": {
                "native-change-read": "unsupported",
                "change-evidence-export": "supported",
                "supplied-change-delivery": "supported",
                "reviewer-change-consume": "supported",
            },
            "copilot": {
                "native-change-read": "unsupported",
                "change-evidence-export": "supported",
                "supplied-change-delivery": "supported",
                "reviewer-change-consume": "supported",
            },
        }
        for host, expected_dimensions in expected.items():
            with self.subTest(host=host):
                actual = VALIDATOR._normalized_decision_capabilities(
                    enforcement["hosts"][host]
                )
                self.assertEqual(
                    expected_dimensions,
                    {field: actual.get(field) for field in expected_dimensions},
                )

        no_task_export = copy.deepcopy(enforcement["hosts"]["codex"])
        no_task_export["roles"]["task-agent"]["rendered_tools"] = ["read", "edit"]
        capabilities = VALIDATOR._normalized_decision_capabilities(no_task_export)
        self.assertEqual("supported", capabilities["native-change-read"])
        self.assertEqual("unsupported", capabilities["change-evidence-export"])
        self.assertEqual("unsupported", capabilities["supplied-change-delivery"])
        self.assertEqual("supported", capabilities["reviewer-change-consume"])

        no_reviewer_consumer = copy.deepcopy(enforcement["hosts"]["copilot"])
        no_reviewer_consumer["roles"]["review-agent"]["rendered_tools"] = []
        capabilities = VALIDATOR._normalized_decision_capabilities(
            no_reviewer_consumer
        )
        self.assertEqual("unsupported", capabilities["native-change-read"])
        self.assertEqual("supported", capabilities["change-evidence-export"])
        self.assertEqual("supported", capabilities["supplied-change-delivery"])
        self.assertEqual("unsupported", capabilities["reviewer-change-consume"])

    def test_profile_rule_limits_are_core_driven_and_enforced(self) -> None:
        limits = VALIDATOR.PROFILE_CONTRACT_MODEL["instruction_rule_count"]
        source = json.loads(VALIDATOR.SOURCE.read_text(encoding="utf-8"))
        profiles = {profile["name"]: profile for profile in source["profiles"]}
        task_rules = profiles["task-agent"]["instructions"].splitlines()
        for role, profile in profiles.items():
            maximum = limits["maximum_by_role"].get(role, limits["maximum"])
            self.assertLessEqual(len(profile["instructions"].splitlines()), maximum)
        # Role ceilings bound resident rule scale; they do not license compound
        # bullets, which remain subject to the one-decision readability detector.
        for role in ("task-agent", "review-agent"):
            errors: list[str] = []
            findings = VALIDATOR.validate_ai_readability(
                profiles[role]["instructions"],
                f"{role}#instructions",
                errors,
            )
            self.assertEqual([], errors)
            self.assertFalse(
                any(finding["kind"] == "bullet-decisions" for finding in findings)
            )

        last_rule = task_rules[-1]
        task_maximum = limits["maximum_by_role"].get(
            "task-agent", limits["maximum"]
        )
        overflow = "\n".join(
            f"- Preserve unrelated extra instruction {index}."
            for index in range(task_maximum - len(task_rules) + 1)
        )
        result, output = self._mutated_source_result(
            "task-agent",
            last_rule,
            f"{last_rule}\n{overflow}",
        )
        self.assertEqual(1, result)
        self.assertIn(
            f"instructions must contain {limits['minimum']}-{task_maximum} "
            "newline bullet rules",
            output,
        )

    def test_overlong_description_is_rejected(self) -> None:
        profile = {"description": " ".join(
            [f"word{index}" for index in range(41)]
        ) + "."}
        errors: list[str] = []
        VALIDATOR._validate_profile_description(
            profile,
            "main-control-agent",
            errors,
        )
        self.assertEqual(1, len(errors))
        self.assertIn("#description", errors[0])
        self.assertIn("hard maximum is 40", errors[0])

    def test_required_terms_must_share_one_instruction_bullet(self) -> None:
        errors: list[str] = []
        VALIDATOR._validate_instruction_rule_groups(
            role_name="analysis-agent",
            contract_label="synthetic boundary",
            groups=[{"rule_id": "same-bullet", "required_terms": ["alpha", "beta"]}],
            rules=["- alpha", "- beta"],
            errors=errors,
        )
        self.assertEqual(1, len(errors))
        self.assertIn("exactly one instruction bullet", errors[0])

    def test_every_normal_task_agent_receives_universal_implementation_discipline(
        self,
    ) -> None:
        core = json.loads(
            (ROOT / "src/control-model/core-contracts.json").read_text(
                encoding="utf-8"
            )
        )
        contract = core.get("implementation_discipline_contract")
        self.assertIsInstance(contract, dict)
        self.assertEqual(2, contract["schema_version"])
        self.assertEqual("every normal implementation task-agent", contract["applies_to"])
        projection = contract["profile_projection"]
        self.assertLessEqual(
            count_o200k_base_tokens(
                "\n".join(rule["exact_rule"] for rule in projection)
            ),
            330,
        )
        self.assertEqual(
            [
                "inspect-before-edit",
                "inspection-stop-conditions",
                "observable-acceptance",
                "verified-bugfix-cause",
                "owner-first-placement",
                "placement-stop-conditions",
                "no-test-only-public-api",
                "smallest-complete-change",
                "adaptive-method-selection",
                "test-first-required",
                "red-proof-classification",
                "validation-integrity",
                "test-after-boundary",
                "existing-proof-only-boundary",
                "non-test-validation-boundary",
                "material-edit-staleness",
                "final-edit-rerun",
                "validation-outcome-reporting",
                "changed-behavior-proof",
            ],
            [rule["rule_id"] for rule in projection],
        )
        self.assertEqual(
            [
                "inspect-before-edit",
                "observable-acceptance",
                "verified-bugfix-cause",
                "owner-first-placement",
                "smallest-complete-change",
                "adaptive-testing",
                "universal-validation",
            ],
            [group["guard_group_id"] for group in contract["guard_groups"]],
        )
        self.assertIn(
            contract["profile_capability_id"],
            core["profile_contract"]["role_capabilities"]["task-agent"][
                "required_capability_ids"
            ],
        )

        source = json.loads(VALIDATOR.SOURCE.read_text(encoding="utf-8"))
        task_profile = next(
            profile for profile in source["profiles"] if profile["name"] == "task-agent"
        )
        self.assertLessEqual(
            count_o200k_base_tokens(task_profile["instructions"]),
            854,
        )
        source_rules = task_profile["instructions"].splitlines()
        for rule in projection:
            with self.subTest(rule=rule["rule_id"]):
                self.assertEqual(1, source_rules.count(rule["exact_rule"]))

        first_rule = projection[0]["exact_rule"]
        for platform in ("codex", "claude", "copilot"):
            with self.subTest(platform=platform):
                result, output = self._mutated_built_result(
                    platform,
                    "task-agent",
                    first_rule,
                    first_rule,
                )
                self.assertEqual(0, result, output)

    def test_ordinary_direct_task_without_layer3_receives_resident_validation_rules(
        self,
    ) -> None:
        fixture = json.loads(
            (
                ROOT / "evals/agent-light-trajectories/cases.yaml"
            ).read_text(encoding="utf-8")
        )
        direct_case = next(
            case for case in fixture["cases"] if case["id"] == "single-file-bug-fix"
        )
        self.assertEqual("direct", direct_case["kind"])
        dispatch = next(
            step
            for step in direct_case["steps"]
            if step.get("action") == "dispatch"
            and step.get("profile") == "task-agent"
        )
        self.assertEqual([], dispatch["layer3_skills"])
        self.assertEqual([], dispatch["layer3_references"])

        source = json.loads(VALIDATOR.SOURCE.read_text(encoding="utf-8"))
        enforcement = json.loads(
            VALIDATOR.ENFORCEMENT_SOURCE.read_text(encoding="utf-8")
        )
        task_profile = next(
            profile for profile in source["profiles"] if profile["name"] == "task-agent"
        )
        resident_ids = {
            "adaptive-method-selection",
            "test-first-required",
            "red-proof-classification",
            "validation-integrity",
            "test-after-boundary",
            "existing-proof-only-boundary",
            "non-test-validation-boundary",
            "material-edit-staleness",
            "final-edit-rerun",
            "validation-outcome-reporting",
            "changed-behavior-proof",
        }
        resident_rules = [
            rule["exact_rule"]
            for rule in VALIDATOR.IMPLEMENTATION_DISCIPLINE_MODEL[
                "profile_projection"
            ]
            if rule["rule_id"] in resident_ids
        ]
        self.assertEqual(11, len(resident_rules))
        for renderer in (
            BUILDER._render_codex_profile,
            BUILDER._render_claude_profile,
            BUILDER._render_copilot_profile,
        ):
            rendered = renderer(task_profile, enforcement)
            for rule in resident_rules:
                self.assertEqual(1, rendered.count(rule))

    def test_universal_implementation_discipline_rejects_projection_drift(
        self,
    ) -> None:
        projection = VALIDATOR.IMPLEMENTATION_DISCIPLINE_MODEL[
            "profile_projection"
        ]
        for rule in projection:
            with self.subTest(surface="source", rule=rule["rule_id"]):
                result, output = self._mutated_source_result(
                    "task-agent",
                    rule["exact_rule"],
                    "- This universal implementation guard is missing.",
                )
                self.assertEqual(1, result)
                self.assertIn("exact canonical bullet", output)

        first_rule = projection[0]
        for platform in ("codex", "claude", "copilot"):
            with self.subTest(surface=platform, rule=first_rule["rule_id"]):
                result, output = self._mutated_built_result(
                    platform,
                    "task-agent",
                    first_rule["exact_rule"],
                    "- This universal implementation guard is missing.",
                )
                self.assertEqual(1, result)
                self.assertIn("exact canonical bullet", output)

    def test_resident_validation_rules_reject_semantic_drift(self) -> None:
        projection = {
            rule["rule_id"]: rule["exact_rule"]
            for rule in VALIDATOR.IMPLEMENTATION_DISCIPLINE_MODEL[
                "profile_projection"
            ]
        }
        mutations = {
            "red-proof-classification": (
                "absent target behavior, never environment/fixture/import/syntax/unrelated failure",
                "environment failure",
            ),
            "validation-integrity": ("Preserve", "Weaken"),
            "final-edit-rerun": ("Rerun", "Skip"),
            "changed-behavior-proof": ("alone never prove", "alone can prove"),
        }
        for rule_id, replacement in mutations.items():
            with self.subTest(rule=rule_id):
                exact_rule = projection[rule_id]
                result, output = self._mutated_source_result(
                    "task-agent",
                    exact_rule,
                    exact_rule.replace(*replacement, 1),
                )
                self.assertEqual(1, result)
                self.assertIn("exact canonical bullet", output)

    def test_safety_critical_rules_match_exact_canonical_bullets(self) -> None:
        source = json.loads(VALIDATOR.SOURCE.read_text(encoding="utf-8"))
        profiles = {item["name"]: item for item in source["profiles"]}
        bindings = (
            ("task-agent", "task-normal-mode", "bounded-validation-retry"),
            ("task-agent", "task-normal-mode", "bounded-validation-stop"),
            ("review-agent", "review-target-modes", "implementation-review"),
        )
        for role, capability_id, rule_id in bindings:
            with self.subTest(role=role, rule=rule_id):
                rule = next(
                    item
                    for item in VALIDATOR.PROFILE_CONTRACT_MODEL["capability_terms"][
                        capability_id
                    ]
                    if item["rule_id"] == rule_id
                )
                self.assertEqual(
                    1,
                    profiles[role]["instructions"].splitlines().count(
                        rule["exact_rule"]
                    ),
                )

    def test_safety_critical_exact_rules_reject_semantic_drift(self) -> None:
        bindings = (
            (
                "task-agent",
                "task-normal-mode",
                "bounded-validation-retry",
                "An unchanged retry is allowed.",
                ("After 2 same-path failures", "After 3 same-path failures"),
            ),
            (
                "task-agent",
                "task-normal-mode",
                "bounded-validation-stop",
                "Rerouting is allowed.",
                ("never reroute", "reroute"),
            ),
            (
                "review-agent",
                "review-target-modes",
                "implementation-review",
                "A summary may replace the evidence.",
                ("delivered current", "unavailable"),
            ),
        )
        for role, capability_id, rule_id, contradiction, wrong_replacement in bindings:
            exact_rule = next(
                item["exact_rule"]
                for item in VALIDATOR.PROFILE_CONTRACT_MODEL["capability_terms"][
                    capability_id
                ]
                if item["rule_id"] == rule_id
            )
            mutations = {
                "missing": "- This safety-critical rule is missing.",
                "extra-contradiction": f"{exact_rule} {contradiction}",
                "wrong-semantics": exact_rule.replace(*wrong_replacement, 1),
                "appended-text": f"{exact_rule} Additional text.",
            }
            for mutation_kind, mutation in mutations.items():
                with self.subTest(
                    role=role,
                    rule=rule_id,
                    mutation=mutation_kind,
                ):
                    result, output = self._mutated_source_result(
                        role,
                        exact_rule,
                        mutation,
                    )
                    self.assertEqual(1, result)
                    self.assertIn("exact canonical bullet", output)

    def test_decoded_built_instructions_reject_exact_rule_drift(self) -> None:
        bindings = (
            (
                "task-agent",
                "task-normal-mode",
                "bounded-validation-retry",
                "contradiction",
                0,
                lambda rule: f"{rule} A third unchanged retry is allowed.",
            ),
            (
                "task-agent",
                "task-normal-mode",
                "bounded-validation-stop",
                "contradiction",
                0,
                lambda rule: f"{rule} Rerouting is allowed.",
            ),
            (
                "review-agent",
                "review-target-modes",
                "implementation-review",
                "extra",
                2,
                lambda rule: f"{rule}\n{rule}",
            ),
            (
                "review-agent",
                "review-target-modes",
                "implementation-review",
                "contradiction",
                0,
                lambda rule: f"{rule} Re-review may be skipped after repair.",
            ),
        )
        for (
            role,
            capability_id,
            rule_id,
            mutation_kind,
            expected_exact_count,
            mutate,
        ) in bindings:
            exact_rule = next(
                item["exact_rule"]
                for item in VALIDATOR.PROFILE_CONTRACT_MODEL["capability_terms"][
                    capability_id
                ]
                if item["rule_id"] == rule_id
            )
            for platform in ("codex", "claude", "copilot"):
                with self.subTest(
                    platform=platform,
                    role=role,
                    mutation=mutation_kind,
                ):
                    result, output = self._mutated_built_result(
                        platform,
                        role,
                        exact_rule,
                        mutate(exact_rule),
                    )
                    self.assertEqual(1, result)
                    self.assertIn("exact canonical bullet", output)
                    self.assertIn(f"found {expected_exact_count}", output)

    def test_decoded_built_instructions_accept_current_profiles(self) -> None:
        exact_rule = next(
            item["exact_rule"]
            for item in VALIDATOR.IMPLEMENTATION_DISCIPLINE_MODEL[
                "profile_projection"
            ]
            if item["rule_id"] == "final-edit-rerun"
        )
        for platform in ("codex", "claude", "copilot"):
            with self.subTest(platform=platform):
                result, output = self._mutated_built_result(
                    platform,
                    "task-agent",
                    exact_rule,
                    exact_rule,
                )
                self.assertEqual(0, result, output)

    def test_built_profiles_reject_crlf_raw_bytes(self) -> None:
        source = json.loads(VALIDATOR.SOURCE.read_text(encoding="utf-8"))
        enforcement = json.loads(
            VALIDATOR.ENFORCEMENT_SOURCE.read_text(encoding="utf-8")
        )
        renderers = {
            "codex": BUILDER._render_codex_profile,
            "claude": BUILDER._render_claude_profile,
            "copilot": BUILDER._render_copilot_profile,
        }
        extensions = {
            "codex": ".toml",
            "claude": ".md",
            "copilot": ".agent.md",
        }
        for platform, renderer in renderers.items():
            with self.subTest(platform=platform), tempfile.TemporaryDirectory() as raw:
                root = Path(raw) / "agents"
                root.mkdir()
                extension = extensions[platform]
                for profile in source["profiles"]:
                    rendered = renderer(profile, enforcement)
                    (root / f"{profile['name']}{extension}").write_bytes(
                        rendered.replace("\n", "\r\n").encode("utf-8")
                    )
                output = io.StringIO()
                with (
                    mock.patch.object(
                        VALIDATOR,
                        "OUTPUTS",
                        ((platform, root, extension),),
                    ),
                    mock.patch.object(VALIDATOR, "BUILT_MANIFESTS", ()),
                    redirect_stdout(output),
                    redirect_stderr(output),
                ):
                    result = VALIDATOR.main([])
                rendered_output = output.getvalue()
                self.assertEqual(1, result, rendered_output)
                self.assertIn("must use canonical LF bytes", rendered_output)

    def test_decoded_built_surface_rejects_instruction_after_rule_block(
        self,
    ) -> None:
        boundary = "\n\nDeclared tool boundary:"
        injected = (
            "\n\nValidation may be skipped after a material edit."
            "\n\nDeclared tool boundary:"
        )
        for platform in ("codex", "claude", "copilot"):
            with self.subTest(platform=platform):
                result, output = self._mutated_built_result(
                    platform,
                    "task-agent",
                    boundary,
                    injected,
                )
                self.assertEqual(1, result)
                self.assertIn(
                    "decoded instruction surface must equal the canonical Profile "
                    "rule block",
                    output,
                )

    def test_profile_source_json_failures_are_controlled(self) -> None:
        for kind, payload, expected in INVALID_JSON_OBJECT_PAYLOADS:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as raw:
                source = Path(raw) / "role-agents.json"
                source.write_text(payload, encoding="utf-8")
                output = io.StringIO()
                with (
                    mock.patch.object(VALIDATOR, "SOURCE", source),
                    redirect_stdout(output),
                    redirect_stderr(output),
                ):
                    result = VALIDATOR.main(["--source-only"])
                rendered = output.getvalue()
                self.assertEqual(1, result)
                self.assertIn("validate-agent-profiles: ERROR:", rendered)
                self.assertIn(expected, rendered)

    def test_host_enforcement_json_failures_are_controlled(self) -> None:
        for kind, payload, expected in INVALID_JSON_OBJECT_PAYLOADS:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as raw:
                enforcement = Path(raw) / "host-enforcement.json"
                enforcement.write_text(payload, encoding="utf-8")
                output = io.StringIO()
                with (
                    mock.patch.object(
                        VALIDATOR,
                        "ENFORCEMENT_SOURCE",
                        enforcement,
                    ),
                    redirect_stdout(output),
                    redirect_stderr(output),
                ):
                    result = VALIDATOR.main(["--source-only"])
                rendered = output.getvalue()
                self.assertEqual(1, result)
                self.assertIn("validate-agent-profiles: ERROR:", rendered)
                self.assertIn(expected, rendered)

    def test_build_manifest_json_failures_are_controlled(self) -> None:
        for kind, payload, expected in INVALID_JSON_OBJECT_PAYLOADS:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as raw:
                manifest = Path(raw) / ".changeforge-build-manifest.json"
                manifest.write_text(payload, encoding="utf-8")
                output = io.StringIO()
                with (
                    mock.patch.object(VALIDATOR, "OUTPUTS", ()),
                    mock.patch.object(
                        VALIDATOR,
                        "BUILT_MANIFESTS",
                        (manifest,),
                    ),
                    redirect_stdout(output),
                    redirect_stderr(output),
                ):
                    result = VALIDATOR.main([])
                rendered = output.getvalue()
                self.assertEqual(1, result)
                self.assertIn("validate-agent-profiles: ERROR:", rendered)
                self.assertIn(expected, rendered)

    def test_analysis_handoff_status_is_owned_by_engineering_brief(self) -> None:
        profile = next(
            item
            for item in json.loads(VALIDATOR.SOURCE.read_text(encoding="utf-8"))["profiles"]
            if item["name"] == "analysis-agent"
        )["instructions"]
        brief = (
            ROOT
            / "src/control-skills/engineering-control-plane/references/engineering-brief-template.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Professional/mode contract owns", profile)
        self.assertIn("in_progress / blocked / partial / completed", brief)

    def test_analysis_assignment_status_is_owned_by_task_template(self) -> None:
        brief = (
            ROOT
            / "src/control-skills/engineering-control-plane/references/engineering-brief-template.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Status: in_progress", brief)
        self.assertIn("Task Contract v2", brief)

    def test_main_profile_rejects_prompt_owned_contract_copies(self) -> None:
        anchor = (
            "Capability facts authoritative; host/tool/command identifiers "
            "absent/unrecognized=unsupported."
        )
        copied_rules = (
            "Task Contract v2 starts assignments.",
            "Use a visible Evidence Ledger.",
            "completed is terminal.",
        )
        for copied in copied_rules:
            with self.subTest(copied=copied):
                result, output = self._mutated_source_result(
                    "main-control-agent",
                    anchor,
                    anchor + "\n- " + copied,
                )
                self.assertEqual(1, result)
                self.assertIn("must not be copied into Profile instructions", output)

    def test_review_agent_requires_exact_independent_review_claims(self) -> None:
        proof = VALIDATOR.EVIDENCE_LEDGER_MODEL["completion_proof"][
            "implementation"
        ]
        projection = next(
            item
            for item in proof["projections"]
            if item["target"] == "profile:review-agent"
        )
        for term in projection["terms"]:
            with self.subTest(term=term):
                result, output = self._mutated_source_result(
                    "review-agent",
                    term,
                    "REMOVED_REVIEW_PROOF_TERM",
                )
                self.assertEqual(1, result)
                self.assertIn("independent review evidence projection", output)

    def test_task_agent_requires_exact_validation_evidence_claim(self) -> None:
        proof = VALIDATOR.EVIDENCE_LEDGER_MODEL["completion_proof"][
            "implementation"
        ]
        projection = next(
            item
            for item in proof["projections"]
            if item["target"] == "profile:task-agent"
        )
        for term in projection["terms"]:
            with self.subTest(term=term):
                expected_error = (
                    "exact canonical bullet"
                    if term == "latest material edit"
                    else "independent review evidence projection"
                )
                result, output = self._mutated_source_result(
                    "task-agent",
                    term,
                    "REMOVED_TASK_VALIDATION_PROOF_TERM",
                )
                self.assertEqual(1, result)
                self.assertIn(expected_error, output)

    def test_each_task_forbidden_storage_projection_is_required(self) -> None:
        for rule in VALIDATOR.EVIDENCE_LEDGER_MODEL["forbidden_storage"]:
            term = rule["projection_terms"][0]
            with self.subTest(rule=rule["id"]):
                result, output = self._mutated_source_result(
                    "task-agent",
                    term,
                    "REMOVED_STORAGE_TERM",
                )
                self.assertEqual(1, result)
                self.assertIn(
                    f"forbidden storage projection {rule['id']!r}",
                    output,
                )

    def test_role_boundaries_are_required_for_analysis_task_and_review(self) -> None:
        mutations = (
            ("analysis-agent", "perform final review", "summarize review"),
            ("task-agent", "perform final review", "summarize review"),
            ("review-agent", "Never edit", "Never change files"),
        )
        for role, old, new in mutations:
            with self.subTest(role=role):
                result, output = self._mutated_source_result(role, old, new)
                self.assertEqual(1, result)
                self.assertIn("capability", output)
                self.assertIn("boundary", output)

    def test_analysis_and_review_profiles_load_relocated_decision_owners(self) -> None:
        source = json.loads(VALIDATOR.SOURCE.read_text(encoding="utf-8"))
        profiles = {item["name"]: item["instructions"] for item in source["profiles"]}
        analysis = profiles["analysis-agent"]
        implementation = (
            ROOT
            / "src/professional-skills/engineering-change-analysis/references/implementation-preparation.md"
        ).read_text(encoding="utf-8")
        self.assertIn("selected Professional/mode contract owns", analysis)
        for term in (
            "complete updated Engineering Brief",
            "Delta Impact",
            "Main consumes",
            "without reinterpreting",
        ):
            with self.subTest(role="analysis-agent", term=term):
                self.assertIn(term, implementation)
                self.assertNotIn(term, analysis)
        review = profiles["review-agent"]
        review_handoff = (
            ROOT
            / "src/control-skills/engineering-control-plane/references/review-handoff-template.md"
        ).read_text(encoding="utf-8")
        self.assertIn("assigned Review Handoff", review)
        for term in (
            "Finding Relation",
            "before severity or blocker",
            "implementation or repair review",
            "Pre-implementation artifact review is exempt",
        ):
            with self.subTest(role="review-agent", term=term):
                self.assertIn(term, review_handoff)

    def test_external_read_is_analysis_only_and_resident_rules_are_locked(self) -> None:
        source = json.loads(VALIDATOR.SOURCE.read_text(encoding="utf-8"))
        profiles = {item["name"]: item for item in source["profiles"]}
        self.assertIn("external-source-read", profiles["analysis-agent"]["tools"])
        for role in ("main-control-agent", "task-agent", "review-agent"):
            self.assertNotIn("external-source-read", profiles[role]["tools"])

        analysis = profiles["analysis-agent"]["instructions"]
        for terms in (
            ("Material unresolved Claim", "local or current evidence", "Proof Limit"),
            ("Untrusted evidence input", "normalized Claim", "Engineering Brief"),
            ("minimum public information", "repository-private source", "credential"),
            ("external-source-read", "unsupported", "unknown-critical-boundary"),
        ):
            self.assertTrue(
                any(all(term in rule for term in terms) for rule in analysis.splitlines()),
                terms,
            )
        for role in ("task-agent", "review-agent"):
            instructions = profiles[role]["instructions"]
            self.assertIn("Leave external-source-read", instructions)
            self.assertIn("analysis-agent", instructions)

    def test_external_read_host_modes_and_native_tool_projection_are_exact(self) -> None:
        enforcement = json.loads(
            VALIDATOR.ENFORCEMENT_SOURCE.read_text(encoding="utf-8")
        )
        expected = {
            "codex": "prompt-enforced",
            "claude": "native-enforced",
            "copilot": "prompt-enforced",
            "cline": "unsupported",
            "openai-api": "unsupported",
        }
        for host, host_entry in enforcement["hosts"].items():
            roles = host_entry["roles"]
            self.assertEqual(expected[host], roles["analysis-agent"]["external_source_read"])
            for role in ("main-control-agent", "task-agent", "review-agent"):
                self.assertEqual("unsupported", roles[role]["external_source_read"])
        self.assertEqual(
            ["Skill", "Read", "Grep", "Glob", "WebSearch", "WebFetch"],
            enforcement["hosts"]["claude"]["roles"]["analysis-agent"][
                "rendered_tools"
            ],
        )
        self.assertEqual(
            ["read", "search", "web"],
            enforcement["hosts"]["copilot"]["roles"]["analysis-agent"][
                "rendered_tools"
            ],
        )

    def test_external_read_host_mode_drift_is_rejected(self) -> None:
        mutations = (
            lambda data: data["hosts"]["codex"]["roles"]["analysis-agent"].__setitem__(
                "external_source_read", "general-network"
            ),
            lambda data: data["hosts"]["claude"]["roles"]["task-agent"].__setitem__(
                "external_source_read", "native-enforced"
            ),
            lambda data: data["hosts"]["copilot"]["roles"]["analysis-agent"].pop(
                "external_source_read", None
            ),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                result, output = self._mutated_enforcement_result(mutate)
                self.assertEqual(1, result)
                self.assertIn("external_source_read", output)

    def test_copilot_analysis_tool_projection_drift_is_rejected(self) -> None:
        mutations = (
            ["read", "search"],
            ["read", "search", "web", "execute"],
            ["web", "read", "search"],
        )
        for rendered_tools in mutations:
            with self.subTest(rendered_tools=rendered_tools):
                result, output = self._mutated_enforcement_result(
                    lambda data: data["hosts"]["copilot"]["roles"][
                        "analysis-agent"
                    ].__setitem__("rendered_tools", rendered_tools)
                )
                self.assertEqual(1, result)
                self.assertIn(
                    "copilot:analysis-agent must expose only read, search, and web",
                    output,
                )

    def test_external_read_mode_is_injected_only_into_analysis_profiles(self) -> None:
        source = json.loads(VALIDATOR.SOURCE.read_text(encoding="utf-8"))
        enforcement = json.loads(
            VALIDATOR.ENFORCEMENT_SOURCE.read_text(encoding="utf-8")
        )
        profiles = {item["name"]: item for item in source["profiles"]}
        for host, renderer in (
            ("codex", BUILDER._render_codex_profile),
            ("claude", BUILDER._render_claude_profile),
            ("copilot", BUILDER._render_copilot_profile),
        ):
            with self.subTest(host=host):
                analysis = renderer(profiles["analysis-agent"], enforcement)
                expected_mode = enforcement["hosts"][host]["roles"][
                    "analysis-agent"
                ]["external_source_read"]
                self.assertEqual(
                    1,
                    analysis.count(
                        "Current external-read mode: "
                        f"external_source_read={expected_mode}."
                    ),
                )
                for role in ("main-control-agent", "task-agent", "review-agent"):
                    rendered = renderer(profiles[role], enforcement)
                    self.assertNotIn("Current external-read mode:", rendered)


if __name__ == "__main__":
    unittest.main()
