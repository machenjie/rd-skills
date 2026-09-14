from __future__ import annotations

import copy
import importlib.util
import io
import json
import re
import sys
import tempfile
import tomllib
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build as BUILDER
from validation_utils import CORE_CONTRACTS, count_o200k_base_tokens, validate_core_contracts


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
    def test_analysis_executes_observations_without_edit_or_review_authority(self) -> None:
        profiles = {profile["name"]: profile for profile in BUILDER._load_agent_profiles()}
        analysis = profiles["analysis-agent"]
        self.assertIn("execute-read-only", analysis["tools"])
        self.assertFalse({"edit", "execute", "dispatch"} & set(analysis["tools"]))
        self.assertEqual("read-only", analysis["sandbox"])
        self.assertFalse(CORE_CONTRACTS["roles"]["analysis-agent"]["may_review"])
        self.assertTrue(CORE_CONTRACTS["roles"]["review-agent"]["may_review"])
        self.assertEqual([], validate_core_contracts(CORE_CONTRACTS))

        matrix = BUILDER._load_host_enforcement()
        codex = tomllib.loads(BUILDER._render_codex_profile(analysis, matrix))
        self.assertEqual("read-only", codex["sandbox_mode"])
        self.assertIn("execute-read-only", codex["developer_instructions"])
        for host, renderer, command in (
            ("claude", BUILDER._render_claude_profile, "Bash"),
            ("copilot", BUILDER._render_copilot_profile, "execute"),
        ):
            with self.subTest(host=host):
                rendered = renderer(analysis, matrix)
                tools_line = next(line for line in rendered.splitlines() if line.startswith("tools: "))
                tools = (json.loads(tools_line[7:]) if host == "copilot"
                         else tools_line[7:].split(", "))
                self.assertIn(command, tools)
                self.assertFalse({"Edit", "Write", "edit", "Task", "agent"} & set(tools))
                role = matrix["hosts"][host]["roles"]["analysis-agent"]
                self.assertEqual("prompt-enforced", role["workspace_write_protection"])
                self.assertEqual("prompt-enforced", role["read_only_command_semantics"])
        for surface in matrix["host_surfaces"].values():
            tools = surface["roles"]["analysis-agent"]["rendered_tools"]
            self.assertIn("execute", tools)
            self.assertNotIn("edit", tools)

    def test_core_rejects_analysis_mutation_and_review_authority(self) -> None:
        for tool in ("edit", "execute", "dispatch"):
            with self.subTest(tool=tool):
                core = copy.deepcopy(CORE_CONTRACTS)
                core["roles"]["analysis-agent"]["tools"].append(tool)
                self.assertTrue(validate_core_contracts(core))
        core = copy.deepcopy(CORE_CONTRACTS)
        core["roles"]["analysis-agent"]["may_review"] = True
        self.assertIn("may_review must belong only to review-agent", validate_core_contracts(core))

    def test_analysis_host_delivery_rejects_missing_execution_edits_and_false_enforcement(self) -> None:
        baseline = json.loads(VALIDATOR.ENFORCEMENT_SOURCE.read_text(encoding="utf-8"))
        for host, command, edit in (
            ("codex", "execute-read-only", "edit"),
            ("claude", "Bash", "Write"),
            ("copilot", "execute", "edit"),
        ):
            for change in ("missing-execution", "edit", "false-enforcement"):
                with self.subTest(host=host, change=change):
                    matrix = copy.deepcopy(baseline)
                    role = matrix["hosts"][host]["roles"]["analysis-agent"]
                    if change == "missing-execution":
                        role["rendered_tools"].remove(command)
                    elif change == "edit":
                        role["rendered_tools"].append(edit)
                    else:
                        role["workspace_write_protection"] = "native-enforced"
                    with tempfile.TemporaryDirectory() as raw:
                        path = Path(raw) / "host-enforcement.json"
                        path.write_text(json.dumps(matrix), encoding="utf-8")
                        with mock.patch.object(BUILDER, "HOST_ENFORCEMENT_SOURCE", path):
                            with self.assertRaises(BUILDER.BuildError):
                                BUILDER._load_host_enforcement()
                    result, output = self._mutated_enforcement_result(
                        lambda data: data.update(matrix)
                    )
                    self.assertEqual(1, result, output)
                    self.assertIn("analysis-agent", output)

    def test_source_composite_ignores_stale_built_profiles(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "source_invariants_profile_test", SCRIPTS / "validate-src-invariants.py"
        )
        assert spec is not None and spec.loader is not None
        composite = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(composite)
        calls = []

        def run_validator(argv, **kwargs):
            calls.append(argv)
            if Path(argv[1]).name == "validate-agent-profiles.py" and "--source-only" not in argv:
                return mock.Mock(returncode=1, stdout="", stderr="stale built Profile")
            return mock.Mock(returncode=0, stdout="", stderr="")

        with mock.patch.object(composite.subprocess, "run", side_effect=run_validator), redirect_stdout(io.StringIO()):
            self.assertEqual(0, composite.main())
        profile_calls = [argv for argv in calls if Path(argv[1]).name == "validate-agent-profiles.py"]
        self.assertEqual(1, len(profile_calls))
        self.assertIn("--source-only", profile_calls[0])

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
        self.assertEqual([], errors)
        errors = VALIDATOR.role_control_reference_errors(
            "review-agent", "Load references/not-registered.md."
        )
        self.assertTrue(any("missing control Reference" in error for error in errors), errors)

    def _mutated_source_result(
        self,
        role: str,
        old: str,
        new: str,
    ) -> tuple[int, str]:
        source = json.loads(VALIDATOR.SOURCE.read_text(encoding="utf-8"))
        profile = next(item for item in source["profiles"] if item["name"] == role)
        self.assertIn(old, profile["instructions"])
        profile["instructions"] = re.sub(re.escape(old), new, profile["instructions"], flags=re.IGNORECASE)
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
                    rendered = rendered.replace(old, new)
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

    def test_source_instructions_pass_readability_gate(self) -> None:
        errors: list[str] = []
        for profile in BUILDER._load_agent_profiles():
            VALIDATOR.validate_ai_readability(
                profile["instructions"], profile["name"], errors
            )
        self.assertEqual([], errors)


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
            ["read", "search", "execute", "web"],
            surfaces["copilot-vscode"]["roles"]["analysis-agent"][
                "rendered_tools"
            ],
        )
        for surface in ("copilot-cli", "copilot-coding-agent"):
            self.assertEqual(
                ["read", "search", "execute"],
                surfaces[surface]["roles"]["analysis-agent"]["rendered_tools"],
            )

    def test_profile_rule_limits_are_core_driven_and_enforced(self) -> None:
        limits = VALIDATOR.PROFILE_CONTRACT_MODEL["instruction_rule_count"]
        source = json.loads(VALIDATOR.SOURCE.read_text(encoding="utf-8"))
        profiles = {profile["name"]: profile for profile in source["profiles"]}
        task_rules = profiles["task-agent"]["instructions"].splitlines()
        for role, profile in profiles.items():
            maximum = limits.get("maximum_by_role", {}).get(role, limits["maximum"])
            self.assertLessEqual(len(profile["instructions"].splitlines()), maximum)
        last_rule = task_rules[-1]
        task_maximum = limits.get("maximum_by_role", {}).get(
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




    def test_decoded_built_instructions_accept_current_profiles(self) -> None:
        source = json.loads(VALIDATOR.SOURCE.read_text(encoding="utf-8"))
        profiles = {profile["name"]: profile for profile in source["profiles"]}
        for role in ("analysis-agent", "task-agent", "review-agent"):
            exact_rule = profiles[role]["instructions"].splitlines()[0]
            for platform in ("codex", "claude", "copilot"):
                with self.subTest(role=role, platform=platform):
                    result, output = self._mutated_built_result(
                        platform, role, exact_rule, exact_rule
                    )
                    self.assertEqual(0, result, output)

    def test_worker_primary_consumption_cannot_be_removed(self) -> None:
        consumption = "Apply Main's assigned Primary Professional Skill"
        for role in ("analysis-agent", "task-agent", "review-agent"):
            with self.subTest(role=role):
                result, output = self._mutated_source_result(
                    role, consumption, "Observe the assignment"
                )
                self.assertEqual(1, result, output)
                self.assertIn("professional delivery safeguard", output)
                self.assertIn(consumption, output)
            for platform in ("codex", "claude", "copilot"):
                with self.subTest(role=role, platform=platform):
                    result, output = self._mutated_built_result(
                        platform, role, consumption, "Observe the assignment"
                    )
                    self.assertEqual(1, result, output)
                    self.assertIn("professional delivery safeguard", output)
                    self.assertIn(consumption, output)

    def test_worker_consumption_preserves_conditional_loading_and_routing(self) -> None:
        # Each mutation removes or reverses one instruction. These are static
        # contract checks, not a simulated Worker or evidence of Host invocation.
        mutations = (
            ("only assigned Layer 3/needed References",
             "any related Layer 3/References"),
            ("when relevant", "for an assignment log"),
            ("possibly empty", "Layer 3 must never be empty"),
            ("Reuse supplied content; load missing via Host", "reload context or load missing content"),
            ("load missing via Host", "load all through model familiarity"),
            ("supplied content", "model familiarity"),
            ("bounded discovery may precede loading", "Bounded source discovery requires prior loading"),
            ("No rerouting/catalog preload", "Reroute and preload the catalog"),
            ("Return selection-changing source evidence to Main", "adjust selection from source evidence"),
        )
        for role in ("analysis-agent", "task-agent", "review-agent"):
            for old, new in mutations:
                with self.subTest(role=role, safeguard=old):
                    result, output = self._mutated_source_result(role, old, new)
                    self.assertEqual(1, result, output)
                    self.assertIn("professional delivery safeguard", output)
                    self.assertIn(old, output)

    def test_review_consumes_its_independent_assignment(self) -> None:
        for old, new in (
            ("Use Main's independent Review assignment", "Reuse the Task assignment"),
            ("Never copy/union Task Layer 3", "copy/union Task Layer 3"),
        ):
            with self.subTest(safeguard=old):
                result, output = self._mutated_source_result("review-agent", old, new)
                self.assertEqual(1, result, output)
                self.assertIn("independent Review safeguard", output)
                self.assertIn(old, output)
            for platform in ("codex", "claude", "copilot"):
                with self.subTest(platform=platform, safeguard=old):
                    result, output = self._mutated_built_result(
                        platform, "review-agent", old, new
                    )
                    self.assertEqual(1, result, output)
                    self.assertIn("independent Review safeguard", output)
                    self.assertIn(old, output)

    def test_task_tool_boundary_survives_instruction_deduplication(self) -> None:
        profiles = {row["name"]: row for row in BUILDER._load_agent_profiles()}
        task = profiles["task-agent"]
        self.assertEqual(["read", "search", "edit", "execute"], task["tools"])
        self.assertNotIn("- Use read/search/edit/execute.", task["instructions"])
        self.assertIn("selection-changing source evidence to Main", task["instructions"])
        boundary = "Declared tool boundary: read, search, edit, execute."
        for platform in ("codex", "claude", "copilot"):
            with self.subTest(platform=platform):
                result, output = self._mutated_built_result(
                    platform, "task-agent", boundary, boundary
                )
                self.assertEqual(0, result, output)
                result, output = self._mutated_built_result(
                    platform, "task-agent", boundary, "Declared tool boundary: read."
                )
                self.assertEqual(1, result, output)
                self.assertIn("decoded instruction surface", output)

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







    def test_role_boundaries_are_required_for_analysis_task_and_review(self) -> None:
        mutations = (
            ("analysis-agent", "read-only", "read-write"),
            ("task-agent", "authorized write scope", "any write scope"),
            ("review-agent", "read-only", "read-write"),
        )
        for role, old, new in mutations:
            with self.subTest(role=role):
                result, output = self._mutated_source_result(role, old, new)
                self.assertEqual(1, result)
                self.assertTrue(
                    "behavioral safeguard" in output,
                    output,
                )





    def test_external_read_is_analysis_only_and_resident_rules_are_locked(self) -> None:
        source = json.loads(VALIDATOR.SOURCE.read_text(encoding="utf-8"))
        profiles = {item["name"]: item for item in source["profiles"]}
        self.assertIn("external-source-read", profiles["analysis-agent"]["tools"])
        for role in ("main-control-agent", "task-agent", "review-agent"):
            self.assertNotIn("external-source-read", profiles[role]["tools"])

        for role, boundary in (
            ("task-agent", "external reads require Analysis"),
            ("review-agent", "no edit, repair, dispatch, or independent external-source-read"),
        ):
            with self.subTest(role=role):
                self.assertIn(boundary, profiles[role]["instructions"])


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
            ["Skill", "Read", "Grep", "Glob", "Bash", "WebSearch", "WebFetch"],
            enforcement["hosts"]["claude"]["roles"]["analysis-agent"][
                "rendered_tools"
            ],
        )
        self.assertEqual(
            ["read", "search", "execute", "web"],
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
            ["read", "search", "execute", "web", "edit"],
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
                    "copilot:analysis-agent must expose only read, search, execute, and web",
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
