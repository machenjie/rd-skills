#!/usr/bin/env python3
"""Pure Professional Completeness binding, carry, and capsule helpers.

This module intentionally has no CLI and does not import ``expert_panel_review``.
The panel module owns artifact schemas and validation; this module owns only
canonical projections that future incremental review can reuse without creating
an import cycle or adding more stateful behavior to the panel module.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

import expert_panel_contracts as panel_contracts

ACCEPTED_PROFESSIONAL_DISPOSITION = (
    panel_contracts.PROFESSIONAL_ACCEPTED_DISPOSITION
)
PROFESSIONAL_CARRY_CONTRACT = copy.deepcopy(
    panel_contracts.PROFESSIONAL_CARRY_CONTRACT
)
PROFESSIONAL_CAPSULE_CONTRACT = copy.deepcopy(
    panel_contracts.PROFESSIONAL_REVIEW_CAPSULE_CONTRACT
)
PROFESSIONAL_DISCOVERY_CAPSULE_CONTRACT = copy.deepcopy(
    panel_contracts.PROFESSIONAL_DISCOVERY_CAPSULE_CONTRACT
)

_MATERIAL_RECORD_FIELDS = set(
    panel_contracts.PROFESSIONAL_MATERIAL_RECORD_FIELDS
)
_ADJACENCY_REVIEW_BINDING_FIELDS = set(
    panel_contracts.PROFESSIONAL_ADJACENCY_REVIEW_BINDING_FIELDS
)
_SEMANTIC_RESPONSIBILITY_FIELDS = set(
    panel_contracts.PROFESSIONAL_SEMANTIC_RESPONSIBILITY_FIELDS
)
_SEMANTIC_RESPONSIBILITY_REQUIRED_LIST_FIELDS = set(
    panel_contracts.PROFESSIONAL_SEMANTIC_RESPONSIBILITY_REQUIRED_LIST_FIELDS
)
_SEMANTIC_RESPONSIBILITY_OPTIONAL_LIST_FIELDS = set(
    panel_contracts.PROFESSIONAL_SEMANTIC_RESPONSIBILITY_OPTIONAL_LIST_FIELDS
)
_SEMANTIC_FACT_PROJECTION_VERSION = (
    panel_contracts.PROFESSIONAL_SEMANTIC_FACT_PROJECTION_VERSION
)
_SEMANTIC_FACT_FIELDS = set(
    panel_contracts.PROFESSIONAL_SEMANTIC_FACT_FIELDS
)
_SEMANTIC_ARGUMENT_ROLE_FIELDS = set(
    panel_contracts.PROFESSIONAL_SEMANTIC_ARGUMENT_ROLE_FIELDS
)
_SEMANTIC_ARGUMENT_RELATIONS = set(
    panel_contracts.PROFESSIONAL_SEMANTIC_ARGUMENT_RELATIONS
)
_SEMANTIC_ARGUMENT_ATTACHMENTS = set(
    panel_contracts.PROFESSIONAL_SEMANTIC_ARGUMENT_ATTACHMENTS
)
_SEMANTIC_SECTION_ALIASES = copy.deepcopy(
    panel_contracts.PROFESSIONAL_SEMANTIC_SECTION_ALIASES
)
_SEMANTIC_EXCLUDED_SECTION_ALIASES = tuple(
    panel_contracts.PROFESSIONAL_SEMANTIC_EXCLUDED_SECTION_ALIASES
)
_SEMANTIC_SECTION_FACTS = copy.deepcopy(
    panel_contracts.PROFESSIONAL_SEMANTIC_SECTION_FACTS
)
_SEMANTIC_REGISTRY_FACTS = copy.deepcopy(
    panel_contracts.PROFESSIONAL_SEMANTIC_REGISTRY_FACTS
)
_SEMANTIC_ACTION_ALIASES = copy.deepcopy(
    panel_contracts.PROFESSIONAL_SEMANTIC_ACTION_ALIASES
)
_SEMANTIC_OBJECT_CONDITION_ALIASES = copy.deepcopy(
    panel_contracts.PROFESSIONAL_SEMANTIC_OBJECT_CONDITION_ALIASES
)
_SEMANTIC_TERM_ALIASES = copy.deepcopy(
    panel_contracts.PROFESSIONAL_SEMANTIC_TERM_ALIASES
)
_SEMANTIC_STOP_TOKENS = set(
    panel_contracts.PROFESSIONAL_SEMANTIC_STOP_TOKENS
)
_SEMANTIC_MODALITY_ALIASES = copy.deepcopy(
    panel_contracts.PROFESSIONAL_SEMANTIC_MODALITY_ALIASES
)
_SEMANTIC_NEGATION_ALIASES = tuple(
    panel_contracts.PROFESSIONAL_SEMANTIC_NEGATION_ALIASES
)
_SEMANTIC_PREDICATE_CONNECTORS = set(
    panel_contracts.PROFESSIONAL_SEMANTIC_PREDICATE_CONNECTORS
)
_SEMANTIC_CONDITION_CONCEPTS = set(
    panel_contracts.PROFESSIONAL_SEMANTIC_CONDITION_CONCEPTS
)
_SEMANTIC_PREDICATE_LEAD_TOKENS = set(
    panel_contracts.PROFESSIONAL_SEMANTIC_PREDICATE_LEAD_TOKENS
)
_SEMANTIC_UNIT_KINDS = set(
    panel_contracts.PROFESSIONAL_SEMANTIC_UNIT_KINDS
)
_SEMANTIC_FINITE_RELATION_ALIASES = copy.deepcopy(
    panel_contracts.PROFESSIONAL_SEMANTIC_FINITE_RELATION_ALIASES
)
_SEMANTIC_RELATIVE_CONDITION_TOKENS = set(
    panel_contracts.PROFESSIONAL_SEMANTIC_RELATIVE_CONDITION_TOKENS
)
_SEMANTIC_GRAMMATICAL_CONDITION_BOUNDARIES = tuple(
    panel_contracts.PROFESSIONAL_SEMANTIC_GRAMMATICAL_CONDITION_BOUNDARIES
)
_FRESH_ADJACENCY_CONTEXT_FIELDS = {
    "algorithm",
    "declared_skills",
    "required_candidate_selection",
    "required_candidates",
    "full_catalog_count",
    "full_catalog_ranking",
}
_TARGET_BINDING_FIELDS = set(
    panel_contracts.PROFESSIONAL_TARGET_BINDING_FIELDS
)
_SNAPSHOT_TARGET_FIELDS = set(
    panel_contracts.PROFESSIONAL_SNAPSHOT_TARGET_FIELDS
)
_DECISION_DEPENDENCY_FIELDS = set(
    panel_contracts.PROFESSIONAL_DECISION_DEPENDENCY_FIELDS
)
_CAPSULE_FIELDS = {
    "projection_contract",
    "assigned_fresh_target_ids",
    "material_catalog",
    "targets",
}
_CAPSULE_TARGET_FIELDS = {
    "skill_id",
    "review_unit_binding",
    "adjacency",
    "candidate_material_manifest",
}
_CAPSULE_MANIFEST_FIELDS = {
    "skill_id",
    "review_origin",
    "discovery_reason",
    "material_fingerprint",
}
_DISCOVERY_CAPSULE_FIELDS = {
    "projection_contract",
    "assigned_fresh_target_ids",
    "material_catalog",
    "boundary_catalog",
    "targets",
}
_DISCOVERY_CAPSULE_TARGET_FIELDS = {
    "skill_id",
    "review_unit_binding",
    "adjacency",
    "required_candidate_material_manifest",
}
_DISCOVERY_BOUNDARY_FIELDS = {
    "skill_id",
    "layer",
    "responsibility_contract",
    "required_expertise_tags",
    "material_fingerprint",
}
_REVIEWER_ADDED_REQUEST_FIELDS = {
    "skill_id",
    "discovery_reason",
    "ranking_evidence",
    "material_fingerprint",
}
_PROFESSIONAL_EVIDENCE_METRIC_KEYS = {
    "target_vote_count",
    "required_adjacency_candidate_count",
    "criterion_result_count",
    "criterion_anchor_binding_count",
    "criterion_assertion_count",
    "evidence_anchor_count",
    "examined_failure_mode_count",
    "examined_omission_candidate_count",
    "examined_adjacency_count",
    "examined_required_adjacency_count",
    "reviewer_added_adjacency_count",
    "proof_limit_count",
    "qualification_claim_count",
}


class ProfessionalCarryForwardError(ValueError):
    """Raised when an internal carry or capsule projection is not canonical."""


class _HistoricalContentBindingCatalog(dict[str, dict[str, Any]]):
    """Invocation-local adapter for immutable pre-semantic review artifacts."""


class ProfessionalReviewerAddedRequiredRelationshipDrift(
    ProfessionalCarryForwardError
):
    """Reviewer-added candidates became required after all authority checks."""

    def __init__(self, overlaps: Mapping[str, Sequence[str]]) -> None:
        canonical = tuple(
            (
                skill_id,
                tuple(sorted(set(candidate_ids))),
            )
            for skill_id, candidate_ids in sorted(overlaps.items())
            if candidate_ids
        )
        if not canonical:
            raise ValueError("Professional relationship drift must be non-empty")
        self.overlaps = canonical
        rendered = "; ".join(
            f"{skill_id}={','.join(candidate_ids)}"
            for skill_id, candidate_ids in canonical
        )
        super().__init__(
            "Professional reviewer-added candidates overlap current required "
            f"relationships: {rendered}"
        )


def canonical_json_bytes(value: object) -> bytes:
    """Return deterministic UTF-8 JSON bytes without claiming artifact status."""

    try:
        rendered = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise ProfessionalCarryForwardError(
            "value is not canonical-JSON serializable"
        ) from exc
    return rendered.encode("utf-8")


def canonical_json_sha256(value: object) -> str:
    """Hash the canonical bytes used by every helper in this module."""

    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _is_sha256(value: object) -> bool:
    return bool(
        isinstance(value, str)
        and re.fullmatch(r"[0-9a-f]{64}", value)
    )


def _require_sha256(value: object, *, label: str) -> str:
    if not _is_sha256(value):
        raise ProfessionalCarryForwardError(
            f"{label} must be a lowercase SHA-256 digest"
        )
    return str(value)


def _require_skill_id(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProfessionalCarryForwardError(f"{label} must be non-empty")
    return value


def _sorted_unique_strings(value: object, *, label: str) -> list[str]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise ProfessionalCarryForwardError(f"{label} must be a string array")
    if value != sorted(set(value)):
        raise ProfessionalCarryForwardError(
            f"{label} must be sorted and unique"
        )
    return list(value)


def _is_canonical_repository_path(value: object) -> bool:
    return bool(
        isinstance(value, str)
        and value
        and "\\" not in value
        and not PurePosixPath(value).is_absolute()
        and PurePosixPath(value).as_posix() == value
        and all(part not in {"", ".", ".."} for part in value.split("/"))
    )


def _canonical_material_record(value: object, *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != _MATERIAL_RECORD_FIELDS:
        raise ProfessionalCarryForwardError(
            f"{label} must be one complete review-material record"
        )
    path = value.get("path")
    content = value.get("content")
    line_count = value.get("line_count")
    digest = _require_sha256(value.get("sha256"), label=f"{label}.sha256")
    if not _is_canonical_repository_path(path):
        raise ProfessionalCarryForwardError(
            f"{label}.path must be repository-relative"
        )
    if not isinstance(content, str):
        raise ProfessionalCarryForwardError(f"{label}.content must be text")
    if type(line_count) is not int or line_count != len(content.splitlines()):
        raise ProfessionalCarryForwardError(
            f"{label}.line_count must match content"
        )
    if hashlib.sha256(content.encode("utf-8")).hexdigest() != digest:
        raise ProfessionalCarryForwardError(
            f"{label}.sha256 must bind content"
        )
    return copy.deepcopy(value)


def professional_materials_by_skill(
    targets: Sequence[dict[str, Any]],
) -> dict[str, dict[str, dict[str, Any]]]:
    """Index target-owned root and Reference records for review validation.

    This intentionally preserves the legacy panel helper's projection: it does
    not copy or add fields, so existing ballot validation behavior and packet
    serialization remain unchanged.
    """

    return {
        target["skill_id"]: {
            target["root"]["path"]: target["root"],
            **{
                reference["path"]: reference
                for reference in target["indexed_references"]
            },
        }
        for target in targets
    }


def professional_own_material_binding(
    target: Mapping[str, Any],
) -> dict[str, Any]:
    """Project exactly the target's root and indexed Reference material."""

    return _canonical_own_material_binding(
        {
            "root": target.get("root"),
            "indexed_references": target.get("indexed_references"),
        },
        label=str(target.get("skill_id", "target")),
    )


def _canonical_own_material_binding(
    value: object, *, label: str
) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != {
        "root",
        "indexed_references",
    }:
        raise ProfessionalCarryForwardError(
            f"{label} own material fields are not canonical"
        )
    root = _canonical_material_record(value.get("root"), label=f"{label}.root")
    references_raw = value.get("indexed_references")
    if not isinstance(references_raw, list):
        raise ProfessionalCarryForwardError(
            "target.indexed_references must be an array"
        )
    references = [
        _canonical_material_record(
            reference,
            label=f"{label}.indexed_references[{index}]",
        )
        for index, reference in enumerate(references_raw)
    ]
    reference_paths = [item["path"] for item in references]
    if reference_paths != sorted(set(reference_paths)):
        raise ProfessionalCarryForwardError(
            "target indexed References must be path-sorted and unique"
        )
    if root["path"] in set(reference_paths):
        raise ProfessionalCarryForwardError(
            "target root path must not duplicate an indexed Reference path"
        )
    return {"root": root, "indexed_references": references}


def professional_registry_responsibility_binding(
    target: Mapping[str, Any],
) -> dict[str, Any]:
    """Project the Registry path and embedded responsibility contract."""

    registry = target.get("registry")
    if not isinstance(registry, dict) or set(registry) not in (
        {"path", "responsibility_contract"},
        {"path", "entry_fingerprint", "responsibility_contract"},
    ):
        raise ProfessionalCarryForwardError(
            "target.registry must contain the canonical Registry binding"
        )
    if not _is_canonical_repository_path(registry.get("path")):
        raise ProfessionalCarryForwardError(
            "target.registry.path must be non-empty"
        )
    if not isinstance(registry.get("responsibility_contract"), dict):
        raise ProfessionalCarryForwardError(
            "target.registry.responsibility_contract must be an object"
        )
    return {
        "path": registry["path"],
        "responsibility_contract": copy.deepcopy(
            registry["responsibility_contract"]
        ),
    }


def professional_required_expertise_binding(
    target: Mapping[str, Any],
) -> list[str]:
    """Project the exact closed expertise requirement for one target."""

    return _sorted_unique_strings(
        target.get("required_expertise_tags"),
        label="target.required_expertise_tags",
    )


def _normalized_semantic_text(value: object, *, label: str) -> str:
    """Normalize presentation syntax while preserving lexical authority."""

    if not isinstance(value, str) or not value.strip():
        raise ProfessionalCarryForwardError(f"{label} must be non-empty text")
    text = unicodedata.normalize("NFKC", value).casefold()
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
    text = re.sub(r"[`*_~]+", "", text)
    text = re.sub(r"[^\w]+", " ", text, flags=re.UNICODE)
    normalized = " ".join(text.split())
    if not normalized:
        raise ProfessionalCarryForwardError(
            f"{label} must contain semantic text"
        )
    return normalized


def _normalized_semantic_list(
    value: object, *, label: str, allow_empty: bool
) -> list[str]:
    if not isinstance(value, list):
        raise ProfessionalCarryForwardError(f"{label} must be a string array")
    normalized = [
        _normalized_semantic_text(item, label=f"{label}[{index}]")
        for index, item in enumerate(value)
    ]
    if not allow_empty and not normalized:
        raise ProfessionalCarryForwardError(f"{label} must be non-empty")
    return sorted(set(normalized))


def professional_semantic_responsibility_binding(
    target: Mapping[str, Any],
) -> dict[str, Any]:
    """Project only structured responsibility authority used for rereview."""

    registry = target.get("registry")
    responsibility = (
        registry.get("responsibility_contract")
        if isinstance(registry, Mapping)
        else None
    )
    if not isinstance(responsibility, Mapping):
        raise ProfessionalCarryForwardError(
            "target responsibility contract must be an object"
        )
    missing = sorted(_SEMANTIC_RESPONSIBILITY_FIELDS - set(responsibility))
    if missing:
        raise ProfessionalCarryForwardError(
            "target responsibility contract lacks semantic authority: "
            + ", ".join(missing)
        )
    projected: dict[str, Any] = {}
    for field in sorted(_SEMANTIC_RESPONSIBILITY_REQUIRED_LIST_FIELDS):
        projected[field] = _normalized_semantic_list(
            responsibility[field],
            label=f"target responsibility {field}",
            allow_empty=False,
        )
    for field in sorted(_SEMANTIC_RESPONSIBILITY_OPTIONAL_LIST_FIELDS):
        projected[field] = _normalized_semantic_list(
            responsibility[field],
            label=f"target responsibility {field}",
            allow_empty=True,
        )
    for field in ("group", "content_class", "delivery_scope"):
        value = responsibility[field]
        projected[field] = (
            None
            if value is None
            else _normalized_semantic_text(
                value, label=f"target responsibility {field}"
            )
        )
    task_routable = responsibility["task_routable"]
    if task_routable is not None and type(task_routable) is not bool:
        raise ProfessionalCarryForwardError(
            "target responsibility task_routable must be boolean or null"
        )
    projected["task_routable"] = task_routable
    if set(projected) != _SEMANTIC_RESPONSIBILITY_FIELDS:
        raise ProfessionalCarryForwardError(
            "target semantic responsibility projection is incomplete"
        )
    return projected


def _semantic_tokenize(value: str) -> list[str]:
    text = unicodedata.normalize("NFKC", value).casefold()
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r" \1 ", text)
    text = re.sub(r"<https?://[^ >]+>", " ", text)
    text = text.replace("mustn't", "must not")
    text = text.replace("shalln't", "shall not")
    text = text.replace("can't", "cannot")
    text = re.sub(r"[`*_~]", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    tokens = text.split()
    for alias, canonical in sorted(
        _SEMANTIC_TERM_ALIASES.items(),
        key=lambda item: len(item[0].split()),
        reverse=True,
    ):
        alias_tokens = alias.split()
        replacement = canonical.split()
        position = 0
        while position <= len(tokens) - len(alias_tokens):
            if tokens[position : position + len(alias_tokens)] == alias_tokens:
                tokens[position : position + len(alias_tokens)] = replacement
                position += len(replacement)
            else:
                position += 1
    return tokens


def _semantic_lexeme_forms(token: str) -> set[str]:
    forms = {token}
    if token.endswith("ies") and len(token) > 3:
        forms.add(token[:-3] + "y")
    if token.endswith("ing") and len(token) > 4:
        forms.update({token[:-3], token[:-3] + "e"})
    if token.endswith("ed") and len(token) > 3:
        forms.update({token[:-2], token[:-2] + "e"})
    if token.endswith("es") and len(token) > 3:
        forms.update({token[:-2], token[:-1]})
    elif token.endswith("s") and len(token) > 2:
        forms.add(token[:-1])
    return forms


@lru_cache(maxsize=None)
def _semantic_alias_index(
    namespace: str,
) -> tuple[dict[str, tuple[str, ...]], tuple[tuple[tuple[str, ...], str], ...]]:
    aliases = {
        "action": _SEMANTIC_ACTION_ALIASES,
        "modality": _SEMANTIC_MODALITY_ALIASES,
        "object-condition": _SEMANTIC_OBJECT_CONDITION_ALIASES,
    }.get(namespace)
    if aliases is None:
        raise ProfessionalCarryForwardError(
            f"unknown Professional semantic alias namespace: {namespace}"
        )
    singles: dict[str, set[str]] = {}
    phrases: list[tuple[tuple[str, ...], str]] = []
    for concept, values in aliases.items():
        for alias in values:
            alias_tokens = tuple(_semantic_tokenize(alias))
            if not alias_tokens:
                raise ProfessionalCarryForwardError(
                    "Professional semantic alias must contain tokens"
                )
            if len(alias_tokens) == 1:
                singles.setdefault(alias_tokens[0], set()).add(concept)
            else:
                phrases.append((alias_tokens, concept))
    return (
        {
            alias: tuple(sorted(concepts))
            for alias, concepts in singles.items()
        },
        tuple(sorted(phrases)),
    )


def _semantic_alias_matches(
    tokens: Sequence[str], namespace: str
) -> tuple[set[str], set[int]]:
    singles, phrases = _semantic_alias_index(namespace)
    concepts: set[str] = set()
    covered: set[int] = set()
    for index, token in enumerate(tokens):
        for form in _semantic_lexeme_forms(token):
            matched = singles.get(form, ())
            if matched:
                concepts.update(matched)
                covered.add(index)
    for alias_tokens, concept in phrases:
        width = len(alias_tokens)
        for start in range(0, len(tokens) - width + 1):
            if tuple(tokens[start : start + width]) == alias_tokens:
                concepts.add(concept)
                covered.update(range(start, start + width))
    return concepts, covered


def _semantic_phrase_present(tokens: Sequence[str], phrase: str) -> bool:
    phrase_tokens = _semantic_tokenize(phrase)
    for start in range(0, len(tokens) - len(phrase_tokens) + 1):
        candidate = tokens[start : start + len(phrase_tokens)]
        if candidate == phrase_tokens:
            return True
        if (
            candidate[:-1] == phrase_tokens[:-1]
            and phrase_tokens[-1] in _semantic_lexeme_forms(candidate[-1])
        ):
            return True
    return False


def _semantic_section_kind(title: str | None) -> str | None:
    if title is None:
        return None
    tokens = _semantic_tokenize(title)
    normalized = " ".join(tokens)
    if any(
        _semantic_phrase_present(tokens, alias)
        for alias in _SEMANTIC_EXCLUDED_SECTION_ALIASES
    ):
        return "excluded"
    priority = (
        "source-citation",
        "anti-trigger",
        "trigger",
        "required-input",
        "required-output",
        "responsibility",
        "failure-constraint",
        "verification",
        "adjacency-routing",
        "decision-rules",
    )
    for section_kind in priority:
        aliases = _SEMANTIC_SECTION_ALIASES[section_kind]
        if any(
            _semantic_phrase_present(tokens, alias)
            for alias in aliases
        ):
            return section_kind
    return "general-guidance" if normalized else None


def _professional_markdown_semantic_units(
    markdown: str,
) -> list[dict[str, Any]]:
    """Return logical Markdown units without path, position, or presentation."""

    lines = markdown.splitlines()
    units: list[dict[str, Any]] = []
    current_heading: str | None = None
    current_parts: list[str] = []
    current_kind: str | None = None
    table_headers: list[str] | None = None
    in_frontmatter = bool(lines and lines[0].strip() == "---")
    in_fence = False
    fence_marker: str | None = None
    in_comment = False

    def append_unit(kind: str, text: str) -> None:
        if kind not in _SEMANTIC_UNIT_KINDS:
            raise ProfessionalCarryForwardError(
                f"unknown Professional semantic unit kind: {kind}"
            )
        label_match = re.match(
            r"^\s*(?:\*\*)?([^:*][^:]{0,79}):(?:\*\*)?\s+(.+)$",
            text,
        )
        if label_match:
            units.append(
                {
                    "heading": current_heading,
                    "unit_kind": "labeled-field",
                    "label": label_match.group(1).strip(),
                    "text": label_match.group(2).strip(),
                }
            )
            return
        units.append(
            {
                "heading": current_heading,
                "unit_kind": kind,
                "text": text,
            }
        )

    def flush() -> None:
        nonlocal current_parts, current_kind
        text = " ".join(part.strip() for part in current_parts if part.strip())
        if text:
            append_unit(current_kind or "paragraph", text)
        current_parts = []
        current_kind = None

    index = 1 if in_frontmatter else 0
    while index < len(lines):
        raw_line = lines[index]
        stripped = raw_line.strip()
        if in_frontmatter:
            if stripped == "---":
                in_frontmatter = False
            index += 1
            continue
        fence_match = re.match(r"^(```+|~~~+)", stripped)
        if fence_match:
            flush()
            marker = fence_match.group(1)[:3]
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif fence_marker == marker:
                in_fence = False
                fence_marker = None
            index += 1
            continue
        if in_fence:
            index += 1
            continue
        if in_comment:
            if "-->" in raw_line:
                in_comment = False
            index += 1
            continue
        if "<!--" in raw_line:
            before, _marker, after = raw_line.partition("<!--")
            raw_line = before
            stripped = raw_line.strip()
            if "-->" not in after:
                in_comment = True
        heading = re.match(r"^#{2,6}\s+(.+?)\s*$", stripped)
        if heading:
            flush()
            current_heading = heading.group(1)
            table_headers = None
            index += 1
            continue
        if re.match(r"^#(?:\s+|$)", stripped):
            flush()
            index += 1
            continue
        if not stripped:
            flush()
            index += 1
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            flush()
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            next_line = lines[index + 1].strip() if index + 1 < len(lines) else ""
            if re.fullmatch(r"\|?(?:\s*:?-+:?\s*\|)+\s*", next_line):
                table_headers = cells
                index += 2
                continue
            if re.fullmatch(r"\|?(?:\s*:?-+:?\s*\|)+\s*", stripped):
                index += 1
                continue
            if table_headers and len(table_headers) == len(cells):
                fields = [
                    {"label": header, "text": cell}
                    for header, cell in zip(table_headers, cells)
                    if cell
                ]
            else:
                fields = [
                    {"label": f"column-{position}", "text": cell}
                    for position, cell in enumerate(cells, start=1)
                    if cell
                ]
            if fields:
                units.append(
                    {
                        "heading": current_heading,
                        "unit_kind": "table-row",
                        "fields": fields,
                        "text": " ".join(
                            f"{field['label']} {field['text']}"
                            for field in fields
                        ),
                    }
                )
            index += 1
            continue
        list_match = re.match(r"^\s*([-*+]|\d+[.)])\s+(.+)$", raw_line)
        if list_match:
            flush()
            current_kind = (
                "ordered-step"
                if list_match.group(1)[0].isdigit()
                else "list-item"
            )
            current_parts = [list_match.group(2)]
            index += 1
            continue
        if current_kind in {"list-item", "ordered-step"} and raw_line[:1].isspace():
            current_parts.append(stripped)
        else:
            if current_kind != "paragraph":
                flush()
                current_kind = "paragraph"
            current_parts.append(stripped)
        index += 1
    flush()
    return units


def _semantic_clause_slices(text: str) -> list[str]:
    return [
        clause.strip()
        for clause in re.split(r"(?<=[.!?])\s+", text)
        if clause.strip()
    ]


def _semantic_alias_spans(
    tokens: Sequence[str], namespace: str
) -> list[tuple[int, int, str]]:
    """Return non-overlapping closed alias spans with their concepts."""

    singles, phrases = _semantic_alias_index(namespace)
    matches: set[tuple[int, int, str]] = set()
    for index, token in enumerate(tokens):
        for form in _semantic_lexeme_forms(token):
            for concept in singles.get(form, ()):
                matches.add((index, index + 1, concept))
    for alias_tokens, concept in phrases:
        width = len(alias_tokens)
        for start in range(0, len(tokens) - width + 1):
            if tuple(tokens[start : start + width]) == alias_tokens:
                matches.add((start, start + width, concept))

    selected: list[tuple[int, int, str]] = []
    for start, end, concept in sorted(
        matches, key=lambda row: (row[0], -(row[1] - row[0]), row[2])
    ):
        overlaps = [
            current
            for current in selected
            if start < current[1] and current[0] < end
        ]
        if not overlaps:
            selected.append((start, end, concept))
            continue
        if all(current[2] == concept for current in overlaps):
            continue
        if namespace == "action":
            raise ProfessionalCarryForwardError(
                "material semantic clause is ambiguous: overlapping closed "
                f"{namespace} aliases"
            )
        selected.append((start, end, concept))
    return sorted(selected)


def _semantic_negation_indexes(tokens: Sequence[str]) -> set[int]:
    indexes: set[int] = set()
    for alias in _SEMANTIC_NEGATION_ALIASES:
        alias_tokens = _semantic_tokenize(alias)
        for start in range(0, len(tokens) - len(alias_tokens) + 1):
            if list(tokens[start : start + len(alias_tokens)]) == alias_tokens:
                indexes.update(range(start, start + len(alias_tokens)))
    return indexes


def _semantic_finite_relation_spans(
    tokens: Sequence[str],
) -> list[tuple[int, int, str]]:
    spans = []
    for concept, aliases in _SEMANTIC_FINITE_RELATION_ALIASES.items():
        for alias in aliases:
            alias_tokens = _semantic_tokenize(alias)
            for start in range(0, len(tokens) - len(alias_tokens) + 1):
                if list(tokens[start : start + len(alias_tokens)]) == alias_tokens:
                    spans.append((start, start + len(alias_tokens), concept))
    return sorted(set(spans))


def _semantic_action_candidates(
    tokens: Sequence[str],
) -> list[tuple[int, int, str]]:
    condition_spans = [
        (start, end)
        for start, end, concept in _semantic_alias_spans(
            tokens, "object-condition"
        )
        if concept in _SEMANTIC_CONDITION_CONCEPTS
    ]
    actions = [
        action
        for action in _semantic_alias_spans(tokens, "action")
        if not any(
            action[0] < end and start < action[1]
            for start, end in condition_spans
        )
        and not (
            action[2] == "execute"
            and list(tokens[action[0] : action[1]]) == ["do"]
            and action[1] < len(tokens)
            and tokens[action[1]] == "not"
        )
    ]
    by_span = {(start, end): concept for start, end, concept in actions}
    for start, end, concept in _semantic_finite_relation_spans(tokens):
        by_span.setdefault((start, end), concept)
    return sorted((start, end, concept) for (start, end), concept in by_span.items())


def _semantic_first_content_index(tokens: Sequence[str], start: int = 0) -> int:
    index = start
    while index < len(tokens) and tokens[index] in _SEMANTIC_PREDICATE_LEAD_TOKENS:
        index += 1
    return index


def _semantic_action_at(
    actions: Sequence[tuple[int, int, str]], index: int
) -> tuple[int, int, str] | None:
    return next((action for action in actions if action[0] == index), None)


def _semantic_action_surface_is_exact(
    tokens: Sequence[str], action: tuple[int, int, str]
) -> bool:
    surface = tuple(tokens[action[0] : action[1]])
    aliases = _SEMANTIC_ACTION_ALIASES.get(action[2], ())
    return any(
        tuple(_semantic_tokenize(alias)) == surface for alias in aliases
    ) or any(
        tuple(_semantic_tokenize(alias)) == surface
        for alias in _SEMANTIC_FINITE_RELATION_ALIASES.get(action[2], ())
    )


def _semantic_action_surface_is_exact_closed_alias(
    tokens: Sequence[str], action: tuple[int, int, str]
) -> bool:
    surface = tuple(tokens[action[0] : action[1]])
    return any(
        tuple(_semantic_tokenize(alias)) == surface
        for alias in _SEMANTIC_ACTION_ALIASES.get(action[2], ())
    )


def _semantic_forced_head(
    tokens: Sequence[str],
    actions: Sequence[tuple[int, int, str]],
    *,
    start: int,
    allow_lexical: bool,
) -> tuple[int, int, str] | None:
    index = _semantic_first_content_index(tokens, start)
    if index >= len(tokens):
        return None
    action = _semantic_action_at(actions, index)
    if action is not None:
        return action
    if allow_lexical:
        return (index, index + 1, f"lexical:{tokens[index]}")
    return None


def _semantic_first_predicate(
    tokens: Sequence[str],
    actions: Sequence[tuple[int, int, str]],
    *,
    unit_kind: str,
) -> tuple[int, int, str] | None:
    finite = _semantic_finite_relation_spans(tokens)
    if unit_kind in {"list-item", "ordered-step"}:
        first = _semantic_first_content_index(tokens)
        if first < len(tokens) and tokens[first] in {"a", "an", "the", "this"}:
            if finite:
                return finite[0]
        return _semantic_forced_head(
            tokens, actions, start=0, allow_lexical=True
        )
    direct = _semantic_forced_head(
        tokens, actions, start=0, allow_lexical=False
    )
    if direct is not None:
        return direct
    modality_indexes = _semantic_alias_matches(tokens, "modality")[1]
    negation_indexes = _semantic_negation_indexes(tokens)
    forced_indexes = sorted(modality_indexes | negation_indexes)
    for index in forced_indexes:
        head = _semantic_forced_head(
            tokens, actions, start=index + 1, allow_lexical=True
        )
        if head is not None:
            return head
    if finite:
        return finite[0]
    return next((action for action in actions if action[0] > 0), None)


def _semantic_token_has_object_concept(token: str) -> bool:
    return bool(_semantic_alias_matches([token], "object-condition")[0])


def _semantic_predicates(
    tokens: Sequence[str],
    *,
    unit_kind: str,
) -> list[tuple[str, int, tuple[int, int, str]]]:
    actions = _semantic_action_candidates(tokens)
    first = _semantic_first_predicate(tokens, actions, unit_kind=unit_kind)
    if first is None:
        return []
    predicates: list[tuple[str, int, tuple[int, int, str]]] = [
        ("root", 0, first)
    ]
    occupied_until = first[1]
    for connector_index in range(first[1], len(tokens)):
        connector = tokens[connector_index]
        if connector not in _SEMANTIC_PREDICATE_CONNECTORS:
            continue
        head = _semantic_forced_head(
            tokens,
            actions,
            start=connector_index + 1,
            allow_lexical=True,
        )
        if head is None or head[0] < occupied_until:
            continue
        head_is_closed = not head[2].startswith("lexical:")
        if head_is_closed and not _semantic_action_surface_is_exact(tokens, head):
            continue
        previous_index = connector_index - 1
        next_index = head[0] + 1
        object_coordination = (
            previous_index >= occupied_until
            and _semantic_token_has_object_concept(tokens[previous_index])
            and _semantic_token_has_object_concept(tokens[head[0]])
            and not (
                next_index < len(tokens)
                and tokens[next_index] in _SEMANTIC_RELATIVE_CONDITION_TOKENS
            )
        )
        if object_coordination:
            continue
        if not head_is_closed:
            if (
                next_index >= len(tokens)
                or not _semantic_token_has_object_concept(tokens[next_index])
            ):
                continue
        following_connector = next(
            (
                index
                for index in range(head[1], len(tokens))
                if tokens[index] in _SEMANTIC_PREDICATE_CONNECTORS
            ),
            len(tokens),
        )
        trailing_tokens = tokens[head[1] : following_connector]
        prior_tokens = tokens[occupied_until:connector_index]
        if (
            not any(
                token not in _SEMANTIC_STOP_TOKENS
                for token in trailing_tokens
            )
            and not any(token in {"it", "them"} for token in trailing_tokens)
            and any(
                token not in _SEMANTIC_STOP_TOKENS for token in prior_tokens
            )
        ):
            continue
        predicates.append((connector, connector_index, head))
        occupied_until = head[1]
    return predicates


def _semantic_grammatical_condition_spans(
    tokens: Sequence[str],
) -> list[tuple[int, int, str]]:
    matches: list[tuple[int, int, str]] = []
    for boundary in sorted(
        _SEMANTIC_GRAMMATICAL_CONDITION_BOUNDARIES,
        key=lambda value: len(value.split()),
        reverse=True,
    ):
        boundary_tokens = _semantic_tokenize(boundary)
        for start in range(0, len(tokens) - len(boundary_tokens) + 1):
            if list(tokens[start : start + len(boundary_tokens)]) == boundary_tokens:
                matches.append((start, start + len(boundary_tokens), boundary))
    selected: list[tuple[int, int, str]] = []
    for match in sorted(matches, key=lambda row: (row[0], -(row[1] - row[0]))):
        if not any(match[0] < end and start < match[1] for start, end, _ in selected):
            selected.append(match)
    return sorted(selected)


def _semantic_scope_partition(
    tokens: Sequence[str],
    *,
    start: int,
    action_indexes: set[int],
    ignored_indexes: set[int],
) -> tuple[set[str], set[str]]:
    spans = _semantic_alias_spans(tokens, "object-condition")
    condition_spans = _semantic_grammatical_condition_spans(tokens)
    first_condition = condition_spans[0][0] if condition_spans else None
    objects: set[str] = set()
    conditions: set[str] = set()
    consumed = set(action_indexes) | set(ignored_indexes)
    for span_start, span_end, _boundary in condition_spans:
        consumed.update(range(span_start, span_end))
    for span_start, span_end, concept in spans:
        indexes = set(range(span_start, span_end))
        consumed.update(indexes)
        if indexes & action_indexes or span_end <= start:
            continue
        destination = conditions if (
            concept in _SEMANTIC_CONDITION_CONCEPTS
            or (first_condition is not None and span_start >= first_condition)
        ) else objects
        destination.add(concept)
    trailing_modalities, trailing_modality_indexes = _semantic_alias_matches(
        tokens, "modality"
    )
    consumed.update(trailing_modality_indexes)
    if first_condition is not None:
        conditions.update(
            f"modality:{concept}" for concept in trailing_modalities
        )
    for index in range(start, len(tokens)):
        token = tokens[index]
        if index in consumed or token in _SEMANTIC_STOP_TOKENS:
            continue
        destination = conditions if (
            first_condition is not None and index >= first_condition
        ) else objects
        destination.add(f"term:{token}")
    return objects, conditions


def _semantic_first_condition_index(tokens: Sequence[str]) -> int | None:
    spans = _semantic_grammatical_condition_spans(tokens)
    return spans[0][0] if spans else None


def _semantic_relation_scope_concepts(tokens: Sequence[str]) -> list[str]:
    """Project one relation scope without treating semantic concepts as grammar."""

    concepts: set[str] = set()
    consumed: set[int] = set()
    for span_start, span_end, concept in _semantic_alias_spans(
        tokens, "object-condition"
    ):
        consumed.update(range(span_start, span_end))
        concepts.add(concept)
    _modalities, modality_indexes = _semantic_alias_matches(tokens, "modality")
    consumed.update(modality_indexes)
    consumed.update(_semantic_negation_indexes(tokens))
    for span_start, span_end, _boundary in _semantic_grammatical_condition_spans(
        tokens
    ):
        consumed.update(range(span_start, span_end))
    for index, token in enumerate(tokens):
        if index in consumed or token in _SEMANTIC_STOP_TOKENS:
            continue
        concepts.add(f"term:{token}")
    return sorted(concepts)


def _semantic_lexical_action_head(
    tokens: Sequence[str], index: int
) -> tuple[int, int, str] | None:
    """Return one closed-slot lexical base head without widening aliases."""

    if index >= len(tokens):
        return None
    token = tokens[index]
    if not re.fullmatch(r"[a-z]+", token):
        return None
    boundary_tokens = {
        part
        for boundary in _SEMANTIC_GRAMMATICAL_CONDITION_BOUNDARIES
        for part in _semantic_tokenize(boundary)
    }
    negation_tokens = {
        part
        for alias in _SEMANTIC_NEGATION_ALIASES
        for part in _semantic_tokenize(alias)
    }
    if token in (
        _SEMANTIC_STOP_TOKENS
        | _SEMANTIC_PREDICATE_CONNECTORS
        | {"from", "into", "to"}
        | boundary_tokens
        | negation_tokens
    ):
        return None
    if (
        token.endswith("ed")
        or token.endswith("ing")
        or token.endswith("ies")
        or (token.endswith("s") and not token.endswith("ss"))
    ):
        return None
    action_concepts, _action_indexes = _semantic_alias_matches(
        [token], "action"
    )
    finite_relations = _semantic_finite_relation_spans([token])
    object_concepts, _object_indexes = _semantic_alias_matches(
        [token], "object-condition"
    )
    modality_concepts, _modality_indexes = _semantic_alias_matches(
        [token], "modality"
    )
    if (
        action_concepts
        or finite_relations
        or object_concepts
        or modality_concepts
    ):
        return None
    return (index, index + 1, f"lexical:{token}")


def _semantic_marker_classification(
    tokens: Sequence[str],
    *,
    condition_spans: Sequence[tuple[int, int, str]],
) -> tuple[dict[int, str], list[tuple[int, tuple[int, int, str]]]]:
    """Classify grammatical infinitives before projecting direction roles."""

    actions = _semantic_action_candidates(tokens)
    directions: dict[int, str] = {}
    infinitives: list[tuple[int, tuple[int, int, str]]] = []
    determiners = {"a", "an", "any", "each", "every", "the", "this"}

    def has_complement(start: int) -> bool:
        boundary_starts = {
            boundary_start
            for boundary_start, _boundary_end, _kind in condition_spans
        }
        for position in range(start, len(tokens)):
            token = tokens[position]
            if (
                position in boundary_starts
                or token in {"from", "into", "to"}
                or token in _SEMANTIC_PREDICATE_CONNECTORS
            ):
                return False
            if token not in _SEMANTIC_STOP_TOKENS:
                return True
        return False

    for marker, token in enumerate(tokens):
        if token not in {"from", "into", "to"}:
            continue
        if any(
            start <= marker < end
            for start, end, _boundary in condition_spans
        ):
            continue
        if token in {"from", "into"}:
            directions[marker] = "from" if token == "from" else "to"
            continue
        following = [action for action in actions if action[0] == marker + 1]
        if following:
            if len(following) != 1:
                raise ProfessionalCarryForwardError(
                    "material semantic clause has overlapping infinitive action aliases"
                )
            action = following[0]
            if not _semantic_action_surface_is_exact_closed_alias(tokens, action):
                raise ProfessionalCarryForwardError(
                    "material semantic clause has unsupported inflected infinitive"
                )
            infinitives.append((marker, action))
            continue
        lexical = _semantic_lexical_action_head(tokens, marker + 1)
        if lexical is None:
            directions[marker] = "to"
            continue
        determiner_index = lexical[1]
        if (
            determiner_index >= len(tokens)
            or tokens[determiner_index] not in determiners
        ):
            directions[marker] = "to"
            continue
        if not has_complement(determiner_index + 1):
            raise ProfessionalCarryForwardError(
                "material semantic clause has malformed lexical infinitive complement"
            )
        infinitives.append((marker, lexical))
    return directions, infinitives


def _semantic_structural_owner_events(
    tokens: Sequence[str],
    *,
    condition_spans: Sequence[tuple[int, int, str]],
    infinitives: Sequence[tuple[int, tuple[int, int, str]]],
    initial_condition_scope: bool = False,
) -> list[tuple[int, int, int, str | None, str, str, str]]:
    """Return closed dependent owner signals for directional attachments."""

    actions = _semantic_action_candidates(tokens)
    first_condition = condition_spans[0][0] if condition_spans else len(tokens)
    events: list[tuple[int, int, int, str | None, str, str, str]] = []
    composite_action_spans: set[tuple[int, int]] = set()

    def is_condition_region(index: int) -> bool:
        return initial_condition_scope or index >= first_condition

    def closed_or_direction_alias(
        index: int, *, frame: str
    ) -> tuple[int, int, str] | None:
        action = _semantic_action_at(actions, index)
        if action is not None:
            return action
        forms = _semantic_lexeme_forms(tokens[index])
        if frame == "gerund" and "turn" in forms:
            return (index, index + 1, "change")
        if frame == "modal" and "distinguish" in forms:
            return (index, index + 1, "compare")
        if frame == "passive" and tokens[index] == "mapped":
            return (index, index + 1, "map")
        return None

    def owner_metadata(lead: Sequence[str]) -> tuple[str, str]:
        modal_classes: set[str] = set()
        if any(token in {"can", "cannot", "may"} for token in lead):
            modal_classes.add("permitted")
        if "should" in lead:
            modal_classes.add("recommended")
        if any(token in {"must", "shall"} for token in lead):
            modal_classes.add("required")
        if len(modal_classes) > 1:
            raise ProfessionalCarryForwardError(
                "material semantic clause has conflicting dependent owner modalities"
            )
        modality = next(iter(modal_classes)) if modal_classes else "asserted"
        polarity = (
            "negative"
            if any(token in {"cannot", "never", "not"} for token in lead)
            else "affirmative"
        )
        return modality, polarity

    def add_event(
        signal_start: int,
        action_start: int,
        action_end: int,
        action_concept: str | None,
        attachment: str,
        modality: str,
        polarity: str,
    ) -> None:
        same_span = [
            event
            for event in events
            if event[1:5]
            == (action_start, action_end, action_concept, attachment)
        ]
        if same_span:
            if any(event[5:] != (modality, polarity) for event in same_span):
                raise ProfessionalCarryForwardError(
                    "material semantic clause has conflicting dependent owner metadata"
                )
            return
        events.append(
            (
                signal_start,
                action_start,
                action_end,
                action_concept,
                attachment,
                modality,
                polarity,
            )
        )

    for marker, action in infinitives:
        attachment = (
            "dependent-condition"
            if is_condition_region(action[0])
            else "dependent-complement"
        )
        add_event(
            marker,
            action[0],
            action[1],
            action[2],
            attachment,
            "asserted",
            "affirmative",
        )

    for preposition_index, token in enumerate(tokens[:-1]):
        action_index = preposition_index + 1
        if token not in {"by", "in", "through", "while"}:
            continue
        if not tokens[action_index].endswith("ing"):
            continue
        action = closed_or_direction_alias(action_index, frame="gerund")
        attachment = (
            "dependent-condition"
            if is_condition_region(action_index)
            else "dependent-complement"
        )
        add_event(
            preposition_index,
            action[0] if action is not None else action_index,
            action[1] if action is not None else action_index + 1,
            action[2] if action is not None else None,
            attachment,
            "asserted",
            "affirmative",
        )

    owner_lead_tokens = {
        "can",
        "cannot",
        "do",
        "may",
        "must",
        "never",
        "not",
        "shall",
        "should",
    }
    lead_index = 0
    while lead_index < len(tokens):
        if tokens[lead_index] not in owner_lead_tokens:
            lead_index += 1
            continue
        lead_end = lead_index
        while lead_end < len(tokens) and tokens[lead_end] in owner_lead_tokens:
            lead_end += 1
        modality, polarity = owner_metadata(tokens[lead_index:lead_end])
        if (
            lead_end + 1 < len(tokens)
            and tokens[lead_end] == "be"
            and tokens[lead_end + 1].endswith("ed")
        ):
            action = closed_or_direction_alias(lead_end + 1, frame="passive")
            attachment = (
                "dependent-condition"
                if is_condition_region(lead_end + 1)
                else "dependent-complement"
            )
            action_start = action[0] if action is not None else lead_end + 1
            action_end = action[1] if action is not None else lead_end + 2
            add_event(
                lead_index,
                action_start,
                action_end,
                action[2] if action is not None else None,
                attachment,
                modality,
                polarity,
            )
            composite_action_spans.add((action_start, action_end))
            lead_index = lead_end + 2
            continue
        action_index = lead_end
        if action_index >= len(tokens):
            lead_index = max(lead_end, lead_index + 1)
            continue
        action = closed_or_direction_alias(action_index, frame="modal")
        if action is None:
            action = _semantic_lexical_action_head(tokens, action_index)
        attachment = (
            "dependent-condition"
            if is_condition_region(action_index)
            else "dependent-complement"
        )
        action_start = action[0] if action is not None else action_index
        action_end = action[1] if action is not None else action_index + 1
        add_event(
            lead_index,
            action_start,
            action_end,
            action[2] if action is not None else None,
            attachment,
            modality,
            polarity,
        )
        lead_index = action_end

    for be_index, token in enumerate(tokens[:-1]):
        action_index = be_index + 1
        if token not in {"are", "be", "is", "was", "were"}:
            continue
        if not tokens[action_index].endswith("ed"):
            continue
        if (action_index, action_index + 1) in composite_action_spans:
            continue
        action = closed_or_direction_alias(action_index, frame="passive")
        attachment = (
            "dependent-condition"
            if is_condition_region(action_index)
            else "dependent-complement"
        )
        add_event(
            be_index,
            action[0] if action is not None else action_index,
            action[1] if action is not None else action_index + 1,
            action[2] if action is not None else None,
            attachment,
            "asserted",
            "affirmative",
        )

    for action in actions:
        if not _semantic_action_surface_is_exact_closed_alias(tokens, action):
            continue
        if any(event[1:3] == (action[0], action[1]) for event in events):
            continue
        attachment = (
            "dependent-condition"
            if is_condition_region(action[0])
            else "barrier"
        )
        add_event(
            action[0],
            action[0],
            action[1],
            action[2],
            attachment,
            "asserted",
            "affirmative",
        )
    return sorted(events, key=lambda event: (event[0], event[1], event[2]))


def _semantic_argument_role_bindings(
    tokens: Sequence[str],
    *,
    governing_action_concept: str,
    governing_modality: str,
    governing_polarity: str,
    initial_condition_scope: bool = False,
) -> list[dict[str, Any]]:
    """Bind ordered directional arguments to their structural predicate owner."""

    condition_spans = _semantic_grammatical_condition_spans(tokens)
    direction_relations, infinitives = _semantic_marker_classification(
        tokens,
        condition_spans=condition_spans,
    )
    direction_indexes = sorted(direction_relations)
    if not direction_indexes:
        object_end = condition_spans[0][0] if condition_spans else len(tokens)
        scopes = _semantic_relation_scope_concepts(tokens[:object_end])
        if not scopes and condition_spans:
            scopes = _semantic_relation_scope_concepts(
                tokens[condition_spans[0][1] :]
            )
            if scopes:
                return [
                    {
                        "argument_ordinal": 1,
                        "relation": "direct",
                        "scope_concepts": scopes,
                        "attachment": "condition-scope",
                        "owner_action_concept": None,
                        "owner_modality": None,
                        "owner_polarity": None,
                    }
                ]
        if not scopes:
            return []
        return [
            {
                "argument_ordinal": 1,
                "relation": "direct",
                "scope_concepts": scopes,
                "attachment": "governing-predicate",
                "owner_action_concept": governing_action_concept,
                "owner_modality": governing_modality,
                "owner_polarity": governing_polarity,
            }
        ]

    owner_events = _semantic_structural_owner_events(
        tokens,
        condition_spans=condition_spans,
        infinitives=infinitives,
        initial_condition_scope=initial_condition_scope,
    )
    owners_by_marker: dict[
        int, tuple[int, int, int, str | None, str, str, str] | None
    ] = {}

    def interval_end(
        owner: tuple[int, int, int, str | None, str, str, str],
    ) -> int:
        candidates = [len(tokens)]
        candidates.extend(
            start
            for start, _end, _kind in condition_spans
            if start >= owner[2]
        )
        candidates.extend(
            event[0]
            for event in owner_events
            if event is not owner and event[0] >= owner[2]
        )
        return min(candidates)

    for marker in direction_indexes:
        candidates = [
            event
            for event in owner_events
            if event[4] != "barrier"
            and event[2] <= marker < interval_end(event)
        ]
        if candidates:
            nearest_end = max(event[2] for event in candidates)
            candidates = [
                event for event in candidates if event[2] == nearest_end
            ]
        if len(candidates) > 1:
            raise ProfessionalCarryForwardError(
                "material semantic clause has competing dependent owners"
            )
        owner = candidates[0] if candidates else None
        if owner is not None and owner[3] is None:
            raise ProfessionalCarryForwardError(
                "material semantic clause has structurally signaled unknown "
                "dependent owner"
            )
        owners_by_marker[marker] = owner

    selected_owners = {
        event for event in owners_by_marker.values() if event is not None
    }
    events: list[tuple[int, int, str, object]] = []
    for start, end, boundary in condition_spans:
        events.append((start, end, "boundary", boundary))
    for event in selected_owners:
        events.append((event[0], event[2], "owner", event))
    for marker in direction_indexes:
        events.append((marker, marker + 1, "direction", marker))
    events.sort(key=lambda event: (event[0], event[1], event[2]))

    bindings: list[dict[str, Any]] = []
    cursor = 0
    relation = "direct"
    attachment = "governing-predicate"
    owner_action: str | None = governing_action_concept
    owner_modality: str | None = governing_modality
    owner_polarity: str | None = governing_polarity
    pending_direction = False

    def append_scope(end: int) -> None:
        nonlocal pending_direction
        if end < cursor:
            raise ProfessionalCarryForwardError(
                "material semantic clause has overlapping directional attachment"
            )
        scopes = _semantic_relation_scope_concepts(tokens[cursor:end])
        if not scopes:
            if pending_direction:
                raise ProfessionalCarryForwardError(
                    "material semantic clause has incomplete directional argument segment"
                )
            return
        bindings.append(
            {
                "argument_ordinal": len(bindings) + 1,
                "relation": relation,
                "scope_concepts": scopes,
                "attachment": attachment,
                "owner_action_concept": owner_action,
                "owner_modality": owner_modality,
                "owner_polarity": owner_polarity,
            }
        )
        pending_direction = False

    for event_start, event_end, event_kind, payload in events:
        if event_start < cursor:
            raise ProfessionalCarryForwardError(
                "material semantic clause has overlapping directional attachment"
            )
        append_scope(event_start)
        if event_kind == "boundary":
            if pending_direction:
                raise ProfessionalCarryForwardError(
                    "material semantic clause has incomplete directional argument segment"
                )
            relation = "direct"
            attachment = "condition-scope"
            owner_action = None
            owner_modality = None
            owner_polarity = None
        elif event_kind == "owner":
            if pending_direction:
                raise ProfessionalCarryForwardError(
                    "material semantic clause has overlapping directional attachment"
                )
            owner_event = payload
            if not isinstance(owner_event, tuple):  # pragma: no cover - local invariant
                raise AssertionError("directional owner event must be a tuple")
            relation = "direct"
            attachment = owner_event[4]
            owner_action = owner_event[3]
            owner_modality = owner_event[5]
            owner_polarity = owner_event[6]
        else:
            marker = payload
            if not isinstance(marker, int):  # pragma: no cover - local invariant
                raise AssertionError("directional marker must be an integer")
            selected_owner = owners_by_marker[marker]
            if selected_owner is None:
                is_after_boundary = any(
                    start < marker for start, _end, _kind in condition_spans
                ) or initial_condition_scope
                attachment = (
                    "condition-scope" if is_after_boundary else "governing-predicate"
                )
                owner_action = None if is_after_boundary else governing_action_concept
                owner_modality = None if is_after_boundary else governing_modality
                owner_polarity = None if is_after_boundary else governing_polarity
            else:
                attachment = selected_owner[4]
                owner_action = selected_owner[3]
                owner_modality = selected_owner[5]
                owner_polarity = selected_owner[6]
            relation = direction_relations[marker]
            pending_direction = True
        cursor = event_end
    append_scope(len(tokens))
    if pending_direction:
        raise ProfessionalCarryForwardError(
            "material semantic clause has incomplete directional argument segment"
        )
    if not bindings:
        raise ProfessionalCarryForwardError(
            "material semantic clause has unconsumed direction marker"
        )
    return bindings


def _semantic_object_scope_union(
    argument_role_bindings: Sequence[Mapping[str, Any]],
) -> list[str]:
    return sorted(
        {
            concept
            for binding in argument_role_bindings
            for concept in binding["scope_concepts"]
        }
    )


def _semantic_rebind_governing_argument_roles(
    argument_role_bindings: Sequence[Mapping[str, Any]],
    *,
    action_concept: str,
    modality: str,
    polarity: str,
) -> list[dict[str, Any]]:
    rebound = copy.deepcopy(list(argument_role_bindings))
    for binding in rebound:
        if binding["attachment"] != "governing-predicate":
            continue
        binding["owner_action_concept"] = action_concept
        binding["owner_modality"] = modality
        binding["owner_polarity"] = polarity
    return rebound


def _validate_semantic_fact(fact: Mapping[str, Any]) -> None:
    """Reject malformed or lossy semantic facts before canonical deduplication."""

    if set(fact) != _SEMANTIC_FACT_FIELDS:
        raise ProfessionalCarryForwardError(
            "Professional semantic fact fields do not match the closed contract"
        )
    for field in (
        "fact_class",
        "section_kind",
        "fact_kind",
        "action_concept",
        "modality",
        "polarity",
    ):
        if not isinstance(fact[field], str) or not fact[field]:
            raise ProfessionalCarryForwardError(
                f"Professional semantic fact {field} must be non-empty text"
            )
    if fact["source_class"] not in panel_contracts.PROFESSIONAL_SEMANTIC_FACT_SOURCE_CLASSES:
        raise ProfessionalCarryForwardError(
            "Professional semantic fact has unknown source class"
        )
    if fact["unit_kind"] not in _SEMANTIC_UNIT_KINDS:
        raise ProfessionalCarryForwardError(
            "Professional semantic fact has unknown unit kind"
        )
    if type(fact["predicate_ordinal"]) is not int or fact["predicate_ordinal"] < 1:
        raise ProfessionalCarryForwardError(
            "Professional semantic predicate ordinal must be a positive integer"
        )
    if fact["incoming_connector"] not in _SEMANTIC_PREDICATE_CONNECTORS | {"root"}:
        raise ProfessionalCarryForwardError(
            "Professional semantic fact has unknown incoming connector"
        )
    if fact["predicate_ordinal"] == 1:
        if fact["incoming_connector"] != "root":
            raise ProfessionalCarryForwardError(
                "first Professional semantic predicate must use root connector"
            )
    elif fact["incoming_connector"] == "root":
        raise ProfessionalCarryForwardError(
            "non-first Professional semantic predicate cannot use root connector"
        )

    for field in (
        "subject_scope_concepts",
        "object_scope_concepts",
        "condition_concepts",
    ):
        value = fact[field]
        if (
            not isinstance(value, list)
            or value != sorted(set(value))
            or any(not isinstance(item, str) or not item for item in value)
        ):
            raise ProfessionalCarryForwardError(
                f"Professional semantic fact {field} must be a sorted unique text list"
            )
    if not fact["subject_scope_concepts"]:
        raise ProfessionalCarryForwardError(
            "Professional semantic fact subject scope must not be empty"
        )
    if fact["modality"] not in {"asserted", "permitted", "recommended", "required"}:
        raise ProfessionalCarryForwardError(
            "Professional semantic fact has unknown modality"
        )
    if fact["polarity"] not in {"affirmative", "negative"}:
        raise ProfessionalCarryForwardError(
            "Professional semantic fact has unknown polarity"
        )

    bindings = fact["argument_role_bindings"]
    if not isinstance(bindings, list) or not bindings:
        raise ProfessionalCarryForwardError(
            "Professional semantic fact argument role bindings must not be empty"
        )
    for expected_ordinal, binding in enumerate(bindings, start=1):
        if not isinstance(binding, Mapping) or set(binding) != _SEMANTIC_ARGUMENT_ROLE_FIELDS:
            raise ProfessionalCarryForwardError(
                "Professional semantic argument role fields do not match the closed contract"
            )
        if binding["argument_ordinal"] != expected_ordinal:
            raise ProfessionalCarryForwardError(
                "Professional semantic argument ordinals must be contiguous"
            )
        if binding["relation"] not in _SEMANTIC_ARGUMENT_RELATIONS:
            raise ProfessionalCarryForwardError(
                "Professional semantic fact has unknown argument relation"
            )
        if binding["attachment"] not in _SEMANTIC_ARGUMENT_ATTACHMENTS:
            raise ProfessionalCarryForwardError(
                "Professional semantic fact has unknown argument attachment"
            )
        owner_action = binding["owner_action_concept"]
        owner_modality = binding["owner_modality"]
        owner_polarity = binding["owner_polarity"]
        if binding["attachment"] == "condition-scope":
            if any(
                value is not None
                for value in (owner_action, owner_modality, owner_polarity)
            ):
                raise ProfessionalCarryForwardError(
                    "Professional semantic condition-scope owner metadata must be null"
                )
        else:
            if not isinstance(owner_action, str) or not owner_action:
                raise ProfessionalCarryForwardError(
                    "Professional semantic attached owner action must be non-empty text"
                )
            if owner_modality not in {
                "asserted",
                "permitted",
                "recommended",
                "required",
            }:
                raise ProfessionalCarryForwardError(
                    "Professional semantic attached owner modality is unknown"
                )
            if owner_polarity not in {"affirmative", "negative"}:
                raise ProfessionalCarryForwardError(
                    "Professional semantic attached owner polarity is unknown"
                )
        if (
            binding["attachment"] == "governing-predicate"
            and (
                owner_action != fact["action_concept"]
                or owner_modality != fact["modality"]
                or owner_polarity != fact["polarity"]
            )
        ):
            raise ProfessionalCarryForwardError(
                "Professional semantic governing argument owner metadata mismatch"
            )
        scopes = binding["scope_concepts"]
        if (
            not isinstance(scopes, list)
            or not scopes
            or scopes != sorted(set(scopes))
            or any(not isinstance(item, str) or not item for item in scopes)
        ):
            raise ProfessionalCarryForwardError(
                "Professional semantic argument scope concepts must be a non-empty "
                "sorted unique text list"
            )
    if fact["object_scope_concepts"] != _semantic_object_scope_union(bindings):
        raise ProfessionalCarryForwardError(
            "Professional semantic fact object scope union mismatch"
        )


def _semantic_subject_scope(
    tokens: Sequence[str],
    *,
    action_start: int,
    lead_indexes: set[int],
) -> list[str]:
    objects, conditions = _semantic_scope_partition(
        tokens[:action_start],
        start=0,
        action_indexes=set(),
        ignored_indexes=lead_indexes,
    )
    scopes = objects | conditions
    return sorted(scopes) if scopes else ["actor:implicit"]


def _semantic_labeled_fact(
    *,
    source_class: str,
    section_kind: str,
    unit_kind: str,
    fact_class: str,
    fact_kind: str,
    label: str,
    text: str,
    predicate_ordinal: int,
    forced_modality: str | None,
    default_object: str,
) -> dict[str, Any]:
    label_tokens = _semantic_tokenize(label)
    value_tokens = _semantic_tokenize(text)
    subjects, subject_conditions = _semantic_scope_partition(
        label_tokens,
        start=0,
        action_indexes=set(),
        ignored_indexes=set(),
    )
    objects, conditions = _semantic_scope_partition(
        value_tokens,
        start=0,
        action_indexes=set(),
        ignored_indexes=set(),
    )
    symbol_names = {
        "&": "ampersand",
        ",": "comma",
        "?": "question-mark",
    }
    objects.update(
        f"symbol:{name}" for symbol, name in symbol_names.items() if symbol in text
    )
    subjects.update(subject_conditions)
    if not subjects:
        subjects.add("field:unlabeled")
    if not objects:
        objects.add(default_object)
    argument_role_bindings = [
        {
            "argument_ordinal": 1,
            "relation": "direct",
            "scope_concepts": sorted(objects),
            "attachment": "governing-predicate",
            "owner_action_concept": "define",
            "owner_modality": forced_modality or "asserted",
            "owner_polarity": "affirmative",
        }
    ]
    return {
        "source_class": source_class,
        "fact_class": fact_class,
        "section_kind": section_kind,
        "unit_kind": unit_kind,
        "fact_kind": fact_kind,
        "predicate_ordinal": predicate_ordinal,
        "incoming_connector": "root" if predicate_ordinal == 1 else "then",
        "subject_scope_concepts": sorted(subjects),
        "action_concept": "define",
        "argument_role_bindings": argument_role_bindings,
        "object_scope_concepts": _semantic_object_scope_union(
            argument_role_bindings
        ),
        "condition_concepts": sorted(conditions),
        "modality": forced_modality or "asserted",
        "polarity": "affirmative",
    }


def _semantic_clause_facts(
    *,
    source_class: str,
    section_kind: str | None,
    unit_kind: str,
    text: str,
    fact_defaults: tuple[str, str, str, str] | None = None,
    forced_modality: str | None = None,
    label: str | None = None,
) -> list[dict[str, Any]] | None:
    tokens = _semantic_tokenize(text)
    if section_kind in {"excluded", "source-citation"}:
        return None
    if text.rstrip().endswith(":") and _semantic_section_kind(
        text.rstrip()[:-1]
    ) == "source-citation":
        return None
    if unit_kind not in _SEMANTIC_UNIT_KINDS:
        raise ProfessionalCarryForwardError(
            f"unknown Professional semantic unit kind: {unit_kind}"
        )
    if not tokens and re.search(r"https?://", text):
        return None
    if not tokens and unit_kind not in {"table-row", "labeled-field"}:
        raise ProfessionalCarryForwardError(
            "material semantic clause has no predicate"
        )
    effective_section = section_kind or "general-guidance"
    defaults = fact_defaults or _SEMANTIC_SECTION_FACTS.get(effective_section)
    if defaults is None:
        return None
    fact_class, fact_kind, default_action, default_object = defaults
    if unit_kind in {"table-row", "labeled-field"}:
        return [
            _semantic_labeled_fact(
                source_class=source_class,
                section_kind=effective_section,
                unit_kind=unit_kind,
                fact_class=fact_class,
                fact_kind=fact_kind,
                label=label or effective_section,
                text=text,
                predicate_ordinal=1,
                forced_modality=forced_modality,
                default_object=default_object,
            )
        ]

    predicates = _semantic_predicates(tokens, unit_kind=unit_kind)
    if fact_defaults is not None:
        direct = predicates[0][2] if predicates else None
        if direct is None or any(
            token not in _SEMANTIC_PREDICATE_LEAD_TOKENS
            for token in tokens[: direct[0]]
        ):
            return [
                _semantic_labeled_fact(
                    source_class=source_class,
                    section_kind=effective_section,
                    unit_kind="labeled-field",
                    fact_class=fact_class,
                    fact_kind=fact_kind,
                    label=effective_section,
                    text=text,
                    predicate_ordinal=1,
                    forced_modality=forced_modality,
                    default_object=default_object,
                )
            ]
    if not predicates:
        if section_kind is None:
            return None
        if effective_section not in {"decision-rules", "general-guidance"}:
            return [
                _semantic_labeled_fact(
                    source_class=source_class,
                    section_kind=effective_section,
                    unit_kind="labeled-field",
                    fact_class=fact_class,
                    fact_kind=fact_kind,
                    label=effective_section,
                    text=text,
                    predicate_ordinal=1,
                    forced_modality=forced_modality,
                    default_object=default_object,
                )
            ]
        raise ProfessionalCarryForwardError(
            "material semantic clause has no predicate "
            f"({source_class}/{effective_section}: {' '.join(tokens[:16])})"
        )

    facts: list[dict[str, Any]] = []
    inherited_modality: str | None = None
    inherited_subject: list[str] | None = None
    clause_condition_spans = _semantic_grammatical_condition_spans(tokens)
    for ordinal, (connector, connector_index, action) in enumerate(
        predicates, start=1
    ):
        next_boundary = (
            predicates[ordinal][1]
            if ordinal < len(predicates)
            else len(tokens)
        )
        window_start = 0 if ordinal == 1 else connector_index + 1
        prefix_tokens = tokens[window_start : action[0]]
        local_modalities, local_modality_indexes = _semantic_alias_matches(
            prefix_tokens, "modality"
        )
        if len(local_modalities) > 1:
            raise ProfessionalCarryForwardError(
                "material semantic clause is ambiguous: one predicate has "
                "conflicting modalities"
            )
        local_negation_indexes = _semantic_negation_indexes(prefix_tokens)
        lead_indexes = set(local_modality_indexes) | local_negation_indexes
        lead_indexes.update(
            index
            for index, token in enumerate(prefix_tokens)
            if token in _SEMANTIC_PREDICATE_LEAD_TOKENS
        )
        subjects = _semantic_subject_scope(
            prefix_tokens,
            action_start=len(prefix_tokens),
            lead_indexes=lead_indexes,
        )
        if subjects == ["actor:implicit"] and inherited_subject is not None:
            subjects = inherited_subject
        ignored_indexes = set()
        after_action = tokens[action[1] : next_boundary]
        _objects, conditions = _semantic_scope_partition(
            after_action,
            start=0,
            action_indexes=set(),
            ignored_indexes=ignored_indexes,
        )
        if forced_modality is not None:
            modality = forced_modality
        elif local_modalities:
            modality = next(iter(local_modalities))
        elif ordinal == 1 and unit_kind in {"list-item", "ordered-step"}:
            modality = "required"
        elif inherited_modality is not None:
            modality = inherited_modality
        else:
            modality = "asserted"
        polarity = "negative" if local_negation_indexes else "affirmative"
        argument_role_bindings = _semantic_argument_role_bindings(
            after_action,
            governing_action_concept=action[2] or default_action,
            governing_modality=modality,
            governing_polarity=polarity,
            initial_condition_scope=any(
                boundary_end <= action[1]
                for _boundary_start, boundary_end, _kind in clause_condition_spans
            ),
        )
        if (
            not argument_role_bindings
            and not conditions
            and any(token in {"it", "them"} for token in after_action)
            and facts
        ):
            argument_role_bindings = _semantic_rebind_governing_argument_roles(
                facts[-1]["argument_role_bindings"],
                action_concept=action[2] or default_action,
                modality=modality,
                polarity=polarity,
            )
            conditions.update(facts[-1]["condition_concepts"])
        facts.append(
            {
                "source_class": source_class,
                "fact_class": fact_class,
                "section_kind": effective_section,
                "unit_kind": unit_kind,
                "fact_kind": fact_kind,
                "predicate_ordinal": ordinal,
                "incoming_connector": connector,
                "subject_scope_concepts": subjects,
                "action_concept": action[2] or default_action,
                "argument_role_bindings": argument_role_bindings,
                "object_scope_concepts": _semantic_object_scope_union(
                    argument_role_bindings
                ),
                "condition_concepts": sorted(conditions),
                "modality": modality,
                "polarity": polarity,
            }
        )
        inherited_modality = modality
        inherited_subject = subjects

    for index in range(len(facts) - 1, -1, -1):
        fact = facts[index]
        if fact["argument_role_bindings"] or fact["condition_concepts"]:
            continue
        if (
            index + 1 < len(facts)
            and facts[index + 1]["incoming_connector"] in {"and", "or", "but"}
            and (
                facts[index + 1]["argument_role_bindings"]
                or facts[index + 1]["condition_concepts"]
            )
        ):
            fact["argument_role_bindings"] = (
                _semantic_rebind_governing_argument_roles(
                    facts[index + 1]["argument_role_bindings"],
                    action_concept=fact["action_concept"],
                    modality=fact["modality"],
                    polarity=fact["polarity"],
                )
            )
            fact["object_scope_concepts"] = _semantic_object_scope_union(
                fact["argument_role_bindings"]
            )
            fact["condition_concepts"] = list(
                facts[index + 1]["condition_concepts"]
            )
            continue
        if len(facts) == 1:
            fact["argument_role_bindings"] = [
                {
                    "argument_ordinal": 1,
                    "relation": "direct",
                    "scope_concepts": [default_object],
                    "attachment": "governing-predicate",
                    "owner_action_concept": fact["action_concept"],
                    "owner_modality": fact["modality"],
                    "owner_polarity": fact["polarity"],
                }
            ]
            fact["object_scope_concepts"] = [default_object]
            continue
        raise ProfessionalCarryForwardError(
            "material semantic clause is ambiguous: predicate attachment "
            "is not unique"
        )
    return facts


def _semantic_identity_concept(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProfessionalCarryForwardError(f"{label} must be non-empty text")
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    if not normalized:
        raise ProfessionalCarryForwardError(
            f"{label} has no canonical semantic identity"
        )
    return normalized


def professional_semantic_fact_projection(
    target: Mapping[str, Any],
) -> dict[str, Any]:
    """Project closed Professional facts without raw prose or repository state."""

    semantic_target = target
    if "root" not in target and isinstance(target.get("own_material"), Mapping):
        own = target["own_material"]
        semantic_target = {
            **target,
            "root": own.get("root"),
            "indexed_references": own.get("indexed_references"),
        }
    own_material = professional_own_material_binding(semantic_target)
    professional_registry_responsibility_binding(target)
    responsibility = professional_semantic_responsibility_binding(target)
    expertise = professional_required_expertise_binding(target)
    facts: list[dict[str, Any]] = []

    for source_class, records in (
        ("root", [own_material["root"]]),
        ("indexed-reference", own_material["indexed_references"]),
    ):
        for record in records:
            for unit in _professional_markdown_semantic_units(record["content"]):
                section_kind = _semantic_section_kind(unit["heading"])
                if unit["unit_kind"] == "table-row":
                    for ordinal, field in enumerate(unit["fields"], start=1):
                        field_facts = _semantic_clause_facts(
                            source_class=source_class,
                            section_kind=section_kind,
                            unit_kind="table-row",
                            text=field["text"],
                            label=field["label"],
                        )
                        if field_facts is not None:
                            field_facts[0]["predicate_ordinal"] = ordinal
                            field_facts[0]["incoming_connector"] = (
                                "root" if ordinal == 1 else "then"
                            )
                            facts.extend(field_facts)
                    continue
                for clause in _semantic_clause_slices(unit["text"]):
                    clause_facts = _semantic_clause_facts(
                        source_class=source_class,
                        section_kind=section_kind,
                        unit_kind=unit["unit_kind"],
                        text=clause,
                        label=unit.get("label"),
                    )
                    if clause_facts is not None:
                        facts.extend(clause_facts)

    for field, defaults in sorted(_SEMANTIC_REGISTRY_FACTS.items()):
        for value in responsibility[field]:
            clause_facts = _semantic_clause_facts(
                source_class="registry",
                section_kind=defaults[1],
                unit_kind="paragraph",
                text=value,
                fact_defaults=(defaults[0], defaults[2], defaults[3], defaults[4]),
                forced_modality="required",
            )
            if clause_facts is None:  # pragma: no cover - registry sections are material
                raise AssertionError("registry fact projection was unexpectedly empty")
            facts.extend(clause_facts)

    for field, fact_class in (
        ("layer3_candidates", "required-adjacency"),
        ("used_by", "required-adjacency"),
    ):
        for value in responsibility[field]:
            facts.append(
                {
                    "source_class": "registry",
                    "fact_class": fact_class,
                    "section_kind": f"registry-{field.replace('_', '-')}",
                    "unit_kind": "labeled-field",
                    "fact_kind": "routing",
                    "predicate_ordinal": 1,
                    "incoming_connector": "root",
                    "subject_scope_concepts": [
                        f"registry-field:{field.replace('_', '-')}"
                    ],
                    "action_concept": "handoff",
                    "argument_role_bindings": [
                        {
                            "argument_ordinal": 1,
                            "relation": "direct",
                            "scope_concepts": [
                                "skill:" + _semantic_identity_concept(
                                    value,
                                    label=f"target responsibility {field}",
                                )
                            ],
                            "attachment": "governing-predicate",
                            "owner_action_concept": "handoff",
                            "owner_modality": "required",
                            "owner_polarity": "affirmative",
                        }
                    ],
                    "object_scope_concepts": [
                        "skill:" + _semantic_identity_concept(
                            value, label=f"target responsibility {field}"
                        )
                    ],
                    "condition_concepts": [],
                    "modality": "required",
                    "polarity": "affirmative",
                }
            )
    for field in ("group", "content_class", "delivery_scope"):
        value = responsibility[field]
        if value is not None:
            facts.append(
                {
                    "source_class": "registry",
                    "fact_class": "responsibility",
                    "section_kind": f"registry-{field.replace('_', '-')}",
                    "unit_kind": "labeled-field",
                    "fact_kind": "classification",
                    "predicate_ordinal": 1,
                    "incoming_connector": "root",
                    "subject_scope_concepts": [
                        f"registry-field:{field.replace('_', '-')}"
                    ],
                    "action_concept": "classify",
                    "argument_role_bindings": [
                        {
                            "argument_ordinal": 1,
                            "relation": "direct",
                            "scope_concepts": [
                                f"{field.replace('_', '-')}:"
                                + _semantic_identity_concept(
                                    value,
                                    label=f"target responsibility {field}",
                                )
                            ],
                            "attachment": "governing-predicate",
                            "owner_action_concept": "classify",
                            "owner_modality": "asserted",
                            "owner_polarity": "affirmative",
                        }
                    ],
                    "object_scope_concepts": [
                        f"{field.replace('_', '-')}:"
                        + _semantic_identity_concept(
                            value, label=f"target responsibility {field}"
                        )
                    ],
                    "condition_concepts": [],
                    "modality": "asserted",
                    "polarity": "affirmative",
                }
            )
    if responsibility["task_routable"] is not None:
        facts.append(
            {
                "source_class": "registry",
                "fact_class": "routing-boundary",
                "section_kind": "registry-task-routable",
                "unit_kind": "labeled-field",
                "fact_kind": "routing",
                "predicate_ordinal": 1,
                "incoming_connector": "root",
                "subject_scope_concepts": ["registry-field:task-routable"],
                "action_concept": "handoff",
                "argument_role_bindings": [
                    {
                        "argument_ordinal": 1,
                        "relation": "direct",
                        "scope_concepts": ["target"],
                        "attachment": "governing-predicate",
                        "owner_action_concept": "handoff",
                        "owner_modality": "asserted",
                        "owner_polarity": (
                            "affirmative"
                            if responsibility["task_routable"]
                            else "negative"
                        ),
                    }
                ],
                "object_scope_concepts": ["target"],
                "condition_concepts": [],
                "modality": "asserted",
                "polarity": (
                    "affirmative"
                    if responsibility["task_routable"]
                    else "negative"
                ),
            }
        )
    for tag in expertise:
        facts.append(
            {
                "source_class": "required-expertise",
                "fact_class": "required-expertise",
                "section_kind": "registry-required-expertise",
                "unit_kind": "labeled-field",
                "fact_kind": "qualification",
                "predicate_ordinal": 1,
                "incoming_connector": "root",
                "subject_scope_concepts": [
                    "registry-field:required-expertise"
                ],
                "action_concept": "require",
                "argument_role_bindings": [
                    {
                        "argument_ordinal": 1,
                        "relation": "direct",
                        "scope_concepts": [
                            "expertise:"
                            + _semantic_identity_concept(
                                tag, label="target required expertise tag"
                            )
                        ],
                        "attachment": "governing-predicate",
                        "owner_action_concept": "require",
                        "owner_modality": "required",
                        "owner_polarity": "affirmative",
                    }
                ],
                "object_scope_concepts": [
                    "expertise:"
                    + _semantic_identity_concept(
                        tag, label="target required expertise tag"
                    )
                ],
                "condition_concepts": [],
                "modality": "required",
                "polarity": "affirmative",
            }
        )
    for fact in facts:
        _validate_semantic_fact(fact)
    deduplicated = {
        canonical_json_bytes(fact): fact
        for fact in facts
    }
    return {
        "contract_version": _SEMANTIC_FACT_PROJECTION_VERSION,
        "facts": [deduplicated[key] for key in sorted(deduplicated)],
    }


def professional_candidate_semantic_review_binding(
    target: Mapping[str, Any],
) -> dict[str, Any]:
    """Project stable Professional judgment authority, excluding raw prose."""

    skill_id = _require_skill_id(target.get("skill_id"), label="target.skill_id")
    layer = _require_skill_id(target.get("layer"), label=f"{skill_id}.layer")
    return {
        "skill_id": skill_id,
        "layer": layer,
        "semantic_fact_projection": professional_semantic_fact_projection(target),
    }


def professional_adjacency_review_binding(
    target: Mapping[str, Any],
) -> dict[str, Any]:
    """Project only target-local selection authority used by currentness."""

    context = professional_fresh_adjacency_review_context(target)
    selection = context["required_candidate_selection"]
    version = selection.get("version")
    if not isinstance(version, str) or not version.strip():
        raise ProfessionalCarryForwardError(
            "target adjacency selection contract version must be non-empty"
        )
    required_ids = [
        candidate["skill_id"] for candidate in context["required_candidates"]
    ]
    return _canonical_adjacency_review_binding(
        {
            "required_candidate_ids": required_ids,
            "selection_contract_version": version,
        }
    )


def _canonical_adjacency_review_binding(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != (
        _ADJACENCY_REVIEW_BINDING_FIELDS
    ):
        raise ProfessionalCarryForwardError(
            "target adjacency carry fields are not canonical"
        )
    required_ids = _sorted_unique_strings(
        value.get("required_candidate_ids"),
        label="target adjacency required_candidate_ids",
    )
    version = value.get("selection_contract_version")
    if not isinstance(version, str) or not version.strip():
        raise ProfessionalCarryForwardError(
            "target adjacency selection_contract_version must be non-empty"
        )
    return {
        "required_candidate_ids": required_ids,
        "selection_contract_version": version,
    }


def professional_fresh_adjacency_review_context(
    target: Mapping[str, Any],
) -> dict[str, Any]:
    """Project full ranking context for fresh review, never for currentness."""

    adjacency = target.get("routing_adjacency")
    if not isinstance(adjacency, dict):
        raise ProfessionalCarryForwardError(
            "target.routing_adjacency must be an object"
        )
    required = adjacency.get("required_candidates")
    ranking = adjacency.get("full_catalog_ranking")
    selection = adjacency.get("required_candidate_selection")
    if not isinstance(required, list) or not isinstance(ranking, list):
        raise ProfessionalCarryForwardError(
            "target adjacency must bind required candidates and full ranking"
        )
    if not isinstance(selection, dict):
        raise ProfessionalCarryForwardError(
            "target adjacency must bind its required-candidate selection contract"
        )
    required_ids = [
        _require_skill_id(item.get("skill_id"), label="required candidate skill_id")
        if isinstance(item, dict)
        else _raise_invalid_candidate("required candidate")
        for item in required
    ]
    ranking_ids = [
        _require_skill_id(item.get("skill_id"), label="ranking candidate skill_id")
        if isinstance(item, dict)
        else _raise_invalid_candidate("ranking candidate")
        for item in ranking
    ]
    if required_ids != sorted(set(required_ids)):
        raise ProfessionalCarryForwardError(
            "required adjacency candidates must be skill-sorted and unique"
        )
    if len(ranking_ids) != len(set(ranking_ids)):
        raise ProfessionalCarryForwardError(
            "full catalog ranking must contain unique Skill IDs"
        )
    if not set(required_ids) <= set(ranking_ids):
        raise ProfessionalCarryForwardError(
            "required adjacency candidates must be present in full ranking"
        )
    if adjacency.get("full_catalog_count") != len(ranking):
        raise ProfessionalCarryForwardError(
            "full catalog count must match embedded ranking"
        )
    missing = sorted(_FRESH_ADJACENCY_CONTEXT_FIELDS - set(adjacency))
    if missing:
        raise ProfessionalCarryForwardError(
            "target adjacency lacks review-visible fields: " + ", ".join(missing)
        )
    return {
        field: copy.deepcopy(adjacency[field])
        for field in sorted(_FRESH_ADJACENCY_CONTEXT_FIELDS)
    }


def _raise_invalid_candidate(label: str) -> str:
    raise ProfessionalCarryForwardError(f"{label} must be an object")


def professional_candidate_material_binding(
    target: Mapping[str, Any],
) -> dict[str, Any]:
    """Project complete candidate material while deliberately excluding ranking.

    A candidate's adjacency/ranking is not review material for another target.
    Excluding it prevents a ranking-only change from recursively invalidating
    every target that reviewed this candidate.
    """

    skill_id = _require_skill_id(target.get("skill_id"), label="target.skill_id")
    layer = _require_skill_id(target.get("layer"), label=f"{skill_id}.layer")
    return {
        "skill_id": skill_id,
        "layer": layer,
        "own_material": professional_own_material_binding(target),
        "registry": professional_registry_responsibility_binding(target),
        "required_expertise_tags": professional_required_expertise_binding(target),
    }


def _canonical_target_index(
    targets: Sequence[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    if not isinstance(targets, Sequence) or isinstance(targets, (str, bytes)):
        raise ProfessionalCarryForwardError("targets must be an array")
    index: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for position, target in enumerate(targets):
        if not isinstance(target, dict):
            raise ProfessionalCarryForwardError(
                f"targets[{position}] must be an object"
            )
        skill_id = _require_skill_id(
            target.get("skill_id"), label=f"targets[{position}].skill_id"
        )
        if skill_id in index:
            raise ProfessionalCarryForwardError(
                f"duplicate target Skill ID: {skill_id}"
            )
        index[skill_id] = target
        order.append(skill_id)
    if order != sorted(order):
        raise ProfessionalCarryForwardError("targets must be skill-sorted")
    return index


def professional_review_bindings(
    targets: Sequence[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Build separate raw-content and canonical semantic review bindings."""

    target_index = _canonical_target_index(targets)
    candidate_materials = {
        skill_id: professional_candidate_material_binding(target)
        for skill_id, target in target_index.items()
    }
    content_fingerprints = {
        skill_id: canonical_json_sha256(material)
        for skill_id, material in candidate_materials.items()
    }
    candidate_semantic_bindings = {
        skill_id: professional_candidate_semantic_review_binding(target)
        for skill_id, target in target_index.items()
    }
    candidate_fingerprints = {
        skill_id: canonical_json_sha256(binding)
        for skill_id, binding in candidate_semantic_bindings.items()
    }
    bindings: dict[str, dict[str, Any]] = {}
    for skill_id in sorted(target_index):
        target = target_index[skill_id]
        own_material = candidate_materials[skill_id]["own_material"]
        registry = candidate_materials[skill_id]["registry"]
        expertise = candidate_materials[skill_id]["required_expertise_tags"]
        adjacency = professional_adjacency_review_binding(target)
        required_ids = adjacency["required_candidate_ids"]
        unknown = sorted(set(required_ids) - set(target_index))
        if unknown:
            raise ProfessionalCarryForwardError(
                f"{skill_id} requires unknown adjacency candidates: "
                + ", ".join(unknown)
            )
        dependency_material_bindings = {
            candidate_id: candidate_fingerprints[candidate_id]
            for candidate_id in required_ids
        }
        binding: dict[str, Any] = {
            "skill_id": skill_id,
            "layer": candidate_materials[skill_id]["layer"],
            "own_material": own_material,
            "registry": registry,
            "required_expertise_tags": expertise,
            "adjacency": adjacency,
            "content_fingerprint": content_fingerprints[skill_id],
            "package_material_binding": candidate_fingerprints[skill_id],
            "dependency_material_bindings": dependency_material_bindings,
        }
        binding["review_unit_binding"] = canonical_json_sha256(
            {
                "skill_id": skill_id,
                "layer": binding["layer"],
                "package_material_binding": binding[
                    "package_material_binding"
                ],
                "dependency_material_bindings": binding[
                    "dependency_material_bindings"
                ],
                "adjacency": binding["adjacency"],
            }
        )
        bindings[skill_id] = binding
    _validate_binding_catalog(bindings)
    return bindings


def professional_historical_content_review_bindings(
    targets: Sequence[dict[str, Any]],
) -> Mapping[str, dict[str, Any]]:
    """Reproduce the retired raw-content binding for historical validation.

    New packets and carry plans must use :func:`professional_review_bindings`.
    This adapter exists only so immutable schema-3 evidence created before the
    semantic binding migration remains auditable without authorizing carry.
    """

    target_index = _canonical_target_index(targets)
    candidate_materials = {
        skill_id: professional_candidate_material_binding(target)
        for skill_id, target in target_index.items()
    }
    candidate_fingerprints = {
        skill_id: canonical_json_sha256(material)
        for skill_id, material in candidate_materials.items()
    }
    bindings: _HistoricalContentBindingCatalog = (
        _HistoricalContentBindingCatalog()
    )
    for skill_id in sorted(target_index):
        target = target_index[skill_id]
        material = candidate_materials[skill_id]
        adjacency = professional_adjacency_review_binding(target)
        required_ids = adjacency["required_candidate_ids"]
        unknown = sorted(set(required_ids) - set(target_index))
        if unknown:
            raise ProfessionalCarryForwardError(
                f"{skill_id} requires unknown adjacency candidates: "
                + ", ".join(unknown)
            )
        legacy_projection = {
            "skill_id": skill_id,
            "layer": material["layer"],
            "own_material": material["own_material"],
            "registry": material["registry"],
            "required_expertise_tags": material[
                "required_expertise_tags"
            ],
            "adjacency": adjacency,
            "package_material_binding": candidate_fingerprints[skill_id],
            "dependency_material_bindings": {
                candidate_id: candidate_fingerprints[candidate_id]
                for candidate_id in required_ids
            },
        }
        bindings[skill_id] = {
            **legacy_projection,
            "content_fingerprint": candidate_fingerprints[skill_id],
            "review_unit_binding": canonical_json_sha256(legacy_projection),
        }
    _validate_binding_catalog(bindings)
    return bindings


def _validate_binding_catalog(
    bindings: Mapping[str, dict[str, Any]],
) -> None:
    if not isinstance(bindings, Mapping) or not bindings:
        raise ProfessionalCarryForwardError(
            "professional bindings must be a non-empty mapping"
        )
    if list(bindings) != sorted(bindings):
        raise ProfessionalCarryForwardError(
            "professional bindings must be Skill-sorted"
        )
    historical_content = isinstance(bindings, _HistoricalContentBindingCatalog)
    candidate_fingerprints: dict[str, str] = {}
    for key, binding in bindings.items():
        if not isinstance(binding, dict) or set(binding) != _TARGET_BINDING_FIELDS:
            raise ProfessionalCarryForwardError(
                f"binding {key} fields are not canonical"
            )
        if binding.get("skill_id") != key:
            raise ProfessionalCarryForwardError(
                f"binding key {key} does not match skill_id"
            )
        own = _canonical_own_material_binding(
            binding.get("own_material"), label=f"binding {key}"
        )
        registry = professional_registry_responsibility_binding(binding)
        expertise = professional_required_expertise_binding(binding)
        adjacency = _canonical_adjacency_review_binding(
            binding.get("adjacency")
        )
        content_projection = {
            "skill_id": key,
            "layer": binding["layer"],
            "own_material": own,
            "registry": registry,
            "required_expertise_tags": expertise,
        }
        if binding.get("content_fingerprint") != canonical_json_sha256(
            content_projection
        ):
            raise ProfessionalCarryForwardError(
                f"binding {key}.content_fingerprint is stale"
            )
        semantic_projection = (
            None
            if historical_content
            else professional_candidate_semantic_review_binding(binding)
        )
        candidate_fingerprint = (
            binding["content_fingerprint"]
            if historical_content
            else canonical_json_sha256(semantic_projection)
        )
        if binding.get("package_material_binding") != candidate_fingerprint:
            raise ProfessionalCarryForwardError(
                f"binding {key}.package_material_binding is stale"
            )
        candidate_fingerprints[key] = candidate_fingerprint
        review_fingerprint = binding["review_unit_binding"]
        review_projection = (
            {
                field: copy.deepcopy(binding[field])
                for field in (
                    "skill_id",
                    "layer",
                    "own_material",
                    "registry",
                    "required_expertise_tags",
                    "adjacency",
                    "package_material_binding",
                    "dependency_material_bindings",
                )
            }
            if historical_content
            else {
                "skill_id": key,
                "layer": binding["layer"],
                "package_material_binding": candidate_fingerprint,
                "dependency_material_bindings": binding[
                    "dependency_material_bindings"
                ],
                "adjacency": adjacency,
            }
        )
        if review_fingerprint != canonical_json_sha256(review_projection):
            raise ProfessionalCarryForwardError(
                f"binding {key}.review_unit_binding is stale"
            )
    for key, binding in bindings.items():
        required_ids = binding["adjacency"]["required_candidate_ids"]
        material_bindings = binding.get("dependency_material_bindings")
        if not isinstance(material_bindings, dict):
            raise ProfessionalCarryForwardError(
                f"binding {key}.dependency_material_bindings is invalid"
            )
        material_ids = list(material_bindings)
        if material_ids != required_ids:
            raise ProfessionalCarryForwardError(
                f"binding {key} required candidate material set is stale"
            )
        for candidate_id, material_fingerprint in material_bindings.items():
            if candidate_id not in candidate_fingerprints:
                raise ProfessionalCarryForwardError(
                    f"binding {key} names unknown candidate {candidate_id}"
                )
            if material_fingerprint != candidate_fingerprints[candidate_id]:
                raise ProfessionalCarryForwardError(
                    f"binding {key} candidate material for {candidate_id} is stale"
                )


def professional_carry_snapshot(
    bindings: Mapping[str, dict[str, Any]],
    *,
    review_contract_fingerprint: str,
) -> dict[str, Any]:
    """Create the semantic-only compact baseline consumed by carry planning."""

    _validate_binding_catalog(bindings)
    contract = _require_sha256(
        review_contract_fingerprint,
        label="review_contract_fingerprint",
    )
    targets = {
        skill_id: {
            field: copy.deepcopy(binding[field])
            for field in sorted(_SNAPSHOT_TARGET_FIELDS)
        }
        for skill_id, binding in bindings.items()
    }
    return {
        "review_contract_fingerprint": contract,
        "targets": targets,
    }


def professional_current_authority(
    bindings: Mapping[str, dict[str, Any]],
    *,
    authenticated_claims: Mapping[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Project the complete fail-closed authority map for compact evidence."""

    _validate_binding_catalog(bindings)
    if (
        not isinstance(authenticated_claims, Mapping)
        or set(authenticated_claims) != set(bindings)
    ):
        raise ProfessionalCarryForwardError(
            "Professional current package authority coverage is stale"
        )
    candidate_semantic_bindings = {
        skill_id: binding["package_material_binding"]
        for skill_id, binding in bindings.items()
    }
    authority: dict[str, dict[str, Any]] = {}
    relationship_overlaps: dict[str, tuple[str, ...]] = {}
    for skill_id, binding in bindings.items():
        claims = authenticated_claims[skill_id]
        if not isinstance(claims, dict) or set(claims) != {
            "vote_authorities",
            "reviewer_partition",
            "evidence_metrics",
            "origin",
            "reviewer_added_candidate_ids_union",
        }:
            raise ProfessionalCarryForwardError(
                f"{skill_id} authenticated Professional claims are incomplete"
            )
        votes = claims["vote_authorities"]
        partition = claims["reviewer_partition"]
        metrics = claims["evidence_metrics"]
        origin = claims["origin"]
        required_ids = binding["adjacency"]["required_candidate_ids"]
        reviewer_added_ids = _sorted_unique_strings(
            claims["reviewer_added_candidate_ids_union"],
            label=f"{skill_id}.reviewer_added_candidate_ids_union",
        )
        unknown_added = sorted(set(reviewer_added_ids) - set(bindings))
        if unknown_added:
            raise ProfessionalCarryForwardError(
                f"{skill_id} reviewer-added candidates are unknown: "
                + ", ".join(unknown_added)
            )
        overlap = tuple(sorted(set(reviewer_added_ids) & set(required_ids)))
        if overlap:
            relationship_overlaps[skill_id] = overlap
        if (
            not isinstance(votes, dict)
            or len(votes) != panel_contracts.PROFESSIONAL_PANEL_SIZE
            or any(
                not isinstance(voter_id, str)
                or not voter_id
                or not isinstance(vote, dict)
                or vote.get("reviewer") != voter_id
                or not _is_sha256(vote.get("review_evidence_fingerprint"))
                for voter_id, vote in votes.items()
            )
            or not isinstance(partition, dict)
            or set(partition) != {"domain_voters", "architecture_voter"}
            or not isinstance(partition["domain_voters"], list)
            or partition["domain_voters"]
            != sorted(set(partition["domain_voters"]))
            or len(partition["domain_voters"])
            != panel_contracts.PROFESSIONAL_REQUIRED_DOMAIN_EXPERTS
            or not all(
                isinstance(voter_id, str) and voter_id
                for voter_id in partition["domain_voters"]
            )
            or not isinstance(partition["architecture_voter"], str)
            or not partition["architecture_voter"]
            or partition["architecture_voter"] in partition["domain_voters"]
            or set(votes)
            != {
                *partition["domain_voters"],
                partition["architecture_voter"],
            }
            or not isinstance(metrics, dict)
            or set(metrics) != _PROFESSIONAL_EVIDENCE_METRIC_KEYS
            or any(type(value) is not int or value < 0 for value in metrics.values())
            or not isinstance(origin, dict)
            or set(origin) != {
                "origin_review_id",
                "origin_commit",
                "origin_verdict_digest",
            }
            or not isinstance(origin["origin_review_id"], str)
            or not origin["origin_review_id"]
            or not isinstance(origin["origin_commit"], str)
            or re.fullmatch(r"[0-9a-f]{40}", origin["origin_commit"]) is None
            or not _is_sha256(origin["origin_verdict_digest"])
        ):
            raise ProfessionalCarryForwardError(
                f"{skill_id} authenticated Professional claims are invalid"
            )
        authority[skill_id] = {
            "package_material_binding": binding[
                "package_material_binding"
            ],
            "review_unit_binding": binding[
                "review_unit_binding"
            ],
            "required_expertise_tags": copy.deepcopy(
                binding["required_expertise_tags"]
            ),
            "selection_contract_version": binding["adjacency"][
                "selection_contract_version"
            ],
            "required_candidate_ids": copy.deepcopy(required_ids),
            "required_candidate_material_bindings": {
                candidate_id: candidate_semantic_bindings[candidate_id]
                for candidate_id in required_ids
            },
            "reviewer_added_candidate_ids_union": reviewer_added_ids,
            "reviewer_added_candidate_material_bindings": {
                candidate_id: candidate_semantic_bindings[candidate_id]
                for candidate_id in reviewer_added_ids
            },
            "vote_authorities": copy.deepcopy(votes),
            "reviewer_partition": copy.deepcopy(partition),
            "evidence_metrics": copy.deepcopy(metrics),
            "origin": copy.deepcopy(origin),
        }
    if relationship_overlaps:
        raise ProfessionalReviewerAddedRequiredRelationshipDrift(
            relationship_overlaps
        )
    return authority


def _required_candidate_ids(target: Mapping[str, Any]) -> list[str]:
    adjacency = target.get("routing_adjacency")
    required = adjacency.get("required_candidates") if isinstance(adjacency, dict) else None
    if not isinstance(required, list):
        raise ProfessionalCarryForwardError(
            "prior target lacks required adjacency candidates"
        )
    ids = [
        _require_skill_id(row.get("skill_id"), label="required candidate skill_id")
        if isinstance(row, dict)
        else _raise_invalid_candidate("required candidate")
        for row in required
    ]
    if ids != sorted(set(ids)):
        raise ProfessionalCarryForwardError(
            "prior required candidate IDs must be sorted and unique"
        )
    return ids


def professional_prior_decision_dependencies(
    *,
    prior_packet: Mapping[str, Any],
    prior_ballots: Sequence[Mapping[str, Any]],
    prior_decision: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    """Extract one-hop dependencies from previously validated panel artifacts.

    The reviewer-added set is recomputed as a union across all three target
    votes, including a candidate added only by a dissenting/minority ballot.  A
    decision's audit projection is cross-checked against that union.  Missing
    evidence is represented as ``evidence_complete=false`` so the carry planner
    fails the target fresh instead of treating an incomplete baseline as an
    exceptional control-flow error.
    """

    targets_raw = prior_packet.get("professional_targets")
    decisions_raw = prior_decision.get("professional_decisions")
    if not isinstance(targets_raw, list):
        raise ProfessionalCarryForwardError(
            "prior packet professional_targets must be an array"
        )
    if not isinstance(prior_ballots, Sequence) or isinstance(
        prior_ballots, (str, bytes)
    ):
        raise ProfessionalCarryForwardError("prior ballots must be an array")
    if not isinstance(decisions_raw, list):
        decisions_raw = []
    target_index = _canonical_target_index(targets_raw)
    full_ranking_ids = {
        skill_id: {
            row["skill_id"]
            for row in target["routing_adjacency"]["full_catalog_ranking"]
        }
        for skill_id, target in target_index.items()
    }
    required_by_target = {
        skill_id: _required_candidate_ids(target)
        for skill_id, target in target_index.items()
    }

    decision_index: dict[str, Mapping[str, Any]] = {}
    duplicate_decisions: set[str] = set()
    for row in decisions_raw:
        if not isinstance(row, Mapping):
            continue
        skill_id = row.get("skill_id")
        if not isinstance(skill_id, str):
            continue
        if skill_id in decision_index:
            duplicate_decisions.add(skill_id)
        decision_index[skill_id] = row
    unknown_decisions = sorted(set(decision_index) - set(target_index))
    if unknown_decisions:
        raise ProfessionalCarryForwardError(
            "prior decision names unknown targets: " + ", ".join(unknown_decisions)
        )

    packet_review_id = prior_packet.get("review_id")
    packet_sources = prior_packet.get("source_fingerprints")
    ballot_voters: dict[str, dict[str, Any]] = {}
    agent_owners: dict[str, str] = {}
    votes_by_target: dict[
        str, list[tuple[str, Mapping[str, Any], bool]]
    ] = {skill_id: [] for skill_id in target_index}
    for ballot_index, ballot in enumerate(prior_ballots):
        if not isinstance(ballot, Mapping):
            raise ProfessionalCarryForwardError(
                f"prior_ballots[{ballot_index}] must be an object"
            )
        voter = ballot.get("voter")
        if not isinstance(voter, Mapping):
            raise ProfessionalCarryForwardError(
                f"prior_ballots[{ballot_index}].voter must be an object"
            )
        voter_id = _require_skill_id(
            voter.get("voter_id"),
            label=f"prior_ballots[{ballot_index}].voter.voter_id",
        )
        agent_id = _require_skill_id(
            voter.get("agent_id"),
            label=f"prior_ballots[{ballot_index}].voter.agent_id",
        )
        if voter_id in ballot_voters:
            raise ProfessionalCarryForwardError(
                f"prior ballots duplicate voter_id {voter_id}"
            )
        if agent_id in agent_owners:
            raise ProfessionalCarryForwardError(
                f"prior ballots duplicate agent_id {agent_id}"
            )
        expertise_tags = voter.get("expertise_tags")
        if not isinstance(expertise_tags, list) or not all(
            isinstance(tag, str) and tag for tag in expertise_tags
        ):
            expertise_tags = []
        claims = voter.get("qualification_claims")
        claimed_tags = (
            [
                claim.get("expertise_tag")
                for claim in claims
                if isinstance(claim, Mapping)
            ]
            if isinstance(claims, list)
            else []
        )
        architecture = expertise_tags == ["skill-reference-architecture"]
        claims_complete = bool(
            isinstance(claims, list)
            and claims
            and all(
                isinstance(claim, Mapping)
                and isinstance(claim.get("qualification_basis"), str)
                and claim["qualification_basis"].strip()
                and isinstance(claim.get("proof_limit"), str)
                and claim["proof_limit"].strip()
                for claim in claims
            )
        )
        axis_complete = bool(
            architecture
            or "skill-reference-architecture" not in expertise_tags
        )
        qualification_complete = bool(
            expertise_tags
            and expertise_tags == sorted(set(expertise_tags))
            and claimed_tags == expertise_tags
            and claims_complete
            and axis_complete
            and voter.get("independent_review") is True
        )
        ballot_voters[voter_id] = {
            "agent_id": agent_id,
            "expertise_tags": expertise_tags,
            "voter_kind": "architecture" if architecture else "domain",
            "qualification_complete": qualification_complete,
        }
        agent_owners[agent_id] = voter_id
        ballot_current = bool(
            ballot.get("review_id") == packet_review_id
            and ballot.get("source_fingerprints") == packet_sources
        )
        votes = ballot.get("professional_votes")
        if not isinstance(votes, list):
            continue
        seen_in_ballot: set[str] = set()
        for vote in votes:
            if not isinstance(vote, Mapping):
                continue
            skill_id = vote.get("skill_id")
            if not isinstance(skill_id, str):
                continue
            if skill_id not in target_index:
                raise ProfessionalCarryForwardError(
                    f"prior ballot names unknown target {skill_id}"
                )
            if skill_id in seen_in_ballot:
                raise ProfessionalCarryForwardError(
                    f"prior ballot duplicates target {skill_id}"
                )
            seen_in_ballot.add(skill_id)
            votes_by_target[skill_id].append(
                (voter_id, vote, ballot_current)
            )

    decision_voters_raw = prior_decision.get("voters")
    decision_voters: dict[str, str] = {}
    decision_voters_complete = isinstance(decision_voters_raw, list)
    if isinstance(decision_voters_raw, list):
        for row in decision_voters_raw:
            if not isinstance(row, Mapping):
                decision_voters_complete = False
                continue
            voter_id = row.get("voter_id")
            agent_id = row.get("agent_id")
            if (
                not isinstance(voter_id, str)
                or not isinstance(agent_id, str)
                or voter_id in decision_voters
            ):
                decision_voters_complete = False
                continue
            decision_voters[voter_id] = agent_id
    decision_round_current = bool(
        prior_decision.get("review_id") == packet_review_id
        and prior_decision.get("source_fingerprints") == packet_sources
        and decision_voters_complete
        and decision_voters
        == {
            voter_id: metadata["agent_id"]
            for voter_id, metadata in ballot_voters.items()
        }
    )

    dependencies: dict[str, dict[str, Any]] = {}
    for skill_id in sorted(target_index):
        required_ids = required_by_target[skill_id]
        target_votes = votes_by_target[skill_id]
        reviewer_added_by_voter: dict[str, set[str]] = {}
        target_voter_ids = [voter_id for voter_id, _vote, _current in target_votes]
        votes_complete = bool(
            len(target_votes) == panel_contracts.PROFESSIONAL_PANEL_SIZE
            and len(target_voter_ids) == len(set(target_voter_ids))
            and all(current for _voter_id, _vote, current in target_votes)
        )
        domain_voters: list[str] = []
        architecture_voters: list[str] = []
        target_required_expertise = target_index[skill_id].get(
            "required_expertise_tags"
        )
        if not isinstance(target_required_expertise, list):
            target_required_expertise = []
            votes_complete = False
        for voter_id, vote, _current in target_votes:
            voter_metadata = ballot_voters[voter_id]
            if voter_metadata["voter_kind"] == "architecture":
                architecture_voters.append(voter_id)
            else:
                domain_voters.append(voter_id)
                if not set(target_required_expertise) <= set(
                    voter_metadata["expertise_tags"]
                ):
                    votes_complete = False
            if voter_metadata["qualification_complete"] is not True:
                votes_complete = False
            reviews = vote.get("examined_adjacent_candidates")
            if not isinstance(reviews, list):
                votes_complete = False
                continue
            reviewed_required: set[str] = set()
            added_for_voter: set[str] = set()
            reviewed_ids: set[str] = set()
            for review in reviews:
                if not isinstance(review, Mapping):
                    votes_complete = False
                    continue
                candidate_id = review.get("skill_id")
                origin = review.get("review_origin")
                if (
                    not isinstance(candidate_id, str)
                    or candidate_id not in full_ranking_ids[skill_id]
                    or candidate_id in reviewed_ids
                ):
                    votes_complete = False
                    continue
                reviewed_ids.add(candidate_id)
                if origin == "packet-required" and candidate_id in required_ids:
                    reviewed_required.add(candidate_id)
                elif origin == "reviewer-added" and candidate_id not in required_ids:
                    added_for_voter.add(candidate_id)
                else:
                    votes_complete = False
            if reviewed_required != set(required_ids):
                votes_complete = False
            if added_for_voter:
                reviewer_added_by_voter[voter_id] = added_for_voter
        if (
            len(domain_voters)
            != panel_contracts.PROFESSIONAL_REQUIRED_DOMAIN_EXPERTS
            or len(architecture_voters)
            != panel_contracts.PROFESSIONAL_REQUIRED_ARCHITECTURE_EXPERTS
        ):
            votes_complete = False

        reviewer_added = {
            candidate_id
            for candidates in reviewer_added_by_voter.values()
            for candidate_id in candidates
        }
        decision = decision_index.get(skill_id)
        final_disposition = (
            decision.get("final_disposition")
            if isinstance(decision, Mapping)
            else None
        )
        decision_added_by_voter: dict[str, set[str]] = {}
        decision_reviews = (
            decision.get("reviewer_added_adjacency_reviews")
            if isinstance(decision, Mapping)
            else None
        )
        decision_projection_complete = isinstance(decision_reviews, list)
        if isinstance(decision_reviews, list):
            for voter_review in decision_reviews:
                voter_id = (
                    voter_review.get("voter_id")
                    if isinstance(voter_review, Mapping)
                    else None
                )
                candidates = (
                    voter_review.get("candidates")
                    if isinstance(voter_review, Mapping)
                    else None
                )
                if (
                    not isinstance(voter_id, str)
                    or voter_id not in target_voter_ids
                    or voter_id in decision_added_by_voter
                    or not isinstance(candidates, list)
                ):
                    decision_projection_complete = False
                    continue
                ids = {
                    candidate.get("skill_id")
                    for candidate in candidates
                    if isinstance(candidate, Mapping)
                    and isinstance(candidate.get("skill_id"), str)
                }
                if len(ids) != len(candidates):
                    decision_projection_complete = False
                if any(
                    not isinstance(candidate, Mapping)
                    or candidate.get("review_origin") != "reviewer-added"
                    for candidate in candidates
                ):
                    decision_projection_complete = False
                decision_added_by_voter[voter_id] = ids
        qualification_coverage = (
            decision.get("qualification_coverage")
            if isinstance(decision, Mapping)
            else None
        )
        expected_qualification_coverage = {
            "required_expertise_tags": target_required_expertise,
            "domain_voters": sorted(domain_voters),
            "architecture_voter": (
                architecture_voters[0]
                if len(architecture_voters) == 1
                else None
            ),
        }
        package_fingerprint_current = target_index[skill_id].get(
            "package_fingerprint"
        )
        package_fingerprint_prior = (
            decision.get("package_fingerprint")
            if isinstance(decision, Mapping)
            else None
        )
        evidence_complete = bool(
            votes_complete
            and decision_round_current
            and decision is not None
            and skill_id not in duplicate_decisions
            and isinstance(final_disposition, str)
            and package_fingerprint_current == package_fingerprint_prior
            and qualification_coverage == expected_qualification_coverage
            and decision_projection_complete
            and reviewer_added_by_voter == decision_added_by_voter
        )
        dependency_ids = sorted(set(required_ids) | reviewer_added)
        dependencies[skill_id] = {
            "skill_id": skill_id,
            "final_disposition": final_disposition,
            "evidence_complete": evidence_complete,
            "prior_target_vote_count": len(target_votes),
            "required_candidate_ids": required_ids,
            "reviewer_added_candidate_ids_union": sorted(reviewer_added),
            "dependency_candidate_ids": dependency_ids,
        }
    return dependencies


def _snapshot_targets(
    prior_snapshot: object,
) -> tuple[str | None, dict[str, dict[str, Any]] | None]:
    if prior_snapshot is None:
        return None, None
    if not isinstance(prior_snapshot, Mapping) or set(prior_snapshot) != {
        "review_contract_fingerprint",
        "targets",
    }:
        raise ProfessionalCarryForwardError(
            "prior snapshot fields are not canonical"
        )
    contract = _require_sha256(
        prior_snapshot.get("review_contract_fingerprint"),
        label="prior_snapshot.review_contract_fingerprint",
    )
    targets = prior_snapshot.get("targets")
    if not isinstance(targets, dict):
        raise ProfessionalCarryForwardError(
            "prior_snapshot.targets must be an object"
        )
    if list(targets) != sorted(targets):
        raise ProfessionalCarryForwardError(
            "prior_snapshot.targets must be Skill-sorted"
        )
    for skill_id, target in targets.items():
        if not isinstance(target, dict) or set(target) != _SNAPSHOT_TARGET_FIELDS:
            raise ProfessionalCarryForwardError(
                f"prior snapshot target {skill_id} fields are not canonical"
            )
        if target.get("skill_id") != skill_id:
            raise ProfessionalCarryForwardError(
                f"prior snapshot target key {skill_id} is stale"
            )
    return contract, targets


def _decision_dependencies(
    value: Mapping[str, dict[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ProfessionalCarryForwardError(
            "prior decision dependencies must be an object"
        )
    dependencies: dict[str, dict[str, Any]] = {}
    for skill_id in sorted(value):
        dependency = value[skill_id]
        if not isinstance(dependency, dict) or set(dependency) != _DECISION_DEPENDENCY_FIELDS:
            raise ProfessionalCarryForwardError(
                f"prior decision dependency {skill_id} fields are not canonical"
            )
        if dependency.get("skill_id") != skill_id:
            raise ProfessionalCarryForwardError(
                f"prior decision dependency key {skill_id} is stale"
            )
        for field in (
            "required_candidate_ids",
            "reviewer_added_candidate_ids_union",
            "dependency_candidate_ids",
        ):
            _sorted_unique_strings(
                dependency.get(field), label=f"{skill_id}.{field}"
            )
        expected_union = sorted(
            set(dependency["required_candidate_ids"])
            | set(dependency["reviewer_added_candidate_ids_union"])
        )
        if dependency["dependency_candidate_ids"] != expected_union:
            raise ProfessionalCarryForwardError(
                f"prior decision dependency {skill_id} union is stale"
            )
        dependencies[skill_id] = dependency
    return dependencies


def plan_exact_professional_carry_forward(
    *,
    current_bindings: Mapping[str, dict[str, Any]],
    prior_snapshot: Mapping[str, Any] | None,
    prior_decision_dependencies: Mapping[str, dict[str, Any]] | None,
    review_contract_fingerprint: str,
) -> dict[str, Any]:
    """Partition whole packages into deterministic fresh and carry sets.

    The plan compares canonical semantic bindings only.  Raw content digests
    remain artifact-integrity evidence.  It never propagates another target's
    fresh/carry status, so A semantics can invalidate B when B reviewed A, but
    cannot invalidate C merely because C reviewed B.
    """

    _validate_binding_catalog(current_bindings)
    current_contract = _require_sha256(
        review_contract_fingerprint,
        label="review_contract_fingerprint",
    )
    prior_contract, prior_targets = _snapshot_targets(prior_snapshot)
    dependencies = _decision_dependencies(prior_decision_dependencies)
    reasons_by_target: dict[str, list[str]] = {}

    global_reason: str | None = None
    if prior_targets is None:
        global_reason = "no-prior-baseline"
    elif prior_contract != current_contract:
        global_reason = "review-contract-changed"

    for skill_id, binding in current_bindings.items():
        reasons: set[str] = set()
        if global_reason is not None:
            reasons.add(global_reason)
        else:
            prior = prior_targets.get(skill_id) if prior_targets else None
            dependency = dependencies.get(skill_id)
            if prior is None:
                reasons.add("target-not-in-prior-snapshot")
            if dependency is None or dependency.get("evidence_complete") is not True:
                reasons.add("prior-evidence-missing")
            if (
                dependency is not None
                and dependency.get("final_disposition")
                != ACCEPTED_PROFESSIONAL_DISPOSITION
            ):
                reasons.add("prior-final-not-accepted")
            if prior is not None:
                comparisons = (
                    ("layer", "target-placement-changed"),
                    ("package_material_binding", "target-material-changed"),
                )
                for field, reason in comparisons:
                    if prior.get(field) != binding.get(field):
                        reasons.add(reason)

                prior_required = prior["dependency_material_bindings"]
                current_required = binding["dependency_material_bindings"]
                if set(prior_required) != set(current_required):
                    reasons.add("adjacency-review-binding-changed")
                if set(prior_required) == set(current_required) and any(
                    prior_required[candidate_id]
                    != current_required[candidate_id]
                    for candidate_id in current_required
                ):
                    reasons.add("required-candidate-material-changed")
                if (
                    prior.get("review_unit_binding")
                    != binding.get("review_unit_binding")
                    and not reasons
                ):
                    reasons.add("review-unit-binding-changed")

                if dependency is not None:
                    for candidate_id in dependency[
                        "reviewer_added_candidate_ids_union"
                    ]:
                        prior_candidate = (
                            prior_targets.get(candidate_id)
                            if prior_targets is not None
                            else None
                        )
                        current_candidate = current_bindings.get(candidate_id)
                        if (
                            prior_candidate is None
                            or current_candidate is None
                            or prior_candidate.get(
                                "package_material_binding"
                            )
                            != current_candidate.get(
                                "package_material_binding"
                            )
                        ):
                            reasons.add(
                                "reviewer-added-candidate-material-changed"
                            )
                            break
        reasons_by_target[skill_id] = sorted(reasons)

    fresh = sorted(
        skill_id for skill_id, reasons in reasons_by_target.items() if reasons
    )
    carry = sorted(set(current_bindings) - set(fresh))
    return {
        "review_contract_fingerprint": current_contract,
        "fresh_target_ids": fresh,
        "carry_target_ids": carry,
        "reasons_by_target": reasons_by_target,
    }


def _candidate_projection_from_binding(
    binding: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "skill_id": binding["skill_id"],
        "layer": binding["layer"],
        "own_material": copy.deepcopy(binding["own_material"]),
        "registry": copy.deepcopy(binding["registry"]),
        "required_expertise_tags": copy.deepcopy(
            binding["required_expertise_tags"]
        ),
        "material_fingerprint": binding["content_fingerprint"],
    }


def _candidate_boundary_projection_from_binding(
    binding: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "skill_id": binding["skill_id"],
        "layer": binding["layer"],
        "responsibility_contract": copy.deepcopy(
            binding["registry"]["responsibility_contract"]
        ),
        "required_expertise_tags": copy.deepcopy(
            binding["required_expertise_tags"]
        ),
        "material_fingerprint": binding["content_fingerprint"],
    }


def _normalize_assigned_targets(
    *,
    bindings: Mapping[str, dict[str, Any]],
    assigned_fresh_target_ids: Sequence[str],
) -> list[str]:
    _validate_binding_catalog(bindings)
    if not isinstance(assigned_fresh_target_ids, Sequence) or isinstance(
        assigned_fresh_target_ids, (str, bytes)
    ):
        raise ProfessionalCarryForwardError(
            "assigned fresh targets must be an array"
        )
    assigned = list(assigned_fresh_target_ids)
    if not assigned:
        raise ProfessionalCarryForwardError(
            "assigned fresh targets must be non-empty"
        )
    if not all(isinstance(item, str) and item for item in assigned):
        raise ProfessionalCarryForwardError(
            "assigned fresh targets must contain Skill IDs"
        )
    if len(assigned) != len(set(assigned)):
        raise ProfessionalCarryForwardError(
            "assigned fresh targets must not contain duplicates"
        )
    assigned = sorted(assigned)
    unknown = sorted(set(assigned) - set(bindings))
    if unknown:
        raise ProfessionalCarryForwardError(
            "assigned fresh targets are unknown: " + ", ".join(unknown)
        )
    return assigned


def _fresh_adjacency_contexts(
    *,
    bindings: Mapping[str, dict[str, Any]],
    review_targets: Sequence[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Authenticate full fresh-review context outside carry/currentness state."""

    target_index = _canonical_target_index(review_targets)
    if set(target_index) != set(bindings):
        raise ProfessionalCarryForwardError(
            "fresh review target coverage is stale"
        )
    if professional_review_bindings(list(target_index.values())) != bindings:
        raise ProfessionalCarryForwardError(
            "fresh review targets do not match target-local bindings"
        )
    return {
        skill_id: professional_fresh_adjacency_review_context(target)
        for skill_id, target in target_index.items()
    }


def _project_professional_discovery_capsule(
    *,
    bindings: Mapping[str, dict[str, Any]],
    adjacency_contexts: Mapping[str, dict[str, Any]],
    assigned: Sequence[str],
) -> dict[str, Any]:
    targets: list[dict[str, Any]] = []
    material_ids: set[str] = set(assigned)
    for skill_id in assigned:
        binding = bindings[skill_id]
        required_ids = binding["adjacency"]["required_candidate_ids"]
        material_ids.update(required_ids)
        targets.append(
            {
                "skill_id": skill_id,
                "review_unit_binding": binding[
                    "review_unit_binding"
                ],
                "adjacency": copy.deepcopy(adjacency_contexts[skill_id]),
                "required_candidate_material_manifest": [
                    {
                        "skill_id": candidate_id,
                        "material_fingerprint": bindings[candidate_id][
                            "content_fingerprint"
                        ],
                    }
                    for candidate_id in required_ids
                ],
            }
        )
    return {
        "projection_contract": copy.deepcopy(
            PROFESSIONAL_DISCOVERY_CAPSULE_CONTRACT
        ),
        "assigned_fresh_target_ids": list(assigned),
        "material_catalog": [
            _candidate_projection_from_binding(bindings[skill_id])
            for skill_id in sorted(material_ids)
        ],
        "boundary_catalog": [
            _candidate_boundary_projection_from_binding(bindings[skill_id])
            for skill_id in sorted(bindings)
        ],
        "targets": targets,
    }


def project_professional_discovery_capsule(
    *,
    bindings: Mapping[str, dict[str, Any]],
    review_targets: Sequence[dict[str, Any]],
    assigned_fresh_target_ids: Sequence[str],
) -> dict[str, Any]:
    """Project the immutable first-stage discovery input for one reviewer."""

    assigned = _normalize_assigned_targets(
        bindings=bindings,
        assigned_fresh_target_ids=assigned_fresh_target_ids,
    )
    adjacency_contexts = _fresh_adjacency_contexts(
        bindings=bindings,
        review_targets=review_targets,
    )
    capsule = _project_professional_discovery_capsule(
        bindings=bindings,
        adjacency_contexts=adjacency_contexts,
        assigned=assigned,
    )
    validate_professional_discovery_capsule(
        capsule,
        bindings=bindings,
        review_targets=review_targets,
        assigned_fresh_target_ids=assigned,
    )
    return capsule


def validate_professional_discovery_capsule(
    capsule: object,
    *,
    bindings: Mapping[str, dict[str, Any]],
    review_targets: Sequence[dict[str, Any]],
    assigned_fresh_target_ids: Sequence[str],
) -> dict[str, Any]:
    """Reject incomplete, expanded, or stale discovery projections."""

    assigned = _normalize_assigned_targets(
        bindings=bindings,
        assigned_fresh_target_ids=assigned_fresh_target_ids,
    )
    adjacency_contexts = _fresh_adjacency_contexts(
        bindings=bindings,
        review_targets=review_targets,
    )
    if not isinstance(capsule, dict) or set(capsule) != _DISCOVERY_CAPSULE_FIELDS:
        raise ProfessionalCarryForwardError(
            "discovery capsule fields are not closed"
        )
    if (
        capsule.get("projection_contract")
        != PROFESSIONAL_DISCOVERY_CAPSULE_CONTRACT
    ):
        raise ProfessionalCarryForwardError(
            "discovery capsule projection contract is stale"
        )
    expected = _project_professional_discovery_capsule(
        bindings=bindings,
        adjacency_contexts=adjacency_contexts,
        assigned=assigned,
    )
    if capsule.get("assigned_fresh_target_ids") != assigned:
        raise ProfessionalCarryForwardError(
            "discovery capsule assigned target set is stale"
        )
    targets = _closed_ids(
        capsule.get("targets"),
        field="skill_id",
        label="discovery capsule.targets",
        expected=set(assigned),
    )
    for skill_id, target in targets.items():
        if set(target) != _DISCOVERY_CAPSULE_TARGET_FIELDS:
            raise ProfessionalCarryForwardError(
                f"discovery capsule target {skill_id} fields are not closed"
            )
    boundary = _closed_ids(
        capsule.get("boundary_catalog"),
        field="skill_id",
        label="discovery capsule.boundary_catalog",
        expected=set(bindings),
    )
    for skill_id, row in boundary.items():
        if set(row) != _DISCOVERY_BOUNDARY_FIELDS:
            raise ProfessionalCarryForwardError(
                f"discovery boundary {skill_id} fields are not closed"
            )
    expected_material_ids = {
        row["skill_id"] for row in expected["material_catalog"]
    }
    _closed_ids(
        capsule.get("material_catalog"),
        field="skill_id",
        label="discovery capsule.material_catalog",
        expected=expected_material_ids,
    )
    if capsule != expected:
        raise ProfessionalCarryForwardError(
            "discovery capsule is extra, missing, duplicate, or stale"
        )
    return capsule


def _normalize_capsule_inputs(
    *,
    bindings: Mapping[str, dict[str, Any]],
    adjacency_contexts: Mapping[str, dict[str, Any]],
    assigned_fresh_target_ids: Sequence[str],
    reviewer_added_requests_by_target: (
        Mapping[str, Sequence[Mapping[str, Any]]] | None
    ),
) -> tuple[list[str], dict[str, list[dict[str, Any]]]]:
    assigned = _normalize_assigned_targets(
        bindings=bindings,
        assigned_fresh_target_ids=assigned_fresh_target_ids,
    )
    raw_added = reviewer_added_requests_by_target or {}
    if not isinstance(raw_added, Mapping):
        raise ProfessionalCarryForwardError(
            "reviewer-added requests must be an object"
        )
    extra_targets = sorted(set(raw_added) - set(assigned))
    if extra_targets:
        raise ProfessionalCarryForwardError(
            "reviewer-added candidates contain extra target assignments: "
            + ", ".join(extra_targets)
        )
    normalized: dict[str, list[dict[str, Any]]] = {}
    for skill_id in assigned:
        values = raw_added.get(skill_id, [])
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
            raise ProfessionalCarryForwardError(
                f"reviewer-added requests for {skill_id} must be an array"
            )
        added: list[dict[str, Any]] = []
        for index, raw in enumerate(values):
            if not isinstance(raw, Mapping) or set(raw) != _REVIEWER_ADDED_REQUEST_FIELDS:
                raise ProfessionalCarryForwardError(
                    f"reviewer-added request {skill_id}[{index}] fields are not closed"
                )
            candidate_id = _require_skill_id(
                raw.get("skill_id"),
                label=f"reviewer-added request {skill_id}[{index}].skill_id",
            )
            reason = raw.get("discovery_reason")
            if not isinstance(reason, str) or not reason.strip():
                raise ProfessionalCarryForwardError(
                    f"reviewer-added request {skill_id}[{index}].discovery_reason must be non-empty"
                )
            added.append(copy.deepcopy(dict(raw)))
        added_ids = [row["skill_id"] for row in added]
        if len(added_ids) != len(set(added_ids)):
            raise ProfessionalCarryForwardError(
                f"reviewer-added requests for {skill_id} contain duplicates"
            )
        added.sort(key=lambda row: row["skill_id"])
        adjacency = adjacency_contexts[skill_id]
        ranking = {
            row["skill_id"]: row
            for row in adjacency["full_catalog_ranking"]
        }
        required_ids = {
            row["skill_id"]
            for row in adjacency["required_candidates"]
        }
        outside = sorted(set(added_ids) - set(ranking))
        if outside:
            raise ProfessionalCarryForwardError(
                f"reviewer-added requests for {skill_id} are absent from full ranking: "
                + ", ".join(outside)
            )
        already_required = sorted(set(added_ids) & required_ids)
        if already_required:
            raise ProfessionalCarryForwardError(
                f"reviewer-added requests for {skill_id} are already packet-required: "
                + ", ".join(already_required)
            )
        for request in added:
            candidate_id = request["skill_id"]
            if request["ranking_evidence"] != ranking[candidate_id]:
                raise ProfessionalCarryForwardError(
                    f"reviewer-added request {skill_id}->{candidate_id} ranking evidence is stale"
                )
            if request["material_fingerprint"] != bindings[candidate_id][
                "content_fingerprint"
            ]:
                raise ProfessionalCarryForwardError(
                    f"reviewer-added request {skill_id}->{candidate_id} material fingerprint is stale"
                )
        normalized[skill_id] = added
    return assigned, normalized


def _project_professional_review_capsule(
    *,
    bindings: Mapping[str, dict[str, Any]],
    adjacency_contexts: Mapping[str, dict[str, Any]],
    assigned: Sequence[str],
    reviewer_added: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, Any]:
    targets: list[dict[str, Any]] = []
    material_ids: set[str] = set(assigned)
    for skill_id in assigned:
        binding = bindings[skill_id]
        required_ids = binding["adjacency"]["required_candidate_ids"]
        added_by_id = {
            row["skill_id"]: row for row in reviewer_added[skill_id]
        }
        added_ids = sorted(added_by_id)
        origin_by_id = {
            **{candidate_id: "packet-required" for candidate_id in required_ids},
            **{candidate_id: "reviewer-added" for candidate_id in added_ids},
        }
        candidate_ids = sorted(origin_by_id)
        material_ids.update(candidate_ids)
        manifest = [
            {
                "skill_id": candidate_id,
                "review_origin": origin_by_id[candidate_id],
                "discovery_reason": (
                    added_by_id[candidate_id]["discovery_reason"]
                    if candidate_id in added_by_id
                    else None
                ),
                "material_fingerprint": bindings[candidate_id][
                    "content_fingerprint"
                ],
            }
            for candidate_id in candidate_ids
        ]
        targets.append(
            {
                "skill_id": skill_id,
                "review_unit_binding": binding[
                    "review_unit_binding"
                ],
                "adjacency": copy.deepcopy(adjacency_contexts[skill_id]),
                "candidate_material_manifest": manifest,
            }
        )
    return {
        "projection_contract": copy.deepcopy(PROFESSIONAL_CAPSULE_CONTRACT),
        "assigned_fresh_target_ids": list(assigned),
        "material_catalog": [
            _candidate_projection_from_binding(bindings[skill_id])
            for skill_id in sorted(material_ids)
        ],
        "targets": targets,
    }


def project_professional_review_capsule(
    *,
    bindings: Mapping[str, dict[str, Any]],
    review_targets: Sequence[dict[str, Any]],
    assigned_fresh_target_ids: Sequence[str],
    reviewer_added_requests_by_target: (
        Mapping[str, Sequence[Mapping[str, Any]]] | None
    ) = None,
) -> dict[str, Any]:
    """Project one exact final capsule from validated request rows."""

    adjacency_contexts = _fresh_adjacency_contexts(
        bindings=bindings,
        review_targets=review_targets,
    )
    assigned, reviewer_added = _normalize_capsule_inputs(
        bindings=bindings,
        adjacency_contexts=adjacency_contexts,
        assigned_fresh_target_ids=assigned_fresh_target_ids,
        reviewer_added_requests_by_target=reviewer_added_requests_by_target,
    )
    capsule = _project_professional_review_capsule(
        bindings=bindings,
        adjacency_contexts=adjacency_contexts,
        assigned=assigned,
        reviewer_added=reviewer_added,
    )
    validate_professional_review_capsule(
        capsule,
        bindings=bindings,
        review_targets=review_targets,
        assigned_fresh_target_ids=assigned,
        reviewer_added_requests_by_target=reviewer_added,
    )
    return capsule


def _closed_ids(
    rows: object,
    *,
    field: str,
    label: str,
    expected: set[str],
) -> dict[str, Mapping[str, Any]]:
    if not isinstance(rows, list):
        raise ProfessionalCarryForwardError(f"{label} must be an array")
    index: dict[str, Mapping[str, Any]] = {}
    duplicates: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            raise ProfessionalCarryForwardError(f"{label} entries must be objects")
        item_id = row.get(field)
        if not isinstance(item_id, str) or not item_id:
            raise ProfessionalCarryForwardError(
                f"{label}.{field} must be a Skill ID"
            )
        if item_id in index:
            duplicates.add(item_id)
        index[item_id] = row
    if duplicates:
        raise ProfessionalCarryForwardError(
            f"{label} contains duplicate IDs: " + ", ".join(sorted(duplicates))
        )
    missing = sorted(expected - set(index))
    extra = sorted(set(index) - expected)
    if missing or extra:
        raise ProfessionalCarryForwardError(
            f"{label} closed set mismatch; missing={missing}; extra={extra}"
        )
    return index


def validate_professional_review_capsule(
    capsule: object,
    *,
    bindings: Mapping[str, dict[str, Any]],
    review_targets: Sequence[dict[str, Any]],
    assigned_fresh_target_ids: Sequence[str],
    reviewer_added_requests_by_target: (
        Mapping[str, Sequence[Mapping[str, Any]]] | None
    ) = None,
) -> dict[str, Any]:
    """Reject extra, missing, duplicate, or stale capsule projections."""

    adjacency_contexts = _fresh_adjacency_contexts(
        bindings=bindings,
        review_targets=review_targets,
    )
    assigned, reviewer_added = _normalize_capsule_inputs(
        bindings=bindings,
        adjacency_contexts=adjacency_contexts,
        assigned_fresh_target_ids=assigned_fresh_target_ids,
        reviewer_added_requests_by_target=reviewer_added_requests_by_target,
    )
    if not isinstance(capsule, dict) or set(capsule) != _CAPSULE_FIELDS:
        raise ProfessionalCarryForwardError("capsule fields are not closed")
    if capsule.get("projection_contract") != PROFESSIONAL_CAPSULE_CONTRACT:
        raise ProfessionalCarryForwardError("capsule projection contract is stale")
    assigned_in_capsule = capsule.get("assigned_fresh_target_ids")
    if not isinstance(assigned_in_capsule, list):
        raise ProfessionalCarryForwardError(
            "capsule assigned_fresh_target_ids must be an array"
        )
    if len(assigned_in_capsule) != len(set(assigned_in_capsule)):
        raise ProfessionalCarryForwardError(
            "capsule assigned_fresh_target_ids contains duplicates"
        )
    if assigned_in_capsule != assigned:
        missing = sorted(set(assigned) - set(assigned_in_capsule))
        extra = sorted(set(assigned_in_capsule) - set(assigned))
        raise ProfessionalCarryForwardError(
            "capsule assigned target set is stale; "
            f"missing={missing}; extra={extra}"
        )
    target_index = _closed_ids(
        capsule.get("targets"),
        field="skill_id",
        label="capsule.targets",
        expected=set(assigned),
    )
    expected_capsule = _project_professional_review_capsule(
        bindings=bindings,
        adjacency_contexts=adjacency_contexts,
        assigned=assigned,
        reviewer_added=reviewer_added,
    )
    expected_target_index = {
        row["skill_id"]: row for row in expected_capsule["targets"]
    }
    expected_catalog_ids = {
        row["skill_id"] for row in expected_capsule["material_catalog"]
    }
    material_index = _closed_ids(
        capsule.get("material_catalog"),
        field="skill_id",
        label="capsule.material_catalog",
        expected=expected_catalog_ids,
    )
    if [row["skill_id"] for row in capsule["material_catalog"]] != sorted(
        expected_catalog_ids
    ):
        raise ProfessionalCarryForwardError(
            "capsule material_catalog must be Skill-sorted"
        )
    if [row["skill_id"] for row in capsule["targets"]] != assigned:
        raise ProfessionalCarryForwardError(
            "capsule targets must be Skill-sorted"
        )
    for skill_id in assigned:
        target = target_index[skill_id]
        expected_target = expected_target_index[skill_id]
        if set(target) != _CAPSULE_TARGET_FIELDS:
            raise ProfessionalCarryForwardError(
                f"capsule target {skill_id} fields are not closed"
            )
        expected_candidate_ids = {
            row["skill_id"]
            for row in expected_target["candidate_material_manifest"]
        }
        manifest_index = _closed_ids(
            target.get("candidate_material_manifest"),
            field="skill_id",
            label=f"capsule target {skill_id} candidate manifest",
            expected=expected_candidate_ids,
        )
        for candidate_id, manifest in manifest_index.items():
            if set(manifest) != _CAPSULE_MANIFEST_FIELDS:
                raise ProfessionalCarryForwardError(
                    f"capsule target {skill_id} candidate manifest fields are not closed"
                )
            if (
                material_index[candidate_id].get("material_fingerprint")
                != manifest.get("material_fingerprint")
            ):
                raise ProfessionalCarryForwardError(
                    f"capsule target {skill_id} candidate {candidate_id} manifest is stale"
                )
        if target != expected_target:
            raise ProfessionalCarryForwardError(
                f"capsule target {skill_id} projection is stale"
            )
    if capsule["material_catalog"] != expected_capsule["material_catalog"]:
        raise ProfessionalCarryForwardError(
            "capsule material_catalog projection is stale"
        )
    return capsule


def professional_review_capsule_cost_proxy(capsule: object) -> dict[str, Any]:
    """Return deterministic size proxies; never claim latency or real token cost."""

    payload = canonical_json_bytes(capsule)
    result: dict[str, Any] = {
        "canonical_json_bytes_proxy": len(payload),
        "o200k_base_tokens_proxy": None,
        "o200k_tokenizer_available": False,
    }
    try:
        import tiktoken  # type: ignore[import-not-found]

        encoding = tiktoken.get_encoding("o200k_base")
    except (ImportError, KeyError, OSError, ValueError):
        return result
    result["o200k_base_tokens_proxy"] = len(
        encoding.encode(payload.decode("utf-8"))
    )
    result["o200k_tokenizer_available"] = True
    return result


def versioned_explicit_source_manifest(
    *,
    contract_version: str,
    source_paths: Sequence[str],
    repository_root: Path,
) -> dict[str, object]:
    """Bind a versioned contract to an explicit repository source manifest."""

    if not isinstance(contract_version, str) or not contract_version.strip():
        raise ProfessionalCarryForwardError("contract_version must be non-empty")
    if (
        not isinstance(source_paths, Sequence)
        or isinstance(source_paths, (str, bytes))
        or not source_paths
        or any(not isinstance(path, str) or not path for path in source_paths)
        or list(source_paths) != sorted(set(source_paths))
    ):
        raise ProfessionalCarryForwardError(
            "source_paths must be non-empty sorted unique repository paths"
        )
    root = repository_root.resolve()
    source_manifest: list[dict[str, str]] = []
    for relative in source_paths:
        path = PurePosixPath(relative)
        if (
            path.is_absolute()
            or not path.parts
            or ".." in path.parts
            or "\\" in relative
        ):
            raise ProfessionalCarryForwardError(
                f"source path is not canonical repository-relative: {relative}"
            )
        source = root.joinpath(*path.parts)
        try:
            resolved = source.resolve(strict=True)
            resolved.relative_to(root)
        except (OSError, ValueError) as exc:
            raise ProfessionalCarryForwardError(
                f"source path is missing or outside the repository: {relative}"
            ) from exc
        if not resolved.is_file():
            raise ProfessionalCarryForwardError(
                f"source path is not a file: {relative}"
            )
        try:
            content = resolved.read_bytes()
        except OSError as exc:
            raise ProfessionalCarryForwardError(
                f"source path is unreadable: {relative}"
            ) from exc
        source_manifest.append(
            {
                "path": relative,
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    payload: dict[str, object] = {
        "contract_version": contract_version,
        "source_manifest": source_manifest,
    }
    payload["aggregate_source_digest"] = canonical_json_sha256(payload)
    return payload
