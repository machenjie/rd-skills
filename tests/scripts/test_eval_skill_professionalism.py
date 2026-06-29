from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "eval-skill-professionalism.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("eval_skill_professionalism", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class EvalSkillProfessionalismTests(unittest.TestCase):
    def _write_skill(self, root: Path, body: str) -> Path:
        skill_dir = root / "sample-skill"
        skill_dir.mkdir(parents=True)
        path = skill_dir / "SKILL.md"
        path.write_text(
            "\n".join(
                [
                    "---",
                    "name: sample-skill",
                    "description: Sample skill for professionalism eval tests.",
                    "license: MIT",
                    "changeforge_kind: professional-skill",
                    "changeforge_version: 0.1.0",
                    "---",
                    "",
                    "# Sample Skill",
                    "",
                    body,
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        return path

    def test_authoring_template_paths_are_excluded_from_runtime_eval(self) -> None:
        module = _load_module()
        self.assertTrue(
            module._is_authoring_template_path(
                ROOT / "src" / "foundation" / "capabilities" / "_template" / "SKILL.md"
            )
        )
        self.assertFalse(
            module._is_authoring_template_path(
                ROOT / "src" / "foundation" / "capabilities" / "cache-design" / "SKILL.md"
            )
        )

    def test_missing_mode_matrix_professional_skill_warns(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_skill(
                Path(tmp),
                "\n".join(
                    [
                        "## Mission",
                        "Evaluate a focused behavior.",
                        "## When To Use",
                        "Use when a concrete signal appears.",
                        "## Do Not Use When",
                        "Do not use for unrelated work.",
                        "## Output Contract",
                        "Return validation evidence and residual risk.",
                        "## Failure Modes",
                        "- Missing the hidden risk.",
                        "## Quality Gate",
                        "Passes when evidence is present.",
                    ]
                ),
            )
            item = module._evaluate_skill(path, "professional-skill", set())
        self.assertIn("Mode Matrix", item.likely_missing_sections)
        self.assertTrue(any("missing Mode Matrix" in warning for warning in item.warnings))
        warning = next(warning for warning in item.warnings if "missing Mode Matrix" in warning.message)
        self.assertEqual(warning.scope, "professional-skill")
        self.assertEqual(warning.release_relevance, "release-blocking")
        self.assertEqual(warning.item_kind, "professional-skill")

    def test_non_key_foundation_capability_does_not_require_professional_skill_sections(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_skill(
                Path(tmp),
                "\n".join(
                    [
                        "## Mission",
                        "Guide a focused support capability.",
                        "## When To Use",
                        "Use when a concrete support signal appears.",
                        "## Do Not Use When",
                        "Do not use for top-level routing behavior.",
                        "## Output Contract",
                        "Return decision scope, output evidence, and handoff notes.",
                        "## Failure Modes",
                        "- Missing the support boundary.",
                        "- Treating a support capability as a runtime professional skill.",
                        "- Handing off without evidence.",
                        "## Quality Gate",
                        "Passes when the output evidence and handoff are explicit.",
                    ]
                ),
            )
            item = module._evaluate_skill(path, "foundation-capability", set())
        self.assertNotIn("Mode Matrix", item.likely_missing_sections)
        self.assertNotIn("Proactive Professional Triggers", item.likely_missing_sections)
        self.assertNotIn("Evidence Contract", item.likely_missing_sections)
        self.assertNotIn("Reference Loading Policy", item.likely_missing_sections)

    def test_mode_matrix_without_evidence_warns(self) -> None:
        module = _load_module()
        body = "\n".join(
            [
                "| Mode | Trigger signals | Professional focus | Companion capabilities |",
                "| --- | --- | --- | --- |",
                "| Coding | code change | implement locally | `code-review` |",
                "| Testing | tests | run tests | `test-strategy` |",
                "| Review | PR | review | `code-review` |",
                "| Release | deploy | ship | `release-rollback` |",
            ]
        )
        warning = module._mode_matrix_warning(body)
        self.assertIsNotNone(warning)
        self.assertIn("required professional columns", warning)

    def test_section_only_fake_mode_matrix_does_not_score_high(self) -> None:
        module = _load_module()
        sections = {"Stage Fit": "", "Selection Rules": ""}
        score = module._score_mode_coverage(
            "\n".join(
                [
                    "This section says Mode Matrix but only lists professional words.",
                    "",
                    "| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities / gates | Skip guidance |",
                    "| --- | --- | --- | --- | --- | --- |",
                    "| Coding | do work | be professional | evidence | gate | skip if not needed |",
                    "| Review | check things | be careful | evidence | gate | skip if not needed |",
                    "| Testing | add tests | ensure quality | run tests | gate | skip if not needed |",
                    "| Release | ship safely | robust solution | validation | gate | skip if not needed |",
                ]
            ),
            sections,
            "professional-skill",
            ROOT / "src" / "professional-skills" / "sample" / "SKILL.md",
        )
        self.assertLessEqual(score, 2)

    def test_proactive_trigger_quality_requires_hidden_risk_route_and_evidence(self) -> None:
        module = _load_module()
        trigger = "\n".join(
            [
                "- **Signal:** repository resource query uses an id without tenant scope.",
                "  **Hidden risk:** tenant IDOR data leak from identifier-only repository query.",
                "  **Required professional action:** inspect controller, service, repository, and permission policy ownership.",
                "  **Route to:** `permission-boundary-modeling`.",
                "  **Evidence required:** denied cross-tenant regression test output.",
            ]
            * 5
        )
        self.assertEqual(module._score_proactive_trigger_quality(trigger, "professional-skill"), 5)
        self.assertEqual(module._trigger_quality_warnings(trigger, {"permission-boundary-modeling"}), [])

    def test_checklist_only_trigger_skill_scores_low(self) -> None:
        module = _load_module()
        trigger = "\n".join(
            [
                "- **Signal:** check security.",
                "  **Hidden risk:** quality risk.",
                "  **Required professional action:** add tests.",
                "  **Route to:** `quality-test-gate`.",
                "  **Evidence required:** run tests.",
            ]
            * 5
        )
        self.assertLessEqual(module._score_proactive_trigger_quality(trigger, "professional-skill"), 2)
        warnings = module._trigger_quality_warnings(trigger, {"quality-test-gate"})
        self.assertTrue(any("too generic" in warning for warning in warnings))

    def test_valid_backend_like_sample_scores_above_fake_skill(self) -> None:
        module = _load_module()
        fake_trigger = "\n".join(
            [
                "- **Signal:** add tests.",
                "  **Hidden risk:** quality risk.",
                "  **Required professional action:** check things.",
                "  **Route to:** `quality-test-gate`.",
                "  **Evidence required:** run tests.",
            ]
            * 3
        )
        valid_trigger = "\n".join(
            [
                "- **Signal:** repository lookup fetches an invoice by id without tenant filter.",
                "  **Hidden risk:** tenant data leak from identifier-only query.",
                "  **Required professional action:** inspect controller, service, repository, and permission policy boundaries.",
                "  **Route to:** `backend-change-builder`, `permission-boundary-modeling`, `regression-testing`.",
                "  **Evidence required:** denied cross-tenant regression test and same-pattern query scan output.",
                "- **Signal:** queue consumer mutates order state before acknowledging the message.",
                "  **Hidden risk:** duplicate fulfillment from retry or redelivery.",
                "  **Required professional action:** require idempotency key, durable write boundary, and replay path.",
                "  **Route to:** `idempotency-retry-design`, `message-queue-design`.",
                "  **Evidence required:** duplicate delivery test and DLQ/replay command evidence.",
                "- **Signal:** migration removes a column while old pods may still read it.",
                "  **Hidden risk:** rolling deploy version skew breaks the API contract.",
                "  **Required professional action:** model expand-contract rollout and rollback boundary.",
                "  **Route to:** `release-rollback`, `data-migration-design`.",
                "  **Evidence required:** forward and rollback migration validation command output.",
            ]
        )
        self.assertGreater(
            module._score_proactive_trigger_quality(valid_trigger, "professional-skill"),
            module._score_proactive_trigger_quality(fake_trigger, "professional-skill") + 2,
        )

    def test_trigger_warning_flags_checklist_without_route_evidence(self) -> None:
        module = _load_module()
        warnings = module._trigger_quality_warnings("- checklist: add tests when code changes", set())
        self.assertTrue(warnings)
        self.assertTrue(any("too few" in warning for warning in warnings))

    def test_trigger_warning_flags_missing_hidden_risk_route_and_evidence(self) -> None:
        module = _load_module()
        trigger = (
            "- **Signal:** generated helper.\n"
            "  **Required professional action:** verify symbol."
        )
        warnings = module._trigger_quality_warnings(trigger, {"code-review"})
        self.assertTrue(any("hidden risk" in warning for warning in warnings))
        self.assertTrue(any("route to" in warning for warning in warnings))
        self.assertTrue(any("evidence required" in warning for warning in warnings))

    def test_trigger_warning_flags_unknown_route(self) -> None:
        module = _load_module()
        trigger = (
            "- **Signal:** generated helper.\n"
            "  **Hidden risk:** invented API.\n"
            "  **Required professional action:** verify symbol.\n"
            "  **Route to:** `missing-capability`.\n"
            "  **Evidence required:** typecheck output."
        )
        warnings = module._trigger_quality_warnings(trigger, {"code-review"})
        self.assertTrue(any("unknown" in warning for warning in warnings))

    def test_evidence_contract_alias_is_extracted(self) -> None:
        module = _load_module()
        body = "# Evidence Contract Answer Set\n\n- Basis\n"
        self.assertIn("Basis", module._extract_section(body, "Evidence Contract"))

    def test_copied_template_evidence_contract_lacks_professional_depth(self) -> None:
        module = _load_module()
        sections = {
            "Failure Modes": "- Generic failure.",
            "Quality Gate": "Passes when quality is ensured.",
        }
        body = "\n".join(
            [
                "## Mission",
                "Apply professional best practices.",
                "## Evidence Contract",
                "- Boundaries inspected: describe boundaries.",
                "- Validation evidence: provide validation evidence.",
                "- What evidence proves: quality.",
                "- What evidence does not prove: everything.",
                "- Residual risk: state residual risk.",
                "- Next gate: state next gate.",
                "- Reuse / placement rationale: state rationale.",
                "- Behavior preservation: state behavior preservation.",
                "Use robust solution guidance where appropriate and ensure quality as needed.",
            ]
        )
        self.assertLessEqual(module._score_professional_depth(body, sections), 2)
        self.assertLessEqual(
            module._score_evidence_contract_strength(
                module._extract_section(body, "Evidence Contract"),
                "professional-skill",
                ROOT / "src" / "professional-skills" / "sample" / "SKILL.md",
            ),
            3,
        )

    def test_bloated_skill_without_reference_loading_hint_loses_anti_bloat_points(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_skill(
                Path(tmp),
                "\n".join(
                    [
                        "## Mission",
                        "Evaluate a focused backend behavior.",
                        "## When To Use",
                        "Use for a repository query and tenant permission boundary.",
                        "## Do Not Use When",
                        "Do not use for unrelated work.",
                        "## Evidence Contract",
                        "- Boundaries inspected: repository and permission policy.",
                    ]
                    + [f"- Long example line {index}: repeat benchmark-like content." for index in range(360)]
                ),
            )
            refs = path.parent / "references"
            refs.mkdir()
            (refs / "deep-check.md").write_text("# Deep Check\n", encoding="utf-8")
            _metadata, _raw, body = module.parse_frontmatter(path)
            sections = {"Reference Loading Policy": "", "Evidence Contract": "x" * 2000}
            score = module._score_anti_bloat(body, "professional-skill", "", sections, path)
        self.assertLessEqual(score, 2)

    def test_minimal_correctness_terms_affect_anti_bloat_score(self) -> None:
        module = _load_module()
        strong = "\n".join(
            [
                "existence challenge",
                "simplicity ladder",
                "standard library native existing repository installed dependency local direct",
                "new dependency one implementation delete shrink yagni",
                "shortcut ceiling upgrade trigger validation evidence residual risk",
            ]
        )
        weak = "minimal code with less text"
        self.assertGreaterEqual(module._minimal_correctness_term_hits(strong), 15)
        self.assertLess(module._minimal_correctness_term_hits(weak), 7)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "minimal-correct-implementation" / "SKILL.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                "---\n"
                "name: minimal-correct-implementation\n"
                "description: Minimal correctness test fixture.\n"
                "license: MIT\n"
                "changeforge_kind: foundation-capability\n"
                "changeforge_version: 0.1.0\n"
                "---\n"
                "# Minimal Correct Implementation\n",
                encoding="utf-8",
            )
            sections = {"Reference Loading Policy": "", "Evidence Contract": ""}
            strong_score = module._score_anti_bloat(
                strong,
                "foundation-capability",
                "",
                sections,
                path,
            )
            weak_score = module._score_anti_bloat(
                weak,
                "foundation-capability",
                "",
                sections,
                path,
            )
        self.assertGreater(strong_score, weak_score)

    def test_reference_file_without_loading_hint_warns(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_skill(
                Path(tmp),
                "\n".join(
                    [
                        "## Mission",
                        "Evaluate a focused behavior.",
                        "## When To Use",
                        "Use when a concrete signal appears.",
                        "## Do Not Use When",
                        "Do not use for unrelated work.",
                        "## Mode Matrix",
                        "| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |",
                        "| --- | --- | --- | --- | --- | --- |",
                        "| Coding | signal | focus | evidence | `code-review` | skip deep release |",
                        "| Testing | signal | focus | evidence | `test-strategy` | skip release |",
                        "| Review | signal | focus | evidence | `code-review` | skip release |",
                        "| Release | signal | focus | evidence | `release-rollback` | skip coding |",
                        "## Output Contract",
                        "Return validation evidence and residual risk.",
                        "## Failure Modes",
                        "- Missing the hidden risk.",
                        "## Quality Gate",
                        "Passes when evidence is present.",
                    ]
                ),
            )
            refs = path.parent / "references"
            refs.mkdir()
            (refs / "deep-check.md").write_text("# Deep Check\n", encoding="utf-8")
            item = module._evaluate_skill(path, "professional-skill", {"code-review", "test-strategy", "release-rollback"})
        self.assertTrue(any("lacks a reference loading hint" in warning for warning in item.warnings))

    def test_main_writes_markdown_json_reports_and_remains_warning_only(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            exit_code = module.main(["--reports-dir", tmp])
            reports = Path(tmp)
            self.assertEqual(exit_code, 0)
            self.assertTrue((reports / "skill-professionalism-eval.md").is_file())
            self.assertTrue((reports / "skill-professionalism-eval.json").is_file())
            self.assertTrue((reports / "professional-coverage-matrix.md").is_file())
            self.assertTrue((reports / "professional-coverage-matrix.json").is_file())
            matrix = json.loads((reports / "professional-coverage-matrix.json").read_text(encoding="utf-8"))
            router = next(row for row in matrix["rows"] if row["name"] == "change-forge-router")
            self.assertTrue(router["routing_coverage"].startswith("n/a (router owns routing fixture corpus"))
            self.assertTrue(router["benchmark_coverage"].startswith("n/a (covered by eval-routing"))

    def test_benchmark_coverage_counts_codegen_route_hints(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            professional_dir = root / "professional-benchmarks"
            codegen_case = root / "codegen" / "code-elements" / "sample"
            codegen_case.mkdir(parents=True)
            (codegen_case / "expected-qualities.yaml").write_text(
                "\n".join(
                    [
                        "route_hints:",
                        "  skills:",
                        "    - quality-test-gate",
                        "  capabilities:",
                        "    - code-element-professionalism",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            with patch.object(module, "PROFESSIONAL_BENCHMARKS_DIR", professional_dir), patch.object(
                module,
                "CODEGEN_BENCHMARKS_DIR",
                root / "codegen",
            ):
                counts = module._coverage_counts_from_benchmarks()

        self.assertEqual(counts["quality-test-gate"], 1)
        self.assertEqual(counts["code-element-professionalism"], 1)


if __name__ == "__main__":
    unittest.main()
