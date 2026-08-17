#!/usr/bin/env python3
"""Validate authored Reference structure from fresh registry and Markdown source."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from datetime import date
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validation_utils import validate_ai_readability


ROOT = SCRIPT_DIR.parent
AUDIT_SCRIPT = ROOT / "scripts" / "audit-skill-content.py"
TARGETED_LINE_LIMIT = 60
MODE_CONTRACT_LINE_LIMIT = 80
DECISION_ITEM_LIMIT = 15
REFERENCE_CONTENT_SCHEMA_VERSION = 5
PREFACE_CONTRACT_SCHEMA_VERSION = 3
PREFACE_SOURCE_PRECEDENCE = ("local", "reference-index", "parent-root")
PREFACE_FIELDS = (
    "reference_type",
    "load_when",
    "do_not_load_when",
    "required_by",
    "required_output",
)
PREFACE_STATUSES = {"resolved", "missing", "conflict", "invalid"}
SEMANTIC_SCHEMA_VERSION = 7
SEMANTIC_DETECTOR_CONTRACT_VERSION = (
    "reference-semantic-detector-contract-v1"
)
SEMANTIC_DETECTOR_ALGORITHM = "sha256-canonical-json-v1"
SEMANTIC_DISPOSITION_SCHEMA_VERSION = 2
SEMANTIC_EXCEPTION_SOURCE = "config/skill-content-exceptions.yaml"
SEMANTIC_FINDINGS = (
    "unconditional_absolute_candidate",
    "fixed_number_candidate",
    "exact_normalized_duplicate_block",
    "templated_block_candidate",
)
SEMANTIC_GROUP_FINDINGS = (
    "exact_normalized_duplicate_block",
    "templated_block_candidate",
)
SEMANTIC_V4_COUNT_FIELDS = (
    "raw",
    "detector_downgraded",
    "untriaged",
    "rewrite",
    "valid_contextual_rule",
    "false_positive",
    "time_bounded_exception",
    "unresolved",
    "resolved",
    "p0_unresolved",
    "p1_unresolved",
    "p2_unresolved",
)
SEMANTIC_OBJECT_FIELDS = frozenset(
    {
        "schema_version",
        "detector_contract",
        "finding_families",
        "summary",
        "candidates",
        "disposition_contract",
        "limitations",
    }
)
SEMANTIC_SUMMARY_FIELDS = frozenset(
    {
        "raw_candidates",
        "detector_downgraded_candidates",
        "untriaged_candidates",
        "rewrite_candidates",
        "valid_contextual_rule_candidates",
        "false_positive_candidates",
        "time_bounded_exception_candidates",
        "unresolved_candidates",
        "resolved_candidates",
        "p0_unresolved_candidates",
        "p1_unresolved_candidates",
        "p2_unresolved_candidates",
        "by_finding",
        "group_metrics",
        "strict_unresolved",
    }
)
SEMANTIC_STRICT_UNRESOLVED_FIELDS = frozenset(
    {
        "fixed_number_candidates",
        "templated_block_groups",
        "unconditional_absolute_p0_p1_candidates",
        "p2_rewrite_advisories",
    }
)
SEMANTIC_GROUP_METRIC_FIELDS = frozenset({"groups", "occurrences", "tokens"})
SEMANTIC_CONTRACT_FIELDS = frozenset(
    {
        "schema_version",
        "source",
        "configured_count",
        "applied_count",
        "entries",
        "errors",
        "common_errors",
        "surface_errors",
        "group_scope",
    }
)
SEMANTIC_CANDIDATE_BASE_FIELDS = frozenset(
    {
        "finding",
        "fingerprint",
        "scope",
        "candidate_id",
        "path",
        "layer",
        "owner",
        "skill_owner",
        "tokens",
        "total_tokens",
        "signals",
        "preview",
        "detector_status",
        "occurrence_count",
        "occurrences",
        "evidence_fingerprint",
        "content_fingerprint",
        "priority",
        "disposition",
        "disposition_record",
        "governance_status",
        "unresolved",
        "resolved",
    }
)
SEMANTIC_GROUP_CANDIDATE_FIELDS = frozenset({"distinct_path_count", "owner_count"})
SEMANTIC_SENTENCE_OCCURRENCE_FIELDS = frozenset(
    {"path", "layer", "owner", "lines", "tokens", "signals", "preview", "detector_status"}
)
SEMANTIC_GROUP_OCCURRENCE_FIELDS = frozenset(
    {
        "fingerprint",
        "content_fingerprint",
        "path",
        "layer",
        "owner",
        "lines",
        "tokens",
        "preview",
    }
)
SEMANTIC_FINGERPRINT_RE = re.compile(r"^[0-9a-f]{64}$")
REFERENCE_REGISTRY_PATHS = {
    "control": Path("src/registry/control-skills.yaml"),
    "professional": Path("src/registry/professional-skills.yaml"),
    "foundation": Path("src/registry/foundation-skills.yaml"),
    "domain": Path("src/registry/domain-skills.yaml"),
}


def _is_exact_non_negative_int(value: object) -> bool:
    return type(value) is int and value >= 0


def _is_exact_positive_int(value: object) -> bool:
    return type(value) is int and value >= 1


@lru_cache(maxsize=1)
def _load_auditor() -> ModuleType:
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    module_name = "validate_reference_content_auditor"
    spec = importlib.util.spec_from_file_location(module_name, AUDIT_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {AUDIT_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _fresh_reference_content(
    *, evaluation_date: date | None = None
) -> dict[str, Any]:
    """Collect current registries and Markdown without reading or writing reports."""

    auditor = _load_auditor()
    if evaluation_date is None:
        return auditor._collect_reference_content()
    return auditor._collect_reference_content(evaluation_date=evaluation_date)


def _registry_scalar(value: str) -> str:
    value = value.strip()
    if value.startswith('"'):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return value
        return parsed if isinstance(parsed, str) else value
    return value


def _canonical_registry_reference_fields(
) -> tuple[dict[tuple[str, str, str, str], tuple[int, str]], list[str]]:
    """Rebuild exact Registry owner/path/field provenance from authored YAML."""

    result: dict[tuple[str, str, str, str], tuple[int, str]] = {}
    errors: list[str] = []
    for registry_path in REFERENCE_REGISTRY_PATHS.values():
        relative = registry_path.as_posix()
        candidate = ROOT / registry_path
        try:
            lines = candidate.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError):
            errors.append(f"cannot rebuild canonical Registry provenance from {relative}")
            continue
        owner: str | None = None
        reference_path: str | None = None
        in_reference_index = False
        for line_number, line in enumerate(lines, start=1):
            owner_match = re.match(r"^  - name:\s*(.+?)\s*$", line)
            if owner_match:
                owner = _registry_scalar(owner_match.group(1))
                reference_path = None
                in_reference_index = False
                continue
            if owner is None:
                continue
            if re.match(r"^    reference_index:\s*", line):
                in_reference_index = True
                reference_path = None
                continue
            if in_reference_index and re.match(r"^    \S", line):
                in_reference_index = False
                reference_path = None
            if not in_reference_index:
                continue
            path_match = re.match(r"^      - path:\s*(.+?)\s*$", line)
            if path_match:
                reference_path = _registry_scalar(path_match.group(1))
                continue
            field_match = re.match(
                r"^        (type|load_when|do_not_load_when|required_by|required_output):\s*(.+?)\s*$",
                line,
            )
            if field_match is None or reference_path is None:
                continue
            field = field_match.group(1)
            value = _registry_scalar(field_match.group(2))
            if field in {"required_by", "required_output"}:
                try:
                    parsed = json.loads(value)
                except json.JSONDecodeError:
                    parsed = None
                if isinstance(parsed, list):
                    value = json.dumps(parsed, ensure_ascii=True, separators=(",", ":"))
            key = (relative, owner, reference_path, field)
            if key in result:
                errors.append(
                    f"duplicate canonical Registry provenance for {owner}:{reference_path}:{field}"
                )
                continue
            result[key] = (line_number, value)
    return result, errors


def _effective_preface_contract(
    reference_content: dict[str, Any],
) -> tuple[dict[str, int], list[str]]:
    counts = {
        "missing_effective_reference_type": 0,
        "missing_effective_load_when": 0,
        "missing_effective_do_not_load_when": 0,
        "missing_effective_required_by": 0,
        "missing_effective_required_output": 0,
        "effective_preface_conflicts": 0,
        "effective_preface_invalid": 0,
        "effective_preface_contract_errors": 0,
        "effective_reference_types": 0,
        "effective_load_when": 0,
        "effective_do_not_load_when": 0,
        "effective_required_by": 0,
        "effective_required_output": 0,
    }
    errors: list[str] = []
    registry_line_cache: dict[Path, list[str]] = {}
    canonical_registry_fields, canonical_registry_errors = (
        _canonical_registry_reference_fields()
    )
    errors.extend(canonical_registry_errors)
    if reference_content.get("schema_version") != REFERENCE_CONTENT_SCHEMA_VERSION:
        errors.append(
            f"reference_content.schema_version must equal {REFERENCE_CONTENT_SCHEMA_VERSION}"
        )
    contract = reference_content.get("preface_contract")
    if not isinstance(contract, dict):
        return counts, [*errors, "reference_content.preface_contract must be a mapping"]
    if contract.get("schema_version") != PREFACE_CONTRACT_SCHEMA_VERSION:
        errors.append(
            "reference_content.preface_contract.schema_version must equal "
            f"{PREFACE_CONTRACT_SCHEMA_VERSION}"
        )
    if contract.get("source_precedence") != list(PREFACE_SOURCE_PRECEDENCE):
        errors.append(
            "reference_content.preface_contract.source_precedence must exactly match "
            + ", ".join(PREFACE_SOURCE_PRECEDENCE)
        )
    if contract.get("fields") != list(PREFACE_FIELDS):
        errors.append(
            "reference_content.preface_contract.fields must exactly match "
            + ", ".join(PREFACE_FIELDS)
        )
    source_fingerprint = contract.get("source_fingerprint")
    if not isinstance(source_fingerprint, dict):
        errors.append("reference_content.preface_contract.source_fingerprint must be a mapping")
    else:
        if set(source_fingerprint) != {"algorithm", "value", "document_count"}:
            errors.append(
                "reference_content.preface_contract.source_fingerprint must contain exactly algorithm, value, and document_count"
            )
        if source_fingerprint.get("algorithm") != "sha256":
            errors.append("reference_content.preface_contract.source_fingerprint.algorithm must equal sha256")
        if not re.fullmatch(r"[0-9a-f]{64}", str(source_fingerprint.get("value", ""))):
            errors.append("reference_content.preface_contract.source_fingerprint.value must be a lowercase SHA-256")
        document_count = source_fingerprint.get("document_count")
        if isinstance(document_count, bool) or not isinstance(document_count, int) or document_count < 1:
            errors.append("reference_content.preface_contract.source_fingerprint.document_count must be a positive integer")
    contract_errors = contract.get("errors")
    if not isinstance(contract_errors, list):
        errors.append("reference_content.preface_contract.errors must be a list")
        contract_errors = []
    contract_conflicts = contract.get("conflicts")
    if not isinstance(contract_conflicts, list):
        errors.append("reference_content.preface_contract.conflicts must be a list")
        contract_conflicts = []
    counts["effective_preface_contract_errors"] = len(contract_errors)
    counts["effective_preface_conflicts"] = len(contract_conflicts)

    allowed_contract_sources = {*PREFACE_SOURCE_PRECEDENCE, "registry"}
    for index, item in enumerate(contract_errors):
        item_path = f"reference_content.preface_contract.errors[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{item_path} must be a mapping")
            continue
        if item.get("source") not in allowed_contract_sources:
            errors.append(f"{item_path}.source is not recognized")
        if not isinstance(item.get("code"), str) or not item["code"]:
            errors.append(f"{item_path}.code must be a non-empty string")
        path = item.get("path")
        if not isinstance(path, str) or not path or Path(path).is_absolute() or ".." in Path(path).parts:
            errors.append(f"{item_path}.path must be repository-relative")
        line = item.get("line")
        if isinstance(line, bool) or not isinstance(line, int) or line < 1:
            errors.append(f"{item_path}.line must be a positive integer")
        if not isinstance(item.get("message"), str) or not item["message"]:
            errors.append(f"{item_path}.message must be a non-empty string")

    def contract_error_key(item: dict) -> tuple[str, int, str, str]:
        line = item.get("line")
        return (
            str(item.get("path", "")),
            int(line) if isinstance(line, int) and not isinstance(line, bool) else -1,
            str(item.get("code", "")),
            str(item.get("target", "")),
        )

    if contract_errors != sorted(contract_errors, key=contract_error_key):
        errors.append("reference_content.preface_contract.errors must be deterministically sorted")

    def evidence_key(item: dict) -> tuple[int, str, int, str]:
        source = item.get("source")
        source_index = (
            PREFACE_SOURCE_PRECEDENCE.index(source)
            if source in PREFACE_SOURCE_PRECEDENCE
            else len(PREFACE_SOURCE_PRECEDENCE)
        )
        line = item.get("line")
        return (
            source_index,
            str(item.get("path", "")),
            int(line) if isinstance(line, int) and not isinstance(line, bool) else -1,
            str(item.get("value", "")),
        )

    auditor = _load_auditor()
    flattened_conflicts: list[dict] = []
    references = reference_content.get("references")
    if not isinstance(references, list):
        return counts, [*errors, "reference_content.references must be a list"]
    for index, item in enumerate(references):
        item_path = f"reference_content.references[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{item_path} must be a mapping")
            continue
        if not item.get("exists"):
            continue
        target = item.get("path")
        if not isinstance(target, str) or not target:
            errors.append(f"{item_path}.path must be a non-empty string")
            continue
        effective = item.get("effective_preface")
        if not isinstance(effective, dict):
            errors.append(f"{item_path}.effective_preface must be a mapping")
            continue
        reported_conflicts = effective.get("conflicts")
        if not isinstance(reported_conflicts, list):
            errors.append(f"{item_path}.effective_preface.conflicts must be a list")
            reported_conflicts = []
        for conflict in reported_conflicts:
            if not isinstance(conflict, dict):
                errors.append(f"{item_path}.effective_preface.conflicts entries must be mappings")
                continue
            if not isinstance(conflict.get("field"), str) or not conflict["field"]:
                errors.append(f"{item_path}.effective_preface conflict field must be non-empty")
            if not isinstance(conflict.get("code"), str) or not conflict["code"]:
                errors.append(f"{item_path}.effective_preface conflict code must be non-empty")
            if not isinstance(conflict.get("message"), str) or not conflict["message"]:
                errors.append(f"{item_path}.effective_preface conflict message must be non-empty")
            if not isinstance(conflict.get("evidence"), list) or not conflict["evidence"]:
                errors.append(f"{item_path}.effective_preface conflict evidence must be non-empty")
        target_path = Path(target)
        owner_root = target_path.parent.parent
        owner = item.get("owner")
        try:
            reference_path = target_path.relative_to(owner_root).as_posix()
        except ValueError:
            reference_path = ""
        canonical_by_field: dict[str, list[dict]] = {
            field: [] for field in PREFACE_FIELDS
        }
        for field in PREFACE_FIELDS:
            field_path = f"{item_path}.effective_preface.{field}"
            value = effective.get(field)
            if not isinstance(value, dict):
                errors.append(f"{field_path} must be a mapping")
                continue
            status = value.get("status")
            if status not in PREFACE_STATUSES:
                errors.append(f"{field_path}.status must be resolved, missing, conflict, or invalid")
                continue
            evidence = value.get("evidence")
            if not isinstance(evidence, list):
                errors.append(f"{field_path}.evidence must be a list")
                evidence = []
            for evidence_index, row in enumerate(evidence):
                evidence_path = f"{field_path}.evidence[{evidence_index}]"
                if not isinstance(row, dict):
                    errors.append(f"{evidence_path} must be a mapping")
                    continue
                source = row.get("source")
                path = row.get("path")
                line = row.get("line")
                raw_value = row.get("value")
                accepted = row.get("accepted")
                if source not in PREFACE_SOURCE_PRECEDENCE:
                    errors.append(f"{evidence_path}.source is not recognized")
                if not isinstance(path, str) or not path or Path(path).is_absolute() or ".." in Path(path).parts:
                    errors.append(f"{evidence_path}.path must be a repository-relative owner path")
                else:
                    expected_path = {
                        "local": target_path,
                        "reference-index": REFERENCE_REGISTRY_PATHS.get(
                            str(item.get("layer", ""))
                        ),
                        "parent-root": owner_root / "SKILL.md",
                    }.get(source)
                    if expected_path is not None and Path(path) != expected_path:
                        errors.append(
                            f"{evidence_path}.path does not match the canonical {source} document"
                        )
                    candidate = ROOT / path
                    if candidate.exists() or candidate.is_symlink():
                        if auditor._path_chain_uses_symlink(candidate, ROOT):
                            errors.append(f"{evidence_path}.path uses a symlink chain")
                        else:
                            evidence_boundary = (
                                ROOT / "src" / "registry"
                                if source == "reference-index"
                                else ROOT / owner_root
                            )
                            contained = True
                            try:
                                candidate.resolve(strict=True).relative_to(
                                    evidence_boundary.resolve(strict=True)
                                )
                            except (OSError, ValueError):
                                contained = False
                                errors.append(
                                    f"{evidence_path}.path realpath crosses the target owner boundary"
                                )
                            if contained and source == "reference-index":
                                try:
                                    source_lines = registry_line_cache.setdefault(
                                        candidate,
                                        candidate.read_text(encoding="utf-8").splitlines(),
                                    )
                                except (OSError, UnicodeError):
                                    errors.append(
                                        f"{evidence_path}.path cannot be read as Registry YAML"
                                    )
                                    source_lines = []
                                if isinstance(line, int) and not isinstance(line, bool):
                                    if line < 1 or line > len(source_lines):
                                        errors.append(
                                            f"{evidence_path}.line is outside the Registry document"
                                        )
                                    elif isinstance(raw_value, str):
                                        registry_field = (
                                            "type" if field == "reference_type" else field
                                        )
                                        declaration = re.match(
                                            rf"^\s*{re.escape(registry_field)}:\s*(.+?)\s*$",
                                            source_lines[line - 1],
                                        )
                                        if declaration is None:
                                            errors.append(
                                                f"{evidence_path}.line does not declare {registry_field}"
                                            )
                                        else:
                                            declared: object = declaration.group(1).strip()
                                            if isinstance(declared, str) and declared.startswith(("\"", "[")):
                                                try:
                                                    declared = json.loads(declared)
                                                except json.JSONDecodeError:
                                                    pass
                                            if isinstance(declared, list):
                                                declared = json.dumps(
                                                    declared,
                                                    ensure_ascii=True,
                                                    separators=(",", ":"),
                                                )
                                            if declared != raw_value:
                                                errors.append(
                                                    f"{evidence_path}.line value does not match its Registry declaration"
                                                )
                                if (
                                    isinstance(owner, str)
                                    and owner
                                    and reference_path
                                    and isinstance(raw_value, str)
                                ):
                                    registry_field = (
                                        "type" if field == "reference_type" else field
                                    )
                                    canonical_key = (
                                        path,
                                        owner,
                                        reference_path,
                                        registry_field,
                                    )
                                    canonical = canonical_registry_fields.get(
                                        canonical_key
                                    )
                                    if canonical is None:
                                        errors.append(
                                            f"{evidence_path} has no canonical Registry owner/path/field declaration"
                                        )
                                    elif (line, raw_value) != canonical:
                                        errors.append(
                                            f"{evidence_path} does not match its canonical Registry owner/path/field declaration"
                                        )
                if isinstance(line, bool) or not isinstance(line, int) or line < 1:
                    errors.append(f"{evidence_path}.line must be a positive integer")
                if not isinstance(raw_value, str) or not raw_value.strip():
                    errors.append(f"{evidence_path}.value must be a non-empty string")
                if not isinstance(accepted, bool):
                    errors.append(f"{evidence_path}.accepted must be a boolean")
                if (
                    source in PREFACE_SOURCE_PRECEDENCE
                    and isinstance(path, str)
                    and path
                    and isinstance(line, int)
                    and not isinstance(line, bool)
                    and line >= 1
                    and isinstance(raw_value, str)
                    and raw_value.strip()
                ):
                    canonical = auditor._canonical_preface_evidence(field, row)
                    canonical_by_field[field].append(canonical)
                    if row != canonical:
                        errors.append(
                            f"{evidence_path} does not match its canonical declaration"
                        )
            if evidence != sorted(evidence, key=evidence_key):
                errors.append(f"{field_path}.evidence must be in deterministic source/path/line order")
        canonical_effective = auditor._effective_preface(canonical_by_field)
        if effective != canonical_effective:
            errors.append(
                f"{item_path}.effective_preface does not match canonical evidence resolution"
            )
        for field in PREFACE_FIELDS:
            canonical_field = canonical_effective[field]
            status = canonical_field["status"]
            if status == "resolved":
                counts[
                    f"effective_{field}"
                    if field != "reference_type"
                    else "effective_reference_types"
                ] += 1
            elif status == "missing":
                counts[f"missing_effective_{field}"] += 1
            elif status == "invalid":
                counts["effective_preface_invalid"] += 1
        for conflict in canonical_effective["conflicts"]:
            flattened_conflicts.append(
                {
                    "layer": item.get("layer"),
                    "owner": item.get("owner"),
                    "path": target,
                    **conflict,
                }
            )

    layer_order = {"control": 0, "professional": 1, "foundation": 2, "domain": 3}

    def conflict_key(item: dict) -> tuple[int, str, str, str, str, str]:
        return (
            layer_order.get(str(item.get("layer", "")), len(layer_order)),
            str(item.get("owner", "")),
            str(item.get("path", "")),
            str(item.get("field", "")),
            str(item.get("code", "")),
            json.dumps(item.get("evidence", []), sort_keys=True),
        )

    if contract_conflicts != sorted(contract_conflicts, key=conflict_key):
        errors.append("reference_content.preface_contract.conflicts must be deterministically sorted")
    if contract_conflicts != sorted(flattened_conflicts, key=conflict_key):
        errors.append("reference_content.preface_contract.conflicts does not match per-reference conflicts")
    counts["effective_preface_conflicts"] = len(flattened_conflicts)
    summary = reference_content.get("summary")
    if not isinstance(summary, dict):
        errors.append("reference_content.summary must be a mapping")
    else:
        expected_summary = {
            "effective_reference_types": counts["effective_reference_types"],
            "missing_effective_reference_types": counts[
                "missing_effective_reference_type"
            ],
            "effective_load_when": counts["effective_load_when"],
            "missing_effective_load_when": counts["missing_effective_load_when"],
            "effective_do_not_load_when": counts["effective_do_not_load_when"],
            "missing_effective_do_not_load_when": counts[
                "missing_effective_do_not_load_when"
            ],
            "effective_required_by": counts["effective_required_by"],
            "missing_effective_required_by": counts[
                "missing_effective_required_by"
            ],
            "effective_required_output": counts["effective_required_output"],
            "missing_effective_required_output": counts[
                "missing_effective_required_output"
            ],
            "effective_preface_conflicts": counts["effective_preface_conflicts"],
            "effective_preface_contract_errors": counts["effective_preface_contract_errors"],
            "effective_preface_invalid": counts["effective_preface_invalid"],
        }
        for key, expected in expected_summary.items():
            if summary.get(key) != expected:
                errors.append(f"reference_content.summary.{key} does not match effective preface facts")
    return counts, errors


def _semantic_contract(
    reference_content: dict[str, Any],
    *,
    evaluation_date: date | None = None,
) -> tuple[dict[str, int], list[str]]:
    """Validate semantic schema v7 and recompute every governance fact."""

    counts = {
        "semantic_raw_candidates": 0,
        "semantic_detector_downgraded_candidates": 0,
        "semantic_untriaged_candidates": 0,
        "semantic_rewrite_candidates": 0,
        "semantic_resolved_candidates": 0,
        "semantic_unresolved_candidates": 0,
        "unconditional_absolute_p0_p1_unresolved_candidates": 0,
        "fixed_number_unresolved_candidates": 0,
        "templated_block_unresolved_groups": 0,
        "p2_rewrite_advisory_candidates": 0,
        "exact_normalized_duplicate_unresolved_groups": 0,
        "exact_duplicate_occurrences": 0,
        "exact_duplicate_tokens": 0,
        "templated_block_occurrences": 0,
        "templated_block_tokens": 0,
        "semantic_disposition_configured": 0,
        "semantic_disposition_applied": 0,
        "semantic_disposition_errors": 0,
    }
    errors: list[str] = []
    semantic = reference_content.get("semantic_advisories")
    if not isinstance(semantic, dict):
        return counts, ["semantic_advisories must be a current mapping"]
    auditor = _load_auditor()
    if set(semantic) != SEMANTIC_OBJECT_FIELDS:
        errors.append(
            "semantic_advisories must contain exactly: "
            + ", ".join(sorted(SEMANTIC_OBJECT_FIELDS))
        )
    if semantic.get("schema_version") != SEMANTIC_SCHEMA_VERSION:
        errors.append(
            f"semantic_advisories.schema_version must equal {SEMANTIC_SCHEMA_VERSION}"
        )
    detector_contract = semantic.get("detector_contract")
    if not isinstance(detector_contract, dict) or set(detector_contract) != {
        "contract_version",
        "algorithm",
        "value",
    }:
        errors.append(
            "semantic_advisories.detector_contract must contain exactly "
            "algorithm, contract_version, and value"
        )
    else:
        if (
            detector_contract.get("contract_version")
            != SEMANTIC_DETECTOR_CONTRACT_VERSION
        ):
            errors.append(
                "semantic_advisories.detector_contract.contract_version is invalid"
            )
        if detector_contract.get("algorithm") != SEMANTIC_DETECTOR_ALGORITHM:
            errors.append(
                "semantic_advisories.detector_contract.algorithm is invalid"
            )
        value = detector_contract.get("value")
        if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
            errors.append(
                "semantic_advisories.detector_contract.value must be lowercase SHA-256"
            )
        expected_detector = auditor._reference_semantic_detector_contract()
        if detector_contract != expected_detector:
            errors.append(
                "semantic_advisories.detector_contract does not match current "
                "reachable Reference detector behavior"
            )
    if semantic.get("finding_families") != list(SEMANTIC_FINDINGS):
        errors.append(
            "semantic_advisories.finding_families must exactly match "
            + ", ".join(SEMANTIC_FINDINGS)
        )
    candidates = semantic.get("candidates")
    if not isinstance(candidates, list):
        errors.append("semantic_advisories.candidates must be a list")
        candidates = []
    if candidates != sorted(candidates, key=auditor._semantic_candidate_sort_key):
        errors.append("semantic_advisories.candidates must be canonically sorted")
    seen_candidate_ids: set[str] = set()
    expected_by_finding = {
        finding: {field: 0 for field in SEMANTIC_V4_COUNT_FIELDS}
        for finding in SEMANTIC_FINDINGS
    }
    group_metrics = {
        finding: {"groups": 0, "occurrences": 0, "tokens": 0}
        for finding in SEMANTIC_GROUP_FINDINGS
    }

    for index, candidate in enumerate(candidates):
        label = f"semantic_advisories.candidates[{index}]"
        if not isinstance(candidate, dict):
            errors.append(f"{label} must be a mapping")
            continue
        finding = candidate.get("finding")
        if finding not in SEMANTIC_FINDINGS:
            errors.append(f"{label}.finding is not declared")
            continue
        expected_candidate_fields = set(SEMANTIC_CANDIDATE_BASE_FIELDS)
        if finding in SEMANTIC_GROUP_FINDINGS:
            expected_candidate_fields.update(SEMANTIC_GROUP_CANDIDATE_FIELDS)
        if finding == "unconditional_absolute_candidate" and "downgrade_reasons" in candidate:
            expected_candidate_fields.add("downgrade_reasons")
        if set(candidate) != expected_candidate_fields:
            errors.append(
                f"{label} fields must exactly match the schema for {finding}"
            )
        fingerprint = candidate.get("fingerprint")
        if not isinstance(fingerprint, str) or not SEMANTIC_FINGERPRINT_RE.fullmatch(
            fingerprint
        ):
            errors.append(f"{label}.fingerprint must be lowercase sha256")
            continue
        scope = candidate.get("scope")
        path = candidate.get("path")
        owner = candidate.get("owner")
        skill_owner = candidate.get("skill_owner")
        is_group = finding in SEMANTIC_GROUP_FINDINGS
        if is_group:
            if any(
                value != "group"
                for value in (scope, path, candidate.get("layer"), owner, skill_owner)
            ):
                errors.append(
                    f"{label} group scope/path/layer/owner/skill_owner must equal 'group'"
                )
        else:
            if not auditor._is_canonical_semantic_path(path) or scope != path:
                errors.append(
                    f"{label} sentence scope/path must be the same canonical relative POSIX path"
                )
            if skill_owner != owner or not isinstance(skill_owner, str) or not skill_owner:
                errors.append(f"{label}.skill_owner must match the sentence owner")
        try:
            expected_id = auditor._semantic_candidate_id(finding, scope, fingerprint)
        except (TypeError, ValueError):
            expected_id = None
        candidate_id = candidate.get("candidate_id")
        if not isinstance(candidate_id, str) or not SEMANTIC_FINGERPRINT_RE.fullmatch(
            candidate_id
        ):
            errors.append(f"{label}.candidate_id must be lowercase sha256")
        elif candidate_id != expected_id:
            errors.append(f"{label}.candidate_id does not match stable identity inputs")
        elif candidate_id in seen_candidate_ids:
            errors.append(f"{label}.candidate_id must be unique")
        else:
            seen_candidate_ids.add(candidate_id)
        for field in ("tokens", "total_tokens"):
            value = candidate.get(field)
            if not _is_exact_non_negative_int(value):
                errors.append(f"{label}.{field} must be a non-negative integer")
        if not isinstance(candidate.get("preview"), str):
            errors.append(f"{label}.preview must be a string")
        signals = candidate.get("signals")
        if (
            not isinstance(signals, list)
            or signals != sorted(set(signals))
            or not all(isinstance(item, str) and item for item in signals)
        ):
            errors.append(f"{label}.signals must be sorted unique non-blank strings")
        occurrences = candidate.get("occurrences")
        occurrence_count = candidate.get("occurrence_count")
        if not isinstance(occurrences, list) or not occurrences:
            errors.append(f"{label}.occurrences must be a non-empty list")
            occurrences = []
        if not _is_exact_non_negative_int(occurrence_count):
            errors.append(f"{label}.occurrence_count must be a non-negative integer")
        elif occurrence_count != len(occurrences):
            errors.append(f"{label}.occurrence_count must match occurrences")
        valid_occurrences: list[dict] = []
        occurrence_keys: set[tuple[str, int, int]] = set()
        for occurrence_index, occurrence in enumerate(occurrences):
            occurrence_label = f"{label}.occurrences[{occurrence_index}]"
            if not isinstance(occurrence, dict):
                errors.append(f"{occurrence_label} must be a mapping")
                continue
            expected_occurrence_fields = set(
                SEMANTIC_GROUP_OCCURRENCE_FIELDS
                if is_group
                else SEMANTIC_SENTENCE_OCCURRENCE_FIELDS
            )
            if finding == "unconditional_absolute_candidate":
                if "downgrade_reason" in occurrence:
                    expected_occurrence_fields.add("downgrade_reason")
                if "semantic_contexts" in occurrence:
                    expected_occurrence_fields.add("semantic_contexts")
            if set(occurrence) != expected_occurrence_fields:
                errors.append(
                    f"{occurrence_label} fields must exactly match the schema for {finding}"
                )
            occurrence_path = occurrence.get("path")
            occurrence_owner = occurrence.get("owner")
            lines = occurrence.get("lines")
            if not auditor._is_canonical_semantic_path(occurrence_path):
                errors.append(
                    f"{occurrence_label}.path must be a canonical relative POSIX path"
                )
                continue
            if not isinstance(occurrence_owner, str) or not occurrence_owner:
                errors.append(f"{occurrence_label}.owner must be non-empty")
                continue
            if is_group and (
                not isinstance(occurrence.get("content_fingerprint"), str)
                or not SEMANTIC_FINGERPRINT_RE.fullmatch(
                    occurrence["content_fingerprint"]
                )
            ):
                errors.append(
                    f"{occurrence_label}.content_fingerprint must be lowercase sha256"
                )
                continue
            occurrence_tokens = occurrence.get("tokens")
            if not _is_exact_non_negative_int(occurrence_tokens):
                errors.append(f"{occurrence_label}.tokens must be a non-negative integer")
                continue
            if not isinstance(lines, dict):
                errors.append(f"{occurrence_label}.lines must be a mapping")
                continue
            if set(lines) != {"start", "end"}:
                errors.append(
                    f"{occurrence_label}.lines must contain exactly start and end"
                )
            start, end = lines.get("start"), lines.get("end")
            if (
                not _is_exact_positive_int(start)
                or not _is_exact_positive_int(end)
                or end < start
            ):
                errors.append(f"{occurrence_label}.lines must be a positive ordered range")
                continue
            key = (occurrence_path, start, end)
            if key in occurrence_keys:
                errors.append(f"{occurrence_label} duplicates a path/range occurrence")
            occurrence_keys.add(key)
            if not is_group:
                occurrence_signals = occurrence.get("signals")
                if (
                    not isinstance(occurrence_signals, list)
                    or occurrence_signals != sorted(set(occurrence_signals))
                    or not all(
                        isinstance(item, str) and item for item in occurrence_signals
                    )
                ):
                    errors.append(
                        f"{occurrence_label}.signals must be sorted unique non-blank strings"
                    )
                occurrence_status = occurrence.get("detector_status")
                if occurrence_status not in {"candidate", "downgraded"}:
                    errors.append(f"{occurrence_label}.detector_status is invalid")
                if finding == "unconditional_absolute_candidate":
                    reason = occurrence.get("downgrade_reason")
                    if (occurrence_status == "downgraded") != (
                        isinstance(reason, str) and bool(reason)
                    ):
                        errors.append(
                            f"{occurrence_label}.downgrade_reason presence is inconsistent"
                        )
                    if reason is not None and reason not in (
                        auditor.SEMANTIC_ABSOLUTE_DOWNGRADE_REASONS
                    ):
                        errors.append(
                            f"{occurrence_label}.downgrade_reason is not declared"
                        )
                    contexts = occurrence.get("semantic_contexts")
                    if contexts is not None and (
                        not isinstance(contexts, list)
                        or contexts != sorted(set(contexts))
                        or not all(isinstance(item, str) and item for item in contexts)
                    ):
                        errors.append(
                            f"{occurrence_label}.semantic_contexts must be sorted unique non-blank strings"
                        )
            valid_occurrences.append(occurrence)
        expected_occurrences = sorted(
            valid_occurrences,
            key=lambda row: (
                row["path"],
                row["lines"]["start"],
                row["lines"]["end"],
                row.get("preview", ""),
            ),
        )
        if valid_occurrences != expected_occurrences:
            errors.append(f"{label}.occurrences must be deterministically ordered")
        if not is_group and any(row.get("path") != path for row in valid_occurrences):
            errors.append(f"{label} sentence occurrences must stay within candidate path")
        if valid_occurrences:
            canonical = valid_occurrences[0]
            if candidate.get("tokens") != canonical.get("tokens"):
                errors.append(f"{label}.tokens must match the canonical occurrence")
            if candidate.get("preview") != canonical.get("preview"):
                errors.append(f"{label}.preview must match the canonical occurrence")
            if not is_group:
                if candidate.get("layer") != canonical.get("layer"):
                    errors.append(f"{label}.layer must match the canonical occurrence")
                if candidate.get("owner") != canonical.get("owner"):
                    errors.append(f"{label}.owner must match the canonical occurrence")
                if candidate.get("total_tokens") != sum(
                    row.get("tokens", 0) for row in valid_occurrences
                ):
                    errors.append(f"{label}.total_tokens does not match occurrences")
                expected_signals = sorted(
                    {
                        signal
                        for row in valid_occurrences
                        for signal in row.get("signals", [])
                    }
                )
                if candidate.get("signals") != expected_signals:
                    errors.append(f"{label}.signals does not match occurrences")
                expected_detector_status = (
                    "candidate"
                    if any(
                        row.get("detector_status") == "candidate"
                        for row in valid_occurrences
                    )
                    else "downgraded"
                )
                if candidate.get("detector_status") != expected_detector_status:
                    errors.append(f"{label}.detector_status does not match occurrences")
                expected_reasons = sorted(
                    {
                        row["downgrade_reason"]
                        for row in valid_occurrences
                        if isinstance(row.get("downgrade_reason"), str)
                    }
                )
                if finding == "unconditional_absolute_candidate":
                    if expected_reasons:
                        if candidate.get("downgrade_reasons") != expected_reasons:
                            errors.append(
                                f"{label}.downgrade_reasons does not match occurrences"
                            )
                    elif "downgrade_reasons" in candidate:
                        errors.append(
                            f"{label}.downgrade_reasons must be absent without downgraded occurrences"
                        )
        evidence_fingerprint = candidate.get("evidence_fingerprint")
        content_fingerprint = candidate.get("content_fingerprint")
        if is_group:
            expected_evidence = auditor._semantic_evidence_fingerprint(valid_occurrences)
            if evidence_fingerprint != expected_evidence:
                errors.append(f"{label}.evidence_fingerprint does not match membership")
            try:
                expected_content = auditor._semantic_content_fingerprint(
                    valid_occurrences
                )
            except ValueError as exc:
                errors.append(f"{label}.content_fingerprint: {exc}")
                expected_content = None
            if content_fingerprint != expected_content:
                errors.append(
                    f"{label}.content_fingerprint does not match normalized content"
                )
            if len({row["path"] for row in valid_occurrences}) < 2:
                errors.append(f"{label} group must retain at least two paths")
            if finding == "templated_block_candidate" and len(
                {row["owner"] for row in valid_occurrences}
            ) < 2:
                errors.append(f"{label} templated group must retain at least two owners")
            group_metrics[finding]["groups"] += 1
            group_metrics[finding]["occurrences"] += len(valid_occurrences)
            total_tokens = candidate.get("total_tokens")
            if _is_exact_non_negative_int(total_tokens):
                group_metrics[finding]["tokens"] += total_tokens
                if total_tokens != sum(row["tokens"] for row in valid_occurrences):
                    errors.append(f"{label}.total_tokens does not match occurrences")
            else:
                errors.append(f"{label}.total_tokens must be a non-negative integer")
            distinct_path_count = candidate.get("distinct_path_count")
            if not _is_exact_non_negative_int(distinct_path_count):
                errors.append(f"{label}.distinct_path_count must be a non-negative integer")
            elif distinct_path_count != len(
                {row["path"] for row in valid_occurrences}
            ):
                errors.append(f"{label}.distinct_path_count does not match occurrences")
            owner_count = candidate.get("owner_count")
            if not _is_exact_non_negative_int(owner_count):
                errors.append(f"{label}.owner_count must be a non-negative integer")
            elif owner_count != len(
                {row["owner"] for row in valid_occurrences}
            ):
                errors.append(f"{label}.owner_count does not match occurrences")
        elif evidence_fingerprint is not None:
            errors.append(f"{label}.evidence_fingerprint must be null for sentence candidates")
        elif content_fingerprint is not None:
            errors.append(f"{label}.content_fingerprint must be null for sentence candidates")

        detector_status = candidate.get("detector_status")
        disposition = candidate.get("disposition")
        priority = candidate.get("priority")
        governance_status = candidate.get("governance_status")
        unresolved = candidate.get("unresolved")
        resolved = candidate.get("resolved")
        record = candidate.get("disposition_record")
        if detector_status not in {"candidate", "downgraded"}:
            errors.append(f"{label}.detector_status is invalid")
        if disposition is not None and disposition not in auditor.SEMANTIC_DISPOSITIONS:
            errors.append(f"{label}.disposition is invalid")
        if priority is not None and priority not in auditor.SEMANTIC_PRIORITIES:
            errors.append(f"{label}.priority is invalid")
        expected_status: str
        expected_unresolved: bool
        expected_resolved: bool
        if disposition is None and detector_status == "downgraded":
            expected_status, expected_unresolved, expected_resolved = (
                "detector-downgraded",
                False,
                False,
            )
            if priority is not None:
                errors.append(f"{label} detector-downgraded priority must be null")
        elif disposition is None:
            expected_status, expected_unresolved, expected_resolved = (
                "untriaged",
                True,
                False,
            )
            if priority != auditor.SEMANTIC_DEFAULT_PRIORITIES[finding]:
                errors.append(f"{label} untriaged priority is not fail-closed")
        elif disposition == "rewrite":
            expected_status, expected_unresolved, expected_resolved = (
                "unresolved-rewrite",
                True,
                False,
            )
        else:
            expected_status, expected_unresolved, expected_resolved = (
                f"resolved-{disposition}",
                False,
                True,
            )
        if (
            governance_status != expected_status
            or unresolved is not expected_unresolved
            or resolved is not expected_resolved
        ):
            errors.append(f"{label} governance status flags are inconsistent")
        if (disposition is None) != (record is None):
            errors.append(f"{label}.disposition_record presence is inconsistent")

        row = expected_by_finding[finding]
        row["raw"] += 1
        row["detector_downgraded"] += governance_status == "detector-downgraded"
        row["untriaged"] += governance_status == "untriaged"
        row["rewrite"] += disposition == "rewrite"
        row["valid_contextual_rule"] += disposition == "valid-contextual-rule"
        row["false_positive"] += disposition == "false-positive"
        row["time_bounded_exception"] += disposition == "time-bounded-exception"
        row["unresolved"] += bool(unresolved)
        row["resolved"] += bool(resolved)
        row["p0_unresolved"] += bool(unresolved) and priority == "P0"
        row["p1_unresolved"] += bool(unresolved) and priority == "P1"
        row["p2_unresolved"] += bool(unresolved) and priority == "P2"

    summary = semantic.get("summary")
    if not isinstance(summary, dict):
        errors.append("semantic_advisories.summary must be a mapping")
        summary = {}
    elif set(summary) != SEMANTIC_SUMMARY_FIELDS:
        errors.append(
            "semantic_advisories.summary must contain exactly: "
            + ", ".join(sorted(SEMANTIC_SUMMARY_FIELDS))
        )
    by_finding = summary.get("by_finding")
    if not isinstance(by_finding, dict) or set(by_finding) != set(SEMANTIC_FINDINGS):
        errors.append(
            "semantic_advisories.summary.by_finding must contain exactly the declared finding families"
        )
    else:
        for finding, row in by_finding.items():
            if not isinstance(row, dict) or set(row) != set(SEMANTIC_V4_COUNT_FIELDS):
                errors.append(
                    f"semantic_advisories.summary.by_finding.{finding} fields must exactly match schema v7"
                )
                continue
            for field in SEMANTIC_V4_COUNT_FIELDS:
                if not _is_exact_non_negative_int(row.get(field)):
                    errors.append(
                        f"semantic_advisories.summary.by_finding.{finding}.{field} must be a non-negative integer"
                    )
    if by_finding != expected_by_finding:
        errors.append("semantic_advisories.summary.by_finding does not match candidates")
    reported_group_metrics = summary.get("group_metrics")
    if not isinstance(reported_group_metrics, dict) or set(
        reported_group_metrics
    ) != set(SEMANTIC_GROUP_FINDINGS):
        errors.append(
            "semantic_advisories.summary.group_metrics must contain exactly the group finding families"
        )
    else:
        for finding, row in reported_group_metrics.items():
            if not isinstance(row, dict) or set(row) != SEMANTIC_GROUP_METRIC_FIELDS:
                errors.append(
                    f"semantic_advisories.summary.group_metrics.{finding} fields must exactly match schema v7"
                )
                continue
            for field in SEMANTIC_GROUP_METRIC_FIELDS:
                if not _is_exact_non_negative_int(row.get(field)):
                    errors.append(
                        f"semantic_advisories.summary.group_metrics.{finding}.{field} must be a non-negative integer"
                    )
    if reported_group_metrics != group_metrics:
        errors.append("semantic_advisories.summary.group_metrics does not match candidates")
    totals = {
        field: sum(expected_by_finding[finding][field] for finding in SEMANTIC_FINDINGS)
        for field in SEMANTIC_V4_COUNT_FIELDS
    }
    expected_top = {
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
    }
    for field, expected in expected_top.items():
        value = summary.get(field)
        if not _is_exact_non_negative_int(value):
            errors.append(
                f"semantic_advisories.summary.{field} must be a non-negative integer"
            )
        elif value != expected:
            errors.append(f"semantic_advisories.summary.{field} does not match candidates")
    strict_unresolved = {
        "fixed_number_candidates": expected_by_finding["fixed_number_candidate"][
            "unresolved"
        ],
        "templated_block_groups": expected_by_finding["templated_block_candidate"][
            "unresolved"
        ],
        "unconditional_absolute_p0_p1_candidates": (
            expected_by_finding["unconditional_absolute_candidate"]["p0_unresolved"]
            + expected_by_finding["unconditional_absolute_candidate"]["p1_unresolved"]
        ),
        "p2_rewrite_advisories": sum(
            isinstance(candidate, dict)
            and candidate.get("disposition") == "rewrite"
            and candidate.get("priority") == "P2"
            and candidate.get("finding") not in SEMANTIC_GROUP_FINDINGS
            and candidate.get("finding") != "fixed_number_candidate"
            for candidate in candidates
        ),
    }
    reported_strict = summary.get("strict_unresolved")
    if not isinstance(reported_strict, dict) or set(
        reported_strict
    ) != SEMANTIC_STRICT_UNRESOLVED_FIELDS:
        errors.append(
            "semantic_advisories.summary.strict_unresolved fields must exactly match schema v7"
        )
    else:
        for field in SEMANTIC_STRICT_UNRESOLVED_FIELDS:
            if not _is_exact_non_negative_int(reported_strict.get(field)):
                errors.append(
                    f"semantic_advisories.summary.strict_unresolved.{field} must be a non-negative integer"
                )
    if reported_strict != strict_unresolved:
        errors.append("semantic_advisories.summary.strict_unresolved does not match candidates")

    evaluated_on = (
        _load_auditor()._effective_evaluation_date()
        if evaluation_date is None
        else evaluation_date
    )
    contract = semantic.get("disposition_contract")
    if not isinstance(contract, dict):
        errors.append("semantic_advisories.disposition_contract must be a mapping")
        contract = {}
    elif set(contract) != SEMANTIC_CONTRACT_FIELDS:
        errors.append(
            "semantic_advisories.disposition_contract fields must exactly match schema v7"
        )
    if contract.get("schema_version") != SEMANTIC_DISPOSITION_SCHEMA_VERSION:
        errors.append(
            "semantic_advisories.disposition_contract.schema_version must equal "
            f"{SEMANTIC_DISPOSITION_SCHEMA_VERSION}"
        )
    if contract.get("source") != SEMANTIC_EXCEPTION_SOURCE:
        errors.append(
            "semantic_advisories.disposition_contract.source must name the single governance file"
        )
    if not isinstance(contract.get("group_scope"), str) or not contract[
        "group_scope"
    ].strip():
        errors.append(
            "semantic_advisories.disposition_contract.group_scope must be a non-blank string"
        )
    limitations = semantic.get("limitations")
    if (
        not isinstance(limitations, list)
        or not limitations
        or not all(isinstance(item, str) and item.strip() for item in limitations)
    ):
        errors.append(
            "semantic_advisories.limitations must be a non-empty list of non-blank strings"
        )
    entries = contract.get("entries")
    if not isinstance(entries, list):
        errors.append("semantic_advisories.disposition_contract.entries must be a list")
        entries = []
    configured_count = contract.get("configured_count")
    applied_count = contract.get("applied_count")
    reported_errors = contract.get("errors")
    if not _is_exact_non_negative_int(configured_count):
        errors.append(
            "semantic_advisories.disposition_contract.configured_count must be a non-negative integer"
        )
    elif configured_count != len(entries):
        errors.append(
            "semantic_advisories.disposition_contract.configured_count does not match entries"
        )
    if not _is_exact_non_negative_int(applied_count):
        errors.append(
            "semantic_advisories.disposition_contract.applied_count must be a non-negative integer"
        )
    if not isinstance(reported_errors, list):
        errors.append("semantic_advisories.disposition_contract.errors must be a list")
        reported_errors = []
    elif reported_errors:
        errors.append("semantic_advisories.disposition_contract contains validation errors")
    expected_common_errors, expected_surface_errors = (
        auditor._reference_disposition_error_attribution(
            [str(item) for item in reported_errors],
            entries,
            candidates,
        )
    )
    if contract.get("common_errors") != expected_common_errors:
        errors.append(
            "semantic_advisories.disposition_contract.common_errors does not match attributable errors"
        )
    if contract.get("surface_errors") != expected_surface_errors:
        errors.append(
            "semantic_advisories.disposition_contract.surface_errors does not match attributable errors"
        )
    normalized_entries, matches, recomputed_errors = (
        auditor._validate_reference_semantic_dispositions(
            candidates, entries, evaluated_on, require_applied=True
        )
    )
    errors.extend(
        f"semantic disposition contract: {item}" for item in recomputed_errors
    )
    if normalized_entries != entries:
        errors.append("semantic_advisories.disposition_contract entries are not canonical")
    actual_applied = sum(
        isinstance(candidate, dict) and candidate.get("disposition") is not None
        for candidate in candidates
    )
    if applied_count != actual_applied or applied_count != len(matches):
        errors.append(
            "semantic_advisories.disposition_contract.applied_count does not match candidates"
        )

    counts.update(
        {
            "semantic_raw_candidates": totals["raw"],
            "semantic_detector_downgraded_candidates": totals[
                "detector_downgraded"
            ],
            "semantic_untriaged_candidates": totals["untriaged"],
            "semantic_rewrite_candidates": totals["rewrite"],
            "semantic_resolved_candidates": totals["resolved"],
            "semantic_unresolved_candidates": totals["unresolved"],
            "unconditional_absolute_p0_p1_unresolved_candidates": strict_unresolved[
                "unconditional_absolute_p0_p1_candidates"
            ],
            "fixed_number_unresolved_candidates": strict_unresolved[
                "fixed_number_candidates"
            ],
            "templated_block_unresolved_groups": strict_unresolved[
                "templated_block_groups"
            ],
            "p2_rewrite_advisory_candidates": strict_unresolved[
                "p2_rewrite_advisories"
            ],
            "exact_normalized_duplicate_unresolved_groups": expected_by_finding[
                "exact_normalized_duplicate_block"
            ]["unresolved"],
            "semantic_disposition_configured": (
                configured_count if _is_exact_non_negative_int(configured_count) else 0
            ),
            "semantic_disposition_applied": (
                applied_count if _is_exact_non_negative_int(applied_count) else 0
            ),
            "semantic_disposition_errors": len(reported_errors),
        }
    )
    for finding, prefix in (
        ("exact_normalized_duplicate_block", "exact_duplicate"),
        ("templated_block_candidate", "templated_block"),
    ):
        counts[f"{prefix}_occurrences"] = group_metrics[finding]["occurrences"]
        counts[f"{prefix}_tokens"] = group_metrics[finding]["tokens"]
    return counts, errors


def _surface_validation_contract(reference_content: dict[str, Any]) -> list[str]:
    auditor = _load_auditor()
    reported = reference_content.get("surface_validation")
    if not isinstance(reported, dict):
        return ["reference_content.surface_validation must be a mapping"]
    errors: list[str] = []
    if set(reported) != {"schema_version", "common_errors", "surfaces"}:
        errors.append(
            "reference_content.surface_validation must contain exactly schema_version, common_errors, and surfaces"
        )
    if reported.get("schema_version") != auditor.SURFACE_VALIDATION_SCHEMA_VERSION:
        errors.append(
            "reference_content.surface_validation.schema_version must equal "
            f"{auditor.SURFACE_VALIDATION_SCHEMA_VERSION}"
        )
    common_errors = reported.get("common_errors")
    if (
        not isinstance(common_errors, list)
        or any(not isinstance(item, str) or not item for item in common_errors)
        or common_errors != list(dict.fromkeys(common_errors))
    ):
        errors.append(
            "reference_content.surface_validation.common_errors must be an ordered unique string list"
        )
    surfaces = reported.get("surfaces")
    if not isinstance(surfaces, dict) or set(surfaces) != set(
        auditor.REFERENCE_CONTENT_SURFACES
    ):
        errors.append(
            "reference_content.surface_validation.surfaces must exactly match the declared Reference surfaces"
        )
        surfaces = {}
    expected_fields = {
        "status",
        "indexed_reference_count",
        "existing_reference_count",
        "semantic_candidate_count",
        "semantic_unresolved_count",
        "semantic_fixed_number_unresolved_count",
        "semantic_templated_group_unresolved_count",
        "semantic_absolute_p0_p1_unresolved_count",
        "disposition_configured_count",
        "disposition_applied_count",
        "errors",
    }
    for surface in auditor.REFERENCE_CONTENT_SURFACES:
        row = surfaces.get(surface)
        context = f"reference_content.surface_validation.surfaces.{surface}"
        if not isinstance(row, dict) or set(row) != expected_fields:
            errors.append(f"{context} fields do not match the closed schema")
            continue
        if row.get("status") not in {"pass", "fail"}:
            errors.append(f"{context}.status must be pass or fail")
        for field in expected_fields - {"status", "errors"}:
            if not _is_exact_non_negative_int(row.get(field)):
                errors.append(f"{context}.{field} must be a non-negative integer")
        row_errors = row.get("errors")
        if (
            not isinstance(row_errors, list)
            or any(not isinstance(item, str) or not item for item in row_errors)
            or row_errors != list(dict.fromkeys(row_errors))
        ):
            errors.append(f"{context}.errors must be an ordered unique string list")
    expected = auditor._reference_surface_validation(reference_content)
    if reported != expected:
        errors.append(
            "reference_content.surface_validation does not match canonical source attribution"
        )
    return errors


def _evaluate(
    reference_content: dict[str, Any],
    *,
    strict: bool,
    evaluation_date: date | None = None,
    validate_readability_sources: bool = False,
) -> tuple[dict[str, int], list[str]]:
    references = list(reference_content.get("references") or [])
    existing = [item for item in references if item.get("exists")]
    missing = list(reference_content.get("missing") or [])
    orphans = list(reference_content.get("orphans") or [])
    templates = list(reference_content.get("template_assets") or [])
    advisories = dict(reference_content.get("advisories") or {})
    summary = dict(reference_content.get("summary") or {})
    semantic_counts, semantic_errors = _semantic_contract(
        reference_content,
        evaluation_date=evaluation_date,
    )
    preface_counts, preface_errors = _effective_preface_contract(reference_content)

    missing_h1 = [item for item in existing if item.get("h1_status") == "missing"]
    non_template_multiple = list(advisories.get("non_template_multiple_h1") or [])
    non_template_empty = list(advisories.get("non_template_empty_headings") or [])
    non_template_invalid_decision_sections = list(
        advisories.get("non_template_invalid_decision_section_headings") or []
    )
    template_multiple = [
        item
        for item in existing
        if item.get("kind") == "template" and item.get("h1_status") == "multiple"
    ]
    unindexed_templates = [item for item in templates if not item.get("indexed")]

    missing_reference_type = [
        item for item in existing if not item.get("has_reference_type_preface")
    ]
    missing_load_when = [
        item for item in existing if not item.get("has_load_when_preface")
    ]
    missing_do_not_load_when = [
        item for item in existing if not item.get("has_do_not_load_when_preface")
    ]
    targeted_over = list(advisories.get("targeted_over_60_lines") or [])
    mode_contract_over = list(advisories.get("mode_contract_over_80_lines") or [])
    decision_items_over = list(advisories.get("decision_items_over_15") or [])

    counts = {
        "indexed": len(references),
        "existing": len(existing),
        "physical": int(summary.get("physical_markdown_references") or 0),
        "missing": len(missing),
        "non_template_orphan": len(orphans),
        "template_assets": len(templates),
        "unindexed_template_assets": len(unindexed_templates),
        "missing_h1": len(missing_h1),
        "non_template_multiple_h1": len(non_template_multiple),
        "non_template_empty_heading": len(non_template_empty),
        "non_template_invalid_decision_section_heading": len(
            non_template_invalid_decision_sections
        ),
        "template_multiple_h1": len(template_multiple),
        "missing_reference_type": len(missing_reference_type),
        "missing_load_when": len(missing_load_when),
        "missing_do_not_load_when": len(missing_do_not_load_when),
        "targeted_over_60": len(targeted_over),
        "mode_contract_over_80": len(mode_contract_over),
        "decision_items_over_15": len(decision_items_over),
        **preface_counts,
        **semantic_counts,
    }

    errors: list[str] = [
        *preface_errors,
        *semantic_errors,
        *_surface_validation_contract(reference_content),
    ]
    if validate_readability_sources:
        readability_paths = sorted(
            {
                str(item.get("path"))
                for item in [*existing, *orphans, *templates]
                if isinstance(item, dict)
                and isinstance(item.get("path"), str)
                and item.get("path")
            }
        )
        for relative in readability_paths:
            path = ROOT / relative
            try:
                markdown = path.read_text(encoding="utf-8")
            except OSError as exc:
                errors.append(f"{relative}: cannot read Reference for readability: {exc}")
                continue
            validate_ai_readability(markdown, relative, errors)
    default_gates = (
        ("missing indexed reference(s)", "missing"),
        ("non-template orphan reference(s)", "non_template_orphan"),
        ("indexed reference(s) missing H1", "missing_h1"),
        ("non-template reference(s) with multiple H1", "non_template_multiple_h1"),
        ("non-template reference(s) with empty heading", "non_template_empty_heading"),
        (
            "non-template reference(s) with invalid decision-section heading",
            "non_template_invalid_decision_section_heading",
        ),
        ("effective preface contract error(s)", "effective_preface_contract_errors"),
        ("effective preface conflict(s)", "effective_preface_conflicts"),
        ("invalid effective preface declaration(s)", "effective_preface_invalid"),
    )
    strict_gates = (
        ("indexed reference(s) missing effective reference type", "missing_effective_reference_type"),
        ("indexed reference(s) missing effective load condition", "missing_effective_load_when"),
        ("indexed reference(s) missing effective do-not-load condition", "missing_effective_do_not_load_when"),
        ("indexed reference(s) missing effective required consumer", "missing_effective_required_by"),
        ("indexed reference(s) missing effective required output", "missing_effective_required_output"),
        (f"targeted reference(s) over {TARGETED_LINE_LIMIT} lines", "targeted_over_60"),
        (
            f"mode-contract reference(s) over {MODE_CONTRACT_LINE_LIMIT} lines",
            "mode_contract_over_80",
        ),
        (
            f"reference(s) with a Gate/Checklist/Decision section over {DECISION_ITEM_LIMIT} items",
            "decision_items_over_15",
        ),
        (
            "unresolved fixed-number semantic candidate(s)",
            "fixed_number_unresolved_candidates",
        ),
        (
            "unresolved templated-block semantic group(s)",
            "templated_block_unresolved_groups",
        ),
        (
            "unresolved P0/P1 unconditional-absolute semantic candidate(s)",
            "unconditional_absolute_p0_p1_unresolved_candidates",
        ),
    )
    for label, key in default_gates + (strict_gates if strict else ()):
        if counts[key]:
            errors.append(f"{label}: {counts[key]}")
    return counts, errors


def _format_counts(counts: dict[str, int], *, strict: bool) -> list[str]:
    mode = "strict" if strict else "default"
    return [
        f"validate-reference-content: mode={mode}; evidence=fresh-source",
        (
            "validate-reference-content: inventory "
            f"indexed={counts['indexed']} existing={counts['existing']} "
            f"physical={counts['physical']} missing={counts['missing']} "
            f"non_template_orphan={counts['non_template_orphan']}"
        ),
        (
            "validate-reference-content: structure "
            f"missing_h1={counts['missing_h1']} "
            f"non_template_multiple_h1={counts['non_template_multiple_h1']} "
            f"non_template_empty_heading={counts['non_template_empty_heading']}"
        ),
        (
            "validate-reference-content: allowed-template-facts "
            f"template_assets={counts['template_assets']} "
            f"template_multiple_h1={counts['template_multiple_h1']} "
            f"unindexed_template_assets={counts['unindexed_template_assets']}"
        ),
        (
            "validate-reference-content: local-prefaces "
            f"missing_reference_type={counts['missing_reference_type']} "
            f"missing_load_when={counts['missing_load_when']} "
            f"missing_do_not_load_when={counts['missing_do_not_load_when']}"
        ),
        (
            "validate-reference-content: effective-prefaces "
            f"reference_types={counts['effective_reference_types']} "
            f"load_when={counts['effective_load_when']} "
            f"do_not_load_when={counts['effective_do_not_load_when']} "
            f"required_by={counts['effective_required_by']} "
            f"required_output={counts['effective_required_output']} "
            f"missing_reference_type={counts['missing_effective_reference_type']} "
            f"missing_load_when={counts['missing_effective_load_when']} "
            f"missing_do_not_load_when={counts['missing_effective_do_not_load_when']} "
            f"missing_required_by={counts['missing_effective_required_by']} "
            f"missing_required_output={counts['missing_effective_required_output']}"
        ),
        (
            "validate-reference-content: preface-contract "
            f"schema={PREFACE_CONTRACT_SCHEMA_VERSION} "
            f"errors={counts['effective_preface_contract_errors']} "
            f"conflicts={counts['effective_preface_conflicts']} "
            f"invalid={counts['effective_preface_invalid']}"
        ),
        (
            "validate-reference-content: size-advisories "
            f"targeted_over_{TARGETED_LINE_LIMIT}={counts['targeted_over_60']} "
            f"mode_contract_over_{MODE_CONTRACT_LINE_LIMIT}={counts['mode_contract_over_80']} "
            f"decision_items_over_{DECISION_ITEM_LIMIT}={counts['decision_items_over_15']}"
        ),
        (
            "validate-reference-content: semantic-governance "
            f"raw={counts['semantic_raw_candidates']} "
            f"detector_downgraded={counts['semantic_detector_downgraded_candidates']} "
            f"untriaged={counts['semantic_untriaged_candidates']} "
            f"rewrite={counts['semantic_rewrite_candidates']} "
            f"resolved={counts['semantic_resolved_candidates']} "
            f"unresolved={counts['semantic_unresolved_candidates']} "
            f"absolute_p0_p1_unresolved={counts['unconditional_absolute_p0_p1_unresolved_candidates']} "
            f"fixed_number_unresolved={counts['fixed_number_unresolved_candidates']} "
            f"templated_group_unresolved={counts['templated_block_unresolved_groups']} "
            f"p2_rewrite_advisory={counts['p2_rewrite_advisory_candidates']} "
            f"exact_duplicate_unresolved_groups={counts['exact_normalized_duplicate_unresolved_groups']} "
            f"duplicate_occurrences={counts['exact_duplicate_occurrences'] + counts['templated_block_occurrences']} "
            f"duplicate_tokens={counts['exact_duplicate_tokens'] + counts['templated_block_tokens']} "
            f"dispositions_configured={counts['semantic_disposition_configured']} "
            f"dispositions_applied={counts['semantic_disposition_applied']} "
            f"disposition_errors={counts['semantic_disposition_errors']}"
        ),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote effective-preface, size, and decision-item advisories to failures.",
    )
    args = parser.parse_args(argv)

    effective_evaluation_date = _load_auditor()._effective_evaluation_date()
    reference_content = _fresh_reference_content(
        evaluation_date=effective_evaluation_date
    )
    counts, errors = _evaluate(
        reference_content,
        strict=args.strict,
        evaluation_date=effective_evaluation_date,
        validate_readability_sources=True,
    )
    for line in _format_counts(counts, strict=args.strict):
        print(line)
    if errors:
        sys.stdout.flush()
        for error in errors:
            print(f"validate-reference-content: ERROR: {error}", file=sys.stderr)
        return 1
    print("validate-reference-content: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
