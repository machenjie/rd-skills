from __future__ import annotations

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

    def test_all_profile_surfaces_have_no_readability_findings(self) -> None:
        source = json.loads(VALIDATOR.SOURCE.read_text(encoding="utf-8"))
        for profile in source["profiles"]:
            for part, check_bullets in (
                ("description", False),
                ("instructions", True),
            ):
                role = profile["name"]
                with self.subTest(role=role, part=part):
                    errors: list[str] = []
                    findings = VALIDATOR.validate_ai_readability(
                        profile[part],
                        f"{role}#{part}",
                        errors,
                        check_bullets=check_bullets,
                    )
                    self.assertEqual([], errors)
                    self.assertEqual([], findings)

    def test_task_agent_uses_an_explicit_rule_count_override(self) -> None:
        limits = VALIDATOR.PROFILE_CONTRACT_MODEL["instruction_rule_count"]
        self.assertEqual(16, limits["maximum"])
        self.assertEqual(
            {"task-agent": 38, "review-agent": 18},
            limits["maximum_by_role"],
        )

        source = json.loads(VALIDATOR.SOURCE.read_text(encoding="utf-8"))
        profiles = {profile["name"]: profile for profile in source["profiles"]}
        task_rules = profiles["task-agent"]["instructions"].splitlines()
        self.assertEqual(38, len(task_rules))
        self.assertEqual(18, len(profiles["review-agent"]["instructions"].splitlines()))
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
        result, output = self._mutated_source_result(
            "task-agent",
            last_rule,
            f"{last_rule}\n- Preserve one unrelated extra instruction.",
        )
        self.assertEqual(1, result)
        self.assertIn("instructions must contain 6-38 newline bullet rules", output)

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
            835,
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
                "Re-review may be skipped after repair.",
                ("including re-review of only", "excluding re-review of"),
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

    def test_analysis_handoff_requires_four_state_status(self) -> None:
        result, output = self._mutated_source_result(
            "analysis-agent",
            "four-state Status, a visible task-local Evidence Ledger",
            "completed Status, a visible task-local Evidence Ledger",
        )
        self.assertEqual(1, result)
        self.assertIn("handoff 'analysis-handoff'", output)

    def test_analysis_assignments_require_initial_in_progress(self) -> None:
        result, output = self._mutated_source_result(
            "analysis-agent",
            "`Status: in_progress`",
            "`Status: partial`",
        )
        self.assertEqual(1, result)
        self.assertIn("task-contract-status", output)

    def test_main_profile_rejects_prompt_owned_contract_copies(self) -> None:
        anchor = (
            "Generated host modes are authoritative; absent or unrecognized means "
            "unsupported."
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
                result, output = self._mutated_source_result(
                    "task-agent",
                    term,
                    "REMOVED_TASK_VALIDATION_PROOF_TERM",
                )
                self.assertEqual(1, result)
                self.assertIn("independent review evidence projection", output)

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


if __name__ == "__main__":
    unittest.main()
