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

    def test_foundation_depth_recognizes_capability_alias_sections(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_skill(
                Path(tmp),
                "\n".join(
                    [
                        "## Mission",
                        "Return a focused support decision with validation evidence and residual risk.",
                        "## Capability Boundary",
                        "`sample-skill` returns an owner-returned fragment to backend-change-builder. It does not replace the selected professional owner, decide top-level scope, or close unrelated work.",
                        "## Load When",
                        "Use when a concrete backend boundary, validation, or handoff signal requires a focused capability decision.",
                        "## Do Not Load When",
                        "Do not load for top-level routing, unrelated architecture, or work without a boundary signal.",
                        "## Selection Rules",
                        "- When owner input is missing, return a missing-input fragment instead of guessing.",
                        "- When validation evidence is missing, block approval and route the residual risk to the owner.",
                        "- When the signal belongs to another owner, hand off rather than expanding scope.",
                        "## Failure Modes",
                        "- Condition: owner input missing; consequence: guessed scope; detection: absent owner path; repair: return missing-input fragment; evidence: cited missing field.",
                        "- Condition: validation omitted; consequence: false approval; detection: no command output; repair: require focused validation evidence.",
                        "- Condition: capability acts as owner; consequence: boundary confusion; detection: output lacks next owner; repair: return to owner skill.",
                        "## Output Fragment",
                        "- selected mode: focused capability support.",
                        "- professional decision: approve, block, or return missing input.",
                        "- inspected boundaries: owner file, affected layer, and handoff boundary.",
                        "- evidence collected: validation command or reviewed source path.",
                        "- evidence limits: what remains unverified.",
                        "- validation status: pass, fail, blocked, or not run with reason.",
                        "- residual risk: owner-visible unresolved risk.",
                        "- next gate: owner skill, reviewer, or validation gate.",
                        "- next owner: selected professional owner skill.",
                        "## Evidence Requirement",
                        "- Boundaries inspected: owner path and affected boundary.",
                        "- Validation evidence: command output or source-backed reason.",
                        "- What evidence proves: selected boundary behavior.",
                        "- What evidence does not prove: unrelated architecture behavior.",
                        "- Residual risk: unresolved owner decision.",
                        "- Next gate: owner skill review.",
                        "## Return To Owner Skill",
                        "Return the fragment to the selected professional owner with handoff evidence and residual risk.",
                    ]
                ),
            )
            sections = module._depth_sections(path.read_text(encoding="utf-8"))
            item = module._evaluate_professional_depth(path, "foundation-capability")

        warning_types = {warning.type for warning in item.warnings}
        self.assertIn("owner-returned fragment", sections["Stage Ownership"])
        self.assertIn("owner-returned fragment", sections["Adjacent Skill Conflict Resolution"])
        self.assertIn("selected mode", sections["Output Contract"])
        self.assertIn("Boundaries inspected", sections["Evidence Contract"])
        self.assertIn("Return the fragment", sections["Handoff"])
        self.assertNotIn("owner_capability_confusion", warning_types)
        self.assertGreaterEqual(item.dimensions["professional_responsibility_clarity"], 7)
        self.assertGreaterEqual(item.dimensions["boundary_and_ownership_precision"], 7)
        self.assertGreaterEqual(item.dimensions["output_contract_actionability"], 7)
        self.assertGreaterEqual(item.dimensions["evidence_contract_completeness"], 8)

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

    def test_depth_recognizes_snake_case_output_and_anti_rationalization_aliases(self) -> None:
        module = _load_module()
        body = "\n".join(
            [
                "# Output Fragment",
                "- `mode_selected`: focused review.",
                "- `professional_decision`: approve or block.",
                "- `boundaries_inspected`: owner and affected file.",
                "- `evidence_collected`: validation output.",
                "- `evidence_limits`: skipped integration path.",
                "- `validation_status`: pass.",
                "- `residual_risk`: none.",
                "- `next_gate`: owner review.",
                "# Evidence Requirement",
                "- `boundaries_inspected`: owner file.",
                "- `validation_evidence`: command output.",
                "- `residual_risk`: remaining gap.",
                "- `next_gate`: selected owner.",
                "# Anti-Rationalization Table",
                "| Rationalization | Hidden Risk | Required Correction |",
                "| --- | --- | --- |",
                "| It is simple. | Boundary drift. | Require evidence. |",
            ]
        )
        sections = module._depth_sections(body)
        self.assertIn("mode_selected", sections["Output Contract"])
        self.assertIn("boundaries_inspected", sections["Evidence Contract"])
        self.assertIn("It is simple", sections["Anti-Patterns"])
        self.assertGreaterEqual(module._score_depth_output(sections), 8)
        self.assertGreaterEqual(module._score_depth_anti_patterns(sections), 4)

    def test_depth_recognizes_title_case_output_and_domain_residual_risk(self) -> None:
        module = _load_module()
        body = "\n".join(
            [
                "# Output Fragment",
                "- **Mode selected**: runtime review.",
                "- **Boundaries inspected**: owner and build files.",
                "- **Validation evidence**: command output.",
                "- **Evidence limits**: production tuning unverified.",
                "- **Residual JVM risk**: untested GC behavior.",
                "- **Next gate**: reliability review.",
                "# Evidence Requirement",
                "- **What evidence proves**: inspected runtime behavior.",
                "- **What evidence does not prove**: all production platforms.",
                "- **Residual JVM risk**: untested GC behavior.",
            ]
        )
        sections = module._depth_sections(body)
        evidence_hits = module._evidence_obligation_hits(
            "\n".join([sections["Evidence Contract"], sections["Output Contract"]])
        )
        self.assertIn("residual risk", evidence_hits)
        self.assertGreaterEqual(module._score_depth_output(sections), 7)

    def test_failure_mode_specificity_recognizes_equivalent_structure_terms(self) -> None:
        module = _load_module()
        sections = {
            "Failure Modes": "\n".join(
                [
                    "- **Boundary drift:** Symptom: owner output expands. Cause: missing boundary. Detection: review output. Impact: owner confusion. Required correction: return a fragment with evidence.",
                    "- **Validation overclaim:** Symptom: approval without command. Cause: stale evidence. Detection: missing exit code. Impact: false confidence. Required correction: state residual risk.",
                    "- **Unsafe shortcut:** Symptom: temporary branch persists. Cause: no owner. Detection: cleanup search. Impact: permanent debt. Required correction: assign owner and expiry.",
                ]
            )
        }
        self.assertGreaterEqual(module._score_depth_failure_modes(sections), 8)

    def test_decision_depth_counts_required_input_fragment_as_missing_policy(self) -> None:
        module = _load_module()
        body = "\n".join(
            [
                "# Required Input Fragment",
                "For this capability, the owner skill must provide task intent and validation target. If that input is missing, return a missing-input fragment instead of guessing.",
                "# Decision Rules",
                "- Select the capability when the owner needs a focused decision.",
                "- Do not select it when another owner owns the boundary.",
            ]
        )
        sections = module._depth_sections(body)
        self.assertIn("missing-input", sections["Required Context / Missing Information Policy"])
        self.assertGreaterEqual(module._score_depth_decisions(sections), 6)

    def test_decision_depth_counts_do_not_use_as_skip_guidance(self) -> None:
        module = _load_module()
        body = "\n".join(
            [
                "# Decision Rules",
                "When owner input is missing, return a missing-input fragment instead of guessing.",
                "Escalate to the owner when the boundary is non-owned.",
                "# Do Not Use When",
                "Do not use when the selected owner confirms the boundary is unrelated.",
            ]
        )
        sections = module._depth_sections(body)
        self.assertGreaterEqual(module._score_depth_decisions(sections), 8)

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

    def test_depth_judgment_requires_item_specific_axis_context(self) -> None:
        module = _load_module()
        axes = [
            "input validation and trust boundary",
            "server side authorization and tenant isolation",
            "transaction and consistency control",
            "idempotency retry and async safety",
            "error contract and observability",
            "service repository and adapter placement",
        ]
        sections = {
            "Non-Negotiable Rules": "",
            "Technical Selection Criteria": "",
            "Selection Rules": "",
            "Risk Escalation Rules": "",
            "Critical Details": "",
            "Proactive Professional Triggers": "",
        }
        generic = (
            "Use boundary, contract, evidence, failure, handoff, validation, "
            "residual risk, escalation, and professional decision language."
        )
        specific = "\n".join(
            [
                "- Input validation and trust boundary: block untrusted request fields until parser and authorization evidence are inspected.",
                "- Server side authorization and tenant isolation: require denied cross-tenant regression evidence before approval.",
                "- Transaction and consistency control: inspect commit boundaries, rollback behavior, and concurrent update failure modes.",
                "- Idempotency retry and async safety: require replay evidence for duplicate delivery and retry limits.",
                "- Error contract and observability: keep client errors stable and emit logs/metrics/traces that prove the failed path.",
                "- Service repository and adapter placement: route persistence and provider code to the owning adapter boundary.",
            ]
        )
        self.assertLess(
            module._score_depth_judgment(generic, sections, "professional-skill", axes),
            module._score_depth_judgment(specific, sections, "professional-skill", axes),
        )
        self.assertLessEqual(
            module._score_depth_judgment(generic, sections, "professional-skill", axes),
            8,
        )

    def test_missing_item_specific_axes_warns_for_professional_skill(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_skill(
                Path(tmp),
                "\n".join(
                    [
                        "## Mission",
                        "Evaluate a focused backend behavior.",
                        "## Selection Rules",
                        "Use when owner evidence is present; block when it is missing.",
                        "## Failure Modes",
                        "- Condition: missing evidence; consequence: unsafe approval; detection: absent command; repair: block.",
                        "## Output Contract",
                        "- professional_decision: approve or block.",
                        "- evidence_collected: validation output.",
                        "- residual_risk: unverified branch.",
                        "## Evidence Requirement",
                        "- What evidence proves: selected behavior.",
                        "- What evidence does not prove: unrelated behavior.",
                    ]
                ),
            )
            item = module._evaluate_professional_depth(
                path,
                "professional-skill",
                {
                    "default_axes": {
                        "professional-skill": [
                            "owned decision boundary",
                            "evidence requirement",
                            "failure prevented",
                        ]
                    },
                    "items": {},
                },
            )
        self.assertIn("missing_judgment_axes", {warning.type for warning in item.warnings})
        self.assertEqual(item.judgment_axis_source, "default_axes.professional-skill")

    def test_axis_registry_prefers_canonical_items_over_legacy_buckets(self) -> None:
        module = _load_module()
        axis_spec = module._professional_axes_for(
            "backend-change-builder",
            "professional-skill",
            {
                "items": {
                    "backend-change-builder": {"axes": ["canonical service boundary"]},
                },
                "skills": {
                    "backend-change-builder": {"axes": ["legacy service boundary"]},
                },
            },
        )
        self.assertEqual(axis_spec["source"], "items.backend-change-builder")
        self.assertEqual(axis_spec["axes"], ["canonical service boundary"])

    def test_axis_registry_reads_legacy_buckets_as_compatibility_fallback(self) -> None:
        module = _load_module()
        professional = module._professional_axes_for(
            "backend-change-builder",
            "professional-skill",
            {
                "skills": {
                    "backend-change-builder": {"axes": ["legacy service boundary"]},
                },
            },
        )
        capability = module._professional_axes_for(
            "idempotency-retry-design",
            "foundation-capability",
            {
                "capabilities": {
                    "idempotency-retry-design": {"axes": ["legacy idempotency key scope"]},
                },
            },
        )
        self.assertEqual(professional["source"], "skills.backend-change-builder")
        self.assertEqual(professional["axes"], ["legacy service boundary"])
        self.assertEqual(capability["source"], "capabilities.idempotency-retry-design")
        self.assertEqual(capability["axes"], ["legacy idempotency key scope"])

    def test_key_foundation_capability_requires_item_specific_axes(self) -> None:
        module = _load_module()
        key = module._professional_axes_for(
            "cache-design",
            "foundation-capability",
            {"default_axes": {"foundation-capability": ["generic capability axis"]}},
        )
        non_key = module._professional_axes_for(
            "api-contract-design",
            "foundation-capability",
            {"default_axes": {"foundation-capability": ["generic capability axis"]}},
        )
        self.assertTrue(key["missing_specific_axes"])
        self.assertEqual(key["source"], "default_axes.foundation-capability")
        self.assertFalse(non_key["missing_specific_axes"])

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
            self.assertTrue((reports / "skill-professionalism-depth.md").is_file())
            self.assertTrue((reports / "skill-professionalism-depth.json").is_file())
            self.assertTrue((reports / "professional-coverage-matrix.md").is_file())
            self.assertTrue((reports / "professional-coverage-matrix.json").is_file())
            depth = json.loads((reports / "skill-professionalism-depth.json").read_text(encoding="utf-8"))
            self.assertIn("average_professionalism_score", depth)
            self.assertEqual(
                depth["score_model_path"],
                "docs/skill_professionalism_standard/SKILL_PROFESSIONALISM_DIMENSION_RUBRIC.md",
            )
            self.assertEqual(
                depth["judgment_axis_registry"],
                "docs/skill_professionalism_standard/professionalism-axes.yaml",
            )
            self.assertEqual(depth["metadata_warnings"], [])
            self.assertTrue(all("judgment_axes" in item for item in depth["items"]))
            self.assertTrue(
                all("trigger_accuracy" not in item["dimensions"] for item in depth["items"])
            )
            matrix = json.loads((reports / "professional-coverage-matrix.json").read_text(encoding="utf-8"))
            router = next(row for row in matrix["rows"] if row["name"] == "change-forge-router")
            self.assertTrue(router["routing_coverage"].startswith("n/a (router owns routing fixture corpus"))
            self.assertTrue(router["benchmark_coverage"].startswith("n/a (covered by eval-routing"))

    def test_professional_depth_includes_domain_extensions(self) -> None:
        module = _load_module()
        report = module._build_professional_depth_report()
        kinds = {item.kind for item in report.items}
        self.assertIn("professional-skill", kinds)
        self.assertIn("foundation-capability", kinds)
        self.assertIn("domain-extension", kinds)

    def test_professional_depth_low_when_only_reference_efficiency_is_strong(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_skill(
                Path(tmp),
                "\n".join(
                    [
                        "## Mission",
                        "Use references efficiently.",
                        "## Reference Loading Policy",
                        "Load only selected references and skip adjacent references with reasons.",
                    ]
                ),
            )
            item = module._evaluate_professional_depth(path, "professional-skill")
        self.assertLess(item.professionalism_score, 60)
        self.assertNotIn("reference_precision", item.dimensions)

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
