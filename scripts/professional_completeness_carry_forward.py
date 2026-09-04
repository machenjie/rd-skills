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
from importlib import metadata as importlib_metadata
import json
import re
import unicodedata
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

import expert_panel_contracts as panel_contracts

try:
    from markdown_it import MarkdownIt
except ImportError:  # pragma: no cover - exercised through the fail-closed seam
    MarkdownIt = None

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
_RESPONSIBILITY_FIELDS = set(
    panel_contracts.PROFESSIONAL_SEMANTIC_RESPONSIBILITY_FIELDS
)
_RESPONSIBILITY_REQUIRED_LIST_FIELDS = set(
    panel_contracts.PROFESSIONAL_SEMANTIC_RESPONSIBILITY_REQUIRED_LIST_FIELDS
)
_RESPONSIBILITY_OPTIONAL_LIST_FIELDS = set(
    panel_contracts.PROFESSIONAL_SEMANTIC_RESPONSIBILITY_OPTIONAL_LIST_FIELDS
)
_CURRENTNESS_PROJECTION_VERSION = (
    panel_contracts.PROFESSIONAL_CURRENTNESS_PROJECTION_VERSION
)
_REGISTRY_AUTHORITY_REQUIRED_FIELDS = set(
    panel_contracts.PROFESSIONAL_REGISTRY_AUTHORITY_REQUIRED_FIELDS
)
_REFERENCE_AUTHORITY_FIELDS = set(
    panel_contracts.PROFESSIONAL_REFERENCE_AUTHORITY_FIELDS
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
_HISTORICAL_TARGET_BINDING_FIELDS = _TARGET_BINDING_FIELDS - {
    "registry_authority",
    "reference_authority",
}
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
    "reference_authority",
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

    if "root" not in target and isinstance(target.get("own_material"), Mapping):
        return _canonical_own_material_binding(
            target["own_material"],
            label=str(target.get("skill_id", "target")),
        )
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


def professional_required_expertise_binding(
    target: Mapping[str, Any],
) -> list[str]:
    """Project the exact closed expertise requirement for one target."""

    return _sorted_unique_strings(
        target.get("required_expertise_tags"),
        label="target.required_expertise_tags",
    )


def _normalize_horizontal_text(value: str) -> str:
    value = unicodedata.normalize(
        "NFC", value.replace("\r\n", "\n").replace("\r", "\n")
    )
    return "\n".join(
        re.sub(r"[ \t\f\v]+", " ", line).strip()
        for line in value.split("\n")
    ).strip("\n")


def _normalize_structured_authority(value: object, *, label: str) -> Any:
    """Normalize only deterministic presentation in validated structured data."""

    if value is None or type(value) in {bool, int}:
        return value
    if isinstance(value, str):
        return _normalize_horizontal_text(value)
    if isinstance(value, list):
        return [
            _normalize_structured_authority(
                item, label=f"{label}[{index}]"
            )
            for index, item in enumerate(value)
        ]
    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key:
                raise ProfessionalCarryForwardError(
                    f"{label} keys must be non-empty text"
                )
            normalized_key = unicodedata.normalize("NFC", key)
            if normalized_key in normalized:
                raise ProfessionalCarryForwardError(
                    f"{label} keys collide after Unicode NFC normalization"
                )
            normalized[normalized_key] = _normalize_structured_authority(
                item, label=f"{label}.{normalized_key}"
            )
        return normalized
    raise ProfessionalCarryForwardError(
        f"{label} must contain only canonical JSON values"
    )


def _required_string_list(
    value: object, *, label: str, allow_empty: bool
) -> list[str]:
    if not isinstance(value, list) or (
        not allow_empty and not value
    ):
        raise ProfessionalCarryForwardError(
            f"{label} must be {'a' if allow_empty else 'a non-empty'} string array"
        )
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ProfessionalCarryForwardError(
            f"{label} must contain non-empty strings"
        )
    if len(value) != len(set(value)):
        raise ProfessionalCarryForwardError(
            f"{label} must not contain duplicates"
        )
    return list(value)


def professional_reference_authority_binding(
    target: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Return ordered exact Reference Contract v2 currentness authority."""

    value = target.get("reference_authority")
    if not isinstance(value, list):
        raise ProfessionalCarryForwardError(
            "target.reference_authority must be an array"
        )
    records: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for index, raw in enumerate(value):
        label = f"target.reference_authority[{index}]"
        if not isinstance(raw, Mapping) or set(raw) != _REFERENCE_AUTHORITY_FIELDS:
            raise ProfessionalCarryForwardError(
                f"{label} must contain one exact Reference Contract v2 record"
            )
        path = raw.get("path")
        if not _is_canonical_repository_path(path):
            raise ProfessionalCarryForwardError(
                f"{label}.path must be repository-relative"
            )
        if path in seen_paths:
            raise ProfessionalCarryForwardError(
                f"{label}.path duplicates {path!r}"
            )
        seen_paths.add(str(path))
        for field in ("type", "load_when", "do_not_load_when"):
            field_value = raw.get(field)
            if (
                not isinstance(field_value, str)
                or not field_value.strip()
                or "\n" in field_value
                or "\r" in field_value
            ):
                raise ProfessionalCarryForwardError(
                    f"{label}.{field} must be non-empty single-line text"
                )
        for field in ("required_by", "required_output"):
            _required_string_list(
                raw.get(field), label=f"{label}.{field}", allow_empty=False
            )
        records.append(
            _normalize_structured_authority(raw, label=label)
        )
    return records


def _responsibility_from_registry_authority(
    authority: Mapping[str, Any],
) -> dict[str, Any]:
    responsibility: dict[str, Any] = {}
    for field in sorted(_RESPONSIBILITY_REQUIRED_LIST_FIELDS):
        responsibility[field] = _required_string_list(
            authority.get(field),
            label=f"target.registry_authority.{field}",
            allow_empty=False,
        )
    for field in sorted(_RESPONSIBILITY_OPTIONAL_LIST_FIELDS):
        responsibility[field] = _required_string_list(
            authority.get(field, []),
            label=f"target.registry_authority.{field}",
            allow_empty=True,
        )
    for field in ("group", "content_class", "delivery_scope"):
        value = authority.get(field)
        if value is not None and (
            not isinstance(value, str) or not value.strip()
        ):
            raise ProfessionalCarryForwardError(
                f"target.registry_authority.{field} must be text or null"
            )
        responsibility[field] = value
    task_routable = authority.get("task_routable")
    if task_routable is not None and type(task_routable) is not bool:
        raise ProfessionalCarryForwardError(
            "target.registry_authority.task_routable must be boolean or null"
        )
    responsibility["task_routable"] = task_routable
    if set(responsibility) != _RESPONSIBILITY_FIELDS:
        raise ProfessionalCarryForwardError(
            "target Registry responsibility authority is incomplete"
        )
    return _normalize_structured_authority(
        responsibility, label="target.registry_authority.responsibility"
    )


def professional_registry_authority_binding(
    target: Mapping[str, Any],
) -> dict[str, Any]:
    """Return the complete canonical Registry row used by currentness."""

    raw = target.get("registry_authority")
    if not isinstance(raw, Mapping):
        raise ProfessionalCarryForwardError(
            "target.registry_authority must be a complete Registry row"
        )
    missing = sorted(_REGISTRY_AUTHORITY_REQUIRED_FIELDS - set(raw))
    if missing:
        raise ProfessionalCarryForwardError(
            "target.registry_authority lacks required fields: "
            + ", ".join(missing)
        )
    skill_id = _require_skill_id(
        target.get("skill_id"), label="target.skill_id"
    )
    if raw.get("name") != skill_id:
        raise ProfessionalCarryForwardError(
            "target.registry_authority.name must match target.skill_id"
        )
    if not _is_canonical_repository_path(raw.get("path")):
        raise ProfessionalCarryForwardError(
            "target.registry_authority.path must be repository-relative"
        )
    expertise = professional_required_expertise_binding(target)
    if raw.get("required_expertise_tags") != expertise:
        raise ProfessionalCarryForwardError(
            "target Registry and target expertise authority drift"
        )
    reference_authority = professional_reference_authority_binding(target)
    normalized = _normalize_structured_authority(
        raw, label="target.registry_authority"
    )
    if normalized.get("reference_index") != reference_authority:
        raise ProfessionalCarryForwardError(
            "target Registry reference_index and reference_authority drift"
        )

    own = professional_own_material_binding(target)
    registry_directory = PurePosixPath(str(normalized["path"]))
    expected_paths = [
        (registry_directory / reference["path"]).as_posix()
        for reference in reference_authority
    ]
    material_paths = [
        reference["path"] for reference in own["indexed_references"]
    ]
    if sorted(expected_paths) != material_paths:
        raise ProfessionalCarryForwardError(
            "target Reference authority and indexed material coverage drift"
        )

    registry = target.get("registry")
    if not isinstance(registry, Mapping) or set(registry) not in (
        {"path", "responsibility_contract"},
        {"path", "entry_fingerprint", "responsibility_contract"},
    ):
        raise ProfessionalCarryForwardError(
            "target.registry must contain the compatibility Registry binding"
        )
    if not _is_canonical_repository_path(registry.get("path")):
        raise ProfessionalCarryForwardError(
            "target.registry.path must be repository-relative"
        )
    responsibility = _responsibility_from_registry_authority(normalized)
    compatibility = registry.get("responsibility_contract")
    if not isinstance(compatibility, Mapping):
        raise ProfessionalCarryForwardError(
            "target.registry.responsibility_contract must be an object"
        )
    if _normalize_structured_authority(
        compatibility,
        label="target.registry.responsibility_contract",
    ) != responsibility:
        raise ProfessionalCarryForwardError(
            "target Registry responsibility compatibility projection drift"
        )
    return normalized


def professional_registry_responsibility_binding(
    target: Mapping[str, Any],
) -> dict[str, Any]:
    """Derive the compatibility Registry view from complete authority."""

    authority = professional_registry_authority_binding(target)
    registry = target["registry"]
    return {
        "path": registry["path"],
        "responsibility_contract": _responsibility_from_registry_authority(
            authority
        ),
    }


_AUTHENTICATED_SOURCE_COMMENT_RE = re.compile(
    r"^<!--\s*(?:"
    r"rd-semantic-id:v2\s+finding=[a-z0-9_]+\s+"
    r"rule=[a-z0-9][a-z0-9/-]*\s+occurrence=[a-z0-9][a-z0-9-]*"
    r"|(?:BEGIN|END)\s+CHANGEFORGE\s+[A-Za-z0-9][A-Za-z0-9 _:/.-]*"
    r"|[a-z0-9-]+-contract:[BE]"
    r")\s*-->[ \t]*$"
)


def _frontmatter_scalar(value: str) -> str | None:
    value = value.strip()
    if not value:
        return None
    if value.startswith('"') and value.endswith('"'):
        try:
            decoded = json.loads(value)
        except (TypeError, ValueError):
            return None
        return decoded if isinstance(decoded, str) else None
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    if value[:1] in "[{&*!>|" or value.startswith(("!!", "<<:")):
        return None
    return value


def _structured_frontmatter_projection(
    lines: Sequence[str],
) -> dict[str, Any] | None:
    allowed_fields = {"name", "description"}
    values: dict[str, str] = {}
    for raw_line in lines:
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line[:1].isspace():
            return None
        match = re.fullmatch(
            r"([A-Za-z_][A-Za-z0-9_-]*)[ \t]*:[ \t]*(.*)",
            raw_line,
        )
        if (
            match is None
            or match.group(1) not in allowed_fields
            or match.group(1) in values
        ):
            return None
        scalar = _frontmatter_scalar(match.group(2))
        if scalar is None:
            return None
        values[match.group(1)] = _normalize_horizontal_text(scalar)
    return values if values else None


_MARKDOWN_DISTRIBUTION_VERSIONS = {
    "markdown-it-py": "4.2.0",
    "mdurl": "0.1.2",
}


def _verified_professional_markdown_parser() -> Any:
    for distribution, expected in _MARKDOWN_DISTRIBUTION_VERSIONS.items():
        try:
            actual = importlib_metadata.version(distribution)
        except importlib_metadata.PackageNotFoundError as exc:
            raise ProfessionalCarryForwardError(
                f"Professional currentness requires {distribution}=={expected}"
            ) from exc
        if actual != expected:
            raise ProfessionalCarryForwardError(
                "Professional currentness requires "
                f"{distribution}=={expected}; found {actual}"
            )
    if MarkdownIt is None:
        raise ProfessionalCarryForwardError(
            "Professional currentness requires markdown-it-py==4.2.0"
        )
    return MarkdownIt(
        "commonmark",
        {
            "html": True,
            "linkify": False,
            "typographer": False,
            "breaks": False,
        },
    ).enable("table")


def _parse_professional_markdown(value: str) -> tuple[list[Any], dict[str, Any]]:
    parser = _verified_professional_markdown_parser()
    environment: dict[str, Any] = {}
    try:
        tokens = parser.parse(value, environment)
    except Exception as exc:
        raise ProfessionalCarryForwardError(
            "Professional currentness Markdown parsing failed closed"
        ) from exc
    return tokens, environment


def _empty_token_attrs(token: Any) -> bool:
    return getattr(token, "attrs", None) in (None, {})


def _plain_token_state(token: Any, *, nesting: int, block: bool) -> bool:
    return (
        getattr(token, "nesting", None) == nesting
        and getattr(token, "block", None) is block
        and getattr(token, "meta", None) == {}
        and _empty_token_attrs(token)
        and isinstance(getattr(token, "level", None), int)
        and isinstance(getattr(token, "hidden", None), bool)
    )


def _canonical_token_attrs(
    token: Any, *, required: set[str], allowed: set[str]
) -> list[list[str]] | None:
    attrs = getattr(token, "attrs", None)
    if not isinstance(attrs, Mapping) or not required <= set(attrs) <= allowed:
        return None
    if not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in attrs.items()
    ):
        return None
    return [[key, attrs[key]] for key in sorted(attrs)]


def _append_inline_fragment(
    target: list[dict[str, Any]], fragment: dict[str, Any]
) -> None:
    if fragment["type"] == "space" and target and target[-1]["type"] == "space":
        return
    if fragment["type"] == "text" and target and target[-1]["type"] == "text":
        target[-1]["value"] += fragment["value"]
        return
    target.append(fragment)


def _append_text_fragments(target: list[dict[str, Any]], value: str) -> None:
    for fragment in re.split(r"([ \t\f\v]+)", unicodedata.normalize("NFC", value)):
        if not fragment:
            continue
        if re.fullmatch(r"[ \t\f\v]+", fragment):
            _append_inline_fragment(target, {"type": "space"})
        else:
            _append_inline_fragment(target, {"type": "text", "value": fragment})


def _project_inline_tokens(tokens: object) -> list[dict[str, Any]] | None:
    if not isinstance(tokens, list):
        return None
    root: list[dict[str, Any]] = []
    containers: list[list[dict[str, Any]]] = [root]
    stack: list[tuple[str, str, str]] = []
    for token in tokens:
        token_type = getattr(token, "type", None)
        level = getattr(token, "level", None)
        if (
            getattr(token, "meta", None) != {}
            or getattr(token, "block", None) is not False
        ):
            return None
        if (
            getattr(token, "map", None) is not None
            or getattr(token, "hidden", None) is not False
        ):
            return None
        if token_type == "text":
            if (
                not _plain_token_state(token, nesting=0, block=False)
                or level != len(stack)
                or getattr(token, "children", None) is not None
                or getattr(token, "markup", None) != ""
                or getattr(token, "info", None) != ""
                or not isinstance(getattr(token, "content", None), str)
            ):
                return None
            _append_text_fragments(containers[-1], token.content)
            continue
        if token_type == "softbreak":
            if (
                not _plain_token_state(token, nesting=0, block=False)
                or level != len(stack)
                or getattr(token, "children", None) is not None
                or getattr(token, "content", None) != ""
                or getattr(token, "markup", None) != ""
                or getattr(token, "info", None) != ""
            ):
                return None
            _append_inline_fragment(containers[-1], {"type": "space"})
            continue
        if token_type == "hardbreak":
            if (
                not _plain_token_state(token, nesting=0, block=False)
                or level != len(stack)
                or getattr(token, "children", None) is not None
                or getattr(token, "content", None) != ""
            ):
                return None
            _append_inline_fragment(containers[-1], {"type": "hardbreak"})
            continue
        if token_type == "code_inline":
            if (
                not _plain_token_state(token, nesting=0, block=False)
                or level != len(stack)
                or getattr(token, "children", None) is not None
                or not isinstance(getattr(token, "content", None), str)
                or re.fullmatch(r"`+", getattr(token, "markup", "")) is None
                or getattr(token, "info", None) != ""
            ):
                return None
            _append_inline_fragment(
                containers[-1], {"type": "inline-code", "value": token.content}
            )
            continue
        if token_type in {"em_open", "strong_open"}:
            expected_markup = {"em_open": {"*", "_"}, "strong_open": {"**", "__"}}
            if (
                not _plain_token_state(token, nesting=1, block=False)
                or level != len(stack)
                or getattr(token, "children", None) is not None
                or getattr(token, "content", None) != ""
                or getattr(token, "markup", None) not in expected_markup[token_type]
                or getattr(token, "info", None) != ""
            ):
                return None
            stack.append((token_type.removesuffix("_open"), token.markup, "format"))
            continue
        if token_type in {"em_close", "strong_close"}:
            expected_kind = token_type.removesuffix("_close")
            if (
                not stack
                or stack[-1][0] != expected_kind
                or stack[-1][2] != "format"
                or not _plain_token_state(token, nesting=-1, block=False)
                or level != len(stack) - 1
                or getattr(token, "markup", None) != stack[-1][1]
                or getattr(token, "children", None) is not None
                or getattr(token, "content", None) != ""
                or getattr(token, "info", None) != ""
            ):
                return None
            stack.pop()
            continue
        if token_type == "link_open":
            attrs = _canonical_token_attrs(
                token, required={"href"}, allowed={"href", "title"}
            )
            markup = getattr(token, "markup", None)
            info = getattr(token, "info", None)
            kind = "autolink" if (markup, info) == ("autolink", "auto") else "direct"
            if kind == "direct" and (markup, info) != ("", ""):
                return None
            if (
                attrs is None
                or getattr(token, "nesting", None) != 1
                or level != len(stack)
                or getattr(token, "block", None) is not False
                or getattr(token, "meta", None) != {}
                or getattr(token, "children", None) is not None
                or getattr(token, "content", None) != ""
                or getattr(token, "map", None) is not None
                or getattr(token, "hidden", None) is not False
            ):
                return None
            node = {"type": "link", "kind": kind, "attrs": attrs, "children": []}
            containers[-1].append(node)
            containers.append(node["children"])
            stack.append(("link", f"{markup}\0{info}", "container"))
            continue
        if token_type == "link_close":
            markup = getattr(token, "markup", None)
            info = getattr(token, "info", None)
            if (
                not stack
                or stack[-1][0] != "link"
                or stack[-1][2] != "container"
                or stack[-1][1] != f"{markup}\0{info}"
                or not _plain_token_state(token, nesting=-1, block=False)
                or level != len(stack) - 1
                or getattr(token, "children", None) is not None
                or getattr(token, "content", None) != ""
            ):
                return None
            stack.pop()
            containers.pop()
            continue
        if token_type == "image":
            attrs = _canonical_token_attrs(
                token, required={"src", "alt"}, allowed={"src", "alt", "title"}
            )
            children = _project_inline_tokens(getattr(token, "children", None))
            if (
                attrs is None
                or children is None
                or getattr(token, "nesting", None) != 0
                or level != len(stack)
                or getattr(token, "block", None) is not False
                or getattr(token, "meta", None) != {}
                or getattr(token, "map", None) is not None
                or getattr(token, "hidden", None) is not False
                or getattr(token, "markup", None) != ""
                or getattr(token, "info", None) != ""
            ):
                return None
            _append_inline_fragment(
                containers[-1],
                {"type": "image", "attrs": attrs, "children": children},
            )
            continue
        return None
    if stack or len(containers) != 1:
        return None
    return root


def _block_open_projection(token: Any) -> tuple[str, dict[str, Any]] | None:
    token_type = getattr(token, "type", None)
    if not _plain_token_state(token, nesting=1, block=True):
        return None
    if (
        getattr(token, "children", None) is not None
        or getattr(token, "content", None) != ""
    ):
        return None
    if getattr(token, "info", None) != "":
        return None
    if (
        token_type == "paragraph_open"
        and getattr(token, "tag", None) == "p"
        and getattr(token, "markup", None) == ""
    ):
        return "paragraph", {"type": "paragraph", "children": []}
    if token_type == "heading_open" and re.fullmatch(
        r"h[1-6]", getattr(token, "tag", "")
    ):
        level = int(token.tag[1:])
        markup = getattr(token, "markup", None)
        if not (
            (isinstance(markup, str) and markup == "#" * level)
            or (markup == "=" and level == 1)
            or (markup == "-" and level == 2)
        ):
            return None
        return "heading", {
            "type": "heading",
            "level": level,
            "children": [],
        }
    if (
        token_type == "blockquote_open"
        and getattr(token, "tag", None) == "blockquote"
        and getattr(token, "markup", None) == ">"
    ):
        return "blockquote", {"type": "blockquote", "children": []}
    if (
        token_type == "bullet_list_open"
        and getattr(token, "tag", None) == "ul"
        and getattr(token, "markup", None) in {"-", "+", "*"}
    ):
        return "bullet_list", {"type": "bullet-list", "children": []}
    if (
        token_type == "list_item_open"
        and getattr(token, "tag", None) == "li"
        and getattr(token, "markup", None) in {"-", "+", "*"}
    ):
        return "list_item", {"type": "list-item", "children": []}
    return None


def _project_professional_markdown_tokens(
    tokens: object, environment: object
) -> dict[str, Any] | None:
    if not isinstance(tokens, list) or environment != {}:
        return None
    document = {"type": "document", "children": []}
    containers: list[tuple[str, list[dict[str, Any]]]] = [
        ("document", document["children"])
    ]
    for token in tokens:
        token_type = getattr(token, "type", None)
        depth = len(containers) - 1
        opened = _block_open_projection(token)
        if opened is not None:
            kind, node = opened
            parent = containers[-1][0]
            allowed_parent = (
                parent == "bullet_list"
                if kind == "list_item"
                else parent in {"document", "blockquote", "list_item"}
            )
            if not allowed_parent or token.level != depth:
                return None
            containers[-1][1].append(node)
            containers.append((kind, node["children"]))
            continue
        close_kinds = {
            "paragraph_close": "paragraph",
            "heading_close": "heading",
            "blockquote_close": "blockquote",
            "bullet_list_close": "bullet_list",
            "list_item_close": "list_item",
        }
        if token_type in close_kinds:
            expected = close_kinds[token_type]
            if (
                len(containers) == 1
                or containers[-1][0] != expected
                or not _plain_token_state(token, nesting=-1, block=True)
                or token.level != depth - 1
                or getattr(token, "children", None) is not None
                or getattr(token, "content", None) != ""
                or getattr(token, "info", None) != ""
            ):
                return None
            containers.pop()
            continue
        if token_type == "inline":
            if (
                containers[-1][0] not in {"paragraph", "heading"}
                or containers[-1][1]
                or not _plain_token_state(token, nesting=0, block=True)
                or token.level != depth
                or getattr(token, "tag", None) != ""
                or getattr(token, "markup", None) != ""
                or getattr(token, "info", None) != ""
            ):
                return None
            inline = _project_inline_tokens(getattr(token, "children", None))
            if inline is None:
                return None
            containers[-1][1].append({"type": "inline", "children": inline})
            continue
        if token_type in {"fence", "code_block", "hr"}:
            if (
                containers[-1][0] not in {"document", "blockquote", "list_item"}
                or not _plain_token_state(token, nesting=0, block=True)
                or token.level != depth
                or getattr(token, "children", None) is not None
            ):
                return None
            if token_type == "fence":
                if (
                    getattr(token, "tag", None) != "code"
                    or re.fullmatch(
                        r"(?:`{3,}|~{3,})", getattr(token, "markup", "")
                    )
                    is None
                    or not isinstance(getattr(token, "info", None), str)
                    or not isinstance(getattr(token, "content", None), str)
                ):
                    return None
                node = {
                    "type": "fenced-code",
                    "info": token.info,
                    "content": token.content,
                }
            elif token_type == "code_block":
                if (
                    getattr(token, "tag", None) != "code"
                    or getattr(token, "markup", None) != ""
                    or getattr(token, "info", None) != ""
                    or not isinstance(getattr(token, "content", None), str)
                ):
                    return None
                node = {"type": "indented-code", "content": token.content}
            else:
                if (
                    getattr(token, "tag", None) != "hr"
                    or not isinstance(getattr(token, "markup", None), str)
                    or getattr(token, "info", None) != ""
                    or getattr(token, "content", None) != ""
                ):
                    return None
                node = {"type": "thematic-break"}
            containers[-1][1].append(node)
            continue
        return None
    if len(containers) != 1:
        return None
    return document


def _remove_authenticated_source_markers(
    value: str, tokens: Sequence[Any]
) -> str:
    marker_lines: set[int] = set()
    for token in tokens:
        token_map = getattr(token, "map", None)
        content = getattr(token, "content", None)
        if (
            getattr(token, "type", None) == "html_block"
            and getattr(token, "level", None) == 0
            and getattr(token, "nesting", None) == 0
            and getattr(token, "block", None) is True
            and getattr(token, "meta", None) == {}
            and _empty_token_attrs(token)
            and isinstance(token_map, list)
            and len(token_map) == 2
            and token_map[1] == token_map[0] + 1
            and isinstance(content, str)
            and _AUTHENTICATED_SOURCE_COMMENT_RE.fullmatch(
                content[:-1] if content.endswith("\n") else content
            )
        ):
            marker_lines.add(token_map[0])
    if not marker_lines:
        return value
    return "".join(
        line
        for index, line in enumerate(value.splitlines(keepends=True))
        if index not in marker_lines
    )


def _opaque_document(value: str) -> dict[str, Any]:
    return {"type": "opaque-document", "value": value}


def _parse_after_authenticated_marker_removal(
    value: str,
) -> tuple[str, list[Any], dict[str, Any]]:
    initial_tokens, _initial_environment = _parse_professional_markdown(value)
    retained = _remove_authenticated_source_markers(value, initial_tokens)
    tokens, environment = _parse_professional_markdown(retained)
    return retained, tokens, environment


def professional_markdown_currentness_projection(
    markdown: str,
) -> list[dict[str, Any]]:
    """Project a closed CommonMark token subset without prose inference."""

    if not isinstance(markdown, str):
        raise ProfessionalCarryForwardError(
            "Professional material content must be text"
        )
    normalized = unicodedata.normalize(
        "NFC", markdown.replace("\r\n", "\n").replace("\r", "\n")
    )
    projection: list[dict[str, Any]] = []
    source_lines = normalized.splitlines(keepends=True)
    body = normalized

    if source_lines and source_lines[0].rstrip("\n") == "---":
        end = next(
            (
                position
                for position in range(1, len(source_lines))
                if source_lines[position].rstrip("\n") == "---"
            ),
            None,
        )
        if end is None:
            retained, _tokens, _environment = (
                _parse_after_authenticated_marker_removal(normalized)
            )
            return [_opaque_document(retained)]
        frontmatter_lines = [
            line.rstrip("\n") for line in source_lines[1:end]
        ]
        structured = _structured_frontmatter_projection(frontmatter_lines)
        if structured is None:
            retained, _tokens, _environment = (
                _parse_after_authenticated_marker_removal(normalized)
            )
            return [_opaque_document(retained)]
        projection.append({"type": "frontmatter", "value": structured})
        body = "".join(source_lines[end + 1 :])

    body, tokens, environment = _parse_after_authenticated_marker_removal(
        body
    )
    document = _project_professional_markdown_tokens(tokens, environment)
    if document is None:
        projection.append(_opaque_document(body))
    else:
        projection.append(document)
    return projection


def professional_material_currentness_projection(
    record: object, *, label: str
) -> dict[str, Any]:
    material = _canonical_material_record(record, label=label)
    return {
        "path": material["path"],
        "markdown": professional_markdown_currentness_projection(
            material["content"]
        ),
    }


def professional_candidate_currentness_projection(
    target: Mapping[str, Any],
) -> dict[str, Any]:
    """Project only conservative package material used for currentness."""

    skill_id = _require_skill_id(
        target.get("skill_id"), label="target.skill_id"
    )
    layer = _require_skill_id(
        target.get("layer"), label=f"{skill_id}.layer"
    )
    own = professional_own_material_binding(target)
    registry_authority = professional_registry_authority_binding(target)
    reference_authority = professional_reference_authority_binding(target)
    expertise = professional_required_expertise_binding(target)
    return {
        "contract_version": _CURRENTNESS_PROJECTION_VERSION,
        "skill_id": skill_id,
        "layer": layer,
        "materials": {
            "root": professional_material_currentness_projection(
                own["root"], label=f"{skill_id}.root"
            ),
            "indexed_references": [
                professional_material_currentness_projection(
                    reference,
                    label=f"{skill_id}.indexed_references[{index}]",
                )
                for index, reference in enumerate(
                    own["indexed_references"]
                )
            ],
        },
        "registry_authority": registry_authority,
        "reference_authority": reference_authority,
        "required_expertise_tags": expertise,
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
    professional_registry_authority_binding(target)
    professional_reference_authority_binding(target)
    return {
        "skill_id": skill_id,
        "layer": layer,
        "own_material": professional_own_material_binding(target),
        "registry": professional_registry_responsibility_binding(target),
        "registry_authority": copy.deepcopy(target["registry_authority"]),
        "reference_authority": copy.deepcopy(target["reference_authority"]),
        "required_expertise_tags": professional_required_expertise_binding(target),
    }


def _historical_candidate_material_binding(
    target: Mapping[str, Any],
) -> dict[str, Any]:
    """Reproduce the exact pre-currentness raw material projection."""

    skill_id = _require_skill_id(
        target.get("skill_id"), label="target.skill_id"
    )
    layer = _require_skill_id(
        target.get("layer"), label=f"{skill_id}.layer"
    )
    registry = target.get("registry")
    if not isinstance(registry, dict) or set(registry) not in (
        {"path", "responsibility_contract"},
        {"path", "entry_fingerprint", "responsibility_contract"},
    ):
        raise ProfessionalCarryForwardError(
            "historical target.registry fields are invalid"
        )
    if not _is_canonical_repository_path(registry.get("path")):
        raise ProfessionalCarryForwardError(
            "historical target.registry.path must be repository-relative"
        )
    responsibility = registry.get("responsibility_contract")
    if not isinstance(responsibility, dict):
        raise ProfessionalCarryForwardError(
            "historical target responsibility contract must be an object"
        )
    return {
        "skill_id": skill_id,
        "layer": layer,
        "own_material": professional_own_material_binding(target),
        "registry": {
            "path": registry["path"],
            "responsibility_contract": copy.deepcopy(responsibility),
        },
        "required_expertise_tags": professional_required_expertise_binding(
            target
        ),
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
    """Build separate raw-content and conservative currentness bindings."""

    target_index = _canonical_target_index(targets)
    candidate_materials = {
        skill_id: professional_candidate_material_binding(target)
        for skill_id, target in target_index.items()
    }
    content_fingerprints = {
        skill_id: canonical_json_sha256(material)
        for skill_id, material in candidate_materials.items()
    }
    candidate_currentness_projections = {
        skill_id: professional_candidate_currentness_projection(target)
        for skill_id, target in target_index.items()
    }
    candidate_fingerprints = {
        skill_id: canonical_json_sha256(binding)
        for skill_id, binding in candidate_currentness_projections.items()
    }
    bindings: dict[str, dict[str, Any]] = {}
    for skill_id in sorted(target_index):
        target = target_index[skill_id]
        own_material = candidate_materials[skill_id]["own_material"]
        registry = candidate_materials[skill_id]["registry"]
        registry_authority = candidate_materials[skill_id][
            "registry_authority"
        ]
        reference_authority = candidate_materials[skill_id][
            "reference_authority"
        ]
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
            "registry_authority": registry_authority,
            "reference_authority": reference_authority,
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
        skill_id: _historical_candidate_material_binding(target)
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
        expected_fields = (
            _HISTORICAL_TARGET_BINDING_FIELDS
            if historical_content
            else _TARGET_BINDING_FIELDS
        )
        if not isinstance(binding, dict) or set(binding) != expected_fields:
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
        registry = (
            _historical_candidate_material_binding(binding)["registry"]
            if historical_content
            else professional_registry_responsibility_binding(binding)
        )
        expertise = professional_required_expertise_binding(binding)
        adjacency = _canonical_adjacency_review_binding(
            binding.get("adjacency")
        )
        content_projection: dict[str, Any] = {
            "skill_id": key,
            "layer": binding["layer"],
            "own_material": own,
            "registry": registry,
            "required_expertise_tags": expertise,
        }
        if not historical_content:
            professional_registry_authority_binding(binding)
            professional_reference_authority_binding(binding)
            content_projection["registry_authority"] = copy.deepcopy(
                binding["registry_authority"]
            )
            content_projection["reference_authority"] = copy.deepcopy(
                binding["reference_authority"]
            )
        if binding.get("content_fingerprint") != canonical_json_sha256(
            content_projection
        ):
            raise ProfessionalCarryForwardError(
                f"binding {key}.content_fingerprint is stale"
            )
        currentness_projection = (
            None
            if historical_content
            else professional_candidate_currentness_projection(binding)
        )
        candidate_fingerprint = (
            binding["content_fingerprint"]
            if historical_content
            else canonical_json_sha256(currentness_projection)
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
    """Create the material-only compact baseline consumed by carry planning."""

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
    candidate_material_bindings = {
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
                candidate_id: candidate_material_bindings[candidate_id]
                for candidate_id in required_ids
            },
            "reviewer_added_candidate_ids_union": reviewer_added_ids,
            "reviewer_added_candidate_material_bindings": {
                candidate_id: candidate_material_bindings[candidate_id]
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

    The plan compares conservative material bindings only.  Raw content digests
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
        "registry_authority": copy.deepcopy(
            binding["registry_authority"]
        ),
        "reference_authority": copy.deepcopy(
            binding["reference_authority"]
        ),
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
        "reference_authority": copy.deepcopy(
            binding["reference_authority"]
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
