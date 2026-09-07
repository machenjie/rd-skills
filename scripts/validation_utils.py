#!/usr/bin/env python3
"""Shared validation helpers for rd-skills authoring contracts."""

from __future__ import annotations

import copy
import base64
import binascii
import hashlib
import io
import subprocess
import re
import shlex
import sys
import json
import tokenize
import unicodedata
from fnmatch import fnmatchcase
from functools import lru_cache
from itertools import combinations
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any, Iterable

try:  # PyYAML is optional; the fallback covers the repository registries.
    import yaml as _yaml
except Exception:  # pragma: no cover - depends on local environment
    _yaml = None


ROOT = Path(__file__).resolve().parents[1]
AFFECTED_CONTEXT_ENV = "CHANGEFORGE_AFFECTED_CONTEXT"
AFFECTED_SOURCE_REPOSITORY_ENV = "CHANGEFORGE_AFFECTED_SOURCE_REPOSITORY"
FOUNDATION_DECISION_CARD_MODEL = "foundation-decision-card-v1"
FOUNDATION_DECISION_CARD_FRONT_LINES = 60
FOUNDATION_DECISION_RULE_MIN = 3
FOUNDATION_DECISION_RULE_MAX = 8
# Built Professional and Domain roots start after route-once and receive the
# bounded assignment inputs. Registry routing and source Required Inputs stay
# authoritative without repeating them in Task, Analysis, or Review context.
PROFESSIONAL_BUILT_KERNEL_HEADINGS = (
    "Role",
    "Professional Decision Rules",
    "Stop / Escalation Conditions",
    "Output Contract",
)
_FOUNDATION_DECISION_VERB_RE = re.compile(
    r"\b(?:choose|compare|derive|define|detect|enforce|gate|inspect|map|preserve|"
    r"prove|record|reject|require|route|select|stop|validate|verify|avoid|"
    r"escalate|isolate|bound|classify|measure|reconcile)\b",
    re.IGNORECASE,
)
_FOUNDATION_RULE_CONTEXT_RE = re.compile(
    r"\b(?:if|when|unless|until|before|after|while|where|only|without|otherwise|"
    r"rather\s+than|because|so\s+that|according\s+to|derived\s+from|evidence|proof|"
    r"source|contract|policy|authority|owner|constraint|boundary|risk|failure|harm|"
    r"unknown|invariant|compatibility|consequence|recovery|rollback|reject|omit|"
    r"cannot|must\s+not|do\s+not|instead)\b",
    re.IGNORECASE,
)
_FOUNDATION_GENERIC_DECISION_TOKENS = frozenset(
    {
        "apply", "boundary", "choose", "current", "decision", "evidence",
        "first", "inspect", "invariant", "keep", "limits", "named",
        "preserve", "proof", "residual", "return", "risk", "selected",
        "source", "using", "verify", "with",
    }
)
_FOUNDATION_H2_RE = re.compile(r"^##\s+(.+?)\s*#*\s*$")
MARKDOWN_ANY_LIST_ITEM_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<marker>[-*+]|\d+[.)])"
    r"(?P<spacing>[ \t]+)(?P<text>.+?)\s*$"
)
SEMANTIC_ID_COMPONENT_PATTERN = r"[a-z][a-z0-9]*(?:[._/-][a-z0-9]+)*"
SEMANTIC_ID_COMPONENT_RE = re.compile(rf"^{SEMANTIC_ID_COMPONENT_PATTERN}$")
SEMANTIC_ID_FINDINGS_BY_AXIS = {
    "reference": frozenset(
        {
            "unconditional_absolute_candidate",
            "fixed_number_candidate",
            "exact_normalized_duplicate_block",
            "templated_block_candidate",
        }
    ),
    "root": frozenset(
        {
            "unconditional_mechanism_candidate",
            "fixed_duration_threshold_status_candidate",
            "fixed_vendor_tool_candidate",
            "mandatory_artifact_candidate",
            "tutorial_explanatory_density_candidate",
            "long_root_example_candidate",
            "context_free_organization_policy_candidate",
        }
    ),
}
SEMANTIC_ID_GROUP_FINDINGS = frozenset(
    {"exact_normalized_duplicate_block", "templated_block_candidate"}
)
SEMANTIC_ID_MARKER_HTML_RE = re.compile(
    rf"^\s*<!-- rd-semantic-id:v2 finding=(?P<finding>{SEMANTIC_ID_COMPONENT_PATTERN}) "
    rf"rule=(?P<rule>{SEMANTIC_ID_COMPONENT_PATTERN}) "
    rf"occurrence=(?P<occurrence>{SEMANTIC_ID_COMPONENT_PATTERN}) -->\s*$"
)
SEMANTIC_ID_MARKER_YAML_RE = re.compile(
    rf"^\s*# rd-semantic-id:v2 finding=(?P<finding>{SEMANTIC_ID_COMPONENT_PATTERN}) "
    rf"rule=(?P<rule>{SEMANTIC_ID_COMPONENT_PATTERN}) "
    rf"occurrence=(?P<occurrence>{SEMANTIC_ID_COMPONENT_PATTERN})\s*$"
)
# Build-time stripping retains the retired v1 form only as a leakage guard for
# historical/synthetic inputs. Semantic collection accepts v2 exclusively.
SEMANTIC_ID_LEGACY_MARKER_HTML_RE = re.compile(
    rf"^\s*<!-- rd-semantic-id:v1 rule={SEMANTIC_ID_COMPONENT_PATTERN} "
    rf"occurrence={SEMANTIC_ID_COMPONENT_PATTERN} -->\s*$"
)
SEMANTIC_ID_LEGACY_MARKER_YAML_RE = re.compile(
    rf"^\s*# rd-semantic-id:v1 rule={SEMANTIC_ID_COMPONENT_PATTERN} "
    rf"occurrence={SEMANTIC_ID_COMPONENT_PATTERN}\s*$"
)
SEMANTIC_ID_MAX_LENGTH = 96


def semantic_identity_projection(
    source: str,
    *,
    owner: str,
    axis: str,
) -> dict[str, object]:
    """Return marker-free visible text plus strict source-owned semantic markers.

    Marker lines are replaced by blank lines so all downstream source locations
    remain physical-source locations. The original source remains the provenance
    and build-freshness input; callers explicitly choose this projection only for
    authored-content semantics.
    """

    if not isinstance(source, str):
        raise ValueError("semantic marker source must be text")
    if axis not in {"root", "reference"}:
        raise ValueError("semantic marker axis must be root or reference")
    if (
        not isinstance(owner, str)
        or not SEMANTIC_ID_COMPONENT_RE.fullmatch(owner)
        or len(owner) > SEMANTIC_ID_MAX_LENGTH
    ):
        raise ValueError("semantic marker owner is invalid")

    kept = source.splitlines(keepends=True)
    plain_lines = source.splitlines()
    markers: list[dict[str, object]] = []
    marker_indices: set[int] = set()
    in_frontmatter = bool(plain_lines and plain_lines[0].strip() == "---")
    frontmatter_closed = not in_frontmatter
    fence: str | None = None

    for index, line in enumerate(plain_lines):
        stripped = line.strip()
        if index > 0 and in_frontmatter and stripped == "---":
            in_frontmatter = False
            frontmatter_closed = True
            continue
        fence_match = re.match(r"^\s*(```+|~~~+)", line)
        if not in_frontmatter and fence_match:
            token = fence_match.group(1)
            if fence is None:
                fence = token[0]
            elif token[0] == fence:
                fence = None
        if "rd-semantic-id:" not in line:
            continue
        html = SEMANTIC_ID_MARKER_HTML_RE.fullmatch(line)
        yaml_marker = SEMANTIC_ID_MARKER_YAML_RE.fullmatch(line)
        match = html or yaml_marker
        if match is None:
            raise ValueError(f"semantic marker line {index + 1} is malformed")
        if fence is not None:
            raise ValueError(f"semantic marker line {index + 1} is inside a fence")
        if yaml_marker is not None and not in_frontmatter:
            raise ValueError(
                f"semantic marker line {index + 1} uses frontmatter form outside frontmatter"
            )
        if html is not None and not frontmatter_closed:
            raise ValueError(
                f"semantic marker line {index + 1} uses Markdown form inside frontmatter"
            )
        rule_id = match.group("rule")
        occurrence_id = match.group("occurrence")
        finding = match.group("finding")
        if finding not in SEMANTIC_ID_FINDINGS_BY_AXIS[axis]:
            raise ValueError(
                f"semantic marker line {index + 1} finding is not declared for {axis}"
            )
        if any(
            len(value) > SEMANTIC_ID_MAX_LENGTH
            for value in (finding, rule_id, occurrence_id)
        ):
            raise ValueError(f"semantic marker line {index + 1} exceeds 96 characters")
        expected_prefix = (
            "group/"
            if finding in SEMANTIC_ID_GROUP_FINDINGS
            else f"{owner}/"
        )
        if not rule_id.startswith(expected_prefix):
            raise ValueError(
                f"semantic marker line {index + 1} rule-id has invalid owner prefix"
            )
        bound = index + 1
        while bound < len(plain_lines) and not plain_lines[bound].strip():
            bound += 1
        if bound >= len(plain_lines):
            raise ValueError(f"semantic marker line {index + 1} is orphaned")
        if "rd-semantic-id:" in plain_lines[bound]:
            raise ValueError(f"semantic marker line {index + 1} has ambiguous binding")
        markers.append(
            {
                "axis": axis,
                "finding": finding,
                "rule_id": rule_id,
                "occurrence_id": occurrence_id,
                "marker_line": index + 1,
                "bound_line": bound + 1,
            }
        )
        marker_indices.add(index)

    for index in marker_indices:
        ending = "\r\n" if kept[index].endswith("\r\n") else "\n" if kept[index].endswith("\n") else ""
        kept[index] = ending
    return {"visible_text": "".join(kept), "markers": markers}


def validate_semantic_identity_marker_inventory(
    records: list[dict[str, object]],
) -> None:
    """Validate one closed, already-parsed semantic marker inventory.

    Callers obtain ``markers`` only from :func:`semantic_identity_projection`;
    this second stage owns cross-document occurrence and rule collisions.
    """

    if not isinstance(records, list):
        raise ValueError("semantic marker inventory must be a list")
    occurrence_sources: dict[tuple[str, str], tuple[str, int]] = {}
    rule_sources: dict[tuple[str, str], list[tuple[str, str, str, int]]] = {}
    for record_index, record in enumerate(records):
        label = f"semantic marker inventory[{record_index}]"
        if not isinstance(record, dict) or set(record) != {
            "path", "owner", "axis", "markers"
        }:
            raise ValueError(f"{label} fields are invalid")
        path = record.get("path")
        owner = record.get("owner")
        axis = record.get("axis")
        markers = record.get("markers")
        if (
            not isinstance(path, str)
            or not path
            or "\\" in path
            or path.startswith("/")
            or any(part in {"", ".", ".."} for part in path.split("/"))
        ):
            raise ValueError(f"{label}.path must be canonical relative POSIX")
        if (
            not isinstance(owner, str)
            or not SEMANTIC_ID_COMPONENT_RE.fullmatch(owner)
            or len(owner) > SEMANTIC_ID_MAX_LENGTH
        ):
            raise ValueError(f"{label}.owner is invalid")
        if axis not in SEMANTIC_ID_FINDINGS_BY_AXIS:
            raise ValueError(f"{label}.axis is invalid")
        if not isinstance(markers, list):
            raise ValueError(f"{label}.markers must be a list")
        prior_marker_line = 0
        bound_lines: set[int] = set()
        for marker_index, marker in enumerate(markers):
            marker_label = f"{label}.markers[{marker_index}]"
            if not isinstance(marker, dict) or set(marker) != {
                "axis", "finding", "rule_id", "occurrence_id",
                "marker_line", "bound_line",
            }:
                raise ValueError(f"{marker_label} fields are invalid")
            finding = marker.get("finding")
            rule_id = marker.get("rule_id")
            occurrence_id = marker.get("occurrence_id")
            marker_line = marker.get("marker_line")
            bound_line = marker.get("bound_line")
            if marker.get("axis") != axis:
                raise ValueError(f"{marker_label}.axis does not match its source")
            if finding not in SEMANTIC_ID_FINDINGS_BY_AXIS[axis]:
                raise ValueError(f"{marker_label}.finding is not declared")
            if any(
                not isinstance(value, str)
                or not SEMANTIC_ID_COMPONENT_RE.fullmatch(value)
                or len(value) > SEMANTIC_ID_MAX_LENGTH
                for value in (rule_id, occurrence_id)
            ):
                raise ValueError(f"{marker_label} identity is invalid")
            expected_prefix = (
                "group/"
                if finding in SEMANTIC_ID_GROUP_FINDINGS
                else f"{owner}/"
            )
            if not rule_id.startswith(expected_prefix):
                raise ValueError(f"{marker_label} rule-id has invalid owner prefix")
            if (
                type(marker_line) is not int
                or type(bound_line) is not int
                or marker_line <= prior_marker_line
                or bound_line <= marker_line
            ):
                raise ValueError(f"{marker_label} has invalid or orphaned binding")
            if bound_line in bound_lines:
                raise ValueError(f"{marker_label} has ambiguous binding")
            prior_marker_line = marker_line
            bound_lines.add(bound_line)

            occurrence_key = (str(axis), str(occurrence_id))
            source = (path, marker_line)
            if occurrence_key in occurrence_sources:
                previous = occurrence_sources[occurrence_key]
                raise ValueError(
                    "duplicate semantic marker occurrence-id for "
                    f"{axis}: {occurrence_id} ({previous[0]}, {path})"
                )
            occurrence_sources[occurrence_key] = source
            rule_sources.setdefault((str(axis), str(rule_id)), []).append(
                (
                    str(finding),
                    "group" if str(rule_id).startswith("group/") else owner,
                    path,
                    marker_line,
                )
            )

    for (axis, rule_id), sources in sorted(rule_sources.items()):
        if len(sources) <= 1:
            continue
        if not rule_id.startswith("group/"):
            raise ValueError(f"semantic marker rule-id collision for {axis}: {rule_id}")
        selector_scopes = {
            (finding, owner_or_group)
            for finding, owner_or_group, _path, _line in sources
        }
        if len(selector_scopes) != 1:
            raise ValueError(
                f"semantic grouped marker selector collision for {axis}: {rule_id}"
            )


def strip_semantic_identity_markers(source: str) -> str:
    """Strip well-formed semantic marker lines from a built artifact."""

    lines = source.splitlines(keepends=True)
    output: list[str] = []
    for line in lines:
        plain = line.rstrip("\r\n")
        if "rd-semantic-id:" not in plain:
            output.append(line)
            continue
        if not (
            SEMANTIC_ID_MARKER_HTML_RE.fullmatch(plain)
            or SEMANTIC_ID_MARKER_YAML_RE.fullmatch(plain)
            or SEMANTIC_ID_LEGACY_MARKER_HTML_RE.fullmatch(plain)
            or SEMANTIC_ID_LEGACY_MARKER_YAML_RE.fullmatch(plain)
        ):
            raise ValueError("built source contains a malformed semantic marker")
    return "".join(output)


def report_output_paths(
    reports_dir: Path,
    json_filename: str,
    markdown_filename: str,
) -> tuple[Path, Path]:
    """Resolve one producer's JSON and Markdown within an explicit directory."""

    filenames = (json_filename, markdown_filename)
    if any(
        not filename
        or Path(filename).name != filename
        or filename in {".", ".."}
        for filename in filenames
    ):
        raise ValueError("report filenames must be plain non-empty names")
    return reports_dir / json_filename, reports_dir / markdown_filename


def parse_markdown_logical_list_items(markdown: str) -> dict[str, list[str]]:
    """Parse logical list items without borrowing from adjacent prose."""

    def columns(value: str) -> int:
        column = 0
        for character in value:
            column += 4 - (column % 4) if character == "\t" else 1
        return column

    def leading_columns(line: str) -> int:
        prefix = re.match(r"^[ \t]*", line)
        return columns(prefix.group(0) if prefix else "")

    items: list[str] = []
    non_list_content: list[str] = []
    current: list[str] = []
    current_content_indent: int | None = None
    active_items: list[tuple[int, int]] = []

    def finish_current() -> None:
        nonlocal current, current_content_indent
        if current:
            items.append(" ".join(current))
        current = []
        current_content_indent = None

    for line in markdown.splitlines():
        match = MARKDOWN_ANY_LIST_ITEM_RE.match(line)
        if match:
            marker_indent = columns(match.group("indent"))
            content_indent = columns(line[: match.start("text")])
            while active_items and marker_indent < active_items[-1][1]:
                active_items.pop()
            legal_marker = (
                active_items[-1][1] <= marker_indent <= active_items[-1][1] + 3
                if active_items
                else marker_indent <= 3
            )
            finish_current()
            if legal_marker:
                active_items.append((marker_indent, content_indent))
                current = [match.group("text").strip()]
                current_content_indent = content_indent
            else:
                non_list_content.append(line.strip())
            continue
        if not line.strip():
            finish_current()
            continue
        line_indent = leading_columns(line)
        if (
            current
            and current_content_indent is not None
            and line_indent >= current_content_indent
        ):
            current.append(line.strip())
        else:
            finish_current()
            non_list_content.append(line.strip())
        while active_items and line_indent < active_items[-1][1]:
            active_items.pop()
    finish_current()
    return {
        "items": items,
        "non_list_content": non_list_content,
    }


def foundation_decision_card(markdown: str) -> dict[str, Any]:
    """Return the canonical Foundation decision-card actionability result."""

    lines = markdown.splitlines()
    headings = [
        (index, match.group(1).strip())
        for index, line in enumerate(lines)
        if (match := _FOUNDATION_H2_RE.match(line))
    ]
    positions = {title: index for index, title in headings}

    def section(title: str) -> list[str]:
        start = positions.get(title)
        if start is None:
            return []
        end = next(
            (
                index
                for index, _heading in headings
                if index > start
            ),
            len(lines),
        )
        return lines[start + 1 : end]

    trigger_text = "\n".join(section("Registry Trigger")).casefold()
    parsed_rules = parse_markdown_logical_list_items(
        "\n".join(section("High-Value Rules"))
    )
    rules = parsed_rules["items"]

    def decision_bearing(value: str) -> bool:
        plain = re.sub(r"[`*_~]", "", value)
        words = re.findall(r"\b[\w/-]+\b", plain)
        domain_tokens = {
            word.casefold()
            for word in words
            if len(word) >= 4
            and word.casefold() not in _FOUNDATION_GENERIC_DECISION_TOKENS
        }
        return bool(
            len(domain_tokens) >= 2
            and (
                _FOUNDATION_DECISION_VERB_RE.search(plain)
                or _FOUNDATION_RULE_CONTEXT_RE.search(plain)
            )
        )

    decision_count = sum(decision_bearing(rule) for rule in rules)
    density = round(decision_count / max(1, len(rules)), 3)
    findings: list[str] = []
    trigger_line = positions.get("Registry Trigger")
    rules_line = positions.get("High-Value Rules")
    anti_line = positions.get("Anti-Patterns")
    stop_line = positions.get("Stop Conditions")
    output_line = positions.get("Output Contract")
    references_line = positions.get("Targeted References")
    if (
        trigger_line is None
        or rules_line is None
        or trigger_line >= rules_line
        or "use when" not in trigger_text
        or "do not use when" not in trigger_text
    ):
        findings.append("trigger-boundaries-not-front-loaded")
    if (
        rules_line is None
        or rules_line + 1 > FOUNDATION_DECISION_CARD_FRONT_LINES
    ):
        findings.append("high-value-rules-not-early")
    if not FOUNDATION_DECISION_RULE_MIN <= len(rules) <= FOUNDATION_DECISION_RULE_MAX:
        findings.append("decision-rule-count-outside-3-8")
    if decision_count < len(rules) or density < 1.0:
        findings.append("decision-density-low")
    if parsed_rules["non_list_content"]:
        findings.append("non-list-content")
    stop_ordered = (
        stop_line is not None
        and rules_line is not None
        and anti_line is not None
        and references_line is not None
        and rules_line < anti_line < stop_line < references_line
        and (
            output_line is None
            or stop_line < output_line < references_line
        )
    )
    if not stop_ordered:
        findings.append("stop-conditions-missing-or-late")
    return {
        "model": FOUNDATION_DECISION_CARD_MODEL,
        "applicable": bool(findings),
        "findings": findings,
        "metrics": {
            "high_value_rule_count": len(rules),
            "high_value_rule_decision_count": decision_count,
            "high_value_rules_without_decision_semantics": (
                len(rules) - decision_count
            ),
            "decision_density": density,
        },
    }


CORE_CONTRACTS_PATH = ROOT / "src" / "control-model" / "core-contracts.json"
CORE_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
AUTHORITATIVE_BUILD_INPUT_SCHEMA_VERSION = 1
AUTHORITATIVE_BUILD_INPUT_ROOTS = ("src",)
AUTHORITATIVE_BUILD_INPUT_BASE_FILES = (
    "pyproject.toml",
    "scripts/build.py",
    "scripts/validation_utils.py",
)
AUTHORITATIVE_BUILD_INPUT_EXCLUDED_PATHS = (
    ".git",
    "dist",
    "reports",
    "docs/SHOWCASE.md",
    "docs/MARKETPLACE_CATALOG.md",
    "evals/pressure/outputs",
)
AUTHORITATIVE_BUILD_INPUT_EXCLUDED_DIRECTORY_NAMES = (
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
)
SKILL_ROOT_SOURCE_COLLECTOR_ID = "scripts/audit-skill-content.py:root-skill-content"
SKILL_ROOT_SOURCE_NORMALIZATION = "unicode-nfkc-whitespace-collapse-v1"


def normalize_skill_root_source(value: str) -> str:
    """Normalize one root Skill source or source anchor for authority binding."""

    return " ".join(unicodedata.normalize("NFKC", value).split())


def collect_skill_root_source(path: Path, *, root: Path = ROOT) -> dict[str, str]:
    """Collect one repository-owned root ``SKILL.md`` through the audit path."""

    resolved_root = root.resolve()
    try:
        resolved_path = path.resolve(strict=True)
        relative_path = resolved_path.relative_to(resolved_root)
    except (OSError, ValueError) as exc:
        raise ValueError(f"root Skill source is outside the repository: {path}") from exc
    if relative_path.name != "SKILL.md" or ".." in relative_path.parts:
        raise ValueError(f"root Skill source must name a canonical SKILL.md: {path}")
    try:
        with resolved_path.open("r", encoding="utf-8", newline="") as handle:
            raw_source = handle.read()
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"cannot read root Skill source {relative_path}") from exc
    normalized_source = normalize_skill_root_source(raw_source)
    return {
        "collector": SKILL_ROOT_SOURCE_COLLECTOR_ID,
        "normalization": SKILL_ROOT_SOURCE_NORMALIZATION,
        "path": relative_path.as_posix(),
        "raw_source": raw_source,
        "normalized_source": normalized_source,
        "source_fingerprint": hashlib.sha256(
            normalized_source.encode("utf-8")
        ).hexdigest(),
    }


def skill_source_anchor_fingerprint(anchors: Iterable[str]) -> str:
    """Fingerprint ordered normalized anchors without redefining their meaning."""

    normalized = [normalize_skill_root_source(anchor) for anchor in anchors]
    payload = "skill-root-source-anchors-v1\0" + "\0".join(normalized)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
AUTHORITATIVE_BUILD_INPUT_EXCLUDED_FILE_NAMES = (".DS_Store",)
AUTHORITATIVE_BUILD_INPUT_EXCLUDED_SUFFIXES = (".pyc", ".pyo")
AUTHORITATIVE_BUILD_INPUT_RECORD_FORMAT = (
    "relative-path-nul-type-nul-length-nul-content-v1"
)
AUTHORITATIVE_BUILD_INPUT_KIND = "changeforge.authoritative_build_inputs"
_AUTHORITATIVE_BUILD_INPUT_IDENTITY_FIELDS = (
    "schema_version",
    "kind",
    "algorithm",
    "record_format",
    "include_roots",
    "include_files",
    "exclusions",
    "file_count",
    "sha256",
)
_AUTHORITATIVE_BUILD_INPUT_SNAPSHOT_FIELDS = frozenset(
    (*_AUTHORITATIVE_BUILD_INPUT_IDENTITY_FIELDS, "git")
)
PRINCIPLE_PREDICATE_OPERATORS = {
    "contains",
    "equals",
    "greater_than_or_equal",
    "less_than_or_equal",
    "not_contains",
    "not_equals",
}
EXPERT_PANEL_RELEASE_MANIFEST_SCHEMA_VERSION = 1
EXPERT_PANEL_RELEASE_MANIFEST_ARTIFACTS = (
    (
        "readability",
        "evals/expert-panel/readability.json",
        "accepted-current-readability",
    ),
    (
        "semantic-disposition",
        "evals/expert-panel/semantic-disposition.json",
        "accepted-current-semantic-disposition",
    ),
    (
        "professional-completeness",
        "evals/expert-panel/professional-completeness.json",
        "accepted-current-professional-completeness",
    ),
)


def validate_expert_panel_release_manifest(
    value: object,
    *,
    require_current: bool,
    expected_head_commit: str | None = None,
) -> list[str]:
    """Validate the closed downstream Expert Panel release identity."""

    errors: list[str] = []
    fields = {
        "schema_version",
        "status",
        "head_commit",
        "artifacts",
        "verification_toolchain",
    }
    if not isinstance(value, dict) or set(value) != fields:
        return ["expert_panel_release_manifest fields are invalid"]
    if value.get("schema_version") != EXPERT_PANEL_RELEASE_MANIFEST_SCHEMA_VERSION:
        errors.append("expert_panel_release_manifest schema_version is invalid")
    status = value.get("status")
    allowed_statuses = {"current", "not-evaluated", "missing", "stale", "pending"}
    if status not in allowed_statuses:
        errors.append("expert_panel_release_manifest status is invalid")
    if require_current and status != "current":
        errors.append("formal release requires a current Expert Panel manifest")
    if status != "current":
        if (
            value.get("head_commit") is not None
            or value.get("artifacts") != []
            or value.get("verification_toolchain") is not None
        ):
            errors.append(
                "non-current Expert Panel manifest cannot claim artifact identity"
            )
        return errors

    head_commit = value.get("head_commit")
    if (
        not isinstance(head_commit, str)
        or len(head_commit) not in {40, 64}
        or any(char not in "0123456789abcdef" for char in head_commit)
    ):
        errors.append("expert_panel_release_manifest HEAD commit is invalid")
    elif expected_head_commit is not None and head_commit != expected_head_commit:
        errors.append(
            "expert_panel_release_manifest HEAD does not match the current commit"
        )

    artifacts = value.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != 3:
        errors.append(
            "expert_panel_release_manifest must contain exactly three artifacts"
        )
        artifacts = []
    artifact_fields = {
        "axis",
        "path",
        "external_sha256",
        "size_bytes",
        "review_id",
        "verdict",
    }
    for index, expected in enumerate(EXPERT_PANEL_RELEASE_MANIFEST_ARTIFACTS):
        if index >= len(artifacts):
            break
        artifact = artifacts[index]
        axis, path, verdict = expected
        if not isinstance(artifact, dict) or set(artifact) != artifact_fields:
            errors.append(
                f"expert_panel_release_manifest artifact {index} fields are invalid"
            )
            continue
        if (
            artifact.get("axis") != axis
            or artifact.get("path") != path
            or artifact.get("verdict") != verdict
        ):
            errors.append(
                f"expert_panel_release_manifest artifact {index} authority is invalid"
            )
        digest = artifact.get("external_sha256")
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(char not in "0123456789abcdef" for char in digest)
        ):
            errors.append(
                f"expert_panel_release_manifest artifact {index} sha256 is invalid"
            )
        if type(artifact.get("size_bytes")) is not int or artifact["size_bytes"] <= 0:
            errors.append(
                f"expert_panel_release_manifest artifact {index} size is invalid"
            )
        if not isinstance(artifact.get("review_id"), str) or not artifact["review_id"]:
            errors.append(
                f"expert_panel_release_manifest artifact {index} review_id is invalid"
            )

    verification = value.get("verification_toolchain")
    expected_verification = {
        "head_commit_matches_current": True,
        "artifact_count": 3,
        "accepted_artifact_count": 3,
        "head_byte_equal_count": 3,
        "clean_artifact_count": 3,
    }
    if verification != expected_verification:
        errors.append(
            "expert_panel_release_manifest verification observations are not current"
        )
    return errors


CANONICAL_CORE_PRINCIPLE_IDENTITIES = (
    ("ai-first", "AI First"),
    ("core-model", "Core Model"),
    ("control-plane-only", "Control Plane Only"),
    ("minimum-sufficient-process", "Minimum Sufficient Process"),
    ("explicit-task-contract", "Explicit Task Contract"),
    ("safe-parallelism", "Safe Parallelism"),
    ("context-isolation", "Context Isolation"),
    ("professional-skill-injection", "Professional Skill Injection"),
    ("reference-loading", "Reference Loading"),
    ("evidence-before-completion", "Evidence Before Completion"),
    ("single-source-of-truth", "Single Source of Truth"),
    ("framework-transparency", "Framework Transparency"),
    ("strong-user-feedback", "Strong User Feedback"),
    ("explicit-completion-state", "Explicit Completion State"),
    ("final-goal", "Final Goal"),
)
MIN_PRODUCER_TIMEOUT_SECONDS = 1
MAX_PRODUCER_TIMEOUT_SECONDS = 3600
PROFESSIONAL_REVIEW_COST_LIMITATIONS = [
    "Canonical effective discovery/request/final input-block bytes are a structural proxy; identical blocks are counted at most three times, while formal policy separately recomputes required-only source coverage and reviewer-added relationship/evidence metadata overhead; neither measure proves actual tokens, wall-clock time, subagent count, monetary cost, or reviewer behavior.",
    "Static qualification claims do not prove reviewer identity, credentials, or domain experience.",
    "Static round-tree validation cannot prove that historical schema-3 rounds were not deleted.",
]
PROFESSIONAL_REVIEW_FIXTURE_LIMITATIONS = [
    *PROFESSIONAL_REVIEW_COST_LIMITATIONS,
    "Routing-neutral isolated material-binding sensitivity keeps Registry, expertise, Reference paths and headings, adjacency ranking and selection unchanged and assumes an empty reviewer-added candidate union; real history-added dependencies or governance changes can require more review.",
]

PROFESSIONAL_REVIEW_FORMAL_ROUND_POLICY_FIELDS = {
    "schema_version",
    "full_fresh_source_material_coverage_ratio_ppm",
    "maximum_reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm",
    "maximum_reviewer_added_unique_union_to_required_ratio_ppm",
}

PROFESSIONAL_REVIEW_COST_FIELDS = {
    "fresh_vote_count",
    "carried_forward_vote_count",
    "effective_vote_count",
    "fresh_criterion_result_count",
    "carried_forward_criterion_result_count",
    "effective_criterion_result_count",
    "canonical_capsule_input_bytes_proxy",
    "full_rereview_deduplicated_capsule_input_bytes_proxy",
    "input_ratio_ppm",
    "required_only_capsule_input_bytes_proxy",
    "required_only_input_ratio_ppm",
    "required_only_source_material_input_bytes_proxy",
    "source_material_input_bytes_proxy",
    "full_rereview_source_material_input_bytes_proxy",
    "source_material_coverage_ratio_ppm",
    "reviewer_added_source_material_input_bytes_proxy",
    "reviewer_added_relationship_evidence_metadata_overhead_bytes_proxy",
    "reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm",
    "reviewer_added_request_count",
    "reviewer_added_unique_relationship_count",
    "maximum_reviewer_added_unique_union_to_required_ratio_ppm",
    "formal_round_policy_fingerprint",
    "maximum_origin_depth",
    "plan_lineage_depth",
    "policy_status",
    "limitations",
}

PROFESSIONAL_REVIEW_COST_TEXT_FIELDS = {
    "formal_round_policy_fingerprint",
    "policy_status",
    "limitations",
}


def _authoritative_build_input_exclusions() -> dict[str, list[str]]:
    return {
        "paths": list(AUTHORITATIVE_BUILD_INPUT_EXCLUDED_PATHS),
        "directory_names": list(
            AUTHORITATIVE_BUILD_INPUT_EXCLUDED_DIRECTORY_NAMES
        ),
        "file_names": list(AUTHORITATIVE_BUILD_INPUT_EXCLUDED_FILE_NAMES),
        "suffixes": list(AUTHORITATIVE_BUILD_INPUT_EXCLUDED_SUFFIXES),
    }


def _authoritative_build_input_path(relative: PurePosixPath) -> bool:
    text = relative.as_posix()
    if text in AUTHORITATIVE_BUILD_INPUT_FILES:
        return True
    if not relative.parts or relative.parts[0] not in AUTHORITATIVE_BUILD_INPUT_ROOTS:
        return False
    if any(
        part in AUTHORITATIVE_BUILD_INPUT_EXCLUDED_DIRECTORY_NAMES
        for part in relative.parts[:-1]
    ):
        return False
    if relative.name in AUTHORITATIVE_BUILD_INPUT_EXCLUDED_FILE_NAMES:
        return False
    return not any(
        relative.name.endswith(suffix)
        for suffix in AUTHORITATIVE_BUILD_INPUT_EXCLUDED_SUFFIXES
    )


def _authoritative_build_input_files(repository_root: Path) -> list[tuple[str, bytes]]:
    root = repository_root.expanduser().absolute()
    paths: set[Path] = set()
    for relative_text in AUTHORITATIVE_BUILD_INPUT_FILES:
        path = root.joinpath(*PurePosixPath(relative_text).parts)
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"authoritative build input {relative_text} must be a regular file")
        paths.add(path)
    for relative_text in AUTHORITATIVE_BUILD_INPUT_ROOTS:
        source_root = root.joinpath(*PurePosixPath(relative_text).parts)
        if source_root.is_symlink() or not source_root.is_dir():
            raise ValueError(
                f"authoritative build input root {relative_text} must be a regular directory"
            )
        for path in source_root.rglob("*"):
            relative = PurePosixPath(path.relative_to(root).as_posix())
            if not _authoritative_build_input_path(relative):
                continue
            if path.is_symlink():
                raise ValueError(
                    f"authoritative build input {relative.as_posix()} must not be a symlink"
                )
            if path.is_file():
                paths.add(path)
            elif not path.is_dir():
                raise ValueError(
                    f"authoritative build input {relative.as_posix()} has unsupported type"
                )
    records: list[tuple[str, bytes]] = []
    for path in paths:
        relative = path.relative_to(root).as_posix()
        records.append((relative, path.read_bytes()))
    return sorted(records, key=lambda item: item[0])


def _git_authoritative_build_input_paths(raw_status: bytes) -> list[PurePosixPath]:
    fields = raw_status.split(b"\0")
    paths: list[PurePosixPath] = []
    index = 0
    while index < len(fields):
        record = fields[index]
        index += 1
        if not record:
            continue
        if len(record) < 4 or record[2:3] != b" ":
            return [PurePosixPath("src")]
        status = record[:2]
        paths.append(
            PurePosixPath(record[3:].decode("utf-8", errors="surrogateescape"))
        )
        if b"R" in status or b"C" in status:
            if index >= len(fields) or not fields[index]:
                return [PurePosixPath("src")]
            paths.append(
                PurePosixPath(
                    fields[index].decode("utf-8", errors="surrogateescape")
                )
            )
            index += 1
    return paths


def _authoritative_build_input_git_metadata(
    repository_root: Path,
) -> dict[str, str | None]:
    root = repository_root.expanduser().absolute()
    try:
        head_result = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except (FileNotFoundError, OSError):
        return {"head": None, "state": "unavailable"}
    if head_result.returncode != 0:
        return {"head": None, "state": "unavailable"}
    head = head_result.stdout.decode("ascii", errors="strict").strip().lower()
    if re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", head) is None:
        return {"head": None, "state": "unavailable"}
    try:
        status_result = subprocess.run(
            [
                "git",
                "status",
                "--porcelain=v1",
                "-z",
                "--untracked-files=all",
                "--",
                *AUTHORITATIVE_BUILD_INPUT_ROOTS,
                *AUTHORITATIVE_BUILD_INPUT_FILES,
            ],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except (FileNotFoundError, OSError):
        return {"head": head, "state": "unavailable"}
    if status_result.returncode != 0:
        return {"head": head, "state": "unavailable"}
    dirty = any(
        _authoritative_build_input_path(relative)
        for relative in _git_authoritative_build_input_paths(status_result.stdout)
    )
    return {"head": head, "state": "dirty" if dirty else "clean"}


def authoritative_build_input_snapshot(
    repository_root: Path = ROOT,
) -> dict[str, object]:
    """Bind the complete deterministic input set used by ``scripts/build.py``."""

    records = _authoritative_build_input_files(repository_root)
    digest = hashlib.sha256()
    digest.update(b"changeforge-authoritative-build-inputs-v1\0")
    for relative, content in records:
        header = f"{relative}\0file\0{len(content)}\0".encode("utf-8")
        digest.update(len(header).to_bytes(8, byteorder="big"))
        digest.update(header)
        digest.update(content)
    return {
        "schema_version": AUTHORITATIVE_BUILD_INPUT_SCHEMA_VERSION,
        "kind": AUTHORITATIVE_BUILD_INPUT_KIND,
        "algorithm": "sha256",
        "record_format": AUTHORITATIVE_BUILD_INPUT_RECORD_FORMAT,
        "include_roots": list(AUTHORITATIVE_BUILD_INPUT_ROOTS),
        "include_files": list(AUTHORITATIVE_BUILD_INPUT_FILES),
        "exclusions": _authoritative_build_input_exclusions(),
        "file_count": len(records),
        "sha256": digest.hexdigest(),
        "git": _authoritative_build_input_git_metadata(repository_root),
    }


def authoritative_build_input_snapshot_errors(
    recorded: object,
    repository_root: Path = ROOT,
) -> list[str]:
    """Reject malformed or stale snapshots; Git metadata remains audit-only."""

    if not isinstance(recorded, dict) or set(recorded) != set(
        _AUTHORITATIVE_BUILD_INPUT_SNAPSHOT_FIELDS
    ):
        return ["authoritative build input snapshot schema is invalid"]
    git_metadata = recorded.get("git")
    if not isinstance(git_metadata, dict) or set(git_metadata) != {"head", "state"}:
        return ["authoritative build input snapshot Git metadata is invalid"]
    head = git_metadata.get("head")
    state = git_metadata.get("state")
    if state not in {"clean", "dirty", "unavailable"} or (
        head is not None
        and (
            not isinstance(head, str)
            or re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", head) is None
        )
    ):
        return ["authoritative build input snapshot Git metadata is invalid"]
    try:
        current = authoritative_build_input_snapshot(repository_root)
    except (OSError, ValueError) as exc:
        return [f"authoritative build inputs are stale or unavailable: {exc}"]
    if any(recorded.get(field) != current[field] for field in _AUTHORITATIVE_BUILD_INPUT_IDENTITY_FIELDS):
        return [
            "authoritative build inputs are stale: recorded file set or content differs from the current source tree"
        ]
    return []

EXPECTED_DOC_PROJECTION_IDS = {
    "operating-model-task-evidence-completion",
    "subagent-model-task-evidence-completion",
}
EXPECTED_CONTEXT_BUDGET_DOC_PROJECTION_IDS = {
    "validation-rendered-context-budget",
    "benchmarks-rendered-context-budget",
}
PROMPT_MANAGED_PROJECTION_CONTRACTS = {}
PROFILE_EXACT_RULE_BINDINGS = frozenset(
    {
        ("task-normal-mode", "bounded-validation-retry"),
        ("task-normal-mode", "bounded-validation-stop"),
        ("review-target-modes", "implementation-review"),
        ("review-target-modes", "no-summary-substitute"),
        ("review-target-modes", "review-never-exports"),
    }
)


def derived_context_budget_limits(contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Validate and project soft/hard limits from the Core Model authority."""

    if contract.get("schema_version") != 3:
        raise ValueError("context budget contract must use schema_version 3")

    classes = contract.get("budget_classes")
    if not isinstance(classes, dict) or not classes:
        raise ValueError("context budget classes must be a non-empty object")
    limits: dict[str, dict[str, Any]] = {}
    for budget_class, entry in classes.items():
        if not isinstance(entry, dict):
            raise ValueError(f"context budget class {budget_class!r} must be an object")
        expected_fields = {
            "label",
            "category",
            "soft_target",
            "hard_ceiling",
            "calibration_status",
        }
        if set(entry) != expected_fields:
            raise ValueError(
                f"context budget class {budget_class!r} fields must be exactly "
                f"{sorted(expected_fields)}"
            )
        label = entry.get("label")
        if not isinstance(label, str) or not label.strip():
            raise ValueError(
                f"context budget class {budget_class!r} label must be non-empty text"
            )
        category = entry.get("category")
        if category not in {"resident_runtime", "dispatch_composition"}:
            raise ValueError(
                f"context budget class {budget_class!r} category is invalid"
            )
        soft_target = entry.get("soft_target")
        hard_ceiling = entry.get("hard_ceiling")
        if (
            not isinstance(soft_target, int)
            or isinstance(soft_target, bool)
            or soft_target <= 0
        ):
            raise ValueError(
                f"context budget class {budget_class!r} soft_target must be positive"
            )
        if (
            not isinstance(hard_ceiling, int)
            or isinstance(hard_ceiling, bool)
            or hard_ceiling <= 0
        ):
            raise ValueError(
                f"context budget class {budget_class!r} hard_ceiling must be positive"
            )
        if soft_target >= hard_ceiling:
            raise ValueError(
                f"context budget class {budget_class!r} soft_target must be below hard_ceiling"
            )
        if entry.get("calibration_status") != "provisional-migration-value":
            raise ValueError(
                f"context budget class {budget_class!r} calibration_status must mark a provisional migration value"
            )
        limits[budget_class] = {
            "label": label,
            "category": category,
            "soft_target": soft_target,
            "hard_ceiling": hard_ceiling,
            "calibration_status": entry["calibration_status"],
        }

    taxonomy = contract.get("context_taxonomy")
    expected_taxonomy_categories = {
        "authoring",
        "resident_runtime",
        "dispatch_composition",
        "runtime_dynamic_context",
    }
    if not isinstance(taxonomy, dict) or set(taxonomy) != expected_taxonomy_categories:
        raise ValueError(
            "context budget taxonomy must define authoring, resident_runtime, "
            "dispatch_composition, and runtime_dynamic_context"
        )

    def taxonomy_classes(category: str) -> list[str]:
        entry = taxonomy.get(category)
        if not isinstance(entry, dict):
            raise ValueError(f"context budget taxonomy {category!r} must be an object")
        values = entry.get("classes")
        if (
            not isinstance(values, list)
            or any(not isinstance(value, str) or not value for value in values)
        ):
            raise ValueError(
                f"context budget taxonomy {category!r} classes must be text names"
            )
        if len(values) != len(set(values)):
            raise ValueError(
                f"context budget taxonomy {category!r} classes must be unique"
            )
        return values

    resident_classes = taxonomy_classes("resident_runtime")
    dispatch_classes = taxonomy_classes("dispatch_composition")
    authoring_classes = taxonomy_classes("authoring")
    dynamic_classes = taxonomy_classes("runtime_dynamic_context")
    resident_set = set(resident_classes)
    dispatch_set = set(dispatch_classes)
    rendered_classes = set(limits)
    if resident_set & dispatch_set:
        raise ValueError(
            "resident_runtime and dispatch_composition taxonomy classes must be disjoint"
        )
    if resident_set | dispatch_set != rendered_classes:
        raise ValueError(
            "resident_runtime and dispatch_composition taxonomy classes must cover "
            "every rendered budget class exactly once"
        )
    resident_entries = {
        name for name, entry in limits.items() if entry["category"] == "resident_runtime"
    }
    dispatch_entries = {
        name
        for name, entry in limits.items()
        if entry["category"] == "dispatch_composition"
    }
    if resident_set != resident_entries:
        raise ValueError(
            "resident_runtime taxonomy classes must equal rendered classes with "
            "category resident_runtime"
        )
    if dispatch_set != dispatch_entries:
        raise ValueError(
            "dispatch_composition taxonomy classes must equal rendered classes with "
            "category dispatch_composition"
        )
    unsupported_rendered = rendered_classes & (
        set(authoring_classes) | set(dynamic_classes)
    )
    if unsupported_rendered:
        raise ValueError(
            "authoring and runtime_dynamic_context taxonomy classes cannot be rendered "
            f"budget classes: {sorted(unsupported_rendered)}"
        )
    return limits


def context_budget_docs_projection_block(
    data: dict[str, Any], projection: dict[str, Any]
) -> str:
    """Render the managed documentation view of authoritative context limits."""

    identifier = projection["id"]
    contract = data["context_budget_contract"]
    limits = derived_context_budget_limits(contract)
    lines = [
        f"<!-- BEGIN CHANGEFORGE CONTEXT BUDGET PROJECTION: {identifier} -->",
        "Source: `src/control-model/core-contracts.json#/context_budget_contract`.",
        "",
        "Budget taxonomy and all Runtime/Rendered limits are owned only by Core. "
        "Budget is a cost guardrail and never changes routing, required context, "
        "or correctness obligations.",
        "",
        "Authoring Budget classes: "
        + ", ".join(
            item.replace("_", " ").title()
            for item in contract["context_taxonomy"]["authoring"]["classes"]
        )
        + ".",
        "Resident Runtime Budget classes: Main always-loaded.",
        "Dispatch Composition Budget classes: Direct Task, Analyzed Task, Analysis, Review, Utility.",
        "Runtime Dynamic Context classes: "
        + ", ".join(
            item.replace("_", " ").title()
            for item in contract["context_taxonomy"]["runtime_dynamic_context"]["classes"]
        )
        + "; observation-only, with host conversation compaction out of scope.",
        "",
        "| Category | Context | Soft target | Hard ceiling | Calibration status |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for limit in limits.values():
        lines.append(
            f"| {contract['context_taxonomy'][limit['category']]['label']} | "
            f"{limit['label']} | {limit['soft_target']} | {limit['hard_ceiling']} | "
            f"{limit['calibration_status']} |"
        )
    lines.extend(
        [
            "",
            "Soft-target overage is a growth advisory; hard-ceiling overage fails "
            "Conformance. Calibration does not apply either limit to candidate selection or exit.",
            "Required routing, Professional, Domain, Layer 3, Reference, Review, and Evidence "
            "context is never truncated to satisfy a budget.",
            "Quality-first A/B gate: Routing, Review, and Codegen evidence must preserve "
            "quality before a candidate enters the token/turn/elapsed cost frontier. Any "
            "quality regression rejects the candidate even when tokens decrease. Missing "
            "comparable evidence is structural-only/not-enough-evidence; absent live behavior, "
            "codegen, or elapsed evidence is not_collected.",
            "Candidate total not greater than baseline is not correctness acceptance. The "
            "Core hard ceiling remains an independent Conformance failure, and static token "
            "proxies do not prove latency.",
            "",
            f"Tokenizer: `{contract['tokenizer']}`. Exact duplicate-rule ratio gate: "
            f"`{contract['duplicate_rule_token_ratio_max']:.2f}`.",
            f"<!-- END CHANGEFORGE CONTEXT BUDGET PROJECTION: {identifier} -->",
        ]
    )
    return "\n".join(lines)


DOC_PROJECTION_RENDERERS = frozenset({"strings", "projection-rule-terms"})


def _core_contract_source_value(data: dict[str, Any], source_path: str) -> object:
    """Resolve one dot-separated docs binding without permitting list indexes."""

    parts = source_path.split(".")
    if not parts or any(
        re.fullmatch(r"[a-z][a-z0-9_]*", part) is None for part in parts
    ):
        raise ValueError(f"invalid source_path {source_path!r}")
    current: object = data
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            raise ValueError(f"unknown source_path {source_path!r}")
        current = current[part]
    return current


def docs_projection_terms(
    data: dict[str, Any], projection: dict[str, Any]
) -> list[str]:
    """Render one documentation projection directly from canonical contracts."""

    terms: list[str] = []
    bindings = projection.get("bindings")
    if not isinstance(bindings, list) or not bindings:
        raise ValueError("docs projection bindings must be a non-empty list")
    for binding in bindings:
        if not isinstance(binding, dict) or set(binding) != {"source_path", "render"}:
            raise ValueError("docs projection binding fields must be source_path and render")
        source_path = binding["source_path"]
        renderer = binding["render"]
        if not isinstance(source_path, str) or not source_path:
            raise ValueError("docs projection source_path must be non-empty text")
        if renderer not in DOC_PROJECTION_RENDERERS:
            raise ValueError(f"unknown docs projection renderer {renderer!r}")
        value = _core_contract_source_value(data, source_path)
        if renderer == "strings":
            if not isinstance(value, list) or any(
                not isinstance(item, str) or not item.strip() for item in value
            ):
                raise ValueError(f"{source_path!r} must resolve to non-empty strings")
            terms.extend(value)
            continue
        if not isinstance(value, list) or not value:
            raise ValueError(
                f"{source_path!r} must resolve to projection-rule objects"
            )
        for index, rule in enumerate(value):
            projection_terms = rule.get("projection_terms") if isinstance(rule, dict) else None
            if not isinstance(projection_terms, list) or any(
                not isinstance(item, str) or not item.strip()
                for item in projection_terms
            ):
                raise ValueError(
                    f"{source_path}[{index}].projection_terms must be non-empty strings"
                )
            terms.extend(projection_terms)
    required_terms = projection.get("required_terms")
    if not isinstance(required_terms, list) or any(
        not isinstance(item, str) or not item.strip() for item in required_terms
    ):
        raise ValueError("docs projection required_terms must be non-empty strings")
    terms.extend(required_terms)
    return list(dict.fromkeys(terms))


def _prompt_projection_markers(identifier: str) -> tuple[str, str]:
    return (
        f"<!-- {identifier}:B -->",
        f"<!-- {identifier}:E -->",
    )


def _json_object_without_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def resolve_json_pointer(document: object, pointer: str) -> object:
    """Resolve one RFC 6901 JSON pointer without accepting URI fragments."""

    if pointer == "":
        return document
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ValueError("JSON pointer must be empty or start with '/'")
    current = document
    for raw_part in pointer[1:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if "~" in raw_part.replace("~0", "").replace("~1", ""):
            raise ValueError(f"JSON pointer contains an invalid escape: {pointer!r}")
        if isinstance(current, dict):
            if part not in current:
                raise ValueError(f"JSON pointer does not resolve: {pointer!r}")
            current = current[part]
        elif isinstance(current, list):
            if not part.isdigit() or (part.startswith("0") and part != "0"):
                raise ValueError(f"JSON pointer has an invalid array index: {pointer!r}")
            index = int(part)
            if index >= len(current):
                raise ValueError(f"JSON pointer does not resolve: {pointer!r}")
            current = current[index]
        else:
            raise ValueError(f"JSON pointer traverses a scalar: {pointer!r}")
    return current


def validate_principle_acceptance_contract(
    data: object,
    root: Path = ROOT,
) -> list[str]:
    """Validate the generic executable-outcome graph for all declared principles.

    This validation proves only that the graph is closed, safe to execute, and
    addressable. It never treats a JSON pointer or an existing script as a
    passing principle outcome; only ``eval-core-principles.py`` executes and
    evaluates outcomes.
    """

    errors: list[str] = []

    def exact_keys(value: object, expected: set[str], context: str) -> bool:
        if not isinstance(value, dict):
            errors.append(f"{context} must be an object")
            return False
        if set(value) != expected:
            errors.append(
                f"{context} fields must be exactly {sorted(expected)}, found "
                f"{sorted(value)}"
            )
            return False
        return True

    def identifier(value: object, context: str) -> str | None:
        if not isinstance(value, str) or re.fullmatch(
            r"[a-z0-9]+(?:-[a-z0-9]+)*", value
        ) is None:
            errors.append(f"{context} must be kebab-case")
            return None
        return value

    def strings(
        value: object,
        context: str,
        *,
        nonempty: bool = False,
    ) -> list[str]:
        if not isinstance(value, list) or any(
            not isinstance(item, str) or not item.strip() for item in value
        ):
            errors.append(f"{context} must be a list of non-empty strings")
            return []
        if nonempty and not value:
            errors.append(f"{context} must not be empty")
        if len(value) != len(set(value)):
            errors.append(f"{context} must not contain duplicates")
        return list(value)

    if not isinstance(data, dict):
        return ["authoritative control model must be an object"]
    principles = data.get("core_principles")
    acceptance = data.get("principle_acceptance_contract")
    if not isinstance(principles, list) or len(principles) != 15:
        errors.append("core_principles must contain exactly 15 entries")
        principles = []
    if not exact_keys(
        acceptance,
        {"schema_version", "dimensions", "authorities", "producers", "outcomes"},
        "principle_acceptance_contract",
    ):
        return errors
    assert isinstance(acceptance, dict)
    if acceptance["schema_version"] != 3:
        errors.append("principle_acceptance_contract.schema_version must be 3")

    canonical_principle_ids = {
        principle_id for principle_id, _ in CANONICAL_CORE_PRINCIPLE_IDENTITIES
    }
    dimension_rows: dict[str, dict[str, object]] = {}
    dimension_owners: dict[str, str] = {}
    dimension_capabilities: dict[str, set[str]] = {}
    dimensions = acceptance["dimensions"]
    if not isinstance(dimensions, list) or not dimensions:
        errors.append("principle_acceptance_contract.dimensions must be non-empty")
        dimensions = []
    for index, dimension in enumerate(dimensions):
        context = f"principle_acceptance_contract.dimensions[{index}]"
        if not exact_keys(dimension, {"id", "principle", "capabilities"}, context):
            continue
        assert isinstance(dimension, dict)
        dimension_id = identifier(dimension["id"], f"{context}.id")
        principle_id = dimension["principle"]
        capabilities = strings(
            dimension["capabilities"], f"{context}.capabilities", nonempty=True
        )
        valid_capabilities = {
            capability
            for capability_index, capability in enumerate(capabilities)
            if identifier(
                capability, f"{context}.capabilities[{capability_index}]"
            )
            is not None
        }
        if not isinstance(principle_id, str) or principle_id not in canonical_principle_ids:
            errors.append(f"{context}.principle must name a canonical Core Principle")
            continue
        if dimension_id is None:
            continue
        if not dimension_id.startswith(f"{principle_id}-"):
            errors.append(
                f"{context}.id must be namespaced by its canonical principle id"
            )
        if dimension_id in dimension_rows:
            errors.append("principle acceptance dimension ids must be unique")
            continue
        dimension_rows[dimension_id] = dimension
        dimension_owners[dimension_id] = principle_id
        dimension_capabilities[dimension_id] = valid_capabilities

    authority_values: dict[str, object] = {}
    authority_pointers: dict[str, str] = {}
    authorities = acceptance["authorities"]
    if not isinstance(authorities, list) or not authorities:
        errors.append("principle_acceptance_contract.authorities must be non-empty")
        authorities = []
    for index, authority in enumerate(authorities):
        context = f"principle_acceptance_contract.authorities[{index}]"
        if not exact_keys(authority, {"id", "pointer", "scope"}, context):
            continue
        assert isinstance(authority, dict)
        authority_id = identifier(authority["id"], f"{context}.id")
        pointer = authority["pointer"]
        scope = authority["scope"]
        if not isinstance(scope, str) or not scope.strip():
            errors.append(f"{context}.scope must be non-empty text")
        if authority_id is None:
            continue
        if authority_id in authority_values:
            errors.append("principle acceptance authority ids must be unique")
            continue
        if not isinstance(pointer, str) or not pointer.startswith("/"):
            errors.append(f"{context}.pointer must be a non-root JSON pointer")
            continue
        if pointer.startswith("/principle_acceptance_contract") or pointer.startswith(
            "/core_principles"
        ):
            errors.append(f"{context}.pointer must not make the outcome graph self-containing")
            continue
        try:
            authority_values[authority_id] = resolve_json_pointer(data, pointer)
        except ValueError as exc:
            errors.append(f"{context}.pointer: {exc}")
            continue
        authority_pointers[authority_id] = pointer

    producer_rows: dict[str, dict[str, object]] = {}
    argv_owners: dict[tuple[str, ...], str] = {}
    report_owners: dict[str, str] = {}
    machine_report_owners: dict[str, str] = {}
    producers = acceptance["producers"]
    if not isinstance(producers, list) or not producers:
        errors.append("principle_acceptance_contract.producers must be non-empty")
        producers = []
    safe_arg = re.compile(r"[A-Za-z0-9_./:=+,-]+")
    for index, producer in enumerate(producers):
        context = f"principle_acceptance_contract.producers[{index}]"
        if not exact_keys(
            producer,
            {
                "id",
                "argv",
                "depends_on",
                "reports",
                "release_reports",
                "authority_inputs",
                "timeout_seconds",
            },
            context,
        ):
            continue
        assert isinstance(producer, dict)
        producer_id = identifier(producer["id"], f"{context}.id")
        argv = strings(producer["argv"], f"{context}.argv", nonempty=True)
        dependencies = strings(producer["depends_on"], f"{context}.depends_on")
        reports = strings(producer["reports"], f"{context}.reports")
        release_reports = strings(
            producer["release_reports"], f"{context}.release_reports"
        )
        authority_inputs = strings(
            producer["authority_inputs"], f"{context}.authority_inputs"
        )
        timeout_seconds = producer["timeout_seconds"]
        if (
            not isinstance(timeout_seconds, int)
            or isinstance(timeout_seconds, bool)
            or not MIN_PRODUCER_TIMEOUT_SECONDS
            <= timeout_seconds
            <= MAX_PRODUCER_TIMEOUT_SECONDS
        ):
            errors.append(
                f"{context}.timeout_seconds must be an integer in "
                f"[{MIN_PRODUCER_TIMEOUT_SECONDS}, {MAX_PRODUCER_TIMEOUT_SECONDS}]"
            )
        if producer_id is None:
            continue
        if producer_id in producer_rows:
            errors.append("principle acceptance producer ids must be unique")
            continue
        producer_rows[producer_id] = producer
        if len(argv) < 2 or argv[0] != "python3":
            errors.append(f"{context}.argv must start with python3 and one script path")
        elif argv[1] in {"-c", "-m"}:
            errors.append(f"{context}.argv must execute one repository script path")
        else:
            script = PurePosixPath(argv[1])
            if (
                script.is_absolute()
                or not script.parts
                or script.parts[0] != "scripts"
                or script.suffix != ".py"
                or ".." in script.parts
            ):
                errors.append(f"{context}.argv script must be a safe scripts/*.py path")
            elif script.as_posix() == "scripts/eval-core-principles.py":
                errors.append(f"{context}.argv must not recursively execute the evaluator")
            elif not (root / script).is_file():
                errors.append(f"{context}.argv script does not exist: {script.as_posix()}")
        for argument in argv[2:]:
            if safe_arg.fullmatch(argument) is None or ".." in PurePosixPath(argument).parts:
                errors.append(f"{context}.argv contains a disallowed argument {argument!r}")
        canonical_argv = tuple(argv)
        prior_argv_owner = argv_owners.get(canonical_argv)
        if canonical_argv and prior_argv_owner is not None:
            errors.append(
                f"{context}.argv duplicates producer {prior_argv_owner!r}; canonical argv must be unique"
            )
        elif canonical_argv:
            argv_owners[canonical_argv] = producer_id
        for report in reports:
            report_path = PurePosixPath(report)
            if (
                report_path.is_absolute()
                or not report_path.parts
                or report_path.parts[0] != "reports"
                or report_path.suffix != ".json"
                or ".." in report_path.parts
            ):
                errors.append(f"{context}.reports contains an unsafe JSON report path {report!r}")
                continue
            if report in {
                "reports/core-principles-outcomes.json",
                "reports/core-principles-outcomes.md",
            }:
                errors.append(f"{context}.reports must not include the evaluator's own report")
            prior_report_owner = report_owners.get(report)
            if prior_report_owner is not None:
                errors.append(
                    f"{context}.reports reuses {report!r} from producer {prior_report_owner!r}"
                )
            else:
                report_owners[report] = producer_id
                machine_report_owners[report] = producer_id
        for report in release_reports:
            report_path = PurePosixPath(report)
            if (
                report_path.is_absolute()
                or not report_path.parts
                or report_path.parts[0] != "reports"
                or report_path.suffix != ".md"
                or ".." in report_path.parts
            ):
                errors.append(
                    f"{context}.release_reports contains an unsafe Markdown report path {report!r}"
                )
                continue
            if report == "reports/core-principles-outcomes.md":
                errors.append(
                    f"{context}.release_reports must not include the evaluator's own projection"
                )
            prior_report_owner = report_owners.get(report)
            if prior_report_owner is not None:
                errors.append(
                    f"{context}.release_reports reuses {report!r} from producer {prior_report_owner!r}"
                )
            else:
                report_owners[report] = producer_id
        if release_reports and not reports:
            errors.append(
                f"{context}.release_reports requires a canonical JSON report"
            )
        if producer_id in dependencies:
            errors.append(f"{context}.depends_on must not contain the producer itself")

    producer_ids = set(producer_rows)
    for producer_id, producer in producer_rows.items():
        dependencies = producer.get("depends_on", [])
        unknown_dependencies = sorted(set(dependencies) - producer_ids)
        if unknown_dependencies:
            errors.append(
                f"producer {producer_id!r} depends on unknown producers {unknown_dependencies}"
            )
        unknown_authorities = sorted(
            set(producer.get("authority_inputs", [])) - set(authority_values)
        )
        if unknown_authorities:
            errors.append(
                f"producer {producer_id!r} references unknown authorities {unknown_authorities}"
            )

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(producer_id: str, path: list[str]) -> None:
        if producer_id in visited:
            return
        if producer_id in visiting:
            start = path.index(producer_id) if producer_id in path else 0
            errors.append(
                "principle acceptance producer dependency cycle: "
                + " -> ".join([*path[start:], producer_id])
            )
            return
        visiting.add(producer_id)
        for dependency in producer_rows[producer_id].get("depends_on", []):
            if dependency in producer_rows:
                visit(str(dependency), [*path, producer_id])
        visiting.remove(producer_id)
        visited.add(producer_id)

    for producer_id in producer_rows:
        visit(producer_id, [])

    outcome_rows: dict[str, dict[str, object]] = {}
    outcome_dimensions: dict[str, set[str]] = {}
    outcome_capabilities: dict[str, set[str]] = {}
    producer_outcomes: dict[str, set[str]] = {}
    report_predicate_consumers: set[str] = set()
    report_schema_consumers: set[str] = set()
    outcomes = acceptance["outcomes"]
    if not isinstance(outcomes, list) or not outcomes:
        errors.append("principle_acceptance_contract.outcomes must be non-empty")
        outcomes = []
    for index, outcome in enumerate(outcomes):
        context = f"principle_acceptance_contract.outcomes[{index}]"
        if not exact_keys(
            outcome,
            {"id", "producer", "dimensions", "capabilities", "predicates"},
            context,
        ):
            continue
        assert isinstance(outcome, dict)
        outcome_id = identifier(outcome["id"], f"{context}.id")
        producer_id = outcome["producer"]
        if not isinstance(producer_id, str) or producer_id not in producer_rows:
            errors.append(f"{context}.producer must reference a declared producer")
            continue
        if outcome_id is None:
            continue
        if outcome_id in outcome_rows:
            errors.append("principle acceptance outcome ids must be unique")
            continue
        outcome_rows[outcome_id] = outcome
        producer_outcomes.setdefault(producer_id, set()).add(outcome_id)
        tagged_dimensions = set(
            strings(outcome["dimensions"], f"{context}.dimensions", nonempty=True)
        )
        tagged_capabilities = set(
            strings(outcome["capabilities"], f"{context}.capabilities", nonempty=True)
        )
        unknown_dimensions = sorted(tagged_dimensions - set(dimension_rows))
        if unknown_dimensions:
            errors.append(f"{context} references unknown dimensions {unknown_dimensions}")
        allowed_capabilities = set().union(
            *(
                dimension_capabilities[dimension_id]
                for dimension_id in tagged_dimensions
                if dimension_id in dimension_capabilities
            ),
            set(),
        )
        disallowed_capabilities = sorted(tagged_capabilities - allowed_capabilities)
        if disallowed_capabilities:
            errors.append(
                f"{context} capability tags are not allowed by its dimensions "
                f"{disallowed_capabilities}"
            )
        for dimension_id in sorted(tagged_dimensions & set(dimension_rows)):
            if not tagged_capabilities & dimension_capabilities[dimension_id]:
                errors.append(
                    f"{context} has no capability tag for dimension {dimension_id!r}"
                )
        outcome_dimensions[outcome_id] = tagged_dimensions
        outcome_capabilities[outcome_id] = tagged_capabilities
        predicates = outcome["predicates"]
        if not isinstance(predicates, list) or not predicates:
            errors.append(f"{context}.predicates must be a non-empty closed list")
            continue
        process_exit_predicates = 0
        for predicate_index, predicate in enumerate(predicates):
            predicate_context = f"{context}.predicates[{predicate_index}]"
            if not isinstance(predicate, dict):
                errors.append(f"{predicate_context} must be an object")
                continue
            expected_keys = {"source", "pointer", "operator"}
            if "expected" in predicate:
                expected_keys.add("expected")
            if "expected_from" in predicate:
                expected_keys.add("expected_from")
            if set(predicate) != expected_keys or not (
                ("expected" in predicate) ^ ("expected_from" in predicate)
            ):
                errors.append(
                    f"{predicate_context} must contain source, pointer, operator, and "
                    "exactly one of expected or expected_from"
                )
                continue
            source = predicate["source"]
            pointer = predicate["pointer"]
            operator = predicate["operator"]
            if operator not in PRINCIPLE_PREDICATE_OPERATORS:
                errors.append(f"{predicate_context}.operator is not allowed")
            if not isinstance(pointer, str) or not pointer.startswith("/"):
                errors.append(f"{predicate_context}.pointer must be a non-root JSON pointer")
            declared_reports = set(producer_rows[producer_id].get("reports", []))
            if source == "process":
                if pointer == "/exit_code" and operator == "equals" and predicate.get(
                    "expected"
                ) == 0:
                    process_exit_predicates += 1
            elif not isinstance(source, str) or source not in declared_reports:
                errors.append(
                    f"{predicate_context}.source must be process or a report declared by "
                    f"producer {producer_id!r}"
                )
            else:
                report_predicate_consumers.add(source)
                if (
                    pointer == "/schema_version"
                    and operator == "equals"
                    and isinstance(predicate.get("expected"), int)
                    and not isinstance(predicate.get("expected"), bool)
                    and predicate["expected"] > 0
                ):
                    report_schema_consumers.add(source)
            if "expected_from" in predicate:
                expected_from = predicate["expected_from"]
                if not exact_keys(
                    expected_from,
                    {"authority", "pointer"},
                    f"{predicate_context}.expected_from",
                ):
                    continue
                assert isinstance(expected_from, dict)
                authority_id = expected_from["authority"]
                expected_pointer = expected_from["pointer"]
                if authority_id not in producer_rows[producer_id].get(
                    "authority_inputs", []
                ):
                    errors.append(
                        f"{predicate_context}.expected_from authority must be an actual "
                        f"input of producer {producer_id!r}"
                    )
                elif authority_id in authority_values:
                    try:
                        resolve_json_pointer(
                            authority_values[authority_id], expected_pointer
                        )
                    except (TypeError, ValueError) as exc:
                        errors.append(f"{predicate_context}.expected_from.pointer: {exc}")
        if process_exit_predicates != 1:
            errors.append(
                f"{context}.predicates must contain exactly one process /exit_code equals 0 predicate"
            )

    outcome_ids = set(outcome_rows)
    referenced_outcomes: set[str] = set()
    principle_ids: set[str] = set()
    principle_names: set[str] = set()
    principle_required_outcomes: dict[str, set[str]] = {}
    principle_required_dimensions: dict[str, set[str]] = {}
    declared_identities = [
        (principle.get("id"), principle.get("name"))
        for principle in principles
        if isinstance(principle, dict)
    ]
    if declared_identities != list(CANONICAL_CORE_PRINCIPLE_IDENTITIES):
        errors.append(
            "core_principles canonical identities or order have drifted"
        )
    for index, principle in enumerate(principles):
        context = f"core_principles[{index}]"
        if not exact_keys(
            principle,
            {"id", "name", "required_dimensions", "required_outcomes"},
            context,
        ):
            continue
        assert isinstance(principle, dict)
        principle_id = identifier(principle["id"], f"{context}.id")
        name = principle["name"]
        if principle_id is not None:
            if principle_id in principle_ids:
                errors.append("core principle ids must be unique")
            principle_ids.add(principle_id)
        if not isinstance(name, str) or not name.strip():
            errors.append(f"{context}.name must be non-empty text")
        elif name in principle_names:
            errors.append("core principle names must be unique")
        else:
            principle_names.add(name)
        required_dimensions = set(
            strings(
                principle["required_dimensions"],
                f"{context}.required_dimensions",
                nonempty=True,
            )
        )
        unknown_dimensions = sorted(required_dimensions - set(dimension_rows))
        if unknown_dimensions:
            errors.append(
                f"{context} references unknown required dimensions {unknown_dimensions}"
            )
        if principle_id is not None:
            allowed_dimensions = {
                dimension_id
                for dimension_id, owner in dimension_owners.items()
                if owner == principle_id
            }
            if required_dimensions != allowed_dimensions:
                errors.append(
                    f"{context}.required_dimensions must exactly match its allowed "
                    f"dimension catalog {sorted(allowed_dimensions)}"
                )
            principle_required_dimensions[principle_id] = required_dimensions
        required = principle["required_outcomes"]
        if not exact_keys(required, {"authoring", "formal_release"}, f"{context}.required_outcomes"):
            continue
        assert isinstance(required, dict)
        authoring = strings(
            required["authoring"],
            f"{context}.required_outcomes.authoring",
            nonempty=True,
        )
        formal = strings(
            required["formal_release"],
            f"{context}.required_outcomes.formal_release",
        )
        unknown = sorted((set(authoring) | set(formal)) - outcome_ids)
        if unknown:
            errors.append(f"{context} references unknown outcomes {unknown}")
        overlap = sorted(set(authoring) & set(formal))
        if overlap:
            errors.append(
                f"{context} repeats authoring outcomes in formal_release {overlap}"
            )
        referenced_outcomes.update(authoring)
        referenced_outcomes.update(formal)
        if principle_id is not None:
            principle_required_outcomes[principle_id] = set(authoring) | set(formal)

    for principle_id in canonical_principle_ids:
        required_outcome_ids = principle_required_outcomes.get(principle_id, set())
        required_dimension_ids = principle_required_dimensions.get(principle_id, set())
        covered_dimensions: set[str] = set()
        covered_capabilities: dict[str, set[str]] = {
            dimension_id: set() for dimension_id in required_dimension_ids
        }
        for outcome_id in required_outcome_ids & set(outcome_rows):
            for dimension_id in outcome_dimensions.get(outcome_id, set()):
                if dimension_owners.get(dimension_id) != principle_id:
                    continue
                covered_dimensions.add(dimension_id)
                covered_capabilities.setdefault(dimension_id, set()).update(
                    outcome_capabilities.get(outcome_id, set())
                )
        if covered_dimensions != required_dimension_ids:
            errors.append(
                f"core principle {principle_id!r} required outcome tags must exactly "
                f"cover required_dimensions; covered {sorted(covered_dimensions)}"
            )
        for dimension_id in sorted(required_dimension_ids & set(dimension_rows)):
            missing_capabilities = sorted(
                dimension_capabilities[dimension_id]
                - covered_capabilities.get(dimension_id, set())
            )
            if missing_capabilities:
                errors.append(
                    f"core principle {principle_id!r} dimension {dimension_id!r} "
                    f"lacks required outcome capability coverage {missing_capabilities}"
                )

    for outcome_id, tagged_dimensions in outcome_dimensions.items():
        for dimension_id in tagged_dimensions & set(dimension_rows):
            owner = dimension_owners[dimension_id]
            if outcome_id not in principle_required_outcomes.get(owner, set()):
                errors.append(
                    f"outcome {outcome_id!r} tags dimension {dimension_id!r} but is "
                    f"not required by its owner principle {owner!r}"
                )

    orphan_outcomes = sorted(outcome_ids - referenced_outcomes)
    if orphan_outcomes:
        errors.append(f"principle acceptance outcomes contain orphans {orphan_outcomes}")
    orphan_producers = sorted(producer_ids - set(producer_outcomes))
    if orphan_producers:
        errors.append(f"principle acceptance producers contain orphans {orphan_producers}")
    orphan_reports = sorted(set(machine_report_owners) - report_predicate_consumers)
    if orphan_reports:
        errors.append(f"principle acceptance reports contain orphans {orphan_reports}")
    reports_without_schema = sorted(
        set(machine_report_owners) - report_schema_consumers
    )
    if reports_without_schema:
        errors.append(
            "principle acceptance reports lack a closed schema_version predicate "
            f"{reports_without_schema}"
        )
    authority_consumers: dict[str, set[str]] = {key: set() for key in authority_values}
    for producer_id, producer in producer_rows.items():
        for authority_id in producer.get("authority_inputs", []):
            if authority_id in authority_consumers:
                authority_consumers[authority_id].add(producer_id)
    orphan_authorities = sorted(
        authority_id
        for authority_id, consumers in authority_consumers.items()
        if not consumers
    )
    if orphan_authorities:
        errors.append(
            f"principle acceptance authorities have no actual producer consumer {orphan_authorities}"
        )
    return errors


def professional_review_skill_ids(professional_entries: object) -> tuple[str, ...]:
    """Select Review expertise from the current Professional role declarations."""

    if not isinstance(professional_entries, list):
        raise ValidationProblem("professional Skill registry entries must be a list")
    selected: list[str] = []
    for index, entry in enumerate(professional_entries):
        if not isinstance(entry, dict):
            raise ValidationProblem(
                f"professional Skill registry entry {index} must be an object"
            )
        roles = entry.get("role_support")
        if not isinstance(roles, list):
            continue
        if "review-agent" not in roles:
            continue
        name = entry.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValidationProblem(
                f"review-capable professional Skill entry {index} requires a name"
            )
        selected.append(name)
    return tuple(selected)


TEST_LAYER_ORDER = ["unit", "integration", "contract", "governance", "release"]


def _test_layer_for_module(test_selection: dict[str, Any], module: str) -> str:
    overrides = {
        row["module"]: row["layer"]
        for row in test_selection.get("module_overrides", [])
        if isinstance(row, dict)
        and isinstance(row.get("module"), str)
        and isinstance(row.get("layer"), str)
    }
    return overrides.get(module, str(test_selection.get("default_layer", "")))


def unit_test_dependency_errors(
    root: Path,
    test_selection: dict[str, Any],
) -> list[str]:
    """Reject unit tests coupled to workspace outputs or another test layer."""

    errors: list[str] = []
    policy = test_selection.get("unit_dependency_policy", {})
    forbidden_roots = policy.get("forbidden_workspace_roots", [])
    forbidden_layers = set(policy.get("forbidden_test_layers", []))
    overrides = {
        row["module"]: row["layer"]
        for row in test_selection.get("module_overrides", [])
        if isinstance(row, dict)
        and isinstance(row.get("module"), str)
        and isinstance(row.get("layer"), str)
    }
    tests_root = root / "tests"
    if not tests_root.is_dir():
        return errors
    def canonical_test_import(dotted: str) -> str | None:
        parts = dotted.split(".")
        if not parts or parts[0] != "tests":
            return None
        for index, part in enumerate(parts):
            if part != "tests" and part.startswith("test"):
                return "/".join(parts[: index + 1]) + ".py"
        return None

    def imported_test_modules(
        tokens: list[tokenize.TokenInfo],
    ) -> list[tuple[str, int]]:
        imports: list[tuple[str, int]] = []
        for index, token in enumerate(tokens):
            if token.type != tokenize.NAME or token.string not in {"from", "import"}:
                continue
            if token.string == "from":
                cursor = index + 1
                package_parts: list[str] = []
                while cursor < len(tokens):
                    current = tokens[cursor]
                    if current.type == tokenize.NAME and current.string == "import":
                        break
                    if current.type == tokenize.NEWLINE:
                        break
                    if current.type == tokenize.NAME or (
                        current.type == tokenize.OP and current.string == "."
                    ):
                        package_parts.append(current.string)
                    cursor += 1
                if cursor >= len(tokens) or tokens[cursor].string != "import":
                    continue
                package = "".join(package_parts)
                package_test = canonical_test_import(package)
                if package_test is not None:
                    imports.append((package_test, token.start[0]))
                    continue
                expect_name = True
                skip_alias = False
                cursor += 1
                while cursor < len(tokens) and tokens[cursor].type != tokenize.NEWLINE:
                    current = tokens[cursor]
                    if current.type == tokenize.OP and current.string == ",":
                        expect_name = True
                        skip_alias = False
                    elif current.type == tokenize.NAME and current.string == "as":
                        skip_alias = True
                    elif current.type == tokenize.NAME and expect_name:
                        if not skip_alias:
                            imported = canonical_test_import(
                                f"{package}.{current.string}"
                            )
                            if imported is not None:
                                imports.append((imported, current.start[0]))
                        expect_name = False
                    cursor += 1
                continue

            cursor = index + 1
            module_parts: list[str] = []
            while cursor < len(tokens) and tokens[cursor].type != tokenize.NEWLINE:
                current = tokens[cursor]
                if current.type == tokenize.OP and current.string == ",":
                    imported = canonical_test_import("".join(module_parts))
                    if imported is not None:
                        imports.append((imported, token.start[0]))
                    module_parts = []
                elif current.type == tokenize.NAME and current.string == "as":
                    imported = canonical_test_import("".join(module_parts))
                    if imported is not None:
                        imports.append((imported, token.start[0]))
                    module_parts = []
                    cursor += 1
                elif current.type == tokenize.NAME or (
                    current.type == tokenize.OP and current.string == "."
                ):
                    module_parts.append(current.string)
                cursor += 1
            imported = canonical_test_import("".join(module_parts))
            if imported is not None:
                imports.append((imported, token.start[0]))
        return imports

    for path in sorted(tests_root.rglob("test*.py")):
        module = path.relative_to(root).as_posix()
        if overrides.get(module, test_selection.get("default_layer")) != "unit":
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"unit test dependency audit cannot read {module}: {exc}")
            continue
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
        significant = [
            token
            for token in tokens
            if token.type
            not in {
                tokenize.ENCODING,
                tokenize.ENDMARKER,
                tokenize.INDENT,
                tokenize.DEDENT,
                tokenize.NEWLINE,
                tokenize.NL,
                tokenize.COMMENT,
            }
        ]
        for index in range(len(significant) - 2):
            owner, slash, literal = significant[index : index + 3]
            if owner.type != tokenize.NAME or owner.string not in {
                "ROOT",
                "REPOSITORY_ROOT",
            }:
                continue
            if slash.type != tokenize.OP or slash.string != "/":
                continue
            if literal.type != tokenize.STRING:
                continue
            matched_literal = re.fullmatch(
                r"(?i:[rubf]*)(?:'([^'\n]*)'|\"([^\"\n]*)\")",
                literal.string,
            )
            if matched_literal is None:
                continue
            value = matched_literal.group(1) or matched_literal.group(2) or ""
            workspace_root = value.split("/", 1)[0]
            if workspace_root in forbidden_roots:
                errors.append(
                    f"unit test {module}:{owner.start[0]} depends on workspace "
                    f"{workspace_root}/"
                )
        for imported_path, line_number in imported_test_modules(tokens):
            imported_layer = overrides.get(
                imported_path, test_selection.get("default_layer")
            )
            if imported_layer in forbidden_layers:
                errors.append(
                    f"unit test {module}:{line_number} imports {imported_layer} "
                    f"test {imported_path}"
                )
    return errors


def validate_impact_graph_contract(
    data: object,
    root: Path = ROOT,
) -> list[str]:
    """Validate the single Core-owned affected producer and test graph."""

    errors: list[str] = []
    if not isinstance(data, dict):
        return ["authoritative control model must be an object"]
    contract = data.get("impact_graph_contract")
    contract_fields = {
        "schema_version",
        "resolver",
        "producer_source",
        "test_selection",
        "stages",
        "known_no_impact_patterns",
        "rules",
    }
    if not isinstance(contract, dict) or set(contract) != contract_fields:
        actual = sorted(contract) if isinstance(contract, dict) else []
        errors.append(
            "impact_graph_contract fields must be exactly "
            f"{sorted(contract_fields)}, found {actual}"
        )
        return errors
    if contract["schema_version"] != 1:
        errors.append("impact_graph_contract.schema_version must be 1")
    resolver = contract["resolver"]
    if resolver != "scripts/impact_graph.py" or not (root / str(resolver)).is_file():
        errors.append(
            "impact_graph_contract.resolver must name existing scripts/impact_graph.py"
        )
    if contract["producer_source"] != "/principle_acceptance_contract/producers":
        errors.append(
            "impact_graph_contract.producer_source must reference canonical producers"
        )

    test_selection = contract["test_selection"]
    test_selection_fields = {
        "order",
        "default_layer",
        "module_overrides",
        "unit_dependency_policy",
    }
    if (
        not isinstance(test_selection, dict)
        or set(test_selection) != test_selection_fields
    ):
        errors.append(
            "impact_graph_contract.test_selection fields must be exactly "
            f"{sorted(test_selection_fields)}"
        )
        return errors
    if test_selection["order"] != TEST_LAYER_ORDER:
        errors.append(
            "impact_graph_contract.test_selection.order must be exactly "
            f"{TEST_LAYER_ORDER}"
        )
    if test_selection["default_layer"] != "unit":
        errors.append("impact graph default test layer must be unit")
    overrides = test_selection["module_overrides"]
    override_modules: list[str] = []
    if not isinstance(overrides, list):
        errors.append("test selection module_overrides must be a list")
        overrides = []
    for index, override in enumerate(overrides):
        context = f"impact_graph_contract.test_selection.module_overrides[{index}]"
        if not isinstance(override, dict) or set(override) != {"module", "layer"}:
            errors.append(f"{context} fields must be module and layer")
            continue
        module = override["module"]
        layer = override["layer"]
        module_path = PurePosixPath(module) if isinstance(module, str) else None
        if (
            module_path is None
            or module_path.is_absolute()
            or not module_path.parts
            or module_path.parts[0] != "tests"
            or ".." in module_path.parts
            or module_path.suffix != ".py"
            or not module_path.name.startswith("test")
        ):
            errors.append(f"{context}.module must be a safe tests/ test module")
        else:
            override_modules.append(module)
            if not (root / module_path).is_file():
                errors.append(f"{context}.module does not exist: {module}")
        if layer not in TEST_LAYER_ORDER or layer == "unit":
            errors.append(f"{context}.layer must name one non-unit canonical layer")
    if len(override_modules) != len(set(override_modules)):
        errors.append("test selection module override paths must be unique")
    unit_policy = test_selection["unit_dependency_policy"]
    if unit_policy != {
        "forbidden_workspace_roots": ["dist", "reports"],
        "forbidden_test_layers": [
            "integration",
            "contract",
            "governance",
            "release",
        ],
    }:
        errors.append("unit dependency policy must forbid dist, reports, and non-unit tests")

    acceptance = data.get("principle_acceptance_contract")
    producer_ids = (
        {
            producer.get("id")
            for producer in acceptance.get("producers", [])
            if isinstance(producer, dict)
            and isinstance(producer.get("id"), str)
        }
        if isinstance(acceptance, dict)
        else set()
    )
    authorities = (
        acceptance.get("authorities", []) if isinstance(acceptance, dict) else []
    )
    authority_matches = [
        authority
        for authority in authorities
        if isinstance(authority, dict)
        and (
            authority.get("id") == "impact-graph-authority"
            or authority.get("pointer") == "/impact_graph_contract"
        )
    ]
    if (
        len(authority_matches) != 1
        or authority_matches[0].get("id") != "impact-graph-authority"
        or authority_matches[0].get("pointer") != "/impact_graph_contract"
    ):
        errors.append(
            "impact_graph_contract must have exactly one impact-graph-authority pointer"
        )

    stages = contract["stages"]
    if not isinstance(stages, dict) or set(stages) != {"affected", "ci-tests"}:
        errors.append("impact_graph_contract.stages must be affected and ci-tests")
        return errors
    affected = stages["affected"]
    affected_fields = {
        "runtime_build",
        "dependency_closure",
        "expert_panel_evidence_projection",
        "isolated_execution",
        "test_policy",
        "eligible_producer_ids",
        "professionalism",
    }
    if not isinstance(affected, dict) or set(affected) != affected_fields:
        errors.append(
            "impact_graph_contract.stages.affected fields must be exactly "
            f"{sorted(affected_fields)}"
        )
        return errors
    eligible = affected["eligible_producer_ids"]
    if (
        not isinstance(eligible, list)
        or not eligible
        or any(not isinstance(item, str) or not item for item in eligible)
        or len(eligible) != len(set(eligible))
    ):
        errors.append("affected eligible_producer_ids must be non-empty unique strings")
        eligible = []
    unknown_eligible = sorted(set(eligible) - producer_ids)
    if unknown_eligible:
        errors.append(
            f"affected eligible_producer_ids contain unknown producers {unknown_eligible}"
        )
    if affected["dependency_closure"] is not True:
        errors.append("affected stage must enable canonical producer dependency closure")
    if affected["isolated_execution"] is not True:
        errors.append("affected stage must require isolated execution")
    runtime_projection = affected["runtime_build"]
    expected_runtime_projection = {
        "runtime_name": "recommended",
        "producer_id": "build-recommended",
        "package_layers": ["professional", "foundation", "domain"],
        "unknown_package_policy": "runtime",
    }
    if runtime_projection != expected_runtime_projection:
        errors.append(
            "affected runtime_build must match the canonical single Runtime graph"
        )
    elif runtime_projection["producer_id"] not in eligible:
        errors.append("affected Runtime producer must be stage-eligible")
    if affected["test_policy"] != {
        "always_layers": ["unit", "contract"],
        "direct_only_layers": ["integration", "governance"],
        "forbidden_layers": ["release"],
    }:
        errors.append(
            "affected test policy must always select unit/contract, select "
            "integration/governance only by direct impact, and forbid release"
        )
    professionalism = affected["professionalism"]
    professionalism_fields = {
        "schema_version",
        "context_environment",
        "producer_id",
        "registry_sources",
        "full_scope_patterns",
    }
    if (
        not isinstance(professionalism, dict)
        or set(professionalism) != professionalism_fields
    ):
        errors.append(
            "affected professionalism fields must be exactly "
            f"{sorted(professionalism_fields)}"
        )
        return errors
    if professionalism["schema_version"] != 1:
        errors.append("affected professionalism schema_version must be 1")
    if professionalism["context_environment"] != "CHANGEFORGE_AFFECTED_CONTEXT":
        errors.append(
            "affected professionalism context_environment must be "
            "CHANGEFORGE_AFFECTED_CONTEXT"
        )
    if professionalism["producer_id"] != "eval-skill-professionalism":
        errors.append(
            "affected professionalism producer_id must be eval-skill-professionalism"
        )
    if professionalism["producer_id"] not in eligible:
        errors.append("affected professionalism producer must be stage-eligible")
    registry_sources = professionalism["registry_sources"]
    expected_registry_sources = [
        {
            "path": "src/registry/professional-skills.yaml",
            "collection": "professional_skills",
            "layer": "professional",
        },
        {
            "path": "src/registry/foundation-skills.yaml",
            "collection": "foundation_skills",
            "layer": "foundation",
        },
        {
            "path": "src/registry/domain-skills.yaml",
            "collection": "domain_skills",
            "layer": "domain",
        },
    ]
    if registry_sources != expected_registry_sources:
        errors.append(
            "affected professionalism registry_sources must name the three "
            "canonical non-Control registries"
        )
    full_scope_patterns_value = professionalism["full_scope_patterns"]
    if (
        not isinstance(full_scope_patterns_value, list)
        or not full_scope_patterns_value
        or any(
            not isinstance(item, str) or not item
            for item in full_scope_patterns_value
        )
        or len(full_scope_patterns_value) != len(set(full_scope_patterns_value))
    ):
        errors.append(
            "impact_graph_contract.stages.affected.professionalism."
            "full_scope_patterns must be non-empty unique strings"
        )
        full_scope_patterns: list[str] = []
    else:
        full_scope_patterns = list(full_scope_patterns_value)
        for pattern in full_scope_patterns:
            candidate = PurePosixPath(pattern)
            if (
                candidate.is_absolute()
                or not candidate.parts
                or ".." in candidate.parts
                or "\\" in pattern
                or "\x00" in pattern
            ):
                errors.append(
                    "impact_graph_contract.stages.affected.professionalism."
                    f"full_scope_patterns contains unsafe pattern {pattern!r}"
                )
    expected_full_scope_patterns = [
        "scripts/eval-skill-professionalism.py",
        "scripts/expert_panel_contracts.py",
    ]
    if full_scope_patterns != expected_full_scope_patterns:
        errors.append(
            "affected professionalism full_scope_patterns must contain only "
            "the static evaluator and explicit Professional semantic-contract authority"
        )

    evidence_projection = affected["expert_panel_evidence_projection"]
    evidence_fields = {
        "schema_version",
        "unchanged_status",
        "affected_status",
        "axis_order",
        "axis_sources",
    }
    if (
        not isinstance(evidence_projection, dict)
        or set(evidence_projection) != evidence_fields
    ):
        errors.append(
            "affected expert_panel_evidence_projection fields must be exactly "
            f"{sorted(evidence_fields)}"
        )
    else:
        axis_order = [
            "readability",
            "semantic-disposition",
            "professional-completeness",
        ]
        if evidence_projection["schema_version"] != 1:
            errors.append("affected Expert Panel evidence schema_version must be 1")
        if evidence_projection["unchanged_status"] != "unchanged":
            errors.append("unaffected Expert Panel evidence status must be unchanged")
        if evidence_projection["affected_status"] != "soft-stale":
            errors.append("affected Expert Panel evidence status must be soft-stale")
        if evidence_projection["axis_order"] != axis_order:
            errors.append("affected Expert Panel evidence axis order is invalid")
        axis_sources = evidence_projection["axis_sources"]
        if not isinstance(axis_sources, list):
            errors.append("affected Expert Panel evidence axis_sources must be a list")
            axis_sources = []
        actual_axes: list[str] = []
        paths_by_axis: dict[str, list[str]] = {}
        for index, source in enumerate(axis_sources):
            context = (
                "impact_graph_contract.stages.affected."
                f"expert_panel_evidence_projection.axis_sources[{index}]"
            )
            if not isinstance(source, dict) or set(source) != {
                "axis",
                "path_patterns",
            }:
                errors.append(f"{context} fields must be axis and path_patterns")
                continue
            axis = source["axis"]
            if not isinstance(axis, str):
                errors.append(f"{context}.axis must be a string")
                continue
            actual_axes.append(axis)
            patterns = source["path_patterns"]
            if (
                not isinstance(patterns, list)
                or not patterns
                or any(not isinstance(pattern, str) or not pattern for pattern in patterns)
                or len(patterns) != len(set(patterns))
            ):
                errors.append(f"{context}.path_patterns must be non-empty unique strings")
                continue
            paths_by_axis[axis] = list(patterns)
            for pattern in patterns:
                candidate = PurePosixPath(pattern)
                if (
                    candidate.is_absolute()
                    or not candidate.parts
                    or ".." in candidate.parts
                    or "\\" in pattern
                    or "\x00" in pattern
                ):
                    errors.append(f"{context} contains unsafe pattern {pattern!r}")
        if actual_axes != axis_order:
            errors.append("affected Expert Panel evidence axis sources are invalid")
        required_axis_sources = {
            "readability": {
                "scripts/audit-skill-content.py",
                "scripts/expert_panel_contracts.py",
                "evals/expert-panel/readability.json",
            },
            "semantic-disposition": {
                "scripts/audit-skill-content.py",
                "scripts/expert_panel_contracts.py",
                "evals/expert-panel/semantic-disposition.json",
            },
            "professional-completeness": {
                "scripts/expert_panel_contracts.py",
                "scripts/professional_completeness_carry_forward.py",
                "evals/expert-panel/professional-completeness.json",
            },
        }
        for axis, required in required_axis_sources.items():
            missing = sorted(required - set(paths_by_axis.get(axis, [])))
            if missing:
                errors.append(
                    f"affected Expert Panel evidence axis {axis!r} lacks sources {missing}"
                )
    ci_tests = stages["ci-tests"]
    ci_fields = {"runner", "test_self_patterns"}
    if not isinstance(ci_tests, dict) or set(ci_tests) != ci_fields:
        errors.append(
            "impact_graph_contract.stages.ci-tests fields must be exactly "
            f"{sorted(ci_fields)}"
        )
        return errors
    runner = ci_tests["runner"]
    if runner != "scripts/run-ci-tests.py" or not (root / str(runner)).is_file():
        errors.append("ci-tests runner must name existing scripts/run-ci-tests.py")
    if ci_tests["test_self_patterns"] != ["tests/**/test*.py"]:
        errors.append("ci-tests test_self_patterns must contain only tests/**/test*.py")

    def safe_patterns(value: object, context: str, *, nonempty: bool) -> list[str]:
        if (
            not isinstance(value, list)
            or (nonempty and not value)
            or any(not isinstance(item, str) or not item for item in value)
            or len(value) != len(set(value))
        ):
            errors.append(f"{context} must be {'non-empty ' if nonempty else ''}unique strings")
            return []
        result = list(value)
        for pattern in result:
            path = PurePosixPath(pattern)
            if (
                path.is_absolute()
                or not path.parts
                or ".." in path.parts
                or "\\" in pattern
                or "\x00" in pattern
            ):
                errors.append(f"{context} contains unsafe pattern {pattern!r}")
        return result

    no_impact_patterns = safe_patterns(
        contract["known_no_impact_patterns"],
        "impact_graph_contract.known_no_impact_patterns",
        nonempty=True,
    )
    rules = contract["rules"]
    if not isinstance(rules, list) or not rules:
        errors.append("impact_graph_contract.rules must be non-empty")
        return errors
    rule_fields = {"id", "path_patterns", "producer_ids", "test_modules"}
    seen_ids: set[str] = set()
    pattern_owners: dict[str, str] = {
        pattern: "known-no-impact" for pattern in no_impact_patterns
    }
    for index, rule in enumerate(rules):
        context = f"impact_graph_contract.rules[{index}]"
        if not isinstance(rule, dict) or set(rule) != rule_fields:
            errors.append(f"{context} fields must be exactly {sorted(rule_fields)}")
            continue
        rule_id = rule["id"]
        if not isinstance(rule_id, str) or re.fullmatch(
            r"[a-z0-9]+(?:-[a-z0-9]+)*", rule_id
        ) is None:
            errors.append(f"{context}.id must be kebab-case")
        elif rule_id in seen_ids:
            errors.append("impact_graph_contract rule ids must be unique")
        else:
            seen_ids.add(rule_id)
        patterns = safe_patterns(
            rule["path_patterns"], f"{context}.path_patterns", nonempty=True
        )
        for pattern in patterns:
            prior = pattern_owners.get(pattern)
            if prior is not None:
                errors.append(
                    f"impact graph path pattern {pattern!r} is declared by both "
                    f"{prior!r} and {rule_id!r}"
                )
            elif isinstance(rule_id, str):
                pattern_owners[pattern] = rule_id

        mapped_producers = rule["producer_ids"]
        if (
            not isinstance(mapped_producers, list)
            or any(
                not isinstance(producer_id, str) or not producer_id
                for producer_id in mapped_producers
            )
            or len(mapped_producers) != len(set(mapped_producers))
        ):
            errors.append(f"{context}.producer_ids must be unique strings")
            mapped_producers = []
        else:
            for producer_id in mapped_producers:
                if producer_id not in producer_ids:
                    errors.append(
                        f"{context}.producer_ids contains unknown producer id "
                        f"{producer_id!r}"
                    )
                elif producer_id not in eligible:
                    errors.append(
                        f"{context}.producer_ids contains stage-ineligible producer id "
                        f"{producer_id!r}"
                    )

        test_modules = rule["test_modules"]
        if (
            not isinstance(test_modules, list)
            or any(not isinstance(module, str) or not module for module in test_modules)
            or len(test_modules) != len(set(test_modules))
        ):
            errors.append(f"{context}.test_modules must be unique strings")
            test_modules = []
        for module in test_modules:
            module_path = PurePosixPath(module)
            if (
                module_path.is_absolute()
                or not module_path.parts
                or module_path.parts[0] != "tests"
                or ".." in module_path.parts
                or module_path.suffix != ".py"
                or not module_path.name.startswith("test")
            ):
                errors.append(
                    f"{context}.test_modules must contain safe tests/ test module paths"
                )
            elif not (root / module_path).is_file():
                errors.append(
                    f"{context}.test module does not exist: {module_path.as_posix()}"
                )
        if not mapped_producers and not test_modules:
            errors.append(f"{context} must select a producer or test module")

    producer_rows = {
        producer.get("id"): producer
        for producer in acceptance.get("producers", [])
        if isinstance(producer, dict) and isinstance(producer.get("id"), str)
    } if isinstance(acceptance, dict) else {}
    for producer_id in eligible:
        producer = producer_rows.get(producer_id)
        if not isinstance(producer, dict):
            continue
        ineligible_dependencies = sorted(
            set(producer.get("depends_on", [])) - set(eligible)
        )
        if ineligible_dependencies:
            errors.append(
                f"affected producer {producer_id!r} depends on stage-ineligible "
                f"producers {ineligible_dependencies}"
            )
    errors.extend(unit_test_dependency_errors(root, test_selection))
    return errors


def parse_affected_professionalism_context(
    raw: str | None,
    *,
    known_package_ids: Iterable[str] | None = None,
) -> dict[str, Any] | None:
    """Parse the one closed affected context shared by isolated producers."""

    if raw is None:
        return None
    try:
        context = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValidationProblem("affected context is not valid JSON") from exc
    expected_top = {
        "schema_version",
        "mode",
        "base_sha",
        "head_sha",
        "professionalism",
    }
    if not isinstance(context, dict) or set(context) != expected_top:
        raise ValidationProblem("affected context fields are not canonical")
    if context.get("schema_version") != 1 or context.get("mode") != "affected":
        raise ValidationProblem("affected context identity is invalid")
    for field in ("base_sha", "head_sha"):
        value = context.get(field)
        if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{40}", value) is None:
            raise ValidationProblem(f"affected context {field} is invalid")
    professionalism = context.get("professionalism")
    if not isinstance(professionalism, dict) or set(professionalism) != {
        "scope",
        "direct_package_ids",
        "reason_chains",
    }:
        raise ValidationProblem("affected professionalism fields are not canonical")
    scope = professionalism.get("scope")
    direct = professionalism.get("direct_package_ids")
    reason_chains = professionalism.get("reason_chains")
    if scope not in {"none", "packages", "full"}:
        raise ValidationProblem("affected professionalism scope is invalid")
    if (
        not isinstance(direct, list)
        or any(not isinstance(item, str) or not item for item in direct)
        or direct != sorted(set(direct))
    ):
        raise ValidationProblem("affected direct package IDs are not canonical")
    if scope == "packages" and not direct:
        raise ValidationProblem("package affected scope requires direct packages")
    if scope in {"none", "full"} and direct:
        raise ValidationProblem(f"{scope} affected scope cannot name direct packages")
    if (
        not isinstance(reason_chains, list)
        or any(
            not isinstance(chain, list)
            or not chain
            or any(not isinstance(item, str) or not item for item in chain)
            for chain in reason_chains
        )
    ):
        raise ValidationProblem("affected professionalism reason chains are invalid")
    if known_package_ids is not None:
        known = set(known_package_ids)
        unknown = sorted(set(direct) - known)
        if unknown:
            raise ValidationProblem(
                f"affected context names unknown packages: {unknown}"
            )
    return context


DECISION_EVAL_AXES = [
    "path-decision",
    "gap-ownership",
    "discovery-decision",
    "professional-layer3-decision",
    "action-authority",
    "review-decision",
]
DECISION_EVAL_BINDINGS = [
    (
        "source-fact-to-ask-user",
        "action-authority",
        "source-fact-resolves-without-user-question",
        "decision-source-fact-not-user-question",
    ),
    (
        "user-choice-to-source-inference",
        "gap-ownership",
        "user-choice-requires-user-answer",
        "decision-user-choice-not-source-inference",
    ),
    (
        "route-material-unknown-to-direct",
        "path-decision",
        "route-material-unknown-fails-closed",
        "decision-material-unknown-not-direct",
    ),
    (
        "direct-discovery-escape-then-edit",
        "discovery-decision",
        "invalidated-discovery-stops-before-edit",
        "decision-discovery-invalidated-stop-before-edit",
    ),
    (
        "token-overflow-drops-layer3",
        "professional-layer3-decision",
        "context-pressure-preserves-required-layer3",
        "decision-context-preserve-required-layer3",
    ),
    (
        "review-copies-implementation-layer3",
        "review-decision",
        "review-layer3-selected-from-review-risk",
        "decision-review-layer3-independent",
    ),
]


def decision_eval_contract_errors(
    data: object,
    root: Path = ROOT,
) -> list[str]:
    """Validate the source-owned seven-axis Decision Eval projection."""

    errors: list[str] = []
    if not isinstance(data, dict):
        return ["decision_eval_contract source must be an object"]
    contract = data.get("decision_eval_contract")
    fields = {
        "schema_version",
        "fixture_path",
        "decision_axes",
        "invariant_bindings",
        "compatibility_baseline",
        "route_once",
        "layer3_cardinality",
        "runtime_dependency",
    }
    if not isinstance(contract, dict) or set(contract) != fields:
        return [
            "decision_eval_contract fields must be exactly "
            f"{sorted(fields)}"
        ]
    if contract["schema_version"] != 1:
        errors.append("decision_eval_contract.schema_version must be 1")
    fixture_path = contract["fixture_path"]
    fixture = PurePosixPath(fixture_path) if isinstance(fixture_path, str) else None
    if (
        fixture is None
        or fixture.is_absolute()
        or ".." in fixture.parts
        or fixture.as_posix() != "evals/routing/decision-cases.yaml"
    ):
        errors.append(
            "decision_eval_contract.fixture_path must be "
            "evals/routing/decision-cases.yaml"
        )
    elif not (root / fixture).is_file():
        errors.append(
            "decision_eval_contract.fixture_path does not exist: "
            f"{fixture.as_posix()}"
        )
    if contract["decision_axes"] != DECISION_EVAL_AXES:
        errors.append(
            "decision_eval_contract.decision_axes must remain the declared behavioral axes"
        )
    bindings = contract["invariant_bindings"]
    binding_fields = {"mutant_id", "axis", "invariant_id", "failure_id"}
    actual_bindings: list[tuple[object, object, object, object]] = []
    if not isinstance(bindings, list):
        errors.append("decision_eval_contract.invariant_bindings must be a list")
    else:
        for index, binding in enumerate(bindings):
            context = f"decision_eval_contract.invariant_bindings[{index}]"
            if not isinstance(binding, dict) or set(binding) != binding_fields:
                errors.append(
                    f"{context} fields must be exactly {sorted(binding_fields)}"
                )
                continue
            values = tuple(binding[field] for field in (
                "mutant_id",
                "axis",
                "invariant_id",
                "failure_id",
            ))
            if any(
                not isinstance(value, str)
                or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value) is None
                for value in values
            ):
                errors.append(f"{context} values must be kebab-case ids")
            actual_bindings.append(values)
        if actual_bindings != DECISION_EVAL_BINDINGS:
            errors.append(
                "decision_eval_contract.invariant_bindings must remain the exact "
                "nine controlled mutants and stable invariant/failure ids"
            )
        if len({item[0] for item in actual_bindings}) != len(actual_bindings):
            errors.append("Decision Eval mutant ids must be unique")
        if len({item[3] for item in actual_bindings}) != len(actual_bindings):
            errors.append("Decision Eval failure ids must be unique")
    if contract["compatibility_baseline"] != {
        "routing_cases": 233,
        "capability_cases": 62,
    }:
        errors.append(
            "decision_eval_contract.compatibility_baseline must freeze 233+62 routes"
        )
    if contract["route_once"] != "required":
        errors.append("decision_eval_contract.route_once must be required")
    if contract["layer3_cardinality"] != {
        "minimum": 0,
        "maximum": 3,
        "duplicates": "fail",
        "overflow": "fail-never-truncate",
    }:
        errors.append(
            "decision_eval_contract.layer3_cardinality must require unique 0..3 "
            "and fail without truncation"
        )
    if contract["runtime_dependency"] is not False:
        errors.append("Decision Eval must remain test/eval-only")
    return errors


def decision_eval_authority(data: object) -> dict[str, Any]:
    """Return a detached validated projection of Decision Eval authority."""

    errors = decision_eval_contract_errors(data)
    if errors:
        raise ValueError("invalid Decision Eval authority: " + "; ".join(errors))
    assert isinstance(data, dict)
    return copy.deepcopy(data["decision_eval_contract"])


def behavior_eval_contract_errors(
    data: object,
    root: Path = ROOT,
) -> list[str]:
    """Validate the Core-owned dev/eval-only behavior comparison contract."""

    errors: list[str] = []
    if not isinstance(data, dict):
        return ["behavior_eval_contract source must be an object"]
    contract = data.get("behavior_eval_contract")
    fields = {
        "schema_version",
        "comparison_manifest_path",
        "modes",
        "artifact_roles",
        "controlled_bindings",
        "evidence_classes",
        "live_evidence_statuses",
        "routing_metrics",
        "review_metrics",
        "cost_metrics",
        "quality_metrics",
        "metric_directions",
        "review_input_ready_fields",
        "reviewer_forbidden_actions",
        "finding_relations",
        "finding_dispositions",
        "finding_oracle_fields",
        "finding_observation_fields",
        "review_dispatch_gate_fields",
        "main_dispatch_surface_contract",
        "scalar_authority_contract",
        "observation_contract",
        "live_capture_contract",
        "agent_visible_contract",
        "claim_boundaries",
        "verdicts",
        "verdict_policy",
        "physical_artifact_isolation",
        "runtime_dependency",
    }
    if not isinstance(contract, dict) or set(contract) != fields:
        return [
            "behavior_eval_contract fields must be exactly " f"{sorted(fields)}"
        ]
    if contract["schema_version"] != 2:
        errors.append("behavior_eval_contract.schema_version must be 2")
    manifest_value = contract["comparison_manifest_path"]
    manifest = PurePosixPath(manifest_value) if isinstance(manifest_value, str) else None
    if (
        manifest is None
        or manifest.is_absolute()
        or ".." in manifest.parts
        or manifest.suffix not in {".yaml", ".yml"}
        or not manifest.parts[:2] == ("evals", "agent-behavior")
    ):
        errors.append(
            "behavior_eval_contract.comparison_manifest_path must be a contained "
            "agent-behavior YAML path"
        )
    elif not (root / manifest).is_file():
        errors.append(
            "behavior_eval_contract.comparison_manifest_path does not exist: "
            f"{manifest.as_posix()}"
        )

    def closed_ids(field: str) -> list[str]:
        value = contract[field]
        if (
            not isinstance(value, list)
            or not value
            or any(
                not isinstance(item, str)
                or re.fullmatch(r"[a-z][a-z0-9]*(?:[_-][a-z0-9]+)*", item) is None
                for item in value
            )
            or len(value) != len(set(value))
        ):
            errors.append(
                f"behavior_eval_contract.{field} must be a non-empty unique id list"
            )
            return []
        return value

    modes = closed_ids("modes")
    artifact_roles = closed_ids("artifact_roles")
    controlled_bindings = closed_ids("controlled_bindings")
    evidence_classes = closed_ids("evidence_classes")
    live_statuses = closed_ids("live_evidence_statuses")
    routing_metrics = closed_ids("routing_metrics")
    review_metrics = closed_ids("review_metrics")
    cost_metrics = closed_ids("cost_metrics")
    quality_metrics = closed_ids("quality_metrics")
    ready_fields = closed_ids("review_input_ready_fields")
    forbidden_actions = closed_ids("reviewer_forbidden_actions")
    finding_relations = closed_ids("finding_relations")
    verdicts = closed_ids("verdicts")
    expected_lists = {
        "modes": ["captured_handoff", "blind_old_new_comparison"],
        "artifact_roles": [
            "agent_packet", "oracle", "observations", "verifier_capture", "reveal"
        ],
        "controlled_bindings": [
            "task_id", "host_id", "model_id", "agent_profile",
            "repository_state_sha", "evidence_boundary_id", "evaluator_id",
            "expected_behavior_definition_digest",
        ],
        "evidence_classes": ["live_agent", "structural_only"],
        "live_evidence_statuses": ["collected", "not_collected"],
        "routing_metrics": [
            "path_accuracy", "start_profile_accuracy",
            "primary_professional_skill_accuracy", "layer3_precision",
            "layer3_recall", "layer3_f1", "domain_extension_fpr",
            "domain_extension_fnr", "unnecessary_layer3_load_rate",
            "safe_fallback_accuracy", "paraphrase_stability",
            "boundary_transition_accuracy",
        ],
        "review_metrics": [
            "primary_review_skill_accuracy", "review_layer3_precision",
            "review_layer3_recall", "review_layer3_f1",
            "required_specialist_review_recall", "required_specialist_review_fnr",
            "specialist_review_set_accuracy", "unnecessary_specialist_review_rate",
            "review_boundary_correctness",
        ],
        "cost_metrics": ["tokens", "turns", "elapsed_ms"],
        "review_input_ready_fields": [
            "latest_changed_scope", "latest_diff_or_reference",
            "post_latest_edit_validation", "fixed_review_boundary", "required_evidence",
        ],
        "reviewer_forbidden_actions": [
            "edited", "repaired", "rerouted", "write_scope_expanded",
            "used_implementer_conclusion", "requested_diff_export",
        ],
        "finding_relations": ["current-task", "scope-blocker", "adjacent"],
        "finding_oracle_fields": [
            "finding_identity", "relation", "material", "repair_eligible",
            "disposition", "fresh", "affected_scope",
        ],
        "finding_observation_fields": [
            "finding_identity", "relation", "material", "repair_eligible",
            "entered_repair", "disposition", "fresh", "affected_scope",
        ],
        "review_dispatch_gate_fields": [
            "latest_changed_scope", "latest_diff_or_reference",
            "post_latest_edit_validation", "fixed_review_boundary", "required_evidence", "review_boundary_due",
        ],
        "verdicts": [
            "improved", "hardening_only", "no_effect", "regression",
            "not_enough_evidence",
        ],
    }
    actual_lists = {
        "modes": modes,
        "artifact_roles": artifact_roles,
        "controlled_bindings": controlled_bindings,
        "evidence_classes": evidence_classes,
        "live_evidence_statuses": live_statuses,
        "routing_metrics": routing_metrics,
        "review_metrics": review_metrics,
        "cost_metrics": cost_metrics,
        "review_input_ready_fields": ready_fields,
        "reviewer_forbidden_actions": forbidden_actions,
        "finding_relations": finding_relations,
        "finding_oracle_fields": closed_ids("finding_oracle_fields"),
        "finding_observation_fields": closed_ids("finding_observation_fields"),
        "review_dispatch_gate_fields": closed_ids("review_dispatch_gate_fields"),
        "verdicts": verdicts,
    }
    for field, expected in expected_lists.items():
        if actual_lists[field] != expected:
            errors.append(
                f"behavior_eval_contract.{field} must preserve the exact invariant-required closed set"
            )
    if quality_metrics != routing_metrics + review_metrics:
        errors.append(
            "behavior_eval_contract.quality_metrics must derive from routing_metrics "
            "followed by review_metrics"
        )
    directions = contract["metric_directions"]
    all_metrics = routing_metrics + review_metrics + cost_metrics
    if (
        not isinstance(directions, dict)
        or set(directions) != set(all_metrics)
        or any(
            value not in {"higher_is_better", "lower_is_better"}
            for value in directions.values()
        )
    ):
        errors.append(
            "behavior_eval_contract.metric_directions must cover every Core metric once"
        )
    lower_is_better = {
        "domain_extension_fpr", "domain_extension_fnr",
        "unnecessary_layer3_load_rate", "required_specialist_review_fnr",
        "unnecessary_specialist_review_rate", "tokens", "turns", "elapsed_ms",
    }
    expected_directions = {
        metric: (
            "lower_is_better" if metric in lower_is_better else "higher_is_better"
        )
        for metric in all_metrics
    }
    if directions != expected_directions:
        errors.append(
            "behavior_eval_contract.metric_directions must preserve exact metric semantics"
        )
    if contract["finding_dispositions"] != {
        "current-task": "repair-if-material",
        "scope-blocker": "main-delta-analysis",
        "adjacent": "record-only",
    }:
        errors.append(
            "behavior_eval_contract.finding_dispositions must preserve relation routing"
        )
    if contract["observation_contract"] != {
        "routing_fields": [
            "path", "start_profile", "primary_professional_skill",
            "layer3_skills", "domain_extensions", "safe_fallback",
        ],
        "no_dispatch_review_fields": [
            "dispatch_count", "primary_review_skill", "layer3_skills",
            "specialist_reviews", "boundary_decision", "review_boundary_due",
        ],
        "gated_no_dispatch_review_fields": [
            "dispatch_count", "primary_review_skill", "layer3_skills",
            "specialist_reviews", "boundary_decision", "main_dispatch_gate",
            "main_dispatch_surface", "review_boundary_due",
        ],
        "dispatch_review_fields": [
            "dispatch_count", "primary_review_skill", "layer3_skills",
            "specialist_reviews", "boundary_decision", "review_input_ready",
            "reviewer_actions", "initial_review", "repair_re_review", "findings", "review_boundary_due",
        ],
        "initial_review_fields": [
            "completed_fixed_boundary", "stopped_after_ordinary_finding",
            "covered_review_dimensions", "returned_findings",
        ],
        "repair_rereview_fields": [
            "validation_after_latest_edit", "uses_latest_repair_diff",
            "uses_initial_review_diff", "focused_scope_only", "frozen_scope",
            "covering_focused_re_review", "duplicate_final_review_dispatched",
        ],
        "list_semantics": "typed-unique-ordered",
        "boolean_semantics": "real-boolean-only",
        "dispatch_count_semantics": "integer-non-bool-zero-or-one",
        "extra_or_missing_fields": "fail",
    }:
        errors.append("behavior_eval_contract.observation_contract is malformed")
    if contract["main_dispatch_surface_contract"] != {
        "decision_actor_profile": "main-control-agent",
        "review_candidate_profile": "review-agent",
        "decision": "review-input-ready",
        "evaluated_before_review_execution": True,
        "reviewer_executed": False,
        "dispatch_count": 0,
    }:
        errors.append(
            "behavior_eval_contract.main_dispatch_surface_contract is malformed"
        )
    if contract["scalar_authority_contract"] != {
        "path_values_source": "route_decision_contract.path_values",
        "path_profile_mapping_source": "route_decision_contract.path_start_profiles",
        "profile_source": "profile_contract.source_path",
        "professional_registry_path": "src/registry/professional-skills.yaml",
        "professional_role_field": "role_support",
        "review_boundary_by_dispatch": {
            "0": ["not-required", "input-not-ready"],
            "1": ["initial-review", "focused-re-review"],
        },
        "zero_dispatch_review_skill": None,
    }:
        errors.append("behavior_eval_contract.scalar_authority_contract is malformed")
    if contract["live_capture_contract"] != {
        "artifact_role": "verifier_capture",
        "capture_fields": [
            "capture_bytes", "artifact_sha256", "capture_sequence",
            "treatment_source", "controlled_bindings", "provenance",
        ],
        "provenance_fields": [
            "verifier_id", "source_execution_id", "treatment_source", "host_id",
            "model_id", "agent_profile", "repository_state_sha",
            "capture_sequence", "reveal_sequence", "observed_before_reveal",
        ],
        "treatment_sources": ["baseline", "candidate"],
        "digest": "sha256-utf8-capture-bytes",
        "copied_arm_capture": "not-enough-evidence",
        "missing_or_invalid": "not-enough-evidence",
        "caller_supplied_authority": "integrity-only",
        "host_execution_authority": "unavailable",
        "effective_live_evidence_status": "not_collected",
    }:
        errors.append("behavior_eval_contract.live_capture_contract is malformed")
    if contract["agent_visible_contract"] != {
        "payload_fields": ["task_id", "prompt", "evidence_refs"],
        "packet_fields": [
            "id", "agent_input", "controlled_bindings", "blind_arm_ids"
        ],
        "evaluator_only_fields": ["scenario_id", "relationship"],
        "opaque_binding_fields": [
            "task_id", "host_id", "model_id", "evidence_boundary_id",
            "evaluator_id",
        ],
        "opaque_id_pattern": "opaque-[0-9]{3}",
        "expected_definition_binding": "digest-only",
        "semantic_answer_leakage": "fail",
    }:
        errors.append("behavior_eval_contract.agent_visible_contract is malformed")
    if contract["claim_boundaries"] != {
        "structural_only": "harness-validity-only",
        "caller_supplied_capture": "not-enough-evidence",
    }:
        errors.append("behavior_eval_contract.claim_boundaries is malformed")
    policy = contract["verdict_policy"]
    if policy != {
        "quality_regression": "regression",
        "old-fail-new-complete-succeed": "improved",
        "old-correct-new-correct": ["no_effect", "hardening_only"],
        "incomplete-non-regressing": "no_effect",
        "missing-live-agent-data": "not_enough_evidence",
        "structural-fixture-claim": "harness-validity-only",
        "case-regression-dominates": True,
    }:
        errors.append("behavior_eval_contract.verdict_policy is malformed")
    if contract["physical_artifact_isolation"] is not True:
        errors.append("behavior comparison artifacts must remain physically isolated")
    if contract["runtime_dependency"] is not False:
        errors.append("Behavior Eval must remain dev/eval-only")
    return errors


def behavior_eval_authority(data: object) -> dict[str, Any]:
    """Return a detached validated projection of Behavior Eval authority."""

    errors = behavior_eval_contract_errors(data)
    if errors:
        raise ValueError("invalid Behavior Eval authority: " + "; ".join(errors))
    assert isinstance(data, dict)
    return copy.deepcopy(data["behavior_eval_contract"])


RUNTIME_ASSET_INLINE_IDENTITY_CONTRACT = "changeforge.runtime-inline-identity/v2"
RUNTIME_ASSET_INLINE_IDENTITY_VERSION = 2
RUNTIME_ASSET_INTEGRITY_MANIFEST_CONTRACT = (
    "changeforge.runtime-integrity-manifest/v1"
)
RUNTIME_ASSET_INTEGRITY_MANIFEST_PATH = (
    "references/runtime/integrity-manifest.json"
)
RUNTIME_ASSET_METADATA_EXCLUSIONS = (
    RUNTIME_ASSET_INTEGRITY_MANIFEST_PATH,
)
RUNTIME_ASSET_INTEGRITY_MANIFEST_FIELDS = {
    "contract",
    "schema_version",
    "runtime_version",
    "build_identity",
    "professional_skill",
    "assets",
    "integrity_manifest_sha256",
}
RUNTIME_ASSET_INTEGRITY_ROW_FIELDS = {"path", "kind", "sha256", "size"}
RUNTIME_REFERENCE_RECORD_FIELDS = {
    "owner_skill",
    "owner_layer",
    "path",
    "type",
    "load_when",
    "do_not_load_when",
    "required_by",
    "required_output",
    "context_admissibility",
    "residency",
}
RUNTIME_REFERENCE_PARTITION_FIELDS = {
    "contract",
    "authority_contract",
    "professional_skill",
    "owner_skill",
    "records_sha256",
    "reference_records",
    "build",
}
RUNTIME_ASSET_ROOT_BINDING_FIELDS = {
    "professional_skill",
    "runtime_version",
    "authoritative_build_inputs_sha256",
    "build_identity_algorithm",
    "build_identity",
    "inline_identity_contract",
    "inline_identity_version",
    "integrity_manifest_path",
    "integrity_manifest_full_bytes_sha256",
}
RUNTIME_ASSET_FIXED_PATHS = {
    "selector_envelope_path": "references/runtime/selector.json",
    "selector_complete_path": "references/runtime/selectors/complete.json",
    "selector_shard_path_template": (
        "references/runtime/selectors/<decision-id>.json"
    ),
    "reference_partition_path_template": (
        "references/runtime/reference-records/<owner-skill>.json"
    ),
    "layer3_path_template": "references/layer3/<layer3-skill>.md",
    "professional_reference_record_path_template": "references/<file>.md",
    "layer3_reference_record_path_template": (
        "references/layer3/<owner-skill>/references/<file>.md"
    ),
    "integrity_manifest_path": RUNTIME_ASSET_INTEGRITY_MANIFEST_PATH,
}
RUNTIME_ASSET_BUILD_IDENTITY_ALGORITHM = "sha256-prefix-128-base64url-nopad"
RUNTIME_ASSET_PROFESSIONAL_JIT_TEMPLATE = (
    "JIT: `references/runtime/selector.json`; Runtime: `<V>/<B>`."
)
RUNTIME_ASSET_LAYER3_MARKER_TEMPLATE = (
    "<!-- Build: <B> -->"
)


def runtime_asset_build_identity(full_digest: object) -> str:
    """Derive the canonical 128-bit Runtime comparator from one full SHA-256."""

    if (
        not isinstance(full_digest, str)
        or re.fullmatch(r"[0-9a-f]{64}", full_digest) is None
    ):
        raise ValueError("Runtime build input digest must be 64 lowercase hex")
    return base64.urlsafe_b64encode(bytes.fromhex(full_digest)[:16]).decode(
        "ascii"
    ).rstrip("=")


def runtime_asset_build_identity_bytes(build_identity: object) -> bytes:
    """Decode one canonical base64url-no-padding 128-bit Runtime comparator."""

    if (
        not isinstance(build_identity, str)
        or re.fullmatch(r"[A-Za-z0-9_-]{22}", build_identity) is None
        or build_identity[-1] not in "AQgw"
    ):
        raise ValueError(
            "Runtime build identity must be canonical base64url-nopad-22"
        )
    try:
        decoded = base64.b64decode(
            build_identity + "==",
            altchars=b"-_",
            validate=True,
        )
    except (binascii.Error, ValueError) as exc:
        raise ValueError(
            "Runtime build identity must be canonical base64url-nopad-22"
        ) from exc
    if (
        len(decoded) != 16
        or base64.urlsafe_b64encode(decoded).decode("ascii").rstrip("=")
        != build_identity
    ):
        raise ValueError(
            "Runtime build identity must be canonical base64url-nopad-22"
        )
    return decoded


def validate_core_contracts(
    data: object,
    root: Path = ROOT,
) -> list[str]:
    """Validate the complete authoritative control-model shape and invariants."""

    errors: list[str] = []
    declared_freshness_targets: dict[str, set[str]] = {}
    declared_forbidden_storage_targets: dict[str, set[str]] = {}
    freshness_rule_targets: dict[str, set[str]] = {}
    forbidden_storage_rule_targets: dict[str, set[str]] = {}

    def bind_projection_ids(
        bindings: dict[str, set[str]],
        rule_ids: list[str],
        target: str,
    ) -> None:
        for rule_id in rule_ids:
            bindings.setdefault(rule_id, set()).add(target)

    def exact_keys(value: object, expected: set[str], context: str) -> bool:
        if not isinstance(value, dict):
            errors.append(f"{context} must be an object")
            return False
        actual = set(value)
        if actual != expected:
            errors.append(
                f"{context} fields must be exactly {sorted(expected)}, found "
                f"{sorted(actual)}"
            )
            return False
        return True

    def string_list(
        value: object,
        context: str,
        *,
        nonempty: bool = True,
        unique: bool = True,
    ) -> list[str]:
        if not isinstance(value, list) or any(
            not isinstance(item, str) or not item.strip() for item in value
        ):
            errors.append(f"{context} must be a list of non-empty strings")
            return []
        if nonempty and not value:
            errors.append(f"{context} must not be empty")
        if unique and len(value) != len(set(value)):
            errors.append(f"{context} must not contain duplicates")
        return value

    def projection_rule_map(
        value: object,
        context: str,
        *,
        extra_field: str | None = None,
    ) -> dict[str, list[str]]:
        """Validate structured, addressable projection rules."""

        if not isinstance(value, list) or not value:
            errors.append(f"{context} must be a non-empty rule list")
            return {}
        result: dict[str, list[str]] = {}
        for index, rule in enumerate(value):
            rule_context = f"{context}[{index}]"
            expected_fields = {"id", "projection_terms"}
            if extra_field is not None:
                expected_fields.add(extra_field)
            if not isinstance(rule, dict) or set(rule) != expected_fields:
                errors.append(
                    f"{rule_context} fields must be exactly {sorted(expected_fields)}"
                )
                continue
            identifier = rule["id"]
            if not isinstance(identifier, str) or re.fullmatch(
                r"[a-z0-9]+(?:-[a-z0-9]+)*", identifier
            ) is None:
                errors.append(f"{rule_context}.id must be kebab-case")
                continue
            if identifier in result:
                errors.append(f"{context} ids must be unique")
            result[identifier] = string_list(
                rule["projection_terms"], f"{rule_context}.projection_terms"
            )
            if extra_field == "projection_targets":
                string_list(
                    rule["projection_targets"], f"{rule_context}.projection_targets"
                )
        return result

    def instruction_rule_groups(
        value: object,
        context: str,
        *,
        allow_exact_rule: bool = False,
    ) -> dict[str, list[str]]:
        """Validate profile rule groups that must each project to one bullet."""

        if not isinstance(value, list) or not value:
            errors.append(f"{context} must be a non-empty instruction-rule list")
            return {}
        result: dict[str, list[str]] = {}
        for index, rule in enumerate(value):
            rule_context = f"{context}[{index}]"
            required_fields = {"rule_id", "required_terms"}
            allowed_fields = required_fields | (
                {"exact_rule"} if allow_exact_rule else set()
            )
            if not isinstance(rule, dict):
                errors.append(f"{rule_context} must be an object")
                continue
            missing = sorted(required_fields - set(rule))
            extra = sorted(set(rule) - allowed_fields)
            if missing or extra:
                errors.append(
                    f"{rule_context} fields must contain {sorted(required_fields)}"
                    f" with optional exact_rule={allow_exact_rule}; "
                    f"missing={missing}, extra={extra}"
                )
                continue
            identifier = rule["rule_id"]
            if not isinstance(identifier, str) or re.fullmatch(
                r"[a-z0-9]+(?:-[a-z0-9]+)*", identifier
            ) is None:
                errors.append(f"{rule_context}.rule_id must be kebab-case")
                continue
            if identifier in result:
                errors.append(f"{context} rule ids must be unique")
            terms = string_list(
                rule["required_terms"], f"{rule_context}.required_terms"
            )
            result[identifier] = terms
            if "exact_rule" not in rule:
                continue
            exact_rule = rule["exact_rule"]
            if (
                not isinstance(exact_rule, str)
                or not exact_rule.startswith("- ")
                or not exact_rule[2:].strip()
                or "\n" in exact_rule
                or "\r" in exact_rule
            ):
                errors.append(
                    f"{rule_context}.exact_rule must be one non-empty canonical bullet"
                )
                continue
            folded_rule = exact_rule.casefold()
            missing_terms = [term for term in terms if term.casefold() not in folded_rule]
            if missing_terms:
                errors.append(
                    f"{rule_context}.exact_rule must contain every required term: "
                    f"missing={missing_terms}"
                )
        return result

    top_fields = {
        "schema_version",
        "kind",
        "core_principles",
        "principle_acceptance_contract",
        "impact_graph_contract",
        "roles",
        "runtime_asset_resolution_contract",
        "environment_risk_calibration_contract",
        "external_read_contract",
        "context_budget_contract",
        "final_goal_contract",
        "reference_contract",
        "decision_eval_contract",
        "behavior_eval_contract",
        "route_decision_contract",
        "layer3_selector_contract",
        "prompt_contract",
        "profile_contract",
        "control_skill_contract",
        "docs_contract",
    }
    if not exact_keys(data, top_fields, "authoritative control model"):
        return errors
    assert isinstance(data, dict)
    if data["schema_version"] != 1 or data["kind"] != "changeforge.core_contracts":
        errors.append(
            "authoritative control model must use changeforge.core_contracts schema 1"
        )

    errors.extend(validate_principle_acceptance_contract(data, root))
    errors.extend(validate_impact_graph_contract(data, root))
    errors.extend(decision_eval_contract_errors(data, root))
    errors.extend(behavior_eval_contract_errors(data, root))

    role_names = {
        "main-control-agent",
        "analysis-agent",
        "task-agent",
        "review-agent",
    }
    roles = data["roles"]
    if not isinstance(roles, dict) or set(roles) != role_names:
        errors.append(f"roles must be exactly {sorted(role_names)}")
        roles = {}
    role_fields = {"sandbox", "tools", "may_dispatch", "may_edit", "may_review"}
    capability_owners = {
        "may_dispatch": "main-control-agent",
        "may_edit": "task-agent",
        "may_review": "review-agent",
    }
    allowed_tools = {
        "dispatch",
        "read",
        "search",
        "edit",
        "execute",
        "execute-read-only",
        "external-source-read",
    }
    for role_name in sorted(role_names):
        role = roles.get(role_name)
        if not exact_keys(role, role_fields, f"roles.{role_name}"):
            continue
        assert isinstance(role, dict)
        tools = string_list(role["tools"], f"roles.{role_name}.tools")
        unknown_tools = sorted(set(tools) - allowed_tools)
        if unknown_tools:
            errors.append(f"roles.{role_name}.tools contains unknown tools {unknown_tools}")
        sandbox = role["sandbox"]
        if sandbox not in {"dispatch-only", "read-only", "workspace-write"}:
            errors.append(f"roles.{role_name}.sandbox is invalid")
        for capability, owner in capability_owners.items():
            value = role[capability]
            if not isinstance(value, bool):
                errors.append(f"roles.{role_name}.{capability} must be boolean")
            elif value != (role_name == owner):
                errors.append(f"{capability} must belong only to {owner}")
        if bool(role["may_dispatch"]) != ("dispatch" in tools):
            errors.append(f"roles.{role_name}: dispatch tool and may_dispatch disagree")
        if bool(role["may_edit"]) != ({"edit", "execute"} <= set(tools)):
            errors.append(f"roles.{role_name}: write tools and may_edit disagree")
        if bool(role["may_review"]) != ("execute-read-only" in tools):
            errors.append(f"roles.{role_name}: review tool and may_review disagree")
        if ("external-source-read" in tools) != (role_name == "analysis-agent"):
            errors.append(
                "external-source-read must belong only to analysis-agent and be absent "
                "from main-control-agent, task-agent, and review-agent"
            )
        expected_sandbox = (
            "dispatch-only"
            if role["may_dispatch"]
            else "workspace-write"
            if role["may_edit"]
            else "read-only"
        )
        if sandbox != expected_sandbox:
            errors.append(f"roles.{role_name}: sandbox and capability flags disagree")

    runtime_assets = data["runtime_asset_resolution_contract"]
    runtime_asset_fields = {
        "schema_version",
        "selected_root",
        "professional_root",
        "path_policy",
        "reference_record_path",
        "inline_identity",
        "integrity_manifest",
        "fixed_paths",
        "fixed_locator_projection",
        "acyclic_generation_order",
        "root_manifest_binding",
        "runtime_roles",
        "runtime_inline_verification",
        "non_runtime_verifier",
        "exact_set_bypass",
        "mixed_install",
        "failure",
    }
    if exact_keys(
        runtime_assets,
        runtime_asset_fields,
        "runtime_asset_resolution_contract",
    ):
        assert isinstance(runtime_assets, dict)
        if runtime_assets["schema_version"] != 1:
            errors.append("runtime_asset_resolution_contract.schema_version must be 1")
        if (
            runtime_assets["selected_root"]
            != "host-resolved-current-professional-root"
            or runtime_assets["professional_root"] != "."
        ):
            errors.append("Runtime assets must bind one Host-selected Professional root")
        path_policy = runtime_assets["path_policy"]
        expected_path_policy = {
            "addressing": "professional-root-relative-fixed-paths-only",
            "forbidden": [
                "absolute",
                "parent-traversal",
                "symlink",
                "parent-search",
                "sibling-root",
                "glob",
                "rglob",
                "HOME-enumeration",
                "~/.copilot",
            ],
        }
        if path_policy != expected_path_policy:
            errors.append("Runtime asset path policy must forbid inferred lookup surfaces")

        reference_record_path = runtime_assets["reference_record_path"]
        expected_reference_record_path = {
            "authoring_authority": "registry-selector-source-relative",
            "projection_owner": "build-only",
            "runtime_path_fields": ["path"],
            "professional_path": "references/<file>.md",
            "layer3_path": (
                "references/layer3/<owner-skill>/references/<file>.md"
            ),
            "runtime_read": "read-path-verbatim",
            "resolution": (
                "professional-root-plus-record-path-after-bounded-relative-validation"
            ),
            "required_target": [
                "within-professional-root",
                "exists",
                "regular-file",
                "not-symlink",
            ],
            "forbidden": [
                "basename-inference",
                "owner-plus-relative-concatenation",
                "source-runtime-dual-path",
                "search-fallback",
                "glob-fallback",
                "HOME-fallback",
                "parent-fallback",
                "sibling-fallback",
            ],
        }
        if reference_record_path != expected_reference_record_path:
            errors.append(
                "Runtime Reference record paths must be Build-projected and read verbatim"
            )

        inline_identity = runtime_assets["inline_identity"]
        inline_identity_fields = {
            "contract",
            "runtime_version_source",
            "build_identity_derivation",
            "build_identity_bits",
            "build_identity_format",
            "professional_binding",
            "professional_entrypoint_jit_line",
            "selector_build_field",
            "selector_assets",
            "selector_read",
            "selection_receipt_build_field",
            "selection_receipt_hash_domain",
            "layer3_first_line",
            "layer3_marker_mode",
            "layer3_professional_binding",
        }
        if exact_keys(
            inline_identity,
            inline_identity_fields,
            "runtime asset inline identity",
        ):
            assert isinstance(inline_identity, dict)
            if (
                inline_identity["contract"]
                != RUNTIME_ASSET_INLINE_IDENTITY_CONTRACT
                or inline_identity["runtime_version_source"] != "root-source-version"
                or inline_identity["build_identity_derivation"]
                != "authoritative-build-inputs-sha256-prefix-128-base64url-nopad"
                or inline_identity["build_identity_bits"] != 128
                or inline_identity["build_identity_format"]
                != "base64url-nopad-22"
                or inline_identity["professional_binding"] != "frontmatter-name"
                or inline_identity["professional_entrypoint_jit_line"]
                != RUNTIME_ASSET_PROFESSIONAL_JIT_TEMPLATE
                or inline_identity["selector_build_field"] != "build"
                or inline_identity["selector_assets"]
                != [
                    "selector-envelope",
                    "direct-selector",
                    "complete-selector",
                    "decision-shard",
                    "reference-record-partition",
                ]
                or inline_identity["selector_read"]
                != "single-existing-load-no-reread"
                or inline_identity["selection_receipt_build_field"] != "build"
                or inline_identity["selection_receipt_hash_domain"]
                != "canonical-semantic-domain-includes-build"
                or inline_identity["layer3_first_line"]
                != RUNTIME_ASSET_LAYER3_MARKER_TEMPLATE
                or inline_identity["layer3_marker_mode"]
                != "replace-existing-generated-marker"
                or inline_identity["layer3_professional_binding"]
                != "host-root-plus-receipt-plus-fixed-path"
            ):
                errors.append("Runtime inline identity contract is invalid")

        manifest = runtime_assets["integrity_manifest"]
        manifest_fields = {
            "contract",
            "schema_version",
            "path",
            "fields",
            "asset_fields",
            "asset_order",
            "inventory",
            "excluded_metadata_paths",
            "semantic_hash_field",
            "semantic_hash_domain",
            "canonical_json",
            "runtime_read",
        }
        if exact_keys(manifest, manifest_fields, "runtime asset integrity manifest"):
            assert isinstance(manifest, dict)
            if (
                manifest["contract"] != RUNTIME_ASSET_INTEGRITY_MANIFEST_CONTRACT
                or manifest["schema_version"] != 1
                or manifest["path"] != RUNTIME_ASSET_INTEGRITY_MANIFEST_PATH
                or set(manifest["fields"])
                != RUNTIME_ASSET_INTEGRITY_MANIFEST_FIELDS
                or len(manifest["fields"])
                != len(RUNTIME_ASSET_INTEGRITY_MANIFEST_FIELDS)
                or set(manifest["asset_fields"])
                != RUNTIME_ASSET_INTEGRITY_ROW_FIELDS
                or len(manifest["asset_fields"])
                != len(RUNTIME_ASSET_INTEGRITY_ROW_FIELDS)
                or manifest["asset_order"] != "unique-lexicographic-path"
                or manifest["inventory"] != "every-non-metadata-delivery-asset"
                or manifest["excluded_metadata_paths"]
                != list(RUNTIME_ASSET_METADATA_EXCLUSIONS)
                or manifest["semantic_hash_field"]
                != "integrity_manifest_sha256"
                or manifest["semantic_hash_domain"]
                != "canonical-json-semantics-excluding-own-hash-no-trailing-newline"
                or manifest["runtime_read"] != "forbidden"
            ):
                errors.append("Runtime integrity manifest schema/hash/read contract is invalid")
        manifest_canonical_json = {
            "encoding": "utf-8",
            "ensure_ascii": False,
            "sort_keys": True,
            "separators": [",", ":"],
            "trailing_newline": False,
        }
        if (
            not isinstance(manifest, dict)
            or manifest.get("canonical_json") != manifest_canonical_json
        ):
            errors.append("Runtime integrity manifest semantic hash must use canonical JSON")
        if runtime_assets["fixed_paths"] != RUNTIME_ASSET_FIXED_PATHS:
            errors.append("Runtime asset fixed paths must match Professional-local grammar")
        locator = runtime_assets["fixed_locator_projection"]
        expected_locator = {
            "owner": "generated-professional-entrypoint-and-selector-envelope",
            "professional_entrypoint_line": RUNTIME_ASSET_PROFESSIONAL_JIT_TEMPLATE,
            "selector_owns": [
                "complete-selector",
                "decision-shard",
                "reference-partition",
            ],
            "layer3_path_grammar": "references/layer3/<layer3-skill>.md",
            "forbidden": [
                "runtime-identity-sidecar",
                "cross-skill-selector-locator",
                "duplicate-layer3-locator",
                "duplicate-profile-main-brief-locator",
                "search-discovery",
            ],
        }
        if locator != expected_locator:
            errors.append("Runtime fixed locator projection is invalid")
        expected_generation_order = [
            "authoritative-build-inputs-and-source-version",
            "full-sha256-and-runtime-version",
            "sha256-prefix-128-comparator",
            "professional-selector-receipt-layer3-inline-bindings",
            "integrity-inventory-and-semantic-hash",
            "root-manifest-integrity-exact-byte-binding",
        ]
        if runtime_assets["acyclic_generation_order"] != expected_generation_order:
            errors.append("Runtime metadata generation order must remain acyclic")
        root_binding = runtime_assets["root_manifest_binding"]
        if (
            not isinstance(root_binding, dict)
            or set(root_binding)
            != {
                "fields",
                "build_identity_algorithm",
                "inline_identity_contract",
                "inline_identity_version",
                "hash_domain",
                "completeness",
            }
            or set(root_binding.get("fields", []))
            != RUNTIME_ASSET_ROOT_BINDING_FIELDS
            or len(root_binding.get("fields", []))
            != len(RUNTIME_ASSET_ROOT_BINDING_FIELDS)
            or root_binding.get("build_identity_algorithm")
            != RUNTIME_ASSET_BUILD_IDENTITY_ALGORITHM
            or root_binding.get("inline_identity_contract")
            != RUNTIME_ASSET_INLINE_IDENTITY_CONTRACT
            or root_binding.get("inline_identity_version")
            != RUNTIME_ASSET_INLINE_IDENTITY_VERSION
            or root_binding.get("hash_domain") != "exact-serialized-file-bytes"
            or root_binding.get("completeness")
            != "integrity-assets-plus-one-metadata-full-byte-binding"
        ):
            errors.append("root build manifest must bind inline identity and integrity exactly")
        runtime_roles = runtime_assets["runtime_roles"]
        if (
            not isinstance(runtime_roles, dict)
            or set(runtime_roles)
            != {
                "profiles",
                "required_reads",
                "forbidden_reads",
                "digest_operations",
                "forbidden_operations",
            }
            or set(runtime_roles.get("profiles", [])) != role_names
            or runtime_roles.get("required_reads")
            != [
                "professional-entrypoint",
                "logical-selection-receipt",
                "current-fixed-assets",
            ]
            or runtime_roles.get("forbidden_reads")
            != ["integrity-manifest", "root-build-manifest"]
            or runtime_roles.get("digest_operations") != []
            or any(
                item not in runtime_roles.get("forbidden_operations", [])
                for item in (
                    "runtime-identity-sidecar-read",
                    "selector-reload",
                    "sha256",
                    "size",
                    "HOME-enumeration",
                    "parent-search",
                    "glob",
                )
            )
        ):
            errors.append("Runtime roles must use compact inline verification only")
        inline = runtime_assets["runtime_inline_verification"]
        if (
            not isinstance(inline, dict)
            or inline.get("inputs")
            != [
                "professional-entrypoint",
                "logical-selection-receipt",
                "current-fixed-assets",
            ]
            or inline.get("checks")
            != [
                "professional-frontmatter-name",
                "professional-jit-runtime-version-build",
                "base64url-nopad-22-build-identity",
                "selector-or-partition-build-on-existing-read",
                "selection-receipt-build",
                "layer3-first-line-build",
                "profile",
                "selection-owner",
                "selection-kind",
                "selected-or-exact-layer3",
                "unique-max-three",
                "itemwise-profile-domain-authorization",
                "current-asset-professional-binding",
                "reference-record-path-verbatim",
            ]
            or inline.get("proof_limits")
            != [
                "full-digest-derivation",
                "raw-byte-integrity",
                "coherent-old-bundle-currentness",
            ]
        ):
            errors.append("Runtime inline verification boundary is invalid")
        verifier = runtime_assets["non_runtime_verifier"]
        if (
            not isinstance(verifier, dict)
            or verifier.get("owner")
            != "scripts/validation_utils.py#runtime_asset_bundle_metadata_errors"
            or verifier.get("consumers")
            != ["build", "installer", "doctor", "evaluator", "tests"]
            or verifier.get("inputs")
            != [
                "integrity-manifest-full-bytes",
                "complete-delivery-assets",
                "root-manifest-binding",
                "full-authoritative-input-sha256",
            ]
            or verifier.get("checks")
            != [
                "full-digest-format",
                "prefix-128-derivation",
                "professional-jit-version-build",
                "selector-partition-build",
                "selection-receipt-build",
                "layer3-first-line-build",
                "integrity-semantics",
                "complete-inventory",
                "asset-digest-size",
                "reference-record-path-shape-and-exact-target",
                "one-metadata-full-byte-binding",
            ]
        ):
            errors.append("Runtime byte integrity must have one non-Runtime verifier owner")
        if (
            runtime_assets["exact_set_bypass"]
            != "professional-entrypoint-and-logical-selection-receipt-and-layer3-"
            "binding-required-selector-skipped"
            or runtime_assets["mixed_install"]
            != "one-host-selected-professional-root-never-cross-root-compose"
        ):
            errors.append("Runtime exact-set and mixed-install bindings are invalid")
        if runtime_assets["failure"] != "fail-closed-no-utility-no-reroute":
            errors.append("Runtime asset failure must fail closed without Utility or reroute")


    external_read = data["external_read_contract"]
    expected_external_read = {
        "capability_field": "external-source-read",
        "capability_states": ["supported", "unsupported"],
        "exclusive_role": "analysis-agent",
        "operation": "external-source-read",
        "general_network_counts_as_supported": False,
        "jit_policy": {
            "local_or_current_evidence_sufficient": "do-not-read-externally",
            "material_unresolved_claim": "external-source-read",
            "non_material_unknown": "record-proof-limit",
            "broad_or_untargeted_research": "forbidden",
        },
        "source_priority": [
            "official-primary-source",
            "version-specific-documentation",
            "version-date-or-lifecycle-source",
        ],
        "forbidden_capabilities": [
            "workspace-mutation",
            "unbounded-network-operation",
            "external-write",
            "dependency-installation",
            "production-operation",
            "agent-dispatch",
            "implementation",
            "review",
        ],
        "trust_boundary": {
            "external_content": "evidence-input-only-never-control-input",
            "execute_returned_instructions": False,
            "normalization_path": ["external-source", "analysis-agent-judgment", "source-backed-claim"],
            "protected_control_fields": ["Role", "Skill", "Scope", "Acceptance", "Owner", "Authorization"],
            "raw_external_instruction_downstream": "forbidden",
        },
        "disclosure_guard": {
            "request_minimization": "minimum-public-information-required-for-claim",
            "forbidden_request_content": [
                "repository-private-source",
                "secret-token-credential",
                "user-sensitive-data",
                "internal-identifier",
                "proprietary-content",
            ],
        },
        "missing_evidence": {
            "critical": {
                "trigger": "critical-fact-missing-can-invalidate-current-slice",
                "action": "resolve-important-question-before-dependent-edit",
                "dispatch_implementation": False,
            },
            "non_critical": {
                "action": "record-proof-limit",
                "blocks_safe_slice": False,
            },
        },
        "unsupported_behavior": "continue-when-existing-evidence-is-sufficient",
        "unsupported_critical_behavior": (
            "fail-closed-when-critical-fact-unobtainable"
        ),
        "downstream_research_roles": {
            "task-agent": "forbidden",
            "review-agent": "forbidden",
        },
    }
    if external_read != expected_external_read:
        errors.append(
            "external_read_contract must equal the closed analysis-only JIT "
            "read and evidence policy"
        )


    context_budget = data["context_budget_contract"]
    context_budget_fields = {
        "schema_version",
        "tokenizer",
        "policy_status",
        "context_taxonomy",
        "budget_classes",
        "duplicate_rule_token_ratio_max",
        "runtime_asset_projection",
        "quality_cost_gate",
    }
    if exact_keys(
        context_budget,
        context_budget_fields,
        "context_budget_contract",
    ):
        assert isinstance(context_budget, dict)
        if context_budget["schema_version"] != 3:
            errors.append("context_budget_contract.schema_version must be 3")
        if context_budget["tokenizer"] != "o200k_base":
            errors.append("context_budget_contract.tokenizer must be o200k_base")
        if (
            context_budget["policy_status"]
            != "provisional-migration-values-not-calibrated-optima"
        ):
            errors.append(
                "context_budget_contract.policy_status must mark provisional migration values"
            )
        taxonomy = context_budget["context_taxonomy"]
        expected_taxonomy = {
            "authoring": {
                "label": "Authoring Budget",
                "classes": [
                    "main_prompt",
                    "control_skill",
                    "professional_skill",
                    "foundation",
                    "domain",
                ],
            },
            "resident_runtime": {
                "label": "Resident Runtime Budget",
                "classes": ["main"],
            },
            "dispatch_composition": {
                "label": "Dispatch Composition Budget",
                "classes": [
                    "task",
                    "analyzed_task",
                    "analysis",
                    "review",
                    "utility",
                ],
            },
            "runtime_dynamic_context": {
                "label": "Runtime Dynamic Context",
                "classes": [
                    "repository_reads",
                    "diff",
                    "command_output",
                    "tool_system_prompt",
                    "conversation_history",
                ],
                "observation_only": True,
                "host_compaction_out_of_scope": True,
            },
        }
        if taxonomy != expected_taxonomy:
            errors.append(
                "context_budget_contract.context_taxonomy must classify authoring, "
                "resident runtime, dispatch composition, and observation-only dynamic context"
            )
        budget_classes = context_budget["budget_classes"]
        expected_budget_classes = {
            "main",
            "task",
            "analyzed_task",
            "analysis",
            "review",
            "utility",
        }
        if not isinstance(budget_classes, dict) or set(budget_classes) != expected_budget_classes:
            errors.append(
                "context_budget_contract.budget_classes must define the six rendered contexts"
            )
        else:
            for budget_class, entry in budget_classes.items():
                entry_context = f"context_budget_contract.budget_classes.{budget_class}"
                expected_entry_fields = {
                    "label",
                    "category",
                    "soft_target",
                    "hard_ceiling",
                    "calibration_status",
                }
                if not exact_keys(
                    entry,
                    expected_entry_fields,
                    entry_context,
                ):
                    continue
                assert isinstance(entry, dict)
                if not isinstance(entry["label"], str) or not entry["label"].strip():
                    errors.append(f"{entry_context}.label must be non-empty text")
            try:
                derived_context_budget_limits(context_budget)
            except ValueError as exc:
                errors.append(f"context_budget_contract: {exc}")
        duplicate_ratio = context_budget["duplicate_rule_token_ratio_max"]
        if (
            isinstance(duplicate_ratio, bool)
            or not isinstance(duplicate_ratio, (int, float))
            or not 0 <= duplicate_ratio < 1
        ):
            errors.append(
                "context_budget_contract.duplicate_rule_token_ratio_max must be in [0, 1)"
            )
        runtime_projection = context_budget["runtime_asset_projection"]
        expected_runtime_projection = {
            "schema_version": 1,
            "baseline_commit": "ee55c55e4950f7abd7818de0290076e3f6fe0467",
            "ordinary_cohort": [
                "single-file-bug-fix",
                "single-module-feature",
                "review-only",
                "validation-task-no-edit",
            ],
            "exceptional_cohort": [
                "diagnosis-only",
                "material-executable-evidence-continuation",
                "runtime-asset-integrity-failure",
                "filesystem-process-normal-correctness",
                "filesystem-process-trust-sensitive",
            ],
            "comparison_key": ["case", "host", "step", "budget_class"],
            "identity_accounting": "inline-existing-component-bytes",
            "identity_component_count_per_professional_assignment": 0,
            "integrity_manifest_runtime_load_count": 0,
            "selective_identity_field_read_count": 0,
            "identity_structural_selector_load_delta_max": 0,
            "inline_accounted_components": [
                "professional-entrypoint",
                "selector-or-reference-partition",
                "logical-selection-receipt",
                "targeted-reference-layer3-marker",
            ],
            "cross_skill_selector_locator_occurrence_count": 0,
            "cumulative_trajectory_cost": (
                "reported-observation-not-correctness-acceptance"
            ),
            "post_implementation_gate": (
                "unproved-stop-on-context-route-coverage-or-binding-failure"
            ),
            "ordinary_delta_gate": {
                "operator": "less-than-or-equal-minimum",
                "absolute_token_max": 32,
                "relative_ppm": 15_000,
                "relative_rounding": "ceiling",
            },
            "main_token_delta_max": 0,
            "profile_token_delta_max": 0,
            "duplicate_rule_token_ratio_max": 0.03,
            "required_semantic_counts": (
                "non-decreasing-skills-layer3-references-validation-review"
            ),
            "measurement_limits": [
                "deterministic-token-proxy-not-live-billed-tokens",
                "deterministic-trace-not-live-host-behavior",
                "no-wall-clock-proof",
            ],
        }
        if runtime_projection != expected_runtime_projection:
            errors.append(
                "context_budget_contract.runtime_asset_projection must freeze inline "
                "Runtime identity accounting and ordinary/exceptional cohorts"
            )
        quality_cost_gate = context_budget["quality_cost_gate"]
        gate_fields = {
            "schema_version",
            "owner",
            "scope",
            "behavior_authority",
            "quality_dimensions",
            "cost_metrics",
            "quality_preserving_verdicts",
            "regression_verdict",
            "missing_evidence_verdict",
            "structural_claim",
            "not_collected_value",
            "frontier_rule",
            "candidate_total_not_greater_is_correctness_acceptance",
            "hard_ceiling_independent",
            "required_context_truncation",
            "static_token_proxy_proves_latency",
            "runtime_dependency",
        }
        if exact_keys(
            quality_cost_gate,
            gate_fields,
            "context_budget_contract.quality_cost_gate",
        ):
            assert isinstance(quality_cost_gate, dict)
            behavior_contract = data.get("behavior_eval_contract", {})
            behavior_verdicts = (
                behavior_contract.get("verdicts", [])
                if isinstance(behavior_contract, dict)
                else []
            )
            expected_gate = {
                "schema_version": 1,
                "owner": "context-budget-authority",
                "scope": "dev-eval-only",
                "behavior_authority": "behavior_eval_contract",
                "quality_dimensions": ["routing", "review", "codegen"],
                "cost_metrics": ["tokens", "turns", "elapsed_ms"],
                "quality_preserving_verdicts": [
                    "improved",
                    "hardening_only",
                    "no_effect",
                ],
                "regression_verdict": "regression",
                "missing_evidence_verdict": "not_enough_evidence",
                "structural_claim": "structural-only",
                "not_collected_value": "not_collected",
                "frontier_rule": "quality-preserved-before-cost-comparison",
                "candidate_total_not_greater_is_correctness_acceptance": False,
                "hard_ceiling_independent": True,
                "required_context_truncation": "forbidden",
                "static_token_proxy_proves_latency": False,
                "runtime_dependency": False,
            }
            if quality_cost_gate != expected_gate:
                errors.append(
                    "context_budget_contract.quality_cost_gate must preserve the "
                    "quality-first dev/eval-only cost frontier contract"
                )
            if not set(quality_cost_gate["quality_preserving_verdicts"]).issubset(
                set(behavior_verdicts)
            ) or any(
                quality_cost_gate[field] not in behavior_verdicts
                for field in ("regression_verdict", "missing_evidence_verdict")
            ):
                errors.append(
                    "context_budget_contract.quality_cost_gate verdicts must derive "
                    "from behavior_eval_contract"
                )

    final_goal = data["final_goal_contract"]
    if exact_keys(
        final_goal,
        {
            "schema_version",
            "maximum_structural_proxies",
            "professional_review_cost_fixtures",
        },
        "final_goal_contract",
    ):
        assert isinstance(final_goal, dict)
        if final_goal["schema_version"] != 3:
            errors.append("final_goal_contract.schema_version must be 3")
        proxies = final_goal["maximum_structural_proxies"]
        expected_proxies = {
            "control_turn_count",
            "duplicate_read_count",
            "subagent_count",
            "verification_action_count",
        }
        if not isinstance(proxies, dict) or set(proxies) != expected_proxies:
            errors.append(
                "final_goal_contract.maximum_structural_proxies must define control "
                "turn, subagent, duplicate-read, and verification-action costs"
            )
        else:
            for name, value in proxies.items():
                if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                    errors.append(
                        f"final_goal_contract.maximum_structural_proxies.{name} "
                        "must be a non-negative integer"
                    )
        fixtures = final_goal["professional_review_cost_fixtures"]
        fixture_fields = {
            "thresholds",
            "formal_round_policy",
        }
        if not isinstance(fixtures, dict) or set(fixtures) != fixture_fields:
            errors.append(
                "final_goal_contract.professional_review_cost_fixtures must "
                "define thresholds and formal_round_policy"
            )
        else:
            thresholds = fixtures["thresholds"]
            threshold_fields = {
                "maximum_fresh_target_count",
                "maximum_mean_fresh_target_count",
                "maximum_input_ratio_ppm",
                "maximum_mean_input_ratio_ppm",
            }
            valid_thresholds = bool(
                isinstance(thresholds, dict)
                and set(thresholds) == threshold_fields
                and all(
                    isinstance(value, int)
                    and not isinstance(value, bool)
                    and value > 0
                    for value in thresholds.values()
                )
            )
            if not valid_thresholds:
                errors.append(
                    "professional review cost thresholds must define positive "
                    "integer fresh-target and input-ratio bounds"
                )
            elif (
                thresholds["maximum_mean_fresh_target_count"]
                > thresholds["maximum_fresh_target_count"]
                or thresholds["maximum_mean_input_ratio_ppm"]
                > thresholds["maximum_input_ratio_ppm"]
                or thresholds["maximum_input_ratio_ppm"] > 1_000_000
                or thresholds["maximum_fresh_target_count"] > 188
            ):
                valid_thresholds = False
                errors.append(
                    "professional review cost threshold ordering or ppm bounds "
                    "are invalid"
                )
            formal_round_policy = fixtures["formal_round_policy"]
            expected_formal_round_policy = {
                "schema_version": 1,
                "full_fresh_source_material_coverage_ratio_ppm": 1_000_000,
                "maximum_reviewer_added_relationship_evidence_metadata_overhead_ratio_ppm": 50_000,
                "maximum_reviewer_added_unique_union_to_required_ratio_ppm": 1_000_000,
            }
            if (
                not isinstance(formal_round_policy, dict)
                or set(formal_round_policy)
                != PROFESSIONAL_REVIEW_FORMAL_ROUND_POLICY_FIELDS
                or formal_round_policy != expected_formal_round_policy
            ):
                errors.append(
                    "professional review formal-round policy must preserve "
                    "schema 1, complete source coverage, 50000 ppm metadata "
                    "overhead, and a 1000000 ppm reviewer-added union bound"
                )
    reference = data["reference_contract"]
    reference_fields = {
        "schema_version",
        "fields",
        "types",
        "outputs",
        "allowed_outputs_by_type",
        "minimum_outputs_by_type",
        "control_required_by",
        "control_required_output",
    }
    if exact_keys(reference, reference_fields, "reference_contract"):
        assert isinstance(reference, dict)
        if reference["schema_version"] != 2:
            errors.append("reference_contract.schema_version must be 2")
        fields = string_list(reference["fields"], "reference_contract.fields")
        required_reference_fields = {
            "path",
            "type",
            "load_when",
            "do_not_load_when",
            "required_by",
            "required_output",
        }
        if set(fields) != required_reference_fields:
            errors.append(
                "reference_contract.fields must define the complete Reference Contract v2"
            )
        types = string_list(reference["types"], "reference_contract.types")
        outputs = reference["outputs"]
        if not isinstance(outputs, dict) or not outputs or any(
            not isinstance(key, str)
            or not key
            or not isinstance(value, str)
            or not value.strip()
            for key, value in (outputs.items() if isinstance(outputs, dict) else ())
        ):
            errors.append("reference_contract.outputs must map output ids to non-empty text")
            outputs = {}
        allowed = reference["allowed_outputs_by_type"]
        minimum = reference["minimum_outputs_by_type"]
        validated_output_mappings: dict[str, dict[str, list[str]]] = {}
        for mapping_name, mapping in (
            ("allowed_outputs_by_type", allowed),
            ("minimum_outputs_by_type", minimum),
        ):
            validated_output_mappings[mapping_name] = {}
            if not isinstance(mapping, dict) or set(mapping) != set(types):
                errors.append(
                    f"reference_contract.{mapping_name} keys must match Reference types"
                )
                continue
            for type_name, values in mapping.items():
                items = string_list(
                    values,
                    f"reference_contract.{mapping_name}.{type_name}",
                    nonempty=mapping_name == "allowed_outputs_by_type",
                )
                validated_output_mappings[mapping_name][type_name] = items
                unknown = sorted(set(items) - set(outputs))
                if unknown:
                    errors.append(
                        f"reference_contract.{mapping_name}.{type_name} contains "
                        f"unknown outputs {unknown}"
                    )
        validated_allowed = validated_output_mappings["allowed_outputs_by_type"]
        validated_minimum = validated_output_mappings["minimum_outputs_by_type"]
        for type_name in set(validated_allowed) & set(validated_minimum):
            if not set(validated_minimum[type_name]) <= set(validated_allowed[type_name]):
                    errors.append(
                        f"reference_contract.minimum_outputs_by_type.{type_name} "
                        "must be allowed for that type"
                    )
        required_by = reference["control_required_by"]
        required_output = reference["control_required_output"]
        if not isinstance(required_by, dict) or not isinstance(required_output, dict):
            errors.append("Reference control projections must be objects")
        else:
            if set(required_by) != set(required_output):
                errors.append("Reference control projection paths must match")
            for path, required_roles in required_by.items():
                role_items = string_list(
                    required_roles,
                    f"reference_contract.control_required_by.{path}",
                )
                if not set(role_items) <= set(roles):
                    errors.append(f"{path}: control_required_by contains an unknown role")
            for path, required_outputs in required_output.items():
                output_items = string_list(
                    required_outputs,
                    f"reference_contract.control_required_output.{path}",
                )
                if not set(output_items) <= set(outputs):
                    errors.append(f"{path}: control_required_output contains an unknown output")


    def ordered_heading_titles(value: object, context: str) -> list[str]:
        if not isinstance(value, list) or not value:
            errors.append(f"{context} must be a non-empty heading list")
            return []
        titles: list[str] = []
        for index, item in enumerate(value):
            if (
                not isinstance(item, list)
                or len(item) != 2
                or not isinstance(item[0], int)
                or isinstance(item[0], bool)
                or item[0] not in {1, 2, 3}
                or not isinstance(item[1], str)
                or not item[1].strip()
            ):
                errors.append(f"{context}[{index}] must be [level, title]")
                continue
            titles.append(item[1])
        if len(titles) != len(set(titles)):
            errors.append(f"{context} titles must be unique")
        if value and sum(
            1 for item in value if isinstance(item, list) and item and item[0] == 1
        ) != 1:
            errors.append(f"{context} must contain exactly one H1")
        if (
            value
            and (
                not isinstance(value[0], list)
                or len(value[0]) != 2
                or value[0][0] != 1
            )
        ):
            errors.append(f"{context} must start with its H1")
        return titles

    def concept_contract_errors(
        concepts: object,
        headings: list[str],
        context: str,
    ) -> set[str]:
        if not isinstance(concepts, list) or not concepts:
            errors.append(f"{context} must be a non-empty list")
            return set()
        identifiers: list[str] = []
        for index, concept in enumerate(concepts):
            item_context = f"{context}[{index}]"
            if not exact_keys(concept, {"id", "section", "required_terms"}, item_context):
                continue
            assert isinstance(concept, dict)
            identifier = concept["id"]
            if not isinstance(identifier, str) or re.fullmatch(
                r"[a-z0-9]+(?:-[a-z0-9]+)*", identifier
            ) is None:
                errors.append(f"{item_context}.id must be kebab-case")
            else:
                identifiers.append(identifier)
            section = concept["section"]
            if section is not None and section not in headings:
                errors.append(f"{item_context}.section is not an ordered heading")
            string_list(concept["required_terms"], f"{item_context}.required_terms")
        if len(identifiers) != len(set(identifiers)):
            errors.append(f"{context} ids must be unique")
        return set(identifiers)


    if "execution_level_contract" in data:
        errors.append("Execution Levels are retired; do not introduce a replacement hierarchy")
    environment = data["environment_risk_calibration_contract"]
    if environment.get("baseline", {}).get("safety_proof") is not False:
        errors.append("the controlled workspace baseline must not be treated as safety proof")
    if environment.get("escalation_requires_all") != ["less-trusted-actor-input-or-writer", "privilege-or-sensitive-asset", "reachable-material-impact-path"]:
        errors.append("trust escalation requires actor, affected asset and reachable impact")
    if environment.get("filesystem_process_safety_projection", {}).get("critical_unknown_ref") != "#/environment_risk_calibration_contract/critical_unknown":
        errors.append("critical unknown must resolve to the reachable-risk owner")
    return errors


def load_core_contracts(path: Path = CORE_CONTRACTS_PATH) -> dict[str, Any]:
    """Load the authoritative static control model and reject partial schemas."""

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot load authoritative control model {path}: {exc}") from exc
    errors = validate_core_contracts(data)
    if errors:
        raise RuntimeError(
            "invalid authoritative control model:\n- " + "\n- ".join(errors)
        )
    assert isinstance(data, dict)
    return data


CORE_CONTRACTS = load_core_contracts()
PRINCIPLE_ACCEPTANCE_PRODUCER_PATHS = tuple(
    sorted(
        {
            str(producer["argv"][1])
            for producer in CORE_CONTRACTS["principle_acceptance_contract"][
                "producers"
            ]
        }
    )
)
AUTHORITATIVE_BUILD_INPUT_FILES = tuple(
    dict.fromkeys(
        (
            *AUTHORITATIVE_BUILD_INPUT_BASE_FILES,
            *PRINCIPLE_ACCEPTANCE_PRODUCER_PATHS,
        )
    )
)
REFERENCE_CONTRACT_MODEL = CORE_CONTRACTS["reference_contract"]
ROUTE_DECISION_MODEL = CORE_CONTRACTS["route_decision_contract"]
ROLE_CONTRACT_MODEL = CORE_CONTRACTS["roles"]


def _valid_current_task_id(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(value.strip())
        and value.strip().casefold() != "unspecified"
    )


_TASK_PATH_GLOB_CHARS = frozenset("*?[")


def _path_is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


_EXECUTION_BLOCKER_RE = re.compile(
    r"^EXECUTION_BLOCKED task=(?P<task>[^;\n]+); "
    r"operation=(?P<operation>read|edit|execute); "
    r"observed=(?P<observed>[^\n]+)$"
)
def _normalized_task_path(value: object, workspace_root: Path) -> str:
    """Normalize one scoped path/glob and reject lexical or symlink escape."""

    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise ValueError("scoped path must be a non-empty string")
    raw = value.strip()
    candidate = Path(raw)
    if ".." in candidate.parts:
        raise ValueError("parent traversal is forbidden")
    parts = candidate.parts
    glob_index = next(
        (
            index
            for index, part in enumerate(parts)
            if any(marker in part for marker in _TASK_PATH_GLOB_CHARS)
        ),
        len(parts),
    )
    prefix = Path(*parts[:glob_index]) if glob_index else Path(".")
    lexical_prefix = prefix if prefix.is_absolute() else workspace_root / prefix
    resolved_prefix = lexical_prefix.resolve(strict=False)
    lexical_inside_workspace = _path_is_within(lexical_prefix, workspace_root)
    if (not candidate.is_absolute() or lexical_inside_workspace) and not _path_is_within(
        resolved_prefix, workspace_root
    ):
        raise ValueError("relative or existing symlink escape is forbidden")
    remainder = parts[glob_index:]
    return resolved_prefix.joinpath(*remainder).as_posix()

def _target_in_task_scope(
    target: object,
    scope: list[str],
    workspace_root: Path,
) -> bool:
    try:
        candidate = _normalized_task_path(target, workspace_root)
        normalized_scope = [
            _normalized_task_path(allowed, workspace_root) for allowed in scope
        ]
    except ValueError:
        return False
    return any(
        _task_path_glob_matches(candidate, allowed) for allowed in normalized_scope
    )

def _task_path_glob_matches(candidate: str, pattern: str) -> bool:
    """Match normalized paths without letting segment globs consume ``/``.

    A standalone ``**`` segment matches zero or more complete path segments.
    Other glob syntax is delegated to ``fnmatchcase`` one segment at a time.
    """

    candidate_parts = candidate.split("/")
    pattern_parts = pattern.split("/")

    def match(candidate_index: int, pattern_index: int) -> bool:
        while pattern_index < len(pattern_parts):
            pattern_part = pattern_parts[pattern_index]
            if pattern_part == "**":
                if pattern_index + 1 == len(pattern_parts):
                    return True
                return any(
                    match(next_candidate, pattern_index + 1)
                    for next_candidate in range(
                        candidate_index, len(candidate_parts) + 1
                    )
                )
            if candidate_index >= len(candidate_parts) or not fnmatchcase(
                candidate_parts[candidate_index], pattern_part
            ):
                return False
            candidate_index += 1
            pattern_index += 1
        return candidate_index == len(candidate_parts)

    return match(0, 0)


def format_execution_blocker(
    *, task_id: str, operation: str, observed: str
) -> str:
    """Format canonical syntax after a caller observes a Host/tool failure.

    Formatting proves no failure provenance. The invocation event and raw Host
    output remain the only failure evidence owner.
    """

    if not _valid_current_task_id(task_id) or any(
        marker in task_id for marker in (";", "\n", "\r")
    ):
        raise ValueError("execution blocker requires the current real Task ID")
    if operation not in {"read", "edit", "execute"}:
        raise ValueError("execution blocker operation must be read, edit, or execute")
    if (
        not isinstance(observed, str)
        or not observed.strip()
        or "\n" in observed
        or "\r" in observed
    ):
        raise ValueError("execution blocker observed text must be one non-empty line")
    return (
        f"EXECUTION_BLOCKED task={task_id}; operation={operation}; "
        f"observed={observed.strip()}"
    )


def execution_blocker_errors(
    value: object,
    *,
    current_task_id: str,
    expected_operation: str,
) -> list[str]:
    """Check blocker syntax and identity, never actual failure provenance."""

    errors: list[str] = []
    if not _valid_current_task_id(current_task_id):
        return ["current Task ID must be non-empty and not unspecified"]
    if not isinstance(value, str):
        return ["execution blocker must be the canonical visible string"]
    match = _EXECUTION_BLOCKER_RE.fullmatch(value)
    if match is None:
        return ["execution blocker must match the canonical actual-failure format"]
    if match.group("task") != current_task_id:
        errors.append("execution blocker must preserve the current Task ID")
    blocker_operation = "read" if expected_operation == "search" else expected_operation
    if blocker_operation not in {"read", "edit", "execute"}:
        errors.append("expected operation is outside blocker syntax")
    if match.group("operation") != blocker_operation:
        errors.append("execution blocker operation must match expected operation")
    return errors


def _git_diff_header_paths(header: str) -> tuple[str, str] | None:
    try:
        fields = shlex.split(header)
    except ValueError:
        return None
    if (
        len(fields) != 4
        or fields[:2] != ["diff", "--git"]
        or not fields[2].startswith("a/")
        or not fields[3].startswith("b/")
        or len(fields[2]) <= 2
        or len(fields[3]) <= 2
    ):
        return None
    return fields[2][2:], fields[3][2:]


def _diff_metadata_values(lines: list[str]) -> dict[str, str] | None:
    patterns = (
        ("index", r"index [0-9a-f]+\.\.[0-9a-f]+(?: [0-7]{6})?"),
        ("old-mode", r"old mode [0-7]{6}"),
        ("new-mode", r"new mode [0-7]{6}"),
        ("new-file", r"new file mode [0-7]{6}"),
        ("deleted-file", r"deleted file mode [0-7]{6}"),
        ("similarity", r"similarity index [0-9]+%"),
        ("dissimilarity", r"dissimilarity index [0-9]+%"),
        ("rename-from", r"rename from (.+)"),
        ("rename-to", r"rename to (.+)"),
        ("copy-from", r"copy from (.+)"),
        ("copy-to", r"copy to (.+)"),
    )
    values: dict[str, str] = {}
    for line in lines:
        matched = False
        for key, pattern in patterns:
            match = re.fullmatch(pattern, line)
            if match is None:
                continue
            if key in values:
                return None
            values[key] = match.group(1) if match.lastindex else line
            matched = True
            break
        if not matched:
            return None
    return values


def _diff_metadata_form(
    lines: list[str],
    before_path: str,
    after_path: str,
    content_kind: str,
) -> str | None:
    values = _diff_metadata_values(lines)
    if values is None:
        return None
    keys = set(values)
    rename_keys = {"rename-from", "rename-to"}
    copy_keys = {"copy-from", "copy-to"}
    similarity_keys = {"similarity", "dissimilarity"}
    if len(keys & similarity_keys) > 1:
        return None

    if keys & (rename_keys | copy_keys):
        if keys & rename_keys and keys & copy_keys:
            return None
        form = "rename" if keys & rename_keys else "copy"
        pair = rename_keys if form == "rename" else copy_keys
        if (
            before_path == after_path
            or not pair <= keys
            or len(keys & similarity_keys) != 1
            or not keys <= pair | similarity_keys | {"index"}
            or values[f"{form}-from"] != before_path
            or values[f"{form}-to"] != after_path
            or (content_kind == "none" and "index" in keys)
        ):
            return None
        return form

    if before_path != after_path:
        return None
    if "new-file" in keys or "deleted-file" in keys:
        if (
            content_kind not in {"text", "binary"}
            or {"new-file", "deleted-file"} <= keys
        ):
            return None
        form = "new" if "new-file" in keys else "delete"
        marker = "new-file" if form == "new" else "deleted-file"
        return form if keys <= {marker, "index"} else None

    mode_keys = {"old-mode", "new-mode"}
    if keys & mode_keys and not mode_keys <= keys:
        return None
    if content_kind == "none":
        return "mode" if keys == mode_keys else None
    if content_kind not in {"text", "binary"}:
        return None
    return "normal" if keys <= {"index", *mode_keys} else None


def _valid_unified_hunks(lines: list[str]) -> bool:
    if not lines:
        return False
    header_pattern = re.compile(
        r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?: .*)?"
    )
    index = 0
    while index < len(lines):
        match = header_pattern.fullmatch(lines[index])
        if match is None:
            return False
        expected_old = int(match.group(2) or 1)
        expected_new = int(match.group(4) or 1)
        old_count = 0
        new_count = 0
        content_count = 0
        change_count = 0
        index += 1
        while index < len(lines) and not lines[index].startswith("@@ "):
            line = lines[index]
            if line == r"\ No newline at end of file":
                if content_count == 0:
                    return False
            elif not line:
                return False
            elif line[0] == " ":
                old_count += 1
                new_count += 1
                content_count += 1
            elif line[0] == "-":
                old_count += 1
                content_count += 1
                change_count += 1
            elif line[0] == "+":
                new_count += 1
                content_count += 1
                change_count += 1
            else:
                return False
            index += 1
        if (
            content_count == 0
            or change_count == 0
            or old_count != expected_old
            or new_count != expected_new
        ):
            return False
    return True


def unified_diff_paths(payload: object) -> list[str] | None:
    """Return exact changed paths only for a structurally valid Git diff."""

    if not isinstance(payload, str) or not payload.strip():
        return None
    section_matches = list(re.finditer(r"^diff --git .+$", payload, flags=re.MULTILINE))
    if not section_matches or payload[: section_matches[0].start()].strip():
        return None
    changed_paths: list[str] = []
    for section_index, match in enumerate(section_matches):
        end = (
            section_matches[section_index + 1].start()
            if section_index + 1 < len(section_matches)
            else len(payload)
        )
        section_lines = payload[match.start() : end].splitlines()
        header_paths = _git_diff_header_paths(section_lines[0])
        if header_paths is None or len(section_lines) == 1:
            return None
        before_path, after_path = header_paths
        body = section_lines[1:]
        hunk_indexes = [index for index, line in enumerate(body) if line.startswith("@@")]
        first_hunk = hunk_indexes[0] if hunk_indexes else len(body)
        file_header_region = body[:first_hunk]
        old_headers = [
            index
            for index, line in enumerate(file_header_region)
            if line.startswith("--- ")
        ]
        new_headers = [
            index
            for index, line in enumerate(file_header_region)
            if line.startswith("+++ ")
        ]
        binary_lines = [line for line in body if line.startswith("Binary files ")]
        if old_headers or new_headers or hunk_indexes:
            if (
                len(old_headers) != 1
                or len(new_headers) != 1
                or new_headers[0] != old_headers[0] + 1
                or not hunk_indexes
                or hunk_indexes[0] != new_headers[0] + 1
                or binary_lines
            ):
                return None
            form = _diff_metadata_form(
                body[: old_headers[0]], before_path, after_path, "text"
            )
            if form not in {"normal", "new", "delete", "rename", "copy"}:
                return None
            expected_old = "/dev/null" if form == "new" else f"a/{before_path}"
            expected_new = "/dev/null" if form == "delete" else f"b/{after_path}"
            if (
                body[old_headers[0]] != f"--- {expected_old}"
                or body[new_headers[0]] != f"+++ {expected_new}"
                or not _valid_unified_hunks(body[hunk_indexes[0] :])
            ):
                return None
        else:
            if binary_lines:
                if len(binary_lines) != 1:
                    return None
                marker_index = body.index(binary_lines[0])
                form = _diff_metadata_form(
                    body[:marker_index], before_path, after_path, "binary"
                )
                if form not in {"normal", "new", "delete", "rename", "copy"}:
                    return None
                expected_old = "/dev/null" if form == "new" else f"a/{before_path}"
                expected_new = "/dev/null" if form == "delete" else f"b/{after_path}"
                marker = f"Binary files {expected_old} and {expected_new} differ"
                if binary_lines[0] != marker or marker_index != len(body) - 1:
                    return None
            else:
                form = _diff_metadata_form(body, before_path, after_path, "none")
                if form not in {"rename", "copy", "mode"}:
                    return None
        changed_paths.append(before_path if form == "delete" else after_path)
    if len(changed_paths) != len(set(changed_paths)):
        return None
    return changed_paths


def native_change_reference_bound(
    artifact: object,
    changed_paths: object,
    current_generation: object,
    assigned_reviewer: str,
    *,
    native_fields: tuple[str, ...] = (
        "reference",
        "generation",
        "reviewer",
        "changed_paths",
        "readable",
    ),
) -> bool:
    """Fail closed because this static owner has no native-change resolver.

    A native reference becomes review evidence only when the Host actually
    dereferences it and binds the exact read content to the current reviewer,
    generation, and changed paths. These caller-supplied fields cannot prove
    that event, even when they are internally consistent.
    """

    del artifact, changed_paths, current_generation, assigned_reviewer, native_fields
    return False


def exact_change_evidence_accessible(
    kind: object,
    artifact: object,
    changed_paths: object,
    accessibility: object,
    *,
    current_generation: object,
    assigned_reviewer: str,
    exact_kinds: set[str],
    accessibility_fields: tuple[str, ...],
    native_fields: tuple[str, ...],
) -> bool:
    """Validate supplied exact diff evidence through the single strict owner."""

    if (
        not isinstance(accessibility, dict)
        or tuple(accessibility) != accessibility_fields
        or accessibility.get("reviewer") != assigned_reviewer
        or accessibility.get("generation") != current_generation
        or accessibility.get("changed_paths") != changed_paths
        or accessibility.get("readable") is not True
    ):
        return False
    if kind == "reviewer-accessible-native-reference":
        return native_change_reference_bound(
            artifact,
            changed_paths,
            current_generation,
            assigned_reviewer,
            native_fields=native_fields,
        )
    return kind in exact_kinds and unified_diff_paths(artifact) == changed_paths


CONTEXT_BUDGET_MODEL = CORE_CONTRACTS["context_budget_contract"]
BEHAVIOR_EVAL_MODEL = behavior_eval_authority(CORE_CONTRACTS)
PROMPT_CONTRACT_MODEL = CORE_CONTRACTS["prompt_contract"]
PROFILE_CONTRACT_MODEL = CORE_CONTRACTS["profile_contract"]
CONTROL_SKILL_CONTRACT_MODEL = CORE_CONTRACTS["control_skill_contract"]
DOCS_CONTRACT_MODEL = CORE_CONTRACTS["docs_contract"]


REFERENCE_CONTEXT_ADMISSIBILITY_CONTRACT = (
    "changeforge.reference-context-admissibility/v3"
)
_REFERENCE_CONTEXT_DECLARATION_FIELDS = {
    "conflicts_with",
    "decision_problem",
    "sequenced_after",
    "must_co_trigger_with",
}
_REFERENCE_CONTEXT_SEQUENCE_FIELDS = {
    "reference",
    "required_output",
    "carried_by",
}
_REFERENCE_CONTEXT_RECEIPT_FIELDS = {
    "contract",
    "authority_contract",
    "selection_owner",
    "profile",
    "professional_skill",
    "selection_kind",
    "selection_basis",
    "selector_ids",
    "evidence_signals",
    "selected_layer3",
}


def _reference_context_carrier_authority() -> dict[str, set[str]]:
    # Eval-only staged Reference outputs may travel in optional human-readable
    # decisions or review evidence. No Task/Review runtime record is required.
    return {
        "selector-receipt": set(_REFERENCE_CONTEXT_RECEIPT_FIELDS),
        "engineering-brief": {"Key Decisions", "Important Constraints and Invariants"},
        "review-handoff": {"Evidence", "Proof Limit"},
    }


def _reference_context_carrier_field_error(value: object) -> str | None:
    if not isinstance(value, str) or not value:
        return "carrier field must be a non-empty string"
    namespaces = _reference_context_carrier_authority()
    for namespace in sorted(namespaces, key=len, reverse=True):
        prefix = f"{namespace}."
        if value.startswith(prefix):
            field = value[len(prefix) :]
            if field in namespaces[namespace]:
                return None
            return f"unknown or case-mismatched {namespace} field {field!r}"
    return f"unknown carrier namespace in {value!r}"


def reference_context_admissibility_authority(
    professional_data: object,
    foundation_data: object,
    domain_data: object | None = None,
    *,
    context: str = "Reference context admissibility",
) -> dict[str, object]:
    """Project source-owned eval-only Reference reachability declarations."""

    documents = [
        (professional_data, "professional_skills", "professional"),
        (foundation_data, "foundation_skills", "foundation"),
    ]
    if domain_data is not None:
        documents.append((domain_data, "domain_skills", "domain"))
    owners: dict[str, dict[str, object]] = {}
    declared_count = 0
    for document, list_name, layer in documents:
        if not isinstance(document, dict) or not isinstance(
            document.get(list_name), list
        ):
            raise ValidationProblem(
                f"{context}: {layer} registry must contain {list_name}"
            )
        for index, row in enumerate(document[list_name]):
            row_context = f"{context}:{layer}[{index}]"
            if not isinstance(row, dict):
                raise ValidationProblem(f"{row_context} must be a mapping")
            owner = row.get("name")
            if not isinstance(owner, str) or not owner:
                raise ValidationProblem(f"{row_context}.name must be a Skill id")
            if owner in owners:
                raise ValidationProblem(
                    f"{context}: Reference owner {owner!r} is duplicated"
                )
            contracts = reference_contracts(
                row.get("reference_index"),
                f"{row_context}.reference_index",
                owner=owner,
            )
            reference_types = {
                contract["path"]: contract["type"] for contract in contracts
            }
            reference_roles = {
                contract["path"]: list(contract["required_by"])
                for contract in contracts
            }
            reference_outputs = {
                contract["path"]: list(contract["required_output"])
                for contract in contracts
            }
            projection: dict[str, object] = {
                "layer": layer,
                "reference_types": reference_types,
                "reference_roles": reference_roles,
                "reference_outputs": reference_outputs,
                "declarations": {},
            }
            raw_declaration = row.get("context_admissibility")
            if raw_declaration is not None:
                if not isinstance(raw_declaration, dict) or set(
                    raw_declaration
                ) != {"contract", "references"}:
                    raise ValidationProblem(
                        f"{row_context}.context_admissibility must contain "
                        "contract and references"
                    )
                if (
                    raw_declaration["contract"]
                    != REFERENCE_CONTEXT_ADMISSIBILITY_CONTRACT
                ):
                    raise ValidationProblem(
                        f"{row_context}.context_admissibility contract is invalid"
                    )
                declared_references = raw_declaration["references"]
                if not isinstance(declared_references, dict) or not declared_references:
                    raise ValidationProblem(
                        f"{row_context}.context_admissibility.references must be a "
                        "non-empty mapping"
                    )
                declarations: dict[str, dict[str, object]] = {}
                for path, raw_rule in declared_references.items():
                    rule_context = (
                        f"{row_context}.context_admissibility.references[{path!r}]"
                    )
                    if path not in reference_types:
                        raise ValidationProblem(
                            f"{rule_context} names an unknown owner Reference"
                        )
                    if reference_types[path] == "index":
                        raise ValidationProblem(
                            f"{rule_context} cannot declare an index Reference"
                        )
                    if not isinstance(raw_rule, dict) or set(raw_rule) != (
                        _REFERENCE_CONTEXT_DECLARATION_FIELDS
                    ):
                        raise ValidationProblem(
                            f"{rule_context} must contain exactly "
                            f"{sorted(_REFERENCE_CONTEXT_DECLARATION_FIELDS)}"
                        )
                    conflicts = raw_rule["conflicts_with"]
                    decision_problem = raw_rule["decision_problem"]
                    sequenced_after = raw_rule["sequenced_after"]
                    must_co_trigger = raw_rule["must_co_trigger_with"]
                    expected_problem = PurePosixPath(path).stem
                    if decision_problem != expected_problem:
                        raise ValidationProblem(
                            f"{rule_context}.decision_problem must equal the "
                            f"source filename stem {expected_problem!r}"
                        )
                    if (
                        not isinstance(conflicts, list)
                        or any(
                            not isinstance(conflict, str) or not conflict
                            for conflict in conflicts
                        )
                        or len(conflicts) != len(set(conflicts))
                    ):
                        raise ValidationProblem(
                            f"{rule_context}.conflicts_with must be a unique string list"
                        )
                    unknown_conflicts = sorted(
                        set(conflicts) - set(reference_types)
                    )
                    if unknown_conflicts or path in conflicts:
                        raise ValidationProblem(
                            f"{rule_context}.conflicts_with must name other owner "
                            f"References; unknown={unknown_conflicts}"
                        )
                    if not isinstance(sequenced_after, list) or any(
                        not isinstance(sequence, dict)
                        or set(sequence) != _REFERENCE_CONTEXT_SEQUENCE_FIELDS
                        for sequence in sequenced_after
                    ):
                        raise ValidationProblem(
                            f"{rule_context}.sequenced_after must contain exact "
                            "reference/required_output/carried_by mappings"
                        )
                    if (
                        not isinstance(must_co_trigger, list)
                        or any(
                            not isinstance(reference, str) or not reference
                            for reference in must_co_trigger
                        )
                        or len(must_co_trigger) != len(set(must_co_trigger))
                    ):
                        raise ValidationProblem(
                            f"{rule_context}.must_co_trigger_with must be a unique "
                            "qualified Reference list"
                        )
                    declarations[path] = {
                        "conflicts_with": list(conflicts),
                        "decision_problem": decision_problem,
                        "sequenced_after": copy.deepcopy(sequenced_after),
                        "must_co_trigger_with": list(must_co_trigger),
                    }
                    declared_count += 1
                projection["declarations"] = declarations
            owners[owner] = projection

    qualified_references: dict[str, tuple[str, str, dict[str, object]]] = {}
    for owner, projection in owners.items():
        reference_types = projection["reference_types"]
        assert isinstance(reference_types, dict)
        for path in reference_types:
            qualified_references[f"{owner}/{path}"] = (owner, path, projection)

    receipt_fields = [
        f"selector-receipt.{field}"
        for field in (
            "contract",
            "authority_contract",
            "selection_owner",
            "profile",
            "professional_skill",
            "selection_kind",
            "selection_basis",
            "selector_ids",
            "evidence_signals",
            "selected_layer3",
                )
    ]
    brief_fields = ["engineering-brief.Key Decisions", "engineering-brief.Important Constraints and Invariants"]
    expected_carriers = {
        "task-agent": {"engineering-brief": [*receipt_fields, *brief_fields]},
        "review-agent": {"engineering-brief": [*receipt_fields, *brief_fields, "review-handoff.Evidence", "review-handoff.Proof Limit"]},
    }
    sequence_edges: set[tuple[str, str]] = set()
    co_trigger_edges: set[frozenset[str]] = set()
    conflict_edges: set[frozenset[str]] = set()
    sequence_count = 0
    for owner, projection in owners.items():
        declarations = projection["declarations"]
        reference_roles = projection["reference_roles"]
        assert isinstance(declarations, dict)
        assert isinstance(reference_roles, dict)
        for path, rule in declarations.items():
            assert isinstance(rule, dict)
            qualified_path = f"{owner}/{path}"
            for conflict in rule["conflicts_with"]:
                reverse = declarations.get(conflict)
                if not isinstance(reverse, dict) or path not in reverse["conflicts_with"]:
                    raise ValidationProblem(
                        f"{context}:{qualified_path} conflict with {conflict!r} "
                        "must be reciprocal and source-owned"
                    )
                conflict_edges.add(frozenset((qualified_path, f"{owner}/{conflict}")))
            for sequence_index, sequence in enumerate(rule["sequenced_after"]):
                sequence_context = (
                    f"{context}:{qualified_path}.sequenced_after[{sequence_index}]"
                )
                predecessor = sequence["reference"]
                if predecessor == qualified_path:
                    raise ValidationProblem(f"{sequence_context} cannot be a self-edge")
                predecessor_row = qualified_references.get(predecessor)
                if predecessor_row is None:
                    raise ValidationProblem(
                        f"{sequence_context}.reference is unknown: {predecessor!r}"
                    )
                predecessor_owner, predecessor_path, predecessor_projection = (
                    predecessor_row
                )
                predecessor_types = predecessor_projection["reference_types"]
                predecessor_outputs = predecessor_projection["reference_outputs"]
                predecessor_roles = predecessor_projection["reference_roles"]
                assert isinstance(predecessor_types, dict)
                assert isinstance(predecessor_outputs, dict)
                assert isinstance(predecessor_roles, dict)
                if predecessor_types[predecessor_path] == "index":
                    raise ValidationProblem(
                        f"{sequence_context}.reference cannot be an index"
                    )
                required_output = sequence["required_output"]
                if required_output not in predecessor_outputs[predecessor_path]:
                    raise ValidationProblem(
                        f"{sequence_context}.required_output {required_output!r} "
                        "is not produced by the predecessor"
                    )
                carried_by = sequence["carried_by"]
                if not isinstance(carried_by, dict) or not carried_by:
                    raise ValidationProblem(
                        f"{sequence_context}.carried_by must be a non-empty "
                        "profile/selection-owner mapping"
                    )
                if set(carried_by) != set(expected_carriers):
                    raise ValidationProblem(
                        f"{sequence_context}.carried_by must declare exactly the "
                        "current analyzed Task and Review surfaces"
                    )
                for profile, owner_mapping in carried_by.items():
                    if profile not in expected_carriers:
                        raise ValidationProblem(
                            f"{sequence_context}.carried_by profile {profile!r} "
                            "has no current canonical carrier surface"
                        )
                    role_order = {
                        "analysis-agent": 0,
                        "task-agent": 1,
                        "review-agent": 2,
                    }
                    predecessor_role_set = predecessor_roles[predecessor_path]
                    forward_role_flow = (
                        profile in role_order
                        and any(
                            predecessor_role in role_order
                            and role_order[predecessor_role] <= role_order[profile]
                            for predecessor_role in predecessor_role_set
                        )
                    )
                    if (
                        profile not in reference_roles[path]
                        or not forward_role_flow
                    ):
                        raise ValidationProblem(
                            f"{sequence_context}.carried_by reverses or leaves the "
                            f"declared forward role flow for {profile}"
                        )
                    if not isinstance(owner_mapping, dict) or set(owner_mapping) != {
                        "engineering-brief"
                    }:
                        raise ValidationProblem(
                            f"{sequence_context}.carried_by supports only the "
                            "engineering-brief selection owner"
                        )
                    fields = owner_mapping["engineering-brief"]
                    if fields != expected_carriers[profile]["engineering-brief"]:
                        raise ValidationProblem(
                            f"{sequence_context}.carried_by fields are stale, "
                            "incomplete, unknown, or case-mismatched"
                        )
                    for field in fields:
                        field_error = _reference_context_carrier_field_error(field)
                        if field_error is not None:
                            raise ValidationProblem(
                                f"{sequence_context}.carried_by {field_error}"
                            )
                sequence_edges.add((predecessor, qualified_path))
                sequence_count += 1
            for co_trigger in rule["must_co_trigger_with"]:
                if co_trigger == qualified_path:
                    raise ValidationProblem(
                        f"{context}:{qualified_path} cannot co-trigger itself"
                    )
                peer_row = qualified_references.get(co_trigger)
                if peer_row is None:
                    raise ValidationProblem(
                        f"{context}:{qualified_path} co-trigger is unknown: "
                        f"{co_trigger!r}"
                    )
                peer_owner, peer_path, peer_projection = peer_row
                peer_declarations = peer_projection["declarations"]
                peer_rule = (
                    peer_declarations.get(peer_path)
                    if isinstance(peer_declarations, dict)
                    else None
                )
                if (
                    not isinstance(peer_rule, dict)
                    or qualified_path not in peer_rule["must_co_trigger_with"]
                ):
                    raise ValidationProblem(
                        f"{context}:{qualified_path} co-trigger with {co_trigger!r} "
                        "must be reciprocal"
                    )
                co_trigger_edges.add(frozenset((qualified_path, co_trigger)))

    sequence_pairs = {
        frozenset((predecessor, successor))
        for predecessor, successor in sequence_edges
    }
    overlap = sorted(
        (conflict_edges & sequence_pairs)
        | (conflict_edges & co_trigger_edges)
        | (sequence_pairs & co_trigger_edges),
        key=lambda edge: sorted(edge),
    )
    if overlap:
        raise ValidationProblem(
            f"{context}: conflict/sequence/co-trigger relations overlap: "
            f"{[sorted(edge) for edge in overlap]}"
        )

    successors: dict[str, set[str]] = {}
    indegree = {qualified: 0 for qualified in qualified_references}
    for predecessor, successor in sequence_edges:
        if successor not in successors.setdefault(predecessor, set()):
            successors[predecessor].add(successor)
            indegree[successor] += 1
    frontier = sorted(
        qualified for qualified, degree in indegree.items() if degree == 0
    )
    visited = 0
    while frontier:
        current = frontier.pop(0)
        visited += 1
        for successor in sorted(successors.get(current, set())):
            indegree[successor] -= 1
            if indegree[successor] == 0:
                frontier.append(successor)
                frontier.sort()
    if visited != len(qualified_references):
        raise ValidationProblem(f"{context}: Reference sequencing graph is cyclic")
    return {
        "contract": REFERENCE_CONTEXT_ADMISSIBILITY_CONTRACT,
        "owners": owners,
        "declared_reference_count": declared_count,
        "sequence_count": sequence_count,
        "carrier_fields": expected_carriers,
    }


def reference_context_admissibility_decisions(
    authority: object,
    *,
    references: Iterable[tuple[str, str]],
    path: str,
) -> dict[str, object]:
    """Decide one eval-only composition without matching task prose."""

    if (
        not isinstance(authority, dict)
        or authority.get("contract") != REFERENCE_CONTEXT_ADMISSIBILITY_CONTRACT
        or not isinstance(authority.get("owners"), dict)
    ):
        raise ValidationProblem("Reference context admissibility authority is invalid")
    paths = ROUTE_DECISION_MODEL["path_values"]
    if path not in paths:
        raise ValidationProblem(f"unknown composition path {path!r}")
    rows = list(references)
    if len(rows) != len(set(rows)):
        raise ValidationProblem("composition References must be unique")
    declarations: list[dict[str, object]] = []
    undeclared: list[tuple[str, str]] = []
    selected_by_owner: dict[str, set[str]] = {}
    for owner, reference_path in rows:
        owner_projection = authority["owners"].get(owner)
        if not isinstance(owner_projection, dict):
            raise ValidationProblem(
                f"composition names unknown Reference owner {owner!r}"
            )
        reference_types = owner_projection.get("reference_types")
        if (
            not isinstance(reference_types, dict)
            or reference_path not in reference_types
        ):
            raise ValidationProblem(
                f"composition names unknown Reference {owner}/{reference_path}"
            )
        selected_by_owner.setdefault(owner, set()).add(reference_path)
        owner_declarations = owner_projection.get("declarations")
        rule = (
            owner_declarations.get(reference_path)
            if isinstance(owner_declarations, dict)
            else None
        )
        if not isinstance(rule, dict):
            undeclared.append((owner, reference_path))
            continue
        declarations.append({"owner": owner, "path": reference_path})

    conflicts: list[dict[str, str]] = []
    for owner, selected in selected_by_owner.items():
        owner_projection = authority["owners"][owner]
        reference_types = owner_projection["reference_types"]
        owner_declarations = owner_projection["declarations"]
        for left, right in combinations(sorted(selected), 2):
            mode_conflict = (
                reference_types[left]
                == reference_types[right]
                == "mode-contract"
            )
            left_rule = owner_declarations.get(left, {})
            declared_conflict = right in left_rule.get("conflicts_with", [])
            if mode_conflict or declared_conflict:
                conflicts.append(
                    {
                        "owner": owner,
                        "left": left,
                        "right": right,
                        "basis": (
                            "mode-contract" if mode_conflict else "owner-declaration"
                        ),
                    }
                )
    return {
        "path": path,
        "reachable": not conflicts,
        "failure_id": (
            "context-reference-conflict"
            if conflicts
            else None
        ),
        "declarations": declarations,
        "undeclared_references": undeclared,
        "conflicts": conflicts,
    }


def reference_context_staged_plan(
    authority: object,
    *,
    references: Iterable[tuple[str, str]],
    path: str,
    profile: str,
    selection_owner: str,
    available_carrier_fields: object,
    receipt_replayed: bool,
    brief_current: bool,
    review_fresh: bool,
    requested_same_stage: object | None = None,
) -> dict[str, object]:
    """Project independent Reference stages from canonical v3 authority."""

    selected = list(references)
    decision = reference_context_admissibility_decisions(
        authority,
        references=selected,
        path=path,
    )
    if not decision["reachable"]:
        return {
            **decision,
            "profile": profile,
            "selection_owner": selection_owner,
            "stages": [],
            "selected_union": [],
            "loaded_union": [],
            "carried_predecessors": [],
            "required_output_receipts": [],
            "carrier_validated": False,
        }
    assert isinstance(authority, dict)
    owners = authority["owners"]
    assert isinstance(owners, dict)
    selected_set = set(selected)
    if profile not in {"analysis-agent", "task-agent", "review-agent"}:
        raise ValidationProblem(f"unknown staged Reference profile {profile!r}")
    if selection_owner not in {"main-control-agent", "engineering-brief"}:
        raise ValidationProblem(
            f"unknown staged Reference selection owner {selection_owner!r}"
        )

    def rule_for(reference: tuple[str, str]) -> dict[str, object] | None:
        owner, reference_path = reference
        owner_projection = owners.get(owner)
        if not isinstance(owner_projection, dict):
            return None
        declarations = owner_projection.get("declarations")
        rule = (
            declarations.get(reference_path)
            if isinstance(declarations, dict)
            else None
        )
        return rule if isinstance(rule, dict) else None

    def reference_from_qualified(qualified: object) -> tuple[str, str]:
        if not isinstance(qualified, str):
            raise ValidationProblem(
                f"staged Reference relation is malformed: {qualified!r}"
            )
        predecessor_owner, marker, predecessor_suffix = qualified.partition(
            "/references/"
        )
        if not marker or not predecessor_owner or not predecessor_suffix:
            raise ValidationProblem(
                f"staged Reference relation is malformed: {qualified!r}"
            )
        return predecessor_owner, f"references/{predecessor_suffix}"

    def failed(failure_id: str) -> dict[str, object]:
        return {
            **decision,
            "reachable": False,
            "failure_id": failure_id,
            "profile": profile,
            "selection_owner": selection_owner,
            "stages": [],
            "selected_union": [list(reference) for reference in selected],
            "loaded_union": [],
            "carried_predecessors": [],
            "required_output_receipts": [],
            "carrier_validated": False,
        }

    must_neighbors: dict[tuple[str, str], set[tuple[str, str]]] = {
        reference: set() for reference in selected
    }
    for reference in selected:
        rule = rule_for(reference)
        if rule is None:
            continue
        for qualified_peer in rule["must_co_trigger_with"]:
            peer = reference_from_qualified(qualified_peer)
            if peer not in selected_set:
                return failed("required-co-trigger-missing")
            must_neighbors[reference].add(peer)

    component_by_reference: dict[tuple[str, str], frozenset[tuple[str, str]]] = {}
    components: list[frozenset[tuple[str, str]]] = []
    remaining = set(selected)
    while remaining:
        root = min(remaining)
        pending = [root]
        component: set[tuple[str, str]] = set()
        while pending:
            current = pending.pop()
            if current in component:
                continue
            component.add(current)
            pending.extend(sorted(must_neighbors[current] - component, reverse=True))
        frozen_component = frozenset(component)
        components.append(frozen_component)
        for reference in component:
            component_by_reference[reference] = frozen_component
        remaining -= component

    if requested_same_stage is not None:
        if not isinstance(requested_same_stage, list):
            raise ValidationProblem("requested same-stage groups must be a list")
        requested_members: set[tuple[str, str]] = set()
        for raw_group in requested_same_stage:
            if not isinstance(raw_group, list) or not raw_group:
                raise ValidationProblem(
                    "requested same-stage groups must contain non-empty lists"
                )
            group: list[tuple[str, str]] = []
            for raw_reference in raw_group:
                if (
                    not isinstance(raw_reference, (list, tuple))
                    or len(raw_reference) != 2
                    or not all(isinstance(value, str) for value in raw_reference)
                ):
                    raise ValidationProblem(
                        "requested same-stage Reference must be an owner/path pair"
                    )
                reference = (raw_reference[0], raw_reference[1])
                if reference not in selected_set or reference in requested_members:
                    raise ValidationProblem(
                        "requested same-stage References must be unique selected items"
                    )
                requested_members.add(reference)
                group.append(reference)
            group_set = frozenset(group)
            if len(group_set) > 1 and component_by_reference[group[0]] != group_set:
                return failed("context-reference-simultaneity-unauthorized")

    sequence_edges: list[tuple[tuple[str, str], tuple[str, str]]] = []
    externally_carried: dict[
        tuple[str, str], set[tuple[str, str]]
    ] = {}
    for successor in selected:
        rule = rule_for(successor)
        if rule is None:
            continue
        for sequence in rule["sequenced_after"]:
            predecessor = reference_from_qualified(sequence["reference"])
            if predecessor in selected_set:
                sequence_edges.append((predecessor, successor))
            elif (
                profile in {"task-agent", "review-agent"}
                and selection_owner == "engineering-brief"
            ):
                externally_carried.setdefault(successor, set()).add(predecessor)

    sequencing_enabled = bool(sequence_edges or externally_carried)
    carrier_validated = False
    if sequencing_enabled:
        expected_fields = authority.get("carrier_fields", {}).get(profile, {}).get(
            selection_owner
        )
        carrier_validated = (
            isinstance(available_carrier_fields, list)
            and available_carrier_fields == expected_fields
            and receipt_replayed is True
            and brief_current is True
            and (profile != "review-agent" or review_fresh is True)
        )
        if not carrier_validated:
            return failed("context-reference-carrier-stale")

    component_successors: dict[
        frozenset[tuple[str, str]], set[frozenset[tuple[str, str]]]
    ] = {}
    component_predecessors: dict[
        frozenset[tuple[str, str]], set[tuple[str, str]]
    ] = {component: set() for component in components}
    indegree = {component: 0 for component in components}
    for predecessor, successor in sequence_edges:
        predecessor_component = component_by_reference[predecessor]
        successor_component = component_by_reference[successor]
        if predecessor_component == successor_component:
            return failed("context-reference-simultaneity-unauthorized")
        successors = component_successors.setdefault(predecessor_component, set())
        if successor_component not in successors:
            successors.add(successor_component)
            indegree[successor_component] += 1
        component_predecessors[successor_component].add(predecessor)
    for successor, predecessors in externally_carried.items():
        component_predecessors[component_by_reference[successor]].update(
            predecessors
        )
    frontier = sorted(
        (component for component, degree in indegree.items() if degree == 0),
        key=lambda component: tuple(sorted(component)),
    )
    ordered_components: list[frozenset[tuple[str, str]]] = []
    while frontier:
        component = frontier.pop(0)
        ordered_components.append(component)
        for successor_component in sorted(
            component_successors.get(component, set()),
            key=lambda item: tuple(sorted(item)),
        ):
            indegree[successor_component] -= 1
            if indegree[successor_component] == 0:
                frontier.append(successor_component)
                frontier.sort(key=lambda item: tuple(sorted(item)))
    if len(ordered_components) != len(components):
        raise ValidationProblem("staged Reference component graph is cyclic")

    required_output_receipts: list[dict[str, object]] = []
    for reference in sorted(selected):
        owner, reference_path = reference
        owner_projection = owners[owner]
        outputs = owner_projection["reference_outputs"][reference_path]
        required_output_receipts.append(
            {
                "reference": list(reference),
                "required_outputs": list(outputs),
            }
        )

    stages: list[dict[str, object]] = []
    carried_union: set[tuple[str, str]] = set()
    loaded_union: set[tuple[str, str]] = set()
    if not ordered_components:
        stages.append(
            {
                "stage": 0,
                "loaded_references": [],
                "carried_predecessors": [],
                "required_output_receipts": [],
            }
        )
    for stage_index, component in enumerate(ordered_components):
        loaded = sorted(component)
        carried = sorted(component_predecessors[component] - set(loaded))
        stage_receipts = [
            receipt
            for receipt in required_output_receipts
            if tuple(receipt["reference"]) in component
        ]
        loaded_union.update(loaded)
        carried_union.update(carried)
        stages.append(
            {
                "stage": stage_index,
                "loaded_references": [list(reference) for reference in loaded],
                "carried_predecessors": [list(reference) for reference in carried],
                "required_output_receipts": stage_receipts,
            }
        )
    if loaded_union != selected_set:
        raise ValidationProblem(
            "staged Reference plan dropped selected obligations"
        )
    return {
        **decision,
        "profile": profile,
        "selection_owner": selection_owner,
        "stages": stages,
        "selected_union": [list(reference) for reference in selected],
        "loaded_union": [list(reference) for reference in sorted(loaded_union)],
        "carried_predecessors": [
            list(reference) for reference in sorted(carried_union)
        ],
        "required_output_receipts": required_output_receipts,
        "carrier_validated": carrier_validated,
    }


def validate_main_execution(main_execution: object, *, route_contract=None) -> list[str]:
    """Validate the actual dispatch producer and task identity for routing fixtures."""
    model = ROUTE_DECISION_MODEL if route_contract is None else route_contract
    if not isinstance(main_execution, dict) or set(main_execution) != {"producer", "task_id"}:
        return ["Main assignment must contain producer and task_id"]
    errors = []
    if main_execution["producer"] != model["main_execution_producer"]:
        errors.append("Main assignment producer must be main-control-agent")
    if not _valid_current_task_id(main_execution["task_id"]):
        errors.append("Main assignment task_id must be non-empty and not unspecified")
    return errors


def validate_main_assignment(main_assignment: object, *, route_contract=None) -> list[str]:
    """The same small assignment identifies implementation, analysis and review."""
    return validate_main_execution(main_assignment, route_contract=route_contract)


def validate_route_decision(
    envelope: object,
    *,
    main_execution: object,
    routing_authority: object,
    accepted_analysis_task_id: str | None = None,
    contract: dict[str, object] | None = None,
) -> list[str]:
    """Validate one route projection without selecting a route or computing a level."""

    model = ROUTE_DECISION_MODEL if contract is None else contract
    errors: list[str] = []

    def exact_fields(
        value: object,
        expected: list[str],
        context: str,
    ) -> dict[str, object] | None:
        if not isinstance(value, dict):
            errors.append(f"{context} must be an object")
            return None
        if set(value) != set(expected):
            errors.append(
                f"{context} fields must be exactly {expected}, found {sorted(value)}"
            )
            return None
        return value

    def string_items(
        value: object,
        context: str,
        *,
        maximum: int | None = None,
        nonempty: bool = False,
    ) -> list[str] | None:
        if not isinstance(value, list) or any(
            not isinstance(item, str) or not item.strip() for item in value
        ):
            errors.append(f"{context} must be a list of non-empty strings")
            return None
        if nonempty and not value:
            errors.append(f"{context} must not be empty")
        if len(value) != len(set(value)):
            errors.append(f"{context} must not contain duplicate values")
        if maximum is not None and len(value) > maximum:
            errors.append(f"{context} must contain at most {maximum} values")
        return value

    def canonical_json_bytes(value: object, context: str) -> bytes | None:
        try:
            return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False, separators=(",", ":")).encode("utf-8")
        except (
            RecursionError,
            TypeError,
            ValueError,
            UnicodeError,
            OverflowError,
        ) as exc:
            errors.append(f"{context} must be canonical JSON: {exc}")
            return None

    envelope_object = exact_fields(
        envelope,
        model["envelope_fields"],
        "route decision envelope",
    )
    authority_object = exact_fields(
        routing_authority,
        [
            "primary_skills_by_profile",
            "review_skills",
            "layer3_candidates_by_primary",
        ],
        "routing authority",
    )
    if envelope_object is None or authority_object is None:
        return errors
    canonical_authority = professional_routing_authority()
    if authority_object != canonical_authority:
        errors.append(
            "routing authority must equal the current Professional registry projection"
        )
    authority_model = canonical_authority

    path = envelope_object["path"]
    if path not in model["path_values"]:
        errors.append(
            f"route decision envelope.path must be one of {model['path_values']}"
        )
    analysis_path = path == "analyzed"
    main_fields = (
        model["main_analysis_assignment_fields"]
        if analysis_path
        else model["main_execution_provenance_fields"]
    )
    main_context = (
        "main analysis assignment"
        if analysis_path
        else "main execution input"
    )
    main_object = exact_fields(main_execution, main_fields, main_context)
    if main_object is None:
        return errors

    result = exact_fields(
        envelope_object["route_result"],
        model["route_result_fields"],
        "route_result",
    )
    selection = exact_fields(
        envelope_object["selection_evidence"],
        model["selection_evidence_fields"],
        "selection_evidence",
    )
    provenance = (
        None
        if analysis_path
        else exact_fields(
            envelope_object["main_execution_provenance"],
            model["main_execution_provenance_fields"],
            "main execution provenance",
        )
    )
    if analysis_path and envelope_object["main_execution_provenance"] is not None:
        errors.append(
            "analyzed route main_execution_provenance must be null because "
            "Analysis assignment is supplied separately"
        )
    if result is None or selection is None or (not analysis_path and provenance is None):
        return errors

    primary_by_profile = authority_model["primary_skills_by_profile"]
    review_authority = set(authority_model["review_skills"])
    layer3_authority = authority_model["layer3_candidates_by_primary"]
    known_primary_authority = {
        skill
        for skills in primary_by_profile.values()
        for skill in skills
    }

    start_profile = result["start_profile"]
    valid_start_profile = (
        isinstance(start_profile, str)
        and start_profile in ROLE_CONTRACT_MODEL
        and start_profile != "main-control-agent"
    )
    if not valid_start_profile:
        errors.append("route_result.start_profile must be a known non-Main profile")
    if (
        isinstance(path, str)
        and valid_start_profile
        and start_profile not in model["path_start_profiles"].get(path, [])
    ):
        errors.append(
            "route decision path/start_profile must follow the Core path/profile "
            "contract"
        )
    primary_skill = result["primary_skill"]
    review_skill = result["review_skill"]
    valid_primary = isinstance(primary_skill, str) and primary_skill.strip()
    if valid_primary and re.search(r"\s+plus\s+", primary_skill, re.IGNORECASE):
        errors.append(
            "route_result.primary_skill must not use an A plus B cross-layer "
            "routing expression"
        )
    if not valid_primary or primary_skill not in known_primary_authority:
        errors.append(
            "route_result.primary_skill must name exactly one known professional "
            "Primary Professional Skill"
        )
    elif (
        valid_start_profile
        and primary_skill not in primary_by_profile.get(start_profile, [])
    ):
        errors.append(
            "route_result.primary_skill must belong to the start_profile primary "
            "authority"
        )
    valid_review = isinstance(review_skill, str) and review_skill.strip()
    if (start_profile == "review-agent" and (not valid_review or review_skill not in review_authority)) or (start_profile != "review-agent" and review_skill is not None):
        errors.append(
            "route_result.review_skill must name exactly one known professional "
            "Review Skill from review authority"
        )

    selected_layer3 = string_items(
        result["layer3_skills"],
        "route_result.layer3_skills",
        maximum=model["maximum_layer3_skills"],
    )
    allowed_layer3 = set(
        layer3_authority.get(primary_skill, [])
        if valid_primary
        else []
    )
    if selected_layer3 is not None:
        unknown_layer3 = sorted(set(selected_layer3) - allowed_layer3)
        if unknown_layer3:
            errors.append(
                "route_result.layer3_skills must contain only known candidates "
                f"for the selected primary Skill: {unknown_layer3}"
            )
        if valid_primary and valid_start_profile and not unknown_layer3:
            try:
                selector_authority = layer3_selector_authority(
                    load_yaml_file(
                        ROOT / "src" / "registry" / "foundation-skills.yaml"
                    ),
                    load_yaml_file(
                        ROOT / "src" / "registry" / "professional-skills.yaml"
                    ),
                    load_yaml_file(
                        ROOT / "src" / "registry" / "domain-skills.yaml"
                    ),
                    context="route decision typed Layer 3 authorization",
                )
                layer3_selector_runtime_projection(
                    selector_authority,
                    professional_skill=primary_skill,
                    profile=start_profile,
                    selection_owner="main-control-agent",
                    exact_layer3=selected_layer3,
                )
            except (OSError, ValidationProblem, ValueError) as exc:
                errors.append(
                    "route_result.layer3_skills must be Foundation or Domain "
                    "items authorized itemwise by the current Professional "
                    f"selector/profile/domain: {exc}"
                )

    if main_object["producer"] != model["main_execution_producer"]:
        errors.append(
            "main execution input producer must be main-control-agent"
        )
    if (
        not isinstance(main_object["task_id"], str)
        or not main_object["task_id"].strip()
    ):
        errors.append("main execution input task_id must be non-empty text")
    provenance_json = (
        None
        if analysis_path
        else canonical_json_bytes(
            provenance,
            "main execution provenance",
        )
    )
    main_json = canonical_json_bytes(
        main_object,
        "main execution input",
    )
    if (
        not analysis_path
        and provenance is not None
        and provenance_json is not None
        and main_json is not None
        and provenance_json != main_json
    ):
        errors.append(
            "main execution provenance must equal the supplied Main execution input"
        )
    raw_evidence = selection["task_evidence"]
    evidence_ids: set[str] = set()
    if not isinstance(raw_evidence, list) or not raw_evidence:
        errors.append("selection_evidence.task_evidence must be a non-empty list")
        raw_evidence = []
    for index, item in enumerate(raw_evidence):
        context = f"selection_evidence.task_evidence[{index}]"
        evidence = exact_fields(item, model["task_evidence_fields"], context)
        if evidence is None:
            continue
        evidence_id = evidence["id"]
        if (
            not isinstance(evidence_id, str)
            or CORE_ID_RE.fullmatch(evidence_id) is None
        ):
            errors.append(f"{context}.id must be a canonical identifier")
        elif evidence_id in evidence_ids:
            errors.append("selection_evidence task evidence ids must be unique")
        else:
            evidence_ids.add(evidence_id)
        if evidence["task_id"] != main_object["task_id"]:
            errors.append(
                f"{context}.task_id must bind task-local evidence to the Main task_id"
            )
        for field in ("kind", "task_id", "source_anchor"):
            if not isinstance(evidence[field], str) or not evidence[field].strip():
                errors.append(f"{context}.{field} must be non-empty text")

    def candidate_rows(
        field: str,
        known_skills: set[str],
        known_label: str,
        *,
        required: bool,
    ) -> list[dict[str, object]]:
        raw_rows = selection[field]
        if not isinstance(raw_rows, list) or (required and not raw_rows):
            qualifier = "non-empty " if required else ""
            errors.append(f"selection_evidence.{field} must be a {qualifier}list")
            return []
        rows: list[dict[str, object]] = []
        seen_skills: set[str] = set()
        for index, raw_row in enumerate(raw_rows):
            context = f"selection_evidence.{field}[{index}]"
            row = exact_fields(raw_row, model["candidate_fields"], context)
            if row is None:
                continue
            skill = row["skill"]
            valid_skill = isinstance(skill, str) and bool(skill.strip())
            if not valid_skill:
                errors.append(f"{context}.skill must be non-empty text")
            elif skill in seen_skills:
                errors.append(f"selection_evidence.{field} skills must be unique")
            else:
                seen_skills.add(skill)
            if valid_skill and skill not in known_skills:
                errors.append(f"{context}.skill must be a {known_label}")
            eligible = row["eligible"]
            if not isinstance(eligible, bool):
                errors.append(f"{context}.eligible must be boolean")
            row_evidence = string_items(
                row["evidence_ids"],
                f"{context}.evidence_ids",
                nonempty=True,
            )
            if row_evidence is not None:
                unknown_evidence = sorted(set(row_evidence) - evidence_ids)
                if unknown_evidence:
                    errors.append(
                        f"{context}.evidence_ids contain unknown task evidence "
                        f"{unknown_evidence}"
                    )
            rejection_reasons = string_items(
                row["rejection_reasons"],
                f"{context}.rejection_reasons",
            )
            if eligible is True and rejection_reasons:
                errors.append(
                    f"{context}.rejection_reasons must be empty when eligible"
                )
            if eligible is False and rejection_reasons == []:
                errors.append(
                    f"{context}.rejection_reasons must explain an ineligible candidate"
                )
            rows.append(row)
        return rows

    primary_rows = candidate_rows(
        "primary_candidates",
        known_primary_authority,
        "known professional Primary Professional Skill",
        required=True,
    )
    review_rows = candidate_rows(
        "review_candidates",
        review_authority,
        "known professional Review Skill from review authority",
        required=True,
    )
    layer3_rows = candidate_rows(
        "layer3_candidates",
        allowed_layer3,
        "known candidate for the selected primary Skill",
        required=False,
    )
    expected_primary_partition = set(
        primary_by_profile.get(start_profile, [])
        if valid_start_profile
        else []
    )
    expected_review_partition = set(review_authority)
    expected_layer3_partition = set(allowed_layer3)
    for field, rows, expected_partition in (
        ("primary_candidates", primary_rows, expected_primary_partition),
        ("review_candidates", review_rows, expected_review_partition),
        ("layer3_candidates", layer3_rows, expected_layer3_partition),
    ):
        actual_partition = {
            row["skill"]
            for row in rows
            if isinstance(row.get("skill"), str)
        }
        if actual_partition != expected_partition:
            errors.append(
                f"selection_evidence.{field} must be the exact full current "
                f"registry partition; missing {sorted(expected_partition - actual_partition)}, "
                f"extra {sorted(actual_partition - expected_partition)}"
            )

    eligible_primary = [
        row["skill"]
        for row in primary_rows
        if row.get("eligible") is True and isinstance(row.get("skill"), str)
    ]
    eligible_review = [
        row["skill"]
        for row in review_rows
        if row.get("eligible") is True and isinstance(row.get("skill"), str)
    ]
    eligible_layer3 = [
        row["skill"]
        for row in layer3_rows
        if row.get("eligible") is True and isinstance(row.get("skill"), str)
    ]
    if len(eligible_primary) != 1 or eligible_primary != [primary_skill]:
        errors.append(
            "route decision must have exactly one eligible primary candidate "
            "matching route_result.primary_skill"
        )
    if eligible_review != ([review_skill] if review_skill is not None else []):
        errors.append(
            "route decision must have exactly one eligible review candidate "
            "matching route_result.review_skill"
        )
    if selected_layer3 is not None and eligible_layer3 != selected_layer3:
        errors.append(
            "eligible Layer 3 candidates must exactly match "
            "route_result.layer3_skills"
        )

    declared_count = selection["eligible_primary_count"]
    computed_count = len(eligible_primary)
    if (
        not isinstance(declared_count, int)
        or isinstance(declared_count, bool)
        or declared_count != computed_count
    ):
        errors.append(
            "selection_evidence.eligible_primary_count must equal the eligible "
            f"primary candidate count {computed_count}"
        )
    route_once = envelope_object["route_once"]
    if not isinstance(route_once, bool):
        errors.append("route_once must be boolean")
    elif route_once != (computed_count == 1):
        errors.append(
            "route_once must be true exactly when eligible primary candidate "
            "count equals 1"
        )

    return errors


NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REFERENCE_CONTRACT_FIELDS = frozenset(
    REFERENCE_CONTRACT_MODEL["fields"]
)
REFERENCE_CONTRACT_TYPES = frozenset(
    REFERENCE_CONTRACT_MODEL["types"]
)
REFERENCE_CONTRACT_ROLES = frozenset(ROLE_CONTRACT_MODEL)
REFERENCE_OUTPUT_TYPES = frozenset(REFERENCE_CONTRACT_MODEL["outputs"])
REFERENCE_OUTPUTS_BY_TYPE = {
    key: frozenset(value)
    for key, value in REFERENCE_CONTRACT_MODEL["allowed_outputs_by_type"].items()
}
REFERENCE_MINIMUM_OUTPUTS_BY_TYPE = {
    key: frozenset(value)
    for key, value in REFERENCE_CONTRACT_MODEL["minimum_outputs_by_type"].items()
}
REFERENCE_LINE_BUDGET_KIND = {
    "decision-checklist": "targeted",
    "evidence-pattern": "targeted",
    "benchmark-pattern": "targeted",
    "targeted": "targeted",
    "mode-contract": "mode-contract",
    "template": None,
    "index": None,
}
_REFERENCE_CONDITION_GENERIC_RE = re.compile(
    r"^(?:(?:when|if) )?(?:needed|required|relevant|applicable)$"
    r"|^as needed$"
    r"|^(?:read|load|use )?(?:this )?(?:reference )?(?:only )?"
    r"(?:when |if )?(?:its )?subject changes (?:the )?current decision$",
    re.IGNORECASE,
)
_REFERENCE_ANCHOR_STOP_WORDS = {
    "accepted",
    "affected",
    "and",
    "artifacts",
    "behavior",
    "behaviors",
    "boundaries",
    "boundary",
    "change",
    "changes",
    "checklist",
    "claim",
    "claims",
    "constraints",
    "coverage",
    "current",
    "decision",
    "decisions",
    "design",
    "evidence",
    "extension",
    "failure",
    "failures",
    "index",
    "mechanism",
    "mechanisms",
    "negative",
    "owner",
    "path",
    "patterns",
    "proof",
    "reference",
    "references",
    "required",
    "risk",
    "risks",
    "root",
    "runtime",
    "selected",
    "skill",
    "source",
    "task",
    "tests",
    "triggered",
    "unresolved",
}
_REFERENCE_MECHANICAL_TRIPLET_RE = re.compile(
    r"^(?:patterns:\s+.+\s+leaves mechanism or failure-mode trade-offs"
    r"|checklist:\s+.+\s+needs boundary, failure, or negative-case coverage"
    r"|evidence:\s+.+\s+needs source, freshness, or negative-control proof)[.!]?$",
    re.IGNORECASE,
)
_REFERENCE_BROKEN_CONDITION_RES = (
    re.compile(r"\bdecision\s+is\s+or\b", re.IGNORECASE),
    re.compile(r"\bmissing\s+(?:leaves|needs)\b", re.IGNORECASE),
    re.compile(r"\band\s+(?:leaves|needs)\b", re.IGNORECASE),
    re.compile(r"^(?:(?:patterns|checklist|evidence):\s*)?or\b", re.IGNORECASE),
)
FRONTMATTER_DELIMITER = "---"
EXPECTED_PROFESSIONAL_SKILL_COUNT = 25
EXPECTED_CONTROL_SKILL_COUNT = 1
EXPECTED_FOUNDATION_CAPABILITY_COUNT = 150
EXPECTED_DOMAIN_EXTENSION_COUNT = 13
MARKETPLACE_SCHEMA_VERSION = 3
COMPILED_LAYER3_FORMAT = "ai-consumption-v1"
REGISTRY_SCHEMA_VERSIONS = {
    "control": 3,
    "professional": 5,
    "foundation": 8,
    "domain": 6,
}
PROFESSIONAL_ROUTING_MODES = frozenset(
    {"automatic", "evidence-only", "not-automatic"}
)
PROFESSIONAL_AUTOMATIC_ROUTING_FAMILIES = frozenset(
    {
        "backend",
        "data-middleware",
        "frontend",
        "installed-client",
        "integration",
        "logging",
        "platform-infrastructure",
        "test-validation",
        "repository-tooling",
    }
)
PROFESSIONAL_AUTOMATIC_ROUTING_POLICY = {
    "implementation_owner": {
        "accepted": {
            "path": "direct",
            "profile": "task-agent",
            "layer3": {
                "source": "task-evidence",
                "default": [],
                "max": 3,
            },
            "review": {
                "source": "selected-one-T2C-risk-or-default",
                "default": "ai-code-review-refactor",
            },
        },
        "conflict": {
            "path": "analyzed",
            "profile": "analysis-agent",
            "primary_skill": "engineering-change-analysis",
            "layer3_skills": ["repository-context-map"],
            "review_skill": "architecture-impact-reviewer",
            "reason": "implementation-owner-conflict",
        },
    }
}
DOMAIN_ROUTING_MODES = frozenset({"modifier-only"})
DOMAIN_MODIFIER_ONLY_ROUTING_MODE = "modifier-only"


def professional_automatic_routing_contract_errors(
    data: object,
    context: str = "professional-skills.yaml",
) -> list[str]:
    """Validate the typed registry authority for automatic implementation owners."""

    if not isinstance(data, dict):
        return [f"{context}: must be a mapping"]
    errors: list[str] = []
    if data.get("schema_version") != REGISTRY_SCHEMA_VERSIONS["professional"]:
        errors.append(
            f"{context}: schema_version must be exact int "
            f"{REGISTRY_SCHEMA_VERSIONS['professional']}"
        )
    if data.get("automatic_routing_policy") != (
        PROFESSIONAL_AUTOMATIC_ROUTING_POLICY
    ):
        errors.append(
            f"{context}: automatic_routing_policy must match the typed "
            "implementation-owner contract"
        )
    entries = data.get("professional_skills")
    if not isinstance(entries, list):
        errors.append(f"{context}:professional_skills must be a list")
        return errors
    mode_counts = {
        "automatic": 0,
        "evidence-only": 0,
        "not-automatic": 0,
    }
    family_owners: dict[str, str] = {}
    entries_by_name: dict[str, dict[str, Any]] = {}
    for index, entry in enumerate(entries):
        row_context = f"{context}:professional_skills[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{row_context}: must be a mapping")
            continue
        name = entry.get("name")
        if not isinstance(name, str) or NAME_RE.fullmatch(name) is None:
            errors.append(f"{row_context}.name must be an exact Skill id")
            name = ""
        elif name in entries_by_name:
            errors.append(f"{row_context}.name duplicates {name!r}")
        else:
            entries_by_name[name] = entry
        mode = entry.get("routing_mode")
        if mode not in PROFESSIONAL_ROUTING_MODES:
            errors.append(
                f"{row_context}.routing_mode must be one of "
                f"{sorted(PROFESSIONAL_ROUTING_MODES)}"
            )
            continue
        mode_counts[mode] += 1
        expected_task_routable = mode != "not-automatic"
        if entry.get("task_routable") is not expected_task_routable:
            errors.append(
                f"{row_context}.task_routable must be "
                f"{expected_task_routable!r} for {mode!r}"
            )
        family = entry.get("routing_family")
        if mode == "automatic":
            if family not in PROFESSIONAL_AUTOMATIC_ROUTING_FAMILIES:
                errors.append(
                    f"{row_context}.routing_family must be one of "
                    f"{sorted(PROFESSIONAL_AUTOMATIC_ROUTING_FAMILIES)}"
                )
            elif family in family_owners:
                errors.append(
                    f"{row_context}.routing_family duplicates {family!r}"
                )
            else:
                family_owners[family] = name
            roles = entry.get("role_support")
            if not isinstance(roles, list) or "task-agent" not in roles:
                errors.append(
                    f"{row_context}.role_support must include task-agent "
                    "for automatic routing"
                )
        elif "routing_family" in entry:
            errors.append(
                f"{row_context}.routing_family is allowed only for automatic rows"
            )
    expected_counts = {
        "automatic": 9,
        "evidence-only": 16,
        "not-automatic": 0,
    }
    if mode_counts != expected_counts:
        errors.append(
            f"{context}: routing_mode counts must be {expected_counts}, "
            f"found {mode_counts}"
        )
    if set(family_owners) != PROFESSIONAL_AUTOMATIC_ROUTING_FAMILIES:
        errors.append(
            f"{context}: automatic routing families must be exactly "
            f"{sorted(PROFESSIONAL_AUTOMATIC_ROUTING_FAMILIES)}"
        )
    policy = data.get("automatic_routing_policy")
    if policy == PROFESSIONAL_AUTOMATIC_ROUTING_POLICY:
        implementation = policy["implementation_owner"]
        accepted = implementation["accepted"]
        conflict = implementation["conflict"]
        named_roles = (
            (
                accepted["review"]["default"],
                "review-agent",
                "accepted.review.default",
            ),
            (
                conflict["primary_skill"],
                conflict["profile"],
                "conflict.primary_skill",
            ),
            (
                conflict["review_skill"],
                "review-agent",
                "conflict.review_skill",
            ),
        )
        for name, role, field in named_roles:
            entry = entries_by_name.get(name)
            roles = entry.get("role_support") if entry is not None else None
            if not isinstance(roles, list) or role not in roles:
                errors.append(
                    f"{context}: automatic_routing_policy.{field} must name "
                    f"a Professional Skill supporting {role}"
                )
        conflict_primary = entries_by_name.get(conflict["primary_skill"])
        allowed = (
            conflict_primary.get("layer3_candidates")
            if conflict_primary is not None
            else None
        )
        if not isinstance(allowed, list) or any(
            name not in allowed for name in conflict["layer3_skills"]
        ):
            errors.append(
                f"{context}: conflict.layer3_skills must be authorized by "
                "conflict.primary_skill"
            )
    return errors


def professional_automatic_routing_authority(
    data: object,
    context: str = "professional-skills.yaml",
) -> dict[str, Any]:
    """Return registry-derived implementation owners after strict validation."""

    errors = professional_automatic_routing_contract_errors(data, context)
    if errors:
        raise ValidationProblem("; ".join(errors))
    assert isinstance(data, dict)
    entries = data["professional_skills"]
    assert isinstance(entries, list)
    owners = {
        entry["routing_family"]: {
            "name": entry["name"],
            "layer3_candidates": list(entry["layer3_candidates"]),
        }
        for entry in entries
        if isinstance(entry, dict)
        and entry.get("routing_mode") == "automatic"
    }
    return {
        "owners_by_family": {
            family: owners[family]
            for family in sorted(owners)
        },
        "policy": data["automatic_routing_policy"],
    }


def professional_automatic_routing_policy_fingerprint(
    data: object,
    context: str = "professional-skills.yaml",
) -> str:
    """Return the stable digest of the validated automatic-routing policy."""

    professional_automatic_routing_authority(data, context)
    assert isinstance(data, dict)
    payload = json.dumps(
        data["automatic_routing_policy"],
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def domain_registry_contract_errors(
    data: object,
    context: str = "domain-skills.yaml",
) -> list[str]:
    """Validate the registry-owned Domain modifier membership contract."""

    if not isinstance(data, dict):
        return [f"{context}: must be a mapping"]
    errors: list[str] = []
    version = data.get("schema_version")
    if type(version) is not int or version != REGISTRY_SCHEMA_VERSIONS["domain"]:
        errors.append(
            f"{context}: schema_version must be exact int "
            f"{REGISTRY_SCHEMA_VERSIONS['domain']}"
        )
    entries = data.get("domain_skills")
    if not isinstance(entries, list):
        errors.append(f"{context}:domain_skills must be a list")
        return errors
    if len(entries) != 13:
        errors.append(
            f"{context}:domain_skills must contain exactly 13 rows, "
            f"found {len(entries)}"
        )
    seen: set[str] = set()
    for index, entry in enumerate(entries):
        row_context = f"{context}:domain_skills[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{row_context}: must be a mapping")
            continue
        name = entry.get("name")
        if not isinstance(name, str) or NAME_RE.fullmatch(name) is None:
            errors.append(f"{row_context}.name must be an exact Skill id")
            name = ""
        elif name in seen:
            errors.append(f"{row_context}.name duplicates {name!r}")
        else:
            seen.add(name)
        mode = entry.get("routing_mode")
        if mode not in DOMAIN_ROUTING_MODES:
            errors.append(
                f"{row_context}.routing_mode must be one of "
                f"{sorted(DOMAIN_ROUTING_MODES)}"
            )
        used_by = entry.get("used_by")
        if not isinstance(used_by, list) or not used_by:
            errors.append(f"{row_context}.used_by must be a non-empty list")
        elif any(
            not isinstance(owner, str) or NAME_RE.fullmatch(owner) is None
            for owner in used_by
        ):
            errors.append(
                f"{row_context}.used_by must contain exact Skill ids"
            )
        else:
            if len(used_by) != len(set(used_by)):
                errors.append(f"{row_context}.used_by must not contain duplicates")
            if used_by != sorted(used_by):
                errors.append(f"{row_context}.used_by must be sorted")
        roles = entry.get("role_support")
        if (
            not isinstance(roles, list)
            or not roles
            or any(
                role
                not in {"analysis-agent", "task-agent", "review-agent"}
                for role in roles
            )
            or len(roles) != len(set(roles))
        ):
            errors.append(
                f"{row_context}.role_support must contain unique supported "
                "Agent Profile ids"
            )
    return errors


def domain_modifier_routing_authority(
    domain_data: object,
    professional_data: object,
    *,
    domain_context: str = "domain-skills.yaml",
    professional_context: str = "professional-skills.yaml",
) -> dict[str, Any]:
    """Return reciprocal, role-compatible Domain modifier authority."""

    errors = domain_registry_contract_errors(domain_data, domain_context)
    if not isinstance(professional_data, dict):
        errors.append(f"{professional_context}: must be a mapping")
        professional_entries: object = None
    else:
        professional_entries = professional_data.get("professional_skills")
    if not isinstance(professional_entries, list):
        errors.append(
            f"{professional_context}:professional_skills must be a list"
        )
        professional_entries = []

    domains_by_name: dict[str, dict[str, Any]] = {}
    if isinstance(domain_data, dict):
        raw_domains = domain_data.get("domain_skills", [])
        if isinstance(raw_domains, list):
            domains_by_name = {
                str(entry.get("name")): entry
                for entry in raw_domains
                if isinstance(entry, dict)
                and isinstance(entry.get("name"), str)
            }
    professionals_by_name: dict[str, dict[str, Any]] = {}
    for index, entry in enumerate(professional_entries):
        row_context = (
            f"{professional_context}:professional_skills[{index}]"
        )
        if not isinstance(entry, dict):
            errors.append(f"{row_context}: must be a mapping")
            continue
        name = entry.get("name")
        if not isinstance(name, str) or NAME_RE.fullmatch(name) is None:
            errors.append(f"{row_context}.name must be an exact Skill id")
            continue
        if name in professionals_by_name:
            errors.append(f"{row_context}.name duplicates {name!r}")
            continue
        professionals_by_name[name] = entry

    declared_edges: set[tuple[str, str]] = set()
    for domain, entry in domains_by_name.items():
        owners = entry.get("used_by", [])
        if not isinstance(owners, list):
            continue
        domain_roles = entry.get("role_support", [])
        for owner in owners:
            if not isinstance(owner, str):
                continue
            declared_edges.add((owner, domain))
            professional = professionals_by_name.get(owner)
            if professional is None:
                errors.append(
                    f"{domain_context}:{domain}.used_by names unknown "
                    f"Professional Skill {owner!r}"
                )
                continue
            professional_roles = professional.get("role_support")
            if not isinstance(professional_roles, list) or not set(
                professional_roles
            ).issubset(set(domain_roles) if isinstance(domain_roles, list) else set()):
                errors.append(
                    f"{domain_context}:{domain} does not support every role "
                    f"declared by {owner}"
                )

    reciprocal_edges: set[tuple[str, str]] = set()
    domain_names = set(domains_by_name)
    for owner, professional in professionals_by_name.items():
        candidates = professional.get("layer3_candidates")
        if not isinstance(candidates, list):
            errors.append(
                f"{professional_context}:{owner}.layer3_candidates must be a list"
            )
            continue
        if len(candidates) != len(set(candidates)):
            errors.append(
                f"{professional_context}:{owner}.layer3_candidates must not "
                "contain duplicates"
            )
        reciprocal_edges.update(
            (owner, candidate)
            for candidate in candidates
            if candidate in domain_names
        )

    if declared_edges != reciprocal_edges:
        errors.append(
            "Domain modifier reciprocity differs; "
            f"domain-only={sorted(declared_edges - reciprocal_edges)}; "
            f"professional-only={sorted(reciprocal_edges - declared_edges)}"
        )
    if len(declared_edges) != 47:
        errors.append(
            "Domain modifier authority must contain exactly 47 reciprocal "
            f"edges, found {len(declared_edges)}"
        )
    analysis_domains = {
        domain
        for owner, domain in declared_edges
        if owner == "engineering-change-analysis"
    }
    if analysis_domains != domain_names:
        errors.append(
            "engineering-change-analysis must authorize every Domain modifier; "
            f"missing={sorted(domain_names - analysis_domains)}; "
            f"extra={sorted(analysis_domains - domain_names)}"
        )
    if errors:
        raise ValidationProblem("; ".join(errors))

    return {
        "domain_order": list(domains_by_name),
        "domains_by_name": domains_by_name,
        "domains_by_professional": {
            owner: [
                domain
                for domain in domains_by_name
                if (owner, domain) in declared_edges
            ]
            for owner in professionals_by_name
        },
        "edge_count": len(declared_edges),
    }


def domain_routing_mode_map(
    data: object,
    context: str = "domain-skills.yaml",
) -> dict[str, str]:
    """Return registry-authoritative Domain membership after strict validation."""

    errors = domain_registry_contract_errors(data, context)
    if errors:
        raise ValidationProblem("; ".join(errors))
    assert isinstance(data, dict)
    entries = data["domain_skills"]
    assert isinstance(entries, list)
    return {
        str(entry["name"]): str(entry["routing_mode"])
        for entry in entries
        if isinstance(entry, dict)
    }
EXPERTISE_TAG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SKILL_REFERENCE_ARCHITECTURE_TAG = "skill-reference-architecture"
SKILL_EXPERTISE_TAGS = frozenset(
    {
        "domain-ai-product-extension",
        "domain-bigdata-product-extension",
        "domain-iot-embedded-extension",
        "domain-low-level-systems-extension",
        "domain-android-platform-extension",
        "domain-cloud-platform-extension",
        "domain-cross-platform-client-extension",
        "domain-ios-ipados-platform-extension",
        "domain-linux-desktop-platform-extension",
        "domain-macos-platform-extension",
        "domain-windows-platform-extension",
        "domain-payment-trading-extension",
        "domain-web3-product-extension",
        "foundation-architecture-design",
        "foundation-backend-engineering",
        "foundation-cross-cutting-safety",
        "foundation-data-api-contracts",
        "foundation-data-middleware",
        "foundation-delivery-platform",
        "foundation-domain-engineering",
        "foundation-domain-modeling",
        "foundation-engineering-workflow",
        "foundation-experience-design",
        "foundation-frontend-engineering",
        "foundation-intake-requirements",
        "foundation-interface-contracts",
        "foundation-language-professional-usage",
        "foundation-quality-testing",
        "foundation-reliability-operations",
        "foundation-repository-intelligence",
        "foundation-security-privacy",
        "foundation-technology-selection",
        "specialty-concurrency-coordination",
        "specialty-identity-access-control",
        "specialty-lang-cpp",
        "specialty-lang-go",
        "specialty-lang-jvm",
        "specialty-lang-python",
        "specialty-lang-rust",
        "specialty-lang-shell-cli",
        "specialty-lang-sql",
        "specialty-lang-typescript",
        "specialty-messaging-event-delivery",
        "specialty-migration-compatibility",
        "specialty-transaction-consistency",
    }
)
FOUNDATION_DELIVERY_SCOPES = frozenset(
    {"product", "authoring-only", "dev-only"}
)
FOUNDATION_CONTENT_CLASSES = frozenset({"compact", "complex"})
FOUNDATION_CONTENT_BUDGETS = {
    "compact": {"target_words": 400, "hard_words": 500},
    "complex": {"target_words": 500, "hard_words": 600},
}
FOUNDATION_CONTENT_HARD_TOKENS = 900
LAYER_ROOT_CONTENT_BUDGET_SCOPE = (
    "governed-body-excluding-registry-targeted-references"
)
LAYER_ROOT_CONTENT_BUDGETS = {
    "professional-skill": {
        "target_words": 550,
        "hard_words": 650,
        "target_tokens": 850,
        "hard_tokens": 1000,
    },
    "domain-extension": {
        "target_words": 500,
        "hard_words": 600,
        "target_tokens": 800,
        "hard_tokens": 900,
    },
}
CONTENT_BUDGET_CLASSIFICATIONS = (
    "KEEP",
    "REVIEW_DENSITY",
    "TIGHTEN_BODY",
    "BLOCK",
)


def classify_content_budget(
    *,
    word_count: int,
    token_count: int,
    target_words: int,
    hard_words: int,
    target_tokens: int | None = None,
    hard_tokens: int | None = None,
) -> str:
    """Classify governed root content against one closed budget contract."""

    over_hard_words = word_count > hard_words
    over_hard_tokens = hard_tokens is not None and token_count > hard_tokens
    if over_hard_words or over_hard_tokens:
        return "BLOCK"

    utilization: list[float] = []
    if word_count > target_words:
        utilization.append(word_count / hard_words)
    if target_tokens is not None and token_count > target_tokens:
        if hard_tokens is None:
            raise ValidationProblem("token target requires a token hard limit")
        utilization.append(token_count / hard_tokens)
    if not utilization:
        return "KEEP"
    if max(utilization) > 0.9:
        return "TIGHTEN_BODY"
    return "REVIEW_DENSITY"
FOUNDATION_CONTENT_CLASS_RATIONALE_MIN_WORDS = 12
FOUNDATION_CONTENT_CLASS_RATIONALE_MARKERS = (
    "coupl",
    "interdepend",
    "cannot be separated",
    "cannot safely be separated",
    "must be decided together",
    "same evidence",
    "shared failure",
)
FOUNDATION_CONTENT_CLASS_GENERIC_RATIONALES = frozenset(
    {
        "complex content",
        "complex decisions",
        "needed for completeness",
        "too much content",
        "professionalism",
        "special case",
    }
)

# AI-facing prose remains concise across prompts, Profiles, Skill roots,
# References, and compiled Layer 3 projections.  The two lower thresholds are
# review bands; the hard limit is the blocking contract.
AI_SENTENCE_TARGET_WORDS = 24
AI_COMPLEX_SENTENCE_TARGET_WORDS = 32
AI_SENTENCE_HARD_WORDS = 40

_AI_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[-/][A-Za-z0-9]+)*")
_AI_SENTENCE_BOUNDARY_RE = re.compile(
    r"(?<=[.!?])\s+(?=[`*_\[(]*[A-Za-z0-9])"
)
_AI_SENTENCE_ABBREVIATIONS = frozenset(
    {
        "e.g.",
        "i.e.",
        "etc.",
        "vs.",
        "mr.",
        "mrs.",
        "ms.",
        "dr.",
        "prof.",
        "sr.",
        "jr.",
        "no.",
    }
)
_AI_FENCE_RE = re.compile(r"^\s*(```+|~~~+)")
_AI_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+")
_AI_LIST_ITEM_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?:[-*+]|\d+[.)])\s+(?P<text>\S.*)$"
)
_AI_INLINE_LINK_RE = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
_AI_INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
_AI_LEADING_DECISION_LABEL_RE = re.compile(
    r"^\s*\*\*[^*\n]+(?:[.:]\*\*|\*\*[.:])\s*"
)
TARGETED_REFERENCE_TABLE_COLUMNS = (
    "Path",
    "Type",
    "Load when",
    "Do not load when",
    "Required by",
    "Required output",
)
_REFERENCE_PATH_SLUG_PATTERN = r"[a-z0-9]+(?:-[a-z0-9]+)*"
_REFERENCE_PATH_PROJECTION_PATTERN = (
    rf"references/(?:{_REFERENCE_PATH_SLUG_PATTERN}/)*"
    rf"{_REFERENCE_PATH_SLUG_PATTERN}\.md"
)
_REFERENCE_PATH_PROJECTION_RE = re.compile(
    rf"^{_REFERENCE_PATH_PROJECTION_PATTERN}$"
)
_TARGETED_REFERENCE_TABLE_LINK_RE = re.compile(
    rf"^\[(?P<label>[a-z0-9]+(?: [a-z0-9]+)*)\]\("
    rf"(?P<path>{_REFERENCE_PATH_PROJECTION_PATTERN})\)$"
)
_AI_TARGETED_REFERENCE_METADATA_RE = re.compile(
    r"^(?:Load when|Do not load when|Required by|Required output):\s+(?P<body>.+)$"
)
_REFERENCE_CONDITION_RESERVED_DELIMITER_RE = re.compile(
    r";\s*(?:load|skip|required by|produces)\b",
    re.IGNORECASE,
)
_REFERENCE_CONDITION_MARKDOWN_CONTROL_RE = re.compile(r"[`\[\]()<>*_#|\\]")
_AI_STANDALONE_COMMAND_RE = re.compile(
    r"^(?:\$\s*)?(?:python\d*|git|rg|grep|find|sed|awk|bash|sh|zsh|"
    r"pytest|npm|pnpm|yarn|make|cargo|go|mvn|gradle|docker|kubectl|curl)\b",
    re.IGNORECASE,
)
_AI_HARD_OBLIGATION_RE = re.compile(
    r"\b(?:must(?:\s+(?:not|never))?|never|do\s+not|forbid)\b",
    re.IGNORECASE,
)
_AI_STOP_ACTION = r"stop(?!\s+(?:conditions?|boundaries|criteria|signals?|rules?)\b)"
_AI_DECISION_ACTIONS = (
    "ask",
    "bind",
    "branch",
    "choose",
    "classify",
    "compare",
    "create",
    "define",
    "derive",
    "edit",
    "eliminate",
    "enforce",
    "escalate",
    "evaluate",
    "handle",
    "identify",
    "implement",
    "include",
    "inspect",
    "load",
    "maintain",
    "map",
    "measure",
    "omit",
    "pass",
    "preserve",
    "protect",
    "prove",
    "reconcile",
    "record",
    "reject",
    "remove",
    "report",
    "require",
    "return",
    "review",
    "route",
    "run",
    "scale",
    "select",
    "send",
    "state",
    "stop",
    "test",
    "trace",
    "use",
    "validate",
    "verify",
    "write",
)
_AI_DECISION_ACTION_ALT = "|".join(
    _AI_STOP_ACTION
    if action == "stop"
    else r"state(?!-machine-modeling\b)"
    if action == "state"
    else action
    for action in _AI_DECISION_ACTIONS
)
_AI_EXECUTION_ACTION_ALT = (
    "create|derive|dispatch|edit|eliminate|evaluate|handle|include|"
    r"load(?!\s+failure\b)|maintain|implement|measure|"
    r"pass(?!\s+criteria\b)|protect|reconcile|remove|"
    r"return(?!\s+destination\b)|"
    r"review(?!\s+(?:owner|process)\b)|"
    r"route(?!\s+wiring\b)|run|"
    r"scale(?!-down\s+behavior\b)|select|send|"
    rf"{_AI_STOP_ACTION}|"
    r"test(?!\s+(?:coverage|evidence)\b|-(?:only-interface|portfolio)\b|/validation\b)|"
    r"trace(?!\s+propagation\b)|use|validate|verify|"
    r"write(?!\s+(?:query|access)\s+patterns?\b)"
)
_AI_LEADING_DECISION_ACTION_RE = re.compile(
    rf"^(?:when\b[^,]*,\s*|if\b[^,]*,\s*)?"
    rf"(?P<action>{_AI_DECISION_ACTION_ALT})\b",
    re.IGNORECASE,
)
_AI_LOGICAL_CLAUSE_SPLIT_RE = re.compile(
    rf";+|\band\s+(?=(?:(?:{_AI_EXECUTION_ACTION_ALT})\b|"
    r"must(?:\s+(?:not|never))?\b|never\b|do\s+not\b|forbid\b))",
    re.IGNORECASE,
)
_AI_CANDIDATE_MENU_RE = re.compile(
    r"\b(?:candidate\s+(?:controls?|mechanisms?|options?|sources?|implementations?)\s+"
    r"include|(?:controls?|mechanisms?|options?|sources?|implementations?)\s+are\s+"
    r"candidates?|candidates?\s+(?:include|are|selected|depend))\b",
    re.IGNORECASE,
)
_AI_CANDIDATE_SELECTION_RE = re.compile(
    r"\b(?:depend(?:s)?\s+on|fit\s+depends|selected\s+from|selected\s+by|"
    r"chosen\s+from|chosen\s+by|derived\s+from)\b",
    re.IGNORECASE,
)
_AI_APPLICABILITY_EXCEPTION_RE = re.compile(
    r"\b(?:not\s+every|no\s+(?:one|single)|does\s+not\s+"
    r"(?:apply|inherit|require)|only\s+(?:when|if|for)|where\s+applicable|"
    r"except(?:\s+when)?|unless|unrelated\b.{0,80}\bout\s+of\s+scope)\b",
    re.IGNORECASE,
)
_TARGETED_REFERENCES_SECTION_RE = re.compile(
    r"(?ms)^## Targeted References[ \t]*\n.*?(?=^## |\Z)"
)
FOUNDATION_REGISTRY_BASE_FIELDS = frozenset(
    {
        "name",
        "path",
        "required_expertise_tags",
        "content_class",
        "role_support",
        "trigger_signals",
        "anti_trigger_signals",
        "required_inputs",
        "output_contract",
        "escalation_signals",
        "reference_index",
        "used_by",
        "group",
        "delivery_scope",
    }
)
_FOUNDATION_ACTIVATION_REQUIRED_FIELDS = frozenset(
    {
        "contract",
        "id",
        "mode",
        "path",
        "profile",
        "primary_skill",
        "review_skill",
        "semantic_atoms",
        "matcher_evidence",
        "negative_families",
    }
)
_FOUNDATION_ACTIVATION_FIELDS = frozenset(
    {
        *_FOUNDATION_ACTIVATION_REQUIRED_FIELDS,
        "runtime_matcher",
    }
)
_FOUNDATION_ACTIVATION_CONTRACT = "foundation-activation/v1"
_FOUNDATION_RUNTIME_MATCHER_FIELDS = (
    "contract",
    "rollout",
    "action",
    "combine",
    "predicates",
)
_FOUNDATION_RUNTIME_MATCHER_PREDICATE_FIELDS = (
    "atom",
    "operator",
    "scope",
    "polarity",
    "action",
    "term_groups",
)
_FOUNDATION_RUNTIME_MATCHER_CONTRACT = "foundation-semantic-matcher/v1"
_FOUNDATION_OCCURRENCE_MATCHER_FIELDS = (
    "contract",
    "rollout",
    "action",
    "combine",
    "relations",
)
_FOUNDATION_OCCURRENCE_RELATION_FIELDS = (
    "atom",
    "operator",
    "scope",
    "actions",
    "objects",
    "owner_relation",
    "non_owner_modifiers",
)
_FOUNDATION_OCCURRENCE_OWNER_RELATION_FIELDS = (
    "mode",
    "qualifiers",
)
_FOUNDATION_OCCURRENCE_MATCHER_CONTRACT = (
    "foundation-occurrence-matcher/v1"
)
_FOUNDATION_OCCURRENCE_RELATION_CONTRACTS = {
    "business-rule-occurrence": {
        "actions": ("analyze", "analyse", "extract"),
        "objects": (
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
        ),
        "owner_mode": "intrinsic-qualified-object",
        "modifiers": ("accepted", "current", "existing", "material"),
    },
    "state-machine-occurrence": {
        "actions": ("analyze", "analyse", "model"),
        "objects": (
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
        ),
        "owner_mode": "immediate-qualified-subject",
        "modifiers": (
            "accepted",
            "current",
            "existing",
            "material",
            "proposed",
            "target",
        ),
    },
}
_FOUNDATION_RUNTIME_MATCHER_TERM_RE = re.compile(
    r"^[a-z0-9]+(?: [a-z0-9]+)*$"
)
_FOUNDATION_ACTIVATION_MODE_CONTRACTS = {
    "explicit-analyzed": {
        "path": "analyzed",
        "profile": "analysis-agent",
        "negative_family": "analysis-authority-invalid",
    },
    "accepted-brief-review": {
        "path": "direct",
        "profile": "review-agent",
        "negative_family": "artifact-authority-invalid",
    },
}
_FOUNDATION_ACTIVATION_COMMON_NEGATIVE_FAMILIES = frozenset(
    {
        "lexical-near-miss",
        "explicit-anti-or-adjacent",
        "alternate-professional-owner",
    }
)
_FOUNDATION_ACTIVATION_KEBAB_RE = re.compile(
    r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
)
PROFESSIONAL_COVERAGE_STATES = (
    "registered",
    "route_covered",
    "negative_route_covered",
    "behavior_covered",
    "pressure_covered",
    "release_critical_covered",
)
PROFESSIONAL_COVERAGE_DECISION_KIND = "professional-coverage-gate"
EXPECTED_FOUNDATION_DELIVERY_SCOPE_COUNTS = {
    "product": 141,
    "authoring-only": 1,
    "dev-only": 8,
}
EXPECTED_RUNTIME_TOP_LEVEL_SKILL_COUNT = (
    EXPECTED_CONTROL_SKILL_COUNT + EXPECTED_PROFESSIONAL_SKILL_COUNT
)
EXPECTED_RUNTIME_DELIVERY_MODE_COUNTS = {
    "top_level_skill": EXPECTED_RUNTIME_TOP_LEVEL_SKILL_COUNT,
    "targeted_reference": 154,
    "routing_index_only": 9,
}

BANNED_BEGINNER_SECTIONS = (
    "Basic Usage",
    "Installation Tutorial",
    "Hello World",
    "Introduction",
    "What is",
    "Getting Started",
    "Quick Start",
    "Beginner Guide",
    "Syntax",
    "Framework Setup",
)

PERSONAL_ASSET_REFERENCES = (
    "folder.md",
    "personal notes",
    "local knowledge base",
    "toolbox",
    "user's asset library",
    "users asset library",
    "private documents",
)

SKILL_TEXT_QUALITY_SMELLS = (
    (re.compile(r"(?<![a-z])re owns\b", re.I), "re owns"),
    (re.compile(r",\s+re owns\b", re.I), ", re owns"),
    (re.compile(r"\bthis file's\b", re.I), "this file's"),
    (re.compile(r"\bthis skill's surface\b", re.I), "this skill's surface"),
    (re.compile(r"\bgeneric placeholder\b", re.I), "generic placeholder"),
)

class ValidationProblem(Exception):
    """Raised for malformed inputs that cannot be validated further."""


def foundation_content_budget(content_class: object) -> dict[str, int]:
    """Return the closed class-aware Foundation word budget."""

    if content_class not in FOUNDATION_CONTENT_BUDGETS:
        raise ValidationProblem(
            "Foundation content_class must be one of "
            f"{sorted(FOUNDATION_CONTENT_CLASSES)}, found {content_class!r}"
        )
    return dict(FOUNDATION_CONTENT_BUDGETS[str(content_class)])


def foundation_content_class_errors(
    entry: dict[str, Any],
    context: str,
) -> list[str]:
    """Validate explicit compact/complex classification and rationale ownership."""

    errors: list[str] = []
    content_class = entry.get("content_class")
    if content_class not in FOUNDATION_CONTENT_CLASSES:
        errors.append(
            f"{context}: content_class must be one of "
            f"{sorted(FOUNDATION_CONTENT_CLASSES)}, found {content_class!r}"
        )
        return errors

    has_rationale = "content_class_rationale" in entry
    rationale = entry.get("content_class_rationale")
    if content_class == "compact":
        if has_rationale:
            errors.append(
                f"{context}: compact content_class forbids content_class_rationale"
            )
        return errors

    if not isinstance(rationale, str) or not rationale.strip():
        errors.append(
            f"{context}: complex content_class requires a non-empty "
            "content_class_rationale"
        )
        return errors

    normalized = " ".join(rationale.casefold().split())
    if (
        normalized in FOUNDATION_CONTENT_CLASS_GENERIC_RATIONALES
        or len(re.findall(r"\b[\w/-]+\b", rationale))
        < FOUNDATION_CONTENT_CLASS_RATIONALE_MIN_WORDS
        or not any(marker in normalized for marker in FOUNDATION_CONTENT_CLASS_RATIONALE_MARKERS)
    ):
        errors.append(
            f"{context}: content_class_rationale must name the concrete coupled "
            "decisions and why they cannot safely be governed as a compact card"
        )
    return errors


def _ordered_closed_mapping_errors(
    value: object,
    context: str,
    required_fields: tuple[str, ...],
) -> list[str]:
    """Validate one ordered, closed mapping without short-circuiting diagnostics."""

    if not isinstance(value, dict):
        return [f"{context} must be a mapping"]

    errors: list[str] = []
    actual_fields = list(value)
    actual_field_set = set(actual_fields)
    required_field_set = set(required_fields)
    for field in required_fields:
        if field not in actual_field_set:
            errors.append(f"{context}.{field} is required")
    unknown_fields = actual_field_set - required_field_set
    for field in sorted(
        unknown_fields,
        key=lambda item: (type(item).__qualname__, repr(item)),
    ):
        if isinstance(field, str):
            errors.append(f"{context}.{field} is unknown")
        else:
            errors.append(
                f"{context}[{field!r}] is unknown; mapping keys must be strings"
            )
    if (
        not (required_field_set - actual_field_set)
        and not unknown_fields
        and actual_fields != list(required_fields)
    ):
        errors.append(
            f"{context} field order must be exact {list(required_fields)!r}"
        )
    return errors


def _foundation_occurrence_closed_list_errors(
    value: object,
    context: str,
    expected: tuple[str, ...],
) -> list[str]:
    """Validate one ordered, normalized, closed occurrence vocabulary."""

    if not isinstance(value, list):
        return [f"{context} must be a non-empty list"]
    if not value:
        return [f"{context} must be a non-empty list"]

    errors: list[str] = []
    normalized_values: list[str] = []
    first_index: dict[str, int] = {}
    for index, item in enumerate(value):
        item_context = f"{context}[{index}]"
        if not isinstance(item, str):
            errors.append(f"{item_context} must be a string")
            continue
        normalized = " ".join(item.casefold().split())
        if (
            item != normalized
            or _FOUNDATION_RUNTIME_MATCHER_TERM_RE.fullmatch(item) is None
        ):
            errors.append(
                f"{item_context} must be normalized lowercase "
                "alphanumeric terms separated by single spaces"
            )
        if normalized in first_index:
            errors.append(
                f"{item_context} duplicates normalized value at index "
                f"{first_index[normalized]}"
            )
        else:
            first_index[normalized] = index
        normalized_values.append(normalized)

    if normalized_values != list(expected):
        errors.append(
            f"{context} must use the exact closed vocabulary and order "
            f"{list(expected)!r}"
        )
    return errors


def _foundation_occurrence_matcher_errors(
    value: object,
    semantic_atoms: object,
    context: str,
) -> list[str]:
    """Validate one registry-owned governed-object occurrence matcher."""

    errors = _ordered_closed_mapping_errors(
        value,
        context,
        _FOUNDATION_OCCURRENCE_MATCHER_FIELDS,
    )
    if not isinstance(value, dict):
        return errors

    if (
        "contract" in value
        and value.get("contract") != _FOUNDATION_OCCURRENCE_MATCHER_CONTRACT
    ):
        errors.append(
            f"{context}.contract must be exact "
            f"{_FOUNDATION_OCCURRENCE_MATCHER_CONTRACT!r}"
        )
    if "rollout" in value and value.get("rollout") != "enabled":
        errors.append(f"{context}.rollout must be exact 'enabled'")
    if "action" in value and value.get("action") != "analysis-only":
        errors.append(f"{context}.action must be exact 'analysis-only'")
    if "combine" in value and value.get("combine") != "any":
        errors.append(f"{context}.combine must be exact 'any'")

    relations = value.get("relations")
    relations_context = f"{context}.relations"
    if not isinstance(relations, list):
        if "relations" in value:
            errors.append(f"{relations_context} must be a non-empty list")
        return errors
    if not relations:
        errors.append(f"{relations_context} must be a non-empty list")
        return errors

    expected_atoms = (
        list(semantic_atoms)
        if isinstance(semantic_atoms, list)
        and all(isinstance(atom, str) for atom in semantic_atoms)
        else []
    )
    observed_atoms: list[object] = []
    first_atom_index: dict[object, int] = {}
    for index, relation in enumerate(relations):
        relation_context = f"{relations_context}[{index}]"
        errors.extend(
            _ordered_closed_mapping_errors(
                relation,
                relation_context,
                _FOUNDATION_OCCURRENCE_RELATION_FIELDS,
            )
        )
        if not isinstance(relation, dict):
            continue

        atom = relation.get("atom")
        observed_atoms.append(atom)
        relation_contract = (
            _FOUNDATION_OCCURRENCE_RELATION_CONTRACTS.get(atom)
            if isinstance(atom, str)
            else None
        )
        if "atom" in relation:
            if not isinstance(atom, str):
                errors.append(f"{relation_context}.atom must be a string")
            else:
                if atom in first_atom_index:
                    errors.append(
                        f"{relation_context}.atom duplicates relation "
                        f"{first_atom_index[atom]} atom {atom!r}"
                    )
                else:
                    first_atom_index[atom] = index
                if index >= len(expected_atoms):
                    errors.append(
                        f"{relation_context}.atom is an extra semantic atom "
                        f"{atom!r}"
                    )
                elif atom != expected_atoms[index]:
                    errors.append(
                        f"{relation_context}.atom must follow semantic_atoms "
                        f"order with exact value {expected_atoms[index]!r}"
                    )
                if relation_contract is None:
                    errors.append(
                        f"{relation_context}.atom is not a supported "
                        f"occurrence relation: {atom!r}"
                    )

        if (
            "operator" in relation
            and relation.get("operator") != "governed-object-occurrence"
        ):
            errors.append(
                f"{relation_context}.operator must be exact "
                "'governed-object-occurrence'"
            )
        if (
            "scope" in relation
            and relation.get("scope") != "bounded-clause"
        ):
            errors.append(
                f"{relation_context}.scope must be exact 'bounded-clause'"
            )

        if relation_contract is not None:
            for field in ("actions", "objects"):
                if field in relation:
                    errors.extend(
                        _foundation_occurrence_closed_list_errors(
                            relation.get(field),
                            f"{relation_context}.{field}",
                            relation_contract[field],
                        )
                    )

        owner = relation.get("owner_relation")
        owner_context = f"{relation_context}.owner_relation"
        errors.extend(
            _ordered_closed_mapping_errors(
                owner,
                owner_context,
                _FOUNDATION_OCCURRENCE_OWNER_RELATION_FIELDS,
            )
        )
        if isinstance(owner, dict) and relation_contract is not None:
            if (
                "mode" in owner
                and owner.get("mode") != relation_contract["owner_mode"]
            ):
                errors.append(
                    f"{owner_context}.mode must be exact "
                    f"{relation_contract['owner_mode']!r}"
                )
            if "qualifiers" in owner:
                errors.extend(
                    _foundation_occurrence_closed_list_errors(
                        owner.get("qualifiers"),
                        f"{owner_context}.qualifiers",
                        ("business", "domain"),
                    )
                )

        if (
            relation_contract is not None
            and "non_owner_modifiers" in relation
        ):
            errors.extend(
                _foundation_occurrence_closed_list_errors(
                    relation.get("non_owner_modifiers"),
                    f"{relation_context}.non_owner_modifiers",
                    relation_contract["modifiers"],
                )
            )

    observed_atom_strings = [
        atom
        for atom in observed_atoms
        if isinstance(atom, str)
    ]
    for atom in expected_atoms:
        if atom not in observed_atom_strings:
            errors.append(
                f"{relations_context} is missing semantic atom {atom!r}"
            )
    return errors


def _foundation_runtime_matcher_errors(
    value: object,
    semantic_atoms: object,
    context: str,
) -> list[str]:
    """Validate one registry-declared generic semantic matcher contract."""

    if (
        isinstance(value, dict)
        and (
            "relations" in value
            or value.get("contract")
            == _FOUNDATION_OCCURRENCE_MATCHER_CONTRACT
        )
    ):
        return _foundation_occurrence_matcher_errors(
            value,
            semantic_atoms,
            context,
        )

    errors = _ordered_closed_mapping_errors(
        value,
        context,
        _FOUNDATION_RUNTIME_MATCHER_FIELDS,
    )
    if not isinstance(value, dict):
        return errors

    if (
        "contract" in value
        and value.get("contract") != _FOUNDATION_RUNTIME_MATCHER_CONTRACT
    ):
        errors.append(
            f"{context}.contract must be exact "
            f"{_FOUNDATION_RUNTIME_MATCHER_CONTRACT!r}"
        )
    if "rollout" in value and value.get("rollout") != "enabled":
        errors.append(f"{context}.rollout must be exact 'enabled'")
    if "action" in value and value.get("action") != "analysis-only":
        errors.append(f"{context}.action must be exact 'analysis-only'")
    if "combine" in value and value.get("combine") != "all":
        errors.append(f"{context}.combine must be exact 'all'")

    predicates = value.get("predicates")
    predicates_context = f"{context}.predicates"
    if not isinstance(predicates, list):
        if "predicates" in value:
            errors.append(f"{predicates_context} must be a non-empty list")
        return errors
    if not predicates:
        errors.append(f"{predicates_context} must be a non-empty list")
        return errors

    expected_atoms = (
        list(semantic_atoms)
        if isinstance(semantic_atoms, list)
        and all(isinstance(atom, str) for atom in semantic_atoms)
        else []
    )
    observed_atoms: list[object] = []
    first_atom_index: dict[object, int] = {}
    for index, predicate in enumerate(predicates):
        predicate_context = f"{predicates_context}[{index}]"
        errors.extend(
            _ordered_closed_mapping_errors(
                predicate,
                predicate_context,
                _FOUNDATION_RUNTIME_MATCHER_PREDICATE_FIELDS,
            )
        )
        if not isinstance(predicate, dict):
            continue

        atom = predicate.get("atom")
        observed_atoms.append(atom)
        if "atom" in predicate:
            if not isinstance(atom, str):
                errors.append(f"{predicate_context}.atom must be a string")
            else:
                if atom in first_atom_index:
                    errors.append(
                        f"{predicate_context}.atom duplicates predicate "
                        f"{first_atom_index[atom]} atom {atom!r}"
                    )
                else:
                    first_atom_index[atom] = index
                if index >= len(expected_atoms):
                    errors.append(
                        f"{predicate_context}.atom is an extra semantic atom "
                        f"{atom!r}"
                    )
                elif atom != expected_atoms[index]:
                    errors.append(
                        f"{predicate_context}.atom must follow semantic_atoms "
                        f"order with exact value {expected_atoms[index]!r}"
                    )

        if (
            "operator" in predicate
            and predicate.get("operator") != "all-term-groups"
        ):
            errors.append(
                f"{predicate_context}.operator must be exact 'all-term-groups'"
            )
        if "scope" in predicate and predicate.get("scope") != "bounded-clause":
            errors.append(
                f"{predicate_context}.scope must be exact 'bounded-clause'"
            )
        if "polarity" in predicate:
            polarity = predicate.get("polarity")
            if (
                not isinstance(polarity, str)
                or polarity not in ("present", "absent")
            ):
                errors.append(
                    f"{predicate_context}.polarity must be one of "
                    "['absent', 'present']"
                )
        if "action" in predicate:
            predicate_action = predicate.get("action")
            if (
                not isinstance(predicate_action, str)
                or predicate_action not in ("none", "selection")
            ):
                errors.append(
                    f"{predicate_context}.action must be one of "
                    "['none', 'selection']"
                )

        term_groups = predicate.get("term_groups")
        term_groups_context = f"{predicate_context}.term_groups"
        if not isinstance(term_groups, list):
            if "term_groups" in predicate:
                errors.append(
                    f"{term_groups_context} must be a non-empty list"
                )
            continue
        if not term_groups:
            errors.append(f"{term_groups_context} must be a non-empty list")
            continue

        normalized_groups: dict[tuple[str, ...], int] = {}
        for group_index, group in enumerate(term_groups):
            group_context = f"{term_groups_context}[{group_index}]"
            if not isinstance(group, list):
                errors.append(f"{group_context} must be a non-empty list")
                continue
            if not group:
                errors.append(f"{group_context} must be a non-empty list")
                continue

            normalized_terms: list[str] = []
            first_term_index: dict[str, int] = {}
            group_is_normalized = True
            for term_index, term in enumerate(group):
                term_context = f"{group_context}[{term_index}]"
                if not isinstance(term, str):
                    errors.append(f"{term_context} must be a string")
                    group_is_normalized = False
                    continue
                normalized = " ".join(term.casefold().split())
                if (
                    term != normalized
                    or _FOUNDATION_RUNTIME_MATCHER_TERM_RE.fullmatch(term)
                    is None
                ):
                    errors.append(
                        f"{term_context} must be normalized lowercase "
                        "alphanumeric terms separated by single spaces"
                    )
                    group_is_normalized = False
                if normalized in first_term_index:
                    errors.append(
                        f"{term_context} duplicates normalized term at index "
                        f"{first_term_index[normalized]}"
                    )
                else:
                    first_term_index[normalized] = term_index
                normalized_terms.append(normalized)

            normalized_group = tuple(normalized_terms)
            if group_is_normalized:
                if normalized_group in normalized_groups:
                    errors.append(
                        f"{group_context} duplicates normalized group at index "
                        f"{normalized_groups[normalized_group]}"
                    )
                else:
                    normalized_groups[normalized_group] = group_index

    observed_atom_strings = [
        atom
        for atom in observed_atoms
        if isinstance(atom, str)
    ]
    for atom in expected_atoms:
        if atom not in observed_atom_strings:
            errors.append(
                f"{predicates_context} is missing semantic atom {atom!r}"
            )
    return errors


def _foundation_activation_field_errors(
    entry: dict[str, Any],
    context: str,
) -> list[str]:
    """Validate one optional closed Foundation activation contract."""

    activation = entry.get("activation")
    if not isinstance(activation, dict):
        return [f"{context}: activation must be a mapping"]

    errors: list[str] = []
    actual_fields = set(activation)
    for field in sorted(
        _FOUNDATION_ACTIVATION_REQUIRED_FIELDS - actual_fields
    ):
        errors.append(f"{context}: activation.{field} is required")
    unknown_fields = actual_fields - _FOUNDATION_ACTIVATION_FIELDS
    for field in sorted(
        unknown_fields,
        key=lambda value: (type(value).__qualname__, repr(value)),
    ):
        if isinstance(field, str):
            errors.append(f"{context}: activation.{field} is unknown")
        else:
            errors.append(
                f"{context}: activation[{field!r}] is unknown; "
                "activation mapping keys must be strings"
            )

    if (
        "contract" in activation
        and activation.get("contract") != _FOUNDATION_ACTIVATION_CONTRACT
    ):
        errors.append(
            f"{context}: activation.contract must be exact "
            f"{_FOUNDATION_ACTIVATION_CONTRACT!r}"
        )

    if "id" in activation:
        name = entry.get("name")
        expected_id = (
            f"foundation-activation-{name}"
            if isinstance(name, str)
            else None
        )
        activation_id = activation.get("id")
        if (
            not isinstance(activation_id, str)
            or _FOUNDATION_ACTIVATION_KEBAB_RE.fullmatch(activation_id) is None
            or activation_id != expected_id
        ):
            errors.append(
                f"{context}: activation.id must be exact row-bound id "
                f"{expected_id!r}"
            )

    mode = activation.get("mode")
    mode_contract = (
        _FOUNDATION_ACTIVATION_MODE_CONTRACTS.get(mode)
        if isinstance(mode, str)
        else None
    )
    if "mode" in activation and mode_contract is None:
        errors.append(
            f"{context}: activation.mode must be one of "
            f"{sorted(_FOUNDATION_ACTIVATION_MODE_CONTRACTS)}"
        )
    if mode_contract is not None:
        for field in ("path", "profile"):
            if (
                field in activation
                and activation.get(field) != mode_contract[field]
            ):
                errors.append(
                    f"{context}: activation.{field} must be exact "
                    f"{mode_contract[field]!r} for mode {mode!r}"
                )

    for field in ("primary_skill", "review_skill"):
        if field not in activation:
            continue
        value = activation.get(field)
        if (
            not isinstance(value, str)
            or _FOUNDATION_ACTIVATION_KEBAB_RE.fullmatch(value) is None
        ):
            errors.append(
                f"{context}: activation.{field} must be a non-empty "
                "canonical Professional Skill name"
            )

    atom_sets: dict[str, set[str]] = {}
    foundation_name = entry.get("name")
    for field in ("semantic_atoms", "matcher_evidence"):
        if field not in activation:
            continue
        value = activation.get(field)
        if not isinstance(value, list) or not value:
            errors.append(
                f"{context}: activation.{field} must be a non-empty list"
            )
            continue
        atoms = [
            atom
            for atom in value
            if isinstance(atom, str)
            and _FOUNDATION_ACTIVATION_KEBAB_RE.fullmatch(atom) is not None
        ]
        if len(atoms) != len(value):
            errors.append(
                f"{context}: activation.{field} must contain only "
                "lowercase-kebab atoms"
            )
        if len(atoms) != len(set(atoms)):
            errors.append(
                f"{context}: activation.{field} must contain unique atoms"
            )
        if isinstance(foundation_name, str) and any(
            foundation_name in atom for atom in atoms
        ):
            errors.append(
                f"{context}: activation.{field} must not contain the "
                "Foundation row name"
            )
        atom_sets[field] = set(atoms)

    if (
        atom_sets.get("semantic_atoms", set())
        & atom_sets.get("matcher_evidence", set())
    ):
        errors.append(
            f"{context}: activation.matcher_evidence must be disjoint from "
            "activation.semantic_atoms"
        )

    if "negative_families" in activation:
        value = activation.get("negative_families")
        if not isinstance(value, list) or not value:
            errors.append(
                f"{context}: activation.negative_families must be a "
                "non-empty list"
            )
        else:
            families = [
                family
                for family in value
                if isinstance(family, str)
                and _FOUNDATION_ACTIVATION_KEBAB_RE.fullmatch(family)
                is not None
            ]
            if len(families) != len(value):
                errors.append(
                    f"{context}: activation.negative_families must contain "
                    "only lowercase-kebab values"
                )
            if len(families) != len(set(families)):
                errors.append(
                    f"{context}: activation.negative_families must contain "
                    "unique values"
                )
            if mode_contract is not None:
                expected_families = {
                    *_FOUNDATION_ACTIVATION_COMMON_NEGATIVE_FAMILIES,
                    str(mode_contract["negative_family"]),
                }
                if set(families) != expected_families:
                    errors.append(
                        f"{context}: activation.negative_families must be the "
                        f"exact mode-specific set {sorted(expected_families)}"
                    )
    if "runtime_matcher" in activation:
        errors.extend(
            _foundation_runtime_matcher_errors(
                activation.get("runtime_matcher"),
                activation.get("semantic_atoms"),
                f"{context}: activation.runtime_matcher",
            )
        )
    return errors


def foundation_registry_field_errors(
    entry: dict[str, Any],
    context: str,
) -> list[str]:
    """Enforce the closed schema-v8 field set for Foundation entries."""

    expected = set(FOUNDATION_REGISTRY_BASE_FIELDS)
    if entry.get("content_class") == "complex":
        expected.add("content_class_rationale")
    if "activation" in entry:
        expected.add("activation")
    if "context_admissibility" in entry:
        expected.add("context_admissibility")
    actual = set(entry)
    errors: list[str] = []
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing:
        errors.append(f"{context}: missing Foundation field(s): {', '.join(missing)}")
    if unknown:
        errors.append(f"{context}: unknown Foundation field(s): {', '.join(unknown)}")
    if "activation" in entry:
        errors.extend(_foundation_activation_field_errors(entry, context))
    return errors


def foundation_runtime_matcher_authority(
    data: object,
    context: str = "foundation-skills.yaml",
) -> list[dict[str, Any]]:
    """Validate schema-v8 metadata and project enabled matchers in registry order."""

    errors: list[str] = []
    if not isinstance(data, dict):
        raise ValidationProblem(f"{context}: registry must be a mapping")

    version = data.get("schema_version")
    if (
        type(version) is not int
        or version != REGISTRY_SCHEMA_VERSIONS["foundation"]
    ):
        errors.append(
            f"{context}: schema_version must be exact "
            f"{REGISTRY_SCHEMA_VERSIONS['foundation']}"
        )
    if data.get("kind") != "changeforge.foundation_skills":
        errors.append(
            f"{context}: kind must be exact 'changeforge.foundation_skills'"
        )
    rows = data.get("foundation_skills")
    if not isinstance(rows, list):
        errors.append(f"{context}: foundation_skills must be a list")
        rows = []

    projections: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(
                f"{context}:foundation_skills[{index}] must be a mapping"
            )
            continue
        name = row.get("name")
        row_context = (
            f"{context}:{name}"
            if isinstance(name, str) and name
            else f"{context}:foundation_skills[{index}]"
        )
        row_errors = foundation_registry_field_errors(row, row_context)
        errors.extend(row_errors)
        activation = row.get("activation")
        if (
            not row_errors
            and isinstance(activation, dict)
            and "runtime_matcher" in activation
        ):
            projections.append(
                {
                    "name": name,
                    "activation_id": activation["id"],
                    "path": activation["path"],
                    "profile": activation["profile"],
                    "primary_skill": activation["primary_skill"],
                    "review_skill": activation["review_skill"],
                    "semantic_atoms": copy.deepcopy(
                        activation["semantic_atoms"]
                    ),
                    "matcher_evidence": copy.deepcopy(
                        activation["matcher_evidence"]
                    ),
                    "runtime_matcher": copy.deepcopy(
                        activation["runtime_matcher"]
                    ),
                }
            )
    if errors:
        raise ValidationProblem("; ".join(errors))
    return projections


LAYER3_SELECTOR_AUTHORITY_CONTRACT = (
    "changeforge.layer3-selector-authority/v1"
)
LAYER3_SELECTOR_RUNTIME_CONTRACT = (
    "changeforge.layer3-selector-runtime/v1"
)
LAYER3_SELECTOR_CONTROL_CONTRACT = (
    "changeforge.layer3-selector-control/v1"
)
LAYER3_SELECTOR_NORMALIZED_CONTROL_CONTRACT = (
    "changeforge.layer3-selector-normalized-control/v1"
)
LAYER3_SELECTOR_DECISION_ENVELOPE_CONTRACT = (
    "changeforge.layer3-selector-decision-envelope/v1"
)
LAYER3_SELECTOR_DECISION_PARTITION_CONTRACT = (
    "changeforge.layer3-selector-decision-partition/v1"
)
LAYER3_SELECTOR_REFERENCE_RECORDS_CONTRACT = (
    "changeforge.layer3-selector-reference-records-partition/v1"
)
def _runtime_asset_semantic_sha256(document: dict[str, Any], hash_field: str) -> str:
    semantics = {key: value for key, value in document.items() if key != hash_field}
    return hashlib.sha256(
        json.dumps(
            semantics,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _runtime_asset_json_object(raw: object, label: str) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(raw, bytes):
        return None, f"{label} must be exact bytes"

    def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate key {key!r}")
            result[key] = value
        return result

    try:
        document = json.loads(raw.decode("utf-8"), object_pairs_hook=reject_duplicate_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return None, f"{label} is malformed JSON: {exc}"
    if not isinstance(document, dict):
        return None, f"{label} root must be an object"
    return document, None


def _runtime_asset_safe_path(path: object) -> bool:
    if not isinstance(path, str) or not path or "\\" in path or "//" in path:
        return False
    candidate = PurePosixPath(path)
    return (
        not candidate.is_absolute()
        and path not in {".", ".."}
        and not path.startswith("./")
        and ".." not in candidate.parts
        and candidate.as_posix() == path
    )


_RUNTIME_REFERENCE_FILE_RE = re.compile(r"[a-z0-9][a-z0-9.-]*\.md\Z")


def runtime_reference_record_errors(
    record: object,
    *,
    expected_professional_skill: str,
    context: str,
) -> list[str]:
    """Validate one Build-projected Runtime Reference record.

    Registry and selector authority deliberately remain source-relative.  This
    validator accepts only the single Professional-local ``path`` emitted by
    Build; it never derives a basename, owner-relative fragment, or alternate
    source path.
    """

    if not isinstance(record, dict) or set(record) != RUNTIME_REFERENCE_RECORD_FIELDS:
        return [
            f"{context} must contain exactly {sorted(RUNTIME_REFERENCE_RECORD_FIELDS)}"
        ]
    owner = record.get("owner_skill")
    layer = record.get("owner_layer")
    path = record.get("path")
    if not isinstance(owner, str) or NAME_RE.fullmatch(owner) is None:
        return [f"{context}.owner_skill must be one safe Skill id"]
    if layer not in {"professional", "foundation", "domain"}:
        return [f"{context}.owner_layer is invalid"]
    if not _runtime_asset_safe_path(path):
        return [f"{context}.path must be one safe normalized relative path"]
    assert isinstance(path, str)
    parts = PurePosixPath(path).parts
    if layer == "professional":
        expected_shape = (
            len(parts) == 2
            and parts[0] == "references"
            and _RUNTIME_REFERENCE_FILE_RE.fullmatch(parts[1]) is not None
            and owner == expected_professional_skill
        )
        if not expected_shape:
            return [
                f"{context}.path must be exact Professional Runtime form "
                "references/<file>.md"
            ]
    else:
        expected_shape = (
            len(parts) == 5
            and parts[:2] == ("references", "layer3")
            and parts[2] == owner
            and parts[3] == "references"
            and _RUNTIME_REFERENCE_FILE_RE.fullmatch(parts[4]) is not None
        )
        if not expected_shape:
            return [
                f"{context}.path must be exact compiled Layer 3 Runtime form "
                "references/layer3/<owner-skill>/references/<file>.md"
            ]
    return []


def runtime_reference_record_target(
    professional_root: Path,
    record: object,
    *,
    expected_professional_skill: str,
    context: str,
) -> Path:
    """Return ``professional_root / record.path`` after fail-closed checks.

    The returned spelling is the direct lexical join.  No resolved, searched,
    inferred, or fallback path is substituted for the record value.
    """

    errors = runtime_reference_record_errors(
        record,
        expected_professional_skill=expected_professional_skill,
        context=context,
    )
    if errors:
        raise ValidationProblem("; ".join(errors))
    assert isinstance(record, dict) and isinstance(record["path"], str)
    root = professional_root.absolute()
    if root.is_symlink() or not root.is_dir():
        raise ValidationProblem(f"{context}: Professional root must be a regular directory")
    relative = PurePosixPath(record["path"])
    target = root.joinpath(*relative.parts)
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValidationProblem(
            f"{context}.path escapes the current Professional root"
        ) from exc
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValidationProblem(f"{context}.path must not traverse a symlink")
    if not target.exists() or not target.is_file():
        raise ValidationProblem(f"{context}.path is a missing regular file")
    try:
        target.resolve(strict=True).relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise ValidationProblem(
            f"{context}.path escapes the current Professional root"
        ) from exc
    return target


def runtime_reference_record_tree_errors(
    professional_root: Path,
    *,
    expected_professional_skill: str,
) -> list[str]:
    """Verify every generated partition record against its exact local target."""

    errors: list[str] = []
    partition_root = (
        professional_root / "references" / "runtime" / "reference-records"
    )
    if partition_root.is_symlink() or not partition_root.is_dir():
        return ["Runtime Reference partition root is missing or symlinked"]
    try:
        entries = sorted(partition_root.iterdir())
    except OSError as exc:
        return [f"Runtime Reference partition root is unreadable: {exc}"]
    if not entries:
        return ["Runtime Reference partition root is empty"]
    for partition_path in entries:
        context = f"Runtime Reference partition {partition_path.name}"
        if (
            partition_path.is_symlink()
            or not partition_path.is_file()
            or partition_path.suffix != ".json"
        ):
            errors.append(f"{context} must be one regular JSON file")
            continue
        try:
            raw = partition_path.read_bytes()
        except OSError as exc:
            errors.append(f"{context} is unreadable: {exc}")
            continue
        partition, parse_error = _runtime_asset_json_object(raw, context)
        if parse_error is not None:
            errors.append(parse_error)
            continue
        assert partition is not None
        if (
            set(partition) != RUNTIME_REFERENCE_PARTITION_FIELDS
            or partition.get("contract") != LAYER3_SELECTOR_REFERENCE_RECORDS_CONTRACT
            or partition.get("professional_skill") != expected_professional_skill
            or partition.get("owner_skill") != partition_path.stem
            or not isinstance(partition.get("build"), str)
        ):
            errors.append(f"{context} fields or bindings are malformed")
            continue
        records = partition.get("reference_records")
        if not isinstance(records, list):
            errors.append(f"{context}.reference_records must be a list")
            continue
        canonical_records = (
            json.dumps(
                records,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
        if partition.get("records_sha256") != hashlib.sha256(
            canonical_records
        ).hexdigest():
            errors.append(f"{context}.records_sha256 is stale")
        for index, record in enumerate(records):
            record_context = f"{context}.reference_records[{index}]"
            try:
                runtime_reference_record_target(
                    professional_root,
                    record,
                    expected_professional_skill=expected_professional_skill,
                    context=record_context,
                )
            except ValidationProblem as exc:
                errors.append(str(exc))
    return errors


def runtime_asset_bundle_metadata_errors(
    integrity_manifest_bytes: object,
    delivery_assets: object,
    root_binding: object,
    *,
    expected_source_version: str,
    expected_authoritative_build_inputs_sha256: str,
    expected_professional_skill: str,
) -> list[str]:
    """Verify inline Runtime identity and complete non-Runtime closure bytes.

    This is the sole non-Runtime byte verifier contract. Runtime agents consume
    the already-loaded Professional entrypoint, logical selection receipt, and
    current fixed-path assets without reading manifests or computing digests.
    """

    errors: list[str] = []
    full_hash_re = re.compile(r"[0-9a-f]{64}")
    if not all(
        isinstance(value, str) and value
        for value in (expected_source_version, expected_professional_skill)
    ):
        return ["expected inline Runtime identity fields must be non-empty strings"]
    if (
        not isinstance(expected_authoritative_build_inputs_sha256, str)
        or full_hash_re.fullmatch(expected_authoritative_build_inputs_sha256) is None
    ):
        return ["expected authoritative build input SHA-256 must be lowercase hex"]
    expected_build_identity = runtime_asset_build_identity(
        expected_authoritative_build_inputs_sha256
    )

    manifest, manifest_error = _runtime_asset_json_object(
        integrity_manifest_bytes, "Runtime integrity manifest"
    )
    if manifest_error:
        errors.append(manifest_error)
    if manifest is None:
        return errors

    if set(manifest) != RUNTIME_ASSET_INTEGRITY_MANIFEST_FIELDS:
        errors.append("Runtime integrity manifest fields are not exact")
    if (
        manifest.get("contract") != RUNTIME_ASSET_INTEGRITY_MANIFEST_CONTRACT
        or manifest.get("schema_version") != 1
    ):
        errors.append("Runtime integrity manifest contract/schema is invalid")

    for field, expected in (
        ("runtime_version", expected_source_version),
        ("build_identity", expected_build_identity),
        ("professional_skill", expected_professional_skill),
    ):
        if manifest.get(field) != expected:
            errors.append(f"Runtime integrity manifest {field} mismatch")

    manifest_hash = manifest.get("integrity_manifest_sha256")
    if (
        not isinstance(manifest_hash, str)
        or full_hash_re.fullmatch(manifest_hash) is None
        or manifest_hash
        != _runtime_asset_semantic_sha256(
            manifest, "integrity_manifest_sha256"
        )
    ):
        errors.append("Runtime integrity manifest semantic hash is invalid")

    if (
        not isinstance(delivery_assets, dict)
        or any(
            not _runtime_asset_safe_path(path) or not isinstance(payload, bytes)
            for path, payload in delivery_assets.items()
        )
    ):
        errors.append("delivery assets must be safe relative paths mapped to bytes")
        delivery_assets = {}
    metadata_leaks = sorted(set(delivery_assets) & set(RUNTIME_ASSET_METADATA_EXCLUSIONS))
    if metadata_leaks:
        errors.append(
            "delivery assets must exclude the integrity metadata path: "
            f"{metadata_leaks}"
        )
    if "references/runtime/identity.json" in delivery_assets:
        errors.append("Runtime identity sidecar is forbidden")

    rows = manifest.get("assets")
    row_paths: list[str] = []
    if not isinstance(rows, list):
        errors.append("Runtime integrity manifest assets must be a list")
        rows = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != RUNTIME_ASSET_INTEGRITY_ROW_FIELDS:
            errors.append(f"Runtime integrity manifest asset row {index} fields are not exact")
            continue
        path = row.get("path")
        row_paths.append(path if isinstance(path, str) else "")
        if not _runtime_asset_safe_path(path):
            errors.append(f"Runtime integrity manifest asset row {index} path is unsafe")
            continue
        if path in RUNTIME_ASSET_METADATA_EXCLUSIONS:
            errors.append("Runtime integrity manifest must exclude its sole metadata file")
        kind = row.get("kind")
        digest = row.get("sha256")
        size = row.get("size")
        if not isinstance(kind, str) or not kind:
            errors.append(f"Runtime integrity manifest asset row {index} kind is invalid")
        if not isinstance(digest, str) or full_hash_re.fullmatch(digest) is None:
            errors.append(f"Runtime integrity manifest asset row {index} digest is invalid")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            errors.append(f"Runtime integrity manifest asset row {index} size is invalid")
        payload = delivery_assets.get(path)
        if payload is None:
            errors.append(f"Runtime integrity manifest asset {path!r} is missing")
        elif (
            hashlib.sha256(payload).hexdigest() != digest
            or len(payload) != size
        ):
            errors.append(f"Runtime integrity manifest asset {path!r} bytes mismatch")
    if row_paths != sorted(set(row_paths)):
        errors.append("Runtime integrity manifest assets must be unique and path-sorted")
    if set(row_paths) != set(delivery_assets):
        errors.append("Runtime integrity manifest inventory is incomplete or has extra assets")

    professional_bytes = delivery_assets.get("SKILL.md")
    expected_jit_line = (
        "JIT: `references/runtime/selector.json`; Runtime: "
        f"`{expected_source_version}/{expected_build_identity}`."
    )
    if not isinstance(professional_bytes, bytes):
        errors.append("Runtime Professional entrypoint is missing")
    else:
        try:
            professional_text = professional_bytes.decode("utf-8")
        except UnicodeDecodeError:
            errors.append("Runtime Professional entrypoint is not UTF-8")
        else:
            if professional_text.count(expected_jit_line) != 1:
                errors.append("Runtime Professional JIT version/build marker is missing or duplicated")
            if "references/runtime/identity.json" in professional_text:
                errors.append("Runtime Professional entrypoint retains identity sidecar lookup")
            frontmatter = professional_text.split("---", 2)
            expected_name = f"name: {expected_professional_skill}"
            if len(frontmatter) < 3 or expected_name not in frontmatter[1].splitlines():
                errors.append("Runtime Professional frontmatter name binding is invalid")

    selector_paths = sorted(
        path
        for path in delivery_assets
        if path == "references/runtime/selector.json"
        or path.startswith("references/runtime/selectors/")
        or path.startswith("references/runtime/reference-records/")
    )
    if "references/runtime/selector.json" not in selector_paths:
        errors.append("Runtime selector envelope/direct selector is missing")
    for path in selector_paths:
        selector, selector_error = _runtime_asset_json_object(
            delivery_assets[path], f"Runtime selector asset {path}"
        )
        if selector_error:
            errors.append(selector_error)
            continue
        assert selector is not None
        if selector.get("build") != expected_build_identity:
            errors.append(f"Runtime selector asset {path} build mismatch")
        if not path.startswith("references/runtime/reference-records/"):
            continue
        partition_context = f"Runtime Reference partition {path}"
        if (
            set(selector) != RUNTIME_REFERENCE_PARTITION_FIELDS
            or selector.get("contract")
            != LAYER3_SELECTOR_REFERENCE_RECORDS_CONTRACT
            or selector.get("professional_skill") != expected_professional_skill
            or selector.get("owner_skill") != PurePosixPath(path).stem
            or not isinstance(selector.get("authority_contract"), str)
            or not selector["authority_contract"]
        ):
            errors.append(f"{partition_context} fields or bindings are malformed")
            continue
        records = selector.get("reference_records")
        if not isinstance(records, list):
            errors.append(f"{partition_context}.reference_records must be a list")
            continue
        canonical_records = (
            json.dumps(
                records,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
        if selector.get("records_sha256") != hashlib.sha256(
            canonical_records
        ).hexdigest():
            errors.append(f"{partition_context}.records_sha256 is stale")
        for record_index, record in enumerate(records):
            record_context = (
                f"{partition_context}.reference_records[{record_index}]"
            )
            record_errors = runtime_reference_record_errors(
                record,
                expected_professional_skill=expected_professional_skill,
                context=record_context,
            )
            errors.extend(record_errors)
            if record_errors:
                continue
            assert isinstance(record, dict) and isinstance(record["path"], str)
            if record["path"] not in delivery_assets:
                errors.append(
                    f"{record_context}.path has no exact delivery target "
                    f"{record['path']!r}"
                )

    expected_layer3_marker = RUNTIME_ASSET_LAYER3_MARKER_TEMPLATE.replace(
        "<B>", expected_build_identity
    )
    for path, payload in sorted(delivery_assets.items()):
        candidate = PurePosixPath(path)
        if (
            len(candidate.parts) != 3
            or candidate.parts[:2] != ("references", "layer3")
            or candidate.suffix != ".md"
            or candidate.name == "index.md"
        ):
            continue
        try:
            first_line = payload.decode("utf-8").splitlines()[0]
        except (UnicodeDecodeError, IndexError):
            first_line = ""
        if first_line != expected_layer3_marker:
            errors.append(f"Runtime Layer 3 asset {path} build marker mismatch")

    if not isinstance(root_binding, dict) or set(root_binding) != RUNTIME_ASSET_ROOT_BINDING_FIELDS:
        errors.append("root Runtime metadata binding fields are not exact")
        root_binding = {}
    for field, expected in (
        ("runtime_version", expected_source_version),
        ("build_identity", expected_build_identity),
        ("professional_skill", expected_professional_skill),
        (
            "authoritative_build_inputs_sha256",
            expected_authoritative_build_inputs_sha256,
        ),
        ("build_identity_algorithm", RUNTIME_ASSET_BUILD_IDENTITY_ALGORITHM),
        ("inline_identity_contract", RUNTIME_ASSET_INLINE_IDENTITY_CONTRACT),
        ("inline_identity_version", RUNTIME_ASSET_INLINE_IDENTITY_VERSION),
    ):
        if root_binding.get(field) != expected:
            errors.append(f"root Runtime metadata binding {field} mismatch")
    root_full_digest = root_binding.get("authoritative_build_inputs_sha256")
    root_comparator = root_binding.get("build_identity")
    try:
        root_derived_comparator = runtime_asset_build_identity(root_full_digest)
        runtime_asset_build_identity_bytes(root_comparator)
    except ValueError:
        root_derived_comparator = None
    if root_comparator != root_derived_comparator:
        errors.append("root Runtime build identity is not the full digest 128-bit prefix")
    expected_manifest_full_hash = hashlib.sha256(integrity_manifest_bytes).hexdigest()
    if root_binding.get("integrity_manifest_path") != RUNTIME_ASSET_INTEGRITY_MANIFEST_PATH:
        errors.append("root Runtime metadata integrity manifest path mismatch")
    if (
        root_binding.get("integrity_manifest_full_bytes_sha256")
        != expected_manifest_full_hash
    ):
        errors.append("root Runtime metadata integrity manifest full-byte hash mismatch")
    return errors


_LAYER3_SELECTOR_SOURCE_KINDS = (
    "direct-static",
    "dynamic-helper-only",
    "runtime-matcher",
)
_LAYER3_SELECTOR_SOURCE_SYMBOLS = {
    "direct-static": {"_route_impl"},
    "dynamic-helper-only": {
        "_accessibility_behavior_requested",
        "_build_route_candidates",
        "_implementation_owner_layer3",
        "_review_risk_layer3",
    },
    "runtime-matcher": {"foundation_runtime_matcher_authority"},
}
_LAYER3_SELECTOR_FIELDS = {
    "selector_id",
    "selectable_layer3",
    "source",
    "positive_evidence",
    "owner_bindings",
    "route_bindings",
}
_LAYER3_SELECTOR_OWNER_FIELDS = {"primary_skill", "review_skill"}
_LAYER3_SELECTOR_ROUTE_FIELDS = {
    "candidate_id",
    "rule_id",
    "routing_family",
    "primary_skill",
    "review_skill",
}
_LAYER3_SELECTOR_ALIAS_FIELDS = {
    "candidate_id",
    "source_selector_ids",
    "primary_skill",
    "review_skill",
}


def layer3_selector_authority(
    foundation_data: object,
    professional_data: object,
    domain_data: object,
    *,
    context: str = "Layer 3 selector authority",
) -> dict[str, Any]:
    """Project the registry-owned selector records for Oracle and Runtime."""

    errors: list[str] = []
    if not isinstance(foundation_data, dict):
        raise ValidationProblem(f"{context}: Foundation registry must be a mapping")
    if not isinstance(professional_data, dict):
        raise ValidationProblem(f"{context}: Professional registry must be a mapping")
    if not isinstance(domain_data, dict):
        raise ValidationProblem(f"{context}: Domain registry must be a mapping")

    foundation_rows = foundation_data.get("foundation_skills")
    professional_rows = professional_data.get("professional_skills")
    if not isinstance(foundation_rows, list):
        errors.append(f"{context}: foundation_skills must be a list")
        foundation_rows = []
    if not isinstance(professional_rows, list):
        errors.append(f"{context}: professional_skills must be a list")
        professional_rows = []
    foundation_by_name = {
        row.get("name"): row
        for row in foundation_rows
        if isinstance(row, dict) and isinstance(row.get("name"), str)
    }
    professional_by_name = {
        row.get("name"): row
        for row in professional_rows
        if isinstance(row, dict) and isinstance(row.get("name"), str)
    }
    for index, row in enumerate(foundation_rows):
        if isinstance(row, dict):
            errors.extend(
                foundation_registry_field_errors(
                    row,
                    f"{context}:foundation_skills[{index}]",
                )
            )
    errors.extend(
        professional_automatic_routing_contract_errors(
            professional_data,
            f"{context}:professional",
        )
    )
    try:
        domain_authority = domain_modifier_routing_authority(
            domain_data,
            professional_data,
            domain_context=f"{context}:domain",
            professional_context=f"{context}:professional",
        )
    except ValidationProblem as exc:
        errors.append(str(exc))
        domain_authority = {"domains_by_professional": {}}

    raw_authority = foundation_data.get("selector_authority")
    expected_authority_fields = {
        "contract",
        "inventory",
        "selectors",
        "aliases",
        "alias_member_subsets",
    }
    if (
        not isinstance(raw_authority, dict)
        or set(raw_authority) != expected_authority_fields
    ):
        actual = sorted(raw_authority) if isinstance(raw_authority, dict) else []
        errors.append(
            f"{context}: selector_authority fields must be exactly "
            f"{sorted(expected_authority_fields)}, found {actual}"
        )
        raw_authority = {}
    if raw_authority.get("contract") != LAYER3_SELECTOR_AUTHORITY_CONTRACT:
        errors.append(
            f"{context}: selector_authority.contract must be exact "
            f"{LAYER3_SELECTOR_AUTHORITY_CONTRACT!r}"
        )

    raw_selectors = raw_authority.get("selectors")
    if not isinstance(raw_selectors, list) or not raw_selectors:
        errors.append(f"{context}: selector_authority.selectors must be non-empty")
        raw_selectors = []
    runtime_matchers = {
        row["activation_id"]: row
        for row in foundation_runtime_matcher_authority(
            foundation_data,
            context=f"{context}:runtime-matcher",
        )
    }
    seen_ids: set[str] = set()
    seen_layer3: set[str] = set()
    projected: list[dict[str, Any]] = []
    domains_by_professional = domain_authority.get(
        "domains_by_professional",
        {},
    )
    for index, raw_record in enumerate(raw_selectors):
        record_context = f"{context}:selectors[{index}]"
        if not isinstance(raw_record, dict) or set(raw_record) != _LAYER3_SELECTOR_FIELDS:
            actual = sorted(raw_record) if isinstance(raw_record, dict) else []
            errors.append(
                f"{record_context} fields must be exactly "
                f"{sorted(_LAYER3_SELECTOR_FIELDS)}, found {actual}"
            )
            continue
        selector_id = raw_record.get("selector_id")
        if (
            not isinstance(selector_id, str)
            or not selector_id
            or selector_id != selector_id.strip()
        ):
            errors.append(f"{record_context}.selector_id must be nonblank trimmed text")
            continue
        if selector_id in seen_ids:
            errors.append(f"{record_context}.selector_id duplicates {selector_id!r}")
        seen_ids.add(selector_id)

        selectable = raw_record.get("selectable_layer3")
        if (
            not isinstance(selectable, list)
            or not selectable
            or len(selectable) > 3
            or len(selectable) != len(set(selectable))
            or not all(isinstance(item, str) and item for item in selectable)
        ):
            errors.append(
                f"{record_context}.selectable_layer3 must be unique 1..3 Skill ids"
            )
            selectable = []
        duplicate_layer3 = sorted(set(selectable) & seen_layer3)
        if duplicate_layer3:
            errors.append(
                f"{record_context}.selectable_layer3 duplicates selector authority "
                f"for {duplicate_layer3}"
            )
        seen_layer3.update(selectable)
        rows = [foundation_by_name.get(item) for item in selectable]
        if any(
            not isinstance(row, dict) or row.get("delivery_scope") != "product"
            for row in rows
        ):
            errors.append(
                f"{record_context}.selectable_layer3 must name product Foundations"
            )
        valid_rows = [row for row in rows if isinstance(row, dict)]
        role_support = sorted(
            set.intersection(
                *(set(row.get("role_support", [])) for row in valid_rows)
            )
        ) if valid_rows else []
        nearest_negative = list(
            dict.fromkeys(
                signal
                for row in valid_rows
                for signal in row.get("anti_trigger_signals", [])
                if isinstance(signal, str) and signal
            )
        )
        if not role_support:
            errors.append(f"{record_context} has no common supported role")
        if not nearest_negative:
            errors.append(f"{record_context} has no nearest-negative evidence")

        source = raw_record.get("source")
        if not isinstance(source, dict) or set(source) != {"kind", "symbol"}:
            errors.append(f"{record_context}.source must contain kind and symbol")
            source = {}
        source_kind = source.get("kind")
        source_symbol = source.get("symbol")
        if (
            source_kind not in _LAYER3_SELECTOR_SOURCE_KINDS
            or source_symbol not in _LAYER3_SELECTOR_SOURCE_SYMBOLS.get(
                source_kind,
                set(),
            )
        ):
            errors.append(f"{record_context}.source is outside closed authority")
        if source_kind == "runtime-matcher":
            matcher = runtime_matchers.get(selector_id)
            if (
                matcher is None
                or selectable != [matcher.get("name")]
            ):
                errors.append(
                    f"{record_context} runtime matcher binding is not reciprocal"
                )

        positive = raw_record.get("positive_evidence")
        terminal = f"foundation-selector:{selector_id}"
        if (
            not isinstance(positive, list)
            or not positive
            or len(positive) != len(set(positive))
            or positive[-1] != terminal
            or positive.count(terminal) != 1
            or not all(isinstance(item, str) and item for item in positive)
        ):
            errors.append(
                f"{record_context}.positive_evidence must be unique and end in "
                f"{terminal!r}"
            )
            positive = []
        concrete_positive = [
            signal
            for signal in positive
            if not signal.startswith(
                ("foundation-selector:", "dynamic-helper:")
            )
            and signal not in _LAYER3_SELECTOR_SOURCE_SYMBOLS.get(
                source_kind,
                set(),
            )
        ]
        runtime_layer3_signals = {
            row["name"]: {
                "positive_signals": list(row.get("trigger_signals", [])),
                "nearest_negative_signals": list(
                    row.get("anti_trigger_signals", [])
                ),
            }
            for row in valid_rows
        }

        raw_bindings = raw_record.get("owner_bindings")
        if not isinstance(raw_bindings, list) or not raw_bindings:
            errors.append(f"{record_context}.owner_bindings must be non-empty")
            raw_bindings = []
        owner_pairs: set[tuple[str, str]] = set()
        bindings: list[dict[str, Any]] = []
        for binding_index, raw_binding in enumerate(raw_bindings):
            binding_context = f"{record_context}.owner_bindings[{binding_index}]"
            if (
                not isinstance(raw_binding, dict)
                or set(raw_binding) != _LAYER3_SELECTOR_OWNER_FIELDS
            ):
                errors.append(f"{binding_context} has invalid fields")
                continue
            primary = raw_binding.get("primary_skill")
            review = raw_binding.get("review_skill")
            pair = (primary, review)
            if pair in owner_pairs:
                errors.append(f"{binding_context} duplicates owner binding {pair!r}")
            owner_pairs.add(pair)
            primary_row = professional_by_name.get(primary)
            review_row = professional_by_name.get(review)
            if (
                not isinstance(primary_row, dict)
                or not isinstance(review_row, dict)
                or primary_row.get("task_routable") is not True
                or "review-agent" not in review_row.get("role_support", [])
                or not set(selectable).intersection(
                    primary_row.get("layer3_candidates", [])
                )
            ):
                errors.append(f"{binding_context} is not reciprocal")
                binding_roles: list[str] = []
            else:
                binding_roles = [
                    role
                    for role in role_support
                    if role in primary_row.get("role_support", [])
                ]
                if not binding_roles:
                    errors.append(f"{binding_context} has no supported owner role")
            bindings.append(
                {
                    "primary_skill": primary,
                    "review_skill": review,
                    "role_support": binding_roles,
                    "domain_authorization": list(
                        domains_by_professional.get(primary, [])
                    ),
                }
            )

        route_bindings = raw_record.get("route_bindings")
        if not isinstance(route_bindings, list):
            errors.append(f"{record_context}.route_bindings must be a list")
            route_bindings = []
        normalized_routes: list[dict[str, Any]] = []
        for route_index, route in enumerate(route_bindings):
            route_context = f"{record_context}.route_bindings[{route_index}]"
            if not isinstance(route, dict) or set(route) != _LAYER3_SELECTOR_ROUTE_FIELDS:
                errors.append(f"{route_context} has invalid fields")
                continue
            pair = (route.get("primary_skill"), route.get("review_skill"))
            if pair not in owner_pairs:
                errors.append(f"{route_context} uses undeclared owner binding {pair!r}")
            for field in ("candidate_id", "primary_skill", "review_skill"):
                if not isinstance(route.get(field), str) or not route.get(field):
                    errors.append(f"{route_context}.{field} must be nonblank text")
            for field in ("rule_id", "routing_family"):
                if route.get(field) is not None and (
                    not isinstance(route.get(field), str) or not route.get(field)
                ):
                    errors.append(f"{route_context}.{field} must be null or nonblank text")
            normalized_routes.append(copy.deepcopy(route))

        projected.append(
            {
                "selector_id": selector_id,
                "selectable_layer3": list(selectable),
                "source": copy.deepcopy(source),
                "positive_evidence": list(positive),
                "nearest_negative": nearest_negative,
                "runtime_selector_signals": concrete_positive,
                "runtime_layer3_signals": runtime_layer3_signals,
                "role_support": role_support,
                "owner_bindings": bindings,
                "route_bindings": normalized_routes,
            }
        )

    expected_order = sorted(
        projected,
        key=lambda record: (
            _LAYER3_SELECTOR_SOURCE_KINDS.index(record["source"]["kind"]),
            record["selector_id"],
        ),
    ) if all(
        record.get("source", {}).get("kind") in _LAYER3_SELECTOR_SOURCE_KINDS
        for record in projected
    ) else []
    if projected != expected_order:
        errors.append(f"{context}: selectors are not in canonical source/id order")
    runtime_selector_ids = {
        record["selector_id"]
        for record in projected
        if record.get("source", {}).get("kind") == "runtime-matcher"
    }
    if runtime_selector_ids != set(runtime_matchers):
        errors.append(
            f"{context}: runtime matcher selector parity differs; "
            f"authority-only={sorted(runtime_selector_ids - set(runtime_matchers))}; "
            f"runtime-only={sorted(set(runtime_matchers) - runtime_selector_ids)}"
        )

    raw_aliases = raw_authority.get("aliases")
    aliases: list[dict[str, Any]] = []
    if not isinstance(raw_aliases, list):
        errors.append(f"{context}: selector_authority.aliases must be a list")
        raw_aliases = []
    projected_by_id = {record["selector_id"]: record for record in projected}
    alias_keys: set[tuple[str, tuple[str, ...], str, str]] = set()
    for index, alias in enumerate(raw_aliases):
        alias_context = f"{context}:aliases[{index}]"
        if not isinstance(alias, dict) or set(alias) != _LAYER3_SELECTOR_ALIAS_FIELDS:
            errors.append(f"{alias_context} has invalid fields")
            continue
        sources = alias.get("source_selector_ids")
        primary = alias.get("primary_skill")
        review = alias.get("review_skill")
        if (
            not isinstance(alias.get("candidate_id"), str)
            or not alias.get("candidate_id")
            or not isinstance(sources, list)
            or not sources
            or len(sources) != len(set(sources))
            or not all(isinstance(source, str) and source for source in sources)
        ):
            errors.append(f"{alias_context} has invalid identity or sources")
            continue
        key = (alias["candidate_id"], tuple(sources), primary, review)
        if key in alias_keys:
            errors.append(f"{alias_context} duplicates alias binding")
        alias_keys.add(key)
        for source_id in sources:
            record = projected_by_id.get(source_id)
            owner_pairs = {
                (binding["primary_skill"], binding["review_skill"])
                for binding in record.get("owner_bindings", [])
            } if isinstance(record, dict) else set()
            if record is None or (primary, review) not in owner_pairs:
                errors.append(f"{alias_context} is not reciprocal with {source_id!r}")
        aliases.append(copy.deepcopy(alias))

    raw_subsets = raw_authority.get("alias_member_subsets")
    if not isinstance(raw_subsets, dict):
        errors.append(
            f"{context}: selector_authority.alias_member_subsets must be a mapping"
        )
        raw_subsets = {}
    for candidate_id, subset in raw_subsets.items():
        if (
            not isinstance(candidate_id, str)
            or not isinstance(subset, list)
            or not subset
            or len(subset) > 3
            or len(subset) != len(set(subset))
            or not set(subset) <= seen_layer3
            or not any(alias["candidate_id"] == candidate_id for alias in aliases)
        ):
            errors.append(f"{context}: invalid alias member subset {candidate_id!r}")

    inventory = raw_authority.get("inventory")
    observed_inventory = {
        "selector_count": len(projected),
        "selectable_layer3_count": len(seen_layer3),
        "owner_binding_count": sum(
            len(record["owner_bindings"]) for record in projected
        ),
    }
    if inventory != observed_inventory:
        errors.append(
            f"{context}: selector inventory differs; expected={inventory!r}; "
            f"observed={observed_inventory!r}"
        )
    if errors:
        raise ValidationProblem("; ".join(errors))
    reference_authority = reference_context_admissibility_authority(
        professional_data,
        foundation_data,
        domain_data,
        context=f"{context}:Reference delivery",
    )
    domains_by_name = domain_authority.get("domains_by_name", {})
    runtime_professionals: dict[str, dict[str, Any]] = {}
    for name, row in professional_by_name.items():
        candidates = row.get("layer3_candidates", [])
        roles = row.get("role_support", [])
        if not isinstance(candidates, list) or not isinstance(roles, list):
            continue
        candidates_by_role = {
            role: [
                candidate
                for candidate in candidates
                if (
                    isinstance(foundation_by_name.get(candidate), dict)
                    and role
                    in foundation_by_name[candidate].get("role_support", [])
                )
                or (
                    isinstance(domains_by_name.get(candidate), dict)
                    and candidate
                    in domains_by_professional.get(name, [])
                    and role
                    in domains_by_name[candidate].get("role_support", [])
                )
            ]
            for role in roles
        }
        reference_rows: list[dict[str, Any]] = []
        for reference_owner in [name, *candidates]:
            owner_reference_authority = reference_authority["owners"].get(
                reference_owner
            )
            if not isinstance(owner_reference_authority, dict):
                raise ValidationProblem(
                    f"{context}: Reference delivery is missing owner "
                    f"{reference_owner!r}"
                )
            owner_layer = owner_reference_authority.get("layer")
            owner_row = (
                professional_by_name.get(reference_owner)
                if owner_layer == "professional"
                else foundation_by_name.get(reference_owner)
                if owner_layer == "foundation"
                else domains_by_name.get(reference_owner)
                if owner_layer == "domain"
                else None
            )
            declarations = owner_reference_authority.get("declarations")
            if not isinstance(owner_row, dict) or not isinstance(
                declarations, dict
            ):
                raise ValidationProblem(
                    f"{context}: Reference delivery authority is malformed for "
                    f"{reference_owner!r}"
                )
            for contract in reference_contracts(
                owner_row.get("reference_index"),
                f"{context}:{owner_layer}[{reference_owner!r}].reference_index",
                owner=reference_owner,
            ):
                if contract["type"] == "index":
                    continue
                declaration = declarations.get(contract["path"])
                reference_rows.append(
                    {
                        "owner_skill": reference_owner,
                        "owner_layer": owner_layer,
                        "path": contract["path"],
                        "type": contract["type"],
                        "load_when": contract["load_when"],
                        "do_not_load_when": contract["do_not_load_when"],
                        "required_by": list(contract["required_by"]),
                        "required_output": list(contract["required_output"]),
                        "context_admissibility": copy.deepcopy(declaration),
                        "residency": (
                            "must-co-trigger-component"
                            if isinstance(declaration, dict)
                            and declaration.get("must_co_trigger_with")
                            else "singleton"
                        ),
                    }
                )
        runtime_professionals[name] = {
            "role_support": list(roles),
            "candidates_by_role": candidates_by_role,
            "domain_authorization": list(
                domains_by_professional.get(name, [])
            ),
            "reference_records": reference_rows,
        }
    runtime_domains = {
        name: {
            "role_support": list(row.get("role_support", [])),
            "trigger_signals": list(row.get("trigger_signals", [])),
            "boundary_signals": list(row.get("boundary_signals", [])),
            "anti_trigger_signals": list(
                row.get("anti_trigger_signals", [])
            ),
        }
        for name, row in domains_by_name.items()
        if isinstance(row, dict)
    }
    return {
        "contract": LAYER3_SELECTOR_AUTHORITY_CONTRACT,
        "inventory": observed_inventory,
        "selectors": projected,
        "aliases": aliases,
        "alias_member_subsets": copy.deepcopy(raw_subsets),
        "runtime_professionals": runtime_professionals,
        "runtime_domains": runtime_domains,
    }


def layer3_selector_runtime_projection(
    authority: object,
    *,
    professional_skill: str,
    profile: str,
    selection_owner: str,
    exact_layer3: object,
    exact_references: object = None,
) -> dict[str, Any]:
    """Return one owner/profile-local declarative selector projection."""

    if (
        not isinstance(authority, dict)
        or authority.get("contract")
        != LAYER3_SELECTOR_AUTHORITY_CONTRACT
    ):
        raise ValidationProblem(
            "runtime selector projection requires canonical authority"
        )
    owner_contract = {
        ("task-agent", "main-control-agent"),
        ("review-agent", "main-control-agent"),
        ("analysis-agent", "main-control-agent"),
        ("task-agent", "engineering-brief"),
        ("review-agent", "engineering-brief"),
    }
    if (profile, selection_owner) not in owner_contract:
        raise ValidationProblem(
            "runtime selector selection owner is not authorized"
        )
    professional_authorizations = authority.get("runtime_professionals")
    if not isinstance(professional_authorizations, dict):
        raise ValidationProblem(
            "runtime selector projection lacks Professional authorization"
        )
    professional = professional_authorizations.get(professional_skill)
    if not isinstance(professional, dict):
        raise ValidationProblem(
            "runtime selector projection names an unknown Professional Skill"
        )
    roles = professional.get("role_support")
    candidates_by_role = professional.get("candidates_by_role")
    domain_authorization = professional.get("domain_authorization")
    reference_records = professional.get("reference_records")
    if (
        not isinstance(roles, list)
        or profile not in roles
        or not isinstance(candidates_by_role, dict)
        or not isinstance(candidates_by_role.get(profile), list)
        or not isinstance(domain_authorization, list)
        or not isinstance(reference_records, list)
    ):
        raise ValidationProblem(
            "runtime selector Professional does not authorize the profile"
        )
    authorized_layer3 = list(candidates_by_role[profile])
    if (
        len(authorized_layer3) != len(set(authorized_layer3))
        or not all(
            isinstance(item, str) and item for item in authorized_layer3
        )
    ):
        raise ValidationProblem(
            "runtime selector Professional authorization is malformed"
        )
    runtime_domains = authority.get("runtime_domains")
    if not isinstance(runtime_domains, dict):
        raise ValidationProblem(
            "runtime selector projection lacks Domain authorization"
        )
    role_reference_records = [
        copy.deepcopy(record)
        for record in reference_records
        if isinstance(record, dict)
        and profile in record.get("required_by", [])
        and (
            record.get("owner_skill") == professional_skill
            or record.get("owner_skill") in authorized_layer3
        )
    ]
    if any(
        record.get("type") == "index"
        or not isinstance(record.get("owner_skill"), str)
        or not record["owner_skill"]
        or record.get("owner_layer")
        not in {"professional", "foundation", "domain"}
        or not isinstance(record.get("path"), str)
        or not record["path"]
        or not isinstance(record.get("required_output"), list)
        or not record["required_output"]
        for record in role_reference_records
    ):
        raise ValidationProblem(
            "runtime selector Reference projection is malformed or exposes an index"
        )
    if exact_references is not None:
        if (
            not isinstance(exact_references, list)
            or len(exact_references) != len(set(exact_references))
            or not all(
                isinstance(path, str) and path for path in exact_references
            )
        ):
            raise ValidationProblem(
                "exact References must be an ordered unique non-empty path list"
            )
        unresolved_references: list[str] = []
        ambiguous_references: list[str] = []
        for exact_reference in exact_references:
            matches = [
                record
                for record in role_reference_records
                if exact_reference == record["path"]
                or exact_reference
                == f"{record['owner_skill']}:{record['path']}"
            ]
            if not matches:
                unresolved_references.append(exact_reference)
            elif len(matches) > 1:
                ambiguous_references.append(exact_reference)
        if unresolved_references or ambiguous_references:
            raise ValidationProblem(
                "exact References contain unauthorized or ambiguous current-"
                "Professional/profile paths: "
                f"unauthorized={sorted(set(unresolved_references))}; "
                f"ambiguous={sorted(set(ambiguous_references))}"
            )
    reference_delivery = {
        "reference_selection_owner": selection_owner,
        "reference_selector_loaded": exact_references is None,
        "exact_references": (
            None if exact_references is None else list(exact_references)
        ),
        "reference_records": (
            role_reference_records if exact_references is None else []
        ),
    }
    if exact_layer3 is not None:
        if (
            not isinstance(exact_layer3, list)
            or len(exact_layer3) > 3
            or len(exact_layer3) != len(set(exact_layer3))
            or not all(isinstance(item, str) and item for item in exact_layer3)
        ):
            raise ValidationProblem(
                "exact Layer 3 must be an ordered unique 0..3 list; never truncate"
            )
        unauthorized = [
            item for item in exact_layer3 if item not in authorized_layer3
        ]
        unauthorized_domains = [
            item
            for item in exact_layer3
            if item in runtime_domains
            and item not in domain_authorization
        ]
        if unauthorized or unauthorized_domains:
            raise ValidationProblem(
                "exact Layer 3 contains unauthorized Professional, profile, "
                "or Domain items: "
                f"{sorted(set([*unauthorized, *unauthorized_domains]))}"
            )
        return {
            "contract": LAYER3_SELECTOR_RUNTIME_CONTRACT,
            "authority_contract": authority["contract"],
            "professional_skill": professional_skill,
            "profile": profile,
            "selection_owner": selection_owner,
            "selection_basis": (
                "review-risk"
                if profile == "review-agent"
                else "professional-risk"
            ),
            "authorized_layer3": authorized_layer3,
            "domain_authorization": list(domain_authorization),
            "selector_loaded": False,
            "exact_layer3": list(exact_layer3),
            "selectors": [],
            **reference_delivery,
        }

    selectors: list[dict[str, Any]] = []
    binding_field = (
        "review_skill" if profile == "review-agent" else "primary_skill"
    )
    authorized = set(authorized_layer3)
    for record in authority.get("selectors", []):
        if not isinstance(record, dict):
            continue
        if not any(
            isinstance(binding, dict)
            and binding.get(binding_field) == professional_skill
            for binding in record.get("owner_bindings", [])
        ):
            continue
        selectable = [
            item
            for item in record.get("selectable_layer3", [])
            if item in authorized
        ]
        if not selectable:
            continue
        signal_authority = record.get("runtime_layer3_signals")
        if not isinstance(signal_authority, dict):
            raise ValidationProblem(
                "runtime selector lacks declarative Layer 3 signals"
            )
        selector_signals = record.get("runtime_selector_signals")
        if not isinstance(selector_signals, list):
            raise ValidationProblem(
                "runtime selector lacks declarative selector signals"
            )
        positive = list(selector_signals)
        if not positive:
            positive = list(
                dict.fromkeys(
                    signal
                    for item in selectable
                    for signal in signal_authority.get(item, {}).get(
                        "positive_signals", []
                    )
                )
            )
        nearest_negative = list(
            dict.fromkeys(
                signal
                for item in selectable
                for signal in signal_authority.get(item, {}).get(
                    "nearest_negative_signals", []
                )
            )
        )
        if not positive or not nearest_negative:
            raise ValidationProblem(
                "runtime selector signals must contain concrete positive and "
                "nearest-negative evidence"
            )
        selectors.append(
            {
                "selector_id": record["selector_id"],
                "selector_kind": "foundation",
                "selectable_layer3": selectable,
                "positive_signal_groups": [positive],
                "nearest_negative_signals": nearest_negative,
            }
        )

    domain_selectors: list[dict[str, Any]] = []
    for domain in domain_authorization:
        if domain not in authorized:
            continue
        row = runtime_domains.get(domain)
        if not isinstance(row, dict):
            raise ValidationProblem(
                f"runtime selector Domain authority is missing {domain!r}"
            )
        triggers = row.get("trigger_signals")
        boundaries = row.get("boundary_signals")
        nearest_negative = row.get("anti_trigger_signals")
        if (
            not isinstance(triggers, list)
            or not triggers
            or not isinstance(boundaries, list)
            or not boundaries
            or not isinstance(nearest_negative, list)
            or not nearest_negative
        ):
            raise ValidationProblem(
                f"runtime selector Domain {domain!r} lacks declarative signals"
            )
        domain_selectors.append(
            {
                "selector_id": f"domain:{domain}",
                "selector_kind": "domain",
                "selectable_layer3": [domain],
                "positive_signal_groups": [
                    list(triggers),
                    list(boundaries),
                    ["changed-surface"],
                ],
                "nearest_negative_signals": list(nearest_negative),
            }
        )
    return {
        "contract": LAYER3_SELECTOR_RUNTIME_CONTRACT,
        "authority_contract": authority["contract"],
        "professional_skill": professional_skill,
        "profile": profile,
        "selection_owner": selection_owner,
        "selection_basis": (
            "review-risk"
            if profile == "review-agent"
            else "professional-risk"
        ),
        "authorized_layer3": authorized_layer3,
        "domain_authorization": list(domain_authorization),
        "selector_loaded": True,
        "exact_layer3": None,
        "selectors": [*domain_selectors, *selectors],
        **reference_delivery,
    }


def layer3_selector_control_projections(
    authority: object,
) -> dict[str, dict[str, Any]]:
    """Project one no-index Control payload per Professional Skill."""

    if (
        not isinstance(authority, dict)
        or authority.get("contract")
        != LAYER3_SELECTOR_AUTHORITY_CONTRACT
        or not isinstance(authority.get("runtime_professionals"), dict)
    ):
        raise ValidationProblem(
            "Control selector projections require canonical authority"
        )
    projections: dict[str, dict[str, Any]] = {}
    for professional_skill in sorted(authority["runtime_professionals"]):
        professional = authority["runtime_professionals"][professional_skill]
        roles = professional.get("role_support", [])
        surfaces: list[dict[str, Any]] = []
        for profile, owner in (
            ("analysis-agent", "main-control-agent"),
            ("task-agent", "main-control-agent"),
            ("review-agent", "main-control-agent"),
            ("task-agent", "engineering-brief"),
            ("review-agent", "engineering-brief"),
        ):
            if profile not in roles:
                continue
            surfaces.append(
                layer3_selector_runtime_projection(
                    authority,
                    professional_skill=professional_skill,
                    profile=profile,
                    selection_owner=owner,
                    exact_layer3=None,
                )
            )
        projections[f"{professional_skill}.json"] = {
            "contract": LAYER3_SELECTOR_CONTROL_CONTRACT,
            "professional_skill": professional_skill,
            "selection_surfaces": surfaces,
        }
    return projections


def _canonical_selector_document_bytes(document: object) -> bytes:
    """Serialize one generated selector document with its required final LF."""

    return (
        json.dumps(
            document,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _engineering_change_diagnosis_decision_authority(
    authority: object,
    release_scenarios: object,
) -> dict[str, Any]:
    """Bind the one source-owned diagnosis decision to selector authority."""

    if (
        not isinstance(authority, dict)
        or authority.get("contract") != LAYER3_SELECTOR_AUTHORITY_CONTRACT
    ):
        raise ValidationProblem("diagnosis selector decision lacks canonical authority")
    if (
        not isinstance(release_scenarios, dict)
        or release_scenarios.get("schema_version") != 2
        or release_scenarios.get("kind")
        != "changeforge.release_routing_scenarios"
        or not isinstance(release_scenarios.get("scenarios"), list)
    ):
        raise ValidationProblem("diagnosis selector decision lacks release scenarios")
    scenarios = [
        row
        for row in release_scenarios["scenarios"]
        if isinstance(row, dict) and row.get("id") == "diagnosis"
    ]
    if len(scenarios) != 1:
        raise ValidationProblem("diagnosis selector decision scenario is missing or ambiguous")
    scenario = scenarios[0]
    router = scenario.get("router")
    expected = router.get("expected") if isinstance(router, dict) else None
    expected_route = {
        "profile": "analysis-agent",
        "primary": "engineering-change-analysis",
        "layer3": ["failure-diagnosis"],
        "review": "reliability-observability-gate",
    }
    if (
        not isinstance(router, dict)
        or router.get("trigger") != "failure diagnosis (`diagnosis-only`)"
        or expected != expected_route
    ):
        raise ValidationProblem("diagnosis selector decision scenario is not canonical")

    aliases = [
        row
        for row in authority.get("aliases", [])
        if isinstance(row, dict)
        and row.get("candidate_id") == "failure-diagnosis-analysis"
    ]
    if len(aliases) != 1:
        raise ValidationProblem("diagnosis selector decision alias is missing or ambiguous")
    alias = aliases[0]
    if (
        alias.get("source_selector_ids") != ["incident-response-coordination"]
        or alias.get("primary_skill") != expected_route["primary"]
        or alias.get("review_skill") != expected_route["review"]
    ):
        raise ValidationProblem("diagnosis selector decision alias is not reciprocal")
    selectors = [
        row
        for row in authority.get("selectors", [])
        if isinstance(row, dict)
        and row.get("selector_id") == "incident-response-coordination"
    ]
    if len(selectors) != 1:
        raise ValidationProblem("diagnosis selector decision source is missing or ambiguous")
    selector = selectors[0]
    owner_pairs = {
        (row.get("primary_skill"), row.get("review_skill"))
        for row in selector.get("owner_bindings", [])
        if isinstance(row, dict)
    }
    if (
        selector.get("selectable_layer3") != expected_route["layer3"]
        or (expected_route["primary"], expected_route["review"])
        not in owner_pairs
        or "analysis-agent" not in selector.get("role_support", [])
    ):
        raise ValidationProblem("diagnosis selector decision owner is not reciprocal")

    router_path = (
        ROOT
        / "src/control-skills/engineering-control-plane/references/"
        "professional-skill-router.md"
    )
    scenario_path = ROOT / "src/registry/release-routing-scenarios.yaml"
    foundation_path = ROOT / "src/registry/foundation-skills.yaml"
    expected_router_row = (
        "| failure diagnosis (`diagnosis-only`) | analysis-agent | "
        "engineering-change-analysis | reliability-observability-gate |"
    )
    try:
        router_bytes = router_path.read_bytes()
        scenario_bytes = scenario_path.read_bytes()
        foundation_bytes = foundation_path.read_bytes()
    except OSError as exc:
        raise ValidationProblem("diagnosis selector source authority is unavailable") from exc
    if router_bytes.decode("utf-8").count(expected_router_row) != 1:
        raise ValidationProblem("diagnosis selector Router trigger is missing or ambiguous")
    return {
        "decision_id": "failure-diagnosis-analysis",
        "route_trigger": router["trigger"],
        "scenario_id": scenario["id"],
        "profile": expected_route["profile"],
        "selection_owner": "main-control-agent",
        "professional_skill": expected_route["primary"],
        "review_skill": expected_route["review"],
        "selected_layer3": list(expected_route["layer3"]),
        "selector_ids": [selector["selector_id"]],
        "source_authority": {
            "router": {
                "path": router_path.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(router_bytes).hexdigest(),
                "pointer": expected_router_row,
            },
            "release_scenario": {
                "path": scenario_path.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(scenario_bytes).hexdigest(),
                "pointer": "scenarios[id=diagnosis]",
            },
            "selector_registry": {
                "path": foundation_path.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(foundation_bytes).hexdigest(),
                "pointer": (
                    "selector_authority.aliases[candidate_id="
                    "failure-diagnosis-analysis]"
                ),
            },
        },
    }


def layer3_selector_normalized_control_projections(
    authority: object,
    *,
    release_scenarios: object = None,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    """Normalize selector views and owner-scoped Reference partitions."""

    canonical = layer3_selector_control_projections(authority)
    runtime_professionals = authority.get("runtime_professionals")
    if not isinstance(runtime_professionals, dict):
        raise ValidationProblem(
            "normalized selector projections require Professional authority"
        )
    selectors: dict[str, dict[str, Any]] = {}
    partitions: dict[str, dict[str, Any]] = {}
    if release_scenarios is None:
        release_scenarios = load_yaml_file(
            ROOT / "src/registry/release-routing-scenarios.yaml"
        )
    diagnosis_decision = _engineering_change_diagnosis_decision_authority(
        authority,
        release_scenarios,
    )
    profile_fields = {
        "profile",
        "selection_basis",
        "authorized_layer3",
        "domain_authorization",
        "selectors",
    }
    for filename, document in canonical.items():
        professional_skill = document["professional_skill"]
        professional = runtime_professionals.get(professional_skill)
        if not isinstance(professional, dict):
            raise ValidationProblem(
                f"normalized selector lacks {professional_skill!r} authority"
            )
        raw_records = professional.get("reference_records")
        if not isinstance(raw_records, list):
            raise ValidationProblem(
                f"normalized selector {professional_skill!r} lacks Reference records"
            )
        records_by_owner: dict[str, list[dict[str, Any]]] = {}
        identities: dict[tuple[str, str], dict[str, Any]] = {}
        for raw_record in raw_records:
            if not isinstance(raw_record, dict):
                raise ValidationProblem(
                    f"normalized selector {professional_skill!r} has malformed Reference records"
                )
            record = copy.deepcopy(raw_record)
            identity = (record.get("owner_skill"), record.get("path"))
            if not all(isinstance(value, str) and value for value in identity):
                raise ValidationProblem(
                    f"normalized selector {professional_skill!r} has malformed Reference identity"
                )
            previous = identities.get(identity)
            if previous is not None:
                if previous != record:
                    raise ValidationProblem(
                        f"normalized selector {professional_skill!r} has conflicting duplicate Reference records"
                    )
                continue
            identities[identity] = record
            records_by_owner.setdefault(identity[0], []).append(record)
        partition_owners = {
            professional_skill,
            *(
                owner
                for candidates in professional.get("candidates_by_role", {}).values()
                for owner in candidates
            ),
        }
        for owner_skill in sorted(partition_owners):
            records = records_by_owner.get(owner_skill, [])
            partitions[f"{professional_skill}/{owner_skill}.json"] = {
                "contract": LAYER3_SELECTOR_REFERENCE_RECORDS_CONTRACT,
                "authority_contract": authority["contract"],
                "professional_skill": professional_skill,
                "owner_skill": owner_skill,
                "records_sha256": hashlib.sha256(
                    _canonical_selector_document_bytes(records)
                ).hexdigest(),
                "reference_records": records,
            }

        profile_authority: list[dict[str, Any]] = []
        profiles: dict[str, dict[str, Any]] = {}
        owner_surfaces: list[dict[str, str]] = []
        for surface in document["selection_surfaces"]:
            profile = surface["profile"]
            profile_row = {
                field: copy.deepcopy(surface[field]) for field in profile_fields
            }
            previous = profiles.get(profile)
            if previous is not None and previous != profile_row:
                raise ValidationProblem(
                    f"normalized selector {professional_skill!r} has owner-dependent Profile authority"
                )
            if previous is None:
                profiles[profile] = profile_row
                profile_authority.append(profile_row)
            owner_surfaces.append(
                {
                    "profile": profile,
                    "selection_owner": surface["selection_owner"],
                }
            )
        base = {
            "contract": LAYER3_SELECTOR_NORMALIZED_CONTROL_CONTRACT,
            "authority_contract": authority["contract"],
            "professional_skill": professional_skill,
            "maximum_layer3": 3,
            "exact_layer3_bypass": True,
            "profile_authority": profile_authority,
            "owner_surfaces": owner_surfaces,
            "reference_records_partition": {
                "contract": LAYER3_SELECTOR_REFERENCE_RECORDS_CONTRACT,
                "path_template": (
                    f"../reference-records/{professional_skill}/"
                    "{owner_skill}.json"
                ),
            },
        }
        for surface in document["selection_surfaces"]:
            selected_layer3: list[str] = []
            selected_partitions = {
                professional_skill: partitions[
                    f"{professional_skill}/{professional_skill}.json"
                ]
            }
            expanded = layer3_selector_expand_runtime_projection(
                base,
                selected_partitions,
                profile=surface["profile"],
                selection_owner=surface["selection_owner"],
                exact_layer3=None,
                selected_layer3=selected_layer3,
                exact_references=None,
            )
            expected = copy.deepcopy(surface)
            expected["reference_records"] = [
                record
                for record in expected["reference_records"]
                if record["owner_skill"] == professional_skill
            ]
            if expanded != expected:
                raise ValidationProblem(
                    f"normalized selector {professional_skill!r} does not expand to canonical authority"
                )
        if professional_skill != "engineering-change-analysis":
            selectors[filename] = base
            continue

        profile_rows = [
            row
            for row in base["profile_authority"]
            if row["profile"] == diagnosis_decision["profile"]
        ]
        owner_rows = [
            row
            for row in base["owner_surfaces"]
            if row
            == {
                "profile": diagnosis_decision["profile"],
                "selection_owner": diagnosis_decision["selection_owner"],
            }
        ]
        if len(profile_rows) != 1 or len(owner_rows) != 1:
            raise ValidationProblem(
                "diagnosis selector decision lacks one canonical owner/Profile surface"
            )
        shard_profile = copy.deepcopy(profile_rows[0])
        shard_profile["selectors"] = [
            row
            for row in shard_profile["selectors"]
            if row.get("selector_id") in diagnosis_decision["selector_ids"]
        ]
        if [row.get("selector_id") for row in shard_profile["selectors"]] != (
            diagnosis_decision["selector_ids"]
        ):
            raise ValidationProblem(
                "diagnosis selector decision does not resolve one canonical selector"
            )
        shard_projection = {
            **copy.deepcopy(base),
            "profile_authority": [shard_profile],
            "owner_surfaces": owner_rows,
        }
        shard = {
            "contract": LAYER3_SELECTOR_DECISION_PARTITION_CONTRACT,
            "authority_contract": authority["contract"],
            "professional_skill": professional_skill,
            "decision_id": diagnosis_decision["decision_id"],
            "profile": diagnosis_decision["profile"],
            "selection_owner": diagnosis_decision["selection_owner"],
            "review_skill": diagnosis_decision["review_skill"],
            "selected_layer3": copy.deepcopy(
                diagnosis_decision["selected_layer3"]
            ),
            "selector_ids": copy.deepcopy(diagnosis_decision["selector_ids"]),
            "projection": shard_projection,
        }
        complete_path = f"{professional_skill}/complete.json"
        decision_path = (
            f"{professional_skill}/{diagnosis_decision['decision_id']}.json"
        )
        envelope_decision = {
            "runtime_key": {
                "route_source": copy.deepcopy(
                    diagnosis_decision["source_authority"]["router"]
                ),
                "trigger": diagnosis_decision["route_trigger"],
                "start_profile": diagnosis_decision["profile"],
                "primary_professional_skill": diagnosis_decision[
                    "professional_skill"
                ],
                "review_skill": diagnosis_decision["review_skill"],
                "selection_owner": diagnosis_decision["selection_owner"],
            },
            "provenance": {
                "decision_id": diagnosis_decision["decision_id"],
                "scenario_id": diagnosis_decision["scenario_id"],
                "release_scenario": copy.deepcopy(
                    diagnosis_decision["source_authority"]["release_scenario"]
                ),
                "selector_registry": copy.deepcopy(
                    diagnosis_decision["source_authority"]["selector_registry"]
                ),
            },
        }
        envelope_decision.update(
            {
                "path": decision_path,
                "sha256": hashlib.sha256(
                    _canonical_selector_document_bytes(shard)
                ).hexdigest(),
            }
        )
        envelope = {
            "contract": LAYER3_SELECTOR_DECISION_ENVELOPE_CONTRACT,
            "authority_contract": authority["contract"],
            "professional_skill": professional_skill,
            "maximum_layer3": 3,
            "exact_layer3_bypass": True,
            "decisions": [envelope_decision],
            "complete": {
                "path": complete_path,
                "sha256": hashlib.sha256(
                    _canonical_selector_document_bytes(base)
                ).hexdigest(),
            },
        }
        selectors[filename] = envelope
        selectors[complete_path] = base
        selectors[decision_path] = shard
    return selectors, partitions


def layer3_selector_resolve_control_projection(
    envelope: object,
    documents: object,
    *,
    runtime_key: object,
) -> dict[str, Any]:
    """Resolve one exact decision shard or the complete fail-closed fallback."""

    envelope_fields = {
        "contract",
        "authority_contract",
        "professional_skill",
        "maximum_layer3",
        "exact_layer3_bypass",
        "decisions",
        "complete",
    }
    envelope_build = envelope.get("build") if isinstance(envelope, dict) else None
    if envelope_build is not None:
        envelope_fields.add("build")
        try:
            runtime_asset_build_identity_bytes(envelope_build)
        except ValueError as exc:
            raise ValidationProblem("selector decision envelope is malformed") from exc
    if (
        not isinstance(envelope, dict)
        or set(envelope) != envelope_fields
        or envelope.get("contract")
        != LAYER3_SELECTOR_DECISION_ENVELOPE_CONTRACT
        or envelope.get("authority_contract")
        != LAYER3_SELECTOR_AUTHORITY_CONTRACT
        or not isinstance(envelope.get("professional_skill"), str)
        or not envelope["professional_skill"]
        or envelope.get("maximum_layer3") != 3
        or envelope.get("exact_layer3_bypass") is not True
        or not isinstance(envelope.get("decisions"), list)
        or not envelope["decisions"]
        or not isinstance(documents, dict)
    ):
        raise ValidationProblem("selector decision envelope is malformed")
    complete = envelope.get("complete")
    if (
        not isinstance(complete, dict)
        or set(complete) != {"path", "sha256"}
        or not all(isinstance(value, str) and value for value in complete.values())
    ):
        raise ValidationProblem("selector decision complete fallback is malformed")
    runtime_key_fields = {
        "route_source",
        "trigger",
        "start_profile",
        "primary_professional_skill",
        "review_skill",
        "selection_owner",
    }
    route_source_fields = {"path", "sha256", "pointer"}
    source_provenance_fields = {
        "decision_id",
        "scenario_id",
        "release_scenario",
        "selector_registry",
    }
    runtime_provenance_fields = {
        "decision_id",
        "scenario_id",
        "selector_registry",
    }
    provenance_fields = (
        runtime_provenance_fields
        if envelope_build is not None
        else source_provenance_fields
    )
    provenance_authority_fields = (
        ("selector_registry",)
        if envelope_build is not None
        else ("release_scenario", "selector_registry")
    )
    decision_fields = {"runtime_key", "provenance", "path", "sha256"}
    decisions = envelope["decisions"]
    if (
        not isinstance(runtime_key, dict)
        or set(runtime_key) != runtime_key_fields
        or not isinstance(runtime_key.get("route_source"), dict)
        or set(runtime_key["route_source"]) != route_source_fields
        or not all(
            isinstance(value, str) and value
            for value in (
                *runtime_key["route_source"].values(),
                runtime_key["trigger"],
                runtime_key["start_profile"],
                runtime_key["primary_professional_skill"],
                runtime_key["review_skill"],
                runtime_key["selection_owner"],
            )
        )
    ):
        raise ValidationProblem("selector decision runtime tuple is malformed")
    if any(
        not isinstance(row, dict)
        or set(row) != decision_fields
        or not isinstance(row.get("runtime_key"), dict)
        or set(row["runtime_key"]) != runtime_key_fields
        or not isinstance(row["runtime_key"].get("route_source"), dict)
        or set(row["runtime_key"]["route_source"]) != route_source_fields
        or not isinstance(row.get("provenance"), dict)
        or set(row["provenance"]) != provenance_fields
        or not all(
            isinstance(row["provenance"].get(field), str)
            and row["provenance"][field]
            for field in ("decision_id", "scenario_id")
        )
        or not all(
            isinstance(row["provenance"].get(field), dict)
            and set(row["provenance"][field]) == route_source_fields
            and all(
                isinstance(value, str) and value
                for value in row["provenance"][field].values()
            )
            for field in provenance_authority_fields
        )
        for row in decisions
    ):
        raise ValidationProblem("selector decision envelope contains a malformed decision")
    decision_ids = [row["provenance"]["decision_id"] for row in decisions]
    decision_paths = [row["path"] for row in decisions]
    decision_keys = [
        _canonical_selector_document_bytes(row["runtime_key"])
        for row in decisions
    ]
    route_sources = [
        _canonical_selector_document_bytes(row["runtime_key"]["route_source"])
        for row in decisions
    ]
    if (
        len(decision_ids) != len(set(decision_ids))
        or len(decision_paths) != len(set(decision_paths))
        or len(decision_keys) != len(set(decision_keys))
        or len(route_sources) != len(set(route_sources))
    ):
        raise ValidationProblem("selector decision envelope is duplicate or ambiguous")
    same_source = [
        row
        for row in decisions
        if row["runtime_key"]["route_source"] == runtime_key["route_source"]
    ]
    exact = [
        row
        for row in same_source
        if row["runtime_key"] == runtime_key
    ]
    if same_source and len(exact) != 1:
        raise ValidationProblem("selector decision runtime tuple identity mismatch")
    if exact:
        decision = exact[0]
        if set(documents) != {decision["path"]}:
            raise ValidationProblem("selector decision document is missing or unexpected")
        if hashlib.sha256(
            _canonical_selector_document_bytes(documents[decision["path"]])
        ).hexdigest() != decision["sha256"]:
            raise ValidationProblem("selector decision document is stale")
        shard = documents[decision["path"]]
        shard_selected = shard.get("selected_layer3") if isinstance(shard, dict) else None
        if (
            not isinstance(shard, dict)
            or shard.get("contract")
            != LAYER3_SELECTOR_DECISION_PARTITION_CONTRACT
            or shard.get("authority_contract") != envelope["authority_contract"]
            or shard.get("professional_skill")
            != runtime_key["primary_professional_skill"]
            or shard.get("decision_id")
            != decision["provenance"]["decision_id"]
            or shard.get("profile") != runtime_key["start_profile"]
            or shard.get("selection_owner") != runtime_key["selection_owner"]
            or shard.get("review_skill") != runtime_key["review_skill"]
            or not isinstance(shard_selected, list)
            or not shard_selected
            or len(shard_selected) > 3
            or len(shard_selected) != len(set(shard_selected))
            or any(not isinstance(item, str) or not item for item in shard_selected)
            or not isinstance(shard.get("selector_ids"), list)
            or not shard["selector_ids"]
            or not isinstance(shard.get("projection"), dict)
            or (
                envelope_build is not None
                and (
                    shard.get("build") != envelope_build
                    or shard["projection"].get("build") != envelope_build
                )
            )
        ):
            raise ValidationProblem("selector decision partition binding mismatch")
        profile_rows = [
            row
            for row in shard["projection"].get("profile_authority", [])
            if isinstance(row, dict)
            and row.get("profile") == runtime_key["start_profile"]
        ]
        if (
            len(profile_rows) != 1
            or any(
                item not in profile_rows[0].get("authorized_layer3", [])
                for item in shard_selected
            )
        ):
            raise ValidationProblem("selector decision partition Layer 3 is unauthorized")
        return {
            "contract": "changeforge.layer3-selector-resolution/v1",
            "selection_kind": "exact",
            "decision_id": decision["provenance"]["decision_id"],
            "path": decision["path"],
            "sha256": decision["sha256"],
            "runtime_key": copy.deepcopy(runtime_key),
            "provenance": copy.deepcopy(decision["provenance"]),
            "selected_layer3": copy.deepcopy(shard_selected),
            "projection": copy.deepcopy(shard["projection"]),
        }

    if set(documents) != {complete["path"]}:
        raise ValidationProblem("selector decision complete fallback is missing or unexpected")
    fallback = documents[complete["path"]]
    if hashlib.sha256(_canonical_selector_document_bytes(fallback)).hexdigest() != (
        complete["sha256"]
    ):
        raise ValidationProblem("selector decision document is stale")
    if (
        not isinstance(fallback, dict)
        or fallback.get("contract") != LAYER3_SELECTOR_NORMALIZED_CONTROL_CONTRACT
        or fallback.get("authority_contract") != envelope["authority_contract"]
        or fallback.get("professional_skill")
        != runtime_key["primary_professional_skill"]
        or (
            envelope_build is not None
            and fallback.get("build") != envelope_build
        )
    ):
        raise ValidationProblem("selector decision complete fallback is malformed")
    return {
        "contract": "changeforge.layer3-selector-resolution/v1",
        "selection_kind": "complete",
        "decision_id": None,
        "path": complete["path"],
        "sha256": complete["sha256"],
        "runtime_key": copy.deepcopy(runtime_key),
        "provenance": None,
        "selected_layer3": None,
        "projection": copy.deepcopy(fallback),
    }


def layer3_selector_runtime_decision_envelope(
    envelope: object,
    documents: object,
    *,
    build_identity: object,
) -> dict[str, Any]:
    """Validate full source provenance before emitting a compact Runtime envelope."""

    try:
        runtime_asset_build_identity_bytes(build_identity)
    except ValueError as exc:
        raise ValidationProblem("selector Runtime build identity is malformed") from exc
    if (
        not isinstance(envelope, dict)
        or "build" in envelope
        or not isinstance(documents, dict)
        or not isinstance(envelope.get("decisions"), list)
        or not envelope["decisions"]
    ):
        raise ValidationProblem("selector source envelope is malformed")
    for row in envelope["decisions"]:
        path = row.get("path") if isinstance(row, dict) else None
        runtime_key = row.get("runtime_key") if isinstance(row, dict) else None
        if not isinstance(path, str) or not path or path not in documents:
            raise ValidationProblem("selector source provenance document is missing")
        layer3_selector_resolve_control_projection(
            envelope,
            {path: documents[path]},
            runtime_key=runtime_key,
        )

    runtime_envelope = copy.deepcopy(envelope)
    runtime_envelope["build"] = build_identity
    for row in runtime_envelope["decisions"]:
        provenance = row["provenance"]
        row["provenance"] = {
            field: copy.deepcopy(provenance[field])
            for field in (
                "decision_id",
                "scenario_id",
                        "selector_registry",
            )
        }
    return runtime_envelope


def layer3_selector_expand_runtime_projection(
    base: object,
    partitions: object,
    *,
    profile: str,
    selection_owner: str,
    exact_layer3: object,
    selected_layer3: object = None,
    exact_references: object = None,
    exact_reference_bindings: object = None,
) -> dict[str, Any]:
    """Expand one normalized selector assignment to the canonical runtime view."""

    base_fields = {
        "contract",
        "authority_contract",
        "professional_skill",
        "maximum_layer3",
        "exact_layer3_bypass",
        "profile_authority",
        "owner_surfaces",
        "reference_records_partition",
    }
    base_build = base.get("build") if isinstance(base, dict) else None
    if base_build is not None:
        base_fields.add("build")
        try:
            runtime_asset_build_identity_bytes(base_build)
        except ValueError as exc:
            raise ValidationProblem("normalized selector base is malformed") from exc
    if (
        not isinstance(base, dict)
        or set(base) != base_fields
        or base.get("contract") != LAYER3_SELECTOR_NORMALIZED_CONTROL_CONTRACT
        or base.get("authority_contract") != LAYER3_SELECTOR_AUTHORITY_CONTRACT
        or not isinstance(base.get("professional_skill"), str)
        or not base["professional_skill"]
        or base.get("maximum_layer3") != 3
        or base.get("exact_layer3_bypass") is not True
    ):
        raise ValidationProblem("normalized selector base is malformed")
    owner_surfaces = base.get("owner_surfaces")
    if (
        not isinstance(owner_surfaces, list)
        or not owner_surfaces
        or any(
            not isinstance(row, dict)
            or set(row) != {"profile", "selection_owner"}
            or not all(isinstance(value, str) and value for value in row.values())
            for row in owner_surfaces
        )
        or len(
            {(row["profile"], row["selection_owner"]) for row in owner_surfaces}
        )
        != len(owner_surfaces)
    ):
        raise ValidationProblem("normalized selector owner surfaces are malformed or duplicate")
    if {"profile": profile, "selection_owner": selection_owner} not in owner_surfaces:
        raise ValidationProblem("normalized selector assignment is unauthorized")
    profile_authority = base.get("profile_authority")
    profile_fields = {
        "profile",
        "selection_basis",
        "authorized_layer3",
        "domain_authorization",
        "selectors",
    }
    matches = [
        row
        for row in profile_authority
        if isinstance(row, dict) and row.get("profile") == profile
    ] if isinstance(profile_authority, list) else []
    if (
        len(matches) != 1
        or set(matches[0]) != profile_fields
        or len(
            {
                row.get("profile")
                for row in profile_authority
                if isinstance(row, dict)
            }
        )
        != len(profile_authority)
    ):
        raise ValidationProblem("normalized selector Profile authority is missing or duplicate")
    profile_row = matches[0]
    authorized_layer3 = profile_row.get("authorized_layer3")
    domain_authorization = profile_row.get("domain_authorization")
    selector_records = profile_row.get("selectors")
    if (
        not isinstance(authorized_layer3, list)
        or len(authorized_layer3) != len(set(authorized_layer3))
        or not all(isinstance(item, str) and item for item in authorized_layer3)
        or not isinstance(domain_authorization, list)
        or len(domain_authorization) != len(set(domain_authorization))
        or not all(isinstance(item, str) and item for item in domain_authorization)
        or not isinstance(selector_records, list)
    ):
        raise ValidationProblem("normalized selector Profile authority is malformed")
    selector_ids: list[str] = []
    for selector in selector_records:
        selector_id = selector.get("selector_id") if isinstance(selector, dict) else None
        if not isinstance(selector_id, str) or not selector_id:
            raise ValidationProblem("normalized selector record is malformed")
        selector_ids.append(selector_id)
    if len(selector_ids) != len(set(selector_ids)):
        raise ValidationProblem("normalized selector records contain a duplicate")

    if exact_layer3 is not None:
        if (
            not isinstance(exact_layer3, list)
            or len(exact_layer3) > base["maximum_layer3"]
            or len(exact_layer3) != len(set(exact_layer3))
            or not all(isinstance(item, str) and item for item in exact_layer3)
        ):
            raise ValidationProblem(
                "exact Layer 3 must be an ordered unique 0..3 list; never truncate"
            )
        unauthorized = [
            item for item in exact_layer3 if item not in authorized_layer3
        ]
        unauthorized_domains = [
            item
            for item in exact_layer3
            if item in domain_authorization and item not in authorized_layer3
        ]
        if unauthorized or unauthorized_domains:
            raise ValidationProblem(
                "exact Layer 3 contains unauthorized Professional, profile, or Domain items"
            )

    if selected_layer3 is None:
        selected_layer3 = list(exact_layer3) if exact_layer3 is not None else []
    if (
        not isinstance(selected_layer3, list)
        or len(selected_layer3) > base["maximum_layer3"]
        or len(selected_layer3) != len(set(selected_layer3))
        or not all(isinstance(item, str) and item for item in selected_layer3)
        or any(item not in authorized_layer3 for item in selected_layer3)
    ):
        raise ValidationProblem(
            "selected Layer 3 must be an authorized ordered unique 0..3 list"
        )
    if exact_layer3 is not None and selected_layer3 != exact_layer3:
        raise ValidationProblem("selected Layer 3 disagrees with exact Layer 3")

    role_reference_records: list[dict[str, Any]] = []
    if exact_references is None:
        required_owners = [base["professional_skill"], *selected_layer3]
        link = base.get("reference_records_partition")
        accepted_partition_templates = {
            (
                f"../reference-records/{base['professional_skill']}/"
                "{owner_skill}.json"
            ),
            "reference-records/{owner_skill}.json",
            "../reference-records/{owner_skill}.json",
        }
        if (
            not isinstance(link, dict)
            or set(link) != {"contract", "path_template"}
            or link.get("contract") != LAYER3_SELECTOR_REFERENCE_RECORDS_CONTRACT
            or link.get("path_template") not in accepted_partition_templates
        ):
            raise ValidationProblem("normalized selector Reference partition template is malformed")
        if (
            not isinstance(partitions, dict)
            or set(partitions) != set(required_owners)
        ):
            raise ValidationProblem(
                "normalized selector requires exactly the Professional and selected Layer 3 partitions"
            )
        record_fields = {
            "owner_skill",
            "owner_layer",
            "path",
            "type",
            "load_when",
            "do_not_load_when",
            "required_by",
            "required_output",
            "context_admissibility",
            "residency",
        }
        identities: list[tuple[str, str]] = []
        partition_fields = {
            "contract",
            "authority_contract",
            "professional_skill",
            "owner_skill",
            "records_sha256",
            "reference_records",
        }
        if base_build is not None:
            partition_fields.add("build")
        for owner_skill in required_owners:
            partition = partitions[owner_skill]
            if (
                not isinstance(partition, dict)
                or set(partition) != partition_fields
                or partition.get("contract")
                != LAYER3_SELECTOR_REFERENCE_RECORDS_CONTRACT
                or partition.get("authority_contract") != base["authority_contract"]
                or partition.get("professional_skill") != base["professional_skill"]
                or partition.get("owner_skill") != owner_skill
                or (
                    base_build is not None
                    and partition.get("build") != base_build
                )
                or not isinstance(partition.get("reference_records"), list)
                or partition.get("records_sha256")
                != hashlib.sha256(
                    _canonical_selector_document_bytes(
                        partition.get("reference_records")
                    )
                ).hexdigest()
            ):
                raise ValidationProblem(
                    "normalized selector Reference partition is missing, malformed, owner-mismatched, or stale"
                )
            for record in partition["reference_records"]:
                if not isinstance(record, dict) or set(record) != record_fields:
                    raise ValidationProblem("normalized selector Reference partition record is malformed")
                identity = (record.get("owner_skill"), record.get("path"))
                if not all(isinstance(value, str) and value for value in identity):
                    raise ValidationProblem("normalized selector Reference partition identity is malformed")
                identities.append(identity)
                if record["owner_skill"] != owner_skill:
                    raise ValidationProblem("normalized selector has owner-leaking Reference partition")
                if (
                    record.get("type") == "index"
                    or record.get("owner_layer") not in {"professional", "foundation", "domain"}
                    or not isinstance(record.get("required_by"), list)
                    or not record["required_by"]
                    or not set(record["required_by"])
                    <= {"analysis-agent", "task-agent", "review-agent"}
                    or not isinstance(record.get("required_output"), list)
                    or not record["required_output"]
                ):
                    raise ValidationProblem("normalized selector Reference partition record is malformed")
                if profile in record["required_by"]:
                    role_reference_records.append(copy.deepcopy(record))
        if len(identities) != len(set(identities)):
            raise ValidationProblem("normalized selector Reference partitions have duplicate records")

    if exact_references is not None:
        if (
            not isinstance(exact_references, list)
            or len(exact_references) != len(set(exact_references))
            or not all(isinstance(path, str) and path for path in exact_references)
        ):
            raise ValidationProblem(
                "exact References must be an ordered unique path list"
            )
        if partitions not in (None, {}):
            raise ValidationProblem("exact References must not load Reference partitions")
        if exact_reference_bindings is None:
            exact_reference_bindings = []
        if (
            not isinstance(exact_reference_bindings, list)
            or len(exact_reference_bindings) != len(exact_references)
        ):
            raise ValidationProblem("exact References require one ordered native binding each")
        allowed_exact_owners = {base["professional_skill"], *selected_layer3}
        for exact_reference, binding in zip(
            exact_references, exact_reference_bindings, strict=True
        ):
            if (
                not isinstance(binding, dict)
                or not isinstance(binding.get("owner_skill"), str)
                or not isinstance(binding.get("path"), str)
                or binding["owner_skill"] not in allowed_exact_owners
                or exact_reference
                not in {
                    binding["path"],
                    f"{binding['owner_skill']}:{binding['path']}",
                    f"{binding['owner_skill']}/{binding['path']}",
                }
            ):
                raise ValidationProblem(
                    "exact References contain unauthorized or mismatched native bindings"
                )
        if len(
            {(row["owner_skill"], row["path"]) for row in exact_reference_bindings}
        ) != len(exact_reference_bindings):
            raise ValidationProblem(
                "exact References contain duplicate native bindings"
            )

    result = {
        "contract": LAYER3_SELECTOR_RUNTIME_CONTRACT,
        "authority_contract": base["authority_contract"],
        "professional_skill": base["professional_skill"],
        "profile": profile,
        "selection_owner": selection_owner,
        "selection_basis": profile_row["selection_basis"],
        "authorized_layer3": copy.deepcopy(authorized_layer3),
        "domain_authorization": copy.deepcopy(domain_authorization),
        "selector_loaded": exact_layer3 is None,
        "exact_layer3": None if exact_layer3 is None else list(exact_layer3),
        "selectors": copy.deepcopy(selector_records) if exact_layer3 is None else [],
        "reference_selection_owner": selection_owner,
        "reference_selector_loaded": exact_references is None,
        "exact_references": (
            None if exact_references is None else list(exact_references)
        ),
        "reference_records": (
            role_reference_records if exact_references is None else []
        ),
    }
    if base_build is not None:
        result["build"] = base_build
    return result


def layer3_selector_runtime_selection_receipt(
    projection: object,
    *,
    evidence_signals: object,
    build_identity: str,
) -> dict[str, Any]:
    """Resolve one local projection and emit its deterministic owner receipt."""

    try:
        runtime_asset_build_identity_bytes(build_identity)
    except ValueError as exc:
        raise ValidationProblem(
            "runtime selector receipt build identity is malformed"
        ) from exc
    if (
        not isinstance(projection, dict)
        or projection.get("contract")
        != LAYER3_SELECTOR_RUNTIME_CONTRACT
        or not isinstance(projection.get("selectors"), list)
        or not isinstance(projection.get("authorized_layer3"), list)
    ):
        raise ValidationProblem(
            "runtime selector decision requires one canonical local projection"
        )
    projection_build = projection.get("build")
    if projection_build is not None and projection_build != build_identity:
        raise ValidationProblem(
            "runtime selector receipt build identity disagrees with projection"
        )
    if projection.get("selector_loaded") is False:
        exact = projection.get("exact_layer3")
        if not isinstance(exact, list):
            raise ValidationProblem(
                "fixed runtime selector projection lacks exact Layer 3"
            )
        evidence: list[str] = []
        selected = list(exact)
        selector_ids = ["exact-layer3-authority"]
    else:
        if (
            not isinstance(evidence_signals, list)
            or not all(
                isinstance(signal, str) and signal.strip()
                for signal in evidence_signals
            )
        ):
            raise ValidationProblem(
                "runtime selector evidence must be a list of nonblank signals"
            )

        def normalized(signal: str) -> str:
            return " ".join(signal.casefold().split())

        evidence = [normalized(signal) for signal in evidence_signals]
        if len(evidence) != len(set(evidence)):
            raise ValidationProblem(
                "runtime selector evidence signals must be unique"
            )
        evidence_set = set(evidence)
        selected = []
        selector_ids = []
        for record in projection["selectors"]:
            if not isinstance(record, dict):
                raise ValidationProblem("runtime selector record must be a mapping")
            groups = record.get("positive_signal_groups")
            nearest_negative = record.get("nearest_negative_signals")
            layer3 = record.get("selectable_layer3")
            selector_id = record.get("selector_id")
            if (
                not isinstance(groups, list)
                or not groups
                or not all(isinstance(group, list) and group for group in groups)
                or not isinstance(nearest_negative, list)
                or not nearest_negative
                or not isinstance(layer3, list)
                or not layer3
                or not isinstance(selector_id, str)
                or not selector_id
            ):
                raise ValidationProblem("runtime selector record is malformed")
            if any(
                normalized(signal) in evidence_set
                for signal in nearest_negative
            ):
                continue
            if not all(
                any(normalized(signal) in evidence_set for signal in group)
                for group in groups
            ):
                continue
            selector_ids.append(selector_id)
            selected.extend(item for item in layer3 if item not in selected)
        authorized = set(projection["authorized_layer3"])
        if not set(selected) <= authorized:
            raise ValidationProblem(
                "runtime selector selected unauthorized Layer 3"
            )
        if len(selected) > 3:
            raise ValidationProblem(
                "runtime selector selected more than three Layer 3 items; never truncate"
            )

    profile = projection.get("profile")
    selection_kinds = {
        "analysis-agent": "analysis-risk",
        "task-agent": "implementation-risk",
        "review-agent": "review-risk",
    }
    selection_kind = selection_kinds.get(profile)
    if selection_kind is None:
        raise ValidationProblem("runtime selector receipt profile is invalid")
    receipt: dict[str, Any] = {
        "contract": "changeforge.layer3-selector-selection-receipt/v1",
        "build": build_identity,
        "authority_contract": projection.get("authority_contract"),
        "selection_owner": projection.get("selection_owner"),
        "profile": profile,
        "professional_skill": projection.get("professional_skill"),
        "selection_kind": selection_kind,
        "selection_basis": projection.get("selection_basis"),
        "selector_ids": selector_ids,
        "evidence_signals": evidence,
        "selected_layer3": selected,
    }
    return receipt


def layer3_selector_runtime_selection_receipt_errors(
    receipt: object,
    *,
    expected_owner: str,
    expected_profile: str,
    expected_professional: str,
    expected_selection_kind: str,
    expected_selected_layer3: list[str],
    expected_build_identity: str,
) -> list[str]:
    """Replay one receipt from canonical authority and compare it exactly."""

    expected_fields = {
        "contract",
        "build",
        "authority_contract",
        "selection_owner",
        "profile",
        "professional_skill",
        "selection_kind",
        "selection_basis",
        "selector_ids",
        "evidence_signals",
        "selected_layer3",
        }
    if not isinstance(receipt, dict) or set(receipt) != expected_fields:
        return ["selector selection receipt fields are not exact"]
    errors: list[str] = []
    canonical_selection_kinds = {
        "analysis-agent": "analysis-risk",
        "task-agent": "implementation-risk",
        "review-agent": "review-risk",
    }
    canonical_kind = canonical_selection_kinds.get(expected_profile)
    if canonical_kind is None or expected_selection_kind != canonical_kind:
        errors.append(
            "selector selection receipt expected profile/selection_kind "
            "binding is not canonical"
        )
        return errors
    try:
        runtime_asset_build_identity_bytes(expected_build_identity)
    except ValueError:
        errors.append(
            "selector selection receipt expected build identity is malformed"
        )
        return errors
    if (
        not isinstance(expected_owner, str)
        or not expected_owner
        or not isinstance(expected_professional, str)
        or not expected_professional
        or not isinstance(expected_selected_layer3, list)
        or len(expected_selected_layer3) > 3
        or len(expected_selected_layer3) != len(set(expected_selected_layer3))
        or not all(
            isinstance(item, str) and item
            for item in expected_selected_layer3
        )
    ):
        errors.append(
            "selector selection receipt expected assignment binding is malformed"
        )
        return errors
    evidence = receipt["evidence_signals"]
    if (
        not isinstance(evidence, list)
        or len(evidence) != len(set(evidence))
        or not all(isinstance(item, str) and item for item in evidence)
    ):
        errors.append("selector selection receipt evidence_signals are invalid")
        return errors
    try:
        authority = layer3_selector_authority(
            load_yaml_file(ROOT / "src" / "registry" / "foundation-skills.yaml"),
            load_yaml_file(ROOT / "src" / "registry" / "professional-skills.yaml"),
            load_yaml_file(ROOT / "src" / "registry" / "domain-skills.yaml"),
            context="selector selection receipt canonical replay",
        )
        projection = layer3_selector_runtime_projection(
            authority,
            professional_skill=expected_professional,
            profile=expected_profile,
            selection_owner=expected_owner,
            exact_layer3=(
                expected_selected_layer3
                if receipt.get("selector_ids") == ["exact-layer3-authority"]
                else None
            ),
        )
        replayed = layer3_selector_runtime_selection_receipt(
            projection,
            evidence_signals=evidence,
            build_identity=expected_build_identity,
        )
    except (OSError, ValidationProblem, ValueError) as exc:
        errors.append(
            "selector selection receipt canonical replay failed closed: "
            f"{exc}"
        )
        return errors
    if replayed["selected_layer3"] != expected_selected_layer3:
        errors.append(
            "selector selection receipt replayed selected_layer3 must equal "
            f"{expected_selected_layer3!r}"
        )
    for field in sorted(expected_fields):
        if receipt[field] != replayed[field]:
            errors.append(
                f"selector selection receipt {field} differs from canonical replay"
            )
    return errors


def layer3_selector_runtime_selection(
    projection: object,
    *,
    evidence_signals: object,
    build_identity: str,
) -> list[str]:
    """Resolve exact Layer 3 through the receipt-producing selection consumer."""

    return list(
        layer3_selector_runtime_selection_receipt(
            projection,
            evidence_signals=evidence_signals,
            build_identity=build_identity,
        )["selected_layer3"]
    )


def required_expertise_tag_errors(
    value: object,
    context: str,
    *,
    layer: str | None = None,
    skill_name: object = None,
    foundation_group: object = None,
) -> list[str]:
    """Validate canonical domain-expertise tags owned by one Skill registry row."""

    if not isinstance(value, list) or not value:
        return [f"{context}: required_expertise_tags must be a non-empty list"]
    errors: list[str] = []
    normalized: list[str] = []
    for index, item in enumerate(value):
        label = f"{context}.required_expertise_tags[{index}]"
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{label}: must be a non-empty string")
            continue
        tag = item.strip()
        normalized.append(tag)
        if EXPERTISE_TAG_RE.fullmatch(tag) is None:
            errors.append(f"{label}: must be a canonical lowercase slug")
        elif tag not in SKILL_EXPERTISE_TAGS:
            errors.append(f"{label}: unknown Skill expertise tag {tag!r}")
        if tag == SKILL_REFERENCE_ARCHITECTURE_TAG:
            errors.append(
                f"{label}: architecture qualification belongs to reviewers, not Skills"
            )
    if normalized != sorted(set(normalized)):
        errors.append(
            f"{context}: required_expertise_tags must be sorted and unique"
        )
    if layer == "foundation":
        if not isinstance(foundation_group, str) or not foundation_group.strip():
            errors.append(f"{context}: Foundation expertise requires a group")
        else:
            expected = f"foundation-{foundation_group.strip()}"
            if expected not in normalized:
                errors.append(
                    f"{context}: Foundation expertise must include group tag {expected!r}"
                )
    if layer == "domain":
        if not isinstance(skill_name, str) or not skill_name.strip():
            errors.append(f"{context}: Domain expertise requires a Skill name")
        else:
            expected = f"domain-{skill_name.strip()}"
            if expected not in normalized:
                errors.append(
                    f"{context}: Domain expertise must include Skill tag {expected!r}"
                )
    return errors


def foundation_ownership_errors(
    foundation_entries: list[dict[str, Any]],
    professional_entries: list[dict[str, Any]],
    *,
    label: str = "foundation-skills.yaml",
) -> list[str]:
    """Validate Foundation delivery scope and reciprocal Professional ownership."""

    errors: list[str] = []
    professional_entries_by_name: dict[str, list[dict[str, Any]]] = {}
    for entry in professional_entries:
        name = entry.get("name")
        if isinstance(name, str) and name:
            professional_entries_by_name.setdefault(name, []).append(entry)
    foundation_by_name = {
        entry["name"]: entry
        for entry in foundation_entries
        if isinstance(entry.get("name"), str) and entry["name"]
    }
    professional_by_name = {
        entry["name"]: entry
        for entry in professional_entries
        if isinstance(entry.get("name"), str) and entry["name"]
    }
    actual_owners: dict[str, set[str]] = {
        name: set() for name in foundation_by_name
    }
    for professional_name, professional in professional_by_name.items():
        candidates = professional.get("layer3_candidates")
        if not isinstance(candidates, list):
            continue
        for candidate in candidates:
            if isinstance(candidate, str) and candidate in actual_owners:
                actual_owners[candidate].add(professional_name)

    scope_counts = {scope: 0 for scope in FOUNDATION_DELIVERY_SCOPES}
    for foundation_name, foundation in foundation_by_name.items():
        context = f"{label}:{foundation_name}"
        scope = foundation.get("delivery_scope")
        if scope not in FOUNDATION_DELIVERY_SCOPES:
            errors.append(
                f"{context}: delivery_scope must be one of "
                f"{sorted(FOUNDATION_DELIVERY_SCOPES)}, found {scope!r}"
            )
        else:
            scope_counts[scope] += 1

        used_by_value = foundation.get("used_by")
        if not isinstance(used_by_value, list):
            errors.append(f"{context}: used_by must be a list")
            declared_owners: list[str] = []
        else:
            declared_owners = [
                owner
                for owner in used_by_value
                if isinstance(owner, str) and owner.strip()
            ]
            if len(declared_owners) != len(used_by_value):
                errors.append(
                    f"{context}: used_by must contain only non-empty Professional names"
                )
            if len(declared_owners) != len(set(declared_owners)):
                errors.append(f"{context}: used_by must not contain duplicates")
        for owner in declared_owners:
            if owner not in professional_by_name:
                errors.append(
                    f"{context}: used_by must reference a Professional Skill, found {owner!r}"
                )

        declared_set = set(declared_owners)
        actual_set = actual_owners[foundation_name]
        if declared_set != actual_set:
            errors.append(
                f"{context}: used_by must exactly match Professional layer3_candidates; "
                f"declared={sorted(declared_set)}, actual={sorted(actual_set)}"
            )

        if (
            "activation" in foundation
            and not _foundation_activation_field_errors(foundation, context)
        ):
            activation = foundation["activation"]
            primary_name = activation["primary_skill"]
            primary_matches = professional_entries_by_name.get(
                primary_name,
                [],
            )
            if len(primary_matches) != 1:
                errors.append(
                    f"{context}: activation.primary_skill must resolve to "
                    "exactly one Professional Skill"
                )
            else:
                primary = primary_matches[0]
                primary_candidates = primary.get("layer3_candidates")
                if (
                    primary_name not in declared_set
                    or not isinstance(primary_candidates, list)
                    or foundation_name not in primary_candidates
                ):
                    errors.append(
                        f"{context}: activation.primary_skill must be a "
                        "reciprocal Foundation owner"
                    )
                if primary.get("task_routable") is not True:
                    errors.append(
                        f"{context}: activation.primary_skill must be "
                        "task_routable"
                    )
                profile = activation["profile"]
                foundation_roles = foundation.get("role_support")
                primary_roles = primary.get("role_support")
                if (
                    not isinstance(foundation_roles, list)
                    or profile not in foundation_roles
                    or not isinstance(primary_roles, list)
                    or profile not in primary_roles
                ):
                    errors.append(
                        f"{context}: activation.primary_skill and Foundation "
                        "role_support must include activation.profile"
                    )

            review_name = activation["review_skill"]
            review_matches = professional_entries_by_name.get(
                review_name,
                [],
            )
            if len(review_matches) != 1:
                errors.append(
                    f"{context}: activation.review_skill must resolve to "
                    "exactly one Professional Skill"
                )
            else:
                review = review_matches[0]
                if review.get("task_routable") is not True:
                    errors.append(
                        f"{context}: activation.review_skill must be "
                        "task_routable"
                    )
                review_roles = review.get("role_support")
                if (
                    not isinstance(review_roles, list)
                    or "review-agent" not in review_roles
                ):
                    errors.append(
                        f"{context}: activation.review_skill must support "
                        "review-agent"
                    )

        if scope == "product":
            if not actual_set:
                errors.append(
                    f"{context}: product Foundation Skill must have at least one "
                    "Professional owner"
                )
            foundation_roles = {
                role
                for role in foundation.get("role_support", [])
                if isinstance(role, str)
            }
            for owner in sorted(actual_set):
                professional = professional_by_name[owner]
                if professional.get("task_routable") is not True:
                    errors.append(
                        f"{context}: product owner {owner!r} must be task_routable"
                    )
                professional_roles = {
                    role
                    for role in professional.get("role_support", [])
                    if isinstance(role, str)
                }
                if not foundation_roles & professional_roles:
                    errors.append(
                        f"{context}: product owner {owner!r} has no role_support "
                        "intersection"
                    )
        elif scope in {"authoring-only", "dev-only"} and (
            declared_set or actual_set
        ):
            errors.append(
                f"{context}: {scope} Foundation Skill must have no Professional owner"
            )

    for scope, expected in EXPECTED_FOUNDATION_DELIVERY_SCOPE_COUNTS.items():
        actual = scope_counts[scope]
        if actual != expected:
            errors.append(
                f"{label}: expected {expected} Foundation Skill(s) with "
                f"delivery_scope={scope!r}, found {actual}"
            )
    return errors


def _reference_condition_projection_error(condition: str) -> str | None:
    """Return why a JIT condition cannot be embedded in one Markdown record."""

    if "\n" in condition or "\r" in condition:
        return "must stay on one line"
    if _REFERENCE_CONDITION_RESERVED_DELIMITER_RE.search(condition):
        return "must not contain a reserved '; load' or '; skip' delimiter"
    if _REFERENCE_CONDITION_MARKDOWN_CONTROL_RE.search(condition):
        return "must not contain Markdown control characters"
    return None


def _reference_path_projection_error(path: str) -> str | None:
    """Return why a Reference path is not one canonical local projection path."""

    if _REFERENCE_PATH_PROJECTION_RE.fullmatch(path) is None:
        return (
            "must be a normalized path inside references/ using "
            "Markdown-link-safe slugs and a .md suffix"
        )
    return None


def compact_markdown_table_cell(value: str, context: str) -> str:
    """Return one canonical compact Markdown table cell.

    A literal pipe is the only escaped character. Registry contracts already
    reject backslashes in their free-text and path fields, so accepting another
    escape spelling here would create two byte representations for one value.
    """

    if not isinstance(value, str) or not value or "\n" in value or "\r" in value:
        raise ValidationProblem(
            f"{context}: compact table cell must be one non-empty line"
        )
    if "\\" in value:
        raise ValidationProblem(
            f"{context}: compact table cell must not contain backslashes"
        )
    return value.replace("|", "\\|")


def _render_compact_markdown_table_row(
    values: Iterable[str],
    context: str,
) -> str:
    cells = tuple(values)
    return (
        "| "
        + " | ".join(
            compact_markdown_table_cell(value, f"{context}[{index}]")
            for index, value in enumerate(cells)
        )
        + " |"
    )


def render_compact_markdown_table(
    columns: Iterable[str],
    rows: Iterable[Iterable[str]],
    context: str,
) -> str:
    """Render one exact compact Markdown table without a trailing newline."""

    column_values = tuple(columns)
    if not column_values:
        raise ValidationProblem(f"{context}: compact table must declare columns")
    rendered_rows: list[str] = []
    for row_index, raw_row in enumerate(rows):
        row = tuple(raw_row)
        if len(row) != len(column_values):
            raise ValidationProblem(
                f"{context}: row {row_index} has {len(row)} cell(s); "
                f"expected {len(column_values)}"
            )
        rendered_rows.append(
            _render_compact_markdown_table_row(row, f"{context}.rows[{row_index}]")
        )
    return "\n".join(
        [
            _render_compact_markdown_table_row(column_values, f"{context}.columns"),
            "|" + "|".join("---" for _column in column_values) + "|",
            *rendered_rows,
        ]
    )


def _parse_compact_markdown_table_row(
    line: str,
    column_count: int,
) -> list[str] | None:
    """Parse one row only when its escaping and spacing are canonical."""

    if not line.startswith("| ") or not line.endswith(" |"):
        return None
    payload = line[2:-2]
    cells: list[str] = []
    current: list[str] = []
    index = 0
    while index < len(payload):
        if payload.startswith(" | ", index):
            cells.append("".join(current))
            current = []
            index += 3
            continue
        character = payload[index]
        if character == "\\":
            if index + 1 >= len(payload) or payload[index + 1] != "|":
                return None
            current.append("|")
            index += 2
            continue
        if character == "|":
            return None
        current.append(character)
        index += 1
    cells.append("".join(current))
    if len(cells) != column_count:
        return None
    try:
        canonical = _render_compact_markdown_table_row(cells, "parsed compact table row")
    except ValidationProblem:
        return None
    return cells if canonical == line else None


def _targeted_reference_section_lines(
    contracts: list[dict[str, Any]],
    context: str,
) -> list[str]:
    lines = ["## Targeted References", ""]
    if not contracts:
        return [*lines, "- No task-local Reference is indexed for this Skill."]
    rows: list[tuple[str, ...]] = []
    for contract in contracts:
        path = str(contract["path"])
        rows.append(
            (
                f"[{targeted_reference_label(path)}]({path})",
                str(contract["type"]),
                str(contract["load_when"]).rstrip(" ."),
                str(contract["do_not_load_when"]).rstrip(" ."),
                ", ".join(contract["required_by"]),
                ", ".join(contract["required_output"]),
            )
        )
    table = render_compact_markdown_table(
        TARGETED_REFERENCE_TABLE_COLUMNS,
        rows,
        f"{context}.Targeted References",
    )
    return [*lines, *table.splitlines()]


def _parse_targeted_reference_projection(
    section: str,
    *,
    expected_trailing_newlines: int,
) -> list[dict[str, Any]] | None:
    """Parse only one canonical projection with its contextual terminator."""

    if "\r" in section:
        return None
    if expected_trailing_newlines not in {1, 2}:
        raise ValueError("Targeted References terminator must be one or two newlines")
    trailing_newlines = len(section) - len(section.rstrip("\n"))
    if trailing_newlines != expected_trailing_newlines:
        return None
    core = section[:-trailing_newlines]
    lines = core.split("\n")
    if len(lines) < 3 or lines[:2] != ["## Targeted References", ""]:
        return None
    records = lines[2:]
    if records == ["- No task-local Reference is indexed for this Skill."]:
        return []
    if len(records) < 3:
        return None

    expected_header = _render_compact_markdown_table_row(
        TARGETED_REFERENCE_TABLE_COLUMNS,
        "Targeted References columns",
    )
    expected_separator = (
        "|" + "|".join("---" for _column in TARGETED_REFERENCE_TABLE_COLUMNS) + "|"
    )
    if records[:2] != [expected_header, expected_separator]:
        return None

    parsed: list[dict[str, Any]] = []
    for raw_row in records[2:]:
        cells = _parse_compact_markdown_table_row(
            raw_row,
            len(TARGETED_REFERENCE_TABLE_COLUMNS),
        )
        if cells is None:
            return None
        link = _TARGETED_REFERENCE_TABLE_LINK_RE.fullmatch(cells[0])
        if link is None:
            return None
        path = link.group("path")
        if link.group("label") != targeted_reference_label(path):
            return None
        parsed.append(
            {
                "path": path,
                "type": cells[1],
                "load_when": cells[2],
                "do_not_load_when": cells[3],
                "required_by": cells[4].split(", "),
                "required_output": cells[5].split(", "),
            }
        )
    try:
        validated = reference_contracts(
            parsed,
            "Targeted References projection",
        )
        expected_core = "\n".join(
            _targeted_reference_section_lines(
                validated,
                "Targeted References projection",
            )
        )
    except ValidationProblem:
        return None
    return validated if core == expected_core else None


def reference_contracts(
    value: Any,
    label: str,
    *,
    owner: str | None = None,
) -> list[dict[str, Any]]:
    """Return one fail-closed structured Reference index.

    Reference Contract v2 deliberately rejects legacy entries so every indexed
    file carries an explicit JIT loading and consumption boundary.
    """

    if not isinstance(value, list):
        raise ValidationProblem(f"{label} must be a list")
    contracts: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(value):
        context = f"{label}[{index}]"
        if isinstance(raw, str):
            raise ValidationProblem(
                f"{context} uses a legacy string; expected a Reference Contract v2 mapping"
            )
        if not isinstance(raw, dict):
            raise ValidationProblem(f"{context} must be a mapping")
        if set(raw) != REFERENCE_CONTRACT_FIELDS:
            missing = sorted(REFERENCE_CONTRACT_FIELDS - set(raw))
            extra = sorted(set(raw) - REFERENCE_CONTRACT_FIELDS)
            raise ValidationProblem(
                f"{context} must contain exactly {sorted(REFERENCE_CONTRACT_FIELDS)}; "
                f"missing={missing}, extra={extra}"
            )
        contract: dict[str, Any] = {}
        for field in ("path", "type", "load_when", "do_not_load_when"):
            field_value = raw.get(field)
            if not isinstance(field_value, str) or not field_value.strip():
                raise ValidationProblem(f"{context}.{field} must be a non-empty string")
            if "\n" in field_value or "\r" in field_value:
                raise ValidationProblem(f"{context}.{field} must stay on one line")
            # Path bytes are projected into a Markdown link and therefore must
            # already be canonical.  Do not silently normalize surrounding
            # whitespace before the closed path grammar evaluates it.
            contract[field] = field_value if field == "path" else field_value.strip()
        for field, vocabulary in (
            ("required_by", REFERENCE_CONTRACT_ROLES),
            ("required_output", REFERENCE_OUTPUT_TYPES),
        ):
            values = raw.get(field)
            if not isinstance(values, list) or not values:
                raise ValidationProblem(f"{context}.{field} must be a non-empty list")
            if any(not isinstance(item, str) or not item.strip() for item in values):
                raise ValidationProblem(
                    f"{context}.{field} entries must be non-empty strings"
                )
            normalized_values = [item.strip() for item in values]
            if len(normalized_values) != len(set(normalized_values)):
                raise ValidationProblem(f"{context}.{field} must not contain duplicates")
            unknown = sorted(set(normalized_values) - vocabulary)
            if unknown:
                raise ValidationProblem(
                    f"{context}.{field} contains unknown value(s) {unknown}"
                )
            contract[field] = normalized_values

        path = contract["path"]
        path_error = _reference_path_projection_error(path)
        if path_error is not None:
            raise ValidationProblem(f"{context}.path {path_error}")
        if path in seen:
            raise ValidationProblem(f"{context}.path duplicates {path!r}")
        seen.add(path)

        if contract["type"] not in REFERENCE_CONTRACT_TYPES:
            raise ValidationProblem(
                f"{context}.type must be one of {sorted(REFERENCE_CONTRACT_TYPES)}"
            )
        output_type = contract["type"]
        incompatible = sorted(
            set(contract["required_output"])
            - REFERENCE_OUTPUTS_BY_TYPE[output_type]
        )
        if incompatible:
            raise ValidationProblem(
                f"{context}.required_output {incompatible} is incompatible with type "
                f"{output_type!r}"
            )
        missing_minimum = sorted(
            REFERENCE_MINIMUM_OUTPUTS_BY_TYPE[output_type]
            - set(contract["required_output"])
        )
        if missing_minimum:
            raise ValidationProblem(
                f"{context}.required_output must include {missing_minimum} for type "
                f"{output_type!r}"
            )
        for field in ("load_when", "do_not_load_when"):
            condition = contract[field]
            projection_error = _reference_condition_projection_error(condition)
            if projection_error is not None:
                raise ValidationProblem(
                    f"{context}.{field} {projection_error}"
                )
            normalized = " ".join(re.findall(r"[a-z0-9]+", condition.casefold()))
            if (
                len(re.findall(r"[A-Za-z0-9]+", condition)) < 4
                or len(condition) > 240
                or _REFERENCE_CONDITION_GENERIC_RE.fullmatch(normalized)
                or re.search(
                    r"\b(?:when|if)\s+(?:needed|required|relevant|applicable)\b|\bas needed\b",
                    condition,
                    re.IGNORECASE,
                )
            ):
                raise ValidationProblem(
                    f"{context}.{field} must be concise and task-specific, not generic"
                )
        if re.search(
            r"\bclosure\s+needs?\b.*\bchecklist\b"
            r"|\bclaims?\s+needs?\s+(?:the\s+)?evidence\s+patterns?\b"
            r"|\bdecisions?\s+needs?\s+(?:the\s+)?(?:benchmarks?\s+(?:and\s+)?patterns?|patterns?)\b",
            contract["load_when"],
            re.IGNORECASE,
        ):
            raise ValidationProblem(
                f"{context}.load_when uses a forbidden generic role template"
            )
        if re.search(
            r"\broot\s+(?:already\s+)?(?:resolves?|closes?|bounds?|defines?)\b",
            contract["do_not_load_when"],
            re.IGNORECASE,
        ):
            raise ValidationProblem(
                f"{context}.do_not_load_when must state a real anti-condition"
            )
        for field in ("load_when", "do_not_load_when"):
            condition = contract[field]
            if _REFERENCE_MECHANICAL_TRIPLET_RE.fullmatch(condition):
                raise ValidationProblem(
                    f"{context}.{field} uses a forbidden mechanical JIT template"
                )
            if any(pattern.search(condition) for pattern in _REFERENCE_BROKEN_CONDITION_RES):
                raise ValidationProblem(
                    f"{context}.{field} contains a truncated or malformed JIT condition"
                )
        if _normalized_contract_condition(contract["load_when"]) == _normalized_contract_condition(
            contract["do_not_load_when"]
        ):
            raise ValidationProblem(
                f"{context}.load_when and do_not_load_when must express different boundaries"
            )
        if owner == "engineering-control-plane":
            expected_by = REFERENCE_CONTRACT_MODEL["control_required_by"].get(path)
            expected_output = REFERENCE_CONTRACT_MODEL["control_required_output"].get(path)
            if contract["required_by"] != expected_by:
                raise ValidationProblem(
                    f"{context}.required_by must equal the control-model consumer {expected_by}"
                )
            if contract["required_output"] != expected_output:
                raise ValidationProblem(
                    f"{context}.required_output must equal the control-model output {expected_output}"
                )
        contracts.append(contract)
    return contracts


def reference_paths(value: Any, label: str, *, owner: str | None = None) -> list[str]:
    """Return structured Reference paths after validating the complete contract."""

    return [item["path"] for item in reference_contracts(value, label, owner=owner)]


def targeted_reference_label(path: str) -> str:
    """Return the stable human label used by source and built projections."""

    stem = PurePosixPath(path).stem
    if stem in {"benchmarks-and-patterns", "evidence-patterns"}:
        return stem.replace("-", " ")
    for suffix in ("-template", "-checklist", "-patterns"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
            break
    return stem.replace("-", " ")


def render_targeted_reference_section(
    markdown: str,
    contracts: list[dict[str, Any]],
    owner: str,
) -> str:
    """Project the Registry-owned JIT contracts into one root Markdown section."""

    contracts = reference_contracts(
        contracts,
        f"{owner}.reference_index",
        owner=owner,
    )
    matches = list(_TARGETED_REFERENCES_SECTION_RE.finditer(markdown))
    if len(matches) != 1:
        raise ValidationProblem(
            f"{owner}: expected exactly one Targeted References section, "
            f"found {len(matches)}"
        )
    lines = _targeted_reference_section_lines(contracts, owner)
    match = matches[0]
    suffix = markdown[match.end():]
    # Keep one final newline at EOF.  When another section follows, preserve
    # one blank line before its heading.  This makes ordinary source edits and
    # the synchronization command converge on the same representation.
    replacement = "\n".join(lines) + ("\n\n" if suffix else "\n")
    return f"{markdown[:match.start()]}{replacement}{suffix}"


def strip_registry_targeted_reference_projection(markdown: str) -> str:
    """Blank one canonical Registry projection while preserving line offsets."""

    matches = list(_TARGETED_REFERENCES_SECTION_RE.finditer(markdown))
    if len(matches) != 1:
        return markdown
    match = matches[0]
    section = match.group(0)
    lines = section.splitlines(keepends=True)
    if not lines or lines[0].strip() != "## Targeted References":
        return markdown
    expected_trailing_newlines = 1 if match.end() == len(markdown) else 2
    if _parse_targeted_reference_projection(
        section,
        expected_trailing_newlines=expected_trailing_newlines,
    ) is None:
        return markdown
    blank = "".join(
        "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""
        for line in lines
    )
    return f"{markdown[:match.start()]}{blank}{markdown[match.end():]}"


def registry_targeted_reference_projection_line_count(markdown: str) -> int:
    """Return physical lines owned by one canonical Registry projection.

    The count deliberately reuses the same closed parser as projection stripping.
    A malformed, missing, or repeated section is authored content and therefore
    contributes no Registry-owned projection overhead.
    """

    matches = list(_TARGETED_REFERENCES_SECTION_RE.finditer(markdown))
    if len(matches) != 1:
        return 0
    match = matches[0]
    section = match.group(0)
    expected_trailing_newlines = 1 if match.end() == len(markdown) else 2
    if _parse_targeted_reference_projection(
        section,
        expected_trailing_newlines=expected_trailing_newlines,
    ) is None:
        return 0
    return len(section.splitlines())


def _canonical_frontmatter_body_projection_source(
    body_fragment: str,
    raw_source: str,
) -> str | None:
    """Reconstruct raw body Markdown only from a proven canonical source."""

    if (
        "\r" in raw_source
        or not raw_source.endswith("\n")
        or raw_source.endswith("\n\n")
        or not raw_source.endswith(body_fragment + "\n")
    ):
        return None
    lines = raw_source.splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_DELIMITER:
        return None
    end_index = next(
        (
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.strip() == FRONTMATTER_DELIMITER
        ),
        None,
    )
    if end_index is None:
        return None
    if "\n".join(lines[end_index + 1 :]) != body_fragment:
        return None
    return body_fragment + "\n"


def strip_frontmatter_body_targeted_reference_projection(
    body_fragment: str,
    raw_source: str,
) -> str:
    """Blank canonical projection metadata from one proven body fragment.

    ``parse_frontmatter`` deliberately returns a newline-free body fragment.
    This adapter restores its terminator only after the original source proves
    exact one-newline EOF canonicality and exact fragment provenance.
    """

    markdown = _canonical_frontmatter_body_projection_source(
        body_fragment,
        raw_source,
    )
    if markdown is None:
        return body_fragment
    stripped = strip_registry_targeted_reference_projection(markdown)
    if stripped == markdown:
        return body_fragment
    return stripped


def frontmatter_body_targeted_reference_projection_line_count(
    body_fragment: str,
    raw_source: str,
) -> int:
    """Count projection lines only for a proven canonical body fragment."""

    markdown = _canonical_frontmatter_body_projection_source(
        body_fragment,
        raw_source,
    )
    if markdown is None:
        return 0
    return registry_targeted_reference_projection_line_count(markdown)


def _ai_source_span(
    markdown: str, *, start_offset: int, end_offset: int
) -> dict[str, object]:
    """Bind a codepoint half-open range to exact continuous document-part lines."""

    if not 0 <= start_offset < end_offset <= len(markdown):
        raise AssertionError("AI readability source span is outside its context")
    lines = markdown.splitlines()
    starts: list[int] = []
    cursor = 0
    for line in markdown.splitlines(keepends=True):
        starts.append(cursor)
        cursor += len(line)
    if markdown and (not starts or cursor < len(markdown)):
        starts.append(cursor)
    start_index = max(
        index for index, offset in enumerate(starts) if offset <= start_offset
    )
    end_character = end_offset - 1
    end_index = max(
        index for index, offset in enumerate(starts) if offset <= end_character
    )
    span_lines = lines[start_index : end_index + 1]
    absolute_start = start_index + 1
    numbered = [
        {"line": absolute_start + index, "text": text}
        for index, text in enumerate(span_lines)
    ]
    return {
        "start_offset": start_offset,
        "end_offset": end_offset,
        "start_line": absolute_start,
        "end_line": absolute_start + len(numbered) - 1,
        "start_column": start_offset - starts[start_index] + 1,
        "end_column": end_offset - starts[end_index] + 1,
        "lines": numbered,
        "sha256": hashlib.sha256(
            markdown[start_offset:end_offset].encode("utf-8")
        ).hexdigest(),
    }


def _ai_markdown_units(
    markdown: str, *, line_offset: int = 0
) -> list[dict[str, object]]:
    """Return canonical logical units with exact continuous source spans."""

    units: list[dict[str, object]] = []
    line_starts: list[int] = []
    cursor = 0
    for raw_with_ending in markdown.splitlines(keepends=True):
        line_starts.append(cursor)
        cursor += len(raw_with_ending)
    current_kind: str | None = None
    current_line = 0
    current_indent = 0
    current_parts: list[tuple[int, str, int]] = []
    in_fence = False
    fence_prefix: str | None = None
    in_comment = False

    def flush() -> None:
        nonlocal current_kind, current_line, current_indent, current_parts
        normalized_parts: list[str] = []
        segments: list[dict[str, int]] = []
        offset_map: list[int] = []
        cursor = 0
        for source_line, fragment, raw_column in current_parts:
            token_matches = list(re.finditer(r"\S+", fragment))
            normalized = " ".join(match.group(0) for match in token_matches)
            if not normalized:
                continue
            if normalized_parts:
                cursor += 1
                offset_map.append(offset_map[-1] + 1)
            start_offset = cursor
            normalized_parts.append(normalized)
            for token_index, match in enumerate(token_matches):
                if token_index:
                    offset_map.append(
                        line_starts[source_line - 1]
                        + raw_column
                        + match.start()
                        - 1
                    )
                    cursor += 1
                token_start = (
                    line_starts[source_line - 1] + raw_column + match.start()
                )
                offset_map.extend(
                    token_start + index for index in range(len(match.group(0)))
                )
                cursor += len(match.group(0))
            segments.append(
                {
                    "start_offset": start_offset,
                    "end_offset": cursor,
                    "line": source_line,
                }
            )
        text = " ".join(normalized_parts)
        if current_kind is not None and text:
            units.append(
                {
                    "kind": current_kind,
                    "line": current_line,
                    "line_offset": line_offset,
                    "text": text,
                    "canonical_text": text,
                    "source_span": _ai_source_span(
                        markdown,
                        start_offset=offset_map[0],
                        end_offset=offset_map[-1] + 1,
                    ),
                    "segments": segments,
                    "offset_map": offset_map,
                    "_markdown": markdown,
                    "_line_offset": line_offset,
                }
            )
        current_kind = None
        current_line = 0
        current_indent = 0
        current_parts = []

    for line_number, raw_line in enumerate(markdown.splitlines(), start=1):
        stripped = raw_line.strip()
        fence_match = _AI_FENCE_RE.match(raw_line)
        if fence_match:
            flush()
            marker = fence_match.group(1)[:3]
            if not in_fence:
                in_fence = True
                fence_prefix = marker
            elif fence_prefix == marker:
                in_fence = False
                fence_prefix = None
            continue
        if in_fence:
            continue
        if in_comment:
            if "-->" in raw_line:
                in_comment = False
            continue
        if stripped.startswith("<!--"):
            flush()
            in_comment = "-->" not in stripped
            continue
        if (
            not stripped
            or _AI_HEADING_RE.match(raw_line)
            or (stripped.startswith("|") and stripped.count("|") >= 2)
        ):
            flush()
            continue

        list_match = _AI_LIST_ITEM_RE.match(raw_line)
        if list_match:
            flush()
            current_kind = "list-item"
            current_line = line_number
            current_indent = len(list_match.group("indent").expandtabs(4)) + 2
            current_parts = [
                (
                    line_number,
                    list_match.group("text"),
                    list_match.start("text"),
                )
            ]
            continue

        line_indent = len(raw_line) - len(raw_line.lstrip(" \t"))
        fragment = re.sub(r"^>\s*", "", stripped)
        raw_column = raw_line.find(fragment)
        if raw_column < 0:  # pragma: no cover - fragment is derived from raw_line
            raise AssertionError("Markdown fragment is absent from its source line")
        if current_kind == "list-item" and line_indent >= current_indent:
            current_parts.append((line_number, fragment, raw_column))
            continue
        if current_kind == "paragraph":
            current_parts.append((line_number, fragment, raw_column))
            continue
        flush()
        current_kind = "paragraph"
        current_line = line_number
        current_parts = [(line_number, fragment, raw_column)]

    flush()
    return units


def _ai_sentence_records(text: str) -> list[dict[str, object]]:
    """Split prose while preserving each canonical sentence's exact offsets."""

    sentences: list[dict[str, object]] = []
    start = 0
    for boundary in _AI_SENTENCE_BOUNDARY_RE.finditer(text):
        prefix = text[: boundary.start()].casefold()
        abbreviation = re.search(
            r"(?:^|[^a-z0-9])([a-z]+(?:\.[a-z]+)*)\.$", prefix
        )
        if (
            abbreviation is not None
            and f"{abbreviation.group(1)}." in _AI_SENTENCE_ABBREVIATIONS
        ):
            continue
        if re.search(r"(?:^|\s)[a-z]\.$", prefix):
            continue
        raw_start = start
        raw_end = boundary.start()
        while raw_start < raw_end and text[raw_start].isspace():
            raw_start += 1
        while raw_end > raw_start and text[raw_end - 1].isspace():
            raw_end -= 1
        value = text[raw_start:raw_end]
        if value:
            sentences.append(
                {
                    "sentence": value,
                    "start_offset": raw_start,
                    "end_offset": raw_end,
                }
            )
        start = boundary.end()
    raw_start = start
    raw_end = len(text)
    while raw_start < raw_end and text[raw_start].isspace():
        raw_start += 1
    while raw_end > raw_start and text[raw_end - 1].isspace():
        raw_end -= 1
    value = text[raw_start:raw_end]
    if value:
        sentences.append(
            {
                "sentence": value,
                "start_offset": raw_start,
                "end_offset": raw_end,
            }
        )
    return sentences


def _ai_sentence_slices(text: str) -> list[str]:
    """Compatibility projection of canonical sentence text only."""

    return [str(row["sentence"]) for row in _ai_sentence_records(text)]


def _ai_unit_slice_source_span(
    unit: dict[str, object], *, start_offset: int, end_offset: int
) -> dict[str, object]:
    """Project one unit substring onto continuous exact document-part lines."""

    offset_map = unit["offset_map"]
    assert isinstance(offset_map, list)
    if not 0 <= start_offset < end_offset <= len(offset_map):
        raise AssertionError("canonical sentence slice is outside its Markdown unit")
    span = unit["source_span"]
    assert isinstance(span, dict)
    raw_start = int(offset_map[start_offset])
    raw_end = int(offset_map[end_offset - 1]) + 1
    markdown = str(unit["_markdown"])
    return _ai_source_span(
        markdown,
        start_offset=raw_start,
        end_offset=raw_end,
    )


def ai_sentence_word_count(sentence: str) -> int:
    """Count prose words while treating links and inline code as AI atoms."""

    normalized = _AI_INLINE_LINK_RE.sub(lambda match: match.group(1), sentence)
    normalized = _AI_INLINE_CODE_RE.sub(" CODE ", normalized)
    normalized = re.sub(r"[*_~>]", " ", normalized)
    return len(_AI_WORD_RE.findall(normalized))


def ai_markdown_list_sentence_counts(markdown: str) -> list[dict[str, object]]:
    """Return sentence counts for logical Markdown list items."""

    counts: list[dict[str, object]] = []
    for unit in _ai_markdown_units(markdown):
        if unit["kind"] != "list-item":
            continue
        text = _ai_readability_payload(str(unit["text"]))
        counts.append(
            {
                "line": int(unit["line"]),
                "sentences": len(_ai_sentence_slices(text)),
                "text": text,
            }
        )
    return counts


def _ai_standalone_exception(text: str) -> bool:
    stripped = text.strip()
    if re.fullmatch(r"`[^`\n]+`[.!]?", stripped):
        return True
    plain = re.sub(r"^[`*_~]+|[`*_~]+$", "", stripped).strip()
    if _AI_STANDALONE_COMMAND_RE.match(plain):
        return True
    # A pure field/term enumeration has no governing prose decision.  It may
    # contain many exact names without becoming one long executable sentence.
    if (
        not re.search(
            rf"\b(?:must|never|do\s+not|{_AI_DECISION_ACTION_ALT})\b",
            plain,
            re.IGNORECASE,
        )
        and len(re.findall(r"[,;]", plain)) >= 4
        and not re.search(r"[.!?]", plain)
    ):
        return True
    return False


def _ai_decision_clause_count(text: str) -> int:
    """Count independently governed obligations in one logical Bullet."""

    # A bold leading label names the Bullet's one primary decision. Supporting
    # clauses remain governed, but the label itself is not a second execution
    # instruction.
    plain = _AI_LEADING_DECISION_LABEL_RE.sub("", text)
    plain = re.sub(r"[`*_~]", "", plain)
    execution_clauses = 0
    for sentence in _ai_sentence_slices(plain):
        logical_clauses = [
            clause.strip()
            for clause in _AI_LOGICAL_CLAUSE_SPLIT_RE.split(sentence)
            if clause.strip()
        ]
        for clause in logical_clauses:
            # A logical clause contributes at most one decision. This avoids
            # double-counting a leading command such as ``Escalate`` or a proof
            # statement whose governed predicate contains ``never``.
            if _AI_LEADING_DECISION_ACTION_RE.match(
                clause
            ) or _AI_HARD_OBLIGATION_RE.search(clause):
                execution_clauses += 1

    decision_clauses = execution_clauses

    # Candidate menus are a separate decision only when the same Bullet already
    # owns another executable obligation. A standalone menu remains one decision.
    candidate_menu = bool(_AI_CANDIDATE_MENU_RE.search(plain))
    if candidate_menu and decision_clauses:
        decision_clauses += 1

    # This three-part shape repeatedly hid several decisions in Domain roots:
    # enumerate mechanisms, state how selection changes, then append an
    # applicability exception. It is compound even when written declaratively.
    if (
        candidate_menu
        and _AI_CANDIDATE_SELECTION_RE.search(plain)
        and _AI_APPLICABILITY_EXCEPTION_RE.search(plain)
    ):
        decision_clauses = max(decision_clauses, 2)
    return decision_clauses


def _ai_readability_payload(text: str) -> str:
    """Remove only canonical Reference projection labels from governed prose."""

    match = _AI_TARGETED_REFERENCE_METADATA_RE.fullmatch(text.strip())
    return match.group("body") if match is not None else text


def _ai_readability_payload_with_offset(text: str) -> tuple[str, int]:
    """Return governed prose and its start in the canonical Markdown unit."""

    payload = _ai_readability_payload(text)
    if payload == text:
        return payload, 0
    offset = text.find(payload)
    if offset < 0:  # pragma: no cover - fullmatch-derived payload is a substring
        raise AssertionError("readability payload is not in its canonical unit")
    return payload, offset


def ai_readability_findings(
    markdown: str,
    context: str,
    *,
    check_bullets: bool = True,
    line_offset: int = 0,
) -> list[dict[str, object]]:
    """Return deterministic findings with canonical text and exact source spans."""

    findings: list[dict[str, object]] = []
    for unit in _ai_markdown_units(markdown, line_offset=line_offset):
        text = str(unit["text"])
        governed_text, governed_offset = _ai_readability_payload_with_offset(text)
        sentence_records = _ai_sentence_records(governed_text)
        for sentence_record in sentence_records:
            sentence = str(sentence_record["sentence"])
            if _ai_standalone_exception(sentence):
                continue
            words = ai_sentence_word_count(sentence)
            if words <= AI_SENTENCE_TARGET_WORDS:
                band = "target"
            elif words <= AI_COMPLEX_SENTENCE_TARGET_WORDS:
                band = "review-as-complex"
            elif words <= AI_SENTENCE_HARD_WORDS:
                band = "tighten"
            else:
                band = "hard-fail"
            if band != "target":
                source_span = _ai_unit_slice_source_span(
                    unit,
                    start_offset=(
                        governed_offset + int(sentence_record["start_offset"])
                    ),
                    end_offset=(
                        governed_offset + int(sentence_record["end_offset"])
                    ),
                )
                findings.append(
                    {
                        "kind": "sentence-length",
                        "severity": "error" if band == "hard-fail" else "advisory",
                        "context": context,
                        "line": source_span["start_line"],
                        "words": words,
                        "band": band,
                        "sentence": sentence,
                        "source_span": source_span,
                    }
                )
        if (
            check_bullets
            and unit["kind"] == "list-item"
            and not _ai_standalone_exception(governed_text)
        ):
            decisions = _ai_decision_clause_count(governed_text)
            if decisions > 1:
                source_span = _ai_unit_slice_source_span(
                    unit,
                    start_offset=governed_offset,
                    end_offset=governed_offset + len(governed_text),
                )
                findings.append(
                    {
                        "kind": "bullet-decisions",
                        "severity": "error",
                        "context": context,
                        "line": source_span["start_line"],
                        "decisions": decisions,
                        "sentence": governed_text,
                        "source_span": source_span,
                    }
                )
    return findings


def validate_ai_readability(
    markdown: str,
    context: str,
    errors: list[str],
    *,
    check_bullets: bool = True,
) -> list[dict[str, object]]:
    """Append blocking readability findings and return all review bands."""

    findings = ai_readability_findings(
        markdown, context, check_bullets=check_bullets
    )
    for finding in findings:
        if finding["severity"] != "error":
            continue
        if finding["kind"] == "sentence-length":
            errors.append(
                f"{context}:{finding['line']}: sentence has {finding['words']} words; "
                f"hard maximum is {AI_SENTENCE_HARD_WORDS}"
            )
        else:
            errors.append(
                f"{context}:{finding['line']}: Bullet carries "
                f"{finding['decisions']} independent decision clauses; maximum is 1"
            )
    return findings


_REFERENCE_EXACT_TYPE_BY_STEM = {
    "clean-checkout": "evidence-pattern",
    "execution-report-and-gates": "template",
    "simplicity-ladder": "benchmark-pattern",
}


def reference_type_for_path(path: str) -> str:
    """Infer the canonical Reference contract type from its authored role."""

    relative = PurePosixPath(path)
    stem = relative.stem.casefold()
    lowered_parts = {part.casefold() for part in relative.parts}
    exact_type = _REFERENCE_EXACT_TYPE_BY_STEM.get(stem)
    if exact_type is not None:
        return exact_type
    if "_template" in lowered_parts or "template" in stem:
        return "template"
    if stem == "index":
        return "index"
    if stem in {
        "professional-modes",
        "implementation-preparation",
        "diagnosis-only",
        "source-backed-answer",
    }:
        return "mode-contract"
    if "checklist" in stem:
        return "decision-checklist"
    if "evidence" in stem:
        return "evidence-pattern"
    if any(marker in stem for marker in ("benchmark", "pattern", "catalog")):
        return "benchmark-pattern"
    return "targeted"


def _normalized_contract_condition(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))


def reference_contract_has_owner_anchor(
    contract: dict[str, str], owner: str, owner_context: str
) -> bool:
    """Require Foundation JIT conditions to name their actual decision surface."""

    path_stem = PurePosixPath(contract["path"]).stem
    anchors = {
        token
        for token in re.findall(
            r"[a-z0-9]+", f"{owner} {path_stem} {owner_context}".casefold()
        )
        if len(token) >= 4 and token not in _REFERENCE_ANCHOR_STOP_WORDS
    }
    if not anchors:
        return True
    for field in ("load_when", "do_not_load_when"):
        words = set(re.findall(r"[a-z0-9]+", contract[field].casefold()))
        if not words & anchors:
            return False
    return True


def count_nonblank_lines(text: str) -> int:
    """Count effective lines, excluding blank and whitespace-only lines."""

    return sum(1 for line in text.splitlines() if line.strip())


@lru_cache(maxsize=1)
def _o200k_base_encoding() -> Any:
    """Return the canonical tokenizer required by control-context budgets."""

    try:
        import tiktoken
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "exact o200k_base token counting requires the 'tiktoken' package"
        ) from exc
    return tiktoken.get_encoding("o200k_base")


def count_o200k_base_tokens(text: str) -> int:
    """Count exact canonical o200k_base tokens without an estimation fallback."""

    return len(_o200k_base_encoding().encode(text, disallowed_special=()))


def normalized_non_heading_lines(
    markdown: str,
    *,
    minimum_length: int = 50,
) -> set[str]:
    """Return long non-heading lines normalized for copy detection."""

    normalized: set[str] = set()
    for line in markdown.splitlines():
        if re.match(r"^\s{0,3}#{1,6}(?:\s+|$)", line):
            continue
        folded = " ".join(line.casefold().split())
        if len(folded) >= minimum_length:
            normalized.add(folded)
    return normalized


def shared_normalized_non_heading_lines(
    first: str,
    second: str,
    *,
    minimum_length: int = 50,
    allowed_lines: Iterable[str] = (),
) -> list[str]:
    """Find identical normalized long lines shared by two Markdown documents."""

    allowed = {" ".join(line.casefold().split()) for line in allowed_lines}
    shared = normalized_non_heading_lines(
        first,
        minimum_length=minimum_length,
    ) & normalized_non_heading_lines(second, minimum_length=minimum_length)
    return sorted(shared - allowed)


def role_contract_map_errors(
    value: Any,
    roles: Iterable[str],
    label: str,
) -> list[str]:
    """Validate a role-keyed string-list contract uniformly across surfaces."""

    role_list = [str(role) for role in roles]
    if len(role_list) <= 1:
        if value in (None, {}):
            return []
        return [f"{label} must be absent or empty for a single-role Skill"]
    if not isinstance(value, dict):
        return [f"{label} must be a mapping for a multi-role Skill"]
    errors: list[str] = []
    if set(value) != set(role_list):
        errors.append(f"{label} keys must exactly match role_support {role_list}")
    for role in role_list:
        items = value.get(role)
        if not isinstance(items, list) or not items:
            errors.append(f"{label}.{role} must be a non-empty string list")
            continue
        if any(not isinstance(item, str) or not item.strip() for item in items):
            errors.append(f"{label}.{role} must contain non-empty strings")
        if len(items) != len(set(items)):
            errors.append(f"{label}.{role} must not contain duplicates")
    return errors


def read_text_preserve_newlines(path: Path) -> str:
    """Read UTF-8 text without translating on-disk newline sequences."""

    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def relpath(root: Path, path: Path) -> str:
    return str(path.relative_to(root))


def fail_many(label: str, errors: Iterable[str]) -> int:
    items = list(errors)
    if not items:
        return 0
    for message in items:
        print(f"{label}: ERROR: {message}", file=sys.stderr)
    return 1


def visible_child_dirs(
    root: Path,
    *,
    excluded_prefixes: tuple[str, ...] = (".",),
    excluded_names: tuple[str, ...] = (),
) -> list[Path]:
    if not root.is_dir():
        return []
    return [
        path
        for path in sorted(root.iterdir())
        if path.is_dir()
        and not path.name.startswith(excluded_prefixes)
        and path.name not in excluded_names
    ]


def validate_expected_count(
    errors: list[str],
    label: str,
    actual: int,
    expected: int,
    context: str,
) -> None:
    if actual != expected:
        errors.append(f"{context}: expected {expected} {label}, found {actual}")


def _parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if value == "":
        return ""
    if value in {"[]", "[ ]"}:
        return []
    if value in {"{}", "{ }"}:
        return {}
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if value.lower() in {"null", "~"}:
        return None
    if value.startswith('"') and value.endswith('"'):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    if value.startswith("{") and value.endswith("}"):
        inner = value[1:-1].strip()
        if not inner:
            return {}
        result: dict[str, Any] = {}
        for part in _split_inline_items(inner):
            if ":" not in part:
                return value
            key, item_value = part.split(":", 1)
            result[key.strip().strip("'\"")] = _parse_scalar(item_value)
        return result
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(part) for part in _split_inline_items(inner)]
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value


def _split_inline_items(value: str) -> list[str]:
    """Split a flow-style YAML list or mapping at top-level commas."""
    items: list[str] = []
    start = 0
    depth = 0
    quote: str | None = None
    escaped = False
    for index, character in enumerate(value):
        if quote is not None:
            if escaped:
                escaped = False
            elif character == "\\" and quote == '"':
                escaped = True
            elif character == quote:
                quote = None
            continue
        if character in {"'", '"'}:
            quote = character
        elif character in "[{(":
            depth += 1
        elif character in "]})":
            depth = max(0, depth - 1)
        elif character == "," and depth == 0:
            items.append(value[start:index].strip())
            start = index + 1
    items.append(value[start:].strip())
    return [item for item in items if item]


def _is_yaml_list_marker(content: str) -> bool:
    return content == "-" or content.startswith("- ")


def _is_block_scalar(value: str) -> bool:
    """A YAML block scalar indicator; only the indicator is retained."""
    return value[:1] in {"|", ">"}


def _yaml_significant_lines(text: str) -> list[tuple[int, str]]:
    """Return (indent, stripped-content) for each structural YAML line.

    Blank lines, top-level comments, and frontmatter delimiters are dropped so
    the recursive parser sees only structural lines. Indented comment-looking
    lines are retained because YAML block scalars often contain Markdown
    headings such as "# Implementation Plan".
    """
    lines: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped == FRONTMATTER_DELIMITER:
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if indent == 0 and stripped.startswith("#"):
            continue
        lines.append((indent, stripped))
    return lines


def _simple_yaml_load(text: str) -> dict[str, Any]:
    """Parse the indentation-based YAML subset used by rd-skills assets.

    Supports nested mappings, lists of scalars, lists of mappings (whose items
    may carry nested mapping values), and simple block scalars to any depth.
    PyYAML is still preferred when available; this keeps the validation,
    routing, and telemetry tooling free of a hard YAML dependency.
    """
    value, _ = _parse_yaml_block(_yaml_significant_lines(text), 0, 0)
    return value if isinstance(value, dict) else {}


def _parse_yaml_block(
    lines: list[tuple[int, str]], start: int, indent: int
) -> tuple[Any, int]:
    if start >= len(lines):
        return {}, start
    if _is_yaml_list_marker(lines[start][1]):
        return _parse_yaml_list(lines, start, indent)
    return _parse_yaml_map(lines, start, indent)


def _parse_yaml_map(
    lines: list[tuple[int, str]], start: int, indent: int
) -> tuple[dict[str, Any], int]:
    result: dict[str, Any] = {}
    index = start
    while index < len(lines):
        line_indent, content = lines[index]
        if line_indent < indent or _is_yaml_list_marker(content):
            break
        if line_indent > indent or ":" not in content:
            index += 1
            continue
        key, raw_value = content.split(":", 1)
        key = key.strip()
        value = raw_value.strip()
        if value:
            index += 1
            if _is_block_scalar(value):
                block_entries: list[tuple[int, str]] = []
                while index < len(lines) and lines[index][0] > indent:
                    block_entries.append(lines[index])
                    index += 1
                min_indent = min((line_indent for line_indent, _ in block_entries), default=indent + 2)
                result[key] = "\n".join(
                    (" " * max(0, line_indent - min_indent)) + content
                    for line_indent, content in block_entries
                )
            else:
                result[key] = _parse_scalar(value)
            continue
        index += 1
        if index < len(lines) and lines[index][0] > indent:
            child, index = _parse_yaml_block(lines, index, lines[index][0])
            result[key] = child
        else:
            # Match the historical fallback: an empty root key is an empty
            # mapping, an empty nested key is an empty (scalar child) list.
            result[key] = {} if indent == 0 else []
    return result, index


def _parse_yaml_list(
    lines: list[tuple[int, str]], start: int, indent: int
) -> tuple[list[Any], int]:
    items: list[Any] = []
    index = start
    while index < len(lines):
        line_indent, content = lines[index]
        if line_indent != indent or not _is_yaml_list_marker(content):
            break
        remainder = content[1:].strip()
        index += 1
        child_lines: list[tuple[int, str]] = []
        while index < len(lines) and lines[index][0] > indent:
            child_lines.append(lines[index])
            index += 1
        if not remainder:
            if child_lines:
                value, _ = _parse_yaml_block(child_lines, 0, child_lines[0][0])
                items.append(value)
            else:
                items.append(None)
        elif ":" in remainder and remainder[:1] not in {"'", '"', "[", "{"}:
            # A mapping item: the inline key shares the dash line, so re-anchor
            # it (and any continuation keys) one block level deeper.
            synthesized = [(indent + 2, remainder), *child_lines]
            value, _ = _parse_yaml_block(synthesized, 0, indent + 2)
            items.append(value)
        else:
            items.append(_parse_scalar(remainder))
    return items, index


def load_yaml_text(text: str, path: Path) -> Any:
    if _yaml is not None:
        try:
            loaded = _yaml.safe_load(text)
        except Exception as exc:  # pragma: no cover - parser-specific
            raise ValidationProblem(f"invalid YAML in {path}: {exc}") from exc
        return {} if loaded is None else loaded

    return _simple_yaml_load(text)


def load_yaml_file(path: Path) -> Any:
    return load_yaml_text(path.read_text(encoding="utf-8"), path)


def professional_routing_authority(
    path: Path | None = None,
) -> dict[str, object]:
    """Project route roles and Layer 3 candidates from the Professional registry."""

    registry_path = (
        ROOT / "src" / "registry" / "professional-skills.yaml"
        if path is None
        else path
    )
    data = load_yaml_file(registry_path)
    if not isinstance(data, dict):
        raise ValidationProblem(
            f"{registry_path}: Professional registry must be an object"
        )
    errors = professional_automatic_routing_contract_errors(
        data,
        str(registry_path),
    )
    if errors:
        raise ValidationProblem("; ".join(errors))
    entries = data.get("professional_skills")
    if not isinstance(entries, list) or not entries:
        raise ValidationProblem(
            f"{registry_path}: professional_skills must be a non-empty list"
        )

    primary_by_profile: dict[str, list[str]] = {
        role: []
        for role in ROLE_CONTRACT_MODEL
        if role != "main-control-agent"
    }
    review_skills: list[str] = []
    layer3_by_primary: dict[str, list[str]] = {}
    seen_names: set[str] = set()
    for index, entry in enumerate(entries):
        context = f"{registry_path}:professional_skills[{index}]"
        if not isinstance(entry, dict):
            raise ValidationProblem(f"{context}: must be an object")
        name = entry.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValidationProblem(f"{context}.name must be non-empty text")
        if name in seen_names:
            raise ValidationProblem(
                f"{registry_path}: Professional Skill names must be unique"
            )
        seen_names.add(name)
        roles = entry.get("role_support")
        if not isinstance(roles, list) or any(
            not isinstance(role, str) or role not in ROLE_CONTRACT_MODEL
            for role in roles
        ):
            raise ValidationProblem(
                f"{context}.role_support must contain only known profiles"
            )
        if len(roles) != len(set(roles)):
            raise ValidationProblem(f"{context}.role_support must be unique")
        candidates = entry.get("layer3_candidates")
        if not isinstance(candidates, list) or any(
            not isinstance(candidate, str) or not candidate.strip()
            for candidate in candidates
        ):
            raise ValidationProblem(
                f"{context}.layer3_candidates must contain non-empty Skill names"
            )
        if len(candidates) != len(set(candidates)):
            raise ValidationProblem(
                f"{context}.layer3_candidates must not contain duplicates"
            )
        if entry.get("task_routable") is True:
            for role in primary_by_profile:
                if role in roles:
                    primary_by_profile[role].append(name)
            layer3_by_primary[name] = list(candidates)
        if "review-agent" in roles:
            review_skills.append(name)

    return {
        "primary_skills_by_profile": {
            role: sorted(names)
            for role, names in primary_by_profile.items()
        },
        "review_skills": sorted(review_skills),
        "layer3_candidates_by_primary": {
            name: layer3_by_primary[name]
            for name in sorted(layer3_by_primary)
        },
    }


def load_professional_coverage_policy(
    path: Path,
    *,
    known_skills: set[str] | None = None,
) -> dict[str, Any]:
    """Load the one typed Professional coverage decision from release policy."""

    data = load_yaml_file(path)
    if not isinstance(data, dict):
        raise ValidationProblem(f"{path}: release review config must be a mapping")
    decisions = data.get("decisions")
    if not isinstance(decisions, list):
        raise ValidationProblem(f"{path}: decisions must be a list")
    matches = [
        item
        for item in decisions
        if isinstance(item, dict)
        and item.get("kind") == PROFESSIONAL_COVERAGE_DECISION_KIND
    ]
    if len(matches) != 1:
        raise ValidationProblem(
            f"{path}: expected exactly one {PROFESSIONAL_COVERAGE_DECISION_KIND!r} "
            f"decision, found {len(matches)}"
        )
    decision = matches[0]
    expected_fields = {"id", "kind", "schema_version", "requirements"}
    if set(decision) != expected_fields:
        missing = sorted(expected_fields - set(decision))
        extra = sorted(set(decision) - expected_fields)
        raise ValidationProblem(
            f"{path}: Professional coverage decision fields must exactly match "
            f"{sorted(expected_fields)}; missing={missing}, extra={extra}"
        )
    decision_id = decision.get("id")
    if not isinstance(decision_id, str) or not NAME_RE.fullmatch(decision_id):
        raise ValidationProblem(
            f"{path}: Professional coverage decision id must be a kebab-case name"
        )
    if decision.get("schema_version") != 1:
        raise ValidationProblem(
            f"{path}: Professional coverage decision schema_version must equal 1"
        )
    raw_requirements = decision.get("requirements")
    if not isinstance(raw_requirements, dict) or not raw_requirements:
        raise ValidationProblem(
            f"{path}: Professional coverage decision requirements must be a non-empty mapping"
        )
    state_order = {name: index for index, name in enumerate(PROFESSIONAL_COVERAGE_STATES)}
    requirements: dict[str, list[str]] = {}
    for skill, raw_states in raw_requirements.items():
        if not isinstance(skill, str) or not NAME_RE.fullmatch(skill):
            raise ValidationProblem(
                f"{path}: Professional coverage requirement keys must be Skill names"
            )
        if known_skills is not None and skill not in known_skills:
            raise ValidationProblem(
                f"{path}: Professional coverage policy names unknown Skill {skill!r}"
            )
        if not isinstance(raw_states, list) or not raw_states:
            raise ValidationProblem(
                f"{path}: requirements.{skill} must be a non-empty list"
            )
        if not all(isinstance(item, str) and item.strip() for item in raw_states):
            raise ValidationProblem(
                f"{path}: requirements.{skill} must contain non-blank state names"
            )
        states = [item.strip() for item in raw_states]
        if len(states) != len(set(states)):
            raise ValidationProblem(
                f"{path}: requirements.{skill} must not repeat coverage states"
            )
        unknown = sorted(set(states) - set(PROFESSIONAL_COVERAGE_STATES))
        if unknown:
            raise ValidationProblem(
                f"{path}: requirements.{skill} contains unknown coverage states: "
                + ", ".join(unknown)
            )
        requirements[skill] = sorted(states, key=state_order.__getitem__)

    normalized = {
        "id": decision_id,
        "kind": PROFESSIONAL_COVERAGE_DECISION_KIND,
        "schema_version": 1,
        "requirements": {
            skill: requirements[skill] for skill in sorted(requirements)
        },
    }
    fingerprint = hashlib.sha256(
        json.dumps(
            normalized,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return {
        **normalized,
        "source": str(path),
        "fingerprint": {"algorithm": "sha256", "value": fingerprint},
    }


def parse_frontmatter(path: Path) -> tuple[dict[str, Any], str, str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_DELIMITER:
        raise ValidationProblem(f"{path} is missing YAML frontmatter")

    end_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == FRONTMATTER_DELIMITER:
            end_index = index
            break

    if end_index is None:
        raise ValidationProblem(f"{path} has unterminated YAML frontmatter")

    raw_frontmatter = "\n".join(lines[1:end_index])
    body = "\n".join(lines[end_index + 1 :])
    loaded = load_yaml_text(raw_frontmatter, path)
    if not isinstance(loaded, dict):
        raise ValidationProblem(f"{path} frontmatter must be a mapping")

    return loaded, raw_frontmatter, body


def _markdown_fence_opener(line: str) -> tuple[str, int] | None:
    match = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
    if not match:
        return None
    marker = match.group(1)
    return marker[0], len(marker)


def _is_markdown_fence_closer(
    line: str,
    marker_character: str,
    minimum_length: int,
) -> bool:
    return bool(
        re.fullmatch(
            rf"\s{{0,3}}{re.escape(marker_character)}{{{minimum_length},}}\s*",
            line,
        )
    )


def heading_entries(markdown: str) -> list[tuple[int, int, str]]:
    entries: list[tuple[int, int, str]] = []
    fence: tuple[str, int] | None = None
    for line_number, line in enumerate(markdown.splitlines(), start=1):
        if fence is not None:
            if _is_markdown_fence_closer(line, *fence):
                fence = None
            continue
        opener = _markdown_fence_opener(line)
        if opener is not None:
            fence = opener
            continue
        match = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        if match:
            level = len(line.lstrip().split(" ", 1)[0])
            entries.append((line_number, level, match.group(1).strip()))
    return entries


def heading_titles(markdown: str) -> list[str]:
    return [title for _line_number, _level, title in heading_entries(markdown)]


def empty_markdown_headings(markdown: str) -> list[tuple[int, int, str]]:
    """Return non-H1 headings with no authored content before the next heading.

    Blank lines and HTML comments do not count as content. Fenced code headings
    are ignored by ``heading_entries``. Template callers may decide whether an
    explicit placeholder is acceptable; root Skill validators do not allow it.
    """

    lines = markdown.splitlines()
    entries = heading_entries(markdown)
    empty: list[tuple[int, int, str]] = []
    for index, entry in enumerate(entries):
        line_number, level, _title = entry
        if level == 1:
            continue
        next_line = entries[index + 1][0] - 1 if index + 1 < len(entries) else len(lines)
        section = "\n".join(lines[line_number:next_line])
        without_comments = re.sub(r"<!--.*?-->", "", section, flags=re.DOTALL)
        if not without_comments.strip():
            empty.append(entry)
    return empty


def has_section(markdown: str, section: str) -> bool:
    wanted = section.casefold()
    return any(title.casefold() == wanted for title in heading_titles(markdown))


def extract_section_body(markdown: str, section: str) -> str | None:
    """Return the body for a markdown heading with the exact title.

    The section ends at the next heading of the same or higher level. Fenced
    code blocks are ignored for heading detection so example output templates
    do not masquerade as authored sections.
    """

    wanted = section.casefold()
    lines = markdown.splitlines()
    capture_level: int | None = None
    captured: list[str] = []
    fence: tuple[str, int] | None = None

    for line in lines:
        if fence is not None:
            if _is_markdown_fence_closer(line, *fence):
                fence = None
            if capture_level is not None:
                captured.append(line)
            continue
        opener = _markdown_fence_opener(line)
        if opener is not None:
            fence = opener
            if capture_level is not None:
                captured.append(line)
            continue

        heading_match = re.match(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            if capture_level is not None and level <= capture_level:
                break
            if title.casefold() == wanted:
                capture_level = level
                captured = []
            elif capture_level is not None:
                captured.append(line)
            continue

        if capture_level is not None:
            captured.append(line)

    if capture_level is None:
        return None
    return "\n".join(captured).strip()


def validate_required_sections(
    body: str,
    required_sections: Iterable[str],
    context: str,
    errors: list[str],
    *,
    require_order: bool = False,
) -> None:
    entries = heading_entries(body)
    by_title: dict[str, list[tuple[int, int, str]]] = {}
    for entry in entries:
        by_title.setdefault(entry[2].casefold(), []).append(entry)

    ordered_positions: list[tuple[str, int]] = []
    for section in required_sections:
        matches = by_title.get(section.casefold(), [])
        if not matches:
            errors.append(f"{context}: missing required section '{section}'")
            continue
        if len(matches) > 1:
            lines = ", ".join(str(line_number) for line_number, _level, _title in matches)
            errors.append(f"{context}: duplicate required section '{section}' at lines {lines}")
        ordered_positions.append((section, matches[0][0]))

    if require_order:
        for (previous_section, previous_line), (section, line_number) in zip(
            ordered_positions,
            ordered_positions[1:],
        ):
            if previous_line >= line_number:
                errors.append(
                    f"{context}: required section '{section}' must appear after "
                    f"'{previous_section}'"
                )


def count_markdown_list_items(section_body: str) -> int:
    return sum(1 for line in section_body.splitlines() if re.match(r"^\s*[-*]\s+", line))


def validate_skill_text_quality(text: str, context: str, errors: list[str]) -> None:
    for pattern, label in SKILL_TEXT_QUALITY_SMELLS:
        if pattern.search(text):
            errors.append(f"{context}: suspicious generated text fragment '{label}'")


def validate_no_beginner_sections(body: str, context: str, errors: list[str]) -> None:
    for title in heading_titles(body):
        folded = title.casefold()
        for banned in BANNED_BEGINNER_SECTIONS:
            banned_folded = banned.casefold()
            if folded == banned_folded or (
                banned_folded == "what is" and folded.startswith("what is ")
            ):
                errors.append(f"{context}: banned beginner section '{title}'")


def validate_no_personal_references(text: str, context: str, errors: list[str]) -> None:
    folded = text.casefold()
    for phrase in PERSONAL_ASSET_REFERENCES:
        if phrase.casefold() in folded:
            errors.append(f"{context}: banned personal/private reference '{phrase}'")


def validate_required_frontmatter(
    metadata: dict[str, Any],
    required_keys: Iterable[str],
    context: str,
    errors: list[str],
) -> None:
    for key in required_keys:
        value = metadata.get(key)
        if value is None or value == "":
            errors.append(f"{context}: missing required frontmatter '{key}'")


def validate_name(value: Any, context: str, errors: list[str], field: str = "name") -> None:
    if not isinstance(value, str) or not NAME_RE.fullmatch(value):
        errors.append(f"{context}: frontmatter '{field}' must be lowercase hyphen-separated")


def validate_description_length(
    value: Any,
    minimum: int,
    maximum: int,
    context: str,
    errors: list[str],
) -> None:
    if not isinstance(value, str):
        errors.append(f"{context}: frontmatter 'description' must be text")
        return

    length = len(value.strip())
    if length < minimum or length > maximum:
        errors.append(
            f"{context}: frontmatter 'description' must be {minimum}-{maximum} characters"
        )


def metadata_value_contains_tool(value: Any, tool_names: Iterable[str]) -> bool:
    folded = " ".join(_flatten_string_values(value)).casefold()
    return any(re.search(rf"\b{re.escape(tool.casefold())}\b", folded) for tool in tool_names)


def _flatten_string_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        values: list[str] = []
        for key, item in value.items():
            values.extend(_flatten_string_values(key))
            values.extend(_flatten_string_values(item))
        return values
    if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray)):
        values = []
        for item in value:
            values.extend(_flatten_string_values(item))
        return values
    return [str(value)]


def validate_allowed_tools_warning(
    metadata: dict[str, Any],
    raw_frontmatter: str,
    body: str,
    context: str,
    errors: list[str],
) -> None:
    allowed_tool_values = [
        value
        for key, value in metadata.items()
        if key.casefold().replace("_", "-") == "allowed-tools"
    ]
    raw_allowed_tools = re.findall(
        r"(?im)^allowed[-_ ]tools\s*:\s*(.+)$",
        raw_frontmatter,
    )
    requires_warning = any(
        metadata_value_contains_tool(value, ("shell", "bash"))
        for value in allowed_tool_values + raw_allowed_tools
    )
    if requires_warning and not has_section(body, "Trusted Tooling Warning"):
        errors.append(
            f"{context}: allowed-tools may not include shell/bash without "
            "a 'Trusted Tooling Warning' section"
        )


def validate_ai_markdown_format(
    body: str,
    context: str,
    errors: list[str],
    *,
    check_bullets: bool = True,
) -> None:
    """Reject malformed fragments and enforce the shared AI readability gate."""
    for line_number, line in enumerate(body.splitlines(), start=1):
        if line.startswith("+-"):
            errors.append(f"{context}:{line_number}: malformed '+-' list marker")
        if line.startswith("- \"") and line.count('"') % 2:
            errors.append(
                f"{context}:{line_number}: unmatched quote in Markdown list item"
            )
    validate_ai_readability(
        body,
        context,
        errors,
        check_bullets=check_bullets,
    )


def registry_items(data: Any, key: str, path: Path, errors: list[str]) -> list[Any]:
    if not isinstance(data, dict):
        errors.append(f"{path}: registry must be a mapping")
        return []

    value = data.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list):
        errors.append(f"{path}: '{key}' must be a list")
        return []
    return value


def entry_ref(entry: Any, keys: Iterable[str]) -> str | None:
    if isinstance(entry, str):
        return entry
    if not isinstance(entry, dict):
        return None

    for key in keys:
        value = entry.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def entry_path(entry: Any) -> str | None:
    if not isinstance(entry, dict):
        return None
    value = entry.get("path")
    return value if isinstance(value, str) and value else None


def collect_reference_values(obj: Any, reference_keys: set[str]) -> list[str]:
    refs: list[str] = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            normalized_key = str(key).casefold().replace("-", "_")
            if normalized_key in reference_keys:
                refs.extend(_reference_strings(value))
            else:
                refs.extend(collect_reference_values(value, reference_keys))
    elif isinstance(obj, list):
        for item in obj:
            refs.extend(collect_reference_values(item, reference_keys))

    return refs


def _reference_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        refs: list[str] = []
        for item in value:
            refs.extend(_reference_strings(item))
        return refs
    if isinstance(value, dict):
        for key in (
            "name",
            "id",
            "skill",
            "skill_name",
            "capability_id",
            "changeforge_capability_id",
            "domain_extension",
            "domain_extension_id",
            "path",
        ):
            item = value.get(key)
            if isinstance(item, str) and item:
                return [item]
    return []


def path_is_within(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def first_path_part(path_value: str) -> str:
    return path_value.strip("/").split("/", 1)[0]
