from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build
from validation_utils import (
    REFERENCE_OUTPUTS_BY_TYPE,
    ValidationProblem,
    ai_markdown_list_sentence_counts,
    ai_readability_findings,
    load_yaml_file,
    parse_frontmatter,
    reference_contract_has_owner_anchor,
    reference_contracts,
    registry_targeted_reference_projection_line_count,
    render_targeted_reference_section,
    strip_registry_targeted_reference_projection,
)


def _load_script(module_name: str, filename: str):
    spec = importlib.util.spec_from_file_location(module_name, SCRIPTS / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


AUDIT = _load_script("reference_registry_jit_audit", "audit-skill-content.py")
REFERENCE_VALIDATOR = _load_script(
    "reference_registry_jit_validator", "validate-reference-content.py"
)
DOMAIN_VALIDATOR = _load_script(
    "reference_registry_jit_domain_validator", "validate-domain-extensions.py"
)


def _foundation_readability_violations(
    markdown: str,
    context: str,
) -> list[tuple[str, int]]:
    findings = ai_readability_findings(markdown, context)
    violations = [
        (str(finding["band"]), int(finding["line"]))
        for finding in findings
        if finding.get("band") in {"tighten", "hard-fail"}
    ]
    violations.extend(
        ("compound", int(finding["line"]))
        for finding in findings
        if finding["kind"] == "bullet-decisions"
    )
    return violations


def _foundation_targeted_or_template_violations(
    markdown: str,
    context: str,
    reference_type: str,
) -> list[tuple[str, int]]:
    if reference_type not in {"targeted", "template"}:
        raise ValueError("reference_type must be targeted or template")
    violations = _foundation_readability_violations(markdown, context)
    line_count = len(markdown.splitlines())
    if (
        reference_type == "targeted"
        and line_count > REFERENCE_VALIDATOR.TARGETED_LINE_LIMIT
    ):
        violations.append(("line-budget", line_count))
    return violations


def _reference_semantic_units(markdown: str) -> list[str]:
    return [
        " ".join(piece.strip() for piece, _line in unit["pieces"]).casefold()
        for unit in AUDIT._semantic_logical_units(
            markdown,
            include_negative_examples=True,
        )
    ]


def _assert_unique_contiguous_semantic_window(
    test_case: unittest.TestCase,
    units: list[str],
    terms: tuple[str, ...],
    *,
    window_size: int,
) -> None:
    expected = tuple(term.casefold() for term in terms)

    def matching_windows(source_units: list[str]) -> list[list[str]]:
        windows = (
            source_units[start : start + window_size]
            for start in range(len(source_units) - window_size + 1)
        )
        return [
            window
            for window in windows
            if all(any(term in unit for unit in window) for term in expected)
            and all(any(term in unit for term in expected) for unit in window)
        ]

    test_case.assertEqual(1, len(matching_windows(units)))
    missing_anchor = [unit.replace(expected[0], "", 1) for unit in units]
    test_case.assertEqual(0, len(matching_windows(missing_anchor)))


def _foundation_checklist_violations(
    markdown: str,
    context: str,
) -> list[tuple[str, int]]:
    violations = _foundation_readability_violations(markdown, context)
    facts = AUDIT._markdown_structural_facts(markdown, "decision-checklist")
    line_count = len(markdown.splitlines())
    if line_count > REFERENCE_VALIDATOR.TARGETED_LINE_LIMIT:
        violations.append(("line-budget", line_count))
    item_count = int(facts["max_decision_section_item_count"])
    if item_count > REFERENCE_VALIDATOR.DECISION_ITEM_LIMIT:
        violations.append(("decision-items", item_count))
    invalid_headings = list(facts["invalid_decision_section_headings"])
    if invalid_headings:
        violations.append(("decision-section-heading", len(invalid_headings)))
    return violations


def _foundation_evidence_pattern_violations(
    markdown: str,
    context: str,
) -> list[tuple[str, int]]:
    violations = _foundation_readability_violations(markdown, context)
    line_count = len(markdown.splitlines())
    if line_count > REFERENCE_VALIDATOR.TARGETED_LINE_LIMIT:
        violations.append(("line-budget", line_count))
    return violations


def _foundation_benchmark_pattern_violations(
    markdown: str,
    context: str,
) -> list[tuple[str, int]]:
    violations = _foundation_readability_violations(markdown, context)
    line_count = len(markdown.splitlines())
    if line_count > REFERENCE_VALIDATOR.TARGETED_LINE_LIMIT:
        violations.append(("line-budget", line_count))
    return violations


def _professional_reference_violations(
    markdown: str,
    context: str,
) -> list[tuple[str, int]]:
    violations = _foundation_readability_violations(markdown, context)
    line_count = len(markdown.splitlines())
    if line_count > REFERENCE_VALIDATOR.TARGETED_LINE_LIMIT:
        violations.append(("line-budget", line_count))
    return violations


class ReferenceRegistryJitTest(unittest.TestCase):
    def test_all_registry_projections_have_no_readability_blockers(self) -> None:
        specs = (
            ("control-skills.yaml", "control_skills", False),
            ("professional-skills.yaml", "professional_skills", False),
            ("foundation-skills.yaml", "foundation_skills", True),
            ("domain-skills.yaml", "domain_skills", True),
        )
        contract_count = 0
        layer3_projection_count = 0
        blockers: list[dict[str, object]] = []
        for filename, key, is_layer3 in specs:
            registry = load_yaml_file(ROOT / "src" / "registry" / filename)
            for entry in registry[key]:
                contracts = reference_contracts(
                    entry["reference_index"],
                    f"{filename}:{entry['name']}.reference_index",
                    owner=entry["name"],
                )
                contract_count += len(contracts)
                layer3_projection_count += int(is_layer3)
                projection = render_targeted_reference_section(
                    "## Targeted References\n\n- stale projection\n",
                    contracts,
                    entry["name"],
                )
                blockers.extend(
                    finding
                    for finding in ai_readability_findings(
                        projection,
                        f"{filename}:{entry['name']}",
                    )
                    if finding["severity"] == "error"
                )

        self.assertEqual(525, contract_count)
        self.assertEqual(163, layer3_projection_count)
        self.assertEqual([], blockers)

    def test_all_source_targeted_reference_sections_match_registry_projection(self) -> None:
        specs = (
            ("control-skills.yaml", "control_skills"),
            ("professional-skills.yaml", "professional_skills"),
            ("foundation-skills.yaml", "foundation_skills"),
            ("domain-skills.yaml", "domain_skills"),
        )
        checked = 0
        for filename, key in specs:
            registry = load_yaml_file(ROOT / "src" / "registry" / filename)
            for entry in registry[key]:
                source_path = ROOT / entry["path"] / "SKILL.md"
                source = source_path.read_text(encoding="utf-8")
                contracts = reference_contracts(
                    entry["reference_index"],
                    f"{filename}:{entry['name']}.reference_index",
                    owner=entry["name"],
                )
                self.assertEqual(
                    source,
                    render_targeted_reference_section(
                        source, contracts, entry["name"]
                    ),
                    source_path,
                )
                checked += 1
        self.assertEqual(190, checked)

    def test_all_indexed_references_have_effective_registry_contracts(self) -> None:
        specs = (
            ("control-skills.yaml", "control_skills"),
            ("professional-skills.yaml", "professional_skills"),
            ("foundation-skills.yaml", "foundation_skills"),
            ("domain-skills.yaml", "domain_skills"),
        )
        total = 0
        for filename, key in specs:
            registry = load_yaml_file(ROOT / "src" / "registry" / filename)
            expected_schema = {
                "control-skills.yaml": 3,
                "professional-skills.yaml": 5,
                "foundation-skills.yaml": 8,
                "domain-skills.yaml": 6,
            }[filename]
            self.assertEqual(expected_schema, registry["schema_version"])
            for entry in registry[key]:
                total += len(
                    reference_contracts(
                        entry["reference_index"],
                        f"{filename}:{entry['name']}.reference_index",
                        owner=entry["name"],
                    )
                )
        self.assertEqual(525, total)

        original_counter = AUDIT.count_o200k_base_tokens
        AUDIT.count_o200k_base_tokens = lambda _text: 0
        try:
            content = AUDIT._collect_reference_content()
        finally:
            AUDIT.count_o200k_base_tokens = original_counter
        summary = content["summary"]
        self.assertEqual(525, summary["indexed_reference_entries"])
        for field in (
            "missing_effective_reference_types",
            "missing_effective_load_when",
            "missing_effective_do_not_load_when",
            "effective_preface_conflicts",
            "effective_preface_contract_errors",
            "effective_preface_invalid",
        ):
            self.assertEqual(0, summary[field], field)

        counts, errors = REFERENCE_VALIDATOR._effective_preface_contract(content)
        self.assertEqual([], errors)
        self.assertEqual(525, counts["effective_reference_types"])
        self.assertEqual(525, counts["effective_load_when"])
        self.assertEqual(525, counts["effective_do_not_load_when"])

        cache_checklist = next(
            item
            for item in content["references"]
            if item["owner"] == "cache-design"
            and item["path"].endswith("/references/checklist.md")
        )
        registry_path = ROOT / "src/registry/foundation-skills.yaml"
        registry_lines = registry_path.read_text(encoding="utf-8").splitlines()
        for field, registry_field in (
            ("reference_type", "type"),
            ("load_when", "load_when"),
            ("do_not_load_when", "do_not_load_when"),
        ):
            evidence = next(
                row
                for row in cache_checklist["effective_preface"][field]["evidence"]
                if row["source"] == "reference-index"
            )
            self.assertGreater(evidence["line"], 1)
            self.assertIn(
                f"{registry_field}:", registry_lines[evidence["line"] - 1]
            )
            self.assertIn(evidence["value"], registry_lines[evidence["line"] - 1])

    def test_cache_design_contract_renders_structured_jit_instructions(self) -> None:
        registry = load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
        entry = next(
            item for item in registry["foundation_skills"]
            if item["name"] == "cache-design"
        )
        contracts = reference_contracts(
            entry["reference_index"],
            "cache-design.reference_index",
            owner="cache-design",
        )
        source = (ROOT / entry["path"] / "SKILL.md").read_text(encoding="utf-8")
        rendered = build._render_targeted_reference_section(
            source, contracts, "cache-design"
        )
        section = rendered.split("## Targeted References", 1)[1]
        checklist = next(
            contract
            for contract in contracts
            if contract["path"] == "references/checklist.md"
        )
        self.assertIn(
            "| [checklist](references/checklist.md) | decision-checklist | "
            f"{checklist['load_when'].rstrip(' .')} | "
            f"{checklist['do_not_load_when'].rstrip(' .')} | "
            f"{', '.join(checklist['required_by'])} | "
            f"{', '.join(checklist['required_output'])} |",
            section,
        )
        self.assertIn(
            "[benchmarks and patterns](references/benchmarks-and-patterns.md)",
            section,
        )
        self.assertIn(
            "[evidence patterns](references/evidence-patterns.md)", section
        )
        self.assertNotIn("- [checklist.md](references/checklist.md)\n", section)
        projected_paths = [
            line.split("](", 1)[1].split(")", 1)[0]
            for line in section.splitlines()
            if line.startswith("| [")
        ]
        self.assertEqual(
            [contract["path"] for contract in contracts],
            projected_paths,
        )

    def test_implementation_structure_references_keep_targeted_decision_contract(
        self,
    ) -> None:
        foundation = load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
        entry = next(
            item
            for item in foundation["foundation_skills"]
            if item["name"] == "implementation-structure-design"
        )
        contracts = reference_contracts(
            entry["reference_index"],
            "implementation-structure-design.reference_index",
            owner="implementation-structure-design",
        )
        self.assertEqual(
            [
                "references/object-module-decomposition.md",
                "references/reuse-and-placement.md",
                "references/evidence-patterns.md",
            ],
            [contract["path"] for contract in contracts],
        )
        decomposition = contracts[0]
        self.assertEqual("targeted", decomposition["type"])
        self.assertEqual(
            [
                "decision-record",
                "validation-plan",
                "proof-limit",
                "residual-risk",
            ],
            decomposition["required_output"],
        )
        reuse = contracts[1]
        self.assertEqual("targeted", reuse["type"])
        self.assertEqual(
            [
                "selected-approach",
                "validation-plan",
                "proof-limit",
                "residual-risk",
            ],
            reuse["required_output"],
        )
        evidence = contracts[2]
        self.assertEqual("evidence-pattern", evidence["type"])
        self.assertEqual(
            [
                "evidence-record",
                "validation-plan",
                "proof-limit",
                "residual-risk",
            ],
            evidence["required_output"],
        )

        root = ROOT / entry["path"]
        source = (root / "SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(
            source,
            render_targeted_reference_section(
                source,
                contracts,
                "implementation-structure-design",
            ),
        )
        indexed_paths = {contract["path"] for contract in contracts}
        physical_paths = {
            path.relative_to(root).as_posix()
            for path in (root / "references").glob("*.md")
        }
        self.assertEqual(indexed_paths, physical_paths)
        self.assertTrue(all((root / path).is_file() for path in indexed_paths))

        self.assertEqual(
            frozenset(
                {
                    "boundary-decision",
                    "decision-record",
                    "failure-decision",
                    "gate-decision",
                    "release-decision",
                    "routing-decision",
                    "selected-approach",
                    "validation-plan",
                    "evidence-gap",
                    "proof-limit",
                    "residual-risk",
                }
            ),
            REFERENCE_OUTPUTS_BY_TYPE["targeted"],
        )
        self.assertNotIn("checklist-result", REFERENCE_OUTPUTS_BY_TYPE["targeted"])

        expected_consumers = {
            "architecture-impact-reviewer",
            "backend-change-builder",
            "repository-tooling-change-builder",
            "ai-code-review-refactor",
        }
        self.assertEqual(expected_consumers, set(entry["used_by"]))
        professional = load_yaml_file(
            ROOT / "src/registry/professional-skills.yaml"
        )
        actual_consumers = {
            item["name"]
            for item in professional["professional_skills"]
            if "implementation-structure-design"
            in item.get("layer3_candidates", [])
        }
        self.assertEqual(expected_consumers, actual_consumers)

    def test_structure_responsibility_consumer_matrix_is_reciprocal_and_role_valid(
        self,
    ) -> None:
        expected = {
            "domain-object-identification": {
                "domain-impact-modeler",
                "backend-change-builder",
                "ai-code-review-refactor",
            },
            "design-pattern-selection": {
                "architecture-impact-reviewer",
                "backend-change-builder",
                "repository-tooling-change-builder",
                "ai-code-review-refactor",
            },
            "minimal-correct-implementation": {
                "engineering-change-analysis",
                "backend-change-builder",
                "repository-tooling-change-builder",
                "ai-code-review-refactor",
            },
            "implementation-structure-design": {
                "architecture-impact-reviewer",
                "backend-change-builder",
                "repository-tooling-change-builder",
                "ai-code-review-refactor",
            },
            "module-boundary-design": {
                "architecture-impact-reviewer",
                "high-risk-design-review",
            },
            "refactoring": {
                "engineering-change-analysis",
                "ai-code-review-refactor",
            },
        }
        foundation = load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
        professional = load_yaml_file(ROOT / "src/registry/professional-skills.yaml")
        foundation_by_name = {
            item["name"]: item for item in foundation["foundation_skills"]
        }
        professional_by_name = {
            item["name"]: item for item in professional["professional_skills"]
        }
        for capability, expected_consumers in expected.items():
            with self.subTest(capability=capability):
                self.assertEqual(
                    expected_consumers,
                    set(foundation_by_name[capability]["used_by"]),
                )
                actual_consumers = {
                    name
                    for name, item in professional_by_name.items()
                    if capability in item.get("layer3_candidates", [])
                }
                self.assertEqual(expected_consumers, actual_consumers)
                capability_roles = set(
                    foundation_by_name[capability]["role_support"]
                )
                consumer_role_union = set().union(
                    *(
                        set(professional_by_name[consumer]["role_support"])
                        for consumer in expected_consumers
                    )
                )
                self.assertTrue(
                    capability_roles.issubset(consumer_role_union),
                    (capability, sorted(capability_roles - consumer_role_union)),
                )
                for consumer in expected_consumers:
                    self.assertTrue(
                        capability_roles.intersection(
                            professional_by_name[consumer]["role_support"]
                        ),
                        (capability, consumer),
                    )

    def test_engineering_change_analysis_ownership_projection_is_exact(self) -> None:
        removed = {
            "requirement-clarification",
            "acceptance-standard-definition",
            "interaction-state-modeling",
            "design-system-rules",
            "business-rule-extraction",
            "state-machine-modeling",
            "task-dag-decomposition",
            "module-boundary-design",
            "architecture-tradeoff-analysis",
            "test-data-management",
            "authentication-authorization",
            "contract-testing",
        }
        foundation = load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
        domain = load_yaml_file(ROOT / "src/registry/domain-skills.yaml")
        professional = load_yaml_file(ROOT / "src/registry/professional-skills.yaml")
        foundation_by_name = {
            item["name"]: item for item in foundation["foundation_skills"]
        }
        eca = next(
            item
            for item in professional["professional_skills"]
            if item["name"] == "engineering-change-analysis"
        )
        candidates = set(eca["layer3_candidates"])
        domain_names = {item["name"] for item in domain["domain_skills"]}
        product_foundation_names = {
            item["name"]
            for item in foundation["foundation_skills"]
            if item["delivery_scope"] == "product"
        }

        self.assertEqual(37, len(candidates))
        self.assertTrue(removed.isdisjoint(candidates))
        self.assertIn("configuration-runtime-policy", candidates)
        self.assertIn("dependency-vulnerability-scanning", candidates)
        self.assertIn("test-strategy", candidates)
        self.assertEqual(domain_names, candidates & domain_names)
        for capability in removed:
            with self.subTest(capability=capability):
                self.assertNotIn(
                    "engineering-change-analysis",
                    foundation_by_name[capability]["used_by"],
                )

        professional_item = SimpleNamespace(registry=eca)
        for profile in ("recommended", "full", "dev"):
            with self.subTest(profile=profile):
                compiled = set(
                    build._compiled_layer3_names(
                        profile,
                        professional_item,
                        domain_names,
                        product_foundation_names,
                    )
                )
                self.assertTrue(removed.isdisjoint(compiled))
                if profile != "dev":
                    self.assertIn("test-strategy", compiled)
                if profile == "recommended":
                    self.assertTrue(domain_names.issubset(compiled))
                elif profile == "full":
                    self.assertTrue(domain_names.isdisjoint(compiled))
                else:
                    self.assertEqual(set(), compiled)

    def test_scenario_decomposition_contract_and_jit_owner_are_exact(self) -> None:
        expected_output_contract = [
            "primary scenario with trigger, pre-state, decision, observable "
            "postcondition, acceptance mapping, traceable oracle, and proof limits",
            "applicable task-local failure, abuse, recovery, and operational "
            "paths only",
            "considered-but-excluded task-local category with cited omission "
            "or non-applicability rationale",
            "residual scenario-risk owners",
        ]
        foundation = load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
        professional = load_yaml_file(
            ROOT / "src/registry/professional-skills.yaml"
        )
        domain = load_yaml_file(ROOT / "src/registry/domain-skills.yaml")
        scenario = next(
            item
            for item in foundation["foundation_skills"]
            if item["name"] == "scenario-decomposition"
        )
        professional_by_name = {
            item["name"]: item for item in professional["professional_skills"]
        }
        actual_consumers = {
            name
            for name, item in professional_by_name.items()
            if "scenario-decomposition"
            in item.get("layer3_candidates", [])
        }

        self.assertEqual(expected_output_contract, scenario["output_contract"])
        self.assertEqual(
            ["acceptance-criteria-builder"],
            scenario["used_by"],
        )
        self.assertEqual(
            {"acceptance-criteria-builder"},
            actual_consumers,
        )

        root_text = (
            ROOT
            / "src/foundation/capabilities/scenario-decomposition/SKILL.md"
        ).read_text(encoding="utf-8")
        output_section = root_text.split("## Output Contract\n\n", 1)[1].split(
            "\n\n## Targeted References",
            1,
        )[0]
        root_output_contract = [
            line.removeprefix("- ")
            for line in output_section.splitlines()
            if line.startswith("- ")
        ]
        self.assertEqual(expected_output_contract, root_output_contract)

        domain_names = {
            item["name"] for item in domain["domain_skills"]
        }
        product_foundation_names = {
            item["name"]
            for item in foundation["foundation_skills"]
            if item["delivery_scope"] == "product"
        }
        for profile, expected in (
            ("recommended", True),
            ("full", True),
            ("dev", False),
        ):
            with self.subTest(profile=profile):
                acceptance_compiled = set(
                    build._compiled_layer3_names(
                        profile,
                        SimpleNamespace(
                            registry=professional_by_name[
                                "acceptance-criteria-builder"
                            ]
                        ),
                        domain_names,
                        product_foundation_names,
                    )
                )
                eca_compiled = set(
                    build._compiled_layer3_names(
                        profile,
                        SimpleNamespace(
                            registry=professional_by_name[
                                "engineering-change-analysis"
                            ]
                        ),
                        domain_names,
                        product_foundation_names,
                    )
                )
                self.assertEqual(
                    expected,
                    "scenario-decomposition" in acceptance_compiled,
                )
                self.assertNotIn("scenario-decomposition", eca_compiled)

    def test_module_boundary_roles_and_backend_escalation_are_exact(self) -> None:
        foundation = load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
        professional = load_yaml_file(
            ROOT / "src/registry/professional-skills.yaml"
        )
        module = next(
            item
            for item in foundation["foundation_skills"]
            if item["name"] == "module-boundary-design"
        )
        expected_roles = ["analysis-agent", "review-agent"]
        self.assertEqual(expected_roles, module["role_support"])
        self.assertEqual(
            {"architecture-impact-reviewer", "high-risk-design-review"},
            set(module["used_by"]),
        )
        for reference in module["reference_index"]:
            with self.subTest(reference=reference["path"]):
                self.assertEqual(expected_roles, reference["required_by"])

        backend = next(
            item
            for item in professional["professional_skills"]
            if item["name"] == "backend-change-builder"
        )
        self.assertIn(
            "implementation-structure-design",
            backend["layer3_candidates"],
        )
        self.assertNotIn("module-boundary-design", backend["layer3_candidates"])
        proactive = (
            ROOT
            / "src/professional-skills/backend-change-builder/references/"
            "proactive-triggers.md"
        ).read_text(encoding="utf-8")
        for phrase in (
            "Owner-internal placement stays with `implementation-structure-design`.",
            "If module ownership, public surface, or dependency direction changes, stop implementation.",
            "Route Analyzed Work to `architecture-impact-reviewer` with `module-boundary-design`.",
        ):
            self.assertIn(phrase, proactive)

    def test_structure_responsibility_content_contracts_are_complete(self) -> None:
        domain_root = (
            ROOT / "src/foundation/capabilities/domain-object-identification"
        )
        domain_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                domain_root / "SKILL.md",
                domain_root / "examples/example-output.md",
                domain_root / "references/benchmarks-and-patterns.md",
                domain_root / "references/checklist.md",
                domain_root / "references/evidence-patterns.md",
            )
        ).casefold()
        for phrase in (
            "no independent identity",
            "immutable",
            "replacement semantics",
            "aggregate root",
            "invariant entry point",
            "writer authority",
            "rejected alternatives",
            "proof limits",
            "residual risks",
            "microsoft",
            "oracle",
            "java equality",
        ):
            self.assertIn(phrase, domain_text)

        implementation_root = (
            ROOT / "src/foundation/capabilities/implementation-structure-design"
        )
        implementation_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                implementation_root / "SKILL.md",
                implementation_root / "references/object-module-decomposition.md",
                implementation_root / "references/reuse-and-placement.md",
                implementation_root / "references/evidence-patterns.md",
            )
        ).casefold()
        for phrase in (
            "owner-private new structure",
            "deliberate separate implementation",
            "drift",
            "delete condition",
            "editable source",
            "generator/template/config",
            "committed/derived policy",
            "semantic diff",
            "mechanical diff",
            "unknown authority",
            "repository-context-map",
            "build-tool-professional-usage",
            "bazel",
            "proof limits",
        ):
            self.assertIn(phrase, implementation_text)

        module_root = ROOT / "src/foundation/capabilities/module-boundary-design"
        module_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                module_root / "SKILL.md",
                module_root / "references/module-decomposition.md",
                module_root / "references/benchmarks-and-enforcement.md",
            )
        ).casefold()
        for phrase in (
            "boundary-kind",
            "plain directory",
            "language package/module",
            "build target/package",
            "distributable sdk/library",
            "runtime/service",
            "authoritative mechanism",
            "enforcement owner",
            "go",
            "bazel",
            "directory name",
            "proof limits",
        ):
            self.assertIn(phrase, module_text)

    def test_structure_codegen_cases_name_required_layer3_decisions(self) -> None:
        expected = {
            "complexity-delete-list-review": {
                "minimal-correct-implementation",
            },
            "design-pattern-overengineering": {
                "design-pattern-selection",
                "minimal-correct-implementation",
                "implementation-structure-design",
            },
            "object-method-encapsulation-placement": {
                "domain-object-identification",
                "implementation-structure-design",
            },
            "observer-lifecycle-backpressure": {
                "design-pattern-selection",
                "concurrency-control",
                "implementation-structure-design",
            },
            "over-fragmented-file-split": {
                "minimal-correct-implementation",
                "implementation-structure-design",
            },
            "oversized-service-object-split": {
                "domain-object-identification",
                "implementation-structure-design",
            },
            "parent-child-sibling-object-relationship": {
                "domain-object-identification",
                "design-pattern-selection",
                "implementation-structure-design",
            },
            "pattern-selection-with-real-variation": {
                "design-pattern-selection",
                "implementation-structure-design",
                "payment-trading-extension",
            },
        }
        professional = load_yaml_file(ROOT / "src/registry/professional-skills.yaml")
        candidates = {
            item["name"]: set(item.get("layer3_candidates", []))
            for item in professional["professional_skills"]
        }
        foundation = load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
        domain = load_yaml_file(ROOT / "src/registry/domain-skills.yaml")
        roles = {
            item["name"]: set(item.get("role_support", []))
            for item in (
                foundation["foundation_skills"] + domain["domain_skills"]
            )
        }
        for case_id, expected_layer3 in expected.items():
            with self.subTest(case_id=case_id):
                path = (
                    ROOT
                    / "evals/codegen/structure"
                    / case_id
                    / "expected-qualities.yaml"
                )
                payload = load_yaml_file(path)
                route_hints = payload["route_hints"]
                actual_layer3 = set(route_hints["layer3_skills"])
                self.assertEqual(expected_layer3, actual_layer3)
                self.assertLessEqual(len(actual_layer3), 3)
                primary = route_hints["primary_skill"]
                self.assertTrue(expected_layer3.issubset(candidates[primary]))
                for capability in expected_layer3:
                    self.assertIn(
                        route_hints["agent_profile"],
                        roles[capability],
                        (case_id, capability),
                    )

    def test_legacy_string_reference_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValidationProblem, "legacy string"):
            reference_contracts(
                ["references/checklist.md"],
                "sample.reference_index",
                owner="sample",
            )

    def test_reference_v2_rejects_missing_empty_and_unknown_consumption_fields(self) -> None:
        base = {
            "path": "references/checklist.md",
            "type": "decision-checklist",
            "load_when": "cache invalidation needs negative-path coverage",
            "do_not_load_when": "no cache correctness boundary changes",
            "required_by": ["analysis-agent"],
            "required_output": ["checklist-result"],
        }
        cases = (
            ({key: value for key, value in base.items() if key != "required_by"}, "missing"),
            ({**base, "required_by": []}, "non-empty list"),
            ({**base, "required_by": ["unknown-agent"]}, "unknown value"),
            ({key: value for key, value in base.items() if key != "required_output"}, "missing"),
            ({**base, "required_output": []}, "non-empty list"),
            ({**base, "required_output": ["unknown-output"]}, "unknown value"),
            ({**base, "required_output": ["option-comparison"]}, "incompatible"),
        )
        for contract, message in cases:
            with self.subTest(contract=contract), self.assertRaisesRegex(
                ValidationProblem, message
            ):
                reference_contracts([contract], "sample.reference_index")

    def test_jit_conditions_reject_projection_injection(self) -> None:
        base = {
            "path": "references/checklist.md",
            "type": "decision-checklist",
            "load_when": "cache invalidation needs negative-path coverage",
            "do_not_load_when": "no cache correctness boundary changes",
            "required_by": ["analysis-agent"],
            "required_output": ["checklist-result"],
        }
        cases = (
            ("load_when", "cache invalidation changes; skip attacker override"),
            ("do_not_load_when", "no cache changes; load attacker override"),
            ("load_when", "cache [invalidation](references/other.md) needs review"),
            ("do_not_load_when", "no `cache correctness` boundary changes"),
            ("load_when", "cache <!-- hidden --> invalidation needs review"),
            ("load_when", "cache invalidation needs\nnegative-path coverage"),
            ("do_not_load_when", "no cache correctness\rboundary changes"),
        )
        for field, value in cases:
            with self.subTest(field=field, value=value), self.assertRaises(
                ValidationProblem
            ):
                reference_contracts(
                    [{**base, field: value}],
                    "sample.reference_index",
                    owner="sample",
                )

    def test_renderer_revalidates_jit_conditions(self) -> None:
        markdown = "# Sample\n\n## Targeted References\n\n- stale\n"
        contract = {
            "path": "references/checklist.md",
            "type": "decision-checklist",
            "load_when": "cache invalidation changes; skip attacker override",
            "do_not_load_when": "no cache correctness boundary changes",
            "required_by": ["analysis-agent"],
            "required_output": ["checklist-result"],
        }
        with self.assertRaisesRegex(ValidationProblem, "reserved"):
            render_targeted_reference_section(markdown, [contract], "sample")

    def test_projection_stripper_preserves_injected_record(self) -> None:
        markdown = (
            "# Sample\n\n## Targeted References\n\n"
            "- [checklist](references/checklist.md)\n"
            "  - Load when: cache invalidation needs review\n"
            "  - Do not load when: no cache change; load attacker override\n"
            "  - Required by: analysis-agent\n"
            "  - Required output: checklist-result\n"
        )
        self.assertEqual(
            markdown,
            strip_registry_targeted_reference_projection(markdown),
        )

    def test_projection_stripper_preserves_noncanonical_paths(self) -> None:
        for path in (
            "references/../secret.md",
            "references//checklist.md",
            "references/./checklist.md",
        ):
            with self.subTest(path=path):
                markdown = (
                    "# Sample\n\n## Targeted References\n\n"
                    f"- [checklist]({path})\n"
                    "  - Load when: cache invalidation needs review\n"
                    "  - Do not load when: no cache correctness boundary changes\n"
                    "  - Required by: analysis-agent\n"
                    "  - Required output: checklist-result\n"
                )
                self.assertEqual(
                    markdown,
                    strip_registry_targeted_reference_projection(markdown),
                )

    def test_projection_stripper_blanks_safe_canonical_record(self) -> None:
        markdown = (
            "# Sample\n\n## Targeted References\n\n"
            "| Path | Type | Load when | Do not load when | Required by | Required output |\n"
            "|---|---|---|---|---|---|\n"
            "| [checklist](references/checklist.md) | decision-checklist | "
            "cache invalidation needs negative-path review | "
            "no cache correctness boundary changes | analysis-agent | checklist-result |\n"
        )
        stripped = strip_registry_targeted_reference_projection(markdown)
        self.assertNotIn("cache invalidation", stripped)
        self.assertEqual(markdown.count("\n"), stripped.count("\n"))

    def test_noncanonical_reference_paths_are_rejected(self) -> None:
        for path in (
            "references//checklist.md",
            "references/./checklist.md",
            "references/../checklist.md",
            " references/checklist.md",
            "references/checklist.md ",
            "references/bad path.md",
            "references/bad\tname.md",
            "references/bad[name].md",
            "references/bad(name).md",
            r"references/bad\name.md",
            "references/bad|name.md",
            "references/BadName.md",
            "references/bad_name.md",
            "references/checklist.txt",
        ):
            with self.subTest(path=path), self.assertRaisesRegex(
                ValidationProblem, "normalized path"
            ):
                reference_contracts(
                    [
                        {
                            "path": path,
                            "type": "targeted",
                            "load_when": "sample task needs checklist coverage",
                            "do_not_load_when": "sample task has no checklist risk",
                            "required_by": ["analysis-agent"],
                            "required_output": ["decision-record"],
                        }
                    ],
                    "sample.reference_index",
                    owner="sample",
                )

    def test_markdown_safe_nested_reference_path_round_trips(self) -> None:
        contract = {
            "path": "references/security/access-checklist.md",
            "type": "decision-checklist",
            "load_when": "authorization changes need denied-path coverage",
            "do_not_load_when": "no authorization behavior or ownership changes",
            "required_by": ["analysis-agent"],
            "required_output": ["checklist-result"],
        }
        markdown = render_targeted_reference_section(
            "# Sample\n\n## Targeted References\n\n- stale\n",
            [contract],
            "sample",
        )
        self.assertIn(
            "[access](references/security/access-checklist.md)", markdown
        )
        stripped = strip_registry_targeted_reference_projection(markdown)
        self.assertNotEqual(markdown, stripped)
        self.assertNotIn("references/security/access-checklist.md", stripped)

    def test_renderer_emits_exact_contextual_projection_terminators(self) -> None:
        contract = {
            "path": "references/checklist.md",
            "type": "decision-checklist",
            "load_when": "authorization changes need denied-path coverage",
            "do_not_load_when": "no authorization behavior or ownership changes",
            "required_by": ["analysis-agent"],
            "required_output": ["checklist-result"],
        }
        for label, contracts, eof_lines, h2_lines in (
            ("table", [contract], 5, 6),
            ("sentinel", [], 3, 4),
        ):
            with self.subTest(shape=label, position="eof"):
                rendered = render_targeted_reference_section(
                    "# Sample\n\n## Targeted References\n\n- stale",
                    contracts,
                    "sample",
                )
                self.assertTrue(rendered.endswith("\n"))
                self.assertFalse(rendered.endswith("\n\n"))
                self.assertEqual(
                    eof_lines,
                    registry_targeted_reference_projection_line_count(rendered),
                )
                self.assertNotEqual(
                    rendered,
                    strip_registry_targeted_reference_projection(rendered),
                )

            with self.subTest(shape=label, position="before-h2"):
                rendered = render_targeted_reference_section(
                    "# Sample\n\n## Targeted References\n\n- stale\n## Next\n\nDecision.\n",
                    contracts,
                    "sample",
                )
                prefix, suffix = rendered.split("## Next", 1)
                self.assertTrue(prefix.endswith("\n\n"))
                self.assertFalse(prefix.endswith("\n\n\n"))
                self.assertEqual("\n\nDecision.\n", suffix)
                self.assertEqual(
                    h2_lines,
                    registry_targeted_reference_projection_line_count(rendered),
                )
                self.assertNotEqual(
                    rendered,
                    strip_registry_targeted_reference_projection(rendered),
                )

    def test_generic_jit_role_templates_are_rejected(self) -> None:
        base = {
            "path": "references/checklist.md",
            "type": "decision-checklist",
            "load_when": "authorization changes need denied-path coverage",
            "do_not_load_when": "no authorization boundary changes",
            "required_by": ["analysis-agent"],
            "required_output": ["checklist-result"],
        }
        for load_when in (
            "cache closure needs the checklist",
            "cache claims need evidence patterns",
            "cache decisions need benchmarks and patterns",
        ):
            with self.subTest(load_when=load_when), self.assertRaisesRegex(
                ValidationProblem, "forbidden generic role template"
            ):
                reference_contracts(
                    [{**base, "load_when": load_when}], "sample.reference_index"
                )
        with self.assertRaisesRegex(ValidationProblem, "real anti-condition"):
            reference_contracts(
                [
                    {
                        **base,
                        "do_not_load_when": "cache root already closes triggered risks",
                    }
                ],
                "sample.reference_index",
            )

    def test_mechanical_and_malformed_jit_conditions_are_rejected(self) -> None:
        base = {
            "path": "references/checklist.md",
            "type": "decision-checklist",
            "load_when": "cache invalidation failures need denied-path coverage",
            "do_not_load_when": "no cache correctness path is affected",
            "required_by": ["analysis-agent"],
            "required_output": ["checklist-result"],
        }
        cases = (
            "patterns: cache keys leaves mechanism or failure-mode trade-offs",
            "checklist: cache keys needs boundary, failure, or negative-case coverage",
            "evidence: cache keys needs source, freshness, or negative-control proof",
            "no task-local cache decision is or tests cover the risk",
            "cache input missing leaves mechanism unresolved",
            "cache invalidation and needs boundary coverage",
            "evidence: or cache freshness changed",
        )
        for load_when in cases:
            with self.subTest(load_when=load_when), self.assertRaises(ValidationProblem):
                reference_contracts(
                    [{**base, "load_when": load_when}],
                    "sample.reference_index",
                )

    def test_foundation_owner_anchor_rejects_cross_owner_copy(self) -> None:
        contract = reference_contracts(
            [
                {
                    "path": "references/checklist.md",
                    "type": "decision-checklist",
                    "load_when": "payment settlement reconciliation failures need negative-path coverage",
                    "do_not_load_when": "no money movement or ledger state changes",
                    "required_by": ["analysis-agent"],
                    "required_output": ["checklist-result"],
                }
            ],
            "cache-design.reference_index",
            owner="cache-design",
        )[0]
        self.assertFalse(
            reference_contract_has_owner_anchor(
                contract,
                "cache-design",
                "cache keys TTL invalidation stampede stale reads hot keys source load",
            )
        )

    def test_foundation_owner_anchor_rejects_cross_owner_skip(self) -> None:
        contract = reference_contracts(
            [
                {
                    "path": "references/checklist.md",
                    "type": "decision-checklist",
                    "load_when": "cache staleness and hot-key failures need negative-path coverage",
                    "do_not_load_when": "no money movement or ledger state changes",
                    "required_by": ["analysis-agent"],
                    "required_output": ["checklist-result"],
                }
            ],
            "cache-design.reference_index",
            owner="cache-design",
        )[0]
        self.assertFalse(
            reference_contract_has_owner_anchor(
                contract,
                "cache-design",
                "cache keys TTL invalidation stampede stale reads hot keys source load",
            )
        )

    def test_domain_neighbor_anti_triggers_match_all_three_surfaces(self) -> None:
        registry = load_yaml_file(ROOT / "src/registry/domain-skills.yaml")
        for entry in registry["domain_skills"]:
            skill_file = ROOT / entry["path"] / "SKILL.md"
            _metadata, _raw, body = parse_frontmatter(skill_file)
            contracts = reference_contracts(
                entry["reference_index"],
                f"{entry['name']}.reference_index",
                owner=entry["name"],
            )
            with self.subTest(owner=entry["name"]):
                self.assertEqual(
                    [],
                    DOMAIN_VALIDATOR._neighbor_anti_errors(
                        entry, body, contracts, str(skill_file.relative_to(ROOT))
                    ),
                )

        ai = next(
            entry
            for entry in registry["domain_skills"]
            if entry["name"] == "ai-product-extension"
        )
        _metadata, _raw, ai_body = parse_frontmatter(ROOT / ai["path"] / "SKILL.md")
        ai_contracts = reference_contracts(
            ai["reference_index"], "ai-product-extension.reference_index"
        )
        missing_router_boundary = {
            **ai,
            "anti_trigger_signals": ["static algorithm without a model decision"],
        }
        errors = DOMAIN_VALIDATOR._neighbor_anti_errors(
            missing_router_boundary,
            ai_body,
            ai_contracts,
            "ai-product-extension",
        )
        self.assertTrue(
            any("registry anti_trigger_signals" in error and "ordinary search" in error for error in errors),
            errors,
        )

    def test_foundation_decision_checklists_fit_readability_and_size_contract(
        self,
    ) -> None:
        registry = load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
        checked: list[str] = []
        violations: list[tuple[str, str, int]] = []
        for entry in registry["foundation_skills"]:
            contracts = reference_contracts(
                entry["reference_index"],
                f"foundation-skills.yaml:{entry['name']}.reference_index",
                owner=entry["name"],
            )
            for contract in contracts:
                if contract["type"] != "decision-checklist":
                    continue
                path = ROOT / entry["path"] / contract["path"]
                relative = path.relative_to(ROOT).as_posix()
                checked.append(relative)
                violations.extend(
                    (relative, kind, value)
                    for kind, value in _foundation_checklist_violations(
                        path.read_text(encoding="utf-8"),
                        relative,
                    )
                )

        self.assertEqual(109, len(checked))
        self.assertEqual(len(checked), len(set(checked)))
        self.assertEqual([], violations)

    def test_foundation_decision_checklist_gate_has_negative_controls(self) -> None:
        long_rule = "# Checklist\n\n- Preserve " + " ".join(
            f"word{index}" for index in range(33)
        ) + ".\n"
        compound_rule = "# Checklist\n\n- Record the source. Verify the result.\n"
        over_line_budget = "\n".join(
            ["# Targeted", *(f"Line {index}" for index in range(60))]
        )
        over_item_budget = "# Checklist\n\n" + "\n".join(
            f"- Verify case {index}." for index in range(16)
        )
        cases = {
            "tighten": long_rule,
            "compound": compound_rule,
            "line-budget": over_line_budget,
            "decision-items": over_item_budget,
        }
        for expected, markdown in cases.items():
            with self.subTest(expected=expected):
                self.assertIn(
                    expected,
                    {
                        kind
                        for kind, _value in _foundation_checklist_violations(
                            markdown,
                            f"negative-{expected}.md",
                        )
                    },
                )
        at_line_limit = "\n".join(
            ["# Targeted", *(f"Line {index}" for index in range(59))]
        )
        self.assertNotIn(
            "line-budget",
            {
                kind
                for kind, _value in _foundation_checklist_violations(
                    at_line_limit,
                    "positive-60-lines.md",
                )
            },
        )

        split_valid = "# Checklist\n\n## Custody Controls\n\n" + "\n".join(
            f"- Verify custody case {index}." for index in range(8)
        ) + "\n\n## Settlement Controls\n\n" + "\n".join(
            f"- Verify settlement case {index}." for index in range(8)
        )
        split_generic = "# Checklist\n\n## Section 1\n\n" + "\n".join(
            f"- Verify first case {index}." for index in range(8)
        ) + "\n\n## More\n\n" + "\n".join(
            f"- Verify second case {index}." for index in range(8)
        )
        repeated = "# Checklist\n\n## Custody Controls\n\n" + "\n".join(
            f"- Verify first case {index}." for index in range(8)
        ) + "\n\n## custody-controls\n\n" + "\n".join(
            f"- Verify second case {index}." for index in range(8)
        )
        valid_kinds = {
            kind
            for kind, _value in _foundation_checklist_violations(
                split_valid, "positive-section-split.md"
            )
        }
        generic_kinds = {
            kind
            for kind, _value in _foundation_checklist_violations(
                split_generic, "negative-generic-section.md"
            )
        }
        repeated_kinds = {
            kind
            for kind, _value in _foundation_checklist_violations(
                repeated, "negative-repeated-section.md"
            )
        }
        self.assertNotIn("decision-items", valid_kinds)
        self.assertIn("decision-section-heading", generic_kinds)
        self.assertIn("decision-items", repeated_kinds)

    def test_foundation_evidence_patterns_fit_readability_and_size_contract(
        self,
    ) -> None:
        registry = load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
        checked: list[str] = []
        violations: list[tuple[str, str, int]] = []
        for entry in registry["foundation_skills"]:
            contracts = reference_contracts(
                entry["reference_index"],
                f"foundation-skills.yaml:{entry['name']}.reference_index",
                owner=entry["name"],
            )
            for contract in contracts:
                if contract["type"] != "evidence-pattern":
                    continue
                path = ROOT / entry["path"] / contract["path"]
                relative = path.relative_to(ROOT).as_posix()
                checked.append(relative)
                violations.extend(
                    (relative, kind, value)
                    for kind, value in _foundation_evidence_pattern_violations(
                        path.read_text(encoding="utf-8"),
                        relative,
                    )
                )

        self.assertEqual(109, len(checked))
        self.assertEqual(len(checked), len(set(checked)))
        self.assertEqual([], violations)

    def test_foundation_evidence_pattern_gate_has_negative_controls(self) -> None:
        long_rule = "# Evidence\n\n- Preserve " + " ".join(
            f"word{index}" for index in range(33)
        ) + ".\n"
        compound_rule = "# Evidence\n\n- Record the source. Verify the result.\n"
        over_line_budget = "\n".join(
            ["# Evidence", *(f"Line {index}" for index in range(60))]
        )
        cases = {
            "tighten": long_rule,
            "compound": compound_rule,
            "line-budget": over_line_budget,
        }
        for expected, markdown in cases.items():
            with self.subTest(expected=expected):
                self.assertIn(
                    expected,
                    {
                        kind
                        for kind, _value in _foundation_evidence_pattern_violations(
                            markdown,
                            f"negative-evidence-{expected}.md",
                        )
                    },
                )

        at_line_limit = "\n".join(
            ["# Evidence", *(f"Line {index}" for index in range(59))]
        )
        self.assertNotIn(
            "line-budget",
            {
                kind
                for kind, _value in _foundation_evidence_pattern_violations(
                    at_line_limit,
                    "positive-evidence-60-lines.md",
                )
            },
        )

    def test_foundation_evidence_patterns_preserve_high_risk_semantic_anchors(
        self,
    ) -> None:
        semantic_window_sizes = {
            (
                "api-contract-design",
                "references/evidence-patterns.md",
            ): 2,
            (
                "dependency-vulnerability-scanning",
                "references/evidence-patterns.md",
            ): 3,
        }
        anchors = {
            (
                "acceptance-standard-definition",
                "references/evidence-patterns.md",
            ): ((
                "accountable owner or review artifact",
                "evidence freshness",
                "evidence proves",
                "non-proofs",
                "recommended next step",
            ),),
            (
                "api-contract-design",
                "references/evidence-patterns.md",
            ): ((
                "record its source",
                "consumer scope",
                "proof limit",
                "residual-risk owner",
                "evidence-producing reports or artifacts",
                "preserve identifying fields",
            ),),
            (
                "dependency-vulnerability-scanning",
                "references/evidence-patterns.md",
            ): ((
                "external or credential-sensitive",
                "bounded approved credentials",
                "when required",
                "redaction",
                "registry boundary",
                "artifact owner",
            ),),
            (
                "secret-configuration-security",
                "references/evidence-patterns.md",
            ): ((
                "raw secrets",
                "real credentials",
                "compromised secret",
                "unredacted scanner output",
                "owner approval",
                "no leak exists",
            ),),
            (
                "message-queue-design",
                "references/evidence-patterns.md",
            ): ((
                "authorized topic or queue scope",
                "stop condition",
                "pause or rollback path",
                "payload redaction",
                "bounded window",
                "allowed message class",
            ),),
            (
                "shell-cli-professional-usage",
                "references/evidence-patterns.md",
            ): ((
                "displayed commands",
                "executed argv",
                "run's shell",
                "working directory",
                "omits or redacts",
                "expanded secrets",
                "credential-bearing environment",
            ),),
        }
        registry = load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
        entries = {entry["name"]: entry for entry in registry["foundation_skills"]}
        for (owner, reference_path), groups in anchors.items():
            path = ROOT / entries[owner]["path"] / reference_path
            units = _reference_semantic_units(path.read_text(encoding="utf-8"))
            for group in groups:
                expected = tuple(term.casefold() for term in group)
                with self.subTest(owner=owner, anchor=expected[0]):
                    _assert_unique_contiguous_semantic_window(
                        self,
                        units,
                        group,
                        window_size=semantic_window_sizes.get(
                            (owner, reference_path),
                            1,
                        ),
                    )

    def test_professional_references_fit_readability_and_size_contract(
        self,
    ) -> None:
        registry = load_yaml_file(ROOT / "src/registry/professional-skills.yaml")
        self.assertEqual(26, len(registry["professional_skills"]))
        checked: list[str] = []
        violations: list[tuple[str, str, int]] = []
        review_count = 0
        for entry in registry["professional_skills"]:
            contracts = reference_contracts(
                entry["reference_index"],
                f"professional-skills.yaml:{entry['name']}.reference_index",
                owner=entry["name"],
            )
            for contract in contracts:
                path = ROOT / entry["path"] / contract["path"]
                relative = path.relative_to(ROOT).as_posix()
                markdown = path.read_text(encoding="utf-8")
                checked.append(relative)
                violations.extend(
                    (relative, kind, value)
                    for kind, value in _professional_reference_violations(
                        markdown,
                        relative,
                    )
                )
                review_count += sum(
                    finding.get("band") == "review-as-complex"
                    for finding in ai_readability_findings(markdown, relative)
                )

        self.assertEqual(93, len(checked))
        self.assertEqual(len(checked), len(set(checked)))
        self.assertLessEqual(review_count, 102)
        self.assertEqual([], violations)

    def test_professional_reference_gate_has_negative_controls(self) -> None:
        long_rule = "# Reference\n\n- Preserve " + " ".join(
            f"word{index}" for index in range(33)
        ) + ".\n"
        compound_rule = "# Reference\n\n- Record the source. Verify the result.\n"
        over_line_budget = "\n".join(
            ["# Reference", *(f"Line {index}" for index in range(60))]
        )
        cases = {
            "tighten": long_rule,
            "compound": compound_rule,
            "line-budget": over_line_budget,
        }
        for expected, markdown in cases.items():
            with self.subTest(expected=expected):
                self.assertIn(
                    expected,
                    {
                        kind
                        for kind, _value in _professional_reference_violations(
                            markdown,
                            f"negative-professional-{expected}.md",
                        )
                    },
                )

        at_line_limit = "\n".join(
            ["# Reference", *(f"Line {index}" for index in range(59))]
        )
        self.assertNotIn(
            "line-budget",
            {
                kind
                for kind, _value in _professional_reference_violations(
                    at_line_limit,
                    "positive-professional-60-lines.md",
                )
            },
        )

    def test_professional_references_preserve_high_risk_semantic_anchors(
        self,
    ) -> None:
        anchors = {
            (
                "task-dag-planner",
                "references/task-contract-patterns.md",
            ): ((
                "requires a concrete downstream blocker",
                "required artifacts",
                "schema or data availability",
                "release order",
                "nonblocking sequence preferences",
            ),),
            (
                "architecture-impact-reviewer",
                "references/architecture-output-and-gates.md",
            ): ((
                "public or indirect consumers",
                "authoritative data ownership",
                "known/unknown consumers",
                "data-owner delta",
                "compatibility/versioning or migration need",
                "rollout boundary",
                "evidence for preserved behavior",
            ),),
            (
                "backend-change-builder",
                "references/backend-output-and-gates.md",
            ): (
                (
                    "original finding or failure mechanism",
                    "recurrence signals",
                    "same-pattern results",
                    "only when triggered",
                ),
                (
                    "protects the affected invariant",
                    "exposes partial success",
                    "publish-after-commit",
                    "system boundary supports the choice",
                ),
            ),
            (
                "security-privacy-gate",
                "references/security-output-and-gates.md",
            ): ((
                "authority-boundary crossing",
                "prompts, retrieval, model output, agents, connectors, scanners, shell, iac, and network writes",
                "permission or isolation evidence",
                "abuse tests",
                "proof limits",
                "residual exfiltration or unsafe-action risk",
            ),),
            (
                "reliability-observability-gate",
                "references/reliability-output-and-gates.md",
            ): ((
                "freshness semantics",
                "material user-visible state",
                "recovery or reconciliation evidence",
                "silent staleness is not availability",
            ),),
            (
                "delivery-release-gate",
                "references/delivery-output-and-gates.md",
            ): (
                (
                    "desired/effective or rendered change",
                    "state/sync/drift behavior",
                    "hooks or crds",
                    "containment/recovery evidence",
                    "actual toolchain",
                ),
                (
                    "only the applicable outcomes",
                    "incident evidence",
                    "mitigation or resolution boundary",
                    "regulated-release evidence",
                    "approval, provenance, audit, retention, and exceptions",
                ),
            ),
            (
                "ai-code-review-refactor",
                "references/review-output-and-gates.md",
            ): ((
                "authoritative dependency evidence",
                "acceptance gap",
                "reachable source-to-impact path",
                "request the missing proof",
            ),),
            (
                "change-documentation-gate",
                "references/documentation-output-and-gates.md",
            ): ((
                "api or schema documentation surface",
                "public shape",
                "error model",
                "applicable rate limits",
                "generated-client impact",
                "deprecation policy",
                "final source and contract tests",
            ),),
        }
        registry = load_yaml_file(ROOT / "src/registry/professional-skills.yaml")
        entries = {entry["name"]: entry for entry in registry["professional_skills"]}
        for (owner, reference_path), groups in anchors.items():
            path = ROOT / entries[owner]["path"] / reference_path
            units = _reference_semantic_units(path.read_text(encoding="utf-8"))
            for group in groups:
                expected = tuple(term.casefold() for term in group)
                with self.subTest(owner=owner, anchor=expected[0]):
                    self.assertEqual(
                        1,
                        sum(
                            all(term in unit for term in expected)
                            for unit in units
                        ),
                    )
                    missing_anchor = [
                        unit.replace(expected[0], "", 1) for unit in units
                    ]
                    self.assertEqual(
                        0,
                        sum(
                            all(term in unit for term in expected)
                            for unit in missing_anchor
                        ),
                    )

    def test_foundation_benchmark_patterns_fit_readability_and_size_contract(
        self,
    ) -> None:
        registry = load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
        self.assertEqual(150, len(registry["foundation_skills"]))
        checked: list[str] = []
        violations: list[tuple[str, str, int]] = []
        review_count = 0
        line_count = 0
        list_sentence_count = 0
        for entry in registry["foundation_skills"]:
            contracts = reference_contracts(
                entry["reference_index"],
                f"foundation-skills.yaml:{entry['name']}.reference_index",
                owner=entry["name"],
            )
            for contract in contracts:
                if contract["type"] != "benchmark-pattern":
                    continue
                path = ROOT / entry["path"] / contract["path"]
                relative = path.relative_to(ROOT).as_posix()
                markdown = path.read_text(encoding="utf-8")
                checked.append(relative)
                line_count += len(markdown.splitlines())
                list_sentence_count += len(
                    ai_markdown_list_sentence_counts(markdown)
                )
                violations.extend(
                    (relative, kind, value)
                    for kind, value in _foundation_benchmark_pattern_violations(
                        markdown,
                        relative,
                    )
                )
                review_count += sum(
                    finding.get("band") == "review-as-complex"
                    for finding in ai_readability_findings(markdown, relative)
                )

        self.assertEqual(109, len(checked))
        self.assertEqual(len(checked), len(set(checked)))
        self.assertEqual(3830, line_count)
        self.assertEqual(758, list_sentence_count)
        self.assertEqual(106, review_count)
        self.assertEqual([], violations)

    def test_foundation_benchmark_gate_has_negative_controls(self) -> None:
        long_rule = "# Benchmark\n\n- Preserve " + " ".join(
            f"word{index}" for index in range(33)
        ) + ".\n"
        compound_rule = "# Benchmark\n\n- Record the source. Verify the result.\n"
        over_line_budget = "\n".join(
            ["# Benchmark", *(f"Line {index}" for index in range(60))]
        )
        cases = {
            "tighten": long_rule,
            "compound": compound_rule,
            "line-budget": over_line_budget,
        }
        for expected, markdown in cases.items():
            with self.subTest(expected=expected):
                self.assertIn(
                    expected,
                    {
                        kind
                        for kind, _value in _foundation_benchmark_pattern_violations(
                            markdown,
                            f"negative-benchmark-{expected}.md",
                        )
                    },
                )

        at_line_limit = "\n".join(
            ["# Benchmark", *(f"Line {index}" for index in range(59))]
        )
        self.assertNotIn(
            "line-budget",
            {
                kind
                for kind, _value in _foundation_benchmark_pattern_violations(
                    at_line_limit,
                    "positive-benchmark-60-lines.md",
                )
            },
        )

    def test_foundation_benchmarks_preserve_high_risk_semantic_anchors(
        self,
    ) -> None:
        semantic_window_sizes = {
            (
                "dto-schema-design",
                "references/benchmarks-and-patterns.md",
            ): 5,
        }
        anchors = {
            (
                "user-role-identification",
                "references/benchmarks-and-patterns.md",
            ): ((
                "discovery or ux inputs",
                "do not treat them as authorization authority",
                "trusted policy inputs",
                "server-side enforcement",
            ),),
            (
                "state-machine-modeling",
                "references/benchmarks-and-patterns.md",
            ): ((
                "authoritative domain or policy transition contract",
                "deny origins or targets absent from that contract",
                "unsearched producers and migration scripts as proof limits",
            ),),
            (
                "dto-schema-design",
                "references/benchmarks-and-patterns.md",
            ): ((
                "exclude credentials, secrets, tokens, and api keys from ordinary external dtos",
                "explicitly issues, recovers, or exchanges them",
                "authorized, purpose-bound, minimized one-time delivery",
                "forbid logging, caching, and uncontrolled replay",
                "scope, expiry, rotation, and recovery lifecycle",
            ),),
            (
                "data-migration-design",
                "references/benchmarks-and-patterns.md",
            ): ((
                "rows that still require migration",
                "concurrent writers merge or dual-write",
                "does not establish production lock, lag, or capacity safety",
            ),),
            (
                "permission-boundary-modeling",
                "references/benchmarks-and-patterns.md",
            ): ((
                "authoritative decision before the protected disclosure or effect",
                "each reachable path",
                "actual architecture and bypass analysis",
            ),),
            (
                "form-validation-design",
                "references/benchmarks-and-patterns.md",
            ): ((
                "explicit product need",
                "state-management-design plus security-privacy-gate ownership",
                "bind user/tenant scope",
                "prove purge on submit/cancel/expiry/logout or identity switch",
            ),),
            (
                "transaction-consistency",
                "references/benchmarks-and-patterns.md",
            ): (
                (
                    "remote call occurs while a local transaction or lock is open",
                    "invariant requires that ordering",
                    "provider latency, timeout, connection/lock exhaustion, deadlock, cancellation, duplicate-call, and rollback",
                    "representative concurrency",
                ),
                (
                    "remote call occurs before final local commit",
                    "remote success followed by local rollback",
                    "replay safety",
                    "reservation/authorization expiry or provider cancellation",
                ),
            ),
            (
                "cache-design",
                "references/benchmarks-and-patterns.md",
            ): (
                (
                    "hot keys, synchronized expiry, restart/failover, or cross-pod concurrency",
                    "topology-appropriate outcome",
                    "coalescing, a lease, early refresh, stagger/jitter, stale fallback, warm-up, or origin limiting",
                ),
                (
                    "attacker-controlled or high-cardinality misses",
                    "normalization, admission/rate control, bounded negative caching, or an existence filter",
                    "legitimate key set, false-result behavior, and recovery needs determine the choice",
                ),
            ),
            (
                "consumer-impact-analysis",
                "references/benchmarks-and-patterns.md",
            ): ((
                "structural schema tooling governs a mixed-version rollout",
                "backward/forward/full mode",
                "producer/consumer order",
                "supports shape compatibility",
                "does not prove semantic, default, or rollout safety",
            ),),
            (
                "skill-efficacy-benchmark",
                "references/benchmarks-and-patterns.md",
            ): ((
                "static validators prove the represented cases, not unrepresented ones",
                "small samples do not estimate population catch rate",
                "token proxies are not live usage",
                "reports and builds do not prove real-host startup, wall-clock performance, production accuracy, or installed user experience",
            ),),
        }
        registry = load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
        entries = {entry["name"]: entry for entry in registry["foundation_skills"]}
        for (owner, reference_path), groups in anchors.items():
            path = ROOT / entries[owner]["path"] / reference_path
            units = _reference_semantic_units(path.read_text(encoding="utf-8"))
            for group in groups:
                expected = tuple(term.casefold() for term in group)
                with self.subTest(owner=owner, anchor=expected[0]):
                    _assert_unique_contiguous_semantic_window(
                        self,
                        units,
                        group,
                        window_size=semantic_window_sizes.get(
                            (owner, reference_path),
                            1,
                        ),
                    )

    def test_foundation_decision_checklists_preserve_semantic_anchor_groups(
        self,
    ) -> None:
        anchors = {
            "code-clarity-maintainability": ((
                "inspected paths",
                "current diff or review",
                "separate artifact",
            ),),
            "controller-api-implementation": ((
                "transport boundary",
                "owning service contract",
                "trigger is absent",
                "triggered business",
                "decisions to their owners",
            ),),
            "domain-event-modeling": ((
                "producer",
                "rollback path",
                "validation evidence",
                "proves and does not prove",
                "residual-risk owner",
                "handoff boundary",
                "next professional gate",
            ),),
            "file-storage-processing": ((
                "manual review procedure",
                "final-edit freshness",
                "proves and does not prove",
                "rollback/containment path",
                "next handoff owner",
            ),),
            "form-validation-design": ((
                "frontend validation",
                "backend schema",
                "trusted enforcement authority",
                "neither duplicates nor replaces",
            ),),
            "message-queue-design": (
                (
                    "schema evolution or replay",
                    "replay can outlive",
                    "duplicate-safe effects",
                    "without expired deduplication state",
                ),
                (
                    "select tests from paths triggered",
                    "applicable paths include",
                    "version-skew behavior",
                    "unverified production or provider limits",
                ),
            ),
            "testability-seam-design": ((
                "inventory reachable collaborators",
                "generated inputs, and dependency-graph overrides",
                "externally owned",
                "deliberately real boundaries",
                "unrelated seam types",
            ),),
            "version-compatibility": ((
                "api",
                "generated client surfaces",
                "stored data and behavior surfaces",
                "old/new coexistence or rollback",
                "unknown consumers or surfaces",
            ),),
        }
        registry = load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
        entries = {entry["name"]: entry for entry in registry["foundation_skills"]}
        for owner, groups in anchors.items():
            path = ROOT / entries[owner]["path"] / "references/checklist.md"
            units: list[str] = []
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.startswith("- "):
                    units.append(line[2:].casefold())
                elif line.startswith("  ") and units:
                    units[-1] += " " + line.strip().casefold()
                elif line.strip() and not line.startswith("#"):
                    units.append(line.strip().casefold())
            for group in groups:
                expected = tuple(term.casefold() for term in group)
                with self.subTest(owner=owner, anchor=expected[0]):
                    self.assertEqual(
                        1,
                        sum(
                            all(term in unit for term in expected)
                            for unit in units
                        ),
                    )
                    missing_anchor = [
                        unit.replace(expected[0], "", 1) for unit in units
                    ]
                    self.assertEqual(
                        0,
                        sum(
                            all(term in unit for term in expected)
                            for unit in missing_anchor
                        ),
                    )

    def test_foundation_targeted_and_template_references_fit_contract(
        self,
    ) -> None:
        registry = load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
        counts = {"targeted": 0, "template": 0}
        exact_line_limit: list[str] = []
        violations: list[tuple[str, str, int]] = []
        for entry in registry["foundation_skills"]:
            contracts = reference_contracts(
                entry["reference_index"],
                f"foundation-skills.yaml:{entry['name']}.reference_index",
                owner=entry["name"],
            )
            for contract in contracts:
                reference_type = contract["type"]
                if reference_type not in counts:
                    continue
                path = ROOT / entry["path"] / contract["path"]
                relative = path.relative_to(ROOT).as_posix()
                markdown = path.read_text(encoding="utf-8")
                counts[reference_type] += 1
                if (
                    reference_type == "targeted"
                    and len(markdown.splitlines())
                    == REFERENCE_VALIDATOR.TARGETED_LINE_LIMIT
                ):
                    exact_line_limit.append(relative)
                violations.extend(
                    (relative, kind, value)
                    for kind, value in _foundation_targeted_or_template_violations(
                        markdown,
                        relative,
                        reference_type,
                    )
                )

        self.assertEqual({"targeted": 48, "template": 1}, counts)
        self.assertEqual(
            [
                "src/foundation/capabilities/code-review/"
                "references/finding-taxonomy.md",
                "src/foundation/capabilities/skill-authoring-expert/"
                "references/pressure-scenarios.md"
            ],
            exact_line_limit,
        )
        self.assertEqual([], violations)

    def test_foundation_targeted_and_template_gate_has_negative_controls(
        self,
    ) -> None:
        long_rule = "# Reference\n\n- Preserve " + " ".join(
            f"word{index}" for index in range(33)
        ) + ".\n"
        compound_rule = "# Reference\n\n- Record the source. Verify the result.\n"
        for reference_type in ("targeted", "template"):
            with self.subTest(reference_type=reference_type, finding="tighten"):
                self.assertIn(
                    "tighten",
                    {
                        kind
                        for kind, _value in (
                            _foundation_targeted_or_template_violations(
                                long_rule,
                                f"negative-{reference_type}-tighten.md",
                                reference_type,
                            )
                        )
                    },
                )
            with self.subTest(reference_type=reference_type, finding="compound"):
                self.assertIn(
                    "compound",
                    {
                        kind
                        for kind, _value in (
                            _foundation_targeted_or_template_violations(
                                compound_rule,
                                f"negative-{reference_type}-compound.md",
                                reference_type,
                            )
                        )
                    },
                )

        at_line_limit = "\n".join(
            ["# Targeted", *(f"Line {index}" for index in range(59))]
        )
        over_line_limit = at_line_limit + "\nLine 59"
        self.assertNotIn(
            "line-budget",
            {
                kind
                for kind, _value in _foundation_targeted_or_template_violations(
                    at_line_limit,
                    "positive-targeted-60-lines.md",
                    "targeted",
                )
            },
        )
        self.assertIn(
            "line-budget",
            {
                kind
                for kind, _value in _foundation_targeted_or_template_violations(
                    over_line_limit,
                    "negative-targeted-61-lines.md",
                    "targeted",
                )
            },
        )

    def test_foundation_targeted_and_template_semantic_anchor_groups(
        self,
    ) -> None:
        anchors = {
            (
                "agent-execution-discipline",
                "references/evidence-reuse-patterns.md",
            ): (
                ("same claim, scope, input identity, and mechanism",),
                ("source or provenance is missing",),
                ("two artifacts support incompatible results",),
                ("contradictory until their scope",),
                ("both artifact identities and unresolved relationship",),
                ("proof limit", "residual uncertainty"),
            ),
            (
                "task-context-selection",
                "references/context-selection-checklist.md",
            ): (
                ("source identity", "freshness basis", "decision use"),
                ("layer 3 skill or reference material", "named distinction"),
                ("exclude irrelevant, stale, and redundant context", "record omissions"),
                ("material state change", "freshness or decision use"),
                ("context-budget tradeoff", "residual uncertainty"),
            ),
            (
                "task-handoff-context",
                "references/task-context-checklist.md",
            ): (
                ("downstream consumer and purpose", "decision or next action"),
                ("decision-changing claim", "exact artifact", "latest diff"),
                ("fresh validation", "coverage and proof limits"),
                ("unresolved decisions", "constraints", "findings", "owner"),
                ("exclusions and omissions", "downstream impact"),
                ("staleness and reload triggers", "material artifact"),
                ("contradictory evidence", "needed to reconcile"),
                ("lossy transfer", "qualification", "proof limit"),
            ),
            (
                "task-dag-decomposition",
                "references/candidate-graph-evidence.md",
            ): (
                ("acceptance-linked outcome", "produced output"),
                ("data edge", "control edge", "contract edge", "order edge"),
                ("current source", "downstream blocker", "evidence-backed edge"),
                ("rejected edges", "nonblocking"),
                ("collision surfaces", "shared-write surfaces", "resource surfaces"),
                ("candidate critical path", "supported edges"),
                ("parallel opportunity", "no path dependency"),
                ("cycles", "uncertainty"),
                ("proof limits", "residual risk", "consumer acceptance or rejection"),
            ),
            (
                "targeted-validation-selection",
                "references/repository-command-entry-evidence.md",
            ): (
                ("test, build, schema, lint, static-analysis", "generator entrypoints"),
                ("existing tests", "paths and behavior"),
                ("exact source path", "configuration key", "candidate command"),
                ("observable acceptance", "risk surface", "command coverage"),
                ("smallest-sufficient commands", "combined coverage"),
                ("repository source", "expected signal"),
                ("actual result when run", "freshness input/hash/time facts"),
                ("freshness values as facts", "Core Guard G"),
                ("entrypoint is unavailable", "repository-defined fallback"),
                ("unavailable-entry fallback", "no supported command"),
                ("unverified scope", "proof limits", "residual risk"),
            ),
            (
                "repository-context-map",
                "references/validation-freshness-handoff.md",
            ): (
                "downstream implementation or review",
                "next owner",
                "validation limits",
                "residual risks",
                "known task-relevant rollback clue",
                "needed rollback clue is unavailable",
                "mark that gap instead of inventing one",
            ),
            (
                "skill-authoring-expert",
                "references/pressure-scenarios.md",
            ): (
                (
                    "strong rule bypassed as a small change",
                    "this is tiny",
                    "discipline does not apply",
                    "rule fires regardless of size",
                    "pressure case proves that behavior",
                ),
                (
                    "reference bloat into the body",
                    "keep it in the body for visibility",
                    "deep content uses a reference with a loading policy",
                    "body stays within its context budget",
                ),
            ),
        }
        registry = load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
        entries = {entry["name"]: entry for entry in registry["foundation_skills"]}
        for (owner, reference_path), raw_groups in anchors.items():
            groups = (
                raw_groups
                if isinstance(raw_groups[0], tuple)
                else (raw_groups,)
            )
            path = ROOT / entries[owner]["path"] / reference_path
            units = _reference_semantic_units(path.read_text(encoding="utf-8"))
            for group in groups:
                expected = tuple(term.casefold() for term in group)
                with self.subTest(owner=owner, anchor=expected[0]):
                    self.assertEqual(
                        1,
                        sum(
                            all(term in unit for term in expected)
                            for unit in units
                        ),
                    )
                    missing_anchor = [
                        unit.replace(expected[0], "", 1) for unit in units
                    ]
                    self.assertEqual(
                        0,
                        sum(
                            all(term in unit for term in expected)
                            for unit in missing_anchor
                        ),
                    )

    def test_domain_checklists_preserve_semantic_anchor_groups(self) -> None:
        anchors = {
            "ai-product-extension": (
                (
                    "user-facing evidence authority",
                    "independent verification",
                    "explicit degraded decisions",
                ),
                ("tool calls", "identity", "recovery", "audit evidence"),
            ),
            "bigdata-product-extension": (
                ("event time", "event-time authority", "clock semantics"),
                ("metadata and manifest lifecycles", "state evolution"),
                ("state or partition growth", "replay or backfill progress"),
                ("dead-letter or quarantine records", "data classification"),
            ),
            "iot-embedded-extension": (
                (
                    "credential rotation and revocation",
                    "affected trust boundaries",
                    "attestation-loss recovery",
                ),
                ("secret-exposure behavior", "supported revisions in scope"),
                (
                    "boot-loop detection evidence",
                    "bootable, serviceable, or safe target",
                    "behavior when its image",
                    "connectivity is unavailable",
                ),
            ),
            "low-level-systems-extension": (
                ("deferred-work handoff", "interrupted-state cleanup"),
                (
                    "panic, exception, and unwind behavior",
                    "allocator pairing",
                    "callback registration and revocation",
                    "cross-runtime contract",
                ),
            ),
            "payment-trading-extension": (
                (
                    "client order or request identity",
                    "correction identity",
                    "snapshot or authoritative-query recovery",
                ),
                (
                    "quantity and notional bounds",
                    "fee and funding semantics",
                    "price and quantity scale",
                ),
                ("ordering or reorder behavior", "audit evidence"),
                ("insurance or loss allocation", "auto-deleveraging states"),
                ("price or limit rejection", "balance or position drift"),
            ),
            "web3-product-extension": (
                ("replacement or cancellation economics", "work ceilings"),
                ("wallet or custody records", "authoritative rebuild behavior"),
                ("current chain state", "stale-index decisions"),
                ("proxy-admin", "implementation ownership"),
                (
                    "sequencer and challenge-window behavior",
                    "destination-completion evidence",
                ),
            ),
        }
        expected_structure = {
            "ai-product-extension": (15, 15, [15]),
            "bigdata-product-extension": (15, 15, [15]),
            "iot-embedded-extension": (15, 15, [15]),
            "low-level-systems-extension": (15, 15, [15]),
            "payment-trading-extension": (27, 14, [3, 6, 4, 14]),
            "web3-product-extension": (36, 9, [9, 5, 4, 7, 1, 8, 2]),
        }
        independent_anchor_items = {
            "payment-trading-extension": (
                "Custody Authority",
                "finality roles",
                "authoritative server-side events or state",
                True,
            ),
            "web3-product-extension": (
                "Allowances, Nonstandard Assets, and Delegated Calls",
                "nonce or replay state",
                "residual authority",
                False,
            ),
        }
        registry = load_yaml_file(ROOT / "src/registry/domain-skills.yaml")
        entries = {entry["name"]: entry for entry in registry["domain_skills"]}
        self.assertTrue(set(anchors).issubset(entries))
        self.assertTrue(set(expected_structure).issubset(entries))
        for owner, groups in anchors.items():
            path = ROOT / entries[owner]["path"] / "references/checklist.md"
            text = path.read_text(encoding="utf-8")
            bullets = [
                line.casefold() for line in text.splitlines() if line.startswith("- ")
            ]
            facts = AUDIT._markdown_structural_facts(text, "decision-checklist")
            total, maximum, section_counts = expected_structure[owner]
            with self.subTest(owner=owner):
                self.assertEqual(total, facts["decision_item_count"])
                self.assertEqual(maximum, facts["max_decision_section_item_count"])
                self.assertEqual(
                    section_counts,
                    [
                        row["decision_item_count"]
                        for row in facts["decision_sections"]
                    ],
                )
                self.assertEqual(
                    [],
                    ai_readability_findings(text, path.as_posix()),
                )
            for group in groups:
                with self.subTest(owner=owner, anchors=group):
                    self.assertEqual(
                        1,
                        sum(
                            all(term.casefold() in bullet for term in group)
                            for bullet in bullets
                        ),
                    )
            if owner not in independent_anchor_items:
                continue
            expected_heading, first_anchor, second_anchor, adjacent = (
                independent_anchor_items[owner]
            )
            section_bullets: dict[str, list[str]] = {}
            current_heading = ""
            for line in text.splitlines():
                if line.startswith("## "):
                    current_heading = line[3:]
                    section_bullets.setdefault(current_heading, [])
                elif line.startswith("- ") and current_heading:
                    section_bullets[current_heading].append(line[2:].casefold())
            first_matches = [
                (heading, index)
                for heading, values in section_bullets.items()
                for index, value in enumerate(values)
                if first_anchor in value
            ]
            second_matches = [
                (heading, index)
                for heading, values in section_bullets.items()
                for index, value in enumerate(values)
                if second_anchor in value
            ]
            with self.subTest(owner=owner, independent_anchors=True):
                self.assertEqual(1, len(first_matches))
                self.assertEqual(1, len(second_matches))
                self.assertEqual(expected_heading, first_matches[0][0])
                self.assertEqual(expected_heading, second_matches[0][0])
                self.assertLess(first_matches[0][1], second_matches[0][1])
                if adjacent:
                    self.assertEqual(
                        first_matches[0][1] + 1,
                        second_matches[0][1],
                    )
    def test_domain_absolute_detector_rejects_unscoped_every_claims(self) -> None:
        registry = load_yaml_file(ROOT / "src/registry/domain-skills.yaml")
        documents = []
        for entry in registry["domain_skills"]:
            contracts = reference_contracts(
                entry["reference_index"],
                f"domain-skills.yaml:{entry['name']}.reference_index",
                owner=entry["name"],
            )
            for contract in contracts:
                if contract["type"] != "decision-checklist":
                    continue
                path = ROOT / entry["path"] / contract["path"]
                documents.append(
                    {
                        "path": path.relative_to(ROOT).as_posix(),
                        "layer": "domain",
                        "owner": entry["name"],
                        "text": path.read_text(encoding="utf-8"),
                    }
                )
        original_counter = AUDIT.count_o200k_base_tokens
        AUDIT.count_o200k_base_tokens = lambda _text: 0
        try:
            current = AUDIT._collect_reference_semantic_advisories(documents)
        finally:
            AUDIT.count_o200k_base_tokens = original_counter
        unresolved = [
            item
            for item in current["candidates"]
            if item["finding"] == "unconditional_absolute_candidate"
            and item["unresolved"]
        ]
        self.assertEqual([], unresolved)

        original_counter = AUDIT.count_o200k_base_tokens
        AUDIT.count_o200k_base_tokens = lambda _text: 0
        try:
            synthetic = AUDIT._collect_reference_semantic_advisories(
                [
                    {
                        "path": "src/domain-extensions/synthetic/references/checklist.md",
                        "layer": "domain",
                        "owner": "synthetic",
                        "text": "# Checklist\n\n- Compatibility bounds every state.\n",
                    }
                ]
            )
        finally:
            AUDIT.count_o200k_base_tokens = original_counter
        rejected = [
            item
            for item in synthetic["candidates"]
            if item["finding"] == "unconditional_absolute_candidate"
            and item["unresolved"]
        ]
        self.assertEqual(1, len(rejected))


if __name__ == "__main__":
    unittest.main()
