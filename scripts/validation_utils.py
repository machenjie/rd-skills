#!/usr/bin/env python3
"""Shared validation helpers for rd-skills authoring contracts."""

from __future__ import annotations

import copy
import hashlib
import io
import subprocess
import re
import sys
import json
import tokenize
import unicodedata
from decimal import Decimal, InvalidOperation, ROUND_CEILING
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


def evidence_resolution_source_declaration(
    path: Path | None = None,
    *,
    root: Path = ROOT,
    source_record: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Read the closed Evidence Resolution declaration from its owning Skill."""

    if source_record is None:
        if path is None:
            raise ValueError("Evidence Resolution source declaration needs a Skill path")
        source_record = collect_skill_root_source(path, root=root)
    raw_source = source_record.get("raw_source")
    if not isinstance(raw_source, str):
        raise ValueError("Evidence Resolution source declaration lacks collected source")
    begin = "<!-- BEGIN CHANGEFORGE EVIDENCE RESOLUTION SOURCE -->"
    end = "<!-- END CHANGEFORGE EVIDENCE RESOLUTION SOURCE -->"
    if raw_source.count(begin) != 1 or raw_source.count(end) != 1:
        raise ValueError(
            "Evidence Resolution source declaration markers must occur exactly once"
        )
    payload = raw_source.split(begin, 1)[1].split(end, 1)[0].strip()
    if not payload.startswith("```json\n") or not payload.endswith("\n```"):
        raise ValueError(
            "Evidence Resolution source declaration must be one fenced JSON object"
        )
    try:
        declaration = json.loads(payload[len("```json\n") : -len("\n```")])
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError("Evidence Resolution source declaration is invalid JSON") from exc
    if not isinstance(declaration, dict) or set(declaration) != {
        "contract",
        "gap_classes",
        "decision_rules",
    }:
        raise ValueError("Evidence Resolution source declaration fields are not closed")
    if declaration["contract"] != "changeforge.evidence-resolution-source/v1":
        raise ValueError("Evidence Resolution source declaration contract is invalid")
    if not isinstance(declaration["gap_classes"], list) or not isinstance(
        declaration["decision_rules"], dict
    ):
        raise ValueError("Evidence Resolution source declaration shape is invalid")
    return declaration


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
PROMPT_MANAGED_PROJECTION_CONTRACTS = {
    "execution-level-contract": {
        "section": "Execution Level and Validation",
        "required_contracts": ["execution_level_contract"],
    },
    "review-evidence-contract": {
        "section": "Review and Repair",
        "required_contracts": [
            "visible_evidence_contract",
            "review_discipline_contract",
            "task_contract",
        ],
    },
    "closure-contract": {
        "section": "Closure",
        "required_contracts": [
            "visible_evidence_contract",
            "completion_state",
        ],
    },
}
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
    """Derive release and evolution targets from the Core Model authority."""

    if contract.get("schema_version") != 2:
        raise ValueError("context budget contract must use schema_version 2")

    classes = contract.get("budget_classes")
    if not isinstance(classes, dict) or not classes:
        raise ValueError("context budget classes must be a non-empty object")
    limits: dict[str, dict[str, Any]] = {}
    for budget_class, entry in classes.items():
        if not isinstance(entry, dict):
            raise ValueError(f"context budget class {budget_class!r} must be an object")
        ceiling = entry.get("capacity_ceiling")
        ratio_value = entry.get("minimum_headroom_ratio")
        if not isinstance(ceiling, int) or isinstance(ceiling, bool) or ceiling <= 0:
            raise ValueError(
                f"context budget class {budget_class!r} capacity_ceiling must be positive"
            )
        if isinstance(ratio_value, bool) or not isinstance(ratio_value, (int, float)):
            raise ValueError(
                f"context budget class {budget_class!r} minimum_headroom_ratio must be numeric"
            )
        try:
            ratio = Decimal(str(ratio_value))
        except InvalidOperation as exc:
            raise ValueError(
                f"context budget class {budget_class!r} minimum_headroom_ratio is invalid"
            ) from exc
        if ratio < 0 or ratio >= 1:
            raise ValueError(
                f"context budget class {budget_class!r} minimum_headroom_ratio must be in [0, 1)"
            )
        reserve = int(
            (Decimal(ceiling) * ratio).to_integral_value(rounding=ROUND_CEILING)
        )
        release_target = ceiling - reserve
        if release_target <= 0:
            raise ValueError(
                f"context budget class {budget_class!r} derived release target must be positive"
            )
        if budget_class == "main" and "minimum_release_margin_tokens" not in entry:
            raise ValueError(
                "context budget class 'main' must define minimum_release_margin_tokens"
            )
        if (
            budget_class != "main"
            and "minimum_release_margin_tokens" in entry
        ):
            raise ValueError(
                "minimum_release_margin_tokens is allowed only for the main context"
            )
        minimum_release_margin = entry.get("minimum_release_margin_tokens", 0)
        if (
            not isinstance(minimum_release_margin, int)
            or isinstance(minimum_release_margin, bool)
            or minimum_release_margin < 0
        ):
            raise ValueError(
                f"context budget class {budget_class!r} "
                "minimum_release_margin_tokens must be a non-negative integer"
            )
        evolution_target = release_target - minimum_release_margin
        if evolution_target <= 0:
            raise ValueError(
                f"context budget class {budget_class!r} derived evolution target must be positive"
            )
        limits[budget_class] = {
            "label": entry.get("label"),
            "capacity_ceiling": ceiling,
            "minimum_headroom_ratio": float(ratio),
            "required_reserve_tokens": reserve,
            "release_target": release_target,
            "minimum_release_margin_tokens": minimum_release_margin,
            "evolution_target": evolution_target,
        }
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
        "`required reserve = ceil(capacity ceiling * minimum headroom ratio)`; "
        "`release target = capacity ceiling - required reserve`; "
        "`evolution target = release target - minimum release margin`.",
        "Release and evolution targets are derived and are not stored as second authorities.",
        "",
        "| Context | Capacity ceiling | Minimum headroom ratio | Required reserve | Release target | Minimum release margin | Evolution target |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for limit in limits.values():
        lines.append(
            f"| {limit['label']} | {limit['capacity_ceiling']} | "
            f"{limit['minimum_headroom_ratio']:.2f} | "
            f"{limit['required_reserve_tokens']} | {limit['release_target']} | "
            f"{limit['minimum_release_margin_tokens']} | "
            f"{limit['evolution_target']} |"
        )
    lines.extend(
        [
            "",
            f"Tokenizer: `{contract['tokenizer']}`. Exact duplicate-rule ratio gate: "
            f"`{contract['duplicate_rule_token_ratio_max']:.2f}`.",
            f"<!-- END CHANGEFORGE CONTEXT BUDGET PROJECTION: {identifier} -->",
        ]
    )
    return "\n".join(lines)


def completion_transition_groups(completion: dict[str, Any]) -> list[str]:
    """Render the canonical same-task transition groups from the graph."""

    statuses = completion["statuses"]
    transitions = completion["allowed_transitions"]
    terminals = set(completion["terminal_statuses"])
    return [
        f"{source} -> {' | '.join(transitions[source])}"
        for source in statuses
        if source not in terminals
    ]


def completion_transition_edges(completion: dict[str, Any]) -> list[tuple[str, str]]:
    """Return every canonical nonterminal edge in stable graph order."""

    terminals = set(completion["terminal_statuses"])
    return [
        (source, target)
        for source in completion["statuses"]
        if source not in terminals
        for target in completion["allowed_transitions"][source]
    ]


def completion_transition_projection_terms(completion: dict[str, Any]) -> list[str]:
    return ["same Task ID", *completion_transition_groups(completion)]


def completion_transition_matrix_text(completion: dict[str, Any]) -> str:
    return "; ".join(completion_transition_groups(completion))


def completion_fail_closed_groups(completion: dict[str, Any]) -> list[str]:
    """Render each canonical fail-closed outcome in declared rule order."""

    return [
        f"{rule_id} -> {' | '.join(allowed_statuses)}"
        for rule_id, allowed_statuses in completion["fail_closed_rules"].items()
    ]


def completion_fail_closed_projection_terms(completion: dict[str, Any]) -> list[str]:
    return ["fail-closed outcomes", *completion_fail_closed_groups(completion)]


def completion_fail_closed_surface_errors(
    surface: str,
    completion: dict[str, Any],
    context: str,
) -> list[str]:
    """Require one exact projection of every fail-closed outcome."""

    errors: list[str] = []
    statuses = completion["statuses"]
    status_pattern = "|".join(re.escape(status) for status in statuses)
    for rule_id, expected_targets in completion["fail_closed_rules"].items():
        expression = re.compile(
            rf"\b{re.escape(rule_id)}\s*->\s*"
            rf"(?P<targets>(?:{status_pattern})(?:\s*\|\s*(?:{status_pattern}))*)",
            flags=re.IGNORECASE,
        )
        matches = list(expression.finditer(surface))
        if len(matches) != 1:
            errors.append(
                f"{context}: fail-closed outcome {rule_id!r} must appear exactly once"
            )
            continue
        actual_targets = [
            item.strip().casefold()
            for item in matches[0].group("targets").split("|")
        ]
        if actual_targets != expected_targets:
            errors.append(
                f"{context}: fail-closed outcome {rule_id!r} must be exactly "
                f"{' | '.join(expected_targets)!r}, got {' | '.join(actual_targets)!r}"
            )
    return errors


def completion_transition_surface_errors(
    surface: str,
    completion: dict[str, Any],
    context: str,
) -> list[str]:
    """Require one exact, graph-derived transition matrix and reject extra edges."""

    statuses = completion["statuses"]
    source_pattern = "|".join(re.escape(status) for status in statuses)
    expression = re.compile(
        rf"\b(?P<source>{source_pattern})\s*->\s*"
        r"(?P<targets>[a-z][a-z0-9_]*(?:\s*\|\s*[a-z][a-z0-9_]*)*)",
        re.IGNORECASE,
    )
    actual = [
        (
            match.group("source").casefold(),
            tuple(
                target.strip().casefold()
                for target in match.group("targets").split("|")
            ),
        )
        for match in expression.finditer(surface)
    ]
    terminals = set(completion["terminal_statuses"])
    expected = [
        (source, tuple(completion["allowed_transitions"][source]))
        for source in statuses
        if source not in terminals
    ]
    if actual != expected:
        return [
            f"{context}: same-task transition matrix must be exactly "
            f"{completion_transition_matrix_text(completion)!r}; found {actual!r}"
        ]
    return []


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


def docs_projection_block(data: dict[str, Any], projection: dict[str, Any]) -> str:
    """Render the unique managed Markdown body for one docs projection."""

    task_fields = data["task_contract"]["required_for_direct_task"]
    evidence_fields = data["visible_evidence_contract"]["fields"]
    transitions = completion_transition_groups(data["completion_state"])
    fail_closed = completion_fail_closed_groups(data["completion_state"])
    identifier = projection["id"]
    lines = [
        f"<!-- BEGIN CHANGEFORGE CORE DOCS PROJECTION: {identifier} -->",
        "Contract identities:",
        "",
        *[f"- {term}" for term in projection["required_terms"]],
        "",
        "Task Contract v2 fields (exact order):",
        "",
        *[f"{index}. `{field}`" for index, field in enumerate(task_fields, 1)],
        "",
        "New task assignment initial Status:",
        "",
        f"`{data['task_contract']['assignment_initial_status']}`",
        "",
        "visible task-local Evidence Ledger fields (exact order):",
        "",
        *[f"{index}. `{field}`" for index, field in enumerate(evidence_fields, 1)],
        "",
        "same Task ID transitions (exact):",
        "",
        "```text",
        *transitions,
        "```",
        "",
        "fail-closed outcomes (exact):",
        "",
        "```text",
        *fail_closed,
        "```",
        "",
        "No transition leaves completed for that Task ID.",
        "New work after completion starts `in_progress` under a new Task ID.",
        f"<!-- END CHANGEFORGE CORE DOCS PROJECTION: {identifier} -->",
    ]
    rendered = "\n".join(lines)
    normalized = " ".join(rendered.casefold().split())
    missing = [
        term
        for term in docs_projection_terms(data, projection)
        if " ".join(term.casefold().split()) not in normalized
    ]
    if missing:
        raise ValueError(
            f"docs projection renderer omitted canonical terms: {missing}"
        )
    return rendered


def _prompt_projection_markers(identifier: str) -> tuple[str, str]:
    return (
        f"<!-- {identifier}:B -->",
        f"<!-- {identifier}:E -->",
    )


def _completion_rule_text(rule: dict[str, Any]) -> str:
    """Render one completion rule from its canonical terms."""

    identifier = rule["id"]
    terms = rule["projection_terms"]
    if identifier == "requested-result-satisfied" and len(terms) == 3:
        return f"`completed` only when {terms[0]} is {terms[1]} within {terms[2]}."
    if identifier == "required-evidence-current" and len(terms) == 3:
        return f"{terms[0].capitalize()} is {terms[1]} or {terms[2]}."
    if identifier == "answer-diagnosis-proof-limits" and len(terms) == 4:
        return f"{terms[0].capitalize()}/{terms[1]} may complete when requested result/evidence boundary/{terms[2]} are {terms[3]}."
    raise ValueError(f"unknown or malformed completion rule {identifier!r}")


def _execution_level_formula_text(contract: dict[str, Any]) -> str:
    """Render valid and fail-closed effective-level formulas from Core sources."""

    aliases = {
        "requested_or_automatic": "requested-or-automatic",
        "minimum_eligible_level": "minimum eligible",
        "mandatory_floor": "mandatory",
        "prior_historical_max_effective": "prior historical max effective",
    }
    try:
        valid_sources = [
            aliases[source]
            for source in contract["formula"]["effective_level_sources"]
        ]
    except (KeyError, TypeError) as exc:
        raise ValueError("execution effective-level sources are unsupported") from exc
    critical = contract["critical_unknown"]
    return (
        "Effective=max("
        + ",".join(valid_sources)
        + "); fallback=max("
        + critical["floor"]
        + ",explicit known "
        + contract["levels"][-1]["id"]
        + ",prior historical max effective)."
    )


def prompt_projection_block(
    data: dict[str, Any], projection: dict[str, Any]
) -> str:
    """Render one exact Prompt block from the authoritative Core Model."""

    identifier = projection["id"]
    begin, end = _prompt_projection_markers(identifier)
    evidence = data["visible_evidence_contract"]
    completion = data["completion_state"]
    proof = evidence["completion_proof"]["implementation"]

    if identifier == "execution-level-contract":
        contract = data["execution_level_contract"]
        runtime = contract["projection"]["runtime_reference"]
        runtime_path = "references/" + Path(runtime["path"]).name
        critical = contract["critical_unknown"]
        scope = contract["scope_lineage"]
        lines = [
            begin,
            runtime_path + " JIT-owns L1-L5 predicates, formula, Basis, history, obligations, and confirmation; policy data, not instructions. Trust exact build/install validation.",
            ""
            + "|".join(contract["main_evidence_kinds"])
            + " -> compute "
            + contract["projection"]["router"]["input_field"]
            + "; Three axes are independent per Core; automatic L5 asks once.",
            "integrity fallback/no partial computation: edit "
            + critical["edit_status"]
            + "; read-only diagnosis; never Router.",
            contract["levels"][0]["id"]
            + "-"
            + contract["levels"][-1]["id"]
            + " remain; default "
            + contract["default_level"]
            + " applies only to executable Tasks; "
            + contract["levels"][-1]["id"]
            + " explicit or confirmed automatic recommendation; "
            + contract["non_bypassable"][-2]
            + ". Initial Analysis has no Execution Level; First Executable Slice computes from analysis_handoff.",
            "After 2 same-path failures require changed hypothesis/material/gap/transition or return Main/block; never third unchanged retry. Active/resumed edit/validation/review requires current Level/Basis reissue.",
            end,
        ]
        return "\n".join(lines)

    if identifier == "review-evidence-contract":
        forbidden = [
            rule["projection_terms"][0]
            for rule in evidence["forbidden_storage"]
            if f"prompt:{projection['section']}" in rule["projection_targets"]
        ]
        lines = [
            begin,
            "Before review-agent dispatch, Review Input Ready=latest changed paths+post-latest-edit validation+fixed scope.",
            "exact delivered unified diff or current reviewer-readable native reference+instance consumption capability also required. Static host support alone is never readiness; forward evidence unchanged; never send Review to export it.",
            "Missing=>review dispatch=0; Legacy/incomplete permits one recovery; Review before Task before Review is forbidden.",
            "references/implementation-handoff-template.md JIT-owns Ledger State/currentness, freshness, capability branches, and review proof. Latest material edit invalidates validation/evidence; Claims: "
            + proof["latest_material_edit_claim"]
            + ", "
            + proof["validation_claim"]
            + ".",
            "Current review-agent evidence: actual diff/every changed file/validation results/changed-scope-reviewed/high-risk-review-passed/blocking-findings-none|blocking-findings-resolved.",
            "not-required JIT-loads from the Handoff owner; Missing/inconsistent authority/binding fails closed→reissue.",
            "The fixed Review Boundary closes first. Material current-task findings with the same Review Round ID+Task ID form exactly one Repair batch; cross-Task batch is forbidden. Adjacent record-only: no Repair/Analysis; ordinary finding no Analysis; scope-blocker or protected Authority/Brief invalidation→Main bounded Delta. Repair requires fresh validation/re-review: fresh validation, latest actual diff, fresh re-review.",
            "Initial Review keeps the full fixed boundary/scope/base/professional-risk depth. Full-boundary completion applies only to Initial Review.",
            "Focused Re-review checks inherited findings, repair diff/regressions, affected transitive dependents, and frozen Acceptance/Invariant/Contract/professional-risk boundaries.",
            "Its focused completion explicitly preserves the frozen professional-risk boundary without reopening Initial scope.",
            "Re-review: Re-review Classification=inherited|repair-regression|frozen-boundary-violation|protected-invalidation|adjacent; Classification Evidence required; frozen-boundary-violation needs explicit boundary evidence. Main consumes fields with no prose inference; Initial may omit/use not-applicable. Protected invalidation invalidates affected validation/review evidence before Delta→Task→fresh validation→PASS re-review; adjacent residual-only.",
            "At most 2 automatic Repair rounds per Task ID; Review Boundary/Review Round/Delta Analysis never reset the count. At cap: blocker→BLOCKED non-converged, protected invalidation→Main→Delta Analysis, adjacent/hardening-only may close the current contract; cap never implies PASS. Review-driven Delta Analysis follows the same two-failure changed hypothesis/material/gap/transition rule and cannot third-replan unchanged.",
            "No " + "/".join(forbidden) + ". review_discipline_contract and task_contract.finding_relations authoritative.",
            end,
        ]
        return "\n".join(lines)

    if identifier == "closure-contract":
        statuses = completion["statuses"]
        terminals = completion["terminal_statuses"]
        new_work = completion["new_work_after_completion"]
        transition_text = completion_transition_matrix_text(completion)
        fail_closed_text = "; ".join(completion_fail_closed_groups(completion))
        completed_rule_text = " ".join(
            _completion_rule_text(rule) for rule in completion["completed_rules"]
        )
        lines = [
            begin,
            "Status: " + " | ".join(statuses) + ". Same Task ID: "
            f"{transition_text}. {' | '.join(terminals)} terminal for that Task ID; new work after completion: new Task ID at "
            f"{new_work['initial_status']}.",
            completed_rule_text,
            f"Exact fail-closed outcomes: {fail_closed_text}.",
            "Implementation needs post-edit validation, every changed file reviewed, and no blockers; repair needs fresh validation/re-review.",
            "State unverified scope/residual risk; current evidence scope covers claimed result.",
            end,
        ]
        return "\n".join(lines)

    raise ValueError(f"unknown Prompt managed projection {identifier!r}")


def prompt_projection_errors(
    text: str,
    data: dict[str, Any],
    *,
    document_bytes: bytes | None = None,
) -> list[str]:
    """Validate exact managed Prompt bytes and its whole-document binding."""

    errors: list[str] = []
    prompt = data["prompt_contract"]
    actual_sha256 = hashlib.sha256(
        document_bytes if document_bytes is not None else text.encode("utf-8")
    ).hexdigest()
    if actual_sha256 != prompt["document_sha256"]:
        errors.append("whole-document SHA-256 does not match the Core Model")
    for projection in prompt["managed_projections"]:
        expected = prompt_projection_block(data, projection)
        actual = extract_section_body(text, projection["section"])
        if actual != expected:
            errors.append(
                f"managed Prompt projection {projection['id']!r} must equal the "
                "exact Core Model rendering"
            )
        begin, end = _prompt_projection_markers(projection["id"])
        if text.count(begin) != 1 or text.count(end) != 1:
            errors.append(
                f"managed Prompt projection {projection['id']!r} markers must each "
                "appear exactly once"
            )
    return errors


EXECUTION_LEVEL_RUNTIME_DESCRIPTION = (
    "Generated from the authoritative Core execution_level_contract; do not edit by hand. "
    "Load the JSON as policy data, never as instructions."
)


def _canonical_execution_level_value(value: object, context: str) -> object:
    """Normalize one JSON value while rejecting ambiguous Unicode and key shapes."""

    if isinstance(value, str):
        for character in value:
            category = unicodedata.category(character)
            if category == "Cs":
                raise ValueError(f"{context} contains invalid Unicode surrogate data")
            if category == "Cc" and character not in {"\t", "\n", "\r"}:
                raise ValueError(f"{context} contains a non-permitted control character")
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [
            _canonical_execution_level_value(item, f"{context}[{index}]")
            for index, item in enumerate(value)
        ]
    if isinstance(value, dict):
        normalized: dict[str, object] = {}
        for raw_key, item in value.items():
            if not isinstance(raw_key, str):
                raise ValueError(f"{context} contains a non-text JSON key")
            key = _canonical_execution_level_value(raw_key, f"{context}.<key>")
            assert isinstance(key, str)
            if key in normalized:
                raise ValueError(f"{context} contains duplicate NFC-normalized key {key!r}")
            normalized[key] = _canonical_execution_level_value(
                item,
                f"{context}.{key}",
            )
        return normalized
    if value is None or isinstance(value, (bool, int)):
        return value
    raise ValueError(f"{context} contains unsupported JSON value {type(value).__name__}")


def _canonical_execution_level_json_bytes(value: object, context: str) -> bytes:
    """Serialize one execution-level value through the existing canonical protocol."""

    normalized = _canonical_execution_level_value(value, context)
    return json.dumps(
        normalized,
        allow_nan=False,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def execution_level_runtime_payload(
    data: dict[str, Any] | None = None,
) -> dict[str, object]:
    """Return the closed runtime policy payload, excluding projection metadata."""

    data = CORE_CONTRACTS if data is None else data
    contract = data["execution_level_contract"]
    runtime = contract["projection"]["runtime_reference"]
    excluded = runtime["excluded_fields"]
    expected_excluded = ["projection"]
    if excluded != expected_excluded:
        raise ValueError(
            "execution-level runtime payload must exclude only projection metadata"
        )
    candidate = dict(data)
    candidate_execution = dict(contract)
    candidate_execution["projection"] = CORE_CONTRACTS["execution_level_contract"][
        "projection"
    ]
    candidate["execution_level_contract"] = candidate_execution
    payload_schema_errors = [
        error
        for error in validate_core_contracts(candidate)
        if error.startswith(("execution ", "execution_level_contract", "validation "))
    ]
    if payload_schema_errors:
        raise ValueError(
            "execution-level runtime payload schema is invalid: "
            + "; ".join(payload_schema_errors)
        )
    payload = {
        key: value
        for key, value in contract.items()
        if key not in set(excluded)
    }
    normalized = _canonical_execution_level_value(
        payload,
        "execution_level_contract runtime payload",
    )
    assert isinstance(normalized, dict)
    return normalized


def execution_level_runtime_payload_bytes(
    data: dict[str, Any] | None = None,
) -> bytes:
    """Serialize the runtime payload as canonical NFC UTF-8 JSON."""

    payload = execution_level_runtime_payload(data)
    return _canonical_execution_level_json_bytes(
        payload,
        "execution_level_contract runtime payload",
    )


def execution_level_runtime_payload_sha256(
    data: dict[str, Any] | None = None,
) -> str:
    """Return the authoring/build identity of the canonical payload bytes."""

    return hashlib.sha256(execution_level_runtime_payload_bytes(data)).hexdigest()


def execution_level_runtime_reference(
    data: dict[str, Any] | None = None,
) -> str:
    """Render the complete generated targeted Reference."""

    data = CORE_CONTRACTS if data is None else data
    runtime = data["execution_level_contract"]["projection"]["runtime_reference"]
    identifier = runtime["id"]
    payload = execution_level_runtime_payload_bytes(data).decode("utf-8")
    return "\n".join(
        [
            "# Execution Level Contract",
            "",
            EXECUTION_LEVEL_RUNTIME_DESCRIPTION,
            "",
            f"<!-- BEGIN CHANGEFORGE CORE RUNTIME REFERENCE: {identifier} -->",
            "```json",
            payload,
            "```",
            f"<!-- END CHANGEFORGE CORE RUNTIME REFERENCE: {identifier} -->",
            "",
        ]
    )


def _json_object_without_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def execution_level_runtime_reference_errors(
    text: str,
    data: dict[str, Any] | None = None,
) -> list[str]:
    """Validate the generated Reference's structure, payload, and exact bytes."""

    data = CORE_CONTRACTS if data is None else data
    runtime = data["execution_level_contract"]["projection"]["runtime_reference"]
    identifier = runtime["id"]
    begin = f"<!-- BEGIN CHANGEFORGE CORE RUNTIME REFERENCE: {identifier} -->"
    end = f"<!-- END CHANGEFORGE CORE RUNTIME REFERENCE: {identifier} -->"
    errors: list[str] = []
    if text.count(begin) != 1 or text.count(end) != 1:
        errors.append("execution-level runtime Reference markers must each appear exactly once")
        return errors
    if text.index(end) <= text.index(begin):
        errors.append("execution-level runtime Reference markers are misordered")
        return errors
    fence_matches = list(
        re.finditer(r"^```json\n(?P<payload>[^\n]*)\n```$", text, re.MULTILINE)
    )
    if len(fence_matches) != 1:
        errors.append("execution-level runtime Reference must contain one one-line JSON fence")
        return errors
    payload_text = fence_matches[0].group("payload")
    try:
        parsed = json.loads(
            payload_text,
            object_pairs_hook=_json_object_without_duplicate_keys,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        errors.append(f"execution-level runtime Reference JSON parse failed: {exc}")
        return errors
    if not isinstance(parsed, dict):
        errors.append("execution-level runtime Reference JSON payload must be an object")
        return errors
    try:
        normalized = _canonical_execution_level_value(parsed, "runtime Reference payload")
    except ValueError as exc:
        errors.append(str(exc))
        return errors
    assert isinstance(normalized, dict)
    expected_payload = execution_level_runtime_payload(data)
    expected_keys = set(expected_payload)
    actual_keys = set(normalized)
    if actual_keys != expected_keys:
        errors.append(
            "execution-level runtime Reference closed schema differs: "
            f"missing={sorted(expected_keys - actual_keys)}, extra={sorted(actual_keys - expected_keys)}"
        )
    candidate = dict(data)
    candidate_execution = dict(normalized)
    authoritative_execution = data["execution_level_contract"]
    for field in runtime["excluded_fields"]:
        candidate_execution[field] = authoritative_execution[field]
    candidate["execution_level_contract"] = candidate_execution
    schema_errors = [
        error
        for error in validate_core_contracts(candidate)
        if error.startswith("execution") or "validation" in error
    ]
    if schema_errors:
        errors.append(
            "execution-level runtime Reference schema is invalid: "
            + "; ".join(schema_errors)
        )
    canonical = json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    if payload_text != canonical:
        errors.append("execution-level runtime Reference JSON is not canonical NFC UTF-8")
    if normalized != expected_payload:
        errors.append("execution-level runtime Reference payload drifts from Core")
    if text != execution_level_runtime_reference(data):
        errors.append("execution-level runtime Reference must equal the exact Core rendering")
    return errors


def execution_level_router_block(data: dict[str, Any] | None = None) -> str:
    """Render the router's three-line consumer projection from the Core owner."""

    data = CORE_CONTRACTS if data is None else data
    contract = data["execution_level_contract"]
    projection = contract["projection"]["router"]
    projection_id = projection["id"]
    input_field = projection["input_field"]
    return "\n".join(
        [
            f"<!-- BEGIN CHANGEFORGE CORE ROUTER PROJECTION: {projection_id} -->",
            f"Route once per task using Main's Core-computed `{input_field}` input field to select Skills without recomputing execution level.",
            f"<!-- END CHANGEFORGE CORE ROUTER PROJECTION: {projection_id} -->",
        ]
    )


def execution_level_router_errors(
    text: str,
    data: dict[str, Any] | None = None,
) -> list[str]:
    """Validate byte-exact router projection and unique managed markers."""

    data = CORE_CONTRACTS if data is None else data
    expected = execution_level_router_block(data)
    projection_id = data["execution_level_contract"]["projection"]["router"]["id"]
    begin = f"<!-- BEGIN CHANGEFORGE CORE ROUTER PROJECTION: {projection_id} -->"
    end = f"<!-- END CHANGEFORGE CORE ROUTER PROJECTION: {projection_id} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        return ["execution-level router projection markers must each appear exactly once"]
    start = text.index(begin)
    end_start = text.index(end)
    if end_start <= start:
        return ["execution-level router projection markers are misordered"]
    finish = end_start + len(end)
    errors: list[str] = []
    if text[start:finish] != expected:
        errors.append("execution-level router projection must equal the exact Core rendering")
    forbidden_titles = (
        "Execution Level Projection",
        "Closed Trigger Registry",
        "L2 Eligibility",
        "Level Obligations",
        "Canonical Formula and Boundary",
        "Scope, Validation, and Obligations",
    )
    if any(title in text for title in forbidden_titles):
        errors.append("router must not contain the former execution-level matrix titles")
    trigger_ids = [row["id"] for row in data["execution_level_contract"]["trigger_registry"]]
    if any(identifier in text for identifier in trigger_ids):
        errors.append("router must not contain execution-level trigger IDs")
    if len(text.splitlines()) > 62:
        errors.append("professional Skill router must contain at most 62 lines")
    return errors


def public_execution_template_block(
    core: dict[str, Any],
    surface: str,
) -> str:
    """Render one surface-owned public Execution Level template block."""

    execution = core["execution_level_contract"]
    insertions = core["task_contract"]["execution_level_extension"][
        "surface_insertions"
    ]
    if surface not in insertions:
        raise ValueError(f"unknown public execution template surface {surface!r}")
    public = execution["projection"]["public_task_extension"]
    formula = execution["formula"]
    levels = [row["id"] for row in execution["levels"]]
    automatic_values = execution["dynamic_levels"]
    domain = lambda values: " / ".join(str(value) for value in values)
    l5_requirements = [
        obligation
        for obligation in execution["levels"][-1]["obligations"]
        if obligation
        in {
            "independent pre-implementation review",
            "strong safety and applicability proof",
            "declared-scope comprehensive negative and failure proof",
            "exhaustive final review",
        }
    ]

    def named(label: str, values: dict[str, str]) -> str:
        fields = public["line_fields"][label]
        if set(values) != set(fields):
            raise ValueError(f"public execution template {label} fields drift")
        return "; ".join(
            f"{field}={values[field]}" for field in fields
        )

    values = {
        "Level": named(
            "Level",
            {
                "requested": domain(execution["requested_values"]),
                "automatic": domain(automatic_values),
                "minimum": domain(levels),
                "default": execution["default_level"],
                "effective": domain(levels),
                "edit": "allowed / blocked",
            },
        ),
        "Basis": named(
            "Basis",
            {
                "source": "user_fact:<anchor> / analysis_handoff:<anchor>",
                "triggers": '["<matched or unknown trigger ID>"] / []',
                "l1": '["<false or unknown L1 predicate ID>"] / []',
                "l2": '["<false or unknown L2 predicate ID>"] / []',
                "l5": '["<false or unknown L5 predicate ID>"] / []',
                "confirmation": domain(
                    execution["l5_confirmation"]["states"]
                ),
                "unresolved": (
                    '[] / ["unknown-critical-boundary=>L4,edit=blocked"]'
                ),
            },
        ),
        "L5 Evidence": named(
            "L5 Evidence",
            {
                "when": "effective L5 only",
                "requires": domain(l5_requirements),
            },
        ),
    }
    labels = public["ordered_labels"]
    if set(values) != set(labels):
        raise ValueError("public execution template labels drift from public grammar")
    lines = [
        "<!-- BEGIN CHANGEFORGE CORE PUBLIC EXECUTION TEMPLATE: "
        f"{surface} -->",
        *(f"{label}: {values[label]}" for label in labels),
        "<!-- END CHANGEFORGE CORE PUBLIC EXECUTION TEMPLATE: "
        f"{surface} -->",
    ]
    return "\n".join(lines)


def public_execution_template_spans(
    text: str,
    core: dict[str, Any],
    surface: str,
) -> tuple[list[tuple[int, int]], list[str]]:
    """Locate only byte-exact managed blocks at the Core-owned surface count."""

    insertions = core["task_contract"]["execution_level_extension"][
        "surface_insertions"
    ]
    if surface not in insertions:
        return [], [f"unknown public execution template surface {surface!r}"]
    insertion = insertions[surface]
    expected_count = len(insertion.get("sections", [insertion]))
    begin = (
        "<!-- BEGIN CHANGEFORGE CORE PUBLIC EXECUTION TEMPLATE: "
        f"{surface} -->"
    )
    end = (
        "<!-- END CHANGEFORGE CORE PUBLIC EXECUTION TEMPLATE: "
        f"{surface} -->"
    )
    if text.count(begin) != expected_count or text.count(end) != expected_count:
        return [], [
            f"{surface}: managed public Execution Level markers must each appear "
            f"exactly {expected_count} time(s)"
        ]
    expected = public_execution_template_block(core, surface)
    matches = list(
        re.finditer(re.escape(begin) + r".*?" + re.escape(end), text, re.DOTALL)
    )
    if len(matches) != expected_count:
        return [], [f"{surface}: managed public Execution Level markers are misordered"]
    errors: list[str] = []
    spans: list[tuple[int, int]] = []
    for index, match in enumerate(matches, start=1):
        if match.group(0) != expected:
            errors.append(
                f"{surface}: managed public Execution Level block {index} must "
                "equal the exact Core rendering"
            )
        else:
            spans.append(match.span())
    label_pattern = re.compile(r"(?m)^(?:Level|Basis|L5 Evidence):[^\n]*$")
    label_matches = list(label_pattern.finditer(text))
    expected_label_count = expected_count * 3
    if len(label_matches) != expected_label_count or any(
        not any(start <= match.start() and match.end() <= finish for start, finish in spans)
        for match in label_matches
    ):
        errors.append(
            f"{surface}: unrecognized, duplicate, or displaced lightweight "
            "public Execution Level line"
        )

    placement_fragments: list[str]
    if insertion["kind"] == "heading":
        if insertion["after"] == "Status":
            placement_fragments = [
                "## Status\n\nin_progress\n\n## Execution Level\n\n"
                f"{expected}\n\n## Goal"
            ]
        else:
            placement_fragments = [
                f"## {insertion['after']}\n\n## Execution Level\n\n{expected}"
            ]
    else:
        sections = (
            insertion["sections"]
            if "sections" in insertion
            else [insertion["section"]]
        )
        if insertion["after"] == "Status":
            placement_fragments = [
                f"## {section}\n\nTask ID:\nStatus: in_progress\n{expected}\nGoal:"
                for section in sections
            ]
        else:
            placement_fragments = [
                f"## {section}\n\n{insertion['after']}:\n{expected}\nStatus:"
                for section in sections
            ]
    if any(text.count(fragment) != 1 for fragment in placement_fragments):
        errors.append(
            f"{surface}: managed public Execution Level block is displaced from "
            "its declared insertion point"
        )
    if errors:
        return [], errors
    return spans, []


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


def _execution_public_task_extension_errors(
    value: object,
    execution: dict[str, Any],
) -> list[str]:
    """Validate the lightweight decision-only public execution projection."""

    errors: list[str] = []
    context = "execution_level_contract.projection.public_task_extension"
    expected = {
        "version": "execution-level/v2",
        "ordered_labels": ["Level", "Basis", "L5 Evidence"],
        "line_fields": {
            "Level": [
                "requested",
                "automatic",
                "minimum",
                "default",
                "effective",
                "edit",
            ],
            "Basis": [
                "source",
                "triggers",
                "l1",
                "l2",
                "l5",
                "confirmation",
                "unresolved",
            ],
            "L5 Evidence": ["when", "requires"],
        },
    }
    if value != expected:
        errors.append(
            f"{context}: public task extension must be the exact decision-only "
            "execution-level/v2 schema"
        )
    return errors

def conditional_test_evidence_projection_text(contract: object) -> str:
    """Render the one public projection from the closed Core evidence values."""

    if not isinstance(contract, dict):
        raise ValueError("conditional test evidence contract must be an object")
    claims = contract.get("claim_values")
    if (
        not isinstance(claims, list)
        or len(claims) != 3
        or not all(isinstance(value, str) for value in claims)
    ):
        raise ValueError("conditional test evidence values cannot be projected")
    return (
        f"Record one `{claims[0]}` Claim for each normal behavior batch with its "
        f"Guard G approach, reason, oracle, evidence, and proof boundary. Record current "
        f"`{claims[1]}` and `{claims[2]}` only when applicable, with current proof after "
        "the final material edit; they are evidence, not a separate stage. Never "
        "fabricate unavailable proof."
    )


def professional_review_skill_ids(
    professional_entries: object,
    matrix: object,
) -> tuple[str, ...]:
    """Select every Professional Skill covered by the Core review-risk matrix."""

    expected_selector = {
        "registry": "professional-skills.yaml",
        "field": "role_support",
        "contains": "review-agent",
    }
    if not isinstance(matrix, dict) or matrix.get("registry_selector") != expected_selector:
        raise ValidationProblem(
            "professional review risk matrix must use the canonical dynamic registry selector"
        )
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


def professional_review_risk_matrix_block(matrix: object) -> str:
    """Render the single public Review Handoff projection of the Core matrix."""

    if not isinstance(matrix, dict):
        raise ValueError("professional review risk matrix must be an object")
    dimensions = matrix.get("dimensions")
    statuses = matrix.get("statuses")
    if (
        not isinstance(dimensions, list)
        or not dimensions
        or not all(isinstance(item, str) and item for item in dimensions)
        or not isinstance(statuses, list)
        or not statuses
        or not all(isinstance(item, str) and item for item in statuses)
    ):
        raise ValueError("professional review risk matrix cannot be projected")
    lines = [
        "<!-- BEGIN CHANGEFORGE CORE PROFESSIONAL RISK MATRIX -->",
        "For every assigned Review Skill at L1-L5, record exactly one decision per",
        "Core professional-risk dimension. Allowed statuses: "
        + ", ".join(f"`{status}`" for status in statuses)
        + ".",
        "`not-applicable` requires a source-backed reason and evidence. `delegated`",
        "requires a named registered Review Skill, scope, and reason. A missing,",
        "duplicate, or unknown dimension or status blocks the verdict.",
        "",
        "| Dimension | Status | Reason | Evidence | Specialist Skill | Delegated Scope |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    lines.extend(f"| `{dimension}` |  |  |  |  |  |" for dimension in dimensions)
    lines.append("<!-- END CHANGEFORGE CORE PROFESSIONAL RISK MATRIX -->")
    return "\n".join(lines)


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
        "build_profile_projection",
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
    build_projection = affected["build_profile_projection"]
    expected_build_projection = {
        "profiles": ["recommended", "full", "dev"],
        "producer_ids": {
            "recommended": "build-recommended",
            "full": "build-full",
            "dev": "build-dev",
        },
        "professional_candidate_field": "layer3_candidates",
        "foundation_scope_field": "delivery_scope",
        "foundation_shared_scope": "product",
        "unknown_package_policy": "all-profiles",
    }
    if build_projection != expected_build_projection:
        errors.append(
            "affected build_profile_projection must match the canonical build graph"
        )
    elif not set(build_projection["producer_ids"].values()).issubset(set(eligible)):
        errors.append("affected build profile producers must be stage-eligible")
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
    "execution-level",
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
        "unsupported-l1-downgrade",
        "execution-level",
        "effective-level-respects-all-floors",
        "decision-level-no-unsupported-downgrade",
    ),
    (
        "keyword-only-l5",
        "execution-level",
        "automatic-l5-requires-confirmed-analysis-evidence",
        "decision-level-l5-not-keyword-only",
    ),
    (
        "l5-confirmation-reroute",
        "professional-layer3-decision",
        "level-confirmation-preserves-semantic-route",
        "decision-level-confirmation-route-invariant",
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
            "decision_eval_contract.decision_axes must remain the exact seven axes"
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
        "external_read_contract",
        "evidence_localization_contract",
        "implementation_discipline_contract",
        "review_discipline_contract",
        "context_budget_contract",
        "final_goal_contract",
        "reference_contract",
        "decision_eval_contract",
        "route_decision_contract",
        "layer3_selector_contract",
        "execution_level_contract",
        "task_contract",
        "visible_evidence_contract",
        "completion_state",
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
            "normalization_path": [
                "external-source",
                "analysis-agent-judgment",
                "normalized-claim",
                "evidence-ledger",
                "engineering-brief-decision",
            ],
            "protected_control_fields": [
                "Role",
                "Skill",
                "Scope",
                "Execution Level",
                "Acceptance",
                "Owner",
                "Review Policy",
                "Task Contract",
            ],
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
        "ledger_projection": {
            "schema_source": "visible_evidence_contract",
            "capability_values": ["external-source-read"],
            "artifact_value": "source-identifier-or-url",
            "schema_change": "forbidden",
        },
        "missing_evidence": {
            "critical": {
                "trigger": "critical-fact-missing-can-invalidate-current-slice",
                "execution_trigger": "unknown-critical-boundary",
                "edit_status": "blocked",
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

    evidence_localization = data["evidence_localization_contract"]
    expected_evidence_localization = {
        "schema_version": 1,
        "applies_to": ["analysis-agent", "task-agent", "review-agent"],
        "purpose": "locate-current-source-evidence",
        "host_capabilities": {
            "required": ["read", "search"],
            "optional": ["symbol-search", "structural-search"],
            "structural_fallback": "read-search",
        },
        "location_sequence": {
            "known_exact": "direct-exact-read-no-search-or-duplicate-discovery",
            "unknown": "search-candidates-then-read",
            "widen": "only-when-current-evidence-is-insufficient",
            "proof": "minimum-complete-current-source-evidence",
        },
        "selector_only": [
            "top-k",
            "ranked-search",
            "semantic-search",
            "repo-map",
            "repo-graph",
            "truncated-search-result",
            "prior-summary",
            "nearby-file",
        ],
        "material_claim_source": "current-source-only",
        "completeness_claims": [
            "no-other-consumer",
            "no-other-same-pattern-occurrence",
            "no-other-affected-path",
            "unique-owner",
            "impact-scope-closed",
        ],
        "incomplete_coverage": "record-proof-limit",
        "minimum_complete_evidence": [
            "owner",
            "consumer",
            "invariant",
            "test",
            "contract",
            "validation-boundary",
        ],
        "evidence_reuse": {
            "allowed_anchors": [
                "path",
                "symbol-or-range",
                "claim",
                "scope",
                "freshness",
                "proof-limit",
            ],
            "forbidden_inheritance": [
                "coverage-conclusion",
                "correctness-conclusion",
            ],
            "review_independent_confirmation": True,
        },
        "direct_boundary": {
            "stable_owner": (
                "continue-direct-with-current-route-skill-level-and-scope"
            ),
            "material_boundaries": [
                "unknown-owner",
                "cross-module-or-public-contract",
                "security",
                "money",
                "migration",
                "other-material-boundary",
            ],
            "material_outcome": "stop-before-edit-return-main-for-analysis",
            "worker_route_or_skill_selection": False,
        },
        "authority_exclusions": [
            "route-selection",
            "professional-skill-selection",
            "layer3-selection",
            "execution-level",
            "task-scope-or-write-authority",
            "current-task-scope-blocker-adjacent-classification",
            "finding-classification",
            "review-or-repair-authority",
        ],
        "infrastructure_exclusions": [
            "locator-agent",
            "daemon",
            "index",
            "vector-database",
            "persistent-retrieval-state",
        ],
        "unchanged_authorities": [
            "route_decision_contract",
            "layer3_selector_contract",
            "execution_level_contract",
            "task-contract-v2-fields-and-order",
            "engineering-brief-authority",
            "review-and-finding-authority",
            "four-profile-architecture",
        ],
        "profile_projection": {
            "analysis-agent": [
                {
                    "rule_id": "analysis-localization",
                    "required_terms": [
                        "current source",
                        "direct read/search",
                        "minimum complete",
                        "counts are selectors only",
                        "Proof Limit",
                        "never correctness/coverage conclusions",
                    ],
                }
            ],
            "task-agent": [
                {
                    "rule_id": "task-localization",
                    "required_terms": [
                        "current source",
                        "direct read/search",
                        "minimum complete",
                        "bounded discovery",
                        "selectors only",
                        "Proof Limit",
                        "never inherit correctness/coverage",
                    ],
                }
            ],
            "review-agent": [
                {
                    "rule_id": "review-localization",
                    "required_terms": [
                        "independently",
                        "current source",
                        "direct read/search",
                        "minimum complete",
                        "selectors only",
                        "never inherit correctness/coverage",
                        "Proof Limit",
                    ],
                }
            ],
        },
        "cost_observation_fields": [
            "search_count",
            "exact_read_count",
            "broad_or_full_file_read_count",
            "repeated_read_count",
            "search_result_volume",
            "truncated_search_count",
            "evidence_byte_proxy",
            "time_to_owner_proof_step",
            "time_to_first_edit_step",
        ],
        "quality_cost_separation": {
            "quality_gate": "authoritative",
            "cost_observation": "secondary-after-quality",
            "cost_cannot_override_quality_failure": True,
        },
        "evidence_closure": {
            "requirement_outcomes": [
                "proved",
                "not-applicable",
                "legitimate-proof-limit",
            ],
            "closed_when": (
                "all-current-requirements-resolved-and-no-unresolved-material-risk"
            ),
            "post_closure_search_or_read": (
                "forbidden-without-new-or-invalidated-evidence-requirement"
            ),
            "stop_basis": "claim-completeness-not-search-top-k-or-file-count",
            "reopening": {
                "claim-local": "claim-local-bounded-reproof-no-analysis",
                "new-requirement": (
                    "bounded-discovery-for-new-evidence-requirement"
                ),
                "protected-or-material": (
                    "stop-edit-return-main-bounded-delta"
                ),
            },
            "contradiction_scope": "reopen-intersecting-claim-only",
            "material_proof_limit": "stop-before-edit-return-main",
            "profile_projection": {
                role: [
                    {
                        "rule_id": f"{role.removesuffix('-agent')}-evidence-closure",
                        "required_terms": [
                            "Evidence Closure:",
                            "proved/not-applicable/Proof Limit",
                            "no material risk",
                            "new/invalidated/contradicted",
                            "reopens affected only",
                            "protected/material returns Main/Delta",
                            "counts",
                        ],
                    }
                ]
                for role in ("analysis-agent", "task-agent", "review-agent")
            },
        },
    }
    if evidence_localization != expected_evidence_localization:
        errors.append(
            "Evidence Localization must equal the closed current-source, "
            "quality-first localization-only contract"
        )

    implementation_discipline = data["implementation_discipline_contract"]
    implementation_discipline_capability_id = ""
    if exact_keys(
        implementation_discipline,
        {
            "schema_version",
            "applies_to",
            "profile_capability_id",
            "adaptive_testing_contract",
            "guard_groups",
            "profile_projection",
        },
        "implementation_discipline_contract",
    ):
        assert isinstance(implementation_discipline, dict)
        if implementation_discipline["schema_version"] != 2:
            errors.append("implementation_discipline_contract.schema_version must be 2")
        if (
            implementation_discipline["applies_to"]
            != "every normal implementation task-agent"
        ):
            errors.append(
                "implementation_discipline_contract.applies_to must cover every "
                "normal implementation task-agent"
            )
        implementation_discipline_capability_id = implementation_discipline[
            "profile_capability_id"
        ]
        if implementation_discipline_capability_id != "task-implementation-discipline":
            errors.append(
                "implementation_discipline_contract.profile_capability_id must be "
                "'task-implementation-discipline'"
            )
        expected_adaptive_testing = {
            "schema_version": 1,
            "guard_id": "guard-g-adaptive-testing",
            "decision_fields": [
                "change_kind",
                "approach",
                "reason",
                "failure_mechanism",
                "boundary",
                "oracle",
                "risk_triggers",
                "evidence",
                "proof_boundary",
            ],
            "approaches": [
                "test-first",
                "test-after",
                "existing-proof-only",
                "non-test-validation",
            ],
            "test_first_required_for": [
                "reproducible-bug",
                "review-finding",
                "core-rule",
                "permission",
                "money",
                "idempotency",
                "concurrency",
                "state-machine",
                "public-contract",
                "migration",
            ],
            "high_risk_triggers": [
                "reproducible-bug",
                "review-finding",
                "core-rule",
                "permission",
                "money",
                "idempotency",
                "concurrency",
                "state-machine",
                "public-contract",
                "migration",
            ],
            "derived_high_risk_bindings": {
                "implementation_kind": {
                    "bugfix": ["reproducible-bug"],
                    "repair": ["review-finding"],
                    "migration": ["migration"],
                    "security": ["permission"],
                },
                "primary_skill": {
                    "data-api-contract-changer": ["public-contract"],
                    "security-privacy-gate": ["permission"],
                    "payment-trading-extension": ["money"],
                },
                "layer3_skill": {
                    "payment-trading-extension": ["money"],
                    "idempotency-retry-design": ["idempotency"],
                    "concurrency-control": ["concurrency"],
                    "state-machine-modeling": ["state-machine"],
                    "contract-testing": ["public-contract"],
                    "permission-boundary-modeling": ["permission"],
                },
                "task_risk_category": {
                    "permission": ["permission"],
                    "security": ["permission"],
                    "money": ["money"],
                    "idempotency": ["idempotency"],
                    "concurrency": ["concurrency"],
                    "state-machine": ["state-machine"],
                    "public-contract": ["public-contract"],
                    "migration": ["migration"],
                    "verified-bug": ["reproducible-bug"],
                    "review-finding": ["review-finding"],
                },
            },
            "behavior_batch_binding": "task-id-binds-all-material-edits",
            "selection_order": "before-first-material-edit",
            "current_proof_order": "after-final-material-edit",
            "unbound_independent_batch": "fail-closed",
            "valid_red_failure_class": "target-behavior-missing",
            "invalid_red_failure_classes": [
                "environment",
                "fixture",
                "import",
                "syntax",
                "unrelated",
            ],
            "test_after_only_for": [
                "low-risk-local-exploration",
                "existing-primary-coverage",
            ],
            "existing_proof_only_requires": [
                "existing-regression-mechanism",
                "no-new-uncovered-behavior",
                "fresh-post-edit-rerun",
            ],
            "non_test_validation_only_for": [
                "documentation",
                "comment",
                "formatting",
                "generated-sync",
                "static-config",
                "schema",
                "build",
            ],
            "material_edit_kinds": [
                "source",
                "test",
                "fixture",
                "schema",
                "configuration",
                "generated-artifact",
                "validation-command",
            ],
            "validation_outcomes_to_report": [
                "skipped",
                "flaky",
                "retried",
                "partial",
                "unavailable",
                "not-run",
            ],
            "insufficient_changed_behavior_proof": [
                "lint",
                "type-check",
                "build",
                "coverage",
                "manual-check",
                "full-suite",
            ],
            "high_risk_downgrade": "forbidden",
            "assertion_weakening": "forbidden",
            "non_behavior_red_green": "forbidden",
        }
        if implementation_discipline["adaptive_testing_contract"] != expected_adaptive_testing:
            errors.append(
                "implementation_discipline_contract.adaptive_testing_contract must "
                "equal the closed Core Guard G decision contract"
            )
        implementation_rule_ids = list(
            instruction_rule_groups(
                implementation_discipline["profile_projection"],
                "implementation_discipline_contract.profile_projection",
                allow_exact_rule=True,
            )
        )
        expected_implementation_rule_ids = [
            "inspect-before-edit",
            "inspection-stop-conditions",
            "observable-acceptance",
            "verified-bugfix-cause",
            "owner-first-placement",
            "placement-stop-conditions",
            "no-test-only-public-api",
            "smallest-complete-change",
            "adaptive-method-selection",
            "test-first-required",
            "red-proof-classification",
            "validation-integrity",
            "test-after-boundary",
            "existing-proof-only-boundary",
            "non-test-validation-boundary",
            "material-edit-staleness",
            "final-edit-rerun",
            "validation-outcome-reporting",
            "changed-behavior-proof",
        ]
        if implementation_rule_ids != expected_implementation_rule_ids:
            errors.append(
                "implementation_discipline_contract.profile_projection must define "
                f"the ordered universal guards {expected_implementation_rule_ids}"
            )
        guard_groups = implementation_discipline["guard_groups"]
        actual_guard_groups: list[tuple[str, list[str]]] = []
        if not isinstance(guard_groups, list) or not guard_groups:
            errors.append(
                "implementation_discipline_contract.guard_groups must be a non-empty list"
            )
        else:
            for index, group in enumerate(guard_groups):
                context = f"implementation_discipline_contract.guard_groups[{index}]"
                if not exact_keys(
                    group,
                    {"guard_group_id", "profile_rule_ids"},
                    context,
                ):
                    continue
                assert isinstance(group, dict)
                guard_group_id = group["guard_group_id"]
                if not isinstance(guard_group_id, str) or re.fullmatch(
                    r"[a-z0-9]+(?:-[a-z0-9]+)*", guard_group_id
                ) is None:
                    errors.append(f"{context}.guard_group_id must be kebab-case")
                    continue
                profile_rule_ids = string_list(
                    group["profile_rule_ids"],
                    f"{context}.profile_rule_ids",
                )
                actual_guard_groups.append((guard_group_id, profile_rule_ids))
        expected_guard_groups = [
            (
                "inspect-before-edit",
                ["inspect-before-edit", "inspection-stop-conditions"],
            ),
            ("observable-acceptance", ["observable-acceptance"]),
            ("verified-bugfix-cause", ["verified-bugfix-cause"]),
            (
                "owner-first-placement",
                [
                    "owner-first-placement",
                    "placement-stop-conditions",
                    "no-test-only-public-api",
                ],
            ),
            ("smallest-complete-change", ["smallest-complete-change"]),
            (
                "adaptive-testing",
                [
                    "adaptive-method-selection",
                    "test-first-required",
                    "red-proof-classification",
                    "validation-integrity",
                    "test-after-boundary",
                    "existing-proof-only-boundary",
                    "non-test-validation-boundary",
                ],
            ),
            (
                "universal-validation",
                [
                    "material-edit-staleness",
                    "final-edit-rerun",
                    "validation-outcome-reporting",
                    "changed-behavior-proof",
                ],
            ),
        ]
        if actual_guard_groups != expected_guard_groups:
            errors.append(
                "implementation_discipline_contract.guard_groups must define exactly "
                "the seven ordered semantic guard groups and their profile rules"
            )
        elif [
            rule_id
            for _, profile_rule_ids in actual_guard_groups
            for rule_id in profile_rule_ids
        ] != implementation_rule_ids:
            errors.append(
                "implementation_discipline_contract.guard_groups must cover the "
                "profile projection exactly once in order"
            )

    review_discipline = data["review_discipline_contract"]
    review_discipline_capability_id = ""
    review_discipline_fields = {
        "schema_version",
        "applies_to",
        "profile_capability_id",
        "review_input_readiness",
        "generic_capability_contract",
        "trace_action",
        "event_fields",
        "diff_fields",
        "validation_fields",
        "base_dimensions",
        "level_base_dimensions",
        "dimension_decisions",
        "professional_risk_matrix",
        "diff_kinds",
        "validation_sources",
        "validation_results",
        "evidence_sources",
        "forbidden_evidence_sources",
        "review_kinds",
        "verdicts",
        "repair_order",
        "level_extension_rule",
        "review_frequency_policy",
        "preimplementation_convergence",
        "validation_evidence_reuse",
        "complete_review_pass",
        "review_boundary_contract",
        "obligation_subsumption",
        "material_edit_invalidation_policy",
        "repair_invalidation_policy",
        "review_scope",
        "finding_policy_source",
        "effective_level_policy",
        "profile_projection",
        "handoff_projection",
    }
    if exact_keys(
        review_discipline,
        review_discipline_fields,
        "review_discipline_contract",
    ):
        assert isinstance(review_discipline, dict)
        if review_discipline["schema_version"] != 2:
            errors.append("review_discipline_contract.schema_version must be 2")
        if review_discipline["applies_to"] != "every implementation or repair review at L1-L5":
            errors.append(
                "review_discipline_contract.applies_to must cover every "
                "implementation or repair review at L1-L5"
            )
        review_discipline_capability_id = review_discipline["profile_capability_id"]
        if review_discipline_capability_id != "review-discipline":
            errors.append(
                "review_discipline_contract.profile_capability_id must be "
                "'review-discipline'"
            )
        if review_discipline["trace_action"] != "review-discipline":
            errors.append(
                "review_discipline_contract.trace_action must be 'review-discipline'"
            )
        readiness = review_discipline["review_input_readiness"]
        if not isinstance(readiness, dict) or readiness.get(
            "required_fields"
        ) != [
            "latest_changed_paths",
            "exact_change_evidence",
            "reviewer_capability_accessibility",
            "validation_after_latest_material_edit",
            "fixed_review_scope",
        ] or readiness.get("review_dispatch_count_when_missing") != 0:
            errors.append(
                "review input readiness must fail before review dispatch when "
                "any producer evidence is missing"
            )
        elif readiness.get("native_evidence_fields") != [
            "reference",
            "generation",
            "reviewer",
            "changed_paths",
            "readable",
        ] or readiness.get("native_evidence_rule") != (
            "structured-current-reference-binds-assigned-reviewer-generation-"
            "changed-paths-and-readability"
        ):
            errors.append(
                "native review evidence must bind the assigned reviewer, current "
                "generation, exact changed paths, and readable instance"
            )
        capability_contract = review_discipline["generic_capability_contract"]
        capability_contract_fields = {
            "fields",
            "injected_fields",
            "states",
            "decision_inputs",
            "ignored_adapter_metadata",
            "equivalence_rule",
            "prompt_branches",
        }
        if not exact_keys(
            capability_contract,
            capability_contract_fields,
            "review_discipline_contract.generic_capability_contract",
        ):
            capability_contract = {}
        if capability_contract.get(
            "decision_inputs"
        ) != "capability-state-only" or capability_contract.get(
            "equivalence_rule"
        ) != (
            "equal-capability-state-produces-equal-routing-level-review-and-"
            "completion-decisions"
        ):
            errors.append(
                "generic control decisions must depend only on normalized "
                "capability state"
            )
        elif capability_contract.get("fields") != [
            "bounded-source-read",
            "workspace-mutation",
            "non-mutating-validation",
            "native-change-read",
            "change-evidence-export",
            "supplied-change-delivery",
            "reviewer-change-consume",
            "workspace-state-observation",
        ] or capability_contract.get("injected_fields") != capability_contract.get(
            "fields"
        ) or capability_contract.get("states") != ["supported", "unsupported"]:
            errors.append("generic capability vocabulary must remain closed and ordered")
        else:
            capability_fields = capability_contract["fields"]
            prompt_branches = capability_contract.get("prompt_branches")
            expected_prompt_fields = [
                "native-change-read",
                "change-evidence-export",
                "supplied-change-delivery",
                "reviewer-change-consume",
                "non-mutating-validation",
            ]
            if not isinstance(prompt_branches, list) or [
                branch.get("field") if isinstance(branch, dict) else None
                for branch in prompt_branches
            ] != expected_prompt_fields:
                errors.append(
                    "generic capability prompt branches must use the five canonical "
                    "injected decision fields in order"
                )
            else:
                for index, branch in enumerate(prompt_branches):
                    if not exact_keys(
                        branch,
                        {"field", "next_field", "branches"},
                        f"review_discipline_contract.generic_capability_contract."
                        f"prompt_branches[{index}]",
                    ):
                        continue
                    field = branch["field"]
                    if field not in capability_fields:
                        errors.append(
                            f"generic capability prompt field {field!r} is not injected"
                        )
                    expected_next = (
                        expected_prompt_fields[index + 1]
                        if index + 1 < len(expected_prompt_fields)
                        else None
                    )
                    if branch["next_field"] != expected_next:
                        errors.append(
                            "generic capability prompt branches must form one ordered chain"
                        )
                    modes = branch["branches"]
                    if not isinstance(modes, list) or [
                        mode.get("value") if isinstance(mode, dict) else None
                        for mode in modes
                    ] != ["supported", "unsupported"]:
                        errors.append(
                            f"generic capability prompt field {field!r} must use closed states"
                        )
        expected_event_fields = [
            "actor",
            "action",
            "schema_version",
            "task_id",
            "execution_level",
            "review_kind",
            "diff",
            "validation",
            "evidence_source",
            "dimensions",
            "professional_risks",
            "verdict",
        ]
        if review_discipline["event_fields"] != expected_event_fields:
            errors.append(
                "review_discipline_contract.event_fields must define the exact "
                "lightweight typed event"
            )
        if review_discipline["diff_fields"] != [
            "kind",
            "artifact",
            "generation",
            "changed_files",
        ]:
            errors.append("review_discipline_contract.diff_fields are not canonical")
        if review_discipline["validation_fields"] != [
            "source",
            "evidence_id",
            "result",
            "generation",
        ]:
            errors.append(
                "review_discipline_contract.validation_fields are not canonical"
            )
        expected_dimensions = [
            "actual-latest-diff",
            "every-changed-file",
            "observable-acceptance",
            "validation-freshness",
            "regression-mechanism",
            "negative-boundary-behavior",
            "ownership-placement",
            "unnecessary-scope",
            "unverified-scope",
            "residual-risk",
        ]
        if review_discipline["base_dimensions"] != expected_dimensions:
            errors.append(
                "review_discipline_contract.base_dimensions must define the ten "
                "ordered non-bypassable review dimensions"
            )
        expected_level_dimensions = {
            level: expected_dimensions for level in ("L1", "L2", "L3", "L4", "L5")
        }
        if review_discipline["level_base_dimensions"] != expected_level_dimensions:
            errors.append(
                "review_discipline_contract.level_base_dimensions must keep the "
                "same base dimensions at L1-L5"
            )
        professional_risk_matrix = review_discipline["professional_risk_matrix"]
        matrix_fields = {
            "schema_version",
            "registry_selector",
            "dimensions",
            "level_dimensions",
            "statuses",
            "decision_fields",
            "not_applicable_required_fields",
            "delegated_required_fields",
            "invalid_matrix_rule",
            "evaluation_scope",
            "repository_health_audit",
            "allowed_context_reads",
            "context_read_grants_repair_authority",
            "specialist_trigger",
        }
        expected_professional_dimensions = [
            "correctness-invariants",
            "authority-security-privacy",
            "failure-recovery-concurrency",
            "performance-resources",
            "contracts-data-consumers",
            "tests-evidence",
            "maintainability-structure",
            "operations-documentation-release",
        ]
        if exact_keys(
            professional_risk_matrix,
            matrix_fields,
            "review_discipline_contract.professional_risk_matrix",
        ):
            assert isinstance(professional_risk_matrix, dict)
            expected_selector = {
                "registry": "professional-skills.yaml",
                "field": "role_support",
                "contains": "review-agent",
            }
            if professional_risk_matrix["schema_version"] != 1:
                errors.append(
                    "review_discipline_contract.professional_risk_matrix.schema_version "
                    "must be 1"
                )
            if professional_risk_matrix["registry_selector"] != expected_selector:
                errors.append(
                    "review_discipline_contract.professional_risk_matrix must select "
                    "all professional registry Skills supporting review-agent"
                )
            if professional_risk_matrix["dimensions"] != expected_professional_dimensions:
                errors.append(
                    "review_discipline_contract.professional_risk_matrix.dimensions "
                    "must define the eight ordered professional-risk dimensions"
                )
            expected_professional_levels = {
                level: expected_professional_dimensions
                for level in ("L1", "L2", "L3", "L4", "L5")
            }
            if (
                professional_risk_matrix["level_dimensions"]
                != expected_professional_levels
            ):
                errors.append(
                    "review_discipline_contract.professional_risk_matrix.level_dimensions "
                    "must keep all eight dimensions at L1-L5"
                )
            matrix_closed_values = {
                "statuses": [
                    "verified",
                    "finding",
                    "not-applicable",
                    "delegated",
                    "blocked",
                ],
                "decision_fields": [
                    "dimension",
                    "status",
                    "reason",
                    "evidence",
                    "specialist_skill",
                    "scope",
                ],
                "not_applicable_required_fields": ["reason", "evidence"],
                "delegated_required_fields": [
                    "specialist_skill",
                    "scope",
                    "reason",
                ],
            }
            for field, expected in matrix_closed_values.items():
                if professional_risk_matrix[field] != expected:
                    errors.append(
                        "review_discipline_contract.professional_risk_matrix."
                        f"{field} must equal {expected}"
                    )
            if professional_risk_matrix["invalid_matrix_rule"] != "block-verdict":
                errors.append(
                    "review_discipline_contract.professional_risk_matrix invalid "
                    "content must block the verdict"
                )
            expected_matrix_scope = [
                "Current Task Boundary",
                "latest actual diff",
                "current change reachable impact",
            ]
            if professional_risk_matrix["evaluation_scope"] != expected_matrix_scope:
                errors.append(
                    "review professional-risk evaluation scope must be the current "
                    "task, latest diff, and reachable change impact"
                )
            if professional_risk_matrix["repository_health_audit"] is not False:
                errors.append(
                    "review professional-risk matrix must not become a repository "
                    "health audit"
                )
            if professional_risk_matrix["allowed_context_reads"] != [
                "caller",
                "consumer",
                "sibling",
                "config",
            ]:
                errors.append(
                    "review professional-risk context reads must remain bounded"
                )
            if (
                professional_risk_matrix["context_read_grants_repair_authority"]
                is not False
            ):
                errors.append(
                    "review context reads must not grant repair authority"
                )
            if (
                professional_risk_matrix["specialist_trigger"]
                != "concrete-risk-requires-independent-professional-judgment"
            ):
                errors.append(
                    "review specialist gates must be triggered only by concrete risk"
                )
        closed_lists = {
            "dimension_decisions": ["verified", "finding", "not-applicable", "blocked"],
            "diff_kinds": ["actual-diff", "host-native-actual-diff", "unavailable"],
            "validation_sources": ["trajectory-validation", "supplied-validation", "unavailable"],
            "validation_results": ["passed", "failed", "unavailable"],
            "evidence_sources": ["independent-review", "unavailable"],
            "forbidden_evidence_sources": ["implementer-reasoning", "changed-file-summary"],
            "review_kinds": ["implementation", "repair"],
            "verdicts": ["pass", "findings", "blocked"],
            "repair_order": ["fresh-validation", "latest-actual-diff", "fresh-re-review"],
        }
        for field, expected in closed_lists.items():
            if review_discipline[field] != expected:
                errors.append(
                    f"review_discipline_contract.{field} must equal {expected}"
                )
        if (
            review_discipline["level_extension_rule"]
            != "depth-independence-additional-evidence-only"
        ):
            errors.append(
                "review_discipline_contract.level_extension_rule may add only "
                "depth, independence, or evidence"
            )
        expected_review_frequency_policy = {
            "separation_rule": (
                "effective-level-decides-depth-review-or-risk-boundary-decides-frequency"
            ),
            "task_completion_triggers_review": False,
            "minimum_sufficient_review_boundaries": True,
            "defaults": {
                "L1-L3": "one-combined-independent-final-review",
                "L4": "same-frequency-plus-triggered-professional-depth",
                "L5": "required-independent-preimplementation-and-final-review",
            },
            "intermediate_review_triggers": [
                "delayed-review-materially-increases-downstream-risk",
                "downstream-consumer-would-commit-to-a-materially-risky-contract",
                "materially-irreversible-or-wide-blast-radius-before-final-review",
                "L5-or-explicit-professional-gate",
            ],
        }
        if review_discipline["review_frequency_policy"] != expected_review_frequency_policy:
            errors.append(
                "review_discipline_contract.review_frequency_policy must separate "
                "Effective Level depth from minimum-sufficient Review Boundary frequency"
            )
        expected_preimplementation_convergence = {
            "L1-L3": "forbidden",
            "L4": "material-intermediate-trigger-per-unchanged-boundary",
            "L5": "mandatory-independent",
            "keyword_only_trigger": "forbidden",
            "review_boundary": "fixed-and-complete-finding-frontier",
            "ordinary_finding": "record-and-continue-boundary",
            "finding_boundary_expansion": "forbidden",
            "post_delta_or_repair": "scoped-verification-or-scoped-rereview",
            "post_delta_expanded_pre_review": (
                "current-trigger-exact-nonempty-new-task-expansion-"
                "material_boundary_expanded-true-broad-false"
            ),
            "repeat_broad_review": (
                "forbidden-without-protected-decision-or-material-boundary-expansion"
            ),
            "preparation_loop": "forbidden-without-new-material-evidence",
        }
        if (
            review_discipline["preimplementation_convergence"]
            != expected_preimplementation_convergence
        ):
            errors.append(
                "review_discipline_contract.preimplementation_convergence must "
                "close risk-triggered pre-review without repeated broad review"
            )
        expected_validation_reuse = {
            "default": "reuse-unless-a-declared-reproduction-trigger-applies",
            "required_qualities": ["fresh", "scope-correct", "trustworthy-oracle"],
            "reproduction_triggers": [
                "stale-evidence",
                "coverage-gap",
                "suspicious-oracle-or-test",
                "flaky-or-retry",
                "environment-sensitive-result",
                "concrete-reviewer-doubt",
                "effective-level-or-professional-risk-independent-reproduction",
            ],
            "reviewer_independence_requires_duplicate_execution": False,
        }
        if review_discipline["validation_evidence_reuse"] != expected_validation_reuse:
            errors.append(
                "review_discipline_contract.validation_evidence_reuse must reuse "
                "fresh scoped trustworthy evidence unless a closed trigger applies"
            )
        expected_complete_review_pass = {
            "ordinary_material_finding_action": (
                "record-and-continue-fixed-review-boundary"
            ),
            "initial_review_completion_requirements": [
                "required-changed-scope",
                "base-review-dimensions",
                "required-professional-risk-dimensions",
            ],
            "rereview_completion_requirements": [
                "inherited-finding-resolution",
                "repair-diff-correctness",
                "repair-regression",
                "repair-affected-scope-and-transitive-dependents",
                "frozen-acceptance-invariant-contract-and-professional-risk-boundary",
            ],
            "handoff_contents": (
                "all-evidence-backed-findings-from-current-review-round-and-fixed-boundary"
            ),
            "finding_expands_review_boundary": False,
            "early_block_triggers": [
                "fundamental-architecture-error",
                "invalid-public-contract",
                "major-security-defect",
                "acceptance-fundamentally-unmet",
            ],
            "early_block_scope_report": ["Reviewed Scope", "Unreviewed Scope"],
            "post_dispatch_block": {
                "timing": "after-review-input-ready-and-dispatch",
                "reasons": [
                    "required-review-evidence-or-surface-unavailable",
                    "required-current-evidence-stale",
                    "protected-authority-or-engineering-brief-invalidated",
                ],
                "required_scope_report": [
                    "Reviewed Scope",
                    "Unreviewed Scope",
                    "Proof Limit",
                ],
                "authority_invalidation_route": [
                    "blocked",
                    "main-control-agent",
                    "analysis-agent",
                ],
                "forbidden_reasons": [
                    "ordinary-uncertainty",
                    "ordinary-difficulty",
                    "ordinary-finding",
                    "continuable-evidence-gap",
                ],
            },
            "round_completion_actions": ["review", "re-review"],
            "initial_review_outcomes_require_complete_boundary": True,
            "rereview_outcomes_require_focused_boundary": True,
            "pass_requires_no_blocking_findings": True,
        }
        if review_discipline["complete_review_pass"] != expected_complete_review_pass:
            errors.append(
                "review_discipline_contract.complete_review_pass must accumulate "
                "ordinary findings through the complete fixed Review Boundary"
            )
        expected_review_boundary_contract = {
            "schema_version": 1,
            "boundary_fields": [
                "Review Boundary ID",
                "Review Strategy",
                "Review Round ID",
                "Effective Level",
                "Required Review Skills",
                "Specialist Obligations",
                "Covered Task IDs",
                "Required Changed Scope",
                "Professional Risk Dimensions",
                "Required Validation / Evidence Binding",
                "Review Assignments",
                "Primary Close Ordering",
            ],
            "assignment_fields": [
                "assignment_id",
                "role",
                "profile",
                "review_skill",
                "layer3_skills",
                "layer3_selection_basis",
                "scope",
            ],
            "assignment_roles": ["primary", "specialist"],
            "assignment_profile": "review-agent",
            "primary_assignment_count": "exactly-one",
            "specialist_assignment_count": "zero-or-more",
            "review_skill_per_assignment": "exactly-one",
            "maximum_layer3_skills_per_assignment": 3,
            "layer3_selection_basis": "review-risk",
            "layer3_selection_rule": (
                "review-risk-independent-of-task-layer3-union"
            ),
            "assignment_scope": "non-empty-bounded-scope",
            "shared_round_rule": (
                "all-boundary-assignments-share-one-review-round-id"
            ),
            "round_count_rule": (
                "specialist-results-do-not-increment-review-round-count"
            ),
            "specialist_completion_rule": (
                "specialist-results-do-not-close-covered-tasks"
            ),
            "close_order": (
                "specialists-before-primary-close-in-one-shared-round"
            ),
            "primary_close_rule": (
                "primary-consumes-every-current-required-specialist-result-and-"
                "emits-the-sole-closing-artifact"
            ),
            "artifact_fields": [
                "artifact_id",
                "artifact_digest",
                "review_boundary_id",
                "review_round_id",
                "covered_task_ids",
                "required_changed_scope",
                "evidence_scope",
                "task_generations",
                "assignment_result_ids",
                "primary_assignment_id",
                "verdict",
            ],
            "task_completion_projection_fields": [
                "task_id",
                "artifact_id",
                "artifact_digest",
                "review_boundary_id",
                "review_round_id",
                "generation",
            ],
            "artifact_identity_fields": ["artifact_id", "artifact_digest"],
            "artifact_generation_rule": "current-for-every-covered-task",
            "task_completion_projection_rule": (
                "one-exact-artifact-projection-per-covered-task"
            ),
            "task_node_requirement_fields": [
                "Required Review Skills",
                "Specialist Obligations",
                "Professional Risk Dimensions",
            ],
            "task_node_forbidden_scheduling_fields": [
                "Review Strategy",
                "Review Round ID",
                "Review Assignments",
                "Primary Close Ordering",
            ],
            "legacy_fixture_boundary_fields": [
                "effective_level",
                "primary_review_skill",
                "required_review_skills",
                "specialist_obligations",
                "covered_task_ids",
                "required_changed_scope",
                "professional_risk_dimensions",
                "required_validation_evidence_binding",
            ],
        }
        if review_discipline["review_boundary_contract"] != expected_review_boundary_contract:
            errors.append(
                "review_discipline_contract.review_boundary_contract must define "
                "assignment-aware combined review, one shared round, and one artifact"
            )
        expected_subsumption = {
            "satisfier": "same-or-stronger-current-independent-review",
            "review_boundary_fields": [
                "Review Boundary ID",
                "Review Strategy",
                "Review Round ID",
                "Effective Level",
                "Required Review Skills",
                "Specialist Obligations",
                "Covered Task IDs",
                "Required Changed Scope",
                "Professional Risk Dimensions",
                "Required Validation / Evidence Binding",
                "Review Assignments",
                "Primary Close Ordering",
            ],
            "primary_review_assignment_per_boundary": "exactly-one",
            "required_validation_evidence_binding": {
                "generation": "current",
                "coverage": "covered-task-ids",
            },
            "coverage_dimensions": [
                "review-boundary-id",
                "review-strategy",
                "review-round-id",
                "effective-level",
                "required-review-skills",
                "specialist-obligations",
                "covered-task-ids",
                "required-changed-scope",
                "professional-risk-dimensions",
                "required-validation-evidence-binding",
                "review-assignments",
                "primary-close-ordering",
            ],
            "unique_specialist_obligations_preserved": True,
            "weaker_equivalent_review_obligations": "satisfied-without-repeat",
            "covering_repair_rereview_satisfies_final_review": True,
        }
        if review_discipline["obligation_subsumption"] != expected_subsumption:
            errors.append(
                "review_discipline_contract.obligation_subsumption must close all "
                "all Review Boundary dimensions without dropping Specialist obligations"
            )
        expected_material_edit_invalidation = {
            "default_scope": (
                "intersecting-scope-and-transitive-task-dependencies-only"
            ),
            "invalidates": ["validation-evidence", "review-evidence"],
            "retains": "unaffected-current-evidence",
            "dependency_direction": "downstream-transitive-dependents",
            "requires_declared_changed_scope": True,
            "full_boundary_invalidation_by_default": False,
        }
        if (
            review_discipline["material_edit_invalidation_policy"]
            != expected_material_edit_invalidation
        ):
            errors.append(
                "review_discipline_contract.material_edit_invalidation_policy must "
                "invalidate only intersecting and transitive dependent evidence"
            )
        expected_repair_invalidation = {
            "default_scope": "intersecting-and-transitively-dependent-evidence-only",
            "invalidates": [
                "repair-intersecting-scope",
                "claims-dependent-on-modified-behavior",
                "transitive-repair-impact",
            ],
            "retains": "unaffected-fresh-evidence",
            "rereview_focus": [
                "inherited-finding-resolution",
                "repair-diff-correctness",
                "repair-regression",
                "repair-affected-scope-and-transitive-dependents",
                "frozen-acceptance-invariant-contract-and-professional-risk-boundary",
            ],
            "initial_review_rule": (
                "complete-fixed-review-boundary-changed-scope-base-dimensions-"
                "and-professional-risk-dimensions"
            ),
            "rereview_rule": (
                "focused-rereview-only-without-reopening-frozen-boundary"
            ),
            "scope_expansion_triggers": [
                "public-or-shared-contract",
                "schema",
                "common-abstraction",
                "ownership",
                "dependency-graph",
                "security-boundary",
                "transaction-or-concurrency-semantics",
                "integration-behavior",
            ],
            "full-history-rereview-by-default": False,
        }
        if review_discipline["repair_invalidation_policy"] != expected_repair_invalidation:
            errors.append(
                "review_discipline_contract.repair_invalidation_policy must invalidate "
                "only intersecting or dependent evidence and expand at named boundaries"
            )
        expected_review_scope = {
            "task_boundary_source": "task_contract.task_boundary",
            "handoff_projection_fields": [
                "Acceptance",
                "Review Boundary",
                "Effective Level",
                "Required Review Skills",
                "Required Changed Scope",
                "Latest Actual Diff or Accessible Reference",
                "Current Structured Validation",
                "Relevant Current Evidence",
                "Scope",
                "Freshness",
                "Proof Limit",
                "Unverified Scope",
            ],
            "read_grants_repair_authority": False,
            "finding_relation_precedes": ["severity", "blocker"],
        }
        if review_discipline["review_scope"] != expected_review_scope:
            errors.append(
                "review_discipline_contract.review_scope must project the current "
                "Task Boundary and write ceiling without granting repair authority"
            )
        if (
            review_discipline["finding_policy_source"]
            != "task_contract.finding_relations"
        ):
            errors.append(
                "review finding classification must use task_contract.finding_relations"
            )
        expected_effective_level_policy = {
            "source": "execution_level_contract.effective_level",
            "creates_review_level": False,
            "all_levels_require_base_dimensions": True,
            "final_review_profile": "review-agent",
            "final_review_target": ["latest actual diff", "every changed file"],
            "level_increases_only": [
                "review-depth",
                "evidence-strength",
                "independence",
                "actual-professional-gates",
            ],
            "specialist_review_replaces_final_review": False,
            "finding_merge_owner": "review-agent",
            "main_merges_professional_findings": False,
            "reviewer_repairs_own_findings": False,
            "levels": {
                "L1": {
                    "final_reviewers": 1,
                    "independent_final_review": True,
                    "professional_risk_matrix": "base",
                    "preimplementation_review": False,
                    "secondary_reviewer": False,
                },
                "L2": {
                    "final_reviewers": 1,
                    "independent_final_review": True,
                    "professional_risk_matrix": "base",
                    "preimplementation_review": False,
                    "secondary_reviewer": False,
                },
                "L3": {
                    "final_reviewers": 1,
                    "independent_final_review": True,
                    "professional_risk_matrix": "base",
                    "risk_triggered_jit_lenses": True,
                    "preimplementation_review": False,
                    "secondary_reviewer": False,
                },
                "L4": {
                    "final_reviewers": 1,
                    "independent_final_review": True,
                    "professional_gates": "actual-triggered-only",
                    "specialist_condition": (
                        "concrete-risk-requires-independent-professional-judgment"
                    ),
                    "preimplementation_condition": (
                        "risk-carried-by-preimplementation-design-decision"
                    ),
                    "default_preimplementation_review": False,
                    "default_secondary_reviewer": False,
                },
                "L5": {
                    "independent_preimplementation_review": True,
                    "independent_implementation_review": True,
                    "declared_scope_negative_and_failure_proof": True,
                    "exhaustive_final_review": True,
                    "full_ci_required": False,
                    "formal_release_required": False,
                    "cross_model_review_required": False,
                },
            },
            "new_high_risk_route": [
                "finding",
                "blocked",
                "main-control-agent",
                "analysis-agent",
                "update-engineering-brief",
                "recompute-effective-level",
                "redispatch",
            ],
            "reviewer_self_upgrades_execution_level": False,
            "ordinary_l1_l3_agent_count_increase": False,
            "ordinary_l1_l3_review_round_increase": False,
        }
        if (
            review_discipline["effective_level_policy"]
            != expected_effective_level_policy
        ):
            errors.append(
                "review_discipline_contract.effective_level_policy must derive "
                "closed review depth from the existing Effective Level"
            )
        review_rule_ids = list(
            instruction_rule_groups(
                review_discipline["profile_projection"],
                "review_discipline_contract.profile_projection",
                allow_exact_rule=True,
            )
        )
        if review_rule_ids != [
            "uniform-review-dimensions",
            "professional-risk-matrix",
            "repair-review-order",
            "initial-review-and-focused-rereview",
            "rereview-finding-classification",
            "review-frequency-and-subsumption",
            "validation-evidence-reuse",
            "material-findings-and-fail-fast",
            "complete-review-pass",
        ]:
            errors.append(
                "review_discipline_contract.profile_projection must define the "
                "uniform dimensions, risk matrix, repair, frequency, reuse, finding, "
                "Initial/Re-review convergence, and complete-pass rules"
            )
        handoff_projection = review_discipline["handoff_projection"]
        if exact_keys(
            handoff_projection,
            {"target", "required_terms"},
            "review_discipline_contract.handoff_projection",
        ):
            assert isinstance(handoff_projection, dict)
            if handoff_projection["target"] != "review-handoff-template.md":
                errors.append(
                    "review_discipline_contract.handoff_projection must target "
                    "review-handoff-template.md"
                )
            handoff_terms = string_list(
                handoff_projection["required_terms"],
                "review_discipline_contract.handoff_projection.required_terms",
            )
            dimension_projection_terms = {
                "negative-boundary-behavior": "negative and boundary behavior",
                "ownership-placement": "ownership and placement",
            }
            missing_dimension_terms = [
                dimension_projection_terms.get(dimension, dimension.replace("-", " "))
                for dimension in expected_dimensions
                if dimension_projection_terms.get(
                    dimension, dimension.replace("-", " ")
                )
                not in handoff_terms
            ]
            if missing_dimension_terms:
                errors.append(
                    "review_discipline_contract.handoff_projection must name every "
                    f"base dimension: missing {missing_dimension_terms}"
                )
            professional_projection_terms = [
                "Professional Risk Matrix",
                *expected_professional_dimensions,
                "source-backed reason and evidence",
                "named registered Review Skill, scope, and reason",
            ]
            missing_professional_terms = [
                term for term in professional_projection_terms if term not in handoff_terms
            ]
            if missing_professional_terms:
                errors.append(
                    "review_discipline_contract.handoff_projection must name the "
                    "professional-risk matrix contract: missing "
                    f"{missing_professional_terms}"
                )

    context_budget = data["context_budget_contract"]
    context_budget_fields = {
        "schema_version",
        "tokenizer",
        "budget_classes",
        "duplicate_rule_token_ratio_max",
    }
    if exact_keys(
        context_budget,
        context_budget_fields,
        "context_budget_contract",
    ):
        assert isinstance(context_budget, dict)
        if context_budget["schema_version"] != 2:
            errors.append("context_budget_contract.schema_version must be 2")
        if context_budget["tokenizer"] != "o200k_base":
            errors.append("context_budget_contract.tokenizer must be o200k_base")
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
                    "capacity_ceiling",
                    "minimum_headroom_ratio",
                }
                if budget_class == "main":
                    expected_entry_fields.add("minimum_release_margin_tokens")
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
                limits = derived_context_budget_limits(context_budget)
            except ValueError as exc:
                errors.append(f"context_budget_contract: {exc}")
                limits = {}
            main_limit = limits.get("main")
            if main_limit is not None and (
                main_limit["capacity_ceiling"] != 2200
                or main_limit["minimum_headroom_ratio"] != 0.10
                or main_limit["minimum_release_margin_tokens"] != 80
            ):
                errors.append(
                    "main context budget must use capacity_ceiling 2200 and "
                    "minimum_headroom_ratio 0.10 with an 80-token minimum release margin"
                )
        duplicate_ratio = context_budget["duplicate_rule_token_ratio_max"]
        if (
            isinstance(duplicate_ratio, bool)
            or not isinstance(duplicate_ratio, (int, float))
            or not 0 <= duplicate_ratio < 1
        ):
            errors.append(
                "context_budget_contract.duplicate_rule_token_ratio_max must be in [0, 1)"
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
                or thresholds["maximum_fresh_target_count"] > 189
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

    route_decision = data["route_decision_contract"]
    route_decision_fields = {
        "schema_version",
        "envelope_fields",
        "path_values",
        "path_start_profiles",
        "route_result_fields",
        "selection_evidence_fields",
        "task_evidence_fields",
        "candidate_fields",
        "main_analysis_assignment_fields",
        "main_execution_provenance_fields",
        "execution_provenance_by_path",
        "maximum_layer3_skills",
        "main_execution_producer",
    }
    if exact_keys(
        route_decision,
        route_decision_fields,
        "route_decision_contract",
    ):
        assert isinstance(route_decision, dict)
        if route_decision["schema_version"] != 1:
            errors.append("route_decision_contract.schema_version must be 1")
        exact_route_lists = {
            "envelope_fields": [
                "path",
                "route_result",
                "selection_evidence",
                "main_execution_provenance",
                "route_once",
            ],
            "path_values": ["direct", "analyzed"],
            "route_result_fields": [
                "start_profile",
                "primary_skill",
                "layer3_skills",
                "review_skill",
                "execution_level",
                "level_basis",
            ],
            "selection_evidence_fields": [
                "task_evidence",
                "primary_candidates",
                "review_candidates",
                "layer3_candidates",
                "eligible_primary_count",
            ],
            "task_evidence_fields": ["id", "kind", "task_id", "source_anchor"],
            "candidate_fields": [
                "skill",
                "eligible",
                "evidence_ids",
                "rejection_reasons",
            ],
            "main_analysis_assignment_fields": [
                "producer",
                "task_id",
            ],
            "main_execution_provenance_fields": [
                "producer",
                "task_id",
                "execution_level",
                "level_basis",
            ],
        }
        for field, expected in exact_route_lists.items():
            actual = string_list(
                route_decision[field],
                f"route_decision_contract.{field}",
            )
            if actual != expected:
                errors.append(
                    f"route_decision_contract.{field} must remain exactly {expected}"
                )
        path_start_profiles = route_decision["path_start_profiles"]
        if exact_keys(
            path_start_profiles,
            {"direct", "analyzed"},
            "route_decision_contract.path_start_profiles",
        ):
            assert isinstance(path_start_profiles, dict)
            expected_path_profiles = {
                "direct": ["task-agent", "review-agent"],
                "analyzed": ["analysis-agent"],
            }
            for path, expected in expected_path_profiles.items():
                actual = string_list(
                    path_start_profiles[path],
                    f"route_decision_contract.path_start_profiles.{path}",
                )
                if actual != expected:
                    errors.append(
                        "route_decision_contract.path_start_profiles."
                        f"{path} must remain exactly {expected}"
                    )
        if route_decision["maximum_layer3_skills"] != 3:
            errors.append(
                "route_decision_contract.maximum_layer3_skills must remain 3"
            )
        if route_decision["main_execution_producer"] != "main-control-agent":
            errors.append(
                "route_decision_contract.main_execution_producer must remain "
                "main-control-agent"
            )
        if route_decision["execution_provenance_by_path"] != {
            "analyzed": {
                "input": "main-analysis-assignment",
                "execution_level": None,
                "level_basis": None,
                "main_execution_provenance": None,
            },
            "direct": {
                "input": "main-execution",
                "execution_level": "required",
                "level_basis": "required",
                "main_execution_provenance": "required",
            },
        }:
            errors.append(
                "route execution provenance must distinguish non-executable "
                "Analysis from executable Direct work"
            )

    selector_contract = data["layer3_selector_contract"]
    expected_selector_contract = {
        "schema_version": 2,
        "source": "src/registry/foundation-skills.yaml#/selector_authority",
        "selection_owners": {
            "direct-task": "main-control-agent",
            "direct-review": "main-control-agent",
            "initial-analysis": "main-control-agent",
            "analyzed-task": "engineering-brief",
            "analyzed-review": "engineering-brief",
        },
        "selector_load": "only-when-current-owner-must-select",
        "professional_projection": "current-professional-only",
        "delivery_projection": "control-local-professional-json",
        "delivery_path_template": (
            "engineering-control-plane/references/selectors/"
            "<professional-skill>.json"
        ),
        "exact_layer3": "skip-selection-signals-after-authorization",
        "authorization": "itemwise-professional-profile-domain",
        "minimum": 0,
        "maximum": 3,
        "duplicates": "fail-closed",
        "over_maximum": "fail-closed",
        "worker_reroute": "forbidden-return-main",
        "level_invariant_fields": [
            "primary-professional",
            "foundation",
            "domain",
            "layer3-eligibility",
            "required-review-skill",
        ],
        "review_selection": "independent-review-risk",
        "review_projection": "fixed-review-skill-and-review-risk",
        "review_implementation_relation": "never-copy-or-union",
    }
    if selector_contract != expected_selector_contract:
        errors.append(
            "layer3_selector_contract must preserve JIT ownership, fail-closed "
            "cardinality, Level invariance, and independent Review selection"
        )

    completion = data["completion_state"]
    completion_fields = {
        "schema_version",
        "statuses",
        "allowed_transitions",
        "terminal_statuses",
        "new_work_after_completion",
        "fail_closed_rules",
        "completed_rules",
        "agent_projection",
    }
    statuses: list[str] = []
    if exact_keys(completion, completion_fields, "completion_state"):
        assert isinstance(completion, dict)
        if completion["schema_version"] != 1:
            errors.append("completion_state.schema_version must be 1")
        statuses = string_list(completion["statuses"], "completion_state.statuses")
        if statuses != ["in_progress", "blocked", "partial", "completed"]:
            errors.append(
                "completion_state.statuses must be exactly in_progress, blocked, partial, completed"
            )
        transitions = completion["allowed_transitions"]
        if not isinstance(transitions, dict) or set(transitions) != set(statuses):
            errors.append("completion_state.allowed_transitions keys must match statuses")
            transitions = {}
        for source, targets in transitions.items():
            target_items = string_list(
                targets,
                f"completion_state.allowed_transitions.{source}",
                nonempty=source != "completed",
            )
            if not set(target_items) <= set(statuses):
                errors.append(f"completion transition from {source!r} has unknown target")
            if source in target_items:
                errors.append(f"completion transition from {source!r} must not self-transition")
        terminals = string_list(
            completion["terminal_statuses"], "completion_state.terminal_statuses"
        )
        if terminals != ["completed"]:
            errors.append("completion_state.terminal_statuses must be exactly ['completed']")
        for terminal in terminals:
            if transitions.get(terminal) != []:
                errors.append(f"terminal completion status {terminal!r} must have no transitions")
        for source in set(statuses) - set(terminals):
            reachable: set[str] = set()
            pending = [source]
            while pending:
                current = pending.pop()
                for target in transitions.get(current, []):
                    if target not in reachable:
                        reachable.add(target)
                        pending.append(target)
            if "completed" not in reachable:
                errors.append(
                    f"completion status {source!r} must have a path to completed"
                )
        new_work = completion["new_work_after_completion"]
        if exact_keys(
            new_work,
            {"requires_new_task_id", "initial_status", "rule"},
            "completion_state.new_work_after_completion",
        ):
            assert isinstance(new_work, dict)
            if new_work["requires_new_task_id"] is not True:
                errors.append("new work after completion must require a new Task ID")
            if new_work["initial_status"] != "in_progress":
                errors.append("new work after completion must start in_progress")
            if not isinstance(new_work["rule"], str) or "new Task ID" not in new_work["rule"]:
                errors.append("new work after completion must state the new Task ID rule")
        fail_closed = completion["fail_closed_rules"]
        required_failures = {
            "validation-failed",
            "validation-unavailable",
            "high-risk-review-missing",
            "blocking-finding-unresolved",
            "changed-scope-unreviewed",
            "evidence-stale-after-edit",
        }
        if not isinstance(fail_closed, dict) or set(fail_closed) != required_failures:
            errors.append("completion_state.fail_closed_rules are incomplete")
        else:
            for rule, allowed_statuses in fail_closed.items():
                allowed_items = string_list(
                    allowed_statuses, f"completion_state.fail_closed_rules.{rule}"
                )
                if not set(allowed_items) <= set(statuses) or "completed" in allowed_items:
                    errors.append(f"{rule}: fail-closed states must be known and non-completed")
        completed_rules = projection_rule_map(
            completion["completed_rules"], "completion_state.completed_rules"
        )
        if len(completed_rules) < 3:
            errors.append("completion_state.completed_rules must cover evidence and result closure")
        expected_completed_rules = {
            "requested-result-satisfied": [
                "requested result",
                "fully satisfied",
                "declared scope",
            ],
            "required-evidence-current": [
                "each required evidence",
                "current",
                "explicitly not applicable",
            ],
            "answer-diagnosis-proof-limits": [
                "diagnosis-only",
                "answer-only",
                "proof limits",
                "fully delivered",
            ],
        }
        if completed_rules != expected_completed_rules:
            errors.append(
                "completion_state.completed_rules must retain exact canonical terms"
            )
        agent_projection = completion["agent_projection"]
        if exact_keys(
            agent_projection,
            {"prompt_section", "rules"},
            "completion_state.agent_projection",
        ):
            assert isinstance(agent_projection, dict)
            if not isinstance(agent_projection["prompt_section"], str) or not agent_projection[
                "prompt_section"
            ].strip():
                errors.append("completion_state.agent_projection.prompt_section must be text")
            completion_projection_rules = projection_rule_map(
                agent_projection["rules"],
                "completion_state.agent_projection.rules",
            )
            if set(completion_projection_rules) != {
                "same-task-transitions",
                "fail-closed-outcomes",
                "completed-terminal",
                "new-work-new-task",
            }:
                errors.append(
                    "completion_state.agent_projection must define transitions, "
                    "fail-closed outcomes, terminality, and new work"
                )
            raw_projection_rules = {
                rule.get("id"): rule
                for rule in agent_projection["rules"]
                if isinstance(rule, dict) and isinstance(rule.get("id"), str)
            }
            transition_projection = raw_projection_rules.get(
                "same-task-transitions", {}
            )
            derived_transition_terms = completion_transition_projection_terms(
                completion
            )
            if transition_projection.get("projection_terms") != derived_transition_terms:
                errors.append(
                    "same-task-transitions prompt projection must derive exactly "
                    "from completion_state.allowed_transitions"
                )
            fail_closed_projection = raw_projection_rules.get(
                "fail-closed-outcomes", {}
            )
            derived_fail_closed_terms = completion_fail_closed_projection_terms(
                completion
            )
            if (
                fail_closed_projection.get("projection_terms")
                != derived_fail_closed_terms
            ):
                errors.append(
                    "fail-closed-outcomes prompt projection must derive exactly "
                    "from completion_state.fail_closed_rules"
                )

    execution = data["execution_level_contract"]
    execution_fields = {
        "schema_version",
        "levels",
        "requested_values",
        "dynamic_levels",
        "default_level",
        "lifecycle",
        "decision_axes",
        "routing_invariance",
        "material_assessment_fields",
        "material_candidate_statuses",
        "critical_unknown_fields",
        "calibration_principles",
        "candidate_signals_not_sufficient_for_l4",
        "same_trust_principal",
        "action_authority",
        "trigger_registry",
        "l1_eligibility",
        "l2_eligibility",
        "l5_assurance_eligibility",
        "l5_confirmation",
        "main_evidence_kinds",
        "critical_unknown",
        "integrity_fallback",
        "formula",
        "level_basis_fields",
        "scope_lineage",
        "retry_policy",
        "non_bypassable",
        "legacy_migration",
        "projection",
    }
    if exact_keys(execution, execution_fields, "execution_level_contract"):
        assert isinstance(execution, dict)
        if execution["schema_version"] != 2:
            errors.append("execution_level_contract.schema_version must be 2")
        levels = execution["levels"]
        level_ids: list[str] = []
        level_ranks: dict[str, int] = {}
        if not isinstance(levels, list) or not levels:
            errors.append("execution_level_contract.levels must be a non-empty list")
            levels = []
        for index, level in enumerate(levels):
            context = f"execution_level_contract.levels[{index}]"
            if not exact_keys(level, {"id", "rank", "obligations"}, context):
                continue
            assert isinstance(level, dict)
            level_id = level["id"] if isinstance(level["id"], str) else ""
            level_ids.append(level_id)
            if not level_id.strip():
                errors.append(f"{context}.id must be non-empty text")
            elif level_id in level_ranks:
                errors.append("execution level ids must be unique")
            else:
                level_ranks[level_id] = level["rank"]
            if level["rank"] != index + 1:
                errors.append(f"{context}.rank must be {index + 1}")
            string_list(level["obligations"], f"{context}.obligations")
        if level_ids != ["L1", "L2", "L3", "L4", "L5"]:
            errors.append("execution levels must remain exactly L1 through L5")
        l5 = next(
            (level for level in levels if isinstance(level, dict) and level.get("id") == "L5"),
            None,
        )
        l5_obligations = l5.get("obligations") if isinstance(l5, dict) else None
        if not isinstance(l5_obligations, list) or not {
            "explicit request or confirmed automatic assurance recommendation",
            "independent implementation review",
        } <= set(item for item in l5_obligations if isinstance(item, str)):
            errors.append(
                "execution L5 must require an explicit request or confirmed automatic recommendation and independent implementation review"
            )
        requested = string_list(
            execution["requested_values"],
            "execution_level_contract.requested_values",
        )
        if requested != ["unspecified", "L1", "L2", "L3", "L4", "L5"]:
            errors.append("execution requested values must remain unspecified plus L1 through L5")
        dynamic = string_list(
            execution["dynamic_levels"],
            "execution_level_contract.dynamic_levels",
        )
        if dynamic != ["L1", "L2", "L3", "L4", "L5"]:
            errors.append("execution automatic levels must remain exactly L1 through L5")
        if execution["default_level"] != "L3":
            errors.append("execution default level must remain L3")
        expected_lifecycle = {
            "analysis_assignment_has_execution_level": False,
            "analysis_default_level": False,
            "analysis_writes_historical_effective_level": False,
            "analysis_participates_in_historical_max": False,
            "first_computation_point": "first-executable-slice-or-direct-executable-task",
            "automatic_default_l3_applies_to": "executable-task-only",
            "analyzed_work_sequence": [
                "analysis-agent",
                "engineering-brief",
                "first-executable-slice",
                "compute-execution-level",
                "task-agent",
            ],
            "post_analysis_evidence_kind": "analysis_handoff",
            "post_material_work_history_rule": "retain-confirmed-executable-task-maxima",
        }
        if execution["lifecycle"] != expected_lifecycle:
            errors.append(
                "execution lifecycle must compute Level only for the First "
                "Executable Slice or a Direct executable Task"
            )

        expected_axes = {
            "professional_risk_signal": {
                "decision": "skill-or-risk-lens-selection",
                "execution_level_effect": "none",
                "rule": "route expertise from concrete task evidence without inferring material residual impact",
            },
            "residual_reachable_material_risk": {
                "decision": "execution-level",
                "execution_level_effect": "L4 only for a reachable material residual impact or explicit policy floor",
                "rule": "evaluate the impact path after existing enforced controls",
            },
            "concrete_action_authority": {
                "decision": "action-decision",
                "execution_level_effect": "none unless the action exposes a new material Task risk",
                "rule": "classify each action from host capability, Task Scope, and user authority without granting permission",
            },
        }
        if execution["decision_axes"] != expected_axes:
            errors.append("execution decision axes must remain exact and independent")
        expected_routing_invariance = {
            "requested_levels": ["unspecified", "L1", "L2", "L3", "L4", "L5"],
            "fixed_fields": [
                "primary_professional_skill",
                "implementation_layer3",
                "domain",
                "required_review_skills",
            ],
            "allowed_variations": [
                "effective_level",
                "validation_depth",
                "review_depth_or_frequency",
                "evidence_strength",
                "independence",
                "level_dependent_targeted_reference",
            ],
            "confirmation_scope": "execution-level-projection-only",
            "forbidden_confirmation_effects": [
                "analysis-invalidation",
                "brief-semantic-mutation",
                "expertise-reroute",
                "selector-reload",
                "layer3-reselection",
            ],
        }
        if execution["routing_invariance"] != expected_routing_invariance:
            errors.append(
                "execution Level routing invariance must preserve expertise fields across requested Levels and confirmation"
            )
        expected_material_fields = [
            "affected_asset_or_invariant",
            "actor_or_controlling_input",
            "authority_or_behavior_delta",
            "reachable_impact_path",
            "blast_radius",
            "reversibility_or_recovery",
            "existing_enforced_controls",
            "residual_impact",
        ]
        if execution["material_assessment_fields"] != expected_material_fields:
            errors.append("execution material assessment fields must remain exact and ordered")
        if execution["material_candidate_statuses"] != [
            "matched",
            "non_material",
            "unknown",
            "not_matched",
        ]:
            errors.append(
                "execution material candidate statuses must remain exact and ordered"
            )
        expected_critical_fields = [
            "candidate_l4_predicate",
            "missing_fact",
            "plausible_impact_path",
            "material_consequence",
        ]
        if execution["critical_unknown_fields"] != expected_critical_fields:
            errors.append("execution critical unknown fields must remain exact and ordered")
        if execution["calibration_principles"] != [
            "Possibility != Reachability.",
            "Mutability != Trust Boundary.",
            "Capability != Authorization.",
            "Risk Category != Material Risk.",
        ]:
            errors.append("execution calibration principles must remain exact")
        candidate_signals = string_list(
            execution["candidate_signals_not_sufficient_for_l4"],
            "execution_level_contract.candidate_signals_not_sufficient_for_l4",
        )
        if len(candidate_signals) != 10 or len(candidate_signals) != len(set(candidate_signals)):
            errors.append("execution candidate signals must remain ten unique non-L4 proofs")
        same_principal = execution["same_trust_principal"]
        if not exact_keys(
            same_principal,
            {"rule", "escalation_requirement", "user_request_effect"},
            "execution_level_contract.same_trust_principal",
        ):
            pass
        elif any(
            not isinstance(same_principal[field], str) or not same_principal[field].strip()
            for field in ("rule", "escalation_requirement", "user_request_effect")
        ):
            errors.append("execution same-trust-principal rules must be non-empty")
        action_authority = execution["action_authority"]
        action_fields = {
            "fact_fields",
            "authority_states",
            "outcomes",
            "material_risk_delta_outcome",
            "runtime_state",
            "host_grant",
        }
        if exact_keys(
            action_authority,
            action_fields,
            "execution_level_contract.action_authority",
        ):
            assert isinstance(action_authority, dict)
            if action_authority["fact_fields"] != [
                "exact_target",
                "mutation_surface",
                "reversibility",
                "recovery",
                "external_effects",
                "capability_facts",
                "authorization_facts",
                "unresolved_ambiguity",
            ]:
                errors.append("execution action-authority fact fields must remain exact")
            expected_states = [
                "within-current-authority",
                "bounded-extra-authority-required",
                "user-owned-decision-required",
                "unsafe-or-unsupported",
            ]
            if action_authority["authority_states"] != expected_states:
                errors.append("execution action-authority states must remain exact")
            if set(action_authority["outcomes"]) != set(expected_states):
                errors.append("execution action-authority outcomes must cover every state")
            if action_authority["runtime_state"] is not False:
                errors.append("execution action authority must not add runtime state")
            if action_authority["host_grant"] is not False:
                errors.append("execution action authority must not grant host permission")

        triggers = execution["trigger_registry"]
        seen_triggers: set[str] = set()
        if not isinstance(triggers, list) or not triggers:
            errors.append("execution_level_contract.trigger_registry must be non-empty")
            triggers = []
        for index, trigger in enumerate(triggers):
            context = f"execution_level_contract.trigger_registry[{index}]"
            if not exact_keys(
                trigger,
                {"id", "floor", "positive_predicate", "anti_trigger", "source_anchor"},
                context,
            ):
                continue
            assert isinstance(trigger, dict)
            identifier = trigger["id"]
            if not isinstance(identifier, str) or CORE_ID_RE.fullmatch(identifier) is None:
                errors.append(f"{context}.id must be a canonical identifier")
                continue
            if identifier in seen_triggers:
                errors.append("execution trigger ids must be unique")
            seen_triggers.add(identifier)
            if trigger["floor"] not in level_ids:
                errors.append(f"{context}.floor must reference a declared level")
            for field in ("positive_predicate", "anti_trigger", "source_anchor"):
                if not isinstance(trigger[field], str) or not trigger[field].strip():
                    errors.append(f"{context}.{field} must be non-empty text")
            if trigger["positive_predicate"] == trigger["anti_trigger"]:
                errors.append(f"{context} positive predicate and anti-trigger must differ")

        def validate_eligibility_registry(
            field: str, expected_ids: list[str]
        ) -> list[str]:
            rows = execution[field]
            identifiers: list[str] = []
            if not isinstance(rows, list) or not rows:
                errors.append(f"execution_level_contract.{field} must be non-empty")
                return identifiers
            for index, row in enumerate(rows):
                context = f"execution_level_contract.{field}[{index}]"
                if not exact_keys(
                    row,
                    {"id", "positive_predicate", "anti_trigger", "source_anchor"},
                    context,
                ):
                    continue
                assert isinstance(row, dict)
                identifier = row["id"]
                identifiers.append(identifier if isinstance(identifier, str) else "")
                if not isinstance(identifier, str) or CORE_ID_RE.fullmatch(identifier) is None:
                    errors.append(f"{context}.id must be a canonical identifier")
                for predicate_field in (
                    "positive_predicate",
                    "anti_trigger",
                    "source_anchor",
                ):
                    if (
                        not isinstance(row[predicate_field], str)
                        or not row[predicate_field].strip()
                    ):
                        errors.append(
                            f"{context}.{predicate_field} must be non-empty text"
                        )
                if row["positive_predicate"] == row["anti_trigger"]:
                    errors.append(
                        f"{context} positive predicate and anti-trigger must differ"
                    )
            if identifiers != expected_ids:
                errors.append(
                    f"execution {field} ids must remain exact and ordered"
                )
            if len(identifiers) != len(set(identifiers)):
                errors.append(f"execution {field} ids must be unique")
            return identifiers

        validate_eligibility_registry(
            "l1_eligibility",
            [
                "no-runtime-or-product-behavior-change",
                "no-public-or-shared-contract-change",
                "no-state-data-or-invariant-change",
                "no-external-or-integration-effect",
                "deterministic-bounded-verification",
                "trivial-bounded-revert",
            ],
        )
        l2_rows = execution["l2_eligibility"]
        l2_ids: list[str] = []
        if not isinstance(l2_rows, list) or not l2_rows:
            errors.append("execution_level_contract.l2_eligibility must be non-empty")
            l2_rows = []
        for index, row in enumerate(l2_rows):
            context = f"execution_level_contract.l2_eligibility[{index}]"
            if not exact_keys(
                row,
                {"id", "positive_predicate", "anti_trigger", "source_anchor"},
                context,
            ):
                continue
            assert isinstance(row, dict)
            identifier = row["id"]
            l2_ids.append(identifier if isinstance(identifier, str) else "")
            if not isinstance(identifier, str) or CORE_ID_RE.fullmatch(identifier) is None:
                errors.append(f"{context}.id must be a canonical identifier")
            for field in ("positive_predicate", "anti_trigger", "source_anchor"):
                if not isinstance(row[field], str) or not row[field].strip():
                    errors.append(f"{context}.{field} must be non-empty text")
            if row["positive_predicate"] == row["anti_trigger"]:
                errors.append(f"{context} positive predicate and anti-trigger must differ")
        if len(l2_ids) != len(set(l2_ids)):
            errors.append("execution L2 eligibility ids must be unique")
        validate_eligibility_registry(
            "l5_assurance_eligibility",
            [
                "confirmed-material-l4",
                "critical-consequence",
                "broad-blast-radius",
                "irreversible",
                "weak-recovery",
                "extra-assurance-materially-reduces-uncertainty",
            ],
        )
        confirmation = execution["l5_confirmation"]
        expected_confirmation = {
            "required_source": "analysis_handoff",
            "states": [
                "not-required",
                "pending",
                "confirmed",
                "rejected",
                "explicit",
            ],
            "automatic_pending_action": "ask-once",
            "confirmed_level": "L5",
            "rejected_level": "L4",
            "explicit_l5_state": "explicit",
            "confirmation_effect": "execution-level-projection-only",
            "forbidden_effects": [
                "analysis-invalidation",
                "brief-semantic-mutation",
                "expertise-reroute",
                "selector-reload",
                "layer3-reselection",
            ],
        }
        if confirmation != expected_confirmation:
            errors.append(
                "execution L5 confirmation must remain exact, ask once, and change only the execution projection"
            )
        evidence_kinds = string_list(
            execution["main_evidence_kinds"],
            "execution_level_contract.main_evidence_kinds",
        )
        if evidence_kinds != ["user_fact", "analysis_handoff"]:
            errors.append("main execution evidence kinds must be user_fact and analysis_handoff")

        critical = execution["critical_unknown"]
        if exact_keys(
            critical,
            {"floor", "edit_status", "provisional", "required_fields", "rule"},
            "execution_level_contract.critical_unknown",
        ):
            assert isinstance(critical, dict)
            if critical["floor"] not in level_ids:
                errors.append("critical unknown floor must reference a declared level")
            if not isinstance(critical["edit_status"], str) or not critical["edit_status"].strip():
                errors.append("critical unknown edit status must be non-empty text")
            if not isinstance(critical["rule"], str) or not critical["rule"].strip():
                errors.append("execution critical unknown rule must be non-empty")
            if critical["provisional"] is not True:
                errors.append("execution critical unknown L4 must be provisional")
            if critical["required_fields"] != execution["critical_unknown_fields"]:
                errors.append("execution critical unknown required fields must use Core authority")

        fallback = execution["integrity_fallback"]
        fallback_fields = {
            "inputs",
            "floor",
            "retain_explicit_known_l5",
            "retain_prior_historical_maxima",
            "provisional_floor",
            "historical_effect",
            "edit_status",
            "partial_computation",
            "allowed_outcomes",
            "forbidden_actions",
        }
        if exact_keys(
            fallback,
            fallback_fields,
            "execution_level_contract.integrity_fallback",
        ):
            assert isinstance(fallback, dict)
            if fallback["inputs"] != ["missing", "malformed", "duplicate"]:
                errors.append(
                    "execution integrity fallback inputs must remain missing, malformed, and duplicate"
                )
            if fallback["floor"] != "L4":
                errors.append("execution integrity fallback floor must remain L4")
            if fallback["retain_explicit_known_l5"] is not True:
                errors.append("execution integrity fallback must retain explicit known L5")
            if fallback["retain_prior_historical_maxima"] is not True:
                errors.append("execution integrity fallback must retain prior historical maxima")
            if fallback["provisional_floor"] is not True:
                errors.append("execution integrity fallback L4 must be provisional")
            if fallback["historical_effect"] != (
                "retain confirmed prior maxima without recording the fallback L4"
            ):
                errors.append("execution integrity fallback historical effect must remain exact")
            if fallback["edit_status"] != "blocked":
                errors.append("execution integrity fallback must block editing")
            if fallback["partial_computation"] is not False:
                errors.append("execution integrity fallback must forbid partial computation")
            if fallback["allowed_outcomes"] != [
                "report-integrity-blocker",
                "dispatch-read-only-diagnosis",
            ]:
                errors.append("execution integrity fallback allowed outcomes must remain fail-closed")
            if fallback["forbidden_actions"] != [
                "implementation",
                "validation",
                "release",
                "router",
            ]:
                errors.append("execution integrity fallback forbidden actions must remain exact")

        formula = execution["formula"]
        formula_fields = {
            "computed_floor_seed",
            "trigger_aggregation",
            "source_aggregation",
            "automatic_high_risk_floor",
            "automatic_high_risk_level",
            "automatic_l2_ceiling",
            "automatic_l2_level",
            "automatic_default_level",
            "l1_requirement",
            "l2_requirement",
            "l5_requirement",
            "requested_base",
            "minimum_eligible_sources",
            "mandatory_floor_sources",
            "effective_level_sources",
            "next_historical_floor_sources",
            "next_historical_effective_sources",
        }
        if exact_keys(formula, formula_fields, "execution_level_contract.formula"):
            assert isinstance(formula, dict)
            for field in (
                "computed_floor_seed",
                "automatic_high_risk_floor",
                "automatic_high_risk_level",
                "automatic_l2_ceiling",
                "automatic_l2_level",
                "automatic_default_level",
            ):
                if formula[field] not in level_ids:
                    errors.append(f"execution formula {field} must reference a declared level")
            if formula["trigger_aggregation"] != "max":
                errors.append("execution trigger aggregation operator must be max")
            if formula["source_aggregation"] != "max":
                errors.append("execution source aggregation operator must be max")
            if formula["l2_requirement"] != "all_true":
                errors.append("execution L2 requirement operator must be all_true")
            if formula["l1_requirement"] != "all_true_and_l2_true":
                errors.append(
                    "execution L1 requirement must remain an all-true strict L2 subset"
                )
            if formula["l5_requirement"] != {
                "required_all": [
                    "confirmed-material-l4",
                    "critical-consequence",
                    "extra-assurance-materially-reduces-uncertainty",
                ],
                "required_any": [
                    "broad-blast-radius",
                    "irreversible",
                    "weak-recovery",
                ],
                "source": "analysis_handoff",
            }:
                errors.append(
                    "execution L5 requirement must bind confirmed material evidence, critical consequence, recovery severity, assurance value, and analysis handoff source"
                )
            requested_base = formula["requested_base"]
            if requested_base != {
                "unspecified": "automatic",
                "L1": "L1",
                "L2": "L2",
                "L3": "L3",
                "L4": "L4",
                "L5": "L5",
            }:
                errors.append(
                    "execution requested-base mapping must preserve automatic plus explicit L1 through L5"
                )
            if formula["automatic_default_level"] != "L3":
                errors.append("execution automatic default level must remain L3")
            source_sequences = {
                "minimum_eligible_sources": [
                    "l1_eligibility",
                    "l2_eligibility",
                    "computed_floor",
                ],
                "mandatory_floor_sources": [
                    "computed_floor",
                    "prior_historical_max_floor",
                ],
                "effective_level_sources": [
                    "requested_or_automatic",
                    "minimum_eligible_level",
                    "mandatory_floor",
                    "prior_historical_max_effective",
                ],
                "next_historical_floor_sources": [
                    "prior_historical_max_floor",
                    "confirmed_mandatory_floor",
                ],
                "next_historical_effective_sources": [
                    "prior_historical_max_effective",
                    "confirmed_effective_level",
                ],
            }
            for field, expected_sources in source_sequences.items():
                values = string_list(formula[field], f"execution_level_contract.formula.{field}")
                if values != expected_sources:
                    errors.append(
                        f"execution formula {field} must retain exact ordered sources"
                    )
        level_basis_fields = string_list(
            execution["level_basis_fields"],
            "execution_level_contract.level_basis_fields",
        )
        if level_basis_fields != [
            "trigger_evaluations",
            "l1_eligibility",
            "l2_eligibility",
            "l5_assurance_eligibility",
            "l5_confirmation",
            "obligations",
            "unresolved",
            "edit_status",
        ]:
            errors.append("execution Level Basis schema fields must be exact and ordered")

        scope_lineage = execution["scope_lineage"]
        scope_fields = {
            "lock_key_fields",
            "history_independent_of_material_tree",
            "same_task_new_lineage",
            "scope_expansion",
            "lowering_requirements",
            "requested_lowering_after_edit",
            "provisional_floor_history",
            "confirmed_material_l4_history",
            "same_task_resolved_provisional",
        }
        if exact_keys(scope_lineage, scope_fields, "execution_level_contract.scope_lineage"):
            assert isinstance(scope_lineage, dict)
            if scope_lineage["lock_key_fields"] != ["Task ID", "Scope Lineage"]:
                errors.append("execution scope lock key must be Task ID plus Scope Lineage")
            if scope_lineage["history_independent_of_material_tree"] is not True:
                errors.append("execution history must remain independent of material tree")
            if scope_lineage["same_task_new_lineage"] != "invalid":
                errors.append("same Task ID cannot open a new execution scope lineage")
            if scope_lineage["scope_expansion"] != "inherit historical maxima":
                errors.append("scope expansion must inherit historical maxima")
            if scope_lineage["lowering_requirements"] != [
                "new Task ID",
                "child Scope Lineage",
                "strict canonical scope narrowing proof",
            ]:
                errors.append("execution lowering requirements are incomplete")
            if scope_lineage["requested_lowering_after_edit"] != "record only; effective level cannot decrease":
                errors.append("requested lowering after edit must not lower effective level")
            if scope_lineage["provisional_floor_history"] != "excluded":
                errors.append("provisional execution floors must be excluded from history")
            if scope_lineage["confirmed_material_l4_history"] != "retained":
                errors.append("confirmed material L4 history must remain retained")
            if scope_lineage["same_task_resolved_provisional"] != (
                "recompute with confirmed history before material edit"
            ):
                errors.append("resolved provisional risk must recompute on the same Task")

        retry_policy = execution["retry_policy"]
        retry_fields = {
            "same_path_failure_limit",
            "retry_change_dimensions",
            "unchanged_retry_after_limit",
            "third_unchanged_retry",
        }
        if exact_keys(
            retry_policy,
            retry_fields,
            "execution_level_contract.retry_policy",
        ):
            assert isinstance(retry_policy, dict)
            if retry_policy["same_path_failure_limit"] != 2:
                errors.append("execution retry same-path failure limit must remain 2")
            if retry_policy["retry_change_dimensions"] != [
                "hypothesis",
                "material",
                "gap",
                "transition",
            ]:
                errors.append(
                    "execution retry change dimensions must remain hypothesis, "
                    "material, gap, and transition"
                )
            if (
                retry_policy["unchanged_retry_after_limit"]
                != "return-to-main-or-block"
            ):
                errors.append(
                    "execution unchanged retry after the limit must return to Main "
                    "or block"
                )
            if retry_policy["third_unchanged_retry"] != "forbidden":
                errors.append("execution third unchanged retry must remain forbidden")

        non_bypassable = string_list(
            execution["non_bypassable"],
            "execution_level_contract.non_bypassable",
        )
        if not non_bypassable or len(non_bypassable) != len(set(non_bypassable)):
            errors.append("execution non-bypassable controls must be non-empty and unique")
        if "independent implementation review" not in non_bypassable:
            errors.append(
                "execution non-bypassable controls must require independent implementation review"
            )
        if execution["legacy_migration"] != {
            "completed_without_level": "readable only for completed/read; reissue before completed edit, validation, or review",
            "active_or_resumed_without_level": "reissue before active or resumed work, edit, validation, or review",
        }:
            errors.append("legacy execution-level migration contract must remain additive v2")
        projection = execution["projection"]
        expected_projection = {
            "prompt": {"id": "execution-level-contract", "section": "Execution Level and Validation"},
            "router": {
                "path": "src/control-skills/engineering-control-plane/references/professional-skill-router.md",
                "id": "execution-level-router-projection",
                "input_field": "effective_level",
            },
            "runtime_reference": {
                "path": "src/control-skills/engineering-control-plane/references/execution-level-contract.md",
                "id": "execution-level-runtime-reference",
                "excluded_fields": ["projection"],
            },
        }
        if not isinstance(projection, dict) or set(projection) != {
            *expected_projection,
            "public_task_extension",
        }:
            errors.append("execution level projections must bind Prompt and router canonically")
        else:
            for projection_id, expected in expected_projection.items():
                if projection[projection_id] != expected:
                    errors.append(
                        "execution level projections must bind Prompt and router canonically"
                    )
            errors.extend(
                _execution_public_task_extension_errors(
                    projection["public_task_extension"], execution
                )
            )

    task = data["task_contract"]
    task_fields = {
        "schema_version",
        "assignment_initial_status",
        "fields",
        "required_for_direct_task",
        "optional_for_direct_task",
        "required_for_dag_task",
        "parallel_group_fields",
        "execution_level_extension",
        "scheduling_rules",
        "evidence_resolution",
        "direct_bounded_discovery",
        "analyzed_work_authority",
        "task_boundary",
        "finding_relations",
        "repair_routing",
        "same_pattern_scan",
        "template_schemas",
        "utility_projection_rules",
    }
    if exact_keys(task, task_fields, "task_contract"):
        assert isinstance(task, dict)
        if task["schema_version"] != 2:
            errors.append("task_contract.schema_version must be 2")
        if task["assignment_initial_status"] != "in_progress":
            errors.append(
                "task_contract.assignment_initial_status must be exactly in_progress"
            )
        fields = string_list(task["fields"], "task_contract.fields")
        if fields[:2] != ["Task ID", "Status"]:
            errors.append("task_contract.fields must place Status immediately after Task ID")
        required_task_fields: dict[str, list[str]] = {}
        for list_name in ("required_for_direct_task", "required_for_dag_task"):
            values = string_list(task[list_name], f"task_contract.{list_name}")
            required_task_fields[list_name] = values
            if not set(values) <= set(fields):
                errors.append(f"task_contract.{list_name} contains an unknown field")
            if values != [field for field in fields if field in values]:
                errors.append(f"task_contract.{list_name} must preserve canonical field order")
            if values[:2] != ["Task ID", "Status"]:
                errors.append(f"task_contract.{list_name} must start with Task ID and Status")
        if "Dependencies" in required_task_fields["required_for_direct_task"]:
            errors.append("Direct Task dependencies must remain optional")
        optional_direct_fields = string_list(
            task["optional_for_direct_task"],
            "task_contract.optional_for_direct_task",
        )
        if optional_direct_fields != ["Dependencies"]:
            errors.append(
                "task_contract.optional_for_direct_task must be exactly ['Dependencies']"
            )
        if set(optional_direct_fields) & set(required_task_fields["required_for_direct_task"]):
            errors.append("optional Direct Task fields must not also be required")
        if "Dependencies" not in required_task_fields["required_for_dag_task"]:
            errors.append("DAG task Dependencies are required")
        parallel_fields = string_list(
            task["parallel_group_fields"], "task_contract.parallel_group_fields"
        )
        for owner_field in (
            "Integration Owner",
            "Merge Owner",
            "Conflict Resolution Owner",
        ):
            if owner_field not in parallel_fields:
                errors.append(f"parallel_group_fields must include {owner_field!r}")
        canonical_extension_fields = [
            "Requested Level",
            "Automatic Level",
            "Minimum Eligible Level",
            "Default Level",
            "Effective Level",
            "Edit Status",
            "Level Basis",
            "L5 Evidence Requirements",
        ]
        canonical_public_extension_fields = ["Level", "Basis", "L5 Evidence"]
        extension = task["execution_level_extension"]
        extension_fields = {
            "heading",
            "fields",
            "surface_insertions",
        }
        if exact_keys(
            extension,
            extension_fields,
            "task_contract.execution_level_extension",
        ):
            assert isinstance(extension, dict)
            if extension["heading"] != "Execution Level":
                errors.append("execution level extension heading must be Execution Level")
            if extension["fields"] != canonical_extension_fields:
                errors.append("execution level extension fields must be exact and ordered")
            expected_insertions = {
                "direct-task-template.md": {"kind": "heading", "after": "Status"},
                "engineering-brief-template.md": {
                    "kind": "labeled-section",
                    "section": "First Executable Slice",
                    "after": "Status",
                },
                "task-dag-template.md": {
                    "kind": "labeled-section",
                    "sections": ["Task A", "Task B"],
                    "after": "Status",
                },
                "implementation-handoff-template.md": {"kind": "heading", "after": "Task ID"},
                "review-handoff-template.md": {"kind": "heading", "after": "Task ID"},
            }
            if extension["surface_insertions"] != expected_insertions:
                errors.append("execution level surface insertions must bind every canonical surface")
        scheduling = task["scheduling_rules"]
        if exact_keys(
            scheduling,
            {"shared_or_unknown_writes", "parallel_write_requirements"},
            "task_contract.scheduling_rules",
        ):
            assert isinstance(scheduling, dict)
            if scheduling["shared_or_unknown_writes"] != "serialize":
                errors.append("shared or unknown workspace writes must serialize")
            requirements = string_list(
                scheduling["parallel_write_requirements"],
                "task_contract.scheduling_rules.parallel_write_requirements",
            )
            if set(requirements) != {
                "isolated workspace",
                "no dependency",
                "no shared write surface",
            }:
                errors.append("parallel write requirements are incomplete")

        evidence = task["evidence_resolution"]
        evidence_fields = {
            "semantics_owner",
            "source_path",
            "projection_only",
            "source_binding",
            "gap_classes",
            "route_affecting_surfaces",
            "decision_rules",
            "path_values",
            "maximum_user_questions",
        }
        if exact_keys(evidence, evidence_fields, "task_contract.evidence_resolution"):
            assert isinstance(evidence, dict)
            source_path_value = evidence["source_path"]
            source_path = (
                PurePosixPath(source_path_value)
                if isinstance(source_path_value, str)
                else None
            )
            if (
                source_path is None
                or source_path.is_absolute()
                or source_path.name != "SKILL.md"
                or ".." in source_path.parts
            ):
                errors.append(
                    "Task Evidence Resolution source_path must name one repository root SKILL.md"
                )
                source_record = None
            else:
                if evidence["semantics_owner"] != source_path.parent.name:
                    errors.append(
                        "Task Evidence Resolution semantics_owner must match its owning Skill path"
                    )
                try:
                    source_record = collect_skill_root_source(
                        root / source_path,
                        root=root,
                    )
                except ValueError as exc:
                    errors.append(f"Task Evidence Resolution source_path is invalid: {exc}")
                    source_record = None
            if evidence["projection_only"] is not True:
                errors.append("Task Evidence Resolution must remain projection-only")

            source_declaration: dict[str, Any] | None = None
            if source_record is not None:
                try:
                    source_declaration = evidence_resolution_source_declaration(
                        source_record=source_record,
                    )
                except ValueError as exc:
                    errors.append(
                        f"Task Evidence Resolution source declaration is invalid: {exc}"
                    )

            binding = evidence["source_binding"]
            if exact_keys(
                binding,
                {
                    "collector",
                    "normalization",
                    "source_fingerprint",
                    "anchor_fingerprint",
                },
                "task_contract.evidence_resolution.source_binding",
            ):
                assert isinstance(binding, dict)
                if binding["collector"] != SKILL_ROOT_SOURCE_COLLECTOR_ID:
                    errors.append(
                        "Task Evidence Resolution must use the root Skill content collector"
                    )
                if binding["normalization"] != SKILL_ROOT_SOURCE_NORMALIZATION:
                    errors.append(
                        "Task Evidence Resolution source normalization must remain canonical"
                    )
                if source_record is not None and binding["source_fingerprint"] != source_record[
                    "source_fingerprint"
                ]:
                    errors.append(
                        "Task Evidence Resolution source fingerprint does not match the owning Skill"
                    )

            gap_classes = evidence["gap_classes"]
            anchors: list[str] = []
            gap_rows: list[dict[str, Any]] = []
            if not isinstance(gap_classes, list) or len(gap_classes) != 3:
                errors.append(
                    "Task Evidence Resolution must project exactly three source-backed gap classes"
                )
            else:
                for index, row in enumerate(gap_classes):
                    context = f"task_contract.evidence_resolution.gap_classes[{index}]"
                    if not exact_keys(
                        row,
                        {"id", "source_semantic", "source_anchor", "subtypes"},
                        context,
                    ):
                        continue
                    assert isinstance(row, dict)
                    if any(
                        not isinstance(row[field], str) or not row[field].strip()
                        for field in ("id", "source_semantic", "source_anchor")
                    ):
                        errors.append(f"{context} source projection fields must be non-empty")
                        continue
                    subtypes = string_list(
                        row["subtypes"], f"{context}.subtypes", nonempty=False
                    )
                    anchor = normalize_skill_root_source(row["source_anchor"])
                    anchors.append(anchor)
                    gap_rows.append(row)
                    if (
                        source_record is not None
                        and anchor not in source_record["normalized_source"]
                    ):
                        errors.append(
                            f"Task Evidence Resolution source anchor {index} is absent from the owning Skill"
                        )
                    if len(subtypes) != len(set(subtypes)):
                        errors.append(f"{context}.subtypes must remain unique")
                ids = [row["id"] for row in gap_rows]
                semantics = [row["source_semantic"] for row in gap_rows]
                if len(ids) != len(set(ids)) or len(semantics) != len(set(semantics)):
                    errors.append(
                        "Task Evidence Resolution class IDs and source semantics must be unique"
                    )
                if len([row for row in gap_rows if row["subtypes"]]) != 1:
                    errors.append(
                        "Task Evidence Resolution must have one source-backed user-choice projection"
                    )
            if isinstance(binding, dict) and set(binding) == {
                "collector",
                "normalization",
                "source_fingerprint",
                "anchor_fingerprint",
            } and binding["anchor_fingerprint"] != skill_source_anchor_fingerprint(anchors):
                errors.append(
                    "Task Evidence Resolution anchor fingerprint does not match normalized source anchors"
                )

            if (
                source_declaration is not None
                and gap_classes != source_declaration["gap_classes"]
            ):
                errors.append(
                    "Task Evidence Resolution gap classes differ from the source declaration"
                )

            decision_rules = evidence["decision_rules"]
            if not isinstance(decision_rules, dict):
                errors.append("Task Evidence Resolution decision_rules must be an object")
            else:
                expected_rule_ids: set[str] = set()
                for row in gap_rows:
                    expected_rule_ids.update(row["subtypes"] or [row["id"]])
                if set(decision_rules) != expected_rule_ids:
                    errors.append(
                        "Task Evidence Resolution decision rules must bind every projected class or choice subtype exactly once"
                    )
                if any(not isinstance(rule, dict) or not rule for rule in decision_rules.values()):
                    errors.append(
                        "Task Evidence Resolution decision rules must be non-empty objects"
                    )
                if (
                    source_declaration is not None
                    and decision_rules != source_declaration["decision_rules"]
                ):
                    errors.append(
                        "Task Evidence Resolution decision rules differ from the source declaration"
                    )
            route_surfaces = string_list(
                evidence["route_affecting_surfaces"],
                "task_contract.evidence_resolution.route_affecting_surfaces",
            )
            if not route_surfaces:
                errors.append("Task Evidence Resolution route-affecting surfaces must not be empty")
            paths = string_list(
                evidence["path_values"],
                "task_contract.evidence_resolution.path_values",
            )
            route_contract = data.get("route_decision_contract")
            route_paths = route_contract.get("path_values") if isinstance(route_contract, dict) else None
            if paths != route_paths:
                errors.append(
                    "Task Evidence Resolution paths must reuse route_decision_contract"
                )
            if evidence["maximum_user_questions"] != 1:
                errors.append("Task Evidence Resolution permits one user question at most")

        expected_direct_bounded_discovery = {
            "preconditions": [
                "primary-professional-stable",
                "domain-and-layer3-route-stable",
                "semantic-scope-stable",
                "no-unresolved-user-choice",
                "no-unresolved-material-risk",
                "bounded-read-boundary",
            ],
            "allowed_checks": [
                "exact-owning-symbol-or-file",
                "relevant-existing-test",
                "minimum-local-consumer",
                "local-reuse-candidate",
                "local-validation-command",
                "placement-within-known-owner-boundary",
            ],
            "prohibited": [
                "repo-wide-discovery",
                "unknown-owner-module-or-system",
                "unknown-external-consumer-graph",
                "security-money-migration-or-domain-boundary-discovery",
                "worker-rerouting",
                "worker-skill-domain-or-layer3-selection",
            ],
            "outcomes": {
                "boundary-confirmed": "confirm-and-continue",
                "route-or-risk-invalidated": (
                    "stop-before-edit-return-main-for-analysis"
                ),
                "user-choice-discovered": (
                    "stop-before-edit-return-main-for-one-question"
                ),
            },
            "worker_route_authority": False,
            "level_rules": {
                "simpler": "preserve-current",
                "higher-risk": "recompute",
            },
            "read_boundary": "already-known-owner-test-and-minimum-consumer",
        }
        if task["direct_bounded_discovery"] != expected_direct_bounded_discovery:
            errors.append(
                "Direct bounded discovery must keep exact preconditions, local "
                "checks, stops, worker no-reroute, and monotonic Level rules"
            )

        expected_analyzed_work_authority = {
            "applies_to": "analyzed-work",
            "operational_authority": "current-engineering-brief",
            "authoritative_sections": [
                "Problem and Desired Behavior",
                "Acceptance and Non-goals",
                "Ownership and Invariants",
                "Placement and Reuse",
                "Contract / Data / Failure Impact",
                "Validation Strategy",
                "Risks and Rollback",
                "First Executable Slice",
                "Task Dependencies",
                "Integration Boundary",
                "Review Boundary",
                "Evidence Gaps and Proof Limits",
            ],
            "input_kinds": [
                "user-request",
                "issue-prd-change-request",
                "source-and-tests",
                "external-evidence",
                "specialist-analysis",
            ],
            "derived_artifacts": [
                "task-dag",
                "task-contract",
                "implementation-handoff",
                "review-handoff",
            ],
            "protected_decisions": [
                "Acceptance",
                "Non-goals",
                "Owner",
                "Invariants",
                "Placement",
                "Contract semantics",
                "Rollback",
                "First Executable Slice",
            ],
            "initial_analysis": "one-complete-initial-analysis",
            "first_analysis_kind": "initial",
            "target_authority": {
                "authority": ["desired_behavior", "observable_acceptance"],
                "observed_behavior_role": "failure-evidence-only",
                "observed_behavior_as_target": "forbidden",
            },
            "initial_closure_obligations": [
                "acceptance-and-non-goals",
                "owner-placement-invariant",
                "contract-data-failure-impact",
                "acceptance-proving-validation",
                "rollback",
                "executable-task-dependencies",
                "professional-and-layer3-boundaries",
                "minimum-sufficient-review-boundaries",
                "critical-evidence-gaps",
                "minimum-safe-first-executable-slice",
            ],
            "non_invalidation_events": [
                "task-completion",
                "task-switch",
                "ordinary-implementation-discovery",
                "review-boundary-not-reached",
                "claim-local-evidence-reproof",
            ],
            "decision_invalidation_triggers": [
                "Acceptance-or-Non-goals",
                "Owner-or-Placement-or-Invariant",
                "contract-or-data-semantics",
                "dependency-or-rollback",
                "material-risk",
                "scope-blocker",
            ],
            "delta_analysis": {
                "scope": "invalidated-decisions-and-transitive-impact-only",
                "updates": [
                    "affected-brief-sections",
                    "affected-tasks",
                    "affected-dependencies",
                    "affected-skill-assignments",
                    "affected-review-boundaries",
                ],
                "full_reanalysis_condition": (
                    "foundational-goal-or-system-assumptions-invalidated"
                ),
                "skill_assignment_default": "preserve",
                "skill_reroute_triggers": [
                    "professional-domain",
                    "work-type",
                    "material-risk-trigger",
                ],
                "forbidden_triggers": [
                    "better-design-preference",
                    "speculative-abstraction",
                    "future-extensibility",
                    "optional-robustness",
                    "non-material-gap",
                    "style-or-documentation-polish",
                    "task-switch-or-completion",
                    "claim-local-evidence-reproof",
                ],
            },
            "first_executable_slice": {
                "defined_by": "engineering-brief",
                "contract": "Task Contract v2",
                "required_fields_source": (
                    "task_contract.template_schemas.engineering-brief-template.md."
                    "labeled_sections.First Executable Slice"
                ),
                "dispatch": "verbatim",
                "main_reinterpretation": "forbidden",
                "main_generation": "forbidden",
                "dag_reselection": "forbidden",
            },
            "decision_change_route": [
                "blocked",
                "main-control-agent",
                "analysis-agent",
                "update-engineering-brief",
                "redispatch-affected-tasks",
            ],
            "downstream_conflict": "return-to-analysis",
            "specialist_policy": {
                "authority": "input-only",
                "source_proven_placement": "write-directly-into-engineering-brief",
                "real_structural_choice": "invoke-corresponding-specialist",
                "effective_after": "incorporated-into-current-engineering-brief",
                "parallel_analysis_authority": "forbidden",
            },
            "decision_ownership": {
                "engineering_brief": [
                    "Goal",
                    "Acceptance",
                    "Non-goals",
                    "Owner",
                    "Invariants",
                    "Scope",
                    "Professional Skill",
                    "Layer3",
                    "Review requirements",
                ],
                "main": [
                    "Path control",
                    "Execution Level projection",
                    "Review scheduling",
                    "user decision interaction",
                ],
                "main_reinterpretation": "forbidden",
                "worker_route_change": "forbidden",
            },
            "dag_planner_policy": {
                "allowed": [
                    "task-splitting",
                    "dependencies",
                    "parallel-safety",
                    "critical-path",
                    "integration-merge-conflict-ownership",
                    "remaining-task-contract-projection",
                ],
                "forbidden": [
                    "select-first-executable-slice",
                    "modify-acceptance-or-non-goals",
                    "modify-owner-or-invariants",
                    "modify-contract-semantics",
                    "modify-rollback",
                ],
                "insufficient_brief": "return-to-analysis",
            },
            "unchanged_paths": ["direct-task", "non-implementation"],
        }
        if task["analyzed_work_authority"] != expected_analyzed_work_authority:
            errors.append(
                "task_contract.analyzed_work_authority must keep the Engineering "
                "Brief as the single analyzed-work decision authority"
            )

        expected_task_boundary = {
            "name": "Current Task Boundary",
            "fields": ["Goal", "Acceptance", "Non-goals"],
            "allowed_read_scope": "inspection-and-discovery-boundary",
            "allowed_write_scope": "permission-ceiling-not-work-obligation",
            "discovery_grants_repair_authority": False,
            "repository_clean_required": False,
            "granularity": "semantic-change-and-primary-professional-skill-boundary",
            "cohesion_rule": "one-acceptance-coeffective-and-naturally-validated-together",
            "primary_skill_per_task": "exactly-one",
            "split_when": [
                "distinct-semantic-change",
                "materially-different-primary-professional-skill",
            ],
            "do_not_split_by": ["file", "function", "code-layer", "test", "edit-step"],
            "review_requirement_fields": [
                "Required Review Skills",
                "Specialist Obligations",
                "Professional Risk Dimensions",
            ],
            "review_scheduling_forbidden_on_task_nodes": [
                "Review Strategy",
                "Review Round ID",
                "Review Assignments",
                "Primary Close Ordering",
            ],
            "combined_review_preserves": [
                "task-primary-professional-skills",
                "required-review-skills",
                "specialist-obligations",
                "professional-risk-dimensions",
            ],
            "scheduling_priority": [
                "current-requested-task",
                "declared-dag-work",
                "current-task-blockers",
                "adjacent-follow-up",
            ],
        }
        if task["task_boundary"] != expected_task_boundary:
            errors.append(
                "task_contract.task_boundary must equal Goal + Acceptance + "
                "Non-goals with read/discovery and write-permission ceilings"
            )

        expected_finding_relations = {
            "field": "Finding Relation",
            "values": ["current-task", "scope-blocker", "adjacent"],
            "classification_order": ["relation", "severity", "blocker"],
            "severity_relation": "orthogonal",
            "rules": {
                "current-task": {
                    "match_any": [
                        "introduced-or-regressed-by-current-diff",
                        "directly-violates-current-acceptance",
                        "violates-required-invariant-or-contract",
                        "required-to-complete-current-task-correctly",
                    ],
                    "blocking_allowed": True,
                    "repair_input_allowed": True,
                    "route": "task-agent-repair",
                },
                "scope-blocker": {
                    "required_for_current_task": True,
                    "match_any": [
                        "requires-expanded-allowed-write-scope",
                        "requires-acceptance-or-non-goal-change",
                        "requires-owner-invariant-or-contract-change",
                        "requires-new-analysis-decision",
                    ],
                    "blocking_allowed": True,
                    "repair_input_allowed": False,
                    "route": [
                        "blocked",
                        "main-control-agent",
                        "analysis-agent",
                        "update-authoritative-task-boundary",
                    ],
                },
                "adjacent": {
                    "required_for_current_task": False,
                    "blocking_allowed": False,
                    "repair_input_allowed": False,
                    "actions": [
                        "record-residual-risk",
                        "recommend-next-step",
                        "defer",
                        "continue-current-task",
                    ],
                    "high_or_critical_scope_authority": False,
                },
            },
            "material_current_task_criteria": [
                "acceptance",
                "correctness-or-invariant",
                "regression",
                "security-or-reliability",
                "material-code-health",
            ],
            "non_repair_categories": [
                "adjacent-issue",
                "optional-cleanup",
                "style-preference",
                "speculative-abstraction",
                "unrelated-technical-debt",
                "future-improvement",
            ],
            "fail_fast": {
                "triggers": [
                    "fundamental-architecture-error",
                    "invalid-public-contract",
                    "major-security-defect",
                    "acceptance-fundamentally-unmet",
                ],
                "verdict": "blocked",
                "required_scope_report": ["Reviewed Scope", "Unreviewed Scope"],
                "pass_requires_complete_changed_scope": True,
            },
            "ordinary_finding_action": (
                "continue-and-complete-fixed-review-boundary"
            ),
            "review_handoff_finding_set": (
                "all-evidence-backed-findings-from-current-review-round-and-fixed-boundary"
            ),
            "review_finding_scope_authority": False,
            "repair_input_relations": ["current-task"],
        }
        if task["finding_relations"] != expected_finding_relations:
            errors.append(
                "task_contract.finding_relations must remain the closed "
                "current-task/scope-blocker/adjacent relation policy"
            )

        expected_repair_routing = {
            "scope_authority": [
                "original-task-boundary",
                "accepted-current-task-finding",
            ],
            "batch_key": ["Review Round ID", "Task ID"],
            "batch_cardinality": (
                "exactly-one-repair-assignment-per-review-round-and-task-id"
            ),
            "assignment_contract": "Task Contract v2",
            "task_id_rule": "unchanged-from-finding-task-id",
            "batch_contents": (
                "all-material-current-task-findings-for-the-same-review-round-and-task-id"
            ),
            "eligible_round_completions": ["review", "re-review"],
            "per_finding_preserves": [
                "Finding Relation",
                "affected scope",
                "Acceptance or risk impact",
                "required validation",
                "required covering re-review",
            ],
            "cross_task_batching": "forbidden",
            "current_task_blocking": "task-agent-repair",
            "scope_blocker": "return-main-analysis",
            "adjacent": "report-defer-continue-primary-task",
            "adjacent_discovered_during_repair": "record-without-repair-expansion",
            "unrelated_changed_file": (
                "remove-current-task-unrelated-edit-without-repairing-file"
            ),
            "review_convergence": {
                "maximum_automatic_repair_rounds_per_task_id": 2,
                "budget_key": "Task ID",
                "budget_reset_forbidden": [
                    "Review Boundary ID",
                    "Review Round ID",
                    "Delta Analysis",
                ],
                "rereview_classifications": [
                    "inherited",
                    "repair-regression",
                    "frozen-boundary-violation",
                    "protected-invalidation",
                    "adjacent",
                ],
                "rereview_classification_to_finding_relation": {
                    "inherited": "current-task",
                    "repair-regression": "current-task",
                    "frozen-boundary-violation": "current-task",
                    "protected-invalidation": "scope-blocker",
                    "adjacent": "adjacent",
                },
                "blocking_classifications": [
                    "inherited",
                    "repair-regression",
                    "frozen-boundary-violation",
                ],
                "frozen_boundary_violation_requires_evidence": True,
                "cap_disposition": {
                    "unresolved-blocker": "blocked-non-converged",
                    "protected-decision-invalidated": "main-delta-analysis",
                    "adjacent-or-hardening-only": (
                        "close-current-contract-record-residual"
                    ),
                },
                "cap_implies_pass": False,
                "delta_analysis_budget_effect": (
                    "preserve-per-task-repair-count"
                ),
                "review_driven_delta_same_path_limit": 2,
                "review_driven_delta_retry_requires_any": [
                    "changed-hypothesis",
                    "changed-material",
                    "changed-gap",
                    "changed-transition",
                ],
                "third_unchanged_replan": "forbidden-blocked",
            },
        }
        if task["repair_routing"] != expected_repair_routing:
            errors.append(
                "task_contract.repair_routing must admit only current-task "
                "findings and return scope blockers to Main/Analysis"
            )

        expected_same_pattern_scan = {
            "required": True,
            "discovery_grants_repair_authority": False,
            "decision_inputs": [
                "current Acceptance",
                "current Invariant",
                "authorized repair scope",
            ],
            "routes": {
                "affects_current_inside_authorized_scope": "current-task-fix",
                "affects_current_outside_authorized_scope": (
                    "scope-blocker-return-main"
                ),
                "does_not_affect_current": "adjacent-record-do-not-edit",
            },
            "completion_requirement": (
                "all-current-task-occurrences-inside-authorized-repair-scope-fixed"
            ),
            "adjacent_requirement": "record-rationale-and-residual-risk",
        }
        if task["same_pattern_scan"] != expected_same_pattern_scan:
            errors.append(
                "task_contract.same_pattern_scan must preserve discovery while "
                "separating it from repair authorization"
            )

        templates = task["template_schemas"]
        utility_projection_rules = projection_rule_map(
            task["utility_projection_rules"],
            "task_contract.utility_projection_rules",
        )
        if len(utility_projection_rules) < 5:
            errors.append("task_contract.utility_projection_rules are incomplete")
        expected_templates = {
            "direct-task-template.md",
            "engineering-brief-template.md",
            "task-dag-template.md",
            "implementation-handoff-template.md",
            "review-handoff-template.md",
            "utility-capsule-template.md",
        }
        if not isinstance(templates, dict) or set(templates) != expected_templates:
            errors.append(f"task_contract.template_schemas must be exactly {sorted(expected_templates)}")
            templates = {}
        brief_schema = templates.get("engineering-brief-template.md")
        if isinstance(brief_schema, dict):
            labeled_sections = brief_schema.get("labeled_sections")
            first_slice_fields = (
                labeled_sections.get("First Executable Slice")
                if isinstance(labeled_sections, dict)
                else None
            )
            if not isinstance(first_slice_fields, list):
                errors.append(
                    "Engineering Brief First Executable Slice must define complete "
                    "Task Contract v2 fields"
                )
            else:
                projected_task_fields = [
                    field
                    for field in first_slice_fields
                    if field in required_task_fields["required_for_dag_task"]
                ]
                if projected_task_fields != required_task_fields["required_for_dag_task"]:
                    errors.append(
                        "Engineering Brief First Executable Slice must project every "
                        "required DAG Task Contract v2 field in canonical order"
                    )

        def validate_headings(schema: dict[str, Any], context: str) -> list[str]:
            raw = schema.get("headings")
            if not isinstance(raw, list) or not raw:
                errors.append(f"{context}.headings must be a non-empty list")
                return []
            titles: list[str] = []
            h1_titles: list[str] = []
            current_h1 = "<document>"
            scoped_titles: list[tuple[str, str]] = []
            for index, item in enumerate(raw):
                if (
                    not isinstance(item, list)
                    or len(item) != 2
                    or not isinstance(item[0], int)
                    or isinstance(item[0], bool)
                    or item[0] not in {1, 2}
                    or not isinstance(item[1], str)
                    or not item[1].strip()
                ):
                    errors.append(f"{context}.headings[{index}] must be [level, title]")
                    continue
                level, title = item
                titles.append(title)
                if level == 1:
                    h1_titles.append(title)
                    current_h1 = title
                else:
                    scoped_titles.append((current_h1, title))
            if len(h1_titles) != len(set(h1_titles)):
                errors.append(f"{context}.headings H1 titles must be unique")
            if (
                not h1_titles
                or not isinstance(raw[0], list)
                or len(raw[0]) != 2
                or raw[0][0] != 1
            ):
                errors.append(f"{context}.headings must start with an H1")
            if len(scoped_titles) != len(set(scoped_titles)):
                errors.append(
                    f"{context}.headings titles must be unique within each H1 section"
                )
            return titles

        def canonical_core_subsequence(
            values: list[str], context: str, *, allow_optional_direct: bool = False
        ) -> None:
            core_values = [value for value in values if value in fields]
            if len(core_values) != len(set(core_values)):
                errors.append(f"{context} must not repeat a core Task Contract field")
                return
            allowed = (
                required_task_fields["required_for_direct_task"]
                + optional_direct_fields
                if allow_optional_direct
                else fields
            )
            expected = [value for value in fields if value in core_values]
            if core_values != expected or not set(core_values) <= set(allowed):
                errors.append(f"{context} core fields must preserve canonical order")

        for file_name, schema in templates.items():
            context = f"task_contract.template_schemas.{file_name}"
            if not isinstance(schema, dict):
                errors.append(f"{context} must be an object")
                continue
            common = {"container", "headings"}
            if file_name == "direct-task-template.md":
                expected_schema_fields = common | {
                    "task_fields",
                    "optional_heading_insertions",
                    "extension_fields",
                    "extension_heading_insertions",
                }
            elif file_name == "engineering-brief-template.md":
                expected_schema_fields = common | {
                    "labeled_sections",
                    "task_fields_section",
                    "task_extension_fields",
                }
            elif file_name == "task-dag-template.md":
                expected_schema_fields = common | {
                    "labeled_sections",
                    "task_node_sections",
                    "task_extension_fields",
                }
            elif file_name == "implementation-handoff-template.md":
                expected_schema_fields = common | {
                    "labeled_sections",
                    "ledger_required",
                    "freshness_projection_ids",
                    "forbidden_storage_projection_ids",
                }
            elif file_name == "review-handoff-template.md":
                expected_schema_fields = common | {
                    "labeled_sections",
                    "ledger_required",
                    "freshness_projection_ids",
                }
            elif file_name == "utility-capsule-template.md":
                expected_schema_fields = common | {"ledger_required", "status_sections"}
            else:
                expected_schema_fields = common | {"ledger_required"}
            if not exact_keys(schema, expected_schema_fields, context):
                continue
            if schema["container"] not in {"fenced-markdown", "document"}:
                errors.append(f"{context}.container is invalid")
            titles = validate_headings(schema, context)
            if file_name == "direct-task-template.md":
                direct_fields = string_list(schema["task_fields"], f"{context}.task_fields")
                extensions = string_list(schema["extension_fields"], f"{context}.extension_fields")
                canonical_core_subsequence(
                    direct_fields,
                    f"{context}.task_fields",
                    allow_optional_direct=True,
                )
                if not set(required_task_fields["required_for_direct_task"]) <= set(direct_fields):
                    errors.append(f"{context}.task_fields omit a required Direct Task field")
                if set(direct_fields) - set(required_task_fields["required_for_direct_task"]):
                    errors.append(f"{context}.task_fields may contain only required fields")
                insertions = schema["optional_heading_insertions"]
                if not isinstance(insertions, dict) or set(insertions) != set(
                    optional_direct_fields
                ):
                    errors.append(
                        f"{context}.optional_heading_insertions must cover optional Direct fields"
                    )
                    insertions = {}
                for optional_field, insertion in insertions.items():
                    insertion_context = (
                        f"{context}.optional_heading_insertions.{optional_field}"
                    )
                    if not exact_keys(insertion, {"after"}, insertion_context):
                        continue
                    assert isinstance(insertion, dict)
                    previous_index = fields.index(optional_field) - 1
                    if previous_index < 0 or insertion["after"] != fields[previous_index]:
                        errors.append(
                            f"{insertion_context}.after must use canonical insertion position"
                        )
                if set(extensions) & set(fields):
                    errors.append(f"{context}.extension_fields must not redefine core fields")
                extension_insertions = schema["extension_heading_insertions"]
                if not isinstance(extension_insertions, dict) or set(
                    extension_insertions
                ) != set(extensions):
                    errors.append(
                        f"{context}.extension_heading_insertions must cover every extension"
                    )
                    extension_insertions = {}
                ordered_direct_titles = list(direct_fields)
                for extension in extensions:
                    insertion = extension_insertions.get(extension)
                    insertion_context = (
                        f"{context}.extension_heading_insertions.{extension}"
                    )
                    if not exact_keys(insertion, {"after"}, insertion_context):
                        continue
                    assert isinstance(insertion, dict)
                    anchor = insertion["after"]
                    if anchor not in ordered_direct_titles:
                        errors.append(
                            f"{insertion_context}.after must name an earlier visible field"
                        )
                        continue
                    ordered_direct_titles.insert(
                        ordered_direct_titles.index(anchor) + 1,
                        extension,
                    )
                expected_direct_headings = [
                    [1, "Direct Task Contract v2"],
                    *[[2, field] for field in ordered_direct_titles],
                ]
                if schema["headings"] != expected_direct_headings:
                    errors.append(
                        f"{context}.headings must exactly follow the Direct Task "
                        "core and extension field order"
                    )
            elif file_name in {"engineering-brief-template.md", "task-dag-template.md"}:
                labeled = schema["labeled_sections"]
                if not isinstance(labeled, dict) or not labeled:
                    errors.append(f"{context}.labeled_sections must be a non-empty object")
                    continue
                for section, section_fields in labeled.items():
                    if section not in titles:
                        errors.append(f"{context}: labeled section {section!r} lacks a heading")
                    values = string_list(
                        section_fields, f"{context}.labeled_sections.{section}"
                    )
                    canonical_core_subsequence(
                        values, f"{context}.labeled_sections.{section}"
                    )
                extensions = string_list(
                    schema["task_extension_fields"], f"{context}.task_extension_fields"
                )
                if set(extensions) & set(fields):
                    errors.append(f"{context}.task_extension_fields redefine core fields")
                if file_name == "engineering-brief-template.md":
                    if labeled.get("Review Boundary") != [
                        "Review Owner",
                        *expected_subsumption["review_boundary_fields"],
                    ]:
                        errors.append(
                            f"{context}: Review Boundary must derive every Core subsumption field"
                        )
                    task_section = schema["task_fields_section"]
                    if task_section not in labeled:
                        errors.append(f"{context}.task_fields_section is unknown")
                    else:
                        trailing_extensions = [
                            value
                            for value in extensions
                            if value not in canonical_public_extension_fields
                        ]
                        expected_task_fields = (
                            required_task_fields["required_for_dag_task"][:2]
                            + canonical_public_extension_fields
                            + required_task_fields["required_for_dag_task"][2:]
                            + trailing_extensions
                        )
                        if labeled[task_section] != expected_task_fields:
                            errors.append(f"{context}: executable slice fields are not canonical")
                else:
                    if labeled.get("Review Boundary") != [
                        "Review Owner",
                        *expected_subsumption["review_boundary_fields"],
                    ]:
                        errors.append(
                            f"{context}: Review Boundary must derive every Core subsumption field"
                        )
                    node_sections = string_list(
                        schema["task_node_sections"], f"{context}.task_node_sections"
                    )
                    trailing_extensions = [
                        value
                        for value in extensions
                        if value not in canonical_public_extension_fields
                    ]
                    expected_task_fields = (
                        required_task_fields["required_for_dag_task"][:2]
                        + canonical_public_extension_fields
                        + required_task_fields["required_for_dag_task"][2:]
                        + trailing_extensions
                    )
                    for section in node_sections:
                        if labeled.get(section) != expected_task_fields:
                            errors.append(f"{context}: {section} fields are not canonical")
                    if labeled.get("Parallel Group") != parallel_fields:
                        errors.append(f"{context}: Parallel Group fields are not canonical")
            else:
                if schema["ledger_required"] is not True:
                    errors.append(f"{context}.ledger_required must be true")
                if file_name == "implementation-handoff-template.md":
                    labeled = schema["labeled_sections"]
                    expected_labels = [
                        "Latest Changed Paths",
                        "Exact Reviewable Change Evidence",
                        "Reviewer Capability Accessibility",
                        "Validation After Latest Material Edit",
                        "Fixed Review Scope",
                    ]
                    if (
                        not isinstance(labeled, dict)
                        or labeled.get("Review Input Ready") != expected_labels
                        or set(labeled) != {"Review Input Ready"}
                    ):
                        errors.append(
                            f"{context}.labeled_sections must project the exact "
                            "Review Input Ready fields"
                        )
                elif file_name == "review-handoff-template.md":
                    labeled = schema["labeled_sections"]
                    if (
                        not isinstance(labeled, dict)
                        or labeled.get("Inbound Review Projection")
                        != review_discipline["review_scope"][
                            "handoff_projection_fields"
                        ]
                        or labeled.get("Review Boundary")
                        != expected_subsumption["review_boundary_fields"]
                        or set(labeled)
                        != {"Inbound Review Projection", "Review Boundary"}
                    ):
                        errors.append(
                            f"{context}.labeled_sections must project the exact inbound "
                            "Review projection and every Review Boundary dimension"
                        )
                if "freshness_projection_ids" in schema:
                    freshness_ids = string_list(
                        schema["freshness_projection_ids"],
                        f"{context}.freshness_projection_ids",
                    )
                    bind_projection_ids(
                        declared_freshness_targets,
                        freshness_ids,
                        file_name,
                    )
                if "forbidden_storage_projection_ids" in schema:
                    forbidden_storage_ids = string_list(
                        schema["forbidden_storage_projection_ids"],
                        f"{context}.forbidden_storage_projection_ids",
                    )
                    bind_projection_ids(
                        declared_forbidden_storage_targets,
                        forbidden_storage_ids,
                        file_name,
                    )
                for required_heading in ("Status", "Task ID", "Owner", "Evidence Ledger"):
                    if required_heading not in titles:
                        errors.append(f"{context}.headings must include {required_heading!r}")
                if file_name == "utility-capsule-template.md":
                    status_sections = schema["status_sections"]
                    if not isinstance(status_sections, list) or len(status_sections) != 2:
                        errors.append(f"{context}.status_sections must define assignment and return")
                    else:
                        expected_parents = ["Utility Assignment", "Utility Return"]
                        valid_status_sections = all(
                            isinstance(status_section, dict)
                            for status_section in status_sections
                        )
                        for index, status_section in enumerate(status_sections):
                            status_context = f"{context}.status_sections[{index}]"
                            if not exact_keys(
                                status_section,
                                {"parent", "allowed"},
                                status_context,
                            ):
                                continue
                            assert isinstance(status_section, dict)
                            if status_section["parent"] != expected_parents[index]:
                                errors.append(f"{status_context}.parent is out of order")
                            allowed_statuses = string_list(
                                status_section["allowed"], f"{status_context}.allowed"
                            )
                            if not set(allowed_statuses) <= set(statuses):
                                errors.append(f"{status_context}.allowed contains unknown status")
                        if valid_status_sections:
                            if status_sections[0].get("allowed") != [
                                task["assignment_initial_status"]
                            ]:
                                errors.append(
                                    f"{context}: Utility Assignment must use the canonical "
                                    "assignment initial status"
                                )
                            if status_sections[1].get("allowed") != [
                                "blocked",
                                "partial",
                                "completed",
                            ]:
                                errors.append(
                                    f"{context}: Utility Return status values are invalid"
                                )

    evidence = data["visible_evidence_contract"]
    evidence_fields = {
        "schema_version",
        "visibility",
        "persistence",
        "fields",
        "states",
        "conditional_test_evidence",
        "completion_proof",
        "freshness_rules",
        "forbidden_storage",
    }
    if exact_keys(evidence, evidence_fields, "visible_evidence_contract"):
        assert isinstance(evidence, dict)
        if evidence["schema_version"] != 3:
            errors.append("visible_evidence_contract.schema_version must be 3")
        if evidence["visibility"] != "task-local-visible-markdown":
            errors.append("Evidence Ledger must be task-local visible Markdown")
        if evidence["persistence"] != "handoff-only":
            errors.append("Evidence Ledger must be handoff-only")
        ledger_fields = string_list(evidence["fields"], "visible_evidence_contract.fields")
        expected_ledger_fields = [
            "Claim",
            "Owner",
            "Artifact",
            "Command",
            "Result",
            "Freshness",
            "Scope",
            "Proof Limit",
            "State",
        ]
        if ledger_fields != expected_ledger_fields:
            errors.append("Evidence Ledger fields must be the exact lightweight visible core")
        ledger_states = string_list(
            evidence["states"], "visible_evidence_contract.states"
        )
        if ledger_states != ["current", "superseded", "invalid"]:
            errors.append("Evidence Ledger states must be current, superseded, invalid")
        conditional_test_evidence = evidence["conditional_test_evidence"]
        conditional_context = "conditional test evidence contract"
        if exact_keys(
            conditional_test_evidence,
            {
                "schema_version",
                "claim_values",
                "record_only_when_applicable",
                "separate_stage",
                "unavailable_proof_rule",
                "projection_targets",
                "projection_text",
            },
            conditional_context,
        ):
            assert isinstance(conditional_test_evidence, dict)
            if conditional_test_evidence["schema_version"] != 1:
                errors.append(f"{conditional_context}.schema_version must be 1")
            claim_values = string_list(
                conditional_test_evidence["claim_values"],
                f"{conditional_context}.claim_values",
            )
            if claim_values != [
                "test-approach-selected",
                "red-proof",
                "green-proof",
            ]:
                errors.append(
                    f"{conditional_context}.claim_values must be the exact supported claims"
                )
            if conditional_test_evidence["record_only_when_applicable"] is not True:
                errors.append(
                    f"{conditional_context}.record_only_when_applicable must be true"
                )
            if conditional_test_evidence["separate_stage"] is not False:
                errors.append(f"{conditional_context}.separate_stage must be false")
            if conditional_test_evidence["unavailable_proof_rule"] != "never-fabricate":
                errors.append(
                    f"{conditional_context}.unavailable_proof_rule must be "
                    "never-fabricate"
                )
            projection_targets = string_list(
                conditional_test_evidence["projection_targets"],
                f"{conditional_context}.projection_targets",
            )
            expected_conditional_targets = [
                "direct-task-template.md",
                "engineering-brief-template.md",
                "task-dag-template.md",
                "implementation-handoff-template.md",
                "review-handoff-template.md",
            ]
            if projection_targets != expected_conditional_targets:
                errors.append(
                    f"{conditional_context}.projection_targets must bind the five "
                    "implementation assignment, handoff, and review templates exactly"
                )
            try:
                expected_projection_text = conditional_test_evidence_projection_text(
                    conditional_test_evidence
                )
            except ValueError as exc:
                errors.append(f"{conditional_context}: {exc}")
            else:
                if (
                    conditional_test_evidence["projection_text"]
                    != expected_projection_text
                ):
                    errors.append(
                        f"{conditional_context}.projection_text must be the exact "
                        "Core-derived public guidance"
                    )
        completion_proof = evidence["completion_proof"]
        if exact_keys(
            completion_proof,
            {"implementation"},
            "visible_evidence_contract.completion_proof",
        ):
            assert isinstance(completion_proof, dict)
            implementation_proof = completion_proof["implementation"]
            proof_context = "visible_evidence_contract.completion_proof.implementation"
            if exact_keys(
                implementation_proof,
                {
                    "task_claim_owner",
                    "implementation_owner_role",
                    "independent_review_owner",
                    "independent_owner_required",
                    "latest_material_edit_claim",
                    "validation_claim",
                    "high_risk_review_requirement",
                    "required_review_claims",
                    "projections",
                },
                proof_context,
            ):
                assert isinstance(implementation_proof, dict)
                if implementation_proof["task_claim_owner"] != "completion-claim-owner":
                    errors.append(
                        f"{proof_context}.task_claim_owner must bind to the completion claim owner"
                    )
                implementation_owner = implementation_proof[
                    "implementation_owner_role"
                ]
                if implementation_owner != "task-agent" or implementation_owner not in role_names:
                    errors.append(
                        f"{proof_context}.implementation_owner_role must be task-agent"
                    )
                review_owner = implementation_proof["independent_review_owner"]
                if review_owner != "review-agent" or review_owner not in role_names:
                    errors.append(
                        f"{proof_context}.independent_review_owner must be review-agent"
                    )
                if implementation_proof["independent_owner_required"] is not True:
                    errors.append(
                        f"{proof_context}.independent_owner_required must be true"
                    )
                if implementation_owner == review_owner:
                    errors.append(
                        f"{proof_context} implementation and review owners must differ"
                    )
                latest_edit_claim = implementation_proof[
                    "latest_material_edit_claim"
                ]
                if latest_edit_claim != "latest-material-edit":
                    errors.append(
                        f"{proof_context}.latest_material_edit_claim must be latest-material-edit"
                    )
                validation_claim = implementation_proof["validation_claim"]
                if validation_claim != "validation-passed":
                    errors.append(
                        f"{proof_context}.validation_claim must be validation-passed"
                    )
                review_requirement = implementation_proof[
                    "high_risk_review_requirement"
                ]
                expected_review_requirement = {
                    "binding_fields": ["capsule_canonical_sha256"],
                    "authority_fields": ["task_dispatch", "review_assignment"],
                    "authority_actor": "main-control-agent",
                    "authority_task_profile": "task-agent",
                    "authority_review_profile": "review-agent",
                    "capsule_contract_version": "changeforge.fixture-capsule.v2",
                    "high_risk_floor": "L4",
                    "critical_trigger_statuses": ["matched"],
                    "provisional_critical_trigger": {
                        "id": "unknown-critical-boundary",
                        "status": "unknown",
                        "flag": "plausible_critical",
                    },
                    "low_risk_review_strategy": "independent-implementation-review",
                    "low_risk_review_mode": "implementation-review",
                    "high_risk_review_strategies": [
                        "independent-high-risk-review",
                        "exhaustive-high-risk-review",
                    ],
                    "legacy_not_required": "reissue-with-current-binding",
                }
                if review_requirement != expected_review_requirement:
                    errors.append(
                        f"{proof_context}.high_risk_review_requirement must bind "
                        "a digest-only claim to authoritative task and review dispatches"
                    )
                required_review_claims = implementation_proof[
                    "required_review_claims"
                ]
                expected_review_conditions = {
                    "changed_scope_reviewed": {"true"},
                    "high_risk_review": {"passed"},
                    "blocking_findings": {"none", "resolved"},
                }
                review_claim_values: list[str] = []
                if not isinstance(required_review_claims, dict) or set(
                    required_review_claims
                ) != set(expected_review_conditions):
                    errors.append(
                        f"{proof_context}.required_review_claims are incomplete"
                    )
                else:
                    for field, expected_values in expected_review_conditions.items():
                        mapping = required_review_claims[field]
                        if not isinstance(mapping, dict) or set(mapping) != expected_values:
                            errors.append(
                                f"{proof_context}.required_review_claims.{field} "
                                "has invalid conditions"
                            )
                            continue
                        review_claim_values.extend(
                            string_list(
                                list(mapping.values()),
                                f"{proof_context}.required_review_claims.{field}",
                            )
                        )
                    if len(review_claim_values) != len(set(review_claim_values)):
                        errors.append(
                            f"{proof_context}.required_review_claims must be unique"
                        )
                prompt_contract = data.get("prompt_contract", {})
                prompt_target = (
                    f"prompt:{prompt_contract.get('evidence_section')}"
                    if isinstance(prompt_contract, dict)
                    else ""
                )
                base_review_terms = {
                    "current review-agent evidence",
                    "latest material edit",
                    *review_claim_values,
                }
                expected_projections = {
                    prompt_target: {
                        f"Claims: {latest_edit_claim}, {validation_claim}",
                        *base_review_terms,
                    },
                    "profile:task-agent": {
                        "current task-agent evidence",
                        "latest material edit",
                        latest_edit_claim,
                        validation_claim,
                    },
                    "implementation-handoff-template.md": {
                        "current task-agent evidence",
                        "latest material edit",
                        latest_edit_claim,
                        validation_claim,
                    },
                    "profile:review-agent": base_review_terms,
                    "review-handoff-template.md": base_review_terms,
                }
                projections = implementation_proof["projections"]
                seen_targets: set[str] = set()
                if not isinstance(projections, list) or len(projections) != len(
                    expected_projections
                ):
                    errors.append(f"{proof_context}.projections are incomplete")
                else:
                    for index, projection in enumerate(projections):
                        projection_context = f"{proof_context}.projections[{index}]"
                        if not exact_keys(
                            projection,
                            {"target", "terms"},
                            projection_context,
                        ):
                            continue
                        assert isinstance(projection, dict)
                        target = projection["target"]
                        if not isinstance(target, str) or not target:
                            errors.append(f"{projection_context}.target must be text")
                            continue
                        if target in seen_targets:
                            errors.append(
                                f"{proof_context}.projections repeat target {target!r}"
                            )
                        seen_targets.add(target)
                        terms = string_list(
                            projection["terms"], f"{projection_context}.terms"
                        )
                        expected_terms = expected_projections.get(target)
                        if expected_terms is None or set(terms) != expected_terms:
                            errors.append(
                                f"{projection_context} must exactly project the "
                                "assigned review evidence contract"
                            )
                    if seen_targets != set(expected_projections):
                        errors.append(
                            f"{proof_context}.projections must target prompt, task-agent, "
                            "Implementation Handoff, review-agent, and Review Handoff exactly"
                        )
        freshness_rules = projection_rule_map(
            evidence["freshness_rules"],
            "visible_evidence_contract.freshness_rules",
            extra_field="projection_targets",
        )
        if len(freshness_rules) < 3:
            errors.append("Evidence Ledger freshness rules are incomplete")
        task_templates = data.get("task_contract", {}).get("template_schemas", {})
        prompt_model = data.get("prompt_contract", {})
        prompt_sections = {
            value
            for key, value in (
                prompt_model.items() if isinstance(prompt_model, dict) else ()
            )
            if key.endswith("_section") and isinstance(value, str)
        }
        allowed_freshness_targets = {
            *(task_templates if isinstance(task_templates, dict) else {}),
            *{f"prompt:{section}" for section in prompt_sections},
        }
        for index, rule in enumerate(evidence["freshness_rules"]):
            if not isinstance(rule, dict):
                continue
            targets = string_list(
                rule.get("projection_targets"),
                f"visible_evidence_contract.freshness_rules[{index}].projection_targets",
            )
            if not set(targets) <= allowed_freshness_targets:
                errors.append(
                    "Evidence Ledger freshness rule has an unknown projection target"
                )
            rule_id = rule.get("id")
            if isinstance(rule_id, str):
                freshness_rule_targets[rule_id] = set(targets)
        forbidden_rules = projection_rule_map(
            evidence["forbidden_storage"],
            "visible_evidence_contract.forbidden_storage",
            extra_field="projection_targets",
        )
        required_forbidden_ids = {
            "no-daemon",
            "no-database",
            "no-private-evidence-storage",
            "no-runtime-task-state-engine",
            "no-hidden-protocol-record",
        }
        if set(forbidden_rules) != required_forbidden_ids:
            errors.append("Evidence Ledger forbidden storage ids are incomplete")
        for index, rule in enumerate(evidence["forbidden_storage"]):
            if not isinstance(rule, dict):
                continue
            targets = string_list(
                rule.get("projection_targets"),
                f"visible_evidence_contract.forbidden_storage[{index}].projection_targets",
            )
            rule_id = rule.get("id")
            if isinstance(rule_id, str):
                forbidden_storage_rule_targets[rule_id] = set(targets)

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

    prompt_concept_ids: set[str] = set()
    prompt = data["prompt_contract"]
    prompt_fields = {
        "schema_version",
        "path",
        "document_sha256",
        "managed_projections",
        "ordered_headings",
        "concepts",
        "task_contract_section",
        "completion_section",
        "evidence_section",
        "capability_section",
        "freshness_projection_ids_by_section",
        "forbidden_storage_projection_ids_by_section",
    }
    if exact_keys(prompt, prompt_fields, "prompt_contract"):
        assert isinstance(prompt, dict)
        if prompt["schema_version"] != 1:
            errors.append("prompt_contract.schema_version must be 1")
        if not isinstance(prompt["path"], str) or not prompt["path"].endswith(".md"):
            errors.append("prompt_contract.path must name a Markdown source")
        if not isinstance(prompt["document_sha256"], str) or re.fullmatch(
            r"[0-9a-f]{64}", prompt["document_sha256"]
        ) is None:
            errors.append("prompt_contract.document_sha256 must be lowercase SHA-256")
        prompt_headings = ordered_heading_titles(
            prompt["ordered_headings"], "prompt_contract.ordered_headings"
        )
        managed_projections = prompt["managed_projections"]
        seen_managed_ids: set[str] = set()
        if not isinstance(managed_projections, list) or not managed_projections:
            errors.append("prompt_contract.managed_projections must be a non-empty list")
            managed_projections = []
        for index, managed in enumerate(managed_projections):
            context = f"prompt_contract.managed_projections[{index}]"
            if not exact_keys(
                managed,
                {"id", "section", "required_contracts"},
                context,
            ):
                continue
            assert isinstance(managed, dict)
            identifier = managed["id"]
            if not isinstance(identifier, str) or identifier not in (
                PROMPT_MANAGED_PROJECTION_CONTRACTS
            ):
                errors.append(f"{context}.id is not a supported Prompt projection")
                continue
            if identifier in seen_managed_ids:
                errors.append("prompt_contract managed projection ids must be unique")
            seen_managed_ids.add(identifier)
            expected_managed = PROMPT_MANAGED_PROJECTION_CONTRACTS[identifier]
            if managed["section"] != expected_managed["section"]:
                errors.append(f"{context}.section disagrees with the managed contract")
            contracts = string_list(
                managed["required_contracts"], f"{context}.required_contracts"
            )
            if contracts != expected_managed["required_contracts"]:
                errors.append(
                    f"{context}.required_contracts must exactly bind its source contracts"
                )
            try:
                prompt_projection_block(data, managed)
            except (IndexError, KeyError, TypeError, ValueError) as exc:
                errors.append(f"{context}: cannot render managed Prompt projection: {exc}")
        if seen_managed_ids != set(PROMPT_MANAGED_PROJECTION_CONTRACTS):
            errors.append(
                "prompt_contract.managed_projections must exactly cover Review/Evidence "
                "and Closure"
            )
        prompt_concept_ids = concept_contract_errors(
            prompt["concepts"], prompt_headings, "prompt_contract.concepts"
        )
        for section_field in (
            "task_contract_section",
            "completion_section",
            "evidence_section",
            "capability_section",
        ):
            if prompt[section_field] not in prompt_headings:
                errors.append(f"prompt_contract.{section_field} is not an ordered heading")
        for mapping_field, bindings in (
            (
                "freshness_projection_ids_by_section",
                declared_freshness_targets,
            ),
            (
                "forbidden_storage_projection_ids_by_section",
                declared_forbidden_storage_targets,
            ),
        ):
            mapping = prompt[mapping_field]
            if not isinstance(mapping, dict) or not mapping:
                errors.append(f"prompt_contract.{mapping_field} must be a non-empty object")
                continue
            for section, rule_ids in mapping.items():
                if section not in prompt_headings:
                    errors.append(
                        f"prompt_contract.{mapping_field}.{section} is not an ordered heading"
                    )
                ids = string_list(
                    rule_ids,
                    f"prompt_contract.{mapping_field}.{section}",
                )
                bind_projection_ids(bindings, ids, f"prompt:{section}")

    profile_contract = data["profile_contract"]
    profile_fields = {
        "schema_version",
        "source_path",
        "profile_fields",
        "optional_fields_by_role",
        "instruction_rule_count",
        "forbidden_instruction_terms",
        "capability_terms",
        "role_capabilities",
        "handoff_contracts",
    }
    if exact_keys(profile_contract, profile_fields, "profile_contract"):
        assert isinstance(profile_contract, dict)
        if profile_contract["schema_version"] != 2:
            errors.append("profile_contract.schema_version must be 2")
        if not isinstance(profile_contract["source_path"], str) or not profile_contract[
            "source_path"
        ].endswith(".json"):
            errors.append("profile_contract.source_path must name a JSON source")
        base_profile_fields = string_list(
            profile_contract["profile_fields"], "profile_contract.profile_fields"
        )
        for field in ("name", "description", "sandbox", "tools", "instructions"):
            if field not in base_profile_fields:
                errors.append(f"profile_contract.profile_fields must include {field!r}")
        optional = profile_contract["optional_fields_by_role"]
        if not isinstance(optional, dict) or set(optional) != set(roles):
            errors.append("profile_contract.optional_fields_by_role must match roles")
            optional = {}
        for role_name, values in optional.items():
            optional_fields = string_list(
                values,
                f"profile_contract.optional_fields_by_role.{role_name}",
                nonempty=False,
            )
            if set(optional_fields) & set(base_profile_fields):
                errors.append(f"{role_name}: optional profile fields duplicate base fields")
        limits = profile_contract["instruction_rule_count"]
        if exact_keys(
            limits,
            {"minimum", "maximum", "maximum_by_role"},
            "profile_contract.instruction_rule_count",
        ):
            assert isinstance(limits, dict)
            if (
                not isinstance(limits["minimum"], int)
                or isinstance(limits["minimum"], bool)
                or not isinstance(limits["maximum"], int)
                or isinstance(limits["maximum"], bool)
                or not 1 <= limits["minimum"] <= limits["maximum"]
            ):
                errors.append("profile_contract instruction limits are invalid")
            maximum_by_role = limits["maximum_by_role"]
            if not isinstance(maximum_by_role, dict):
                errors.append(
                    "profile_contract instruction maximum_by_role must be an object"
                )
            else:
                unknown_limit_roles = set(maximum_by_role) - set(roles)
                if unknown_limit_roles:
                    errors.append(
                        "profile_contract instruction maximum_by_role contains unknown "
                        f"roles: {sorted(unknown_limit_roles)}"
                    )
                for role_name, role_maximum in maximum_by_role.items():
                    if (
                        not isinstance(role_maximum, int)
                        or isinstance(role_maximum, bool)
                        or role_maximum < limits["maximum"]
                    ):
                        errors.append(
                            "profile_contract instruction maximum_by_role."
                            f"{role_name} must be an integer at least equal to the "
                            "default maximum"
                        )
        string_list(
            profile_contract["forbidden_instruction_terms"],
            "profile_contract.forbidden_instruction_terms",
        )
        capability_terms = profile_contract["capability_terms"]
        if not isinstance(capability_terms, dict) or not capability_terms:
            errors.append("profile_contract.capability_terms must be a non-empty object")
            capability_terms = {}
        else:
            exact_rule_bindings: set[tuple[str, str]] = set()
            for capability_id, rules in capability_terms.items():
                if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", capability_id) is None:
                    errors.append(f"invalid profile capability id {capability_id!r}")
                instruction_rule_groups(
                    rules,
                    f"profile_contract.capability_terms.{capability_id}",
                    allow_exact_rule=True,
                )
                if isinstance(rules, list):
                    for rule in rules:
                        if (
                            isinstance(rule, dict)
                            and isinstance(rule.get("rule_id"), str)
                            and "exact_rule" in rule
                        ):
                            exact_rule_bindings.add(
                                (capability_id, str(rule["rule_id"]))
                            )
            if exact_rule_bindings != PROFILE_EXACT_RULE_BINDINGS:
                errors.append(
                    "profile_contract exact_rule bindings must be exactly "
                    f"{sorted(PROFILE_EXACT_RULE_BINDINGS)}; "
                    f"found {sorted(exact_rule_bindings)}"
                )
        handoffs = profile_contract["handoff_contracts"]
        if not isinstance(handoffs, dict) or not handoffs:
            errors.append("profile_contract.handoff_contracts must be a non-empty object")
            handoffs = {}
        else:
            for handoff_id, rules in handoffs.items():
                if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", handoff_id) is None:
                    errors.append(f"invalid profile handoff id {handoff_id!r}")
                instruction_rule_groups(
                    rules, f"profile_contract.handoff_contracts.{handoff_id}"
                )
        role_capabilities = profile_contract["role_capabilities"]
        if not isinstance(role_capabilities, dict) or set(role_capabilities) != set(roles):
            errors.append("profile_contract.role_capabilities must match roles")
            role_capabilities = {}
        for role_name, role_capability in role_capabilities.items():
            context = f"profile_contract.role_capabilities.{role_name}"
            if not exact_keys(
                role_capability,
                {
                    "required_capability_ids",
                    "forbidden_capabilities",
                    "handoff_contract",
                    "forbidden_storage_projection_ids",
                },
                context,
            ):
                continue
            assert isinstance(role_capability, dict)
            capability_ids = string_list(
                role_capability["required_capability_ids"],
                f"{context}.required_capability_ids",
            )
            known_capability_ids = set(capability_terms)
            if implementation_discipline_capability_id:
                known_capability_ids.add(implementation_discipline_capability_id)
            if review_discipline_capability_id:
                known_capability_ids.add(review_discipline_capability_id)
            unknown_ids = sorted(set(capability_ids) - known_capability_ids)
            if unknown_ids:
                errors.append(f"{context} contains unknown capability ids {unknown_ids}")
            has_implementation_discipline = (
                implementation_discipline_capability_id in capability_ids
            )
            if has_implementation_discipline != (role_name == "task-agent"):
                errors.append(
                    f"{context} must project implementation discipline only to "
                    "task-agent"
                )
            has_review_discipline = review_discipline_capability_id in capability_ids
            if has_review_discipline != (role_name == "review-agent"):
                errors.append(
                    f"{context} must project review discipline only to review-agent"
                )
            forbidden_capabilities = string_list(
                role_capability["forbidden_capabilities"],
                f"{context}.forbidden_capabilities",
            )
            expected_forbidden = {
                capability
                for capability in ("may_dispatch", "may_edit", "may_review")
                if isinstance(roles.get(role_name), dict)
                and roles[role_name].get(capability) is False
            }
            if set(forbidden_capabilities) != expected_forbidden:
                errors.append(f"{context}.forbidden_capabilities disagree with role flags")
            if role_capability["handoff_contract"] not in handoffs:
                errors.append(f"{context}.handoff_contract is unknown")
            forbidden_storage_projection_ids = string_list(
                role_capability["forbidden_storage_projection_ids"],
                f"{context}.forbidden_storage_projection_ids",
                nonempty=False,
            )
            bind_projection_ids(
                declared_forbidden_storage_targets,
                forbidden_storage_projection_ids,
                f"profile:{role_name}",
            )

    control_concept_ids: set[str] = set()
    control_skill = data["control_skill_contract"]
    control_skill_fields = {
        "schema_version",
        "path",
        "prompt_path",
        "ordered_headings",
        "concepts",
        "reference_path_source",
        "forbidden_storage_projection_ids_by_section",
    }
    if exact_keys(control_skill, control_skill_fields, "control_skill_contract"):
        assert isinstance(control_skill, dict)
        if control_skill["schema_version"] != 1:
            errors.append("control_skill_contract.schema_version must be 1")
        for path_field in ("path", "prompt_path"):
            if not isinstance(control_skill[path_field], str) or not control_skill[
                path_field
            ].endswith(".md"):
                errors.append(f"control_skill_contract.{path_field} must name Markdown")
        if isinstance(prompt, dict) and control_skill["prompt_path"] != prompt.get("path"):
            errors.append("control Skill prompt_path must match prompt_contract.path")
        control_headings = ordered_heading_titles(
            control_skill["ordered_headings"],
            "control_skill_contract.ordered_headings",
        )
        control_concept_ids = concept_contract_errors(
            control_skill["concepts"],
            control_headings,
            "control_skill_contract.concepts",
        )
        if control_skill["reference_path_source"] != "reference_contract.control_required_by":
            errors.append("control Skill References must derive from Reference Contract v2")
        forbidden_bindings = control_skill[
            "forbidden_storage_projection_ids_by_section"
        ]
        if not isinstance(forbidden_bindings, dict) or not forbidden_bindings:
            errors.append(
                "control_skill_contract.forbidden_storage_projection_ids_by_section "
                "must be a non-empty object"
            )
        else:
            for section, rule_ids in forbidden_bindings.items():
                if section not in control_headings:
                    errors.append(
                        "control_skill_contract."
                        "forbidden_storage_projection_ids_by_section."
                        f"{section} is not an ordered heading"
                    )
                ids = string_list(
                    rule_ids,
                    "control_skill_contract."
                    "forbidden_storage_projection_ids_by_section."
                    f"{section}",
                )
                bind_projection_ids(
                    declared_forbidden_storage_targets,
                    ids,
                    f"control-skill:{section}",
                )

    docs_projection_ids: set[str] = set()
    docs_contract = data["docs_contract"]
    if exact_keys(
        docs_contract,
        {
            "schema_version",
            "required_contracts",
            "projections",
            "context_budget_projections",
        },
        "docs_contract",
    ):
        assert isinstance(docs_contract, dict)
        if docs_contract["schema_version"] != 1:
            errors.append("docs_contract.schema_version must be 1")
        required_docs_contracts = string_list(
            docs_contract["required_contracts"],
            "docs_contract.required_contracts",
        )
        expected_docs_contracts = [
            "task_contract",
            "visible_evidence_contract",
            "completion_state",
        ]
        if required_docs_contracts != expected_docs_contracts:
            errors.append(
                "docs_contract.required_contracts must exactly bind Task, Evidence, "
                "and Completion contracts"
            )
        projections = docs_contract["projections"]
        if not isinstance(projections, list) or not projections:
            errors.append("docs_contract.projections must be a non-empty list")
            projections = []
        projection_paths: list[str] = []
        for index, projection in enumerate(projections):
            context = f"docs_contract.projections[{index}]"
            if not exact_keys(
                projection,
                {
                    "id",
                    "path",
                    "section",
                    "bindings",
                    "required_terms",
                },
                context,
            ):
                continue
            assert isinstance(projection, dict)
            identifier = projection["id"]
            if not isinstance(identifier, str) or re.fullmatch(
                r"[a-z0-9]+(?:-[a-z0-9]+)*", identifier
            ) is None:
                errors.append(f"{context}.id must be kebab-case")
            elif identifier in docs_projection_ids:
                errors.append("docs_contract projection ids must be unique")
            else:
                docs_projection_ids.add(identifier)
            path = projection["path"]
            pure_path = PurePosixPath(path) if isinstance(path, str) else None
            if (
                pure_path is None
                or pure_path.is_absolute()
                or ".." in pure_path.parts
                or len(pure_path.parts) < 2
                or pure_path.parts[0] != "docs"
                or pure_path.suffix != ".md"
            ):
                errors.append(f"{context}.path must name repository docs Markdown")
            else:
                projection_paths.append(path)
            if projection["section"] != "Core Contract Projection":
                errors.append(
                    f"{context}.section must be 'Core Contract Projection'"
                )
            required_terms = string_list(
                projection["required_terms"], f"{context}.required_terms"
            )
            bindings = projection["bindings"]
            if not isinstance(bindings, list) or not bindings:
                errors.append(f"{context}.bindings must be a non-empty list")
                bindings = []
            bound_contracts: set[str] = set()
            seen_bindings: set[tuple[str, str]] = set()
            for binding_index, binding in enumerate(bindings):
                binding_context = f"{context}.bindings[{binding_index}]"
                if not exact_keys(
                    binding, {"source_path", "render"}, binding_context
                ):
                    continue
                assert isinstance(binding, dict)
                source_path = binding["source_path"]
                renderer = binding["render"]
                if not isinstance(source_path, str) or not source_path:
                    errors.append(f"{binding_context}.source_path must be non-empty")
                    continue
                root_contract = source_path.split(".", 1)[0]
                bound_contracts.add(root_contract)
                if root_contract not in required_docs_contracts:
                    errors.append(
                        f"{binding_context}.source_path is outside required contracts"
                    )
                if renderer not in DOC_PROJECTION_RENDERERS:
                    errors.append(f"{binding_context}.render is invalid")
                binding_key = (source_path, str(renderer))
                if binding_key in seen_bindings:
                    errors.append(f"{context}.bindings must not contain duplicates")
                seen_bindings.add(binding_key)
            if bound_contracts != set(required_docs_contracts):
                errors.append(
                    f"{context}.bindings must cover exactly "
                    f"{sorted(required_docs_contracts)}"
                )
            if required_terms and bindings:
                try:
                    docs_projection_terms(data, projection)
                    docs_projection_block(data, projection)
                except ValueError as exc:
                    errors.append(f"{context}: {exc}")
        if len(projection_paths) != len(set(projection_paths)):
            errors.append("docs_contract projection paths must be unique")
        if docs_projection_ids != EXPECTED_DOC_PROJECTION_IDS:
            errors.append(
                "docs_contract projection ids must exactly match the managed projection set: "
                f"{sorted(EXPECTED_DOC_PROJECTION_IDS)}"
            )
        budget_projection_ids: set[str] = set()
        budget_projection_paths: list[str] = []
        budget_projections = docs_contract["context_budget_projections"]
        if not isinstance(budget_projections, list) or not budget_projections:
            errors.append(
                "docs_contract.context_budget_projections must be a non-empty list"
            )
            budget_projections = []
        for index, projection in enumerate(budget_projections):
            context = f"docs_contract.context_budget_projections[{index}]"
            if not exact_keys(
                projection,
                {"id", "path", "section", "source_path"},
                context,
            ):
                continue
            assert isinstance(projection, dict)
            identifier = projection["id"]
            if not isinstance(identifier, str) or re.fullmatch(
                r"[a-z0-9]+(?:-[a-z0-9]+)*", identifier
            ) is None:
                errors.append(f"{context}.id must be kebab-case")
            elif identifier in budget_projection_ids:
                errors.append("context budget docs projection ids must be unique")
            else:
                budget_projection_ids.add(identifier)
            path = projection["path"]
            if path not in {"docs/VALIDATION.md", "docs/BENCHMARKS.md"}:
                errors.append(
                    f"{context}.path must name VALIDATION.md or BENCHMARKS.md"
                )
            else:
                budget_projection_paths.append(path)
            if projection["section"] != "Rendered Context Budget Contract":
                errors.append(
                    f"{context}.section must be 'Rendered Context Budget Contract'"
                )
            if projection["source_path"] != "context_budget_contract":
                errors.append(
                    f"{context}.source_path must bind context_budget_contract"
                )
            try:
                context_budget_docs_projection_block(data, projection)
            except (KeyError, TypeError, ValueError) as exc:
                errors.append(f"{context}: cannot render context budget projection: {exc}")
        if len(budget_projection_paths) != len(set(budget_projection_paths)):
            errors.append("context budget docs projection paths must be unique")
        if budget_projection_ids != EXPECTED_CONTEXT_BUDGET_DOC_PROJECTION_IDS:
            errors.append(
                "context budget docs projection ids must exactly match the managed set: "
                f"{sorted(EXPECTED_CONTEXT_BUDGET_DOC_PROJECTION_IDS)}"
            )

    for label, declared, required in (
        (
            "freshness",
            declared_freshness_targets,
            freshness_rule_targets,
        ),
        (
            "forbidden storage",
            declared_forbidden_storage_targets,
            forbidden_storage_rule_targets,
        ),
    ):
        all_rule_ids = set(declared) | set(required)
        for rule_id in sorted(all_rule_ids):
            declared_targets = declared.get(rule_id, set())
            required_targets = required.get(rule_id, set())
            if declared_targets != required_targets:
                errors.append(
                    f"Evidence Ledger {label} rule {rule_id!r} projection targets "
                    f"must be consumed exactly: declared {sorted(required_targets)}, "
                    f"bound {sorted(declared_targets)}"
                )

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
EXECUTION_LEVEL_MODEL = CORE_CONTRACTS["execution_level_contract"]
TASK_CONTRACT_MODEL = CORE_CONTRACTS["task_contract"]
EVIDENCE_RESOLUTION_MODEL = TASK_CONTRACT_MODEL["evidence_resolution"]
DIRECT_BOUNDED_DISCOVERY_MODEL = TASK_CONTRACT_MODEL[
    "direct_bounded_discovery"
]
EVIDENCE_LEDGER_MODEL = CORE_CONTRACTS["visible_evidence_contract"]
COMPLETION_STATE_MODEL = CORE_CONTRACTS["completion_state"]
ROLE_CONTRACT_MODEL = CORE_CONTRACTS["roles"]
IMPLEMENTATION_DISCIPLINE_MODEL = CORE_CONTRACTS[
    "implementation_discipline_contract"
]
REVIEW_DISCIPLINE_MODEL = CORE_CONTRACTS["review_discipline_contract"]
EVIDENCE_LOCALIZATION_MODEL = CORE_CONTRACTS["evidence_localization_contract"]


def normalized_decision_capabilities(entry: dict[str, Any]) -> dict[str, str]:
    """Project one host declaration to the Core generic capability ceilings."""

    supported_enforcement = {
        "native-enforced",
        "sandbox-enforced",
        "prompt-enforced",
    }
    profile_supported = entry.get("profile_delivery") in supported_enforcement
    roles = entry.get("roles")
    roles = roles if isinstance(roles, dict) else {}

    def rendered_tools(role: str) -> set[str]:
        role_facts = roles.get(role)
        tools = role_facts.get("rendered_tools") if isinstance(role_facts, dict) else None
        return set(tools) if isinstance(tools, list) else set()

    diff_input_mode = entry.get("diff_input_mode")
    native_change_read = profile_supported and diff_input_mode == "native"
    change_evidence_export = profile_supported and bool(
        rendered_tools("task-agent") & {"execute", "Bash"}
    )
    supplied_change_delivery = (
        profile_supported and diff_input_mode == "supplied-artifact"
    )
    reviewer_change_consume = profile_supported and bool(
        rendered_tools("review-agent")
        & {"read", "Read", "search", "Grep", "Glob", "execute-read-only"}
    )
    validation_supported = entry.get("validation_mode") in {
        "native-read-only",
        "task-no-edit",
    }
    observation_supported = entry.get("utility_no_edit") in supported_enforcement
    return {
        "bounded-source-read": "supported" if profile_supported else "unsupported",
        "workspace-mutation": "supported" if profile_supported else "unsupported",
        "non-mutating-validation": (
            "supported" if validation_supported else "unsupported"
        ),
        "native-change-read": "supported" if native_change_read else "unsupported",
        "change-evidence-export": (
            "supported" if change_evidence_export else "unsupported"
        ),
        "supplied-change-delivery": (
            "supported" if supplied_change_delivery else "unsupported"
        ),
        "reviewer-change-consume": (
            "supported" if reviewer_change_consume else "unsupported"
        ),
        "workspace-state-observation": (
            "supported" if observation_supported else "unsupported"
        ),
    }


def _current_handoff_selected_capabilities(
    handoff: dict[str, Any] | None,
    facts: dict[str, str],
    authority: dict[str, Any],
) -> tuple[str, ...] | None:
    """Return the selected evidence path only for a current complete handoff."""

    if not isinstance(handoff, dict):
        return None
    try:
        readiness = authority["review_discipline_contract"][
            "review_input_readiness"
        ]
        required_fields = tuple(readiness["required_fields"])
        exact_kinds = set(readiness["exact_change_evidence_kinds"])
    except (KeyError, TypeError):
        return None
    if any(field not in handoff for field in required_fields):
        return None
    latest = handoff.get("latest_changed_paths")
    fixed = handoff.get("fixed_review_scope")
    evidence = handoff.get("exact_change_evidence")
    access = handoff.get("reviewer_capability_accessibility")
    validation = handoff.get("validation_after_latest_material_edit")
    if (
        not isinstance(latest, list)
        or not latest
        or not all(isinstance(path, str) and path for path in latest)
        or fixed != latest
        or not isinstance(evidence, dict)
        or evidence.get("kind") not in exact_kinds
        or type(evidence.get("generation")) is not int
        or not isinstance(access, dict)
        or not isinstance(validation, dict)
        or validation.get("result") != "passed"
        or validation.get("generation") != evidence["generation"]
    ):
        return None
    kind = evidence["kind"]
    artifact = evidence.get("artifact")
    if kind == "reviewer-accessible-native-reference":
        selected = (
            "native-change-read",
            "reviewer-change-consume",
            "non-mutating-validation",
        )
        if (
            not isinstance(artifact, dict)
            or set(readiness.get("native_evidence_fields", [])) - set(artifact)
            or artifact.get("generation") != evidence["generation"]
            or artifact.get("reviewer") != "review-agent"
            or artifact.get("changed_paths") != latest
            or artifact.get("readable") is not True
            or not isinstance(artifact.get("reference"), str)
            or not artifact["reference"].startswith("native-change://")
        ):
            return None
    else:
        selected = (
            "change-evidence-export",
            "supplied-change-delivery",
            "reviewer-change-consume",
            "non-mutating-validation",
        )
        if not isinstance(artifact, str) or not artifact.startswith("diff --git "):
            return None
    if any(
        facts.get(field) != "supported" or access.get(field) != "supported"
        for field in selected
    ):
        return None
    return selected


def main_capability_projection_from_facts(
    facts: dict[str, str],
    *,
    handoff: dict[str, Any] | None = None,
    core: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Derive Main's four current decisions from Core, ceilings, and one handoff."""

    authority = CORE_CONTRACTS if core is None else core
    try:
        contract = authority["review_discipline_contract"][
            "generic_capability_contract"
        ]
    except (KeyError, TypeError) as exc:
        raise ValueError("Core capability projection authority is incomplete") from exc
    required = {
        "native-change-read",
        "change-evidence-export",
        "supplied-change-delivery",
        "reviewer-change-consume",
        "non-mutating-validation",
    }
    if not required <= set(contract.get("injected_fields", [])):
        raise ValueError("Core capability projection fields are incomplete")
    selected = None
    if all(facts.get(field) in {"supported", "unsupported"} for field in required):
        selected = _current_handoff_selected_capabilities(
            handoff, facts, authority
        )
    ready = selected is not None
    return {
        "exact-change-evidence-read": "supported" if ready else "unsupported",
        "reviewer-accessible-change-reference": (
            "supported" if ready else "unsupported"
        ),
        "non-mutating-validation": facts.get(
            "non-mutating-validation", "unsupported"
        ),
        "not-required": "supported" if ready else "unsupported",
    }


def main_capability_projection(
    entry: dict[str, Any],
    *,
    handoff: dict[str, Any] | None = None,
    core: dict[str, Any] | None = None,
) -> dict[str, str]:
    return main_capability_projection_from_facts(
        normalized_decision_capabilities(entry), handoff=handoff, core=core
    )


def render_decision_capability_facts(capabilities: dict[str, str]) -> str:
    authority = REVIEW_DISCIPLINE_MODEL["generic_capability_contract"]
    ceiling_fields = tuple(authority["injected_fields"])
    main_fields = (
        "exact-change-evidence-read",
        "reviewer-accessible-change-reference",
        "non-mutating-validation",
        "not-required",
    )
    if tuple(capabilities) == ceiling_fields:
        capabilities = main_capability_projection_from_facts(capabilities)
    if tuple(capabilities) != main_fields:
        raise ValueError("decision capability projection has unexpected fields")
    groups = {
        state: [field for field in main_fields if capabilities[field] == state]
        for state in authority["states"]
    }
    return (
        "Current capability facts: supported "
        + ("/".join(groups["supported"]) or "none")
        + "; unsupported "
        + ("/".join(groups["unsupported"]) or "none")
        + "."
    )
CONTEXT_BUDGET_MODEL = CORE_CONTRACTS["context_budget_contract"]
PROMPT_CONTRACT_MODEL = CORE_CONTRACTS["prompt_contract"]
PROFILE_CONTRACT_MODEL = CORE_CONTRACTS["profile_contract"]
CONTROL_SKILL_CONTRACT_MODEL = CORE_CONTRACTS["control_skill_contract"]
DOCS_CONTRACT_MODEL = CORE_CONTRACTS["docs_contract"]


def execution_level_role_projection(
    extension: dict[str, object], *, role: str
) -> dict[str, object]:
    """Project Main's complete Level decision to one non-calculating worker role."""

    if role not in {"task-agent", "review-agent"}:
        raise ExecutionLevelError(
            "execution Level role projection is only for Task and Review"
        )
    if not isinstance(extension, dict):
        raise ExecutionLevelError("execution Level extension must be an object")
    level = extension.get("effective_level")
    levels = {
        row["id"]: row
        for row in EXECUTION_LEVEL_MODEL["levels"]
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    }
    if level not in levels:
        raise ExecutionLevelError("execution Level projection has unknown effective level")
    basis = extension.get("level_basis")
    fallback = (
        extension.get("integrity_status") == "blocked"
        and extension.get("edit_status") == "blocked"
        and "implementation" in extension.get("forbidden_actions", [])
    )
    if not isinstance(basis, dict) and not fallback:
        raise ExecutionLevelError("execution Level projection has no complete basis")
    obligations = basis.get("obligations") if isinstance(basis, dict) else [
        *levels[level]["obligations"],
        *EXECUTION_LEVEL_MODEL["non_bypassable"],
    ]
    if not isinstance(obligations, list) or any(
        not isinstance(value, str) or not value for value in obligations
    ):
        raise ExecutionLevelError("execution Level projection obligations are invalid")
    edit_status = (
        basis.get("edit_status")
        if isinstance(basis, dict)
        else extension.get("edit_status")
    )
    if not isinstance(edit_status, str) or not edit_status:
        raise ExecutionLevelError("execution Level projection edit status is invalid")
    payload = json.dumps(
        extension, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    common = {
        "version": EXECUTION_LEVEL_MODEL["schema_version"],
        "effective_level": level,
        "source_sha256": hashlib.sha256(payload).hexdigest(),
    }
    if role == "task-agent":
        return {
            **common,
            "edit_status": edit_status,
            "current_obligations": list(obligations),
        }

    review_obligations: list[str] = []
    for value in [
        *levels[level]["obligations"],
        *(
            item
            for item in EXECUTION_LEVEL_MODEL["non_bypassable"]
            if "review" in item or "evidence" in item
        ),
    ]:
        if value in obligations and value not in review_obligations:
            review_obligations.append(value)
    return {
        **common,
        "review_depth": levels[level]["rank"],
        "assurance_obligations": review_obligations,
    }


def evidence_resolution_authority(data: object) -> dict[str, Any]:
    """Return the source-owned intake-semantics projection for routing evals."""

    if not isinstance(data, dict):
        raise ValueError("Evidence Resolution authority source must be an object")
    task = data.get("task_contract")
    candidate = task.get("evidence_resolution") if isinstance(task, dict) else None
    if not isinstance(candidate, dict):
        raise ValueError("Evidence Resolution authority is missing")
    canonical = EVIDENCE_RESOLUTION_MODEL
    if candidate != canonical:
        raise ValueError(
            "Evidence Resolution authority must match the current Core projection"
        )
    return copy.deepcopy(candidate)


def resolve_evidence_gap(
    gap_class: str,
    *,
    route_affecting_surfaces: Iterable[str] = (),
    choice_kind: str | None = None,
) -> dict[str, object]:
    """Evaluate one gap without performing routing or repository discovery."""

    authority = EVIDENCE_RESOLUTION_MODEL
    classes = {row["id"]: row for row in authority["gap_classes"]}
    if gap_class not in classes:
        raise ValueError(f"unknown Evidence Resolution gap class {gap_class!r}")
    gap = classes[gap_class]
    supplied_surfaces = list(route_affecting_surfaces)
    if len(supplied_surfaces) != len(set(supplied_surfaces)):
        raise ValueError("route-affecting surfaces must be unique")
    unknown_surfaces = sorted(
        set(supplied_surfaces) - set(authority["route_affecting_surfaces"])
    )
    if unknown_surfaces:
        raise ValueError(f"unknown route-affecting surfaces {unknown_surfaces}")
    base: dict[str, object] = {
        "gap_class": gap_class,
        "path": None,
        "resolution": "unresolved",
        "action_authority": "block",
        "question_count": 0,
        "invalidation": "none",
        "semantic_route_change": False,
    }
    if gap["subtypes"]:
        if supplied_surfaces:
            raise ValueError("user-owned choice cannot carry fact projections")
        if choice_kind not in gap["subtypes"]:
            raise ValueError("user-owned choice requires one declared choice kind")
        rule = authority["decision_rules"][choice_kind]
        base.update(
            {
                "resolution": "ask-user",
                "action_authority": "ask",
                "question_count": authority["maximum_user_questions"],
                "invalidation": rule["invalidation"],
                "semantic_route_change": (
                    rule["invalidation"] != "execution-level-projection-only"
                ),
            }
        )
        return base

    rule = authority["decision_rules"][gap_class]
    if "route_affecting" in rule:
        if choice_kind is not None:
            raise ValueError("source-resolvable fact cannot name a choice kind")
        analyzed_path = rule["route_affecting"]
        direct_paths = [
            path for path in authority["path_values"] if path != analyzed_path
        ]
        if len(direct_paths) != 1:
            raise ValueError("Evidence Resolution fact projection lacks one Direct path")
        base.update(
            {
                "path": analyzed_path if supplied_surfaces else direct_paths[0],
                "resolution": (
                    "analysis" if supplied_surfaces else rule["otherwise"]
                ),
                "action_authority": "execute",
            }
        )
        return base
    if choice_kind is not None or supplied_surfaces:
        raise ValueError(
            "material unknown cannot carry fact or choice projections"
        )
    analyzed_paths = [path for path in authority["path_values"] if path != "direct"]
    if len(analyzed_paths) != 1 or "decision" not in rule:
        raise ValueError("Evidence Resolution unknown projection is incomplete")
    base.update(
        {
            "path": analyzed_paths[0],
            "resolution": rule["decision"],
            "action_authority": "block",
        }
    )
    return base


REFERENCE_CONTEXT_ADMISSIBILITY_CONTRACT = (
    "changeforge.reference-context-admissibility/v3"
)
_REFERENCE_CONTEXT_DECLARATION_FIELDS = {
    "gap_class",
    "route_affecting_surfaces",
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
    "receipt_sha256",
}


def _reference_context_carrier_authority() -> dict[str, set[str]]:
    brief_fields = set(
        TASK_CONTRACT_MODEL["analyzed_work_authority"]["decision_ownership"][
            "engineering_brief"
        ]
    )
    brief_fields.update({"Layer3"})
    review_schema = TASK_CONTRACT_MODEL["template_schemas"][
        "review-handoff-template.md"
    ]
    review_projection = set(
        review_schema["labeled_sections"]["Inbound Review Projection"]
    )
    review_boundary = set(
        review_schema["labeled_sections"]["Review Boundary"]
    )
    return {
        "selector-receipt": set(_REFERENCE_CONTEXT_RECEIPT_FIELDS),
        "engineering-brief": brief_fields,
        "task-contract": set(TASK_CONTRACT_MODEL["fields"]),
        "implementation-handoff": {
            heading
            for level, heading in TASK_CONTRACT_MODEL["template_schemas"][
                "implementation-handoff-template.md"
            ]["headings"]
            if level == 2
        },
        "review-handoff.Inbound Review Projection": review_projection,
        "review-handoff.Review Boundary": review_boundary,
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
                    gap_class = raw_rule["gap_class"]
                    surfaces = raw_rule["route_affecting_surfaces"]
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
                    if not isinstance(gap_class, str):
                        raise ValidationProblem(
                            f"{rule_context}.gap_class must be an Evidence class id"
                        )
                    if gap_class == "user-owned-choice":
                        raise ValidationProblem(
                            f"{rule_context} cannot project a user-owned choice"
                        )
                    if (
                        not isinstance(surfaces, list)
                        or any(
                            not isinstance(surface, str) or not surface
                            for surface in surfaces
                        )
                        or len(surfaces) != len(set(surfaces))
                    ):
                        raise ValidationProblem(
                            f"{rule_context}.route_affecting_surfaces must be a "
                            "unique string list"
                        )
                    unknown_surfaces = sorted(
                        set(surfaces)
                        - set(EVIDENCE_RESOLUTION_MODEL["route_affecting_surfaces"])
                    )
                    if unknown_surfaces:
                        raise ValidationProblem(
                            f"{rule_context} has unknown route-affecting surfaces "
                            f"{unknown_surfaces}"
                        )
                    try:
                        if gap_class == "route-or-material-unknown":
                            if not surfaces:
                                raise ValidationProblem(
                                    f"{rule_context} material unknown must name "
                                    "affected surfaces"
                                )
                            resolution = resolve_evidence_gap(gap_class)
                        else:
                            resolution = resolve_evidence_gap(
                                gap_class,
                                route_affecting_surfaces=surfaces,
                            )
                    except ValueError as exc:
                        raise ValidationProblem(
                            f"{rule_context} cannot resolve declared Evidence: {exc}"
                        ) from exc
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
                        "gap_class": gap_class,
                        "route_affecting_surfaces": list(surfaces),
                        "conflicts_with": list(conflicts),
                        "decision_problem": decision_problem,
                        "sequenced_after": copy.deepcopy(sequenced_after),
                        "must_co_trigger_with": list(must_co_trigger),
                        "resolution": resolution,
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
            "receipt_sha256",
        )
    ]
    brief_fields = [
        "engineering-brief.Owner",
        "engineering-brief.Scope",
        "engineering-brief.Professional Skill",
        "engineering-brief.Layer3",
    ]
    expected_carriers = {
        "task-agent": {
            "engineering-brief": [*receipt_fields, *brief_fields],
        },
        "review-agent": {
            "engineering-brief": [
                *receipt_fields,
                *brief_fields,
                "review-handoff.Inbound Review Projection.Review Boundary",
                "review-handoff.Inbound Review Projection.Required Changed Scope",
                "review-handoff.Inbound Review Projection.Scope",
                "review-handoff.Inbound Review Projection.Freshness",
                "review-handoff.Inbound Review Projection.Proof Limit",
            ],
        },
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
        "gap_class_ids": [
            row["id"] for row in EVIDENCE_RESOLUTION_MODEL["gap_classes"]
        ],
        "route_affecting_surfaces": list(
            EVIDENCE_RESOLUTION_MODEL["route_affecting_surfaces"]
        ),
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
    paths = EVIDENCE_RESOLUTION_MODEL["path_values"]
    if path not in paths:
        raise ValidationProblem(f"unknown composition path {path!r}")
    rows = list(references)
    if len(rows) != len(set(rows)):
        raise ValidationProblem("composition References must be unique")
    declarations: list[dict[str, object]] = []
    undeclared: list[tuple[str, str]] = []
    selected_by_owner: dict[str, set[str]] = {}
    minimum_path = "direct"
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
        resolution = rule["resolution"]
        assert isinstance(resolution, dict)
        if resolution["path"] == "analyzed":
            minimum_path = "analyzed"
        declarations.append(
            {
                "owner": owner,
                "path": reference_path,
                "gap_class": rule["gap_class"],
                "route_affecting_surfaces": list(
                    rule["route_affecting_surfaces"]
                ),
                "resolution": resolution["resolution"],
                "action_authority": resolution["action_authority"],
            }
        )

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
    path_blocked = path == "direct" and minimum_path == "analyzed"
    return {
        "path": path,
        "minimum_path": minimum_path,
        "reachable": not path_blocked and not conflicts,
        "failure_id": (
            "context-reference-conflict"
            if conflicts
            else "context-reference-requires-analysis"
            if path_blocked
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


def direct_bounded_discovery_outcome(
    outcome: str,
    *,
    risk_change: str = "same",
) -> dict[str, object]:
    """Project a worker's bounded discovery result without granting reroute authority."""

    if outcome not in DIRECT_BOUNDED_DISCOVERY_MODEL["outcomes"]:
        raise ValueError(f"unknown Direct discovery outcome {outcome!r}")
    if risk_change not in {"same", "simpler", "higher"}:
        raise ValueError(f"unknown Direct discovery risk change {risk_change!r}")
    if outcome == "boundary-confirmed" and risk_change == "higher":
        raise ValueError("higher risk invalidates the Direct discovery boundary")
    if outcome == "boundary-confirmed":
        return {
            "worker_action": "confirm-and-continue",
            "may_edit": True,
            "return_to_main": False,
            "question_count": 0,
            "level_action": "preserve-current",
            "route_authority": "current-route-only",
        }
    if outcome == "route-or-risk-invalidated":
        return {
            "worker_action": "return-main-for-analysis",
            "may_edit": False,
            "return_to_main": True,
            "question_count": 0,
            "level_action": "recompute" if risk_change == "higher" else "preserve-current",
            "route_authority": "worker-reroute-forbidden",
        }
    return {
        "worker_action": "return-main-for-one-question",
        "may_edit": False,
        "return_to_main": True,
        "question_count": EVIDENCE_RESOLUTION_MODEL["maximum_user_questions"],
        "level_action": "preserve-current",
        "route_authority": "worker-reroute-forbidden",
    }


def validate_main_execution(
    main_execution: object,
    *,
    route_contract: dict[str, object] | None = None,
    execution_contract: dict[str, object] | None = None,
) -> list[str]:
    """Validate Main-owned routing input without routing or computing a level."""

    route_model = (
        ROUTE_DECISION_MODEL if route_contract is None else route_contract
    )
    execution_model = (
        EXECUTION_LEVEL_MODEL
        if execution_contract is None
        else execution_contract
    )
    errors: list[str] = []
    expected_fields = route_model["main_execution_provenance_fields"]
    if not isinstance(main_execution, dict):
        return ["main execution input must be an object"]
    if set(main_execution) != set(expected_fields):
        return [
            "main execution input fields must be exactly "
            f"{expected_fields}, found "
            f"{sorted(str(field) for field in main_execution)}"
        ]
    if main_execution["producer"] != route_model["main_execution_producer"]:
        errors.append("main execution input producer must be main-control-agent")
    task_id = main_execution["task_id"]
    if not isinstance(task_id, str) or not task_id.strip():
        errors.append("main execution input task_id must be non-empty text")
    known_levels = {
        row["id"]
        for row in execution_model["levels"]
        if isinstance(row, dict)
    }
    execution_level = main_execution["execution_level"]
    if (
        not isinstance(execution_level, str)
        or execution_level not in known_levels
    ):
        errors.append("main execution input.execution_level must be a known level")
    level_basis = main_execution["level_basis"]
    expected_basis_fields = set(execution_model["level_basis_fields"])
    legacy_v1_basis_fields = {
        "trigger_evaluations",
        "l2_eligibility",
        "obligations",
        "unresolved",
        "edit_status",
    }
    if (
        isinstance(level_basis, dict)
        and execution_model.get("schema_version") == 2
        and set(level_basis) == legacy_v1_basis_fields
    ):
        errors.append(
            "active Main execution-level/v1 requires v2 reissue before routing"
        )
    elif (
        not isinstance(level_basis, dict)
        or set(level_basis) != expected_basis_fields
    ):
        errors.append(
            "main execution input.level_basis fields must be exactly "
            f"{sorted(expected_basis_fields)}"
        )
    try:
        _canonical_execution_level_json_bytes(
            main_execution,
            "main execution input",
        )
    except (
        RecursionError,
        TypeError,
        ValueError,
        UnicodeError,
        OverflowError,
    ) as exc:
        errors.append(f"main execution input must be canonical JSON: {exc}")
    return errors


def validate_main_assignment(
    main_assignment: object,
    *,
    route_contract: dict[str, object] | None = None,
    execution_contract: dict[str, object] | None = None,
) -> list[str]:
    """Validate a non-executable Analysis assignment or executable Main input."""

    route_model = (
        ROUTE_DECISION_MODEL if route_contract is None else route_contract
    )
    if not isinstance(main_assignment, dict):
        return ["main assignment input must be an object"]
    analysis_fields = set(route_model["main_analysis_assignment_fields"])
    if set(main_assignment) != analysis_fields:
        return validate_main_execution(
            main_assignment,
            route_contract=route_model,
            execution_contract=execution_contract,
        )
    errors: list[str] = []
    if main_assignment.get("producer") != route_model["main_execution_producer"]:
        errors.append("main analysis assignment producer must be main-control-agent")
    task_id = main_assignment.get("task_id")
    if not isinstance(task_id, str) or not task_id.strip():
        errors.append("main analysis assignment task_id must be non-empty text")
    try:
        _canonical_execution_level_json_bytes(
            main_assignment,
            "main analysis assignment",
        )
    except (
        RecursionError,
        TypeError,
        ValueError,
        UnicodeError,
        OverflowError,
    ) as exc:
        errors.append(f"main analysis assignment must be canonical JSON: {exc}")
    return errors


def validate_route_decision(
    envelope: object,
    *,
    main_execution: object,
    routing_authority: object,
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
            return _canonical_execution_level_json_bytes(value, context)
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
            "Analysis has no Execution Level"
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
    if not valid_primary or primary_skill not in known_primary_authority:
        errors.append(
            "route_result.primary_skill must name one known professional "
            "primary authority Skill"
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
    if not valid_review or review_skill not in review_authority:
        errors.append(
            "route_result.review_skill must name one known professional review "
            "authority Skill"
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

    known_levels = {
        row["id"] for row in EXECUTION_LEVEL_MODEL["levels"] if isinstance(row, dict)
    }
    expected_basis_fields = set(EXECUTION_LEVEL_MODEL["level_basis_fields"])
    if analysis_path:
        if result["execution_level"] is not None or result["level_basis"] is not None:
            errors.append(
                "analyzed route must not carry Execution Level or Level Basis"
            )
    else:
        assert provenance is not None
        errors.extend(
            validate_main_execution(
                main_object,
                route_contract=model,
                execution_contract=EXECUTION_LEVEL_MODEL,
            )
        )
        for context, value in (
            ("route_result", result),
            ("main execution provenance", provenance),
            ("main execution input", main_object),
        ):
            execution_level = value["execution_level"]
            if (
                not isinstance(execution_level, str)
                or execution_level not in known_levels
            ):
                errors.append(f"{context}.execution_level must be a known level")
            basis = value["level_basis"]
            if (
                not isinstance(basis, dict)
                or set(basis) != expected_basis_fields
            ):
                errors.append(
                    f"{context}.level_basis fields must be exactly "
                    f"{sorted(expected_basis_fields)}"
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
    if not analysis_path:
        route_basis_json = canonical_json_bytes(
            result["level_basis"],
            "route_result.level_basis",
        )
        main_basis_json = canonical_json_bytes(
            main_object["level_basis"],
            "main execution input.level_basis",
        )
        if (
            result["execution_level"] != main_object["execution_level"]
            or (
                route_basis_json is not None
                and main_basis_json is not None
                and route_basis_json != main_basis_json
            )
        ):
            errors.append(
                "route_result execution_level and level_basis must equal the supplied "
                "Main execution input"
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
        "known professional primary authority Skill",
        required=True,
    )
    review_rows = candidate_rows(
        "review_candidates",
        review_authority,
        "known professional review authority Skill",
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
    if len(eligible_review) != 1 or eligible_review != [review_skill]:
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


class ExecutionLevelError(ValueError):
    """Raised when canonical execution-level evidence is incomplete or invalid."""


def _execution_rank(level: str, contract: dict[str, object] | None = None) -> int:
    model = EXECUTION_LEVEL_MODEL if contract is None else contract
    ranks = {row["id"]: row["rank"] for row in model["levels"]}
    try:
        return ranks[level]
    except KeyError as exc:
        raise ExecutionLevelError(f"unknown execution level {level!r}") from exc


def _max_execution_level(
    *levels: str,
    contract: dict[str, object] | None = None,
) -> str:
    return max(levels, key=lambda level: _execution_rank(level, contract))


def _nonempty_execution_text_mapping(
    value: object,
    fields: list[str],
    *,
    context: str,
) -> dict[str, str]:
    """Validate one closed, non-empty evidence mapping."""

    if not isinstance(value, dict) or list(value) != fields:
        raise ExecutionLevelError(f"{context} fields must be {fields}")
    if any(not isinstance(value[field], str) or not value[field].strip() for field in fields):
        raise ExecutionLevelError(f"{context} fields must be non-empty text")
    return {field: value[field] for field in fields}


def classify_concrete_action_authority(
    facts: object,
    *,
    contract: dict[str, object] | None = None,
) -> dict[str, object]:
    """Classify one concrete action without storing state or granting permission."""

    contract = EXECUTION_LEVEL_MODEL if contract is None else contract
    policy = contract["action_authority"]
    fact_fields = policy["fact_fields"]
    required = [*fact_fields, "authority_state", "material_task_risk_delta"]
    if not isinstance(facts, dict) or list(facts) != required:
        raise ExecutionLevelError(
            f"concrete action authority fields must be {required}"
        )
    _nonempty_execution_text_mapping(
        {field: facts[field] for field in fact_fields},
        fact_fields,
        context="concrete action authority facts",
    )
    state = facts["authority_state"]
    if state not in policy["authority_states"]:
        raise ExecutionLevelError("concrete action authority state is invalid")
    risk_delta = facts["material_task_risk_delta"]
    if not isinstance(risk_delta, bool):
        raise ExecutionLevelError("concrete action material Task risk delta must be boolean")
    if risk_delta:
        return {
            "decision": "block",
            "execution_level_effect": policy["material_risk_delta_outcome"],
            "exact_target": facts["exact_target"],
        }
    return {
        "decision": policy["outcomes"][state],
        "execution_level_effect": "unchanged",
        "exact_target": facts["exact_target"],
    }


def compute_execution_level(
    *,
    requested: str,
    trigger_evaluations: dict[str, dict[str, object]],
    l1_evaluations: dict[str, dict[str, object]] | None = None,
    l2_evaluations: dict[str, dict[str, object]],
    l5_assurance_evaluations: dict[str, dict[str, object]] | None = None,
    l5_confirmation: str = "not-required",
    prior_historical_max_floor: str | None = None,
    prior_historical_max_effective: str | None = None,
    contract: dict[str, object] | None = None,
) -> dict[str, object]:
    """Apply the unique Core execution-level formula to explicit main-agent evidence."""

    contract = EXECUTION_LEVEL_MODEL if contract is None else contract
    formula = contract["formula"]
    if prior_historical_max_floor is None:
        prior_historical_max_floor = formula["computed_floor_seed"]
    if prior_historical_max_effective is None:
        prior_historical_max_effective = formula["computed_floor_seed"]
    if requested not in contract["requested_values"]:
        raise ExecutionLevelError(f"requested level {requested!r} is not allowed")
    if (
        formula["trigger_aggregation"] != "max"
        or formula["l1_requirement"] != "all_true_and_l2_true"
        or formula["l2_requirement"] != "all_true"
    ):
        raise ExecutionLevelError("unsupported execution trigger or L2 operator")
    _execution_rank(prior_historical_max_floor, contract)
    _execution_rank(prior_historical_max_effective, contract)
    evidence_kinds = set(contract["main_evidence_kinds"])
    registry = {row["id"]: row for row in contract["trigger_registry"]}
    if set(trigger_evaluations) != set(registry):
        unknown = sorted(set(trigger_evaluations) - set(registry))
        missing = sorted(set(registry) - set(trigger_evaluations))
        raise ExecutionLevelError(
            f"trigger evaluations must cover the closed registry; unknown={unknown}, missing={missing}"
        )
    confirmed_matched_floors = [formula["computed_floor_seed"]]
    unresolved: list[str] = []
    critical_unknown = False
    material_candidate_statuses = set(contract["material_candidate_statuses"])
    material_candidate_evaluations: dict[str, dict[str, object]] = {}
    canonical_triggers: list[dict[str, object]] = []
    for identifier, row in registry.items():
        evaluation = trigger_evaluations[identifier]
        base_fields = {"status", "evidence_kind", "source_anchor", "plausible_critical"}
        optional_fields = {"material_assessment", "critical_unknown"}
        if (
            not isinstance(evaluation, dict)
            or not base_fields <= set(evaluation)
            or set(evaluation) - base_fields - optional_fields
        ):
            raise ExecutionLevelError(
                f"trigger {identifier!r} evaluation fields must contain {sorted(base_fields)} with only conditional material assessment or critical unknown evidence"
            )
        status = evaluation["status"]
        material_candidate = (
            row["floor"] == "L4"
            and identifier
            not in {"formal-release-declared", "unknown-critical-boundary"}
        )
        allowed_statuses = (
            material_candidate_statuses
            if material_candidate
            else {"matched", "not_matched", "unknown"}
        )
        if status not in allowed_statuses:
            raise ExecutionLevelError(f"trigger {identifier!r} has invalid status {status!r}")
        if evaluation["evidence_kind"] not in evidence_kinds:
            raise ExecutionLevelError(f"trigger {identifier!r} uses invalid evidence kind")
        if not isinstance(evaluation["source_anchor"], str) or not evaluation[
            "source_anchor"
        ].strip():
            raise ExecutionLevelError(f"trigger {identifier!r} needs a source anchor")
        if not isinstance(evaluation["plausible_critical"], bool):
            raise ExecutionLevelError(
                f"trigger {identifier!r} plausible_critical must be boolean"
            )
        if status != "unknown" and evaluation["plausible_critical"]:
            raise ExecutionLevelError(
                f"trigger {identifier!r} plausible_critical is valid only for unknown status"
            )
        if identifier == "unknown-critical-boundary" and status == "matched":
            raise ExecutionLevelError(
                "unknown-critical-boundary must be unknown with concrete critical evidence, never a confirmed match"
            )
        if (
            identifier == "unknown-critical-boundary"
            and status == "unknown"
            and evaluation["plausible_critical"] is not True
        ):
            raise ExecutionLevelError(
                "unknown-critical-boundary unknown status requires concrete critical evidence"
            )
        material_assessment = evaluation.get("material_assessment")
        critical_evidence = evaluation.get("critical_unknown")
        requires_material_assessment = material_candidate and status in {
            "matched",
            "non_material",
            "unknown",
        }
        if requires_material_assessment:
            _nonempty_execution_text_mapping(
                material_assessment,
                contract["material_assessment_fields"],
                context=f"trigger {identifier!r} material assessment",
            )
        elif material_assessment is not None:
            raise ExecutionLevelError(
                f"trigger {identifier!r} material assessment is valid only for an applicable material L4 predicate"
            )
        if material_candidate:
            material_candidate_evaluations[identifier] = evaluation
        if evaluation["plausible_critical"]:
            if identifier != "unknown-critical-boundary":
                raise ExecutionLevelError(
                    "plausible critical evidence must use unknown-critical-boundary"
                )
            critical_mapping = _nonempty_execution_text_mapping(
                critical_evidence,
                contract["critical_unknown_fields"],
                context="critical unknown",
            )
            candidate = critical_mapping["candidate_l4_predicate"]
            candidate_row = registry.get(candidate)
            if (
                not isinstance(candidate_row, dict)
                or candidate_row.get("floor") != "L4"
                or candidate in {"formal-release-declared", "unknown-critical-boundary"}
            ):
                raise ExecutionLevelError(
                    "critical unknown candidate_l4_predicate must name a material L4 predicate"
                )
            candidate_evaluation = material_candidate_evaluations.get(candidate)
            if (
                not isinstance(candidate_evaluation, dict)
                or candidate_evaluation.get("status") != "unknown"
            ):
                raise ExecutionLevelError(
                    "critical unknown must reference a material L4 candidate with status=unknown"
                )
        elif critical_evidence is not None:
            raise ExecutionLevelError(
                f"trigger {identifier!r} critical unknown evidence requires plausible_critical=true"
            )
        if status == "matched":
            confirmed_matched_floors.append(row["floor"])
        elif status == "unknown":
            unresolved.append(identifier)
            if evaluation["plausible_critical"]:
                critical_unknown = True
        canonical_triggers.append({"id": identifier, **evaluation})
    confirmed_computed_floor = _max_execution_level(
        *confirmed_matched_floors,
        contract=contract,
    )
    computed_floor = (
        _max_execution_level(
            confirmed_computed_floor,
            contract["critical_unknown"]["floor"],
            contract=contract,
        )
        if critical_unknown
        else confirmed_computed_floor
    )

    l2_registry = {row["id"]: row for row in contract["l2_eligibility"]}
    if set(l2_evaluations) != set(l2_registry):
        unknown = sorted(set(l2_evaluations) - set(l2_registry))
        missing = sorted(set(l2_registry) - set(l2_evaluations))
        raise ExecutionLevelError(
            f"L2 evaluations must cover the closed registry; unknown={unknown}, missing={missing}"
        )
    all_l2_true = True
    canonical_l2: list[dict[str, object]] = []
    for identifier in l2_registry:
        evaluation = l2_evaluations[identifier]
        expected_fields = {"status", "evidence_kind", "source_anchor"}
        if not isinstance(evaluation, dict) or set(evaluation) != expected_fields:
            raise ExecutionLevelError(
                f"L2 predicate {identifier!r} fields must be {sorted(expected_fields)}"
            )
        status = evaluation["status"]
        if status not in {"true", "false", "unknown"}:
            raise ExecutionLevelError(
                f"L2 predicate {identifier!r} has invalid status {status!r}"
            )
        if evaluation["evidence_kind"] not in evidence_kinds:
            raise ExecutionLevelError(f"L2 predicate {identifier!r} uses invalid evidence kind")
        if not isinstance(evaluation["source_anchor"], str) or not evaluation[
            "source_anchor"
        ].strip():
            raise ExecutionLevelError(f"L2 predicate {identifier!r} needs a source anchor")
        if status != "true":
            all_l2_true = False
        if status == "unknown":
            unresolved.append(identifier)
        canonical_l2.append({"id": identifier, **evaluation})

    def canonical_eligibility(
        registry_field: str,
        evaluations: dict[str, dict[str, object]] | None,
        *,
        compatibility_status: str,
    ) -> tuple[bool, list[dict[str, object]], dict[str, dict[str, object]]]:
        eligibility_registry = {
            row["id"]: row for row in contract[registry_field]
        }
        if evaluations is None:
            evaluations = {
                identifier: {
                    "status": compatibility_status,
                    "evidence_kind": "user_fact",
                    "source_anchor": f"legacy-v1:{identifier}:not-proven",
                }
                for identifier in eligibility_registry
            }
        if set(evaluations) != set(eligibility_registry):
            unknown = sorted(set(evaluations) - set(eligibility_registry))
            missing = sorted(set(eligibility_registry) - set(evaluations))
            raise ExecutionLevelError(
                f"{registry_field} evaluations must cover the closed registry; unknown={unknown}, missing={missing}"
            )
        all_true = True
        canonical: list[dict[str, object]] = []
        for identifier in eligibility_registry:
            evaluation = evaluations[identifier]
            expected_fields = {"status", "evidence_kind", "source_anchor"}
            if not isinstance(evaluation, dict) or set(evaluation) != expected_fields:
                raise ExecutionLevelError(
                    f"{registry_field} predicate {identifier!r} fields must be {sorted(expected_fields)}"
                )
            status = evaluation["status"]
            if status not in {"true", "false", "unknown"}:
                raise ExecutionLevelError(
                    f"{registry_field} predicate {identifier!r} has invalid status {status!r}"
                )
            if evaluation["evidence_kind"] not in evidence_kinds:
                raise ExecutionLevelError(
                    f"{registry_field} predicate {identifier!r} uses invalid evidence kind"
                )
            if (
                not isinstance(evaluation["source_anchor"], str)
                or not evaluation["source_anchor"].strip()
            ):
                raise ExecutionLevelError(
                    f"{registry_field} predicate {identifier!r} needs a source anchor"
                )
            if status != "true":
                all_true = False
            if status == "unknown":
                unresolved.append(identifier)
            canonical.append({"id": identifier, **evaluation})
        return all_true, canonical, evaluations

    all_l1_true, canonical_l1, l1_evaluations = canonical_eligibility(
        "l1_eligibility", l1_evaluations, compatibility_status="false"
    )
    all_l5_true, canonical_l5, l5_assurance_evaluations = canonical_eligibility(
        "l5_assurance_eligibility",
        l5_assurance_evaluations,
        compatibility_status="false",
    )

    no_material = l2_evaluations["no-material-high-risk-residual-impact"]
    if no_material["status"] == "true" and any(
        evaluation["status"] in {"matched", "unknown"}
        for evaluation in material_candidate_evaluations.values()
    ):
        raise ExecutionLevelError(
            "no-material-high-risk-residual-impact cannot be true while a material L4 candidate is matched or unknown"
        )

    l1_eligible = all_l1_true and all_l2_true
    if l1_eligible:
        eligibility_base = "L1"
    elif all_l2_true:
        eligibility_base = formula["automatic_l2_level"]
    else:
        eligibility_base = formula["automatic_default_level"]
    minimum_eligible = _max_execution_level(
        eligibility_base, computed_floor, contract=contract
    )
    confirmed_minimum_eligible = _max_execution_level(
        eligibility_base, confirmed_computed_floor, contract=contract
    )

    l5_requirement = formula["l5_requirement"]
    l5_statuses = {
        identifier: evaluation["status"]
        for identifier, evaluation in l5_assurance_evaluations.items()
    }
    l5_sources_are_analysis = all(
        evaluation["evidence_kind"] == l5_requirement["source"]
        for evaluation in l5_assurance_evaluations.values()
    )
    confirmed_material_l4 = any(
        row["floor"] == "L4"
        and row["id"] not in {"formal-release-declared", "unknown-critical-boundary"}
        and trigger_evaluations[row["id"]]["status"] == "matched"
        for row in contract["trigger_registry"]
    )
    if l5_statuses["confirmed-material-l4"] == "true" and not confirmed_material_l4:
        raise ExecutionLevelError(
            "confirmed-material-l4 assurance evidence requires a confirmed non-provisional material L4 trigger"
        )
    l5_eligible = (
        l5_sources_are_analysis
        and confirmed_material_l4
        and all(l5_statuses[item] == "true" for item in l5_requirement["required_all"])
        and any(l5_statuses[item] == "true" for item in l5_requirement["required_any"])
    )
    confirmation_contract = contract["l5_confirmation"]
    if l5_confirmation not in confirmation_contract["states"]:
        raise ExecutionLevelError(f"L5 confirmation {l5_confirmation!r} is invalid")
    if requested == "L5":
        if l5_confirmation not in {"not-required", "explicit"}:
            raise ExecutionLevelError(
                "explicit requested L5 is pre-confirmed and cannot use automatic confirmation states"
            )
        canonical_confirmation = confirmation_contract["explicit_l5_state"]
    elif l5_eligible:
        if l5_confirmation not in {"pending", "confirmed", "rejected"}:
            raise ExecutionLevelError(
                "automatic L5 recommendation requires pending, confirmed, or rejected confirmation"
            )
        canonical_confirmation = l5_confirmation
    else:
        if l5_confirmation != "not-required":
            raise ExecutionLevelError(
                "L5 confirmation is invalid without an eligible automatic recommendation"
            )
        canonical_confirmation = "not-required"

    assurance_recommendation = "L5" if l5_eligible else "not-recommended"
    automatic = minimum_eligible
    if l5_eligible and canonical_confirmation == "confirmed":
        automatic = confirmation_contract["confirmed_level"]
    elif l5_eligible:
        automatic = confirmation_contract["rejected_level"]
    requested_or_automatic = (
        automatic
        if formula["requested_base"][requested] == "automatic"
        else formula["requested_base"][requested]
    )
    mandatory_floor = _max_execution_level(
        computed_floor, prior_historical_max_floor, contract=contract
    )
    effective = _max_execution_level(
        requested_or_automatic,
        minimum_eligible,
        mandatory_floor,
        prior_historical_max_effective,
        contract=contract,
    )
    confirmed_mandatory_floor = _max_execution_level(
        confirmed_computed_floor, prior_historical_max_floor, contract=contract
    )
    confirmed_automatic = confirmed_minimum_eligible
    if l5_eligible and canonical_confirmation == "confirmed":
        confirmed_automatic = confirmation_contract["confirmed_level"]
    elif l5_eligible:
        confirmed_automatic = confirmation_contract["rejected_level"]
    confirmed_requested_or_automatic = (
        confirmed_automatic
        if formula["requested_base"][requested] == "automatic"
        else formula["requested_base"][requested]
    )
    confirmed_effective = _max_execution_level(
        confirmed_requested_or_automatic,
        confirmed_minimum_eligible,
        confirmed_mandatory_floor,
        prior_historical_max_effective,
        contract=contract,
    )
    confirmation_pending = l5_eligible and canonical_confirmation == "pending"
    next_historical_floor = _max_execution_level(
        prior_historical_max_floor,
        confirmed_mandatory_floor,
        contract=contract,
    )
    next_historical_effective = (
        prior_historical_max_effective
        if confirmation_pending
        else _max_execution_level(
            prior_historical_max_effective,
            confirmed_effective,
            contract=contract,
        )
    )
    obligations: list[str] = []
    for level in contract["levels"]:
        if level["rank"] <= _execution_rank(effective, contract):
            obligations.extend(level["obligations"])
    obligations.extend(contract["non_bypassable"])
    return {
        "requested": requested,
        "computed_floor": computed_floor,
        "confirmed_computed_floor": confirmed_computed_floor,
        "provisional_floor": critical_unknown,
        "automatic_level": automatic,
        "minimum_eligible_level": minimum_eligible,
        "requested_base": requested_or_automatic,
        "requested_or_automatic": requested_or_automatic,
        "mandatory_floor": mandatory_floor,
        "effective_level": effective,
        "assurance_recommendation": assurance_recommendation,
        "l5_confirmation": canonical_confirmation,
        "confirmation_action": (
            confirmation_contract["automatic_pending_action"]
            if confirmation_pending
            else "execute"
        ),
        "next_historical_floor": next_historical_floor,
        "next_historical_effective": next_historical_effective,
        "edit_status": (
            contract["critical_unknown"]["edit_status"]
            if critical_unknown or confirmation_pending
            else "allowed"
        ),
        "level_basis": {
            "trigger_evaluations": canonical_triggers,
            "l1_eligibility": canonical_l1,
            "l2_eligibility": canonical_l2,
            "l5_assurance_eligibility": canonical_l5,
            "l5_confirmation": canonical_confirmation,
            "obligations": list(dict.fromkeys(obligations)),
            "unresolved": unresolved,
            "edit_status": (
                contract["critical_unknown"]["edit_status"]
                if critical_unknown or confirmation_pending
                else "allowed"
            ),
        },
    }


def execution_level_integrity_fallback(
    *,
    requested: str,
    prior_historical_max_floor: str | None = None,
    prior_historical_max_effective: str | None = None,
    contract: dict[str, object] | None = None,
) -> dict[str, object]:
    """Return the fixed fail-closed outcome when runtime policy integrity fails."""

    contract = EXECUTION_LEVEL_MODEL if contract is None else contract
    seed = contract["formula"]["computed_floor_seed"]
    prior_floor = seed if prior_historical_max_floor is None else prior_historical_max_floor
    prior_effective = (
        seed
        if prior_historical_max_effective is None
        else prior_historical_max_effective
    )
    _execution_rank(prior_floor, contract)
    _execution_rank(prior_effective, contract)
    if _execution_rank(prior_effective, contract) < _execution_rank(prior_floor, contract):
        raise ExecutionLevelError(
            "historical effective level cannot be below historical floor"
        )
    fallback = contract["integrity_fallback"]
    fallback_floor = fallback["floor"]
    retained_prior_floor = (
        prior_floor if fallback["retain_prior_historical_maxima"] else seed
    )
    retained_prior_effective = (
        prior_effective if fallback["retain_prior_historical_maxima"] else seed
    )
    mandatory_floor = _max_execution_level(
        fallback_floor,
        retained_prior_floor,
        contract=contract,
    )
    requested_known_l5 = (
        "L5"
        if fallback["retain_explicit_known_l5"] and requested == "L5"
        else fallback_floor
    )
    effective = _max_execution_level(
        fallback_floor,
        requested_known_l5,
        retained_prior_effective,
        contract=contract,
    )
    next_effective = retained_prior_effective
    if requested_known_l5 == "L5":
        next_effective = _max_execution_level(
            next_effective,
            requested_known_l5,
            contract=contract,
        )
    return {
        "integrity_status": fallback["edit_status"],
        "computed_floor": mandatory_floor,
        "mandatory_floor": mandatory_floor,
        "effective_level": effective,
        "next_historical_floor": retained_prior_floor,
        "next_historical_effective": next_effective,
        "provisional_floor": fallback["provisional_floor"],
        "edit_status": fallback["edit_status"],
        "partial_computation": fallback["partial_computation"],
        "allowed_outcomes": list(fallback["allowed_outcomes"]),
        "forbidden_actions": list(fallback["forbidden_actions"]),
    }


def execution_scope_transition_errors(
    *,
    previous_task_id: str,
    previous_scope_lineage: str,
    previous_mandatory_floor: str,
    previous_effective_level: str,
    previous_historical_max_floor: str,
    previous_historical_max_effective: str,
    current_task_id: str,
    current_scope_lineage: str,
    current_mandatory_floor: str,
    current_effective_level: str,
    current_historical_max_floor: str,
    current_historical_max_effective: str,
    scope_change: str,
    lowering_requested: bool,
    strict_narrowing_proof: bool,
    previous_provisional_floor: bool,
    current_provisional_floor: bool,
    material_edit_started: bool,
    provisional_resolution_source: str | None,
) -> list[str]:
    """Validate an explicit scope-lineage transition without storing task state."""

    errors: list[str] = []
    if scope_change not in {"same", "expanded", "narrowed"}:
        return [f"unknown scope change {scope_change!r}"]
    for label, value in (
        ("lowering_requested", lowering_requested),
        ("strict_narrowing_proof", strict_narrowing_proof),
        ("previous_provisional_floor", previous_provisional_floor),
        ("current_provisional_floor", current_provisional_floor),
        ("material_edit_started", material_edit_started),
    ):
        if not isinstance(value, bool):
            errors.append(f"{label} must be boolean")
    if provisional_resolution_source is not None and (
        not isinstance(provisional_resolution_source, str)
        or not provisional_resolution_source.strip()
    ):
        errors.append("provisional resolution source must be non-empty text or null")
    level_pairs = (
        ("mandatory floor", previous_mandatory_floor, current_mandatory_floor),
        ("effective level", previous_effective_level, current_effective_level),
        (
            "historical max floor",
            previous_historical_max_floor,
            current_historical_max_floor,
        ),
        (
            "historical max effective",
            previous_historical_max_effective,
            current_historical_max_effective,
        ),
    )
    for _, previous, current in level_pairs:
        _execution_rank(previous)
        _execution_rank(current)
    if previous_task_id == current_task_id and previous_scope_lineage != current_scope_lineage:
        errors.append("same Task ID cannot open a new Scope Lineage")
    resolving_provisional = previous_provisional_floor and not current_provisional_floor
    safe_resolution_source = (
        isinstance(provisional_resolution_source, str)
        and provisional_resolution_source.startswith(("analysis_handoff:", "user_fact:"))
    )
    safe_provisional_resolution = (
        resolving_provisional
        and previous_task_id == current_task_id
        and previous_scope_lineage == current_scope_lineage
        and scope_change == "same"
        and not material_edit_started
        and safe_resolution_source
        and _execution_rank(current_historical_max_floor)
        >= _execution_rank(previous_historical_max_floor)
        and _execution_rank(current_historical_max_effective)
        >= _execution_rank(previous_historical_max_effective)
    )
    if resolving_provisional and not safe_provisional_resolution:
        errors.append(
            "provisional floor resolution requires the same Task, lineage, and scope, "
            "pre-material-edit proof from analysis_handoff or user_fact, and retained confirmed history"
        )
    if (
        not current_provisional_floor
        and _execution_rank(current_historical_max_floor)
        < _execution_rank(current_mandatory_floor)
    ):
        errors.append("historical max floor cannot be below the current mandatory floor")
    if (
        not current_provisional_floor
        and _execution_rank(current_historical_max_effective)
        < _execution_rank(current_effective_level)
    ):
        errors.append("historical max effective cannot be below the current effective level")
    must_inherit = scope_change in {"same", "expanded"}
    observed_lowering = any(
        _execution_rank(current) < _execution_rank(previous)
        for _, previous, current in level_pairs
    )
    if must_inherit:
        for label, previous, current in level_pairs:
            provisional_level = label in {"mandatory floor", "effective level"}
            if (
                _execution_rank(current) < _execution_rank(previous)
                and not (safe_provisional_resolution and provisional_level)
            ):
                errors.append(f"{scope_change} scope cannot lower {label}")
    if scope_change == "expanded" and lowering_requested:
        errors.append("scope expansion inherits historical maxima and cannot lower")
    ordinary_lowering = observed_lowering and not safe_provisional_resolution
    if ordinary_lowering and not lowering_requested:
        errors.append("execution lowering must be declared and proven")
    if lowering_requested or ordinary_lowering:
        if previous_task_id == current_task_id:
            errors.append("execution lowering requires a new Task ID")
        expected_prefix = previous_scope_lineage.rstrip("/") + "/"
        if not current_scope_lineage.startswith(expected_prefix):
            errors.append("execution lowering requires a child Scope Lineage")
        if scope_change != "narrowed" or not strict_narrowing_proof:
            errors.append("execution lowering requires strict canonical scope narrowing proof")
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
EXPECTED_PROFESSIONAL_SKILL_COUNT = 26
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
        "not-automatic": 1,
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
EXPECTED_PROFILE_TOP_LEVEL_COUNTS = {
    # The default installs the control plane and standard Professional Skills.
    # Layer 3 Skills remain targeted references rather than a hidden runtime.
    "recommended": EXPECTED_CONTROL_SKILL_COUNT + EXPECTED_PROFESSIONAL_SKILL_COUNT,
    "full": (
        EXPECTED_CONTROL_SKILL_COUNT
        + EXPECTED_PROFESSIONAL_SKILL_COUNT
        + EXPECTED_DOMAIN_EXTENSION_COUNT
    ),
    "dev": (
        EXPECTED_CONTROL_SKILL_COUNT
        + EXPECTED_PROFESSIONAL_SKILL_COUNT
        + EXPECTED_FOUNDATION_CAPABILITY_COUNT
        + EXPECTED_DOMAIN_EXTENSION_COUNT
    ),
}
EXPECTED_PROFILE_DELIVERY_MODE_COUNTS = {
    "recommended": {
        "top_level_skill": 27,
        "targeted_reference": 154,
        "routing_index_only": 9,
    },
    "full": {
        "top_level_skill": 40,
        "targeted_reference": 141,
        "routing_index_only": 9,
    },
    "dev": {
        "top_level_skill": 190,
        "targeted_reference": 0,
        "routing_index_only": 0,
    },
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
        or scenario.get("light_case_id") != "diagnosis-only"
        or scenario.get("control_path") != "diagnosis"
        or scenario.get("analysis")
        != {
            "primary": "engineering-change-analysis",
            "layer3": ["failure-diagnosis"],
        }
        or scenario.get("tasks") != []
        or scenario.get("review") is not None
        or scenario.get("review_exemption") != "diagnosis-only"
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
        "light_case_id": scenario["light_case_id"],
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
                "light_case_id": diagnosis_decision["light_case_id"],
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
    provenance_fields = {
        "decision_id",
        "scenario_id",
        "light_case_id",
        "release_scenario",
        "selector_registry",
    }
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
            for field in ("decision_id", "scenario_id", "light_case_id")
        )
        or not all(
            isinstance(row["provenance"].get(field), dict)
            for field in ("release_scenario", "selector_registry")
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
        if (
            not isinstance(link, dict)
            or set(link) != {"contract", "path_template"}
            or link.get("contract") != LAYER3_SELECTOR_REFERENCE_RECORDS_CONTRACT
            or link.get("path_template")
            != (
                f"../reference-records/{base['professional_skill']}/"
                "{owner_skill}.json"
            )
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

    return {
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


def layer3_selector_runtime_selection_receipt(
    projection: object,
    *,
    evidence_signals: object,
) -> dict[str, Any]:
    """Resolve one local projection and emit its deterministic owner receipt."""

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
    receipt["receipt_sha256"] = hashlib.sha256(
        json.dumps(
            receipt,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return receipt


def layer3_selector_runtime_selection_receipt_errors(
    receipt: object,
    *,
    expected_owner: str,
    expected_profile: str,
    expected_professional: str,
    expected_selection_kind: str,
    expected_selected_layer3: list[str],
) -> list[str]:
    """Replay one receipt from canonical authority and compare it exactly."""

    expected_fields = {
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
        "receipt_sha256",
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
            exact_layer3=None,
        )
        replayed = layer3_selector_runtime_selection_receipt(
            projection,
            evidence_signals=evidence,
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
) -> list[str]:
    """Resolve exact Layer 3 through the receipt-producing selection consumer."""

    return list(
        layer3_selector_runtime_selection_receipt(
            projection,
            evidence_signals=evidence_signals,
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
