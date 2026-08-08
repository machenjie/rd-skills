from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/audit-skill-content.py"


def _load_module():
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location("audit_skill_content_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _semantic_disposition(candidate: dict, disposition: str, *, priority: str = "P1") -> dict:
    return {
        "candidate_id": candidate["candidate_id"],
        "finding": candidate["finding"],
        "path": candidate["path"],
        "fingerprint": candidate["fingerprint"],
        "skill_owner": candidate["skill_owner"],
        "priority": priority,
        "disposition": disposition,
        "reason": "Current source evidence supports this explicit governance decision.",
        "authority_or_condition": "Repository governance policy owns the declared condition.",
        "decision_owner": "Repository governance owner",
        "evidence": {
            "fingerprint": candidate["evidence_fingerprint"],
            "content_fingerprint": candidate["content_fingerprint"],
            "rationale": "The candidate identity and current source membership were inspected.",
        },
        "mitigation": "Re-evaluate the wording when its source contract or membership changes.",
        "review_after": (
            "2026-08-01" if disposition == "time-bounded-exception" else None
        ),
    }


class AuditSkillContentDeterminismTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def _invoke_gate(
        self,
        gate: str,
        *,
        application: dict,
        content_blockers: int = 0,
        hard_gate_ready: bool = True,
        root_surface_validation: dict | None = None,
        reference_surface_validation: dict | None = None,
    ) -> tuple[int, dict, bytes, str]:
        def passing_surface_validation() -> dict:
            return {
                "schema_version": 1,
                "common_errors": [],
                "surfaces": {
                    "professional": {"status": "pass", "errors": []},
                },
            }

        result = {
            "metrics": [],
            "raw_common_lines": {},
            "actionable_common_lines": {},
            "optimality_files": [],
            "ai_readability": {
                "summary": {"hard_gate_ready": hard_gate_ready},
            },
            "root_content": {
                "surface_validation": (
                    passing_surface_validation()
                    if root_surface_validation is None
                    else root_surface_validation
                ),
            },
            "reference_content": {
                "summary": {
                    "existing_indexed_references": 0,
                    "missing_references": 0,
                    "orphan_references": 0,
                    "template_assets": 0,
                },
                "surface_validation": (
                    passing_surface_validation()
                    if reference_surface_validation is None
                    else reference_surface_validation
                ),
            },
            "semantic_disposition_application": application,
        }
        summary = {
            "professional_skills": 0,
            "foundation_capabilities": 0,
            "domain_extensions": 0,
            "content_review_density_candidates": 0,
            "content_tighten_candidates": 0,
            "content_blockers": content_blockers,
            "review_states": {},
        }
        with tempfile.TemporaryDirectory() as raw:
            reports = Path(raw)
            report_json = reports / "skill-content-audit.json"
            report_md = reports / "skill-content-audit.md"
            stderr = io.StringIO()
            with (
                mock.patch.object(self.module, "ROOT", reports),
                mock.patch.object(self.module, "REPORTS_DIR", reports),
                mock.patch.object(self.module, "JSON_REPORT", report_json),
                mock.patch.object(self.module, "MARKDOWN_REPORT", report_md),
                mock.patch.object(self.module, "audit", return_value=result),
                mock.patch.object(
                    self.module,
                    "_reference_source_safety_errors",
                    return_value=[],
                ),
                mock.patch.object(self.module, "_summary", return_value=summary),
                mock.patch.object(
                    self.module,
                    "_format_md",
                    return_value="# Audit fixture\n",
                ),
                contextlib.redirect_stderr(stderr),
            ):
                status = self.module.main(["--gate", gate])
            report_bytes = report_json.read_bytes()
            report = json.loads(report_bytes)
        return status, report, report_bytes, stderr.getvalue()

    def _assert_stale_authoring_blocker(
        self,
        *,
        blocker_id: str,
        blocker_message: str,
        **gate_inputs: object,
    ) -> None:
        stale_application = {
            "schema_version": 1,
            "kind": "changeforge.semantic-disposition-application",
            "status": "invalid",
            "error": {
                "id": "semantic-decision-application-invalid",
                "message": "semantic disposition packet is stale against the current audit",
            },
        }
        status, report, report_bytes, stderr = self._invoke_gate(
            "authoring",
            application=stale_application,
            **gate_inputs,
        )

        self.assertEqual(1, status)
        self.assertEqual(
            [{"id": blocker_id, "message": blocker_message}],
            report["gate_status"]["authoring"]["blockers"],
        )
        self.assertEqual(
            stale_application,
            report["semantic_disposition_application"],
        )
        self.assertIn(f"{blocker_id}: {blocker_message}", stderr)
        for expected in stale_application["error"].values():
            self.assertIn(expected.encode(), report_bytes)
            self.assertIn(expected, stderr)

    def test_authoring_gate_still_fails_deterministic_content_blockers(self) -> None:
        status, report, _report_bytes, stderr = self._invoke_gate(
            "authoring",
            application={
                "schema_version": 1,
                "kind": "changeforge.semantic-disposition-application",
                "status": "current",
            },
            content_blockers=1,
        )

        self.assertEqual(1, status)
        self.assertEqual("fail", report["gate_status"]["authoring"]["status"])
        self.assertEqual(
            ["content-blockers-present"],
            [
                blocker["id"]
                for blocker in report["gate_status"]["authoring"]["blockers"]
            ],
        )
        self.assertIn("content-blockers-present", stderr)

    def test_authoring_gate_fails_when_ai_readability_hard_gate_is_not_ready(
        self,
    ) -> None:
        self._assert_stale_authoring_blocker(
            blocker_id="ai-readability-hard-gate-not-ready",
            blocker_message="AI-readability deterministic hard gate is not ready",
            hard_gate_ready=False,
        )

    def test_authoring_gate_fails_on_root_surface_validation(self) -> None:
        self._assert_stale_authoring_blocker(
            blocker_id="root-content-surface-invalid",
            blocker_message=(
                "root-content deterministic surface validation failed; "
                "common_errors=1; failing_surfaces=none"
            ),
            root_surface_validation={
                "schema_version": 1,
                "common_errors": [{"code": "fixture-root-error"}],
                "surfaces": {
                    "professional": {"status": "pass", "errors": []},
                },
            },
        )

    def test_authoring_gate_fails_on_reference_surface_validation(self) -> None:
        self._assert_stale_authoring_blocker(
            blocker_id="reference-content-surface-invalid",
            blocker_message=(
                "reference-content deterministic surface validation failed; "
                "common_errors=0; failing_surfaces=professional"
            ),
            reference_surface_validation={
                "schema_version": 1,
                "common_errors": [],
                "surfaces": {
                    "professional": {
                        "status": "fail",
                        "errors": [{"code": "fixture-reference-error"}],
                    },
                },
            },
        )

    def test_stale_formal_application_is_visible_but_does_not_fail_authoring(
        self,
    ) -> None:
        current_application = {
            "schema_version": 1,
            "kind": "changeforge.semantic-disposition-application",
            "status": "current",
        }
        stale_application = {
            **current_application,
            "status": "invalid",
            "error": {
                "id": "semantic-decision-application-invalid",
                "message": "semantic disposition packet is stale against the current audit",
            },
        }
        current_bytes = json.dumps(
            current_application, sort_keys=True, separators=(",", ":")
        ).encode()
        stale_bytes = json.dumps(
            stale_application, sort_keys=True, separators=(",", ":")
        ).encode()
        self.assertNotEqual(current_bytes, stale_bytes)

        authoring_status, report, report_bytes, stderr = self._invoke_gate(
            "authoring",
            application=stale_application,
        )

        self.assertEqual(0, authoring_status, stderr)
        self.assertEqual("pass", report["gate_status"]["authoring"]["status"])
        self.assertEqual(
            "blocked",
            report["gate_status"]["formal_release"]["status"],
        )
        self.assertEqual(
            stale_application,
            report["semantic_disposition_application"],
        )
        for expected in (
            stale_application["error"]["id"],
            stale_application["error"]["message"],
        ):
            self.assertIn(expected.encode(), report_bytes)
            self.assertIn(expected, stderr)
        self.assertTrue(report["gate_status"]["limitations"])

        formal_status, formal_report, formal_bytes, formal_stderr = (
            self._invoke_gate(
                "formal-release",
                application=stale_application,
            )
        )
        self.assertEqual(1, formal_status)
        self.assertEqual(stale_application, formal_report["semantic_disposition_application"])
        self.assertIn(stale_application["error"]["id"].encode(), formal_bytes)
        self.assertIn(stale_application["error"]["message"], formal_stderr)

    def test_common_lines_use_fanout_then_lexical_order(self) -> None:
        common_lines = {
            "zeta normalized line": {"a", "b"},
            "alpha normalized line": {"c", "d"},
            "widest normalized line": {"e", "f", "g"},
        }
        self.assertEqual(
            [
                "widest normalized line",
                "alpha normalized line",
                "zeta normalized line",
            ],
            [line for line, _files in self.module._sorted_common_lines(common_lines)],
        )

    def test_ai_readability_collector_preserves_review_and_hard_bands(self) -> None:
        def sentence(words: int) -> str:
            return " ".join(f"word{index}" for index in range(words)) + "."

        documents = [
            {
                "document_id": "src/example/SKILL.md#body",
                "path": "src/example/SKILL.md",
                "document_part": "body",
                "surface": "foundation-capability-body",
                "owner": "example",
                "line_offset": 7,
                "source_selector": {
                    "kind": "yaml-body",
                    "path": "src/example/SKILL.md",
                },
                "text": "\n\n".join(
                    sentence(words) for words in (24, 25, 32, 33, 40, 41)
                )
                + "\n\n- Validate the boundary. Return the evidence.\n",
                "check_bullets": True,
            },
            {
                "document_id": "src/example/SKILL.md#description",
                "path": "src/example/SKILL.md",
                "document_part": "description",
                "surface": "foundation-capability-description",
                "owner": "example",
                "line_offset": 0,
                "source_selector": {
                    "kind": "yaml-description",
                    "path": "src/example/SKILL.md",
                    "field": "description",
                },
                "text": "Validate the boundary. Return the evidence.",
                "check_bullets": False,
            },
        ]
        result = self.module._collect_ai_readability(documents)
        summary = result["summary"]
        self.assertEqual(2, summary["review_as_complex_sentences"])
        self.assertEqual(2, summary["tighten_sentences"])
        self.assertEqual(1, summary["hard_fail_sentences"])
        self.assertEqual(1, summary["compound_bullets"])
        self.assertEqual(4, summary["advisory_sentences"])
        self.assertEqual(2, summary["blocker_findings"])
        self.assertFalse(summary["hard_gate_ready"])
        body = result["documents"][0]
        self.assertEqual("tighten", body["highest_advisory_band"])

    def test_ai_readability_fingerprint_is_deterministic_and_source_bound(self) -> None:
        document = {
            "document_id": "src/example/SKILL.md#body",
            "path": "src/example/SKILL.md",
            "document_part": "body",
            "surface": "professional-skill-body",
            "owner": "example",
            "line_offset": 3,
            "source_selector": {
                "kind": "yaml-body",
                "path": "src/example/SKILL.md",
            },
            "text": "Inspect the bounded source before choosing the implementation path.",
            "check_bullets": True,
        }
        first = self.module._collect_ai_readability([document])
        second = self.module._collect_ai_readability([dict(document)])
        changed = self.module._collect_ai_readability(
            [{**document, "text": document["text"] + " Record current evidence."}]
        )
        self.assertEqual(first["source_fingerprint"], second["source_fingerprint"])
        self.assertNotEqual(
            first["source_fingerprint"]["value"],
            changed["source_fingerprint"]["value"],
        )

    def test_ai_readability_inventory_includes_profiles_roots_and_references(self) -> None:
        documents = self.module._ai_readability_documents()
        document_ids = [item["document_id"] for item in documents]
        self.assertEqual(document_ids, sorted(document_ids))
        self.assertEqual(len(document_ids), len(set(document_ids)))
        profile_rows = [
            item
            for item in documents
            if item["path"] == "src/agent-profiles/role-agents.json"
        ]
        self.assertEqual(
            {"description", "instructions"},
            {item["document_part"] for item in profile_rows},
        )
        self.assertEqual(
            {"agent-profile-description", "agent-profile-instructions"},
            {item["surface"] for item in profile_rows},
        )
        for surface in (
            "control-prompt",
            "control-skill-body",
            "professional-skill-body",
            "foundation-capability-body",
            "domain-extension-body",
            "control-reference",
            "professional-reference",
            "foundation-reference",
            "domain-reference",
        ):
            self.assertIn(surface, {item["surface"] for item in documents})

    def test_readability_inventory_keeps_only_reliable_line_offset_metadata(self) -> None:
        roots = self.module._root_skill_documents()
        body = next(item for item in roots if item["document_part"] == "body")
        raw = (ROOT / body["path"]).read_text(encoding="utf-8")
        _metadata, frontmatter, _body = self.module.parse_frontmatter(
            ROOT / body["path"]
        )
        self.assertEqual(len(frontmatter.splitlines()) + 2, body["line_offset"])
        self.assertTrue(raw.startswith("---\n"))
        descriptions = [
            item
            for item in self.module._ai_readability_documents()
            if item["document_part"] == "description"
            and item["source_selector"]["kind"] == "yaml-description"
        ]
        self.assertTrue(descriptions)
        self.assertTrue(all(item["line_offset"] == 0 for item in descriptions))

    def test_readability_spans_cover_wrapped_and_same_line_sentences_exactly(self) -> None:
        long_sentence = " ".join(f"bounded{index}" for index in range(25)) + "."
        wrapped = (
            "- "
            + " ".join(long_sentence.split()[:14])
            + "\n  "
            + " ".join(long_sentence.split()[14:])
            + " Next short sentence.\n"
        )
        wrapped_finding = self.module.ai_readability_findings(
            wrapped, "wrapped"
        )[0]
        span = wrapped_finding["source_span"]
        self.assertEqual((1, 2), (span["start_line"], span["end_line"]))
        self.assertEqual(
            hashlib.sha256(
                wrapped[span["start_offset"] : span["end_offset"]].encode(
                    "utf-8"
                )
            ).hexdigest(),
            span["sha256"],
        )

        repeated = f"{long_sentence} {long_sentence}\n"
        document = {
            "document_id": "src/example.md#reference",
            "path": "src/example.md",
            "document_part": "reference",
            "surface": "foundation-reference",
            "owner": "example",
            "line_offset": 0,
            "source_selector": {
                "kind": "whole-file",
                "path": "src/example.md",
            },
            "text": repeated,
            "check_bullets": True,
        }
        result = self.module._collect_ai_readability([document])
        findings = result["findings"]
        self.assertEqual(2, len(findings))
        self.assertEqual(1, findings[0]["source_span"]["start_line"])
        self.assertEqual(1, findings[1]["source_span"]["start_line"])
        self.assertNotEqual(
            findings[0]["source_span"]["start_offset"],
            findings[1]["source_span"]["start_offset"],
        )
        self.assertNotEqual(findings[0]["finding_id"], findings[1]["finding_id"])

        unicode_sentence = (
            "界🙂 e\u0301 "
            + " ".join(f"unicode{index}" for index in range(25))
            + "."
        )
        crlf = f"Heading\r\n- {unicode_sentence}\r\n"
        unicode_findings = self.module.ai_readability_findings(
            crlf, "unicode-crlf"
        )
        self.assertEqual(1, len(unicode_findings))
        line_start = len("Heading\r\n")
        for finding in unicode_findings:
            source_span = finding["source_span"]
            exact = crlf[
                source_span["start_offset"] : source_span["end_offset"]
            ]
            self.assertEqual(unicode_sentence, exact)
            self.assertEqual(2, source_span["start_line"])
            self.assertEqual(2, source_span["end_line"])
            self.assertEqual(
                source_span["start_offset"] - line_start + 1,
                source_span["start_column"],
            )
            self.assertEqual(
                source_span["end_offset"] - line_start + 1,
                source_span["end_column"],
            )
            self.assertEqual(
                hashlib.sha256(exact.encode("utf-8")).hexdigest(),
                source_span["sha256"],
            )

    def test_current_readability_inventory_is_exact_and_unique(self) -> None:
        result = self.module._collect_ai_readability()
        self.assertEqual(2, result["schema_version"])
        self.assertEqual(357, result["summary"]["advisory_documents"])
        # The compressed Main prompt keeps the deterministic advisory inventory bounded.
        self.assertEqual(978, result["summary"]["advisory_sentences"])
        finding_ids = [item["finding_id"] for item in result["findings"]]
        self.assertEqual(978, len(finding_ids))
        self.assertEqual(978, len(set(finding_ids)))

    def test_markdown_is_independent_of_common_line_insertion_order(self) -> None:
        rows = [
            ("zeta normalized line", {"a", "b"}),
            ("alpha normalized line", {"c", "d"}),
            ("widest normalized line", {"e", "f", "g"}),
        ]

        def render(ordered_rows):
            common = dict(ordered_rows)
            return self.module._format_md(
                {
                    "metrics": [],
                    "common_lines": common,
                    "raw_common_lines": common,
                    "actionable_common_lines": common,
                    "optimality_files": [],
                    "shared_optimality": False,
                }
            )

        self.assertEqual(render(rows), render(reversed(rows)))

    def test_front_loading_recognizes_required_high_value_gotchas(self) -> None:
        body = """# example

## Role

Inspect the assigned boundary.

## High-Value Gotchas

- Hidden ownership can invalidate the local fix.

## Execution Checklist

1. Inspect source and verify the owner.

## Stop / Escalation Conditions

- Stop when authority or proof is missing.
"""
        self.assertEqual(self.module.THRESHOLDS["front_window_lines"], 60)
        self.assertGreaterEqual(self.module._front_loaded_action_score(body), 60)

    def test_front_loading_recognizes_trace_as_a_domain_action(self) -> None:
        baseline = """# example

## High-Value Rules

- Consider the current boundary end to end.
"""
        traced = """# example

## High-Value Rules

- Trace the current boundary end to end.
"""
        self.assertIn("trace", self.module.DOMAIN_ACTION_VERBS)
        self.assertEqual(
            self.module._front_loaded_action_score(baseline) + 4,
            self.module._front_loaded_action_score(traced),
        )

    def test_shared_scaffold_is_actionable_outside_targeted_references(self) -> None:
        canonical = (
            "return the decision, evidence, proof limits, escalation, and residual risk."
        )
        actionable = self.module._actionable_significant_lines(
            f"# Example\n\n## Output Contract\n\n- {canonical}\n"
        )
        excluded = self.module._actionable_significant_lines(
            f"# Example\n\n## Targeted References\n\n- {canonical}\n"
        )
        self.assertIn(canonical, actionable)
        self.assertNotIn(canonical, excluded)

    def test_foundation_core_is_complete_without_optional_sections(self) -> None:
        body = """# example

## Registry Trigger

**Use when**

- A named invariant requires a focused decision.

**Do not use when**

- The invariant and owner are unchanged.

## Skill Role

Support `task-agent` as a focused Layer 3 Skill for this decision.

## High-Value Rules

- Identify the current owner, affected consumers, and invariant before selecting a mechanism; reject any candidate that moves enforcement to a weaker boundary.
- Compare failure behavior, reversibility, and validation evidence from the current system; a familiar technology is not proof that it fits the named constraint.
- Preserve the smallest correct ownership boundary and state the proof limitation when a material consumer or failure path cannot be inspected.

## Anti-Patterns

- A context-free default can satisfy a happy path while violating an existing consumer contract.

## Targeted References

- No separate Reference is indexed; use this root decision contract.
"""
        metrics = self.module.SkillMetrics(
            name="example",
            path="example/SKILL.md",
            kind="foundation-capability",
            content_class="compact",
            content_target_words=400,
            content_hard_words=500,
        )
        self.module._score(metrics, self.module.parse_sections(body), body)
        self.assertEqual(100, metrics.professionalism_score)
        self.assertEqual(100, metrics.routing_clarity_score)
        self.assertNotIn("missing Execution Checklist", metrics.findings)

    def test_foundation_actionability_uses_decision_card_not_runtime_score(
        self,
    ) -> None:
        body = """# cache-ownership

## Registry Trigger

**Use when**

- Cache invalidation ownership is disputed.

**Do not use when**

- Cache behavior and ownership are unchanged.

## Skill Role

Bound cache invalidation decisions to the current consistency owner.

## High-Value Rules

- Bind cache keys to the data owner and reject invalidation from a weaker boundary.
- Derive eviction timing from stale-read tolerance and measured write behavior.
- Preserve retry and concurrent-write semantics when selecting invalidation behavior.

## Anti-Patterns

- A generic cache default can hide stale reads.

## Stop Conditions

- Stop when the cache owner or stale-read contract is unknown.

## Output Contract

- Return the selected cache invariant and residual stale-read risk.

## Targeted References

- No separate Reference is indexed; use this root decision contract.
"""
        metrics = self.module.SkillMetrics(
            name="cache-ownership",
            path="src/foundation/capabilities/cache-ownership/SKILL.md",
            kind="foundation-capability",
            content_class="compact",
            content_target_words=400,
            content_hard_words=500,
        )
        self.module._score(metrics, self.module.parse_sections(body), body)
        shared = self.module.foundation_decision_card(body)
        self.assertLess(
            metrics.front_loaded_action_score,
            self.module.THRESHOLDS["weak_front_loaded_action"],
        )
        self.assertEqual(shared["model"], metrics.actionability_model)
        self.assertEqual(shared["applicable"], metrics.actionability_applicable)
        self.assertEqual(shared["findings"], metrics.actionability_findings)
        self.assertEqual(
            shared["metrics"]["decision_density"],
            metrics.decision_density,
        )

    def test_foundation_decision_card_rejects_structural_and_density_gaps(
        self,
    ) -> None:
        base = """# cache-ownership

## Registry Trigger

**Use when**

- Cache invalidation ownership is disputed.

**Do not use when**

- Cache behavior and ownership are unchanged.

## Skill Role

Bound cache invalidation decisions to the current consistency owner.

## High-Value Rules

- Bind cache keys to the data owner and reject invalidation from a weaker boundary.
- Derive eviction timing from stale-read tolerance and measured write behavior.
- Preserve retry and concurrent-write semantics when selecting invalidation behavior.

## Anti-Patterns

- A generic cache default can hide stale reads.

## Stop Conditions

- Stop when the cache owner or stale-read contract is unknown.

## Targeted References

- No separate Reference is indexed; use this root decision contract.
"""

        def findings(body: str) -> list[str]:
            metrics = self.module.SkillMetrics(
                name="cache-ownership",
                path="src/foundation/capabilities/cache-ownership/SKILL.md",
                kind="foundation-capability",
                content_class="compact",
                content_target_words=400,
                content_hard_words=500,
            )
            self.module._score(metrics, self.module.parse_sections(body), body)
            self.assertTrue(metrics.actionability_applicable)
            return metrics.actionability_findings

        variants = {
            "delayed-high-value-rules": base.replace(
                "## High-Value Rules",
                ("Decision context remains intentionally non-operative.\n" * 45)
                + "\n## High-Value Rules",
            ),
            "hollow-generic-rules": base.replace(
                "- Bind cache keys to the data owner and reject invalidation from a weaker boundary.\n"
                "- Derive eviction timing from stale-read tolerance and measured write behavior.\n"
                "- Preserve retry and concurrent-write semantics when selecting invalidation behavior.",
                "- First inspect the current decision and verify current evidence.\n"
                "- Preserve the named invariant using the selected boundary.\n"
                "- Return the decision with proof limits and residual risk.",
            ),
            "missing-stop": base.replace(
                "## Stop Conditions\n\n"
                "- Stop when the cache owner or stale-read contract is unknown.\n\n",
                "",
            ),
            "late-stop": base.replace(
                "## Stop Conditions\n\n"
                "- Stop when the cache owner or stale-read contract is unknown.\n\n",
                "",
            ).replace(
                "## Targeted References",
                "## Targeted References\n\n"
                "- No separate Reference is indexed; use this root decision contract.\n\n"
                "## Stop Conditions\n\n"
                "- Stop when the cache owner or stale-read contract is unknown.\n\n"
                "## Ignored Tail",
            ),
            "low-density": base.replace(
                "- Preserve retry and concurrent-write semantics when selecting invalidation behavior.",
                "- First inspect the current decision and verify current evidence.",
            ),
        }
        expected = {
            "delayed-high-value-rules": "high-value-rules-not-early",
            "hollow-generic-rules": "decision-density-low",
            "missing-stop": "stop-conditions-missing-or-late",
            "late-stop": "stop-conditions-missing-or-late",
            "low-density": "decision-density-low",
        }
        for label, body in variants.items():
            with self.subTest(variant=label):
                self.assertIn(expected[label], findings(body))

    def test_foundation_generic_first_verify_scaffold_does_not_clear_failure(
        self,
    ) -> None:
        hollow = """# example

## Registry Trigger

**Use when**

- A cache decision is open.

**Do not use when**

- Cache behavior is unchanged.

## Skill Role

Bound the cache decision.

## High-Value Rules

- Preserve the named invariant using current evidence.
- Return the current decision with proof limits.
- Keep the selected boundary and residual risk.

## Anti-Patterns

- Generic defaults hide ownership.

## Stop Conditions

- Stop when cache ownership is unknown.

## Targeted References

- No separate Reference is indexed.
"""
        scaffolded = hollow.replace(
            "## High-Value Rules",
            "First inspect the current decision.\n"
            "Verify current evidence before returning it.\n\n"
            "## High-Value Rules",
        )
        results = []
        for body in (hollow, scaffolded):
            metrics = self.module.SkillMetrics(
                name="example",
                path="src/foundation/capabilities/example/SKILL.md",
                kind="foundation-capability",
                content_class="compact",
                content_target_words=400,
                content_hard_words=500,
            )
            self.module._score(metrics, self.module.parse_sections(body), body)
            results.append(
                (
                    metrics.actionability_applicable,
                    metrics.actionability_findings,
                )
            )
        self.assertEqual(results[0], results[1])

    def test_foundation_target_overage_is_never_keep(self) -> None:
        metrics = self.module.SkillMetrics(
            name="example",
            path="src/foundation/capabilities/example/SKILL.md",
            kind="foundation-capability",
            content_class="compact",
            content_target_words=400,
            content_hard_words=500,
            over_content_target=True,
            word_count=430,
            high_value_rule_count=5,
            high_value_rule_decision_count=5,
            decision_density=1.0,
            front_loaded_action_score=20,
        )
        self.module._classify(metrics)
        self.assertEqual("REVIEW_DENSITY", metrics.classification)

        metrics.word_count = 450
        self.module._classify(metrics)
        self.assertEqual("REVIEW_DENSITY", metrics.classification)

        metrics.word_count = 451
        self.module._classify(metrics)
        self.assertEqual("TIGHTEN_BODY", metrics.classification)

        metrics.word_count = 501
        metrics.over_content_hard = True
        metrics.over_content_hard_words = True
        self.module._classify(metrics)
        self.assertEqual("BLOCK", metrics.classification)

    def test_professional_control_flow_arc_forces_tighten_below_budget(self) -> None:
        body = """# example

## When To Use

- Use for one bounded change.

## Do Not Use

- Do not use without the named trigger.

## Execution Checklist

1. Confirm the `example` trigger, allowed scope, acceptance, and stop conditions.
2. Inspect only the current source, tests, contracts, and targeted references needed for this decision.
3. Apply the narrow rules without expanding task scope or taking over ownership.
4. Run targeted post-edit validation after the final material edit and record the result.

## Stop / Escalation Conditions

- Stop when the bounded source is unavailable.

## Output Contract

- Return the decision, evidence, proof limits, escalation, and residual risk.
"""
        metrics = self.module.SkillMetrics(
            name="example",
            path="src/professional-skills/example/SKILL.md",
            kind="professional-skill",
            content_target_words=550,
            content_hard_words=650,
            content_target_tokens=850,
            content_hard_tokens=1000,
            word_count=len(body.split()),
            token_count=100,
        )
        self.module._score(metrics, self.module.parse_sections(body), body)
        self.module._classify(metrics)
        self.assertEqual("TIGHTEN_BODY", metrics.classification)
        self.assertLess(metrics.professionalism_score, 100)
        self.assertLess(metrics.context_efficiency_score, 100)
        self.assertTrue(metrics.high_confidence_control_scaffold)
        self.assertEqual(
            [
                "apply-skill-rules",
                "confirm-contract",
                "generic-handoff",
                "inspect-owning-source",
                "post-edit-validation",
            ],
            metrics.control_scaffold_families,
        )
        self.assertTrue(
            any("control scaffold" in finding for finding in metrics.findings),
            metrics.findings,
        )

    def test_professional_arc_requires_distinct_prepare_execute_close_families(
        self,
    ) -> None:
        body = """# example

## Execution Checklist

1. Inspect only the current source needed for this decision.
2. Run targeted post-edit validation after the final material edit.
"""
        findings = self.module._control_scaffold_findings(
            "professional-skill",
            self.module.parse_sections(body),
        )
        self.assertEqual(
            ["inspect-owning-source", "post-edit-validation"],
            sorted({finding["family"] for finding in findings}),
        )
        self.assertFalse(
            self.module._high_confidence_control_scaffold(
                "professional-skill",
                findings,
            )
        )

    def test_specialized_inspect_apply_handoff_does_not_form_generic_arc(
        self,
    ) -> None:
        body = """# example

## Execution Checklist

1. Inspect cache-key ownership and eviction ordering.
2. Apply the selected invalidation invariant to cache writes.

## Output Contract

- Return the selected cache invariant, supporting evidence, and residual stale-read risk.
"""
        findings = self.module._control_scaffold_findings(
            "professional-skill",
            self.module.parse_sections(body),
        )
        self.assertFalse(
            self.module._high_confidence_control_scaffold(
                "professional-skill",
                findings,
            ),
            findings,
        )

    def test_specialized_inspect_and_verify_do_not_form_control_arc(self) -> None:
        body = """# example

## When To Use

- Use for cache invalidation changes.

## Do Not Use

- Do not use when cache behavior is unchanged.

## Professional Decision Rules

- Inspect cache ownership and verify stale reads against the current consistency contract.

## Execution Checklist

1. Inspect the eviction path for the affected cache key.
2. Verify stale-read behavior under the selected invalidation strategy.

## Stop / Escalation Conditions

- Stop when cache ownership is unknown.

## Output Contract

- State the selected cache invariant and its proof limit.
"""
        metrics = self.module.SkillMetrics(
            name="example",
            path="src/professional-skills/example/SKILL.md",
            kind="professional-skill",
            content_target_words=550,
            content_hard_words=650,
            content_target_tokens=850,
            content_hard_tokens=1000,
            word_count=len(body.split()),
            token_count=100,
        )
        self.module._score(metrics, self.module.parse_sections(body), body)
        self.module._classify(metrics)
        self.assertFalse(metrics.high_confidence_control_scaffold)
        self.assertEqual("KEEP", metrics.classification)

    def test_foundation_exact_generic_return_scaffold_is_high_confidence(self) -> None:
        generic = "- Return the decision to the primary Professional Skill."
        specialized = "- Return an error when the cache key cannot be decoded."
        for line, expected in ((generic, True), (specialized, False)):
            with self.subTest(line=line):
                body = f"""# example

## Registry Trigger

**Use when**

- A cache invariant needs a focused decision.

**Do not use when**

- Cache behavior is unchanged.

## Skill Role

Support `task-agent` as a focused Layer 3 Skill for cache ownership.

## High-Value Rules

- Preserve the cache owner and derive invalidation from current consistency evidence.

## Anti-Patterns

- A context-free cache default can violate the current consistency boundary.

## Output Contract

{line}

## Targeted References

- No separate Reference is indexed; use this root decision contract.
"""
                metrics = self.module.SkillMetrics(
                    name="example",
                    path="src/foundation/capabilities/example/SKILL.md",
                    kind="foundation-capability",
                    content_class="compact",
                    content_target_words=400,
                    content_hard_words=500,
                    word_count=len(body.split()),
                    token_count=100,
                    high_value_rule_count=3,
                    high_value_rule_decision_count=3,
                    decision_density=1.0,
                )
                self.module._score(metrics, self.module.parse_sections(body), body)
                self.module._classify(metrics)
                self.assertEqual(expected, metrics.high_confidence_control_scaffold)
                self.assertEqual(
                    "TIGHTEN_BODY" if expected else "KEEP",
                    metrics.classification,
                )

    def test_foundation_specialized_authority_handoff_is_not_generic(self) -> None:
        body = """# example

## Skill Role

Return security authority decisions to the service that owns the protected resource.
"""
        findings = self.module._control_scaffold_findings(
            "foundation-capability",
            self.module.parse_sections(body),
        )
        self.assertEqual(
            ["foundation-broad-governance"],
            [finding["match"] for finding in findings],
        )
        self.assertFalse(
            self.module._high_confidence_control_scaffold(
                "foundation-capability",
                findings,
            )
        )

    def test_profile_family_normalizes_owner_and_profile_spelling(self) -> None:
        variants = (
            "Run this step in analysis-agent mode.",
            "Run this step in the Analysis Agent Profile.",
            "The `analysis-agent` owns this generic step.",
        )
        for value in variants:
            with self.subTest(value=value):
                findings = self.module._control_scaffold_findings(
                    "professional-skill",
                    self.module.parse_sections(
                        f"# example\n\n## Execution Checklist\n\n- {value}\n"
                    ),
                )
                self.assertIn(
                    "profile-mode",
                    {finding["family"] for finding in findings},
                )

    def test_fanout_alone_never_forces_a_hard_classification(self) -> None:
        metrics = self.module.SkillMetrics(
            name="example",
            path="src/professional-skills/example/SKILL.md",
            kind="professional-skill",
            content_target_words=550,
            content_hard_words=650,
            content_target_tokens=850,
            content_hard_tokens=1000,
            word_count=100,
            token_count=150,
            used_by_count=999,
        )
        self.module._classify(metrics)
        self.assertEqual("KEEP", metrics.classification)

    def test_control_scaffold_never_overrides_block(self) -> None:
        metrics = self.module.SkillMetrics(
            name="example",
            path="src/professional-skills/example/SKILL.md",
            kind="professional-skill",
            content_target_words=550,
            content_hard_words=650,
            content_target_tokens=850,
            content_hard_tokens=1000,
            word_count=700,
            token_count=1100,
            over_content_hard=True,
            over_content_hard_words=True,
            over_content_hard_tokens=True,
            high_confidence_control_scaffold=True,
        )
        self.module._classify(metrics)
        self.assertEqual("BLOCK", metrics.classification)

    def test_ledger_boilerplate_requires_hidden_runtime_or_persistence_signal(self) -> None:
        forbidden = (
            "private evidence ledger",
            "private, task-local evidence ledger",
            "hidden evidence ledger",
            "hidden, internal evidence ledger",
            "runtime evidence ledger",
            "persistent evidence ledger",
            "persisted task-local evidence ledger",
        )
        for value in forbidden:
            with self.subTest(value=value):
                self.assertGreater(
                    self.module._control_boilerplate_density(f"- Use a {value}."),
                    0,
                )
        self.assertEqual(
            0,
            self.module._control_boilerplate_density(
                "- Use a visible task-local evidence ledger in the handoff."
            ),
        )

    def test_skill_detector_contract_is_deterministic_and_covers_report_fields(
        self,
    ) -> None:
        first = self.module._skill_detector_contract()
        second = self.module._skill_detector_contract()

        self.assertEqual(first, second)
        self.assertEqual(3, first["schema_version"])
        self.assertEqual("changeforge.skill-content-detector", first["kind"])
        self.assertRegex(
            first["detector_fingerprint"]["value"],
            r"^[0-9a-f]{64}$",
        )
        self.assertEqual(
            "sha256",
            first["detector_fingerprint"]["algorithm"],
        )
        self.assertEqual(
            set(first["required_skill_fields"]),
            {
                "actionability_applicable",
                "actionability_findings",
                "actionability_model",
                "actionable_repeated_phrase_count",
                "classification",
                "control_boilerplate_density",
                "control_scaffold_families",
                "control_scaffold_findings",
                "description_findings",
                "front_loaded_action_score",
                "generic_control_phrase_count",
                "governed_line_count",
                "high_confidence_control_scaffold",
                "kind",
                "line_count",
                "name",
                "projection_overhead_lines",
                "review_reasons",
                "review_state",
                "split_candidate_score",
            },
        )
        self.assertTrue(
            set(first["required_skill_fields"])
            <= set(self.module.SkillMetrics.__dataclass_fields__)
        )
        self.assertEqual(
            ["family", "section", "line", "text", "match"],
            first["finding_fields"],
        )
        self.assertEqual(
            list(self.module.REVIEW_STATE_PRIORITY),
            first["review_state_values"],
        )
        self.assertEqual(
            list(self.module.REVIEW_REASON_PRIORITY),
            first["review_reason_values"],
        )

    def test_skill_detector_fingerprint_binds_repository_source(self) -> None:
        baseline = self.module._skill_detector_fingerprint()
        source_reader = self.module._detector_repository_source_text

        def changed(path: Path) -> str:
            text = source_reader(path)
            if path.resolve() != SCRIPT.resolve():
                return text
            original = (
                'if metrics.professionalism_score < THRESHOLDS["low_professionalism"]:'
            )
            replacement = (
                'if metrics.professionalism_score <= THRESHOLDS["low_professionalism"]:'
            )
            self.assertEqual(1, text.count(original))
            return text.replace(original, replacement, 1)

        with mock.patch.object(
            self.module,
            "_detector_repository_source_text",
            side_effect=changed,
        ):
            self.assertNotEqual(baseline, self.module._skill_detector_fingerprint())

        with mock.patch.dict(
            self.module.THRESHOLDS,
            {"low_professionalism": self.module.THRESHOLDS["low_professionalism"] + 1},
        ):
            self.assertEqual(baseline, self.module._skill_detector_fingerprint())

    def test_review_state_keeps_all_reasons_in_closed_priority_order(self) -> None:
        metrics = self.module.SkillMetrics(
            name="example",
            path="src/professional-skills/example/SKILL.md",
            kind="professional-skill",
            line_count=90,
            governed_line_count=70,
            projection_overhead_lines=20,
            front_loaded_action_score=0,
            actionability_model="runtime-front-loaded-v1",
            actionability_applicable=True,
            high_confidence_control_scaffold=True,
            actionable_repeated_phrase_count=1,
            description_findings=["description: exceeds recommended budget"],
            split_candidate_score=80,
            classification="TIGHTEN_BODY",
        )
        state, reasons = self.module._review_state_and_reasons(
            metrics,
            {
                "review_as_complex_count": 1,
                "tighten_count": 1,
                "hard_fail_count": 1,
                "compound_bullet_count": 1,
            },
        )

        self.assertEqual("BLOCK", state)
        self.assertEqual(
            [
                "ai_readability_hard_fail",
                "ai_readability_compound_bullet",
                "classification_tighten_body",
                "ai_readability_tighten",
                "ai_readability_review_as_complex",
                "professional_projection_pushes_physical_lines_over_80",
                "weak_front_loaded_action",
                "control_boilerplate_risk",
                "actionable_duplicate_content",
                "description_authoring_advisory",
                "split_candidate",
            ],
            reasons,
        )

    def test_projection_line_metrics_use_only_the_canonical_projection(self) -> None:
        canonical = """# example

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | current decision needs a bounded checklist | current evidence already closes the checklist decision | analysis-agent | checklist-result |
"""
        metrics = self.module._base_metrics(
            "professional-skill",
            ROOT / "src/professional-skills/example/SKILL.md",
            canonical,
            {},
            {},
            raw_source=canonical,
            body_is_frontmatter_fragment=False,
        )
        self.assertEqual(7, metrics.line_count)
        self.assertEqual(2, metrics.governed_line_count)
        self.assertEqual(5, metrics.projection_overhead_lines)

        malformed = canonical.replace(
            "|---|---|---|---|---|---|",
            "| --- | --- | --- | --- | --- | --- |",
        )
        malformed_metrics = self.module._base_metrics(
            "professional-skill",
            ROOT / "src/professional-skills/example/SKILL.md",
            malformed,
            {},
            {},
            raw_source=malformed,
            body_is_frontmatter_fragment=False,
        )
        self.assertEqual(malformed_metrics.line_count, malformed_metrics.governed_line_count)
        self.assertEqual(0, malformed_metrics.projection_overhead_lines)

    def test_router_domain_modifier_rewrite_removes_unconditional_mechanism(self) -> None:
        old = (
            "Domain rows are evidence examples for modifier-only Layer 3 selection "
            "after the base Professional route is fixed; they never select or "
            "recompute path, profile, Professional owner, Review Skill, Execution "
            "Level, or Level Basis."
        )
        replacement = (
            "Domain rows add Layer 3 modifiers only after Main fixes the base route."
        )

        def mechanism_candidates(sentence: str) -> list[tuple[str, str]]:
            report = self.module._collect_root_semantic_advisories(
                [
                    {
                        "path": (
                            "src/control-skills/engineering-control-plane/references/"
                            "professional-skill-router.md"
                        ),
                        "layer": "control",
                        "owner": "engineering-control-plane",
                        "kind": "routing-table",
                        "document_part": "body",
                        "text": f"# Professional Skill Router\n\n{sentence}\n",
                    }
                ],
                disposition_entries=[],
            )
            return [
                (item["finding"], item["priority"])
                for item in report["candidates"]
                if item["finding"] == "unconditional_mechanism_candidate"
            ]

        self.assertEqual(
            [("unconditional_mechanism_candidate", "P1")],
            mechanism_candidates(old),
        )
        self.assertEqual([], mechanism_candidates(replacement))

        router = (
            ROOT
            / "src/control-skills/engineering-control-plane/references"
            / "professional-skill-router.md"
        ).read_text(encoding="utf-8")
        self.assertNotIn(old, router)
        self.assertIn(replacement, router)

    def test_frontmatter_fragment_metrics_and_semantics_require_raw_eof_proof(self) -> None:
        body = """# Capability

## High-Value Rules

- Preserve the owned invariant before accepting completion evidence.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | every change requires a checklist | no review decision remains | analysis-agent | checklist-result |"""
        prefix = "---\nname: capability\ndescription: Fixture.\n---\n"
        canonical_source = prefix + body + "\n"
        governed = self.module.strip_frontmatter_body_targeted_reference_projection(
            body,
            canonical_source,
        )

        metrics = self.module._base_metrics(
            "professional-skill",
            ROOT / "src/professional-skills/example/SKILL.md",
            body,
            {},
            {},
            raw_source=canonical_source,
            body_is_frontmatter_fragment=True,
        )
        self.assertEqual(5, metrics.projection_overhead_lines)
        self.assertEqual(metrics.line_count - 5, metrics.governed_line_count)
        self.assertEqual(
            self.module.count_o200k_base_tokens(governed),
            metrics.token_count,
        )

        document = {
            "path": "src/professional-skills/capability/SKILL.md",
            "layer": "professional-skill",
            "owner": "capability",
            "kind": "professional-skill",
            "text": body,
            "governed_text": governed,
            "line_offset": 0,
            "document_part": "body",
        }
        self.assertEqual(
            [],
            self.module._collect_root_semantic_advisories(
                [document],
                disposition_entries=[],
            )["candidates"],
        )

        missing_eof_source = canonical_source[:-1]
        ungoverned = self.module.strip_frontmatter_body_targeted_reference_projection(
            body,
            missing_eof_source,
        )
        self.assertEqual(body, ungoverned)
        missing_eof_metrics = self.module._base_metrics(
            "professional-skill",
            ROOT / "src/professional-skills/example/SKILL.md",
            body,
            {},
            {},
            raw_source=missing_eof_source,
            body_is_frontmatter_fragment=True,
        )
        self.assertEqual(0, missing_eof_metrics.projection_overhead_lines)
        self.assertEqual(
            missing_eof_metrics.line_count,
            missing_eof_metrics.governed_line_count,
        )
        ungoverned_document = {**document, "governed_text": ungoverned}
        self.assertIn(
            "unconditional_mechanism_candidate",
            {
                item["finding"]
                for item in self.module._collect_root_semantic_advisories(
                    [ungoverned_document],
                    disposition_entries=[],
                )["candidates"]
            },
        )

    def test_audit_base_metrics_keep_crlf_projection_in_governed_budget(self) -> None:
        body = (
            "# Fixture\n\n## Targeted References\n\n"
            "| Path | Type | Load when | Do not load when | Required by | Required output |\n"
            "|---|---|---|---|---|---|\n"
            "| [checklist](references/checklist.md) | decision-checklist | "
            "every change requires a checklist | no review decision remains | "
            "analysis-agent | checklist-result |"
        )
        prefix = "---\nname: fixture\ndescription: Fixture.\n---\n"
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            skill = root / "src/professional-skills/fixture/SKILL.md"
            skill.parent.mkdir(parents=True)
            patches = (
                mock.patch.object(
                    self.module,
                    "_load_foundation_content_contracts",
                    return_value={},
                ),
                mock.patch.object(
                    self.module,
                    "_load_used_by_counts",
                    return_value={},
                ),
                mock.patch.object(
                    self.module,
                    "_collect_files",
                    return_value=[("professional-skill", skill)],
                ),
                mock.patch.object(
                    self.module,
                    "_collect_ai_readability",
                    return_value={"documents": []},
                ),
                mock.patch.object(
                    self.module,
                    "_collect_semantic_content_with_application",
                    return_value=(
                        {},
                        {},
                        {
                            "schema_version": 1,
                            "kind": "changeforge.semantic-disposition-application",
                            "status": "current",
                        },
                    ),
                ),
                mock.patch.object(
                    self.module,
                    "count_o200k_base_tokens",
                    side_effect=lambda text: (
                        1001 if "every change requires a checklist" in text else 1
                    ),
                ),
            )
            with contextlib.ExitStack() as stack:
                stack.enter_context(mock.patch.object(self.module, "ROOT", root))
                for patcher in patches:
                    stack.enter_context(patcher)
                skill.write_bytes((prefix + body + "\n").encode("utf-8"))
                canonical = self.module.audit()["metrics"][0]
                self.assertEqual(5, canonical.projection_overhead_lines)
                self.assertEqual(1, canonical.token_count)

                crlf_source = (prefix + body + "\n").replace("\n", "\r\n")
                skill.write_bytes(crlf_source.encode("utf-8"))
                governed = self.module.audit()["metrics"][0]
                self.assertEqual(0, governed.projection_overhead_lines)
                self.assertEqual(governed.line_count, governed.governed_line_count)
                self.assertEqual(1001, governed.token_count)

    def test_root_document_collector_preserves_raw_eof_provenance(self) -> None:
        body = (
            "# Fixture\n\n## Targeted References\n\n"
            "| Path | Type | Load when | Do not load when | Required by | Required output |\n"
            "|---|---|---|---|---|---|\n"
            "| [checklist](references/checklist.md) | decision-checklist | "
            "every change requires a checklist | no review decision remains | "
            "analysis-agent | checklist-result |"
        )
        prefix = "---\nname: fixture\ndescription: Fixture.\n---\n"
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            skills_root = root / "src/professional-skills"
            skill = skills_root / "fixture/SKILL.md"
            skill.parent.mkdir(parents=True)
            with mock.patch.multiple(
                self.module,
                ROOT=root,
                DESCRIPTION_ROOTS=(("professional-skill", skills_root),),
                ROOT_AGENT_DOCUMENTS=(),
                SKILL_CONTENT_EXCEPTIONS_FILE=(
                    root / "config/skill-content-exceptions.yaml"
                ),
            ):
                skill.write_text(prefix + body + "\n", encoding="utf-8")
                documents = self.module._root_skill_documents({})
                body_document = next(
                    item for item in documents if item["document_part"] == "body"
                )
                self.assertNotIn(
                    "every change requires a checklist",
                    body_document["governed_text"],
                )

                skill.write_text(prefix + body, encoding="utf-8")
                documents = self.module._root_skill_documents({})
                body_document = next(
                    item for item in documents if item["document_part"] == "body"
                )
                self.assertIn(
                    "every change requires a checklist",
                    body_document["governed_text"],
                )

                crlf_source = (prefix + body + "\n").replace("\n", "\r\n")
                skill.write_bytes(crlf_source.encode("utf-8"))
                documents = self.module._root_skill_documents({})
                body_document = next(
                    item for item in documents if item["document_part"] == "body"
                )
                self.assertIn(
                    "every change requires a checklist",
                    body_document["governed_text"],
                )
                with mock.patch.object(
                    self.module,
                    "count_o200k_base_tokens",
                    side_effect=lambda text: len(text.split()),
                ):
                    candidates = self.module._collect_root_semantic_advisories(
                        [body_document],
                        disposition_entries=[],
                    )["candidates"]
                self.assertIn(
                    "unconditional_mechanism_candidate",
                    {item["finding"] for item in candidates},
                )

    def test_description_budgets_are_kind_specific(self) -> None:
        self.assertEqual(
            self.module.DESCRIPTION_BUDGETS["control-skill"],
            {"recommended": 220, "hard": 300},
        )
        self.assertEqual(
            self.module.DESCRIPTION_BUDGETS["professional-skill"],
            {"recommended": 220, "hard": 300},
        )
        self.assertEqual(
            self.module.DESCRIPTION_BUDGETS["foundation-capability"],
            {"recommended": 180, "hard": 260},
        )
        self.assertEqual(
            self.module.DESCRIPTION_BUDGETS["domain-extension"],
            {"recommended": 180, "hard": 260},
        )
        self.assertNotIn(
            "description: reads like a workflow summary; move the workflow to the body",
            self.module._description_findings(
                "professional-skill",
                "Use `review-agent` to assess a First Executable Slice for material risk.",
            ),
        )

    def test_all_layers_fit_description_budgets(self) -> None:
        summary = self.module._summary([])
        self.assertEqual(
            summary["description_checked_by_kind"],
            {
                "control-skill": 1,
                "professional-skill": 26,
                "foundation-capability": 150,
                "domain-extension": 13,
            },
        )
        self.assertEqual(summary["description_recommended_over_budget"], 0)
        self.assertEqual(summary["description_hard_over_budget"], 0)
        self.assertEqual(
            summary["description_recommended_over_budget_by_kind"],
            {kind: 0 for kind in self.module.DESCRIPTION_BUDGETS},
        )
        self.assertEqual(
            summary["description_hard_over_budget_by_kind"],
            {kind: 0 for kind in self.module.DESCRIPTION_BUDGETS},
        )
        self.assertNotIn(
            "description: reads like a workflow summary; move the workflow to the body",
            self.module._description_findings(
                "professional-skill",
                "Use `review-agent` to assess a First Executable Slice, rollback, and risk.",
            ),
        )

    def test_compact_foundation_descriptions_keep_discovery_anchors(self) -> None:
        cases = {
            "implementation-structure-design": ("reuse", "method/class/file placement"),
            "data-format-contract-usage": ("protobuf", "old-reader/new-writer"),
            "permission-boundary-modeling": ("tenant isolation", "privilege-escalation"),
            "rust-professional-usage": ("unsafe/ffi", "ownership"),
            "observable-action-sequence-analysis": ("offline", "never infer live"),
        }
        root = ROOT / "src" / "foundation" / "capabilities"
        for name, anchors in cases.items():
            metadata, _raw, _body = self.module.parse_frontmatter(
                root / name / "SKILL.md"
            )
            description = str(metadata["description"]).casefold()
            for anchor in anchors:
                self.assertIn(anchor, description, (name, anchor, description))

    def test_reference_kind_distinguishes_template_index_and_mode_contract(self) -> None:
        self.assertEqual(
            "template",
            self.module._reference_kind(
                "src/foundation/capabilities/_template/references/checklist.md"
            ),
        )
        self.assertEqual(
            "template",
            self.module._reference_kind("references/implementation-handoff-template.md"),
        )
        self.assertEqual("index", self.module._reference_kind("references/index.md"))
        self.assertEqual(
            "mode-contract",
            self.module._reference_kind("references/professional-modes.md"),
        )
        self.assertEqual(
            "targeted",
            self.module._reference_kind("references/review-output-and-gates.md"),
        )
        self.assertEqual(
            "evidence-pattern",
            self.module._reference_kind("references/evidence-patterns.md"),
        )

    def test_reference_content_is_deterministic_and_separates_templates(self) -> None:
        first = self.module._collect_reference_content()
        second = self.module._collect_reference_content()
        self.assertEqual(first, second)
        self.assertEqual(
            sorted(
                first["references"],
                key=self.module._reference_sort_key,
            ),
            first["references"],
        )
        orphan_paths = {item["path"] for item in first["orphans"]}
        template_paths = {item["path"] for item in first["template_assets"]}
        self.assertTrue(template_paths)
        self.assertTrue(any("/_template/" in path for path in template_paths))
        self.assertTrue(orphan_paths.isdisjoint(template_paths))
        multiple_h1_advisories = {
            item["path"]
            for item in first["advisories"]["non_template_multiple_h1"]
        }
        self.assertNotIn(
            "src/control-skills/engineering-control-plane/references/utility-capsule-template.md",
            multiple_h1_advisories,
        )
        for item in first["references"]:
            if item["exists"]:
                self.assertGreater(item["line_count"], 0)
                self.assertGreater(item["token_count"], 0)

    def test_structural_facts_ignore_fenced_headings_and_keep_placeholders(self) -> None:
        markdown = """# Real Reference

Reference body.

Reference type: template
**Load when:** a reusable output shape is needed.
**Do not load when:** current output is already complete.

## Fenced Example

```markdown
# Fake H1
## Fake Empty Heading
```

## Placeholder Section

{{PLACEHOLDER_TEXT}}

## Empty Section

## Quality Gate

1. First decision.
2. Second decision.

| Decision | Evidence |
| --- | --- |
| Third | Source |
| Fourth | Test |
"""
        facts = self.module._markdown_structural_facts(markdown, "targeted")
        self.assertEqual(1, facts["h1_count"])
        self.assertEqual("exactly-one", facts["h1_status"])
        self.assertEqual(
            ["Fenced Example", "Placeholder Section", "Empty Section", "Quality Gate"],
            [item["title"] for item in facts["h2_plus_headings"]],
        )
        self.assertEqual(
            ["Empty Section"],
            [item["title"] for item in facts["empty_headings"]],
        )
        self.assertTrue(facts["has_reference_type_preface"])
        self.assertTrue(facts["has_load_when_preface"])
        self.assertTrue(facts["has_do_not_load_when_preface"])
        self.assertEqual("template", facts["advisory_kind"])
        self.assertEqual("explicit", facts["advisory_kind_source"])
        self.assertEqual(2, facts["decision_list_item_count"])
        self.assertEqual(2, facts["decision_table_item_count"])
        self.assertEqual(4, facts["decision_item_count"])

    def test_local_preface_evidence_ignores_fences_and_accepts_named_headings(self) -> None:
        markdown = """# Reference

```markdown
Reference type: targeted
Load when: fenced text must not count.
Do not load when: fenced text must not count.
```

## Load Trigger

A transaction boundary can change the decision.

## Do Not Load

The root contract already settles the bounded change.
"""
        evidence = self.module._local_preface_evidence(markdown, "src/x/references/r.md")
        self.assertEqual([], evidence["reference_type"])
        self.assertEqual(1, len(evidence["load_when"]))
        self.assertEqual(1, len(evidence["do_not_load_when"]))
        self.assertTrue(evidence["load_when"][0]["accepted"])

    def test_decision_items_are_bounded_per_semantic_section(self) -> None:
        one_section = "# Checklist\n\n## Custody Controls\n\n" + "\n".join(
            f"- Verify custody case {index}." for index in range(16)
        )
        split_sections = (
            "# Checklist\n\n## Custody Controls\n\n"
            + "\n".join(f"- Verify custody case {index}." for index in range(8))
            + "\n\n## Settlement Controls\n\n"
            + "\n".join(f"- Verify settlement case {index}." for index in range(8))
        )

        one_facts = self.module._markdown_structural_facts(
            one_section, "decision-checklist"
        )
        split_facts = self.module._markdown_structural_facts(
            split_sections, "decision-checklist"
        )

        self.assertEqual(16, one_facts["decision_item_count"])
        self.assertEqual(16, one_facts["max_decision_section_item_count"])
        self.assertEqual([16], [row["decision_item_count"] for row in one_facts["decision_sections"]])
        self.assertEqual(16, split_facts["decision_item_count"])
        self.assertEqual(8, split_facts["max_decision_section_item_count"])
        self.assertEqual(
            [8, 8],
            [row["decision_item_count"] for row in split_facts["decision_sections"]],
        )

    def test_invalid_or_repeated_decision_section_headings_cannot_split_quota(self) -> None:
        def items(prefix: str) -> str:
            return "\n".join(f"- Verify {prefix} case {index}." for index in range(8))

        generic = f"# Checklist\n\n## Section 1\n\n{items('first')}\n\n## More\n\n{items('second')}"
        repeated = f"# Checklist\n\n## Custody Controls\n\n{items('first')}\n\n## custody-controls\n\n{items('second')}"
        blank = f"# Checklist\n\n##\n\n{items('first')}\n\n## Section 2\n\n{items('second')}"

        generic_facts = self.module._markdown_structural_facts(
            generic, "decision-checklist"
        )
        repeated_facts = self.module._markdown_structural_facts(
            repeated, "decision-checklist"
        )
        blank_facts = self.module._markdown_structural_facts(
            blank, "decision-checklist"
        )

        self.assertEqual(16, generic_facts["max_decision_section_item_count"])
        self.assertEqual(2, len(generic_facts["invalid_decision_section_headings"]))
        self.assertEqual(16, repeated_facts["max_decision_section_item_count"])
        self.assertEqual(
            [3, 14], repeated_facts["decision_sections"][0]["heading_lines"]
        )
        self.assertEqual(16, blank_facts["max_decision_section_item_count"])
        self.assertEqual(2, len(blank_facts["invalid_decision_section_headings"]))

    def test_payment_and_web3_checklists_report_section_aware_totals(self) -> None:
        expected = {
            "src/domain-extensions/payment-trading-extension/references/checklist.md": (
                27,
                14,
                [3, 6, 4, 14],
            ),
            "src/domain-extensions/web3-product-extension/references/checklist.md": (
                36,
                9,
                [9, 5, 4, 7, 1, 8, 2],
            ),
        }
        for relative, (total, maximum, section_counts) in expected.items():
            with self.subTest(path=relative):
                facts = self.module._markdown_structural_facts(
                    (ROOT / relative).read_text(encoding="utf-8"),
                    "decision-checklist",
                )
                self.assertEqual(total, facts["decision_item_count"])
                self.assertEqual(maximum, facts["max_decision_section_item_count"])
                self.assertEqual(
                    section_counts,
                    [row["decision_item_count"] for row in facts["decision_sections"]],
                )

    def test_rds_006_stale_reference_dispositions_are_absent(self) -> None:
        config = self.module.load_yaml_file(
            ROOT / "config/skill-content-exceptions.yaml"
        )
        entries = config["reference_semantic_dispositions"]["entries"]
        stale_paths = {
            "src/foundation/capabilities/agent-execution-discipline/references/execution-report-and-gates.md",
            "src/foundation/capabilities/agent-execution-discipline/references/completion-evidence.md",
        }
        self.assertTrue(stale_paths.isdisjoint({entry["path"] for entry in entries}))
        self.assertNotIn(
            "f8079953197bd9e94700ad08114994c716cf97ade3ca233d51918e5b67bdc947",
            {entry["candidate_id"] for entry in entries},
        )

    def test_fence_parser_requires_same_marker_and_sufficient_legal_close(self) -> None:
        lines = [
            "````markdown",
            "Load when: fenced text must not count.",
            "```",
            "~~~~",
            "```` trailing-text",
            "Do not load when: still fenced.",
            "````",
            "Load when: visible metadata counts.",
        ]
        annotated = self.module._strip_fenced(lines)
        self.assertEqual(
            [True, True, True, True, True, True, True, False],
            [in_fence for _index, _line, in_fence in annotated],
        )

    def test_safe_markdown_rejects_ancestor_symlink_before_read(self) -> None:
        original_root = self.module.ROOT
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            owner = root / "src/professional-skills/owner"
            owner.mkdir(parents=True)
            outside = root / "outside"
            outside.mkdir()
            (outside / "target.md").write_text("# External\n", encoding="utf-8")
            (owner / "references").symlink_to(outside, target_is_directory=True)
            target = owner / "references/target.md"
            self.module.ROOT = root
            try:
                with mock.patch.object(
                    Path,
                    "read_text",
                    side_effect=AssertionError("unsafe source was read"),
                ) as read_text:
                    markdown, errors = self.module._safe_markdown_text(
                        target,
                        allowed_root=owner / "references",
                        source="local",
                        target="src/professional-skills/owner/references/target.md",
                    )
                read_text.assert_not_called()
            finally:
                self.module.ROOT = original_root
        self.assertIsNone(markdown)
        self.assertEqual("source-symlink-chain", errors[0]["code"])

    def test_indexed_references_rejects_symlinked_registry_before_yaml_read(self) -> None:
        original_root = self.module.ROOT
        original_sources = self.module.REFERENCE_SOURCES
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skills_root = root / "src/professional-skills"
            registry_root = root / "src/registry"
            skills_root.mkdir(parents=True)
            registry_root.mkdir(parents=True)
            outside = root / "outside.yaml"
            outside.write_text("professional_skills: []\n", encoding="utf-8")
            registry = registry_root / "professional-skills.yaml"
            registry.symlink_to(outside)
            self.module.ROOT = root
            self.module.REFERENCE_SOURCES = (
                ("professional", registry, "professional_skills", skills_root),
            )
            try:
                with mock.patch.object(
                    self.module,
                    "load_yaml_file",
                    side_effect=AssertionError("unsafe registry was read"),
                ) as load_yaml:
                    references, errors, registry_texts = self.module._indexed_references()
                load_yaml.assert_not_called()
            finally:
                self.module.ROOT = original_root
                self.module.REFERENCE_SOURCES = original_sources
        self.assertEqual([], references)
        self.assertEqual({}, registry_texts)
        self.assertTrue(any(item["code"] == "source-symlink-chain" for item in errors))

    def test_indexed_references_rejects_owner_and_reference_escape_paths(self) -> None:
        original_root = self.module.ROOT
        original_sources = self.module.REFERENCE_SOURCES
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skills_root = root / "src/professional-skills"
            registry_root = root / "src/registry"
            skills_root.mkdir(parents=True)
            registry_root.mkdir(parents=True)
            registry = registry_root / "professional-skills.yaml"
            registry.write_text("professional_skills: []\n", encoding="utf-8")
            outside_owner = root / "src/domain-extensions/outside"
            outside_owner.mkdir(parents=True)
            entries = [
                {"name": "dotdot", "path": "../outside", "reference_index": []},
                {"name": "absolute", "path": str(outside_owner), "reference_index": []},
                {
                    "name": "other-layer",
                    "path": "src/domain-extensions/outside",
                    "reference_index": [],
                },
            ]
            owner = skills_root / "owner"
            (owner / "references").mkdir(parents=True)
            entries.append(
                {
                    "name": "owner",
                    "path": "src/professional-skills/owner",
                    "reference_index": [
                        "../escape.md",
                        str(root / "outside.md"),
                        "examples/not-a-reference.md",
                    ],
                }
            )
            self.module.ROOT = root
            self.module.REFERENCE_SOURCES = (
                ("professional", registry, "professional_skills", skills_root),
            )
            try:
                with mock.patch.object(
                    self.module,
                    "load_yaml_file",
                    return_value={"professional_skills": entries},
                ):
                    references, errors, _registry_texts = self.module._indexed_references()
            finally:
                self.module.ROOT = original_root
                self.module.REFERENCE_SOURCES = original_sources
        self.assertEqual([], references)
        codes = [item["code"] for item in errors]
        self.assertEqual(2, codes.count("registry-owner-path-outside-skills-root"))
        self.assertIn("source-path-outside-owner", codes)
        self.assertEqual(1, codes.count("invalid-registry-reference-contract"))

    def test_physical_references_rejects_skills_root_symlink_before_iteration(self) -> None:
        original_root = self.module.ROOT
        original_sources = self.module.REFERENCE_SOURCES
        for ancestor in (False, True):
            with self.subTest(ancestor=ancestor), tempfile.TemporaryDirectory() as directory:
                root = Path(directory) / "repo"
                outside = Path(directory) / "outside"
                outside.mkdir(parents=True)
                if ancestor:
                    root.mkdir()
                    (root / "src").symlink_to(outside, target_is_directory=True)
                else:
                    (root / "src").mkdir(parents=True)
                    (root / "src/professional-skills").symlink_to(
                        outside, target_is_directory=True
                    )
                skills_root = root / "src/professional-skills"
                registry = root / "src/registry/professional-skills.yaml"
                self.module.ROOT = root
                self.module.REFERENCE_SOURCES = (
                    ("professional", registry, "professional_skills", skills_root),
                )
                try:
                    with mock.patch.object(
                        Path,
                        "iterdir",
                        side_effect=AssertionError("unsafe skills root was iterated"),
                    ) as iterdir:
                        references, markdown, errors = self.module._physical_references()
                    iterdir.assert_not_called()
                finally:
                    self.module.ROOT = original_root
                    self.module.REFERENCE_SOURCES = original_sources
                self.assertEqual([], references)
                self.assertEqual({}, markdown)
                self.assertTrue(
                    any(item["code"] == "source-symlink-chain" for item in errors),
                    errors,
                )

    def test_root_audit_registry_and_exception_symlinks_fail_before_yaml_load(self) -> None:
        original_root = self.module.ROOT
        original_capabilities = self.module.CAPABILITIES_REGISTRY
        original_exceptions = self.module.SKILL_CONTENT_EXCEPTIONS_FILE
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            (root / "src/registry").mkdir(parents=True)
            (root / "config").mkdir()
            outside_registry = Path(directory) / "outside-registry.yaml"
            outside_registry.write_text("foundation_skills: []\n", encoding="utf-8")
            outside_exceptions = Path(directory) / "outside-exceptions.yaml"
            outside_exceptions.write_text(
                "reference_semantic_dispositions:\n  schema_version: 2\n  entries: []\n",
                encoding="utf-8",
            )
            capabilities = root / "src/registry/foundation-skills.yaml"
            exceptions = root / "config/skill-content-exceptions.yaml"
            capabilities.symlink_to(outside_registry)
            exceptions.symlink_to(outside_exceptions)
            self.module.ROOT = root
            self.module.CAPABILITIES_REGISTRY = capabilities
            self.module.SKILL_CONTENT_EXCEPTIONS_FILE = exceptions
            try:
                for consumer in (
                    self.module._load_foundation_content_contracts,
                    self.module._load_used_by_counts,
                    self.module._load_reference_semantic_dispositions,
                ):
                    with self.subTest(consumer=consumer.__name__), mock.patch.object(
                        self.module,
                        "load_yaml_file",
                        side_effect=AssertionError("external YAML was loaded"),
                    ) as load_yaml:
                        with self.assertRaises(self.module.ValidationProblem):
                            consumer()
                    load_yaml.assert_not_called()
            finally:
                self.module.ROOT = original_root
                self.module.CAPABILITIES_REGISTRY = original_capabilities
                self.module.SKILL_CONTENT_EXCEPTIONS_FILE = original_exceptions

    def test_description_root_symlink_fails_before_iteration(self) -> None:
        original_root = self.module.ROOT
        original_description_roots = self.module.DESCRIPTION_ROOTS
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            outside = Path(directory) / "outside-skills"
            (outside / "external").mkdir(parents=True)
            (outside / "external/SKILL.md").write_text(
                "---\nname: external\ndescription: external payload\n---\n# External\n",
                encoding="utf-8",
            )
            (root / "src").mkdir(parents=True)
            description_root = root / "src/professional-skills"
            description_root.symlink_to(outside, target_is_directory=True)
            self.module.ROOT = root
            self.module.DESCRIPTION_ROOTS = (
                ("professional-skill", description_root),
            )
            try:
                for consumer in (
                    self.module._collect_files,
                    self.module._collect_description_lengths_by_kind,
                ):
                    with self.subTest(consumer=consumer.__name__), mock.patch.object(
                        Path,
                        "iterdir",
                        side_effect=AssertionError("external skills root was iterated"),
                    ) as iterdir:
                        with self.assertRaises(self.module.ValidationProblem):
                            consumer()
                    iterdir.assert_not_called()
            finally:
                self.module.ROOT = original_root
                self.module.DESCRIPTION_ROOTS = original_description_roots

    def test_symlinked_skill_file_fails_before_content_read(self) -> None:
        original_root = self.module.ROOT
        original_description_roots = self.module.DESCRIPTION_ROOTS
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            description_root = root / "src/professional-skills"
            skill_dir = description_root / "owner"
            skill_dir.mkdir(parents=True)
            outside = Path(directory) / "outside-skill.md"
            outside.write_text("# External payload\n", encoding="utf-8")
            (skill_dir / "SKILL.md").symlink_to(outside)
            self.module.ROOT = root
            self.module.DESCRIPTION_ROOTS = (
                ("professional-skill", description_root),
            )
            try:
                with mock.patch.object(
                    Path,
                    "read_text",
                    side_effect=AssertionError("external SKILL was read"),
                ) as read_text:
                    with self.assertRaises(self.module.ValidationProblem):
                        self.module._collect_files()
                read_text.assert_not_called()
            finally:
                self.module.ROOT = original_root
                self.module.DESCRIPTION_ROOTS = original_description_roots

    def test_main_does_not_generate_reports_after_unsafe_registry(self) -> None:
        originals = {
            "ROOT": self.module.ROOT,
            "CAPABILITIES_REGISTRY": self.module.CAPABILITIES_REGISTRY,
            "REPORTS_DIR": self.module.REPORTS_DIR,
            "JSON_REPORT": self.module.JSON_REPORT,
            "MARKDOWN_REPORT": self.module.MARKDOWN_REPORT,
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            registry_root = root / "src/registry"
            registry_root.mkdir(parents=True)
            outside = Path(directory) / "outside.yaml"
            outside.write_text("foundation_skills: []\n", encoding="utf-8")
            registry = registry_root / "foundation-skills.yaml"
            registry.symlink_to(outside)
            reports = root / "reports"
            self.module.ROOT = root
            self.module.CAPABILITIES_REGISTRY = registry
            self.module.REPORTS_DIR = reports
            self.module.JSON_REPORT = reports / "skill-content-audit.json"
            self.module.MARKDOWN_REPORT = reports / "skill-content-audit.md"
            try:
                with mock.patch.object(
                    self.module,
                    "load_yaml_file",
                    side_effect=AssertionError("external registry was loaded"),
                ) as load_yaml, mock.patch.object(
                    self.module,
                    "_load_reference_semantic_dispositions",
                    return_value=({"schema_version": 2, "entries": []}, []),
                ):
                    status = self.module.main(["--gate", "authoring"])
                load_yaml.assert_not_called()
            finally:
                for name, value in originals.items():
                    setattr(self.module, name, value)
            self.assertEqual(1, status)
            self.assertFalse(reports.exists())

    def test_main_preserves_reports_for_reference_source_safety_errors(self) -> None:
        original_root = self.module.ROOT
        original_sources = self.module.REFERENCE_SOURCES
        original_reports = self.module.REPORTS_DIR
        original_json = self.module.JSON_REPORT
        original_markdown = self.module.MARKDOWN_REPORT
        original_exceptions = self.module.SKILL_CONTENT_EXCEPTIONS_FILE
        original_load_yaml = self.module.load_yaml_file

        def configure_exceptions(root: Path) -> None:
            path = root / "config/skill-content-exceptions.yaml"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "reference_semantic_dispositions:\n  schema_version: 2\n  entries: []\n",
                encoding="utf-8",
            )
            self.module.SKILL_CONTENT_EXCEPTIONS_FILE = path

        def assert_preserved(root: Path, reference_content: dict, code: str) -> None:
            reports = root / "reports"
            reports.mkdir(parents=True)
            json_report = reports / "skill-content-audit.json"
            markdown_report = reports / "skill-content-audit.md"
            json_report.write_text("JSON SENTINEL\n", encoding="utf-8")
            markdown_report.write_text("MARKDOWN SENTINEL\n", encoding="utf-8")
            self.module.REPORTS_DIR = reports
            self.module.JSON_REPORT = json_report
            self.module.MARKDOWN_REPORT = markdown_report
            result = {
                "metrics": [],
                "raw_common_lines": {},
                "actionable_common_lines": {},
                "optimality_files": [],
                "reference_content": reference_content,
            }
            with mock.patch.object(self.module, "audit", return_value=result), mock.patch.object(
                self.module,
                "_summary",
                side_effect=AssertionError("summary ran after source safety failure"),
            ):
                status = self.module.main(["--gate", "authoring"])
            self.assertEqual(1, status, code)
            self.assertEqual("JSON SENTINEL\n", json_report.read_text(encoding="utf-8"))
            self.assertEqual(
                "MARKDOWN SENTINEL\n", markdown_report.read_text(encoding="utf-8")
            )

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            try:
                # Unsafe Reference registry: no YAML load and reports stay intact.
                root = base / "registry-case"
                skills_root = root / "src/professional-skills"
                registry_root = root / "src/registry"
                skills_root.mkdir(parents=True)
                registry_root.mkdir(parents=True)
                outside_registry = base / "outside-registry.yaml"
                outside_registry.write_text("professional_skills: []\n", encoding="utf-8")
                registry = registry_root / "professional-skills.yaml"
                registry.symlink_to(outside_registry)
                self.module.ROOT = root
                configure_exceptions(root)
                self.module.REFERENCE_SOURCES = (
                    ("professional", registry, "professional_skills", skills_root),
                )

                def reject_registry_load(path: Path):
                    if path == registry:
                        raise AssertionError("external registry was loaded")
                    return original_load_yaml(path)

                with mock.patch.object(
                    self.module,
                    "load_yaml_file",
                    side_effect=reject_registry_load,
                ) as load_yaml:
                    content = self.module._collect_reference_content()
                self.assertFalse(any(call.args[0] == registry for call in load_yaml.call_args_list))
                assert_preserved(root, content, "source-symlink-chain")

                # Registry owner escapes its declared skills root.
                root = base / "owner-case"
                skills_root = root / "src/professional-skills"
                registry_root = root / "src/registry"
                skills_root.mkdir(parents=True)
                registry_root.mkdir(parents=True)
                outside_owner = root / "src/domain-extensions/outside"
                outside_owner.mkdir(parents=True)
                registry = registry_root / "professional-skills.yaml"
                registry.write_text("professional_skills: []\n", encoding="utf-8")
                self.module.ROOT = root
                configure_exceptions(root)
                self.module.REFERENCE_SOURCES = (
                    ("professional", registry, "professional_skills", skills_root),
                )

                owner_registry_data = {
                    "professional_skills": [
                        {
                            "name": "outside",
                            "path": "src/domain-extensions/outside",
                            "reference_index": [],
                        }
                    ]
                }

                def load_owner_case(path: Path):
                    return owner_registry_data if path == registry else original_load_yaml(path)

                with mock.patch.object(
                    self.module,
                    "load_yaml_file",
                    side_effect=load_owner_case,
                ):
                    content = self.module._collect_reference_content()
                assert_preserved(root, content, "source-path-outside-owner")

                # Registered Reference file is an external symlink and is never read.
                root = base / "reference-case"
                skills_root = root / "src/professional-skills"
                owner = skills_root / "owner"
                references = owner / "references"
                registry_root = root / "src/registry"
                references.mkdir(parents=True)
                registry_root.mkdir(parents=True)
                registry = registry_root / "professional-skills.yaml"
                registry.write_text("professional_skills: []\n", encoding="utf-8")
                outside_reference = base / "outside-reference.md"
                outside_reference.write_text("# EXTERNAL PAYLOAD\n", encoding="utf-8")
                reference = references / "target.md"
                reference.symlink_to(outside_reference)
                self.module.ROOT = root
                configure_exceptions(root)
                self.module.REFERENCE_SOURCES = (
                    ("professional", registry, "professional_skills", skills_root),
                )
                original_read_text = Path.read_text

                def guarded_read_text(path: Path, *args, **kwargs):
                    if path == reference:
                        raise AssertionError("external Reference was read")
                    return original_read_text(path, *args, **kwargs)

                reference_registry_data = {
                    "professional_skills": [
                        {
                            "name": "owner",
                            "path": "src/professional-skills/owner",
                            "reference_index": ["references/target.md"],
                        }
                    ]
                }

                def load_reference_case(path: Path):
                    return reference_registry_data if path == registry else original_load_yaml(path)

                with mock.patch.object(
                    self.module,
                    "load_yaml_file",
                    side_effect=load_reference_case,
                ), mock.patch.object(Path, "read_text", guarded_read_text):
                    content = self.module._collect_reference_content()
                assert_preserved(root, content, "source-symlink-chain")
            finally:
                self.module.ROOT = original_root
                self.module.REFERENCE_SOURCES = original_sources
                self.module.REPORTS_DIR = original_reports
                self.module.JSON_REPORT = original_json
                self.module.MARKDOWN_REPORT = original_markdown
                self.module.SKILL_CONTENT_EXCEPTIONS_FILE = original_exceptions

    def test_child_directory_safety_gate_precedes_is_dir(self) -> None:
        original_root = self.module.ROOT
        original_description_roots = self.module.DESCRIPTION_ROOTS
        original_sources = self.module.REFERENCE_SOURCES
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            outside = Path(directory) / "outside"
            outside.mkdir(parents=True)
            description_root = root / "src/professional-skills"
            description_root.mkdir(parents=True)
            (description_root / "linked-skill").symlink_to(
                outside, target_is_directory=True
            )
            registry_root = root / "src/registry"
            registry_root.mkdir(parents=True)
            registry = registry_root / "professional-skills.yaml"
            registry.write_text("professional_skills: []\n", encoding="utf-8")
            self.module.ROOT = root
            self.module.DESCRIPTION_ROOTS = (
                ("professional-skill", description_root),
            )
            self.module.REFERENCE_SOURCES = (
                ("professional", registry, "professional_skills", description_root),
            )
            try:
                with mock.patch.object(
                    Path,
                    "is_dir",
                    side_effect=AssertionError("is_dir ran before child safety gate"),
                ) as is_dir:
                    with self.assertRaises(self.module.ValidationProblem):
                        self.module._collect_files()
                    _references, _markdown, errors = self.module._physical_references()
                is_dir.assert_not_called()
            finally:
                self.module.ROOT = original_root
                self.module.DESCRIPTION_ROOTS = original_description_roots
                self.module.REFERENCE_SOURCES = original_sources
        self.assertTrue(any(item["code"] == "source-symlink-chain" for item in errors))

    def test_effective_preface_preserves_precedence_and_only_provable_conflicts(self) -> None:
        local = self.module._preface_evidence(
            source="local", path="src/x/references/r.md", line=3,
            value="A material transaction boundary changes.",
        )
        index = self.module._preface_evidence(
            source="reference-index", path="src/x/references/index.md", line=7,
            value="A multi-write invariant needs transaction evidence.",
        )
        result = self.module._effective_preface(
            {
                "reference_type": [],
                "load_when": [index, local],
                "do_not_load_when": [],
            }
        )
        self.assertEqual("resolved", result["load_when"]["status"])
        self.assertEqual("local", result["load_when"]["source"])
        self.assertEqual([], result["conflicts"])

        type_result = self.module._effective_preface(
            {
                "reference_type": [
                    self.module._preface_evidence(
                        source="local", path="src/x/references/r.md", line=2,
                        value="targeted",
                    ),
                    self.module._preface_evidence(
                        source="reference-index", path="src/x/references/index.md", line=7,
                        value="mode-contract",
                    ),
                ],
                "load_when": [],
                "do_not_load_when": [],
            }
        )
        self.assertEqual("conflict", type_result["reference_type"]["status"])
        self.assertIsNone(type_result["reference_type"]["value"])

    def test_index_and_root_preface_sources_are_exact_and_owner_bounded(self) -> None:
        original_root = self.module.ROOT
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            owner = root / "src/professional-skills/owner"
            references = owner / "references"
            references.mkdir(parents=True)
            (references / "target.md").write_text("# Target\n", encoding="utf-8")
            (references / "mode.md").write_text("# Mode\n", encoding="utf-8")
            (references / "index.md").write_text(
                """# Index

| Reference | Load When | Do Not Load When |
| --- | --- | --- |
| [target.md](target.md) | A transaction boundary is material. | The root contract settles the decision. |

```markdown
| [target.md](target.md) | Fenced fake. | Fenced fake. |
```
""",
                encoding="utf-8",
            )
            (owner / "SKILL.md").write_text(
                """# Owner

## Targeted References

- Read [target.md](references/target.md) only when its subject changes the current decision.
- `mode`: load only [mode.md](references/mode.md).
- Never load one mode reference while executing another.
- Read [escape](../other/references/escape.md) when unsafe.
""",
                encoding="utf-8",
            )
            self.module.ROOT = root
            try:
                paths = {
                    "src/professional-skills/owner/references/index.md",
                    "src/professional-skills/owner/references/target.md",
                    "src/professional-skills/owner/references/mode.md",
                }
                indexed, index_errors = self.module._owner_index_preface_evidence(owner, paths)
                rooted, root_errors = self.module._owner_root_preface_evidence(owner, paths)
            finally:
                self.module.ROOT = original_root
        self.assertEqual([], index_errors)
        self.assertEqual(1, len(indexed["src/professional-skills/owner/references/target.md"]["load_when"]))
        target_root = rooted["src/professional-skills/owner/references/target.md"]
        self.assertFalse(target_root["load_when"][0]["accepted"])
        mode_root = rooted["src/professional-skills/owner/references/mode.md"]
        self.assertEqual("mode-contract", mode_root["reference_type"][0]["value"])
        self.assertEqual(1, len(mode_root["do_not_load_when"]))
        self.assertTrue(any(item["code"] == "cross-owner-reference-target" for item in root_errors))

    def test_root_compound_conditions_resolve_independently_and_reject_unconditional_negative(self) -> None:
        original_root = self.module.ROOT
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            owner = root / "src/domain-extensions/owner"
            references = owner / "references"
            references.mkdir(parents=True)
            for name in ("compound.md", "unconditional.md", "other.md"):
                (references / name).write_text(f"# {name}\n", encoding="utf-8")
            (owner / "SKILL.md").write_text(
                """# Owner

## Targeted References

- Read [compound](references/compound.md) only for a decision-relevant device risk; otherwise do not load it.
- Do not load [unconditional](references/unconditional.md).
- Read [two](references/compound.md) and [targets](references/other.md) when ambiguous.
""",
                encoding="utf-8",
            )
            self.module.ROOT = root
            try:
                paths = {
                    f"src/domain-extensions/owner/references/{name}"
                    for name in ("compound.md", "unconditional.md", "other.md")
                }
                evidence, errors = self.module._owner_root_preface_evidence(owner, paths)
            finally:
                self.module.ROOT = original_root
        compound = evidence["src/domain-extensions/owner/references/compound.md"]
        self.assertTrue(compound["load_when"][0]["accepted"])
        self.assertTrue(compound["do_not_load_when"][0]["accepted"])
        unconditional = evidence["src/domain-extensions/owner/references/unconditional.md"]
        self.assertFalse(unconditional["do_not_load_when"][0]["accepted"])
        self.assertEqual(
            "missing",
            self.module._effective_preface(unconditional)["do_not_load_when"]["status"],
        )
        self.assertTrue(any(item["code"] == "ambiguous-root-link" for item in errors))

    def test_index_tables_require_separator_complete_rows_and_global_unique_target(self) -> None:
        original_root = self.module.ROOT
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            owner = root / "src/professional-skills/owner"
            references = owner / "references"
            references.mkdir(parents=True)
            (references / "target.md").write_text("# Target\n", encoding="utf-8")
            target = "src/professional-skills/owner/references/target.md"
            (references / "index.md").write_text(
                """# Index

| Reference | Load When | Do Not Load When |
| --- | --- | --- |
| [target](target.md) | A material transaction boundary changes. | The owner contract settles the decision. |

| Reference | Load When | Do Not Load When |
| --- | --- | --- |
| [target](target.md) | when needed | The bounded root already proves the outcome. |

| Reference | Load When | Do Not Load When |
| [target](target.md) | Missing separator must fail. | This row must not be read. |

| Reference | Load When | Do Not Load When |
| --- | --- | --- |
| [target](target.md) | Missing final cell |
""",
                encoding="utf-8",
            )
            self.module.ROOT = root
            try:
                evidence, errors = self.module._owner_index_preface_evidence(
                    owner,
                    {target, "src/professional-skills/owner/references/index.md"},
                )
            finally:
                self.module.ROOT = original_root
        codes = [item["code"] for item in errors]
        self.assertIn("duplicate-index-row", codes)
        self.assertIn("malformed-index-separator", codes)
        self.assertIn("malformed-index-row", codes)
        result = self.module._effective_preface(evidence[target])
        self.assertEqual("conflict", result["load_when"]["status"])

    def test_local_valid_and_invalid_declarations_fail_closed(self) -> None:
        evidence = self.module._local_preface_evidence(
            """# Reference

Reference type: targeted
Reference type: nonsense
Load when: A material transaction boundary changes.
Load when: when needed
""",
            "src/skills/owner/references/target.md",
        )
        effective = self.module._effective_preface(evidence)
        self.assertEqual("conflict", effective["reference_type"]["status"])
        self.assertEqual("conflict", effective["load_when"]["status"])

        invalid_only = self.module._effective_preface(
            {
                "reference_type": [
                    self.module._preface_evidence(
                        source="local",
                        path="src/skills/owner/references/target.md",
                        line=2,
                        value="nonsense",
                        accepted=False,
                        reason="unrecognized-reference-type",
                    )
                ],
                "load_when": [],
                "do_not_load_when": [],
            }
        )
        self.assertEqual("invalid", invalid_only["reference_type"]["status"])

    def test_effective_reference_type_controls_line_budget_kind(self) -> None:
        metrics = self.module.ReferenceMetrics(
            layer="professional",
            owner="owner",
            path="src/professional-skills/owner/references/professional-modes.md",
            kind="mode-contract",
            exists=True,
            advisory_kind="mode-contract",
            effective_preface=self.module._effective_preface(
                {
                    "reference_type": [
                        self.module._preface_evidence(
                            source="reference-index",
                            path="src/professional-skills/owner/references/index.md",
                            line=7,
                            value="targeted",
                        )
                    ],
                    "load_when": [],
                    "do_not_load_when": [],
                }
            ),
        )
        self.assertEqual("targeted", self.module._reference_budget_kind(metrics))

    def test_fenced_prefaces_do_not_override_inferred_advisory_kind(self) -> None:
        markdown = """# Reference

Body text.

```markdown
Reference type: template
Load when: never
Do not load when: never
## Fake Heading
```
"""
        facts = self.module._markdown_structural_facts(markdown, "mode-contract")
        self.assertFalse(facts["has_reference_type_preface"])
        self.assertFalse(facts["has_load_when_preface"])
        self.assertFalse(facts["has_do_not_load_when_preface"])
        self.assertEqual("mode-contract", facts["advisory_kind"])
        self.assertEqual("inferred", facts["advisory_kind_source"])
        self.assertEqual([], facts["h2_plus_headings"])

    def test_absolute_candidates_downgrade_conditions_and_ignore_examples(self) -> None:
        report = self.module._collect_reference_semantic_advisories(
            [
                {
                    "path": "src/foundation/example/references/rules.md",
                    "layer": "foundation",
                    "owner": "example",
                    "text": """# Rules

## Decisions

- Every consumer must use mutual TLS.
- If current evidence shows a legacy client, all callers must use the compatibility bridge.
- Use this reference only for migration review.
- The reviewer remains read-only.
- The restored copy protects not only the primary snapshot.
- Does every consumer require a new credential?

| Claim | What it does not prove |
| --- | --- |
| The inspected route is covered. | All deployments are safe. |

## Anti-Patterns To Reject

- Never validate only the happy path.

## Examples

- All jobs must finish within 30 minutes.

```text
Never retain this example.
```
""",
                }
            ]
        )
        rows = [
            item
            for item in report["candidates"]
            if item["finding"] == "unconditional_absolute_candidate"
        ]
        self.assertEqual(6, len(rows))
        self.assertEqual(1, sum(item["governance_status"] == "untriaged" for item in rows))
        self.assertEqual(5, sum(item["detector_status"] == "downgraded" for item in rows))
        self.assertEqual(
            {
                "negative_or_proof_limit_table_context",
                "not_only_idiom",
                "question_context",
                "reference_loading_scope",
                "same_sentence_conditional_language",
            },
            {
                item["downgrade_reasons"][0]
                for item in rows
                if item["detector_status"] == "downgraded"
            },
        )
        self.assertFalse(any("read-only" in item["preview"] for item in rows))
        self.assertFalse(any("happy path" in item["preview"] for item in rows))
        self.assertFalse(any("finish within" in item["preview"] for item in rows))
        self.assertFalse(any("retain this example" in item["preview"] for item in rows))

    def test_wrapped_diagnosis_condition_preserves_range_and_is_downgraded(self) -> None:
        path = (
            ROOT
            / "src/professional-skills/engineering-change-analysis/references/diagnosis-only.md"
        )
        report = self.module._collect_reference_semantic_advisories(
            [
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "layer": "professional",
                    "owner": "engineering-change-analysis",
                    "text": path.read_text(encoding="utf-8"),
                }
            ]
        )
        rows = [
            item
            for item in report["candidates"]
            if "Verified Cause" in item["preview"]
        ]
        self.assertEqual(1, len(rows))
        self.assertEqual("downgraded", rows[0]["detector_status"])
        self.assertEqual(
            ["same_sentence_conditional_language"], rows[0]["downgrade_reasons"]
        )
        self.assertEqual({"start": 26, "end": 27}, rows[0]["occurrences"][0]["lines"])

    def test_scoped_only_and_preceding_context_are_downgraded(self) -> None:
        report = self.module._collect_reference_semantic_advisories(
            [
                {
                    "path": "scope.md",
                    "layer": "professional",
                    "owner": "example",
                    "text": """# Scope

- Use this reference only for migration review. All callers must preserve compatibility.
- Use this index to load only the local reference needed for this risk.
- Load only the sections needed for the selected decision.
- Remove the old path only after consumer evidence is current.

## Proof Limits

All external consumers are covered.
""",
                }
            ]
        )
        rows = [
            item
            for item in report["candidates"]
            if item["finding"] == "unconditional_absolute_candidate"
        ]
        self.assertEqual(6, len(rows))
        self.assertTrue(all(item["detector_status"] == "downgraded" for item in rows))
        self.assertIn(
            "preceding_reference_loading_scope",
            {reason for item in rows for reason in item.get("downgrade_reasons", [])},
        )
        self.assertIn(
            "scoped_only_restriction",
            {reason for item in rows for reason in item.get("downgrade_reasons", [])},
        )

    def test_absolute_table_context_rules_have_exact_positive_and_negative_boundaries(self) -> None:
        self.assertEqual(
            ["Notes | Scope", "Use When", "Required Control"],
            self.module._split_markdown_table_row(
                r"| Notes \| Scope | Use When | Required Control |"
            ),
        )
        self.assertEqual(
            ["`notes|scope`", "Use When", "Required Control"],
            self.module._split_markdown_table_row(
                "| `notes|scope` | Use When | Required Control |"
            ),
        )
        for header in self.module.ABSOLUTE_TABLE_CONTEXT_HEADERS:
            with self.subTest(r2_header=header):
                self.assertTrue(
                    self.module._absolute_exact_table_context(
                        {"unit-kind:table-cell", f"table-header:{header}"}
                    )
                )
        for header in ("required control", "guardrail", "minimum evidence"):
            with self.subTest(r2_negative_header=header):
                self.assertFalse(
                    self.module._absolute_exact_table_context(
                        {"unit-kind:table-cell", f"table-header:{header}"}
                    )
                )
        documents = [
            {
                "path": "r2-positive.md",
                "layer": "foundation",
                "owner": "r2-positive",
                "kind": "targeted",
                "text": "# R2\n\n| Notes \\| Scope | Use When | Required Control |\n| --- | --- | --- |\n| `notes|scope` | Load all references. | Every Kubernetes service must conform. |\n",
            },
            {
                "path": "r5.md",
                "layer": "foundation",
                "owner": "r5",
                "kind": "evidence-pattern",
                "text": "# R5\n\n| Boundary record | Notes |\n| --- | --- |\n| Read-only inspection; never refresh fixtures. | Context |\n| Read-only inspection; every database must use PostgreSQL. | Context |\n",
            },
            {
                "path": "r7.md",
                "layer": "foundation",
                "owner": "r7",
                "kind": "targeted",
                "text": "# R7\n\n| Location | Runtime fit | Condition | Allowed Actions |\n| --- | --- | --- | --- |\n| Build/test only | Builder stage only. | Never existed or unavailable | All available actions |\n| All services must conform | Every database PostgreSQL only | Always choose PostgreSQL | Only deploy Kubernetes |\n",
            },
        ]
        report = self.module._collect_reference_semantic_advisories(
            documents, disposition_entries=[]
        )
        rows = {
            item["preview"]: item
            for item in report["candidates"]
            if item["finding"] == "unconditional_absolute_candidate"
        }
        self.assertEqual(
            ["exact_table_context_header"],
            rows["Load all references."]["downgrade_reasons"],
        )
        self.assertEqual(
            ["boundary_record_authority"],
            rows["Read-only inspection; never refresh fixtures."]["downgrade_reasons"],
        )
        self.assertEqual(
            ["short_classification_fragment"],
            rows["Build/test only"]["downgrade_reasons"],
        )
        self.assertEqual(
            ["short_classification_fragment"],
            rows["Builder stage only."]["downgrade_reasons"],
        )
        self.assertEqual(
            ["short_classification_fragment"],
            rows["Never existed or unavailable"]["downgrade_reasons"],
        )
        self.assertEqual(
            ["short_classification_fragment"],
            rows["All available actions"]["downgrade_reasons"],
        )
        for preview in (
            "Every Kubernetes service must conform.",
            "Read-only inspection; every database must use PostgreSQL.",
            "All services must conform",
            "Every database PostgreSQL only",
            "Always choose PostgreSQL",
            "Only deploy Kubernetes",
        ):
            self.assertEqual("untriaged", rows[preview]["governance_status"])

    def test_absolute_token_and_authority_rules_have_positive_and_negative_boundaries(self) -> None:
        for compound in (
            "load-all",
            "all-or-nothing",
            "catch-all",
            "always-on",
            "must-handle",
            "must-wait",
            "never-existed",
        ):
            with self.subTest(compound=compound):
                self.assertTrue(
                    self.module._absolute_literal_or_compound(
                        f"Treat {compound} as a lexical label."
                    )
                )
        self.assertTrue(
            self.module._absolute_literal_or_compound(
                "The literal `must` and all-or-nothing are labels."
            )
        )
        self.assertFalse(
            self.module._absolute_literal_or_compound(
                "The literal `must` applies, and all services deploy Kubernetes."
            )
        )
        self.assertFalse(
            self.module._absolute_literal_or_compound(
                "A must-deploy Kubernetes policy is required."
            )
        )
        documents = [
            {
                "path": "r1.md",
                "layer": "foundation",
                "owner": "r1",
                "kind": "targeted",
                "text": "# R1\n\n- Treat `must` and all-or-nothing as lexical labels.\n- A must-deploy Kubernetes policy applies to every cluster.\n",
            },
            {
                "path": "r3.md",
                "layer": "foundation",
                "owner": "r3",
                "kind": "targeted",
                "text": "# R3\n\n- A local test does not prove all deployments.\n- Integration evidence does not prove all deployments, every provider behavior, all consumers.\n- A local test does not prove all deployments, and cannot cover every consumer.\n- One validator can cover only the inspected route.\n- Proof limit: a local test does not prove all deployments.\n- A local test does not prove all deployments, every service runs.\n- A local test does not prove all deployments, every service uses a cache.\n- A local test does not prove all deployments, every service is healthy.\n- A local test does not prove all deployments, every service relies on a shared state.\n- A local test does not prove all deployments, every service must retry.\n- A local test does not prove all deployments, every service fails.\n- A local test does not prove all deployments, every worker executes commands.\n- A local test does not prove all deployments, every service tests consumers.\n- A local test does not prove all deployments, every service tests.\n- A local test does not prove all deployments, every service reports outcomes.\n- A local test does not prove all deployments; every service must use Kubernetes.\n- A local test does not prove all deployments, and every database runs on PostgreSQL.\n- A local test does not prove one route, but all databases rely exclusively on PostgreSQL.\n- A local test does not prove all deployments: every service runs on PostgreSQL.\n- A local test does not prove all deployments — every service runs on PostgreSQL.\n- A local test does not prove all deployments – every service runs on PostgreSQL.\n- A local test does not prove all deployments - every service runs on PostgreSQL.\n- A local test does not prove: all deployments.\n",
            },
            {
                "path": "r4.md",
                "layer": "foundation",
                "owner": "r4",
                "kind": "targeted",
                "text": "# R4\n\n- The review-agent may only read, search, and inspect current source.\n- Only the task profile may run it with explicit authority.\n- Owner is using task-agent only.\n- The review-agent may only read current source, and it must not edit files.\n- The review-agent may only read current source, and every database must use PostgreSQL.\n",
            },
            {
                "path": "r6-positive.md",
                "layer": "foundation",
                "owner": "r6-positive",
                "kind": "evidence-pattern",
                "text": "# R6\n\n- Map every final claim to fresh evidence or residual risk.\n",
            },
            {
                "path": "r6-negative.md",
                "layer": "foundation",
                "owner": "r6-negative",
                "kind": "benchmark-pattern",
                "text": "# R6 negative\n\n- Map every API to Kubernetes.\n",
            },
            {
                "path": "r6-checklist.md",
                "layer": "foundation",
                "owner": "r6-checklist",
                "kind": "decision-checklist",
                "text": "# R6 checklist\n\n- Map every manifest reference in scope.\n",
            },
            {
                "path": "r6-laundering.md",
                "layer": "foundation",
                "owner": "r6-laundering",
                "kind": "evidence-pattern",
                "text": "# R6 laundering\n\n- Map every accepted claim to a current command, source path, owner review, or explicit residual risk.\n- Map every API to Kubernetes and append evidence.\n- Map every API to PostgreSQL; record evidence.\n- Map every API to fresh evidence for all databases.\n- Map every API to evidence in Kubernetes.\n- Map every API to evidence or Kubernetes.\n- Map every API to evidence and PostgreSQL.\n- Map every API to evidence, owner review, and PostgreSQL.\n",
            },
        ]
        report = self.module._collect_reference_semantic_advisories(
            documents, disposition_entries=[]
        )
        rows = {
            item["preview"]: item
            for item in report["candidates"]
            if item["finding"] == "unconditional_absolute_candidate"
        }
        expected_reasons = {
            "Treat `must` and all-or-nothing as lexical labels.": "lexical_literal_or_compound",
            "A local test does not prove all deployments.": "clause_local_proof_limit",
            "A local test does not prove all deployments, and cannot cover every consumer.": "clause_local_proof_limit",
            "One validator can cover only the inspected route.": "clause_local_proof_limit",
            "Proof limit: a local test does not prove all deployments.": "clause_local_proof_limit",
            "The review-agent may only read, search, and inspect current source.": "explicit_profile_agent_authority",
            "Only the task profile may run it with explicit authority.": "explicit_profile_agent_authority",
            "Owner is using task-agent only.": "explicit_profile_agent_authority",
            "The review-agent may only read current source, and it must not edit files.": "explicit_profile_agent_authority",
            "Map every final claim to fresh evidence or residual risk.": "map_every_evidence_closure",
            "Map every manifest reference in scope.": "map_every_evidence_closure",
            "Map every accepted claim to a current command, source path, owner review, or explicit residual risk.": "map_every_evidence_closure",
        }
        for preview, reason in expected_reasons.items():
            self.assertEqual([reason], rows[preview]["downgrade_reasons"])
        for preview in (
            "A must-deploy Kubernetes policy applies to every cluster.",
            "Integration evidence does not prove all deployments, every provider behavior, all consumers.",
            "A local test does not prove all deployments, every service runs.",
            "A local test does not prove all deployments, every service uses a cache.",
            "A local test does not prove all deployments, every service is healthy.",
            "A local test does not prove all deployments, every service relies on a shared state.",
            "A local test does not prove all deployments, every service must retry.",
            "A local test does not prove all deployments, every service fails.",
            "A local test does not prove all deployments, every worker executes commands.",
            "A local test does not prove all deployments, every service tests consumers.",
            "A local test does not prove all deployments, every service tests.",
            "A local test does not prove all deployments, every service reports outcomes.",
            "A local test does not prove all deployments; every service must use Kubernetes.",
            "A local test does not prove all deployments, and every database runs on PostgreSQL.",
            "A local test does not prove one route, but all databases rely exclusively on PostgreSQL.",
            "A local test does not prove all deployments: every service runs on PostgreSQL.",
            "A local test does not prove all deployments — every service runs on PostgreSQL.",
            "A local test does not prove all deployments – every service runs on PostgreSQL.",
            "A local test does not prove all deployments - every service runs on PostgreSQL.",
            "A local test does not prove: all deployments.",
            "The review-agent may only read current source, and every database must use PostgreSQL.",
            "Map every API to Kubernetes.",
            "Map every API to Kubernetes and append evidence.",
            "Map every API to PostgreSQL; record evidence.",
            "Map every API to fresh evidence for all databases.",
            "Map every API to evidence in Kubernetes.",
            "Map every API to evidence or Kubernetes.",
            "Map every API to evidence and PostgreSQL.",
            "Map every API to evidence, owner review, and PostgreSQL.",
        ):
            self.assertEqual("untriaged", rows[preview]["governance_status"])

    def test_fixed_number_candidates_exclude_dates_versions_code_and_baselines(self) -> None:
        report = self.module._collect_reference_semantic_advisories(
            [
                {
                    "path": "src/foundation/example/references/numbers.md",
                    "layer": "foundation",
                    "owner": "example",
                    "text": """# Numbers

- Complete the rollback within 30 minutes.
- Require an external audit above $100K.
- Set the error-budget threshold to 1 percent.
- Review this decision on 2026-07-12.
- RFC 8594 and TLS 1.3 define protocol behavior.
- Use `timeout=30s` in this code sample.
- The candidate threshold is 10 percent.
- The baseline cost is $100.

## Example

- Retain the artifact for 90 days.

## Failure Patterns

- Treat $250K as a universal audit threshold.
""",
                }
            ]
        )
        rows = [
            item
            for item in report["candidates"]
            if item["finding"] == "fixed_number_candidate"
        ]
        self.assertEqual(3, len(rows))
        self.assertEqual(
            ["cost-slo-threshold", "money", "percent", "time"],
            sorted({signal for item in rows for signal in item["signals"]}),
        )
        previews = " ".join(item["preview"] for item in rows)
        for excluded in (
            "2026",
            "RFC",
            "TLS",
            "timeout=30s",
            "candidate",
            "baseline",
            "90 days",
            "$250K",
        ):
            self.assertNotIn(excluded, previews)

    def test_fixed_number_detects_maturity_options_org_windows_and_scores(self) -> None:
        positives = {
            "Require 3+ years of comparable production maturity.": "maturity-count",
            "Require 2+ maintainers before adoption.": "maturity-count",
            "Score 2-3 candidates against current constraints.": "option-count",
            "Fix this in the current sprint.": "organization-window",
            "Review the exception next quarter.": "organization-window",
            "OpenSSF Scorecard below 5/10 blocks adoption.": "score-threshold",
        }
        for sentence, expected in positives.items():
            with self.subTest(sentence=sentence):
                self.assertIn(expected, self.module._fixed_number_signals(sentence))

        for sentence in (
            "Python 3.12 and Java 21 are supported versions.",
            "CVSS 7.0-8.9 is the official HIGH severity band.",
            "RFC 8594 and TLS 1.3 define protocol behavior.",
            "Candidate version 2-3 remains a draft identifier.",
            "The benchmark scored 5/10 in this example.",
            "HTTP/2 response handling remains unchanged.",
        ):
            with self.subTest(negative=sentence):
                self.assertEqual([], self.module._fixed_number_signals(sentence))

    def test_fixed_number_requires_syntactic_value_association(self) -> None:
        report = self.module._collect_reference_semantic_advisories(
            [
                {
                    "path": "numbers.md",
                    "layer": "foundation",
                    "owner": "example",
                    "text": """# Numbers

- N+1 I/O and recomputation are cost decisions.
- Verify PID 1 behavior and graceful timeout escalation.
- Map HTTP/1.1, HTTP/2, 401, 403, 404, and 500 responses to timeout and SLA states.
- NIST SP 800-92 defines log retention controls; RFC 8594 applies to HTTP version 2.
- Review this decision on 2026-07-12.
- Set timeout to 30.
- Set the error threshold at 5.
- Complete rollback within 30 minutes.
- Require an audit above $100K.
- Keep the error budget below 1 percent.
""",
                }
            ]
        )
        rows = [
            item
            for item in report["candidates"]
            if item["finding"] == "fixed_number_candidate"
        ]
        previews = " ".join(item["preview"] for item in rows)
        for false_positive in (
            "N+1",
            "PID 1",
            "HTTP/1.1",
            "HTTP/2",
            "401",
            "NIST SP 800-92",
            "RFC 8594",
            "2026-07-12",
        ):
            self.assertNotIn(false_positive, previews)
        for true_positive in (
            "timeout to 30",
            "threshold at 5",
            "30 minutes",
            "$100K",
            "1 percent",
        ):
            self.assertIn(true_positive, previews)
        self.assertEqual(5, len(rows))

    def test_fixed_number_masks_only_inline_and_contextual_clauses(self) -> None:
        self.assertEqual(
            ["time"],
            self.module._fixed_number_signals(
                "Complete recovery within 30 minutes and run `cleanup`."
            ),
        )
        self.assertEqual(
            ["time"],
            self.module._fixed_number_signals(
                "The baseline is 10 ms but cleanup must finish within 30 minutes."
            ),
        )
        self.assertEqual(
            [],
            self.module._fixed_number_signals(
                "The benchmark baseline is 30 minutes."
            ),
        )
        self.assertEqual([], self.module._fixed_number_signals("Use Python 3.12."))
        self.assertIn(
            "percent",
            self.module._fixed_number_signals(
                "Candidate threshold 5, current SLO is 99.9 percent."
            ),
        )
        self.assertEqual(
            ["money"],
            self.module._fixed_number_signals(
                "Require an audit above $12,345.67."
            ),
        )
        self.assertEqual(
            [],
            self.module._fixed_number_signals(
                "Use Python 3.12, benchmark baseline is 30 minutes."
            ),
        )

    def test_semantic_paths_are_canonical_and_cannot_bypass_candidate_id(self) -> None:
        for path in (
            "",
            "../escape.md",
            "./dot.md",
            "a//b.md",
            "a\\b.md",
            "/abs.md",
            "C:/abs.md",
        ):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.module._semantic_candidate_id(
                    "fixed_number_candidate", path, "a" * 64
                )
            with self.subTest(document_path=path), self.assertRaises(ValueError):
                self.module._collect_reference_semantic_advisories(
                    [{
                        "path": path,
                        "layer": "foundation",
                        "owner": "owner",
                        "text": "# Rule\n\n- Complete recovery within 30 minutes.\n",
                    }],
                    disposition_entries=[],
                )

    def test_semantic_fingerprint_and_candidate_id_are_line_stable(self) -> None:
        documents = [
            {
                "path": path,
                "layer": "foundation",
                "owner": path[0],
                "text": "# Rule\n\n- Every external write must have an owner.\n",
            }
            for path in ("b/reference.md", "a/reference.md")
        ]
        first = self.module._collect_reference_semantic_advisories(documents)
        second = self.module._collect_reference_semantic_advisories(
            list(reversed(documents))
        )
        self.assertEqual(first, second)
        rows = first["candidates"]
        self.assertEqual(2, len(rows))
        self.assertEqual(1, len({item["fingerprint"] for item in rows}))
        self.assertTrue(all(len(item["fingerprint"]) == 64 for item in rows))
        self.assertTrue(all("canonical_occurrence" not in item for item in rows))
        self.assertTrue(all("lines" not in item for item in rows))
        shifted = [dict(documents[0], text="# Rule\n\n\n- Every external write must have an owner.\n")]
        before = next(
            item for item in first["candidates"] if item["path"] == "b/reference.md"
        )
        after = self.module._collect_reference_semantic_advisories(
            shifted, disposition_entries=[]
        )["candidates"][0]
        self.assertEqual(before["candidate_id"], after["candidate_id"])
        self.assertNotEqual(
            before["occurrences"][0]["lines"], after["occurrences"][0]["lines"]
        )

    def test_exact_normalized_duplicate_groups_owner_and_bullet_variants(self) -> None:
        documents = [
            {
                "path": "b/reference.md",
                "layer": "foundation",
                "owner": "beta-service",
                "kind": "targeted",
                "text": """# Beta

## Evidence Closure

* BETA SERVICE must inspect every current consumer, generated artifact, and release boundary before closure.
* Record the command, result, freshness, proof limitation, residual owner, and rollback implication.
* Reject closure when source evidence is stale, validation predates the final edit, or ownership is unknown.
""",
            },
            {
                "path": "a/reference.md",
                "layer": "foundation",
                "owner": "alpha-service",
                "kind": "targeted",
                "text": """# Alpha

## Evidence Closure

- Alpha Service must inspect every current consumer, generated artifact, and release boundary before closure.
- Record the command, result, freshness, proof limitation, residual owner, and rollback implication.
- Reject closure when source evidence is stale, validation predates the final edit, or ownership is unknown.
""",
            },
        ]
        first = self.module._collect_reference_semantic_advisories(documents)
        second = self.module._collect_reference_semantic_advisories(
            list(reversed(documents))
        )
        self.assertEqual(first, second)
        rows = [
            item
            for item in first["candidates"]
            if item["finding"] == "exact_normalized_duplicate_block"
        ]
        self.assertEqual(1, len(rows))
        self.assertEqual(2, rows[0]["occurrence_count"])
        self.assertEqual(2, rows[0]["distinct_path_count"])
        self.assertEqual("a/reference.md", rows[0]["occurrences"][0]["path"])
        self.assertEqual({"start": 5, "end": 7}, rows[0]["occurrences"][0]["lines"])
        self.assertGreaterEqual(rows[0]["tokens"], 36)

    def test_duplicate_detectors_exclude_examples_indexes_and_semantic_similarity(self) -> None:
        shared = """# Shared

## Evidence Closure

- Inspect every current consumer and generated artifact before closure.
- Record command, result, freshness, proof limits, residual owner, and rollback.
- Reject stale source evidence, pre-edit validation, and unknown ownership.
"""
        documents = [
            {
                "path": "index.md",
                "layer": "professional",
                "owner": "index-owner",
                "kind": "index",
                "text": shared,
            },
            {
                "path": "example.md",
                "layer": "foundation",
                "owner": "example-owner",
                "kind": "targeted",
                "text": shared.replace("## Evidence Closure", "## Example Evidence Closure"),
            },
            {
                "path": "matrix-a.md",
                "layer": "foundation",
                "owner": "matrix-a",
                "kind": "targeted",
                "text": """# A

## Evidence Matrix

| Claim | Evidence | What it proves |
| --- | --- | --- |
| Availability | Current SLO query | Current observed availability |
| Recovery | Restore rehearsal | Inspected restore path |
""",
            },
            {
                "path": "matrix-b.md",
                "layer": "foundation",
                "owner": "matrix-b",
                "kind": "targeted",
                "text": """# B

## Evidence Matrix

| Claim | Risk | Required action |
| --- | --- | --- |
| Availability | Missing window | Query current SLO |
| Recovery | Stale runbook | Rehearse restore |
""",
            },
        ]
        report = self.module._collect_reference_semantic_advisories(documents)
        duplicate_rows = [
            item
            for item in report["candidates"]
            if item["finding"]
            in {"exact_normalized_duplicate_block", "templated_block_candidate"}
        ]
        self.assertEqual([], duplicate_rows)

    def test_templated_yaml_and_tool_permission_shapes_are_grouped_not_exact(self) -> None:
        def document(path: str, owner: str, domain: str) -> dict:
            return {
                "path": path,
                "layer": "foundation",
                "owner": owner,
                "kind": "targeted",
                "text": f"""# {domain}

## Handoff Evidence Shape

```yaml
{owner.replace('-', '_')}_evidence_closure:
  inspected_{domain.lower()}_paths: []
  accepted_prior_claims: []
  rejected_or_stale_claims: []
  tool_permission_boundary:
    action_class: ""
    state_mutation: ""
    redaction: ""
  residual_{domain.lower()}_risk: []
  next_gate: ""
```

## Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Read | Inspect current {domain} source only |
| Validate | Record command and result |
| Mutate | Require bounded authority |
""",
            }

        documents = [
            document("b.md", "beta-service", "Beta"),
            document("a.md", "alpha-service", "Alpha"),
        ]
        report = self.module._collect_reference_semantic_advisories(documents)
        templated = [
            item
            for item in report["candidates"]
            if item["finding"] == "templated_block_candidate"
        ]
        self.assertEqual(2, len(templated))
        self.assertEqual(
            {"markdown-table-schema", "yaml-key-path-shape"},
            {item["signals"][0] for item in templated},
        )
        self.assertTrue(all(item["owner_count"] == 2 for item in templated))
        self.assertTrue(all(item["occurrences"][0]["path"] == "a.md" for item in templated))
        exact = [
            item
            for item in report["candidates"]
            if item["finding"] == "exact_normalized_duplicate_block"
        ]
        self.assertEqual([], exact)

    def test_semantic_dispositions_apply_all_four_states_and_reject_bad_entries(self) -> None:
        document = {
            "path": "src/foundation/example/references/rules.md",
            "layer": "foundation",
            "owner": "example",
            "kind": "targeted",
            "text": "# Rules\n\n- Every external write must retain a current owner and rollback record.\n",
        }
        evaluated_on = date(2026, 7, 12)
        base = self.module._collect_reference_semantic_advisories(
            [document], disposition_entries=[], evaluation_date=evaluated_on
        )
        candidate = base["candidates"][0]
        expected_states = {
            "rewrite": ("unresolved-rewrite", True, False),
            "valid-contextual-rule": ("resolved-valid-contextual-rule", False, True),
            "false-positive": ("resolved-false-positive", False, True),
            "time-bounded-exception": (
                "resolved-time-bounded-exception",
                False,
                True,
            ),
        }
        for disposition, expected in expected_states.items():
            entry = _semantic_disposition(candidate, disposition)
            report = self.module._collect_reference_semantic_advisories(
                [document],
                disposition_entries=[entry],
                evaluation_date=evaluated_on,
            )
            governed = report["candidates"][0]
            self.assertEqual(expected, (
                governed["governance_status"],
                governed["unresolved"],
                governed["resolved"],
            ))
            self.assertEqual(entry, governed["disposition_record"])
            self.assertEqual([], report["disposition_contract"]["errors"])

        base_entry = _semantic_disposition(candidate, "false-positive")
        bad_cases = (
            ([base_entry, base_entry], "duplicate semantic disposition"),
            ([{**base_entry, "candidate_id": "f" * 64}], "candidate_id does not match"),
            ([{**base_entry, "path": "renamed.md"}], "candidate_id does not match"),
            ([{**base_entry, "path": "../escape.md"}], "canonical relative POSIX path"),
            ([{**base_entry, "skill_owner": "wrong-owner"}], "skill_owner does not match"),
            ([{**base_entry, "reason": "approved"}], "reason is blank or generic"),
            ([{
                **_semantic_disposition(candidate, "time-bounded-exception"),
                "review_after": "2026-07-12",
            }], "strictly after"),
        )
        for entries, expected_error in bad_cases:
            invalid = self.module._collect_reference_semantic_advisories(
                [document],
                disposition_entries=entries,
                evaluation_date=evaluated_on,
            )
            self.assertTrue(
                any(expected_error in error for error in invalid["disposition_contract"]["errors"]),
                invalid["disposition_contract"]["errors"],
            )
            self.assertEqual(0, invalid["disposition_contract"]["applied_count"])

    def test_semantic_candidates_and_dispositions_use_canonical_order(self) -> None:
        documents = [
            {
                "path": path,
                "layer": "foundation",
                "owner": owner,
                "kind": "targeted",
                "text": text,
            }
            for path, owner, text in (
                (
                    "a.md",
                    "alpha",
                    "# Alpha\n\n- Every external write must retain a current owner.\n",
                ),
                (
                    "b.md",
                    "beta",
                    "# Beta\n\n- Every destructive operation must retain rollback evidence.\n",
                ),
            )
        ]
        evaluated_on = date(2026, 7, 12)
        base = self.module._collect_reference_semantic_advisories(
            documents, disposition_entries=[], evaluation_date=evaluated_on
        )
        self.assertEqual(
            base["candidates"],
            sorted(base["candidates"], key=self.module._semantic_candidate_sort_key),
        )
        candidates = [
            item for item in base["candidates"] if item["detector_status"] == "candidate"
        ]
        self.assertEqual(2, len(candidates))
        entries = sorted(
            [_semantic_disposition(item, "false-positive") for item in candidates],
            key=lambda item: item["candidate_id"],
            reverse=True,
        )
        invalid = self.module._collect_reference_semantic_advisories(
            documents,
            disposition_entries=entries,
            evaluation_date=evaluated_on,
        )
        self.assertTrue(
            any(
                "entries must be sorted by candidate_id" in error
                for error in invalid["disposition_contract"]["errors"]
            ),
            invalid["disposition_contract"]["errors"],
        )
        self.assertEqual(0, invalid["disposition_contract"]["applied_count"])

    def test_group_membership_and_content_fingerprints_are_independent(self) -> None:
        def occurrence(path: str, owner: str, start: int, body: str) -> dict:
            return {
            "fingerprint": "a" * 64,
            "content_fingerprint": self.module._semantic_occurrence_content_fingerprint(
                body
            ),
            "path": path,
            "layer": "foundation",
            "owner": owner,
            "lines": {"start": start, "end": start + 2},
            "tokens": 40,
            "preview": "shared decision block",
            }
        two = self.module._group_duplicate_occurrences(
            "templated_block_candidate",
            [
                occurrence("a.md", "alpha", 1, "alpha decision row"),
                occurrence("b.md", "beta", 1, "beta decision row"),
            ],
            require_distinct_owners=True,
        )[0]
        three = self.module._group_duplicate_occurrences(
            "templated_block_candidate",
            [
                occurrence("a.md", "alpha", 1, "alpha decision row"),
                occurrence("a.md", "alpha", 10, "alpha decision row"),
                occurrence("b.md", "beta", 1, "beta decision row"),
            ],
            require_distinct_owners=True,
        )[0]
        self.assertEqual(two["candidate_id"], three["candidate_id"])
        self.assertNotEqual(two["evidence_fingerprint"], three["evidence_fingerprint"])
        self.assertNotEqual(two["content_fingerprint"], three["content_fingerprint"])
        moved = self.module._group_duplicate_occurrences(
            "templated_block_candidate",
            [
                occurrence("a.md", "alpha", 20, "alpha decision row"),
                occurrence("b.md", "beta", 30, "beta decision row"),
            ],
            require_distinct_owners=True,
        )[0]
        self.assertEqual(two["evidence_fingerprint"], moved["evidence_fingerprint"])
        self.assertEqual(two["content_fingerprint"], moved["content_fingerprint"])
        changed = self.module._group_duplicate_occurrences(
            "templated_block_candidate",
            [
                occurrence("a.md", "alpha", 1, "generic shared decision row"),
                occurrence("b.md", "beta", 1, "generic shared decision row"),
            ],
            require_distinct_owners=True,
        )[0]
        self.assertEqual(two["candidate_id"], changed["candidate_id"])
        self.assertEqual(two["evidence_fingerprint"], changed["evidence_fingerprint"])
        self.assertNotEqual(two["content_fingerprint"], changed["content_fingerprint"])

    def test_templated_group_content_binds_rows_not_lines_or_headers(self) -> None:
        header = """| Surface | Inspect | Validation Evidence | Common False Proof |
| --- | --- | --- | --- |
"""

        def document(path: str, owner: str, first_row: str, *, padding: str = "") -> dict:
            return {
                "path": path,
                "layer": "foundation",
                "owner": owner,
                "kind": "targeted",
                "text": (
                    f"# {owner}\n\n{padding}## Evidence Map\n\n{header}"
                    f"| Primary surface | {first_row} | Owner-specific command | Generic approval |\n"
                    "| Secondary surface | Current source boundary | Targeted proof | Memory only |\n"
                ),
            }

        def group(documents: list[dict], entries: list[dict] | None = None) -> tuple[dict, dict]:
            report = self.module._collect_reference_semantic_advisories(
                documents,
                disposition_entries=[] if entries is None else entries,
                evaluation_date=date(2026, 7, 12),
            )
            candidate = next(
                item
                for item in report["candidates"]
                if item["finding"] == "templated_block_candidate"
            )
            return report, candidate

        long_prefix = "Observed decision evidence " + ("stable scope " * 30)
        base_documents = [
            document(
                "a.md",
                "alpha",
                long_prefix + "guide-specific proof limit",
            ),
            document("b.md", "beta", "Interpreter boundary and package contract"),
        ]
        _base_report, base = group(base_documents)
        _moved_report, moved = group(
            [
                document(
                    "a.md",
                    "alpha",
                    long_prefix + "guide-specific proof limit",
                    padding="\n\n",
                ),
                base_documents[1],
            ]
        )
        self.assertEqual(base["candidate_id"], moved["candidate_id"])
        self.assertEqual(base["evidence_fingerprint"], moved["evidence_fingerprint"])
        self.assertEqual(base["content_fingerprint"], moved["content_fingerprint"])

        generic_documents = [
            document(
                "a.md",
                "alpha",
                long_prefix + "generic converged proof limit",
            ),
            document("b.md", "beta", "Interpreter boundary and package contract"),
        ]
        _generic_report, generic = group(generic_documents)
        self.assertEqual(base["candidate_id"], generic["candidate_id"])
        self.assertEqual(base["evidence_fingerprint"], generic["evidence_fingerprint"])
        self.assertEqual(base["preview"], generic["preview"])
        self.assertNotEqual(base["content_fingerprint"], generic["content_fingerprint"])

        stale_entry = _semantic_disposition(base, "false-positive", priority="P2")
        stale_report, _stale_candidate = group(generic_documents, [stale_entry])
        self.assertEqual(0, stale_report["disposition_contract"]["applied_count"])
        self.assertTrue(
            any(
                "evidence.content_fingerprint does not match" in error
                for error in stale_report["disposition_contract"]["errors"]
            ),
            stale_report["disposition_contract"]["errors"],
        )

    def test_yaml_template_content_includes_sequences_and_block_bodies(self) -> None:
        def document(list_item: str, block_body: str) -> dict:
            return {
                "path": "yaml.md",
                "layer": "foundation",
                "owner": "yaml-owner",
                "kind": "targeted",
                "text": f"""# YAML

## Evidence Output

```yaml
result:
  status: accepted
  owner: team
  checks:
    - {list_item}
  evidence:
    source: current
    report: named
  notes: |
    {block_body}
```
""",
            }

        base = self.module._yaml_template_occurrences(
            document("alpha-only", "alpha decision detail")
        )[0]
        changed_sequence = self.module._yaml_template_occurrences(
            document("changed-list-item", "alpha decision detail")
        )[0]
        changed_block = self.module._yaml_template_occurrences(
            document("alpha-only", "changed block decision detail")
        )[0]
        self.assertEqual(base["fingerprint"], changed_sequence["fingerprint"])
        self.assertEqual(base["fingerprint"], changed_block["fingerprint"])
        self.assertNotEqual(
            base["content_fingerprint"], changed_sequence["content_fingerprint"]
        )
        self.assertNotEqual(
            base["content_fingerprint"], changed_block["content_fingerprint"]
        )


if __name__ == "__main__":
    unittest.main()
