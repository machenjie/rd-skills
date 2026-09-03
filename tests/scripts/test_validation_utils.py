from __future__ import annotations

import builtins
import copy
import contextlib
import importlib.util
import tempfile
import unittest
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validation_utils.py"
TEST_BUILD_IDENTITY = "AAECAwQFBgcICQoLDA0ODw"


@contextlib.contextmanager
def _module_without_tiktoken() -> Iterator[tuple[ModuleType, list[str]]]:
    original_import = builtins.__import__
    tiktoken_imports: list[str] = []

    def guarded_import(
        name: str,
        globals=None,
        locals=None,
        fromlist=(),
        level: int = 0,
    ):
        if name == "tiktoken" or name.startswith("tiktoken."):
            tiktoken_imports.append(name)
            raise ModuleNotFoundError(
                "No module named 'tiktoken'",
                name="tiktoken",
            )
        return original_import(name, globals, locals, fromlist, level)

    spec = importlib.util.spec_from_file_location(
        "validation_utils_without_tiktoken",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    with mock.patch("builtins.__import__", side_effect=guarded_import):
        spec.loader.exec_module(module)
        yield module, tiktoken_imports


class ValidationUtilsDependencyBoundaryTests(unittest.TestCase):
    def test_runtime_asset_build_identity_v2_vectors_and_canonical_decoder(
        self,
    ) -> None:
        with _module_without_tiktoken() as (module, imports):
            self.assertEqual(
                "AAAAAAAAAAAAAAAAAAAAAA",
                module.runtime_asset_build_identity("00" * 32),
            )
            self.assertEqual(
                "_____________________w",
                module.runtime_asset_build_identity("ff" * 32),
            )
            self.assertEqual(
                "AAECAwQFBgcICQoLDA0ODw",
                module.runtime_asset_build_identity(
                    "000102030405060708090a0b0c0d0e0f"
                    "101112131415161718191a1b1c1d1e1f"
                ),
            )
            self.assertEqual(
                bytes(range(16)),
                module.runtime_asset_build_identity_bytes(
                    "AAECAwQFBgcICQoLDA0ODw"
                ),
            )
            self.assertEqual([], imports)

            for malformed_digest in (
                None,
                b"00" * 32,
                "0" * 63,
                "0" * 65,
                "A" * 64,
                "g" * 64,
                "0" * 63 + " ",
            ):
                with self.subTest(digest=malformed_digest):
                    with self.assertRaises(ValueError):
                        module.runtime_asset_build_identity(malformed_digest)

            for malformed_identity in (
                None,
                b"A" * 22,
                "0" * 32,
                "A" * 21,
                "A" * 23,
                "A" * 21 + "B",
                "A" * 21 + "+",
                "A" * 21 + "/",
                "A" * 21 + "=",
                "A" * 21 + " ",
            ):
                with self.subTest(identity=malformed_identity):
                    with self.assertRaises(ValueError):
                        module.runtime_asset_build_identity_bytes(malformed_identity)

    def test_runtime_selection_wrapper_requires_and_forwards_build_identity(
        self,
    ) -> None:
        with _module_without_tiktoken() as (module, _imports):
            with self.assertRaises(TypeError):
                module.layer3_selector_runtime_selection(
                    {},
                    evidence_signals=["bounded signal"],
                )
            receipt = {"selected_layer3": ["configuration-runtime-policy"]}
            with mock.patch.object(
                module,
                "layer3_selector_runtime_selection_receipt",
                return_value=receipt,
            ) as consumer:
                selected = module.layer3_selector_runtime_selection(
                    {"contract": "fixed projection"},
                    evidence_signals=["bounded signal"],
                    build_identity=TEST_BUILD_IDENTITY,
                )
            self.assertEqual(["configuration-runtime-policy"], selected)
            consumer.assert_called_once_with(
                {"contract": "fixed projection"},
                evidence_signals=["bounded signal"],
                build_identity=TEST_BUILD_IDENTITY,
            )

    def test_review_finding_order_is_core_owned_and_closed(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            canonical = copy.deepcopy(module.CORE_CONTRACTS)
            compiler = canonical["review_discipline_contract"][
                "review_boundary_contract"
            ]["finding_compiler"]
            review = (
                ROOT
                / "src/control-skills/engineering-control-plane/references/review-handoff-template.md"
            ).read_text(encoding="utf-8")
            field_block = review.partition(
                "For each implementation or repair finding, state fields in this order:\n\n"
            )[2].partition(
                "\n\nRe-review findings require both classification fields"
            )[0]
            artifact_labels = [
                line.split(":", 1)[0]
                for line in field_block.splitlines()
                if line
            ]
            self.assertEqual(
                compiler["public_handoff_raw_field_order"],
                artifact_labels,
            )

            for label, mutate in (
                (
                    "swap",
                    lambda values: [values[1], values[0], *values[2:]],
                ),
                ("insert", lambda values: [*values[:2], "Unexpected", *values[2:]]),
                ("delete", lambda values: values[1:]),
                ("duplicate", lambda values: [values[0], *values]),
            ):
                with self.subTest(mutation=label):
                    mutated = copy.deepcopy(canonical)
                    order = mutated["review_discipline_contract"][
                        "review_boundary_contract"
                    ]["finding_compiler"]["public_handoff_raw_field_order"]
                    mutated["review_discipline_contract"][
                        "review_boundary_contract"
                    ]["finding_compiler"]["public_handoff_raw_field_order"] = mutate(
                        order
                    )
                    self.assertTrue(module.validate_core_contracts(mutated))

    def test_quality_cost_gate_is_core_owned_and_quality_first(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            core = copy.deepcopy(module.CORE_CONTRACTS)
            gate = core["context_budget_contract"]["quality_cost_gate"]
            self.assertFalse(
                gate["candidate_total_not_greater_is_correctness_acceptance"]
            )
            self.assertTrue(gate["hard_ceiling_independent"])
            self.assertFalse(gate["runtime_dependency"])
            gate["candidate_total_not_greater_is_correctness_acceptance"] = True
            self.assertTrue(module.validate_core_contracts(core))

    def test_context_budget_taxonomy_and_rendered_categories_are_bijective(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            contract = module.CORE_CONTRACTS["context_budget_contract"]
            mutations: list[tuple[str, dict[str, object]]] = []

            swapped_entry = copy.deepcopy(contract)
            swapped_entry["budget_classes"]["main"][
                "category"
            ] = "dispatch_composition"
            mutations.append(("swapped-entry", swapped_entry))

            missing = copy.deepcopy(contract)
            missing["context_taxonomy"]["resident_runtime"]["classes"] = []
            mutations.append(("missing", missing))

            unknown = copy.deepcopy(contract)
            unknown["context_taxonomy"]["dispatch_composition"]["classes"].append(
                "unknown"
            )
            mutations.append(("unknown", unknown))

            overlap = copy.deepcopy(contract)
            overlap["context_taxonomy"]["dispatch_composition"]["classes"].append(
                "main"
            )
            mutations.append(("overlap", overlap))

            duplicate = copy.deepcopy(contract)
            duplicate["context_taxonomy"]["resident_runtime"]["classes"].append(
                "main"
            )
            mutations.append(("duplicate", duplicate))

            authoring_leak = copy.deepcopy(contract)
            authoring_leak["context_taxonomy"]["authoring"]["classes"].append(
                "main"
            )
            mutations.append(("authoring-leak", authoring_leak))

            dynamic_leak = copy.deepcopy(contract)
            dynamic_leak["context_taxonomy"]["runtime_dynamic_context"][
                "classes"
            ].append("task")
            mutations.append(("dynamic-leak", dynamic_leak))

            swapped_taxonomy = copy.deepcopy(contract)
            swapped_taxonomy["context_taxonomy"]["resident_runtime"][
                "classes"
            ].remove("main")
            swapped_taxonomy["context_taxonomy"]["dispatch_composition"][
                "classes"
            ].append("main")
            mutations.append(("swapped-taxonomy", swapped_taxonomy))

            for label, mutation in mutations:
                with self.subTest(label=label):
                    with self.assertRaises(ValueError):
                        module.derived_context_budget_limits(mutation)
                    core = copy.deepcopy(module.CORE_CONTRACTS)
                    core["context_budget_contract"] = mutation
                    self.assertTrue(module.validate_core_contracts(core))

    def test_unit_dependency_audit_rejects_workspace_outputs_not_temp_fixture_text(self) -> None:
        with _module_without_tiktoken() as (module, _imports), tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            tests = root / "tests/scripts"
            tests.mkdir(parents=True)
            fixture_only = tests / "test_fixture_only.py"
            fixture_only.write_text(
                "from pathlib import Path\n"
                "def fixture(root: Path) -> None:\n"
                "    (root / 'reports').mkdir()\n"
                "    (root / 'dist/example.txt').write_text('fixture')\n",
                encoding="utf-8",
            )
            contract = {
                "default_layer": "unit",
                "module_overrides": [],
                "unit_dependency_policy": {
                    "forbidden_workspace_roots": ["dist", "reports"],
                    "forbidden_test_layers": [
                        "integration",
                        "contract",
                        "governance",
                        "release",
                    ],
                },
            }
            self.assertEqual(
                [], module.unit_test_dependency_errors(root, contract)
            )

            fixture_only.write_text(
                "from pathlib import Path\n"
                "ROOT = Path(__file__).resolve().parents[2]\n"
                "REPORT = ROOT / 'reports/result.json'\n",
                encoding="utf-8",
            )
            errors = module.unit_test_dependency_errors(root, contract)
            self.assertTrue(any("reports" in item for item in errors), errors)

            integration = tests / "test_integration.py"
            integration.write_text("import unittest\n", encoding="utf-8")
            fixture_only.write_text(
                "import tests.scripts.test_integration\n", encoding="utf-8"
            )
            contract["module_overrides"] = [
                {
                    "module": "tests/scripts/test_integration.py",
                    "layer": "integration",
                }
            ]
            errors = module.unit_test_dependency_errors(root, contract)
            self.assertTrue(any("integration" in item for item in errors), errors)

            import_forms = (
                "from tests.scripts import test_integration\n",
                "from tests.scripts.test_integration import fixture\n",
                "import tests.scripts.test_integration as integration\n",
            )
            for source in import_forms:
                with self.subTest(source=source):
                    fixture_only.write_text(source, encoding="utf-8")
                    errors = module.unit_test_dependency_errors(root, contract)
                    self.assertTrue(
                        any("test_integration.py" in item for item in errors),
                        errors,
                    )

    def test_impact_graph_schema_and_stage_references_fail_closed(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            canonical = copy.deepcopy(module.CORE_CONTRACTS)
            self.assertEqual(
                [], module.validate_impact_graph_contract(canonical, ROOT)
            )
            cases = []
            missing = copy.deepcopy(canonical)
            del missing["impact_graph_contract"]
            cases.append((missing, "impact_graph_contract fields"))
            malformed = copy.deepcopy(canonical)
            malformed["impact_graph_contract"]["rules"][0]["extra"] = True
            cases.append((malformed, "fields must be exactly"))
            unknown = copy.deepcopy(canonical)
            unknown["impact_graph_contract"]["rules"][0]["producer_ids"] = [
                "unknown-producer"
            ]
            cases.append((unknown, "unknown producer"))
            ineligible = copy.deepcopy(canonical)
            eligible = ineligible["impact_graph_contract"]["stages"]["affected"][
                "eligible_producer_ids"
            ]
            producer_id = eligible.pop(0)
            ineligible["impact_graph_contract"]["rules"][0]["producer_ids"] = [
                producer_id
            ]
            cases.append((ineligible, "stage-ineligible"))
            for mutation, expected in cases:
                with self.subTest(expected=expected):
                    errors = module.validate_impact_graph_contract(mutation, ROOT)
                    self.assertTrue(any(expected in item for item in errors), errors)

            release_enabled = copy.deepcopy(canonical)
            policy = release_enabled["impact_graph_contract"]["stages"][
                "affected"
            ]["test_policy"]
            policy["forbidden_layers"].remove("release")
            policy["always_layers"].append("release")
            errors = module.validate_impact_graph_contract(release_enabled, ROOT)
            self.assertTrue(any("release" in item for item in errors), errors)

            duplicate_override = copy.deepcopy(canonical)
            overrides = duplicate_override["impact_graph_contract"]["test_selection"][
                "module_overrides"
            ]
            overrides.append(copy.deepcopy(overrides[0]))
            errors = module.validate_impact_graph_contract(duplicate_override, ROOT)
            self.assertTrue(any("unique" in item for item in errors), errors)

            unknown_layer = copy.deepcopy(canonical)
            unknown_layer["impact_graph_contract"]["test_selection"][
                "module_overrides"
            ][0]["layer"] = "system"
            errors = module.validate_impact_graph_contract(unknown_layer, ROOT)
            self.assertTrue(any("canonical layer" in item for item in errors), errors)

    def test_reference_type_exact_semantic_overrides_are_closed(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            expected = {
                "references/clean-checkout.md": "evidence-pattern",
                "references/execution-report-and-gates.md": "template",
                "references/simplicity-ladder.md": "benchmark-pattern",
            }
            for path, reference_type in expected.items():
                with self.subTest(path=path):
                    self.assertEqual(
                        reference_type,
                        module.reference_type_for_path(path),
                    )
                    self.assertNotEqual(
                        "targeted",
                        module.reference_type_for_path(path),
                    )

            for path in (
                "references/clean-checkout-notes.md",
                "references/execution-report-and-gates-extra.md",
                "references/simplicity-ladder-notes.md",
            ):
                with self.subTest(non_exact_path=path):
                    self.assertEqual(
                        "targeted",
                        module.reference_type_for_path(path),
                    )

    def test_non_token_helpers_import_and_work_without_tiktoken(self) -> None:
        with _module_without_tiktoken() as (module, tiktoken_imports):
            self.assertEqual([], tiktoken_imports)
            self.assertEqual(
                {"routes": [{"name": "example"}]},
                module.load_yaml_text(
                    "routes:\n  - name: example\n",
                    Path("fixture.yaml"),
                ),
            )
            self.assertEqual([], tiktoken_imports)

    def test_token_helper_fails_closed_without_tiktoken(self) -> None:
        with _module_without_tiktoken() as (module, tiktoken_imports):
            with self.assertRaisesRegex(
                RuntimeError,
                "exact o200k_base token counting requires the 'tiktoken' package",
            ) as caught:
                module.count_o200k_base_tokens("exact tokens only")

            self.assertEqual(["tiktoken"], tiktoken_imports)
            self.assertIsInstance(caught.exception.__cause__, ModuleNotFoundError)

    def test_empty_heading_scan_ignores_fenced_fake_headings(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            markdown = """## Example

```markdown
## Fenced Fake
```

## Decision

- Keep the real rule.
"""
            self.assertEqual([], module.empty_markdown_headings(markdown))

    def test_empty_heading_scan_detects_consecutive_headings(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            self.assertEqual(
                [(1, 2, "Empty")],
                module.empty_markdown_headings(
                    "## Empty\n\n### Next\n\n- Decision-bearing content.\n"
                ),
            )

    def test_empty_heading_scan_detects_heading_at_eof(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            self.assertEqual(
                [(1, 2, "Empty At EOF")],
                module.empty_markdown_headings("## Empty At EOF\n\n"),
            )

    def test_empty_heading_scan_treats_html_comments_as_placeholders(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            markdown = """## Placeholder

<!-- template authors fill this section
with decision-bearing content -->

## Complete

Decision rule.
"""
            self.assertEqual(
                [(1, 2, "Placeholder")],
                module.empty_markdown_headings(markdown),
            )

    def test_empty_heading_scan_accepts_authored_content(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            markdown = """# Root

## Decision

<!-- rationale label -->
- Reject the change when its owner is unknown.

## Return

Return the named owner and remaining risk.
"""
            self.assertEqual([], module.empty_markdown_headings(markdown))

    def test_professional_coverage_policy_is_typed_and_canonical(self) -> None:
        with _module_without_tiktoken() as (module, _imports), tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "release-review.yaml"
            path.write_text(
                "schema_version: 2\n"
                "review_owner: maintainers\n"
                'reviewed_at: "2026-07-14"\n'
                "decisions:\n"
                "  - id: release-critical-professional-coverage\n"
                "    kind: professional-coverage-gate\n"
                "    schema_version: 1\n"
                "    requirements:\n"
                "      security-privacy-gate:\n"
                "        - release_critical_covered\n"
                "        - registered\n"
                "expert_content_review_attestation: {}\n",
                encoding="utf-8",
            )
            policy = module.load_professional_coverage_policy(
                path, known_skills={"security-privacy-gate"}
            )
            self.assertEqual(
                ["registered", "release_critical_covered"],
                policy["requirements"]["security-privacy-gate"],
            )
            self.assertEqual(64, len(policy["fingerprint"]["value"]))

            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "        - registered\n",
                    "        - registered\n        - registered\n",
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(module.ValidationProblem, "must not repeat"):
                module.load_professional_coverage_policy(
                    path, known_skills={"security-privacy-gate"}
                )

    def test_professional_coverage_policy_rejects_unknown_target(self) -> None:
        with _module_without_tiktoken() as (module, _imports), tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "release-review.yaml"
            path.write_text(
                "decisions:\n"
                "  - id: release-critical-professional-coverage\n"
                "    kind: professional-coverage-gate\n"
                "    schema_version: 1\n"
                "    requirements:\n"
                "      missing-skill: [registered]\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(module.ValidationProblem, "unknown Skill"):
                module.load_professional_coverage_policy(
                    path, known_skills={"security-privacy-gate"}
                )


class AiReadabilityContractTests(unittest.TestCase):
    @staticmethod
    def _blocking(module: ModuleType, markdown: str) -> list[dict[str, object]]:
        return [
            finding
            for finding in module.ai_readability_findings(markdown, "fixture.md")
            if finding["severity"] == "error"
        ]

    def test_sentence_hard_boundary_accepts_40_and_rejects_41_words(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            accepted = " ".join(["word"] * 40) + "."
            rejected = " ".join(["word"] * 41) + "."

            self.assertEqual([], self._blocking(module, accepted))
            findings = self._blocking(module, rejected)
            self.assertEqual(1, len(findings))
            self.assertEqual("sentence-length", findings[0]["kind"])
            self.assertEqual(41, findings[0]["words"])

    def test_wrapped_list_item_is_one_logical_sentence(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            markdown = "- " + " ".join(["word"] * 25) + "\n  " + " ".join(
                ["word"] * 16
            ) + ".\n"
            findings = self._blocking(module, markdown)
            self.assertEqual(1, len(findings))
            self.assertEqual(1, findings[0]["line"])
            self.assertEqual(41, findings[0]["words"])

    def test_abbreviation_detection_uses_complete_final_token(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            self.assertEqual(
                ["Claims.", "Compare the current result."],
                module._ai_sentence_slices(
                    "Claims. Compare the current result."
                ),
            )
            self.assertEqual(
                ["Ask Dr. Smith for evidence.", "Record the result."],
                module._ai_sentence_slices(
                    "Ask Dr. Smith for evidence. Record the result."
                ),
            )

    def test_non_prose_surfaces_are_exempt(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            long_words = " ".join(["word"] * 50)
            enumeration = ", ".join(f"field{index}" for index in range(50))
            markdown = (
                f"# {long_words}\n\n"
                f"| {long_words} | value |\n"
                "| --- | --- |\n"
                f"```text\n{long_words}\n```\n\n"
                f"python3 script.py {long_words}\n\n"
                f"{enumeration}\n"
            )
            self.assertEqual([], self._blocking(module, markdown))

    def test_inline_code_is_one_atom_and_link_uses_its_label(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            inline = " ".join(["argument"] * 80)
            sentence = f"Use [validator](https://example.test/path) with `{inline}`."
            self.assertEqual(4, module.ai_sentence_word_count(sentence))
            self.assertEqual([], self._blocking(module, sentence))

    def test_compound_bullet_obligations_fail(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            for markdown in (
                "- Validate the input and return the evidence.\n",
                "- Never edit files; never use the network.\n",
                "- Send the diff. Run the check. Return the evidence.\n",
                "- Run only non-modifying checks; never edit the target.\n",
            ):
                with self.subTest(markdown=markdown):
                    findings = self._blocking(module, markdown)
                    self.assertTrue(
                        any(item["kind"] == "bullet-decisions" for item in findings),
                        findings,
                    )

            self.assertEqual(
                [],
                self._blocking(
                    module,
                    "- Verify that denied requests fail and state the proof limit.\n",
                ),
            )
            self.assertEqual(
                [],
                self._blocking(
                    module,
                    "- **Use representative evidence.** Validate the changed boundary.\n",
                ),
            )

    def test_cross_sentence_decision_actions_accumulate(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            for markdown in (
                "- Bind the authority. Reject excess scope.\n",
                "- Record the source. Use independent review.\n",
                "- Define the boundary. Preserve the invariant.\n",
                "- Verify the input. Return the evidence.\n",
            ):
                with self.subTest(markdown=markdown):
                    findings = self._blocking(module, markdown)
                    self.assertTrue(
                        any(item["kind"] == "bullet-decisions" for item in findings),
                        findings,
                    )

    def test_supporting_decision_words_do_not_create_extra_clauses(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            for markdown in (
                "- Verify denied requests fail and state the proof limit.\n",
                "- Inspect the owning source and identify the owner.\n",
                "- Use the report to define the boundary.\n",
                "- The evidence records the owner and preserves the result.\n",
                "- **Use authoritative evidence**: Bind it to the intended operation.\n",
            ):
                with self.subTest(markdown=markdown):
                    self.assertEqual([], self._blocking(module, markdown))

    def test_single_decisions_are_not_split_by_action_like_nouns(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            cases = (
                "- Escalate unresolved ownership to the named reviewer.\n",
                "- Reject unsupported scope at the task boundary.\n",
                "- Route the unresolved decision to its owner.\n",
                "- Stop the task when required evidence is unavailable.\n",
                "- Preserve request, trace, and message identifiers across retries.\n",
                "- Preserve currency, monetary scale, and rounding semantics.\n",
                "- Define stop conditions, boundaries, criteria, signals, and rules.\n",
                "- Prove untrusted input never reaches the privileged sink.\n",
            )
            for markdown in cases:
                with self.subTest(markdown=markdown):
                    self.assertEqual(1, module._ai_decision_clause_count(markdown[2:]))
                    self.assertEqual([], self._blocking(module, markdown))

            for noun_phrase in (
                "Stop conditions describe terminal outcomes.",
                "Stop boundaries describe terminal outcomes.",
                "Stop criteria describe terminal outcomes.",
                "Stop signals describe terminal outcomes.",
                "Stop rules describe terminal outcomes.",
            ):
                with self.subTest(noun_phrase=noun_phrase):
                    self.assertEqual(0, module._ai_decision_clause_count(noun_phrase))

    def test_coordinated_action_like_reference_nouns_remain_one_decision(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            cases = (
                "- Record risks, mitigations, and review owner.\n",
                "- Prove current architecture, rejected option, ADR, and review owner.\n",
                "- Map provider values, strategy drift, and test coverage.\n",
                "- Reconcile current contract and route wiring.\n",
                "- Map read and write query patterns, volumes, and latency needs.\n",
                "- Define review and test evidence for component consistency.\n",
                "- Define owner, allowed implementers, and review process.\n",
                "- Define empty, denied, and load failure states.\n",
                "- Derive priority and scale-down behavior from capacity evidence.\n",
                "- Map redaction and trace propagation to validation commands.\n",
                "- Define required commands and pass criteria.\n",
                "- Define loop prevention and return destination behavior.\n",
                "- Reject snapshot-only and test-only-interface shortcuts.\n",
                "- Route performance and test-portfolio conclusions to specialist owners.\n",
                "- Map the changed guarantee to test/validation evidence.\n",
                "- Map read and write access patterns.\n",
                "- Use current rule evidence; state-machine-modeling applies to lifecycle discovery.\n",
            )
            for markdown in cases:
                with self.subTest(markdown=markdown):
                    self.assertEqual(1, module._ai_decision_clause_count(markdown[2:]))
                    self.assertEqual([], self._blocking(module, markdown))

    def test_contextual_noun_exclusions_do_not_hide_real_commands(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            leading_commands = (
                "Review owner permissions.",
                "Test coverage before release.",
                "Route wiring changes through independent review.",
                "Write query patterns into the design record.",
                "Load failure fixtures before validation.",
                "Scale down behavior after the pressure test.",
                "Return destination behavior to the caller.",
                "Trace propagation across the changed boundary.",
                "Pass criteria to the release owner.",
                "State the machine-modeling decision.",
            )
            for sentence in leading_commands:
                with self.subTest(sentence=sentence):
                    self.assertEqual(1, module._ai_decision_clause_count(sentence))

            coordinated_commands = (
                "- Define the contract and test it.\n",
                "- Map the source and write it to the report.\n",
                "- Inspect the artifact and review it.\n",
                "- Define the boundary and route the request.\n",
                "- Create the fixture and load it.\n",
                "- Measure the workload and scale down the deployment.\n",
                "- Validate ownership and return the result.\n",
                "- Map the signal and trace it.\n",
                "- Define the gate and pass the result to its owner.\n",
            )
            for markdown in coordinated_commands:
                with self.subTest(markdown=markdown):
                    findings = self._blocking(module, markdown)
                    self.assertTrue(
                        any(item["kind"] == "bullet-decisions" for item in findings),
                        findings,
                    )

    def test_expanded_decision_verbs_count_independent_obligations(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            cases = (
                "- Derive the compatibility boundary and remove the unsupported fallback.\n",
                "- Evaluate the failure mode; reconcile the conflicting owner contract.\n",
                "- Protect the tenant boundary. Trace the affected consumer path.\n",
                "- Measure representative load and scale the selected mechanism.\n",
                "- Handle the denied state and maintain the recovery invariant.\n",
            )
            for markdown in cases:
                with self.subTest(markdown=markdown):
                    findings = self._blocking(module, markdown)
                    self.assertTrue(
                        any(item["kind"] == "bullet-decisions" for item in findings),
                        findings,
                    )

    def test_coordinated_define_verify_and_implement_test_are_blocked(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            cases = (
                "- Define the compatibility contract and verify the migration path.\n",
                "- Identify the owning service and select the recovery policy.\n",
                "- Implement the accepted API change and test its rollback path.\n",
                "- Report the accepted result; do not omit its proof limit.\n",
                "- When current evidence conflicts, preserve the invariant and select the safe fallback.\n",
            )
            for markdown in cases:
                with self.subTest(markdown=markdown):
                    findings = self._blocking(module, markdown)
                    self.assertTrue(
                        any(item["kind"] == "bullet-decisions" for item in findings),
                        findings,
                    )

    def test_domain_candidate_selection_and_exception_mix_is_compound(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            real_mobile_rule = (
                "- **Connectivity-dependent flows need explicit degraded behavior**: "
                "when interruption can lose work or create duplicate effects, define "
                "offline, retry, pending, conflict, and user-visible states. Durable "
                "queues, local caches, optimistic state, or explicit online-only "
                "blocking are candidates selected from business semantics and storage "
                "guarantees; not every screen needs offline persistence.\n"
            )
            findings = self._blocking(module, real_mobile_rule)
            self.assertTrue(
                any(item["kind"] == "bullet-decisions" for item in findings),
                findings,
            )

            for markdown in (
                "- Candidate mechanisms depend on current storage guarantees.\n",
                "- Not every screen needs offline persistence.\n",
                "- Select one mechanism from current evidence.\n",
            ):
                with self.subTest(markdown=markdown):
                    self.assertEqual([], self._blocking(module, markdown))

    def test_targeted_reference_checks_load_and_skip_clauses_separately(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            short = (
                "- [checklist](references/checklist.md)\n"
                "  - Load when: cache invalidation changes affect correctness\n"
                "  - Do not load when: no cache behavior changes\n"
                "  - Required by: task-agent\n"
                "  - Required output: checklist-result\n"
            )
            self.assertEqual([], self._blocking(module, short))

            compiled = short.replace(
                "references/checklist.md",
                "cache-design/references/checklist.md",
            )
            self.assertEqual([], self._blocking(module, compiled))

            long_clause = " ".join(["condition"] * 41)
            findings = self._blocking(
                module,
                "- [checklist](references/checklist.md)\n"
                f"  - Load when: {long_clause}\n"
                f"  - Do not load when: {long_clause}\n"
                "  - Required by: task-agent\n"
                "  - Required output: checklist-result\n",
            )
            self.assertEqual(2, len(findings))
            self.assertTrue(
                all(item["kind"] == "sentence-length" for item in findings)
            )

    def test_targeted_reference_labels_are_metadata_but_bodies_remain_governed(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            self.assertEqual(
                [],
                self._blocking(
                    module,
                    "  - Load when: Validate the changed cache boundary.\n"
                    "  - Do not load when: Verify no cache behavior changed.\n"
                    "  - Required by: task-agent\n"
                    "  - Required output: checklist-result\n",
                ),
            )

            compound = self._blocking(
                module,
                "  - Load when: Validate the input and return the evidence.\n",
            )
            self.assertTrue(
                any(item["kind"] == "bullet-decisions" for item in compound),
                compound,
            )
            stop_action = self._blocking(
                module,
                "  - Load when: Validate the input and stop the task.\n",
            )
            self.assertTrue(
                any(item["kind"] == "bullet-decisions" for item in stop_action),
                stop_action,
            )

            long_body = " ".join(["condition"] * 41)
            findings = self._blocking(
                module,
                f"  - Required output: {long_body}\n",
            )
            self.assertEqual(1, len(findings))
            self.assertEqual("sentence-length", findings[0]["kind"])
            self.assertEqual(41, findings[0]["words"])

    def test_professional_and_domain_root_budgets_are_centralized(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            self.assertEqual(
                {
                    "target_words": 550,
                    "hard_words": 650,
                    "target_tokens": 850,
                    "hard_tokens": 1000,
                },
                module.LAYER_ROOT_CONTENT_BUDGETS["professional-skill"],
            )
            self.assertEqual(
                {
                    "target_words": 500,
                    "hard_words": 600,
                    "target_tokens": 800,
                    "hard_tokens": 900,
                },
                module.LAYER_ROOT_CONTENT_BUDGETS["domain-extension"],
            )
            self.assertEqual(
                "governed-body-excluding-registry-targeted-references",
                module.LAYER_ROOT_CONTENT_BUDGET_SCOPE,
            )

    def test_content_budget_classification_uses_closed_boundaries(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            values = {
                "token_count": 700,
                "target_words": 500,
                "hard_words": 600,
                "target_tokens": 800,
                "hard_tokens": 900,
            }
            expected = (
                (500, "KEEP"),
                (501, "REVIEW_DENSITY"),
                (540, "REVIEW_DENSITY"),
                (541, "TIGHTEN_BODY"),
                (600, "TIGHTEN_BODY"),
                (601, "BLOCK"),
            )
            for word_count, classification in expected:
                with self.subTest(word_count=word_count):
                    self.assertEqual(
                        classification,
                        module.classify_content_budget(
                            word_count=word_count,
                            **values,
                        ),
                    )

    def test_only_canonical_registry_projection_is_blankable_metadata(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            canonical = (
                "# Root\n\nDecision text.\n\n## Targeted References\n\n"
                "| Path | Type | Load when | Do not load when | Required by | Required output |\n"
                "|---|---|---|---|---|---|\n"
                "| [checklist](references/checklist.md) | decision-checklist | "
                "cache invalidation changes affect correctness | no cache behavior changes | "
                "task-agent | checklist-result |\n"
            )
            governed = module.strip_registry_targeted_reference_projection(
                canonical
            )
            self.assertEqual(
                len(canonical.splitlines()), len(governed.splitlines())
            )
            self.assertIn("Decision text.", governed)
            self.assertNotIn("cache invalidation", governed)

            bare = canonical.replace(
                "| [checklist](references/checklist.md) | decision-checklist | "
                "cache invalidation changes affect correctness | no cache behavior changes | "
                "task-agent | checklist-result |",
                "- [checklist.md](references/checklist.md)",
            )
            self.assertEqual(
                bare, module.strip_registry_targeted_reference_projection(bare)
            )

            for path in (
                "references/../checklist.md",
                "references//checklist.md",
                "references/./checklist.md",
                " references/checklist.md",
                "references/checklist.md ",
                "references/bad path.md",
                "references/bad[name].md",
                "references/bad(name).md",
                r"references/bad\name.md",
                "references/bad|name.md",
            ):
                with self.subTest(path=path):
                    noncanonical = canonical.replace(
                        "references/checklist.md",
                        path,
                    )
                    self.assertEqual(
                        noncanonical,
                        module.strip_registry_targeted_reference_projection(
                            noncanonical
                        ),
                    )

    def test_compact_table_serializer_has_one_canonical_pipe_escape(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            self.assertEqual(
                "| First | Second |\n|---|---|\n| alpha\\|beta | gamma |",
                module.render_compact_markdown_table(
                    ("First", "Second"),
                    (("alpha|beta", "gamma"),),
                    "fixture",
                ),
            )
            with self.assertRaisesRegex(module.ValidationProblem, "backslashes"):
                module.render_compact_markdown_table(
                    ("First",),
                    ((r"alpha\\beta",),),
                    "fixture",
                )

    def test_projection_stripper_rejects_every_noncanonical_table_shape(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            canonical = (
                "# Root\n\n## Targeted References\n\n"
                "| Path | Type | Load when | Do not load when | Required by | Required output |\n"
                "|---|---|---|---|---|---|\n"
                "| [checklist](references/checklist.md) | decision-checklist | "
                "cache invalidation changes affect correctness | no cache behavior changes | "
                "task-agent | checklist-result |\n"
            )
            row = (
                "| [checklist](references/checklist.md) | decision-checklist | "
                "cache invalidation changes affect correctness | no cache behavior changes | "
                "task-agent | checklist-result |"
            )
            header = (
                "| Path | Type | Load when | Do not load when | Required by | Required output |"
            )
            noncanonical = (
                canonical.replace(
                    "## Targeted References\n\n",
                    "## Targeted References \n\n",
                ),
                canonical.replace(
                    "## Targeted References\n\n",
                    "## Targeted References\n",
                ),
                canonical.replace(
                    "task-agent | checklist-result |",
                    "task-agent, task-agent | checklist-result |",
                ),
                canonical.replace(
                    "checklist-result |",
                    "checklist-result, checklist-result |",
                ),
                canonical.replace("[checklist]", "[custom label]"),
                canonical.replace("Path | Type", "Type | Path"),
                canonical.replace("|---|---|---|---|---|---|", "| --- | --- | --- | --- | --- | --- |"),
                canonical.replace(header, header + " Extra"),
                canonical.replace(" | checklist-result |", " |"),
                canonical.replace(" | checklist-result |", " | checklist-result | extra |"),
                canonical.replace("affect correctness |", "affect | correctness |"),
                canonical.replace("affect correctness |", r"affect \\q correctness |"),
                canonical.replace("affect correctness |", "affect correctness  |"),
                canonical.replace("decision-checklist", "template"),
                canonical.replace(row + "\n", row + "\n" + row + "\n"),
                canonical.replace(row + "\n", ""),
                (
                    "# Root\n\n## Targeted References\n\n"
                    f"{header}\n|---|---|---|---|---|---|\n"
                ),
                (
                    "# Root\n\n## Targeted References\n\n"
                    "- [checklist](references/checklist.md)\n"
                    "  - Load when: cache invalidation changes affect correctness\n"
                    "  - Do not load when: no cache behavior changes\n"
                    "  - Required by: task-agent\n"
                    "  - Required output: checklist-result\n"
                ),
                canonical + canonical.split("## Targeted References\n\n", 1)[1],
                canonical + "\n\n",
            )
            for markdown in noncanonical:
                with self.subTest(markdown=markdown):
                    self.assertEqual(
                        markdown,
                        module.strip_registry_targeted_reference_projection(markdown),
                    )

            sentinel = (
                "# Root\n\n## Targeted References\n\n"
                "- No task-local Reference is indexed for this Skill.\n"
            )
            self.assertNotEqual(
                sentinel,
                module.strip_registry_targeted_reference_projection(sentinel),
            )

    def test_projection_stripper_requires_contextual_exact_terminator(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            table = (
                "## Targeted References\n\n"
                "| Path | Type | Load when | Do not load when | Required by | Required output |\n"
                "|---|---|---|---|---|---|\n"
                "| [checklist](references/checklist.md) | decision-checklist | "
                "cache invalidation changes affect correctness | no cache behavior changes | "
                "task-agent | checklist-result |"
            )
            sentinel = (
                "## Targeted References\n\n"
                "- No task-local Reference is indexed for this Skill."
            )

            for label, core, eof_lines, h2_lines in (
                ("table", table, 5, 6),
                ("sentinel", sentinel, 3, 4),
            ):
                with self.subTest(shape=label, terminator="eof-canonical"):
                    markdown = core + "\n"
                    self.assertNotEqual(
                        markdown,
                        module.strip_registry_targeted_reference_projection(markdown),
                    )
                    self.assertEqual(
                        eof_lines,
                        module.registry_targeted_reference_projection_line_count(markdown),
                    )
                for suffix in ("", "\n\n", "\n\n\n"):
                    with self.subTest(shape=label, terminator=repr(suffix)):
                        markdown = core + suffix
                        self.assertEqual(
                            markdown,
                            module.strip_registry_targeted_reference_projection(markdown),
                        )
                        self.assertEqual(
                            0,
                            module.registry_targeted_reference_projection_line_count(markdown),
                        )

                canonical_h2 = core + "\n\n## Next\n\nDecision.\n"
                with self.subTest(shape=label, terminator="h2-canonical"):
                    stripped = module.strip_registry_targeted_reference_projection(
                        canonical_h2
                    )
                    self.assertNotEqual(canonical_h2, stripped)
                    self.assertIn("## Next\n\nDecision.\n", stripped)
                    self.assertEqual(canonical_h2.count("\n"), stripped.count("\n"))
                    self.assertEqual(
                        h2_lines,
                        module.registry_targeted_reference_projection_line_count(
                            canonical_h2
                        ),
                    )
                for separator in ("", "\n", "\n\n\n"):
                    with self.subTest(shape=label, terminator=f"h2-{separator!r}"):
                        markdown = core + separator + "## Next\n"
                        self.assertEqual(
                            markdown,
                            module.strip_registry_targeted_reference_projection(markdown),
                        )
                        self.assertEqual(
                            0,
                            module.registry_targeted_reference_projection_line_count(markdown),
                        )

    def test_frontmatter_body_projection_requires_proven_raw_source(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            prefix = "---\nname: fixture\ndescription: Fixture.\n---\n"
            table = (
                "## Targeted References\n\n"
                "| Path | Type | Load when | Do not load when | Required by | Required output |\n"
                "|---|---|---|---|---|---|\n"
                "| [checklist](references/checklist.md) | decision-checklist | "
                "cache invalidation changes affect correctness | no cache behavior changes | "
                "task-agent | checklist-result |"
            )
            sentinel = (
                "## Targeted References\n\n"
                "- No task-local Reference is indexed for this Skill."
            )
            for label, projection, eof_lines, h2_lines in (
                ("table", table, 5, 6),
                ("sentinel", sentinel, 3, 4),
            ):
                body = "\n# Root\n\n" + projection
                canonical_source = prefix + body + "\n"
                with self.subTest(shape=label, source="canonical-eof"):
                    governed = (
                        module.strip_frontmatter_body_targeted_reference_projection(
                            body,
                            canonical_source,
                        )
                    )
                    self.assertNotEqual(body, governed)
                    self.assertEqual(len(body.splitlines()), len(governed.splitlines()))
                    self.assertEqual(
                        eof_lines,
                        module.frontmatter_body_targeted_reference_projection_line_count(
                            body,
                            canonical_source,
                        ),
                    )

                for source_label, raw_source in (
                    ("missing-eof", prefix + body),
                    ("double-eof", prefix + body + "\n\n"),
                    (
                        "crlf-source",
                        (prefix + body + "\n").replace("\n", "\r\n"),
                    ),
                    ("fragment-mismatch", prefix + body.replace("# Root", "# Other") + "\n"),
                    ("non-frontmatter", body + "\n"),
                ):
                    with self.subTest(shape=label, source=source_label):
                        self.assertEqual(
                            body,
                            module.strip_frontmatter_body_targeted_reference_projection(
                                body,
                                raw_source,
                            ),
                        )
                        self.assertEqual(
                            0,
                            module.frontmatter_body_targeted_reference_projection_line_count(
                                body,
                                raw_source,
                            ),
                        )

                h2_body = body + "\n\n## Next\n\nDecision."
                h2_source = prefix + h2_body + "\n"
                with self.subTest(shape=label, source="canonical-before-h2"):
                    governed = (
                        module.strip_frontmatter_body_targeted_reference_projection(
                            h2_body,
                            h2_source,
                        )
                    )
                    self.assertNotEqual(h2_body, governed)
                    self.assertIn("## Next\n\nDecision.", governed)
                    self.assertEqual(
                        h2_lines,
                        module.frontmatter_body_targeted_reference_projection_line_count(
                            h2_body,
                            h2_source,
                        ),
                    )

    def test_raw_text_reader_preserves_on_disk_newline_sequences(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            with tempfile.TemporaryDirectory() as raw:
                path = Path(raw) / "fixture.md"
                source = "alpha\r\nbeta\ngamma\r"
                path.write_bytes(source.encode("utf-8"))

                self.assertEqual(source, module.read_text_preserve_newlines(path))


class Repair177OccurrenceMatcherValidationRedTests(unittest.TestCase):
    MATCHER_FIELDS = (
        "contract",
        "rollout",
        "action",
        "combine",
        "relations",
    )
    RELATION_FIELDS = (
        "atom",
        "operator",
        "scope",
        "actions",
        "objects",
        "owner_relation",
        "non_owner_modifiers",
    )
    OWNER_RELATION_FIELDS = ("mode", "qualifiers")
    BUSINESS_OBJECTS = [
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
    STATE_OBJECTS = [
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

    @classmethod
    def _matcher(
        cls,
        *,
        atom: str,
        actions: list[str],
        objects: list[str],
        mode: str,
        modifiers: list[str],
    ) -> dict[str, object]:
        return {
            "contract": "foundation-occurrence-matcher/v1",
            "rollout": "enabled",
            "action": "analysis-only",
            "combine": "any",
            "relations": [
                {
                    "atom": atom,
                    "operator": "governed-object-occurrence",
                    "scope": "bounded-clause",
                    "actions": actions,
                    "objects": objects,
                    "owner_relation": {
                        "mode": mode,
                        "qualifiers": ["business", "domain"],
                    },
                    "non_owner_modifiers": modifiers,
                }
            ],
        }

    @classmethod
    def _business_matcher(cls) -> dict[str, object]:
        return cls._matcher(
            atom="business-rule-occurrence",
            actions=["analyze", "analyse", "extract"],
            objects=list(cls.BUSINESS_OBJECTS),
            mode="intrinsic-qualified-object",
            modifiers=["accepted", "current", "existing", "material"],
        )

    @classmethod
    def _state_matcher(cls) -> dict[str, object]:
        return cls._matcher(
            atom="state-machine-occurrence",
            actions=["analyze", "analyse", "model"],
            objects=list(cls.STATE_OBJECTS),
            mode="immediate-qualified-subject",
            modifiers=[
                "accepted",
                "current",
                "existing",
                "material",
                "proposed",
                "target",
            ],
        )

    def test_repair177_occurrence_matcher_closed_schema_matrix(self) -> None:
        with _module_without_tiktoken() as (module, _imports):
            validator = getattr(
                module,
                "_foundation_runtime_matcher_errors",
                None,
            )
            self.assertTrue(
                callable(validator),
                "the existing private matcher-schema owner must remain reused",
            )
            if not callable(validator):
                return

            business = self._business_matcher()
            state = self._state_matcher()
            self.assertEqual(
                [],
                validator(
                    copy.deepcopy(business),
                    ["business-rule-occurrence"],
                    "repair177.business",
                ),
            )
            self.assertEqual(
                [],
                validator(
                    copy.deepcopy(state),
                    ["state-machine-occurrence"],
                    "repair177.state",
                ),
            )
            combined = copy.deepcopy(business)
            combined["relations"].append(
                copy.deepcopy(state["relations"][0])
            )
            combined_atoms = [
                "business-rule-occurrence",
                "state-machine-occurrence",
            ]
            self.assertEqual(
                [],
                validator(
                    copy.deepcopy(combined),
                    combined_atoms,
                    "repair177.combined-selected-rows",
                ),
                "the validator must select each relation's own vocabulary "
                "instead of one union/global list",
            )
            self.assertEqual(
                self.MATCHER_FIELDS,
                tuple(business),
            )
            self.assertEqual(
                self.RELATION_FIELDS,
                tuple(business["relations"][0]),
            )
            self.assertEqual(
                self.OWNER_RELATION_FIELDS,
                tuple(business["relations"][0]["owner_relation"]),
            )

            cases: list[tuple[str, object, list[str], tuple[str, ...]]] = []

            cases.append(
                (
                    "matcher-nonmapping",
                    "not-a-mapping",
                    ["business-rule-occurrence"],
                    ("mapping",),
                )
            )
            for field in self.MATCHER_FIELDS:
                value = copy.deepcopy(business)
                del value[field]
                cases.append(
                    (
                        f"matcher-missing-{field}",
                        value,
                        ["business-rule-occurrence"],
                        (field, "required"),
                    )
                )
            value = copy.deepcopy(business)
            value["unexpected"] = "closed"
            cases.append(
                (
                    "matcher-unknown",
                    value,
                    ["business-rule-occurrence"],
                    ("unexpected", "unknown"),
                )
            )
            value = {
                field: copy.deepcopy(business[field])
                for field in reversed(self.MATCHER_FIELDS)
            }
            cases.append(
                (
                    "matcher-reordered",
                    value,
                    ["business-rule-occurrence"],
                    ("field order",),
                )
            )
            for field, invalid in (
                ("contract", "foundation-occurrence-matcher/v2"),
                ("rollout", "disabled"),
                ("action", "implementation"),
                ("combine", "all"),
            ):
                value = copy.deepcopy(business)
                value[field] = invalid
                cases.append(
                    (
                        f"matcher-wrong-{field}",
                        value,
                        ["business-rule-occurrence"],
                        (field,),
                    )
                )

            for label, relations in (
                ("relations-nonlist", {}),
                ("relations-empty", []),
                (
                    "relations-oversized",
                    copy.deepcopy(business["relations"]) * 2,
                ),
                ("relation-nonmapping", ["not-a-mapping"]),
            ):
                value = copy.deepcopy(business)
                value["relations"] = relations
                cases.append(
                    (
                        label,
                        value,
                        ["business-rule-occurrence"],
                        ("relations",),
                    )
                )

            for field in self.RELATION_FIELDS:
                value = copy.deepcopy(business)
                del value["relations"][0][field]
                cases.append(
                    (
                        f"relation-missing-{field}",
                        value,
                        ["business-rule-occurrence"],
                        (field, "required"),
                    )
                )
            value = copy.deepcopy(business)
            value["relations"][0]["unexpected"] = "closed"
            cases.append(
                (
                    "relation-unknown",
                    value,
                    ["business-rule-occurrence"],
                    ("unexpected", "unknown"),
                )
            )
            value = copy.deepcopy(business)
            relation = value["relations"][0]
            value["relations"][0] = {
                field: relation[field]
                for field in reversed(self.RELATION_FIELDS)
            }
            cases.append(
                (
                    "relation-reordered",
                    value,
                    ["business-rule-occurrence"],
                    ("field order",),
                )
            )

            for label, atoms, mutation in (
                (
                    "atom-misaligned",
                    ["other-occurrence"],
                    lambda value: None,
                ),
                (
                    "atom-duplicate",
                    [
                        "business-rule-occurrence",
                        "business-rule-occurrence",
                    ],
                    lambda value: value["relations"].append(
                        copy.deepcopy(value["relations"][0])
                    ),
                ),
                (
                    "atom-out-of-order",
                    [
                        "state-machine-occurrence",
                        "business-rule-occurrence",
                    ],
                    lambda value: (
                        value["relations"].append(
                            copy.deepcopy(value["relations"][0])
                        ),
                        value["relations"][0].__setitem__(
                            "atom",
                            "business-rule-occurrence",
                        ),
                        value["relations"][1].__setitem__(
                            "atom",
                            "state-machine-occurrence",
                        ),
                    ),
                ),
            ):
                value = copy.deepcopy(business)
                mutation(value)
                cases.append((label, value, atoms, ("atom",)))

            for field, invalid in (
                ("operator", "substring"),
                ("scope", "whole-prompt"),
            ):
                value = copy.deepcopy(business)
                value["relations"][0][field] = invalid
                cases.append(
                    (
                        f"relation-wrong-{field}",
                        value,
                        ["business-rule-occurrence"],
                        (field,),
                    )
                )

            for field, invalid, fragments in (
                ("actions", {}, ("actions", "list")),
                ("actions", [], ("actions", "non-empty")),
                (
                    "actions",
                    ["analyze", "analyze"],
                    ("actions", "duplicate"),
                ),
                (
                    "actions",
                    ["Analyze"],
                    ("actions", "normalized"),
                ),
                (
                    "actions",
                    ["review"],
                    ("actions",),
                ),
                (
                    "actions",
                    ["analyze", "analyse", "extract", "model"],
                    ("actions",),
                ),
                ("objects", {}, ("objects", "list")),
                ("objects", [], ("objects", "non-empty")),
                (
                    "objects",
                    [
                        self.BUSINESS_OBJECTS[0],
                        self.BUSINESS_OBJECTS[0],
                    ],
                    ("objects", "duplicate"),
                ),
                (
                    "objects",
                    ["Business invariant"],
                    ("objects", "normalized"),
                ),
                (
                    "objects",
                    self.BUSINESS_OBJECTS + ["domain decision authorities"],
                    ("objects",),
                ),
                (
                    "objects",
                    self.STATE_OBJECTS,
                    ("objects",),
                ),
            ):
                value = copy.deepcopy(business)
                value["relations"][0][field] = invalid
                cases.append(
                    (
                        f"relation-invalid-{field}-{len(cases)}",
                        value,
                        ["business-rule-occurrence"],
                        fragments,
                    )
                )

            owner_path = "owner_relation"
            for field in self.OWNER_RELATION_FIELDS:
                value = copy.deepcopy(business)
                del value["relations"][0][owner_path][field]
                cases.append(
                    (
                        f"owner-missing-{field}",
                        value,
                        ["business-rule-occurrence"],
                        (owner_path, field, "required"),
                    )
                )
            for label, owner, fragments in (
                ("owner-nonmapping", [], (owner_path, "mapping")),
                (
                    "owner-unknown",
                    {
                        "mode": "intrinsic-qualified-object",
                        "qualifiers": ["business", "domain"],
                        "unexpected": True,
                    },
                    ("unexpected", "unknown"),
                ),
                (
                    "owner-reordered",
                    {
                        "qualifiers": ["business", "domain"],
                        "mode": "intrinsic-qualified-object",
                    },
                    (owner_path, "field order"),
                ),
                (
                    "owner-mode",
                    {
                        "mode": "remote-qualified-object",
                        "qualifiers": ["business", "domain"],
                    },
                    ("mode",),
                ),
                (
                    "qualifiers-nonlist",
                    {
                        "mode": "intrinsic-qualified-object",
                        "qualifiers": {},
                    },
                    ("qualifiers", "list"),
                ),
                (
                    "qualifiers-empty",
                    {
                        "mode": "intrinsic-qualified-object",
                        "qualifiers": [],
                    },
                    ("qualifiers", "non-empty"),
                ),
                (
                    "qualifiers-duplicate",
                    {
                        "mode": "intrinsic-qualified-object",
                        "qualifiers": ["business", "business"],
                    },
                    ("qualifiers", "duplicate"),
                ),
                (
                    "qualifiers-reordered",
                    {
                        "mode": "intrinsic-qualified-object",
                        "qualifiers": ["domain", "business"],
                    },
                    ("qualifiers", "order"),
                ),
                (
                    "qualifiers-workflow",
                    {
                        "mode": "intrinsic-qualified-object",
                        "qualifiers": ["business", "workflow"],
                    },
                    ("qualifiers",),
                ),
                (
                    "qualifiers-product",
                    {
                        "mode": "intrinsic-qualified-object",
                        "qualifiers": ["business", "product"],
                    },
                    ("qualifiers",),
                ),
            ):
                value = copy.deepcopy(business)
                value["relations"][0][owner_path] = owner
                cases.append(
                    (
                        label,
                        value,
                        ["business-rule-occurrence"],
                        fragments,
                    )
                )

            value = copy.deepcopy(business)
            value["relations"][0]["objects"][0] = "invariant"
            cases.append(
                (
                    "business-object-unqualified",
                    value,
                    ["business-rule-occurrence"],
                    ("objects",),
                )
            )
            value = copy.deepcopy(state)
            value["relations"][0]["owner_relation"]["mode"] = (
                "intrinsic-qualified-object"
            )
            cases.append(
                (
                    "state-intrinsic-mode",
                    value,
                    ["state-machine-occurrence"],
                    ("mode",),
                )
            )
            value = copy.deepcopy(state)
            value["relations"][0]["owner_relation"]["qualifiers"] = [
                "business",
                "workflow",
            ]
            cases.append(
                (
                    "state-workflow-owner",
                    value,
                    ["state-machine-occurrence"],
                    ("qualifiers",),
                )
            )

            for label, modifiers, fragments in (
                ("modifiers-nonlist", {}, ("non_owner_modifiers", "list")),
                (
                    "modifiers-duplicate",
                    ["accepted", "accepted"],
                    ("non_owner_modifiers", "duplicate"),
                ),
                (
                    "modifiers-nonnormalized",
                    ["Accepted"],
                    ("non_owner_modifiers", "normalized"),
                ),
                (
                    "modifiers-reordered",
                    ["current", "accepted", "existing", "material"],
                    ("non_owner_modifiers",),
                ),
                (
                    "modifiers-oversized",
                    [
                        "accepted",
                        "current",
                        "existing",
                        "material",
                        "proposed",
                    ],
                    ("non_owner_modifiers",),
                ),
                (
                    "modifiers-unknown",
                    ["accepted", "current", "existing", "revised"],
                    ("non_owner_modifiers",),
                ),
            ):
                value = copy.deepcopy(business)
                value["relations"][0]["non_owner_modifiers"] = modifiers
                cases.append(
                    (
                        label,
                        value,
                        ["business-rule-occurrence"],
                        fragments,
                    )
                )

            state_selected_cases = (
                (
                    "state-selected-modifiers-missing",
                    "non_owner_modifiers",
                    [
                        "accepted",
                        "current",
                        "existing",
                        "material",
                        "proposed",
                    ],
                    ("relations[1].non_owner_modifiers",),
                ),
                (
                    "state-selected-modifiers-reordered",
                    "non_owner_modifiers",
                    [
                        "current",
                        "accepted",
                        "existing",
                        "material",
                        "proposed",
                        "target",
                    ],
                    ("relations[1].non_owner_modifiers",),
                ),
                (
                    "state-selected-modifiers-duplicate",
                    "non_owner_modifiers",
                    [
                        "accepted",
                        "current",
                        "existing",
                        "material",
                        "proposed",
                        "accepted",
                    ],
                    ("relations[1].non_owner_modifiers", "duplicate"),
                ),
                (
                    "state-selected-modifiers-extra",
                    "non_owner_modifiers",
                    [
                        "accepted",
                        "current",
                        "existing",
                        "material",
                        "proposed",
                        "target",
                        "revised",
                    ],
                    ("relations[1].non_owner_modifiers",),
                ),
                (
                    "state-selected-actions-nonlist",
                    "actions",
                    {},
                    ("relations[1].actions", "list"),
                ),
                (
                    "state-selected-actions-empty",
                    "actions",
                    [],
                    ("relations[1].actions", "non-empty"),
                ),
                (
                    "state-selected-actions-reordered",
                    "actions",
                    ["analyse", "analyze", "model"],
                    ("relations[1].actions",),
                ),
                (
                    "state-selected-actions-duplicate",
                    "actions",
                    ["analyze", "analyse", "analyze"],
                    ("relations[1].actions", "duplicate"),
                ),
                (
                    "state-selected-actions-extra",
                    "actions",
                    ["analyze", "analyse", "model", "extract"],
                    ("relations[1].actions",),
                ),
                (
                    "state-selected-objects-nonlist",
                    "objects",
                    {},
                    ("relations[1].objects", "list"),
                ),
                (
                    "state-selected-objects-empty",
                    "objects",
                    [],
                    ("relations[1].objects", "non-empty"),
                ),
                (
                    "state-selected-objects-reordered",
                    "objects",
                    [
                        self.STATE_OBJECTS[1],
                        self.STATE_OBJECTS[0],
                        *self.STATE_OBJECTS[2:],
                    ],
                    ("relations[1].objects",),
                ),
                (
                    "state-selected-objects-duplicate",
                    "objects",
                    [
                        self.STATE_OBJECTS[0],
                        self.STATE_OBJECTS[0],
                        *self.STATE_OBJECTS[2:],
                    ],
                    ("relations[1].objects", "duplicate"),
                ),
                (
                    "state-selected-objects-extra",
                    "objects",
                    [*self.STATE_OBJECTS, "workflow state"],
                    ("relations[1].objects",),
                ),
            )
            for label, field, invalid, fragments in state_selected_cases:
                value = copy.deepcopy(combined)
                value["relations"][1][field] = invalid
                cases.append((label, value, combined_atoms, fragments))

            violations: list[str] = []
            for label, value, atoms, fragments in cases:
                errors = validator(value, atoms, f"repair177.{label}")
                diagnostic = "; ".join(errors)
                if not errors:
                    violations.append(f"{label}: malformed schema was accepted")
                    continue
                missing = [
                    fragment
                    for fragment in fragments
                    if fragment not in diagnostic
                ]
                if missing:
                    violations.append(
                        f"{label}: missing diagnostics {missing!r}: "
                        f"{diagnostic!r}"
                    )
                if (
                    label.startswith("state-selected-")
                    and ".relations[0]" in diagnostic
                ):
                    violations.append(
                        f"{label}: State-row mutation leaked a diagnostic "
                        f"onto the valid Business row: {diagnostic!r}"
                    )
            self.assertEqual([], violations)


if __name__ == "__main__":
    unittest.main()
