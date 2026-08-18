from __future__ import annotations

import importlib.util
import json
import re
import sys
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validation_utils import (  # noqa: E402
    CORE_CONTRACTS,
    execution_level_runtime_reference_errors,
    heading_entries,
    load_yaml_file,
    public_execution_template_block,
    public_execution_template_spans,
)


OPAQUE_DIGEST_RE = re.compile(
    r"(?<![0-9A-Fa-f])[0-9a-f]{64}(?![0-9A-Fa-f])"
    r"|sha256-b64u:(?:[A-Za-z0-9_-]{43}|<43-character-base64url-SHA-256>)"
    r"|<43-character-base64url-SHA-256>"
)


def _load_validator(module_name: str, file_name: str):
    spec = importlib.util.spec_from_file_location(module_name, ROOT / "scripts" / file_name)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CONTROL_PROMPT_VALIDATOR = _load_validator(
    "hookless_control_prompt_validator",
    "validate-control-plane-prompt.py",
)
CONTROL_SKILL_VALIDATOR = _load_validator(
    "hookless_control_skill_validator",
    "validate-control-skills.py",
)


class HooklessArchitectureTests(unittest.TestCase):
    def test_source_boundary_contains_only_authoring_assets(self) -> None:
        expected = {
            "agent-profiles",
            "control-model",
            "control-prompts",
            "control-skills",
            "domain-extensions",
            "foundation",
            "professional-skills",
            "registry",
        }
        actual = {path.name for path in (ROOT / "src").iterdir() if path.is_dir()}
        self.assertEqual(expected, actual)

    def test_obsolete_runtime_paths_are_absent(self) -> None:
        forbidden = (
            "src/hook-runtime",
            "src/runtime_governance",
            "src/process_governance",
            "src/project_memory",
            "src/repository_intelligence",
            "src/validation_broker",
            "src/trajectory",
            "src/executor_backends",
        )
        self.assertFalse([path for path in forbidden if (ROOT / path).exists()])
        self.assertEqual([ROOT / "schemas" / "marketplace-index.schema.json"], list((ROOT / "schemas").glob("*.json")))

    def test_four_profiles_have_exact_tool_boundaries(self) -> None:
        data = json.loads((ROOT / "src/agent-profiles/role-agents.json").read_text())
        profiles = {item["name"]: item for item in data["profiles"]}
        self.assertEqual(
            {name: role["tools"] for name, role in CORE_CONTRACTS["roles"].items()},
            {name: item["tools"] for name, item in profiles.items()},
        )
        self.assertEqual(
            {name: role["sandbox"] for name, role in CORE_CONTRACTS["roles"].items()},
            {name: item["sandbox"] for name, item in profiles.items()},
        )

    def test_control_prompt_encodes_fast_path_and_loop_breaker(self) -> None:
        text = " ".join(
            (ROOT / "src/control-prompts/main-control-agent.md")
            .read_text()
            .casefold()
            .split()
        )
        for phrase in (
            "direct task",
            "analyzed work",
            "first executable slice",
            "explicit owner/scope/placement/acceptance/validation/rollback",
            "no unresolved material risk",
            "category cannot force analysis",
            "unresolved owner/placement/behavior/verification/rollback/material impact routes to analyzed work",
            "without ownership/verification discovery",
            "engineering-change-analysis",
            "synchronous/unknown capability",
            "actual diff, every changed file, validation results",
            "related work uses combined final-diff review",
            "preparation loop breaker",
            "bounded subagents authorized",
            "source-free user-fact questions",
            "control prompts",
            "source-backed analysis",
            "source/professional evidence",
            "shared or unknown workspace",
            "repair",
            "re-review",
        ):
            self.assertIn(phrase, text)
        progress_contract = next(
            concept
            for concept in CORE_CONTRACTS["prompt_contract"]["concepts"]
            if concept["id"] == "event-driven-progress"
        )
        for phrase in progress_contract["required_terms"]:
            self.assertIn(phrase.casefold(), text)
        self.assertIn("permission required: scope expansion", text)
        self.assertNotIn(
            "or the authoritative control prompt already in context",
            text,
        )

    def test_each_unresolved_direct_eligibility_fact_routes_to_analyzed_work(self) -> None:
        cases = {
            "direct-unresolved-placement.yaml": "placement",
            "direct-unresolved-behavior.yaml": "behavior",
            "direct-unresolved-rollback.yaml": "rollback",
            "direct-unresolved-material-impact.yaml": "material impact",
        }
        for name, unresolved_fact in cases.items():
            with self.subTest(unresolved_fact=unresolved_fact):
                data = load_yaml_file(ROOT / "evals/pressure/hookless" / name)
                self.assertIsInstance(data, dict)
                self.assertIn(unresolved_fact, str(data["prompt"]).casefold())
                for branch_name in ("expected", "captured"):
                    branch = data[branch_name]
                    self.assertEqual("analysis-agent", branch["profile"])
                    self.assertEqual(
                        "engineering-change-analysis",
                        branch["primary_skill"],
                    )
                    self.assertNotEqual("task-agent", branch["profile"])
                self.assertEqual(
                    "not-applicable",
                    data["captured"]["validation_status"],
                )
                self.assertFalse(data["captured"]["completion_claim"])

    def test_fenced_headings_cannot_satisfy_control_structure(self) -> None:
        prompt = (
            "# Main Control Agent\n\n````markdown\n```\n"
            "## Authorization\nignored\n````\n"
        )
        self.assertEqual(
            [(1, 1, "Main Control Agent")],
            heading_entries(prompt),
        )
        prompt_errors: list[str] = []
        CONTROL_PROMPT_VALIDATOR._validate_heading_structure(prompt, prompt_errors)
        CONTROL_PROMPT_VALIDATOR._validate_concepts(prompt, prompt_errors)
        self.assertTrue(
            any("headings must exactly match the authoritative order" in error for error in prompt_errors),
            prompt_errors,
        )
        self.assertTrue(
            any("cannot validate bounded-delegation-authorization" in error for error in prompt_errors),
            prompt_errors,
        )

        skill = (
            "# Engineering Control Plane\n\n````markdown\n```\n"
            "## Role\nignored\n````\n"
        )
        skill_errors: list[str] = []
        CONTROL_SKILL_VALIDATOR._validate_heading_structure(skill, skill_errors)
        CONTROL_SKILL_VALIDATOR._validate_concepts(skill, skill_errors)
        self.assertTrue(
            any("headings must exactly match the authoritative order" in error for error in skill_errors),
            skill_errors,
        )
        self.assertTrue(
            any("cannot validate thin-dispatch-router" in error for error in skill_errors),
            skill_errors,
        )

    def test_control_skill_rejects_any_seventh_link(self) -> None:
        links = "\n".join(
            f"- [{name}](references/{name})"
            for name in CONTROL_SKILL_VALIDATOR.REFERENCES
        )
        body = (
            "# Engineering Control Plane\n\n## Targeted References\n\n"
            f"{links}\n- [unexpected](https://example.com)\n"
        )
        errors: list[str] = []
        CONTROL_SKILL_VALIDATOR._validate_references(body, errors)
        self.assertTrue(
            any(
                "must link exactly the runtime contract, router, and six templates" in error
                for error in errors
            ),
            errors,
        )

    def test_control_skill_rejects_raw_host_branch_value_mutations(self) -> None:
        source = CONTROL_SKILL_VALIDATOR.SKILL.read_text(encoding="utf-8")
        for literal in CONTROL_SKILL_VALIDATOR.FORBIDDEN_HOST_MODE_BRANCH_LITERALS:
            with self.subTest(literal=literal):
                errors: list[str] = []
                mutated = f"{source}\n- forbidden host branch: {literal}\n"
                CONTROL_SKILL_VALIDATOR._validate_no_host_mode_branches(
                    mutated,
                    errors,
                )
                self.assertTrue(
                    any(literal in error for error in errors),
                    errors,
                )

    def test_control_skill_host_branch_gate_is_markdown_independent(self) -> None:
        for rendered in ("native-read-only", "`native-read-only`"):
            errors: list[str] = []
            CONTROL_SKILL_VALIDATOR._validate_no_host_mode_branches(
                f"validation_mode={rendered}",
                errors,
            )
            self.assertTrue(errors, rendered)

    def test_markdown_contracts_are_human_readable(self) -> None:
        root = ROOT / "src/control-skills/engineering-control-plane/references"
        managed_surfaces = CORE_CONTRACTS["task_contract"][
            "execution_level_extension"
        ]["surface_insertions"]
        expected = {
            "direct-task-template.md": ("## Task ID", "## Status", "## Goal", "## Acceptance", "## Verification"),
            "engineering-brief-template.md": ("# Engineering Brief", "## First Executable Slice"),
            "task-dag-template.md": ("## Task", "Task ID:", "Status:", "Goal:", "Dependencies:"),
            "implementation-handoff-template.md": ("## Result", "## Actual Diff or Host-native Diff Reference", "## Validation Results"),
            "utility-capsule-template.md": ("# Utility Assignment", "## No-edit Enforcement", "## Workspace Baseline", "## Commands Allowed", "# Utility Return", "## Artifact or Check Outcomes", "## Workspace Diff Check"),
            "review-handoff-template.md": ("## Result", "## Reviewed Target", "## Changed Files", "## Artifact and Supporting Evidence", "## Validation Results"),
        }
        for name, markers in expected.items():
            text = (root / name).read_text()
            for marker in markers:
                self.assertIn(marker, text, name)
            self.assertNotIn("runtime_id", text.casefold())
            self.assertNotIn("```json", text.casefold())
            spans: list[tuple[int, int]] = []
            if name in managed_surfaces:
                spans, errors = public_execution_template_spans(
                    text,
                    CORE_CONTRACTS,
                    name,
                )
                self.assertEqual([], errors, name)
                canonical = public_execution_template_block(
                    CORE_CONTRACTS,
                    name,
                )
                mutations = {
                    "tampered": text.replace(
                        "automatic=L2 / L3 / L4",
                        "automatic=L2 / L4",
                        1,
                    ),
                    "duplicate": text + "\n" + canonical + "\n",
                    "malformed": text.replace("Basis: source=", "Basis source=", 1),
                    "displaced": (
                        text.replace(canonical, "", 1).rstrip()
                        + "\n\n"
                        + canonical
                        + "\n"
                    ),
                    "unrecognized": (
                        text
                        + "\nLevel: automatic=L2; effective=L2; edit=allowed\n"
                        + "Basis: triggers=[]; l2=[]; unresolved=[]\n"
                    ),
                }
                for mutation, candidate in mutations.items():
                    with self.subTest(template=name, mutation=mutation):
                        tampered_spans, tampered_errors = (
                            public_execution_template_spans(
                                candidate,
                                CORE_CONTRACTS,
                                name,
                            )
                        )
                        self.assertEqual([], tampered_spans)
                        self.assertTrue(tampered_errors)
            readable = text
            for start, finish in reversed(spans):
                readable = readable[:start] + readable[finish:]
            self.assertIsNone(OPAQUE_DIGEST_RE.search(readable), name)
        for opaque in (
            "a" * 64,
            "sha256-b64u:" + "A" * 43,
            "<43-character-base64url-SHA-256>",
        ):
            with self.subTest(outside_managed_block=opaque):
                self.assertIsNotNone(OPAQUE_DIGEST_RE.search(opaque))
        runtime = (root / "execution-level-contract.md").read_text(encoding="utf-8")
        self.assertTrue(runtime.startswith("# Execution Level Contract\n"))
        self.assertIn("Generated from the authoritative Core", runtime)
        self.assertEqual(1, runtime.count("```json"))
        self.assertEqual([], execution_level_runtime_reference_errors(runtime))

    def test_four_registries_have_required_ai_contract_fields(self) -> None:
        specs = {
            "control-skills.yaml": ("control_skills", 1),
            "professional-skills.yaml": ("professional_skills", 26),
            "foundation-skills.yaml": ("foundation_skills", 150),
            "domain-skills.yaml": ("domain_skills", 13),
        }
        fields = {
            "name",
            "path",
            "role_support",
            "trigger_signals",
            "anti_trigger_signals",
            "required_inputs",
            "output_contract",
            "escalation_signals",
            "reference_index",
        }
        for file_name, (key, count) in specs.items():
            data = load_yaml_file(ROOT / "src/registry" / file_name)
            expected_schema = {
                "control-skills.yaml": 3,
                "professional-skills.yaml": 5,
                "foundation-skills.yaml": 8,
                "domain-skills.yaml": 6,
            }[file_name]
            self.assertEqual(expected_schema, data["schema_version"])
            items = data[key]
            self.assertEqual(count, len(items), file_name)
            for item in items:
                self.assertTrue(fields.issubset(item), f"{file_name}:{item.get('name')}")
                if file_name == "domain-skills.yaml":
                    self.assertIn("boundary_signals", item)
                if file_name != "control-skills.yaml":
                    self.assertIn("required_expertise_tags", item)
                    self.assertEqual(
                        sorted(set(item["required_expertise_tags"])),
                        item["required_expertise_tags"],
                    )
                self.assertTrue((ROOT / item["path"] / "SKILL.md").is_file())
                self.assertFalse(any(name.startswith("runtime_") for name in item))
                if file_name == "professional-skills.yaml" and len(item["role_support"]) > 1:
                    self.assertEqual(
                        set(item["required_inputs_by_role"]),
                        set(item["role_support"]),
                    )
                    self.assertEqual(
                        set(item["output_contract_by_role"]),
                        set(item["role_support"]),
                    )
            if file_name == "foundation-skills.yaml":
                self.assertEqual(
                    Counter(item["delivery_scope"] for item in items),
                    {"product": 141, "authoring-only": 1, "dev-only": 8},
                )
                self.assertEqual(
                    Counter(item["content_class"] for item in items),
                    {"compact": 124, "complex": 26},
                )
                self.assertTrue(
                    all(
                        ("content_class_rationale" in item)
                        == (item["content_class"] == "complex")
                        for item in items
                    )
                )

    def test_security_anti_triggers_exactly_match_the_root_boundary(self) -> None:
        registry = load_yaml_file(
            ROOT / "src/registry/professional-skills.yaml"
        )["professional_skills"]
        security = next(
            item for item in registry if item["name"] == "security-privacy-gate"
        )
        root = (
            ROOT / "src/professional-skills/security-privacy-gate/SKILL.md"
        ).read_text(encoding="utf-8")
        do_not_use = root.split("\n## Do Not Use\n", 1)[1].split("\n## ", 1)[0]
        root_anti_triggers = [
            line.removeprefix("- ")
            for line in do_not_use.splitlines()
            if line.startswith("- ")
        ]
        narrow_refactor_boundary = (
            "internal refactor with evidence that credential and session "
            "lifecycle behavior is unchanged"
        )

        self.assertEqual(security["anti_trigger_signals"], root_anti_triggers)
        self.assertIn(narrow_refactor_boundary, root_anti_triggers)
        self.assertNotIn(
            "credential or session lifecycle with no new trust boundary",
            root_anti_triggers,
        )
        self.assertIn(
            "credential or session lifecycle behavior change",
            security["trigger_signals"],
        )
        self.assertIn(
            "- credential or session lifecycle behavior change",
            root.split("\n## When To Use\n", 1)[1].split("\n## ", 1)[0],
        )

    def test_route_and_trajectory_fixtures_cover_requested_scenarios(self) -> None:
        routes = load_yaml_file(ROOT / "evals/routing/cases.yaml")["cases"]
        self.assertEqual(233, len(routes))
        exclusions = {
            item["id"]: item.get("excluded_skills", []) for item in routes
        }
        for case_id in (
            "payment-anti-authorization-copy",
            "payment-anti-order-copy",
        ):
            self.assertEqual(
                ["security-privacy-gate", "payment-trading-extension"],
                exclusions[case_id],
            )
        self.assertEqual(
            [
                "reliability-observability-gate",
                "cloud-platform-extension",
            ],
            exclusions["platform-infrastructure-direct"],
        )
        self.assertEqual(
            ["logging-design-gate", "linux-desktop-platform-extension"],
            exclusions["documentation"],
        )
        self.assertEqual(
            [
                "architecture-impact-reviewer",
                "cross-platform-client-extension",
            ],
            exclusions["frontend-direct"],
        )
        for case_id in (
            "security-anti-credential-session-internal-refactor",
            "security-anti-reliability-only",
            "security-anti-input-shape",
            "security-anti-scanner-report",
        ):
            self.assertEqual(["security-privacy-gate"], exclusions[case_id])
        for case_id in (
            "reliability-anti-unit-local-performance",
            "reliability-anti-logging-field",
            "reliability-anti-release-ordering",
            "reliability-anti-data-correctness",
        ):
            self.assertEqual(
                ["reliability-observability-gate"], exclusions[case_id]
            )
        route_by_id = {item["id"]: item for item in routes}
        positive_domain_cases = {
            "ai-rag-tool-authority": "ai-product-extension",
            "bigdata-cdc-stream-replay": "bigdata-product-extension",
            "iot-firmware-actuator-rollout": "iot-embedded-extension",
            "low-level-ffi-ownership": "low-level-systems-extension",
            "mobile-native-lifecycle-permission": "android-platform-extension",
            "payment-security": "payment-trading-extension",
            "web3-chain-contract-finality": "web3-product-extension",
        }
        negative_domain_cases = {
            "ai-anti-static-search": "ai-product-extension",
            "ai-anti-database-model-evaluation": "ai-product-extension",
            "bigdata-anti-single-database-table": "bigdata-product-extension",
            "bigdata-anti-single-table-without-pipeline": "bigdata-product-extension",
            "iot-anti-cloud-device-api": "iot-embedded-extension",
            "iot-anti-cloud-only-no-firmware-physical": "iot-embedded-extension",
            "iot-anti-cloud-network-protocol-timing": "iot-embedded-extension",
            "low-level-anti-rust-business-service": "low-level-systems-extension",
            "mobile-anti-responsive-pwa": "android-platform-extension",
            "payment-anti-authorization-copy": "payment-trading-extension",
            "payment-anti-order-copy": "payment-trading-extension",
            "payment-anti-order-display-unchanged-state": "payment-trading-extension",
            "web3-anti-hash-signature": "web3-product-extension",
            "web3-anti-payment-wallet-recovery": "web3-product-extension",
        }
        for case_id, domain in positive_domain_cases.items():
            with self.subTest(positive_domain_case=case_id):
                self.assertIn(
                    domain,
                    route_by_id[case_id]["expected"]["layer3_skills"],
                )
        for case_id, domain in negative_domain_cases.items():
            with self.subTest(negative_domain_case=case_id):
                self.assertIn(domain, exclusions[case_id])
        family_variants: dict[tuple[str, str], set[str]] = {}
        domain_anti_count = 0
        domain_transition_count = 0
        domain_unchanged_count = 0
        for item in routes:
            domain_anti_count += bool(item.get("domain_anti"))
            domain_transition_count += bool(item.get("domain_transition"))
            domain_unchanged_count += (
                item.get("domain_anti_variant") == "unchanged-paraphrase"
            )
            family = item.get("domain_family")
            if not family:
                continue
            key = (family["domain"], family["family"])
            family_variants.setdefault(key, set()).add(family["variant"])
            self.assertIn(family["domain"], item["expected"]["layer3_skills"])
            self.assertNotIn(family["domain"], item["prompt"])
        self.assertEqual(26, domain_anti_count)
        self.assertEqual(13, domain_transition_count)
        self.assertEqual(14, domain_unchanged_count)
        self.assertEqual(21, len(family_variants))
        self.assertTrue(
            all(
                variants == {"canonical", "paraphrase"}
                for variants in family_variants.values()
            )
        )
        lifecycle = next(
            item
            for item in routes
            if item["id"] == "security-credential-session-lifecycle-change"
        )
        self.assertEqual(
            {
                "path": "analyzed",
                "profile": "analysis-agent",
                "primary_skill": "security-privacy-gate",
                "layer3_skills": ["authentication-security"],
                "review_skill": "security-privacy-gate",
            },
            lifecycle["expected"],
        )
        trajectory = json.loads((ROOT / "evals/agent-light-trajectories/cases.yaml").read_text())
        self.assertEqual(13, len(trajectory["cases"]))
        self.assertEqual(
            ["shared-workspace-serial-write"],
            [item["id"] for item in trajectory["scheduling_cases"]],
        )
        self.assertEqual(2, len(trajectory["utility_cases"]))
        ids = {item["id"] for item in trajectory["cases"]}
        self.assertTrue(
            {
                "single-file-bug-fix",
                "isolated-write-parallel-contract",
                "repair-and-rereview",
                "api-contract-change",
                "data-migration",
                "security-ssrf-boundary",
                "cache-stampede-reliability",
                "release-rollback",
                "source-backed-payment-retry-proof",
                "module-boundary-benchmark-review",
            }.issubset(ids)
        )
        fixture_text = json.dumps(trajectory).casefold()
        self.assertNotIn("control_state", fixture_text)
        self.assertNotIn("runtime_id", fixture_text)
        by_id = {item["id"]: item for item in trajectory["cases"]}
        def dispatch_shape(case_id: str) -> list[tuple[str, str, list[str]]]:
            return [
                (
                    step["profile"],
                    step["primary_skill"],
                    step["layer3_skills"],
                )
                for step in by_id[case_id]["steps"]
                if step.get("action") == "dispatch"
            ]

        self.assertEqual(
            [
                ("task-agent", "integration-change-builder", ["contract-testing"]),
                ("task-agent", "integration-change-builder", ["contract-testing"]),
                ("task-agent", "integration-change-builder", ["contract-testing"]),
                ("review-agent", "ai-code-review-refactor", []),
            ],
            dispatch_shape("isolated-write-parallel-contract"),
        )
        isolated = json.dumps(
            by_id["isolated-write-parallel-contract"]
        ).casefold()
        self.assertIn("accepted, artifact-reviewed authoritative task dag", isolated)
        self.assertNotIn('"actor": "analysis-agent"', isolated)
        self.assertNotIn('"action": "search"', isolated)
        self.assertNotIn('"action": "first_executable_slice"', isolated)

        ssrf = json.dumps(by_id["security-ssrf-boundary"]).casefold()
        self.assertIn("url fetch", ssrf)
        self.assertIn("threat-modeling", ssrf)
        self.assertIn("web-security", ssrf)
        self.assertNotIn("ai-product-extension", ssrf)
        self.assertNotIn("permission-boundary-modeling", ssrf)
        self.assertEqual(
            [
                (
                    "analysis-agent",
                    "engineering-change-analysis",
                    ["threat-modeling", "web-security"],
                ),
                (
                    "task-agent",
                    "security-privacy-gate",
                    ["threat-modeling", "web-security"],
                ),
                ("review-agent", "security-privacy-gate", []),
            ],
            dispatch_shape("security-ssrf-boundary"),
        )
        scheduling_by_id = {
            item["id"]: item for item in trajectory["scheduling_cases"]
        }
        shared = scheduling_by_id["shared-workspace-serial-write"]
        rag = json.dumps(shared).casefold()
        for phrase in (
            "rag retriever-to-model-context",
            "ai-product-extension",
            "permission-boundary-modeling",
            "security-privacy-gate",
            "tenant and object permission filters",
            "before prompt context assembly",
            "revoked-access",
        ):
            self.assertIn(phrase, rag)
        shared_b = next(
            step
            for step in shared["steps"]
            if step.get("action") == "dispatch"
            and step.get("task_id") == "task-shared-workspace-serial-write-2"
        )
        self.assertEqual("security-privacy-gate", shared_b["primary_skill"])
        self.assertEqual(
            ["permission-boundary-modeling", "ai-product-extension"],
            shared_b["layer3_skills"],
        )
        shared_review = next(
            step
            for step in shared["steps"]
            if step.get("action") == "dispatch"
            and step.get("profile") == "review-agent"
        )
        self.assertEqual(
            "security-privacy-gate",
            shared_review["primary_skill"],
        )
        cache = json.dumps(by_id["cache-stampede-reliability"]).casefold()
        for phrase in (
            "single-flight",
            "degradation",
            "hot-key",
            "concurrency-control",
            "degradation-circuit-breaking",
            "observability",
        ):
            self.assertIn(phrase, cache)
        self.assertEqual(
            [
                (
                    "analysis-agent",
                    "engineering-change-analysis",
                    [
                        "concurrency-control",
                        "degradation-circuit-breaking",
                        "observability",
                    ],
                ),
                (
                    "task-agent",
                    "reliability-observability-gate",
                    [
                        "concurrency-control",
                        "degradation-circuit-breaking",
                        "observability",
                    ],
                ),
                ("review-agent", "reliability-observability-gate", []),
            ],
            dispatch_shape("cache-stampede-reliability"),
        )
        for forbidden in (
            "private evidence storage",
            "private evidence ledger",
            "hidden protocol record",
            "hidden state ledger",
        ):
            self.assertNotIn(forbidden, cache)
        self.assertIn('"ledger_source_kind"', cache)

if __name__ == "__main__":
    unittest.main()
