from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate-reference-content.py"
_MISSING = object()


def _registry_declaration(field: str) -> tuple[int, str]:
    registry_field = "type" if field == "reference_type" else field
    lines = (ROOT / "src/registry/foundation-skills.yaml").read_text(
        encoding="utf-8"
    ).splitlines()
    for line_number, line in enumerate(lines, start=1):
        match = re.match(rf"^\s*{re.escape(registry_field)}:\s*(.+?)\s*$", line)
        if match is None:
            continue
        raw = match.group(1).strip()
        parsed = json.loads(raw) if raw.startswith(("\"", "[")) else raw
        value = (
            json.dumps(parsed, ensure_ascii=True, separators=(",", ":"))
            if isinstance(parsed, list)
            else parsed
        )
        if field == "reference_type" and value != "targeted":
            continue
        return line_number, value
    raise AssertionError(f"missing Registry declaration for {registry_field}")


def _effective_preface(
    *,
    reference_type="missing",
    load_when="missing",
    do_not_load_when="missing",
    required_by="resolved",
    required_output="resolved",
    source="reference-index",
) -> dict:
    fields = {}
    for field, status in (
        ("reference_type", reference_type),
        ("load_when", load_when),
        ("do_not_load_when", do_not_load_when),
        ("required_by", required_by),
        ("required_output", required_output),
    ):
        resolved = status == "resolved"
        line, value = _registry_declaration(field)
        fields[field] = {
            "status": status,
            "value": value if resolved else None,
            "source": source if resolved else None,
            "evidence": (
                [
                    {
                        "source": source,
                        "path": "src/registry/foundation-skills.yaml",
                        "line": line,
                        "value": value,
                        "accepted": True,
                    }
                ]
                if resolved
                else []
            ),
        }
    return {**fields, "conflicts": []}


def _load_module():
    spec = importlib.util.spec_from_file_location("validate_reference_content_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _semantic(candidates=None) -> dict:
    candidates = list(candidates or [])
    families = (
        "unconditional_absolute_candidate",
        "fixed_number_candidate",
        "exact_normalized_duplicate_block",
        "templated_block_candidate",
    )
    by_finding = {}
    for finding in families:
        rows = [item for item in candidates if item["finding"] == finding]
        by_finding[finding] = {
            "raw": len(rows),
            "detector_downgraded": sum(
                item["governance_status"] == "detector-downgraded" for item in rows
            ),
            "untriaged": sum(item["governance_status"] == "untriaged" for item in rows),
            "rewrite": sum(item.get("disposition") == "rewrite" for item in rows),
            "valid_contextual_rule": sum(
                item.get("disposition") == "valid-contextual-rule" for item in rows
            ),
            "false_positive": sum(
                item.get("disposition") == "false-positive" for item in rows
            ),
            "time_bounded_exception": sum(
                item.get("disposition") == "time-bounded-exception" for item in rows
            ),
            "unresolved": sum(bool(item["unresolved"]) for item in rows),
            "resolved": sum(bool(item["resolved"]) for item in rows),
            "p0_unresolved": sum(item["unresolved"] and item["priority"] == "P0" for item in rows),
            "p1_unresolved": sum(item["unresolved"] and item["priority"] == "P1" for item in rows),
            "p2_unresolved": sum(item["unresolved"] and item["priority"] == "P2" for item in rows),
        }
    totals = {
        field: sum(by_finding[finding][field] for finding in families)
        for field in next(iter(by_finding.values()))
    }
    entries = [item["disposition_record"] for item in candidates if item.get("disposition_record")]
    return {
        "schema_version": 5,
        "finding_families": list(families),
        "summary": {
            "raw_candidates": totals["raw"],
            "detector_downgraded_candidates": totals["detector_downgraded"],
            "untriaged_candidates": totals["untriaged"],
            "rewrite_candidates": totals["rewrite"],
            "valid_contextual_rule_candidates": totals["valid_contextual_rule"],
            "false_positive_candidates": totals["false_positive"],
            "time_bounded_exception_candidates": totals["time_bounded_exception"],
            "unresolved_candidates": totals["unresolved"],
            "resolved_candidates": totals["resolved"],
            "p0_unresolved_candidates": totals["p0_unresolved"],
            "p1_unresolved_candidates": totals["p1_unresolved"],
            "p2_unresolved_candidates": totals["p2_unresolved"],
            "by_finding": by_finding,
            "group_metrics": {
                finding: {
                    "groups": len(
                        [item for item in candidates if item["finding"] == finding]
                    ),
                    "occurrences": sum(
                        item.get("occurrence_count", 0)
                        for item in candidates
                        if item["finding"] == finding
                    ),
                    "tokens": sum(
                        item.get("total_tokens", 0)
                        for item in candidates
                        if item["finding"] == finding
                    ),
                }
                for finding in (
                    "exact_normalized_duplicate_block",
                    "templated_block_candidate",
                )
            },
            "strict_unresolved": {
                "fixed_number_candidates": by_finding["fixed_number_candidate"]["unresolved"],
                "templated_block_groups": by_finding["templated_block_candidate"]["unresolved"],
                "unconditional_absolute_p0_p1_candidates": (
                    by_finding["unconditional_absolute_candidate"]["p0_unresolved"]
                    + by_finding["unconditional_absolute_candidate"]["p1_unresolved"]
                ),
                "p2_rewrite_advisories": sum(
                    item.get("disposition") == "rewrite"
                    and item.get("priority") == "P2"
                    and item["finding"]
                    not in {"fixed_number_candidate", "exact_normalized_duplicate_block", "templated_block_candidate"}
                    for item in candidates
                ),
            },
        },
        "candidates": candidates,
        "disposition_contract": {
            "schema_version": 2,
            "source": "config/skill-content-exceptions.yaml",
            "evaluated_on": "2026-07-12",
            "configured_count": len(entries),
            "applied_count": len(entries),
            "entries": entries,
            "errors": [],
            "common_errors": [],
            "surface_errors": {
                "control": [],
                "professional": [],
                "foundation": [],
                "domain": [],
            },
            "group_scope": "Group candidate IDs use the literal scope 'group'.",
        },
        "limitations": ["Synthetic semantic contract fixture."],
    }


def _disposition(candidate: dict, value: str, *, priority: str = "P1") -> dict:
    return {
        "candidate_id": candidate["candidate_id"],
        "finding": candidate["finding"],
        "path": candidate["path"],
        "fingerprint": candidate["fingerprint"],
        "skill_owner": candidate["skill_owner"],
        "priority": priority,
        "disposition": value,
        "reason": "Current source evidence supports this explicit governance decision.",
        "authority_or_condition": "Repository governance policy owns the declared condition.",
        "decision_owner": "Repository governance owner",
        "evidence": {
            "fingerprint": candidate["evidence_fingerprint"],
            "content_fingerprint": candidate["content_fingerprint"],
            "rationale": "Current candidate identity and source membership were inspected.",
        },
        "mitigation": "Re-evaluate the rule when its source contract or membership changes.",
        "review_after": "2026-08-01" if value == "time-bounded-exception" else None,
    }


def _content(
    *, references=None, missing=None, orphans=None, templates=None, advisories=None,
    semantic_advisories=_MISSING,
):
    references = copy.deepcopy(list(references or []))
    for item in references:
        item.setdefault("layer", "foundation")
        item.setdefault("owner", "owner")
        item.setdefault("effective_preface", _effective_preface())
        for field in ("required_by", "required_output"):
            value = item["effective_preface"][field]
            if value["status"] != "resolved":
                continue
            value["source"] = "local"
            for evidence in value["evidence"]:
                evidence["source"] = "local"
                evidence["path"] = item["path"]
    effective_reference_types = sum(
        item.get("exists")
        and item["effective_preface"]["reference_type"]["status"] == "resolved"
        for item in references
    )
    effective_load_when = sum(
        item.get("exists")
        and item["effective_preface"]["load_when"]["status"] == "resolved"
        for item in references
    )
    effective_do_not_load_when = sum(
        item.get("exists")
        and item["effective_preface"]["do_not_load_when"]["status"] == "resolved"
        for item in references
    )
    effective_required_by = sum(
        item.get("exists")
        and item["effective_preface"]["required_by"]["status"] == "resolved"
        for item in references
    )
    effective_required_output = sum(
        item.get("exists")
        and item["effective_preface"]["required_output"]["status"] == "resolved"
        for item in references
    )
    existing_references = [item for item in references if item.get("exists")]
    missing_effective_reference_types = sum(
        item["effective_preface"]["reference_type"]["status"] == "missing"
        for item in existing_references
    )
    missing_effective_load_when = sum(
        item["effective_preface"]["load_when"]["status"] == "missing"
        for item in existing_references
    )
    missing_effective_do_not_load_when = sum(
        item["effective_preface"]["do_not_load_when"]["status"] == "missing"
        for item in existing_references
    )
    missing_effective_required_by = sum(
        item["effective_preface"]["required_by"]["status"] == "missing"
        for item in existing_references
    )
    missing_effective_required_output = sum(
        item["effective_preface"]["required_output"]["status"] == "missing"
        for item in existing_references
    )
    effective_preface_invalid = sum(
        item["effective_preface"][field]["status"] == "invalid"
        for item in existing_references
        for field in (
            "reference_type",
            "load_when",
            "do_not_load_when",
            "required_by",
            "required_output",
        )
    )
    conflicts = [
        {"layer": item["layer"], "owner": item["owner"], "path": item["path"], **conflict}
        for item in references
        for conflict in item["effective_preface"].get("conflicts", [])
    ]
    content = {
        "schema_version": 4,
        "preface_contract": {
            "schema_version": 3,
            "source_precedence": ["local", "reference-index", "parent-root"],
            "fields": [
                "reference_type",
                "load_when",
                "do_not_load_when",
                "required_by",
                "required_output",
            ],
            "source_fingerprint": {
                "algorithm": "sha256",
                "value": "a" * 64,
                "document_count": 1,
            },
            "errors": [],
            "conflicts": conflicts,
        },
        "summary": {
            "physical_markdown_references": len(references),
            "effective_reference_types": effective_reference_types,
            "missing_effective_reference_types": missing_effective_reference_types,
            "effective_load_when": effective_load_when,
            "missing_effective_load_when": missing_effective_load_when,
            "effective_do_not_load_when": effective_do_not_load_when,
            "missing_effective_do_not_load_when": missing_effective_do_not_load_when,
            "effective_required_by": effective_required_by,
            "missing_effective_required_by": missing_effective_required_by,
            "effective_required_output": effective_required_output,
            "missing_effective_required_output": missing_effective_required_output,
            "effective_preface_conflicts": len(conflicts),
            "effective_preface_contract_errors": 0,
            "effective_preface_invalid": effective_preface_invalid,
        },
        "references": references,
        "missing": list(missing or []),
        "orphans": list(orphans or []),
        "template_assets": list(templates or []),
        "advisories": {
            "non_template_multiple_h1": [],
            "non_template_empty_headings": [],
            "non_template_invalid_decision_section_headings": [],
            "targeted_over_60_lines": [],
            "mode_contract_over_80_lines": [],
            "decision_items_over_15": [],
            **dict(advisories or {}),
        },
        "semantic_advisories": (
            _semantic() if semantic_advisories is _MISSING else semantic_advisories
        ),
    }
    auditor = _load_module()._load_auditor()
    content["surface_validation"] = auditor._reference_surface_validation(content)
    return content


class ValidateReferenceContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_default_allows_reported_template_exceptions(self) -> None:
        content = _content(
            references=[
                {
                    "path": "src/control/references/template.md",
                    "exists": True,
                    "kind": "template",
                    "h1_status": "multiple",
                    "has_reference_type_preface": False,
                    "has_load_when_preface": False,
                    "has_do_not_load_when_preface": False,
                }
            ],
            templates=[
                {"path": "src/control/references/template.md", "indexed": True},
                {"path": "src/foundation/_template/references/checklist.md", "indexed": False},
            ],
        )
        counts, errors = self.module._evaluate(content, strict=False)
        self.assertEqual([], errors)
        self.assertEqual(1, counts["template_multiple_h1"])
        self.assertEqual(1, counts["unindexed_template_assets"])

    def test_default_hard_failures_have_stable_order(self) -> None:
        content = _content(
            references=[
                {
                    "path": "missing-h1.md",
                    "exists": True,
                    "kind": "targeted",
                    "h1_status": "missing",
                    "has_reference_type_preface": True,
                    "has_load_when_preface": True,
                    "has_do_not_load_when_preface": True,
                }
            ],
            missing=[{"path": "missing.md"}],
            orphans=[{"path": "orphan.md"}],
            advisories={
                "non_template_multiple_h1": [{"path": "multiple.md"}],
                "non_template_empty_headings": [{"path": "empty.md"}],
                "non_template_invalid_decision_section_headings": [
                    {"path": "generic.md"}
                ],
            },
        )
        _counts, errors = self.module._evaluate(content, strict=False)
        self.assertEqual(
            [
                "missing indexed reference(s): 1",
                "non-template orphan reference(s): 1",
                "indexed reference(s) missing H1: 1",
                "non-template reference(s) with multiple H1: 1",
                "non-template reference(s) with empty heading: 1",
                "non-template reference(s) with invalid decision-section heading: 1",
            ],
            errors,
        )

    def test_strict_promotes_advisories_without_weakening_thresholds(self) -> None:
        self.assertEqual(60, self.module.TARGETED_LINE_LIMIT)
        self.assertEqual(80, self.module.MODE_CONTRACT_LINE_LIMIT)
        self.assertEqual(15, self.module.DECISION_ITEM_LIMIT)
        content = _content(
            references=[
                {
                    "path": "targeted.md",
                    "exists": True,
                    "kind": "targeted",
                    "h1_status": "exactly-one",
                    "has_reference_type_preface": False,
                    "has_load_when_preface": False,
                    "has_do_not_load_when_preface": False,
                }
            ],
            advisories={
                "targeted_over_60_lines": [{"path": "targeted.md", "line_count": 61}],
                "mode_contract_over_80_lines": [{"path": "mode.md", "line_count": 81}],
                "decision_items_over_15": [{"path": "decisions.md", "decision_item_count": 16}],
            },
        )
        _default_counts, default_errors = self.module._evaluate(content, strict=False)
        counts, strict_errors = self.module._evaluate(content, strict=True)
        self.assertEqual([], default_errors)
        self.assertEqual(1, counts["missing_reference_type"])
        self.assertEqual(
            [
                "indexed reference(s) missing effective reference type: 1",
                "indexed reference(s) missing effective load condition: 1",
                "indexed reference(s) missing effective do-not-load condition: 1",
                "targeted reference(s) over 60 lines: 1",
                "mode-contract reference(s) over 80 lines: 1",
                "reference(s) with a Gate/Checklist/Decision section over 15 items: 1",
            ],
            strict_errors,
        )

    def test_strict_uses_effective_preface_without_redefining_local_counts(self) -> None:
        fresh = self.module._fresh_reference_content()
        reference = copy.deepcopy(
            next(
                item
                for item in fresh["references"]
                if item["owner"] == "cache-design"
                and item["path"].endswith("/references/checklist.md")
            )
        )
        content = _content(references=[reference])
        counts, errors = self.module._evaluate(content, strict=True)
        self.assertEqual([], errors)
        self.assertEqual(1, counts["missing_reference_type"])
        self.assertEqual(0, counts["missing_effective_reference_type"])

    def test_registry_provenance_rejects_same_value_from_another_entry(self) -> None:
        content = self.module._fresh_reference_content()
        item = next(
            row
            for row in content["references"]
            if row["owner"] == "engineering-control-plane"
            and row["path"].endswith("/references/direct-task-template.md")
        )
        evidence = item["effective_preface"]["reference_type"]["evidence"][0]
        registry_lines = (ROOT / evidence["path"]).read_text(
            encoding="utf-8"
        ).splitlines()
        replacement_line = next(
            line_number
            for line_number, line in enumerate(registry_lines, start=1)
            if line.strip() == "type: template" and line_number != evidence["line"]
        )
        evidence["line"] = replacement_line

        _counts, errors = self.module._effective_preface_contract(content)
        self.assertTrue(
            any(
                "canonical Registry owner/path/field declaration" in error
                for error in errors
            ),
            errors,
        )

    def test_effective_preface_schema_and_contract_errors_fail_by_default(self) -> None:
        content = _content()
        content["preface_contract"]["schema_version"] = 0
        content["preface_contract"]["errors"] = [
            {
                "code": "duplicate-index-row",
                "source": "reference-index",
                "path": "src/skills/owner/references/index.md",
                "line": 7,
                "message": "duplicate",
            }
        ]
        content["summary"]["effective_preface_contract_errors"] = 1
        counts, errors = self.module._evaluate(content, strict=False)
        self.assertEqual(1, counts["effective_preface_contract_errors"])
        self.assertTrue(any("schema_version must equal 3" in item for item in errors))
        self.assertIn("effective preface contract error(s): 1", errors)

    def test_effective_preface_conflict_is_a_default_hard_failure(self) -> None:
        local = {
            "source": "local",
            "path": "src/skills/owner/references/targeted.md",
            "line": 2,
            "value": "targeted",
            "accepted": True,
        }
        indexed = {
            "source": "reference-index",
            "path": "src/registry/foundation-skills.yaml",
            "line": 7,
            "value": "mode-contract",
            "accepted": True,
        }
        conflict = {
            "field": "reference_type",
            "code": "inconsistent-source-evidence",
            "message": "type conflict",
            "evidence": [local, indexed],
        }
        effective = _effective_preface()
        effective["reference_type"] = {
            "status": "conflict",
            "value": None,
            "source": None,
            "evidence": [local, indexed],
        }
        effective["conflicts"] = [conflict]
        content = _content(
            references=[
                {
                    "path": "src/skills/owner/references/targeted.md",
                    "exists": True,
                    "kind": "targeted",
                    "h1_status": "exactly-one",
                    "has_reference_type_preface": True,
                    "has_load_when_preface": False,
                    "has_do_not_load_when_preface": False,
                    "effective_preface": effective,
                }
            ]
        )
        counts, errors = self.module._evaluate(content, strict=False)
        self.assertEqual(1, counts["effective_preface_conflicts"])
        self.assertIn("effective preface conflict(s): 1", errors)

    def test_canonical_recompute_rejects_forged_selected_value(self) -> None:
        target = "src/skills/owner/references/targeted.md"
        effective = _effective_preface(
            reference_type="resolved",
            load_when="resolved",
            do_not_load_when="resolved",
            source="local",
        )
        for field in ("reference_type", "load_when", "do_not_load_when"):
            effective[field]["evidence"][0]["path"] = target
        effective["reference_type"]["value"] = "mode-contract"
        content = _content(
            references=[
                {
                    "path": target,
                    "exists": True,
                    "kind": "targeted",
                    "h1_status": "exactly-one",
                    "has_reference_type_preface": True,
                    "has_load_when_preface": True,
                    "has_do_not_load_when_preface": True,
                    "effective_preface": effective,
                }
            ]
        )
        _counts, errors = self.module._evaluate(content, strict=False)
        self.assertTrue(
            any("does not match canonical evidence resolution" in item for item in errors),
            errors,
        )

    def test_canonical_recompute_rejects_hidden_duplicate_and_generic_acceptance(self) -> None:
        target = "src/skills/owner/references/targeted.md"
        effective = _effective_preface(
            reference_type="resolved",
            load_when="resolved",
            source="local",
        )
        for field in ("reference_type", "load_when"):
            effective[field]["evidence"][0]["path"] = target
        effective["reference_type"]["evidence"].append(
            {
                "source": "local",
                "path": target,
                "line": 8,
                "value": "mode-contract",
                "accepted": True,
            }
        )
        effective["load_when"] = {
            "status": "resolved",
            "value": "when needed",
            "source": "local",
            "evidence": [
                {
                    "source": "local",
                    "path": target,
                    "line": 9,
                    "value": "when needed",
                    "accepted": True,
                }
            ],
        }
        content = _content(
            references=[
                {
                    "path": target,
                    "exists": True,
                    "kind": "targeted",
                    "h1_status": "exactly-one",
                    "has_reference_type_preface": True,
                    "has_load_when_preface": True,
                    "has_do_not_load_when_preface": False,
                    "effective_preface": effective,
                }
            ]
        )
        _counts, errors = self.module._evaluate(content, strict=False)
        self.assertTrue(any("canonical declaration" in item for item in errors), errors)
        self.assertTrue(
            any("canonical evidence resolution" in item for item in errors), errors
        )
        self.assertTrue(
            any("does not match per-reference conflicts" in item for item in errors),
            errors,
        )

    def test_canonical_recompute_rejects_source_specific_path_claim(self) -> None:
        target = "src/skills/owner/references/targeted.md"
        effective = _effective_preface(reference_type="resolved", source="local")
        effective["reference_type"]["evidence"][0]["path"] = (
            "src/skills/owner/references/index.md"
        )
        content = _content(
            references=[
                {
                    "path": target,
                    "exists": True,
                    "kind": "targeted",
                    "h1_status": "exactly-one",
                    "has_reference_type_preface": True,
                    "has_load_when_preface": False,
                    "has_do_not_load_when_preface": False,
                    "effective_preface": effective,
                }
            ]
        )
        _counts, errors = self.module._evaluate(content, strict=False)
        self.assertTrue(
            any("does not match the canonical local document" in item for item in errors),
            errors,
        )

    def test_source_fingerprint_shape_is_fail_closed(self) -> None:
        content = _content()
        content["preface_contract"]["source_fingerprint"]["value"] = "not-a-hash"
        _counts, errors = self.module._evaluate(content, strict=False)
        self.assertTrue(any("must be a lowercase SHA-256" in item for item in errors), errors)

    def test_count_output_is_deterministic(self) -> None:
        content = _content()
        first_counts, _errors = self.module._evaluate(content, strict=True)
        second_counts = dict(reversed(list(first_counts.items())))
        self.assertEqual(
            self.module._format_counts(first_counts, strict=True),
            self.module._format_counts(second_counts, strict=True),
        )

    def test_semantic_unresolved_candidates_are_default_advisories_and_strict_gates(self) -> None:
        auditor = self.module._load_auditor()
        documents = [
            {
                "path": "rule.md",
                "layer": "foundation",
                "owner": "rule-owner",
                "kind": "targeted",
                "text": "# Rule\n\n- Every external mutation must retain an owner.\n- Complete recovery within 30 minutes.\n",
            },
        ] + [
            {
                "path": path,
                "layer": "foundation",
                "owner": owner,
                "kind": "targeted",
                "text": "# Evidence\n\n## Tool Permission Boundary\n\n| Action | Boundary record |\n| --- | --- |\n| Read | Inspect current source |\n| Validate | Record command and result |\n| Mutate | Require bounded authority |\n",
            }
            for path, owner in (("a.md", "alpha"), ("b.md", "beta"))
        ]
        semantic = auditor._collect_reference_semantic_advisories(
            documents, disposition_entries=[], evaluation_date=date(2026, 7, 12)
        )
        content = _content(semantic_advisories=semantic)
        counts, default_errors = self.module._evaluate(content, strict=False)
        _strict_counts, strict_errors = self.module._evaluate(content, strict=True)
        self.assertEqual([], default_errors)
        self.assertTrue(any("unresolved fixed-number" in item for item in strict_errors))
        self.assertTrue(any("unresolved templated-block" in item for item in strict_errors))
        self.assertTrue(any("unresolved P0/P1 unconditional" in item for item in strict_errors))
        self.assertGreaterEqual(counts["semantic_unresolved_candidates"], 3)
        self.assertEqual(1, counts["fixed_number_unresolved_candidates"])
        self.assertIn(
            "semantic-governance raw=",
            "\n".join(self.module._format_counts(counts, strict=True)),
        )

    def test_semantic_schema_is_a_default_hard_failure(self) -> None:
        for malformed, expected in (
            (None, "semantic_advisories must be a current mapping"),
            ({}, "schema_version must equal 5"),
            (
                {**_semantic(), "finding_families": ["fixed_number_candidate"]},
                "finding_families must exactly match",
            ),
        ):
            content = _content(semantic_advisories=malformed)
            _counts, errors = self.module._evaluate(content, strict=False)
            self.assertTrue(any(expected in error for error in errors), errors)

    def test_semantic_v5_rejects_every_legacy_or_unknown_field(self) -> None:
        auditor = self.module._load_auditor()
        document = {
            "path": "rule.md",
            "layer": "foundation",
            "owner": "rule-owner",
            "kind": "targeted",
            "text": "# Rule\n\n- Every external mutation must retain an owner.\n",
        }
        base = auditor._collect_reference_semantic_advisories(
            [document], disposition_entries=[], evaluation_date=date(2026, 7, 12)
        )
        mutations = (
            lambda report: report.__setitem__("exception_contract", {}),
            lambda report: report["summary"].__setitem__("actionable_candidates", 1),
            lambda report: report["candidates"][0].__setitem__("legacy_field", True),
            lambda report: report["candidates"][0]["occurrences"][0].__setitem__(
                "legacy_field", True
            ),
            lambda report: report["disposition_contract"].__setitem__(
                "legacy_field", True
            ),
        )
        for mutate in mutations:
            malformed = copy.deepcopy(base)
            mutate(malformed)
            _counts, errors = self.module._evaluate(
                _content(semantic_advisories=malformed), strict=False
            )
            self.assertTrue(any("exactly" in item for item in errors), errors)

        entry = _disposition(base["candidates"][0], "false-positive")
        governed = auditor._collect_reference_semantic_advisories(
            [document], disposition_entries=[entry], evaluation_date=date(2026, 7, 12)
        )
        governed["disposition_contract"]["entries"][0]["owner"] = "legacy-owner"
        _counts, errors = self.module._evaluate(
            _content(semantic_advisories=governed), strict=False
        )
        self.assertTrue(any("unknown field" in item for item in errors), errors)

    def test_semantic_v5_rejects_noncanonical_paths_after_id_recomputation(self) -> None:
        auditor = self.module._load_auditor()
        semantic = auditor._collect_reference_semantic_advisories(
            [{
                "path": "rule.md",
                "layer": "foundation",
                "owner": "rule-owner",
                "kind": "targeted",
                "text": "# Rule\n\n- Complete recovery within 30 minutes.\n",
            }],
            disposition_entries=[],
            evaluation_date=date(2026, 7, 12),
        )
        for path in ("../escape.md", "./dot.md", "a\\b.md", "/abs.md", "C:/abs.md"):
            malformed = copy.deepcopy(semantic)
            candidate = malformed["candidates"][0]
            candidate["path"] = path
            candidate["scope"] = path
            candidate["occurrences"][0]["path"] = path
            payload = (
                "reference-semantic-candidate-v1\0"
                + candidate["finding"]
                + "\0"
                + path
                + "\0"
                + candidate["fingerprint"]
            )
            candidate["candidate_id"] = hashlib.sha256(payload.encode()).hexdigest()
            _counts, errors = self.module._evaluate(
                _content(semantic_advisories=malformed), strict=False
            )
            self.assertTrue(
                any("canonical relative POSIX path" in item for item in errors),
                errors,
            )

    def test_semantic_v5_rejects_unknown_absolute_downgrade_reason(self) -> None:
        auditor = self.module._load_auditor()
        semantic = auditor._collect_reference_semantic_advisories(
            [{
                "path": "conditional.md",
                "layer": "foundation",
                "owner": "conditional-owner",
                "kind": "targeted",
                "text": "# Rule\n\n- If compatibility is proven, all callers retain the bridge.\n",
            }],
            disposition_entries=[],
            evaluation_date=date(2026, 7, 12),
        )
        candidate = semantic["candidates"][0]
        candidate["occurrences"][0]["downgrade_reason"] = "unknown_reason"
        candidate["downgrade_reasons"] = ["unknown_reason"]
        _counts, errors = self.module._evaluate(
            _content(semantic_advisories=semantic), strict=False
        )
        self.assertTrue(any("downgrade_reason is not declared" in item for item in errors))

    def test_semantic_count_arithmetic_and_candidates_must_match(self) -> None:
        auditor = self.module._load_auditor()
        semantic = auditor._collect_reference_semantic_advisories(
            [{
                "path": "number.md",
                "layer": "foundation",
                "owner": "number-owner",
                "kind": "targeted",
                "text": "# Number\n\n- Complete recovery within 30 minutes.\n",
            }],
            disposition_entries=[],
            evaluation_date=date(2026, 7, 12),
        )
        semantic["summary"]["raw_candidates"] = 2
        content = _content(semantic_advisories=semantic)
        _counts, errors = self.module._evaluate(content, strict=False)
        self.assertIn(
            "semantic_advisories.summary.raw_candidates does not match candidates",
            errors,
        )

    def test_semantic_v5_rejects_reverse_candidate_and_disposition_order(self) -> None:
        auditor = self.module._load_auditor()
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
        base = auditor._collect_reference_semantic_advisories(
            documents, disposition_entries=[], evaluation_date=evaluated_on
        )
        reversed_candidates = copy.deepcopy(base)
        reversed_candidates["candidates"].reverse()
        _counts, candidate_errors = self.module._evaluate(
            _content(semantic_advisories=reversed_candidates), strict=False
        )
        self.assertIn(
            "semantic_advisories.candidates must be canonically sorted",
            candidate_errors,
        )

        entries = sorted(
            [_disposition(item, "false-positive") for item in base["candidates"]],
            key=lambda item: item["candidate_id"],
        )
        governed = auditor._collect_reference_semantic_advisories(
            documents, disposition_entries=entries, evaluation_date=evaluated_on
        )
        governed["disposition_contract"]["entries"].reverse()
        _counts, disposition_errors = self.module._evaluate(
            _content(semantic_advisories=governed),
            strict=False,
            evaluation_date=evaluated_on,
        )
        self.assertTrue(
            any(
                "entries must be sorted by candidate_id" in error
                for error in disposition_errors
            ),
            disposition_errors,
        )

    def test_semantic_v5_rejects_bool_for_every_count_and_index_field(self) -> None:
        def assert_rejected(report: dict, mutate, expected: str) -> None:
            malformed = copy.deepcopy(report)
            mutate(malformed)
            _counts, errors = self.module._evaluate(
                _content(semantic_advisories=malformed), strict=False
            )
            self.assertTrue(any(expected in error for error in errors), errors)

        empty = _semantic()
        top_count_fields = sorted(
            set(empty["summary"])
            - {"by_finding", "group_metrics", "strict_unresolved"}
        )
        for field in top_count_fields:
            with self.subTest(surface="summary", field=field):
                assert_rejected(
                    empty,
                    lambda report, field=field: report["summary"].__setitem__(
                        field, False
                    ),
                    f"summary.{field} must be a non-negative integer",
                )
        for finding, row in empty["summary"]["by_finding"].items():
            for field in row:
                with self.subTest(surface="by_finding", finding=finding, field=field):
                    assert_rejected(
                        empty,
                        lambda report, finding=finding, field=field: report["summary"]
                        ["by_finding"][finding].__setitem__(field, False),
                        f"by_finding.{finding}.{field} must be a non-negative integer",
                    )
        for finding, row in empty["summary"]["group_metrics"].items():
            for field in row:
                with self.subTest(surface="group_metrics", finding=finding, field=field):
                    assert_rejected(
                        empty,
                        lambda report, finding=finding, field=field: report["summary"]
                        ["group_metrics"][finding].__setitem__(field, False),
                        f"group_metrics.{finding}.{field} must be a non-negative integer",
                    )
        for field in empty["summary"]["strict_unresolved"]:
            with self.subTest(surface="strict_unresolved", field=field):
                assert_rejected(
                    empty,
                    lambda report, field=field: report["summary"]
                    ["strict_unresolved"].__setitem__(field, False),
                    f"strict_unresolved.{field} must be a non-negative integer",
                )
        for field in ("configured_count", "applied_count"):
            with self.subTest(surface="disposition_contract", field=field):
                assert_rejected(
                    empty,
                    lambda report, field=field: report["disposition_contract"].__setitem__(
                        field, False
                    ),
                    f"disposition_contract.{field} must be a non-negative integer",
                )

        auditor = self.module._load_auditor()
        documents = [
            {
                "path": "rule.md",
                "layer": "foundation",
                "owner": "rule-owner",
                "kind": "targeted",
                "text": "# Rule\n\n- Every external mutation must retain an owner.\n",
            },
            *[
                {
                    "path": path,
                    "layer": "foundation",
                    "owner": owner,
                    "kind": "targeted",
                    "text": "# Evidence\n\n## Tool Permission Boundary\n\n| Action | Boundary record |\n| --- | --- |\n| Read | Inspect current source |\n| Validate | Record command and result |\n| Mutate | Require bounded authority |\n",
                }
                for path, owner in (("a.md", "alpha"), ("b.md", "beta"))
            ],
        ]
        populated = auditor._collect_reference_semantic_advisories(
            documents, disposition_entries=[], evaluation_date=date(2026, 7, 12)
        )
        sentence_index = next(
            index
            for index, item in enumerate(populated["candidates"])
            if item["finding"] == "unconditional_absolute_candidate"
        )
        group_index = next(
            index
            for index, item in enumerate(populated["candidates"])
            if item["finding"] == "templated_block_candidate"
        )
        candidate_mutations = (
            (
                lambda report: report["candidates"][sentence_index].__setitem__(
                    "tokens", False
                ),
                f"candidates[{sentence_index}].tokens must be a non-negative integer",
            ),
            (
                lambda report: report["candidates"][sentence_index].__setitem__(
                    "total_tokens", False
                ),
                f"candidates[{sentence_index}].total_tokens must be a non-negative integer",
            ),
            (
                lambda report: report["candidates"][sentence_index].__setitem__(
                    "occurrence_count", True
                ),
                f"candidates[{sentence_index}].occurrence_count must be a non-negative integer",
            ),
            (
                lambda report: report["candidates"][sentence_index]["occurrences"][
                    0
                ].__setitem__("tokens", False),
                f"candidates[{sentence_index}].occurrences[0].tokens must be a non-negative integer",
            ),
            (
                lambda report: report["candidates"][sentence_index]["occurrences"][
                    0
                ]["lines"].__setitem__("start", True),
                f"candidates[{sentence_index}].occurrences[0].lines must be a positive ordered range",
            ),
            (
                lambda report: report["candidates"][sentence_index]["occurrences"][
                    0
                ]["lines"].__setitem__("end", False),
                f"candidates[{sentence_index}].occurrences[0].lines must be a positive ordered range",
            ),
            (
                lambda report: report["candidates"][group_index].__setitem__(
                    "distinct_path_count", False
                ),
                f"candidates[{group_index}].distinct_path_count must be a non-negative integer",
            ),
            (
                lambda report: report["candidates"][group_index].__setitem__(
                    "owner_count", False
                ),
                f"candidates[{group_index}].owner_count must be a non-negative integer",
            ),
        )
        for mutate, expected in candidate_mutations:
            with self.subTest(surface=expected):
                assert_rejected(populated, mutate, expected)

    def test_stale_two_family_semantic_report_hard_fails(self) -> None:
        semantic = _semantic()
        semantic["schema_version"] = 2
        semantic["finding_families"] = [
            "unconditional_absolute_candidate",
            "fixed_number_candidate",
        ]
        semantic["summary"]["by_finding"] = {
            key: semantic["summary"]["by_finding"][key]
            for key in semantic["finding_families"]
        }
        semantic["summary"].pop("group_metrics")
        _counts, errors = self.module._evaluate(
            _content(semantic_advisories=semantic), strict=False
        )
        self.assertTrue(any("schema_version must equal 5" in item for item in errors))
        self.assertTrue(any("finding_families must exactly match" in item for item in errors))
        self.assertTrue(any("group_metrics does not match" in item for item in errors))

    def test_duplicate_group_metrics_reconcile_candidates(self) -> None:
        auditor = self.module._load_auditor()
        documents = [
            {
                "path": path,
                "layer": "foundation",
                "owner": owner,
                "kind": "targeted",
                "text": "# Evidence\n\n## Tool Permission Boundary\n\n| Action | Boundary record |\n| --- | --- |\n| Read | Inspect current source |\n| Validate | Record command and result |\n| Mutate | Require bounded authority |\n",
            }
            for path, owner in (("a.md", "alpha"), ("b.md", "beta"))
        ]
        semantic = auditor._collect_reference_semantic_advisories(
            documents, disposition_entries=[], evaluation_date=date(2026, 7, 12)
        )
        candidate_index = next(
            index
            for index, item in enumerate(semantic["candidates"])
            if item["finding"] == "templated_block_candidate"
        )
        candidate = semantic["candidates"][candidate_index]
        counts, errors = self.module._evaluate(
            _content(semantic_advisories=semantic), strict=False
        )
        self.assertEqual([], errors)
        self.assertEqual(1, counts["templated_block_unresolved_groups"])
        self.assertEqual(2, counts["templated_block_occurrences"])
        self.assertEqual(candidate["total_tokens"], counts["templated_block_tokens"])

        mutations = (
            (
                lambda item: item["occurrences"][0].__setitem__(
                    "tokens", item["occurrences"][0]["tokens"] + 1
                ),
                "total_tokens does not match occurrences",
            ),
            (
                lambda item: item.__setitem__(
                    "canonical_occurrence",
                    {"path": "b.md", "lines": {"start": 4, "end": 9}},
                ),
                "fields must exactly match",
            ),
            (
                lambda item: item.__setitem__("distinct_path_count", 7),
                "distinct_path_count does not match occurrences",
            ),
            (
                lambda item: item.__setitem__("owner_count", 7),
                "owner_count does not match occurrences",
            ),
            (
                lambda item: item["occurrences"].__setitem__(
                    1, copy.deepcopy(item["occurrences"][0])
                ),
                "duplicates a path/range occurrence",
            ),
            (
                lambda item: item.__setitem__("fingerprint", "not-a-sha256"),
                "fingerprint must be lowercase sha256",
            ),
            (
                lambda item: item.__setitem__("content_fingerprint", "b" * 64),
                "content_fingerprint does not match normalized content",
            ),
            (
                lambda item: item["occurrences"][0].__setitem__(
                    "content_fingerprint", "b" * 64
                ),
                "content_fingerprint does not match normalized content",
            ),
        )
        for mutate, expected in mutations:
            malformed = copy.deepcopy(semantic)
            mutate(malformed["candidates"][candidate_index])
            _counts, errors = self.module._evaluate(
                _content(semantic_advisories=malformed), strict=False
            )
            self.assertTrue(any(expected in item for item in errors), errors)

    def test_semantic_disposition_contract_is_current_expiring_and_mutation_safe(self) -> None:
        auditor = self.module._load_auditor()
        document = {
            "path": "rule.md",
            "layer": "foundation",
            "owner": "rule-owner",
            "kind": "targeted",
            "text": "# Rule\n\n- Every external mutation must retain a current owner and rollback record.\n",
        }
        evaluated_on = date(2026, 7, 12)
        base = auditor._collect_reference_semantic_advisories(
            [document], disposition_entries=[], evaluation_date=evaluated_on
        )
        candidate = base["candidates"][0]
        entry = _disposition(candidate, "time-bounded-exception")
        semantic = auditor._collect_reference_semantic_advisories(
            [document], disposition_entries=[entry], evaluation_date=evaluated_on
        )
        counts, errors = self.module._evaluate(
            _content(semantic_advisories=semantic),
            strict=False,
            evaluation_date=evaluated_on,
        )
        self.assertEqual([], errors)
        self.assertEqual(1, counts["semantic_disposition_configured"])
        self.assertEqual(1, counts["semantic_disposition_applied"])
        self.assertEqual(1, counts["semantic_resolved_candidates"])

        _counts, expired_errors = self.module._evaluate(
            _content(semantic_advisories=semantic),
            strict=False,
            evaluation_date=date(2026, 8, 1),
        )
        self.assertTrue(any("strictly after" in item for item in expired_errors))

        for mutate, expected in (
            (
                lambda report: report["candidates"][0].__setitem__(
                    "fingerprint", "b" * 64
                ),
                "fingerprint must be lowercase|candidate_id does not match|stable identity",
            ),
            (
                lambda report: report["candidates"][0].__setitem__(
                    "skill_owner", "mutated-owner"
                ),
                "skill_owner must match|skill_owner does not match",
            ),
            (
                lambda report: report["candidates"][0]["disposition_record"].__setitem__(
                    "reason", "Mutated candidate exception rationale."
                ),
                "metadata was mutated",
            ),
        ):
            malformed = copy.deepcopy(semantic)
            mutate(malformed)
            _counts, mutation_errors = self.module._evaluate(
                _content(semantic_advisories=malformed),
                strict=False,
                evaluation_date=evaluated_on,
            )
            self.assertTrue(
                any(re.search(expected, item) for item in mutation_errors),
                mutation_errors,
            )

        missing = copy.deepcopy(base)
        missing.pop("disposition_contract")
        _counts, missing_errors = self.module._evaluate(
            _content(semantic_advisories=missing),
            strict=False,
            evaluation_date=evaluated_on,
        )
        self.assertTrue(
            any("disposition_contract must be a mapping" in item for item in missing_errors)
        )

    def test_control_disposition_error_does_not_block_professional_reference(self) -> None:
        auditor = self.module._load_auditor()
        documents = [
            {
                "path": "src/control-skills/control/references/rule.md",
                "layer": "control",
                "owner": "control",
                "kind": "targeted",
                "text": (
                    "# Rule\n\n"
                    "- Every external mutation must retain a current owner and rollback record.\n"
                ),
            },
            {
                "path": "src/professional-skills/professional/references/rule.md",
                "layer": "professional",
                "owner": "professional",
                "kind": "targeted",
                "text": (
                    "# Rule\n\n"
                    "- Every external deletion must retain a current owner and recovery record.\n"
                ),
            },
        ]
        initial = auditor._collect_reference_semantic_advisories(
            documents,
            disposition_entries=[],
            evaluation_date=date(2026, 7, 12),
        )
        candidates = {item["layer"]: item for item in initial["candidates"]}
        control_entry = _disposition(candidates["control"], "valid-contextual-rule")
        control_entry["skill_owner"] = "wrong-control-owner"
        professional_entry = _disposition(
            candidates["professional"], "valid-contextual-rule"
        )
        governed = auditor._collect_reference_semantic_advisories(
            documents,
            disposition_entries=sorted(
                [control_entry, professional_entry],
                key=lambda item: item["candidate_id"],
            ),
            evaluation_date=date(2026, 7, 12),
        )
        contract = governed["disposition_contract"]
        self.assertEqual([], contract["common_errors"])
        self.assertTrue(contract["surface_errors"]["control"])
        self.assertEqual([], contract["surface_errors"]["professional"])
        governed_by_layer = {item["layer"]: item for item in governed["candidates"]}
        self.assertIsNone(governed_by_layer["control"]["disposition"])
        self.assertEqual(
            "valid-contextual-rule",
            governed_by_layer["professional"]["disposition"],
        )

    def test_group_disposition_error_is_attributed_to_every_member_surface(self) -> None:
        auditor = self.module._load_auditor()
        candidate = {
            "candidate_id": "a" * 64,
            "layer": "group",
            "path": "group",
            "occurrences": [
                {"layer": "professional", "path": "professional.md"},
                {"layer": "foundation", "path": "foundation.md"},
            ],
        }
        entry = {"candidate_id": candidate["candidate_id"], "path": "group"}
        message = "reference_semantic_dispositions.entries[0]: invalid group evidence"
        common, surfaces = auditor._reference_disposition_error_attribution(
            [message],
            [entry],
            [candidate],
        )
        self.assertEqual([], common)
        self.assertEqual([message], surfaces["professional"])
        self.assertEqual([message], surfaces["foundation"])
        self.assertEqual([], surfaces["control"])
        self.assertEqual([], surfaces["domain"])

    def test_surface_validation_tampering_fails_closed(self) -> None:
        content = _content()
        content["surface_validation"]["surfaces"]["foundation"]["status"] = "fail"
        _counts, errors = self.module._evaluate(content, strict=False)
        self.assertTrue(
            any("does not match canonical source attribution" in item for item in errors),
            errors,
        )

    def test_fresh_collection_is_report_free_and_separate_from_current_application(self) -> None:
        report_paths = (
            ROOT / "reports" / "skill-content-audit.json",
            ROOT / "reports" / "skill-content-audit.md",
        )

        def hashes():
            return [hashlib.sha256(path.read_bytes()).hexdigest() for path in report_paths]

        before = hashes()
        auditor = self.module._load_auditor()
        with (
            mock.patch.object(self.module, "_load_auditor", return_value=auditor),
            mock.patch.object(
                auditor,
                "_collect_reference_content",
                wraps=auditor._collect_reference_content,
            ) as collect_reference,
            mock.patch.object(
                auditor,
                "_collect_semantic_content_with_application",
                side_effect=AssertionError("nonformal Reference validation consumed application state"),
            ) as collect_application,
        ):
            content = self.module._fresh_reference_content()
        collect_reference.assert_called_once_with()
        collect_application.assert_not_called()
        after = hashes()
        for strict in (False, True):
            with self.subTest(strict=strict):
                _counts, errors = self.module._evaluate(
                    content,
                    strict=strict,
                    validate_readability_sources=True,
                )
                self.assertEqual([], errors)
        self.assertEqual(before, after)

        _root, _reference, application = (
            auditor._collect_semantic_content_with_application()
        )
        self.assertEqual("current", application["status"])
        self.assertIsNone(application["error"])
        decision = json.loads(
            (ROOT / application["decision"]["path"]).read_text(encoding="utf-8")
        )
        expected_target_count = len(decision["semantic_decisions"])
        self.assertEqual(expected_target_count, application["target_count"])
        self.assertEqual(expected_target_count, application["applied_count"])
        self.assertEqual(0, application["completed_rewrite_count"])
        self.assertEqual(before, hashes())

    def test_authentication_security_jwt_verifier_source_contract(self) -> None:
        path = (
            ROOT
            / "src/foundation/capabilities/authentication-security/references/evidence-patterns.md"
        )
        row = next(
            line
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.startswith("| Access token validation matches its format |")
        )
        for required in (
            "explicit configured allowed-algorithm set (allowlist)",
            "bound to expected key types and verifier keys",
            "rejecting untrusted token-header attempts",
            "select an unconfigured algorithm",
            "switch key types",
            "select a verifier key",
            "For opaque/reference only:",
        ):
            with self.subTest(required=required):
                self.assertIn(required, row)


if __name__ == "__main__":
    unittest.main()
