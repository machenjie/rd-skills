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
    def test_role_reference_consumers_are_source_declared_and_cross_role_safe(self) -> None:
        self.assertEqual(
            [],
            VALIDATOR.role_control_reference_errors(
                "main-control-agent",
                "Load references/direct-task-template.md when Direct Task is selected.",
            ),
        )
        self.assertEqual(
            [],
            VALIDATOR.role_control_reference_errors(
                "task-agent",
                "Load references/implementation-handoff-template.md at closure.",
            ),
        )
        errors = VALIDATOR.role_control_reference_errors(
            "main-control-agent",
            "Load references/implementation-handoff-template.md for capability facts.",
        )
        self.assertTrue(any("owned by task-agent" in error for error in errors), errors)
        errors = VALIDATOR.role_control_reference_errors(
            "review-agent", "Load references/not-registered.md."
        )
        self.assertTrue(any("undeclared control Reference" in error for error in errors), errors)

    def test_task_and_review_profiles_are_role_minimal_consumers(self) -> None:
        source = json.loads(VALIDATOR.SOURCE.read_text(encoding="utf-8"))
        profiles = {profile["name"]: profile for profile in source["profiles"]}
        task = profiles["task-agent"]["instructions"]
        review = profiles["review-agent"]["instructions"]
        self.assertIn("Consume Main's bound effective Level", task)
        self.assertIn("Main-bound Level/depth/assurance", review)
        self.assertIn("never calculate or recompute", task)
        self.assertIn("never recalculate route/authority", review)
        self.assertIn("final edit", task)
        self.assertIn("exact change capture", task)
        self.assertIn("Actual diff authoritative", review)
        self.assertIn("fresh re-review", review)
        self.assertIn(
            "Initial Review completes fixed Review Boundary",
            review,
        )
        self.assertIn("Ready-dispatch blocks", review)
        self.assertIn("Reviewed/Unreviewed Scope+Proof Limit", review)
        self.assertIn("PASS=no blocker", review)
        self.assertIn("Re-review Classification", review)
        self.assertIn("Classification Evidence", review)
        self.assertIn("no prose inference", review)
        for obligation in (
            "Depth only Level-added, never removed.",
            "independently direct read/search current source→minimum complete proof",
            "counts/Top-K/files/summaries/digests/paths/output/opaque refs are selectors only",
            "Actual diff authoritative; every changed file required; missing blocks",
            "older review cannot cover later edits.",
            "Never edit, repair, dispatch or inherit implementer reasoning",
        ):
            self.assertIn(obligation, review)
        self.assertNotIn("PASS requires the full changed scope", review)
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
            "- Semantic Role, Task Contract, and Host tools/sandbox own direct execution; only actual failure blocks.\n"
            "- Retry preserves the same real Task ID and complete unchanged Task Contract with route/Level/review/handoff bindings; Main never implements; task=unspecified is forbidden.\n"
            "- Forward reviewer-accessible exact evidence."
        )

        self.assertEqual(expected, main["instructions"])
        self.assertIn("Dispatch only/no target-code access", main["instructions"])

    def test_host_matrix_declares_tools_and_enforcement_without_runtime_state(self) -> None:
        enforcement = json.loads(
            VALIDATOR.ENFORCEMENT_SOURCE.read_text(encoding="utf-8")
        )
        self.assertEqual(5, enforcement["schema_version"])
        for host in ("codex", "claude", "copilot"):
            with self.subTest(host=host):
                task = enforcement["hosts"][host]["roles"]["task-agent"]
                self.assertTrue(
                    {"edit", "execute", "Write", "Bash"}
                    & set(task["rendered_tools"]),
                    host,
                )
                self.assertIn(
                    task["tool_allowlist"],
                    {"native-enforced", "sandbox-enforced", "prompt-enforced"},
                )
        serialized = json.dumps(enforcement)
        for obsolete in (
            "diff_input_mode",
            "validation_mode",
            "utility_no_edit",
            "native_diff_safeguards",
        ):
            self.assertNotIn(obsolete, serialized)

    def test_copilot_surfaces_are_independent_static_declarations(self) -> None:
        enforcement = json.loads(
            VALIDATOR.ENFORCEMENT_SOURCE.read_text(encoding="utf-8")
        )
        surfaces = enforcement["host_surfaces"]
        self.assertEqual(
            {"copilot-cli", "copilot-vscode", "copilot-coding-agent"},
            set(surfaces),
        )
        self.assertEqual(
            ["read", "search", "web"],
            surfaces["copilot-vscode"]["roles"]["analysis-agent"][
                "rendered_tools"
            ],
        )
        for surface in ("copilot-cli", "copilot-coding-agent"):
            self.assertEqual(
                ["read", "search"],
                surfaces[surface]["roles"]["analysis-agent"]["rendered_tools"],
            )

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

    def test_every_normal_task_agent_receives_source_bound_minimal_kernel(
        self,
    ) -> None:
        core = json.loads(
            (ROOT / "src/control-model/core-contracts.json").read_text(
                encoding="utf-8"
            )
        )
        contract = core["implementation_discipline_contract"]
        self.assertEqual(2, contract["schema_version"])
        self.assertEqual("every normal implementation task-agent", contract["applies_to"])
        self.assertEqual(
            ["task-agent"],
            core["reference_contract"]["control_required_by"][
                "references/implementation-handoff-template.md"
            ],
        )
        source = json.loads(VALIDATOR.SOURCE.read_text(encoding="utf-8"))
        profiles = {profile["name"]: profile for profile in source["profiles"]}
        task = profiles["task-agent"]["instructions"]
        review = profiles["review-agent"]["instructions"]
        for role, text in (("task-agent", task), ("review-agent", review)):
            rules = text.splitlines()
            errors: list[str] = []
            VALIDATOR._validate_minimal_role_projection(role, rules, errors)
            self.assertEqual([], errors)
            for terms in VALIDATOR.ROLE_MINIMAL_REQUIRED_GROUPS[role]:
                self.assertEqual(1, len(VALIDATOR._rule_group_matches(rules, list(terms))))

        fixture = json.loads(
            (ROOT / "evals/agent-light-trajectories/cases.yaml").read_text(
                encoding="utf-8"
            )
        )
        direct_case = next(case for case in fixture["cases"] if case["id"] == "single-file-bug-fix")
        dispatch = next(
            step
            for step in direct_case["steps"]
            if step.get("action") == "dispatch" and step.get("profile") == "task-agent"
        )
        self.assertEqual([], dispatch["layer3_skills"])
        self.assertEqual([], dispatch["layer3_references"])
        for term in ("fresh targeted validation", "exact change capture", "missing or stale facts block"):
            self.assertIn(term, task)

        enforcement = json.loads(VALIDATOR.ENFORCEMENT_SOURCE.read_text(encoding="utf-8"))
        for renderer in (
            BUILDER._render_codex_profile,
            BUILDER._render_claude_profile,
            BUILDER._render_copilot_profile,
        ):
            rendered = renderer(profiles["task-agent"], enforcement)
            for rule in task.splitlines():
                self.assertEqual(1, rendered.count(rule))

    def test_role_minimal_kernels_reject_source_and_built_drift(self) -> None:
        source = json.loads(VALIDATOR.SOURCE.read_text(encoding="utf-8"))
        profiles = {profile["name"]: profile for profile in source["profiles"]}
        for role in ("task-agent", "review-agent"):
            instructions = profiles[role]["instructions"]
            rules = instructions.splitlines()
            for terms in VALIDATOR.ROLE_MINIMAL_REQUIRED_GROUPS[role]:
                exact_rule = next(
                    rule for rule in rules if all(term in rule for term in terms)
                )
                mutation = exact_rule.replace(terms[0], "REMOVED_ROLE_BOUND_TERM", 1)
                with self.subTest(surface="source", role=role, term=terms[0]):
                    result, output = self._mutated_source_result(role, exact_rule, mutation)
                    self.assertEqual(1, result)
                    self.assertIn("role-minimal projection terms", output)

            for terms in VALIDATOR.ROLE_MINIMAL_REQUIRED_GROUPS[role]:
                exact_rule = next(
                    rule for rule in rules if all(term in rule for term in terms)
                )
                mutation = exact_rule.replace(
                    terms[0], "REMOVED_ROLE_BOUND_TERM", 1
                )
                for platform in ("codex", "claude", "copilot"):
                    with self.subTest(
                        surface=platform, role=role, term=terms[0]
                    ):
                        result, output = self._mutated_built_result(
                            platform, role, exact_rule, mutation
                        )
                        self.assertEqual(1, result)
                        self.assertIn("role-minimal projection terms", output)

    def test_decoded_built_instructions_accept_current_profiles(self) -> None:
        source = json.loads(VALIDATOR.SOURCE.read_text(encoding="utf-8"))
        profiles = {profile["name"]: profile for profile in source["profiles"]}
        exact_rule = profiles["task-agent"]["instructions"].splitlines()[0]
        for platform in ("codex", "claude", "copilot"):
            with self.subTest(platform=platform):
                result, output = self._mutated_built_result(
                    platform, "task-agent", exact_rule, exact_rule
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
            "Semantic Role, Task Contract, and Host tools/sandbox own direct "
            "execution; only actual failure blocks."
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
        handoff = (
            ROOT
            / "src/control-skills/engineering-control-plane/references/review-handoff-template.md"
        ).read_text(encoding="utf-8")
        profile = next(
            item["instructions"]
            for item in json.loads(VALIDATOR.SOURCE.read_text(encoding="utf-8"))["profiles"]
            if item["name"] == "review-agent"
        )
        for term in projection["terms"]:
            with self.subTest(term=term):
                self.assertIn(term.casefold(), handoff.casefold())
                self.assertNotIn(term, profile)
        self.assertIn("current evidence", profile)
        self.assertIn("reviewed/unreviewed scope", profile)

    def test_task_agent_requires_exact_validation_evidence_claim(self) -> None:
        proof = VALIDATOR.EVIDENCE_LEDGER_MODEL["completion_proof"][
            "implementation"
        ]
        projection = next(
            item
            for item in proof["projections"]
            if item["target"] == "profile:task-agent"
        )
        handoff = (
            ROOT
            / "src/control-skills/engineering-control-plane/references/implementation-handoff-template.md"
        ).read_text(encoding="utf-8")
        profile_owned_terms = {"latest material edit", "latest-material-edit", "validation-passed"}
        for term in projection["terms"]:
            with self.subTest(term=term):
                self.assertIn(term.casefold(), handoff.casefold())
                if term in profile_owned_terms:
                    result, output = self._mutated_source_result(
                        "task-agent", term, "REMOVED_TASK_VALIDATION_PROOF_TERM"
                    )
                    self.assertEqual(1, result)
                    self.assertIn("role-minimal projection terms", output)

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
                self.assertIn("role-minimal projection terms", output)

    def test_role_boundaries_are_required_for_analysis_task_and_review(self) -> None:
        mutations = (
            ("analysis-agent", "perform final review", "summarize review"),
            ("task-agent", "review your work", "perform final review"),
            ("review-agent", "Never edit", "Never change files"),
        )
        for role, old, new in mutations:
            with self.subTest(role=role):
                result, output = self._mutated_source_result(role, old, new)
                self.assertEqual(1, result)
                self.assertTrue(
                    "capability" in output or "role-minimal projection" in output,
                    output,
                )

    def test_worker_evidence_closure_projection_survives_temp_host_render_and_mutation(
        self,
    ) -> None:
        source = json.loads(VALIDATOR.SOURCE.read_text(encoding="utf-8"))
        enforcement = json.loads(
            VALIDATOR.ENFORCEMENT_SOURCE.read_text(encoding="utf-8")
        )
        renderers = (
            BUILDER._render_codex_profile,
            BUILDER._render_claude_profile,
            BUILDER._render_copilot_profile,
        )
        for profile in source["profiles"]:
            if profile["name"] not in {"analysis-agent", "task-agent", "review-agent"}:
                continue
            role = profile["name"]
            with self.subTest(role=role):
                self.assertEqual(
                    1,
                    profile["instructions"].count("Evidence Closure:"),
                )
                for renderer in renderers:
                    rendered = renderer(profile, enforcement)
                    self.assertEqual(1, rendered.count("Evidence Closure:"))
                result, output = self._mutated_source_result(
                    role,
                    "Evidence Closure:",
                    "Evidence Completion:",
                )
                self.assertEqual(1, result, output)
                self.assertIn("evidence closure", output.casefold())

    def test_worker_evidence_closure_is_losslessly_sentence_split(self) -> None:
        source = json.loads(VALIDATOR.SOURCE.read_text(encoding="utf-8"))
        profiles = {profile["name"]: profile for profile in source["profiles"]}
        selector_limits = {
            "analysis-agent": (
                "Exact locator/counts are selectors only, never "
                "correctness/coverage conclusions."
            ),
            "task-agent": (
                "Exact locator/counts are selectors only; never inherit "
                "correctness/coverage."
            ),
            "review-agent": (
                "Exact locator/counts/Top-K/files/summaries/digests/paths/output/"
                "opaque refs are selectors only; never inherit correctness/coverage."
            ),
        }
        for role, selector_limit in selector_limits.items():
            with self.subTest(role=role):
                instructions = profiles[role]["instructions"]
                rules = instructions.splitlines()
                closure_line = next(
                    index
                    for index, rule in enumerate(rules, start=1)
                    if rule.startswith("- Evidence Closure:")
                )
                closure_rule = rules[closure_line - 1]
                for sentence in (
                    ". New/invalidated/contradicted reopens affected only.",
                    (
                        "Protected/material returns Main: initial Analysis without "
                        "accepted Brief; bounded Delta only after accepted Brief invalidation."
                    ),
                    selector_limit,
                ):
                    self.assertIn(sentence, closure_rule)
                errors: list[str] = []
                findings = VALIDATOR.validate_ai_readability(
                    instructions,
                    f"{role}#instructions",
                    errors,
                )
                self.assertEqual([], errors)
                self.assertFalse(
                    any(
                        finding["line"] == closure_line
                        and finding["kind"] == "sentence-length"
                        for finding in findings
                    ),
                    findings,
                )

    def test_task_handoff_is_losslessly_sentence_split(self) -> None:
        source = json.loads(VALIDATOR.SOURCE.read_text(encoding="utf-8"))
        profiles = {profile["name"]: profile for profile in source["profiles"]}
        instructions = profiles["task-agent"]["instructions"]
        rules = instructions.splitlines()
        handoff_line = next(
            index
            for index, rule in enumerate(rules, start=1)
            if rule.startswith("- Handoff after final edit+fresh validation:")
        )
        handoff_rule = rules[handoff_line - 1]
        for sentence in (
            "Implementation Handoff/Main readiness.",
            "Completion gate: missing or stale facts block.",
            "Recovery boundary: no recovery Task.",
        ):
            self.assertIn(sentence, handoff_rule)
        self.assertEqual(
            1,
            sum(
                profile["instructions"].count("no recovery Task")
                for profile in profiles.values()
            ),
        )
        errors: list[str] = []
        findings = VALIDATOR.validate_ai_readability(
            instructions,
            "task-agent#instructions",
            errors,
        )
        self.assertEqual([], errors)
        self.assertFalse(
            any(
                finding["line"] == handoff_line
                and finding["band"] in {"tighten", "hard-fail"}
                for finding in findings
            ),
            findings,
        )

    def test_analysis_and_review_profiles_load_relocated_decision_owners(self) -> None:
        source = json.loads(VALIDATOR.SOURCE.read_text(encoding="utf-8"))
        profiles = {item["name"]: item["instructions"] for item in source["profiles"]}
        analysis = profiles["analysis-agent"]
        implementation = (
            ROOT
            / "src/control-skills/engineering-control-plane/references/engineering-brief-template.md"
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

    def test_static_capability_and_external_read_modes_are_not_injected(self) -> None:
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
                for role in (
                    "main-control-agent",
                    "analysis-agent",
                    "task-agent",
                    "review-agent",
                ):
                    rendered = renderer(profiles[role], enforcement)
                    self.assertNotIn("Current external-read mode:", rendered)
                    self.assertNotIn("Current capability facts:", rendered)


if __name__ == "__main__":
    unittest.main()
